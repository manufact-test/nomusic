package pro.celikom.armv7loaderhost;
import android.app.Activity;
import android.graphics.Color;
import android.media.AudioAttributes;
import android.media.MediaDataSource;
import android.media.MediaPlayer;
import android.widget.*;
import java.io.IOException;
/** Synthetic WAVs, one MediaPlayer and one stream. Never accesses Yandex. */
public final class AudioSmokeScreen extends ScrollView {
    private final TextView status;
    private MediaPlayer player;
    private MediaDataSource data;
    private long revision;
    private boolean prepared,playing,fallback;
    private int track,selected=-1,pauses,resumes,seeks,nexts,errors,preparedCount;
    private String last="Ready";
    public AudioSmokeScreen(Activity owner){
        super(owner);
        LinearLayout ui=new LinearLayout(owner);
        ui.setOrientation(LinearLayout.VERTICAL);ui.setPadding(24,24,24,24);
        ui.setBackgroundColor(Color.WHITE);
        status=new TextView(owner);status.setTextColor(Color.BLACK);status.setTextSize(17);
        ui.addView(status);
        button(owner,ui,"Start A — alternative 660 Hz",()->open(1,false));
        button(owner,ui,"Pause / Resume",this::pauseResume);
        button(owner,ui,"Seek +3 seconds",this::seek);
        button(owner,ui,"Next B — original 330 Hz",()->{nexts++;open(2,false);});
        button(owner,ui,"Fallback A — original 440 Hz",()->open(1,true));
        button(owner,ui,"Stop",this::stopAndRelease);
        addView(ui);render();
    }
    private void button(Activity a,LinearLayout parent,String title,Runnable cb){
        Button b=new Button(a);b.setAllCaps(false);b.setText(title);
        b.setOnClickListener(v->{try{cb.run();}catch(Throwable t){errors++;last="Button ERROR";}render();});
        parent.addView(b);
    }
    private void open(int nextTrack,boolean forceOriginal){
        release();
        track=nextTrack;fallback=forceOriginal;
        selected=nextTrack==2?AudioSmokeSource.originalB():
            forceOriginal?AudioSmokeSource.originalA():AudioSmokeSource.chooseA();
        if(!AudioSmokeSource.valid(selected)){
            selected=nextTrack==2?AudioSmokeSource.originalB():AudioSmokeSource.originalA();fallback=true;
        }
        final long ticket=revision;
        final int sourceId=selected,trackId=nextTrack;
        try{
            data=new MemoryWav(AudioSmokeSource.wave(sourceId));
            MediaPlayer p=new MediaPlayer();player=p;
            p.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            p.setDataSource(data);p.setVolume(0.30f,0.30f);
            p.setOnPreparedListener(mp->{
                if(ticket!=revision||mp!=player)return;
                try{prepared=true;preparedCount++;mp.start();playing=true;last="PLAYING";}catch(Throwable x){failed(trackId,sourceId,"START");}
                render();
            });
            p.setOnSeekCompleteListener(mp->{
                if(ticket!=revision||mp!=player)return;
                seeks++;last="SEEK COMPLETED";render();
            });
            p.setOnCompletionListener(mp->{
                if(ticket!=revision||mp!=player)return;
                playing=false;last="ENDED";render();
            });
            p.setOnErrorListener((mp,what,extra)->{
                if(ticket==revision&&mp==player)failed(trackId,sourceId,"DECODE");
                return true;
            });
            last="PREPARING";p.prepareAsync();
        }catch(Throwable x){failed(trackId,sourceId,"PREPARE");}
        render();
    }
    private void failed(int trackId,int sourceId,String why){
        errors++;boolean retry=trackId==1&&sourceId==AudioSmokeSource.A_ALT&&!fallback;
        if(retry){open(1,true);last="FALLBACK ORIGINAL after "+why;}
        else{release();last="ERROR "+why+"; NO RETRY LOOP";}
        render();
    }
    private void pauseResume(){
        if(!prepared||player==null){last="NOT PREPARED";return;}
        try{
            if(playing){player.pause();pauses++;playing=false;last="PAUSED";}
            else{player.start();resumes++;playing=true;last="RESUMED";}
        }catch(Throwable x){errors++;last="PAUSE FAILED";}
    }
    private void seek(){
        if(!prepared||player==null){last="NOT PREPARED";return;}
        try{int pos=Math.min(7600,player.getCurrentPosition()+3000);
            player.seekTo(pos,MediaPlayer.SEEK_CLOSEST);last="SEEK REQUESTED "+pos+"ms";
        }catch(Throwable x){errors++;last="SEEK FAILED";}
    }
    private void release(){
        revision++;MediaPlayer old=player;MediaDataSource oldData=data;
        player=null;data=null;prepared=false;playing=false;
        if(old!=null)try{old.setOnErrorListener(null);old.setOnPreparedListener(null);
            old.setOnSeekCompleteListener(null);old.setOnCompletionListener(null);old.release();}catch(Throwable ignored){}
        if(oldData!=null)try{oldData.close();}catch(IOException ignored){}
    }
    public void stopAndRelease(){release();last="STOPPED";render();}
    private void render(){
        String src=selected==1?"ALT A 660Hz":selected==2?"ORIGINAL B 330Hz":
            selected==0?"ORIGINAL A 440Hz":"NONE";
        status.setText("CELIKOM AUDIO SOURCE SMOKE — OWN APP\nNo Yandex, account, internet or files.\n\n"+
            "Module hook ARMED: "+(AudioSmokeState.armed()?"YES":"NOT OBSERVED")+"\n"+
            "Source changed BEFORE PREPARE: "+(AudioSmokeState.swapped()?"YES":"NOT OBSERVED")+"\n"+
            "Track: "+(track==1?"A":track==2?"B":"NONE")+"\n"+
            "Source: "+src+"\nPrepared: "+(prepared?"YES":"NOT YET")+
            "\nPlaying: "+(playing?"YES":"NO")+"\nFallback: "+(fallback?"YES":"NO")+
            "\nPrepare="+preparedCount+" Pause="+pauses+" Resume="+resumes+
            "\nSeekComplete="+seeks+" Next="+nexts+" Errors="+errors+
            "\nLast: "+last+"\n\nTest: Start A → Pause/Resume → Seek +3s → Next B → Fallback A.\n"+
            "Only ONE platform MediaPlayer. Does NOT prove Yandex's decoder works.");
    }
    private static final class MemoryWav extends MediaDataSource {
        private final byte[] wav;private boolean closed;
        MemoryWav(byte[] wav){this.wav=wav;}
        @Override public int readAt(long at,byte[] dst,int offset,int len){
            if(closed||at<0||at>=wav.length)return -1;
            if(offset<0||len<0||offset>dst.length-len)return -1;
            int n=(int)Math.min((long)len,wav.length-at);
            System.arraycopy(wav,(int)at,dst,offset,n);return n;
        }
        @Override public long getSize(){return wav.length;}
        @Override public void close()throws IOException{closed=true;}
    }
}
