#!/usr/bin/env python3
"""Signed native audio candidate: exact callers and bounded result propagation.

Investigate the only two direct Lcq7.i0 callers and the only Lha4
constructor caller, then classify the resulting models without inferring
the runtime-selected audio player. No bytecode/URL/strings/users exported.
"""
from __future__ import annotations

from collections import defaultdict
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
from audit_native_register_bridge import (instructions, move_object_registers,
    invoke_registers, instruction_successors)
from audit_native_ga4_field_receiver import field_key
from audit_native_typed_wrapper_coroutines import (
    method_profile,profile_tracked_results,brief_type
)
from audit_native_ga4_field2_value_origins import safe_operand_metadata
from audit_native_media_implementors import relations
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

FOCUS={
 ("Lcq7;","D"),("Lcq7;","T"),
 ("Lcq7;","i0"),("Lo4y;","c"),("Locv;","i0"),
 ("Lga4;","b"),("Lga4;","c"),("Lga4;","d"),
 ("Lmir;","t"),("Lmir;","remove"),
 ("Lero;","<init>"),("Lmb4;","a"),
 ("Ldl8;","a"),("Lbr1;","invoke"),("Lx3f;","invokeSuspend")
}
PRODUCERS={
 ("Lcq7;","A"),("Lcq7;","i0"),
 ("Lga4;","a"),("Lga4;","b"),("Lga4;","c"),("Lga4;","d"),
 ("Le48;","a"),("Luiq;","a"),
 ("Lz3f;","a"),("Lz3f;","b"),
}
MAX_METHOD_BODIES=80
MAX_OUTLINE=60
MAX_CALLS=32
MAX_TARGET_WINDOW=38


def relevant(m):
    return (m[0],m[1]) in FOCUS


def invocation_windows(d,ins,producer):
    """Only safe op family, register coordinates, and class/method hints."""
    windows=[]
    for i,(pc,op,w) in enumerate(ins):
        if op not in INVOKES or (d.method(w[1])[0],d.method(w[1])[1]) not in producer:
            continue
        reg_roles=[{
            "ordinal":i+k,
            **safe_operand_metadata(d,hop,words)
        } for k,(_,hop,words) in enumerate(
            ins[i:min(len(ins),i+MAX_TARGET_WINDOW)])]
        windows.append({
            "called":bounded_obfuscated(d.method(w[1])),
            "invoke_ordinal":i,
            "opcode_window":reg_roles,
            "may_cross_branch_or_async_execution":True,
        })
    return windows[:MAX_CALLS]



def source_wrapper_field_projections(d,code_off):
    """Track the FIELD VALUE, never the Lcq7.i0 wrapper object itself.

    Explicit iget-object is a heap projection. Only the projected register
    is propagated on a bounded CFG with branch uncertainty. A matching
    invocation is a POSSIBLE conditional path, not a live player instance.
    """
    ins=list(instructions(d,code_off))
    positions={pc:i for i,(pc,_,_) in enumerate(ins)}
    result=[]
    for i,(_,op,w) in enumerate(ins):
        if op not in INVOKES or i+2>=len(ins) or ins[i+1][1]!=0x0c:
            continue
        called=d.method(w[1])
        if (called[0],called[1])!=("Lcq7;","i0"):
            continue
        wrapper_reg=ins[i+1][2][0]>>8
        # Each direct field projection of the returned wrapper within a
        # short basic-block window is independently qualified.
        for j in range(i+2,min(i+12,len(ins))):
            _,hop,words=ins[j]
            if hop in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=hop<=0x3d:
                break
            if hop!=0x54:
                continue
            input_reg=(words[0]>>12)&15
            if input_reg!=wrapper_reg:
                continue
            dst=(words[0]>>8)&15
            field=field_key(d,words[1])
            work=[(ins[j+1][0],frozenset({dst}),False,0)] if j+1<len(ins) else []
            visited=set()
            events=set()
            truncated=False
            while work:
                pc,aliases,crossed_branch,depth=work.pop()
                state=(pc,aliases,crossed_branch)
                if state in visited:continue
                visited.add(state)
                if len(visited)>12000 or depth>220:
                    truncated=True
                    continue
                k=positions.get(pc)
                if k is None:continue
                cur_pc,opcode,params=ins[k]
                regs=set(aliases)
                if opcode in INVOKES:
                    method=d.method(params[1])
                    for word_idx,reg in enumerate(invoke_registers(opcode,params)):
                        if reg in regs and (method[0] in {
                            "Lero;","Lnro;","Lmir;","Lga4;","Le48;"
                        } or method[0].startswith("Landroidx/media3/")):
                            events.add((
                                bounded_obfuscated(method),word_idx,
                                crossed_branch))
                move=move_object_registers(opcode,params)
                if move:
                    dest,source=move
                    has=source in regs
                    regs.discard(dest)
                    if has:regs.add(dest)
                elif opcode in (0x01,0x12,0x54):
                    regs.discard((params[0]>>8)&15)
                elif opcode==0x03:
                    regs.discard(params[1])
                elif opcode in (0x02,0x0a,0x0b,0x0c,0x13,0x14,0x15,
                               0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,
                               0x22,0x62,0x63,0x64):
                    regs.discard(params[0]>>8)
                if not regs or k+1>=len(ins):continue
                nxt=ins[k+1][0]
                nexts=instruction_successors(cur_pc,opcode,params,nxt)
                for successor in nexts:
                    if successor in positions:
                        work.append((successor,frozenset(regs),
                                     crossed_branch or 0x32<=opcode<=0x3d
                                     or opcode in (0x2b,0x2c),depth+1))
            cast_types=[]
            for _,nextop,nextwords in ins[j+1:min(j+7,len(ins))]:
                if nextop==0x1f and nextwords[0]>>8==dst:
                    cast_types.append(brief_type(d.descriptor(nextwords[1])))
            result.append({
                "source_producer":"Lcq7;->i0",
                "wrapper_result_word_register":wrapper_reg,
                "projection_declared_owner":brief_type(field[0]),
                "projection_declared_type":brief_type(field[1]),
                "projection_cast_types":cast_types,
                "distinct_object_identity_from_wrapper":True,
                "projected_field_may_flow_events":[{
                    "callee":callee,"argument_word":arg,
                    "conditional_branch_crossed":branched,
                    "actual_runtime_call_proven":False
                } for callee,arg,branched in sorted(events)[:MAX_EVENTS]],
                "bounded_cfg_truncated":truncated,
                "runtime_active_track_proven":False,
            })
    return result[:MAX_CALLS]


