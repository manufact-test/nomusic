"""Read-only exact private DEX provider-authority cross-reference triage.

Publishes ONLY fixed categories and capped booleans; no original APK, method,
literal, class, secret, credential or bytecode is logged.
"""
import struct
from a1_private_dex_flow import decode_instructions,FlowDecodeError

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
                               "methods_referencing_bounded":0}
    methods=set()
    for mid,code in dex.code_methods():
        try:ins=decode_instructions(code)
        except FlowDecodeError:continue
        for pc,op,_ in ins:
            if op==0x1a:
                idx=struct.unpack_from("<H",code,pc+2)[0]
            elif op==0x1b:
                idx=struct.unpack_from("<I",code,pc+2)[0]
            else:continue
            if idx in candidates:
                owner,name=dex.method(mid)
                if owner.startswith("Lio/appmetrica/analytics/"):
                    cat="MODERN_METRICA"
                elif owner.startswith("Lru/yandex/music/"):
                    cat="MUSIC_HOST"
                else:
                    cat=group_class(owner)
                methods.add((mid,cat))
    return {"literal_found":True,
            "method_groups":sorted({cat for _,cat in methods}),
            "methods_referencing_bounded":min(len(methods),32)}
