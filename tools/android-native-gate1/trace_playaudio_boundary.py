#!/usr/bin/env python3
"""Static DEX callgraph and bounded Retrofit annotations for Yandex PlayAudioApi.

Never reads dynamic network traffic, credentials, track files, or user data.
Only interfaces/annotations baked into a publisher-signed APK are analyzed.
A Retrofit route and callsite do NOT prove the live player source selection.
"""
from __future__ import annotations

import re
from inspect_android_host import Dex, DexError
from trace_native_callers import invoked_method_indexes, method_definitions, uleb

TARGET = "Lcom/yandex/music/shared/play/audio2/data/PlayAudioApi;"
PREFIX = "Lcom/yandex/music/shared/play/audio2/"
HTTP_ANNOTATIONS = frozenset({
    "Lretrofit2/http/GET;", "Lretrofit2/http/POST;",
    "Lretrofit2/http/PUT;", "Lretrofit2/http/PATCH;",
    "Lretrofit2/http/DELETE;", "Lretrofit2/http/HTTP;",
    # Seen on official-signer PlayAudioApi.a; do NOT assume Liml is @POST yet.
    "Liml;",
})
MAX_REFS = 90
MAX_CALLS = 70
MAX_ANNOTATIONS = 40

def _annotation_strings(dex: Dex, offset: int) -> list[dict]:
    """Parse a *selected method's* annotation set; show only HTTP path 'value'."""
    if not offset:
        return []
    count = dex.u32(offset)
    if count > 32:
        raise DexError("Too many annotations")
    dex.bounds(offset + 4, count * 4)
    out = []
    for i in range(count):
        anno_off = dex.u32(offset + 4 + i * 4)
        dex.bounds(anno_off, 2)
        pos = anno_off + 1  # annotation_item visibility
        typ, pos = uleb(dex, pos)
        typ_name = dex.descriptor(typ)
        size, pos = uleb(dex, pos)
        if size > 64:
            raise DexError("Too many encoded annotation elements")
        for _ in range(size):
            name_idx, pos = uleb(dex, pos)
            key = dex.string(name_idx)
            value, pos = _encoded_value(dex, pos)
            # ONLY known HTTP annotations and literal path: no @Headers and no auth.
            if (typ_name in HTTP_ANNOTATIONS and key == "value"
                    and isinstance(value, str)
                    and re.fullmatch(r"[A-Za-z0-9_./{}?=&:%+-]{1,200}", value)):
                out.append({"annotation": typ_name, "static_path": value})
    return out

def _encoded_value(dex: Dex, offset: int, depth: int = 0):
    if depth > 10:
        raise DexError("Encoded annotation recursion overflow")
    dex.bounds(offset, 1)
    code = dex.data[offset]
    offset += 1
    value_type, arg = code & 31, code >> 5
    width = arg + 1
    if value_type in (0x00, 0x02, 0x03, 0x04, 0x06, 0x10, 0x11,
                      0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b):
        dex.bounds(offset, width)
        val = int.from_bytes(dex.data[offset:offset + width], "little")
        offset += width
        if value_type == 0x17:
            return dex.string(val), offset
        return None, offset
    if value_type == 0x1e:
        return None, offset
    if value_type == 0x1f:
        return bool(arg), offset
    if value_type == 0x1c:  # encoded array
        size, offset = uleb(dex, offset)
        if size > 512:
            raise DexError("Too many annotation array values")
        for _ in range(size):
            _, offset = _encoded_value(dex, offset, depth + 1)
        return None, offset
    if value_type == 0x1d:  # encoded annotation
        _, offset = uleb(dex, offset)
        size, offset = uleb(dex, offset)
        if size > 128:
            raise DexError("Too many nested annotation values")
        for _ in range(size):
            _, offset = uleb(dex, offset)
            _, offset = _encoded_value(dex, offset, depth + 1)
        return None, offset
    raise DexError("Unexpected DEX encoded_value type")

