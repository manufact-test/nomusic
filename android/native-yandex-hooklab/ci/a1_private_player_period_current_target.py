#!/usr/bin/env python3
"""NAV41: publisher-signed-only exact current PlaybackInfo PeriodID field-name compiler.

Compiles exactly seven DEX-anchored *field names* into one ephemeral private
Java class used only by CELIKOM's read-only cloned-app observer. Never exports
those names, values, music or signed DEX into git, logs or owner reports.
All hard identity claims remain STRUCTURAL_ONLY until owner phone observation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import exo_queue_slot_role_exact as exact
import lft2_class_inspection as trusted

audit=trusted.audit
EXPECTED_FIELDS=(
    ("ENGINE_PLAYBACK_INFO",1260,0x54,exact.ENGINE[0],exact.PLAYBACK_INFO),
    ("PLAYBACK_INFO_CURRENT_ID",1262,0x54,exact.PLAYBACK_INFO,exact.PERIOD_ID),
    ("HOLDER_INFO",1266,0x54,exact.HOLDER,exact.PERIOD_INFO),
    ("HOLDER_PERIOD_ID",1268,0x54,exact.PERIOD_INFO,exact.PERIOD_ID),
    ("PERIOD_UID",1264,0x54,exact.PERIOD_ID,"Ljava/lang/Object;"),
    ("PERIOD_FIRST_INT",1282,0x52,exact.PERIOD_ID,"I"),
    ("PERIOD_SECOND_INT",1295,0x52,exact.PERIOD_ID,"I"),
)

def pinned_names_from_engine(dex,off):
    """Only exact signed e.break instruction PCs; unknown opcode/field rejects."""
    code={pc:(op,words) for pc,op,words in audit.instructions(dex,off)}
    result={}
    for key,pc,want_op,want_owner,want_type in EXPECTED_FIELDS:
        op,words=code.get(pc,(None,None))
        if op!=want_op:
            raise ValueError("NAV41_EXACT_FIELD_OPCODE_OR_PC_DRIFT")
        owner,name,typ=audit.field_id(dex,words[1])
        if (owner!=want_owner or typ!=want_type or
            not isinstance(name,str) or not name or len(name)>100 or
            not re.fullmatch(r"[A-Za-z0-9_$<>-]+",name)):
            raise ValueError("NAV41_EXACT_FIELD_TYPE_OR_PRIVATE_NAME_INVALID")
        result[key]=name
    def f(pc,op=0x52):
        row=code.get(pc)
        if row is None or row[0]!=op:raise ValueError("NAV41_INT_FIELD_PC_DRIFT")
        return audit.field_id(dex,row[1][1])
    if (f(1282)!=f(1291) or f(1295)!=f(1297)
            or f(1282)==f(1295)):
        raise ValueError("NAV41_TWO_INTS_NOT_DISTINCT_OR_NOT_PAIRED")
    if f(1264,0x54)!=f(1270,0x54):
        raise ValueError("NAV41_UID_FIELD_MISMATCH")
    if (f(1260,0x54)!=f(1278,0x54) or
            f(1262,0x54)!=f(1280,0x54) or
            f(1266,0x54)!=f(1287,0x54) or
            f(1268,0x54)!=f(1289,0x54)):
        raise ValueError("NAV41_SECOND_SNAPSHOT_FIELD_MISMATCH")
    return result

def derive_signed_private_field_names(xapk:Path):
    if os.environ.get("GITHUB_ACTIONS")!="true" or (
        os.environ.get("GITHUB_REPOSITORY")!="manufact-test/nomusic"):
        raise RuntimeError("NAV41_PRIVATE_SIGNED_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("NAV41_PINNED_XAPK_SIZE")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("NAV41_PINNED_XAPK_HASH")
    with tempfile.TemporaryDirectory(prefix="celikom-nav41-original-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16 or audit.verify_split_set(apks).get(
                "verified_issuer_signed_splits")!=16:
            raise ValueError("NAV41_PUBLISHER_ISSUER_OR_SPLITS")
        bases=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("NAV41_PUBLISHER_PACKAGE_VERSION")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("NAV41_SIGNED_BASE_MISMATCH")
        # Reuse all currently green exact checks rather than create
        # another speculative mapping between source, front and SLOT_B.
        signed=exact.scan_signed(apks)
        front=signed.get("exact_original_player_front_UID_equals_boundary",{})
        post=signed.get("exact_original_player_front_post_UID_guard",{})
        correspondence=signed.get("exact_player_state_field_correspondence",{})
        if not (
            front.get("original_java_equals_receives_player_uid_and_front_holder_uid")
            and post.get("post_UID_both_IDs_test_same_exact_first_int_field_against_minus_one")
            and post.get("second_int_field_same_for_both_and_distinct_from_first")
            and correspondence.get("engine_timeline_field_matches_player_M0")
            and correspondence.get("engine_player_ID_field_exact_M0_iget_match_PCs")==[74,96,259]
            and correspondence.get("engine_player_ID_field_M0_distinct_PCs")==[138,257]
        ):
            raise ValueError("NAV41_SIGNED_PLAYER_PERIOD_BRIDGE_NOT_PROVEN")
        matches=[]
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for member in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):
                        continue
                    dex=audit.Dex(archive.read(member.filename))
                    for method,flags,off in audit.method_definitions_with_flags(dex):
                        if method==exact.ENGINE and off:
                            matches.append(pinned_names_from_engine(dex,off))
        if len(matches)!=1:
            raise ValueError("NAV41_EXACT_ONE_ENGINE_METHOD")
        return matches[0]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",required=True,type=Path)
    parser.add_argument("--private-java",required=True,type=Path)
    opts=parser.parse_args()
    if opts.private_java.exists():
        raise ValueError("NAV41_PRIVATE_TARGET_ALREADY_EXISTS")
    fields=derive_signed_private_field_names(opts.xapk)
    opts.private_java.parent.mkdir(parents=True,exist_ok=True)
    content="package pro.celikom.a1exitwitness;\n"
    content+="final class PrivateNativePlayerPeriodTarget {\n"
    for key,_,_,_,_ in EXPECTED_FIELDS:
        content+="  static final String "+key+" = "+json.dumps(fields[key],ensure_ascii=True)+";\n"
    content+="  private PrivateNativePlayerPeriodTarget() {}\n}\n"
    opts.private_java.write_text(content,encoding="utf-8")
    print("NAV41_PINNED_SIGNED_PLAYER_CURRENT_PERIOD_TARGET_PASS")

if __name__=="__main__":
    main()
