#!/usr/bin/env python3
"""Experimental independent, HONEST OWN source stamp (never issuer provenance).

2025 publisher original APK contains 'stamp-cert-sha256' ZIP metadata; a
routine independent signing naturally removes that publisher source stamp.
This causal control asks whether an independently signed APK with its OWN,
cryptographically valid, different source stamp can launch without spoofing
a publisher, invalidating Android checks or changing protected app code.

All derived source-stamped APKs and BOTH temporary own keys are erased by CI.
No original source binaries are modified, no account or audio is accessed,
no output APK is distributed; owner HONOR never touched.
"""
from __future__ import annotations

import json
import os
import platform
import re
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    CODE, CONTAINER, ORIGINAL, PKG, SPLITS, apk_name, cmd, guest,
    install_clones, lab_sdk_tool, source, stop, verified_orig_paths,
)
from owner_2025_same_name_own_key_arm13_control import (
    sign_same_name, observe_main_75_seconds,
)
from owner_2025_paired_issuer_vs_own_signer_arm13 import strict_75s_stable
from lab_signer_signal_gate import probe_apk_zip
from own_key_full_payload_identity_gate import _non_signing_entry_hashes
from owner_2025_signature_permission_comparison import compare_issuer_own_signer_package_grants

BRANCH="experiment/android-a1-2025-self-stamp-causal-arm13-20261112"
STAMP_ENTRY="stamp-cert-sha256"


def source_stamp_supported() -> None:
    help_result=cmd([lab_sdk_tool("apksigner"),"sign","--help"],timeout=50)
    if help_result.returncode or "--stamp-signer" not in (
            help_result.stdout + help_result.stderr):
        stop("OWN_STAMP_OFFICIAL_SIGNER_UNSUPPORTED")


