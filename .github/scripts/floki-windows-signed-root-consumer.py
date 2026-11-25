#!/usr/bin/env python3
"""Root-owned Floki release consumer. Never execute code from runner spool.

Install only after a separate trusted administrator has reviewed this file.
The runner can only deposit signed ZIP data. All version changes are checked
against the root-pinned P-256 public key and existing monotonic release floor.
"""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request

SPOOL = Path("/srv/celikom/ci-runner/runner/celikom-windows-signed-spool")
IMPORT_ROOT = Path("/root/celikom-release-import")
PIN = Path("/root/celikom-secrets/windows-stable-public.der")
PUBLISH_TOOLS = Path("/root/celikom-release-tools")
ROOT = Path("/srv/celikom-releases/windows/stable")
OWNER = Path("/srv/celikom-releases/owner-downloads")
IMPORTER = Path("/usr/local/lib/celikom-windows-intake/windows-stable-private-import.py")
PIN_HASH = "46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95"
NAME = re.compile(r"windows-((?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4}))-([1-9][0-9]{0,14})-([a-f0-9]{64})\.zip")
MAX_BYTES = 125_100_000
TRUSTED_TOOLS = {
    "windows-stable-publish-floki.mjs":"dcb83ff6d2ac3097e6ca76437f8b1fac51f05a44",
    "windows-stable-release-verify.mjs":"ae38c2c48a032fec0ad1eaae14c444e43dfb2b18",
    "windows-stable-existing-latest.mjs":"bb4d19672d45bdd0393497c3b33280308d67ef32",
}

def check(ok,code):
    if not ok:
        raise RuntimeError("WINDOWS_ROOT_"+code)

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()

def secure_root_file(path):
    s=path.lstat()
    check(stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and not s.st_mode&0o022,
          "UNTRUSTED_ROOT_FILE")
    return s

