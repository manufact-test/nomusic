#!/usr/bin/env python3
"""Isolated LSPatch metaloader A/B, zero signature bypass, NO modules.

Only wraps a previously verified ONE-APK independent-signature clone under
CI in disposable ephemeral emulator. The original issuer-signed Yandex APK
is NEVER patched, installed over, uploaded, authenticated or modified.
This does not test audio and CANNOT be sent to user's HONOR 50.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import copy
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


def check_zero_loader(apk: Path, prior: Path, expected_signer: str, arsc,
                      witness_module_sha256: str | None = None) -> dict:
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
        if witness_module_sha256 is None:
            if module_names:
                raise arsc.TrialError("METALOADER_CONTROL_HAS_EMBEDDED_MODULE")
        elif (len(module_names) != 1 or
              not re.fullmatch(r"[0-9a-f]{64}", witness_module_sha256) or
              hashlib.sha256(z.read(module_names[0])).hexdigest() != witness_module_sha256):
            raise arsc.TrialError("METALOADER_WITNESS_MODULE_DRIFT")
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
        "separate_module_embedded": witness_module_sha256 is not None,
        "embedded_origin_dex_count": sum(x.startswith("classes") and x.endswith(".dex") for x in actual),
        "embedded_origin_native_lib_count": sum(x.startswith("lib/") for x in actual),
        "embedded_origin_sha256_payload_parity": True,
        "login_tested": False,
        "audio_swap_tested": False,
        "play_protect_tested": False,
        "consumer_release": False,
    }


def verify_native_loader_elf_offsets(apk: Path, expected_x86_machine: int = 3) -> dict:
    """Audit ABI/ELF/ZIP page alignment on the ACTUALLY signed outer APK.

    Absolute offsets cannot be inferred from a rebuilt unsigned intermediary.
    Match exact 4 known architectures; do not expose any third-party binary
    bytes. Fail closed if any loader was compressed, missing, misaligned or
    has an unexpected ELF ISA.
    """
    architectures = {"armeabi-v7a": (40, 1), "arm64-v8a": (183, 2),
                     "x86": (expected_x86_machine, 1), "x86_64": (62, 2)}
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



def mirror_x86_loader_resource_for_arm_bridge(source_apk: Path, output_apk: Path) -> dict:
    """Emulator ONLY: mirror upstream ARMv7 ELF at the x86-named resource.

    The zero-bypass LSPatch Java stub stays byte-identical. Test whether the
    Android x86/native-ARM bridge accepts the correct EM_ARM loader. This is
    not a distributable app or a fix for general x86 hardware.
    """
    if source_apk.resolve() == output_apk.resolve() or output_apk.exists():
        raise ValueError("BRIDGE_MIRROR_NEW_OUTPUT_REQUIRED")
    arm_name = "assets/lspatch/so/armeabi-v7a/liblspatch.so"
    x86_name = "assets/lspatch/so/x86/liblspatch.so"
    with zipfile.ZipFile(source_apk) as source_zip:
        infos = source_zip.infolist()
        names = [m.filename for m in infos]
        if len(infos) > 10000 or len(names) != len(set(names)):
            raise ValueError("BRIDGE_MIRROR_UNSAFE_ZIP_ENTRIES")
        if sum(m.file_size for m in infos) > 512 * 1024 * 1024:
            raise ValueError("BRIDGE_MIRROR_ZIP_SIZE_LIMIT")
        arm, x86 = source_zip.read(arm_name), source_zip.read(x86_name)
        if (arm[:4] != b"\x7fELF" or x86[:4] != b"\x7fELF"
                or arm[4] != 1 or x86[4] != 1
                or struct.unpack_from("<H", arm, 18)[0] != 40
                or struct.unpack_from("<H", x86, 18)[0] != 3):
            raise ValueError("BRIDGE_MIRROR_SOURCE_ABI_UNEXPECTED")
        if (source_zip.getinfo(arm_name).compress_type != zipfile.ZIP_STORED
                or source_zip.getinfo(x86_name).compress_type != zipfile.ZIP_STORED):
            raise ValueError("BRIDGE_MIRROR_NATIVE_NOT_STORED")
        with zipfile.ZipFile(output_apk, "w", allowZip64=True) as result:
            result.comment = source_zip.comment
            for entry in infos:
                body = arm if entry.filename == x86_name else source_zip.read(entry)
                dst = copy.copy(entry)
                dst.extra = b""
                dst.CRC = dst.file_size = dst.compress_size = 0
                if (dst.filename.startswith("assets/lspatch/so/")
                        and dst.filename.endswith("/liblspatch.so")
                        and dst.compress_type == zipfile.ZIP_STORED):
                    pos = result.fp.tell()
                    pad = (-(pos + 30 + len(dst.filename.encode("utf-8")))) % 4096
                    if 0 < pad < 4:
                        pad += 4096
                    if pad:
                        dst.extra = struct.pack("<HH", 0xEFA1, pad - 4) + bytes(pad - 4)
                result.writestr(dst, body, compress_type=entry.compress_type)
    with zipfile.ZipFile(output_apk) as result:
        if result.read(x86_name) != result.read(arm_name):
            raise ValueError("BRIDGE_MIRROR_NOT_ARMV7_IDENTICAL")
        for entry in result.infolist():
            result.read(entry)
    return {"scope": "EMULATOR_X86_ARMV7_BRIDGE_ONLY",
            "loader_bytes_from": "PINNED_UPSTREAM_ARMV7",
            "source_x86_machine": 3, "mirrored_x86_resource_machine": 40,
            "host_dex_changed": False, "signature_bypass_changed": False,
            "redistributable": False}


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
    witness_digest = None
    signed_witness = None
    if os.getenv("CELIKOM_A1_EXIT_WITNESS") == "1":
        if (os.getenv("GITHUB_ACTIONS") != "true" or
                os.getenv("CELIKOM_NATIVE_ARM13_REDDROID_CLONE") != "1"):
            raise arsc.TrialError("EXIT_WITNESS_DISPOSABLE_NATIVE_ARM_ONLY")
        path = os.getenv("CELIKOM_A1_EXIT_WITNESS_APK", "")
        runner = Path(os.getenv("RUNNER_TEMP", "/nonexistent")).resolve()
        candidate = Path(path).resolve() if path else Path("/nonexistent")
        if not candidate.is_file() or runner not in candidate.parents:
            raise arsc.TrialError("EXIT_WITNESS_EPHEMERAL_MODULE_MISSING")
        if candidate.stat().st_size > 4 * 1024 * 1024:
            raise arsc.TrialError("EXIT_WITNESS_MODULE_TOO_LARGE")
        with zipfile.ZipFile(candidate) as mz:
            if (mz.read("META-INF/xposed/scope.list").decode("utf-8").split()
                    != [source.DEST] or
                    mz.read("META-INF/xposed/java_init.list").decode("utf-8").strip()
                    != "pro.celikom.a1exitwitness.ExitCallsiteWitness" or
                    "minApiVersion=102" not in
                    mz.read("META-INF/xposed/module.prop").decode("utf-8")):
                raise arsc.TrialError("EXIT_WITNESS_MODULE_SCOPE_INVALID")
        manifest = arsc.run(
            [source.sdk_tool("aapt"), "dump", "xmltree", str(candidate), "AndroidManifest.xml"],
            "EXIT_WITNESS_MANIFEST_AUDIT", 45)
        if "E: uses-permission" in manifest:
            raise arsc.TrialError("EXIT_WITNESS_PERMISSIONS_FORBIDDEN")
        signed_witness = work / "lab-exit-observer-only.apk"
        shutil.copyfile(candidate, signed_witness)
        arsc.run([source.sdk_tool("apksigner"), "sign", "--ks", str(key),
                  "--ks-pass", "pass:ephemeral-lab-only",
                  "--ks-key-alias", "research", "--key-pass", "pass:ephemeral-lab-only",
                  "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                  str(signed_witness)], "EXIT_WITNESS_SIGN_WITH_OWN_LAB_KEY", 90)
        if fingerprint(signed_witness, arsc) != expected_signer:
            raise arsc.TrialError("EXIT_WITNESS_SAME_LAB_SIGNER_REQUIRED")
        witness_digest = hashlib.sha256(signed_witness.read_bytes()).hexdigest()
    stage = work / "private-lab-metadata-loader-zero"
    stage.mkdir()
    print(json.dumps({"lspatch_zero_phase": "PINNED_PATCHER_VERIFIED"}))
    patch_command = ["java", "-jar", str(patcher), "-k", str(key),
                     "ephemeral-lab-only", "research", "ephemeral-lab-only"]
    if signed_witness is not None:
        patch_command.extend(["-m", str(signed_witness)])
    patch_command.extend(["-o", str(stage), "-l", "0", str(clone)])
    arsc.run(patch_command, "LSPATCH_CLONE_BOOTSTRAP_ZERO_BYPASS", 500)
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
    report = check_zero_loader(final_apk, clone, expected_signer, arsc,
                               witness_module_sha256=witness_digest)
    try:
        report["signed_lspatch_native_elf_layout"] = verify_native_loader_elf_offsets(final_apk)
    except (ValueError, zipfile.BadZipFile):
        raise arsc.TrialError("LSPATCH_SIGNED_LOADER_ABI_OR_ALIGNMENT_FAILED") from None
    report["nested_origin_zip_crc_repaired"] = crc_report["crc_repaired"]
    report["nested_origin_zip_layout_repacked"] = crc_report["layout_repacked"]
    if crc_report["layout_repacked"]:
        report["nested_origin_zip_layout_issue"] = crc_report["repacked_reason"]
    if os.getenv("CELIKOM_BRIDGE_X86_RESOURCE_ARMV7") == "1":
        if not (os.getenv("GITHUB_ACTIONS") == "true"
                and os.getenv("CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION") == "1"
                and os.getenv("CELIKOM_CLONE_LSPATCH_LOADER_ZERO") == "1"):
            raise arsc.TrialError("BRIDGE_MIRROR_DISPOSABLE_CI_ONLY")
        raw = work / "bridge-armv7-mirror-unsigned.apk"
        try:
            bridge_report = mirror_x86_loader_resource_for_arm_bridge(final_apk, raw)
        except (ValueError, zipfile.BadZipFile):
            raise arsc.TrialError("BRIDGE_MIRROR_STRUCTURAL_FAILURE") from None
        aligned = work / "bridge-armv7-mirror-aligned.apk"
        arsc.run([source.sdk_tool("zipalign"), "-f", "-p", "4",
                  str(raw), str(aligned)], "BRIDGE_MIRROR_ALIGN", 90)
        arsc.run([source.sdk_tool("apksigner"), "sign", "--ks", str(key),
                  "--ks-pass", "pass:ephemeral-lab-only",
                  "--ks-key-alias", "research", "--key-pass", "pass:ephemeral-lab-only",
                  "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                  str(aligned)], "BRIDGE_MIRROR_LAB_SIGN_ONLY", 90)
        if fingerprint(aligned, arsc) != expected_signer:
            raise arsc.TrialError("BRIDGE_MIRROR_SIGNER_MISMATCH")
        check_zero_loader(aligned, clone, expected_signer, arsc,
                          witness_module_sha256=witness_digest)
        try:
            bridge_report["signed_mirrored_elf_layout"] = (
                verify_native_loader_elf_offsets(aligned, expected_x86_machine=40))
        except (ValueError, zipfile.BadZipFile):
            raise arsc.TrialError("BRIDGE_MIRROR_SIGNED_ABI_OR_ALIGNMENT_FAILED") from None
        report["bridge_mirror_ab"] = bridge_report
        final_apk = aligned
    return final_apk, report
