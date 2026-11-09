#!/usr/bin/env python3
"""Read-only DEX invoke callsite map for media-source APIs; NOT a Yandex hook proof."""
from __future__ import annotations
import argparse, io, json, struct, sys, zipfile
from pathlib import Path
from inspect_android_host import Dex, DexError, DEX_MAX, TARGET_FAMILIES, METHOD_NAMES

OP_WIDTH = {}
for lo, hi, width in [
    (0x01,0x01,1),(0x02,0x02,2),(0x03,0x03,3),
    (0x04,0x04,1),(0x05,0x05,2),(0x06,0x06,3),
    (0x07,0x07,1),(0x08,0x08,2),(0x09,0x09,3),
    (0x0a,0x12,1),(0x13,0x13,2),(0x14,0x14,3),(0x15,0x15,2),
    (0x16,0x16,2),(0x17,0x17,3),(0x18,0x18,5),(0x19,0x19,2),
    (0x1a,0x1a,2),(0x1b,0x1b,3),(0x1c,0x1c,2),
    (0x1d,0x1e,1),(0x1f,0x20,2),(0x21,0x21,1),(0x22,0x22,2),
    (0x23,0x23,2),(0x24,0x25,3),(0x26,0x26,3),(0x27,0x28,1),
    (0x29,0x29,2),(0x2a,0x2c,3),
    (0x2d,0x3d,2),(0x44,0x6d,2),(0x6e,0x72,3),
    (0x74,0x78,3),(0x7b,0x8f,1),(0x90,0xaf,2),
    (0xb0,0xcf,1),(0xd0,0xe2,2),(0xfa,0xfb,4),
    (0xfc,0xfd,3),(0xfe,0xff,2),
]:
    OP_WIDTH.update({op:width for op in range(lo,hi+1)})
INVOKES = set(range(0x6e,0x73)) | set(range(0x74,0x79)) | {0xfa,0xfb}
MAX_CODE_UNITS,MAX_CALLERS,MAX_METHOD_DEFS = 3_000_000,250,1_000_000

def uleb(dex:Dex,pos:int)->tuple[int,int]:
    value=0
    for i in range(5):
        dex.bounds(pos,1)
        b=dex.data[pos];pos+=1
        if i==4 and b&0xf0:raise DexError("ULEB overflow")
        value|=(b&0x7f)<<(7*i)
        if b<0x80:return value,pos
    raise DexError("Unterminated ULEB")

def method_definitions(dex:Dex):
    seen=0
    for i in range(dex.class_count):
        off=dex.class_offset+i*32
        owner=dex.descriptor(dex.u32(off))
        data_off=dex.u32(off+24)
        if not data_off:continue
        dex.bounds(data_off,1)
        n0,pos=uleb(dex,data_off)
        n1,pos=uleb(dex,pos)
        direct,pos=uleb(dex,pos)
        virtual,pos=uleb(dex,pos)
        if max(n0,n1,direct,virtual)>MAX_METHOD_DEFS:raise DexError("Large class_data")
        for _ in range(n0+n1):
            _,pos=uleb(dex,pos);_,pos=uleb(dex,pos)
        for count in (direct,virtual):
            previous=0
            for _ in range(count):
                delta,pos=uleb(dex,pos)
                idx=previous+delta;previous=idx
                if idx>=dex.method_count:raise DexError("Method index overflow")
                _,pos=uleb(dex,pos)
                code_off,pos=uleb(dex,pos)
                if dex.method(idx)[0]!=owner:raise DexError("Method owner mismatch")
                seen+=1
                if seen>MAX_METHOD_DEFS:raise DexError("Too many method defs")
                if code_off:yield idx,code_off

def payload_width(dex:Dex,start:int,count:int,pc:int,tag:int)->int:
    if tag==0:return 1
    if tag in (1,2):
        if pc+2>count:raise DexError("Truncated switch payload")
        n=dex.u16(start+(pc+1)*2)
        return 4+2*n if tag==1 else 2+4*n
    if tag==3:
        if pc+4>count:raise DexError("Truncated array payload")
        element=dex.u16(start+(pc+1)*2)
        n=dex.u32(start+(pc+2)*2)
        if element not in (1,2,4,8):raise DexError("Invalid payload width")
        return 4+(element*n+1)//2
    raise DexError("Unknown pseudo-instruction")

