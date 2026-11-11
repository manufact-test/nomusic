#!/usr/bin/env python3
"""Ephemeral public storefront download of exact 2025 GPR *candidate* + issuer verification.

Uses normal public UI and no credentials / undocumented APIs. Downloads only into
private disposable GitHub runner storage, never logs links, APK content, cert
data beyond fixed pinned SHA comparison or uploads any binary/artifact.
Never installs, repacks or runs the candidate. Any mismatched signature/version
causes strict rejection, not a candidate accepted by origin branding.
"""
from __future__ import annotations

import contextlib
import io
import os
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from publisher_2025_provenance_gate import (
    GateError, inspect, file_hashes, verify_metadata, private_command,
    VERSION_CODE, VERSION_NAME_GPR, KNOWN_ISSUER_CERT, MAX_BYTES,
)

DETAIL = "https://yandex-music.ru.uptodown.com/android/dw/1120247189"
STOREFRONTS = {"yandex-music.ru.uptodown.com", "yandex-music.en.uptodown.com"}
VERSION_RE = re.compile(r"2025\.10\.4\s*#120\.1gpr", re.I)
DOWNLOAD_RE = re.compile(r"Скачать|Download|Get APK|Загрузить", re.I)
MAX_ARCHIVE_BYTES = 170 * 1024 * 1024
MAX_PARTS = 20


def category(error: Exception) -> str:
    if isinstance(error, GateError):
        return str(error)
    if isinstance(error, zipfile.BadZipFile):
        return "BAD_APK_OR_XAPK_ARCHIVE"
    return "PUBLIC_SITE_OR_DOWNLOAD_NOT_READY"


def safe_download_filename(name: str) -> bool:
    return (
        isinstance(name, str) and bool(name) and
        len(name) < 200 and
        "/" not in name and "\\" not in name and
        (name.lower().endswith(".apk") or name.lower().endswith(".xapk") or name.lower().endswith(".apks"))
    )


def unbundle_candidate(path: Path, destination: Path) -> list[Path]:
    """Extract only .apk ZIP members with caps; files are NEVER altered."""
    # Check archive bytes and ZIP structure before allocation/extraction.
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise GateError("PUBLIC_ARCHIVE_TOO_LARGE")
    if not zipfile.is_zipfile(path):
        raise GateError("PUBLIC_DOWNLOAD_NOT_APK_ARCHIVE")
    with zipfile.ZipFile(path) as archive:
        files = archive.infolist()
        if "classes.dex" in {x.filename for x in files}:
            return [path]  # a normal APK, never extract or rewrite it
        apk_infos = [x for x in files if x.filename.lower().endswith(".apk")]
        if not 1 <= len(apk_infos) <= MAX_PARTS:
            raise GateError("PUBLIC_SPLIT_SET_INVALID")
        if sum(x.file_size for x in apk_infos) > 210 * 1024 * 1024:
            raise GateError("PUBLIC_SPLITS_TOO_LARGE")
        paths = []
        for i, info in enumerate(apk_infos):
            if info.file_size <= 0 or info.file_size > MAX_BYTES:
                raise GateError("PUBLIC_SPLIT_TOO_LARGE")
            out = destination / f"verified-structure-{i}.apk"
            size = 0
            with archive.open(info) as src, out.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_BYTES or size > info.file_size:
                        raise GateError("PUBLIC_SPLIT_DECOMPRESSION_OVER_LIMIT")
                    dst.write(chunk)
            if size != info.file_size:
                raise GateError("PUBLIC_SPLIT_SIZE_MISMATCH")
            paths.append(out)
    return paths


def verify_split_set(apks: list[Path]) -> dict:
    if not apks or len(apks) > MAX_PARTS:
        raise GateError("PUBLIC_SPLIT_SET_INVALID")
    bases = 0
    names = set()
    for path in apks:
        result = inspect(path, channel="gpr")
        # inspect validates signature, exact version and cert for EACH split.
        # For a split-only version name quirk, fail closed rather than guessing.
        badging = private_command(["aapt", "dump", "badging", str(path)])
        split = re.search(r"^package:.*?\bsplit='([^']+)'", badging, re.M)
        name = split.group(1) if split else "base"
        if name in names:
            raise GateError("PUBLIC_DUPLICATE_SPLIT")
        names.add(name)
        bases += int(name == "base")
        if not result["publisher_cert_matches_verified_rustore_2026_reference"]:
            raise GateError("PUBLIC_ISSUER_NOT_CONFIRMED")
    if bases != 1:
        raise GateError("PUBLIC_BASE_SPLIT_MISSING")
    return {"verified_issuer_signed_splits": len(apks),
            "all_apks_have_exact_2025_gpr_identity": True,
            "all_apks_cryptographically_signed": True}


