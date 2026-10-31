#!/usr/bin/env python3
"""Privacy-safe, run-scoped audit of CELIKOM JSONL diagnostics.

The report excludes track IDs, titles, identity keys and URLs. It summarizes
transport/control telemetry only; it cannot measure PCM phase or acoustic output.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Iterable


def data(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("data")
    return value if isinstance(value, dict) else {}


def number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def stats(values: Iterable[Any], thresholds: tuple[float, ...] = ()) -> dict[str, Any]:
    values = [number(v) for v in values]
    values = [v for v in values if v is not None]
    if not values:
        return {"count": 0, "min": None, "max": None, "median": None,
                "over": {str(t): 0 for t in thresholds}}
    return {"count": len(values), "min": min(values), "max": max(values),
            "median": statistics.median(values),
            "over": {str(t): sum(v > t for v in values) for t in thresholds}}


def parse_runs(lines: Iterable[str]) -> list[dict[str, Any]]:
    """Split a combined journal at run_start; ignore only the text preamble."""
    runs: list[dict[str, Any]] = []
    current = None
    for line_no, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw or not raw.startswith("{"):
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            if current is not None:
                raise ValueError(f"invalid JSON inside run at line {line_no}") from exc
            continue
        if not isinstance(event, dict) or not isinstance(event.get("event"), str):
            continue
        if event["event"] == "run_start":
            current = {"version": str(data(event).get("version", "unknown")),
                       "startLine": line_no, "events": []}
            runs.append(current)
        if current is not None:
            current["events"].append(event)
    return runs


def select_run(runs: list[dict[str, Any]], version: str | None = None) -> dict[str, Any]:
    if not runs:
        raise ValueError("no run_start event found")
    matches = runs if version is None else [r for r in runs if r["version"] == version]
    if not matches:
        raise ValueError(f"version {version!r} not found")
    return matches[-1]


def source_buffer_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Never pair a source-buffer start across a media-item boundary."""
    active: dict[Any, bool] = {}
    durations: list[float] = []
    retired = superseded = orphan_resumes = 0
    for event in events:
        name, d = event["event"], data(event)
        if name == "replacement_source_buffer":
            track = d.get("trackId")
            if track in active:
                superseded += 1
            active[track] = True
        elif name == "source_discontinuity":
            old, new = d.get("oldIndex"), d.get("nextIndex")
            if old is not None and new is not None and old != new:
                retired += len(active)
                active.clear()
        elif name in {"replacement_released", "replacement_source_boundary"}:
            retired += len(active)
            active.clear()
        elif name == "replacement_source_buffer_resumed":
            track = d.get("trackId")
            if track not in active and track is None and len(active) == 1:
                track = next(iter(active))
            if track in active:
                active.pop(track)
                duration = number(d.get("bufferMs"))
                if duration is not None:
                    durations.append(duration)
            else:
                orphan_resumes += 1
    return {
        "starts": sum(e["event"] == "replacement_source_buffer" for e in events),
        "resumes": sum(e["event"] == "replacement_source_buffer_resumed" for e in events),
        "completedIntervals": len(durations),
        "completedDurationMs": stats(durations),
        "retiredByItemBoundary": retired,
        "supersededStarts": superseded,
        "orphanResumes": orphan_resumes,
        "openAtRunEnd": len(active),
    }


