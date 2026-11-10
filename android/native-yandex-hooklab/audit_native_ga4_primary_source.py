#!/usr/bin/env python3
"""Read-only signed Yandex DEX investigation of Lga4 TWO Le48 slots.

The concrete Le48 instance consumed by Lga4.d differs from the one read by
Lga4.b/c. Trace both exact slots, then inspect typed source factory Lcq7.A
and Leyc.d without literal bytes, URLs or media. Do not infer runtime current
track, native decoder prepare, or applicability to Android audio playback.
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

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
from inspect_android_host import Dex,DexError,DEX_MAX
from trace_native_callers import method_definitions
from audit_native_ga4_field2_value_origins import (
    discover_read_slot,exact_store_witnesses,safe_writer_structural_excerpt,
    safe_operand_metadata
)
from audit_native_ga4_field_receiver import field_key
from audit_native_register_bridge import instructions
from audit_native_typed_wrapper_coroutines import method_profile
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

TARGETS={
    ("Lcq7;","A"),("Lcq7;","i0"),
    ("Leyc;","d"),("Lga4;","b"),("Lga4;","c"),("Lga4;","d"),
    ("Lya4;","a"),("Lza4;","b"),
}
MAX_SUMMARIES=32
MAX_WRITES=40
MAX_SHAPE_OPS=160


def writer_evidence_for_slot(apks,slots,label):
    """Exact field-key identity retained privately; only bounded summaries out."""
    output=[]
    total_dex=0
    matching_bodies=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for entry in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>DEX_MAX:raise ValueError("DEX_TOO_LARGE")
                d=Dex(z.read(entry.filename))
                total_dex+=1
                # Slot values may be referenced in multiple signed DEX files;
                # never compare raw field indices across DEX.
                present={key for i in range(d.table(80,8)[0])
                         if (key:=field_key(d,i)) in slots}
                if not present:continue
                for mid,coff in method_definitions(d):
                    matching_bodies+=1
                    triple=d.method(mid)
                    witness=exact_store_witnesses(d,coff,present)
                    if not witness:continue
                    excerpts=safe_writer_structural_excerpt(d,coff,present)
                    for site in witness:
                        output.append({
                            "writer":bounded_obfuscated(triple),
                            "writer_profile":method_profile(triple),
                            "register_origin":site["value_provenance"],
                            "structural_windows":excerpts[:3],
                        })
                    if len(output)>MAX_WRITES:
                        raise ValueError("EXCESSIVE_DIRECT_WRITERS")
    if total_dex!=6:raise ValueError("REQUIRED_SIGNED_SIX_DEX")
    return {
        "slot":label,
        "direct_write_site_count":len(output),
        "scan_method_body_count":matching_bodies,
        "writers":output,
        "source_instance_bound_to_active_track":False,
    }


def exact_method_outlines(apks):
    found={}
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for e in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",e.filename):continue
                d=Dex(z.read(e.filename))
                dex_count+=1
                for mid,coff in method_definitions(d):
                    method=d.method(mid)
                    if (method[0],method[1]) not in TARGETS:continue
                    ins=list(instructions(d,coff))
                    important=[{
                        "ordinal":idx,
                        **safe_operand_metadata(d,op,word)
                    } for idx,(_,op,word) in enumerate(ins[:MAX_SHAPE_OPS])]
                    if method in found:raise ValueError("DUPLICATED_TARGET_METHOD")
                    found[method]={
                        "profile":method_profile(method),
                        "instruction_count":len(ins),
                        "roles_truncated":len(ins)>MAX_SHAPE_OPS,
                        "register_and_callsite_shapes":important,
                        "actual_audio_decoder_proven":False,
                    }
    if dex_count!=6:raise ValueError("WRONG_DEX_COUNT")
    if not any(m[0]=="Lcq7;" and m[1]=="A" for m in found):
        raise ValueError("SOURCE_BUILDER_LCQ7_A_ABSENT")
    if not any(m[0]=="Leyc;" and m[1]=="d" for m in found):
        raise ValueError("TRANSFORM_LEYC_D_ABSENT")
    return {
        "method_count":len(found),
        "source_factory_methods":[{"owner_method":bounded_obfuscated(m),**rec}
                              for m,rec in sorted(found.items())[:MAX_SUMMARIES]],
    }


def scan_signed(apks):
    secondary=discover_read_slot(apks,reader_method="c")
    secondary_b=discover_read_slot(apks,reader_method="b")
    primary=discover_read_slot(apks,reader_method="d")
    if secondary!=secondary_b:
        raise ValueError("LE48_SECONDARY_READER_MISMATCH")
    if primary==secondary:
        raise ValueError("SOURCE_AND_SECONDARY_LE48_FIELDS_MIXED")
    one=writer_evidence_for_slot(apks,primary,"Lga4.d-reader")
    two=writer_evidence_for_slot(apks,secondary,"Lga4.b/c-reader")
    return {
        "publisher_original_split_apks":5,
        "publisher_original_dex":6,
        "Le48_primary_different_from_secondary":True,
        "actual_Lga4_d_reads_primary":True,
        "actual_Lga4_b_and_c_read_secondary":True,
        "primary_field_sources":one,
        "secondary_field_sources":two,
        "typed_source_factory_signatures":exact_method_outlines(apks),
        "FileInfo_trackId_edition_generation_bound_to_current_decoder":False,
        "native_audio_replacement_proven":False,
        "original_apk_patched_or_exported":False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("ORIGINAL_SIGNED_READ_ONLY_CI")
    with tempfile.TemporaryDirectory(prefix="celikom-exact-two-le48-slots-") as tmp:
        root=Path(tmp)
        archive=root/"publisher-original-unchanged.xapk"
        length,digest=exact.gpr.download(archive)
        if length!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_ARCHIVE_HASH_MISMATCH")
        apks=exact.gpr.split_apks(archive,root)
        if len(apks)!=5:raise ValueError("EXPECTED_FIVE_SIGNED_SPLITS")
        exact.gpr.inspect_publisher(apks)
        evidence=scan_signed(apks)
    return {"verdict":"SIGNED_TWO_LE48_SLOTS_TYPED_SOURCE_CANDIDATES_NOT_DECODER",
            **evidence,
            "no_original_app_user_account_or_media_access":True}


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,DexError,OSError,zipfile.BadZipFile) as exc:
        print(json.dumps({"verdict":"SIGNED_TWO_LE48_FIELD_READER_AUDIT_INCOMPLETE",
                          "error_class_only":type(exc).__name__,
                          "native_audio_replacement_proven":False}))
        sys.exit(2)
