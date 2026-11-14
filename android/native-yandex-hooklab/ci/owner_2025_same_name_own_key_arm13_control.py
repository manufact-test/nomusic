#!/usr/bin/env python3
"""Disposable causal control: same original package NAME, OWN signer, no rebuild.

Only an offline side-by-side *research variable isolation*: a genuine original
16-split set is reconstituted as new ZIPs and signed with a fresh, different
ephemeral key, without changing any manifest, resources, classes or native code.
The derived APKs are used ONLY on a fresh ARM Android13 Redroid in CI, then
irreversibly deleted. They must not be offered to an owner or distributed.
This neither passes off publisher trust nor bypasses any app security, DRM or
Yandex authentication. A native runtime failure is a product NO-GO.
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

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import clone_native_splits_ephemeral as source
import clone_main_crash_buffer as diagnostics
from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    CODE, CONTAINER, ORIGINAL, SPLITS, apk_name, cmd, guest,
    install_clones, lab_manifest_min_sdk, lab_sdk_tool,
    stop, verified_orig_paths,
)
from lab_signer_signal_gate import probe_apk_zip
from lab_unsigned_archive_cleanroom import remove_stale_v1_from_disposable_unsigned

REF="experiment/android-a1-2025-causal-startup-controls-20261112"

def ensure_disposable_arm13() -> dict:
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic"
            or os.getenv("GITHUB_REF_NAME") != REF
            or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1"
            or platform.machine() != "aarch64"):
        stop("OWN_KEY_CONTROL_DISPOSABLE_ARM_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("OWN_KEY_CONTROL_ANDROID_GUEST_NOT_READY")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"} <= abis:
        stop("OWN_KEY_CONTROL_WRONG_NATIVE_ABI")
    if guest("pm","path",ORIGINAL).stdout.strip():
        stop("OWN_KEY_CONTROL_GUEST_NOT_FRESH")
    if guest("pm","path","pro.celikom.yandex.nativeclonelab").stdout.strip():
        stop("OWN_KEY_CONTROL_GUEST_HAS_CLONE")
    return {"fresh_native_arm_android13":True,"owner_device_untouched":True}

def sign_same_name(originals: list[Path], work: Path, keystore_path: Path | None = None) -> tuple[list[tuple[str,Path]],dict]:
    bases=[p for p in originals if not apk_name(p).get("split","")]
    if len(bases)!=1:
        stop("OWN_KEY_CONTROL_BASE_NOT_UNIQUE")
    base_sdk=lab_manifest_min_sdk(bases[0])
    if base_sdk!=24:
        stop("OWN_KEY_CONTROL_ORIGINAL_BASE_MIN_SDK_DRIFT")
    key=Path(keystore_path) if keystore_path is not None else work/"unique-own-key.jks"
    if keystore_path is None:
        source.action(["keytool","-genkeypair","-noprompt","-storetype","JKS",
                       "-keystore",str(key),"-storepass","ephemeral-lab-only",
                       "-keypass","ephemeral-lab-only","-alias","own-key",
                       "-keyalg","RSA","-keysize","2048","-validity","1",
                       "-dname","CN=CELIKOM Original Identity Own Signer Offline Control, O=CELIKOM, C=XX"],
                      "OWN_KEY_CONTROL_KEY_ERROR",90)
    elif key.is_symlink() or not key.is_file():
        stop("OWN_KEY_CONTROL_SUPPLIED_KEYSTORE_INVALID")
    lab=[]
    signer=None
    seen=set()
    removed=0
    for i,original in enumerate(originals):
        name=apk_name(original).get("split","")
        if name in seen:
            stop("OWN_KEY_CONTROL_DUPLICATE_SPLIT")
        seen.add(name)
        scratch=work/f"scratch-{i}.apk"
        # Re-create only an *independent lab intermediate*. Read source signed
        # original without modification; never invoke scrub on issuer file.
        with zipfile.ZipFile(original,"r") as src, zipfile.ZipFile(
                scratch,"w",allowZip64=True) as dst:
            for member in src.infolist():
                dst.writestr(member,src.read(member.filename))
        clean=work/f"unsigned-{i}.apk"
        report=remove_stale_v1_from_disposable_unsigned(scratch,clean)
        removed+=report["discarded_obsolete_v1_entries"]
        aligned=work/f"resigned-{i}.apk"
        source.action([lab_sdk_tool("zipalign"),"-f","-p","4",
                       str(clean),str(aligned)],"OWN_KEY_CONTROL_ALIGNMENT_FAILED",90)
        source.action([lab_sdk_tool("apksigner"),"sign",
                       "--ks",str(key),"--ks-pass","pass:ephemeral-lab-only",
                       "--ks-key-alias","own-key",
                       "--key-pass","pass:ephemeral-lab-only",
                       "--min-sdk-version",str(base_sdk),
                       "--v1-signing-enabled","true",
                       "--v2-signing-enabled","true",
                       "--v3-signing-enabled","true",
                       "--v4-signing-enabled","false",
                       str(aligned)],"OWN_KEY_CONTROL_SIGNING_FAILED",90)
        output_meta=apk_name(aligned)
        if (output_meta.get("name")!=ORIGINAL
                or output_meta.get("versionCode")!=CODE
                or output_meta.get("split","")!=name):
            stop("OWN_KEY_CONTROL_ORIGINAL_PACKAGE_IDENTITY_DRIFT")
        if source.native_payload_hashes(original)!=source.native_payload_hashes(aligned):
            stop("OWN_KEY_CONTROL_DEX_NATIVE_PAYLOAD_CHANGED")
        p=probe_apk_zip(aligned)
        if (not p["zip_integrity_ok"] or p["duplicate_entry_names"]
                or p["unsafe_entry_name_count"]
                or p["encrypted_entry_count"]):
            stop("OWN_KEY_CONTROL_ZIP_INVALID")
        command=[lab_sdk_tool("apksigner"),"verify","--verbose","--print-certs"]
        if name:
            command.extend(["--min-sdk-version",str(base_sdk)])
        v=cmd(command+[str(aligned)],90)
        if v.returncode:
            stop("OWN_KEY_CONTROL_CRYPTO_VERIFY_FAILED")
        matches=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([a-fA-F0-9:]+)",
                           v.stdout)
        if len(matches)!=1:
            stop("OWN_KEY_CONTROL_SINGLE_SIGNER_MISSING")
        digest=matches[0].replace(":","").lower()
        if digest==source.RUSTORE_SHA256_CERT:
            stop("OWN_KEY_CONTROL_PUBLISHER_CERT_MUST_DIFFER")
        if signer is not None and digest!=signer:
            stop("OWN_KEY_CONTROL_SPLIT_SIGNERS_DISAGREE")
        signer=digest
        lab.append((name if name else "base",aligned))
    if len(lab)!=SPLITS or len(seen)!=SPLITS or "" not in seen:
        stop("OWN_KEY_CONTROL_16_SPLITS_NOT_COMPLETE")
    return lab,{
        "own_key_same_vendor_package_name":True,
        "publisher_cert_impersonated":False,
        "full_original_signer_verification_required":True,
        "own_signature_verification_all_16":True,
        "payload_classes_and_native_unchanged":True,
        "resources_and_manifest_payload_not_transformed":True,
        "repack_without_apkeditor":True,
        "old_jarsigner_entries_removed_from_lab_copy":removed,
        "base_min_sdk":base_sdk,
        "own_signer_sha256":signer,
    }

def observe_main_75_seconds() -> dict:
    # No passwords, accounts, network calls or media attempts.
    start=guest("am","start","--user","0","-n",
                ORIGINAL+"/ru.yandex.music.main.MainScreenActivity",timeout=65)
    result={"launch_intent_accepted":start.returncode==0
            and ("Starting:" in start.stdout or "Warning: Activity not started" in start.stdout)}
    pids=[]
    resumed=0
    for _ in range(25):
        time.sleep(3)
        ps=guest("pidof",ORIGINAL)
        pids.append(ps.stdout.strip() if re.fullmatch(r"\d+",ps.stdout.strip()) else None)
        activity=guest("dumpsys","activity","activities")
        resumed+=int(any(ORIGINAL+"/" in line and
            ("mResumedActivity" in line or "topResumedActivity" in line)
            for line in activity.stdout.splitlines()))
    result["main_alive_25_of_25"]=all(pid is not None for pid in pids)
    result["same_exact_main_pid_25_of_25"]=(result["main_alive_25_of_25"]
                                            and len(set(pids))==1)
    result["resumed_25_of_25"]=resumed==25
    if not result["same_exact_main_pid_25_of_25"]:
        exit_info=guest("dumpsys","activity","exit-info",ORIGINAL,timeout=40)
        if exit_info.returncode==0:
            result["exit_status"]=diagnostics.classify_main_exit_status(
                exit_info.stdout,target_package=ORIGINAL)
            crash=guest("logcat","-b","crash","-d",timeout=45)
            if crash.returncode==0:
                result["main_crash_category"]=diagnostics.classify_main_crash_buffer(
                    exit_info.stdout,crash.stdout,target_package=ORIGINAL)
    return result

def main(xapk: Path) -> dict:
    device=ensure_disposable_arm13()
    with tempfile.TemporaryDirectory(prefix="celikom-same-name-own-signer-") as temp:
        work=Path(temp)
        originals=verified_orig_paths(xapk,work)
        lab,signer=sign_same_name(originals,work)
        out={**device,**signer,
             "verified_publisher_source_splits":len(originals),
             "verified_own_signed_splits":len(lab),
             "no_lspatch_or_signature_bypass":True,
             "no_owner_account_or_yandex_login_tested":True,
             "no_audio_or_play_protect_tested":True,
             "third_party_binary_uploaded":False}
        out["install_status"]=install_clones(lab)
        if out["install_status"]=="INSTALLED":
            rows=guest("pm","path",ORIGINAL).stdout.splitlines()
            out["installed_splits"]=sum(x.startswith("package:") for x in rows)
            if out["installed_splits"]==SPLITS:
                out.update(observe_main_75_seconds())
        stable=(out.get("install_status")=="INSTALLED"
                and out.get("installed_splits")==SPLITS
                and out.get("same_exact_main_pid_25_of_25")
                and out.get("resumed_25_of_25"))
        out["verdict"]=("OWN_KEY_UNMODIFIED_PACKAGE_75S_MAIN_STABLE"
                        if stable else "OWN_KEY_UNMODIFIED_PACKAGE_MAIN_NO_GO")
        out["stage_a"]="NO_GO"
        return out

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    args=p.parse_args()
    try:
        report=main(args.xapk)
        print(json.dumps(report,sort_keys=True))
        raise SystemExit(0 if report["verdict"]=="OWN_KEY_UNMODIFIED_PACKAGE_75S_MAIN_STABLE" else 1)
    except Exception as err:
        reason=str(err)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,92}",reason):
            reason="OWN_KEY_PUBLISHER_NAME_PRIVATE_LAB_EXCEPTION"
        print(json.dumps({"verdict":"OWN_KEY_CONTROL_ABORTED","reason":reason,
                          "source_original_modified":False,"owner_phone_touched":False,
                          "binary_published":False,"stage_a":"NO_GO"},sort_keys=True))
        raise SystemExit(2)
