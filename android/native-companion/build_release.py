"""Offline Android-only build from the verified 0.3.22 APK and recovered source.

No server, SSH, account, catalogue export or production mutation is involved.
Signing material and binary dependencies are external to Git and source bundles.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
VERSION = "0.3.32"
VERSION_CODE = 33


def run(args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "build-tools", "apktool", "base-apk", "signing-dir", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--deps-dir", type=Path, default=ROOT / "deps")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "addon/build/package")
    args = parser.parse_args()
    inputs = json.loads((ROOT / "build-inputs.json").read_text())
    assert sha(args.base_apk) == inputs["base_apk_sha256"], "Unexpected baseline APK"
    assert ('NAME="' + VERSION + '"') in (ROOT / "addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java").read_text(), "Source version mismatch"
    for name, digest in inputs["dependencies"].items():
        assert sha(args.deps_dir / name) == digest, "Dependency mismatch: " + name
    private = args.signing_dir.resolve()
    assert not private.is_relative_to(ROOT), "Keep signing files outside source tree"
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    decoded = work / "decoded"
    if decoded.exists():
        shutil.rmtree(decoded)
    run(["java", "-jar", args.apktool, "d", args.base_apk, "-o", decoded, "-f"])
    shutil.rmtree(decoded / "smali_classes2")
    yml = decoded / "apktool.yml"
    config = yml.read_text()
    config = re.sub(r"versionCode: \d+", "versionCode: " + str(VERSION_CODE), config)
    config = re.sub(r"versionName: [^\n]+", "versionName: " + VERSION, config)
    yml.write_text(config)
    manifest = decoded / "AndroidManifest.xml"
    ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
    tree = ET.parse(manifest)
    android_attr = "{http://schemas.android.com/apk/res/android}"
    application = tree.getroot().find("application")
    application.set(android_attr + "label", "CELIKOM")
    for activity in application.findall("activity"):
        if activity.get(android_attr + "name") == "pro.celikom.nativeprobe.identitydiag.RecorderActivity":
            activity.set(android_attr + "theme", "@android:style/Theme.Material.NoActionBar")
    for service in application.findall("service"):
        if service.get(android_attr + "name") == "pro.celikom.nativeprobe.identitydiag.ProbeService":
            service.find("property").set(android_attr + "value", "User initiated current-song observation and automatic audio replacement; foreground playback continues until the user stops it")
    tree.write(manifest, encoding="utf-8", xml_declaration=True)
    for p in (decoded / "smali/pro/celikom/nativeprobe").rglob("*.smali"):
        source = p.read_text()
        updated = source.replace("0.3.22-probe", VERSION)
        if p.name == "BuildConfig.smali":
            updated = re.sub(r"(\.field public static final VERSION_CODE:I = )0x[0-9a-f]+", lambda m: m[1] + hex(VERSION_CODE), updated)
        if source != updated:
            p.write_text(updated)
    classes = work / "classes"
    shutil.rmtree(classes, ignore_errors=True)
    classes.mkdir()
    android = args.sdk / "platforms/android-36/android.jar"
    jars = [args.deps_dir / n for n in sorted(inputs["dependencies"]) if n != "json.jar"]
    cp = os.pathsep.join(map(str, [android, *jars]))
    run(["java", "com.sun.tools.javac.Main", "-encoding", "UTF-8", "-source", "8", "-target", "8", "-cp", cp, "-d", classes, *sorted((ROOT / "addon/src").rglob("*.java"))])
    run(["python3", ROOT / "tests/run_engine.py"], env={**os.environ, "CELIKOM_ANDROID_DEPS": str(args.deps_dir.resolve())})
    tests = work / "tests"
    tests.mkdir(exist_ok=True)
    test_cp = os.pathsep.join(map(str, [args.deps_dir / "json.jar", classes, android]))
    run(["java", "com.sun.tools.javac.Main", "-encoding", "UTF-8", "-source", "8", "-target", "8", "-cp", test_cp, "-d", tests, *sorted((ROOT / "addon").glob("Test*.java"))])
    for test in ("TestPure", "TestHybrid", "TestContracts", "TestMobileActions", "TestAppPresentation", "TestNotifications", "TestDiagnosticArchive", "TestAudioTransfer", "TestBufferedAudio", "TestTransitionReadFence", "TestTransitionRecovery", "TestRequestPacing"):
        run(["java", "-cp", os.pathsep.join(map(str, [args.deps_dir / "json.jar", classes, tests, android])), "pro.celikom.nativeprobe.identitydiag." + test])
    addon_jar = work / "addon.jar"
    run(["java", "sun.tools.jar.Main", "--create", "--file", addon_jar, "-C", classes, "."])
    dex = work / "dex"
    shutil.rmtree(dex, ignore_errors=True)
    dex.mkdir()
    d8 = ["java", "-Xmx1500m", "-cp", args.build_tools / "lib/d8.jar", "com.android.tools.r8.D8", "--min-api", "28", "--lib", android, "--output", dex]
    for jar in jars:
        d8.extend(["--classpath", jar])
    run([*d8, addon_jar])
    bundle = io.BytesIO()
    source_files = [*sorted((ROOT / "addon/src").rglob("*.java")), *sorted((ROOT / "addon").glob("Test*.java")), ROOT / "build_release.py", ROOT / "verify_release.py", ROOT / "build-inputs.json", ROOT / "RECOVERED-0.3.22.json", ROOT / "README.md", *[p for p in sorted((ROOT / "tests").rglob("*")) if p.is_file() and p.suffix in (".java", ".py", ".tsv")]]
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in source_files:
            info = zipfile.ZipInfo("CELIKOM-" + VERSION + "-source/" + str(p.relative_to(ROOT)), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    (decoded / "assets/identity-integration-source.zip").write_bytes(bundle.getvalue())
    unsigned, aligned = work / "unsigned.apk", work / "aligned.apk"
    run(["java", "-jar", args.apktool, "b", decoded, "-o", unsigned])
    # Recreate, rather than append, so an Apktool-restored addon entry cannot
    # leave two classes2.dex records or stale code in the signed package.
    addon_apk = work / "with-addon.apk"
    with zipfile.ZipFile(unsigned) as source_apk, zipfile.ZipFile(addon_apk, "w") as z:
        assert len(source_apk.namelist()) == len(set(source_apk.namelist()))
        for info in source_apk.infolist():
            if info.filename != "classes2.dex":
                z.writestr(info, source_apk.read(info.filename))
        assert len(list(dex.glob("*.dex"))) == 1, "Unexpected additional addon DEX"
        z.write(dex / "classes.dex", "classes2.dex")
    run([args.build_tools / "zipalign", "-f", "4", addon_apk, aligned])
    signing = json.loads((private / "signing.json").read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="celikom-sign-") as tmp:
        tmp = Path(tmp)
        for name, key in (("store-password", "store_password"), ("key-password", "key_password")):
            p = tmp / name
            p.write_text(signing[key])
            p.chmod(0o600)
        run(["java", "-jar", args.build_tools / "lib/apksigner.jar", "sign", "--ks", private / "celikom-native-probe.p12", "--ks-key-alias", signing["alias"], "--ks-pass", "file:" + str(tmp / "store-password"), "--key-pass", "file:" + str(tmp / "key-password"), "--out", args.output, aligned])
    run(["python3", ROOT / "verify_release.py", "--apk", args.output, "--base-apk", args.base_apk, "--build-tools", args.build_tools, "--decoded", decoded, "--compiled-dex", dex / "classes.dex"])
    print("APK", args.output, "BYTES", args.output.stat().st_size, "SHA256", sha(args.output))


if __name__ == "__main__":
    main()
