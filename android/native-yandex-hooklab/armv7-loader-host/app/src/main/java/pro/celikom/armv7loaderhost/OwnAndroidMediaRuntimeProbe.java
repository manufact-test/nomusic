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
 * Real Android SDK MediaPlayer callback test with OWN generated 8s WAV audio.
 *
 * The activity is a CELIKOM-owned test APK in a disposable emulator; this
 * NEVER hooks/launches Yandex and never reads user accounts, URLs or files.
 * Logs contain ONLY fixed stage identifiers and PASS/FAIL, not audio data.
 * Emulator "-noaudio" proves decoder lifecycle, NOT audible output.
 */
public final class OwnAndroidMediaRuntimeProbe {
    private static final String TAG="CelikomOwnMediaProbe";
    private static final long TIMEOUT_MS=35000;
    private final Activity activity;
    private final TextView view;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private MediaPlayer player;
    private Data data;
    private long revision;
    private int source=-1, prepareCount, releaseCount, pauseCount, positionRestoreCount;
    private boolean expectedPlaying, completed;
    private String phase="READY";
    private int pausedAtMs;

    public OwnAndroidMediaRuntimeProbe(Activity activity,TextView view){
        this.activity=activity;
        this.view=view;
    }
    public void run(){
        if(!"pro.celikom.armv7loaderhost.audio".equals(activity.getPackageName())){
            result(false,"WRONG_PACKAGE");
            return;
        }
        note("START_OWN_ONLY");
        handler.postDelayed(()->{
            if(!completed)result(false,"CALLBACK_TIMEOUT");
        },TIMEOUT_MS);
        prepare(0,0,true,"A_ORIGINAL",()->{
            handler.postDelayed(()->{
                if(completed)return;
                if(player==null||!player.isPlaying()){
                    result(false,"ORIGINAL_NEVER_STARTED");return;
                }
                phase="SEEK_A";
                try {player.seekTo(2200,MediaPlayer.SEEK_CLOSEST);}
                catch(Throwable bad){result(false,"SEEK_A_FAILED");}
            },260);
        },()->{
            if(completed)return;
            try {
                player.pause();
                pauseCount++;
                pausedAtMs=player.getCurrentPosition();
                if(pausedAtMs<1500||pausedAtMs>3200||player.isPlaying()){
                    result(false,"PAUSE_SEEK_NOT_RETAINED");return;
                }
                note("PAUSE_AND_SEEK_A_PASS");
                // Windows W60 principle: rebuild only source, with original
                // paused state and progress; old player released FIRST.
                prepare(1,pausedAtMs,false,"A_ALTERNATE_PAUSED",()->{},()->{
                    if(completed)return;
                    try {
                        if(player.isPlaying()){
                            result(false,"PAUSE_BROKEN_AFTER_SOURCE_CHANGE");return;
                        }
                        int actual=player.getCurrentPosition();
                        if(Math.abs(actual-pausedAtMs)>550){
                            result(false,"POSITION_BROKEN_AFTER_PAUSED_RELOAD");return;
                        }
                        note("PAUSED_RELOAD_PASS");
                        // Resume the same PLAYER; then reload original A
                        // while playing, preserving actual progress.
                        player.start();
                        handler.postDelayed(()->{
                            if(completed)return;
                            try {
                                if(!player.isPlaying()){
                                    result(false,"ALTERNATE_NEVER_STARTED");return;
                                }
                                int position=player.getCurrentPosition();
                                prepare(0,position,true,"A_ORIGINAL_PLAYING",()->{},()->{
                                    if(completed)return;
                                    try {
                                        if(!player.isPlaying() || 
                                            Math.abs(player.getCurrentPosition()-position)>800) {
                                            result(false,"PLAYING_RELOAD_FAILED");return;
                                        }
                                        note("PLAYING_RELOAD_PASS");
                                        // Next to a distinct original track B.
                                        prepare(2,0,true,"B_ORIGINAL_NEXT",()->{
                                            handler.postDelayed(()->{
                                                if(completed)return;
                                                if(source!=2||player==null||!player.isPlaying()
                                                        ||prepareCount!=4||releaseCount!=3
                                                        ||pauseCount!=1||positionRestoreCount!=2){
                                                    result(false,"NEXT_SINGLE_PLAYER_COUNTS");return;
                                                }
                                                note("NEXT_B_PASS");
                                                result(true,"OWN_DECODER_LIFECYCLE");
                                            },200);
                                        },()->{});
                                    }catch(Throwable bad){
                                        result(false,"PLAYING_RELOAD_STATE");
                                    }
                                });
                            }catch(Throwable bad){
                                result(false,"ALTERNATE_STATE");
                            }
                        },240);
                    }catch(Throwable bad){
                        result(false,"PAUSED_RELOAD_STATE");
                    }
                });
            }catch(Throwable bad){result(false,"PAUSE_A_FAILED");}
        });
    }
    /**
     * Each invocation RELEASES any old player before constructing new one.
     * Exactly one owned MediaPlayer exists; no queue changes or hidden song.
     */
    private void prepare(int variant,int position,boolean resume,
                         String label,Runnable afterPrepared,Runnable afterSeek){
        if(completed)return;
        release();
        source=variant;
        final long ticket=revision;
        expectedPlaying=resume;
        phase=label;
        try {
            data=new Data(AudioSmokeSource.wave(variant));
            MediaPlayer p=new MediaPlayer();
            player=p;
            p.setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            p.setDataSource(data);
            p.setVolume(0.1f,0.1f);
            p.setOnPreparedListener(mp->{
                if(ticket!=revision||mp!=player||completed)return;
                try {
                    prepareCount++;
                    if(position>0) {
                        // Stay paused before/on restore. PLAYING resumes
                        // only after this asynchronous seek completes.
                        mp.seekTo(Math.max(0,Math.min(7900,position)),
                            MediaPlayer.SEEK_CLOSEST);
                    }else {
                        if(expectedPlaying)mp.start();
                        note(label+"_PREPARED");
                        afterPrepared.run();
                    }
                }catch(Throwable bad){result(false,"PREPARED_CALLBACK");}
            });
            p.setOnSeekCompleteListener(mp->{
                if(ticket!=revision||mp!=player||completed)return;
                try {
                    positionRestoreCount++;
                    if(expectedPlaying)mp.start();
                    note(label+"_SEEK_RESTORED");
                    afterSeek.run();
                }catch(Throwable bad){result(false,"RESTORE_CALLBACK");}
            });
            p.setOnErrorListener((mp,what,extra)->{
                if(ticket==revision&&mp==player)result(false,"DECODER_ERROR");
                return true;
            });
            p.prepareAsync();
        }catch(Throwable bad){result(false,"PREPARE_FAILED");}
    }

