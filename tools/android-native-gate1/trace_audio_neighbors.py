#!/usr/bin/env python3
"""Read-only DEX callgraph around confirmed PlayAudioApi -> qdw.a boundary.

Only public bytecode type/method signatures, opcode and order. No user data,
network requests, token/string literals, response bodies or proprietary binaries
are stored or printed. A static graph is not proof of execution.
"""
from __future__ import annotations
from inspect_android_host import Dex, DexError
from trace_native_callers import method_definitions, invoked_method_indexes

CALLER_CLASS = "Lqdw;"
UPSTREAM_CLASS = "Lsy5;"
API_CLASS = "Lcom/yandex/music/shared/play/audio2/data/PlayAudioApi;"
MAX_EDGES = 90

def inspect_neighbors(data: bytes) -> dict:
    d = Dex(data)
    candidates = set()
    for i in range(d.method_count):
        cls, name, sig = d.method(i)
        if (cls == CALLER_CLASS and name == "a") or (cls == UPSTREAM_CLASS and name == "invokeSuspend") or cls == API_CLASS:
            candidates.add(i)
    inbound = []
    body = []
    errors = []
    scanned = 0
    for idx, code in method_definitions(d):
        c, method, signature = d.method(idx)
        own_target = (c == CALLER_CLASS and method == "a") or (c == UPSTREAM_CLASS and method == "invokeSuspend")
        refs = []
        try:
            for tgt, pc, op in invoked_method_indexes(d, code):
                dst = d.method(tgt)
                if own_target and len(refs) < 110:
                    refs.append({
                        "pc": pc, "invoke": f"{op:#04x}",
                        "class": dst[0], "method": dst[1], "signature": dst[2]})
                if tgt in candidates and len(inbound) < MAX_EDGES:
                    inbound.append({
                        "source_class": c, "source_method": method,
                        "source_signature": signature, "target_class": dst[0],
                        "target_method": dst[1], "target_signature": dst[2],
                        "code_unit_offset": pc
                    })
            if own_target and len(body) < 15:
                body.append({"class": c, "method": method, "signature": signature,
                             "invoked_methods": refs})
        except DexError as exc:
            if len(errors) < 12:
                errors.append({"caller_class": c, "reason": str(exc)})
        scanned += 1
    return {
        "target_class": CALLER_CLASS, "api_class": API_CLASS,
        "method_id_candidates": len(candidates),
        "defined_methods_examined": scanned,
        "qdw_a_bodies": body,
        "inbound_callsite_count_sampled": len(inbound),
        "bounded_inbound_calls": inbound,
        "errors": errors,
        "verdict": "STATIC_NOT_RUNTIME_PLAYER_SOURCE_PROOF"
    }
