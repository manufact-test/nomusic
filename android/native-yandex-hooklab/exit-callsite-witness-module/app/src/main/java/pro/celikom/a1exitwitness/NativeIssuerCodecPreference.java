package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;

/**
 * BETA33 codec safety rollback.
 *
 * BETA32 changed the original FileInfo codecs query to MP3, but the fresh
 * phone diagnostic still showed no MPEG decoder configuration and the owner
 * reported that Yandex could not play the target track. Do not mutate the
 * publisher's codec negotiation until the selected decoder and replacement
 * source can be proven to agree.
 *
 * Keep the explicit call contract, but fail closed without inspecting or
 * changing any original request argument.
 */
final class NativeIssuerCodecPreference {
    static boolean preferMp3ForOwnedFileInfo(
            Method originalMethod,Object[] actualArguments,int trackIndex,
            boolean ownerEnabled,boolean exactOriginalFileInfoApi) {
        return false;
    }

    private NativeIssuerCodecPreference() {}
}