def invoked_method_indexes(dex:Dex,code_off:int):
    dex.bounds(code_off,16)
    count=dex.u32(code_off+12)
    if count>MAX_CODE_UNITS:raise DexError("Excessive method code")
    start=code_off+16
    dex.bounds(start,count*2)
    pc=0
    while pc<count:
        word=dex.u16(start+pc*2)
        op=word&0xff
        width=payload_width(dex,start,count,pc,word>>8) if op==0 else OP_WIDTH.get(op)
        if width is None:raise DexError(f"Unsupported opcode {op:#x}")
        if pc+width>count:raise DexError("Truncated instruction")
        if op in INVOKES:
            idx=dex.u16(start+(pc+1)*2)
            if idx>=dex.method_count:raise DexError("Invalid invoke method index")
            yield idx,pc,op
        pc+=width

def dex_callers(data:bytes)->dict:
    dex=Dex(data)
    targets={}
    for i in range(dex.method_count):
        klass,name,sig=dex.method(i)
        if name not in METHOD_NAMES:continue
        for family,classes in TARGET_FAMILIES.items():
            if klass in classes:
                targets[i]=(family,klass,name,sig)
                break
    callers=[];count=0;anomalies=[]
    if targets:
        for idx,code in method_definitions(dex):
            try:
                for target,pc,op in invoked_method_indexes(dex,code):
                    info=targets.get(target)
                    if info is None:continue
                    count+=1
                    if len(callers)<MAX_CALLERS:
                        c,m,s=dex.method(idx)
                        family,tc,tm,ts=info
                        callers.append({"caller_class":c,"caller_method":m,"caller_signature":s,
                            "code_unit_offset":pc,"opcode":f"{op:#04x}","target_family":family,
                            "target_class":tc,"target_method":tm,"target_signature":ts})
            except DexError as exc:
                if len(anomalies)<20:anomalies.append({"method_index":idx,"reason":str(exc)})
    return {"target_refs":len(targets),"call_sites":count,"callers":callers,
            "truncated":count>MAX_CALLERS,"anomalies":anomalies,"complete":not anomalies}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("apks",nargs="+",type=Path,help="Offline APK/XAPK/APKS")
    p.add_argument("--output",type=Path,help="LOCAL private JSON report, never commit")
    a=p.parse_args(argv)
    result={"purpose":"STATIC_NATIVE_CALLSITE_MAP","verdict":"NO_NATIVE_SOURCE_HOOK_PROVEN",
            "notice":"A bytecode callsite is not proof of live Yandex playback, permissions or exact track/edition IDs",
            "apks":[]}
    try:
        for path in a.apks:
            with zipfile.ZipFile(path) as outer:
                candidates=[(path.name,outer)]
                if not any(n.startswith("classes") and n.endswith(".dex") for n in outer.namelist()):
                    candidates=[]
                    for n in outer.namelist():
                        if not n.lower().endswith(".apk"):continue
                        info=outer.getinfo(n)
                        if info.file_size>DEX_MAX:raise ValueError("Nested APK size >128MiB")
                        candidates.append((n,zipfile.ZipFile(io.BytesIO(outer.read(n)))))
                try:
                    for label,z in candidates:
                        record={"name":label,"dex":[]}
                        for n in sorted(n for n in z.namelist() if n.startswith("classes") and n.endswith(".dex") and "/" not in n):
                            info=z.getinfo(n)
                            if info.file_size>DEX_MAX:raise ValueError("DEX >128MiB")
                            record["dex"].append({"entry":n,**dex_callers(z.read(n))})
                        if record["dex"]:result["apks"].append(record)
                finally:
                    for _,z in candidates:
                        if z is not outer:z.close()
        payload=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
        if a.output:a.output.write_text(payload,encoding="utf-8")
        else:print(payload,end="")
        return 0
    except (DexError,OSError,ValueError,zipfile.BadZipFile) as exc:
        print(f"STATIC_CALLER_TRACE_ERROR: {exc}",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
