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
