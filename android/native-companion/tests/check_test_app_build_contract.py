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
for required in ("check_0385_seek_baseline.py", "UpdateCenter", "REQUEST_INSTALL_PACKAGES", "celikom_test_icon.xml", "BuildConfig.smali"):
    assert required in builder or required in verifier, "Missing test build safety gate: " + required
assert "if not (v2 or v3)" in verifier
assert "base_v3" in verifier and "signer_v3" in verifier
assert "APK Signature Scheme v3" in verifier
assert "APPLICATION_ID" in builder and "SPEC[\"package\"]" in builder
assert "BuildConfig" in verifier and "SPEC[\"stable_package\"]" in verifier
assert 'activity.set(A + "label", SPEC["label"])' in builder
assert "launcher_label_verified" in verifier
runner = (ROOT / "tests/run_addon_host.py").read_text(encoding="utf-8")
assert "CELIKOM_ANDROID_DEPS" in runner and "DEPS/name" in runner

workflow = (ROOT.parents[1] / ".github/workflows/android-0385-test-app-build.yml").read_text(encoding="utf-8")
assert "workflow_call:" in workflow
assert "source_sha" in workflow and "source_branch" in workflow
assert "source_repository" in workflow and "validation_run_id" in workflow
assert "github.run_id" not in workflow
for forbidden_trigger in ("\\npush:", "\\npull_request:", "\\nworkflow_dispatch:", "\\nworkflow_run:"):
    assert forbidden_trigger not in workflow, "Test APK builder must be callable only after validation"
for forbidden_action in ("stable.json", "/updates/android/stable.json", "publish-stable"):
    assert forbidden_action not in workflow, "Test APK workflow must not publish or touch stable OTA: " + forbidden_action
assert "scp -P 65002" in workflow and "CELIKOM_HOSTINGER_SSH_KEY" in workflow
assert "CELIKOM_ANDROID_SIGNING_P12_B64" in workflow
assert "actions/upload-artifact@v4" in workflow and "retention-days: 7" in workflow
assert "fetch-depth: 0" in workflow
assert "merge-base" in workflow and "--is-ancestor" in workflow
assert "'git','diff','--quiet'" in workflow
for required in (
    "signature_v2_verified", "signature_v3_verified", "separate_android_sandbox",
    "stable_manifest_reference_absent", "ota_updater_absent", "package_id_is_distinct",
):
    assert required in verifier, "Missing final APK verification field: " + required

print("PASS: CELIKOM Test reusable build contract and OTA isolation")
