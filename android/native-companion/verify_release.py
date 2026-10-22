"""Verify signing continuity, manifest boundary, source completeness and addon DEX."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent


def certificate(apk, tools):
    output = subprocess.check_output(["java", "-jar", str(tools / "lib/apksigner.jar"), "verify", "--verbose", "--print-certs", str(apk)], text=True)
    match = re.search(r"Signer #1 certificate SHA-256 digest: ([a-f0-9]+)", output)
    assert match, "Signing certificate missing"
    assert any("Verified using v" + str(v) + " scheme (APK Signature Scheme v" + str(v) + "): true" in output for v in (2, 3)), "APK v2/v3 signature missing"
    return match[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("apk", "base-apk", "build-tools", "decoded", "compiled-dex"):
        p.add_argument("--" + arg, type=Path, required=True)
    args = p.parse_args()
    cert = certificate(args.apk, args.build_tools)
    assert cert == certificate(args.base_apk, args.build_tools), "Installed-app signing identity changed"
    subprocess.run([str(args.build_tools / "zipalign"), "-c", "4", str(args.apk)], check=True)
    android = "{http://schemas.android.com/apk/res/android}"
    current = ET.parse(args.decoded / "AndroidManifest.xml").getroot()
    baseline = ET.parse(ROOT / "decoded/AndroidManifest.xml").getroot()
    # Only the approved app label, native UI theme and service description change.
    expected_app = baseline.find("application")
    expected_app.set(android + "label", "CELIKOM")
    for activity in expected_app.findall("activity"):
        if activity.get(android + "name") == "pro.celikom.nativeprobe.identitydiag.RecorderActivity":
            activity.set(android + "theme", "@android:style/Theme.Material.NoActionBar")
    for service in expected_app.findall("service"):
        if service.get(android + "name") == "pro.celikom.nativeprobe.identitydiag.ProbeService":
            service.find("property").set(android + "value", "User initiated current-song observation and automatic audio replacement; foreground playback continues until the user stops it")
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
    assert "versionCode='31'" in badging and "versionName='0.3.30'" in badging
    assert "sdkVersion:'28'" in badging and "targetSdkVersion:'36'" in badging
    with zipfile.ZipFile(args.apk) as built, zipfile.ZipFile(args.base_apk) as base:
        assert len(built.namelist()) == len(set(built.namelist())), "Duplicate APK entry"
        assert sorted(n for n in built.namelist() if re.fullmatch(r"classes\d*\.dex", n)) == ["classes.dex", "classes2.dex"]
        assert built.read("classes2.dex") == args.compiled_dex.read_bytes()
        for name in base.namelist():
            if name.startswith("assets/") and name != "assets/identity-integration-source.zip":
                assert built.read(name) == base.read(name), "Unexpected asset/catalogue change: " + name
        with zipfile.ZipFile(io.BytesIO(built.read("assets/identity-integration-source.zip"))) as source:
            names = source.namelist()
            assert any(n.endswith("/tests/TestResumeClock.java") for n in names)
            assert any(n.endswith("/verify_release.py") for n in names)
            for name in names:
                path = Path(name)
                assert path.parts[0] == "CELIKOM-0.3.30-source" and ".." not in path.parts
                assert not any(part in ("private", "deps", "classes", "build") for part in path.parts)
                relative = Path(*path.parts[1:])
                assert source.read(name) == (ROOT / relative).read_bytes(), "Stale embedded source: " + name
    proof = {
        "version": "0.3.30", "version_code": 31,
        "apk_sha256": hashlib.sha256(args.apk.read_bytes()).hexdigest(),
        "base_apk_sha256": hashlib.sha256(args.base_apk.read_bytes()).hexdigest(),
        "signer_sha256": cert,
        "addon_dex_sha256": hashlib.sha256(args.compiled_dex.read_bytes()).hexdigest(),
        "signing_continuity": True, "manifest_matches_approved_changes": True,
        "permissions_components_unchanged": True,
        "original_catalogue_assets_unchanged": True, "source_archive_verified": True,
        "physical_phone_playback_verified": False,
    }
    args.apk.with_suffix(".verification.json").write_text(json.dumps(proof, indent=2) + "\n")
    print("PASS: same signing identity; APK v2/v3 signature; alignment; version/API; approved manifest boundary and unchanged catalogue assets; exact compiled DEX and embedded source")


if __name__ == "__main__":
    main()
