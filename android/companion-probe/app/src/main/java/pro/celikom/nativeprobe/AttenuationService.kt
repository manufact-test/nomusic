package pro.celikom.nativeprobe

import android.app.Service
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.media.audiofx.AudioEffect
import android.media.audiofx.DynamicsProcessing
import android.os.Handler
import android.os.Looper
import android.os.IBinder
import android.os.SystemClock
import org.json.JSONObject

/** Explicit short diagnostic; no global mixer, track commands or automatic attach. */
class AttenuationService : Service() {
    private val handler = Handler(Looper.getMainLooper())
    private var effect: DynamicsProcessing? = null
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
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == STOP) { finish("user_stop"); return START_NOT_STICKY }
        if (deadline > 0) return START_NOT_STICKY
        val session = verifiedSession(ProbeStore.report(this), System.currentTimeMillis())
        if (!ProbeStore.enabled(this) || session == null) { stopSelf(); return START_NOT_STICKY }
        result = JSONObject().put("status", "waiting").put("session_id", session)
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
        deadline = SystemClock.elapsedRealtime()+10000
        ProbeStore.put(this, "attenuation_test", result)
        handler.postDelayed({ finish("timeout") }, 10000)
        handler.postDelayed({
            if (stopped || SystemClock.elapsedRealtime() >= deadline) return@postDelayed
            if (!ProbeStore.enabled(this) || verifiedSession(ProbeStore.report(this), System.currentTimeMillis()) != session) { finish("session_changed"); return@postDelayed }
            try {
                val candidate = DynamicsProcessing(0, session, null); effect = candidate
                if (!candidate.hasControl()) { finish("no_effect_control"); return@postDelayed }
                candidate.setInputGainAllChannelsTo(-100f)
                if (candidate.setEnabled(true) != AudioEffect.SUCCESS) { finish("enable_failed"); return@postDelayed }
                result.put("status", "attenuating").put("effect_attached", true).put("gain_db", -100)
                    .put("attached_at_ms", System.currentTimeMillis())
                ProbeStore.put(this, "attenuation_test", result)
            } catch (_: RuntimeException) { finish("effect_unavailable") }
        }, 3000)
        return START_NOT_STICKY
    }
    private fun release(): Boolean {
        var released = true
        effect?.let { try { it.setEnabled(false) } catch (_: RuntimeException) { }; try { it.release() } catch (_: RuntimeException) { released = false } }
        effect = null
        return released
    }
    private fun finish(reason: String) {
        if (stopped) return
        stopped = true; handler.removeCallbacksAndMessages(null); val released = release()
        if (result.length() > 0) {
            result.put("status", "finished").put("reason", reason).put("released", released).put("finished_at_ms", System.currentTimeMillis())
            ProbeStore.put(this, "attenuation_test", result)
        }
        stopForeground(STOP_FOREGROUND_REMOVE); stopSelf()
    }
    override fun onDestroy() { finish("service_destroyed"); release(); super.onDestroy() }
    override fun onTaskRemoved(rootIntent: Intent?) { finish("task_removed"); super.onTaskRemoved(rootIntent) }
}
