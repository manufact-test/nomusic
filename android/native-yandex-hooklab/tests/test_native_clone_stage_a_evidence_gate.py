"""Pure documentary Stage-A release gate tests. No Android or proprietary APK."""
import copy
import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = BASE / "native_clone_stage_a_evidence_gate.py"
EVIDENCE = BASE.parents[1] / "docs/android/CELIKOM-ANDROID-A1-STAGE-A-EVIDENCE-20261111.json"
spec = importlib.util.spec_from_file_location("native_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class StageAEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_current_frozen_true_arm_evidence_is_blocked_not_failed_validation(self):
        result = gate.inspect(self.data)
        self.assertEqual(result["result"], "STAGE_A_RELEASE_NO_GO")
        self.assertFalse(result["ready_for_user_apk"])
        self.assertFalse(result["ready_for_phase_b"])
        self.assertIn("clone_five_splits_main", result["blocked_gates"])
        self.assertIn("publisher_authorized_embedding", result["missing_release_prerequisites"])
        self.assertIn("owner_audible_stage_a_acceptance", result["unverified_gates"])
        self.assertTrue(result["no_ci_pass_is_audio_acceptance"])

    def test_no_forged_ready_flag(self):
        self.data["user_apk_release_allowed"] = True
        with self.assertRaises(gate.EvidenceError):
            gate.inspect(self.data)

    def test_no_fake_stage_b_before_owner(self):
        self.data["phase_b_start_allowed"] = True
        with self.assertRaises(gate.EvidenceError):
            gate.inspect(self.data)

    def test_no_signature_bypass_or_spoof(self):
        for k, v in [("signature_bypass_level", 1),
                     ("publisher_signature_spoofing", True),
                     ("owner_phone_touched_by_ci", True)]:
            with self.subTest(k=k):
                mutated=copy.deepcopy(self.data)
                mutated[k]=v
                with self.assertRaises(gate.EvidenceError):
                    gate.inspect(mutated)

    def test_no_secret_or_arbitrary_evidence_url(self):
        for fake in ("https://evil.invalid/secret",
                     "https://github.com/other/other/actions/runs/42991987803",
                     "https://github.com/manufact-test/nomusic/actions/runs/42991987803?token=PRIVATE"):
            with self.subTest(fake=fake):
                mutated=copy.deepcopy(self.data)
                mutated["gates"]["clone_five_splits_main"]["evidence"]=[fake]
                with self.assertRaises(gate.EvidenceError):
                    gate.inspect(mutated)

    def test_cannot_mislabel_unknown_publisher_permission_as_pass(self):
        self.data["gates"]["publisher_authorized_embedding"]["status"]="pass"
        with self.assertRaises(gate.EvidenceError):
            gate.inspect(self.data)

    def test_required_gates_cannot_be_dropped(self):
        del self.data["gates"]["owner_audible_stage_a_acceptance"]
        with self.assertRaises(gate.EvidenceError):
            gate.inspect(self.data)

    def test_cli_current_report_success_as_audit_but_not_releasable(self):
        p=subprocess.run([sys.executable,str(SCRIPT),str(EVIDENCE)],
                         capture_output=True,text=True,timeout=20)
        self.assertEqual(p.returncode,0)
        self.assertEqual(json.loads(p.stdout)["result"],"STAGE_A_RELEASE_NO_GO")
        gated=subprocess.run([sys.executable,str(SCRIPT),str(EVIDENCE),
                              "--require-release-ready"],
                             capture_output=True,text=True,timeout=20)
        self.assertEqual(gated.returncode,2)
        self.assertFalse(json.loads(gated.stdout)["ready_for_user_apk"])


if __name__ == "__main__":
    unittest.main()
