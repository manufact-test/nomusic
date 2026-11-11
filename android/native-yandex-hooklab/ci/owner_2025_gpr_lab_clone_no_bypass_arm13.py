#!/usr/bin/env python3
"""New real 2025 GPR vs lab-signed clone feasibility experiment, NO bypass.

Read-only original is cryptographically signed, then each of 16 disposable
splits is decoded, given an independent CELIKOM-lab package ID/signature,
with original DEX/native payload bytes preserved. Clone is NEVER distributed,
published, or installed onto an owner device. No publisher certificate spoof,
root, DRM/Passport hooks, LSPatch bypass levels, or owner account.
"""
from __future__ import annotations
import hashlib, json, os, platform, re, subprocess, sys, tempfile, time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
import clone_native_splits_ephemeral as source
import clone_native_splits_arsclib_ephemeral as arsc
import clone_main_crash_buffer as diagnostics
from uptodown_2025_gpr_ephemeral_verify import unbundle_candidate,verify_split_set
from publisher_2025_provenance_gate import GateError,private_command
from lab_signer_signal_gate import probe_apk_zip, safe_report
from lab_unsigned_archive_cleanroom import remove_stale_v1_from_disposable_unsigned

PKG="pro.celikom.yandex.nativeclonelab"
ORIGINAL="ru.yandex.music"
CONTAINER="celikom-native-arm-android13"
EXPECTED_ARCHIVE_BYTES=45961661
EXPECTED_SHA256="8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053"
CODE="24025542"
SPLITS=16

def stop(reason: str):
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
        reason="PRIVATE_LAB_FAILURE"
    raise RuntimeError(reason)

def cmd(argv,timeout=90):
    return subprocess.run(argv,capture_output=True,text=True,errors="replace",
                          check=False,timeout=timeout)

def guest(*argv,timeout=35):
    return cmd(["docker","exec",CONTAINER,*argv],timeout)

def lab_sdk_tool(name: str) -> str:
    """Pin actual SDK Build Tools in an isolated CI, not apt tool symlinks."""
    version = os.getenv("CELIKOM_A1_PINNED_SDK_VERSION")
    if not version:
        return source.sdk_tool(name)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        stop("PINNED_ANDROID_SDK_VERSION_INVALID")
    root_text = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    if not root_text:
        stop("PINNED_ANDROID_SDK_ROOT_MISSING")
    root = Path(root_text).resolve()
    folder = root / "build-tools" / version
    candidate = folder / name
    if (not candidate.is_file() or candidate.is_symlink()
            or not candidate.resolve().is_relative_to(folder.resolve())):
        stop("PINNED_ANDROID_SDK_TOOL_NOT_OFFICIAL")
    return str(candidate)


def apk_name(path: Path) -> dict:
    return source.apkmeta(path)

def verified_orig_paths(xapk: Path, root: Path) -> list[Path]:
    if not xapk.is_file() or xapk.is_symlink() or xapk.stat().st_size!=EXPECTED_ARCHIVE_BYTES:
        stop("ORIGINAL_XAPK_SIZE_DRIFT")
    digest=hashlib.sha256()
    with xapk.open("rb") as stream:
        for data in iter(lambda:stream.read(1024*1024),b""):
            digest.update(data)
    if digest.hexdigest()!=EXPECTED_SHA256:
        stop("ORIGINAL_XAPK_DIGEST_DRIFT")
    src=root/"trusted-source-splits"
    src.mkdir()
    parts=unbundle_candidate(xapk,src)
    if len(parts)!=SPLITS:
        stop("ORIGINAL_SPLIT_COUNT_DRIFT")
    check=verify_split_set(parts)
    if check["verified_issuer_signed_splits"]!=SPLITS:
        stop("ORIGINAL_ISSUER_VERIFICATION_FAILED")
    return parts

def lab_manifest_min_sdk(apk: Path) -> int | None:
    """Return only numerical minSdk from public APK manifest metadata."""
    result = cmd([lab_sdk_tool("aapt"), "dump", "badging", str(apk)], 60)
    if result.returncode:
        return None
    match = re.search(r"^sdkVersion:'(\d+)'", result.stdout, re.M)
    return int(match.group(1)) if match else None


