package pro.celikom.nativeprobe

import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaMetadata
import android.media.audiofx.AudioEffect
import android.os.Environment
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import android.content.ContentValues
import android.provider.MediaStore
import android.graphics.Bitmap

@RunWith(AndroidJUnit4::class)
class ProbeTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context = instrumentation.targetContext
    @Test fun boundedReportRejectsSpoofAndDoesNotRequestAudioOrNetwork() {
        ProbeStore.clear(context)
        val spoof = Intent(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION)
            .putExtra(AudioEffect.EXTRA_PACKAGE_NAME, ProbeStore.YANDEX)
            .putExtra(AudioEffect.EXTRA_AUDIO_SESSION, 42)
        SessionReceiver().onReceive(context, spoof)
        val first = ProbeStore.report(context).getJSONArray("events").getJSONObject(0)
        assertFalse(first.getBoolean("verified_panel_caller")); assertFalse(first.getBoolean("effect_applied"))
        assertEquals(1, ProbeStore.report(context).getJSONArray("events").length())
        ProbeStore.clear(context)
        repeat(40) { index -> ProbeStore.event(context, ProbeStore.effectEvent(Intent(spoof).putExtra(AudioEffect.EXTRA_AUDIO_SESSION, index + 1), null)) }
        assertEquals(30, ProbeStore.report(context).getJSONArray("events").length())
        ProbeStore.setEnabled(context, false); SessionReceiver().onReceive(context, spoof)
        assertEquals(30, ProbeStore.report(context).getJSONArray("events").length())
        ProbeStore.setEnabled(context, true)
        val permissions = context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_PERMISSIONS).requestedPermissions?.toList() ?: emptyList()
        for (name in listOf("android.permission.INTERNET", "android.permission.RECORD_AUDIO", "android.permission.MODIFY_AUDIO_SETTINGS")) assertFalse(permissions.contains(name))
        val metadata = MediaMetadata.Builder().putString(MediaMetadata.METADATA_KEY_MEDIA_ID, "144530503")
            .putString(MediaMetadata.METADATA_KEY_MEDIA_URI, "https://user:secret@example.org/track/144530503?token=secret#secret")
            .putString("private.credentials", "secret").build()
        val safe = ProbeStore.metadata(metadata)
        assertFalse(safe.toString().contains("secret")); assertFalse(safe.getBoolean("exact_track_id_verified"))
        val bundle = android.os.Bundle().apply { putString("trackId", "36116709"); putString("media_id", "-4"); putString("password", "secret") }
        assertEquals("36116709", ProbeStore.numericCandidates(bundle).getString("trackId"))
        assertFalse(ProbeStore.numericCandidates(bundle).toString().contains("secret"))
        assertFalse(ProbeStore.numericCandidates(bundle).has("media_id"))
        ProbeStore.clear(context)
    }
    @Test fun sharedLinkIsExplicitReferenceAndNeverClaimsCurrentTrack() {
        ProbeStore.clear(context)
        assertTrue(ProbeStore.acceptSharedLink(context, "https://music.yandex.ru/album/1777786/track/36116709?token=do-not-store"))
        val report = ProbeStore.report(context)
        assertEquals("36116709", report.getJSONObject("shared_track").getString("track_id"))
        assertFalse(report.getJSONObject("shared_track").getBoolean("current_track_verified"))
        assertFalse(report.toString().contains("do-not-store"))
        assertFalse(ProbeStore.acceptSharedLink(context, "https://example.org/album/1/track/2"))
        assertFalse(ProbeStore.acceptSharedLink(context, "https://music.yandex.ru/album/1/track/2evil"))
        assertFalse(ProbeStore.acceptSharedLink(context, "https://user:secret@music.yandex.ru/album/1/track/2"))
        if (BuildConfig.PANEL_ONLY) {
            assertFalse(report.getBoolean("automatic_track_observation"))
            val info = context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_SERVICES)
            assertFalse(info.services?.any { it.name.endsWith("MusicListener") } ?: false)
            assertEquals(0, report.getJSONObject("media").length())
        }
        ProbeStore.clear(context)
    }
    @Test fun nativeUiStartsWithoutYandexOrLoginAndProducesScreenshot() {
        val activity = instrumentation.startActivitySync(Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        instrumentation.waitForIdleSync()
        val view = activity.window.decorView
        assertTrue(view.width > 0); assertTrue(view.height > 0)
        val image = instrumentation.uiAutomation.takeScreenshot()
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, "native-probe.png")
            put(MediaStore.MediaColumns.MIME_TYPE, "image/png")
            put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
        }
        val uri = context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values) ?: error("Cannot save screenshot")
        context.contentResolver.openOutputStream(uri)!!.use { assertTrue(image.compress(Bitmap.CompressFormat.PNG, 100, it)) }
        image.recycle()
        instrumentation.runOnMainSync { activity.finish() }
    }
}
