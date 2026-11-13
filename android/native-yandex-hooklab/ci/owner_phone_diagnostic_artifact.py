"""Export exactly one private owner-phone diagnostic APK after native acceptance."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

EXPECTED_VERDICT = "METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO"
OUTPUT_DIRECTORY = "celikom-a1-owner-phone-test"
OUTPUT_NAME = "CELIKOM-A1-Native-ReadOnly-Diagnostic.apk"
MAX_APK_BYTES = 150_000_000
MIN_APK_BYTES = 1_000_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_after_native_acceptance(source_apk, report: dict, runner_temp) -> dict:
    """Copy only the tested clone APK; never export on a partial/failed run."""
    accepted = (
        isinstance(report, dict)
        and report.get("verdict") == EXPECTED_VERDICT
        and report.get("native_clone_main_75s") is True
        and report.get("publisher_stable_75s_before_clone") is True
        and report.get("publisher_still_installed_after_clone_start") is True
        and report.get("publisher_app_and_clone_can_be_concurrently_installed") is True
        and report.get("single_clone_installed_after_original") is True
        and report.get("original_splits_installed_before_clone") == 16
    )
    if not accepted:
        raise ValueError("DIAGNOSTIC_EXPORT_NATIVE_ACCEPTANCE_REQUIRED")

    source = Path(source_apk)
    if source.is_symlink() or not source.is_file():
        raise ValueError("DIAGNOSTIC_EXPORT_SOURCE_INVALID")
    root = Path(runner_temp).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("DIAGNOSTIC_EXPORT_RUNNER_TEMP_INVALID")
    target_dir = root / OUTPUT_DIRECTORY
    if target_dir.exists() or target_dir.is_symlink():
        raise ValueError("DIAGNOSTIC_EXPORT_DESTINATION_EXISTS")

    target_dir.mkdir(mode=0o700)
    target = target_dir / OUTPUT_NAME
    shutil.copyfile(source, target)
    size = target.stat().st_size
    if size < MIN_APK_BYTES or size > MAX_APK_BYTES:
        target.unlink(missing_ok=True)
        target_dir.rmdir()
        raise ValueError("DIAGNOSTIC_EXPORT_SIZE_OUT_OF_RANGE")
    source_hash = _sha256(source)
    target_hash = _sha256(target)
    if source_hash != target_hash:
        target.unlink(missing_ok=True)
        target_dir.rmdir()
        raise ValueError("DIAGNOSTIC_EXPORT_HASH_MISMATCH")
    return {"exported": True, "size_bytes": size, "sha256": target_hash}
