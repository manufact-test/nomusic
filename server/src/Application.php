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
    private ?\PDO $database = null;
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
        } catch (\Throwable $error) {
            // Codes only: no credentials, SQL, filesystem paths or signed URLs.
            $code = $error instanceof \PDOException
                ? '_sqlstate_' . preg_replace('/[^A-Z0-9]/', '', (string)($error->errorInfo[0] ?? ''))
                    . '_driver_' . (int)($error->errorInfo[1] ?? 0)
                : '';
            error_log('CELIKOM service_unavailable' . $code);
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
            return (new AdminPanel($this->database(), $this->storage(), (bool)($this->config['billing_views_enabled'] ?? false),
                (bool)($this->config['reward_eligibility_enabled'] ?? false), $this->config))
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
            return (new AuthController(new AuthService($this->database(), $this->config)))
                ->handle($method, $path, $headers, $body);
        }
        if ($path==='/api/v1/support' || preg_match('#^/api/v1/support/([1-9][0-9]{0,17})$#D',$path,$supportMatch)) {
            if(!($this->config['auth_enabled']??false))return Response::json(404,['error'=>'not_found']);
            $pdo=$this->database();$session=(new BearerAuthenticator($pdo))->session($headers);
            if(!$session)return Response::json(401,['error'=>'invalid_session']);
            $support=new \Celikom\Support\SupportService($pdo,$this->config);
            try {
                if($method==='GET')$data=isset($supportMatch[1])?$support->thread((int)$supportMatch[1],(int)$session['user_id'],max(1,min(100000,(int)($query['message_page']??1)))):['tickets'=>$support->listForUser((int)$session['user_id'],max(1,min(100000,(int)($query['page']??1))))];
                elseif($method==='POST'&&$path==='/api/v1/support'){
                    if(strlen($body)>16000)throw new \InvalidArgumentException();
                    $data=json_decode($body,true,16,JSON_THROW_ON_ERROR);
                    if(!is_array($data)||!is_string($data['message']??null)||!is_string($data['request_key']??null))throw new \InvalidArgumentException();
                    if(!in_array($data['kind']??'general',['general','song'],true))throw new \InvalidArgumentException();
                    $report=($data['kind']??'general')==='song'?\Celikom\Support\SongReport::normalize($data['report']??null):null;
                    $data=['ticket_id'=>$support->create((int)$session['user_id'],$data['message'],$data['request_key'],$report)];
                }else return Response::json(405,['error'=>'method_not_allowed']);
                if(isset($data['tickets'])){$data['has_more']=count($data['tickets'])>5;$data['tickets']=array_slice($data['tickets'],0,5);}
                $response=new Response(200,['Content-Type'=>'application/json; charset=utf-8','Cache-Control'=>'no-store'],json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE));return $response;
            }catch(\InvalidArgumentException|\JsonException){return Response::json(400,['error'=>'invalid_request']);}
            catch(\DomainException $e){return Response::json($e->getMessage()==='rate_limited'?429:404,['error'=>$e->getMessage()==='rate_limited'?'rate_limited':'not_found']);}
        }
        if($path==='/api/v1/promos/redeem'){
            if(!($this->config['auth_enabled']??false)||!($this->config['entitlement_enabled']??false))return Response::json(404,['error'=>'not_found']);
            if($method!=='POST')return Response::json(405,['error'=>'method_not_allowed']);
            $pdo=$this->database();$session=(new BearerAuthenticator($pdo))->session($headers);
            if($session===null)return Response::json(401,['error'=>'invalid_session']);
            if(!(new \Celikom\Promo\PromoAttemptLimiter($pdo,(string)$this->config['analytics_privacy_key']))->allow((int)$session['user_id'],(string)$session['installation_id'],(string)($_SERVER['REMOTE_ADDR']??'unknown')))
                return Response::json(429,['error'=>'rate_limited']);
            try{
                if(strlen($body)>2048)throw new \InvalidArgumentException();
                $data=json_decode($body,true,16,JSON_THROW_ON_ERROR);
                if(!is_array($data)||array_keys($data)!==['code']||!is_string($data['code']))throw new \InvalidArgumentException();
                $result=(new \Celikom\Promo\PromoService($pdo))->redeem((int)$session['user_id'],$data['code']);
                $response=Response::json(200,$result);$response->headers['Cache-Control']='no-store';return $response;
            }catch(\JsonException|\InvalidArgumentException){return Response::json(400,['error'=>'invalid_promo']);}
            catch(\DomainException $e){return Response::json(409,['error'=>in_array($e->getMessage(),['promo_payment_pending','promo_lifetime_active','account_unavailable'],true)?$e->getMessage():'promo_unavailable']);}
        }
        if ($path === '/api/v1/rewards') {
            if (!($this->config['reward_eligibility_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
                return Response::json(404,['error'=>'not_found']);
            if ($method !== 'GET') return Response::json(405,['error'=>'method_not_allowed']);
            $pdo=$this->database();$session=(new BearerAuthenticator($pdo))->session($headers);
            if ($session===null) return Response::json(401,['error'=>'invalid_session']);
            $response=Response::json(200,(new \Celikom\Reward\RewardService($pdo))->summary($session['user_id']));
            $response->headers['Cache-Control']='no-store';return $response;
        }
        if (in_array($path,['/api/v1/referrals','/api/v1/referrals/code'],true)) {
            if (!($this->config['referrals_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
                return Response::json(404,['error'=>'not_found']);
            if (($path==='/api/v1/referrals' ? 'GET' : 'POST')!==$method)
                return Response::json(405,['error'=>'method_not_allowed']);
            $pdo=$this->database();$session=(new BearerAuthenticator($pdo))->session($headers);
            if ($session===null) return Response::json(401,['error'=>'invalid_session']);
            $service=new \Celikom\Referral\ReferralService($pdo);
            if ($method==='POST') {
                if ($body!=='' && $body!=='{}') return Response::json(400,['error'=>'invalid_request']);
                $service->code($session['user_id']);
            }
            $response=Response::json(200,$service->summary($session['user_id']));
            $response->headers['Cache-Control']='no-store';return $response;
        }
        if ($method === 'GET' && $path === '/api/v1/subscription') {
            if (!($this->config['billing_views_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
                return Response::json(404, ['error'=>'not_found']);
            $pdo=$this->database();
            $session=(new BearerAuthenticator($pdo))->session($headers);
            if ($session===null) return Response::json(401, ['error'=>'invalid_session']);
            $response=Response::json(200,(new \Celikom\Billing\SubscriptionView($pdo))->forUser($session['user_id']));
            $response->headers['Cache-Control']='no-store';
            return $response;
        }
        if ($method === 'GET' && $path === '/api/v1/entitlement') {
            if (!($this->config['entitlement_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
                return Response::json(404, ['error' => 'not_found']);
            $pdo = $this->database();
            $user = (new BearerAuthenticator($pdo))->session($headers);
            if ($user === null) return Response::json(401, ['error' => 'invalid_session']);
            return Response::json(200, (new EntitlementService($pdo))->check($user['user_id'])->json());
        }
        if ($method === 'GET' && $path === '/api/v1/config') {
            $incident = ($this->config['entitlement_enabled'] ?? false)
                ? (new \Celikom\Incident\IncidentService($this->database()))->state()
                : ['active'=>false,'service'=>'yandex'];
            return Response::json(200, [
                'incident' => $incident,
                'api_version' => 1,
                'support_email' => filter_var($this->config['mail_from']??'',FILTER_VALIDATE_EMAIL) ? $this->config['mail_from'] : '',
                'minimum_extension_version' => $this->config['minimum_extension_version'],
                'upload_enabled' => (bool)($this->config['user_uploads_enabled'] ?? false) && (bool)($this->config['entitlement_enabled'] ?? false),
                'max_upload_size' => $this->config['max_audio_size'],
                'allowed_audio_formats' => ['mp3', 'wav'],
                'maintenance' => false,
                'features' => ['replacements' => $this->config['api_enabled'], 'analytics' => $this->config['analytics_enabled'], 'auth' => (bool)($this->config['auth_enabled'] ?? false), 'entitlement' => (bool)($this->config['entitlement_enabled'] ?? false), 'billing_views'=>(bool)($this->config['billing_views_enabled'] ?? false), 'referrals'=>(bool)($this->config['referrals_enabled'] ?? false), 'rewards'=>(bool)($this->config['reward_eligibility_enabled'] ?? false)],
                'resolve_cache_ttl_seconds' => ResolveCachePolicy::positive($this->config['resolve_cache_ttl_seconds'] ?? 120, $this->config['audio_token_ttl']),
                'negative_cache_ttl_seconds' => ResolveCachePolicy::negative($this->config['negative_cache_ttl_seconds'] ?? 15),
            ]);
        }
        if ($method === 'GET' && $path === '/api/v1/tracks/version-status') {
            // Read-only presence for signed-in users, independent of the upload
            // switch and trial activation. Never provides playback credentials.
            if (!($this->config['auth_enabled'] ?? false)) return Response::json(404, ['error' => 'not_found']);
            $pdo = $this->database();
            if ((new BearerAuthenticator($pdo))->session($headers) === null) {
                return Response::json(401, ['error' => 'invalid_session']);
            }
            if (!is_string($query['service'] ?? null) || !is_string($query['track_id'] ?? null)) {
                return Response::json(400, ['error' => 'invalid_track']);
            }
            try {
                return Response::json(200, (new TrackUploadStatusService($pdo))->state($query['service'], $query['track_id']));
            } catch (\InvalidArgumentException) {
                return Response::json(400, ['error' => 'invalid_track']);
            }
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
                return Response::json(200, (new TrackUploadStatusService($this->database()))
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
            $pdo = $this->database();
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
            // Account limits survive session rotation. Independent device and IP
            // ceilings prevent multi-account bypass without collecting raw IPs.
            // REMOTE_ADDR is authoritative; forwarded headers are not trusted.
            if (!$owner) {
                $privacyKey = (string) $this->config['analytics_privacy_key'];
                $operation = $isUpload ? 'upload' : 'track_request';
                $deviceHash = hash_hmac('sha256', 'contribution.device.' . $access['installation_id'], $privacyKey);
                $ipHash = hash_hmac('sha256', 'contribution.ip.' . ($_SERVER['REMOTE_ADDR'] ?? 'unknown'), $privacyKey);
                if (!$limiter->check($deviceHash, $operation, $isUpload ? 20 : 40)
                    || !$limiter->check($ipHash, $operation, $isUpload ? 60 : 120)) {
                    return Response::json(429, ['error' => 'rate_limited']);
                }
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
                        ->upload($fields, $files['file'] ?? [], $ownerHash, $owner ? null : $access['user_id']);
                } else {
                    $data = (new TrackRequestService($pdo))->submit($fields, $ownerHash);
                }
                return Response::json(202, $data);
            } catch (\LengthException) {
                return Response::json(413, ['error' => 'upload_too_large']);
            } catch (\DomainException $error) {
                $code = $error->getMessage();
                return Response::json(in_array($code, ['idempotency_conflict', 'already_approved', 'track_pending', 'track_already_approved'], true) ? 409 : 415,
                    ['error' => in_array($code, ['invalid_mp3', 'invalid_m4a', 'duration_mismatch', 'rights_declaration_required', 'idempotency_conflict', 'already_approved', 'asset_conflict', 'track_pending', 'track_already_approved'], true)
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
                $result = (new ReportService($this->database(),
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
                    $this->config['negative_cache_ttl_seconds'] ?? 15))->resolve($query['service'], $query['track_id'], $access, ($query['audio_formats'] ?? '') === 'mp3,m4a'));
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
            $this->analytics ??= new AnalyticsEventService(new PdoEventRepository($this->database()), $this->config['analytics_privacy_key']);
            return Response::json(202, $this->analytics->batch($batch));
        }
        if (in_array($method, ['GET', 'HEAD'], true) && preg_match('~^/api/v1/audio/([1-9]\d{0,17})$~D', $path, $match)) {
            if (!$this->config['api_enabled']) {
                return Response::json(503, ['error' => 'replacements_disabled']);
            }
            return (new AudioController($this->catalog(), $this->storage(), $this->tokens(),
                ($this->config['entitlement_enabled'] ?? false) ? new AudioAccessService($this->database()) : null))->handle($method, (int) $match[1], $query, $headers);
        }
        return Response::json(404, ['error' => 'not_found']);
    }

    private function userAccess(array $headers): array|Response
    {
        if (!($this->config['entitlement_enabled'] ?? false) || !($this->config['auth_enabled'] ?? false))
            return Response::json(401, ['error' => 'unauthorized']);
        $pdo = $this->database();
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

    // One database connection per application/request, shared by catalog,
    // session and entitlement checks. Audio Range must not reconnect twice.
    private function database(): \PDO
    {
        return $this->database ??= Connection::open($this->config);
    }

    private function catalog(): CatalogRepository
    {
        return $this->catalog ??= new PdoCatalogRepository($this->database());
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
