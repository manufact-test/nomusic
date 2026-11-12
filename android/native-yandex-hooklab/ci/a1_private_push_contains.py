"""Private exact DEX String.contains operand provenance, fixed enums only.

No raw vendor literal, method, class, identifier, APK or bytecode is exposed.
All inference is conservative and never changes the clone.
"""
import struct
from a1_private_dex_flow import decode_instructions,FlowDecodeError,INVOKE_METHOD

def _literal_family(value):
    if value=="":return "EMPTY"
    if value==":":return "PROCESS_SEPARATOR"
    if value==":metrica":return "METRICA_PROCESS_SUFFIX"
    if value=="ru.yandex.music":return "STOCK_PACKAGE_LITERAL"
    if value=="pro.celikom.yandex.nativeclonelab":return "CLONE_PACKAGE_LITERAL"
    if value.startswith("ru.yandex.music:"):return "STOCK_PROCESS_SUFFIX"
    if value.startswith("pro.celikom.yandex.nativeclonelab:"):
        return "CLONE_PROCESS_SUFFIX"
    if value.startswith(("io.appmetrica.","com.yandex.metrica.")):
        return "METRICA_NAMESPACE"
    if value.startswith("ru.yandex."):return "YANDEX_NAMESPACE"
    return "OTHER_LITERAL"

def _reg_source(dex,inst,code,start_idx,reg,group_call):
    for i in range(start_idx-1,max(-1,start_idx-90),-1):
        pc,op,_=inst[i]
        if op in (0x07,0x01,0x04) and (code[pc+1]&15)==reg:
            reg=code[pc+1]>>4
            continue
        if op in (0x08,0x02,0x05) and code[pc+1]==reg:
            reg=struct.unpack_from("<H",code,pc+2)[0]
            continue
        if op in (0x09,0x03,0x06) and struct.unpack_from(
                "<H",code,pc+2)[0]==reg:
            reg=struct.unpack_from("<H",code,pc+4)[0]
            continue
        if op in (0x1a,0x1b) and code[pc+1]==reg:
            index=(struct.unpack_from("<H",code,pc+2)[0] if op==0x1a
                   else struct.unpack_from("<I",code,pc+2)[0])
            if index<dex.string_count:return _literal_family(dex.string(index))
            return "UNKNOWN_STRING_REF"
        if op==0x0c and code[pc+1]==reg:
            if i>0:
                before,callop,_=inst[i-1]
                if callop in INVOKE_METHOD:
                    mid=struct.unpack_from("<H",code,before+2)[0]
                    if mid<dex.method_count:
                        owner,name=dex.method(mid)
                        cat=group_call(owner,name)
                        return "CALL_"+cat
            return "UNKNOWN_RESULT"
        if 0x52<=op<=0x6d and (code[pc+1]&15)==reg:
            return "FIELD_VALUE"
    return "UNRESOLVED"

def inspect_push_contains(binary,Dex,group_class,group_call,exact_fatal_cfg):
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return []
    insights=[]
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner)!="PUSH_IMPL" or name!="a":continue
        cfg=exact_fatal_cfg(code,targets,dex,group_call)
        if not cfg["decoded"] or not cfg["fatal_throw_candidates"]:continue
        try:inst=decode_instructions(code)
        except FlowDecodeError:continue
        for j,(pc,op,_) in enumerate(inst):
            if op not in range(0x6e,0x79):continue
            ref=struct.unpack_from("<H",code,pc+2)[0]
            if ref>=dex.method_count or dex.method(ref)!=(
                    "Ljava/lang/String;","contains"):
                continue
            if op<0x74:
                count=code[pc+1]>>4
                receiver=code[pc+4]&15
                argument=code[pc+4]>>4
            else:
                count=code[pc+1]
                receiver=struct.unpack_from("<H",code,pc+4)[0]
                argument=receiver+1
            if count!=2:continue
            source=_reg_source(dex,inst,code,j,argument,group_call)
            receiver_source=_reg_source(dex,inst,code,j,receiver,group_call)
            guarded=(j+2<len(inst) and inst[j+1][1]==0x0a
                     and inst[j+2][1] in range(0x32,0x3e))
            insights.append({"argument":source,"receiver":receiver_source,
                             "direct_guard":guarded})
    return insights
