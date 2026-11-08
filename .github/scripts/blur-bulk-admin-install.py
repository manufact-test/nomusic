#!/usr/bin/env python3
"""One-shot, SHA-guarded CELIKOM admin-only release patch.

The owner explicitly requested an admin-only update. This installer has no
music importer, song uploader, or moderation execution path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


TARGETS = {
    "AdminPanel.php": "src/Admin/AdminPanel.php",
    "ModerationService.php": "src/Admin/ModerationService.php",
    "BulkModerationService.php": "src/Admin/BulkModerationService.php",
    "BulkModerationView.php": "src/Admin/BulkModerationView.php",
    "admin-style.css": "src/Admin/admin-style.css",
    "bulk-moderation.js": "src/Admin/bulk-moderation.js",
    "019_bulk_moderation_tombstones.sql": "migrations/019_bulk_moderation_tombstones.sql",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_atomically(source: Path, target: Path) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=".bulk-install-", dir=target.parent)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        shutil.copyfile(source, tmp)
        os.chmod(tmp, 0o644)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: admin-install.py RELEASE_DIR STAGING_DIR")
    root = Path(sys.argv[1]).resolve(strict=True)
    staging = Path(sys.argv[2]).resolve(strict=True)
    domain = Path("/home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom")
    release_root = (domain / "releases").resolve(strict=True)
    current = domain / "current"
    if not current.is_symlink() or current.resolve() != root or not root.is_relative_to(release_root):
        raise SystemExit("BLOCK: unexpected active release")
    if not staging.is_relative_to((domain / "incoming").resolve(strict=True)):
        raise SystemExit("BLOCK: staging is outside private incoming")
    manifest = json.loads((staging / "expected.json").read_text(encoding="utf-8"))
    if set(manifest) != set(TARGETS):
        raise SystemExit("BLOCK: manifest file set mismatch")

    # ALL preconditions must pass BEFORE writing anything.
    for name, rel in TARGETS.items():
        expected = manifest[name]
        source = staging / name
        target = root / rel
        if not source.is_file() or source.is_symlink() or target.is_symlink():
            raise SystemExit("BLOCK: unsafe source/target " + name)
        if source.stat().st_size < 1 or source.stat().st_size > 900_000:
            raise SystemExit("BLOCK: invalid staged file size " + name)
        if not target.parent.is_dir():
            raise SystemExit("BLOCK: missing target directory " + name)
        if expected is None:
            if target.exists():
                raise SystemExit("BLOCK: newly added module already exists " + name)
        elif not target.is_file() or sha(target) != expected:
            raise SystemExit("BLOCK: live changed during preparation " + name)

    php = "/opt/alt/php83/usr/bin/php"
    if not Path(php).is_file():
        raise SystemExit("BLOCK: trusted PHP runtime not found")
    for name in [n for n in TARGETS if n.endswith(".php")]:
        subprocess.run([php, "-l", str(staging / name)], check=True, timeout=20,
                       stdout=subprocess.DEVNULL)

    backup = staging / "backup"
    backup.mkdir(mode=0o700, exist_ok=False)
    for name, rel in TARGETS.items():
        if manifest[name] is not None:
            shutil.copy2(root / rel, backup / name)
    replaced: list[str] = []
    try:
        if current.resolve() != root:
            raise RuntimeError("active release changed")
        for name, rel in TARGETS.items():
            replace_atomically(staging / name, root / rel)
            replaced.append(name)
        if current.resolve() != root:
            raise RuntimeError("active release changed during patch")
        for name, rel in TARGETS.items():
            if sha(root / rel) != sha(staging / name):
                raise RuntimeError("installed hash mismatch " + name)
        for name in [n for n in TARGETS if n.endswith(".php")]:
            subprocess.run([php, "-l", str(root / TARGETS[name])], check=True,
                           timeout=20, stdout=subprocess.DEVNULL)
        # The release's OWN migrations are used; do not copy old migrations.
        # This adds only the new tombstone table to its already applied schema.
        migration = subprocess.run([php, str(root / "bin/migrate.php")], cwd=root,
                                   capture_output=True, text=True, timeout=75)
        if migration.returncode:
            raise RuntimeError("migration gate failed: " + migration.stderr[:300])
        if "Schema ready." not in migration.stdout:
            raise RuntimeError("migration gate returned no ready marker")
        if current.resolve() != root:
            raise RuntimeError("active release changed after migration")
        print("PASS guarded seven-file admin-only patch")
        print("PASS active release lease and PHP syntax")
        print("PASS additive tombstone migration")
        print("No songs imported, approved, rejected or deleted")
        return 0
    except Exception as exc:
        # Revert PHP/CSS/JS and new migration FILE on any failure.
        # Additive DB table may remain; it is inert without admin routes.
        for name in reversed(replaced):
            target = root / TARGETS[name]
            if manifest[name] is None:
                if target.is_file():
                    target.unlink()
            else:
                replace_atomically(backup / name, target)
        print("ROLLBACK completed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
