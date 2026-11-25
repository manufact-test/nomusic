#!/usr/bin/env python3
"""Stage signed legacy Android stable APK+manifest as isolated CI DATA ONLY.

No production mounts, SSH, release-root writes or elevation. The trusted root
consumer must recheck signer, package, version, manifest, size and digest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import shutil

SPOOL=Path("/home/runner/celikom-build-spool/android-stable")
CERT="67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
PACKAGE="pro.celikom.nativeprobe"
VER=re.compile(r"0\.3\.(?:0|[1-9][0-9]{0,3})\Z")
SHA=re.compile(r"[a-f0-9]{64}\Z")
MAX=200*1024*1024


def need(ok,code):
    if not ok:
        raise RuntimeError("ANDROID_STABLE_SPOOL_"+code)


def signed_hash(path):
    h=hashlib.sha256()
    count=0
    with path.open("rb") as f:
        while data:=f.read(1024*1024):
            count+=len(data)
            need(count<=MAX,"INPUT_TOO_LARGE")
            h.update(data)
    return count,h.hexdigest()


def stage(apk,manifest,proof,spool=SPOOL):
    need(apk.is_file() and not apk.is_symlink(),"APK_INPUT")
    need(manifest.is_file() and not manifest.is_symlink(),"MANIFEST_INPUT")
    need(proof.is_file() and not proof.is_symlink(),"PROOF_INPUT")
    a=json.loads(proof.read_text())
    m=json.loads(manifest.read_text())
    need(type(a) is dict and set(a)=={
        "source_run","source_attempt","version","version_code","apk_sha256",
        "apk_size","apk_name","signer_sha256","package"
    },"PROOF_FIELDS")
    need(type(a["source_run"]) is int and 1<=a["source_run"]<=10**14 and
         type(a["source_attempt"]) is int and 1<=a["source_attempt"]<=100 and
         type(a["version_code"]) is int and a["version_code"]>=95 and
         isinstance(a["version"],str) and VER.fullmatch(a["version"]) and
         a["signer_sha256"]==CERT and a["package"]==PACKAGE,
         "PROOF_IDENTITY")
    need(a["apk_name"]==f'CELIKOM-Android-{a["version"]}-SIGNED.apk'
         and apk.name==a["apk_name"],"APK_NAME")
    size,digest=signed_hash(apk)
    need(size>=100_000 and size==a["apk_size"] and digest==a["apk_sha256"],"APK_HASH")
    need(m.get("schemaVersion")==1 and m.get("enabled") is True and
         m.get("channel")=="stable" and m.get("packageName")==PACKAGE and
         m.get("versionName")==a["version"] and
         m.get("versionCode")==a["version_code"] and
         m.get("signerSha256")==CERT and m.get("apkSha256")==digest and
         m.get("sizeBytes")==size and m.get("minSdk")==28 and
         m.get("apkUrl")==f'https://celikom.com/releases/android/{a["version_code"]}-{digest}.apk',
         "MANIFEST_IDENTITY")
    base=spool.parent
    base_info=base.lstat()
    need(stat.S_ISDIR(base_info.st_mode) and base_info.st_uid==os.getuid() and
         stat.S_IMODE(base_info.st_mode)==0o700,"BASE_SPOOL_MODE")
    spool.mkdir(mode=0o700,exist_ok=True)
    s=spool.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid() and
         stat.S_IMODE(s.st_mode)==0o700,"STABLE_SPOOL_MODE")
    label=f'android-stable-{a["version_code"]}-{digest}'
    destination=spool/label
    if destination.exists() or destination.is_symlink():
        need(destination.is_dir() and not destination.is_symlink(),
             "IMMUTABLE_STAGE_CONFLICT")
        for filename,source in ((apk.name,apk),("stable.json",manifest),("proof.json",proof)):
            need(signed_hash(destination/filename)==signed_hash(source),
                 "IMMUTABLE_STAGE_MISMATCH")
        print("ANDROID_STABLE_SIGNED_DATA_READY",label,"existing")
        return destination
    tmp=Path(tempfile.mkdtemp(prefix=".incoming-",dir=spool))
    try:
        for filename,source in ((apk.name,apk),("stable.json",manifest),("proof.json",proof)):
            dest=tmp/filename
            shutil.copyfile(source,dest)
            dest.chmod(0o600)
            need(signed_hash(dest)==signed_hash(source),"COPY_HASH_MISMATCH")
        os.rename(tmp,destination)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    print("ANDROID_STABLE_SIGNED_DATA_READY",label,"root-verification-pending")
    return destination


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--apk",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--proof",required=True,type=Path)
    a=p.parse_args()
    stage(a.apk,a.manifest,a.proof)
