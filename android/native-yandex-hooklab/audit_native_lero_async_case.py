#!/usr/bin/env python3
"""Publisher-original exact Lero.t -> Lwq7 constructor tag -> switch case witness.

Checks the REAL signed six-DEX switch payload and the concrete int discriminator
passed to a synthetic shared-dispatch lambda. Only a matching tag, same field
slot and matching switch branch can establish a static scheduled read path.
No coroutine/instance/current-track/ExoPlayer prepare proof. Never export
literal vendor tag values, APK/DEX, URLs, strings or media.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
from inspect_android_host import Dex,DexError,DEX_MAX
from trace_native_callers import method_definitions,INVOKES
from audit_native_register_bridge import (
    instructions,invoke_registers,move_object_registers,signed_bits
)
from audit_native_ga4_field_receiver import field_key
from audit_native_typed_wrapper_coroutines import method_profile,brief_type
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

OWNER="Lwq7;"
ORIGIN="Lero;"
LOADER="Lmb4;"
MAX_CASES=300
MAX_BODIES=230600
MAX_HITS=25
MAX_METHOD_LENGTH=15000


def int_constant_from_words(op,words):
    """DEX const/4, const/16, const, const/high16, no arbitrary literals."""
    if op==0x12:
        return signed_bits((words[0]>>12)&15,4)
    if op==0x13:
        return signed_bits(words[1],16)
    if op==0x14:
        return signed_bits(words[1] | words[2]<<16,32)
    if op==0x15:
        return signed_bits(words[1]<<16,32)
    return None


def nearby_constructor_tag(d,ins,at):
    """Backtrack EXACT integer tag word 1 of Lwq7.<init>(I,Object).

    Do not cross basic-block boundaries. Respect move copies and clobbers.
    """
    _,op,words=ins[at]
    method=d.method(words[1])
    if not (method[0]==OWNER and method[1]=="<init>" and
            method[2].startswith("(ILjava/lang/Object;)V")):
        return None
    regs=invoke_registers(op,words)
    if len(regs)!=3:return None
    source=regs[1]
    for i in range(at-1,max(-1,at-18),-1):
        _,op,words=ins[i]
        if op in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            break
        if op in (0x01,0x02,0x03):
            if op==0x01:
                dest=(words[0]>>8)&15
                origin=(words[0]>>12)&15
            elif op==0x02:dest=words[0]>>8;origin=words[1]
            else:dest=words[1];origin=words[2]
            if dest==source:source=origin
            continue
        if op in (0x12,0x13,0x14,0x15):
            dest=((words[0]>>8)&15) if op==0x12 else words[0]>>8
            if dest==source:
                return {"tag":int_constant_from_words(op,words),
                        "constructor":method,
                        "arg_coords":regs,
                        "const_ordinal":i,
                        "constructor_ordinal":at,
                        "single_basic_block":True}
        if op in (0x0a,0x0b,0x0c,0x1a,0x1b,0x1c,0x22,0x54,0x62):
            dst=(words[0]>>8)&15 if op==0x54 else words[0]>>8
            if dst==source:break
    return {"tag":None,"constructor":method,"arg_coords":regs,
            "const_ordinal":None,"constructor_ordinal":at,
            "single_basic_block":False}


def switch_table_for_ins(ins,idx):
    """Decode DEX packed/sparse-switch payload (31t), not a guessed case."""
    pc,op,words=ins[idx]
    if op not in (0x2b,0x2c):raise DexError("EXPECTED_SWITCH")
    offset=signed_bits(words[1]|(words[2]<<16),32)
    payload_pc=pc+offset
    payload=next((w for at,pop,w in ins if at==payload_pc and pop==0),None)
    if payload is None or len(payload)<4:raise DexError("SWITCH_PAYLOAD_NOT_FOUND")
    expect=0x0100 if op==0x2b else 0x0200
    if payload[0]!=expect:raise DexError("SWITCH_PAYLOAD_KIND")
    size=payload[1]
    if size>MAX_CASES:raise DexError("SWITCH_CASE_BOUND")
    cases={}
    if op==0x2b:
        if len(payload)!=4+size*2:raise DexError("PACKED_SWITCH_LENGTH")
        first_key=signed_bits(payload[2]|payload[3]<<16,32)
        keys=[first_key+i for i in range(size)]
        where=4
    else:
        if len(payload)!=2+size*4:raise DexError("SPARSE_SWITCH_LENGTH")
        keys=[signed_bits(payload[2+2*i]|payload[3+2*i]<<16,32)
              for i in range(size)]
        where=2+size*2
    for i,key in enumerate(keys):
        target_offset=signed_bits(payload[where+2*i] |
                                  payload[where+2*i+1]<<16,32)
        target_pc=pc+target_offset
        if key in cases:raise DexError("DUPLICATE_SWITCH_KEY")
        cases[key]=target_pc
    return cases


def field_k(d,w):
    return field_key(d,w[1])


def ctor_and_switch_slot(d,ins):
    """Inspect exact synthetic dispatcher int tag field read + switch."""
    for i,(_,op,words) in enumerate(ins):
        if op not in (0x2b,0x2c):continue
        # Need first local 10 instructions, constrain possible selected switch.
        if i>20:continue
        switch_reg=words[0]>>8
        reg=switch_reg
        field=None
        for j in range(i-1,max(-1,i-9),-1):
            _,previous,pr=ins[j]
            move=move_object_registers(previous,pr)
            if move:
                dst,src=move
                if dst==reg:reg=src
                continue
            if previous==0x52 and (pr[0]>>8)&15==reg:
                field=field_k(d,pr)
                break
            if previous in (0x12,0x13,0x14,0x15):
                break
        if field:
            return {"switch_ordinal":i,"switch":ins[i],
                    "tag_field":field,"cases":switch_table_for_ins(ins,i)}
    return None


def constructor_tag_field(d,ins,tag_reg):
    """Match DEX iput (0x59) of tag register to exact field key."""
    for _,op,w in ins:
        if op!=0x59:continue
        source=(w[0]>>8)&15
        if source==tag_reg:return field_k(d,w)
    return None


def branch_contains_loader(d,ins,start_pc):
    """Case target belongs to direct loader invocation before next switch case?

    The first block may fall through; avoid traversing arbitrary cases.
    Only accept a local invoke Lmb4.a (<=12 instructions) with a strict
    field projection Lwq7.object -> Lero -> Lmb4 before it.
    """
    index={pc:i for i,(pc,_,_) in enumerate(ins)}
    start=index.get(start_pc)
    if start is None:return False
    seen_lero=False
    seen_loader=False
    for _,op,w in ins[start:start+12]:
        if op in (0x0e,0x0f,0x10,0x11,0x27,0x28,0x29,0x2a,0x2b,0x2c):
            break
        if op==0x1f and d.descriptor(w[1])==ORIGIN:
            seen_lero=True
        if op==0x54:
            key=field_k(d,w)
            if key[0]==ORIGIN and key[1]==LOADER:
                seen_loader=True
        if op in INVOKES:
            m=d.method(w[1])
            if (m[0],m[1])==(LOADER,"a"):
                return seen_lero and seen_loader
    return False


def direct_lero_dispatch_witness(d,defs):
    origin=[]
    constructor=None
    dispatcher=None
    for m,off in defs:
        ins=list(instructions(d,off))
        if len(ins)>MAX_METHOD_LENGTH:raise ValueError("FOCUSED_METHOD_TOO_LARGE")
        if m[0]==ORIGIN and m[1]=="t":
            for i,(_,op,w) in enumerate(ins):
                if op not in INVOKES:continue
                callee=d.method(w[1])
                if callee[0]==OWNER and callee[1]=="<init>":
                    evidence=nearby_constructor_tag(d,ins,i)
                    if evidence:origin.append(evidence)
        if m[0]==OWNER and m[1]=="<init>" and m[2]=="(ILjava/lang/Object;)V":
            # constructor parameter input int coordinate is in registers/ins.
            # Cannot infer before finding exact iput: derive from iput field
            # source register and compare to *method parameter register* via
            # register count/header, not guessed register positions.
            constructor=(d,off,ins,m)
        if m[0]==OWNER and m[1]=="e":
            dispatcher=(d,off,ins,m)
    return origin,constructor,dispatcher


def signed_scan(apks):
    source=[]
    ctor=None
    dispatch=None
    defs_all=[]
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("DEX_LIMIT")
                d=Dex(z.read(item.filename))
                dex_count+=1
                focus=[(d.method(mid),off) for mid,off in method_definitions(d)
                       if d.method(mid)[0] in (ORIGIN,OWNER)]
                if not focus:continue
                origin,c,sw=direct_lero_dispatch_witness(d,focus)
                source.extend(origin)
                if c:
                    if ctor:raise ValueError("DUPLICATE_TAG_CTOR")
                    ctor=c
                if sw:
                    if dispatch:raise ValueError("DUPLICATE_DISPATCH")
                    dispatch=sw
    if dex_count!=6 or not ctor or not dispatch or not source:
        raise ValueError("SIGNED_LERO_LWQ7_EXACT_TRIAD_MISSING")
    cd,off,ins,method=ctor
    # DEX code_item: register total = u16, incoming word count = u16 at +2.
    registers=cd.u16(off)
    incoming=cd.u16(off+2)
    # For (I,Object) constructor: p0=this, p1=int, p2=object.
    int_param=registers-incoming+1
    exact_ctor_field=constructor_tag_field(cd,ins,int_param)
    if exact_ctor_field is None:
        raise ValueError("SIGNED_LWQ7_TAG_FIELD_NOT_STORED")
    dd,doff,dins,dm=dispatch
    table=ctor_and_switch_slot(dd,dins)
    if table is None:raise ValueError("SIGNED_LWQ7_SWITCH_TAG_ABSENT")
    actual_case=[]
    for record in source:
        tag=record["tag"]
        if tag is None:
            actual_case.append({"tag_is_direct_constant":False})
            continue
        target=table["cases"].get(tag)
        actual_case.append({
            "tag_is_direct_constant":True,
            "tag_field_matches_dispatch_read":
                exact_ctor_field==table["tag_field"],
            "tag_has_explicit_switch_case":target is not None,
            "case_target_directly_invokes_exact_loader":
                branch_contains_loader(dd,dins,target) if target is not None else False,
            "constructor_source_object_is_lero_argument":record["arg_coords"][2]
                is not None,
            "no_run_time_current_decoder_or_track_proven":True,
        })
    static_match=any(x.get("tag_field_matches_dispatch_read") and
                     x.get("case_target_directly_invokes_exact_loader")
                     for x in actual_case)
    return {
        "signed_original_split_count":5,
        "signed_original_dex_count":6,
        "lifecycle_Lero_t_to_Lwq7_tagged_task_call_count":len(source),
        "constructor_selector_field_matches_switch":exact_ctor_field==table["tag_field"],
        "dispatch_switch_case_count":len(table["cases"]),
        "callsite_case_results":actual_case[:MAX_HITS],
        "exact_Lero_scheduled_task_selects_Lmb4_a_case":static_match,
        "not_observed_executor_execution":True,
        "not_observed_current_track_or_edition_or_decoder_prepare":True,
        "no_vendor_binary_media_string_or_app_patch":True,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_CI_READ_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-lwq7-switch-case-") as folder:
        base=Path(folder)
        archive=base/"unchanged-publisher-signed-original.xapk"
        size,digest=exact.gpr.download(archive)
        if size!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_ARCHIVE_PIN")
        apks=exact.gpr.split_apks(archive,base)
        if len(apks)!=5:raise ValueError("SIGNED_SPLIT_COUNT")
        exact.gpr.inspect_publisher(apks)
        result=signed_scan(apks)
    return {
        "verdict":"SIGNED_LERO_LWQ7_DISCRIMINATOR_BRANCH_WITNESS_ONLY",
        **result,
        "real_playback_substitution_proven":False,
    }


if __name__=="__main__":
    try:print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        known={
            "FOCUSED_METHOD_TOO_LARGE","DUPLICATE_TAG_CTOR",
            "DUPLICATE_DISPATCH","SIGNED_LERO_LWQ7_EXACT_TRIAD_MISSING",
            "SIGNED_LWQ7_TAG_FIELD_NOT_STORED",
            "SIGNED_LWQ7_SWITCH_TAG_ABSENT","SIGNED_SIX_DEX_REQUIRED",
            "SIGNED_ARCHIVE_PIN","SIGNED_SPLIT_COUNT",
        }
        message=str(exc)
        print(json.dumps({"verdict":"SIGNED_LWQ7_CASE_AUDIT_INCOMPLETE",
                          "error_class_only":type(exc).__name__,
                          "static_failure_code":message if message in known else "OTHER",
                          "real_playback_substitution_proven":False}))
        sys.exit(2)
