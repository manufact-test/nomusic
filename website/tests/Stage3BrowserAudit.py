#!/usr/bin/env python3
"""Offline Chromium regression for accepted CELIKOM v10 (no deploy, no CMS).
Requires: pip install playwright ; python -m playwright install chromium

Both pages receive the same licensed local Manrope CSS. The reference keeps its
five original inline style blocks and two inline scripts; runtime uses the
extracted files. The approved popup raster is intentionally NOT included here.
"""
import http.server
import json
from pathlib import Path
import re
import subprocess
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[1]
PUBLIC = BASE / "public"
REFERENCE = BASE / "reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html"
RUNTIME = BASE / "app/Templates/site-v10.html"
FONT_LINK = '<link rel="stylesheet" href="/assets/css/v10/manrope-local.css"/>'
WIDTHS = [1440, 1024, 768, 390, 320]
EXPECTED_WRAP = {1440: 1240, 1024: 964, 768: 708, 390: 354, 320: 292}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        route = urlsplit(self.path).path
        if route not in ("/audit/reference", "/audit/runtime", "/audit/draft"):
            return super().do_GET()
        if route.endswith("/draft"):
            draft = subprocess.run(
                ["php", str(BASE / "tools/render-first-screen-preview.php"),
                 str(BASE / "tests/fixtures/preview-stage4-first-screen.json")],
                capture_output=True, text=True, timeout=10, check=True)
            html = draft.stdout
        elif route.endswith("/runtime"):
            html = RUNTIME.read_text(encoding="utf-8")
        else:
            html = REFERENCE.read_text(encoding="utf-8")
            # Normalise font delivery, not typography or styling, for a fair
            # comparison of the original inline styles and extracted styles.
            font_links = re.findall(r'<link\b[^>]*(?:fonts\.googleapis|fonts\.gstatic)[^>]*/>', html)
            assert len(font_links) == 3, "Original font declaration contract changed"
            html = html.replace(font_links[0], FONT_LINK, 1)
            html = html.replace("</head>", '<link rel="stylesheet" href="/assets/css/v10/focus-visible.css"/></head>', 1)
            for link in font_links[1:]:
                html = html.replace(link, "", 1)
        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def font_status(page):
    return page.evaluate("""async () => {
      await document.fonts.load('400 16px Manrope', 'Привет CELIKOM');
      await document.fonts.load('800 16px Manrope', 'Песня и музыка');
      await document.fonts.ready;
      return {
        loaded: [...document.fonts].filter(f =>
          f.family.replaceAll('"', '').replaceAll("'", '') === 'Manrope'
          && f.status === 'loaded').length,
        family: getComputedStyle(document.body).fontFamily,
        fontCheck: document.fonts.check('700 16px Manrope', 'Знакомая песня')
      };
    }""")


def state_checks(page, width):
    geometry = page.evaluate("""() => {
      const box = document.querySelector('header .wrap').getBoundingClientRect();
      return {
        documentWidth: document.documentElement.scrollWidth,
        viewport: innerWidth,
        wrapWidth: box.width,
        wrapLeft: box.left,
        sectionCount: document.querySelectorAll('main section[id]').length,
        faqCount: document.querySelectorAll('#faq details.faq-item').length,
        buttons: document.querySelectorAll('#faq button.faq-filter').length
      };
    }""")
    assert geometry["documentWidth"] <= width + 1, f"Horizontal page overflow at {width}: {geometry}"
    assert abs(geometry["wrapWidth"] - EXPECTED_WRAP[width]) < 2, f"Container drift at {width}: {geometry}"
    assert geometry["sectionCount"] == 11 and geometry["faqCount"] == 28
    assert geometry["buttons"] == 5
    missing = page.evaluate("""() => Array.from(document.querySelectorAll('a[href^="#"]'))
      .map(a => a.getAttribute('href'))
      .filter(href => href.length > 1 && !document.getElementById(href.slice(1)))""")
    assert not missing, f"Broken internal anchors: {missing}"
    fs = font_status(page)
    assert fs["loaded"] >= 2 and fs["fontCheck"], f"Local Cyrillic/Latin Manrope not loaded: {fs}"

    page.locator("#mode-restored").click()
    assert page.locator("#sound-panel").get_attribute("data-mode") == "restored"
    assert page.locator("#mode-restored").get_attribute("aria-pressed") == "true"
    assert page.locator("#mode-service").get_attribute("aria-pressed") == "false"
    page.locator("#mode-service").click()
    assert page.locator("#sound-panel").get_attribute("data-mode") == "service"

    page.locator('#faq button[data-filter="start"]').click()
    visible_cats = page.eval_on_selector_all("#faq .faq-item:not([hidden])",
        "(items) => items.map(item => item.dataset.category)")
    assert len(visible_cats) > 0 and set(visible_cats) == {"start"}
    page.locator('#faq button[data-filter="all"]').click()
    assert page.locator("#faq .faq-item:not([hidden])").count() == 28

    # <summary> must be usable without mouse.
    summary = page.locator("#faq details.faq-item summary").first
    summary.focus()
    page.keyboard.press("Enter")
    assert page.locator("#faq details.faq-item").first.get_attribute("open") is not None
    summary.focus()
    page.keyboard.press("Tab")
    page.keyboard.press("Shift+Tab")
    assert summary.evaluate("(el) => document.activeElement === el"), "Keyboard focus escaped FAQ summary"
    focus = summary.evaluate("""el => {
      const s = getComputedStyle(el);
      return {outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,boxShadow:s.boxShadow};
    }""")
    has_focus = ((focus["outlineStyle"] not in ("none", "hidden")
                  and float(focus["outlineWidth"].replace("px", "")) >= 1.5)
                 or focus["boxShadow"] != "none")
    assert has_focus, f"FAQ summary missing visible keyboard focus at {width}: {focus}"
    return {"width": width, "geometry": geometry, "font": fs,
            "summaryFocusVisible": has_focus, "summaryFocusCss": focus}


