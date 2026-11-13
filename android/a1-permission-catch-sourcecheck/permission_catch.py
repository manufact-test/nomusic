#!/usr/bin/env python3
"""One source-grounded hypothesis only: is a signature-protected permission
check on the TRUE-normal -> fatal catch route? Private exact 2025 XAPK
inside ephemeral GitHub ARM runner. No APK/DEX/symbols/method IDs output.
Not a generic SDK scanner and not runtime proof.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
import struct
import sys

CI=Path(__file__).resolve().parents[1]/"native-yandex-hooklab"/"ci"
CATCH=Path(__file__).resolve().parents[1]/"a1-exact-catch-helper"
sys.path.insert(0,str(CI))
sys.path.insert(0,str(CATCH))
from a1_private_push_dex_method import (
    Dex, group_class, group_call, private_java_parameter_signature, private_exclusive_fatal_guard_refs,
    private_near_true_exact_throw_path,
)
from a1_private_dex_fatal_cfg import exact_fatal_cfg, _nexts
from a1_private_dex_flow import decode_instructions, INVOKE_METHOD, FlowDecodeError
from exact_catch import (
    Closed, _verified_xapk, _locate_code_item, read_catches, _targets,
    _reached_nodes, _reach, _inside,
)

BRANCH="experiment/android-a1-metrica-init-state-observer-arm13-20261112"
AUTH_NAMES=frozenset((
    "checkPermission","checkSelfPermission","checkCallingPermission",
    "checkCallingOrSelfPermission","enforcePermission","enforceCallingPermission",
    "enforceCallingOrSelfPermission","checkUidPermission","checkSignatures",
    "hasSigningCertificate","getPackagesForUid","getPackageInfo",
))
AUTH_OWNERS=("Landroid/content/pm/PackageManager;",
             "Landroid/content/Context;",
             "Landroid/content/ContextWrapper;",
             "Landroid/os/Process;")
# Only this known existing manifest-level permission difference is under test.
PERMISSION_MARKER="com.yandex.permission.READ_CREDENTIALS"

def _method_refs(code,dex):
    ins=decode_instructions(code)
    refs=[]
    for pc,opcode,_ in ins:
        if opcode in INVOKE_METHOD:
            mid=struct.unpack_from("<H",code,pc+2)[0]
            if mid>=dex.method_count:raise Closed("METHOD_REF")
            refs.append((pc,mid))
    return refs

def _direct_auth(code,dex):
    refset={mid for _,mid in _method_refs(code,dex)}
    return any((lambda o,n:n in AUTH_NAMES and o in AUTH_OWNERS)(*dex.method(mid))
               for mid in refset)

def _direct_literal(code,dex):
    for pc,opcode,_ in decode_instructions(code):
        if opcode not in (0x1a,0x1b):continue
        idx=(struct.unpack_from("<H",code,pc+2)[0] if opcode==0x1a
             else struct.unpack_from("<I",code,pc+2)[0])
        if idx<dex.string_count and dex.string(idx)==PERMISSION_MARKER:
            return True
    return False

def _explicit_iae_throw(code,dex):
    """One precise bytecode invariant: new-instance IAE vR -> throw vR.

    This is evidence that a callee CAN throw, not that it did so at runtime.
    Does not pretend arbitrary exceptions or invoke-sites are equivalent.
    """
    ins=decode_instructions(code)
    created=[]
    for pos,(pc,op,_) in enumerate(ins):
        if op!=0x22:continue
        typ=struct.unpack_from("<H",code,pc+2)[0]
        if typ>=dex.type_count or dex.type(typ)!="Ljava/lang/IllegalArgumentException;":
            continue
        reg=code[pc+1]
        created.append((pc,reg))
        for later_pc,later_op,_ in ins[pos+1:]:
            if later_pc>pc+200:break
            if later_op==0x27 and code[later_pc+1]==reg:
                return "IAE_DIRECT_THROW"
    return "IAE_CONSTRUCT_ONLY" if created else "NO_IAE_CONSTRUCTION"

def _explicit_sdk_illegal_state(code,dex):
    """Conservatively match one callee's own IllegalStateException construction
    and direct same-register throw. Never infer that the live method executed.
    """
    ins=decode_instructions(code)
    for i,(pc,op,_) in enumerate(ins):
        if op!=0x22:continue
        tid=struct.unpack_from("<H",code,pc+2)[0]
        if tid>=dex.type_count or dex.type(tid)!="Ljava/lang/IllegalStateException;":
            continue
        reg=code[pc+1]
        for later_pc,later_op,_ in ins[i+1:]:
            if later_pc>pc+200:break
            if later_op==0x27 and code[later_pc+1]==reg:
                return True
    return False

def inspect(xapk,private_java=None,provider_java=None):
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise Closed("CI_ISOLATION")
    targets=[]
    service_private=[]
    provider_impl_private=[]
    for blob in _verified_xapk(xapk):
        dex=Dex(blob)
        # Concrete implementation of exactly one already source-confirmed
        # getPushServiceController() interface dispatch. Private methods only.
        for mid,code in dex.code_methods():
            owner,name=dex.method(mid)
            if (owner.endswith("/FirebasePushServiceControllerProvider;") and
                name=="getPushServiceController" and
                private_java_parameter_signature(dex,mid)==""):
                provider_impl_private.append((owner,name))
        strings=dex.possible_error_strings()
        if not strings:continue
        # Per-DEX method declaration lookup, not a global scan of dependencies.
        defined={}
        for mid,code in dex.code_methods():
            defined[dex.method_signature(mid)]=code
        for mid,code in dex.code_methods():
            owner,name=dex.method(mid)
            if group_class(owner)!="PUSH_IMPL" or name!="a":continue
            if not exact_fatal_cfg(code,strings,dex,group_call)["fatal_throw_candidates"]:
                continue
            refs=private_exclusive_fatal_guard_refs(code,strings,dex,group_call)
            if private_near_true_exact_throw_path(code,refs,strings)!="TRUE_CFG_BLOCKS_THROW":
                continue
            off=_locate_code_item(dex,mid)
            exact,ranges=read_catches(dex.data,off,dex)
            if exact!=code:raise Closed("CODE_DRIFT")
            ins=decode_instructions(code)
            pcs={p for p,_,_ in ins}
            normal={p:_nexts(code,(p,op,size),pcs) for p,op,size in ins}
            near=[i for i,(p,op,_) in enumerate(ins) if
                  op in INVOKE_METHOD and
                  struct.unpack_from("<H",code,p+2)[0] in refs]
            if len(near)!=1 or near[0]+2>=len(ins):
                raise Closed("NEAR_LAYOUT")
            idx=near[0]
            if ins[idx+1][1]!=0x0a or ins[idx+2][1] not in (0x38,0x39):
                raise Closed("NEAR_LAYOUT")
            pc_guard,opcode,_=ins[idx+2]
            if code[ins[idx+1][0]+1]!=code[pc_guard+1]:
                raise Closed("NEAR_LAYOUT")
            true_pc=(normal[pc_guard][1] if opcode==0x39 else normal[pc_guard][0])
            reached=_reached_nodes(true_pc,normal)
            throw_targets={t for _,t in _targets(code,ins,strings)}
            relevant_handlers={dest for start,end,entries in ranges
                for _,dest in entries if _reach(dest,throw_targets,normal)}
            candidates=set()
            for pc,callee in _method_refs(code,dex):
                if pc not in reached:continue
                if not any(start<=pc<end and any(
                        dest in relevant_handlers for _,dest in entries)
                        for start,end,entries in ranges):
                    continue
                candidates.add(callee)
            candidates_codes=[]
            for callee in candidates:
                try: signature=dex.method_signature(callee)
                except (IndexError,ValueError):continue
                if signature in defined:
                    candidates_codes.append(defined[signature])
            direct_auth=sum((lambda o,n:n in AUTH_NAMES and o in AUTH_OWNERS)(
                    *dex.method(callee)) for callee in candidates)
            # ONE hypothesis tied to AppMetrica's published PushCore.init:
            # does PushServiceFacade.initPushService occur on the exact live
            # TRUE-normal + catch-covered DEX path? Exact source only.
            def push_service_target(mid):
                owner,name=dex.method(mid)
                return owner.endswith("/PushServiceFacade;") and name=="initPushService"
            service_direct=[mid for mid in candidates if push_service_target(mid)]
            if (len(service_direct)==1 and
                dex.method_signature(service_direct[0]) in defined and
                private_java_parameter_signature(dex,service_direct[0])==
                "android.content.Context"):
                service_private.append(dex.method(service_direct[0]))
            provider_get=[mid for mid in candidates
                if dex.method(mid)[1]=="getPushServiceController"]
            provider_get_public=[mid for mid in provider_get if
                dex.method(mid)[0].endswith("/PushServiceControllerProvider;")]
            provider_concrete=[mid for mid in candidates if
                dex.method(mid)[1]=="getIdentifier"]
            composite_ctor=[mid for mid in candidates if
                dex.method(mid)[1]=="<init>" and
                dex.method(mid)[0].endswith("/PushServiceControllerComposite;")]
            service_onehop=[mid for mid in candidates
                if dex.method_signature(mid) in defined
                and any(push_service_target(other)
                    for _,other in _method_refs(
                      defined[dex.method_signature(mid)],dex))]
            iae_direct_methods=[callee for callee in candidates
                if dex.method_signature(callee) in defined
                and _explicit_iae_throw(
                    defined[dex.method_signature(callee)],dex)=="IAE_DIRECT_THROW"]
            iae_construct_methods=[callee for callee in candidates
                if dex.method_signature(callee) in defined
                and _explicit_iae_throw(
                    defined[dex.method_signature(callee)],dex)=="IAE_CONSTRUCT_ONLY"]
            ise_direct_methods=[callee for callee in candidates
                if dex.method_signature(callee) in defined and _explicit_sdk_illegal_state(
                    defined[dex.method_signature(callee)],dex)]
            onehop_auth=sum(_direct_auth(method,dex) for method in candidates_codes)
            onehop_literal=sum(_direct_literal(method,dex) for method in candidates_codes)
            targets.append({
                "exact_method":"ONE",
                "true_catch_invokes_bounded":min(len(candidates),64),
                "catch_handlers_to_modeled_error_bounded":min(len(relevant_handlers),16),
                "direct_permission_or_signature_api_bounded":min(direct_auth,16),
                "one_hop_permission_or_signature_api_bounded":min(onehop_auth,16),
                "one_hop_known_permission_literal_bounded":min(onehop_literal,16),
                "provider_get_direct_bounded":min(len(provider_get),8),
                "provider_get_exact_api_class_bounded":min(len(provider_get_public),8),
                "provider_get_declared_same_dex":sum(dex.method_signature(mid) in defined for mid in provider_get),
                "provider_get_prototype_arity_zero":sum(private_java_parameter_signature(dex,mid)=="" for mid in provider_get),
                "identifier_lookup_direct_bounded":min(len(provider_concrete),8),
                "composite_constructor_direct_bounded":min(len(composite_ctor),8),
                "service_class_matches_public_modern":(len(service_direct)==1 and
                    dex.method(service_direct[0])[0]==
                    "Lio/appmetrica/analytics/push/coreutils/internal/PushServiceFacade;"),
                "service_proto_exact_context":(len(service_direct)==1 and
                    private_java_parameter_signature(dex,service_direct[0])==
                    "android.content.Context"),
                "service_declared_same_dex":(len(service_direct)==1 and
                    dex.method_signature(service_direct[0]) in defined),
                "push_service_init_direct_on_true_catch_bounded":min(len(service_direct),8),
                "push_service_init_onehop_on_true_catch_bounded":min(len(service_onehop),8),
                "push_service_hypothesis":("DIRECT" if len(service_direct)==1 else
                    "ONE_HOP" if len(service_onehop)==1 else "NOT_ESTABLISHED"),
                                "exact_candidate_callees_with_ISE_direct_throw_bounded":min(len(ise_direct_methods),16),
                "ISE_source_candidate":("ONE" if len(ise_direct_methods)==1 else
                                        "NONE" if not ise_direct_methods else "MULTIPLE"),
                "ISE_source_candidate_group":(
                    group_class(dex.method(ise_direct_methods[0])[0])
                    if len(ise_direct_methods)==1 else "UNKNOWN"),
                                "exact_candidate_callees_with_IAE_direct_throw_bounded":min(len(iae_direct_methods),16),
                "exact_candidate_callees_with_IAE_construct_only_bounded":min(len(iae_construct_methods),16),
                "single_source_IAE_callee":(
                    "ONE" if len(iae_direct_methods)==1 else
                    "NONE" if len(iae_direct_methods)==0 else "MULTIPLE"),
                "single_source_IAE_group":(
                    group_class(dex.method(iae_direct_methods[0])[0])
                    if len(iae_direct_methods)==1 else "UNKNOWN"),
                "source_permission_link":(
                    "DIRECT_API" if direct_auth else
                    "ONE_HOP_API" if onehop_auth else
                    "LITERAL_ONLY" if onehop_literal else "NOT_ESTABLISHED"),
                "runtime_throw_site_proven":False,
                "sdk_state_changed":False
            })
    if len(targets)!=1:
        return {"exact_method":"AMBIGUOUS_OR_ABSENT",
                "source_permission_link":"UNKNOWN",
                "runtime_throw_site_proven":False}
    targets[0]["provider_concrete_source_decl_count_bounded"]=min(len(provider_impl_private),8)
    targets[0]["provider_concrete_source_class_unique"]=len(provider_impl_private)==1
    if private_java is not None:
        root=Path(os.environ.get("GITHUB_WORKSPACE","/unavailable")).resolve()
        dest=Path(private_java).resolve()
        if (dest.name!="PrivatePostTrueServiceTarget.java" or
            root not in dest.parents or len(service_private)!=1):
            raise Closed("PRIVATE_SERVICE_SOURCE_BOUND")
        owner,method=service_private[0]
        class_name=owner[1:-1].replace("/",".") if owner.startswith("L") and owner.endswith(";") else ""
        if (not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$.]*",class_name) or
            method!="initPushService"):
            raise Closed("PRIVATE_SERVICE_TOKEN_INVALID")
        # Third-party class identity exists only in this runner's transient Java.
        # Never include this generated class in git or uploaded artifacts.
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(
            "package pro.celikom.a1exitwitness;\n"
            "public final class PrivatePostTrueServiceTarget {\n"
            "  public static String[] exact() { return new String[] {"
            +json.dumps(class_name)+","+json.dumps(method)+","
            +json.dumps("android.content.Context")+"}; }\n"
            "}\n",encoding="utf-8")
    if provider_java is not None:
        root=Path(os.environ.get("GITHUB_WORKSPACE","/unavailable")).resolve()
        dest=Path(provider_java).resolve()
        if (dest.name!="PrivatePostTrueProviderTarget.java" or
            root not in dest.parents or len(provider_impl_private)!=1):
            raise Closed("PRIVATE_PROVIDER_SOURCE_BOUND")
        owner,method=provider_impl_private[0]
        class_name=owner[1:-1].replace("/",".") if owner.startswith("L") and owner.endswith(";") else ""
        if (not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$.]*",class_name) or
            method!="getPushServiceController"):
            raise Closed("PRIVATE_PROVIDER_TOKEN_INVALID")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(
            "package pro.celikom.a1exitwitness;\n"
            "public final class PrivatePostTrueProviderTarget {\n"
            "  public static String[] exact() { return new String[] {"
            +json.dumps(class_name)+","+json.dumps(method)+"}; }\n"
            "}\n",encoding="utf-8")
    return targets[0]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--xapk",required=True,type=Path)
    ap.add_argument("--private-java",type=Path)
    ap.add_argument("--provider-java",type=Path)
    args=ap.parse_args()
    try:
        out=inspect(args.xapk,args.private_java,args.provider_java)
        print("PERMISSION_CATCH_CHECK "+json.dumps(out,sort_keys=True))
        return 0 if out["exact_method"]=="ONE" else 2
    except (Closed,FlowDecodeError,ValueError,IndexError,struct.error,OSError):
        print('PERMISSION_CATCH_CHECK {"exact_method":"UNKNOWN","source_permission_link":"UNKNOWN","runtime_throw_site_proven":false}')
        return 2

if __name__=="__main__":raise SystemExit(main())
