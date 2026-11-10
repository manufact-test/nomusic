#!/usr/bin/env python3
"""Signed Yandex DEX: prove/disprove candidate Le48 receiver of Lga4.c.

A broad possible-interface dispatch graph found an apparent path to Lro7,
but Le48.a has 16 possible implementations. This read-only source audit
checks the EXACT field Lga4.c uses, all direct DEX writes to that same
field, and the concrete type stored by the actual Lga4 constructor.

No vendor binary/media/strings exported. No live object flow or decoder claim.
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
from trace_native_callers import method_definitions
from audit_native_register_bridge import instructions, move_object_registers
from audit_native_typed_wrapper_coroutines import brief_type,method_profile
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

CLASS="Lga4;"
FIELD_TYPE="Le48;"
MAX_INSTRUCTIONS_TOTAL=50000000
MAX_FIELD_HANDLERS=50
MAX_SIGNATURES=35


def field_key(dex,idx):
    count,table=dex.table(80,8)
    if idx<0 or idx>=count:raise DexError("BAD_FIELD_INDEX")
    pos=table+idx*8
    owner=dex.descriptor(dex.u16(pos))
    typ=dex.descriptor(dex.u16(pos+2))
    private_name=dex.string(dex.u32(pos+4))
    # Name is handled only as a private join key. NEVER emit it.
    return (owner,typ,private_name)


def type_provenance_writes(dex,code_off,interesting):
    """Track unbranched new-instance register up to exact field iput-object.

    This does not infer runtime object identities, reflection or unknown
    exception/re-entry paths. Only deterministic new-instance alias chains
    without branches/unknown writes within a single method body.
    """
    ins=list(instructions(dex,code_off))
    reg_types={}
    results=[]
    uncertain=False
    for _,op,words in ins:
        if op in (0x27,0x28,0x29,0x2a,0x2b,0x2c) or 0x32<=op<=0x3d:
            uncertain=True
            reg_types.clear()
        if op==0x22:
            reg_types[words[0]>>8]=dex.descriptor(words[1])
        else:
            moved=move_object_registers(op,words)
            if moved:
                dst,src=moved
                typ=reg_types.get(src)
                reg_types.pop(dst,None)
                if typ is not None:reg_types[dst]=typ
            elif op in (0x0a,0x0b,0x0c,0x12,0x13,0x14,0x15,
                        0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,0x54,0x62):
                reg_types.pop(words[0]>>8,None)
        if op==0x5b:
            key=field_key(dex,words[1])
            if key not in interesting:continue
            value=(words[0]>>8)&15
            results.append({
                "_field_key":key,
                "new_instance_type_on_same_unbranched_register":
                    (brief_type(reg_types[value]) if value in reg_types else "unknown"),
                "has_branch_or_exception_uncertainty":uncertain,
                "constructor_instance_bound_to_live_receiver":False,
            })
    return results


def direct_field_accesses(dex,code_off,interesting):
    ins=list(instructions(dex,code_off))
    out=[]
    for index,(_,op,words) in enumerate(ins):
        if op not in (0x54,0x5b):continue
        field=field_key(dex,words[1])
        if field not in interesting:continue
        # iv A,B,field: A=dest for iget or source for iput
        target=((words[0]>>8)&15)
        link_to_interface=False
        if op==0x54:
            for _,hop,params in ins[index+1:index+6]:
                if hop in (0x72,0x78):
                    callee=dex.method(params[1])
                    if callee[0]==FIELD_TYPE and callee[1]=="a":
                        from audit_native_register_bridge import invoke_registers
                        if target in invoke_registers(hop,params):
                            link_to_interface=True
        out.append({
            "_field_key":field,
            "operation":"iget_object" if op==0x54 else "iput_object",
            "value_register_directly_consumed_by_Le48_a":link_to_interface,
        })
    return out


def scan_fields(apks):
    records=[]
    all_keys=set()
    target_defs=[]
    scanned_bodies=0
    total_code_units=0
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("DEX_LIMIT")
                d=Dex(z.read(item.filename))
                dex_count+=1
                field_size,_=d.table(80,8)
                keys=set()
                for i in range(field_size):
                    key=field_key(d,i)
                    if key[0]==CLASS and key[1]==FIELD_TYPE:
                        keys.add(key)
                all_keys.update(keys)
                for idx,off in method_definitions(d):
                    method=d.method(idx)
                    scanned_bodies+=1
                    if method[0]==CLASS:
                        target_defs.append(method)
                    if not keys:continue
                    ins=list(instructions(d,off))
                    total_code_units+=len(ins)
                    if total_code_units>MAX_INSTRUCTIONS_TOTAL:
                        raise ValueError("CODE_SCAN_LIMIT")
                    if not any(op in (0x54,0x5b) for _,op,_ in ins):
                        continue
                    touches=direct_field_accesses(d,off,keys)
                    if not touches:continue
                    provenance=type_provenance_writes(d,off,keys)
                    records.append({
                        "method":method,
                        "accesses":touches,
                        "stores":provenance,
                    })
    if dex_count!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    if not all_keys:raise ValueError("LE48_GA4_FIELDS_MISSING")
    slots={key:f"typed-Le48-field-{i+1}" for i,key in enumerate(sorted(all_keys))}
    readers=defaultdict(set)
    writers=defaultdict(set)
    ctor_types=defaultdict(set)
    all_writer_types=defaultdict(list)
    target_read_slots=set()
    for record in records:
        for access in record["accesses"]:
            slot=slots[access["_field_key"]]
            if access["operation"]=="iget_object":
                readers[slot].add(record["method"])
                if record["method"][0]==CLASS and record["method"][1]=="c":
                    target_read_slots.add(slot)
            else:
                writers[slot].add(record["method"])
        for store in record["stores"]:
            slot=slots[store["_field_key"]]
            observed=store["new_instance_type_on_same_unbranched_register"]
            all_writer_types[slot].append({
                "writer":bounded_obfuscated(record["method"]),
                "same_method_unbranched_new_instance":observed,
                "branch_uncertainty":store["has_branch_or_exception_uncertainty"],
                "runtime_receiver_selected":False,
            })
            if record["method"][0]==CLASS and record["method"][1]=="<init>":
                ctor_types[slot].add(observed)
    return {
        "six_original_dex_complete":True,
        "defined_method_bodies_scanned":scanned_bodies,
        "method_bodies_with_target_field_access":len(records),
        "all_code_instruction_count":total_code_units,
        "distinct_le48_fields_on_ga4":len(slots),
        "exact_field_slot_caller_c":{
            "used_slots":sorted(target_read_slots),
            "call_receiver_from_field_observed":any(
                rec["method"][0]==CLASS and rec["method"][1]=="c"
                and any(acc["value_register_directly_consumed_by_Le48_a"]
                        for acc in rec["accesses"])
                for rec in records),
        },
        "field_write_and_initialization_census":[{
            "field_slot":slot,
            "read_method_count":len(readers.get(slot,())),
            "read_method_hints":[bounded_obfuscated(m) for m in sorted(readers.get(slot,()))[:MAX_FIELD_HANDLERS]],
            "write_method_count":len(writers.get(slot,())),
            "writer_hints":[bounded_obfuscated(m) for m in sorted(writers.get(slot,()))[:MAX_FIELD_HANDLERS]],
            "bounded_writer_value_origins":all_writer_types.get(slot,[])[:MAX_FIELD_HANDLERS],
            "ctor_new_instance_types":sorted(ctor_types.get(slot,())),
            "no_reflection_or_dynamic_field_write_proven":False,
        } for slot in sorted(slots.values())],
        "constructor_method_count":sum(m[1]=="<init>" for m in target_defs),
        "static_receiver_runtime_class_unconditionally_proven":False,
        "possible_Le48_to_Ldl8_dispatch_is_current_audio_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-static-ga4-field-") as name:
        root=Path(name)
        path=root/"publisher-original-unchanged.xapk"
        size,digest=exact.gpr.download(path)
        if size!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("PINNED_APK_HASH")
        splits=exact.gpr.split_apks(path,root)
        if len(splits)!=5:raise ValueError("PINNED_SPLITS")
        exact.gpr.inspect_publisher(splits)
        result=scan_fields(splits)
    return {
        "verdict":"SIGNED_NATIVE_EXACT_LE48_FIELD_RECEIVER_PROVENANCE_ONLY",
        "publisher":"2026.10.3 #170gpr",
        **result,
        "no_original_app_or_media_export":True,
        "no_source_swap_or_decoder_proof":True,
    }


if __name__=="__main__":
    try:print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as ex:
        print(json.dumps({"verdict":"SIGNED_GA4_RECEIVER_SCAN_INCOMPLETE",
                          "error_class_only":type(ex).__name__,
                          "no_source_swap_or_decoder_proof":True}))
        sys.exit(2)
