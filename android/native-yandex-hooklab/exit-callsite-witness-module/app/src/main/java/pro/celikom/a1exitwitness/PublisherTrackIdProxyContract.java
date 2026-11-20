package pro.celikom.a1exitwitness;

import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Exact runtime contract for a publisher Retrofit Java proxy.
 *
 * The service interface may inherit its annotated endpoint from a parent
 * interface. Inspect the actual proxy interface graph and retain only a
 * uniquely annotated Query/Path("trackId") parameter with a supported type.
 * Never infer a track ID from an unannotated or arbitrary argument.
 */
final class PublisherTrackIdProxyContract {
    static final class AnnotatedParameter {
        final String declaringInterfaceName;
        final String methodName;
        final String annotationKind;
        final String annotationValue;
        final String parameterTypeName;
        final String declaringLoaderName;
        final boolean inherited;

        AnnotatedParameter(Method method, int index, String kind,
                String value, boolean inherited) {
            declaringInterfaceName = method.getDeclaringClass().getName();
            methodName = method.getName();
            annotationKind = kind;
            annotationValue = value;
            parameterTypeName = method.getParameterTypes()[index].getName();
            ClassLoader loader = method.getDeclaringClass().getClassLoader();
            declaringLoaderName = loaderName(loader);
            this.inherited = inherited;
        }
    }

    static final class Inspection {
        final Method method;
        final int trackArgumentIndex;
        final String annotationKind;
        final String annotationValue;
        final String parameterTypeName;
        final boolean inherited;
        final boolean apiImplemented;
        final boolean proxyInterfacesMatchRequested;
        final boolean ambiguous;
        final boolean unsupportedTrackIdParameter;
        final boolean metadataComplete;
        final int relevantInterfaceCount;
        final List<String> directInterfaceNames;
        final List<AnnotatedParameter> annotatedParameters;
        final String requestedProxyLoaderName;
        final String proxyClassLoaderName;
        final String apiClassLoaderName;
        final boolean proxyLoaderMatchesRequested;
        final boolean apiLoaderMatchesRequested;
        final boolean apiLoaderMatchesProxy;

        Inspection(Method method, int index, String kind, String value,
                String parameterType, boolean inherited, boolean apiImplemented,
                boolean interfacesMatch, boolean ambiguous,
                boolean unsupported, boolean metadataComplete,
                int relevantInterfaceCount, List<String> directInterfaceNames,
                List<AnnotatedParameter> annotatedParameters,
                ClassLoader requestedLoader, ClassLoader proxyLoader,
                ClassLoader apiLoader) {
            this.method = method;
            trackArgumentIndex = index;
            annotationKind = kind;
            annotationValue = value;
            parameterTypeName = parameterType;
            this.inherited = inherited;
            this.apiImplemented = apiImplemented;
            proxyInterfacesMatchRequested = interfacesMatch;
            this.ambiguous = ambiguous;
            unsupportedTrackIdParameter = unsupported;
            this.metadataComplete = metadataComplete;
            this.relevantInterfaceCount = relevantInterfaceCount;
            this.directInterfaceNames = directInterfaceNames;
            this.annotatedParameters = annotatedParameters;
            requestedProxyLoaderName = loaderName(requestedLoader);
            proxyClassLoaderName = loaderName(proxyLoader);
            apiClassLoaderName = loaderName(apiLoader);
            proxyLoaderMatchesRequested = requestedLoader == proxyLoader;
            apiLoaderMatchesRequested = requestedLoader == apiLoader;
            apiLoaderMatchesProxy = apiLoader == proxyLoader;
        }
    }

    private static final class AnnotationValue {
        final String kind;
        final String value;
        AnnotationValue(String kind, String value) {
            this.kind = kind;
            this.value = value;
        }
    }

