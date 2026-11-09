#!/usr/bin/env python3
"""Read-only exact #170gpr five-split ABI inventory. No device or APK uploads."""
from __future__ import annotations
import json
import os
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
import clone_native_splits_ephemeral as original


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-original-abi-") as td:
        root = Path(td)
        archive = root / "signed-original.xapk"
        size, digest = original.gpr.download(archive)
        if size != 60433885 or digest != original.ARCHIVE_SHA:
            raise ValueError("SIGNED_ORIGINAL_ARCHIVE_DRIFT")
        apks = original.gpr.split_apks(archive, root)
        if len(apks) != 5:
            raise ValueError("EXACT_FIVE_SPLITS_REQUIRED")
        original.gpr.inspect_publisher(apks)
        splits = []
        all_abis = set()
        for i, apk in enumerate(apks):
            meta = original.apkmeta(apk)
            if meta.get("name") != original.SOURCE or meta.get("versionCode") != "24026531":
                raise ValueError("SPLIT_IDENTITY_MISMATCH")
            abis = Counter()
            with zipfile.ZipFile(apk) as z:
                for filename in z.namelist():
                    parts = filename.split("/")
                    if len(parts) == 3 and parts[0] == "lib" and parts[2].endswith(".so"):
                        abis[parts[1]] += 1
            all_abis.update(abis)
            splits.append({"index": i, "split": meta.get("split", "") or "base",
                           "native_library_count_by_abi": dict(sorted(abis.items()))})
        return {
            "verdict": "ORIGINAL_NATIVE_ABI_STATIC_ONLY",
            "version": "2026.10.3 #170gpr",
            "five_signed_splits_verified": True,
            "supported_native_library_abis": sorted(all_abis),
            "split_inventory": splits,
            "installed_or_executed": False,
            "owner_phone_touched": False,
            "vendor_apk_distributed": False
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"verdict": "ORIGINAL_NATIVE_ABI_AUDIT_BLOCKED",
                          "reason_type": type(exc).__name__,
                          "vendor_apk_distributed": False}))
        sys.exit(2)
