package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

/**
 * Resolves the exact zero-argument product method on the factory instance
 * returned by the signed original Exo descriptor factory. The caller hooks
 * this method only after the factory instance has been linked to that exact
 * descriptor. Ambiguous or absent methods are rejected.
 */
final class NativeExoFactoryProductWitness {
    static final class Resolution {
        final Method method;
        final int candidateCount;

        Resolution(Method method, int candidateCount) {
            this.method = method;
            this.candidateCount = candidateCount;
        }
    }

    private NativeExoFactoryProductWitness() { }

    static Resolution resolve(Object factory, Class<?> sourceType) {
        if (factory == null || sourceType == null)
            return new Resolution(null, 0);
        Map<String, Method> candidates = new LinkedHashMap<>();
        for (Class<?> type = factory.getClass(); type != null && type != Object.class;
                type = type.getSuperclass()) {
            for (Method method : type.getDeclaredMethods())
                addCandidate(candidates, method, sourceType);
        }
        collectDefaultInterfaceMethods(factory.getClass(), sourceType,
            candidates, new HashSet<Class<?>>());
        if (candidates.size() != 1)
            return new Resolution(null, candidates.size());
        return new Resolution(candidates.values().iterator().next(), 1);
    }

    private static void collectDefaultInterfaceMethods(Class<?> type,
            Class<?> sourceType, Map<String, Method> candidates,
            Set<Class<?>> visited) {
        if (type == null) return;
        for (Class<?> iface : type.getInterfaces()) {
            if (!visited.add(iface)) continue;
            for (Method method : iface.getDeclaredMethods()) {
                if (!Modifier.isAbstract(method.getModifiers()))
                    addCandidate(candidates, method, sourceType);
            }
            collectDefaultInterfaceMethods(iface, sourceType, candidates, visited);
        }
        collectDefaultInterfaceMethods(type.getSuperclass(), sourceType,
            candidates, visited);
    }

    private static void addCandidate(Map<String, Method> candidates,
            Method method, Class<?> sourceType) {
        int modifiers = method.getModifiers();
        if (method.getParameterTypes().length != 0
                || Modifier.isStatic(modifiers)
                || Modifier.isAbstract(modifiers)
                || method.isBridge() || method.isSynthetic()
                || !sourceType.isAssignableFrom(method.getReturnType()))
            return;
        String key = method.getName() + "()";
        Method prior = candidates.get(key);
        if (prior == null || prior.getDeclaringClass()
                .isAssignableFrom(method.getDeclaringClass()))
            candidates.put(key, method);
    }
}
