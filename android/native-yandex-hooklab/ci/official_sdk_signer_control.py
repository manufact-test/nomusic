#!/usr/bin/env python3
"""SDK signing sanity controls using exclusively ORIGINAL synthetic APKs.

Before any vendor APK rebuild, prove official (not Debian-symlinked) SDK toolchain
can package, align, sign, verify and reject tampered test APKs. All generated
files, keystores and exact tool output remain in an erased temporary directory.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from lab_signer_signal_gate import classify_apksigner_failure

SDK_VERSION = "35.0.0"


class SyntheticSignerFailure(Exception):
    pass


def resolve_tools() -> tuple[dict[str, str], str]:
    root_text = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not root_text:
        raise SyntheticSignerFailure("OFFICIAL_ANDROID_SDK_ROOT_MISSING")
    root = Path(root_text).resolve(strict=True)
    build_dir = root / "build-tools" / SDK_VERSION
    if not build_dir.is_dir() or build_dir.is_symlink():
        raise SyntheticSignerFailure("OFFICIAL_BUILD_TOOLS_35_NOT_INSTALLED")
    tools = {}
    for name in ("aapt", "zipalign", "apksigner"):
        candidate = build_dir / name
        if not candidate.is_file() or candidate.is_symlink():
            raise SyntheticSignerFailure("OFFICIAL_BUILD_TOOL_MISSING_OR_SYMLINK")
        if not candidate.resolve().is_relative_to(build_dir.resolve()):
            raise SyntheticSignerFailure("OFFICIAL_BUILD_TOOL_REDIRECTED")
        tools[name] = str(candidate)
    platforms = sorted((root / "platforms").glob("android-*/android.jar"),
                       key=lambda p: int(p.parent.name.split("-")[-1])
                       if p.parent.name.split("-")[-1].isdigit() else -1,
                       reverse=True)
    if not platforms:
        raise SyntheticSignerFailure("OFFICIAL_ANDROID_PLATFORM_MISSING")
    if not platforms[0].resolve().is_relative_to(root):
        raise SyntheticSignerFailure("ANDROID_PLATFORM_REDIRECTED")
    return tools, str(platforms[0])


def process(args: list[str], category: str, timeout: int = 90) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                errors="replace", timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SyntheticSignerFailure(category + "_TOOL_UNAVAILABLE") from None
    if result.returncode:
        if "apksigner" in args[0] and "verify" in args:
            diagnostic = classify_apksigner_failure(
                result.returncode, result.stdout, result.stderr)
            print(json.dumps({"stage": category, "safe_signer_diagnostic": diagnostic},
                             sort_keys=True))
        raise SyntheticSignerFailure(category)
    return result.stdout


def build_and_sign(tools: dict[str, str], android_jar: str, root: Path,
                   min_sdk: int, key: Path) -> tuple[Path, str]:
    folder = root / ("synthetic-" + str(min_sdk))
    folder.mkdir()
    manifest = folder / "AndroidManifest.xml"
    manifest.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
        'package="pro.celikom.sdk.signercontrol" '
        'android:versionCode="1" android:versionName="1.0">\n'
        f'<uses-sdk android:minSdkVersion="{min_sdk}" android:targetSdkVersion="28"/>\n'
        '<application android:label="Owned synthetic signer test"/>\n'
        '</manifest>\n', encoding="utf-8")
    unsigned = folder / "unsigned.apk"
    aligned = folder / "aligned.apk"
    process([tools["aapt"], "package", "-f", "-M", str(manifest),
             "-I", android_jar, "-F", str(unsigned)], "SYNTHETIC_AAPT_PACKAGE_FAILED")
    process([tools["zipalign"], "-f", "-p", "4",
             str(unsigned), str(aligned)], "SYNTHETIC_ZIPALIGN_FAILED")
    process([tools["apksigner"], "sign", "--ks", str(key),
             "--ks-pass", "pass:ephemeral-lab-only", "--ks-key-alias", "test",
             "--key-pass", "pass:ephemeral-lab-only",
             "--min-sdk-version", str(min_sdk),
             "--v1-signing-enabled", "true",
             "--v2-signing-enabled", "true",
             "--v3-signing-enabled", "true",
             "--v4-signing-enabled", "false",
             str(aligned)], "SYNTHETIC_APKSIGNER_SIGN_FAILED")
    # No minSdk override: the verifier must independently read the binary
    # manifest and confirm all required schemes for this synthetic package.
    verified = process([tools["apksigner"], "verify", "--verbose",
                        "--print-certs", str(aligned)], "SYNTHETIC_SIGNED_VERIFY_FAILED")
    digest = re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9A-Fa-f:]+)",
                        verified)
    if len(digest) != 1:
        raise SyntheticSignerFailure("SYNTHETIC_CERT_NOT_SINGLE")
    return aligned, digest[0].replace(":", "").lower()


def tamper_synthetic_copy(signed: Path, destination: Path) -> None:
    shutil.copyfile(signed, destination)
    with zipfile.ZipFile(destination) as archive:
        info = archive.getinfo("AndroidManifest.xml")
        with destination.open("rb") as src:
            src.seek(info.header_offset)
            header = src.read(30)
        if len(header) != 30 or header[:4] != b"PK\x03\x04":
            raise SyntheticSignerFailure("SYNTHETIC_MANIFEST_LOCAL_HEADER_INVALID")
        namelen = int.from_bytes(header[26:28], "little")
        extralen = int.from_bytes(header[28:30], "little")
        offset = info.header_offset + 30 + namelen + extralen
        if info.compress_size < 5:
            raise SyntheticSignerFailure("SYNTHETIC_MANIFEST_PAYLOAD_TOO_SMALL")
        offset += info.compress_size // 2
    with destination.open("r+b") as target:
        target.seek(offset)
        chunk = target.read(1)
        if len(chunk) != 1:
            raise SyntheticSignerFailure("SYNTHETIC_MUTATION_FAILED")
        target.seek(offset)
        target.write(bytes([chunk[0] ^ 0x01]))


def run_controls() -> dict:
    tools, android_jar = resolve_tools()
    with tempfile.TemporaryDirectory(prefix="celikom-owned-signer-controls-") as folder:
        work = Path(folder)
        key = work / "synthetic-ephemeral.jks"
        process(["keytool", "-genkeypair", "-noprompt", "-storetype", "JKS",
                 "-keystore", str(key), "-storepass", "ephemeral-lab-only",
                 "-keypass", "ephemeral-lab-only", "-alias", "test",
                 "-keyalg", "RSA", "-keysize", "2048", "-validity", "1",
                 "-dname", "CN=CELIKOM Synthetic APK Test, O=CELIKOM, C=XX"],
                "SYNTHETIC_KEY_CREATION_FAILED")
        fingerprints = []
        for api in (21, 28):
            signed, cert = build_and_sign(tools, android_jar, work, api, key)
            fingerprints.append(cert)
            tampered = work / ("tampered-" + str(api) + ".apk")
            tamper_synthetic_copy(signed, tampered)
            check = subprocess.run([tools["apksigner"], "verify", str(tampered)],
                                   capture_output=True, text=True, timeout=60,
                                   errors="replace", check=False)
            if check.returncode == 0:
                raise SyntheticSignerFailure("SYNTHETIC_TAMPERING_UNDETECTED")
        if len(set(fingerprints)) != 1:
            raise SyntheticSignerFailure("SYNTHETIC_SIGNER_FINGERPRINT_DRIFT")
    return {
        "verdict": "OFFICIAL_SDK_35_SYNTHETIC_SIGNING_CONTROLS_PASS",
        "build_tools": SDK_VERSION,
        "official_sdk_tools_not_symlinks": True,
        "owned_apk_minsdk_21_signed_and_verified": True,
        "owned_apk_minsdk_28_signed_and_verified": True,
        "tampered_synthetic_apks_rejected": 2,
        "owned_disposable_key_used": True,
        "publisher_original_read_or_modified": False,
        "vendor_apk_used_as_synthetic_control": False,
        "files_uploaded": False,
        "product_stage_a": "NO_GO",
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run_controls(), sort_keys=True))
    except (SyntheticSignerFailure, OSError, ValueError, subprocess.TimeoutExpired) as failure:
        reason = str(failure)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{5,96}", reason):
            reason = "SYNTHETIC_SIGNER_PRIVATE_FAILURE"
        print(json.dumps({"verdict": "SYNTHETIC_SIGNER_CONTROLS_FAILED",
                          "reason": reason, "publisher_original_modified": False,
                          "stage_a": "NO_GO"}, sort_keys=True))
        raise SystemExit(2)
