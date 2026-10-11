package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Intent
import android.content.IntentFilter
import android.media.MediaMetadata
import android.media.audiofx.AudioEffect
import android.media.session.MediaController
import android.media.session.MediaSessionManager
import android.media.session.PlaybackState
import android.os.Handler
import android.os.Looper
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject

class MusicListener : NotificationListenerService() {
    private val handler = Handler(Looper.getMainLooper())
    private val callbacks = mutableMapOf<MediaController, MediaController.Callback>()
    private val manager by lazy { getSystemService(MediaSessionManager::class.java) }
    private val sessionsChanged = MediaSessionManager.OnActiveSessionsChangedListener { bind(it ?: emptyList()) }
    private val receiver = SessionReceiver()
    private var registered = false
    override fun onListenerConnected() {
        if (registered) cleanup()
        ProbeStore.put(this, "listener", JSONObject().put("connected", true).put("at_ms", System.currentTimeMillis()))
        try {
            manager.addOnActiveSessionsChangedListener(sessionsChanged, ComponentName(this, MusicListener::class.java), handler)
            val filter = IntentFilter(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION)
            filter.addAction(AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION)
            ContextCompat.registerReceiver(this, receiver, filter, ContextCompat.RECEIVER_EXPORTED)
            registered = true
            refresh()
        } catch (e: SecurityException) { failure(e) }
    }
    private fun refresh() {
        try { bind(manager.getActiveSessions(ComponentName(this, MusicListener::class.java))) }
        catch (e: SecurityException) { failure(e) }
    }
    private fun failure(e: SecurityException) {
        ProbeStore.put(this, "listener", JSONObject().put("connected", false).put("error", e.javaClass.simpleName))
    }
    private fun bind(controllers: List<MediaController>) {
        val selected = if (ProbeStore.enabled(this)) controllers.filter { it.packageName == ProbeStore.YANDEX }.take(4) else emptyList()
        callbacks.keys.filter { old -> selected.none { it.sessionToken == old.sessionToken } }.toList().forEach { old ->
            callbacks.remove(old)?.let { old.unregisterCallback(it) }
        }
        selected.filter { candidate -> callbacks.keys.none { it.sessionToken == candidate.sessionToken } }.forEach { c ->
            val cb = object : MediaController.Callback() {
                override fun onMetadataChanged(metadata: MediaMetadata?) = save()
                override fun onPlaybackStateChanged(state: PlaybackState?) = save()
                override fun onQueueChanged(queue: MutableList<android.media.session.MediaSession.QueueItem>?) = save()
                override fun onExtrasChanged(extras: android.os.Bundle?) = save()
                override fun onSessionDestroyed() = refresh()
            }
            callbacks[c] = cb; c.registerCallback(cb, handler)
        }
        save()
    }
    private fun save() {
        if (!ProbeStore.enabled(this)) return
        val sessions = JSONArray()
        try { callbacks.keys.forEach { c ->
            val state = c.playbackState
            val queue = c.queue
            val item = queue?.firstOrNull { it.queueId == state?.activeQueueItemId }
            val description = item?.description
            val current = JSONObject().put("found", item != null).put("queue_size", queue?.size ?: 0)
                .put("active_queue_item_id", state?.activeQueueItemId ?: -1)
                .put("media_id", ProbeStore.clean(description?.mediaId) ?: JSONObject.NULL)
                .put("numeric_candidates", ProbeStore.numericCandidates(description?.extras))
                .put("extra_keys", ProbeStore.keys(description?.extras))
            val uri = description?.mediaUri
            if (uri != null) current.put("media_uri", ProbeStore.clean("${uri.scheme ?: ""}://${uri.host ?: ""}${uri.path ?: ""}"))
            sessions.put(JSONObject().put("package", c.packageName).put("metadata", ProbeStore.metadata(c.metadata))
                .put("state", state?.state ?: -1).put("position_ms", state?.position ?: -1)
                .put("position_update_elapsed_ms", state?.lastPositionUpdateTime ?: -1)
                .put("speed", state?.playbackSpeed ?: 0).put("actions", state?.actions ?: 0)
                .put("playback_error", state?.state == PlaybackState.STATE_ERROR)
                .put("current_queue_item", current).put("session_extra_keys", ProbeStore.keys(c.extras))
                .put("session_numeric_candidates", ProbeStore.numericCandidates(c.extras)))
        } } catch (e: SecurityException) { failure(e); return }
        ProbeStore.media(this, JSONObject().put("observed_at_ms", System.currentTimeMillis()).put("sessions", sessions))
    }
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn?.packageName == ProbeStore.YANDEX) refresh()
    }
    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        if (sbn?.packageName == ProbeStore.YANDEX) refresh()
    }
    override fun onListenerDisconnected() {
        ProbeStore.put(this, "listener", JSONObject().put("connected", false).put("at_ms", System.currentTimeMillis()))
        cleanup()
    }
    private fun cleanup() {
        callbacks.forEach { (c, cb) -> c.unregisterCallback(cb) }; callbacks.clear()
        manager.removeOnActiveSessionsChangedListener(sessionsChanged)
        if (registered) { unregisterReceiver(receiver); registered = false }
    }
    override fun onDestroy() { cleanup(); super.onDestroy() }
}
