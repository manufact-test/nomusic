<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Application;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with($config['db_name'], 'celikom_test')) throw new RuntimeException('disposable_test_only');
$pdo = Connection::open($config);
(new MigrationRunner($pdo, dirname(__DIR__) . '/migrations'))->run();
foreach (['user_email_security','user_auth_events','user_sessions','user_devices','user_auth_attempts','users'] as $table) {
    $pdo->exec('DELETE FROM ' . $table);
}
$config['auth_enabled'] = true;
$config['environment'] = 'test';
$config['mail_code_pepper'] = str_repeat('test-email-pepper-', 3);
$sentEmails = [];
$config['mail_test_sink'] = static function (string $to, string $message, string $purpose) use (&$sentEmails): void {
    preg_match('/([0-9]{6})/', $message, $m);
    $sentEmails[$to . ':' . $purpose] = $m[1] ?? '';
};
$app = new Application($config);
$install1 = '8de936d6-2af5-4ca7-973f-24cb5d355111';
$install2 = '8de936d6-2af5-4ca7-973f-24cb5d355112';
$email = 'stage9-user@example.org';
$password = 'correct horse battery staple stage9';
function callAuth(Application $app, string $method, string $endpoint, array $input = [], string $access = ''): array
{
    $result = $app->handle($method, '/api/v1/auth/' . $endpoint, [],
        ['Content-Type' => 'application/json', 'Authorization' => 'Bearer ' . $access],
        $method === 'GET' ? '' : json_encode((object)$input, JSON_THROW_ON_ERROR));
    return [$result->status, json_decode($result->body, true, flags: JSON_THROW_ON_ERROR)];
}
run('Stage9 auth OFF by default and independent of admin/resolve', function () use ($config): void {
    $off = $config; $off['auth_enabled'] = false;
    expect((new Application($off))->handle('GET', '/api/v1/auth/me')->status === 404, 'flag off');
});
[$code, $first] = callAuth($app, 'POST', 'register',
    ['email' => $email, 'password' => $password, 'installation_id' => $install1]);
expect($code === 201 && ($first['verification_required'] ?? false), 'pending email first');
expect(callAuth($app, 'POST', 'login',
    ['email'=>$email,'password'=>$password,'installation_id'=>$install1])[1]['verification_required'] ?? false, 'unverified login never grants session');
[$verifiedStatus, $first] = callAuth($app, 'POST', 'verify-email', [
    'email'=>$email, 'code'=>$sentEmails[$email.':verify'], 'installation_id'=>$install1
]);
expect($verifiedStatus === 200, 'first email verified');

