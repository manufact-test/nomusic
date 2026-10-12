package pro.celikom.nativeprobe

import android.content.Context
import android.media.MediaMetadata
import android.media.audiofx.AudioEffect
import android.content.Intent
import android.net.Uri
import android.os.Build
import org.json.JSONArray
import org.json.JSONObject

object ProbeStore {
    const val YANDEX = "ru.yandex.music"
    private fun prefs(c: Context) = c.getSharedPreferences("native_probe", Context.MODE_PRIVATE)
    @Synchronized fun put(c: Context, key: String, value: JSONObject) {
        prefs(c).edit().putString(key, value.toString()).apply()
    }
    @Synchronized fun event(c: Context, event: JSONObject) {
        event.put("observed_at_ms", System.currentTimeMillis())
        val all = JSONArray(prefs(c).getString("events", "[]"))
        if (all.length() > 0) {
            val previous = all.getJSONObject(all.length() - 1)
            if (previous.optString("action") == event.optString("action") &&
                previous.optInt("session_id") == event.optInt("session_id") &&
                previous.optBoolean("verified_panel_caller") == event.optBoolean("verified_panel_caller") &&
                event.getLong("observed_at_ms") - previous.optLong("observed_at_ms") < 250) return
        }
        val next = JSONArray()
        for (i in maxOf(0, all.length() - 29) until all.length()) next.put(all.get(i))
        next.put(event)
        prefs(c).edit().putString("events", next.toString()).apply()
    }
    fun clean(value: String?): String? = value?.take(240)?.replace(Regex("[\\p{Cntrl}]"), " ")
    // Only whitelisted metadata. Never dump notification text, Bundle extras, artwork or URL credentials.
    fun metadata(m: MediaMetadata?): JSONObject {
        val result = JSONObject().put("present", m != null).put("exact_track_id_verified", false)
        if (m == null) return result
        for (key in listOf(MediaMetadata.METADATA_KEY_TITLE, MediaMetadata.METADATA_KEY_ARTIST,
            MediaMetadata.METADATA_KEY_MEDIA_ID)) clean(m.getString(key))?.let { result.put(key, it) }
        for (key in listOf(MediaMetadata.METADATA_KEY_MEDIA_URI)) {
            val uri = m.getString(key)?.let { Uri.parse(it) }
            if (uri != null) result.put(key, clean("${uri.scheme ?: ""}://${uri.host ?: ""}${uri.path ?: ""}"))
        }
        result.put("metadata_keys", JSONArray(m.keySet().sorted().take(32).map { clean(it)?.take(80) }))
        result.put("duration_ms", m.getLong(MediaMetadata.METADATA_KEY_DURATION))
        return result
    }
    fun effectEvent(intent: Intent, caller: String?): JSONObject = JSONObject()
        .put("action", clean(intent.action))
        .put("claimed_package", clean(intent.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME)))
        .put("session_id", intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, -1))
        .put("verified_panel_caller", caller == YANDEX)
        .put("caller_package", clean(caller) ?: JSONObject.NULL)
        .put("effect_applied", false)
    fun numericCandidates(bundle: android.os.Bundle?): JSONObject {
        val result = JSONObject()
        if (bundle == null) return result
        for (key in listOf("trackId", "track_id", "mediaId", "media_id", "yandex_track_id")) {
            @Suppress("DEPRECATION")
            val value = try { bundle.get(key) } catch (_: RuntimeException) { null }
            val text = when (value) { is String -> value; is Long -> value.toString(); is Int -> value.toString(); else -> null }
            if (text != null && Regex("[1-9][0-9]{0,23}").matches(text)) result.put(key, text)
        }
        return result
    }
    fun keys(bundle: android.os.Bundle?): JSONArray = JSONArray().apply {
        try { bundle?.keySet()?.sorted()?.take(32)?.forEach { put(clean(it)?.take(80)) } }
        catch (_: RuntimeException) { }
    }
    @Synchronized fun media(c: Context, value: JSONObject) {
        val pref = prefs(c)
        val previous = JSONObject(pref.getString("media", "{}"))
        val sessions = value.optJSONArray("sessions")
        if (previous.optJSONArray("sessions")?.toString() != sessions?.toString()) {
            val history = JSONArray(pref.getString("media_history", "[]")); val next = JSONArray()
            for (i in maxOf(0, history.length() - 19) until history.length()) next.put(history.get(i))
            next.put(value); pref.edit().putString("media_history", next.toString()).apply()
        }
        put(c, "media", value)
    }
    fun enabled(c: Context): Boolean = prefs(c).getBoolean("enabled", true)
    fun setEnabled(c: Context, enabled: Boolean) { prefs(c).edit().putBoolean("enabled", enabled).apply() }
    fun clear(c: Context) { prefs(c).edit().remove("events").remove("media").remove("media_history").remove("shared_track").remove("public_media").remove("public_browser").remove("attenuation_test").apply() }
    fun acceptSharedLink(c: Context, input: String?): Boolean {
        if (input == null || input.length > 2048) return false
        val raw = Regex("https://[^\\s]+").find(input)?.value ?: return false
        val uri = Uri.parse(raw)
        if (uri.host !in listOf("music.yandex.ru", "music.yandex.com") || uri.userInfo != null || uri.port != -1) return false
        if (!Regex("/album/[1-9][0-9]*/track/[1-9][0-9]{0,23}").matches(uri.path ?: "")) return false
        val id = uri.pathSegments.lastOrNull() ?: return false
        put(c, "shared_track", JSONObject().put("track_id", id).put("source", "user_shared_link")
            .put("observed_at_ms", System.currentTimeMillis()).put("current_track_verified", false))
        return true
    }
    fun report(c: Context): JSONObject {
        val version = try { c.packageManager.getPackageInfo(YANDEX, 0).versionName ?: "unknown" }
            catch (_: android.content.pm.PackageManager.NameNotFoundException) { "not_found" }
        return JSONObject().put("schema", 1).put("probe_version", "0.3.7-probe")
            .put("generated_at_ms", System.currentTimeMillis()).put("manufacturer", Build.MANUFACTURER)
            .put("model", Build.MODEL).put("android_release", Build.VERSION.RELEASE).put("api", Build.VERSION.SDK_INT)
            .put("yandex_version", version).put("observation_enabled", enabled(c))
            .put("listener", if (BuildConfig.PANEL_ONLY) JSONObject().put("connected", false).put("available", false) else JSONObject(prefs(c).getString("listener", "{}")))
            .put("probe_mode", if (BuildConfig.PANEL_ONLY) "audio_session_only" else "media_session")
            .put("automatic_track_observation", !BuildConfig.PANEL_ONLY)
            .put("public_browser", JSONObject(prefs(c).getString("public_browser", "{}")))
            .put("attenuation_test", JSONObject(prefs(c).getString("attenuation_test", "{}")))
            .put("shared_track", JSONObject(prefs(c).getString("shared_track", "{}")))
            .put("media", if (BuildConfig.PANEL_ONLY) JSONObject(prefs(c).getString("public_media", "{}")) else JSONObject(prefs(c).getString("media", "{}")))
            .put("media_history", if (BuildConfig.PANEL_ONLY) JSONArray() else JSONArray(prefs(c).getString("media_history", "[]")))
            .put("events", JSONArray(prefs(c).getString("events", "[]")))
            .put("yandex_replacement_tested", false).put("physical_routes_tested", false)
    }
}
