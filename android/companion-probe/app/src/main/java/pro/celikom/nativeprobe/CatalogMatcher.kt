package pro.celikom.nativeprobe

import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/** Metadata evidence inside an incomplete external universe. Never verifies external Track ID. */
object CatalogMatcher {
    fun normalize(value: String): String = Normalizer.normalize(value,Normalizer.Form.NFKC).lowercase(Locale.ROOT)
        .replace('ё','е').trim().replace(Regex("\\s+")," ")
    fun artists(value: String): List<String> = value.split(Regex("[,;]|\\s+(?:feat\\.?|ft\\.?|featuring|&)\\s+",RegexOption.IGNORE_CASE))
        .map { normalize(it) }.filter { it.isNotEmpty() }.distinct().sorted()
    fun match(snapshot: JSONObject, title: String, artist: String, album: String, duration: Long, now: Long): JSONObject {
        val rows=snapshot.getJSONArray("tracks")
        require(snapshot.optInt("schema")==1 && rows.length()<=5000)
        val result=JSONObject().put("mode","metadata_diagnostic_only").put("exact_track_id_verified",false)
            .put("replacement_started",false).put("catalog_total",snapshot.optInt("total_tracks",rows.length()))
            .put("catalog_generated_at_ms",snapshot.optLong("generated_at_ms")).put("catalog_complete",snapshot.optBoolean("complete",false))
            .put("observed_at_ms",now)
        val currentTitle=normalize(title);val currentArtists=artists(artist);val currentAlbum=normalize(album)
        if (currentTitle.isEmpty() || currentArtists.isEmpty() || currentAlbum.isEmpty() || duration<=0)
            return result.put("status","insufficient_current_metadata").put("candidates",JSONArray())
        val candidates=mutableListOf<JSONObject>()
        var strong=0;var winner: String?=null;var incompleteRows=0
        for (i in 0 until rows.length()) {
            val row=rows.getJSONObject(i)
            if (listOf("title","artist","album").any { row.optString(it).isBlank() } || row.optLong("duration_ms")<=0) incompleteRows++
            val titleMatch=normalize(row.optString("title"))==currentTitle
            val artistMatch=artists(row.optString("artist"))==currentArtists
            if (!titleMatch && !artistMatch) continue
            val albumMatch=normalize(row.optString("album"))==currentAlbum
            val catalogDuration=row.optLong("duration_ms")
            val delta=if (catalogDuration>0) kotlin.math.abs(catalogDuration-duration) else Long.MAX_VALUE
            val durationMatch=delta<=1500
            val reasons=JSONArray()
            if (!titleMatch) reasons.put("title_mismatch")
            if (!artistMatch) reasons.put("artists_mismatch")
            if (!albumMatch) reasons.put(if (row.optString("album").isBlank()) "catalog_album_missing" else "album_mismatch")
            if (!durationMatch) reasons.put(if (catalogDuration<=0) "catalog_duration_missing" else "duration_mismatch")
            val all=titleMatch && artistMatch && albumMatch && durationMatch
            val id=row.getString("track_id")
            require(Regex("[1-9][0-9]{0,23}").matches(id))
            if (all) { strong++;winner=id }
            candidates.add(JSONObject().put("track_id",id).put("title",row.optString("title")).put("artist",row.optString("artist"))
                .put("album",row.optString("album")).put("duration_ms",catalogDuration).put("replacement_available",row.optBoolean("replacement_available"))
                .put("title_match",titleMatch).put("artists_match",artistMatch).put("album_match",albumMatch).put("duration_match",durationMatch)
                .put("duration_delta_ms",if (catalogDuration>0) delta else JSONObject.NULL).put("matching_fields",listOf(titleMatch,artistMatch,albumMatch,durationMatch).count { it })
                .put("rejection_reasons",reasons).put("all_fields_match",all))
        }
        val age=now-snapshot.optLong("generated_at_ms")
        val status=when {
            !snapshot.optBoolean("complete",false) -> "catalog_incomplete"
            age<0 || age>7*86400000L -> "catalog_snapshot_stale"
            strong>1 -> "ambiguous_metadata_candidates"
            strong==1 -> "unique_metadata_candidate_unverified"
            candidates.isNotEmpty() -> "no_complete_metadata_match"
            incompleteRows>0 -> "catalog_metadata_incomplete"
            else -> "no_catalog_candidate"
        }
        result.put("status",status).put("catalog_rows_missing_metadata",incompleteRows).put("complete_match_count",strong).put("candidate_count",candidates.size)
            .put("candidates",JSONArray(candidates.sortedByDescending { it.getInt("matching_fields") }.take(10)))
        if (status=="unique_metadata_candidate_unverified") result.put("candidate_track_id",winner)
        return result
    }
}
