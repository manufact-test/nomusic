<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\AdminAuth;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsDraftStore;
use Celikom\Website\CmsEditor;
use Celikom\Website\CmsRevisions;
use Celikom\Website\Database;
use Celikom\Website\Security;

function cmsAssert(bool $value, string $message): void {
    if (!$value) throw new RuntimeException($message);
}
function cmsReject(callable $callback, string $reason): void {
    try { $callback(); } catch (\InvalidArgumentException|\RuntimeException $expected) { return; }
    throw new RuntimeException('CMS safety invariant missing: '.$reason);
}
$base=dirname(__DIR__);
$pdo=Database::connect(CmsConfig::databaseSettings());
$pdo->exec("SET time_zone = '+00:00'");
$schema=file_get_contents($base.'/database/migrations/001_website_cms.sql');
if (!is_string($schema)) throw new RuntimeException('Missing schema');
$schema=preg_replace('/^--.*$/m','',$schema);
foreach(explode(';',$schema) as $ddl){
    if(trim($ddl)!=='') $pdo->exec(trim($ddl));
}
cmsAssert($pdo->query('SELECT published_revision_id FROM site_state WHERE id=1')->fetchColumn()===null,
    'Site must begin unpublished');
cmsReject(fn()=>AdminAuth::authenticate($pdo,'owner','password','127.0.0.1','short',1000),'weak HMAC key');
cmsReject(fn()=>AdminAuth::authenticate($pdo,'owner','password','unknown','x',1000),'invalid IP');
$secret=str_repeat('K',40);
$hash=password_hash('valid-Admin!2026-OnlyForCI',PASSWORD_DEFAULT);
$pdo->prepare('INSERT INTO admin_users(username,password_hash,is_active) VALUES (?,?,1)')
    ->execute(['owner',$hash]);
$id=(int)$pdo->lastInsertId();
cmsAssert($id>0,'Owner test identity');
$now=1770000000;
cmsAssert(AdminAuth::authenticate($pdo,'absent','incorrect','198.51.100.10',$secret,$now)===null,'Unknown user denied');
cmsAssert(AdminAuth::authenticate($pdo,'owner','incorrect','198.51.100.11',$secret,$now)===null,'Wrong password denied');
cmsAssert(AdminAuth::authenticate($pdo,'owner','valid-Admin!2026-OnlyForCI','198.51.100.12',$secret,$now)===$id,
    'Correct password must authenticate');
$wrongIP='198.51.100.13';
for($i=0;$i<5;$i++){
    cmsAssert(AdminAuth::authenticate($pdo,'absent'.(string)$i,'bad',$wrongIP,$secret,$now+$i)===null,
        'Failed login not denied');
}
cmsAssert(AdminAuth::authenticate($pdo,'owner','valid-Admin!2026-OnlyForCI',$wrongIP,$secret,$now+5)===null,
    'Per-IP lock did not block correct credentials');
cmsAssert(AdminAuth::authenticate($pdo,'owner','valid-Admin!2026-OnlyForCI',$wrongIP,$secret,$now+906)===$id,
    'Lock never expires');
$pdo->prepare('UPDATE admin_users SET is_active=0 WHERE id=?')->execute([$id]);
cmsAssert(AdminAuth::authenticate($pdo,'owner','valid-Admin!2026-OnlyForCI','198.51.100.14',$secret,$now+901)===null,
    'Inactive admin allowed');
$pdo->prepare('UPDATE admin_users SET is_active=1 WHERE id=?')->execute([$id]);

