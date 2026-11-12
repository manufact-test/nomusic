"""Private Push string supplier dependency triage.

Only fixed aggregate categories leave ephemeral CI. Never expose field, method,
class, string, identifier, or raw DEX bytecode.
"""
import struct
from a1_private_dex_flow import (
    decode_instructions, FlowDecodeError, INVOKE_METHOD,
    private_push_utils_supplier_refs,
)

def _family(owner, name, group_call):
    family=group_call(owner,name)
    if owner.startswith("Landroid/content/") and name in (
            "getPackageName","getApplicationContext","getSharedPreferences"):
        return "ANDROID_CONTEXT"
    if owner.startswith("Landroid/") and family=="ANDROID_FRAMEWORK":
        return "ANDROID_OTHER"
    if owner=="Ljava/lang/reflect/Method;":
        return {"invoke":"REFLECTION_INVOKE",
                "setAccessible":"REFLECTION_ACCESSIBILITY"}.get(name,"REFLECTION_METHOD_OTHER")
    if owner=="Ljava/lang/reflect/AccessibleObject;":
        return {"setAccessible":"REFLECTION_ACCESSIBILITY"}.get(name,"REFLECTION_ACCESSIBLE_OTHER")
    if family=="JAVA_RUNTIME":
        if owner=="Ljava/lang/String;":
            return {
                "length":"STRING_LENGTH",
                "equals":"STRING_EQUALS",
                "valueOf":"STRING_VALUEOF",
                "concat":"STRING_CONCAT",
                "isEmpty":"STRING_ISEMPTY",
                "toString":"STRING_TOSTRING",
            }.get(name,"STRING_OTHER")
        if owner=="Ljava/lang/StringBuilder;":
            return {
                "<init>":"STRINGBUILDER_CTOR",
                "append":"STRINGBUILDER_APPEND",
                "toString":"STRINGBUILDER_FINISH",
            }.get(name,"STRINGBUILDER_OTHER")
        if owner=="Ljava/lang/System;":
            return {
                "getProperty":"SYSTEM_PROPERTY",
                "getenv":"SYSTEM_ENVIRONMENT",
                "currentTimeMillis":"SYSTEM_CLOCK",
            }.get(name,"SYSTEM_OTHER")
        if owner=="Ljava/lang/Class;":
            return {
                "getName":"REFLECT_CLASS_NAME",
                "forName":"REFLECT_CLASS_FORNAME",
                "getSimpleName":"REFLECT_SIMPLE_NAME",
                "getMethod":"REFLECT_CLASS_GET_METHOD",
                "getDeclaredMethod":"REFLECT_CLASS_DECLARED_METHOD",
                "getField":"REFLECT_CLASS_GET_FIELD",
                "getDeclaredField":"REFLECT_CLASS_DECLARED_FIELD",
                "newInstance":"REFLECT_CLASS_NEW_INSTANCE",
                "getClassLoader":"REFLECT_CLASS_LOADER",
                "isAssignableFrom":"REFLECT_ASSIGNABLE",
                "getDeclaredMethods":"REFLECT_DECLARED_METHODS",
            }.get(name,"REFLECT_CLASS_OTHER")
        if owner=="Ljava/lang/Object;":
            return {
                "getClass":"OBJECT_GET_CLASS",
                "toString":"OBJECT_TOSTRING",
            }.get(name,"OBJECT_OTHER")
        if owner=="Ljava/lang/Throwable;":
            return {
                "getMessage":"THROWABLE_MESSAGE",
                "toString":"THROWABLE_TOSTRING",
            }.get(name,"THROWABLE_OTHER")
        return "JAVA_RUNTIME_OTHER"
    return family

def _field_category(dex, field_id, group_call):
    if len(dex.data)<88:return ("UNKNOWN","UNKNOWN")
    size,off=struct.unpack_from("<II",dex.data,80)
    if field_id>=size or off+size*8>len(dex.data):
        return ("UNKNOWN","UNKNOWN")
    cl,ftype,_=struct.unpack_from("<HHI",dex.data,off+field_id*8)
    owner=dex.type(cl)
    desc=dex.type(ftype)
    if desc=="Ljava/lang/String;": typ="STRING"
    elif desc=="Z": typ="BOOLEAN"
    elif len(desc)==1: typ="PRIMITIVE"
    elif desc.startswith(("L","[")):typ="OBJECT"
    else:typ="UNKNOWN"
    return group_call(owner,"field"),typ

