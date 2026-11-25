#!/usr/bin/env python3
"""Promote only owner-accepted, root-verified legacy Android APK to public OTA.

Android A1 is unrelated. Old Hostinger URL stays intact until explicit cutover.
Never touch music/API, runner spools or signing keys.
"""
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
import urllib.request

MIRROR=Path("/home/celikom-mirror/github-mirror.git")
APPROVAL=".github/release/android-customer-stable.json"
OWNER=Path("/srv/celikom-releases/private/android-stable")
PUBLIC=Path("/srv/celikom-releases/public/android-ota-stable")
HEX=re.compile(r"[a-f0-9]{64}\Z")
VERSION=re.compile(r"0\.3\.[0-9]{1,4}\Z")
CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"


def require(cond,code):
    if not cond:raise RuntimeError("ANDROID_PUBLIC_STABLE_"+code)


def read_exact(path,maxsize=16384,uid=0):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_uid==uid and
                not st.st_mode&0o022 and 0<st.st_size<=maxsize,
                "UNSAFE_FILE")
        with os.fdopen(fd,"rb",closefd=False) as f:content=f.read(maxsize+1)
        require(len(content)==st.st_size,"INPUT_CHANGED")
        return content
    finally:os.close(fd)


def sha_bytes(data):return hashlib.sha256(data).hexdigest()


def sha_file(path,limit):
    s=path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022 and
            100000<=s.st_size<=limit,"INVALID_APK")
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    require(path.stat().st_size==s.st_size,"APK_CHANGED")
    return s.st_size,h.hexdigest()


def approved():
    r=subprocess.run(
        ["/usr/bin/git","-c","safe.directory="+str(MIRROR),
         "--git-dir="+str(MIRROR),"show","refs/heads/main:"+APPROVAL],
        check=True,capture_output=True,timeout=30)
    require(len(r.stdout)<4096,"APPROVAL_TOO_LARGE")
    j=json.loads(r.stdout)
    require(type(j) is dict and set(j)=={"schema","channel","approved"} and
            j["schema"]==1 and j["channel"]=="customer-stable","APPROVAL_SCHEMA")
    a=j["approved"]
    if a is None:return None
    require(type(a) is dict and set(a)=={
        "version_code","version_name","sha256","owner_accepted"
    },"APPROVAL_FIELDS")
    require(type(a["version_code"]) is int and 95<=a["version_code"]<2**31 and
            type(a["version_name"]) is str and VERSION.fullmatch(a["version_name"]) and
            type(a["sha256"]) is str and HEX.fullmatch(a["sha256"]) and
            a["owner_accepted"] is True,"NOT_OWNER_ACCEPTED")
    return a


def verify_owned(a):
    v=a["version_code"]
    digest=a["sha256"]
    owner_state=json.loads(read_exact(OWNER/"current-owner.json",4096))
    require(owner_state["channel"]=="owner-only" and
            owner_state["https_verified"] is True and
            owner_state["versionCode"]==v and
            owner_state["versionName"]==a["version_name"] and
            owner_state["sha256"]==digest,"OWNER_RECEIPT_NOT_MATCHING")
    stem=str(v)+"-"+digest
    folder=OWNER/"versions"/stem
    d=folder.lstat()
    require(stat.S_ISDIR(d.st_mode) and d.st_uid==0 and not d.st_mode&0o022,
            "UNSAFE_ROOT_STORE")
    name="CELIKOM-Android-"+a["version_name"]+"-SIGNED.apk"
    apk=folder/name
    size,h=sha_file(apk,200*1024*1024)
    require(h==digest and size==owner_state["sizeBytes"],"APK_SHA256_MISMATCH")
    manifest_bytes=read_exact(folder/"stable.json")
    m=json.loads(manifest_bytes)
    require(m["versionCode"]==v and m["versionName"]==a["version_name"] and
            m["apkSha256"]==digest and m["sizeBytes"]==size and
            m["packageName"]=="pro.celikom.nativeprobe" and
            m["signerSha256"]==CERT and m["enabled"] is True and
            m["channel"]=="stable" and
            m["apkUrl"]=="https://celikom.com/releases/android/"+stem+".apk",
            "MANIFEST_IDENTITY")
    return apk,manifest_bytes,stem,size


def publish_file(src,dst,expected,size):
    if dst.exists() or dst.is_symlink():
        s=dst.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and
                s.st_size==size and not s.st_mode&0o022,
                "IMMUTABLE_PUBLIC_CONFLICT")
        require(sha_file(dst,200*1024*1024)==(size,expected),
                "IMMUTABLE_PUBLIC_DIGEST")
        return
    fd,t=tempfile.mkstemp(prefix=".android-signed-public-",dir=PUBLIC)
    try:
        with os.fdopen(fd,"wb") as out,src.open("rb") as inp:
            shutil.copyfileobj(inp,out,1024*1024)
            out.flush();os.fsync(out.fileno())
        os.chmod(t,0o644);os.chown(t,0,0)
        require(sha_file(Path(t),200*1024*1024)==(size,expected),
                "PUBLIC_COPY_DIGEST")
        os.link(t,dst)
    finally:
        if os.path.lexists(t):os.unlink(t)


