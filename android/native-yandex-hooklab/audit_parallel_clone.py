#!/usr/bin/env python3
"""Exact signed GPR parallel-install feasibility audit (read-only).

This is NOT a clone generator. It inspects manifest/package identity and
code-string dependency *counts* only, without exposing third-party code,
strings, URLs, tokens, file paths, or any APK. No install/patch/signing happens.
A static-only check never certifies a repackage for distribution or install.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
import audit_gpr_apkpure_once as gpr
from audit_rustore_host_once import RUSTORE_SHA256_CERT, sdk_tool
from inspect_android_host import Dex, DEX_MAX

ORIGINAL = "ru.yandex.music"
CODE = "24026531"
VERSION = "2026.10.3 #170gpr"
EXPECTED_SPLITS = 5
LIMIT_MANIFEST_OUTPUT = 4 * 1024 * 1024
MAX_DEX_STRING_ITEMS = 1_000_000


def manifest_summary(xmltree: str) -> dict:
    """Summarize original identity surfaces by *role*, not total package mentions.

    Class names may retain ru.yandex.music after a legitimate applicationId
    change: unlike ContentProvider authorities they are not by themselves
    installation collisions. Never reveal actual values.
    """
    counts = {k: 0 for k in (
        "activities", "services", "receivers", "providers", "provider_authorities",
        "original_package_provider_authorities", "package_bound_manifest_attributes",
        "original_package_class_name_attributes",
        "original_package_permission_attributes",
        "original_package_routing_attributes",
        "original_package_root_identity_attributes",
        "original_package_other_attributes",
        "custom_permissions", "queries", "intent_filters", "custom_schemes",
        "shared_user_id_attributes",
    )}
    current = ""
    for raw in xmltree.splitlines():
        line = raw.strip()
        element = re.match(r"E: ([a-zA-Z0-9_.-]+)(?:\s|$)", line)
        if element:
            current = element.group(1)
            names = {"activity": "activities", "service": "services",
                     "receiver": "receivers", "provider": "providers",
                     "permission": "custom_permissions", "queries": "queries",
                     "intent-filter": "intent_filters"}
            if current in names:
                counts[names[current]] += 1
        attr = re.match(r"A: ([a-zA-Z0-9_.:-]+)(?:\([^)]*\))?=", line)
        if not attr:
            continue
        key = attr.group(1)
        matched = re.search(r'="([^"]*)"', line)
        val = matched.group(1) if matched else ""
        if key.endswith(":authorities") and current == "provider":
            counts["provider_authorities"] += 1
            if ORIGINAL in val:
                counts["original_package_provider_authorities"] += 1
        if key.endswith(":scheme") and val:
            counts["custom_schemes"] += 1
        if key.endswith(":sharedUserId"):
            counts["shared_user_id_attributes"] += 1
        if ORIGINAL not in val:
            continue
        counts["package_bound_manifest_attributes"] += 1
        if key == "package":
            counts["original_package_root_identity_attributes"] += 1
        elif key.endswith(":authorities") or key.endswith(":name") and current in (
                "activity", "service", "receiver", "provider", "activity-alias",
                "application", "instrumentation"):
            if key.endswith(":name"):
                counts["original_package_class_name_attributes"] += 1
            else:
                counts["original_package_routing_attributes"] += 1
        elif (key.endswith(":permission") or key.endswith(":readPermission")
              or key.endswith(":writePermission") or current in (
                  "permission", "uses-permission", "permission-group",
                  "permission-tree")):
            counts["original_package_permission_attributes"] += 1
        elif key.endswith((":targetPackage", ":targetProcesses", ":process",
                           ":taskAffinity", ":scheme", ":host")):
            counts["original_package_routing_attributes"] += 1
        else:
            counts["original_package_other_attributes"] += 1
    role_sum = sum(counts[k] for k in (
        "original_package_class_name_attributes",
        "original_package_permission_attributes",
        "original_package_routing_attributes",
        "original_package_root_identity_attributes",
        "original_package_other_attributes",
    ))
    if role_sum != counts["package_bound_manifest_attributes"]:
        raise ValueError("MANIFEST_ROLE_CLASSIFICATION_INCOMPLETE")
    return counts

def count_dex_package_dependencies(raw: bytes) -> dict:
    """Bounded DEX parse, exact package literal/reference statistics only."""
    d = Dex(raw)
    if d.string_count > MAX_DEX_STRING_ITEMS:
        raise ValueError("DEX_STRING_TABLE_TOO_LARGE")
    counts = {
        "original_package_exact_strings": 0,
        "original_package_substring_strings": 0,
        "original_package_slash_descriptor_strings": 0,
    }
    for i in range(d.string_count):
        value = d.string(i)
        if value == ORIGINAL:
            counts["original_package_exact_strings"] += 1
        elif ORIGINAL in value:
            counts["original_package_substring_strings"] += 1
        if "ru/yandex/music" in value:
            counts["original_package_slash_descriptor_strings"] += 1
    return counts


def summarize_signed_bundle(paths: list[Path], aapt: str, 
                            run_tool=None) -> dict:
    """Never executes the target APK and never emits private manifest values."""
    if run_tool is None:
        run_tool = subprocess.run
    if len(paths) != EXPECTED_SPLITS:
        raise ValueError("EXACT_SPLIT_COUNT_REQUIRED")
    seen = set()
    base = None
    version_names = set()
    for apk in paths:
        # Parse known trusted aapt metadata, not filenames.
        p = run_tool([aapt, "dump", "badging", str(apk)],
                     capture_output=True, text=True, timeout=60)
        if p.returncode:
            raise ValueError("BAD_APK_METADATA")
        row = next((x for x in p.stdout.splitlines() if x.startswith("package:")), "")
        attrs = dict(re.findall(r"(\w+)='([^']*)'", row))
        if attrs.get("name") != ORIGINAL or attrs.get("versionCode") != CODE:
            raise ValueError("WRONG_SIGNED_HOST_IDENTITY")
        version_names.add(attrs.get("versionName"))
        split = attrs.get("split", "")
        if split in seen:
            raise ValueError("DUPLICATE_SPLIT")
        seen.add(split)
        if not split:
            base = apk
    if not base or VERSION not in version_names:
        raise ValueError("EXACT_GPR_BASE_MISSING")
    manifest = run_tool([aapt, "dump", "xmltree", str(base), "AndroidManifest.xml"],
                        capture_output=True, text=True, timeout=60)
    if manifest.returncode or len(manifest.stdout) > LIMIT_MANIFEST_OUTPUT:
        raise ValueError("BASE_MANIFEST_UNAVAILABLE")
    info = manifest_summary(manifest.stdout)
    dex_counts = {key: 0 for key in (
        "original_package_exact_strings",
        "original_package_substring_strings",
        "original_package_slash_descriptor_strings",
    )}
    dex_files = 0
    with zipfile.ZipFile(base) as z:
        for entry in z.infolist():
            if not re.fullmatch(r"classes\d*\.dex", entry.filename):
                continue
            if entry.file_size > DEX_MAX:
                raise ValueError("DEX_TOO_LARGE")
            for key, value in count_dex_package_dependencies(z.read(entry)).items():
                dex_counts[key] += value
            dex_files += 1
    if dex_files == 0:
        raise ValueError("BASE_WITHOUT_DEX")
    blockers = [
        "UNMODIFIED_PACKAGE_ID_COLLIDES_WITH_INSTALLED_YANDEX",
        "PUBLISHER_SIGNING_IDENTITY_UNAVAILABLE_FOR_CUSTOM_CLIENT",
        "CLONE_MODULE_SCOPE_NOT_IMPLEMENTED",
        "CLONE_RUNTIME_LOGIN_AND_PLAY_PROTECT_UNVERIFIED",
    ]
    if info["original_package_provider_authorities"] > 0:
        blockers.append("MANIFEST_PROVIDER_AUTHORITY_REWRITE_REQUIRED")
    if sum(info[k] for k in ("original_package_permission_attributes",
                             "original_package_routing_attributes",
                             "original_package_other_attributes")):
        blockers.append("MANIFEST_NONCLASS_PACKAGE_REFERENCES_REQUIRE_REVIEW")
    if sum(dex_counts.values()) > 0:
        blockers.append("DEX_PACKAGE_IDENTITY_DEPENDENCIES_REVIEW_REQUIRED")
    if info["shared_user_id_attributes"]:
        blockers.append("SHARED_USER_ID_SIGNER_COMPATIBILITY_UNKNOWN")
    return {
        "verdict": "NO_GO_PARALLEL_CLONE_NOT_BUILT",
        "target": ORIGINAL,
        "version": VERSION,
        "version_code": int(CODE),
        "verified_split_count": len(paths),
        "split_ids_verified": len(seen),
        "base_dex_count": dex_files,
        "manifest_counts": info,
        "dex_identity_dependency_counts": dex_counts,
        "blockers": blockers,
        "official_yandex_install_touched": False,
        "modified_apk_created": False,
        "audio_playback_tested": False,
        "play_protect_verified": False,
    }


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="celikom-native-clone-readonly-") as folder:
            root = Path(folder)
            xapk = root / "pinned-gpr.xapk"
            size, digest = gpr.download(xapk)
            # Only previously pinned exact archive may pass.
            if (size != 60433885 or
                digest != "918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84"):
                raise ValueError("PINNED_SOURCE_ARCHIVE_MISMATCH")
            apks = gpr.split_apks(xapk, root)
            gpr.inspect_publisher(apks)
            result = summarize_signed_bundle(apks, sdk_tool("aapt"))
            # Archive, extracted APKs and their metadata are erased on exit.
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError,
            zipfile.BadZipFile) as exc:
        # Do not forward any external error body or file path.
        error = str(exc)
        safe = error if error in {
            "PINNED_SOURCE_ARCHIVE_MISMATCH", "EXACT_SPLIT_COUNT_REQUIRED",
            "BAD_APK_METADATA", "WRONG_SIGNED_HOST_IDENTITY",
            "DUPLICATE_SPLIT", "EXACT_GPR_BASE_MISSING",
            "BASE_MANIFEST_UNAVAILABLE", "DEX_TOO_LARGE", "BASE_WITHOUT_DEX",
            "DEX_STRING_TABLE_TOO_LARGE", "MANIFEST_UNAVAILABLE",
        } else "SOURCE_OR_SDK_UNAVAILABLE"
        print(json.dumps({"verdict": "STATIC_AUDIT_BLOCKED", "reason": safe,
                          "modified_apk_created": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
