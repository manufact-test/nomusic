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


def _exact_extractor_source_register(code: bytes, pc: int, opcode: int):
    """Dalvik 35c/3rc instance receiver + ONE MediaDataSource argument."""
    if opcode==0x6e:  # invoke-virtual {C,D}
        return code[pc+4]>>4 if code[pc+1]>>4==2 else None
    if opcode==0x74:  # invoke-virtual/range {vCCCC .. vNNNN}
        return struct.unpack_from("<H",code,pc+4)[0]+1 if code[pc+1]==2 else None
    return None


def _exact_extractor_register_origin(dex, code: bytes, instructions, index: int):
    """Conservative straight-line local backslice, with private class kept in memory.

    Never resolve through unknown branches, external calls, objects, registers,
    fields, track identity or decoder state. Source is only a static clue.
    """
    pc,opcode,_=instructions[index]
    register=_exact_extractor_source_register(code,pc,opcode)
    if register is None:
        return ("ARGUMENT_SHAPE_UNRESOLVED",None)
    for j in range(index-1,max(-1,index-81),-1):
        p,op,_=instructions[j]
        # A branch or exception edge prevents a reliable straight-line claim.
        if op in (0x0e,0x0f,0x10,0x11,0x27,0x28,0x29,0x2a,
                  0x2b,0x2c) or 0x32<=op<=0x3d:
            return ("FLOW_BOUNDARY_UNRESOLVED",None)
        if op==0x07:  # move-object vA,vB
            if code[p+1]&15==register:
                register=code[p+1]>>4
            continue
        if op==0x08:  # move-object/from16 vAA,vBBBB
            if code[p+1]==register:
                register=struct.unpack_from("<H",code,p+2)[0]
            continue
        if op==0x09:  # move-object/16 vAAAA,vBBBB
            if struct.unpack_from("<H",code,p+2)[0]==register:
                register=struct.unpack_from("<H",code,p+4)[0]
            continue
        if op==0x22 and code[p+1]==register:  # new-instance vAA,type@BBBB
            return ("NEW_INSTANCE",dex.type(struct.unpack_from("<H",code,p+2)[0]))
        if op==0x0c and code[p+1]==register:  # move-result-object
            if j>0 and instructions[j-1][1] in INVOKE_METHOD:
                return ("INVOKE_RETURN_OBJECT",None)
            return ("UNLINKED_RESULT",None)
        if op==0x54 and code[p+1]&15==register:  # iget-object
            return ("INSTANCE_OBJECT_FIELD",None)
        if op==0x62 and code[p+1]==register:  # sget-object
            return ("STATIC_OBJECT_FIELD",None)
        if op==0x46 and code[p+1]==register:  # aget-object
            return ("ARRAY_OBJECT_ELEMENT",None)
        if op==0x12 and code[p+1]&15==register:
            return ("LITERAL_OR_NULL",None)
        if op in (0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b,
                  0x23) and code[p+1]==register:
            return ("OTHER_REGISTER_WRITE",None)
    return ("PARAMETER_OR_CAPTURE_UNRESOLVED",None)


def classify_private_extractor_sink_rows(rows, superclasses, readat, getsize):
    """Publish finite categories ONLY; third-party class/caller never leaves memory."""
    candidates=sorted(owner for owner,parent in superclasses.items()
                      if parent=="Landroid/media/MediaDataSource;"
                      and owner in readat and owner in getsize)
    result=[]
    for caller,(kind,private_type) in rows[:4]:
        if kind=="NEW_INSTANCE":
            if private_type in candidates:
                kind="DIRECT_NEW_TARGET_"+str(candidates.index(private_type))
            else:
                kind="DIRECT_NEW_NON_TARGET"
        result.append(kind)
    return {
        "exact_2025_extractor_mediadatasource_callsites_bounded":len(rows),
        "exact_2025_extractor_mediadatasource_argument_categories":sorted(result),
        "private_source_class_or_caller_disclosed":False,
        "same_decoder_active_track_proven":False,
        "real_player_execution_proven":False,
    }



