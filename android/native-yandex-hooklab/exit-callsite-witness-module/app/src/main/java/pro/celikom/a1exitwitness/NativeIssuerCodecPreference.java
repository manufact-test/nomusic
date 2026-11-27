package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;

/**
 * BETA26 safety pause.
 *
 * The BETA25 owner diagnostic showed that this request-only override changed
 * the original Yandex FileInfoApi codecs argument to "mp3" while the approved
 * CELIKOM DataSource never reached DATASOURCE_ARMED, AUDIO_OPEN or AUDIO_READ.
 * That request rewrite therefore changed publisher playback without delivering
 * replacement audio. Until the exact native source can be armed, preserve the
 * publisher's original codec negotiation byte-for-byte.
 *
 * Keep the existing call signature so the proxy contract stays explicit.
 * This method intentionally performs no argument inspection or mutation.
 */
final class NativeIssuerCodecPreference {
    static boolean preferMp3ForOwnedFileInfo(
            Method originalMethod,Object[] actualArguments,int trackIndex,
            boolean ownerEnabled,boolean exactOriginalFileInfoApi) {
        return false;
    }

    private NativeIssuerCodecPreference() {}
}
