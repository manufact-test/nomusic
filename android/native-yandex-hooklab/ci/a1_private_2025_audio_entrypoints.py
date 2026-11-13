#!/usr/bin/env python3
"""Read-only exact 2025.10.4 publisher DEX audio API inventory.

No user playback, decoder hook, original modification, account, URL or
unredacted third-party class/method names in the report. API references
are not proof of executing source-before-decoder for a current track.
"""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile
import struct
from a1_private_dex_flow import decode_instructions, FlowDecodeError, INVOKE_METHOD

from a1_private_push_dex_method import Dex, DexError, EXPECTED_LEN, EXPECTED_SHA
from uptodown_2025_gpr_ephemeral_verify import unbundle_candidate, verify_split_set

# Exact, publicly documented Android/ExoPlayer APIs only.
PUBLIC_METHODS = {
    "MEDIA3_DATA_SOURCE_OPEN": {
        ("Landroidx/media3/datasource/DataSource;", "open"),
        ("Landroidx/media3/datasource/DefaultDataSource;", "open"),
        ("Landroidx/media3/datasource/DefaultHttpDataSource;", "open")},
    "MEDIA3_DATA_SOURCE_FACTORY": {
        ("Landroidx/media3/datasource/DataSource$Factory;", "createDataSource"),
        ("Landroidx/media3/datasource/DefaultDataSource$Factory;", "createDataSource"),
        ("Landroidx/media3/datasource/DefaultHttpDataSource$Factory;", "createDataSource")},
    "MEDIA3_MEDIA_SOURCE_FACTORY": {
        ("Landroidx/media3/exoplayer/source/MediaSource$Factory;", "createMediaSource"),
        ("Landroidx/media3/exoplayer/source/ProgressiveMediaSource$Factory;", "createMediaSource")},
    "MEDIA3_PLAYER_PREPARE": {
        ("Landroidx/media3/exoplayer/ExoPlayer;", "prepare"),
        ("Landroidx/media3/common/Player;", "prepare")},
    "LEGACY_EXOPLAYER_DATA_SOURCE": {
        ("Lcom/google/android/exoplayer2/upstream/DataSource;", "open"),
        ("Lcom/google/android/exoplayer2/upstream/DataSource$Factory;", "createDataSource"),
        ("Lcom/google/android/exoplayer2/upstream/DefaultDataSource$Factory;", "createDataSource")},
    "LEGACY_EXOPLAYER_PLAYER": {
        ("Lcom/google/android/exoplayer2/ExoPlayer;", "prepare"),
        ("Lcom/google/android/exoplayer2/Player;", "prepare")},
    "ANDROID_MEDIA_PLAYER_PREPARE": {
        ("Landroid/media/MediaPlayer;", "prepare"),
        ("Landroid/media/MediaPlayer;", "prepareAsync")},
    "ANDROID_MEDIA_EXTRACTOR_SOURCE": {
        ("Landroid/media/MediaExtractor;", "setDataSource")},
    "ANDROID_AUDIO_TRACK_OUTPUT": {
        ("Landroid/media/AudioTrack;", "write"),
        ("Landroid/media/AudioTrack;", "play")},
    "ANDROID_MEDIA_CODEC_INPUT": {
        ("Landroid/media/MediaCodec;", "configure"),
        ("Landroid/media/MediaCodec;", "queueInputBuffer"),
        ("Landroid/media/MediaCodec;", "dequeueOutputBuffer")}
}
# Historical 2026.10.3 #170gpr obfuscated classes are only a comparison
# against current 2025.10.4. Never assume these are the native source.
HISTORICAL = {
    ("Lcq7;", "i0"), ("Lga4;", "d"), ("Lha4;", "read"),
}

def classify(owner: str, name: str) -> str | None:
    return next((role for role, methods in PUBLIC_METHODS.items()
                 if (owner, name) in methods), None)

def summarize_methods(methods, defined_indices=()):
    counts=Counter()
    present=set()
    for index, (owner, name) in enumerate(methods):
        role=classify(owner,name)
        if role:
            counts[role]+=1
            if index in defined_indices:
                counts["DEFINED_"+role]+=1
        if (owner,name) in HISTORICAL:
            present.add((owner,name))
    return {
        "public_api_references": {k:min(counts[k], 9999) for k in PUBLIC_METHODS},
        "public_api_defined_bodies": {
            k:min(counts["DEFINED_"+k],9999) for k in PUBLIC_METHODS},
        "historical_2026_candidate_symbols_present_bounded":len(present),
        "active_current_track_or_decoder_binding_proven":False,
        "actual_audio_or_account_observed":False,
    }

