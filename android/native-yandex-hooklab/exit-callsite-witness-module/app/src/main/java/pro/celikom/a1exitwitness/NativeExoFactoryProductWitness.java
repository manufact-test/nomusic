package pro.celikom.a1exitwitness;

import java.lang.reflect.Method;
import java.lang.reflect.Field;
import java.util.ArrayList;
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

    /**
     * A signed original c.for result is an obfuscated wrapper, not a direct
     * DataSource factory. Require one Java identity reference path (<=2 fields)
     * to the exact original $b.for receiver. Never call vendor methods.
     */
    static boolean uniquelyReferencesNestedFactory(Object outer,Object nested) {
        if(outer==null || nested==null || outer==nested)return false;
        ClassLoader loader=nested.getClass().getClassLoader();
        if(loader==null || outer.getClass().getClassLoader()!=loader)return false;
        ArrayList<Object> first=new ArrayList<>();
        if(!collectReferences(outer,loader,first))return false;
        int matches=0;
        for(Object child:first) {
            if(child==nested)matches++;
            if(child==null || child==outer || child==nested
                    || child.getClass().getClassLoader()!=loader)continue;
            ArrayList<Object> second=new ArrayList<>();
            if(!collectReferences(child,loader,second))return false;
            for(Object grandchild:second)if(grandchild==nested)matches++;
            if(matches>1)return false;
        }
        return matches==1;
    }

    private static boolean collectReferences(Object obj,ClassLoader loader,
            ArrayList<Object> values) {
        int examined=0;
        for(Class<?> type=obj.getClass();type!=null && type!=Object.class;
                type=type.getSuperclass()) {
            if(type.getClassLoader()!=loader)break;
            for(Field field:type.getDeclaredFields()) {
                if(Modifier.isStatic(field.getModifiers()) || field.isSynthetic()
                        || field.getType().isPrimitive())continue;
                if(++examined>32)return false;
                try {
                    field.setAccessible(true);
                    Object value=field.get(obj);
                    if(value!=null && value.getClass().getClassLoader()==loader) {
                        if(values.size()>=32)return false;
                        values.add(value);
                    }
                } catch(Throwable ignored) {return false;}
            }
        }
        return true;
    }
}
