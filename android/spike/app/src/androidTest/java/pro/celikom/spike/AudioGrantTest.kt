package pro.celikom.spike
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.json.JSONObject
@RunWith(AndroidJUnit4::class)
class AudioGrantTest {
    @Test fun signedAudioCannotEscapeApiOrAcceptDuplicateQueryKeys(){
        val now=System.currentTimeMillis();val expiry=now/1000+600
        val url=MobileAccount.ORIGIN+"/api/v1/audio/1?token="+"a".repeat(64)+"&expires=$expiry&sid=1"
        fun response(u:String)=JSONObject().put("found",true).put("replacement_id",1).put("duration_ms",10000).put("expires_at",expiry).put("version",1).put("audio_url",u)
        assertNotNull(AudioGrant.parse(response(url),now))
        for(u in listOf(url.replace("https:","http:"),url.replace("/audio/1","/audio/2"),url+"&sid=2",url.replace("darkred-camel-588676.hostingersite.com","evil.test"),url+"#fragment")) {
            assertTrue(u,runCatching{AudioGrant.parse(response(u),now)}.isFailure)
        }
        assertEquals("Доступ: навсегда",MainActivity.formatAccess(JSONObject().put("allowed",true).put("valid_until",JSONObject.NULL)))
        assertTrue(MainActivity.formatAccess(JSONObject().put("allowed",true).put("valid_until","2026-10-11T20:00:00Z")).contains("23:00"))
    }
}
