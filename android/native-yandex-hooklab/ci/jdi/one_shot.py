"""One-shot exact caught-exception JDI experiment for disposable own Android13 clone.

Off by default. No hook of 16 methods; one exact DEX method-entry filter,
then caught ExceptionEvent on its thread. Private names and PCs stay in CI.
A debuggable disposable clone is NECESSARY for JDI and is not product evidence.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import io
import struct

HERE=Path(__file__).resolve().parent
CI=HERE.parent
sys.path.insert(0,str(CI))
sys.path.insert(0,str(CI.parents[1]/"a1-exact-catch-helper"))
from a1_private_push_dex_method import (
    Dex,EXPECTED_LEN,EXPECTED_SHA,private_java_parameter_signature,
)
from a1_private_dex_flow import decode_instructions,INVOKE_METHOD
from exact_catch import _locate_code_item,read_catches,_inside

TARGET=CI.parent/"exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/PrivatePushTargets.java"
JDI_JAVA=HERE/"ExactCatchJdi.java"
VALID_FAMILY={"SDK_LEGACY","SDK_MODERN","JAVA","ANDROID","OTHER"}

def exact_target():
    data=TARGET.read_text(encoding="utf-8")
    match=re.search(
        r"getFatalExactObjectTargets\(\).*?return new String\[\]\[\]\s*\{(.*?)\};",
        data,re.S)
    if not match:raise RuntimeError("JDI_EXACT_TARGET_MISSING")
    rows=re.findall(r'\{\s*"[^"\\]*(?:\\.[^"\\]*)*"\s*,\s*"[^"\\]*"\s*,\s*"[^"\\]*(?:\\.[^"\\]*)*"\s*\}',match.group(1))
    if len(rows)!=1:raise RuntimeError("JDI_EXACT_TARGET_NOT_UNIQUE")
    item=json.loads("["+rows[0].replace("{","[",1).rsplit("}",1)[0]+"]]")
    if len(item)!=3 or item[1]!="a":raise RuntimeError("JDI_EXACT_TARGET_INVALID")
    return item

def candidate_pcs(xapk, target):
    """Only exact class/name/argument signature from verified private original."""
    import hashlib
    file=Path(xapk)
    if file.stat().st_size != EXPECTED_LEN or hashlib.file_digest(file.open("rb"),"sha256").hexdigest()!=EXPECTED_SHA:
        raise RuntimeError("JDI_PRIVATE_SOURCE_INVALID")
    candidates=[]
    with zipfile.ZipFile(file) as archive:
        for info in archive.infolist():
            if not info.filename.endswith(".apk") or info.file_size>60000000:continue
            with zipfile.ZipFile(io.BytesIO(archive.read(info))) as inner:
                for name in inner.namelist():
                    if not name.startswith("classes") or not name.endswith(".dex"):continue
                    payload=inner.read(name)
                    if not payload.startswith(b"dex\n"):continue
                    dex=Dex(payload)
                    for mid,code in dex.code_methods():
                        owner,method=dex.method(mid)
                        owner=owner.strip("L;").replace("/",".")
                        if (owner,method,private_java_parameter_signature(dex,mid))!=tuple(target):
                            continue
                        off=_locate_code_item(dex,mid)
                        checked,ranges=read_catches(dex.data,off,dex)
                        if checked!=code:raise RuntimeError("JDI_CODE_ITEM_DRIFT")
                        pcs=sorted({pc for pc,op,_ in decode_instructions(code)
                            if op in INVOKE_METHOD and _inside(pc,ranges)})
                        candidates.append(pcs)
    if len(candidates)!=1:raise RuntimeError("JDI_METHOD_MATCH_NOT_UNIQUE")
    return candidates[0]

def safe_map(raw, pcs):
    events=[]
    for line in raw.splitlines()[:16]:
        match=re.fullmatch(r"(-?\d+)\|(SDK_LEGACY|SDK_MODERN|JAVA|ANDROID|OTHER)\|(SDK_LEGACY|SDK_MODERN|JAVA|ANDROID|OTHER)",line)
        if not match:continue
        index=int(match.group(1))
        # ART JDWP codeIndex may use DEX code units or bytes. Only unambiguous
        # instruction-boundary matches are admissible; never guess a PC.
        matches=[i for i,pc in enumerate(pcs) if index in (pc,pc//2)]
        label=("CASE_"+str(matches[0]).zfill(2)) if len(matches)==1 and matches[0]<100 else "UNMAPPED"
        events.append({"callsite":label,"throw_family":match.group(2),"exception_family":match.group(3)})
    return events

def one_shot(guest,cmd,package,xapk):
    report={"status":"UNKNOWN","debuggable_lab_only":True,
            "observed_exact_catches":[],"vendor_data_published":False,
            "suppressed":False,"sdk_modified":False}
    try:
        if os.getenv("CELIKOM_A1_JDI_CATCH_DIAG")!="1":
            report["status"]="DISABLED";return report
        if not shutil.which("adb") or not shutil.which("javac") or not shutil.which("java"):
            report["status"]="HOST_JDI_TOOLS_ABSENT";return report
        target=exact_target()
        pcs=candidate_pcs(xapk,target)
        conn=cmd(["adb","connect","127.0.0.1:5555"],timeout=20)
        if conn.returncode:report["status"]="ADB_CONNECT_FAILED";return report
        g=guest("dumpsys","package",package,timeout=40)
        if g.returncode or "DEBUGGABLE" not in g.stdout:
            report["status"]="CLONE_NOT_DEBUGGABLE";return report
        build=Path(os.environ["RUNNER_TEMP"])/"celikom-exact-jdi-classes"
        build.mkdir(mode=0o700,parents=True,exist_ok=True)
        compiled=cmd(["javac","--add-modules","jdk.jdi","-d",str(build),str(JDI_JAVA)],timeout=50)
        if compiled.returncode:
            report["status"]="JDI_COMPILE_FAILED";return report
        waiting=guest("am","set-debug-app","-w",package)
        if waiting.returncode:
            report["status"]="SET_DEBUG_APP_FAILED";return report
        component=package+"/ru.yandex.music.main.MainScreenActivity"
        launched=guest("am","start","--user","0","-n",component,timeout=40)
        if launched.returncode:
            report["status"]="CLONE_DEBUG_LAUNCH_FAILED";return report
        pid=None
        for i in range(40):
            time.sleep(0.5)
            current=guest("pidof",package)
            if not re.fullmatch(r"[1-9][0-9]{0,8}",current.stdout.strip()):continue
            candidate=current.stdout.strip()
            listing=cmd(["adb","-s","127.0.0.1:5555","jdwp"],timeout=15)
            if listing.returncode==0 and candidate in listing.stdout.splitlines():
                pid=candidate;break
        if not pid:
            report["status"]="JDWP_PROCESS_ABSENT";return report
        forward=cmd(["adb","-s","127.0.0.1:5555","forward","tcp:8707","jdwp:"+pid],timeout=20)
        if forward.returncode:
            report["status"]="JDWP_FORWARD_FAILED";return report
        with tempfile.TemporaryDirectory(prefix="celikom-jdi-private-",dir=os.environ["RUNNER_TEMP"]) as temp:
            witness=Path(temp)/"catch-identity.txt"
            executable=["java","--add-modules","jdk.jdi","-cp",str(build),
                "pro.celikom.a1diagnostic.ExactCatchJdi","8707",*target,str(witness)]
            jdi=subprocess.run(executable,capture_output=True,text=True,timeout=95)
            # Parse only fixed finite status and counts; no raw debugger output.
            m=re.search(r'JDI_RESULT\s+(\{.*?\})',jdi.stdout)
            result=json.loads(m.group(1)) if m else {}
            report["status"]=result.get("status","JDI_NO_SUMMARY") if result.get("status") in (
                "VM_EXIT","ATTACHED","PARTIAL","ATTACH_OR_RUNTIME_FAILURE"
            ) else "JDI_NO_SUMMARY"
            report["exact_method_entries"]=min(max(int(result.get("exact_method_entries",0)),0),99)
            report["exact_caught_events"]=min(max(int(result.get("exact_caught_events",0)),0),8)
            if witness.is_file():
                report["observed_exact_catches"]=safe_map(witness.read_text(),pcs)
        return report
    except (Exception,TimeoutError):
        report["status"]="JDI_INCONCLUSIVE"
        return report
    finally:
        # Debug wait and local forward NEVER survive to ordinary 75s gate.
        try:guest("am","clear-debug-app")
        except Exception:pass
        try:guest("am","force-stop",package)
        except Exception:pass
        if shutil.which("adb"):
            try:cmd(["adb","-s","127.0.0.1:5555","forward","--remove","tcp:8707"],timeout=10)
            except Exception:pass
