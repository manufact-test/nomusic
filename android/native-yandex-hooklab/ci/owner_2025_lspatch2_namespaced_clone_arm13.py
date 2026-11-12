#!/usr/bin/env python3
"""Native ARM13 real A/B: namespaced CELIKOM clone from publisher-input LSPatch2.

Only disposable CI, verified previously uploaded original and our own signer.
No foreign competitor module, no account, no audio and never owner device.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import clone_native_splits_ephemeral as source
from clone_native_splits_arsclib_ephemeral import download_editor
from ci.owner_2025_lspatch2_resigned_native_arm13 import wrap_lab_base
from ci.owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest,cmd,stop,verified_orig_paths,apk_name,install_clones,lab_sdk_tool,
    ORIGINAL,SPLITS
)
from ci.owner_2025_same_name_own_key_arm13_control import sign_same_name

BRANCH="experiment/android-a1-2025-native-lspatch2-clone-namespace-20261112"
DEST=source.DEST
VERSION="24025542"
ANDROID="{http://schemas.android.com/apk/res/android}"
KNOWN_SIGNATURE_PERMISSIONS={
    "com.yandex.permission.READ_CREDENTIALS",
    "com.yandex.music.RELAY_PERMISSION",
}
# Globally unique in this clone; original Yandex remains the owner of its
# original provider and signature-protected permission declarations.
GLOBAL_PROVIDER="com.yandex.preinstallsatellite.appmetrica.provider"


def require_guest():
    if (os.getenv("GITHUB_ACTIONS")!="true"
        or os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic"
        or os.getenv("GITHUB_REF_NAME")!=BRANCH
        or os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1"
        or platform.machine()!="aarch64"):
        stop("NAMESPACED_LSPATCH2_DISPOSABLE_ARM13_ONLY")
    if (guest("getprop","ro.build.version.sdk").stdout.strip()!="33"
        or guest("getprop","sys.boot_completed").stdout.strip()!="1"
        or guest("pm","path",ORIGINAL).stdout.strip()
        or guest("pm","path",DEST).stdout.strip()):
        stop("NAMESPACED_LSPATCH2_FRESH_ANDROID13_REQUIRED")


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def patch_manifest(data):
    raw,stats=source.rewrite_manifest(data.decode("utf-8"))
    root=ET.fromstring(raw)
    permissions_removed=0
    providers_rewritten=0
    for entry in list(root):
        if entry.tag=="permission":
            name=entry.attrib.get(ANDROID+"name","")
            if name in KNOWN_SIGNATURE_PERMISSIONS:
                # Do not shadow the publisher's system signature permission.
                if entry.attrib.get(ANDROID+"protectionLevel")!="signature":
                    stop("NAMESPACED_CLONE_PERMISSION_PROTECTION_DRIFT")
                root.remove(entry)
                permissions_removed+=1
    for provider in root.iter("provider"):
        auth=provider.attrib.get(ANDROID+"authorities","")
        if not auth: continue
        values=auth.split(";")
        updated=[DEST+".thirdparty.appmetrica.provider"
                 if value==GLOBAL_PROVIDER else value for value in values]
        if updated!=values:
            providers_rewritten+=1
            provider.set(ANDROID+"authorities",";".join(updated))
    return ET.tostring(root,encoding="utf-8",xml_declaration=True),{
        "source_scoped_provider_rewrites":stats["provider_authorities"],
        "global_appmetrica_provider_rewrites":providers_rewritten,
        "duplicate_publisher_permission_declarations_removed":permissions_removed,
    }


def resign_own(apk, keystore):
    done=cmd([lab_sdk_tool("apksigner"),"sign",
              "--ks",str(keystore),"--ks-pass","pass:ephemeral-lab-only",
              "--ks-key-alias","own-key","--key-pass","pass:ephemeral-lab-only",
              "--min-sdk-version","24","--v4-signing-enabled","false",
              str(apk)],timeout=130)
    if done.returncode:
        stop("NAMESPACED_OWN_SIGNATURE_FAILED")
    checked=cmd([lab_sdk_tool("apksigner"),"verify","--verbose",
                 "--min-sdk-version","24",str(apk)],timeout=100)
    if checked.returncode:
        stop("NAMESPACED_OWN_APK_VERIFY_FAILED")


def name_one(apk,editor,root,index,keystore):
    decoded=root/("clone-manifest-"+str(index))
    out=cmd(["java","-Xmx3g","-jar",str(editor),"d","-t","xml","-dex",
             "-i",str(apk),"-o",str(decoded)],timeout=330)
    if out.returncode:
        stop("NAMESPACED_APKEDITOR_DECODE_FAILED")
    manifest=decoded/"AndroidManifest.xml"
    if not manifest.is_file():
        stop("NAMESPACED_DECODED_MANIFEST_ABSENT")
    payload=manifest.read_bytes()
    if not payload.lstrip().startswith(b"<"):
        stop("NAMESPACED_DECODED_MANIFEST_NOT_XML")
    changed,stats=patch_manifest(payload)
    manifest.write_bytes(changed)
    output=root/("clone-rebuilt-"+str(index)+".apk")
    built=cmd(["java","-Xmx3g","-jar",str(editor),"b","-t","xml",
               "-i",str(decoded),"-o",str(output)],timeout=340)
    if built.returncode or not output.is_file():
        stop("NAMESPACED_APKEDITOR_REBUILD_FAILED")
    aligned=root/("clone-aligned-"+str(index)+".apk")
    a=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",str(output),str(aligned)],timeout=120)
    if a.returncode:
        stop("NAMESPACED_APK_ALIGNMENT_FAILED")
    resign_own(aligned,keystore)
    meta=apk_name(aligned)
    original=apk_name(apk)
    if meta.get("name")!=DEST or meta.get("versionCode")!=VERSION or \
       meta.get("split","")!=original.get("split",""):
        stop("NAMESPACED_SIGNED_CLONE_PACKAGE_OR_SPLIT_DRIFT")
    with zipfile.ZipFile(apk) as old,zipfile.ZipFile(aligned) as new:
        if new.testzip() is not None:
            stop("NAMESPACED_REBUILT_ZIP_CRC_INVALID")
        protected=[e for e in old.namelist() if
                   e.startswith("assets/lspatch/") and
                   (e=="assets/lspatch/origin.apk" or
                    e.endswith(".dex") or e.endswith("liblspatch.so"))]
        for name in protected:
            if name not in new.namelist() or digest_bytes(old.read(name))!=digest_bytes(new.read(name)):
                stop("NAMESPACED_LSPATCH_NESTED_ORIGIN_OR_LOADER_CHANGED")
        if source.native_payload_hashes(apk)!=source.native_payload_hashes(aligned):
            stop("NAMESPACED_DEX_OR_NATIVE_LIB_CHANGED")
    return aligned,stats


def observe_clone(seconds=75):
    component=DEST+"/ru.yandex.music.main.MainScreenActivity"
    launched=guest("am","start","--user","0","-n",component,timeout=65)
    accepted=launched.returncode==0 and ("Starting:" in launched.stdout or
                     "Warning: Activity not started" in launched.stdout)
    pids=[]
    resumed=0
    for _ in range(seconds//3):
        time.sleep(3)
        ps=guest("pidof",DEST)
        pid=ps.stdout.strip()
        pids.append(pid if re.fullmatch(r"\d+",pid) else None)
        activities=guest("dumpsys","activity","activities")
        resumed+=int(any(DEST+"/" in line and
            ("mResumedActivity" in line or "topResumedActivity" in line)
            for line in activities.stdout.splitlines()))
    return accepted and all(pids) and len(set(pids))==1 and resumed==len(pids)


def run(xapk):
    require_guest()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-namespaced-lspatch2-") as tmp:
        work=Path(tmp)
        originals=verified_orig_paths(xapk,work)
        independent,signer=sign_same_name(originals,work)
        publisher_base=[p for p in originals if not apk_name(p).get("split","")]
        own_base=[p for name,p in independent if name=="base"]
        if len(publisher_base)!=1 or len(own_base)!=1:
            stop("NAMESPACED_2025_BASE_SPLIT_SET_INCOMPLETE")
        # The key causal result: keep actual publisher-signed source as input,
        # never feed already own-signed original to the LSPatch compatibility loader.
        loader=wrap_lab_base(publisher_base[0],work,own_base[0])
        editor=work/"pinned-owned-manifest-editor.jar"
        download_editor(editor)
        renamed=[]
        source_splits={name for name,_ in independent}
        if len(source_splits)!=16:
            stop("NAMESPACED_EXPECTED_SIXTEEN_SIGNED_SPLITS")
        for index,(name,part) in enumerate(independent):
            input_apk=loader if name=="base" else part
            signed,stats=name_one(input_apk,editor,work,index,
                                   work/"unique-own-key.jks")
            renamed.append((name,signed))
        report={
            "verified_publisher_source_splits":16,
            "own_signed_cloned_splits":len(renamed),
            "LSPatch_level":2,
            "LSPatch_direct_input_publisher_verified":True,
            "signed_clone_package":DEST,
            "single_apk_achieved":False,
            "publisher_app_and_clone_can_be_concurrently_installed":False,
            "native_clone_main_75s":False,
            "audio_or_account_tested":False,
            "owner_phone_touched":False,
            "binary_published":False,
            "stage_a":"NO_GO",
        }
        report["clone_install"]=install_clones(renamed)
        if report["clone_install"]!="INSTALLED":
            report["verdict"]="NAMESPACED_CLONE_INSTALL_FAIL"
            return report
        count=sum(line.startswith("package:") for line in
                  guest("pm","path",DEST).stdout.splitlines())
        if count!=16:
            report["verdict"]="NAMESPACED_CLONE_SPLIT_COUNT_FAIL"
            return report
        guest("logcat","-c")
        report["native_clone_main_75s"]=observe_clone()
        # Independently verified exact publisher originals installed without
        # modifying any original bytes or removing our cloned package.
        report["publisher_install"]=install_clones(
            [(apk_name(p).get("split","") or "base",p) for p in originals])
        report["publisher_app_and_clone_can_be_concurrently_installed"]=(
            report["publisher_install"]=="INSTALLED")
        report["verdict"]=(
            "NAMESPACED_LSPATCH2_NATIVE_AND_COEXIST_PASS_NOT_AUDIO"
            if report["native_clone_main_75s"] and
               report["publisher_app_and_clone_can_be_concurrently_installed"]
            else "NAMESPACED_LSPATCH2_NATIVE_OR_COEXIST_NO_GO")
        return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        result=run(args.xapk)
        print(json.dumps(result,sort_keys=True))
        sys.exit(0 if result["verdict"]=="NAMESPACED_LSPATCH2_NATIVE_AND_COEXIST_PASS_NOT_AUDIO" else 1)
    except Exception as e:
        code=str(e)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",code):
            code="NAMESPACED_PRIVATE_DISPOSABLE_ERROR"
        print(json.dumps({"verdict":"NAMESPACED_LSPATCH2_EXPERIMENT_ABORTED",
            "reason":code,"owner_phone_touched":False,"stage_a":"NO_GO",
            "vendor_apk_published":False},sort_keys=True))
        sys.exit(2)