cmsReject(fn()=>Security::startAdminSession(false),'HTTP admin session');
Security::startAdminSession(true);
$csrf=Security::csrfToken();
cmsAssert(strlen($csrf)===64 && Security::verifyCsrf($csrf),'CSRF generation');
cmsAssert(!Security::verifyCsrf('wrong') && !Security::verifyCsrf([]),'CSRF validation');
AdminAuth::finishLogin($id);
cmsAssert(!Security::verifyCsrf($csrf),'Old CSRF survives privilege transition');
cmsAssert(AdminAuth::checkSession($pdo,$now)===null,'Suspicious future timestamp session accepted');
AdminAuth::finishLogin($id);
$_SESSION['authenticated_at']=$now;
$_SESSION['last_seen_at']=$now;
cmsAssert(AdminAuth::checkSession($pdo,$now)===$id,'Valid owner session rejected');
cmsAssert(AdminAuth::checkSession($pdo,$now+1801)===null,'Idle timeout not enforced');
cmsAssert(!isset($_SESSION['cms_admin_id']),'Expired session kept admin authorization');
AdminAuth::finishLogin($id);

$template=file_get_contents($base.'/app/Templates/site-v10.html');
$manifest=file_get_contents($base.'/app/Config/content-fields-v10.json');
$seed=file_get_contents($base.'/database/seeds/faq-v10.json');
if(!is_string($template)||!is_string($manifest)||!is_string($seed)) throw new RuntimeException('v10 missing');
$fields=CmsEditor::fields($manifest);
cmsAssert(count($fields)===84,'Stage 9 safe copy/link fields across sections');
$draft=['content'=>['faq.text.02'=>'Вопросы CELIKOM сегодня.'],'faq'=>[]];
$page=CmsEditor::validate($template,$manifest,$seed,$draft);
cmsAssert(str_contains($page,'Вопросы CELIKOM сегодня.'),'Editor does not render draft');
cmsAssert(substr_count($page,'class="faq-item"')===28,'Draft modified FAQ structure');
cmsAssert(str_contains($page,'Идёт тестирование'),'Editor removed launch lock');
cmsReject(fn()=>CmsEditor::validate($template,$manifest,$seed,[
    'content'=>['install.status'=>'Уже доступно'],'faq'=>[]
]),'CMS opened release status');
cmsReject(fn()=>CmsEditor::validate($template,$manifest,$seed,[
    'content'=>['rewards.text.03'=>'100% бесплатно'],'faq'=>[]
]),'CMS changed financial terms');
cmsReject(fn()=>CmsEditor::validate($template,$manifest,$seed,[
    'content'=>['faq.text.02'=>''],'faq'=>[]
]),'CMS allowed empty headline');
cmsReject(fn()=>CmsEditor::validate($template,$manifest,$seed,[
    'content'=>[],'faq'=>['updates'=>['faq-question-08'=>['answer'=>'Pay now']]]
]),'FAQ bypassed guarded scope');
cmsAssert(CmsDraftStore::get($pdo)['version']===0,'Draft must begin empty');
cmsAssert(CmsDraftStore::save($pdo,$id,0,$draft)===1,'Draft save v1');
cmsAssert(CmsDraftStore::get($pdo)['content']===$draft['content'],'Draft round trip');
cmsAssert(CmsDraftStore::save($pdo,$id,0,$draft)===null,'Stale version overwrote draft');
cmsAssert(CmsDraftStore::get($pdo)['version']===1,'Stale save mutated version');
$next=['content'=>['faq.text.02'=>'Ответы на вопросы CELIKOM.'],'faq'=>[]];
cmsAssert(CmsDraftStore::save($pdo,$id,1,$next)===2,'Draft save v2');
cmsAssert(CmsDraftStore::get($pdo)['content']===$next['content'],'New draft lost');
cmsAssert($pdo->query('SELECT published_revision_id FROM site_state WHERE id=1')->fetchColumn()===null,
    'Draft unexpectedly published');
cmsAssert((int)$pdo->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn()===0,
    'Draft generated a published revision');
cmsAssert((int)$pdo->query("SELECT COUNT(*) FROM audit_log WHERE event_name='cms.draft.saved'")->fetchColumn()===2,
    'Draft changes not audited');
