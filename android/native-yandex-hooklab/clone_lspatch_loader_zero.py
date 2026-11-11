#!/usr/bin/env python3
"""Isolated LSPatch metaloader A/B, zero signature bypass, NO modules.

Only wraps a previously verified ONE-APK independent-signature clone under
CI in disposable ephemeral emulator. The original issuer-signed Yandex APK
is NEVER patched, installed over, uploaded, authenticated or modified.
This does not test audio and CANNOT be sent to user's HONOR 50.
"""
from __future__ import annotations

import hashlib
import zipfile
import json
import re
import zipfile
import struct
import urllib.request
from pathlib import Path

from merge_lab_splits_ephemeral import fingerprint, verify_merged_payloads
from recover_stored_origin_crc import rewrite_only_if_origin_crc_mismatch
import clone_native_splits_ephemeral as source

JAR_URL = "https://github.com/JingMatrix/LSPatch/releases/download/v1.2/lspatch-v1.2-487-release.jar"
JAR_SHA256 = "d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165"


def download_pinned_patcher(path: Path) -> None:
    h = hashlib.sha256()
    amount = 0
    req = urllib.request.Request(JAR_URL, headers={"User-Agent": "CELIKOM-A1-private-lab/1.0"})
    with urllib.request.urlopen(req, timeout=100) as stream, path.open("wb") as out:
        while chunk := stream.read(1024 * 1024):
            amount += len(chunk)
            if amount > 20 * 1024 * 1024:
                raise ValueError("UPSTREAM_PATCHER_UNEXPECTED_SIZE")
            h.update(chunk)
            out.write(chunk)
    if h.hexdigest() != JAR_SHA256:
        raise ValueError("UPSTREAM_PATCHER_DIGEST_DRIFT")


def check_zero_loader(apk: Path, prior: Path, expected_signer: str, arsc) -> dict:
    """Fail closed on signature bypass, package/version drift, lost code or modules."""
    p = source.apkmeta(apk)
    original_id = source.apkmeta(prior)
    if (p.get("name") != source.DEST or
            p.get("versionCode") != "24026531" or
            p.get("split", "") or original_id.get("name") != p.get("name")):
        raise arsc.TrialError("METALOADER_CLONE_IDENTITY_INVALID")
    if fingerprint(apk, arsc) != expected_signer:
        raise arsc.TrialError("METALOADER_DIFFERENT_LAB_SIGNER")
    if not zipfile.is_zipfile(apk):
        raise arsc.TrialError("METALOADER_OUTER_NOT_ZIP")
    print(json.dumps({"lspatch_zero_phase": "OUTER_APK_ZIP_CONFIRMED"}))
    with zipfile.ZipFile(apk) as z:
        required = ("assets/lspatch/config.json", "assets/lspatch/origin.apk",
                    "assets/lspatch/loader.dex", "classes.dex")
        if any(name not in z.namelist() for name in required):
            raise arsc.TrialError("METALOADER_MISSING_BOOTSTRAP_PART")
        module_names = [name for name in z.namelist()
                        if name.startswith("assets/lspatch/modules/") and name.endswith(".apk")]
        if module_names:
            raise arsc.TrialError("METALOADER_CONTROL_HAS_EMBEDDED_MODULE")
        try:
            cfg = json.loads(z.read("assets/lspatch/config.json").decode("utf-8"))
        except zipfile.BadZipFile:
            raise arsc.TrialError("METALOADER_CONFIG_MEMBER_BAD_CRC") from None
        except (ValueError, UnicodeError):
            raise arsc.TrialError("METALOADER_CONFIG_INVALID") from None
        if (type(cfg.get("sigBypassLevel")) is not int or
                cfg["sigBypassLevel"] != 0):
            raise arsc.TrialError("NONZERO_SIGNATURE_BYPASS_PROHIBITED")
        if cfg.get("useManager") is not False:
            raise arsc.TrialError("METALOADER_EXTERNAL_MANAGER_NOT_ALLOWED")
        # Compare original code and native libs inside the embedded host, not
        # outer stub classes.dex (which deliberately contains loader, NOT host).
        try:
            nested_data = z.read("assets/lspatch/origin.apk")
        except zipfile.BadZipFile:
            raise arsc.TrialError("METALOADER_EMBEDDED_ORIGIN_MEMBER_BAD_CRC") from None
        if len(nested_data) > 128 * 1024 * 1024:
            raise arsc.TrialError("METALOADER_ORIGIN_TOO_LARGE")
        import io
        if not zipfile.is_zipfile(io.BytesIO(nested_data)):
            raise arsc.TrialError("METALOADER_EMBEDDED_ORIGIN_NOT_ZIP")
        if not zipfile.is_zipfile(prior):
            raise arsc.TrialError("METALOADER_PRIOR_CLONE_NOT_ZIP")
        print(json.dumps({"lspatch_zero_phase": "INNER_HOST_ZIP_CONFIRMED"}))
        with zipfile.ZipFile(io.BytesIO(nested_data)) as original_zip, \
             zipfile.ZipFile(prior) as prior_zip:
            def payload(zf):
                return {name: hashlib.sha256(zf.read(name)).hexdigest()
                        for name in zf.namelist() if
                        re.fullmatch(r"classes\d*\.dex", name)
                        or name.startswith("lib/") and name.endswith(".so")}
            try:
                actual, expected = payload(original_zip), payload(prior_zip)
            except zipfile.BadZipFile:
                raise arsc.TrialError("METALOADER_ORIGIN_CODE_CRC_INVALID") from None
            if actual != expected or "classes.dex" not in actual:
                raise arsc.TrialError("METALOADER_ORIGIN_NATIVE_CODE_DRIFT")
    return {
        "status": "METALOADER_ZERO_BYPASS_STRUCTURAL_ONLY",
        "rootless_one_apk": True,
        "clone_package": source.DEST,
        "issuer_signed_original_touched": False,
        "signature_bypass_level": 0,
        "separate_module_embedded": False,
        "embedded_origin_dex_count": sum(x.startswith("classes") and x.endswith(".dex") for x in actual),
        "embedded_origin_native_lib_count": sum(x.startswith("lib/") for x in actual),
        "embedded_origin_sha256_payload_parity": True,
        "login_tested": False,
        "audio_swap_tested": False,
        "play_protect_tested": False,
        "consumer_release": False,
    }


