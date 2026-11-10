import java.lang.reflect.Method;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicReference;
import pro.celikom.yandex.nativehooklab.HookSpec;
import pro.celikom.yandex.nativehooklab.NativeOwnerConstructionWitness;
import pro.celikom.yandex.nativehooklab.NativeSourceDispatchWitness;

/** Only execution nesting / exact references: never player or decoder proof. */
public final class NativeOwnerConstructionWitnessTest {
    private static int tests;
    private static void yes(boolean condition,String why){
        tests++;
        if(!condition)throw new AssertionError(why+" #"+tests);
    }
    public static void main(String[] ignored)throws Exception{
        ClassLoader loader=NativeOwnerConstructionWitnessTest.class.getClassLoader();
        Method sourceBuilder=HookSpec.findLocvSourceBuilder(loader);
        yes(sourceBuilder.getDeclaringClass()==ocv.class
                &&sourceBuilder.getParameterCount()==0
                &&sourceBuilder.getReturnType()==void.class,
                "only exact signed ocv.i0 void source builder");

        NativeOwnerConstructionWitness w=new NativeOwnerConstructionWitness();
        ocv owner=new ocv();
        ero child=new ero();
        NativeOwnerConstructionWitness.Scope s=w.begin(owner);
        w.onConstructed(child);
        w.onConstructed(child); // 2-arg constructor delegates to 3-arg.
        NativeOwnerConstructionWitness.Match hit=w.finish(s,true);
        yes(hit!=null&&hit.owner==owner&&hit.child==child,
                "same object from delegating ctor counted once");
        yes(w.finish(s,true)==null,"duplicate exit rejected");
        s=w.begin(owner);
        w.onConstructed(new ero());
        w.onConstructed(new ero());
        yes(w.finish(s,true)==null,"multiple distinct children ambiguous");
        s=w.begin(owner);
        w.onConstructed(new ero());
        yes(w.finish(s,false)==null,"throwing original i0 rejects child");
        s=w.begin(owner);
        yes(w.finish(s,true)==null,"zero created sources cannot make evidence");

        // Constructor after the owner frame completes is orphaned.
        w.onConstructed(new ero());
        yes(w.snapshot().orphanConstructors>=1,
                "outside i0 constructor never backfills earlier owner");

        // Nested i0 does not mix different exact owners.
        ocv a=new ocv(), b=new ocv();
        ero outer=new ero(),inner=new ero();
        s=w.begin(a);
        w.onConstructed(outer);
        NativeOwnerConstructionWitness.Scope nested=w.begin(b);
        w.onConstructed(inner);
        NativeOwnerConstructionWitness.Match innerMatch=w.finish(nested,true);
        NativeOwnerConstructionWitness.Match outerMatch=w.finish(s,true);
        yes(innerMatch!=null&&innerMatch.owner==b&&innerMatch.child==inner,
                "inner owner sees only its own exact child");
        yes(outerMatch!=null&&outerMatch.owner==a&&outerMatch.child==outer,
                "outer frame restored without child confusion");

        // Reader construction on a second thread cannot be attributed to
        // the currently executing ocv.i0 frame on first thread.
        s=w.begin(a);
        CountDownLatch completed=new CountDownLatch(1);
        AtomicReference<Throwable> error=new AtomicReference<>();
        Thread other=new Thread(()->{
            try{w.onConstructed(new ero());}
            catch(Throwable ex){error.set(ex);}
            finally{completed.countDown();}
        });
        other.start();completed.await();other.join();
        yes(error.get()==null,"independent thread callback safe");
        yes(w.finish(s,true)==null,
                "ThreadLocal cannot attribute foreign-thread constructor");

        // Link only when the observed ocv factory object was actually
        // submitted to t(); then exact child, then exact reader.
        NativeSourceDispatchWitness source=new NativeSourceDispatchWitness();
        ocv factoryOwner=new ocv();
        ero builtChild=new ero();
        mb4 ownedReader=new mb4();
        source.onFactory(factoryOwner,100);
        source.onConstructed(builtChild,101);
        yes(!source.onOwnerChild(factoryOwner,builtChild,102),
                "factory alone is not evidence that owner was started");
        source.onLifecycleTBegin(factoryOwner,103);
        yes(source.onOwnerChild(factoryOwner,builtChild,104),
                "same owner entered t, constructed same nested child");
        source.onLifecycleTFinish(factoryOwner,true,105);
        source.onLifecycleTBegin(builtChild,106);
        yes(source.onOwnedReader(builtChild,ownedReader,107),
                "exact child carries exact reader");
        yes(!source.onCompletedReader(ownedReader,108),
                "reader result remains provisional while child t in flight");
        yes(source.onLifecycleTFinish(builtChild,true,109),
                "child t finally succeeded");
        yes(source.snapshot().parentChildLinks==1
                &&source.snapshot().parentOwnerReaderCompletions==1,
                "one strict owner→child→successful reader causal relation");

        NativeSourceDispatchWitness thrown=new NativeSourceDispatchWitness();
        ocv errorOwner=new ocv();
        ero errorChild=new ero();
        mb4 read=new mb4();
        thrown.onFactory(errorOwner,200);
        thrown.onConstructed(errorChild,201);
        thrown.onLifecycleTBegin(errorOwner,202);
        yes(thrown.onOwnerChild(errorOwner,errorChild,203),
                "owner link is provisional while t is pending");
        thrown.onLifecycleTFinish(errorOwner,false,204);
        thrown.onLifecycleTBegin(errorChild,205);
        thrown.onOwnedReader(errorChild,read,206);
        thrown.onCompletedReader(read,207);
        thrown.onLifecycleTFinish(errorChild,true,208);
        yes(thrown.snapshot().parentOwnerReaderCompletions==0,
                "throwing owner t never proves source selection by later child");

        // Late callback after remove or age expiry cannot re-link.
        source.onRemove(factoryOwner,110);
        yes(!source.onOwnerChild(factoryOwner,builtChild,111),
                "removed owner cannot relink a child");
        source.onFactory(factoryOwner,500);
        source.onLifecycleTBegin(factoryOwner,501);
        source.onLifecycleTFinish(factoryOwner,true,502);
        yes(!source.onOwnerChild(factoryOwner,builtChild,15103),
                "15s bound expires old child and owner");

        // Stress nested exact owner+child events and aborts with zero
        // persistent ThreadLocal references after each call.
        for(int i=0;i<10000;i++){
            ocv owner2=new ocv();
            ero child2=new ero();
            NativeOwnerConstructionWitness.Scope local=w.begin(owner2);
            w.onConstructed(child2);
            NativeOwnerConstructionWitness.Match m=w.finish(local,i%7!=0);
            yes((m!=null)==(i%7!=0),
                    "no child on exceptional i0 #"+i);
        }
        yes(w.snapshot().exactPairs==3+10000-1429,
                "only actual nonexceptional owner/source nested pairs");
        System.out.println("PASS: "+tests+
                " owner-constructor/reader provenance assertions; 10k nested"
                +" cases, cross-thread and exception rejection; SYNTHETIC ONLY");
    }
}
