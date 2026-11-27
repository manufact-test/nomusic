#!/bin/bash
set -Eeuo pipefail
umask 077
python3 - <<'PY'
import pathlib,stat,json,runpy,time
P=pathlib.Path
a=json.loads("{\"version\":\"0.4.92\",\"source_commit\":\"4e6ff1aeb8b8ad97c66ebf66ad66b6181bef4885\",\"run_id\":\"45978089929\",\"attempt\":\"1\",\"name\":\"celikom-extension-0.4.92.zip\",\"size\":2502122,\"sha256\":\"8c7cb39ec1564ad3f063bcfd8d9c0d361fc4bbea092057598d22d68877cece0b\"}")
receipt=P('/srv/celikom/ci-runner/runner/celikom-build-spool')/(a['source_commit']+'-'+a['run_id']+'-'+a['attempt'])/'receipt.json'
deadline=time.monotonic()+45
while not receipt.exists() and time.monotonic()<deadline:time.sleep(1)
assert receipt.exists(), 'VERIFIED_CANDIDATE_SPOOL_NOT_READY'
consumer=P('/usr/local/lib/celikom-extension-release/consumer.py')
st=consumer.lstat()
assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not(st.st_mode&0o022)
trusted=runpy.run_path(str(consumer))
data=trusted['verify_spool'](a)
assert len(data)==a['size']
print('EXTENSION_0492_SPOOL_INDEPENDENTLY_VERIFIED',json.dumps(a,sort_keys=True))
PY
