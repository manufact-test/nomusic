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
    fun enabled(c: Context): Boolean = prefs(c).getBoolean("enabled", true)
    fun setEnabled(c: Context, enabled: Boolean) { prefs(c).edit().putBoolean("enabled", enabled).apply() }
    fun clear(c: Context) { prefs(c).edit().remove("events").remove("media").apply() }
    fun report(c: Context): JSONObject {
        val version = try { c.packageManager.getPackageInfo(YANDEX, 0).versionName ?: "unknown" }
            catch (_: android.content.pm.PackageManager.NameNotFoundException) { "not_found" }
        return JSONObject().put("schema", 1).put("probe_version", "0.3.0-probe")
            .put("generated_at_ms", System.currentTimeMillis()).put("manufacturer", Build.MANUFACTURER)
            .put("model", Build.MODEL).put("android_release", Build.VERSION.RELEASE).put("api", Build.VERSION.SDK_INT)
            .put("yandex_version", version).put("observation_enabled", enabled(c))
            .put("listener", JSONObject(prefs(c).getString("listener", "{}")))
            .put("media", JSONObject(prefs(c).getString("media", "{}")))
            .put("events", JSONArray(prefs(c).getString("events", "[]")))
            .put("yandex_replacement_tested", false).put("physical_routes_tested", false)
    }
}
