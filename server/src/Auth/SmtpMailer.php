<?php
declare(strict_types=1);
namespace Celikom\Auth;

/** Private credentials are supplied from Hostinger's env; SMTP TLS is required. */
final class SmtpMailer
{
    public function __construct(private readonly array $config) {}

    public function ready(): bool
    {
        if (($this->config['environment'] ?? '') === 'test'
            && ($this->config['mail_test_sink'] ?? null) instanceof \Closure) return true;
        return ($this->config['mail_transport'] ?? '') === 'smtp'
            && preg_match('/^[a-zA-Z0-9.-]{4,200}$/D', (string)($this->config['mail_host'] ?? ''))
            && in_array((int)($this->config['mail_port'] ?? 0), [465, 587], true)
            && strlen((string)($this->config['mail_user'] ?? '')) > 2
            && strlen((string)($this->config['mail_password'] ?? '')) > 8
            && filter_var($this->config['mail_from'] ?? '', FILTER_VALIDATE_EMAIL);
    }

    /** Sends only fixed-purpose six-digit challenge messages, never arbitrary markup. */
    public function sendCode(string $to, string $code, string $purpose): void
    {
        if (!$this->ready() || !filter_var($to, FILTER_VALIDATE_EMAIL)
            || !preg_match('/^[0-9]{6}$/D',$code)
            || !in_array($purpose, ['verify','reset'], true)) throw new \RuntimeException('mail_unavailable');
        $message = $purpose === 'verify'
            ? "Код подтверждения почты CELIKOM: $code\nСрок действия — 10 минут.\nЕсли вы не регистрировались, проигнорируйте это письмо."
            : "Код восстановления пароля CELIKOM: $code\nСрок действия — 10 минут.\nЕсли вы не запрашивали восстановление, проигнорируйте это письмо.";
        if (($this->config['environment'] ?? '') === 'test'
            && ($this->config['mail_test_sink'] ?? null) instanceof \Closure) {
            ($this->config['mail_test_sink'])($to, $message, $purpose);
            return;
        }
        $host = (string)$this->config['mail_host'];
        $port = (int)$this->config['mail_port'];
        $ssl = ['ssl'=>['verify_peer'=>true,'verify_peer_name'=>true,'peer_name'=>$host,'allow_self_signed'=>false]];
        $socket = @stream_socket_client(($port===465?'ssl://':'tcp://').$host.':'.$port,
            $errno,$errstr,12,STREAM_CLIENT_CONNECT,stream_context_create($ssl));
        if (!$socket) throw new \RuntimeException('mail_unavailable');
        stream_set_timeout($socket, 12);
        try {
            $read = static function(int $want) use ($socket): void {
                do {
                    $line = fgets($socket, 1024);
                    if (!is_string($line) || !preg_match('/^([0-9]{3})([- ])/', $line, $m)) {
                        throw new \RuntimeException('smtp_unavailable');
                    }
                    $code = (int)$m[1];
                    if ($m[2] === ' ') break;
                } while (true);
                if ($code !== $want) throw new \RuntimeException('smtp_unavailable');
            };
            $send = static function(string $line) use ($socket): void {
                if (fwrite($socket,$line."\r\n") === false) throw new \RuntimeException('smtp_unavailable');
            };
            $read(220);
            $send('EHLO celikom.local'); $read(250);
            if ($port===587) {
                $send('STARTTLS'); $read(220);
                if (@stream_socket_enable_crypto($socket,true,STREAM_CRYPTO_METHOD_TLSv1_2_CLIENT | STREAM_CRYPTO_METHOD_TLSv1_3_CLIENT) !== true) {
                    throw new \RuntimeException('smtp_tls_required');
                }
                $send('EHLO celikom.local'); $read(250);
            }
            $send('AUTH LOGIN'); $read(334);
            $send(base64_encode((string)$this->config['mail_user'])); $read(334);
            $send(base64_encode((string)$this->config['mail_password'])); $read(235);
            $from = (string)$this->config['mail_from'];
            $send('MAIL FROM:<'.$from.'>'); $read(250);
            $send('RCPT TO:<'.$to.'>'); $read(250);
            $send('DATA'); $read(354);
            $subject = base64_encode($purpose==='verify'?'CELIKOM — подтверждение почты':'CELIKOM — восстановление пароля');
            $headers = "From: CELIKOM <".$from.">\r\nTo: <".$to.">\r\n"
                ."Subject: =?UTF-8?B?".$subject."?=\r\n"
                ."MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\n"
                ."Content-Transfer-Encoding: base64\r\n";
            $data = $headers."\r\n".chunk_split(base64_encode($message), 76, "\r\n");
            if (fwrite($socket,$data."\r\n.\r\n") === false) throw new \RuntimeException('smtp_unavailable');
            $read(250);
            $send('QUIT');
        } finally { fclose($socket); }
    }
}
