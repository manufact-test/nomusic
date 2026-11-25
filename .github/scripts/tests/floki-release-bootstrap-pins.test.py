#!/usr/bin/env python3
"""Release bootstrap pin and channel-isolation static guard, no privileged access."""
from pathlib import Path
import json
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/".github/scripts"
bootstrap=(SCRIPTS/"floki-release-owner-bootstrap.sh").read_text()
pins=re.findall(
 r"fetch_exact ([a-f0-9]{40}) \\\n  (\.github/scripts/[a-zA-Z0-9._-]+) \\\n  ([a-f0-9]{40})",
 bootstrap)
assert len(pins)>=7,("TOO_FEW_PINNED_BOOTSTRAP_SOURCES",len(pins))
files=set()
for commit,path,blob in pins:
    assert path not in files,"DUPLICATE_BOOTSTRAP_PIN"
    files.add(path)
    content=ROOT/path
    assert content.is_file() and not content.is_symlink(),path
    actual=subprocess.run(["git","hash-object",str(content)],check=True,
            capture_output=True,text=True).stdout.strip()
    assert actual==blob,("STALE_BOOTSTRAP_PIN",path,actual,blob)
assert ".github/scripts/floki-android-stable-owner-install.sh" in files
assert ".github/scripts/floki-android-customer-stable-install.sh" in files
assert ".github/scripts/floki-windows-customer-stable-install.sh" in files
assert ".github/scripts/floki-extension-owner-install.sh" in files

for name,consumer_path,expected in (
 ("floki-windows-customer-stable-install.sh",
  "floki-windows-customer-stable-consumer.py", "BLOB="),
 ("floki-android-stable-owner-install.sh",
  "floki-android-stable-root-consumer.py","BLOB="),
 ("floki-android-customer-stable-install.sh",
  "floki-android-customer-stable-consumer.py","BLOB="),
 ("floki-extension-owner-install.sh",
  "floki-extension-owner-consumer.py","BLOB="),
):
    installer=(SCRIPTS/name).read_text()
    match=re.search(r"(?m)^BLOB=([a-f0-9]{40})$",installer)
    assert match,("CONSUMER_NOT_PINNED",name)
    content=SCRIPTS/consumer_path
    actual=subprocess.run(["git","hash-object",str(content)],check=True,
                 capture_output=True,text=True).stdout.strip()
    assert actual==match[1],("STALE_CONSUMER_PIN",name,actual,match[1])

for p in ("windows-customer-stable.json","android-customer-stable.json"):
    j=json.loads((ROOT/".github/release"/p).read_text())
    assert j=={"schema":1,"channel":"customer-stable","approved":None},p

j=json.loads((ROOT/".github/release/extension-owner-promotions.json").read_text())
assert j["approved"]==[] and j["public_stable"] is None,"WITHDRAWN_EXTENSION_PUBLICATION"
assert "celikom-a1-signed-owner.timer || true" in bootstrap
assert "celikom-windows-signed-owner.timer" in bootstrap
print("CELIKOM_BOOTSTRAP_CURRENT_HASH_PINS_AND_CUSTOMER_OWNER_ISOLATION_OK")
