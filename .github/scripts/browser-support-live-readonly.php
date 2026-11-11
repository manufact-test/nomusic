<?php
declare(strict_types=1);
ini_set('display_errors','0');
try {
 if(PHP_SAPI!=='cli')throw new RuntimeException();
 $root='/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom';
 $release=realpath($root.'/current');
 if(!$release||!str_starts_with($release,$root.'/releases/'))throw new RuntimeException();
 $files=[];
 foreach(['src/Application.php','src/Admin/AdminPanel.php','src/Support/SongReport.php','src/Support/SupportService.php','src/Support/SupportAdminView.php','src/Support/SupportReport.php','src/Support/WindowsSupportDiagnostics.php'] as $path)
  $files[$path]=is_file($release.'/'.$path)?hash_file('sha256',$release.'/'.$path):null;
 echo json_encode(['read_only'=>true,'database_opened'=>false,'release'=>basename($release),'files'=>$files],JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES),"\n";
}catch(Throwable $e){fwrite(STDERR,"Read-only source preflight failed.\n");exit(1);}
