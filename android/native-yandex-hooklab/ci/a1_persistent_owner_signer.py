"""Import and pin the owner-controlled persistent Android APK signing key."""
from __future__ import annotations
import base64
import os
import re
import subprocess
from pathlib import Path

DEST_STORE_PASSWORD = "ephemeral-lab-only"
DEST_KEY_PASSWORD = "ephemeral-lab-only"
DEST_ALIAS = "own-key"
SECRET_NAMES = (
    "CELIKOM_A1_OWNER_KEYSTORE_BASE64",
    "CELIKOM_A1_OWNER_KEYSTORE_PASSWORD",
    "CELIKOM_A1_OWNER_KEY_ALIAS",
    "CELIKOM_A1_OWNER_KEY_PASSWORD",
    "CELIKOM_A1_OWNER_CERT_SHA256",
)

def normalize_sha256(value) -> str:
    normalized = re.sub(r"[^0-9a-fA-F]", "", str(value or "")).lower()
    return normalized if re.fullmatch(r"[0-9a-f]{64}", normalized) else ""

def _keytool(args: list[str], failure_code: str, timeout: int = 90) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except Exception:
        raise ValueError(failure_code) from None
    if result.returncode != 0:
        raise ValueError(failure_code)
    return result.stdout or ""

def prepare_persistent_owner_keystore(work_directory, env=None) -> dict:
    """Import the owner PKCS#12 into a short-lived JKS with the legacy pipeline alias."""
    values = os.environ if env is None else env
    if any(not str(values.get(name, "")).strip() for name in SECRET_NAMES):
        raise ValueError("OWNER_SIGNER_SECRETS_INCOMPLETE")
    alias = str(values["CELIKOM_A1_OWNER_KEY_ALIAS"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", alias):
        raise ValueError("OWNER_SIGNER_ALIAS_INVALID")
    store_password = str(values["CELIKOM_A1_OWNER_KEYSTORE_PASSWORD"]).rstrip("\r\n")
    key_password = str(values["CELIKOM_A1_OWNER_KEY_PASSWORD"]).rstrip("\r\n")
    if len(store_password) < 6 or len(key_password) < 6:
        raise ValueError("OWNER_SIGNER_PASSWORD_INVALID")
    expected = normalize_sha256(values["CELIKOM_A1_OWNER_CERT_SHA256"])
    if not expected:
        raise ValueError("OWNER_SIGNER_EXPECTED_CERT_SHA256_INVALID")
    encoded = re.sub(r"\s+", "", str(values["CELIKOM_A1_OWNER_KEYSTORE_BASE64"]))
    try:
        source_bytes = base64.b64decode(encoded, validate=True)
    except Exception:
        raise ValueError("OWNER_SIGNER_KEYSTORE_BASE64_INVALID") from None
    if not 1024 <= len(source_bytes) <= 262144:
        raise ValueError("OWNER_SIGNER_KEYSTORE_SIZE_INVALID")
    work = Path(work_directory).resolve(strict=True)
    if not work.is_dir():
        raise ValueError("OWNER_SIGNER_TEMP_DIRECTORY_INVALID")
    source_path = work / "owner-signer-source.p12"
    destination_path = work / "unique-own-key.jks"
    if source_path.exists() or source_path.is_symlink() or destination_path.exists() or destination_path.is_symlink():
        raise ValueError("OWNER_SIGNER_TEMP_PATH_EXISTS")
    descriptor = os.open(source_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(source_bytes)
        del source_bytes
        _keytool([
            "keytool", "-importkeystore", "-noprompt",
            "-srckeystore", str(source_path), "-srcstoretype", "PKCS12",
            "-srcstorepass", store_password, "-srcalias", alias,
            "-srckeypass", key_password,
            "-destkeystore", str(destination_path), "-deststoretype", "JKS",
            "-deststorepass", DEST_STORE_PASSWORD,
            "-destkeypass", DEST_KEY_PASSWORD, "-destalias", DEST_ALIAS,
        ], "OWNER_SIGNER_KEYSTORE_IMPORT_FAILED")
        os.chmod(destination_path, 0o600)
        listing = _keytool([
            "keytool", "-list", "-v", "-keystore", str(destination_path),
            "-storetype", "JKS", "-storepass", DEST_STORE_PASSWORD,
            "-alias", DEST_ALIAS,
        ], "OWNER_SIGNER_KEYSTORE_VERIFY_FAILED")
        if not re.search(r"(?im)^\s*Entry type:\s*PrivateKeyEntry\s*$", listing):
            raise ValueError("OWNER_SIGNER_PRIVATE_KEY_ENTRY_REQUIRED")
        matches = re.findall(
            r"(?im)^\s*(?:SHA256|Certificate fingerprint \(SHA-256\)):\s*([0-9a-f:]{64,95})\s*$",
            listing,
        )
        fingerprints = {normalize_sha256(item) for item in matches}
        fingerprints.discard("")
        if len(fingerprints) != 1:
            raise ValueError("OWNER_SIGNER_CERTIFICATE_FINGERPRINT_UNAVAILABLE")
        actual = next(iter(fingerprints))
        if actual != expected:
            raise ValueError("OWNER_SIGNER_CERTIFICATE_FINGERPRINT_MISMATCH")
        return {"keystore_path": str(destination_path), "certificate_sha256": actual, "alias": DEST_ALIAS}
    except Exception:
        destination_path.unlink(missing_ok=True)
        raise
    finally:
        source_path.unlink(missing_ok=True)
