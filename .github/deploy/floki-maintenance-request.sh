#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
python3 - <<'PY'
import hashlib, pathlib, stat, json
# Independently compare the existing Android candidate with its known identity.
ad=pathlib.Path('/srv/celikom-releases/public/android')
apk_sha='5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a'
manifest=ad/'updates/android/stable.json'
apk=ad/'releases'/('93-'+apk_sha+'.apk')
for p in (manifest,apk):
    st=p.lstat()
    assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and not st.st_mode&0o022
assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='d61f4476f9e008b37d141e56f82f98867f634285dad15d24c646ff6959bcc03e'
m=json.loads(manifest.read_bytes())
assert m['versionCode']==93 and m['versionName']=='0.3.92' and m['packageName']=='pro.celikom.nativeprobe'
assert m['signerSha256']=='67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f'
assert m['apkSha256']==apk_sha and m['apkUrl']=='https://celikom.com/releases/android/93-'+apk_sha+'.apk'
assert apk.stat().st_size==m['sizeBytes']==8845385
with apk.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==apk_sha
print('CELIKOM_ANDROID_LEGACY_PRIVATE_CANDIDATE_BYTES_MATCH')
PY
# Real decode of a newly synthesized 1.3-second silent MP3 on the actual
# VPS under www-data. No system encoder or changes to the staged application.
BIN=/srv/celikom/app/staging-20261122/tools/mp3-validator
test -f "$BIN" && test ! -L "$BIN"
printf '%s  %s\n' d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939 "$BIN" | sha256sum -c -
work=$(mktemp -d /tmp/celikom-synthetic-decode.XXXXXXXX)
trap 'rm -rf -- "$work"' EXIT
chown root:www-data "$work"
chmod 0750 "$work"
printf '%s' 'H4sIAAAAAAAAA/v/2eIIAwMDsweQYPBx9HU11jM0MAjFBvDLEgH+A+2Kh9mFXylV7FowateoXaN2jdo1ateoXaN2jdo1ateoXaN2jdo1ateoXcPLLooBPe0CAFVCqgp0EAAA' | base64 -d | gzip -d > "$work/synthetic.mp3"
chown root:www-data "$work/synthetic.mp3"
chmod 0640 "$work/synthetic.mp3"
printf '%s  %s\n' 7237bf4bf7e791bdd272b96a42af8b72a460574e3024967eeefb83cbdcb0d711 "$work/synthetic.mp3" | sha256sum -c -
runuser -u www-data -- timeout 20 "$BIN" -nostdin -hide_banner -v error -xerror -err_detect explode -threads 1 -protocol_whitelist file -f mp3 -i "$work/synthetic.mp3" -map 0:a:0 -threads 1 -f null - 2>"$work/errors"
test ! -s "$work/errors"
echo CELIKOM_VPS_ACTUAL_SYNTHETIC_MP3_DECODE_OK

# Remove the disposable decoder fixture before the separate recovery rehearsal.
rm -rf -- "$work"
trap - EXIT

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
