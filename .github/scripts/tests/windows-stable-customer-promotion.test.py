import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
RELEASE = (ROOT / ".github/workflows/windows-stable-signed-release.yml").read_text()
FLOKI = (ROOT / ".github/workflows/windows-stable-floki-private-stage.yml").read_text()


class WindowsCustomerStablePromotionContract(unittest.TestCase):
    def test_existing_public_customer_route_defaults_to_floki_explicitly(self):
        self.assertIn("publish_target:", RELEASE)
        self.assertIn("type: choice", RELEASE)
        self.assertIn("default: floki", RELEASE)
        self.assertIn("CELIKOM_STABLE_PUBLISHER: ${{ inputs.publish_target || vars.CELIKOM_STABLE_PUBLISHER || 'floki' }}", RELEASE)
        self.assertIn("publish_floki:", RELEASE)
        floki_job = RELEASE.split("  publish_floki:", 1)[1].split("\n  publish:", 1)[0]
        self.assertIn("actions: read", floki_job)
        self.assertIn("contents: write", floki_job)
        self.assertIn("windows-stable-production", FLOKI)

    def test_customer_approval_is_written_only_after_protected_floki_stage(self):
        stage = FLOKI.index("Persist approved signed transfer for Floki root stable promotion")
        approval = FLOKI.index("Record owner-approved version for the existing public customer stable feed")
        self.assertLess(stage, approval)
        self.assertIn("environment: windows-stable-production", FLOKI)
        self.assertIn("actions: read", FLOKI)
        self.assertIn("contents: write", FLOKI)
        self.assertIn('/actions/runs/"+run_id+"/approvals', FLOKI)
        self.assertIn("PROTECTED_PRODUCTION_APPROVAL_NOT_RECORDED", FLOKI)
        self.assertNotIn('gh api "repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID/approvals"', FLOKI)
        self.assertIn('approvals=api("/actions/runs/"+run_id+"/approvals")', FLOKI)
        self.assertIn("owner_accepted", FLOKI)
        self.assertIn("CUSTOMER_STABLE_DOWNGRADE_REFUSED", FLOKI)
        self.assertIn("verifyExistingStableLatest", FLOKI)
        self.assertIn("46b36bb222154316f2229c35cf65e6c953e0b6524dfb0aad8de05949dc143a95", FLOKI)

    def test_public_customer_feed_is_verified_against_exact_signed_artifact(self):
        self.assertIn("verify_customer_stable:", RELEASE)
        self.assertIn("needs: [prepare, publish_floki]", RELEASE)
        self.assertIn("CELIKOM-Windows-P256-transfer-${{ inputs.version }}-${{ github.sha }}", RELEASE)
        self.assertIn("cmp \"$p/latest.json\" \"$p/public-latest.json\"", RELEASE)
        self.assertIn("sha256sum -c", RELEASE)
        self.assertIn("/downloads/windows/CELIKOM-Windows-stable.exe", RELEASE)
        self.assertIn("W198_PUBLIC_CUSTOMER_STABLE_OTA_VERIFIED", RELEASE)


if __name__ == "__main__":
    unittest.main()
