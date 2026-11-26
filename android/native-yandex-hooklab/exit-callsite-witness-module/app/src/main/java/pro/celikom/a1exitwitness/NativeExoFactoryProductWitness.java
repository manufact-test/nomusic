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

    static Resolution resolve(Object factory, Class<?> sourceType,
            Class<?>... sourceContracts) {
        if (factory == null || sourceType == null)
            return new Resolution(null, 0);
        Map<String, Method> candidates = new LinkedHashMap<>();
        for (Class<?> type = factory.getClass(); type != null && type != Object.class;
                type = type.getSuperclass()) {
            for (Method method : type.getDeclaredMethods())
                addCandidate(candidates, method, sourceType, sourceContracts);
        }
        collectDefaultInterfaceMethods(factory.getClass(), sourceType,
            sourceContracts, candidates, new HashSet<Class<?>>());
        if (candidates.size() != 1)
            return new Resolution(null, candidates.size());
        return new Resolution(candidates.values().iterator().next(), 1);
    }

    private static void collectDefaultInterfaceMethods(Class<?> type,
            Class<?> sourceType, Class<?>[] sourceContracts,
            Map<String, Method> candidates, Set<Class<?>> visited) {
        if (type == null) return;
        for (Class<?> iface : type.getInterfaces()) {
            if (!visited.add(iface)) continue;
            for (Method method : iface.getDeclaredMethods()) {
                if (!Modifier.isAbstract(method.getModifiers()))
                    addCandidate(candidates, method, sourceType, sourceContracts);
            }
            collectDefaultInterfaceMethods(iface, sourceType, sourceContracts,
                candidates, visited);
        }
        collectDefaultInterfaceMethods(type.getSuperclass(), sourceType,
            sourceContracts, candidates, visited);
    }

    private static void addCandidate(Map<String, Method> candidates,
            Method method, Class<?> sourceType, Class<?>[] sourceContracts) {
        int modifiers = method.getModifiers();
        if (method.getParameterTypes().length != 0
                || Modifier.isStatic(modifiers)
                || Modifier.isAbstract(modifiers)
                || method.isBridge() || method.isSynthetic()
                || !isAllowedSourceReturn(method.getReturnType(), sourceType,
                    sourceContracts))
            return;
        String key = method.getName() + "()";
        Method prior = candidates.get(key);
        if (prior == null || prior.getDeclaringClass()
                .isAssignableFrom(method.getDeclaringClass()))
            candidates.put(key, method);
    }

    private static boolean isAllowedSourceReturn(Class<?> returnType,
            Class<?> sourceType, Class<?>[] sourceContracts) {
        if (sourceType.isAssignableFrom(returnType)) return true;
        if (returnType == Object.class || !returnType.isAssignableFrom(sourceType))
            return false;
        for (Class<?> contract : sourceContracts) {
            if (contract != null && contract.isAssignableFrom(returnType))
                return true;
        }
        return false;
    }
}
