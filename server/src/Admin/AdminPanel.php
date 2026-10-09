<?php

declare(strict_types=1);

namespace Celikom\Admin;

use Celikom\Http\ByteRange;
use Celikom\Http\Response;
use Celikom\Auth\UserMetrics;
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
                $result = $auth->login(is_string($form['login'] ?? null) ? $form['login'] : '',
                    is_string($form['password'] ?? null) ? $form['password'] : '',
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
        if ($path === '/admin/metadata' && $method === 'POST') {
            if ($admin['role'] !== 'owner') return Response::json(403,['error'=>'forbidden']);
            $form = $this->form($headers,$body);
            if (!AdminAuth::validCsrf($admin,$form['csrf'] ?? null)) {
                return Response::json(403,['error'=>'csrf_failed']);
            }
            $track = $this->positiveInt($form['track'] ?? null);
            if (!$track || !is_string($form['expected_track_id'] ?? null)
                || !is_string($form['artist'] ?? null) || !is_string($form['title'] ?? null)) {
                return Response::json(400,['error'=>'invalid_metadata']);
            }
            try {
                (new MetadataService($this->pdo))->update($admin['id'],$track,
                    $form['expected_track_id'],$form['artist'],$form['title']);
                return new Response(303,['Location'=>'/admin?tab=uploads','Cache-Control'=>'no-store']);
            } catch (\InvalidArgumentException) {
                return Response::json(400,['error'=>'invalid_metadata']);
            } catch (\DomainException) {
                return Response::json(409,['error'=>'metadata_conflict']);
            }
        }
        if ($path === '/admin/action' && $method === 'POST') {
            if (!in_array($admin['role'], ['owner','moderator'], true)) return Response::json(403, ['error'=>'forbidden']);
            $form = $this->form($headers, $body);
            if (!AdminAuth::validCsrf($admin, $form['csrf'] ?? null)) return Response::json(403, ['error'=>'csrf_failed']);
            $id = $this->positiveInt($form['id'] ?? null);
            $action = $form['action'] ?? null;
            $kind = $form['kind'] ?? null;
            $reason = $form['reason'] ?? null;
            if (!$id || !is_string($action) || !is_string($kind)) {
                return Response::json(400, ['error'=>'invalid_action']);
            }
            // The new two-step disclosure forms are only selectors. The final POST
            // carries an explicit decision type and is validated server-side.
            if ($kind === 'replacement' && array_key_exists('decision', $form)) {
                $choice = self::replacementDecision($form, $action);
                if ($choice === null) {
                    return $this->page('<section class="panel">'
                        . '<h1>Проверьте решение</h1>'
                        . '<p>Укажите причину отказа. Для варианта «Другая причина»'
                        . ' обязательно напишите свой текст. Комментарий не должен превышать 180 символов.</p>'
                        . '<a class="btn" href="/admin?tab=uploads">Вернуться к модерации</a>'
                        . '</section>', status: 400);
                }
                [$action, $reason] = $choice;
            }
            if (!is_string($reason)) return Response::json(400, ['error'=>'invalid_action']);
            try {
                $moderation = new ModerationService($this->pdo, $this->storage);
                if ($kind === 'replacement') {
                    if ($action === 'reactivate' && $admin['role'] !== 'owner') {
                        return Response::json(403, ['error'=>'forbidden']);
                    }
                    $expected = $this->nonnegativeInt($form['expected_active'] ?? null);
                    if ($expected === null) return Response::json(400, ['error'=>'invalid_action']);
                    $moderation->replacement($admin['id'], $id, $action, $reason, $expected,
                        ($form['rights_confirmed'] ?? null) === '1');
                } elseif ($kind === 'track_request') {
                    $moderation->trackRequest($admin['id'], $id, $action, $reason);
                } elseif ($kind === 'report') {
                    $moderation->report($admin['id'], $id, $action, $reason);
                } else {
                    return Response::json(400, ['error'=>'invalid_action']);
                }
                return new Response(303, ['Location'=>'/admin?tab=' . ($kind === 'report' ? 'reports' : ($kind === 'track_request' ? 'requests' : 'uploads')),
                    'Cache-Control'=>'no-store']);
            } catch (\InvalidArgumentException) {
                return Response::json(400, ['error'=>'invalid_action']);
            } catch (\DomainException) {
                return Response::json(409, ['error'=>'moderation_conflict_or_unverified']);
            }
        }
        if ($path === '/admin/export' && $method === 'POST') {
            if (!in_array($admin['role'], ['owner','moderator'], true)) return Response::json(403,['error'=>'forbidden']);
            $form=$this->form($headers,$body);
            if (!AdminAuth::validCsrf($admin,$form['csrf'] ?? null)) return Response::json(403,['error'=>'csrf_failed']);
            return $this->exportAudit($admin);
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

    /**
     * Converts the two explicit confirmation forms into the existing atomic
     * moderation actions. The optional owner comment is stored in audit_log.
     * Older guarded workflows using reason/action continue to function.
     *
     * @return array{string,string}|null
     */
    private static function replacementDecision(array $form, string $action): ?array
    {
        $decision = $form['decision'] ?? null;
        $note = $form['review_note'] ?? '';
        if (!is_string($decision) || !is_string($note)) return null;
        $note = trim(str_replace(["\r\n", "\r"], "\n", $note));
        if (!mb_check_encoding($note, 'UTF-8') || mb_strlen($note, 'UTF-8') > 180
            || preg_match('/[\x00-\x09\x0B-\x1F\x7F]/u', $note)) return null;
        if ($decision === 'approval') {
            if ($action !== 'approve') return null;
            $reason = 'Аудио и права проверены'
                . ($note !== '' ? ' · Комментарий: ' . $note : '');
        } elseif ($decision === 'rejection') {
            if ($action !== 'reject') return null;
            $category = $form['reject_category'] ?? null;
            if (!is_string($category)) return null;
            $choices = [
                'duplicate' => ['duplicate','Дубликат'],
                'wrong_track' => ['wrong_track','Не тот трек'],
                'bad_quality' => ['bad_quality','Плохое качество'],
                'rights' => ['reject','Проблемы с правами'],
                'other' => ['reject','Другая причина'],
            ];
            if (!isset($choices[$category]) || ($category === 'other' && $note === '')) return null;
            [$action,$label] = $choices[$category];
            $reason = $label . ($note !== '' ? ' · Комментарий: ' . $note : '');
        } else {
            return null;
        }
        return strlen($reason) <= 500 ? [$action,$reason] : null;
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

    private static function statusLabel(string $status): string
    {
        return match ($status) {
            'pending' => 'На проверке', 'approved' => 'Одобрено',
            'rejected' => 'Отклонено', 'disabled' => 'Отключено',
            'reviewed' => 'Рассмотрено', 'dismissed' => 'Отклонена',
            default => 'Неизвестный статус',
        };
    }

    private static function actionLabel(string $action): string
    {
        return match ($action) {
            'replacement_approve' => 'Подмена одобрена',
            'replacement_reactivate' => 'Подмена восстановлена',
            'replacement_reject' => 'Версия отклонена',
            'replacement_duplicate' => 'Отмечен дубликат',
            'replacement_wrong_track' => 'Неверный трек',
            'replacement_bad_quality' => 'Плохое качество',
            'replacement_disable' => 'Подмена отключена',
            'track_request_reviewed' => 'Предложение рассмотрено',
            'track_request_rejected' => 'Предложение отклонено',
            'report_reviewed' => 'Жалоба рассмотрена',
            'report_dismissed' => 'Жалоба отклонена',
            'audit_csv_export' => 'Журнал скачан',
            'track_metadata_labeled' => 'Подпись трека уточнена',
            default => 'Другое действие',
        };
    }

    private static function formatDuration(int $millis): string
    {
        $seconds = max(0, (int) round($millis / 1000));
        $minutes = intdiv($seconds, 60);
        return $minutes . ':' . str_pad((string) ($seconds % 60), 2, '0', STR_PAD_LEFT);
    }

    private static function formatSize(int $bytes): string
    {
        return number_format(max(0, $bytes) / 1048576, 2, ',', ' ') . ' МБ';
    }

    private static function displayTitle(mixed $artist, mixed $title): string
    {
        $artist = trim((string) $artist);
        $title = trim((string) $title);
        if ($artist === 'celikom-ci' && str_starts_with($title, 'synthetic-')) {
            return 'Тестовая запись — синтетическое аудио';
        }
        if ($title === '' && $artist === '') return 'Название не указано';
        if ($title === '') return $artist . ' — название не указано';
        if ($artist === '') return $title . ' — исполнитель не указан';
        return $artist . ' — ' . $title;
    }

    private static function statusPill(string $status): string
    {
        $class = in_array($status, ['pending','approved','rejected','disabled','reviewed','dismissed'], true)
            ? $status : 'disabled';
        return '<span class="pill pill-' . $class . '">' . self::e(self::statusLabel($status)) . '</span>';
    }

    private static function yandexLink(string $trackId): string
    {
        if (!preg_match('/^[1-9]\d{0,23}$/D', $trackId)) return '';
        return '<a href="https://music.yandex.ru/track/' . self::e($trackId)
            . '" target="_blank" rel="noopener noreferrer">Открыть в Яндекс Музыке ↗</a>';
    }

    private function page(string $inner, array $otherHeaders = [], int $status = 200): Response
    {
        $css = file_get_contents(__DIR__ . '/admin-style.css');
        if ($css === false) throw new \RuntimeException('admin_style_not_found');
        $html = '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            . '<meta name="viewport" content="width=device-width,initial-scale=1">'
            . '<meta name="theme-color" content="#f4f8f6"><title>CELIKOM · Панель управления</title><style>'
            . $css . '</style></head><body><main>' . $inner . '</main></body></html>';
        return new Response($status, array_merge([
            'Content-Type'=>'text/html; charset=utf-8','Cache-Control'=>'no-store',
            'Content-Security-Policy'=>"default-src 'none'; style-src 'unsafe-inline'; media-src 'self';"
                . " form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            'X-Frame-Options'=>'DENY','X-Robots-Tag'=>'noindex, nofollow'
        ], $otherHeaders), $html);
    }

    private function loginPage(string $csrf): string
    {
        return '<div class="login-shell"><section class="panel login-card">'
            . '<div class="brand"><span class="brand-mark">♫</span><span><strong>CELIKOM</strong>'
            . '<small>Панель управления</small></span></div>'
            . '<h1 style="margin-top:28px">Добро пожаловать</h1>'
            . '<p class="muted">Войдите в закрытую панель модерации</p>'
            . '<form method="post" action="/admin/login">'
            . '<input type="hidden" name="csrf" value="' . self::e($csrf) . '">'
            . '<label>Логин<input name="login" autocomplete="username" required></label>'
            . '<label>Пароль<input type="password" name="password" autocomplete="current-password" required></label>'
            . '<button class="primary" type="submit">Войти</button></form></section></div>';
    }

    private function dashboard(array $admin, array $query): string
    {
        $tab = is_string($query['tab'] ?? null) ? $query['tab'] : 'uploads';
        $allowed = ['uploads','requests','reports','audit','overview'];
        if (!in_array($tab, $allowed, true)) $tab = 'uploads';
        $csrf = self::e($admin['csrf']);
        $size = $this->pageSize($query);
        $role = match ($admin['role']) {
            'owner' => 'Владелец', 'moderator' => 'Модератор',
            'viewer' => 'Наблюдатель', default => 'Сотрудник'
        };
        $html = '<header class="header"><a class="brand" href="/admin">'
            . '<span class="brand-mark" aria-hidden="true">♫</span><span><strong>CELIKOM</strong>'
            . '<small>Панель управления</small></span></a><div class="header-actions">'
            . '<span class="account" aria-label="Роль в системе">● ' . self::e($role) . '</span>';
        if (in_array($admin['role'], ['owner','moderator'], true)) {
            $html .= '<form class="head-form" method="post" action="/admin/export">'
                . '<input type="hidden" name="csrf" value="' . $csrf . '">'
                . '<button type="submit" title="Скачать журнал действий в CSV">↓ Скачать журнал</button></form>';
        }
        $html .= '<form class="head-form" method="post" action="/admin/logout">'
            . '<input type="hidden" name="csrf" value="' . $csrf . '">'
            . '<button type="submit">Выйти ↗</button></form></div></header><nav class="nav" aria-label="Разделы">';
        foreach ([
            'uploads'=>'Загруженные версии', 'requests'=>'Предложить песню',
            'reports'=>'Жалобы', 'audit'=>'Журнал действий', 'overview'=>'Обзор'
        ] as $key => $name) {
            $html .= '<a href="/admin?tab=' . $key . '&per_page=' . $size . '"'
                . ($tab === $key ? ' class="current" aria-current="page"' : '') . '>'
                . self::e($name) . '</a>';
        }
        $html .= '</nav>';
        $counts = $this->pdo->query("SELECT
            (SELECT COUNT(*) FROM track_replacements WHERE status='pending') AS pending_uploads,
            (SELECT COUNT(*) FROM track_requests WHERE status='pending') AS pending_requests,
            (SELECT COUNT(*) FROM reports WHERE status='pending') AS pending_reports")->fetch(\PDO::FETCH_ASSOC);
        $html .= '<div class="stats">'
            . '<a class="stat" href="/admin?tab=uploads&status=pending&per_page=' . $size
            . '"><span>Версии на проверке<span class="sub">Загруженные аудиофайлы</span></span><strong>'
            . (int) $counts['pending_uploads'] . '</strong></a>'
            . '<a class="stat" href="/admin?tab=requests&status=pending&per_page=' . $size
            . '"><span>Предложения песен<span class="sub">Без загрузки аудио</span></span><strong>'
            . (int) $counts['pending_requests'] . '</strong></a>'
            . '<a class="stat" href="/admin?tab=reports&status=pending&per_page=' . $size
            . '"><span>Новые жалобы<span class="sub">Ожидают решения</span></span><strong>'
            . (int) $counts['pending_reports'] . '</strong></a></div>';
        return $html . match ($tab) {
            'requests' => $this->requests($admin, $csrf, $query),
            'reports' => $this->reports($admin, $csrf, $query),
            'audit' => $this->auditLog($query),
            'overview' => $this->overview($query),
            default => $this->uploads($admin, $csrf, $query),
        };
    }

    /** Validated, fixed page sizes prevent unbounded MySQL lists. */
    private function pageSize(array $query): int
    {
        $value = $query['per_page'] ?? '25';
        return is_string($value) && in_array($value, ['10','25','50'], true)
            ? (int) $value : 25;
    }

    /** User-supplied values never become free-form SQL predicates or LIMITs. */
    private function queueOptions(string $tab, array $query, array $statuses): array
    {
        $status = is_string($query['status'] ?? null) && in_array($query['status'], $statuses, true)
            ? $query['status'] : '';
        $p = $query['page'] ?? '1';
        $page = is_string($p) && preg_match('/^[1-9]\d{0,2}$/D', $p) ? (int) $p : 1;
        $perPage = $this->pageSize($query);
        $offset = ($page - 1) * $perPage;
        $form = '<div class="toolbar"><form method="get" action="/admin">'
            . '<input type="hidden" name="tab" value="' . self::e($tab) . '">'
            . '<label class="form-field">Статус<select name="status"><option value="">Все статусы</option>';
        foreach ($statuses as $value) {
            $form .= '<option value="' . self::e($value) . '"'
                . ($status === $value ? ' selected' : '') . '>'
                . self::e(self::statusLabel($value)) . '</option>';
        }
        $form .= '</select></label><label class="form-field">На странице<select name="per_page">';
        foreach ([10,25,50] as $size) {
            $form .= '<option value="' . $size . '"' . ($size === $perPage ? ' selected' : '')
                . '>' . $size . ' записей</option>';
        }
        $form .= '</select></label><button type="submit">Применить</button></form></div>';
        return [$status, $page, $offset, $form, $perPage];
    }

    private function queuePages(string $tab, string $status, int $page, int $perPage, int $total): string
    {
        $totalPages = max(1, (int) ceil($total / $perPage));
        $base = '/admin?tab=' . rawurlencode($tab) . '&status=' . rawurlencode($status)
            . '&per_page=' . $perPage . '&page=';
        $view = '<nav class="pagination" aria-label="Страницы списка"><span>Всего: '
            . $total . ' · Страница ' . $page . ' из ' . $totalPages . '</span><div class="pages">';
        $link = static fn(int $i): string => $base . $i;
        if ($page > 1) {
            $view .= '<a href="' . self::e($link($page - 1)) . '" aria-label="Предыдущая страница">‹</a>';
        } else {
            $view .= '<span class="disabled" aria-hidden="true">‹</span>';
        }
        $start = max(1, min($page - 2, max(1, $totalPages - 4)));
        $last = min($totalPages, $start + 4);
        for ($i = $start; $i <= $last; $i++) {
            $view .= $i === $page ? '<span class="current" aria-current="page">' . $i . '</span>'
                : '<a href="' . self::e($link($i)) . '">' . $i . '</a>';
        }
        if ($page < $totalPages) {
            $view .= '<a href="' . self::e($link($page + 1)) . '" aria-label="Следующая страница">›</a>';
        } else {
            $view .= '<span class="disabled" aria-hidden="true">›</span>';
        }
        return $view . '</div></nav>';
    }

    private function uploads(array $admin, string $csrf, array $query): string
    {
        [$status,$page,$offset,$filter,$perPage] = $this->queueOptions('uploads', $query,
            ['pending','approved','rejected','disabled']);
        $where = $status !== '' ? ' WHERE r.status = ? ' : ' ';
        $params = $status !== '' ? [$status] : [];
        $count = $this->pdo->prepare('SELECT COUNT(*) FROM track_replacements r ' . $where);
        $count->execute($params);
        $total = (int) $count->fetchColumn();
        $stmt = $this->pdo->prepare("SELECT r.id,r.status,r.is_active,r.version,r.track_id,
            t.service,t.service_track_id,t.artist,t.title,t.duration_ms AS original_duration_ms,
            a.duration_ms AS audio_duration_ms,a.mime_type,a.size_bytes,a.sha256,
            d.action AS decision_action,d.reason AS decision_reason,d.created_at AS decision_at,
            (SELECT q.id FROM track_replacements q WHERE q.track_id=r.track_id
                AND q.status='approved' AND q.is_active=1 AND q.disabled_at IS NULL LIMIT 1) AS active_id
            FROM track_replacements r JOIN tracks t ON t.id=r.track_id
            JOIN audio_assets a ON a.id=r.audio_asset_id
            LEFT JOIN audit_log d ON d.id = (
                SELECT l.id FROM audit_log l WHERE l.entity_type='track_replacement'
                AND l.entity_id=r.id AND l.action IN
                ('replacement_approve','replacement_reactivate','replacement_reject',
                 'replacement_duplicate','replacement_wrong_track','replacement_bad_quality',
                 'replacement_disable')
                ORDER BY l.id DESC LIMIT 1
            ) " . $where .
            " ORDER BY FIELD(r.status,'pending','approved','rejected','disabled'),r.id DESC LIMIT "
            . $perPage . " OFFSET " . $offset);
        $stmt->execute($params);
        $rows = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<div class="page-head"><div><div class="eyebrow">Библиотека / модерация</div>'
            . '<h1>Загруженные версии</h1><p class="muted">Новые песни появляются здесь только после загрузки. '
            . 'Подмена включается вручную после проверки файла и прав.</p></div></div>' . $filter
            . '<div class="cards">';
        foreach ($rows as $r) {
            $id = (int) $r['id'];
            $trackId = (string) $r['service_track_id'];
            $html .= '<article class="track-card"><div class="track-top"><div class="track-heading">'
                . '<span class="track-icon" aria-hidden="true">♫</span><div>'
                . '<h2 class="track-title">#' . $id . ' · '
                . self::e(self::displayTitle($r['artist'], $r['title'])) . '</h2>'
                . '<div class="track-subtitle">Яндекс Музыка · Track ID ' . self::e($trackId) . '</div>'
                . self::yandexLink($trackId) . '</div></div>'
                . self::statusPill((string) $r['status']) . '</div>'
                . '<div class="track-meta">'
                . '<span>Длительность в Яндексе: <strong>'
                . self::formatDuration((int) $r['original_duration_ms']) . '</strong></span>'
                . '<span>Загруженное аудио: <strong>'
                . self::formatDuration((int) $r['audio_duration_ms']) . '</strong></span>'
                . '<span>Подмена: <strong>' . ((int) $r['is_active'] === 1 ? 'включена' : 'выключена')
                . '</strong></span></div>'
                . '<div class="player-wrap"><audio controls preload="none"'
                . ' aria-label="Прослушать загруженную версию #' . $id . '"'
                . ' src="/admin/audio/' . $id . '"></audio>'
                . '<small>Прослушивание доступно только администратору</small></div>'
                . '<details class="detail-toggle"><summary>Технические сведения</summary>'
                . '<div class="technical">Размер: ' . self::formatSize((int) $r['size_bytes'])
                . ' · Формат: ' . (in_array($r['mime_type'], ['audio/mpeg'], true) ? 'MP3' : 'Аудио')
                . '<p style="margin:8px 0 0">Контрольная сумма SHA-256: '
                . self::e($r['sha256']) . '</p></div></details>';
            if ($admin['role'] === 'owner'
                && (trim((string) $r['artist']) === '' || trim((string) $r['title']) === '')) {
                $html .= '<details class="detail-toggle"><summary>Уточнить название и исполнителя</summary>'
                    . '<p class="muted">Проверьте оригинал по ссылке на Яндекс Музыку. '
                    . 'Сохраняется только подпись — сам аудиофайл не меняется.</p>'
                    . '<form class="metadata-form" method="post" action="/admin/metadata">'
                    . '<input type="hidden" name="csrf" value="' . $csrf . '">'
                    . '<input type="hidden" name="track" value="' . (int) $r['track_id'] . '">'
                    . '<input type="hidden" name="expected_track_id" value="' . self::e($trackId) . '">'
                    . '<label class="form-field">Исполнитель'
                    . '<input name="artist" maxlength="240" value="' . self::e($r['artist']) . '"></label>'
                    . '<label class="form-field">Название песни'
                    . '<input name="title" maxlength="240" required value="' . self::e($r['title']) . '"></label>'
                    . '<button class="primary" type="submit">Сохранить подпись</button></form></details>';
            }
            if (is_string($r['decision_reason']) && trim($r['decision_reason']) !== '') {
                $html .= '<div class="decision-history"><strong>'
                    . self::e(self::actionLabel((string)$r['decision_action']))
                    . '</strong><span>' . self::e($r['decision_reason']) . '</span>'
                    . '<small>' . self::e($r['decision_at']) . ' UTC · Подробнее в журнале</small>'
                    . '</div>';
            }
            if (in_array($admin['role'], ['owner','moderator'], true)
                && ($r['status'] === 'pending'
                    || ($r['status'] === 'approved' && (int) $r['is_active'] === 1)
                    || ($r['status'] === 'disabled' && $admin['role'] === 'owner' && !$r['active_id']))) {
                $common = '<input type="hidden" name="csrf" value="' . $csrf . '">'
                    . '<input type="hidden" name="kind" value="replacement">'
                    . '<input type="hidden" name="id" value="' . $id . '">'
                    . '<input type="hidden" name="expected_active" value="'
                    . (int) ($r['active_id'] ?? 0) . '">';
                if ($r['status'] === 'pending') {
                    // Native details groups form a two-step confirmation without JS.
                    $html .= '<section class="decision" aria-label="Решение по версии">'
                        . '<div class="decision-heading">Решение по версии</div>'
                        . '<div class="decision-options">'
                        . '<details class="decision-choice choice-approval" name="review-' . $id . '">'
                        . '<summary>✓ Одобрить</summary><div class="decision-body">'
                        . '<p class="muted">Проверьте аудио и права. Открытие формы ничего не меняет.</p>'
                        . '<form method="post" action="/admin/action">' . $common
                        . '<input type="hidden" name="action" value="approve">'
                        . '<input type="hidden" name="decision" value="approval">'
                        . '<label class="rights-check"><input type="checkbox" name="rights_confirmed"'
                        . ' value="1" required>Подтверждаю, что проверил аудио и права на его использование</label>'
                        . '<label class="form-field" for="approve-note-' . $id . '">'
                        . 'Комментарий (необязательно)'
                        . '<textarea id="approve-note-' . $id . '" name="review_note" maxlength="180"'
                        . ' rows="2" placeholder="При необходимости добавьте пояснение"></textarea></label>'
                        . '<button class="primary" type="submit">Подтвердить одобрение</button>'
                        . '</form></div></details>'
                        . '<details class="decision-choice choice-rejection" name="review-' . $id . '">'
                        . '<summary>✕ Отклонить</summary><div class="decision-body">'
                        . '<p class="muted">Выберите причину отклонения и подтвердите решение.</p>'
                        . '<form method="post" action="/admin/action">' . $common
                        . '<input type="hidden" name="action" value="reject">'
                        . '<input type="hidden" name="decision" value="rejection">'
                        . '<label class="form-field" for="reject-category-' . $id . '">'
                        . 'Причина отклонения<select class="reject-category" name="reject_category" id="reject-category-' . $id . '" required>'
                        . '<option value="" selected disabled hidden>Выберите причину</option>'
                        . '<option value="duplicate">Дубликат</option>'
                        . '<option value="wrong_track">Не тот трек</option>'
                        . '<option value="bad_quality">Плохое качество</option>'
                        . '<option value="rights">Проблемы с правами</option>'
                        . '<option value="other">Другая причина</option>'
                        . '</select></label>'
                        . '<label class="form-field" for="reject-note-' . $id . '">'
                        . 'Комментарий (обязателен для «Другой причины»)'
                        . '<textarea id="reject-note-' . $id . '" name="review_note" maxlength="180"'
                        . ' rows="2" placeholder="Свой вариант причины или подробности"></textarea></label>'
                        . '<button class="danger" type="submit">Подтвердить отклонение</button>'
                        . '</form></div></details></div></section>';
                } else {
                    $html .= '<div class="decision"><form method="post" action="/admin/action">'
                        . $common
                        . '<label class="form-field">Причина решения'
                        . '<input name="reason" required maxlength="500"'
                        . ' placeholder="Кратко опишите проверку"></label>';
                    if ($r['status'] === 'disabled') {
                        $html .= '<label><input type="checkbox" name="rights_confirmed" value="1">'
                            . ' Права перепроверены</label>'
                            . '<button class="primary" name="action" value="reactivate">'
                            . 'Восстановить подмену</button>';
                    } else {
                        $html .= '<button class="danger" name="action" value="disable">'
                            . 'Отключить подмену</button>';
                    }
                    $html .= '</form></div>';
                }
            }
            $html .= '</article>';
        }
        if (!$rows) $html .= '<section class="empty"><strong>Записей пока нет</strong>'
            . 'Попробуйте изменить фильтр статуса.</section>';
        return $html . '</div>' . $this->queuePages('uploads', $status, $page, $perPage, $total);
    }

    private function requests(array $admin, string $csrf, array $query): string
    {
        [$status,$page,$offset,$filter,$perPage] = $this->queueOptions('requests', $query,
            ['pending','reviewed','rejected']);
        $where = $status !== '' ? ' WHERE status = ? ' : ' ';
        $params = $status !== '' ? [$status] : [];
        $count = $this->pdo->prepare('SELECT COUNT(*) FROM track_requests ' . $where);
        $count->execute($params);
        $total = (int) $count->fetchColumn();
        $stmt = $this->pdo->prepare("SELECT r.id,r.service,r.service_track_id,r.artist,r.title,r.status,r.created_at,
            (SELECT COUNT(DISTINCT x.uploader_hash) FROM track_requests x
              WHERE x.service = r.service AND x.service_track_id = r.service_track_id) AS proposal_count
            FROM track_requests r " . ($status !== '' ? ' WHERE r.status = ? ' : ' ') .
            " ORDER BY FIELD(r.status,'pending','reviewed','rejected'),r.id DESC LIMIT "
            . $perPage . " OFFSET " . $offset);
        $stmt->execute($params);
        $rows = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<div class="page-head"><div><div class="eyebrow">Обратная связь</div>'
            . '<h1>Предложения песен</h1><p class="muted">'
            . 'Запросы на замену без загрузки аудиофайлов и без подтверждения прав на MP3.'
            . '</p></div></div>' . $filter . '<div class="cards">';
        foreach ($rows as $r) {
            $id = (int) $r['id'];
            $trackId = (string) $r['service_track_id'];
            $html .= '<article class="track-card"><div class="track-top">'
                . '<div class="track-heading"><span class="track-icon">♫</span><div>'
                . '<h2 class="track-title">#' . $id . ' · '
                . self::e(self::displayTitle($r['artist'], $r['title'])) . '</h2>'
                . '<div class="track-subtitle">Яндекс Музыка · Track ID '
                . self::e($trackId) . '</div>' . self::yandexLink($trackId)
                . '</div></div>' . self::statusPill((string) $r['status'])
                . '</div><div class="track-meta"><span>Уникальных предложений: '
                . (int) $r['proposal_count'] . '</span><span>Получено: '
                . self::e($r['created_at']) . ' UTC</span></div>';
            if ($r['status'] === 'pending' && in_array($admin['role'], ['owner','moderator'], true)) {
                $html .= '<div class="decision"><form method="post" action="/admin/action">'
                    . '<input type="hidden" name="csrf" value="' . $csrf . '">'
                    . '<input type="hidden" name="kind" value="track_request">'
                    . '<input type="hidden" name="id" value="' . $id . '">'
                    . '<label class="form-field">Результат проверки'
                    . '<input name="reason" required maxlength="500" placeholder="Напишите результат"></label>'
                    . '<button class="primary" name="action" value="reviewed">Отметить рассмотренным</button>'
                    . '<button class="danger" name="action" value="rejected">Отклонить предложение</button>'
                    . '</form></div>';
            }
            $html .= '</article>';
        }
        if (!$rows) $html .= '<section class="empty"><strong>Предложений пока нет</strong>'
            . 'Когда пользователи предложат песни, они появятся здесь.</section>';
        return $html . '</div>' . $this->queuePages('requests', $status, $page, $perPage, $total);
    }

    private function reports(array $admin, string $csrf, array $query): string
    {
        [$status,$page,$offset,$filter,$perPage] = $this->queueOptions('reports', $query,
            ['pending','reviewed','dismissed']);
        $where = $status !== '' ? ' WHERE status = ? ' : ' ';
        $params = $status !== '' ? [$status] : [];
        $count = $this->pdo->prepare('SELECT COUNT(*) FROM reports ' . $where);
        $count->execute($params);
        $total = (int) $count->fetchColumn();
        $stmt = $this->pdo->prepare('SELECT id,replacement_id,category,details,status,created_at FROM reports '
            . $where . ' ORDER BY id DESC LIMIT ' . $perPage . ' OFFSET ' . $offset);
        $stmt->execute($params);
        $rows = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<div class="page-head"><div><div class="eyebrow">Обратная связь</div>'
            . '<h1>Жалобы на версии</h1><p class="muted">'
            . 'Проверяйте обращения и фиксируйте решения. Жалоба сама не отключает подмену.'
            . '</p></div></div>' . $filter
            . '<div class="table-shell"><table><thead><tr><th>Жалоба</th>'
            . '<th>Версия</th><th>Причина</th><th>Описание</th><th>Статус и решение</th>'
            . '</tr></thead><tbody>';
        foreach ($rows as $r) {
            $category = match ($r['category']) {
                'wrong_track' => 'Не тот трек', 'bad_quality' => 'Плохое качество',
                'broken_audio' => 'Проблема с аудио', 'rights' => 'Нарушение прав',
                'other' => 'Другое', default => 'Неизвестная причина'
            };
            $html .= '<tr><td>#' . (int) $r['id'] . '<div class="muted">'
                . self::e($r['created_at']) . ' UTC</div></td>'
                . '<td>№ ' . (int) $r['replacement_id'] . '</td>'
                . '<td>' . self::e($category) . '</td>'
                . '<td>' . self::e($r['details']) . '</td><td>'
                . self::statusPill((string) $r['status']);
            if ($r['status'] === 'pending' && in_array($admin['role'], ['owner','moderator'], true)) {
                $html .= '<form method="post" action="/admin/action">'
                    . '<input type="hidden" name="csrf" value="' . $csrf . '">'
                    . '<input type="hidden" name="kind" value="report">'
                    . '<input type="hidden" name="id" value="' . (int) $r['id'] . '">'
                    . '<input name="reason" required maxlength="500" aria-label="Результат проверки"'
                    . ' placeholder="Результат проверки">'
                    . '<button class="primary" name="action" value="reviewed">Рассмотрено</button>'
                    . '<button name="action" value="dismissed">Отклонить жалобу</button></form>';
            }
            $html .= '</td></tr>';
        }
        if (!$rows) $html .= '<tr><td colspan="5" class="muted">Жалоб с таким статусом нет.</td></tr>';
        return $html . '</tbody></table></div>'
            . $this->queuePages('reports', $status, $page, $perPage, $total);
    }

    private function auditLog(array $query): string
    {
        $p = $query['page'] ?? '1';
        $page = is_string($p) && preg_match('/^[1-9]\d{0,2}$/D', $p) ? (int) $p : 1;
        $perPage = $this->pageSize($query);
        $offset = ($page - 1) * $perPage;
        $total = (int) $this->pdo->query('SELECT COUNT(*) FROM audit_log')->fetchColumn();
        $stmt = $this->pdo->query('SELECT l.created_at,a.login,a.role,l.action,l.entity_type,l.entity_id,l.reason
            FROM audit_log l JOIN admins a ON a.id=l.admin_id ORDER BY l.id DESC LIMIT '
            . $perPage . ' OFFSET ' . $offset);
        $rows = $stmt->fetchAll(\PDO::FETCH_ASSOC);
        $html = '<div class="page-head"><div><div class="eyebrow">Контроль</div>'
            . '<h1>Журнал действий</h1><p class="muted">'
            . 'История решений модераторов. Записи нельзя изменять из панели.</p></div></div>'
            . '<div class="toolbar"><form method="get" action="/admin">'
            . '<input type="hidden" name="tab" value="audit">'
            . '<label class="form-field">На странице<select name="per_page">';
        foreach ([10,25,50] as $size) {
            $html .= '<option value="' . $size . '"' . ($size === $perPage ? ' selected' : '')
                . '>' . $size . ' записей</option>';
        }
        $html .= '</select></label><button type="submit">Применить</button></form></div>'
            . '<div class="table-shell"><table><thead><tr><th>Время (UTC)</th>'
            . '<th>Сотрудник</th><th>Действие</th><th>Объект</th><th>Комментарий</th>'
            . '</tr></thead><tbody>';
        foreach ($rows as $r) {
            $role = match ($r['role']) {
                'owner' => 'Владелец','moderator' => 'Модератор',
                'viewer' => 'Наблюдатель',default => 'Сотрудник'
            };
            $object = match ($r['entity_type']) {
                'track_replacement' => 'Версия', 'track_request' => 'Предложение', 'track' => 'Трек',
                'report' => 'Жалоба', 'admin' => 'Администратор',
                default => 'Объект'
            };
            $html .= '<tr><td>' . self::e($r['created_at']) . '</td><td>'
                . self::e($role) . '</td><td>' . self::e(self::actionLabel((string)$r['action']))
                . '</td><td>' . self::e($object) . ' № ' . (int) $r['entity_id']
                . '</td><td>' . self::e($r['reason']) . '</td></tr>';
        }
        if (!$rows) $html .= '<tr><td colspan="5" class="muted">Записей пока нет.</td></tr>';
        return $html . '</tbody></table></div>'
            . $this->queuePages('audit', '', $page, $perPage, $total);
    }

    /** Real period comparisons only; payment counters remain unavailable. */
    private function overview(array $query): string
    {
        $to = is_string($query['to'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/D',$query['to'])
            ? $query['to'] : gmdate('Y-m-d');
        $from = is_string($query['from'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/D',$query['from'])
            ? $query['from'] : gmdate('Y-m-d',time()-6*86400);
        try {
            $start=new \DateTimeImmutable($from,new \DateTimeZone('UTC'));
            $finish=new \DateTimeImmutable($to,new \DateTimeZone('UTC'));
            if ($start->format('Y-m-d')!==$from || $finish->format('Y-m-d')!==$to
                || $start>$finish || $finish->getTimestamp()-$start->getTimestamp()>366*86400) {
                throw new \InvalidArgumentException('invalid_dates');
            }
        } catch(\Exception) {
            return '<section class="panel"><p>Неверный диапазон дат.</p></section>';
        }
        $endExclusive=$finish->modify('+1 day');
        $days=(int)$start->diff($endExclusive)->days;
        $beforeStart=$start->modify('-'.$days.' days');
        $counts=function(string $table,string $left,string $right):array {
            $sql="SELECT status,COUNT(*) AS amount FROM ".$table."
                WHERE created_at >= ? AND created_at < ? GROUP BY status";
            $stmt=$this->pdo->prepare($sql);$stmt->execute([$left,$right]);
            $rows=$stmt->fetchAll(\PDO::FETCH_ASSOC);
            $ret=[];foreach($rows as $r)$ret[$r['status']]=(int)$r['amount'];
            return $ret;
        };
        $date=function(\DateTimeImmutable $d):string{return $d->format('Y-m-d H:i:s');};
        $html='<div class="page-head"><div><div class="eyebrow">Статистика</div><h1>Операционный обзор</h1>'
            .'<p class="muted">Показатели на основе фактических данных</p></div></div><section class="panel"><form method="get" action="/admin">'
            .'<input type="hidden" name="tab" value="overview"><label>От <input type="date" name="from" value="'.self::e($from).'"></label>'
            .'<label>До <input type="date" name="to" value="'.self::e($to).'"></label>'
            .'<button type="submit">Показать</button></form>'
            .'<p><small>Сравнение с предыдущим равным периодом. Текущие статусы заявок, созданных в диапазоне.</small></p>'
            .'<table><tr><th>Тип / статус</th><th>Выбранный период</th><th>Предыдущий</th></tr>';
        foreach([['MP3','track_replacements'],['Предложения','track_requests']] as [$label,$table]){
            $now=$counts($table,$date($start),$date($endExclusive));
            $prior=$counts($table,$date($beforeStart),$date($start));
            foreach(['pending','approved','rejected','disabled','reviewed'] as $status){
                if(!isset($now[$status])&&!isset($prior[$status]))continue;
                $html.='<tr><td>'.self::e($label.' / '.self::statusLabel($status)).'</td><td>'.($now[$status]??0)
                    .'</td><td>'.($prior[$status]??0).'</td></tr>';
            }
        }
        $html.='</table></section>';
        $aggregate=$this->pdo->prepare('SELECT metric,SUM(event_count) AS events
            FROM analytics_daily_aggregates WHERE aggregate_date>=? AND aggregate_date<=?
            GROUP BY metric ORDER BY metric');
        $aggregate->execute([$from,$to]);
        $rows=$aggregate->fetchAll(\PDO::FETCH_ASSOC);
        if($rows) {
            $html.='<section class="panel"><h3>Агрегированные события (фактические)</h3><table>';
            foreach($rows as $r)$html.='<tr><td>'.self::e($r['metric']).'</td><td>'.(int)$r['events'].'</td></tr>';
            $html.='</table></section>';
        }else{
            $html.='<p>Агрегированная аналитика: данных за период нет. Нули не подставляются.</p>';
        }
        $accounts = new UserMetrics($this->pdo);
        if ($accounts->hasAccounts()) {
            $current = $accounts->forPeriod($date($start), $date($endExclusive));
            $previous = $accounts->forPeriod($date($beforeStart), $date($start));
            $html .= '<section class="panel"><h3>Аккаунты и активность CELIKOM</h3><table>'
                . '<tr><th>Метрика</th><th>Выбранный период</th><th>Предыдущий</th></tr>';
            foreach (['new'=>'Новые аккаунты','first'=>'Первые активации',
                'active'=>'Активные пользователи','returning'=>'Возвращающиеся пользователи'] as $key=>$label) {
                $html .= '<tr><td>'.self::e($label).'</td><td>'.$current[$key]
                    .'</td><td>'.$previous[$key].'</td></tr>';
            }
            $html .= '</table><p><small>Активность = подтверждённый запуск CELIKOM после входа. '
                . 'Возвращающиеся = запускали CELIKOM раньше выбранного периода. '
                . 'Анонимные установки не объединяются с аккаунтами.</small></p></section>';
        } else {
            $html .= '<p><small>Аккаунты ещё не создавались — пользовательские показатели пока недоступны.</small></p>';
        }
        $html .= '<p><small>Платежи и подписки подключаются на следующих этапах.</small></p>';
        return $html;
    }

    /** CSV has no raw uploader hashes or storage keys. Export access is audited. */
    private function exportAudit(array $admin): Response
    {
        $rows=$this->pdo->query('SELECT l.created_at,a.login,l.action,l.entity_type,l.entity_id,l.reason
            FROM audit_log l JOIN admins a ON a.id=l.admin_id ORDER BY l.id DESC LIMIT 1000')
            ->fetchAll(\PDO::FETCH_ASSOC);
        $moderation = new ModerationService($this->pdo,$this->storage);
        $moderation->audit($admin['id'],'audit_csv_export','admin',$admin['id'],
            'export up to 1000 recent audit rows',[],['row_count'=>count($rows)]);
        $escape=static function(mixed $v):string {
            $s=(string)($v??'');
            if(preg_match('/^[\s]*[=+\-@\t\r]/u',$s))$s="'".$s;
            return '"'.str_replace('"','""',$s).'"';
        };
        $csv="created_at,admin,action,entity_type,entity_id,reason\r\n";
        foreach($rows as $r)$csv.=implode(',',array_map($escape,array_values($r)))."\r\n";
        return new Response(200,['Content-Type'=>'text/csv; charset=utf-8',
            'Content-Disposition'=>'attachment; filename="celikom-audit.csv"',
            'Cache-Control'=>'private, no-store'], "\xEF\xBB\xBF".$csv);
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
