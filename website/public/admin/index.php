<?php
declare(strict_types=1);
/**
 * CELIKOM Stage 9 protected CMS editor, FIRST vertical slice.
 * Intentionally unavailable on production until Stage 10 creates the private
 * release approval marker. No publishing, uploads or arbitrary HTML editing.
 * Local test route requires PHP cli-server AND CELIKOM_LOCAL_ADMIN=1.
 */
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');
header('Referrer-Policy: no-referrer');
header('X-Robots-Tag: noindex, nofollow, noarchive');
header('Cache-Control: no-store, private');
header("Content-Security-Policy: default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'");
$root = dirname(__DIR__, 2);
$dev = PHP_SAPI === 'cli-server' && getenv('CELIKOM_LOCAL_ADMIN') === '1';
$app = $dev ? $root.'/app' : $root.'/celikom-private/app';
if (!$dev && !is_file($app.'/release-approved.php')) {
    http_response_code(503);
    header('Retry-After: 86400');
    echo 'Панель CELIKOM пока недоступна.';
    exit;
}
$https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
    || (int)($_SERVER['SERVER_PORT'] ?? 0) === 443;
if (!$https && !$dev) {
    http_response_code(403);
    echo 'Для управления сайтом требуется HTTPS.';
    exit;
}
if (!is_file($app.'/bootstrap.php') || !is_file($app.'/Templates/site-v10.html')) {
    http_response_code(503);
    echo 'Панель временно недоступна.';
    exit;
}
require_once $app.'/bootstrap.php';
use Celikom\Website\AdminAuth;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsDraftStore;
use Celikom\Website\CmsEditor;
use Celikom\Website\Content;
use Celikom\Website\Database;
use Celikom\Website\Security;

