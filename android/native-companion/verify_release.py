"""Verify signing continuity, manifest boundary, source completeness and addon DEX."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from release_contract import load_release
from release_archive import inspect_zip

ROOT = Path(__file__).resolve().parent
VERSION, VERSION_CODE, SIGNER_CERT_SHA256 = load_release()


def certificate(apk, tools):
    output = subprocess.check_output(["java", "-jar", str(tools / "lib/apksigner.jar"), "verify", "--verbose", "--print-certs", str(apk)], text=True)
    match = re.search(r"Signer #1 certificate SHA-256 digest: ([a-f0-9]+)", output)
    assert match, "Signing certificate missing"
    assert any("Verified using v" + str(v) + " scheme (APK Signature Scheme v" + str(v) + "): true" in output for v in (2, 3)), "APK v2/v3 signature missing"
    return match[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("apk", "base-apk", "build-tools", "decoded", "compiled-dex", "apktool"):
        p.add_argument("--" + arg, type=Path, required=True)
    args = p.parse_args()
    pinned_inputs = json.loads((ROOT / "build-inputs.json").read_text())
    assert hashlib.sha256(args.apktool.read_bytes()).hexdigest() == pinned_inputs["apktool_sha256"], "Verifier Apktool mismatch"
    cert = certificate(args.apk, args.build_tools)
    assert cert == certificate(args.base_apk, args.build_tools) == SIGNER_CERT_SHA256, "Signer differs from installed baseline or pinned certificate"
    subprocess.run([str(args.build_tools / "zipalign"), "-c", "4", str(args.apk)], check=True)
    android = "{http://schemas.android.com/apk/res/android}"
    current = ET.parse(args.decoded / "AndroidManifest.xml").getroot()
    # Decode the supplied, SHA-pinned baseline APK instead of relying on a
    # stale machine-local decoded directory. This is safe for offline rebuilds.
    with tempfile.TemporaryDirectory(prefix="celikom-verify-baseline-") as directory:
        reference = Path(directory) / "baseline"
        subprocess.run(["java", "-jar", str(args.apktool), "d", str(args.base_apk),
                        "-f", "-o", str(reference)], check=True, stdout=subprocess.DEVNULL)
        baseline = ET.parse(reference / "AndroidManifest.xml").getroot()
    # Only the approved app label, native UI theme and service description change.
    expected_app = baseline.find("application")
    expected_app.set(android + "label", "CELIKOM")
    for activity in expected_app.findall("activity"):
        if activity.get(android + "name") == "pro.celikom.nativeprobe.identitydiag.RecorderActivity":
            activity.set(android + "theme", "@android:style/Theme.Material.NoActionBar")
    for service in expected_app.findall("service"):
        if service.get(android + "name") == "pro.celikom.nativeprobe.identitydiag.ProbeService":
            service.find("property").set(android + "value", "User initiated current-song observation and automatic audio replacement; foreground playback continues until the user stops it")
    # Exact allowlist for Update Center. Any extra Android permission/component fails.
    ET.SubElement(baseline, "uses-permission", {android + "name": "android.permission.REQUEST_INSTALL_PACKAGES"})
    ET.SubElement(expected_app, "service", {
        android + "name": "pro.celikom.nativeprobe.identitydiag.UpdateCheckJob",
        android + "permission": "android.permission.BIND_JOB_SERVICE",
        android + "exported": "false",
    })
    ET.SubElement(expected_app, "receiver", {
        android + "name": "pro.celikom.nativeprobe.identitydiag.UpdateInstallReceiver",
        android + "exported": "false",
    })
    def structure(node):
        # Apktool may reorder names in a flags bitmask without changing it.
        attributes = [(key, "|".join(sorted(value.split("|"))) if key == android + "foregroundServiceType" else value) for key, value in node.attrib.items()]
        return node.tag, sorted(attributes), [structure(child) for child in node]
    assert structure(current) == structure(baseline), "Application manifest differs from verified baseline"
    assert current.get("package") == "pro.celikom.nativeprobe"
    app = current.find("application")
    assert app.get(android + "allowBackup") == "false"
    assert app.get(android + "usesCleartextTraffic") == "false"
    denied = ("BIND_NOTIFICATION_LISTENER_SERVICE", "BIND_ACCESSIBILITY_SERVICE", "RECORD_AUDIO", "READ_SMS", "READ_CONTACTS", "QUERY_ALL_PACKAGES")
    assert not any(any(key in value for key in denied) for node in current.iter() for value in node.attrib.values())
    badging = subprocess.check_output([str(args.build_tools / "aapt"), "dump", "badging", str(args.apk)], text=True)
    assert "versionCode='" + str(VERSION_CODE) + "'" in badging and "versionName='" + VERSION + "'" in badging
    assert "sdkVersion:'28'" in badging and "targetSdkVersion:'36'" in badging
    archive_proof = inspect_zip(args.apk, args.base_apk, args.compiled_dex)
    assert archive_proof["original_assets_unchanged"]
    assert app.get(android + "debuggable", "false") == "false"
    legacy = (args.decoded / "smali/pro/celikom/nativeprobe/MainActivity.smali").read_text()
    method = re.search(r"\.method protected onCreate\(Landroid/os/Bundle;\)V(.*?)\.end method", legacy, re.S).group(1)
    assert "identitydiag/RecorderActivity" in method and "->finish()V" in method and "setContentView" not in method
    assert "new-instance v0, Landroid/content/Intent;" in method and "->setClass(" not in method, "Launcher still forwards untrusted task flags"
    assert "android.intent.action.SEND" in method, "Shared text links no longer forwarded"
    # Inspect the *signed* DEX directly instead of decompiling the entire APK.
    # The byte-for-byte compiled DEX comparison above binds all source/tests to
    # this artifact; repeated full Apktool decompilation can stall on Android 16.
    with zipfile.ZipFile(args.apk) as signed:
        dex = signed.read("classes2.dex")
        assert dex.startswith(b"dex" + bytes([10])), "Signed addon has no DEX header"
        markers = (
            VERSION.encode("ascii"), b"ReplacementEngine", b"AudioOwnership", b"UpdateInstallReceiver", b"finishAndRemoveTask",
            b"ClockSupervisor", b"SourceEventArbiter", b"retireDecoder",
            b"SourceTransitionGate", b"AudioContinuityMonitor",
            b"audio_command_anomaly", b"audio_decoder_start",
            b"replacement_resume_fast", b"replacement_duration_mismatch",
            b"SupportTrace", b"PlaybackDuration", b"AlbumMatch",
        )
        for marker in markers:
            assert marker in dex, "Signed APK missing code marker: " + marker.decode()
    addon = ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag"
    engine = (addon / "ReplacementEngine.java").read_text()
    ownership = (addon / "AudioOwnership.java").read_text()
    matcher = (addon / "AlbumMatch.java").read_text()
    updater = (addon / "UpdateInstallReceiver.java").read_text()
    assert "PackageInstaller.STATUS_SUCCESS" in updater
    assert "getLongVersionCode()" in updater and "getAppTasks()" in updater
    assert "finishAndRemoveTask()" in updater
    success_callback = re.search(
        r"else if \(status == PackageInstaller\.STATUS_SUCCESS\) \{(.*?)\n\s*\} else",
        updater, re.S
    )
    assert success_callback and "closeTasksAfterVerifiedInstall(context, expectedCode)" in success_callback.group(1)
    assert "startActivity" not in success_callback.group(1), "Successful update must close/remove tasks, not relaunch CELIKOM"
    assert "PAUSE_RESUME_FADE_MS=180" in engine and "PAUSE_GRACE_MS=30000" in engine
    assert "HANDOVER_DRIFT_MS=350" in engine
    assert "warmSeekTransition" not in engine and "handoverPending" not in engine, "Competing audio clock flags returned"
    assert "audioOwner.seekInFlight(p)" in engine and "audioOwner.handoverWaitForClock(alignLive)" in engine
    assert "handoverAwaitingClock()" in ownership and "mayConsumeCompletion" in ownership
    assert "grantReplacement" in ownership and "validPause" in ownership
    assert "audioOwner.grantReplacement" in engine and "audioOwner.validPause" in engine
    assert matcher.count("artistKey(") >= 3 and '"quest pistols"' in matcher
    assert "SourceTransitionGate" in (addon / "SourceTransitionGate.java").read_text()
    assert "AudioContinuityMonitor" in (addon / "AudioContinuityMonitor.java").read_text()
    source_digests = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "addon/src").rglob("*.java"))}
    proof = {
        "version": VERSION, "version_code": VERSION_CODE,
        "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        "base_apk_sha256": hashlib.sha256(args.base_apk.read_bytes()).hexdigest(),
        "signer_sha256": cert, "signer_matches_pinned_identity": cert == SIGNER_CERT_SHA256,
        "addon_dex_sha256": hashlib.sha256(args.compiled_dex.read_bytes()).hexdigest(),
        "signing_continuity": True, "manifest_matches_approved_changes": True,
        "permissions_components_unchanged": False,
        "original_catalogue_assets_unchanged": True, "source_archive_absent": True, "legacy_launcher_gated": True,
        "archive_integrity_verified": True, "asset_count": archive_proof["asset_count"],
        "physical_phone_playback_verified": False,
        "final_apk_artist_matcher_verified": True, "final_apk_handover_guard_verified": True, "final_apk_exclusive_audio_gate_verified": True, "final_apk_handover_tolerance_ms": 350,
        "source_fingerprint": hashlib.sha256(json.dumps(source_digests, sort_keys=True).encode()).hexdigest(),
    }
    args.apk.with_suffix(".verification.json").write_text(json.dumps(proof, indent=2) + "\n")
    print("PASS: same signing identity; APK v2/v3 signature; alignment; version/API; approved manifest boundary and unchanged catalogue assets; exact compiled addon DEX; no recovery sources or signing files; legacy launcher redirects to gated UI")


if __name__ == "__main__":
    main()
