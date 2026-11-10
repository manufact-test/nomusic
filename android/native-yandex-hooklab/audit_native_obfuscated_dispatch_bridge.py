#!/usr/bin/env python3
"""Publisher-verified READ ONLY virtual/interface-dispatch proximity for FileInfo.

The concrete signed sequence ends at internal source-model factories producing
Lkq7/Lga4/Lnro; this scan tests *possible* virtual dispatch via their actual
super-types. It never treats graph reachability as playback data flow.
No binary extraction into repository, hook, DRM bypass, install or audio.
"""
from __future__ import annotations

from collections import defaultdict,deque
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
from trace_native_callers import method_definitions
from trace_native_source_hops import inspect_one_dex
from audit_native_media_implementors import relations,transitive_implementors
from audit_native_postfileinfo_lifecycle import merge_reverse,reverse_to_forward
from audit_native_jgv_media_candidates import MEDIA_CONCRETES,PLAYER_INTERFACES
from trace_native_model_to_decoder import bounded_obfuscated
from audit_native_typed_wrapper_coroutines import method_profile
import clone_native_splits_ephemeral as exact

ROOTS=("Le48;","Le93;","Lmir;")
SOURCE_METHODS={
 ("Lcq7;","D"),("Lcq7;","T"),("Lcq7;","i0"),
 ("Lo4y;","a"),("Lo4y;","b"),("Lo4y;","c"),("Lo4y;","d"),
 ("Llvc;","a"),("Lygv;","r"),("Larv;","g")
}
MAX_SUBTYPES=500
MAX_DYNAMIC_EDGES=30000
MAX_PATH_DEPTH=7
MAX_VISITED=160000
MAX_HITS=14


def type_subclasses(rel,root):
    """Only hierarchy connectivity, not runtime instances or active selection."""
    members=transitive_implementors(rel,root)
    if len(members)>MAX_SUBTYPES:
        raise ValueError("TOO_MANY_SUBTYPES")
    return members


def method_definitions_by_owner(apks,owners):
    definitions=defaultdict(set)
    dexes=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for info in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",info.filename):continue
                if info.file_size>DEX_MAX:raise ValueError("DEX_LIMIT")
                d=Dex(z.read(info.filename))
                dexes+=1
                for mid,off in method_definitions(d):
                    triple=d.method(mid)
                    if triple[0] in owners:
                        definitions[triple[0]].add(triple)
    if dexes!=6:raise ValueError("SIX_SIGNED_DEX_REQUIRED")
    return definitions


def possible_virtual_overrides(reverse,rel,defs,roots=ROOTS):
    """Map root method ref to exact named-override bodies on signed descendants.

    Interface invoke may dispatch into any implementing type; impossible to
    select runtime receiver without actual instance dataflow. Report each edge
    as POSSIBLE, and never over-interpret.
    """
    edges=defaultdict(set)
    summary={}
    for root in roots:
        subclasses=type_subclasses(rel,root)
        root_refs=[m for m in reverse if m[0]==root]
        total=0
        for method in root_refs:
            for owner in subclasses:
                for matching in defs.get(owner,()):
                    if matching[1:]==method[1:]:
                        edges[method].add(matching)
                        total+=1
                        if total>MAX_DYNAMIC_EDGES:
                            raise ValueError("DISPATCH_EDGE_BUDGET")
        summary[root]={
            "concrete_descendant_class_count":len(subclasses),
            "virtual_root_method_refs":len(root_refs),
            "candidate_dispatch_edges":total,
            "descendant_class_hints":[c for c in subclasses[:16] if
                re.fullmatch(r"L[A-Za-z0-9_$]{1,16};",c)],
            "actual_receiver_bound":False,
        }
    return edges,summary


def media_destination(m):
    return (m[0] in MEDIA_CONCRETES or m[0] in PLAYER_INTERFACES
      or m[0].startswith("Landroidx/media3/exoplayer/source/")
      or m[0].startswith("Landroidx/media3/datasource/")
      or m[0] in {"Landroid/media/MediaCodec;","Landroid/media/AudioTrack;",
                   "Landroid/media/MediaExtractor;","Landroid/media/MediaPlayer;"})


def reachable_media(forward,virtual,seeds):
    """Shortest bounded method-invoke path including possible override edges."""
    results=[]
    per_seed=[]
    for seed in sorted(seeds):
        q=deque([(seed,0,(seed,),False)])
        seen=set()
        count=0
        witness=None
        truncated=False
        while q:
            node,depth,path,uses_dynamic=q.popleft()
            key=(node,uses_dynamic)
            if key in seen:continue
            seen.add(key)
            count+=1
            if count>MAX_VISITED:
                truncated=True
                break
            if depth>0 and media_destination(node):
                edges=[]
                for before,after in zip(path,path[1:]):
                    options=virtual.get(before,set())
                    dynamic=after in options
                    edges.append({
                        "kind":"possible_virtual_dispatch" if dynamic else "static_invoke_adjacency",
                        "dispatch_candidate_count":len(options) if dynamic else 0,
                        "dynamic_receiver_selected_in_live_player":False,
                    })
                witness={
                    "seed":bounded_obfuscated(seed),
                    "hops":depth,
                    "possible_virtual_dispatch_used":uses_dynamic,
                    "method_hints":[bounded_obfuscated(x) for x in path],
                    "signed_method_prototypes":[method_profile(x) for x in path],
                    "edge_qualification":edges,
                    "audio_source_identity_or_decoder_proven":False,
                }
                break
            if depth>=MAX_PATH_DEPTH:continue
            for callee in forward.get(node,()):
                q.append((callee,depth+1,path+(callee,),uses_dynamic))
            for dest in virtual.get(node,()):
                q.append((dest,depth+1,path+(dest,),True))
        per_seed.append({
            "method":bounded_obfuscated(seed),
            "bounded_states":count,
            "truncated":truncated,
            "nearest_media_path_discovered":witness is not None
        })
        if witness and len(results)<MAX_HITS:results.append(witness)
    return {
        "seed_count":len(seeds),
        "per_seed":per_seed[:40],
        "media_paths":results[:MAX_HITS],
        "no_path_does_not_rule_out_async_runtime":True,
        "current_decoder_source_proven":False,
    }



