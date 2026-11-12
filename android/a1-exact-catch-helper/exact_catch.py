#!/usr/bin/env python3
"""Issue #50 ONLY: private exact Push.impl.a try_item -> catch-handler -> throw edges.

No DEX rewriting, third-party symbols, offsets, registers, code or exception values
leave ephemeral CI. A's existing exact candidate/ref/normal-CFG parser is imported
unchanged. UNKNOWN is a deliberate, testable outcome for ambiguous layouts.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import zipfile

A_CI=Path(__file__).resolve().parents[1]/"native-yandex-hooklab"/"ci"
sys.path.insert(0,str(A_CI))
from a1_private_push_dex_method import (Dex,DexError,EXPECTED_LEN,EXPECTED_SHA,
    group_class,group_call,private_near_true_exact_throw_path)
from a1_private_dex_fatal_cfg import exact_fatal_cfg,private_exclusive_fatal_guard_refs,_nexts
from a1_private_dex_flow import decode_instructions,FlowDecodeError,INVOKE_METHOD

BRANCH="experiment/android-a1-helper-exact-try-handler-arm13-20261112"
MAX_TRIES=128
MAX_HANDLERS=128
MAX_CATCHES=32
MAX_GRAPH=12000

class Closed(Exception):
    """Fixed local parser constraint; never print untrusted content."""

def _u(data,at,end):
    x=0
    for i in range(5):
        if at>=end:raise Closed("ULEB_BOUND")
        b=data[at];at+=1
        x|=(b&127)<<(7*i)
        if not b&128:
            if x>0xffffffff:raise Closed("ULEB_OVERFLOW")
            return x,at
    raise Closed("ULEB_LENGTH")

def _s(data,at,end):
    x=0
    shift=0
    for i in range(5):
        if at>=end:raise Closed("SLEB_BOUND")
        b=data[at];at+=1
        x|=(b&127)<<shift
        shift+=7
        if not b&128:
            if b&0x40:x|=-(1<<shift)
            if x<-(2**31) or x>2**31-1:raise Closed("SLEB_OVERFLOW")
            return x,at
    raise Closed("SLEB_LENGTH")

def _kind(desc):
    # Exact fixed classes, no vendor symbol in any output.
    return {
        "Ljava/lang/Throwable;":"TYPED_THROWABLE",
        "Ljava/lang/Exception;":"TYPED_EXCEPTION",
        "Ljava/lang/RuntimeException;":"TYPED_RUNTIME_EXCEPTION",
        "Ljava/lang/IllegalStateException;":"TYPED_ILLEGAL_STATE",
    }.get(desc,"TYPED_OTHER")

def _locate_code_item(dex,target_mid):
    """Find the already-selected single method's code_item offset, not a scanner."""
    data=dex.data
    for c in range(dex.class_count):
        at=struct.unpack_from("<I",data,dex.class_off+32*c+24)[0]
        if not at:continue
        static,at=_u(data,at,len(data))
        fields,at=_u(data,at,len(data))
        direct,at=_u(data,at,len(data))
        virtual,at=_u(data,at,len(data))
        if static+fields+direct+virtual>100000:raise Closed("CLASS_BOUND")
        for _ in range(static+fields):
            _,at=_u(data,at,len(data))
            _,at=_u(data,at,len(data))
        for n in (direct,virtual):
            mid=0
            for _ in range(n):
                delta,at=_u(data,at,len(data));mid+=delta
                _,at=_u(data,at,len(data))
                off,at=_u(data,at,len(data))
                if mid==target_mid:
                    if not off:raise Closed("NO_CODE")
                    return off
    raise Closed("TARGET_OFFSET_UNKNOWN")

