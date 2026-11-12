#!/usr/bin/env python3
"""Isolated 2025 GPR sixteen-split -> single-APK LSPatch 0/2 native ARM13 A/B.

Strict provenance; no vendor certificate impersonation, account, audio or user
device test. All proprietary inputs and lab-signed APKs stay on one ephemeral
runner and are removed. A green result means MAIN/RESUMED, NOT usable music.
"""
from __future__ import annotations

import json
import hashlib
import xml.etree.ElementTree as ET
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import clone_native_splits_ephemeral as source
import clone_native_splits_arsclib_ephemeral as arsc
import clone_main_crash_buffer as diagnostics
from clone_lspatch_loader_zero import wrap_clone_with_lspatch_zero
from merge_lab_splits_ephemeral import fingerprint, verify_merged_payloads
from owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    verified_orig_paths, ephemeral_clone, apk_name, guest, cmd, PKG, ORIGINAL,
    SPLITS, CODE, CONTAINER, stop
)
import owner_2025_gpr_arm13_signed_control as original_control

BRANCH = "experiment/android-a1-independent-sig-compat-arm13-20261112"
VERSION = "24025542"
SOURCE_BYTES = 45961661
SOURCE_SHA256 = "8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
ANDROID = "{http://schemas.android.com/apk/res/android}"
OWNED_CLONE_PERMISSIONS_TO_OMIT = {
    "com.yandex.permission.READ_CREDENTIALS",
    "com.yandex.music.RELAY_PERMISSION",
}


def coexist_manifest_2025(source_text: str) -> tuple[bytes, dict]:
    """Rewrite *only* independent lab clone manifests to avoid global duplicates.

    Original 16 publisher-signed APKs are never modified. Mirrors the proven
    16+16 coexistence namespace rules, now BEFORE the one-APK merger.
    """
    rewritten, earlier = source.rewrite_manifest(source_text)
    tree = ET.fromstring(rewritten)
    if tree.tag != "manifest":
        stop("SIGCOMPAT_2025_MANIFEST_ROOT_INVALID")
    removed = 0
    provider_rewrites = 0
    for child in list(tree):
        if child.tag != "permission":
            continue
        name = child.attrib.get(ANDROID + "name", "")
        if name not in OWNED_CLONE_PERMISSIONS_TO_OMIT:
            continue
        if child.attrib.get(ANDROID + "protectionLevel") != "signature":
            stop("SIGCOMPAT_2025_PERMISSION_PROTECTION_CHANGED")
        tree.remove(child)
        removed += 1
    for provider in tree.iter("provider"):
        authority = provider.attrib.get(ANDROID + "authorities", "")
        if not authority:
            continue
        old = authority.split(";")
        new = [value if value.startswith(PKG + ".") else
               PKG + ".provider." + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
               for value in old]
        if any(not value for value in old):
            stop("SIGCOMPAT_2025_EMPTY_PROVIDER_AUTHORITY")
        provider_rewrites += sum(a != b for a, b in zip(old, new))
        provider.set(ANDROID + "authorities", ";".join(new))
    stats = {
        "provider_authorities": earlier["provider_authorities"] + provider_rewrites,
        "global_provider_authorities_renamed": provider_rewrites,
        "publisher_signature_permission_declarations_removed": removed,
    }
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True), stats