def exact_path_constructor_census(reverse):
    """Static caller evidence for Le48 candidate receiver creation only.

    Method appearance is not concrete object flow; different overloaded
    constructors or async injection can create distinct instances.
    """
    owners={"Lga4;","Ldl8;","Lsu5;","Lero;","Lro7;"}
    methods=set()
    result={}
    for m in sorted(reverse):
        if m[0] not in owners or m[1] not in ("<init>","a","c","invoke","y0"):
            continue
        methods.add(m)
        result.setdefault(m[0],[]).append({
            "callee":method_profile(m),
            "direct_caller_count":len(reverse[m]),
            "callers":[bounded_obfuscated(c) for c in sorted(reverse[m])[:18]],
            "receiver_instance_proven":False,
        })
    return {
        "observed_path_method_targets":len(methods),
        "per_owner":{owner:rows[:24] for owner,rows in sorted(result.items())},
        "fileinfo_to_callback_instance_binding_proven":False,
    }


def signed_scan(apks):
    scans=[]
    relationships={}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for info in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",info.filename):continue
                if info.file_size>DEX_MAX:raise ValueError("DEX_SIZE_LIMIT")
                raw=z.read(info.filename)
                d=Dex(raw)
                rel=relations(d)
                if set(rel)&set(relationships):
                    raise ValueError("CROSS_DEX_CLASS_DUPLICATE")
                relationships.update(rel)
                scans.append(inspect_one_dex(raw))
    if len(scans)!=6 or any(not x["complete"] for x in scans):
        raise ValueError("SIGNED_SCAN_INCOMPLETE")
    reverse=merge_reverse(scans)
    forward=reverse_to_forward(reverse)
    subclass_owners=set(ROOTS)
    for root in ROOTS:
        subclass_owners.update(type_subclasses(relationships,root))
    definitions=method_definitions_by_owner(apks,subclass_owners)
    virtual,classes=possible_virtual_overrides(reverse,relationships,definitions)
    seeds={m for m in forward if (m[0],m[1]) in SOURCE_METHODS}
    if not seeds:raise ValueError("EXPECTED_REAL_FACTORY_SEEDS_MISSING")
    return {
        "signed_apk_count":5,"signed_dex_count":6,
        "defined_method_bodies":sum(x["defined_method_bodies"] for x in scans),
        "invoke_call_edges":sum(x["invoke_edges"] for x in scans),
        "obfuscated_root_class_hierarchy_dispatch":classes,
        "candidate_virtual_edges":sum(len(x) for x in virtual.values()),
        "exact_candidate_receiver_constructor_census":exact_path_constructor_census(reverse),
        "bounded_callgraph_with_possible_dispatch":reachable_media(
            forward,virtual,seeds),
        "virtual_edges_are_over_approximation":True,
        "fileinfo_l_div_l_jgv_current_audio_decoder_connected":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("SIGNED_ONLY_CI")
    with tempfile.TemporaryDirectory(prefix="celikom-signed-virtual-callback-") as td:
        directory=Path(td)
        original=directory/"original-unchanged.xapk"
        length,sha=exact.gpr.download(original)
        if length!=60433885 or sha!=exact.ARCHIVE_SHA:
            raise ValueError("HASH_VERIFICATION_FAILED")
        apks=exact.gpr.split_apks(original,directory)
        if len(apks)!=5:raise ValueError("EXPECTED_FIVE_ORIGINAL_SPLITS")
        exact.gpr.inspect_publisher(apks)
        results=signed_scan(apks)
    return {
        "verdict":"SIGNED_NATIVE_OBFUSCATED_POSSIBLE_DISPATCH_GRAPH_ONLY",
        "host":"2026.10.3 #170gpr",
        **results,
        "no_vendor_apk_export_or_install":True,
        "no_media_or_account_access":True,
        "actual_audio_substitution_proven":False,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (ValueError,RuntimeError,DexError,OSError,zipfile.BadZipFile) as ex:
        print(json.dumps({
            "verdict":"SIGNED_VIRTUAL_DISPATCH_SCAN_INCOMPLETE",
            "error_class_only":type(ex).__name__,
            "actual_audio_substitution_proven":False,
        }))
        sys.exit(2)
