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
from a1_private_provider_authority import inspect_authority_refs
from a1_private_push_contains import inspect_push_contains
from a1_private_dex_fatal_cfg import exact_fatal_cfg,private_exclusive_fatal_guard_refs
from a1_private_push_init import inspect_legacy_push_init
from a1_private_dex_callers import bounded_fatal_callers
from a1_private_dex_supply_chain import classify_private_supplier_chain,inspect_source_chain,_family
from a1_private_dex_predicate import code_items_with_meta,rule_from_synthetic_lengths
from a1_private_dex_flow import exact_error_guard_report,private_direct_guard_invokes,private_guard_input_sources,private_push_utils_supplier_refs,private_direct_guard_branch_roles,decode_instructions,FlowDecodeError,INVOKE_METHOD

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
                "exact_guard_flow": exact_error_guard_report(code,targets,dex,group_call),
                "exact_fatal_cfg": exact_fatal_cfg(code,targets,dex,group_call),
                "exact_fatal_cfg_refined": exact_fatal_cfg(
                    code,targets,dex,lambda owner,name:_family(owner,name,group_call)),
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
    seen=0;matches=[];guard_insights=[];guard_rules=[];supplier_chains=[];near_guard_chains=[];fatal_callers=[];fatal_signatures=[];fatal_overloads=[];near_overload_counts=[];case_categories={};contains_cases=[];authority_refs=[];push_public_routes=[];legacy_init_reports=[]
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
                        guard_insights.append(private_guard_dependency_info(payload))
                        guard_rules.extend(private_guard_synthetic_rule(payload))
                        fatal_signatures.extend(private_fatal_a_signature_families(payload))
                        fatal_overloads.extend(private_fatal_overload_shapes(payload))
                        near_overload_counts.append(private_near_guard_overload_count(payload))
                        case_categories.update(private_exact_guard_case_categories(payload))
                        contains_cases.extend(inspect_push_contains(payload,Dex,group_class,
                                            group_call,exact_fatal_cfg))
                        authority_refs.append(inspect_authority_refs(payload,Dex,group_class))
                        push_public_routes.append(private_public_push_entrypoints(payload))
                        legacy_init_reports.append(inspect_legacy_push_init(payload,Dex,group_call))
                        chain=classify_private_supplier_chain(
                            payload,Dex,group_class,group_call,exact_error_guard_report)
                        if chain is not None:supplier_chains.append(chain)
                        near_guard_chain=private_near_guard_dependencies(payload)
                        if near_guard_chain is not None:
                            near_guard_chains.append(near_guard_chain)
                        graph=bounded_fatal_callers(
                            Dex(payload),group_class,group_call,
                            code_candidates,exact_error_guard_report)
                        if graph is not None:fatal_callers.append(graph)
    exact=[m for m in matches if m["owner"]=="PUSH_IMPL"]
    fatal_a=[m for m in exact if m["obfuscated_a"]]
    private_cases=sorted(case_categories.items())[:8]
    return {
        "private_global_metrica_authority_literal_in_dex":any(
            item["literal_found"] for item in authority_refs),
        "private_global_metrica_authority_literal_callsite_groups":sorted({
            grp for item in authority_refs for grp in item["method_groups"]}),
        "private_global_metrica_authority_sdk_api_cooccurrence":sorted({
            grp for item in authority_refs for grp in item["call_api_cooccurrences"]}),
        "private_global_metrica_authority_direct_methods_bounded":min(sum(
            item["methods_referencing_bounded"] for item in authority_refs),32),
        "private_authority_literal_then_uri_parse_methods_bounded":min(sum(
            item["literal_followed_by_uri_parse_bounded"] for item in authority_refs),16),
        "private_authority_literal_then_resolver_query_methods_bounded":min(sum(
            item["literal_followed_by_resolver_query_bounded"] for item in authority_refs),16),
        "push_impl_exact_string_contains_guard_cases":[
            {"argument":c["argument"],"receiver":c["receiver"],
             "direct_guard":c["direct_guard"]}
            for c in contains_cases[:12]],
        "private_exact_guard_case_categories":[
            {"case":"CASE_"+str(i),
             "owner":data["group"],
             "callee_categories":data["calls"]}
            for i,(_,data) in enumerate(private_cases)],
        "near_fatal_guard_actual_methods_bounded":min(sum(
            x["target_methods"] for x in near_overload_counts),16),
        "near_fatal_guard_same_name_boolean_overloads_bounded":min(sum(
            x["bool_overloads_in_matching_classes"]
            for x in near_overload_counts),32),
        "private_exact_fatal_a_overload_shapes_bounded":sorted({
            item["params"] for item in fatal_overloads}),
        "private_exact_fatal_a_overload_count_bounded":min(len(fatal_overloads),16),
        "private_exact_fatal_a_overload_near_guard_families":sorted({
            item["params"] + "__" + source for item in fatal_overloads
            for source in item["guard_sources"]}),
        "private_exact_fatal_a_overload_boolean_fatal_families":sorted({
            item["params"] + "__" + source for item in fatal_overloads
            for source in item["near_guard_bool_result"]}),
        "near_fatal_guard_dependency_calls_by_depth":[
            sorted({x for chain in near_guard_chains
                    for x in chain[depth]["calls"]})
            for depth in range(3)],
        "near_fatal_guard_dependency_fields_by_depth":[
            sorted({x for chain in near_guard_chains
                    for x in chain[depth]["fields"]})
            for depth in range(3)],
        "near_fatal_guard_dependency_method_counts_by_depth":[
            min(sum(chain[depth]["methods_with_body_bounded"]
                    for chain in near_guard_chains),32)
            for depth in range(3)],
        "legacy_push_init_overloads_bounded":min(sum(
            item["overloads"] for item in legacy_init_reports),12),
        "legacy_push_init_body_count_bounded":min(sum(
            item["body_count"] for item in legacy_init_reports),12),
        "legacy_push_init_parameter_shapes":sorted({
            shape for item in legacy_init_reports
            for shape in item["param_signatures"]}),
        "legacy_push_init_call_families_by_depth":[
            sorted({cat for item in legacy_init_reports
                    for cat in item["calls_by_depth"][level]})
            for level in range(3)],
        "legacy_push_init_declared_body_methods_by_depth":[
            min(sum(item["method_counts_by_depth"][level]
                for item in legacy_init_reports),32)
            for level in range(3)],
        "legacy_push_init_flow_unresolved":any(
            item["unresolved_calls"] for item in legacy_init_reports),
        "public_push_entrypoint_methods_known":sorted({
            x for r in push_public_routes for x in r["public_push_methods"]}),
        "public_push_entrypoint_invoked_candidates":sorted({
            x for r in push_public_routes for x in r["public_push_invoke_candidates"]}),
        "public_push_entrypoint_music_host_candidates":sorted({
            x for r in push_public_routes for x in r["music_host_push_invoke_candidates"]}),
        "public_push_entrypoint_call_scan_approximate":True,
        "exact_push_fatal_a_signature_categories":sorted(set(fatal_signatures)),
        "exact_fatal_caller_families_by_depth":[
            sorted({v for graph in fatal_callers
                    for v in graph["caller_depth"][depth]["caller_families"]})
            for depth in range(3)],
        "exact_fatal_caller_counts_by_depth_bounded":[
            min(sum(graph["caller_depth"][depth]["caller_methods_bounded"]
                    for graph in fatal_callers),64)
            for depth in range(3)],
        "exact_static_caller_graph_not_runtime_proof":True,
        "exact_string_supplier_literal_families_by_depth":[
            sorted({v for chain in supplier_chains
                    for v in chain[depth]["literal_families"]})
            for depth in range(3)],
        "exact_string_supplier_catch_instruction_by_depth":[
            any(chain[depth]["catch_handler_instruction_seen"]
                for chain in supplier_chains)
            for depth in range(3)],
        "exact_string_supplier_call_families_by_depth":[
            sorted({v for chain in supplier_chains
                    for v in chain[depth]["calls"]})
            for depth in range(3)],
        "exact_string_supplier_field_families_by_depth":[
            sorted({v for chain in supplier_chains
                    for v in chain[depth]["fields"]})
            for depth in range(3)],
        "exact_string_supplier_body_methods_by_depth_bounded":[
            min(sum(chain[depth]["methods_with_body_bounded"]
                    for chain in supplier_chains),16)
            for depth in range(3)],
        "exact_guard_synthetic_length_rules":sorted(set(guard_rules)),
        "synthetic_length_evaluation_not_runtime_proof":True,
        "exact_guard_method_candidates_bounded":min(sum(
            x["guard_targets"] for x in guard_insights),16),
        "exact_guard_return_type_families":sorted({
            t for x in guard_insights for t in x["return_kinds"]}),
        "exact_guard_parameter_type_families":sorted({
            t for x in guard_insights for t in x["parameter_families"]}),
        "exact_guard_input_possible_source_families":sorted({
            t for x in guard_insights for t in x["input_sources"]}),
        "exact_guard_branch_skip_polarities":sorted({
            t for x in guard_insights for t in x["branch_polarities"]}),
        "exact_string_supplier_methods_bounded":min(sum(
            x["supplier_methods"] for x in guard_insights),16),
        "exact_string_supplier_direct_dependency_families":sorted({
            t for x in guard_insights for t in x["supplier_body_called_categories"]}),
        "exact_string_supplier_reads_local_field":any(
            x["supplier_reads_field"] for x in guard_insights),
        "exact_guard_implementation_count_bounded":min(sum(
            x["body_found"] for x in guard_insights),16),
        "exact_guard_direct_dependency_families":sorted({
            t for x in guard_insights for t in x["called_categories"]}),
        "exact_guard_reads_local_field":any(x["reads_fields"] for x in guard_insights),
        "push_impl_a_refined_guard_sources":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg_refined"]["guard_source_categories"]}),
        "push_impl_a_refined_near_guard_sources":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg_refined"]["near_fatal_sources"]}),
        "push_impl_a_fatal_cfg_decoded":all(
            m["exact_fatal_cfg"]["decoded"] for m in fatal_a),
        "push_impl_a_exclusive_fatal_guards_bounded":min(sum(
            m["exact_fatal_cfg"]["exclusive_fatal_guards"] for m in fatal_a),32),
        "push_impl_a_exclusive_guard_sources":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg"]["guard_source_categories"]}),
        "push_impl_a_near_fatal_guard_sources":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg"]["near_fatal_sources"]}),
        "push_impl_a_near_fatal_guard_polarities":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg"]["near_fatal_polarities"]}),
        "push_impl_a_near_fatal_BOOLEAN_result_to_exception":sorted({
            x for m in fatal_a
            for x in m["exact_fatal_cfg"]["near_fatal_boolean_result_polarities"]}),
        "push_impl_a_exclusive_guard_direction":sorted({
            x for m in fatal_a for x in m["exact_fatal_cfg"]["fatal_guard_polarities"]}),
        "push_impl_a_fatal_cfg_is_not_runtime_proof":True,
        "push_impl_a_exact_flow_decoded":all(
            m["exact_guard_flow"]["decoded"] for m in fatal_a),
        "push_impl_a_exact_error_string_candidates_bounded":min(
            sum(m["exact_guard_flow"]["target_strings"] for m in fatal_a),16),
        "push_impl_a_exact_guards_skipping_throw_bounded":min(
            sum(m["exact_guard_flow"]["guards_skipping_throw"]
                for m in fatal_a),16),
        "push_impl_a_exact_guard_source_categories":sorted({
            category for m in fatal_a
            for category in m["exact_guard_flow"]["verified_guard_sources"]}),
        "exact_flow_proves_runtime_predicate":False,
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







def private_near_guard_dependencies(binary):
    """Read only finite dependency categories for verified near-fatal predicates."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return None
    codes={}
    roots=set()
    declarations={}
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
            codes[mid]=code
            declarations[dex.method_signature(mid)]=mid
        if group_class(owner)=="PUSH_IMPL" and name=="a":
            report=exact_error_guard_report(code,targets,dex,group_call)
            if report["decoded"] and report["target_strings"]:
                roots.update(private_exclusive_fatal_guard_refs(
                    code,targets,dex,group_call))
    if not roots:return None
    return inspect_source_chain(dex,codes,roots,group_call,
                                dex.push_interface_implementors(),declarations)




def private_java_parameter_signature(dex,mid):
    """Only for transient private Java targeting; never returned in public JSON."""
    _,proto,_=struct.unpack_from("<HHI",dex.data,dex.method_off+mid*8)
    count,off=struct.unpack_from("<II",dex.data,72)
    if proto>=count or off+count*12>len(dex.data):raise DexError("PROTO_BOUND")
    _,params=struct.unpack_from("<II",dex.data,off+proto*12+4)
    if not params:return ""
    if params+4>len(dex.data):raise DexError("PROTO_BOUND")
    n=struct.unpack_from("<I",dex.data,params)[0]
    if n>16 or params+4+n*2>len(dex.data):raise DexError("PROTO_BOUND")
    java={"V":"void","Z":"boolean","B":"byte","C":"char","S":"short",
          "I":"int","J":"long","F":"float","D":"double"}
    result=[]
    for i in range(n):
        desc=dex.type(struct.unpack_from("<H",dex.data,params+4+i*2)[0])
        if desc in java:result.append(java[desc])
        elif desc.startswith("L") and desc.endswith(";"):
            result.append(desc[1:-1].replace("/","."))
        elif desc.startswith("["):
            result.append(desc.replace("/","."))
        else:raise DexError("PROTO_BOUND")
    return ",".join(result)


def private_all_exact_guard_methods(binary):
    """Exact class/name/arg-signature tuples held exclusively inside private CI."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    refs=set()
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner)!="PUSH_IMPL" or name!="a":continue
        cfg=exact_fatal_cfg(code,targets,dex,group_call)
        if not cfg["decoded"] or not cfg["fatal_throw_candidates"]:continue
        refs.update(private_exclusive_fatal_guard_refs(
            code,targets,dex,group_call,max_distance=len(code)))
    result=set()
    for ref in refs:
        owner,name=dex.method(ref)
        if group_call(owner,name) not in (
                "PUSH_IMPL_HELPER","PUSH_COMMON","PUSH_OTHER_HELPER","PUSH_UTILS"):
            continue
        result.add((owner.strip("L;").replace("/","."),name,
                    private_java_parameter_signature(dex,ref)))
    return result


