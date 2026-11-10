#!/usr/bin/env python3
"""Read-only publisher-signed DEX register audit of native source factory handoff.

Provable local facts, and nothing more:
  Lcq7.i0 result of Lcq7.A -> exact primary Le48 field on Lga4;
  Lga4.d primary Le48.a result -> Lha4 constructor source argument;
  Lha4 source interface.open and parent.read callsites;
  direct (and possibly asynchronous) callers of these methods.
No current track identity, decoded sound, URL, bytecode, account or hook.
"""
from __future__ import annotations

from collections import Counter, defaultdict
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
    instructions, invoke_registers, move_object_registers
)
from audit_native_typed_wrapper_coroutines import method_profile,brief_type
from audit_native_ga4_field_receiver import field_key
from audit_native_ga4_field2_value_origins import discover_read_slot,source_register
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

# Full method descriptors also checked at runtime; never rely on bare names.
SOURCE_CANDIDATES={
    ("Lcq7;","A"),("Lcq7;","i0"),
    ("Lga4;","a"),("Lga4;","b"),("Lga4;","c"),("Lga4;","d"),
    ("Lha4;","<init>"),("Lha4;","b"),("Lha4;","f"),("Lha4;","read"),
    ("Lz3f;","a"),("Lz3f;","b"),
    ("Luiq;","a"),("Lygv;","r"),
    ("Locv;","i0"),("Lw4y;","z"),("Lfwm;","M"),
    ("Lero;","<init>"),("Lnro;","<init>"),("Llky;","<init>"),
    ("Locv;","t"),("Locv;","remove"),
    ("Lemb;","t"),("Lemb;","remove"),
}
MAX_CALLER_METHODS=75
MAX_FOCUSED_BODY_LENGTH=5000
MAX_RESULT_ROWS=40
MAX_EVENTS=20
MAX_BODIES=230600

def candidate(m):
    return (m[0],m[1]) in SOURCE_CANDIDATES

def concrete_invoke_result_to_field(dex, code_off, producer_owner, producer_name, exact_slot):
    """Straight-line local def/use only, fail closed when branches intervene.

    Object identity can be asserted *within a basic block* if the result register
    is not reassigned. Cross-method/heap/async identity is never asserted.
    """
    ins=list(instructions(dex,code_off))
    witness=[]
    for i,(pc,op,w) in enumerate(ins):
        if op not in INVOKES:continue
        target=dex.method(w[1])
        if (target[0],target[1])!=(producer_owner,producer_name):continue
        if i+1>=len(ins) or ins[i+1][1]!=0x0c:continue
        traced={ins[i+1][2][0]>>8}
        steps=[]
        for j in range(i+2,min(i+100,len(ins))):
            ip,nextop,words=ins[j]
            if nextop in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=nextop<=0x3d or nextop in (0x0e,0x0f,0x10,0x11):
                break
            if nextop==0x5b and field_key(dex,words[1])==exact_slot:
                src=(words[0]>>8)&15
                if src in traced:
                    steps.append({"sink":"exact_primary_le48_iput",
                                  "relative_instruction_count":j-i,
                                  "same_register_value":True})
            move=move_object_registers(nextop,words)
            if move:
                dst,src=move
                was=src in traced
                traced.discard(dst)
                if was:traced.add(dst)
            # These opcodes define the register and destroy a previous object.
            elif nextop in (0x0a,0x0b,0x0c,0x12,0x13,0x14,0x15,
                           0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x22,0x62):
                traced.discard(words[0]>>8)
            elif nextop==0x54:
                traced.discard((words[0]>>8)&15)
        witness.append({
            "invoke":bounded_obfuscated(target),
            "direct_primary_store_candidates":steps,
            "basic_block_register_link_observed":len(steps)>0,
            "across_coroutine_and_decoder_proven":False,
        })
    return witness[:MAX_RESULT_ROWS]


