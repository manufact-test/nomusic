#!/bin/bash
set -Eeuo pipefail
umask 077
systemctl start celikom-mirror-sync.service
if ! systemctl start celikom-extension-owner.service; then
  journalctl -u celikom-extension-owner.service -n 12 --no-pager -o cat
  exit 1
fi
python3 - <<'PY'
import json, pathlib, stat, hashlib, runpy
P=pathlib.Path
a={'version':'0.4.91','source_commit':'e52f819d6c69dc7e96734f60e14a17a92394b84c','run_id':'45876465975','attempt':'1','name':'celikom-extension-0.4.91.zip','size':2501753,'sha256':'018741154c8440e53f21a4f76465bf2be5e37f234897c61f21f46d777ed6c9cb'}
p=P('/srv/celikom-releases/private/extension/current-owner.json')
st=p.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022) and st.st_size<4096
current=json.loads(p.read_text())
expected={'version':a['version'],'sha256':a['sha256'],'size':a['size'],'filename':a['name'],'source_commit':a['source_commit'],'run_id':a['run_id'],'attempt':a['attempt'],'channel':'owner-only','https_verified':True}
assert current==expected, 'TRUSTED_OWNER_RECEIPT_MISMATCH'
for path in [P('/srv/celikom-releases/owner-downloads')/a['name'],P('/srv/celikom-releases/owner-downloads/celikom-extension-latest.zip')]:
 s=path.lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not(s.st_mode&0o022) and s.st_size==a['size']
 assert hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256']
consumer=P('/usr/local/lib/celikom-extension-release/consumer.py')
st=consumer.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022)
trusted=runpy.run_path(str(consumer))
trusted['verify_https'](a)
print('TRUSTED_OWNER_RECEIPT',json.dumps(current,sort_keys=True))
print('OWNER_DOWNLOAD_URL','https://celikom.com/downloads/extension/'+a['name'])
print('OWNER_LATEST_URL','https://celikom.com/downloads/extension/celikom-extension-latest.zip')
print('EXTENSION_0491_PRIVATE_OWNER_DELIVERY_VERIFIED')
PY
