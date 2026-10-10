<?php

declare(strict_types=1);

namespace Celikom;

use Celikom\Admin\AdminPanel;
use Celikom\Auth\AuthController;
use Celikom\Auth\AuthService;
use Celikom\Auth\BearerAuthenticator;
use Celikom\Entitlement\EntitlementService;
use Celikom\Entitlement\AudioAccessService;
use Celikom\Admin\ReportService;
use Celikom\Analytics\AnalyticsEventService;
use Celikom\Analytics\PdoEventRepository;
use Celikom\Application\AudioTokenService;
use Celikom\Application\ResolveService;
use Celikom\Application\UploadService;
use Celikom\Application\DeferredFingerprintService;
use Celikom\Application\UploadRateLimiter;
use Celikom\Application\TrackRequestService;
use Celikom\Application\TrackUploadStatusService;
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

    public function handle(string $method, string $path, array $query = [], array $headers = [], string $body = '', array $fields = [], array $files = []): Response
    {
        $headers = array_change_key_case($headers, CASE_LOWER);
        try {
            $response = $this->route($method, $path, $query, $headers, $body, $fields, $files);
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

    private function route(string $method, string $path, array $query, array $headers, string $body, array $fields, array $files): Response
    {
        if ($path === '/admin' || str_starts_with($path, '/admin/')) {
            if (!($this->config['admin_enabled'] ?? false)) {
                return Response::json(404, ['error' => 'not_found']);
            }
            return (new AdminPanel(Connection::open($this->config), $this->storage()))
                ->handle($method, $path, $query, $headers, $body);
        }
        if ($method === 'OPTIONS' && str_starts_with($path, '/api/v1/') && in_array($headers['origin'] ?? '', $this->config['allowed_origins'], true)) {
            return new Response(204, ['Access-Control-Allow-Methods' => 'GET, HEAD, POST, OPTIONS', 'Access-Control-Allow-Headers' => 'Authorization, Content-Type, Range', 'Access-Control-Max-Age' => '600']);
        }
        if ($method === 'GET' && in_array($path, ['/health', '/api/v1/health'], true)) {
            return Response::json(200, ['status' => 'ok', 'service' => 'celikom-api', 'version' => $this->config['version'], 'environment' => $this->config['environment']]);
        }
        if (str_starts_with($path, '/api/v1/auth/')) {
            if (!($this->config['auth_enabled'] ?? false)) {
                return Response::json(404, ['error' => 'not_found']);
            }
            return (new AuthController(new AuthService(Connection::open($this->config), $this->config)))
                ->handle($method, $path, $headers, $body);
        }
        if ($method === 'GET' && $path === '/api/v1/entitlement') {
            if (!($this->config['entitlement_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
                return Response::json(404, ['error' => 'not_found']);
            $pdo = Connection::open($this->config);
            $user = (new BearerAuthenticator($pdo))->session($headers);
            if ($user === null) return Response::json(401, ['error' => 'invalid_session']);
            return Response::json(200, (new EntitlementService($pdo))->check($user['user_id'])->json());
        }
        if ($method === 'GET' && $path === '/api/v1/config') {
            return Response::json(200, [
                'api_version' => 1,
                'minimum_extension_version' => $this->config['minimum_extension_version'],
                'upload_enabled' => (bool)($this->config['user_uploads_enabled'] ?? false) && (bool)($this->config['entitlement_enabled'] ?? false),
                'max_upload_size' => $this->config['max_audio_size'],
                'allowed_audio_formats' => ['mp3', 'wav'],
                'maintenance' => false,
                'features' => ['replacements' => $this->config['api_enabled'], 'analytics' => $this->config['analytics_enabled'], 'auth' => (bool)($this->config['auth_enabled'] ?? false), 'entitlement' => (bool)($this->config['entitlement_enabled'] ?? false)],
                'resolve_cache_ttl_seconds' => ResolveCachePolicy::positive($this->config['resolve_cache_ttl_seconds'] ?? 120, $this->config['audio_token_ttl']),
                'negative_cache_ttl_seconds' => ResolveCachePolicy::negative($this->config['negative_cache_ttl_seconds'] ?? 15),
            ]);
        }
        if ($method === 'GET' && $path === '/api/v1/tracks/upload-status') {
            // Only moderation presence, no asset or user data. Used to stop duplicate
            // submissions after the popup closes or the browser restarts.
            if ($this->config['user_uploads_enabled'] ?? false) {
                $access = $this->userAccess($headers);
                if ($access instanceof Response) return $access;
            } elseif (!($this->config['owner_uploads_enabled'] ?? false)) {
                return Response::json(404, ['error' => 'not_found']);
            }
            if (!is_string($query['service'] ?? null) || !is_string($query['track_id'] ?? null)) {
                return Response::json(400, ['error' => 'invalid_track']);
            }
            try {
                return Response::json(200, (new TrackUploadStatusService(Connection::open($this->config)))
                    ->state($query['service'], $query['track_id']));
            } catch (\InvalidArgumentException) {
                return Response::json(400, ['error' => 'invalid_track']);
            }
        }
        if ($method === 'POST' && in_array($path, ['/api/v1/uploads', '/api/v1/track-requests'], true)) {
            // Separate non-public owner credential: API_TEST_TOKEN is read-only.
            // No server-side writes are possible until the private gate is explicitly enabled.
            $secret = (string) ($this->config['owner_upload_token'] ?? '');
            $owner = ($this->config['owner_uploads_enabled'] ?? false) && strlen($secret) >= 40
                && hash_equals('Bearer ' . $secret, (string)($headers['authorization'] ?? ''));
            if (!$owner && !($this->config['user_uploads_enabled'] ?? false)) {
                return ($this->config['owner_uploads_enabled'] ?? false) && strlen($secret) >= 40
                    ? Response::json(401, ['error' => 'unauthorized'])
                    : Response::json(503, ['error' => 'uploads_disabled']);
            }
            $pdo = Connection::open($this->config);
            if ($owner) {
                $ownerHash = hash('sha256', $secret);
            } else {
                $access = $this->userAccess($headers);
                if ($access instanceof Response) return $access;
                // Stable account identity across refresh and independent devices.
                $ownerHash = hash_hmac('sha256', 'contribution.user.' . $access['user_id'],
                    $this->config['analytics_privacy_key']);
            }
            $limiter = new UploadRateLimiter($pdo);
            $isUpload = $path === '/api/v1/uploads';
            if (!$limiter->check($ownerHash, $isUpload ? 'upload' : 'track_request', $isUpload ? 10 : 20)) {
                return Response::json(429, ['error' => 'rate_limited']);
            }
            if ($isUpload && isset($headers['content-length'])
                && ctype_digit((string) $headers['content-length'])
                && (float) $headers['content-length'] > (int) $this->config['max_audio_size'] + 1048576) {
                return Response::json(413, ['error' => 'upload_too_large']);
            }
            if (!str_starts_with(strtolower((string) ($headers['content-type'] ?? '')), 'multipart/form-data')) {
                return Response::json(415, ['error' => 'multipart_required']);
            }
            try {
                if ($isUpload) {
                    $data = (new UploadService($pdo, $this->storage(),
                        (int) $this->config['max_audio_size'], null, new DeferredFingerprintService($pdo)))
                        ->upload($fields, $files['file'] ?? [], $ownerHash);
                } else {
                    $data = (new TrackRequestService($pdo))->submit($fields, $ownerHash);
                }
                return Response::json(202, $data);
            } catch (\LengthException) {
                return Response::json(413, ['error' => 'upload_too_large']);
            } catch (\DomainException $error) {
                $code = $error->getMessage();
                return Response::json(in_array($code, ['idempotency_conflict', 'already_approved', 'track_pending', 'track_already_approved'], true) ? 409 : 415,
                    ['error' => in_array($code, ['invalid_mp3', 'rights_declaration_required', 'idempotency_conflict', 'already_approved', 'asset_conflict', 'track_pending', 'track_already_approved'], true)
                        ? $code : 'upload_rejected']);
            } catch (\InvalidArgumentException) {
                return Response::json(400, ['error' => 'invalid_upload']);
            }
        }
        if ($method === 'POST' && $path === '/api/v1/report') {
            // Pre-account private test only; Stage 9 will replace this with user auth.
            if (!($this->config['owner_reports_enabled'] ?? false)) {
                return Response::json(404, ['error' => 'not_found']);
            }
            $reportToken = (string) ($this->config['owner_report_token'] ?? '');
            if (strlen($reportToken) < 40 || !hash_equals('Bearer ' . $reportToken,
                (string) ($headers['authorization'] ?? ''))) {
                return Response::json(401, ['error' => 'unauthorized']);
            }
            if (strlen($body) > 4096) return Response::json(413, ['error' => 'report_too_large']);
            if (!str_starts_with(strtolower((string)($headers['content-type'] ?? '')), 'application/json')) {
                return Response::json(415, ['error' => 'json_required']);
            }
            try {
                $data = json_decode($body, true, 16, JSON_THROW_ON_ERROR);
                if (!is_array($data)) throw new \InvalidArgumentException('invalid_report');
                $result = (new ReportService(Connection::open($this->config),
                    (string) $this->config['analytics_privacy_key']))->submit($data);
                return Response::json(202, $result);
            } catch (\JsonException|\InvalidArgumentException) {
                return Response::json(400, ['error' => 'invalid_report']);
            } catch (\DomainException $error) {
                return Response::json($error->getMessage() === 'report_rate_limited' ? 429 : 404,
                    ['error' => 'report_unavailable']);
            }
        }
        if (($method === 'GET' && $path === '/api/v1/resolve') || ($method === 'POST' && $path === '/api/v1/events/batch')) {
            $access = null;
            if (!$this->authorized($headers)) {
                $access = $this->userAccess($headers);
                if ($access instanceof Response) return $access;
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
                    $this->config['negative_cache_ttl_seconds'] ?? 15))->resolve($query['service'], $query['track_id'], $access));
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
            return (new AudioController($this->catalog(), $this->storage(), $this->tokens(),
                ($this->config['entitlement_enabled'] ?? false) ? new AudioAccessService(Connection::open($this->config)) : null))->handle($method, (int) $match[1], $query, $headers);
        }
        return Response::json(404, ['error' => 'not_found']);
    }

    private function userAccess(array $headers): array|Response
    {
        if (!($this->config['entitlement_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
            return Response::json(401, ['error' => 'unauthorized']);
        $pdo = Connection::open($this->config);
        $session = (new BearerAuthenticator($pdo))->session($headers);
        if ($session === null) return Response::json(401, ['error' => 'invalid_session']);
        $entitlement = (new EntitlementService($pdo))->check($session['user_id']);
        if (!$entitlement->allowed) return Response::json(403, ['error' => 'access_denied', 'entitlement' => $entitlement->json()]);
        return $session + ['valid_until' => $entitlement->validUntil];
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
