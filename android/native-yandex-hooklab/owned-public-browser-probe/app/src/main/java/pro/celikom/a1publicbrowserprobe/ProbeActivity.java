package pro.celikom.a1publicbrowserprobe;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

/** Transient launcher: all read-only IPC now happens after Yandex regains focus. */
public final class ProbeActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        startService(new Intent(this, PublicBrowserProbeService.class));
        finish();
    }
}
