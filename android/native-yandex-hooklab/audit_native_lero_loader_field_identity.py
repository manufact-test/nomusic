#!/usr/bin/env python3
"""Exact signed Lga4.c -> Lero Lha4 -> Lmb4.<init> -> source field -> read.

Trace actual DEX *field keys*, register coordinates and full source writer
census. Local identity inside one basic block is proof; crossing separate
methods/conditional branches is static structural witness ONLY.
No vendor APK/DEX/strings/media, no current track or decoder proof.
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
from audit_native_ga4_field_receiver import field_key
from audit_native_typed_wrapper_coroutines import method_profile,brief_type
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

MAX_BODIES=230600
MAX_CALL_INS=90
MAX_WRITERS=80
MAX_METHODS=100

def basic_block_return_into_reader_ctor(d,code_off):
    """Same unmodified result register Lga4.c -> Lmb4.<init> arg p1."""
    ins=list(instructions(d,code_off))
    observations=[]
    for i,(_,op,w) in enumerate(ins):
        if op not in INVOKES or i+2>=len(ins):continue
        called=d.method(w[1])
        if called[0]!="Lga4;" or called[1]!="c" or ins[i+1][1]!=0x0c:
            continue
        original=ins[i+1][2][0]>>8
        aliases={original}
        sinks=[]
        for j in range(i+2,min(i+MAX_CALL_INS,len(ins))):
            _,current,words=ins[j]
            if current in (0x27,0x28,0x29,0x2a,0x2b,0x2c,0x0e,0x0f,0x10,0x11) or 0x32<=current<=0x3d:
                break
            if current in INVOKES:
                target=d.method(words[1])
                if target[0]=="Lmb4;" and target[1]=="<init>":
                    regs=invoke_registers(current,words)
                    for pos,reg in enumerate(regs):
                        if pos==1 and reg in aliases:
                            sinks.append({
                                "constructor":bounded_obfuscated(target),
                                "source_argument_word":pos,
                                "source_model_is_original_Lga4_c_return_in_basic_block":True,
                            })
            if current==0x5b:
                key=field_key(d,words[1])
                src=(words[0]>>8)&15
                if key[0]=="Lero;" and key[1]=="Lha4;" and src in aliases:
                    sinks.append({"source_saved_to_exact_Lero_Lha4_field":True})
            move=move_object_registers(current,words)
            if move:
                dst,src=move
                had=src in aliases
                aliases.discard(dst)
                if had:aliases.add(dst)
            elif current in (0x01,0x12,0x54):
                aliases.discard((words[0]>>8)&15)
            elif current in (0x02,0x03,0x0a,0x0b,0x0c,0x13,0x14,0x15,
                            0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x22,0x62):
                aliases.discard(words[0]>>8 if current!=0x03 else words[1])
        observations.append({
            "converter":bounded_obfuscated(called),
            "bounded_direct_target_events":sinks,
            "source_to_reader_ctor_argument_basic_block_witness":any(
                x.get("source_model_is_original_Lga4_c_return_in_basic_block")
                for x in sinks),
            "no_coroutine_or_live_player_identification":True,
        })
    return observations


def constructor_source_field(d,code_off,constructor):
    """Find exact Lmb4 Lm48 field whose value is constructor's Lha4 p1."""
    registers=d.u16(code_off)
    incoming=d.u16(code_off+2)
    p0=registers-incoming
    p1=p0+1
    slots=set()
    for _,op,w in instructions(d,code_off):
        if op==0x5b:
            src=(w[0]>>8)&15
            holder=(w[0]>>12)&15
            key=field_key(d,w[1])
            if src==p1 and holder==p0 and key[0]=="Lmb4;" and key[1]=="Lm48;":
                slots.add(key)
    if len(slots)!=1:return None
    return next(iter(slots))


def loader_source_field_reads(d,code_off,slot):
    """DEX exact typed source field loads with a following cast to Lha4."""
    ins=list(instructions(d,code_off))
    results=[]
    for i,(_,op,w) in enumerate(ins):
        if op!=0x54 or field_key(d,w[1])!=slot:continue
        result_reg=(w[0]>>8)&15
        cast=any(t==0x1f and (words[0]>>8)==result_reg and
                 d.descriptor(words[1])=="Lha4;"
                 for _,t,words in ins[i+1:i+5])
        calls=[]
        if cast:
            for j,(_,t,words) in enumerate(ins[i+1:i+55],start=i+1):
                if t not in INVOKES:continue
                m=d.method(words[1])
                if m[0]!="Lha4;" or m[1] not in ("b","read","close"):continue
                regs=invoke_registers(t,words)
                calls.append({
                    "target":bounded_obfuscated(m),
                    "same_register_coordinate_as_field_read":
                        bool(regs and regs[0]==result_reg),
                    "crossed_conditions_may_change_object_or_path":True,
                })
        results.append({
            "source_field_type":brief_type(slot[1]),
            "field_result_register":result_reg,
            "subclass_cast_to_Lha4_within_four_instructions":cast,
            "bounded_source_calls":calls[:15],
            "same_instance_across_conditionals_not_proven":True,
        })
    return results


