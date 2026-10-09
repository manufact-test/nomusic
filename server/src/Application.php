<?php

declare(strict_types=1);

namespace Celikom;

use Celikom\Analytics\AnalyticsEventService;
use Celikom\Analytics\PdoEventRepository;
use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Application\ResolveCachePolicy;
use Celikom\Database\Connection;
use Celikom\Http\AudioController;
use Celikom\Http\Response;
use Celikom\Repositories\CatalogRepository;
use Celikom\Repositories\PdoCatalogRepository;
use Celikom\Storage\LocalStorageAdapter;
use Celikom\Storage\StorageAdapter;

final class Application
{
    public function __construct(private readonly array $config, private ?CatalogRepository $catalog = null, private ?StorageAdapter $storage = null, private ?AnalyticsEventService $analytics = null)
    {
    }

    public function handle(string $method, string $path, array $query = [], array $headers = [], string $body = ''): Response
    {
        $headers = array_change_key_case($headers, CASE_LOWER);
        try {
            $response = $this->route($method, $path, $query, $headers, $body);
        } catch (\InvalidArgumentException) {
            $response = Response::json(400, ['error' => 'invalid_request']);
        } catch (\Throwable) {
            error_log('CELIKOM service_unavailable');
            $response = Response::json(503, ['error' => 'service_unavailable']);
        }
        $response->headers['X-Content-Type-Options'] = 'nosniff';
        $response->headers['Referrer-Policy'] = 'no-referrer';
        if (in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)) {
            $response->headers['Access-Control-Allow-Origin'] = $headers['origin'];
            $response->headers['Access-Control-Expose-Headers'] = 'Accept-Ranges, Content-Range, Content-Length, ETag';
            $response->headers['Vary'] = 'Origin';
        }
        return $response;
    }

    private function route(string $method, string $path, array $query, array $headers, string $body): Response
    {
        if ($method === 'OPTIONS' && str_starts_with($path, '/api/v1/') && in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)) {
            return new Response(204, ['Access-Control-Allow-Methods' => 'GET, HEAD, POST, OPTIONS', 'Access-Control-Allow-Headers' => 'Authorization, Content-Type, Range', 'Access-Control-Max-Age' => '600']);
        }
        if ($method === 'GET' && in_array($path, ['/health', '/api/v1/health'], true)) {
            return Response::json(200, ['status' => 'ok', 'service' => 'celikom-api', 'version' => $this->config['version'], 'environment' => $this->config['environment']]);
        }
        if ($method === 'GET' && $path === '/api/v1/config') {
            return Response::json(200, [
                'api_version' => 1,
                'minimum_extension_version' => $this->config['minimum_extension_version'],
                'upload_enabled' => false,
                'max_upload_size' => $this->config['max_audio_size'],
                'allowed_audio_formats' => ['mp3', 'wav'],
                'maintenance' => false,
                'features' => ['replacements' => $this->config['api_enabled'], 'analytics' => $this->config['analytics_enabled']],
                'resolve_cache_ttl_seconds' => ResolveCachePolicy::positive($this->config['resolve_cache_ttl_seconds'] ?? 120, $this->config['audio_token_ttl']),
                'negative_cache_ttl_seconds' => ResolveCachePolicy::negative($this->config['negative_cache_ttl_seconds'] ?? 15),
            ]);
        }
        if (($method === 'GET' && $path === '/api/v1/resolve') || ($method === 'POST' && $path === '/api/v1/events/batch')) {
            if (!$this->authorized($headers)) {
                return Response::json(401, ['error' => 'unauthorized']);
            }
            if ($path === '/api/v1/resolve') {
                if (!$this->config['api_enabled']) {
                    return Response::json(503, ['error' => 'replacements_disabled']);
                }
                if (!is_string($query['service'] ?? null) || !is_string($query['track_id'] ?? null)) {
                    return Response::json(400, ['error' => 'invalid_track']);
                }
                return Response::json(200, (new ResolveService($this->catalog(), $this->storage(), $this->tokens(),
                    $this->config['resolve_cache_ttl_seconds'] ?? 120,
                    $this->config['negative_cache_ttl_seconds'] ?? 15))->resolve($query['service'], $query['track_id']));
            }
            if (!$this->config['analytics_enabled']) {
                return Response::json(503, ['error' => 'analytics_disabled']);
            }
            if (strlen($body) > 65536) {
                return Response::json(413, ['error' => 'batch_too_large']);
            }
            if (!str_starts_with(strtolower($headers['content-type'] ?? ''), 'application/json')) {
                return Response::json(415, ['error' => 'json_required']);
            }
            try {
                $batch = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
            } catch (\JsonException) {
                return Response::json(400, ['error' => 'invalid_json']);
            }
            if (!is_array($batch)) {
                return Response::json(400, ['error' => 'invalid_event_batch']);
            }
            $this->analytics ??= new AnalyticsEventService(new PdoEventRepository(Connection::open($this->config)), $this->config['analytics_privacy_key']);
            return Response::json(202, $this->analytics->batch($batch));
        }
        if (in_array($method, ['GET', 'HEAD'], true) && preg_match('~^/api/v1/audio/([1-9]\d{0,17})$~D', $path, $match)) {
            if (!$this->config['api_enabled']) {
                return Response::json(503, ['error' => 'replacements_disabled']);
            }
            return (new AudioController($this->catalog(), $this->storage(), $this->tokens()))->handle($method, (int) $match[1], $query, $headers);
        }
        return Response::json(404, ['error' => 'not_found']);
    }

    private function authorized(array $headers): bool
    {
        $token = $this->config['test_api_token'];
        // Private test access until the account and entitlement stages.
        return strlen($token) >= 24 && hash_equals('Bearer ' . $token, $headers['authorization'] ?? '');
    }

    private function catalog(): CatalogRepository
    {
        return $this->catalog ??= new PdoCatalogRepository(Connection::open($this->config));
    }

    private function storage(): StorageAdapter
    {
        if ($this->storage !== null) {
            return $this->storage;
        }
        if ($this->config['storage_driver'] !== 'local') {
            throw new \RuntimeException('unsupported_storage_driver');
        }
        $adapter = new LocalStorageAdapter($this->config['storage_path']);
        $path = realpath($this->config['storage_path']);
        $public = realpath(dirname(__DIR__) . '/public');
        if ($path !== false && $public !== false && ($path === $public || str_starts_with($path, $public . '/'))) {
            throw new \RuntimeException('storage_must_be_private');
        }
        return $this->storage = $adapter;
    }

    private function tokens(): AudioTokenService
    {
        return new AudioTokenService($this->config['audio_signing_key'], $this->config['audio_token_ttl']);
    }
}