# Classify standard framework setDataSource overloads only. Never print
# private Java signatures, path strings, content URIs or network endpoints.
EXTRACTOR_SHAPES=(
    "STRING_UNKNOWN_URI_OR_FILE", "FILE_DESCRIPTOR",
    "FD_OFFSET_LENGTH", "MEDIA_DATA_SOURCE", "CONTEXT_URI",
    "CONTEXT_URI_HEADERS", "OTHER_PUBLIC_SHAPE", "UNREADABLE_SHAPE"
)

def public_extractor_shape(parameters):
    names=tuple(parameters)
    fixed={
        ("Ljava/lang/String;",):"STRING_UNKNOWN_URI_OR_FILE",
        ("Ljava/io/FileDescriptor;",):"FILE_DESCRIPTOR",
        ("Ljava/io/FileDescriptor;","J","J"):"FD_OFFSET_LENGTH",
        ("Landroid/media/MediaDataSource;",):"MEDIA_DATA_SOURCE",
        ("Landroid/content/Context;","Landroid/net/Uri;"):"CONTEXT_URI",
        ("Landroid/content/Context;","Landroid/net/Uri;","Ljava/util/Map;"):"CONTEXT_URI_HEADERS",
    }
    return fixed.get(names,"OTHER_PUBLIC_SHAPE")

def extractor_argument_shape(dex, method_index):
    """Read the DEX proto list; return a fixed public overload enum only."""
    try:
        _owner,_name,proto=dex.method_signature(method_index)
        count,offset=struct.unpack_from("<II",dex.data,72)
        if proto>=count or offset+count*12>len(dex.data):
            return "UNREADABLE_SHAPE"
        params_off=struct.unpack_from("<I",dex.data,offset+proto*12+8)[0]
        if params_off==0:
            return public_extractor_shape(())
        if params_off+4>len(dex.data):
            return "UNREADABLE_SHAPE"
        n=struct.unpack_from("<I",dex.data,params_off)[0]
        if n>8 or params_off+4+n*2>len(dex.data):
            return "UNREADABLE_SHAPE"
        arg_types=[dex.type(struct.unpack_from("<H",dex.data,params_off+4+i*2)[0])
                   for i in range(n)]
        return public_extractor_shape(arg_types)
    except (AttributeError,IndexError,struct.error,DexError,ValueError):
        return "UNREADABLE_SHAPE"

def count_direct_public_invocations(dex):
    """Actual DEX invoke instructions; never logs direct caller identities.

    A code path present in DEX is NOT proof that Android executed it.
    Unsupported instruction decoding remains explicit, not a false zero.
    """
    counts=Counter()
    overloads=Counter()
    complete=0
    undecoded=0
    same_body=0
    for _index, code in dex.code_methods():
        body_roles=set()
        try:
            instructions=decode_instructions(code)
        except FlowDecodeError:
            undecoded+=1
            continue
        complete+=1
        for pc,op,_ in instructions:
            if op not in INVOKE_METHOD:
                continue
            method_index=struct.unpack_from("<H",code,pc+2)[0]
            if method_index>=dex.method_count:
                raise DexError("AUDIO_CALLSITE_REF_BOUND")
            role=classify(*dex.method(method_index))
            if role:
                counts[role]+=1
                body_roles.add(role)
                if role=="ANDROID_MEDIA_EXTRACTOR_SOURCE":
                    overloads[extractor_argument_shape(dex,method_index)]+=1
        if "ANDROID_MEDIA_EXTRACTOR_SOURCE" in body_roles and (
            "ANDROID_AUDIO_TRACK_OUTPUT" in body_roles or
            "ANDROID_MEDIA_CODEC_INPUT" in body_roles):
            same_body+=1
    return {
        "direct_public_invocation_counts":{k:min(counts[k],9999) for k in PUBLIC_METHODS},
        "android_extractor_callsite_overload_categories":{
            k:min(overloads[k],9999) for k in EXTRACTOR_SHAPES},
        "extractor_and_renderer_invoked_same_method_bodies_bounded":min(same_body,9999),
        "decoded_code_bodies_bounded":min(complete,999999),
        "undecoded_code_bodies_bounded":min(undecoded,999999),
        "executed_on_real_player_proven":False,
    }


