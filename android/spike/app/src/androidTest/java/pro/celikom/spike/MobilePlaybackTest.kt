package pro.celikom.spike

import android.content.Context
import android.media.MediaPlayer
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.json.JSONObject
import kotlin.math.abs

/** Production controller with owned native media and an isolated API/surface double. */
@RunWith(AndroidJUnit4::class)
class MobilePlaybackTest {
    private class Account:PlaybackAccount {
        @Volatile var allowed=true
        @Volatile var delayMs=0L
        override fun entitlement(activate:Boolean)=JSONObject().put("allowed",allowed)
        override fun request(path:String,body:JSONObject?,authenticated:Boolean,retry:Boolean):JSONObject {
            if(path.endsWith("config"))return JSONObject().put("maintenance",false).put("features",JSONObject().put("replacements",true))
            Thread.sleep(delayMs)
            val expiry=System.currentTimeMillis()/1000+600
            return JSONObject().put("found",true).put("replacement_id",1).put("duration_ms",8000).put("version",1).put("expires_at",expiry)
                .put("audio_url",MobileAccount.ORIGIN+"/api/v1/audio/1?token="+"a".repeat(64)+"&expires=$expiry")
        }
    }
    private class Surface(override val context:Context,val original:MediaPlayer):PlaybackSurface {
        var guarded=false;var track="144530503";var valid=true;var lease="";var engagements=0
        override fun snapshot(callback:(JSONObject?)->Unit){callback(JSONObject().put("valid",valid).put("trackId",track).put("mediaId","owned")
            .put("position",original.currentPosition/1000.0).put("duration",8).put("paused",!original.isPlaying)
            .put("seeking",false).put("guarded",guarded).put("muted",false).put("volume",0.5).put("rate",1))}
        override fun engage(track:String,media:String,token:String,callback:(Boolean)->Unit){
            val ok=track==this.track&&media=="owned"&&valid&&original.isPlaying
            if(ok){guarded=true;lease=token;engagements++;original.setVolume(0f,0f)};callback(ok)
        }
        override fun release(token:String?){if(token!=null&&token!=lease)return;guarded=false;lease="";original.setVolume(0.5f,0.5f)}
    }
    @Test fun productionControllerSynchronizesAndReturnsOriginalOnPauseRevokeAndStaleResolve(){
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            lateinit var original:MediaPlayer;lateinit var surface:Surface;lateinit var controller:MobilePlayback
            val account=Account()
            scenario.onActivity { activity ->
                original=MediaPlayer.create(activity,R.raw.original);original.isLooping=true;original.start()
                surface=Surface(activity,original)
                controller=MobilePlayback(account,surface,{}){p,_->
                    activity.resources.openRawResourceFd(R.raw.alternate).use { p.setDataSource(it.fileDescriptor,it.startOffset,it.length) }
                }
                controller.start()
            }
            fun await(timeout:Long=6000,condition:()->Boolean){
                val until=System.currentTimeMillis()+timeout
                while(System.currentTimeMillis()<until){var ok=false;scenario.onActivity{ok=condition()};if(ok)return;Thread.sleep(100)}
                fail("Controller did not reach expected state")
            }
            try {
                await {surface.guarded&&controller.diagnostic().optBoolean("playing")}
                scenario.onActivity{assertTrue(abs(controller.diagnostic().getInt("positionMs")-original.currentPosition)<500);original.pause()}
                await { !surface.guarded&&!controller.diagnostic().optBoolean("playing") }
                scenario.onActivity{original.start()}
                await {surface.guarded}
                account.allowed=false
                await(8000){!surface.guarded&&!controller.diagnostic().optBoolean("enabled")}
                scenario.onActivity{assertFalse(controller.diagnostic().optBoolean("playing"));account.allowed=true;account.delayMs=700;controller.start()}
                Thread.sleep(400)
                scenario.onActivity{controller.stop();assertFalse(surface.guarded)}
                Thread.sleep(1300)
                scenario.onActivity{assertFalse(surface.guarded);assertFalse(controller.diagnostic().optBoolean("playing"))}
                scenario.onActivity{surface.valid=false;controller.start()}
                Thread.sleep(500)
                scenario.onActivity{assertFalse(surface.guarded);assertFalse(controller.diagnostic().optBoolean("playing"))}
            }finally{scenario.onActivity{controller.close();original.release()}}
        }
    }
}
