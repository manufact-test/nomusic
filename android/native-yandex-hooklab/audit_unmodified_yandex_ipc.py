#!/usr/bin/env python3
"""Read-only manifest IPC feasibility gate for unmodified signed Yandex #170gpr.

Counts exported Android components and observable media entrypoints; never
invokes them, reads tokens, patches APKs, or exposes provider authorities/URLs.
A public component is NOT proof of an audio source replacement contract.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import audit_parallel_clone as clone

COMPONENTS = ("activity", "activity-alias", "service", "receiver", "provider")
MEDIA_ACTIONS = {
    "android.media.browse.MediaBrowserService",
    "android.media.action.MEDIA_PLAY_FROM_SEARCH",
    "android.intent.action.MEDIA_SEARCH",
    "android.intent.action.VIEW",
    "android.intent.action.SEND",
    "android.intent.action.SEND_MULTIPLE",
}
# Numbers and names below are aggregate metadata only, never account values.

def element_indent(line):
    return len(line) - len(line.lstrip())

def collect_components(xmltree: str) -> dict:
    comp = []
    current = None
    filter_depth = None
    for line in xmltree.splitlines():
        trim = line.strip()
        indent = element_indent(line)
        element = re.match(r"E: ([a-zA-Z0-9_.-]+)(?:\s|$)", trim)
        if element:
            tag = element.group(1)
            if current and indent <= current["_depth"]:
                comp.append(current)
                current = None
                filter_depth = None
            if tag in COMPONENTS:
                current = {
                    "kind": tag, "exported": "unknown", "permission": False,
                    "read_write_permission": False, "provider_grant": False,
                    "intent_filters": 0, "media_intents": set(),
                    "_depth": indent,
                }
                filter_depth = None
            elif current and tag == "intent-filter":
                current["intent_filters"] += 1
                filter_depth = indent
            elif current and filter_depth is not None and indent <= filter_depth:
                filter_depth = None
            continue
        if not current:
            continue
        match = re.match(r'A: ([a-zA-Z0-9_.:-]+)(?:\([^)]*\))?=', trim)
        if not match:
            continue
        key = match.group(1)
        qm = re.search(r'="([^"]*)"', trim)
        value = qm.group(1) if qm else ""
        # aapt dump xmltree boolean attrs often serialize as "(type 0x12)0xffffffff"
        is_true = value.lower() == "true" or ("(type 0x12)" in trim and trim.endswith("0xffffffff"))
        is_false = value.lower() == "false" or ("(type 0x12)" in trim and trim.endswith("0x0"))
        if key.endswith(":exported"):
            current["exported"] = "yes" if is_true else ("no" if is_false else "unknown")
        if key.endswith(":permission"):
            current["permission"] = bool(value) or "(type" in trim
        if key.endswith((":readPermission", ":writePermission")):
            current["read_write_permission"] = bool(value) or "(type" in trim
        if key.endswith(":grantUriPermissions"):
            current["provider_grant"] = is_true
        if key.endswith(":name") and filter_depth is not None and value in MEDIA_ACTIONS:
            current["media_intents"].add(value)
    if current:
        comp.append(current)
    totals = {}
    for typ in COMPONENTS:
        group = [x for x in comp if x["kind"] == typ]
        totals[typ] = {
            "total": len(group),
            "exported_true": sum(x["exported"] == "yes" for x in group),
            "exported_false": sum(x["exported"] == "no" for x in group),
            "exported_unspecified": sum(x["exported"] == "unknown" for x in group),
            "explicit_permission_guard": sum(x["permission"] or x["read_write_permission"] for x in group),
            "intent_filters": sum(x["intent_filters"] for x in group),
            "media_action_declared": sum(bool(x["media_intents"]) for x in group),
        }
        if typ == "provider":
            totals[typ]["grant_uri_permission_true"] = sum(x["provider_grant"] for x in group)
    visible = {action: sum(action in x["media_intents"] for x in comp)
               for action in sorted(MEDIA_ACTIONS)}
    return {
        "component_roles": totals, "media_action_counts": visible,
        "manifest_claim": "COUNT_ONLY_NO_EXTERNAL_AUDIO_REPLACEMENT_PROOF",
        "private_values_emitted": False,
    }

def inspect_exact_host() -> dict:
    with tempfile.TemporaryDirectory(prefix="celikom-unchanged-ipc-") as tmpdir:
        root = Path(tmpdir)
        xapk = root / "signed-source.xapk"
        length, digest = clone.gpr.download(xapk)
        if length != 60433885 or digest != "918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84":
            raise ValueError("PINNED_SOURCE_MISMATCH")
        splits = clone.gpr.split_apks(xapk, root)
        clone.gpr.inspect_publisher(splits)
        aapt = clone.sdk_tool("aapt")
        bases = []
        for file in splits:
            result = subprocess.run([aapt, "dump", "badging", str(file)],
                                    capture_output=True, text=True, timeout=50)
            row = next((s for s in result.stdout.splitlines() if s.startswith("package:")), "")
            attrs = dict(re.findall(r"(\w+)='([^']*)'", row))
            if result.returncode or attrs.get("name") != clone.ORIGINAL or attrs.get("versionCode") != clone.CODE:
                raise ValueError("EXACT_SPLITS_REQUIRED")
            if not attrs.get("split"):
                bases.append(file)
        if len(splits) != 5 or len(bases) != 1:
            raise ValueError("EXACT_SPLITS_REQUIRED")
        tree = subprocess.run([aapt, "dump", "xmltree", str(bases[0]), "AndroidManifest.xml"],
                              capture_output=True, text=True, timeout=60)
        if tree.returncode or len(tree.stdout) > clone.LIMIT_MANIFEST_OUTPUT:
            raise ValueError("MANIFEST_SCAN_BLOCKED")
        summary = collect_components(tree.stdout)
        return {
            "verdict": "NO_UNMODIFIED_NATIVE_SOURCE_REPLACEMENT_CONTRACT_PROVEN",
            "original_signed_host": "#170gpr",
            "five_splits_original_signer_verified": True,
            "external_manifest": summary,
            "manipulated_apk": False,
            "installed_or_launched": False,
            "account_or_media_accessed": False,
            "yandex_decoder_intercept_tested": False,
            "conclusion_limit": "Manifest-only: exported components do not imply replaceable FileInfoDto or decoded audio",
        }

def main() -> int:
    try:
        print(json.dumps(inspect_exact_host(), indent=2, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"verdict":"STATIC_NO_GO","reason":"SIGNED_SOURCE_OR_MANIFEST_UNAVAILABLE",
                          "modified_apk":False}))
        return 2

if __name__ == "__main__":
    sys.exit(main())
