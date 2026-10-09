<?php

declare(strict_types=1);

namespace Celikom\Auth;

use Celikom\Http\Response;

final class AuthController
{
    public function __construct(private readonly AuthService $auth)
    {
    }

    public function handle(string $method, string $path, array $headers, string $rawBody): Response
    {
        if (!in_array($path, ['/api/v1/auth/register', '/api/v1/auth/login',
            '/api/v1/auth/refresh', '/api/v1/auth/logout', '/api/v1/auth/me',
            '/api/v1/auth/sessions', '/api/v1/auth/sessions/revoke', '/api/v1/auth/activate'], true)) {
            return Response::json(404, ['error' => 'not_found']);
        }
        $get = in_array($path, ['/api/v1/auth/me', '/api/v1/auth/sessions'], true);
        if (($get ? 'GET' : 'POST') !== $method) return Response::json(405, ['error' => 'method_not_allowed']);
        $input = [];
        if (!$get) {
            if (!str_starts_with(strtolower($headers['content-type'] ?? ''), 'application/json')) {
                return Response::json(415, ['error' => 'json_required']);
            }
            if (strlen($rawBody) > 8192) return Response::json(413, ['error' => 'request_too_large']);
            try {
                $input = json_decode($rawBody, true, 8, JSON_THROW_ON_ERROR);
                if (!is_array($input) || array_is_list($input)) throw new \InvalidArgumentException();
            } catch (\JsonException|\InvalidArgumentException) {
                return Response::json(400, ['error' => 'invalid_request']);
            }
        }
        try {
            $access = preg_match('/^Bearer ([0-9a-f]{64})$/D', $headers['authorization'] ?? '', $m) ? $m[1] : '';
            $result = match ($path) {
                '/api/v1/auth/register' => $this->auth->register($input, $_SERVER['REMOTE_ADDR'] ?? 'unknown'),
                '/api/v1/auth/login' => $this->auth->login($input, $_SERVER['REMOTE_ADDR'] ?? 'unknown'),
                '/api/v1/auth/refresh' => $this->auth->refresh($input),
                '/api/v1/auth/logout' => $this->auth->logout($input),
                '/api/v1/auth/me' => $this->auth->me($access),
                '/api/v1/auth/sessions' => $this->auth->sessions($access),
                '/api/v1/auth/sessions/revoke' => $this->auth->revoke($access, $input),
                '/api/v1/auth/activate' => $this->auth->activate($access),
            };
            return Response::json(in_array($path, ['/api/v1/auth/register'], true) ? 201 : 200, $result,
                ['Cache-Control' => 'no-store']);
        } catch (\InvalidArgumentException) {
            return Response::json(400, ['error' => 'invalid_request']);
        } catch (\DomainException $error) {
            $code = $error->getMessage();
            $status = match ($code) {
                'rate_limited' => 429,
                'weak_password' => 422,
                'account_unavailable' => 409,
                'account_disabled' => 403,
                default => 401
            };
            return Response::json($status, ['error' => in_array($code,
                ['rate_limited','weak_password','account_unavailable','account_disabled','invalid_credentials'], true)
                ? $code : 'invalid_session'], ['Cache-Control' => 'no-store']);
        }
    }
}
