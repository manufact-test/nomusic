#!/usr/bin/env python3
"""NAV17 signed original: bounded exact Lxh6/Lup1/Lo96 sample-stream origin map.
Static structural routing only. Does not imply selected current audio.
No private field names/values, IDs, URLs, account data or audio read/export.
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
HOLDER="Lxh6;"
WRAPPER="Lup1;"
PERIOD="Lo96;"
MEDIAPERIOD="Lwh6;"
STREAM="LR29;"
STREAM_ARRAY="[LR29;"
OWNER_SET=frozenset((HOLDER,WRAPPER,PERIOD))
MAX_DECLARED_METHODS=110
MAX_INSTRUCTIONS_PER_METHOD=720
MAX_EVENTS_PER_METHOD=90
MAX_TOTAL_EVENTS=500

def scope_owner(owner):
    return owner in OWNER_SET

def scope_call(method):
    owner,name,desc=method
    return (owner in (HOLDER,WRAPPER,PERIOD,MEDIAPERIOD,STREAM) or
            STREAM in audit.parse_types(desc) or
            STREAM_ARRAY in audit.parse_types(desc) or
            STREAM in desc.split(")",1)[1] or STREAM_ARRAY in desc.split(")",1)[1])


EXACT_RENDERER_COMPARE_METHODS=frozenset({
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"),
})
HOLDER_CONSTRUCTOR=("Lxh6;","<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
HOLDER_SELECT=("Lxh6;","if","(LRFa;JZ[Z)J")
PERIOD_WRAPPER_SELECT=("Lup1;","case","([Lw24;[Z[LR29;[ZJ)J")
ORIGINAL_PERIOD_SELECT=("Lo96;","case","([Lw24;[Z[LR29;[ZJ)J")
PERIOD_INTERFACE_SELECT=("Lwh6;","case","([Lw24;[Z[LR29;[ZJ)J")
SHARED_FIELD_USE_PCS={
    HOLDER_CONSTRUCTOR:(30,0x5b),
    HOLDER_SELECT:(63,0x54),
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"):(4,0x54),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"):(2,0x54),
}

def verify_exact_shared_stream_field(methods):
    """Opaque complete DEX field-ref equality across verified call chain.
    No field name/index/value exported or logged."""
    field_refs=[]
    for method,(pc,opcode) in SHARED_FIELD_USE_PCS.items():
        if method not in methods or not methods[method][2]:
            raise ValueError("STREAM_SHARED_FIELD_OWNER_BODY_MISSING")
        dex,flags,off=methods[method]
        insns={pc_:(op,words) for pc_,op,words in audit.instructions(dex,off)}
        insn=insns.get(pc)
        if not insn or insn[0]!=opcode:
            raise ValueError("STREAM_SHARED_FIELD_OPCODE_MISMATCH")
        owner,_private_name,typ=audit.field_id(dex,insn[1][1])
        if owner!=HOLDER or typ!=STREAM_ARRAY:
            raise ValueError("STREAM_SHARED_FIELD_TYPE_MISMATCH")
        field_refs.append((owner,_private_name,typ))
    if len(set(field_refs))!=1:
        raise ValueError("STREAM_SHARED_FIELD_REFERENCE_MISMATCH")
    return {"same_exact_holder_stream_array_field_from_all_four_methods":True,
            "holder_allocation_store_pc":30,
            "holder_selection_read_pc":63,
            "renderer_compare_reads_pcs":[4,2],
            "private_field_names_or_values_exported":False}

def limited_stream_selection_bytecode(method,entry):
    """Register topology on 4 exact relevant methods; no constant or field names."""
    dex,flags,off=entry
    insns=list(audit.instructions(dex,off))
    if len(insns)>140:raise ValueError("STREAM_EXACT_SELECTION_METHOD_SIZE_LIMIT")
    rows=[]
    for pc,op,words in insns:
        r={"pc":pc}
        if 0x52<=op<=0x6d:
            owner,_private_name,typ=audit.field_id(dex,words[1])
            if typ not in (STREAM_ARRAY,MEDIAPERIOD,WRAPPER,PERIOD):
                continue
            r.update(action="FIELD_TYPED",owner=owner,type=typ,opcode=op,
                     first_reg=(words[0]>>8)&15,second_reg=(words[0]>>12)&15)
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            m=dex.method(words[1])
            if m not in (PERIOD_INTERFACE_SELECT,PERIOD_WRAPPER_SELECT,ORIGINAL_PERIOD_SELECT):
                continue
            r.update(action="PERIOD_SELECT_CALL",callee=list(m),
                     registers=audit.invoke_registers(op,words))
        elif op in (0x07,0x08,0x09):
            d,source=audit.move_object_registers(op,words)
            r.update(action="MOVE_OBJECT",dest=d,source=source)
        elif op in (0x0a,0x0b,0x0c):
            r.update(action="MOVE_RESULT",dest=words[0]>>8)
        elif op in (0x46,0x4d):
            r.update(action="STREAM_ARRAY_ELEMENT",opcode=op,
                     first_reg=(words[0]>>8)&255)
        elif op in (0x23,0x24,0x25) and dex.descriptor(words[1])==STREAM_ARRAY:
            r.update(action="NEW_STREAM_ARRAY")
        elif op in (0x28,0x29,0x2a) or 0x32<=op<=0x3d:
            r.update(action="BRANCH",opcode=op)
        else:continue
        rows.append(r)
        if len(rows)>100:
            raise ValueError("STREAM_EXACT_SELECTION_BYTECODE_ROW_LIMIT")
    return {"method":list(method),"steps":rows}


def exact_holder_period_receiver_shape(method,entry):
    """Anonymised field/type/register shape, no private names/values."""
    dex,flags,off=entry
    rows=[]
    for pc,op,words in audit.instructions(dex,off):
        if 0x52<=op<=0x6d:
            owner,_name,typ=audit.field_id(dex,words[1])
            if owner==HOLDER or owner==WRAPPER or typ in (HOLDER,WRAPPER,MEDIAPERIOD):
                rows.append({"pc":pc,"kind":"FIELD","op":op,
                            "owner":owner,"type":typ,
                            "first":(words[0]>>8)&15,"second":(words[0]>>12)&15})
        elif 0x6e<=op<=0x78:
            m=dex.method(words[1])
            if m[0] in (HOLDER,WRAPPER,MEDIAPERIOD) or m[1]=="<init>" and m[0]==WRAPPER:
                rows.append({"pc":pc,"kind":"CALL","callee":list(m),
                             "registers":audit.invoke_registers(op,words)})
        if len(rows)>130:
            raise ValueError("STREAM_EXACT_HOLDER_FIELD_SCOPE_EXCEEDED")
    return {"method":list(method),"events":rows}
def scan(apks):
    dexes=0
    methods={}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("STREAM_ORIGIN_SIGNED_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes+=1
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if not (scope_owner(method[0]) or method in EXACT_RENDERER_COMPARE_METHODS):continue
                    if method in methods:raise ValueError("STREAM_ORIGIN_DUPLICATE_METHOD")
                    methods[method]=(dex,flags,off)
                    if len(methods)>MAX_DECLARED_METHODS:
                        raise ValueError("STREAM_ORIGIN_METHOD_COUNT_LIMIT")
    if dexes!=6 or not all(any(m[0]==owner for m in methods) for owner in OWNER_SET):
        raise ValueError("STREAM_ORIGIN_EXACT_SIGNED_CLASS_MISSING")
    rows=[]
    total_events=0
    for method,(dex,flags,off) in sorted(methods.items()):
        if not off or not scope_owner(method[0]):continue
        insns=list(audit.instructions(dex,off))
        if len(insns)>MAX_INSTRUCTIONS_PER_METHOD:
            raise ValueError("STREAM_ORIGIN_METHOD_SIZE_LIMIT")
        events=[]
        for pc,op,words in insns:
            if 0x52<=op<=0x6d:
                owner,_private,typ=audit.field_id(dex,words[1])
                if typ in (STREAM,STREAM_ARRAY,MEDIAPERIOD,WRAPPER,PERIOD) and owner in OWNER_SET:
                    events.append({"pc":pc,"action":"FIELD_READ" if op<=0x58 else "FIELD_WRITE",
                                   "opcode":op,"owner":owner,"type":typ})
            elif op in audit.INVOKES and 0x6e<=op<=0x78:
                called=dex.method(words[1])
                if scope_call(called):
                    events.append({"pc":pc,"action":"CALL","owner":called[0],"name":called[1],
                                   "signature":called[2]})
            elif op in (0x23,0x24,0x25):
                type_=dex.descriptor(words[1])
                if type_==STREAM_ARRAY:
                    events.append({"pc":pc,"action":"NEW_TYPED_STREAM_ARRAY","type":type_})
            elif op in (0x46,0x4d):
                events.append({"pc":pc,"action":"STREAM_ARRAY_READ_OR_WRITE_CANDIDATE",
                               "opcode":op})
            if len(events)>MAX_EVENTS_PER_METHOD:
                raise ValueError("STREAM_ORIGIN_METHOD_EVENT_LIMIT")
        total_events+=len(events)
        if total_events>MAX_TOTAL_EVENTS:
            raise ValueError("STREAM_ORIGIN_TOTAL_EVENT_LIMIT")
        if events or (method[0]==HOLDER and method[1]=="<init>"):
            rows.append({"method":list(method),"instruction_count":len(insns),
                         "events":events})
    holder_period_receiver_shapes=[
        exact_holder_period_receiver_shape(method,methods[method])
        for method in (HOLDER_CONSTRUCTOR,HOLDER_SELECT,PERIOD_WRAPPER_SELECT)
    ]
    shared_field=verify_exact_shared_stream_field(methods)
    selected=[]
    for method in (HOLDER_CONSTRUCTOR,HOLDER_SELECT,PERIOD_WRAPPER_SELECT,ORIGINAL_PERIOD_SELECT):
        selected.append(limited_stream_selection_bytecode(method,methods[method]))
    return {"exact_holder_period_receiver_shapes":holder_period_receiver_shapes,
            "exact_shared_holder_stream_field":shared_field,
            "exact_stream_selection_register_topology":selected,
            "verdict":"SIGNED_EXACT_HOLDER_STREAM_OWNER_STRUCTURAL_MAP",
            "six_signed_dex_verified":dexes,
            "class_method_count":{owner:sum(m[0]==owner for m in methods) for owner in sorted(OWNER_SET)},
            "scoped_methods_with_stream_or_period_uses":rows,
            "static_map_only_no_live_selection":True,
            "active_period_stream_to_decoder_proven":False,
            "replacement_audio_connected":False,
            "private_field_names_values_media_ids_urls_or_audio_exported":False}

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("STREAM_ORIGIN_EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("STREAM_ORIGIN_PINNED_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("STREAM_ORIGIN_PINNED_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-stream-origin-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:
            raise ValueError("STREAM_ORIGIN_SIGNED_SPLITS_REQUIRED")
        sig=audit.verify_split_set(apks)
        if sig.get("verified_issuer_signed_splits")!=16:
            raise ValueError("STREAM_ORIGIN_PUBLISHER_SIGNER_MISMATCH")
        base=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if meta.get("name")!=trusted.EXPECTED_PACKAGE or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("STREAM_ORIGIN_ORIGINAL_VERSION_MISMATCH")
            if not meta.get("split"):base.append(apk)
        if len(base)!=1 or trusted.sha256_file(base[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("STREAM_ORIGIN_NAV17_BASE_MISMATCH")
        result=scan(apks)
    return {**result,"signed_original_ephemeral_only":True}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(run(args.xapk),sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as err:
        msg=str(err)
        print(json.dumps({"verdict":"STREAM_ORIGIN_INCOMPLETE",
            "safe_error_code":msg if re.fullmatch(r"[A-Z0-9_]{1,90}",msg) else None,
            "active_period_stream_to_decoder_proven":False}))
        raise SystemExit(2)
