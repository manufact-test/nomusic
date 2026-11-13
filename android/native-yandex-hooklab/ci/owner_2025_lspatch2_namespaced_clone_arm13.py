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
from ci.a1_metrica_witness_private_parser import scoped_metrica_witness
from ci.a1_metrica_service_snapshot import classify_metrica_service_snapshot
from merge_lab_splits_ephemeral import verify_merged_payloads
from clone_lspatch_loader_zero import verify_native_loader_elf_offsets
from ci.owner_2025_lspatch2_resigned_native_arm13 import wrap_lab_base
from ci.owner_2025_gpr_lab_clone_no_bypass_arm13 import (
    guest,cmd,stop,verified_orig_paths,apk_name,install_clones,lab_sdk_tool,
    ORIGINAL,SPLITS
)
from ci.owner_2025_same_name_own_key_arm13_control import sign_same_name
from ci.a1_resource_package_rename import (
    rewrite_exact_namespace,package_names,InvalidResourceTable,
    classify_outer_signing_change,only_expected_own_v1_signing_changes
)
from ci.a1_passport_sync_exact import rewrite_exact_sync_authority, PassportResourceMismatch
import ci.owner_2025_gpr_arm13_signed_control as publisher_control
from owner_phone_diagnostic_artifact import export_after_native_acceptance

# Scoped native verification: exact signing helper is now restored, no payload allowlist broadened.
BRANCH="experiment/android-a1-metrica-init-state-observer-arm13-20261112"
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



def _outer_signer_cert_sha256(apk):
    """Verify exactly one APK signer and return its SHA-256, without logging."""
    result=cmd([lab_sdk_tool("apksigner"),"verify","--verbose",
                "--print-certs","--min-sdk-version","24",str(apk)],timeout=100)
    if result.returncode:
        stop("NAMESPACE_OWN_SIGNING_CERT_VERIFY_FAILED")
    fingerprints=re.findall(
        r"(?im)^\s*Signer #1 certificate SHA-256 digest:\s*([0-9a-f]{64})\s*$",
        result.stdout or "")
    if len(fingerprints)!=1:
        stop("NAMESPACE_OWN_SIGNING_CERT_UNIQUE_FAILED")
    return fingerprints[0].lower()


def _firebase_resource_table_parity(original_apk,clone_apk):
    """Name/package only from aapt resource table; no values leave CI."""
    def scan(apk):
        result=cmd(["aapt","dump","resources",str(apk)],timeout=120)
        if result.returncode!=0 or not result.stdout:
            return {"pair":"UNKNOWN","namespace":"UNKNOWN"}
        raw=result.stdout
        names=("google_app_id","gcm_defaultSenderId")
        has=[bool(re.search(r"(?:^|[\\s:])string/"+re.escape(name)+
                             r"(?=[:\\s])",raw,re.MULTILINE))
             for name in names]
        pair="BOTH" if all(has) else "PARTIAL" if any(has) else "NONE"
        packages=set(re.findall(r"(?m)^\\s*Package(?: Group)?\\s+\\d+[^\\n]*?\\bname=([^\\s]+)",raw))
        own=DEST in packages
        stock=ORIGINAL in packages
        namespace=("BOTH_NAMES" if own and stock else "CLONE_ONLY"
                   if own else "ORIGINAL_ONLY" if stock else
                   "UNKNOWN" if not packages else "OTHER")
        return {"pair":pair,"namespace":namespace}
    stock=scan(original_apk)
    clone=scan(clone_apk)
    return {"publisher_resource_names":stock["pair"],
            "clone_resource_names":clone["pair"],
            "publisher_table_namespace":stock["namespace"],
            "clone_table_namespace":clone["namespace"],
            "source_strings_or_values_logged":False,
            "original_or_clone_apk_modified_by_audit":False}