def exact_extractor_caller_return_shape(dex, method_index: int) -> str:
    """Only a public TYPE CATEGORY, never the private return descriptor.

    The exact signed DEX's caller may be a factory. A public return type
    still does not prove the extractor is used by the music player.
    """
    try:
        _owner,_name,proto=dex.method_signature(method_index)
        count,offset=struct.unpack_from("<II",dex.data,72)
        if not 0<=proto<count<=100000 or offset+count*12>len(dex.data):
            return "UNREADABLE_PROTO"
        type_idx=struct.unpack_from("<I",dex.data,offset+proto*12+4)[0]
        actual=dex.type(type_idx)
        if actual=="Landroid/media/MediaExtractor;":
            return "RETURNS_EXTRACTOR"
        if actual=="Landroid/media/MediaDataSource;":
            return "RETURNS_MEDIA_SOURCE"
        if actual=="Landroid/media/MediaFormat;":
            return "RETURNS_MEDIA_FORMAT"
        if actual=="V":
            return "RETURNS_VOID"
        if actual=="[B":
            return "RETURNS_BYTES"
        if actual in ("Z","B","S","C","I","J","F","D"):
            return "RETURNS_PRIMITIVE"
        return "RETURNS_OTHER_OBJECT" if actual.startswith(("L","[")) else "UNREADABLE_PROTO"
    except (AttributeError, IndexError, ValueError, struct.error, DexError):
        return "UNREADABLE_PROTO"


# Exact public Android framework method names only. These are STATIC DEX
# invocations, not proof of music playback, same extractor instance or even
# an executed branch. No private symbols or argument values are exported.
EXTRACTOR_LIFECYCLE_STEPS = {
    "setDataSource": "SET_SOURCE",
    "getTrackCount": "GET_TRACK_COUNT",
    "getTrackFormat": "GET_TRACK_FORMAT",
    "selectTrack": "SELECT_TRACK",
    "unselectTrack": "UNSELECT_TRACK",
    "readSampleData": "READ_SAMPLE_DATA",
    "advance": "ADVANCE",
    "getSampleTime": "GET_SAMPLE_TIME",
    "getSampleFlags": "GET_SAMPLE_FLAGS",
    "getSampleTrackIndex": "GET_SAMPLE_TRACK_INDEX",
    "seekTo": "SEEK_TO",
    "release": "RELEASE",
}
METADATA_RETRIEVER_STEPS = {
    "extractMetadata": "EXTRACT_METADATA",
    "getEmbeddedPicture": "GET_EMBEDDED_PICTURE",
}
def public_extractor_lifecycle_role(owner: str, name: str) -> str | None:
    if owner=="Landroid/media/MediaExtractor;":
        return EXTRACTOR_LIFECYCLE_STEPS.get(name)
    if owner=="Landroid/media/MediaMetadataRetriever;":
        return METADATA_RETRIEVER_STEPS.get(name)
    return None


def classify_private_extractor_sink_lifecycle(rows: list[dict]) -> dict:
    """Return only bounded public API enums for the *one* signed-2025 sink.

    Same-class marker does not imply same MediaExtractor object; same-method
    callsite presence does not imply execution. Synthetic tests guard this.
    """
    if len(rows)!=1:
        return {
            "exact_sink_count":min(len(rows),4),
            "same_method_public_framework_steps":[],
            "same_class_public_framework_steps":[],
            "caller_return_shapes":[],
            "caller_return_object_opcode_present":False,
            "same_method_reads_samples":False,
            "same_class_reads_samples":False,
            "unambiguous_single_static_sink":False,
            "live_playback_or_same_object_proven":False,
            "private_symbols_disclosed":False,
        }
    row=rows[0]
    method=sorted(set(row["same_method_steps"]))[:20]
    clazz=sorted(set(row["same_class_steps"]))[:20]
    return {
        "exact_sink_count":1,
        "same_method_public_framework_steps":method,
        "same_class_public_framework_steps":clazz,
        "caller_return_shapes":[row["return_shape"]],
        "caller_return_object_opcode_present":row["return_object_opcode"],
        "same_method_reads_samples":"READ_SAMPLE_DATA" in method,
        "same_class_reads_samples":"READ_SAMPLE_DATA" in clazz,
        "unambiguous_single_static_sink":True,
        "live_playback_or_same_object_proven":False,
        "private_symbols_disclosed":False,
    }

