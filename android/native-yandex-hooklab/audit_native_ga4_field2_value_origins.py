#!/usr/bin/env python3
"""Immutable, publisher-signed six-DEX field-2 writer value origin investigation.

Determine the exact Le48 field slot read by Lga4.c (do NOT confuse two
fields with the same declared type), find every direct writer, and trace
the immediate source register backwards to a concrete constructor,
method return, field read, or argument. No class literals/URLs/bytecode
are emitted; only bounded type and invoke summaries. This is not an
interprocedural or runtime player-source witness.
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
from inspect_android_host import Dex, DexError, DEX_MAX
from trace_native_callers import method_definitions, INVOKES
from audit_native_register_bridge import instructions, move_object_registers
from audit_native_ga4_field_receiver import field_key, CLASS, FIELD_TYPE
from audit_native_typed_wrapper_coroutines import brief_type, method_profile
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

MAX_TRAVERSE=100
MAX_RESULT=40
BARRIERS={0x27,0x28,0x29,0x2a,0x2b,0x2c}|set(range(0x32,0x3e))
OBJECT_GETS={0x54,0x62}
# Include object move and every common result/constant/new-object form. Treat
# unhandled opcodes as possible register clobbers; no false certain types.
SIMPLE_REG_WRITES={0x0a,0x0b,0x0c,0x12,0x13,0x14,0x15,
                   0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,
                   0x22,0x54,0x62}
OBJECT_CASTS={0x1f}
OPAQUE_WRITES={0x01,0x02,0x03,0x04,0x05,0x06,
               0x0a,0x0b,0x0c,0x12,0x13,0x14,0x15,
               0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,
               0x22,0x54,0x62,0x63,0x64,0x65,0x66,0x67,0x68}
MOVE_OPS={0x07,0x08,0x09}


def limited_method(m):
    return bounded_obfuscated(m)


def source_register(op,words):
    if op==0x5b:return (words[0]>>8)&15
    if op==0x69:return words[0]>>8
    raise DexError("NOT_OBJECT_STORE")


def destination_reg(op, words):
    if op in (0x01,0x04,0x07):
        return (words[0]>>8)&15
    if op in (0x02,0x05,0x08,0x03,0x06,0x09):
        return words[0]>>8 if op in (0x02,0x05,0x08) else words[1]
    if op==0x54 or op==0x12:
        return (words[0]>>8)&15
    if op in OPAQUE_WRITES:
        return words[0]>>8
    return None


def find_definition(dex, ins, before, reg, max_traverse=MAX_TRAVERSE):
    """A strictly local backwards def-use slice in a SINGLE straight-line run.

    Any branch/switch/throw encountered makes the result speculative; stop
    rather than accidentally joining across incompatible basic blocks.
    """
    visited=set()
    source=reg
    depth=0
    seen_casts=[]
    for j in range(before-1,max(-1,before-max_traverse-1),-1):
        pc,op,words=ins[j]
        depth+=1
        if op in BARRIERS or op in (0x0e,0x0f,0x10,0x11):
            return {
                "kind":"control_flow_boundary",
                "steps":depth,
                "register_copy_hops":len(visited),
                "cast_type_hints":seen_casts[:8],
                "direct_producer_unambiguous":False,
            }
        if op in OBJECT_CASTS and (words[0]>>8)==source:
            seen_casts.append(brief_type(dex.descriptor(words[1])))
            continue
        moved=move_object_registers(op,words)
        if moved is not None:
            dst,orig=moved
            if dst==source:
                source=orig
                visited.add((j,source))
            continue
        dst=destination_reg(op,words)
        if dst!=source:
            continue
        result={
            "steps":depth,
            "register_copy_hops":len(visited),
            "cast_type_hints":seen_casts[:8],
            "direct_producer_unambiguous":False, # no interprocedural identity
        }
        if op==0x22:
            result.update({
                "kind":"new_instance",
                "inferred_type":brief_type(dex.descriptor(words[1])),
            })
        elif op in OBJECT_GETS:
            key=field_key(dex,words[1])
            result.update({
                "kind":"instance_field_read" if op==0x54 else "static_field_read",
                "field_owner":brief_type(key[0]),
                "field_type":brief_type(key[1]),
            })
        elif op==0x0c:
            if j and ins[j-1][1] in INVOKES:
                producer=dex.method(ins[j-1][2][1])
                result.update({
                    "kind":"invoke_result",
                    "producer":limited_method(producer),
                    "producer_profile":method_profile(producer),
                })
            else:
                result.update({"kind":"unpaired_move_result"})
        elif op in (0x01,0x02,0x03,0x04,0x05,0x06):
            result.update({"kind":"primitive_move_not_object"})
        else:
            result.update({"kind":"unknown_register_definition",
                           "opcode_family":"opaque"})
        return result
    code_off=ins[0][0] if ins else 0
    return {
        "kind":"incoming_register_or_long_distance",
        "steps":depth,
        "register_copy_hops":len(visited),
        "cast_type_hints":seen_casts[:8],
        "direct_producer_unambiguous":False,
    }


def exact_store_witnesses(dex,code_off,slot_keys):
    """Site-specific evidence for a pre-discovered exact field slot."""
    ins=list(instructions(dex,code_off))
    out=[]
    branch_count=sum(op in BARRIERS for _,op,_ in ins)
    for i,(pc,op,words) in enumerate(ins):
        if op!=0x5b:
            continue
        key=field_key(dex,words[1])
        if key not in slot_keys:continue
        src=source_register(op,words)
        provenance=find_definition(dex,ins,i,src)
        before=[{
            "family":("branch" if o in BARRIERS else
                      "iget-object" if o==0x54 else
                      "new-instance" if o==0x22 else
                      "move-object" if o in MOVE_OPS else
                      "move-result-object" if o==0x0c else
                      "invoke" if o in INVOKES else "other")
        } for _,o,_ in ins[max(0,i-6):i]]
        out.append({
            "_slot":key,
            "value_provenance":provenance,
            "method_total_instruction_count":len(ins),
            "branch_or_switch_opcode_count":branch_count,
            "nearby_pre_store_instruction_families":before,
            "exact_current_audio_receiver_proven":False,
        })
        if len(out)>MAX_RESULT:raise ValueError("WRITES_PER_METHOD_LIMIT")
    return out


def discover_read_slot(apks):
    """Determine field by actual read and invoke in Lga4.c, not alphabetical order."""
    candidates=set()
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if not re.fullmatch(r"classes[0-9]*\.dex",name):continue
                d=Dex(z.read(name))
                for mid,coff in method_definitions(d):
                    owner,meth,_=d.method(mid)
                    if owner!=CLASS or meth!="c":continue
                    ins=list(instructions(d,coff))
                    for i,(_,op,words) in enumerate(ins):
                        if op!=0x54:continue
                        key=field_key(d,words[1])
                        if key[0]!=CLASS or key[1]!=FIELD_TYPE:continue
                        register=(words[0]>>8)&15
                        for _,following,following_words in ins[i+1:i+5]:
                            if following in (0x72,0x78):
                                called=d.method(following_words[1])
                                if called[0]==FIELD_TYPE and called[1]=="a":
                                    from audit_native_register_bridge import invoke_registers
                                    if register in invoke_registers(following,following_words):
                                        candidates.add(key)
    if len(candidates)!=1:
        raise ValueError("EXACT_LE48_RECEIVER_SLOT_AMBIGUOUS")
    return candidates



def safe_operand_metadata(dex, op, words):
    """DEX register *coordinates* and safe type hints, never constant values."""
    from audit_native_register_bridge import invoke_registers
    from audit_native_typed_wrapper_coroutines import safe_instruction_shape
    role=safe_instruction_shape(dex,op,words)
    if op in INVOKES:
        role["argument_register_coordinates"]=invoke_registers(op,words)
    elif op in MOVE_OPS:
        moved=move_object_registers(op,words)
        role["copy_dest"],role["copy_source"]=moved
    elif op in (0x22,0x0c,0x62):
        role["result_register"]=words[0]>>8
    elif op in (0x1f,):
        role["cast_register"]=words[0]>>8
    elif op==0x54:
        role["result_register"]=(words[0]>>8)&15
        role["object_register"]=words[0]>>12
    elif op==0x5b:
        role["stored_value_register"]=(words[0]>>8)&15
        role["target_object_register"]=words[0]>>12
    elif op==0x12:
        role["result_register"]=(words[0]>>8)&15
    elif op in (0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c):
        role["result_register"]=words[0]>>8
    return role


def safe_writer_structural_excerpt(dex,code_off,slot_keys):
    """Full (<=90 instr) method or 60-instr around exact field2 writes.

    Retains only register coordinates, public/obfuscated class descriptors and
    safe invocation signatures, with zero constant values or proprietary raw
    class method bodies.
    """
    ins=list(instructions(dex,code_off))
    sites=[i for i,(_,op,w) in enumerate(ins)
           if op==0x5b and field_key(dex,w[1]) in slot_keys]
    if not sites:return []
    windows=[]
    for target in sites:
        start=0 if len(ins)<=90 else max(0,target-35)
        end=len(ins) if len(ins)<=90 else min(len(ins),target+25)
        windows.append({
            "total_instructions":len(ins),
            "selected_store_ordinal":target,
            "truncated":start>0 or end<len(ins),
            "register_roles":[{
                "ordinal":i,
                **safe_operand_metadata(dex,ins[i][1],ins[i][2]),
            } for i in range(start,end)],
            "may_describe_unrelated_paths":True,
        })
    return windows


def scan_signed(apks):
    slots=discover_read_slot(apks)
    writes=[]
    scanned=0
    dexes=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if not re.fullmatch(r"classes[0-9]*\.dex",name):continue
                dexes+=1
                d=Dex(z.read(name))
                present={key for index in range(d.table(80,8)[0])
                         if (key:=field_key(d,index)) in slots}
                if not present:continue
                for mid,coff in method_definitions(d):
                    scanned+=1
                    method=d.method(mid)
                    for item in exact_store_witnesses(d,coff,present):
                        item.pop("_slot")
                        item["writer_method"]=limited_method(method)
                        item["writer_profile"]=method_profile(method)
                        item["writer_register_windows"]=safe_writer_structural_excerpt(d,coff,present)
                        writes.append(item)
    if dexes!=6 or not writes:raise ValueError("MISSING_SIGNED_OR_FIELD_WRITES")
    if len(writes)>MAX_RESULT:raise ValueError("FIELD_WRITES_LIMIT")
    return {
        "signed_original_apks":5,"signed_original_dex":6,
        "exact_Lga4_c_receiver_slot_unique":True,
        "scanned_method_bodies_in_matching_Dex":scanned,
        "direct_value_write_sites":len(writes),
        "sites":writes,
        "receiver_class_in_live_audio_proven":False,
        "current_track_fileinfo_to_datasource_identity_proven":False,
        "original_apk_modified":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("READ_ONLY_GITHUB_CI")
    with tempfile.TemporaryDirectory(prefix="celikom-exact-ga4-slot-") as tmp:
        folder=Path(tmp)
        archive=folder/"unchanged-publisher.xapk"
        size,sha=exact.gpr.download(archive)
        if size!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_HASH_MISMATCH")
        apks=exact.gpr.split_apks(archive,folder)
        if len(apks)!=5:raise ValueError("SPLIT_COUNT")
        exact.gpr.inspect_publisher(apks)
        data=scan_signed(apks)
    return {"verdict":"SIGNED_EXACT_LE48_FIELD2_WRITER_REGISTER_ORIGINS_ONLY",
            "publisher_original":"2026.10.3 #170gpr",**data,
            "no_media_credentials_dex_or_apk_export":True}


if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_FIELD2_WRITER_ORIGIN_SCAN_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "original_apk_modified":False,
        }))
        sys.exit(2)
