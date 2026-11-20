package pro.celikom.a1exitwitness;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import retrofit2.http.Path;
import retrofit2.http.Query;

public final class PublisherTrackIdProxyContractTest {
    public interface BaseFileInfoApi {
        @Query("trackId") Object lookup(String trackId, String untouched);
        @Query("albumId") Object lookupAlbum(String albumId);
    }
    public interface FileInfoApi extends BaseFileInfoApi {
        @Query("format") Object format(String format);
    }
    public interface ExtendedFileInfoApi extends FileInfoApi {}
    public interface ExtraApi {
        @Path("id") Object unrelated(long id);
    }
    public interface DownloadInfoApi {
        @Path("trackId") Object download(long trackId, int retry);
    }
    public interface UnsupportedApi {
        @Query("trackId") Object objectTrack(Object trackId);
        Object unannotated(String trackId, long number);
        @Query("id") Object wrongName(String id);
    }
    public interface AmbiguousApi {
        @Query("trackId") Object byString(String id);
        @Path("trackId") Object byLong(long id);
    }
    public interface DuplicateParameterApi {
        Object both(@Query("trackId") String first,
                    @Path("trackId") String second);
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static Object proxy(Class<?>[] interfaces, InvocationHandler handler) {
        return Proxy.newProxyInstance(
            PublisherTrackIdProxyContractTest.class.getClassLoader(),
            interfaces, handler);
    }

    private static void inheritedMethodAndOriginalInvocationOnce() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        AtomicReference<Method> seenMethod = new AtomicReference<>();
        AtomicReference<Object[]> seenArguments = new AtomicReference<>();
        InvocationHandler original = (instance, method, arguments) -> {
            calls.incrementAndGet();
            seenMethod.set(method);
            seenArguments.set(arguments.clone());
            return null;
        };
        ClassLoader loader = FileInfoApi.class.getClassLoader();
        Class<?>[] interfaces = { FileInfoApi.class, ExtraApi.class };
        Object instance = Proxy.newProxyInstance(loader, interfaces, original);

        check(FileInfoApi.class.getDeclaredMethod("format", String.class) != null,
            "DECLARED_METHOD_PRESENT");
        for (Method method : FileInfoApi.class.getDeclaredMethods())
            check(!"lookup".equals(method.getName()),
                "PARENT_METHOD_MUST_NOT_APPEAR_IN_GET_DECLARED_METHODS");

        PublisherTrackIdProxyContract.Inspection result =
            PublisherTrackIdProxyContract.inspect(
                instance, FileInfoApi.class, loader, interfaces);
        check(result != null && result.method != null,
            "INHERITED_TRACKID_METHOD_SELECTED");
        check(result.method.getDeclaringClass() == BaseFileInfoApi.class,
            "EXACT_PARENT_DECLARING_INTERFACE");
        check(result.inherited, "INHERITED_METHOD_RECORDED");
        check(result.trackArgumentIndex == 0, "EXACT_TRACK_ARGUMENT_INDEX");
        check("QUERY".equals(result.annotationKind), "QUERY_ANNOTATION_RECORDED");
        check("trackId".equals(result.annotationValue), "EXACT_QUERY_VALUE");
        check("java.lang.String".equals(result.parameterTypeName),
            "EXACT_STRING_PARAMETER_TYPE");
        check(result.apiImplemented, "API_ROOT_IMPLEMENTED");
        check(result.proxyInterfacesMatchRequested, "ACTUAL_PROXY_INTERFACE_SET_MATCHES");
        check(result.directInterfaceNames.size() == 2,
            "ALL_DIRECT_PROXY_INTERFACES_RECORDED");
        check(result.proxyLoaderMatchesRequested, "PROXY_USES_REQUESTED_CLASSLOADER");
        check(result.apiLoaderMatchesRequested, "API_USES_REQUESTED_CLASSLOADER");
        check(result.apiLoaderMatchesProxy, "API_AND_PROXY_CLASSLOADERS_MATCH");

        ((BaseFileInfoApi) instance).lookup("144530503", "unchanged");
        check(calls.get() == 1, "ORIGINAL_PROXY_HANDLER_CALLED_EXACTLY_ONCE");
        check(result.method.equals(seenMethod.get()),
            "SELECTED_METHOD_EQUALS_REAL_PROXY_INVOKED_METHOD");
        check("144530503".equals(seenArguments.get()[result.trackArgumentIndex]),
            "ONLY_ANNOTATED_TRACKID_ARGUMENT_IS_READ");
        check("unchanged".equals(seenArguments.get()[1]),
            "OTHER_ARGUMENT_PASSED_UNCHANGED");
    }

