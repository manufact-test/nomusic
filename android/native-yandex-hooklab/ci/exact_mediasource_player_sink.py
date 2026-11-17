#!/usr/bin/env python3
"""Bounded signed NAV17 source-to-Player source-setter identity audit.

The exact LIr8 -> LdC0 -> LSl6 lineage and LiLb$a -> LWT1.strictfp source
handoff are verified by the predecessor CI; inspect only actual known
LSl6-typed Player source mutators and direct callsites in the same signed DEX.
No global List/Object tracing or unpinned obfuscated-name exploration.
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
audit=trusted.audit

SOURCE="LSl6;"
PLAYER_METHODS=frozenset(
    (owner,name,sig)
    for owner in (
        "LA14;", "Lp24;", "Landroidx/media3/exoplayer/ExoPlayer;"
    )
    for name,sig in (
        ("T","(LSl6;)V"),
        ("e","(LSl6;J)V"),
    )
)
COMPOSITE_ADD=("LWT1;","strictfp","(Ljava/lang/Object;LSl6;)V")
COMPOSITE_CREATE=("LiLb;","<init>","(LdA9;LgA9;LJI7;LOf6;LFq1;LHy9$a;LPAa;)V")
SOURCE_CANDIDATE_FACT=("LlLb;","if","(LdA9;LQAa;LOf6;LgA9;)LIr8;")
EXACT_TARGETS=PLAYER_METHODS|{COMPOSITE_ADD}
KNOWN_CLASSES=frozenset({
    "LSl6;", "LWT1;", "LiLb;", "LIr8;", "LdC0;", "LA14;",
    "Lp24;", "Landroidx/media3/exoplayer/ExoPlayer;",
    "LsO7;", "LBs4;", "LrD0;", "LcA9;", "Lwq2;",
})
MAX_CALLS=192
MAX_TRACE=16


def is_exact_mutator(method):
    return method in PLAYER_METHODS


def scan_signed(apks):
    dexes=[]
    profiles={}
    definitions={}
    calls=[]
    call_count=0
    target_counts={target:0 for target in EXACT_TARGETS}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("SOURCE_SINK_SIGNED_DEX_SIZE_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for owner in KNOWN_CLASSES:
                    meta=class_metadata(dex,owner)
                    if meta.get("defined"):
                        if owner in profiles:raise ValueError("SOURCE_SINK_DUPLICATE_CLASS")
                        profiles[owner]=meta
    if len(dexes)!=6:
        raise ValueError("SOURCE_SINK_EXPECTED_SIX_DEX")
    for dex in dexes:
        for caller,flags,code_off in audit.method_definitions_with_flags(dex):
            if caller in EXACT_TARGETS or caller in (COMPOSITE_CREATE,SOURCE_CANDIDATE_FACT):
                if caller in definitions:raise ValueError("SOURCE_SINK_DUPLICATE_METHOD")
                definitions[caller]=(dex,flags,code_off)
            for ordinal,op,words in audit.instructions(dex,code_off):
                if op not in audit.INVOKES or not 0x6E<=op<=0x78:
                    continue
                callee=dex.method(words[1])
                if callee not in EXACT_TARGETS:
                    continue
                target_counts[callee]+=1
                call_count+=1
                if call_count>MAX_CALLS:
                    raise ValueError("SOURCE_SINK_CALLSITE_LIMIT")
                calls.append({
                    "caller_owner":caller[0],"caller_method":caller[1],
                    "caller_signature":caller[2],"ordinal":ordinal,
                    "callee_owner":callee[0],"callee_method":callee[1],
                    "callee_signature":callee[2],"invoke_opcode":op,
                })
    traces=[]
    trace_refs=set()
    # Trace the exact caller only, never continue through generic collection
    # or decoder. We keep a bounded number of caller bodies and report
    # incomplete provenance as incomplete.
    for row in calls:
        key=(row["caller_owner"],row["caller_method"],row["caller_signature"])
        if key in trace_refs or len(trace_refs)>=MAX_TRACE:
            continue
        if row["callee_owner"]=="LWT1;" or row["callee_owner"] in (
            "LA14;","Lp24;","Landroidx/media3/exoplayer/ExoPlayer;"
        ):
            # Find this specific defining method (previously screened call).
            found=None
            for dex in dexes:
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if method==key:
                        found=(dex,flags,code_off)
                        break
                if found:break
            if not found:continue
            trace_refs.add(key)
            dex,flags,code_off=found
            try:
                result=audit.trace_identity_method(
                    dex,key,flags,code_off,
                    extra_identity_types=(
                        "LSl6;","LIr8;","LiLb;","LWT1;","LOf6;","LgLb;"
                    ),
                    capture_argument_provenance_targets=EXACT_TARGETS,
                    track_fields_from_any_receiver=True,
                )
                trace_events=[
                    ev for ev in result.get("events",())
                    if (ev.get("kind")=="CALL_ARGUMENT_PROVENANCE"
                        and (ev["callee"]["owner"],ev["callee"]["method"],
                             ev["callee"]["signature"]) in EXACT_TARGETS)
                ]
                traces.append({
                    "caller_owner":key[0],"caller_method":key[1],
                    "caller_signature":key[2],
                    "method_trace_complete":True,
                    "branch_seen_aliases_cleared":result.get("branch_seen_aliases_cleared"),
                    "setter_argument_provenance":trace_events[:24],
                    "truncated":len(trace_events)>24,
                })
            except (ValueError,audit.DexError) as e:
                safe=str(e)
                traces.append({
                    "caller_owner":key[0],"caller_method":key[1],
                    "method_trace_complete":False,
                    "safe_error":safe if re.fullmatch("[A-Z0-9_]{1,80}",safe) else None,
                })
    profile_li=profiles.get("LiLb;",{})
    profile_super=profiles.get("LWT1;",{})
    actual_source_super=profiles.get("LdC0;",{})
    return {
        "verdict":"EXACT_PLAYER_SOURCE_SETTER_DIRECT_CALLS_ONLY_NOT_SELECTED",
        "signed_dex_count":len(dexes),
        "LIr8_to_LdC0_to_LSl6_static":(
            profiles.get("LIr8;",{}).get("superclass")=="LdC0;"
            and SOURCE in actual_source_super.get("interfaces",())
        ),
        "LiLb_to_LWT1_static":profile_li.get("superclass")=="LWT1;",
        "LWT1_class_profile":profile_super,
        "Player_source_method_reference_count":len(PLAYER_METHODS),
        "source_mutator_call_count":sum(
            n for target,n in target_counts.items() if is_exact_mutator(target)
        ),
        "composite_child_add_call_count":target_counts[COMPOSITE_ADD],
        "individual_target_counts":[
            {"target_owner":a,"target_method":b,"target_signature":c,"call_count":n}
            for (a,b,c),n in sorted(target_counts.items())
        ],
        "exact_direct_calls":calls[:MAX_CALLS],
        "direct_callers_truncated":call_count>len(calls),
        "scoped_same_method_provenance":traces,
        "scoped_traces_skipped_due_to_limit":len({
            (c["caller_owner"],c["caller_method"],c["caller_signature"])
            for c in calls
        })>MAX_TRACE,
        "runtime_player_receiver_selected_source_proven":False,
        "same_selected_track_album_edition_generation_to_decoder_proven":False,
        "audio_replacement_connected":False,
        "private_values_ids_urls_or_audio_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("SOURCE_SINK_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("SOURCE_SINK_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-source-sink-readonly-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("SOURCE_SINK_16_SPLITS_REQUIRED")
        signer=audit.verify_split_set(splits)
        if signer.get("verified_issuer_signed_splits")!=16:
            raise ValueError("SOURCE_SINK_SIGNER_MISMATCH")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE
                or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("SOURCE_SINK_PACKAGE_VERSION_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("SOURCE_SINK_NAV17_BASE_MISMATCH")
        report=scan_signed(splits)
    return {**report,"signed_NAV17_original_verified":True,"read_only_ephemeral":True}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        print(json.dumps(run(args.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({
            "verdict":"SOURCE_SINK_DIRECT_AUDIT_INCOMPLETE",
            "safe_error":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "audio_replacement_connected":False,
        }))
        raise SystemExit(2)
