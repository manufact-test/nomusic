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
         {"entry_type"}, {("Landroid/content/Intent;", "getParcelableExtra")}),
      ("LeY5$a;", "emit"): (
         {"auto_login"}, {("LWS3$b;", "<init>"), ("LYX5;", "if")}),
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
    }

def verify_original(apkbytes: bytes) -> dict:
    requirements = required_callsites()
    matched = set()
    with zipfile.ZipFile(io.BytesIO(apkbytes)) as apk:
        files = {f"classes{i if i>1 else ''}.dex" for i in range(1, ORIGINAL_CLASSES+1)}
        if not files <= set(apk.namelist()):
            raise ValueError("PRIVATE_ISSUER_DEX_SET_MISMATCH")
        for dex_name in sorted(files):
            dex = Dex(apk.read(dex_name))
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
    return {"private_postlogin_contracts_present":len(matched),
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
