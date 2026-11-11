<?php
declare(strict_types=1);
namespace Celikom\Support;

/** Bounded, allowlisted technical snapshot for Windows user-initiated support. */
final class WindowsSupportDiagnostics
{
 public static function normalize(mixed $input):array {
  if(!is_array($input)||($input['platform']??null)!=='windows')
   throw new \InvalidArgumentException('invalid_request');
  $out=['platform'=>'windows'];
  foreach(['appVersion','nativeModuleVersion','yandexVersion'] as $key){
   $v=$input[$key]??'unknown';
   $out[$key]=is_string($v)&&preg_match('/^(?:unknown|\d{1,4}(?:\.\d{1,4}){1,3})$/D',$v)?$v:'unknown';
  }
  $integration=$input['integration']??'UNKNOWN';
  $out['integration']=is_string($integration)&&preg_match('/^[A-Z][A-Z0-9_]{2,47}$/D',$integration)?$integration:'UNKNOWN';
  foreach(['bridgeStarted','enabled'] as $key)
   $out[$key]=is_bool($input[$key]??null)?$input[$key]:false;
  $matches=$input['nativeMatchesApplication']??null;
  $out['nativeMatchesApplication']=is_bool($matches)?$matches:null;
  $id=$input['lastTrackId']??null;
  $out['lastTrackId']=is_string($id)&&preg_match('/^[1-9][0-9]{0,17}$/D',$id)?$id:null;
  $out['scopeSeconds']=900;
  $out['events']=[];
  foreach(array_slice(is_array($input['events']??null)?$input['events']:[],-64) as $row){
   if(!is_array($row))continue;
   $code=$row['code']??null;$age=$row['ageSeconds']??null;
   if(!is_string($code)||!preg_match('/^[A-Z][A-Z0-9_]{2,47}$/D',$code)||
      !str_contains($code,'_')||!is_int($age)||$age<0||$age>900)continue;
   $event=['code'=>$code,'ageSeconds'=>$age];
   foreach(['trackId','resourceId'] as $field){
    $value=$row[$field]??null;
    if(is_string($value)&&preg_match('/^[1-9][0-9]{0,17}$/D',$value))
     $event[$field]=$value;
   }
   $out['events'][]=$event;
  }
  return $out;
 }
}
