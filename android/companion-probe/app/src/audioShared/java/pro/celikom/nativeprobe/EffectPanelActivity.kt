package pro.celikom.nativeprobe

import android.app.Activity
import android.os.Bundle
import android.content.Intent

class EffectPanelActivity : Activity() {
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        if (ProbeStore.enabled(this)) ProbeStore.event(this, ProbeStore.effectEvent(intent, callingPackage))
        setResult(RESULT_OK)
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
