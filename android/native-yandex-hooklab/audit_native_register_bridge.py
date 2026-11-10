#!/usr/bin/env python3
"""Publisher-pinned, read-only DEX REGISTER audit around exact FileInfo callers.

Unlike call-graph adjacency this tracks a converter invoke's move-result-object
and bounded same-basic-block uses of that *register*. It never claims that the
result is a current-track decoder source. No APK/DEX, URLs or strings exported.
"""
from __future__ import annotations

from collections import defaultdict
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools" / "android-native-gate1"))
from inspect_android_host import Dex, DexError, DEX_MAX
from trace_native_callers import OP_WIDTH, INVOKES, method_definitions, payload_width
from trace_native_source_hops import inspect_one_dex
from trace_native_model_to_decoder import bounded_obfuscated
import clone_native_splits_ephemeral as exact

SEED_OWNERS = {"Lhee;", "Lged;"}
SOURCE_OWNER = "Lsw7;"
MODEL_OWNER = "Leed;"
MAX_BODY_INSTRUCTIONS = 30000
MAX_NEIGHBORS = 80
MAX_EVENTS = 16
BRANCHES = set(range(0x27, 0x2d)) | set(range(0x32, 0x3e))
EXITS = {0x0e, 0x0f, 0x10, 0x11, 0x27}


def instructions(dex, code_off):
    """DEX code-unit iterator; fail closed on malformed and unknown opcodes."""
    dex.bounds(code_off, 16)
    count = dex.u32(code_off + 12)
    if count > 3_000_000:
        raise DexError("METHOD_CODE_LIMIT")
    start = code_off + 16
    dex.bounds(start, count * 2)
    pc, seen = 0, 0
    while pc < count:
        w = dex.u16(start + pc * 2)
        op = w & 255
        width = (payload_width(dex, start, count, pc, w >> 8)
                 if op == 0 else OP_WIDTH.get(op))
        if width is None or pc + width > count:
            raise DexError("UNSUPPORTED_OR_TRUNCATED_OPCODE")
        words = tuple(dex.u16(start + (pc + j) * 2) for j in range(width))
        yield pc, op, words
        pc += width
        seen += 1
        if seen > MAX_BODY_INSTRUCTIONS:
            raise DexError("METHOD_INSTRUCTION_LIMIT")


def invoke_registers(op, words):
    """DEX 35c/3rc/45cc/4rcc invoke argument register decoding."""
    if 0x6e <= op <= 0x72 or op in (0xfa, 0xfc):
        # 35c (and 45cc): A=argument words, G=fifth argument register.
        count = (words[0] >> 12) & 15
        if count > 5:
            raise DexError("INVALID_35C_ARG_COUNT")
        packed = words[2]
        regs = [(packed >> (4 * n)) & 15 for n in range(min(count, 4))]
        if count == 5:
            regs.append((words[0] >> 8) & 15)
        return regs
    if 0x74 <= op <= 0x78 or op in (0xfb, 0xfd):
        count = words[0] >> 8
        if count > 255:
            raise DexError("INVALID_3RC_ARG_COUNT")
        return list(range(words[2], words[2] + count))
    return []


def move_object_registers(op, words):
    if op == 0x07:                 # move-object vA, vB (12x)
        return (words[0] >> 8) & 15, (words[0] >> 12) & 15
    if op == 0x08:                 # move-object/from16 (22x)
        return (words[0] >> 8), words[1]
    if op == 0x09:                 # move-object/16 (32x)
        return words[1], words[2]
    return None


def describe_callee(triple):
    return {
        "hint": bounded_obfuscated(triple),
        "model_or_converter": (triple[0] in (MODEL_OWNER, SOURCE_OWNER)
                               or MODEL_OWNER in triple[2]),
        "continuation_signature": "Lkotlin/coroutines/Continuation;" in triple[2],
        "media3_or_framework": (
            triple[0].startswith("Landroidx/media3/")
            or triple[0].startswith("Landroid/media/")),
    }


