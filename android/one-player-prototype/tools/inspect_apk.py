#!/usr/bin/env python3
"""Read-only APK feasibility inventory; never installs, signs, patches, or uploads APKs."""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

PROBES = {
    "androidx_media3": b"androidx/media3",
    "legacy_exoplayer": b"com/google/android/exoplayer2",
    "media_player": b"android/media/MediaPlayer",
    "media_session": b"MediaSession",
    "progressive_media_source": b"ProgressiveMediaSource",
    "dash_media_source": b"DashMediaSource",
    "data_source_factory": b"DataSource$Factory",
}
MAX_DEX_BYTES = 200 * 1024 * 1024


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tools_capture(args):
    if not shutil.which(args[0]):
        return None
    result = subprocess.run(args, text=True, capture_output=True,
                            timeout=25, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def inspect(path):
    report = {
        "apk_sha256": sha256_file(path),
        "apk_bytes": path.stat().st_size,
        "zip_integrity": "not_checked",
        "dex_entries": [],
        "native_library_abis": [],
        "player_marker_hits": {},
        "package": None,
        "version_name": None,
        "version_code": None,
        "signer_cert_sha256": None,
        "limitations": [
            "DEX string markers are hints, never proof of real player/source selection.",
            "No hooks, patching, credentials, auth requests, or Play Protect test.",
            "Signer reported only if local Android apksigner tool is available.",
        ],
    }
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError("APK ZIP integrity failure")
        report["zip_integrity"] = "ok"
        entries = archive.namelist()
        report["dex_entries"] = [
            name for name in entries if re.fullmatch(r"classes\d*\.dex", name)
        ]
        report["native_library_abis"] = sorted({
            parts[1] for name in entries
            if name.startswith("lib/") and name.endswith(".so")
            for parts in [name.split("/")] if len(parts) == 3
        })
        hits = {name: False for name in PROBES}
        for name in report["dex_entries"]:
            info = archive.getinfo(name)
            if info.file_size > MAX_DEX_BYTES:
                raise ValueError("DEX too large for bounded inspection")
            data = archive.read(name)
            for probe, needle in PROBES.items():
                if needle in data:
                    hits[probe] = True
        report["player_marker_hits"] = hits
    badging = tools_capture(["aapt", "dump", "badging", str(path)])
    if badging:
        match = re.search(r"package: name='([^']+)' versionCode='([^']*)' versionName='([^']*)'", badging)
        if match:
            report["package"], report["version_code"], report["version_name"] = match.groups()
    signing = tools_capture(["apksigner", "verify", "--print-certs", str(path)])
    if signing:
        match = re.search(r"Signer #1 certificate SHA-256 digest: ([0-9a-fA-F:]+)", signing)
        if match:
            report["signer_cert_sha256"] = match.group(1).lower().replace(":", "")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=pathlib.Path)
    parser.add_argument("--expected-package", help="Optional exact package equality gate")
    args = parser.parse_args()
    try:
        report = inspect(args.apk)
        if args.expected_package and report["package"] != args.expected_package:
            report["package_gate"] = "FAIL: package unavailable or differs"
        elif args.expected_package:
            report["package_gate"] = "PASS"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report.get("package_gate", "").startswith("FAIL"):
            return 2
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.TimeoutExpired) as e:
        print("APK inspection failed: " + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