def read_catches(data,code_off,dex):
    """DEX code_item: padding, try_item[], encoded_catch_handler_list.

    start/insn_count and handler addresses are in 16-bit code units; handler_off
    is a BYTE offset from the beginning of encoded_catch_handler_list.
    Validates all handler PC boundaries after instruction decoding, fail-closed.
    Internal offsets are never returned to stdout, only finite labels.
    """
    if code_off<0 or code_off+16>len(data):raise Closed("CODE_HEADER")
    tries=struct.unpack_from("<H",data,code_off+6)[0]
    insn_units=struct.unpack_from("<I",data,code_off+12)[0]
    if tries>MAX_TRIES or insn_units>200000:raise Closed("METHOD_BOUND")
    insn_begin=code_off+16
    insn_end=insn_begin+insn_units*2
    if insn_end>len(data):raise Closed("INSN_BOUND")
    code=data[insn_begin:insn_end]
    decoded=decode_instructions(code)
    boundaries={pc for pc,_,_ in decoded}
    boundaries.add(len(code))
    if not tries:return code,[]
    at=insn_end+(2 if insn_units%2 else 0)
    if at+8*tries>len(data):raise Closed("TRY_BOUND")
    items=[]
    prior_end=0
    for i in range(tries):
        start,count,handler_off=struct.unpack_from("<IHH",data,at+8*i)
        end=start+count
        if count==0 or start<prior_end or end>insn_units:raise Closed("TRY_RANGE")
        if start*2 not in boundaries or end*2 not in boundaries:
            raise Closed("TRY_INSN_BOUNDARY")
        items.append((start*2,end*2,handler_off))
        prior_end=end
    handler_base=at+tries*8
    count,cur=_u(data,handler_base,len(data))
    if not 0<count<=MAX_HANDLERS:raise Closed("HANDLER_COUNT")
    handlers={}
    for _ in range(count):
        relative=cur-handler_base
        size,cur=_s(data,cur,len(data))
        if abs(size)>MAX_CATCHES:raise Closed("HANDLER_TYPES_BOUND")
        entries=[]
        seen_types=set()
        for _ in range(abs(size)):
            typ,cur=_u(data,cur,len(data))
            address,cur=_u(data,cur,len(data))
            if typ>=dex.type_count or typ in seen_types:
                raise Closed("HANDLER_TYPE")
            seen_types.add(typ)
            pc=address*2
            if pc not in boundaries or pc==len(code):raise Closed("HANDLER_PC")
            entries.append((_kind(dex.type(typ)),pc))
        if size<=0:
            address,cur=_u(data,cur,len(data))
            pc=address*2
            if pc not in boundaries or pc==len(code):raise Closed("HANDLER_PC")
            entries.append(("CATCH_ALL",pc))
        if not entries:raise Closed("EMPTY_HANDLER")
        handlers[relative]=tuple(entries)
    if any(off not in handlers for _,_,off in items):
        raise Closed("INVALID_HANDLER_OFFSET")
    return code,[(start,end,handlers[ref]) for start,end,ref in items]

def _targets(code,ins,strings):
    positions=[]
    for pc,op,_ in ins:
        if op in (0x1a,0x1b):
            index=(struct.unpack_from("<H",code,pc+2)[0] if op==0x1a
                   else struct.unpack_from("<I",code,pc+2)[0])
            if index in strings:positions.append(pc)
    throws={pc for pc,op,_ in ins if op==0x27}
    pairs=[]
    for st in positions:
        target=min((pc for pc in throws if st<pc<=st+256),default=None)
        if target is not None:pairs.append((st,target))
    return sorted(set(pairs))

def _inside(pc,ranges):
    return [entry for start,end,entries in ranges if start<=pc<end
            for entry in entries]

def _reach(from_pc,goals,graph):
    stack=[from_pc];seen=set()
    while stack:
        pc=stack.pop()
        if pc in goals:return True
        if pc in seen:continue
        if len(seen)>MAX_GRAPH:raise Closed("GRAPH_BOUND")
        seen.add(pc)
        stack.extend(n for n in graph.get(pc,[]) if n not in seen)
    return False

def _reached_nodes(from_pc,graph):
    stack=[from_pc];seen=set()
    while stack:
        pc=stack.pop()
        if pc in seen:continue
        if len(seen)>MAX_GRAPH:raise Closed("GRAPH_BOUND")
        seen.add(pc)
        stack.extend(n for n in graph.get(pc,[]) if n not in seen)
    return seen

