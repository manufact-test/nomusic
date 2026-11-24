#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Actual decoder check in the same isolated permission model previously
# accepted. Do not make the existing staged application traversable.
decode_work=$(mktemp -d /tmp/celikom-mp3-check.XXXXXXXX)
trap 'rm -rf -- "$decode_work"' EXIT
cat > "$decode_work/test.sh" <<'BASH'
#!/bin/bash
set -Eeuo pipefail
umask 077
work=$1
ZIP=/srv/celikom-releases/private/backend/5745e10c3a02917964e6aa433e59b24f4e684f34/celikom-server-0.4.57.zip
[[ -f "$ZIP" && ! -L "$ZIP" && $(stat -c '%u:%a:%s' "$ZIP") == 0:600:1136102 ]]
printf '%s  %s\n' 15ad1af4be74a29d0ab182ac966755b4aac60e8995adba68f146d4827900526d "$ZIP" | sha256sum -c -
chgrp www-data "$work"
chmod 750 "$work"
install -d -o root -g www-data -m 750 "$work/tools" "$work/src" "$work/src/Application"
python3 - "$ZIP" "$work" <<'PY'
import zipfile,pathlib,sys
root=pathlib.Path(sys.argv[2])
with zipfile.ZipFile(sys.argv[1]) as z:
    for name in ('tools/mp3-validator','src/Application/Mp3Inspector.php','src/Application/Mp3Normalizer.php','src/Application/Mp3DecodeValidator.php'):
        (root/name).write_bytes(z.read(name))
PY
chown root:www-data "$work/tools/mp3-validator" "$work/src/Application/"*.php
chmod 750 "$work/tools/mp3-validator"
chmod 640 "$work/src/Application/"*.php
printf '%s  %s\n' d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939 "$work/tools/mp3-validator" | sha256sum -c -
install -o root -g www-data -m 660 /dev/null "$work/tools/decode-slot-0.lock"
install -o root -g www-data -m 660 /dev/null "$work/tools/decode-slot-1.lock"
printf '%s' 'H4sIAAAAAAAAA/v/2eIIAwMDsweQYPBx9HU11jM0MAjFBvDLEgH+A+2Kh9mFXylV7FowateoXaN2jdo1ateoXaN2jdo1ateoXaN2jdo1ateoXcPLLooBPe0CAFVCqgp0EAAA' | base64 -d | gzip -d > "$work/synthetic.mp3"
chgrp www-data "$work/synthetic.mp3"
chmod 640 "$work/synthetic.mp3"
printf '%s  %s\n' 7237bf4bf7e791bdd272b96a42af8b72a460574e3024967eeefb83cbdcb0d711 "$work/synthetic.mp3" | sha256sum -c -
runuser -u www-data -- test -x "$work/tools/mp3-validator"
runuser -u www-data -- test ! -w "$work/tools"
runuser -u www-data -- test ! -w "$work/tools/mp3-validator"
runuser -u www-data -- test -w "$work/tools/decode-slot-0.lock"
runuser -u www-data -- test -w "$work/tools/decode-slot-1.lock"
runuser -u www-data -- php -r '
require $argv[1]."/src/Application/Mp3Inspector.php";
require $argv[1]."/src/Application/Mp3Normalizer.php";
require $argv[1]."/src/Application/Mp3DecodeValidator.php";
$p=(new Celikom\Application\Mp3Normalizer())->prepare($argv[1]."/synthetic.mp3");
try {
    (new Celikom\Application\Mp3DecodeValidator())->check($p["path"]);
    if ($p["duration_ms"] < 1000 || $p["size"] < 1024) throw new RuntimeException("bad_synthetic_fixture");
    echo "CELIKOM_VPS_ACTUAL_SYNTHETIC_MP3_DECODE_OK duration_ms=",$p["duration_ms"]," size=",$p["size"],PHP_EOL;
} finally { unlink($p["path"]); }
' "$work"
BASH
decoder_status=0
bash "$decode_work/test.sh" "$decode_work" || decoder_status=$?
rm -rf -- "$decode_work"
trap - EXIT
echo "DECODER_REHEARSAL_STATUS=$decoder_status"

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
cat > "$work/safe-restore.py" <<'PY'
import os,sys,tarfile,posixpath,pathlib
root=pathlib.Path(sys.argv[1]).resolve()
rebased=[]
def safe_filter(member,destination):
    # The original Nginx enabled-site links are absolute host paths. Rebase
    # only archived config-tree targets inside the disposable restore root.
    # Keep Python's full data filter for every member; never follow host links.
    if member.issym() and member.linkname.startswith('/'):
        target=posixpath.normpath(member.linkname)
        allowed=('/etc/nginx/','/etc/letsencrypt/')
        if not target.startswith(allowed):
            raise tarfile.AbsoluteLinkError(member)
        name=posixpath.normpath(member.name)
        if name.startswith('/') or not name.startswith(('etc/nginx/','etc/letsencrypt/')):
            raise tarfile.AbsoluteLinkError(member)
        local=posixpath.relpath(target.lstrip('/'),posixpath.dirname(name))
        rebased.append((name,target))
        member=member.replace(linkname=local,deep=False)
    return tarfile.data_filter(member,destination)
with tarfile.open(fileobj=sys.stdin.buffer,mode="r|*") as t:
    t.extractall(root,filter=safe_filter)
while sys.stdin.buffer.read(1024*1024): pass
for name,target in rebased:
    p=root/name
    assert p.is_symlink() and p.resolve()==(root/target.lstrip('/')).resolve()
    assert p.resolve().is_relative_to(root)
    assert p.exists(), 'archived absolute config link has no restored target'
print('OFFSITE_ABSOLUTE_CONFIG_LINKS_SAFELY_REBASED',len(rebased))
PY
gpg --homedir "$work/gnupg" --batch --no-tty --pinentry-mode loopback --passphrase-file "$KEY" --decrypt "$ARCHIVE" 2>/dev/null | \
  python3 "$work/safe-restore.py" "$work/tree"
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

[[ "$decoder_status" == 0 ]]
