#!/usr/bin/env python3
"""Issue #47: ONE CASE_0 process-role hypothesis, read-only exact XAPK + ARM13.

Proprietary symbols and strings stay inside disposable CI. All stdout fields
are finite categories/counters. Imports A's exact reader and native runner,
without editing their code, runtime SDK values, fatal handlers or APK signing.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import threading
import time
import zipfile

BRANCH="experiment/android-a1-helper-process-identity-case0-arm13-20261112"
ORIGINAL="ru.yandex.music"
CLONE="pro.celikom.yandex.nativeclonelab"
CONTAINER="celikom-native-arm-android13"
NATIVE=Path(__file__).resolve().parents[1]/"native-yandex-hooklab"
CI=NATIVE/"ci"
STAGE="LOAD"
for item in (str(NATIVE),str(CI)):
    if item not in sys.path:sys.path.insert(0,item)
from ci import a1_private_push_dex_method as dexmod
from ci.a1_private_dex_flow import decode_instructions, FlowDecodeError, INVOKE_METHOD

def required_environment():
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"):
        raise ValueError("HELPER_CI_BRANCH_ISOLATION")

def read_apks_exact(xapk:Path):
    if not xapk.is_file() or xapk.is_symlink() or xapk.stat().st_size!=dexmod.EXPECTED_LEN:
        raise ValueError("VERIFIED_XAPK_SIZE")
    with xapk.open("rb") as fp:
        if hashlib.file_digest(fp,"sha256").hexdigest()!=dexmod.EXPECTED_SHA:
            raise ValueError("VERIFIED_XAPK_SHA")
    with zipfile.ZipFile(xapk) as root:
        for apk in root.infolist():
            if not apk.filename.endswith(".apk") or apk.file_size>60_000_000:continue
            with zipfile.ZipFile(io.BytesIO(root.read(apk))) as part:
                for name in part.namelist():
                    if name.startswith("classes") and name.endswith(".dex"):
                        data=part.read(name)
                        if data.startswith(b"dex\n"):yield data

def _api_category(owner,name):
    if owner=="Landroid/app/ActivityThread;" and name in (
        "currentProcessName","currentPackageName"):
        return "ANDROID_PROCESS_NAME_SUPPLIER"
    if owner=="Landroid/app/Application;" and name=="getProcessName":
        return "APPLICATION_PROCESS_NAME_SUPPLIER"
    if owner=="Landroid/os/Process;" and name in ("myPid","myUid"):
        return "ANDROID_PID_OR_UID"
    if owner=="Landroid/app/ActivityManager;" and name=="getRunningAppProcesses":
        return "ACTIVITY_MANAGER_PROCESS_LIST"
    if owner in ("Landroid/content/Context;","Landroid/app/Application;") and name=="getPackageName":
        return "ANDROID_CONTEXT_PACKAGE_SUPPLIER"
    if owner=="Ljava/lang/String;" and name in ("equals","equalsIgnoreCase"):
        return "JAVA_STRING_EQUALITY"
    if owner=="Ljava/lang/String;" and name in ("startsWith","contains","isEmpty"):
        return "JAVA_STRING_OTHER_PREDICATE"
    if owner=="Landroid/text/TextUtils;" and name=="equals":
        return "ANDROID_TEXT_EQUALITY"
    if owner=="Ljava/util/Objects;" and name=="equals":
        return "JAVA_OBJECT_EQUALITY"
    if owner.startswith("Lcom/yandex/metrica/") or owner.startswith("Lio/appmetrica/analytics/"):
        return "SDK_INTERNAL_OR_PUBLIC"
    return "OTHER"

def _body(dex,mid,code):
    try: ins=decode_instructions(code)
    except FlowDecodeError:
        return {"decoded":False,"direct_process_supply":[],"comparison_apis":[],
                "branches":[],"one_hop":[],"return_op_count":0,
                "old_stock_literal_in_method":False,"new_clone_literal_in_method":False},set()
    cats=set()
    refs=set()
    old=new=False
    branches=set()
    ret=0
    for pc,op,_ in ins:
        if op in INVOKE_METHOD:
            idx=struct.unpack_from("<H",code,pc+2)[0]
            if idx>=dex.method_count:continue
            refs.add(idx)
            cats.add(_api_category(*dex.method(idx)))
        if op in (0x1a,0x1b):
            idx=(struct.unpack_from("<H",code,pc+2)[0] if op==0x1a
                 else struct.unpack_from("<I",code,pc+2)[0])
            if idx<dex.string_count:
                string=dex.string(idx)
                old |= string==ORIGINAL or string.startswith(ORIGINAL+":")
                new |= string==CLONE or string.startswith(CLONE+":")
        if op in (0x38,0x39):
            branches.add("IF_EQZ" if op==0x38 else "IF_NEZ")
        elif 0x32<=op<=0x37:
            branches.add("IF_TWO_REG")
        elif 0x3a<=op<=0x3d:
            branches.add("IF_OTHER_ZERO")
        if op==0x0f:ret+=1
    return {
        "decoded":True,
        "direct_process_supply":sorted(cats & {
            "ANDROID_PROCESS_NAME_SUPPLIER","APPLICATION_PROCESS_NAME_SUPPLIER",
            "ANDROID_CONTEXT_PACKAGE_SUPPLIER","ACTIVITY_MANAGER_PROCESS_LIST",
            "ANDROID_PID_OR_UID"}),
        "comparison_apis":sorted(cats & {"JAVA_STRING_EQUALITY",
            "JAVA_OBJECT_EQUALITY","ANDROID_TEXT_EQUALITY","JAVA_STRING_OTHER_PREDICATE"}),
        "branches":sorted(branches),
        "return_op_count":min(ret,24),
        "old_stock_literal_in_method":old,
        "new_clone_literal_in_method":new,
        "one_hop":[],
    },refs

def inspect(xapk:Path, generated:Path|None):
    global STAGE
    STAGE="VERIFY_ENV"
    required_environment()
    cases=set()
    STAGE="VERIFY_SOURCE"
    files=list(read_apks_exact(xapk))
    STAGE="ENUMERATE_CASES"
    for payload in files:
        cases.update(dexmod.private_all_exact_guard_methods(payload))
    STAGE="RESOLVE_CASE0"
    selected=sorted(cases)[:8]
    outcome={"verified_xapk":True, "dex_files_bounded":min(len(files),20),
             "case_count":min(len(selected),8), "case0_present":bool(selected),
             "case0_return_type_boolean":False,"stock_in_jvm_value":"UNKNOWN",
             "actual_meaning_of_false":"UNKNOWN",
             "exact_predicate_branch_for_main":"UNKNOWN",
             "case0_direct_process_supplier":[],"case0_comparison_api":[],
             "case0_if_opcodes":[],"case0_return_instruction_count":0,
             "case0_original_package_literal":False,
             "case0_clone_package_literal":False,
             "case0_one_hop_process_supplier":[],
             "private_methods_or_values_published":False}
    if selected:
        cls,name,proto=selected[0]
        matched=0
        known_onehop=set()
        STAGE="READ_CASE0_BODY"
        for payload in files:
            dex=dexmod.Dex(payload)
            bodies={mid:body for mid,body in dex.code_methods()}
            index={}
            for mid in bodies:
                o,n=dex.method(mid)
                key=(o.strip("L;").replace("/","."),n,dexmod.private_java_parameter_signature(dex,mid))
                if key==(cls,name,proto):index[mid]=bodies[mid]
            for mid,code in index.items():
                matched+=1
                base,refs=_body(dex,mid,code)
                outcome["case0_return_type_boolean"] |= dex.method_returns_boolean(mid)
                outcome["case0_direct_process_supplier"]=base["direct_process_supply"]
                outcome["case0_comparison_api"]=base["comparison_apis"]
                outcome["case0_if_opcodes"]=base["branches"]
                outcome["case0_return_instruction_count"]=base["return_op_count"]
                outcome["case0_original_package_literal"] |= base["old_stock_literal_in_method"]
                outcome["case0_clone_package_literal"] |= base["new_clone_literal_in_method"]
                for ref in sorted(refs)[:40]:
                    if ref in bodies and ref!=mid:
                        one,_=_body(dex,ref,bodies[ref])
                        known_onehop.update(one["direct_process_supply"])
        outcome["case0_matching_bodies_bounded"]=min(matched,8)
        outcome["case0_one_hop_process_supplier"]=sorted(known_onehop)
    STAGE="GENERATE_TEMP_TARGETS"
    if generated is not None:
        # Own isolated temp copy of A module. Source-derived Java stays PRIVATE.
        targets=dexmod.generate_private_targets(xapk,generated)
        outcome["transient_targets_generated"]=bool(
            targets.get("private_transient_all_fatal_guard_exact_targets_bounded"))
        if not outcome["transient_targets_generated"]:
            raise ValueError("CASE0_PRIVATE_HOOK_TARGET_MISSING")
    STAGE="DONE"
    print("CASE0_PRIVATE_DEX "+json.dumps(outcome,sort_keys=True),flush=True)
    return outcome

def guest(*args,timeout=18):
    try:
        p=subprocess.run(["docker","exec",CONTAINER,*args],capture_output=True,
                         text=True,errors="replace",check=False,timeout=timeout)
        return (p.returncode==0,p.stdout[:1_000_000])
    except (subprocess.TimeoutExpired,OSError):
        return (False,"")

def parse_ps(ps,package):
    # Android ps -A last column is the exact kernel command name.
    names=[row.split()[-1] for row in ps.splitlines()[:2500] if row.split()]
    return {"main":package in names,
            "any_aux":any(n.startswith(package+":") for n in names),
            "wrong_original_main":package==CLONE and ORIGINAL in names,
            "metrica_aux":any(n.startswith(package+":") and "metrica" in n.lower()
                              for n in names)}

def parse_events(s,package):
    count=collections.Counter()
    for line in s.splitlines()[-18000:]:
        if package not in line:continue
        if "am_proc_start" in line:kind="START"
        elif "am_proc_bound" in line:kind="BOUND"
        elif "am_proc_died" in line:kind="DIED"
        else:continue
        # Exact package vs :service name, no raw string leaks.
        linepart=line.split(package,1)[1]
        role="AUX" if linepart.startswith(":") else "MAIN"
        count[kind+"_"+role]+=1
    return {k:min(v,30) for k,v in sorted(count.items())}

class RoleSampler:
    def __init__(self,package):
        self.package=package
        self.stop=threading.Event()
        self.stats=collections.Counter()
        self.cycles=0
        self.thread=threading.Thread(target=self._run,daemon=True)
    def _run(self):
        for i in range(42):
            if self.stop.is_set():break
            ok,s=guest("ps","-A",timeout=15)
            if ok:
                roles=parse_ps(s,self.package)
                for k,v in roles.items():
                    if v:self.stats[k+"_seen"]+=1
            else:self.stats["ps_unavailable"]+=1
            self.cycles+=1
            if self.stop.wait(0.9):break
    def start(self):self.thread.start()
    def finish(self):
        self.stop.set();self.thread.join(timeout=16)
        ok,events=guest("logcat","-d","-b","events","-v","tag",timeout=26)
        return {"ps_observations_bounded":self.cycles,
                "ps_error_samples":min(self.stats["ps_unavailable"],42),
                "actual_package_main_pid_observed":self.stats["main_seen"]>0,
                "actual_package_aux_pid_observed":self.stats["any_aux_seen"]>0,
                "metrica_aux_pid_observed":self.stats["metrica_aux_seen"]>0,
                "system_eventlog_available":ok,
                "android_activity_manager_process_events":parse_events(events,self.package) if ok else {},
                "actual_process_name_value_logged":False}

def _manifest(xml):
    # Read app default process and single launchable main activity process.
    section=None;depth=0
    result={"application_process":"DEFAULT","main_activity_process":"DEFAULT",
            "application_class_present":False,"main_activity_manifest_seen":False}
    for line in xml.splitlines()[:30000]:
        stripped=line.lstrip()
        indent=len(line)-len(stripped)
        if re.match(r"E: (application|activity)(?:\s|$)",stripped):
            section="application" if stripped.startswith("E: application") else "activity"
            depth=indent
        elif section and stripped.startswith("E: ") and indent<=depth:
            section=None
        if section and indent>depth:
            if 'android:name' in stripped and "ru.yandex.music.main.MainScreenActivity" in stripped:
                result["main_activity_manifest_seen"]=True
            if 'android:name' in stripped and section=="application":
                result["application_class_present"]=True
            if 'android:process' in stripped:
                # Classify literal only in memory; no vendor value in stdout.
                m=re.search(r'="([^"]+)"',stripped)
                if m:
                    v=m.group(1)
                    role=("DEFAULT" if not v else "PRIVATE_AUX" if v.startswith(":") else
                          "STOCK_ABSOLUTE" if v.startswith(ORIGINAL) else
                          "CLONE_ABSOLUTE" if v.startswith(CLONE) else "OTHER_ABSOLUTE")
                    result[("application" if section=="application" else "main_activity")+"_process"]=role
    return result

def run_native(xapk):
    required_environment()
    import ci.owner_2025_lspatch2_namespaced_clone_arm13 as lead
    # Existing native runner imported unchanged; only branch fence is adapted.
    lead.BRANCH=BRANCH
    result={"control_original_case0_in_jvm":"UNKNOWN",
            "own_fatal_suppression_changed":False}
    original_merge=lead.merge_publisher_input_lspatch_clone_splits
    def capture(renamed,editor,work,key):
        single=original_merge(renamed,editor,work,key)
        stock=[p for p in (work/"trusted-source-splits").glob("*.apk")
               if not lead.apk_name(p).get("split","")]
        def classifier(f):
            p=lead.cmd(["aapt","dump","xmltree",str(f),"AndroidManifest.xml"],timeout=45)
            return _manifest(p.stdout) if p.returncode==0 else {"manifest_parse_succeeded":False}
        result["manifest"]={"stock":classifier(stock[0]) if len(stock)==1 else {},
                            "clone":classifier(single)}
        return single
    lead.merge_publisher_input_lspatch_clone_splits=capture
    launch=lead.publisher_control.launch_main
    def clear_then_launch(*args,**kwargs):
        guest("logcat","-c",timeout=12)
        return launch(*args,**kwargs)
    lead.publisher_control.launch_main=clear_then_launch
    def observe(phase,package,real):
        def wrapped(*args,**kwargs):
            sampler=RoleSampler(package);sampler.start()
            try:return real(*args,**kwargs)
            finally:
                result[phase+"_process"]=sampler.finish()
                print("CASE0_ARM_PHASE "+json.dumps(
                    {"phase":phase,"data":result[phase+"_process"]},sort_keys=True),flush=True)
        return wrapped
    lead.publisher_control.observe=observe("stock",ORIGINAL,lead.publisher_control.observe)
    lead.observe_clone=observe("clone",CLONE,lead.observe_clone)
    try:
        baseline=lead.run(xapk)
        sdk=baseline.get("scoped_own_readonly_witness",{})
        result["stock_75s_25of25"]=bool(baseline.get("publisher_stable_75s_before_clone"))
        result["clone_75s_25of25"]=bool(baseline.get("native_clone_main_75s"))
        result["case0_observed_on_clone"]=sdk.get("private_all_exact_guard_case_states",{}).get("CASE_0",{})
        result["case0_readonly_hook_registered"]=sdk.get("private_all_exact_guard_hook_registered",False)
        result["sdk_fatal_category"]=sdk.get("bounded_fatal_metrica_detail_categories",[])
        result["fatal_suppression_count"]=sdk.get("lab_only_metrica_fatal_suppression_count_bounded",None)
        result["original_runner_verdict"]=baseline.get("verdict","UNKNOWN")
        print("CASE0_ARM_RESULT "+json.dumps(result,sort_keys=True),flush=True)
        if not result["stock_75s_25of25"]:return 2
        return 0 if result["clone_75s_25of25"] and result["fatal_suppression_count"]==0 else 1
    except Exception:
        print('CASE0_ARM_ABORT {"category":"UNSPECIFIED_NATIVE_RUNNER_ERROR","original_sdk_changed":false}')
        return 2

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--xapk",required=True,type=Path)
    arg.add_argument("--private-java",type=Path)
    arg.add_argument("--run-native",action="store_true")
    options=arg.parse_args()
    try:
        if options.run_native:
            return run_native(options.xapk)
        inspect(options.xapk,options.private_java)
        return 0
    except Exception as e:
        safe={"HELPER_CI_BRANCH_ISOLATION","VERIFIED_XAPK_SIZE","VERIFIED_XAPK_SHA",
              "CASE0_PRIVATE_HOOK_TARGET_MISSING"}
        label=str(e) if str(e) in safe else "PRIVATE_ANALYSIS_FAILED"
        print("CASE0_HELPER_ABORT "+json.dumps({"reason":label,"stage":STAGE,"error_type":type(e).__name__ if type(e).__name__ in ("DexError","ValueError","KeyError","IndexError","TypeError","AttributeError","FileNotFoundError","OverflowError","RuntimeError","MemoryError","BadZipFile") else "OTHER","private_data_exposed":False}))
        return 2

if __name__=="__main__":
    sys.exit(main())
