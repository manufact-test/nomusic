"""Inspect an UNSIGNED, NON-INSTALLABLE CELIKOM package.

This is not a release verifier. It deliberately rejects any signed APK and
never prints or accesses signing credentials. Output is explicitly marked unsafe
for installation; the real signed APK MUST pass verify_release.py separately.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
from release_archive import inspect_zip
from release_contract import load_release

ROOT = Path(__file__).resolve().parent


def digest(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("apk", "base-apk", "compiled-dex", "build-tools"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--expected-dex-sha256", required=True)
    args = p.parse_args()
    version, code, signer = load_release()
    inputs = json.loads((ROOT / "build-inputs.json").read_text())
    if not args.apk.name.endswith("-INSPECTION-UNSIGNED.apk") or version not in args.apk.name:
        raise ValueError("Unsafe output filename: inspection must be explicitly UNSIGNED")
    if not re.fullmatch(r"[a-f0-9]{64}", args.expected_dex_sha256):
        raise ValueError("Trusted CI DEX SHA256 must be supplied")
    if digest(args.base_apk) != inputs["base_apk_sha256"]:
        raise ValueError("Baseline APK SHA256 mismatch")
    if digest(args.compiled_dex) != args.expected_dex_sha256:
        raise ValueError("Supplied DEX differs from expected CI artifact SHA256")
    check = subprocess.run(["java", "-jar", str(args.build_tools / "lib/apksigner.jar"),
                            "verify", "--verbose", str(args.apk)],
                           capture_output=True, text=True)
    if check.returncode == 0:
        raise ValueError("Signed APK cannot be classified as unsigned inspection")
    subprocess.run([str(args.build_tools / "zipalign"), "-c", "4", str(args.apk)], check=True)
    badge = subprocess.check_output([str(args.build_tools / "aapt"), "dump", "badging",
                                     str(args.apk)], text=True)
    if ("versionCode='" + str(code) + "'") not in badge or ("versionName='" + version + "'") not in badge:
        raise ValueError("APK version is not the requested inspection candidate")
    if "sdkVersion:'28'" not in badge or "targetSdkVersion:'36'" not in badge:
        raise ValueError("Unexpected SDK constraints")
    if not re.search(r"package: name='pro\.celikom\.nativeprobe'", badge):
        raise ValueError("Unexpected package identity")
    data = inspect_zip(args.apk, args.base_apk, args.compiled_dex)
    result = {
        "status": "UNSIGNED_INSPECTION_ONLY_NOT_INSTALLABLE",
        "version": version, "version_code": code,
        "apk_sha256": digest(args.apk), "ci_dex_sha256": digest(args.compiled_dex),
        "original_assets_unchanged": True,
        "archive_entries": data["archive_entries"], "asset_count": data["asset_count"],
        "signing_verified": False, "signed_release": False,
        "physical_phone_playback_verified": False,
    }
    path = args.apk.with_suffix(".inspection.json")
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("PASS: non-installable unsigned APK structure; not a signed release", path)


if __name__ == "__main__":
    main()
