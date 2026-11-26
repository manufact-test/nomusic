#!/usr/bin/env python3
"""Read-only pinned 2025 signed Exo factory graph triage, fixed enums only.

Never print proprietary DEX symbols, methods, field names, bytes, original
packages, paths, URLs, identifiers or signing details. No runtime binding claim.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path
from a1_private_push_dex_method import Dex, EXPECTED_LEN, EXPECTED_SHA

OWNER = "Lcom/yandex/music/shared/player/download2/exo/c;"
SOURCE = "Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource;"
INNER_FACTORY = "Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource$b;"
FACTORY_PARAMS = ("LdA9;", "LQAa;", "Lmu3;", "LgA9;")
PUBLIC_SOURCE_CONTRACTS = {
    "Landroidx/media3/datasource/DataSource;",
    "Lcom/google/android/exoplayer2/upstream/DataSource;",
}
PUBLIC_FACTORY_CONTRACTS = {
    "Landroidx/media3/datasource/DataSource$Factory;",
    "Lcom/google/android/exoplayer2/upstream/DataSource$Factory;",
}

def bounded(n):
    return min(n,16)

def prototype(dex, proto):
    count,offset = struct.unpack_from("<II",dex.data,72)
    if not 0 <= proto < count <= 100000 or offset+count*12>len(dex.data):
        raise ValueError("FACTORY_PROTO_BOUND")
    ret = dex.type(struct.unpack_from("<I",dex.data,offset+proto*12+4)[0])
    at = struct.unpack_from("<I",dex.data,offset+proto*12+8)[0]
    if not at: return ret,()
    if at+4>len(dex.data): raise ValueError("FACTORY_PARAMS_BOUND")
    n=struct.unpack_from("<I",dex.data,at)[0]
    if n>64 or at+4+n*2>len(dex.data):
        raise ValueError("FACTORY_PARAMS_BOUND")
    return ret,tuple(dex.type(struct.unpack_from("<H",dex.data,at+4+2*i)[0])
                     for i in range(n))

def return_kind(type_name):
    if type_name==SOURCE:return "SOURCE_CONCRETE"
    if type_name==INNER_FACTORY:return "INNER_SOURCE_FACTORY"
    if type_name in PUBLIC_SOURCE_CONTRACTS:return "PUBLIC_SOURCE_CONTRACT"
    if type_name in PUBLIC_FACTORY_CONTRACTS:return "PUBLIC_FACTORY_CONTRACT"
    if type_name=="Ljava/lang/Object;":return "OBJECT_ERASED"
    if type_name.startswith("Lkotlin/jvm/functions/"):
        return "KOTLIN_FUNCTION"
    if type_name.startswith("Lcom/yandex/music/shared/player/download2/"):
        return "VENDOR_DOWNLOAD_OBJECT"
    return "OTHER"

def inspect(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != EXPECTED_LEN:
        raise ValueError("SIGNED_EXO_XAPK_SIZE")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream,"sha256").hexdigest()!=EXPECTED_SHA:
            raise ValueError("SIGNED_EXO_XAPK_SHA")
    records=[]
    with zipfile.ZipFile(path) as xapk:
        for part in xapk.infolist():
            if not part.filename.endswith(".apk") or part.file_size>60_000_000:
                continue
            with zipfile.ZipFile(io.BytesIO(xapk.read(part))) as apk:
                for name in apk.namelist():
                    if not re.fullmatch(r"classes[0-9]*\\.dex",name):
                        continue
                    info=apk.getinfo(name)
                    if info.file_size>25_000_000:continue
                    records.append(Dex(apk.read(info)))
    if len(records)!=6:raise ValueError("SIGNED_EXO_DEX_COUNT")
    exact=[]
    inner_returns=[]
    for dex in records:
        defined=set(index for index,_ in dex.code_methods())
        for mid in range(dex.method_count):
            owner,name,proto=dex.method_signature(mid)
            if owner not in (OWNER,INNER_FACTORY):continue
            if name not in ("for","<init>"):continue
            ret,params=prototype(dex,proto)
            if owner==OWNER and name=="for" and params==FACTORY_PARAMS:
                exact.append((dex,ret,mid in defined))
            elif owner==INNER_FACTORY and name=="for" and not params:
                inner_returns.append((return_kind(ret),mid in defined))
    definitions={ret for _,ret,has_body in exact if has_body}
    if len(definitions)!=1:
        raise ValueError("SIGNED_EXO_OUTER_FACTORY_DRIFT")
    return_type=next(iter(definitions))
    methods=set()
    fields=set()
    for dex in records:
        for mid in range(dex.method_count):
            owner,name,proto=dex.method_signature(mid)
            if owner!=return_type:continue
            ret,params=prototype(dex,proto)
            methods.add((name,len(params),return_kind(ret)))
        field_count,field_offset=struct.unpack_from("<II",dex.data,80)
        if field_count>500000 or field_offset+field_count*8>len(dex.data):
            raise ValueError("SIGNED_EXO_FIELDS_BOUND")
        for idx in range(field_count):
            obj,typ,_=struct.unpack_from("<HHI",dex.data,field_offset+idx*8)
            if dex.type(obj)==return_type:
                fields.add(dex.type(typ))
    shape = {
      "verified_signed_original":True,
      "exact_outer_factory_declared":True,
      "outer_factory_return_kind":return_kind(return_type),
      "return_is_inner_factory":return_type==INNER_FACTORY,
      "return_is_source":return_type==SOURCE,
      "return_is_media3_factory":return_type in PUBLIC_FACTORY_CONTRACTS,
      "returned_object_zero_arg_source_method_refs":bounded(sum(
          1 for _,argc,ret in methods if argc==0 and ret in
          ("SOURCE_CONCRETE","PUBLIC_SOURCE_CONTRACT"))),
      "returned_object_zero_arg_inner_factory_method_refs":bounded(sum(
          1 for _,argc,ret in methods if argc==0 and ret=="INNER_SOURCE_FACTORY")),
      "returned_object_zero_arg_object_method_refs":bounded(sum(
          1 for _,argc,ret in methods if argc==0 and ret=="OBJECT_ERASED")),
      "returned_object_param_source_method_refs":bounded(sum(
          1 for _,argc,ret in methods if argc>0 and ret in
          ("SOURCE_CONCRETE","PUBLIC_SOURCE_CONTRACT"))),
      "returned_object_inner_factory_field_refs":int(INNER_FACTORY in fields),
      "returned_object_source_field_refs":int(SOURCE in fields),
      "returned_object_private_field_refs":bounded(sum(
          1 for t in fields if t.startswith("Lcom/yandex/music/shared/player/download2/"))),
      "pinned_inner_factory_zero_arg_product_kinds":sorted(set(
          kind for kind,_ in inner_returns)),
      "pinned_inner_factory_defined":any(defined for _,defined in inner_returns),
      "static_shape_not_audio_proof":True,
      "private_names_disclosed":False,
    }
    return shape

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    args=p.parse_args()
    print("A1_PRIVATE_EXO_FACTORY_SHAPE "+json.dumps(inspect(args.xapk),sort_keys=True))
