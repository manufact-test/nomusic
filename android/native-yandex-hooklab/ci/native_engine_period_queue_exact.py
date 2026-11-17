#!/usr/bin/env python3
"""Signed NAV17 ExoPlayer engine's ONE exact Lxh6 constructor caller.

Continuation: TrackWrapper->MediaSource->native source list->Lo96 Period
->Lxh6.<init> from AndroidX ExoPlayer internal e.break().
This inspects only that exact bounded caller, without inferring active/current
selection or decoder from a period holder / prefetch / queue operation.
No private fields, media metadata, audio, URLs, IDs or user data read.
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

ENGINE=("Landroidx/media3/exoplayer/e;","break","()V")
PERIOD_HOLDER=("Lxh6;","<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
MAX_CALLS=240
MAX_EXACT_HOLDER_REFS=90
MAX_FIELD_OPS=110
MAX_NEW=72


def only_grounded_engine(method):
    return method==ENGINE


def scan_signed(apks):
    exact=None
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("ENGINE_EXACT_SIGNED_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dex_count+=1
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if only_grounded_engine(method):
                        if exact:raise ValueError("ENGINE_EXACT_METHOD_DUPLICATE")
                        exact=(dex,flags,code_off)
    if dex_count!=6:raise ValueError("ENGINE_EXPECTED_SIGNED_SIX_DEX")
    if not exact or not exact[2]:
        raise ValueError("ENGINE_EXACT_CALLER_NOT_DEFINED")
    dex,flags,off=exact
    instructions=list(audit.instructions(dex,off))
    new_holder=[]
    holder_ctor=[]
    relevant=[]
    instance_creations=[]
    fields=[]
    all_calls=0
    for pc,op,words in instructions:
        if op==0x22:
            t=dex.descriptor(words[1])
            if len(instance_creations)>=MAX_NEW:raise ValueError("ENGINE_NEW_LIMIT")
            instance_creations.append({"pc":pc,"type":t})
            if t=="Lxh6;":new_holder.append(pc)
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            all_calls+=1
            if all_calls>MAX_CALLS:raise ValueError("ENGINE_INVOKES_LIMIT")
            callee=dex.method(words[1])
            if callee==PERIOD_HOLDER:
                holder_ctor.append(pc)
            if (callee[0] in (
                    "Lxh6;","Landroidx/media3/exoplayer/e;",
                    "Landroidx/media3/exoplayer/i;","Lup1;","Lo96;"
                ) or "Lxh6;" in audit.parse_types(callee[2])
                    or callee[2].split(")",1)[1]=="Lxh6;"):
                if len(relevant)>=MAX_EXACT_HOLDER_REFS:
                    raise ValueError("ENGINE_TYPED_HOLDER_CALL_LIMIT")
                relevant.append({
                    "pc":pc,"callee_owner":callee[0],
                    "callee_method":callee[1],"callee_signature":callee[2],
                })
        if 0x52<=op<=0x6d:
            owner,_field,typ=audit.field_id(dex,words[1])
            # Limit field projections to exact period/holder/manager types;
            # Exo engine has many unrelated fields. Never broaden them.
            if (owner=="Lxh6;" or typ in (
                "Lxh6;","Lup1;","Lo96;","Lwh6;",
                "Landroidx/media3/exoplayer/i;")):
                if len(fields)>=MAX_FIELD_OPS:
                    raise ValueError("ENGINE_RELEVANT_FIELD_LIMIT")
                fields.append({"pc":pc,"owner":owner,"field_type":typ,"opcode":op})
    if len(new_holder)!=1 or len(holder_ctor)!=1:
        raise ValueError("ENGINE_EXACT_HOLDER_ALLOCATION_SHAPE_MISMATCH")
    try:
        trace=audit.trace_identity_method(
            dex,ENGINE,flags,off,
            extra_identity_types=(
                "Lxh6;","Lup1;","Lo96;","Landroidx/media3/exoplayer/i;"
            ),
            capture_argument_provenance_targets={PERIOD_HOLDER},
            track_fields_from_any_receiver=True,
        )
        events=[
            e for e in trace.get("events",())
            if (
                e.get("kind")=="CALL_ARGUMENT_PROVENANCE"
                and (e["callee"]["owner"],e["callee"]["method"],
                    e["callee"]["signature"])==PERIOD_HOLDER
            ) or (
                e.get("kind") in (
                    "FIELD_STORE_TYPED_IDENTITY","FIELD_READ_TYPED_IDENTITY",
                    "MOVE_RESULT_TYPED_IDENTITY","CALL_WITH_TYPED_IDENTITY",
                    "RETURN_TYPED_IDENTITY","CALL_WITH_POSSIBLE_IDENTITY")
                and "EXTRA_OBJECT:Lxh6;" in str(e)
            )
        ][:45]
        trace_complete=True
        alias_cleared=trace.get("branch_seen_aliases_cleared")
        error=None
    except (ValueError,audit.DexError) as e:
        events=[];trace_complete=False;alias_cleared=None
        error=type(e).__name__
    # Distinct source period, queue inclusion and active playback are
    # separate notions. A single constructor is not a current selection.
    return {
        "verdict":"EXACT_NATIVE_ENGINE_NEW_PERIOD_HOLDER_CALLER_STATIC_ONLY",
        "six_signed_dex":dex_count,
        "method":ENGINE,
        "engine_instruction_count":len(instructions),
        "engine_invoke_count":all_calls,
        "single_Lxh6_new_instance_pc":new_holder,
        "single_exact_Lxh6_ctor_pc":holder_ctor,
        "scoped_native_engine_and_holder_calls":relevant,
        "scoped_native_engine_holder_field_types":fields,
        "method_object_allocations":instance_creations,
        "identity_trace_complete":trace_complete,
        "branch_aliases_cleared":alias_cleared,
        "local_same_holder_reference_events":events,
        "identity_trace_error_class":error,
        "exact_source_period_in_engine_queue_current_proven":False,
        "active_period_from_queue_vs_prefetch_proven":False,
        "decoder_attached_to_same_current_period_proven":False,
        "stage_b_replacement_connected_or_audible":False,
        "private_field_names_values_ids_urls_media_or_audio_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("ENGINE_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("ENGINE_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exo-engine-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:raise ValueError("ENGINE_16_PUBLISHER_SPLITS_REQUIRED")
        sig=audit.verify_split_set(apks)
        if sig.get("verified_issuer_signed_splits")!=16:
            raise ValueError("ENGINE_ISSUER_SIGNATURE_MISMATCH")
        bases=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if meta.get("name")!=trusted.EXPECTED_PACKAGE or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("ENGINE_PINNED_VERSION_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("ENGINE_NAV17_BASE_SHA_MISMATCH")
        result=scan_signed(apks)
    return {**result,"publisher_signed_original_verified":True,"ephemeral_read_only":True}


if __name__=="__main__":
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("--xapk",required=True,type=Path)
    p=args.parse_args()
    try:print(json.dumps(run(p.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({
            "verdict":"ENGINE_EXACT_HOLDER_AUDIT_INCOMPLETE",
            "safe_error_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "stage_b_replacement_connected_or_audible":False
        }))
        raise SystemExit(2)
