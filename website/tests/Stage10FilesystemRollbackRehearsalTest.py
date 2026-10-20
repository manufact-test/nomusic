#!/usr/bin/env python3
"""Stage 10 preparation: real filesystem rollout + rollback on a disposable domain.

No SSH, production credentials, release marker, database connection or network.
Only the repository's existing public/app/database trees and tmpdir are used.
This is NOT the production deployment workflow or a disaster-recovery test.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import shutil
import subprocess
import socket
import time
import http.client

SITE = Path(__file__).resolve().parents[1]
REPO = SITE.parent
SOURCES = {
    "public_html": SITE / "public",
    "app": SITE / "app",
    "database": SITE / "database",
}
PREVIOUS = {
    "public_html": ("index.php", b"<?php echo 'Previous site';\n"),
    "app": ("bootstrap.php", b"<?php // previous CMS app\n"),
    "database": ("migrations/001_prev.sql", b"-- previous schema\n"),
}

def verify(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError("Offline rollback: " + reason)

def inventory(folder: Path) -> dict[str, str]:
    files = {}
    verify(folder.is_dir() and not folder.is_symlink(), f"invalid tree {folder.name}")
    for path in folder.rglob("*"):
        verify(not path.is_symlink(), "symlinks are forbidden, including private trees")
        if path.is_file():
            files[path.relative_to(folder).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return files

def paths_for(domain: Path) -> dict[str, Path]:
    return {
        "public_html": domain / "public_html",
        "app": domain / "celikom-private/app",
        "database": domain / "celikom-private/database",
    }

def seed_previous(paths: dict[str, Path]) -> None:
    for name, (filename, content) in PREVIOUS.items():
        p = paths[name] / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

def stage_candidate(staging: Path) -> dict[str, dict[str, str]]:
    verify(not (SITE / "RELEASE_READY").exists(), "release marker unexpectedly exists")
    ensure_public_private_boundary()
    manifests = {}
    for name, source in SOURCES.items():
        verify(source.is_dir(), "missing verified website source")
        manifests[name] = inventory(source)
        target = staging / name
        shutil.copytree(source, target, symlinks=False)
        verify(inventory(target) == manifests[name], f"staging altered {name}")
    return manifests

def ensure_public_private_boundary() -> None:
    public = SOURCES["public_html"]
    verify(not any((public / x).exists() for x in ("app", "database", "celikom-private")),
           "private CMS source under public web root")
    banned = {".env", ".key", ".pem", ".sql", ".sqlite", ".bak", ".zip"}
    for item in public.rglob("*"):
        verify(not item.is_symlink(), "public symlinks forbidden")
        if item.is_file():
            verify(item.name not in {".env", "id_rsa"} and
                   item.suffix.lower() not in banned,
                   "private-looking file under public_html")
    verify((SOURCES["app"] / "Templates/site-v10.html").is_file(),
           "approved private v10 template missing")
    verify((SOURCES["database"] / "seeds/faq-v10.json").is_file(),
           "original v10 FAQ seed missing")

def failure_rehearsal(fail_after: int | None) -> dict:
    """One isolated deployment. Failure is injected after N completed tree swaps."""
    with TemporaryDirectory(prefix="celikom-site-rehearsal-") as root:
        domain = Path(root) / "domain"
        domain.mkdir(mode=0o700)
        live = paths_for(domain)
        seed_previous(live)
        old_hash = {name: inventory(path) for name, path in live.items()}
        # Unmanaged content must survive BOTH update and rollback.
        sidecar = domain / "celikom-private/media/owner-stays-private.txt"
        sidecar.parent.mkdir(mode=0o700)
        sidecar.write_bytes(b"owner private media is not in app/database\n")
        other_site = Path(root) / "another-site/public_html/index.php"
        other_site.parent.mkdir(parents=True)
        other_site.write_bytes(b"other site must never be changed\n")

        staging = domain / ".site-staging"
        staging.mkdir(mode=0o700)
        desired = stage_candidate(staging)
        backup = domain / ".site-rollback"
        backup.mkdir(mode=0o700)
        quarantined = domain / ".site-failed"
        quarantined.mkdir(mode=0o700)
        swapped = []
        did_fail = False
        try:
            for name in SOURCES:
                # Renames occur inside the *same* sandbox filesystem, unlike
                # dangerous in-place scp over a live web root.
                os.replace(live[name], backup / name)
                try:
                    os.replace(staging / name, live[name])
                except BaseException:
                    os.replace(backup / name, live[name])
                    raise
                swapped.append(name)
                if fail_after == len(swapped):
                    raise RuntimeError("injected deployment interruption")
            for name, path in live.items():
                verify(inventory(path) == desired[name], f"new {name} differs from source")
            verify(not (live["app"] / "release-approved.php").exists(),
                   "sandbox changed the owner-controlled release authorization")
            verify((live["public_html"] / "index.php").is_file(),
                   "missing public PHP entry after activation")
            # Despite staged trees, the public page must stay closed.
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("CELIKOM_SITE_") and
                   not key.startswith("CELIKOM_LOCAL_")}
            server = subprocess.Popen(
                ["php", "-S", f"127.0.0.1:{port}", "-t", str(live["public_html"])],
                cwd=domain, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                response = None
                for trial in range(50):
                    try:
                        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                        conn.request("GET", "/")
                        response = conn.getresponse()
                        code, headers, body = response.status, dict(response.getheaders()), response.read()
                        conn.close()
                        break
                    except OSError:
                        if trial == 49:
                            raise
                        time.sleep(0.1)
                verify(code == 503 and headers.get("X-Robots-Tag", "").startswith("noindex") and
                       b"CELIKOM" in body, "unapproved website became publicly available")
            finally:
                server.terminate()
                try:
                    server.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
        except RuntimeError as exc:
            verify(fail_after is not None and
                   str(exc) == "injected deployment interruption",
                   f"unexpected real deployment error: {exc}")
            did_fail = True
        finally:
            # Restore prior public + CMS + schema trees in reverse order.
            # Never touch unmanaged owner media or unrelated sites.
            for name in reversed(swapped):
                os.replace(live[name], quarantined / name)
                os.replace(backup / name, live[name])
            for name in SOURCES:
                verify(inventory(live[name]) == old_hash[name],
                       f"rollback failed to restore old {name}")
            verify(sidecar.read_bytes() == b"owner private media is not in app/database\n",
                   "owner's private media changed")
            verify(other_site.read_bytes() == b"other site must never be changed\n",
                   "an unrelated website changed")
            verify(not (live["app"] / "release-approved.php").exists(),
                   "rehearsal created a release approval")
        verify(did_fail == (fail_after is not None), "injected failure not reached")
        return {"interrupted_after": fail_after, "rollback_exact": True}

for point in (1, 2, 3, None):
    failure_rehearsal(point)
print("Stage10 rehearsal: 3 forced failures + success, exact rollback, owner media and other sites safe, public 503 — PASS")
