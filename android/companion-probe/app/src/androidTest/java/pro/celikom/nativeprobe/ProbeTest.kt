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
        for (name in listOf("android.permission.INTERNET", "android.permission.RECORD_AUDIO")) assertFalse(permissions.contains(name))
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
    @Test fun shortAttenuationReleasesAfterActivityFinishes() {
        ProbeStore.clear(context); ProbeStore.setEnabled(context,true)
        val activity = instrumentation.startActivitySync(Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        instrumentation.waitForIdleSync()
        val track=android.media.AudioTrack.Builder().setAudioAttributes(android.media.AudioAttributes.Builder()
            .setUsage(android.media.AudioAttributes.USAGE_MEDIA).setContentType(android.media.AudioAttributes.CONTENT_TYPE_MUSIC).build())
            .setAudioFormat(android.media.AudioFormat.Builder().setEncoding(android.media.AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(8000).setChannelMask(android.media.AudioFormat.CHANNEL_OUT_MONO).build())
            .setTransferMode(android.media.AudioTrack.MODE_STATIC).setBufferSizeInBytes(16000).build()
        try {
            track.write(ByteArray(16000),0,16000); track.setLoopPoints(0,8000,-1); track.play()
            ProbeStore.event(context, ProbeStore.effectEvent(Intent(AudioEffect.ACTION_DISPLAY_AUDIO_EFFECT_CONTROL_PANEL)
                .putExtra(AudioEffect.EXTRA_AUDIO_SESSION,track.audioSessionId),ProbeStore.YANDEX))
            instrumentation.runOnMainSync { context.startForegroundService(Intent(context,AttenuationService::class.java).putExtra("play_tone",true)) }
            android.os.SystemClock.sleep(500)
            assertEquals("waiting",ProbeStore.report(context).getJSONObject("attenuation_test").getString("status"))
            instrumentation.runOnMainSync { activity.finish() }
            android.os.SystemClock.sleep(4000)
            val active=ProbeStore.report(context).getJSONObject("attenuation_test")
            assertEquals("attenuating",active.getString("status")); assertTrue(active.getBoolean("effect_attached"))
            val blocking = java.util.concurrent.CountDownLatch(1)
            val unblocked = java.util.concurrent.CountDownLatch(1)
            android.os.Handler(android.os.Looper.getMainLooper()).post {
                blocking.countDown(); android.os.SystemClock.sleep(10000); unblocked.countDown()
            }
            assertTrue(blocking.await(2,java.util.concurrent.TimeUnit.SECONDS))
            android.os.SystemClock.sleep(7000)
            assertEquals(1L,unblocked.count) // The effect must release while UI dispatch is stalled.
            val result=ProbeStore.report(context).getJSONObject("attenuation_test")
            assertEquals("finished",result.getString("status")); assertEquals("timeout",result.getString("reason")); assertTrue(result.getBoolean("released"))
            assertFalse(result.getBoolean("audible_result_verified"))
            val tone=result.getJSONObject("test_tone")
            assertEquals("local_test_tone",tone.getString("source"));assertTrue(tone.getBoolean("different_from_yandex_session"))
            assertTrue(tone.getInt("played_frames")>16000);assertEquals(112000,tone.getInt("submitted_frames"))
            assertTrue(tone.getBoolean("released"));assertFalse(tone.getBoolean("focus_requested"))
            assertTrue(result.getBoolean("wake_lock_held_at_attach")); assertTrue(result.getBoolean("wake_lock_released"))
            assertTrue(result.getLong("elapsed_ms") in 9500..11500)
            assertTrue(result.getLong("mute_elapsed_ms") in 6000..8500)
            assertTrue(unblocked.await(5,java.util.concurrent.TimeUnit.SECONDS))
            assertTrue(result.getLong("finished_at_ms")-result.getLong("started_at_ms")<12000)
        } finally { context.stopService(Intent(context,AttenuationService::class.java));track.stop();track.release();ProbeStore.clear(context) }
    }
    @Test fun attenuationRequiresFreshVerifiedNonGlobalSession() {
        val now = System.currentTimeMillis()
        fun report(session: Int, verified: Boolean, age: Long) = org.json.JSONObject().put("events", org.json.JSONArray().put(
            org.json.JSONObject().put("action", AudioEffect.ACTION_DISPLAY_AUDIO_EFFECT_CONTROL_PANEL)
                .put("session_id", session).put("verified_panel_caller", verified).put("caller_package", ProbeStore.YANDEX)
                .put("observed_at_ms", now-age)))
        assertEquals(42, AttenuationService.verifiedSession(report(42,true,1000),now))
        assertNull(AttenuationService.verifiedSession(report(0,true,0),now))
        assertNull(AttenuationService.verifiedSession(report(-1,true,0),now))
        assertNull(AttenuationService.verifiedSession(report(42,false,0),now))
        assertNull(AttenuationService.verifiedSession(report(42,true,60001),now))
        assertNull(AttenuationService.verifiedSession(report(42,true,-1),now))
        val info=context.packageManager.getPackageInfo(context.packageName, PackageManager.GET_SERVICES)
        val service=info.services!!.first { it.name.endsWith("AttenuationService") }
        assertFalse(service.exported)
        if (android.os.Build.VERSION.SDK_INT >= 29) assertEquals(android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK,service.foregroundServiceType)
    }
    @Test fun publicBrowserRejectsForeignPrivateOrUnexportedServices() {
        val s = android.content.pm.ServiceInfo().apply { packageName = ProbeStore.YANDEX; exported = true; enabled = true }
        assertTrue(PublicMediaProbe.eligible(s))
        s.permission = "android.permission.MEDIA_CONTENT_CONTROL"; assertFalse(PublicMediaProbe.eligible(s))
        s.permission = null; s.exported = false; assertFalse(PublicMediaProbe.eligible(s))
        s.exported = true; s.packageName = "other.app"; assertFalse(PublicMediaProbe.eligible(s))
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