def ephemeral_clone(originals: list[Path], work: Path) -> tuple[list[tuple[str,Path]],dict]:
    jar=work/"APKEditor-1.4.9-verified.jar"
    arsc.download_editor(jar)
    lab_key=work/"unique-ephemeral-signer.jks"
    source.action(["keytool","-genkeypair","-noprompt","-storetype","JKS",
        "-keystore",str(lab_key),"-storepass","ephemeral-lab-only",
        "-keypass","ephemeral-lab-only","-alias","celikom-lab",
        "-keyalg","RSA","-keysize","2048","-validity","1",
        "-dname","CN=CELIKOM Disposable Source Compatibility Lab, O=CELIKOM, C=XX"],
        "OWN_LAB_SIGNING_KEY_CREATION_FAILED",100)
    output=[]
    expected_signer=None
    originals_seen=set()
    clone_seen=set()
    provider_rewrites=0
    obsolete_v1_entries_removed=0
    for i,original in enumerate(originals):
        old=apk_name(original)
        name=old.get("split","")
        if (old.get("name")!=ORIGINAL or old.get("versionCode")!=CODE
            or name in originals_seen):
            stop("ORIGINAL_META_DRIFT")
        originals_seen.add(name)
        decoded=work/f"decoded-{i}"
        arsc.run(["java","-Xmx3g","-jar",str(jar),"d","-t","xml",
                  "-dex","-i",str(original),"-o",str(decoded)],
                 "ARSC_DECODE_2025_SPLIT",360)
        manifest=decoded/"AndroidManifest.xml"
        if not manifest.is_file():
            stop("DECODED_MANIFEST_MISSING")
        raw=manifest.read_bytes()
        if not raw.lstrip().startswith(b"<"):
            stop("DECODED_MANIFEST_UNEXPECTED_FORMAT")
        rewritten,stats=source.rewrite_manifest(raw.decode("utf-8"))
        provider_rewrites+=stats["provider_authorities"]
        manifest.write_bytes(rewritten)
        raw_clone=work/f"unsigned-{i}.apk"
        arsc.run(["java","-Xmx3g","-jar",str(jar),"b","-t","xml",
                  "-i",str(decoded),"-o",str(raw_clone)],
                 "ARSC_REBUILD_2025_SPLIT",360)
        unsigned_probe=probe_apk_zip(raw_clone)
        if (not unsigned_probe["zip_integrity_ok"]
            or unsigned_probe["duplicate_entry_names"]
            or unsigned_probe["unsafe_entry_name_count"]
            or unsigned_probe["encrypted_entry_count"]
            or not unsigned_probe["contains_binary_manifest"]):
            print(json.dumps({"stage":"UNSIGNED_LAB_ARCHIVE",
                              "lab_split_index":i,
                              "zip_probe":unsigned_probe},sort_keys=True))
            stop("OWN_CLONE_UNSIGNED_ZIP_INVALID")
        cleaned=work/f"own-lab-clean-unsigned-{i}.apk"
        cleaned_meta=remove_stale_v1_from_disposable_unsigned(raw_clone,cleaned)
        obsolete_v1_entries_removed+=cleaned_meta["discarded_obsolete_v1_entries"]
        aligned=work/f"lab-clone-{i}.apk"
        source.action([lab_sdk_tool("zipalign"),"-f","-p","4",
                       str(cleaned),str(aligned)],"CLONE_ZIPALIGN_FAILED",100)
        source.action([lab_sdk_tool("apksigner"),"sign",
                      "--ks",str(lab_key),"--ks-pass","pass:ephemeral-lab-only",
                      "--ks-key-alias","celikom-lab",
                      "--key-pass","pass:ephemeral-lab-only",
                      "--min-sdk-version","21","--v1-signing-enabled","true",
                      "--v2-signing-enabled","true",
                      "--v3-signing-enabled","true",
                      "--v4-signing-enabled","false",
                      str(aligned)],"CLONE_SIGN_FAILED",90)
        signed_probe=probe_apk_zip(aligned)
        if (not signed_probe["zip_integrity_ok"]
            or signed_probe["duplicate_entry_names"]
            or signed_probe["unsafe_entry_name_count"]
            or signed_probe["encrypted_entry_count"]
            or not signed_probe["contains_binary_manifest"]):
            print(json.dumps({"stage":"SIGNED_LAB_ARCHIVE",
                              "lab_split_index":i,
                              "zip_probe":signed_probe},sort_keys=True))
            stop("OWN_CLONE_SIGNED_ZIP_INVALID")
        check=apk_name(aligned)
        if (check.get("name")!=PKG or check.get("versionCode")!=CODE or
            check.get("split","")!=name or name in clone_seen):
            stop("OWN_CLONE_SPLIT_MANIFEST_DRIFT")
        if source.native_payload_hashes(original)!=source.native_payload_hashes(aligned):
            stop("OWN_CLONE_DEX_OR_NATIVE_PAYLOAD_DRIFT")
        verified=cmd([lab_sdk_tool("apksigner"),"verify",
                      "--verbose","--print-certs",str(aligned)],100)
        if verified.returncode:
            # Classify failure without publishing unsigned app bytes,
            # private paths, certificate, stack, stderr or vendor strings.
            private=(verified.stdout+"\n"+verified.stderr).lower()
            signals={
                "digest_mismatch": ("digest" in private and "mismatch" in private),
                "zip_reconstruction": ("zip entry" in private or "zip central" in private),
                "scheme_v1": ("jar signature" in private or "v1 signature" in private),
                "scheme_v2": ("v2 scheme" in private or "v2 signature" in private),
                "scheme_v3": ("v3 scheme" in private or "v3 signature" in private),
                "manifest_format": ("manifest" in private or "binary xml" in private),
                "min_sdk": ("min sdk" in private or "minsdk" in private),
                "unsigned_entry": ("unsigned" in private),
                "signer_certificate": ("certificate" in private or "signer" in private),
            }
            print(json.dumps({"stage":"LAB_SIGNATURE_VALIDATION",
                              "original_vendor_signature_unmodified":True,
                              **safe_report(unsigned_probe,signed_probe,
                                            verified.returncode,verified.stdout,
                                            verified.stderr,i),
                              "sdk_failure_signals":[k for k,v in signals.items() if v],
                              "split_is_base":name=="",
                              "original_declared_min_sdk":lab_manifest_min_sdk(original),
                              "scratch_signed_declared_min_sdk":lab_manifest_min_sdk(aligned),
                              "signer_forced_min_sdk":21,
                              "sdk_result_exit_nonzero":True,
                              "clone_apk_not_installed":True},sort_keys=True))
            stop("OWN_CLONE_SIGNATURE_NOT_VERIFIED")
        signature=verified.stdout
        matched=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F:]+)",
                           signature)
        if len(matched)!=1:
            stop("OWN_CLONE_SIGNER_SET_NOT_SINGLE")
        cert=matched[0].replace(":","").lower()
        if cert==source.RUSTORE_SHA256_CERT:
            stop("OWN_LAB_CERT_MUST_DIFFER_FROM_PUBLISHER")
        if expected_signer is not None and cert!=expected_signer:
            stop("OWN_LAB_SPLIT_SIGNER_DISAGREEMENT")
        expected_signer=cert
        clone_seen.add(name)
        output.append((name if name else "base",aligned))
    if (len(output)!=SPLITS or clone_seen!=originals_seen
        or "" not in originals_seen or len(clone_seen)!=SPLITS):
        stop("OWN_CLONE_SPLIT_SET_INCOMPLETE")
    return output,{"lab_cloned_2025_splits":len(output),
      "all_original_dex_and_native_payloads_byte_preserved":True,
      "clone_cert_distinct_from_verified_publisher":True,
      "provider_authorities_from_original_package_rewritten":provider_rewrites,
      "obsolete_v1_jarsign_entries_removed_from_disposable_clone":obsolete_v1_entries_removed,
      "original_signer_spoofed":False,"signature_bypass_used":False}

