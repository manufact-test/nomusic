package pro.celikom.nativeprobe

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.audiofx.AudioEffect

class SessionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (!ProbeStore.enabled(context)) return
        if (intent.action !in listOf(AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION,
                AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION)) return
        if (intent.getStringExtra(AudioEffect.EXTRA_PACKAGE_NAME) != ProbeStore.YANDEX) return
        // Broadcast extras are claims, not proof of origin. Never attach an effect here.
        ProbeStore.event(context, ProbeStore.effectEvent(intent, null))
        val test = ProbeStore.report(context).optJSONObject("attenuation_test")
        if (test?.optString("status") in listOf("waiting", "attenuating")) {
            val session = intent.getIntExtra(AudioEffect.EXTRA_AUDIO_SESSION, -1)
            if ((intent.action == AudioEffect.ACTION_CLOSE_AUDIO_EFFECT_CONTROL_SESSION && session == test?.optInt("session_id")) ||
                (intent.action == AudioEffect.ACTION_OPEN_AUDIO_EFFECT_CONTROL_SESSION && session != test?.optInt("session_id")))
                context.stopService(Intent(context, AttenuationService::class.java))
        }
    }
}
