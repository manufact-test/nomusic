#!/usr/bin/env python3
"""Independently verify and promote signed legacy Android owner candidates.

For old stable Android (package pro.celikom.nativeprobe), NOT experimental A1.
Only data arrives from isolated CI. Root verifies immutable APK/signature and
publishes behind current site owner Basic auth. Customer stable OTA is separate.
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

SPOOL=Path("/srv/celikom/ci-runner/runner/celikom-build-spool/android-stable")
ROOT=Path("/srv/celikom-releases/private/android-stable")
OWNER=Path("/srv/celikom-releases/owner-downloads")
CRED=Path("/root/celikom-secrets/celikom-owner-basic-verification.txt")
CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
PKG="pro.celikom.nativeprobe"
LABEL=re.compile(r"android-stable-([1-9][0-9]{0,8})-([a-f0-9]{64})\Z")
VER=re.compile(r"0\.3\.(?:0|[1-9][0-9]{0,3})\Z")
MAX=200*1024*1024
FIELDS={"schemaVersion","enabled","channel","packageName","versionCode",
        "versionName","signerSha256","apkSha256","sizeBytes","minSdk","apkUrl","notesRu"}


def check(ok,code):
    if not ok:
        raise RuntimeError("ANDROID_STABLE_ROOT_"+code)


def json_no_duplicates(pairs):
    obj={}
    for k,v in pairs:
        check(k not in obj,"DUPLICATE_MANIFEST_KEY")
        obj[k]=v
    return obj


def regular_bytes(path,limit,uid):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        check(stat.S_ISREG(s.st_mode) and s.st_uid==uid and s.st_nlink==1
              and not s.st_mode&0o022 and 1<=s.st_size<=limit,"UNSAFE_FILE")
        with os.fdopen(fd,"rb",closefd=False) as f:
            data=f.read(limit+1)
        check(len(data)==s.st_size,"INPUT_CHANGED")
        return data
    finally:
        os.close(fd)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate(meta,proof,code,digest):
    check(set(proof)=={"source_run","source_attempt","version","version_code",
          "apk_sha256","apk_size","apk_name","signer_sha256","package"},"PROOF_FIELDS")
    check(type(proof["version_code"]) is int and proof["version_code"]==code
          and proof["apk_sha256"]==digest and proof["signer_sha256"]==CERT
          and proof["package"]==PKG and
          isinstance(proof["version"],str) and VER.fullmatch(proof["version"])
          and proof["apk_name"]=="CELIKOM-Android-"+proof["version"]+"-SIGNED.apk"
          and type(proof["apk_size"]) is int and 100_000<=proof["apk_size"]<=MAX
          and type(proof["source_run"]) is int and proof["source_run"]>0
          and type(proof["source_attempt"]) is int and 1<=proof["source_attempt"]<=100,
          "PROOF_INVALID")
    check(set(meta)==FIELDS and meta["schemaVersion"]==1 and meta["enabled"] is True
          and meta["channel"]=="stable" and meta["packageName"]==PKG
          and meta["versionCode"]==code and
          meta["versionName"]==proof["version"] and
          meta["signerSha256"]==CERT and
          meta["apkSha256"]==digest and
          meta["sizeBytes"]==proof["apk_size"] and meta["minSdk"]==28
          and meta["apkUrl"]==
              "https://celikom.com/releases/android/"+str(code)+"-"+digest+".apk",
          "MANIFEST_INVALID")
    check(isinstance(meta["notesRu"],str) and len(meta["notesRu"])<=800
          and "<" not in meta["notesRu"] and ">" not in meta["notesRu"],
          "UNSAFE_RELEASE_NOTES")
    return proof["apk_name"]


def read_apk_snapshot(path,owner,expected_size,expected_sha,tmp):
    source=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    dest=tmp/"signed.apk"
    try:
        st=os.fstat(source)
        check(stat.S_ISREG(st.st_mode) and st.st_uid==owner and st.st_nlink==1
              and stat.S_IMODE(st.st_mode)==0o600 and
              st.st_size==expected_size,"UNSAFE_APK_FILE")
        h=hashlib.sha256()
        count=0
        with os.fdopen(source,"rb") as original,dest.open("xb") as output:
            source=-1
            while part:=original.read(1024*1024):
                count+=len(part)
                check(count<=expected_size,"APK_TOO_LARGE")
                h.update(part)
                output.write(part)
            output.flush()
            os.fsync(output.fileno())
        check(count==expected_size and h.hexdigest()==expected_sha,"APK_HASH")
        return dest
    finally:
        if source>=0:os.close(source)


def verify_signature(apk,proof):
    s=subprocess.run(["/usr/bin/apksigner","verify","--verbose","--print-certs",str(apk)],
                      check=True,capture_output=True,text=True,timeout=100)
    matches=re.findall(r"^Signer #([0-9]+) certificate SHA-256 digest: ([0-9a-f]{64})$",
                       s.stdout,re.MULTILINE)
    check(matches==[("1",CERT)],"WRONG_SIGNING_CERT")
    check(re.search(r"^Verified using v[23] scheme .*: true$",s.stdout,re.MULTILINE),
          "NO_MODERN_SIGNATURE")
    a=subprocess.run(["/usr/bin/aapt","dump","badging",str(apk)],
                     check=True,capture_output=True,text=True,timeout=100)
    identity="package: name='"+PKG+"' versionCode='"+str(proof["version_code"])+ \
             "' versionName='"+proof["version"]+"'"
    check(identity in a.stdout and re.search(r"(?m)^sdkVersion:'(?:[1-9]|1[0-9]|2[0-8])'\s*$",
                                              a.stdout),"PACKAGE_VERSION_OR_SDK")
    print("ANDROID_STABLE_ROOT_ORIGINAL_CERT_PACKAGE_VERSION_VERIFIED")


def immutable_copy(src,dst,sha256,size):
    if dst.exists() or dst.is_symlink():
        st=dst.lstat()
        check(stat.S_ISREG(st.st_mode) and st.st_uid==0
              and st.st_size==size and not st.st_mode&0o022,"IMMUTABLE_CONFLICT")
        with dst.open("rb") as s:
            check(hashlib.file_digest(s,"sha256").hexdigest()==sha256,
                  "IMMUTABLE_HASH")
        return
    fd,t=tempfile.mkstemp(prefix=".legacy-android-",dir=dst.parent)
    try:
        with os.fdopen(fd,"wb") as output,src.open("rb") as inp:
            shutil.copyfileobj(inp,output,1024*1024)
            output.flush()
            os.fsync(output.fileno())
        os.chown(t,0,0)
        os.chmod(t,0o644)
        with open(t,"rb") as chk:
            check(hashlib.file_digest(chk,"sha256").hexdigest()==sha256,
                  "COPY_HASH")
        os.link(t,dst)
    finally:
        if os.path.lexists(t):os.unlink(t)


def replace_state(path,obj):
    data=(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()
    fd,tmp=tempfile.mkstemp(prefix=".android-state-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.chown(tmp,0,0)
        os.chmod(tmp,0o644)
        os.replace(tmp,path)
    finally:
        if os.path.lexists(tmp):os.unlink(tmp)


def latest_link(source,dest):
    fd,temp=tempfile.mkstemp(prefix=".android-latest-",dir=dest.parent)
    os.close(fd)
    os.unlink(temp)
    try:
        os.link(source,temp)
        os.replace(temp,dest)
    finally:
        if os.path.lexists(temp):os.unlink(temp)


def auth_header():
    raw=regular_bytes(CRED,4096,0).decode()
    values={}
    for line in raw.splitlines():
        match=re.fullmatch(r"\s*(HTTP Basic username|HTTP Basic password)\s*[:=]\s*(.*?)\s*",
                           line,re.I)
        if match:values[match[1].lower()]=match[2]
    check(set(values)=={"http basic username","http basic password"},
          "OWNER_CREDENTIALS_UNAVAILABLE")
    return "Basic "+base64.b64encode(
        (values["http basic username"]+":"+values["http basic password"]).encode()
    ).decode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def verify_owner(version,sha256,size):
    opener=urllib.request.build_opener(NoRedirect())
    for name in ("CELIKOM-Android-"+version+"-SIGNED.apk","CELIKOM-Android-latest.apk"):
        url="https://celikom.com/downloads/android/"+name
        try:
            with opener.open(url,timeout=25):
                check(False,"PRIVATE_ROUTE_WAS_PUBLIC")
        except urllib.error.HTTPError as e:
            check(e.code==401,"OWNER_ROUTE_NOT_401")
        req=urllib.request.Request(url,headers={"Authorization":auth_header(),
             "User-Agent":"CELIKOM-Android-Owner-Private-Verification"})
        with opener.open(req,timeout=180) as response:
            check(response.status==200,"OWNER_HTTPS_NOT_200")
            h=hashlib.sha256()
            n=0
            while chunk:=response.read(1024*1024):
                n+=len(chunk)
                check(n<=size,"OWNER_APK_TOO_LARGE")
                h.update(chunk)
        check(n==size and h.hexdigest()==sha256,"OWNER_HTTPS_SHA256_MISMATCH")
    print("ANDROID_STABLE_ROOT_OWNER_HTTPS_FULL_SHA_VERIFIED",version,sha256)


def promote(dirpath,runner_uid,code,digest):
    entry=dirpath.lstat()
    check(stat.S_ISDIR(entry.st_mode) and entry.st_uid==runner_uid
          and stat.S_IMODE(entry.st_mode)==0o700,"UNSAFE_STAGED_DIRECTORY")
    proof=json.loads(regular_bytes(dirpath/"proof.json",4096,runner_uid),
                     object_pairs_hook=json_no_duplicates)
    manifest_bytes=regular_bytes(dirpath/"stable.json",16384,runner_uid)
    manifest=json.loads(manifest_bytes,object_pairs_hook=json_no_duplicates)
    name=validate(manifest,proof,code,digest)
    apk=dirpath/name
    existing=ROOT/"current-owner.json"
    previous=json.loads(regular_bytes(existing,4096,0)) if existing.exists() else None
    if previous:
        check(code>=previous["versionCode"],"DOWNGRADE_REFUSED")
        if code==previous["versionCode"]:
            check(digest==previous["sha256"],"SAME_CODE_CHANGED")
            return
    with tempfile.TemporaryDirectory(prefix=".android-intake-",dir=ROOT) as td:
        tmp=Path(td)
        snapshot=read_apk_snapshot(apk,runner_uid,proof["apk_size"],digest,tmp)
        verify_signature(snapshot,proof)
        destdir=ROOT/"versions"/(str(code)+"-"+digest)
        destdir.mkdir(mode=0o750,exist_ok=True)
        private=destdir/name
        immutable_copy(snapshot,private,digest,proof["apk_size"])
        mpath=destdir/"stable.json"
        if mpath.exists():
            check(regular_bytes(mpath,16384,0)==manifest_bytes,"MANIFEST_IMMUTABLE_CONFLICT")
        else:
            fd,staged=tempfile.mkstemp(prefix=".stable-manifest-",dir=destdir)
            try:
                with os.fdopen(fd,"wb") as f:
                    f.write(manifest_bytes);f.flush();os.fsync(f.fileno())
                os.chown(staged,0,0);os.chmod(staged,0o644)
                os.link(staged,mpath)
            finally:
                if os.path.lexists(staged):os.unlink(staged)
        owner_file=OWNER/name
        immutable_copy(private,owner_file,digest,proof["apk_size"])
        latest=OWNER/"CELIKOM-Android-latest.apk"
        latest_link(owner_file,latest)
        try:
            verify_owner(proof["version"],digest,proof["apk_size"])
        except BaseException:
            if previous:
                older=OWNER/("CELIKOM-Android-"+previous["versionName"]+"-SIGNED.apk")
                latest_link(older,latest)
            else:
                latest.unlink(missing_ok=True)
            raise
        replace_state(existing,{"versionCode":code,"versionName":proof["version"],
                                "sha256":digest,"sizeBytes":proof["apk_size"],
                                "file":name,"https_verified":True,
                                "channel":"owner-only"})
        print("ANDROID_STABLE_ROOT_OWNER_SIGNED_CANDIDATE_READY",proof["version"],code)


def main():
    check(os.geteuid()==0,"ROOT_REQUIRED")
    spool_st=SPOOL.lstat()
    check(stat.S_ISDIR(spool_st.st_mode) and spool_st.st_uid!=0
          and stat.S_IMODE(spool_st.st_mode)==0o700,"UNTRUSTED_SPOOL")
    for d in (ROOT,ROOT/"versions",OWNER):
        st=d.lstat()
        check(stat.S_ISDIR(st.st_mode) and st.st_uid==0
              and not st.st_mode&0o022,"UNSAFE_STORE")
    fd=os.open(ROOT/".android-stable.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        candidates=[]
        for d in SPOOL.iterdir():
            if d.name.startswith(".incoming-") or d.name=="receipts":
                continue
            m=LABEL.fullmatch(d.name)
            check(m,"UNKNOWN_SPOOL_ENTRY")
            candidates.append((int(m[1]),m[2],d))
        check(len(candidates)<=12,"TOO_MANY_PENDING")
        for code,digest,directory in sorted(candidates):
            promote(directory,spool_st.st_uid,code,digest)
            # Keep immutable receipts in root store, not CI-writable release authority.
            # Original spool data may be retained for incident review; never execute it.
    finally:
        os.close(fd)


if __name__=="__main__":
    main()
