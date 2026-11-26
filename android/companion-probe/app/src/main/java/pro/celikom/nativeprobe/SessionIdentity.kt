package pro.celikom.nativeprobe

import android.net.Uri
import android.os.Bundle
import org.json.JSONArray
import org.json.JSONObject

/** Bounded evidence from public session extras. Never serializes arbitrary Bundle values. */
object SessionIdentity {
    fun extras(bundle: Bundle?): JSONObject {
        val result=JSONObject().put("keys",ProbeStore.keys(bundle)).put("exact_track_id_verified",false)
        val numbers=JSONObject();val links=JSONObject();val nested=JSONObject()
        if (bundle!=null) for (key in bundle.keySet().sorted().take(40)) {
            val suffix=key.substringAfterLast('.').replace("_","").lowercase()
            @Suppress("DEPRECATION")
            val value=try { bundle.get(key) } catch (_: RuntimeException) { null }
            val safeKey=ProbeStore.clean(key)?.take(80) ?: continue
            if (suffix in listOf("trackid","yandextrackid","servicetrackid")) {
                val id=when(value) { is String -> value;is Int,is Long -> value.toString();else -> null }
                if (id!=null && Regex("[1-9][0-9]{0,23}").matches(id)) numbers.put(safeKey,id)
            }
            if (suffix in listOf("trackuri","trackurl","mediauri","mediaurl","url","uri","deeplink")) {
                val uri=when(value) { is Uri -> value;is String -> try { Uri.parse(value.take(2048)) } catch (_: RuntimeException) { null };else -> null }
                val evidence=MediaIdentity.uri(uri)
                if (evidence.has("track_id_candidate")) links.put(safeKey,evidence)
            }
            if (value is Bundle && suffix in listOf("track","currenttrack","metadata","mediaitem")) {
                nested.put(safeKey,JSONObject().put("keys",ProbeStore.keys(value)).put("numeric_candidates",ProbeStore.numericCandidates(value)))
            }
        }
        return result.put("track_id_candidates",numbers).put("public_track_links",links).put("nested_evidence",nested)
    }
}
