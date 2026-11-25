#!/usr/bin/env python3
"""Read-only, original-signed-2025 iLb -> lLb child Of6 DEX provenance.

No raw DEX, private vendor code, field names/IDs, paths, strings, tokens,
registers or method identities in output. A STATIC field path is NOT proof
of a runtime Java identity, current playback, or CELIKOM audio replacement.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile

from a1_private_push_dex_method import Dex, EXPECTED_LEN, EXPECTED_SHA
from a1_private_dex_flow import decode_instructions, FlowDecodeError, INVOKE_METHOD

SOURCE_OWNER="LiLb;"
CHILD_OWNER="LlLb;"
OF6="LOf6;"
CTOR_TYPES=("LdA9;","LgA9;","LJI7;",OF6,"LFq1;","LHy9$a;","LPAa;")
CHILD_TYPES=("LdA9;","LQAa;",OF6,"LgA9;")
BOUNDARY=set(range(0x32,0x3e)) | {0x27,0x28,0x29,0x2a,0x2b,0x2c}
MAX_METHOD_CODES=800000

def params_for(dex,proto):
    total,off=struct.unpack_from("<II",dex.data,72)
    if proto>=total or off+total*12>len(dex.data):
        return None
    p=struct.unpack_from("<I",dex.data,off+proto*12+8)[0]
    if p==0:return ()
    if p+4>len(dex.data):return None
    length=struct.unpack_from("<I",dex.data,p)[0]
    if length>24 or p+4+length*2>len(dex.data):return None
    return tuple(dex.type(struct.unpack_from("<H",dex.data,p+4+i*2)[0])
                 for i in range(length))

def of6_field(dex,idx):
    count,off=struct.unpack_from("<II",dex.data,80)
    if idx>=count or count>500000 or off+count*8>len(dex.data):
        return False
    owner,type_index,_=struct.unpack_from("<HHI",dex.data,off+idx*8)
    return dex.type(owner)==SOURCE_OWNER and dex.type(type_index)==OF6

def field_descriptor(dex,idx):
    count,off=struct.unpack_from("<II",dex.data,80)
    if idx>=count or count>500000 or off+count*8>len(dex.data):
        return None
    owner,typ,_=struct.unpack_from("<HHI",dex.data,off+idx*8)
    return (dex.type(owner),dex.type(typ))

def returns_original_item_type(dex,proto):
    total,off=struct.unpack_from("<II",dex.data,72)
    if proto>=total or off+total*12>len(dex.data):return False
    idx=struct.unpack_from("<I",dex.data,off+proto*12+4)[0]
    return dex.type(idx)==OF6

def child_invoke_result_ref(code,ins,index,reg):
    """In-memory only; never print method references."""
    if reg is None:return None
    for k in range(index-1,max(-1,index-101),-1):
        p,op,_=ins[k]
        if op in BOUNDARY:return None
        if op==0x07 and code[p+1]&15==reg:reg=code[p+1]>>4
        elif op==0x08 and code[p+1]==reg:
            reg=struct.unpack_from("<H",code,p+2)[0]
        elif op==0x09 and struct.unpack_from("<H",code,p+2)[0]==reg:
            reg=struct.unpack_from("<H",code,p+4)[0]
        elif op==0x0c and code[p+1]==reg:
            if k>0 and ins[k-1][1] in INVOKE_METHOD:
                return struct.unpack_from("<H",code,ins[k-1][0]+2)[0]
            return None
        elif op==0x54 and code[p+1]&15==reg:return None
        elif op in (0x12,0x13,0x14,0x15,0x16,0x1a,0x1b,0x22) and (
                (code[p+1]&15 if op==0x12 else code[p+1])==reg):return None
    return None

def child_argument_origin(dex,code,ins,index,reg,constructor_fields):
    """Finite static shape; never export field indices, owners or registers."""
    if reg is None:return "UNSUPPORTED_INVOKE_SHAPE"
    for k in range(index-1,max(-1,index-101),-1):
        p,op,_=ins[k]
        if op in BOUNDARY:return "CONTROL_FLOW_UNRESOLVED"
        if op==0x07 and code[p+1]&15==reg:
            reg=code[p+1]>>4
        elif op==0x08 and code[p+1]==reg:
            reg=struct.unpack_from("<H",code,p+2)[0]
        elif op==0x09 and struct.unpack_from("<H",code,p+2)[0]==reg:
            reg=struct.unpack_from("<H",code,p+4)[0]
        elif op==0x54 and code[p+1]&15==reg:
            fid=struct.unpack_from("<H",code,p+2)[0]
            ft=field_descriptor(dex,fid)
            if fid in constructor_fields:return "ORIGINAL_CTOR_FIELD_REFERENCE"
            if ft is not None and ft[1]==OF6:
                return "OTHER_OF6_TYPED_FIELD_REFERENCE"
            return "OTHER_TYPED_FIELD_REFERENCE"
        elif op==0x0c and code[p+1]==reg:
            if k==0 or ins[k-1][1] not in INVOKE_METHOD:
                return "INVOKE_RESULT_UNLINKED"
            invoke_pc=ins[k-1][0]
            ref=struct.unpack_from("<H",code,invoke_pc+2)[0]
            owner,_,proto=dex.method_signature(ref)
            if not returns_original_item_type(dex,proto):
                return "INVOKE_RESULT_NON_OF6_RETURN_TYPE"
            if owner==SOURCE_OWNER:return "INVOKE_OF6_FROM_SOURCE_OWNER"
            if owner==CHILD_OWNER:return "INVOKE_OF6_FROM_CHILD_OWNER"
            return "INVOKE_OF6_FROM_OTHER_OWNER"
        elif op in (0x12,0x13,0x14,0x15,0x16,0x1a,0x1b,0x22) and (
                (code[p+1]&15 if op==0x12 else code[p+1])==reg):
            return "OTHER_VALUE_PRODUCER"
    return "PARAMETER_OR_CAPTURE_UNRESOLVED"

def source_argument_register(code,pc,opcode):
    """Return the third argument in the exact static four-arg invoke."""
    if opcode==0x71: # invoke-static {C,D,E,F}: E is Of6
        count=code[pc+1]>>4
        return code[pc+5]&0xf if count==4 else None
    if opcode==0x77: # invoke-static/range {vX .. vX+3}
        count=code[pc+1]
        return struct.unpack_from("<H",code,pc+4)[0]+2 if count==4 else None
    return None

def field_from_local_backtrace(dex,code,ins,index,reg):
    if reg is None:return None
    for k in range(index-1,max(-1,index-101),-1):
        p,op,_=ins[k]
        if op in BOUNDARY:return None
        if op==0x07 and code[p+1]&15==reg:
            reg=code[p+1]>>4
        elif op==0x08 and code[p+1]==reg:
            reg=struct.unpack_from("<H",code,p+2)[0]
        elif op==0x09 and struct.unpack_from("<H",code,p+2)[0]==reg:
            reg=struct.unpack_from("<H",code,p+4)[0]
        elif op==0x54 and code[p+1]&15==reg: # iget-object vA,vB,field@CCCC
            return struct.unpack_from("<H",code,p+2)[0]
        elif op==0x0c and code[p+1]==reg:
            return None # unresolved method result
        elif op in (0x12,0x13,0x14,0x15,0x16,0x1a,0x1b,0x22) and (
                (code[p+1]&15 if op==0x12 else code[p+1])==reg):
            return None
    return None

def inspect_dex(payload, caller_types=None):
    dex=Dex(payload)
    child_refs=set()
    for idx in range(dex.method_count):
        owner,name,proto=dex.method_signature(idx)
        if owner==CHILD_OWNER and name=="if" and params_for(dex,proto)==CHILD_TYPES:
            child_refs.add(idx)

    # Pass 1: capture only the field identity in the *exact* original iLb
    # constructor. Do not assume that iLb itself owns invokeSuspend or the
    # lLb.if callsite (the first static run disproved that assumption).
    ctor_present=False
    ctor_fields=set()
    i_lb_resume=False
    for mid,code in dex.code_methods():
        owner,name,proto=dex.method_signature(mid)
        if owner!=SOURCE_OWNER:continue
        if name=="invokeSuspend":i_lb_resume=True
        if name!="<init>" or params_for(dex,proto)!=CTOR_TYPES:continue
        ctor_present=True
        try:ins=decode_instructions(code)
        except FlowDecodeError:continue
        for pc,op,_ in ins:
            if op==0x5b:  # original iput-object vA,vB,field@CCCC
                fid=struct.unpack_from("<H",code,pc+2)[0]
                if of6_field(dex,fid):ctor_fields.add(fid)

    # Pass 2: locate *all* exact static callers, no matter which private
    # continuation class owns them. The earlier narrow owner-only scan
    # incorrectly reported no calls when the source coroutine was in a
    # separate owner. No vendor method/class identities leave this function.
    calls=0
    from_ctor_field=0
    from_other_field=0
    unresolved=0
    caller_source=0
    caller_child=0
    caller_other=0
    caller_suspend=0
    origin_counts={}
    producer_refs=set()
    for mid,code in dex.code_methods():
        if not child_refs or (b"\x71" not in code and b"\x77" not in code):
            continue
        try:ins=decode_instructions(code)
        except FlowDecodeError:continue
        owner,caller_name,_=dex.method_signature(mid)
        for i,(pc,op,_) in enumerate(ins):
            if op not in (0x71,0x77):continue
            ref=struct.unpack_from("<H",code,pc+2)[0]
            if ref not in child_refs:continue
            calls+=1
            if owner==SOURCE_OWNER:caller_source+=1
            elif owner==CHILD_OWNER:caller_child+=1
            else:caller_other+=1
            if caller_name=="invokeSuspend":
                caller_suspend+=1
                if caller_types is not None:caller_types.add(owner)
            reg=source_argument_register(code,pc,op)
            shape=child_argument_origin(dex,code,ins,i,reg,ctor_fields)
            origin_counts[shape]=origin_counts.get(shape,0)+1
            if shape=="INVOKE_OF6_FROM_CHILD_OWNER":
                producer=child_invoke_result_ref(code,ins,i,reg)
                if producer is not None:producer_refs.add(producer)
            if shape=="ORIGINAL_CTOR_FIELD_REFERENCE":from_ctor_field+=1
            elif shape=="OTHER_OF6_TYPED_FIELD_REFERENCE":from_other_field+=1
            else:unresolved+=1

    # Pass 3: resolve the single child-owner Of6 producer's *defined*
    # return-object body, if it exists in the original signed DEX. A static
    # producer shape still cannot certify selected-track playback or Java ==.
    producer_return_shapes={}
    producer_defined=0
    for mid,code in dex.code_methods():
        if mid not in producer_refs:continue
        producer_defined+=1
        try:ins=decode_instructions(code)
        except FlowDecodeError:
            producer_return_shapes["UNREADABLE_BODY"]=1
            continue
        for i,(pc,op,_) in enumerate(ins):
            if op!=0x11:continue  # return-object vAA
            origin=child_argument_origin(dex,code,ins,i,code[pc+1],ctor_fields)
            producer_return_shapes[origin]=producer_return_shapes.get(origin,0)+1

    return {
        "exact_original_constructor_present":ctor_present,
        "exact_original_child_reference_present":bool(child_refs),
        "coroutine_body_present":i_lb_resume,
        "constructor_original_item_field_count":min(len(ctor_fields),8),
        "original_child_calls_bounded":min(calls,16),
        "child_item_from_constructor_field":min(from_ctor_field,16),
        "child_item_from_other_original_item_field":min(from_other_field,16),
        "child_item_origin_unresolved":min(unresolved,16),
        "callers_in_constructor_owner":min(caller_source,16),
        "callers_in_child_owner":min(caller_child,16),
        "callers_in_other_owner":min(caller_other,16),
        "callers_in_coroutine_resume":min(caller_suspend,16),
        "child_item_argument_origin_shapes":origin_counts,
        "child_item_producer_bodies_defined":min(producer_defined,16),
        "child_item_producer_return_shapes":producer_return_shapes,
    }

def coroutine_source_capture(dexes, caller_types):
    """Cross-DEX capture shape only. A typed field/argument is not identity proof."""
    out = {
        "unique_child_coroutine_owner": int(len(caller_types) == 1),
        "coroutine_source_typed_fields": 0,
        "coroutine_source_parameter_constructors": 0,
        "coroutine_source_field_writes": 0,
        "coroutine_source_field_reads_in_resume": 0,
        "coroutine_constructed_inside_source_owner": 0,
        "coroutine_constructed_inside_child_owner": 0,
        "coroutine_constructed_inside_other_owner": 0,
        "coroutine_resume_calls_source_owner": 0,
    }
    if len(caller_types) != 1:
        return out
    target = next(iter(caller_types))
    for dex in dexes:
        count, off = struct.unpack_from("<II", dex.data, 80)
        if count > 500000 or off + count*8 > len(dex.data):
            raise ValueError("FIELD_TABLE_BOUND")
        source_fields = {i for i in range(count)
                         if field_descriptor(dex, i) == (target, SOURCE_OWNER)}
        constructors = set()
        source_calls = set()
        for mid in range(dex.method_count):
            owner, name, proto = dex.method_signature(mid)
            if owner == target and name == "<init>":
                constructors.add(mid)
            if owner == SOURCE_OWNER:
                source_calls.add(mid)
        for mid, code in dex.code_methods():
            owner, name, proto = dex.method_signature(mid)
            if owner == target and name == "<init>":
                if SOURCE_OWNER in (params_for(dex, proto) or ()):
                    out["coroutine_source_parameter_constructors"] += 1
            if not (owner == target or constructors):
                continue
            try:
                ins = decode_instructions(code)
            except FlowDecodeError:
                continue
            for pc, op, _ in ins:
                if owner == target and op in (0x54, 0x5b):
                    ref = struct.unpack_from("<H", code, pc+2)[0]
                    if ref in source_fields:
                        if op == 0x5b:
                            out["coroutine_source_field_writes"] += 1
                        elif name == "invokeSuspend":
                            out["coroutine_source_field_reads_in_resume"] += 1
                if op not in INVOKE_METHOD:
                    continue
                ref = struct.unpack_from("<H", code, pc+2)[0]
                if ref in constructors and op in (0x70, 0x76):
                    key = ("coroutine_constructed_inside_source_owner" if owner == SOURCE_OWNER
                           else "coroutine_constructed_inside_child_owner" if owner == CHILD_OWNER
                           else "coroutine_constructed_inside_other_owner")
                    out[key] += 1
                if owner == target and name == "invokeSuspend" and ref in source_calls:
                    out["coroutine_resume_calls_source_owner"] += 1
        # DEX field IDs include references, not just definitions. Deduplicate
        # across slices by the complete field signature internally.
    signatures = set()
    for dex in dexes:
        count, off = struct.unpack_from("<II", dex.data, 80)
        for i in range(count):
            if field_descriptor(dex, i) == (target, SOURCE_OWNER):
                _, _, name_idx = struct.unpack_from("<HHI", dex.data, off+i*8)
                signatures.add(dex.string(name_idx))
    out["coroutine_source_typed_fields"] = len(signatures)
    return {k: min(v, 16) for k, v in out.items()}

def inspect_xapk(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size!=EXPECTED_LEN:
        raise ValueError("INVALID_ORIGINAL_SIZE")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest()!=EXPECTED_SHA:
            raise ValueError("INVALID_ORIGINAL_HASH")
    records=[]
    dexes=[]
    caller_types=set()
    with zipfile.ZipFile(path) as xapk:
        for part in xapk.infolist():
            if not part.filename.endswith(".apk") or part.file_size>60_000_000:continue
            with zipfile.ZipFile(io.BytesIO(xapk.read(part))) as apk:
                for name in apk.namelist():
                    if not name.startswith("classes") or not name.endswith(".dex"):continue
                    meta=apk.getinfo(name)
                    if meta.file_size>25_000_000:continue
                    dex=apk.read(name)
                    if dex.startswith(b"dex\n"):
                        records.append(inspect_dex(dex, caller_types))
                        dexes.append(Dex(dex))
    return {
        "source_input_verified":True,
        "dex_slices_checked":min(len(records),100),
        "exact_original_constructor_present":any(v["exact_original_constructor_present"] for v in records),
        "exact_original_child_reference_present":any(v["exact_original_child_reference_present"] for v in records),
        "coroutine_body_present":any(v["coroutine_body_present"] for v in records),
        "constructor_original_item_field_count":min(sum(v["constructor_original_item_field_count"] for v in records),8),
        "original_child_calls_bounded":min(sum(v["original_child_calls_bounded"] for v in records),16),
        "child_item_from_constructor_field":min(sum(v["child_item_from_constructor_field"] for v in records),16),
        "child_item_from_other_original_item_field":min(sum(v["child_item_from_other_original_item_field"] for v in records),16),
        "child_item_origin_unresolved":min(sum(v["child_item_origin_unresolved"] for v in records),16),
        "callers_in_constructor_owner":min(sum(v["callers_in_constructor_owner"] for v in records),16),
        "callers_in_child_owner":min(sum(v["callers_in_child_owner"] for v in records),16),
        "callers_in_other_owner":min(sum(v["callers_in_other_owner"] for v in records),16),
        "callers_in_coroutine_resume":min(sum(v["callers_in_coroutine_resume"] for v in records),16),
        "child_item_argument_origin_shapes":{
            key:min(sum(v["child_item_argument_origin_shapes"].get(key,0) for v in records),16)
            for key in sorted({k for v in records for k in v["child_item_argument_origin_shapes"]})
        },
        "child_item_producer_bodies_defined":min(sum(v["child_item_producer_bodies_defined"] for v in records),16),
        "child_item_producer_return_shapes":{
            key:min(sum(v["child_item_producer_return_shapes"].get(key,0) for v in records),16)
            for key in sorted({k for v in records for k in v["child_item_producer_return_shapes"]})
        },
        "coroutine_source_capture_shape":coroutine_source_capture(dexes, caller_types),
        "static_only_no_runtime_source_or_audio_proof":True,
    }

def selftest():
    # 35c E=third argument, 3rc third offset; assert never reads F/G.
    c=bytes([0x71,0x40,0,0,0x21,0x43])
    assert source_argument_register(c,0,0x71)==3
    d=bytes([0x77,0x04,0,0,0x15,0])
    assert source_argument_register(d,0,0x77)==0x17
    assert source_argument_register(c,0,0x6e) is None
    assert coroutine_source_capture([], set())["unique_child_coroutine_owner"] == 0
    assert coroutine_source_capture([], {"Lsynthetic;"})["unique_child_coroutine_owner"] == 1
    print("A1_ORIGINAL_CHILD_STATIC_PROVENANCE_SELFTEST_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path)
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    if args.selftest:selftest()
    elif args.xapk:
        print("A1_ORIGINAL_CHILD_STATIC_ONLY",json.dumps(inspect_xapk(args.xapk),sort_keys=True))
    else:parser.error("--xapk or --selftest required")
