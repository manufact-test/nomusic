#!/usr/bin/env python3
"""One bounded signed-2025 wh6/o96 MediaPeriod.prepare shape check.

Checks ONLY the already-established original period interface and concrete
period implementation; no track data, guessed IDs, media bytes, network or
private symbols are exposed. Does NOT prove actual playback/call timing.
"""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

import lft2_class_inspection as trusted
from trace_native_callers import uleb

audit=trusted.audit
IFACE="Lwh6;"
CONCRETE="Lo96;"
MAX_METHODS=600

def declared_methods(dex, class_index):
    base=dex.class_offset+class_index*32
    pos=dex.u32(base+24)
    if not pos:
        return []
    n_static,pos=uleb(dex,pos)
    n_instance,pos=uleb(dex,pos)
    n_direct,pos=uleb(dex,pos)
    n_virtual,pos=uleb(dex,pos)
    if max(n_static,n_instance,n_direct,n_virtual)>MAX_METHODS:
        raise ValueError("EXACT_PERIOD_CLASS_LIMIT")
    for _ in range(n_static+n_instance):
        _,pos=uleb(dex,pos)
        _,pos=uleb(dex,pos)
    methods=[]
    for total in (n_direct,n_virtual):
        mid=0
        for _ in range(total):
            diff,pos=uleb(dex,pos)
            flags,pos=uleb(dex,pos)
            _code,pos=uleb(dex,pos)
            mid+=diff
            methods.append((dex.method(mid),flags))
    return methods

def scan(splits):
    found={}
    dex_count=0
    for apk in splits:
        with zipfile.ZipFile(apk) as z:
            for item in z.infolist():
                if not re.fullmatch(r"classes\d*\.dex",item.filename):
                    continue
                dex_count+=1
                dex=audit.Dex(z.read(item.filename))
                for ci in range(dex.class_count):
                    base=dex.class_offset+ci*32
                    desc=dex.descriptor(dex.u32(base))
                    if desc not in (IFACE,CONCRETE):
                        continue
                    if desc in found:
                        raise ValueError("EXACT_PERIOD_CLASS_DUPLICATE")
                    found[desc]={
                        "is_interface":bool(dex.u32(base+4)&0x200),
                        "methods":declared_methods(dex,ci)
                    }
    if dex_count!=6 or len(found)!=2:
        raise ValueError("EXACT_SIGNED_PERIOD_CLASSES_SIX_DEX_REQUIRED")
    iface=found[IFACE]
    concrete=found[CONCRETE]
    candidates=[]
    for (owner,name,proto),flags in iface["methods"]:
        params=audit.parse_types(proto)
        if (owner==IFACE and len(params)==2
                and params[0].startswith("Lwh6$")
                and params[1]=="J" and proto.endswith(")V")):
            candidates.append((name,proto))
    exact_matches=sum(
        (owner==CONCRETE and (name,proto) in candidates
         and not (flags&0x0400) and not (flags&0x0008))
        for (owner,name,proto),flags in concrete["methods"]
    )
    return {
        "verdict": ("ONE_EXACT_CONCRETE_PERIOD_PREPARE_SHAPE"
                    if iface["is_interface"] and not concrete["is_interface"]
                    and len(candidates)==1 and exact_matches==1
                    else "NO_GO_PERIOD_PREPARE_SHAPE_NOT_UNIQUE"),
        "original_period_interface_defined":iface["is_interface"],
        "concrete_period_class_defined":not concrete["is_interface"],
        "callback_long_void_contract_count":len(candidates),
        "concrete_override_count":exact_matches,
        "live_original_prepare_observed":False,
        "current_track_album_edition_attested":False,
        "alternate_audio_connected":False,
        "private_method_names_exported":False
    }

def run(path):
    if os.environ.get("GITHUB_ACTIONS")!="true" or os.environ.get("GITHUB_REPOSITORY")!="manufact-test/nomusic":
        raise RuntimeError("PINNED_ORIGINAL_CI_ONLY")
    if path.stat().st_size!=trusted.PINNED_XAPK_BYTES or trusted.sha256_file(path)!=trusted.PINNED_XAPK_SHA256:
        raise ValueError("PINNED_ORIGINAL_SOURCE_HASH_DRIFT")
    with tempfile.TemporaryDirectory(prefix="celikom-original-period-") as tmp:
        splits=audit.unbundle_candidate(path,Path(tmp))
        if len(splits)!=16 or audit.verify_split_set(splits).get("verified_issuer_signed_splits")!=16:
            raise ValueError("ORIGINAL_SOURCE_SIGNING_MISMATCH")
        return scan(splits)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--xapk",required=True,type=Path)
    args=ap.parse_args()
    try:
        print(json.dumps(run(args.xapk),sort_keys=True))
    except Exception as error:
        print(json.dumps({"verdict":"PERIOD_PREPARE_TARGET_SCAN_FAILED",
            "error_type":type(error).__name__,"alternate_audio_connected":False},
            sort_keys=True))
        raise SystemExit(2)
