#!/usr/bin/env python3
"""NAV17 signed original: bounded exact Lxh6/Lup1/Lo96 sample-stream origin map.
Static structural routing only. Does not imply selected current audio.
No private field names/values, IDs, URLs, account data or audio read/export.
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

audit=trusted.audit
HOLDER="Lxh6;"
WRAPPER="Lup1;"
PERIOD="Lo96;"
MEDIAPERIOD="Lwh6;"
STREAM="LR29;"
STREAM_ARRAY="[LR29;"
OWNER_SET=frozenset((HOLDER,WRAPPER,PERIOD))
MAX_DECLARED_METHODS=110
MAX_INSTRUCTIONS_PER_METHOD=720
MAX_EVENTS_PER_METHOD=90
MAX_TOTAL_EVENTS=500

def scope_owner(owner):
    return owner in OWNER_SET

def scope_call(method):
    owner,name,desc=method
    return (owner in (HOLDER,WRAPPER,PERIOD,MEDIAPERIOD,STREAM) or
            STREAM in audit.parse_types(desc) or
            STREAM_ARRAY in audit.parse_types(desc) or
            STREAM in desc.split(")",1)[1] or STREAM_ARRAY in desc.split(")",1)[1])


EXACT_RENDERER_COMPARE_METHODS=frozenset({
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"),
})
HOLDER_CONSTRUCTOR=("Lxh6;","<init>","([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V")
HOLDER_SELECT=("Lxh6;","if","(LRFa;JZ[Z)J")
PERIOD_WRAPPER_SELECT=("Lup1;","case","([Lw24;[Z[LR29;[ZJ)J")
ORIGINAL_PERIOD_SELECT=("Lo96;","case","([Lw24;[Z[LR29;[ZJ)J")
PERIOD_INTERFACE_SELECT=("Lwh6;","case","([Lw24;[Z[LR29;[ZJ)J")
SHARED_FIELD_USE_PCS={
    HOLDER_CONSTRUCTOR:(30,0x5b),
    HOLDER_SELECT:(63,0x54),
    ("LmQ8;","try","(Lxh6;Landroidx/media3/exoplayer/k;)Z"):(4,0x54),
    ("LmQ8;","new","(Lxh6;)Landroidx/media3/exoplayer/k;"):(2,0x54),
}

def verify_exact_shared_stream_field(methods):
    """Opaque complete DEX field-ref equality across verified call chain.
    No field name/index/value exported or logged."""
    field_refs=[]
    for method,(pc,opcode) in SHARED_FIELD_USE_PCS.items():
        if method not in methods or not methods[method][2]:
            raise ValueError("STREAM_SHARED_FIELD_OWNER_BODY_MISSING")
        dex,flags,off=methods[method]
        insns={pc_:(op,words) for pc_,op,words in audit.instructions(dex,off)}
        insn=insns.get(pc)
        if not insn or insn[0]!=opcode:
            raise ValueError("STREAM_SHARED_FIELD_OPCODE_MISMATCH")
        owner,_private_name,typ=audit.field_id(dex,insn[1][1])
        if owner!=HOLDER or typ!=STREAM_ARRAY:
            raise ValueError("STREAM_SHARED_FIELD_TYPE_MISMATCH")
        field_refs.append((owner,_private_name,typ))
    if len(set(field_refs))!=1:
        raise ValueError("STREAM_SHARED_FIELD_REFERENCE_MISMATCH")
    return {"same_exact_holder_stream_array_field_from_all_four_methods":True,
            "holder_allocation_store_pc":30,
            "holder_selection_read_pc":63,
            "renderer_compare_reads_pcs":[4,2],
            "private_field_names_or_values_exported":False}

def limited_stream_selection_bytecode(method,entry):
    """Register topology on 4 exact relevant methods; no constant or field names."""
    dex,flags,off=entry
    insns=list(audit.instructions(dex,off))
    if len(insns)>140:raise ValueError("STREAM_EXACT_SELECTION_METHOD_SIZE_LIMIT")
    rows=[]
    for pc,op,words in insns:
        r={"pc":pc}
        if 0x52<=op<=0x6d:
            owner,_private_name,typ=audit.field_id(dex,words[1])
            if typ not in (STREAM_ARRAY,MEDIAPERIOD,WRAPPER,PERIOD):
                continue
            r.update(action="FIELD_TYPED",owner=owner,type=typ,opcode=op,
                     first_reg=(words[0]>>8)&15,second_reg=(words[0]>>12)&15)
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            m=dex.method(words[1])
            if m not in (PERIOD_INTERFACE_SELECT,PERIOD_WRAPPER_SELECT,ORIGINAL_PERIOD_SELECT):
                continue
            r.update(action="PERIOD_SELECT_CALL",callee=list(m),
                     registers=audit.invoke_registers(op,words))
        elif op in (0x07,0x08,0x09):
            d,source=audit.move_object_registers(op,words)
            r.update(action="MOVE_OBJECT",dest=d,source=source)
        elif op in (0x0a,0x0b,0x0c):
            r.update(action="MOVE_RESULT",dest=words[0]>>8)
        elif op in (0x46,0x4d):
            r.update(action="STREAM_ARRAY_ELEMENT",opcode=op,
                     first_reg=(words[0]>>8)&255)
        elif op in (0x23,0x24,0x25) and dex.descriptor(words[1])==STREAM_ARRAY:
            r.update(action="NEW_STREAM_ARRAY")
        elif op in (0x28,0x29,0x2a) or 0x32<=op<=0x3d:
            r.update(action="BRANCH",opcode=op)
        else:continue
        rows.append(r)
        if len(rows)>100:
            raise ValueError("STREAM_EXACT_SELECTION_BYTECODE_ROW_LIMIT")
    return {"method":list(method),"steps":rows}


def exact_holder_period_receiver_shape(method,entry):
    """Anonymised field/type/register shape, no private names/values."""
    dex,flags,off=entry
    rows=[]
    for pc,op,words in audit.instructions(dex,off):
        if 0x52<=op<=0x6d:
            owner,_name,typ=audit.field_id(dex,words[1])
            if owner==HOLDER or owner==WRAPPER or typ in (HOLDER,WRAPPER,MEDIAPERIOD):
                rows.append({"pc":pc,"kind":"FIELD","op":op,
                            "owner":owner,"type":typ,
                            "first":(words[0]>>8)&15,"second":(words[0]>>12)&15})
        elif 0x6e<=op<=0x78:
            m=dex.method(words[1])
            if m[0] in (HOLDER,WRAPPER,MEDIAPERIOD) or m[1]=="<init>" and m[0]==WRAPPER:
                rows.append({"pc":pc,"kind":"CALL","callee":list(m),
                             "registers":audit.invoke_registers(op,words)})
        if len(rows)>130:
            raise ValueError("STREAM_EXACT_HOLDER_FIELD_SCOPE_EXCEEDED")
    return {"method":list(method),"events":rows}

def verify_exact_holder_wrapper_period_selection(methods):
    """Fail closed: exact Lup1 allocation -> Lxh6 Object storage -> same read
    into period-select interface; exact [LR29 holder field passed to that call.
    The wrapper may adapt streams; DO NOT assert same child stream instance.
    """
    ctor_dex,_,ctor_off=methods[HOLDER_CONSTRUCTOR]
    sel_dex,_,sel_off=methods[HOLDER_SELECT]
    wrap_dex,_,wrap_off=methods[PERIOD_WRAPPER_SELECT]
    orig_dex,_,orig_off=methods[ORIGINAL_PERIOD_SELECT]
    ci={pc:(op,words) for pc,op,words in audit.instructions(ctor_dex,ctor_off)}
    si={pc:(op,words) for pc,op,words in audit.instructions(sel_dex,sel_off)}
    wi={pc:(op,words) for pc,op,words in audit.instructions(wrap_dex,wrap_off)}
    oi={pc:(op,words) for pc,op,words in audit.instructions(orig_dex,orig_off)}
    new_wrappers=[(pc,(words[0]>>8)&255) for pc,(op,words) in ci.items()
                  if op==0x22 and ctor_dex.descriptor(words[1])==WRAPPER]
    if len(new_wrappers)!=1:
        raise ValueError("PERIOD_WRAPPER_UNIQUE_ALLOCATION_REQUIRED")
    alloc_pc,allocated_reg=new_wrappers[0]
    init_op,init_words=ci.get(132,(None,None))
    if init_op not in audit.INVOKES or ctor_dex.method(init_words[1])!=(
        WRAPPER,"<init>","(Lwh6;ZJJ)V"):
        raise ValueError("PERIOD_WRAPPER_INIT_CALL_MISMATCH")
    ctor_regs=audit.invoke_registers(init_op,init_words)
    # Track the unique newly allocated wrapper through local moves, not an
    # incorrect assumption that the constructor register must equal allocation.
    aliases={allocated_reg}
    for step in sorted(p for p in ci if alloc_pc<p<=136):
        op,words=ci[step]
        if step==132 and ctor_regs[0] not in aliases:
            raise ValueError("PERIOD_WRAPPER_ALLOC_TO_CTOR_SAME_OBJECT_MISSING")
        if step==136:
            if ((words[0]>>8)&15) not in aliases:
                raise ValueError("PERIOD_WRAPPER_CTOR_TO_FIELD_STORE_SAME_OBJECT_MISSING")
            break
        if op in (0x07,0x08,0x09):
            dst,src=audit.move_object_registers(op,words)
            aliases.discard(dst)
            if src in aliases:aliases.add(dst)
        elif op==0x1f or op in audit.INVOKES or op==0x00:
            continue
        elif op in (0x28,0x29,0x2a) or 0x32<=op<=0x3d:
            raise ValueError("PERIOD_WRAPPER_ALLOC_TO_STORE_UNMODELED_BRANCH")
        else:
            dst=audit.written_register(op,words)
            if dst is None:
                raise ValueError("PERIOD_WRAPPER_ALLOC_TO_STORE_UNMODELED_OPCODE")
            aliases.discard(dst)
    move_op,move_words=ci.get(135,(None,None))
    store_op,store_words=ci.get(136,(None,None))
    if move_op not in (0x07,0x08,0x09) or store_op!=0x5b:
        raise ValueError("PERIOD_WRAPPER_STORE_SHAPE_MISMATCH")
    move_dest,move_source=audit.move_object_registers(move_op,move_words)
    stored_reg=(store_words[0]>>8)&15
    if move_dest!=stored_reg:
        raise ValueError("PERIOD_WRAPPER_STORE_DESTINATION_MISMATCH")
    stored_owner,stored_private,stored_type=audit.field_id(ctor_dex,store_words[1])
    if stored_owner!=HOLDER or stored_type!="Ljava/lang/Object;":
        raise ValueError("PERIOD_WRAPPER_HOLDER_OBJECT_FIELD_MISMATCH")
    read_op,read_words=si.get(61,(None,None))
    if read_op!=0x54 or audit.field_id(sel_dex,read_words[1])!=(
            stored_owner,stored_private,stored_type):
        raise ValueError("PERIOD_WRAPPER_SELECTION_FIELD_IDENTITY_MISMATCH")
    receiver=(read_words[0]>>8)&15
    call_op,call_words=si.get(73,(None,None))
    if call_op not in audit.INVOKES or sel_dex.method(call_words[1])!=PERIOD_INTERFACE_SELECT:
        raise ValueError("PERIOD_WRAPPER_SELECTION_CALL_MISMATCH")
    regs=audit.invoke_registers(call_op,call_words)
    if regs[0]!=receiver:
        raise ValueError("PERIOD_WRAPPER_SELECTION_RECEIVER_NOT_SAME")
    arr_op,arr_words=si.get(63,(None,None))
    if arr_op!=0x54:
        raise ValueError("PERIOD_WRAPPER_SELECTION_STREAM_READ_MISSING")
    stream_reg=(arr_words[0]>>8)&15
    if regs[3]!=stream_reg:
        raise ValueError("PERIOD_WRAPPER_SELECTION_STREAM_ARRAY_ALIAS_MISMATCH")
    # No local write to either provenance-bearing register after the field reads.
    # cast and invokes are identity-preserving. Overwrites fail closed.
    for pc,(op,words) in si.items():
        if not (61<pc<73):continue
        if op==0x1f:continue  # check-cast preserves object reference
        if op in audit.INVOKES:
            continue
        written=audit.written_register(op,words)
        if written==receiver or (pc>63 and written==stream_reg):
            raise ValueError("PERIOD_WRAPPER_SELECTION_REGISTER_OVERWRITE")
    # Lup1.case allocates a separate child stream array for nested MediaPeriod
    # and can adapt return streams; never falsely claim child/direct identity.
    if 10 not in wi or wi[10][0]!=0x23 or wrap_dex.descriptor(wi[10][1][1])!=STREAM_ARRAY:
        raise ValueError("PERIOD_WRAPPER_CHILD_STREAM_ALLOCATION_MISMATCH")
    child_arr=(wi[10][1][0]>>8)&15
    wop,wwords=wi.get(45,(None,None))
    if wop not in audit.INVOKES or wrap_dex.method(wwords[1])!=PERIOD_INTERFACE_SELECT:
        raise ValueError("PERIOD_WRAPPER_CHILD_SELECT_INVOKE_MISMATCH")
    wregs=audit.invoke_registers(wop,wwords)
    if wregs[3]!=child_arr:
        raise ValueError("PERIOD_WRAPPER_CHILD_STREAM_ARRAY_ALIAS_MISMATCH")
    oop,owords=oi.get(32,(None,None))
    if oop not in audit.INVOKES or orig_dex.method(owords[1])!=PERIOD_INTERFACE_SELECT:
        raise ValueError("EXACT_LO96_CHILD_PERIOD_SELECT_MISSING")
    return {
        "exact_Lup1_object_allocated_and_initialized_in_holder":True,
        "Lup1_stored_and_read_from_same_exact_Lxh6_field":True,
        "Lup1_same_ref_is_period_select_call_receiver":True,
        "holder_owned_stream_array_same_ref_passed_to_period_select":True,
        "Lup1_uses_separate_child_stream_array_for_nested_selection":True,
        "Lo96_delegates_to_native_child_period_select":True,
        "child_stream_equals_renderer_stream_proven":False,
        "live_period_selected_and_audio_consumed_proven":False,
        "private_field_identifier_exported":False,
    }


STREAM_ADAPTER_CTOR=("Lup1$a;","<init>","(Lup1;LR29;)V")
STREAM_ADAPTER_CLASS="Lup1$a;"

def inspect_exact_stream_adapter(methods):
    if STREAM_ADAPTER_CTOR not in methods:
        raise ValueError("STREAM_ADAPTER_EXACT_CTOR_NOT_DEFINED")
    dex,flags,off=methods[STREAM_ADAPTER_CTOR]
    if not off:raise ValueError("STREAM_ADAPTER_EXACT_CTOR_NO_CODE")
    adapter_ops=[]
    for pc,op,words in audit.instructions(dex,off):
        if 0x52<=op<=0x6d:
            owner,_private,typ=audit.field_id(dex,words[1])
            if typ==STREAM:
                adapter_ops.append({"pc":pc,"op":op,"owner":owner,"type":typ})
    child_dex,_,child_off=methods[PERIOD_WRAPPER_SELECT]
    trace=[]
    for pc,op,words in audit.instructions(child_dex,child_off):
        if pc<112 or pc>158:continue
        row={"pc":pc}
        if op in (0x46,0x4d):
            row.update(action="ARRAY_STREAM_SLOT",
                op=op,value=(words[0]>>8)&255,
                array=words[1]&255,index=(words[1]>>8)&255)
        elif op==0x22:
            typ=child_dex.descriptor(words[1])
            if typ!=STREAM_ADAPTER_CLASS:continue
            row.update(action="NEW_ADAPTER",dest=(words[0]>>8)&255)
        elif op in (0x07,0x08,0x09):
            dst,src=audit.move_object_registers(op,words)
            row.update(action="MOVE_OBJECT",dest=dst,source=src)
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            m=child_dex.method(words[1])
            if m[0]!=STREAM_ADAPTER_CLASS:continue
            row.update(action="CALL",callee=list(m),
                       registers=audit.invoke_registers(op,words))
        elif 0x32<=op<=0x3d or op in (0x28,0x29,0x2a):
            row.update(action="BRANCH",op=op)
        else:continue
        trace.append(row)
    if len(trace)>48:
        raise ValueError("STREAM_ADAPTER_FOCUSED_TRACE_LIMIT")
    return {"adapter_constructor_field_ops":adapter_ops,
            "wrapper_case_stream_loop":trace,
            "caller_stream_instance_proven":False}


def scoped_wrapper_loop_register_lifecycle(methods):
    """Exact Lup1.case only. Register topology, never private values."""
    dex,_,off=methods[PERIOD_WRAPPER_SELECT]
    rows=[]
    for pc,op,words in audit.instructions(dex,off):
        if pc<40 or pc>155:continue
        row={"pc":pc,"opcode":op}
        if op in (0x46,0x4d):
            row.update(kind="ARRAY",source_or_dest=(words[0]>>8)&255,
                       array=words[1]&255,index=(words[1]>>8)&255)
        elif op in (0x07,0x08,0x09):
            d,src=audit.move_object_registers(op,words)
            row.update(kind="MOVE_OBJECT",dest=d,source=src)
        elif op in (0x0a,0x0b,0x0c):
            row.update(kind="MOVE_RESULT",dest=words[0]>>8)
        elif op in (0x22,0x23):
            row.update(kind="NEW_OBJECT_OR_ARRAY",type=dex.descriptor(words[1]),
                       dest=words[0]>>8)
        elif op in audit.INVOKES and 0x6e<=op<=0x78:
            m=dex.method(words[1])
            row.update(kind="CALL",callee=list(m) if m[0] in (WRAPPER,MEDIAPERIOD,STREAM_ADAPTER_CLASS)
                       else ["OTHER_CALL","",""],registers=audit.invoke_registers(op,words))
        elif 0x52<=op<=0x6d:
            owner,_private,typ=audit.field_id(dex,words[1])
            row.update(kind="FIELD",owner=owner,type=typ,
                       reg_a=(words[0]>>8)&15,reg_b=(words[0]>>12)&15)
        elif 0x32<=op<=0x3d or op in (0x28,0x29,0x2a):
            row.update(kind="BRANCH")
        elif op in (0x1f,0x21):
            row.update(kind="CHECK_CAST_OR_ARRAY_LENGTH")
        else:
            wrote=audit.written_register(op,words)
            row.update(kind="OTHER",dest=wrote)
        rows.append(row)
        if len(rows)>110:
            raise ValueError("STREAM_WRAPPER_LOOP_EXACT_REGISTER_LIMIT")
    return rows

def verify_exact_native_child_to_holder_stream_adapter(methods):
    """Scoped DEX register + exact field ref contract only.
    Nested period stream -> Lup1$a adapter -> incoming holder stream array.
    Confirms bytecode can do this, NEVER that live renderer equality succeeds.
    """
    wd,wf,wo=methods[PERIOD_WRAPPER_SELECT]
    ad,af,ao=methods[STREAM_ADAPTER_CTOR]
    wi={pc:(op,words) for pc,op,words in audit.instructions(wd,wo)}
    ai={pc:(op,words) for pc,op,words in audit.instructions(ad,ao)}
    def op(pc,expected):
        if pc not in wi or wi[pc][0]!=expected:
            raise ValueError("STREAM_ADAPTER_EXACT_OPCODE_AT_PC_MISMATCH")
        return wi[pc][1]
    # v8 is the incoming stream-array parameter, not an unrelated local array
    p2=wi.get(2)
    if p2 is None or p2[0] not in (0x07,0x08,0x09):
        raise ValueError("STREAM_ADAPTER_CALLER_ARRAY_PARAM_MOVE_MISSING")
    caller_array,source_param=audit.move_object_registers(p2[0],p2[1])
    if caller_array!=8 or source_param!=20:
        raise ValueError("STREAM_ADAPTER_INCOMING_HOLDER_ARRAY_PARAMETER_MISMATCH")
    new_arr=op(10,0x23)
    if wd.descriptor(new_arr[1])!=STREAM_ARRAY or ((new_arr[0]>>8)&15)!=4:
        raise ValueError("STREAM_ADAPTER_NESTED_ARRAY_ALLOCATION_MISMATCH")
    nested_op,nested_words=wi.get(45,(None,None))
    if nested_op not in audit.INVOKES or wd.method(nested_words[1])!=PERIOD_INTERFACE_SELECT:
        raise ValueError("STREAM_ADAPTER_NESTED_SELECT_CALLEE_MISMATCH")
    if audit.invoke_registers(nested_op,nested_words)[3]!=4:
        raise ValueError("STREAM_ADAPTER_NESTED_SELECT_ARRAY_ARGUMENT_MISMATCH")
    child=op(121,0x46)
    if ((child[0]>>8)&255,child[1]&255,(child[1]>>8)&255)!=(2,4,1):
        raise ValueError("STREAM_ADAPTER_CHILD_READ_REGISTER_MISMATCH")
    a130=op(130,0x54)
    a147=op(147,0x54)
    field130=wd_field= audit.field_id(wd,a130[1])
    if field130 != audit.field_id(wd,a147[1]) or field130[0]!=WRAPPER or field130[2]!="[Lup1$a;":
        raise ValueError("STREAM_ADAPTER_EXACT_LUP1_FIELD_MISMATCH")
    if (a130[0]>>8)&15!=5 or (a147[0]>>8)&15!=2:
        raise ValueError("STREAM_ADAPTER_EXACT_ADAPTER_ARRAY_REG_MISMATCH")
    existing=op(132,0x46)
    if ((existing[0]>>8)&255,existing[1]&255,(existing[1]>>8)&255)!=(6,5,1):
        raise ValueError("STREAM_ADAPTER_EXACT_EXISTING_ADAPTER_READ_MISMATCH")
    read_delegate=op(136,0x54)
    adaptor_field=wd.field_id if False else audit.field_id(wd,read_delegate[1])
    if adaptor_field[0]!=STREAM_ADAPTER_CLASS or adaptor_field[2]!=STREAM:
        raise ValueError("STREAM_ADAPTER_CHILD_DELEGATE_FIELD_WRONG_TYPE")
    ctor_field_op,ctor_field_words=ai.get(5,(None,None))
    if ctor_field_op!=0x5b or audit.field_id(ad,ctor_field_words[1])!=adaptor_field:
        raise ValueError("STREAM_ADAPTER_CHILD_DELEGATE_EXACT_FIELD_DIFFERENCE")
    cmp_words=op(138,0x32)
    if {(cmp_words[0]>>8)&15,(cmp_words[0]>>12)&15}!={2,6}:
        raise ValueError("STREAM_ADAPTER_REFERENCE_MATCH_OPERANDS_DIFFER")
    new_adapter=op(140,0x22)
    if wd.descriptor(new_adapter[1])!=STREAM_ADAPTER_CLASS or (new_adapter[0]>>8)!=6:
        raise ValueError("STREAM_ADAPTER_EXACT_ALLOCATION_MISMATCH")
    invoke_op,invoke_words=wi.get(142,(None,None))
    if invoke_op not in audit.INVOKES or wd.method(invoke_words[1])!=STREAM_ADAPTER_CTOR:
        raise ValueError("STREAM_ADAPTER_EXACT_CTOR_CALLEE_MISMATCH")
    if audit.invoke_registers(invoke_op,invoke_words)!=[6,0,2]:
        raise ValueError("STREAM_ADAPTER_CHILD_REG_TO_CTOR_MISMATCH")
    put_adapter=op(145,0x4d)
    if ((put_adapter[0]>>8)&255,put_adapter[1]&255,(put_adapter[1]>>8)&255)!=(6,5,1):
        raise ValueError("STREAM_ADAPTER_INSERT_EXACT_ARRAY_MISMATCH")
    read_stored=op(149,0x46)
    if ((read_stored[0]>>8)&255,read_stored[1]&255,(read_stored[1]>>8)&255)!=(2,2,1):
        raise ValueError("STREAM_ADAPTER_RESULT_FROM_EXACT_STORED_ARRAY_MISMATCH")
    put_output=op(151,0x4d)
    if ((put_output[0]>>8)&255,put_output[1]&255,(put_output[1]>>8)&255)!=(2,8,1):
        raise ValueError("STREAM_ADAPTER_OUTPUT_TO_ORIGINAL_HOLDER_ARRAY_MISMATCH")
    # Check v8 is not overwritten by any instruction after the caller-param move.
    for pc,(opcode,words) in wi.items():
        if pc<=2:continue
        if opcode in audit.INVOKES or opcode==0x1f or opcode in (
            0x4d,0x4e,0x4f,0x50,0x51,0x5b,0x5c,0x5d,0x5e,0x5f,0x6b,0x6c,0x6d):
            continue
        if audit.written_register(opcode,words)==caller_array:
            raise ValueError("STREAM_ADAPTER_CALLER_ARRAY_REGISTER_OVERWRITTEN")
    return {
        "child_stream_array_allocated_and_passed_to_nested_MediaPeriod":True,
        "child_sample_stream_array_element_loaded_for_adapter":True,
        "adapter_child_stream_identity_compared_with_existing_delegate":True,
        "new_adapter_stores_exact_child_stream_typed_field":True,
        "same_adapter_array_field_read_after_store":True,
        "selected_adapter_written_into_original_holder_stream_array":True,
        "no_direct_child_stream_identity_equivalence_claim":True,
        "active_sound_or_decoder_consumption_observed":False,
        "private_field_values_or_names_exported":False,
    }


def strict_scoped_alias_transition(dex,op,words,aliases):
    """Dalvik alias state: exact bounded stream adapter construction CFG.
    Writes and unknown instructions fail closed; no string/value inspection."""
    next_alias=set(aliases)
    if op in (0x07,0x08,0x09):
        dst,src=audit.move_object_registers(op,words)
        next_alias.discard(dst)
        if src in aliases:next_alias.add(dst)
        return frozenset(next_alias)
    if op==0x1f or op in audit.INVOKES or op in (0x00,0x0e,0x27,0x28,0x29,0x2a):
        return frozenset(next_alias)
    if 0x32<=op<=0x3d:
        return frozenset(next_alias)
    if op in (0x4d,0x4e,0x4f,0x50,0x51) or 0x59<=op<=0x5f or 0x66<=op<=0x6d:
        return frozenset(next_alias)  # stores do not overwrite registers
    dest=audit.written_register(op,words)
    if dest is None:
        raise ValueError("STREAM_ADAPTER_CFG_OPCODE_UNMODELED")
    next_alias.discard(dest)
    return frozenset(next_alias)

def verify_adapter_child_parameter_identity(methods):
    """The exact child sample v2 survives on ALL CFG states reaching adapter
    constructor; its LR29 argument is stored unchanged on adapter.this."""
    dex,flags,off=methods[PERIOD_WRAPPER_SELECT]
    ci=audit.build_dex_control_flow(dex,off)
    by_pc=ci["by_pc"]
    succ=ci["successors"]
    start=121
    if by_pc.get(start,None) is None or by_pc[start][0]!=0x46:
        raise ValueError("STREAM_ADAPTER_CHILD_READ_PIVOT_MISSING")
    work=[(n,frozenset((2,))) for n in succ.get(start,()) if start<n<=142]
    seen=set()
    total=matched=0
    while work:
        pc,aliases=work.pop()
        if (pc,aliases) in seen:continue
        seen.add((pc,aliases))
        if len(seen)>300:
            raise ValueError("STREAM_ADAPTER_BRANCH_STATE_LIMIT")
        if pc==142:
            total+=1
            op,words=by_pc[pc]
            if op not in audit.INVOKES or dex.method(words[1])!=STREAM_ADAPTER_CTOR:
                raise ValueError("STREAM_ADAPTER_EXACT_CFG_TARGET_CHANGED")
            regs=audit.invoke_registers(op,words)
            if regs[2] in aliases:matched+=1
            continue
        if pc<=start or pc>142:continue
        op,words=by_pc[pc]
        next_alias=strict_scoped_alias_transition(dex,op,words,aliases)
        for nxt in succ.get(pc,()):
            if start<nxt<=142:
                work.append((nxt,next_alias))
    if not total or total!=matched:
        raise ValueError("STREAM_ADAPTER_CHILD_ALIAS_NOT_ON_ALL_CTOR_PATHS")
    ad,flags,off=methods[STREAM_ADAPTER_CTOR]
    registers_size=ad.u16(off)
    ins_size=ad.u16(off+2)
    if ins_size!=3 or registers_size<ins_size:
        raise ValueError("STREAM_ADAPTER_CONSTRUCTOR_INCOMING_REGISTERS_MISMATCH")
    child_param=registers_size-1
    ctor_code={pc:(op,words) for pc,op,words in audit.instructions(ad,off)}
    if 5 not in ctor_code or ctor_code[5][0]!=0x5b:
        raise ValueError("STREAM_ADAPTER_CHILD_FIELD_STORE_MISSING")
    child_store_reg=(ctor_code[5][1][0]>>8)&15
    aliases=frozenset((child_param,))
    for pc in sorted(ctor_code):
        if pc>=5:break
        op,words=ctor_code[pc]
        aliases=strict_scoped_alias_transition(ad,op,words,aliases)
    if child_store_reg not in aliases:
        raise ValueError("STREAM_ADAPTER_CHILD_PARAM_NOT_STORED_EXACT")
    return {"child_same_reference_on_all_scoped_ctor_reaching_states":True,
            "scoped_reaching_state_count":total,
            "constructor_stores_exact_incoming_LR29_argument":True,
            "field_name_or_runtime_child_value_exported":False}
def scan(apks):
    dexes=0
    methods={}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex",entry.filename):
                    continue
                if entry.file_size>audit.DEX_MAX:
                    raise ValueError("STREAM_ORIGIN_SIGNED_DEX_LIMIT")
                dex=audit.Dex(archive.read(entry.filename))
                dexes+=1
                for method,flags,off in audit.method_definitions_with_flags(dex):
                    if not (scope_owner(method[0]) or method in EXACT_RENDERER_COMPARE_METHODS or method==STREAM_ADAPTER_CTOR):continue
                    if method in methods:raise ValueError("STREAM_ORIGIN_DUPLICATE_METHOD")
                    methods[method]=(dex,flags,off)
                    if len(methods)>MAX_DECLARED_METHODS:
                        raise ValueError("STREAM_ORIGIN_METHOD_COUNT_LIMIT")
    if dexes!=6 or not all(any(m[0]==owner for m in methods) for owner in OWNER_SET):
        raise ValueError("STREAM_ORIGIN_EXACT_SIGNED_CLASS_MISSING")
    rows=[]
    total_events=0
    for method,(dex,flags,off) in sorted(methods.items()):
        if not off or not scope_owner(method[0]):continue
        insns=list(audit.instructions(dex,off))
        if len(insns)>MAX_INSTRUCTIONS_PER_METHOD:
            raise ValueError("STREAM_ORIGIN_METHOD_SIZE_LIMIT")
        events=[]
        for pc,op,words in insns:
            if 0x52<=op<=0x6d:
                owner,_private,typ=audit.field_id(dex,words[1])
                if typ in (STREAM,STREAM_ARRAY,MEDIAPERIOD,WRAPPER,PERIOD) and owner in OWNER_SET:
                    events.append({"pc":pc,"action":"FIELD_READ" if op<=0x58 else "FIELD_WRITE",
                                   "opcode":op,"owner":owner,"type":typ})
            elif op in audit.INVOKES and 0x6e<=op<=0x78:
                called=dex.method(words[1])
                if scope_call(called):
                    events.append({"pc":pc,"action":"CALL","owner":called[0],"name":called[1],
                                   "signature":called[2]})
            elif op in (0x23,0x24,0x25):
                type_=dex.descriptor(words[1])
                if type_==STREAM_ARRAY:
                    events.append({"pc":pc,"action":"NEW_TYPED_STREAM_ARRAY","type":type_})
            elif op in (0x46,0x4d):
                events.append({"pc":pc,"action":"STREAM_ARRAY_READ_OR_WRITE_CANDIDATE",
                               "opcode":op})
            if len(events)>MAX_EVENTS_PER_METHOD:
                raise ValueError("STREAM_ORIGIN_METHOD_EVENT_LIMIT")
        total_events+=len(events)
        if total_events>MAX_TOTAL_EVENTS:
            raise ValueError("STREAM_ORIGIN_TOTAL_EVENT_LIMIT")
        if events or (method[0]==HOLDER and method[1]=="<init>"):
            rows.append({"method":list(method),"instruction_count":len(insns),
                         "events":events})
    holder_period_receiver_shapes=[
        exact_holder_period_receiver_shape(method,methods[method])
        for method in (HOLDER_CONSTRUCTOR,HOLDER_SELECT,PERIOD_WRAPPER_SELECT)
    ]
    stream_adapter=inspect_exact_stream_adapter(methods)
    exact_stream_bridge=verify_exact_native_child_to_holder_stream_adapter(methods)
    child_param_proof=verify_adapter_child_parameter_identity(methods)
    wrapper_loop=scoped_wrapper_loop_register_lifecycle(methods)
    shared_field=verify_exact_shared_stream_field(methods)
    period_wrapper_selection=verify_exact_holder_wrapper_period_selection(methods)
    selected=[]
    for method in (HOLDER_CONSTRUCTOR,HOLDER_SELECT,PERIOD_WRAPPER_SELECT,ORIGINAL_PERIOD_SELECT):
        selected.append(limited_stream_selection_bytecode(method,methods[method]))
    return {"child_stream_exact_constructor_parameter_proof":child_param_proof,
            "exact_nested_media_period_to_holder_stream_bridge":exact_stream_bridge,
            "scoped_wrapper_loop_register_lifecycle":wrapper_loop,
            "scoped_child_to_wrapper_stream_adapter":stream_adapter,
            "exact_holder_period_selection_identity":period_wrapper_selection,
            "exact_holder_period_receiver_shapes":holder_period_receiver_shapes,
            "exact_shared_holder_stream_field":shared_field,
            "exact_stream_selection_register_topology":selected,
            "verdict":"SIGNED_EXACT_HOLDER_STREAM_OWNER_STRUCTURAL_MAP",
            "six_signed_dex_verified":dexes,
            "class_method_count":{owner:sum(m[0]==owner for m in methods) for owner in sorted(OWNER_SET)},
            "scoped_methods_with_stream_or_period_uses":rows,
            "static_map_only_no_live_selection":True,
            "active_period_stream_to_decoder_proven":False,
            "replacement_audio_connected":False,
            "private_field_names_values_media_ids_urls_or_audio_exported":False}

def run(xapk):
    if os.environ.get("GITHUB_ACTIONS")!="true":
        raise RuntimeError("STREAM_ORIGIN_EPHEMERAL_CI_ONLY")
    if not xapk.is_file() or xapk.stat().st_size!=trusted.PINNED_XAPK_BYTES:
        raise ValueError("STREAM_ORIGIN_PINNED_SIZE_MISMATCH")
    if trusted.sha256_file(xapk)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("STREAM_ORIGIN_PINNED_SHA_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="celikom-stream-origin-") as tmp:
        apks=audit.unbundle_candidate(xapk,Path(tmp))
        if len(apks)!=16:
            raise ValueError("STREAM_ORIGIN_SIGNED_SPLITS_REQUIRED")
        sig=audit.verify_split_set(apks)
        if sig.get("verified_issuer_signed_splits")!=16:
            raise ValueError("STREAM_ORIGIN_PUBLISHER_SIGNER_MISMATCH")
        base=[]
        for apk in apks:
            meta=trusted.package_metadata(apk)
            if meta.get("name")!=trusted.EXPECTED_PACKAGE or meta.get("versionCode")!=trusted.EXPECTED_VERSION_CODE:
                raise ValueError("STREAM_ORIGIN_ORIGINAL_VERSION_MISMATCH")
            if not meta.get("split"):base.append(apk)
        if len(base)!=1 or trusted.sha256_file(base[0])!=trusted.PINNED_BASE_APK_SHA256:
            raise ValueError("STREAM_ORIGIN_NAV17_BASE_MISMATCH")
        result=scan(apks)
    return {**result,"signed_original_ephemeral_only":True}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(run(args.xapk),sort_keys=True))
    except (RuntimeError,ValueError,audit.DexError,OSError,zipfile.BadZipFile) as err:
        msg=str(err)
        print(json.dumps({"verdict":"STREAM_ORIGIN_INCOMPLETE",
            "safe_error_code":msg if re.fullmatch(r"[A-Z0-9_]{1,90}",msg) else None,
            "active_period_stream_to_decoder_proven":False}))
        raise SystemExit(2)
