#!/usr/bin/env python3
"""Read-only six-DEX SHARED-CALLER proximity to native media implementation.

The previous trace searches only downstream from FileInfo conversion callers.
An actual player orchestrator can invoke FileInfo and the player as independent
siblings; this search finds their *common callers* instead. This is NOT
register-value flow, not playback identity, not permission to patch Yandex.

Never emit raw APK/DEX, signed URLs, tokens, media, strings or user data.
Only the exact publisher-verified native Yandex #170gpr XAPK is accepted.
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
from inspect_android_host import DexError, DEX_MAX
from trace_native_source_hops import inspect_one_dex
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

SUPPORTED_MEDIA_OWNERS = {
    # Exact named ExoPlayer interface and four concrete implementors from
    # publisher-verified native classes; does NOT establish active audio.
    "Landroidx/media3/exoplayer/ExoPlayer;",
    "Lfxc;", "Lro7;", "Lwxc;", "Lyzt;",
}
PLATFORM_MEDIA = {
    "Landroid/media/MediaCodec;",
    "Landroid/media/MediaExtractor;",
    "Landroid/media/MediaPlayer;",
    "Landroid/media/AudioTrack;",
}
MAX_DEPTH = 4
MAX_GRAPH_NODES = 250_000
MAX_HINTS = 12


def upstream_depths(reverse: dict, seeds: set, depth: int = MAX_DEPTH,
                    cap: int = MAX_GRAPH_NODES) -> dict:
    """Breadth first caller graph, capturing shortest distances only.

    This is only call adjacency. No code values are inspected or inferred.
    """
    if depth < 0 or depth > 6 or len(seeds) > cap:
        raise ValueError("BOUND_EXCEEDED")
    found = {seed: 0 for seed in seeds}
    frontier = set(seeds)
    for n in range(1, depth + 1):
        upcoming = set()
        for method in frontier:
            for caller in reverse.get(method, ()):
                if caller not in found:
                    if len(found) >= cap:
                        raise ValueError("CALL_GRAPH_SEARCH_LIMIT")
                    found[caller] = n
                    upcoming.add(caller)
        frontier = upcoming
        if not frontier:
            break
    return found


def shared_caller_proximity(reverse: dict, source: set, sinks: set,
                            depth: int = MAX_DEPTH) -> dict:
    """Nearest common CALLER of source path and media call path.

    A common caller can be an application start or unrelated supervisor.
    Even distance 1+1 does NOT imply returned audio goes to a decoder.
    """
    sources = upstream_depths(reverse, source, depth)
    media = upstream_depths(reverse, sinks, depth)
    common = sources.keys() & media.keys()
    ordered = sorted(common, key=lambda x: (sources[x] + media[x],
                                             max(sources[x], media[x]), x))
    return {
        "source_seed_methods": len(source),
        "media_sink_methods": len(sinks),
        "source_ancestors": len(sources),
        "media_ancestors": len(media),
        "shared_callers_within_bounded_depth": len(common),
        "lowest_sum_of_call_distances": (
            sources[ordered[0]] + media[ordered[0]] if ordered else None),
        "first_bounded_hints": [
            {
                "caller": bounded_obfuscated(method),
                "fileinfo_call_depth": sources[method],
                "media_call_depth": media[method],
                "current_audio_source_or_decoder_proven": False,
            } for method in ordered[:MAX_HINTS]
        ],
        "interpretation": "INVOKE_PROXIMITY_ONLY_NO_REGISTER_VALUE_FLOW",
    }


def sink_family(method: tuple) -> str | None:
    owner, name, signature = method
    if owner in SUPPORTED_MEDIA_OWNERS:
        return "media3_interface_or_obfuscated_implementor"
    if owner in PLATFORM_MEDIA:
        return "android_framework_media"
    return None



def media_session_api_family(method: tuple) -> str | None:
    """Exact public Android framework method names used by our observer.

    Do not infer that Media3 or Compat inevitably calls platform methods.
    Both can use reflection, adapters, AIDL, and different player sessions.
    """
    owner, name, signature = method
    if (owner == "Landroid/media/session/MediaSession;"
            and (name == "setMetadata" and
                 signature == "(Landroid/media/MediaMetadata;)V" or
                 name == "setPlaybackState" and
                 signature == "(Landroid/media/session/PlaybackState;)V")):
        return "exact_android_framework_observer_methods"
    if owner in {
        "Landroid/support/v4/media/session/MediaSessionCompat;",
        "Landroidx/media/session/MediaSessionCompat;"
    } and name in ("setMetadata", "setPlaybackState"):
        return "media_session_compat_methods"
    if owner == "Landroidx/media3/session/MediaSession;" and name in (
            "setPlayer", "setSessionActivity", "setExtras"):
        return "media3_public_session_methods"
    return None


def media_session_callsite_census(reverse: dict) -> dict:
    """Count method *callers*, not runtime state changes or actual invocations."""
    groups = {
        "exact_android_framework_observer_methods": {},
        "media_session_compat_methods": {},
        "media3_public_session_methods": {},
    }
    for callee, callers in reverse.items():
        group = media_session_api_family(callee)
        if group is None:
            continue
        # Never print original APK string values, code or named private classes.
        label = callee[1]
        entry = groups[group].setdefault(label, {"distinct_caller_methods": set()})
        entry["distinct_caller_methods"].update(callers)

    out = {}
    for group, methods in groups.items():
        out[group] = {
            "observed_static_invoke_target_names": sorted(methods),
            "unique_direct_caller_methods": len(set().union(
                *(value["distinct_caller_methods"] for value in methods.values()))),
            "per_method": {
                method: {
                    "unique_caller_methods": len(item["distinct_caller_methods"]),
                    "bounded_caller_hints": [
                        bounded_obfuscated(x)
                        for x in sorted(item["distinct_caller_methods"])[:6]
                    ],
                } for method, item in sorted(methods.items())
            },
            "runtime_media_session_callback_proven": False,
        }
    return out


def joined_graph_findings(items: list[dict]) -> dict:
    """Join exact *method triples* across all verified DEX, not local IDs."""
    reverse = defaultdict(set)
    source = set()
    model = set()
    scanned = 0
    edges = 0
    for item in items:
        if not item.get("complete"):
            raise ValueError("INCOMPLETE_DEX_SCAN")
        source.update(item["_source_methods"]["converter_caller"])
        model.update(item["_source_methods"]["model_consumer"])
        scanned += item["defined_method_bodies"]
        edges += item["invoke_edges"]
        if edges > 2_000_000 or scanned > 400_000:
            raise ValueError("SIGNED_GRAPH_TOO_LARGE")
        for callee, callers in item["_reverse_edges"].items():
            reverse[callee].update(callers)
    called_methods = set(reverse)
    for callers in reverse.values():
        called_methods.update(callers)
    families = defaultdict(set)
    for method in called_methods:
        group = sink_family(method)
        if group:
            families[group].add(method)
    report = {}
    for group in ("media3_interface_or_obfuscated_implementor",
                  "android_framework_media"):
        sinks = families[group]
        report[group] = {
            "converter_callers": shared_caller_proximity(reverse, source, sinks),
            "model_consumers": shared_caller_proximity(reverse, model, sinks),
        }
    return {
        "dex_body_count": scanned,
        "dex_invoke_edge_count": edges,
        "method_triples_joined_across_six_dex": True,
        "source_kind": "signed FileInfo converter callers, exact native DTO model",
        # Minimal identifiers only: guide the next audit to the actual signed
        # converter callsite, not just a class name guessed from R8 symbols.
        "direct_converter_caller_hints": [
            bounded_obfuscated(x) for x in sorted(source)[:8]],
        "direct_model_consumer_hints": [
            bounded_obfuscated(x) for x in sorted(model)[:12]],
        "converter_caller_count": len(source),
        "model_consumer_count": len(model),
        "source_callsite_audio_flow_proven": False,
        "sink_kinds": {
            "media3_implementor_symbols": 4,
            "media3_public_interface": True,
            "android_framework_media_classes": len(PLATFORM_MEDIA),
        },
        "method_proximity": report,
        "platform_media_session_hook_static_callsite_census":
            media_session_callsite_census(reverse),
        "real_player_selected": False,
        "real_decoder_proven": False,
        "trackid_edition_generation_bound_to_source": False,
        "replacement_audio_played_in_native_android": False,
        "warning": "A common caller can prefetch independent sources or merely manage UI. NEVER use the output as an audio hook.",
    }


def run() -> dict:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("CI_ONLY_SIGNED_APK")
    with tempfile.TemporaryDirectory(prefix="celikom-exact-signed-native-call-proximity-") as tmp:
        root = Path(tmp)
        original = root / "unchanged-publisher.xapk"
        length, digest = exact.gpr.download(original)
        if length != 60433885 or digest != exact.ARCHIVE_SHA:
            raise ValueError("PINNED_XAPK_SHA256_MISMATCH")
        apks = exact.gpr.split_apks(original, root)
        if len(apks) != 5:
            raise ValueError("PINNED_SPLIT_COUNT_MISMATCH")
        exact.gpr.inspect_publisher(apks)
        scanned = []
        for apk in apks:
            with zipfile.ZipFile(apk) as z:
                for entry in z.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                        continue
                    if entry.file_size > DEX_MAX:
                        raise ValueError("DEX_TOO_LARGE")
                    scanned.append(inspect_one_dex(z.read(entry)))
        if len(scanned) != 6:
            raise ValueError("PINNED_DEX_COUNT_MISMATCH")
        # TemporaryDirectory closes before any CLI output.
        report = joined_graph_findings(scanned)
    return {
        "verdict": "SIGNED_NATIVE_FILEINFO_MEDIA_SHARED_CALLER_PROXIMITY_ONLY",
        "publisher_original": "Yandex Music 2026.10.3 #170gpr",
        "publisher_apks": 5,
        "publisher_dex": 6,
        **report,
        "no_app_installation_or_patch": True,
        "no_credentials_or_media_read": True,
        "no_vendor_apk_export": True,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except (ValueError, RuntimeError, DexError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict": "STATIC_GRAPH_AUDIT_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "patched_apk_created": False,
        }))
        sys.exit(2)
