"""Conservative DEX control-flow analysis at exact private Push exception.

Only fixed families and bounded counts are returned. Method IDs, raw
instructions, field values, vendor code, strings and offsets remain private.
No DEX rewriting, exception interception or runtime behavior change.
"""
import struct
from a1_private_dex_flow import (
    decode_instructions,FlowDecodeError,IF_OPS,_guard_source,
)

def _nexts(code,inst,pcs):
    p,op,size=inst
    after=p+size*2
    if op in range(0x0e,0x12) or op==0x27:
        return []
    if op in (0x2b,0x2c):
        raise FlowDecodeError("SWITCH_UNSUPPORTED")
    if op==0x28:
        off=code[p+1]
        if off>=128:off-=256
        targets=[p+off*2]
    elif op==0x29:
        targets=[p+struct.unpack_from("<h",code,p+2)[0]*2]
    elif op==0x2a:
        targets=[p+struct.unpack_from("<i",code,p+2)[0]*2]
    elif op in IF_OPS:
        targets=[after,p+struct.unpack_from("<h",code,p+2)[0]*2]
    else:
        targets=[after]
    if any(q not in pcs for q in targets):
        raise FlowDecodeError("JUMP_TARGET")
    return targets

def exact_fatal_cfg(code:bytes,target_strings:set[int],dex,group_call):
    result={"decoded":False,"fatal_throw_candidates":0,
            "exclusive_fatal_guards":0,"guard_source_categories":[],
            "fatal_guard_polarities":[],"near_fatal_sources":[],
            "near_fatal_polarities":[],
            "near_fatal_boolean_result_polarities":[],
            "has_switch_or_unknown_layout":False,
            "runtime_causality_proven":False}
    try:
        ins=decode_instructions(code)
        pcs={p for p,_,_ in ins}
        graph={p:_nexts(code,(p,op,size),pcs) for p,op,size in ins}
    except FlowDecodeError:
        result["has_switch_or_unknown_layout"]=True
        return result
    result["decoded"]=True
    positions=[p for p,op,_ in ins if
         (op==0x1a and struct.unpack_from("<H",code,p+2)[0] in target_strings)
         or (op==0x1b and struct.unpack_from("<I",code,p+2)[0] in target_strings)]
    if not positions:return result
    throws={p for p,op,_ in ins if op==0x27}
    candidate_throws={min((p for p in throws if stringp<p<=stringp+256),default=-1)
                      for stringp in positions}-{-1}
    result["fatal_throw_candidates"]=min(len(candidate_throws),16)
    if not candidate_throws:return result
    memo={}
    def reaches(start,target):
        key=(start,target)
        if key in memo:return memo[key]
        visited=set()
        stack=[start]
        while stack:
            p=stack.pop()
            if p==target:
                memo[key]=True;return True
            if p in visited:continue
            visited.add(p)
            stack.extend(q for q in graph.get(p,[]) if q not in visited)
        memo[key]=False
        return False
    sources=set()
    polarities=set()
    near=set()
    near_polarities=set()
    near_result_polarities=set()
    count=0
    for target in candidate_throws:
        for i,(pc,op,_) in enumerate(ins):
            if op not in IF_OPS:continue
            true_target=graph[pc][1]
            false_target=graph[pc][0]
            # An IF has a structurally discriminating successor only when
            # exactly one successor can reach the concrete fatal throw.
            truth=reaches(true_target,target)
            falsity=reaches(false_target,target)
            if truth==falsity:continue
            if not reaches(0,pc):continue
            count+=1
            src=_guard_source(code,ins,i,dex,group_call)
            sources.add(src)
            polarities.add("BRANCH_ON_TRUE_FATAL" if truth
                           else "FALLTHROUGH_FATAL")
            if abs(pc-target)<=256:
                near.add(src)
                near_polarities.add(src + "__" + (
                    "BRANCH_ON_TRUE_FATAL" if truth else "FALLTHROUGH_FATAL"))
                if op in (0x38,0x39):
                    # Distinguish Dalvik IF opcode's branch success from the
                    # *Boolean value* returned by the preceding method.
                    returns_true_fatal = (op==0x39 and truth) or (
                        op==0x38 and not truth)
                    near_result_polarities.add(src + "__" + (
                        "RESULT_TRUE_FATAL" if returns_true_fatal
                        else "RESULT_FALSE_FATAL"))
                else:
                    near_result_polarities.add(src+"__RESULT_POLARITY_UNPROVEN")
    result["exclusive_fatal_guards"]=min(count,32)
    result["guard_source_categories"]=sorted(sources)
    result["fatal_guard_polarities"]=sorted(polarities)
    result["near_fatal_sources"]=sorted(near)
    result["near_fatal_polarities"]=sorted(near_polarities)
    result["near_fatal_boolean_result_polarities"]=sorted(near_result_polarities)
    return result

def private_exclusive_fatal_guard_refs(code:bytes,target_strings:set[int],dex,group_call,
                                       max_distance=256):
    """Transient DEX method IDs of nearby Boolean guards, never serialized.

    Only a move-result directly preceded by an invoke and verified via exact
    CFG reachability is considered. No vendor symbols or code leave the runner.
    """
    try:
        ins=decode_instructions(code)
        pcs={p for p,_,_ in ins}
        graph={p:_nexts(code,(p,op,size),pcs) for p,op,size in ins}
    except FlowDecodeError:return set()
    strings=[p for p,op,_ in ins if
             (op==0x1a and struct.unpack_from("<H",code,p+2)[0] in target_strings)
             or (op==0x1b and struct.unpack_from("<I",code,p+2)[0] in target_strings)]
    throws={p for p,op,_ in ins if op==0x27}
    candidates={min((p for p in throws if st<p<=st+256),default=-1)
                for st in strings}-{-1}
    refs=set()
    def can_reach(a,target):
        stack=[a];seen=set()
        while stack:
            p=stack.pop()
            if p==target:return True
            if p in seen:continue
            seen.add(p)
            stack.extend(q for q in graph.get(p,[]) if q not in seen)
        return False
    for target in candidates:
        for i,(pc,op,_) in enumerate(ins):
            if op not in range(0x38,0x3e) or i<2:continue
            if not (0<target-pc<=max_distance):continue
            if can_reach(graph[pc][0],target)==can_reach(graph[pc][1],target):
                continue
            result_pc,result_op,_=ins[i-1]
            call_pc,call_op,_=ins[i-2]
            if result_op not in (0x0a,0x0b,0x0c) or call_op not in (
                    *range(0x6e,0x73),*range(0x74,0x79),0xfa,0xfb):
                continue
            if code[result_pc+1]!=code[pc+1]:continue
            ref=struct.unpack_from("<H",code,call_pc+2)[0]
            if ref>=dex.method_count or not dex.method_returns_boolean(ref):
                continue
            owner,name=dex.method(ref)
            if group_call(owner,name) in (
                    "PUSH_IMPL_HELPER","PUSH_COMMON",
                    "PUSH_OTHER_HELPER","PUSH_UTILS"):
                refs.add(ref)
    return refs