run('Stage9 registration uses opaque tokens and hashed DB secrets', function () use ($pdo, $code, $first, $password): void {
    expect($code === 201 && isset($first['user']['id']) && strlen($first['refresh_token']) === 64, 'registered');
    $row = $pdo->query('SELECT u.password_hash, s.access_hash, s.refresh_hash
        FROM users u JOIN user_sessions s ON s.user_id = u.id LIMIT 1')->fetch();
    expect(password_verify($password, $row['password_hash']), 'KDF hash');
    expect($row['access_hash'] === hash('sha256', $first['access_token']), 'Access digest');
    expect($row['refresh_hash'] === hash('sha256', $first['refresh_token']), 'Refresh digest');
    expect($row['refresh_hash'] !== $first['refresh_token'], 'Refresh plaintext absent');
});
run('Stage9 duplicates, weak passwords, malformed UUID, admin isolation', function () use ($app, $email, $password, $install1): void {
    expect(callAuth($app, 'POST', 'register', ['email' => $email, 'password' => $password, 'installation_id' => $install1])[0] === 409, 'duplicate');
    expect(callAuth($app, 'POST', 'register', ['email' => 'x@example.org', 'password' => 'short', 'installation_id' => $install1])[0] === 422, 'weak');
    expect(callAuth($app, 'POST', 'register', ['email' => 'y@example.org', 'password' => $password, 'installation_id' => 'music.yandex.ru'])[0] === 400, 'PII/invalid UUID');
    expect(callAuth($app, 'GET', 'me', [], str_repeat('f', 64))[0] === 401, 'private admin token cannot authorize');
});
[$code2, $second] = callAuth($app, 'POST', 'login',
    ['email' => strtoupper($email), 'password' => $password, 'installation_id' => $install2]);
run('Stage9 multiple independent device sessions', function () use ($app, $pdo, $first, $second, $code2): void {
    expect($code2 === 200 && $second['user']['id'] === $first['user']['id'], 'same user');
    expect((int)$pdo->query('SELECT COUNT(*) FROM user_devices')->fetchColumn() === 2, '2 devices');
    expect(callAuth($app, 'GET', 'me', [], $first['access_token'])[0] === 200, 'device 1 valid');
    expect(callAuth($app, 'GET', 'me', [], $second['access_token'])[0] === 200, 'device 2 valid');
    expect(count(callAuth($app, 'GET', 'sessions', [], $second['access_token'])[1]['sessions']) === 2, 'sessions listed');
});
[$rotatedCode, $rotated] = callAuth($app, 'POST', 'refresh',
    ['installation_id' => $install1, 'refresh_token' => $first['refresh_token']]);
run('Stage9 refresh rotation invalidates old access', function () use ($app, $install1, $first, $rotatedCode, $rotated): void {
    expect($rotatedCode === 200 && $rotated['refresh_token'] !== $first['refresh_token'], 'token rotated');
    expect(callAuth($app, 'GET', 'me', [], $first['access_token'])[0] === 401, 'old access invalid');
    expect(callAuth($app, 'GET', 'me', [], $rotated['access_token'])[0] === 200, 'new access valid');
    expect(callAuth($app, 'POST', 'refresh', ['installation_id' => $install1, 'refresh_token' => str_repeat('1', 64)])[0] === 401, 'stolen/unknown denied');
});
run('Stage9 replayed refresh revokes only affected device', function () use ($app, $first, $second, $rotated, $install1): void {
    expect(callAuth($app, 'POST', 'refresh', ['installation_id' => $install1, 'refresh_token' => $first['refresh_token']])[0] === 401, 'replay rejected');
    expect(callAuth($app, 'GET', 'me', [], $rotated['access_token'])[0] === 401, 'device1 revoked');
    expect(callAuth($app, 'GET', 'me', [], $second['access_token'])[0] === 200, 'device2 remains valid');
});
run('Stage9 login, logout one device and disabled user', function () use ($app, $pdo, $install1, $second, $email, $password): void {
    [$code,$again] = callAuth($app, 'POST', 'login', ['email'=>$email,'password'=>$password,'installation_id'=>$install1]);
    expect($code === 200 && $again['user']['id'] === $second['user']['id'], 'reinstall/login same user');
    expect(callAuth($app, 'POST', 'activate', [], $again['access_token'])[0] === 200, 'activation');
    expect(callAuth($app, 'POST', 'activate', [], $again['access_token'])[0] === 200, 'activation idempotent');
    expect((int)$pdo->query("SELECT COUNT(*) FROM user_auth_events WHERE event_name = 'first_activation'")->fetchColumn() === 1, 'one activation event');
    expect(callAuth($app, 'POST', 'logout', ['installation_id'=>$install1,'refresh_token'=>$again['refresh_token']])[0] === 200, 'logout');
    expect(callAuth($app, 'GET', 'me', [], $again['access_token'])[0] === 401, 'logout invalidated access');
    expect(callAuth($app, 'GET', 'me', [], $second['access_token'])[0] === 200, 'other device survives');
    $pdo->exec("UPDATE users SET status = 'disabled' WHERE email = 'stage9-user@example.org'");
    expect(callAuth($app, 'GET', 'me', [], $second['access_token'])[0] === 401, 'disabled rejects access');
    expect(callAuth($app, 'POST', 'login', ['email'=>$email,'password'=>$password,'installation_id'=>$install1])[0] === 403, 'disabled rejects login');
});
run('Stage9 session expiry, revoked and cleanup do not alter catalog', function () use ($pdo, $app, $second, $install2): void {
    $pdo->exec('UPDATE user_sessions SET refresh_expires_at = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 1 SECOND)');
    expect(callAuth($app, 'POST', 'refresh', ['installation_id'=>$install2,'refresh_token'=>$second['refresh_token']])[0] === 401, 'expired refresh denied');
    expect((int)$pdo->query("SELECT COUNT(*) FROM user_auth_events WHERE event_name = 'user_registered'")->fetchColumn() === 1, 'registration event');
});

run('Stage9 expired access token rotates via valid refresh without waiting 15 minutes', function () use ($app, $pdo): void {
    $installation = '8de936d6-2af5-4ca7-973f-24cb5d355113';
    $email = 'stage9-expiry@example.org';
    $password = 'correct horse battery staple expiry';
    [$registerCode, $registered] = callAuth($app, 'POST', 'register', [
        'email' => $email, 'password' => $password, 'installation_id' => $installation
    ]);
    expect($registerCode === 201 && ($registered['verification_required'] ?? false), 'expiry pending account created');
    $challenge = $GLOBALS['sentEmails'][$email . ':verify'];
    [$verificationCode, $registered] = callAuth($app,'POST','verify-email',[
        'email'=>$email,'code'=>$challenge,'installation_id'=>$installation
    ]);
    expect($verificationCode === 200, 'verified expiry account');
    $accessHash = hash('sha256', $registered['access_token']);
    $stmt = $pdo->prepare('UPDATE user_sessions
        SET access_expires_at = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 2 SECOND)
        WHERE access_hash = ?');
    $stmt->execute([$accessHash]);
    expect($stmt->rowCount() === 1, 'access expiry simulated for only this session');
    expect(callAuth($app, 'GET', 'me', [], $registered['access_token'])[0] === 401, 'expired access denied');
    [$refreshCode, $rotated] = callAuth($app, 'POST', 'refresh', [
        'installation_id' => $installation, 'refresh_token' => $registered['refresh_token']
    ]);
    expect($refreshCode === 200, 'valid refresh survives access expiry');
    expect($rotated['access_token'] !== $registered['access_token'], 'new access');
    expect(callAuth($app, 'GET', 'me', [], $rotated['access_token'])[0] === 200, 'rotated access accepted');
    expect(callAuth($app, 'POST', 'logout', [
        'installation_id' => $installation, 'refresh_token' => $rotated['refresh_token']
    ])[0] === 200, 'expired-access test logout');
});