def guest_clean() -> dict:
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic"
            or os.getenv("GITHUB_REF_NAME") != BRANCH
            or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
            or platform.machine() != "aarch64"):
        stop("OWN_STAMP_DISPOSABLE_NATIVE_ARM13_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
            or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("OWN_STAMP_ANDROID13_NOT_BOOTED")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"} <= abis:
        stop("OWN_STAMP_NATIVE_32_AND_64_ABI_REQUIRED")
    if (guest("pm","path",ORIGINAL).stdout.strip()
            or guest("pm","path",PKG).stdout.strip()):
        stop("OWN_STAMP_GUEST_NOT_FRESH")
    return {"native_arm_android13":True,"same_fresh_guest":True}


def manifest_and_content_equal_except_honest_stamp(
    publisher: Path, lab_stamped: Path
) -> dict:
    """Every ordinary original file unchanged; stamp metadata must DIFFER."""
    a=_non_signing_entry_hashes(publisher)
    b=_non_signing_entry_hashes(lab_stamped)
    if STAMP_ENTRY not in a or STAMP_ENTRY not in b:
        stop("OWN_STAMP_MARKER_MISSING")
    if a.pop(STAMP_ENTRY)==b.pop(STAMP_ENTRY):
        stop("OWN_STAMP_MUST_NOT_REUSE_PUBLISHER_STAMP")
    if not a or a.keys()!=b.keys():
        stop("OWN_STAMP_ORDINARY_ENTRY_SET_CHANGED")
    if any(digest!=b[name] for name,digest in a.items()):
        stop("OWN_STAMP_ORDINARY_PAYLOAD_CHANGED")
    return {"every_nonstamp_app_content_entry_byte_identical":True,
            "ordinary_entry_count_bounded":min(len(a),16000),
            "publisher_source_stamp_reused":False,
            "own_distinct_source_stamp_present":True,
            "vendor_entry_names_or_hashes_exposed":False}


def sign_own_source_stamp(
    original: list[Path], own: list[tuple[str,Path]], work: Path
) -> tuple[list[tuple[str,Path]],dict]:
    source_stamp_supported()
    app_key=work/"unique-own-key.jks"
    if not app_key.is_file():
        stop("OWN_STAMP_MAIN_SIGNER_UNAVAILABLE")
    stamp_key=work/"own-lab-source-stamp.jks"
    source.action(["keytool","-genkeypair","-noprompt","-storetype","JKS",
                   "-keystore",str(stamp_key),"-storepass","ephemeral-stamp-only",
                   "-keypass","ephemeral-stamp-only","-alias","own-stamp",
                   "-keyalg","RSA","-keysize","2048","-validity","1",
                   "-dname","CN=CELIKOM Independent Lab Source Stamp, O=CELIKOM, C=XX"],
                  "OWN_STAMP_PRIVATE_KEY_CREATE_FAILED",100)
    if len(original)!=SPLITS or len(own)!=SPLITS:
        stop("OWN_STAMP_SPLIT_SET_COUNT_INVALID")
    result=[]
    publisher_hashes=[]
    own_hashes=[]
    total_entries=0
    for i,((name,source_file),intermediate) in enumerate(zip(
          [(apk_name(p).get("split","") or "base",p) for p in original],own)):
        if name!=intermediate[0]:
            stop("OWN_STAMP_SPLIT_ORDER_CHANGED")
        own_input=intermediate[1]
        signed=work/f"own-stamped-{i}.apk"
        sign_args=[
            lab_sdk_tool("apksigner"),"sign",
            "--in",str(own_input),"--out",str(signed),
            "--force-stamp-overwrite",
            "--min-sdk-version","24",
            "--v1-signing-enabled","true",
            "--v2-signing-enabled","true",
            "--v3-signing-enabled","true",
            "--v4-signing-enabled","false",
            "--ks",str(app_key),
            "--ks-pass","pass:ephemeral-lab-only",
            "--ks-key-alias","own-key",
            "--key-pass","pass:ephemeral-lab-only",
            "--stamp-signer",
            "--ks",str(stamp_key),
            "--ks-pass","pass:ephemeral-stamp-only",
            "--ks-key-alias","own-stamp",
            "--key-pass","pass:ephemeral-stamp-only",
        ]
        source.action(sign_args,"OWN_STAMP_SIGNING_FAILED",130)
        meta=apk_name(signed)
        if (meta.get("name")!=ORIGINAL or meta.get("versionCode")!=CODE or
                (meta.get("split","") or "base")!=name):
            stop("OWN_STAMP_PACKAGE_META_DRIFT")
        probe=probe_apk_zip(signed)
        if (not probe["zip_integrity_ok"] or probe["duplicate_entry_names"]
                or probe["unsafe_entry_name_count"]
                or probe["encrypted_entry_count"]):
            stop("OWN_STAMP_ZIP_VERIFY_FAILED")
        verified=[lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs"]
        if name!="base":
            verified+=["--min-sdk-version","24"]
        verified.append(str(signed))
        check=cmd(verified,100)
        if check.returncode:
            stop("OWN_STAMP_APK_CRYPTO_VERIFY_FAILED")
        if not re.search(r"Verified for SourceStamp:\s*true",check.stdout,re.I):
            stop("OWN_STAMP_CRYPTO_SOURCE_STAMP_NOT_VERIFIED")
        maincert=re.findall(
            r"Signer #1 certificate SHA-256 digest:\s*([a-fA-F0-9:]+)",
            check.stdout)
        stampcert=re.findall(
            r"Source Stamp Signer certificate SHA-256 digest:\s*([a-fA-F0-9:]+)",
            check.stdout)
        if len(maincert)!=1 or len(stampcert)!=1:
            stop("OWN_STAMP_SIGNER_CERT_SET_INVALID")
        main_digest=maincert[0].replace(":","").lower()
        stamp_digest=stampcert[0].replace(":","").lower()
        if (main_digest==source.RUSTORE_SHA256_CERT or
            stamp_digest==source.RUSTORE_SHA256_CERT or
            main_digest==stamp_digest):
            stop("OWN_STAMP_CELIKOM_SIGNERS_MUST_DIFFER_FROM_ISSUER_AND_EACH_OTHER")
        publisher_hashes.append(main_digest)
        own_hashes.append(stamp_digest)
        strict_content=manifest_and_content_equal_except_honest_stamp(source_file,signed)
        total_entries+=strict_content["ordinary_entry_count_bounded"]
        result.append((name,signed))
    if len(set(publisher_hashes))!=1 or len(set(own_hashes))!=1:
        stop("OWN_STAMP_INCONSISTENT_SPLIT_SIGNERS")
    return result,{
        "source_stamp_issued_by_own_distinct_temporary_key":True,
        "publisher_source_stamp_or_signer_reused":False,
        "publisher_signature_spoofed":False,
        "original_nonstamp_files_all_byte_identical":True,
        "nonstamp_content_entries_checked_bounded":min(total_entries,16000),
        "source_stamp_crypto_verified_16_of_16":True,
    }


def no_side_effect_install_set(paths: list[tuple[str,Path]]) -> bool:
    return (install_clones(paths)=="INSTALLED"
        and sum(x.startswith("package:") for x in
                guest("pm","path",ORIGINAL).stdout.splitlines())==SPLITS)


def run(xapk: Path) -> dict:
    env=guest_clean()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-ownstamp-") as tmp:
        work=Path(tmp)
        original=verified_orig_paths(xapk,work)
        owned,_=sign_same_name(original,work)
        stamped,metadata=sign_own_source_stamp(original,owned,work)
        result={**env,**metadata,
            "original_issuer_splits_verified_16":True,
            "own_stamped_signed_splits_verified_16":True,
            "no_publisher_credential_or_media_tested":True,
            "no_owner_handset_touched":True,
            "original_publisher_apk_modified":False,
            "third_party_lab_apk_published":False,
            "stage_a":"NO_GO"}
        original_layout=[(apk_name(apk).get("split","") or "base",apk)
                         for apk in original]
        pub_installed=no_side_effect_install_set(original_layout)
        result["original_16_splits_installed"]=pub_installed
        if not pub_installed:
            result["verdict"]="ISSUER_CONTROL_INSTALL_FAILED"
            return result
        issuer_permission_raw=guest("dumpsys","package",ORIGINAL,timeout=80).stdout
        guest("logcat","-c")
        pub=observe_main_75_seconds()
        result["original_75s_stable"]=strict_75s_stable(pub)
        if not result["original_75s_stable"]:
            result["verdict"]="ISSUER_ORIGINAL_75S_CONTROL_FAILED"
            return result
        uninstall=guest("pm","uninstall","--user","0",ORIGINAL,timeout=90)
        if uninstall.returncode or not uninstall.stdout.strip().startswith("Success"):
            stop("OWN_STAMP_ORIGINAL_UNINSTALL_FAILED")
        for _ in range(15):
            if not guest("pm","path",ORIGINAL).stdout.strip() and not guest("pidof",ORIGINAL).stdout.strip():
                break
            time.sleep(1)
        if guest("pm","path",ORIGINAL).stdout.strip() or guest("pidof",ORIGINAL).stdout.strip():
            stop("OWN_STAMP_ORIGINAL_UNINSTALL_INCOMPLETE")
        stamped_installed=no_side_effect_install_set(stamped)
        result["own_source_stamp_16_splits_installed"]=stamped_installed
        if not stamped_installed:
            result["verdict"]="OWN_SOURCE_STAMP_INSTALL_FAILED"
            return result
        own_permission_raw=guest("dumpsys","package",ORIGINAL,timeout=80).stdout
        result["same_package_issuer_vs_own_signer_platform_grants"]=compare_issuer_own_signer_package_grants(issuer_permission_raw,own_permission_raw)
        guest("logcat","-c")
        own=observe_main_75_seconds()
        result["own_stamp_main_75s"]=own
        result["own_stamp_75s_stable"]=strict_75s_stable(own)
        result["verdict"]=(
           "OWN_SOURCE_STAMP_MAIN_75S_STABLE"
           if result["own_stamp_75s_stable"] else
           "OWN_SOURCE_STAMP_STILL_MAIN_NO_GO")
        return result


if __name__=="__main__":
    parser=__import__("argparse").ArgumentParser()
    parser.add_argument("--xapk",required=True,type=Path)
    args=parser.parse_args()
    try:
        report=run(args.xapk)
        print(json.dumps(report,sort_keys=True))
        sys.exit(0 if report["verdict"]=="OWN_SOURCE_STAMP_MAIN_75S_STABLE" else 1)
    except Exception as err:
        reason=str(err)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
            reason="OWN_STAMP_PRIVATE_CONTROL_EXCEPTION"
        print(json.dumps({
            "verdict":"OWN_STAMP_CONTROL_ABORTED",
            "reason":reason,
            "stage_a":"NO_GO",
            "source_apk_modified":False,
            "third_party_apk_distributed":False,
            "user_phone_touched":False
        },sort_keys=True))
        sys.exit(2)
