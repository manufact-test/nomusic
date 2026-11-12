#!/usr/bin/env python3
"""Genuine Yandex 2025 issuer input -> own-signed LSPatch2 outer + NESTED clone.

Verify BOTH outer and embedded origin.apk have the same independent cloned
package name, as in the user's competitor sample, while preserving original
publisher signing metadata produced by upstream LSPatch from genuine source.
No foreign module/code, credential hook, audio playback, owner phone or APK
distribution; only native disposable ARM Android13 lifecycle and coexistence.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import struct
import sys
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from ci.owner_2025_lspatch2_namespaced_clone_arm13 import (
    name_one, observe_clone, DEST
)
from ci.owner_2025_lspatch2_resigned_native_arm13 import wrap_lab_base
from ci.owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest,cmd,stop,verified_orig_paths,apk_name,install_clones,lab_sdk_tool,
    ORIGINAL,SPLITS
)
from ci.owner_2025_same_name_own_key_arm13_control import sign_same_name
from clone_native_splits_arsclib_ephemeral import download_editor

BRANCH="experiment/android-a1-2025-namespaced-lspatch2-inner-outer-identity-20261112"
VERSION="24025542"
EMBEDDED="assets/lspatch/origin.apk"
CFG="assets/lspatch/config.json"


def guard_guest():
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or platform.machine()!="aarch64"):
        stop("MATCHED_INNER_OUTER_DISPOSABLE_ARM13_ONLY")
    if (guest("getprop","ro.build.version.sdk").stdout.strip()!="33"
        or guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("pm","path",ORIGINAL).stdout.strip()
        or guest("pm","path",DEST).stdout.strip()):
        stop("MATCHED_INNER_OUTER_GUEST_NOT_FRESH")


def signed_outer(apk,key):
    signed=cmd([lab_sdk_tool("apksigner"),"sign",
             "--ks",str(key),"--ks-pass","pass:ephemeral-lab-only",
             "--ks-key-alias","own-key","--key-pass","pass:ephemeral-lab-only",
             "--min-sdk-version","24","--v4-signing-enabled","false",
             str(apk)],timeout=120)
    verified=cmd([lab_sdk_tool("apksigner"),"verify","--verbose",
                  "--min-sdk-version","24",str(apk)],timeout=110)
    if signed.returncode or verified.returncode:
        stop("MATCHED_OUTER_INDEPENDENT_SIGNATURE_INVALID")


def replace_embedded(wrapper,inner,work,key):
    if apk_name(inner).get("name")!=DEST:
        stop("MATCHED_NESTED_ORIGIN_NOT_CLONE_PACKAGE")
    original=work/"matched-origin-rebuilt-unsigned.apk"
    with zipfile.ZipFile(wrapper) as src:
        entries=src.infolist()
        names=[x.filename for x in entries]
        if len(entries)>10000 or len(names)!=len(set(names)) or EMBEDDED not in names or CFG not in names:
            stop("MATCHED_WRAPPER_ZIP_STRUCTURE_INVALID")
        if sum(x.file_size for x in entries)>512*1024*1024:
            stop("MATCHED_WRAPPER_ZIP_TOO_LARGE")
        oldconfig=src.read(CFG)
        if json.loads(oldconfig).get("sigBypassLevel")!=2:
            stop("MATCHED_WRAPPER_SIGCOMPAT_LEVEL_DRIFT")
        new_origin=inner.read_bytes()
        if len(new_origin)>128*1024*1024:
            stop("MATCHED_NESTED_SOURCE_OVERSIZED")
        with zipfile.ZipFile(original,"w",allowZip64=True) as dst:
            for item in entries:
                payload=new_origin if item.filename==EMBEDDED else src.read(item)
                meta=copy.copy(item)
                meta.extra=b""
                meta.CRC=meta.file_size=meta.compress_size=0
                if item.filename.startswith("assets/lspatch/so/") and item.filename.endswith("/liblspatch.so") and item.compress_type==zipfile.ZIP_STORED:
                    position=dst.fp.tell()
                    padding=(-(position+30+len(item.filename.encode("utf-8"))))%4096
                    if 0<padding<4:padding+=4096
                    if padding:
                        meta.extra=struct.pack("<HH",0xEFA1,padding-4)+bytes(padding-4)
                dst.writestr(meta,payload,compress_type=item.compress_type)
    aligned=work/"matched-origin-rebuilt-aligned.apk"
    a=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",str(original),str(aligned)],timeout=120)
    if a.returncode:stop("MATCHED_WRAPPER_OUTER_ALIGN_FAILED")
    signed_outer(aligned,key)
    with zipfile.ZipFile(aligned) as out,zipfile.ZipFile(wrapper) as before:
        if out.testzip() is not None:
            stop("MATCHED_WRAPPER_OUTER_CRC_FAILED")
        if out.read(EMBEDDED)!=inner.read_bytes():
            stop("MATCHED_WRAPPER_NESTED_CLONE_BYTES_CHANGED")
        if out.read(CFG)!=oldconfig:
            stop("MATCHED_WRAPPER_ISSUER_SIGNATURE_METADATA_CHANGED")
        for member in before.namelist():
            # An OWN re-sign necessarily rewrites/omits legacy JAR v1 signature
            # records. Never claim signing metadata are an immutable payload.
            signed_meta=(member=="stamp-cert-sha256" or
                member.startswith("META-INF/") and
                (member.upper().endswith((".SF",".RSA",".DSA",".EC")) or
                 member.upper()=="META-INF/MANIFEST.MF"))
            if member==EMBEDDED or signed_meta:
                continue
            if member not in out.namelist() or out.read(member)!=before.read(member):
                stop("MATCHED_WRAPPER_UNRELATED_PAYLOAD_DRIFT")
    return aligned


def run(archive):
    guard_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-matched-inner-outer-") as td:
        root=Path(td)
        originals=verified_orig_paths(archive,root)
        owner_signed,_=sign_same_name(originals,root)
        publisher_base=[p for p in originals if not apk_name(p).get("split","")]
        own_base=[p for name,p in owner_signed if name=="base"]
        if len(originals)!=16 or len(publisher_base)!=1 or len(own_base)!=1:
            stop("MATCHED_SIGNED_PUBLISHER_SOURCE_BASE_INVALID")
        wrapped=wrap_lab_base(publisher_base[0],root,own_base[0])
        editor=root/"pinned-apkeditor.jar"
        download_editor(editor)
        # First clone the NESTED publisher-signed Yandex code, not just outer
        # Android package manifest. This is the crucial missing arrangement.
        raw_inner=root/"verified-lspatch-nested-publisher-source.apk"
        with zipfile.ZipFile(wrapped) as z:
            raw_inner.write_bytes(z.read(EMBEDDED))
        inner_clone,inner_stats=name_one(raw_inner,editor,root,100,
                                           root/"unique-own-key.jks")
        if apk_name(inner_clone).get("name")!=DEST:
            stop("MATCHED_NESTED_ORIGIN_PACKAGE_NOT_CLONED")
        repaired_outer=replace_embedded(wrapped,inner_clone,root,
                                         root/"unique-own-key.jks")
        renamed=[]
        total_duplicate=0
        total_global=0
        for i,(name,piece) in enumerate(owner_signed):
            base=repaired_outer if name=="base" else piece
            updated,stats=name_one(base,editor,root,i,
                                    root/"unique-own-key.jks")
            renamed.append((name,updated))
            total_duplicate+=stats["duplicate_publisher_permission_declarations_removed"]
            total_global+=stats["global_appmetrica_provider_rewrites"]
        if len(renamed)!=16 or len(set(n for n,_ in renamed))!=16:
            stop("MATCHED_16_SPLIT_SET_INCOMPLETE")
        clone_base=[p for n,p in renamed if n=="base"]
        if len(clone_base)!=1:
            stop("MATCHED_CLONE_OUTER_BASE_NOT_UNIQUE")
        with zipfile.ZipFile(clone_base[0]) as outer:
            data=outer.read(EMBEDDED)
            embedded_copy=root/"matched-final-embedded.apk"
            embedded_copy.write_bytes(data)
            if apk_name(clone_base[0]).get("name")!=DEST or \
               apk_name(embedded_copy).get("name")!=DEST:
                stop("MATCHED_FINAL_OUTER_INNER_PACKAGE_IDENTITY_MISMATCH")
            if json.loads(outer.read(CFG)).get("sigBypassLevel")!=2:
                stop("MATCHED_FINAL_LSPATCH_LEVEL_DRIFT")
        report={
            "original_signed_splits_issuer_verified":16,
            "LSPatch_direct_input_publisher_signed":True,
            "original_signature_metadata_preserved":True,
            "outer_and_embedded_origin_match_clone_package":True,
            "clone_package":DEST,
            "LSPatch_level":2,
            "cloned_splits":16,
            "clone_global_provider_rewrites":total_global,
            "publisher_signature_permission_declarations_removed":total_duplicate,
            "single_apk_built":False,
            "native_clone_main_75s":False,
            "original_and_clone_coexist_installed":False,
            "user_phone_touched":False,
            "media_or_account_tested":False,
            "third_party_binaries_published":False,
            "stage_a":"NO_GO"
        }
        report["clone_install"]=install_clones(renamed)
        if report["clone_install"]!="INSTALLED":
            report["verdict"]="MATCHED_INNER_OUTER_CLONE_INSTALL_FAILED"
            return report
        report["installed_clone_count"]=sum(x.startswith("package:")
            for x in guest("pm","path",DEST).stdout.splitlines())
        if report["installed_clone_count"]!=16:
            report["verdict"]="MATCHED_INNER_OUTER_CLONE_SPLITS_MISSING"
            return report
        guest("logcat","-c")
        native=observe_clone()
        report["native_clone_main_75s"]=native["stable"]
        report["native_lifecycle"]=native
        report["publisher_install"]=install_clones([
            (apk_name(p).get("split","") or "base",p) for p in originals])
        report["original_and_clone_coexist_installed"]=report["publisher_install"]=="INSTALLED"
        report["verdict"]=(
            "MATCHED_INNER_OUTER_2025_LSPATCH2_NATIVE_AND_COEXIST_PASS"
            if report["native_clone_main_75s"] and report["original_and_clone_coexist_installed"]
            else "MATCHED_INNER_OUTER_LAUNCH_OR_COEXIST_NO_GO")
        return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        result=run(args.xapk)
        print(json.dumps(result,sort_keys=True))
        sys.exit(0 if result["verdict"]=="MATCHED_INNER_OUTER_2025_LSPATCH2_NATIVE_AND_COEXIST_PASS" else 1)
    except Exception as exc:
        code=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",code):
            code="MATCHED_INNER_OUTER_DISPOSABLE_ERROR"
        print(json.dumps({"verdict":"MATCHED_INNER_OUTER_EXPERIMENT_ABORTED",
                          "reason":code,"stage_a":"NO_GO",
                          "user_phone_touched":False,
                          "third_party_apk_published":False},sort_keys=True))
        sys.exit(2)
