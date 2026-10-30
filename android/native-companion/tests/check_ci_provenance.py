"""Negative tests for DEX/source/CI record substitution."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ci_provenance import prepare_provenance, validate_provenance

checks = 0
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "addon/src/pro/celikom/nativeprobe/identitydiag").mkdir(parents=True)
    (root / "release-spec.json").write_bytes((ROOT / "release-spec.json").read_bytes())
    for p in sorted((ROOT / "addon/src").rglob("*.java")):
        to = root / p.relative_to(ROOT)
        to.parent.mkdir(parents=True, exist_ok=True)
        to.write_bytes(p.read_bytes())
    dex = root / "classes.dex"
    dex.write_bytes(b"dex\n" + b"\0"*64)
    record = prepare_provenance(root, "a" * 40, dex)
    assert validate_provenance(record, root, dex) == "a" * 40
    checks += 1

    def reject(changed, label):
        global checks
        try:
            validate_provenance(changed, root, dex)
        except ValueError:
            checks += 1
            return
        raise AssertionError("Unsafe CI provenance accepted: " + label)

    for field, value in [
        ("commit", "unknown"),
        ("version", "0.3.51"),
        ("version_code", 52),
        ("signing_certificate_sha256", "f" * 64),
        ("dex_sha256", "0" * 64),
        ("java_source_fingerprint", "b" * 64),
        ("signature_attestation", True),
        ("kind", "SIGNED_RELEASE"),
    ]:
        wrong = dict(record); wrong[field] = value
        reject(wrong, field)
    java = root / "addon/src/pro/celikom/nativeprobe/identitydiag/AppVersion.java"
    java.write_text(java.read_text() + "\n/* changed since CI */\n")
    reject(record, "changed Java sources after CI")
    java.write_text(java.read_text().replace("\n/* changed since CI */\n", ""))
    dex.write_bytes(dex.read_bytes() + b"changed")
    reject(record, "changed DEX after CI")

print("PASS:", checks, "CI source/DEX provenance negative cases")
