#!/usr/bin/env python3
"""CI-only LSPatch packaging for our OWN independent ARMv7 host, not Yandex."""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APK = HERE / "armv7-loader-host/app/build/outputs/apk/debug/app-debug.apk"
PACKAGE = "pro.celikom.armv7loaderhost"
JAR_URL = "https://github.com/JingMatrix/LSPatch/releases/download/v1.2/lspatch-v1.2-487-release.jar"
JAR_SHA = "d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165"

def run(args, timeout=120):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if p.returncode:
        raise ValueError("TOOL_COMMAND_FAILED")
    return p.stdout

def sdk(name):
    home = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    if not home:
        raise ValueError("SDK_UNAVAILABLE")
    paths = sorted((Path(home) / "build-tools").glob("*/" + name))
    if not paths:
        raise ValueError("APK_TOOL_UNAVAILABLE")
    return str(paths[-1])

def apk_identity(path):
    output = run([sdk("aapt"), "dump", "badging", str(path)])
    line = next((x for x in output.splitlines() if x.startswith("package:")), "")
    meta = dict(re.findall(r"(\w+)='([^']*)'", line))
    return meta.get("name"), meta.get("versionCode"), meta.get("split", "")

def signed_sha(path):
    out = run([sdk("apksigner"), "verify", "--verbose", "--print-certs", str(path)])
    if not ("Verified using v2 scheme (APK Signature Scheme v2): true" in out
            or "Verified using v3 scheme (APK Signature Scheme v3): true" in out):
        raise ValueError("SIGNING_VERIFICATION_FAILED")
    certs = re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F:]+)", out)
    if len(certs) != 1:
        raise ValueError("SIGNER_COUNT_INVALID")
    return certs[0].lower().replace(":", "")

def check_host(path, patched=False):
    if apk_identity(path) != (PACKAGE, "1", ""):
        raise ValueError("PACKAGE_MISMATCH")
    tree = run([sdk("aapt"), "dump", "xmltree", str(path), "AndroidManifest.xml"])
    if "E: uses-permission" in tree or "ru.yandex.music" in tree:
        raise ValueError("OWNED_HOST_PERMISSIONS_OR_IDENTITY_INVALID")
    with zipfile.ZipFile(path) as archive:
        native = [n for n in archive.namelist()
                  if n.startswith("lib/") and n.endswith(".so")]
        if not native or any(not n.startswith("lib/armeabi-v7a/") for n in native):
            raise ValueError("HOST_ABI_NOT_ARMV7_ONLY")
        elf = archive.read("lib/armeabi-v7a/libcelikom_host_probe.so")[:20]
        if len(elf) != 20 or elf[:4] != b"\x7fELF" or elf[4] != 1 or \
                struct.unpack_from("<H", elf, 18)[0] != 40:
            raise ValueError("HOST_ARMV7_ELF_INVALID")
        if patched:
            names = archive.namelist()
            if "assets/lspatch/config.json" not in names:
                raise ValueError("LSPATCH_RUNTIME_NOT_EMBEDDED")
            if "assets/lspatch/so/armeabi-v7a/liblspatch.so" not in names:
                raise ValueError("LSPATCH_ARMV7_LOADER_MISSING")
            if any(n.startswith("assets/lspatch/modules/") and n.endswith(".apk")
                   for n in names):
                raise ValueError("UNEXPECTED_MODULE_EMBEDDED")
    return True

def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("ONLY_SUPPORTED_IN_EPHEMERAL_CI")
    check_host(APK)
    original_cert = signed_sha(APK)
    with tempfile.TemporaryDirectory(prefix="celikom-own-arm-loader-") as tmp:
        root = Path(tmp)
        jar = root / "lspatch.jar"
        with urllib.request.urlopen(JAR_URL, timeout=90) as stream, jar.open("wb") as out:
            total = 0
            while True:
                chunk = stream.read(1024*1024)
                if not chunk: break
                total += len(chunk)
                if total > 20*1024*1024: raise ValueError("PATCHER_TOO_LARGE")
                out.write(chunk)
        if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA:
            raise ValueError("PATCHER_CHECKSUM_CHANGED")
        store = root / "lab-keystore.jks"
        run(["keytool", "-genkeypair", "-storetype", "JKS", "-keystore", str(store),
             "-storepass", "owned-test-only", "-keypass", "owned-test-only",
             "-alias", "celikomlab", "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "30",
             "-dname", "CN=CELIKOM Owned ARMv7 Lab, O=CELIKOM, C=XX"], 80)
        output = root / "patched"
        output.mkdir()
        run(["java", "-jar", str(jar), "-k", str(store), "owned-test-only",
             "celikomlab", "owned-test-only", "-o", str(output),
             "-l", "0", str(APK)], 500)
        produced = list(output.glob("*.apk"))
        if len(produced) != 1:
            raise ValueError("PATCHER_OUTPUT_COUNT_INVALID")
        patched = produced[0]
        check_host(patched, patched=True)
        patched_cert = signed_sha(patched)
        if patched_cert == original_cert:
            raise ValueError("PATCHED_CERT_NOT_SEPARATE")
        artifact = os.getenv("CELIKOM_OWNED_ARTIFACT_DIR")
        if artifact:
            dest = Path(artifact).resolve()
            root_temp = Path(os.environ["RUNNER_TEMP"]).resolve()
            if root_temp not in dest.parents or dest.exists():
                raise ValueError("INVALID_ARTIFACT_LOCATION")
            dest.mkdir(parents=True, mode=0o700)
            shutil.copyfile(patched, dest / "CELIKOM-ARMv7-LOADER-ONLY-Test.apk")
        print(json.dumps({
            "verdict": "OWN_SOURCE_ARMV7_PATCHED_STATIC_PASS_NO_DEVICE_RUN",
            "package": PACKAGE, "native_abi": "armeabi-v7a",
            "permissions": 0, "sigbypass": 0, "modules_embedded": 0,
            "yandex_code_included": False,
            "yandex_modified_or_installed": False, "runtime_tested": False,
            "play_protect_verdict": "NOT_TESTED_ON_DEVICE",
            "artifact_prepared": bool(artifact),
        }, sort_keys=True))
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        detail = str(exc)
        safe = detail if re.fullmatch("[A-Z_]{8,70}", detail) else "CI_STAGE_FAILED"
        print(json.dumps({"verdict": "BLOCKED", "reason": safe}), file=sys.stderr)
        sys.exit(2)
