#!/usr/bin/env python3
"""Publisher-verified READ-ONLY shallow invoke-chain evidence, not runtime proof.

Scans ONLY unchanged original signed #170gpr DEX, on disposable CI.
A DEX invoke path does not prove a value flows into Media3's decoder.
Never outputs APK, media, credentials, URL, raw log, string constant, or DEX.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
import clone_native_splits_ephemeral as exact
from inspect_android_host import Dex, DexError, DEX_MAX
from trace_native_callers import method_definitions, invoked_method_indexes
from trace_native_model_to_decoder import is_media_call, bounded_obfuscated

CONVERTER = "Lsw7;"
MODEL = "Leed;"
MAX_DEFINED = 350000
MAX_EDGES = 1800000
MAX_HOPS = 3
MAX_WITNESSES = 12


def media_namespace_family(method):
    """Classify PUBLIC SDK class namespaces only; do not infer decoder ownership."""
    owner, name, signature = method
    if owner.startswith("Landroidx/media3/"):
        return "androidx_media3"
    if owner.startswith("Lcom/google/android/exoplayer2/"):
        return "legacy_exoplayer2"
    if owner == "Landroid/media/MediaCodec;":
        return "platform_media_codec"
    if owner == "Landroid/media/AudioTrack;":
        return "platform_audio_track"
    if owner == "Landroid/media/MediaExtractor;":
        return "platform_media_extractor"
    if owner == "Landroid/media/MediaPlayer;":
        return "platform_media_player"
    if owner == "Lged;":
        return "named_obfuscated_bridge_ged"
    return None


def call_graph_hops(reverse, source_methods, media_methods, max_hops=MAX_HOPS):
    """Traverse from a Media3 call backwards, never infer data movement."""
    if not 1 <= max_hops <= MAX_HOPS:
        raise ValueError("HOP_LIMIT")
    shortest = {method: 0 for method in media_methods}
    next_step = {}
    frontier = set(media_methods)
    for depth in range(1, max_hops + 1):
        upcoming = set()
        for callee in sorted(frontier):
            for caller in sorted(reverse.get(callee, ())):
                if caller not in shortest:
                    shortest[caller] = depth
                    next_step[caller] = callee
                    upcoming.add(caller)
        frontier = upcoming
        if not frontier:
            break
    paths = []
    for method in sorted(source_methods):
        if method not in shortest:
            continue
        chain = [method]
        while chain[-1] in next_step:
            chain.append(next_step[chain[-1]])
        if len(chain) >= 2 and chain[-1] in media_methods:
            paths.append(chain)
    paths.sort(key=lambda x: (len(x), x))
    return paths


def inspect_one_dex(data):
    dex = Dex(data)
    reverse = defaultdict(set)
    sources = {"converter_caller": set(), "model_consumer": set()}
    media_methods = set()
    # Method refs, not classes: a 0 in media3 indicates no un-obfuscated
    # symbols, NOT evidence that no media engine exists in the APK.
    media_family_refs = defaultdict(set)
    for method_index in range(dex.method_count):
        triple = dex.method(method_index)
        family = media_namespace_family(triple)
        if family is not None:
            media_family_refs[family].add(triple)
    defined_classes = dex.defined_classes()
    media_family_defined = defaultdict(int)
    for owner in defined_classes:
        family = media_namespace_family((owner, "", ""))
        if family is not None:
            media_family_defined[family] += 1
    scanned = 0
    edges = 0
    unsupported_bodies = 0
    for idx, code_off in method_definitions(dex):
        scanned += 1
        if scanned > MAX_DEFINED:
            raise ValueError("DEFINED_METHODS_LIMIT")
        owner, name, signature = caller = dex.method(idx)
        if owner == MODEL or MODEL in signature:
            sources["model_consumer"].add(caller)
        try:
            called = {dex.method(midx)
                      for midx, _, _ in invoked_method_indexes(dex, code_off)}
        except DexError:
            unsupported_bodies += 1
            continue
        edges += len(called)
        if edges > MAX_EDGES:
            raise ValueError("INVOKE_EDGE_LIMIT")
        if any(m[0] == CONVERTER and m[1] in ("y0", "z0") for m in called):
            sources["converter_caller"].add(caller)
        if any(m[0] == MODEL or MODEL in m[2] for m in called):
            sources["model_consumer"].add(caller)
        for callee in called:
            reverse[callee].add(caller)
            if is_media_call(callee):
                media_methods.add(callee)
        if is_media_call(caller):
            media_methods.add(caller)
    if unsupported_bodies:
        return {
            "complete": False, "unsupported_method_bodies": unsupported_bodies,
            "defined_method_bodies": scanned, "invoke_edges": edges,
        }
    results = {}
    for kind, seeds in sources.items():
        chains = call_graph_hops(reverse, seeds, media_methods)
        results[kind] = {
            "seed_method_count": len(seeds),
            "media3_invoke_chain_count_up_to_3": len(chains),
            "by_call_depth": {str(n): sum(len(c) - 1 == n for c in chains)
                              for n in range(1, MAX_HOPS + 1)},
            "bounded_method_hints": [
                {
                    "hop_count": len(path) - 1,
                    "method_classes": [bounded_obfuscated(item) for item in path],
                    "dataflow_proven": False,
                } for path in chains[:MAX_WITNESSES]
            ],
        }
    return {
        "complete": True, "unsupported_method_bodies": 0,
        "defined_method_bodies": scanned, "invoke_edges": edges,
        "media3_source_methods_referenced": len(media_methods),
        "media_family_method_refs": dict(sorted(
            (key, len(value)) for key, value in media_family_refs.items())),
        "media_family_defined_classes": dict(sorted(media_family_defined.items())),
        "namespace_limit": "A missing named API is not proof no player/decoder exists.",
        "search": results,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("CI_ONLY_SIGNED_STATIC_SCAN")
    with tempfile.TemporaryDirectory(prefix="celikom-pinned-source-hops-") as temp:
        root = Path(temp)
        original = root / "pinned.xapk"
        size, digest = exact.gpr.download(original)
        if size != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("PINNED_ARCHIVE_DRIFT")
        splits = exact.gpr.split_apks(original, root)
        if len(splits) != 5:
            raise ValueError("EXPECTED_FIVE_SPLITS")
        exact.gpr.inspect_publisher(splits)
        observed = []
        for apk in splits:
            with zipfile.ZipFile(apk) as z:
                for entry in z.infolist():
                    if not re.fullmatch(r"classes\d*\.dex", entry.filename):
                        continue
                    if entry.file_size > DEX_MAX:
                        raise ValueError("DEX_TOO_LARGE")
                    observed.append(inspect_one_dex(z.read(entry)))
        if len(observed) != 6 or any(not d["complete"] for d in observed):
            raise ValueError("SIGNED_DEX_SCAN_NOT_COMPLETE")
        return {
            "verdict": "STATIC_INVOKE_CHAIN_ONLY_NO_PLAYBACK_PROOF",
            "signed_original_split_count": 5,
            "dex_count": 6,
            "all_code_bodies_scanned": True,
            "scan_counts": {
                "defined_bodies": sum(d["defined_method_bodies"] for d in observed),
                "invoke_edges": sum(d["invoke_edges"] for d in observed),
                "media3_source_method_refs": sum(d["media3_source_methods_referenced"]
                                                 for d in observed),
            },
            "public_player_namespace_census": {
                family: {
                    "method_refs": sum(d["media_family_method_refs"].get(family, 0)
                                       for d in observed),
                    "defined_classes": sum(d["media_family_defined_classes"].get(family, 0)
                                           for d in observed)
                } for family in (
                    "androidx_media3", "legacy_exoplayer2", "platform_media_codec",
                    "platform_audio_track", "platform_media_extractor",
                    "platform_media_player", "named_obfuscated_bridge_ged")
            },
            "by_dex": [
                {"ordinal": i + 1, "search": item["search"]}
                for i, item in enumerate(observed)
            ],
            "warning": "Invoke adjacency cannot prove same register, catalog edition, data flow, MediaSource prepare or playable audio.",
            "source_or_apk_modified": False,
            "user_account_access": False,
            "media_stream_access": False,
            "third_party_apk_or_trace_published": False,
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except (ValueError, DexError, RuntimeError, OSError, zipfile.BadZipFile) as ex:
        print(json.dumps({
            "verdict": "STATIC_SOURCE_HOPS_BLOCKED",
            "error_type": type(ex).__name__,
            "vendor_apk_published": False,
        }))
        sys.exit(2)
