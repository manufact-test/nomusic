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
    result["exclusive_fatal_guards"]=min(count,32)
    result["guard_source_categories"]=sorted(sources)
    result["fatal_guard_polarities"]=sorted(polarities)
    result["near_fatal_sources"]=sorted(near)
    return result
