package pro.celikom.spike
import android.content.Context
import org.json.JSONObject

interface PlaybackAccount {
    fun request(path:String,body:JSONObject?=null,authenticated:Boolean=true,retry:Boolean=true):JSONObject
    fun entitlement(activate:Boolean=false):JSONObject
}
interface PlaybackSurface {
    val context:Context
    fun snapshot(callback:(JSONObject?)->Unit)
    fun engage(track:String,media:String,token:String,callback:(Boolean)->Unit)
    fun release(token:String?=null)
}