def private_class_superclasses(dex):
    """Use DEX class-def metadata in memory; never emit vendor descriptors."""
    result={}
    for idx in range(dex.class_count):
        off=dex.class_off+32*idx
        if off+12>len(dex.data):
            raise DexError("AUDIO_CLASS_DEF_BOUNDS")
        class_idx=struct.unpack_from("<I",dex.data,off)[0]
        super_idx=struct.unpack_from("<I",dex.data,off+8)[0]
        name=dex.type(class_idx)
        if name in result:
            raise DexError("AUDIO_DUPLICATE_CLASS")
        result[name]=None if super_idx==0xffffffff else dex.type(super_idx)
    return result

def summarize_mediadatasource_inheritance(superclasses,readat_owners,getsize_owners):
    """Subclass structure, NOT a live player or proof any source is selected."""
    base="Landroid/media/MediaDataSource;"
    def is_child(owner):
        seen=set()
        name=owner
        for _ in range(16):
            if name in seen:
                return False
            seen.add(name)
            parent=superclasses.get(name)
            if parent==base:
                return True
            if parent is None:
                return False
            name=parent
        return False
    descendants={name for name in superclasses if is_child(name)}
    direct={name for name in superclasses if superclasses[name]==base}
    return {
        "direct_2025_mediadatasource_subclasses_bounded":min(len(direct),9999),
        "transitive_2025_mediadatasource_subclasses_bounded":min(len(descendants),9999),
        "descendant_readat_method_bodies_bounded":min(len(descendants & set(readat_owners)),9999),
        "descendant_getsize_method_bodies_bounded":min(len(descendants & set(getsize_owners)),9999),
        "current_playback_or_current_track_proven":False,
        "third_party_class_names_disclosed":False,
    }


