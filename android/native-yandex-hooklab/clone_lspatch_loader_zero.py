#!/usr/bin/env python3
"""Isolated LSPatch metaloader A/B, zero signature bypass, NO modules.

Only wraps a previously verified ONE-APK independent-signature clone under
CI in disposable ephemeral emulator. The original issuer-signed Yandex APK
is NEVER patched, installed over, uploaded, authenticated or modified.
This does not test audio and CANNOT be sent to user's HONOR 50.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
import urllib.request
from pathlib import Path

from merge_lab_splits_ephemeral import fingerprint, verify_merged_payloads
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
        except (ValueError, UnicodeError):
            raise arsc.TrialError("METALOADER_CONFIG_INVALID") from None
        if (type(cfg.get("sigBypassLevel")) is not int or
                cfg["sigBypassLevel"] != 0):
            raise arsc.TrialError("NONZERO_SIGNATURE_BYPASS_PROHIBITED")
        if cfg.get("useManager") is not False:
            raise arsc.TrialError("METALOADER_EXTERNAL_MANAGER_NOT_ALLOWED")
        # Compare original code and native libs inside the embedded host, not
        # outer stub classes.dex (which deliberately contains loader, NOT host).
        nested_data = z.read("assets/lspatch/origin.apk")
        if len(nested_data) > 128 * 1024 * 1024:
            raise arsc.TrialError("METALOADER_ORIGIN_TOO_LARGE")
        import io
        with zipfile.ZipFile(io.BytesIO(nested_data)) as original_zip, \
             zipfile.ZipFile(prior) as prior_zip:
            def payload(zf):
                return {name: hashlib.sha256(zf.read(name)).hexdigest()
                        for name in zf.namelist() if
                        re.fullmatch(r"classes\d*\.dex", name)
                        or name.startswith("lib/") and name.endswith(".so")}
            actual, expected = payload(original_zip), payload(prior_zip)
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
    arsc.run(
        ["java", "-jar", str(patcher), "-k", str(key),
         "ephemeral-lab-only", "research", "ephemeral-lab-only",
         "-o", str(stage), "-l", "0", str(clone)],
        "LSPATCH_CLONE_BOOTSTRAP_ZERO_BYPASS", 500)
    results = list(stage.glob("*.apk"))
    if len(results) != 1:
        raise arsc.TrialError("METALOADER_NOT_EXACT_ONE_APK")
    report = check_zero_loader(results[0], clone, expected_signer, arsc)
    return results[0], report
