#!/usr/bin/env python3
"""Exact signed-2025 Track/Album identity annotation gate; read-only, CI only.

Read ONLY whitelisted JSON/serialization annotation labels on the original
Track and Album model fields. Do not expose obfuscated field names, arbitrary
annotation values, media, account data or any original APK bytes.
The output is a NEGATIVE/POSITIVE STATIC CANDIDATE, never an audio admission.
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
MODELS = {
    "track": "Lru/yandex/music/data/audio/o;",
    "album": "Lru/yandex/music/data/audio/Album;",
}
# Only semantic identifiers, not URLs, user strings or arbitrary vendor metadata.
LABELS = {
    "id", "trackid", "realid", "albumid", "editionid",
    "edition", "versionid", "playbackgeneration", "generation",
}
STRING = "Ljava/lang/String;"
FIELD_TYPES = {STRING, "J", "Ljava/lang/Long;", "I", "Ljava/lang/Integer;"}
MAX_FIELDS = 128
MAX_ANNOTATIONS = 20
MAX_ITEMS = 20

def safe_label(value):
    if not isinstance(value, str):
        return None
    # Normalise label, retaining only an already-whitelisted semantic token.
    name = re.sub(r"[_-]", "", value.lower())
    return name if name in LABELS else None

def annotations_for_field(dex, set_offset):
    if not set_offset:
        return set()
    count = dex.u32(set_offset)
    if count > MAX_ANNOTATIONS:
        raise ValueError("IDENTITY_ANNOTATION_SET_OVER_LIMIT")
    found = set()
    for i in range(count):
        offset = dex.u32(set_offset + 4 + i * 4)
        if not offset:
            continue
        dex.bounds(offset, 2)
        _, cur = uleb(dex, offset + 1)
        entries, cur = uleb(dex, cur)
        if entries > MAX_ITEMS:
            raise ValueError("IDENTITY_ANNOTATION_PAIRS_OVER_LIMIT")
        for _ in range(entries):
            key_idx, cur = uleb(dex, cur)
            key = dex.string(key_idx)
            value, cur = _encoded_value(dex, cur)
            if key in ("value", "name"):
                label = safe_label(value)
                if label:
                    found.add(label)
    return found

def scan(splits):
    result = {name: {"class_count": 0, "instance_field_count": 0,
                     "serialization_identity_fields": []}
              for name in MODELS}
    dex_count = 0
    for apk in splits:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes\d*\.dex", item.filename):
                    continue
                dex_count += 1
                dex = audit.Dex(z.read(item.filename))
                for i in range(dex.class_count):
                    base = dex.class_offset + i * 32
                    desc = dex.descriptor(dex.u32(base))
                    model = next((key for key, value in MODELS.items()
                                  if desc == value), None)
                    if model is None:
                        continue
                    row = result[model]
                    row["class_count"] += 1
                    class_data = dex.u32(base + 24)
                    if not class_data:
                        raise ValueError("IDENTITY_MODEL_NO_CLASS_DATA")
                    nstatic, pos = uleb(dex, class_data)
                    ninstance, pos = uleb(dex, pos)
                    _, pos = uleb(dex, pos)
                    _, pos = uleb(dex, pos)
                    if nstatic > MAX_FIELDS or ninstance > MAX_FIELDS:
                        raise ValueError("IDENTITY_MODEL_TOO_MANY_FIELDS")
                    last = 0
                    for _ in range(nstatic):
                        delta, pos = uleb(dex, pos)
                        last += delta
                        _, pos = uleb(dex, pos)
                    last = 0
                    local_fields = set()
                    for _ in range(ninstance):
                        delta, pos = uleb(dex, pos)
                        last += delta
                        _, pos = uleb(dex, pos)
                        fowner, _fname, ftype = audit.field_id(dex, last)
                        if fowner != desc:
                            raise ValueError("IDENTITY_MODEL_FIELD_OWNER_DRIFT")
                        local_fields.add(last)
                    row["instance_field_count"] = ninstance
                    annotation_off = dex.u32(base + 20)
                    if not annotation_off:
                        continue
                    nfields = dex.u32(annotation_off + 4)
                    nmethods = dex.u32(annotation_off + 8)
                    nparams = dex.u32(annotation_off + 12)
                    if max(nfields, nmethods, nparams) > 500:
                        raise ValueError("IDENTITY_MODEL_ANNOTATION_DIRECTORY_BOUND")
                    for j in range(nfields):
                        field_idx = dex.u32(annotation_off + 16 + j * 8)
                        set_offset = dex.u32(annotation_off + 20 + j * 8)
                        if field_idx not in local_fields:
                            continue
                        owner, _name, ftype = audit.field_id(dex, field_idx)
                        if owner != desc:
                            raise ValueError("IDENTITY_MODEL_ANNOTATED_FIELD_OWNER")
                        labels = annotations_for_field(dex, set_offset)
                        if labels:
                            row["serialization_identity_fields"].extend(
                                {"label": label, "type": ftype,
                                 "primitive_or_string": ftype in FIELD_TYPES}
                                for label in sorted(labels))
    if dex_count != 6 or any(v["class_count"] != 1 for v in result.values()):
        raise ValueError("IDENTITY_PINNED_SIX_DEX_MODEL_UNIQUE_REQUIRED")
    track = result["track"]["serialization_identity_fields"]
    album = result["album"]["serialization_identity_fields"]
    # Both id fields AND a distinct edition label are mandatory. An id alone
    # must NOT be treated as edition or current playback generation.
    has_track = any(v["label"] in ("trackid", "realid", "id") and
                    v["primitive_or_string"] for v in track)
    has_album = any(v["label"] in ("albumid", "id") and
                    v["primitive_or_string"] for v in album)
    has_edition = any(v["label"] in ("editionid", "edition", "versionid") and
                      v["primitive_or_string"] for v in track + album)
    return {
        "verdict": ("SERIALIZED_IDENTITY_FIELDS_CANDIDATE_NOT_CURRENT_SOURCE_PROOF"
                    if all((has_track, has_album, has_edition))
                    else "NO_GO_EXACT_ID_AND_EDITION_NOT_SEMANTICALLY_ATTESTED"),
        "models": result,
        "track_id_annotation_present": has_track,
        "album_id_annotation_present": has_album,
        "distinct_edition_annotation_present": has_edition,
        "current_playback_generation_proven": False,
        "active_source_album_edition_binding_proven": False,
        "replacement_connected": False,
        "private_field_names_or_values_exported": False,
    }

def run(xapk):
    if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("GITHUB_REPOSITORY") != "manufact-test/nomusic":
        raise RuntimeError("IDENTITY_EPHEMERAL_GITHUB_ONLY")
    if xapk.stat().st_size != trusted.PINNED_XAPK_BYTES or trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("IDENTITY_PUBLISHER_SIGNED_XAPK_HASH_DRIFT")
    with tempfile.TemporaryDirectory(prefix="celikom-track-annotation-") as tmp:
        splits = audit.unbundle_candidate(xapk, Path(tmp))
        if len(splits) != 16 or audit.verify_split_set(splits).get("verified_issuer_signed_splits") != 16:
            raise ValueError("IDENTITY_ISSUER_SIGNED_16_SPLITS_REQUIRED")
        base = [x for x in splits if not trusted.package_metadata(x).get("split")]
        if len(base) != 1 or trusted.sha256_file(base[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("IDENTITY_SIGNED_BASE_HASH_DRIFT")
        return scan(splits)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xapk", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.xapk), sort_keys=True))
    except Exception as e:
        # Keep any private exception text out of logs.
        print(json.dumps({"verdict":"IDENTITY_STATIC_SCAN_FAILED",
                          "error_type":type(e).__name__,
                          "replacement_connected":False}, sort_keys=True))
        raise SystemExit(2)
