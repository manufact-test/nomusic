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
$releaseApproved = $dev;
if (!$dev && is_file($app.'/bootstrap.php')) {
    require_once $app.'/bootstrap.php';
    $releaseApproved = \Celikom\Website\CmsReleaseGate::approved($app);
}
if (!$releaseApproved) {
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
use Celikom\Website\CmsFaqManager;
use Celikom\Website\CmsRevisions;
use Celikom\Website\CmsMediaStore;
use Celikom\Website\CmsMediaAssignment;
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
            $previous=CmsDraftStore::get($pdo);
            $snapshot = ['content'=>$edited,'faq'=>$previous['faq']];
            CmsEditor::validate($template,$manifest,$seed,$snapshot);
            $expected = filter_var($_POST['version'] ?? null,FILTER_VALIDATE_INT);
            if (!is_int($expected) || $expected < 0) {
                throw new InvalidArgumentException('Missing draft version');
            }
            $newVersion = $previous['version'] === $expected
                ? CmsDraftStore::save($pdo,$admin,$expected,$snapshot) : null;
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
    } elseif (($action === 'faq_update' || $action === 'faq_create') && $admin !== null) {
        try {
            $manifest=file_get_contents($app.'/Config/content-fields-v10.json');
            $template=file_get_contents($app.'/Templates/site-v10.html');
            $seed=file_get_contents($dev
                ? $root.'/database/seeds/faq-v10.json'
                : $root.'/celikom-private/database/seeds/faq-v10.json');
            if(!is_string($manifest)||!is_string($template)||!is_string($seed)) {
                throw new RuntimeException('Missing approved FAQ source');
            }
            $expected=filter_var($_POST['version']??null,FILTER_VALIDATE_INT);
            if(!is_int($expected)||$expected<0) {
                throw new InvalidArgumentException('Invalid draft version');
            }
            $previous=CmsDraftStore::get($pdo);
            if($expected!==$previous['version']) {
                http_response_code(409);
                $error='Черновик изменён в другой вкладке. Обновите страницу.';
            } else {
                $fields=[
                    'category'=>$_POST['category']??null,
                    'question'=>$_POST['question']??null,
                    'answer'=>$_POST['answer']??null,
                    'sort_order'=>$action==='faq_update'
                        ? filter_var($_POST['sort_order']??null,FILTER_VALIDATE_INT)
                        : 0,
                    'is_visible'=>isset($_POST['visible']) && $_POST['visible']==='1',
                ];
                if($action==='faq_create') {
                    $nextFaq=CmsFaqManager::create($seed,$previous['faq'],$fields);
                } else {
                    $id=$_POST['faq_id']??null;
                    if(!is_string($id))throw new InvalidArgumentException('Invalid FAQ ID');
                    $nextFaq=CmsFaqManager::change($seed,$previous['faq'],$id,$fields);
                }
                $next=['content'=>$previous['content'],'faq'=>$nextFaq];
                CmsEditor::validate($template,$manifest,$seed,$next);
                $saved=CmsDraftStore::save($pdo,$admin,$expected,$next);
                if($saved===null) {
                    http_response_code(409);
                    $error='Черновик изменён в другой вкладке. Обновите страницу.';
                } else {
                    header('Location: /admin/?saved=faq#faq-editor',true,303);
                    exit;
                }
            }
        } catch (\InvalidArgumentException $e) {
            http_response_code(422);
            $error='Проверьте данные FAQ: длину, категорию и доступность правки.';
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: FAQ draft save failed');
            http_response_code(503);
            $error='FAQ не сохранён. Повторите позже.';
        }
    } elseif (($action === 'publish' || $action === 'restore') && $admin !== null) {
        try {
            $expected=filter_var($_POST['version']??null,FILTER_VALIDATE_INT);
            if(!is_int($expected) || $expected<1 ||
                ($_POST['confirm']??null)!=='yes') {
                throw new InvalidArgumentException('Confirm the revision and current version');
            }
            $manifest=file_get_contents($app.'/Config/content-fields-v10.json');
            $template=file_get_contents($app.'/Templates/site-v10.html');
            $seed=file_get_contents($dev
                ? $root.'/database/seeds/faq-v10.json'
                : $root.'/celikom-private/database/seeds/faq-v10.json');
            if(!is_string($manifest)||!is_string($template)||!is_string($seed)) {
                throw new RuntimeException('Approved source unavailable');
            }
            $note=$_POST['note']??null;
            if(!is_string($note))throw new InvalidArgumentException('Invalid revision note');
            // Same release gate as entire /admin/: offline tests do not open
            // the public endpoint, even after publishing a DB snapshot.
            if($action==='publish') {
                $updated=CmsRevisions::publish($pdo,$admin,$expected,$note,
                    $template,$manifest,$seed);
            } else {
                $target=filter_var($_POST['target_revision']??null,FILTER_VALIDATE_INT);
                if(!is_int($target)||$target<1)throw new InvalidArgumentException('Unknown revision');
                $updated=CmsRevisions::restore($pdo,$admin,$target,$expected,$note,
                    $template,$manifest,$seed);
            }
            if($updated===null) {
                http_response_code(409);
                $error='Состояние изменилось в другой вкладке. Обновите страницу.';
            } else {
                header('Location: /admin/?saved='.($action==='publish'?'published':'restored').'#revision-editor',
                    true,303);
                exit;
            }
        } catch (\InvalidArgumentException $e) {
            http_response_code(422);
            $error='Проверьте выбранную редакцию, комментарий и подтверждение.';
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: revision operation failed');
            http_response_code(503);
            $error='Операция с редакцией не выполнена.';
        }
    } elseif ($action === 'media_upload' && $admin !== null) {
        try {
            $directory=getenv('CELIKOM_SITE_MEDIA_DIR');
            if(!is_string($directory) || $directory==='') {
                throw new RuntimeException('Private media path is not configured');
            }
            $uploaded=$_FILES['image']??null;
            $alt=$_POST['alt']??null;
            if(!is_array($uploaded) || !is_string($alt)) {
                throw new InvalidArgumentException('Invalid media upload form');
            }
            CmsMediaStore::accept($pdo,$admin,$uploaded,$alt,
                $directory,$root.'/public');
            header('Location: /admin/?saved=media#media-editor',true,303);
            exit;
        } catch (\InvalidArgumentException $e) {
            http_response_code(422);
            $error='Изображение отклонено: проверьте формат PNG/JPEG/WebP, размер до 2 МБ, размеры и alt.';
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: private media upload unavailable');
            http_response_code(503);
            $error='Медиафайл не сохранён в защищённое хранилище.';
        }
    } elseif ($action === 'media_select' && $admin !== null) {
        try {
            $folder=getenv('CELIKOM_SITE_MEDIA_DIR');
            if(!is_string($folder) || $folder==='') {
                throw new RuntimeException('Private media storage not configured');
            }
            $expected=filter_var($_POST['selection_version']??null,FILTER_VALIDATE_INT);
            $inputId=$_POST['asset_id']??null;
            if(!is_int($expected) || $expected<0 || !is_string($inputId)) {
                throw new InvalidArgumentException('Invalid image selection');
            }
            $chosen=$inputId==='original' ? null : filter_var($inputId,FILTER_VALIDATE_INT);
            if($chosen===false || ($chosen!==null && $chosen<1)) {
                throw new InvalidArgumentException('Unknown image selection');
            }
            $new=CmsMediaAssignment::choose($pdo,$admin,$expected,$chosen,
                $folder,$root.'/public');
            if($new===null) {
                http_response_code(409);
                $error='Изображение уже выбрано в другой вкладке. Обновите страницу.';
            } else {
                header('Location: /admin/?saved=media-choice#media-editor',true,303);
                exit;
            }
        } catch (\InvalidArgumentException $e) {
            http_response_code(422);
            $error='Выберите доступное изображение из библиотеки.';
        } catch (\Throwable $e) {
            error_log('CELIKOM CMS: private media selection unavailable');
            http_response_code(503);
            $error='Предварительный выбор изображения не сохранён.';
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
if ($admin !== null && $_SERVER['REQUEST_METHOD'] === 'GET' &&
    ($_GET['view'] ?? '') === 'media') {
    try {
        $id=filter_var($_GET['id']??null,FILTER_VALIDATE_INT);
        $folder=getenv('CELIKOM_SITE_MEDIA_DIR');
        if(!is_int($id) || $id<1 || !is_string($folder) || $folder==='') {
            throw new InvalidArgumentException('Unknown private image');
        }
        $image=CmsMediaStore::privatePreview($pdo,$id,$folder,$root.'/public');
        header('Content-Type: '.$image['mime']);
        header('Content-Length: '.strlen($image['body']));
        header('Content-Disposition: inline; filename="celikom-private-preview"');
        header('Cross-Origin-Resource-Policy: same-origin');
        echo $image['body'];
    } catch (\InvalidArgumentException $e) {
        http_response_code(404);
        echo 'Изображение не найдено.';
    } catch (\Throwable $e) {
        error_log('CELIKOM CMS: private media preview unavailable');
        http_response_code(503);
        echo 'Изображение временно недоступно.';
    }
    exit;
}
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
        $preview=CmsEditor::validate($html,$manifest,$seed,[
            'content'=>$saved['content'],'faq'=>$saved['faq']
        ]);
        $selection=CmsMediaAssignment::get($pdo);
        if($selection['asset_id']!==null) {
            $folder=getenv('CELIKOM_SITE_MEDIA_DIR');
            if(!is_string($folder) || $folder==='') {
                throw new RuntimeException('Selected image requires private storage');
            }
            $media=CmsMediaStore::privatePreview($pdo,$selection['asset_id'],
                $folder,$root.'/public');
            $preview=CmsMediaAssignment::privatePage(
                $preview,$selection['asset_id'],$media['alt']
            );
        }
        echo $preview;
    } catch (\Throwable $e) {
        error_log('CELIKOM CMS: preview failed');
        http_response_code(503);
        echo 'Предпросмотр временно недоступен.';
    }
    exit;
}
$fields = [];
$current = ['version'=>0,'content'=>[],'faq'=>[]];
$faqItems=[];
$history=[];
$published=null;
$mediaFiles=[];
$mediaSelection=['version'=>0,'asset_id'=>null];
$mediaEnabled=is_string(getenv('CELIKOM_SITE_MEDIA_DIR')) &&
    is_dir((string)getenv('CELIKOM_SITE_MEDIA_DIR'));
