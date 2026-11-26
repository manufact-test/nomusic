package pro.celikom.a1exitwitness;

public final class NativeExoFactoryProductWitnessTest {
    static final class DataSource { }
    static final class UniqueFactory {
        private DataSource makeSource() { return new DataSource(); }
    }
    static class BaseFactory {
        protected DataSource makeSource() { return new DataSource(); }
    }
    static final class InheritedFactory extends BaseFactory { }
    static class ParentFactory {
        protected DataSource makeSource() { return new DataSource(); }
    }
    static final class OverrideFactory extends ParentFactory {
        @Override protected DataSource makeSource() { return new DataSource(); }
    }
    static final class AmbiguousFactory {
        DataSource makeFirst() { return new DataSource(); }
        DataSource makeSecond() { return new DataSource(); }
    }
    static final class StaticOnlyFactory {
        static DataSource makeSource() { return new DataSource(); }
    }
    static final class WrongReturnFactory {
        Object makeSource() { return new DataSource(); }
    }
    interface DefaultFactory {
        default DataSource makeSource() { return new DataSource(); }
    }
    static final class DefaultOnlyFactory implements DefaultFactory { }

    private static int assertions;
    private static void check(boolean value, String label) {
        assertions++;
        if (!value) throw new AssertionError(label);
    }

    public static void main(String[] args) {
        NativeExoFactoryProductWitness.Resolution unique =
            NativeExoFactoryProductWitness.resolve(new UniqueFactory(), DataSource.class);
        check(unique.candidateCount == 1 && unique.method != null,
            "unique exact product method");
        check(unique.method.getName().equals("makeSource"), "unique method name");
        check(unique.method.getDeclaringClass() == UniqueFactory.class,
            "unique declaring class");

        NativeExoFactoryProductWitness.Resolution inherited =
            NativeExoFactoryProductWitness.resolve(new InheritedFactory(), DataSource.class);
        check(inherited.candidateCount == 1 && inherited.method != null,
            "inherited exact product method");
        check(inherited.method.getDeclaringClass() == BaseFactory.class,
            "inherited declaring class");

        NativeExoFactoryProductWitness.Resolution overridden =
            NativeExoFactoryProductWitness.resolve(new OverrideFactory(), DataSource.class);
        check(overridden.candidateCount == 1 && overridden.method != null,
            "overridden method deduplicated");
        check(overridden.method.getDeclaringClass() == OverrideFactory.class,
            "most specific override selected");

        NativeExoFactoryProductWitness.Resolution ambiguous =
            NativeExoFactoryProductWitness.resolve(new AmbiguousFactory(), DataSource.class);
        check(ambiguous.candidateCount == 2 && ambiguous.method == null,
            "ambiguous product methods rejected");

        NativeExoFactoryProductWitness.Resolution staticOnly =
            NativeExoFactoryProductWitness.resolve(new StaticOnlyFactory(), DataSource.class);
        check(staticOnly.candidateCount == 0 && staticOnly.method == null,
            "static method rejected");

        NativeExoFactoryProductWitness.Resolution wrongReturn =
            NativeExoFactoryProductWitness.resolve(new WrongReturnFactory(), DataSource.class);
        check(wrongReturn.candidateCount == 0 && wrongReturn.method == null,
            "non-source return rejected");

        NativeExoFactoryProductWitness.Resolution defaultMethod =
            NativeExoFactoryProductWitness.resolve(new DefaultOnlyFactory(), DataSource.class);
        check(defaultMethod.candidateCount == 1 && defaultMethod.method != null,
            "exact default interface product method");
        check(defaultMethod.method.getDeclaringClass() == DefaultFactory.class,
            "default interface method selected");

        System.out.println("NATIVE_EXO_FACTORY_PRODUCT_WITNESS_PASS assertions=" + assertions);
    }
}
