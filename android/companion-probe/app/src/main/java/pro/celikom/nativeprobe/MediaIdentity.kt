package pro.celikom.nativeprobe

import android.net.Uri
import androidx.media3.common.MediaItem
import org.json.JSONObject

/** Evidence only. Arbitrary stream/local URI paths and query credentials are never recorded. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
object MediaIdentity {
    fun uri(uri: Uri?): JSONObject {
        val result=JSONObject().put("present",uri!=null)
        if (uri==null) return result
        result.put("scheme",ProbeStore.clean(uri.scheme)).put("host",ProbeStore.clean(uri.host))
        if (uri.scheme in listOf("https","http") && uri.host in listOf("music.yandex.ru","music.yandex.com") && uri.userInfo==null &&
            Regex("/album/[1-9][0-9]*/track/[1-9][0-9]*").matches(uri.path ?: "")) {
            result.put("public_track_url","https://${uri.host}${uri.path}")
                .put("track_id_candidate",uri.lastPathSegment)
        }
        return result
    }
    fun item(item: MediaItem?): JSONObject {
        val metadata=item?.mediaMetadata
        return JSONObject().put("present",item!=null).put("media_id",ProbeStore.clean(item?.mediaId) ?: JSONObject.NULL)
            .put("title",ProbeStore.clean(metadata?.title?.toString()) ?: JSONObject.NULL)
            .put("artist",ProbeStore.clean(metadata?.artist?.toString()) ?: JSONObject.NULL)
            .put("album",ProbeStore.clean(metadata?.albumTitle?.toString()) ?: JSONObject.NULL)
            .put("request_uri",uri(item?.requestMetadata?.mediaUri))
            .put("local_uri",uri(item?.localConfiguration?.uri))
            .put("request_numeric_candidates",ProbeStore.numericCandidates(item?.requestMetadata?.extras))
            .put("request_extra_keys",ProbeStore.keys(item?.requestMetadata?.extras))
            .put("metadata_numeric_candidates",ProbeStore.numericCandidates(metadata?.extras))
            .put("metadata_extra_keys",ProbeStore.keys(metadata?.extras))
            .put("exact_track_id_verified",false)
    }
}
