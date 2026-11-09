#!/usr/bin/env python3
"""Pin API interface method annotation owning native media file-info routes.

Reads ONLY annotation descriptors and whitelisted compile-time route values
from locally verified-signer DEX. Never touches app private data, OAuth,
actual user requests or audio, and never emits other annotation values.
"""
from __future__ import annotations
from inspect_android_host import Dex, DexError
from trace_native_callers import uleb
from trace_playaudio_boundary import _encoded_value

ROUTES = frozenset((
    "resources/v2/file-info",
    "tracks/{trackId}/download-info",
    "get-file-info",
    "download-info",
    "file-info",
    "rotor/station/{stationId}/stream",
))
MAX_MATCHES=35

def inspect_media_route_annotations(data:bytes)->dict:
    dex=Dex(data)
    matches=[]
    examined=0
    for c in range(dex.class_count):
        classpos=dex.class_offset+c*32
        owner=dex.descriptor(dex.u32(classpos))
        off=dex.u32(classpos+20)
        if not off:continue
        nfields,nmethods,nparams=(dex.u32(off+4),dex.u32(off+8),dex.u32(off+12))
        if max(nfields,nmethods,nparams)>100000:
            raise DexError("Unexpected annotation directory size")
        pos=off+16+nfields*8
        dex.bounds(pos,nmethods*8)
        for m in range(nmethods):
            midx=dex.u32(pos+8*m)
            setoff=dex.u32(pos+8*m+4)
            if midx>=dex.method_count:
                raise DexError("Invalid method id in annotation directory")
            if not setoff:continue
            n=dex.u32(setoff)
            if n>80:raise DexError("Unreasonable method annotation set")
            dex.bounds(setoff+4,n*4)
            for a in range(n):
                annotation_off=dex.u32(setoff+4+4*a)
                dex.bounds(annotation_off,2)
                p=annotation_off+1
                typ,p=uleb(dex,p)
                annotation_class=dex.descriptor(typ)
                size,p=uleb(dex,p)
                if size>64:raise DexError("Oversize encoded method annotation")
                for _ in range(size):
                    key,p=uleb(dex,p)
                    name=dex.string(key)
                    value,p=_encoded_value(dex,p)
                    if name=="value" and isinstance(value,str) and value in ROUTES:
                        methodowner,method,signature=dex.method(midx)
                        if methodowner!=owner:raise DexError("Method owner mismatches annotation")
                        if len(matches)<MAX_MATCHES:
                            matches.append({
                                "interface_class":owner,
                                "method":method,"signature":signature,
                                "annotation_class":annotation_class,
                                "static_route":value})
            examined+=1
    return {"method_annotations_examined":examined,
            "route_matches":matches,
            "match_limit_reached":len(matches)>=MAX_MATCHES,
            "evidence":"ANNOTATION_STATIC_ONLY_NOT_PROOF_OF_RUNTIME_STREAM_SELECTION"}
