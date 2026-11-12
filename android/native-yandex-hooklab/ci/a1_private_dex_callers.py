"""Privacy-bounded inbound call graph to the exact Push fatal method.

All method identifiers, code units and class names remain inside ephemeral CI.
Only fixed subsystem enums and bounded counts leave the runner.
"""
import struct
from a1_private_dex_flow import decode_instructions,FlowDecodeError,INVOKE_METHOD

def caller_family(owner,name,group_call):
    category=group_call(owner,name)
    if category=="OTHER":
        if owner.startswith("Lru/yandex/"):
            return "YANDEX_HOST_OTHER"
        if owner.startswith("Lkotlin/") or owner.startswith("Lkotlinx/"):
            return "KOTLIN_RUNTIME"
        return "OTHER_OWNER"
    return category

def bounded_fatal_callers(dex, group_class,group_call,code_candidates,
                          exact_error_guard_report):
    targets=dex.possible_error_strings()
    if not targets:return None
    declared={}
    fatal_ids=set()
    for mid,code in dex.code_methods():
        declared[mid]=code
        owner,name=dex.method(mid)
        if group_class(owner)=="PUSH_IMPL" and name=="a":
            report=exact_error_guard_report(code,targets,dex,group_call)
            if report["decoded"] and report["target_strings"]:
                fatal_ids.add(mid)
    if not fatal_ids:return None
    reverse={}
    decoded_methods=0
    for caller,code in declared.items():
        # Cheap screening before strict decode: operands can false match;
        # false matches are discarded by exact instruction decoder.
        _,possible=code_candidates(code,set())
        if not any(ref in declared for _,ref in possible):
            continue
        try:ins=decode_instructions(code)
        except FlowDecodeError:continue
        decoded_methods+=1
        for pc,op,_ in ins:
            if op not in INVOKE_METHOD:continue
            method_ref=struct.unpack_from("<H",code,pc+2)[0]
            if method_ref in declared:
                reverse.setdefault(method_ref,set()).add(caller)
    direct=set(reverse.get(next(iter(fatal_ids)),set()))
    for mid in fatal_ids:
        direct.update(reverse.get(mid,set()))
    depth=[]
    seen=set(fatal_ids)
    frontier=set(fatal_ids)
    for _ in range(3):
        parents=set()
        for mid in frontier:
            parents.update(reverse.get(mid,set()))
        parents-=seen
        seen.update(parents)
        cats=sorted({caller_family(*dex.method(mid),group_call) for mid in parents})
        depth.append({"caller_methods_bounded":min(len(parents),64),
                      "caller_families":cats})
        frontier=parents
    return {"fatal_method_count_bounded":min(len(fatal_ids),8),
            "decoded_direct_callers_bounded":min(len(direct),64),
            "caller_depth":depth,
            "static_call_graph_only_not_runtime_proof":True}
