#!/usr/bin/env python3
"""Stage 10 fail-closed release/rollback state-machine rehearsal (NO DEPLOY).

Disposable on-disk CMS release trees + synthetic logical MySQL state/media.
The real encrypted MySQL restore is tested by the separate PHP CI tests.
This is intentionally NOT a Hostinger server deployer: no SSH, credentials,
SQL endpoint, release token, change to production workflow, or live domain.
"""
from __future__ import annotations

import http.client
import json
import os
from hashlib import sha256
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time

SITE = Path(__file__).resolve().parents[1]
SOURCES = {
    "public_html": SITE / "public",
    "app": SITE / "app",
    "database": SITE / "database",
}
STEPS = ("db", "media", "app", "database", "public_html", "health")


def demand(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError("Stage10 lifecycle: " + reason)


def digest(path: Path) -> dict[str, str]:
    """Recursive byte inventory, refusing symlinks in all managed trees."""
    demand(path.exists() and not path.is_symlink(), f"missing {path.name}")
    result = {}
    for item in ([path] if path.is_file() else path.rglob("*")):
        demand(not item.is_symlink(), "symlink inside managed release")
        if item.is_file():
            name = item.relative_to(path).as_posix() if path.is_dir() else "."
            result[name] = sha256(item.read_bytes()).hexdigest()
    return result


def clone(source: Path, target: Path) -> None:
    demand(not target.exists() and not target.is_symlink(), "overwrite forbidden")
    if source.is_dir():
        shutil.copytree(source, target, symlinks=True)
    else:
        shutil.copy2(source, target)


def remove(path: Path) -> None:
    if path.is_symlink():
        raise AssertionError("Refusing symlink during rollback")
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def write_json_atomic(target: Path, payload: dict) -> None:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    temp = target.with_name("." + target.name + ".tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fp:
            fp.write(raw)
            fp.flush()
            os.fsync(fp.fileno())
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


class DisposableRelease:
    def __init__(self, root: Path):
        demand(os.environ.get("CI") == "true" and
               os.environ.get("CELIKOM_SITE_SANDBOX_RELEASE") == "1",
               "an explicit isolated CI release sandbox is required")
        demand(str(root.resolve()).startswith(str(Path(tempfile.gettempdir()).resolve()) + os.sep)
               and root.name.startswith("celikom-release-life-"),
               "root must be a fresh, disposable test directory")
        self.domain = root / "domain"
        self.backup = self.domain / ".site-recovery-snapshot"
        self.stage = self.domain / ".site-candidate"
        self.journal = self.domain / ".site-recovery-journal.json"
        self.paths = {
            "public_html": self.domain / "public_html",
            "app": self.domain / "celikom-private" / "app",
            "database": self.domain / "celikom-private" / "database",
            "media": self.domain / "celikom-private" / "media",
            "db": self.domain / "celikom-private" / "cms-db-test.json",
        }

    def seed(self) -> None:
        self.domain.mkdir(mode=0o700)
        for part, filename, raw in [
            ("public_html", "index.php", b"<?php http_response_code(503); echo 'old site';"),
            ("app", "bootstrap.php", b"<?php // previous CMS"),
            ("database", "migrations/001.sql", b"-- previous CMS schema"),
            ("media", "keep-private.png", b"synthetic-private-previous-image"),
        ]:
            p = self.paths[part] / filename
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        self.paths["db"].write_text(json.dumps({
            "site_state": {"revision": 41}, "admin_users": ["owner"],
            "audit_log": ["before-release"]
        }), encoding="utf-8")
        self.owner_file = self.domain / "celikom-private" / "owner-credentials-do-not-touch.txt"
        self.owner_file.write_text("unmanaged owner file", encoding="utf-8")
        self.other_site = self.domain.parent / "independent-site" / "index.php"
        self.other_site.parent.mkdir()
        self.other_site.write_text("unrelated site", encoding="utf-8")
        self.previous = {kind: digest(path) for kind, path in self.paths.items()}

    def prepare(self) -> None:
        demand(not self.journal.exists() and not self.backup.exists() and
               not self.stage.exists(), "another release is in progress")
        demand(not (SITE / "RELEASE_READY").exists(),
               "no release authorization may be created by a rehearsal")
        demand(not any((SITE / "public" / name).exists()
                       for name in ("app", "database", ".env", "celikom-private")),
               "candidate puts private PHP under public web root")
        self.stage.mkdir(mode=0o700)
        for kind, source in SOURCES.items():
            expected = digest(source)
            clone(source, self.stage / kind)
            demand(digest(self.stage / kind) == expected, "staged code differs")
        self.desired = {kind: digest(self.stage / kind) for kind in SOURCES}
        self.backup.mkdir(mode=0o700)
        # In a real release these must be coordinated with a CMS write freeze.
        # Here the database is a synthetic logical snapshot, NOT a copied
        # production MySQL datadir (never safe to copy while mysqld runs).
        for kind, path in self.paths.items():
            clone(path, self.backup / kind)
            demand(digest(self.backup / kind) == self.previous[kind],
                   f"recovery copy corrupt: {kind}")
        write_json_atomic(self.journal, {
            "format": 1, "phase": "prepared", "steps": [],
            "backup_digests": self.previous,
            "candidate_digests": self.desired,
            "write_freeze": "simulated-only",
        })

    def _journal(self, step: str) -> None:
        state = json.loads(self.journal.read_text(encoding="utf-8"))
        state["steps"].append(step)
        state["phase"] = "applying"
        write_json_atomic(self.journal, state)

    def _health(self) -> bool:
        """Actual PHP HTTP smoke, still EXPECTS a blocked 503/noindex release."""
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CELIKOM_SITE_") and
               not k.startswith("CELIKOM_LOCAL_")}
        proc = subprocess.Popen(
            ["php", "-S", f"127.0.0.1:{port}", "-t", str(self.paths["public_html"])],
            cwd=self.domain, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            for route in ("/", "/admin/"):
                for attempt in range(45):
                    try:
                        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                        conn.request("GET", route)
                        reply = conn.getresponse()
                        status = reply.status
                        header = reply.getheader("X-Robots-Tag", "")
                        reply.read()
                        conn.close()
                        break
                    except OSError:
                        demand(attempt < 44, "PHP sandbox did not start")
                        time.sleep(0.1)
                if status != 503 or not header.lower().startswith("noindex"):
                    return False
            return True
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=4)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def activate(self, fail_at: int | None = None, unhealthy: bool = False) -> None:
        demand(self.journal.exists() and self.backup.is_dir(),
               "release must have a validated recovery checkpoint")
        state = json.loads(self.journal.read_text(encoding="utf-8"))
        demand(state["phase"] == "prepared" and
               state["write_freeze"] == "simulated-only",
               "refusing unprepared release")
        demand(all(digest(self.stage / kind) == state["candidate_digests"][kind]
                   for kind in SOURCES), "candidate changed after verification")
        demand(all(digest(self.backup / kind) == state["backup_digests"][kind]
                   for kind in self.paths), "restore snapshot changed after verification")

        for index, step in enumerate(STEPS, start=1):
            if step == "db":
                # Model a schema/data migration while writes are frozen.
                data = json.loads(self.paths["db"].read_text(encoding="utf-8"))
                data["site_state"]["revision"] = 42
                data["audit_log"].append("simulated-migration")
                self.paths["db"].write_text(json.dumps(data), encoding="utf-8")
            elif step == "media":
                (self.paths["media"] / "candidate-preview.png").write_bytes(
                    b"synthetic-test-only-binary")
            elif step in SOURCES:
                remove(self.paths[step])
                clone(self.stage / step, self.paths[step])
            elif step == "health":
                demand(not unhealthy and self._health(), "release HTTP healthcheck failed")
            # For odd steps emulate crash AFTER writing but BEFORE updating the journal.
            if index % 2 == 0:
                self._journal(step)
            if fail_at == index:
                raise RuntimeError(f"simulated abrupt process termination: {step}")
            if index % 2 != 0:
                self._journal(step)
        demand(all(digest(self.paths[kind]) == self.desired[kind]
                   for kind in SOURCES), "installed candidate is not byte-identical")
        write_json_atomic(self.journal, {
            **json.loads(self.journal.read_text(encoding="utf-8")),
            "phase": "completed-in-test-only"
        })

    def recover_after_crash(self) -> None:
        """New process may invoke this using only the persisted journal."""
        demand(self.journal.is_file(), "missing recovery journal")
        state = json.loads(self.journal.read_text(encoding="utf-8"))
        demand(state["format"] == 1 and state["phase"] in
               ("prepared", "applying", "completed-in-test-only"),
               "unrecognized rollback state")
        for kind, path in self.paths.items():
            demand(digest(self.backup / kind) == state["backup_digests"][kind],
                   "backup damaged; stop instead of risking destructive restore")
            remove(path)
            clone(self.backup / kind, path)
            demand(digest(path) == state["backup_digests"][kind],
                   "rollback did not reproduce the original bytes")
        self.journal.unlink()
        demand(self.owner_file.read_text(encoding="utf-8") ==
               "unmanaged owner file", "unmanaged owner credentials changed")
        demand(self.other_site.read_text(encoding="utf-8") ==
               "unrelated site", "unrelated website changed")
        demand(not (self.paths["app"] / "release-approved.php").exists(),
               "release approval was fabricated")


def case(fail_at: int | None, unhealthy: bool = False,
         corrupt_candidate: bool = False, corrupt_backup: bool = False) -> None:
    with tempfile.TemporaryDirectory(prefix="celikom-release-life-") as location:
        root = Path(location)
        model = DisposableRelease(root)
        model.seed()
        model.prepare()
        if corrupt_candidate:
            (model.stage / "public_html" / "index.php").write_text(
                "<?php echo 'tampered';", encoding="utf-8")
        if corrupt_backup:
            (model.backup / "db").write_text("tampered", encoding="utf-8")
        raised = False
        try:
            model.activate(fail_at, unhealthy)
        except (RuntimeError, AssertionError):
            raised = True
        demand(raised == (fail_at is not None or unhealthy or
                           corrupt_candidate or corrupt_backup),
               "expected failure was not detected")
        # A corrupted recovery source must not be trusted or applied.
        if corrupt_backup:
            demand(all(digest(path) == model.previous[k]
                       for k, path in model.paths.items()),
                   "corrupted backup changed live state")
            try:
                model.recover_after_crash()
            except AssertionError:
                pass
            else:
                raise AssertionError("corrupted rollback backup was trusted")
            return
        # Reopen after a simulated interruption: no in-memory swap list used.
        resumed = DisposableRelease(root)
        resumed.owner_file = model.owner_file
        resumed.other_site = model.other_site
        resumed.recover_after_crash()
        demand(all(digest(path) == model.previous[k]
                   for k, path in resumed.paths.items()),
               "journal-based rollback lost database, media or code")
        demand(not resumed.journal.exists(), "rollback journal not cleared")


if __name__ == "__main__":
    for failure in range(1, len(STEPS) + 1):
        case(failure)
    case(None, unhealthy=True)
    case(None, corrupt_candidate=True)
    case(None, corrupt_backup=True)
    case(None)
    print("Stage10: 6 crashes + failed healthcheck + tamper cases + successful staged activation; persisted-journal DB/media/code rollback, real PHP 503/noindex — PASS")
