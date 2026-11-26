#!/usr/bin/env python3
"""Read-only signed 2025 source/factory field graph. Fixed finite enums only.

No third-party names, paths, raw DEX, audio, URLs, track IDs or signed assets
may be printed. No source binding is authorised by this static inventory.
"""
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
INNER = "Lcom/yandex/music/shared/player/download2/exo/RetryingBalancingDataSource$b;"
FACTORY_PARAMS=("LdA9;", "LQAa;", "Lmu3;", "LgA9;")

def proto(dex,index):
    n,off=struct.unpack_from("<II",dex.data,72)
    if not 0<=index<n<=100000: raise ValueError("PROTO_BAD")
    at=off+index*12
    ret=dex.type(struct.unpack_from("<I",dex.data,at+4)[0])
    args=struct.unpack_from("<I",dex.data,at+8)[0]
    if not args:return ret,()
    count=struct.unpack_from("<I",dex.data,args)[0]
    if count>64:return ret,()
    return ret,tuple(dex.type(struct.unpack_from("<H",dex.data,args+4+i*2)[0]) for i in range(count))

def type_category(t):
    if t==SOURCE:return "SOURCE"
    if t==INNER:return "INNER"
    if t in ("LQAa;","LQBa;"):return "SIGNED_DESCRIPTOR_CLASS"
    if t.startswith("Landroidx/media3/"):return "MEDIA3"
    if t.startswith("Lcom/google/android/exoplayer2/"):return "LEGACY_EXO"
    if t.startswith("Lcom/yandex/music/shared/player/download2/exo/"):return "SIGNED_EXO"
    if t.startswith("Lcom/yandex/music/shared/player/download2/"):return "SIGNED_DOWNLOAD"
    if t.startswith("Landroid/"):return "ANDROID"
    if t.startswith("Ljava/"):return "JAVA"
    if re.fullmatch(r"L[A-Za-z0-9_$]{1,30};",t):return "OBFUSCATED_ROOT"
    if t.startswith("Lkotlin/"):return "KOTLIN"
    return "OTHER"

def inspect(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=EXPECTED_LEN:
        raise ValueError("XAPK_SIZE")
    with path.open("rb") as f:
        if hashlib.file_digest(f,"sha256").hexdigest()!=EXPECTED_SHA:
            raise ValueError("XAPK_SHA")
    records=[]
    with zipfile.ZipFile(path) as xapk:
        for part in xapk.infolist():
            if not part.filename.endswith(".apk") or part.file_size>60_000_000:continue
            with zipfile.ZipFile(io.BytesIO(xapk.read(part))) as apk:
                for name in apk.namelist():
                    if re.fullmatch(r"classes[0-9]*\\.dex",name):
                        info=apk.getinfo(name)
                        if info.file_size<=25_000_000:records.append(Dex(apk.read(info)))
    if len(records)!=6:raise ValueError("DEX_COUNT")
    outer=set();inner=set()
    fields={}
    relations={}
    for dex in records:
        classes=dex.class_count
        for i in range(classes):
            off=dex.class_off+i*32
            ti,flags,superidx,ifaceoff=struct.unpack_from("<IIII",dex.data,off)
            owner=dex.type(ti)
            ancestors=relations.setdefault(owner,set())
            if superidx!=0xffffffff:ancestors.add(dex.type(superidx))
            if ifaceoff:
                count=struct.unpack_from("<I",dex.data,ifaceoff)[0]
                if count>256:raise ValueError("IFACE_BOUND")
                for j in range(count):
                    ancestors.add(dex.type(struct.unpack_from("<H",dex.data,ifaceoff+4+j*2)[0]))
        fcount,foff=struct.unpack_from("<II",dex.data,80)
        if fcount>500000:raise ValueError("FIELDS_BOUND")
        for i in range(fcount):
            owner_idx,type_idx,_=struct.unpack_from("<HHI",dex.data,foff+i*8)
            fields.setdefault(dex.type(owner_idx),set()).add(dex.type(type_idx))
        for mid in range(dex.method_count):
            owner,name,pi=dex.method_signature(mid)
            if name!="for" or owner not in (OWNER,INNER):continue
            ret,args=proto(dex,pi)
            if owner==OWNER and args==FACTORY_PARAMS:outer.add(ret)
            if owner==INNER and not args:inner.add(ret)
    if len(outer)!=1 or len(inner)!=1:raise ValueError("SIGNED_METHOD_RETURN_DRIFT")
    outer_type=next(iter(outer));inner_type=next(iter(inner))
    def is_parent(parent,child):
        frontier=[child]
        seen=set()
        for _ in range(8):
            newer=[]
            for obj in frontier:
                if obj==parent:return True
                if obj in seen:continue
                seen.add(obj)
                newer.extend(relations.get(obj,()))
            frontier=newer
        return False
    counts=[]
    frontier={outer_type}
    seen={outer_type}
    for depth in range(1,5):
        nxt=set()
        for owner in frontier:
            nxt.update(x for x in fields.get(owner,()) if x.startswith("L"))
        counts.append({
           "depth":depth,
           "unique_field_types_bounded":min(len(nxt),32),
           "contains_inner":INNER in nxt,
           "contains_source":SOURCE in nxt,
           "contains_inner_supertype":any(
               x!= "Ljava/lang/Object;" and is_parent(x,INNER) for x in nxt),
        })
        frontier=nxt-seen
        seen.update(nxt)
        if len(seen)>512:break
    return {
       "source_verified":True,
       "outer_result_category":type_category(outer_type),
       "inner_product_declared_category":type_category(inner_type),
       "inner_product_assignable_from_source":is_parent(inner_type,SOURCE),
       "outer_result_assignable_from_inner":is_parent(outer_type,INNER),
       "outer_result_assignable_from_source":is_parent(outer_type,SOURCE),
       "outer_result_field_graph":counts,
       "outer_result_known_original_descriptor":outer_type in ("LQAa;","LQBa;"),
       "inner_product_is_object":inner_type=="Ljava/lang/Object;",
       "signed_dex_static_only_not_runtime_identity_or_audio":True,
       "private_vendor_names_disclosed":False,
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    a=p.parse_args()
    print("A1_PRIVATE_EXO_FACTORY_GRAPH "+json.dumps(inspect(a.xapk),sort_keys=True))