def class_ancestry(rel,owner):
    parents=rel.get(owner,(0,()))[1]
    return {
        "direct_parents":[brief_type(p) for p in parents],
        "runtime_player_instance_proven":False,
    }


def inspect_targets(apks):
    definitions={}
    matching=set()
    dex_count=0
    rel={}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for e in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",e.filename):continue
                if e.file_size>DEX_MAX:raise ValueError("DEX_SIZE_BOUND")
                d=Dex(z.read(e.filename))
                dex_count+=1
                relationships=relations(d)
                if set(rel)&set(relationships):raise ValueError("DUPLICATE_DEX_CLASSES")
                rel.update(relationships)
                for mid,off in method_definitions(d):
                    m=d.method(mid)
                    if not relevant(m):continue
                    if m in definitions:raise ValueError("DUPLICATE_TARGET_DEF")
                    if len(definitions)>MAX_METHOD_BODIES:raise ValueError("TOO_MANY_FOCUSED_METHODS")
                    ins=list(instructions(d,off))
                    interesting={d.method(w[1]) for _,op,w in ins
                        if op in INVOKES and (d.method(w[1])[0],d.method(w[1])[1]) in PRODUCERS}
                    result_flow=profile_tracked_results(d,off,interesting) if interesting else []
                    profiles=[{
                        "called":method_profile(d.method(w[1])),
                        "invoke_ordinal":i,
                    } for i,(_,op,w) in enumerate(ins) if op in INVOKES and
                        (d.method(w[1])[0] in {
                         "Lcq7;","Lga4;","Le48;","Luiq;","Lm48;","Lv38;",
                         "Lro7;","Lfxc;","Lwxc;","Lyzt;"
                        } or "Landroidx/media3/" in d.method(w[1])[0])]
                    record={
                        "method":method_profile(m),
                        "instruction_count":len(ins),
                        "branch_count":sum(op in (0x2b,0x2c) or 0x32<=op<=0x3d for _,op,_ in ins),
                        "direct_typed_source_calls":profiles[:MAX_OUTLINE],
                        "producer_result_mayflow":result_flow[:MAX_OUTLINE],
                        "wrapper_field_projection":source_wrapper_field_projections(d,off)
                        if m[0] in ("Lo4y;","Locv;") else [],
                        "callee_windows":invocation_windows(d,ins,PRODUCERS),
                        "named_exoplayer_owner_direct_invoked":any(
                          d.method(w[1])[0] in {"Lro7;","Lfxc;","Lwxc;","Lyzt;"}
                          for _,op,w in ins if op in INVOKES),
                        "end_to_end_source_flow_proven":False,
                    }
                    definitions[m]=record
                    matching.add((m[0],m[1]))
    if dex_count!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    if not {("Lo4y;","c"),("Locv;","i0")}.issubset(matching):
        raise ValueError("EXPECTED_I0_CALLERS_MISSING")
    profiles=[{
        **row,
        "class_hierarchy":class_ancestry(rel,m[0])
    } for m,row in sorted(definitions.items())]
    return {
        "original_signed_apks":5,"original_signed_dex":6,
        "focused_defined_methods":len(definitions),
        "source_factory_direct_caller_method_profiles":profiles,
        "no_source_selection_or_active_decoder_proven":True,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_READ_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-signed-actual-source-callers-") as td:
        base=Path(td)
        original=base/"publisher-unchanged-original.xapk"
        size,sha=exact.gpr.download(original)
        if size!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_ORIGINAL_SHA_FAILED")
        splits=exact.gpr.split_apks(original,base)
        if len(splits)!=5:raise ValueError("ORIGINAL_SPLITS_FAILED")
        exact.gpr.inspect_publisher(splits)
        data=inspect_targets(splits)
    return {
        "verdict":"SIGNED_LCQ7_I0_CALLERS_AND_SOURCE_CONSUMER_REGISTERS_ONLY",
        **data,
        "no_vendor_patch_apk_or_data_export":True,
        "actual_source_decoder_prepare_proven":False,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,DexError,zipfile.BadZipFile) as exc:
        print(json.dumps({"verdict":"SIGNED_I0_CALLER_AUDIT_INCOMPLETE",
                          "error_class_only":type(exc).__name__,
                          "actual_source_decoder_prepare_proven":False}))
        sys.exit(2)