try {
    $pdo = Database::connect(CmsConfig::databaseSettings());
    Security::startAdminSession($https || $dev);
} catch (\Throwable $e) {
    error_log('CELIKOM CMS: unavailable (configuration/session)');
    http_response_code(503);
    echo 'Панель временно недоступна.';
    exit;
}
$now = time();
try {
    $admin = AdminAuth::checkSession($pdo, $now);
} catch (\Throwable $e) {
    error_log('CELIKOM CMS: session verification unavailable');
    http_response_code(503);
    echo 'Панель временно недоступна.';
    exit;
}
$error = null;
$notice = null;
$action = $_POST['action'] ?? null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!Security::verifyCsrf($_POST['csrf'] ?? null)) {
        http_response_code(403);
        $error = 'Недействительная форма. Обновите страницу.';
    } elseif (!is_string($action)) {
        http_response_code(400);
        $error = 'Неизвестная операция.';
    } elseif ($action === 'login' && $admin === null) {
        try {
            $found = AdminAuth::authenticate(
                $pdo,
                is_string($_POST['username'] ?? null) ? $_POST['username'] : '',
                is_string($_POST['password'] ?? null) ? $_POST['password'] : '',
                (string)($_SERVER['REMOTE_ADDR'] ?? ''),
                CmsConfig::rateSecret(),
                $now
            );
            if ($found !== null) {
                AdminAuth::finishLogin($found);
                header('Location: /admin/', true, 303);
                exit;
            }
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: login processing unavailable');
            http_response_code(503);
        }
        $error = 'Неверные данные или временно ограничен вход.';
    } elseif ($action === 'logout' && $admin !== null) {
        Security::clearSession();
        header('Location: /admin/', true, 303);
        exit;
    } elseif ($action === 'save' && $admin !== null) {
        try {
            $manifest = file_get_contents($app.'/Config/content-fields-v10.json');
            $template = file_get_contents($app.'/Templates/site-v10.html');
            $seedFile = $dev
                ? $root.'/database/seeds/faq-v10.json'
                : $root.'/celikom-private/database/seeds/faq-v10.json';
            $seed = file_get_contents($seedFile);
            if (!is_string($manifest) || !is_string($template) || !is_string($seed)) {
                throw new RuntimeException('Approved layout missing');
            }
            $fields = CmsEditor::fields($manifest);
            $submitted = $_POST['text'] ?? [];
            if (!is_array($submitted) || count($submitted) !== count($fields) ||
                array_diff(array_keys($submitted),array_keys($fields)) ||
                array_diff(array_keys($fields),array_keys($submitted))) {
                throw new InvalidArgumentException('Unexpected CMS form');
            }
            $edited = [];
            foreach ($fields as $key=>$field) {
                $value = $submitted[$key];
                if (!is_string($value)) throw new InvalidArgumentException('Not text');
                if (trim($value) !== trim((string)$field['default'])) {
                    $edited[$key] = $value;
                }
            }
            $snapshot = ['content'=>$edited,'faq'=>[]];
            CmsEditor::validate($template,$manifest,$seed,$snapshot);
            $expected = filter_var($_POST['version'] ?? null,FILTER_VALIDATE_INT);
            if (!is_int($expected) || $expected < 0) {
                throw new InvalidArgumentException('Missing draft version');
            }
            $newVersion = CmsDraftStore::save($pdo,$admin,$expected,$snapshot);
            if ($newVersion === null) {
                http_response_code(409);
                $error = 'Черновик изменён в другой вкладке. Обновите страницу.';
            } else {
                header('Location: /admin/?saved=1',true,303);
                exit;
            }
        } catch (\InvalidArgumentException $e) {
            http_response_code(422);
            $error = 'Проверьте длину и содержимое полей.';
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: draft save failed');
            http_response_code(503);
            $error = 'Черновик не сохранён. Повторите позже.';
        }
    } else {
        http_response_code(403);
        $error = 'Операция недоступна.';
    }
}
function cmsEscape(string $text): string
{
    return Content::escape($text);
}
$csrf = Security::csrfToken();
if ($admin !== null && $_SERVER['REQUEST_METHOD'] === 'GET' && ($_GET['view'] ?? '') === 'preview') {
    try {
        $saved = CmsDraftStore::get($pdo);
        $manifest = file_get_contents($app.'/Config/content-fields-v10.json');
        $html = file_get_contents($app.'/Templates/site-v10.html');
        $seed = file_get_contents($dev
            ? $root.'/database/seeds/faq-v10.json'
            : $root.'/celikom-private/database/seeds/faq-v10.json');
        if (!is_string($manifest) || !is_string($html) || !is_string($seed)) {
            throw new RuntimeException('Missing approved preview files');
        }
        echo CmsEditor::validate($html,$manifest,$seed,[
            'content'=>$saved['content'],'faq'=>$saved['faq']
        ]);
    } catch (\Throwable $e) {
        error_log('CELIKOM CMS: preview failed');
        http_response_code(503);
        echo 'Предпросмотр временно недоступен.';
    }
    exit;
}
$fields = [];
$current = ['version'=>0,'content'=>[],'faq'=>[]];
if ($admin !== null) {
    try {
        $manifest = file_get_contents($app.'/Config/content-fields-v10.json');
        if (!is_string($manifest)) throw new RuntimeException('Missing manifest');
        $fields = CmsEditor::fields($manifest);
        $current = CmsDraftStore::get($pdo);
    } catch (\Throwable $e) {
        error_log('CELIKOM CMS: draft could not be loaded');
        http_response_code(503);
        echo 'Редактор временно недоступен.';
        exit;
    }
}
?><!doctype html>
<html lang="ru"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>CELIKOM — управление сайтом</title>
<style>
:root{font-family:system-ui,sans-serif;color:#F7F8F4;background:#0B1013}
*{box-sizing:border-box}body{margin:0;padding:24px}main{max-width:1040px;margin:0 auto}
h1{font-size:clamp(24px,4vw,38px)}h2{font-size:20px;margin-top:32px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
form{margin:0}.panel{padding:24px;border:1px solid #375048;border-radius:18px;background:#14201D}
label{display:block;margin:18px 0 6px;font-size:14px}
input,textarea{display:block;width:100%;padding:12px;color:#111;background:#F7F8F4;border:1px solid #95B1A7;border-radius:9px;font:inherit}
textarea{min-height:92px;resize:vertical}
button,.action{display:inline-block;cursor:pointer;margin-top:14px;padding:12px 20px;border:0;border-radius:999px;background:#66E0BF;color:#071814;font-weight:700;text-decoration:none;font:inherit}
.action{margin-left:10px}.muted{color:#B8CAC4;font-size:14px}.error{color:#FFC7BF}.ok{color:#9BE8CE}
fieldset{border:0;padding:0;margin:0}fieldset+fieldset{margin-top:32px}
@media(max-width:600px){body{padding:12px}.panel{padding:16px}.action{margin-left:0}}
</style></head><body><main><header><h1>CELIKOM · сайт</h1>
<?php if ($admin !== null): ?>
<form method="post" action="/admin/"><input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/><input type="hidden" name="action" value="logout"/><button type="submit">Выйти</button></form>
<?php endif; ?></header>
<?php if ($error !== null): ?><p role="alert" class="error"><?=cmsEscape($error)?></p><?php endif; ?>
<?php if ($admin === null): ?>
<section class="panel"><h2>Вход администратора</h2>
<p class="muted">Управление сайтом доступно только владельцу.</p>
<form method="post" action="/admin/">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/><input type="hidden" name="action" value="login"/>
<label for="username">Логин</label><input id="username" name="username" autocomplete="username" required maxlength="80"/>
<label for="password">Пароль</label><input id="password" type="password" name="password" autocomplete="current-password" required/>
<button type="submit">Войти</button></form></section>
<?php else: ?>
<section class="panel"><h2>Черновик текстов</h2>
<p class="muted">Редактируются только безопасные заголовки и пояснения доверия, FAQ, установки и футера. Версия <?= (int)$current['version']?>. Публикация пока недоступна.</p>
<?php if (($_GET['saved'] ?? null) === '1'): ?><p class="ok" role="status">Черновик сохранён в базе данных.</p><?php endif; ?>
<form method="post" action="/admin/">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/><input type="hidden" name="action" value="save"/>
<input type="hidden" name="version" value="<?= (int)$current['version']?>"/>
<?php $previousSection=''; foreach($fields as $key=>$field):
$section=(string)$field['section'];
if ($section!==$previousSection):
    if ($previousSection!=='') echo '</fieldset>';
    echo '<fieldset><h2>'.cmsEscape($section).'</h2>';
    $previousSection=$section;
endif;
$value=$current['content'][$key]??$field['default'];
?>
<label for="<?=cmsEscape($key)?>"><?=cmsEscape((string)$field['label'])?></label>
<textarea id="<?=cmsEscape($key)?>" name="text[<?=cmsEscape($key)?>]" maxlength="<?= (int)$field['max_chars']?>"><?=cmsEscape((string)$value)?></textarea>
<?php endforeach; if($previousSection!=='')echo '</fieldset>'; ?>
<button type="submit">Сохранить черновик</button>
<a class="action" href="/admin/?view=preview" target="_blank" rel="noopener">Предпросмотр сохранённого</a>
</form></section>
<?php endif; ?>
</main></body></html>
