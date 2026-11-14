#!/usr/bin/env python3
"""Read-only inventory of exact 2025.10.4 onboarding preference callsites.

Runs only in ephemeral private CI against the pinned issuer XAPK. It emits
method identifiers and Android preference API names only; never emits DEX,
strings other than the already-known preference key, file paths, tokens,
account data, credentials or user information.
"""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import struct
import zipfile

from a1_private_postlogin_contract import source_from_xapk
from a1_private_push_dex_method import Dex
from a1_private_dex_flow import decode_instructions, INVOKE_METHOD, FlowDecodeError

ORIGINAL_CLASSES = 6
EDITOR_CALLS = {"putBoolean", "putString", "putInt", "putLong", "remove", "clear", "apply", "commit"}
READ_CALLS = {"getBoolean", "getString", "getInt", "getLong", "contains"}
KEY_WRITERS = {"putBoolean", "setValue", "putString", "putInt", "putLong"}


def _refs(dex, code, instructions=None):
    strings = set()
    calls = set()
    instructions = instructions if instructions is not None else decode_instructions(code)
    for pc, opcode, _ in instructions:
        if opcode == 0x1a:
            strings.add(dex.string(struct.unpack_from("<H", code, pc + 2)[0]))
        elif opcode == 0x1b:
            strings.add(dex.string(struct.unpack_from("<I", code, pc + 2)[0]))
        elif opcode in INVOKE_METHOD:
            calls.add(dex.method(struct.unpack_from("<H", code, pc + 2)[0]))
    return strings, calls


def classify_calls(calls):
    names = sorted({name for _, name in calls if name in EDITOR_CALLS | READ_CALLS})
    writes = sorted({name for _, name in calls if name in KEY_WRITERS})
    reads = sorted({name for _, name in calls if name in READ_CALLS})
    return {"preference_calls": names, "write_candidates": writes, "read_calls": reads}


def _invoke_registers(code, pc, opcode):
    """Return DEX invoke argument registers; unsupported polymorphic forms fail closed."""
    if opcode in (0xfa, 0xfb):
        return None
    if 0x74 <= opcode <= 0x78:  # 3rc range form
        count = code[pc + 1]
        start = struct.unpack_from("<H", code, pc + 4)[0]
        if count > 32 or start + count > 0xffff:
            return None
        return list(range(start, start + count))
    if 0x6e <= opcode <= 0x72:  # 35c form
        count = code[pc + 1] >> 4
        raw = code[pc + 4:pc + 6]
        registers = [raw[0] & 0x0f, raw[0] >> 4,
                     raw[1] & 0x0f, raw[1] >> 4,
                     code[pc + 1] & 0x0f]
        return registers[:count]
    return None


def _writes_register(opcode, code, pc, register):
    """Conservative destination-register check for the small backward string slice."""
    dest = None
    if opcode in (0x01, 0x04, 0x07):
        dest = code[pc + 1] & 0x0f
    elif opcode in (0x02, 0x05, 0x08):
        dest = code[pc + 1]
    elif opcode in (0x03, 0x06, 0x09):
        dest = struct.unpack_from("<H", code, pc + 2)[0]
    elif opcode in range(0x0a, 0x0e):
        dest = code[pc + 1]
    elif opcode == 0x12:
        dest = code[pc + 1] & 0x0f
    elif opcode in (0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19,
                    0x1a, 0x1b, 0x1c, 0x20, 0x21, 0x22, 0x23,
                    0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66):
        dest = code[pc + 1]
    elif opcode == 0x1f:  # check-cast rewrites the same reference register
        dest = code[pc + 1]
    elif 0x2d <= opcode <= 0x31:
        dest = code[pc + 1]
    elif 0x44 <= opcode <= 0x5f:
        dest = code[pc + 1] & 0x0f
    elif 0x90 <= opcode <= 0xaf or 0xd0 <= opcode <= 0xe2:
        dest = code[pc + 1] & 0x0f
    return dest == register


def _literal_argument(dex, code, instructions, call_index, register):
    """Resolve only a nearby direct const-string; aliases/complex flows stay unknown."""
    for prior_index in range(call_index - 1, max(-1, call_index - 6), -1):
        pc, opcode, _ = instructions[prior_index]
        if opcode in (0x1a, 0x1b) and code[pc + 1] == register:
            string_index = struct.unpack_from(
                "<H" if opcode == 0x1a else "<I", code, pc + 2
            )[0]
            return dex.string(string_index)
        if _writes_register(opcode, code, pc, register):
            return None
    return None


