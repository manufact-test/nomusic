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
        text.setText("CELIKOM ARMv7 loader test\n\n"
            + "This is a separate test app. No Yandex, music or account access.\n"
            + "If visible: the 32-bit host activity launched.\n"
            + "This does NOT prove audio substitution or Play Protect acceptance.");
        setContentView(text);
    }
}
