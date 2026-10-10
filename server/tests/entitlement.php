<?php

declare(strict_types=1);

require __DIR__ . '/smoke.php';

use Celikom\Auth\BearerAuthenticator;
use Celikom\Database\Connection;
use Celikom\Database\MigrationRunner;
use Celikom\Entitlement\EntitlementService;
use Celikom\Entitlement\TrialService;

$config = require dirname(__DIR__) . '/config/app.php';
if (!str_starts_with($config['db_name'], 'celikom_test')) throw new RuntimeException('disposable_test_only');
$pdo = Connection::open($config);
$runner = new MigrationRunner($pdo, dirname(__DIR__) . '/migrations');
$runner->run();
$trial = new TrialService($pdo);
$entitlement = new EntitlementService($pdo);
$catalogBefore = $pdo->query('SELECT id, status, is_active, version FROM track_replacements ORDER BY id')->fetchAll();
$ids = [];
function fixtureUser(PDO $pdo, array &$ids, bool $verified = true): int
{
    $stmt = $pdo->prepare('INSERT INTO users (email, password_hash) VALUES (?, ?)');
    $stmt->execute(['stage10-' . bin2hex(random_bytes(8)) . '@example.org', 'test-only-not-login']);
    $id = (int)$pdo->lastInsertId();
    $ids[] = $id;
    if ($verified) $pdo->exec('INSERT INTO user_email_security (user_id, verified_at) VALUES (' . $id . ', UTC_TIMESTAMP(6))');
    return $id;
}
function denyTrial(TrialService $trial, int $id, string $reason): void
{
    try { $trial->activate($id); throw new RuntimeException('activation unexpectedly allowed'); }
    catch (DomainException $error) { expect($error->getMessage() === $reason, 'denied activation reason'); }
}
try {
    run('Stage10 read-only check does not start trial; old Stage9 activation does not backfill', function () use ($pdo, &$ids, $entitlement, $trial): void {
        $id = fixtureUser($pdo, $ids);
        $pdo->exec('UPDATE users SET first_activated_at = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 30 DAY) WHERE id = ' . $id);
        expect($entitlement->check($id)->reason === 'trial_not_started', 'no automatic start');
        expect((int)$pdo->query('SELECT COUNT(*) FROM account_trials WHERE user_id = ' . $id)->fetchColumn() === 0, 'no writes');
        $result = $trial->activate($id);
        expect($result['activated'] && $result['trial_seconds'] === 432000, 'explicit activation starts now');
        expect(str_ends_with($result['trial_ends_at'], 'Z'), 'unambiguous UTC');
        $row = $pdo->query('SELECT TIMESTAMPDIFF(MICROSECOND, valid_from, valid_until) AS duration FROM account_trials WHERE user_id = ' . $id)->fetch();
        expect((int)$row['duration'] === 432000000000, 'exactly five days including microseconds');
        $state = $entitlement->check($id);
        expect($state->allowed && $state->source === 'trial' && $state->validUntil === $result['trial_ends_at'], 'allowed canonical result');
        expect($trial->activate($id)['activated'] === false, 'reinstallation/retry does not reset trial');
        expect((int)$pdo->query('SELECT COUNT(*) FROM entitlement_ledger WHERE user_id = ' . $id)->fetchColumn() === 1, 'one ledger row');
    });
    run('Stage10 unverified/missing/restricted/disabled users denied with no trial', function () use ($pdo, &$ids, $entitlement, $trial): void {
        expect($entitlement->check(0)->reason === 'user_not_found', 'missing user denied');
        denyTrial($trial, 0, 'user_not_found');
        $id = fixtureUser($pdo, $ids, false);
        expect($entitlement->check($id)->reason === 'email_unverified', 'unverified denied');
        denyTrial($trial, $id, 'email_unverified');
        foreach (['restricted', 'disabled'] as $status) {
            $id = fixtureUser($pdo, $ids);
            $pdo->exec("UPDATE users SET status = '$status' WHERE id = $id");
            denyTrial($trial, $id, 'account_disabled');
            expect(!$entitlement->check($id)->allowed, 'inactive account denied');
        }
    });
    run('Stage10 exact expiry uses database clock, never restarts an expired trial', function () use ($pdo, &$ids, $trial, $entitlement): void {
        $id = fixtureUser($pdo, $ids);
        $trial->activate($id);
        $window = $pdo->query('SELECT valid_until FROM account_trials WHERE user_id = ' . $id)->fetchColumn();
        // MySQL session clock controls UTC_TIMESTAMP, independent of PHP/client time.
        $future = (int)$pdo->query('SELECT UNIX_TIMESTAMP(DATE_ADD(UTC_TIMESTAMP(), INTERVAL 6 DAY))')->fetchColumn();
        try {
            $pdo->exec('SET timestamp = ' . $future);
            expect(!$entitlement->check($id)->allowed, 'database expiry defeats PHP-clock allow');
            expect(!$trial->activate($id)['activated'], 'expired cannot reactivate');
            $pdo->exec('SET timestamp = ' . ($future - 86400));
            // Create an exact boundary on the database clock, keeping ledger consistent.
            $pdo->exec('UPDATE account_trials SET valid_from = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 432000 SECOND), valid_until = UTC_TIMESTAMP(6) WHERE user_id = ' . $id);
            $pdo->exec('UPDATE entitlement_ledger l JOIN account_trials t ON t.ledger_id = l.id SET l.valid_from = t.valid_from, l.valid_until = t.valid_until WHERE t.user_id = ' . $id);
            expect(!$entitlement->check($id)->allowed, 'exclusive expiry boundary');
            $pdo->exec('SET timestamp = ' . ($future - 86400 - 1));
            expect($entitlement->check($id)->allowed, 'one second before boundary');
        } finally { $pdo->exec('SET timestamp = 0'); }
        expect(is_string($window), 'original expiry captured');
    });
    run('Stage10 ledger failure rolls back trial; retry succeeds', function () use ($pdo, &$ids, $trial): void {
        $id = fixtureUser($pdo, $ids);
        $pdo->exec("CREATE TRIGGER stage10_test_ledger_failure BEFORE INSERT ON entitlement_ledger FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'fixture_failure'");
        try {
            try { $trial->activate($id); throw new RuntimeException('failure was ignored'); }
            catch (PDOException) { expect(!$pdo->inTransaction(), 'failed transaction rolled back'); }
            expect((int)$pdo->query('SELECT COUNT(*) FROM account_trials WHERE user_id = ' . $id)->fetchColumn() === 0, 'no orphan trial');
        } finally { $pdo->exec('DROP TRIGGER stage10_test_ledger_failure'); }
        $pdo->exec("CREATE TRIGGER stage10_test_trial_failure BEFORE INSERT ON account_trials FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'fixture_failure'");
        try {
            try { $trial->activate($id); throw new RuntimeException('failure was ignored'); }
            catch (PDOException) { expect(!$pdo->inTransaction(), 'insert failure rolled back'); }
            expect((int)$pdo->query('SELECT COUNT(*) FROM entitlement_ledger WHERE user_id = ' . $id)->fetchColumn() === 0, 'no orphan ledger grant');
        } finally { $pdo->exec('DROP TRIGGER stage10_test_trial_failure'); }
        expect($trial->activate($id)['activated'], 'retry creates trial');
        $pdo->exec("UPDATE entitlement_ledger SET reason = 'test_corruption' WHERE user_id = $id");
        expect(!(new EntitlementService($pdo))->check($id)->allowed, 'inconsistent ledger fails closed');
    });
    run('Stage10 simultaneous device workers produce one trial and one ledger entry', function () use ($pdo, &$ids): void {
        $id = fixtureUser($pdo, $ids);
        $workers = [];
        $pdo->beginTransaction();
        $pdo->query('SELECT id FROM users WHERE id = ' . $id . ' FOR UPDATE')->fetch();
        try {
            for ($i = 0; $i < 2; $i++) {
                $process = proc_open([PHP_BINARY, __DIR__ . '/trial-race-worker.php', (string)$id],
                    [0 => ['pipe','r'], 1 => ['pipe','w'], 2 => ['pipe','w']], $pipes);
                expect(is_resource($process), 'worker created');
                fclose($pipes[0]);
                stream_set_timeout($pipes[1], 10);
                $workers[] = [$process, $pipes];
                expect(trim((string)fgets($pipes[1])) === 'ready', 'independent PDO worker connected');
            }
        } finally { $pdo->rollBack(); }
        $results = [];
        foreach ($workers as [$process, $pipes]) {
            $results[] = json_decode((string)stream_get_contents($pipes[1]), true, flags: JSON_THROW_ON_ERROR);
            fclose($pipes[1]);
            $error = stream_get_contents($pipes[2]); fclose($pipes[2]);
            expect(proc_close($process) === 0 && $error === '', 'worker succeeds');
        }
        expect(count(array_filter($results, fn($r) => $r['activated'])) === 1, 'one activation winner');
        expect($results[0]['trial_ends_at'] === $results[1]['trial_ends_at'], 'same account deadline');
        expect((int)$pdo->query('SELECT COUNT(*) FROM entitlement_ledger WHERE user_id = ' . $id)->fetchColumn() === 1, 'one ledger grant');
    });
    run('Stage10 bearer requires verified active user and live independent session', function () use ($pdo, &$ids, $config): void {
        $id = fixtureUser($pdo, $ids);
        $pdo->exec("INSERT INTO user_devices (user_id, installation_id) VALUES ($id, '8de936d6-2af5-4ca7-973f-24cb5d355199')");
        $device = (int)$pdo->lastInsertId();
        $access = bin2hex(random_bytes(32));
        $stmt = $pdo->prepare('INSERT INTO user_sessions (user_id, device_id, access_hash, refresh_hash, access_expires_at, refresh_expires_at) VALUES (?, ?, ?, ?, DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 900 SECOND), DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 90 DAY))');
        $stmt->execute([$id, $device, hash('sha256', $access), hash('sha256', random_bytes(32))]);
        $bearer = new BearerAuthenticator($pdo);
        $headers = ['authorization' => 'Bearer ' . $access];
        expect($bearer->userId($headers) === $id, 'valid bearer');
        $pdo->exec("UPDATE users SET status = 'disabled' WHERE id = $id");
        expect($bearer->userId($headers) === null, 'disabled account bearer rejected');
        $pdo->exec("UPDATE users SET status = 'active' WHERE id = $id");
        $pdo->exec("UPDATE user_email_security SET verified_at = NULL WHERE user_id = $id");
        expect($bearer->userId($headers) === null, 'unverified bearer rejected');
        $pdo->exec("UPDATE user_email_security SET verified_at = UTC_TIMESTAMP(6) WHERE user_id = $id");
        $pdo->exec("UPDATE user_sessions SET revoked_at = UTC_TIMESTAMP(6) WHERE user_id = $id");
        expect($bearer->userId($headers) === null, 'revoked bearer rejected');
    });
    run('Stage10 user bearer activates trial, resolves approved-only signed Range and revokes audio', function () use ($pdo, &$ids, $config): void {
        $id = fixtureUser($pdo, $ids);
        $pdo->exec("INSERT INTO user_devices (user_id, installation_id) VALUES ($id, '8de936d6-2af5-4ca7-973f-24cb5d355198')");
        $device = (int)$pdo->lastInsertId();
        $access = bin2hex(random_bytes(32));
        $stmt = $pdo->prepare('INSERT INTO user_sessions (user_id, device_id, access_hash, refresh_hash, access_expires_at, refresh_expires_at) VALUES (?, ?, ?, ?, DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 900 SECOND), DATE_ADD(UTC_TIMESTAMP(6), INTERVAL 90 DAY))');
        $stmt->execute([$id, $device, hash('sha256', $access), hash('sha256', random_bytes(32))]);
        $sessionId = (int)$pdo->lastInsertId();
        $cfg = $config; $cfg['api_enabled'] = true; $cfg['auth_enabled'] = true; $cfg['entitlement_enabled'] = true;
        $cfg['test_api_token'] = str_repeat('private-legacy-test-', 3);
        $cfg['audio_signing_key'] = str_repeat('stage10-test-signing-', 3);
        $cfg['analytics_privacy_key'] = str_repeat('stage10-test-privacy-', 3);
        $cfg['user_uploads_enabled'] = true;
        $app = new Celikom\Application($cfg);
        $headers = ['Authorization' => 'Bearer ' . $access, 'Content-Type' => 'application/json'];
        $active = $pdo->query("SELECT t.service_track_id FROM tracks t JOIN track_replacements r ON r.track_id=t.id WHERE r.status='approved' AND r.is_active=1 LIMIT 1")->fetchColumn();
        expect(is_string($active), 'approved synthetic fixture exists');
        $query = ['service' => 'yandex', 'track_id' => $active];
        expect($app->handle('GET', '/api/v1/resolve', $query)->status === 401, 'anonymous denied');
        expect($app->handle('GET', '/api/v1/resolve', $query, $headers)->status === 403, 'no auto-start from resolve');
        expect($app->handle('POST', '/api/v1/auth/activate', [], $headers, '{}')->status === 200, 'verified activation');
        $decision = $app->handle('GET', '/api/v1/entitlement', [], $headers);
        expect($decision->status === 200 && json_decode($decision->body, true)['allowed'], 'entitlement endpoint');
        $resolved = $app->handle('GET', '/api/v1/resolve', $query, $headers);
        $data = json_decode($resolved->body, true);
        expect($resolved->status === 200 && $data['found'], 'approved fixture resolves');
        parse_str((string)parse_url($data['audio_url'], PHP_URL_QUERY), $signed);
        expect((int)$signed['sid'] === $sessionId, 'signed to this device');
        $path = (string)parse_url($data['audio_url'], PHP_URL_PATH);
        expect($app->handle('GET', $path, $signed, ['Range' => 'bytes=0-3'])->status === 206, 'real Range');
        expect($app->handle('HEAD', $path, $signed)->status === 200, 'signed HEAD');
        expect($app->handle('GET', $path, $signed, ['Range' => 'bytes=999999999-'])->status === 416, 'signed 416');
        $tampered = $signed; $tampered['sid'] = (string)($sessionId + 1);
        expect($app->handle('GET', $path, $tampered)->status === 403, 'cannot move capability to another session');
        unset($tampered['sid']);
        expect($app->handle('GET', $path, $tampered)->status === 403, 'cannot downgrade signature');
        $suggestHeaders = ['Authorization' => 'Bearer ' . $access, 'Content-Type' => 'multipart/form-data; boundary=ci'];
        $fields = ['service' => 'yandex', 'track_id' => '199999991', 'title' => 'Stage10 suggestion', 'artist' => 'CI'];
        $suggest = $app->handle('POST', '/api/v1/track-requests', [], $suggestHeaders, fields: $fields);
        expect($suggest->status === 202, 'suggestion without file or rights');
        $first = json_decode($suggest->body, true);
        $again = json_decode($app->handle('POST', '/api/v1/track-requests', [], $suggestHeaders, fields: $fields)->body, true);
        expect($first['request_id'] === $again['request_id'], 'account suggestion retry deduplicated');
        $hash = hash_hmac('sha256', 'contribution.user.' . $id, $cfg['analytics_privacy_key']);
        $pdo->prepare('DELETE FROM track_requests WHERE uploader_hash = ?')->execute([$hash]);
        $pdo->prepare('DELETE FROM upload_rate_buckets WHERE identity_hash = ?')->execute([$hash]);
        $originalWindow = $pdo->query('SELECT valid_from, valid_until FROM account_trials WHERE user_id = ' . $id)->fetch();
        $pdo->exec('UPDATE account_trials SET valid_from = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 432001 SECOND), valid_until = DATE_SUB(UTC_TIMESTAMP(6), INTERVAL 1 SECOND) WHERE user_id = ' . $id);
        $pdo->exec('UPDATE entitlement_ledger l JOIN account_trials t ON t.ledger_id=l.id SET l.valid_from=t.valid_from, l.valid_until=t.valid_until WHERE t.user_id=' . $id);
        expect($app->handle('GET', $path, $signed)->status === 403, 'expired trial invalidates unexpired signature');
        expect($app->handle('GET', '/api/v1/resolve', $query, $headers)->status === 403, 'expired account denied');
        $restore = $pdo->prepare('UPDATE account_trials SET valid_from=?, valid_until=? WHERE user_id=?');
        $restore->execute([$originalWindow['valid_from'], $originalWindow['valid_until'], $id]);
        $pdo->exec('UPDATE entitlement_ledger l JOIN account_trials t ON t.ledger_id=l.id SET l.valid_from=t.valid_from, l.valid_until=t.valid_until WHERE t.user_id=' . $id);
        $missingRights = $app->handle('POST', '/api/v1/uploads', [], $suggestHeaders, fields: $fields);
        expect($missingRights->status === 415 && json_decode($missingRights->body, true)['error'] === 'rights_declaration_required', 'MP3 upload still requires rights');
        $pdo->prepare('DELETE FROM upload_rate_buckets WHERE identity_hash = ?')->execute([$hash]);
        $pending = $pdo->query("SELECT t.service_track_id, r.id FROM tracks t JOIN track_replacements r ON r.track_id=t.id WHERE r.status='pending' LIMIT 1")->fetch();
        if ($pending) {
            $notApproved = $app->handle('GET', '/api/v1/resolve', ['service'=>'yandex', 'track_id'=>$pending['service_track_id']], $headers);
            expect(!json_decode($notApproved->body, true)['found'], 'pending never resolves');
            expect($app->handle('GET', '/api/v1/audio/' . $pending['id'], $signed)->status === 404, 'pending never streams');
        }
        $pdo->exec('UPDATE user_sessions SET revoked_at = UTC_TIMESTAMP(6) WHERE id = ' . $sessionId);
        expect($app->handle('GET', $path, $signed)->status === 403, 'revoked session invalidates buffered seek/range');
        expect($app->handle('GET', '/api/v1/resolve', $query, $headers)->status === 401, 'revoked resolve denied');
    });
    run('Stage10 migration rerun preserves existing trial and catalog', function () use ($pdo, $runner, $catalogBefore): void {
        $before = $pdo->query('SELECT * FROM account_trials ORDER BY user_id')->fetchAll();
        expect($runner->run() === [], 'migration idempotent');
        expect($pdo->query('SELECT * FROM account_trials ORDER BY user_id')->fetchAll() === $before, 'trial deadlines preserved');
        expect($pdo->query('SELECT id, status, is_active, version FROM track_replacements ORDER BY id')->fetchAll() === $catalogBefore, 'catalog unchanged');
    });
} finally {
    if ($pdo->inTransaction()) $pdo->rollBack();
    foreach ($ids as $id) {
        foreach (['account_trials','entitlement_ledger','user_auth_events','user_sessions','user_devices','user_email_security','users'] as $table) {
            $column = $table === 'users' ? 'id' : 'user_id';
            $pdo->exec('DELETE FROM ' . $table . ' WHERE ' . $column . ' = ' . $id);
        }
    }
}