$audit=(string)$pdo->query('SELECT GROUP_CONCAT(CONCAT(event_name,":",COALESCE(subject_key,""))) FROM audit_log')->fetchColumn();
cmsAssert(!str_contains($audit,'198.51.100.') && !str_contains($audit,'valid-Admin!'),
    'Audit stored IP/password');
// Stage 9G: all publication state changes are an atomic pointer swap to
// immutable whole-page snapshots. This never releases the public website.
cmsAssert(CmsRevisions::publishedId($pdo)===null,'Unpublished site has a revision ID');
cmsAssert(CmsRevisions::publishedPage($pdo,$template,$manifest,$seed)===$template,
    'Pre-publication v10 is not canonical');
$first=CmsRevisions::publish($pdo,$id,2,'Первый снимок',$template,$manifest,$seed);
cmsAssert(is_int($first) && $first>0,'First revision not created');
cmsAssert(CmsRevisions::publishedId($pdo)===$first,'Published pointer mismatch');
cmsAssert(str_contains(CmsRevisions::publishedPage($pdo,$template,$manifest,$seed),
    'Ответы на вопросы CELIKOM.'),'Published page lost complete saved draft');
cmsAssert(CmsRevisions::publish($pdo,$id,1,'Старый черновик',$template,$manifest,$seed)===null,
    'Old draft version published');
cmsAssert(CmsRevisions::publishedId($pdo)===$first,'Stale publish switched pointer');
cmsAssert(CmsDraftStore::save($pdo,$id,2,[
    'content'=>['faq.text.02'=>'Справка CELIKOM: изменения.'],'faq'=>[]
])===3,'New draft cannot be saved after publication');
cmsAssert(CmsRevisions::publishedId($pdo)===$first &&
    str_contains(CmsRevisions::publishedPage($pdo,$template,$manifest,$seed),
        'Ответы на вопросы CELIKOM.'),
    'Unpublished draft leaked into public snapshot');
$second=CmsRevisions::publish($pdo,$id,3,'Второй снимок',$template,$manifest,$seed);
cmsAssert(is_int($second) && $second>$first,'Second revision invalid');
cmsAssert(str_contains(CmsRevisions::publishedPage($pdo,$template,$manifest,$seed),
    'Справка CELIKOM: изменения.'),'Second snapshot not loaded');
cmsAssert(CmsRevisions::restore($pdo,$id,$first,$first,'Устаревшая вкладка',$template,$manifest,$seed)===null,
    'Concurrent rollback succeeded');
$restore=CmsRevisions::restore($pdo,$id,$first,$second,'Откат редакции',$template,$manifest,$seed);
cmsAssert(is_int($restore) && $restore>$second && CmsRevisions::publishedId($pdo)===$restore,
    'Restore did not create a new immutable revision');
cmsAssert(str_contains(CmsRevisions::publishedPage($pdo,$template,$manifest,$seed),
    'Ответы на вопросы CELIKOM.'),'Restore did not recover first snapshot');
cmsAssert((int)$pdo->query('SELECT COUNT(*) FROM content_revisions')->fetchColumn()===3,
    'Revision history mutated or missing');
cmsAssert(CmsDraftStore::get($pdo)['version']===3,'Publishing changed editable draft');
cmsReject(fn()=>CmsRevisions::restore(
    $pdo,$id,999999,$restore,'Missing revision',$template,$manifest,$seed
),'Invalid restore target');
cmsReject(fn()=>CmsRevisions::publish(
    $pdo,$id,3,"Note\x00bad",$template,$manifest,$seed
),'Control character in revision note');
cmsAssert(CmsRevisions::publishedId($pdo)===$restore,'Rejected revision changed publication');
cmsAssert((int)$pdo->query("SELECT COUNT(*) FROM audit_log WHERE event_name LIKE 'cms.revision.%'")->fetchColumn()===3,
    'Publish/rollback audit count');
echo "Stage9: MySQL auth, sessions, safe drafts, immutable atomic publish and rollback — PASS\n";