def verify_native_loader_elf_offsets(apk: Path) -> dict:
    """Audit ABI/ELF/ZIP page alignment on the ACTUALLY signed outer APK.

    Absolute offsets cannot be inferred from a rebuilt unsigned intermediary.
    Match exact 4 known architectures; do not expose any third-party binary
    bytes. Fail closed if any loader was compressed, missing, misaligned or
    has an unexpected ELF ISA.
    """
    architectures = {"armeabi-v7a": (40, 1), "arm64-v8a": (183, 2),
                     "x86": (3, 1), "x86_64": (62, 2)}
    result = {}
    with zipfile.ZipFile(apk) as archive, apk.open("rb") as fh:
        for abi, (machine, elf_class) in architectures.items():
            member = f"assets/lspatch/so/{abi}/liblspatch.so"
            if member not in archive.namelist():
                raise ValueError("METALOADER_LIBRARY_ABI_MISSING")
            info = archive.getinfo(member)
            if info.compress_type != zipfile.ZIP_STORED:
                raise ValueError("METALOADER_LIBRARY_NOT_STORED")
            fh.seek(info.header_offset)
            local_header = fh.read(30)
            if len(local_header) != 30 or local_header[:4] != b"PK\x03\x04":
                raise ValueError("METALOADER_LIBRARY_LOCAL_HEADER_INVALID")
            name_len, extra_len = struct.unpack_from("<HH", local_header, 26)
            offset = info.header_offset + 30 + name_len + extra_len
            with archive.open(info) as library:
                elf = library.read(20)
            if not elf.startswith(b"\x7fELF") or len(elf) != 20:
                raise ValueError("METALOADER_LIBRARY_INVALID_ELF")
            found = struct.unpack_from("<H", elf, 18)[0]
            if found != machine or elf[4] != elf_class:
                raise ValueError("METALOADER_LIBRARY_ABI_ELF_MISMATCH")
            result[abi] = {"expected_elf_machine": machine,
                           "elf_class": elf_class,
                           "page_aligned_4096": offset % 4096 == 0,
                           "stored": True}
    if not all(x["page_aligned_4096"] for x in result.values()):
        raise ValueError("METALOADER_LIBRARY_UNALIGNED_IN_SIGNED_APK")
    return result


