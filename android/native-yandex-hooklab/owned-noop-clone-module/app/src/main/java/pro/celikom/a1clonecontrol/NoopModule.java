package pro.celikom.a1clonecontrol;
import io.github.libxposed.api.XposedModule;
/** No hooking, no network, no data, no changes to vendor process. */
public final class NoopModule extends XposedModule {
    @Override public void onModuleLoaded(ModuleLoadedParam param) { }
}
