#!/usr/bin/env python3
"""Guard source-to-runtime parity against owner-approved CELIKOM v10."""
from html.parser import HTMLParser
from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[1]
REFERENCE = BASE / "reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html"
TEMPLATE = BASE / "app/Templates/site-v10.html"
CSS_NAMES = ["00-base.css", "01-v6.css", "02-v7.css", "03-v8.css", "04-v10.css"]
JS_NAMES = ["sound-demo.js", "faq.js"]
EXPECTED_IDS = [
    "top", "features", "how", "sound", "player", "contribute",
    "transparency", "faq", "rewards", "install", "closing"
]
EXPECTED_FILTERS = ["all", "start", "rewards", "music", "help"]

class V10Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self.faq_items = 0
        self.faq_filters = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = (a.get("class") or "").split()
        if tag == "section" and a.get("id"):
            self.sections.append(a["id"])
        if tag == "details" and "faq-item" in classes:
            self.faq_items += 1
        if tag == "button" and "faq-filter" in classes:
            self.faq_filters.append(a.get("data-filter"))
        if tag == "img":
            self.images.append(a.get("src", ""))

assert REFERENCE.is_file(), "Sanitized approved v10 reference is missing"
assert TEMPLATE.is_file(), "Private runtime template is missing"
reference = REFERENCE.read_text(encoding="utf-8")
runtime = TEMPLATE.read_text(encoding="utf-8")
inline_css = re.findall(r"<style>(.*?)</style>", reference, flags=re.S)
inline_js = re.findall(r"<script>(.*?)</script>", reference, flags=re.S)
assert len(inline_css) == len(CSS_NAMES), "Approved CSS cascade has changed"
assert len(inline_js) == len(JS_NAMES), "Approved interactive scripts have changed"

# Source-to-runtime transformation MUST be an exact substitution, not a redraw:
reconstructed = reference
for name, original in zip(CSS_NAMES, inline_css):
    extracted = (BASE / "public/assets/css/v10" / name).read_text(encoding="utf-8")
    assert extracted == original, f"v10 CSS content modified: {name}"
    reconstructed = reconstructed.replace(
        f"<style>{original}</style>",
        f'<link rel="stylesheet" href="/assets/css/v10/{name}"/>',
        1,
    )
for name, original in zip(JS_NAMES, inline_js):
    extracted = (BASE / "public/assets/js/v10" / name).read_text(encoding="utf-8")
    assert extracted == original, f"v10 JS behavior modified: {name}"
    reconstructed = reconstructed.replace(
        f"<script>{original}</script>",
        f'<script src="/assets/js/v10/{name}"></script>',
        1,
    )
assert runtime == reconstructed, "Runtime page drifted from approved v10"

p = V10Parser()
p.feed(runtime)
assert p.sections == EXPECTED_IDS, f"Section order changed: {p.sections}"
assert p.faq_items == 28, f"Expected 28 FAQ items, found {p.faq_items}"
assert p.faq_filters == EXPECTED_FILTERS, f"FAQ categories changed: {p.faq_filters}"
assert len(p.images) == 3, "Unexpected number of v10 images"
assert p.images.count("/assets/images/celikom-mark.svg") == 2, "Approved mark changed"
assert "/media/celikom-popup-approved.png" in p.images, "Real popup media slot missing"
assert not any("base64," in src for src in p.images), "Embedded screenshot in public content"
visible_markup = re.sub(r"(?is)<(?:script|style)\b[^>]*>.*?</(?:script|style)>", "", reference)
assert "3%" not in visible_markup, "Obsolete 3% in visible copy"
assert "2%" in visible_markup and "20%" in visible_markup, "Approved reward policy missing"
for token in ("mode-service", "mode-restored", "sound-panel", "faq-item"):
    assert token in reference, f"Interactive element missing: {token}"
print("CELIKOM v10: 5 unchanged CSS blocks, 2 unchanged scripts, 11 sections, 28 FAQ, 5 categories — PASS")
