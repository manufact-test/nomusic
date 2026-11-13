#!/usr/bin/env python3
"""Single failure-specific audit: source 2025 XAPK Firebase identifier *names*.

Only exact 16 publisher splits, only in ephemeral CI. No resource string values,
manifest attribute values, file names, class names, tokens or APK bytes printed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

SHA="8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
LENGTH=45961661
BRANCH="experiment/android-a1-metrica-init-state-observer-arm13-20261112"
META=(
    "ymp_firebase_app_id","ymp_gcm_sender_id",
    "ymp_firebase_default_app_id","ymp_gcm_default_sender_id"
)
RESOURCES=("google_app_id","gcm_defaultSenderId")

def ensure_isolated():
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!=BRANCH):
        raise ValueError("ISOLATION")

def names_in_xml(text):
    return {name:bool(re.search(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',text))
            for name in META}

def names_in_resources(text):
    # aapt resource name index, not the resource's string content.
    return {name:bool(re.search(r'(?:^|\\s)string/'+re.escape(name)+r'(?=[:\\s])',
                 text,re.MULTILINE))
            for name in RESOURCES}

def aapt(args):
    p=subprocess.run(["aapt",*args],capture_output=True,text=True,
                     errors="replace",timeout=90)
    if p.returncode!=0:
        raise ValueError("AAPT_READ_FAILED")
    return p.stdout

def run(xapk):
    ensure_isolated()
    raw=Path(xapk).read_bytes()
    if len(raw)!=LENGTH or hashlib.sha256(raw).hexdigest()!=SHA:
        raise ValueError("PUBLISHER_INPUT_DRIFT")
    with zipfile.ZipFile(xapk) as z:
        members=[m for m in z.infolist() if m.filename.lower().endswith(".apk")]
        if len(members)!=16:
            raise ValueError("SOURCE_SPLITS_NOT_16")
        mflags={name:False for name in META}
        rflags={name:False for name in RESOURCES}
        successful=0
        with tempfile.TemporaryDirectory(prefix="celikom-a1-source-firebase-") as tmp:
            for idx,member in enumerate(members):
                with z.open(member) as f:
                    data=f.read()
                p=Path(tmp)/("split-%02d.apk"%idx)
                p.write_bytes(data)
                xml=aapt(["dump","xmltree",str(p),"AndroidManifest.xml"])
                res=aapt(["dump","resources",str(p)])
                for name,flag in names_in_xml(xml).items():
                    mflags[name] |= flag
                for name,flag in names_in_resources(res).items():
                    rflags[name] |= flag
                successful+=1
    return {
        "publisher_source_verified":True,
        "splits_audited":successful,
        "custom_metadata_name_pair": "BOTH" if mflags[META[0]] and mflags[META[1]]
            else "PARTIAL" if mflags[META[0]] or mflags[META[1]] else "NONE",
        "default_metadata_name_pair": "BOTH" if mflags[META[2]] and mflags[META[3]]
            else "PARTIAL" if mflags[META[2]] or mflags[META[3]] else "NONE",
        "google_string_resource_name_pair":
            "BOTH" if rflags[RESOURCES[0]] and rflags[RESOURCES[1]]
            else "PARTIAL" if rflags[RESOURCES[0]] or rflags[RESOURCES[1]]
            else "NONE",
        "values_or_binary_disclosed":False,
        "runtime_causality_proven":False,
    }

def test_only():
    assert names_in_xml('android:name="ymp_firebase_app_id"')["ymp_firebase_app_id"]
    assert not names_in_xml('android:name="ymp_firebase_app_id_bad"')["ymp_firebase_app_id"]
    assert names_in_resources('resource 0x78 test:string/google_app_id: t=0x03')["google_app_id"]
    assert not names_in_resources('resource 0x78 test:string/google_app_id_EXTRA:')["google_app_id"]
    return {"self_test":"PASS","values_or_binary_disclosed":False}

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--xapk",type=Path)
    cli.add_argument("--self-test",action="store_true")
    args=cli.parse_args()
    try:
        result=test_only() if args.self_test else run(args.xapk)
        print("FIREBASE_SOURCE_PRESENCE "+json.dumps(result,sort_keys=True))
    except Exception:
        print('FIREBASE_SOURCE_PRESENCE {"audit":"UNKNOWN","values_or_binary_disclosed":false}')
        raise SystemExit(2)
