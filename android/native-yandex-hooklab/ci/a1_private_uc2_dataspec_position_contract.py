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
                    if method[0]==RETRY and method[2]=="(LUC2;)J":
                        if len(source_open)>=2:raise ValueError("ORIGINAL_OPEN_AMBIGUOUS")
                        source_open.append((method[1],len(list(audit.instructions(dex,code)))))
    if count!=6:raise ValueError("SIGNED_SIX_DEX_REQUIRED")
    longs=[name for kind,name,ftype in found if kind=="instance" and ftype=="J"]
    return {
        "target":"SIGNED_ORIGINAL_MEDIA3_DATASPEC_UC2",
        "class_present":bool(found),
        "original_datasource_open_exact_signature_count":len(source_open),
        "original_datasource_open_method_shape_only":
            [{"declared_method":name,"instruction_count":ins} for name,ins in source_open],
        "dataspec_instance_long_field_names":longs,
        "exact_public_position_field_present":"position" in longs,
        "byte_offset_field_semantically_attested":False,
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
