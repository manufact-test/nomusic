"""Negative regression cases for the Android release identity contract."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from release_contract import validate_release, load_release, patch_apktool_metadata

data = json.loads((ROOT / "release-spec.json").read_text(encoding="utf-8"))
java = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java").read_text(encoding="utf-8")
assert load_release()[:2] == ("0.3.52", 53)
count = 1


def must_reject(meta, text, label):
    global count
    try:
        validate_release(meta, text)
    except ValueError:
        count += 1
        return
    raise AssertionError("Unsafe release metadata accepted: " + label)


for key, value in [
    ("version", "0.3.51"), ("version", "0.3.53"),
    ("version_code", 52), ("version_code", 54),
    ("version_code", "53"), ("previous_rejected_code", 53),
    ("previous_rejected_version", "0.3.50"),
    ("package", "invalid.package"),
    ("signing_certificate_sha256", "a" * 64),
    ("signing_certificate_sha256", ""),
]:
    broken = dict(data)
    broken[key] = value
    must_reject(broken, java, key)

must_reject(data, java.replace('NAME="0.3.52"', 'NAME="0.3.51"'), "stale AppVersion")
must_reject(data, java.replace('NAME="0.3.52"', 'NAME="0.3.52"; static final String NAME="0.3.52"'), "duplicate AppVersion")
assert "from release_contract import load_release" in (ROOT / "build_release.py").read_text()
assert "from release_contract import load_release" in (ROOT / "verify_release.py").read_text()
assert "/private/" in (ROOT / ".gitignore").read_text()
count += 3
print("PASS:", count, "negative release version, signing identity and code-source contract checks")

sample = "versionCode: 23\nversionName: 0.3.22\nunrelated: value\n"
expected = "versionCode: 53\nversionName: 0.3.52\nunrelated: value\n"
assert patch_apktool_metadata(sample, "0.3.52", 53) == expected
count += 1
for text in ["versionCode: 23\nunrelated: value\n", "versionCode: 23\nversionCode: 24\nversionName: 0.3.22\n"]:
    try:
        patch_apktool_metadata(text, "0.3.52", 53)
    except ValueError:
        count += 1
    else:
        raise AssertionError("Ambiguous/incomplete Apktool metadata was accepted")
print("PASS: Apktool version substitution preserves metadata and rejects ambiguity")

# Real Apktool 2.11.1 decoded source uses two-space indentation in versionInfo.
real_apktool_yaml = "versionInfo:\n  versionCode: 23\n  versionName: 0.3.22-probe\n"
want_yaml = "versionInfo:\n  versionCode: 53\n  versionName: 0.3.52\n"
assert patch_apktool_metadata(real_apktool_yaml, "0.3.52", 53) == want_yaml
assert patch_apktool_metadata(want_yaml, "0.3.52", 53) == want_yaml
print("PASS: actual Apktool 2.11.1 indented versionInfo and idempotence")
