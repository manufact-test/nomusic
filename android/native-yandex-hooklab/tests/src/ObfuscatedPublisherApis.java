import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

// Synthetic JVM fixture of exact R8 annotation class names from signed 2025 DEX.
public final class ObfuscatedPublisherApis {
    public interface FileInfoApi {
        Object getFileInfo(@Vz8("trackId") String id, @Vz8("codecs") String codecs);
    }
    public interface DownloadInfoApi {
        Object downloadInfo(@fj7("trackId") String id, @Vz8("direct") Boolean direct);
    }
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.PARAMETER)
    public @interface FakeTrackId { String value(); }
    public interface FakeApi {
        Object unrelated(@FakeTrackId("trackId") String id);
    }
}
