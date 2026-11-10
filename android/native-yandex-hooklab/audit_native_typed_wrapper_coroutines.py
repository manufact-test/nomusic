#!/usr/bin/env python3
"""Read-only publisher-pinned native DEX evidence for exact FileInfo wrapper flow.

This is intentionally an engineering *audit*, not a hook or patch. It reads only
a hash-pinned publisher signed six-DEX APK, and prints bounded class/method/
argument/field shapes. No string literals, method bodies, URLs, media or APK.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
from inspect_android_host import Dex, DexError, DEX_MAX
from trace_native_callers import method_definitions, INVOKES
from audit_native_media_implementors import relations
from trace_native_model_to_decoder import bounded_obfuscated
from audit_native_register_bridge import (
    instructions, move_object_registers, invoke_registers,
    instruction_successors, cfg_result_witness
)
import clone_native_splits_ephemeral as exact

WRAPPERS = ("Lxa7;", "Lta7;", "Lwa7;", "Leed;")
SEEDS = ("Lhee;", "Lged;", "Lfed;", "Lgee;", "Lfqr;")
INTERFACES = ("Lcod;", "Leod;")
OWNERS = frozenset(WRAPPERS + SEEDS + INTERFACES)
SOURCE = "Lsw7;"
MODEL = "Leed;"
METHOD_COUNT_CAP = 50
MAX_FIELD_COUNT = 100
MAX_RELATIONS = 320000
MAX_TARGET_BODIES = 350
MAX_OUTPUT = 18
MAX_PATH_STATES = 6000
MAX_PATH_DEPTH = 220


def brief_type(t):
    if t in "VZBSCIJFD" and len(t) == 1:
        return t
    if t.startswith("["):
        return "array"
    if re.fullmatch(r"L[A-Za-z0-9_$]{1,16};", t):
        return t
    if t == "Ljava/lang/Object;":
        return "java-object"
    if t == "Ljava/lang/String;":
        return "java-string"
    if t == "Lkotlin/coroutines/Continuation;":
        return "coroutine-continuation"
    if t.startswith("Landroidx/media3/"):
        return "public-media3-type"
    if t.startswith("Landroid/media/"):
        return "platform-media-type"
    return "other-object"


def parse_types(proto):
    """Simple JVM/Dalvik descriptor tokenizer; do not emit private names."""
    if not proto.startswith("(") or ")" not in proto:
        raise DexError("PROTO_INVALID")
    arg, ret = proto[1:].split(")", 1)
    def tokenize(value):
        out=[]
        i=0
        while i<len(value):
            start=i
            while i<len(value) and value[i]=="[":
                i+=1
            if i>=len(value):
                raise DexError("PROTO_INVALID_ARRAY")
            if value[i]=="L":
                end=value.find(";",i)
                if end<0:raise DexError("PROTO_UNTERMINATED_TYPE")
                i=end+1
            elif value[i] in "VZBSCIJFD":
                i+=1
            else:
                raise DexError("PROTO_INVALID_TYPE")
            out.append(value[start:i])
        return out
    args = tokenize(arg)
    result = tokenize(ret)
    if len(result)!=1 or len(args)>48:
        raise DexError("PROTO_LIMIT")
    return args,result[0]


def method_profile(triple):
    owner, name, proto = triple
    args, returned = parse_types(proto)
    return {
        "owner": brief_type(owner), "method": name[:35],
        "param_types": [brief_type(x) for x in args[:12]],
        "param_count": len(args),
        "return_type": brief_type(returned),
        "mentions_eed": MODEL in proto,
        "continuation": "Lkotlin/coroutines/Continuation;" in proto,
    }


def field_at(dex, field_idx):
    count, table = dex.table(80, 8)
    if field_idx < 0 or field_idx >= count:
        raise DexError("FIELD_INDEX_OOB")
    pos = table + field_idx*8
    cidx=dex.u16(pos)
    tidx=dex.u16(pos+2)
    return (dex.descriptor(cidx), dex.descriptor(tidx))


def class_field_shapes(dex, owner):
    """DEX class_data field indexes, never raw field names or stored values."""
    fields=[]
    if owner not in dex.defined_classes():
        return []
    count, table=dex.table(80,8)
    for n in range(count):
        o,t=field_at(dex,n)
        if o==owner:
            fields.append(brief_type(t))
            if len(fields)>MAX_FIELD_COUNT:
                raise ValueError("CLASS_FIELD_LIMIT")
    return sorted(fields)


def enumerate_target_bodies(apks):
    """Only target class bodies; no arbitrary vendor code export."""
    bodies={}
    types={}
    seen=0
    stats={"signed_dex":0,"definitions":0}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for entry in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>DEX_MAX:raise ValueError("DEX_SIZE_LIMIT")
                d=Dex(z.read(entry.filename))
                stats["signed_dex"]+=1
                for name,(flags,parents) in relations(d).items():
                    if name in OWNERS:
                        if name in types:
                            raise ValueError("DUPLICATE_TARGET_CLASS")
                        types[name]={
                            "flags": flags,
                            "parents": [brief_type(x) for x in parents],
                            "fields": class_field_shapes(d,name),
                        }
                for mid,coff in method_definitions(d):
                    triple=d.method(mid)
                    stats["definitions"]+=1
                    if triple[0] not in OWNERS:
                        continue
                    if triple in bodies:
                        raise ValueError("DUPLICATE_TARGET_METHOD")
                    seen+=1
                    if seen>MAX_TARGET_BODIES:
                        raise ValueError("TARGET_BODY_COUNT_BOUND")
                    ins=list(instructions(d,coff))
                    calls=[]
                    for _,op,words in ins:
                        if op in INVOKES:
                            calls.append(method_profile(d.method(words[1])))
                    # Discard DEX immediately after reducing to deidentified shape
                    bodies[triple]={
                        "method":method_profile(triple),
                        "instructions":len(ins),
                        "invokes_total":len(calls),
                        "invoke_examples":calls[:MAX_OUTPUT],
                        "exact_target_invokes":[x for x in calls
                            if x["owner"] in WRAPPERS+SEEDS+INTERFACES][:MAX_OUTPUT],
                        "source_register_witnesses":cfg_result_witness(d,coff),
                        "direct_field_read_count":sum(op in (0x54,0x62) for _,op,_ in ins),
                        "direct_field_write_count":sum(op in (0x5b,0x69) for _,op,_ in ins),
                    }
    if stats["signed_dex"]!=6:
        raise ValueError("SIGNED_SIX_DEX_EXPECTED")
    return bodies,types,stats


def _abstract_short(x):
    return bounded_obfuscated(x) if x[0] in OWNERS or x[0]==SOURCE else brief_type(x[0])+"->"+x[1][:20]


def profile_tracked_results(dex, code_off, producers):
    """Per-invoke argument-position MAY-flow for returns to wrapper/consumer.

    Neither exact interprocedural object identity nor decoder source is proven.
    Controls branch and alias semantics only, NOT heap, exception handlers,
    suspended coroutines, reflection, polymorphic receiver resolutions.
    """
    ins=list(instructions(dex,code_off))
    positions={pc:i for i,(pc,_,_) in enumerate(ins)}
    output=[]
    for i,(pc,op,w) in enumerate(ins):
        if op not in INVOKES or i+2>=len(ins) or ins[i+1][1]!=0x0c:
            continue
        prod=dex.method(w[1])
        if prod not in producers:
            continue
        seed=ins[i+1][2][0]>>8
        work=[(ins[i+2][0],frozenset({seed}),0)]
        visited=set()
        evidence=set()
        incomplete=False
        while work:
            at,state,depth=work.pop()
            marker=(at,state)
            if marker in visited:continue
            visited.add(marker)
            if len(visited)>MAX_PATH_STATES or depth>MAX_PATH_DEPTH:
                incomplete=True
                continue
            ii=positions.get(at)
            if ii is None:continue
            ip,opcode,words=ins[ii]
            regs=set(state)
            if opcode in INVOKES:
                target=dex.method(words[1])
                for idx,reg in enumerate(invoke_registers(opcode,words)):
                    if reg in regs:
                        evidence.add(("invoke_interface" if opcode in (0x72,0x78)
                                      else "invoke",
                                      _abstract_short(target),idx))
            if opcode in (0x5b,0x69):
                src=((words[0]>>8)&15) if opcode==0x5b else words[0]>>8
                if src in regs:
                    field_idx=words[1]
                    owner,typ=field_at(dex,field_idx)
                    evidence.add(("field_store",brief_type(owner)+":"+brief_type(typ),0))
            if opcode==0x11 and (words[0]>>8) in regs:
                evidence.add(("return_object","none",0))
            moved=move_object_registers(opcode,words)
            if moved:
                dest,src=moved
                is_source=src in regs
                regs.discard(dest)
                if is_source:regs.add(dest)
            elif opcode in (
                0x01,0x02,0x03,0x0a,0x0b,0x0c,0x12,0x13,0x14,
                0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,0x1c,
                0x22,0x62,0x63,0x64,0x54):
                regs.discard(words[0]>>8)
            nxt=ins[ii+1][0] if ii+1<len(ins) else None
            if nxt is None or not regs:continue
            for successor in instruction_successors(ip,opcode,words,nxt):
                if successor in positions:
                    work.append((successor,frozenset(regs),depth+1))
        output.append({
            "producer":_abstract_short(prod),
            "events":[{"action":a,"target":b,"arg_word":k}
                      for a,b,k in sorted(evidence)[:MAX_OUTPUT]],
            "bounded_search_truncated":incomplete,
            "proven_exact_track":False,
        })
    return output[:MAX_OUTPUT]


def inspect_seed_propagation(apks):
    tracked={
        ("Lsw7;","y0"),("Lsw7;","z0"),
        ("Lhee;","a"),("Lged;","a"),
        ("Lta7;","c"),("Lwa7;","a"),("Leed;","a")
    }
    scan_owners=frozenset(SEEDS+WRAPPERS)
    output={}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for entry in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                d=Dex(z.read(entry))
                for mid,off in method_definitions(d):
                    triple=d.method(mid)
                    if triple[0] not in scan_owners:
                        continue
                    if triple[1] not in ("a","invokeSuspend","c","<init>"):
                        continue
                    candidates={d.method(i) for i in range(d.method_count)
                                if (d.method(i)[0],d.method(i)[1]) in tracked}
                    if not candidates:continue
                    events=profile_tracked_results(d,off,candidates)
                    if events:
                        output[_abstract_short(triple)]=events
    return dict(sorted(output.items()))


def scan_signed(apks):
    bodies,classes,stats=enumerate_target_bodies(apks)
    paths=inspect_seed_propagation(apks)
    simplified=[]
    for triple,record in sorted(bodies.items()):
        if triple[0] in WRAPPERS or triple[1]=="invokeSuspend":
            simplified.append(record)
    return {
        "stats":stats,
        "target_class_shapes":{
            brief_type(t):types for t,types in sorted(classes.items())},
        "target_method_body_count":len(bodies),
        "wrapper_and_coroutine_method_profiles":simplified[:MAX_TARGET_BODIES],
        "exact_producer_argument_path_mayflow":paths,
        "real_audio_datasource_reached":False,
        "current_trackid_edition_generation_proven":False,
        "decoder_preprepare_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("SIGNED_VENDOR_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-signed-wrapper-only-") as td:
        tmp=Path(td)
        src=tmp/"unchanged-signed-original.xapk"
        size,digest=exact.gpr.download(src)
        if size!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("PINNED_SIGNATURE_MISMATCH")
        apks=exact.gpr.split_apks(src,tmp)
        if len(apks)!=5:
            raise ValueError("EXPECTED_FIVE_SPLIT_APKS")
        exact.gpr.inspect_publisher(apks)
        result=scan_signed(apks)
    return {
        "verdict":"SIGNED_NATIVE_TYPED_WRAPPER_COROUTINE_AUDIT_ONLY",
        "publisher_original":"2026.10.3 #170gpr",
        **result,
        "no_vendor_source_or_bytecode_export":True,
        "no_media_or_account_access":True,
        "no_yandex_install_patch_or_drm_bypass":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,DexError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_TYPED_WRAPPER_AUDIT_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "real_audio_datasource_reached":False,
        }))
        sys.exit(2)
