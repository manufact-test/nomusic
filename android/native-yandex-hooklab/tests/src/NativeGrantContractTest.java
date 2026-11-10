import pro.celikom.yandex.nativehooklab.NativeGrantContract;
import pro.celikom.yandex.nativehooklab.NativeGrantContract.Grant;

public final class NativeGrantContractTest {
    private static int checks;
    private static final long NOW = 1_799_000_000_000L;
    private static final long EXPIRES = NOW + 300_000L;
    private static final String ORIGIN = "https://api.celikom.test";
    private static final String T = "a".repeat(64);
    private static final String GOOD = ORIGIN + "/api/v1/audio/139?token=" + T
            + "&expires=" + (EXPIRES / 1000) + "&sid=7";
    private static void yes(boolean actual, String msg) {
        checks++;
        if (!actual) throw new AssertionError(msg + " #" + checks);
    }
    private static Grant grant(String id, boolean approved, boolean entitled, String url,
                               long expiry, String type) {
        return new Grant(id, approved, entitled, url, expiry, type);
    }
    private static Grant good(String url) {
        return grant("42498653", true, true, url, EXPIRES, "audio/mpeg");
    }
    private static boolean accept(Grant g) {
        return NativeGrantContract.isAcceptable(g, "42498653", ORIGIN, NOW);
    }
    private static void exactOriginalContract() {
        yes(accept(good(GOOD)), "exact signed session grant accepted structurally");
        yes(accept(good(GOOD.replace("&sid=7",""))), "optional SID allowed if server issues none");
        yes(!accept(good(GOOD + "&celikom_native_query_guard=0")),
                "do not blindly port desktop-only padding to native Android");
        yes(!accept(good(GOOD + "?vsid=X&source_index=2")),
                "double question mark cannot corrupt SID");
        yes(!accept(good(GOOD.replace("sid=7", "sid=7?vsid=X"))), "corrupted SID rejected");
        yes(!accept(good(GOOD.replace("token="+T, "token=INVALID"))),
                "invalid token syntax rejected");
        yes(!accept(good(GOOD.replace("token="+T, "token="+T+"&token="+T))),
                "duplicate token rejected");
        yes(!accept(good(GOOD.replace("sid=7", "sid=%37"))), "encoded SID rejected");
        yes(!accept(good(GOOD.replace("&sid=7", "&sid=7&debug=1"))),
                "unknown param rejected");
        yes(!accept(good(GOOD+"#t=60")), "source fragment rejected until decoder proves it");
        yes(!accept(good(GOOD.replace("/audio/139","/audio/../139"))),
                "path traversal rejected");
        yes(!accept(good(GOOD.replace("/audio/139","/audio/0139"))),
                "resource ID must be canonical");
        yes(!accept(good(GOOD.replace(ORIGIN,"https://other.test"))),
                "other host rejected");
        yes(!accept(good(GOOD.replace("https://","http://"))),
                "plaintext HTTP rejected");
        yes(!accept(good(GOOD.replace(ORIGIN,"https://bad@api.celikom.test"))),
                "userinfo rejected");
    }
    private static void identityAndSecurity() {
        yes(NativeGrantContract.isExactTrackId("42884423"), "exact decimal track");
        for (String bad : new String[]{"0","00","01","x12"," 1","1 ","1:3","-1","1.2","","1".repeat(25)}) {
            yes(!NativeGrantContract.isExactTrackId(bad), "reject noncanonical track "+bad);
        }
        yes(!accept(grant("9",true,true,GOOD,EXPIRES,"audio/mpeg")), "wrong track grant");
        yes(!accept(grant("42498653",false,true,GOOD,EXPIRES,"audio/mpeg")), "unapproved");
        yes(!accept(grant("42498653",true,false,GOOD,EXPIRES,"audio/mpeg")), "not entitled");
        yes(!accept(grant("42498653",true,true,GOOD,EXPIRES,"text/plain")), "wrong media MIME");
        yes(!accept(grant("42498653",true,true,GOOD,EXPIRES+1,"audio/mpeg")),
                "URL expiry and grant timestamp mismatch");
        yes(!accept(grant("42498653",true,true,GOOD,NOW+3000,"audio/mpeg")),
                "insufficient lifetime");
        yes(!accept(grant("42498653",true,true,GOOD,NOW+40*60*1000,"audio/mpeg")),
                "excessive lifetime");
        yes(!NativeGrantContract.isAcceptable(good(GOOD),"42498653",
                "https://api.celikom.test/path",NOW), "origin must be root");
        yes(!NativeGrantContract.isAcceptable(good(GOOD),"42498653",
                "http://api.celikom.test",NOW), "allowed origin HTTPS only");
        yes(!NativeGrantContract.isAcceptable(good(GOOD),"42498653",
                "https://api.celikom.test?ignored=1",NOW), "origin query forbidden");
        yes(!NativeGrantContract.isAcceptable(good(GOOD), "another-track",
                ORIGIN,NOW), "no fuzzy matching");
        yes(!NativeGrantContract.isAcceptable(good(GOOD), "42498653",
                ORIGIN,-1), "invalid monotonic auth time rejected");
    }
    public static void main(String[] args) {
        exactOriginalContract();
        identityAndSecurity();
        System.out.println("PASS: NativeGrantContract " + checks
                + " URL/identity/expiry/source safety assertions (no network, tokens logged or decoder)");
    }
}
