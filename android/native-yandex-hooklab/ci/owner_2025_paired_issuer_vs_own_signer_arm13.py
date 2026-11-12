#!/usr/bin/env python3
"""Paired native Android 13 causal control, fresh same guest & original package.

A: reverify pinned 16 publisher-signed APKs, install UNCHANGED, cold start 75s.
B: clean uninstall, install the same 16 APKS independently signed with ONE
    ephemeral non-publisher key, cold start 75s.
Only the signing+ZIP representation differs; no APKEditor or package rewrite.
Only private, PID-scoped Boolean/enumerated evidence can leave ephemeral CI.

No signature spoof, PackageManager or vendor check bypass, root on owner phone,
Yandex login/media, changes to publisher binaries, redistribution or artifact.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import time

from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest, install_clones, verified_orig_paths, apk_name, PKG, ORIGINAL, SPLITS,
    stop,
)
from owner_2025_same_name_own_key_arm13_control import (
    sign_same_name, observe_main_75_seconds,
)
from own_key_full_payload_identity_gate import verify_independent_signature_preserves_payload

EXPECTED_BRANCH="experiment/android-a1-2025-paired-signer-native-arm13-20261112"


def guard_clean_guest() -> dict:
    if (os.getenv("GITHUB_ACTIONS") != "true"
        or os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME") != EXPECTED_BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
        or platform.machine() != "aarch64"):
        stop("PAIRED_CONTROL_DISPOSABLE_ARM13_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("PAIRED_CONTROL_GUEST_BOOT_INVALID")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"} <= abis:
        stop("PAIRED_CONTROL_NATIVE_ABI_DRIFT")
    if guest("pm","path",ORIGINAL).stdout.strip() or guest("pm","path",PKG).stdout.strip():
        stop("PAIRED_CONTROL_GUEST_NOT_FRESH")
    return {"same_fresh_native_arm13_guest":True,"native_abi_arm64_and_armv7":True}


def verify_install_count() -> bool:
    rows=guest("pm","path",ORIGINAL).stdout.splitlines()
    return sum(x.startswith("package:") for x in rows) == SPLITS


def launch_after_clear_log() -> dict:
    cleared=guest("logcat","-c",timeout=45)
    if cleared.returncode:
        stop("PAIRED_CONTROL_LOG_BUFFER_CLEAR_FAILED")
    return observe_main_75_seconds()


def strict_75s_stable(observation: dict) -> bool:
    return (observation.get("launch_intent_accepted") is True
        and observation.get("main_alive_25_of_25") is True
        and observation.get("same_exact_main_pid_25_of_25") is True
        and observation.get("resumed_25_of_25") is True)


def verdict_for_pair(original_installed: bool, original: dict,
                     own_installed: bool, own: dict) -> str:
    """A differential is real only if the original 75s gate passes first."""
    if not original_installed or not strict_75s_stable(original):
        return "CONTROL_ORIGINAL_75S_NO_GO"
    if not own_installed:
        return "CONTROL_OWN_KEY_INSTALL_NO_GO"
    if strict_75s_stable(own):
        return "PAIRED_BOTH_NATIVE_MAIN_75S_STABLE"
    exit_info=own.get("exit_status",{})
    crash=own.get("main_crash_category",{})
    if (exit_info.get("latest_main_exit_reason")=="JAVA_CRASH"
        and crash.get("java_fatal_thread_enum")=="MAIN_UI"
        and crash.get("java_top_exception_enum")=="ILLEGAL_STATE"
        and "SIGNATURE" in crash.get("java_exception_security_markers",[])
        and crash.get("java_top_stack_family")=="YANDEX_APP"):
        return "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_SIGNATURE_JAVA_CRASH"
    return "PAIRED_ORIGINAL_STABLE_OWN_KEY_MAIN_OTHER_NO_GO"


def paired_run(archive: Path) -> dict:
    props=guard_clean_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-paired-signature-") as tmp:
        work=Path(tmp)
        originals=verified_orig_paths(archive,work)
        parts=[(apk_name(p).get("split","") or "base",p) for p in originals]
        if len(parts)!=SPLITS or len({x[0] for x in parts})!=SPLITS:
            stop("PAIRED_CONTROL_SOURCE_SPLITS_DRIFT")
        # Sign while issuer original is still untouched, so all cryptographic
        # and ZIP transformations are completed BEFORE both runtime passes.
        owned, signer=sign_same_name(originals,work)
        if len(parts)!=SPLITS or len(owned)!=SPLITS:
            stop("PAIRED_CONTROL_SPLIT_LAYOUT_MISMATCH")
        total_entry_payloads=0
        for (source_name, original_apk), (own_name, owned_apk) in zip(parts, owned):
            if source_name != own_name:
                stop("PAIRED_CONTROL_SPLIT_NAME_ORDER_CHANGED")
            # Crucial causal invariant: ZIP header/signature formats MAY differ,
            # but ALL ordinary entry contents must be exactly byte-identical,
            # not only native code, DEX and the manifest.
            proof=verify_independent_signature_preserves_payload(original_apk,owned_apk)
            total_entry_payloads+=proof["non_signature_zip_entries_checked"]
        result={
            "all_16_split_non_signing_entry_payloads_byte_identical":True,
            "non_signing_entry_content_hashes_verified_bounded":min(total_entry_payloads,16000),
            "signature_and_zip_metadata_not_claimed_identical":True,
            **props,
            **signer,
            "publisher_source_issuer_signed_16_of_16_verified":True,
            "source_apk_never_modified":True,
            "both_use_exact_original_vendor_package_name":True,
            "both_original_dex_and_native_payload_unchanged":True,
            "no_apkeditor_in_both_arms":True,
            "no_vendor_signature_spoof_or_bypass":True,
            "account_or_drm_or_audio_not_tested":True,
            "owner_phone_touched":False,
            "third_party_binary_distributed":False,
            "product_stage_a":"NO_GO",
        }
        result["publisher_install_status"]=install_clones(parts)
        source_install=(result["publisher_install_status"]=="INSTALLED"
                        and verify_install_count())
        result["publisher_16_splits_installed"]=source_install
        if not source_install:
            result["comparative_verdict"]="CONTROL_ORIGINAL_INSTALL_NO_GO"
            return result
        source_observation=launch_after_clear_log()
        result["publisher_main_75s"]=source_observation
        # Refuse to infer anything about our signer when issuer original
        # cannot pass the SAME guest / native-runtime window.
        if not strict_75s_stable(source_observation):
            result["comparative_verdict"]="CONTROL_ORIGINAL_75S_NO_GO"
            return result
        # Use Android PackageManager's normal uninstall. No user packages
        # or other system data can exist in this disposable fresh guest.
        uninstall=guest("pm","uninstall","--user","0",ORIGINAL,timeout=90)
        if (uninstall.returncode or
            not uninstall.stdout.strip().startswith("Success")):
            stop("PAIRED_CONTROL_ORIGINAL_UNINSTALL_FAILED")
        for _ in range(15):
            if (not guest("pm","path",ORIGINAL).stdout.strip()
                and not guest("pidof",ORIGINAL).stdout.strip()):
                break
            time.sleep(1)
        if (guest("pm","path",ORIGINAL).stdout.strip() or
            guest("pidof",ORIGINAL).stdout.strip()):
            stop("PAIRED_CONTROL_UNINSTALL_NOT_CLEAN")
        result["same_guest_publisher_uninstall_clean"]=True
        result["own_key_install_status"]=install_clones(owned)
        own_install=(result["own_key_install_status"]=="INSTALLED"
                     and verify_install_count())
        result["own_key_16_splits_installed"]=own_install
        own_observation=launch_after_clear_log() if own_install else {}
        result["own_key_main_75s"]=own_observation
        result["comparative_verdict"]=verdict_for_pair(
            source_install,source_observation,own_install,own_observation)
        # Even if two 75s UI stages run, the owner's audio acceptance is absent.
        result["product_stage_a"]="NO_GO"
        return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    options=parser.parse_args()
    try:
        output=paired_run(options.xapk)
        print(json.dumps(output,sort_keys=True))
        # A strict product gate cannot turn green merely because a
        # differential experiment confirmed an app-signature mismatch.
        return 1 if output["comparative_verdict"] != "PAIRED_BOTH_NATIVE_MAIN_75S_STABLE" else 0
    except Exception as exc:
        reason=str(exc)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
            reason="PAIRED_CONTROL_PRIVATE_EXCEPTION"
        print(json.dumps({
            "comparative_verdict":"PAIRED_CONTROL_ABORTED",
            "abort_reason":reason,
            "original_apk_modified":False,
            "binary_distributed":False,
            "owner_phone_touched":False,
            "product_stage_a":"NO_GO",
        },sort_keys=True))
        return 2


if __name__=="__main__":
    sys.exit(main())
