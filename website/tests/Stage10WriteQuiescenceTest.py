#!/usr/bin/env python3
"""Stage 10 cross-process flock freeze contract; filesystem-only disposable test.

Runs PHP leases in separate processes; no database, Hostinger, SSH, secrets or
production release approval. Raises if writer slips through exclusive snapshot.
"""
import os
import select
import subprocess
import tempfile
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
BOOT = SITE / "app/bootstrap.php"
PUBLIC = SITE / "public"
PHP = r"""
require $argv[1];
try {
    $lease = $argv[3] === 'exclusive'
        ? \Celikom\Website\CmsWriteQuiescence::snapshot($argv[2], 150)
        : \Celikom\Website\CmsWriteQuiescence::writer($argv[2], 150);
    echo "ACQUIRED\n";
    fflush(STDOUT);
    if (($argv[4] ?? '') === 'hold') sleep(20);
    $lease->release();
} catch (\RuntimeException $e) {
    fwrite(STDERR, "REJECTED\n");
    exit(23);
}
"""


def env_with(path=None):
    env = os.environ.copy()
    env.pop("CELIKOM_SITE_WRITE_GATE_FILE", None)
    if path is not None:
        env["CELIKOM_SITE_WRITE_GATE_FILE"] = str(path)
    return env


def args(mode, hold=False):
    return ["php", "-r", PHP, str(BOOT), str(PUBLIC), mode] + (["hold"] if hold else [])


def probe(mode, env, accepted=True):
    p = subprocess.run(args(mode), env=env, capture_output=True, timeout=6)
    assert p.returncode == (0 if accepted else 23), (
        "lease", mode, "accepted" if accepted else "rejected",
        p.returncode, p.stdout.decode()[:100], p.stderr.decode()[:100]
    )


def holder(mode, env):
    process = subprocess.Popen(args(mode, True), env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ready, _, _ = select.select([process.stdout], [], [], 4)
    assert ready, "lease acquisition timed out"
    assert process.stdout.readline() == b"ACQUIRED\n", "lease holder did not start"
    return process


def stop(process):
    process.kill()  # abrupt worker crash: kernel must release flock
    process.communicate(timeout=4)


with tempfile.TemporaryDirectory(prefix="celikom-lock-ci-") as tmp:
    private = Path(tmp) / "owner-private"
    private.mkdir(mode=0o700)
    gate = private / ".celikom-cms-writes.lock"
    env = env_with(gate)

    probe("writer", env)
    probe("exclusive", env)
    shared = holder("writer", env)
    try:
        probe("writer", env)  # multiple concurrent writers may finish
        probe("exclusive", env, accepted=False)
    finally:
        stop(shared)
    probe("exclusive", env)  # recovered from crashed writer

    exclusive = holder("exclusive", env)
    try:
        probe("writer", env, accepted=False)
        probe("exclusive", env, accepted=False)
    finally:
        stop(exclusive)
    probe("writer", env)  # automatically unfreezes after crash

    gate.chmod(0o644)
    probe("writer", env, accepted=False)  # never silently repair exposure
    gate.chmod(0o600)
    gate.unlink()

    target = private / "innocent.txt"
    target.write_text("unmanaged", encoding="utf-8")
    gate.symlink_to(target)
    probe("exclusive", env, accepted=False)
    assert target.read_text(encoding="utf-8") == "unmanaged"
    gate.unlink()
    probe("writer", env_with(), accepted=False)
    probe("writer", env_with(PUBLIC / ".celikom-cms-writes.lock"), accepted=False)
    assert not (PUBLIC / ".celikom-cms-writes.lock").exists()

print("Stage10: cross-process writer/snapshot exclusion, concurrent writers, crash release, unsafe paths/modes rejected — PASS")
