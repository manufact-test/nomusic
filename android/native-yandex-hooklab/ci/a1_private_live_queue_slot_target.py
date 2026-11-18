#!/usr/bin/env python3
"""NAV28 CI-only exact publisher-signed 2025 h.SLOT_B Java reflection target.

The existing signed original 16-split CFG proof anchors e.break PC 547,
then proves the same field flows into e.catch at two unique callsites.
We write ONLY a generated Java FIELD NAME to the ephemeral private build.
Do not print private field names, raw XAPK content, tracks or identifiers.
No runtime vendor mutation, queue state reading or audio manipulation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import lft2_class_inspection as trusted
import secondary_renderer_attach_caller_owner_exact as secondary

TARGET=("Landroidx/media3/exoplayer/e;","break","()V")
EXPECTED_OWNER="Landroidx/media3/exoplayer/h;"
EXPECTED_TYPE="Lxh6;"
EXPECTED_PROOFS={(1051,1183),(2,51)}


def derive_signed_slot_field(xapk:Path)->str:
    if os.environ.get("GITHUB_ACTIONS")!="true" or (
            os.environ.get("GITHUB_REPOSITORY")!="manufact-test/nomusic"):
        raise RuntimeError("NAV28_PRIVATE_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("NAV28_PINNED_XAPK_SIZE")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("NAV28_PINNED_XAPK_HASH")
    with tempfile.TemporaryDirectory(prefix="celikom-private-nav28-") as tmp:
        apks=trusted.audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:raise ValueError("NAV28_SIGNED_16_SPLITS")
        signed=trusted.audit.verify_split_set(apks)
        if signed.get("verified_issuer_signed_splits")!=16:
            raise ValueError("NAV28_PUBLISHER_SIGNATURE")
        bases=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("NAV28_PUBLISHER_VERSION")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("NAV28_PINNED_PUBLISHER_BASE")
        report=secondary.scan_exact(apks)
        proofs=report["engine_enable_queue_slot_b_cfg_proofs"]
        actual={(row["source_pc"],row["target_engine_catch_pc"])
                for row in proofs
                if row.get("cfg_strict_same_holder_from_slot_b_proven")
                and row.get("field_is_exact_same_queue_slot_b")
                and row.get("same_object_reference_in_every_reaching_state")
                and row.get("source_dominates_target")}
        if actual!=EXPECTED_PROOFS or len(proofs)!=2:
            raise ValueError("NAV28_QUEUE_CFG_NOT_STRICT")
        fields=[]
        for apk in apks:
            with zipfile.ZipFile(apk) as archive:
                for member in archive.infolist():
                    if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):
                        continue
                    dex=trusted.audit.Dex(archive.read(member.filename))
                    for method,flags,offset in trusted.audit.method_definitions_with_flags(dex):
                        if not offset or method!=TARGET:continue
                        raw=next(((op,words)
                          for pc,op,words in trusted.audit.instructions(dex,offset)
                          if pc==547),None)
                        if raw is None or raw[0]!=0x54:
                            raise ValueError("NAV28_QUEUE_SOURCE_OPCODE")
                        owner,name,typ=trusted.audit.field_id(dex,raw[1][1])
                        if owner!=EXPECTED_OWNER or typ!=EXPECTED_TYPE:
                            raise ValueError("NAV28_QUEUE_FIELD_DESCRIPTOR")
                        if not isinstance(name,str) or not name or len(name)>100:
                            raise ValueError("NAV28_QUEUE_FIELD_NAME_INVALID")
                        fields.append(name)
        if len(fields)!=1:raise ValueError("NAV28_QUEUE_FIELD_SOURCE_NOT_UNIQUE")
        return fields[0]


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    p.add_argument("--private-java",required=True,type=Path)
    args=p.parse_args()
    if args.private_java.exists():raise ValueError("NAV28_PRIVATE_TARGET_ALREADY_EXISTS")
    field=derive_signed_slot_field(args.xapk)
    args.private_java.parent.mkdir(parents=True,exist_ok=True)
    java_name=json.dumps(field,ensure_ascii=True)
    args.private_java.write_text(
        "package pro.celikom.a1exitwitness;\n"
        "final class PrivateNativeQueueSlotTarget {\n"
        "  static final String QUEUE_SLOT_B_FIELD_NAME = " + java_name + ";\n"
        "  private PrivateNativeQueueSlotTarget() {}\n"
        "}\n",encoding="utf-8")
    print("NAV28_PUBLISHER_SIGNED_EXACT_QUEUE_SLOT_B_PRIVATE_TARGET_PASS")


if __name__=="__main__":
    main()
