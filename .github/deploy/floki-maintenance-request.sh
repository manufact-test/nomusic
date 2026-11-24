#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Read-only audit of the exact reconciled CI packages; no database, deployment,
# release activation, permissions changes, or access to private credentials.
python3 - <<'PY'
import hashlib, json, os, pathlib, stat, zipfile
base=pathlib.Path('/srv/celikom/ci-runner/runner/celikom-build-spool/5745e10c3a02917964e6aa433e59b24f4e684f34-45498064520-1')
for p in [base,*base.parents]:
    st=p.lstat()
    assert stat.S_ISDIR(st.st_mode) and not p.is_symlink()
assert base.stat().st_mode & 0o077 == 0
for name,size,sha in [
    ('celikom-server-0.4.57.zip',1136102,'15ad1af4be74a29d0ab182ac966755b4aac60e8995adba68f146d4827900526d'),
    ('celikom-extension-0.4.73.zip',2489436,'968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb'),
]:
    path=base/name
    st=path.lstat()
    assert stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_size == size and st.st_mode & 0o077 == 0
    with path.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        if name.startswith('celikom-server-'):
            modes={'tools/mp3-validator':0o755,'tools/decode-slot-0.lock':0o660,'tools/decode-slot-1.lock':0o660}
            for entry,expected in modes.items():
                info=z.getinfo(entry)
                mode=info.external_attr >> 16
                assert stat.S_ISREG(mode) and stat.S_IMODE(mode)==expected, (entry, oct(mode))
                print(entry,oct(stat.S_IMODE(mode)))
            for entry in ['src/Application/Mp3DecodeValidator.php','src/Application/Mp3Normalizer.php',
                'src/Admin/BulkModerationService.php','src/Admin/BulkModerationView.php','src/Admin/bulk-moderation.js',
                'migrations/021_bulk_moderation_tombstones_reconcile.sql']:
                assert entry in z.namelist(), entry
            assert b'$admissionDeadline' in z.read('src/Application/Mp3DecodeValidator.php')
            assert '.env' not in z.namelist() and not any(n.startswith('tests/') for n in z.namelist())
        else:
            assert json.loads(z.read('api/config.json'))['baseUrl']=='https://api.celikom.com'
    print('VERIFIED',name,size,sha)
print('CELIKOM_RECONCILED_PRIVATE_PACKAGE_AUDIT_OK')
PY
