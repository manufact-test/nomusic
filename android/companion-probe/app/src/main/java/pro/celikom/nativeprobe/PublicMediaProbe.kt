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
    private val phases = linkedMapOf<String,String>()
    private val attempts = JSONArray()
    private var leaseUntil = 0L
    private val modern = ModernMediaProbe(context) { name, phase, error -> attempt(name,phase,error);paintConnection() }
    private fun attempt(name: String, phase: String, error: String? = null) {
        phases[name] = phase
        if (attempts.length()>=30) attempts.remove(0)
        attempts.put(JSONObject().put("component",ProbeStore.clean(name)).put("event",phase)
            .put("at_ms",System.currentTimeMillis()).put("error_type",error ?: JSONObject.NULL))
        ProbeStore.put(context,"browser_attempts",JSONObject().put("events",attempts))
    }
    private fun paintConnection() {
        val phase = connectionStatus(phases.values,controllers.isNotEmpty() || modern.connected)
        status(phase)
    }
    companion object {
        private var shared: PublicMediaProbe? = null
        fun shared(context: Context): PublicMediaProbe = shared ?: PublicMediaProbe(context.applicationContext).also { shared = it }
        fun connectionStatus(phases: Collection<String>, connected: Boolean): String = when {
            connected -> "connected"
            phases.any { it=="connecting" || it=="retry_wait" } -> "connecting"
            phases.any { it=="timeout_without_callback" } -> "connection_timeout"
            else -> "connection_failed"
        }
        fun eligible(s: ServiceInfo): Boolean = MediaServiceDiscovery.reason(s,ProbeStore.YANDEX) == "eligible"
    }
    private fun status(value: String, count: Int = phases.size) {
        ProbeStore.put(context, "public_browser", JSONObject().put("status", value).put("attempted", count).put("at_ms", System.currentTimeMillis()))
    }
    fun start() {
        if (ProbeStore.enabled(context) && (modern.active || controllers.isNotEmpty() || phases.values.any { it=="retry_wait" })) {
            modern.refresh();controllers.keys.toList().forEach { save(it,generation) };paintConnection();renewLease();return
        }
        stop()
        renewLease()
        if (!ProbeStore.enabled(context)) { status("observation_disabled"); return }
        phases.clear()
        while (attempts.length()>0) attempts.remove(0)
        ProbeStore.put(context,"browser_attempts",JSONObject().put("events",attempts))
        val run = generation
        val discovery = try { MediaServiceDiscovery.scan(context) } catch (_: RuntimeException) {
            status("discovery_failed"); return
        }
        ProbeStore.put(context,"service_discovery",discovery.report)
        val services = discovery.candidates
        if (services.isEmpty()) { status("no_public_service"); return }
        status("connecting", services.size)
        services.forEach { s ->
            val rows = discovery.report.getJSONArray("declared_services")
            val modernService = (0 until rows.length()).map { rows.getJSONObject(it) }.any {
                it.optString("name")==s.name && it.getJSONArray("media_actions").toString().contains("androidx.media3.session.")
            }
            if (modernService) { modern.connect(ComponentName(s.packageName,s.name));return@forEach }
            attempt(s.name,"connecting")
            lateinit var browser: MediaBrowser
            val callback = object : MediaBrowser.ConnectionCallback() {
                override fun onConnected() {
                    if (run != generation || !ProbeStore.enabled(context)) { browser.disconnect(); return }
                    try {
                        val controller = MediaController(context, browser.sessionToken)
                        if (controller.packageName != ProbeStore.YANDEX) { attempt(s.name,"unexpected_package");browser.disconnect();paintConnection();return }
                        val changes = object : MediaController.Callback() {
                            override fun onMetadataChanged(metadata: MediaMetadata?) = save(controller, run)
                            override fun onPlaybackStateChanged(state: PlaybackState?) = save(controller, run)
                            override fun onQueueChanged(queue: MutableList<android.media.session.MediaSession.QueueItem>?) = save(controller, run)
                            override fun onSessionDestroyed() { if (run == generation) { status("session_destroyed"); ProbeStore.put(context, "public_media", JSONObject()) } }
                        }
                        controllers[controller] = changes
                        controller.registerCallback(changes, handler)
                        attempt(s.name,"connected");paintConnection();save(controller, run)
                    } catch (error: RuntimeException) { attempt(s.name,"connection_exception",error.javaClass.simpleName);paintConnection() }
                }
                override fun onConnectionFailed() { if (run==generation) { attempt(s.name,"connection_failed_callback");paintConnection() } }
                override fun onConnectionSuspended() { if (run == generation) { attempt(s.name,"connection_suspended_callback");status("connection_suspended"); ProbeStore.put(context, "public_media", JSONObject()) } }
            }
            browser = MediaBrowser(context, ComponentName(s.packageName, s.name), callback, null)
            browsers += browser
            try { browser.connect() } catch (error: RuntimeException) { attempt(s.name,"connect_exception",error.javaClass.simpleName);paintConnection() }
        }
        handler.postDelayed({
            if (run==generation && controllers.isEmpty() && !modern.connected) {
                phases.filterValues { it=="connecting" && !modern.active }.keys.toList().forEach { attempt(it,"timeout_without_callback") }
                browsers.forEach { try { it.disconnect() } catch (_: RuntimeException) { } }
                paintConnection()
            }
        },7000)
    }
    private fun renewLease() {
        leaseUntil = android.os.SystemClock.elapsedRealtime()+120000
        val run=generation
        handler.postDelayed({ if (run==generation && android.os.SystemClock.elapsedRealtime()>=leaseUntil) { stop();status("observation_window_finished",0) } },120000)
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
        modern.stop()
        handler.removeCallbacksAndMessages(null)
        controllers.forEach { (c, callback) -> try { c.unregisterCallback(callback) } catch (_: RuntimeException) { } }; controllers.clear()
        browsers.forEach { try { it.disconnect() } catch (_: RuntimeException) { } }; browsers.clear()
        ProbeStore.put(context, "public_media", JSONObject())
        status("stopped", 0)
    }
}
