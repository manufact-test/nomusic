package pro.celikom.spike

import android.media.AudioAttributes
import android.media.MediaPlayer
import kotlinx.coroutines.*
import org.json.JSONObject
import kotlin.math.abs

/** Native replacement follows exact WebView master; guard expires without native heartbeats. */
class MobilePlayback(private val account:PlaybackAccount,private val surface:PlaybackSurface,private val state:(String)->Unit,
    private val loadAudio:(MediaPlayer,AudioGrant)->Unit={p,g->p.setDataSource(surface.context,android.net.Uri.parse(g.url),mapOf("android-allow-cross-domain-redirect" to "0"))}) {
    private val scope=CoroutineScope(SupervisorJob()+Dispatchers.Main.immediate)
    private var player:MediaPlayer?=null
    private var epoch=0L
    private var enabled=false
    private var preparing=false
    private var polling=false
    private var pollAt=0L
    private var boundTrack=""
    private var boundMedia=""
    private var token=""
    private var expiry=0L
    private var accessUntil=0L
    private var nextAttempt=0L
    private var lastSeek=0L
    private var latest:JSONObject?=null
    init { scope.launch { while(isActive){delay(250);tick()} } }
    fun start(){stop();enabled=true;state("Проверяем доступ и текущий трек…")}
    fun stop(message:String="Звучит оригинал") {
        enabled=false;epoch++;preparing=false;polling=false;latest=null
        val old=token;token="";boundTrack="";boundMedia="";expiry=0;accessUntil=0;nextAttempt=0
        player?.let { runCatching{it.setVolume(0f,0f)};runCatching{it.release()} };player=null
        surface.release(old.ifEmpty{null});state(message)
    }
    fun guardReleased(released:String){
        if(released!=token||token.isEmpty())return
        val resume=enabled
        stop("Плеер изменился — звучит оригинал")
        enabled=resume
    }
    private fun fail(message:String){stop(message)}
    private fun tick(){
        if(!enabled)return
        if(polling){if(System.currentTimeMillis()-pollAt>1200)fail("Нет ответа плеера — звучит оригинал");return}
        polling=true;pollAt=System.currentTimeMillis();val generation=epoch
        surface.snapshot { s ->
            if(generation!=epoch)return@snapshot
            polling=false
            if(!enabled)return@snapshot
            latest=s
            if(s==null||!s.optBoolean("valid")) { if(player!=null||preparing)fail("Плеер изменился — возвращён оригинал") else state("Включите трек в Яндекс Музыке");return@snapshot }
            if(s.optBoolean("paused")||s.optBoolean("seeking")) {
                if(player!=null||preparing){stop("Пауза или перемотка — звучит оригинал");enabled=true}
                return@snapshot
            }
            val track=s.optString("trackId");val media=s.optString("mediaId")
            if(!track.matches(Regex("[1-9][0-9]{0,23}")))return@snapshot
            if(player!=null||preparing) {
                if(track!=boundTrack||media!=boundMedia){stop("Проверяем новый трек…");enabled=true;return@snapshot}
            }
            val p=player
            if(p==null) {if(!preparing&&System.currentTimeMillis()>=nextAttempt)resolve(s);return@snapshot}
            if(preparing)return@snapshot
            if(!s.optBoolean("guarded")){fail("Связь с плеером восстановлена: звучит оригинал");return@snapshot}
            if(System.currentTimeMillis()>=expiry||System.currentTimeMillis()>=accessUntil){fail("Нужно повторно проверить доступ. Звучит оригинал");return@snapshot}
            runCatching {
                val target=(s.getDouble("position")*1000).toInt().coerceAtLeast(0)
                if(target>=p.duration)error("Конец подмены")
                val now=System.currentTimeMillis()
                if(abs(p.currentPosition-target)>350&&now-lastSeek>800){lastSeek=now;p.seekTo(target.toLong(),MediaPlayer.SEEK_CLOSEST)}
                val rate=s.optDouble("rate",1.0).toFloat();require(rate in 0.5f..2f)
                if(abs(p.playbackParams.speed-rate)>0.01f)p.playbackParams=p.playbackParams.setSpeed(rate)
                val volume=if(s.optBoolean("muted"))0f else s.optDouble("volume",1.0).toFloat().coerceIn(0f,1f)
                p.setVolume(volume,volume)
            }.onFailure{fail("Ошибка подмены — возвращён оригинал")}
        }
    }
    private fun resolve(s:JSONObject){
        preparing=true;val generation=epoch
        boundTrack=s.getString("trackId");boundMedia=s.getString("mediaId")
        val requestedTrack=boundTrack
        state("Загружаем подмену…")
        scope.launch {
            try {
                val grant=withContext(Dispatchers.IO){
                    val config=account.request("/api/v1/config",authenticated=false)
                    require(!config.optBoolean("maintenance")&&config.getJSONObject("features").optBoolean("replacements")){"Подмена временно приостановлена"}
                    val entitlement=account.entitlement(true)
                    require(entitlement.optBoolean("allowed")){if(entitlement.optString("reason")=="service_incident") "Подмена временно приостановлена" else "Нет действующего доступа"}
                    AudioGrant.parse(account.request("/api/v1/resolve?service=yandex&track_id=$requestedTrack"))
                }
                if(generation!=epoch||!enabled)return@launch
                if(grant==null){preparing=false;nextAttempt=System.currentTimeMillis()+15000;state("Для этого трека пока нет подмены");return@launch}
                val current=latest
                require(current!=null&&current.optString("trackId")==boundTrack&&current.optString("mediaId")==boundMedia&&!current.optBoolean("paused"))
                val p=MediaPlayer();player=p;token="android:$generation:${System.nanoTime()}"
                expiry=grant.expiresAt;accessUntil=System.currentTimeMillis()+15000
                p.setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
                p.setVolume(0f,0f)
                p.setOnErrorListener{_,_,_->if(player===p)fail("Не удалось воспроизвести подмену — звучит оригинал");true}
                p.setOnCompletionListener{if(player===p)fail("Подмена закончилась — звучит оригинал")}
                p.setOnPreparedListener {
                    if(generation!=epoch||player!==p)return@setOnPreparedListener
                    val target=latest?.optDouble("position",0.0)?.times(1000)?.toLong()?:0L
                    if(target>=p.duration){fail("Подмена короче текущей позиции — звучит оригинал");return@setOnPreparedListener}
                    p.setOnSeekCompleteListener {
                        if(generation!=epoch||player!==p)return@setOnSeekCompleteListener
                        p.setOnSeekCompleteListener(null)
                        runCatching{p.start()}.onFailure{fail("Не удалось начать подмену");return@setOnSeekCompleteListener}
                        surface.engage(boundTrack,boundMedia,token){ok->
                            if(generation!=epoch||player!==p)return@engage
                            if(!ok){fail("Не удалось безопасно управлять оригиналом");return@engage}
                            preparing=false;state("Подмена включена")
                            val v=latest?.let{if(it.optBoolean("muted"))0f else it.optDouble("volume",1.0).toFloat()}?:1f
                            p.setVolume(v.coerceIn(0f,1f),v.coerceIn(0f,1f))
                            refreshAccess(generation)
                        }
                    }
                    p.seekTo(target,MediaPlayer.SEEK_CLOSEST)
                }
                loadAudio(p,grant);p.prepareAsync()
                scope.launch{delay(12000);if(generation==epoch&&preparing)fail("Тайм-аут загрузки — звучит оригинал")}
            }catch(e:Exception){if(generation==epoch)fail(e.message?.takeIf{it.length<120}?:"Сбой связи — звучит оригинал")}
        }
    }
    private fun refreshAccess(generation:Long){scope.launch{
        while(isActive&&enabled&&epoch==generation){
            delay(5000)
            try {
                val allowed=withContext(Dispatchers.IO){
                    val c=account.request("/api/v1/config",authenticated=false)
                    !c.optBoolean("maintenance")&&c.getJSONObject("features").optBoolean("replacements")&&account.entitlement().optBoolean("allowed")
                }
                if(epoch!=generation)return@launch
                if(!allowed){fail("Подмена приостановлена — звучит оригинал");return@launch}
                accessUntil=System.currentTimeMillis()+15000
            }catch(_:Exception){if(epoch==generation)fail("Не удалось проверить доступ — звучит оригинал");return@launch}
        }
    }}
    fun diagnostic():JSONObject=JSONObject().put("enabled",enabled).put("preparing",preparing)
        .put("playing",runCatching{player?.isPlaying?:false}.getOrDefault(false))
        .put("positionMs",runCatching{player?.currentPosition?:0}.getOrDefault(0)).put("trackId",boundTrack)
    fun close(){stop();scope.cancel()}
}
