"""Static safety checks for the isolated CELIKOM Test packaging path."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
spec = json.loads((ROOT / "test-app-spec.json").read_text(encoding="utf-8"))
builder = (ROOT / "build_test_release.py").read_text(encoding="utf-8")
verifier = (ROOT / "verify_test_release.py").read_text(encoding="utf-8")

assert spec["package"] == "pro.celikom.nativeprobe.test"
assert spec["stable_package"] == "pro.celikom.nativeprobe"
assert spec["label"] == "CELIKOM Test"
assert spec["version"] == "0.3.85-test"
assert spec["version_code"] == 86085
assert spec["signing_certificate_sha256"] == "67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f"
assert spec["test_permission"].startswith(spec["package"] + ".")
assert spec["file_provider_authority"].startswith(spec["package"] + ".")
assert spec["startup_authority"].startswith(spec["package"] + ".")
assert spec["update_notice"] == "Тестовая сборка · автоматические обновления отключены"

for forbidden in ("from release_contract", "load_release(", "release-spec.json", "android-auto-publish-hostinger"):
    assert forbidden not in builder, "Test builder must not route through stable release code: " + forbidden
for excluded in ("UpdateCenter.java", "UpdateCheckJob.java", "UpdateInstallReceiver.java"):
    assert excluded in builder, "Test builder must explicitly exclude updater source: " + excluded
for required in ("check_0385_seek_baseline.py", "UpdateCenter", "REQUEST_INSTALL_PACKAGES", "celikom_test_icon.xml"):
    assert required in builder or required in verifier, "Missing test build safety gate: " + required
for required in (
    "signature_v2_verified", "signature_v3_verified", "separate_android_sandbox",
    "stable_manifest_reference_absent", "ota_updater_absent", "package_id_is_distinct",
):
    assert required in verifier, "Missing final APK verification field: " + required

print("PASS: CELIKOM Test packaging identity and OTA isolation contract")
