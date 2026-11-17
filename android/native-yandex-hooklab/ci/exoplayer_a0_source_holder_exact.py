#!/usr/bin/env python3
"""Exact signed Yandex 2025 native source List -> d.A0 source-holder constructor.

Bounded to the newly proven ExoPlayer.d.T0 -> A0(List,int) playlist admission.
Reports only DEX method type descriptors and per-method reference flow. Does not
infer List.get element identity without a verified immutable singleton origin.
Does not read Track fields, URLs, audio or user data.
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
SOURCE="LSl6;"
TARGET=(OWNER,"A0","(Ljava/util/List;I)Ljava/util/ArrayList;")
PARENT=(OWNER,"T0","(Ljava/util/List;IJZ)V")
MAX_INVOKES=140
MAX_OBJECT_CREATIONS=64
MAX_TYPED_FIELDS=48
HOLDER="Landroidx/media3/exoplayer/i$c;"
HOLDER_CONSTRUCTOR=(HOLDER,"<init>","(LSl6;Z)V")
LIST_GET=("Ljava/util/List;","get","(I)Ljava/lang/Object;")
ARRAY_ADD=("Ljava/util/ArrayList;","add","(Ljava/lang/Object;)Z")


def exact_source_handoff(method):
    return method in (TARGET,PARENT,HOLDER_CONSTRUCTOR)



def same_reference_from_get_to_holder(dex, flags, off):
    """Only one exact local List.get -> move-result -> checked-cast -> holder init."""
    ins=list(audit.instructions(dex,off))
    get_sites=[i for i,(_pc,op,words) in enumerate(ins)
        if op in audit.INVOKES and 0x6E<=op<=0x78
        and dex.method(words[1])==LIST_GET]
    init_sites=[i for i,(_pc,op,words) in enumerate(ins)
        if op in audit.INVOKES and 0x6E<=op<=0x78
        and dex.method(words[1])==HOLDER_CONSTRUCTOR]
    result={
        "unique_List_get":len(get_sites)==1,
        "unique_holder_constructor":len(init_sites)==1,
        "List_get_receiver_is_exact_parameter":False,
        "same_get_result_passed_to_holder_ctor":False,
        "LSl6_check_cast_preserves_reference":False,
        "local_block_has_branch":False,
    }
    if len(get_sites)!=1 or len(init_sites)!=1:
        return result
    a,b=get_sites[0],init_sites[0]
    if a>=b or a+1>=b:return result
    param_regs=audit.typed_parameter_registers(
        dex,TARGET,flags,off,"Ljava/util/List;")
    get_regs=audit.invoke_registers(ins[a][1],ins[a][2])
    result["List_get_receiver_is_exact_parameter"]=(
        len(param_regs)==1 and len(get_regs)>=2 and get_regs[0] in param_regs
    )
    if not result["List_get_receiver_is_exact_parameter"]:return result
    if ins[a+1][1]!=0x0c:return result
    alias={(ins[a+1][2][0] >>8)}
    cast=False
    for pos in range(a+2,b):
        _pc,op,words=ins[pos]
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            result["local_block_has_branch"]=True
            return result
        if op==0x1f:
            r=words[0]>>8
            if r in alias and dex.descriptor(words[1])=="LSl6;":
                cast=True
            continue
        # Move-object preserves exact Java reference identity; all other
        # writes invalidate the destination's old provenance.
        if op in (0x07,0x08,0x09):
            coords=audit.move_object_registers(op,words)
            if coords is None:
                return result
            dest,src=coords
            if src in alias:alias.add(dest)
            else:alias.discard(dest)
            continue
        dest=audit.written_register(op,words)
        if dest is not None:alias.discard(dest)
    ctor_op,ctor_words=ins[b][1],ins[b][2]
    ctor_regs=audit.invoke_registers(ctor_op,ctor_words)
    result["same_get_result_passed_to_holder_ctor"]=(
        len(ctor_regs)==3 and ctor_regs[1] in alias
    )
    result["LSl6_check_cast_preserves_reference"]=cast
    return result


def same_holder_allocation_added_to_array(dex, off):
    """One unique newly created i$c object goes to the first typed ArrayList.add."""
    ins=list(audit.instructions(dex,off))
    starts=[i for i,(_pc,op,words) in enumerate(ins)
        if op==0x22 and dex.descriptor(words[1])==HOLDER]
    adds=[i for i,(_pc,op,words) in enumerate(ins)
        if op in audit.INVOKES and 0x6E<=op<=0x78
        and dex.method(words[1])==ARRAY_ADD]
    result={
        "unique_holder_new_instance":len(starts)==1,
        "unique_first_ArrayList_add":len(adds)==1,
        "same_new_holder_passed_into_ArrayList_add":False,
        "branch_between_creation_and_add":False,
    }
    if len(starts)!=1 or len(adds)!=1:return result
    a,b=starts[0],adds[0]
    if a>=b:return result
    reg=ins[a][2][0]>>8
    aliases={reg}
    for pos in range(a+1,b):
        _pc,op,words=ins[pos]
        if op in (0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            result["branch_between_creation_and_add"]=True
            return result
        if op in (0x07,0x08,0x09):
            coords=audit.move_object_registers(op,words)
            if coords is None:return result
            dest,src=coords
            if src in aliases:aliases.add(dest)
            else:aliases.discard(dest)
            continue
        if op==0x1f:continue
        dest=audit.written_register(op,words)
        if dest is not None:aliases.discard(dest)
    regs=audit.invoke_registers(ins[b][1],ins[b][2])
    result["same_new_holder_passed_into_ArrayList_add"]=(
        len(regs)==2 and regs[1] in aliases
    )
    return result


def scan_signed(splits):
    dexes=[]
    defs={}
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:raise ValueError("A0_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if exact_source_handoff(method):
                        if method in defs:raise ValueError("A0_DUPLICATE_TARGET")
                        defs[method]=(dex,flags,off)
    if len(dexes)!=6:raise ValueError("A0_EXPECTED_SIX_SIGNED_DEX")
    if set(defs)!={TARGET,PARENT,HOLDER_CONSTRUCTOR}:raise ValueError("A0_TARGET_BODY_NOT_FOUND")
    dex,flags,off=defs[TARGET]
    if not off:raise ValueError("A0_TARGET_NOT_EXECUTABLE")
    methods=[]
    instance_creations=[]
    field_refs=[]
    invoked_by_target=[]
    source_methods=[]
    list_methods=[]
    counts={"list_get":0,"iterator":0,"source_constructor":0}
    for ordinal,op,words in audit.instructions(dex,off):
        if op==0x22:
            descriptor=dex.descriptor(words[1])
            instance_creations.append({"ordinal":ordinal,"descriptor":descriptor})
            if len(instance_creations)>MAX_OBJECT_CREATIONS:
                raise ValueError("A0_OBJECT_CREATION_LIMIT")
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            callee=dex.method(words[1])
            row={"ordinal":ordinal,"owner":callee[0],"method":callee[1],
                 "signature":callee[2],"opcode":op}
            methods.append(row)
            if len(methods)>MAX_INVOKES:raise ValueError("A0_INVOKE_LIMIT")
            if callee[0] in ("Ljava/util/List;","Ljava/util/Iterator;",
                             "Ljava/util/Collection;"):
                list_methods.append(row)
                if callee[1]=="get":counts["list_get"]+=1
                if callee[1]=="iterator":counts["iterator"]+=1
            if SOURCE in audit.parse_types(callee[2]):
                source_methods.append(row)
                if callee[1]=="<init>":counts["source_constructor"]+=1
        if 0x52<=op<=0x6d:
            owner,_field_name,typ=audit.field_id(dex,words[1])
            if typ in (SOURCE,"Ljava/util/List;","Ljava/util/ArrayList;"):
                field_refs.append({"ordinal":ordinal,"owner":owner,"field_type":typ,
                                   "opcode":op})
                if len(field_refs)>MAX_TYPED_FIELDS:raise ValueError("A0_TYPED_FIELD_LIMIT")
    get_to_ctor=same_reference_from_get_to_holder(dex,flags,off)
    holder_to_list=same_holder_allocation_added_to_array(dex,off)
    ctor_dex,ctor_flags,ctor_off=defs[HOLDER_CONSTRUCTOR]
    if not ctor_off:raise ValueError("A0_HOLDER_CONSTRUCTOR_NO_BODY")
    holder_ctor_field_types=[]
    for ordinal,op,words in audit.instructions(ctor_dex,ctor_off):
        if 0x59<=op<=0x6d:
            owner,_name,field_type=audit.field_id(ctor_dex,words[1])
            if len(holder_ctor_field_types)<32:
                holder_ctor_field_types.append({
                    "ordinal":ordinal,"opcode":op,
                    "owner":owner,"field_type":field_type,
                })
    holder_ctor_cfg_events=[]
    try:
        ctor_trace=audit.trace_track_identity_method_cfg(ctor_dex,HOLDER_CONSTRUCTOR,ctor_flags,ctor_off,
            extra_identity_types={SOURCE:"NATIVE_MEDIA_SOURCE"})
        holder_ctor_cfg_events=[
            e for e in ctor_trace["events"]
            if e.get("kind") in (
                "FIELD_STORE_TYPED_IDENTITY","CALL_WITH_TYPED_IDENTITY",
                "CALL_WITH_POSSIBLE_IDENTITY","FIELD_READ_TYPED_IDENTITY")
        ][:24]
        stored=[e for e in ctor_trace["events"]
            if e.get("kind")=="FIELD_STORE_TYPED_IDENTITY"
            and e.get("identity_type")=="NATIVE_MEDIA_SOURCE"
            and e.get("destination_owner")==HOLDER
            and e.get("receiver_is_this_on_all_paths") is True
            and "NATIVE_MEDIA_SOURCE_PARAMETER" in e.get("origins",())]
        holder_field_store_proven=bool(stored)
        holder_cfg_error=None
    except (ValueError,audit.DexError) as e:
        holder_field_store_proven=False
        holder_cfg_error=type(e).__name__
    try:
        trace=audit.trace_track_identity_method_cfg(dex,TARGET,flags,off,
                extra_identity_types={
                    "Ljava/util/List;":"SOURCE_ADMISSION_LIST",
                    SOURCE:"NATIVE_MEDIA_SOURCE",
                    "Ljava/util/ArrayList;":"SOURCE_HOLDER_LIST",
                })
        events=[
            e for e in trace["events"]
            if (e.get("identity_type") in ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                or any(x.get("identity_type") in
                       ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                       for x in e.get("identity_arguments",[]))
                or any(x.get("identity_type") in
                       ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                       for x in e.get("possible_identity_arguments",[])))
        ]
        cfg_states=trace.get("processed_state_count");cfg_failure=None
    except (ValueError,audit.DexError) as e:
        events=[];cfg_states=None;cfg_failure=type(e).__name__

    # Parent proof is from the exact successful T0 audit:
    # d.e(source) -> singletonList(source) -> d.T0(theList) -> d.A0(theList).
    return {
        "verdict":"EXACT_A0_PLAYLIST_SOURCE_HOLDER_CANDIDATES_ONLY",
        "six_publisher_signed_dex":len(dexes),
        "exact_owner":TARGET[0],"exact_method":TARGET[1],
        "target_invokes":methods,
        "List_get_to_i_c_exact_same_object":get_to_ctor,
        "new_i_c_to_ArrayList_add_exact_same_object":holder_to_list,
        "holder_LSl6_parameter_stored_on_this":holder_field_store_proven,
        "holder_constructor_cfg_error":holder_cfg_error,
        "holder_constructor_typed_field_opcodes":holder_ctor_field_types,
        "holder_constructor_identity_events":holder_ctor_cfg_events,
        "one_source_to_internal_playlist_holder_static_proven":bool(
            get_to_ctor["List_get_receiver_is_exact_parameter"]
            and get_to_ctor["same_get_result_passed_to_holder_ctor"]
            and get_to_ctor["LSl6_check_cast_preserves_reference"]
            and holder_to_list["same_new_holder_passed_into_ArrayList_add"]
            and holder_field_store_proven),
        "source_typed_invokes":source_methods,
        "list_or_iterator_invokes":list_methods,
        "target_new_instances":instance_creations,
        "target_typed_field_access":field_refs,
        "operation_counters":counts,
        "typed_list_cfg_events":events[:48],
        "typed_list_cfg_events_truncated":len(events)>48,
        "cfg_state_count":cfg_states,
        "cfg_error_class":cfg_failure,
        "active_selected_media_period_confirmed":False,
        "same_source_to_current_decoder_proven":False,
        "selected_track_album_edition_duration_generation_proven":False,
        "replacement_audio_connected":False,
        "private_field_names_or_values_urls_audio_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("A0_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("A0_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exoplayer-a0-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("A0_16_SIGNED_SPLITS_REQUIRED")
        issuer=audit.verify_split_set(splits)
        if issuer.get("verified_issuer_signed_splits")!=16:
            raise ValueError("A0_ISSUER_SIGNATURE_MISMATCH")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE or
                meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("A0_PINNED_PACKAGE_IDENTITY_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("A0_NAV17_BASE_SHA_MISMATCH")
        report=scan_signed(splits)
    return {**report,"signed_exact_NAV17_verified":True,"read_only_ephemeral":True}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk",required=True,type=Path)
    a=parser.parse_args()
    try:print(json.dumps(run(a.xapk),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({"verdict":"A0_SOURCE_HOLDER_AUDIT_INCOMPLETE",
             "safe_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
             "replacement_audio_connected":False}))
        raise SystemExit(2)
