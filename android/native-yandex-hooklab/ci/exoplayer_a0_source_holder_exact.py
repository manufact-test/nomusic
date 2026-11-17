#!/usr/bin/env python3
"""Exact signed Yandex 2025 native source List -> d.A0 source-holder constructor.

Bounded to the newly proven ExoPlayer.d.T0 -> A0(List,int) playlist admission.
Reports only DEX method type descriptors and per-method reference flow. Does not
infer List.get element identity without a verified immutable singleton origin.
Does not read Track fields, URLs, audio or user data.
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
OWNER="Landroidx/media3/exoplayer/d;"
SOURCE="LSl6;"
TARGET=(OWNER,"A0","(Ljava/util/List;I)Ljava/util/ArrayList;")
PARENT=(OWNER,"T0","(Ljava/util/List;IJZ)V")
MAX_INVOKES=140
MAX_OBJECT_CREATIONS=64
MAX_TYPED_FIELDS=48


def exact_source_handoff(method):
    return method in (TARGET,PARENT)


def scan_signed(splits):
    dexes=[]
    defs={}
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:raise ValueError("A0_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if exact_source_handoff(method):
                        if method in defs:raise ValueError("A0_DUPLICATE_TARGET")
                        defs[method]=(dex,flags,off)
    if len(dexes)!=6:raise ValueError("A0_EXPECTED_SIX_SIGNED_DEX")
    if set(defs)!={TARGET,PARENT}:raise ValueError("A0_TARGET_BODY_NOT_FOUND")
    dex,flags,off=defs[TARGET]
    if not off:raise ValueError("A0_TARGET_NOT_EXECUTABLE")
    methods=[]
    instance_creations=[]
    field_refs=[]
    invoked_by_target=[]
    source_methods=[]
    list_methods=[]
    counts={"list_get":0,"iterator":0,"source_constructor":0}
    for ordinal,op,words in audit.instructions(dex,off):
        if op==0x22:
            descriptor=dex.descriptor(words[1])
            instance_creations.append({"ordinal":ordinal,"descriptor":descriptor})
            if len(instance_creations)>MAX_OBJECT_CREATIONS:
                raise ValueError("A0_OBJECT_CREATION_LIMIT")
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            callee=dex.method(words[1])
            row={"ordinal":ordinal,"owner":callee[0],"method":callee[1],
                 "signature":callee[2],"opcode":op}
            methods.append(row)
            if len(methods)>MAX_INVOKES:raise ValueError("A0_INVOKE_LIMIT")
            if callee[0] in ("Ljava/util/List;","Ljava/util/Iterator;",
                             "Ljava/util/Collection;"):
                list_methods.append(row)
                if callee[1]=="get":counts["list_get"]+=1
                if callee[1]=="iterator":counts["iterator"]+=1
            if SOURCE in audit.parse_types(callee[2]):
                source_methods.append(row)
                if callee[1]=="<init>":counts["source_constructor"]+=1
        if 0x52<=op<=0x6d:
            owner,_field_name,typ=audit.field_id(dex,words[1])
            if typ in (SOURCE,"Ljava/util/List;","Ljava/util/ArrayList;"):
                field_refs.append({"ordinal":ordinal,"owner":owner,"field_type":typ,
                                   "opcode":op})
                if len(field_refs)>MAX_TYPED_FIELDS:raise ValueError("A0_TYPED_FIELD_LIMIT")
    try:
        trace=audit.trace_track_identity_method_cfg(dex,TARGET,flags,off,
                extra_identity_types={
                    "Ljava/util/List;":"SOURCE_ADMISSION_LIST",
                    SOURCE:"NATIVE_MEDIA_SOURCE",
                    "Ljava/util/ArrayList;":"SOURCE_HOLDER_LIST",
                })
        events=[
            e for e in trace["events"]
            if (e.get("identity_type") in ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                or any(x.get("identity_type") in
                       ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                       for x in e.get("identity_arguments",[]))
                or any(x.get("identity_type") in
                       ("SOURCE_ADMISSION_LIST","NATIVE_MEDIA_SOURCE")
                       for x in e.get("possible_identity_arguments",[])))
        ]
        cfg_states=trace.get("processed_state_count");cfg_failure=None
    except (ValueError,audit.DexError) as e:
        events=[];cfg_states=None;cfg_failure=type(e).__name__

    # Parent proof is from the exact successful T0 audit:
    # d.e(source) -> singletonList(source) -> d.T0(theList) -> d.A0(theList).
    return {
        "verdict":"EXACT_A0_PLAYLIST_SOURCE_HOLDER_CANDIDATES_ONLY",
        "six_publisher_signed_dex":len(dexes),
        "exact_owner":TARGET[0],"exact_method":TARGET[1],
        "target_invokes":methods,
        "source_typed_invokes":source_methods,
        "list_or_iterator_invokes":list_methods,
        "target_new_instances":instance_creations,
        "target_typed_field_access":field_refs,
        "operation_counters":counts,
        "typed_list_cfg_events":events[:48],
        "typed_list_cfg_events_truncated":len(events)>48,
        "cfg_state_count":cfg_states,
        "cfg_error_class":cfg_failure,
        "active_selected_media_period_confirmed":False,
        "same_source_to_current_decoder_proven":False,
        "selected_track_album_edition_duration_generation_proven":False,
        "replacement_audio_connected":False,
        "private_field_names_or_values_urls_audio_read":False,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("A0_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("A0_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-exoplayer-a0-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("A0_16_SIGNED_SPLITS_REQUIRED")
        issuer=audit.verify_split_set(splits)
        if issuer.get("verified_issuer_signed_splits")!=16:
            raise ValueError("A0_ISSUER_SIGNATURE_MISMATCH")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE or
                meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("A0_PINNED_PACKAGE_IDENTITY_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("A0_NAV17_BASE_SHA_MISMATCH")
        report=scan_signed(splits)
    return {**report,"signed_exact_NAV17_verified":True,"read_only_ephemeral":True}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xapk",required=True,type=Path)
    a=parser.parse_args()
    try:print(json.dumps(run(a.xapk),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({"verdict":"A0_SOURCE_HOLDER_AUDIT_INCOMPLETE",
             "safe_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
             "replacement_audio_connected":False}))
        raise SystemExit(2)
