#!/usr/bin/env python3
"""Bounded signed-2025 track-ID API provenance probe. Read only.

Locate publisher-annotated trackId request parameters (not a guessed Track field)
and count same-method original Track-typed origins. Does NOT equate a caller's
Track to the current SLOT_B or prove edition/queue generation. No values,
private field names, user data, URLs or signed binaries exported.
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
from trace_native_callers import uleb
from trace_playaudio_boundary import _encoded_value

audit = trusted.audit
TRACK = "Lru/yandex/music/data/audio/o;"
ALBUM = "Lru/yandex/music/data/audio/Album;"
APIS = {
    "Lcom/yandex/music/shared/player/content/remote/fileinfo/FileInfoApi;": "FILE_INFO",
    "Lcom/yandex/music/shared/player/content/remote/fileinfo/OldFileInfoApi;": "OLD_FILE_INFO",
    "Lcom/yandex/music/shared/player/content/remote/downloadinfo/DownloadInfoApi;": "DOWNLOAD_INFO",
}
LABELS = {"trackId", "track_id", "track-id", "realId", "albumId", "editionId"}
MAX_ANNOTATIONS = 32
MAX_PAIRS = 32
MAX_PARAMS = 64

def api_parameter_labels(dex, class_index):
    """Only already-whitelisted identity parameter annotation values."""
    base = dex.class_offset + class_index * 32
    directory = dex.u32(base + 20)
    result = {}
    if not directory:
        return result
    nfields = dex.u32(directory + 4)
    nmethods = dex.u32(directory + 8)
    nparams = dex.u32(directory + 12)
    if max(nfields, nmethods, nparams) > 800:
        raise ValueError("SOURCE_API_ANNOTATION_DIRECTORY_LIMIT")
    at = directory + 16 + (nfields + nmethods) * 8
    for i in range(nparams):
        mid = dex.u32(at + 8 * i)
        off = dex.u32(at + 8 * i + 4)
        if not off:
            continue
        method = dex.method(mid)
        count = dex.u32(off)
        if count > MAX_PARAMS:
            raise ValueError("SOURCE_API_PARAMETER_LIMIT")
        for idx in range(count):
            set_off = dex.u32(off + 4 + 4 * idx)
            if not set_off:
                continue
            n = dex.u32(set_off)
            if n > MAX_ANNOTATIONS:
                raise ValueError("SOURCE_API_ANNOTATIONS_LIMIT")
            for j in range(n):
                aoff = dex.u32(set_off + 4 + 4 * j)
                if not aoff:
                    continue
                dex.bounds(aoff, 2)
                _, cursor = uleb(dex, aoff + 1)
                pairs, cursor = uleb(dex, cursor)
                if pairs > MAX_PAIRS:
                    raise ValueError("SOURCE_API_PAIRS_LIMIT")
                for _ in range(pairs):
                    key_idx, cursor = uleb(dex, cursor)
                    key = dex.string(key_idx)
                    value, cursor = _encoded_value(dex, cursor)
                    if key == "value" and isinstance(value, str) and value in LABELS:
                        result.setdefault(method, set()).add((idx, value))
    return result

def method_sources(dex, method, off):
    """Only same-method typed proximity: intentionally NOT argument alias proof."""
    source = set()
    for typ in audit.parse_types(method[2]):
        if typ == TRACK:
            source.add("PARAM_TRACK")
        if typ == ALBUM:
            source.add("PARAM_ALBUM")
    for pc, opcode, words in audit.instructions(dex, off):
        if opcode in (0x52, 0x53, 0x54, 0x55, 0x60, 0x61, 0x62):
            owner, _fname, ftype = audit.field_id(dex, words[1])
            if owner == TRACK and ftype in ("Ljava/lang/String;", "J", "Ljava/lang/Long;"):
                source.add("FIELD_FROM_TRACK_CLASS_NOT_SAME_OBJECT")
            if owner == ALBUM and ftype in ("Ljava/lang/String;", "J", "Ljava/lang/Long;"):
                source.add("FIELD_FROM_ALBUM_CLASS_NOT_SAME_OBJECT")
            if ftype == TRACK:
                source.add("TRACK_OBJECT_FIELD_READ")
            if ftype == ALBUM:
                source.add("ALBUM_OBJECT_FIELD_READ")
        elif opcode in audit.INVOKES:
            callee = dex.method(words[1])
            if callee[0] == TRACK:
                source.add("TRACK_MODEL_METHOD_CALL")
            if callee[0] == ALBUM:
                source.add("ALBUM_MODEL_METHOD_CALL")
    return sorted(source)

def scan(splits):
    apis_seen = set()
    api_specs = {}
    method_defs = {}
    api_calls = []
    accessor = {}
    dex_count = 0
    for apk in splits:
        with zipfile.ZipFile(apk) as z:
            for member in z.infolist():
                if not re.fullmatch(r"classes\d*\.dex", member.filename):
                    continue
                dex_count += 1
                dex = audit.Dex(z.read(member.filename))
                for ci in range(dex.class_count):
                    owner = dex.descriptor(dex.u32(dex.class_offset + ci * 32))
                    if owner not in APIS:
                        continue
                    apis_seen.add(APIS[owner])
                    for method, labels in api_parameter_labels(dex, ci).items():
                        if method[0] != owner:
                            raise ValueError("SOURCE_API_ANNOTATION_OWNER_DRIFT")
                        if labels:
                            if method in api_specs:
                                raise ValueError("SOURCE_API_ANNOTATED_METHOD_DUPLICATE")
                            api_specs[method] = sorted(labels)
                for method, flags, off in audit.method_definitions_with_flags(dex):
                    if method[0] in (TRACK, ALBUM) and method[1] in ("super", "if"):
                        key = ("TRACK" if method[0] == TRACK else "ALBUM") + "_" + method[1]
                        # String-producing getter method shape is informative
                        # but cannot be called a track ID without semantic provenance.
                        if method[2] == "()Ljava/lang/String;":
                            if key in accessor:
                                raise ValueError("SOURCE_MODEL_GETTER_DUPLICATE")
                            calls = set()
                            fields = []
                            n = 0
                            for pc, opcode, words in audit.instructions(dex, off):
                                n += 1
                                if opcode in (0x54, 0x53, 0x52):
                                    own, _field, ftype = audit.field_id(dex, words[1])
                                    if own == method[0]:
                                        fields.append(ftype)
                                elif opcode in audit.INVOKES:
                                    m = dex.method(words[1])
                                    if m[0].startswith(("Ljava/lang/", "Lkotlin/")):
                                        calls.add(m[0].split("/")[-1].rstrip(";"))
                            accessor[key] = {"instruction_count": n, "local_field_types_read": fields,
                                             "java_kotlin_invoker_classes": sorted(calls),
                                             "semantics_proven": False}
                    hits = []
                    for pc, opcode, words in audit.instructions(dex, off):
                        if opcode in audit.INVOKES:
                            invoked = dex.method(words[1])
                            if invoked[0] in APIS:
                                hits.append((pc, invoked))
                    if hits:
                        if len(api_calls) >= 150:
                            raise ValueError("SOURCE_API_CALLSITE_LIMIT")
                        api_calls.append((dex, method, off, hits))
    targets = {m:labels for m,labels in api_specs.items()
               if any(value in ("trackId", "track_id", "track-id")
                      for _,value in labels)}
    summaries = {kind: {"track_id_annotated_methods": 0, "all_annotated_methods": 0,
                        "all_callers": 0, "track_id_callers": 0,
                        "track_id_callers_with_same_method_track_proximity": 0}
                 for kind in APIS.values()}
    for method, labels in api_specs.items():
        summaries[APIS[method[0]]]["all_annotated_methods"] += 1
        if method in targets:
            summaries[APIS[method[0]]]["track_id_annotated_methods"] += 1
    for dex, caller, off, hits in api_calls:
        prox = method_sources(dex, caller, off)
        for _,m in hits:
            label = APIS[m[0]]
            summaries[label]["all_callers"] += 1
            if m in targets:
                summaries[label]["track_id_callers"] += 1
                if prox:
                    summaries[label]["track_id_callers_with_same_method_track_proximity"] += 1
    if dex_count != 6:
        raise ValueError("SOURCE_SIGNED_SIX_DEX_REQUIRED")
    return {
        "verdict": ("PUBLISHER_TRACKID_API_ANNOTATIONS_PRESENT_NOT_SOURCE_PROOF"
                    if targets else "NO_PROVEN_ANNOTATED_TRACKID_API_IN_SIGNED_2025"),
        "api_classes_present": sorted(apis_seen),
        "bounded_api_calls": summaries,
        "track_string_getter_structures_not_semantics": accessor,
        "distinct_track_album_edition_proven": False,
        "same_original_live_source_proven": False,
        "runtime_active_generation_proven": False,
        "replacement_connected": False,
        "private_method_or_field_names_disclosed": False
    }

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("GITHUB_REPOSITORY") != "manufact-test/nomusic":
        raise RuntimeError("API_PROVENANCE_CI_ONLY")
    if xapk.stat().st_size != trusted.PINNED_XAPK_BYTES or trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("API_PROVENANCE_SIGNED_HASH_DRIFT")
    with tempfile.TemporaryDirectory(prefix="celikom-api-route-") as tmp:
        splits = audit.unbundle_candidate(xapk, Path(tmp))
        if len(splits) != 16 or audit.verify_split_set(splits).get("verified_issuer_signed_splits") != 16:
            raise ValueError("API_PROVENANCE_ISSUER_SIGNED_16_SPLITS")
        base = [s for s in splits if not trusted.package_metadata(s).get("split")]
        if len(base) != 1 or trusted.sha256_file(base[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("API_PROVENANCE_SIGNED_BASE_MISMATCH")
        return scan(splits)

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    opts=p.parse_args()
    try:
        print(json.dumps(run(opts.xapk), sort_keys=True))
    except Exception as ex:
        print(json.dumps({"verdict":"API_PROVENANCE_SCAN_FAILED",
                          "error_type":type(ex).__name__,
                          "replacement_connected":False},sort_keys=True))
        raise SystemExit(2)
