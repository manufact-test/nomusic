#!/usr/bin/env python3
"""Privacy-safe structural audit of local CELIKOM combined Android journals.

Never claim physical audio, finger gestures or manual Next from transport logs.
This helper is for OFFLINE owner-supplied diagnostics, never a shipping APK.
"""
import argparse
import json
from collections import Counter
from pathlib import Path


def parse_runs(lines):
    runs = []
    for line_no, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            if not runs:  # Human-readable combined-report preamble.
                continue
            raise ValueError("Malformed JSON event at line %d" % line_no) from exc
        if not isinstance(event, dict) or not isinstance(event.get("event"), str):
            if runs:
                raise ValueError("Malformed event at line %d" % line_no)
            continue
        if event["event"] == "run_start":
            version = event.get("data", {}).get("version")
            if not isinstance(version, str):
                raise ValueError("Run without version at line %d" % line_no)
            runs.append({"version": version, "start_line": line_no, "events": []})
        if runs:
            runs[-1]["events"].append(event)
    if not runs:
        raise ValueError("No run_start event found")
    return runs


def select_run(runs, version=None):
    matching = [run for run in runs if version is None or run["version"] == version]
    if not matching:
        raise ValueError("No matching run_start version")
    return matching[-1]  # Never merge old and new sessions.


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def audit_run(run):
    events = run["events"]
    by_event = {}
    for event in events:
        by_event.setdefault(event["event"], []).append(event)
    data = lambda event: event.get("data", {}) if isinstance(event.get("data"), dict) else {}
    seek = [number(data(e).get("elapsedMs")) for e in by_event.get("replacement_seek_complete", [])]
    seek = [v for v in seek if v is not None]
    seek_residual = [abs(number(data(e).get("residualMs"))) for e in by_event.get("replacement_seek_complete", [])
                     if number(data(e).get("residualMs")) is not None]
    buffer_ms = [number(data(e).get("bufferMs")) for e in by_event.get("replacement_source_buffer_resumed", [])]
    buffer_ms = [v for v in buffer_ms if v is not None]
    source_events = by_event.get("source_discontinuity", [])
    known_indexes = [data(e) for e in source_events
                     if isinstance(data(e).get("oldIndex"), int) and isinstance(data(e).get("nextIndex"), int)]
    anomalies = Counter(data(e).get("kind", "unclassified") for e in by_event.get("audio_command_anomaly", []))
    transitions = Counter(data(e).get("joinMode", "unclassified")
                          for e in by_event.get("replacement_transition_complete", []))
    joins = by_event.get("replacement_unified_join_start", [])
    advancing = by_event.get("replacement_decoder_advancing", [])
    join_drift = []
    for join in joins:
        # Closest preceding decoder-clock validation, not speaker-PCM phase.
        prior = [e for e in advancing if 0 <= join["elapsed_ms"] - e["elapsed_ms"] <= 50]
        if prior:
            value = number(data(prior[-1]).get("driftMs"))
            if value is not None:
                join_drift.append(value)
    high_drift = [number(data(e).get("driftMs")) for e in advancing]
    high_drift = [v for v in high_drift if v is not None and abs(v) > 200]
    return {
        "version": run["version"],
        "startLine": run["start_line"],
        "eventCount": len(events),
        "decoderSeekCallback": {
            "count": len(seek), "minMs": min(seek) if seek else None,
            "maxMs": max(seek) if seek else None,
            "over100Ms": sum(v > 100 for v in seek),
            "over200Ms": sum(v > 200 for v in seek),
            "over500Ms": sum(v > 500 for v in seek),
            "absoluteResidualOver200Ms": sum(v > 200 for v in seek_residual),
        },
        "media3Discontinuity": {
            "total": len(source_events),
            "sameIndex": sum(d["oldIndex"] == d["nextIndex"] for d in known_indexes),
            "changedIndex": sum(d["oldIndex"] != d["nextIndex"] for d in known_indexes),
            "indexUnknown": len(source_events) - len(known_indexes),
            "reasonSeek": sum(data(e).get("userSeek") is True for e in source_events),
            "manualNextButtonProven": False,  # No button observation channel.
        },
        "shortBufferResume": {
            "count": len(buffer_ms), "maxMs": max(buffer_ms) if buffer_ms else None,
        },
        "handover": {
            "joinStarts": len(joins),
            "joinCoarseTransportDriftMinMs": min(join_drift) if join_drift else None,
            "joinCoarseTransportDriftMaxMs": max(join_drift) if join_drift else None,
            "decoderClockDriftAbsOver200Ms": len(high_drift),
            "modeCounts": dict(sorted(transitions.items())),
            "pcmPhaseVerified": False,
        },
        "audioCommandFindings": dict(sorted(anomalies.items())),
        "limitations": [
            "Decoder seek callback latency is not an audible gap or presentation timestamp.",
            "Media3 SEEK discontinuity can cross item indices: it is not proof of a finger swipe or Next button.",
            "Commanded-silence event describes an earlier interval, not the source-muted field at emission.",
            "Transport drift and gain commands cannot establish PCM phase, acoustic loudness or speaker silence.",
            "Counts across unequal-length listening runs are not normalized comparisons.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Private local CELIKOM journal audit; outputs no track metadata")
    parser.add_argument("journal", type=Path)
    parser.add_argument("--version", help="Select the last run_start of this exact version (default: last run)")
    args = parser.parse_args()
    with args.journal.open("r", encoding="utf-8-sig") as file:
        report = audit_run(select_run(parse_runs(file), args.version))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
