#!/usr/bin/env python3
"""CI-only, exact signed #170gpr DEX string-ID sort invariant A/B audit.

A fixed-length byte replacement can invalidate Android DEX ordering without
affecting file size, SHA-1 or Adler32. Report ONLY yes/no state, not arbitrary
original DEX strings, URLs, tokens, source contents or APKs.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import clone_native_splits_ephemeral as signed
import clone_native_identity_phase2_ephemeral as clone
from inspect_android_host import Dex


def slot_order(dex_data: bytes, expected: str):
    dex = Dex(dex_data)
    indices = [i for i in range(dex.string_count) if dex.string(i) == expected]
    if len(indices) != 1:
        raise ValueError("EXPECTED_ONE_DEX_STRING_ID")
    i = indices[0]
    if i == 0 or i == dex.string_count - 1:
        raise ValueError("DEX_STRING_NOT_INTERNAL")
    prev, actual, nex = (dex.string(i - 1), dex.string(i), dex.string(i + 1))
    return {
        "found_one": True,
        "previous_le_target": prev <= actual,
        "target_lt_next": actual < nex,
        "slot_order_valid": prev <= actual < nex
    }


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-dex-string-order-") as td:
        root = Path(td)
        archive = root / "pinned.xapk"
        n, digest = signed.gpr.download(archive)
        if n != 60433885 or digest != signed.ARCHIVE_SHA:
            raise ValueError("SIGNED_ORIGINAL_PIN_DRIFT")
        apks = signed.gpr.split_apks(archive, root)
        if len(apks) != 5:
            raise ValueError("ORIGINAL_FIVE_SPLITS_DRIFT")
        signed.gpr.inspect_publisher(apks)
        base = next(p for p in apks if not signed.apkmeta(p).get("split", ""))
        results = []
        with zipfile.ZipFile(base) as z:
            for dex_file in sorted(n for n in z.namelist()
                                   if n.startswith("classes") and n.endswith(".dex")):
                original = z.read(dex_file)
                changed, patched = clone.patch_one_dex(original)
                if not patched:
                    continue
                old_slot = slot_order(original, clone.OLD_METRICA)
                new_slot = slot_order(changed, clone.NEW_METRICA)
                if not old_slot["slot_order_valid"]:
                    raise ValueError("PUBLISHER_STRING_ID_SLOT_INVALID")
                results.append({
                    "dex_file": dex_file,
                    "publisher_string_id_slot_sorted": old_slot["slot_order_valid"],
                    "modified_string_id_slot_sorted": new_slot["slot_order_valid"],
                    "modified_previous_le_target": new_slot["previous_le_target"],
                    "modified_target_lt_next": new_slot["target_lt_next"]
                })
        if len(results) != 1:
            raise ValueError("PATCHED_DEX_COUNT_DRIFT")
        return {
            "verdict": "EXACT_SIGNED_DEX_STRING_ID_ORDER_AUDIT",
            "signed_source": "2026.10.3 #170gpr",
            "five_publisher_signed_splits_verified": True,
            "targeted_patch_occurrences": len(results),
            "dex_string_id_order_invariant": results,
            "raw_dex_or_arbitrary_strings_published": False,
            "user_device_touched": False,
            "runtime_or_audio_tested": False
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"verdict": "DEX_STRING_ID_ORDER_AUDIT_BLOCKED",
                          "stage": type(exc).__name__, "user_device_touched": False}))
        sys.exit(2)
