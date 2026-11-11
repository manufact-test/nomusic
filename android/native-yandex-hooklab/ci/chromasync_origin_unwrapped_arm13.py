#!/usr/bin/env python3
"""NO-MODIFICATION A/B: test nested 2025 Yandex origin.apk WITHOUT ChromaSync shell.

The exact owner-supplied competitor APK is sourced from an UNPUBLISHED draft.
Extract a byte-identical origin.apk ONLY to an ephemeral ARM13 CI guest, no
patching, no LSPatch, no modules, no signature bypass, no account or audio.
This cannot prove the original publisher-signed 2025 host was tested.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import platform
import sys
import tempfile
import zipfile
from pathlib import Path

from chromasync_exact_arm13_probe import (
    CLONE_PACKAGE, EXPECTED_SHA256, DockerGuest,
    package_installed, sha256_file
)

EMBEDDED_NAME = "assets/lspatch/origin.apk"
MAX_ORIGIN_BYTES = 115 * 1024 * 1024


def inspect_nested_origin(data: bytes) -> dict:
    """Structural safeguards; no vendor bytecode content logged or changed."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        dex_names = [
            name for name in names
            if name == "classes.dex" or
            (name.startswith("classes") and name.endswith(".dex") and
             name[7:-4].isdigit())
        ]
        if len(dex_names) != 6 or "AndroidManifest.xml" not in names:
            raise RuntimeError("EXACT_2025_NESTED_HOST_STRUCTURE_MISMATCH")
        if "assets/lspatch/config.json" in names or "assets/lspatch/loader.dex" in names:
            raise RuntimeError("NESTED_ORIGIN_CONTAINS_OUTER_LOADER")
        libs = [x for x in names if x.startswith("lib/") and x.endswith(".so")]
        return {
            "original_nested_dex_count": len(dex_names),
            "original_nested_manifest_present": True,
            "original_nested_native_libs_present": len(libs) > 0,
            "origin_lspatch_loader_embedded": False,
        }


def extract_exact_nested_origin(source: Path, output: Path) -> dict:
    if sha256_file(source) != EXPECTED_SHA256:
        raise RuntimeError("EXACT_OWNER_CHROMASYNC_DIGEST_MISMATCH")
    with zipfile.ZipFile(source) as outer:
        info = outer.getinfo(EMBEDDED_NAME)
        if info.file_size <= 0 or info.file_size > MAX_ORIGIN_BYTES:
            raise RuntimeError("NESTED_HOST_SIZE_OUT_OF_BOUNDS")
        raw = outer.read(info)
    meta = inspect_nested_origin(raw)
    output.write_bytes(raw)
    return {
        **meta,
        "original_nested_apk_bytes": len(raw),
        "original_nested_sha256": hashlib.sha256(raw).hexdigest(),
        "exact_owner_outer_sha_verified": True,
        "nested_content_modified": False,
        "foreign_module_installed": False,
        "signature_bypass_used": False,
    }


def run(source: Path, guest: DockerGuest) -> dict:
    if (os.getenv("GITHUB_ACTIONS") != "true" or
        os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID") != "1" or
        platform.machine() != "aarch64" or guest.serial != "127.0.0.1:5555"):
        raise RuntimeError("ONLY_DISPOSABLE_NATIVE_ARM13_CI")
    if guest.shell("getprop", "sys.boot_completed").strip() != "1":
        raise RuntimeError("ANDROID_NOT_BOOTED")
    if guest.shell("getprop", "ro.build.version.sdk").strip() != "33":
        raise RuntimeError("ANDROID_NOT_API33")
    if package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        raise RuntimeError("ANDROID_GUEST_NOT_CLEAN")
    result = {
        "mode": "extracted_nested_origin_2025_only",
        "account_login_tested": False,
        "audio_tested": False,
        "play_protect_tested": False,
        "wrapper_installed": False,
        "owner_device_touched": False,
    }
    with tempfile.TemporaryDirectory(prefix="celikom-owner-exact-unwrapped-") as folder:
        origin = Path(folder) / "origin.apk"
        result.update(extract_exact_nested_origin(source, origin))
        result["origin_install"] = guest.install([origin])
    if result["origin_install"] != "INSTALLED":
        result["verdict"] = "UNWRAPPED_HOST_INSTALL_FAILED"
        return result
    if not package_installed(guest.shell("pm", "list", "packages"), CLONE_PACKAGE):
        result["verdict"] = "UNWRAPPED_HOST_PACKAGE_MISMATCH"
        return result
    result["launch"] = guest.launch(CLONE_PACKAGE)
    if result["launch"] != "MAIN_LAUNCH_ACCEPTED":
        result["verdict"] = "UNWRAPPED_HOST_LAUNCH_FAILED"
        return result
    result.update(guest.observe(CLONE_PACKAGE))
    result["verdict"] = (
        "UNWRAPPED_2025_HOST_MAIN_SAME_PID_16S"
        if result["main_survives"] and result["activity_resumed_all_samples"]
        else "UNWRAPPED_2025_HOST_MAIN_NOT_SUSTAINED"
    )
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outer", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = run(args.outer, DockerGuest())
        print(json.dumps(result, sort_keys=True))
        return 0 if result["verdict"] == "UNWRAPPED_2025_HOST_MAIN_SAME_PID_16S" else 1
    except (OSError, RuntimeError, zipfile.BadZipFile, KeyError) as error:
        # Fixed-error class and fail closed; never emit vendor strings or paths.
        reason = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"verdict": "UNWRAPPED_CONTROL_NOT_COMPLETED", "reason": reason}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