def private_exact_guard_case_categories(binary):
    """Keyed privately, outputs only fixed owner/callee categories to caller."""
    targets=private_all_exact_guard_methods(binary)
    if not targets:return {}
    dex=Dex(binary)
    result={}
    target_names={(cls,method) for cls,method,_ in targets}
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        cls=owner.strip("L;").replace("/",".")
        if (cls,name) not in target_names:continue
        key=(cls,name,private_java_parameter_signature(dex,mid))
        if key not in targets:continue
        try:ins=decode_instructions(code)
        except FlowDecodeError:
            result[key]={"group":"UNKNOWN","calls":["UNKNOWN"]}
            continue
        calls=set()
        for pc,op,_ in ins:
            if op not in INVOKE_METHOD:continue
            ref=struct.unpack_from("<H",code,pc+2)[0]
            if ref<dex.method_count:
                calls.add(group_call(*dex.method(ref)))
        result[key]={"group":group_call(owner,name),"calls":sorted(calls)}
    return result

def private_near_guard_overload_count(binary):
    """Count Boolean overload ambiguity of exact near-fatal method references."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    refs=set()
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner)=="PUSH_IMPL" and name=="a":
            cfg=exact_fatal_cfg(code,targets,dex,group_call)
            if cfg["decoded"] and cfg["fatal_throw_candidates"]:
                refs.update(private_exclusive_fatal_guard_refs(
                    code,targets,dex,group_call))
    if not refs:return {"target_methods":0,"bool_overloads_in_matching_classes":0}
    pairs={dex.method(ref) for ref in refs}
    count=sum(1 for mid in range(dex.method_count)
              if dex.method(mid) in pairs and dex.method_returns_boolean(mid))
    return {"target_methods":min(len(refs),16),
            "bool_overloads_in_matching_classes":min(count,32)}

def private_fatal_overload_shapes(binary):
    """Differentiate same-name obfuscated overloads using fixed type families."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return []
    reports=[]
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner)!="PUSH_IMPL" or name!="a":continue
        cfg=exact_fatal_cfg(code,targets,dex,group_call)
        if not cfg["decoded"] or not cfg["fatal_throw_candidates"]:continue
        ci,proto,si=struct.unpack_from("<HHI",dex.data,dex.method_off+mid*8)
        size,off=struct.unpack_from("<II",dex.data,72)
        if proto>=size or off+size*12>len(dex.data):raise DexError("PROTO_BOUND")
        ret,params=struct.unpack_from("<II",dex.data,off+proto*12+4)
        if not params:descriptors=[]
        else:
            if params+4>len(dex.data):raise DexError("PROTO_BOUND")
            n=struct.unpack_from("<I",dex.data,params)[0]
            if n>12 or params+4+2*n>len(dex.data):raise DexError("PROTO_BOUND")
            descriptors=[dex.type(struct.unpack_from("<H",dex.data,params+4+2*i)[0])
                         for i in range(n)]
        types=[]
        for desc in descriptors:
            types.append("CONTEXT" if desc=="Landroid/content/Context;"
                         else "APPLICATION" if desc=="Landroid/app/Application;"
                         else "STRING" if desc=="Ljava/lang/String;"
                         else group_class(desc)
                         if group_class(desc)!="OTHER"
                         else "OTHER_OBJECT" if desc.startswith(("L","["))
                         else "PRIMITIVE")
        reports.append({"params":",".join(types) or "NONE",
                        "guard_sources":cfg["near_fatal_sources"],
                        "near_guard_bool_result":cfg["near_fatal_boolean_result_polarities"],
                        "fatal_thrown_candidates":cfg["fatal_throw_candidates"]})
    return reports