def _rename_only_owned_outer_resource_package(single, work, key):
    """One opt-in A/B: rewrite one outer ARSC package-name field only.

    All other ZIP member payloads must match, including the byte-identical
    nested publisher original and LSPatch loader. Do not touch publisher XAPK.
    """
    unsigned=work/"celikom-namespace-only-unsigned.apk"
    aligned=work/"celikom-namespace-only-aligned.apk"
    try:
        with zipfile.ZipFile(single,"r") as old:
            entries=old.infolist()
            if len(entries)!=len({info.filename for info in entries}):
                stop("NAMESPACE_DUPLICATE_ZIP_ENTRIES")
            if "resources.arsc" not in {info.filename for info in entries}:
                stop("NAMESPACE_OUTER_RESOURCE_TABLE_ABSENT")
            before=old.read("resources.arsc")
            source_names=package_names(before)
            if source_names.count(ORIGINAL)!=1 or DEST in source_names:
                stop("NAMESPACE_RESOURCE_PACKAGE_NOT_EXACT_SOURCE")
            after=rewrite_exact_namespace(before,ORIGINAL,DEST)
            if tuple(x for x in package_names(after) if x!=DEST) != tuple(
                x for x in source_names if x!=ORIGINAL):
                stop("NAMESPACE_NON_SOURCE_RESOURCE_PACKAGE_CHANGED")
            with zipfile.ZipFile(unsigned,"w",allowZip64=True) as new:
                new.comment=old.comment
                for info in entries:
                    # Copy every other entry unmodified, including actual
                    # nested signed original, code, libs, keys and assets.
                    member=(after if info.filename=="resources.arsc"
                            else old.read(info.filename))
                    new.writestr(info,member)
        done=cmd([lab_sdk_tool("zipalign"),"-f","-p","4",
                  str(unsigned),str(aligned)],timeout=120)
        if done.returncode:
            stop("NAMESPACE_PATCH_ZIPALIGN_FAILED")
        resign_own(aligned,key)
        if apk_name(aligned).get("name")!=DEST:
            stop("NAMESPACE_PATCH_APK_IDENTITY_DRIFT")
        changed_names=[]
        diff_counts={label:0 for label in (
            "V1_MANIFEST","V1_SIGNATURE_FILE","V1_SIGNATURE_BLOCK",
            "OTHER_META_INF","NON_META_INF_APP_CONTENT")}
        # Both independently signed ZIPs must have an identical member set,
        # order and contents, except exact ARSC bytes and *three* outer
        # signing metadata members determined by the prior A/B native audit.
        with zipfile.ZipFile(single) as old,zipfile.ZipFile(aligned) as new:
            if old.namelist()!=new.namelist() or new.testzip() is not None:
                stop("NAMESPACE_PATCH_ZIP_STRUCTURE_DRIFT")
            for name in old.namelist():
                if name=="resources.arsc":
                    if new.read(name)!=after:
                        stop("NAMESPACE_PATCH_ARSCTABLE_DRIFT")
                elif digest_bytes(old.read(name))!=digest_bytes(new.read(name)):
                    changed_names.append(name)
                    diff_counts[classify_outer_signing_change(name)]+=1
        if not only_expected_own_v1_signing_changes(changed_names):
            print("NAMESPACE_OUTER_DIFF_REJECTED "+json.dumps({
                "changed_member_types":diff_counts,
                "member_names_or_payloads_logged":False,
                "vendor_content_exempted":False},sort_keys=True),flush=True)
            stop("NAMESPACE_PATCH_NON_RESOURCE_PAYLOAD_CHANGED")
        # The prepatch and postpatch outer APK must BOTH cryptographically
        # verify with the EXACT SAME independently generated CELIKOM signer.
        # This is never the embedded publisher signature or signing key.
        if _outer_signer_cert_sha256(single)!=_outer_signer_cert_sha256(aligned):
            stop("NAMESPACE_PATCH_OWN_SIGNING_CERT_CHANGED")
        own_signing_entries_updated=len(changed_names)
        print("NAMESPACE_SIGNER_DIFF_CONFIRMED "+json.dumps({
            "modified_signer_members":own_signing_entries_updated,
            "modified_app_members":0,
            "same_own_signing_certificate":True,
            "member_names_or_payloads_logged":False},sort_keys=True),flush=True)
        aligned_elf=verify_native_loader_elf_offsets(aligned)
        if not all(row["page_aligned_4096"] for row in aligned_elf.values()):
            stop("NAMESPACE_PATCH_NATIVE_LOADER_ALIGNMENT_INVALID")
    except (OSError,ValueError,InvalidResourceTable,zipfile.BadZipFile):
        stop("NAMESPACE_PATCH_VERIFIED_RESOURCE_FAILED")
    return aligned, min(own_signing_entries_updated,16)



