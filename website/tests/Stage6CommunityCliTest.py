#!/usr/bin/env python3
"""Stage6 CLI cannot change monetary rules, rights or sections outside community."""
import json
from pathlib import Path
import subprocess
import tempfile

BASE = Path(__file__).resolve().parents[1]
CLI = BASE / "tools/render-community-preview.php"
FIXTURE = BASE / "tests/fixtures/preview-stage6-community.json"
TEMPLATE = (BASE / "app/Templates/site-v10.html").read_text(encoding="utf-8")

def run(path):
    return subprocess.run(["php", str(CLI), str(path)], capture_output=True, text=True, timeout=10)

ok = run(FIXTURE)
assert ok.returncode == 0 and not ok.stderr, ok.stderr
page = ok.stdout
assert "Нет нужной версии?" in page
assert "Расскажи сообществу." in page
assert "Загрузить запись" in page
assert "СПАСИБО ЗА ВКЛАД" in page
assert "2% скидки" in page.replace("\u00a0", " ")
assert "20%" in page
assert "10 песен" in page
assert "до запуска оплаты" in page.replace("\u00a0", " ")
assert "необходимые права" in page
assert page.count('class="faq-item"') == 28
assert page.count('class="community-card"') == 2
assert page.count('<section') == TEMPLATE.count('<section')
assert page.count('<script src=') == TEMPLATE.count('<script src=')
with tempfile.TemporaryDirectory() as folder:
    filename = Path(folder) / "bad.json"
    for bad in [
        '{"rewards.text.03":"100% discount for everyone"}',
        '{"rewards.text.04":"Pay now"}',
        '{"contribute.text.08":"Загружай любые записи без ограничений"}',
        '{"contribute.text.08":"Есть права на запись, можно сразу опубликовать."}',
        '{"media.popup.alt":"screenshot"}',
        '{"contribute.text.05":"javascript:alert(1)", "faq.text.01":"oops"}',
        '{"contribute.text.05":["not plain text"]}',
        '{"contribute.text.02":""}',
        '[]',
        '{"contribute.text.07":"' + 'А' * 41 + '"}',
    ]:
        filename.write_text(bad, encoding="utf-8")
        fail = run(filename)
        assert fail.returncode != 0 and fail.stdout == "", f"Bad payload passed: {bad}"
print("Stage 6: private community preview, 2%/20% locked and unsafe content rejected — PASS")
