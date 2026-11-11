#!/usr/bin/env python3
"""Ephemeral CI-only signed ARMv7 OWN LSPatch witness, never a Yandex app."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from build_owned_loader_host import PACKAGE, apk_identity, check_host, signed_sha, sdk
from clone_lspatch_loader_zero import verify_native_loader_elf_offsets
from recover_stored_origin_crc import rewrite_only_if_origin_crc_mismatch

NAME = "CELIKOM-ARMv7-HOOK-WITNESS-Test.apk"
OWN = "pro.celikom.armv7loaderhost.witness"


def command(args, stage):
    result = subprocess.run(args, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise ValueError("OWN_ARMV7_" + stage + "_FAILED")


def module_digest(apk):
    with zipfile.ZipFile(apk) as z:
        entries = [n for n in z.namelist()
                   if re.fullmatch(r"assets/lspatch/modules/[^/]+[.]apk", n)]
        if len(entries) != 1:
            raise ValueError("OWN_ARMV7_MODULE_NOT_EXACTLY_ONE")
        return hashlib.sha256(z.read(entries[0])).digest()


def main():
    if os.getenv("GITHUB_ACTIONS") != "true" or \
            os.getenv("CELIKOM_OWN_WITNESS") != "1" or PACKAGE != OWN:
        raise ValueError("OWN_ARMV7_PRIVATE_CI_ONLY")
    root = Path(os.environ["RUNNER_TEMP"]).resolve()
    apk = Path(os.environ["CELIKOM_OWN_ARM_INPUT"]).resolve()
    output = Path(os.environ["CELIKOM_OWN_ARM_OUTPUT"]).resolve()
    if root not in apk.parents or root not in output.parents or \
            apk.name != NAME or output.name != NAME or not apk.is_file() or \
            output.exists() or output.parent.exists():
        raise ValueError("OWN_ARMV7_ARTIFACT_SCOPE_INVALID")
    check_host(apk, patched=True)
    if apk_identity(apk) != (OWN, "1", "") or not signed_sha(apk):
        raise ValueError("OWN_ARMV7_INPUT_SIGNER_INVALID")
    fingerprint = module_digest(apk)
    with tempfile.TemporaryDirectory(prefix="own-armv7-normalize-") as temp:
        tmp = Path(temp)
        recovered = tmp / "original-fixed-unsigned.apk"
        recovery = rewrite_only_if_origin_crc_mismatch(apk, recovered)
        source = recovered if recovery["layout_repacked"] else apk
        aligned = tmp / "own-armv7-aligned.apk"
        command([sdk("zipalign"), "-f", "-p", "4", str(source), str(aligned)],
                "ZIPALIGN")
        key = tmp / "own-armv7-test-only.jks"
        command(["keytool", "-genkeypair", "-noprompt", "-storetype", "JKS",
                 "-keystore", str(key), "-storepass", "private-arm-lab",
                 "-keypass", "private-arm-lab", "-alias", "own-lab",
                 "-keyalg", "RSA", "-keysize", "2048", "-validity", "2",
                 "-dname", "CN=CELIKOM ARM Private Lab, O=CELIKOM, C=XX"],
                "KEY")
        command([sdk("apksigner"), "sign", "--ks", str(key),
                 "--ks-pass", "pass:private-arm-lab", "--ks-key-alias", "own-lab",
                 "--key-pass", "pass:private-arm-lab",
                 "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                 str(aligned)], "SIGN")
        check_host(aligned, patched=True)
        if apk_identity(aligned) != (OWN, "1", "") or not signed_sha(aligned):
            raise ValueError("OWN_ARMV7_SIGNER_DRIFT")
        layout = verify_native_loader_elf_offsets(aligned)
        if any(not v["page_aligned_4096"] for v in layout.values()):
            raise ValueError("OWN_ARMV7_LOADER_ALIGNMENT_INVALID")
        if module_digest(aligned) != fingerprint:
            raise ValueError("OWN_ARMV7_MODULE_CHANGED")
        with zipfile.ZipFile(aligned) as z, zipfile.ZipFile(apk) as original:
            cfg = json.loads(z.read("assets/lspatch/config.json"))
            if type(cfg.get("sigBypassLevel")) is not int or cfg["sigBypassLevel"] != 0:
                raise ValueError("OWN_ARMV7_SIGNATURE_BYPASS_FORBIDDEN")
            path = "lib/armeabi-v7a/libcelikom_host_probe.so"
            if hashlib.sha256(z.read(path)).digest() != \
                    hashlib.sha256(original.read(path)).digest():
                raise ValueError("OWN_ARMV7_HOST_JNI_CHANGED")
        output.parent.mkdir(mode=0o700, parents=True)
        output.write_bytes(aligned.read_bytes())
    return {"result": "OWN_ARMV7_NORMALIZED_SIGNED_STATIC_PASS",
            "abi": "armeabi-v7a", "modules": 1, "sigBypassLevel": 0,
            "native_loader_layout": "VERIFIED",
            "original_vendor_code_present": False,
            "signed_ephemeral_own_host_only": True,
            "runtime_not_yet_tested": True, "owner_phone_touched": False}


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True))
    except Exception as exc:
        reason = str(exc)
        reason = reason if re.fullmatch("[A-Z0-9_]{8,96}", reason) else \
                 "OWN_ARMV7_PRIVATE_NORMALIZATION_ERROR"
        print(json.dumps({"result": "OWN_ARMV7_STATIC_BLOCKED", "category": reason,
                          "owner_phone_touched": False}), file=sys.stderr)
        sys.exit(2)
