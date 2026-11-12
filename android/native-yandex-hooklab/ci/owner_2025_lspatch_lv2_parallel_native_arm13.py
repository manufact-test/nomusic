#!/usr/bin/env python3
"""Isolated ARM13: own-package Yandex 2025 clone with original issuer signature metadata.

Source metadata comes ONLY from pinned verified original APK via upstream
LSPatch, not from competitor, network API, or secrets. Own-signed cloned host
uses its own manifest and providers. Only ephemeral Android 13 guest, never
owner phone/user login/audio, no APK binary/key artifact distribution.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
import os
import platform
import re
import struct
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    ORIGINAL, PKG, SPLITS, apk_name, cmd, guest, install_clones,
    lab_sdk_tool, stop, verified_orig_paths, ephemeral_clone,
)
from clone_lspatch_loader_zero import (
    download_pinned_patcher, verify_native_loader_elf_offsets,
)

BRANCH="experiment/android-a1-2025-lv2-own-package-parallel-20261112"
CONFIG="assets/lspatch/config.json"


def guard():
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or platform.machine()!="aarch64"):
        stop("PUBLISHER_SOURCE_PARALLEL_DISPOSABLE_ARM13_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("PUBLISHER_SOURCE_PARALLEL_ANDROID13_REQUIRED")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"} <= abis:
        stop("PUBLISHER_SOURCE_PARALLEL_NATIVE_ABI_REQUIRED")
    if guest("pm","path",PKG).stdout.strip() or guest("pm","path",ORIGINAL).stdout.strip():
        stop("PUBLISHER_SOURCE_PARALLEL_EMPTY_GUEST_REQUIRED")


def certificate(path:Path)->str:
    x=cmd([lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs",
           "--min-sdk-version","24",str(path)],90)
    if x.returncode:stop("PUBLISHER_SOURCE_PARALLEL_SIGNATURE_FAILED")
    m=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F:]+)",x.stdout)
    if len(m)!=1:stop("PUBLISHER_SOURCE_PARALLEL_CERTIFICATE_NOT_SINGLE")
    return m[0].replace(":","").lower()


def run_patcher(patcher:Path,source:Path,key:Path,work:Path,folder:str)->Path:
    dest=work/folder
    dest.mkdir()
    result=cmd(["java","-jar",str(patcher),"-k",str(key),
               "ephemeral-lab-only","celikom-lab","ephemeral-lab-only",
               "-o",str(dest),"-l","2",str(source)],500)
    if result.returncode:stop("PUBLISHER_SOURCE_PARALLEL_UPSTREAM_PATCH_FAILED")
    hits=list(dest.glob("*.apk"))
    if len(hits)!=1 or hits[0].stat().st_size>125_000_000:
        stop("PUBLISHER_SOURCE_PARALLEL_PATCH_OUTPUT_INVALID")
    return hits[0]


def read_config(apk:Path)->dict:
    try:
        with zipfile.ZipFile(apk) as z:
            value=json.loads(z.read(CONFIG))
            if (value.get("sigBypassLevel")!=2
                or value.get("useManager") is not False
                or not isinstance(value.get("originalSignature"),str)
                or not value["originalSignature"]):
                stop("PUBLISHER_SOURCE_PARALLEL_CONFIG_INVALID")
            if any(x.startswith("assets/lspatch/modules/") for x in z.namelist()):
                stop("PUBLISHER_SOURCE_PARALLEL_FOREIGN_MODULE_FORBIDDEN")
            return value
    except (KeyError,ValueError,zipfile.BadZipFile):
        stop("PUBLISHER_SOURCE_PARALLEL_CONFIG_READ_FAILED")


def replace_only_signature_metadata(src:Path, dst:Path, issuer_sig:str)->None:
    """Same own independent signer; no copied proprietary module or DEX changes."""
    if src.resolve()==dst.resolve() or dst.exists():
        stop("PUBLISHER_SOURCE_PARALLEL_FRESH_OUTPUT_REQUIRED")
    with zipfile.ZipFile(src) as before, zipfile.ZipFile(dst,"w",allowZip64=True) as after:
        infos=before.infolist()
        if len(infos)>20000 or len({x.filename for x in infos})!=len(infos):
            stop("PUBLISHER_SOURCE_PARALLEL_ZIP_MEMBER_SET_INVALID")
        after.comment=before.comment
        for old in infos:
            body=before.read(old)
            if old.filename==CONFIG:
                cfg=json.loads(body)
                if cfg.get("sigBypassLevel")!=2 or not cfg.get("originalSignature"):
                    stop("PUBLISHER_SOURCE_PARALLEL_OWN_CONFIG_INVALID")
                if cfg["originalSignature"]==issuer_sig:
                    stop("PUBLISHER_SOURCE_PARALLEL_SIGNATURES_NOT_DISTINCT")
                cfg["originalSignature"]=issuer_sig
                body=json.dumps(cfg,sort_keys=True,separators=(",",":")).encode("utf-8")
            info=copy.copy(old)
            info.extra=b""
            info.CRC=info.file_size=info.compress_size=0
            if (info.filename.startswith("assets/lspatch/so/")
                and info.filename.endswith("/liblspatch.so")
                and info.compress_type==zipfile.ZIP_STORED):
                offset=after.fp.tell()
                pad=(-(offset+30+len(info.filename.encode("utf-8"))))%4096
                if 0<pad<4:pad+=4096
                if pad:
                    info.extra=struct.pack("<HH",0xEFA1,pad-4)+bytes(pad-4)
            after.writestr(info,body,compress_type=old.compress_type)
    with zipfile.ZipFile(src) as before, zipfile.ZipFile(dst) as after:
        for item in before.namelist():
            if item!=CONFIG and hashlib.sha256(before.read(item)).digest()!=hashlib.sha256(after.read(item)).digest():
                stop("PUBLISHER_SOURCE_PARALLEL_NONCONFIG_PAYLOAD_DRIFT")


def sign_and_verify(source_apk:Path,key:Path,work:Path,ref_cert:str,
                    expected_package:str,issuer_signature:str)->Path:
    aligned=work/"parallel-lspatch-aligned.apk"
    sign=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",
              str(source_apk),str(aligned)],100)
    if sign.returncode:stop("PUBLISHER_SOURCE_PARALLEL_ZIPALIGN_FAILED")
    sign=cmd([lab_sdk_tool("apksigner"),"sign","--ks",str(key),
              "--ks-pass","pass:ephemeral-lab-only","--ks-key-alias","celikom-lab",
              "--key-pass","pass:ephemeral-lab-only","--min-sdk-version","24",
              "--v1-signing-enabled","true",
              "--v2-signing-enabled","true",
              "--v3-signing-enabled","true",
              "--v4-signing-enabled","false",str(aligned)],100)
    if sign.returncode:stop("PUBLISHER_SOURCE_PARALLEL_SIGN_FAILED")
    if certificate(aligned)!=ref_cert:
        stop("PUBLISHER_SOURCE_PARALLEL_LAB_CERT_MISMATCH")
    m=apk_name(aligned)
    if (m.get("name")!=expected_package or m.get("versionCode")!="24025542"
        or m.get("split","")):
        stop("PUBLISHER_SOURCE_PARALLEL_PACKAGE_VERSION_DRIFT")
    config=read_config(aligned)
    if config["originalSignature"]!=issuer_signature:
        stop("PUBLISHER_SOURCE_PARALLEL_ISSUER_METADATA_DRIFT")
    try:
        loader=verify_native_loader_elf_offsets(aligned)
    except (ValueError,zipfile.BadZipFile):
        stop("PUBLISHER_SOURCE_PARALLEL_ELF_LAYOUT_INVALID")
    if len(loader)!=4:
        stop("PUBLISHER_SOURCE_PARALLEL_LOADER_ABI_DRIFT")
    return aligned


def start(package:str) -> dict:
    started=guest("am","start","--user","0","-n",
                  package+"/ru.yandex.music.main.MainScreenActivity",timeout=70)
    if started.returncode:
        return {"started":False,"same_pid_75s":False,"resumed_75s":False}
    pid_samples=[]
    resumed=0
    for _ in range(25):
        time.sleep(3)
        alive=guest("pidof",package,timeout=30).stdout.strip()
        pid_samples.append(alive if re.fullmatch(r"\d+",alive) else None)
        activity=guest("dumpsys","activity","activities",timeout=45).stdout
        resumed+=int(any(package+"/" in line and
            ("mResumedActivity" in line or "topResumedActivity" in line
             or "ResumedActivity:" in line)
            for line in activity.splitlines()))
    okay=all(x is not None for x in pid_samples) and len(set(pid_samples))==1
    return {"started":True,"same_pid_75s":okay,"resumed_75s":resumed==25,
            "same_exact_package_pid_count_bounded":int(okay),
            "raw_pid_or_trace_logged":False}


def real_trial(xapk:Path)->dict:
    guard()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-own-parallel-lv2-") as t:
        work=Path(t)
        original=verified_orig_paths(xapk,work)
        clones,meta=ephemeral_clone(original,work)
        original_base=next((x for x in original if not apk_name(x).get("split","")),None)
        own_base=next((path for name,path in clones if name=="base"),None)
        if original_base is None or own_base is None or len(clones)!=SPLITS:
            stop("PUBLISHER_SOURCE_PARALLEL_SOURCE_NOT_COMPLETE")
        key=work/"unique-ephemeral-signer.jks"
        if not key.is_file():stop("PUBLISHER_SOURCE_PARALLEL_KEY_NOT_CREATED")
        own_cert=certificate(own_base)
        if certificate(original_base)==own_cert:
            stop("PUBLISHER_SOURCE_PARALLEL_SIGNER_NOT_INDEPENDENT")
        upstream=work/"lspatch-pinned-v1.2-487.jar"
        download_pinned_patcher(upstream)
        # Reference wrapper: publisher signed source provides authentic issuer
        # metadata, but its resulting APK is NEVER installed here.
        reference=run_patcher(upstream,original_base,key,work,"verified-issuer-reference")
        issuer_sig=read_config(reference)["originalSignature"]
        # Actual consumer clone: cloned/renamed base is source for loader with
        # existing own signer; only config's originalSignature is inherited
        # from the publisher reference. Never copy vendor module/secret.
        candidate=run_patcher(upstream,own_base,key,work,"owned-parallel-loader")
        raw=work/"parallel-issuer-compat-unsigned.apk"
        replace_only_signature_metadata(candidate,raw,issuer_sig)
        outer=sign_and_verify(raw,key,work,own_cert,PKG,issuer_sig)
        config_splits=[(name,path) for name,path in clones if name!="base"]
        if len(config_splits)!=15:
            stop("PUBLISHER_SOURCE_PARALLEL_CONFIG_SET_INCOMPLETE")
        clone_status=install_clones([("base",outer),*config_splits])
        clone_result=start(PKG) if clone_status=="INSTALLED" else {}
        # Check coexistence only AFTER real clone MAIN survives all 25 samples.
        if clone_result.get("same_pid_75s") and clone_result.get("resumed_75s"):
            original_layout=[(apk_name(path).get("split","") or "base",path)
                             for path in original]
            stock_status=install_clones(original_layout)
            stock_result=start(ORIGINAL) if stock_status=="INSTALLED" else {}
            own_alive_after=bool(guest("pidof",PKG).stdout.strip())
        else:
            stock_status="NOT_ATTEMPTED_UNTIL_OWN_MAIN_STABLE"
            stock_result={}
            own_alive_after=False
        stable=bool(clone_result.get("same_pid_75s")
                    and clone_result.get("resumed_75s"))
        parallel=stable and bool(stock_result.get("same_pid_75s")
                       and stock_result.get("resumed_75s") and own_alive_after)
        report={"verdict":("TWO_DISTINCT_NATIVE_YANDEX_PACKAGES_75S_COEXIST"
                         if parallel else
                         "OWN_PACKAGE_NATIVE_STABLE_STOCK_NOT_PROVEN"
                         if stable else "OWN_PACKAGE_NATIVE_75S_NOT_PROVEN"),
          "real_2025_publisher_input_splits_cryptographically_verified":16,
          "lspatch_level2_original_signature_metadata_from_real_issuer":True,
          "own_signed_clone_16_splits_prepared":True,
          "original_source_payload_not_published":True,
          "own_clone_status":clone_status,"own_clone_lifecycle":clone_result,
          "publisher_original_status":stock_status,"publisher_lifecycle":stock_result,
          "own_main_alive_after_original_foreground":own_alive_after,
          "native_arm13":True,"no_account_or_music_test":True,
          "owner_phone_touched":False,"no_binary_or_signing_key_artifact":True,
          "stage_a":"NO_GO"}
        print(json.dumps(report,sort_keys=True))
        return report


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    options=p.parse_args()
    try:
        real_trial(options.xapk)
    except Exception as exc:
        reason=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
            reason="PUBLISHER_SOURCE_PARALLEL_PRIVATE_FAILURE"
        print(json.dumps({"verdict":"OWN_PACKAGE_PARALLEL_A1_INCOMPLETE",
            "reason":reason,"owner_phone_touched":False,
            "binary_published":False,"stage_a":"NO_GO"},sort_keys=True))
        sys.exit(2)
