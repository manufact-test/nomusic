#!/usr/bin/env python3
"""Verify future CMS consumes a deterministic read-only Stage 4 field schema."""
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parents[1]
TOOL = BASE / "tools/list-first-screen-fields.php"
proc = subprocess.run(["php", str(TOOL)], capture_output=True, text=True, timeout=10)
assert proc.returncode == 0 and proc.stderr == "", proc.stderr
data = json.loads(proc.stdout)
assert data["contract"] == "celikom-first-screen-v10-stage4"
assert data["preview_only"] is True
assert data["public_admin_available"] is False
assert data["requires_stage9_authentication"] is True
fields = data["fields"]
assert len(fields) == 27
keys = [f["key"] for f in fields]
assert len(set(keys)) == 27
assert [f["section"] for f in fields if f["type"] == "demo_state_text"] == ["sound"]
assert {f["type"] for f in fields} == {"text", "url", "demo_state_text"}
assert {f["section"] for f in fields} == {"header", "top", "sound"}
assert all(f["label"] and f["section_label"] and f["default"] for f in fields)
assert all(isinstance(f["max_chars"], int) and f["max_chars"] > 0 for f in fields)
assert not any("popup" in f["key"] or "password" in f["key"]
               or f["key"].startswith("seo.") for f in fields)
assert keys[-1] == "sound.result.restored"
assert len([f for f in fields if f["type"] == "url"]) == 7
bad = subprocess.run(["php", str(TOOL), "unexpected"], capture_output=True,
                     text=True, timeout=10)
assert bad.returncode != 0 and bad.stdout == ""
print("Stage4 CLI field contract: 27 safe editable fields, no media/SEO, no public CMS — PASS")