if ($admin !== null) {
    try {
        $manifest = file_get_contents($app.'/Config/content-fields-v10.json');
        if (!is_string($manifest)) throw new RuntimeException('Missing manifest');
        $fields = CmsEditor::fields($manifest);
        $current = CmsDraftStore::get($pdo);
        $faqSeed=file_get_contents($dev
            ? $root.'/database/seeds/faq-v10.json'
            : $root.'/celikom-private/database/seeds/faq-v10.json');
        if(!is_string($faqSeed))throw new RuntimeException('FAQ seed missing');
        $faqItems=CmsFaqManager::rows($faqSeed,$current['faq']);
        $history=CmsRevisions::history($pdo);
        $published=CmsRevisions::publishedId($pdo);
        $mediaFiles=CmsMediaStore::recent($pdo);
        $mediaSelection=CmsMediaAssignment::get($pdo);
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
.section-editor{margin:12px 0;border:1px solid #375048;border-radius:12px;padding:0 14px}
.section-editor summary{cursor:pointer;padding:16px 0;font-weight:700;font-size:18px;list-style:revert}
.section-editor[open] summary{border-bottom:1px solid #375048}
.section-editor label:last-child{margin-bottom:18px}
.section-editor summary:focus-visible,.faq-entry summary:focus-visible{outline:2px solid #66E0BF;outline-offset:4px}
.panel{min-width:0}input,textarea,select{max-width:100%;min-width:0}
/* Owner-only CMS: comfortable touch targets, including native mobile selects. */
button,.action,select,input:not([type="checkbox"]):not([type="hidden"]){min-height:44px}

select{display:block;width:100%;padding:10px;border-radius:9px;font:inherit}
.faq-entry{padding:12px 0;border-bottom:1px solid #375048}
.faq-entry summary{cursor:pointer;font-weight:600;display:flex;align-items:center;min-height:44px}
.faq-entry form{padding:14px 0}
.faq-fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.faq-fields label{margin-top:0}
.faq-fields .wide{grid-column:1/-1}
.inline-check{display:flex;align-items:center;gap:8px}
.inline-check input{width:auto}
.secnav{display:flex;flex-wrap:wrap;gap:16px;margin:14px 0 24px}
.secnav a{color:#9BE8CE}
.revision-row{display:flex;gap:14px;align-items:center;flex-wrap:wrap;
padding:12px 0;border-bottom:1px solid #375048}
.revision-row form{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.revision-row label{margin:0}
.revision-row input[type="checkbox"]{width:auto}
.revision-current{font-weight:700;color:#9BE8CE}
.small-note{font-size:13px;color:#B8CAC4}

@media(max-width:600px){.faq-fields{grid-template-columns:1fr}}

@media(max-width:600px){
body{padding:12px;padding-bottom:calc(16px + env(safe-area-inset-bottom))}
main{width:100%;min-width:0}
.panel{padding:16px}
.section-editor{margin:10px 0;padding:0 10px}
button,.action{width:100%;margin-left:0;text-align:center}
.revision-row,.revision-row form{width:100%;align-items:stretch;flex-direction:column}
header{align-items:center}
header form{flex:0 0 auto}
header button{width:auto}
.secnav{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.secnav a{display:block;min-height:44px;padding:10px;border:1px solid #375048;border-radius:10px}
label.inline-check{min-height:44px}
.faq-fields{grid-template-columns:1fr}
}

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
<section class="panel" id="text-editor"><h2>Черновик текстов</h2>
<p class="muted">Редактор v10: тексты, ссылки, SEO и FAQ. Черновик №<?= (int)$current['version']?>.
<?php if($dev): ?>Тестовая публикация сохраняется только в отдельную MySQL, сайт посетителям закрыт.
<?php else: ?>Публикация доступна только после подтверждённого выпуска сайта.
<?php endif; ?></p>
<nav class="secnav" aria-label="Разделы редактора">
<a href="#text-editor">Секции сайта</a><a href="#faq-editor">Вопросы FAQ</a>
<a href="#revision-editor">Публикации и откат</a>
<a href="#media-editor">Медиа</a>
<a href="/admin/?view=preview" target="_blank" rel="noopener">Предпросмотр</a>
</nav>
<?php if (in_array($_GET['saved'] ?? '', ['1','faq'], true)): ?><p class="ok" role="status">Черновик сохранён в базе данных.</p><?php endif; ?>
<?php if (($_GET['saved']??'')==='published'): ?><p class="ok" role="status">Редакция опубликована в MySQL. Публичный сайт не открыт.</p><?php endif; ?>
<?php if (($_GET['saved']??'')==='media-choice'): ?><p class="ok" role="status">Для закрытого предпросмотра выбрано изображение. Публичный сайт и редакции не изменены.</p><?php endif; ?>
<?php if (($_GET['saved']??'')==='media'): ?><p class="ok" role="status">Изображение сохранено приватно. На сайте оно пока не используется.</p><?php endif; ?>
<?php if (($_GET['saved']??'')==='restored'): ?><p class="ok" role="status">Предыдущая редакция восстановлена в MySQL. Черновик не изменился.</p><?php endif; ?>
<form method="post" action="/admin/">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/><input type="hidden" name="action" value="save"/>
<input type="hidden" name="version" value="<?= (int)$current['version']?>"/>
<?php $previousSection=''; foreach($fields as $key=>$field):
$section=(string)$field['section'];
if ($section!==$previousSection):
    if ($previousSection!=='') echo '</div></details>';
    echo '<details class="section-editor"'.($previousSection===''?' open':'').'><summary>'.cmsEscape((string)($field['section_label']??$section)).'</summary><div>';
    $previousSection=$section;
endif;
$value=$current['content'][$key]??$field['default'];
?>
<label for="<?=cmsEscape($key)?>"><?=cmsEscape((string)$field['label'])?></label>
<textarea id="<?=cmsEscape($key)?>" name="text[<?=cmsEscape($key)?>]" maxlength="<?= (int)($field['max_chars']??100)?>"><?=cmsEscape((string)$value)?></textarea>
<?php endforeach; if($previousSection!=='')echo '</div></details>'; ?>
<button type="submit">Сохранить черновик</button>
<a class="action" href="/admin/?view=preview" target="_blank" rel="noopener">Предпросмотр сохранённого</a>
</form></section>
<section class="panel" id="faq-editor" style="margin-top:24px">
<h2>FAQ · вопросы и ответы</h2>
<p class="muted">Защищённые продуктовые условия доступны только для чтения. Новые вопросы создаются скрытыми — их нужно проверить перед показом на сайте. Все изменения сначала сохраняются как черновик.</p>
<?php foreach ($faqItems as $faqItem): ?>
<details class="faq-entry"><summary>
<?=cmsEscape((string)$faqItem['question'])?>
<?php if($faqItem['protected']): ?>(защищённый текст)<?php elseif(!$faqItem['is_visible']): ?>(скрыт)<?php endif; ?>
</summary>
<?php if($faqItem['protected']): ?>
<p class="muted">Факты о продукте, праве и оплате зафиксированы до отдельного согласования.</p>
<?php else: ?>
<form method="post" action="/admin/#faq-editor">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="faq_update"/>
<input type="hidden" name="version" value="<?= (int)$current['version']?>"/>
<input type="hidden" name="faq_id" value="<?=cmsEscape((string)$faqItem['id'])?>"/>
<div class="faq-fields">
<label class="wide">Вопрос
<input name="question" required maxlength="400" value="<?=cmsEscape((string)$faqItem['question'])?>"/></label>
<label class="wide">Ответ
<textarea name="answer" required maxlength="3000"><?=cmsEscape((string)$faqItem['answer'])?></textarea></label>
<label>Категория<select name="category">
<?php foreach (['start'=>'Установка и работа','rewards'=>'Бонусы и стоимость','music'=>'Песни и модерация','help'=>'Аккаунт и помощь'] as $cat=>$catName): ?>
<option value="<?=cmsEscape($cat)?>" <?= $faqItem['category']===$cat?'selected':''?>><?=cmsEscape($catName)?></option>
<?php endforeach; ?>
</select></label>
<label>Порядок<input type="number" name="sort_order" min="0" max="100000" required value="<?= (int)$faqItem['sort_order']?>"/></label>
<label class="inline-check wide"><input type="checkbox" name="visible" value="1" <?= $faqItem['is_visible']?'checked':''?>/>Показывать вопрос</label>
</div>
<button type="submit">Сохранить вопрос в черновик</button>
</form>
<?php endif; ?>
</details>
<?php endforeach; ?>
<h2>Добавить вопрос</h2>
<form method="post" action="/admin/#faq-editor">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="faq_create"/>
<input type="hidden" name="version" value="<?= (int)$current['version']?>"/>
<label>Вопрос<input name="question" required maxlength="400"/></label>
<label>Ответ<textarea name="answer" required maxlength="3000"></textarea></label>
<label>Категория<select name="category">
<option value="help">Аккаунт и помощь</option>
<option value="start">Установка и работа</option>
<option value="music">Песни и модерация</option>
<option value="rewards">Бонусы и стоимость</option>
</select></label>
<button type="submit">Добавить скрытый вопрос в черновик</button>
</form>
</section>
<section class="panel" id="revision-editor" style="margin-top:24px">
<h2>Публикация и история</h2>
<p class="muted">Текущая опубликованная редакция:
<?= $published===null?'отсутствует':'№'.(int)$published ?>.
Публикация создаёт неизменяемый снимок. Черновик остаётся отдельно. В тестовой среде публичный сайт остаётся закрытым независимо от публикации.</p>
<form method="post" action="/admin/#revision-editor">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="publish"/>
<input type="hidden" name="version" value="<?=(int)$current['version']?>"/>
<label for="publication-note">Комментарий к публикации</label>
<input id="publication-note" name="note" maxlength="255" value="" placeholder="Что изменилось?"/>
<label class="inline-check"><input type="checkbox" name="confirm" value="yes" required/>
Подтверждаю публикацию сохранённого черновика №<?= (int)$current['version']?></label>
<button type="submit" <?= $current['version']<1?'disabled':''?>>Опубликовать редакцию в базе</button>
</form>
<h2>История редакций</h2>
<?php if ($history===[]): ?><p class="muted">Публикаций ещё не было.</p><?php endif; ?>
<?php foreach ($history as $revision): ?>
<div class="revision-row">
<div><strong>№<?=(int)$revision['id']?></strong>
<?php if($published===$revision['id']): ?><span class="revision-current"> · текущая</span><?php endif; ?>
<div class="small-note"><?=cmsEscape($revision['at'])?> · <?=cmsEscape($revision['note'])?></div></div>
<?php if ($published!==null && $published!==$revision['id']): ?>
<form method="post" action="/admin/#revision-editor">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="restore"/>
<input type="hidden" name="version" value="<?=(int)$published?>"/>
<input type="hidden" name="target_revision" value="<?=(int)$revision['id']?>"/>
<input type="hidden" name="note" value="Восстановление редакции №<?=(int)$revision['id']?>"/>
<label class="inline-check"><input type="checkbox" name="confirm" value="yes" required/>
Подтверждаю откат</label>
<button type="submit">Восстановить №<?=(int)$revision['id']?></button>
</form>
<?php endif; ?>
</div>
<?php endforeach; ?>
</section>
<section class="panel" id="media-editor" style="margin-top:24px">
<h2>Библиотека медиа</h2>
<p class="muted">Можно назначить изображение только для закрытого предпросмотра popup. Публичный макет и опубликованные редакции сохраняют исходный проверенный скриншот.</p>
<?php if($mediaEnabled): ?>
<form method="post" action="/admin/#media-editor">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="media_select"/>
<input type="hidden" name="selection_version" value="<?=(int)$mediaSelection['version']?>"/>
<label for="media-pending-id">Изображение для закрытого предпросмотра</label>
<select id="media-pending-id" name="asset_id">
<option value="original" <?=$mediaSelection['asset_id']===null?'selected':''?>>Исходный скриншот v10</option>
<?php foreach($mediaFiles as $item): ?>
<option value="<?=(int)$item['id']?>" <?=$mediaSelection['asset_id']===(int)$item['id']?'selected':''?>>#<?=(int)$item['id']?> · <?=cmsEscape((string)$item['original_filename'])?></option>
<?php endforeach; ?>
</select>
<button type="submit">Сохранить выбор только для предпросмотра</button>
<a class="action" href="/admin/?view=preview" target="_blank" rel="noopener">Открыть закрытый предпросмотр</a>
</form>
<?php endif; ?>
<p class="muted">Изображения только в отдельное защищённое хранилище, не в public_html.
Просмотр загруженных файлов доступен только администратору. Замена изображения на публичном сайте потребует отдельной проверки прав и подтверждения запуска.</p>
<?php if($mediaEnabled): ?>
<form method="post" action="/admin/#media-editor" enctype="multipart/form-data">
<input type="hidden" name="csrf" value="<?=cmsEscape($csrf)?>"/>
<input type="hidden" name="action" value="media_upload"/>
<label>Изображение (PNG/JPEG/WebP, до 2 МБ)
<input type="file" name="image" accept="image/png,image/jpeg,image/webp" required/></label>
<label>Описание изображения для доступности
<input name="alt" type="text" required maxlength="300"/></label>
<button type="submit">Сохранить приватно</button>
</form>
<?php else: ?>
<p class="muted">Загрузка отключена: каталог приватного хранения не настроен.</p>
<?php endif; ?>
<?php if($mediaFiles===[]): ?><p class="muted">Файлы ещё не загружены.</p><?php endif; ?>
<?php foreach($mediaFiles as $asset): ?>
<div class="revision-row">
<img src="/admin/?view=media&amp;id=<?=(int)$asset['id']?>" alt="<?=cmsEscape((string)$asset['alt_text'])?>" loading="lazy" width="140" height="90" style="width:140px;height:auto;max-height:110px;object-fit:contain;border:1px solid #375048;border-radius:8px"/>
<strong>#<?=(int)$asset['id']?></strong>
<span><?=cmsEscape((string)$asset['original_filename'])?></span>
<span class="small-note"><?=cmsEscape((string)$asset['mime_type'])?> ·
<?=(int)$asset['pixel_width']?>×<?=(int)$asset['pixel_height']?></span>
<span><?=cmsEscape((string)$asset['alt_text'])?></span>
</div>
<?php endforeach; ?>
</section>
<?php endif; ?>
</main></body></html>
