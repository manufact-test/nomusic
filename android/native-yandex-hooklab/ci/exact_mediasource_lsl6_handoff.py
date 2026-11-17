#!/usr/bin/env python3
"""Bounded read-only signed NAV17 Yandex LiLb.a -> LlLb -> LIr8 MediaSource handoff.

The interface LSl6 and its subtype LIr8 are inspected only because the prior
exact signed Exo factory audit identified LIr8 as a concrete source candidate.
Does not establish active selection, runtime dispatch or a decoder binding.
No account, metadata values, URL, audio or private fields read.
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
from exo_factory_exact_consumer import class_metadata

audit = trusted.audit
NATIVE_SOURCE_IFACE = "LSl6;"
NATIVE_SOURCE_BASE = "LdC0;"
NATIVE_SOURCE_CLASS = "LIr8;"
FACTORY_ADAPTER = (
    "LlLb;", "if", "(LdA9;LQAa;LOf6;LgA9;)LIr8;"
)
PUBLISHER_SOURCE_CONSTRUCTOR = (
    "LIr8;", "<init>", "(LOf6;LCC2$a;LlC2;LPF3;LNP5;ILSr4;)V"
)
NATIVE_SOURCE_GET_ITEM = ("LIr8;", "for", "()LOf6;")
COROUTINE_ENTRY = (
    "LiLb$a;", "invokeSuspend", "(Ljava/lang/Object;)Ljava/lang/Object;"
)
EXACT_TARGETS = frozenset({
    FACTORY_ADAPTER, PUBLISHER_SOURCE_CONSTRUCTOR,
    NATIVE_SOURCE_GET_ITEM, COROUTINE_ENTRY,
})
PLAYER_OWNERS = frozenset({
    "LfH7;", "LsO7;", "LBs4;", "LrD0;", "LA14;", "Lp24;",
    "Lwq2;", "Landroidx/media3/exoplayer/ExoPlayer;",
})
ROOT_TYPES = frozenset({
    NATIVE_SOURCE_IFACE, NATIVE_SOURCE_BASE, NATIVE_SOURCE_CLASS,
    "LlLb;", "LiLb;", "LiLb$a;",
})
MAX_TYPED_REFS = 1400
MAX_CALLSITES = 600
MAX_OUTPUT_TARGETS = 72
MAX_METHODS_IN_CLASS = 96


def source_typed_method(method):
    owner, _name, signature = method
    return (
        owner == NATIVE_SOURCE_IFACE
        or NATIVE_SOURCE_IFACE in audit.parse_types(signature)
        or signature.split(")", 1)[1] == NATIVE_SOURCE_IFACE
    )


def inspect_signed(apks):
    dexes, profiles, declared, typed_refs, definitions = [], {}, {}, set(), {}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("LSL6_SIGNED_DEX_SIZE_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for owner in ROOT_TYPES:
                    meta = class_metadata(dex, owner)
                    if meta["defined"]:
                        if owner in profiles:
                            raise ValueError("LSL6_DUPLICATE_EXACT_CLASS")
                        profiles[owner] = meta
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if source_typed_method(method):
                        typed_refs.add(method)
                        if len(typed_refs) > MAX_TYPED_REFS:
                            raise ValueError("LSL6_TYPED_METHOD_REFERENCES_LIMIT")
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    if method in EXACT_TARGETS:
                        if method in definitions:
                            raise ValueError("LSL6_DUPLICATE_EXACT_METHOD")
                        definitions[method] = (dex, flags, code_off)
                    if method[0] in (NATIVE_SOURCE_IFACE, NATIVE_SOURCE_BASE, NATIVE_SOURCE_CLASS):
                        rows = declared.setdefault(method[0], [])
                        if len(rows) >= MAX_METHODS_IN_CLASS:
                            raise ValueError("LSL6_DECLARED_CLASS_METHOD_LIMIT")
                        rows.append({
                            "method": method[1], "signature": method[2],
                            "abstract": not bool(code_off),
                        })

    if len(dexes) != 6:
        raise ValueError("LSL6_EXPECTED_SIX_SIGNED_DEX")
    if NATIVE_SOURCE_IFACE not in profiles or NATIVE_SOURCE_CLASS not in profiles:
        raise ValueError("LSL6_EXACT_CLASS_NOT_FOUND")
    if FACTORY_ADAPTER not in definitions or PUBLISHER_SOURCE_CONSTRUCTOR not in definitions:
        raise ValueError("LSL6_EXACT_FACTORY_PRODUCER_NOT_DEFINED")

    # Concrete ancestry, not semantic names: LIr8 -> LdC0 implements LSl6.
    base = profiles.get(NATIVE_SOURCE_BASE, {})
    concrete = profiles.get(NATIVE_SOURCE_CLASS, {})
    source_subtype_direct_static = (
        concrete.get("superclass") == NATIVE_SOURCE_BASE
        and NATIVE_SOURCE_IFACE in base.get("interfaces", [])
    )
    source_player_contracts = [
        {"owner": x[0], "method": x[1], "signature": x[2]}
        for x in sorted(typed_refs) if x[0] in PLAYER_OWNERS
    ]
    source_typed_reference_owner_counts = {}
    for x in typed_refs:
        source_typed_reference_owner_counts[x[0]] = (
            source_typed_reference_owner_counts.get(x[0], 0) + 1
        )
    sites, count, typed_count, typed_sites = [], 0, 0, []
    for dex in dexes:
        for caller, _flags, code_off in audit.method_definitions_with_flags(dex):
            for ordinal, op, words in audit.instructions(dex, code_off):
                if op not in audit.INVOKES or not 0x6E <= op <= 0x78:
                    continue
                callee = dex.method(words[1])
                if callee in EXACT_TARGETS:
                    count += 1
                    if count > MAX_CALLSITES:
                        raise ValueError("LSL6_EXACT_CALLSITE_LIMIT")
                    if len(sites) < MAX_OUTPUT_TARGETS:
                        sites.append({
                            "caller_owner": caller[0], "caller_method": caller[1],
                            "caller_signature": caller[2],
                            "callee_owner": callee[0], "callee_method": callee[1],
                            "callee_signature": callee[2],
                            "ordinal": ordinal, "invoke_opcode": op,
                        })
                elif callee in typed_refs:
                    typed_count += 1
                    if typed_count > 2000:
                        raise ValueError("LSL6_TYPED_CALLSITE_LIMIT")
                    if (caller[0] in PLAYER_OWNERS or caller[0] in ROOT_TYPES) and len(typed_sites) < 56:
                        typed_sites.append({
                            "caller_owner": caller[0], "caller_method": caller[1],
                            "caller_signature": caller[2],
                            "callee_owner": callee[0], "callee_method": callee[1],
                            "callee_signature": callee[2], "ordinal": ordinal,
                        })

    traces = []
    for target in (FACTORY_ADAPTER, COROUTINE_ENTRY,
                   PUBLISHER_SOURCE_CONSTRUCTOR, NATIVE_SOURCE_GET_ITEM):
        info = definitions.get(target)
        if info is None or not info[2]:
            traces.append({
                "owner": target[0], "method": target[1],
                "body_found": False,
            })
            continue
        dex, flags, code_off = info
        try:
            trace = audit.trace_identity_method(
                dex, target, flags, code_off,
                extra_identity_types=(
                    "LIr8;", "LSl6;", "LOf6;", "LOr2$a;", "LCC2$a;",
                    "LQAa;", "LlLb;",
                ),
                capture_argument_provenance_targets={
                    FACTORY_ADAPTER, PUBLISHER_SOURCE_CONSTRUCTOR,
                },
                track_fields_from_any_receiver=True,
            )
            events = [
                ev for ev in trace.get("events", ())
                if ev.get("kind") == "CALL_ARGUMENT_PROVENANCE"
                and (ev["callee"]["owner"], ev["callee"]["method"],
                     ev["callee"]["signature"])
                in (FACTORY_ADAPTER, PUBLISHER_SOURCE_CONSTRUCTOR)
                or (
                    ev.get("kind") in {
                        "MOVE_RESULT_TYPED_IDENTITY", "FIELD_READ_TYPED_IDENTITY",
                        "FIELD_STORE_TYPED_IDENTITY", "RETURN_TYPED_IDENTITY",
                        "CALL_WITH_TYPED_IDENTITY"
                    } and any(
                        k in str(ev) for k in ("EXTRA_OBJECT:LIr8;",
                            "EXTRA_OBJECT:LOr2$a;", "EXTRA_OBJECT:LCC2$a;",
                            "EXTRA_OBJECT:LSl6;", "EXTRA_OBJECT:LOf6;")
                    )
                )
            ]
            traces.append({
                "owner": target[0], "method": target[1], "body_found": True,
                "branch_seen_aliases_cleared": trace.get("branch_seen_aliases_cleared"),
                "events": events[:40], "events_truncated": len(events)>40,
            })
        except (ValueError, audit.DexError) as err:
            safe = str(err)
            traces.append({
                "owner": target[0], "method": target[1], "body_found": True,
                "trace_complete": False,
                "safe_error": safe if re.fullmatch("[A-Z0-9_]{1,80}", safe) else None,
            })

    return {
        "verdict": "EXACT_MEDIASOURCE_SUBTYPE_AND_PRODUCER_CANDIDATE_ONLY",
        "signed_dex_count": len(dexes),
        "class_profiles": profiles,
        "LIr8_to_LdC0_to_LSl6_type_ancestry_proven": source_subtype_direct_static,
        "source_interface_and_concrete_methods": declared,
        "source_interface_typed_reference_count": len(typed_refs),
        "source_interface_reference_owners": [
            {"owner": owner, "method_references": n}
            for owner, n in sorted(source_typed_reference_owner_counts.items())
        ][:90],
        "source_interface_reference_owners_truncated":
            len(source_typed_reference_owner_counts)>90,
        "known_player_source_typed_contracts": source_player_contracts[:80],
        "known_player_source_typed_contracts_truncated": len(source_player_contracts)>80,
        "exact_target_direct_call_count": count,
        "exact_target_direct_callsites": sites,
        "exact_target_direct_calls_truncated": count>len(sites),
        "typed_interface_method_direct_call_count": typed_count,
        "source_side_or_known_player_typed_callsites": typed_sites,
        "exact_method_identity_traces": traces,
        "active_playback_source_instance_or_decoder_proven": False,
        "native_selected_track_album_edition_duration_generation_proven": False,
        "replacement_audio_connected_or_audible": False,
        "private_values_url_or_audio_read": False,
    }


def run(path: Path):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not path.is_file() or path.stat().st_size != trusted.PINNED_XAPK_BYTES:
        raise ValueError("LSL6_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(path) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("LSL6_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-lsl6-source-readonly-") as tmp:
        apks = audit.unbundle_candidate(path, Path(tmp))
        if len(apks) != 16:
            raise ValueError("LSL6_SIGNED_SPLIT_COUNT_MISMATCH")
        result = audit.verify_split_set(apks)
        if result.get("verified_issuer_signed_splits") != 16:
            raise ValueError("LSL6_ISSUER_SIGNATURE_MISMATCH")
        bases=[]
        for apk in apks:
            m=trusted.package_metadata(apk)
            if (m.get("name") != trusted.EXPECTED_PACKAGE
                    or m.get("versionCode") != trusted.EXPECTED_VERSION_CODE):
                raise ValueError("LSL6_ORIGINAL_PACKAGE_MISMATCH")
            if not m.get("split"):
                bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("LSL6_NAV17_ORIGINAL_BASE_SHA_MISMATCH")
        report=inspect_signed(apks)
    return {**report,"exact_signed_NAV17_verified":True,"read_only_ephemeral":True}


if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("--xapk",type=Path,required=True)
    a=args.parse_args()
    try:
        print(json.dumps(run(a.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as exc:
        e=str(exc)
        print(json.dumps({"verdict":"EXACT_SOURCE_LSL6_AUDIT_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "safe_error_code":e if re.fullmatch("[A-Z0-9_]{1,80}",e) else None,
            "replacement_audio_connected_or_audible":False}))
        raise SystemExit(2)
