#!/usr/bin/env python3
"""Structural guard against accidental drift from owner-approved CELIKOM v10."""
from html.parser import HTMLParser
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REFERENCE = BASE / "reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html"
TEMPLATE = BASE / "app/Templates/site-v10.html"
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

assert REFERENCE.is_file(), "Sanitized reference is missing"
assert TEMPLATE.is_file(), "Runtime template is missing"
raw = REFERENCE.read_bytes()
assert raw == TEMPLATE.read_bytes(), "Template drifted from v10 reference without approval"
html = raw.decode("utf-8")
p = V10Parser()
p.feed(html)
assert p.sections == EXPECTED_IDS, f"Section order changed: {p.sections}"
assert p.faq_items == 28, f"Expected 28 FAQ items, found {p.faq_items}"
assert p.faq_filters == EXPECTED_FILTERS, f"FAQ category change: {p.faq_filters}"
assert len(p.images) == 3, "Unexpected v10 image count"
assert p.images.count("/assets/images/celikom-mark.svg") == 2, "Approved brand mark changed"
assert "/media/celikom-popup-approved.png" in p.images, "Real popup media slot missing"
assert not any("base64," in src for src in p.images), "Embedded handoff screenshot forbidden"
assert "3%" not in html, "Old test reward percentage surfaced"
assert "2%" in html and "20%" in html, "Approved rewards not present"
for needle in ("mode-service", "mode-restored", "sound-panel", "faq-item"):
    assert needle in html, f"Interactive reference missing {needle}"
print("CELIKOM v10 markup: 11 sections, 28 FAQ, five categories, safe popup slot — passed")
