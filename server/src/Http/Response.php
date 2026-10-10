<?php

declare(strict_types=1);

namespace Celikom\Http;

final class Response
{
    /** @param array<string, string> $headers */
    public function __construct(
        public readonly int $status,
        public array $headers = [],
        public readonly string $body = '',
        private readonly ?\Closure $stream = null,
    ) {
    }

    /** @param array<string, mixed> $payload */
    public static function json(int $status, array $payload): self
    {
        return new self($status, [
            'Content-Type' => 'application/json; charset=utf-8',
            'Cache-Control' => 'no-store',
        ], json_encode($payload, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES));
    }

    public function emitBody(): void
    {
        if ($this->stream !== null) {
            ($this->stream)();
        } else {
            echo $this->body;
        }
    }
}