def _repair_only_owned_passport_sync(single, work, key):
    """One verified clone-only resource-string fix; no Passport code or auth bypass."""
    unsigned=work/"passport-sync-own-unsigned.apk"
    aligned=work/"passport-sync-own-aligned.apk"
    try:
        with zipfile.ZipFile(single) as old:
            entries=old.infolist()
            if len(entries)!=len({info.filename for info in entries}):
                stop("PASSPORT_PATCH_DUPLICATE_ZIP_ENTRIES")
            before=old.read("resources.arsc")
            after=rewrite_exact_sync_authority(before,ORIGINAL,DEST)
            with zipfile.ZipFile(unsigned,"w",allowZip64=True) as out:
                out.comment=old.comment
                for info in entries:
                    out.writestr(info,after if info.filename=="resources.arsc"
                                 else old.read(info.filename))
        if cmd([lab_sdk_tool("zipalign"),"-f","-p","4",
                str(unsigned),str(aligned)],timeout=120).returncode:
            stop("PASSPORT_PATCH_ZIPALIGN_FAILED")
        resign_own(aligned,key)
        changed=[]
        with zipfile.ZipFile(single) as old,zipfile.ZipFile(aligned) as new:
            if old.namelist()!=new.namelist() or new.testzip() is not None:
                stop("PASSPORT_PATCH_ZIP_STRUCTURE_DRIFT")
            for name in old.namelist():
                if name=="resources.arsc":
                    if new.read(name)!=after:
                        stop("PASSPORT_PATCH_RESOURCE_DRIFT")
                elif digest_bytes(old.read(name))!=digest_bytes(new.read(name)):
                    changed.append(name)
        if not only_expected_own_v1_signing_changes(changed):
            stop("PASSPORT_PATCH_NON_RESOURCE_PAYLOAD_CHANGED")
        if _outer_signer_cert_sha256(single)!=_outer_signer_cert_sha256(aligned):
            stop("PASSPORT_PATCH_OWN_CERT_CHANGED")
        if apk_name(aligned).get("name")!=DEST:
            stop("PASSPORT_PATCH_APP_ID_CHANGED")
        elf=verify_native_loader_elf_offsets(aligned)
        if not all(x["page_aligned_4096"] for x in elf.values()):
            stop("PASSPORT_PATCH_NATIVE_ALIGNMENT_CHANGED")
        # The signed embedded publisher input is preserved byte-for-byte.
        with zipfile.ZipFile(single) as old,zipfile.ZipFile(aligned) as new:
            if old.read("assets/lspatch/origin.apk")!=new.read("assets/lspatch/origin.apk"):
                stop("PASSPORT_PATCH_INNER_ORIGIN_CHANGED")
    except (OSError,ValueError,PassportResourceMismatch,zipfile.BadZipFile):
        stop("PASSPORT_PATCH_VERIFICATION_FAILED")
    print("PASSPORT_SYNC_OWN_RESOURCE_PARITY_OK",flush=True)
    return aligned


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
        # This provider's authority is a resource reference, not an independent
        # literal. Keep the reference; the own-outer clone string is updated
        # separately and must equal the Android SyncAdapter authority.
        if provider.attrib.get(ANDROID+"name","").endswith(".core.sync.SyncProvider"):
            if not auth.startswith("@"):
                stop("PASSPORT_SYNC_PROVIDER_RESOURCE_REFERENCE_REQUIRED")
            continue
        values=auth.split(";")
        # ALL provider authorities must be globally unique for Android
        # PackageManager to install the CELIKOM clone next to publisher Yandex.
        # Original Yandex retained every authority; never mutate it.
        updated=[value if value.startswith(DEST+".") else
                 DEST+".provider."+hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
                 for value in values]
        if updated!=values:
            providers_rewritten+=sum(a!=b for a,b in zip(values,updated))
            provider.set(ANDROID+"authorities",";".join(updated))
    return ET.tostring(root,encoding="utf-8",xml_declaration=True),{
        "source_scoped_provider_rewrites":stats["provider_authorities"],
        "global_appmetrica_provider_rewrites":providers_rewritten,
        "duplicate_publisher_permission_declarations_removed":permissions_removed,
        "optional_metrica_components_excluded":0,
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
                    "java_fatal_background_role":raw["java_fatal_background_role"],
                    "java_top_frame_subsystem":raw["java_top_frame_subsystem"],
                    "java_startup_message_shape":raw["java_startup_message_shape"],
                    "java_startup_message_finite_hint":raw["java_startup_message_finite_hint"],
                    "java_exception_message_hint_enum":raw["java_exception_message_hint_enum"],
                }
    return summary