def register_witnesses(dex, code_off):
    """Only straight-line, bounded value uses after exact converter invoke.

    A branch ends the candidate path. Other opcodes are deliberately NOT given
    full SSA semantics; findings are LOCAL CANDIDATES, not interprocedural proof.
    """
    ins = list(instructions(dex, code_off))
    converter_calls = 0
    with_move_result = 0
    candidates = []
    interface_calls = 0
    continuation_calls = 0
    for i, (pc, op, w) in enumerate(ins):
        if op in (0x72, 0x78):
            interface_calls += 1
        if op not in INVOKES:
            continue
        callee = dex.method(w[1])
        if "Lkotlin/coroutines/Continuation;" in callee[2] or callee[1] in ("invokeSuspend", "resumeWith"):
            continuation_calls += 1
        if callee[0] != SOURCE_OWNER or callee[1] not in ("y0", "z0"):
            continue
        converter_calls += 1
        if i + 1 >= len(ins) or ins[i+1][1] != 0x0c:
            continue
        with_move_result += 1
        seed = ins[i+1][2][0] >> 8
        taint = {seed}
        for _pc, next_op, words in ins[i+2:i+66]:
            if next_op in BRANCHES or next_op in EXITS:
                if next_op == 0x11 and (words[0] >> 8) in taint:
                    candidates.append({"kind": "return_object", "target": None})
                break
            move = move_object_registers(next_op, words)
            if move:
                target, origin = move
                taint.discard(target)
                if origin in taint:
                    taint.add(target)
                continue
            if next_op in INVOKES:
                regs = invoke_registers(next_op, words)
                if taint.intersection(regs):
                    target_method = dex.method(words[1])
                    candidates.append({
                        "kind": ("invoke_interface" if next_op in (0x72,0x78)
                                 else "invoke_other"),
                        "target": describe_callee(target_method),
                    })
            if next_op in (0x5b, 0x69):  # iput-object, sput-object
                source_reg = ((words[0] >> 8) & 15) if next_op == 0x5b else (words[0] >> 8)
                if source_reg in taint:
                    candidates.append({"kind": "object_field_store", "target": None})
            # Kill when a known result/constant overwrites a register.
            if next_op in (0x0c, 0x0a, 0x0b, 0x12, 0x13, 0x14,
                           0x15, 0x16, 0x17, 0x18, 0x19, 0x1a,
                           0x1b, 0x1c, 0x22, 0x62, 0x63, 0x64):
                taint.discard(words[0] >> 8)
        if len(candidates) > MAX_EVENTS:
            candidates = candidates[:MAX_EVENTS]
    return {
        "converter_invoke_sites": converter_calls,
        "converter_sites_with_object_result": with_move_result,
        "bounded_result_use_candidates": candidates[:MAX_EVENTS],
        "interface_invoke_sites": interface_calls,
        "continuation_related_invoke_sites": continuation_calls,
        "local_register_witness_is_decoder_proof": False,
    }



def opcode_role(op):
    """Privacy-safe DEX instruction family, never instruction bytes or values."""
    if op in INVOKES:
        return "invoke_interface" if op in (0x72,0x78) else "invoke"
    if op == 0x0c:
        return "move_result_object"
    if op == 0x0b:
        return "move_result_wide"
    if op == 0x0a:
        return "move_result"
    if op in (0x07,0x08,0x09):
        return "move_object"
    if op == 0x11:
        return "return_object"
    if op in BRANCHES:
        return "branch"
    if op in (0x5b,0x69):
        return "object_field_store"
    if op == 0x1f:
        return "check_cast"
    if op in (0x52,0x53,0x54,0x55,0x56,0x57,0x58):
        return "field_get"
    if op in (0x62,0x63,0x64,0x65,0x66,0x67,0x68):
        return "static_get"
    if op in (0x0e,0x0f,0x10):
        return "return"
    return "other"


def coroutine_callsite_witness(dex, code_off):
    """Bounded direct seed/DTO callsites and interface destination hints.

    Coroutine invokeSuspend and reflective/dynamic calls are NOT call-value
    proof. Report only structural categories and short symbols.
    """
    ins = list(instructions(dex, code_off))
    direct_seeds = []
    interface_targets = set()
    model_calls = set()
    for i, (_pc, op, w) in enumerate(ins):
        if op not in INVOKES:
            continue
        callee = dex.method(w[1])
        if op in (0x72,0x78):
            interface_targets.add(bounded_obfuscated(callee))
        if callee[0] == MODEL_OWNER:
            model_calls.add(bounded_obfuscated(callee))
        if callee[0] not in SEED_OWNERS or callee[1] != "a":
            continue
        after = [opcode_role(near_op) for _,near_op,_ in ins[i+1:i+6]]
        sig = callee[2]
        ret = sig.split(")",1)[-1]
        direct_seeds.append({
            "target": bounded_obfuscated(callee),
            "object_return_signature": ret.startswith("L") or ret.startswith("["),
            "returns_exact_eed": ret == MODEL_OWNER,
            "has_continuation_parameter": "Lkotlin/coroutines/Continuation;" in sig,
            "following_opcode_roles": after,
            "direct_argument_word_count": len(invoke_registers(op,w)),
            "dynamic_decoder_or_current_track_proven": False,
        })
    return {
        "direct_Lhee_or_Lged_invokes": direct_seeds[:MAX_EVENTS],
        "interface_dispatch_target_hints": sorted(interface_targets)[:MAX_EVENTS],
        "interface_distinct_count": len(interface_targets),
        "exact_eed_method_target_hints": sorted(model_calls)[:MAX_EVENTS],
        "coroutine_return_or_decoder_bound": False,
    }


