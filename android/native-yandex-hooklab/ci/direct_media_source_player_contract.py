#!/usr/bin/env python3
"""Signed NAV17-2025, read-only check of direct MediaSource-typed Player contracts.

This audit is deliberately narrower than the earlier MediaItem/Player ancestry
search. It checks only exact MediaSource formal parameters on already known
Player interface/implementation owners and their direct invoke callsites.
A positive reference does NOT attest the active/current native source,
selection, Track/Album/edition/duration/generation, or decoder playback.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import lft2_class_inspection as trusted

audit = trusted.audit
SOURCE = "Landroidx/media3/exoplayer/source/MediaSource;"
PLAYER_OWNERS = frozenset({
    "LfH7;", "LsO7;", "LBs4;", "LrD0;", "Lp24;", "LA14;",
    "LDq2;", "Lwq2;", "Landroidx/media3/exoplayer/d;",
    "Landroidx/media3/exoplayer/m;",
    "Landroidx/media3/exoplayer/ExoPlayer;",
})
SOURCE_SIDE_OWNERS = frozenset({
    "Lcom/yandex/music/shared/player/download2/o;",
    "Lcom/yandex/music/shared/player/download2/exo/c;",
    "LcA9;", "LgLb;", "Lwq2;",
})
MAX_TARGET_METHODS = 64
MAX_CALLSITES = 128
MAX_REPORTED_CALLSITES = 32


def direct_contract(method: tuple[str, str, str]) -> bool:
    """Exact descriptor and exact known Player owner; not List/MediaItem."""
    owner, _name, descriptor = method
    return owner in PLAYER_OWNERS and SOURCE in audit.parse_types(descriptor)


def scan_signed(apks: list[Path]) -> dict:
    dexes = []
    dex_count = 0
    source_defined = False
    target_methods = set()
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("DIRECT_SOURCE_DEX_SIZE_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                dex_count += 1
                for index in range(dex.class_count):
                    pos = dex.class_offset + index * 32
                    if dex.descriptor(dex.u32(pos)) == SOURCE:
                        source_defined = True
                for index in range(dex.method_count):
                    method = dex.method(index)
                    if direct_contract(method):
                        target_methods.add(method)
                        if len(target_methods) > MAX_TARGET_METHODS:
                            raise ValueError("DIRECT_SOURCE_CONTRACT_LIMIT")
    if dex_count != 6:
        raise ValueError("DIRECT_SOURCE_EXPECTED_SIX_SIGNED_DEX")
    # No unrelated method/field-value or global list/ByteBuffer tracing.
    sites = []
    count = 0
    source_side_count = 0
    if target_methods:
        for dex in dexes:
            for caller, _flags, code_off in audit.method_definitions_with_flags(dex):
                for ordinal, op, words in audit.instructions(dex, code_off):
                    if op not in audit.INVOKES or not 0x6E <= op <= 0x78:
                        continue
                    callee = dex.method(words[1])
                    if callee not in target_methods:
                        continue
                    count += 1
                    if count > MAX_CALLSITES:
                        raise ValueError("DIRECT_SOURCE_CALLSITE_LIMIT")
                    source_side = caller[0] in SOURCE_SIDE_OWNERS
                    source_side_count += int(source_side)
                    if len(sites) < MAX_REPORTED_CALLSITES:
                        sites.append({
                            "caller_owner": caller[0],
                            "caller_method": caller[1],
                            "caller_signature": caller[2],
                            "ordinal": ordinal,
                            "direct_source_side_owner": source_side,
                            "callee_owner": callee[0],
                            "callee_method": callee[1],
                            "callee_signature": callee[2],
                        })
    return {
        "verdict": (
            "DIRECT_SOURCE_CONTRACT_REFERENCES_ONLY_NOT_ACTIVE_PLAYBACK"
            if target_methods else
            "NO_EXACT_DIRECT_SOURCE_TYPED_PLAYER_CONTRACT_IN_BOUNDED_SCOPE"
        ),
        "signed_dex_count": dex_count,
        "exact_media_source_class_defined": source_defined,
        "exact_player_owner_count": len(PLAYER_OWNERS),
        "exact_direct_media_source_player_contract_count": len(target_methods),
        "direct_source_player_callsite_count": count,
        "source_side_owner_callsite_count": source_side_count,
        "direct_source_player_contracts": [
            {"owner": m[0], "method": m[1], "signature": m[2]}
            for m in sorted(target_methods)
        ],
        "direct_callsites": sites,
        "callsites_truncated": count > len(sites),
        "scope_excludes_obfuscated_or_indirect_source_types": True,
        "static_direct_reference_not_runtime_dispatch": True,
        "selected_track_album_edition_duration_generation_proven": False,
        "active_native_source_to_decoder_proven": False,
        "stage_b_replacement_connected_or_audible": False,
        "field_values_urls_tokens_account_or_audio_read": False,
    }


def run(xapk: Path) -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != trusted.PINNED_XAPK_BYTES:
        raise ValueError("PINNED_2025_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("PINNED_2025_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-direct-source-readonly-") as tmp:
        apks = audit.unbundle_candidate(xapk, Path(tmp))
        if len(apks) != 16:
            raise ValueError("PINNED_2025_SPLIT_COUNT_MISMATCH")
        issuer = audit.verify_split_set(apks)
        if issuer.get("verified_issuer_signed_splits") != 16:
            raise ValueError("PUBLISHER_SIGNATURE_GATE_FAILED")
        base_apks = []
        for apk in apks:
            meta = trusted.package_metadata(apk)
            if (meta.get("name") != trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode") != trusted.EXPECTED_VERSION_CODE):
                raise ValueError("SIGNED_2025_SPLIT_PACKAGE_MISMATCH")
            if not meta.get("split"):
                base_apks.append(apk)
        if len(base_apks) != 1 or trusted.sha256_file(base_apks[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("NAV17_EMBEDDED_ORIGIN_BASE_SHA_MISMATCH")
        result = scan_signed(apks)
    return {
        **result,
        "pinned_origin_and_issuer_verified": True,
        "read_only_and_ephemeral": True,
    }


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--xapk", type=Path, required=True)
    parsed = args.parse_args()
    try:
        print(json.dumps(run(parsed.xapk), ensure_ascii=False, sort_keys=True))
    except (RuntimeError, ValueError, audit.DexError, OSError,
            zipfile.BadZipFile) as exc:
        code = str(exc)
        print(json.dumps({
            "verdict": "DIRECT_SOURCE_AUDIT_INCOMPLETE",
            "error_class": type(exc).__name__,
            "safe_error_code": code if re.fullmatch(r"[A-Z0-9_]{1,80}", code) else None,
            "stage_b_replacement_connected_or_audible": False,
        }))
        raise SystemExit(2)
