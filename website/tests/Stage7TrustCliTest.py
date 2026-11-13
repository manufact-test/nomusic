#!/usr/bin/env python3
"""CLI-only integrated trust and FAQ safeguards, no deployment."""
import json
from pathlib import Path
import subprocess
import tempfile

BASE = Path(__file__).resolve().parents[1]
CLI = BASE / "tools/render-trust-preview.php"
FIXTURE = BASE / "tests/fixtures/preview-stage7-trust.json"
TEMPLATE = (BASE / "app/Templates/site-v10.html").read_text(encoding="utf-8")

def run(file):
    return subprocess.run(["php", str(CLI), str(file)],
                          capture_output=True, text=True, timeout=15)

approved = run(FIXTURE)
assert approved.returncode == 0 and approved.stderr == "", approved.stderr
page = approved.stdout
assert "Как работает CELIKOM." in page
assert "Поможем разобраться." in page
assert "Проверь, что расширение включено" in page
assert "не\u00a0гарантируем неизменность" in page
assert "не\u00a0будет подменять" in page
assert "Мобильная версия — отдельная разработка" in page
assert page.count('class="faq-item"') == 28
assert page.count('<script src=') == TEMPLATE.count('<script src=')
assert page.count('<section') == TEMPLATE.count('<section')
assert page.count('class="faq-filter"') == TEMPLATE.count('class="faq-filter"')

with tempfile.TemporaryDirectory() as temp:
    target = Path(temp) / "draft.json"
    for rejected in [
        [],
        {"texts": {"transparency.text.14": "We guarantee all royalties"}},
        {"texts": {"transparency.text.12": "Android available"}},
        {"texts": {"transparency.text.09": "99"}},
        {"texts": {"rewards.text.03": "100% forever"}},
        {"texts": {"faq.text.01": ["invalid"]}},
        {"texts": {"faq.text.02": ""}},
        {"faq": {"updates": {"faq-question-08": {"answer": "Pay now!"}}}},
        {"faq": {"updates": {"faq-question-25": {"is_visible": False}}}},
        {"faq": {"updates": {"faq-question-27": {"category": "not-a-tab"}}}},
        {"faq": {"new_items": [{"id": "faq-question-29", "category": "start",
                                "question": "<bad>", "answer": "",
                                "sort_order": 290, "is_visible": True}]}},
        {"extra": True},
        {"texts": "bad"},
    ]:
        target.write_text(json.dumps(rejected, ensure_ascii=False), encoding="utf-8")
        result = run(target)
        assert result.returncode != 0 and result.stdout == "", rejected
print("Stage7: local trust/FAQ composite, 28 approved entries, protected facts and invalid JSON refused — PASS")
