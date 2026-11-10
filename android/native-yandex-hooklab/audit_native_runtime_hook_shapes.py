#!/usr/bin/env python3
"""Signed #170gpr exact-class runtime hook preflight, NOT a live audio proof.

Validates only the fixed known six-DEX method/typed-field shapes needed by
the read-only source-instance observer. Private field names, SDK resources,
URLs, codecs, DRM, track identities, DEX bytes and account data are NOT
output. Does not patch/install the publisher's app or claim a decoder.
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"tools"/"android-native-gate1"))
from inspect_android_host import Dex,DexError,DEX_MAX
from trace_native_callers import method_definitions
import clone_native_splits_ephemeral as exact

TARGETS={
    ("Lkvs;","A","(Lzcb;Lgmb;)Lemb;"),
    ("Lero;","t","(Ldmb;)V"),
    ("Lero;","remove","()V"),
    ("Lmb4;","a","()V"),
    ("Lha4;","b","(La58;)J"),
    ("Lha4;","read","([BII)I"),
    ("Lha4;","close","()V"),
}
OWNER_BUILDER=("Locv;","i0","()V")
LIMIT_DEX=6
MAX_BODIES=240000
MAX_LERO_READER_FIELDS=10
SHORT_LERO_CTOR="(Lwzi;Lga4;)V"



def check_shapes(methods,reader_fields):
    """No method body co-occurrence or player connection is inferred."""
    methods=set(methods)
    missing=TARGETS-methods
    return {
        "all_seven_concrete_runtime_methods_defined":not missing,
        "exact_target_definitions_found":len(TARGETS)-len(missing),
        "missing_target_count":len(missing),
        "one_typed_lero_lmb4_field":reader_fields==1,
        "leroreader_field_count":reader_fields,
        "runtime_selected_receiver_proven":False,
        "decoder_preprepare_proven":False,
    }


def check_lero_constructors(signatures):
    """Two independent real Lero creation paths, without exporting third type."""
    shapes=list(signatures)
    short=sum(s==SHORT_LERO_CTOR for s in shapes)
    long=sum(s.startswith("(Lwzi;Lga4;L") and s.endswith(";)V")
             and s!=SHORT_LERO_CTOR and s.count(";")==3
             for s in shapes)
    return {
        "exact_lero_constructor_short_count":short,
        "exact_lero_constructor_long_count":long,
        "direct_Locv_construction_can_bypass_kvs_factory":True,
        "both_exact_lero_creation_shapes_proven":short==1 and long==1,
        "actual_live_selected_source_or_decoder_proven":False,
    }


def inspect_signed(splits):
    defined=Counter()
    reader_fields=set()
    lero_constructors=[]
    dex_count=0
    bodies=0
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>DEX_MAX:raise ValueError("DEX_TOO_LARGE")
                d=Dex(archive.read(entry.filename))
                dex_count+=1
                n,off=d.table(80,8)
                for i in range(n):
                    pos=off+i*8
                    owner=d.descriptor(d.u16(pos))
                    typ=d.descriptor(d.u16(pos+2))
                    if owner=="Lero;" and typ=="Lmb4;":
                        # Keep name as internal join key only; NEVER print it.
                        reader_fields.add(d.string(d.u32(pos+4)))
                        if len(reader_fields)>MAX_LERO_READER_FIELDS:
                            raise ValueError("TOO_MANY_LERO_TYPED_READER_FIELDS")
                for idx,code in method_definitions(d):
                    bodies+=1
                    if bodies>MAX_BODIES:raise ValueError("METHOD_BOUND")
                    signature=d.method(idx)
                    if signature in TARGETS or signature==OWNER_BUILDER:
                        defined[signature]+=1
                    if signature[0]=="Lero;" and signature[1]=="<init>":
                        lero_constructors.append(signature[2])
    if dex_count!=LIMIT_DEX:raise ValueError("SIGNED_SIX_DEX_MISSING")
    if any(defined[t]!=1 for t in TARGETS):
        raise ValueError("EXACT_METHOD_DEFINITION_COUNT")
    if defined[OWNER_BUILDER]!=1:
        raise ValueError("EXACT_LOCV_I0_METHOD_MISSING_OR_AMBIGUOUS")
    result=check_shapes(defined,len(reader_fields))
    creation=check_lero_constructors(lero_constructors)
    if not creation["both_exact_lero_creation_shapes_proven"]:
        raise ValueError("EXACT_LERO_CONSTRUCTOR_PAIR_NOT_PROVEN")
    if not result["one_typed_lero_lmb4_field"]:
        raise ValueError("EXACT_LERO_READER_FIELD_COUNT")
    return {
        "signed_dex_count":dex_count,
        "method_bodies_scanned":bodies,
        **result,
        **creation,
        "signed_exact_ocv_i0_no_arg_void_count":defined[OWNER_BUILDER],
        "owner_constructor_runtime_nesting_proven":False,
        "original_apks_unchanged":True,
        "no_device_account_secret_url_media_or_dex_output":True,
    }


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise RuntimeError("SIGNED_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-native-exact-hook-preflight-") as root:
        directory=Path(root)
        original=directory/"original-signed-host.xapk"
        length,digest=exact.gpr.download(original)
        if length!=60433885 or digest!=exact.ARCHIVE_SHA:
            raise ValueError("PINNED_ORIGINAL_SHA_MISMATCH")
        splits=exact.gpr.split_apks(original,directory)
        if len(splits)!=5:raise ValueError("FIVE_SIGNED_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(splits)
        data=inspect_signed(splits)
    return {"verdict":"SIGNED_EXACT_READER_METHOD_AND_TYPED_FIELD_SHAPES_ONLY",**data}


if __name__=="__main__":
    try:
        print(json.dumps(run(),sort_keys=True,ensure_ascii=False))
    except (RuntimeError,ValueError,OSError,DexError,zipfile.BadZipFile) as exc:
        allowed={
            "DEX_TOO_LARGE","TOO_MANY_LERO_TYPED_READER_FIELDS","METHOD_BOUND",
            "SIGNED_SIX_DEX_MISSING","EXACT_METHOD_DEFINITION_COUNT",
            "EXACT_LERO_READER_FIELD_COUNT","SIGNED_CI_ONLY",
            "EXACT_LERO_CONSTRUCTOR_PAIR_NOT_PROVEN",
            "EXACT_LOCV_I0_METHOD_MISSING_OR_AMBIGUOUS",
            "PINNED_ORIGINAL_SHA_MISMATCH","FIVE_SIGNED_SPLITS_REQUIRED",
        }
        code=str(exc)
        print(json.dumps({
            "verdict":"SIGNED_EXACT_READER_HOOK_PREFLIGHT_REJECTED",
            "reason":code if code in allowed else type(exc).__name__,
            "native_decoder_or_player_identity_proven":False,
        },sort_keys=True))
        sys.exit(2)
