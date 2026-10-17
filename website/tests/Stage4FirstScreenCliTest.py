#!/usr/bin/env python3
"""Stage4 isolation: CLI-only first-screen fixture outputs safe v10 markup."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
TOOL = BASE / "tools/render-first-screen-preview.php"
FIXTURE = BASE / "tests/fixtures/preview-stage4-first-screen.json"
TEMPLATE = (BASE / "app/Templates/site-v10.html").read_text(encoding="utf-8")

def render(path):
    return subprocess.run(["php", str(TOOL), str(path)], capture_output=True, text=True, timeout=10)

ok = render(FIXTURE)
assert ok.returncode == 0 and not ok.stderr, ok.stderr
s = ok.stdout
assert "Зачем CELIKOM" in s
assert "Как работает демонстрация" in s
assert "Демо предпросмотра первого экрана." in s
assert "&lt;script&gt;alert(1)&lt;/script&gt;" in s
assert "<script>alert(1)</script>" not in s
assert 'class="btn primary" href="#sound"' in s
assert s.count('<details class="faq-item"') == 28
assert "data-managed-media=\"celikom.popup.approved\"" in s
assert re.findall(r'<script src="([^"]+)"',s)==(re.findall(r'<script src="([^"]+)"',TEMPLATE) + ["/assets/js/v10/demo-editorial-preview.js"])
assert 'data-editorial-service="Обычный режим &amp; знакомый плеер"' in s
assert 'data-editorial-restored="Проверенная версия &lt;только если доступна&gt;"' in s
assert re.findall(r'<link rel="stylesheet" href="([^"]+)"',s)==re.findall(r'<link rel="stylesheet" href="([^"]+)"',TEMPLATE)
assert len(re.findall(r'<section\b',s)) == len(re.findall(r'<section\b',TEMPLATE))
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/"bad.json"
    for payload in [
        '{"faq":{"updates":{"faq-question-01":{"question":"hacked"}}}}',
        '{"seo.title":"unauthorized"}',
        '{"hero.primary.href":"javascript:alert(1)"}',
        '{"hero.title.first":"ok", "sound.text.01":["not text"]}',
        '{"sound.result.restored":""}',
        '{"sound.result.restored":"\\u0001"}',
        '{"sound.result.restored":["invalid"]}'
    ]:
        path.write_text(payload,encoding="utf-8")
        bad=render(path)
        assert bad.returncode!=0 and not bad.stdout, f"Bad draft passed: {payload}"
print("Stage4 CLI first screen: safe Header/Hero/demo preview, disallowed edits and XSS — PASS")
