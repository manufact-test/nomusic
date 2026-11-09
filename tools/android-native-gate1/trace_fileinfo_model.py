#!/usr/bin/env python3
"""Read-only field/type layout of signed native Yandex FileInfo DTO conversion.

No field values, user information, tokens, URLs or APK binaries are emitted.
A type shape alone does NOT prove media-source ownership.
"""
from __future__ import annotations
from inspect_android_host import Dex,DexError

TARGETS={
    "Leed;",
    "Lhee;",
    "Ldjv;",
    "Lsw7;",
    "Lcom/yandex/music/shared/player/content/remote/fileinfo/FileInfoDto;",
    "Lcom/yandex/music/shared/player/content/remote/fileinfo/OldGetFileInfoDto;",
}
LIMIT=50

def inspect_fileinfo_shapes(data:bytes)->dict:
    dex=Dex(data)
    fcount,foff=dex.table(80,8)
    shapes={}
    for c in sorted(TARGETS):
        shapes[c]={"fields":[],"methods":[],"defined":False}
    defined=dex.defined_classes()
    for c in shapes:
        shapes[c]["defined"]=c in defined
    for i in range(fcount):
        pos=foff+i*8
        owner=dex.descriptor(dex.u16(pos))
        if owner not in TARGETS:continue
        dtype=dex.descriptor(dex.u16(pos+2))
        name=dex.string(dex.u32(pos+4))
        if len(shapes[owner]["fields"])<LIMIT:
            shapes[owner]["fields"].append({"name":name,"type":dtype})
    for i in range(dex.method_count):
        owner,name,sig=dex.method(i)
        if owner not in TARGETS:continue
        if len(shapes[owner]["methods"])<LIMIT:
            shapes[owner]["methods"].append({"name":name,"signature":sig})
    return {"defined_targets":{k:v for k,v in shapes.items() if v["defined"]},
            "reference_only_targets":sorted(k for k,v in shapes.items()
                                            if (v["fields"] or v["methods"]) and not v["defined"]),
            "verdict":"STATIC_DATA_MODEL_ONLY_SOURCE_HOOK_NOT_PROVEN"}
