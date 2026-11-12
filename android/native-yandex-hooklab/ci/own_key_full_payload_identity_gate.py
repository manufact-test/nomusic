"""Read-only content equality of signed original vs separate-key disposable APK.

APK v2/v3 signature block, JAR/v1 signatures, ZIP headers/layout and issuer
certificate are intentionally DIFFERENT. This module proves only that every
other ZIP entry has byte-identical *decompressed content*, and fails closed
on duplicate names, missing entries or a single payload byte mismatch.

It NEVER exports proprietary names, DEX, APKs, paths, hashes or certificate
material to the public GitHub Actions log. Only fixed booleans/counts.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from lab_unsigned_archive_cleanroom import is_v1_signing_artifact

MAX_ENTRIES = 16000
MAX_DECOMPRESSED_BYTES = 900 * 1024 * 1024


def _non_signing_entry_hashes(apk: Path) -> dict[str, bytes]:
    if not apk.is_file() or apk.is_symlink():
        raise ValueError("PAYLOAD_CHECK_APK_MISSING_OR_SYMLINK")
    fingerprints={}
    total=0
    with zipfile.ZipFile(apk,"r") as source:
        entries=source.infolist()
        if len(entries)>MAX_ENTRIES:
            raise ValueError("PAYLOAD_CHECK_EXCESS_ENTRIES")
        all_names=set()
        for item in entries:
            name=item.filename
            if name in all_names:
                raise ValueError("PAYLOAD_CHECK_DUPLICATE_ENTRY")
            all_names.add(name)
            if (item.flag_bits & 0x01) != 0:
                raise ValueError("PAYLOAD_CHECK_ENCRYPTED_ENTRY")
            if name.startswith(("/", "\\")) or ".." in name.split("/"):
                raise ValueError("PAYLOAD_CHECK_UNSAFE_ENTRY_NAME")
            if is_v1_signing_artifact(name):
                continue
            total+=item.file_size
            if total>MAX_DECOMPRESSED_BYTES:
                raise ValueError("PAYLOAD_CHECK_SIZE_BOUND_EXCEEDED")
            fingerprint=hashlib.sha256()
            with source.open(item,"r") as inp:
                for chunk in iter(lambda:inp.read(1 << 20),b""):
                    fingerprint.update(chunk)
            fingerprints[name]=fingerprint.digest()
    return fingerprints


def verify_independent_signature_preserves_payload(
    issuer_signed: Path, own_signed: Path
) -> dict:
    """Reject any unsigned content change; no strings from either APK leak."""
    original=_non_signing_entry_hashes(issuer_signed)
    independently_signed=_non_signing_entry_hashes(own_signed)
    if not original:
        raise ValueError("PAYLOAD_CHECK_NO_ENTRIES")
    if original.keys()!=independently_signed.keys():
        raise ValueError("PAYLOAD_CHECK_ENTRY_SET_CHANGED")
    if any(fingerprint != independently_signed[name]
           for name, fingerprint in original.items()):
        raise ValueError("PAYLOAD_CHECK_ENTRY_CONTENT_CHANGED")
    return {
        "non_signature_zip_entry_payloads_identical":True,
        "non_signature_zip_entries_checked":len(original),
        "file_names_or_hashes_exposed":False,
        "vendor_dex_or_resources_exposed":False,
        "signature_or_zip_metadata_assumed_same":False,
    }
