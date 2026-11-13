#!/usr/bin/env python3
"""Stage 10 read-only operator boundary inventory. NEVER deploy or approve.

The checks intentionally distinguish observed CI engineering evidence from
operator-controlled live prerequisites. A green result means "still blocked
safely", NOT a production release authorization.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SOURCES = {
    "public_home": "website/public/index.php",
    "public_admin": "website/public/admin/index.php",
    "owner_cli": "website/tools/create-website-admin.php",
    "derivative_cli": "website/tools/prepare-private-popup.php",
    "pending_review_cli": "website/tools/review-pending-popup.php",
    "coordinated_cli": "website/tools/backup-coordinated-cms.php",
    "standalone_content_cli": "website/tools/backup-cms-content.php",
    "standalone_full_db_cli": "website/tools/backup-full-cms-db.php",
    "database_writer_login": "website/app/src/AdminAuth.php",
    "database_writer_drafts": "website/app/src/CmsDraftStore.php",
    "database_writer_revisions": "website/app/src/CmsRevisions.php",
    "database_writer_settings": "website/app/src/CmsMediaAssignment.php",
    "filesystem_writer_media": "website/app/src/CmsMediaStore.php",
    "filesystem_writer_derivative": "website/app/src/CmsMediaDerivative.php",
    "locked_snapshot": "website/app/src/CmsConsistentBackup.php",
    "encrypted_db": "website/app/src/CmsFullDbBackup.php",
    "encrypted_offsite": "website/app/src/CmsOffsiteEnvelope.php",
    "isolated_sql_replay": "website/app/src/CmsSandboxRecovery.php",
    "isolated_sql_generation": "website/app/src/CmsSandboxGeneration.php",
    "isolated_http": "website/tests/fixtures/offline-generation-router.php",
    "readiness": "website/app/src/CmsReleaseReadiness.php",
    "deploy": ".github/workflows/deploy-celikom-website.yml",
}
CHECKS = {
    "production_site_guard": (
        "public_home", "CmsReleaseGate::approved", "http_response_code(503)",
        "noindex, nofollow, noarchive",
    ),
    "production_admin_guard": (
        "public_admin", "CmsReleaseGate::approved", "http_response_code(503)",
        "noindex, nofollow, noarchive",
    ),
    "cms_editor_http_writer_lock": (
        "public_admin", "CmsWriteQuiescence::writer", "REQUEST_METHOD",
    ),
    "owner_provisioning_writer_lock": (
        "owner_cli", "CmsWriteQuiescence::writer", "INSERT INTO admin_users",
    ),
    "private_image_derivative_writer_lock": (
        "derivative_cli", "CmsWriteQuiescence::writer",
        "CmsMediaDerivative::preparePending",
    ),
    "pending_review_is_read_only": (
        "pending_review_cli", "CmsMediaReleasePreflight::pending",
        "PHP_SAPI !== 'cli'",
    ),
    "backup_writer_freeze": (
        "coordinated_cli", "CmsWriteQuiescence::snapshot",
        "CmsConsistentBackup::capture",
    ),
    "snapshot_requires_exclusive_lock": (
        "locked_snapshot", "assertExclusive",
        "CmsRecoveryPair::inspect",
    ),
    "offsite_separate_key_required": (
        "encrypted_offsite", "CELIKOM_SITE_OFFSITE_KEY",
        "hash_equals($dbKey,$offsiteKey)",
    ),
    "offsite_ci_only": (
        "encrypted_offsite", "CELIKOM_SITE_SANDBOX_RESTORE",
        "getenv('CI')",
    ),
    "real_db_restore_ci_only": (
        "isolated_sql_replay", "celikom_site_ci_replay_",
        "celikom_site_test",
        "CELIKOM_SITE_SANDBOX_RESTORE",
    ),
    "sql_generation_ci_only": (
        "isolated_sql_generation", "gen-baseline",
        "CELIKOM_SITE_SANDBOX_RESTORE",
    ),
    "offline_http_not_public": (
        "isolated_http", "CELIKOM_SITE_HTTP_SANDBOX",
        "127.0.0.1", "/__ci/page",
    ),
    "operator_consent_remains_blocked": (
        "readiness", "'final_owner_joint_release_consent'] = false",
        "'owner_joint_release_approval_pending'",
    ),
    "full_live_restore_remains_unproved": (
        "readiness", "'full_database_backup_and_restore_verified'] = false",
        "'full_database_backup_and_restore_pending'",
    ),
    "production_file_rollback_remains_unproved": (
        "readiness", "'production_file_rollback_verified'] = false",
        "'production_file_rollback_pending'",
    ),
    "actual_production_deploy_hard_disabled": (
        "deploy", "&& false",
    ),
}
# Statically inventoried application DB and private-media writers. Changes to
# any of these entrypoints require a fresh writer-coverage and migration audit.
WRITERS = {
    "login_rate_limit_and_admin_audit": "database_writer_login",
    "draft_optimistic_changes": "database_writer_drafts",
    "published_revision_and_audit": "database_writer_revisions",
    "private_media_selection_settings": "database_writer_settings",
    "private_upload_and_audit": "filesystem_writer_media",
    "private_derived_image_review": "filesystem_writer_derivative",
}
WRITER_TOKENS = {
    "database_writer_login": "INSERT INTO audit_log",
    "database_writer_drafts": "UPDATE content_drafts",
    "database_writer_revisions": "INSERT INTO content_revisions",
    "database_writer_settings": "UPDATE site_settings",
    "filesystem_writer_media": "INSERT INTO media_assets",
    "filesystem_writer_derivative": "rename(",
}
# External writers/GC/cron, remote backup storage, SSL and consent are NOT
# knowable from this code repository; NEVER assert their approval in CI.
PRODUCTION_BLOCKERS = (
    "owner_joint_release_approval_pending",
    "production_mysql_and_media_recovery_unverified",
    "hostinger_filesystem_flock_and_fsync_unverified",
    "external_sql_cron_gc_writer_inventory_unverified",
    "operator_rights_legal_ssl_domain_reviews_pending",
    "encrypted_remote_backup_storage_and_restore_unverified",
    "atomic_server_generation_cutover_unverified",
    "operator_rollback_runbook_not_accepted",
)


def inventory(sources: dict[str, str]) -> dict:
    missing = {}
    for check, tokens in CHECKS.items():
        filekey, *needles = tokens
        for needle in needles:
            if needle not in sources.get(filekey, ""):
                missing.setdefault(check, []).append(needle)
    for purpose, entry in WRITERS.items():
        needle = WRITER_TOKENS[entry]
        if needle not in sources.get(entry, ""):
            missing.setdefault("writer_inventory_" + purpose, []).append(needle)

    public = sources.get("public_home", "") + sources.get("public_admin", "")
    for forbidden in ("CmsSandboxGeneration", "CmsSandboxReleaseCycle",
                      "CmsOffsiteEnvelope", "/__ci/health"):
        if forbidden in public:
            missing.setdefault("sandbox_must_not_connect_to_public", []).append(forbidden)
    deployment = sources.get("deploy", "")
    if "&& false" not in deployment or "celikom" not in deployment.lower():
        missing.setdefault("deployment_must_stay_disabled", []).append("hard lockout")

    # Standalone exports are not coordinated or sufficient for disaster recovery.
    for key in ("standalone_content_cli", "standalone_full_db_cli"):
        if "CmsConsistentBackup::capture" in sources.get(key, ""):
            missing.setdefault("standalone_exports_must_remain_independent", []).append(key)

    return {
        "format": "celikom-stage10-operator-coverage-v1",
        "ci_boundary_checks_pass": not missing,
        "failed_checks": sorted(missing),
        "cms_writer_inventory": sorted(WRITERS),
        "production_ready": False,
        "production_blockers": list(PRODUCTION_BLOCKERS),
        "proof_scope": "repository static guardrails only; not a hosting audit",
    }


def run() -> None:
    sources = {
        key: (REPO / file).read_text(encoding="utf-8")
        for key, file in SOURCES.items()
    }
    good = inventory(sources)
    assert good["ci_boundary_checks_pass"] and not good["failed_checks"], good
    assert good["production_ready"] is False and len(good["production_blockers"]) >= 8

    # Mutation tests prove the operator checklist fails CLOSED if a developer
    # accidentally deletes a lock, approvals, isolated routing or deploy gate.
    scenarios = (
        ("public_admin", "CmsWriteQuiescence::writer"),
        ("owner_cli", "CmsWriteQuiescence::writer"),
        ("derivative_cli", "CmsWriteQuiescence::writer"),
        ("locked_snapshot", "assertExclusive"),
        ("encrypted_offsite", "CELIKOM_SITE_SANDBOX_RESTORE"),
        ("readiness", "'final_owner_joint_release_consent'] = false"),
        ("deploy", "&& false"),
    )
    for key, token in scenarios:
        changed = dict(sources)
        assert token in changed[key], (key, token)
        changed[key] = changed[key].replace(token, "REMOVED_BY_FAULT_INJECTION", 1)
        bad = inventory(changed)
        assert not bad["ci_boundary_checks_pass"] and bad["failed_checks"], (key, token)
        assert bad["production_ready"] is False

    changed = dict(sources)
    changed["public_home"] += "\n// CmsSandboxGeneration must never route public pages\n"
    assert "sandbox_must_not_connect_to_public" in inventory(changed)["failed_checks"]

    print(json.dumps(good, sort_keys=True, ensure_ascii=False))
    print("Stage10: static writer/route/operator blocker inventory and 8 fail-closed mutations — PASS")


if __name__ == "__main__":
    run()
