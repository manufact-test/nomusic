<?php
declare(strict_types=1);
namespace Celikom\Auth;

/** Server-only HTTPS transport. Never logs provider responses, keys or mail contents. */
final class BrevoMailer
{
    private const ENDPOINT = 'https://api.brevo.com/v3/smtp/email';
    private const MAX_RESPONSE_BYTES = 16384;

    public function __construct(private readonly array $config) {}

    private function fixture(): ?\Closure
    {
        $fixture = $this->config['mail_brevo_test_http'] ?? null;
        return ($this->config['environment'] ?? '') === 'test' && $fixture instanceof \Closure ? $fixture : null;
    }

    public function ready(): bool
    {
        $key = $this->config['mail_brevo_api_key'] ?? '';
        return ($this->config['mail_transport'] ?? '') === 'brevo'
            && is_string($key) && preg_match('/^[\x21-\x7e]{16,512}$/D', $key) === 1
            && filter_var($this->config['mail_from'] ?? '', FILTER_VALIDATE_EMAIL) !== false
            && (function_exists('curl_init') || $this->fixture() !== null);
    }

    public function deliver(string $to, string $message, string $purpose, string $subject): void
    {
        if (!$this->ready() || !filter_var($to, FILTER_VALIDATE_EMAIL)
            || !in_array($purpose, ['verify', 'reset', 'support'], true)) {
            throw new \RuntimeException('mail_unavailable');
        }
        try {
            $json = json_encode([
                'sender' => ['name' => 'CELIKOM', 'email' => $this->config['mail_from']],
                'to' => [['email' => $to]],
                'subject' => $subject,
                'textContent' => $message,
            ], JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
            $headers = [
                'api-key: '.$this->config['mail_brevo_api_key'],
                'accept: application/json',
                'content-type: application/json',
            ];
            $fixture = $this->fixture();
            [$status, $body] = $fixture !== null
                ? $fixture(self::ENDPOINT, $headers, $json, $purpose)
                : $this->post($headers, $json, $purpose);
            if ($status !== 201 || !is_string($body) || strlen($body) > self::MAX_RESPONSE_BYTES) {
                throw new \RuntimeException('mail_unavailable');
            }
            $receipt = json_decode($body, true, 8, JSON_THROW_ON_ERROR);
            if (!is_array($receipt) || !is_string($receipt['messageId'] ?? null)
                || trim($receipt['messageId']) === '' || strlen($receipt['messageId']) > 1024) {
                throw new \RuntimeException('mail_unavailable');
            }
        } catch (\Throwable) {
            // Provider errors may contain recipient PII or credential details.
            // The caller receives only a stable, generic failure; no blind retry.
            throw new \RuntimeException('mail_unavailable');
        }
    }

    private function post(array $headers, string $json, string $purpose): array
    {
        $curl = curl_init(self::ENDPOINT);
        if ($curl === false) throw new \RuntimeException('mail_unavailable');
        $body = '';
        try {
            $ok = curl_setopt_array($curl, [
                CURLOPT_POST => true,
                CURLOPT_HTTPHEADER => $headers,
                CURLOPT_POSTFIELDS => $json,
                CURLOPT_CONNECTTIMEOUT => 3,
                CURLOPT_TIMEOUT => $purpose === 'support' ? 6 : 10,
                CURLOPT_SSL_VERIFYPEER => true,
                CURLOPT_SSL_VERIFYHOST => 2,
                CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
                CURLOPT_FOLLOWLOCATION => false,
                CURLOPT_PROXY => '',
                CURLOPT_VERBOSE => false,
                CURLOPT_WRITEFUNCTION => static function ($handle, string $chunk) use (&$body): int {
                    if (strlen($body) + strlen($chunk) > self::MAX_RESPONSE_BYTES) return 0;
                    $body .= $chunk;
                    return strlen($chunk);
                },
            ]);
            if (!$ok || curl_exec($curl) === false) throw new \RuntimeException('mail_unavailable');
            return [(int)curl_getinfo($curl, CURLINFO_RESPONSE_CODE), $body];
        } finally {
            curl_close($curl);
        }
    }
}
