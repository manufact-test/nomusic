"""Release must not accept unsigned inspection as a substitute for signing."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
builder = ROOT / "build_release.py"
common = [
    sys.executable, str(builder), "--sdk", "/nonexistent/sdk",
    "--build-tools", "/nonexistent/tools", "--apktool", "/nonexistent/apktool.jar",
    "--base-apk", "/nonexistent/base.apk", "--output", "/tmp/CELIKOM-0.3.56-INSPECTION-UNSIGNED.apk",
]


def must_fail(args, expected):
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0 or expected not in result.stderr:
        raise AssertionError("Release mode bypass: " + expected + "\n" + result.stderr[-1200:])


must_fail(common, "signed release requires original --signing-dir")
must_fail(common + ["--unsigned-inspection"], "unsigned inspection requires the source-to-DEX CI provenance JSON")
must_fail(common + ["--unsigned-inspection", "--signing-dir", "/does-not-matter"],
          "unsigned inspection MUST NOT receive a signing directory")
must_fail(common + ["--unsigned-inspection", "--inspection-ci-provenance", "/fake"],
          "unsigned inspection requires a CI DEX")
must_fail(common + ["--unsigned-inspection", "--inspection-ci-dex", "/fake"],
          "unsigned inspection requires the source-to-DEX CI provenance JSON")
must_fail(common + ["--signing-dir", "/signing", "--inspection-ci-dex", "/fake"],
          "prebuilt DEX is forbidden in real signed releases")

original = builder.read_text()
assert 'args.output.name.endswith("-INSPECTION-UNSIGNED.apk")' in original
assert 'parser.error("prebuilt DEX is forbidden in real signed releases")' in original
assert 'args.signing_dir is None' in original
assert 'shutil.copyfile(aligned, args.output)' in original
assert '"--expected-dex-sha256", args.inspection_ci_dex_sha256' in original
assert '"--ci-provenance", args.inspection_ci_provenance' in original
assert 'ci_commit = validate_provenance' in original
assert 'verify_unsigned_inspection.py' in original
assert 'signing = json.loads((private / "signing.json").read_text())' in original
assert 'run(["python3", ROOT / "verify_release.py"' in original
inspector = (ROOT / "verify_unsigned_inspection.py").read_text()
assert 'if check.returncode == 0:' in inspector
assert 'signing_verified": False' in inspector and 'signed_release": False' in inspector
print("PASS: unsigned inspection mode cannot use release signing or become a signed installable build")
