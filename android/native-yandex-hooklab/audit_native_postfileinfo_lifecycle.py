#!/usr/bin/env python3
"""Publisher signed DEX: native FileInfo -> coroutine Ldiv handoff consumer census.

Find *use sites* for the observed concrete Ldiv result value, then inspect
whether method callgraph has bounded adjacent/media targets. Unlike a raw name
search, this starts with a register-supported DTO -> coroutine return object.
Still not actual decoder source, polymorphic dispatch, or runtime evidence.
No vendor binary, code, strings, tokens or media exported.
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
from trace_native_source_hops import inspect_one_dex
from audit_native_register_bridge import instructions
from audit_native_typed_wrapper_coroutines import brief_type, field_at, method_profile
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

DTO = "Ldiv;"
SOURCES = {"Lhee;", "Lged;", "Lfqr;"}
MEDIA_OWNERS={
  "Lfxc;", "Lro7;", "Lwxc;", "Lyzt;",
  "Landroidx/media3/exoplayer/ExoPlayer;",
  "Landroid/media/MediaCodec;",
  "Landroid/media/MediaExtractor;",
  "Landroid/media/AudioTrack;",
  "Landroid/media/MediaPlayer;",
}
MAX_CALLERS=30
MAX_METHOD_SEEDS=500
MAX_DEPTH=5
MAX_WALK=120000


def method_label(method):
    return bounded_obfuscated(method)


def merge_reverse(scans):
    reverse=defaultdict(set)
    for x in scans:
        if not x.get("complete"):
            raise ValueError("INCOMPLETE_DEX")
        for target,callers in x["_reverse_edges"].items():
            reverse[target].update(callers)
    return reverse


def reverse_to_forward(reverse):
    forward=defaultdict(set)
    for callee,callers in reverse.items():
        for caller in callers:
            forward[caller].add(callee)
    return forward


def bounded_path_to_media(forward,seeds,depth=MAX_DEPTH,cap=MAX_WALK):
    """Call adjacency only; method calls are NOT value flow or active player."""
    if not 0<=depth<=6 or not 0<=len(seeds)<=MAX_METHOD_SEEDS:
        raise ValueError("SEARCH_LIMIT")
    queue=deque((m,0,(m,)) for m in sorted(seeds))
    visited=set()
    matched=[]
    while queue:
        method,hops,path=queue.popleft()
        if method in visited:continue
        visited.add(method)
        if len(visited)>cap:
            return {"search_truncated":True, "visited":len(visited),
                    "first_media_proximity_paths":matched[:12],
                    "decoder_proven":False}
        if hops and (method[0] in MEDIA_OWNERS
                     or method[0].startswith("Landroidx/media3/datasource/")):
            matched.append({
                "hop_count":hops,
                "hints":[method_label(item) for item in path[:7]],
                "register_source_flow_proven":False,
            })
            if len(matched)>=12:break
        if hops>=depth:continue
        for next_method in sorted(forward.get(method,())):
            if next_method not in visited:
                queue.append((next_method,hops+1,path+(next_method,)))
    return {
        "search_truncated":False, "visited":len(visited),
        "first_media_proximity_paths":matched[:12],
        "decoder_proven":False,
    }


def typed_anchors(apks):
    """Only model-typed method and field references; no full class/source export."""
    protos=set()
    field_owners=Counter()
    field_types=Counter()
    defined=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",item.filename):
                    continue
                d=Dex(z.read(item))
                for i in range(d.method_count):
                    triple=d.method(i)
                    if DTO in triple[2] or triple[0]==DTO:
                        protos.add(triple)
                count,_=d.table(80,8)
                for i in range(count):
                    owner,typ=field_at(d,i)
                    if typ==DTO:
                        field_owners[owner]+=1
                    if owner==DTO:
                        field_types[brief_type(typ)]+=1
                defined+=1
    if defined!=6:
        raise ValueError("WRONG_SIGNED_DEX_COUNT")
    return {
        "exact_dto_method_refs_count":len(protos),
        "exact_dto_method_refs_examples":[method_profile(x)
             for x in sorted(protos)[:MAX_CALLERS]],
        "typed_l_div_field_owner_count":len(field_owners),
        "typed_l_div_field_owner_examples":[{
            "owner":brief_type(x),"fields":n}
            for x,n in sorted(field_owners.items(),key=lambda x:(-x[1],x[0]))[:MAX_CALLERS]],
        "dto_field_type_counts":dict(sorted(field_types.items())),
        "_dto_protos":protos,
    }


def consumer_summary(reverse):
    dto_callees={m for m in reverse if m[0]==DTO}
    detail=[]
    callers=set()
    for m in sorted(dto_callees):
        local=reverse[m]
        callers.update(local)
        detail.append({
            "method":method_profile(m),
            "direct_caller_count":len(local),
            "caller_hints":[method_label(c) for c in sorted(local)[:MAX_CALLERS]],
        })
    return {
        "dto_method_targets_invoked":len(dto_callees),
        "direct_dto_consumer_method_count":len(callers),
        "per_dto_method_callers":detail[:MAX_CALLERS],
        "direct_consumer_examples":[method_label(x) for x in sorted(callers)[:MAX_CALLERS]],
        "_consumer_methods":callers,
    }


def downstream_consumer_telemetry(reverse,typed):
    info=consumer_summary(reverse)
    consumer=info.pop("_consumer_methods")
    forward=reverse_to_forward(reverse)
    # Different source sets, to avoid 'no path' from arbitrarily selecting just
    # the earliest 30 consumers or over-claiming that any caller is active audio.
    paired=bounded_path_to_media(forward,consumer,MAX_DEPTH)
    actual={
        "consumer_methods_are_register_bound_to_coroutine_l_div":False,
        "direct_consumer_methods":len(consumer),
        "distinct_consumer_owners":len({m[0] for m in consumer}),
        "consumer_owner_examples":[brief_type(x) for x in
                sorted({m[0] for m in consumer})[:MAX_CALLERS]],
        "bounded_consumer_to_media_callgraph_proximity":paired,
    }
    # No reverse relation inference: immediate Ldiv method consumers might be
    # unrelated renderers/debug adapters; nothing licenses a hook.
    return info,actual


def scan_signed(apks):
    scans=[]
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if re.fullmatch(r"classes[0-9]*\.dex",item.filename):
                    if item.file_size>DEX_MAX:raise ValueError("DEX_TOO_LARGE")
                    scans.append(inspect_one_dex(z.read(item.filename)))
    if len(scans)!=6:
        raise ValueError("SIGNED_DEX_COUNT")
    reverse=merge_reverse(scans)
    typed=typed_anchors(apks)
    consumers,proximity=downstream_consumer_telemetry(reverse,typed)
    typed.pop("_dto_protos")
    return {
        "joined_signed_dex_count":len(scans),
        "joined_defined_method_bodies":sum(x["defined_method_bodies"] for x in scans),
        "joined_invoke_edges":sum(x["invoke_edges"] for x in scans),
        "structural_l_div_type_references":typed,
        "direct_l_div_method_consumers":consumers,
        "downstream_caller_proximity":proximity,
        "coroutine_result_object_to_decoder_binding_proven":False,
        "exact_current_track_edition_generation_proven":False,
        "audio_substitution_in_android_runtime_proven":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-native-signed-l-div-consumers-") as td:
        folder=Path(td)
        original=folder/"publisher-unchanged.xapk"
        length,sha=exact.gpr.download(original)
        if length!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_ORIGINAL_SHA_MISMATCH")
        splits=exact.gpr.split_apks(original,folder)
        if len(splits)!=5:raise ValueError("SIGNED_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(splits)
        report=scan_signed(splits)
    return {
        "verdict":"SIGNED_NATIVE_POST_FILEINFO_DATA_MODEL_CONSUMER_AUDIT_ONLY",
        "host_version":"2026.10.3 #170gpr",
        **report,
        "no_original_apk_patch_or_publish":True,
        "no_media_secrets_or_user_accounts_accessed":True,
        "original_playback_unaffected":True,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,sort_keys=True))
    except (ValueError,RuntimeError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict":"SIGNED_POST_FILEINFO_CONSUMER_AUDIT_INCOMPLETE",
            "error_class_only":type(exc).__name__,
            "audio_substitution_in_android_runtime_proven":False,
        }))
        sys.exit(2)
