#!/usr/bin/env python3
"""Signed source truth gate: find actual *defined* decoder/media entrypoints.

Unlike prior broad name/graph proximity checks, this tests which exact public
Media3/ExoPlayer interfaces and implementations exist as class definitions in
the five genuine publisher-signed #170gpr APK splits. No patch, install, login,
audio, private app metadata, source URLs, keys or account information.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
import audit_gpr_apkpure_once as pinned
from inspect_android_host import Dex, DEX_MAX

ARCHIVE_SHA = "918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84"
ARCHIVE_LENGTH = 60433885

# Exact public SDK types only: no obfuscated/proprietary names in output.
ENTRYPOINTS = {
    "media3_exoplayer_impl": "Landroidx/media3/exoplayer/ExoPlayerImpl;",
    "media3_exoplayer_interface": "Landroidx/media3/exoplayer/ExoPlayer;",
    "media3_simple_exoplayer": "Landroidx/media3/exoplayer/SimpleExoPlayer;",
    "media3_default_media_source_factory": "Landroidx/media3/exoplayer/source/DefaultMediaSourceFactory;",
    "media3_progressive_source_factory": "Landroidx/media3/exoplayer/source/ProgressiveMediaSource$Factory;",
    "media3_progressive_media_source": "Landroidx/media3/exoplayer/source/ProgressiveMediaSource;",
    "media3_default_data_source": "Landroidx/media3/datasource/DefaultDataSource;",
    "media3_media_item": "Landroidx/media3/common/MediaItem;",
    "media3_media_session": "Landroidx/media3/session/MediaSession;",
    "legacy_exoplayer2_impl": "Lcom/google/android/exoplayer2/ExoPlayerImpl;",
    "legacy_exoplayer2_interface": "Lcom/google/android/exoplayer2/ExoPlayer;",
    "legacy_default_media_source_factory": "Lcom/google/android/exoplayer2/source/DefaultMediaSourceFactory;",
    "legacy_default_data_source": "Lcom/google/android/exoplayer2/upstream/DefaultDataSource;",
    "legacy_media_item": "Lcom/google/android/exoplayer2/MediaItem;",
}

# These are the only public SDK method names inventoried.
SOURCES = frozenset({
    "prepare", "setMediaSource", "setMediaSources", "setMediaItem",
    "setMediaItems", "createMediaSource", "createDataSource",
    "getMediaItemAt", "getCurrentMediaItem", "open",
})

PUBLIC_PREFIXES = (
    "Landroidx/media3/",
    "Lcom/google/android/exoplayer2/",
)
PUBLIC_FAMILIES = (
    ("exoplayer", "/exoplayer/"),
    ("datasource", "/datasource/"),
    ("session", "/session/"),
    ("common", "/common/"),
    ("extractor", "/extractor/"),
    ("ui", "/ui/"),
    ("legacy_player", "/exoplayer2/"),
)


def family_for(name: str) -> str:
    if not name.startswith(PUBLIC_PREFIXES):
        return "not_public_sdk"
    for family, needle in PUBLIC_FAMILIES:
        if needle in name:
            return family
    return "public_sdk_other"


def snapshot(dex) -> dict:
    defined = dex.defined_classes()
    public = [name for name in defined if name.startswith(PUBLIC_PREFIXES)]
    defined_roles = Counter(family_for(name) for name in public)

    # Index exact *declared* entrypoint methods, rather than all references.
    candidates = {name: {"class_defined": cls in defined,
                         "declared_methods": []}
                  for name, cls in ENTRYPOINTS.items()}
    inverse = {owner: key for key, owner in ENTRYPOINTS.items()}
    for index in range(dex.method_count):
        owner, name, sig = dex.method(index)
        key = inverse.get(owner)
        if key is not None and owner in defined and name in SOURCES:
            # A method reference in the owning class is not, by itself, proof
            # of an actual declared body. The method table can hold refs too.
            candidates[key]["declared_methods"].append((name, sig))
    for candidate in candidates.values():
        candidate["declared_methods"] = sorted(set(candidate["declared_methods"]))[:40]
        candidate["method_table_refs_not_declarations"] = True
    return {"public_sdk_class_count": len(public),
            "public_sdk_defined_classes_by_family": dict(sorted(defined_roles.items())),
            "entrypoints": candidates}


def combine(rows: list[dict]) -> dict:
    total = Counter()
    hits = {key: {"defined": False, "method_references": set()}
            for key in ENTRYPOINTS}
    for row in rows:
        total.update(row["public_sdk_defined_classes_by_family"])
        for role, candidate in row["entrypoints"].items():
            hits[role]["defined"] |= candidate["class_defined"]
            hits[role]["method_references"].update(map(tuple, candidate["declared_methods"]))
    return {
        "sdk_defined_classes_by_family": dict(sorted(total.items())),
        "exact_public_entrypoints": {
            role: {"class_defined_in_signed_dex": hits[role]["defined"],
                   "method_refs_in_defined_class": sorted(hits[role]["method_references"]),
                   "declared_method_body_confirmed": False}
            for role in ENTRYPOINTS
        },
        "real_decoder_source_association_proven": False,
        "actual_fileinfo_hook_executed": False,
        "source_replacement_proven": False,
    }


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="celikom-signed-engine-inventory-") as tmp:
        root = Path(tmp)
        archive = root / "exact-signed-source.xapk"
        size, sha256 = pinned.download(archive)
        if size != ARCHIVE_LENGTH or sha256 != ARCHIVE_SHA:
            raise ValueError("PINNED_PUBLISHER_ARCHIVE_MISMATCH")
        apks = pinned.split_apks(archive, root)
        pinned.inspect_publisher(apks)
        if len(apks) != 5:
            raise ValueError("PINNED_SIGNED_SPLIT_SET_MISMATCH")
        rows = []
        count = 0
        for apk in apks:
            with zipfile.ZipFile(apk) as z:
                for name in z.namelist():
                    if not re.fullmatch(r"classes[0-9]*\.dex", name):
                        continue
                    info = z.getinfo(name)
                    if info.file_size > DEX_MAX:
                        raise ValueError("DEX_LIMIT")
                    rows.append(snapshot(Dex(z.read(info))))
                    count += 1
        if count != 6:
            raise ValueError("PINNED_DEX_COUNT_MISMATCH")
        return {
            "verdict": "SIGNED_SDK_IMPLEMENTATIONS_INVENTORIED_ONLY",
            "publisher_signed_splits": 5, "dex_files": count,
            **combine(rows),
        }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception:
        print(json.dumps({
            "verdict": "SIGNED_MEDIA_ENGINE_SCAN_UNAVAILABLE",
            "media_or_apk_exposed": False, "source_replacement_proven": False,
        }))
        sys.exit(2)
