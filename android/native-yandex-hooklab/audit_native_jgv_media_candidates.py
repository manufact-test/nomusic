#!/usr/bin/env python3
"""Pinned publisher signed DEX: typed Ljgv consumers and media-adjacent factories.

Starts from FileInfo-backed Ldiv -> Lygv.r(Ldiv) -> Ljgv. Examine only real
methods referring to Ljgv, and class hierarchy of their returned models.
Direct call proximity never proves current playback, register value-to-source
binding, decoder prepare, or installation. Nothing is patched or exported.
"""
from __future__ import annotations

from collections import defaultdict, Counter, deque
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
from trace_native_callers import method_definitions, INVOKES, invoked_method_indexes
from audit_native_media_implementors import relations
from audit_native_typed_wrapper_coroutines import (
    brief_type, class_field_shapes, method_profile, instructions,
    safe_instruction_shape
)
from audit_native_postfileinfo_lifecycle import merge_reverse, reverse_to_forward
from trace_native_source_hops import inspect_one_dex
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

TARGET_METHODS={
  "Lygv;":{"a","b","f","g","j","l","o","q","r"},
  "Lcq7;":{"D","T","i0"},
  "Lo4y;":{"a","b","c","d"},
  "Llvc;":{"a"},
  "Larv;":{"g"},
  "Lero;":{"<init>"},
  "Lga4;":{"c","<init>"},
  "Ldl8;":{"a","<init>"},
  "Lsu5;":{"invoke","<init>"},
  "Lro7;":{"y0"},
  "Lya4;":{"a","<init>"},
  "Lkc6;":{"a","<init>"},
  "Lzcd;":{"a","<init>"},
}
MODEL_TYPES={
  "Ljgv;","Ldiv;","Lkq7;","Lga4;","Lt6f;","Lnro;","Lwzi;",
  "Lggv;","Lpkv;","Lw010;","Ligv;","Lavt;","Le48;"
}
CLASSES=set(TARGET_METHODS)|MODEL_TYPES
PLAYER_INTERFACES={
  "Landroidx/media3/exoplayer/ExoPlayer;",
  "Landroidx/media3/common/Player;",
  "Landroidx/media3/datasource/DataSource;",
  "Landroidx/media3/exoplayer/source/MediaSource;",
  "Lcom/google/android/exoplayer2/ExoPlayer;",
}
MEDIA_CONCRETES={"Lfxc;","Lro7;","Lwxc;","Lyzt;"}
MAX_TARGET_METHODS=70
MAX_BODIES=500
MAX_STEPS=20000
MAX_MEDIA_DEPTH=4
MAX_OUTPUT=30


def method_hint(triple):
    return bounded_obfuscated(triple)


def hierarchy_verdict(relationships,target,depth=16):
    visited=set()
    frontier=[(target,0)]
    parents=[]
    while frontier:
        cls,n=frontier.pop(0)
        if cls in visited or n>depth:continue
        visited.add(cls)
        if cls!=target and (cls in PLAYER_INTERFACES
                or cls.startswith("Landroidx/media3/")
                or cls.startswith("Lcom/google/android/exoplayer2/")):
            parents.append({"type":brief_type(cls),"steps":n})
        item=relationships.get(cls)
        if item is not None:
            frontier.extend((p,n+1) for p in item[1])
    return {
        "direct_parents":[brief_type(x) for x in relationships.get(target,(0,()))[1]],
        "named_media_ancestry":parents[:12],
        "media_instance_in_actual_player_proven":False,
    }


def bounded_method_media_calls(triple,dex,code_off):
    ins=list(instructions(dex,code_off))
    api_hits=[]
    to_related=[]
    caller_protos=[]
    for _,op,w in ins:
        if op not in INVOKES:continue
        callee=dex.method(w[1])
        if (callee[0] in MEDIA_CONCRETES or callee[0] in PLAYER_INTERFACES
            or callee[0].startswith("Landroidx/media3/datasource/")
            or callee[0].startswith("Landroidx/media3/exoplayer/source/")
            or callee[0] in {
              "Landroid/media/AudioTrack;","Landroid/media/MediaCodec;",
              "Landroid/media/MediaExtractor;", "Landroid/media/MediaPlayer;"
            }):
            api_hits.append(method_hint(callee))
        if callee[0] in CLASSES and callee[0]!=triple[0]:
            to_related.append(method_hint(callee))
        if "Ljgv;" in callee[2] or callee[0]=="Ljgv;":
            caller_protos.append(method_profile(callee))
    # A 721-opcode synthetic lambda multiplexor can reference Lro7.y0
    # in an UNRELATED switch case. A mere callgraph edge is not sound flow.
    focused=triple[0] in {"Lga4;","Ldl8;","Lsu5;","Lro7;","Lero;","Lya4;","Lkc6;","Lzcd;"}
    small=focused and len(ins)<=80
    role_rows=[safe_instruction_shape(dex,op,w) for _,op,w in ins[:80]] if focused else []
    windows=[]
    if focused and not small:
        for i,(_,op,w) in enumerate(ins):
            if op not in INVOKES:continue
            target=dex.method(w[1])
            if target[0] not in {"Lro7;","Le48;","Lfxc;"}:continue
            window=[safe_instruction_shape(dex,hop,words)
                    for _,hop,words in ins[max(0,i-8):i+9]]
            windows.append({"target":bounded_obfuscated(target),
                            "relative_target_index":min(8,i),
                            "bounded_roles":window})
            if len(windows)>=4:break
    return {
        "instructions":len(ins),
        "switch_opcode_count":sum(op in (0x2b,0x2c) for _,op,_ in ins),
        "small_method_opcode_roles":role_rows if small else [],
        "large_method_start_opcode_roles":role_rows[:32] if focused and not small else [],
        "large_method_media_call_windows":windows,
        "same_body_media_calls_may_be_different_switch_arms":len(ins)>80,
        "direct_named_media_call_count":len(api_hits),
        "direct_named_media_calls":sorted(set(api_hits))[:MAX_OUTPUT],
        "related_model_method_invokes":sorted(set(to_related))[:MAX_OUTPUT],
        "exact_jgv_typed_method_invokes":caller_protos[:MAX_OUTPUT],
        "direct_player_source_proven":False,
    }