def private_public_push_entrypoints(binary):
    """Only well-known public SDK API labels, never obfuscated vendor symbols."""
    dex=Dex(binary)
    known={
        ("Lcom/yandex/metrica/push/YandexMetricaPush;","init"):"LEGACY_INIT",
        ("Lcom/yandex/metrica/push/YandexMetricaPush;","activate"):"LEGACY_ACTIVATE",
        ("Lio/appmetrica/analytics/push/AppMetricaPush;","activate"):"MODERN_ACTIVATE",
        ("Lio/appmetrica/analytics/push/AppMetricaPush;","init"):"MODERN_INIT",
    }
    ids=set()
    types=set()
    for mid in range(dex.method_count):
        key=dex.method(mid)
        if key in known:
            ids.add(mid)
            types.add(known[key])
    invoked=set()
    app_invoke=set()
    for caller,code in dex.code_methods():
        where,calls=code_candidates(code,set())
        owner,name=dex.method(caller)
        for _,ref in calls:
            if ref in ids:
                # A conservative byte-level scan may include operand false positives,
                # so this is a candidate count rather than a proven call graph.
                invoked.add(known[dex.method(ref)])
                if owner.startswith("Lru/yandex/music/"):
                    app_invoke.add(known[dex.method(ref)])
    return {"public_push_methods":types,
            "public_push_invoke_candidates":invoked,
            "music_host_push_invoke_candidates":app_invoke}