    private static void inheritedThroughProxySubinterface() {
        ClassLoader loader = ExtendedFileInfoApi.class.getClassLoader();
        Class<?>[] interfaces = { ExtendedFileInfoApi.class };
        Object instance = proxy(interfaces, (p, m, a) -> null);
        PublisherTrackIdProxyContract.Inspection result =
            PublisherTrackIdProxyContract.inspect(
                instance, FileInfoApi.class, loader, interfaces);
        check(result.method != null && result.inherited,
            "PARENT_METHOD_FOUND_THROUGH_PROXY_SUBINTERFACE");
    }

    private static void exactPathAndNumericType() {
        ClassLoader loader = DownloadInfoApi.class.getClassLoader();
        Class<?>[] interfaces = { DownloadInfoApi.class };
        Object instance = proxy(interfaces, (p, m, a) -> null);
        PublisherTrackIdProxyContract.Inspection result =
            PublisherTrackIdProxyContract.inspect(
                instance, DownloadInfoApi.class, loader, interfaces);
        check(result.method != null, "PATH_TRACKID_METHOD_SELECTED");
        check("PATH".equals(result.annotationKind), "PATH_ANNOTATION_RECORDED");
        check(result.trackArgumentIndex == 0, "PATH_ARGUMENT_INDEX");
        check("long".equals(result.parameterTypeName), "LONG_PARAMETER_TYPE");
        check(!result.inherited, "DIRECT_METHOD_RECORDED_AS_DECLARED");
    }

    private static void rejectUnsupportedAndUnannotatedArguments() {
        ClassLoader loader = UnsupportedApi.class.getClassLoader();
        Class<?>[] interfaces = { UnsupportedApi.class };
        Object instance = proxy(interfaces, (p, m, a) -> null);
        PublisherTrackIdProxyContract.Inspection result =
            PublisherTrackIdProxyContract.inspect(
                instance, UnsupportedApi.class, loader, interfaces);
        check(result.method == null, "UNSUPPORTED_OBJECT_TRACKID_NOT_CAPTURED");
        check(result.unsupportedTrackIdParameter,
            "UNSUPPORTED_ANNOTATED_TYPE_IS_EXPLICIT");
    }

    private static void rejectAmbiguousMethodsAndParameters() {
        ClassLoader loader = AmbiguousApi.class.getClassLoader();
        Class<?>[] interfaces = { AmbiguousApi.class };
        Object instance = proxy(interfaces, (p, m, a) -> null);
        PublisherTrackIdProxyContract.Inspection result =
            PublisherTrackIdProxyContract.inspect(
                instance, AmbiguousApi.class, loader, interfaces);
        check(result.method == null && result.ambiguous,
            "MULTIPLE_TRACKID_METHODS_FAIL_CLOSED");

        Class<?>[] duplicateInterfaces = { DuplicateParameterApi.class };
        Object duplicate = proxy(duplicateInterfaces, (p, m, a) -> null);
        PublisherTrackIdProxyContract.Inspection duplicateResult =
            PublisherTrackIdProxyContract.inspect(
                duplicate, DuplicateParameterApi.class, loader, duplicateInterfaces);
        check(duplicateResult.method == null && duplicateResult.ambiguous,
            "MULTIPLE_TRACKID_PARAMETERS_FAIL_CLOSED");
    }

    private static void rejectWrongProxyInterfaceAndLoaderMetadata() {
        ClassLoader loader = FileInfoApi.class.getClassLoader();
        Class<?>[] actual = { FileInfoApi.class };
        Object instance = proxy(actual, (p, m, a) -> null);
        Class<?>[] wrongRequested = { ExtraApi.class };
        PublisherTrackIdProxyContract.Inspection wrongArray =
            PublisherTrackIdProxyContract.inspect(
                instance, FileInfoApi.class, loader, wrongRequested);
        check(wrongArray.method == null
            && !wrongArray.proxyInterfacesMatchRequested,
            "REQUESTED_PROXY_INTERFACE_SET_MUST_MATCH_ACTUAL");

        PublisherTrackIdProxyContract.Inspection wrongApi =
            PublisherTrackIdProxyContract.inspect(
                instance, DownloadInfoApi.class, loader, actual);
        check(wrongApi.method == null && !wrongApi.apiImplemented,
            "UNRELATED_API_CANNOT_CLAIM_PROXY");
    }

    public static void main(String[] args) throws Exception {
        inheritedMethodAndOriginalInvocationOnce();
        inheritedThroughProxySubinterface();
        exactPathAndNumericType();
        rejectUnsupportedAndUnannotatedArguments();
        rejectAmbiguousMethodsAndParameters();
        rejectWrongProxyInterfaceAndLoaderMetadata();
        System.out.println("ISSUER_PROXY_INHERITED_DECLARED_ANNOTATION_CLASSLOADER_PASS");
    }
}