def put_manifest(data):
    fd,temp=tempfile.mkstemp(prefix=".android-public-manifest-",dir=PUBLIC)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write(data);out.flush();os.fsync(out.fileno())
        os.chown(temp,0,0);os.chmod(temp,0o644)
        os.replace(temp,PUBLIC/"stable.json")
    finally:
        if os.path.lexists(temp):os.unlink(temp)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def verify_external(stem,expected,size,manifest):
    opener=urllib.request.build_opener(NoRedirect())
    for url,payload in (
        ("https://celikom.com/updates/android/stable.json",manifest),):
        with opener.open(url,timeout=25) as r:
            require(r.status==200 and r.read(16385)==payload,
                    "PUBLIC_OTA_MANIFEST_MISMATCH")
    url="https://celikom.com/releases/android/"+stem+".apk"
    with opener.open(url,timeout=180) as r:
        require(r.status==200,"PUBLIC_OTA_APK_HTTP")
        h=hashlib.sha256();n=0
        while data:=r.read(1024*1024):
            n+=len(data)
            require(n<=size,"PUBLIC_OTA_APK_OVERSIZE")
            h.update(data)
    require(n==size and h.hexdigest()==expected,"PUBLIC_OTA_APK_HASH")
    print("ANDROID_PUBLIC_STABLE_HTTPS_200_FULL_SHA256",stem)


def promote(a):
    # Do not fetch the same signed APK from the public site on every timer tick.
    # Only a newly accepted immutable version needs a full external SHA proof.
    current_path=PUBLIC/"stable.json"
    if current_path.exists():
        existing=json.loads(read_exact(current_path))
        require(existing["versionCode"]<=a["version_code"],"DOWNGRADE_FORBIDDEN")
        if existing["versionCode"]==a["version_code"]:
            require(existing["apkSha256"]==a["sha256"] and
                    existing["versionName"]==a["version_name"],
                    "CURRENT_APPROVAL_CONFLICT")
            receipt=PUBLIC/"accepted.json"
            if receipt.exists():
                verified=json.loads(read_exact(receipt,4096))
                if (verified.get("https_verified") is True and
                    verified.get("versionCode")==a["version_code"] and
                    verified.get("sha256")==a["sha256"]):
                    print("ANDROID_PUBLIC_STABLE_ALREADY_ACCEPTED",a["version_name"])
                    return
    apk,manifest,stem,size=verify_owned(a)
    current=PUBLIC/"stable.json"
    prior=read_exact(current) if current.exists() else None
    if prior:
        old=json.loads(prior)
        require(old["versionCode"]<=a["version_code"],"DOWNGRADE_FORBIDDEN")
        if old["versionCode"]==a["version_code"]:
            require(prior==manifest,"IMMUTABLE_STABLE_MANIFEST_CONFLICT")
    publish_file(apk,PUBLIC/(stem+".apk"),a["sha256"],size)
    put_manifest(manifest)
    try:verify_external(stem,a["sha256"],size,manifest)
    except BaseException:
        if prior is None:
            current.unlink(missing_ok=True)
        else:put_manifest(prior)
        raise
    receipt={"versionCode":a["version_code"],"versionName":a["version_name"],
             "sha256":a["sha256"],"https_verified":True}
    fd,t=tempfile.mkstemp(prefix=".android-accepted-",dir=PUBLIC)
    try:
        with os.fdopen(fd,"wb") as out:
            out.write((json.dumps(receipt,sort_keys=True)+"\n").encode())
            out.flush();os.fsync(out.fileno())
        os.chown(t,0,0);os.chmod(t,0o644)
        os.replace(t,PUBLIC/"accepted.json")
    finally:
        if os.path.lexists(t):os.unlink(t)
    print("ANDROID_PUBLIC_STABLE_OWNER_APPROVED",a["version_name"],a["version_code"])


def main():
    require(os.geteuid()==0,"ROOT_ONLY")
    for path in (OWNER,PUBLIC,MIRROR):
        s=path.lstat()
        require(stat.S_ISDIR(s.st_mode) and not path.is_symlink(),
                "MISSING_TRUSTED_STORE")
    lock=os.open(PUBLIC/".publish.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        a=approved()
        if a is None:
            print("ANDROID_PUBLIC_STABLE_NOT_APPROVED_KEEP_OTA_UNCHANGED")
            return
        promote(a)
    finally:os.close(lock)


if __name__=="__main__":main()
