#!/usr/bin/env python3
"""Scoped signed NAV17 ExoPlayer/h Lxh6 queue-slot role map, read-only.
No field names/values, track IDs, URLs, user data, or media bytes printed.
Creating/preparing a period is NEVER treated as currently audible.
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
audit = trusted.audit

QUEUE = "Landroidx/media3/exoplayer/h;"
ENGINE = ("Landroidx/media3/exoplayer/e;", "break", "()V")
HOLDER = "Lxh6;"
MAX_QUEUE_METHODS = 100
MAX_SLOT_IDS = 16
MAX_ROWS = 70
MAX_SCOPED_EVENTS = 160

def slot_field(dex, op, words):
    if op not in (0x54, 0x5b):  # iget-object / iput-object, 22c
        return None
    owner, name, typ = audit.field_id(dex, words[1])
    if owner != QUEUE or typ != HOLDER:
        return None
    return (owner, name, typ)  # internal equality only; never export field name

def direct_getter(instructions, dex, slot_ids):
    """Provable straightline iget-object -> return-object on same register.
    Rejects branches or overwritten aliases; no name-based role guessing."""
    if len(instructions) > 12:
        return None
    values = {}
    found = []
    for pc, op, words in instructions:
        if op in (0x28, 0x29, 0x2a) or 0x32 <= op <= 0x3d:
            return None
        if op == 0x54:
            field = slot_field(dex, op, words)
            reg = (words[0] >> 8) & 0x0f
            values[reg] = slot_ids.get(field) if field else None
        elif op == 0x11:
            reg = (words[0] >> 8) & 0xff
            found.append(values.get(reg))
        elif op in (0x07, 0x08, 0x09):
            dst, src = audit.move_object_registers(op, words)
            values[dst] = values.get(src)
        elif op in (0x00, 0x0e):
            pass
        else:
            written = audit.written_register(op, words)
            if written is None:
                return None
            values[written] = None
    if len(found) != 1 or found[0] is None:
        return None
    return found[0]


def bounded_register_microtrace(dex, instructions, slots, ranges):
    """Only branch/alias/register form, never DEX literals or private fields."""
    result=[]
    for pc, op, words in instructions:
        if not any(lo <= pc <= hi for lo,hi in ranges):
            continue
        kind=None
        row={"pc":pc}
        field=slot_field(dex,op,words)
        if field is not None:
            row.update(action="GET" if op==0x54 else "PUT",
                       slot=slots[field],
                       value_register=(words[0] >> 8)&0xf,
                       receiver_register=(words[0] >> 12)&0xf)
            kind="field"
        elif op in (0x54,0x5b):
            owner,_private_name,typ=audit.field_id(dex,words[1])
            if owner==HOLDER and typ==HOLDER:
                row.update(action="HOLDER_NEXT_TYPED_FIELD",
                           operation="READ" if op==0x54 else "WRITE",
                           value_register=(words[0]>>8)&0xf,
                           receiver_register=(words[0]>>12)&0xf)
                kind="holder_link"
        elif op in (0x07,0x08,0x09):
            dst,src=audit.move_object_registers(op,words)
            row.update(action="MOVE_OBJECT",to=dst,source=src);kind="move"
        elif op in (0x0c,0x0d):
            row.update(action="MOVE_RESULT",register=words[0] >> 8);kind="move"
        elif op==0x22 and dex.descriptor(words[1])==HOLDER:
            row.update(action="NEW_HOLDER",register=words[0] >> 8);kind="new"
        elif op in (0x11,0x0e):
            row.update(action="RETURN",register=words[0]>>8);kind="return"
        elif 0x32<=op<=0x3d or op in (0x28,0x29,0x2a):
            row.update(action="BRANCH",opcode=op);kind="branch"
        elif op in (0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1a,0x1b):
            row.update(action="CONST_REDACTED",register=(words[0]>>8)&0xff);kind="constant"
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            target=dex.method(words[1])
            if target[0] in (QUEUE,HOLDER,"LmQ8;"):
                row.update(action="CALL",callee=[target[0],target[1],target[2]],
                           registers=audit.invoke_registers(op,words));kind="call"
        if kind:result.append(row)
        if len(result)>120:raise ValueError("QUEUE_MICROTRACE_ROW_LIMIT")
    return result


RENDERER_BOUNDARY = frozenset({
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"),
    ("LmQ8;","catch","(Landroidx/media3/exoplayer/k;Lxh6;LRFa;LLL2;)I"),
    ("Landroidx/media3/exoplayer/h;","if","()Lxh6;"),
    ("Landroidx/media3/exoplayer/e;","extends","(Lxh6;)Z"),
})

def producer_queue_slot(producer, pc_insn, dex, slots):
    """Resolve only a direct exact queue field read as holder-call producer."""
    if not isinstance(producer,dict) or producer.get("kind")!="INSTANCE_FIELD":
        return None
    pc=producer.get("ordinal")
    item=pc_insn.get(pc)
    if item is None:
        return None
    op,words=item
    field=slot_field(dex,op,words)
    return slots.get(field)

def renderer_holder_argument_witness(engine_entry, slots):
    dex,flags,off=engine_entry
    insns=list(audit.instructions(dex,off))
    by_pc={pc:(op,words) for pc,op,words in insns}
    try:
        result=audit.trace_identity_method(
            dex,ENGINE,flags,off,
            extra_identity_types=(HOLDER,"Landroidx/media3/exoplayer/i;"),
            capture_argument_provenance_targets=RENDERER_BOUNDARY,
            track_fields_from_any_receiver=True)
        complete=True
    except (audit.DexError,ValueError):
        return {"trace_complete":False,"exact_holder_call_observations":[]}
    events=[]
    for ev in result.get("events",()):
        if ev.get("kind")!="CALL_ARGUMENT_PROVENANCE":continue
        call=ev.get("callee") or {}
        callee=(call.get("owner"),call.get("method"),call.get("signature"))
        if callee not in RENDERER_BOUNDARY:continue
        holders=[]
        for arg in ev.get("reference_arguments",()):
            if arg.get("declared_argument_type")!=HOLDER:continue
            p=arg.get("producer")
            holders.append({
                "argument_position":arg.get("argument_position"),
                "producer_kind":p.get("kind") if isinstance(p,dict) else None,
                "producer_pc":p.get("ordinal") if isinstance(p,dict) else None,
                "direct_queue_slot":producer_queue_slot(p,by_pc,dex,slots),
                "identity_origin_categories":[
                    x.get("identity_type") for x in arg.get("identity_origins",())
                ][:6],
            })
        if holders:
            events.append({"call_pc":ev.get("ordinal"),"method":list(callee),
                           "holder_arguments":holders})
        if len(events)>50:
            raise ValueError("QUEUE_RENDERER_BOUNDARY_EVENT_LIMIT")
    return {"trace_complete":complete,"exact_holder_call_observations":events,
            "selected_rendering_period_from_this_observation_proven":False}



RENDERER_HELPER_METHODS=frozenset({
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"),
})
RENDERER_RELATED_OWNERS=frozenset({
    "Lxh6;","Lup1;","Lwh6;","Landroidx/media3/exoplayer/l;",
    "Landroidx/media3/exoplayer/k;","LmQ8;"
})

def exact_renderer_stream_register_map(dex, insns):
    """Register-level bounded comparison of exact holder/renderer stream.
    No literal values, private field names or media data exported."""
    out=[]
    for pc,op,words in insns:
        item={"pc":pc}
        if 0x52<=op<=0x5f:
            owner,_private,typ=audit.field_id(dex,words[1])
            if owner not in (HOLDER,"LmQ8;","Landroidx/media3/exoplayer/k;"):
                continue
            item.update(action="FIELD_READ_OR_WRITE",owner=owner,
                        field_type=typ,opcode=op,
                        value_register=(words[0]>>8)&15,
                        receiver_register=(words[0]>>12)&15)
        elif op==0x46:
            item.update(action="ARRAY_ELEMENT_READ",
                dest=(words[0]>>8)&255,
                array=words[1]&255,index=(words[1]>>8)&255)
        elif op in (0x32,0x33):
            item.update(action="REFERENCE_EQUALITY_BRANCH",opcode=op,
                left=(words[0]>>8)&15,right=(words[0]>>12)&15)
        elif 0x34<=op<=0x3d:
            item.update(action="OTHER_BRANCH",opcode=op)
        elif op in (0x07,0x08,0x09):
            dest,source=audit.move_object_registers(op,words)
            item.update(action="MOVE_OBJECT",dest=dest,source=source)
        elif op in (0x0a,0x0b,0x0c):
            item.update(action="MOVE_RESULT",dest=words[0]>>8)
        elif op in (0x0f,0x11,0x0e):
            item.update(action="RETURN",register=words[0]>>8)
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            method=dex.method(words[1])
            item.update(action="CALL",callee=list(method),
                        registers=audit.invoke_registers(op,words))
        else:continue
        out.append(item)
        if len(out)>100:raise ValueError("QUEUE_HELPER_REGISTER_ROW_LIMIT")
    return out


RENDER_STREAM_TYPE="LR29;"
RENDER_STREAM_ARRAY="[LR29;"
RENDER_GET_STREAM=("Landroidx/media3/exoplayer/k;","while","()LR29;")

def verify_renderer_attached_stream_comparator(method, entry):
    """Fail-closed exact bytecode equality-operand witness on one named helper.
    It shows a renderer's attached-stream accessor is *compared with* a
    holder-owned stream-array element. It does NOT claim equality at runtime.
    """
    dex,flags,off=entry
    by_pc={pc:(op,words) for pc,op,words in audit.instructions(dex,off)}
    if method[1]=="try":
        field_pc=4
        holder_read_pc=8
        renderer_caller_pcs=(10,16)
        renderer_result_pcs=(13,19)
        equality_pc=20
        renderer_register=3
        holder_stream_register=1
        second=(66,70,72,74,77,78)
    else:
        field_pc=2
        holder_read_pc=17
        renderer_caller_pcs=(13,)
        renderer_result_pcs=(16,)
        equality_pc=19
        renderer_register=2
        holder_stream_register=3
        second=(26,29,30,32)
    if not all(pc in by_pc for pc in (field_pc,holder_read_pc,equality_pc,
                            *renderer_caller_pcs,*renderer_result_pcs,*second)):
        raise ValueError("QUEUE_RENDER_STREAM_COMPARATOR_PCS_MISSING")
    fieldop,fieldwords=by_pc[field_pc]
    if fieldop!=0x54:
        raise ValueError("QUEUE_RENDER_STREAM_HOLDER_FIELD_OPCODE_MISMATCH")
    field_ref=audit.field_id(dex,fieldwords[1])
    if field_ref[0]!=HOLDER or field_ref[2]!=RENDER_STREAM_ARRAY:
        raise ValueError("QUEUE_RENDER_STREAM_HOLDER_ARRAY_MISMATCH")
    array_register=(fieldwords[0]>>8)&15
    aro,arwords=by_pc[holder_read_pc]
    if aro!=0x46 or ((arwords[0]>>8)&255)!=holder_stream_register:
        raise ValueError("QUEUE_RENDER_STREAM_ARRAY_READ_MISMATCH")
    # In try, the element overwrites its own array register. In new,
    # field array remains in v5 for both comparisons.
    if (arwords[1]&255)!=array_register and method[1]=="new":
        raise ValueError("QUEUE_RENDER_STREAM_ARRAY_ORIGIN_MISMATCH")
    for callerpc,resultpc in zip(renderer_caller_pcs,renderer_result_pcs):
        op,words=by_pc[callerpc]
        if op not in audit.INVOKES or dex.method(words[1])!=RENDER_GET_STREAM:
            raise ValueError("QUEUE_RENDER_EXACT_STREAM_GETTER_MISMATCH")
        mover,resultwords=by_pc[resultpc]
        if mover!=0x0c or resultwords[0]>>8!=renderer_register:
            raise ValueError("QUEUE_RENDER_STREAM_MOVE_RESULT_REGISTER_MISMATCH")
    test_op,testwords=by_pc[equality_pc]
    if test_op!=0x33:
        raise ValueError("QUEUE_RENDER_STREAM_REFERENCE_NE_MISSING")
    actual={(testwords[0]>>8)&15,(testwords[0]>>12)&15}
    if actual!={holder_stream_register,renderer_register}:
        raise ValueError("QUEUE_RENDER_STREAM_IDENTITY_OPERAND_MISMATCH")
    if method[1]=="try":
        nextop,nextwords=by_pc[66]
        arrayop,arraywords=by_pc[70]
        getop,getwords=by_pc[72]
        renderop,renderwords=by_pc[74]
        moveop,movewords=by_pc[77]
        cmpop,cmpwords=by_pc[78]
        if not (nextop==arrayop==0x54 and
                audit.field_id(dex,nextwords[1])[0:3][0]==HOLDER and
                audit.field_id(dex,nextwords[1])[2]==HOLDER and
                audit.field_id(dex,arraywords[1])==field_ref and
                getop==0x46 and renderop in audit.INVOKES and
                dex.method(renderwords[1])==RENDER_GET_STREAM and
                moveop==0x0c and cmpop==0x33):
            raise ValueError("QUEUE_RENDER_NEXT_HOLDER_STREAM_COMPARISON_MISMATCH")
        if {((cmpwords[0]>>8)&15),((cmpwords[0]>>12)&15)}!={8,9}:
            raise ValueError("QUEUE_RENDER_NEXT_HOLDER_OPERAND_MISMATCH")
        second_proof=True
    else:
        op26,w26=by_pc[26];op29,w29=by_pc[29]
        op30,w30=by_pc[30];op32,w32=by_pc[32]
        if not (op26 in audit.INVOKES and dex.method(w26[1])==RENDER_GET_STREAM and
                op29==0x0c and (w29[0]>>8)==2 and
                op30==0x46 and (w30[1]&255)==array_register and
                op32==0x33 and {(w32[0]>>8)&15,(w32[0]>>12)&15}=={2,5}):
            raise ValueError("QUEUE_RENDER_ALT_STREAM_IDENTITY_OPERAND_MISMATCH")
        second_proof=True
    return {
        "method":list(method),
        "same_exact_Lxh6_stream_field_compared_with_renderer_k_get_stream":True,
        "renderer_stream_type":RENDER_STREAM_TYPE,
        "holder_stream_array_type":RENDER_STREAM_ARRAY,
        "identity_inequality_branch_verified":True,
        "secondary_comparison_uses_same_holder_stream_field":second_proof,
        "current_runtime_equality_observed":False,
        "current_live_decoder_input_confirmed":False,
    }

def inspect_exact_renderer_helpers(targets):
    """Inspect ONLY two exact LmQ8 methods called with native queue B.
    This is still structural evidence, not an audio decoder proof."""
    rows=[]
    for method in sorted(RENDERER_HELPER_METHODS):
        if method not in targets or not targets[method][2]:
            raise ValueError("QUEUE_EXACT_RENDER_HELPER_BODY_MISSING")
        dex,flags,off=targets[method]
        insns=list(audit.instructions(dex,off))
        if len(insns)>700:
            raise ValueError("QUEUE_RENDER_HELPER_SIZE_LIMIT")
        methods=[]
        fields=[]
        allocations=[]
        for pc,op,words in insns:
            if op in audit.INVOKES and 0x6e<=op<=0x78:
                callee=dex.method(words[1])
                if len(methods)>=90:raise ValueError("QUEUE_HELPER_CALL_LIMIT")
                methods.append({"pc":pc,"owner":callee[0],"name":callee[1],
                                "signature":callee[2],
                                "related":callee[0] in RENDERER_RELATED_OWNERS})
            if 0x52<=op<=0x6d:
                owner,_name,typ=audit.field_id(dex,words[1])
                if owner in RENDERER_RELATED_OWNERS or typ in ("Lxh6;","Lup1;","Lwh6;","Landroidx/media3/exoplayer/l;"):
                    if len(fields)>=80:raise ValueError("QUEUE_HELPER_FIELD_LIMIT")
                    fields.append({"pc":pc,"field_owner":owner,
                                   "field_type":typ,"opcode":op})
            if op==0x22:
                if len(allocations)>=40:raise ValueError("QUEUE_HELPER_ALLOCATION_LIMIT")
                allocations.append({"pc":pc,"type":dex.descriptor(words[1])})
        rows.append({"method":method,"instruction_count":len(insns),
                     "direct_calls":methods,"related_field_type_accesses":fields,
                     "object_allocations":allocations,
                     "bounded_register_comparisons":exact_renderer_stream_register_map(dex,insns)})
    return rows

RENDERER_HELPER = ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z")

def exact_queue_front_successor(h_entry, slots):
    """Prove h.if advances one exact field via a typed holder successor.
    This is queue-head motion, NOT proof of currently audible decoder."""
    dex,flags,off=h_entry
    by_pc={pc:(op,words) for pc,op,words in audit.instructions(dex,off)}
    required=(49,51,53,58,60)
    if not all(pc in by_pc for pc in required):
        raise ValueError("QUEUE_FRONT_ADVANCE_PCS_MISSING")
    a49,w49=by_pc[49]
    a51,w51=by_pc[51]
    a53,w53=by_pc[53]
    a58,w58=by_pc[58]
    a60,w60=by_pc[60]
    if (a49,a51,a53,a58,a60)!=(0x54,0x54,0x5b,0x54,0x11):
        raise ValueError("QUEUE_FRONT_ADVANCE_OPCODE_MISMATCH")
    fields=[slot_field(dex,*by_pc[pc]) for pc in (49,53,58)]
    if len(set(fields))!=1 or slots.get(fields[0])!="SLOT_A":
        raise ValueError("QUEUE_FRONT_ADVANCE_EXACT_FIELD_MISMATCH")
    owner,name,typ=audit.field_id(dex,w51[1])
    if owner!=HOLDER or typ!=HOLDER:
        raise ValueError("QUEUE_FRONT_ADVANCE_SUCCESSOR_FIELD_MISSING")
    reg49=(w49[0]>>8)&15
    child_receiver=(w51[0]>>12)&15
    child_dest=(w51[0]>>8)&15
    store_value=(w53[0]>>8)&15
    returned_field_reg=(w58[0]>>8)&15
    return_reg=w60[0]>>8
    if not (reg49==child_receiver==child_dest==store_value==returned_field_reg==return_reg):
        raise ValueError("QUEUE_FRONT_ADVANCE_ALIAS_MISMATCH")
    if audit.field_id(dex,by_pc[10][1][1]) != audit.field_id(dex,w51[1]) or audit.field_id(dex,by_pc[18][1][1]) != audit.field_id(dex,w51[1]):
        raise ValueError("QUEUE_FRONT_ADVANCE_CONDITIONAL_NEXT_FIELD_MISMATCH")
    return {"exact_front_slot":"SLOT_A",
            "old_front_to_exact_holder_successor_to_new_front":True,
            "other_pointer_updates_use_same_holder_successor_field":True,
            "new_front_returned":True,
            "active_current_decoder_or_sound_proven":False}

def scoped_front_to_renderer_helper(engine_entry, slots):
    """CFG-safe alias of exact h.SLOT_B read into two already-anchored LmQ8 helper calls.
    Tracks only <=80 PC units from one field read. Reject unknown alias effects.
    No generic renderer/data/ByteBuffer scan."""
    dex,flags,off=engine_entry
    cfg=audit.build_dex_control_flow(dex,off)
    by_pc=cfg["by_pc"]
    successors=cfg["successors"]
    start=547
    end=605
    source=by_pc.get(start)
    if source is None or source[0]!=0x54 or slots.get(slot_field(dex,*source))!="SLOT_B":
        raise ValueError("QUEUE_EXACT_RENDER_SOURCE_NOT_B")
    source_reg=(source[1][0]>>8)&0xf
    targets={590:RENDERER_HELPER,598:RENDERER_HELPER}
    work=[(pc,frozenset((source_reg,))) for pc in successors.get(start,()) if start<pc<=end]
    seen=set()
    counts={pc:{"reaching":0,"identity_alias":0} for pc in targets}
    unhandled=[]
    max_states=1600
    no_dest=(set((0x00,0x0e,0x0f,0x10,0x11,0x1d,0x1e,0x26,0x27)) |
             set(range(0x28,0x2d)) |
             set(range(0x32,0x3e)) |
             set(range(0x4b,0x52)) |
             set(range(0x59,0x60)) |
             set(range(0x66,0x6e)))
    while work:
        pc, aliases=work.pop()
        if (pc,aliases) in seen:continue
        seen.add((pc,aliases))
        if len(seen)>max_states:raise ValueError("QUEUE_RENDER_CFG_LIMIT")
        item=by_pc.get(pc)
        if item is None:
            unhandled.append(pc);continue
        op,words=item
        next_alias=set(aliases)
        if pc in targets:
            callee=dex.method(words[1]) if op in audit.INVOKES and 0x6e<=op<=0x78 else None
            if callee!=targets[pc]:
                raise ValueError("QUEUE_RENDER_EXACT_CALLEE_MISMATCH")
            regs=audit.invoke_registers(op,words)
            if len(regs)<2:
                raise ValueError("QUEUE_RENDER_INVOKE_SHAPE_MISMATCH")
            counts[pc]["reaching"]+=1
            if regs[1] in aliases:
                counts[pc]["identity_alias"]+=1
        if op in audit.INVOKES:
            pass
        elif op in (0x07,0x08,0x09):
            dst,src=audit.move_object_registers(op,words)
            next_alias.discard(dst)
            if src in aliases:next_alias.add(dst)
        elif op==0x1f:
            pass
        elif op==0x0c:
            next_alias.discard(words[0]>>8)
        elif op in no_dest:
            pass
        else:
            written=audit.written_register(op,words)
            if written is None:
                unhandled.append(pc)
                continue
            next_alias.discard(written)
        for nextpc in successors.get(pc,()):
            if start<nextpc<=end:
                work.append((nextpc,frozenset(next_alias)))
    complete=not unhandled and all(x["reaching"] for x in counts.values())
    return {
        "source_slot":"SLOT_B","source_read_pc":start,
        "renderer_helper_target_calls":[
            {"pc":pc,**counts[pc],
             "same_exact_slot_B_on_all_reaching_states":bool(complete and counts[pc]["reaching"]==counts[pc]["identity_alias"])}
            for pc in sorted(counts)],
        "cfg_scan_complete":complete,
        "unmodeled_instruction_count":len(set(unhandled)),
        "same_selected_period_to_decoder_proven":False,
    }


STREAM_CLASS_BOUNDARY=frozenset({
    "LR29;","Landroidx/media3/exoplayer/k;","Landroidx/media3/exoplayer/l;",
})
STREAM_METHOD_BOUNDARY=frozenset({
    ("Landroidx/media3/exoplayer/k;","while","()LR29;"),
    ("Landroidx/media3/exoplayer/l;","while","()LR29;"),
})
def inspect_exact_renderer_stream_contract(stream_methods,stream_classes):
    """Exact typed renderer attached-stream getter / stream type declaration.
    This does not examine decoder byte payloads or broad renderer descendants."""
    rows=[]
    for method,(dex,flags,off) in sorted(stream_methods.items()):
        if method[0] not in STREAM_CLASS_BOUNDARY:continue
        if method[0]!="LR29;" and method not in STREAM_METHOD_BOUNDARY:continue
        row={"owner":method[0],"method":method[1],"signature":method[2],
             "abstract_or_native":bool(flags & (0x400|0x100)),
             "has_code":bool(off)}
        if off:
            insns=list(audit.instructions(dex,off))
            if len(insns)>170:raise ValueError("QUEUE_STREAM_METHOD_LIMIT")
            row["body_instructions"]=len(insns)
            row["typed_stream_field_reads"]=[]
            for pc,op,words in insns:
                if op in (0x54,0x5b):
                    owner,_private,typ=audit.field_id(dex,words[1])
                    if typ=="LR29;":
                        row["typed_stream_field_reads"].append({
                            "pc":pc,"field_owner":owner,"op":op})
        rows.append(row)
        if len(rows)>35:raise ValueError("QUEUE_STREAM_DECLARED_METHOD_COUNT_LIMIT")
    if "Landroidx/media3/exoplayer/k;" not in stream_classes or "LR29;" not in stream_classes:
        raise ValueError("QUEUE_STREAM_EXACT_CLASSES_NOT_DEFINED")
    getter_here=any(x["owner"]=="Landroidx/media3/exoplayer/k;" and
                    x["method"]=="while" and x["signature"]=="()LR29;" for x in rows)
    # An invoke reference owner can differ from the method's defining superclass.
    # Never assert the concrete getter owner before resolving the hierarchy.
    return {"renderer_get_stream_declared_on_exact_k_class":getter_here,
            "getter_definition_or_inheritance_resolved":getter_here,
            "stream_and_renderer_classes":stream_classes,
            "exact_bounded_stream_method_contracts":rows,
            "stream_attached_to_live_decoder_proven":False}


# NAV40 owner-phone follow-up: enumerate ALL direct DEX iput-object writes
# to the one publisher-signed h.SLOT_B field, not just the old bounded
# queue/engine method list. No private field names or values leave this audit.
# This direct-bytecode census does NOT rule out reflective/native mutations
# and does NOT attest currently selected Track/edition/queue generation.
SIGNED_SLOT_B_DIRECT_WRITES=frozenset({
    (ENGINE[0],"break","()V",307),
    (ENGINE[0],"break","()V",659),
    (QUEUE,"for","()V",35),
    (QUEUE,"if","()Lxh6;",12),
    (QUEUE,"while","(Lxh6;)I",25),
})

def validate_signed_slot_b_direct_writes(rows):
    """Fail closed on any missing, extra, duplicated or shifted write site."""
    if len(rows)!=len(set(rows)) or frozenset(rows)!=SIGNED_SLOT_B_DIRECT_WRITES:
        raise ValueError("QUEUE_SIGNED_SLOT_B_DIRECT_WRITES_CHANGED")
    return {
        "publisher_base_direct_iput_object_site_count":len(rows),
        "bounded_exact_site_proven":True,
        "reflective_or_native_mutations_excluded":False,
        "currently_selected_track_or_queue_epoch_proven":False,
    }

def signed_slot_b_direct_writer_census(apks,field):
    """Read all method bodies in exactly six signed original DEX files.

    Identify the same field only using exact owner/name/descriptor internally.
    Scan only actual opcode-boundary iput-object 0x5b, never raw byte matches.
    Do not export the private field name, Dex strings or user/media values.
    """
    rows=[]
    dex_seen=0
    dex_with_field=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("QUEUE_WRITER_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dex_seen+=1
                field_count,_=dex.table(80,8)
                ids={i for i in range(field_count)
                     if audit.field_id(dex,i)==field}
                if not ids:
                    continue
                dex_with_field+=1
                for method,_flags,code_off in audit.method_definitions_with_flags(dex):
                    units=dex.u32(code_off+12)
                    if units>3_000_000:
                        raise ValueError("QUEUE_WRITER_CODE_LIMIT")
                    # Fast negative test only. Every candidate is then parsed
                    # with the established fail-closed opcode-boundary iterator.
                    start=code_off+16
                    dex.bounds(start,units*2)
                    if b"\x5b" not in bytes(dex.data[start:start+units*2]):
                        continue
                    for pc,op,words in audit.instructions(dex,code_off):
                        if op==0x5b and words[1] in ids:
                            rows.append((*method,pc))
                            if len(rows)>len(SIGNED_SLOT_B_DIRECT_WRITES):
                                raise ValueError("QUEUE_WRITER_EXTRA_DIRECT_SITE")
    if dex_seen!=6 or dex_with_field!=1:
        raise ValueError("QUEUE_WRITER_SIGNED_DEX_COHORT_CHANGED")
    return {
        **validate_signed_slot_b_direct_writes(rows),
        "publisher_dex_scanned":dex_seen,
        "publisher_dex_referencing_exact_slot_b":dex_with_field,
        "writer_sites":[
            {"scope":"engine" if owner==ENGINE[0] else "queue",
             "pc":pc, "operation":"IPUT_OBJECT_EXACT_SLOT_B"}
            for owner,_name,_sig,pc in sorted(rows)
        ],
    }


# NAV40 exact signed-original five-writer *local* reference provenance.
# Never interpret same-reference register flow as a queue epoch, current
# selected edition, or a player/decoder replacement admission.
def verify_signed_slot_b_local_provenance(targets,slots):
    """Pinned-Dex instruction-site / branch-guard proof, fail closed.

    The verifier intentionally states LOCAL same-register relationships.
    It does not claim whole-program CFG dominance, runtime execution of the
    branch, absence of native/reflection writes or selected MediaItem.
    """
    a=targets[ENGINE]
    b=targets[(QUEUE,"if","()Lxh6;")]
    c=targets[(QUEUE,"while","(Lxh6;)I")]
    d=targets[(QUEUE,"for","()V")]
    def view(entry):
        dex,_flags,off=entry
        return dex,{pc:(op,w) for pc,op,w in audit.instructions(dex,off)}
    engine,e=view(a);advance,h=view(b);append,q=view(c);clear,z=view(d)
    rev={name:field for field,name in slots.items()}
    for slot in ("SLOT_A","SLOT_B","SLOT_C","SLOT_D"):
        if slot not in rev:raise ValueError("SLOT_B_PROVENANCE_SLOT_MISSING")
    def site(dex,ins,pc,opcode,field=None):
        actual=ins.get(pc)
        if actual is None or actual[0]!=opcode:
            raise ValueError("SLOT_B_PROVENANCE_OPCODE_DRIFT")
        op,w=actual
        if field is not None and audit.field_id(dex,w[1])!=field:
            raise ValueError("SLOT_B_PROVENANCE_FIELD_DRIFT")
        return w
    def registers(w):
        return ((w[0]>>8)&15,(w[0]>>12)&15)
    def require(condition):
        if not condition:raise ValueError("SLOT_B_PROVENANCE_REGISTER_OR_BRANCH_DRIFT")
    def holder_next(dex,ins,pc):
        w=site(dex,ins,pc,0x54)
        field=audit.field_id(dex,w[1])
        require(field[0]==HOLDER and field[2]==HOLDER)
        return field,registers(w)
    def branch_to(ins,at_pc,destination):
        # Exact 22t if-ne: verify the branch skips the STORE path;
        # comparison semantics stay restricted to this DEX opcode.
        w=site(None,ins,at_pc,0x33)
        offset=w[1] if w[1]<0x8000 else w[1]-0x10000
        require(at_pc+offset==destination)
        return registers(w)

    # e.break 305/307/309/313: one exact local holder register is
    # installed in A, B, C, D without any intervening register writes.
    init=[site(engine,e,pc,0x5b,rev[slot])
          for pc,slot in ((305,"SLOT_A"),(307,"SLOT_B"),
                          (309,"SLOT_C"),(313,"SLOT_D"))]
    require(len({registers(w) for w in init})==1)
    require(site(engine,e,311,0x5b) is not None)  # field store, no register overwrite
    # e.break 652 → 657 → 659: exact prior B holder's typed
    # successor is stored back to B with the same receiver.
    b_read=registers(site(engine,e,652,0x54,rev["SLOT_B"]))
    _,next_engine=holder_next(engine,e,657)
    b_store=registers(site(engine,e,659,0x5b,rev["SLOT_B"]))
    require(b_read[0]==next_engine[0]==next_engine[1]==b_store[0])
    require(b_read[1]==b_store[1])
    site(engine,e,654,0x71) # invoke-static, cannot overwrite local DEX register

    # h.if 6/8/10/12: if old front equals B, update B to that
    # front's exact typed successor. The unequal branch jumps over store.
    front=registers(site(advance,h,0,0x54,rev["SLOT_A"]))
    b_old=registers(site(advance,h,6,0x54,rev["SLOT_B"]))
    comparison=branch_to(h,8,14)
    successor_field,succ=holder_next(advance,h,10)
    saved=registers(site(advance,h,12,0x5b,rev["SLOT_B"]))
    require(set(comparison)=={front[0],b_old[0]})
    require(succ==(b_old[0],front[0]))
    require(saved==(succ[0],b_old[1]))
    # h.if 49/51/53 original front advance uses same exact holder
    # successor, not merely same declared field type.
    _,front_next=holder_next(advance,h,51)
    require(audit.field_id(advance,h[51][1][1])==successor_field)
    require(front_next==(registers(site(advance,h,49,0x54,rev["SLOT_A"]))[0],)*2)
    require(registers(site(advance,h,53,0x5b,rev["SLOT_A"]))[0]==front_next[0])
    require(audit.field_id(engine,e[657][1][1])==successor_field)

    # h.while 19/21/23/25: conditional B -> A reference assignment;
    # comparing old B with successor does NOT establish selected edition.
    old_b=registers(site(append,q,19,0x54,rev["SLOT_B"]))
    guard=branch_to(q,21,30)
    src_a=registers(site(append,q,23,0x54,rev["SLOT_A"]))
    dst_b=registers(site(append,q,25,0x5b,rev["SLOT_B"]))
    require(old_b[1]==src_a[1]==dst_b[1])
    require(src_a==dst_b)
    require(old_b[0] in guard)
    # h.for 30..37: zero local value written into A,D,B,C.
    const=site(clear,z,30,0x12)
    require(const[0]==0x0012) # const/4 v0, 0; no secret values exported
    nulled=[site(clear,z,pc,0x5b,rev[slot])
            for pc,slot in ((31,"SLOT_A"),(33,"SLOT_D"),
                            (35,"SLOT_B"),(37,"SLOT_C"))]
    require(len({registers(w) for w in nulled})==1)
    require(registers(nulled[0])[0]==0)
    return {
        "exact_writer_local_reference_origin_categories":[
            {"site":"ENGINE_INIT_PC307", "origin":"INITIAL_SAME_HOLDER_REFERENCE"},
            {"site":"ENGINE_ADVANCE_PC659", "origin":"OLD_SLOT_B_HOLDER_SUCCESSOR"},
            {"site":"QUEUE_ADVANCE_PC12", "origin":"FRONT_HOLDER_SUCCESSOR_CONDITIONAL"},
            {"site":"QUEUE_UPDATE_PC25", "origin":"SLOT_A_REFERENCE_CONDITIONAL"},
            {"site":"QUEUE_CLEAR_PC35", "origin":"ZERO_NULL_REFERENCE"},
        ],
        "site_opcode_and_register_proven":True,
        "signed_holder_successor_field_same_across_engine_and_queue":True,
        "conditional_skip_branch_pc_verified":True,
        "whole_program_queue_epoch_proven":False,
        "runtime_selected_edition_proven":False,
        "reflective_or_native_mutations_excluded":False,
    }


# NAV40 static candidate: original SLOT_B holder's mutable period-info
# pointer, immutable period-info->period-id pointer and period-id long slot.
# This does NOT identify the user's current song, edition or queue generation.
PERIOD_INFO="Lyh6;"
PERIOD_ID="LSl6$b;"
SIGNED_PERIOD_TOKEN_CTORS=frozenset({
    (HOLDER,"<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V"),
    (PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V"),
    (PERIOD_ID,"<init>","(Ljava/lang/Object;IIJI)V"),
})
SIGNED_PERIOD_TOKEN_WRITERS={
    "holder_period_info":frozenset({
        ("Landroidx/media3/exoplayer/e;","break","()V",283),
        ("Landroidx/media3/exoplayer/e;","default","(LSl6$b;JJJZI)LCD7;",151),
        ("Landroidx/media3/exoplayer/e;","i","(LSl6$b;JZZ)J",128),
        ("Landroidx/media3/exoplayer/e;","static","(LTva;Z)V",839),
        ("Landroidx/media3/exoplayer/h;","return","(LTva;)I",69),
        ("Landroidx/media3/exoplayer/h;","static","(LTva;JJJ)I",48),
        (HOLDER,"<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V",18),
        (HOLDER,"else","(FLTva;Z)V",68),
    }),
    "period_info_id":frozenset({
        (PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V",48),
    }),
    "period_id_long":frozenset({
        (PERIOD_ID,"<init>","(Ljava/lang/Object;IIJI)V",9),
    }),
}
def validate_signed_period_token_writers(observed):
    """Exact pinned expected member writes, no private field names output."""
    for alias,expected in SIGNED_PERIOD_TOKEN_WRITERS.items():
        actual=observed.get(alias)
        if actual is None or len(actual)!=len(set(actual)) or set(actual)!=set(expected):
            raise ValueError("QUEUE_PERIOD_TOKEN_DIRECT_WRITER_MISMATCH")
    if set(observed)!=set(SIGNED_PERIOD_TOKEN_WRITERS):
        raise ValueError("QUEUE_PERIOD_TOKEN_UNEXPECTED_FIELD_CATEGORY")
    return {
        "holder_period_info_direct_writers":len(observed["holder_period_info"]),
        "period_info_id_direct_writers":len(observed["period_info_id"]),
        "period_id_long_direct_writers":len(observed["period_id_long"]),
        "holder_info_mutable_in_original":True,
        "period_token_direct_writer_guard_pass":True,
        "same_holder_cannot_be_assumed_same_period_info":True,
        "original_selected_edition_or_queue_epoch_proven":False,
        "reflection_or_native_mutations_excluded":False,
    }

SIGNED_PERIOD_INFO_REFRESH=(HOLDER,"else","(FLTva;Z)V")
SIGNED_PERIOD_INFO_CLONE=(PERIOD_INFO,"for","(J)Lyh6;")

def verify_signed_period_info_refresh_preserves_id(targets,holder_field,info_field):
    """Signed same Java ID path in a holder-internal info refresh.

    Even if a holder has the SAME period-id reference after a refresh,
    current song/edition, generation and audible PCM remain unproven.
    """
    holder,_,holder_off=targets[SIGNED_PERIOD_INFO_REFRESH]
    info,_,info_off=targets[SIGNED_PERIOD_INFO_CLONE]
    h={pc:(op,w) for pc,op,w in audit.instructions(holder,holder_off)}
    n={pc:(op,w) for pc,op,w in audit.instructions(info,info_off)}
    def site(tab,pc,op):
        if pc not in tab or tab[pc][0]!=op:
            raise ValueError("QUEUE_PERIOD_INFO_REFRESH_OPCODE_DRIFT")
        return tab[pc][1]
    read=site(h,56,0x54)
    store=site(h,68,0x5b)
    if (audit.field_id(holder,read[1])!=holder_field
        or audit.field_id(holder,store[1])!=holder_field):
        raise ValueError("QUEUE_PERIOD_INFO_REFRESH_FIELD_DRIFT")
    rreg=(read[0]>>8)&15
    owner=(read[0]>>12)&15
    saved=(store[0]>>8)&15
    saved_owner=(store[0]>>12)&15
    call=site(h,64,0x6e)
    if holder.method(call[1])!=SIGNED_PERIOD_INFO_CLONE:
        raise ValueError("QUEUE_PERIOD_INFO_REFRESH_METHOD_DRIFT")
    invoked=audit.invoke_registers(0x6e,call)
    move_result=site(h,67,0x0c)
    if (invoked[0]!=rreg or len(invoked)!=3 or
        ((move_result[0]>>8)&255)!=saved or owner!=saved_owner):
        raise ValueError("QUEUE_PERIOD_INFO_REFRESH_REGISTER_DRIFT")
    # The cloned new Lyh6 uses EXACT original LSl6$b reference
    # extracted from the former Lyh6; no value/equals fallback.
    token_read=site(n,15,0x54)
    if audit.field_id(info,token_read[1])!=info_field:
        raise ValueError("QUEUE_PERIOD_INFO_CLONE_ID_FIELD_DRIFT")
    token_register=(token_read[0]>>8)&15
    constructor=site(n,33,0x76)
    if (info.method(constructor[1])!=(
            PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V")
        or constructor[0]>>8!=15
        or constructor[2]+1!=token_register):
        raise ValueError("QUEUE_PERIOD_INFO_CLONE_ID_REGISTER_DRIFT")
    for pc,op,w in audit.instructions(info,info_off):
        if pc<=15:continue
        if pc>=33:break
        if audit.written_register(op,w)==token_register:
            raise ValueError("QUEUE_PERIOD_INFO_CLONE_ID_OVERWRITTEN")
    return {
        "holder_in_place_period_info_refresh_proven":True,
        "refreshed_period_info_can_retain_same_java_period_id":True,
        "same_period_id_not_sufficient_as_monotonic_queue_epoch":True,
        "currently_selected_edition_or_queue_generation_proven":False,
    }

def signed_holder_period_token_census(apks,targets):
    """Anchor 3 exact original ctor instructions then scan all signed DEX.

    No period-id values, opaque field names, window identifiers, album IDs,
    media details or audio data are read/exported. A long field is NOT proof
    of generation semantics or monotonicity.
    """
    def verify_ctor(method,pc,opcode,owner,typ):
        dex,_flags,off=targets[method]
        table={x:(o,w) for x,o,w in audit.instructions(dex,off)}
        if pc not in table or table[pc][0]!=opcode:
            raise ValueError("QUEUE_PERIOD_TOKEN_CTOR_OPCODE_DRIFT")
        w=table[pc][1]
        f=audit.field_id(dex,w[1])
        if f[0]!=owner or f[2]!=typ:
            raise ValueError("QUEUE_PERIOD_TOKEN_CTOR_TYPE_DRIFT")
        return dex,off,table,w,f
    holder_ctor=(HOLDER,"<init>",
        "([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
    info_ctor=(PERIOD_INFO,"<init>","(LSl6$b;JJJJZZZZZ)V")
    id_ctor=(PERIOD_ID,"<init>","(Ljava/lang/Object;IIJI)V")
    holder,holder_off,holder_ins,holder_word,holder_info=verify_ctor(
        holder_ctor,18,0x5b,HOLDER,PERIOD_INFO)
    info,info_off,info_ins,info_word,info_id=verify_ctor(
        info_ctor,48,0x5b,PERIOD_INFO,PERIOD_ID)
    period,period_off,period_ins,period_word,period_long=verify_ctor(
        id_ctor,9,0x5a,PERIOD_ID,"J")
    # Exact class ctor parameter-to-field locals: holder moves its
    # incoming period-info argument at PC0 into v2, then stores v2 to
    # this at PC18. No intervening store to v2 within bounded PC0..18.
    if (holder.u16(holder_off)!=16 or holder.u16(holder_off+2)!=9
        or holder_ins.get(0)!=(0x07,(0xe207,))
        or ((holder_word[0]>>8)&15,(holder_word[0]>>12)&15)!=(2,7)):
        raise ValueError("QUEUE_PERIOD_TOKEN_HOLDER_CTOR_REGISTER_DRIFT")
    for pc,op,w in audit.instructions(holder,holder_off):
        if pc<=0:continue
        if pc>=18:break
        if audit.written_register(op,w)==2:
            raise ValueError("QUEUE_PERIOD_TOKEN_HOLDER_ARG_OVERWRITE")
    if (info.u16(info_off)!=22 or info.u16(info_off+2)!=15
        or ((info_word[0]>>8)&15,(info_word[0]>>12)&15)!=(8,7)):
        raise ValueError("QUEUE_PERIOD_TOKEN_INFO_CTOR_REGISTER_DRIFT")
    if (period.u16(period_off)!=7 or period.u16(period_off+2)!=7
        or ((period_word[0]>>8)&15,(period_word[0]>>12)&15)!=(4,0)):
        raise ValueError("QUEUE_PERIOD_TOKEN_ID_CTOR_REGISTER_DRIFT")
    anchored={
        "holder_period_info":(holder_info,0x5b),
        "period_info_id":(info_id,0x5b),
        "period_id_long":(period_long,0x5a),
    }
    rows={k:[] for k in anchored}
    dex_seen=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("QUEUE_PERIOD_TOKEN_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dex_seen+=1
                field_count,_=dex.table(80,8)
                ids={}
                for idx in range(field_count):
                    f=audit.field_id(dex,idx)
                    for alias,(target_field,opcode) in anchored.items():
                        if f==target_field:ids[idx]=(alias,opcode)
                if not ids:continue
                for method,_flags,off in audit.method_definitions_with_flags(dex):
                    size=dex.u32(off+12)
                    if size>3_000_000:
                        raise ValueError("QUEUE_PERIOD_TOKEN_CODE_LIMIT")
                    start=off+16
                    dex.bounds(start,size*2)
                    buf=bytes(dex.data[start:start+size*2])
                    # Fast precheck only; opcode positions are validated by
                    # fail-closed iterator before any site is counted.
                    if b"\x5b" not in buf and b"\x5a" not in buf:
                        continue
                    for pc,op,w in audit.instructions(dex,off):
                        if op not in (0x5b,0x5a):continue
                        match=ids.get(w[1])
                        if match is None:continue
                        alias,expected_op=match
                        if op!=expected_op:continue
                        rows[alias].append((*method,pc))
                        if len(rows[alias])>len(SIGNED_PERIOD_TOKEN_WRITERS[alias]):
                            raise ValueError("QUEUE_PERIOD_TOKEN_TOO_MANY_WRITES")
    if dex_seen!=6:raise ValueError("QUEUE_PERIOD_TOKEN_SIGNED_DEX_COUNT")
    return {
        **validate_signed_period_token_writers(rows),
        "publisher_dex_scanned":dex_seen,
        "exact_holder_info_to_period_id_to_long_typed_chain":True,
        "exact_holder_info_constructor_argument_retained":True,
        "signed_holder_info_refresh_id_preservation":
            verify_signed_period_info_refresh_preserves_id(targets,holder_info,info_id),
    }


# Read-only discovery: enumerate the exact signed-original MediaPeriodId
# constructor callsites. A callsite does not imply current playback.
# No instance values, media IDs, string contents or private field names.
MAX_SIGNED_PERIOD_ID_CTOR_SITES=512

SIGNED_PERIOD_ID_CTOR_DIRECT_SITES=frozenset({
    ("LCD7;","<clinit>","()V",7,"(Ljava/lang/Object;)V",112),
    ("LQM2;","case","(Llo$a;)V",120,"(IJLjava/lang/Object;)V",112),
    ("LQM2;","try","(Llo$a;)V",88,"(JLjava/lang/Object;)V",112),
    ("LSl6$b;","<init>","(IJLjava/lang/Object;)V",6,"(Ljava/lang/Object;IIJI)V",118),
    ("LSl6$b;","<init>","(JLjava/lang/Object;)V",6,"(Ljava/lang/Object;IIJI)V",118),
    ("LSl6$b;","<init>","(Ljava/lang/Object;)V",2,"(JLjava/lang/Object;)V",112),
    ("LSl6$b;","if","(Ljava/lang/Object;)LSl6$b;",20,"(Ljava/lang/Object;IIJI)V",118),
    ("LUKb$c;","if","(LSl6;LTva;)V",61,"(Ljava/lang/Object;)V",112),
    ("LUKb;","if","(LUKb;)V",164,"(Ljava/lang/Object;)V",112),
    ("Landroidx/media3/exoplayer/d;","M0","(LCD7;LTva;Landroid/util/Pair;)LCD7;",92,"(Ljava/lang/Object;)V",112),
    ("Landroidx/media3/exoplayer/e;","throwables","(ZZZZ)V",277,"(JLjava/lang/Object;)V",112),
    ("Landroidx/media3/exoplayer/h;","else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;",11,"(Ljava/lang/Object;IIJI)V",118),
    ("Landroidx/media3/exoplayer/h;","goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;",103,"(IJLjava/lang/Object;)V",112),
    ("Landroidx/media3/exoplayer/h;","import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;",126,"(IJLjava/lang/Object;)V",112),
    ("Landroidx/media3/exoplayer/h;","import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;",139,"(Ljava/lang/Object;IIJI)V",118),
})

def validate_signed_period_id_ctor_sites(rows,exact_signed=False):
    """Only exact, distinct, opcode-aligned constructor references qualify."""
    if not rows or len(rows)>MAX_SIGNED_PERIOD_ID_CTOR_SITES:
        raise ValueError("QUEUE_PERIOD_ID_CTOR_SITE_COUNT")
    seen=set()
    signatures={}
    for row in rows:
        if (len(row)!=6 or not all(isinstance(x,str) for x in row[:3])
                or not isinstance(row[3],int) or row[3]<0
                or not isinstance(row[4],str) or row[5] not in (0x70,0x76)
                or not row[4].startswith("(") or not row[4].endswith(")V")):
            raise ValueError("QUEUE_PERIOD_ID_CTOR_SITE_SHAPE")
        if row in seen:
            raise ValueError("QUEUE_PERIOD_ID_CTOR_DUPLICATE_SITE")
        seen.add(row)
        signatures[row[4]]=signatures.get(row[4],0)+1
    if exact_signed and seen!=SIGNED_PERIOD_ID_CTOR_DIRECT_SITES:
        raise ValueError("QUEUE_PERIOD_ID_CTOR_EXACT_SIGNED_SITE_DRIFT")
    return {
        "exact_direct_constructor_callsite_count":len(rows),
        "constructor_signatures_and_counts":sorted(signatures.items()),
        "distinct_instruction_site_guard":True,
        "selected_player_item_generation_at_audio_read_proven":False,
        "callsites_without_reflection_or_native_exclusion":True,
    }

def wide_definition_register_shape(pc,op,words):
    """Only DEX register layout; never read constants or field values/names."""
    if op==0x04:
        return {"pc":pc,"kind":"MOVE_WIDE","dest":(words[0]>>8)&15,
                "source":(words[0]>>12)&15}
    if op==0x05:
        return {"pc":pc,"kind":"MOVE_WIDE_FROM16","dest":words[0]>>8,
                "source":words[1]}
    if op==0x06:
        return {"pc":pc,"kind":"MOVE_WIDE_16","dest":words[1],
                "source":words[2]}
    kinds={0x0b:"MOVE_RESULT_WIDE",0x16:"CONST_WIDE_16",
           0x17:"CONST_WIDE_32",0x18:"CONST_WIDE",0x19:"CONST_WIDE_HIGH16",
           0x53:"IGET_WIDE",0x61:"SGET_WIDE"}
    if op in kinds:
        reg=((words[0]>>8)&15) if op==0x53 else (words[0]>>8)
        return {"pc":pc,"kind":kinds[op],"dest":reg}
    return None


# A narrow normal-control-flow guard for the exact original Queue ID long
# argument. This proves parameter provenance only, never a selected track,
# epoch, audible event, or absence of exceptional/native/reflection changes.
SIGNED_ID_LONG_HANDOFF_SITES=frozenset({
    (QUEUE,"import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;",126,124,18,10),
    (QUEUE,"import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;",139,130,18,10),
    (QUEUE,"else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;",11,9,23,4),
    (QUEUE,"goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;",103,101,34,14),
})

def verify_signed_id_long_normal_cfg(dex,method,flags,off,invoke_pc,move_pc,source_reg,dest_reg):
    """Use signed CFG, not adjacent PCs alone; fail closed on skipped/clobbered moves."""
    cfg=audit.build_dex_control_flow(dex,off)
    by_pc=cfg["by_pc"]
    successors=cfg["successors"]
    move=by_pc.get(move_pc)
    invoke=by_pc.get(invoke_pc)
    parameter_regs=audit.typed_parameter_registers(dex,method,flags,off,"J")
    if (move is None or move[0]!=0x05 or
        move[1][0]>>8!=dest_reg or move[1][1]!=source_reg
        or source_reg not in parameter_regs or invoke is None
        or invoke[0] not in (0x70,0x76)):
        raise ValueError("QUEUE_ID_LONG_EXACT_TARGET_SHAPE_DRIFT")
    descriptor=dex.method(invoke[1][1])
    if descriptor[0]!=PERIOD_ID or descriptor[1]!="<init>":
        raise ValueError("QUEUE_ID_LONG_NOT_PERIOD_ID_CONSTRUCTOR")
    arg_regs=audit.invoke_registers(invoke[0],invoke[1])
    index=1
    j_words=[]
    for param in audit.parse_types(descriptor[2]):
        if param=="J":j_words.append(arg_regs[index])
        index+=2 if param in ("J","D") else 1
    if j_words!=[dest_reg]:
        raise ValueError("QUEUE_ID_LONG_ARGUMENT_REGISTER_DRIFT")
    if not (cfg["entry"] in cfg["reachable"] and
            invoke_pc in cfg["reachable"] and move_pc in cfg["reachable"]):
        raise ValueError("QUEUE_ID_LONG_UNREACHABLE_TARGET")
    if len(cfg["reachable"])>1200:
        raise ValueError("QUEUE_ID_LONG_CFG_SCOPE_LIMIT")
    def can_reach_excluding(excluded):
        seen=set()
        todo=[cfg["entry"]]
        while todo:
            here=todo.pop()
            if here in seen or here in excluded:continue
            seen.add(here)
            if here==invoke_pc:return True
            todo.extend(successors.get(here,()))
        return False
    dominated=not can_reach_excluding({move_pc})
    # Detect any writing to source J word on a normal path reaching the
    # copy, and any writing to destination J word from copy to call.
    def may_clobber(start,stop,pair,skip_start=False):
        todo=[start]
        seen=set()
        while todo:
            here=todo.pop()
            if here==stop:continue
            if here in seen:continue
            seen.add(here)
            if not (skip_start and here==start):
                op,words=by_pc[here]
                written=audit.written_register(op,words)
                if written in pair:
                    return True
                shape=wide_definition_register_shape(here,op,words)
                if shape is not None and shape["dest"]+1 in pair:
                    return True
            todo.extend(successors.get(here,()))
        return False
    before_move_write=may_clobber(cfg["entry"],move_pc,{source_reg,source_reg+1})
    after_move_write=any(
        may_clobber(pc,invoke_pc,{dest_reg,dest_reg+1})
        for pc in successors[move_pc])
    proven=bool(dominated and not before_move_write and not after_move_write)
    return {
        "caller":list(method),
        "ctor_pc":invoke_pc,
        "source_move_pc":move_pc,
        "normal_cfg_move_dominates_ctor":dominated,
        "normal_cfg_input_J_not_overwritten_before_move":not before_move_write,
        "normal_cfg_copy_J_not_overwritten_before_ctor":not after_move_write,
        "original_caller_J_parameter_proven_at_ctor_on_normal_paths":proven,
        "exceptional_control_flow_or_selection_proven":False,
        "selected_item_or_queue_epoch_proven":False,
    }


SIGNED_QUEUE_ID_BUILDERS=frozenset({
    (QUEUE,"import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;"),
    (QUEUE,"else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;"),
    (QUEUE,"goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;"),
})
MAX_SIGNED_QUEUE_ID_BUILDERS_DIRECT_CALLS=96

SIGNED_QUEUE_ID_BUILDER_PINNED_DIRECT_SITES=frozenset({
    ("Landroidx/media3/exoplayer/h;","case","(LTva;LSl6$b;JJ)Lyh6;",25,("Landroidx/media3/exoplayer/h;","else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;"),116),
    ("Landroidx/media3/exoplayer/h;","case","(LTva;LSl6$b;JJ)Lyh6;",40,("Landroidx/media3/exoplayer/h;","goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;"),116),
    ("Landroidx/media3/exoplayer/h;","native","(LTva;Ljava/lang/Object;J)LSl6$b;",180,("Landroidx/media3/exoplayer/h;","import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;"),119),
    ("Landroidx/media3/exoplayer/h;","new","(LTva;Lxh6;J)Lyh6;",148,("Landroidx/media3/exoplayer/h;","import","(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;"),119),
    ("Landroidx/media3/exoplayer/h;","try","(LTva;Lxh6;J)Lyh6;",84,("Landroidx/media3/exoplayer/h;","else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;"),116),
    ("Landroidx/media3/exoplayer/h;","try","(LTva;Lxh6;J)Lyh6;",179,("Landroidx/media3/exoplayer/h;","goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;"),116),
    ("Landroidx/media3/exoplayer/h;","try","(LTva;Lxh6;J)Lyh6;",245,("Landroidx/media3/exoplayer/h;","else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;"),116),
    ("Landroidx/media3/exoplayer/h;","try","(LTva;Lxh6;J)Lyh6;",290,("Landroidx/media3/exoplayer/h;","goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;"),116),
})


def validate_signed_queue_id_builder_callers(rows,exact_signed=False):
    """Normal invoke sites only, never inferred runtime selection or epoch."""
    if not rows or len(rows)>MAX_SIGNED_QUEUE_ID_BUILDERS_DIRECT_CALLS:
        raise ValueError("QUEUE_ID_BUILDERS_CALLSITE_COUNT")
    if len(rows)!=len(set(rows)):
        raise ValueError("QUEUE_ID_BUILDERS_DUPLICATE_CALLSITE")
    for row in rows:
        if len(row)!=6 or not all(isinstance(a,str) for a in row[:3]) or (
            not isinstance(row[3],int) or row[3]<0 or row[4] not in SIGNED_QUEUE_ID_BUILDERS
            or row[5] not in audit.INVOKES):
            raise ValueError("QUEUE_ID_BUILDERS_CALLSITE_SHAPE")
    if exact_signed and set(rows)!=SIGNED_QUEUE_ID_BUILDER_PINNED_DIRECT_SITES:
        raise ValueError("QUEUE_ID_BUILDERS_PINNED_ORIGINAL_SITE_DRIFT")
    return {
        "exact_direct_callsite_count":len(rows),
        "direct_method_call_sites_not_runtime_dispatch":True,
        "original_queue_epoch_or_selected_edition_proven":False,
    }

def signed_wide_writer_type_only(dex,pc,op,words):
    """Typed field declaration only; never disclose obfuscated field name or value."""
    shape=wide_definition_register_shape(pc,op,words)
    if shape is None:return None
    if op in (0x53,0x61):
        owner,_private,typ=audit.field_id(dex,words[1])
        if typ!="J":
            raise ValueError("QUEUE_WIDE_OWNER_FIELD_TYPE_MISMATCH")
        shape={
            **shape,
            "declaring_class":owner,
            "field_type":"J",
            "instance_field_receiver_register":(
                ((words[0]>>12)&15) if op==0x53 else None),
        }
    return shape


SIGNED_OLD_ID_J_REUSE_CALLER=(QUEUE,"case","(LTva;LSl6$b;JJ)Lyh6;")
SIGNED_OLD_ID_J_REUSE_SITES=(
    (13,25,(QUEUE,"else","(LTva;Ljava/lang/Object;IIJJZ)Lyh6;"),1,8),
    (30,40,(QUEUE,"goto","(LTva;Ljava/lang/Object;JJJZ)Lyh6;"),2,7),
)

def verify_signed_old_period_id_long_handoff(targets):
    """Exact old MediaPeriodId.J field -> Queue builder's J parameter.

    This is NORMAL CFG same-field provenance, not an executed transition,
    playback generation, current selected item, or source-to-decoder proof.
    """
    caller=SIGNED_OLD_ID_J_REUSE_CALLER
    ctor=(PERIOD_ID,"<init>","(Ljava/lang/Object;IIJI)V")
    if caller not in targets or ctor not in targets:
        raise ValueError("QUEUE_OLD_ID_REUSE_TARGET_MISSING")
    dex,flags,off=targets[caller]
    id_dex,_id_flags,id_off=targets[ctor]
    ctor_pcs={pc:(op,w) for pc,op,w in audit.instructions(id_dex,id_off)}
    anchored=ctor_pcs.get(9)
    if anchored is None or anchored[0]!=0x5a:
        raise ValueError("QUEUE_OLD_ID_FIELD_CTOR_DRIFT")
    original_J_field=audit.field_id(id_dex,anchored[1][1])
    if original_J_field[0]!=PERIOD_ID or original_J_field[2]!="J":
        raise ValueError("QUEUE_OLD_ID_FIELD_TYPE_DRIFT")
    cfg=audit.build_dex_control_flow(dex,off)
    by_pc=cfg["by_pc"]
    succ=cfg["successors"]
    if len(cfg["reachable"])>1200:
        raise ValueError("QUEUE_OLD_ID_CFG_LIMIT")
    input_ids=audit.typed_parameter_registers(dex,caller,flags,off,PERIOD_ID)
    if len(input_ids)!=1:
        raise ValueError("QUEUE_OLD_ID_TYPED_PARAM_COUNT")
    input_id=next(iter(input_ids))
    def avoid_reaches(start,destination,avoid):
        pending=[start]
        seen=set()
        while pending:
            pc=pending.pop()
            if pc in seen or pc in avoid:continue
            seen.add(pc)
            if pc==destination:return True
            pending.extend(succ.get(pc,()))
        return False
    def path_may_write(start,stop,regs):
        pending=[start]
        visited=set()
        while pending:
            pc=pending.pop()
            if pc in visited or pc==stop:continue
            visited.add(pc)
            op,words=by_pc[pc]
            written=audit.written_register(op,words)
            shape=wide_definition_register_shape(pc,op,words)
            if written in regs or (shape is not None and
                                   (shape["dest"] in regs or shape["dest"]+1 in regs)):
                return True
            pending.extend(succ.get(pc,()))
        return False
    rows=[]
    for read_pc,call_pc,target,j_ordinal,expected_register in SIGNED_OLD_ID_J_REUSE_SITES:
        source=by_pc.get(read_pc)
        call=by_pc.get(call_pc)
        if source is None or source[0]!=0x53 or call is None or (
                call[0] not in audit.INVOKES):
            raise ValueError("QUEUE_OLD_ID_J_SITE_OPCODE_DRIFT")
        value_register=(source[1][0]>>8)&15
        recv=(source[1][0]>>12)&15
        if (audit.field_id(dex,source[1][1])!=original_J_field or
            recv!=input_id or value_register!=expected_register or
            dex.method(call[1][1])!=target):
            raise ValueError("QUEUE_OLD_ID_J_FIELD_OR_RECEIVER_DRIFT")
        invoked=audit.invoke_registers(call[0],call[1])
        index=0 if call[0] in (0x71,0x77) else 1
        Jregs=[]
        for param in audit.parse_types(target[2]):
            if param=="J":Jregs.append(invoked[index])
            index+=2 if param in ("J","D") else 1
        if len(Jregs)<=j_ordinal or Jregs[j_ordinal]!=value_register:
            raise ValueError("QUEUE_OLD_ID_J_INVOKE_REGISTER_DRIFT")
        dominates=(
            read_pc in cfg["reachable"] and call_pc in cfg["reachable"]
            and not avoid_reaches(cfg["entry"],call_pc,{read_pc}))
        caller_id_retained=not path_may_write(
            cfg["entry"],read_pc,{input_id})
        source_unclobbered=not any(
            path_may_write(pc,call_pc,{value_register,value_register+1})
            for pc in succ.get(read_pc,()))
        proven=bool(dominates and caller_id_retained and source_unclobbered)
        rows.append({
            "caller_method":list(caller),
            "old_period_id_j_read_pc":read_pc,
            "queue_builder_call_pc":call_pc,
            "builder":list(target),
            "same_exact_old_period_id_j_field":True,
            "read_receiver_is_exact_typed_id_parameter":True,
            "old_J_read_dominates_builder_call_on_normal_cfg":dominates,
            "old_id_reference_not_overwritten_before_read":caller_id_retained,
            "old_J_register_not_overwritten_before_call":source_unclobbered,
            "old_period_id_J_forwarded_to_new_period_id_constructor_on_normal_cfg":proven,
            "current_selected_item_or_queue_generation_proven":False,
        })
    return {
        "old_id_J_field_reaches_two_builder_paths_on_all_normal_cfg":
            all(row["old_period_id_J_forwarded_to_new_period_id_constructor_on_normal_cfg"]
                for row in rows),
        "verified_exact_original_old_id_J_field_vs_ctor":True,
        "signed_source_sites":rows,
        "exceptional_control_flow_native_or_reflection_excluded":False,
        "current_selected_item_or_unique_playback_generation_proven":False,
    }

def signed_period_id_constructor_site_census(apks):
    """Scan all six publisher-signed DEX for invoke-direct(*/range) of LSl6$b.<init>.

    This is constructor *site discovery*, never a semantic epoch or
    proof that a constructed ID is the actively rendered queue period.
    """
    rows=[]
    parameter_layout=[]
    exact_long_handoffs=[]
    queue_builder_callers=[]
    queue_builder_details=[]
    dex_count=0
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("QUEUE_PERIOD_ID_CTOR_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dex_count+=1
                for caller,_flags,off in audit.method_definitions_with_flags(dex):
                    units=dex.u32(off+12)
                    if units>3_000_000:
                        raise ValueError("QUEUE_PERIOD_ID_CTOR_CODE_LIMIT")
                    start=off+16
                    dex.bounds(start,units*2)
                    buf=bytes(dex.data[start:start+units*2])
                    if not any(bytes((b,)) in buf for b in (0x6e,0x6f,0x70,0x71,0x72,0x74,0x75,0x76,0x77,0x78)):
                        continue
                    for pc,op,words in audit.instructions(dex,off):
                        if op not in audit.INVOKES or not (0x6e<=op<=0x78):
                            continue
                        callee=dex.method(words[1])
                        if callee in SIGNED_QUEUE_ID_BUILDERS:
                            invoked=audit.invoke_registers(op,words)
                            static_call=op in (0x71,0x77)
                            expected=(0 if static_call else 1)+sum(
                                2 if arg in ("J","D") else 1
                                for arg in audit.parse_types(callee[2]))
                            if len(invoked)!=expected:
                                raise ValueError("QUEUE_ID_BUILDERS_CALL_ARG_SHAPE")
                            input_js=audit.typed_parameter_registers(dex,caller,_flags,off,"J")
                            idx=0 if static_call else 1
                            j_inputs=[]
                            for typ in audit.parse_types(callee[2]):
                                if typ=="J":
                                    j_inputs.append({
                                        "argument_word_position":idx,
                                        "source_register_is_direct_caller_J_parameter":
                                            invoked[idx] in input_js,
                                        "argument_register":invoked[idx]
                                    })
                                idx+=2 if typ in ("J","D") else 1
                            queue_builder_callers.append((*caller,pc,callee,op))
                            queue_builder_details.append({
                                "caller":list(caller),"pc":pc,
                                "target":list(callee),"invoke_opcode":op,
                                "direct_caller_J_parameter_argument_layout":j_inputs,
                                "preceding_wide_register_definitions_scope":[
                                    {"argument_register":a["argument_register"],
                                     "candidate_instruction_writers":[
                                        shape for shape in (
                                            signed_wide_writer_type_only(dex,p,o,w)
                                            for p,o,w in audit.instructions(dex,off)
                                            if p<pc)
                                        if shape is not None and
                                           shape["dest"] in (
                                               a["argument_register"],
                                               a["argument_register"]-1)
                                     ][:36]}
                                    for a in j_inputs
                                ],
                                "preceding_writers_are_not_cfg_or_selected_epoch_proof":True,
                                "at_callsite_no_proven_audible_period_or_playlist_edition":True
                            })
                            if len(queue_builder_callers)>MAX_SIGNED_QUEUE_ID_BUILDERS_DIRECT_CALLS:
                                raise ValueError("QUEUE_ID_BUILDERS_TOO_MANY_CALLS")
                        if op not in (0x70,0x76) or callee[0]!=PERIOD_ID or callee[1]!="<init>":
                            continue
                        # No register values are exported: signatures/sites only.
                        invoked=audit.invoke_registers(op,words)
                        if len(invoked)<2:
                            raise ValueError("QUEUE_PERIOD_ID_CTOR_INVOKE_SHAPE")
                        rows.append((*caller,pc,callee[2],op))
                        matching=[x for x in SIGNED_ID_LONG_HANDOFF_SITES
                                  if x[:4]==(*caller,pc)]
                        for site in matching:
                            exact_long_handoffs.append(
                                verify_signed_id_long_normal_cfg(
                                    dex,caller,_flags,off,pc,*site[4:]))

                        # Register layout only. No value-flow or semantic selection
                        # inferred from a J register matching an incoming parameter.
                        args=audit.parse_types(callee[2])
                        expected_words=1+sum(2 if arg in ("J","D") else 1 for arg in args)
                        if len(invoked)!=expected_words:
                            raise ValueError("QUEUE_PERIOD_ID_CTOR_ARGUMENT_WORDS")
                        caller_long_regs=audit.typed_parameter_registers(
                            dex,caller,_flags,off,"J")
                        word_index=1
                        wide_arguments=[]
                        for arg in args:
                            if arg=="J":
                                wide_arguments.append({
                                    "argument_word_index":word_index,
                                    "is_direct_caller_wide_parameter_register":
                                         invoked[word_index] in caller_long_regs,
                                })
                            word_index+=2 if arg in ("J","D") else 1
                        if caller[0] in (QUEUE,ENGINE[0],"Landroidx/media3/exoplayer/d;"):
                            parameter_layout.append({
                                "caller":list(caller),
                                "pc":pc,"ctor":callee[2],
                                "wide_J_argument_register_layout_only":wide_arguments,
                                "caller_declares_J_parameter":bool(caller_long_regs),
                                "caller_long_input_registers":sorted(caller_long_regs),
                                "constructor_long_argument_registers":[
                                    invoked[x["argument_word_index"]]
                                    for x in wide_arguments],
                                "wide_definition_opcode_shapes_before_call":[
                                    item for item in (
                                        wide_definition_register_shape(p,o,w)
                                        for p,o,w in audit.instructions(dex,off)
                                        if p<pc)
                                    if item is not None][:100]
                                if caller[0]==QUEUE else [],

                            })
                        if len(rows)>MAX_SIGNED_PERIOD_ID_CTOR_SITES:
                            raise ValueError("QUEUE_PERIOD_ID_CTOR_TOO_MANY_SITES")
    if dex_count!=6:
        raise ValueError("QUEUE_PERIOD_ID_CTOR_EXPECTED_SIX_DEX")
    witness=validate_signed_period_id_ctor_sites(rows,exact_signed=True)
    queue_builder_witness=validate_signed_queue_id_builder_callers(queue_builder_callers,exact_signed=True)
    if len(exact_long_handoffs)!=len(SIGNED_ID_LONG_HANDOFF_SITES):
        raise ValueError("QUEUE_ID_LONG_EXPECTED_HANDOFF_SITES_CHANGED")
    # Callers are DEX methods, not song/album/media instance data. Keep the
    # output bounded; fail if the discovered cohort is too large to inspect.
    if len(rows)>100:
        raise ValueError("QUEUE_PERIOD_ID_CTOR_REPORT_SCOPE")
    return {
        **witness,
        "publisher_dex_scanned":dex_count,
        "signed_queue_id_builder_direct_callers":{
            **queue_builder_witness,
            "typed_argument_layout":queue_builder_details,
        },
        "original_direct_constructor_callers":[
            {"caller":list(caller[:3]),"pc":caller[3],
             "signature":caller[4],"opcode":"INVOKE_DIRECT_RANGE" if caller[5]==0x76 else "INVOKE_DIRECT"}
            for caller in sorted(rows)
        ],
        "constructor_calls_are_not_selected_queue_epoch":True,
        "exact_signed_queue_J_to_period_ID_normal_CFG":exact_long_handoffs,
        "all_four_queue_J_parameters_to_period_ID_proven_on_normal_CFG":
            all(x["original_caller_J_parameter_proven_at_ctor_on_normal_paths"]
                for x in exact_long_handoffs),
        "scoped_Exo_constructor_J_argument_register_layout":parameter_layout,
        "argument_layout_does_not_prove_control_flow_or_epoch":True,
    }

def scan_signed(apks):
    dex_count = 0
    targets = {}
    stream_classes={}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("QUEUE_SIGNED_DEX_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dex_count += 1
                for index in range(dex.class_count):
                    cbase=dex.class_offset+index*32
                    name=dex.descriptor(dex.u32(cbase))
                    if name not in STREAM_CLASS_BOUNDARY:continue
                    if name in stream_classes:raise ValueError("QUEUE_STREAM_CLASS_DUPLICATE")
                    parent_idx=dex.u32(cbase+8)
                    parent=(dex.descriptor(parent_idx) if parent_idx!=0xffffffff else None)
                    stream_classes[name]={"extends":parent,"access_flags":dex.u32(cbase+4)}
                for method, flags, off in audit.method_definitions_with_flags(dex):
                    if method[0] != QUEUE and method != ENGINE and method not in RENDERER_HELPER_METHODS and method[0] != "LR29;" and method not in STREAM_METHOD_BOUNDARY and method not in SIGNED_PERIOD_TOKEN_CTORS and method not in (SIGNED_PERIOD_INFO_REFRESH,SIGNED_PERIOD_INFO_CLONE):
                        continue
                    if method in targets:
                        raise ValueError("QUEUE_TARGET_DUPLICATE")
                    targets[method] = (dex, flags, off)
    if dex_count != 6 or ENGINE not in targets:
        raise ValueError("QUEUE_EXPECTED_EXACT_SIX_DEX_AND_ENGINE")
    h_methods = {key: value for key, value in targets.items() if key[0] == QUEUE and value[2]}
    if not (2 <= len(h_methods) <= MAX_QUEUE_METHODS):
        raise ValueError("QUEUE_METHOD_SCOPE_MISMATCH")
    all_methods = {**h_methods, ENGINE: targets[ENGINE]}
    scoped_fields = set()
    for method, (dex, flags, off) in all_methods.items():
        for pc, op, words in audit.instructions(dex, off):
            field = slot_field(dex, op, words)
            if field is not None:
                scoped_fields.add(field)
    if not (2 <= len(scoped_fields) <= MAX_SLOT_IDS):
        raise ValueError("QUEUE_SLOT_COUNT_MISMATCH")
    # Deterministic opaque aliases: no private DEX field name or value exported.
    slot_ids = {field: "SLOT_" + chr(65 + i) for i, field in enumerate(sorted(scoped_fields))}
    rows = []
    for method, (dex, flags, off) in all_methods.items():
        insns = list(audit.instructions(dex, off))
        events = []
        for pc, op, words in insns:
            field = slot_field(dex, op, words)
            if field is not None:
                events.append({"pc":pc, "slot":slot_ids[field],
                               "action":"READ" if op == 0x54 else "WRITE"})
            elif op in audit.INVOKES and 0x6e <= op <= 0x78:
                callee = dex.method(words[1])
                if (callee[0] in (QUEUE, HOLDER) and
                    (HOLDER in audit.parse_types(callee[2]) or
                     callee[2].split(")",1)[1] == HOLDER)):
                    events.append({"pc":pc, "call":[callee[0],callee[1],callee[2]]})
        if len(events) > MAX_SCOPED_EVENTS:
            raise ValueError("QUEUE_SCOPED_EVENT_LIMIT")
        if not events and method[2] != "()" + HOLDER:
            continue
        rows.append({"method":[method[0], method[1], method[2]],
                     "instruction_count":len(insns),
                     "direct_single_field_getter_slot": direct_getter(insns,dex,slot_ids)
                        if method[2] == "()" + HOLDER else None,
                     "events":events})
        if len(rows) > MAX_ROWS:
            raise ValueError("QUEUE_METHOD_ROW_LIMIT")
    microtraces={}
    interesting_names={"if","while","this","for","final"}
    for method,(dex,flags,off) in all_methods.items():
        if method == ENGINE:
            ranges=((530,605),(965,1010),(1030,1100),(1150,1190),(1220,1270))
        elif method[0] == QUEUE and method[1] in interesting_names:
            ranges=((0,90),)
        else:
            continue
        trace=bounded_register_microtrace(dex,list(audit.instructions(dex,off)),slot_ids,ranges)
        microtraces[method[0]+method[1]+method[2]]=trace
    native_engine_renderer_boundary=renderer_holder_argument_witness(
        targets[ENGINE],slot_ids)
    renderer_stream_contract=inspect_exact_renderer_stream_contract(
        targets,stream_classes)
    renderer_helper_inspection=inspect_exact_renderer_helpers(targets)
    exact_renderer_stream_comparisons=[
        verify_renderer_attached_stream_comparator(method,targets[method])
        for method in sorted(RENDERER_HELPER_METHODS)
    ]
    exact_slot_b=next((f for f,label in slot_ids.items()
                       if label=="SLOT_B"),None)
    if exact_slot_b is None:raise ValueError("QUEUE_SIGNED_SLOT_B_UNRESOLVED")
    direct_slot_b_writers=signed_slot_b_direct_writer_census(apks,exact_slot_b)
    slot_b_local_provenance=verify_signed_slot_b_local_provenance(targets,slot_ids)
    period_token= signed_holder_period_token_census(apks,targets)
    old_period_J_reuse=verify_signed_old_period_id_long_handoff(targets)
    period_id_ctor_sites=signed_period_id_constructor_site_census(apks)
    front_successor=exact_queue_front_successor(
        h_methods[(QUEUE,"if","()Lxh6;")],slot_ids)
    renderer_helper_flow=scoped_front_to_renderer_helper(
        targets[ENGINE],slot_ids)
    return {
        "exact_renderer_stream_contract":renderer_stream_contract,
        "exact_renderer_stream_comparisons":exact_renderer_stream_comparisons,
        "exact_renderer_helper_inspection":renderer_helper_inspection,
        "exact_queue_front_successor":front_successor,
        "exact_signed_slot_b_direct_writer_census":direct_slot_b_writers,
        "exact_signed_slot_b_local_provenance":slot_b_local_provenance,
        "exact_signed_original_period_token_chain":period_token,
        "exact_old_period_id_long_to_new_queue_builder":old_period_J_reuse,
        "signed_original_period_id_constructor_sites":period_id_ctor_sites,
        "scoped_front_to_renderer_helper":renderer_helper_flow,
        "native_engine_renderer_boundary":native_engine_renderer_boundary,
        "bounded_queue_register_microtraces":microtraces,
        "verdict":"NATIVE_QUEUE_SLOT_ROLE_MAP_STATIC_ONLY",
        "verified_six_signed_dex":dex_count,
        "queue_method_count":len(h_methods),
        "queue_holder_slot_count":len(slot_ids),
        "queue_holder_role_rows":rows,
        "slot_aliases_have_no_exported_private_field_names":True,
        "active_renderer_selected_slot_proven":False,
        "same_selected_period_to_decoder_proven":False,
        "replacement_audio_connected":False,
    }

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("QUEUE_EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size != trusted.PINNED_XAPK_BYTES:
        raise ValueError("QUEUE_XAPK_SIZE_MISMATCH")
    if trusted.sha256_file(xapk) != trusted.PINNED_XAPK_SHA256:
        raise ValueError("QUEUE_XAPK_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-h-queue-") as tmp:
        apks = audit.unbundle_candidate(xapk, Path(tmp))
        if len(apks) != 16:
            raise ValueError("QUEUE_SIGNED_SPLIT_COUNT_MISMATCH")
        if audit.verify_split_set(apks).get("verified_issuer_signed_splits") != 16:
            raise ValueError("QUEUE_PUBLISHER_SIGNER_MISMATCH")
        base = []
        for apk in apks:
            meta = trusted.package_metadata(apk)
            if (meta.get("name") != trusted.EXPECTED_PACKAGE or
                meta.get("versionCode") != trusted.EXPECTED_VERSION_CODE):
                raise ValueError("QUEUE_SIGNED_VERSION_MISMATCH")
            if not meta.get("split"):
                base.append(apk)
        if len(base) != 1 or trusted.sha256_file(base[0]) != trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("QUEUE_NAV17_BASE_MISMATCH")
        result = scan_signed(apks)
    return {**result, "original_input_ephemeral":True}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        print(json.dumps(run(args.xapk),sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as err:
        safe=str(err)
        print(json.dumps({"verdict":"QUEUE_SLOT_AUDIT_INCOMPLETE",
            "safe_error_code":safe if re.fullmatch("[A-Z0-9_]{1,80}",safe) else None,
            "active_renderer_selected_slot_proven":False}))
        raise SystemExit(2)
