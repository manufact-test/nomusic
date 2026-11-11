<?php
declare(strict_types=1);
// Patch a fresh immutable clone only. Never write through current.
ini_set('display_errors','0');
function supportPatch(bool $ok,string $code):void {if(!$ok)throw new RuntimeException($code);}
try {
 supportPatch(PHP_SAPI==='cli'&&$argc===4,'arguments');
 [$self,$candidate,$payload,$manifestPath]=$argv;
 $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
 $real=realpath($candidate);$input=realpath($payload);
 $fixture=getenv('APP_ENV')==='test'&&is_string($real)&&str_starts_with($real,sys_get_temp_dir().'/celikom-support-patch-test-');
 supportPatch(is_string($real)&&is_string($input)&&!is_link($candidate),'candidate');
 supportPatch($fixture||(preg_match('~^'.preg_quote($root,'~').'/releases/browser-support-076-[a-f0-9]{12}$~D',$real)===1
  &&$real!==realpath($root.'/current')),'candidate_not_isolated');
 $manifest=json_decode((string)file_get_contents($manifestPath),true,32,JSON_THROW_ON_ERROR);
 $allowed=['src/Application.php','src/Admin/AdminPanel.php','src/Support/SongReport.php','src/Support/SupportService.php',
  'src/Support/SupportAdminView.php','src/Support/SupportReport.php','src/Support/WindowsSupportDiagnostics.php'];
 supportPatch(array_keys($manifest['files']??[])===$allowed,'manifest_paths');
 $changes=[];
 foreach($manifest['files'] as $name=>$entry){
  $path=$real.'/'.$name;$source=$input.'/'.$name;
  supportPatch(!is_link($path)&&!is_link($source),'source_link');
  $exists=is_file($path);$original=$exists?file_get_contents($path):null;
  supportPatch(($entry['before']===null&&!file_exists($path))||($exists&&hash_equals($entry['before'],hash('sha256',$original))),'live_source_changed');
  if(isset($entry['replace'])){
   supportPatch(is_string($original),'missing_patch_source');$next=$original;
   foreach($entry['replace'] as $pair){
    supportPatch(is_string($pair['old'])&&$pair['old']!==''&&substr_count($next,$pair['old'])===1,'patch_anchor');
    $next=str_replace($pair['old'],$pair['new'],$next);
   }
   $reverse=$next;
   foreach(array_reverse($entry['replace']) as $pair){
    supportPatch(substr_count($reverse,$pair['new'])===1,'reverse_anchor');
    $reverse=str_replace($pair['new'],$pair['old'],$reverse);
   }
   supportPatch(hash_equals(hash('sha256',$original),hash('sha256',$reverse)),'unrelated_source_changed');
  }else{
   supportPatch(is_file($source),'missing_payload');$next=file_get_contents($source);
   supportPatch(hash_equals($entry['after'],hash('sha256',$next)),'payload_changed');
  }
  $changes[$path]=[$next,$exists?(fileperms($path)&0777):0644];
 }
 // Validate every input before the first write, and keep the clone private until activation.
 foreach($changes as $path=>[$next,$mode]){
  if(!is_dir(dirname($path)))mkdir(dirname($path),0755,true);
  supportPatch(file_put_contents($path,$next,LOCK_EX)===strlen($next)&&chmod($path,$mode),'candidate_write');
 }
 echo "SUPPORT_CANDIDATE_PATCH_PASS\n";
}catch(Throwable $error){
 $code=$error instanceof RuntimeException&&preg_match('/^[a-z_]{1,64}$/D',$error->getMessage())?$error->getMessage():'unexpected';
 fwrite(STDERR,'SUPPORT_PATCH_FAILED:'.$code."\n");exit(1);
}
