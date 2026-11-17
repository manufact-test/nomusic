#!/usr/bin/env python3
"""Signed NAV17 Yandex: narrowly track exact ExoPlayer.e(LSl6,J) implementors.

Start from proven LcA9 -> LA14.e -> ExoPlayer.e same-object source handoff.
Inspect only declarations with the *exact* ExoPlayer source method signature
and their bounded call/field-write structure; cannot establish runtime
selected item, source-to-MediaPeriod, renderer, generation or actual sound.
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
from exo_factory_exact_consumer import class_metadata

audit=trusted.audit
INTERFACE="Landroidx/media3/exoplayer/ExoPlayer;"
SOURCE="LSl6;"
SOURCE_SETTER=("e","(LSl6;J)V")
SOURCE_SETTER_NO_POS=("T","(LSl6;)V")
KNOWN_PLAYER_RECEIVER="LA14;"
PLAYER_GETTER=("LA14;","v0","()Landroidx/media3/exoplayer/ExoPlayer;")
MAX_SOURCE_CONTRACT_OWNERS=28
MAX_PLAYER_IMPLEMENTORS=24
MAX_SOURCE_METHOD_INVOKES=110
MAX_SITE_ENTRIES=100


def exact_source_setter(method):
    return method[1:] == SOURCE_SETTER


def declared_source_setter(method):
    return method[1:] in (SOURCE_SETTER,SOURCE_SETTER_NO_POS)


def decoded_class_row(dex, index):
    pos=dex.class_offset+index*32
    owner=dex.descriptor(dex.u32(pos))
    superclass_idx=dex.u32(pos+8)
    superclass=(dex.descriptor(superclass_idx) if superclass_idx != 0xFFFFFFFF else None)
    off=dex.u32(pos+12)
    interfaces=[]
    if off:
        size=dex.u32(off)
        if size>72:raise ValueError("EXOPLAYER_CLASS_INTERFACE_LIMIT")
        interfaces=[dex.descriptor(dex.u16(off+4+i*2)) for i in range(size)]
    return owner,superclass,interfaces,dex.u32(pos+4)


def inspect(apks):
    dexes=[]
    declarations={}
    class_graph={}
    source_owners={}
    getter=None
    getter_referenced=False
    total_dex=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("EXOPLAYER_EXACT_DEX_LIMIT")
                total_dex+=1
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for i in range(dex.class_count):
                    owner,supercls,interfaces,access=decoded_class_row(dex,i)
                    if owner in class_graph:
                        raise ValueError("EXOPLAYER_DUPLICATE_CLASS")
                    class_graph[owner]=(supercls,interfaces,access)
                for mid in range(dex.method_count):
                    if dex.method(mid)==PLAYER_GETTER:
                        getter_referenced=True
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if declared_source_setter(method):
                        source_owners.setdefault(method[0],0)
                        source_owners[method[0]]+=1
                        if len(source_owners)>MAX_SOURCE_CONTRACT_OWNERS:
                            raise ValueError("EXOPLAYER_SOURCE_OWNER_LIMIT")
                        declarations[method]=(dex,flags,code_off)
                    if method==PLAYER_GETTER:
                        getter=(dex,flags,code_off)

    if total_dex!=6:raise ValueError("EXOPLAYER_SIGNED_SIX_DEX_REQUIRED")
    if not getter_referenced:
        raise ValueError("EXOPLAYER_RECEIVER_GETTER_REFERENCE_MISSING")
    if INTERFACE not in class_graph:raise ValueError("EXOPLAYER_INTERFACE_MISSING")
    def reaches(owner,ancestor):
        pending=[owner];seen=set()
        for i in range(160):
            if not pending:break
            cur=pending.pop()
            if cur==ancestor:return True
            if cur in seen:continue
            seen.add(cur)
            if cur in class_graph:
                sup,interfaces,_=class_graph[cur]
                if sup:pending.append(sup)
                pending.extend(interfaces)
        return False

    source_ancestor_owners=sorted(owner for owner in source_owners
        if reaches(owner,INTERFACE) or owner==KNOWN_PLAYER_RECEIVER)
    concrete_implementors=sorted(owner for owner,(parent,interfaces,flags) in class_graph.items()
        if owner!=INTERFACE and not (flags&0x0200) and not (flags&0x0400)
        and reaches(owner,INTERFACE))
    if len(concrete_implementors)>MAX_PLAYER_IMPLEMENTORS:
        raise ValueError("EXOPLAYER_CONCRETE_IMPLEMENTORS_LIMIT")
    implementations=[]
    for method,(dex,flags,code_off) in sorted(declarations.items()):
        if method[0] not in source_ancestor_owners:
            continue
        calls=[]
        source_typed_calls=[]
        source_typed_fields=[]
        if code_off:
            for ordinal,op,words in audit.instructions(dex,code_off):
                if op in audit.INVOKES and 0x6E<=op<=0x78:
                    callee=dex.method(words[1])
                    if len(calls)>=MAX_SOURCE_METHOD_INVOKES:
                        raise ValueError("EXOPLAYER_SETTER_INVOKE_LIMIT")
                    row={
                        "ordinal":ordinal,"callee_owner":callee[0],
                        "callee_method":callee[1],"callee_signature":callee[2],
                        "invoke_opcode":op
                    }
                    calls.append(row)
                    if SOURCE in audit.parse_types(callee[2]) or callee[2].endswith(")"+SOURCE):
                        source_typed_calls.append(row)
                if op in (0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d):
                    # instance/static put; only report exact type, never field name/value
                    owner,_name,typ=audit.field_id(dex,words[1])
                    if typ==SOURCE:
                        source_typed_fields.append({
                            "ordinal":ordinal,
                            "declaring_owner":owner,"field_type":typ,
                        })
            if len(source_typed_fields)>36:raise ValueError("EXOPLAYER_TYPED_FIELD_STORE_LIMIT")
        try:
            cfg=(audit.trace_track_identity_method_cfg(
                dex,method,flags,code_off,
                extra_identity_types={
                    SOURCE:"NATIVE_SOURCE",
                    "Landroidx/media3/exoplayer/ExoPlayer;":"EXO_PLAYER",
                }) if code_off else None)
            flow=[
                row for row in (cfg.get("events",()) if cfg else ())
                if row.get("kind") in (
                    "CALL_WITH_TYPED_IDENTITY","CALL_WITH_POSSIBLE_IDENTITY",
                    "RETURN_TYPED_IDENTITY","FIELD_STORE_TYPED_IDENTITY")
                and (row.get("identity_type")=="NATIVE_SOURCE" or
                   any(y.get("identity_type")=="NATIVE_SOURCE"
                       for y in row.get("identity_arguments",[])) or
                   any(y.get("identity_type")=="NATIVE_SOURCE"
                       for y in row.get("possible_identity_arguments",[])))
            ][:48]
            failure=None
        except (ValueError,audit.DexError) as e:
            cfg=None;flow=[]
            err=str(e)
            failure=err if re.fullmatch("[A-Z0-9_]{1,80}",err) else "INCOMPLETE_CFG"
        implementations.append({
            "owner":method[0],"method":method[1],"signature":method[2],
            "code_declared":bool(code_off),
            "exoplayer_ancestry":reaches(method[0],INTERFACE),
            "direct_calls":calls,
            "source_typed_callees":source_typed_calls,
            "source_field_puts":source_typed_fields,
            "source_object_cfg_events":flow,
            "cfg_state_count":cfg.get("path_state_count") if cfg else None,
            "cfg_failure":failure,
        })
    if len(implementations)>48:raise ValueError("EXOPLAYER_IMPLEMENTATION_ROW_LIMIT")
    # Existing LA14.v0 only; do not try to infer runtime instance.
    getter_events=[]
    getter_error=None
    if getter and getter[2]:
        dex,flags,code_off=getter
        try:
            trace=audit.trace_identity_method(dex,PLAYER_GETTER,flags,code_off,
                extra_identity_types=("Landroidx/media3/exoplayer/ExoPlayer;",),
                track_fields_from_any_receiver=True)
            getter_events=[
                e for e in trace.get("events",())
                if "EXTRA_OBJECT:Landroidx/media3/exoplayer/ExoPlayer;" in str(e)
            ][:20]
        except (ValueError,audit.DexError) as e:
            getter_error=type(e).__name__
    else:
        # Interface / superclass reference is not an exact body definition.
        getter_error="GETTER_REFERENCED_BUT_NOT_DECLARED_IN_OWNER"
    return {
        "verdict":"EXACT_SOURCE_SETTER_IMPLEMENTATION_CANDIDATES_NOT_ACTIVE_PLAYBACK",
        "six_publisher_signed_dex":total_dex,
        "player_source_contract_owner_count":len(source_owners),
        "exoplayer_source_contract_owners":source_ancestor_owners,
        "concrete_exoplayer_implementors":concrete_implementors,
        "exact_player_source_setter_implementations":implementations,
        "exact_player_getter":PLAYER_GETTER,
        "player_getter_reference_in_signed_dex":getter_referenced,
        "player_getter_body_in_exact_owner":bool(getter and getter[2]),
        "player_getter_events":getter_events,
        "player_getter_trace_error":getter_error,
        "runtime_same_player_receiver_to_active_item_proven":False,
        "active_media_period_or_decoder_proven":False,
        "album_edition_duration_generation_proven":False,
        "replacement_audio_proven":False,
        "ids_private_fields_urls_or_audio_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("SOURCE_COMMIT_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("SOURCE_COMMIT_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exoplayer-setter-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("EXOPLAYER_16_SIGNED_SPLITS_EXPECTED")
        sig=audit.verify_split_set(splits)
        if sig.get("verified_issuer_signed_splits")!=16:
            raise ValueError("EXOPLAYER_SIGNED_PUBLISHER_MISMATCH")
        bases=[]
        for apk in splits:
            m=trusted.package_metadata(apk)
            if (m.get("name")!=trusted.EXPECTED_PACKAGE or
                m.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("EXOPLAYER_SIGNED_PACKAGE_VERSION_MISMATCH")
            if not m.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("EXOPLAYER_NAV17_BASE_MISMATCH")
        result=inspect(splits)
    return {**result,"signed_exact_NAV17_original":True,"ephemeral_readonly":True}


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xapk",required=True,type=Path)
    args=ap.parse_args()
    try:
        print(json.dumps(run(args.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({"verdict":"SOURCE_COMMIT_EXACT_AUDIT_INCOMPLETE",
            "safe_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "replacement_audio_proven":False}))
        raise SystemExit(2)