def count_direct_public_invocations(dex, private_sink_rows=None, sink_lifecycle_rows=None):
    """Actual DEX invoke instructions; never logs direct caller identities.

    A code path present in DEX is NOT proof that Android executed it.
    Unsupported instruction decoding remains explicit, not a false zero.
    """
    counts=Counter()
    overloads=Counter()
    complete=0
    undecoded=0
    same_body=0
    # These maps exist only in the ephemeral analysis process.
    lifecycle_by_owner={}
    exact_sink_methods=[]
    for _index, code in dex.code_methods():
        body_roles=set()
        framework_steps=[]
        found_exact_media_sink=False
        try:
            instructions=decode_instructions(code)
        except FlowDecodeError:
            undecoded+=1
            continue
        complete+=1
        for index,(pc,op,_) in enumerate(instructions):
            if op not in INVOKE_METHOD:
                continue
            method_index=struct.unpack_from("<H",code,pc+2)[0]
            if method_index>=dex.method_count:
                raise DexError("AUDIO_CALLSITE_REF_BOUND")
            public_owner,public_name=dex.method(method_index)
            step=public_extractor_lifecycle_role(public_owner,public_name)
            if step is not None:
                framework_steps.append(step)
            role=classify(public_owner,public_name)
            if role:
                counts[role]+=1
                body_roles.add(role)
                if role=="ANDROID_MEDIA_EXTRACTOR_SOURCE":
                    shape=extractor_argument_shape(dex,method_index)
                    overloads[shape]+=1
                    if shape=="MEDIA_DATA_SOURCE":
                        found_exact_media_sink=True
                        if private_sink_rows is not None:
                            # Keep all supplier types private in-run, never report names.
                            if len(private_sink_rows)>=4:
                                raise DexError("EXACT_EXTRACTOR_SINK_BOUND")
                            private_sink_rows.append((
                                dex.method(_index)[0],
                                _exact_extractor_register_origin(dex,code,instructions,index)))
        if framework_steps and sink_lifecycle_rows is not None:
            caller_owner=dex.method(_index)[0] # never serialized
            lifecycle_by_owner.setdefault(caller_owner,set()).update(framework_steps)
        if found_exact_media_sink and sink_lifecycle_rows is not None:
            if len(exact_sink_methods)>=4:
                raise DexError("EXACT_EXTRACTOR_LIFECYCLE_BOUND")
            exact_sink_methods.append((
                dex.method(_index)[0], tuple(framework_steps),
                exact_extractor_caller_return_shape(dex,_index),
                any(op==0x11 for _,op,_ in instructions)))
        if "ANDROID_MEDIA_EXTRACTOR_SOURCE" in body_roles and (
            "ANDROID_AUDIO_TRACK_OUTPUT" in body_roles or
            "ANDROID_MEDIA_CODEC_INPUT" in body_roles):
            same_body+=1
    if sink_lifecycle_rows is not None:
        for owner,steps,shape,returns_object in exact_sink_methods:
            if len(sink_lifecycle_rows)>=4:
                raise DexError("EXACT_EXTRACTOR_LIFECYCLE_BOUND")
            sink_lifecycle_rows.append({
                "same_method_steps":steps,
                "same_class_steps":tuple(lifecycle_by_owner.get(owner,())),
                "return_shape":shape,
                "return_object_opcode":returns_object,
            })
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
        exact_sink_rows=[]
        exact_sink_lifecycle=[]
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
                    direct=count_direct_public_invocations(d,exact_sink_rows,exact_sink_lifecycle)
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
        "exact_media_extractor_source_argument_audit":classify_private_extractor_sink_rows(
            exact_sink_rows,supers,readat,getsize),
        "exact_media_extractor_source_lifecycle_audit":classify_private_extractor_sink_lifecycle(
            exact_sink_lifecycle),
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
