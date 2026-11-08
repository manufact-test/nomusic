#!/usr/bin/env python3
"""CELIKOM five-song validation only. No production writes or media redistribution.

Requires only Python stdlib for metadata checks. Optional --audio-check uses ffprobe,
fetches 5 pinned remote files into a temporary directory, verifies Git blob hashes,
then deletes them; never uploads or retains audio files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

MANIFEST = Path(__file__).with_name("pilot.json")
MAX_AUDIO_BYTES = 25_000_000
SOURCE_REPO = "Hazzz895/FckCensorData"


def validate_manifest(manifest):
    if manifest.get("schema") != 1 or manifest.get("source_repository") != SOURCE_REPO:
        raise ValueError("unexpected manifest schema or source")
    commit = manifest.get("source_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("unpinned source commit")
    tracks = manifest.get("tracks")
    if not isinstance(tracks, list) or len(tracks) != 5:
        raise ValueError("pilot must have exactly 5 entries")
    seen = set()
    for t in tracks:
        tid = t.get("track_id", "")
        if not isinstance(tid, str) or not re.fullmatch(r"[1-9][0-9]{0,19}", tid) or tid in seen:
            raise ValueError("invalid or duplicate track ID")
        seen.add(tid)
        for key in ("artist", "title"):
            val = t.get(key)
            if not isinstance(val, str) or not val.strip() or len(val) > 240 or any(c in val for c in "\r\n\x00"):
                raise ValueError("missing or unsafe track metadata")
        if not isinstance(t.get("source_bytes"), int) or not 1024 <= t["source_bytes"] <= MAX_AUDIO_BYTES:
            raise ValueError("unexpected source size")
        if not re.fullmatch(r"[a-f0-9]{40}", t.get("source_blob_sha1", "")):
            raise ValueError("invalid expected Git blob hash")
    return tracks


def compare_approved_snapshot(tracks, snapshot):
    if snapshot.get("schema") != 1 or snapshot.get("source") != "celikom_owner_catalog_snapshot" or snapshot.get("complete") is not True:
        raise ValueError("invalid or incomplete approved snapshot")
    existing = snapshot.get("tracks")
    if not isinstance(existing, list) or len(existing) != snapshot.get("total_tracks"):
        raise ValueError("inconsistent approved snapshot")
    approved_ids = [str(x.get("track_id")) for x in existing]
    if len(approved_ids) != len(set(approved_ids)):
        raise ValueError("duplicate IDs in approved snapshot")
    matched = [x["track_id"] for x in tracks if x["track_id"] in approved_ids]
    # Same-title may exist under another Track ID, so we report it rather than auto-importing.
    title_matches = []
    for x in tracks:
        for y in existing:
            if (str(y.get("title", "")).strip().casefold() == x["title"].casefold()
                    and x["track_id"] != str(y.get("track_id"))):
                title_matches.append({"candidate_id": x["track_id"], "existing_id": str(y["track_id"]), "title": x["title"]})
    return {"approved_total": len(existing), "exact_duplicates": matched, "same_title_other_id": title_matches}


def check_audio(track, commit, directory):
    """Source is pinned; bytes never leave this local temporary directory."""
    tid = track["track_id"]
    url = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{commit}/tracks/{tid}"
    target = Path(directory) / f"{tid}.source"
    hasher = hashlib.sha1()
    total = 0
    hasher.update(f"blob {track['source_bytes']}\0".encode("ascii"))
    request = Request(url, headers={"User-Agent": "CELIKOM-five-track-readonly-audit/1.0"})
    with urlopen(request, timeout=30) as response, target.open("wb") as out:
        while True:
            chunk = response.read(256 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_AUDIO_BYTES or total > track["source_bytes"]:
                raise ValueError(f"oversize or changed audio source for {tid}")
            hasher.update(chunk)
            out.write(chunk)
    if total != track["source_bytes"] or hasher.hexdigest() != track["source_blob_sha1"]:
        raise ValueError(f"size or Git blob SHA mismatch for {tid}")
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name,bit_rate:stream=codec_name,sample_rate,channels", "-of", "json", str(target)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    info = json.loads(proc.stdout)
    streams = [x for x in info.get("streams", []) if x.get("codec_name")]
    duration = float(info.get("format", {}).get("duration", 0))
    if duration < 10 or duration > 3600 or not streams:
        raise ValueError(f"invalid/unreadable audio for {tid}")
    target.unlink()  # Delete promptly, even before the temporary directory cleanup.
    return {"track_id": tid, "source_verified": True, "bytes": total, "duration_ms": round(duration * 1000), "codec": streams[0].get("codec_name"), "sample_rate": streams[0].get("sample_rate"), "channels": streams[0].get("channels"), "format": info.get("format", {}).get("format_name")}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path, help="read-only approved CELIKOM catalog JSON exported separately")
    p.add_argument("--audio-check", action="store_true", help="technical check of 5 pinned public source blobs in disposable runner; no publishing")
    p.add_argument("--report", type=Path, help="write metadata-only audit JSON")
    args = p.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tracks = validate_manifest(manifest)
    result = {"phase": "preflight_only", "source_commit": manifest["source_commit"], "candidate_count": len(tracks), "track_ids": [x["track_id"] for x in tracks], "live_db_checked": False, "audio_published": False, "production_changed": False, "warnings": ["No source-recording distribution rights established", "Snapshot is not a live check of pending/approved production DB; live dedupe required", "Media quality, censored content, target Yandex track duration and playback integration not yet validated"]}
    if args.catalog:
        snapshot = json.loads(args.catalog.read_text(encoding="utf-8"))
        result["snapshot"] = compare_approved_snapshot(tracks, snapshot)
    if args.audio_check:
        if not shutil_which("ffprobe"):
            raise RuntimeError("ffprobe must be installed for --audio-check")
        checks = []
        with tempfile.TemporaryDirectory(prefix="celikom-blur-audit-") as temp:
            for t in tracks:
                checks.append(check_audio(t, manifest["source_commit"], temp))
        result["audio_technical_checks"] = checks
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("snapshot", {}).get("exact_duplicates"):
        return 2
    return 0


def shutil_which(name):
    import shutil
    return shutil.which(name)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"PILOT FAILED: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)