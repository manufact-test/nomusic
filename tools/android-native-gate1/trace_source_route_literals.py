#!/usr/bin/env python3
"""Static candidate API routes for Yandex's *actual* audio-source resolver.

Search only publisher-signed DEX string constants used in executable methods.
Never dump arbitrary strings, credentials, URL parameters, music data or APK.
This is an allowlisted route-name inventory, NOT proof of source selection.
"""
from __future__ import annotations
import re
from inspect_android_host import Dex, DexError
from trace_native_callers import method_definitions, OP_WIDTH, payload_width

# Exclude "plays" (confirmed PlayAudioApi, likely a listening-event path).
TOKENS=("file-info","download-info","stream","source","playback","get-file",
        "track","audio","playable","play-info")
MAX_MATCHES=80
MAX_SAMPLES=90

def safe_route(value:str)->bool:
    if not (4<=len(value)<=130):
        return False
    if not re.fullmatch(r"[A-Za-z0-9_/{}?.:=&-]+",value):
        return False
    if not any(word in value.lower() for word in TOKENS):
        return False
    if value.lower() in ("plays","audio","source","stream","track","playback"):
        return False
    if "authorization" in value.lower() or "token" in value.lower():
        return False
    return True

def source_route_scan(data:bytes)->dict:
    dex=Dex(data)
    candidates={}
    matches=0
    for i in range(dex.string_count):
        val=dex.string(i)
        if safe_route(val):
            matches+=1
            if len(candidates)<MAX_MATCHES:
                candidates[i]=val
    usages=[]
    visited=0
    errors=[]
    if candidates:
        for method_idx,code in method_definitions(dex):
            dex.bounds(code,16)
            count=dex.u32(code+12)
            if count>3_000_000:
                raise DexError("Huge code item")
            start=code+16
            dex.bounds(start,count*2)
            pc=0
            try:
                while pc<count:
                    word=dex.u16(start+2*pc)
                    op=word&0xff
                    width=payload_width(dex,start,count,pc,word>>8) if op==0 else OP_WIDTH.get(op)
                    if width is None or pc+width>count:
                        raise DexError("Malformed instruction")
                    idx=None
                    if op==0x1a:
                        idx=dex.u16(start+2*(pc+1))
                    elif op==0x1b:
                        idx=dex.u32(start+2*(pc+1))
                    if idx in candidates and len(usages)<MAX_SAMPLES:
                        cls,method,sig=dex.method(method_idx)
                        usages.append({"route":candidates[idx],"caller_class":cls,
                                       "caller_method":method,"callsite":pc})
                    pc+=width
                visited+=1
            except DexError as exc:
                if len(errors)<8:errors.append(str(exc))
    return {
        "candidate_route_strings":list(candidates.values()),
        "matching_strings_total":matches,
        "const_string_usage_examples":usages,
        "methods_scanned":visited,
        "malformed_code_count":len(errors),
        "verdict":"STATIC_ONLY_ROUTE_LITERALS_NOT_DECODER_HOOK"
    }
