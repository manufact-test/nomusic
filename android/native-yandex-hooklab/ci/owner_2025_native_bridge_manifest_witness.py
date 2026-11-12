#!/usr/bin/env python3
"""Read-only Android 13 cross-UID activity embedding and public media IPC gate.

Uses the EXISTING publisher-verified 2025.10.4 #120.1gpr 16-APK source.
Nothing is modified, installed, launched, transmitted or written to artifacts.
Only aggregate framework API facts are printed. An IPC surface is not proof of
a source-before-decoder integration or of a usable CELIKOM clone.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from owner_2025_gpr_arm13_signed_control import prepare
from publisher_2025_provenance_gate import GateError, private_command

MEDIA_SERVICE_ACTIONS = frozenset({
    "android.media.browse.MediaBrowserService",
    "androidx.media3.session.MediaSessionService",
    "androidx.media3.session.MediaLibraryService",
})
COMPONENTS = {"application", "activity", "activity-alias", "service"}
ENTRY = re.compile(r"^( *)E: ([A-Za-z][A-Za-z0-9_.-]*)\b")
ATTRIBUTE = re.compile(r"^ *A: android:([A-Za-z][A-Za-z0-9_]*)\b")
QUOTED = re.compile(r'="([^"]*)"')


def boolean_attribute(raw: str) -> bool | None:
    match = QUOTED.search(raw)
    if match and match.group(1).lower() in ("true", "false"):
        return match.group(1).lower() == "true"
    if "(type 0x12)0xffffffff" in raw:
        return True
    if "(type 0x12)0x0" in raw or "(type 0x12)0x00000000" in raw:
        return False
    return None


def inspect_tree(xmltree: str) -> dict:
    if not xmltree or len(xmltree) > 2_000_000:
        raise ValueError("BOUNDED_MANIFEST_REQUIRED")
    stack: list[tuple[int, str, dict | None]] = []
    app: dict | None = None
    activities: list[dict] = []
    services: list[dict] = []
    for line in xmltree.splitlines():
        element = ENTRY.match(line)
        if element:
            indent = len(element.group(1))
            tag = element.group(2)
            while stack and stack[-1][0] >= indent:
                stack.pop()
            record = None
            if tag in COMPONENTS:
                record = {
                    "exported": None, "enabled": True,
                    "untrusted": None, "known": False, "actions": set(),
                }
                if tag == "application":
                    if app is not None:
                        raise ValueError("MULTIPLE_APPLICATIONS")
                    app = record
                elif tag in ("activity", "activity-alias"):
                    activities.append(record)
                elif tag == "service":
                    services.append(record)
            stack.append((indent, tag, record))
            continue
        attr = ATTRIBUTE.match(line)
        if not attr or not stack:
            continue
        key = attr.group(1)
        tag, record = stack[-1][1:]
        if record is not None:
            if key == "exported":
                record["exported"] = boolean_attribute(line)
            elif key == "enabled":
                record["enabled"] = boolean_attribute(line) is not False
            elif key == "allowUntrustedActivityEmbedding":
                record["untrusted"] = boolean_attribute(line)
            elif key == "knownActivityEmbeddingCerts":
                # A resource/string reference is an allowlist, NOT CELIKOM's cert.
                record["known"] = True
        if tag == "action" and key == "name":
            match = QUOTED.search(line)
            if match and match.group(1) in MEDIA_SERVICE_ACTIONS:
                for _, ancestor, owner in reversed(stack[:-1]):
                    if ancestor == "service" and owner is not None:
                        owner["actions"].add(match.group(1))
                        break
    if app is None or not activities:
        raise ValueError("APPLICATION_OR_ACTIVITY_NOT_OBSERVED")
    def effective_approval(record: dict, attr: str) -> bool:
        return bool(record[attr] if record[attr] is not None else app[attr])
    public_activities = [
        x for x in activities if x["enabled"] and app["enabled"]
        and x["exported"] is True
    ]
    public_media = [
        x for x in services if x["enabled"] and app["enabled"]
        and x["exported"] is True and x["actions"]
    ]
    return {
        "activity_count": len(activities),
        "manifest_exported_enabled_activity_count": len(public_activities),
        "cross_uid_untrusted_embeddable_exported_activity_count": sum(
            effective_approval(x, "untrusted") for x in public_activities),
        "cross_uid_known_signer_cert_allowlisted_exported_activity_count": sum(
            effective_approval(x, "known") for x in public_activities),
        "public_media_browser_service_count": sum(
            "android.media.browse.MediaBrowserService" in x["actions"]
            for x in public_media),
        "public_media3_session_service_count": sum(
            "androidx.media3.session.MediaSessionService" in x["actions"]
            for x in public_media),
        "public_media3_library_service_count": sum(
            "androidx.media3.session.MediaLibraryService" in x["actions"]
            for x in public_media),
        "manifest_parsed": True,
        "trust_attributes_respected": True,
        "media_session_runtime_commands_observed": False,
        "native_audio_source_replace_callback_proven": False,
        "third_party_private_metadata_emitted": False,
    }


def run(xapk: Path) -> dict:
    parts = prepare(xapk)  # Immutable XAPK SHA256, publisher signature 16/16, exact GPR version.
    bases = [part for name, part in parts if name == "base"]
    if len(parts) != 16 or len(bases) != 1:
        raise ValueError("SIGNED_2025_BASE_SPLIT_INVALID")
    xmltree = private_command(["aapt", "dump", "xmltree",
                              str(bases[0]), "AndroidManifest.xml"])
    info = inspect_tree(xmltree)
    has_open_embedded_ui = info["cross_uid_untrusted_embeddable_exported_activity_count"] > 0
    # Known signing cert allowlists cannot be treated as accepting our unrelated cert.
    info.update({
        "verdict": ("PUBLIC_CROSS_UID_EMBEDDING_CANDIDATE_REQUIRES_LIVE_PROOF"
                    if has_open_embedded_ui
                    else "NO_PUBLIC_CROSS_UID_EMBEDDING_OPT_IN_OBSERVED"),
        "original_2025_gpr_pinned_and_all_16_issuer_signatures_verified": True,
        "original_apk_modified": False, "original_apk_installed": False,
        "media_session_arbitrary_source_support_not_inferable": True,
        "publisher_signature_or_drm_bypass_attempted": False,
        "original_apk_published_or_uploaded": False,
        "stage_a": "NO_GO", "stage_b": "LOCKED",
    })
    return info


def parser_selftest() -> None:
    simple = """E: manifest
  E: application
    A: android:allowUntrustedActivityEmbedding=(type 0x12)0x0
    E: activity
      A: android:exported=(type 0x12)0xffffffff
      A: android:allowUntrustedActivityEmbedding=(type 0x12)0x0
    E: activity
      A: android:exported=(type 0x12)0xffffffff
      A: android:knownActivityEmbeddingCerts=@0x7f110001
    E: service
      A: android:exported=(type 0x12)0xffffffff
      E: intent-filter
        E: action
          A: android:name="android.media.browse.MediaBrowserService"
