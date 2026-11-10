package pro.celikom.ownedplayer;

import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.content.SharedPreferences;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * SINGLE player and single native playback clock for every approved CELIKOM track.
 * Never touches the installed Yandex player, token, process or audio output.
 */
public final class OwnedPlaybackService extends MediaSessionService {
    public static final String PLAY="pro.celikom.ownedplayer.PLAY";
    public static final String NEXT="pro.celikom.ownedplayer.NEXT";
    public static final String TOGGLE="pro.celikom.ownedplayer.TOGGLE";
    public static final String SEEK_BACK="pro.celikom.ownedplayer.SEEK_BACK";
    public static final String SEEK_FORWARD="pro.celikom.ownedplayer.SEEK_FORWARD";
    public static final String STOP="pro.celikom.ownedplayer.STOP";
    public static final String EXTRA_TRACK="track_id";

    private final Handler main=new Handler(Looper.getMainLooper());
    private final ExecutorService jobs=Executors.newSingleThreadExecutor();
    private final OwnedQueueFence generation=new OwnedQueueFence();
    private ExoPlayer player;
    private MediaSession session;
    private OwnedApiClient api;
    private OwnedCatalogue catalogue;
    private OwnedCatalogue.Track active;
    private OwnedAudioGrant grant;
    private long confirmedAtMs,accountAtPlay;
    private boolean checking;

    private void status(String value){
        getSharedPreferences("owned-playback",MODE_PRIVATE)
                .edit().putString("state",value).apply();
    }

    @Override public void onCreate(){
        super.onCreate();
        api=OwnedApiClient.get(this);
        player=new ExoPlayer.Builder(this).build();
        session=new MediaSession.Builder(this,player).build();
        player.addListener(new Player.Listener(){
            @Override public void onPlaybackStateChanged(int state){
                if(state==Player.STATE_ENDED && grant!=null)next();
            }
            @Override public void onPlayerError(androidx.media3.common.PlaybackException err){
                stopInternal("Ошибка воспроизведения: доступ закрыт");
            }
        });
        status("Готово. Войдите в CELIKOM и выберите трек.");
        main.postDelayed(leaseCheck,5000);
    }

    @Override public MediaSession onGetSession(MediaSession.ControllerInfo info){
        return session;
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent!=null){
            String action=intent.getAction();
            if(PLAY.equals(action)){
                String id=intent.getStringExtra(EXTRA_TRACK);
                if(OwnedPlaybackContract.validTrackId(id))start(id);
                else stopInternal("Некорректный трек");
            }else if(NEXT.equals(action)){
                next();
            }else if(TOGGLE.equals(action)){
                if(grant!=null && player.getPlaybackState()!=Player.STATE_IDLE){
                    if(player.isPlaying())player.pause();else player.play();
                    status(player.isPlaying()?"Играет":"Пауза");
                }
            }else if(SEEK_BACK.equals(action)){
                if(grant!=null)player.seekTo(Math.max(0,player.getCurrentPosition()-15000));
            }else if(SEEK_FORWARD.equals(action)){
                if(grant!=null){
                    long duration=player.getDuration();
                    long target=player.getCurrentPosition()+15000;
                    if(duration>0)target=Math.min(duration-1,target);
                    player.seekTo(target);
                }
            }else if(STOP.equals(action)){
                stopInternal("Остановлено");
            }
        }
        return super.onStartCommand(intent,flags,startId);
    }

    private void start(String trackId){
        long serial=generation.begin(trackId);
        long initialAccount=api.accountEpoch();
        active=null;grant=null;confirmedAtMs=0;
        player.stop();player.clearMediaItems();
        status("Проверяем подписку и разрешённую дорожку…");
        jobs.execute(()->{
            try{
                api.healthy();
                if(!api.entitled())throw new Exception("no_subscription");
                long accessTime=SystemClock.elapsedRealtime();
                if(api.accountEpoch()!=initialAccount)
                    throw new Exception("account_changed");
                OwnedCatalogue currentCatalog=catalogue;
                if(currentCatalog==null){
                    currentCatalog=api.catalogue();
                }
                int index=currentCatalog.indexOf(trackId);
                if(index<0)throw new Exception("track_not_in_approved_catalogue");
                OwnedAudioGrant received=api.grant(trackId);
                if(received.expiresAtMs-System.currentTimeMillis()<5000)
                    throw new Exception("signed_audio_expired");
                OwnedCatalogue finalCatalog=currentCatalog;
                OwnedCatalogue.Track selected=currentCatalog.get(index);
                main.post(()->{
                    if(!generation.current(serial,trackId) ||
                            api.accountEpoch()!=initialAccount)return;
                    catalogue=finalCatalog;
                    active=selected;grant=received;
                    accountAtPlay=initialAccount;
                    confirmedAtMs=accessTime;
                    if(!OwnedPlaybackContract.activeAccess(true,
                            confirmedAtMs,SystemClock.elapsedRealtime(),15000)){
                        stopInternal("Доступ устарел");
                        return;
                    }
                    MediaMetadata metadata=new MediaMetadata.Builder()
                            .setTitle(selected.title).setArtist(selected.artist).build();
                    MediaItem item=new MediaItem.Builder()
                            .setUri(received.url)
                            .setMediaId(selected.id)
                            .setMediaMetadata(metadata).build();
                    player.setMediaItem(item);
                    player.prepare();
                    player.play();
                    status("Играет: "+selected.title+" — "+selected.artist);
                });
            }catch(Exception failure){
                main.post(()->{
                    if(generation.current(serial,trackId))
                        stopInternal("Нет разрешённого доступа или аудио для трека");
                });
            }
        });
    }

    private void next(){
        if(active==null || catalogue==null){
            stopInternal("Очередь недоступна");
            return;
        }
        int index=catalogue.indexOf(active.id);
        if(index<0 || index+1>=catalogue.count()){
            stopInternal("Конец очереди доступных версий");
            return;
        }
        start(catalogue.get(index+1).id);
    }

    private final Runnable leaseCheck=new Runnable(){
        @Override public void run(){
            if(grant!=null && active!=null){
                long elapsed=SystemClock.elapsedRealtime();
                if(api.accountEpoch()!=accountAtPlay ||
                        !OwnedPlaybackContract.activeAccess(true,confirmedAtMs,elapsed,15000) ||
                        grant.expiresAtMs-System.currentTimeMillis()<=5000){
                    stopInternal("Доступ закончился или не подтверждён");
                }else if(!checking){
                    checking=true;
                    long captured=accountAtPlay;
                    String id=active.id;
                    jobs.execute(()->{
                        boolean allowed=false;
                        try{allowed=api.entitled();}catch(Exception ignored){}
                        boolean grantAllowed=allowed;
                        long verified=SystemClock.elapsedRealtime();
                        main.post(()->{
                            checking=false;
                            if(grant==null||active==null||!active.id.equals(id))return;
                            if(api.accountEpoch()!=captured||!grantAllowed){
                                stopInternal("Сервер не подтвердил доступ");
                                return;
                            }
                            confirmedAtMs=verified;
                        });
                    });
                }
            }
            main.postDelayed(this,5000);
        }
    };

    private void stopInternal(String message){
        generation.clear();
        active=null;grant=null;confirmedAtMs=0;
        player.stop();player.clearMediaItems();
        status(message);
    }

    @Override public void onDestroy(){
        main.removeCallbacks(leaseCheck);
        stopInternal("Приложение закрыто");
        jobs.shutdownNow();
        if(session!=null){session.release();session=null;}
        if(player!=null){player.release();player=null;}
        super.onDestroy();
    }
}
