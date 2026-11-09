#!/usr/bin/env python3
"""Publisher-verified, non-mutating Yandex #170gpr track identity static audit.

Goal: distinguish existence of trackId in API from proof that CURRENT PLAYING
track+edition reaches native source before prepare (which is not proven).
Never sees a user account, media payload, URL, key, token, device or audio.
Only known route annotations, type signatures and exact static identifier names.
APK never published, installed or stored outside ephemeral GitHub CI.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import clone_native_splits_ephemeral as exact

from inspect_android_host import Dex
from trace_media_api_routes import inspect_media_route_annotations
from trace_native_callers import uleb
from trace_playaudio_boundary import _encoded_value

PREFIX = "Lcom/yandex/music/shared/player/content/remote/"
API_CLASSES = {
    PREFIX + "fileinfo/FileInfoApi;": "modern_fileinfo",
    PREFIX + "fileinfo/OldFileInfoApi;": "legacy_fileinfo",
    PREFIX + "downloadinfo/DownloadInfoApi;": "downloadinfo",
}
SOURCE_MODEL = {
    PREFIX + "fileinfo/FileInfoDto;",
    PREFIX + "fileinfo/OldGetFileInfoDto;",
    "Leed;",
}
IDENTITY_NAMES = {
    "trackId", "trackIds", "realId", "albumId", "edition",
    "track_id", "album_id", "id", "resourceId"
}
ROUTE_TARGETS = {
    "resources/v2/file-info",
    "get-file-info",
    "tracks/{trackId}/download-info"
}


def annotated_public_identity_params(dex):
    """Read ONLY pre-approved static identity parameter labels on selected APIs.

    Annotation values such as auth headers, device/session identifiers, URLs and
    other string literals are deliberately ignored, even when present.
    This is STATIC metadata; it is not an observed playback request.
    """
    # Explicit public playback/edition metadata labels only; NEVER log
    # arbitrary annotation values (tokens, headers, keys, device identifiers).
    allowed = {"trackId", "track_id", "track-id", "resourceId",
               "resource_id", "realId", "albumId", "album_id", "album-id",
               "playId", "track", "id", "quality", "codec", "codecs",
               "container", "bitrate", "format", "edition", "version"}
    hits = []
    for class_index in range(dex.class_count):
        base = dex.class_offset + class_index * 32
        owner = dex.descriptor(dex.u32(base))
        if owner not in API_CLASSES:
            continue
        annotations = dex.u32(base + 20)
        if not annotations:
            continue
        field_count = dex.u32(annotations + 4)
        method_count = dex.u32(annotations + 8)
        param_count = dex.u32(annotations + 12)
        if max(field_count, method_count, param_count) > 500:
            raise ValueError("UNEXPECTED_API_ANNOTATION_DIRECTORY")
        pos = annotations + 16 + (field_count + method_count) * 8
        dex.bounds(pos, param_count * 8)
        for i in range(param_count):
            method_idx = dex.u32(pos + i * 8)
            ref_list_off = dex.u32(pos + i * 8 + 4)
            if not ref_list_off:
                continue
            actual_owner, method_name, signature = dex.method(method_idx)
            if actual_owner != owner:
                raise ValueError("API_ANNOTATION_OWNER_MISMATCH")
            parameters = dex.u32(ref_list_off)
            if parameters > 25:
                raise ValueError("UNEXPECTED_PARAM_ANNOTATION_COUNT")
            dex.bounds(ref_list_off + 4, parameters * 4)
            for pidx in range(parameters):
                setoff = dex.u32(ref_list_off + 4 + pidx * 4)
                if not setoff:
                    continue
                annos = dex.u32(setoff)
                if annos > 15:
                    raise ValueError("UNEXPECTED_PARAMETER_ANNOTATION_SET")
                dex.bounds(setoff + 4, annos * 4)
                for ai in range(annos):
                    off = dex.u32(setoff + 4 + ai * 4)
                    dex.bounds(off, 2)
                    typ, cursor = uleb(dex, off + 1)
                    annotation_type = dex.descriptor(typ)
                    fields, cursor = uleb(dex, cursor)
                    if fields > 20:
                        raise ValueError("UNEXPECTED_ENCODED_ANNOTATION_FIELDS")
                    for _ in range(fields):
                        name_idx, cursor = uleb(dex, cursor)
                        key = dex.string(name_idx)
                        value, cursor = _encoded_value(dex, cursor)
                        if key != "value" or not isinstance(value, str) or value not in allowed:
                            continue
                        hits.append({
                            "api": API_CLASSES[owner],
                            "method": method_name,
                            "signature": signature,
                            "parameter_index": pidx,
                            "annotation_type": annotation_type,
                            "identity_label": value
                        })
    return hits


def inspect_splits(apks):
    method_defs = {}
    model_fields = {}
    route_matches = []
    identity_parameter_annotations = []
    exact_identity_strings = {s: 0 for s in IDENTITY_NAMES}
    dex_count = 0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for filename in z.namelist():
                if not re.fullmatch(r"classes\d*\.dex", filename):
                    continue
                dex_count += 1
                dex = Dex(z.read(filename))
                for i in range(dex.method_count):
                    owner, name, signature = dex.method(i)
                    if owner in API_CLASSES:
                        methods = method_defs.setdefault(API_CLASSES[owner], set())
                        methods.add((name, signature))
                for i in range(dex.string_count):
                    s = dex.string(i)
                    if s in exact_identity_strings:
                        exact_identity_strings[s] += 1
                count, off = dex.table(80, 8)
                for i in range(count):
                    pos = off + i * 8
                    owner = dex.descriptor(dex.u16(pos))
                    if owner not in SOURCE_MODEL:
                        continue
                    kind = "eed" if owner == "Leed;" else owner.split("/")[-1].rstrip(";")
                    field_type = dex.descriptor(dex.u16(pos + 2))
                    field_name = dex.string(dex.u32(pos + 4))
                    model_fields.setdefault(kind, set()).add((field_name, field_type))
                identity_parameter_annotations.extend(annotated_public_identity_params(dex))
                routes = inspect_media_route_annotations(z.read(filename))["route_matches"]
                route_matches.extend({
                    "api": API_CLASSES.get(r["interface_class"], "other"),
                    "route": r["static_route"],
                    "method": r["method"],
                    "signature": r["signature"]
                } for r in routes if r["static_route"] in ROUTE_TARGETS)
    if dex_count != 6:
        raise ValueError("PINNED_SIX_DEX_EXPECTED")
    for name in ("modern_fileinfo", "legacy_fileinfo", "downloadinfo"):
        if not method_defs.get(name):
            raise ValueError("REQUIRED_API_NOT_FOUND_" + name.upper())
    if not any(r["api"] == "downloadinfo" and r["route"] == "tracks/{trackId}/download-info"
               for r in route_matches):
        raise ValueError("DOWNLOAD_TRACK_ID_ROUTE_NOT_FOUND")
    return {
        "verdict": "STATIC_TRACK_ID_PRESENT_ACTIVE_PLAYBACK_BINDING_NOT_PROVEN",
        "signed_yandex_version": "2026.10.3 #170gpr",
        "signed_split_count": 5,
        "dex_count": dex_count,
        "fileinfo_api_method_signatures": {
            k: [{"method": n, "signature": sig} for n, sig in sorted(v)][:24]
            for k, v in sorted(method_defs.items())
        },
        "selected_static_route_annotations": sorted(
            route_matches, key=lambda x:(x["route"],x["method"]))[:24],
        "whitelisted_public_track_identity_param_annotations":
            sorted(identity_parameter_annotations,
                   key=lambda x:(x["api"],x["method"],x["parameter_index"]))[:40],
        "fileinfo_model_field_types": {
            k: [{"field": n,"type": t} for n,t in sorted(v)][:40]
            for k,v in sorted(model_fields.items())
        },
        "static_identity_names_present": {k: v for k, v in sorted(exact_identity_strings.items()) if v},
        "critical_limitation": (
            "trackId route is a DOWNLOAD endpoint. No evidence that it identifies the "
            "currently audible Yandex native source. FileInfoDto does not by itself "
            "prove track+edition association. Must later correlate an authorized "
            "in-process play request with source-before-prepare, without user secrets."
        ),
        "owner_phone_touched": False,
        "login_or_account_access": False,
        "native_audio_tested": False,
        "third_party_apk_distributed": False
    }


def main():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-trackid-static-") as td:
        td = Path(td)
        archive = td / "original-pinned.xapk"
        size, sha = exact.gpr.download(archive)
        if size != 60433885 or sha != exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_XAPK_ARCHIVE_PIN_CHANGED")
        apks = exact.gpr.split_apks(archive, td)
        if len(apks) != 5:
            raise ValueError("FIVE_ORIGINAL_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(apks)
        return inspect_splits(apks)


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"verdict":"STATIC_TRACK_ID_AUDIT_BLOCKED",
                          "error_type":type(exc).__name__,
                          "third_party_apk_distributed":False}))
        sys.exit(2)