def _finite_service_snapshot(package):
    ps=guest("ps","-A",timeout=35)
    services=guest("dumpsys","activity","services",package,timeout=45)
    return classify_metrica_service_snapshot(
        ps.stdout,services.stdout,package,
        ps_ok=ps.returncode==0,services_ok=services.returncode==0)


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
        own_witness=Path(os.getenv("CELIKOM_A1_METRICA_OWN_MODULE_PATH","")).resolve()
        runner=Path(os.getenv("RUNNER_TEMP","/nonexistent")).resolve()
        if (not own_witness.is_file() or own_witness.is_symlink() or
                runner not in own_witness.parents):
            stop("METRICA_WITNESS_EPHEMERAL_OWN_MODULE_REQUIRED")
        loader=wrap_lab_base(publisher_base[0],work,own_base[0],
                             witness_module=own_witness)
        editor=work/"pinned-owned-manifest-editor.jar"
        download_editor(editor)
        renamed=[]
        rewrite_summary={"total_source_scoped_providers":0,
                         "total_global_provider_rewrites":0,
                         "total_duplicate_permissions_removed":0,
                         "total_optional_metrica_components_excluded":0}
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
            rewrite_summary["total_optional_metrica_components_excluded"]+=stats["optional_metrica_components_excluded"]
        if rewrite_summary["total_optional_metrica_components_excluded"] != 0:
            stop("METRICA_DETAIL_ORIGINAL_COMPONENTS_NOT_PRESERVED")
        single=merge_publisher_input_lspatch_clone_splits(
            renamed,editor,work,work/"unique-own-key.jks")
        firebase_resource_parity=_firebase_resource_table_parity(publisher_base[0],single)
        namespace_trial=os.getenv("CELIKOM_A1_RESOURCE_NAMESPACE_TRIAL")=="1"
        own_signing_entries_updated=0
        if namespace_trial:
            single,own_signing_entries_updated=_rename_only_owned_outer_resource_package(
                single,work,work/"unique-own-key.jks")
        passport_trial=os.getenv("CELIKOM_A1_PASSPORT_SYNC_TRIAL")=="1"
        if passport_trial:
            single=_repair_only_owned_passport_sync(single,work,work/"unique-own-key.jks")
        firebase_resource_after=_firebase_resource_table_parity(publisher_base[0],single)
        with zipfile.ZipFile(single) as packaged:
            own_modules=[name for name in packaged.namelist()
                         if name.startswith("assets/lspatch/modules/") and name.endswith(".apk")]
            if len(own_modules)!=1 or packaged.read(own_modules[0])!=own_witness.read_bytes():
                stop("METRICA_WITNESS_SINGLE_APK_MODULE_LOST")
        report={
            "verified_publisher_source_splits":16,
            "firebase_resource_table_parity":firebase_resource_parity,
            "firebase_resource_table_after":firebase_resource_after,
            "resource_namespace_trial_only":namespace_trial,
            "passport_sync_config_trial_only":passport_trial,
            "own_signature_metadata_entries_regenerated_bounded":own_signing_entries_updated,
            "clone_provider_namespace_rewrites":rewrite_summary,
            "own_signed_cloned_splits":len(renamed),
            "LSPatch_level":2,
            "LSPatch_direct_input_publisher_verified":True,
            "signed_clone_package":DEST,
            "single_apk_achieved":True,
            "preserves_publisher_metrica_manifest_components_in_clone":True,
            "readonly_no_metrica_fatal_suppression":True,
            "diagnostic_only_not_product_or_releasable":True,
            "own_readonly_witness_module_embedded":True,
            "test_order":"PUBLISHER_FIRST_CLONE_SECOND",
            "publisher_app_and_clone_can_be_concurrently_installed":False,
            "native_clone_main_75s":False,
            "audio_or_account_tested":False,
            "owner_phone_touched":False,
            "binary_published":False,
            "stage_a":"NO_GO",
        }
        # ONE strictly isolated differential: without the publisher installed,
        # does the exact same independently signed clone still crash?
        # This is *not* a product acceptance path. Default remains untouched.
        if os.getenv("CELIKOM_A1_CLONE_ONLY_CONTROL")=="1":
            report["control"]="CLONE_ALONE_FRESH_ANDROID13"
            report["publisher_intentionally_absent"]=not bool(
                guest("pm","path",ORIGINAL).stdout.strip())
            if not report["publisher_intentionally_absent"]:
                stop("CLONE_ONLY_ORIGINAL_PRESENT")
            report["clone_install"]=install_clones([("base",single)])
            if report["clone_install"]!="INSTALLED":
                report["verdict"]="CLONE_ONLY_INSTALL_NO_GO"
                return report
            report["original_splits_installed_before_clone"]=0
            report["single_clone_installed_after_original"]=False
            guest("logcat","-c")
            observed=observe_clone()
            report["clone_lifecycle"]=observed
            report["native_clone_main_75s"]=observed["stable"]
            report["clone_metrica_service_snapshot"]=_finite_service_snapshot(DEST)
            stable_pid=None
            if observed["stable"]:
                live=guest("pidof",DEST,timeout=30).stdout.strip()
                if re.fullmatch(r"[1-9][0-9]{0,8}",live):
                    stable_pid=live
            report["scoped_own_readonly_witness"]=scoped_metrica_witness(
                guest("dumpsys","activity","exit-info",DEST,timeout=45).stdout,
                guest("logcat","-v","threadtime","-d",timeout=55).stdout,
                stable_live_main_pid=stable_pid)
            report["verdict"]=(
                "CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS"
                if observed["stable"] else "CLONE_ONLY_NATIVE_MAIN_NO_GO")
            # No change to any original-first acceptance verdict.
            report["stage_a"]="NO_GO"
            return report
        # Actual owner condition: original publisher app already installed
        # BEFORE CELIKOM is installed. Earlier native test did the reverse.
        publisher_parts = [(apk_name(p).get("split","") or "base", p)
                           for p in originals]
        report["publisher_install"] = install_clones(publisher_parts)
        report["original_splits_installed_before_clone"] = sum(
            row.startswith("package:") for row in
            guest("pm","path",ORIGINAL).stdout.splitlines())
        if (report["publisher_install"] != "INSTALLED" or
                report["original_splits_installed_before_clone"] != 16):
            report["verdict"] = "ORIGINAL_FIRST_PUBLISHER_INSTALL_NO_GO"
            return report
        source_launch = publisher_control.launch_main()
        report["publisher_launch_status"] = source_launch["launch_status"]
        if report["publisher_launch_status"] != "NATIVE_MAIN_ACTIVITY_ACCEPTED":
            report["verdict"] = "ORIGINAL_FIRST_PUBLISHER_START_NO_GO"
            return report
        source_seen = publisher_control.observe()
        report["publisher_stable_75s_before_clone"] = bool(
            source_seen["same_exact_main_pid_all_samples"] and
            source_seen["resumed_activity_samples"] == 25 and
            source_seen["sample_count"] == 25)
        if not report["publisher_stable_75s_before_clone"]:
            report["verdict"] = "ORIGINAL_FIRST_PUBLISHER_NATIVE_GATE_NO_GO"
            return report
        report["publisher_metrica_service_snapshot"]=_finite_service_snapshot(ORIGINAL)
        # Never uninstall or change the real publisher package.
        report["clone_install"] = install_clones([("base", single)])
        report["single_clone_installed_after_original"] = sum(
            row.startswith("package:") for row in
            guest("pm","path",DEST).stdout.splitlines()) == 1
        report["publisher_app_and_clone_can_be_concurrently_installed"] = bool(
            report["clone_install"] == "INSTALLED" and
            report["single_clone_installed_after_original"] and
            sum(row.startswith("package:") for row in
                guest("pm","path",ORIGINAL).stdout.splitlines()) == 16)
        if not report["publisher_app_and_clone_can_be_concurrently_installed"]:
            report["verdict"] = "ORIGINAL_FIRST_SIDE_BY_SIDE_INSTALL_NO_GO"
            return report
        guest("logcat","-c")
        observed = observe_clone()
        report["native_clone_main_75s"] = observed["stable"]
        report["clone_lifecycle"] = observed
        report["clone_metrica_service_snapshot"]=_finite_service_snapshot(DEST)
        # A stable foreground MAIN has *no* exit-info record. Only admit its
        # current exact native pidof if the prior 25/25 lifecycle gate passed.
        stable_pid=None
        if observed["stable"] and report["single_clone_installed_after_original"]:
            live=guest("pidof",DEST,timeout=30).stdout.strip()
            if re.fullmatch(r"[1-9][0-9]{0,8}",live):
                stable_pid=live
        report["scoped_own_readonly_witness"]=scoped_metrica_witness(
            guest("dumpsys","activity","exit-info",DEST,timeout=45).stdout,
            guest("logcat","-v","threadtime","-d",timeout=55).stdout,
            stable_live_main_pid=stable_pid)
        report["publisher_still_installed_after_clone_start"] = sum(
            row.startswith("package:") for row in
            guest("pm","path",ORIGINAL).stdout.splitlines()) == 16
        report["verdict"] = (
            "METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO"
            if report["native_clone_main_75s"] and
               report["publisher_still_installed_after_clone_start"] and
               report["scoped_own_readonly_witness"]["read_only_witness_arm_marker_seen"] and
               not report["scoped_own_readonly_witness"]["lab_only_metrica_fatal_suppression_observed"]
            else "METRICA_READONLY_NATIVE_MAIN_NO_GO")
        if os.getenv("CELIKOM_A1_EXPORT_DIAGNOSTIC_APK") == "1":
            report["owner_phone_diagnostic_artifact"] = export_after_native_acceptance(
                single, report, os.environ["RUNNER_TEMP"])
        return report


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--xapk",type=Path,required=True)
    args=p.parse_args()
    try:
        result=run(args.xapk)
        print(json.dumps(result,sort_keys=True))
        control=os.getenv("CELIKOM_A1_CLONE_ONLY_CONTROL")=="1"
        allowed=(result["verdict"]=="METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO" or
                 (control and result["verdict"]==
                  "CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS"))
        sys.exit(0 if allowed else 1)
    except Exception as e:
        code=str(e)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",code):
            code="NAMESPACED_PRIVATE_DISPOSABLE_ERROR"
        print(json.dumps({"verdict":"NAMESPACED_LSPATCH2_EXPERIMENT_ABORTED",
            "reason":code,"owner_phone_touched":False,"stage_a":"NO_GO",
            "vendor_apk_published":False},sort_keys=True))
        sys.exit(2)
