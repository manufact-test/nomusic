<?php

declare(strict_types=1);

namespace Celikom;

final class Application
{
    /**
     * @param array{environment: string, debug: bool, version: string} $config
     */
    public function __construct(private readonly array $config)
    {
    }

    /**
     * @return array{status: int, headers: array<string, string>, body: string}
     */
    public function handle(string $method, string $path): array
    {
        if ($method === 'GET' && $path === '/health') {
            return $this->json(200, [
                'status' => 'ok',
                'service' => 'celikom-api',
                'version' => $this->config['version'],
                'environment' => $this->config['environment'],
            ]);
        }

        return $this->json(404, [
            'error' => 'not_found',
        ]);
    }

    /**
     * @param array<string, scalar> $payload
     * @return array{status: int, headers: array<string, string>, body: string}
     */
    private function json(int $status, array $payload): array
    {
        $body = json_encode($payload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES);

        return [
            'status' => $status,
            'headers' => [
                'Content-Type' => 'application/json; charset=utf-8',
                'Cache-Control' => 'no-store',
            ],
            'body' => $body,
        ];
    }
}
