package pro.celikom.a1exitwitness;

import java.lang.annotation.Annotation;
import java.lang.reflect.Method;

/**
 * BETA32 owner-only codec alignment for the signed CELIKOM MPEG source.
 *
 * The previous safety pause was necessary while the approved alternate
 * DataSource failed to arm/open/read. BETA31 now has a committed exact source
 * route that reaches those stages. For the explicit owner trial only, ask the
 * original FileInfoApi for MP3 so its format negotiation matches audio/mpeg.
 *
 * Fail closed unless the owner is enabled, the caller identified the exact
 * original FileInfoApi, the annotated publisher trackId is allowlisted, and
 * the method has one unambiguous String @Query("codecs") parameter. Only that
 * codecs argument is changed; every other request remains byte-for-byte intact.
 */
final class NativeIssuerCodecPreference {
    static boolean preferMp3ForOwnedFileInfo(
            Method originalMethod,Object[] actualArguments,int trackIndex,
            boolean ownerEnabled,boolean exactOriginalFileInfoApi) {
        if(!ownerEnabled || !exactOriginalFileInfoApi
                || originalMethod==null || actualArguments==null)
            return false;
        try {
            Class<?>[] parameterTypes=originalMethod.getParameterTypes();
            Annotation[][] parameterAnnotations=originalMethod.getParameterAnnotations();
            if(parameterTypes.length==0
                    || parameterTypes.length!=actualArguments.length
                    || parameterAnnotations.length!=parameterTypes.length)
                return false;

            int annotatedTrackIndex=uniqueQueryIndex(
                parameterTypes,parameterAnnotations,"trackId");
            if(annotatedTrackIndex<0 || annotatedTrackIndex!=trackIndex)
                return false;
            Object rawTrackId=actualArguments[trackIndex];
            if(!(rawTrackId instanceof String)
                    || !NativeTrackIdBetaPolicy.allows((String)rawTrackId))
                return false;

            int codecsIndex=uniqueQueryIndex(
                parameterTypes,parameterAnnotations,"codecs");
            if(codecsIndex<0 || codecsIndex==annotatedTrackIndex)
                return false;
            Object rawCodecs=actualArguments[codecsIndex];
            if(!(rawCodecs instanceof String)
                    || ((String)rawCodecs).isEmpty())
                return false;

            actualArguments[codecsIndex]="mp3";
            return true;
        } catch(Throwable ignored) {
            return false;
        }
    }

    private static int uniqueQueryIndex(Class<?>[] parameterTypes,
            Annotation[][] parameterAnnotations,String expectedValue) {
        int found=-1;
        for(int i=0;i<parameterAnnotations.length;i++) {
            for(Annotation annotation:parameterAnnotations[i]) {
                String value=queryValue(annotation);
                if(!expectedValue.equals(value))continue;
                if(found>=0 || parameterTypes[i]!=String.class)return -1;
                found=i;
            }
        }
        return found;
    }

    private static String queryValue(Annotation annotation) {
        if(annotation==null)return null;
        String annotationName=annotation.annotationType().getName();
        if(!"retrofit2.http.Query".equals(annotationName)
                && !"Vz8".equals(annotationName))
            return null;
        try {
            Object value=annotation.annotationType()
                .getMethod("value").invoke(annotation);
            return value instanceof String?(String)value:null;
        } catch(Throwable ignored) {
            return null;
        }
    }

    private NativeIssuerCodecPreference() {}
}