def main():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = "http://127.0.0.1:" + str(server.server_address[1])
    results = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for width in WIDTHS:
                    context = browser.new_context(
                        viewport={"width": width, "height": 900},
                        device_scale_factor=1, reduced_motion="reduce")
                    page = context.new_page()
                    try:
                        page.goto(origin + "/audit/reference", wait_until="networkidle")
                        font_status(page)
                        reference_png = page.screenshot(full_page=True, animations="disabled")
                        page.goto(origin + "/audit/runtime", wait_until="networkidle")
                        fs = font_status(page)
                        runtime_png = page.screenshot(full_page=True, animations="disabled")
                        assert reference_png == runtime_png, (
                            f"Visual parity drift at {width}px with identical Manrope; "
                            "inspect CSS/JS extraction before accepting UI-kit.")
                        result = state_checks(page, width)
                        result["pngParity"] = True

                        # Stage 4 first-screen editor preview runs server-side
                        # from a guarded test fixture, never from a public route.
                        page.goto(origin + "/audit/draft", wait_until="networkidle")
                        assert page.locator("header nav").inner_text().find("Зачем CELIKOM") >= 0
                        assert "Как работает демонстрация" in page.locator("#sound").text_content(), (
                            "Demo draft text missing from HTML DOM")
                        assert page.locator(".hero-lead").inner_text().startswith(
                            "Демо предпросмотра первого экрана.")
                        assert page.locator("script:not([src])").count() == 0, (
                            "Injected script appeared in draft HTML")
                        draft_result = state_checks(page, width)
                        assert draft_result["geometry"]["documentWidth"] <= width + 1
                        # The approved v10 click handlers still own data-mode
                        # and aria-pressed; the Stage4 adapter only syncs text.
                        page.locator("#mode-restored").click()
                        assert page.locator("#sound-result").inner_text() == (
                            "Проверенная версия <только если доступна>")
                        assert page.locator("#sound-panel").get_attribute("data-mode") == "restored"
                        assert page.locator("#mode-restored").get_attribute("aria-pressed") == "true"
                        page.locator("#mode-service").click()
                        assert page.locator("#sound-result").inner_text() == (
                            "Обычный режим & знакомый плеер")
                        assert page.locator("#mode-restored").get_attribute("aria-pressed") == "false"
                        page.locator("#mode-restored").focus()
                        page.keyboard.press("Enter")
                        assert page.locator("#sound-result").inner_text() == (
                            "Проверенная версия <только если доступна>")
                        assert page.locator("#sound-panel").get_attribute("data-mode") == "restored"
                        assert page.locator("#sound-result script").count() == 0
                        # Header/Hero actions are real, keyboard-reachable
                        # in the narrowest viewport, and their hash exists.
                        primary = page.locator(".hero .btn.primary")
                        assert primary.get_attribute("href") == "#sound"
                        primary.focus()
                        assert primary.evaluate("(e) => document.activeElement === e")
                        page.keyboard.press("Enter")
                        assert page.evaluate("location.hash") == "#sound"
                        assert page.locator("#sound").count() == 1
                        result["firstScreenDraft"] = "PASS"
                        result["font"] = fs
                        results.append(result)
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("CELIKOM Stage 3: five widths, real local Manrope, pixel parity, "
          "responsive container, keyboard FAQ, buttons, filters, first-screen draft and anchors PASS")
    if not all(item["summaryFocusVisible"] for item in results):
        print("ACCESSIBILITY FOLLOW-UP: summary focus-visible may need a "
              "small additive CSS rule; retain owner-approved default-state appearance.")


if __name__ == "__main__":
    main()
