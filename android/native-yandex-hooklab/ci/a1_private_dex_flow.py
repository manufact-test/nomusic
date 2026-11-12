"""Exact-width DEX instruction triage on private CI only.

No decoded bytecode, vendor strings, symbols, method IDs or offsets are printed.
Classification is deliberately conservative: unsupported layouts yield UNKNOWN.
"""
from __future__ import annotations
import struct

class FlowDecodeError(Exception): pass

# DEX 035..039 opcode lengths in 16-bit code units. Unknown opcodes fail closed.
LENGTHS = {}
for op in [0x00,0x01,0x04,0x07,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,
           0x10,0x11,0x12,0x1d,0x1e,0x21,0x27,0x28]:
    LENGTHS[op]=1
for lo,hi in ((0x7b,0x8f),(0xb0,0xcf)):
    for op in range(lo,hi+1):LENGTHS[op]=1
for op in [0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,
           0x1f,0x20,0x22,0x23,0x29,0xfe,0xff]:
    LENGTHS[op]=2
for lo,hi in ((0x2d,0x3d),(0x44,0x6d),(0x90,0xaf),(0xd0,0xe2)):
    for op in range(lo,hi+1):LENGTHS[op]=2
for op in [0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,
           0x26,0x2a,0x2b,0x2c,0xfc,0xfd]:
    LENGTHS[op]=3
for lo,hi in ((0x6e,0x72),(0x74,0x78)):
    for op in range(lo,hi+1):LENGTHS[op]=3
LENGTHS[0xfa]=LENGTHS[0xfb]=4
LENGTHS[0x18]=5

INVOKE_METHOD = set(range(0x6e,0x73)) | set(range(0x74,0x79)) | {0xfa,0xfb}
IF_OPS=set(range(0x32,0x3e))
FIELD_OPS=set(range(0x52,0x6e))
RESULT_OPS={0x0a,0x0b,0x0c}

def decode_instructions(code:bytes):
    if len(code)%2:raise FlowDecodeError("ODD_CODE")
    result=[]
    pc=0
    while pc<len(code):
        op=code[pc]; high=code[pc+1]
        if op==0 and high in (1,2,3):
            if pc+8>len(code):raise FlowDecodeError("PAYLOAD_HEADER")
            size=struct.unpack_from("<H",code,pc+2)[0] if high<3 else struct.unpack_from("<I",code,pc+4)[0]
            if high==1:units=4+2*size
            elif high==2:units=2+4*size
            else:
                width=struct.unpack_from("<H",code,pc+2)[0]
                if width not in (1,2,4,8):raise FlowDecodeError("PAYLOAD_WIDTH")
                units=4+(size*width+1)//2
        else:
            units=LENGTHS.get(op)
            if units is None:raise FlowDecodeError("UNSUPPORTED_OPCODE")
        if units<=0 or pc+2*units>len(code):
            raise FlowDecodeError("INSTRUCTION_BOUND")
        result.append((pc,op,units))
        pc+=2*units
    return result

def _guard_source(code,instructions,guard_index,dex):
    """Describe the register written immediately upstream of a guard.
    No alias/dataflow claim beyond direct local move-result is made.
    """
    pc,op,_=instructions[guard_index]
    if op<0x38:return "TWO_REGISTER_GUARD"
    reg=code[pc+1]
    for i in range(guard_index-1,max(-1,guard_index-17),-1):
        p,opcode,_=instructions[i]
        if opcode in RESULT_OPS and code[p+1]==reg:
            if i==0:return "RESULT_WITHOUT_INVOKE"
            prev,callop,_=instructions[i-1]
            if callop in INVOKE_METHOD:
                method_idx=struct.unpack_from("<H",code,prev+2)[0]
                if method_idx>=dex.method_count:return "BAD_METHOD_REF"
                # The caller supplies a fixed-category group function.
                owner,name=dex.method(method_idx)
                return dex.category(owner,name)
            if callop in (0xfc,0xfd):return "CUSTOM_CALL"
            return "RESULT_WITHOUT_INVOKE"
        if (opcode in FIELD_OPS and code[p+1]==reg):
            return "FIELD_STATE"
        if opcode in (0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19) and (
                (code[p+1] & 0x0f if opcode==0x12 else code[p+1])==reg):
            return "LITERAL_STATE"
        if opcode in (0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09) and (
                (code[p+1] & 0x0f if opcode in (0x01,0x04,0x07) else code[p+1])==reg):
            return "ALIAS_UNRESOLVED"
    return "SOURCE_UNRESOLVED"

def exact_error_guard_report(code:bytes, target_strings:set[int], dex):
    """Correlate real DEX IF destinations with error-string and throw opcodes.

    Only direct local forward IF that skips the eventual throw is reported.
    Unsupported control-flow shapes deliberately remain unresolved.
    """
    try:
        ins=decode_instructions(code)
    except FlowDecodeError:
        return {"decoded":False,"target_strings":0,"verified_guard_sources":[],
                "guards_skipping_throw":0,"causal_branch_proven":False}
    string_pcs=[]
    for pc,op,_ in ins:
        if op==0x1a and struct.unpack_from("<H",code,pc+2)[0] in target_strings:
            string_pcs.append(pc)
        elif op==0x1b and struct.unpack_from("<I",code,pc+2)[0] in target_strings:
            string_pcs.append(pc)
    sources=set()
    guards=0
    for string_pc in string_pcs:
        throw_pc=next((pc for pc,op,_ in ins
                       if op==0x27 and string_pc<pc<=string_pc+256),None)
        if throw_pc is None:continue
        for gi,(pc,op,_) in enumerate(ins):
            if op not in IF_OPS or not (string_pc-384<=pc<string_pc):
                continue
            offset=struct.unpack_from("<h",code,pc+2)[0]
            destination=pc+offset*2
            # Only an actually decoded instruction boundary can be a branch target.
            if destination<=throw_pc or destination not in {p for p,_,_ in ins}:
                continue
            guards+=1
            sources.add(_guard_source(code,ins,gi,dex))
    # Verified control-flow edge is not the same as a proven runtime predicate.
    return {"decoded":True,"target_strings":len(string_pcs),
            "verified_guard_sources":sorted(sources),
            "guards_skipping_throw":min(guards,16),
            "causal_branch_proven":False}