def _retrofit_annotations(dex: Dex) -> list[dict]:
    report = []
    for i in range(dex.class_count):
        base = dex.class_offset + i * 32
        class_name = dex.descriptor(dex.u32(base))
        if class_name != TARGET:
            continue
        off = dex.u32(base + 20)  # annotations_off
        if not off:
            return []
        class_anno_off, field_count, method_count, param_count = (
            dex.u32(off), dex.u32(off + 4), dex.u32(off + 8), dex.u32(off + 12))
        if any(x > 30000 for x in (field_count, method_count, param_count)):
            raise DexError("Oversized annotation directory")
        method_base = off + 16 + 8 * field_count
        dex.bounds(method_base, method_count * 8)
        for k in range(method_count):
            method_idx = dex.u32(method_base + 8 * k)
            set_off = dex.u32(method_base + 8 * k + 4)
            if method_idx >= dex.method_count:
                raise DexError("Invalid annotated method index")
            clazz, name, sig = dex.method(method_idx)
            if clazz != TARGET:
                raise DexError("Annotated method belongs to another class")
            for annotation in _annotation_strings(dex, set_off):
                if len(report) < MAX_ANNOTATIONS:
                    report.append({"method": name, "signature": sig, **annotation})
        return report
    return []

def _annotation_shape(dex: Dex) -> dict:
    """Describe public annotation *types* only, never opaque values/headers."""
    for i in range(dex.class_count):
        base = dex.class_offset + i * 32
        if dex.descriptor(dex.u32(base)) != TARGET:
            continue
        annotations_off = dex.u32(base + 20)
        if not annotations_off:
            return {"interface_defined": True, "annotations_directory": False}
        count_fields = dex.u32(annotations_off + 4)
        count_methods = dex.u32(annotations_off + 8)
        count_params = dex.u32(annotations_off + 12)
        if max(count_fields,count_methods,count_params) > 10000:
            raise DexError("Oversize PlayAudioApi annotation directory")
        start = annotations_off + 16 + count_fields * 8
        dex.bounds(start, count_methods * 8)
        shapes=[]
        for m in range(count_methods):
            method_idx=dex.u32(start + m * 8)
            set_off=dex.u32(start + m * 8 + 4)
            if method_idx >= dex.method_count:
                raise DexError("Annotation method id out of bounds")
            cls, name, sig = dex.method(method_idx)
            kinds=[]
            if set_off:
                number=dex.u32(set_off)
                if number > 64:
                    raise DexError("Too many interface annotations")
                dex.bounds(set_off+4,number*4)
                for k in range(number):
                    item=dex.u32(set_off + 4 + 4*k)
                    dex.bounds(item,2)
                    tid,_=uleb(dex,item+1)
                    kind=dex.descriptor(tid)
                    # Annotation TYPE names only. Obfuscation may rename @POST
                    # and related Retrofit interfaces; never print values.
                    kinds.append(kind)
            shapes.append({"method":name,"signature":sig,"types":sorted(set(kinds))})
        return {"interface_defined":True,"annotations_directory":True,
                "annotated_methods":count_methods,
                "parameter_annotation_lists":count_params,
                "method_annotation_types":shapes[:24]}
    return {"interface_defined":False,"annotations_directory":False}


def trace_playaudio(data: bytes) -> dict:
    dex = Dex(data)
    refs = {}
    names = set()
    for i in range(dex.method_count):
        cls, name, sig = dex.method(i)
        if cls.startswith(PREFIX):
            names.add(cls)
        if cls == TARGET and len(refs) < MAX_REFS:
            refs[i] = (cls, name, sig)
    core = sorted(s for s in dex.defined_classes() if s.startswith(PREFIX))
    invocations = []
    count = 0
    problems = []
    if refs:
        for idx, code_off in method_definitions(dex):
            try:
                for method_idx, pc, opcode in invoked_method_indexes(dex, code_off):
                    target = refs.get(method_idx)
                    if not target:
                        continue
                    count += 1
                    if len(invocations) < MAX_CALLS:
                        cls, method, sig = dex.method(idx)
                        other_cls, other_method, other_sig = target
                        invocations.append({
                            "caller_class": cls,
                            "caller_method": method, "caller_signature": sig,
                            "target_class": other_cls, "target_method": other_method,
                            "target_signature": other_sig, "opcode": f"0x{opcode:02x}"
                        })
            except DexError as exc:
                if len(problems) < 15:
                    problems.append({"method_idx": idx, "message": str(exc)})
    return {
        "playaudio_ref_method_count": len(refs),
        "playaudio_referenced_class_count": len(names),
        "defined_audio2_classes": core[:80],
        "retrofit_static_routes": _retrofit_annotations(dex),
        "retrofit_annotation_shape":_annotation_shape(dex),
        "invocation_count": count,
        "bounded_invocations": invocations,
        "scan_incomplete": bool(problems),
        "scan_errors": problems,
        "verdict": "STATIC_CANDIDATES_ONLY_NO_PROVEN_ACTIVE_PLAYER_HOOK"
    }