    static Inspection inspect(Object proxy, Class<?> apiRoot,
            ClassLoader requestedProxyLoader, Class<?>[] requestedInterfaces) {
        if (proxy == null || apiRoot == null || !apiRoot.isInterface()
                || !Proxy.isProxyClass(proxy.getClass())) return null;

        Class<?> proxyClass = proxy.getClass();
        ClassLoader proxyLoader = proxyClass.getClassLoader();
        ClassLoader apiLoader = apiRoot.getClassLoader();
        Class<?>[] directInterfaces = proxyClass.getInterfaces();
        boolean interfacesMatch = sameInterfaceSet(
            directInterfaces, requestedInterfaces);
        boolean apiImplemented = apiRoot.isInstance(proxy);

        List<String> interfaceNames = new ArrayList<>();
        for (Class<?> type : directInterfaces) {
            if (interfaceNames.size() < 16 && type != null)
                interfaceNames.add(type.getName());
        }

        LinkedHashMap<Method, Boolean> methods = new LinkedHashMap<>();
        int relevantInterfaces = 0;
        boolean metadataComplete = true;
        for (Class<?> direct : directInterfaces) {
            if (direct == null || !direct.isInterface()
                    || !apiRoot.isAssignableFrom(direct)) continue;
            relevantInterfaces++;
            try {
                for (Method method : direct.getMethods()) {
                    Class<?> declaring = method.getDeclaringClass();
                    if (!declaring.isInterface()
                            || !declaring.isAssignableFrom(direct)) continue;
                    boolean inherited = declaring != direct;
                    Boolean previous = methods.get(method);
                    methods.put(method, previous == null
                        ? inherited : previous && inherited);
                }
            } catch (Throwable ignored) {
                metadataComplete = false;
            }
        }

        List<AnnotatedParameter> annotated = new ArrayList<>();
        Method selected = null;
        int selectedIndex = -1;
        String selectedKind = null;
        String selectedValue = null;
        String selectedType = null;
        boolean selectedInherited = false;
        boolean ambiguous = false;
        boolean unsupported = false;

        for (Map.Entry<Method, Boolean> entry : methods.entrySet()) {
            Method method = entry.getKey();
            boolean inherited = entry.getValue();
            Class<?>[] parameterTypes;
            Annotation[][] parameterAnnotations;
            try {
                parameterTypes = method.getParameterTypes();
                parameterAnnotations = method.getParameterAnnotations();
            } catch (Throwable ignored) {
                metadataComplete = false;
                continue;
            }
            if (parameterTypes.length != parameterAnnotations.length) {
                metadataComplete = false;
                continue;
            }

            int methodTrackIndex = -1;
            String methodTrackKind = null;
            String methodTrackValue = null;
            String methodTrackType = null;
            boolean methodAmbiguous = false;

            for (int i = 0; i < parameterAnnotations.length; i++) {
                for (Annotation annotation : parameterAnnotations[i]) {
                    AnnotationValue value = readAnnotationValue(annotation);
                    if (value == null) continue;
                    if (annotated.size() < 32)
                        annotated.add(new AnnotatedParameter(
                            method, i, value.kind, value.value, inherited));
                    if (!"trackId".equals(value.value)) continue;
                    if (!supportedTrackIdType(parameterTypes[i])) {
                        unsupported = true;
                        continue;
                    }
                    if (methodTrackIndex != -1) {
                        methodAmbiguous = true;
                        continue;
                    }
                    methodTrackIndex = i;
                    methodTrackKind = value.kind;
                    methodTrackValue = value.value;
                    methodTrackType = parameterTypes[i].getName();
                }
            }

            if (methodAmbiguous) {
                ambiguous = true;
                continue;
            }
            if (methodTrackIndex >= 0) {
                if (selected != null && !selected.equals(method)) {
                    ambiguous = true;
                    continue;
                }
                selected = method;
                selectedIndex = methodTrackIndex;
                selectedKind = methodTrackKind;
                selectedValue = methodTrackValue;
                selectedType = methodTrackType;
                selectedInherited = inherited;
            }
        }

        boolean usable = apiImplemented && interfacesMatch
            && relevantInterfaces > 0 && metadataComplete
            && !ambiguous && !unsupported && selected != null;
        return new Inspection(
            usable ? selected : null,
            usable ? selectedIndex : -1,
            usable ? selectedKind : null,
            usable ? selectedValue : null,
            usable ? selectedType : null,
            usable && selectedInherited,
            apiImplemented, interfacesMatch, ambiguous, unsupported,
            metadataComplete, relevantInterfaces, interfaceNames, annotated,
            requestedProxyLoader, proxyLoader, apiLoader);
    }

    private static AnnotationValue readAnnotationValue(Annotation annotation) {
        if (annotation == null) return null;
        String name = annotation.annotationType().getName();
        String kind;
        if ("retrofit2.http.Query".equals(name)) kind = "QUERY";
        else if ("retrofit2.http.Path".equals(name)) kind = "PATH";
        else return null;
        try {
            Object value = annotation.annotationType()
                .getMethod("value").invoke(annotation);
            return value instanceof String
                ? new AnnotationValue(kind, (String) value) : null;
        } catch (Throwable ignored) {
            return null;
        }
    }

    private static boolean supportedTrackIdType(Class<?> type) {
        return type == String.class || type == long.class || type == Long.class
            || type == int.class || type == Integer.class;
    }

    private static boolean sameInterfaceSet(Class<?>[] actual, Class<?>[] requested) {
        if (actual == null || requested == null || actual.length != requested.length)
            return false;
        boolean[] used = new boolean[actual.length];
        for (Class<?> expected : requested) {
            boolean found = false;
            for (int i = 0; i < actual.length; i++) {
                if (!used[i] && actual[i] == expected) {
                    used[i] = true;
                    found = true;
                    break;
                }
            }
            if (!found) return false;
        }
        return true;
    }

    private static String loaderName(ClassLoader loader) {
        return loader == null ? "BOOTSTRAP" : loader.getClass().getName();
    }

    private PublisherTrackIdProxyContract() {}
}
