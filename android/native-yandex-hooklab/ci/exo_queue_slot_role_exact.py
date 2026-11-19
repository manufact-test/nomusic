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
                    if method[0] != QUEUE and method != ENGINE and method not in RENDERER_HELPER_METHODS and method[0] != "LR29;" and method not in STREAM_METHOD_BOUNDARY:
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
