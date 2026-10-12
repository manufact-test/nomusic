package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Context
import android.os.Handler
import android.os.Looper
import androidx.media3.common.Player
import androidx.media3.session.MediaBrowser
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import com.google.common.util.concurrent.ListenableFuture
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.Executor

/** Read-only Media3 connection using CELIKOM's real identity and no connection hints. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class ModernMediaProbe(private val context: Context, private val event: (String,String,String?) -> Unit) {
    private val handler = Handler(Looper.getMainLooper())
    private val futures = mutableMapOf<String,ListenableFuture<MediaBrowser>>()
    private val browsers = mutableMapOf<String,MediaBrowser>()
    private var generation = 0
    val connected: Boolean get() = browsers.isNotEmpty()
    fun connect(component: ComponentName) {
        val name = component.className + "#media3"
        val run = generation
        event(name,"connecting",null)
        try {
            val token = SessionToken(context,component)
            check(token.packageName == ProbeStore.YANDEX)
            val listener = object : MediaBrowser.Listener {
                override fun onDisconnected(controller: MediaController) {
                    if (run != generation) return
                    browsers.remove(name)?.release()
                    ProbeStore.put(context,"public_media",JSONObject())
                    event(name,"disconnected",null)
                }
            }
            val future = MediaBrowser.Builder(context,token).setListener(listener).buildAsync()
            futures[name] = future
            future.addListener({
                if (run == generation && ProbeStore.enabled(context)) {
                    try {
                        val browser = future.get()
                        check(browser.connectedToken?.packageName == ProbeStore.YANDEX)
                        browsers[name] = browser
                        browser.addListener(object : Player.Listener {
                            override fun onEvents(player: Player, events: Player.Events) { if (run==generation) save(browser) }
                        })
                        event(name,"connected",null)
                        save(browser)
                        poll(run)
                    } catch (error: Exception) {
                        MediaController.releaseFuture(future)
                        event(name,"connection_failed",(error.cause ?: error).javaClass.simpleName)
                    }
                } else MediaController.releaseFuture(future)
            },Executor { task -> handler.post(task) })
            handler.postDelayed({
                if (run==generation && !future.isDone) {
                    MediaController.releaseFuture(future)
                    event(name,"timeout_without_callback",null)
                }
            },7000)
        } catch (error: RuntimeException) { event(name,"connect_exception",error.javaClass.simpleName) }
    }
    private fun poll(run: Int) {
        handler.postDelayed({ if (run==generation && browsers.isNotEmpty()) {
            browsers.values.toList().forEach { save(it) }; poll(run)
        } },1000)
    }
    private fun save(browser: MediaBrowser) {
        if (!ProbeStore.enabled(context) || !browser.isConnected) return
        try {
            val metadata = browser.mediaMetadata
            val item = browser.currentMediaItem
            val session = JSONObject().put("package",ProbeStore.YANDEX).put("protocol","media3")
                .put("metadata",JSONObject().put("title",ProbeStore.clean(metadata.title?.toString()) ?: JSONObject.NULL)
                    .put("artist",ProbeStore.clean(metadata.artist?.toString()) ?: JSONObject.NULL)
                    .put("album",ProbeStore.clean(metadata.albumTitle?.toString()) ?: JSONObject.NULL))
                .put("media_id",ProbeStore.clean(item?.mediaId) ?: JSONObject.NULL)
                .put("numeric_candidates",ProbeStore.numericCandidates(metadata.extras))
                .put("position_ms",browser.currentPosition).put("duration_ms",browser.duration)
                .put("is_playing",browser.isPlaying).put("play_when_ready",browser.playWhenReady)
                .put("state",browser.playbackState).put("speed",browser.playbackParameters.speed)
                .put("can_read_current_item",browser.isCommandAvailable(Player.COMMAND_GET_CURRENT_MEDIA_ITEM))
                .put("exact_track_id_verified",false)
            ProbeStore.put(context,"public_media",JSONObject().put("observed_at_ms",System.currentTimeMillis()).put("sessions",JSONArray().put(session)))
        } catch (error: RuntimeException) { event("media3","metadata_unavailable",error.javaClass.simpleName) }
    }
    fun stop() {
        generation++
        handler.removeCallbacksAndMessages(null)
        futures.values.forEach { MediaController.releaseFuture(it) }; futures.clear()
        browsers.clear()
    }
}
