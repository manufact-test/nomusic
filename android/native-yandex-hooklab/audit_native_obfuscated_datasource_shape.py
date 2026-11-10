#!/usr/bin/env python3
"""Signed-original DEX: exact obfuscated Lm48 DataSource-like API candidate.

This is a read-only type and caller census. The same FileInfo model reaches
a candidate factory Le48.a -> Lm48 with open/read/close-like signatures, but
no current track, actual source selection, pre-prepare or decoder is proven.
No APK, DEX, string constant, URL, media, credentials or app patch exported.
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
from trace_native_callers import method_definitions,INVOKES
from trace_native_source_hops import inspect_one_dex
from audit_native_media_implementors import relations,transitive_implementors
from audit_native_typed_wrapper_coroutines import (
    brief_type,method_profile,class_field_shapes
)
from audit_native_postfileinfo_lifecycle import merge_reverse
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

SOURCE_INTERFACE="Lm48;"
DATA_READER_ANCESTOR="Lv38;"
FACTORY_INTERFACE="Le48;"
DATASPEC="La58;"
TARGET_OWNER_NAMES={
 "Lm48;","Lv38;","Le48;","Lha4;","Lza4;","Lzcd;",
 "Luiq;","Lz3f;","Lga4;","Lcq7;","Leyc;","La58;",
}
KEEP_METHODS={
 "Lcq7;":{"A","i0"},
 "Leyc;":{"d"},
 "Lga4;":{"a","b","c","d"},
 "Luiq;":{"a","<init>"},
 "Lha4;":{"b","c","d","f","close","read","getUri","<init>"},
 "Lza4;":{"b","c","d","f","close","read","getUri","<init>"},
 "Lz3f;":{"<init>"},
}
MAX_CLASSES=400000
MAX_SUBTYPES=300
MAX_METHODS_PER_OWNER=80
MAX_CALLERS=30
MAX_METHOD_REF_PROFILES=100
MAX_GRAPH_NODES=2000000


def exact_shape(triple):
    return method_profile(triple)


def api_shape_census(methods):
    """Use only structural JVM descriptors; not an identity claim."""
    triples={(m[1],m[2]) for m in methods}
    long_dataspec_any=any(p.startswith("("+DATASPEC+")J") for _,p in triples)
    array_read=any(p.startswith("([BII)I") for _,p in triples)
    uri_accessor=any(n=="getUri" for n,_ in triples)
    close_accessor=any(n=="close" for n,_ in triples)
    return {
        "dataspec_to_long_signature":long_dataspec_any,
        "byte_array_read_signature":array_read,
        "get_uri_named_method":uri_accessor,
        "close_named_method":close_accessor,
        "data_source_like_signature_complete":
            all((long_dataspec_any,array_read,uri_accessor,close_accessor)),
        "actual_instantiated_music_decoder_datasource_proven":False,
    }


def signed_class_and_method_shapes(apks):
    relationships={}
    owners=defaultdict(set)
    definitions=defaultdict(set)
    fields={}
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):continue
                if item.file_size>DEX_MAX:raise ValueError("SIGNED_DEX_SIZE_LIMIT")
                d=Dex(z.read(item.filename))
                dex_count+=1
                rel=relations(d)
                intersection=set(relationships).intersection(rel)
                if intersection:raise ValueError("CROSS_DEX_DUPLICATE")
                relationships.update(rel)
                if len(relationships)>MAX_CLASSES:raise ValueError("CLASS_COUNT_LIMIT")
                for owner in TARGET_OWNER_NAMES:
                    if owner in rel:
                        fields[owner]=class_field_shapes(d,owner)
                for i in range(d.method_count):
                    m=d.method(i)
                    if m[0] in TARGET_OWNER_NAMES:
                        owners[m[0]].add(m)
                for idx,off in method_definitions(d):
                    m=d.method(idx)
                    if m[0] in TARGET_OWNER_NAMES:
                        definitions[m[0]].add(m)
    if dex_count!=6:raise ValueError("SIX_SIGNED_DEX_REQUIRED")
    if SOURCE_INTERFACE not in relationships or DATA_READER_ANCESTOR not in relationships:
        raise ValueError("OBFUSCATED_DATASOURCE_INTERFACE_MISSING")
    if FACTORY_INTERFACE not in relationships:
        raise ValueError("FACTORY_INTERFACE_MISSING")
    implementors=transitive_implementors(relationships,SOURCE_INTERFACE)
    if len(implementors)>MAX_SUBTYPES:raise ValueError("TOO_MANY_DATASOURCE_IMPLEMENTORS")
    classes={}
    for owner in sorted(TARGET_OWNER_NAMES):
        if owner not in relationships:continue
        flags,parents=relationships[owner]
        classes[brief_type(owner)]={
            "flags":flags,
            "parents":[brief_type(x) for x in parents],
            "field_type_counts":{
                t:fields.get(owner,[]).count(t) for t in sorted(set(fields.get(owner,[])))},
            "defined_methods":[exact_shape(m) for m in
                 sorted(definitions[owner])[:MAX_METHODS_PER_OWNER]],
            "method_ref_count":len(owners.get(owner,())),
        }
    return {
        "original_dex_count":dex_count,
        "types":classes,
        "data_reader_method_shapes":api_shape_census(owners[DATA_READER_ANCESTOR]),
        "data_source_method_shapes":api_shape_census(owners[SOURCE_INTERFACE]),
        "data_source_concrete_implementor_count":len(implementors),
        "concrete_implementor_examples":[brief_type(t) for t in implementors[:MAX_SUBTYPES]],
        "ha4_is_implementor":"Lha4;" in implementors,
        "za4_is_implementor":"Lza4;" in implementors,
        "actual_source_ownership_current_audio_proven":False,
    }


def signed_datasource_callsite_census(apks):
    scans=[]
    count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if not re.fullmatch(r"classes[0-9]*\.dex",name):continue
                d=Dex(z.read(name))
                scans.append(inspect_one_dex(d.data.tobytes()))
                count+=1
    if count!=6:raise ValueError("SIX_DEX_REQUIRED")
    reverse=merge_reverse(scans)
    targets={
        m for m in reverse
        if m[0] in {SOURCE_INTERFACE,DATA_READER_ANCESTOR,FACTORY_INTERFACE}
    }
    row=[]
    source_callers=set()
    for m in sorted(targets):
        callers=reverse[m]
        if m[0]==SOURCE_INTERFACE:
            source_callers.update(callers)
        row.append({
            "interface_method":exact_shape(m),
            "direct_caller_count":len(callers),
            "bounded_caller_hints":[bounded_obfuscated(x) for x in sorted(callers)[:MAX_CALLERS]],
            "active_decoder_or_current_track_proven":False,
        })
    return {
        "interface_method_invoked_count":len(targets),
        "interface_callsite_hints":row[:MAX_METHOD_REF_PROFILES],
        "unique_direct_source_interface_callers":len(source_callers),
        "source_interface_caller_owner_examples":[brief_type(c) for c in sorted({t[0] for t in source_callers})[:MAX_CALLERS]],
        "source_interface_called_by_known_obfuscated_exoplayer_implementor":any(
            t[0] in ("Lfxc;","Lro7;","Lwxc;","Lyzt;") for t in source_callers),
        "not_actual_register_dataflow_or_preprepare_proof":True,
    }


def scan_signed(apks):
    return {
        "obfuscated_native_source_api":signed_class_and_method_shapes(apks),
        "six_dex_direct_source_interface_callers":signed_datasource_callsite_census(apks),
        "actual_trackid_edition_generation_to_decoding_source_proven":False,
        "playable_android_replacement_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-original-m48-types-") as temp:
        root=Path(temp)
        archive=root/"publisher-unchanged.xapk"
        length,sha=exact.gpr.download(archive)
        if length!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("PINNED_ORIGINAL_HASH")
        splits=exact.gpr.split_apks(archive,root)
        if len(splits)!=5:raise ValueError("FIVE_SIGNED_SPLITS")
        exact.gpr.inspect_publisher(splits)
        result=scan_signed(splits)
    return {"verdict":"SIGNED_OBFUSCATED_NATIVE_DATASOURCE_SIGNATURE_AND_CALLERS_ONLY",
            "publisher_original":"2026.10.3 #170gpr",**result,
            "original_binary_modification_or_export":False,
            "user_account_drm_or_media_access":False}


if __name__=="__main__":
    try:print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({"verdict":"SIGNED_NATIVE_DATASOURCE_SIGNATURE_SCAN_INCOMPLETE",
                          "error_class_only":type(exc).__name__,
                          "playable_android_replacement_proven":False}))
        sys.exit(2)