def scan_signed(apks):
    focus={}
    all_reader_bodies=[]
    writer_candidates=[]
    num=0
    count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("DEX_FILE_BOUND")
                d=Dex(z.read(item.filename))
                num+=1
                for mid,off in method_definitions(d):
                    count+=1
                    if count>MAX_BODIES:raise ValueError("SIGNED_BODY_BOUND")
                    m=d.method(mid)
                    if (m[0],m[1]) in {
                        ("Lero;","<init>"),("Lmb4;","<init>"),("Lmb4;","a")
                    }:
                        if len(focus)>MAX_METHODS:raise ValueError("FOCUSED_BODY_BOUND")
                        focus[m]=(d,off)
                    if any(thing in m[2] for thing in ("Lmb4;",)):
                        writer_candidates.append(bounded_obfuscated(m))
    if num!=6:raise ValueError("SIGNED_SIX_DEX_EXPECTED")
    full_ctor=next(((m,d,off) for m,(d,off) in focus.items()
                    if m[0]=="Lmb4;" and m[1]=="<init>"
                    and m[2].startswith("(Lha4;La58;")),None)
    lero_ctor=next(((m,d,off) for m,(d,off) in focus.items()
                    if m[0]=="Lero;" and m[1]=="<init>"
                    and m[2].startswith("(Lwzi;Lga4;") and m[2].endswith(")V")),None)
    reader=next(((m,d,off) for m,(d,off) in focus.items()
                 if m[0]=="Lmb4;" and m[1]=="a" and m[2]=="()V"),None)
    if not full_ctor or not lero_ctor or not reader:
        raise ValueError("FOCUSED_LERO_READER_BODIES_MISSING")
    cm,cd,coff=full_ctor
    lm,ld,loff=lero_ctor
    rm,rd,roff=reader
    slot=constructor_source_field(cd,coff,cm)
    if slot is None:raise ValueError("EXACT_LMB4_SOURCE_FIELD_NOT_PROVEN")
    construction=basic_block_return_into_reader_ctor(ld,loff)
    accesses=loader_source_field_reads(rd,roff,slot)
    return {
        "publisher_original_apks":5,
        "signed_original_dex":6,
        "signed_method_bodies_scanned":count,
        "Lmb4_ctor_first_param_written_to_exact_Lm48_field":True,
        "source_result_Lga4_c_to_Lero_ctor_Lmb4":construction,
        "same_exact_Lm48_field_used_by_Lmb4_a":bool(accesses),
        "Lmb4_source_field_to_callsite_bounded":accesses,
        "original_vendor_app_unchanged":True,
        "current_trackid_edition_generation_bound":False,
        "audio_decoder_preprepare_integration_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-lero-lmb4-field-") as root:
        directory=Path(root)
        archive=directory/"publisher-original-unchanged.xapk"
        length,digest=exact.gpr.download(archive)
        if length!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_SHA_MISMATCH")
        apks=exact.gpr.split_apks(archive,directory)
        if len(apks)!=5:raise ValueError("SPLIT_COUNT_FAILED")
        exact.gpr.inspect_publisher(apks)
        return {
            "verdict":"SIGNED_LERO_LMB4_LHA4_EXACT_TYPED_FIELD_IDENTITY_ONLY",
            **scan_signed(apks),
            "no_source_url_media_dex_or_credentials_export":True,
        }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        codes={
            "FOCUSED_LERO_READER_BODIES_MISSING",
            "EXACT_LMB4_SOURCE_FIELD_NOT_PROVEN","SIGNED_SIX_DEX_EXPECTED",
            "SIGNED_BODY_BOUND","FOCUSED_BODY_BOUND",
        }
        print(json.dumps({
            "verdict":"SIGNED_LERO_LOADER_FIELD_IDENTITY_INCOMPLETE",
            "error_code":str(exc) if str(exc) in codes else type(exc).__name__,
            "audio_decoder_preprepare_integration_proven":False,
        }))
        sys.exit(2)
