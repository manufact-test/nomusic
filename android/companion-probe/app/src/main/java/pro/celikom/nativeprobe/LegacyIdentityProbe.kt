package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Context
import android.media.browse.MediaBrowser
import android.media.session.MediaController
import android.media.session.PlaybackState
import android.os.Handler
import android.os.Looper
import org.json.JSONObject

/** Independent legacy transport to the SAME eligible public service; no hints or playback commands. */
class LegacyIdentityProbe(private val context: Context, private val expectedPackage: String = ProbeStore.YANDEX) {
    private val handler = Handler(Looper.getMainLooper())
    private var generation = 0
    private var browser: MediaBrowser? = null
    private var controller: MediaController? = null
    private var callback: MediaController.Callback? = null
    private var connecting = false
    private fun record(status: String, evidence: JSONObject = JSONObject()) {
        ProbeStore.put(context, "legacy_identity", evidence.put("status", status)
            .put("observed_at_ms", System.currentTimeMillis()).put("observed_elapsed_ms", android.os.SystemClock.elapsedRealtime())
            .put("process_instance", ProbeStore.processInstance).put("commands_sent", 0).put("exact_track_id_verified", false))
    }
    fun connect(component: ComponentName) {
        if (component.packageName != expectedPackage) { record("unexpected_package"); return }
        if (browser != null) { save(); return }
        val run = generation
        connecting = true
        record("connecting")
        lateinit var connection: MediaBrowser
        connection = MediaBrowser(context, component, object : MediaBrowser.ConnectionCallback() {
            override fun onConnected() {
                connecting = false
                if (run != generation || !ProbeStore.enabled(context)) { connection.disconnect(); return }
                try {
                    val current = MediaController(context, connection.sessionToken)
                    check(current.packageName == expectedPackage)
                    controller = current
                    val changes = object : MediaController.Callback() {
                        override fun onMetadataChanged(metadata: android.media.MediaMetadata?) { if (run == generation) save() }
                        override fun onPlaybackStateChanged(state: PlaybackState?) { if (run == generation) save() }
                        override fun onQueueChanged(queue: MutableList<android.media.session.MediaSession.QueueItem>?) { if (run == generation) save() }
                        override fun onExtrasChanged(extras: android.os.Bundle?) { if (run == generation) save() }
                        override fun onSessionDestroyed() { if (run == generation) { stop(); record("session_destroyed") } }
                    }
                    callback = changes
                    current.registerCallback(changes, handler)
                    save()
                    poll(run)
                } catch (error: RuntimeException) { record("connection_failed", JSONObject().put("error_type", error.javaClass.simpleName)) }
            }
            override fun onConnectionFailed() { if (run == generation) { connecting = false; record("connection_rejected") } }
            override fun onConnectionSuspended() { if (run == generation) { stop(); record("connection_suspended") } }
        }, null)
        browser = connection
        try { connection.connect() } catch (error: RuntimeException) { connecting = false; record("connection_failed", JSONObject().put("error_type", error.javaClass.simpleName)) }
        handler.postDelayed({ if (run == generation && connecting) { stop(); record("connection_timeout") } }, 7000)
    }
    private fun poll(run: Int) {
        handler.postDelayed({ if (run == generation && controller != null) { save(); poll(run) } }, 1000)
    }
    private fun save() {
        val current = controller ?: return
        if (!ProbeStore.enabled(context)) return
        try {
            val state = current.playbackState
            val activeId = state?.activeQueueItemId
            val item = if (activeId == null || activeId == android.media.session.MediaSession.QueueItem.UNKNOWN_ID.toLong()) null
                else current.queue?.firstOrNull { it.queueId == activeId }
            val description = item?.description
            record("connected", JSONObject().put("package", current.packageName)
                .put("metadata", ProbeStore.metadata(current.metadata))
                .put("session_extras", SessionIdentity.extras(current.extras))
                .put("browser_extras", SessionIdentity.extras(browser?.extras))
                .put("playback_extras", SessionIdentity.extras(state?.extras))
                .put("state", state?.state ?: -1).put("position_ms", state?.position ?: -1)
                .put("active_queue_id", activeId ?: JSONObject.NULL)
                .put("current_queue_item", JSONObject().put("found", item != null)
                    .put("media_id", ProbeStore.clean(description?.mediaId) ?: JSONObject.NULL)
                    .put("media_uri", MediaIdentity.uri(description?.mediaUri))
                    .put("extras", SessionIdentity.extras(description?.extras))))
        } catch (error: RuntimeException) { record("read_failed", JSONObject().put("error_type", error.javaClass.simpleName)) }
    }
    fun stop() {
        generation++
        connecting = false
        handler.removeCallbacksAndMessages(null)
        val changes = callback
        if (changes != null) try { controller?.unregisterCallback(changes) } catch (_: RuntimeException) { }
        controller = null; callback = null
        try { browser?.disconnect() } catch (_: RuntimeException) { }
        browser = null
        record("stopped")
    }
}