def git_blob_sha(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def verify_installed_tools():
    check(os.getuid()==0,"ROOT_REQUIRED")
    check(secure_root_file(PIN).st_size==91 and digest(PIN)==PIN_HASH,"PUBLIC_PIN_MISMATCH")
    for name,sha in TRUSTED_TOOLS.items():
        f=PUBLISH_TOOLS/name
        secure_root_file(f)
        check(git_blob_sha(f)==sha,"PUBLISH_TOOL_MISMATCH")
    secure_root_file(IMPORTER)
    check(IMPORTER.parent.resolve()==Path("/usr/local/lib/celikom-windows-intake"),"IMPORTER_PATH_INVALID")

def list_pending():
    st=SPOOL.lstat()
    check(stat.S_ISDIR(st.st_mode) and st.st_uid!=0 and stat.S_IMODE(st.st_mode)==0o700,
          "SPOOL_UNSAFE")
    candidates=[]
    for name in os.listdir(SPOOL):
        if name.startswith(".incoming-"):
            continue # incomplete non-root atomic publish, never follow
        m=NAME.fullmatch(name)
        check(m is not None,"UNEXPECTED_SPOOL_MEMBER")
        path=SPOOL/name
        s=path.lstat()
        check(stat.S_ISREG(s.st_mode) and s.st_uid==st.st_uid and s.st_nlink==1
              and stat.S_IMODE(s.st_mode)==0o600 and 22<=s.st_size<=MAX_BYTES,
              "UNSAFE_SPOOL_FILE")
        version,sequence,sha=m.groups()
        candidates.append((int(sequence),version,sha,path,s.st_ino,s.st_dev,s.st_size))
    check(len(candidates)<=4,"SPOOL_OVER_LIMIT")
    return sorted(candidates)

def snapshot_into_root(path, inode,device,size,expected,temp):
    dest=temp/"transfer.zip"
    srcfd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        current=os.fstat(srcfd)
        check(current.st_ino==inode and current.st_dev==device and current.st_size==size,
              "SPOOL_FILE_REPLACED")
        outfd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        h=hashlib.sha256()
        with os.fdopen(srcfd,"rb") as source,os.fdopen(outfd,"wb") as output:
            count=0
            while chunk:=source.read(1024*1024):
                count+=len(chunk)
                check(count<=MAX_BYTES,"SPOOL_BUNDLE_TOO_LARGE")
                h.update(chunk)
                output.write(chunk)
            output.flush();os.fsync(output.fileno())
        check(count==size and h.hexdigest()==expected,"SIGNED_TRANSFER_DIGEST_MISMATCH")
        now=path.lstat()
        check(now.st_ino==inode and now.st_dev==device and now.st_size==size,
              "SPOOL_MUTATED")
    except BaseException:
        try: os.close(srcfd)
        except OSError: pass
        raise
    return dest

def independently_import(bundle,version,sequence):
    with bundle.open("rb") as inputfile:
        subprocess.run(["/usr/bin/python3",str(IMPORTER),"receive",
          "--dest-root",str(IMPORT_ROOT),"--floor-root",str(ROOT),
          "--pin",str(PIN),"--version",version,"--sequence",str(sequence)],
          stdin=inputfile,check=True,timeout=180)

NODE_PUBLISH = r"""
import {readFile,lstat,readlink} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {promoteLocalFeed} from './windows-stable-publish-floki.mjs';
import {verifyPreparedStableRelease} from './windows-stable-release-verify.mjs';
const version=process.env.WIN_VERSION, sequence=Number(process.env.WIN_SEQUENCE);
const source='/root/celikom-release-import/windows-'+version;
const root='/srv/celikom-releases/windows/stable';
const key='/root/celikom-secrets/windows-stable-public.der';
const bytes=await readFile(key);
if(createHash('sha256').update(bytes).digest('hex')!=='46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95')
 throw Error('PUBLIC_PIN_MISMATCH');
const arg={source,root,version,sequence,pinnedPublicKeyDerBase64:bytes.toString('base64'),uid:0,origin:'https://celikom.com'};
const proof=await verifyPreparedStableRelease(source,arg);
if(proof.version!==version||proof.sequence!==sequence)throw Error('SIGNED_IDENTITY_MISMATCH');
const current=await readlink(root+'/current');
if(current==='versions/'+version){
  const candidate=await readFile(root+'/versions/'+version+'/manifest.json');
  const inroot=await readFile(source+'/'+version+'/manifest.json');
  if(!candidate.equals(inroot))throw Error('CURRENT_IMMUTABLE_CONFLICT');
}else{
  await promoteLocalFeed(arg);
}
console.log('WINDOWS_ROOT_P256_SIGNED_CURRENT_OK',version,sequence,proof.packageSha256);
"""

def publish_signed_root(version,sequence):
    env=dict(os.environ,WIN_VERSION=version,WIN_SEQUENCE=str(sequence))
    subprocess.run(["/usr/bin/node","--input-type=module"],input=NODE_PUBLISH,
                   encoding="utf-8",env=env,cwd=PUBLISH_TOOLS,check=True,timeout=120)
    check(os.readlink(ROOT/"current")=="versions/"+version,"CURRENT_POINTER_MISMATCH")

def owner_copy(version):
    manifest=json.loads((ROOT/"versions"/version/"manifest.json").read_bytes())
    check(manifest["version"]==version,"RELEASE_IDENTITY_INVALID")
    exe="CELIKOM-Windows-"+version+".exe"
    src=ROOT/"versions"/version/exe
    secure_root_file(src)
    check(src.stat().st_size==manifest["packageSize"] and digest(src)==manifest["sha256"],
          "PUBLISHED_EXE_HASH_MISMATCH")
    st=OWNER.lstat()
    check(stat.S_ISDIR(st.st_mode) and st.st_uid==0
          and stat.S_IMODE(st.st_mode)==0o750,"OWNER_DOWNLOAD_DIR_INVALID")
    dest=OWNER/exe
    if dest.exists() or dest.is_symlink():
        ss=dest.lstat()
        check(stat.S_ISREG(ss.st_mode) and ss.st_uid==0 and ss.st_nlink in (1,2)
              and not ss.st_mode&0o022 and
              ss.st_size==src.stat().st_size and digest(dest)==manifest["sha256"],
              "OWNER_IMMUTABLE_CONFLICT")
    else:
        fd,tmp=tempfile.mkstemp(prefix=".windows-owner-",dir=OWNER)
        try:
            with os.fdopen(fd,"wb") as output,src.open("rb") as inputfile:
                shutil.copyfileobj(inputfile,output,length=1024*1024)
                output.flush();os.fsync(output.fileno())
            os.chown(tmp,0,st.st_gid)
            os.chmod(tmp,0o640)
            check(digest(Path(tmp))==manifest["sha256"],"OWNER_COPY_DIGEST_INVALID")
            os.link(tmp,dest)
        finally:
            os.unlink(tmp)
    latest=OWNER/"CELIKOM-Windows-latest.exe"
    if latest.exists() or latest.is_symlink():
        st=latest.lstat()
        check(stat.S_ISREG(st.st_mode) and st.st_uid==0
              and st.st_nlink<=2 and not st.st_mode&0o022,
              "OWNER_LATEST_UNSAFE")
    fd,tmp=tempfile.mkstemp(prefix=".latest-link-",dir=OWNER)
    os.close(fd);os.unlink(tmp)
    try:
        # Atomic hardlink, not symlink: safe even with Nginx disable_symlinks.
        os.link(dest,tmp)
        os.replace(tmp,latest)
    finally:
        if os.path.lexists(tmp):
            os.unlink(tmp)
    print("WINDOWS_ROOT_OWNER_LATEST_READY",version,manifest["sha256"],manifest["packageSize"])

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def read_owner_auth():
    # The protected original owner Basic credentials are consumed in memory
    # exclusively for exact HTTPS download verification. Never log contents.
    file=Path("/root/celikom-secrets/celikom-owner-basic-verification.txt")
    secure_root_file(file)
    values={}
    for line in file.read_text().splitlines():
        m=re.match(r"^\s*(HTTP Basic username|HTTP Basic password)\s*[:=]\s*(.*?)\s*$",line,re.I)
        if m:
            values[m[1].lower()]=m[2]
    check(set(values)=={"http basic username","http basic password"},"OWNER_BASIC_CREDENTIALS_UNAVAILABLE")
    raw=(values["http basic username"]+":"+values["http basic password"]).encode()
    return "Basic "+base64.b64encode(raw).decode("ascii")


def probe_website(version):
    manifest=json.loads((ROOT/"versions"/version/"manifest.json").read_bytes())
    expected=manifest["sha256"]
    expected_size=manifest["packageSize"]
    auth=read_owner_auth()
    opener=urllib.request.build_opener(NoRedirect())
    for path in ("/downloads/windows/CELIKOM-Windows-"+version+".exe",
                 "/downloads/windows/CELIKOM-Windows-latest.exe"):
        url="https://celikom.com"+path
        anonymous=urllib.request.Request(url,
            headers={"User-Agent":"CELIKOM-Windows-Owner-Release-Check"})
        try:
            with opener.open(anonymous,timeout=20) as response:
                raise RuntimeError("WINDOWS_ROOT_OWNER_ROUTE_PUBLIC_"+str(response.status))
        except urllib.error.HTTPError as e:
            check(e.code==401,"OWNER_ROUTE_EXPECTED_PRIVATE_401")
        authorized=urllib.request.Request(url,headers={
            "Authorization":auth,"User-Agent":"CELIKOM-Windows-Owner-Release-Check"})
        with opener.open(authorized,timeout=180) as response:
            check(response.status==200,"OWNER_AUTH_DOWNLOAD_NOT_200")
            h=hashlib.sha256()
            n=0
            while chunk:=response.read(1024*1024):
                n+=len(chunk)
                check(n<=expected_size,"OWNER_DOWNLOAD_TOO_LARGE")
                h.update(chunk)
            check(n==expected_size and h.hexdigest()==expected,
                  "OWNER_DOWNLOAD_HASH_MISMATCH")
        print("WINDOWS_ROOT_PRIVATE_OWNER_DOWNLOAD_FULL_HASH_OK",path,expected_size)

def record_verified_owner(version, sequence):
    # Do not expose a candidate as confirmed until BOTH owner HTTPS downloads
    # have passed exact-size and full SHA256 verification.
    manifest=json.loads((ROOT/"versions"/version/"manifest.json").read_bytes())
    check(manifest["version"]==version and
          manifest["sequence"]==sequence,"OWNER_RECEIPT_IDENTITY")
    payload=(json.dumps({
        "version":version,"sequence":sequence,"sha256":manifest["sha256"],
        "https_verified":True
    },sort_keys=True,separators=(",",":"))+"\n").encode()
    out=ROOT/"owner-verified.json"
    fd,tmp=tempfile.mkstemp(prefix=".windows-owner-verified-",dir=ROOT)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        os.chown(tmp,0,0);os.chmod(tmp,0o644)
        os.replace(tmp,out)
    finally:
        if os.path.lexists(tmp):os.unlink(tmp)


def main():
    verify_installed_tools()
    lockpath=IMPORT_ROOT/".windows-signed-spool.lock"
    fd=os.open(lockpath,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        s=os.fstat(fd);check(s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o600,"UNSAFE_CONSUMER_LOCK")
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for sequence,version,sha,path,ino,dev,size in list_pending():
            with tempfile.TemporaryDirectory(prefix=".signed-windows-",dir=IMPORT_ROOT) as tmp:
                source=snapshot_into_root(path,ino,dev,size,sha,Path(tmp))
                independently_import(source,version,sequence)
                publish_signed_root(version,sequence)
                owner_copy(version)
                probe_website(version)
                record_verified_owner(version,sequence)
                # Never consume an unverified artifact, and never unlink by
                # name before independently confirming inode and dev.
                now=path.lstat()
                check(now.st_ino==ino and now.st_dev==dev,"SPOOL_REPLACED_BEFORE_DELETE")
                path.unlink()
                print("WINDOWS_ROOT_SIGNED_OWNER_PROMOTED",version,sequence,sha)
    finally:
        os.close(fd)

if __name__=="__main__":
    main()
