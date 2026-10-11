package pro.celikom.spike

import java.net.URI
import java.net.URLDecoder
import org.json.JSONObject

data class AudioGrant(val url:String,val durationMs:Int,val expiresAt:Long) {
    companion object {
        fun parse(j:JSONObject,now:Long=System.currentTimeMillis()):AudioGrant? {
            if(j.optBoolean("found")==false) return null
            val id=j.getLong("replacement_id"); require(id>0)
            val duration=j.getInt("duration_ms"); require(duration in 1..86400000)
            val expiry=j.getLong("expires_at")*1000
            require(expiry>now+1000 && expiry<=now+1800000)
            require(j.getInt("version")>0)
            val u=URI(MobileAccount.ORIGIN).resolve(j.getString("audio_url"))
            require(u.scheme=="https" && u.host==URI(MobileAccount.ORIGIN).host && (u.port==-1||u.port==443) && u.userInfo==null && u.fragment==null)
            require(u.path=="/api/v1/audio/$id")
            val parts=(u.rawQuery?:"").split("&").map { it.split("=",limit=2) }
            require(parts.all { it.size==2 })
            val pairs=parts.map { URLDecoder.decode(it[0],"UTF-8") to URLDecoder.decode(it[1],"UTF-8") }
            require(pairs.map{it.first}.toSet().size==pairs.size)
            val q=pairs.toMap(); require(q.keys==setOf("token","expires")||q.keys==setOf("token","expires","sid"))
            require(q["token"]?.matches(Regex("[0-9a-f]{64}"))==true && q["expires"]==(expiry/1000).toString())
            require(q["sid"]==null||q["sid"]!!.matches(Regex("[1-9][0-9]{0,17}")))
            return AudioGrant(u.toString(),duration,expiry)
        }
    }
}
