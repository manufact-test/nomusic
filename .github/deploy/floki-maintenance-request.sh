#!/bin/bash
set -Eeuo pipefail
umask 077
php <<'PHP'
<?php
declare(strict_types=1);
ini_set('display_errors','0');
require '/srv/celikom/app/staging-20261122/bootstrap.php';
$config=require '/srv/celikom/app/staging-20261122/config/app.php';
$pdo=Celikom\Database\Connection::open($config);
function check(bool $ok,string $code):void{if(!$ok)throw new RuntimeException($code);}
function httpProbe(string $path,string $token='',?array $post=null,?string $range=null):array{
 $url='https://api.celikom.com'.$path;$ch=curl_init($url);$headers=[];
 if($token!=='')$headers[]='Authorization: Bearer '.$token;
 if($post!==null)$headers[]='Content-Type: application/json';
 if($range!==null)$headers[]='Range: '.$range;
 $replyHeaders=[];curl_setopt_array($ch,[CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_CONNECTTIMEOUT=>10,CURLOPT_TIMEOUT=>25,CURLOPT_HTTPHEADER=>$headers,
 CURLOPT_HEADERFUNCTION=>static function($ch,$line)use(&$replyHeaders){$p=explode(':',$line,2);if(count($p)===2)$replyHeaders[strtolower(trim($p[0]))]=trim($p[1]);return strlen($line);}]);
 if($post!==null)curl_setopt_array($ch,[CURLOPT_POST=>true,CURLOPT_POSTFIELDS=>json_encode($post,JSON_FORCE_OBJECT|JSON_THROW_ON_ERROR)]);
 $body=curl_exec($ch);$status=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);check(is_string($body)&&strlen($body)<65536,'http_body');return[$status,$body,$replyHeaders];
}
$session=null;$hash=null;$signed=null;
try{
 $selected=null;
 foreach($pdo->query("SELECT id FROM users WHERE status='active' AND first_activated_at IS NOT NULL AND EXISTS(SELECT 1 FROM account_trials t WHERE t.user_id=users.id) ORDER BY id")->fetchAll(PDO::FETCH_COLUMN)as$id){
  $access=(new Celikom\Entitlement\EntitlementService($pdo,(bool)($config['paid_entitlement_enabled']??false)))->check((int)$id)->json();
  $q=$pdo->prepare('SELECT id FROM user_devices WHERE user_id=? ORDER BY id LIMIT 1');$q->execute([$id]);$device=$q->fetchColumn();
  if($access['allowed']&&$device!==false){$selected=[(int)$id,(int)$device];break;}
 }
 check($selected!==null,'existing_verified_access_required');
 [$userId,$deviceId]=$selected;
 $trialQuery=$pdo->prepare('SELECT * FROM account_trials WHERE user_id=?');$trialQuery->execute([$userId]);$trialBefore=$trialQuery->fetchAll(PDO::FETCH_ASSOC);
 $token=bin2hex(random_bytes(32));$hash=hash('sha256',$token);
 $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at) VALUES(?,?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')->execute([$userId,$deviceId,$hash,hash('sha256',bin2hex(random_bytes(32)))]);
 $session=(int)$pdo->lastInsertId();
 [$status,$body]=httpProbe('/api/v1/auth/me',$token);$me=json_decode($body,true,16,JSON_THROW_ON_ERROR);check($status===200&&(int)($me['user']['id']??0)===$userId,'auth_me');echo "AUTHENTICATED_ME_PASS\n";
 [$status,$body]=httpProbe('/api/v1/entitlement',$token);$entitlement=json_decode($body,true,16,JSON_THROW_ON_ERROR);check($status===200&&($entitlement['allowed']??false)===true,'entitlement');echo "AUTHENTICATED_ENTITLEMENT_PASS\n";
 [$status,$body]=httpProbe('/api/v1/auth/activate',$token,[]);$start=json_decode($body,true,16,JSON_THROW_ON_ERROR);check($status===200&&($start['entitlement']['allowed']??false)===true,'activate');echo "AUTHENTICATED_START_PASS\n";
 $trialQuery->execute([$userId]);check($trialQuery->fetchAll(PDO::FETCH_ASSOC)===$trialBefore,'existing_trial_unchanged');echo "EXISTING_TRIAL_UNCHANGED_PASS\n";
 $track=$pdo->query("SELECT t.service_track_id FROM track_replacements r JOIN tracks t ON t.id=r.track_id JOIN audio_assets a ON a.id=r.audio_asset_id WHERE r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL AND a.mime_type='audio/mpeg' AND a.size_bytes>8192 ORDER BY r.id DESC LIMIT 1")->fetchColumn();check($track!==false,'approved_sample');
 [$status,$body]=httpProbe('/api/v1/resolve?audio_formats=mp3,m4a&service=yandex&track_id='.rawurlencode((string)$track),$token);$result=json_decode($body,true,16,JSON_THROW_ON_ERROR);check($status===200&&($result['found']??false)===true,'resolve');
 $signed=$result['audio_url'];check(is_string($signed)&&str_starts_with($signed,'/api/v1/audio/'),'same_origin_audio');echo "AUTHENTICATED_RESOLVE_SAME_ORIGIN_PASS\n";
 foreach(['bytes=0-1023','bytes=4096-5119']as$range){
  [$status,$body,$headers]=httpProbe($signed,'',null,$range);
  check($status===206&&strlen($body)===1024&&str_starts_with($headers['content-type']??'','audio/')&&isset($headers['content-range']),'range');
 }echo "SIGNED_RANGE_206_SEEK_PASS\n";
}finally{
 if($session!==null)$pdo->prepare('DELETE FROM user_sessions WHERE id=? AND access_hash=?')->execute([$session,$hash]);
}
if($signed!==null){[$status]=httpProbe($signed,'',null,'bytes=0-1023');check(in_array($status,[401,403],true),'expired_probe_denied');echo "REMOVED_PROBE_SESSION_DENIED_PASS\n";}
echo "FLOKI_EXTENSION_AUTH_ACCESS_RANGE_PASS\n";
PHP
