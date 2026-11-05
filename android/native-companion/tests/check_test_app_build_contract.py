"""Static safety checks for the isolated CELIKOM Test packaging path."""
from pathlib import Path
import json
import shutil
import tempfile
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_test_release import patch_test_sources
spec = json.loads((ROOT / "test-app-spec.json").read_text(encoding="utf-8"))
builder = (ROOT / "build_test_release.py").read_text(encoding="utf-8")
verifier = (ROOT / "verify_test_release.py").read_text(encoding="utf-8")

assert spec["package"] == "pro.celikom.nativeprobe.test"
assert spec["stable_package"] == "pro.celikom.nativeprobe"
assert spec["label"] == "CELIKOM Test"
assert spec["version"] == "0.3.85-test.44"
assert spec["version_code"] == 86129
assert spec["apk_filename"] == "CELIKOM-Android-0.3.85-TEST-44-OWNER-ENDPOINT-SIGNED.apk"
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
assert "check_background_diagnostics.py" in (ROOT / "tests/run_engine.py").read_text(encoding="utf-8")
assert "TestLookaheadPrefetchHandoff.java" in (ROOT / "tests/run_engine.py").read_text(encoding="utf-8")
assert "requestFastJoinSamples" in (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/ProbeService.java").read_text(encoding="utf-8")
# Test.41: never deny playback for a repeated unverified same-session OPEN,
# and never enable the Test.40 four-sample cold clock restriction in production.
service_source = (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/ProbeService.java").read_text(encoding="utf-8")
assert "new ReplacementEngine(this,true,true,false)" in service_source
assert "recheckQuietSourceController(session);" not in service_source
assert "source_same_session_open_ignored" in service_source
assert "replacement.adaptiveJoinExperiment=true;" in service_source
assert "HybridIdentity.java" in (ROOT / "tests/run_engine.py").read_text(encoding="utf-8")
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
assert 'SOURCE_RUN="$VALIDATION_RUN_ID"' in workflow
assert 'gh run download "$SOURCE_RUN"' in workflow
caller = (ROOT.parents[1] / ".github/workflows/android-0348-validation.yml").read_text(encoding="utf-8")
assert "build-celikom-test:" in caller
assert "needs: native-android" in caller
assert "uses: ./.github/workflows/android-0385-test-app-build.yml" in caller
assert "validation_run_id: ${{ github.run_id }}" in caller
for required in (
    "signature_v2_verified", "signature_v3_verified", "separate_android_sandbox",
    "stable_manifest_reference_absent", "ota_updater_absent", "package_id_is_distinct",
):
    assert required in verifier, "Missing final APK verification field: " + required


# Real patch smoke: confirm the test APK source is styled without changing stable Java.
activity_rel = Path("pro/celikom/nativeprobe/identitydiag/RecorderActivity.java")
stable_activity = (ROOT / "addon/src" / activity_rel).read_text(encoding="utf-8")
assert "styleLoginInput(" not in stable_activity
assert "v.setTextColor(FG);v.setHintTextColor(MUTED);" in stable_activity

manifest = ET.parse(ROOT / "decoded/AndroidManifest.xml")
android_ns = "{http://schemas.android.com/apk/res/android}"
activities = manifest.getroot().find("application").findall("activity")
recorder = next(a for a in activities if a.get(android_ns + "name", "").endswith(".RecorderActivity"))
assert recorder.get(android_ns + "theme") == "@android:style/Theme.Material.Light.NoActionBar"

with tempfile.TemporaryDirectory(prefix="celikom-test-login-contract-") as work:
    source_root = Path(work) / "src"
    shutil.copytree(ROOT / "addon/src", source_root)
    patch_test_sources(source_root)
    styled = (source_root / activity_rel).read_text(encoding="utf-8")
    assert styled.count("void styleLoginInput(EditText field)") == 1
    assert styled.count("styleLoginInput(email);styleLoginInput(password);") == 1
    assert styled.count("styleLoginInput(code);") == 1
    assert styled.count("styleLoginInput(") == 4
    assert "InputType.TYPE_TEXT_VARIATION_PASSWORD" in styled
    assert "v.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO)" in styled
    assert "api().login(address,pass" in styled and "api().verify(address,value" in styled
    assert "field.setHighlightColor(0xffbfdcff)" in styled
    for color in ("0xff1f2933", "0xff52606d", "0xff1558b0"):
        assert color in styled
    for api in ("setTextCursorDrawable", "setTextSelectHandle(", "setTextSelectHandleLeft(", "setTextSelectHandleRight("):
        assert api in styled

def luminance(rgb):
    channels = [(rgb >> shift) & 255 for shift in (16, 8, 0)]
    channels = [v / 255 for v in channels]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))

def contrast(rgb, background=0xffffff):
    levels = sorted((luminance(rgb), luminance(background)))
    return (levels[1] + 0.05) / (levels[0] + 0.05)

assert contrast(0x1f2933) >= 7       # Entered text and password masking
assert contrast(0x52606d) >= 4.5    # Placeholder
assert contrast(0x1558b0) >= 3      # Cursor and selection handles

print("PASS: CELIKOM Test reusable build, login contrast and OTA isolation")
