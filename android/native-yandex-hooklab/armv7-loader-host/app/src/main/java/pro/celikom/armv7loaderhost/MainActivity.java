package pro.celikom.armv7loaderhost;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.graphics.Color;
import android.view.Gravity;

public final class MainActivity extends Activity {
    static {
        // Default ARMv7 witness still strictly requires real JNI.
        // Our OWN x86_64 WAV-only emulator probe deliberately has no JNI.
        if (!BuildConfig.CELIKOM_OWN_EMULATOR)
            System.loadLibrary("celikom_host_probe");
    }
    private AudioSmokeScreen audioScreen;
    @Override public void onCreate(Bundle b) {
        // Separate own-only Android runtime race mode. No vendor process.
        if(getPackageName().equals("pro.celikom.armv7loaderhost.audio")
                && getIntent()!=null
                && getIntent().getBooleanExtra("celikom_own_race",false)) {
            super.onCreate(b);
            TextView witness=new TextView(this);
            witness.setTextColor(Color.BLACK);
            witness.setBackgroundColor(Color.WHITE);
            witness.setTextSize(17f);
            witness.setPadding(24,24,24,24);
            setContentView(witness);
            new OwnAndroidAsyncRaceProbe(this,witness).run();
            return;
        }
        // Explicit adb-triggered check on our isolated emulator app ONLY.
        // Never reachable from the real Yandex package or normal startup.
        if(getPackageName().equals("pro.celikom.armv7loaderhost.audio")
                && getIntent()!=null
                && getIntent().getBooleanExtra("celikom_own_probe",false)) {
            super.onCreate(b);
            TextView witness=new TextView(this);
            witness.setTextColor(Color.BLACK);
            witness.setBackgroundColor(Color.WHITE);
            witness.setTextSize(17f);
            witness.setPadding(24,24,24,24);
            setContentView(witness);
            new OwnAndroidMediaRuntimeProbe(this,witness).run();
            return;
        }
        if(getPackageName().equals("pro.celikom.armv7loaderhost.audio")) {
            super.onCreate(b);
            audioScreen=new AudioSmokeScreen(this);
            setContentView(audioScreen);
            return;
        }
        super.onCreate(b);
        TextView text = new TextView(this);
        text.setGravity(Gravity.CENTER);
        text.setTextColor(Color.BLACK);
        text.setBackgroundColor(Color.WHITE);
        text.setTextSize(18f);
        if (getPackageName().equals("pro.celikom.armv7loaderhost.witness")
                || getPackageName().equals("pro.celikom.armv7loaderhost.x86control")) {
            boolean armed = HookWitnessState.armed();
            boolean intercepted = HookWitnessState.intercepted();
            text.setText("CELIKOM OWN — hook witness\n\n"
                + "Native host: STARTED\n"
                + "Module hook armed: " + (armed ? "YES" : "NOT OBSERVED") + "\n"
                + "onCreate intercepted: " + (intercepted ? "YES" : "NOT OBSERVED") + "\n\n"
                + "If both YES: LSPatch ran our module inside this OWN lab app.\n"
                + "This is NOT a Yandex or audio replacement test.");
            if (getPackageName().equals("pro.celikom.armv7loaderhost.x86control")) {
                // Fixed enum only; no app data, secrets, URLs or audio in logs.
                android.util.Log.i("CelikomOwnHookWitness", "RESULT="
                    + (armed && intercepted ? "PASS" : "FAIL")
                    + " CODE=OWN_MODULE_ACTIVITY_INTERCEPTED");
            }
        } else {
            text.setText("CELIKOM ARMv7 loader test\n\n"
                + "This is a separate test app. No Yandex, music or account access.\n"
                + "If visible: the 32-bit host activity launched.\n"
                + "This does NOT prove audio substitution or Play Protect acceptance.");
        }
        setContentView(text);
    }
    @Override protected void onStop() {
        if(audioScreen!=null) audioScreen.stopAndRelease();
        super.onStop();
    }
}
