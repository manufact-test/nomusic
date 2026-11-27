#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib,stat,json,hashlib,runpy
P=pathlib.Path
a=json.loads("{\"version\":\"0.4.92\",\"source_commit\":\"4e6ff1aeb8b8ad97c66ebf66ad66b6181bef4885\",\"run_id\":\"45978089929\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.92.zip\",\"size\":2502122,\"sha256\":\"8c7cb39ec1564ad3f063bcfd8d9c0d361fc4bbea092057598d22d68877cece0b\"}")
receipt=P('/srv/celikom-releases/private/extension/current-owner.json')
st=receipt.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022) and st.st_size<4096
current=json.loads(receipt.read_text())
expected={'version':a['version'],'sha256':a['sha256'],'size':a['size'],'filename':a['name'],'source_commit':a['source_commit'],'run_id':a['run_id'],'attempt':a['attempt'],'channel':'owner-only','https_verified':True}
assert current==expected, 'TRUSTED_OWNER_RECEIPT_MISMATCH'
for name in [a['name'],'celikom-extension-latest.zip']:
 p=P('/srv/celikom-releases/owner-downloads')/name
 st=p.lstat()
 assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022)
 assert st.st_size==a['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
consumer=P('/usr/local/lib/celikom-extension-release/consumer.py')
st=consumer.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022)
trusted=runpy.run_path(str(consumer))
trusted['verify_https'](a)
print('TRUSTED_OWNER_RECEIPT',json.dumps(current,sort_keys=True))
print('OWNER_DOWNLOAD_URL','https://celikom.com/downloads/extension/'+a['name'])
print('EXTENSION_0492_OWNER_DELIVERY_VERIFIED')
PY
