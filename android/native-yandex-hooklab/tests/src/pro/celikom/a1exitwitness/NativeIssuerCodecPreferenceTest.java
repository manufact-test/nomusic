package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;
import retrofit2.http.Query;

public final class NativeIssuerCodecPreferenceTest {
    interface FileInfoApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") String codecs,@Query("quality") String quality);
    }
    interface AmbiguousCodecsApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") String first,@Query("codecs") String second);
    }
    interface MissingCodecsApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("quality") String quality);
    }
    interface NonStringCodecsApi {
        Object fileInfo(@Query("trackId") String track,
            @Query("codecs") int codecs);
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

        Object[] target={"144530503","aac,mp3","lossless"};
        yes(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,target,0,true,true));
        equal("mp3",target[1]);
        equal("lossless",target[2]);

        Object[] targetAac={"144530503","aac","lossless"};
        yes(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,targetAac,0,true,true));
        equal("mp3",targetAac[1]);

        Object[] alreadyMp3={"144530503","mp3","lossless"};
        yes(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,alreadyMp3,0,true,true));
        equal("mp3",alreadyMp3[1]);

        for(String allowed:new String[]{"144530503","39949113","42884423"}) {
            Object[] argsForAllowed={allowed,"aac,mp3","lossless"};
            yes(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
                exact,argsForAllowed,0,true,true));
            equal("mp3",argsForAllowed[1]);
        }

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

        Object[] wrongTrackIndex={"144530503","aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,wrongTrackIndex,1,true,true));
        equal("aac",wrongTrackIndex[1]);

        Object[] wrongArgumentCount={"144530503","aac"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,wrongArgumentCount,0,true,true));
        equal("aac",wrongArgumentCount[1]);

        Object[] ambiguous={"144530503","aac","aac"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(AmbiguousCodecsApi.class),ambiguous,0,true,true));
        equal("aac",ambiguous[1]);
        equal("aac",ambiguous[2]);

        Object[] missing={"144530503","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(MissingCodecsApi.class),missing,0,true,true));
        equal("lossless",missing[1]);

        Object[] nonString={"144530503",7};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            method(NonStringCodecsApi.class),nonString,0,true,true));
        equal(Integer.valueOf(7),nonString[1]);

        Object[] nonStringTrack={Long.valueOf(144530503L),"aac","lossless"};
        no(NativeIssuerCodecPreference.preferMp3ForOwnedFileInfo(
            exact,nonStringTrack,0,true,true));
        equal("aac",nonStringTrack[1]);

        System.out.println("BETA32_ALLOWLISTED_MP3_CODEC_PREFERENCE_PASS");
    }
}
