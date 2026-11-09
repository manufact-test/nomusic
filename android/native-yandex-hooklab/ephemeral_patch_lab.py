#!/usr/bin/env python3
"""Ephemeral rootless prototype assembly, NO distributable or phone installer.

Take exact Yandex 2026.10.3 #170gpr signed split APKs, independently verify each
publisher signature, and embed a *read-only* CELIKOM Xposed module with upstream
JingMatrix/LSPatch v1.2 build 487 pinned by SHA256. Disable LSPatch signature
bypass (level 0); NEVER spoof original signing, suppress Play Protect, or try
to install over a store-signed Yandex. All APKs deleted after CI.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "tools" / "android-native-gate1"
sys.path.insert(0, str(TOOLS))
import audit_gpr_apkpure_once as gpr
from audit_rustore_host_once import sdk_tool, RUSTORE_SHA256_CERT
from inspect_android_host import Dex, DEX_MAX
from trace_native_callers import method_definitions

PATCHER_URL = "https://github.com/JingMatrix/LSPatch/releases/download/v1.2/lspatch-v1.2-487-release.jar"
PATCHER_SHA256 = "d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165"
PACKAGE = "ru.yandex.music"
VERSION_CODE = 24026531
MODULE_PATH = HERE / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"


def run(cmd:list[str], *, timeout:int=240)->str:
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    if proc.returncode:
        # Log only exception-class/status lines, NEVER upstream URLs, call arguments,
        # account data, arbitrary stdout, local files or signing passwords.
        safe = []
        for raw in (proc.stderr+"\n"+proc.stdout).splitlines():
            line = raw.strip()
            if any(token in line for token in ("Exception", "Error", "ERROR", "Unsupported",
                                              "failed", "Failed", "NoClassDef", "Caused by",
                                              "invalid", "Invalid", "not found", "Not found")):
                line = re.sub(r"https?://[^ ]+", "<redacted-url>", line)
                line = re.sub(r"/tmp/[^ ]+", "<redacted-tmp>", line)
                line = line.replace("celikom-test-only", "<redacted-lab-key>")
                safe.append(line[:180])
        diagnostics = " | ".join(safe[-7:]) or "no safe diagnostics"
        raise RuntimeError(f"{Path(cmd[0]).name} returned {proc.returncode}: {diagnostics}")
    return proc.stdout

def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            part=f.read(1024*1024)
            if not part:break
            h.update(part)
    return h.hexdigest()

def apk_id(path:Path):
    out=run([sdk_tool("aapt"),"dump","badging",str(path)],timeout=60)
    line=next((x for x in out.splitlines() if x.startswith("package:")),None)
    if line is None:raise ValueError("APK package metadata missing")
    values=dict(re.findall(r"(\w+)='([^']*)'",line))
    return values.get("name"),values.get("versionCode"),values.get("split",""),values.get("versionName")

def signer(path:Path):
    stdout=run([sdk_tool("apksigner"),"verify","--verbose","--print-certs",str(path)],timeout=70)
    values={h.replace(":","").lower() for h in re.findall(
        r"(?:V\d+(?:\.\d+)? Signer:|Signer #\d+) certificate SHA-256 digest:\s*([0-9a-fA-F:]+)",stdout)}
    if len(values)!=1:raise ValueError("Missing or multiple signing identities")
    if "Verified using v2 scheme (APK Signature Scheme v2): true" not in stdout and \
       "Verified using v3 scheme (APK Signature Scheme v3): true" not in stdout:
        raise ValueError("APK v2/v3 verification missing")
    return values.pop()

def verify_observer_binary_methods(base_apk:Path):
    """Fail closed unless the exact published GPR DEX contains both hook targets."""
    expected={
        ("Lsw7;","y0","(Lcom/yandex/music/shared/player/content/remote/fileinfo/FileInfoDto;Z)Leed;"),
        ("Lsw7;","z0","(Lcom/yandex/music/shared/player/content/remote/fileinfo/OldGetFileInfoDto;Z)Leed;"),
    }
    found=set()
    with zipfile.ZipFile(base_apk) as z:
        for item in z.infolist():
            if not re.fullmatch(r"classes\d*\.dex",item.filename):
                continue
            if item.file_size>DEX_MAX:
                raise ValueError("DEX size exceeds static hook preflight cap")
            dex=Dex(z.read(item))
            declared=set(dex.defined_classes())
            if "Lsw7;" not in declared:
                continue
            for idx,code_offset in method_definitions(dex):
                triple=dex.method(idx)
                if triple in expected:
                    found.add(triple)
    if found!=expected:
        raise ValueError("Exact two source conversion methods not defined in pinned #170gpr host")
    return sorted(f"{name}"+signature for cls,name,signature in found)


def original_native_architectures(apks:list[Path]):
    found=set()
    for apk in apks:
        with zipfile.ZipFile(apk) as z:
            for n in z.namelist():
                if n.startswith("lib/") and n.endswith(".so") and n.count("/")>=2:
                    found.add(n.split("/")[1])
    return sorted(found)


def main():
    if not MODULE_PATH.is_file():
        raise ValueError("CELIKOM observer module not built")
    if signer(MODULE_PATH)==RUSTORE_SHA256_CERT:
        raise ValueError("Lab module must NEVER claim original Yandex identity")
    with zipfile.ZipFile(MODULE_PATH) as z:
        init=z.read("META-INF/xposed/java_init.list").decode().strip()
        scope=z.read("META-INF/xposed/scope.list").decode().strip()
        prop=z.read("META-INF/xposed/module.prop").decode()
        if (init!="pro.celikom.yandex.nativehooklab.NativeHookEntry"
                or scope!=PACKAGE or "minApiVersion=102" not in prop):
            raise ValueError("Module scope/entry/API manifest mismatch")
    with tempfile.TemporaryDirectory(prefix="celikom-offline-patchlab-") as folder:
        root=Path(folder)
        # One-time throwaway test key: no key enters Git, no device/release update
        # path is implied. Sign module and patched splits with the SAME lab key.
        keystore=root/"ephemeral-lab-key.jks"
        lab_pass="celikom-test-only"
        lab_alias="celikomlab"
        run(["keytool","-genkeypair","-keystore",str(keystore),
             "-storetype","JKS","-storepass",lab_pass,"-keypass",lab_pass,
             "-alias",lab_alias,"-keyalg","RSA","-keysize","2048",
             "-validity","30","-dname","CN=CELIKOM Disposable Test Only, O=CELIKOM, C=XX"],timeout=70)
        module=root/"celikom-observer-module.apk"
        shutil.copyfile(MODULE_PATH,module)
        run([sdk_tool("apksigner"),"sign","--ks",str(keystore),
             "--ks-pass","pass:"+lab_pass,"--ks-key-alias",lab_alias,
             "--key-pass","pass:"+lab_pass,"--min-sdk-version","28",
             "--v4-signing-enabled","false",str(module)],timeout=80)
        lab_sig=signer(module)
        if lab_sig==RUSTORE_SHA256_CERT:
            raise ValueError("Unexpected signing identity collision")
        incoming=root/"exact-owner-build.xapk"
        nbytes,host_sha=gpr.download(incoming)
        originals=gpr.split_apks(incoming,root)
        gpr.inspect_publisher(originals)  # Checks EXACT version, original publisher and package.
        orig=[(apk_id(p),p) for p in originals]
        exact_base=next((p for p in originals
                         if not apk_id(p)[2]),None)
        if exact_base is None:
            raise ValueError("Missing native Yandex base APK")
        method_contract=verify_observer_binary_methods(exact_base)
        native_abis=original_native_architectures(originals)
        if len(orig)!=5 or len({v[2] for v,p in orig})!=5:
            raise ValueError("Expected five distinct native Yandex splits")
        for identity,p in orig:
            if identity[0]!=PACKAGE or identity[1]!=str(VERSION_CODE) or signer(p)!=RUSTORE_SHA256_CERT:
                raise ValueError("Original split identity drift or signature failure")
        # Normalize filenames; source content unchanged, patcher receives base first.
        prepared=root/"original-inputs";prepared.mkdir()
        ordered=[]
        for identity,p in sorted(orig,key=lambda x:(bool(x[0][2]),x[0][2])):
            split=identity[2]
            dest=prepared/("base.apk" if not split else "split_"+split+".apk")
            if not re.fullmatch(r"[a-zA-Z0-9_.-]*",split):
                raise ValueError("Untrusted split name")
            dest.write_bytes(p.read_bytes())
            ordered.append(dest)
        jar=root/"lspatch-release.jar"
        req=urllib.request.Request(PATCHER_URL,headers={"User-Agent":"CELIKOM-rootless-lab/1.0"})
        with urllib.request.urlopen(req,timeout=100) as stream,jar.open("wb") as out:
            count=0
            while True:
                block=stream.read(1024*1024)
                if not block:break
                count+=len(block)
                if count>20*1024*1024:raise ValueError("Unexpected patcher size")
                out.write(block)
        if sha(jar)!=PATCHER_SHA256:
            raise ValueError("LSPatch release digest mismatch")
        stage=root/"patched"
        stage.mkdir()
        # Level 0: explicitly DISABLE LSPatch's signature impersonation/spoofing.
        # Signature mismatch may prevent Yandex login. Stop instead of bypassing.
        run(["java","-jar",str(jar),"-k",str(keystore),lab_pass,lab_alias,lab_pass,
             "-m",str(module),"-o",str(stage),"-l","0",*map(str,ordered)],timeout=500)
        patched=sorted(stage.glob("*.apk"))
        if len(patched)!=len(originals):
            raise ValueError("Patched split count differs from original")
        identities={v[:3] for v,p in orig}
        outputs={apk_id(p)[:3] for p in patched}
        if outputs!=identities:
            raise ValueError("Patch changed package/version or split composition")
        if {signer(p) for p in patched}!={lab_sig}:
            raise ValueError("Patched split signer differs from lab module")
        base=next(p for p in patched if not apk_id(p)[2])
        with zipfile.ZipFile(base) as z:
            names=z.namelist()
            if "assets/lspatch/config.json" not in names:
                raise ValueError("Missing embedded LSPatch runtime configuration")
            embed=[n for n in names if re.fullmatch(r"assets/lspatch/modules/[^/]+\.apk",n)]
            if len(embed)!=1:
                raise ValueError("Missing or multiple embedded CELIKOM modules")
            content=z.read(embed[0])
            if hashlib.sha256(content).hexdigest()!=sha(module):
                raise ValueError("Embedded CELIKOM module does not match signed module")
            raw=z.read("assets/lspatch/config.json")
            cfg=json.loads(raw.decode("utf-8"))
            # Defensive validation independent of vendor JSON field spelling.
            if any(k in str(cfg).lower() for k in ("password","oauth","authtoken")):
                raise ValueError("Suspicious patched runtime configuration")
        # Optional ONLY for a fresh, isolated CI emulator started in the same job.
        # The runner deletes these original/patched APKs in an always-run cleanup
        # step; public Actions artifacts are never uploaded.
        emulator_dir=os.getenv("CELIKOM_EMULATOR_TEST_DIR")
        if emulator_dir:
            if os.getenv("GITHUB_ACTIONS")!="true":
                raise ValueError("Ephemeral emulator export allowed only in isolated GitHub CI")
            runner_temp=os.getenv("RUNNER_TEMP")
            if not runner_temp:
                raise ValueError("Missing ephemeral runner root")
            base=Path(runner_temp).resolve()
            target=Path(emulator_dir).resolve()
            if target == base or base not in target.parents or target.exists():
                raise ValueError("Emulator staging path must be new and strictly inside RUNNER_TEMP")
            target.mkdir(parents=True,mode=0o700)
            for i,p in enumerate(sorted(patched)):
                shutil.copyfile(p,target/f"native-split-{i}.apk")

        print(json.dumps({
            "result":"PATCHED_EXACT_NATIVE_HOST_BUNDLE_STRUCTURALLY_VERIFIED_NO_RUNTIME",
            "base_original_package":PACKAGE,
            "original_version":"2026.10.3 #170gpr",
            "original_code":VERSION_CODE,
            "original_publisher_signer_sha256":RUSTORE_SHA256_CERT,
            "mirror_archive_sha256":host_sha,
            "mirror_size":nbytes,
            "patcher":"JingMatrix/LSPatch v1.2-487",
            "patcher_sha256":PATCHER_SHA256,
            "signature_spoof_level":0,
            "splits":len(patched),
            "split_ids":sorted([v[2] or "base" for v,p in orig]),
            "native_abis":native_abis,
            "verified_exact_method_contracts":method_contract,
            "embedded_module":"CELIKOM read-only FileInfoDto observer",
            "module_sha256":sha(module),
            "lab_signer_sha256":lab_sig,
            "host_modified_in_ci_only":True,
            "host_installed":False,
            "runtime_hook_evidence":False,
            "play_protect_tested":False,
            "retained_binaries":("RUNNER_TEMP_ONLY_FOR_IMMEDIATE_EMULATOR" if emulator_dir else False)
        },indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        print("ISOLATED_NATIVE_PATCHLAB_NO_GO: "+str(e)[:250],file=sys.stderr)
        sys.exit(2)
