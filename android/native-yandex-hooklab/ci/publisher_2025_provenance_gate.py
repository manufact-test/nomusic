#!/usr/bin/env python3
"""Read-only issuer verification of a pristine Yandex Music 2025 RuStore candidate.

NEVER downloads, installs, modifies, repacks or prints candidate APK content.
A claimed 2025 release listing is NOT a validated publisher-signed APK.
No modification of vendor security, Passport/DRM, certificates or Play Protect.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PACKAGE = "ru.yandex.music"
VERSION_CODE = 24025542
VERSION_NAME = "2025.10.4 #120.1rur"
VERSION_NAME_GPR = "2025.10.4 #120.1gpr"
# Cross-checked historical 31 Oct 2025 4PDA #29718 claim: NOT an issuer attestation.
HISTORICAL_BYTES = 59498960
HISTORICAL_MD5 = "710b04ac0cc784f2576710343d4c37c1"
# Independently verified 2026.10.3 #170rur signer from RuStore (same cert
# documented in tools/android-native-gate1/audit_rustore_host_once.py).
KNOWN_ISSUER_CERT = "aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba"
MAX_BYTES = 160 * 1024 * 1024

class GateError(Exception):
    """Only safe, fixed public failure categories."""


def verify_metadata(aapt_text: str, signer_text: str, expected_version: str = VERSION_NAME) -> dict:
    match = re.search(
        r"^package:\s+name='([^']+)'\s+versionCode='([^']+)'\s+versionName='([^']+)'",
        aapt_text, re.MULTILINE)
    if not match:
        raise GateError("BAD_MANIFEST_METADATA")
    package, code, version = match.groups()
    if (package, code, version) != (PACKAGE, str(VERSION_CODE), expected_version):
        raise GateError("WRONG_PACKAGE_OR_VERSION")

    # apksigner exits nonzero on invalid cryptographic signatures. These
    # strings are ADDITIONAL checks, not substitutes for apksigner exit 0.
    matches = re.findall(
        r"Signer #(\d+) certificate SHA-256 digest:\s*([A-Fa-f0-9:]+)",
        signer_text, flags=re.I)
    if not matches or {n for n, _ in matches} != {"1"}:
        raise GateError("SIGNER_SET_NOT_SINGLE_ISSUER")
    cert = {digest.replace(":", "").lower() for _, digest in matches}
    if cert != {KNOWN_ISSUER_CERT}:
        raise GateError("PUBLISHER_CERTIFICATE_MISMATCH")
    scheme = re.findall(
        r"Verified using v([23]) scheme \([^)]*\):\s*(true|false)",
        signer_text, flags=re.I)
    if not any(value.lower() == "true" for _, value in scheme):
        raise GateError("VALID_V2_V3_SIGNING_NOT_CONFIRMED")
    return {
        "publisher_cert_matches_verified_rustore_2026_reference": True,
        "package_exact": True,
        "version_code_exact": True,
        "version_name_exact": True,
        "cryptographic_apksigner_success_required": True,
        "modified_or_resigned_by_celikom": False,
    }


def file_hashes(candidate: Path) -> tuple[int, str, str]:
    if not candidate.is_file() or candidate.is_symlink():
        raise GateError("CANDIDATE_MISSING_OR_NOT_REGULAR")
    length = candidate.stat().st_size
    if not (0 < length <= MAX_BYTES):
        raise GateError("CANDIDATE_SIZE_OUT_OF_BOUNDS")
    sha, md5 = hashlib.sha256(), hashlib.md5(usedforsecurity=False)
    with candidate.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            sha.update(chunk)
            md5.update(chunk)
    if candidate.stat().st_size != length:
        raise GateError("CANDIDATE_CHANGED_DURING_READ")
    return length, sha.hexdigest(), md5.hexdigest()


def private_command(argv: list[str]) -> str:
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=75)
    except (OSError, subprocess.TimeoutExpired):
        raise GateError("ANDROID_SDK_TOOLS_UNAVAILABLE") from None
    if result.returncode:
        raise GateError("ANDROID_SDK_SIGNATURE_OR_METADATA_VERIFICATION_FAILED")
    return result.stdout


def inspect(candidate: Path, aapt: str = "aapt", apksigner: str = "apksigner", channel: str = "rur") -> dict:
    size, sha, md5 = file_hashes(candidate)
    # DO NOT invoke any code from candidate; only established Android SDK parsers.
    signer = private_command([apksigner, "verify", "--verbose", "--print-certs", str(candidate)])
    manifest = private_command([aapt, "dump", "badging", str(candidate)])
    if channel not in ("rur", "gpr"):
        raise GateError("UNSUPPORTED_RELEASE_CHANNEL")
    checked = verify_metadata(manifest, signer,
                              VERSION_NAME if channel == "rur" else VERSION_NAME_GPR)
    historical = channel == "rur" and size == HISTORICAL_BYTES and md5 == HISTORICAL_MD5
    return {
        "verdict": "PUBLISHER_SIGNED_2025_CANDIDATE_VERIFIED",
        **checked,
        "candidate_sha256": sha,
        "verified_2025_release_channel": channel,
        "historical_4pda_bytes_and_md5_match": historical,
        "historical_forum_md5_is_not_publisher_attestation": True,
        "actual_apk_provenance_channel_independently_confirmed": False,
        "installed_or_executed": False,
        "account_audio_drm_play_protect_tested": False,
        "android_stage_a": "NO_GO",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", type=Path, help="local, unmodified original candidate")
    parser.add_argument("--channel", choices=("rur","gpr"), default="rur")
    args = parser.parse_args(argv)
    if args.apk is None:
        print(json.dumps({
            "verdict": "PUBLISHER_SIGNED_2025_SAMPLE_NOT_YET_OBTAINED",
            "candidate_verified": False,
            "native_2025_test_permitted": False,
            "stage_a": "NO_GO",
        }, sort_keys=True))
        return 0
    try:
        result = inspect(args.apk, channel=args.channel)
        print(json.dumps(result, sort_keys=True))
        return 0
    except GateError as error:
        print(json.dumps({
            "verdict": "PUBLISHER_SIGNED_2025_CANDIDATE_REJECTED",
            "reason": str(error), "native_2025_test_permitted": False,
            "stage_a": "NO_GO",
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