def install_clones(clones: list[tuple[str,Path]]) -> str:
    remote=[]
    session=None
    try:
        for i,(name,path) in enumerate(clones):
            destination=f"/data/local/tmp/celikom-own-lab-{i}.apk"
            copied=cmd(["docker","cp",str(path),f"{CONTAINER}:{destination}"],120)
            if copied.returncode:
                stop("OWN_LAB_SPLIT_COPY_FAILED")
            remote.append((name,destination,path.stat().st_size))
        total=sum(item[2] for item in remote)
        made=guest("pm","install-create","--user","0","-S",str(total),timeout=90)
        found=re.search(r"Success:.*\[([0-9]{1,12})\]",made.stdout)
        if made.returncode or not found:
            return "OWN_LAB_INSTALL_CREATE_FAILED"
        session=found.group(1)
        for name,path,size in remote:
            write=guest("pm","install-write","-S",str(size),session,name,path,timeout=100)
            if write.returncode or not write.stdout.strip().startswith("Success"):
                return "OWN_LAB_INSTALL_WRITE_FAILED"
        commit=guest("pm","install-commit",session,timeout=230)
        if commit.returncode or not commit.stdout.strip().startswith("Success"):
            for category in ("INSTALL_FAILED_DUPLICATE_PERMISSION",
                "INSTALL_FAILED_CONFLICTING_PROVIDER","INSTALL_FAILED_INVALID_APK",
                "INSTALL_FAILED_NO_MATCHING_ABIS","INSTALL_FAILED_SHARED_USER_INCOMPATIBLE",
                "INSTALL_FAILED_MISSING_SPLIT","INSTALL_PARSE_FAILED"):
                if category in commit.stdout+commit.stderr:
                    return category
            return "OWN_LAB_INSTALL_COMMIT_FAILED"
        session=None
        return "INSTALLED"
    finally:
        if session:
            guest("pm","install-abandon",session,timeout=40)
        for _,remote_path,_ in remote:
            guest("rm","-f",remote_path,timeout=35)

