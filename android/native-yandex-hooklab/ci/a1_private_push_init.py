"""Private, exact-width read-only triage of legacy Push.init.

This module runs only on a disposable CI runner holding a SHA-verified publisher
XAPK. It never prints APK content, symbols, class names, method names,
identifiers, field values, or bytecode.
"""
import struct
from a1_private_dex_flow import decode_instructions, FlowDecodeError, INVOKE_METHOD

ENTRY_OWNER="Lcom/yandex/metrica/push/YandexMetricaPush;"

def _return_param_categories(dex,mid):
    ci,proto,si=struct.unpack_from("<HHI",dex.data,dex.method_off+mid*8)
    n,off=struct.unpack_from("<II",dex.data,72)
    if proto>=n or off+12*n>len(dex.data):return ["INVALID_PROTO"]
    ret,params=struct.unpack_from("<II",dex.data,off+proto*12+4)
    kinds=[]
    if params:
        if params+4>len(dex.data):return ["INVALID_PROTO"]
        total=struct.unpack_from("<I",dex.data,params)[0]
        if total>12 or params+4+2*total>len(dex.data):return ["INVALID_PROTO"]
        for k in range(total):
            i=struct.unpack_from("<H",dex.data,params+4+2*k)[0]
            desc=dex.type(i)
            kinds.append("CONTEXT" if desc=="Landroid/content/Context;"
                else "APPLICATION" if desc=="Landroid/app/Application;"
                else "STRING" if desc=="Ljava/lang/String;"
                else "PRIMITIVE" if len(desc)==1
                else "PUSH_SDK_OBJECT" if "/metrica/push/" in desc
                else "OBJECT")
    return kinds

def _type_family(owner,name,group_call):
    if owner=="Lcom/yandex/metrica/push/YandexMetricaPush;":
        return "PUSH_PUBLIC_SELF"
    if owner=="Lio/appmetrica/analytics/ModulesFacade;" and name=="isActivatedForApp":
        return "MODERN_ACTIVATED_CHECK"
    if owner.startswith("Lio/appmetrica/analytics/"):
        return "MODERN_METRICA"
    if owner.startswith("Lcom/yandex/metrica/"):
        return group_call(owner,name)
    if owner.startswith("Landroid/"):return "ANDROID_FRAMEWORK"
    if owner.startswith("Ljava/lang/"):return "JAVA_RUNTIME"
    if owner.startswith("Lru/yandex/music/"):return "MUSIC_HOST"
    return group_call(owner,name)

def inspect_legacy_push_init(binary,Dex,group_call):
    dex=Dex(binary)
    codes=dict(dex.code_methods())
    roots={mid for mid in range(dex.method_count)
           if dex.method(mid)==(ENTRY_OWNER,"init")}
    if not roots:return {"overloads":0,"param_signatures":[],
                         "body_count":0,"calls_by_depth":[[],[],[]],
                         "method_counts_by_depth":[0,0,0],
                         "unresolved_calls":False}
    signatures=sorted({",".join(_return_param_categories(dex,mid))
                       for mid in roots})
    frontier=roots
    visited=set()
    depth_categories=[]
    depth_method_counts=[]
    unresolved=False
    for depth in range(3):
        next_ids=set(); cats=set(); analyzed=0
        for mid in sorted(frontier)[:32]:
            if mid in visited:continue
            visited.add(mid)
            code=codes.get(mid)
            if code is None:continue
            analyzed+=1
            try:inst=decode_instructions(code)
            except FlowDecodeError:
                unresolved=True
                continue
            for pc,op,_ in inst:
                if op not in INVOKE_METHOD:continue
                idx=struct.unpack_from("<H",code,pc+2)[0]
                if idx>=dex.method_count:continue
                owner,name=dex.method(idx)
                category=_type_family(owner,name,group_call)
                cats.add(category)
                if category in ("PUSH_PUBLIC_SELF","PUSH_IMPL_HELPER",
                                "PUSH_OTHER_HELPER","PUSH_UTILS","PUSH_COMMON",
                                "PUSH_MODERN","MODERN_METRICA"):
                    next_ids.add(idx)
        depth_categories.append(sorted(cats))
        depth_method_counts.append(min(analyzed,32))
        frontier=next_ids-visited
    return {
        "overloads":min(len(roots),12),
        "param_signatures":signatures[:12],
        "body_count":min(len(roots & codes.keys()),12),
        "calls_by_depth":depth_categories,
        "method_counts_by_depth":depth_method_counts,
        "unresolved_calls":unresolved,
    }
