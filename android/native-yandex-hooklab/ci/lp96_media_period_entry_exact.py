#!/usr/bin/env python3
"""Strict signed NAV17 exact Lp96 MediaPeriod entry, no active-audio claim.

Continues only from proven i$c -> Lp96 -> LuIb source retention.
Bounded to exact period-returning method on that verified Lp96 wrapper,
its declared return type and immediate typed callsites. Neither prepared
nor current playback follows from this static contract.
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
audit=trusted.audit
SOURCE="LSl6;"
PERIOD="Lo96;"
TARGET=("Lp96;","transient","(LSl6$b;LrH2;J)Lo96;")
SOURCE_ATTACH=("LWT1;","strictfp","(Ljava/lang/Object;LSl6;)V")
MAX_CALLS=96
MAX_SITE=32
MAX_FIELD=40


def period_target(method):
    return method == TARGET


def inspect_signed(splits):
    found=None
    dexes=[]
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("LP96_MEDIA_PERIOD_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes.append(dex)
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if period_target(method):
                        if found:raise ValueError("LP96_PERIOD_DUPLICATE_METHOD")
                        found=(dex,flags,off)
    if len(dexes)!=6:raise ValueError("LP96_PERIOD_EXPECTED_SIGNED_SIX_DEX")
    if not found or not found[2]:raise ValueError("LP96_PERIOD_EXACT_METHOD_NOT_FOUND")
    dex,flags,off=found
    callee_rows=[]
    field_reads=[]
    related_callsites=[]
    constructors=[]
    for ordinal,op,words in audit.instructions(dex,off):
        if op in audit.INVOKES and 0x6E<=op<=0x78:
            callee=dex.method(words[1])
            if len(callee_rows)>=MAX_CALLS:raise ValueError("LP96_PERIOD_INVOKE_LIMIT")
            row={"ordinal":ordinal,"owner":callee[0],"method":callee[1],
                 "signature":callee[2],"opcode":op}
            callee_rows.append(row)
            if callee[1]=="<init>" and len(constructors)<24:
                constructors.append(row)
        if 0x52<=op<=0x6d:
            owner,_name,typ=audit.field_id(dex,words[1])
            if len(field_reads)>=MAX_FIELD:raise ValueError("LP96_PERIOD_FIELD_LIMIT")
            field_reads.append({"ordinal":ordinal,"owner":owner,"type":typ,"opcode":op})
    # Only exact direct callsites, no global MediaPeriod or renderer census.
    for other in dexes:
        for caller,_flags,code_off in audit.method_definitions_with_flags(other):
            if caller==TARGET:continue
            for ordinal,op,words in audit.instructions(other,code_off):
                if op not in audit.INVOKES or not 0x6E<=op<=0x78:continue
                if other.method(words[1]) != TARGET:continue
                if len(related_callsites)>=MAX_SITE:raise ValueError("LP96_PERIOD_CALLER_LIMIT")
                related_callsites.append({
                    "caller_owner":caller[0],"caller_method":caller[1],
                    "caller_signature":caller[2],"ordinal":ordinal,
                })
    try:
        trace=audit.trace_track_identity_method_cfg(
            dex,TARGET,flags,off,
            extra_identity_types={
                SOURCE:"ORIGINAL_MEDIA_SOURCE",
                "Lp96;":"WRAPPING_SOURCE",
                "LuIb;":"SOURCE_BASE",
                PERIOD:"MEDIA_PERIOD",
            })
        identity_events=[
            row for row in trace.get("events",())
            if (row.get("identity_type") in ("ORIGINAL_MEDIA_SOURCE","MEDIA_PERIOD")
                or any(x.get("identity_type") in ("ORIGINAL_MEDIA_SOURCE","MEDIA_PERIOD")
                    for x in row.get("identity_arguments",()))
                or any(x.get("identity_type") in ("ORIGINAL_MEDIA_SOURCE","MEDIA_PERIOD")
                    for x in row.get("possible_identity_arguments",())))
        ]
        cfg_complete=True
        cfg_states=trace.get("processed_state_count")
        trace_error=None
    except (ValueError,audit.DexError) as e:
        identity_events=[]
        cfg_complete=False
        cfg_states=None
        trace_error=type(e).__name__
    # A return type or factory constructor is not a current audio decoder.
    return {
        "verdict":"LP96_EXACT_PERIOD_ENTRY_STATIC_CANDIDATE_NOT_ACTIVE_AUDIO",
        "six_signer_verified_dex":len(dexes),
        "Lp96_exact_media_period_signature":TARGET[2],
        "method_invokes":callee_rows,
        "constructor_invokes":constructors,
        "field_type_operations":field_reads,
        "exact_immediate_callers":related_callsites,
        "cfg_complete":cfg_complete,
        "cfg_states":cfg_states,
        "cfg_error":trace_error,
        "typed_identity_events":identity_events[:48],
        "typed_identity_events_truncated":len(identity_events)>48,
        "period_from_current_selected_player_source_proven":False,
        "decoder_audible_same_source_proven":False,
        "exact_album_edition_generation_proven":False,
        "CELIKOM_replacement_connected":False,
        "no_source_field_values_urls_audio_account_read":True,
    }


def run(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true":raise RuntimeError("EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("LP96_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("LP96_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-lp96-period-") as tmp:
        splits=audit.unbundle_candidate(xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("LP96_16_SPLITS_REQUIRED")
        signed=audit.verify_split_set(splits)
        if signed.get("verified_issuer_signed_splits")!=16:
            raise ValueError("LP96_SIGNER_MISMATCH")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE
                or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("LP96_PACKAGE_IDENTITY_MISMATCH")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("LP96_NAV17_BASE_MISMATCH")
        report=inspect_signed(splits)
    return {**report,"pinned_signed_NAV17_verified":True,"ephemeral_readonly":True}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:print(json.dumps(run(args.xapk),ensure_ascii=False,sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as e:
        code=str(e)
        print(json.dumps({"verdict":"LP96_PERIOD_EXACT_AUDIT_INCOMPLETE",
            "safe_code":code if re.fullmatch("[A-Z0-9_]{1,80}",code) else None,
            "CELIKOM_replacement_connected":False}))
        raise SystemExit(2)
