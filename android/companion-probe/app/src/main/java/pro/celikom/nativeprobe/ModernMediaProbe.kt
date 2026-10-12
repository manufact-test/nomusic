package pro.celikom.nativeprobe

import android.content.ComponentName
import android.content.Context
import android.os.Handler
import android.os.Looper
import androidx.media3.common.Player
import androidx.media3.session.MediaBrowser
import androidx.media3.session.MediaController
import androidx.media3.session.SessionToken
import androidx.media3.session.SessionCommand
import androidx.media3.session.LibraryResult
import androidx.media3.common.MediaItem
import com.google.common.util.concurrent.ListenableFuture
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.Executor

/** Read-only Media3 connection using CELIKOM's real identity and no connection hints. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
class ModernMediaProbe(private val context: Context, private val event: (String,String,String?) -> Unit, private val expectedPackage: String = ProbeStore.YANDEX) {
    private val handler = Handler(Looper.getMainLooper())
    private val futures = mutableMapOf<String,ListenableFuture<MediaBrowser>>()
    private val browsers = mutableMapOf<String,MediaBrowser>()
    private var generation = 0
    private val tickets = mutableMapOf<String,Int>()
    private val retries = mutableMapOf<String,Int>()
    private var polling = false
    private val catalogSnapshot: JSONObject? by lazy {
        try { context.assets.open("catalog-diagnostic.json").bufferedReader().use { JSONObject(it.readText()) } } catch (_: Exception) { null }
    }
    private var identityKey: String? = null
    private var identityQueries = 0
    private var identityFuture: ListenableFuture<LibraryResult<MediaItem>>? = null
    private fun identityKey(browser: MediaBrowser): String = listOf(browser.currentMediaItem?.mediaId,browser.mediaMetadata.title,browser.mediaMetadata.artist).joinToString("|")
    private fun inspectIdentity(browser: MediaBrowser) {
        val key=identityKey(browser)
        if (identityKey==key) return
        identityKey=key
        identityFuture?.cancel(false);identityFuture=null
        val run=generation
        val item=browser.currentMediaItem
        val evidence=JSONObject().put("observed_at_ms",System.currentTimeMillis()).put("current_item",MediaIdentity.item(item))
        val allowed=browser.availableSessionCommands.contains(SessionCommand.COMMAND_CODE_LIBRARY_GET_ITEM)
        evidence.put("get_item_allowed",allowed)
        fun record(status: String) { ProbeStore.put(context,"track_identity",evidence.put("status",status)) }
        if (!allowed) { record("get_item_not_allowed");return }
        val id=item?.mediaId
        if (id.isNullOrBlank()) { record("no_current_media_id");return }
        if (identityQueries>=3) { record("query_limit_reached");return }
        identityQueries++
        evidence.put("query_number",identityQueries)
        record("querying_current_item")
        try {
            val future=browser.getItem(id)
            identityFuture=future
            future.addListener({
                if (run==generation && identityKey==key && browser.isConnected && identityKey(browser)==key && !future.isCancelled) {
                    try {
                        val result=future.get()
                        evidence.put("result_code",result.resultCode).put("library_item",MediaIdentity.item(result.value))
                        record(if (result.value!=null) "current_item_received" else "current_item_unavailable")
                    } catch (error: Exception) {
                        evidence.put("error_type",(error.cause ?: error).javaClass.simpleName);record("current_item_failed")
                    }
                }
            },Executor { task -> handler.post(task) })
            handler.postDelayed({ if (run==generation && identityKey==key && !future.isDone) {
                future.cancel(false);record("current_item_timeout")
            } },5000)
        } catch (error: RuntimeException) { evidence.put("error_type",error.javaClass.simpleName);record("current_item_failed") }
    }
    private fun failure(component: ComponentName, stage: String, error: Throwable, run: Int, retry: Boolean) {
        if (run != generation) return
        val root = generateSequence(error) { it.cause }.take(6).last()
        val name = component.className + "#media3"
        val diagnostic = JSONObject().put("component",component.className).put("stage",stage)
            .put("error_type",root.javaClass.simpleName).put("attempt",retries[name] ?: 1)
            .put("reason",if (root is SecurityException && root.message?.contains("Session rejected the connection request") == true) "session_rejected" else "unspecified")
            .put("client_stack",JSONArray(root.stackTrace.take(6).map { it.className + "." + it.methodName }))
        ProbeStore.put(context,"media3_error",diagnostic)
        event(name,"connection_failed",root.javaClass.simpleName)
        if (retry && (retries[name] ?: 1) < 3) {
            event(name,"retry_wait",null)
            handler.postDelayed({ if (run==generation && ProbeStore.enabled(context)) connectAttempt(component) }, if (retries[name]==1) 1000L else 3000L)
        }
    }
    val connected: Boolean get() = browsers.values.any { it.isConnected }
    val active: Boolean get() = connected || futures.values.any { !it.isDone }
    fun refresh() { browsers.values.toList().forEach { save(it) } }
    fun connect(component: ComponentName) {
        val name = component.className + "#media3"
        if (browsers[name]?.isConnected==true || futures[name]?.isDone==false) { refresh();return }
        retries[name] = 0
        connectAttempt(component)
    }
    private fun connectAttempt(component: ComponentName) {
        val name = component.className + "#media3"
        val run = generation
        retries[name] = (retries[name] ?: 0) + 1
        val ticket = (tickets[name] ?: 0) + 1
        tickets[name] = ticket
        var stage = "create_token"
        event(name,"connecting",null)
        try {
            val token = SessionToken(context,component)
            check(token.packageName == expectedPackage)
            val listener = object : MediaBrowser.Listener {
                override fun onExtrasChanged(controller: MediaController, extras: android.os.Bundle) {
                    if (run==generation && tickets[name]==ticket && controller is MediaBrowser && controller.isConnected) save(controller)
                }
                override fun onDisconnected(controller: MediaController) {
                    if (run != generation || tickets[name]!=ticket || browsers[name] !== controller) return
                    browsers.remove(name)
                    futures.remove(name)?.let { MediaController.releaseFuture(it) }
                    ProbeStore.put(context,"public_media",JSONObject())
                    event(name,"disconnected",null)
                    retries[name] = 0
                    handler.postDelayed({ if (run==generation && ProbeStore.enabled(context)) connectAttempt(component) },1000)
                }
            }
            stage = "build_async"
            val future = MediaBrowser.Builder(context,token).setListener(listener).buildAsync()
            futures[name] = future
            future.addListener({
                if (run == generation && tickets[name]==ticket && ProbeStore.enabled(context)) {
                    try {
                        stage = "future_result"
                        val browser = future.get()
                        stage = "verify_connected_token"
                        check(browser.connectedToken?.packageName == expectedPackage)
                        check(browser.isConnected)
                        browsers[name] = browser
                        browser.addListener(object : Player.Listener {
                            override fun onEvents(player: Player, events: Player.Events) { if (run==generation) save(browser) }
                        })
                        event(name,"connected",null)
                        ProbeStore.put(context,"media3_error",JSONObject())
                        save(browser)
                        if (!polling) { polling = true;poll(run) }
                    } catch (error: Exception) {
                        MediaController.releaseFuture(future)
                        futures.remove(name)
                        browsers.remove(name)
                        failure(component,stage,error,run,true)
                    }
                } else MediaController.releaseFuture(future)
            },Executor { task -> handler.post(task) })
            handler.postDelayed({
                if (run==generation && tickets[name]==ticket && !future.isDone) {
                    tickets[name] = ticket + 1
                    futures.remove(name)
                    MediaController.releaseFuture(future)
                    event(name,"timeout_without_callback",null)
                }
            },7000)
        } catch (error: RuntimeException) { failure(component,stage,error,run,false) }
    }
    private fun poll(run: Int) {
        handler.postDelayed({ if (run==generation && browsers.isNotEmpty()) {
            refresh();poll(run)
        } else polling = false },1000)
    }
    private fun save(browser: MediaBrowser) {
        if (!ProbeStore.enabled(context) || !browser.isConnected) return
        try {
            val metadata = browser.mediaMetadata
            val item = browser.currentMediaItem
            val catalog=try {
                catalogSnapshot?.let { CatalogMatcher.match(it,metadata.title?.toString() ?: "",metadata.artist?.toString() ?: "",
                    metadata.albumTitle?.toString() ?: "",browser.duration,System.currentTimeMillis()) }
                    ?: JSONObject().put("status","catalog_unavailable")
            } catch (_: Exception) { JSONObject().put("status","catalog_invalid") }
            ProbeStore.put(context,"catalog_match",catalog.put("exact_track_id_verified",false).put("replacement_started",false))
            val session = JSONObject().put("package",expectedPackage).put("protocol","media3")
                .put("metadata",JSONObject().put("title",ProbeStore.clean(metadata.title?.toString()) ?: JSONObject.NULL)
                    .put("artist",ProbeStore.clean(metadata.artist?.toString()) ?: JSONObject.NULL)
                    .put("album",ProbeStore.clean(metadata.albumTitle?.toString()) ?: JSONObject.NULL))
                .put("media_id",ProbeStore.clean(item?.mediaId) ?: JSONObject.NULL)
                .put("numeric_candidates",ProbeStore.numericCandidates(metadata.extras))
                .put("item_numeric_candidates",ProbeStore.numericCandidates(item?.mediaMetadata?.extras))
                .put("metadata_extra_keys",JSONArray(metadata.extras?.keySet()?.sorted()?.take(24)?.map { ProbeStore.clean(it)?.take(64) } ?: emptyList<String>()))
                .put("position_ms",browser.currentPosition).put("duration_ms",browser.duration)
                .put("is_playing",browser.isPlaying).put("play_when_ready",browser.playWhenReady)
                .put("state",browser.playbackState).put("speed",browser.playbackParameters.speed)
                .put("can_read_current_item",browser.isCommandAvailable(Player.COMMAND_GET_CURRENT_MEDIA_ITEM))
                .put("exact_track_id_verified",false)
            val commands=JSONArray()
            browser.availableSessionCommands.commands.toList().sortedBy { it.commandCode.toString()+it.customAction }.take(24).forEach { command ->
                commands.put(JSONObject().put("code",command.commandCode).put("action",ProbeStore.clean(command.customAction) ?: JSONObject.NULL)
                    .put("extras",SessionIdentity.extras(command.customExtras)))
            }
            ProbeStore.put(context,"session_identity",JSONObject().put("observed_at_ms",System.currentTimeMillis())
                .put("current_media_id",ProbeStore.clean(item?.mediaId) ?: JSONObject.NULL)
                .put("current_title",ProbeStore.clean(metadata.title?.toString()) ?: JSONObject.NULL)
                .put("session_extras",SessionIdentity.extras(browser.sessionExtras))
                .put("token_extras",SessionIdentity.extras(browser.connectedToken?.extras))
                .put("available_commands",commands).put("commands_sent",0).put("exact_track_id_verified",false))
            ProbeStore.put(context,"public_media",JSONObject().put("observed_at_ms",System.currentTimeMillis()).put("sessions",JSONArray().put(session)))
            inspectIdentity(browser)
        } catch (error: RuntimeException) { event("media3","metadata_unavailable",error.javaClass.simpleName) }
    }
    fun stop() {
        generation++
        handler.removeCallbacksAndMessages(null)
        identityFuture?.cancel(false);identityFuture=null;identityKey=null;identityQueries=0
        ProbeStore.put(context,"track_identity",JSONObject())
        ProbeStore.put(context,"session_identity",JSONObject())
        ProbeStore.put(context,"catalog_match",JSONObject())
        tickets.clear();retries.clear();polling=false
        futures.values.forEach { MediaController.releaseFuture(it) }; futures.clear()
        browsers.clear()
    }
}