def source_constructor_argument_flow(dex, code_off):
    """Trace the Lm48 returned by primary Le48.a into Lha4.<init> argument.

    Return of the interface may be polymorphic: don't assert which concrete
    source or which async instance produced it.
    """
    ins=list(instructions(dex,code_off))
    results=[]
    for i,(_,op,w) in enumerate(ins):
        if op not in INVOKES or i+1>=len(ins) or ins[i+1][1]!=0x0c:
            continue
        method=dex.method(w[1])
        if method[0]!="Le48;" or method[1]!="a":
            continue
        source=ins[i+1][2][0]>>8
        aliases={source}
        sinks=[]
        for j in range(i+2,min(i+70,len(ins))):
            _,hop,words=ins[j]
            if hop in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=hop<=0x3d or hop in (0x0e,0x0f,0x10,0x11):
                break
            if hop in INVOKES:
                callee=dex.method(words[1])
                if callee[0]=="Lha4;" and callee[1]=="<init>":
                    for idx,reg in enumerate(invoke_registers(hop,words)):
                        if reg in aliases:
                            sinks.append({"constructor_argument_word":idx,
                                          "callee":bounded_obfuscated(callee)})
            move=move_object_registers(hop,words)
            if move:
                dst,src=move
                current=src in aliases
                aliases.discard(dst)
                if current:aliases.add(dst)
            elif hop in (0x0a,0x0b,0x0c,0x12,0x13,0x14,0x15,
                        0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x22,0x62):
                aliases.discard(words[0]>>8)
            elif hop==0x54:
                aliases.discard((words[0]>>8)&15)
        results.append({
            "producer":bounded_obfuscated(method),
            "same_basic_block_construction_argument_sites":sinks[:MAX_EVENTS],
            "polymorphic_receiver_class_proven":False,
        })
    return results[:MAX_RESULT_ROWS]


def source_method_callers(apks):
    """Whole six-DEX direct invoke-site census, bounded selected methods only."""
    rows=defaultdict(set)
    focused=[]
    scanned=0
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for e in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",e.filename):continue
                if e.file_size>DEX_MAX:raise ValueError("DEX_SIZE_LIMIT")
                d=Dex(z.read(e.filename))
                dex_count+=1
                for mid,off in method_definitions(d):
                    scanned+=1
                    if scanned>MAX_BODIES:raise ValueError("METHOD_BODY_BOUND")
                    caller=d.method(mid)
                    ins=list(instructions(d,off))
                    if len(ins)>MAX_FOCUSED_BODY_LENGTH and candidate(caller):
                        raise ValueError("FOCUSED_SOURCE_METHOD_TOO_LARGE")
                    found=set()
                    for _,op,w in ins:
                        if op not in INVOKES:continue
                        callee=d.method(w[1])
                        if candidate(callee):found.add(callee)
                    for item in found:rows[item].add(caller)
    if dex_count!=6:
        raise ValueError("PINNED_SIX_DEX_EXPECTED")
    summaries=[{
        "method":method_profile(target),
        "callers":len(callers),
        "caller_hints":[bounded_obfuscated(m) for m in sorted(callers)[:MAX_RESULT_ROWS]],
        "runtime_same_track_proven":False,
    } for target,callers in sorted(rows.items())]
    return {
        "signed_defined_method_bodies_scanned":scanned,
        "target_callee_descriptors":len(summaries),
        "candidate_direct_callers":summaries,
        "callback_dispatch_and_coroutine_resumption_not_modelled":True,
    }