def _literal_family(s):
    # Never emit input text or any raw constant from vendor bytecode.
    if s.startswith("io.appmetrica.analytics."):return "APPMETRICA_CLASS"
    if s.startswith("com.yandex.metrica.push."):return "PUSH_CLASS"
    if s.startswith("com.yandex.metrica."):return "YANDEX_METRICA_CLASS"
    if s.startswith("com.google.firebase."):return "FIREBASE_CLASS"
    if s.startswith("com.google.android.gms."):return "GOOGLE_GMS_CLASS"
    if s.startswith("ru.yandex.music."):return "MUSIC_CLASS"
    if s=="android.os.SystemProperties":return "ANDROID_SYSTEM_PROPERTIES_CLASS"
    if s=="android.app.ActivityThread":return "ANDROID_ACTIVITY_THREAD_CLASS"
    if s=="android.app.AppGlobals":return "ANDROID_APP_GLOBALS_CLASS"
    if s=="android.os.Build":return "ANDROID_BUILD_CLASS"
    if s=="android.util.Log":return "ANDROID_LOG_CLASS"
    if s.startswith("android."):return "ANDROID_OTHER_CLASS"
    if s.startswith("java."):return "JAVA_CLASS"
    if s in ("get","getInt","getBoolean","getLong","set"):
        return "REFLECT_METHOD_PROPERTY"
    if s=="currentApplication":return "REFLECT_METHOD_CURRENT_APPLICATION"
    if s=="currentActivityThread":return "REFLECT_METHOD_CURRENT_THREAD"
    if s=="getInitialApplication":return "REFLECT_METHOD_INITIAL_APPLICATION"
    if s=="currentProcessName":return "REFLECT_METHOD_PROCESS_NAME"
    return "OTHER_LITERAL"


def inspect_source_chain(dex, source_code, initial, group_call):
    """Follow just concrete declared method IDs at depths <=3."""
    visited=set()
    frontier=set(initial)
    depths=[]
    for _ in range(3):
        found=set(); new_refs=set(); refs=set();fields=set(); literals=set()
        catches=False
        for method_id in sorted(frontier)[:24]:
            if method_id in visited or method_id not in source_code:
                continue
            visited.add(method_id)
            found.add(method_id)
            try:ins=decode_instructions(source_code[method_id])
            except FlowDecodeError:continue
            code=source_code[method_id]
            for pc,op,_ in ins:
                if op==0x0d:catches=True
                if op==0x1a:
                    idx=struct.unpack_from("<H",code,pc+2)[0]
                    if idx<dex.string_count:literals.add(_literal_family(dex.string(idx)))
                elif op==0x1b:
                    idx=struct.unpack_from("<I",code,pc+2)[0]
                    if idx<dex.string_count:literals.add(_literal_family(dex.string(idx)))
                if op in INVOKE_METHOD:
                    ref=struct.unpack_from("<H",code,pc+2)[0]
                    if ref>=dex.method_count:continue
                    owner,name=dex.method(ref)
                    refs.add(_family(owner,name,group_call))
                    if group_call(owner,name) in (
                            "PUSH_UTILS","PUSH_IMPL_HELPER",
                            "PUSH_COMMON","PUSH_OTHER_HELPER"):
                        new_refs.add(ref)
                if op in range(0x52,0x6e):
                    field_id=struct.unpack_from("<H",code,pc+2)[0]
                    owner,typ=_field_category(dex,field_id,group_call)
                    read=op in range(0x52,0x59) or op in range(0x60,0x67)
                    fields.add(("READ_" if read else "WRITE_")+owner+"_"+typ)
        depths.append({
            "methods_with_body_bounded":min(len(found),16),
            "calls":sorted(refs),
            "fields":sorted(fields),
            "literal_families":sorted(literals),
            "catch_handler_instruction_seen":catches,
            "has_more_push_helpers":bool(new_refs),
        })
        frontier=new_refs-visited
    return depths

def classify_private_supplier_chain(binary,Dex,group_class,group_call,
                                   exact_error_guard_report):
    dex=Dex(binary)
    targets=dex.possible_error_strings()
    if not targets:return None
    source={}
    roots=set()
    for mid,code in dex.code_methods():
        owner,name=dex.method(mid)
        if group_class(owner) in ("PUSH_IMPL","PUSH_OTHER","PUSH_MODERN"):
            source[mid]=code
        if group_class(owner)=="PUSH_IMPL" and name=="a":
            report=exact_error_guard_report(code,targets,dex,group_call)
            if report["decoded"] and report["target_strings"]:
                roots.update(private_push_utils_supplier_refs(
                    code,targets,dex,group_call))
    if not roots:return None
    return inspect_source_chain(dex,source,roots,group_call)
