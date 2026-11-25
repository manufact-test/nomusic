#!/usr/bin/env python3
"""Public non-sensitive SHA-256 receipts for CELIKOM release automation.

Never exposes private capability URLs, customer identity, repo hashes, tokens,
file paths or full release metadata. A root-owned release publisher wrote each
source receipt only after verifying the complete download. This summary merely
makes that result visible to ordinary ChatGPT/web/CI readers without SSH.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone

BASE=Path("/srv/celikom-releases")
OUTPUT=BASE/"release-status"/"receipt.json"
WIN_OWNER=BASE/"windows/stable/current"
WIN_CUSTOMER=BASE/"windows/customer-stable/accepted.json"
ANDROID_OWNER=BASE/"private/android-stable/current-owner.json"
ANDROID_CUSTOMER=BASE/"public/android/accepted.json"
EXT_OWNER=BASE/"private/extension/current-owner.json"
HEX=re.compile(r"[a-f0-9]{64}\Z")
VER=re.compile(r"(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,3})\.(?:0|[1-9][0-9]{0,4})\Z")


def require(ok,code):
    if not ok:raise RuntimeError("CELIKOM_RELEASE_RECEIPT_"+code)


def read(path,maxsize=16384):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid==0 and
                not s.st_mode&0o022 and 1<=s.st_size<=maxsize,
                "UNSAFE_RECEIPT_FILE")
        with os.fdopen(fd,"rb",closefd=False) as f:b=f.read(maxsize+1)
        require(len(b)==s.st_size,"RECEIPT_CHANGED")
        return b
    finally:os.close(fd)


def digest(o,field):
    v=o[field]
    require(type(v) is str and HEX.fullmatch(v),"SHA_FORMAT")
    return v


def optional_json(path):
    return json.loads(read(path)) if path.exists() else None


def snapshot():
    # Exactly one current owner version, no arbitrary symlink traversal.
    link=WIN_OWNER.lstat()
    require(stat.S_ISLNK(link.st_mode) and link.st_uid==0,
            "WINDOWS_OWNER_CURRENT")
    target=os.readlink(WIN_OWNER)
    require(target.startswith("versions/") and
            VER.fullmatch(target.removeprefix("versions/")),
            "WINDOWS_OWNER_TARGET")
    win=json.loads(read(WIN_OWNER.parent/target/"manifest.json"))
    require(win["version"]==target.removeprefix("versions/"),
            "WINDOWS_OWNER_VERSION")
    result={"windows_owner_sha256":digest(win,"sha256")}
    customer=optional_json(WIN_CUSTOMER)
    result["windows_customer_sha256"]=(digest(customer,"sha256")
        if customer and customer.get("https_verified") is True else None)
    owner=optional_json(ANDROID_OWNER)
    result["android_owner_sha256"]=(digest(owner,"sha256")
        if owner and owner.get("https_verified") is True else None)
    stable=optional_json(ANDROID_CUSTOMER)
    result["android_customer_sha256"]=(digest(stable,"sha256")
        if stable and stable.get("https_verified") is True else None)
    ext=optional_json(EXT_OWNER)
    result["extension_owner_sha256"]=(digest(ext,"sha256")
        if ext and ext.get("https_verified") is True else None)
    return result


def main():
    require(os.geteuid()==0,"ROOT_REQUIRED")
    base=OUTPUT.parent
    st=base.lstat()
    require(stat.S_ISDIR(st.st_mode) and st.st_uid==0 and
            not st.st_mode&0o022,"UNSAFE_STATUS_DIRECTORY")
    j={"schema":1,"channels":snapshot(),
       "checked_at":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    payload=(json.dumps(j,sort_keys=True,separators=(",",":"))+"\n").encode()
    require(len(payload)<4096,"STATUS_SIZE")
    fd,t=tempfile.mkstemp(prefix=".release-receipt-",dir=base)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(payload);f.flush();os.fsync(f.fileno())
        os.chown(t,0,0);os.chmod(t,0o644)
        os.replace(t,OUTPUT)
    finally:
        if os.path.lexists(t):os.unlink(t)
    print("CELIKOM_SANITIZED_RELEASE_RECEIPTS_READY",
          "channels="+str(sum(v is not None for v in j["channels"].values())))


if __name__=="__main__":main()