def source_local_witness(apks,primary):
    target={
        ("Lcq7;","i0"),("Lga4;","d"),("Lha4;","f"),
        ("Lha4;","read"),("Lz3f;","a"),("Luiq;","a"),
    }
    found={}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for e in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",e.filename):continue
                d=Dex(z.read(e.filename))
                for mid,off in method_definitions(d):
                    method=d.method(mid)
                    if (method[0],method[1]) not in target:continue
                    if method in found:raise ValueError("DUPLICATE_METHOD")
                    ins=list(instructions(d,off))
                    direct=[{
                        "method":bounded_obfuscated(d.method(w[1])),
                        "callee_profile":method_profile(d.method(w[1])),
                    } for _,op,w in ins if op in INVOKES and
                        d.method(w[1])[0] in ("Le48;","Lm48;","Lv38;","Lha4;","Lz3f;")]
                    rec={
                        "method":method_profile(method),
                        "instruction_count":len(ins),
                        "focused_source_interface_invokes":direct[:MAX_EVENTS],
                        "exact_current_track_or_decoder_proven":False,
                    }
                    if method[0]=="Lcq7;" and method[1]=="i0":
                        # Every matching (DEX-private) field slot has SAME
                        # logical key across splits, unlike raw field index.
                        rec["source_factory_result_to_primary_field"] = concrete_invoke_result_to_field(
                            d,off,"Lcq7;","A",next(iter(primary)))
                    if method[0]=="Lga4;" and method[1]=="d":
                        rec["primary_factory_result_to_source_constructor"]=source_constructor_argument_flow(d,off)
                    found[method]=rec
    if not any(m[0]=="Lcq7;" and m[1]=="i0" for m in found):
        raise ValueError("SOURCE_FACTORY_NOT_FOUND")
    if not any(m[0]=="Lga4;" and m[1]=="d" for m in found):
        raise ValueError("SOURCE_WRAPPER_NOT_FOUND")
    return {
        "focused_source_methods":len(found),
        "method_witnesses":[v for _,v in sorted(found.items())],
        "same_current_track_identity_not_proven":True,
    }


def scan_signed(apks):
    primary=discover_read_slot(apks,reader_method="d")
    secondary=discover_read_slot(apks,reader_method="c")
    if not primary or primary==secondary:raise ValueError("PRIMARY_LE48_FIELD_UNSAFE")
    local=source_local_witness(apks,primary)
    exact=next(row for row in local["method_witnesses"] if
               row["method"]["owner"]=="Lcq7;" and row["method"]["method"]=="i0")
    factory=exact["source_factory_result_to_primary_field"]
    if not any(x["basic_block_register_link_observed"] for x in factory):
        raise ValueError("NO_SIGNED_PRIMARY_FACTORY_REGISTER_LINK")
    wrapper=next(row for row in local["method_witnesses"] if
               row["method"]["owner"]=="Lga4;" and row["method"]["method"]=="d")
    if not any(x["same_basic_block_construction_argument_sites"] for x in
               wrapper["primary_factory_result_to_source_constructor"]):
        raise ValueError("NO_SIGNED_SOURCE_WRAPPER_REGISTER_LINK")
    return {
        "original_signed_apk_count":5,
        "original_signed_dex_count":6,
        "exact_source_factory_basic_block_witness":True,
        "exact_source_interface_return_to_wrapper_constructor_witness":True,
        "source_local_flow":local,
        "six_dex_callers":source_method_callers(apks),
        "no_vendor_apk_modified_or_exported":True,
        "actual_audio_source_for_active_track_identified":False,
        "pre_decoder_prepare_binding_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("SIGNED_PUBLISHER_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-pinned-source-obj-handoff-") as td:
        tmp=Path(td)
        original=tmp/"original-signed-unchanged.xapk"
        length,sha=exact.gpr.download(original)
        if length!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_APK_HASH_MISMATCH")
        apks=exact.gpr.split_apks(original,tmp)
        if len(apks)!=5:raise ValueError("EXPECTED_FIVE_SPLITS")
        exact.gpr.inspect_publisher(apks)
        report=scan_signed(apks)
    return {
        "verdict":"SIGNED_NATIVE_BASIC_BLOCK_SOURCE_FACTORY_AND_OBFUSCATED_OPEN_WITNESSES",
        "publisher_original":"2026.10.3 #170gpr",
        **report,
        "no_drm_signature_playprotect_workaround":True,
        "no_current_live_audio_or_user_media_access":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,OSError,DexError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_SOURCE_FACTORY_LOCAL_FLOW_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "actual_audio_source_for_active_track_identified":False,
        }))
        sys.exit(2)
