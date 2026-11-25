#!/usr/bin/env python3
"""Obtain only the exact two private signed Windows release drafts.

This script runs on a GitHub-hosted protected job with draft-read access.
It does not sign, edit releases, use server credentials or publish a feed.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

REPO = "manufact-test/nomusic"
PIN_SHA256 = "46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95"
VERSION = re.compile(r"(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,4})")
SHA = re.compile(r"[a-f0-9]{40}")
DIGEST = re.compile(r"sha256:[a-f0-9]{64}")
HERE = pathlib.Path(__file__).resolve().parent


def need(ok, why):
    if not ok:
        raise ValueError(why)


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=180).stdout


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def identity(version, sequence, commit):
    need(VERSION.fullmatch(version) and type(sequence) is int and 0 < sequence <= 2**53-1
         and SHA.fullmatch(commit), "BAD_RELEASE_IDENTITY")


def asset_plan(records, version, sequence, commit):
    identity(version, sequence, commit)
    owner = "celikom-windows-v" + version + "-owner-bootstrap"
    feed = "celikom-windows-v" + version + "-floki-feed-candidate"
    expected = {
        owner: {
            "CELIKOM-Windows-" + version + ".exe": (10000, 125000000),
            "CELIKOM-Windows-" + version + ".zip": (1, 125000000),
            "SHA256SUMS.txt": (1, 4096),
        },
        feed: {"latest.json": (100, 16384), "latest.json.sig": (64, 80),
               "manifest-public-key.der": (64, 256), "manifest.json": (100, 16384),
               "manifest.json.sig": (64, 80)},
    }
    result = {}
    for tag in (owner, feed):
        matches = [x for x in records if x.get("tag_name") == tag]
        need(len(matches) == 1, "MISSING_OR_AMBIGUOUS_DRAFT")
        rec = matches[0]
        need(rec.get("draft") is True and rec.get("target_commitish") == commit,
             "DRAFT_STATE_OR_SOURCE_MISMATCH")
        assets = rec.get("assets")
        need(isinstance(assets, list) and len(assets) == len(expected[tag])
             and {a.get("name") for a in assets} == set(expected[tag]), "DRAFT_ASSET_SET_MISMATCH")
        for a in assets:
            lo, hi = expected[tag][a["name"]]
            need(type(a.get("size")) is int and lo <= a["size"] <= hi
                 and type(a.get("id")) is int and a["id"] > 0
                 and isinstance(a.get("digest"), str) and DIGEST.fullmatch(a["digest"]),
                 "DRAFT_ASSET_METADATA_INVALID")
            name = a["name"]
            if tag == owner and not name.endswith(".exe"):
                continue  # no ZIP/checksums duplication in the signed feed transfer
            dest = version + "/" + name if name.endswith(".exe") or name.startswith("manifest.json") else name
            need(dest not in result, "DUPLICATE_TRANSFER_ASSET")
            result[dest] = (tag, a)
    need(len(result) == 6 and result["manifest-public-key.der"][1]["digest"] == "sha256:" + PIN_SHA256,
         "PIN_OR_TRANSFER_SET_MISMATCH")
    return result


def prepare(version, sequence, commit, output):
    identity(version, sequence, commit)
    need(run(["gh", "repo", "view", REPO, "--json", "visibility", "--jq", ".visibility"]).strip()
         == "PRIVATE", "PRIVATE_REPO_REQUIRED")
    records = json.loads(run(["gh", "api", "--paginate", "--slurp", "repos/" + REPO + "/releases?per_page=100"]))
    need(isinstance(records, list) and all(isinstance(page, list) for page in records), "INVALID_RELEASE_LIST")
    plan = asset_plan([item for page in records for item in page], version, sequence, commit)
    with tempfile.TemporaryDirectory(prefix="celikom-draft-source-") as tmp:
        root = pathlib.Path(tmp)
        (root / version).mkdir(mode=0o700)
        for dest, (tag, a) in plan.items():
            target = root / dest
            # gh release download enforces the authenticated private draft.
            # The exact REST SHA and signed bytes are verified independently.
            subprocess.run(["gh", "release", "download", tag, "--repo", REPO,
                            "--pattern", a["name"], "--output", str(target)],
                           check=True, timeout=180)
            need(target.is_file() and not target.is_symlink() and target.stat().st_size == a["size"]
                 and "sha256:" + sha(target) == a["digest"], "DRAFT_ASSET_BYTES_MISMATCH")
        pin = root / "manifest-public-key.der"
        need(sha(pin) == PIN_SHA256, "PIN_BYTES_MISMATCH")
        subprocess.run([sys.executable, str(HERE / "windows-stable-private-import.py"), "pack",
                        "--source", str(root), "--output", str(output), "--pin", str(pin),
                        "--version", version, "--sequence", str(sequence)], check=True, timeout=120)
    print("CELIKOM_WINDOWS_PRIVATE_DRAFT_SOURCE_OK", version, sequence, sha(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    prepare(args.version, args.sequence, args.commit, args.output)