"""
    out = inspect_tree(simple)
    assert out["cross_uid_untrusted_embeddable_exported_activity_count"] == 0
    assert out["cross_uid_known_signer_cert_allowlisted_exported_activity_count"] == 1
    assert out["public_media_browser_service_count"] == 1
    allowed = simple.replace(
        "A: android:allowUntrustedActivityEmbedding=(type 0x12)0x0\n    E: activity",
        "A: android:allowUntrustedActivityEmbedding=(type 0x12)0xffffffff\n    E: activity", 1)
    assert inspect_tree(allowed)["cross_uid_untrusted_embeddable_exported_activity_count"] == 1
    print('{"parser_safety_check":"PASS_NOT_PRODUCT_EVIDENCE"}')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--xapk", type=Path)
    ap.add_argument("--parser-selftest", action="store_true")
    ns = ap.parse_args()
    try:
        if ns.parser_selftest:
            parser_selftest()
        elif ns.xapk:
            print(json.dumps(run(ns.xapk), sort_keys=True))
        else:
            ap.error("--xapk or --parser-selftest required")
    except (ValueError, GateError, OSError) as exc:
        reason = str(exc) if isinstance(exc, (ValueError, GateError)) else "SOURCE_ACCESS_ERROR"
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,85}", reason):
            reason = "PINNED_ORIGINAL_MANIFEST_NOT_VERIFIED"
        print(json.dumps({"verdict":"INCONCLUSIVE", "reason":reason,
                          "stage_a":"NO_GO", "raw_vendor_data_exposed":False}))
        sys.exit(2)