def private_fatal_a_signature_families(binary):
    """Only finite safe DEX prototype categories, never actual method symbols."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return set()
    result=set()
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner)!="PUSH_IMPL" or name!="a":continue
        report=exact_error_guard_report(code,targets,dex,group_call)
        if not report["decoded"] or not report["target_strings"]:continue
        _,proto,_=struct.unpack_from("<HHI",dex.data,dex.method_off+mid*8)
        count,off=struct.unpack_from("<II",dex.data,72)
        if proto>=count or off+count*12>len(dex.data):raise DexError("PROTO_BOUND")
        ret,params=struct.unpack_from("<II",dex.data,off+proto*12+4)
        if params:
            if params+4>len(dex.data):raise DexError("PROTO_BOUND")
            n=struct.unpack_from("<I",dex.data,params)[0]
            if n>32 or params+4+2*n>len(dex.data):raise DexError("PROTO_BOUND")
        else:n=0
        return_desc=dex.type(ret)
        kind="VOID" if return_desc=="V" else "BOOLEAN" if return_desc=="Z" else "STRING" if return_desc=="Ljava/lang/String;" else "OBJECT_OR_PRIMITIVE"
        result.add(kind+"_PARAMS_"+str(min(n,8)))
    return result

def private_guard_synthetic_rule(binary):
    """Never read a private string; evaluate bounded synthetic lengths only."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return set()
    refs=set()
    for mid,code in dex.code_methods():
        cls,name=dex.method(mid)
        if group_class(cls)!="PUSH_IMPL" or name!="a":continue
        report=exact_error_guard_report(code,targets,dex,group_call)
        if report["decoded"] and report["target_strings"]:
            refs.update(private_direct_guard_invokes(code,targets,dex,group_call))
    rules=set()
    for mid,regs,ins,static,code in code_items_with_meta(dex):
        if mid in refs:
            rules.add(rule_from_synthetic_lengths(code,regs,ins,static,dex))
    if refs and not rules:rules.add("TARGET_METHOD_BODY_MISSING")
    return rules

