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

def scan_signed(apks):
    dex_count = 0
    targets = {}
    for apk in apks:
        with zipfile.ZipFile(apk) as archive:
            for entry in archive.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                if entry.file_size > audit.DEX_MAX:
                    raise ValueError("QUEUE_SIGNED_DEX_LIMIT")
                dex = audit.Dex(archive.read(entry.filename))
                dex_count += 1
                for method, flags, off in audit.method_definitions_with_flags(dex):
                    if method[0] != QUEUE and method != ENGINE:
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
    return {
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
