"""No-release one-APK consolidation of a verified separate-package clone bundle.

Inputs must already be independently signed, exact-version, 5-part lab clones
from clone_native_identity_phase2_ephemeral.py. The publisher original is NEVER
merged, altered, resigned, uploaded or installed over. No sigbypass or DRM work.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import clone_native_splits_ephemeral as source

def fingerprint(apk: Path, arsc) -> str:
    lines = arsc.run(
        [source.sdk_tool("apksigner"), "verify", "--print-certs", str(apk)],
        "LAB_SINGLE_VERIFY_SIGNATURE", 90)
    results = [x.split("digest:", 1)[-1].strip().replace(":", "").lower()
               for x in lines.splitlines() if "certificate SHA-256 digest:" in x]
    if len(results) != 1 or not re.fullmatch(r"[a-f0-9]{64}", results[0]):
        raise arsc.TrialError("LAB_SINGLE_INVALID_SIGNER")
    return results[0]

def byte_payloads(apks: list[Path]) -> dict[str, str]:
    """Only compiled DEX and native library SHA256; no user content."""
    result: dict[str, str] = {}
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for name in z.namelist():
                if not (re.fullmatch(r"classes\d*\.dex", name)
                        or name.startswith("lib/") and name.endswith(".so")):
                    continue
                digest = hashlib.sha256(z.read(name)).hexdigest()
                if name in result and result[name] != digest:
                    raise ValueError("INCONSISTENT_NATIVE_OR_DEX_DUPLICATE")
                result[name] = digest
    if "classes.dex" not in result:
        raise ValueError("BASE_CODE_MISSING")
    return result

def verify_merged_payloads(inputs: list[Path], merged: Path) -> dict:
    expected = byte_payloads(inputs)
    actual = byte_payloads([merged])
    if expected != actual:
        raise ValueError("SINGLE_APK_DEX_OR_NATIVE_PAYLOAD_DRIFT")
    return {
        "single_apk_payload_dex_count": sum(re.fullmatch(r"classes\d*\.dex", k) is not None for k in actual),
        "single_apk_payload_native_library_count": sum(k.startswith("lib/") for k in actual),
        "payload_byte_hashes_match": True,
    }

def merge_ephemeral(apks: list[Path], work: Path, editor: Path,
                    key: Path, expected_lab_cert: str, arsc) -> tuple[Path, dict]:
    if len(apks) != 5:
        raise arsc.TrialError("MERGE_REQUIRES_EXACT_VERIFIED_FIVE_CLONE_SPLITS")
    merge_dir = work / "verified-clone-splits-for-merge"
    merge_dir.mkdir()
    seen = set()
    for apk in apks:
        info = source.apkmeta(apk)
        split = info.get("split", "")
        if (info.get("name") != source.DEST or info.get("versionCode") != "24026531"
                or split in seen or not re.fullmatch(r"[A-Za-z0-9_.-]*", split)):
            raise arsc.TrialError("MERGE_SOURCE_SPLIT_IDENTITY_DRIFT")
        if fingerprint(apk, arsc) != expected_lab_cert:
            raise arsc.TrialError("MERGE_SOURCE_SIGNER_DRIFT")
        seen.add(split)
        shutil.copyfile(apk, merge_dir / ("base.apk" if not split else "split_" + split + ".apk"))
    if len(seen) != 5 or "" not in seen:
        raise arsc.TrialError("MERGE_SOURCE_MISSING_BASE")
    merged_raw = work / "merge-unsigned.apk"
    arsc.run(["java", "-Xmx3g", "-jar", str(editor), "m",
              "-i", str(merge_dir), "-o", str(merged_raw)],
             "MERGE_CLONE_SPLIT_TO_SINGLE", 400)
    aligned = work / "merged-aligned.apk"
    arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
              str(merged_raw), str(aligned)], "MERGED_ZIPALIGN", 90)
    arsc.run([source.sdk_tool("apksigner"), "sign",
              "--ks", str(key), "--ks-pass", "pass:ephemeral-lab-only",
              "--ks-key-alias", "research", "--key-pass", "pass:ephemeral-lab-only",
              "--min-sdk-version", "28", "--v4-signing-enabled", "false",
              str(aligned)], "MERGED_SIGN", 90)
    metadata = source.apkmeta(aligned)
    if (metadata.get("name") != source.DEST or
            metadata.get("versionCode") != "24026531" or
            metadata.get("split", "")):
        raise arsc.TrialError("MERGED_PACKAGE_OR_SPLIT_METADATA_INVALID")
    if fingerprint(aligned, arsc) != expected_lab_cert:
        raise arsc.TrialError("MERGED_SIGNER_NOT_MATCHING_LAB")
    if expected_lab_cert == source.RUSTORE_SHA256_CERT:
        raise arsc.TrialError("MERGED_SIGNER_EQUALS_PUBLISHER_CERT")
    try:
        payload = verify_merged_payloads(apks, aligned)
    except (ValueError, zipfile.BadZipFile):
        raise arsc.TrialError("MERGED_NATIVE_OR_DEX_PAYLOAD_INCONSISTENT") from None
    return aligned, {
        "structural_stage": "SINGLE_APK_MERGED_VERIFIED_NOT_NATIVE_RUNTIME",
        "clone_package": source.DEST,
        "split_count_into_merge": len(apks),
        "output_apk_count": 1,
        "original_publisher_apk_untouched": True,
        "lab_signer_distinct_from_publisher": True,
        "modified_original_dex": False,
        "signature_bypass": False,
        "play_protect_tested": False,
        "native_audio_swap_tested": False,
        "consumer_release": False,
        **payload,
    }