def summarize_graph(scans):
    reverse = defaultdict(set)
    sources = set()
    models = set()
    for x in scans:
        if not x["complete"]:
            raise ValueError("INCOMPLETE_DEX")
        sources.update(x["_source_methods"]["converter_caller"])
        models.update(x["_source_methods"]["model_consumer"])
        for callee, callers in x["_reverse_edges"].items():
            reverse[callee].update(callers)
    seeds = {m for m in sources | models if m[0] in SEED_OWNERS}
    if not any(x[0] == "Lhee;" and x[1] == "a" for x in seeds):
        raise ValueError("EXACT_CONVERTER_CALLER_MISSING")
    neighbors = set(seeds)
    for s in seeds:
        neighbors.update(reverse.get(s, ()))
    # No enormous unrelated orchestration or misleading long-distance hops.
    if len(neighbors) > MAX_NEIGHBORS:
        neighbors = seeds | set(sorted(neighbors - seeds)[:MAX_NEIGHBORS-len(seeds)])
    return reverse, sources, models, neighbors


def scan_signed(apks):
    scans = []
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for entry in z.infolist():
                if re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    if entry.file_size > DEX_MAX:
                        raise ValueError("DEX_TOO_LARGE")
                    scans.append(inspect_one_dex(z.read(entry)))
    if len(scans) != 6:
        raise ValueError("PINNED_SIX_DEX_REQUIRED")
    reverse, sources, models, neighbors = summarize_graph(scans)
    matches = []
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for entry in z.infolist():
                if not re.fullmatch(r"classes[0-9]*\.dex", entry.filename):
                    continue
                d = Dex(z.read(entry))
                for method_id, code_off in method_definitions(d):
                    method = d.method(method_id)
                    if method not in neighbors:
                        continue
                    match = {
                        "method": bounded_obfuscated(method),
                        "is_seed": method in sources or method in models,
                        "model_in_signature": MODEL_OWNER in method[2],
                        "coroutine_signature": "Lkotlin/coroutines/Continuation;" in method[2],
                        "direct_callers_count": len(reverse.get(method, ())),
                        "local_register_trace": register_witnesses(d, code_off),
                        "coroutine_callsite_trace": coroutine_callsite_witness(d, code_off),
                    }
                    matches.append(match)
    chosen = [x for x in matches if x["method"] in ("Lhee;->a", "Lged;->a")]
    if not chosen:
        raise ValueError("NO_EXACT_SEED_BODY")
    return {
        "exact_converter_callers": len(sources),
        "model_consumer_methods": len(models),
        "chosen_seed_bodies": chosen[:12],
        "adjacent_method_bodies_analyzed": len(matches),
        "neighbor_bodies_with_interface_invokes": sum(
            bool(x["local_register_trace"]["interface_invoke_sites"]) for x in matches),
        "neighbor_bodies_with_continuation_invokes": sum(
            bool(x["local_register_trace"]["continuation_related_invoke_sites"]) for x in matches),
        "direct_seed_callers_bounded": [x for x in matches
            if x["method"] not in ("Lhee;->a", "Lged;->a")][:12],
        "current_track_exact_identity_proven": False,
        "decoder_preprepare_input_proven": False,
    }


def run():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("SIGNED_RESEARCH_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-exact-register-audit-") as tmp:
        root = Path(tmp)
        archive = root / "publisher-unchanged.xapk"
        size, sha = exact.gpr.download(archive)
        if size != 60433885 or sha != exact.ARCHIVE_SHA:
            raise ValueError("SIGNED_PUBLISHER_HASH_MISMATCH")
        apks = exact.gpr.split_apks(archive, root)
        if len(apks) != 5:
            raise ValueError("FIVE_SPLITS_REQUIRED")
        exact.gpr.inspect_publisher(apks)
        evidence = scan_signed(apks)
    return {
        "verdict": "SIGNED_NATIVE_REGISTER_WITNESS_ONLY_NO_SOURCE_PROOF",
        "publisher_original": "Yandex 2026.10.3 #170gpr",
        "original_splits": 5, "dex_count": 6,
        **evidence,
        "limits": ("Straight-line, at most 64 instructions after converter result; "
                   "no branch CFG, heap aliases, dynamic dispatch or coroutine "
                   "resume dataflow. No current playback, track edition or generation."),
        "apk_modified_or_exported": False,
        "account_or_media_access": False,
        "audio_replacement_claim": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except (ValueError, RuntimeError, DexError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({
            "verdict": "SIGNED_REGISTER_AUDIT_INCOMPLETE",
            "error_class_only": type(exc).__name__,
            "audio_replacement_claim": False,
        }))
        sys.exit(2)
