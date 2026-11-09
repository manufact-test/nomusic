#!/usr/bin/env python3
"""Ephemeral exact-GPR APKPure acquisition. Fail closed on identity or signer mismatch.

A third-party catalog listing alone is NOT evidence of an authentic Google Play
build. This utility only continues static analysis when Android APK signature,
target manifest and publisher certificate match pinned previously verified Yandex
publisher credential; it never runs/installs APK, patches or uploads binaries.
"""
from __future__ import annotations
import hashlib,io,json,re,subprocess,sys,tempfile,urllib.error,urllib.parse,urllib.request,zipfile
from pathlib import Path
from audit_rustore_host_once import RUSTORE_SHA256_CERT,sdk_tool,scan

PACKAGE="ru.yandex.music"
VERSION="2026.10.3 #170gpr"
CODE=24026531
LIMIT=160*1024*1024
URL="https://d.apkpure.com/b/XAPK/ru.yandex.music?version=latest"
DOMAINS=("apkpure.com","apkpure.net","winudf.com","winudf.net")

def strict_url(url):
    parsed=urllib.parse.urlsplit(url)
    host=(parsed.hostname or "").lower()
    if (parsed.scheme!="https" or not host or parsed.username or parsed.password
            or parsed.port not in (None,443)
            or not any(host==d or host.endswith("."+d) for d in DOMAINS)):
        raise ValueError("Unreviewed download redirect hostname: "+host)
    return url

class GuardedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        strict_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

OPENER=urllib.request.build_opener(GuardedRedirect())

def download(path):
    sha=hashlib.sha256();total=0
    request=urllib.request.Request(strict_url(URL),headers={
        "User-Agent":"Mozilla/5.0 (compatible; research-only)",
        "Accept":"application/octet-stream,application/zip,*/*"})
    with OPENER.open(request,timeout=110) as res,path.open("wb") as f:
        if res.status!=200:raise ValueError("Mirror download status not 200")
        declared=int(res.headers.get("Content-Length") or "0")
        if declared>LIMIT:raise ValueError("Unexpected mirror size")
        while True:
            part=res.read(1024*1024)
            if not part:break
            total+=len(part)
            if total>LIMIT:raise ValueError("Mirror size cap exceeded")
            sha.update(part);f.write(part)
    if total<5000 or not zipfile.is_zipfile(path):
        raise ValueError("Mirror response not APK/XAPK")
    return total,sha.hexdigest()

def split_apks(archive,temp):
    with zipfile.ZipFile(archive) as z:
        if "classes.dex" in z.namelist():
            return [archive]
        items=[x for x in z.infolist() if x.filename.lower().endswith(".apk")]
        if not items or len(items)>24:raise ValueError("Unexpected split APK count")
        paths=[]
        for i,item in enumerate(items):
            if item.file_size>LIMIT:raise ValueError("Split too large")
            path=temp/("split-"+str(i)+".apk")
            with z.open(item) as src,path.open("wb") as out:
                amount=0
                while True:
                    part=src.read(1024*1024)
                    if not part:break
                    amount+=len(part)
                    if amount>LIMIT:raise ValueError("Decompression cap exceeded")
                    out.write(part)
            paths.append(path)
        return paths

def inspect_publisher(apks):
    fingerprints=set()
    manifest_versions=[]
    for a in apks:
        p=subprocess.run([sdk_tool("apksigner"),"verify","--verbose","--print-certs",str(a)],
                         capture_output=True,text=True,timeout=55)
        if p.returncode:raise ValueError("APK signature invalid")
        sha={x.replace(":","").lower() for x in re.findall(
            r"(?:V\d+(?:\.\d+)? Signer:|Signer #\d+) certificate SHA-256 digest:\s*([0-9a-fA-F:]+)",p.stdout)}
        if len(sha)!=1:raise ValueError("Unexpected APK signer count")
        fingerprints.update(sha)
        b=subprocess.run([sdk_tool("aapt"),"dump","badging",str(a)],capture_output=True,text=True,timeout=45)
        if b.returncode:raise ValueError("Invalid APK manifest")
        m=re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'",
                    b.stdout,re.MULTILINE)
        if not m or m.group(1)!=PACKAGE or int(m.group(2))!=CODE:
            raise ValueError("Unexpected APK package or build code")
        manifest_versions.append(m.group(3))
    if VERSION not in manifest_versions:
        raise ValueError("Manifest version is NOT exact owner #170gpr")
    print("EXACT_GPR_PACKAGE_VERIFIED: version="+VERSION+" code="+str(CODE))
    print("EXACT_GPR_CERT_FINGERPRINTS: "+json.dumps(sorted(fingerprints)))
    if fingerprints!={RUSTORE_SHA256_CERT}:
        raise ValueError("Mirror signer differs from verified RuStore publisher certificate; manual independent Play signing attestation required before trusting")
    return manifest_versions

def main():
    try:
        with tempfile.TemporaryDirectory(prefix="celikom-signed-gpr-inspection-") as tmp:
            tmp=Path(tmp)
            path=tmp/"mirrored.xapk"
            size,hashval=download(path)
            print("EXACT_GPR_ARCHIVE: sha256="+hashval+" size="+str(size))
            apks=split_apks(path,tmp)
            print("EXACT_GPR_SPLITS: "+str(len(apks)))
            versions=inspect_publisher(apks)
            with_dex=[]
            for ap in apks:
                with zipfile.ZipFile(ap) as z:
                    if "classes.dex" in z.namelist():with_dex.append(ap)
            if len(with_dex)!=1:raise ValueError("Expected one base APK")
            surface=scan(with_dex[0])
            print(json.dumps({
                "verdict":"STATIC_ONLY_ROOTLESS_AND_PLAY_PROTECT_NOT_TESTED",
                "source":"third-party APKPure mirror checked against pinned Yandex RuStore publisher cert",
                "release":VERSION,"version_code":CODE,
                "mirror_archive_sha256":hashval,"signing_sha256":RUSTORE_SHA256_CERT,
                "static_scan":surface,
                "installed_or_executed":False,"binary_artifact_uploaded":False,
            },ensure_ascii=False,indent=2))
        return 0
    except (ValueError,urllib.error.URLError,OSError,zipfile.BadZipFile,subprocess.SubprocessError) as e:
        print("EXACT_GPR_APKPURE_AUDIT_BLOCKED: "+str(e)[:400],file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
