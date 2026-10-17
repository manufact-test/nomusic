<?php
declare(strict_types=1);
require dirname(__DIR__).'/app/bootstrap.php';

use Celikom\Website\AdminAuth;
use Celikom\Website\CmsConfig;
use Celikom\Website\CmsDraftStore;
use Celikom\Website\CmsEditor;
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
cmsAssert(count($fields)===21,'Stage 9 first-slice 21 safely editable fields');
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
echo "Stage9: MySQL 11 tables, auth throttling, secure sessions/CSRF, draft conflicts, no publish — PASS\n";
