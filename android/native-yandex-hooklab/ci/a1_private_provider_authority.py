"""Read-only exact private DEX provider-authority cross-reference triage.

Publishes ONLY fixed categories and capped booleans; no original APK, method,
literal, class, secret, credential or bytecode is logged.
"""
import struct
from a1_private_dex_flow import decode_instructions,FlowDecodeError,INVOKE_METHOD

def _sdk_call_category(owner,name):
    if owner=="Landroid/content/ContentResolver;":
        return {
            "query":"RESOLVER_QUERY","call":"RESOLVER_CALL",
            "getType":"RESOLVER_GET_TYPE",
            "acquireContentProviderClient":"RESOLVER_ACQUIRE_CLIENT",
            "openInputStream":"RESOLVER_OPEN_INPUT",
            "openFileDescriptor":"RESOLVER_OPEN_DESCRIPTOR",
            "insert":"RESOLVER_INSERT","update":"RESOLVER_UPDATE",
            "delete":"RESOLVER_DELETE",
        }.get(name,"RESOLVER_OTHER")
    if owner=="Landroid/content/Context;":
        return {
            "getContentResolver":"CONTEXT_GET_RESOLVER",
            "getPackageName":"CONTEXT_GET_PACKAGE",
        }.get(name,"CONTEXT_OTHER")
    if owner=="Landroid/net/Uri;":
        return {"parse":"URI_PARSE","getAuthority":"URI_AUTHORITY"
               }.get(name,"URI_OTHER")
    if owner=="Landroid/content/ContentProviderClient;":
        return {"call":"CLIENT_CALL","query":"CLIENT_QUERY"
               }.get(name,"CLIENT_OTHER")
    if owner.startswith("Lio/appmetrica/analytics/"):
        return "MODERN_METRICA_INTERNAL"
    if owner.startswith("Landroid/"):return "ANDROID_OTHER"
    return "OTHER_CALL"


def inspect_authority_refs(binary,Dex,group_class):
    dex=Dex(binary)
    # The public identifier is already in our OWN manifest rewrite source.
    global_marker="com.yandex.preinstallsatellite.appmetrica.provider"
    candidates=set()
    for idx in range(dex.string_count):
        s=dex.string(idx)
        if s==global_marker:
            candidates.add(idx)
    if not candidates:return {"literal_found":False,"method_groups":[],
                               "methods_referencing_bounded":0,
                               "call_api_cooccurrences":[],
                               "literal_followed_by_uri_parse_bounded":0,
                               "literal_followed_by_resolver_query_bounded":0}
    methods=set()
    calls=set()
    parse_after=0
    query_after=0
    for mid,code in dex.code_methods():
        try:ins=decode_instructions(code)
        except FlowDecodeError:continue
        refs=[]
        call_refs=[]
        instructions=[]
        for pc,op,_ in ins:
            if op in INVOKE_METHOD:
                ref=struct.unpack_from("<H",code,pc+2)[0]
                if ref<dex.method_count:
                    call_refs.append(ref)
                    callee,name=dex.method(ref)
                    instructions.append((pc,_sdk_call_category(callee,name)))
            if op==0x1a:
                idx=struct.unpack_from("<H",code,pc+2)[0]
            elif op==0x1b:
                idx=struct.unpack_from("<I",code,pc+2)[0]
            else:continue
            if idx in candidates:refs.append(pc)
        if refs:
            owner,name=dex.method(mid)
            if owner.startswith("Lio/appmetrica/analytics/"):
                cat="MODERN_METRICA"
            elif owner.startswith("Lru/yandex/music/"):
                cat="MUSIC_HOST"
            else:
                cat=group_class(owner)
            methods.add((mid,cat))
            if any(kind=="URI_PARSE" and 0<callpc-litpc<=1024
                   for litpc in refs for callpc,kind in instructions):
                parse_after+=1
            if any(kind=="RESOLVER_QUERY" and 0<callpc-litpc<=2048
                   for litpc in refs for callpc,kind in instructions):
                query_after+=1
            for ref in call_refs:
                callee,method=dex.method(ref)
                calls.add(_sdk_call_category(callee,method))
    return {"literal_found":True,
            "method_groups":sorted({cat for _,cat in methods}),
            "methods_referencing_bounded":min(len(methods),32),
            "call_api_cooccurrences":sorted(calls)[:24],
            "literal_followed_by_uri_parse_bounded":min(parse_after,16),
            "literal_followed_by_resolver_query_bounded":min(query_after,16)}
