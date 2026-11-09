#!/usr/bin/env python3
"""Ephemeral signed-release comparison: 2026.10.3 #170rur vs #170gpr DEX bytes.

Both input packages downloaded under strict HTTPS allowlists, independently
verified with Android apksigner + aapt and pinned Yandex publisher certificate.
Only code section hashes and exact match summary are logged; APKs deleted,
never installed or included in CI artifacts. DEX equivalence != runtime or
Play Protect compatibility and != manifest or native-library equivalence.
"""
from __future__ import annotations
import hashlib,json,re,sys,tempfile,zipfile
from pathlib import Path
import audit_rustore_host_once as rur
import audit_gpr_apkpure_once as gpr

def dex_hashes(path:Path)->dict:
    out={}
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not re.fullmatch(r"classes\d*\.dex",name):
                continue
            info=archive.getinfo(name)
            if info.file_size>rur.DEX_MAX:
                raise ValueError("DEX exceeds 128MiB limit")
            h=hashlib.sha256()
            with archive.open(name) as stream:
                while True:
                    block=stream.read(1024*1024)
                    if not block:break
                    h.update(block)
            out[name]={"bytes":info.file_size,"sha256":h.hexdigest()}
    if not out:raise ValueError("No base-APK DEX entries found")
    return out

def get_base(paths):
    found=[]
    for p in paths:
        with zipfile.ZipFile(p) as z:
            if "classes.dex" in z.namelist():
                found.append(p)
    if len(found)!=1:raise ValueError("Expected exactly one base APK")
    return found[0]

def main():
    try:
        appid=rur.official_metadata()
        rur_url=rur.store_file_url(appid)
        with tempfile.TemporaryDirectory(prefix="celikom-release-compare-") as work:
            root=Path(work)
            rp=root/"official-rur.apk"
            rur_bytes,rur_sha=rur.download_temp(rur_url,rp)
            rur.signer_digest(rp,rur.sdk_tool("apksigner"))
            rur.manifest_version(rp,rur.sdk_tool("aapt"))
            gp=root/"public-mirror-gpr.xapk"
            gpr_bytes,gpr_sha=gpr.download(gp)
            gp_parts=gpr.split_apks(gp,root)
            gpr.inspect_publisher(gp_parts)
            code_rur=dex_hashes(rp)
            code_gpr=dex_hashes(get_base(gp_parts))
            names_match=set(code_rur)==set(code_gpr)
            identical=names_match and all(code_rur[n]==code_gpr[n] for n in code_rur)
            different=sorted(set(code_rur)|set(code_gpr),key=str)
            delta=[n for n in different if code_rur.get(n)!=code_gpr.get(n)]
            print(json.dumps({
                "publisher_verified":True,
                "publisher_sha256":rur.RUSTORE_SHA256_CERT,
                "package":rur.PACKAGE,"rur_version":rur.RUSTORE_VERSION,
                "gpr_version":gpr.VERSION,"version_code":rur.CODE,
                "rur_package_sha256":rur_sha,"gpr_xapk_sha256":gpr_sha,
                "rur_container_size":rur_bytes,"gpr_container_size":gpr_bytes,
                "rur_dex":code_rur,"gpr_dex":code_gpr,
                "all_dex_byte_identical":identical,
                "changed_dex_names":delta,
                "interpretation":(
                    "DEX_CODE_EXACTLY_IDENTICAL_STATIC_IN_PROCESS_JAVA_METHOD_TRACES_TRANSFERABLE"
                    if identical else
                    "DEX_BYTES_DIFFER_CANNOT_ASSUME_SAME_CODE_PATHS"),
                "not_evaluated":"Runtime track/edition ID, native libraries, manifest differences, signing update path or Play Protect",
                "binary_storage":"NONE_EPHEMERAL_DELETED",
            },ensure_ascii=False,indent=2))
        return 0
    except Exception as exc:
        print("SIGNED_RELEASE_COMPARISON_BLOCKED: "+str(exc)[:400],file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
