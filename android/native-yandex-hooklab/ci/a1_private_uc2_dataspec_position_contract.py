#!/usr/bin/env python3
"""Exact original 2025 UC2 DataSpec byte-offset field check for native Exo I/O.

Interoperability only. This is one class and the exact established original
RetryingBalancingDataSource.if(UC2) entrypoint, not a whole-APK semantic scan.
Never opens a network connection or reads media, credentials or user values.
"""
import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import lft2_class_inspection as trusted
from trace_native_callers import uleb

audit=trusted.audit
DATASPEC="LUC2;"
RETRY="Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource;"

def fields_for(dex,ci):
    base=dex.class_offset+32*ci
    data=dex.u32(base+24)
    if not data:return []
    stat,data=uleb(dex,data)
    inst,data=uleb(dex,data)
    direct,data=uleb(dex,data)
    virtual,data=uleb(dex,data)
    if max(stat,inst,direct,virtual)>500:
        raise ValueError("DATASPEC_CLASS_LIMIT")
    result=[]
    for kind,count in (("static",stat),("instance",inst)):
        field=0
        for _ in range(count):
            delta,data=uleb(dex,data)
            _flags,data=uleb(dex,data)
            field+=delta
            owner,name,ftype=audit.field_id(dex,field)
            if owner!=DATASPEC:raise ValueError("FOREIGN_DATASPEC_FIELD")
            if not re.fullmatch(r"[A-Za-z0-9_$]{1,120}",name):
                raise ValueError("INVALID_CLASS_FIELD_SYMBOL")
            result.append((kind,name,ftype))
    return result

def scan(splits):
    found=[]
    source_open=[]
    dataspec_method_wide_reads=[]
    count=0
    for apk in splits:
        with zipfile.ZipFile(apk) as z:
            for member in z.infolist():
                if not re.fullmatch(r"classes\d*\.dex",member.filename):
                    continue
                count+=1
                dex=audit.Dex(z.read(member.filename))
                for ci in range(dex.class_count):
                    owner=dex.descriptor(dex.u32(dex.class_offset+32*ci))
                    if owner==DATASPEC:
                        if found:raise ValueError("DATASPEC_CLASS_DUPLICATE")
                        found=fields_for(dex,ci)
                for method,flags,code in audit.method_definitions_with_flags(dex):
                    if method[0]==DATASPEC:
                        if len(dataspec_method_wide_reads)>40:
                            raise ValueError("DATASPEC_WIDE_METHOD_LIMIT")
                        reads=[]
                        writes=[]
                        for pc,op,words in audit.instructions(dex,code):
                            if op not in (0x53,0x5a):
                                continue
                            owner,name,ftype=audit.field_id(dex,words[1])
                            if owner!=DATASPEC or ftype!="J":continue
                            if op==0x53:reads.append(name)
                            else:writes.append(name)
                        if reads or writes:
                            dataspec_method_wide_reads.append({
                                "declared_method":method[1],
                                "signature":method[2],
                                "iget_wide_order":reads[:24],
                                "iput_wide_order":writes[:24],
                            })
                    if method[0]==RETRY and method[2]=="(LUC2;)J":
                        if len(source_open)>=2:raise ValueError("ORIGINAL_OPEN_AMBIGUOUS")
                        source_open.append((method[1],len(list(audit.instructions(dex,code)))))
    if count!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    longs=[name for kind,name,ftype in found if kind=="instance" and ftype=="J"]
    method_roles={(m["declared_method"],m["signature"]):m
                  for m in dataspec_method_wide_reads}
    constructor=method_roles.get(("<init>",
        "(Landroid/net/Uri;JI[BLjava/util/Map;JJLjava/lang/String;I)V"))
    to_string=method_roles.get(("toString","()Ljava/lang/String;"))
    subrange=method_roles.get(("case","(JJ)LUC2;"))
    remainder=method_roles.get(("try","(J)LUC2;"))
    verified=(
        len(found)>0 and sorted(longs)==["else","for","goto"]
        and constructor is not None
        and constructor["iput_wide_order"]==["for","else","goto"]
        and to_string is not None
        and to_string["iget_wide_order"]==["else","goto"]
        and subrange is not None
        and subrange["iget_wide_order"]==["goto","else","for"]
        and remainder is not None
        and remainder["iget_wide_order"]==["goto"]
        and len(source_open)==2
    )
    return {
        "position_field_exact_original_2025":"else" if verified else None,
        "length_field_exact_original_2025":"goto" if verified else None,
        "uri_offset_field_exact_original_2025":"for" if verified else None,
        "dataspec_position_verdict":("PINNED_ORIGINAL_UC2_POSITION_CONFIRMED"
             if verified else "FAIL_CLOSED_OFFSET_NOT_PROVEN"),
        "target":"SIGNED_ORIGINAL_MEDIA3_DATASPEC_UC2",
        "class_present":bool(found),
        "original_datasource_open_exact_signature_count":len(source_open),
        "original_datasource_open_method_shape_only":
            [{"declared_method":name,"instruction_count":ins} for name,ins in source_open],
        "dataspec_instance_long_field_names":longs,
        "dataspec_exact_method_wide_field_use":dataspec_method_wide_reads,
        "exact_public_position_field_present":"position" in longs,
        "byte_offset_field_semantically_attested":verified,
        "native_byte_route_installed":False,
    }

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true" or os.environ.get("GITHUB_REPOSITORY")!="manufact-test/nomusic":
        raise RuntimeError("SOURCE_POSITION_CHECK_CI_ONLY")
    if xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES or trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("PINNED_SIGNATURE_INPUT_DRIFT")
    with tempfile.TemporaryDirectory(prefix="celikom-dataspec-") as temp:
        splits=audit.unbundle_candidate(xapk,Path(temp))
        if len(splits)!=16 or audit.verify_split_set(splits).get("verified_issuer_signed_splits")!=16:
            raise ValueError("SIGNED_XAPK_SIXTEEN_SPLITS_REQUIRED")
        return scan(splits)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.xapk),sort_keys=True))
