#!/usr/bin/env python3
"""Reconstruct a disposable *unsigned lab output*, leaving issuer original intact.

Rebuilding an APK can preserve obsolete JAR/v1 META-INF signing artifacts. For
a lab-owned separate-key signing pipeline, an unsigned intermediate must not
carry a stale signer. This scrubs only those artifacts in the ephemeral rebuilt
copy; it does not spoof a publisher signer or alter Android's verification
logic. NEVER apply to or write over verified source APKs.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from lab_signer_signal_gate import probe_apk_zip


def is_v1_signing_artifact(name: str) -> bool:
    upper = name.upper()
    if not upper.startswith("META-INF/") or "/" in upper[len("META-INF/"):]:
        return False
    leaf = upper[len("META-INF/"):]
    return (leaf == "MANIFEST.MF"
            or leaf.endswith((".SF", ".RSA", ".DSA", ".EC"))
            or leaf.startswith("SIG-"))


def remove_stale_v1_from_disposable_unsigned(
    original_unsigned: Path, cleaned_unsigned: Path
) -> dict:
    """Only a new, separate file; byte-identical payload entries or FAIL.

    The caller must use an already rebuilt/renamed lab APK (not the genuine
    publisher-signed original). The canonical lab builder confirms that the
    actual original input was never modified and checks original DEX/.so hashes
    after signing. No signature in itself proves vendor app runtime support.
    """
    source = original_unsigned.resolve()
    target = cleaned_unsigned.resolve()
    if source == target:
        raise ValueError("UNSIGNED_CLEANROOM_SOURCE_DESTINATION_COLLISION")
    if not source.is_file() or source.is_symlink() or target.exists():
        raise ValueError("UNSIGNED_CLEANROOM_INPUT_INVALID")
    first = probe_apk_zip(source)
    if (not first["zip_integrity_ok"] or first["duplicate_entry_names"]
            or first["encrypted_entry_count"] or first["unsafe_entry_name_count"]
            or not first["contains_binary_manifest"]
            or first["entry_count_limit_exceeded"]
            or first["total_unpacked_limit_exceeded"]):
        raise ValueError("UNSIGNED_CLEANROOM_UNSAFE_ARCHIVE")

    hashes_before: dict[str, str] = {}
    stripped = 0
    with zipfile.ZipFile(source, "r") as old, zipfile.ZipFile(
        target, "w", allowZip64=True
    ) as new:
        for info in old.infolist():
            if is_v1_signing_artifact(info.filename):
                stripped += 1
                continue
            payload = old.read(info.filename)
            hashes_before[info.filename] = hashlib.sha256(payload).hexdigest()
            # zipfile reconstitutes central directory; signer owns the fresh
            # v1/v2/v3 structures AFTER alignment, not this staging step.
            new.writestr(info, payload)

    after = probe_apk_zip(target)
    if (not after["zip_integrity_ok"] or after["duplicate_entry_names"]
            or after["encrypted_entry_count"] or after["unsafe_entry_name_count"]
            or after["v1_signature_marker_count"]
            or after["v1_manifest_marker_count"]
            or not after["contains_binary_manifest"]):
        raise ValueError("UNSIGNED_CLEANROOM_REBUILT_ARCHIVE_INVALID")
    with zipfile.ZipFile(target, "r") as new:
        hashes_after = {
            info.filename: hashlib.sha256(new.read(info.filename)).hexdigest()
            for info in new.infolist()
        }
    if hashes_before != hashes_after:
        raise ValueError("UNSIGNED_CLEANROOM_NON_SIGNATURE_PAYLOAD_DRIFT")
    return {
        "discarded_obsolete_v1_entries": stripped,
        "all_other_entry_bytes_preserved": True,
        "clean_unsigned_zip_integrity_ok": True,
        "original_source_untouched": True,
        "issuer_certificate_spoofed": False,
        "signature_verification_bypassed": False,
    }
