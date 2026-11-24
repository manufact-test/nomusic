#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# Files only. Keep the already audited CI backend in independent root-private
# staging. No runtime config, database, production vhost or service is changed.
python3 - <<'PY'
import hashlib,os,pathlib,stat,tempfile,json,shutil
commit='5745e10c3a02917964e6aa433e59b24f4e684f34'
sha='15ad1af4be74a29d0ab182ac966755b4aac60e8995adba68f146d4827900526d'
size=1136102
name='celikom-server-0.4.57.zip'
spool=pathlib.Path('/srv/celikom/ci-runner/runner/celikom-build-spool')/(commit+'-45498064520-1')/name
fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
try:
    for part in spool.parts[1:-1]:
        nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
        os.close(fd);fd=nxt
    f=os.open(spool.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
    with os.fdopen(f,'rb') as stream:
        st=os.fstat(stream.fileno())
        assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size==size and not st.st_mode&0o077
        data=stream.read(size+1)
finally:
    os.close(fd)
assert len(data)==size and hashlib.sha256(data).hexdigest()==sha
root=pathlib.Path('/srv/celikom-releases/private')
for p in [root,root.parent,root.parent.parent]:
    st=p.lstat()
    assert stat.S_ISDIR(st.st_mode) and st.st_uid==0 and not st.st_mode&0o022
assert not root.stat().st_mode&0o077
base=root/'backend'
dest=base/commit
for p in (base,dest):
    p.mkdir(mode=0o700,exist_ok=True)
    st=p.lstat()
    assert stat.S_ISDIR(st.st_mode) and st.st_uid==0 and not st.st_mode&0o077
def immutable(p,data):
    if p.exists() or p.is_symlink():
        st=p.lstat()
        assert stat.S_ISREG(st.st_mode) and st.st_uid==0 and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600
        assert p.read_bytes()==data
        return
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.link(tmp,p)
    finally:
        os.unlink(tmp)
immutable(dest/name,data)
immutable(dest/(name+'.sha256'),(sha+'  '+name+'\n').encode())
print('CELIKOM_RECONCILED_BACKEND_ROOT_PRIVATE_STAGED',commit,sha,size)
# Independently compare the existing Android candidate with its known identity.
ad=pathlib.Path('/srv/celikom-releases/public/android')
apk_sha='5ceb9db20d47390e88cd316c3f74c1928534b35bc54e316f5b841f49b951ff6a'
manifest=ad/'stable.json'
apk=ad/('93-'+apk_sha+'.apk')
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
