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

def _guard_source(code,instructions,guard_index,dex,group_call):
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
                return group_call(owner,name)
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

def exact_error_guard_report(code:bytes, target_strings:set[int], dex, group_call):
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
    instruction_pcs={p for p,_,_ in ins}
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
            if destination<=throw_pc or destination not in instruction_pcs:
                continue
            guards+=1
            sources.add(_guard_source(code,ins,gi,dex,group_call))
    # Verified control-flow edge is not the same as a proven runtime predicate.
    return {"decoded":True,"target_strings":len(string_pcs),
            "verified_guard_sources":sorted(sources),
            "guards_skipping_throw":min(guards,16),
            "causal_branch_proven":False}

def private_direct_guard_invokes(code:bytes, target_strings:set[int], dex, group_call):
    """Find only method-result registers tested by a verified local IF edge.

    Returns in-memory DEX method IDs; NEVER log/serialize them. A candidate
    call is not proof the observed runtime took the false branch.
    """
    try:ins=decode_instructions(code)
    except FlowDecodeError:return set()
    pcs={p for p,_,_ in ins}
    refs=set()
    strings=[
        p for p,op,_ in ins
        if (op==0x1a and struct.unpack_from("<H",code,p+2)[0] in target_strings)
        or (op==0x1b and struct.unpack_from("<I",code,p+2)[0] in target_strings)]
    for string_pc in strings:
        throw_pc=next((p for p,op,_ in ins
                       if op==0x27 and string_pc<p<=string_pc+256),None)
        if throw_pc is None:continue
        for i,(p,op,_) in enumerate(ins):
            if op not in range(0x38,0x3e) or i<2 or not (
                    string_pc-384<=p<string_pc):continue
            destination=p+2*struct.unpack_from("<h",code,p+2)[0]
            if destination<=throw_pc or destination not in pcs:continue
            result_pc,result_opcode,_=ins[i-1]
            invoke_pc,invoke_opcode,_=ins[i-2]
            if (result_opcode not in RESULT_OPS or
                    code[result_pc+1]!=code[p+1] or
                    invoke_opcode not in INVOKE_METHOD):continue
            ref=struct.unpack_from("<H",code,invoke_pc+2)[0]
            if ref>=dex.method_count:continue
            owner,name=dex.method(ref)
            if group_call(owner,name) in (
                    "PUSH_COMMON","PUSH_UTILS","PUSH_IMPL_HELPER",
                    "PUSH_OTHER_HELPER"):
                refs.add(ref)
    return refs

def private_guard_input_sources(code:bytes, target_strings:set[int], dex, group_call):
    """Conservative register backslice of the private String->boolean call.

    Only fixed enum families are returned. Never return DEX registers,
    method/class identities, field values, string contents, or offsets.
    """
    try:ins=decode_instructions(code)
    except FlowDecodeError:return {"DECODE_UNAVAILABLE"}
    candidates=private_direct_guard_invokes(code,target_strings,dex,group_call)
    if not candidates:return set()
    found=set()
    for idx,(pc,op,units) in enumerate(ins):
        if op not in INVOKE_METHOD:continue
        ref=struct.unpack_from("<H",code,pc+2)[0]
        if ref not in candidates:continue
        if op in (0xfa,0xfb):
            found.add("INVOKE_SHAPE_UNSUPPORTED")
            continue
        static=op in (0x71,0x77)
        if op>=0x74:  # invoke-*/range; each argument uses a sequential register
            count=code[pc+1]
            start=struct.unpack_from("<H",code,pc+4)[0]
            at=0 if static else 1
            if count<=at:
                found.add("CALL_ARGUMENT_MISSING");continue
            reg=start+at
        else:  # invoke-kind (35c): C,D,E,F,G registers
            count=code[pc+1]>>4
            raw=code[pc+4:pc+6]
            regs=[raw[0]&15,raw[0]>>4,raw[1]&15,raw[1]>>4,code[pc+1]&15]
            at=0 if static else 1
            if count<=at:
                found.add("CALL_ARGUMENT_MISSING");continue
            reg=regs[at]
        category="PARAM_OR_CAPTURE"
        for i in range(idx-1,max(-1,idx-65),-1):
            p,opcode,_=ins[i]
            if opcode in (0x07,0x04,0x01) and (code[p+1]&15)==reg:
                reg=code[p+1]>>4
                continue
            if opcode in (0x08,0x05,0x02) and code[p+1]==reg:
                reg=struct.unpack_from("<H",code,p+2)[0]
                continue
            if opcode in (0x09,0x06,0x03) and struct.unpack_from("<H",code,p+2)[0]==reg:
                reg=struct.unpack_from("<H",code,p+4)[0]
                continue
            if opcode==0x0c and code[p+1]==reg:
                if i and ins[i-1][1] in INVOKE_METHOD:
                    prior=ins[i-1][0]
                    call=struct.unpack_from("<H",code,prior+2)[0]
                    if call<dex.method_count:
                        category="RESULT_"+group_call(*dex.method(call))
                    else:category="RESULT_UNKNOWN"
                else:category="RESULT_UNLINKED"
                break
            if opcode in (0x1a,0x1b) and code[p+1]==reg:
                category="STRING_LITERAL";break
            if opcode in (0x62,0x60,0x61,0x63,0x64,0x65,0x66) and code[p+1]==reg:
                category="STATIC_FIELD";break
            if opcode in range(0x52,0x59) and (code[p+1]&15)==reg:
                category="INSTANCE_FIELD";break
            if opcode==0x46 and code[p+1]==reg:
                category="ARRAY_ELEMENT";break
            if opcode==0x12 and (code[p+1]&15)==reg:
                category="NULL_OR_NUMERIC_LITERAL";break
        found.add(category)
    return found