def wrap_clone_with_lspatch_zero(clone: Path, work: Path, key: Path,
                                 expected_signer: str, arsc) -> tuple[Path, dict]:
    # Strictly after the successful 5->1 cloned-bundle merge and its verifier.
    if clone is None or not clone.is_file():
        raise arsc.TrialError("VERIFIED_CLONE_SINGLE_APK_REQUIRED")
    if expected_signer == source.RUSTORE_SHA256_CERT:
        raise arsc.TrialError("PUBLISHER_CERT_NOT_ALLOWED_FOR_LAB")
    if fingerprint(clone, arsc) != expected_signer:
        raise arsc.TrialError("SOURCE_CLONE_SIGNER_DRIFT")
    patcher = work / "lspatch-upstream-pinned.jar"
    try:
        download_pinned_patcher(patcher)
    except (ValueError, OSError):
        raise arsc.TrialError("PINNED_PATCHER_DOWNLOAD_OR_HASH_FAILED") from None
    stage = work / "private-lab-metadata-loader-zero"
    stage.mkdir()
    print(json.dumps({"lspatch_zero_phase": "PINNED_PATCHER_VERIFIED"}))
    arsc.run(
        ["java", "-jar", str(patcher), "-k", str(key),
         "ephemeral-lab-only", "research", "ephemeral-lab-only",
         "-o", str(stage), "-l", "0", str(clone)],
        "LSPATCH_CLONE_BOOTSTRAP_ZERO_BYPASS", 500)
    print(json.dumps({"lspatch_zero_phase": "PATCH_COMMAND_COMPLETED"}))
    results = list(stage.glob("*.apk"))
    if len(results) != 1:
        raise arsc.TrialError("METALOADER_NOT_EXACT_ONE_APK")
    print(json.dumps({"lspatch_zero_phase": "ONE_PATCH_OUTPUT_DISCOVERED"}))
    try:
        raw_rebuilt = work / "loader-zero-crc-only-rebuilt-unsigned.apk"
        crc_report = rewrite_only_if_origin_crc_mismatch(results[0], raw_rebuilt)
    except (ValueError, zipfile.BadZipFile):
        raise arsc.TrialError("LSPATCH_OUTER_CRC_REPAIR_NOT_SAFE") from None
    final_apk = results[0]
    if crc_report["layout_repacked"]:
        aligned = work / "loader-zero-crc-aligned.apk"
        arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
                  str(raw_rebuilt), str(aligned)],
                 "LSPATCH_REBUILT_ZIPALIGN", 90)
        arsc.run([source.sdk_tool("apksigner"), "sign", "--ks", str(key),
                  "--ks-pass", "pass:ephemeral-lab-only",
                  "--ks-key-alias", "research", "--key-pass", "pass:ephemeral-lab-only",
                  "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                  str(aligned)], "LSPATCH_REBUILT_SIGN_WITH_OWN_LAB_KEY", 90)
        if fingerprint(aligned, arsc) != expected_signer:
            raise arsc.TrialError("LSPATCH_REBUILT_OWN_SIGNER_MISMATCH")
        final_apk = aligned
        print(json.dumps({"lspatch_zero_phase": "EMBEDDED_ORIGIN_ZIP_LAYOUT_REBUILT_OWN_SIGNER"}))
    report = check_zero_loader(final_apk, clone, expected_signer, arsc)
    try:
        report["signed_lspatch_native_elf_layout"] = verify_native_loader_elf_offsets(final_apk)
    except (ValueError, zipfile.BadZipFile):
        raise arsc.TrialError("LSPATCH_SIGNED_LOADER_ABI_OR_ALIGNMENT_FAILED") from None
    report["nested_origin_zip_crc_repaired"] = crc_report["crc_repaired"]
    report["nested_origin_zip_layout_repacked"] = crc_report["layout_repacked"]
    if crc_report["layout_repacked"]:
        report["nested_origin_zip_layout_issue"] = crc_report["repacked_reason"]
    return final_apk, report