def private_java_dependency_family(owner,method):
    # Whitelisted framework families only: no proprietary symbols leave CI.
    if owner.startswith("Ljava/util/concurrent/atomic/"):return "JAVA_ATOMIC"
    if owner.startswith("Ljava/lang/reflect/") or owner=="Ljava/lang/Class;":
        return "JAVA_REFLECTION"
    if owner.startswith("Ljava/util/"):return "JAVA_COLLECTION"
    if owner=="Ljava/lang/String;":
        if method=="isEmpty":return "STRING_EMPTY"
        if method=="equals":return "STRING_EQUALS"
        if method=="length":return "STRING_LENGTH"
        if method=="startsWith":return "STRING_PREFIX"
        if method=="contains":return "STRING_CONTAINS"
        return "STRING_OTHER"
    if owner in ("Ljava/lang/Boolean;","Ljava/lang/Integer;"):return "JAVA_BOX"
    if owner.startswith("Ljava/lang/"):return "JAVA_LANG_OTHER"
    return "JAVA_OTHER"


def private_guard_dependency_info(binary):
    """Only fixed classes of references directly inside source-derived guards."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return {"guard_targets":0,"return_kinds":[],
                            "parameter_families":[],"input_sources":[],
                            "supplier_methods":0,"supplier_body_called_categories":[],
                            "supplier_reads_field":False,"branch_polarities":[],"body_found":0,
                            "called_categories":[],"reads_fields":False}
    source={}
    refs=set()
    possible_input_sources=set()
    branch_polarities=set()
    supplier_refs=set()
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
            source[mid]=code
        if group_class(owner)=="PUSH_IMPL" and name=="a":
            report=exact_error_guard_report(code,targets,dex,group_call)
            if report["decoded"] and report["target_strings"]:
                refs.update(private_direct_guard_invokes(code,targets,dex,group_call))
                possible_input_sources.update(
                    private_guard_input_sources(code,targets,dex,group_call))
                branch_polarities.update(
                    private_direct_guard_branch_roles(code,targets,dex,group_call))
                supplier_refs.update(
                    private_push_utils_supplier_refs(code,targets,dex,group_call))
    kinds=set()
    param_families=set()
    categories=set()
    reads_field=False
    body_found=0
    supplier_body_call_categories=set()
    supplier_reads_field=False
    for supplier in supplier_refs:
        if supplier not in source:continue
        try:instruct=decode_instructions(source[supplier])
        except FlowDecodeError:continue
        for pc,op,_ in instruct:
            if 0x52<=op<=0x58 or 0x60<=op<=0x66:
                supplier_reads_field=True
            if op not in INVOKE_METHOD:continue
            ref=struct.unpack_from("<H",source[supplier],pc+2)[0]
            if ref<dex.method_count:
                owner,name=dex.method(ref)
                family=group_call(owner,name)
                supplier_body_call_categories.add(
                    private_java_dependency_family(owner,name)
                    if family=="JAVA_RUNTIME" else family)
    for mid in refs:
        ci,proto,si=struct.unpack_from("<HHI",dex.data,dex.method_off+mid*8)
        count,off=struct.unpack_from("<II",dex.data,72)
        if proto>=count or off+count*12>len(dex.data):raise DexError("PROTO_BOUND")
        ret,params=struct.unpack_from("<II",dex.data,off+proto*12+4)
        if params:
            if params+4>len(dex.data):raise DexError("PROTO_BOUND")
            n=struct.unpack_from("<I",dex.data,params)[0]
            if n>32 or params+4+2*n>len(dex.data):raise DexError("PROTO_BOUND")
            for x in range(n):
                desc=dex.type(struct.unpack_from("<H",dex.data,params+4+2*x)[0])
                param_families.add("STRING" if desc=="Ljava/lang/String;"
                                   else "CONTEXT" if desc=="Landroid/content/Context;"
                                   else "PRIMITIVE" if len(desc)==1
                                   else "OBJECT")
        descriptor=dex.type(ret)
        kinds.add("BOOLEAN" if descriptor=="Z"
                  else "VOID" if descriptor=="V"
                  else "PRIMITIVE" if descriptor in "IJSCBFD"
                  else "OBJECT" if descriptor.startswith(("L","["))
                  else "UNKNOWN")
        if mid not in source:continue
        body_found+=1
        try:instructions=decode_instructions(source[mid])
        except FlowDecodeError:continue
        for pc,op,_ in instructions:
            if 0x52<=op<=0x58 or 0x60<=op<=0x66:
                reads_field=True
            if op not in INVOKE_METHOD:continue
            call=struct.unpack_from("<H",source[mid],pc+2)[0]
            if call<dex.method_count:
                owner,name=dex.method(call)
                family=group_call(owner,name)
                categories.add(private_java_dependency_family(owner,name)
                               if family=="JAVA_RUNTIME" else family)
    return {"guard_targets":min(len(refs),16),
            "return_kinds":sorted(kinds),
            "parameter_families":sorted(param_families),
            "input_sources":sorted(possible_input_sources),
            "branch_polarities":sorted(branch_polarities),
            "supplier_methods":min(len(supplier_refs),16),
            "supplier_body_called_categories":sorted(supplier_body_call_categories),
            "supplier_reads_field":supplier_reads_field,
            "body_found":min(body_found,16),
            "called_categories":sorted(categories),
            "reads_fields":reads_field}

def private_site_methods(binary):
    """Precise throw-site classes and immediate guard call targets in memory."""
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return set(),set(),set(),set()
    guards=set()
    fatals=set()
    suppliers=set()
    near_guards=set()
    for mid,code in dex.code_methods():
        owner,method=dex.method(mid)
        if group_class(owner)!="PUSH_IMPL" or method!="a":continue
        report=exact_error_guard_report(code,targets,dex,group_call)
        if not report["decoded"] or not report["target_strings"]:continue
        fatals.add((owner.strip("L;").replace("/","."),method))
        for ref in private_direct_guard_invokes(code,targets,dex,group_call):
            cl,name=dex.method(ref)
            guards.add((cl.strip("L;").replace("/","."),name))
        for ref in private_exclusive_fatal_guard_refs(code,targets,dex,group_call):
            cl,name=dex.method(ref)
            near_guards.add((cl.strip("L;").replace("/","."),name))
        for ref in private_push_utils_supplier_refs(code,targets,dex,group_call):
            cl,name=dex.method(ref)
            suppliers.add((cl.strip("L;").replace("/","."),name))
    return guards,fatals,suppliers,near_guards

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
    found=set(); guards=set(); fatals=set(); suppliers=set(); near_guards=set(); all_exact=set()
    with zipfile.ZipFile(source) as outer:
        for item in outer.infolist():
            if not item.filename.endswith(".apk") or item.file_size>60000000:continue
            with zipfile.ZipFile(io.BytesIO(outer.read(item))) as part:
                for name in part.namelist():
                    if name.startswith("classes") and name.endswith(".dex"):
                        payload=part.read(name)
                        if payload.startswith(bytes((100,101,120,10))):
                            found.update(private_boolean_helpers(payload))
                            g,f,sup,near=private_site_methods(payload)
                            guards.update(g);fatals.update(f);suppliers.update(sup)
                            near_guards.update(near)
                            all_exact.update(private_all_exact_guard_methods(payload))
    # Verify source-derived class/method tokens before use as Java literals.
    valid=re.compile("^[A-Za-z_$][A-Za-z0-9_$]*(?:[.][A-Za-z_$][A-Za-z0-9_$]*)*$")
    simple=re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
    names=sorted((cls,method) for cls,method in found
                 if valid.fullmatch(cls) and simple.fullmatch(method))[:24]
    if not names:raise DexError("PRIVATE_TARGETS_EMPTY")
    guard_names=sorted((cls,method) for cls,method in guards
                       if valid.fullmatch(cls) and simple.fullmatch(method))[:24]
    fatal_names=sorted((cls,method) for cls,method in fatals
                       if valid.fullmatch(cls) and simple.fullmatch(method))[:16]
    supplier_names=sorted((cls,method) for cls,method in suppliers
                       if valid.fullmatch(cls) and simple.fullmatch(method))[:16]
    near_guard_names=sorted((cls,method) for cls,method in near_guards
                       if valid.fullmatch(cls) and simple.fullmatch(method))[:16]
    exact_guard_names=sorted((cls,method,signature)
                        for cls,method,signature in all_exact
                        if valid.fullmatch(cls) and simple.fullmatch(method)
                        and len(signature)<512 and all(32<=ord(c)<127 for c in signature))[:12]
    target.parent.mkdir(parents=True,exist_ok=True)
    def java_rows(rows):
        return (","+chr(10)).join("        {"+json.dumps(cls)+","+json.dumps(method)+"}"
                             for cls,method in rows)
    generated=("package pro.celikom.a1exitwitness;"+chr(10)+
               "public final class PrivatePushTargets {"+chr(10)+
               "  public static String[][] getTargets() { return new String[][] {"+chr(10)+
               java_rows(names)+chr(10)+"  }; }"+chr(10)+
               "  public static String[][] getGuardTargets() { return new String[][] {"+chr(10)+
               java_rows(guard_names)+chr(10)+"  }; }"+chr(10)+
               "  public static String[][] getFatalTargets() { return new String[][] {"+chr(10)+
               java_rows(fatal_names)+chr(10)+"  }; }"+chr(10)+
               "  public static String[][] getSupplierTargets() { return new String[][] {"+chr(10)+
               java_rows(supplier_names)+chr(10)+"  }; }"+chr(10)+
               "  public static String[][] getNearFatalGuardTargets() { return new String[][] {"+chr(10)+
               java_rows(near_guard_names)+chr(10)+"  }; }"+chr(10)+
               "  public static String[][] getAllFatalGuardExactTargets() { return new String[][] {"+chr(10)+
               (","+chr(10)).join("        {"+json.dumps(cls)+","+json.dumps(method)+","+
                              json.dumps(signature)+"}"
                              for cls,method,signature in exact_guard_names)+chr(10)+
               "  }; }"+chr(10)+
               "}"+chr(10))
    target.write_text(generated,encoding="utf-8")
    target.chmod(0o600)
    return {"private_transient_boolean_targets_bounded":len(names),
            "private_transient_guard_targets_bounded":len(guard_names),
            "private_transient_fatal_targets_bounded":len(fatal_names),
            "private_transient_supplier_targets_bounded":len(supplier_names),
            "private_transient_near_fatal_guard_targets_bounded":len(near_guard_names),
            "private_transient_all_fatal_guard_exact_targets_bounded":len(exact_guard_names)}


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
            result.update(generate_private_targets(
                args.xapk,args.private_java))
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
