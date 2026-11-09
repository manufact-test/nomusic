#!/usr/bin/env python3
"""Stage exact publisher-signed Yandex Android APK splits for clean AVD baseline.

Only disposable isolated CI, no user device, credentials, audio or accounts.
All original APK copies removed after the AVD test; never an Actions artifact.
"""
from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
import audit_gpr_apkpure_once as gpr

def main():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("Original APK staging restricted to ephemeral CI")
    runner_temp=Path(os.environ["RUNNER_TEMP"]).resolve()
    destination=Path(os.environ["CELIKOM_EMULATOR_TEST_DIR"]).resolve()
    if destination==runner_temp or runner_temp not in destination.parents or destination.exists():
        raise ValueError("Invalid original host staging path")
    with tempfile.TemporaryDirectory(prefix="celikom-baseline-validation-") as folder:
        scratch=Path(folder)
        archive=scratch/"exact-original.xapk"
        size,digest=gpr.download(archive)
        parts=gpr.split_apks(archive,scratch)
        if len(parts)!=5:
            raise ValueError("Unexpected publisher XAPK split count")
        gpr.inspect_publisher(parts)
        destination.mkdir(mode=0o700,parents=True)
        for i,part in enumerate(parts):
            shutil.copyfile(part,destination/f"native-split-{i}.apk")
        print("ORIGINAL_BASELINE_STAGED: exact signed #170gpr; 5 parts; no modification")
        print("ORIGINAL_HOST_SHA256: "+digest)
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print("ORIGINAL_BASELINE_BLOCKED: "+type(exc).__name__,file=sys.stderr)
        raise SystemExit(2)
