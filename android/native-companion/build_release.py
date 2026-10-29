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
from release_contract import load_release, patch_apktool_metadata

ROOT = Path(__file__).resolve().parent
VERSION, VERSION_CODE, SIGNER_CERT_SHA256 = load_release()


def run(args, **kwargs):
    subprocess.run(list(map(str, args)), check=True, **kwargs)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "build-tools", "apktool", "base-apk", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--signing-dir", type=Path, default=None)
    parser.add_argument("--unsigned-inspection", action="store_true", help="structural smoke, NEVER a signed installable APK")
    parser.add_argument("--inspection-ci-dex", type=Path, default=None)
    parser.add_argument("--inspection-ci-dex-sha256", default=None)
    parser.add_argument("--deps-dir", type=Path, default=ROOT / "deps")
    parser.add_argument("--work-dir", type=Path, default=None)
    args = parser.parse_args()
    # Strictly separate read-only unsigned inspection from the release signer.
    inspection = args.unsigned_inspection
    if inspection:
        if args.signing_dir is not None:
            parser.error("unsigned inspection MUST NOT receive a signing directory")
        if args.inspection_ci_dex is None or args.inspection_ci_dex_sha256 is None:
            parser.error("unsigned inspection requires a CI DEX and its trusted SHA256")
        if not args.output.name.endswith("-INSPECTION-UNSIGNED.apk"):
            parser.error("unsigned inspections require a clearly marked UNSIGNED output")
        if not re.fullmatch(r"[a-f0-9]{64}", args.inspection_ci_dex_sha256):
            parser.error("expected CI DEX SHA256 is invalid")
        if sha(args.inspection_ci_dex) != args.inspection_ci_dex_sha256:
            parser.error("provided CI DEX does not match expected SHA256")
    else:
        if args.signing_dir is None:
            parser.error("signed release requires original --signing-dir")
        if args.inspection_ci_dex is not None or args.inspection_ci_dex_sha256 is not None:
            parser.error("prebuilt DEX is forbidden in real signed releases")
        if "UNSIGNED" in args.output.name.upper() or "INSPECTION" in args.output.name.upper():
            parser.error("signed release output cannot be named an inspection")
    inputs = json.loads((ROOT / "build-inputs.json").read_text())
    assert sha(args.base_apk) == inputs["base_apk_sha256"], "Unexpected baseline APK"
    assert sha(args.apktool) == inputs["apktool_sha256"], "Wrong Apktool binary"
    for name in ("aapt", "zipalign", "lib/d8.jar", "lib/apksigner.jar"):
        assert (args.build_tools / name).is_file(), "Missing Android Build Tool: " + name
    assert (args.sdk / "platforms/android-36/android.jar").is_file(), "Missing Android API 36"
    java_info = subprocess.check_output(["java", "-version"], stderr=subprocess.STDOUT, text=True)
    java_match = re.search(r'\bversion "([0-9]+)', java_info)
    assert inspection or (java_match and int(java_match.group(1)) == inputs["jdk"]), "Signed release requires pinned JDK 17"
    for name, digest in inputs["dependencies"].items():
        assert sha(args.deps_dir / name) == digest, "Dependency mismatch: " + name
    assert VERSION in args.output.name, "Output filename must include target release version"
    assert not args.output.exists(), "Refusing to overwrite an existing release"
    assert args.output.resolve() != args.base_apk.resolve(), "Cannot overwrite the pinned baseline"
    private = args.signing_dir.resolve() if not inspection else None
    if private is not None:
        assert not private.is_relative_to(ROOT), "Keep signing files outside source tree"
    build_root = ROOT / "addon/build"
    build_root.mkdir(parents=True, exist_ok=True)
    work = args.work_dir.resolve() if args.work_dir else Path(tempfile.mkdtemp(prefix="package-" + VERSION + "-", dir=build_root))
    work.mkdir(parents=True, exist_ok=True)
    source_inputs = sorted((ROOT / "addon/src").rglob("*.java"))
    source_digests = {str(p.relative_to(ROOT)): sha(p) for p in source_inputs}
    decoded = work / "decoded"
    if decoded.exists():
        shutil.rmtree(decoded)
    run(["java", "-jar", args.apktool, "d", args.base_apk, "-o", decoded, "-f"])
    shutil.rmtree(decoded / "smali_classes2")
    yml = decoded / "apktool.yml"
    config = yml.read_text()
    config = patch_apktool_metadata(config, VERSION, VERSION_CODE)
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
    legacy = decoded / "smali/pro/celikom/nativeprobe/MainActivity.smali"
    legacy_text = legacy.read_text()
    # Fresh explicit Intent for launcher: do not inherit MAIN/LAUNCHER task flags.
    # Preserve only the supported ACTION_SEND text contract.
    redirect = """.method protected onCreate(Landroid/os/Bundle;)V
    .locals 5
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
    new-instance v0, Landroid/content/Intent;
    const-class v1, Lpro/celikom/nativeprobe/identitydiag/RecorderActivity;
    invoke-direct {v0, p0, v1}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V
    invoke-virtual {p0}, Lpro/celikom/nativeprobe/MainActivity;->getIntent()Landroid/content/Intent;
    move-result-object v1
    if-eqz v1, :launch
    invoke-virtual {v1}, Landroid/content/Intent;->getAction()Ljava/lang/String;
    move-result-object v2
    const-string v3, "android.intent.action.SEND"
    invoke-virtual {v3, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :launch
    const-string v2, "android.intent.extra.TEXT"
    invoke-virtual {v1, v2}, Landroid/content/Intent;->getCharSequenceExtra(Ljava/lang/String;)Ljava/lang/CharSequence;
    move-result-object v4
    if-eqz v4, :launch
    invoke-virtual {v0, v3}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;
    const-string v3, "text/plain"
    invoke-virtual {v0, v3}, Landroid/content/Intent;->setType(Ljava/lang/String;)Landroid/content/Intent;
    invoke-virtual {v0, v2, v4}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/CharSequence;)Landroid/content/Intent;
    :launch
    invoke-virtual {p0, v0}, Lpro/celikom/nativeprobe/MainActivity;->startActivity(Landroid/content/Intent;)V
    invoke-virtual {p0}, Lpro/celikom/nativeprobe/MainActivity;->finish()V
    return-void
.end method"""
    legacy_text, count = re.subn(r"\.method protected onCreate\(Landroid/os/Bundle;\)V.*?\.end method", lambda m: redirect, legacy_text, flags=re.S)
    assert count == 1, "Unexpected legacy launcher layout"
    legacy.write_text(legacy_text)
    dex = work / "dex"
    shutil.rmtree(dex, ignore_errors=True)
    dex.mkdir()
    if inspection:
        # Inspection consumes exactly the already-tested CI/D8 bytes; it cannot
        # become a signed release and is never allowed to access signing files.
        shutil.copyfile(args.inspection_ci_dex, dex / "classes.dex")
    else:
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
        for test in ("TestPure", "TestHybrid", "TestContracts", "TestMobileActions", "TestAppPresentation", "TestNotifications", "TestDiagnosticArchive", "TestAudioTransfer", "TestBufferedAudio", "TestTransitionReadFence", "TestTransitionRecovery", "TestRequestPacing", "TestSourceStateWatchdog", "TestDiagnosticAccess", "TestPresencePreview", "TestDiagnosticRequest"):
            run(["java", "-cp", os.pathsep.join(map(str, [args.deps_dir / "json.jar", classes, tests, android])), "pro.celikom.nativeprobe.identitydiag." + test])
        assert source_digests == {str(p.relative_to(ROOT)): sha(p) for p in source_inputs}, "Sources changed during compile/tests"
        addon_jar = work / "addon.jar"
        run(["java", "sun.tools.jar.Main", "--create", "--file", addon_jar, "-C", classes, "."])
        d8 = ["java", "-Xmx1500m", "-cp", args.build_tools / "lib/d8.jar", "com.android.tools.r8.D8", "--min-api", "28", "--lib", android, "--output", dex]
        for jar in jars:
            d8.extend(["--classpath", jar])
        run([*d8, addon_jar])
    # Owner recovery sources belong in Git, never in a distributed APK.
    (decoded / "assets/identity-integration-source.zip").unlink(missing_ok=True)
    unsigned, aligned = work / "unsigned.apk", work / "aligned.apk"
    run(["java", "-jar", args.apktool, "b", decoded, "-o", unsigned])
    # Recreate, rather than append, so an Apktool-restored addon entry cannot
    # leave two classes2.dex records or stale code in the signed package.
    addon_apk = work / "with-addon.apk"
    with zipfile.ZipFile(unsigned) as source_apk, zipfile.ZipFile(addon_apk, "w") as z:
        assert len(source_apk.namelist()) == len(set(source_apk.namelist()))
        for info in source_apk.infolist():
            if info.filename not in ("classes2.dex", "assets/identity-integration-source.zip"):
                z.writestr(info, source_apk.read(info.filename))
        assert len(list(dex.glob("*.dex"))) == 1, "Unexpected additional addon DEX"
        z.write(dex / "classes.dex", "classes2.dex")
    run([args.build_tools / "zipalign", "-f", "4", addon_apk, aligned])
    if inspection:
        # Same Apktool + resource assembly + zipalign as actual signing path.
        # This artefact MUST stay outside user release distribution.
        shutil.copyfile(aligned, args.output)
        run(["python3", ROOT / "verify_unsigned_inspection.py",
             "--apk", args.output, "--base-apk", args.base_apk,
             "--compiled-dex", dex / "classes.dex", "--build-tools", args.build_tools,
             "--expected-dex-sha256", args.inspection_ci_dex_sha256])
        assert source_digests == {str(p.relative_to(ROOT)): sha(p) for p in source_inputs}, "Sources changed during inspection"
        print("UNSIGNED INSPECTION ONLY; NOT INSTALLABLE:", args.output, "SHA256", sha(args.output))
        return
    signing = json.loads((private / "signing.json").read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="celikom-sign-") as tmp:
        tmp = Path(tmp)
        for name, key in (("store-password", "store_password"), ("key-password", "key_password")):
            p = tmp / name
            p.write_text(signing[key])
            p.chmod(0o600)
        run(["java", "-jar", args.build_tools / "lib/apksigner.jar", "sign", "--ks", private / "celikom-native-probe.p12", "--ks-key-alias", signing["alias"], "--ks-pass", "file:" + str(tmp / "store-password"), "--key-pass", "file:" + str(tmp / "key-password"), "--out", args.output, aligned])
    run(["python3", ROOT / "verify_release.py", "--apk", args.output, "--base-apk", args.base_apk, "--build-tools", args.build_tools, "--decoded", decoded, "--compiled-dex", dex / "classes.dex", "--apktool", args.apktool])
    assert source_digests == {str(p.relative_to(ROOT)): sha(p) for p in source_inputs}, "Sources changed during packaging"
    print("APK", args.output, "BYTES", args.output.stat().st_size, "SHA256", sha(args.output))


if __name__ == "__main__":
    main()