def static_target_methods(apks):
    relationships={}
    method_data={}
    types={}
    dexes=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for info in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",info.filename):continue
                if info.file_size>DEX_MAX:raise ValueError("DEX_LIMIT")
                d=Dex(z.read(info.filename))
                dexes+=1
                rel=relations(d)
                overlap=set(relationships)&set(rel)
                if overlap:raise ValueError("CROSS_DEX_DUPLICATE_CLASS")
                relationships.update(rel)
                for owner in CLASSES:
                    if owner in rel:
                        types[owner]={
                            "method_type":brief_type(owner),
                            "field_types":class_field_shapes(d,owner)[:80],
                            "declared_flags":rel[owner][0],
                        }
                for mid,coff in method_definitions(d):
                    method=d.method(mid)
                    if method[0] not in TARGET_METHODS:
                        continue
                    if method[1] not in TARGET_METHODS[method[0]]:
                        continue
                    if method in method_data:raise ValueError("DUPLICATE_METHOD")
                    if len(method_data)>MAX_BODIES:raise ValueError("METHOD_LIMIT")
                    method_data[method]=bounded_method_media_calls(method,d,coff)
    if dexes!=6:raise ValueError("PINNED_DEX_COUNT")
    result=[]
    for method,details in sorted(method_data.items()):
        result.append({
            "method":method_profile(method),
            "local":details,
        })
    return {
        "target_class_count":len(types),
        "target_class_shapes":{
            brief_type(owner):{
                **data,"inheritance":hierarchy_verdict(relationships,owner)}
            for owner,data in sorted(types.items())},
        "exact_typed_bridge_method_census":result[:MAX_BODIES],
        "focused_method_count":len(method_data),
        "candidate_media_lineage_proven":False,
    }


def scan_media_proximity(apks, wanted):
    scans=[]
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for info in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",info.filename):continue
                scans.append(inspect_one_dex(z.read(info.filename)))
    if len(scans)!=6:raise ValueError("SIX_DEX_REQUIRED")
    rev=merge_reverse(scans)
    forward=reverse_to_forward(rev)
    seeds={
        m for m in forward if m[0] in TARGET_METHODS
        and m[1] in TARGET_METHODS[m[0]]
    }
    matches=[]
    visited=0
    for seed in sorted(seeds):
        frontier=deque([(seed,0,[seed])])
        seen=set()
        while frontier:
            node,depth,path=frontier.popleft()
            if node in seen:continue
            seen.add(node)
            visited+=1
            if visited>400000:break
            if depth>0 and (node[0] in MEDIA_CONCRETES
                            or node[0] in PLAYER_INTERFACES
                            or node[0].startswith("Landroidx/media3/datasource/")
                            or node[0].startswith("Landroidx/media3/exoplayer/source/")):
                matches.append({
                    "start":method_hint(seed),
                    "hops":depth,
                    "method_hints":[method_hint(m) for m in path[:MAX_MEDIA_DEPTH+1]],
                    "signed_method_call_proximity_only":True,
                })
                break
            if depth<MAX_MEDIA_DEPTH:
                frontier.extend((child,depth+1,path+[child])
                    for child in sorted(forward.get(node,())))
        if len(matches)>=MAX_OUTPUT or visited>400000:break
    return {
        "signed_methods_sourced":len(seeds),
        "method_states_examined":visited,
        "method_search_bounded":visited<=400000,
        "direct_or_indirect_media_method_proximity":matches[:MAX_OUTPUT],
        "decoder_object_source_proven":False,
    }


def scan_signed(apks):
    shape=static_target_methods(apks)
    graph=scan_media_proximity(apks,TARGET_METHODS)
    return {
        "signed_apks":5,"signed_dex":6,
        "method_and_class_shapes":shape,
        "typed_jgv_consumer_callgraph":graph,
        "currently_active_player_identified":False,
        "pre_decoder_source_edition_generation_proven":False,
        "native_replacement_audio_played":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("SIGNED_APK_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-jgv-real-media-shapes-") as temp:
        root=Path(temp)
        archive=root/"unchanged-original.xapk"
        length,digest=exact.gpr.download(archive)
        if length!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_HASH_REQUIRED")
        apks=exact.gpr.split_apks(archive,root)
        if len(apks)!=5:raise ValueError("FIVE_SIGNED_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(apks)
        result=scan_signed(apks)
    return {
        "verdict":"SIGNED_FILEINFO_TO_TYPED_JGV_MEDIA_PROXIMITY_ONLY",
        "publisher_host":"2026.10.3 #170gpr",
        **result,
        "no_binary_or_media_export":True,
        "no_package_modification_or_installation":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (ValueError,RuntimeError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_JGV_MEDIA_PROXIMITY_AUDIT_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "native_replacement_audio_played":False,
        }))
        sys.exit(2)
