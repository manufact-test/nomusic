#!/usr/bin/env python3
"""Read-only bounded signed NAV17 exact MediaPeriod -> native holder boundary.

Starts from proven Lo96 source to MediaPeriod same-reference in Lp96.transient.
Checks ONLY its two independently observed exact signed caller methods:
 Lp96.goto(LSl6$b;LrH2;J)Lwh6;
 Lxh6.<init>([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V
These may create queue/preload periods, NOT necessarily audible/current periods.
No runtime hooks, media/audio, account, or private field name/value exposure.
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

SOURCE="LSl6;"
PERIOD="Lo96;"
PERIOD_FACTORY=("Lp96;","transient","(LSl6$b;LrH2;J)Lo96;")
PERIOD_ADAPTER=("Lp96;","goto","(LSl6$b;LrH2;J)Lwh6;")
PERIOD_HOLDER_CTOR=("Lxh6;","<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
PERIOD_WRAPPER_CTOR=("Lup1;","<init>","(Lwh6;ZJJ)V")
EXACT_METHODS=frozenset((PERIOD_FACTORY,PERIOD_ADAPTER,PERIOD_HOLDER_CTOR,PERIOD_WRAPPER_CTOR))
WHITELIST=frozenset({
    "Lp96;","Lxh6;","Lo96;","LuIb;","Lwh6;","LSl6;",
    "Landroidx/media3/exoplayer/i;","Landroidx/media3/exoplayer/l;",
    "Landroidx/media3/exoplayer/d;","Landroidx/media3/exoplayer/m;",
    "LrH2;","Lyh6;","Lup1;",
})
MAX_CALLS=100
MAX_FIELDS=110
MAX_NEW=70
MAX_EVENTS=70


def only_exact_entry(method):
    return method in EXACT_METHODS


def scan_signed(apks):
    dexes=[]
    methods={}
    class_refs={}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("PERIOD_ACTIVATION_SIGNED_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for i in range(dex.class_count):
                    cls_off=dex.class_offset+i*32
                    cls=dex.descriptor(dex.u32(cls_off))
                    if cls not in WHITELIST:continue
                    parent_idx=dex.u32(cls_off+8)
                    parent=None if parent_idx==0xFFFFFFFF else dex.descriptor(parent_idx)
                    class_refs[cls]={"superclass":parent,"access_flags":dex.u32(cls_off+4)}
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if not only_exact_entry(method):continue
                    if method in methods:raise ValueError("PERIOD_ACTIVATION_DUPLICATE_TARGET")
                    methods[method]=(dex,flags,off)
    if len(dexes)!=6:raise ValueError("PERIOD_ACTIVATION_SIX_DEX_REQUIRED")
    if set(methods)!=EXACT_METHODS or any(not x[2] for x in methods.values()):
        raise ValueError("PERIOD_ACTIVATION_METHOD_BODY_MISSING")
    # Bound direct construction callsites only for the signed exact holder.
    # These callers are potential queue management sites, not active decoder proof.
    holder_ctor_callers=[]
    for dex in dexes:
        for caller,flags,off in audit.method_definitions_with_flags(dex):
            for pc,op,words in audit.instructions(dex,off):
                if op not in audit.INVOKES or not 0x6E<=op<=0x78:continue
                if dex.method(words[1])!=PERIOD_HOLDER_CTOR:continue
                if len(holder_ctor_callers)>=38:
                    raise ValueError("PERIOD_HOLDER_EXACT_CALLER_LIMIT")
                holder_ctor_callers.append({
                    "caller_owner":caller[0],"caller_method":caller[1],
                    "caller_signature":caller[2],"pc":pc,
                })
    # An exact constructor stores period ownership inside the native period
    # wrapper only when its same-typed argument flows into that instance.
    wrapper_dex,wrapper_flags,wrapper_off=methods[PERIOD_WRAPPER_CTOR]
    wrapper_fields=[]
    for pc,op,words in audit.instructions(wrapper_dex,wrapper_off):
        if 0x52<=op<=0x6d:
            owner,_name,typ=audit.field_id(wrapper_dex,words[1])
            if len(wrapper_fields)>=28:
                raise ValueError("PERIOD_WRAPPER_CTOR_FIELD_LIMIT")
            wrapper_fields.append({
                "pc":pc,"owner":owner,"type":typ,"opcode":op,
            })
    try:
        wrapper_trace=audit.trace_track_identity_method_cfg(
            wrapper_dex,PERIOD_WRAPPER_CTOR,wrapper_flags,wrapper_off,
            extra_identity_types={
                "Lwh6;":"EXACT_INCOMING_PERIOD",
                "Lup1;":"EXACT_NATIVE_PERIOD_WRAPPER",
            })
        wrapper_events=[
            e for e in wrapper_trace.get("events",())
            if e.get("kind") in (
                "FIELD_STORE_TYPED_IDENTITY","CALL_WITH_TYPED_IDENTITY",
                "RETURN_TYPED_IDENTITY")
            and "EXACT_INCOMING_PERIOD" in str(e)
        ][:24]
        wrapper_source_stored=any(
            e.get("kind")=="FIELD_STORE_TYPED_IDENTITY"
            and e.get("identity_type")=="EXACT_INCOMING_PERIOD"
            and e.get("destination_owner")=="Lup1;"
            and e.get("receiver_is_this_on_all_paths") is True
            and "EXACT_INCOMING_PERIOD_PARAMETER" in e.get("origins",())
            for e in wrapper_trace.get("events",())
        )
        wrapper_trace_complete=True
        wrapper_trace_error=None
    except (ValueError,audit.DexError) as e:
        wrapper_events=[];wrapper_source_stored=False
        wrapper_trace_complete=False;wrapper_trace_error=type(e).__name__
    rows=[]
    for target in (PERIOD_ADAPTER,PERIOD_HOLDER_CTOR):
        dex,flags,off=methods[target]
        calls=[]
        fields=[]
        objects=[]
        period_factory_sites=[]
        immediate_period_uses=[]
        for pc,op,words in audit.instructions(dex,off):
            if op in audit.INVOKES and 0x6E<=op<=0x78:
                callee=dex.method(words[1])
                if len(calls)>=MAX_CALLS:raise ValueError("PERIOD_ACTIVATION_INVOKES_LIMIT")
                calls.append({
                    "pc":pc,"owner":callee[0],"method":callee[1],
                    "signature":callee[2],"invoke_opcode":op,
                })
                if callee==PERIOD_FACTORY:
                    period_factory_sites.append(pc)
                if (PERIOD in audit.parse_types(callee[2])
                    or callee[2].split(")",1)[1]==PERIOD
                    or "Lwh6;" in audit.parse_types(callee[2])):
                    immediate_period_uses.append({
                        "pc":pc,"owner":callee[0],"method":callee[1],
                        "signature":callee[2],
                    })
            if op==0x22:
                typ=dex.descriptor(words[1])
                if len(objects)>=MAX_NEW:raise ValueError("PERIOD_ACTIVATION_ALLOCATION_LIMIT")
                objects.append({"pc":pc,"type":typ})
            if 0x52<=op<=0x6d:
                field_owner,_name,field_type=audit.field_id(dex,words[1])
                if len(fields)>=MAX_FIELDS:raise ValueError("PERIOD_ACTIVATION_TYPED_FIELD_LIMIT")
                # No private field name, value, or field index exported.
                if field_owner in WHITELIST or field_type in (PERIOD,"Lwh6;","Lp96;","LSl6;"):
                    fields.append({"pc":pc,"owner":field_owner,
                        "type":field_type,"opcode":op})
        try:
            trace=audit.trace_identity_method(
                dex,target,flags,off,
                extra_identity_types=(
                    PERIOD,"Lwh6;","LSl6;","Lp96;","Lxh6;",
                    "Landroidx/media3/exoplayer/i;"
                ),
                capture_argument_provenance_targets={PERIOD_FACTORY},
                track_fields_from_any_receiver=True,
            )
            selected=[
                e for e in trace.get("events",())
                if (
                    e.get("kind")=="CALL_ARGUMENT_PROVENANCE"
                    and (e["callee"]["owner"],e["callee"]["method"],
                         e["callee"]["signature"])==PERIOD_FACTORY
                ) or (
                    e.get("kind") in (
                        "MOVE_RESULT_TYPED_IDENTITY",
                        "RETURN_TYPED_IDENTITY",
                        "FIELD_STORE_TYPED_IDENTITY",
                        "FIELD_READ_TYPED_IDENTITY",
                        "CALL_WITH_TYPED_IDENTITY",
                        "CALL_WITH_POSSIBLE_IDENTITY",
                    )
                    and any(x in str(e) for x in (
                        "EXTRA_OBJECT:Lo96;","EXTRA_OBJECT:Lwh6;"))
                )
            ]
            complete=True
            trace_error=None
            aliases_cleared=trace.get("branch_seen_aliases_cleared")
        except (ValueError,audit.DexError) as e:
            selected=[]
            complete=False
            aliases_cleared=None
            trace_error=type(e).__name__
        try:
            cfg=audit.trace_track_identity_method_cfg(
                dex,target,flags,off,extra_identity_types={
                    PERIOD:"PERIOD_FROM_LO96_FACTORY",
                    "Lwh6;":"POTENTIAL_NATIVE_PERIOD_ADAPTER",
                    "Lp96;":"SOURCE_WRAPPER",
                    "Landroidx/media3/exoplayer/i;":"NATIVE_EXO_SOURCE_MANAGER",
                })
            event_list=[
                e for e in cfg.get("events",())
                if (
                    e.get("identity_type") in (
                        "PERIOD_FROM_LO96_FACTORY","POTENTIAL_NATIVE_PERIOD_ADAPTER")
                    or any(x.get("identity_type") in (
                        "PERIOD_FROM_LO96_FACTORY","POTENTIAL_NATIVE_PERIOD_ADAPTER")
                        for x in e.get("identity_arguments",()))
                    or any(x.get("identity_type") in (
                        "PERIOD_FROM_LO96_FACTORY","POTENTIAL_NATIVE_PERIOD_ADAPTER")
                        for x in e.get("possible_identity_arguments",()))
                )
            ][:MAX_EVENTS]
            cfg_complete=True;cfg_error=None
            cfg_states=cfg.get("processed_state_count")
        except (ValueError,audit.DexError) as e:
            event_list=[];cfg_complete=False
            cfg_error=type(e).__name__;cfg_states=None
        rows.append({
            "method":{"owner":target[0],"name":target[1],"descriptor":target[2]},
            "exact_factory_callsite_count":len(period_factory_sites),
            "exact_factory_callsite_pcs":period_factory_sites,
            "typed_period_related_calls":immediate_period_uses,
            "direct_invokes":calls,"allocations":objects,
            "bounded_field_type_operations":fields,
            "identity_trace_complete":complete,
            "branch_aliases_cleared":aliases_cleared,
            "identity_trace_error_class":trace_error,
            "local_period_alias_events":selected[:MAX_EVENTS],
            "local_alias_events_truncated":len(selected)>MAX_EVENTS,
            "cfg_complete":cfg_complete,"cfg_states":cfg_states,
            "cfg_error_class":cfg_error,
            "cfg_source_period_events":event_list,
        })
    return {
        "verdict":"EXACT_LO96_PERIOD_TO_NATIVE_HOLDER_CALLERS_STATIC_ONLY",
        "signed_dex_count":len(dexes),
        "bounded_class_ancestry":class_refs,
        "exact_native_period_holder_constructor_callers":holder_ctor_callers,
        "exact_period_wrapper_ctor_fields":wrapper_fields,
        "exact_period_wrapper_ctor_identity_events":wrapper_events,
        "period_argument_stored_on_Lup1_this":wrapper_source_stored,
        "period_wrapper_ctor_trace_complete":wrapper_trace_complete,
        "period_wrapper_ctor_trace_error":wrapper_trace_error,
        "exact_period_handoff_candidate_methods":rows,
        "runtime_period_active_vs_prefetch_proven":False,
        "runtime_current_player_and_queue_generation_proven":False,
        "same_active_period_to_decoder_proven":False,
        "CELIKOM_replacement_audio_connected":False,
        "private_fields_names_values_audio_urls_ids_or_tokens_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("PERIOD_ACTIVATION_PINNED_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("PERIOD_ACTIVATION_PINNED_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-period-activation-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:raise ValueError("PERIOD_ACTIVATION_SIGNED_SPLITS_REQUIRED")
        signed=audit.verify_split_set(apks)
        if signed.get("verified_issuer_signed_splits")!=16:
            raise ValueError("PERIOD_ACTIVATION_PUBLISHER_SIGNER_MISMATCH")
        bases=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if meta.get("name")!=trusted.EXPECTED_PACKAGE or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("PERIOD_ACTIVATION_ORIGINAL_VERSION_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("PERIOD_ACTIVATION_NAV17_ORIGIN_MISMATCH")
        report=scan_signed(apks)
    return {**report,"exact_signed_NAV17_original_verified":True,"ephemeral_read_only":True}

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xapk",type=Path,required=True)
    a=p.parse_args()
    try:print(json.dumps(run(a.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({
            "verdict":"PERIOD_ACTIVATION_EXACT_AUDIT_INCOMPLETE",
            "safe_error_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "CELIKOM_replacement_audio_connected":False,
        }))
        raise SystemExit(2)