def inspect_exact_onboarding_writer(dex, code, instructions=None):
    """Confirm exact Yandex_Music.edit().putBoolean(onboarding, ...).apply/commit.

    This is static direct-call/dataflow evidence only. It does not prove the
    method ran during login or that its caller belongs to Passport success.
    """
    instructions = instructions if instructions is not None else decode_instructions(code)
    preference_registers = set()
    editor_registers = set()
    written_editor_registers = set()
    pending_result = None
    direct_write = False
    persisted_write = False

    for index, (pc, opcode, _) in enumerate(instructions):
        if opcode == 0x0c:  # move-result-object
            destination = code[pc + 1]
            if pending_result == "PREFERENCE":
                preference_registers.add(destination)
            elif pending_result == "EDITOR":
                editor_registers.add(destination)
            elif pending_result == "WRITTEN_EDITOR":
                editor_registers.add(destination)
                written_editor_registers.add(destination)
            pending_result = None
            continue

        if opcode not in INVOKE_METHOD:
            pending_result = None
            continue

        method_index = struct.unpack_from("<H", code, pc + 2)[0]
        owner, name = dex.method(method_index)
        registers = _invoke_registers(code, pc, opcode)
        pending_result = None
        if registers is None:
            continue

        if (owner == "Landroid/content/Context;" and name == "getSharedPreferences"
                and len(registers) >= 2
                and _literal_argument(dex, code, instructions, index, registers[1])
                    == "Yandex_Music"):
            pending_result = "PREFERENCE"
        elif (owner == "Landroid/content/SharedPreferences;" and name == "edit"
                and registers and registers[0] in preference_registers):
            pending_result = "EDITOR"
        elif (owner == "Landroid/content/SharedPreferences$Editor;"
                and name == "putBoolean" and len(registers) >= 3
                and registers[0] in editor_registers
                and _literal_argument(dex, code, instructions, index, registers[1])
                    == "onboarding"):
            direct_write = True
            written_editor_registers.add(registers[0])
            pending_result = "WRITTEN_EDITOR"
        elif (owner == "Landroid/content/SharedPreferences$Editor;"
                and name in ("apply", "commit") and registers
                and registers[0] in written_editor_registers):
            persisted_write = True

    return direct_write, persisted_write


def scan_onboarding_methods(apkbytes: bytes):
    rows = []
    confirmed_writers = []
    persisted_writers = []
    undecodable = 0
    with zipfile.ZipFile(io.BytesIO(apkbytes)) as apk:
        required = {f"classes{i if i > 1 else ''}.dex" for i in range(1, ORIGINAL_CLASSES + 1)}
        if not required <= set(apk.namelist()):
            raise ValueError("PRIVATE_ONBOARDING_DEX_SET_MISMATCH")
        for dex_name in sorted(required):
            dex = Dex(apk.read(dex_name))
            for method_index, code in dex.code_methods():
                try:
                    instructions = decode_instructions(code)
                    strings, calls = _refs(dex, code, instructions)
                except FlowDecodeError:
                    undecodable += 1
                    continue
                if "onboarding" not in strings:
                    continue
                owner, name = dex.method(method_index)
                method = owner + "->" + name
                direct_write, persisted_write = inspect_exact_onboarding_writer(
                    dex, code, instructions
                )
                if direct_write:
                    confirmed_writers.append({"dex": dex_name, "method": method})
                if persisted_write:
                    persisted_writers.append({"dex": dex_name, "method": method})
                rows.append({"method": method, "dex": dex_name, **classify_calls(calls)})

    rows.sort(key=lambda row: (row["dex"], row["method"]))
    confirmed_writers.sort(key=lambda row: (row["dex"], row["method"]))
    persisted_writers.sort(key=lambda row: (row["dex"], row["method"]))
    writers = [row for row in rows if row["write_candidates"]]
    readers = [row for row in rows if row["read_calls"]]
    return {
        "original_dex_files": ORIGINAL_CLASSES,
        "onboarding_literal_method_count": len(rows),
        "undecodable_methods_skipped": undecodable,
        "onboarding_reader_candidates": readers,
        "onboarding_writer_candidates": writers,
        "confirmed_shared_preferences_onboarding_writers": confirmed_writers,
        "confirmed_persisted_onboarding_writers": persisted_writers,
        "static_callsite_not_runtime_login_proof": True,
        "raw_dex_or_preference_values_disclosed": False,
        "owner_auth_or_account_accessed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--xapk", type=Path)
    group.add_argument("--origin-apk", type=Path)
    args = parser.parse_args()
    source = source_from_xapk(args.xapk) if args.xapk else args.origin_apk.read_bytes()
    print(json.dumps(scan_onboarding_methods(source), sort_keys=True))


if __name__ == "__main__":
    main()
