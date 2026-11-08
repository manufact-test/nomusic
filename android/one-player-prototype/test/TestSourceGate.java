import pro.celikom.oneplayer.SourceGate;
import pro.celikom.oneplayer.SourceGate.*;

public class TestSourceGate {
    private static int count;
    private static final String ORIGINAL = "https://example.invalid/authorized-original";
    private static Track track(String id, String edition, Evidence evidence) {
        return new Track(id, edition, ORIGINAL, 232330, evidence);
    }
    private static Candidate candidate(String id, String edition) {
        return new Candidate(id, edition, "content://pro.celikom.oneplayer.test/cache/raskol",
            232333, true, true, true, true);
    }
    private static void check(Selection expected, String reason, Track t, Candidate c) {
        Decision d = SourceGate.select(t,c);
        if (d.selection != expected || !d.reason.equals(reason))
            throw new AssertionError(reason + " expected " + expected + "; got " + d.selection + " / " + d.reason);
        if (d.selection == Selection.ORIGINAL && !ORIGINAL.equals(d.uri))
            throw new AssertionError("Original fallback URI mutated");
        count++;
    }
    public static void main(String[] args) {
        Track raskol = track("42884423","album-edition-A",Evidence.INTERNAL_CATALOG);
        Candidate ready = candidate("42884423","album-edition-A");
        check(Selection.REPLACEMENT,"approved_cached_source",raskol,ready);
        check(Selection.ORIGINAL,"catalog_identity_unverified",
            track("548","album-edition-A",Evidence.EXTERNAL_ALIAS),ready);
        check(Selection.ORIGINAL,"catalog_identity_unverified",
            track("42884423","album-edition-A",Evidence.TITLE_MATCH),ready);
        check(Selection.ORIGINAL,"no_replacement",raskol,null);
        check(Selection.ORIGINAL,"catalog_mismatch",raskol,candidate("1944599","album-edition-A"));
        check(Selection.ORIGINAL,"edition_unverified",raskol,candidate("42884423","album-edition-B"));
        check(Selection.ORIGINAL,"edition_unverified",track("42884423",null,Evidence.INTERNAL_CATALOG),ready);
        check(Selection.ORIGINAL,"not_ready",raskol,
            new Candidate("42884423","album-edition-A","content://cached",232333,true,true,false,true));
        check(Selection.ORIGINAL,"permission_denied",raskol,
            new Candidate("42884423","album-edition-A","content://cached",232333,false,true,true,true));
        check(Selection.ORIGINAL,"permission_denied",raskol,
            new Candidate("42884423","album-edition-A","content://cached",232333,true,false,true,true));
        check(Selection.ORIGINAL,"duration_mismatch",raskol,
            new Candidate("42884423","album-edition-A","content://cached",235000,true,true,true,true));
        check(Selection.ORIGINAL,"untrusted_replacement_uri",raskol,
            new Candidate("42884423","album-edition-A","https://external.invalid/track",232333,true,true,true,true));
        System.out.println("PASS: " + count + " offline pre-play source-gate cases");
    }
}
