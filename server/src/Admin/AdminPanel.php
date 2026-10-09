<?php

declare(strict_types=1);

namespace Celikom\Admin;

use Celikom\Http\ByteRange;
use Celikom\Http\Response;
use Celikom\Storage\StorageAdapter;

/** Minimal server-rendered, default-off Stage 8 operator console. */
final class AdminPanel
{
    public function __construct(private readonly \PDO $pdo, private readonly StorageAdapter $storage) {}

    public function handle(string $method, string $path, array $query, array $headers, string $body): Response
    {
        $auth = new AdminAuth($this->pdo);
        if ($path === '/admin/login') {
            if ($method === 'GET') {
                $nonce = bin2hex(random_bytes(32));
                return $this->page($this->loginPage($nonce),
                    ['Set-Cookie' => AdminAuth::cookie(AdminAuth::LOGIN_COOKIE, $nonce, 600)]);
            }
            if ($method === 'POST') {
                $form = $this->form($headers, $body);
                $nonce = AdminAuth::readCookie($headers, AdminAuth::LOGIN_COOKIE);
                if (!preg_match('/^[a-f0-9]{64}$/D', $nonce)
                    || !is_string($form['csrf'] ?? null)
                    || !hash_equals($nonce, $form['csrf'])) {
                    return $this->page('<h1>Сессия входа истекла</h1><p><a href="/admin/login">Повторить вход</a></p>', status: 403);
                }
                $result = $auth->login((string)($form['login'] ?? ''), (string)($form['password'] ?? ''),
                    (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
                if ($result === null) return $this->page('<h1>Вход не выполнен</h1><p><a href="/admin/login">Попробовать снова</a></p>', status: 401);
                return new Response(303, ['Location'=>'/admin',
                    'Set-Cookie'=>AdminAuth::cookie(AdminAuth::COOKIE, $result['token'], 21600),
                    'Cache-Control'=>'no-store']);
            }
            return Response::json(405, ['error'=>'method_not_allowed']);
        }
        $admin = $auth->authenticate($headers);
        if ($admin === null) {
            if (str_starts_with($path, '/admin/audio/')) return Response::json(403, ['error'=>'forbidden']);
            return new Response(303, ['Location'=>'/admin/login', 'Cache-Control'=>'no-store']);
        }
        if ($path === '/admin/logout' && $method === 'POST') {
            $form = $this->form($headers, $body);
            if (!AdminAuth::validCsrf($admin, $form['csrf'] ?? null)) return Response::json(403, ['error'=>'csrf_failed']);
            $auth->logout($headers);
            return new Response(303, ['Location'=>'/admin/login',
                'Set-Cookie'=>AdminAuth::cookie(AdminAuth::COOKIE, '', 0),
                'Cache-Control'=>'no-store']);
        }
        if ($path === '/admin/action' && $method === 'POST') {
            if (!in_array($admin['role'], ['owner','moderator'], true)) return Response::json(403, ['error'=>'forbidden']);
            $form = $this->form($headers, $body);
            if (!AdminAuth::validCsrf($admin, $form['csrf'] ?? null)) return Response::json(403, ['error'=>'csrf_failed']);
            $id = $this->positiveInt($form['id'] ?? null);
            $action = $form['action'] ?? null;
            $kind = $form['kind'] ?? null;
            $reason = $form['reason'] ?? null;
            if (!$id || !is_string($action) || !is_string($kind) || !is_string($reason)) {
                return Response::json(400, ['error'=>'invalid_action']);
            }
            try {
                $moderation = new ModerationService($this->pdo, $this->storage);
                if ($kind === 'replacement') {
                    $expected = $this->nonnegativeInt($form['expected_active'] ?? null);
                    if ($expected === null) return Response::json(400, ['error'=>'invalid_action']);
                    $moderation->replacement($admin['id'], $id, $action, $reason, $expected,
                        ($form['rights_confirmed'] ?? null) === '1');
                } elseif ($kind === 'track_request') {
                    $moderation->trackRequest($admin['id'], $id, $action, $reason);
                } else {
                    return Response::json(400, ['error'=>'invalid_action']);
                }
                return new Response(303, ['Location'=>'/admin?tab=' . ($kind === 'track_request' ? 'requests' : 'uploads'),
                    'Cache-Control'=>'no-store']);
            } catch (\InvalidArgumentException) {
                return Response::json(400, ['error'=>'invalid_action']);
            } catch (\DomainException) {
                return Response::json(409, ['error'=>'moderation_conflict_or_unverified']);
            }
        }
        if (preg_match('~^/admin/audio/([1-9]\d{0,17})$~D', $path, $m)
            && in_array($method, ['GET','HEAD'], true)) {
            return $this->preview($method, (int)$m[1], $headers);
        }
        if (($path === '/admin' || $path === '/admin/') && $method === 'GET') {
            return $this->page($this->dashboard($admin, $query));
        }
        return Response::json(404, ['error'=>'not_found']);
    }

    private function form(array $headers, string $body): array
    {
        if (!str_starts_with(strtolower((string)($headers['content-type'] ?? '')), 'application/x-www-form-urlencoded')
            || strlen($body) > 8192) return [];
        parse_str($body, $params);
        return is_array($params) ? $params : [];
    }

    private function positiveInt(mixed $v): ?int
    {
        return is_string($v) && preg_match('/^[1-9]\d{0,17}$/D', $v) ? (int)$v : null;
    }

    private function nonnegativeInt(mixed $v): ?int
    {
        return $v === '0' ? 0 : $this->positiveInt($v);
    }

    private static function e(mixed $value): string
    {
        return htmlspecialchars((string)($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
    }

    private function page(string $inner, array $otherHeaders = [], int $status = 200): Response
    {
        $css = 'body{font-family:system-ui,sans-serif;background:#f4f6fa;color:#14213a;margin:0;padding:24px}'
            . 'main{max-width:1180px;margin:auto}.panel{background:white;border:1px solid #dfe4ee;'
            . 'padding:18px;border-radius:12px;margin:14px 0;overflow-wrap:anywhere}'
            . 'nav a{margin-right:16px}a{color:#2256a5}input,select,button,textarea{font:inherit;'
            . 'padding:7px;margin:4px;max-width:100%;box-sizing:border-box}button{cursor:pointer}'
            . 'label{display:inline-block;margin:4px}small{color:#53627c}audio{width:100%;max-width:500px}'
            . 'table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #e3e6ed;'
            . 'padding:8px;text-align:left;vertical-align:top}form{margin:9px 0}'
            . '@media(max-width:700px){body{padding:10px}table{display:block;overflow-x:auto}}';
        $html = '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            . '<meta name="viewport" content="width=device-width,initial-scale=1">'
            . '<title>CELIKOM · Admin</title><style>' . $css . '</style></head><body><main>'
            . $inner . '</main></body></html>';
        return new Response($status, array_merge([
            'Content-Type'=>'text/html; charset=utf-8','Cache-Control'=>'no-store',
            'Content-Security-Policy'=>"default-src 'none'; style-src 'unsafe-inline'; media-src 'self';"
                . " form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            'X-Frame-Options'=>'DENY','X-Robots-Tag'=>'noindex, nofollow'
        ], $otherHeaders), $html);
    }

    private function loginPage(string $csrf): string
    {
        return '<section class="panel"><h1>CELIKOM · Вход администратора</h1>'
            . '<form method="post" action="/admin/login">'
            . '<input type="hidden" name="csrf" value="' . self::e($csrf) . '">'
            . '<label>Логин <input name="login" autocomplete="username" required></label>'
            . '<label>Пароль <input type="password" name="password" autocomplete="current-password" required></label>'
            . '<button type="submit">Войти</button></form></section>';
    }

    private function dashboard(array $admin, array $query): string
    {
        $tab = is_string($query['tab'] ?? null) ? $query['tab'] : 'uploads';
        $allowed = ['uploads','requests','reports','audit'];
        if (!in_array($tab, $allowed, true)) $tab = 'uploads';
        $csrf = self::e($admin['csrf']);
        $html = '<h1>CELIKOM · Модерация</h1><p>Администратор: ' . self::e($admin['login'])
            . ' (' . self::e($admin['role']) . ')</p><nav><a href="/admin?tab=uploads">MP3</a>'
            . '<a href="/admin?tab=requests">Предложить песню</a>'
            . '<a href="/admin?tab=reports">Жалобы</a><a href="/admin?tab=audit">Журнал</a></nav>'
            . '<form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="' . $csrf
            . '"><button type="submit">Выйти</button></form>';
        $counts = $this->pdo->query("SELECT
            (SELECT COUNT(*) FROM track_replacements WHERE status='pending') AS pending_uploads,
            (SELECT COUNT(*) FROM track_requests WHERE status='pending') AS pending_requests,
            (SELECT COUNT(*) FROM reports WHERE status='pending') AS pending_reports")->fetch(\PDO::FETCH_ASSOC);
        $html .= '<section class="panel"><strong>На проверке:</strong> MP3 — '
            . (int)$counts['pending_uploads'] . ' · Предложения — ' . (int)$counts['pending_requests']
            . ' · Жалобы — ' . (int)$counts['pending_reports'] . '</section>';
        return $html . match ($tab) {
            'requests' => $this->requests($admin, $csrf),
            'reports' => $this->reports(),
            'audit' => $this->auditLog(),
            default => $this->uploads($admin, $csrf),
        };
    }

    private function uploads(array $admin, string $csrf): string
    {
        $rows = $this->pdo->query("SELECT r.id,r.status,r.is_active,r.version,r.track_id,
            t.service,t.service_track_id,t.artist,t.title,t.duration_ms AS original_duration_ms,
            a.duration_ms AS audio_duration_ms,a.mime_type,a.size_bytes,a.sha256,
            (SELECT q.id FROM track_replacements q WHERE q.track_id=r.track_id
                AND q.status='approved' AND q.is_active=1 AND q.disabled_at IS NULL LIMIT 1) AS active_id
            FROM track_replacements r JOIN tracks t ON t.id=r.track_id
            JOIN audio_assets a ON a.id=r.audio_asset_id
            ORDER BY FIELD(r.status,'pending','approved','rejected','disabled'),r.id DESC LIMIT 100")
            ->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<h2>Загруженные версии</h2><p><small>Новые файлы не публикуются без ручного одобрения и проверки прав.</small></p>';
        foreach ($rows as $r) {
            $id = (int)$r['id'];
            $html .= '<section class="panel"><h3>#'.$id.' · '.self::e($r['artist']).' — '.self::e($r['title'])
                . '</h3><p>Yandex Track ID: '.self::e($r['service_track_id'])
                . ' · Статус: <strong>'.self::e($r['status']).'</strong> · active: '.(int)$r['is_active'].'</p>'
                . '<p>Длительность трека: '.(int)$r['original_duration_ms']
                . ' мс · MP3: '.(int)$r['audio_duration_ms'].' мс · '.self::e($r['mime_type'])
                . ' · '.(int)$r['size_bytes'].' байт</p><p><small>SHA-256: '.self::e($r['sha256']).'</small></p>'
                . '<audio controls preload="none" src="/admin/audio/'.$id.'"></audio>';
            if (in_array($admin['role'], ['owner','moderator'], true)
                && ($r['status'] === 'pending' || ($r['status'] === 'approved' && (int)$r['is_active']===1))) {
                $html .= '<form method="post" action="/admin/action"><input type="hidden" name="csrf" value="'.$csrf.'">'
                    . '<input type="hidden" name="kind" value="replacement"><input type="hidden" name="id" value="'.$id.'">'
                    . '<input type="hidden" name="expected_active" value="'.(int)($r['active_id'] ?? 0).'">'
                    . '<label>Причина/проверка <input name="reason" required maxlength="500"></label>';
                if ($r['status'] === 'pending') {
                    $html .= '<label><input type="checkbox" name="rights_confirmed" value="1"> Права проверены</label>'
                        . '<button name="action" value="approve">Одобрить и активировать</button>'
                        . '<button name="action" value="reject">Отклонить</button>'
                        . '<button name="action" value="duplicate">Дубликат</button>'
                        . '<button name="action" value="wrong_track">Не тот трек</button>'
                        . '<button name="action" value="bad_quality">Плохое качество</button>';
                } else {
                    $html .= '<button name="action" value="disable">Отключить</button>';
                }
                $html .= '</form>';
            }
            $html .= '</section>';
        }
        return $html ?: '<p>Нет записей.</p>';
    }

    private function requests(array $admin, string $csrf): string
    {
        $rows = $this->pdo->query("SELECT id,service,service_track_id,artist,title,status,created_at
            FROM track_requests ORDER BY FIELD(status,'pending','reviewed','rejected'),id DESC LIMIT 100")
            ->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<h2>Предложенные песни · без MP3</h2>';
        foreach ($rows as $r) {
            $id=(int)$r['id'];
            // Never trust a submitted URL. Build a fixed-host URL from validated exact Track ID.
            $trackId = (string)$r['service_track_id'];
            $url = preg_match('/^[1-9]\d{0,23}$/D', $trackId)
                ? 'https://music.yandex.ru/track/' . $trackId : '';
            $html .= '<section class="panel"><h3>#'.$id.' · '.self::e($r['artist'])
                .' — '.self::e($r['title']).'</h3><p>Track ID: '.self::e($trackId)
                .' · '.self::e($r['status']).' · '.self::e($r['created_at']).'</p>'
                .($url !== '' ? '<p><a href="'.self::e($url).'" target="_blank" rel="noopener noreferrer">Открыть в Яндекс Музыке</a></p>' : '');
            if ($r['status']==='pending' && in_array($admin['role'],['owner','moderator'],true)) {
                $html .= '<form method="post" action="/admin/action"><input type="hidden" name="csrf" value="'.$csrf.'">'
                    .'<input type="hidden" name="kind" value="track_request"><input type="hidden" name="id" value="'.$id.'">'
                    .'<label>Результат проверки <input name="reason" required maxlength="500"></label>'
                    .'<button name="action" value="reviewed">Рассмотрено</button>'
                    .'<button name="action" value="rejected">Отклонить</button></form>';
            }
            $html .= '</section>';
        }
        return $html;
    }

    private function reports(): string
    {
        $rows = $this->pdo->query('SELECT id,replacement_id,category,details,status,created_at FROM reports ORDER BY id DESC LIMIT 100')
            ->fetchAll(\PDO::FETCH_ASSOC);
        $html='<h2>Жалобы</h2><div class="panel"><table><tr><th>ID</th><th>Replacement</th><th>Категория</th><th>Описание</th><th>Статус</th></tr>';
        foreach($rows as $r) $html.='<tr><td>'.(int)$r['id'].'</td><td>'.(int)$r['replacement_id']
            .'</td><td>'.self::e($r['category']).'</td><td>'.self::e($r['details'])
            .'</td><td>'.self::e($r['status']).'</td></tr>';
        return $html.'</table></div>';
    }

    private function auditLog(): string
    {
        $rows=$this->pdo->query('SELECT l.created_at,a.login,l.action,l.entity_type,l.entity_id,l.reason
            FROM audit_log l JOIN admins a ON a.id=l.admin_id ORDER BY l.id DESC LIMIT 100')
            ->fetchAll(\PDO::FETCH_ASSOC);
        $html='<h2>Журнал действий</h2><div class="panel"><table><tr><th>Когда</th><th>Кто</th><th>Действие</th><th>Объект</th><th>Причина</th></tr>';
        foreach($rows as $r) $html.='<tr><td>'.self::e($r['created_at']).'</td><td>'.self::e($r['login'])
            .'</td><td>'.self::e($r['action']).'</td><td>'.self::e($r['entity_type']).' #'.(int)$r['entity_id']
            .'</td><td>'.self::e($r['reason']).'</td></tr>';
        return $html.'</table></div>';
    }

    private function preview(string $method, int $id, array $headers): Response
    {
        $q=$this->pdo->prepare('SELECT a.storage_driver,a.storage_key,a.size_bytes,a.mime_type,a.sha256
            FROM track_replacements r JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.id=? LIMIT 1');
        $q->execute([$id]);
        $a=$q->fetch(\PDO::FETCH_ASSOC);
        if (!$a || $a['storage_driver']!=='local'
            || !in_array($a['mime_type'],['audio/mpeg','audio/wav','audio/x-wav'],true)
            || !$this->storage->exists($a['storage_key'])) return Response::json(404,['error'=>'audio_not_found']);
        $size=$this->storage->getSize($a['storage_key']);
        if ($size<1 || $size !== (int)$a['size_bytes']) return Response::json(404,['error'=>'audio_not_found']);
        $start=0;$end=$size-1;$status=200;
        $out=['Content-Type'=>$a['mime_type'],'Content-Length'=>(string)$size,
            'Accept-Ranges'=>'bytes','Cache-Control'=>'private, no-store',
            'Content-Disposition'=>'inline','X-Robots-Tag'=>'noindex'];
        if ($method==='GET' && isset($headers['range'])) {
            try { [$start,$end]=ByteRange::parse((string)$headers['range'],$size); }
            catch(\InvalidArgumentException) {
                return new Response(416,['Content-Range'=>'bytes */'.$size,'Cache-Control'=>'no-store','Content-Length'=>'0']);
            }
            $status=206;$out['Content-Range']="bytes $start-$end/$size";
            $out['Content-Length']=(string)($end-$start+1);
        }
        if ($method==='HEAD') return new Response($status,$out);
        $stream=$this->storage->openStream($a['storage_key']);
        if(fseek($stream,$start)!==0){fclose($stream);throw new \RuntimeException('private_stream_seek_failed');}
        $remaining=$end-$start+1;
        return new Response($status,$out,stream:static function()use($stream,$remaining):void{
            try{
                while($remaining>0&&!connection_aborted()){
                    $chunk=fread($stream,min(65536,$remaining));
                    if($chunk===false||$chunk==='')break;
                    echo $chunk;$remaining-=strlen($chunk);
                }
            }finally{fclose($stream);}
        });
    }
}
