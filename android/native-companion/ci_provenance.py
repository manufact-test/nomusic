"""Non-secret source-to-DEX provenance manifest for native Android CI.

The manifest is a build evidence record, not a cryptographic signature.
Download it together with the DEX from the same successful GitHub Actions run.
"""
from pathlib import Path
import hashlib
import json
import re
from release_contract import load_release


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_fingerprint(root):
    root = Path(root)
    src = root / "addon/src"
    files = sorted(src.rglob("*.java"))
    if len(files) < 15:
        raise ValueError("Incomplete Android sources for provenance")
    digests = {str(p.relative_to(root)): sha256(p) for p in files}
    return hashlib.sha256(json.dumps(digests, sort_keys=True).encode()).hexdigest()


def prepare_provenance(root, commit, compiled_dex):
    root = Path(root)
    version, code, signer = load_release(root)
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Git commit SHA must be complete")
    return {
        "kind": "CELIKOM_ANDROID_CI_JDK17_SOURCE_DEX",
        "commit": commit,
        "version": version,
        "version_code": code,
        "signing_certificate_sha256": signer,
        "java_source_fingerprint": source_fingerprint(root),
        "dex_sha256": sha256(compiled_dex),
        "signature_attestation": False,
    }


def validate_provenance(record, root, compiled_dex):
    root = Path(root)
    version, code, signer = load_release(root)
    if not isinstance(record, dict):
        raise ValueError("Invalid CI provenance")
    if record.get("kind") != "CELIKOM_ANDROID_CI_JDK17_SOURCE_DEX":
        raise ValueError("Unknown CI evidence type")
    commit = record.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Missing complete GitHub commit")
    if record.get("version") != version or record.get("version_code") != code:
        raise ValueError("CI provenance/version mismatch")
    if record.get("signing_certificate_sha256") != signer:
        raise ValueError("CI signing identity mismatch")
    if record.get("java_source_fingerprint") != source_fingerprint(root):
        raise ValueError("CI DEX source code differs from local Java sources")
    if record.get("dex_sha256") != sha256(compiled_dex):
        raise ValueError("CI DEX hash does not match actual bytes")
    if record.get("signature_attestation") is not False:
        raise ValueError("CI provenance must not masquerade as signed attestation")
    return commit
