#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Rehearse file recovery from the owner's existing encrypted offsite archive.
# No production restore, database connection, service changes or secret output.
ARCHIVE=/srv/celikom/migration/backups/celikom-offsite-20261122.tar.gpg
KEY=/srv/celikom/migration/secrets/celikom-offsite-20261122.key
[[ -f "$ARCHIVE" && ! -L "$ARCHIVE" ]]
[[ -f "$KEY" && ! -L "$KEY" && $(stat -c '%u' "$KEY") == 0 ]]
[[ $(stat -c '%a' "$KEY") == 600 || $(stat -c '%a' "$KEY") == 400 ]]
test "$(stat -c %s "$ARCHIVE")" = 9733284276
printf '%s  %s\n' 9d94a07d3306acd8874a7d3ad959234427d67a0d1b9c402526abb492e3acff15 "$ARCHIVE" | sha256sum -c -
available=$(df -B1 --output=avail /srv/celikom/migration | tail -1)
(( available >= 22000000000 )) || { echo RECOVERY_FREE_SPACE_TOO_LOW; exit 1; }
work=$(mktemp -d /srv/celikom/migration/offsite-restore-check.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
chmod 700 "$work"
install -d -m 700 "$work/gnupg" "$work/tree"
# Python data filter rejects unsafe symlinks, special files and path escape.
python3 -c 'import tarfile; assert hasattr(tarfile,"data_filter")'
gpg --homedir "$work/gnupg" --batch --no-tty --pinentry-mode loopback --passphrase-file "$KEY" --decrypt "$ARCHIVE" 2>/dev/null | \
  python3 -c 'import sys,tarfile; t=tarfile.open(fileobj=sys.stdin.buffer,mode="r|*"); t.extractall(sys.argv[1],filter="data"); t.close(); sys.stdin.buffer.read()' "$work/tree"
python3 - "$work/tree" <<'PY'
import pathlib,sys,hashlib,gzip,tarfile,stat,os
root=pathlib.Path(sys.argv[1])
imp=root/'srv/celikom/migration/hostinger-import'
orig=pathlib.Path('/srv/celikom/migration/hostinger-import')
assert imp.is_dir() and orig.is_dir()
assert (root/'etc/nginx').is_dir() and (root/'etc/letsencrypt').is_dir()
def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
count=0
audio=0
sql=0
for p in imp.rglob('*'):
    if p.is_symlink() or not p.is_file(): continue
    relative=p.relative_to(imp)
    other=orig/relative
    assert other.is_file() and not other.is_symlink(), 'original snapshot member missing'
    assert p.stat().st_size==other.stat().st_size and digest(p)==digest(other), 'restored snapshot mismatch'
    count+=1
    if p.suffix.lower() in {'.mp3','.m4a','.wav'}: audio+=1
    if p.name.endswith('.sql.gz'):
        with gzip.open(p,'rb') as f:
            while f.read(1024*1024): pass
        sql+=1
    elif p.suffix.lower()=='.sql':
        assert p.stat().st_size>0
        sql+=1
assert audio>=1544 and sql>=1, (audio,sql)
git_archive=root/'srv/celikom/migration/backups/forgejo-baseline-20261122.tar.gz'
assert git_archive.is_file()
with tarfile.open(git_archive,'r|gz') as f:
    git_members=sum(1 for _ in f)
assert git_members>0
print('OFFSITE_RESTORED_IMPORT_FILES',count,'AUDIO',audio,'SQL',sql,'FORGEJO_ARCHIVE_MEMBERS',git_members)
print('CELIKOM_ENCRYPTED_OFFSITE_FILE_RESTORE_OK')
PY