def require_guest() -> None:
    if (os.getenv("GITHUB_ACTIONS") != "true" or
            os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic" or
            os.getenv("GITHUB_REF_NAME") != BRANCH or
            os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1" or
            os.getenv("CELIKOM_NATIVE_ARM13_REDDROID_CLONE") != "1" or
            platform.machine() != "aarch64"):
        stop("SIGCOMPAT_2025_EXACT_ARM13_BRANCH_REQUIRED")
    if (guest("getprop", "sys.boot_completed").stdout.strip() != "1" or
            guest("getprop", "ro.build.version.sdk").stdout.strip() != "33"):
        stop("SIGCOMPAT_2025_ANDROID13_GUEST_NOT_BOOTED")
    abis = set(guest("getprop", "ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"armeabi-v7a", "arm64-v8a"} <= abis or {"x86", "x86_64"} & abis:
        stop("SIGCOMPAT_2025_NATIVE_ARM_ABIS_REQUIRED")
    if guest("pm", "path", PKG).stdout.strip() or guest("pm", "path", ORIGINAL).stdout.strip():
        stop("SIGCOMPAT_2025_GUEST_MUST_BE_EMPTY")


def count_installed(package: str) -> int:
    rows = guest("pm", "path", package).stdout.splitlines()
    return sum(line.startswith("package:") for line in rows)


def clone_observation() -> dict:
    started = guest("am", "start", "--user", "0", "-n",
                    PKG + "/ru.yandex.music.main.MainScreenActivity", timeout=65)
    accepted = (started.returncode == 0 and
                ("Starting:" in started.stdout or "Warning: Activity not started" in started.stdout)
                and "Error:" not in started.stdout and "Exception" not in started.stdout)
    main_pids = []
    resumed = 0
    focused = 0
    for i in range(25):
        time.sleep(3)
        pid = guest("pidof", PKG, timeout=30).stdout.strip()
        main_pids.append(pid if re.fullmatch(r"[0-9]+", pid) else None)
        activity = guest("dumpsys", "activity", "activities", timeout=40).stdout
        resumed += int(any(PKG + "/" in line and
                           ("mResumedActivity" in line or "topResumedActivity" in line
                            or "ResumedActivity:" in line)
                           for line in activity.splitlines()))
        if i in (0, 24):
            window = guest("dumpsys", "window", "windows", timeout=40).stdout
            focused += int(any(PKG + "/" in line and
                               ("mCurrentFocus" in line or "mFocusedApp" in line)
                               for line in window.splitlines()))
    stable = (accepted and all(main_pids) and len(set(main_pids)) == 1
              and resumed == 25 and focused == 2)
    report = {
        "native_main_launch_accepted": accepted,
        "main_pid_same_all_25_samples": bool(all(main_pids) and len(set(main_pids)) == 1),
        "resumed_25_samples": resumed,
        "foreground_focus_first_last": focused,
        "native_main_75s_pass": bool(stable),
        "pid_and_vendor_logs_disclosed": False
    }
    if not stable:
        exit_info = guest("dumpsys", "activity", "exit-info", PKG, timeout=45)
        if exit_info.returncode == 0:
            report["main_exit"] = diagnostics.classify_main_exit_status(exit_info.stdout)
            crash = guest("logcat", "-b", "crash", "-d", timeout=45)
            if crash.returncode == 0:
                report["main_crash"] = diagnostics.classify_main_crash_buffer(
                    exit_info.stdout, crash.stdout)
    return report


def merge_2025(clones: list[tuple[str, Path]], work: Path,
               editor: Path, key: Path, expected_cert: str, min_sdk: int) -> Path:
    if len(clones) != 16 or len({name for name, _ in clones}) != 16:
        stop("SIGCOMPAT_2025_MERGE_NEEDS_16_UNIQUE_SPLITS")
    merge_dir = work / "verified-lab-2025-splits"
    merge_dir.mkdir()
    seen = set()
    paths = []
    for name, file in clones:
        split = "" if name == "base" else name
        info = apk_name(file)
        if (not re.fullmatch(r"[A-Za-z0-9_.-]*", split) or split in seen
                or info.get("name") != PKG or info.get("versionCode") != VERSION
                or info.get("split", "") != split):
            stop("SIGCOMPAT_2025_CLONE_SPLIT_IDENTITY_DRIFT")
        seen.add(split)
        shutil.copyfile(file, merge_dir / ("base.apk" if not split else "split_" + split + ".apk"))
        paths.append(file)
    if "" not in seen:
        stop("SIGCOMPAT_2025_CLONE_BASE_MISSING")
    unsigned = work / "merged-2025-unsigned.apk"
    arsc.run(["java", "-Xmx3g", "-jar", str(editor), "m",
              "-i", str(merge_dir), "-o", str(unsigned)],
             "SIGCOMPAT_2025_APKEDITOR_MERGE", 600)
    merged = work / "merged-2025-own-signed.apk"
    arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
              str(unsigned), str(merged)], "SIGCOMPAT_2025_MERGED_ALIGN", 120)
    arsc.run([source.sdk_tool("apksigner"), "sign", "--ks", str(key),
              "--ks-pass", "pass:ephemeral-lab-only", "--ks-key-alias", "research",
              "--key-pass", "pass:ephemeral-lab-only", "--min-sdk-version", str(min_sdk),
              "--v4-signing-enabled", "false", str(merged)],
             "SIGCOMPAT_2025_MERGED_SIGN", 120)
    metadata = apk_name(merged)
    if (metadata.get("name") != PKG or metadata.get("versionCode") != VERSION
            or metadata.get("split", "") or fingerprint(merged, arsc) != expected_cert):
        stop("SIGCOMPAT_2025_MERGED_METADATA_OR_CERT_DRIFT")
    try:
        parity = verify_merged_payloads(paths, merged)
    except (ValueError, OSError):
        stop("SIGCOMPAT_2025_MERGED_DEX_NATIVE_PARITY_FAILED")
    if not parity["payload_byte_hashes_match"]:
        stop("SIGCOMPAT_2025_MERGED_DEX_NATIVE_PARITY_FAILED")
    print(json.dumps({"stage": "2025_SINGLE_APK_MERGE_STRUCTURAL_PASS",
                      "source_split_count": len(clones),
                      "payload_dex_count": parity["single_apk_payload_dex_count"],
                      "payload_native_count": parity["single_apk_payload_native_library_count"],
                      "no_consumer_apk_published": True}, sort_keys=True))
    return merged


