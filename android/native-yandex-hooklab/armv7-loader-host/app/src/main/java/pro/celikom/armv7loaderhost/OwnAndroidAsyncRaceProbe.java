package pro.celikom.armv7loaderhost;

import android.app.Activity;
import android.media.AudioAttributes;
import android.media.MediaDataSource;
import android.media.MediaPlayer;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.TextView;
import java.io.IOException;

/**
 * Real Android 13 SDK MediaPlayer test of rapid SAME-TRACK Start/Stop before
 * prepare and of Next while earlier async sources are still preparing.
 *
 * OWN 440/660/330Hz WAV only; no external app or player instrumentation.
 * A stale-simulated callback is explicitly NOT evidence of an actual stale
 * framework callback. Actual callback counters are tracked separately.
 */
public final class OwnAndroidAsyncRaceProbe {
    private static final String TAG="CelikomOwnMediaRace";
    private static final int ROUNDS=12;
    private static final long TIMEOUT_MS=55000L;
    private final Activity owner;
    private final TextView status;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private MediaPlayer active;
    private OwnedWav source;
    private long revision;
    private int activePlayers, maxActivePlayers, creates, releases;
    private int preparedB, pausedB, seeksB, retiredCallbacks, syntheticStaleRejected;
    private int round;
    private boolean finished;

