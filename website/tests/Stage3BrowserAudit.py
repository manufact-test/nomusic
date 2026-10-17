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
        if route not in ("/audit/reference", "/audit/runtime", "/audit/draft", "/audit/stress", "/audit/principle", "/audit/community", "/audit/trust"):
            return super().do_GET()
        if route.endswith("/trust"):
            preview = subprocess.run(
                ["php", str(BASE / "tools/render-trust-preview.php"),
                 str(BASE / "tests/fixtures/preview-stage7-trust.json")],
                capture_output=True, text=True, timeout=10, check=True)
            html = preview.stdout
        elif route.endswith("/community"):
            preview = subprocess.run(
                ["php", str(BASE / "tools/render-community-preview.php"),
                 str(BASE / "tests/fixtures/preview-stage6-community.json")],
                capture_output=True, text=True, timeout=10, check=True)
            html = preview.stdout
        elif route.endswith("/principle"):
            preview = subprocess.run(
                ["php", str(BASE / "tools/render-principle-preview.php"),
                 str(BASE / "tests/fixtures/preview-stage5-principle.json")],
                capture_output=True, text=True, timeout=10, check=True)
            html = preview.stdout
        elif route.endswith("/stress"):
            preview = subprocess.run(
                ["php", str(BASE / "tools/render-first-screen-preview.php"),
                 str(BASE / "tests/fixtures/preview-stage4-layout-stress.json")],
                capture_output=True, text=True, timeout=10, check=True)
            html = preview.stdout
        elif route.endswith("/draft"):
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

                        # Stage 4 content stress test: long but valid first-
                        # screen copy must remain readable and navigable.
                        page.goto(origin + "/audit/stress", wait_until="networkidle")
                        assert "Верни любимое звучание музыки." in page.locator(".hero h1").inner_text()
                        assert page.locator("#sound-result").inner_text() == (
                            "Сейчас воспроизводится исходный трек")
                        page.locator("#mode-restored").click()
                        assert page.locator("#sound-result").inner_text().startswith(
                            "Если проверенная версия доступна")
                        problematic = page.evaluate("""() => {
                          const selectors = [
                            "header .brand", "header nav", "header .header-chip",
                            ".hero-copy h1", ".hero-lead", ".hero .actions",
                            ".hero .actions .btn", "#sound .section-heading",
                            "#sound .section-body", "#sound .mode-btn",
                            "#sound-result", "#sound .demo-board-foot"
                          ];
                          const failures = [];
                          for (const selector of selectors) {
                            for (const el of document.querySelectorAll(selector)) {
                              const style = getComputedStyle(el);
                              if (style.display === "none" || style.visibility === "hidden") continue;
                              const rect = el.getBoundingClientRect();
                              if (rect.width < 2 || rect.height < 2) continue;
                              if (el.scrollWidth > el.clientWidth + 2) {
                                failures.push(selector + ": inner text overflows " +
                                  el.scrollWidth + ">" + el.clientWidth);
                              }
                              if (rect.left < -2 || rect.right > innerWidth + 2) {
                                failures.push(selector + ": beyond viewport " +
                                  rect.left + ".." + rect.right);
                              }
                            }
                          }
                          return failures;
                        }""")
                        assert not problematic, (
                            f"Editor text overflow at {width}px: {problematic}")
                        result["longCopyStress"] = "PASS"

                        # Stage 5 strictly scoped developer preview reuses
                        # v10 components; three step numbers stay immutable.
                        page.goto(origin + "/audit/principle", wait_until="networkidle")
                        assert page.locator("#features article.benefit").count() == 3
                        assert page.locator("#how .step").count() == 3
                        assert page.locator("#how .num").all_inner_texts() == ["01", "02", "03"]
                        assert "Знакомые песни и версии" in page.locator("#features").inner_text()
                        assert "Как подключиться после запуска" in page.locator("#how").inner_text()
                        assert "Плеер остаётся твоим." in page.locator("#player").inner_text()
                        assert page.locator("#player .familiar-features > div").count() == 4
                        assert page.locator("#faq details.faq-item").count() == 28
                        assert page.locator("script:not([src])").count() == 0
                        bounds = page.evaluate("""() => {
                          const bad = [];
                          for (const selector of [
                            "#features .benefit h3", "#features .benefit p",
                            "#how h2", "#how .step h3", "#how .step p",
                            "#player h2", "#player .section-body",
                            "#player .familiar-features > div"
                          ]) {
                            for (const el of document.querySelectorAll(selector)) {
                              const rect = el.getBoundingClientRect();
                              if (el.scrollWidth > el.clientWidth + 2 ||
                                  rect.left < -2 || rect.right > innerWidth + 2) {
                                bad.push(selector + ": " + rect.left + "..." + rect.right +
                                  " scroll=" + el.scrollWidth + "/" + el.clientWidth);
                              }
                            }
                          }
                          return bad;
                        }""")
                        assert not bounds, f"Stage5 text overflow at {width}px: {bounds}"
                        result["stage5Principle"] = "PASS"

                        # Stage 6 read-only community draft. Financial wording
                        # stays canonical; copy may change only in approved
                        # nonfinancial slots. No upload or payment widgets.
                        page.goto(origin + "/audit/community", wait_until="networkidle")
                        assert page.locator("#contribute .community-card").count() == 2
                        assert "Нет нужной версии?" in page.locator("#contribute").inner_text()
                        assert "Расскажи сообществу." in page.locator("#contribute").inner_text()
                        assert "Загрузить запись" in page.locator("#contribute").inner_text()
                        rewards = page.locator("#rewards").inner_text().replace("\u00a0", " ")
                        assert "2% скидки" in rewards
                        assert "20%" in rewards and "10 песен" in rewards
                        assert "следующие месяцы" in rewards
                        assert "до запуска оплаты" in rewards
                        assert page.locator("#rewards a[href*='pay']").count() == 0
                        assert page.locator("form").count() == 0
                        assert page.locator("script:not([src])").count() == 0
                        assert page.locator("#faq details.faq-item").count() == 28
                        community_bounds = page.evaluate("""() => {
                            const bad = [];
                            for (const selector of [
                              "#contribute .community-header h2",
                              "#contribute .community-header p",
                              "#contribute .community-card h3",
                              "#contribute .community-card p",
                              "#rewards .reward-copy h2",
                              "#rewards .reward-copy .section-body",
                              "#rewards .reward-notice"
                            ]) {
                              for (const el of document.querySelectorAll(selector)) {
                                const rect=el.getBoundingClientRect();
                                if (el.scrollWidth > el.clientWidth+2 ||
                                    rect.left < -2 || rect.right > innerWidth+2) {
                                  bad.push(selector + " " + rect.left + ".." + rect.right);
                                }
                              }
                            }
                            return bad;
                        }""")
                        assert not community_bounds, (
                            f"Stage 6 mobile copy overflow at {width}px: {community_bounds}")
                        result["stage6Community"] = "PASS"

                        # Stage 7: combined trust+FAQ editorial preview reuses
                        # approved v10 without new visual assets or scripts.
                        page.goto(origin + "/audit/trust", wait_until="networkidle")
                        assert "Как работает CELIKOM." in page.locator("#transparency").inner_text()
                        assert "Поможем разобраться." in page.locator("#faq").inner_text()
                        trust = page.locator("#transparency").inner_text().replace("\u00a0", " ")
                        assert "не гарантируем неизменность" in trust
                        assert "не будет подменять" in trust
                        assert "Мобильная версия — отдельная разработка" in trust
                        assert page.locator("#faq details.faq-item").count() == 28
                        assert "Проверь, что расширение включено" in page.locator(
                            "#faq-question-27 .answer").text_content()
                        assert page.locator("#faq button.faq-filter").count() == 5
                        page.locator('#faq button[data-filter="help"]').click()
                        assert page.locator('#faq details.faq-item:not([hidden])').count() == 3
                        page.locator('#faq button[data-filter="all"]').click()
                        assert page.locator('#faq details.faq-item:not([hidden])').count() == 28
                        faq_summary = page.locator("#faq-question-27 summary")
                        faq_summary.focus()
                        page.keyboard.press("Enter")
                        assert page.locator("#faq-question-27").get_attribute("open") is not None
                        assert page.locator("script:not([src])").count() == 0
                        trust_bounds = page.evaluate("""() => {
                          const bad = [];
                          for (const selector of [
                            "#transparency h2", "#transparency p",
                            "#transparency h3", "#transparency li",
                            "#faq .section-heading", "#faq .section-body",
                            "#faq details.faq-item .answer p"
                          ]) {
                            for (const el of document.querySelectorAll(selector)) {
                              const rect = el.getBoundingClientRect();
                              if (el.scrollWidth > el.clientWidth + 2 ||
                                  rect.left < -2 || rect.right > innerWidth + 2) {
                                bad.push(selector + " at " + rect.left + ".." + rect.right);
                              }
                            }
                          }
                          return bad;
                        }""")
                        assert not trust_bounds, f"Stage 7 content overflow at {width}px: {trust_bounds}"
                        result["stage7TrustFaq"] = "PASS"
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