def single_install(apk: Path) -> str:
    remote = "/data/local/tmp/celikom-2025-ephemeral-wrapped.apk"
    copied = cmd(["docker", "cp", str(apk), f"{CONTAINER}:{remote}"], 150)
    if copied.returncode:
        return "DOCKER_COPY_FAILED"
    try:
        installed = guest("pm", "install", "--user", "0", "-t", "-r", remote, timeout=230)
        if installed.returncode == 0 and "Success" in installed.stdout:
            return "INSTALLED"
        for marker in ("INSTALL_FAILED_CONFLICTING_PROVIDER", "INSTALL_FAILED_DUPLICATE_PERMISSION",
                       "INSTALL_FAILED_INVALID_APK", "INSTALL_FAILED_MISSING_SPLIT",
                       "INSTALL_FAILED_UPDATE_INCOMPATIBLE", "INSTALL_FAILED_NO_MATCHING_ABIS"):
            if marker in installed.stdout + installed.stderr:
                return marker
        return "INSTALL_FAILED_OTHER"
    finally:
        guest("rm", "-f", remote, timeout=35)


def run(xapk: Path) -> dict:
    require_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-a1-2025-sigcompat-") as directory:
        work = Path(directory)
        originals = verified_orig_paths(xapk, work)
        parts = [(apk_name(p).get("split", "") or "base", p) for p in originals]
        result = {"source": "2025.10.4 #120.1gpr", "archive_sha256_verified": True,
                  "verified_issuer_splits": len(originals),
                  "exact_source_bytes": SOURCE_BYTES,
                  "native_arm13": True, "sigcompat_levels_requested": [0, 2],
                  "original_apk_modified": False, "publisher_signer_spoofed": False,
                  "phone_touched": False, "consumer_apk_published": False,
                  "account_or_audio_tested": False, "verdict": "PREPARING"}
        original_installed = original_control.install_original(parts)
        result["issuer_install"] = original_installed["install_status"]
        if result["issuer_install"] != "INSTALLED" or count_installed(ORIGINAL) != SPLITS:
            result["verdict"] = "ORIGINAL_2025_INSTALL_NO_GO"
            return result
        result["issuer_launch"] = original_control.launch_main()["launch_status"]
        if result["issuer_launch"] != "NATIVE_MAIN_ACTIVITY_ACCEPTED":
            result["verdict"] = "ORIGINAL_2025_LAUNCH_NO_GO"
            return result
        observed = original_control.observe()
        result["issuer_75s"] = {
            "same_main_pid": observed["same_exact_main_pid_all_samples"],
            "resumed_samples": observed["resumed_activity_samples"],
            "samples": observed["sample_count"],
            "focus_first_last": observed["window_focus_first_last_count"]}
        if (not observed["same_exact_main_pid_all_samples"]
                or observed["resumed_activity_samples"] != 25):
            result["verdict"] = "ORIGINAL_2025_NATIVE_75S_NO_GO"
            return result

        clones, meta = ephemeral_clone(originals, work,
                                       manifest_rewriter=coexist_manifest_2025)
        result["own_2025_verified_splits"] = meta["lab_cloned_2025_splits"]
        key = work / "unique-ephemeral-signer.jks"
        arsc.run(["keytool", "-changealias", "-keystore", str(key),
                  "-storepass", "ephemeral-lab-only", "-keypass", "ephemeral-lab-only",
                  "-alias", "celikom-lab", "-destalias", "research"],
                 "SIGCOMPAT_2025_REUSE_EXACT_OWN_SIGNER", 80)
        base = next(file for name, file in clones if name == "base")
        cert = fingerprint(base, arsc)
        if cert == source.RUSTORE_SHA256_CERT:
            stop("SIGCOMPAT_2025_PUBLISHER_CERT_FORBIDDEN")
        merged = merge_2025(clones, work, work / "APKEditor-1.4.9-verified.jar",
                            key, cert, meta["base_manifest_min_sdk"])
        result["single_apk_verified_before_patch"] = True
        modes = {}
        for level in (0, 2):
            # Remove only the separately installed LAB application. Original stays.
            if count_installed(PKG):
                guest("pm", "uninstall", "--user", "0", PKG, timeout=100)
            staged = work / ("metaloader-level-" + str(level))
            staged.mkdir()
            if level == 2:
                os.environ["CELIKOM_A1_EVAL_SIGBYPASS_LEVEL"] = "2"
            else:
                os.environ.pop("CELIKOM_A1_EVAL_SIGBYPASS_LEVEL", None)
            try:
                wrapped, audit = wrap_clone_with_lspatch_zero(
                    merged, staged, key, cert, arsc, expected_version=VERSION)
                status = single_install(wrapped)
                entry = {"structural_signature_bypass_level": audit["signature_bypass_level"],
                         "verified_original_code_inside_loader": audit[
                             "embedded_origin_sha256_payload_parity"],
                         "install": status, "installed_apk_count": count_installed(PKG),
                         "issuer_still_installed_16_splits": count_installed(ORIGINAL) == 16}
                if status == "INSTALLED" and entry["installed_apk_count"] == 1:
                    guest("logcat", "-c", timeout=40)
                    entry.update(clone_observation())
                else:
                    entry["native_main_75s_pass"] = False
                modes[str(level)] = entry
            except (arsc.TrialError, ValueError, OSError, subprocess.TimeoutExpired) as error:
                reason = str(error)
                if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,92}", reason):
                    reason = "SIGCOMPAT_2025_PRIVATE_BUILD_ERROR"
                modes[str(level)] = {"native_main_75s_pass": False,
                                     "stage_failure": reason}
            print(json.dumps({"mode": level, "native_gate": modes[str(level)]},
                             sort_keys=True))
        result["lspatch_modes"] = modes
        result["issuer_remains_installed"] = count_installed(ORIGINAL) == 16
        result["verdict"] = (
            "2025_LSPATCH_LEVEL2_NATIVE_MAIN_75S_PASS_ONLY_NO_AUDIO"
            if modes["2"]["native_main_75s_pass"] and result["issuer_remains_installed"]
            else "2025_LSPATCH_LEVEL2_NATIVE_MAIN_NO_GO")
        return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--xapk", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.xapk)
        print(json.dumps(report, sort_keys=True))
        sys.exit(0 if report["verdict"] == "2025_LSPATCH_LEVEL2_NATIVE_MAIN_75S_PASS_ONLY_NO_AUDIO" else 1)
    except (RuntimeError, ValueError, OSError, arsc.TrialError,
            subprocess.TimeoutExpired) as error:
        message = str(error)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,92}", message):
            message = "SIGCOMPAT_2025_PRIVATE_RUNTIME_EXCEPTION"
        print(json.dumps({"verdict": "2025_LSPATCH_EXPERIMENT_ABORTED",
                          "reason": message, "owner_phone_touched": False,
                          "artifact_uploaded": False, "stage_a": "NO_GO"}, sort_keys=True))
        sys.exit(2)
