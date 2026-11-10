#!/usr/bin/env python3
"""Read-only signed Yandex DEX: trace concrete implementations of public ExoPlayer interfaces.

No app package patch, runtime, auth, account, audio or API traffic. The class
hierarchy is extracted from unchanged publisher-verified #170gpr split APKs.
A concrete method body is not evidence it is used for current audio playback.
"""
from __future__ import annotations
import json
import re
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
import audit_gpr_apkpure_once as source
from inspect_android_host import Dex, DEX_MAX
from trace_native_callers import method_definitions
from audit_native_media_engine import ARCHIVE_SHA, ARCHIVE_LENGTH

INTERFACES={
    "media3_exoplayer":"Landroidx/media3/exoplayer/ExoPlayer;",
    "legacy_exoplayer2":"Lcom/google/android/exoplayer2/ExoPlayer;",
}
METHOD_NAMES=frozenset(("prepare","setMediaSource","setMediaSources",
                        "setMediaItem","setMediaItems",
                        "createMediaSource","createDataSource"))
MAX_OWNERS=20
MAX_CLASSES=300000


def relations(dex) -> dict:
    """classdef DEX fields with bounded type-list handling and no source strings."""
    out={}
    for n in range(dex.class_count):
        p=dex.class_offset+n*32
        owner=dex.descriptor(dex.u32(p))
        flags=dex.u32(p+4)
        sup=dex.u32(p+8)
        interfaces_off=dex.u32(p+12)
        parents=[]
        if sup!=0xffffffff:
            parents.append(dex.descriptor(sup))
        if interfaces_off:
            count=dex.u32(interfaces_off)
            if count>128:raise ValueError("INVALID_INTERFACE_LIST")
            dex.bounds(interfaces_off+4, count*2)
            parents.extend(dex.descriptor(dex.u16(interfaces_off+4+2*i))
                           for i in range(count))
        if owner in out:raise ValueError("DUPLICATE_CLASS_DEFINITION")
        out[owner]=(flags, tuple(parents))
    return out


def transitive_implementors(relationships:dict, target:str)->list[str]:
    memo={}
    in_progress=set()
    def reaches(owner):
        if owner==target:return True
        if owner in memo:return memo[owner]
        if owner in in_progress:return False
        if owner not in relationships:return False
        in_progress.add(owner)
        result=any(reaches(x) for x in relationships[owner][1])
        in_progress.remove(owner)
        memo[owner]=result
        return result
    return sorted(owner for owner,(flags, _) in relationships.items()
                  if owner!=target and not flags & 0x200 and reaches(owner))


def bounded_name(owner):
    # Report only short compiler-generated class descriptors, never internal
    # full package names or arbitrary third-party strings.
    return owner if re.fullmatch(r"L[A-Za-z0-9_$]{1,16};",owner) else "REDACTED_NAMED_CLASS"


def summarize(relationships:dict, bodies:dict) ->dict:
    report={}
    for group, interface in INTERFACES.items():
        owners=transitive_implementors(relationships,interface)
        evidence=[]
        for owner in owners[:MAX_OWNERS]:
            source_methods=sorted(bodies.get(owner,set()))
            evidence.append({
                "bounded_owner":bounded_name(owner),
                "has_concrete_prepare_body":("prepare","()V") in source_methods,
                "public_api_methods_with_bodies":source_methods,
            })
        report[group]={
            "public_interface_defined":interface in relationships,
            "concrete_implementor_count":len(owners),
            "concrete_prepare_method_body_count":sum(
                ("prepare","()V") in bodies.get(o,set()) for o in owners),
            "first_concrete_candidates":evidence,
            "output_bounded":len(owners)>MAX_OWNERS,
            "audio_decoder_or_real_player_proven":False,
        }
    return report


def run():
    with tempfile.TemporaryDirectory(prefix="celikom-native-signed-impl-") as tmp:
        root=Path(tmp); archive=root/"signed.xapk"
        length,digest=source.download(archive)
        if length!=ARCHIVE_LENGTH or digest!=ARCHIVE_SHA:
            raise ValueError("EXACT_PUBLISHER_ARCHIVE_REQUIRED")
        apks=source.split_apks(archive,root)
        source.inspect_publisher(apks)
        if len(apks)!=5:raise ValueError("SIGNED_SPLITS_MISMATCH")
        combined={}
        bodies=defaultdict(set)
        count=0
        for apk in apks:
            with zipfile.ZipFile(apk) as z:
                for name in z.namelist():
                    if not re.fullmatch(r"classes[0-9]*\.dex",name):
                        continue
                    info=z.getinfo(name)
                    if info.file_size>DEX_MAX:raise ValueError("DEX_SIZE_INVALID")
                    d=Dex(z.read(info))
                    rel=relations(d)
                    overlap=set(combined).intersection(rel)
                    if overlap:raise ValueError("CROSS_DEX_DUPLICATE_CLASSES")
                    combined.update(rel)
                    if len(combined)>MAX_CLASSES:raise ValueError("CLASS_COUNT_LIMIT")
                    for idx, off in method_definitions(d):
                        owner,method,proto=d.method(idx)
                        if method in METHOD_NAMES:
                            bodies[owner].add((method,proto))
                    count+=1
        if count!=6:raise ValueError("SIGNED_DEX_COUNT_MISMATCH")
    return {
        "verdict":"SIGNED_NATIVE_PLAYER_INTERFACE_IMPLEMENTORS_STATIC_ONLY",
        "signed_original_splits":5,"signed_dex_count":count,
        "class_definitions_scanned":len(combined),
        "public_exoplayer_implementors":summarize(combined,bodies),
        "real_native_audio_source_swap_proven":False,
        "user_device_or_account_accessed":False,
        "patched_or_published_yandex":False,
    }


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True))
    except Exception:
        print(json.dumps({
            "verdict":"SIGNED_NATIVE_IMPLEMENTOR_SCAN_UNAVAILABLE",
            "real_native_audio_source_swap_proven":False,
            "patched_or_published_yandex":False,
        }))
        sys.exit(2)
