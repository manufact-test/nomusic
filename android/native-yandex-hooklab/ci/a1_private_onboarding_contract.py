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
import zipfile

from a1_private_postlogin_contract import source_from_xapk
from a1_private_push_dex_method import Dex
from a1_private_dex_flow import decode_instructions, INVOKE_METHOD, FlowDecodeError
import struct

ORIGINAL_CLASSES=6
EDITOR_CALLS={"putBoolean","putString","putInt","putLong","remove","clear","apply","commit"}
READ_CALLS={"getBoolean","getString","getInt","getLong","contains"}
KEY_WRITERS={"putBoolean","setValue","putString","putInt","putLong"}

def _refs(dex, code):
    strings=set()
    calls=set()
    for pc,opcode,_ in decode_instructions(code):
        if opcode==0x1a:
            strings.add(dex.string(struct.unpack_from("<H",code,pc+2)[0]))
        elif opcode==0x1b:
            strings.add(dex.string(struct.unpack_from("<I",code,pc+2)[0]))
        elif opcode in INVOKE_METHOD:
            calls.add(dex.method(struct.unpack_from("<H",code,pc+2)[0]))
    return strings,calls

def classify_calls(calls):
    names=sorted({name for _,name in calls if name in EDITOR_CALLS|READ_CALLS})
    writes=sorted({name for _,name in calls if name in KEY_WRITERS})
    reads=sorted({name for _,name in calls if name in READ_CALLS})
    return {"preference_calls":names,"write_candidates":writes,"read_calls":reads}

def scan_onboarding_methods(apkbytes: bytes):
    rows=[]
    undecodable=0
    with zipfile.ZipFile(io.BytesIO(apkbytes)) as apk:
        required={f"classes{i if i>1 else ''}.dex" for i in range(1,ORIGINAL_CLASSES+1)}
        if not required <= set(apk.namelist()):
            raise ValueError("PRIVATE_ONBOARDING_DEX_SET_MISMATCH")
        for dex_name in sorted(required):
            dex=Dex(apk.read(dex_name))
            for method_index,code in dex.code_methods():
                try:
                    strings,calls=_refs(dex,code)
                except FlowDecodeError:
                    undecodable+=1
                    continue
                if "onboarding" not in strings:
                    continue
                owner,name=dex.method(method_index)
                classified=classify_calls(calls)
                rows.append({"method":owner+"->"+name,
                             "dex":dex_name,
                             **classified})
    rows.sort(key=lambda row:(row["dex"],row["method"]))
    writers=[row for row in rows if row["write_candidates"]]
    readers=[row for row in rows if row["read_calls"]]
    return {
      "original_dex_files":ORIGINAL_CLASSES,
      "onboarding_literal_method_count":len(rows),
      "undecodable_methods_skipped":undecodable,
      "onboarding_reader_candidates":readers,
      "onboarding_writer_candidates":writers,
      "raw_dex_or_preference_values_disclosed":False,
      "owner_auth_or_account_accessed":False,
    }

def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--xapk",type=Path)
    group.add_argument("--origin-apk",type=Path)
    args=parser.parse_args()
    if args.xapk:
        source=source_from_xapk(args.xapk)
    else:
        source=args.origin_apk.read_bytes()
    print(json.dumps(scan_onboarding_methods(source),sort_keys=True))

if __name__=="__main__":
    main()
