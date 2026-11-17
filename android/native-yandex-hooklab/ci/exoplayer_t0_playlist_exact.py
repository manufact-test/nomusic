#!/usr/bin/env python3
"""Read-only exact signed ExoPlayer.d source setter -> T0 playlist admission audit.

Only d.e/d.T/d.T0 are inspected. A source passed to Java singletonList and
then to T0 is not necessarily the currently selected audio MediaPeriod.
No private fields' names or values, URL, tokens or audio are read/exported.
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
OWNER="Landroidx/media3/exoplayer/d;"
SETTERS=frozenset({
    (OWNER,"e","(LSl6;J)V"),(OWNER,"T","(LSl6;)V")
})
COMMIT=(OWNER,"T0","(Ljava/util/List;IJZ)V")
SINGLETON=("Ljava/util/Collections;","singletonList","(Ljava/lang/Object;)Ljava/util/List;")
TARGETS=SETTERS | {COMMIT}
MAX_CALLEES=192
MAX_TARGET_CALLERS=48
MAX_CLASS_FIELDS=120


def exact_targets_only(method):
    return method in TARGETS


def identity_witness(events, singleton, commit):
    src_events=[row for row in events if (
        row.get("kind")=="CALL_WITH_TYPED_IDENTITY"
        and (row.get("callee",{}).get("owner"),row.get("callee",{}).get("method"),
             row.get("callee",{}).get("signature"))==singleton
        and row.get("identity_is_common_to_all_incoming_paths") is True)]
    list_events=[row for row in events if (
        row.get("kind")=="CALL_WITH_TYPED_IDENTITY"
        and (row.get("callee",{}).get("owner"),row.get("callee",{}).get("method"),
             row.get("callee",{}).get("signature"))==commit
        and row.get("identity_is_common_to_all_incoming_paths") is True)]
    source_param=any(any(x.get("identity_type")=="NATIVE_SOURCE"
        and "NATIVE_SOURCE_PARAMETER" in x.get("origins",())
        for x in e.get("identity_arguments",())) for e in src_events)
    list_from_method=any(any(x.get("identity_type")=="EXACT_SOURCE_LIST"
        and "EXACT_SOURCE_LIST_RETURNED_FROM_METHOD" in x.get("origins",())
        for x in e.get("identity_arguments",())) for e in list_events)
    return {
        "source_parameter_to_singletonList":source_param,
        "returned_List_to_exact_T0":list_from_method,
        "one_source_to_T0_list_contract":bool(
            len(src_events)==1 and len(list_events)==1
            and source_param and list_from_method),
        "runtime_active_source_confirmed":False,
    }


def scan_signed(apks):
    dexes=[]
    definitions={}
    target_calls=[]
    method_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("EXOPLAYER_T0_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if exact_targets_only(method):
                        if method in definitions:raise ValueError("EXOPLAYER_T0_DUPLICATE_METHOD")
                        definitions[method]=(dex,flags,code_off)
                    if not code_off:continue
                    for ordinal,op,words in audit.instructions(dex,code_off):
                        if op not in audit.INVOKES or not 0x6E<=op<=0x78:
                            continue
                        callee=dex.method(words[1])
                        if callee in TARGETS:
                            method_count+=1
                            if method_count>MAX_TARGET_CALLERS:
                                raise ValueError("EXOPLAYER_T0_CALLER_LIMIT")
                            target_calls.append({
                                "caller_owner":method[0],"caller_method":method[1],
                                "caller_signature":method[2],"ordinal":ordinal,
                                "target_owner":callee[0],"target_method":callee[1],
                                "target_signature":callee[2],
                            })
    if len(dexes)!=6:raise ValueError("EXOPLAYER_T0_EXPECTED_SIX_DEX")
    if set(definitions)!=TARGETS:
        raise ValueError("EXOPLAYER_T0_EXPECTED_DEFINITIONS_MISSING")
    setter_traces=[]
    for target in sorted(SETTERS):
        dex,flags,code_off=definitions[target]
        calls=[]
        for ordinal,op,words in audit.instructions(dex,code_off):
            if op in audit.INVOKES and 0x6E<=op<=0x78:
                callee=dex.method(words[1])
                calls.append({"ordinal":ordinal,"owner":callee[0],"method":callee[1],
                    "signature":callee[2]})
        if len(calls)>24:raise ValueError("EXOPLAYER_T0_SETTER_CALL_LIMIT")
        try:
            trace=audit.trace_track_identity_method_cfg(
                dex,target,flags,code_off,
                extra_identity_types={
                    "LSl6;":"NATIVE_SOURCE",
                    "Ljava/util/List;":"EXACT_SOURCE_LIST"
                })
            evidence=[
                x for x in trace["events"]
                if x.get("kind") in ("CALL_WITH_TYPED_IDENTITY",
                    "CALL_WITH_POSSIBLE_IDENTITY")
                and (x.get("callee",{}).get("owner"),
                     x.get("callee",{}).get("method"),
                     x.get("callee",{}).get("signature")) in (SINGLETON,COMMIT)
            ]
            witness=identity_witness(trace["events"],SINGLETON,COMMIT)
            complete=True;err=None;states=trace.get("processed_state_count")
        except (ValueError,audit.DexError) as e:
            complete=False
            evidence=[];err=type(e).__name__;states=None
            witness=identity_witness([],SINGLETON,COMMIT)
        setter_traces.append({
            "method":target[1],"calls":calls,
            "branch_cfg_complete":complete,"safe_trace_error":err,
            "processed_path_states":states,
            "exact_transfer_events":evidence[:18],
            **witness,
        })
    dex,flags,code_off=definitions[COMMIT]
    if not code_off:raise ValueError("EXOPLAYER_T0_BODY_MISSING")
    invoked=[]
    source_field_census={}
    reference_count=0
    for ordinal,op,words in audit.instructions(dex,code_off):
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            method=dex.method(words[1])
            reference_count+=1
            if reference_count>MAX_CALLEES:
                raise ValueError("EXOPLAYER_T0_CALLEE_LIMIT")
            invoked.append({
                "ordinal":ordinal,"owner":method[0],
                "method":method[1],"signature":method[2],
                "list_or_source_argument":(
                    "Ljava/util/List;" in audit.parse_types(method[2])
                    or "LSl6;" in audit.parse_types(method[2]))
            })
        if 0x52<=op<=0x6d:
            owner,_name,typ=audit.field_id(dex,words[1])
            if typ in ("Ljava/util/List;","LSl6;") and owner==OWNER:
                source_field_census.setdefault(typ,0)
                source_field_census[typ]+=1
                if sum(source_field_census.values())>MAX_CLASS_FIELDS:
                    raise ValueError("EXOPLAYER_T0_FIELD_LIMIT")
    try:
        targettrace=audit.trace_track_identity_method_cfg(
            dex,COMMIT,flags,code_off,
            extra_identity_types={
                "Ljava/util/List;":"EXACT_SOURCE_LIST","LSl6;":"NATIVE_SOURCE",
            })
        target_events=[
            e for e in targettrace["events"] if (
                any(x.get("identity_type")=="EXACT_SOURCE_LIST"
                    for x in e.get("identity_arguments",())) or
                any(x.get("identity_type")=="EXACT_SOURCE_LIST"
                    for x in e.get("possible_identity_arguments",())) or
                e.get("identity_type")=="EXACT_SOURCE_LIST")
        ]
        target_error=None;target_states=targettrace.get("processed_state_count")
    except (ValueError,audit.DexError) as exc:
        target_events=[];target_error=type(exc).__name__;target_states=None

    return {
        "verdict":"EXOPLAYER_T0_SOURCE_LIST_ADMISSION_CANDIDATE_NOT_AUDIBLE",
        "signed_six_dex":len(dexes),
        "setter_to_singleton_list_to_T0":setter_traces,
        "exact_T0_callsite_count":len(target_calls),
        "T0_and_source_setter_callsites":target_calls,
        "T0_exact_invokes":invoked,
        "T0_owner_list_or_source_field_accesses":source_field_census,
        "T0_cfg_list_alias_events":target_events[:38],
        "T0_cfg_list_alias_events_truncated":len(target_events)>38,
        "T0_cfg_error_class_only":target_error,
        "T0_cfg_state_count":target_states,
        "T0_original_source_committed_to_audible_period":False,
        "runtime_current_player_mediaitem_generation_proven":False,
        "selected_track_album_edition_duration_proven":False,
        "replacement_audio_connected":False,
        "field_values_urls_audio_or_accounts_read":False,
    }


def run(path:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not path.is_file() or path.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("EXOPLAYER_T0_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(path)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("EXOPLAYER_T0_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exo-t0-") as tmp:
        splits=audit.unbundle_candidate(path,Path(tmp))
        if len(splits)!=16:raise ValueError("EXOPLAYER_T0_SIGNED_SPLITS_COUNT")
        signer=audit.verify_split_set(splits)
        if signer.get("verified_issuer_signed_splits")!=16:
            raise ValueError("EXOPLAYER_T0_ISSUER_MISMATCH")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if meta.get("name")!=trusted.EXPECTED_PACKAGE or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("EXOPLAYER_T0_ORIGINAL_PACKAGE_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("EXOPLAYER_T0_NAV17_BASE_MISMATCH")
        result=scan_signed(splits)
    return {**result,"signed_exact_NAV17_verified":True,"ephemeral_read_only":True}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk",type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(run(args.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({"verdict":"EXOPLAYER_T0_SOURCE_AUDIT_INCOMPLETE",
            "safe_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "replacement_audio_connected":False}))
        raise SystemExit(2)
