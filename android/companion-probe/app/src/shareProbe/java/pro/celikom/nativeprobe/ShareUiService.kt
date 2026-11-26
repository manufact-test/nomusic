package pro.celikom.nativeprobe

import android.accessibilityservice.AccessibilityService
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import org.json.JSONArray
import org.json.JSONObject

/** One visible transaction. Never chooses a system recipient, touches clipboard, or runs unarmed. */
class ShareUiService : AccessibilityService() {
    private val handler = Handler(Looper.getMainLooper())
    private var deadline = 0L
    private var step = 0
    private var lastClick = 0L
    private val evidence = JSONArray()
    private var beforeId: String? = null
    private val tick = object : Runnable {
        override fun run() {
            if (deadline == 0L) return
            if (SystemClock.elapsedRealtime() >= deadline) { finish("timeout"); return }
            inspect()
            if (deadline != 0L) handler.postDelayed(this, 350)
        }
    }
    override fun onServiceConnected() { instance = this }
    override fun onDestroy() { finish("service_destroyed"); if (instance === this) instance = null; super.onDestroy() }
    override fun onInterrupt() { finish("interrupted") }
    override fun onAccessibilityEvent(event: AccessibilityEvent?) { /* polling is bounded to the explicitly armed lease */ }
    fun arm(): Boolean {
        finish("cancelled")
        val media = ProbeStore.report(this).optJSONObject("media")
        if (media?.optBoolean("fresh") != true) return false
        beforeId = media.optJSONArray("sessions")?.optJSONObject(0)?.optString("media_id")
        if (beforeId.isNullOrBlank()) return false
        deadline = SystemClock.elapsedRealtime() + 45000
        step = 0; lastClick = 0
        while (evidence.length() > 0) evidence.remove(0)
        ProbeStore.put(this, "share_ui_test", JSONObject())
        ProbeStore.put(this, "share_link_result", JSONObject().put("status", "not_received"))
        record("waiting_for_player")
        handler.post(tick)
        return true
    }
    fun finish(status: String) {
        if (deadline == 0L) return
        deadline = 0L; handler.removeCallbacks(tick); record(status)
    }
    private fun record(status: String) {
        val previous = ProbeStore.report(this).optJSONObject("share_ui_test")
        val value = JSONObject().put("status", status).put("step", step)
            .put("before_media_id", beforeId).put("at_ms", System.currentTimeMillis())
            .put("actions", JSONArray(evidence.toString())).put("exact_track_id_verified", false)
        previous?.optJSONArray("visible_control_ids")?.let { value.put("visible_control_ids", it) }
        if (previous?.has("player_container_present") == true) value.put("player_container_present", previous.optBoolean("player_container_present"))
        ProbeStore.put(this, "share_ui_test", value)
    }
    private fun inspect() {
        val root = rootInActiveWindow ?: return
        try {
            if (root.packageName?.toString() != "ru.yandex.music") return
            val media = ProbeStore.report(this).optJSONObject("media")
            val current = media?.optJSONArray("sessions")?.optJSONObject(0)?.optString("media_id")
            if (media?.optBoolean("fresh") != true || current != beforeId) { finish("player_changed_or_stale"); return }
            if (SystemClock.elapsedRealtime() - lastClick < 1000) return
            val nodes = mutableListOf<AccessibilityNodeInfo>()
            collect(root, nodes)
            try {
                val selected = ShareUiPolicy.choose(nodes.map { ShareUiPolicy.Control(it.packageName?.toString(), it.viewIdResourceName,
                    it.text?.toString(), it.contentDescription?.toString(), it.isVisibleToUser, it.isEnabled,
                    step == 0 && insidePlayer(it)) }, step)
                val candidate = selected?.let { nodes[it] }
                if (candidate != null && click(candidate)) {
                    evidence.put(JSONObject().put("step", step).put("view_id", candidate.viewIdResourceName)
                        .put("at_ms", System.currentTimeMillis()))
                    step++; lastClick = SystemClock.elapsedRealtime(); record(if (step >= 3) "choose_celikom_in_share_menu" else "clicked")
                    if (step >= 3) { finish("choose_celikom_in_share_menu") }
                } else if (step == 0) {
                    val controls = JSONArray()
                    nodes.filter { it.isVisibleToUser && it.isClickable }.take(35).forEach {
                        // Resource identifiers only: no arbitrary text, account names, screen contents or screenshots.
                        controls.put(JSONObject().put("view_id", it.viewIdResourceName).put("class", it.className?.toString()))
                    }
                    val state = ProbeStore.report(this).optJSONObject("share_ui_test") ?: JSONObject()
                    state.put("visible_control_ids", controls).put("player_container_present", nodes.any { it.viewIdResourceName == "ru.yandex.music:id/player_container" })
                    ProbeStore.put(this, "share_ui_test", state)
                }
            } finally { nodes.drop(1).forEach { it.recycle() } }
        } finally { root.recycle() }
    }
    private fun collect(node: AccessibilityNodeInfo, result: MutableList<AccessibilityNodeInfo>, depth: Int = 0) {
        if (result.size >= 180 || depth > 18) { node.recycle(); return }
        result.add(node)
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            if (result.size >= 180) { child.recycle(); break }
            collect(child, result, depth + 1)
        }
    }
    private fun insidePlayer(node: AccessibilityNodeInfo): Boolean {
        var current = node.parent
        repeat(18) {
            val parent = current ?: return false
            val found = parent.viewIdResourceName == "ru.yandex.music:id/player_container"
            current = if (found) null else parent.parent
            parent.recycle()
            if (found) return true
        }
        current?.recycle(); return false
    }
    private fun click(node: AccessibilityNodeInfo): Boolean {
        if (node.isClickable && node.isEnabled) return node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        var current = node.parent
        repeat(3) {
            val parent = current ?: return false
            val clicked = parent.isEnabled && parent.isClickable && parent.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            current = if (clicked) null else parent.parent
            parent.recycle()
            if (clicked) return true
        }
        current?.recycle(); return false
    }
    companion object { var instance: ShareUiService? = null; private set }
}
