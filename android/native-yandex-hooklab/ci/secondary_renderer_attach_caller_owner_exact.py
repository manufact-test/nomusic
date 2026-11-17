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
MAX_METHOD_INSNS=600
MAX_DIRECT_CALLERS=75
MAX_METHOD_EVENTS=80
MAX_SCANNED_METHODS=180000
MAX_CALLERS_REPORT=75

def match_direct_secondary_invoke(callee):
    return tuple(callee)==SECONDARY

def classify_secondary_invoke(callee):
    if tuple(callee)==SECONDARY: return "EXACT_SECONDARY"
    if tuple(callee)==ATTACH or tuple(callee)==ATTACH_INTERFACE: return "EXACT_ATTACH"
    return "OTHER"

def scan_exact(apks):
    scanned=0
    exact_secondary=None
    direct=[]
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
                    for pc,op,raw in audit.instructions(dex,offset):
                        if op not in audit.INVOKES or not (0x6e<=op<=0x78):
                            continue
                        callee=dex.method(raw[1])
                        if not match_direct_secondary_invoke(callee):continue
                        direct.append({"caller":list(method),"pc":pc,"opcode":op,
                                       "args":audit.invoke_registers(op,raw)})
                        if len(direct)>MAX_DIRECT_CALLERS:
                            raise ValueError("SECONDARY_TOO_MANY_DIRECT_CALLERS")
    if exact_secondary is None:raise ValueError("SECONDARY_EXACT_METHOD_MISSING")
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
    if len(attach_calls)!=1 or attach_calls[0]["pc"]!=27:
        raise ValueError("SECONDARY_EXACT_ATTACH_PC27_MISMATCH")
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
