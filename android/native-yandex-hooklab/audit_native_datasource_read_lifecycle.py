#!/usr/bin/env python3
"""Publisher-signed Yandex native source: actual Lha4 open/read callsite consumers.

Unlike a global call graph, this studies exact signed Lmb4.a source lifetime
at concrete invoke ordinals, plus source lifecycle implementors Lero/Locv.
No playback or decoder evidence is inferred from static caller adjacency.
No APK/DEX/code bytes, URLs, strings, accounts or media exported.
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
from audit_native_register_bridge import (
    instructions,invoke_registers,move_object_registers
)
from audit_native_ga4_field2_value_origins import safe_operand_metadata
from audit_native_typed_wrapper_coroutines import method_profile,brief_type
from audit_native_media_implementors import relations,transitive_implementors
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

READ_METHODS={("Lha4;","read"),("Lv38;","read")}
OPEN_METHODS={("Lha4;","b"),("Lm48;","b")}
CLOSE_METHODS={("Lha4;","close"),("Lha4;","d"),("Lm48;","close")}
INTERESTING_CALLS=READ_METHODS|OPEN_METHODS|CLOSE_METHODS
LIFECYCLE_OWNERS={"Lmb4;","Lha4;","Lmir;","Lero;","Locv;","Lemb;","Lcq7;","Lga4;","Loi;","Llir;","Lwq7;"}
TARGET_METHODS={
 ("Lmb4;","a"),("Lmb4;","<init>"),("Lmb4;","b"),
 ("Lha4;","b"),("Lha4;","f"),("Lha4;","read"),("Lha4;","close"),("Lha4;","d"),
 ("Lero;","<init>"),("Lero;","t"),("Lero;","remove"),
 ("Locv;","<init>"),("Locv;","t"),("Locv;","remove"),("Locv;","i0"),
 ("Lmir;","t"),("Lmir;","remove"),("Lmir;","a"),
 ("Llir;","e"),("Loi;","invokeSuspend"),("Lwq7;","e"),
}
MAX_SAFE_WINDOW=13
MAX_FOCUSED_METHODS=100
MAX_CALLSITE_ROWS=80
MAX_GRAPH_METHODS=240000
MAX_METHOD_INPUT_SHAPES=115

def safe_events_for_call(d,ins,i):
    """Local callsite window in instruction ordinals; no private values.

    Interleaving at async or switch is UNKNOWN and never inferred from
    two co-occurring calls even when both occur inside the same method.
    """
    pc,op,w=ins[i]
    callee=d.method(w[1])
    regs=invoke_registers(op,w)
    before=[{
        "relative_ordinal":j-i,
        **safe_operand_metadata(d,ins[j][1],ins[j][2])
    } for j in range(max(0,i-MAX_SAFE_WINDOW),i)]
    after=[{
        "relative_ordinal":j-i,
        **safe_operand_metadata(d,ins[j][1],ins[j][2])
    } for j in range(i+1,min(len(ins),i+MAX_SAFE_WINDOW+1))]
    return {
        "callee":method_profile(callee),
        "invoke_ordinal":i,
        "register_arguments":regs[:12],
        "preceding_safe_roles":before,
        "following_safe_roles":after,
        "requires_control_flow_and_runtime_validation":True,
        "actual_audio_decoding_witness":False,
    }


def short_relatives(d,ins,targets=INTERESTING_CALLS):
    out=[]
    for i,(_,op,w) in enumerate(ins):
        if op not in INVOKES:continue
        called=d.method(w[1])
        if (called[0],called[1]) not in targets:continue
        out.append(safe_events_for_call(d,ins,i))
        if len(out)>MAX_CALLSITE_ROWS:raise ValueError("TOO_MANY_CALLS")
    return out


def source_field_load_to_call(d,ins,i,scan_limit=20):
    """Register coordinate evidence for source receiver, not object identity."""
    _,op,w=ins[i]
    target=d.method(w[1])
    args=invoke_registers(op,w)
    if not args:return {"receiver_loaded_from_field_in_same_basic_block":False}
    receiver=args[0]
    origin=receiver
    for j in range(i-1,max(-1,i-scan_limit-1),-1):
        _,op,words=ins[j]
        if op in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            break
        move=move_object_registers(op,words)
        if move:
            dst,src=move
            if dst==origin:origin=src
            continue
        if op==0x54 and ((words[0]>>8)&15)==origin:
            from audit_native_ga4_field_receiver import field_key
            key=field_key(d,words[1])
            return {
                "receiver_loaded_from_field_in_same_basic_block":True,
                "field_declaring_type":brief_type(key[0]),
                "field_value_type":brief_type(key[1]),
                "field_read_precedes_invoke_by_instructions":i-j,
                "same_object_through_heap_not_proven":True,
            }
        if op in (0x01,0x12) and ((words[0]>>8)&15)==origin:
            break
        if op in (0x0c,0x22,0x62) and (words[0]>>8)==origin:
            break
    return {"receiver_loaded_from_field_in_same_basic_block":False}


def typed_callsite_facts(d,ins):
    out=[]
    for i,(_,op,w) in enumerate(ins):
        if op not in INVOKES:continue
        m=d.method(w[1])
        if (m[0],m[1]) not in INTERESTING_CALLS:continue
        out.append({
            "callsite":safe_events_for_call(d,ins,i),
            "receiver_origin":source_field_load_to_call(d,ins,i),
            "same_method_order_not_guaranteed_runtime_order":True,
        })
        if len(out)>MAX_CALLSITE_ROWS:raise ValueError("SOURCE_CALLSITE_BOUND")
    return out




def bounded_lifecycle_method_shape(d,m,ins):
    """First safe method roles; redacts strings, constants, URLs, bytecode.

    Helps bind the Lha4 instance passed to Lmb4 constructor to fields
    used by Lmb4.a without assuming conditional runtime execution.
    """
    selected=(m[0] in {"Lero;","Lmb4;","Llir;","Loi;","Lwq7;"})
    if not selected:return []
    cap=(115 if m[0] in ("Lmb4;","Lero;") else 55)
    roles=[]
    for i,(_,op,w) in enumerate(ins[:cap]):
        info=safe_operand_metadata(d,op,w)
        if info["kind"]=="other":continue
        roles.append({"ordinal":i,**info})
    return roles[:MAX_METHOD_INPUT_SHAPES]


def exact_source_register_reuse(facts, method):
    """Four callsites may use the same receiver register, NOT live object proof."""
    if method[0]!="Lmb4;" or method[1]!="a":return {}
    candidates=defaultdict(set)
    for event in facts:
        called=event["callsite"]["callee"]
        key=called["owner"]+"->"+called["method"]
        words=event["callsite"]["register_arguments"]
        if words:candidates[key].add(words[0])
    opens=candidates.get("Lha4;->b",set())
    reads=candidates.get("Lha4;->read",set())
    closes=candidates.get("Lha4;->close",set())
    same=bool(opens and reads and closes and opens==reads==closes)
    return {
        "site_receiver_register_sets":{k:sorted(v) for k,v in sorted(candidates.items())},
        "all_open_read_close_callsite_receiver_registers_identical":same,
        "register_identity_across_branches_not_live_object_identity":True,
        "decoder_or_active_track_proven":False,
    }


def inspect_signed(apks):
    dex_count=0
    total_bodies=0
    hierarchy={}
    target_bodies={}
    direct_caller_edges=defaultdict(set)
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("SIGNED_DEX_BOUND")
                d=Dex(z.read(item.filename))
                dex_count+=1
                local_rel=relations(d)
                if set(hierarchy)&set(local_rel):raise ValueError("DUPLICATE_SIGNED_CLASS")
                hierarchy.update(local_rel)
                for mid,off in method_definitions(d):
                    total_bodies+=1
                    if total_bodies>MAX_GRAPH_METHODS:raise ValueError("METHOD_COUNT_BOUND")
                    m=d.method(mid)
                    ins=list(instructions(d,off))
                    edges={d.method(w[1]) for _,op,w in ins if op in INVOKES and
                           (d.method(w[1])[0],d.method(w[1])[1]) in
                           INTERESTING_CALLS|TARGET_METHODS}
                    for callee in edges:direct_caller_edges[callee].add(m)
                    if (m[0],m[1]) not in TARGET_METHODS:continue
                    if m in target_bodies:raise ValueError("DUPLICATE_TARGET_DEF")
                    if len(target_bodies)>=MAX_FOCUSED_METHODS:raise ValueError("TARGET_METHOD_BOUND")
                    direct=[{
                        "callee":bounded_obfuscated(d.method(w[1])),
                        "method":method_profile(d.method(w[1])),
                    } for _,op,w in ins if op in INVOKES and
                       d.method(w[1])[0] in LIFECYCLE_OWNERS]
                    callsite_facts=typed_callsite_facts(d,ins)
                    target_bodies[m]={
                        "method":method_profile(m),
                        "method_start_bounded_safe_roles":bounded_lifecycle_method_shape(d,m,ins),
                        "source_open_read_close_receiver_set":exact_source_register_reuse(callsite_facts,m),
                        "instruction_count":len(ins),
                        "branch_count":sum(op in (0x2b,0x2c) or 0x32<=op<=0x3d
                                           for _,op,_ in ins),
                        "source_open_read_close_calls":callsite_facts,
                        "lifecycle_class_calls":direct[:48],
                        "player_decoder_owner_or_selected_track_proven":False,
                    }
    if dex_count!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    if not any(m[0]=="Lmb4;" and m[1]=="a" for m in target_bodies):
        raise ValueError("SIGNED_READ_CONSUMER_MISSING")
    if not any(m[0]=="Lero;" and m[1]=="t" for m in target_bodies):
        raise ValueError("SIGNED_LIFECYCLE_SOURCE_MISSING")
    m48="Lm48;"
    emb="Lemb;"
    return {
        "publisher_original_apks":5,
        "signed_dex_count":dex_count,
        "signed_defined_bodies_scanned":total_bodies,
        "lifecycle_interface_parent_map":[{
            "type":brief_type(owner),
            "parents":[brief_type(p) for p in hierarchy.get(owner,(0,()))[1]],
            "reference_only_not_runtime_dispatch":True,
        } for owner in sorted(LIFECYCLE_OWNERS)],
        "Lemb_concrete_implementors":[brief_type(x) for x in
             transitive_implementors(hierarchy,emb)[:40]],
        "Lm48_implementor_count":len(transitive_implementors(hierarchy,m48)),
        "selected_signed_method_bodies":[v for _,v in sorted(target_bodies.items())],
        "direct_static_source_callers":[{
            "callee":method_profile(m),
            "distinct_direct_caller_count":len(callers),
            "bounded_caller_hints":[bounded_obfuscated(c) for c in
                                    sorted(callers)[:30]],
            "runtime_direct_dispatch_or_decoder_selected":False,
        } for m,callers in sorted(direct_caller_edges.items())[:150]],
        "cannot_establish_live_exoplayer_source_prepare":True,
        "cannot_establish_trackid_edition_generation_object_identity":True,
        "no_vendor_apk_patch_or_output":True,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("CI_SIGNED_ORIGINAL_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-signed-read-lifecycle-") as name:
        root=Path(name)
        archive=root/"original-publisher-unchanged.xapk"
        length,digest=exact.gpr.download(archive)
        if length!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("ORIGINAL_SIGNED_PIN_MISMATCH")
        splits=exact.gpr.split_apks(archive,root)
        if len(splits)!=5:raise ValueError("SIGNED_SPLIT_COUNT_MISMATCH")
        exact.gpr.inspect_publisher(splits)
        data=inspect_signed(splits)
    return {
        "verdict":"SIGNED_NATIVE_DATASOURCE_LIFECYCLE_READ_CONSUMER_STATIC_ONLY",
        **data,
        "no_private_strings_tokens_uris_or_audio_export":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_SOURCE_READ_LIFECYCLE_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "cannot_establish_live_exoplayer_source_prepare":True,
        }))
        sys.exit(2)