def native_check() -> dict:
    if (os.getenv("GITHUB_ACTIONS")!="true" or
        os.getenv("GITHUB_REPOSITORY")!="manufact-test/nomusic" or
        os.getenv("GITHUB_REF_NAME")!="experiment/android-a1-owner2025-v1-sanitized-signer-lab-20261111" or
        os.getenv("CELIKOM_CLEAN_ANDROID_NATIVE_REDDROID")!="1" or
        platform.machine()!="aarch64"):
        stop("DISPOSABLE_REAL_ARM13_ONLY")
    if (guest("getprop","sys.boot_completed").stdout.strip()!="1" or
        guest("getprop","ro.build.version.sdk").stdout.strip()!="33"):
        stop("NATIVE_ARM13_GUEST_NOT_READY")
    abis=set(guest("getprop","ro.product.cpu.abilist").stdout.strip().split(","))
    if not {"arm64-v8a","armeabi-v7a"} <= abis:
        stop("NATIVE_ARMV7_ABI_MISSING")
    if guest("pm","path",PKG).stdout.strip() or guest("pm","path",ORIGINAL).stdout.strip():
        stop("GUEST_NOT_CLEAN_ORIGINAL_CLONE")
    return {"native_android13_real_arm":True,"fresh_guest_empty":True}

def main(archive: Path) -> dict:
    runtime=native_check()
    with tempfile.TemporaryDirectory(prefix="celikom-2025-disposable-no-bypass-") as d:
        work=Path(d)
        originals=verified_orig_paths(archive,work)
        lab_splits,meta=ephemeral_clone(originals,work)
        result={"verdict":"OWN_2025_LAB_RUNTIME_NOT_VERIFIED",
                **runtime,**meta,"owner_honor_touched":False,
                "owner_original_modified":False,"account_or_drm_tested":False,
                "audio_or_decoder_tested":False,"play_protect_tested":False,
                "published_lab_apk_or_artifact":False}
        result["lab_install_status"]=install_clones(lab_splits)
        if result["lab_install_status"]!="INSTALLED":
            result["verdict"]="OWN_2025_LAB_INSTALL_NO_GO"
            return result
        rows=guest("pm","path",PKG).stdout.splitlines()
        result["installed_lab_split_count"]=sum(x.startswith("package:") for x in rows)
        if result["installed_lab_split_count"]!=SPLITS:
            result["verdict"]="OWN_LAB_INSTALLED_SPLIT_COUNT_INVALID"
            return result
        launch=guest("am","start","--user","0","-n",
                     PKG+"/ru.yandex.music.main.MainScreenActivity",timeout=65)
        result["launch_intent_accepted"]=launch.returncode==0 and (
            "Starting:" in launch.stdout or "Warning: Activity not started" in launch.stdout)
        seen=[]
        resumed=0
        for _ in range(16):
            time.sleep(1)
            pid=guest("pidof",PKG)
            seen.append(pid.stdout.strip() if re.fullmatch(r"\d+",pid.stdout.strip()) else None)
            activity=guest("dumpsys","activity","activities")
            resumed+=int(any(PKG+"/" in x and
                         ("mResumedActivity" in x or "topResumedActivity" in x)
                         for x in activity.stdout.splitlines()))
        result["main_alive_16_of_16"]=all(x is not None for x in seen)
        result["same_exact_main_pid_16_of_16"]=all(x is not None for x in seen) and len(set(seen))==1
        result["resumed_16_of_16"]=resumed==16
        if not result["same_exact_main_pid_16_of_16"]:
            exit_info=guest("dumpsys","activity","exit-info",PKG,timeout=40)
            if exit_info.returncode==0:
                result["own_lab_main_exit"]=diagnostics.classify_main_exit_status(exit_info.stdout)
        result["verdict"]=(
            "OWN_2025_LAB_CLONE_MAIN_16S_STABLE"
            if result["same_exact_main_pid_16_of_16"] and result["resumed_16_of_16"]
            else "OWN_2025_LAB_CLONE_MAIN_NO_GO")
        return result

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--xapk",required=True,type=Path)
    args=parser.parse_args()
    try:
        report=main(args.xapk)
        print(json.dumps(report,sort_keys=True))
        # A strict failure is an experimental NO-GO, never mislabeled green.
        sys.exit(0 if report["verdict"]=="OWN_2025_LAB_CLONE_MAIN_16S_STABLE" else 1)
    except Exception as error:
        reason=str(error)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{4,92}",reason):
            reason="OWN_2025_LAB_PRIVATE_EXCEPTION"
        print(json.dumps({"verdict":"OWN_2025_LAB_EXPERIMENT_ABORTED",
          "reason":reason,"binary_artifact_uploaded":False,
          "owner_device_touched":False,"product_stage_a":"NO_GO"},sort_keys=True))
        sys.exit(2)
