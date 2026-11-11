#!/usr/bin/env python3
"""CELIKOM Android A1 Stage-A release-readiness consistency gate.

This is a fail-closed documentary/evidence check, NOT a security attestation.
It never downloads APKs, contacts a device, changes a branch or reads secrets.
Evidence entries are factual states as of a frozen GitHub test source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GATE_IDS = frozenset({
    "owned_native_arm_lspatch_hook",
    "publisher_signed_original_arm_main",
    "clone_five_splits_main",
    "clone_merged_no_loader_main",
    "clone_merged_lspatch0_main",
    "publisher_authorized_embedding",
    "publisher_supported_native_ui_sdk",
    "independent_clone_native_ui_and_coexistence",
    "native_login_and_mywave",
    "same_yandex_decoder_licensed_source_swap",
    "pause_seek_next_and_background",
    "play_protect_enabled_owner_phone",
    "owner_audible_stage_a_acceptance",
    "exact_candidate_signed_sha_rollback_archived",
})
REQUIRED_TO_RELEASE = frozenset({
    "publisher_authorized_embedding",
    "independent_clone_native_ui_and_coexistence",
    "native_login_and_mywave",
    "same_yandex_decoder_licensed_source_swap",
    "pause_seek_next_and_background",
    "play_protect_enabled_owner_phone",
    "owner_audible_stage_a_acceptance",
    "exact_candidate_signed_sha_rollback_archived",
})
VALID_STATES = frozenset({"pass", "blocked", "not_tested", "unknown"})
ACTION_URL = re.compile(
    r"https://github[.]com/manufact-test/nomusic/actions/runs/[0-9]{6,16}$"
)
SOURCE_HASH = re.compile(r"[0-9a-f]{40}$")


class EvidenceError(ValueError):
    """A machine-verifiable dossier invariant is broken."""


def inspect(data: dict) -> dict:
    """Return a bounded release recommendation; reject contradictory claims.

    Does not evaluate whether uploaded evidence is *true*; GitHub CI must be
    independently checked by a developer, and user/audio checks need actual
    external verification.
    """
    if type(data) is not dict or data.get("schema") != 1 or \
            data.get("project") != "CELIKOM Android native A1":
        raise EvidenceError("INVALID_STAGE_A_EVIDENCE_SCHEMA")
    if data.get("requested_architecture") != "one independently signed native Android APK, original Yandex decoder":
        raise EvidenceError("NATIVE_PRODUCT_CONTRACT_CHANGED")
    if data.get("reference_branch") != "experiment/android-native-a1-lspatch-clone-loader0-20261111":
        raise EvidenceError("UNEXPECTED_REFERENCE_BRANCH")
    if not SOURCE_HASH.fullmatch(str(data.get("frozen_tested_source", ""))):
        raise EvidenceError("INVALID_FROZEN_SOURCE_SHA")
    if (data.get("signature_bypass_level") != 0 or
            type(data.get("signature_bypass_level")) is not int or
            data.get("publisher_signature_spoofing") is not False or
            data.get("owner_phone_touched_by_ci") is not False):
        raise EvidenceError("NATIVE_SECURITY_BOUNDARY_VIOLATED")

    gates = data.get("gates")
    if type(gates) is not dict or set(gates) != GATE_IDS:
        raise EvidenceError("STAGE_A_GATES_MISSING_OR_EXTRA")
    verified = []
    failed = []
    pending = []
    for key in sorted(gates):
        item = gates[key]
        if type(item) is not dict or set(item) != {"status", "evidence"}:
            raise EvidenceError("INVALID_GATE_RECORD")
        state, evidence = item["status"], item["evidence"]
        if state not in VALID_STATES or type(evidence) is not list or len(evidence) > 5:
            raise EvidenceError("INVALID_GATE_STATE_OR_EVIDENCE")
        if len(set(evidence)) != len(evidence) or not all(
            isinstance(x, str) and ACTION_URL.fullmatch(x) for x in evidence
        ):
            raise EvidenceError("EVIDENCE_REQUIRES_DIRECT_CI_RUN_URL")
        if state in ("pass", "blocked") and not evidence:
            raise EvidenceError("CONFIRMED_GATE_REQUIRES_CI_EVIDENCE")
        if state in ("unknown", "not_tested") and evidence:
            raise EvidenceError("PENDING_GATE_CANNOT_PRETEND_CI_PROOF")
        if state == "pass":
            verified.append(key)
        elif state == "blocked":
            failed.append(key)
        else:
            pending.append(key)

    missing_release = sorted(REQUIRED_TO_RELEASE.difference(verified))
    allowed = not missing_release
    claimed_release = data.get("user_apk_release_allowed")
    claimed_phase_b = data.get("phase_b_start_allowed")
    if type(claimed_release) is not bool or claimed_release != allowed:
        raise EvidenceError("RELEASE_FLAG_CONTRADICTS_REQUIRED_EVIDENCE")
    # Stage B only after owner audible acceptance, source swap and archived
    # owner-approved Stage A, regardless of structural CI PASS.
    phase_b_allowed = all(gates[x]["status"] == "pass" for x in (
        "owner_audible_stage_a_acceptance",
        "same_yandex_decoder_licensed_source_swap",
        "exact_candidate_signed_sha_rollback_archived",
    ))
    if type(claimed_phase_b) is not bool or claimed_phase_b != phase_b_allowed:
        raise EvidenceError("PHASE_B_FLAG_CONTRADICTS_OWNER_ACCEPTANCE")
    if allowed and not phase_b_allowed:
        raise EvidenceError("RELEASE_AND_PHASE_B_CONTRACT_MISMATCH")

    return {
        "result": "STAGE_A_RELEASE_GATES_SATISFIED" if allowed
                  else "STAGE_A_RELEASE_NO_GO",
        "source_revision_checked": bool(data.get("frozen_tested_source")),
        "ready_for_user_apk": allowed,
        "ready_for_phase_b": phase_b_allowed,
        "verified_gates": verified,
        "blocked_gates": failed,
        "unverified_gates": pending,
        "missing_release_prerequisites": missing_release,
        "owner_phone_ci_touched": False,
        "user_data_examined": False,
        "no_ci_pass_is_audio_acceptance": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="No-APK A1 Stage-A evidence gate")
    parser.add_argument("dossier", type=Path)
    parser.add_argument("--require-release-ready", action="store_true",
                        help="Fail when owner-ready APK is not proven")
    args = parser.parse_args()
    try:
        evidence = json.loads(args.dossier.read_text(encoding="utf-8"))
        result = inspect(evidence)
    except (EvidenceError, ValueError, OSError, UnicodeError) as err:
        message = str(err)
        category = message if re.fullmatch(r"[A-Z0-9_]{8,95}", message) else \
                   "STAGE_A_PRIVATE_EVIDENCE_ERROR"
        print(json.dumps({"result": "STAGE_A_EVIDENCE_INVALID",
                          "error_category": category}))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if args.require_release_ready and not result["ready_for_user_apk"] else 0


if __name__ == "__main__":
    sys.exit(main())
