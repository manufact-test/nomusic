import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clone_native_identity_phase2_ephemeral import (
    resolved_provider_authorities, OLD_SYNC, NEW_SYNC
)

ORIGINAL = """<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application>
  <provider android:name="com.x.P" android:authorities="@string/passport_sync_adapter_content_authority" />
  <provider android:name="com.x.Q" android:authorities="com.yandex.preinstallsatellite.appmetrica.provider" />
</application></manifest>"""

class ResolvedProviderIdentityTest(unittest.TestCase):
    def test_original_vs_rewritten_distinct(self):
        alt = ORIGINAL.replace(
            "com.yandex.preinstallsatellite.appmetrica.provider",
            "pro.celikom.nativeclonelab.appmetrica.provider.v01"
        )
        old = resolved_provider_authorities(ORIGINAL.encode(), OLD_SYNC)
        new = resolved_provider_authorities(alt.encode(), NEW_SYNC)
        self.assertEqual(2, len(old))
        self.assertEqual(2, len(new))
        self.assertEqual(set(), old & new)

    def test_same_provider_is_collision(self):
        old = resolved_provider_authorities(ORIGINAL.encode(), OLD_SYNC)
        new = resolved_provider_authorities(ORIGINAL.encode(), NEW_SYNC)
        self.assertTrue(old & new)

    def test_unknown_authority_resource_fails_closed(self):
        with self.assertRaisesRegex(Exception, "UNRESOLVED_PROVIDER_AUTHORITY_RESOURCE"):
            resolved_provider_authorities(
                ORIGINAL.replace("passport_sync_adapter_content_authority", "unexpected_unknown_name").encode(),
                NEW_SYNC
            )

if __name__ == "__main__":
    unittest.main()
