"""Fail CI if the HONOR-accepted 0.3.85 seek transport is silently rewritten.

This intentionally protects only the local data-source selection and seek
completion methods. The user can authorize a separate cold-join experiment
without silently changing the working full-local-file scrubbing baseline.
"""

from pathlib import Path
import hashlib

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java"
).read_text(encoding="utf-8")

GOLDEN = {
    "finger_seek_submission": (
        " void seek(PlaybackSource s,long target,long drift,boolean correction){",
        "\n void prepare(",
        "768fa003614332ba7f3e7060e9637f2de2b7d8ca77bf82f38995f5267d430278",
    ),
    "async_seek_completion": (
        " void completeSeek(MediaPlayer mp,String key){",
        "\n boolean mute(",
        "9b3baed205fa6a36b308adaba172ac2453fb8818fbe8537ee2ece1e7d4ac4b4e",
    ),
    "automatic_local_file_selection": (
        "  if(fullFileExperiment){",
        "\n  if(key.equals(streamFallbackKey))",
        "5c3a2d7c9b3be00328996474031438a418c9a889a71cb8b01e0468937d3b635f",
    ),
}

for label, (start_marker, end_marker, expected) in GOLDEN.items():
    start = SOURCE.find(start_marker)
    assert start >= 0, f"HONOR 0.3.85 freeze: {label} entry removed"
    end = SOURCE.find(end_marker, start + len(start_marker))
    assert end > start, f"HONOR 0.3.85 freeze: {label} boundary removed"
    actual = hashlib.sha256(SOURCE[start:end].encode("utf-8")).hexdigest()
    assert actual == expected, (
        f"HONOR 0.3.85 accepted seek path changed ({label}). "
        "Explicitly review with the owner and update the saved baseline only "
        "if the replacement has passed a new real-device listening test."
    )

assert "ReplacementEngine(ProbeService owner){this(owner,true);}" in SOURCE, (
    "HONOR 0.3.85 freeze: production must default to the full local file"
)
print("PASS: HONOR 0.3.85 golden local-file source and seek/ACK implementation unchanged")
