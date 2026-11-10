import pro.celikom.ownedplayer.OwnedPlaybackContract;
import pro.celikom.ownedplayer.OwnedQueueFence;

/** JVM-only security and high-frequency Next races. No owner phone needed. */
public final class OwnedContractTest {
    static int checks;
    static void yes(boolean ok,String why) {
        checks++;
        if(!ok)throw new AssertionError(why+" #"+checks);
    }
    public static void main(String[] ignored) {
        long now=1_800_000_000_000L;
        long expires=now+600000;
        String token="a".repeat(64);
        String good=OwnedPlaybackContract.ORIGIN+"/api/v1/audio/17?token="+token+
                "&expires="+(expires/1000)+"&sid=91";
        yes(OwnedPlaybackContract.validSignedAudioUrl(good,17,expires,now),"valid signed URL");
        for(String bad:new String[] {
                "http://darkred-camel-588676.hostingersite.com/api/v1/audio/17?token="+token+"&expires="+(expires/1000),
                "https://evil.example/api/v1/audio/17?token="+token+"&expires="+(expires/1000),
                "https://darkred-camel-588676.hostingersite.com.evil.example/api/v1/audio/17?token="+token+"&expires="+(expires/1000),
                good+"&token="+token, good+"&x=1",good+"#part",
                good.replace("sid=91","sid=0"),
                good.replace("/17?", "/18?")
        })yes(!OwnedPlaybackContract.validSignedAudioUrl(bad,17,expires,now),"bad URL rejected");
        yes(!OwnedPlaybackContract.validSignedAudioUrl(good,17,now+1000,now),"expired rejected");
        yes(!OwnedPlaybackContract.validSignedAudioUrl(good,17,now+1900000,now),"long TTL rejected");
        yes(!OwnedPlaybackContract.activeAccess(false,now,now,15000),"denied subscription");
        yes(OwnedPlaybackContract.activeAccess(true,now,now+10000,15000),"live lease");
        yes(!OwnedPlaybackContract.activeAccess(true,now,now+15001,15000),"stale lease");
        yes(!OwnedPlaybackContract.activeAccess(true,now,now+10000,20000),"too long lease");
        yes(!OwnedPlaybackContract.validTrackId("0")&&
            !OwnedPlaybackContract.validTrackId("../1")&&
            !OwnedPlaybackContract.validTrackId("001"),"strict track ID");
        OwnedQueueFence fence=new OwnedQueueFence();
        for(int i=0;i<10000;i++){
            String id=String.valueOf(i+1);
            long gen=fence.begin(id);
            yes(fence.current(gen,id),"current generation");
            fence.clear();
            yes(!fence.current(gen,id),"stale after stop/Next");
        }
        System.out.println("PASS owned player "+checks+" contract assertions, 10000 Next/Stop invalidations");
    }
}
