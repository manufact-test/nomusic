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
WITNESS = os.getenv("CELIKOM_OWN_WITNESS") == "1"
AUDIO = os.getenv("CELIKOM_OWN_AUDIO") == "1"
X86 = os.getenv("CELIKOM_OWN_X86_BRIDGE") == "1"
if sum((WITNESS, AUDIO, X86)) > 1:
    raise ValueError("INCOMPATIBLE_TEST_VARIANTS")
PACKAGE = ("pro.celikom.armv7loaderhost.x86control" if X86 else
           "pro.celikom.armv7loaderhost.audio" if AUDIO else
           "pro.celikom.armv7loaderhost.witness" if WITNESS else "pro.celikom.armv7loaderhost")
MODULE = HERE / "armv7-witness-module/app/build/outputs/apk/debug/app-debug.apk"
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
    certs = set()
    for line in out.splitlines():
        if "certificate SHA-256 digest:" not in line:
            continue
        digest = line.split("certificate SHA-256 digest:", 1)[1].strip()
        digest = digest.replace(":", "").lower()
        if re.fullmatch(r"[0-9a-f]{64}", digest):
            certs.add(digest)
    if len(certs) != 1:
        raise ValueError("SIGNER_COUNT_INVALID")
    return next(iter(certs))

def check_host(path, patched=False):
    if apk_identity(path) != (PACKAGE, "1", ""):
        raise ValueError("PACKAGE_MISMATCH")
    tree = run([sdk("aapt"), "dump", "xmltree", str(path), "AndroidManifest.xml"])
    if "E: uses-permission" in tree or "ru.yandex.music" in tree:
        raise ValueError("OWNED_HOST_PERMISSIONS_OR_IDENTITY_INVALID")
    with zipfile.ZipFile(path) as archive:
        native = [n for n in archive.namelist()
                  if n.startswith("lib/") and n.endswith(".so")]
        expected_abi = "x86" if X86 else "armeabi-v7a"
        expected_machine = 3 if X86 else 40
        if not native or any(not n.startswith("lib/" + expected_abi + "/") for n in native):
            raise ValueError("HOST_UNEXPECTED_OWN_ABI")
        elf = archive.read("lib/" + expected_abi + "/libcelikom_host_probe.so")[:20]
        if len(elf) != 20 or elf[:4] != b"\x7fELF" or elf[4] != 1 or \
                struct.unpack_from("<H", elf, 18)[0] != expected_machine:
            raise ValueError("HOST_NATIVE_ELF_INVALID")
        if patched:
            names = archive.namelist()
            if "assets/lspatch/config.json" not in names:
                raise ValueError("LSPATCH_RUNTIME_NOT_EMBEDDED")
            if "assets/lspatch/so/armeabi-v7a/liblspatch.so" not in names:
                raise ValueError("LSPATCH_ARMV7_LOADER_MISSING")
            embedded = [n for n in names if n.startswith("assets/lspatch/modules/") and n.endswith(".apk")]
            if (WITNESS or AUDIO) and len(embedded) != 1:
                raise ValueError("WITNESS_MODULE_NOT_EMBEDDED")
            if not (WITNESS or AUDIO) and embedded:
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
        args = ["java", "-jar", str(jar), "-k", str(store), "owned-test-only",
                "celikomlab", "owned-test-only"]
        signed_module = None
        if WITNESS or AUDIO:
            if not MODULE.is_file():
                raise ValueError("OWN_MODULE_MISSING")
            with zipfile.ZipFile(MODULE) as mz:
                scopes = set(mz.read("META-INF/xposed/scope.list").decode().splitlines())
                if scopes != {"pro.celikom.armv7loaderhost.witness", "pro.celikom.armv7loaderhost.audio"} or PACKAGE not in scopes:
                    raise ValueError("OWN_SOURCE_SCOPES_MISMATCH")
                if mz.read("META-INF/xposed/java_init.list").decode().strip() != "pro.celikom.armv7witnessmodule.HookWitnessEntry":
                    raise ValueError("WITNESS_ENTRY_MISMATCH")
                if "minApiVersion=102" not in mz.read("META-INF/xposed/module.prop").decode():
                    raise ValueError("WITNESS_API_INCOMPATIBLE")
            signed_module = root / "own-module.apk"
            shutil.copyfile(MODULE, signed_module)
            run([sdk("apksigner"), "sign", "--ks", str(store),
                 "--ks-pass", "pass:owned-test-only", "--ks-key-alias", "celikomlab",
                 "--key-pass", "pass:owned-test-only", "--min-sdk-version", "28",
                 "--v4-signing-enabled", "false", str(signed_module)], 90)
            if signed_sha(signed_module) == original_cert:
                raise ValueError("WITNESS_MODULE_SIGNER_INVALID")
            args += ["-m", str(signed_module)]
        args += ["-o", str(output), "-l", "0", str(APK)]
        run(args, 500)
        produced = list(output.glob("*.apk"))
        if len(produced) != 1:
            raise ValueError("PATCHER_OUTPUT_COUNT_INVALID")
        patched = produced[0]
        check_host(patched, patched=True)
        patched_cert = signed_sha(patched)
        if patched_cert == original_cert:
            raise ValueError("PATCHED_CERT_NOT_SEPARATE")
        if WITNESS or AUDIO:
            if patched_cert != signed_sha(signed_module):
                raise ValueError("WITNESS_SIGNER_MISMATCH")
            with zipfile.ZipFile(patched) as z:
                matches = [n for n in z.namelist()
                           if re.fullmatch(r"assets/lspatch/modules/[^/]+[.]apk", n)]
                if len(matches) != 1 or hashlib.sha256(z.read(matches[0])).digest() != hashlib.sha256(signed_module.read_bytes()).digest():
                    raise ValueError("EXACT_WITNESS_MODULE_NOT_EMBEDDED")
        artifact = os.getenv("CELIKOM_OWNED_ARTIFACT_DIR")
        if artifact:
            dest = Path(artifact).resolve()
            root_temp = Path(os.environ["RUNNER_TEMP"]).resolve()
            if root_temp not in dest.parents or dest.exists():
                raise ValueError("INVALID_ARTIFACT_LOCATION")
            dest.mkdir(parents=True, mode=0o700)
            shutil.copyfile(patched, dest / ("CELIKOM-X86-LOADER-ONLY-Test.apk" if X86 else "CELIKOM-ARMv7-AUDIO-SMOKE-Test.apk" if AUDIO else "CELIKOM-ARMv7-HOOK-WITNESS-Test.apk" if WITNESS else "CELIKOM-ARMv7-LOADER-ONLY-Test.apk"))
        print(json.dumps({
            "verdict": ("OWN_X86_NATIVE_PATCHED_STATIC_PASS_NO_DEVICE_RUN" if X86 else "OWN_AUDIO_SMOKE_STATIC_PASS_NO_DEVICE_RUN" if AUDIO else "OWN_MODULE_WITNESS_STATIC_PASS_NO_DEVICE_RUN" if WITNESS else "OWN_SOURCE_ARMV7_PATCHED_STATIC_PASS_NO_DEVICE_RUN"),
            "package": PACKAGE, "native_abi": "x86" if X86 else "armeabi-v7a",
            "permissions": 0, "sigbypass": 0, "modules_embedded": 1 if (WITNESS or AUDIO) else 0,
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
