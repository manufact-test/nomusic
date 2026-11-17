#!/usr/bin/env python3
"""Signed NAV17: only concrete implementations of the exact native renderer k.while()LR29;.
No generic renderer/audio/ByteBuffer scan. Never read runtime data, private fields, IDs or audio.
The resulting static getter body does NOT prove a currently active decoder.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
import lft2_class_inspection as trusted
audit=trusted.audit

RENDERER="Landroidx/media3/exoplayer/k;"
ALT_RENDERER="Landroidx/media3/exoplayer/l;"
STREAM="LR29;"
GETTER_NAME="while"
GETTER_DESC="()LR29;"
MAX_CLASS_NODES=180000
MAX_REACHABLE_RENDERERS=100
MAX_METHOD_ROWS=120
MAX_GETTER_INSNS=130
MAX_EVENT_COUNT=80

def directly_matches_renderer(definition):
    return RENDERER in definition["interfaces"] or definition["parent"]==RENDERER

def descendants_from_renderer(definitions):
    if RENDERER not in definitions:
        raise ValueError("RENDERER_EXACT_INTERFACE_MISSING")
    reachable={RENDERER}
    for _ in range(50):
        new={name for name,definition in definitions.items()
             if name not in reachable and
             (definition["parent"] in reachable or
              set(definition["interfaces"]) & reachable)}
        if not new:
            return reachable
        reachable.update(new)
        if len(reachable)>MAX_REACHABLE_RENDERERS:
            raise ValueError("RENDERER_EXACT_SUBTREE_TOO_LARGE")
    raise ValueError("RENDERER_ANCESTRY_DEPTH_LIMIT")

def declared_interfaces(dex, off):
    if not off:return []
    count=dex.u32(off)
    if count>48: raise ValueError("RENDERER_CLASS_INTERFACE_COUNT_LIMIT")
    dex.bounds(off+4,count*2)
    return [dex.descriptor(dex.u16(off+4+2*j)) for j in range(count)]


CONCRETE_GETTER=("Landroidx/media3/exoplayer/b;","while","()LR29;")
MAX_MATCHED_OWNER_METHODS=1800
MAX_EXACT_FIELD_SITE_ROWS=130

def confirm_direct_reference_getter(method_entry):
    dex,flags,off=method_entry
    if not off:raise ValueError("RENDERER_CONCRETE_GETTER_BODY_REQUIRED")
    insns=list(audit.instructions(dex,off))
    if len(insns)>8:raise ValueError("RENDERER_GETTER_TOO_COMPLEX")
    fields=[(pc,op,words) for pc,op,words in insns if op==0x54]
    returns=[(pc,op,words) for pc,op,words in insns if op==0x11]
    if len(fields)!=1 or len(returns)!=1:
        raise ValueError("RENDERER_GETTER_SHAPE_MISMATCH")
    pc,op,words=fields[0]
    owner,private,type_=audit.field_id(dex,words[1])
    if owner!=CONCRETE_GETTER[0] or type_!=STREAM:
        raise ValueError("RENDERER_GETTER_TYPED_FIELD_MISMATCH")
    read_reg=(words[0]>>8)&0x0f
    return_reg=(returns[0][2][0]>>8)&0xff
    if read_reg!=return_reg or not pc<returns[0][0]:
        raise ValueError("RENDERER_GETTER_FIELD_TO_RETURN_ALIAS_MISMATCH")
    for intermediate_pc,opcode,raw in insns:
        if pc < intermediate_pc < returns[0][0]:
            if audit.written_register(opcode,raw)==read_reg:
                raise ValueError("RENDERER_GETTER_RESULT_OVERWRITTEN")
    return (owner,private,type_)

def inspect_exact_attached_stream_field(apks,reachable,all_getters):
    if CONCRETE_GETTER not in all_getters:
        raise ValueError("RENDERER_CONCRETE_GETTER_NOT_DEFINED")
    field=confirm_direct_reference_getter(all_getters[CONCRETE_GETTER])
    used=[]
    inspected=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                dex=audit.Dex(archive.read(entry.filename))
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if method[0] not in reachable or not off:continue
                    inspected+=1
                    if inspected>MAX_MATCHED_OWNER_METHODS:
                        raise ValueError("RENDERER_SCOPED_OWNER_METHOD_LIMIT")
                    sites=[]
                    for pc,op,words in audit.instructions(dex,off):
                        if op not in (0x54,0x5b):continue
                        if audit.field_id(dex,words[1]) != field:continue
                        sites.append({"pc":pc,
                            "operation":"READ" if op==0x54 else "WRITE",
                            "value_register":(words[0]>>8)&15,
                            "receiver_register":(words[0]>>12)&15})
                    if sites:
                        used.append({"method":list(method),"sites":sites})
                        if len(used)>MAX_EXACT_FIELD_SITE_ROWS:
                            raise ValueError("RENDERER_EXACT_FIELD_SITE_LIMIT")
    if not used or not any(e["operation"]=="WRITE" for row in used for e in row["sites"]):
        raise ValueError("RENDERER_ATTACHED_STREAM_NO_EXACT_WRITES")
    return {"inherited_getter_returns_exact_attached_stream_field":True,
            "exact_renderer_reachable_method_count":inspected,
            "methods_touching_same_exact_field":used,
            "private_attached_field_name_or_values_exported":False,
            "actual_live_attachment_verified":False}


RENDERER_BASE="Landroidx/media3/exoplayer/b;"
ENGINE_OWNER="Landroidx/media3/exoplayer/e;"
ATTACH_DESCRIPTOR="([LSr4;LR29;JJLSl6$b;)V"
EXACT_ATTACH=(RENDERER_BASE,"package",ATTACH_DESCRIPTOR)
MAX_ENGINE_METHODS=220
MAX_ENGINE_ATTACH_CALLS=36

def inspect_exact_native_stream_attachment(methods, getter_methods, exact_field_events):
    """Narrow known b.package (stream attach) + Exo engine/e invokes only.
    No signed user data, field values, audio, or broad renderer operations."""
    if EXACT_ATTACH not in methods or not methods[EXACT_ATTACH][2]:
        raise ValueError("RENDERER_EXACT_STREAM_SETTER_NOT_DEFINED")
    dex,flags,off=methods[EXACT_ATTACH]
    insns=list(audit.instructions(dex,off))
    if len(insns)>100:raise ValueError("RENDERER_SETTER_METHOD_TOO_LARGE")
    if CONCRETE_GETTER not in getter_methods:
        raise ValueError("RENDERER_GETTER_FOR_SETTER_IDENTITY_MISSING")
    field=confirm_direct_reference_getter(getter_methods[CONCRETE_GETTER])
    # exact b.package field write proven in previous bounded signed CI:
    pc7=[(op,words) for pc,op,words in insns if pc==7]
    if len(pc7)!=1 or pc7[0][0]!=0x5b:
        raise ValueError("RENDERER_EXACT_SETTER_IPUT_PC_MISSING")
    words=pc7[0][1]
    if audit.field_id(dex,words[1])!=field:
        raise ValueError("RENDERER_EXACT_SETTER_NOT_SAME_FIELD_AS_GETTER")
    set_value=(words[0]>>8)&15
    set_receiver=(words[0]>>12)&15
    registers=dex.u16(off)
    incoming_words=dex.u16(off+2)
    # non-static package([LSr4; LR29; JJ LSl6$b) receives exactly 9 registers:
    # receiver, objects + four wide argument words + period-id object.
    if flags&0x8:
        raise ValueError("RENDERER_EXACT_SETTER_UNEXPECTED_STATIC")
    types=audit.expand_invoke_register_types(RENDERER_BASE,audit.parse_types(ATTACH_DESCRIPTOR),False)
    parameter_types=[t for t in types if t is not None]
    # Stronger than type-name guess: require exact incoming parameter register
    # flows unchanged into the stored renderer field at the observed PC.
    arg_start=registers-incoming_words
    if arg_start<0 or STREAM not in parameter_types:
        raise ValueError("RENDERER_SETTER_INCOMING_ARGUMENT_LAYOUT")
    stream_logical_index=parameter_types.index(STREAM)
    # expand_invoke_register_types includes None for the second word of J/D.
    stream_reg=arg_start+types.index(STREAM)
    this_reg=arg_start
    if stream_reg!=set_value or this_reg!=set_receiver:
        raise ValueError("RENDERER_SETTER_STREAM_ARGUMENT_FIELD_ALIAS_MISMATCH")
    # The renderer uses this stream as attached state; no sound implied.
    direct_calls=[]
    engine_methods=0
    for method,(this_dex,engine_flags,engine_off) in methods.items():
        if method[0]!=ENGINE_OWNER or not engine_off:continue
        engine_methods+=1
        if engine_methods>MAX_ENGINE_METHODS:
            raise ValueError("RENDERER_ENGINE_METHOD_SCAN_LIMIT")
        for pc,opcode,raw in audit.instructions(this_dex,engine_off):
            if opcode not in audit.INVOKES or not (0x6e<=opcode<=0x78):
                continue
            callee=this_dex.method(raw[1])
            if (callee[0] in (RENDERER,RENDERER_BASE,ALT_RENDERER)
                    and callee[2]==ATTACH_DESCRIPTOR):
                direct_calls.append({"caller":list(method),"pc":pc,
                                     "callee":list(callee),
                                     "arg_registers":audit.invoke_registers(opcode,raw)})
                if len(direct_calls)>MAX_ENGINE_ATTACH_CALLS:
                    raise ValueError("RENDERER_EXACT_ENGINE_ATTACH_CALL_LIMIT")
    return {
        "exact_native_renderer_b_attachment_method":list(EXACT_ATTACH),
        "setter_pc":7,
        "same_exact_stream_field_in_setter_and_getter":True,
        "same_incoming_LR29_argument_written_to_renderer_field":True,
        "single_renderer_instance_receiver":True,
        "native_engine_methods_scoped":engine_methods,
        "native_engine_exact_renderer_attach_calls":direct_calls,
        "actual_renderer_current_decoder_or_audio_confirmed":False,
        "private_field_names_values_ids_urls_or_stream_data_exported":False,
    }


NATIVE_ATTACH_CALLEES=frozenset({
    (RENDERER,"package",ATTACH_DESCRIPTOR),
    (RENDERER_BASE,"package",ATTACH_DESCRIPTOR),
    (ALT_RENDERER,"package",ATTACH_DESCRIPTOR),
})
MAX_EXACT_ATTACH_REFERENCES=64
def find_exact_native_attach_callers(apks):
    """One exact renderer-attachment method descriptor, not generic renderer scan."""
    matched=[]
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):continue
                dex=audit.Dex(archive.read(entry.filename))
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if not off:continue
                    for pc,opcode,words in audit.instructions(dex,off):
                        if opcode not in audit.INVOKES or not (0x6e<=opcode<=0x78):
                            continue
                        callee=dex.method(words[1])
                        if callee not in NATIVE_ATTACH_CALLEES:
                            continue
                        matched.append({"caller":list(method),"pc":pc,"callee":list(callee),
                                        "invoke_opcode":opcode,
                                        "arguments":audit.invoke_registers(opcode,words)})
                        if len(matched)>MAX_EXACT_ATTACH_REFERENCES:
                            raise ValueError("RENDERER_EXACT_ATTACH_CALLERS_LIMIT")
    return {"exact_signed_renderer_attach_method_calls":matched,
            "one_exact_signature_only":True,
            "live_selected_audio_confirmed":False,
            "private_fields_and_audio_not_read":True}

def scan_signed(apks):
    dexes=0
    definitions={}
    method_bodies={}
    exact_owner_methods={}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for ent in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",ent.filename):continue
                if ent.file_size>audit.DEX_MAX:
                    raise ValueError("RENDERER_SIGNED_DEX_SIZE_LIMIT")
                dex=audit.Dex(archive.read(ent.filename))
                dexes+=1
                for index in range(dex.class_count):
                    off=dex.class_offset+index*32
                    name=dex.descriptor(dex.u32(off))
                    if name in definitions:raise ValueError("RENDERER_DUPLICATE_SIGNED_CLASS")
                    parent_idx=dex.u32(off+8)
                    parent=None if parent_idx==0xffffffff else dex.descriptor(parent_idx)
                    interfaces=declared_interfaces(dex,dex.u32(off+12))
                    definitions[name]={"parent":parent,"interfaces":interfaces,"flags":dex.u32(off+4)}
                    if len(definitions)>MAX_CLASS_NODES:raise ValueError("RENDERER_CLASS_GRAPH_LIMIT")
                for method,flags,code_off in audit.method_definitions_with_flags(dex):
                    if method[0] in (ENGINE_OWNER,RENDERER_BASE):
                        if method in exact_owner_methods:raise ValueError("RENDERER_ENGINE_METHOD_DUPLICATE")
                        exact_owner_methods[method]=(dex,flags,code_off)
                    if method[1]!=GETTER_NAME or method[2]!=GETTER_DESC:
                        continue
                    if method in method_bodies:
                        raise ValueError("RENDERER_DUPLICATE_GETTER")
                    method_bodies[method]=(dex,flags,code_off)
                    if len(method_bodies)>MAX_METHOD_ROWS:
                        raise ValueError("RENDERER_METHOD_GETTER_LIMIT")
    if dexes!=6:raise ValueError("RENDERER_SIGNED_SIX_DEX_REQUIRED")
    reachable=descendants_from_renderer(definitions)
    if RENDERER not in reachable or len(reachable)<2:
        raise ValueError("RENDERER_NO_IMPL_IN_SIGNED_DEX")
    direct=sorted(x for x in reachable if x!=RENDERER and directly_matches_renderer(definitions[x]))
    rows=[]
    for owner in sorted(reachable):
        definition=definitions[owner]
        method=(owner,GETTER_NAME,GETTER_DESC)
        row={"type":owner,"parent":definition["parent"],
             "interfaces":[x for x in definition["interfaces"] if x in reachable or x==ALT_RENDERER],
             "is_interface":bool(definition["flags"]&0x200),
             "is_abstract":bool(definition["flags"]&0x400),
             "getter_declared":method in method_bodies}
        if method in method_bodies:
            dex,flags,off=method_bodies[method]
            row["getter_has_code"]=bool(off)
            if off:
                insns=list(audit.instructions(dex,off))
                if len(insns)>MAX_GETTER_INSNS:
                    raise ValueError("RENDERER_CONCRETE_GETTER_TOO_LARGE")
                events=[]
                for pc,op,words in insns:
                    if 0x52<=op<=0x6d:
                        decl,_private,typ=audit.field_id(dex,words[1])
                        if typ==STREAM:
                            events.append({"pc":pc,"kind":"GET_STREAM_FIELD" if op<=0x58 else "SET_STREAM_FIELD",
                                           "declaring_owner":decl,"type":typ,"op":op})
                    if op in audit.INVOKES and 0x6e<=op<=0x78:
                        dest=dex.method(words[1])
                        if dest[2].split(")",1)[1]==STREAM:
                            events.append({"pc":pc,"kind":"CALL_RETURNING_STREAM",
                                           "callee":[dest[0],dest[1],dest[2]]})
                    if op==0x11:
                        events.append({"pc":pc,"kind":"RETURN_OBJECT"})
                    if len(events)>MAX_EVENT_COUNT:
                        raise ValueError("RENDERER_GETTER_EVENT_LIMIT")
                row["getter_instructions"]=len(insns)
                row["getter_scoped_events"]=events
        rows.append(row)
    attached=inspect_exact_attached_stream_field(apks,reachable,method_bodies)
    attach=inspect_exact_native_stream_attachment(exact_owner_methods,method_bodies,attached)
    exact_attach_callers=find_exact_native_attach_callers(apks)
    return {"signed_exact_renderer_stream_attach_callers":exact_attach_callers,
            "exact_native_renderer_stream_attachment":attach,
            "exact_inherited_renderer_attached_stream_field_uses":attached,
            "verdict":"EXACT_SIGNED_RENDERER_INTERFACE_CONCRETE_GETTER_MAP_STATIC_ONLY",
            "signed_dex_count":dexes,"renderer_interface":RENDERER,
            "exact_getter_descriptor":GETTER_DESC,
            "reachable_class_count":len(reachable),
            "direct_implementer_count":len(direct),
            "direct_implementers":direct,
            "concrete_getter_rows":rows,
            "actual_live_attached_renderer_or_decoder_confirmed":False,
            "no_runtime_or_private_field_values_read":True}

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("RENDERER_EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("RENDERER_PINNED_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("RENDERER_PINNED_XAPK_HASH_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-renderer-exact-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:raise ValueError("RENDERER_PINNED_SPLITS_REQUIRED")
        if audit.verify_split_set(apks).get("verified_issuer_signed_splits")!=16:
            raise ValueError("RENDERER_PUBLISHER_SIGNATURE_MISMATCH")
        base=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if (meta.get("name")!=trusted.EXPECTED_PACKAGE or
                meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE):
                raise ValueError("RENDERER_PINNED_YANDEX_VERSION_MISMATCH")
            if not meta.get("split"):base.append(apk)
        if len(base)!=1 or trusted.sha256_file(base[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("RENDERER_NAV17_BASE_MISMATCH")
        out=scan_signed(apks)
    return {**out,"publisher_signed_original_verified":True,"original_input_ephemerally_deleted":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",required=True,type=Path)
    a=p.parse_args()
    try:print(json.dumps(run(a.xapk),sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as exc:
        message=str(exc)
        print(json.dumps({"verdict":"RENDERER_CONCRETE_GETTER_INCOMPLETE",
                          "safe_error_code":message if re.fullmatch("[A-Z0-9_]{1,90}",message) else None,
                          "actual_live_attached_renderer_or_decoder_confirmed":False}))
        raise SystemExit(2)
