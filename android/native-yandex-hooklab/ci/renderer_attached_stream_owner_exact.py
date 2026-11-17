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

def scan_signed(apks):
    dexes=0
    definitions={}
    method_bodies={}
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
    return {"verdict":"EXACT_SIGNED_RENDERER_INTERFACE_CONCRETE_GETTER_MAP_STATIC_ONLY",
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
