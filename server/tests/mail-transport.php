<?php
declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

use Celikom\Auth\SmtpMailer;

function mailExpect(bool $condition, string $label): void
{
    if (!$condition) throw new RuntimeException($label);
}

function mailReject(callable $action, string $label): void
{
    try {
        $action();
    } catch (RuntimeException $e) {
        mailExpect($e->getMessage() === 'mail_unavailable' && $e->getPrevious() === null, $label);
        return;
    }
    throw new RuntimeException($label);
}

$calls = [];
$config = [
    'environment' => 'test',
    'mail_transport' => 'brevo',
    'mail_brevo_api_key' => str_repeat('fixture-', 4),
    'mail_from' => 'sender@example.org',
    'mail_brevo_test_http' => static function (string $url, array $headers, string $json, string $purpose) use (&$calls): array {
        $calls[] = [$url, $headers, json_decode($json, true, 8, JSON_THROW_ON_ERROR), $purpose];
        return [201, '{"messageId":"fixture-id@example.org"}'];
    },
];
$mail = new SmtpMailer($config);
mailExpect($mail->ready(), 'Brevo fixture ready');
$mail->sendCode('recipient@example.org', '012345', 'verify');
$mail->sendCode('recipient@example.org', '987654', 'reset');
$mail->sendSupport('recipient@example.org', 42, 'Тест обращения', false);
mailExpect(count($calls) === 3, 'one request per mail');
foreach ($calls as [$url, $headers, $payload, $purpose]) {
    mailExpect($url === 'https://api.brevo.com/v3/smtp/email', 'fixed HTTPS endpoint');
    mailExpect(in_array('api-key: '.$config['mail_brevo_api_key'], $headers, true), 'key in header only');
    mailExpect($payload['sender'] === ['name'=>'CELIKOM','email'=>'sender@example.org'], 'sender');
    mailExpect($payload['to'] === [['email'=>'recipient@example.org']], 'single recipient');
    mailExpect(array_keys($payload) === ['sender','to','subject','textContent'], 'minimal plaintext payload');
    mailExpect(!str_contains(json_encode($payload), $config['mail_brevo_api_key']), 'no key in payload');
}
mailExpect($calls[0][3] === 'verify' && str_contains($calls[0][2]['textContent'], '012345'), 'verification code');
mailExpect($calls[1][3] === 'reset' && str_contains($calls[1][2]['textContent'], '987654'), 'reset code');
mailExpect($calls[2][3] === 'support' && str_contains($calls[2][2]['textContent'], 'Тест обращения'), 'support text');

foreach (['','short',"fixture-key-long\r\ninjected"] as $key) {
    $bad = $config; $bad['mail_brevo_api_key'] = $key;
    mailExpect(!(new SmtpMailer($bad))->ready(), 'invalid key');
}
$bad = $config; $bad['mail_from'] = 'invalid';
mailExpect(!(new SmtpMailer($bad))->ready(), 'invalid sender');
$bad = $config; $bad['mail_transport'] = '';
mailExpect(!(new SmtpMailer($bad))->ready(), 'explicit opt-in');
mailReject(fn() => $mail->sendCode('invalid', '123456', 'verify'), 'invalid recipient');
mailReject(fn() => $mail->sendCode('recipient@example.org', '12345', 'verify'), 'invalid challenge');
mailReject(fn() => $mail->sendCode('recipient@example.org', '123456', 'other'), 'invalid purpose');
mailExpect(count($calls) === 3, 'invalid inputs do not send');

foreach ([[200,'{"messageId":"id"}'],[302,'{}'],[400,'{}'],[401,'{}'],[429,'{}'],[503,'{}'],
    [201,'{}'],[201,'{"messageId":""}'],[201,'invalid-json'],[201,str_repeat('x',16385)]] as $failure) {
    $bad = $config; $attempts = 0;
    $bad['mail_brevo_test_http'] = static function () use ($failure, &$attempts): array {
        $attempts++;
        return $failure;
    };
    // Valid-looking SMTP settings must not trigger an implicit second delivery.
    $bad += ['mail_host'=>'smtp.example.org','mail_port'=>465,'mail_user'=>'fixture','mail_password'=>'fixture-password'];
    mailReject(fn() => (new SmtpMailer($bad))->sendCode('recipient@example.org', '123456', 'verify'), 'provider failure');
    mailExpect($attempts === 1, 'no ambiguous retries');
}
$bad = $config;
$bad['mail_brevo_test_http'] = static function (): array { throw new RuntimeException('secret provider detail'); };
mailReject(fn() => (new SmtpMailer($bad))->sendCode('recipient@example.org', '123456', 'reset'), 'provider error redacted');

$smtp = ['environment'=>'production','mail_transport'=>'smtp','mail_host'=>'smtp.example.org',
    'mail_port'=>587,'mail_user'=>'fixture','mail_password'=>'fixture-password','mail_from'=>'sender@example.org'];
mailExpect((new SmtpMailer($smtp))->ready(), 'existing SMTP configuration still supported');
$smtp['mail_port'] = 25;
mailExpect(!(new SmtpMailer($smtp))->ready(), 'SMTP rejects plaintext port');
$test = $config; $test['mail_transport'] = ''; $sink = 0;
$test['mail_test_sink'] = static function () use (&$sink): void { $sink++; };
(new SmtpMailer($test))->sendCode('recipient@example.org', '123456', 'verify');
mailExpect($sink === 1, 'existing auth/support test sink unchanged');
$test['environment'] = 'production';
mailExpect(!(new SmtpMailer($test))->ready(), 'test sink unavailable in production');
echo "CELIKOM_MAIL_TRANSPORT_TESTS_OK\n";
