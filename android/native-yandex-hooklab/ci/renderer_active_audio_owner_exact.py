#!/usr/bin/env python3
"""Signed 2025.10.4 exact Exo renderer audio/state and selected queue field audit.

Read-only, finite metadata scan. The source is the already pinned private
16-split Yandex research original. Never inspect media, private field names,
tokens, URLs, sample bytes or app state. Does not equate Renderer STARTED with
audible PCM or current selected CELIKOM source.
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
ENGINE="Landroidx/media3/exoplayer/e;"
QUEUE="Landroidx/media3/exoplayer/h;"
RENDERER="Landroidx/media3/exoplayer/k;"
RENDERER_BASE="Landroidx/media3/exoplayer/b;"
HOLDER="Lxh6;"
ENGINE_BREAK=(ENGINE,"break","()V")
ENGINE_RESET=(ENGINE,"class","([ZJ)V")
ENGINE_ENABLE=(ENGINE,"catch","(Lxh6;IZJ)V")
TRACK_TYPE="getTrackType"
GET_STATE="getState"
MAX_CLASSES=180000
MAX_METHODS=750000
MAX_REACHABLE=100

def renderer_subtree(definitions):
    if RENDERER not in definitions or RENDERER_BASE not in definitions:
        raise ValueError("AUDIO_EXACT_RENDERER_ROOT_MISSING")
    reachable={RENDERER}
    for _ in range(50):
        add={name for name,d in definitions.items()
             if name not in reachable
             and (d["parent"] in reachable or set(d["interfaces"]) & reachable)}
        if not add:break
        reachable|=add
        if len(reachable)>MAX_REACHABLE:
            raise ValueError("AUDIO_RENDERER_SUBTREE_LIMIT")
    if RENDERER_BASE not in reachable:
        raise ValueError("AUDIO_RENDERER_BASE_NOT_INTERFACE_IMPL")
    return reachable

def signature_rows(methods,subtree,name):
    rows=sorted((method,code!=0) for method,(dex,flags,code) in methods.items()
                if method[0] in subtree and method[1]==name and method[2]=="()I")
    if len(rows)>MAX_REACHABLE:
        raise ValueError("AUDIO_METHOD_ROWS_LIMIT")
    return [{"owner":owner,"name":mn,"desc":desc,"has_code":has_code}
            for (owner,mn,desc),has_code in rows]

def checked_field_at(dex,code,pc,owner,typ):
    insns=list(audit.instructions(dex,code))
    matches=[(op,w) for at,op,w in insns if at==pc]
    if len(matches)!=1 or matches[0][0]!=0x54:
        raise ValueError("AUDIO_EXACT_IGET_PC_MISSING")
    field=audit.field_id(dex,matches[0][1][1])
    if field[0]!=owner or field[2]!=typ:
        raise ValueError("AUDIO_EXACT_IGET_OWNER_TYPE_MISMATCH")
    return field

def analyze_signed(apks):
    defs={}
    methods={}
    dex_count=0
    count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):
                    continue
                dex=audit.Dex(z.read(item.filename))
                dex_count+=1
                for i in range(dex.class_count):
                    off=dex.class_offset+i*32
                    owner=dex.descriptor(dex.u32(off))
                    if owner in defs:raise ValueError("AUDIO_DUPLICATE_CLASS")
                    parent_index=dex.u32(off+8)
                    parent=None if parent_index==0xffffffff else dex.descriptor(parent_index)
                    interface_off=dex.u32(off+12)
                    interfaces=[]
                    if interface_off:
                        n=dex.u32(interface_off)
                        if n>48:raise ValueError("AUDIO_INTERFACE_COUNT_LIMIT")
                        dex.bounds(interface_off+4,2*n)
                        interfaces=[dex.descriptor(dex.u16(interface_off+4+2*x)) for x in range(n)]
                    defs[owner]={"parent":parent,"interfaces":interfaces}
                    if len(defs)>MAX_CLASSES:raise ValueError("AUDIO_CLASS_LIMIT")
                for method,flags,code in audit.method_definitions_with_flags(dex):
                    count+=1
                    if count>MAX_METHODS:raise ValueError("AUDIO_METHOD_LIMIT")
                    if method[0] not in (ENGINE,QUEUE,RENDERER,RENDERER_BASE) and not (
                            method[1] in (TRACK_TYPE,GET_STATE)
                            and method[2]=="()I"):
                        continue
                    if method in methods:raise ValueError("AUDIO_DUPLICATE_METHOD")
                    methods[method]=(dex,flags,code)
    if dex_count!=6:raise ValueError("AUDIO_SIGNED_SIX_DEX_REQUIRED")
    subtree=renderer_subtree(defs)
    type_rows=signature_rows(methods,subtree,TRACK_TYPE)
    state_rows=signature_rows(methods,subtree,GET_STATE)
    # Obfuscated 2025 renderer may not expose generic Media3 method names.
    # Never guess getTrackType() from documentation or inject a speculative
    # reflection hook. First produce signed exact interface/base inventory.
    public_int_methods=sorted({
        (owner,mn,desc) for (owner,mn,desc) in methods
        if owner in (RENDERER,RENDERER_BASE) and desc=="()I"
    })
    if len(public_int_methods)>64:
        raise ValueError("AUDIO_RENDERER_INT_INVENTORY_TOO_LARGE")
    engine_k_int_calls=[]
    for method in (ENGINE_BREAK,ENGINE_RESET,ENGINE_ENABLE):
        dex,flags,offset=methods[method]
        for pc,op,w in audit.instructions(dex,offset):
            if op not in audit.INVOKES or not (0x6e<=op<=0x78):
                continue
            callee=dex.method(w[1])
            if callee[0] in (RENDERER,RENDERER_BASE) and callee[2]=="()I":
                engine_k_int_calls.append({"caller":list(method),
                    "pc":pc,"callee":list(callee)})
            if len(engine_k_int_calls)>100:
                raise ValueError("AUDIO_RENDERER_CALLS_TOO_MANY")
    if ENGINE_BREAK not in methods or ENGINE_RESET not in methods or ENGINE_ENABLE not in methods:
        raise ValueError("AUDIO_EXACT_ENGINE_METHODS_MISSING")
    break_dex,_,break_code=methods[ENGINE_BREAK]
    reset_dex,_,reset_code=methods[ENGINE_RESET]
    # Previously signed six-DEX proven exact queue SLOT_B is e.break PC 547.
    # Both new direct engine-holder callers have this exact field ID, not just type.
    slotb=checked_field_at(break_dex,break_code,547,QUEUE,HOLDER)
    b1051=checked_field_at(break_dex,break_code,1051,QUEUE,HOLDER)
    reset2=checked_field_at(reset_dex,reset_code,2,QUEUE,HOLDER)
    if slotb!=b1051 or slotb!=reset2:
        raise ValueError("AUDIO_EXACT_SLOT_B_FIELD_NOT_SAME")
    # Verify the e.break fields pointing to the queue. They may have the same
    # type across branches but MUST be the identical exact DEX field ID.
    q_reads=[]
    for pc,op,w in audit.instructions(break_dex,break_code):
        if op!=0x54:continue
        owner,name,typ=audit.field_id(break_dex,w[1])
        if owner==ENGINE and typ==QUEUE:
            q_reads.append((pc,(owner,name,typ)))
    distinct={field for _,field in q_reads}
    if len(distinct)!=1 or not q_reads:
        raise ValueError("AUDIO_ENGINE_QUEUE_FIELD_AMBIGUOUS")
    queue=next(iter(distinct))
    # Confirm queue field is used in the other engine caller as well.
    reset_queue_reads=[]
    for pc,op,w in audit.instructions(reset_dex,reset_code):
        if op==0x54:
            field=audit.field_id(reset_dex,w[1])
            if field[0]==ENGINE and field[2]==QUEUE:
                reset_queue_reads.append((pc,field))
    if not reset_queue_reads or any(field!=queue for _,field in reset_queue_reads):
        raise ValueError("AUDIO_RESET_ENGINE_QUEUE_NOT_SAME")
    runtime_methods_named=bool(type_rows and state_rows)
    return {
      "verdict":("SIGNED_EXACT_2025_AUDIO_RENDERER_RUNTIME_WITNESS_CANDIDATE"
                 if runtime_methods_named else
                 "SIGNED_2025_RENDERER_METHOD_INVENTORY_REQUIRES_EXACT_OBFUSCATION"),
      "runtime_named_method_gate_ready":runtime_methods_named,
      "renderer_exact_int_method_inventory":[list(t) for t in public_int_methods],
      "engine_renderer_int_method_calls":engine_k_int_calls,
      "original_16_publisher_signed_splits":True,
      "signed_six_dex":True,
      "renderer_interface":RENDERER,
      "renderer_base":RENDERER_BASE,
      "renderer_reachable_class_count":len(subtree),
      "renderer_runtime_getTrackType_declared":type_rows,
      "renderer_runtime_getState_declared":state_rows,
      "engine_exact_queue_reference_same_across_break_reset":True,
      "engine_queue_read_count":len(q_reads),
      "engine_reset_queue_read_count":len(reset_queue_reads),
      "slot_b_field_reference_same_in_break_547_1051_and_reset_2":True,
      "audio_type_runtime_value_1_observed":False,
      "started_state_runtime_value_2_observed":False,
      "currently_audible_track_or_celikom_replacement_proven":False,
      "private_fields_names_or_values_exported":False
    }

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("AUDIO_PRIVATE_SIGNED_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("AUDIO_PINNED_XAPK_SIZE")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("AUDIO_PINNED_XAPK_HASH")
    with tempfile.TemporaryDirectory(prefix="celikom-2025-audio-only-") as temp:
        apks=audit.unbundle_candidate(xapk,Path(temp))
        if len(apks)!=16:raise ValueError("AUDIO_SPLIT_COUNT")
        sig=audit.verify_split_set(apks)
        if sig.get("verified_issuer_signed_splits")!=16:
            raise ValueError("AUDIO_ISSUER_SIG")
        base=[]
        for apk in apks:
            info=trusted.package_metadata(apk)
            if info.get("name")!=trusted.EXPECTED_PACKAGE or info.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("AUDIO_ORIGINAL_PACKAGE_OR_VERSION")
            if not info.get("split"):base.append(apk)
        if len(base)!=1 or trusted.sha256_file(base[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("AUDIO_ORIGINAL_BASE_HASH")
        return analyze_signed(apks)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    options=parser.parse_args()
    try:print(json.dumps(run(options.xapk),sort_keys=True))
    except (ValueError,RuntimeError,audit.DexError,OSError,zipfile.BadZipFile) as err:
        message=str(err)
        print(json.dumps({"verdict":"AUDIO_STATIC_PROOF_INCOMPLETE",
            "error_code":message if re.fullmatch("[A-Z0-9_]{1,90}",message) else None,
            "runtime_hook_allowed":False}))
        raise SystemExit(2)
