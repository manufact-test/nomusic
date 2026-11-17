#!/usr/bin/env python3
"""Exact 2025.10.4 NAV22 live-confirmed renderer secondary caller static provenance.

Analyzes only b.super(lQ8, Sr4[], R29, flags, time, Sl6$b) and its
one-descriptor direct invoke sites in the verified publisher-signed six DEX.
No application execution, private track/account data, stream or sample bytes.
Live owner proof is separate; code shape never asserts currently audible audio.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
import lft2_class_inspection as trusted
audit=trusted.audit

RENDERER_BASE="Landroidx/media3/exoplayer/b;"
SECONDARY=("Landroidx/media3/exoplayer/b;","super",
           "(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V")
ATTACH=("Landroidx/media3/exoplayer/b;","package","([LSr4;LR29;JJLSl6$b;)V")
ATTACH_INTERFACE=("Landroidx/media3/exoplayer/k;","package",ATTACH[2])
ENGINE_ENABLE=("Landroidx/media3/exoplayer/e;","catch","(Lxh6;IZJ)V")
MAX_ENGINE_INSNS=420
MAX_ENGINE_EVENTS=130
MAX_METHOD_INSNS=600
MAX_DIRECT_CALLERS=75
MAX_METHOD_EVENTS=80
MAX_SCANNED_METHODS=750000
MAX_CALLERS_REPORT=75
MAX_ENGINE_ENABLE_INVOKERS=40
MAX_ENGINE_INVOKER_CONTEXT_INSNS=60
MAX_ENGINE_INVOKER_CONTEXT_EVENTS=70

def match_direct_secondary_invoke(callee):
    return tuple(callee)==SECONDARY

def match_secondary_interface_invoke(callee):
    # b implements k and inherits the exact secondary enable-style method.
    # A call compiled against the interface's owner still dispatches to b.
    return (tuple(callee)[1:]==SECONDARY[1:] and
            callee[0] in ("Landroidx/media3/exoplayer/k;",
                           "Landroidx/media3/exoplayer/l;"))

def match_secondary_family_invoke(callee):
    return match_direct_secondary_invoke(callee) or match_secondary_interface_invoke(callee)

def classify_secondary_invoke(callee):
    if tuple(callee)==SECONDARY: return "EXACT_SECONDARY"
    if tuple(callee)==ATTACH or tuple(callee)==ATTACH_INTERFACE: return "EXACT_ATTACH"
    return "OTHER"

def scan_exact(apks):
    scanned=0
    exact_secondary=None
    engine_enable=None
    direct=[]
    engine_invokers=[]
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for member in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):continue
                dex=audit.Dex(archive.read(member.filename))
                for method,flags,offset in audit.method_definitions_with_flags(dex):
                    if not offset:continue
                    scanned+=1
                    if scanned>MAX_SCANNED_METHODS:raise ValueError("SECONDARY_METHOD_CENSUS_LIMIT")
                    if method==SECONDARY:
                        if exact_secondary is not None:raise ValueError("SECONDARY_DUPLICATE_EXACT_METHOD")
                        exact_secondary=(dex,flags,offset)
                    if method==ENGINE_ENABLE:
                        if engine_enable is not None:raise ValueError("SECONDARY_DUPLICATE_ENGINE_ENABLE")
                        engine_enable=(dex,flags,offset)
                    for pc,op,raw in audit.instructions(dex,offset):
                        if op not in audit.INVOKES or not (0x6e<=op<=0x78):
                            continue
                        callee=dex.method(raw[1])
                        if callee==ENGINE_ENABLE:
                            engine_invokers.append((dex,method,flags,offset,pc,op,
                                audit.invoke_registers(op,raw)))
                            if len(engine_invokers)>MAX_ENGINE_ENABLE_INVOKERS:
                                raise ValueError("SECONDARY_ENGINE_TOO_MANY_INVOKERS")
                        if not match_secondary_family_invoke(callee):continue
                        direct.append({"caller":list(method),"pc":pc,"opcode":op,
                                       "callee":list(callee),
                                       "dispatch":"BASE_DIRECT" if match_direct_secondary_invoke(callee)
                                                  else "INTERFACE_VIRTUAL",
                                       "args":audit.invoke_registers(op,raw)})
                        if len(direct)>MAX_DIRECT_CALLERS:
                            raise ValueError("SECONDARY_TOO_MANY_DIRECT_CALLERS")
    if exact_secondary is None:raise ValueError("SECONDARY_EXACT_METHOD_MISSING")
    if engine_enable is None:raise ValueError("SECONDARY_EXACT_ENGINE_ENABLE_MISSING")
    dex,flags,offset=exact_secondary
    insns=list(audit.instructions(dex,offset))
    if len(insns)>MAX_METHOD_INSNS:raise ValueError("SECONDARY_EXACT_METHOD_TOO_LARGE")
    params=audit.expand_invoke_register_types(RENDERER_BASE,
        audit.parse_types(SECONDARY[2]),False)
    regs=dex.u16(offset)
    incoming=dex.u16(offset+2)
    start=regs-incoming
    if flags & 0x8 or start<0 or "LR29;" not in params:
        raise ValueError("SECONDARY_PARAMETER_LAYOUT")
    stream_param_reg=start+params.index("LR29;")
    receiver_reg=start
    attach_calls=[]
    scoped_events=[]
    for pc,op,raw in insns:
        if op in audit.INVOKES and 0x6e<=op<=0x78:
            callee=dex.method(raw[1])
            kind=classify_secondary_invoke(callee)
            if kind=="EXACT_ATTACH":
                args=audit.invoke_registers(op,raw)
                attach_calls.append({"pc":pc,"callee":list(callee),
                                     "args":args,"op":op,
                                     "incoming_receiver_same_register":bool(args and args[0]==receiver_reg),
                                     "incoming_stream_same_register":bool(len(args)>2 and args[2]==stream_param_reg)})
            elif callee[0] in ("LlQ8;","Landroidx/media3/exoplayer/b;","Landroidx/media3/exoplayer/k;"):
                scoped_events.append({"pc":pc,"kind":"NARROW_CALL",
                                      "callee":list(callee),
                                      "args":audit.invoke_registers(op,raw)})
        elif op in (0x54,0x5b):
            owner,_field,typ=audit.field_id(dex,raw[1])
            if typ=="LR29;" or owner=="LlQ8;":
                scoped_events.append({"pc":pc,"kind":"EXACT_TYPED_FIELD",
                                      "owner":owner,"type":typ,"op":op})
        if len(scoped_events)>MAX_METHOD_EVENTS:
            raise ValueError("SECONDARY_SCOPED_EVENTS_LIMIT")
    e_dex,e_flags,e_offset=engine_enable
    e_insns=list(audit.instructions(e_dex,e_offset))
    if len(e_insns)>MAX_ENGINE_INSNS:raise ValueError("SECONDARY_ENGINE_METHOD_TOO_LARGE")
    e_regs=e_dex.u16(e_offset)
    e_incoming=e_dex.u16(e_offset+2)
    e_params=audit.expand_invoke_register_types(ENGINE_ENABLE[0],
        audit.parse_types(ENGINE_ENABLE[2]),False)
    e_holder_reg=e_regs-e_incoming+e_params.index("Lxh6;")
    e_events=[]
    e_calls=[]
    for pc,op,raw in e_insns:
        if op in audit.INVOKES and 0x6e<=op<=0x78:
            callee=e_dex.method(raw[1])
            if match_secondary_family_invoke(callee):
                e_calls.append({"pc":pc,"callee":list(callee),
                                "args":audit.invoke_registers(op,raw)})
            elif callee[0] in ("Landroidx/media3/exoplayer/k;","Lxh6;","Landroidx/media3/exoplayer/e;"):
                e_events.append({"pc":pc,"op":op,"kind":"NARROW_INVOKE",
                                 "callee":list(callee),"args":audit.invoke_registers(op,raw)})
        elif op in (0x54,0x5b,0x62,0x69):
            owner,_name,typ=audit.field_id(e_dex,raw[1])
            if owner=="Lxh6;" or typ in ("LR29;","[LR29;","LSl6$b;"):
                e_events.append({"pc":pc,"op":op,"kind":"NARROW_FIELD",
                                 "owner":owner,"type":typ})
        elif op in (0x46,0x4d):
            e_events.append({"pc":pc,"op":op,"kind":"ARRAY_OBJECT"})
        elif op in (0x07,0x08,0x09):
            dest,source=audit.move_object_registers(op,raw)
            e_events.append({"pc":pc,"op":op,"kind":"MOVE_OBJECT",
                             "dest":dest,"source":source})
        if len(e_events)>MAX_ENGINE_EVENTS:
            raise ValueError("SECONDARY_ENGINE_EVENTS_LIMIT")
    if sorted(row["pc"] for row in e_calls)!=[131,144]:
        raise ValueError("SECONDARY_ENGINE_EXACT_TWO_CALLS_MISMATCH")
    if len(attach_calls)!=1 or attach_calls[0]["pc"]!=27:
        raise ValueError("SECONDARY_EXACT_ATTACH_PC27_MISMATCH")
    engine_sources=[]
    for caller_dex,caller_method,caller_flags,caller_offset,call_pc,op,args in engine_invokers:
        prior=[(pc,opcode,words) for pc,opcode,words
                in audit.instructions(caller_dex,caller_offset)
                if call_pc-35<=pc<=call_pc+9]
        if len(prior)>MAX_ENGINE_INVOKER_CONTEXT_INSNS:
            raise ValueError("SECONDARY_ENGINE_INVOKER_WINDOW_LIMIT")
        scope=[]
        for pc,opcode,words in prior:
            if opcode in audit.INVOKES and 0x6e<=opcode<=0x78:
                callee=caller_dex.method(words[1])
                if callee==ENGINE_ENABLE or callee[0] in (
                        "Landroidx/media3/exoplayer/e;", "Lxh6;",
                        "LmQ8;", "Landroidx/media3/exoplayer/k;"):
                    scope.append({"pc":pc,"kind":"CALL","callee":list(callee),
                                  "args":audit.invoke_registers(opcode,words)})
            elif opcode in (0x54,0x5b,0x62,0x69):
                owner,_field,typ=audit.field_id(caller_dex,words[1])
                if typ=="Lxh6;" or owner=="Lxh6;" or owner=="Landroidx/media3/exoplayer/e;":
                    scope.append({"pc":pc,"kind":"TYPED_FIELD",
                                  "owner":owner,"type":typ,"op":opcode,
                                  "dest_or_value":(words[0]>>8)&15,
                                  "receiver":(words[0]>>12)&15})
            elif opcode in (0x07,0x08,0x09):
                dst,src=audit.move_object_registers(opcode,words)
                scope.append({"pc":pc,"kind":"MOVE_OBJECT","dest":dst,"source":src})
            elif opcode in (0x0c,):
                scope.append({"pc":pc,"kind":"MOVE_RESULT_OBJECT",
                              "dest":words[0]>>8})
            if len(scope)>MAX_ENGINE_INVOKER_CONTEXT_EVENTS:
                raise ValueError("SECONDARY_ENGINE_INVOKER_EVENTS_LIMIT")
        engine_sources.append({"caller":list(caller_method),"pc":call_pc,
                               "opcode":op,"args":args,"context":scope})
    return {
        "verdict":"NAV22_CONFIRMED_SECONDARY_STATIC_CALLERS_ONLY",
        "exact_method":list(SECONDARY),
        "scanned_method_count":scanned,
        "secondary_method_instruction_count":len(insns),
        "secondary_method_registers":regs,
        "secondary_stream_input_register":stream_param_reg,
        "secondary_receiver_register":receiver_reg,
        "native_attach_calls":attach_calls,
        "other_narrow_calls_fields":scoped_events,
        "direct_secondary_callers":direct,
        "direct_secondary_caller_count":len(direct),
        "secondary_interface_invocation_checked":True,
        "exact_engine_caller":list(ENGINE_ENABLE),
        "engine_enable_direct_invoker_count":len(engine_sources),
        "engine_enable_direct_invokers":engine_sources,
        "exact_engine_holder_input_register":e_holder_reg,
        "exact_engine_instruction_count":len(e_insns),
        "exact_engine_to_renderer_enable_invokes":e_calls,
        "exact_engine_scoped_fields_and_moves":e_events,
        "base_only_caller_count":sum(1 for row in direct if row["dispatch"]=="BASE_DIRECT"),
        "interface_caller_count":sum(1 for row in direct if row["dispatch"]=="INTERFACE_VIRTUAL"),
        "scope":"EXACT_PUBLISHER_2025_SIX_DEX",
        "live_secondary_to_renderer_stream_read_proven_by_owner_nav22":True,
        "currently_audible_track_identity_proven":False,
        "celikom_replacement_connected":False,
        "private_fields_values_or_audio_exported":False
    }

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("SECONDARY_PRIVATE_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("SECONDARY_PINNED_XAPK_SIZE")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("SECONDARY_PINNED_XAPK_SHA256")
    with tempfile.TemporaryDirectory(prefix="celikom-2025-secondary-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:raise ValueError("SECONDARY_16_SPLITS_REQUIRED")
        signature=audit.verify_split_set(apks)
        if signature.get("verified_issuer_signed_splits")!=16:
            raise ValueError("SECONDARY_ISSUER_SIGNATURE_INVALID")
        base=[]
        for apk in apks:
            info=trusted.package_metadata(apk)
            if (info.get("name")!=trusted.EXPECTED_PACKAGE or
                info.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("SECONDARY_EXACT_PUBLISHER_VERSION_MISMATCH")
            if not info.get("split"):base.append(apk)
        if len(base)!=1 or trusted.sha256_file(base[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("SECONDARY_BASE_SHA256_MISMATCH")
        result=scan_exact(apks)
    return dict(result, publisher_signed_input_verified=True,
                original_input_ephemerally_deleted=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",required=True,type=Path)
    args=parser.parse_args()
    try: print(json.dumps(run(args.xapk),sort_keys=True))
    except (ValueError,RuntimeError,audit.DexError,OSError,zipfile.BadZipFile) as exc:
        reason=str(exc)
        print(json.dumps({"verdict":"SECONDARY_STATIC_PROOF_INCOMPLETE",
                          "error_code":reason if re.fullmatch("[A-Z0-9_]{1,90}",reason) else None,
                          "audio_replacement_allowed":False}))
        raise SystemExit(2)
