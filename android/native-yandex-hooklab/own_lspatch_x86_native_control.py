#!/usr/bin/env python3
"""No-vendor x86 native LSPatch control on the exact Android 11 ARM-bridge emulator.

This compares a normal OWN x86 process with its zero-bypass embedded LSPatch
version. It does not touch Yandex, phone, Passport, DRM or production.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

from build_owned_loader_host import APK, PACKAGE, check_host, apk_identity, signed_sha, sdk
from clone_lspatch_loader_zero import verify_native_loader_elf_offsets
from own_lspatch_nativebridge_control import execute, launch_owned
from recover_stored_origin_crc import rewrite_only_if_origin_crc_mismatch

X86 = "pro.celikom.armv7loaderhost.x86control"
OUTPUT = "CELIKOM-X86-LOADER-ONLY-Test.apk"


def package_x86_loader(patched: Path, work: Path) -> tuple[Path, dict]:
    recovered = work / "x86-recovered-unsigned.apk"
    info = rewrite_only_if_origin_crc_mismatch(patched, recovered)
    original = recovered if info["layout_repacked"] else patched
    aligned = work / "x86-verified-aligned.apk"
    execute([sdk("zipalign"), "-f", "-p", "4", str(original), str(aligned)],
            "X86_ALIGN", 90)
    key = work / "x86-only-lab.keystore"
    execute(["keytool", "-genkeypair", "-noprompt", "-storetype", "JKS",
             "-keystore", str(key), "-storepass", "x86-only-lab",
             "-keypass", "x86-only-lab", "-alias", "lab",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "2",
             "-dname", "CN=CELIKOM Disposable OWN x86, O=CELIKOM, C=XX"],
            "X86_LAB_KEY", 70)
    execute([sdk("apksigner"), "sign", "--ks", str(key),
             "--ks-pass", "pass:x86-only-lab", "--ks-key-alias", "lab",
             "--key-pass", "pass:x86-only-lab", "--min-sdk-version", "28",
             "--v4-signing-enabled", "false", str(aligned)],
            "X86_LAB_SIGN", 90)
    check_host(aligned, patched=True)
    if apk_identity(aligned) != (X86, "1", "") or not signed_sha(aligned):
        raise RuntimeError("X86_NATIVE_CONTROL_IDENTITY_INVALID")
    layout = verify_native_loader_elf_offsets(aligned)
    if not all(v["page_aligned_4096"] for v in layout.values()):
        raise RuntimeError("X86_NATIVE_LOADER_ZIP_ALIGNMENT_INVALID")
    with zipfile.ZipFile(aligned) as source:
        cfg = json.loads(source.read("assets/lspatch/config.json"))
        if type(cfg.get("sigBypassLevel")) is not int or cfg["sigBypassLevel"] != 0:
            raise RuntimeError("X86_NONZERO_SIGNATURE_BYPASS_PROHIBITED")
        if [n for n in source.namelist() if n.startswith("assets/lspatch/modules/")]:
            raise RuntimeError("X86_UNAUTHORIZED_MODULE")
    return aligned, {"native_library_machine": "EM_386",
                     "no_machine_mirror": True, "upstream_loader_elf_verified": True,
                     "host_abi": "x86", "lab_signature": True,
                     "sigbypass": 0, "modules_embedded": 0,
                     "recovered_origin_layout": bool(info["layout_repacked"])}


def run() -> dict:
    if (os.environ.get("GITHUB_ACTIONS") != "true" or
            os.environ.get("CELIKOM_OWN_X86_BRIDGE") != "1" or
            os.environ.get("CELIKOM_X86_NATIVE_CONTROL") != "1" or
            PACKAGE != X86):
        raise RuntimeError("X86_CONTROL_DISPOSABLE_GITHUB_CI_ONLY")
    abis = execute(["adb", "shell", "getprop", "ro.product.cpu.abilist"],
                   "X86_EMULATOR_ABIS").strip().split(",")
    if "x86" not in abis or "x86_64" in abis:
        raise RuntimeError("X86_NATIVE_CONTROL_INCORRECT_EMULATOR")
    original = execute(["adb", "shell", "pm", "path", "ru.yandex.music"],
                       "X86_VENDOR_ABSENCE", check=False)
    if "package:" in original:
        raise RuntimeError("X86_NATIVE_CONTROL_VENDOR_PRESENT")
    check_host(APK)
    with zipfile.ZipFile(APK) as source:
        lib = source.read("lib/x86/libcelikom_host_probe.so")[:20]
        if not lib.startswith(b"\x7fELF") or int.from_bytes(lib[18:20], "little") != 3:
            raise RuntimeError("X86_OWN_NATIVE_JNI_ELF_INVALID")
    baseline = launch_owned(APK, "X86_BASELINE", package=X86)
    if not (baseline["main_alive"] and baseline["activity_resumed"]):
        raise RuntimeError("X86_OWN_NATIVE_BASELINE_NOT_RUNNING")
    execute(["adb", "uninstall", X86], "X86_ONLY_OWN_UNINSTALL", 60)
    patched = Path(os.environ["RUNNER_TEMP"]) / "celikom-own-x86-lab" / OUTPUT
    if not patched.is_file():
        raise RuntimeError("X86_PATCHER_OUTPUT_MISSING")
    with tempfile.TemporaryDirectory(prefix="celikom-own-native-x86-") as dirname:
        normalized, evidence = package_x86_loader(patched, Path(dirname))
        patched_result = launch_owned(normalized, "X86_LSPATCH_ZERO_NATIVE",
                                      package=X86)
        if patched_result["main_alive"] and patched_result["activity_resumed"]:
            verdict = "OWN_X86_NATIVE_LSPATCH_PROCESS_RESUMED"
        elif patched_result["native_signal"] != "NOT_OBSERVED":
            verdict = "OWN_X86_NATIVE_LSPATCH_SIGNAL_CRASH"
        elif patched_result["dlopen_seen"]:
            verdict = "OWN_X86_NATIVE_LSPATCH_DLOPEN_FAILURE"
        else:
            verdict = "OWN_X86_NATIVE_LSPATCH_INCONCLUSIVE_NO_MAIN"
        return {"result": verdict, "baseline": baseline,
                "patched": patched_result, "metadata": evidence,
                "vendor_package_installed": False,
                "owner_phone_touched": False,
                "audio_substitution_tested": False,
                "raw_crash_content_published": False}


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        reason = str(exc)
        reason = reason if re.fullmatch(r"[A-Z][A-Z0-9_]{6,95}", reason) else \
                 "X86_CONTROL_PRIVATE_RUNTIME_ERROR"
        print(json.dumps({"result":"X86_CONTROL_BLOCKED", "category":reason,
                          "owner_phone_touched":False}), file=sys.stderr)
        sys.exit(2)
