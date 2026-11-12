// Diagnostic-only JDI witness. Attaches exclusively to a disposable, debuggable
// CELIKOM Android13 clone. No SDK/app bytecode rewrites and no exception suppression.
// Third-party class names and method locations are never printed.
package pro.celikom.a1diagnostic;

import com.sun.jdi.Bootstrap;
import com.sun.jdi.Location;
import com.sun.jdi.Method;
import com.sun.jdi.ThreadReference;
import com.sun.jdi.VirtualMachine;
import com.sun.jdi.connect.AttachingConnector;
import com.sun.jdi.connect.Connector;
import com.sun.jdi.event.Event;
import com.sun.jdi.event.EventSet;
import com.sun.jdi.event.ExceptionEvent;
import com.sun.jdi.event.MethodEntryEvent;
import com.sun.jdi.event.VMDeathEvent;
import com.sun.jdi.event.VMDisconnectEvent;
import com.sun.jdi.request.EventRequest;
import com.sun.jdi.request.ExceptionRequest;
import com.sun.jdi.request.MethodEntryRequest;
import com.sun.jdi.request.EventRequestManager;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.TimeUnit;

public final class ExactCatchJdi {
    private ExactCatchJdi() { }

    private static String family(String className) {
        if (className.startsWith("com.yandex.metrica.")) return "SDK_LEGACY";
        if (className.startsWith("io.appmetrica.")) return "SDK_MODERN";
        if (className.startsWith("java.") || className.startsWith("javax.")) return "JAVA";
        if (className.startsWith("android.") || className.startsWith("dalvik.")) return "ANDROID";
        return "OTHER";
    }

    public static void main(String[] args) {
        if (args.length != 5 || !args[0].matches("[0-9]{4,5}")) {
            System.out.println("JDI_RESULT {\"status\":\"INVALID_INPUT\"}");
            System.exit(2);
        }
        String port = args[0], targetClass = args[1], targetMethod = args[2];
        // One exact privately verified original DEX overload; never print this signature.
        String targetArgs = args[3];
        Path output = Path.of(args[4]);
        VirtualMachine vm = null;
        int entries = 0, exactCatch = 0, otherCatch = 0, attempts = 0;
        String status = "UNKNOWN";
        try {
            if (!targetClass.matches("[A-Za-z_$][A-Za-z0-9_$.]*")
                    || !targetMethod.matches("[A-Za-z_$][A-Za-z0-9_$]*")
                    || targetArgs.length() > 512) throw new IllegalArgumentException();
            Files.createDirectories(output.getParent());
            AttachingConnector connector = null;
            for (AttachingConnector c : Bootstrap.virtualMachineManager().attachingConnectors()) {
                if ("com.sun.jdi.SocketAttach".equals(c.name())) {
                    connector = c;
                    break;
                }
            }
            if (connector == null) throw new IllegalStateException();
            Map<String, Connector.Argument> connection = connector.defaultArguments();
            connection.get("hostname").setValue("127.0.0.1");
            connection.get("port").setValue(port);
            connection.get("timeout").setValue("15000");
            vm = connector.attach(connection);
            EventRequestManager erm = vm.eventRequestManager();
            MethodEntryRequest methodEntry = erm.createMethodEntryRequest();
            methodEntry.addClassFilter(targetClass);
            methodEntry.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
            methodEntry.enable();
            Set<Long> threadIds = new HashSet<>();
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(68);
            vm.resume();
            status = "ATTACHED";
            while (System.nanoTime() < deadline && exactCatch < 8) {
                EventSet set = vm.eventQueue().remove(1500L);
                if (set == null) continue;
                try {
                    for (Event event : set) {
                        if (event instanceof MethodEntryEvent entry) {
                            Method m = entry.method();
                            if (!m.declaringType().name().equals(targetClass)
                                    || !m.name().equals(targetMethod)
                                    || !String.join(",", m.argumentTypeNames()).equals(targetArgs)) continue;
                            entries++;
                            ThreadReference thread = entry.thread();
                            if (threadIds.add(thread.uniqueID())) {
                                ExceptionRequest request = erm.createExceptionRequest(null, true, false);
                                request.addThreadFilter(thread);
                                request.setSuspendPolicy(EventRequest.SUSPEND_EVENT_THREAD);
                                request.enable();
                            }
                        } else if (event instanceof ExceptionEvent caught) {
                            Location handler = caught.catchLocation();
                            if (handler == null || !handler.declaringType().name().equals(targetClass)
                                    || !handler.method().name().equals(targetMethod)
                                    || !String.join(",", handler.method().argumentTypeNames()).equals(targetArgs)) {
                                otherCatch++;
                                continue;
                            }
                            exactCatch++;
                            String thrownFamily = family(caught.location().declaringType().name());
                            String exceptionFamily = family(caught.exception().referenceType().name());
                            long callerPc = -1;
                            try {
                                for (var frame : caught.thread().frames()) {
                                    Location frameAt = frame.location();
                                    if (frameAt.declaringType().name().equals(targetClass)
                                            && frameAt.method().name().equals(targetMethod)
                                            && String.join(",", frameAt.method().argumentTypeNames()).equals(targetArgs)) {
                                        callerPc = frameAt.codeIndex();
                                        break;
                                    }
                                }
                            } catch (Exception ignored) { }
                            // This file is inside a transient private CI runner only.
                            // No proprietary location, name, stack, or message is logged.
                            String witness = callerPc + "|" + thrownFamily + "|" + exceptionFamily + "\n";
                            Files.writeString(output, witness,
                                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
                        } else if (event instanceof VMDeathEvent || event instanceof VMDisconnectEvent) {
                            status = "VM_EXIT";
                        }
                        attempts++;
                    }
                } finally {
                    set.resume();
                }
                if ("VM_EXIT".equals(status)) break;
            }
        } catch (Exception exception) {
            status = exactCatch > 0 ? "PARTIAL" : "ATTACH_OR_RUNTIME_FAILURE";
        } finally {
            if (vm != null) {
                try { vm.dispose(); } catch (Exception ignored) { }
            }
        }
        System.out.println("JDI_RESULT {\"status\":\"" + status
            + "\",\"exact_method_entries\":" + Math.min(entries, 99)
            + ",\"exact_caught_events\":" + Math.min(exactCatch, 8)
            + ",\"other_caught_events_bounded\":" + Math.min(otherCatch, 999)
            + ",\"sdk_modified\":false,\"exception_suppressed\":false}");
    }
}