def _route(pc,ranges,targets,graph):
    entries=_inside(pc,ranges)
    matched=[kind for kind,start in entries if _reach(start,targets,graph)]
    if any(k in ("CATCH_ALL","TYPED_THROWABLE") for k in matched):
        return "REACH_DEFINITE_TYPE"
    if matched:return "REACH_TYPED_DEPENDS_ON_THROWN_CLASS"
    return "NOT_REACH"

def _combine(routes):
    if "REACH_DEFINITE_TYPE" in routes:return "EXACT_THROW_IN_HANDLER_REACH"
    if "REACH_TYPED_DEPENDS_ON_THROWN_CLASS" in routes:return "UNKNOWN"
    return "NOT_REACH"

def _result_unknown():
    return {
        "EXACT_HELPER_IN_TRY":"UNKNOWN",
        "EXACT_THROW_IN_HANDLER_REACH":"UNKNOWN",
        "TRY_COVERS_THROW_BUILD":"UNKNOWN",
        "TRUE_PATH_INVOKE_CATCH_REACH":"UNKNOWN",
        "HELPER_OWN_HANDLER_REACH":"UNKNOWN",
        "SDK_INIT_NEARBY_IN_TRY":"UNKNOWN",
        "HANDLER_KIND_FAMILIES":[],
        "true_normal_cfg":"UNKNOWN",
        "method_candidate":"UNKNOWN",
        "source_original_exact_verified":False,
        "live_handler_execution_observed":False,
        "sdk_implementation_modified":False,
    }

def classify(code,ranges,near_refs,strings,dex):
    out=_result_unknown()
    try:
        ins=decode_instructions(code)
        pcs={pc for pc,_,_ in ins}
        graph={pc:_nexts(code,(pc,op,size),pcs) for pc,op,size in ins}
        pairs=_targets(code,ins,strings)
        if not pairs or len(pairs)>16:raise Closed("FATAL_PAIR_AMBIGUITY")
        target={p for _,p in pairs}
        call=[i for i,(pc,op,_) in enumerate(ins) if
              op in INVOKE_METHOD and
              struct.unpack_from("<H",code,pc+2)[0] in near_refs]
        if len(call)!=1:raise Closed("NEAR_CALL_AMBIGUITY")
        i=call[0]
        if i+2>=len(ins):raise Closed("NEAR_GUARD_LAYOUT")
        near_pc,_,_=ins[i]
        mr,mo,_=ins[i+1]
        guard_pc,go,_=ins[i+2]
        if mo!=0x0a or go not in (0x38,0x39) or code[mr+1]!=code[guard_pc+1]:
            raise Closed("NEAR_GUARD_LAYOUT")
        true_pc=graph[guard_pc][1] if go==0x39 else graph[guard_pc][0]
        out["true_normal_cfg"]=(
            "TRUE_NORMAL_REACH" if _reach(true_pc,target,graph) else
            "TRUE_NORMAL_BLOCKS_THROW")
        out["EXACT_HELPER_IN_TRY"]=(
            "EXACT_HELPER_IN_TRY" if _inside(near_pc,ranges) else "NOT_IN_TRY")
        out["HANDLER_KIND_FAMILIES"]=sorted({kind for _,_,entries in ranges for kind,_ in entries})
        covered=[any(start<=s<end and start<=t<end for start,end,_ in ranges)
                 for s,t in pairs]
        out["TRY_COVERS_THROW_BUILD"]=(
            "TRY_COVERS_THROW_BUILD" if any(covered) else "NOT")
        out["HELPER_OWN_HANDLER_REACH"]=_combine([
            _route(near_pc,ranges,target,graph)])
        # A TRUE return means that exact helper invocation itself did not throw.
        # Test exceptional call edges only AFTER its successful guard TRUE path.
        normal_true=_reached_nodes(true_pc,graph)
        guarded_invokes=[pc for pc,op,_ in ins if op in INVOKE_METHOD
                         and pc in normal_true]
        routes=[_route(pc,ranges,target,graph) for pc in guarded_invokes]
        out["TRUE_PATH_INVOKE_CATCH_REACH"]=_combine(routes)
        out["EXACT_THROW_IN_HANDLER_REACH"]=_combine(
            routes+[_route(near_pc,ranges,target,graph)])
        # Only public/exactly named SDK "init"/"activate" is an init call.
        # Unknown obfuscated calls are never silently called initialization.
        init_calls=[]
        for pc in guarded_invokes:
            ref=struct.unpack_from("<H",code,pc+2)[0]
            if ref>=dex.method_count:continue
            owner,name=dex.method(ref)
            if name in ("init","activate") and (
                group_class(owner) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN") or
                owner.startswith(("Lcom/yandex/metrica/","Lio/appmetrica/analytics/"))):
                init_calls.append(pc)
        out["SDK_INIT_NEARBY_IN_TRY"]=(
            "SDK_INIT_NEARBY_IN_TRY" if any(_inside(pc,ranges) for pc in init_calls)
            else "SDK_INIT_NEARBY_NOT_IN_TRY" if init_calls else "NO_EXACT_INIT_CALL")
        out["method_candidate"]="ONE_EXACT_TARGET"
        return out
    except (FlowDecodeError,Closed,IndexError,ValueError,struct.error):
        return _result_unknown()

