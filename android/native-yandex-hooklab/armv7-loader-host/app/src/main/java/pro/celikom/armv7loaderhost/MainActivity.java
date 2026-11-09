package pro.celikom.armv7loaderhost;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.graphics.Color;
import android.view.Gravity;

public final class MainActivity extends Activity {
    static { System.loadLibrary("celikom_host_probe"); }
    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        TextView text = new TextView(this);
        text.setGravity(Gravity.CENTER);
        text.setTextColor(Color.BLACK);
        text.setBackgroundColor(Color.WHITE);
        text.setTextSize(18f);
        if (getPackageName().equals("pro.celikom.armv7loaderhost.witness")) {
            text.setText("CELIKOM ARMv7 — hook witness\n\n"
                + "Native host: STARTED\n"
                + "Module hook armed: " + (HookWitnessState.armed() ? "YES" : "NOT OBSERVED") + "\n"
                + "onCreate intercepted: " + (HookWitnessState.intercepted() ? "YES" : "NOT OBSERVED") + "\n\n"
                + "If both YES: LSPatch ran our module inside this OWN lab app.\n"
                + "This is NOT a Yandex or audio replacement test.");
        } else {
            text.setText("CELIKOM ARMv7 loader test\n\n"
                + "This is a separate test app. No Yandex, music or account access.\n"
                + "If visible: the 32-bit host activity launched.\n"
                + "This does NOT prove audio substitution or Play Protect acceptance.");
        }
        setContentView(text);
    }
}