    public OwnAndroidAsyncRaceProbe(Activity owner,TextView status){
        this.owner=owner;
        this.status=status;
    }
    public void run(){
        if(!"pro.celikom.armv7loaderhost.audio".equals(owner.getPackageName())){
            complete(false,"WRONG_PACKAGE");return;
        }
        handler.postDelayed(()->{
            if(!finished)complete(false,"RACE_TIMEOUT");
        },TIMEOUT_MS);
        runRound(0);
    }
    private void runRound(int number){
        if(finished)return;
        if(number==ROUNDS){
            boolean exact=creates==4*ROUNDS
                &&releases==creates-1
                &&activePlayers==1 &&maxActivePlayers==1
                &&preparedB==ROUNDS &&pausedB==ROUNDS/2 &&seeksB==ROUNDS/2
                &&syntheticStaleRejected==3*ROUNDS;
            complete(exact,exact?"OWN_ASYNC_RACE_PASS":"RACE_COUNTERS");
            return;
        }
        round=number;
        // Exercise two rapid Start/Stop toggles on song A while prepareAsync
        // is pending; only a final Next to B may become actively prepared.
        install(0,null);
        long canceled0=revision;
        OwnSameTrackReloadPlan.Decision start=OwnSameTrackReloadPlan.decide(
                1,0,true,AudioSmokeSource.A_ALT,0,true);
        if(!start.reload||start.targetSource!=1){
            complete(false,"START_TARGET");return;
        }
        install(start.targetSource,null);
        long canceled1=revision;
        OwnSameTrackReloadPlan.Decision stop=OwnSameTrackReloadPlan.decide(
                1,1,false,AudioSmokeSource.A_ORIGINAL,0,true);
        if(!stop.reload||stop.targetSource!=0){
            complete(false,"STOP_TARGET");return;
        }
        install(stop.targetSource,null);
        long canceled2=revision;
        OwnSameTrackReloadPlan.Decision next=OwnSameTrackReloadPlan.decide(
                2,AudioSmokeSource.B_ORIGINAL,true,AudioSmokeSource.A_ALT,0,true);
        if(next.reload||next.targetSource!=AudioSmokeSource.B_ORIGINAL){
            complete(false,"NEXT_TARGET");return;
        }
        install(next.targetSource,()->validateB(number));
        // These are deliberately simulated late signals (source references
        // that are already canceled). Do NOT label as platform callbacks.
        verifySyntheticLate(canceled0);
        verifySyntheticLate(canceled1);
        verifySyntheticLate(canceled2);
    }
    private void verifySyntheticLate(long retiredTicket){
        if(retiredTicket==revision){
            complete(false,"STALE_TICKET_ACCEPTED");
            return;
        }
        syntheticStaleRejected++;
    }
    private void install(int variant,Runnable afterPrepared){
        if(finished)return;
        releaseActive();
        final long ticket=revision;
        try {
            source=new OwnedWav(AudioSmokeSource.wave(variant));
            MediaPlayer candidate=new MediaPlayer();
            creates++;
            activePlayers++;
            maxActivePlayers=Math.max(maxActivePlayers,activePlayers);
            if(activePlayers!=1){
                complete(false,"PARALLEL_PLAYERS");return;
            }
            active=candidate;
            candidate.setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            candidate.setDataSource(source);
            candidate.setVolume(0.04f,0.04f);
            candidate.setOnPreparedListener(mp->{
                if(finished)return;
                if(ticket!=revision||mp!=active){
                    // May be zero on Android when callbacks are removed
                    // during release(). This is not required for PASS.
                    retiredCallbacks++;
                    return;
                }
                if(variant!=AudioSmokeSource.B_ORIGINAL||afterPrepared==null){
                    complete(false,"CANCELED_PREPARE_DELIVERED");return;
                }
                preparedB++;
                afterPrepared.run();
            });
            candidate.setOnErrorListener((mp,what,extra)->{
                if(!finished&&ticket==revision&&mp==active)
                    complete(false,"ACTIVE_PLAYER_ERROR");
                return true;
            });
            candidate.prepareAsync();
        } catch(Throwable failure) {
            complete(false,"NATIVE_PREPARE_ERROR");
        }
    }
    private void validateB(int number){
        if(finished)return;
        final long ticket=revision;
        final MediaPlayer mp=active;
        try{
            if(mp==null||activePlayers!=1){
                complete(false,"MISSING_B_PLAYER");return;
            }
            mp.start();
            if(!mp.isPlaying()){
                complete(false,"B_NOT_PLAYING");return;
            }
            if((number&1)==0){
                handler.postDelayed(()->{
                    if(finished)return;
                    if(ticket!=revision||mp!=active){
                        complete(false,"B_RETIRED_DURING_VALIDATE");return;
                    }
                    try{
                        if(!mp.isPlaying()){
                            complete(false,"B_EARLY_PAUSE");return;
                        }
                        runRound(number+1);
                    }catch(Throwable failure){complete(false,"B_PLAYBACK_STATE");}
                },110);
            } else {
                mp.pause();
                if(mp.isPlaying()){
                    complete(false,"B_PAUSE_STATE");return;
                }
                pausedB++;
                mp.setOnSeekCompleteListener(seeked->{
                    if(finished)return;
                    if(ticket!=revision||seeked!=active){
                        retiredCallbacks++;
                        return;
                    }
                    try{
                        int at=mp.getCurrentPosition();
                        if(mp.isPlaying()||at<950||at>2300){
                            complete(false,"B_SEEK_PAUSE_STATE");return;
                        }
                        seeksB++;
                        handler.postDelayed(()->{
                            if(!finished)runRound(number+1);
                        },30);
                    }catch(Throwable failure){complete(false,"B_SEEK_POSITION");}
                });
                mp.seekTo(1400,MediaPlayer.SEEK_CLOSEST);
            }
        }catch(Throwable failure){complete(false,"B_CALLBACK_STATE");}
    }
    private void releaseActive(){
        revision++;
        MediaPlayer prior=active;
        OwnedWav old=source;
        active=null;
        source=null;
        if(prior!=null){
            releases++;
            activePlayers--;
            try{
                prior.setOnPreparedListener(null);
                prior.setOnErrorListener(null);
                prior.setOnSeekCompleteListener(null);
                prior.release();
            }catch(Throwable ignored){}
        }
        if(old!=null)try{old.close();}catch(IOException ignored){}
    }
    private void complete(boolean success,String code){
        if(finished)return;
        finished=true;
        // Evaluate counts before releasing the final B player.
        String outcome="RESULT="+(success?"PASS":"FAIL")+" CODE="+code;
        releaseActive();
        status.setText("CELIKOM OWN Android race check\n"+outcome
            +"\nOnly generated tones; no Yandex or user data");
        Log.d(TAG,outcome);
    }
    private static final class OwnedWav extends MediaDataSource {
        private final byte[] contents;
        private boolean closed;
        OwnedWav(byte[] contents){this.contents=contents;}
        @Override public int readAt(long pos,byte[] dst,int offset,int size){
            if(closed||pos<0||offset<0||size<0||offset>dst.length-size)return -1;
            if(pos>=contents.length)return -1;
            int amount=(int)Math.min((long)size,contents.length-pos);
            System.arraycopy(contents,(int)pos,dst,offset,amount);
            return amount;
        }
        @Override public long getSize(){return contents.length;}
        @Override public void close()throws IOException{closed=true;}
    }
}
