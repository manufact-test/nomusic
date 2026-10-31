#!/usr/bin/env python3
"""Negative interpretation gates; synthetic data only, never owner audio metadata."""
import io
import json
from honor_journal_audit import audit_run, parse_runs, select_run


def event(name, t=0, **fields):
    return json.dumps({"elapsed_ms": t, "event": name, "data": fields})


synthetic = [
    "Human readable CELIKOM journal preface",
    "Not JSON; safe to ignore before the first run",
    event("run_start", 0, version="0.3.69"),
    event("replacement_seek_complete", 100, elapsedMs=21, residualMs=3),
    event("run_start", 0, version="0.3.70"),
    event("replacement_seek_complete", 200, elapsedMs=990, residualMs=0),
    event("run_start", 0, version="0.3.71"),
    event("replacement_seek_complete", 400, elapsedMs=400, residualMs=330,
          trackId="PRIVATE_TRACK_OLD"),
    event("replacement_seek_complete", 450, elapsedMs=12, residualMs=6),
    event("source_discontinuity", 500, reasonCode=1, userSeek=True,
          oldIndex=0, nextIndex=1, title="DO_NOT_PRINT_PRIVATE"),
    event("source_discontinuity", 520, reasonCode=1, userSeek=True,
          oldIndex=1, nextIndex=1),
    event("replacement_source_buffer_resumed", 530, bufferMs=51),
    event("replacement_decoder_advancing", 620, driftMs=205),
    event("replacement_unified_join_start", 621, phaseVerified=False,
          sourcePcmMeasured=False, trackId="PRIVATE_JOIN"),
    # This event is issued AFTER a commanded gap ends. At emission
    # sourceMutedCommand may already be false; do not reinterpret it.
    event("audio_command_anomaly", 650, kind="commanded_silence",
          durationMs=194, sourceMutedCommand=False),
    event("audio_command_anomaly", 660, kind="overlap_commands", durationMs=0),
    event("replacement_transition_complete", 800, joinMode="unified_complementary_linear"),
    event("replacement_transition_complete", 810, joinMode="exclusive_single_turn"),
]
runs = parse_runs(io.StringIO("\n".join(synthetic) + "\n"))
assert [run["start_line"] for run in runs] == [3, 5, 7]
latest = select_run(runs)
assert latest["version"] == "0.3.71"
report = audit_run(latest)
assert report["eventCount"] == 12, report
assert report["decoderSeekCallback"] == {
    "count": 2, "minMs": 12, "maxMs": 400, "over100Ms": 1,
    "over200Ms": 1, "over500Ms": 0, "absoluteResidualOver200Ms": 1,
}, report
assert report["media3Discontinuity"] == {
    "total": 2, "sameIndex": 1, "changedIndex": 1,
    "indexUnknown": 0, "reasonSeek": 2, "manualNextButtonObserved": False,
}, report
assert report["shortBufferResume"]["maxMs"] == 51
assert report["handover"]["joinCoarseTransportDriftMinMs"] == 205
assert report["handover"]["pcmPhaseVerified"] is False
assert report["handover"]["modeCounts"]["exclusive_single_turn"] == 1
assert report["audioCommandFindings"]["commanded_silence"] == 1
assert report["audioCommandFindings"]["overlap_commands"] == 1
assert audit_run(select_run(runs, "0.3.69"))["decoderSeekCallback"]["count"] == 1
assert audit_run(select_run(runs, "0.3.70"))["decoderSeekCallback"]["maxMs"] == 990
assert audit_run({"version": "future", "start_line": 1, "events": [
    {"elapsed_ms": 0, "event": "source_media_item_transition",
     "data": {"manualNextButtonObserved": True}}
]})["media3Discontinuity"]["manualNextButtonObserved"] is True
assert "PRIVATE" not in json.dumps(report)
assert "DO_NOT_PRINT" not in json.dumps(report)
try:
    select_run(runs, "0.3.72")
except ValueError:
    pass
else:
    raise AssertionError("Missing version silently fell back to an unrelated run")
try:
    parse_runs(io.StringIO(event("run_start", 0, version="0.3.71") + "\nBROKEN_EVENT\n"))
except ValueError:
    pass
else:
    raise AssertionError("Malformed events within a run must not be silently ignored")
print("PASS: privacy-safe combined-journal interpretation gates (version, seek, Media3, PCM, gap, errors)")
