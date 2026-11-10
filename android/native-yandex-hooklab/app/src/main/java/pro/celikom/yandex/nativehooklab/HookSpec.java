package pro.celikom.yandex.nativehooklab;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Version-locked verified structural reflection contract from native Yandex
 * 2026.10.3 #170gpr code 24026531, NOT a general-purpose injection engine.
 */
public final class HookSpec {
    public static final String TARGET_PACKAGE = "ru.yandex.music";
    public static final String TARGET_VERSION = "2026.10.3 #170gpr";
    public static final long TARGET_VERSION_CODE = 24026531L;
    public static final String OBFUSCATED_CONVERTER = "sw7";
    public static final String FILE_DTO =
            "com.yandex.music.shared.player.content.remote.fileinfo.FileInfoDto";
    public static final String OLD_FILE_DTO =
            "com.yandex.music.shared.player.content.remote.fileinfo.OldGetFileInfoDto";

    private HookSpec() {}

    public static boolean isApprovedHost(String packageName, String versionName, long versionCode) {
        return TARGET_PACKAGE.equals(packageName)
                && TARGET_VERSION.equals(versionName)
                && TARGET_VERSION_CODE == versionCode;
    }

    public static Method findConversion(ClassLoader loader, String name, String firstParameter)
            throws ClassNotFoundException, NoSuchMethodException {
        Class<?> holder = Class.forName(OBFUSCATED_CONVERTER, false, loader);
        Class<?> input = Class.forName(firstParameter, false, loader);
        Class<?> result = Class.forName("eed", false, loader);
        for (Method method : holder.getDeclaredMethods()) {
            if (method.getName().equals(name)
                    && Modifier.isStatic(method.getModifiers())
                    && method.getReturnType().equals(result)
                    && method.getParameterCount() == 2
                    && method.getParameterTypes()[0].equals(input)
                    && method.getParameterTypes()[1].equals(boolean.class)) {
                return method;
            }
        }
        throw new NoSuchMethodException(
                "No exact native converter found (refusing approximate hook): " + name);
    }
    /**
     * Two structural source-model conversions must resolve in the SAME host
     * classloader before either is hooked. Prefer Xposed PackageReady loader,
     * but tolerate split/classloader timing by retrying the verified host
     * Context loader; never mix types from unrelated loaders.
     */
    public static final class ResolvedPair {
        public final ClassLoader loader;
        public final Method modern;
        public final Method legacy;

        private ResolvedPair(ClassLoader loader, Method modern, Method legacy) {
            this.loader = loader;
            this.modern = modern;
            this.legacy = legacy;
        }
    }

    public static ResolvedPair findConversionPair(ClassLoader preferred, ClassLoader fallback)
            throws ClassNotFoundException, NoSuchMethodException {
        ClassLoader first = preferred != null ? preferred : fallback;
        if (first == null) throw new ClassNotFoundException("NO_NATIVE_HOST_CLASSLOADER");
        try {
            return new ResolvedPair(first,
                    findConversion(first, "y0", FILE_DTO),
                    findConversion(first, "z0", OLD_FILE_DTO));
        } catch (ClassNotFoundException | NoSuchMethodException miss) {
            if (fallback == null || fallback == first) throw miss;
            return new ResolvedPair(fallback,
                    findConversion(fallback, "y0", FILE_DTO),
                    findConversion(fallback, "z0", OLD_FILE_DTO));
        }
    }

    /**
     * Exact downstream model accessor observed in the signed #170gpr DEX:
     * Leed;->a()Ljava/lang/String;. No inference about contents: do not
     * read, persist or log the returned String.
     */
    public static Method findModelStringAccessor(ClassLoader loader)
            throws ClassNotFoundException, NoSuchMethodException {
        Class<?> model=Class.forName("eed", false, loader);
        Method method=model.getDeclaredMethod("a");
        if (Modifier.isStatic(method.getModifiers())
                || method.getParameterCount()!=0
                || !method.getReturnType().equals(String.class))
            throw new NoSuchMethodException("EXACT_MODEL_ACCESSOR_NOT_PRESENT");
        return method;
    }
}
