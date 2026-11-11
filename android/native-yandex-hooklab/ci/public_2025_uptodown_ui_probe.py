#!/usr/bin/env python3
"""Public storefront *browser UI* check for publisher-signed 2025 original availability.

Only visible non-authenticated storefront content. No private API/keys, DRM,
login, APK download, browser download, repackaging or Android installation.
Pagination is clicked like a normal user; a visible version is NOT an APK proof.
"""
from __future__ import annotations
import json
import re
from urllib.parse import urlsplit

ROOT = "https://yandex-music.ru.uptodown.com/android/versions"
TARGET = "2025.10.4 #120.1rur"
ALT = "2025.10.4 #120.1gpr"
MAX_CLICKS = 18

def approved_storefront(url: str) -> bool:
    u = urlsplit(url)
    return (
        u.scheme == "https" and
        u.hostname in {"yandex-music.ru.uptodown.com", "yandex-music.en.uptodown.com"} and
        u.port in (None, 443) and not u.username and not u.password
    )

def safe_summary(body: str, click_count: int, target_link_present: bool = False) -> dict:
    exact = TARGET in body
    alt = ALT in body
    return {
        "verdict": "PUBLIC_SITE_2025_RUR_LISTING_VISIBLE" if exact else
                   "PUBLIC_SITE_2025_GPR_ALTERNATE_VISIBLE" if alt else
                   "PUBLIC_SITE_TARGET_NOT_VISIBLE",
        "target_rur_visible": exact,
        "alternate_gpr_visible": alt,
        "public_target_link_present": bool(target_link_present and exact),
        "bounded_show_more_clicks": click_count,
        "source_is_official_publisher": False,
        "apk_downloaded": False,
        "publisher_signature_verified": False,
        "native_2025_install_authorized": False,
    }

def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as runtime:
            browser = runtime.chromium.launch(channel="chrome", headless=True,
                                              args=["--no-sandbox", "--disable-dev-shm-usage"])
            context = browser.new_context(locale="ru-RU", accept_downloads=False)
            try:
                page = context.new_page()
                response=page.goto(ROOT, wait_until="domcontentloaded", timeout=45000)
                if response is None or response.status != 200:
                    raise ValueError("PUBLIC_STOREFRONT_HTTP_NON_200")
                page.wait_for_timeout(2000)
                if not approved_storefront(page.url):
                    raise ValueError("OUTSIDE_PUBLIC_STOREFRONT")
                clicks = 0
                body = page.locator("body").inner_text(timeout=15000)
                for _ in range(MAX_CLICKS):
                    if TARGET in body:
                        break
                    # The public 'show more' UI loads older releases dynamically.
                    labels = [
                        page.get_by_text(re.compile(r"^ПОКАЗАТЬ БОЛЬШЕ$",re.I)),
                        page.get_by_text(re.compile(r"^Показать больше$",re.I)),
                        page.get_by_text(re.compile(r"^See more$",re.I)),
                        page.get_by_text(re.compile(r"^Load more$",re.I)),
                        page.get_by_text(re.compile(r"^Показать ещё$",re.I)),
                        page.get_by_text(re.compile(r"^Показать еще$",re.I)),
                        page.get_by_text(re.compile(r"Показать\s+больше|Show\s+more|See\s+more",re.I)),
                    ]
                    clicked=False
                    for label in labels:
                        try:
                            candidate=label.last
                            if label.count() and candidate.is_visible():
                                candidate.click(timeout=4000)
                                page.wait_for_timeout(1100)
                                clicks += 1
                                clicked=True
                                break
                        except Exception:
                            continue
                    if not clicked:
                        break
                    body_next = page.locator("body").inner_text(timeout=10000)
                    if body_next == body:
                        break
                    body = body_next
                has_link = False
                if TARGET in body:
                    has_link = bool(page.locator("a").filter(
                        has_text=re.compile(r"2025\.10\.4\s*#120\.1rur")).count())
                output=safe_summary(body,clicks,has_link)
                output["alternate_public_link_present"] = bool(page.locator("a").filter(
                    has_text=re.compile(r"2025\.10\.4\s*#120\.1gpr")).count()) if ALT in body else False
                output["visible_version_label_occurrences"] = len(re.findall(r"202[56]\.\d{2}\.\d+", body))
                output["public_show_more_text_present"] = bool(re.search(
                    r"ПОКАЗАТЬ БОЛЬШЕ|Показать больше|See more|Load more|Показать е[щш]ё",
                    body,re.I))
                output["page_has_yandex_heading"] = bool(re.search(r"Яндекс Музыка|Yandex Music",body,re.I))
                output["ui_show_more_leaf_matches"] = page.get_by_text(re.compile(
                    r"Показать\s+больше|Show\s+more|See\s+more",re.I)).count()
                print(json.dumps(output,sort_keys=True))
            finally:
                context.close()
                browser.close()
        return 0
    except Exception as error:
        # Don't put remote HTML or browser exceptions into public Actions logs.
        category="PUBLIC_BROWSER_UI_PROBE_UNAVAILABLE"
        if isinstance(error,ValueError) and str(error)=="OUTSIDE_PUBLIC_STOREFRONT":
            category="PUBLIC_BROWSER_UNEXPECTED_REDIRECT"
        elif isinstance(error,ValueError) and str(error)=="PUBLIC_STOREFRONT_HTTP_NON_200":
            category="PUBLIC_STOREFRONT_HTTP_NON_200"
        print(json.dumps({
            "verdict":category,"apk_downloaded":False,
            "publisher_signature_verified":False,
            "native_2025_install_authorized":False,
        },sort_keys=True))
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
