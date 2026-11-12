"""Bounded synthetic-length DEX predicate evaluator. No vendor values disclosed.

Runs entirely on private CI. Supports only a tiny verified subset of Dalvik
instructions; all unknown operations/CFG shapes result in INCONCLUSIVE.
"""
from __future__ import annotations
import struct
from a1_private_dex_flow import decode_instructions,FlowDecodeError,INVOKE_METHOD

def uleb(data,pos):
    value=0
    for shift in range(5):
        if pos>=len(data):raise ValueError("ULEB_BOUND")
        byte=data[pos];pos+=1
        value|=(byte&127)<<(7*shift)
        if not byte&128:return value,pos
    raise ValueError("ULEB_BOUND")

def code_items_with_meta(dex, include_try_size=False):
    data=dex.data
    for class_index in range(dex.class_count):
        at=struct.unpack_from("<I",data,dex.class_off+class_index*32+24)[0]
        if not at:continue
        st,at=uleb(data,at);ins,at=uleb(data,at)
        direct,at=uleb(data,at);virtual,at=uleb(data,at)
        if st+ins+direct+virtual>100000:raise ValueError("CLASS_BOUND")
        for _ in range(st+ins):
            _,at=uleb(data,at);_,at=uleb(data,at)
        for count in (direct,virtual):
            mid=0
            for _ in range(count):
                delta,at=uleb(data,at);mid+=delta
                flags,at=uleb(data,at)
                offset,at=uleb(data,at)
                if not offset:continue
                if offset+16>len(data):raise ValueError("CODE_BOUND")
                reg_count,input_count=struct.unpack_from("<HH",data,offset)
                size=struct.unpack_from("<I",data,offset+12)[0]
                if size>200000 or offset+16+size*2>len(data):
                    raise ValueError("CODE_BOUND")
                item=(mid,reg_count,input_count,bool(flags&8),
                      data[offset+16:offset+16+size*2])
                # Code item tries_size is a bounded structural property only.
                # Keep prior 5-tuple ABI unless explicitly requested by caller.
                yield item+(struct.unpack_from("<H",data,offset+6)[0],) \
                    if include_try_size else item

def _signed4(x):
    return x-16 if x>=8 else x

def eval_string_length_predicate(code,reg_count,input_count,is_static,
                                 dex,length):
    """Execute only primitive register/control-flow operations and String.length.

    The test string is represented by a nonzero sentinel, never real data.
    Any possible side effect or unsupported opcode immediately fails closed.
    """
    if not 0<input_count<=reg_count<=256:return None
    if not is_static and input_count<2:return None
    try:ins=decode_instructions(code)
    except FlowDecodeError:return None
    by_pc={pc:(op,n) for pc,op,n in ins}
    registers=[None]*reg_count
    reg=reg_count-input_count+(0 if is_static else 1)
    registers[reg]=0x60000001
    pc=0
    pending=None
    for _ in range(256):
        entry=by_pc.get(pc)
        if entry is None:return None
        op,n=entry
        nxt=pc+n*2
        b=code[pc+1]
        if op==0x00:pass
        elif op==0x12:
            registers[b&15]=_signed4(b>>4)
        elif op==0x13:
            registers[b]=struct.unpack_from("<h",code,pc+2)[0]
        elif op==0x14:
            registers[b]=struct.unpack_from("<i",code,pc+2)[0]
        elif op in (0x01,0x07):
            registers[b&15]=registers[b>>4]
        elif op in (0x02,0x08):
            registers[b]=registers[struct.unpack_from("<H",code,pc+2)[0]]
        elif op in (0x03,0x09):
            dest,src=struct.unpack_from("<HH",code,pc+2)
            registers[dest]=registers[src]
        elif op in (0x0a,0x0b,0x0c):
            if pending is None:return None
            registers[b]=pending
            pending=None
        elif op in INVOKE_METHOD:
            if op in (0xfa,0xfb):return None
            mid=struct.unpack_from("<H",code,pc+2)[0]
            if mid>=dex.method_count:return None
            owner,name=dex.method(mid)
            if (owner,name)!=("Ljava/lang/String;","length"):
                return None
            if op>=0x74:
                count=b
                receiver=struct.unpack_from("<H",code,pc+4)[0]
            else:
                count=b>>4
                receiver=code[pc+4]&15
            if count!=1 or registers[receiver]!=0x60000001:return None
            pending=length
        elif op in range(0x32,0x3e):
            val=None
            if op<=0x37:
                a=registers[b&15];c=registers[b>>4]
                if a is None or c is None:return None
                val={0x32:a==c,0x33:a!=c,0x34:a<c,0x35:a>=c,
                     0x36:a>c,0x37:a<=c}[op]
            else:
                a=registers[b]
                if a is None:return None
                val={0x38:a==0,0x39:a!=0,0x3a:a<0,0x3b:a>=0,
                     0x3c:a>0,0x3d:a<=0}[op]
            if val:
                nxt=pc+struct.unpack_from("<h",code,pc+2)[0]*2
        elif op==0x28:
            signed=b-256 if b>=128 else b
            nxt=pc+signed*2
        elif op==0x29:
            nxt=pc+struct.unpack_from("<h",code,pc+2)[0]*2
        elif op==0x2a:
            nxt=pc+struct.unpack_from("<i",code,pc+2)[0]*2
        elif op==0x0f:
            v=registers[b]
            return bool(v) if v in (0,1) else None
        else:
            return None
        pc=nxt
    return None

def rule_from_synthetic_lengths(code,reg_count,input_count,is_static,dex):
    cases=[0,1,2,4,8,16,32,64,128]
    values=[eval_string_length_predicate(
        code,reg_count,input_count,is_static,dex,n) for n in cases]
    if any(v is None for v in values):return "INCONCLUSIVE"
    if all(values):return "ALWAYS_TRUE_FOR_TEST_CASES"
    if not any(values):return "ALWAYS_FALSE_FOR_TEST_CASES"
    if values==[True]+[False]*8:return "TRUE_FOR_ZERO_ONLY"
    if values==[False]+[True]*8:return "TRUE_FOR_POSITIVE_LENGTH"
    return "LENGTH_SENSITIVE_OTHER"
