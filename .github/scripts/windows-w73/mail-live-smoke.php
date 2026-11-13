<?php
declare(strict_types=1);
// A two-message live SMTP acceptance probe only; never writes to the CELIKOM DB.
// The recipient is passed over encrypted SSH stdin from a protected Actions secret.
ini_set('display_errors','0');
try {
    if (PHP_SAPI!=='cli') throw new RuntimeException('cli');
    $to=trim((string)stream_get_contents(STDIN,320));
    if (!filter_var($to,FILTER_VALIDATE_EMAIL) || preg_match('/[\x00\r\n]/',$to))
        throw new RuntimeException('test_recipient');
    $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
    if (!is_link($root.'/current')) throw new RuntimeException('current');
    $release=realpath($root.'/current');
    if ($release===false || !str_starts_with($release,$root.'/releases/'))
        throw new RuntimeException('release');
    require $release.'/bootstrap.php';
    $config=require $release.'/config/app.php';
    if (($config['environment']??'')!=='production' || !($config['auth_enabled']??false))
        throw new RuntimeException('production_guard');
    $mailer=new \Celikom\Auth\SmtpMailer($config);
    if (!$mailer->ready()) throw new RuntimeException('smtp_not_ready');
    $from=(string)$config['mail_from'];
    // Don't print actual addresses or hostnames, only the relation needed to diagnose routing.
    echo 'W73_SENDER_IS_SMTP_USERNAME='.(strcasecmp($from,(string)$config['mail_user'])===0?'YES':'NO')."\n";
    echo 'W73_TEST_TO_IS_SUPPORT_ADDRESS='.(strcasecmp($to,$from)===0?'YES':'NO')."\n";
    $ticket=random_int(800000000,999999999);
    $mailer->sendSupport($from,$ticket,'W73: безопасная проверка уведомления поддержки, без данных клиентов.',true);
    echo "W73_SMTP_SUPPORT_NOTIFICATION_ACCEPTED_250\n";
    $mailer->sendSupport($to,$ticket,'W73: безопасная проверка письма-ответа пользователю, без данных клиентов.',false);
    echo "W73_SMTP_USER_REPLY_ACCEPTED_250\n";
    echo "W73_SMTP_PROBE_INBOX_RECEIPT_NOT_VERIFIED\n";
} catch (\Throwable $e) {
    fwrite(STDERR,"W73_SMTP_PROBE_FAILED\n");
    exit(1);
}
