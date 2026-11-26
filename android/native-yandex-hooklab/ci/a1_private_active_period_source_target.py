#!/usr/bin/env python3
"""NAV29 private signed-original exact active-period field name compiler.
Never prints or commits private original DEX member names or media values.
Issuer-signed 2025 16 splits required. Generates only ephemeral own Java.
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
import holder_stream_origin_exact as holder_proof
import lp96_media_period_entry_exact as source_proof
import lca9_exact_source_player_identity as player_proof
import native_period_activation_handoff_exact as period_proof

audit=trusted.audit
HOLDER_CTOR=holder_proof.HOLDER_CONSTRUCTOR
HOLDER_SELECT=holder_proof.HOLDER_SELECT
WRAP_CTOR=period_proof.PERIOD_WRAPPER_CTOR
SOURCE_FACTORY=source_proof.TARGET
REQUIRED={
    HOLDER_CTOR,HOLDER_SELECT,
    holder_proof.PERIOD_WRAPPER_SELECT,holder_proof.ORIGINAL_PERIOD_SELECT,
    holder_proof.STREAM_ADAPTER_CTOR,WRAP_CTOR,SOURCE_FACTORY
}

def require_adapter_identity_proofs(adapter_checked, child_checked):
    """Require both wrapper/array wiring and the separate child-argument CFG proof."""
    if not (
            adapter_checked.get("child_stream_array_allocated_and_passed_to_nested_MediaPeriod")
            and adapter_checked.get("child_sample_stream_array_element_loaded_for_adapter")
            and adapter_checked.get("adapter_child_stream_identity_compared_with_existing_delegate")
            and adapter_checked.get("new_adapter_stores_exact_child_stream_typed_field")
            and adapter_checked.get("same_adapter_array_field_read_after_store")
            and adapter_checked.get("selected_adapter_written_into_original_holder_stream_array")
            and child_checked.get("child_same_reference_on_all_scoped_ctor_reaching_states")
            and child_checked.get("constructor_stores_exact_incoming_LR29_argument")
            and child_checked.get("scoped_reaching_state_count", 0) > 0):
        raise ValueError("NAV31_CHILD_STREAM_ADAPTER_IDENTITY_UNPROVEN")


def derive_fields(splits):
    if player_proof.scan_signed(splits).get(
        "same_LiLb_instance_constructor_to_player_setter_proven") is not True:
        raise ValueError("NAV29_WRAPPER_SOURCE_SETTER_STATIC_PROOF")
    source=source_proof.inspect_signed(splits)
    if not source["strict_same_source_period_witness"].get(
        "static_same_source_to_returned_MediaPeriod_proven"):
        raise ValueError("NAV29_SOURCE_TO_PERIOD_IDENTITY_NOT_PROVEN")
    methods={}
    for apk in splits:
        with zipfile.ZipFile(apk) as archive:
            for member in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",member.filename):continue
                dex=audit.Dex(archive.read(member.filename))
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if method not in REQUIRED:continue
                    if method in methods:raise ValueError("NAV29_DUPLICATE_TARGET")
                    if not off:raise ValueError("NAV29_EMPTY_TARGET")
                    methods[method]=(dex,flags,off)
    if set(methods)!=REQUIRED:raise ValueError("NAV29_MISSING_OR_DUPLICATE_TARGET")
    checked=holder_proof.verify_exact_holder_wrapper_period_selection(methods)
    if not (checked.get("Lup1_stored_and_read_from_same_exact_Lxh6_field")
            and checked.get("exact_Lup1_object_allocated_and_initialized_in_holder")):
        raise ValueError("NAV29_HOLDER_WRAPPER_IDENTITY_UNPROVEN")
    adapter_checked=holder_proof.verify_exact_native_child_to_holder_stream_adapter(
        methods)
    child_checked=holder_proof.verify_adapter_child_parameter_identity(methods)
    require_adapter_identity_proofs(adapter_checked,child_checked)
    def at(method,pc,opcode,expected_owner,expected_type):
        dex,_flags,off=methods[method]
        insn=next(((op,words) for p,op,words in audit.instructions(dex,off)
                   if p==pc),None)
        if insn is None or insn[0]!=opcode:
            raise ValueError("NAV29_EXACT_FIELD_PC_OPCODE_MISMATCH")
        owner,name,typ=audit.field_id(dex,insn[1][1])
        if owner!=expected_owner or typ!=expected_type:
            raise ValueError("NAV29_EXACT_FIELD_DECLARED_TYPE_MISMATCH")
        if not isinstance(name,str) or not name or len(name)>100:
            raise ValueError("NAV29_PRIVATE_FIELD_NAME_INVALID")
        return name
    holder_field=at(HOLDER_CTOR,136,0x5b,"Lxh6;","Ljava/lang/Object;")
    if holder_field!=at(HOLDER_SELECT,61,0x54,"Lxh6;","Ljava/lang/Object;"):
        raise ValueError("NAV29_HOLDER_WRAPPER_READ_WRITE_DIFFER")
    # Only the exact original native period object store from the Lwh6 arg.
    wd,_wf,wo=methods[WRAP_CTOR]
    wrapper_fields=[]
    for pc,op,words in audit.instructions(wd,wo):
        if op!=0x5b:continue
        owner,name,typ=audit.field_id(wd,words[1])
        if owner=="Lup1;" and typ=="Lwh6;":
            wrapper_fields.append(name)
    if len(wrapper_fields)!=1:
        raise ValueError("NAV29_WRAPPER_EXACT_ONE_PERIOD_FIELD")
    # The wrapper retains the exact adapters which it publishes into the
    # native holder's SampleStream[]; each adapter retains its child stream.
    wrapper_adapters_field=at(
        holder_proof.PERIOD_WRAPPER_SELECT,130,0x54,"Lup1;","[Lup1$a;")
    if wrapper_adapters_field!=at(
            holder_proof.PERIOD_WRAPPER_SELECT,147,0x54,
            "Lup1;","[Lup1$a;"):
        raise ValueError("NAV31_WRAPPER_ADAPTER_ARRAY_READS_DIFFER")
    adapter_child_field=at(
        holder_proof.PERIOD_WRAPPER_SELECT,136,0x54,"Lup1$a;","LR29;")
    if adapter_child_field!=at(
            holder_proof.STREAM_ADAPTER_CTOR,5,0x5b,
            "Lup1$a;","LR29;"):
        raise ValueError("NAV31_ADAPTER_CHILD_STREAM_FIELD_DIFFER")
    # The Lo96 object holds exactly the original LSl6 source from LuIb.
    source_field=at(SOURCE_FACTORY,18,0x5b,"Lo96;","LSl6;")
    return (holder_field,wrapper_fields[0],source_field,
            wrapper_adapters_field,adapter_child_field)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    p.add_argument("--private-java",required=True,type=Path)
    args=p.parse_args()
    if os.environ.get("GITHUB_ACTIONS")!="true" or (
            os.environ.get("GITHUB_REPOSITORY")!="manufact-test/nomusic"):
        raise RuntimeError("NAV29_PRIVATE_CI_ONLY")
    if not args.xapk.is_file() or args.xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("NAV29_PINNED_SIGNED_XAPK_SIZE")
    if trusted.sha256_file(args.xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("NAV29_PINNED_SIGNED_XAPK_HASH")
    if args.private_java.exists():raise ValueError("NAV29_PRIVATE_JAVA_ALREADY_EXISTS")
    with tempfile.TemporaryDirectory(prefix="celikom-nav29-signed-") as tmp:
        splits=audit.unbundle_candidate(args.xapk,Path(tmp))
        if len(splits)!=16:raise ValueError("NAV29_16_SPLITS_REQUIRED")
        verified=audit.verify_split_set(splits)
        if verified.get("verified_issuer_signed_splits")!=16:
            raise ValueError("NAV29_PUBLISHER_ISSUER_SIGNATURE")
        bases=[]
        for apk in splits:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE
                    or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("NAV29_PUBLISHER_VERSION_PACKAGE")
            if not meta.get("split"):bases.append(apk)
        if len(bases)!=1 or trusted.sha256_file(bases[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("NAV29_SIGNED_ORIGINAL_BASE")
        fields=derive_fields(splits)
    names=("HOLDER_WRAPPER_FIELD_NAME","WRAPPER_PERIOD_FIELD_NAME",
           "PERIOD_SOURCE_FIELD_NAME","WRAPPER_ADAPTERS_FIELD_NAME",
           "ADAPTER_CHILD_STREAM_FIELD_NAME")
    src="package pro.celikom.a1exitwitness;\n"
    src+="final class PrivateNativeActivePeriodTarget {\n"
    for key,value in zip(names,fields):
        src+="  static final String "+key+" = "+json.dumps(value,ensure_ascii=True)+";\n"
    src+="  private PrivateNativeActivePeriodTarget() {}\n}\n"
    args.private_java.parent.mkdir(parents=True,exist_ok=True)
    args.private_java.write_text(src,encoding="utf-8")
    print("NAV31_PUBLISHER_SIGNED_PERIOD_TO_CHILD_STREAM_ADAPTER_FIELDS_PASS")

if __name__=="__main__":
    main()
