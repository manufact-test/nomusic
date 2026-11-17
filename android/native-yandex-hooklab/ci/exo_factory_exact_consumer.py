#!/usr/bin/env python3
"""NAV17 signed 2025 read-only bounded consumer audit of exact Exo factory.

Counts exact invoke sites of Yandex download2.exo.c.for and typed uses of its
LOr2$a return. This is a *static* factory-consumer locator, not active playback
or same-object proof. It never reads private values, media, data specs or audio.
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

EXO_FACTORY = ("Lcom/yandex/music/shared/player/download2/exo/c;", "for",
               "(LdA9;LQAa;Lmu3;LgA9;)LOr2$a;")
SOURCE_FACTORY_INTERFACE = "LOr2$a;"
SOURCE_INSTANCE_INTERFACE = "LCC2;"
RDS_FACTORY = (
    "Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource$b;",
    "for", "()LCC2;",
)
MAX_TYPED_REFERENCES = 192
MAX_EXACT_FACTORY_CALLS = 48
MAX_REFERENCE_CALLS = 128
MAX_CALLERS_REPORTED = 56
MAX_CLASS_METHODS = 64


def related_method(method):
    """Only exact factory/typed interface contract; no inferred signatures."""
    owner, _name, signature = method
    params = audit.parse_types(signature)
    result = signature.split(")", 1)[1]
    return (
        method == EXO_FACTORY or method == RDS_FACTORY
        or owner == SOURCE_FACTORY_INTERFACE
        or SOURCE_FACTORY_INTERFACE in params
        or result == SOURCE_FACTORY_INTERFACE
    )


def class_metadata(dex, cls):
    for i in range(dex.class_count):
        pos = dex.class_offset + 32 * i
        name = dex.descriptor(dex.u32(pos))
        if name == cls:
            sup_idx = dex.u32(pos + 8)
            parent = None if sup_idx == 0xFFFFFFFF else dex.descriptor(sup_idx)
            off = dex.u32(pos + 12)
            interfaces = []
            if off:
                count = dex.u32(off)
                if count > 64:
                    raise ValueError("EXO_FACTORY_INTERFACE_ANCESTRY_LIMIT")
                interfaces = [dex.descriptor(dex.u16(off + 4 + 2 * j)) for j in range(count)]
            return {"defined": True, "superclass": parent, "interfaces": interfaces,
                    "access_flags": dex.u32(pos + 4)}
    return {"defined": False}


def scan_signed(apks):
    dexes = []
    profile = {}
    typed_methods = set()
    defined = set()
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("EXO_FACTORY_DEX_SIZE_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for cls in (
                    SOURCE_FACTORY_INTERFACE, SOURCE_INSTANCE_INTERFACE,
                    EXO_FACTORY[0], RDS_FACTORY[0],
                ):
                    meta = class_metadata(dex, cls)
                    if meta["defined"]:
                        if cls in defined:
                            raise ValueError("EXO_FACTORY_DUPLICATE_CLASS")
                        defined.add(cls)
                        profile[cls] = meta
                for i in range(dex.method_count):
                    method = dex.method(i)
                    if related_method(method):
                        typed_methods.add(method)
                        if len(typed_methods) > MAX_TYPED_REFERENCES:
                            raise ValueError("EXO_FACTORY_TYPED_REFERENCE_LIMIT")

    if len(dexes) != 6:
        raise ValueError("EXPECTED_EXACT_SIX_SIGNED_DEX")
    if EXO_FACTORY not in typed_methods:
        raise ValueError("EXPECTED_EXO_FACTORY_REFERENCE_ABSENT")
    if RDS_FACTORY not in typed_methods:
        raise ValueError("EXPECTED_RDS_FACTORY_REFERENCE_ABSENT")

    direct_sites = []
    typed_sites = []
    exact_count = 0
    rds_count = 0
    typed_count = 0
    for dex in dexes:
        for caller, _flags, code_off in audit.method_definitions_with_flags(dex):
            for ordinal, op, words in audit.instructions(dex, code_off):
                if op not in audit.INVOKES or not 0x6E <= op <= 0x78:
                    continue
                callee = dex.method(words[1])
                if callee == EXO_FACTORY or callee == RDS_FACTORY:
                    if callee == EXO_FACTORY:
                        exact_count += 1
                    else:
                        rds_count += 1
                    if exact_count + rds_count > MAX_EXACT_FACTORY_CALLS:
                        raise ValueError("EXO_FACTORY_EXACT_CALL_LIMIT")
                    direct_sites.append({
                        "caller_owner": caller[0], "caller_method": caller[1],
                        "caller_signature": caller[2],
                        "ordinal": ordinal, "callee_kind": (
                            "EXO_FACTORY" if callee == EXO_FACTORY else "RDS_FACTORY"),
                        "invoke_opcode": op,
                    })
                elif callee in typed_methods:
                    typed_count += 1
                    if typed_count > MAX_REFERENCE_CALLS:
                        raise ValueError("EXO_FACTORY_TYPED_CALL_LIMIT")
                    if len(typed_sites) < MAX_CALLERS_REPORTED:
                        typed_sites.append({
                            "caller_owner": caller[0], "caller_method": caller[1],
                            "caller_signature": caller[2],
                            "ordinal": ordinal, "callee_owner": callee[0],
                            "callee_method": callee[1],
                            "callee_signature": callee[2],
                        })

    # The returned factory or same typed formal parameter is a candidate
    # only: do NOT infer runtime object selection from a method ref.
    return {
        "verdict": "SIGNED_EXO_FACTORY_TYPED_CONSUMER_CANDIDATES_ONLY",
        "six_signed_dex": len(dexes),
        "exact_factory_defined": EXO_FACTORY[0] in defined,
        "source_factory_interface_defined": SOURCE_FACTORY_INTERFACE in defined,
        "source_instance_interface_defined": SOURCE_INSTANCE_INTERFACE in defined,
        "source_factory_interface_profile": profile.get(SOURCE_FACTORY_INTERFACE),
        "source_instance_interface_profile": profile.get(SOURCE_INSTANCE_INTERFACE),
        "source_factory_direct_callsites": exact_count,
        "retrying_datasource_factory_direct_callsites": rds_count,
        "typed_factory_related_method_refs": len(typed_methods),
        "typed_factory_related_direct_callsites": typed_count,
        "exact_factory_calls": direct_sites,
        "typed_method_references": [
            {"owner": m[0], "method": m[1], "signature": m[2]}
            for m in sorted(typed_methods)[:MAX_TYPED_REFERENCES]
        ],
        "typed_callsites": typed_sites,
        "typed_callsites_truncated": typed_count > len(typed_sites),
        "runtime_dispatch_or_same_return_object_to_player_proven": False,
        "active_selected_track_or_decoder_proven": False,
        "stage_b_replacement_or_audio_proven": False,
        "private_values_ids_urls_tokens_or_audio_read": False,
    }



LG_LB_BUILD = ("LgLb;", "for", "()V")
LL_LB_ADAPT = ("LlLb;", "if", "(LdA9;LQAa;LOf6;LgA9;)LIr8;")
AS2_CONSTRUCTOR = ("Las2;", "<init>", "(LOf6;LOr2$a;)V")
EXACT_DIRECT_TARGETS = frozenset({LG_LB_BUILD, LL_LB_ADAPT, AS2_CONSTRUCTOR})


def inspect_exact_source_adapter(apks):
    """One already-grounded Exo->Las2/LIr8 junction and exact callers only."""
    target_defs = {}
    class_profiles = {}
    direct_calls = []
    call_count = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                dex = audit.Dex(archive.read(entry.filename))
                for cls in ("LgLb;", "LlLb;", "Las2;", "LIr8;"):
                    metadata = class_metadata(dex, cls)
                    if metadata["defined"]:
                        if cls in class_profiles:
                            raise ValueError("EXO_ADAPTER_CLASS_DUPLICATE")
                        class_profiles[cls] = metadata
                for method, flags, code_off in audit.method_definitions_with_flags(dex):
                    if method in EXACT_DIRECT_TARGETS:
                        if method in target_defs:
                            raise ValueError("EXO_ADAPTER_METHOD_DUPLICATE")
                        target_defs[method] = (dex, flags, code_off)
                    for ordinal, op, words in audit.instructions(dex, code_off):
                        if op not in audit.INVOKES or not 0x6E <= op <= 0x78:
                            continue
                        callee = dex.method(words[1])
                        if callee not in EXACT_DIRECT_TARGETS:
                            continue
                        call_count += 1
                        if call_count > 80:
                            raise ValueError("EXO_ADAPTER_CALLSITE_LIMIT")
                        if len(direct_calls) < 48:
                            direct_calls.append({
                                "caller_owner": method[0], "caller_method": method[1],
                                "caller_signature": method[2],
                                "callee_owner": callee[0], "callee_method": callee[1],
                                "callee_signature": callee[2], "ordinal": ordinal,
                                "invoke_opcode": op,
                            })
    focused_traces = []
    for target in (LG_LB_BUILD, LL_LB_ADAPT, AS2_CONSTRUCTOR):
        row = target_defs.get(target)
        if row is None:
            focused_traces.append({
                "owner": target[0], "method": target[1],
                "body_found": False,
            })
            continue
        dex, flags, code_off = row
        if not code_off:
            focused_traces.append({
                "owner": target[0], "method": target[1],
                "body_found": False,
            })
            continue
        try:
            trace = audit.trace_identity_method(
                dex, target, flags, code_off,
                extra_identity_types=("LOr2$a;", "LOf6;", "Las2;", "LQAa;"),
                capture_argument_provenance_targets={
                    EXO_FACTORY, AS2_CONSTRUCTOR,
                },
                track_fields_from_any_receiver=True,
            )
            selected_events = [
                ev for ev in trace.get("events", ())
                if (
                    ev.get("kind") == "CALL_ARGUMENT_PROVENANCE"
                    and (ev["callee"]["owner"], ev["callee"]["method"],
                         ev["callee"]["signature"])
                    in {EXO_FACTORY, AS2_CONSTRUCTOR}
                ) or (
                    ev.get("kind") in {
                        "MOVE_RESULT_TYPED_IDENTITY", "FIELD_STORE_TYPED_IDENTITY",
                        "FIELD_READ_TYPED_IDENTITY", "CONSTRUCTOR_TYPED_IDENTITY",
                    }
                    and ("EXTRA_OBJECT:LOr2$a;" in str(ev)
                         or "EXTRA_OBJECT:LOf6;" in str(ev))
                )
            ]
            focused_traces.append({
                "owner": target[0], "method": target[1],
                "body_found": True,
                "branch_seen_aliases_cleared": trace.get(
                    "branch_seen_aliases_cleared"),
                "selected_events": selected_events[:36],
                "selected_events_truncated": len(selected_events) > 36,
            })
        except (audit.DexError, ValueError) as exc:
            code = str(exc)
            focused_traces.append({
                "owner": target[0], "method": target[1],
                "body_found": True, "trace_complete": False,
                "safe_error": code if re.fullmatch("[A-Z0-9_]{1,80}", code) else None,
            })
    return {
        "exact_adapter_class_profiles": class_profiles,
        "exact_adapter_direct_call_count": call_count,
        "exact_adapter_direct_calls": direct_calls,
        "exact_adapter_callers_truncated": call_count > len(direct_calls),
        "exact_adapter_method_traces": focused_traces,
        "runtime_owner_selection_or_decoder_proven": False,
    }

def run(xapk: Path):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != trusted.PINNED_XAPK_BYTES:
        raise ValueError("EXO_FACTORY_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("EXO_FACTORY_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exo-factory-consumer-") as tmp:
        splits = audit.unbundle_candidate(xapk, Path(tmp))
        if len(splits) != 16:
            raise ValueError("EXO_FACTORY_SPLIT_COUNT_MISMATCH")
        signed = audit.verify_split_set(splits)
        if signed.get("verified_issuer_signed_splits") != 16:
            raise ValueError("EXO_FACTORY_ISSUER_SIGNATURE_MISMATCH")
        bases = []
        for apk in splits:
            meta = trusted.package_metadata(apk)
            if (meta.get("name") != trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode") != trusted.EXPECTED_VERSION_CODE):
                raise ValueError("EXO_FACTORY_VERSION_MISMATCH")
            if not meta.get("split"):
                bases.append(apk)
        if len(bases) != 1 or trusted.sha256_file(bases[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("EXO_FACTORY_NAV17_BASE_MISMATCH")
        report = scan_signed(splits)
        adapter_report = inspect_exact_source_adapter(splits)
    return {**report, **adapter_report, "verified_exact_nav17_signed_original": True, "ephemeral_read_only": True}


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--xapk", type=Path, required=True)
    parsed = args.parse_args()
    try:
        print(json.dumps(run(parsed.xapk), ensure_ascii=False, sort_keys=True))
    except (RuntimeError, ValueError, audit.DexError, OSError, zipfile.BadZipFile) as exc:
        code = str(exc)
        print(json.dumps({
            "verdict": "EXO_FACTORY_TYPED_AUDIT_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "safe_error_code": code if re.fullmatch("[A-Z0-9_]{1,80}", code) else None,
            "stage_b_replacement_or_audio_proven": False,
        }))
        raise SystemExit(2)
