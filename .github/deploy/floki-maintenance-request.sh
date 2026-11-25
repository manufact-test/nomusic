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
function check(bool $b,string $error):void { if(!$b)throw new RuntimeException($error); }
function getApi(string $route,string $token='', ?string $range=null):array {
 $ch=curl_init('https://api.celikom.com'.$route);$headers=[];if($token!=='')$headers[]='Authorization: Bearer '.$token;if($range!==null)$headers[]='Range: '.$range;
 $responseHeaders=[];
 curl_setopt_array($ch,[CURLOPT_HTTPHEADER=>$headers,CURLOPT_RETURNTRANSFER=>true,CURLOPT_FOLLOWLOCATION=>false,CURLOPT_CONNECTTIMEOUT=>8,CURLOPT_TIMEOUT=>18,CURLOPT_HEADERFUNCTION=>static function($ch,$line)use(&$responseHeaders){$x=explode(':',$line,2);if(count($x)===2)$responseHeaders[strtolower(trim($x[0]))]=trim($x[1]);return strlen($line);}]);
 $body=curl_exec($ch);$status=(int)curl_getinfo($ch,CURLINFO_RESPONSE_CODE);curl_close($ch);
 check(is_string($body)&&strlen($body)<65536,'HTTP_BODY_INVALID');return[$status,$body,$responseHeaders];
}
$checked=0;$eligible=0;$grantOk=0;
foreach ($pdo->query("SELECT id FROM users WHERE status='active' AND first_activated_at IS NOT NULL AND EXISTS(SELECT 1 FROM account_trials t WHERE t.user_id=users.id) ORDER BY id LIMIT 5")->fetchAll(PDO::FETCH_COLUMN) as $id) {
 $allowed=(new Celikom\Entitlement\EntitlementService($pdo,(bool)($config['paid_entitlement_enabled']??false)))->check((int)$id)->json();
 $q=$pdo->prepare('SELECT id FROM user_devices WHERE user_id=? ORDER BY id LIMIT 1');$q->execute([$id]);$device=$q->fetchColumn();
 if(!$allowed['allowed']||$device===false)continue;
 ++$eligible;
 $token=bin2hex(random_bytes(32));$hash=hash('sha256',$token);$session=null;
 try {
  $pdo->prepare('INSERT INTO user_sessions(user_id,device_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at) VALUES(?,?,?,?,UTC_TIMESTAMP()+INTERVAL 5 MINUTE,UTC_TIMESTAMP()+INTERVAL 5 MINUTE)')->execute([(int)$id,(int)$device,$hash,hash('sha256',random_bytes(32))]);$session=(int)$pdo->lastInsertId();
  $uri='/api/v1/resolve?service=yandex&track_id=144530503&audio_formats=mp3,m4a&audio_profile=windows_gain_v1';
  [$code,$body]=getApi($uri,$token);
  check($code===200,'WIN_RESOLVE_HTTP_'.$code);
  $data=json_decode($body,true,16,JSON_THROW_ON_ERROR);
  $found=($data['found']??false)===true;
  $valid=false;$rangeOk=false;$expiresSeconds=0;$gainApplied=$data['gain_applied']??null;
  if($found){
   $raw=$data['audio_url']??'';$expiresSeconds=(int)($data['expires_at']??0);
   $parts=parse_url($raw);parse_str($parts['query']??'',$args);
   $valid=str_starts_with($raw,'/api/v1/audio/')&&preg_match('~^/api/v1/audio/[1-9][0-9]{0,17}$~D',$parts['path']??'')===1
      &&preg_match('/^[a-f0-9]{64}$/D',$args['token']??'')===1
      &&preg_match('/^[0-9]{9,12}$/D',$args['expires']??'')===1
      &&preg_match('/^[1-9][0-9]{0,17}$/D',$args['sid']??'')===1
      &&$expiresSeconds==(int)($args['expires']??0)
      &&$expiresSeconds>time()+5&&$expiresSeconds<=time()+1800
      &&is_int($data['duration_ms']??null)&&$data['duration_ms']>0
      &&in_array($data['mime_type']??'',['audio/mpeg','audio/mp4'],true)
      &&is_bool($gainApplied)
      &&($gainApplied===isset($args['variant']))
      &&(!$gainApplied||($args['variant']==='windows_gain_v1'&&(float)($data['gain_db']??0)!==0.0))
      &&is_numeric($data['gain_db']??null)&&abs((float)$data['gain_db'])<=12.0
      &&count(array_diff(array_keys($args),['token','expires','sid','variant']))===0;
   if($valid){ [$rangeStatus,$bytes,$headers]=getApi($raw,'','bytes=0-1023');$rangeOk=$rangeStatus===206&&strlen($bytes)===1024&&isset($headers['content-range']); }
  }
  echo 'WIN_AU_LIVE_RESOLVE '.json_encode(['tested_user_index'=>$eligible,'http'=>$code,'found'=>$found,'grant_validator_compatible'=>$valid,'signed_range_206'=>$rangeOk,'gain_applied'=>$gainApplied,'mime_type'=>$data['mime_type']??null,'expires_margin_seconds'=>$expiresSeconds?($expiresSeconds-time()):0],JSON_THROW_ON_ERROR)."\n";
  ++$checked;
  if($found && $valid && $rangeOk)++$grantOk;
 }finally{if($session!==null)$pdo->prepare('DELETE FROM user_sessions WHERE id=? AND access_hash=?')->execute([$session,$hash]);}
}
echo 'WIN_AU_LIVE_SUMMARY '.json_encode(['eligible'=>$eligible,'checked'=>$checked,'grants_valid'=>$grantOk],JSON_THROW_ON_ERROR)."\n";
check($eligible>0,'NO_ACTIVE_ELIGIBLE_USER');
echo "WIN_AU_LIVE_AUTH_READONLY_DIAGNOSTIC_DONE\n";
PHP
