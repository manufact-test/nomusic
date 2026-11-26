package pro.celikom.a1exitwitness;

import java.lang.annotation.Annotation;
import java.lang.reflect.Method;

/**
 * BETA23, owner-only. Ask the original signed FileInfoApi for MP3 so that
 * its selected extractor/decoder matches the approved MPEG byte source.
 *
 * The exact original method+handler link and FileInfoApi identity are
 * established at proxy creation, not inferred from a string track ID alone.
 * No server URL, media bytes, timing, licence, authentication or vendor
 * response object is rewritten. Non-target tracks and owner-off are unchanged.
 */
final class NativeIssuerCodecPreference {
    private static final String OWNER_TRIAL_TRACK = "144530503";

    static boolean preferMp3ForOwnedFileInfo(
            Method originalMethod,Object[] actualArguments,int trackIndex,
            boolean ownerEnabled,boolean exactOriginalFileInfoApi) {
        if (!ownerEnabled || !exactOriginalFileInfoApi
                || originalMethod == null || actualArguments == null)
            return false;
        final Class<?>[] types;
        final Annotation[][] annotated;
        try {
            types = originalMethod.getParameterTypes();
            annotated = originalMethod.getParameterAnnotations();
        } catch (Throwable ignored) {return false;}
        if (types.length != actualArguments.length
                || annotated.length != types.length
                || trackIndex < 0 || trackIndex >= types.length
                || types[trackIndex] != String.class
                || !OWNER_TRIAL_TRACK.equals(actualArguments[trackIndex]))
            return false;
        int verifiedTrackIndex = -1;
        int codecsIndex = -1;
        for (int i = 0; i < annotated.length; i++) {
            for (Annotation annotation : annotated[i]) {
                if (annotation == null) continue;
                String name = annotation.annotationType().getName();
                if (!"Vz8".equals(name)
                        && !"retrofit2.http.Query".equals(name))
                    continue;
                String key;
                try {
                    Object value = annotation.annotationType()
                        .getMethod("value").invoke(annotation);
                    if (!(value instanceof String)) return false;
                    key = (String) value;
                } catch (Throwable ignored) {return false;}
                if ("trackId".equals(key)) {
                    if (verifiedTrackIndex >= 0) return false;
                    verifiedTrackIndex = i;
                } else if ("codecs".equals(key)) {
                    if (codecsIndex >= 0) return false;
                    codecsIndex = i;
                }
            }
        }
        if (verifiedTrackIndex != trackIndex || codecsIndex < 0
                || codecsIndex == trackIndex
                || types[codecsIndex] != String.class
                || !(actualArguments[codecsIndex] instanceof String))
            return false;
        String old = (String) actualArguments[codecsIndex];
        if (old.isEmpty() || old.length() > 512 || "mp3".equals(old))
            return false;
        // The proxy's original invocation handler receives the same
        // Object[] reference; execute it ONCE after this single exact edit.
        actualArguments[codecsIndex] = "mp3";
        return true;
    }

    private NativeIssuerCodecPreference() {}
}
