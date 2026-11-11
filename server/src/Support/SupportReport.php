<?php
declare(strict_types=1);
namespace Celikom\Support;

/** Optional diagnostic attachment for ordinary support; same narrow song whitelist. */
final class SupportReport
{
 public static function normalize(array $input):array {
  if(($input['schema_version']??null)!==1 || !in_array($input['platform']??null,['chromium','android'],true)
   || !is_string($input['version']??null) || !preg_match('/^\d{1,4}\.\d{1,4}\.\d{1,4}$/D',$input['version']))
   throw new \InvalidArgumentException('invalid_request');
  $out=['schema_version'=>1,'platform'=>$input['platform'],'version'=>$input['version'],
   'diagnostics'=>SongReport::diagnostics($input['diagnostics']??[])];
  if(isset($input['track'])) {
   try {
    $song=SongReport::normalize(['category'=>'other','version'=>$input['version'],'track'=>$input['track']]);
    $out['track']=$song['track'];
   } catch (\InvalidArgumentException) { /* Optional uncertain metadata must not prevent support. */ }
  }
  return $out;
 }
}
