#!/usr/bin/env python3
"""Read-only *optional* official-signer crosscheck of #170gpr mirrored at Aptoide.

No installation, APK repack, user credentials, proprietary artifact upload or
Play Protect bypass. Mirror metadata is untrusted until official pinned APK
signature and target package/version are independently checked.
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys, tempfile, urllib.parse, urllib.request, zipfile
from pathlib import Path
from audit_rustore_host_once import sdk_tool, scan, RUSTORE_SHA256_CERT

PKG="ru.yandex.music"
VERSION="2026.10.3 #170gpr"
CODE=24026531
MAX=150*1024*1024
META="https://ws75.aptoide.com/api/7/app/get/package_name=ru.yandex.music"
ALLOWED=("aptoide.com","aptoide.net","aptoidecdn.com")

def guarded(url):
    p=urllib.parse.urlsplit(url)
    h=(p.hostname or "").lower()
    if p.scheme!="https" or not h or p.username or p.password or p.port not in (None,443):
        raise ValueError("Invalid mirror URL")
    if not any(h==s or h.endswith("."+s) for s in ALLOWED):
        raise ValueError("Unexpected APK mirror hostname: "+h)
    return url

class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        guarded(url)
        return super().redirect_request(req,fp,code,msg,headers,url)
OPENER=urllib.request.build_opener(StrictRedirect())

def metadata():
    with OPENER.open(urllib.request.Request(META,headers={
            "Accept":"application/json","User-Agent":"CELIKOM-static-research/1.0"}),timeout=30) as r:
        if r.status!=200:raise ValueError("Mirror metadata HTTP "+str(r.status))
        blob=r.read(1024*1024+1)
    if len(blob)>1024*1024:raise ValueError("Too large mirror metadata")
    data=json.loads(blob)
    if (data.get("info") or {}).get("status") != "OK":
        raise ValueError("Mirror metadata non-OK")
    d=(((data.get("nodes") or {}).get("meta") or {}).get("data") or {})
    if d.get("package")!=PKG:raise ValueError("Mirror package differs")
    f=d.get("file") or {}
    version=f.get("vername");code=f.get("vercode")
    # Never assume mirror timestamps or names establish byte provenance.
    print("MIRROR_METADATA: package="+PKG+" version="+str(version)[:80]+
          " code="+str(code)[:20])
    if version!=VERSION or code!=CODE:
        # Public version-pin endpoint is distinct from unpinned /app/get.
        # It must identify the exact version independently; never fall back to an older APK.
        api = "https://ws2.aptoide.com/api/7/app/getMeta/package_name=" + PKG + "/vercode=" + str(CODE)
        with OPENER.open(urllib.request.Request(guarded(api),headers={
                "Accept":"application/json","User-Agent":"CELIKOM-static-research/1.0"}),timeout=30) as r:
            if r.status!=200:raise ValueError("Version-pinned mirror HTTP "+str(r.status))
            payload=r.read(1024*1024+1)
        if len(payload)>1024*1024:raise ValueError("Version metadata too large")
        pin=json.loads(payload)
        if (pin.get("info") or {}).get("status")!="OK":
            raise ValueError("Mirror version-specific endpoint not available")
        d=pin.get("data") or {}
        f=d.get("file") or {}
        version,code=f.get("vername"),f.get("vercode")
        print("MIRROR_PINNED_METADATA: package="+str(d.get("package"))+
              " version="+str(version)[:80]+" code="+str(code)[:20])
        if d.get("package")!=PKG or version!=VERSION or code!=CODE:
            raise ValueError("Exact #170gpr not present in public version-specific mirror API")
    url=f.get("path")
    if not isinstance(url,str):raise ValueError("Missing archive path")
    return guarded(url)

def download(url,path):
    total=0
    sha=hashlib.sha256()
    with OPENER.open(urllib.request.Request(guarded(url),headers={
            "User-Agent":"CELIKOM-static-research/1.0"}),timeout=120) as r, path.open("wb") as out:
        if r.status!=200:raise ValueError("Mirror HTTP "+str(r.status))
        size=int(r.headers.get("Content-Length") or "0")
        if size>MAX:raise ValueError("Mirror APK too large")
        while True:
            part=r.read(1024*1024)
            if not part:break
            total+=len(part)
            if total>MAX:raise ValueError("Mirror download cap exceeded")
            out.write(part);sha.update(part)
    if not zipfile.is_zipfile(path):raise ValueError("Mirror response is not APK ZIP")
    return total,sha.hexdigest()

def verify(apk):
    p=subprocess.run([sdk_tool("apksigner"),"verify","--verbose","--print-certs",str(apk)],
        capture_output=True,text=True,timeout=60)
    if p.returncode:raise ValueError("Mirror APK signature cryptographically invalid")
    hashes=set(x.replace(":","").lower() for x in re.findall(
        r"(?:V\d+(?:\.\d+)? Signer:|Signer #\d+) certificate SHA-256 digest:\s*([a-fA-F0-9:]+)",p.stdout))
    if hashes!={RUSTORE_SHA256_CERT}:raise ValueError("Mirror APK signer is NOT the verified official Yandex signer")
    if not ("Verified using v2 scheme (APK Signature Scheme v2): true" in p.stdout or
            "Verified using v3 scheme (APK Signature Scheme v3): true" in p.stdout):
        raise ValueError("Mirror APK lacks verified v2/v3 scheme")
    a=subprocess.run([sdk_tool("aapt"),"dump","badging",str(apk)],
                     capture_output=True,text=True,timeout=60)
    if a.returncode:raise ValueError("Mirror AndroidManifest invalid")
    m=re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'",
                a.stdout,re.MULTILINE)
    if not m or m.group(1)!=PKG or int(m.group(2))!=CODE or m.group(3)!=VERSION:
        raise ValueError("Mirror APK manifest is NOT exact #170gpr package/build")

def main():
    try:
        url=metadata()
        with tempfile.TemporaryDirectory(prefix="celikom-exact-gpr-readonly-") as tmp:
            archive=Path(tmp)/"mirrored-release.apk"
            size,sha=download(url,archive)
            verify(archive)
            # Strictly offline static scan of verified publisher-signed version.
            result=scan(archive)
            print(json.dumps({
                "source":"third-party public Aptoide mirror, verified against official RuStore signer",
                "package":PKG,"target_version":VERSION,"version_code":CODE,
                "sha256":sha,"bytes":size,
                "publisher_certificate_verified":RUSTORE_SHA256_CERT,
                "structural_native_audio_inventory":result,
                "actual_runtime_player_hook":"NOT_PROVEN_STATIC_ONLY",
                "play_protect":"NOT_TESTED",
                "proprietary_apk":"EPHEMERAL_DELETED_AFTER_SCAN_NO_REPO_ARTIFACT",
            },indent=2))
        return 0
    except Exception as exc:
        print("EXACT_GPR_STATIC_AUDIT_BLOCKED: "+str(exc)[:300],file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
