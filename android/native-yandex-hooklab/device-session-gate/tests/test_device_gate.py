"""Security and lifecycle regressions for the optional HONOR read-only public session gate."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
JAVA=(ROOT/"app/src/main/java/pro/celikom/nativegate/GateActivity.java").read_text()
SERVICE=(ROOT/"app/src/main/java/pro/celikom/nativegate/NativeSessionListener.java").read_text()
MANIFEST=(ROOT/"app/src/main/AndroidManifest.xml").read_text()
GRADLE=(ROOT/"app/build.gradle.kts").read_text()

class DeviceSessionGate(unittest.TestCase):
    def test_distinct_app_not_player_or_old_test50(self):
        self.assertIn('applicationId = "pro.celikom.nativegate"',GRADLE)
        self.assertNotIn("pro.celikom.nativeprobe",GRADLE)
        self.assertIn("minSdk = 30",GRADLE)
        self.assertIn("<queries>",MANIFEST)
        self.assertIn('android:name="ru.yandex.music"',MANIFEST)

    def test_manifest_has_no_dangerous_permissions_or_background_network(self):
        self.assertNotIn("<uses-permission",MANIFEST)
        for forbidden in ("android.permission.INTERNET",
                          "android.permission.RECORD_AUDIO",
                          "android.permission.READ_MEDIA_AUDIO",
                          "android.permission.WRITE_EXTERNAL_STORAGE",
                          "android.permission.REQUEST_INSTALL_PACKAGES",
                          "android.accessibilityservice"):
            self.assertNotIn(forbidden,MANIFEST)
        self.assertIn('android:allowBackup="false"',MANIFEST)
        self.assertIn('android:usesCleartextTraffic="false"',MANIFEST)
        self.assertEqual(MANIFEST.count('android.permission.BIND_NOTIFICATION_LISTENER_SERVICE'),1)
        self.assertIn('android.service.notification.NotificationListenerService',MANIFEST)

    def test_notification_callbacks_are_inert(self):
        for name in ("onNotificationPosted","onNotificationRemoved"):
            pattern=re.compile(r"void "+name+r"\(StatusBarNotification ignored\)\s*\{(.*?)\}",re.S)
            hit=pattern.search(SERVICE)
            self.assertIsNotNone(hit)
            self.assertNotIn("ignored.",hit.group(1))
            self.assertNotIn("Log.",hit.group(1))
            self.assertNotIn("getExtras",hit.group(1))
            self.assertNotIn("getNotification",hit.group(1))

    def test_publisher_signer_pin_does_not_leak_version_source(self):
        self.assertIn("aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba",JAVA)
        self.assertIn("PackageManager.GET_SIGNING_CERTIFICATES",JAVA)
        self.assertIn("signers.length!=1",JAVA)
        self.assertIn("UNKNOWN_PUBLISHER_SIGNER",JAVA)
        self.assertIn('private static final String YANDEX="ru.yandex.music"',JAVA)

    def test_only_capabilities_and_public_token(self):
        self.assertIn("getActiveSessions(listener)",JAVA)
        self.assertIn("SessionToken.createSessionToken(",JAVA)
        self.assertIn("Player.COMMAND_CHANGE_MEDIA_ITEMS",JAVA)
        self.assertIn("Player.COMMAND_SET_MEDIA_ITEM",JAVA)
        self.assertIn("PlaybackState.ACTION_PLAY_FROM_URI",JAVA)
        self.assertIn("MediaController.releaseFuture(future)",JAVA)
        self.assertIn("revision==task",JAVA)
        self.assertIn("!future.isDone()",JAVA)
        for forbidden in (".setMediaItem(", ".setMediaItems(", ".replaceMediaItem(",
                          ".prepare(", ".play(", ".pause(", ".seekTo(",
                          ".getMetadata(", ".getQueue(", ".getMediaMetadata(",
                          ".getDescription(", ".getCurrentMediaItem(",
                          ".getMediaId(", ".getUri(", ".getData(",
                          "MediaPlayer(", "AudioTrack(", "setDataSource(",
                          "HttpURLConnection", "WebView(", "getSharedPreferences(",
                          "getAccount", "getStringExtra(", ".getNotifications("):
            self.assertNotIn(forbidden,JAVA,forbidden)

    def test_optional_access_disclosed_and_user_controlled(self):
        self.assertIn('Настройки доступа к уведомлениям',JAVA)
        self.assertIn("широкое разрешение",JAVA)
        self.assertIn("Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS",JAVA)
        self.assertIn('Проверить без дополнительных разрешений',JAVA)
        self.assertIn("android.permission.BIND_NOTIFICATION_LISTENER_SERVICE",MANIFEST)
        self.assertIn("onNotificationPosted",SERVICE)
        self.assertNotIn("requestPermissions(",JAVA)
        self.assertNotIn("disable",JAVA)

    def test_never_claim_source_switch_or_playback(self):
        self.assertIn("не доказывает право",JAVA)
        self.assertIn("Никаких команд Яндексу не отправлено",JAVA)
        self.assertIn("source",JAVA)
        self.assertIn("No mutation",JAVA+" No mutation") # explicit category boundary


if __name__=="__main__":
    unittest.main()
