"""Pinned Android release identity shared by build, verification and CI.

This file contains public metadata, not any signing secrets.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
PINNED_SIGNER = "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"


def validate_release(data, app_version_source):
    version = data.get("version")
    code = data.get("version_code")
    previous = data.get("previous_rejected_code")
    match = re.fullmatch(r"0\.3\.(\d+)", version if isinstance(version, str) else "")
    if not match or type(code) is not int or type(previous) is not int:
        raise ValueError("Invalid release version metadata")
    if code <= previous or previous != 52 or code != int(match.group(1)) + 1:
        raise ValueError("Release must advance rejected Android version 0.3.51/code 52")
    if data.get("previous_rejected_version") != "0.3.51":
        raise ValueError("Rejected baseline changed")
    if data.get("package") != "pro.celikom.nativeprobe":
        raise ValueError("Unexpected Android package")
    signer = data.get("signing_certificate_sha256")
    if signer != PINNED_SIGNER:
        raise ValueError("Pinned signing identity changed")
    names = re.findall(r'\bNAME\s*=\s*"([^"]+)"', app_version_source)
    if names != [version]:
        raise ValueError("AppVersion.java does not match release metadata")
    return version, code, signer


def load_release(root=ROOT):
    metadata = json.loads((root / "release-spec.json").read_text(encoding="utf-8"))
    java = (root / "addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java").read_text(encoding="utf-8")
    return validate_release(metadata, java)


def patch_apktool_metadata(text, version, code):
    """Update exactly one versionCode and one versionName, preserving line breaks."""
    text, n_code = re.subn(r"(?m)^versionCode: [0-9]+[ \t]*$", "versionCode: " + str(code), text)
    text, n_name = re.subn(r"(?m)^versionName: [^\n]+$", "versionName: " + version, text)
    if n_code != 1 or n_name != 1:
        raise ValueError("Unexpected baseline Apktool version metadata")
    return text
