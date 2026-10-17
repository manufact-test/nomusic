#!/usr/bin/env python3
"""CELIKOM stage 3: v10 FAQ import and separate CMS DB contract checks."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reference = (ROOT / "reference/v10/CELIKOM_SITE_CLEAN_v10_sanitized.html").read_text(encoding="utf-8")
seed = json.loads((ROOT / "database/seeds/faq-v10.json").read_text(encoding="utf-8"))
sql = (ROOT / "database/migrations/001_website_cms.sql").read_text(encoding="utf-8")

assert seed["version"] == 1
assert len(seed["items"]) == 28
assert [(c["key"], c["label"]) for c in seed["categories"]] == [
    ("start", "Установка и работа"),
    ("rewards", "Бонусы и стоимость"),
    ("music", "Песни и модерация"),
    ("help", "Аккаунт и помощь"),
]
raw_items = list(re.finditer(r"<details\b([^>]*)>(.*?)</details>", reference, re.S))
assert len(raw_items) == len(seed["items"])
seen = set()
for n, (html, item) in enumerate(zip(raw_items, seed["items"]), start=1):
    attributes, contents = html.groups()
    faq_id = re.search(r'\bid="([^"]+)"', attributes)
    category = re.search(r'\bdata-category="([^"]+)"', attributes)
    question = re.search(r"<summary>\s*<span>(.*?)</span>", contents, re.S)
    answer = re.search(r'<div class="answer">(.*?)</div>', contents, re.S)
    assert faq_id and category and question and answer, f"Unrecognized FAQ item {n}"
    assert item["id"] == faq_id.group(1)
    assert item["id"] not in seen
    seen.add(item["id"])
    assert item["category"] == category.group(1)
    assert item["question"] == question.group(1)
    assert item["answer_html"] == answer.group(1)
    assert re.fullmatch(r"<p>[^<>]*</p>", item["answer_html"], re.S), "Only approved plain paragraphs are seeded"
    assert item["sort_order"] == n * 10
    assert item["is_visible"] is True

all_copy = "\n".join(i["question"] + "\n" + i["answer_html"] for i in seed["items"])
assert "3%" not in all_copy and "2%" in all_copy and "20%" in all_copy
assert "data:image" not in all_copy

tables = set(re.findall(r"(?im)^CREATE TABLE IF NOT EXISTS ([a-z_]+)", sql))
required = {
    "admin_users", "site_content", "faq_categories", "faq_items", "media_assets",
    "content_revisions", "audit_log", "site_settings", "site_state",
    "content_drafts", "login_rate_limits",
}
assert tables == required, f"CMS tables missing or unexpected: {tables ^ required}"
assert "FOREIGN KEY" in sql and "ENGINE=InnoDB" in sql
assert "published_revision_id" in sql
print("Stage 3 FAQ seed matches all 28 v10 Q/A; private 11-table schema contract — PASS")
