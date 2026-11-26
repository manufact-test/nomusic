package pro.celikom.nativeprobe

import android.app.Service
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.media.audiofx.AudioEffect
import android.media.audiofx.DynamicsProcessing
import android.os.PowerManager
import java.util.concurrent.ScheduledThreadPoolExecutor
import java.util.concurrent.TimeUnit
import android.os.IBinder
import android.os.SystemClock
import org.json.JSONObject

/** Explicit short diagnostic; no global mixer, track commands or automatic attach. */
class AttenuationService : Service() {
    private val scheduler = ScheduledThreadPoolExecutor(1) { runnable -> Thread(runnable, "celikom-audio-deadline") }
    private var wakeLock: PowerManager.WakeLock? = null
    private var startedElapsed = 0L
    private var attachedElapsed = 0L
    private var effect: DynamicsProcessing? = null
    private var tone: TestTone? = null
    private var playTone = false
    private var result = JSONObject()
    private var deadline = 0L
    private var stopped = false
    companion object {
        const val STOP = "pro.celikom.nativeprobe.STOP_ATTENUATION"
        fun verifiedSession(report: JSONObject, now: Long): Int? {
            val events = report.optJSONArray("events") ?: return null
            for (i in events.length()-1 downTo 0) {
                val event = events.getJSONObject(i)
                if (event.optString("action") != AudioEffect.ACTION_DISPLAY_AUDIO_EFFECT_CONTROL_PANEL) continue
                val age = now-event.optLong("observed_at_ms", 0)
                return event.optInt("session_id", -1).takeIf { it > 0 && age in 0..60000 &&
                    event.optBoolean("verified_panel_caller") && event.optString("caller_package") == ProbeStore.YANDEX }
            }
            return null
        }
    }
    override fun onBind(intent: Intent?): IBinder? = null
    @Synchronized override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == STOP) { finish("user_stop"); return START_NOT_STICKY }
        if (deadline > 0) return START_NOT_STICKY
        val session = verifiedSession(ProbeStore.report(this), System.currentTimeMillis())
        if (!ProbeStore.enabled(this) || session == null) { stopSelf(); return START_NOT_STICKY }
        playTone = intent?.getBooleanExtra("play_tone", false) == true
        result = JSONObject().put("mode", if (playTone) "attenuation_with_test_tone" else "attenuation_only").put("status", "waiting").put("session_id", session)
            .put("started_at_ms", System.currentTimeMillis()).put("delay_ms", 3000).put("duration_ms", 7000)
            .put("effect_attached", false).put("released", false).put("audible_result_verified", false)
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("sound_test", "Проверка звука CELIKOM", NotificationManager.IMPORTANCE_LOW))
        val stop = PendingIntent.getService(this, 1, Intent(this, AttenuationService::class.java).setAction(STOP), PendingIntent.FLAG_IMMUTABLE)
        val notification = Notification.Builder(this, "sound_test").setSmallIcon(android.R.drawable.ic_media_pause)
            .setContentTitle("CELIKOM: короткая проверка звука").setContentText("Автоматически закончится через 10 секунд")
            .setOngoing(true).addAction(Notification.Action.Builder(null, "Остановить", stop).build()).build()
        try {
            if (android.os.Build.VERSION.SDK_INT >= 29) startForeground(735, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK)
            else startForeground(735, notification)
        } catch (_: RuntimeException) { finish("foreground_denied"); return START_NOT_STICKY }
        try {
            wakeLock = getSystemService(PowerManager::class.java).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "CELIKOM:short-audio-test").apply {
                setReferenceCounted(false); acquire(15000)
            }
        } catch (_: RuntimeException) { finish("wake_lock_denied"); return START_NOT_STICKY }
        startedElapsed = SystemClock.elapsedRealtime()
        deadline = startedElapsed+10000
        result.put("timer", "worker_elapsed_with_bounded_wake_lock").put("started_elapsed_ms", startedElapsed)
        ProbeStore.put(this, "attenuation_test", result)
        scheduler.schedule({ finish("timeout") }, 10000, TimeUnit.MILLISECONDS)
        scheduler.schedule({ attach(session) }, 3000, TimeUnit.MILLISECONDS)
        return START_NOT_STICKY
    }
    @Synchronized private fun attach(session: Int) {
        if (stopped || SystemClock.elapsedRealtime() >= deadline) { finish("deadline_before_attach"); return }
        if (!ProbeStore.enabled(this) || verifiedSession(ProbeStore.report(this), System.currentTimeMillis()) != session) { finish("session_changed"); return }
        try {
            val candidate = DynamicsProcessing(0, session, null); effect = candidate
            if (!candidate.hasControl()) { finish("no_effect_control"); return }
            candidate.setInputGainAllChannelsTo(-100f)
            if (candidate.setEnabled(true) != AudioEffect.SUCCESS) { finish("enable_failed"); return }
            attachedElapsed = SystemClock.elapsedRealtime()
            result.put("status", "attenuating").put("effect_attached", true).put("gain_db", -100)
                .put("attached_at_ms", System.currentTimeMillis()).put("attach_delay_ms", attachedElapsed-startedElapsed)
                .put("wake_lock_held_at_attach", wakeLock?.isHeld == true)
            if (playTone) {
                tone = TestTone(session)
                tone!!.start()
                result.put("test_tone", tone!!.snapshot().put("started", true))
            }
            ProbeStore.put(this, "attenuation_test", result)
        } catch (_: RuntimeException) { finish(if (playTone) "effect_or_tone_unavailable" else "effect_unavailable") }
    }
    private fun release(): Boolean {
        var released = true
        effect?.let { try { it.setEnabled(false) } catch (_: RuntimeException) { }; try { it.release() } catch (_: RuntimeException) { released = false } }
        effect = null
        return released
    }
    @Synchronized private fun finish(reason: String) {
        if (stopped) return
        stopped = true
        tone?.let { player ->
            val snapshot = player.snapshot()
            snapshot.put("released",player.release())
            result.put("test_tone",snapshot)
        }
        tone = null
        val released = release()
        val elapsed = if (startedElapsed > 0) SystemClock.elapsedRealtime()-startedElapsed else 0L
        val mutedElapsed = if (attachedElapsed > 0) SystemClock.elapsedRealtime()-attachedElapsed else 0L
        try { if (wakeLock?.isHeld == true) wakeLock?.release() } catch (_: RuntimeException) { }
        val wakeReleased = wakeLock?.isHeld != true
        wakeLock = null
        scheduler.shutdownNow()
        if (result.length() > 0) {
            result.put("status", "finished").put("reason", reason).put("released", released).put("elapsed_ms", elapsed).put("mute_elapsed_ms", mutedElapsed)
                .put("wake_lock_released", wakeReleased).put("finished_at_ms", System.currentTimeMillis())
            ProbeStore.put(this, "attenuation_test", result)
        }
        stopForeground(STOP_FOREGROUND_REMOVE); stopSelf()
    }
    override fun onDestroy() { finish("service_destroyed"); super.onDestroy() }
    override fun onTaskRemoved(rootIntent: Intent?) { finish("task_removed"); super.onTaskRemoved(rootIntent) }
}
