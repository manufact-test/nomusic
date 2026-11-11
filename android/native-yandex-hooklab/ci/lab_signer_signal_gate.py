#!/usr/bin/env python3
"""Read-only, disclosure-bounded APK archive/signature diagnostics.

Only ZIP metadata and subprocess output categories are handled. This module does
not patch any APK, relax signature acceptance, impersonate a publisher, query a
service, or expose original vendor bytes, member names or raw apksigner stderr.
"""
from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

ENTRY_CAP = 100000
UNPACKED_CAP = 512 * 1024 * 1024

# Avoid printing proprietary path/exception strings from apksigner; just stable
# booleans describing what kind of verification failure happened.
_ERROR_PATTERNS = {
    "missing_verified_signature": (r"does not verify", r"no signatures", r"no signers"),
    "sdk_level_rejection": (r"min.sdk", r"max.sdk", r"minimum sdk", r"unsupported sdk"),
    "zip_or_central_directory": (r"central directory", r"zip entry", r"zip exception"),
    "signing_block_corruption": (r"apk signing block", r"signing block"),
    "v1_jar_problem": (r"jar signature", r"jarsigner", r"v1 signature"),
    "v2_scheme_problem": (r"v2 signature", r"v2 scheme", r"apk signature scheme v2"),
    "v3_scheme_problem": (r"v3 signature", r"v3 scheme", r"apk signature scheme v3"),
    "entry_digest_problem": (r"digest mismatch", r"digest of", r"failed to verify digest"),
    "certificate_or_signer": (r"certificate", r"certificates", r"signer"),
    "unsigned_entry": (r"unsigned entry", r"not signed", r"unsigned apk"),
    "manifest_parse_problem": (r"manifest", r"binary xml"),
}

def classify_apksigner_failure(returncode: int, stdout: str, stderr: str) -> dict:
    """A nonzero exit is never treated as valid, irrespective of message text."""
    if returncode == 0:
        return {"apksigner_exit_zero": True, "failure_categories": []}
    # Never return, log, or preserve the sensitive raw text supplied to this.
    combined = (stdout + "\n" + stderr).lower()[:262144]
    found = sorted(name for name, fragments in _ERROR_PATTERNS.items()
                   if any(re.search(pattern, combined) for pattern in fragments))
    return {
        "apksigner_exit_zero": False,
        "failure_categories": found or ["unclassified"],
    }

def probe_apk_zip(path: Path) -> dict:
    """Bounded read-only integrity/metadata scan; no ZIP member names disclosed.

    Detects stale signing metadata and ambiguous archives independently of Android
    SDK. Stale v1 metadata is a *hypothesis only*, not proof of verification cause.
    """
    summary = {
        "zip_opened": False,
        "zip_integrity_ok": False,
        "entry_count": 0,
        "duplicate_entry_names": False,
        "unsafe_entry_name_count": 0,
        "encrypted_entry_count": 0,
        "v1_signature_marker_count": 0,
        "v1_manifest_marker_count": 0,
        "contains_binary_manifest": False,
        "total_unpacked_limit_exceeded": False,
        "entry_count_limit_exceeded": False,
    }
    try:
        with zipfile.ZipFile(path, "r") as archive:
            summary["zip_opened"] = True
            items = archive.infolist()
            summary["entry_count"] = len(items)
            if len(items) > ENTRY_CAP:
                summary["entry_count_limit_exceeded"] = True
                return summary
            counts = Counter(info.filename for info in items)
            summary["duplicate_entry_names"] = any(v > 1 for v in counts.values())
            for info in items:
                name = info.filename
                pieces = name.replace("\\", "/").split("/")
                summary["unsafe_entry_name_count"] += int(
                    name.startswith("/") or any(x in (".", "..") for x in pieces))
                summary["encrypted_entry_count"] += int(bool(info.flag_bits & 1))
                upper = name.upper()
                in_meta = upper.startswith("META-INF/") and "/" not in upper[9:]
                summary["v1_signature_marker_count"] += int(
                    in_meta and upper.endswith((".RSA", ".DSA", ".EC", ".SF")))
                summary["v1_manifest_marker_count"] += int(
                    upper == "META-INF/MANIFEST.MF")
                if name == "AndroidManifest.xml":
                    summary["contains_binary_manifest"] = True
            total = sum(i.file_size for i in items)
            if total > UNPACKED_CAP:
                summary["total_unpacked_limit_exceeded"] = True
                return summary
            if summary["encrypted_entry_count"]:
                return summary
            # CRC check reads ZIP data; it never executes any archive payload.
            summary["zip_integrity_ok"] = archive.testzip() is None
    except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return summary
    return summary

def safe_report(source_before: dict, source_after: dict, code: int,
                stdout: str, stderr: str, split_index: int) -> dict:
    signed = classify_apksigner_failure(code, stdout, stderr)
    return {
        "lab_split_index": split_index,
        "unsigned_archive_probe": source_before,
        "signed_archive_probe": source_after,
        "signature_verification": signed,
        "vendor_raw_apk_content_logged": False,
        "signed_clone_accepted_without_sdk_verification": False,
    }
