#!/usr/bin/env python3
"""Ephemeral read-only scan of *published RuStore* Yandex Music Android variant.

Only legitimate store URLs, TLS and signing verification. Never installs,
runs, repacks, publishes APKs, reads app private data or obtains credentials.
RuStore #rur is NOT proof of compatibility with owner's Google Play #gpr.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from inspect_android_host import DEX_MAX, Dex, DexError
from trace_native_callers import dex_callers

PACKAGE = "ru.yandex.music"
CODE = 24026531
RUSTORE_VERSION = "2026.10.3 #170rur"
RUSTORE_SHA256_CERT = "aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba"
BASE = "https://backapi.rustore.ru"
MAX_DOWNLOAD = 160 * 1024 * 1024
HEADERS = {"ruStoreVerCode": "1000", "Accept": "application/json",
           "User-Agent": "CELIKOM-readonly-compatibility-research/1.0"}
# Explicit transport whitelist. Additional hosts require source review; never auto-follow.
ALLOWED_SUFFIXES = ("rustore.ru", "vk.com", "vkuser.net", "vk-cdn.net",
                    "vk-cdn.com", "vkcdn.ru", "mycdn.me")

def accepted_url(url):
    p = urllib.parse.urlsplit(url)
    h = (p.hostname or "").lower()
    if p.scheme != "https" or not h or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Non-HTTPS or suspicious RuStore download URL")
    if not any(h == suffix or h.endswith("." + suffix) for suffix in ALLOWED_SUFFIXES):
        raise ValueError("Unexpected store download domain: " + h)
    return url

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        accepted_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

OPENER = urllib.request.build_opener(SafeRedirect())

def request_json(url, post=None):
    accepted_url(url)
    raw = json.dumps(post).encode("utf-8") if post is not None else None
    headers = dict(HEADERS)
    if raw is not None: headers["Content-Type"] = "application/json; charset=utf-8"
    with OPENER.open(urllib.request.Request(url, headers=headers, data=raw), timeout=35) as response:
        if response.status != 200: raise ValueError("Store API HTTP " + str(response.status))
        payload = response.read(1024 * 1024 + 1)
    if len(payload) > 1024 * 1024: raise ValueError("Store metadata exceeds 1MiB")
    return json.loads(payload)

def official_metadata():
    root = request_json(BASE + "/applicationData/overallInfo/" + PACKAGE)
    body = root.get("body") or {}
    if body.get("packageName") != PACKAGE:
        raise ValueError("Unexpected package in official store")
    if body.get("versionName") != RUSTORE_VERSION or body.get("versionCode") != CODE:
        raise ValueError("Store is no longer pinned to reviewed variant")
    if str(body.get("signature") or "").lower().replace(":", "") != RUSTORE_SHA256_CERT:
        raise ValueError("Store metadata signing claim changed; stop")
    app_id = body.get("appId")
    if not isinstance(app_id, int) or app_id <= 0:
        raise ValueError("Missing official store appId")
    return app_id

def store_file_url(app_id):
    data = request_json(BASE + "/v3/showcase/apps/download-link", {
        "appId": app_id, "firstInstall": True, "mobileServices": ["GMS"],
        "supportedAbis": ["arm64-v8a"], "screenDensity": 480,
        "supportedLocales": ["ru"], "sdkVersion": 33, "withoutSplits": False
    })
    urls = data.get("downloadUrls")
    if urls is None: urls = (data.get("body") or {}).get("downloadUrls")
    if not isinstance(urls, list) or not urls:
        raise ValueError("Official store returned no download URLs")
    entry = urls[0]
    if not isinstance(entry, dict):
        raise ValueError("Unexpected download URL shape")
    url = entry.get("url")
    if not isinstance(url, str):
        raise ValueError("Store URL is missing")
    return accepted_url(url)

def download_temp(url, dest):
    accepted_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    total = 0
    digest = hashlib.sha256()
    with OPENER.open(req, timeout=90) as response, dest.open("wb") as out:
        if response.status != 200: raise ValueError("APK download HTTP " + str(response.status))
        declared = int(response.headers.get("Content-Length") or "0")
        if declared > MAX_DOWNLOAD: raise ValueError("Official store file too large")
        while True:
            block = response.read(1024 * 1024)
            if not block: break
            total += len(block)
            if total > MAX_DOWNLOAD: raise ValueError("Download exceeded size cap")
            digest.update(block)
            out.write(block)
    if total < 1024: raise ValueError("Store download unexpectedly short")
    if not zipfile.is_zipfile(dest): raise ValueError("Not an APK/APKS/ZIP container")
    return total, digest.hexdigest()

def sdk_tool(name):
    android = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    if not android: raise ValueError("Android SDK unavailable for signature verification")
    base = Path(android) / "build-tools"
    candidates = sorted(base.glob("*/" + name), reverse=True)
    if not candidates: raise ValueError(name + " unavailable")
    return str(candidates[0])

def signer_digest(apk, apksigner):
    p = subprocess.run([apksigner, "verify", "--verbose", "--print-certs", str(apk)],
                       text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=50)
    if p.returncode: raise ValueError("APK signature verification FAILED")
    hits = re.findall(r"(?:V\d+(?:\.\d+)? Signer|Signer #\d+) certificate SHA-256 digest:\s*([a-fA-F0-9:]+)", p.stdout)
    signers = {h.replace(":", "").lower() for h in hits}
    if signers != {RUSTORE_SHA256_CERT}:
        print("SIGNER_DEBUG: cert_sha256=" + json.dumps(sorted(signers)), file=sys.stderr)
        raise ValueError("Unexpected APK signing certificate set")
    digest = RUSTORE_SHA256_CERT
    if not ("Verified using v2 scheme (APK Signature Scheme v2): true" in p.stdout or
            "Verified using v3 scheme (APK Signature Scheme v3): true" in p.stdout):
        raise ValueError("APK v2/v3 verified signature missing")
    return digest

def manifest_version(apk, aapt):
    p = subprocess.run([aapt, "dump", "badging", str(apk)], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    if p.returncode: raise ValueError("Bad APK manifest/package")
    match = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'",
                      p.stdout, re.MULTILINE)
    if not match: raise ValueError("No Android manifest package/version")
    name, code, version = match.groups()
    if name != PACKAGE or int(code) != CODE or version != RUSTORE_VERSION:
        raise ValueError("App APK version does not match RuStore inventory")
    return version

def scan(apk):
    output = {"classes": 0, "method_ids": 0, "factory_refs": 0,
              "factory_invoke_calls": 0, "incomplete_methods": 0, "dex_count": 0}
    with zipfile.ZipFile(apk) as archive:
        dexnames = sorted(n for n in archive.namelist()
                          if re.fullmatch(r"classes\d*\.dex", n))
        if not dexnames: raise ValueError("Base APK has no DEX")
        for name in dexnames:
            info = archive.getinfo(name)
            if info.file_size > DEX_MAX: raise ValueError("Large DEX entry")
            dexbytes = archive.read(info)
            d = Dex(dexbytes)
            calls = dex_callers(dexbytes)
            output["classes"] += d.class_count
            output["method_ids"] += d.method_count
            output["factory_refs"] += calls["target_refs"]
            output["factory_invoke_calls"] += calls["call_sites"]
            output["incomplete_methods"] += len(calls["anomalies"])
            output["dex_count"] += 1
    return output

def main():
    try:
        appid = official_metadata()
        url = store_file_url(appid)
        # URL/token is deliberately never printed to Actions logs.
        with tempfile.TemporaryDirectory(prefix="celikom-rustore-readonly-") as temp:
            temp = Path(temp)
            path = temp / "store_package.zip"
            size, sha = download_temp(url, path)
            print("OFFICIAL_STORE_TEMP_DOWNLOAD: bytes=" + str(size) + " sha256=" + sha)
            with zipfile.ZipFile(path) as outer:
                if "classes.dex" in outer.namelist():
                    apk_paths = [path]
                else:
                    members = [x for x in outer.infolist() if x.filename.lower().endswith(".apk")]
                    if len(members) > 24: raise ValueError("Too many APK splits")
                    apk_paths = []
                    for i, item in enumerate(members):
                        if item.file_size > MAX_DOWNLOAD: raise ValueError("Embedded APK too large")
                        ap = temp / ("part-" + str(i) + ".apk")
                        with outer.open(item) as src, ap.open("wb") as out:
                            shutil.copyfileobj(src, out)
                        apk_paths.append(ap)
            if not apk_paths: raise ValueError("No APK splits to inspect")
            print("OFFICIAL_STORE_ARCHIVE: apk_splits=" + str(len(apk_paths)))
            signer = sdk_tool("apksigner")
            aapt = sdk_tool("aapt")
            for apk in apk_paths:
                signer_digest(apk, signer)
            bases = []
            for apk in apk_paths:
                try:
                    manifest_version(apk, aapt)
                    bases.append(apk)
                except ValueError as exc:
                    if "No Android manifest package/version" in str(exc):
                        continue
                    # Config splits may have another versionName, but package identity must remain exact.
                    p = subprocess.run([aapt, "dump", "badging", str(apk)], text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
                    if p.returncode or "name='" + PACKAGE + "'" not in p.stdout:
                        raise ValueError("Unexpected split APK package")
            if not bases: raise ValueError("No version-matched base APK")
            results = [scan(ap) for ap in bases]
            print(json.dumps({
                "source": "Official RuStore public Android app distribution",
                "package": PACKAGE, "store_version": RUSTORE_VERSION,
                "version_code": CODE, "owner_gpr_compatibility": "NOT_PROVEN_DIFFERENT_RELEASE_CHANNEL",
                "store_archive_sha256": sha, "bytes": size,
                "signed_apks_verified": len(apk_paths),
                "verified_cert_sha256": RUSTORE_SHA256_CERT,
                "static_source_caller_inventory": results,
                "dynamic_source_selection": "NOT_TESTED",
                "play_protect": "NOT_TESTED",
                "apk_retention": "EPHEMERAL_DELETED_NO_ARTIFACT",
                "verdict": "STATIC_ONLY_NOT_A_WORKING_NATIVE_HOOK"
            }, indent=2))
        return 0
    except Exception as exc:
        print("OFFICIAL_STORE_STATIC_AUDIT_BLOCKED: " + str(exc)[:400], file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