def browser_download(directory: Path) -> tuple[Path | None, dict]:
    from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout
    diagnostics = {
        "page_is_public_stored_version": False,
        "official_publisher_host": False,
        "download_button_visible": False,
        "actual_binary_download_started": False,
        "historical_gpr_2025_source": "UPTODOWN_PUBLIC_THIRD_PARTY_LISTING",
        "source_is_issuer_authorized": False,
    }
    with sync_playwright() as api:
        browser=api.chromium.launch(channel="chrome",headless=os.getenv("CELIKOM_PUBLIC_HEADFUL") != "1",
                                    args=["--no-sandbox","--disable-dev-shm-usage"])
        context=browser.new_context(locale="ru-RU", accept_downloads=True)
        try:
            page=context.new_page()
            captured=[]
            page_events=[]
            def hook_page(new_page):
                new_page.on("download",lambda download: captured.append(download))
                page_events.append(new_page)
            context.on("page",hook_page)
            page.on("download",lambda download: captured.append(download))
            response=page.goto(DETAIL,wait_until="domcontentloaded",timeout=45000)
            if response is None or response.status != 200:
                raise GateError("PUBLIC_VERSION_PAGE_HTTP_NOT_200")
            parsed=urlsplit(page.url)
            if (parsed.scheme != "https" or parsed.hostname not in STOREFRONTS or
                parsed.path != "/android/dw/1120247189"):
                raise GateError("PUBLIC_VERSION_PAGE_REDIRECTED")
            page.wait_for_timeout(2000)
            text=page.locator("body").inner_text(timeout=15000)
            diagnostics["page_is_public_stored_version"] = bool(
                VERSION_RE.search(text) or parsed.path == "/android/dw/1120247189")
            # A download may fire automatically when the old-version page opens.
            if not captured:
                # Uptodown's PUBLIC download page offers a visible
                # "All variants" button for XAPK/APK. Prefer this normal UI
                # instead of the app-store installer download link.
                variants=page.locator("button").filter(
                    has_text=re.compile(r"варианты|variants",re.I))
                diagnostics["variants_button_count"] = variants.count()
                if variants.count():
                    try:
                        variants.last.click(timeout=5000)
                        page.wait_for_timeout(1900)
                        diagnostics["variants_button_clicked"]=True
                    except Exception:
                        diagnostics["variants_button_clicked"]=False
                buttons=[]
                for el in page.locator("a,button,[role='button']").all()[:350]:
                    try:
                        label=el.inner_text(timeout=900).strip()
                        if len(label)>110 or not re.search(
                            r"Download|Скачать|Загрузить|variants|варианты|XAPK|APK",label,re.I):
                            continue
                        href=el.get_attribute("href") or ""
                        dest=urlsplit(href)
                        buttons.append({
                            "element":el.evaluate("(e)=>e.tagName.toLowerCase()"),
                            "short_public_label":" ".join(label.split()[:4])[:55],
                            "visible":el.is_visible(),
                            "label_group":"variants" if re.search(r"варианты|variants",label,re.I)
                               else "download" if DOWNLOAD_RE.search(label) else
                               "archive" if "XAPK" in label.upper() else "apk",
                            "href_path_kind":"download" if "download" in dest.path else
                               "dw" if "/dw/" in dest.path else
                               "other" if href else "none",
                            "href_host_group":"uptodown" if "uptodown.com" in (dest.hostname or "") else
                               "relative" if not dest.hostname else "external",
                            "has_download_attribute":el.get_attribute("download") is not None,
                        })
                    except Exception:
                        continue
                diagnostics["public_download_controls_after_variants"]=buttons[:14]
                # Observe public variant selection; no private API calls.
                maybe=page.locator("a,button").filter(has_text=re.compile(
                    r"^(?:APK|XAPK|Download APK|Скачать APK|Скачать XAPK)$", re.I))
                diagnostics["direct_public_apk_variant_count"]=maybe.count()
                if maybe.count():
                    try:
                        maybe.last.click(timeout=5000)
                        page.wait_for_timeout(1400)
                    except Exception:
                        pass
                if not captured:
                    # Primary download is next to variants; restrict to BUTTON,
                    # avoid older pages' unrelated download/navigation anchors.
                    primary=page.locator("button").filter(has_text=DOWNLOAD_RE)
                    diagnostics["download_button_visible"]=bool(primary.count())
                    if primary.count():
                        try:
                            primary.first.click(timeout=6000)
                            page.wait_for_timeout(3500)
                        except Exception:
                            pass
                final=urlsplit(page.url)
                diagnostics["post_click_same_version_page"]= (
                    final.path == "/android/dw/1120247189")
                diagnostics["post_click_path_category"] = (
                    "same_dw" if final.path == "/android/dw/1120247189" else
                    "post_download" if "post-download" in final.path else
                    "android_download" if final.path.endswith("/android/download") else
                    "other_dw" if "/dw/" in final.path else
                    "other_public_uptodown" if (final.hostname or "").endswith("uptodown.com") else
                    "other_external")
                diagnostics["post_click_path"] = (
                    final.path[:120] if (final.hostname or "").endswith("uptodown.com") else None)
                current_text=page.locator("body").inner_text(timeout=9000)
                diagnostics["post_click_version_text_visible"]=bool(VERSION_RE.search(current_text))
                diagnostics["post_click_variant_controls_visible"]=bool(
                    re.search(r"варианты|variants",current_text,re.I))
                diagnostics["post_click_store_installer_prompt"]=bool(
                    re.search(r"Uptodown App Store|Uptodown App|магазин Uptodown",current_text,re.I))
                diagnostics["post_click_download_text_visible"]=bool(DOWNLOAD_RE.search(current_text))
            # Do not sleep indefinitely or follow restricted destinations.
            for _ in range(10):
                if captured: break
                page.wait_for_timeout(900)
            diagnostics["public_pages_opened"] = len(context.pages)
            if not captured:
                return None, diagnostics
            dl=captured[0]
            if not safe_download_filename(dl.suggested_filename):
                raise GateError("PUBLIC_BINARY_FILENAME_NOT_APK")
            out=directory/"candidate-public-2025"
            dl.save_as(out)
            if dl.failure():
                raise GateError("PUBLIC_DOWNLOAD_FAILED")
            if out.stat().st_size > MAX_ARCHIVE_BYTES or out.stat().st_size < 4096:
                raise GateError("PUBLIC_BINARY_INVALID_LENGTH")
            diagnostics["actual_binary_download_started"]=True
            return out, diagnostics
        finally:
            context.close()
            browser.close()


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="celikom-public-2025-gpr-untrusted-") as work:
            root=Path(work)
            path, diag=browser_download(root)
            if path is None:
                print(json.dumps({"verdict":"PUBLIC_2025_GPR_DOWNLOAD_NOT_EXPOSED_BY_BROWSER",
                    **diag,"apk_verified":False,"installed":False,
                    "native_stage_a":"NO_GO"},sort_keys=True))
                return 0
            parts=unbundle_candidate(path,root)
            result=verify_split_set(parts)
            size, sha, _=file_hashes(path)
            print(json.dumps({"verdict":"PUBLIC_2025_GPR_ISSUER_SIGNED_SOURCE_CONFIRMED",
                **diag,**result,"original_download_sha256":sha,
                "original_download_size":size,
                "old_2025_original_installed":False,
                "native_yandex_ui_tested":False,"celikom_stage_a":"NO_GO",
                "binary_uploaded_or_published":False},sort_keys=True))
            return 0
    except Exception as error:
        print(json.dumps({
            "verdict":"PUBLIC_2025_GPR_CANDIDATE_NOT_VERIFIED",
            "reason":category(error),
            "source_not_publisher_attested":True,
            "apk_published":False,"installed":False,"celikom_stage_a":"NO_GO",
        },sort_keys=True))
        return 0  # Source verification failure is a research outcome, not a bypass.


if __name__=="__main__":
    raise SystemExit(main())
