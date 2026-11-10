#!/usr/bin/env python3
"""Private, local-only research output for the already verified LSPatch split bundle.

Never runs on GitHub Actions, never installs or distributes an APK. Caller MUST
verify exact original publisher signed input, output package/version, all split
signatures, embedded module SHA256 and sigbypass=0 BEFORE calling export.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

ACK = "I_CONFIRM_PRIVATE_ARM_SPARE_RESEARCH_ONLY"
EXPECTED_COUNT = 5
PACKAGE = "ru.yandex.music"
VERSION_CODE = 24026531


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def export_private_lab_parts(
    parts: list[tuple[str, Path]], destination: str | None,
    confirmation: str | None, *, repo_root: Path, lab_signer: str
) -> dict:
    """Called AFTER full existing ephemeral_patch_lab.py verification, never before."""
    if not destination:
        return {"exported": False}
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise ValueError("NEVER_EXPORT_VENDOR_PATCHED_APKS_ON_GITHUB_ACTIONS")
    if confirmation != ACK:
        raise ValueError("PRIVATE_ARM_SPARE_RESEARCH_CONFIRMATION_REQUIRED")
    if len(parts) != EXPECTED_COUNT:
        raise ValueError("EXACT_FIVE_NATIVE_SPLITS_REQUIRED")
    ids = [part_id or "base" for part_id, _ in parts]
    if ids.count("base") != 1 or len(set(ids)) != EXPECTED_COUNT:
        raise ValueError("DUPLICATE_OR_MISSING_NATIVE_SPLIT_IDS")
    if any(not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", x) for x in ids):
        raise ValueError("UNSAFE_SPLIT_ID")
    if not re.fullmatch(r"[a-f0-9]{64}", lab_signer):
        raise ValueError("INVALID_LAB_CERTIFICATE_DIGEST")
    raw_target = Path(destination).expanduser()
    if not raw_target.is_absolute():
        raise ValueError("PRIVATE_LAB_EXPORT_PATH_MUST_BE_ABSOLUTE")
    target = raw_target.resolve()
    root = repo_root.resolve()
    if target == root or root in target.parents:
        raise ValueError("NO_RESEARCH_APKS_INSIDE_GIT_REPOSITORY")
    if target.exists() or not target.parent.is_dir():
        raise ValueError("EXPORT_TARGET_MUST_BE_NEW_WITH_EXISTING_PARENT")
    for _, file in parts:
        if not file.is_file():
            raise ValueError("VERIFIED_PATCHED_SPLIT_MISSING")
    staging = Path(tempfile.mkdtemp(prefix=".celikom-arm-research-", dir=target.parent))
    try:
        details = []
        for split, original in sorted(parts, key=lambda item: (bool(item[0]), item[0])):
            out_name = "base.apk" if not split else "split_" + split + ".apk"
            out = staging / out_name
            shutil.copyfile(original, out)
            os.chmod(out, 0o600)
            details.append({
                "split": split or "base",
                "name": out_name,
                "sha256": digest(out),
                "bytes": out.stat().st_size,
            })
        receipt = {
            "status": "RESEARCH_PATCHED_HOST_SPLITS_NOT_DEVICE_TESTED",
            "purpose": "PRIVATE_DISPOSABLE_ARM_LSPATCH_A1",
            "host_package": PACKAGE,
            "host_version_code": VERSION_CODE,
            "sigbypass": 0,
            "lab_signer_sha256": lab_signer,
            "part_count": len(details),
            "parts": details,
            "owner_main_phone_allowed": False,
            "consumer_single_apk": False,
            "play_protect_tested": False,
            "native_music_swap_tested": False,
            "can_install_over_publisher_signed_yandex": False,
        }
        receipt_path = staging / "research-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        os.chmod(receipt_path, 0o600)
        # Atomic transfer on same volume; a failed export leaves no partial
        # finished output directory. Installer is NEVER executed here.
        os.replace(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"exported": True, "split_count": EXPECTED_COUNT,
            "receipt_sha256": digest(target / "research-receipt.json"),
            "device_installation_performed": False}
