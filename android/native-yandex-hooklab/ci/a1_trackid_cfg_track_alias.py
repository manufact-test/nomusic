#!/usr/bin/env python3
"""Tiny fail-closed DEX must-alias verifier for ONE original Track field read.

Identities are Java register aliases from an exact typed formal Track argument.
Each conditional branch is joined by intersection; a possible non-Track path
prevents promotion. This is static provenance, NOT selected playback/edition.
"""
from collections import deque

TRACK = "Lru/yandex/music/data/audio/o;"
MAX_INSTRUCTIONS = 768
MAX_RELAXATIONS = 12000
MAX_TRACK_FORMALS = 1
TERMINATORS = {0x0e, 0x0f, 0x10, 0x11, 0x27}
IF_BRANCHES = set(range(0x32, 0x3e))
GOTOS = {0x28, 0x29, 0x2a}
UNSUPPORTED_FLOW = {0x26, 0x2b, 0x2c}  # fill-array, packed/sparse switch
SIDE_EFFECT_ONLY = (set(range(0x4b, 0x52)) |
                    set(range(0x59, 0x60)) |
                    set(range(0x67, 0x6e)) |
                    set(range(0x6e, 0x79)) |
                    {0x1d,0x1e,0x00,0xfa,0xfb,0xfc,0xfd})
WIDE_WRITERS = {0x04,0x05,0x06,0x09,0x0b,0x16,0x17,0x18,0x19,
                0x53,0x56,0x61,0x64,0x81,0x82,0x83,0x84,0x85,0x86,
                0x9b,0x9c,0x9d,0x9e,0x9f,0xa0,0xa1,0xa2,
                0xab,0xac,0xad,0xae,0xaf,0xb0,0xb1,0xb2}
# Only the bytecode shapes read by this proof are used; no field contents.

def signed(value, bits):
    limit=1 << bits
    return value-limit if value & (limit >> 1) else value

def _successors(ins):
    loc={pc:i for i,(pc,op,words) in enumerate(ins)}
    result=[]
    for i,(pc,op,words) in enumerate(ins):
        if op in UNSUPPORTED_FLOW or (op == 0 and words[0] != 0):
            return None
        if op in TERMINATORS:
            result.append(())
            continue
        if op in GOTOS:
            if op == 0x28:
                step=signed(words[0] >> 8,8)
            elif op == 0x29:
                step=signed(words[1],16)
            else:
                step=signed(words[1] | (words[2] << 16),32)
            target=loc.get(pc+step)
            if target is None or step==0:
                return None
            result.append((target,))
            continue
        if i + 1 >= len(ins):
            return None
        if op in IF_BRANCHES:
            target=loc.get(pc+signed(words[1],16))
            if target is None:
                return None
            result.append((i+1,target) if i+1 != target else (target,))
        else:
            result.append((i+1,))
    return result

def prove_original_track_receiver(dex,method,flags,code_off,instructions,
                                  field_read_index,receiver,audit,move_object):
    """Return a finite non-sensitive verdict. No source object is accessed."""
    if (field_read_index < 0 or field_read_index >= len(instructions)
            or len(instructions)>MAX_INSTRUCTIONS
            or not instructions or dex.u16(code_off+6)!=0):
        return "CFG_UNSUPPORTED_METHOD"
    size,insize=dex.u16(code_off),dex.u16(code_off+2)
    if insize>size or size>65535:
        return "CFG_BAD_REGISTER_WINDOW"
    cursor=size-insize+(0 if flags & 0x8 else 1)
    track_formals=[]
    for typ in audit.parse_types(method[2]):
        if typ==TRACK:
            track_formals.append(cursor)
        cursor+=2 if typ in ("J","D") else 1
    if len(track_formals)!=MAX_TRACK_FORMALS:
        return "CFG_TRACK_FORMAL_NOT_UNIQUE"
    edges=_successors(instructions)
    if edges is None:
        return "CFG_UNSUPPORTED_FLOW"
    # Must-alias: at EVERY possible path, known registers must still refer
    # to the exact Track formal reference, without invoking equals()/toString().
    states={0:frozenset(track_formals)}
    q=deque([0])
    relaxations=0
    while q:
        i=q.popleft()
        relaxations+=1
        if relaxations>MAX_RELAXATIONS:
            return "CFG_BUDGET_EXCEEDED"
        _pc,op,words=instructions[i]
        alias=set(states[i])
        moving=move_object(op,words)
        if moving is not None:
            dst,src=moving
            incoming=src in alias
            alias.discard(dst)
            if incoming:
                alias.add(dst)
        elif op==0x1f:
            pass  # check-cast does not create a new Java object
        else:
            dst=audit.written_register(op,words)
            if dst is not None:
                alias.discard(dst)
                # WIDE_WRITERS is intentionally conservative. Replacing an
                # aliased register with the upper half of a long is a kill.
                if op in WIDE_WRITERS:
                    alias.discard(dst+1)
            elif op not in (SIDE_EFFECT_ONLY | GOTOS | IF_BRANCHES | TERMINATORS):
                # An opcode whose destination we cannot model may write
                # any live register: fail closed rather than guessing.
                alias.clear()
        outgoing=frozenset(alias)
        for nxt in edges[i]:
            old=states.get(nxt)
            merged=outgoing if old is None else old.intersection(outgoing)
            if old!=merged:
                states[nxt]=merged
                q.append(nxt)
    if field_read_index not in states:
        return "CFG_FIELD_READ_UNREACHABLE"
    return ("CFG_EXACT_FORMAL_TRACK_RECEIVER"
            if receiver in states[field_read_index]
            else "CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN")
