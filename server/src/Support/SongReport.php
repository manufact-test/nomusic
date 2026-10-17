<?php
declare(strict_types=1);
namespace Celikom\Support;

/** Whitelist-only report: never persist URLs, credentials, logs or arbitrary keys. */
final class SongReport
{
 public const CATEGORIES=['not_replacing'=>'Не включается версия CELIKOM','wrong_version'=>'Играет неправильная версия','audio_issue'=>'Звук обрывается или рассинхронизируется','other'=>'Другая проблема'];
 private static function text(mixed $v,int $limit=96):string {
  if(!is_string($v)||strlen($v)>$limit||!preg_match('//u',$v)||preg_match('/[\x00-\x1F]/',$v))throw new \InvalidArgumentException('invalid_request');
  return trim($v);
 }
 public static function normalize(mixed $input):array {
  if(!is_array($input)||!is_string($input['category']??null)||!isset(self::CATEGORIES[$input['category']]))throw new \InvalidArgumentException('invalid_request');
  $track=$input['track']??null;
  if(!is_array($track)||!is_string($track['id']??null)||!preg_match('/^[1-9]\d{0,23}$/D',$track['id']))throw new \InvalidArgumentException('invalid_request');
  $out=['category'=>$input['category'],'track'=>['id'=>$track['id']]];
  foreach(['title','artist','album'] as $k)$out['track'][$k]=self::text($track[$k]??'',512);
  $version=self::text($input['version']??'',32);
  if(!preg_match('/^\d{1,4}\.\d{1,4}\.\d{1,4}$/D',$version))throw new \InvalidArgumentException('invalid_request');
  $out['version']=$version;
  $d=$input['diagnostics']??[];if(!is_array($d))throw new \InvalidArgumentException('invalid_request');
  $safe=[];
  foreach(['phase','replacementError','connectionError','restoreReason'] as $k){
   $v=$d[$k]??null;
   if($v!==null){$v=self::text($v);if(!preg_match('/^[a-zA-Z0-9_:.-]{1,96}$/D',$v))throw new \InvalidArgumentException('invalid_request');$safe[$k]=$v;}
  }
  foreach(['enabled','suspended','recovering','bridgeReady','bridgeHealthy','controllerPresent','paused'] as $k)if(isset($d[$k])&&is_bool($d[$k]))$safe[$k]=$d[$k];
  foreach(['activationCount','restoreCount','currentTime','duration','durationMs','readyState'] as $k){$v=$d[$k]??null;if((is_int($v)||is_float($v))&&is_finite((float)$v)&&$v>=0&&$v<=1e9)$safe[$k]=$v;}
  $safe['network']=[];
  foreach(array_slice(is_array($d['network']??null)?$d['network']:[], -12) as $row){
   if(!is_array($row)||!in_array($row['endpoint']??null,['config','auth/me','entitlement','tracks/version-status','resolve','rewards'],true))continue;
   $status=$row['httpStatus']??null;$elapsed=$row['elapsedMs']??null;
   $result=self::text($row['result']??'',64);if(!preg_match('/^[a-z_]{1,64}$/D',$result))continue;
   $safe['network'][]=['endpoint'=>$row['endpoint'],'httpStatus'=>is_int($status)&&$status>=100&&$status<=599?$status:null,'result'=>$result,'elapsedMs'=>is_numeric($elapsed)&&$elapsed>=0&&$elapsed<=300000?(int)$elapsed:null];
  }
  $out['diagnostics']=$safe;return $out;
 }
}
