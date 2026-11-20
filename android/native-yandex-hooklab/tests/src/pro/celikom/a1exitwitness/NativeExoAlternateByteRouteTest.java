package pro.celikom.a1exitwitness;

import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeSourceGate;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

public final class NativeExoAlternateByteRouteTest {
    private static void check(boolean b,String message) {
        if(!b)throw new AssertionError(message);
    }
    private static final class MemoryCursor implements NativeExoAlternateByteRoute.Cursor {
        final byte[] data;
        final boolean failOnOpen;
        int position;
        boolean closed;
        MemoryCursor(byte[] data,boolean fail) {this.data=data;failOnOpen=fail;}
        public long open(long start) throws IOException {
            if(failOnOpen)throw new IOException("offline");
            if(start<0 || start>=data.length)throw new IOException("range");
            position=(int)start;
            return data.length-start;
        }
        public int read(byte[] out,int offset,int length) {
            if(position>=data.length)return -1;
            int n=Math.min(length,data.length-position);
            System.arraycopy(data,position,out,offset,n);
            position+=n;
            return n;
        }
        public void close() {closed=true;}
    }
    private static final class Factory implements NativeExoAlternateByteRoute.CursorFactory {
        byte[] data="CELIKOM-ALTERNATE".getBytes(StandardCharsets.US_ASCII);
        boolean fail;
        final ArrayList<MemoryCursor> instances=new ArrayList<>();
        public NativeExoAlternateByteRoute.Cursor create(String url,String mime) {
            check(url.startsWith("https://audio.example/"),"URL_NEVER_REWRITTEN");
            check("audio/mpeg".equals(mime),"MIME_UNCHANGED");
            MemoryCursor cursor=new MemoryCursor(data,fail);
            instances.add(cursor);
            return cursor;
        }
    }
    public static void main(String[] args) throws Exception {
        final long now=1795160000000L,expiration=(now / 1000 + 500)*1000;
        final String url="https://audio.example/api/v1/audio/42?token="
            +"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            +"&expires="+expiration/1000+"&sid=8";
        NativeGrantContract.Grant grant=new NativeGrantContract.Grant(
            "42884423","41","main",180000,2,true,true,url,
            expiration,"audio/mpeg");
        Object yandexDataSource=new Object(),prefetch=new Object();
        Factory factory=new Factory();
        NativeExoAlternateByteRoute route=new NativeExoAlternateByteRoute(factory);
        check(route.openIfApproved(yandexDataSource,0)==null,
            "NEVER_REPLACE_WITHOUT_APPROVED_GRANT");
        check(!route.armApproved(1,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ORIGINAL),"ORIGINAL_DECISION_CANNOT_ARM");
        check(!route.armApproved(1,yandexDataSource,"42884424","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),"WRONG_TRACK_CANNOT_ARM");
        check(route.armApproved(1,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),"VALID_REAL_SIGNED_GRANT_ARMS");
        check(route.openIfApproved(prefetch,0)==null,
            "PREFETCH_SOURCE_NOT_ROUTED");
        check(route.openIfApproved(yandexDataSource,0)==factory.data.length,
            "ONE_EXO_DECODER_SEES_REAL_ALTERNATE_LENGTH");
        byte[] b=new byte[50];
        check(route.readIfApproved(prefetch,b,0,b.length)==null,
            "PREFETCH_BYTES_OWNED_BY_VENDOR");
        check(route.readIfApproved(yandexDataSource,b,0,7)==7,
            "EXO_READ_ALT_BYTES");
        check("CELIKOM".equals(new String(b,0,7,StandardCharsets.US_ASCII)),
            "ACTUAL_ALT_BYTES_READ_BY_SAME_EXO_SOURCE");
        check(route.closeIfApproved(yandexDataSource),
            "ALTERNATE_OPEN_NEVER_CLOSE_UNOPENED_VENDOR");
        check(factory.instances.get(0).closed,"ALT_STREAM_CLOSED");
        check(route.openIfApproved(yandexDataSource,8)==factory.data.length-8,
            "SEEK_REOPENS_APPROVED_RANGE_AT_EXACT_BYTE_OFFSET");
        check(route.readIfApproved(yandexDataSource,b,0,3)==3,
            "SEEK_STREAM_READ");
        route.cancelForNext();
        check(factory.instances.get(1).closed,"NEXT_CLOSES_ALT_CURSOR");
        check(route.openIfApproved(yandexDataSource,0)==null,
            "NEXT_REVOKES_OLD_APPROVAL");
        check(route.readIfApproved(yandexDataSource,b,0,8)==null,
            "NEXT_MUST_NOT_READ_PREVIOUS_TRACK");
        check(!route.closeIfApproved(yandexDataSource),
            "UNOPENED_VENDOR_CLOSE_NOT_MASKED");
        check(!route.armApproved(1,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),
            "NEXT_CANNOT_REUSE_OLD_SIGNED_SELECTION_GENERATION");

        Factory broken=new Factory();
        broken.fail=true;
        NativeExoAlternateByteRoute beforeAnyByte=
            new NativeExoAlternateByteRoute(broken);
        check(beforeAnyByte.armApproved(3,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),"SIGNED_GRANT_ACCEPTED");
        check(beforeAnyByte.openIfApproved(yandexDataSource,0)==null,
            "FAILED_FIRST_ALT_OPEN_RETURNS_CONTROL_TO_ORIGINAL");
        check(beforeAnyByte.openIfApproved(yandexDataSource,0)==null,
            "FAILED_ALT_SOURCE_NOT_REARMED");
        check(!beforeAnyByte.armApproved(3,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),
            "FAILED_OPEN_CANNOT_REARM_SAME_SELECTION");
        Factory drop=new Factory();
        NativeExoAlternateByteRoute afterAudio=new NativeExoAlternateByteRoute(drop);
        check(afterAudio.armApproved(4,yandexDataSource,"42884423","41","main",
            180000,grant,"https://audio.example",now,
            NativeSourceGate.Choice.ALTERNATE),"GRANT_ACCEPTED");
        check(afterAudio.openIfApproved(yandexDataSource,0)!=null,
            "ALTERNATE_OPENED");
        drop.fail=true;
        boolean threw=false;
        try {afterAudio.openIfApproved(yandexDataSource,2);}
        catch(IOException expected){threw=true;}
        check(threw,"AFTER_ALT_BYTES_NO_UNSAFE_ORIGINAL_MIXING");
        boolean noOriginalMix=false;
        try {afterAudio.readIfApproved(yandexDataSource,b,0,2);}
        catch(IOException expected) {noOriginalMix=true;}
        // Failed seek cancels old alternate; caller must never silently
        // claim fresh original bytes inside that same decoder stream.
        check(afterAudio.openIfApproved(yandexDataSource,0)==null,
            "FAILED_SEEK_DISCARDS_ALTERNATE_GENERATION");
        check(noOriginalMix || !afterAudio.isArmed(yandexDataSource),
            "FAILED_SEEK_CANNOT_KEEP_STALE_ALT_ARMED");

        System.out.println("NATIVE_EXO_SINGLE_PLAYER_ENCODED_BYTES_ROUTE_PASS");
    }
}
