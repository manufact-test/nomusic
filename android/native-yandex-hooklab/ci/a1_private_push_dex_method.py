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
            # Large vendor strings (e.g. embedded JSON) are irrelevant to the
            # short AppMetrica exception and Dex method/class descriptors.
            # Skip without reading or disclosing them, not a malformed DEX.
            if end<0:
                self.str_cache[index]=""
                return ""
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

    def method_returns_boolean(self,index):
        if index<0 or index>=self.method_count:raise DexError("METHOD_INDEX")
        _,proto,_=struct.unpack_from("<HHI",self.data,self.method_off+index*8)
        count,off=struct.unpack_from("<II",self.data,72)
        if proto>=count or off+count*12>len(self.data):
            raise DexError("PROTO_BOUND")
        result=struct.unpack_from("<I",self.data,off+proto*12+4)[0]
        return self.type(result)=="Z"

    def method_signature(self,index):
        if index<0 or index>=self.method_count:raise DexError("METHOD_INDEX")
        ci,proto,si=struct.unpack_from("<HHI",self.data,self.method_off+index*8)
        return self.type(ci),self.string(si),proto

    def push_interface_implementors(self):
        result={}
        for index in range(self.class_count):
            base=self.class_off+index*32
            cls_index=struct.unpack_from("<I",self.data,base)[0]
            iface_off=struct.unpack_from("<I",self.data,base+12)[0]
            if not iface_off:continue
            owner=self.type(cls_index)
            if group_class(owner) not in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
                continue
            if iface_off+4>len(self.data):raise DexError("INTERFACE_HEADER_BOUND")
            count=struct.unpack_from("<I",self.data,iface_off)[0]
            if count>1024 or iface_off+4+count*2>len(self.data):
                raise DexError("INTERFACE_ARRAY_BOUND")
            for i in range(count):
                tidx=struct.unpack_from("<H",self.data,iface_off+4+2*i)[0]
                interface=self.type(tidx)
                if group_class(interface) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
                    result.setdefault(interface,set()).add(owner)
        return result

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
    if owner.startswith("Lcom/yandex/metrica/push/utils/"):return "PUSH_UTILS"
    if owner.startswith("Lcom/yandex/metrica/push/common/"):return "PUSH_COMMON"
    if owner.startswith("Lcom/yandex/metrica/push/"):return "PUSH_OTHER_HELPER"
    if owner.startswith("Lio/appmetrica/analytics/"):return "MODERN_OTHER"
    if owner.startswith("Ljava/") or owner.startswith("Ljavax/"):return "JAVA_RUNTIME"
    if owner.startswith("Landroid/"):return "ANDROID_FRAMEWORK"
    if owner.startswith("Lkotlin/") or owner.startswith("Lkotlinx/"):return "KOTLIN_RUNTIME"
    if owner.startswith("Lru/yandex/music/"):return "MUSIC_HOST"
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


def helper_chain(dex, source_codes, seeds, interface_impls=None, method_impls=None):
    """Follow up to three direct Push helper invocations using fixed enums."""
    chain=[]
    visited=set()
    frontier=set(seeds)
    interface_impls=interface_impls or {}
    method_impls=method_impls or {}
    for _ in range(3):
        ids=set()
        dispatch=False
        for idx in sorted(frontier)[:128]:
            if idx in source_codes:
                ids.add(idx)
                continue
            # A method-id may refer to an abstract Push interface method.
            # Resolve known concrete implementors in the SAME DEX only.
            owner,name,proto=dex.method_signature(idx)
            for impl_class in sorted(interface_impls.get(owner,()))[:64]:
                target=method_impls.get((impl_class,name,proto))
                if target is not None and target in source_codes:
                    ids.add(target)
                    dispatch=True
        ids=set(sorted(ids - visited)[:128])
        visited.update(ids)
        modern=False
        legacy=False
        nested=set()
        for idx in ids:
            _,calls=code_candidates(source_codes[idx],set())
            for _,ref in calls:
                if ref>=dex.method_count:continue
                owner,name=dex.method(ref)
                cat=group_call(owner,name)
                if cat=="MODERN_PREDICATE":modern=True
                if cat=="LEGACY_PREDICATE":legacy=True
                if cat=="PUSH_IMPL_HELPER":nested.add(ref)
        chain.append({"methods_found":min(len(ids),32),
                      "interface_dispatch_resolved":dispatch,
                      "modern_predicate":modern,
                      "legacy_predicate":legacy,
                      "helper_continuation":bool(nested)})
        frontier=nested
    return chain

def branch_guard_near_target(code,invoke_positions,target_pos):
    """Approximate if-zero control-flow guard between helper call and error."""
    previous=[p for p in invoke_positions if 0<=target_pos-p<=256]
    if not previous:return {"near_helper":False,"if_guard":False}
    start=max(previous)
    guard=any(code[pos] in range(0x32,0x3e)
              for pos in range(start+2,target_pos,2) if pos<len(code))
    return {"near_helper":True,"if_guard":guard}

