#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib, os, stat, hashlib, subprocess, json
P=pathlib.Path
root=P('/srv/celikom/app/staging-20261122/tools')
binary=root/'mp3-validator'
for p in [root,*root.parents]:
 st=p.lstat()
 assert not stat.S_ISLNK(st.st_mode), 'RUNTIME_SYMLINK_REFUSED'
st=binary.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==1000 and st.st_gid==33
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939', 'DECODER_BINARY_IDENTITY_MISMATCH'
paths=[binary,root/'decode-slot-0.lock',root/'decode-slot-1.lock']
before={}
created=[]
for p in paths:
 if p.exists():
  s=p.lstat()
  assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==1000 and s.st_gid==33
  if p!=binary:assert s.st_size==0
  before[str(p)]=stat.S_IMODE(s.st_mode)
 else:
  assert p.name=='decode-slot-1.lock', 'UNEXPECTED_MISSING_RUNTIME_FILE'
try:
 os.chmod(binary,0o750)
 for p in paths[1:]:
  if not p.exists():
   fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o660)
   os.fchown(fd,1000,33);os.fchmod(fd,0o660);os.close(fd);created.append(p)
  else:os.chmod(p,0o660)
 probe=r'''<?php
declare(strict_types=1);
ini_set('display_errors','0');
require '/srv/celikom/app/staging-20261122/bootstrap.php';
$c=require '/srv/celikom/app/staging-20261122/config/app.php';
$p=Celikom\Database\Connection::open($c);
$p->exec('SET TRANSACTION READ ONLY');$p->beginTransaction();
try{
 $q=$p->prepare("SELECT a.storage_key FROM tracks t JOIN track_replacements r ON r.track_id=t.id JOIN audio_assets a ON a.id=r.audio_asset_id WHERE t.service='yandex' AND t.service_track_id=? AND r.status='approved' AND r.is_active=1 AND r.disabled_at IS NULL AND a.mime_type='audio/mpeg' LIMIT 1");
 $q->execute(['144530503']);$key=$q->fetchColumn();
 if(!is_string($key))throw new RuntimeException('sample_unavailable');
 $base=realpath($c['storage_path']);$path=realpath($base.'/'.$key);
 if(!$base||!$path||!str_starts_with($path,$base.'/'))throw new RuntimeException('sample_path_invalid');
 $prepared=(new Celikom\Application\Mp3Normalizer())->prepare($path);
 try{(new Celikom\Application\Mp3DecodeValidator())->check($prepared['path']);}
 finally{if(is_file($prepared['path']))unlink($prepared['path']);}
 echo "UPLOAD_NORMALIZER_AND_DECODER_AS_WWW_DATA_PASS\n";
}finally{if($p->inTransaction())$p->rollBack();}
'''
 result=subprocess.run(['runuser','-u','www-data','--','php'],input=probe,text=True,capture_output=True,timeout=30)
 if result.returncode:
  # Do not print PHP exception text: credentials and database details remain private.
  print('UPLOAD_RUNTIME_PROBE_FAILED',result.returncode)
  raise RuntimeError('UPLOAD_RUNTIME_PROBE_FAILED')
 print(result.stdout.strip())
 assert hashlib.sha256(binary.read_bytes()).hexdigest()=='d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939'
 for p in paths:print('UPLOAD_RUNTIME_REPAIRED',p.name,oct(p.stat().st_mode&0o777))
 print('UPLOAD_RUNTIME_PERMISSION_REPAIR_VERIFIED')
except BaseException:
 for p,mode in before.items():os.chmod(p,mode)
 for p in created:p.unlink()
 print('UPLOAD_RUNTIME_PERMISSION_REPAIR_ROLLED_BACK')
 raise
PY
