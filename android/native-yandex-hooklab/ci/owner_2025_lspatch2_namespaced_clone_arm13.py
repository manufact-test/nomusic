#!/usr/bin/env python3
"""Native ARM13 real A/B: namespaced CELIKOM clone from publisher-input LSPatch2.

Only disposable CI, verified previously uploaded original and our own signer.
No foreign competitor module, no account, no audio and never owner device.
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
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
from clone_main_crash_buffer import classify_main_exit_status, classify_main_crash_buffer
from merge_lab_splits_ephemeral import verify_merged_payloads
from clone_lspatch_loader_zero import verify_native_loader_elf_offsets
from ci.owner_2025_lspatch2_resigned_native_arm13 import wrap_lab_base
from ci.owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest,cmd,stop,verified_orig_paths,apk_name,install_clones,lab_sdk_tool,
    ORIGINAL,SPLITS
)
from ci.owner_2025_same_name_own_key_arm13_control import sign_same_name

BRANCH="experiment/android-a1-2025-singleapk-minimal-package-arm13-20261112"
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
    """Minimal causal control: only the outer manifest root package changes.

    Original manifest authorities, declared permissions, process names and
    component names are left untouched. No original signed Yandex installed in
    this arm: original provider declarations would overlap. NO vendor bytecode
    or original publisher-signed artifacts are changed.
    """
    original=ET.fromstring(data.decode("utf-8"))
    if original.tag!="manifest" or original.attrib.get("package")!=ORIGINAL:
        stop("PACKAGE_ONLY_SOURCE_MANIFEST_IDENTITY_DRIFT")
    if ANDROID+"sharedUserId" in original.attrib:
        stop("PACKAGE_ONLY_SHARED_USER_UNSUPPORTED")
    before=ET.tostring(original,encoding="utf-8",xml_declaration=True)
    original.set("package",DEST)
    updated=ET.tostring(original,encoding="utf-8",xml_declaration=True)
    # Reversing the one allowed root attribute change must recover the
    # original parsed XML exactly, including providers, process and rights.
    original.set("package",ORIGINAL)
    if not updated or ET.tostring(original,encoding="utf-8",xml_declaration=True)!=before:
        stop("PACKAGE_ONLY_MANIFEST_REWRITE_FAILED")
    return updated,{
        "source_scoped_provider_rewrites":0,
        "global_appmetrica_provider_rewrites":0,
        "duplicate_publisher_permission_declarations_removed":0,
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


def merge_publisher_input_lspatch_clone_splits(renamed, editor, work, key):
    """One APK: genuine signed publisher BASE -> LSPatch2 -> clone name -> merge.

    The inner signed issuer-derived origin is preserved byte-for-byte as a
    LSPatch asset. Never modify the genuine publisher original or its signer.
    """
    if len(renamed)!=16 or len({name for name,_ in renamed})!=16:
        stop("SINGLEAPK_2025_EXACT_16_CLONED_SPLITS_REQUIRED")
    merge_dir=work/"single-verified-2025-split-input"
    merge_dir.mkdir()
    base=None
    source_files=[]
    for name,part in renamed:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+",name):
            stop("SINGLEAPK_2025_UNSAFE_SPLIT_NAME")
        meta=apk_name(part)
        split="" if name=="base" else name
        if (meta.get("name")!=DEST or meta.get("versionCode")!=VERSION or
                meta.get("split","")!=split):
            stop("SINGLEAPK_2025_INPUT_METADATA_DRIFT")
        if name=="base":
            base=part
        shutil.copyfile(part,merge_dir/("base.apk" if name=="base" else "split_"+name+".apk"))
        source_files.append(part)
    if base is None:
        stop("SINGLEAPK_2025_CLONE_BASE_ABSENT")
    unsigned=work/"lspatch-2025-single-unsigned.apk"
    built=cmd(["java","-Xmx3g","-jar",str(editor),"m",
               "-i",str(merge_dir),"-o",str(unsigned)],timeout=600)
    if built.returncode or not unsigned.is_file():
        stop("SINGLEAPK_2025_MERGE_FAILED")
    aligned=work/"lspatch-2025-single-owned.apk"
    done=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",
              str(unsigned),str(aligned)],timeout=120)
    if done.returncode:
        stop("SINGLEAPK_2025_ZIPALIGN_FAILED")
    resign_own(aligned,key)
    meta=apk_name(aligned)
    if (meta.get("name")!=DEST or meta.get("versionCode")!=VERSION
            or meta.get("split","")):
        stop("SINGLEAPK_2025_SIGNED_METADATA_DRIFT")
    try:
        parity=verify_merged_payloads(source_files,aligned)
        with zipfile.ZipFile(base) as src,zipfile.ZipFile(aligned) as dst:
            protected=("assets/lspatch/config.json","assets/lspatch/origin.apk",
                       "assets/lspatch/loader.dex")
            if any(member not in dst.namelist() for member in protected):
                stop("SINGLEAPK_2025_LSPATCH_BOOTSTRAP_LOST")
            if any(digest_bytes(src.read(member))!=digest_bytes(dst.read(member))
                   for member in protected):
                stop("SINGLEAPK_2025_NESTED_PUBLISHER_INPUT_DRIFT")
            if dst.testzip() is not None:
                stop("SINGLEAPK_2025_OUTPUT_CRC_INVALID")
        elf=verify_native_loader_elf_offsets(aligned)
        if not all(x["page_aligned_4096"] for x in elf.values()):
            stop("SINGLEAPK_2025_SIGNED_LOADER_ALIGNMENT_INVALID")
    except (ValueError,KeyError,zipfile.BadZipFile,OSError):
        stop("SINGLEAPK_2025_VERIFIED_ASSET_OR_PAYLOAD_DRIFT")
    if not parity["payload_byte_hashes_match"]:
        stop("SINGLEAPK_2025_DEX_NATIVE_PAYLOAD_MISMATCH")
    print(json.dumps({"single_apk_structural":True,
                      "publisher_input_nested_origin_preserved":True,
                      "source_split_count":16,"output_count":1,
                      "dex_count":parity["single_apk_payload_dex_count"],
                      "native_lib_count":parity["single_apk_payload_native_library_count"],
                      "all_signed_loader_abis_page_aligned":True,
                      "consumer_release":False},sort_keys=True))
    return aligned


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
    stable=bool(accepted and all(pids) and len(set(pids))==1 and resumed==len(pids))
    summary={"stable":stable,"resumed_observations":resumed,
             "observed_samples":len(pids)}
    if not stable:
        exit_info=guest("dumpsys","activity","exit-info",DEST,timeout=45)
        if exit_info.returncode==0:
            summary["exit"]=classify_main_exit_status(exit_info.stdout,target_package=DEST)
            crash=guest("logcat","-d","-b","crash",timeout=50)
            if crash.returncode==0:
                raw=classify_main_crash_buffer(exit_info.stdout,crash.stdout,
                                                target_package=DEST)
                summary["crash"]={
                    "fatal_category":raw["fatal_category"],
                    "java_top_exception_enum":raw["java_top_exception_enum"],
                    "java_exception_security_markers":raw["java_exception_security_markers"],
                    "java_top_stack_family":raw["java_top_stack_family"],
                    "application_component_factory_failure":raw["application_component_factory_failure"],
                }
    return summary


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
        rewrite_summary={"total_source_scoped_providers":0,
                         "total_global_provider_rewrites":0,
                         "total_duplicate_permissions_removed":0}
        source_splits={name for name,_ in independent}
        if len(source_splits)!=16:
            stop("NAMESPACED_EXPECTED_SIXTEEN_SIGNED_SPLITS")
        for index,(name,part) in enumerate(independent):
            input_apk=loader if name=="base" else part
            signed,stats=name_one(input_apk,editor,work,index,
                                   work/"unique-own-key.jks")
            renamed.append((name,signed))
            rewrite_summary["total_source_scoped_providers"]+=stats["source_scoped_provider_rewrites"]
            rewrite_summary["total_global_provider_rewrites"]+=stats["global_appmetrica_provider_rewrites"]
            rewrite_summary["total_duplicate_permissions_removed"]+=stats["duplicate_publisher_permission_declarations_removed"]
        single=merge_publisher_input_lspatch_clone_splits(
            renamed,editor,work,work/"unique-own-key.jks")
        report={
            "verified_publisher_source_splits":16,
            "clone_provider_namespace_rewrites":rewrite_summary,
            "own_signed_cloned_splits":len(renamed),
            "LSPatch_level":2,
            "LSPatch_direct_input_publisher_verified":True,
            "signed_clone_package":DEST,
            "single_apk_achieved":True,
            "package_root_only_manifest_change":True,
            "original_absent_for_exact_authority_control":True,
            "publisher_app_and_clone_can_be_concurrently_installed":False,
            "native_clone_main_75s":False,
            "audio_or_account_tested":False,
            "owner_phone_touched":False,
            "binary_published":False,
            "stage_a":"NO_GO",
        }
        report["clone_install"]=install_clones([("base",single)])
        if report["clone_install"]!="INSTALLED":
            report["verdict"]="NAMESPACED_CLONE_INSTALL_FAIL"
            return report
        count=sum(line.startswith("package:") for line in
                  guest("pm","path",DEST).stdout.splitlines())
        if count!=1:
            report["verdict"]="NAMESPACED_CLONE_SPLIT_COUNT_FAIL"
            return report
        guest("logcat","-c")
        observed=observe_clone()
        report["native_clone_main_75s"]=observed["stable"]
        report["clone_lifecycle"]=observed
        # Clone-only causal arm. Installing stock Yandex here would collide
        # with the deliberately preserved original global authority set.
        report["publisher_original_absent_after_clone"]=not bool(
            guest("pm","path",ORIGINAL).stdout.strip())
        report["publisher_app_and_clone_can_be_concurrently_installed"]=False
        report["verdict"]=(
            "PACKAGE_ONLY_CLONE_MAIN_75S_PASS_NO_COEXIST"
            if report["native_clone_main_75s"] and
               report["publisher_original_absent_after_clone"]
            else "PACKAGE_ONLY_CLONE_NATIVE_MAIN_NO_GO")
        return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        result=run(args.xapk)
        print(json.dumps(result,sort_keys=True))
        sys.exit(0 if result["verdict"]=="PACKAGE_ONLY_CLONE_MAIN_75S_PASS_NO_COEXIST" else 1)
    except Exception as e:
        code=str(e)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",code):
            code="NAMESPACED_PRIVATE_DISPOSABLE_ERROR"
        print(json.dumps({"verdict":"NAMESPACED_LSPATCH2_EXPERIMENT_ABORTED",
            "reason":code,"owner_phone_touched":False,"stage_a":"NO_GO",
            "vendor_apk_published":False},sort_keys=True))
        sys.exit(2)
