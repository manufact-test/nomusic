#!/usr/bin/env python3
"""Stage 5 isolated browser fixture, no public route or persistent changes."""
from pathlib import Path
import json
import re
import subprocess
import tempfile

BASE=Path(__file__).resolve().parents[1]
tool=BASE/"tools/render-principle-preview.php"
fixture=BASE/"tests/fixtures/preview-stage5-principle.json"
template=(BASE/"app/Templates/site-v10.html").read_text(encoding="utf-8")

def render(path):
    return subprocess.run(["php", str(tool), str(path)],capture_output=True,text=True,timeout=10)

good=render(fixture)
assert good.returncode==0 and good.stderr=="",good.stderr
html=good.stdout
assert "Знакомые песни и версии" in html
assert "Как подключиться после запуска" in html
assert "Плеер остаётся твоим." in html
assert len(re.findall(r'<div class="num">0[123]</div>',html))==3
assert html.count('class="faq-item"')==28
assert re.findall(r'<script src="([^"]+)"',html)==re.findall(r'<script src="([^"]+)"',template)
assert re.findall(r'<link rel="stylesheet" href="([^"]+)"',html)==re.findall(r'<link rel="stylesheet" href="([^"]+)"',template)
assert 'data-managed-media="celikom.popup.approved"' in html
with tempfile.TemporaryDirectory() as folder:
    p=Path(folder)/"test.json"
    for source in [
        '{"how.text.03":"99"}',
        '{"hero.title.first":"Unauthorized"}',
        '{"features.text.01":["array"]}',
        '{"player.text.06":"\u0001"}',
        '{"player.text.05":""}',
        '{"foo":"bar"}',
        '["bad"]',
        '{"how.text.10":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}'
    ]:
        p.write_text(source,encoding="utf-8")
        bad=render(p)
        assert bad.returncode!=0 and bad.stdout=="",source
print("Stage 5 CLI: benefits, three immutable-number steps and player; invalid data refused — PASS")
