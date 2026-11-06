"""Negative regression cases for the Android release identity contract."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from release_contract import validate_release, load_release, patch_apktool_metadata

data = json.loads((ROOT / "release-spec.json").read_text(encoding="utf-8"))
java = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java").read_text(encoding="utf-8")
assert load_release()[:2] == ("0.3.91", 92)
count = 1

# The APK is downloaded and verified inside CELIKOM, then opened by Android's
# standard system installer via a read-only, single-file content URI.
provider = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/VerifiedUpdateProvider.java").read_text()
updater = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/UpdateCenter.java").read_text()
assert "Intent.ACTION_VIEW" in updater
assert "VerifiedUpdateProvider.contentUri" in updater
assert "Intent.FLAG_GRANT_READ_URI_PERMISSION" in updater
assert "verifyApk(context,tmp,r)" in updater and "Files.move" in updater
assert "PackageInstaller" not in updater
assert '"r".equals(mode)' in provider and "ParcelFileDescriptor.MODE_READ_ONLY" in provider
assert "Unknown update URI" in provider
assert not (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/UpdateInstallReceiver.java").exists()



def must_reject(meta, text, label):
    global count
    try:
        validate_release(meta, text)
    except ValueError:
        count += 1
        return
    raise AssertionError("Unsafe release metadata accepted: " + label)


for key, value in [
    ("version", "0.3.51"), ("version", "0.3.54"), ("version", "0.3.59"), ("version", "0.3.63"), ("version", "0.3.64"), ("version", "0.3.65"), ("version", "0.3.66"), ("version", "0.3.67"), ("version", "0.3.69"), ("version", "0.3.70"), ("version", "0.3.71"), ("version", "0.3.72"), ("version", "0.3.73"), ("version", "0.3.74"), ("version", "0.3.75"), ("version", "0.3.76"), ("version", "0.3.77"), ("version", "0.3.78"), ("version", "0.3.79"), ("version", "0.3.80"), ("version", "0.3.81"), ("version", "0.3.82"), ("version", "0.3.83"), ("version", "0.3.84"), ("version", "0.3.85"), ("version", "0.3.89"),
    ("version_code", 52), ("version_code", 55), ("version_code", 60), ("version_code", 63),
    ("version_code", 64), ("version_code", 65), ("version_code", 66), ("version_code", 67), ("version_code", 68), ("version_code", 70), ("version_code", 71), ("version_code", 72), ("version_code", 73), ("version_code", 74), ("version_code", 75), ("version_code", 76), ("version_code", 77), ("version_code", 78), ("version_code", 79), ("version_code", 80), ("version_code", 81), ("version_code", 82), ("version_code", 83), ("version_code", 84), ("version_code", 85), ("version_code", 86), ("version_code", 87), ("version_code", 88), ("version_code", 89), ("version_code", 90), ("version_code", "56"), ("previous_rejected_code", 54),
    ("previous_rejected_version", "0.3.50"),
    ("package", "invalid.package"),
    ("signing_certificate_sha256", "a" * 64),
    ("signing_certificate_sha256", ""),
]:
    broken = dict(data)
    broken[key] = value
    must_reject(broken, java, key)

must_reject(dict(data,version="0.3.90"),java,"previous version")
must_reject(dict(data,version_code=91),java,"previous code")
must_reject(data, java.replace('NAME="0.3.91"', 'NAME="0.3.51"'), "stale AppVersion")
must_reject(data, java.replace('NAME="0.3.91"', 'NAME="0.3.91"; static final String NAME="0.3.91"'), "duplicate AppVersion")
assert "from release_contract import load_release" in (ROOT / "build_release.py").read_text()
assert "from release_contract import load_release" in (ROOT / "verify_release.py").read_text()
assert '"TestUpdateState"' in (ROOT / "build_release.py").read_text()
assert "TestOutputClockEvidence.java" in (ROOT / "tests/run_engine.py").read_text()
assert "TestHonor068SupersededAlignmentSeek.java" in (ROOT / "tests/run_engine.py").read_text()
assert "check_0385_seek_baseline.py" in (ROOT / "tests/run_engine.py").read_text()
assert (ROOT / "tests/check_0385_seek_baseline.py").is_file()
# Automatic replacement is admin-approved; no owner confirmation gate or UI may return.
engine_source = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java").read_text()
activity_source = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/RecorderActivity.java").read_text()
assert "durationConfirmationRequired" not in engine_source
assert "confirmed.contains" not in engine_source
assert "Подтвердить найденную песню" not in activity_source
assert "confirmTrack()" not in activity_source
count += 4
# GitHub artifact ZIP strips hidden files by default. Ship the ignore POLICY
# as a non-hidden text file, never any ignored signing/private material.
policy = ROOT / ".gitignore"
if not policy.exists():
    policy = ROOT / "source-gitignore.txt"
assert "/private/" in policy.read_text()
count += 3
print("PASS:", count, "negative release version, signing identity and code-source contract checks")

sample = "versionCode: 23\nversionName: 0.3.22\nunrelated: value\n"
expected = "versionCode: 92\nversionName: 0.3.91\nunrelated: value\n"
assert patch_apktool_metadata(sample, "0.3.91", 92) == expected
count += 1
for text in ["versionCode: 23\nunrelated: value\n", "versionCode: 23\nversionCode: 24\nversionName: 0.3.22\n"]:
    try:
        patch_apktool_metadata(text, "0.3.71", 72)
    except ValueError:
        count += 1
    else:
        raise AssertionError("Ambiguous/incomplete Apktool metadata was accepted")
print("PASS: Apktool version substitution preserves metadata and rejects ambiguity")

# Real Apktool 2.11.1 decoded source uses two-space indentation in versionInfo.
real_apktool_yaml = "versionInfo:\n  versionCode: 23\n  versionName: 0.3.22-probe\n"
want_yaml = "versionInfo:\n  versionCode: 92\n  versionName: 0.3.91\n"
assert patch_apktool_metadata(real_apktool_yaml, "0.3.91", 92) == want_yaml
assert patch_apktool_metadata(want_yaml, "0.3.91", 92) == want_yaml
print("PASS: actual Apktool 2.11.1 indented versionInfo and idempotence")


# An actual release may not use an unpinned Apktool binary or a different JDK.
inputs = json.loads((ROOT / "build-inputs.json").read_text())
assert inputs["sdk_api"] == 36
assert inputs["jdk"] == 17
assert inputs["apktool"] == "2.11.1"
assert inputs["apktool_sha256"] == "56d59c524fc764263ba8d345754d8daf55b1887818b15cd3b594f555d249e2db"
print("PASS: Android SDK/JDK/Apktool toolchain release pin")


# All signed release verifiers must run the strict shared archive guard.
from pathlib import Path as _Path
v = (ROOT / "verify_release.py").read_text()
assert "from release_archive import inspect_zip" in v
assert 'archive_proof = inspect_zip(args.apk, args.base_apk, args.compiled_dex)' in v
workflow_file = _Path(__file__).resolve().parents[3] / ".github/workflows/android-0348-validation.yml"
if not workflow_file.is_file():
    workflow_file = ROOT / "ci-android-validation-workflow.yml"
workflow = workflow_file.read_text()
assert "tests/check_release_archive.py" in workflow
print("PASS: strict archive guard is wired to signed release and CI")