def _verified_xapk(path:Path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size!=EXPECTED_LEN:
        raise Closed("SOURCE_LENGTH")
    with path.open("rb") as src:
        if hashlib.file_digest(src,"sha256").hexdigest()!=EXPECTED_SHA:
            raise Closed("SOURCE_HASH")
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            info=z.getinfo(name)
            if not name.endswith(".apk") or info.file_size>60_000_000:continue
            with zipfile.ZipFile(io.BytesIO(z.read(name))) as apk:
                for item in apk.namelist():
                    if item.startswith("classes") and item.endswith(".dex"):
                        payload=apk.read(item)
                        if payload.startswith(b"dex\n"):
                            yield payload

def inspect(path:Path):
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise Closed("BRANCH_BOUND")
    reports=[]
    for payload in _verified_xapk(path):
        dex=Dex(payload)
        strings=dex.possible_error_strings()
        if not strings:continue
        for mid,code in dex.code_methods():
            owner,name=dex.method(mid)
            if group_class(owner)!="PUSH_IMPL" or name!="a":continue
            cfg=exact_fatal_cfg(code,strings,dex,group_call)
            if not cfg["decoded"] or not cfg["fatal_throw_candidates"]:continue
            refs=private_exclusive_fatal_guard_refs(
                code,strings,dex,group_call,max_distance=256)
            # Same exact near helper and original "TRUE_CFG_BLOCKS_THROW"
            # classification as A, rather than another overload's try_items.
            if (private_near_true_exact_throw_path(code,refs,strings)
                    !="TRUE_CFG_BLOCKS_THROW"):
                continue
            try:
                off=_locate_code_item(dex,mid)
                exact,ranges=read_catches(dex.data,off,dex)
                if exact!=code:raise Closed("CODE_ITEM_MISMATCH")
                outcome=classify(code,ranges,refs,strings,dex)
                outcome["source_original_exact_verified"]=True
                outcome["try_regions_bounded"]=min(len(ranges),MAX_TRIES)
                reports.append(outcome)
            except (Closed,FlowDecodeError,IndexError,ValueError,struct.error):
                reports.append(_result_unknown())
    if len(reports)!=1:
        result=_result_unknown()
        result["method_candidate"]="AMBIGUOUS_OR_ABSENT"
        result["candidates_bounded"]=min(len(reports),8)
    else:result=reports[0]
    print("EXACT_CATCH_RESULT "+json.dumps(result,sort_keys=True),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    args=parser.parse_args()
    try:
        out=inspect(args.xapk)
        # An inconclusive result is valid static evidence; no product claim.
        return 0 if out["source_original_exact_verified"] else 2
    except (Closed,DexError,ValueError,zipfile.BadZipFile,OSError,struct.error):
        print('EXACT_CATCH_ABORT {"status":"INCONCLUSIVE","vendor_data_disclosed":false}')
        return 2

if __name__=="__main__":raise SystemExit(main())
