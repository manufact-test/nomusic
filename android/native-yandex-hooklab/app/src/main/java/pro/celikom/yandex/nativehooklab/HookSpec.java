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
    // Exact signed DEX interface Lemb;->t(Ldmb;)V and remove()V, factory
    // Lkvs;->A(Lzcb;Lgmb;)Lemb;. Source class names are intentionally pinned;
    // do not hook approximate/overloaded methods or infer active decoder.
    public static final String[] SOURCE_IMPLEMENTORS={
            "alt","chg","ero","ocv","ojz","t67","t6f","xq7"
    };
    public static Method findSourceFactory(ClassLoader loader)
            throws ClassNotFoundException, NoSuchMethodException {
        Class<?> holder=Class.forName("kvs",false,loader);
        Class<?> first=Class.forName("zcb",false,loader);
        Class<?> second=Class.forName("gmb",false,loader);
        Class<?> result=Class.forName("emb",false,loader);
        for(Method method:holder.getDeclaredMethods()) {
            if("A".equals(method.getName())
                    && !Modifier.isAbstract(method.getModifiers())
                    && method.getReturnType()==result
                    && method.getParameterCount()==2
                    && method.getParameterTypes()[0]==first
                    && method.getParameterTypes()[1]==second) return method;
        }
        throw new NoSuchMethodException("EXACT_LEMB_FACTORY_UNAVAILABLE");
    }

    public static Method findSourceLifecycle(ClassLoader loader,String implementor,
                                             String operation)
            throws ClassNotFoundException, NoSuchMethodException {
        boolean pinned=false;
        for(String name:SOURCE_IMPLEMENTORS)if(name.equals(implementor))pinned=true;
        if(!pinned || (!"t".equals(operation)&&!"remove".equals(operation)))
            throw new NoSuchMethodException("NOT_A_PINNED_LEMB_OPERATION");
        Class<?> contract=Class.forName("emb",false,loader);
        Class<?> holder=Class.forName(implementor,false,loader);
        if(!contract.isAssignableFrom(holder))
            throw new NoSuchMethodException("NOT_AN_EXACT_LEMB_IMPLEMENTOR");
        Class<?> parameter="t".equals(operation)
                ?Class.forName("dmb",false,loader):null;
        for(Method method:holder.getDeclaredMethods()) {
            if(method.getName().equals(operation)
                    && !Modifier.isStatic(method.getModifiers())
                    && !Modifier.isAbstract(method.getModifiers())
                    && method.getReturnType()==void.class
                    && method.getParameterCount()==(parameter==null?0:1)
                    && (parameter==null || method.getParameterTypes()[0]==parameter))
                return method;
        }
        throw new NoSuchMethodException("EXACT_LEMB_LIFECYCLE_UNAVAILABLE");
    }


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
