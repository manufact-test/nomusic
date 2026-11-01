#!/usr/bin/env python3
"""Offline-only v10 Stage 8 editorial preview: never an install/download API."""
import json
from pathlib import Path
import subprocess
import tempfile
BASE=Path(__file__).resolve().parents[1]
CLI=BASE/"tools/render-install-footer-preview.php"
FIXTURE=BASE/"tests/fixtures/preview-stage8-install-footer.json"
TEMPLATE=(BASE/"app/Templates/site-v10.html").read_text(encoding="utf-8")
def render(file):
    return subprocess.run(["php",str(CLI),str(file)],
        capture_output=True,text=True,timeout=10)
ok=render(FIXTURE)
assert ok.returncode==0 and ok.stderr=="",ok.stderr
html=ok.stdout
assert "Скоро можно будет подключиться." in html
assert "Песни, которые хочется слышать снова." in html
assert "Принцип работы" in html
assert "Идёт тестирование" in html
assert "Пока установка закрыта" in html
assert "Установка после запуска" in html
assert 'href="#how"' in html
assert 'href="#faq"' in html
assert '<a href="/download"' not in html
assert html.count('class="faq-item"')==28
assert html.count('<section')==TEMPLATE.count('<section')
assert html.count('<script src=')==TEMPLATE.count('<script src=')
with tempfile.TemporaryDirectory() as temp:
    file=Path(temp)/"bad.json"
    cases=[
        [],
        {"texts":{"install.status":"Доступно прямо сейчас"}},
        {"texts":{"install.text.07":"Скачать бесплатно"}},
        {"texts":{"closing.text.04":"Скачать прямо сейчас"}},
        {"texts":{"closing.text.03":["not text"]}},
        {"texts":{"footer.text.02":""}},
        {"links":{"footer.link.05":"https://celikom.example/download"}},
        {"links":{"footer.link.05":"#missing"}},
        {"links":{"closing.cta.href":"#install"}},
        {"links":{"footer.link.02":"javascript:alert(1)"}},
        {"unapproved":{}},
    ]
    for data in cases:
        file.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
        failed=render(file)
        assert failed.returncode!=0 and failed.stdout=="",data
print("Stage8: safe install/footer preview; product readiness locked; no invented links — PASS")
