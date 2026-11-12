#!/usr/bin/env python3
"""Read-only exact publisher XAPK DEX triage; output is ONLY fixed enums and counts.

Run only on an ephemeral GitHub ARM CI runner. No raw vendor source, APK,
strings, symbols, credentials, signatures or paths are ever printed.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import zipfile

EXPECTED_LEN=45961661
EXPECTED_SHA="8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"

class DexError(Exception): pass

def uleb(data, pos):
    value=0
    for i in range(5):
        if pos>=len(data): raise DexError("ULEB_BAD")
        b=data[pos]; pos+=1; value|=(b&127)<<(i*7)
        if not b&128: return value,pos
    raise DexError("ULEB_TOO_LONG")

class Dex:
    def __init__(self,data):
        if len(data)<112 or data[:4]!=b"dex\n" or data[7]!=0:
            raise DexError("DEX_MAGIC")
        self.data=data
        self.string_count,self.string_off=struct.unpack_from("<II",data,56)
        self.type_count,self.type_off=struct.unpack_from("<II",data,64)
        self.method_count,self.method_off=struct.unpack_from("<II",data,88)
        self.class_count,self.class_off=struct.unpack_from("<II",data,96)
        for size,off,width in ((self.string_count,self.string_off,4),
                               (self.type_count,self.type_off,4),
                               (self.method_count,self.method_off,8),
                               (self.class_count,self.class_off,32)):
            if size>500000 or off+size*width>len(data):
                raise DexError("DEX_TABLE_BOUND")
        self.str_cache={};self.type_cache={};self.method_cache={}

    def string(self,index):
        if index<0 or index>=self.string_count:raise DexError("STR_INDEX")
        if index not in self.str_cache:
            off=struct.unpack_from("<I",self.data,self.string_off+index*4)[0]
            _,start=uleb(self.data,off)
            end=self.data.find(b"\0",start,min(len(self.data),start+4096))
            if end<0: raise DexError("STR_END")
            self.str_cache[index]=self.data[start:end].decode("utf-8","replace")
        return self.str_cache[index]

    def type(self,index):
        if index<0 or index>=self.type_count:raise DexError("TYPE_INDEX")
        if index not in self.type_cache:
            s=struct.unpack_from("<I",self.data,self.type_off+index*4)[0]
            self.type_cache[index]=self.string(s)
        return self.type_cache[index]

    def method(self,index):
        if index<0 or index>=self.method_count:raise DexError("METHOD_INDEX")
        if index not in self.method_cache:
            ci,_,si=struct.unpack_from("<HHI",self.data,self.method_off+index*8)
            self.method_cache[index]=(self.type(ci),self.string(si))
        return self.method_cache[index]

    def possible_error_strings(self):
        found=set()
        for i in range(self.string_count):
            value=self.string(i).lower()
            if "appmetrica" in value and "initialized" in value:
                found.add(i)
        return found

    def code_methods(self):
        data=self.data
        for i in range(self.class_count):
            item=self.class_off+i*32
            at=struct.unpack_from("<I",data,item+24)[0]
            if at==0:continue
            static,at=uleb(data,at)
            fields,at=uleb(data,at)
            direct,at=uleb(data,at)
            virtual,at=uleb(data,at)
            if static+fields+direct+virtual>100000:
                raise DexError("EXCESSIVE_METHODS")
            for _ in range(static+fields):
                _,at=uleb(data,at);_,at=uleb(data,at)
            for count in (direct,virtual):
                index=0
                for _ in range(count):
                    step,at=uleb(data,at);index+=step
                    _,at=uleb(data,at)
                    off,at=uleb(data,at)
                    if off==0:continue
                    if off+16>len(data):raise DexError("CODE_HEADER_BOUND")
                    size=struct.unpack_from("<I",data,off+12)[0]
                    if size>200000 or off+16+size*2>len(data):
                        raise DexError("CODE_BOUND")
                    yield index,data[off+16:off+16+size*2]

def group_class(desc):
    if desc.startswith("Lcom/yandex/metrica/push/impl/"):return "PUSH_IMPL"
    if desc.startswith("Lcom/yandex/metrica/push/"):return "PUSH_OTHER"
    if desc.startswith("Lio/appmetrica/analytics/push/"):return "PUSH_MODERN"
    return "OTHER"

def group_call(owner,name):
    if owner=="Lio/appmetrica/analytics/ModulesFacade;" and name=="isActivatedForApp":
        return "MODERN_PREDICATE"
    if owner=="Lcom/yandex/metrica/ModulesFacade;" and name=="isActivatedForApp":
        return "LEGACY_PREDICATE"
    if owner.startswith("Lcom/yandex/metrica/push/impl/"):return "PUSH_IMPL_HELPER"
    if owner.startswith("Lio/appmetrica/analytics/"):return "MODERN_OTHER"
    return "OTHER"

def code_candidates(code,targets):
    # Code-unit scan: may see operands, results are conservative, not full CFG proof.
    strings=[];invokes=[]
    for pos in range(0,len(code)-3,2):
        op=code[pos]
        if op==0x1a and struct.unpack_from("<H",code,pos+2)[0] in targets:
            strings.append(pos)
        elif op==0x1b and pos+5<len(code) and struct.unpack_from("<I",code,pos+2)[0] in targets:
            strings.append(pos)
        if op in tuple(range(0x6e,0x73))+tuple(range(0x74,0x79))+(0xfa,0xfb):
            invokes.append((pos,struct.unpack_from("<H",code,pos+2)[0]))
    return strings,invokes

def inspect_dex(binary):
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return []
    matches=[]
    for mid,code in dex.code_methods():
        where,calls=code_candidates(code,targets)
        if not where:continue
        owner,method=dex.method(mid)
        grouped=[]
        for pos,ref in calls:
            if ref<dex.method_count:
                callee,name=dex.method(ref)
                grouped.append((pos,group_call(callee,name)))
        for pos in where:
            earlier=[x[1] for x in grouped if pos-120<=x[0]<pos]
            matches.append({
                "owner":group_class(owner),
                "obfuscated_a":method=="a",
                "modern_check":any(x[1]=="MODERN_PREDICATE" for x in grouped),
                "legacy_check":any(x[1]=="LEGACY_PREDICATE" for x in grouped),
                "helper":any(x[1]=="PUSH_IMPL_HELPER" for x in grouped),
                "recent_invoke":earlier[-1] if earlier else "NO_NEARBY_INVOKE",
            })
    return matches

def inspect_xapk(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size!=EXPECTED_LEN:
        raise DexError("OWNER_INPUT_LENGTH")
    with path.open("rb") as file:
        if hashlib.file_digest(file,"sha256").hexdigest()!=EXPECTED_SHA:
            raise DexError("OWNER_INPUT_SHA")
    seen=0;matches=[]
    with zipfile.ZipFile(path) as outer:
        for part in outer.infolist():
            if not part.filename.endswith(".apk") or part.file_size>60_000_000:
                continue
            with zipfile.ZipFile(io.BytesIO(outer.read(part))) as apk:
                for name in apk.namelist():
                    if not name.startswith("classes") or not name.endswith(".dex"):
                        continue
                    payload=apk.read(name);seen+=1
                    if payload.startswith(b"dex\n"):
                        matches.extend(inspect_dex(payload))
    exact=[m for m in matches if m["owner"]=="PUSH_IMPL"]
    return {
        "dex_private_push_insight":True,
        "dex_scanned_bounded":min(seen,99),
        "error_text_methods_bounded":min(len(matches),99),
        "push_impl_error_methods_bounded":min(len(exact),32),
        "push_impl_obfuscated_a_found":any(x["obfuscated_a"] for x in exact),
        "push_impl_direct_modern_predicate":any(x["modern_check"] for x in exact),
        "push_impl_direct_legacy_predicate":any(x["legacy_check"] for x in exact),
        "push_impl_calls_helper":any(x["helper"] for x in exact),
        "nearest_push_impl_call_categories":sorted(set(x["recent_invoke"] for x in exact)),
        "codeunit_scan_is_approximate":True,
        "original_or_owned_apk_published":False,
        "vendor_symbols_or_raw_strings_published":False,
        "credentials_published":False,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    args=parser.parse_args()
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!="experiment/android-a1-metrica-init-state-observer-arm13-20261112"):
        raise DexError("PRIVATE_CI_ONLY")
    try:
        print(json.dumps(inspect_xapk(args.xapk),sort_keys=True))
    except (DexError,zipfile.BadZipFile,ValueError,OSError):
        print('{"dex_private_push_insight":false,"private_scan_failed_without_data_disclosure":true}')
        raise SystemExit(1)

if __name__=="__main__":main()
