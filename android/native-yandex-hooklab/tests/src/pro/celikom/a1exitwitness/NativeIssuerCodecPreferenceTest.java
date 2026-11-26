package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;
import retrofit2.http.Query;

public final class NativeIssuerCodecPreferenceTest {
    interface FileInfoApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") String codecs,@Query("quality") String quality);
    }
    interface NonString {
        Object fileInfo(@Query("trackId") String track,@Query("codecs") int codecs);
    }
    interface Duplicate {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") String one,@Query("codecs") String two);
    }
    interface NoCodec {
        Object fileInfo(@Query("trackId") String track,@Query("quality") String q);
    }
    interface WrongAnnotation {
        Object fileInfo(String track,@Query("codecs") String codecs);
    }

    private static Method method(Class<?> type) {
        return type.getDeclaredMethods()[0];
    }
    private static void yes(boolean condition) {
        if(!condition)throw new AssertionError("EXPECTED_TRUE");
    }
    private static void no(boolean condition) {
        if(condition)throw new AssertionError("EXPECTED_FALSE");
    }
    private static void equal(Object expected,Object actual) {
        if(!expected.equals(actual))
            throw new AssertionError("NOT_EQUAL");
    }

    public static void main(String[] args) {
        Method exact=method(FileInfoApi.class);
        Object[] owned={"144530503","aac,mp3","lossless"};
        yes(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,owned,0,true,true));
        equal("mp3",owned[1]);
        equal("lossless",owned[2]);
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,owned,0,true,true)); // idempotent

        Object[] off={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,off,0,false,true));
        equal("aac",off[1]);

        Object[] other={"123456789","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,other,0,true,true));
        equal("aac",other[1]);

        Object[] download={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,download,0,true,false));
        equal("aac",download[1]);

        Object[] wrongTrackIndex={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,wrongTrackIndex,1,true,true));
        equal("aac",wrongTrackIndex[1]);

        Object[] malformed={"144530503","aac"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,malformed,0,true,true));
        equal("aac",malformed[1]);

        Object[] duplicate={"144530503","aac","mp3"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(Duplicate.class),duplicate,0,true,true));
        equal("aac",duplicate[1]);

        Object[] noCodec={"144530503","aac"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(NoCodec.class),noCodec,0,true,true));
        equal("aac",noCodec[1]);

        Object[] wrongAnnotation={"144530503","aac"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(WrongAnnotation.class),wrongAnnotation,0,true,true));
        equal("aac",wrongAnnotation[1]);

        Object[] nonString={"144530503",99};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(NonString.class),nonString,0,true,true));
        equal(99,nonString[1]);

        System.out.println("BETA23_OWNER_EXACT_MP3_QUERY_REGRESSIONS_PASS");
    }
}
