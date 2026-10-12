package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.media.browse.MediaBrowser
import android.media.session.MediaController
import android.media.MediaMetadata
import android.media.session.PlaybackState
import android.os.Handler
import android.os.Looper
import org.json.JSONArray
import org.json.JSONObject

/** Only user-requested, exported and unprotected Yandex browser services. No identity spoofing. */
class PublicMediaProbe(private val context: Context) {
    private val handler = Handler(Looper.getMainLooper())
    private val browsers = mutableListOf<MediaBrowser>()
    private val controllers = mutableMapOf<MediaController, MediaController.Callback>()
    private var generation = 0
    companion object {
        fun eligible(s: ServiceInfo): Boolean = MediaServiceDiscovery.reason(s,ProbeStore.YANDEX) == "eligible"
    }
    private fun status(value: String, count: Int = browsers.size) {
        ProbeStore.put(context, "public_browser", JSONObject().put("status", value).put("attempted", count).put("at_ms", System.currentTimeMillis()))
    }
    fun start() {
        stop()
        if (!ProbeStore.enabled(context)) { status("observation_disabled"); return }
        val run = generation
        val discovery = try { MediaServiceDiscovery.scan(context) } catch (_: RuntimeException) {
            status("discovery_failed"); return
        }
        ProbeStore.put(context,"service_discovery",discovery.report)
        val services = discovery.candidates
        if (services.isEmpty()) { status("no_public_service"); return }
        status("connecting", services.size)
        services.forEach { s ->
            lateinit var browser: MediaBrowser
            val callback = object : MediaBrowser.ConnectionCallback() {
                override fun onConnected() {
                    if (run != generation || !ProbeStore.enabled(context)) { browser.disconnect(); return }
                    try {
                        val controller = MediaController(context, browser.sessionToken)
                        if (controller.packageName != ProbeStore.YANDEX) { browser.disconnect(); status("unexpected_package"); return }
                        val changes = object : MediaController.Callback() {
                            override fun onMetadataChanged(metadata: MediaMetadata?) = save(controller, run)
                            override fun onPlaybackStateChanged(state: PlaybackState?) = save(controller, run)
                            override fun onQueueChanged(queue: MutableList<android.media.session.MediaSession.QueueItem>?) = save(controller, run)
                            override fun onSessionDestroyed() { if (run == generation) { status("session_destroyed"); ProbeStore.put(context, "public_media", JSONObject()) } }
                        }
                        controllers[controller] = changes
                        controller.registerCallback(changes, handler)
                        status("connected"); save(controller, run)
                    } catch (_: RuntimeException) { status("connection_error") }
                }
                override fun onConnectionFailed() { if (run == generation && controllers.isEmpty()) status("connection_denied") }
                override fun onConnectionSuspended() { if (run == generation) { status("connection_suspended"); ProbeStore.put(context, "public_media", JSONObject()) } }
            }
            browser = MediaBrowser(context, ComponentName(s.packageName, s.name), callback, null)
            browsers += browser
            try { browser.connect() } catch (_: RuntimeException) { status("connection_denied") }
        }
        handler.postDelayed({ if (run == generation && controllers.isEmpty()) { browsers.forEach { try { it.disconnect() } catch (_: RuntimeException) { } }; status("not_connected") } }, 7000)
    }
    private fun save(c: MediaController, run: Int) {
        if (run != generation || !ProbeStore.enabled(context)) return
        try {
            val state = c.playbackState
            val item = c.queue?.firstOrNull { it.queueId == state?.activeQueueItemId }
            val current = JSONObject().put("found", item != null).put("media_id", ProbeStore.clean(item?.description?.mediaId) ?: JSONObject.NULL)
                .put("numeric_candidates", ProbeStore.numericCandidates(item?.description?.extras))
            val uri = item?.description?.mediaUri
            if (uri != null) current.put("media_uri", ProbeStore.clean("${uri.scheme ?: ""}://${uri.host ?: ""}${uri.path ?: ""}"))
            val session = JSONObject().put("package", c.packageName).put("metadata", ProbeStore.metadata(c.metadata))
                .put("state", state?.state ?: -1).put("position_ms", state?.position ?: -1).put("speed", state?.playbackSpeed ?: 0)
                .put("current_queue_item", current).put("exact_track_id_verified", false)
            ProbeStore.put(context, "public_media", JSONObject().put("observed_at_ms", System.currentTimeMillis()).put("sessions", JSONArray().put(session)))
        } catch (_: RuntimeException) { status("metadata_unavailable") }
    }
    fun stop() {
        generation++
        handler.removeCallbacksAndMessages(null)
        controllers.forEach { (c, callback) -> try { c.unregisterCallback(callback) } catch (_: RuntimeException) { } }; controllers.clear()
        browsers.forEach { try { it.disconnect() } catch (_: RuntimeException) { } }; browsers.clear()
        ProbeStore.put(context, "public_media", JSONObject())
        status("stopped", 0)
    }
}