def private_push_utils_supplier_refs(code:bytes, target_strings:set[int],
                                    dex, group_call):
    """In-memory method IDs only, of PUSH_UTILS directly supplying guard input."""
    try:ins=decode_instructions(code)
    except FlowDecodeError:return set()
    guarded=private_direct_guard_invokes(code,target_strings,dex,group_call)
    found=set()
    for idx,(pc,op,_) in enumerate(ins):
        if op not in INVOKE_METHOD or op in (0xfa,0xfb):continue
        mid=struct.unpack_from("<H",code,pc+2)[0]
        if mid not in guarded:continue
        static=op in (0x71,0x77)
        at=0 if static else 1
        if op>=0x74:
            if code[pc+1]<=at:continue
            reg=struct.unpack_from("<H",code,pc+4)[0]+at
        else:
            if code[pc+1]>>4<=at:continue
            raw=code[pc+4:pc+6]
            registers=(raw[0]&15,raw[0]>>4,raw[1]&15,raw[1]>>4,code[pc+1]&15)
            reg=registers[at]
        for i in range(idx-1,max(-1,idx-65),-1):
            p,opcode,_=ins[i]
            if opcode==0x07 and (code[p+1]&15)==reg:
                reg=code[p+1]>>4
                continue
            if opcode==0x08 and code[p+1]==reg:
                reg=struct.unpack_from("<H",code,p+2)[0]
                continue
            if opcode==0x09 and struct.unpack_from("<H",code,p+2)[0]==reg:
                reg=struct.unpack_from("<H",code,p+4)[0]
                continue
            if opcode==0x0c and code[p+1]==reg and i>0:
                prev,callop,_=ins[i-1]
                if callop in INVOKE_METHOD:
                    ref=struct.unpack_from("<H",code,prev+2)[0]
                    if ref<dex.method_count and group_call(
                            *dex.method(ref))=="PUSH_UTILS":
                        found.add(ref)
                break
            if opcode in (0x1a,0x1b,0x62) and code[p+1]==reg:break
            if opcode==0x54 and (code[p+1]&15)==reg:break
    return found

def private_direct_guard_branch_roles(code:bytes,target_strings:set[int],dex,group_call):
    """Only exact IF-EQZ / IF-NEZ whose preceding move-result is the Push guard.

    Category states which Boolean value makes the direct branch skip local throw.
    Does NOT claim the whole method's CFG is resolved.
    """
    try:ins=decode_instructions(code)
    except FlowDecodeError:return {"DECODE_UNAVAILABLE"}
    guarded=private_direct_guard_invokes(code,target_strings,dex,group_call)
    if not guarded:return set()
    pcs={p for p,_,_ in ins}
    strings=[p for p,op,_ in ins
             if (op==0x1a and struct.unpack_from("<H",code,p+2)[0] in target_strings)
             or (op==0x1b and struct.unpack_from("<I",code,p+2)[0] in target_strings)]
    states=set()
    for string_pc in strings:
        throw_pc=next((p for p,op,_ in ins if op==0x27
                       and string_pc<p<=string_pc+256),None)
        if throw_pc is None:continue
        for i,(p,op,_) in enumerate(ins):
            if op not in (0x38,0x39) or i<2 or not (
                    string_pc-384<=p<string_pc):continue
            dest=p+struct.unpack_from("<h",code,p+2)[0]*2
            if dest<=throw_pc or dest not in pcs:continue
            result_pc,result_op,_=ins[i-1]
            call_pc,call_op,_=ins[i-2]
            if (result_op not in RESULT_OPS or
                    code[result_pc+1]!=code[p+1] or
                    call_op not in INVOKE_METHOD):continue
            ref=struct.unpack_from("<H",code,call_pc+2)[0]
            if ref not in guarded:continue
            states.add("BRANCH_SKIPS_THROW_ON_FALSE" if op==0x38
                       else "BRANCH_SKIPS_THROW_ON_TRUE")
    return states
