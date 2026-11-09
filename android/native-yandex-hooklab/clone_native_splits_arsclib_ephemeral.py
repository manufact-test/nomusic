#!/usr/bin/env python3
"""Ephemeral alternative native-Yandex split resource rebuild research.

Uses APKEditor/ARSCLib, NOT Apktool/aapt2 resources reconstruction.
Only runs in GitHub CI; never uploads, installs, or distributes third-party APKs.
The original device application, sessions, certificates, and Test.50 are untouched.
This is a STRUCTURAL feasibility gate; native audio / login are not tested.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import clone_native_splits_ephemeral as baseline

EDITOR_URL = "https://github.com/REAndroid/APKEditor/releases/download/V1.4.9/APKEditor-1.4.9.jar"
EDITOR_SHA256 = "a9cd40df818845456be6d696de6110c89edf4b0a0580cb83438ed6b25a366e67"
EDITOR_BYTES = 7733037


class TrialError(Exception):
    def __init__(self, stage: str, output: str = ""):
        super().__init__(stage)
        self.stage = stage
        # Offline tool diagnostics only, never app files, URLs, credentials or content.
        matched = [x.strip() for x in output.splitlines()
                   if re.search(r"exception|error|failed|missing|unsupported|not found|cannot|invalid",
                                x, re.IGNORECASE)]
        safe = []
        for line in matched[-5:]:
            line = re.sub(r"https?://\S+", "[URL]", line)
            line = re.sub(r"/(?:tmp|home|opt|runner)/\S+", "[PATH]", line)
            safe.append(line[:240])
        self.hints = safe


def run(command: list[str], stage: str, timeout: int = 240) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise TrialError(stage + "_TIMEOUT") from None
    if result.returncode:
        raise TrialError(stage + "_FAILED", result.stderr + "\n" + result.stdout)
    return result.stdout


def download_editor(destination: Path) -> None:
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(EDITOR_URL, timeout=90) as response, destination.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            total += len(chunk)
            if total > 9 * 1024 * 1024:
                raise TrialError("EDITOR_TOO_LARGE")
            target.write(chunk)
    if total != EDITOR_BYTES or digest.hexdigest() != EDITOR_SHA256:
        raise TrialError("EDITOR_PIN_MISMATCH")


def main() -> dict:
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise TrialError("EPHEMERAL_CI_ONLY")
    with tempfile.TemporaryDirectory(prefix="celikom-arsclib-gate-") as dirname:
        work = Path(dirname)
        archive = work / "pinned-original.xapk"
        length, digest = baseline.gpr.download(archive)
        if length != 60433885 or digest != baseline.ARCHIVE_SHA:
            raise TrialError("ORIGINAL_SOURCE_PIN_MISMATCH")
        apks = baseline.gpr.split_apks(archive, work)
        if len(apks) != 5:
            raise TrialError("EXACT_FIVE_SPLITS_REQUIRED")
        baseline.gpr.inspect_publisher(apks)
        editor = work / "APKEditor.jar"
        download_editor(editor)
        key = work / "ephemeral-research-only.jks"
        run(["keytool", "-genkeypair", "-storetype", "JKS",
             "-keystore", str(key), "-storepass", "ephemeral-lab-only",
             "-keypass", "ephemeral-lab-only", "-alias", "research",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "1",
             "-dname", "CN=CELIKOM Isolated Research, O=CELIKOM, C=XX"],
            "RESEARCH_KEY", 60)

        totals = {"package_identity": 0, "provider_authorities": 0,
                  "declared_permissions": 0, "non_component_identity_attributes": 0,
                  "unchanged_component_classes": 0}
        original_splits, rebuilt_splits = set(), set()
        checked = 0
        for index, apk in enumerate(apks):
            old = baseline.apkmeta(apk)
            if old.get("name") != baseline.SOURCE or old.get("versionCode") != "24026531":
                raise TrialError("ORIGINAL_SPLIT_METADATA_DRIFT")
            split = old.get("split", "")
            original_splits.add(split)
            decoded = work / ("arsc-decoded-" + str(index))
            # APKEditor has its own ARSCLib encoder, independent of Apktool's aapt2.
            # -dex keeps exact compiled original DEX rather than a smali round trip.
            run(["java", "-Xmx3g", "-jar", str(editor), "d", "-t", "xml",
                 "-dex", "-i", str(apk), "-o", str(decoded)],
                "ARSC_DECODE_SPLIT_" + str(index), 240)
            manifest = decoded / "AndroidManifest.xml"
            if not manifest.exists():
                raise TrialError("ARSC_MANIFEST_MISSING")
            payload = manifest.read_bytes()
            if not payload.lstrip().startswith(b"<"):
                raise TrialError("ARSC_MANIFEST_NOT_TEXT")
            try:
                edited, counts = baseline.rewrite_manifest(payload.decode("utf-8"))
            except Exception as exc:
                raise TrialError("ARSC_MANIFEST_REWRITE_" + type(exc).__name__.upper()) from None
            # Provider authorities must be globally unique across installed apps:
            # refuse a clone if ANY of the original registered authorities remains.
            ns = "{" + baseline.ANDROID + "}authorities"
            def provider_set(xml_bytes):
                root = baseline.ET.fromstring(xml_bytes)
                return {a.strip() for p in root.iter("provider")
                        for a in p.attrib.get(ns, "").split(";") if a.strip()}
            provider_collisions = provider_set(payload) & provider_set(edited)
            if provider_collisions:
                # ContentProvider authority names are public package metadata,
                # not user data; needed to identify side-by-side install conflicts.
                print(json.dumps({"split_index": index, "colliding_provider_authorities":
                                  sorted(provider_collisions)}, sort_keys=True))
                raise TrialError("ARSC_PROVIDER_AUTHORITY_COLLISION")
            manifest.write_bytes(edited)
            for kind, value in counts.items():
                totals[kind] += value
            unsigned = work / ("arsc-unsigned-" + str(index) + ".apk")
            run(["java", "-Xmx3g", "-jar", str(editor), "b", "-t", "xml",
                 "-i", str(decoded), "-o", str(unsigned)],
                "ARSC_REBUILD_SPLIT_" + str(index), 300)
            aligned = work / ("arsc-aligned-" + str(index) + ".apk")
            run([baseline.sdk_tool("zipalign"), "-f", "-p", "4",
                 str(unsigned), str(aligned)], "ARSC_ZIPALIGN", 60)
            run([baseline.sdk_tool("apksigner"), "sign",
                 "--ks", str(key), "--ks-pass", "pass:ephemeral-lab-only",
                 "--ks-key-alias", "research",
                 "--key-pass", "pass:ephemeral-lab-only",
                 "--min-sdk-version", "28", "--v4-signing-enabled", "false",
                 str(aligned)], "ARSC_SIGN", 80)
            new = baseline.apkmeta(aligned)
            if (new.get("name") != baseline.DEST or
                    new.get("versionCode") != "24026531" or
                    new.get("split", "") != split):
                raise TrialError("ARSC_PACKAGE_OR_SPLIT_METADATA_DRIFT")
            signature = run([baseline.sdk_tool("apksigner"), "verify",
                             "--print-certs", str(aligned)], "ARSC_SIGNATURE", 60)
            # SDK apksigner labels are version-specific ("V3.0 Signer: ..."
            # or "Signer #1 ..."). Match the certificate SHA-256 value, not its prefix.
            certificate_lines = [line for line in signature.splitlines()
                                 if "certificate" in line.lower() and "sha-256" in line.lower()]
            fingerprints = [match.group(0).lower()
                            for line in certificate_lines
                            if (match := re.search(r"\b[0-9a-fA-F]{64}\b", line))]
            if len(fingerprints) != 1 or fingerprints[0] == baseline.RUSTORE_SHA256_CERT:
                raise TrialError("ARSC_SIGNING_IDENTITY_INVALID", signature)
            if baseline.native_payload_hashes(apk) != baseline.native_payload_hashes(aligned):
                raise TrialError("ARSC_DEX_OR_NATIVE_PAYLOAD_DRIFT")
            rebuilt_splits.add(split)
            checked += 1
            print(json.dumps({"split_index": index, "structural_pass": True, "built": checked}))
        if original_splits != rebuilt_splits or len(rebuilt_splits) != 5:
            raise TrialError("ARSC_SPLIT_SET_DRIFT")
        report = {
            "verdict": "ARSC_STRUCTURAL_PASS_NOT_NATIVE_RUNTIME_PROOF",
            "tool": "REAndroid APKEditor 1.4.9 / ARSCLib",
            "source": "verified signed original 2026.10.3 #170gpr",
            "parallel_package": baseline.DEST,
            "rebuilt_split_count": checked,
            "provider_authorities_rewritten": totals["provider_authorities"],
            "component_java_classes_preserved": totals["unchanged_component_classes"],
            "dex_native_payload_byte_identical": True,
            "official_yandex_on_honor_touched": False,
            "play_protect_tested": False,
            "login_tested": False,
            "real_yandex_decoder_tested": False,
            "user_apks_published": False,
            "warning": "Static package identity is insufficient to prove runtime compatibility"
        }
    return report


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False))
    except TrialError as exc:
        print(json.dumps({"verdict": "ARSC_STRUCTURAL_BLOCKED", "stage": exc.stage,
                          "diagnostic": exc.hints, "user_apks_published": False},
                         sort_keys=True))
        sys.exit(2)
