#!/usr/bin/env python3
"""Read-only exact signed 2025.10.4 post-login DEX contract.

Private CI source only. Never reveal original bytes/UIDs/tokens or interpret
static method presence as a successful device login.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile
from a1_private_push_dex_method import Dex, EXPECTED_LEN, EXPECTED_SHA
from a1_private_dex_flow import decode_instructions, INVOKE_METHOD

ORIGINAL_CLASSES = 6

def source_from_xapk(path: Path) -> bytes:
    raw = path.read_bytes()
    if len(raw) != EXPECTED_LEN or hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("PRIVATE_ISSUER_SOURCE_MISMATCH")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        bases = []
        for member in archive.infolist():
            if not member.filename.lower().endswith(".apk"):
                continue
            if member.file_size > 65_000_000 or member.file_size < 1_000_000:
                continue
            data = archive.read(member)
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as split:
                    if {"classes.dex", "classes3.dex", "classes6.dex"} <= set(split.namelist()):
                        bases.append(data)
            except zipfile.BadZipFile:
                continue
        if len(bases) != 1:
            raise ValueError("PRIVATE_ISSUER_BASE_NOT_UNIQUE")
        return bases[0]

def references(dex: Dex, code: bytes) -> tuple[set[str], set[tuple[str, str]]]:
    strings, calls = set(), set()
    for pc, opcode, _ in decode_instructions(code):
        if opcode == 0x1a:
            strings.add(dex.string(struct.unpack_from("<H", code, pc+2)[0]))
        elif opcode == 0x1b:
            strings.add(dex.string(struct.unpack_from("<I", code, pc+2)[0]))
        elif opcode in INVOKE_METHOD:
            calls.add(dex.method(struct.unpack_from("<H", code, pc+2)[0])[:2])
    return strings, calls

def required_callsites():
    # These vendor symbols are exact-2025 private test assertions only.
    return {
      ("Lru/yandex/music/main/MainScreenActivity;", "onCreate"): (
         {"Yandex_Music", "onboarding", "com.yandex.passport.ACTION_LOGIN_RESULT"},
         {("Landroid/content/SharedPreferences;", "getBoolean")}),
      ("Lru/yandex/music/entry/EntryScreenActivity;", "onCreate"): (
         {"entry_type",
          "Entry screen activity entry type must not be null. Fallback to login"},
         {("Landroid/content/Intent;", "getParcelableExtra"),
          ("Lcom/yandex/music/shared/utils/assertions/Assertions;", "throwOrSkip"),
          ("LxT3$b;", "<init>")}),
      ("LeY5$a;", "emit"): (
         {"auto_login"}, {("LWS3$b;", "<init>"), ("LYX5;", "if")}),
      ("LoY5$a;", "emit"): (
         {"login result = "}, {("LqY5;", "if")}),
      ("LpY5$a;", "emit"): (
         {"autologin result = "}, {("LqY5;", "if")}),
      ("LZX5;", "if"): (
         {"EntryScreenLoginResultKey", "EntryScreenCloseLoginKey"},
         {("Landroidx/fragment/app/k;", "r")}),
      ("LhT3;", "try"): (
         {"EntryScreenCloseLoginKey", "EntryScreenLoginResultKey"},
         {("LiT3;", "g")}),
      ("LiT3;", "g"): (
         {"userInfo"}, {("LXS3;", "if")}),
      ("LYS3;", "if"): (
         {"userInfo"}, {("Landroid/app/Activity;", "startActivity")}),
      ("LqY5;", "if"): (
         {"Cannot get token after successful login", "Login is successful, but token is null"},
         {("LEd5;", "this"), ("LiE6;", "public"), ("Lol0;", "if")}),
      ("LKi7;", "try"): (
         set(), {("Lcom/yandex/passport/api/e;", "catch")}),
      ("LNG;", "this"): (
         set(), {("Ltya;", "new")}),
      ("Ltya;", "new"): (
         set(), {("LAd5;", "try"), ("Lyya;", "for")}),
      ("Lcom/yandex/passport/internal/core/accounts/p;", "if"): (
         {"uid", "user_info_body"},
         {("Landroid/accounts/AccountManager;", "addAccountExplicitly")}),
      ("Lcom/yandex/passport/internal/core/accounts/p;", "for"): (
         {"System account '", "account_type"},
         {("Landroid/accounts/AccountManager;", "getUserData")}),
      ("Lcom/yandex/passport/internal/core/accounts/p;", "else"): (
         set(), {("Landroid/accounts/AccountManager;", "getPassword")}),
      ("Lcom/yandex/passport/internal/storage/a;", "<init>"): (
         {"yandex_am_storage", "master_token_key"},
         {("Landroid/content/Context;", "getSharedPreferences"),
          ("LY7a;", "<init>")}),
      ("Lcom/yandex/passport/internal/core/accounts/v;", "try"): (
         {"AES", "SHA1PRNG"},
         {("LY7a;", "getValue"), ("LY7a;", "setValue")}),
      ("LY7a;", "getValue"): (
         {"property"}, {("Landroid/content/SharedPreferences;", "getString")}),
      ("LY7a;", "setValue"): (
         {"property"},
         {("Landroid/content/SharedPreferences$Editor;", "commit"),
          ("Landroid/content/SharedPreferences$Editor;", "apply")}),

    }


def _method_shape(dex: Dex, method_id: int):
    owner, name, proto = dex.method_signature(method_id)
    proto_count, proto_off = struct.unpack_from("<II", dex.data, 72)
    if proto >= proto_count or proto_off + proto_count * 12 > len(dex.data):
        raise DexError("PROTO_BOUND")
    _, return_idx, params_off = struct.unpack_from(
        "<III", dex.data, proto_off + proto * 12)
    params = []
    if params_off:
        if params_off + 4 > len(dex.data):
            raise DexError("TYPE_LIST_BOUND")
        count = struct.unpack_from("<I", dex.data, params_off)[0]
        if count > 64 or params_off + 4 + count * 2 > len(dex.data):
            raise DexError("TYPE_LIST_BOUND")
        params = [dex.type(struct.unpack_from(
            "<H", dex.data, params_off + 4 + i * 2)[0])
            for i in range(count)]
    return owner, name, dex.type(return_idx), tuple(params)


def _private_login_observer_contract(dexes: list[Dex]) -> dict:
    # Exact reflection signatures used by the passive Android observer.
    expected_methods = {
        ("LeY5$a;", "emit"): (
            "Ljava/lang/Object;",
            ("Ljava/lang/Object;", "Lkotlin/coroutines/Continuation;")),
        ("LoY5$a;", "emit"): (
            "Ljava/lang/Object;",
            ("Ljava/lang/Object;", "Lkotlin/coroutines/Continuation;")),
        ("LpY5$a;", "emit"): (
            "Ljava/lang/Object;",
            ("Ljava/lang/Object;", "Lkotlin/coroutines/Continuation;")),
        ("LqY5;", "if"): (
            "Ljava/lang/Object;",
            ("LqY5;", "Z", "Lcom/yandex/passport/api/n0;", "LOe2;")),
        ("LnY5;", "invokeSuspend"): (
            "Ljava/lang/Object;", ("Ljava/lang/Object;",)),
    }
    found = {key: [] for key in expected_methods}
    field_matches = set()
    super_matches = set()
    stage_contract = False

    for dex in dexes:
        for method_id in range(dex.method_count):
            owner, name, _ = dex.method_signature(method_id)
            key = (owner, name)
            if key in expected_methods:
                found[key].append(_method_shape(dex, method_id)[2:])

        field_count, field_off = struct.unpack_from("<II", dex.data, 80)
        if field_count > 500000 or field_off + field_count * 8 > len(dex.data):
            raise DexError("FIELD_TABLE_BOUND")
        for index in range(field_count):
            class_idx, type_idx, name_idx = struct.unpack_from(
                "<HHI", dex.data, field_off + index * 8)
            field_matches.add((
                dex.type(class_idx), dex.type(type_idx), dex.string(name_idx)))

        class_count, class_off = struct.unpack_from("<II", dex.data, 96)
        if class_count > 500000 or class_off + class_count * 32 > len(dex.data):
            raise DexError("CLASS_TABLE_BOUND")
        for index in range(class_count):
            class_idx, _, super_idx = struct.unpack_from(
                "<III", dex.data, class_off + index * 32)
            owner = dex.type(class_idx)
            if owner in ("LnY5;", "LqY5$a$a;", "LqY5$a$b;", "LqY5$a$c;"):
                superclass = (dex.type(super_idx)
                              if super_idx != 0xFFFFFFFF else None)
                super_matches.add((owner, superclass))

        for method_id, code in dex.code_methods():
            if dex.method(method_id) != ("LqY5;", "if"):
                continue
            instructions = decode_instructions(code)
            by_pc = {pc: opcode for pc, opcode, _ in instructions}
            continue_ids = []
            for field_id in range(field_count):
                field_base = field_off + field_id * 8
                if (dex.type(struct.unpack_from("<H", dex.data, field_base)[0]) == "LnY5;" and
                    dex.type(struct.unpack_from("<H", dex.data, field_base + 2)[0]) == "I" and
                    dex.string(struct.unpack_from("<I", dex.data, field_base + 4)[0]) == "continue"):
                    continue_ids.append(field_id)
            stage_contract = len(continue_ids) == 1
            if stage_contract:
                continue_id = continue_ids[0]
                # These exact byte offsets are pinned to the issuer XAPK hash above.
                # Each continuation label is stored immediately before its original
                # suspend call: 1=token request, 2=userInfo request, 3=sync.
                expected_sites = (
                    (0x4A, 0xCE, 0xD2, 1, 6, ("LEd5;", "this")),
                    (0x00, 0x106, 0x10A, 2, 0, ("LiE6;", "public")),
                    (0x48, 0x14C, 0x154, 3, 5, ("Lol0;", "if")),
                )
                for const_pc, iput_pc, call_pc, label, register, target in expected_sites:
                    if (by_pc.get(const_pc) != 0x12 or
                        by_pc.get(iput_pc) != 0x59 or
                        by_pc.get(call_pc) not in INVOKE_METHOD or
                        not const_pc < iput_pc < call_pc):
                        stage_contract = False
                        break
                    const_word = struct.unpack_from("<H", code, const_pc)[0]
                    const_reg = (const_word >> 8) & 0xF
                    const_value = (const_word >> 12) & 0xF
                    if const_value >= 8:
                        const_value -= 16
                    iput_word = struct.unpack_from("<H", code, iput_pc)[0]
                    iput_reg = (iput_word >> 8) & 0xF
                    field_id = struct.unpack_from("<H", code, iput_pc + 2)[0]
                    method_id = struct.unpack_from("<H", code, call_pc + 2)[0]
                    if (const_reg != register or const_value != label or
                        iput_reg != register or field_id != continue_id or
                        dex.method(method_id) != target):
                        stage_contract = False
                        break

    if any(found[key] != [shape] for key, shape in expected_methods.items()):
        raise DexError("PRIVATE_LOGIN_OBSERVER_SIGNATURE_MISMATCH")
    required_fields = {("LnY5;", "I", "continue")}
    required_supers = {
        ("LnY5;", "LOe2;"),
        ("LqY5$a$a;", "LqY5$a;"),
        ("LqY5$a$b;", "LqY5$a;"),
        ("LqY5$a$c;", "LqY5$a;"),
    }
    if not required_fields <= field_matches:
        raise DexError("PRIVATE_LOGIN_RESUME_FIELD_MISMATCH")
    if not required_supers <= super_matches or not stage_contract:
        raise DexError("PRIVATE_LOGIN_RESUME_STAGE_MISMATCH")
    return {
        "login_flow_reflection_signature_exact": True,
        "login_pipeline_reflection_signature_exact": True,
        "coroutine_resume_stage_contract_exact": True,
        "owner_auth_payload_accessed": False,
    }


def verify_original(apkbytes: bytes) -> dict:
    requirements = required_callsites()
    matched = set()
    dexes = []
    with zipfile.ZipFile(io.BytesIO(apkbytes)) as apk:
        files = {f"classes{i if i>1 else ''}.dex" for i in range(1, ORIGINAL_CLASSES+1)}
        if not files <= set(apk.namelist()):
            raise ValueError("PRIVATE_ISSUER_DEX_SET_MISMATCH")
        for dex_name in sorted(files):
            dex = Dex(apk.read(dex_name))
            dexes.append(dex)
            for idx, code in dex.code_methods():
                owner, name = dex.method(idx)
                key = (owner, name)
                if key not in requirements:
                    continue
                strings, calls = references(dex, code)
                required_strings, required_calls = requirements[key]
                if required_strings <= strings and required_calls <= calls:
                    matched.add(key)
    if len(matched) != len(requirements):
        raise ValueError("PRIVATE_POSTLOGIN_CONTRACT_INCOMPLETE")
    observer_contract = _private_login_observer_contract(dexes)
    return {"private_postlogin_contracts_present":len(matched),
            **observer_contract,
            "original_dex_files":ORIGINAL_CLASSES,
            "owner_token_or_auth_was_accessed":False,
            "owner_login_success_proven":False,
            "runtime_return_delivery_proven":False,
            "no_publisher_byte_edits":True}

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--xapk", type=Path)
    group.add_argument("--origin-apk", type=Path)
    args = parser.parse_args()
    raw = source_from_xapk(args.xapk) if args.xapk else args.origin_apk.read_bytes()
    print(json.dumps(verify_original(raw), sort_keys=True))

if __name__ == "__main__":
    main()