def make_ephemeral_mediadatasource_targets(path: Path, superclasses, readat, getsize):
    """Generate only an OWN, temporary CI Java target table; never publish."""
    if (path.name!="PrivateMediaDataSourceTargets.java" or path.is_symlink()
        or "exit-callsite-witness-module" not in path.as_posix()
        or path.exists()):
        raise RuntimeError("PRIVATE_SOURCE_TARGET_PATH_INVALID")
    candidates=sorted(name for name,parent in superclasses.items()
                      if parent=="Landroid/media/MediaDataSource;"
                      and name in readat and name in getsize)
    if len(candidates)!=2 or any(
        re.fullmatch(r"L[A-Za-z0-9_/$]{1,180};",name) is None
        for name in candidates):
        raise RuntimeError("EXACT_TWO_PRIVATE_MEDIA_READERS_REQUIRED")
    dotted=[name[1:-1].replace("/",".") for name in candidates]
    lines=(
        "package pro.celikom.a1exitwitness;\n"
        "final class PrivateMediaDataSourceTargets {\n"
        "  static String[] classes() { return new String[]{"
        + ",".join('"'+name+'"' for name in dotted)
        + "}; }\n"
        "}\n"
    )
    file_descriptor=os.open(str(path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(file_descriptor,"w",encoding="utf-8") as out:
        out.write(lines)
    return len(candidates)

def scan_publisher(xapk: Path,private_java: Path|None=None) -> dict:
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!="experiment/android-a1-metrica-init-state-observer-arm13-20261112"
        or not xapk.is_file() or xapk.is_symlink()
        or xapk.stat().st_size!=EXPECTED_LEN):
        raise RuntimeError("EXACT_EPHEMERAL_2025_XAPK_ONLY")
    h=hashlib.sha256()
    with xapk.open("rb") as fp:
        for block in iter(lambda:fp.read(1024*1024), b""):
            h.update(block)
    if h.hexdigest()!=EXPECTED_SHA:
        raise RuntimeError("EXACT_2025_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="a1-2025-verified-audio-inventory-") as dirname:
        parts=unbundle_candidate(xapk,Path(dirname))
        if len(parts)!=16:
            raise RuntimeError("EXACT_2025_SPLIT_COUNT_INVALID")
        attestation=verify_split_set(parts)
        if not (
            attestation.get("verified_issuer_signed_splits")==16 and
            attestation.get("all_apks_cryptographically_signed") is True and
            attestation.get("exactly_one_2025_gpr_base_manifest") is True
        ):
            raise RuntimeError("EXACT_PUBLISHER_ATTESTATION_FAILED")
        combined=Counter()
        historical=set()
        dex_count=0
        total_decoded=0
        total_undecoded=0
        shared_bodies=0
        supers={}
        readat=set()
        getsize=set()
        for apk in parts:
            with zipfile.ZipFile(apk) as archive:
                if archive.testzip() is not None:
                    raise RuntimeError("PUBLISHER_ZIP_BAD_CRC")
                for info in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex",info.filename):
                        continue
                    if not 100<=info.file_size<=120*1024*1024:
                        raise RuntimeError("PUBLISHER_DEX_BOUND")
                    d=Dex(archive.read(info))
                    dex_count+=1
                    if dex_count>32:
                        raise RuntimeError("PUBLISHER_DEX_COUNT_EXCEEDED")
                    methods=[d.method(i) for i in range(d.method_count)]
                    defined={index for index,_code in d.code_methods()}
                    scan_classes=private_class_superclasses(d)
                    if supers.keys() & scan_classes.keys():
                        raise RuntimeError("AUDIO_DUPLICATE_CLASS_ACROSS_SPLITS")
                    supers.update(scan_classes)
                    readat.update(methods[i][0] for i in defined if methods[i][1]=="readAt")
                    getsize.update(methods[i][0] for i in defined if methods[i][1]=="getSize")
                    row=summarize_methods(methods,defined)
                    for key,value in row["public_api_references"].items(): combined[key]+=value
                    for key,value in row["public_api_defined_bodies"].items(): combined["DEFINED_"+key]+=value
                    historical.update((o,n) for o,n in methods if (o,n) in HISTORICAL)
                    direct=count_direct_public_invocations(d)
                    total_decoded+=direct["decoded_code_bodies_bounded"]
                    total_undecoded+=direct["undecoded_code_bodies_bounded"]
                    shared_bodies+=direct["extractor_and_renderer_invoked_same_method_bodies_bounded"]
                    for shape,n in direct["android_extractor_callsite_overload_categories"].items():
                        combined["SHAPE_"+shape]+=n
                    for role,n in direct["direct_public_invocation_counts"].items():
                        combined["CALL_"+role]+=n
        if dex_count==0:
            raise RuntimeError("PUBLISHER_DEX_MISSING")
        ephemeral_count=(make_ephemeral_mediadatasource_targets(
            private_java,supers,readat,getsize) if private_java is not None else 0)
    return {
        "private_media_target_count_bounded":ephemeral_count,
        "verdict":"VERIFIED_2025_PUBLISHER_AUDIO_API_INVENTORY_ONLY",
        "publisher_issuer_verified_splits":16,
        "publisher_dex_count_bounded":dex_count,
        "public_api_references":{k:min(combined[k],9999) for k in PUBLIC_METHODS},
        "public_api_defined_bodies":{k:min(combined["DEFINED_"+k],9999) for k in PUBLIC_METHODS},
        "historical_2026_candidate_symbols_present_bounded":len(historical),
        "direct_public_invocation_counts": {
            k:min(combined["CALL_"+k],9999) for k in PUBLIC_METHODS},
        "decoded_code_bodies_bounded":min(total_decoded,999999),
        "undecoded_code_bodies_bounded":min(total_undecoded,999999),
        "android_extractor_callsite_overload_categories":{
            k:min(combined["SHAPE_"+k],9999) for k in EXTRACTOR_SHAPES},
        "extractor_and_renderer_invoked_same_method_bodies_bounded":min(shared_bodies,9999),
        "mediadata_source_class_contract":summarize_mediadatasource_inheritance(
            supers,readat,getsize),
        "actual_current_track_binding_proven":False,
        "source_before_decoder_execution_proven":False,
        "native_audio_playback_proven":False,
        "vendor_binary_modified_or_published":False,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    parser.add_argument("--private-java",type=Path,default=None)
    args=parser.parse_args()
    try:
        print(json.dumps(scan_publisher(args.xapk,args.private_java),sort_keys=True))
    except Exception as err:
        # Deliberately do not disclose private exception text or paths.
        print(json.dumps({"verdict":"PUBLISHER_AUDIO_API_INVENTORY_INCOMPLETE",
                          "reason_class":type(err).__name__,
                          "native_audio_playback_proven":False},sort_keys=True))
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