    private void release(){
        revision++;
        MediaPlayer old=player;
        Data previous=data;
        player=null;data=null;
        if(old!=null) {
            releaseCount++;
            try {
                old.setOnErrorListener(null);
                old.setOnPreparedListener(null);
                old.setOnSeekCompleteListener(null);
                old.release();
            }catch(Throwable ignored){}
        }
        if(previous!=null)try{previous.close();}catch(IOException ignored){}
    }
    private void note(String code){
        Log.d(TAG,"STEP="+code);
        view.setText("CELIKOM OWN Android MediaPlayer test\n"+
            "No Yandex / No accounts / No downloaded media\n"+
            "Phase: "+phase+"\nSTEP="+code);
    }
    private void result(boolean success,String code){
        if(completed)return;
        completed=true;
        release();
        String message="RESULT="+(success?"PASS":"FAIL")+" CODE="+code;
        Log.d(TAG,message);
        view.setText("CELIKOM OWN Android MediaPlayer test\n"+message+
            "\nNo proof of Yandex audio replacement.");
    }
    private static final class Data extends MediaDataSource {
        private final byte[] bytes;
        private boolean closed;
        Data(byte[] bytes){this.bytes=bytes;}
        @Override public int readAt(long at,byte[] buffer,int offset,int len){
            if(closed||at<0||offset<0||len<0||offset>buffer.length-len)return -1;
            if(at>=bytes.length)return -1;
            int copy=(int)Math.min(bytes.length-at,(long)len);
            System.arraycopy(bytes,(int)at,buffer,offset,copy);
            return copy;
        }
        @Override public long getSize(){return bytes.length;}
        @Override public void close()throws IOException{closed=true;}
    }
}
