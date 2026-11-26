#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib, os, stat, subprocess, re
P=pathlib.Path
root=P('/srv/celikom/app/staging-20261122')
for rel in ['bootstrap.php','src/Application/UploadService.php','src/Application/Mp3DecodeValidator.php','tools','tools/mp3-validator','tools/decode-slot-0.lock','tools/decode-slot-1.lock']:
 p=root/rel
 if not p.exists():print('UPLOAD_RUNTIME_PATH',rel,'MISSING');continue
 st=p.stat()
 print('UPLOAD_RUNTIME_PATH',rel,'mode',oct(st.st_mode&0o777),'uid',st.st_uid,'gid',st.st_gid,'bytes',st.st_size)
 if rel.startswith('tools'):
  for flag in ['-r','-w','-x']:
   r=subprocess.run(['runuser','-u','www-data','--','test',flag,str(p)],timeout=5)
   print('UPLOAD_RUNTIME_ACCESS',rel,flag,r.returncode==0)
p=root/'src/Application/Mp3DecodeValidator.php'
if p.exists():
 print('DEPLOYED_VALIDATOR_BUSY_WAIT', 'admissionDeadline' in p.read_text())
for p in P('/etc/php').glob('*/fpm/pool.d/*.conf'):
 for line in p.read_text().splitlines():
  if re.match(r'\s*(?:php_admin_value\[)?(?:disable_functions|error_log)\]?',line):print('UPLOAD_FPM_SETTING',line.strip())
r=subprocess.run(['runuser','-u','www-data','--','php','-r','echo "UPLOAD_PROC_OPEN ".(is_callable("proc_open")?"AVAILABLE":"UNAVAILABLE").PHP_EOL;'],capture_output=True,text=True,timeout=10)
print(r.stdout.strip())
print('UPLOAD_RUNTIME_READONLY_AUDIT_DONE')
PY
