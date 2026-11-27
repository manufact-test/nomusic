package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;
import retrofit2.http.Query;

public final class NativeIssuerCodecPreferenceTest {
    interface FileInfoApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") String codecs,@Query("quality") String quality);
    }

    private static Method method(Class<?> type) {
        return type.getDeclaredMethods()[0];
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

        // The allowlisted owner track must retain the exact publisher codec list.
        Object[] target={"144530503","aac,mp3","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,target,0,true,true));
        equal("aac,mp3",target[1]);
        equal("lossless",target[2]);

        // An AAC-only publisher request must also pass through unchanged.
        Object[] targetAac={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,targetAac,0,true,true));
        equal("aac",targetAac[1]);

        Object[] ownerOff={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,ownerOff,0,false,true));
        equal("aac",ownerOff[1]);

        Object[] otherTrack={"123456789","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,otherTrack,0,true,true));
        equal("aac",otherTrack[1]);

        Object[] nonOriginalApi={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,nonOriginalApi,0,true,false));
        equal("aac",nonOriginalApi[1]);

        System.out.println("BETA26_ORIGINAL_CODEC_PASSTHROUGH_PASS");
    }
}