def forward_skip_guard_category(code, const_pos, invokes, dex):
    """Sanitized approximate IF branch crossing the exact exception string."""
    candidates=[]
    for pos in range(max(0,const_pos-1024),const_pos,2):
        if pos+3>=len(code):continue
        opcode=code[pos]
        if not 0x32<=opcode<=0x3d:continue
        offset=struct.unpack_from("<h",code,pos+2)[0]
        destination=pos+2*offset
        if not (pos<const_pos<destination<=len(code)):continue
        prior=[(p,ref) for p,ref in invokes
               if pos-120<=p<pos and ref<dex.method_count]
        if not prior:
            candidates.append("GUARD_WITHOUT_NEAR_CALL")
        else:
            owner,name=dex.method(prior[-1][1])
            candidates.append(group_call(owner,name))
    return candidates[-1] if candidates else "NO_FORWARD_GUARD"

def inspect_dex(binary):
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return []
    matches=[]
    source_codes={}
    impl_signatures={}
    interface_implementors=dex.push_interface_implementors()
    for mid,code in dex.code_methods():
        owner,method=dex.method(mid)
        if group_class(owner) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
            if len(source_codes)<25000:
                source_codes[mid]=code
                impl_signatures[dex.method_signature(mid)]=mid
        where,calls=code_candidates(code,targets)
        if not where:continue
        grouped=[]
        for pos,ref in calls:
            if ref<dex.method_count:
                callee,name=dex.method(ref)
                grouped.append((pos,group_call(callee,name)))
        helpers=set()
        helper_call_positions=[]
        for call_pos,ref in calls:
            if ref<dex.method_count:
                callee,name=dex.method(ref)
                if group_call(callee,name)=="PUSH_IMPL_HELPER":
                    helpers.add(ref)
                    helper_call_positions.append(call_pos)
        for pos in where:
            earlier=[x[1] for x in grouped if pos-120<=x[0]<pos]
            matches.append({
                "owner":group_class(owner),
                "obfuscated_a":method=="a",
                "modern_check":any(x[1]=="MODERN_PREDICATE" for x in grouped),
                "legacy_check":any(x[1]=="LEGACY_PREDICATE" for x in grouped),
                "helper":any(x[1]=="PUSH_IMPL_HELPER" for x in grouped),
                "recent_invoke":earlier[-1] if earlier else "NO_NEARBY_INVOKE",
                "guard":branch_guard_near_target(code,helper_call_positions,pos),
                "forward_guard_category":forward_skip_guard_category(code,pos,calls,dex),
                "helper_refs":helpers,
            })
    # Resolve helper implementations after all declarations have been indexed.
    for entry in matches:
        entry["helper_chain"]=(
            helper_chain(dex,source_codes,entry["helper_refs"],
                         interface_implementors,impl_signatures)
            if entry["owner"]=="PUSH_IMPL" else [])
        del entry["helper_refs"]
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
    fatal_a=[m for m in exact if m["obfuscated_a"]]
    return {
        "push_impl_crash_a_candidates_bounded":min(len(fatal_a),16),
        "push_impl_a_has_nearby_helper":any(m["guard"]["near_helper"] for m in fatal_a),
        "push_impl_a_has_guard_after_helper_approx":any(m["guard"]["if_guard"] for m in fatal_a),
        "push_impl_a_skip_throw_guard_call_categories":
            sorted({m["forward_guard_category"] for m in fatal_a}),
        "push_impl_a_modern_predicate_by_depth":[
            any(m["helper_chain"][level]["modern_predicate"]
                for m in fatal_a if len(m["helper_chain"])>level)
            for level in range(3)],
        "push_impl_a_interface_dispatch_by_depth":[
            any(m["helper_chain"][level]["interface_dispatch_resolved"]
                for m in fatal_a if len(m["helper_chain"])>level)
            for level in range(3)],
        "dex_private_push_insight":True,
        "push_helper_interface_dispatch_by_depth":[
            any(m["helper_chain"][depth]["interface_dispatch_resolved"]
                for m in exact if len(m["helper_chain"])>depth)
            for depth in range(3)],
        "push_helper_methods_by_depth_bounded":[
            min(sum(m["helper_chain"][depth]["methods_found"]
                    for m in exact if len(m["helper_chain"])>depth),64)
            for depth in range(3)],
        "push_helper_modern_predicate_by_depth":[
            any(m["helper_chain"][depth]["modern_predicate"]
                for m in exact if len(m["helper_chain"])>depth)
            for depth in range(3)],
        "push_helper_legacy_predicate_by_depth":[
            any(m["helper_chain"][depth]["legacy_predicate"]
                for m in exact if len(m["helper_chain"])>depth)
            for depth in range(3)],
        "push_helper_continuation_by_depth":[
            any(m["helper_chain"][depth]["helper_continuation"]
                for m in exact if len(m["helper_chain"])>depth)
            for depth in range(3)],
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


def private_boolean_helpers(binary):
    """Private in-process class+method targets, never put into public logs."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return set()
    source_codes={}
    declarations={}
    roots=set()
    for mid,code in dex.code_methods():
        owner,method=dex.method(mid)
        if group_class(owner) in ("PUSH_IMPL","PUSH_OTHER"):
            if len(source_codes)<25000:
                source_codes[mid]=code
                declarations[dex.method_signature(mid)]=mid
        if group_class(owner)=="PUSH_IMPL" and method=="a":
            where,calls=code_candidates(code,targets)
            if where:
                for _,ref in calls:
                    if ref<dex.method_count:
                        callee,name=dex.method(ref)
                        if group_call(callee,name)=="PUSH_IMPL_HELPER":
                            roots.add(ref)
    interfaces=dex.push_interface_implementors()
    frontier=roots
    visited=set()
    output=set()
    for _ in range(4):
        following=set()
        for ref in sorted(frontier)[:128]:
            if ref in visited:continue
            visited.add(ref)
            owner,name,proto=dex.method_signature(ref)
            implementations=[ref] if ref in source_codes else [
                declarations.get((cls,name,proto))
                for cls in sorted(interfaces.get(owner,()))[:64]]
            for actual in implementations:
                if actual is None or actual not in source_codes:continue
                cl,method=dex.method(actual)
                if group_class(cl)=="PUSH_IMPL" and dex.method_returns_boolean(actual):
                    java_name=cl.strip("L;").replace("/",".")
                    output.add((java_name,method))
                _,calls=code_candidates(source_codes[actual],set())
                for _,next_ref in calls:
                    if next_ref<dex.method_count:
                        called,name=dex.method(next_ref)
                        if group_call(called,name)=="PUSH_IMPL_HELPER":
                            following.add(next_ref)
        frontier=following
    return output

def generate_private_targets(source, output_path):
    """Write transient proprietary method symbols only inside ephemeral CI."""
    import re
    target=Path(output_path).resolve()
    workspace=Path(os.environ.get("GITHUB_WORKSPACE","/nonexistent")).resolve()
    temp=Path(os.environ.get("RUNNER_TEMP","/nonexistent")).resolve()
    if (target.name!="PrivatePushTargets.java" or
        not (str(target).startswith(str(workspace)+os.sep) or
             str(target).startswith(str(temp)+os.sep))):
        raise DexError("PRIVATE_TARGET_PATH")
    found=set()
    with zipfile.ZipFile(source) as outer:
        for item in outer.infolist():
            if not item.filename.endswith(".apk") or item.file_size>60000000:continue
            with zipfile.ZipFile(io.BytesIO(outer.read(item))) as part:
                for name in part.namelist():
                    if name.startswith("classes") and name.endswith(".dex"):
                        payload=part.read(name)
                        if payload.startswith(b"dex\\n".replace(b"\\\\",b"\\")):
                            found.update(private_boolean_helpers(payload))
    # Verify source-derived class/method tokens before use as Java literals.
    valid=re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)*$")
    simple=re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
    names=sorted((cls,method) for cls,method in found
                 if valid.fullmatch(cls) and simple.fullmatch(method))[:24]
    if not names:raise DexError("PRIVATE_TARGETS_EMPTY")
    target.parent.mkdir(parents=True,exist_ok=True)
    pairs=",\\n".join("        {"+json.dumps(cls)+","+json.dumps(method)+"}"
                     for cls,method in names)
    generated=("package pro.celikom.a1exitwitness;\\n"+
               "public final class PrivatePushTargets {\\n"+
               "  public static String[][] getTargets() { return new String[][] {\\n"+
               pairs+"\\n  }; }\\n}\\n")
    target.write_text(generated,encoding="utf-8")
    target.chmod(0o600)
    return min(len(names),24)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    parser.add_argument("--private-java",type=Path)
    args=parser.parse_args()
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!="experiment/android-a1-metrica-init-state-observer-arm13-20261112"):
        raise DexError("PRIVATE_CI_ONLY")
    try:
        result=inspect_xapk(args.xapk)
        if args.private_java is not None:
            result["private_transient_boolean_targets_bounded"]=generate_private_targets(
                args.xapk,args.private_java)
            result["raw_target_names_logged"]=False
        print(json.dumps(result,sort_keys=True))
    except (DexError,zipfile.BadZipFile,ValueError,OSError) as error:
        # Never print caught exception contents unless it is an own fixed enum.
        safe={"ULEB_BAD","ULEB_TOO_LONG","DEX_MAGIC","DEX_TABLE_BOUND",
              "STR_INDEX","STR_END","TYPE_INDEX","METHOD_INDEX",
              "EXCESSIVE_METHODS","CODE_HEADER_BOUND","CODE_BOUND",
              "OWNER_INPUT_LENGTH","OWNER_INPUT_SHA",
              "INTERFACE_HEADER_BOUND","INTERFACE_ARRAY_BOUND","PROTO_BOUND",
              "PRIVATE_TARGET_PATH","PRIVATE_TARGETS_EMPTY"}
        reason=(str(error) if isinstance(error,DexError)
                and str(error) in safe else
                "ZIP_READ" if isinstance(error,zipfile.BadZipFile) else
                "UNEXPECTED_STRUCTURE")
        print(json.dumps({"dex_private_push_insight":False,
                          "private_scan_failed_without_data_disclosure":True,
                          "failure_family":reason},sort_keys=True))
        raise SystemExit(1)

if __name__=="__main__":main()
