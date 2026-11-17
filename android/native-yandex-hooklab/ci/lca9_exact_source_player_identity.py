#!/usr/bin/env python3
"""One exact signed NAV17 2025 LcA9 source->Player same-object CFG witness.

Only LcA9.extends() source construction and the exact LiLb constructor /
LA14.e(LSl6,J) setter are in scope. Branch-sensitive object identity with a
unique LiLb allocation is required; type similarity alone cannot pass.
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

audit=trusted.audit
TARGET=("LcA9;","extends",
  "(LcA9;LA14;LtCa;Ljava/lang/Long;JJZLn26;Lnk0;Ljava/lang/String;)V")
MEDIA_SOURCE_CONSTRUCTOR=(
  "LiLb;","<init>","(LdA9;LgA9;LJI7;LOf6;LFq1;LHy9$a;LPAa;)V")
PLAYER_SOURCE_SETTER=("LA14;","e","(LSl6;J)V")
WRAPPER_SOURCE=("Lbq0;","this",
  "(LtCa;Lnk0;JJZLn26;Ljava/lang/String;)LmLb;")
SCOPE=frozenset({MEDIA_SOURCE_CONSTRUCTOR,PLAYER_SOURCE_SETTER,WRAPPER_SOURCE})
LABELS={
    "LiLb;":"MEDIA_SOURCE_HOLDER",
    "LOf6;":"MEDIA_ITEM",
    "LmLb;":"URI_DESCRIPTOR",
    "LSl6;":"MEDIA_SOURCE_INTERFACE",
    "LA14;":"PLAYER_HOLDER",
}


def target_event(events, callee):
    return [
        e for e in events
        if e.get("kind")=="CALL_WITH_TYPED_IDENTITY"
        and (e["callee"]["owner"],e["callee"]["method"],e["callee"]["signature"])==callee
        and e.get("identity_is_common_to_all_incoming_paths") is True
    ]


def has_identity(event,label,origin):
    return any(
        x.get("identity_type")==label and origin in x.get("origins",())
        for x in event.get("identity_arguments",())
    )


def evaluate_identity(events, unique_holder_allocation):
    constructors=target_event(events,MEDIA_SOURCE_CONSTRUCTOR)
    setters=target_event(events,PLAYER_SOURCE_SETTER)
    wrappers=target_event(events,WRAPPER_SOURCE)
    ctor=unique_holder_allocation and any(
        has_identity(e,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE")
        for e in constructors
    )
    player=unique_holder_allocation and any(
        has_identity(e,"MEDIA_SOURCE_HOLDER","MEDIA_SOURCE_HOLDER_NEW_INSTANCE")
        for e in setters
    )
    wrapper=any(
        has_identity(e,"TRACK_WRAPPER","TRACK_WRAPPER_PARAMETER")
        for e in wrappers
    )
    return {
        "same_allocated_LiLb_to_constructor_proven":bool(ctor),
        "same_allocated_LiLb_to_player_source_setter_proven":bool(player),
        "same_LiLb_instance_constructor_to_player_setter_proven":bool(ctor and player),
        "caller_TrackWrapper_to_descriptor_same_object_proven":bool(wrapper),
        "full_current_selected_track_album_edition_generation_proven":False,
        "audible_decoder_source_proven":False,
    }


def scan_signed(splits):
    found=None
    dex_count=0
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("LCA9_DEX_SIZE_LIMIT")
                dex_count+=1
                dex=audit.Dex(archive.read(entry.filename))
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if method==TARGET:
                        if found:
                            raise ValueError("LCA9_DUPLICATE_EXACT_TARGET")
                        found=(dex,flags,code_off)
    if dex_count!=6:raise ValueError("LCA9_EXPECTED_SIX_SIGNED_DEX")
    if not found or not found[2]:
        raise ValueError("LCA9_EXACT_METHOD_NOT_DEFINED")
    dex,flags,code_off=found
    counts={m:0 for m in SCOPE}
    allocations=[]
    for pc,op,words in audit.instructions(dex,code_off):
        if op==0x22 and dex.descriptor(words[1])=="LiLb;":
            allocations.append(pc)
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            callee=dex.method(words[1])
            if callee in counts:counts[callee]+=1
    if counts[MEDIA_SOURCE_CONSTRUCTOR]!=1 or counts[PLAYER_SOURCE_SETTER]!=1:
        raise ValueError("LCA9_EXACT_CALLSITE_SHAPE_MISMATCH")

    try:
        trace=audit.trace_track_identity_method_cfg(
            dex,TARGET,flags,code_off,extra_identity_types=LABELS,
        )
    except (ValueError,audit.DexError) as err:
        safe=str(err)
        return {
            "verdict":"LCA9_CFG_IDENTITY_NOT_COMPLETE",
            "trace_complete":False,
            "error_class_only":type(err).__name__,
            "safe_error":safe if re.fullmatch("[A-Z0-9_]{1,80}",safe) else None,
            "selected_active_source_proven":False,
        }
    selected=[
        row for row in trace["events"]
        if (row.get("callee",{}).get("owner"),
            row.get("callee",{}).get("method"),
            row.get("callee",{}).get("signature")) in SCOPE
    ]
    proven=evaluate_identity(selected,len(allocations)==1)
    return {
        "verdict":(
            "LCA9_ONE_NATIVE_PLAYER_SOURCE_SAME_OBJECT_STATIC_PROVEN"
            if proven["same_LiLb_instance_constructor_to_player_setter_proven"]
            else "LCA9_PLAYER_SOURCE_SAME_OBJECT_UNPROVEN"
        ),
        "signed_dex_count":dex_count,
        "trace_complete":True,
        "branch_sensitive":True,
        "processed_path_states":trace.get("processed_state_count"),
        "branch_count":trace.get("branch_count"),
        "exact_LiLb_new_instance_count":len(allocations),
        "source_constructor_call_count":counts[MEDIA_SOURCE_CONSTRUCTOR],
        "player_source_setter_call_count":counts[PLAYER_SOURCE_SETTER],
        "wrapper_descriptor_call_count":counts[WRAPPER_SOURCE],
        "exact_evidence":selected[:18],
        "evidence_truncated":len(selected)>18,
        **proven,
        "runtime_selection_and_source_to_decoder_proven":False,
        "replacement_audio_connected_or_audible":False,
        "private_values_urls_media_or_tokens_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("LCA9_PINNED_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("LCA9_PINNED_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-lca9-source-readonly-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:
            raise ValueError("LCA9_SIGNED_SPLIT_COUNT_MISMATCH")
        signer=audit.verify_split_set(splits)
        if signer.get("verified_issuer_signed_splits")!=16:
            raise ValueError("LCA9_ISSUER_SIGNER_MISMATCH")
        bases=[]
        for apk in splits:
            m=trusted.package_metadata(apk)
            if (m.get("name")!=trusted.EXPECTED_PACKAGE or
                m.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("LCA9_ORIGINAL_PACKAGE_VERSION_MISMATCH")
            if not m.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("LCA9_NAV17_ORIGIN_SHA_MISMATCH")
        report=scan_signed(splits)
    return {**report,"exact_publisher_signed_NAV17_verified":True,"ephemeral_read_only":True}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        print(json.dumps(run(args.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({
            "verdict":"LCA9_EXACT_SOURCE_PLAYER_INSPECTION_INCOMPLETE",
            "error_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "replacement_audio_connected_or_audible":False,
        }))
        raise SystemExit(2)
