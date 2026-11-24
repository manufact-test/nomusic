#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
echo '=== STAGE VERIFIED RELEASES UNDER INDEPENDENT ROOT-OWNED TREE ==='
python3 - <<'PY'
import os, stat, pathlib, hashlib, tempfile, json, zipfile
def safe_dir(path, mode):
    p = pathlib.Path(path)
    if p.parent != p:
        s = p.parent.lstat()
        assert stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022, "unsafe parent"
    p.mkdir(mode=mode, exist_ok=True)
    s = p.lstat()
    assert stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022, "unsafe directory"
    os.chmod(p, mode)
for path,mode in [
    ("/srv/celikom-releases",0o755),
    ("/srv/celikom-releases/windows",0o755),
    ("/srv/celikom-releases/windows/stable",0o755),
    ("/srv/celikom-releases/private",0o700),
    ("/srv/celikom-releases/private/extension",0o700),
]:
    safe_dir(path,mode)
def read_exact(path, size, digest):
    parts = pathlib.PurePosixPath(path).parts
    fd = os.open("/", os.O_DIRECTORY | os.O_RDONLY)
    try:
        for part in parts[1:-1]:
            nxt = os.open(part, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_RDONLY, dir_fd=fd)
            os.close(fd)
            fd = nxt
        f = os.open(parts[-1], os.O_NOFOLLOW | os.O_RDONLY | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(f,"rb") as stream:
            s = os.fstat(stream.fileno())
            assert stat.S_ISREG(s.st_mode) and s.st_size==size
            data = stream.read(size+1)
    finally:
        os.close(fd)
    assert len(data)==size and hashlib.sha256(data).hexdigest()==digest
    return data
name="celikom-extension-0.4.73.zip"
data=read_exact("/srv/celikom/ci-runner/runner/celikom-build-spool/61d17d9eb97f3db5c58c906e30da6c19ee737090-45446268377-1/"+name,2489436,"968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb")
dest=pathlib.Path("/srv/celikom-releases/private/extension")/name
if dest.exists() or dest.is_symlink():
    s=dest.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o077 and s.st_nlink==1
    assert dest.read_bytes()==data
else:
    fd,tmp=tempfile.mkstemp(dir=dest.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.link(tmp,dest)
    finally:
        os.unlink(tmp)
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert json.loads(z.read("api/config.json"))["baseUrl"]=="https://api.celikom.com"
    manifest=json.loads(z.read("manifest.json"))
    assert manifest["version"]=="0.4.73"
    assert set(manifest["host_permissions"])=={"https://api.celikom.com/*","https://music.yandex.ru/*"}
print("FLOKI_EXTENSION_PRIVATE_RELEASE_READY")
PY
cd /root/celikom-release-tools
test "$(git hash-object windows-stable-publish-floki.mjs)" = dcb83ff6d2ac3097e6ca76437f8b1fac51f05a44
test "$(git hash-object windows-stable-release-verify.mjs)" = ae38c2c48a032fec0ad1eaae14c444e43dfb2b18
test "$(git hash-object windows-stable-existing-latest.mjs)" = bb4d19672d45bdd0393497c3b33280308d67ef32
node --input-type=module <<'NODE'
import {lstat,readFile,readlink} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {promoteLocalFeed} from './windows-stable-publish-floki.mjs';
import {verifyPreparedStableRelease} from './windows-stable-release-verify.mjs';
const source='/root/celikom-release-import/windows-02455', root='/srv/celikom-releases/windows/stable', pin='/root/celikom-secrets/windows-stable-public.der';
for(const d of ['/root','/root/celikom-release-import',source,source+'/0.24.55','/root/celikom-secrets','/srv','/srv/celikom-releases','/srv/celikom-releases/windows',root]){
 const s=await lstat(d);
 if(!s.isDirectory()||s.uid!==0||(s.mode&0o022))throw Error('UNSAFE_ANCESTOR:'+d);
}
const ps=await lstat(pin), bytes=await readFile(pin);
if(!ps.isFile()||ps.uid!==0||ps.nlink!==1||(ps.mode&0o077)||createHash('sha256').update(bytes).digest('hex')!=='46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95')throw Error('INVALID_PIN');
const args={source,root,version:'0.24.55',sequence:2,pinnedPublicKeyDerBase64:bytes.toString('base64'),uid:0};
const proof=await verifyPreparedStableRelease(source,{...args,origin:'https://celikom.com'});
let current=null;
try{current=await lstat(root+'/current')}catch(e){if(e.code!=='ENOENT')throw e;}
if(current){
 if(!current.isSymbolicLink()||current.uid!==0||await readlink(root+'/current')!=='versions/0.24.55')throw Error('EXISTING_FEED_CONFLICT');
 for(const name of ['manifest.json','manifest.json.sig','CELIKOM-Windows-0.24.55.exe']){
  const p=root+'/versions/0.24.55/'+name, s=await lstat(p);
  if(!s.isFile()||s.uid!==0||s.nlink!==1||(s.mode&0o022)||!(await readFile(p)).equals(await readFile(source+'/0.24.55/'+name)))throw Error('EXISTING_FEED_CONFLICT');
 }
}else await promoteLocalFeed(args);
console.log('FLOKI_WINDOWS_SIGNED_RELEASE_READY',JSON.stringify(proof));
NODE
echo '=== ANDROID MIGRATED INPUT INVENTORY ==='
python3 - <<'PY'
import pathlib, json, hashlib
root=pathlib.Path("/srv/celikom/migration/sites-20261124/android-private")
base=root/"android-build-inputs/CELIKOM-0.3.22-install.apk"
assert hashlib.file_digest(base.open("rb"),"sha256").hexdigest()=="170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9"
m=json.loads((root/"android-updates/stable.json").read_text())
assert m["packageName"]=="pro.celikom.nativeprobe" and m["channel"]=="stable"
assert m["signerSha256"]=="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
apk=root/"android-updates/releases"/(str(m["versionCode"])+"-"+m["apkSha256"]+".apk")
assert apk.stat().st_size==m["sizeBytes"] and hashlib.file_digest(apk.open("rb"),"sha256").hexdigest()==m["apkSha256"]
print("ANDROID_BASE_HASH_OK")
print("ANDROID_LEGACY_STABLE_HASH_OK",m["versionName"],m["versionCode"],m["sizeBytes"])
PY
if command -v apksigner >/dev/null; then
  echo ANDROID_APKSIGNER_AVAILABLE
else
  echo ANDROID_APKSIGNER_PENDING
fi
echo '=== API STILL CLOSED FOR WRITES ==='
for url in https://api.celikom.com/api/v1/health https://api.celikom.com/admin/login https://celikom.com/; do
  printf '%s ' "$url"; curl --max-time 15 -sS -o /dev/null -w '%{http_code}\n' "$url"
done
echo CELIKOM_PRIVATE_RELEASE_STORAGE_READY
