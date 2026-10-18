#!/usr/bin/env python3
"""Stage 9/10 rehearsal of Hostinger web-root separation; NEVER deploys.

Create a disposable domain structure using exactly the trees copied by the
manual deploy workflow, then exercise the real PHP production gates on localhost.
The owner-approved v10 assets must remain byte-identical.
"""
from pathlib import Path
from contextlib import contextmanager
import hashlib
import http.client
import os
import shutil
import socket
import subprocess
import tempfile
import time

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parent
DEPLOY = REPO / ".github/workflows/deploy-celikom-website.yml"
SITE = BASE / "public"
PRIVATE = BASE / "app"
DB = BASE / "database"

def ensure(condition, reason):
    if not condition:
        raise AssertionError(reason)

def get(port, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=4)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        conn.close()

def wait_for(port):
    for _ in range(50):
        try:
            return get(port, "/")
        except OSError:
            time.sleep(0.1)
    raise AssertionError("local PHP server never started")

def check_tree():
    workflow = DEPLOY.read_text(encoding="utf-8")
    ensure("workflow_dispatch:" in workflow and
           "test -f website/RELEASE_READY" in workflow and
           "SITE_AND_CMS_ACCEPTED" in workflow,
           "manual joint release gate is missing")
    ensure("&& false" in workflow and
           "Remove ONLY when Stage 10" in workflow,
           "unsafe Hostinger in-place deployment was accidentally enabled")
    ensure("scp -r" in workflow and "website/public/." in workflow and
           "website/app/." in workflow and
           "website/database/." in workflow,
           "the offline layout no longer matches the manual deploy plan")
    ensure(not (BASE / "RELEASE_READY").exists(), "site release marker unexpectedly exists")
    for folder in (SITE, PRIVATE, DB):
        ensure(folder.is_dir() and not folder.is_symlink(), "approved tree unavailable")
    for item in SITE.rglob("*"):
        ensure(not item.is_symlink(), "public symlink could escape web root")
        if item.is_file():
            ensure(item.suffix.lower() not in {
                ".sql", ".sqlite", ".key", ".pem", ".log", ".bak", ".zip", ".env"
            }, "private-looking public artifact present")

with tempfile.TemporaryDirectory(prefix="celikom-dry-domain-") as directory:
    check_tree()
    domain = Path(directory) / "example.invalid"
    public = domain / "public_html"
    app = domain / "celikom-private/app"
    database = domain / "celikom-private/database"
    domain.mkdir(mode=0o700)
    shutil.copytree(SITE, public)
    shutil.copytree(PRIVATE, app)
    shutil.copytree(DB, database)

    ensure((public / "index.php").is_file() and
           (public / "admin/index.php").is_file() and
           (app / "bootstrap.php").is_file() and
           (app / "Templates/site-v10.html").is_file() and
           (database / "migrations/001_website_cms.sql").is_file(),
           "real deploy copy contract incomplete")
    ensure(not (public / "app").exists() and
           not (public / "database").exists() and
           not (public / "celikom-private").exists(),
           "private PHP or database copied into web root")
    for rel in (
        "index.php", "admin/index.php", "assets/css/v10/00-base.css",
        "assets/css/v10/01-v6.css", "assets/css/v10/02-v7.css",
        "assets/css/v10/03-v8.css", "assets/css/v10/04-v10.css",
        "assets/js/v10/faq.js", "assets/js/v10/sound-demo.js",
    ):
        original = SITE / rel
        ensure(original.is_file() and (public / rel).is_file(),
               f"approved source asset missing: {rel}")
        ensure(hashlib.sha256(original.read_bytes()).digest() ==
               hashlib.sha256((public / rel).read_bytes()).digest(),
               f"public code or v10 asset modified in copy: {rel}")
    ensure((app / "Templates/site-v10.html").read_bytes() ==
           (PRIVATE / "Templates/site-v10.html").read_bytes(),
           "approved template changed by staging copy")
    ensure((database / "seeds/faq-v10.json").read_bytes() ==
           (DB / "seeds/faq-v10.json").read_bytes(),
           "v10 FAQ changed by staging copy")

    # Deliberately drop all website DB keys, dev preview switches and markers.
    env = {
        k: v for k, v in os.environ.items()
        if not k.startswith("CELIKOM_SITE_")
        and not k.startswith("CELIKOM_LOCAL_")
    }
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = subprocess.Popen(
        ["php", "-S", f"127.0.0.1:{port}", "-t", str(public)],
        cwd=domain, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        landing = wait_for(port)
        ensure(landing[0] == 503 and
               landing[1].get("X-Robots-Tag", "").startswith("noindex") and
               b"CELIKOM" in landing[2],
               "production site opened without joint release")
        admin = get(port, "/admin/")
        ensure(admin[0] == 503 and
               admin[1].get("X-Robots-Tag", "").startswith("noindex"),
               "production CMS opened without joint release")
        for target in (
            "/app/bootstrap.php",
            "/app/Templates/site-v10.html",
            "/database/migrations/001_website_cms.sql",
            "/celikom-private/app/bootstrap.php",
            "/celikom-private/database/seeds/faq-v10.json",
        ):
            response = get(port, target)
            ensure(response[0] == 404, f"private file leaked via {target}")
        asset = get(port, "/assets/css/v10/00-base.css")
        ensure(asset[0] == 200 and len(asset[2]) > 100,
               "approved v10 CSS missing after deploy-style staging")
        ensure(not (domain / "celikom-private/app/release-approved.php").exists(),
               "rehearsal created a production authorization marker")
    finally:
        server.terminate()
        try:
            server.wait(timeout=4)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
print("Stage9: disposable Hostinger layout, byte parity, public 503, private 404, admin closed — PASS")
