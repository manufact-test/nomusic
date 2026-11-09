#!/usr/bin/env python3
"""Read-only bytecode invocation neighbors for Yandex native file-info APIs.

Only class/method signatures and bounded call graph; no request bodies, OAuth,
user data, audio content or APK retained. Runtime owner / source binding is
NOT proven by an invoke-interface alone.
"""
from __future__ import annotations
from inspect_android_host import Dex,DexError
from trace_native_callers import method_definitions,invoked_method_indexes

TARGETS={
 "Lcom/yandex/music/shared/player/content/remote/fileinfo/FileInfoApi;",
 "Lcom/yandex/music/shared/player/content/remote/fileinfo/OldFileInfoApi;",
 "Lcom/yandex/music/shared/player/content/remote/downloadinfo/DownloadInfoApi;",
}
MAX_SAMPLES=55

def trace_source_api_calls(data:bytes)->dict:
    d=Dex(data)
    refs={}
    for idx in range(d.method_count):
        owner,name,sig=d.method(idx)
        if owner in TARGETS:
            refs[idx]=(owner,name,sig)
    samples=[]
    count=0
    invalid=[]
    if refs:
        for caller_idx,codeoff in method_definitions(d):
            try:
                calls=list(invoked_method_indexes(d,codeoff))
                targets=[(i,pc,target) for i,(target,pc,op) in enumerate(calls) if target in refs]
                for index,pc,target in targets:
                    count+=1
                    if len(samples)>=MAX_SAMPLES:continue
                    caller=d.method(caller_idx)
                    neighbors=[]
                    for n_idx,n_pc,n_op in calls[max(0,index-4):index+7]:
                        cl,na,sg=d.method(n_idx)
                        neighbors.append({
                            "target_class":cl,"target_method":na,"signature":sg,
                            "relative_code_unit":n_pc-pc,
                            "is_file_info_api":n_idx in refs
                        })
                    samples.append({
                        "caller_class":caller[0],"caller_method":caller[1],
                        "caller_signature":caller[2],
                        "called_api_class":refs[target][0],
                        "called_api_method":refs[target][1],
                        "called_api_signature":refs[target][2],
                        "callers_other_invocations_nearby":neighbors
                    })
            except DexError as exc:
                if len(invalid)<16:invalid.append(str(exc))
    return {
        "target_method_refs":len(refs),
        "callsite_count":count,
        "bounded_callsite_neighborhoods":samples,
        "malformed_method_count":len(invalid),
        "evidence":"STATIC_GRAPH_ONLY_NOT_YET_A_PLAYER_SOURCE_HOOK"
    }
