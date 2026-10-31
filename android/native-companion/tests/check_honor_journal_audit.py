#!/usr/bin/env python3
"""Synthetic regression checks for CELIKOM run-scoped diagnostic interpretation."""
import json
import unittest

from honor_journal_audit import audit_run, parse_runs, select_run


def row(elapsed_ms, event, **data):
    return json.dumps({"elapsed_ms": elapsed_ms, "event": event, "data": data})


class HonorJournalAuditTests(unittest.TestCase):
    def test_combined_runs_do_not_leak_old_join_summaries_into_latest_run(self):
        lines = [
            "CELIKOM COMBINED synthetic fixture",
            row(1, "run_start", version="0.3.70"),
            row(10, "replacement_unified_join_start", trackId="private-old", durationMs=160),
            row(170, "replacement_join_clock_summary", trackId="private-old",
                joinDriftStartMs=100, joinDriftEndMs=110,
                sourcePcmMeasured=False, phaseVerified=False),
            row(180, "run_end", reason="fixture"),
            row(1, "run_start", version="0.3.71"),
            row(10, "replacement_unified_join_start", trackId="private-mid", durationMs=160),
            row(180, "run_end", reason="fixture"),
            row(1, "run_start", version="0.3.72"),
            row(10, "replacement_unified_join_start", trackId="private-new", durationMs=160,
                sourcePcmMeasured=False, phaseVerified=False),
            row(180, "run_end", reason="fixture"),
        ]
        runs = parse_runs(lines)
        old = audit_run(select_run(runs, "0.3.70"))
        latest = audit_run(select_run(runs, "0.3.72"))
        self.assertEqual(old["newSongJoin"]["joinClockSummaryRecords"], 1)
        self.assertEqual(latest["newSongJoin"]["joinClockSummaryRecords"], 0)
        self.assertEqual(latest["newSongJoin"]["joinClockCoverage"], "not_recorded")
        self.assertNotIn("private-new", json.dumps(latest))

    def test_warm_seek_starts_are_not_miscounted_as_alignment_callbacks(self):
        lines = [
            row(1, "run_start", version="0.3.72"),
            row(100, "replacement_seek_complete", elapsedMs=679, residualMs=633, correctionPass=0),
            row(135, "replacement_seek_complete", elapsedMs=35, residualMs=38, correctionPass=1),
            row(150, "replacement_warm_alignment",
                **{"driftMs": 417, "pass": 1, "replacementAudible": False}),
        ]
        report = audit_run(select_run(parse_runs(lines)))
        self.assertEqual(report["seek"]["alignmentCallbacks"], 2)
        self.assertEqual(report["seek"]["warmAlignmentSeekStarts"], 1)
        self.assertEqual(report["seek"]["minimumKnownNativeSeekStarts"], 3)
        self.assertFalse(report["seek"]["warmSeekCallbackTimingRecorded"])

    def test_source_buffer_interval_is_retired_at_item_boundary(self):
        lines = [
            row(1, "run_start", version="0.3.72"),
            row(10, "replacement_source_buffer", trackId="old-track"),
            row(20, "source_discontinuity", oldIndex=4, nextIndex=5, reasonCode=1),
            row(30, "replacement_source_buffer", trackId="new-track"),
            row(50, "replacement_source_buffer_resumed", trackId="new-track", bufferMs=20),
        ]
        report = audit_run(select_run(parse_runs(lines)))
        source = report["sourceBuffer"]
        self.assertEqual(source["starts"], 2)
        self.assertEqual(source["completedIntervals"], 1)
        self.assertEqual(source["retiredByItemBoundary"], 1)
        self.assertEqual(source["completedDurationMs"]["max"], 20)

    def test_source_seek_and_item_change_are_separate_from_button_observation(self):
        lines = [
            row(1, "run_start", version="0.3.72"),
            row(10, "source_discontinuity", reasonCode=1, oldIndex=4, nextIndex=4, userSeek=True),
            row(20, "source_discontinuity", reasonCode=1, oldIndex=4, nextIndex=5, userSeek=True),
            row(21, "source_media_item_transition", reasonCode=2, manualNextButtonObserved=False),
        ]
        report = audit_run(select_run(parse_runs(lines)))
        source = report["sourceDiscontinuities"]
        self.assertEqual(source["reasonCodeSeek"], 2)
        self.assertEqual(source["sameIndex"], 1)
        self.assertEqual(source["changedIndex"], 1)
        self.assertEqual(source["manualNextFieldTrueEvents"], 0)

    def test_yandex_buffer_and_replacement_range_wait_are_not_merged(self):
        lines = [
            row(1, "run_start", version="0.3.72"),
            row(10, "replacement_source_buffer", trackId="source-track"),
            row(20, "replacement_source_buffer_resumed", trackId="source-track", bufferMs=10),
            row(30, "replacement_stream_seek_data_wait", trackId="replacement-track",
                cachedBytes=12345, sourceEffectRetained=True,
                replacementSilent=True, seekInFlight=True),
        ]
        report = audit_run(select_run(parse_runs(lines)))
        self.assertEqual(report["sourceBuffer"]["completedIntervals"], 1)
        self.assertEqual(report["replacementStreamSeekDataWait"]["count"], 1)
        self.assertEqual(report["replacementStreamSeekDataWait"]["replacementSilentTrue"], 1)

    def test_join_summary_absence_is_not_zero_drift_or_pcm_proof(self):
        lines = [
            row(1, "run_start", version="0.3.72"),
            row(100, "replacement_decoder_advancing", trackId="opaque", driftMs=250, waitMs=100),
            row(101, "replacement_unified_join_start", trackId="opaque", durationMs=160,
                phaseVerified=False, sourcePcmMeasured=False),
            row(280, "replacement_transition_complete", trackId="opaque", commandDelayMs=179),
            row(281, "audio_command_anomaly", kind="overlap_commands", durationMs=0),
        ]
        report = audit_run(select_run(parse_runs(lines)))
        join = report["newSongJoin"]
        self.assertEqual(join["joinClockCoverage"], "not_recorded")
        self.assertEqual(join["transportDriftImmediatelyBeforeJoinMs"]["max"], 250)
        self.assertEqual(join["postClockGateCommandDelayMsForMatchedJoins"]["max"], 179)
        self.assertEqual(join["phaseVerified"]["false"], 1)
        self.assertEqual(join["sourcePcmMeasured"]["false"], 1)
        self.assertEqual(report["commandAnomalies"], {"overlap_commands": 1})

    def test_malformed_json_inside_run_is_rejected(self):
        lines = [row(1, "run_start", version="0.3.72"), "{broken"]
        with self.assertRaises(ValueError):
            parse_runs(lines)


if __name__ == "__main__":
    unittest.main(verbosity=2)