def audit_run(run: dict[str, Any]) -> dict[str, Any]:
    events = run["events"]
    by: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        by.setdefault(event["event"], []).append(event)

    alignment = by.get("replacement_seek_complete", [])
    warm = by.get("replacement_warm_alignment", [])
    residuals = [abs(float(data(e)["residualMs"])) for e in alignment
                 if number(data(e).get("residualMs")) is not None]

    discontinuities = by.get("source_discontinuity", [])
    same = changed = unknown = reason_seek = 0
    for event in discontinuities:
        d = data(event)
        old, new = d.get("oldIndex"), d.get("nextIndex")
        if old is None or new is None:
            unknown += 1
        elif old == new:
            same += 1
        else:
            changed += 1
        reason_seek += d.get("reasonCode") == 1

    joins = by.get("replacement_unified_join_start", [])
    advancing = by.get("replacement_decoder_advancing", [])
    transitions = by.get("replacement_transition_complete", [])
    join_drifts: list[float] = []
    join_delays: list[float] = []
    unmatched_joins = 0
    for join in joins:
        jd, jt = data(join), join.get("elapsed_ms", -1)
        track = jd.get("trackId")
        prior = [e for e in advancing if e.get("elapsed_ms", -10**12) <= jt
                 and jt - e.get("elapsed_ms", -10**12) <= 50
                 and data(e).get("trackId") == track]
        if prior and number(data(prior[-1]).get("driftMs")) is not None:
            join_drifts.append(data(prior[-1])["driftMs"])
        following = [e for e in transitions if jt <= e.get("elapsed_ms", -1) <= jt + 500
                     and data(e).get("trackId") == track]
        if following and number(data(following[0]).get("commandDelayMs")) is not None:
            join_delays.append(data(following[0])["commandDelayMs"])
        else:
            unmatched_joins += 1

    anomalies: dict[str, int] = {}
    for event in by.get("audio_command_anomaly", []):
        kind = str(data(event).get("kind", "unknown"))
        anomalies[kind] = anomalies.get(kind, 0) + 1

    phase = [data(e).get("phaseVerified") for e in joins]
    pcm = [data(e).get("sourcePcmMeasured") for e in joins]
    stream_waits = by.get("replacement_stream_seek_data_wait", [])
    manual_next_true = sum(data(e).get("manualNextButtonObserved") is True
                           for e in by.get("source_media_item_transition", []))
    speeds = sorted({float(data(e)["speed"]) for e in by.get("player_state", [])
                     if number(data(e).get("speed")) is not None})
    summary_count = len(by.get("replacement_join_clock_summary", []))

    return {
        "version": run["version"],
        "runStartLine": run["startLine"],
        "eventCount": len(events),
        "runEndPresent": bool(by.get("run_end")),
        "sourceDiscontinuities": {
            "total": len(discontinuities), "reasonCodeSeek": reason_seek,
            "sameIndex": same, "changedIndex": changed, "unknownIndex": unknown,
            "manualNextFieldTrueEvents": manual_next_true,
        },
        "playbackSpeedValues": speeds,
        "seek": {
            "alignmentCallbacks": len(alignment),
            "alignmentCallbackElapsedMs": stats(
                [data(e).get("elapsedMs") for e in alignment], (200, 300)),
            "absoluteResidualMs": stats(residuals, (225, 350)),
            "warmAlignmentSeekStarts": len(warm),
            "warmAlignmentDriftMs": stats(
                [data(e).get("driftMs") for e in warm], (350,)),
            "minimumKnownNativeSeekStarts": len(alignment) + len(warm),
            "warmSeekCallbackTimingRecorded": False if warm else None,
        },
        "sourceBuffer": source_buffer_summary(events),
        "replacementStreamSeekDataWait": {
            "count": len(stream_waits),
            "sourceEffectRetainedTrue": sum(data(e).get("sourceEffectRetained") is True for e in stream_waits),
            "replacementSilentTrue": sum(data(e).get("replacementSilent") is True for e in stream_waits),
            "seekInFlightTrue": sum(data(e).get("seekInFlight") is True for e in stream_waits),
        },
        "newSongJoin": {
            "starts": len(joins),
            "joinClockSummaryRecords": summary_count,
            "joinClockCoverage": "recorded" if summary_count else ("not_recorded" if joins else "not_applicable"),
            "transportDriftImmediatelyBeforeJoinMs": stats(join_drifts),
            "postClockGateCommandDelayMsForMatchedJoins": stats(join_delays),
            "joinsWithoutMatchedCompletion": unmatched_joins,
            "phaseVerified": {
                "true": sum(v is True for v in phase),
                "false": sum(v is False for v in phase),
                "unknown": sum(v is None for v in phase),
            },
            "sourcePcmMeasured": {
                "true": sum(v is True for v in pcm),
                "false": sum(v is False for v in pcm),
                "unknown": sum(v is None for v in pcm),
            },
        },
        "commandAnomalies": anomalies,
        "interpretationLimits": [
            "Seek callbacks are transport callbacks, not audible-gap measurements.",
            "WARM seek callbacks are not timed by replacement_seek_complete.",
            "Media3 source buffering and replacement HTTP range waits are separate events.",
            "Join clock summaries measure transport drift only, not PCM phase.",
            "Command anomaly events describe commanded state, not acoustic output.",
            "Media3 SEEK does not identify a finger gesture or a specific UI button.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("journal", type=Path, help="combined CELIKOM JSONL journal")
    parser.add_argument("--version", help="select the last run with this exact version")
    parser.add_argument("--all-runs", action="store_true", help="report every run separately")
    args = parser.parse_args()
    try:
        with args.journal.open("r", encoding="utf-8") as handle:
            runs = parse_runs(handle)
        if args.all_runs:
            if args.version:
                parser.error("--version and --all-runs cannot be combined")
            report = [audit_run(run) for run in runs]
        else:
            report = audit_run(select_run(runs, args.version))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
