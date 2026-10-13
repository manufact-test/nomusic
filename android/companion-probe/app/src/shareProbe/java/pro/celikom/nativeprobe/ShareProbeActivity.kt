package pro.celikom.nativeprobe

import android.app.Activity
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject

class ShareProbeActivity : Activity() {
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var status: TextView
    private lateinit var probe: PublicMediaProbe
    private val refresh = object : Runnable { override fun run() { render(); handler.postDelayed(this, 700) } }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        probe = PublicMediaProbe.shared(applicationContext)
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(30, 65, 30, 45); setBackgroundColor(Color.rgb(11,16,19)) }
        fun text(value: String): TextView = TextView(this).apply { text=value; textSize=17f; setTextColor(Color.WHITE); setPadding(0,12,0,22); box.addView(this) }
        fun button(label: String, action: () -> Unit) { box.addView(Button(this).apply { text=label; isAllCaps=false; setOnClickListener { action() } }) }
        text("CELIKOM — проверка ID
0.1.0")
        text("Одноразовый тест на открытом экране Яндекс Музыки. Музыка и эквалайзер не изменяются. Сначала включи песню и открой её полный плеер, затем открой это приложение.")
        button("1. Разрешить тест кнопок Яндекса") {
            AlertDialog.Builder(this).setTitle("Доступ к кнопкам Яндекса")
                .setMessage("В специальных возможностях включи CELIKOM — проверка ID. Тест читает только экран Яндекс Музыки и только после нажатия кнопки запуска, до 45 секунд. Другие приложения, уведомления и буфер обмена не читаются. Системное меню выбора получателя не нажимается автоматически. После теста доступ можно отключить.")
                .setNegativeButton("Отмена",null).setPositiveButton("Открыть настройки") { _, _ -> startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }.show()
        }
        button("2. Подключиться к плееру") { ProbeStore.setEnabled(this,true); probe.start(); toast("Подожди, пока появится состояние песни") }
        button("3. Запустить тест и открыть Яндекс") {
            val service = ShareUiService.instance
            if (service == null) { toast("Сначала включи доступ в специальных возможностях"); return@button }
            if (!service.arm()) { toast("Сначала подключись к плееру и дождись свежего состояния"); return@button }
            val launch = packageManager.getLaunchIntentForPackage("ru.yandex.music")
            if (launch == null) { service.finish("yandex_not_installed"); toast("Яндекс не найден") }
            else startActivity(launch)
        }
        button("Остановить тест") { ShareUiService.instance?.finish("cancelled"); render() }
        button("Скопировать отчёт") {
            val clipboard = getSystemService(ClipboardManager::class.java)
            clipboard.setPrimaryClip(ClipData.newPlainText("CELIKOM ID diagnostic", report().toString(2)))
            toast("Отчёт скопирован")
        }
        status = text("")
        text("В меню отправки выбери «CELIKOM — проверка ID». Если за 15 секунд меню не открылось, вернись сюда и скопируй отчёт. Вручную кнопки Яндекса в этом тесте не нажимай. Экран не блокируй.")
        val scroll = ScrollView(this).apply { addView(box) }
        scroll.setOnApplyWindowInsetsListener { _, insets ->
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                val bars = insets.getInsets(android.view.WindowInsets.Type.systemBars() or android.view.WindowInsets.Type.displayCutout())
                box.setPadding(30, bars.top + 24, 30, bars.bottom + 24)
            }
            insets
        }
        setContentView(scroll)
        accept(intent)
    }
    private fun accept(value: Intent?) {
        if (value?.action != Intent.ACTION_SEND || value.type != "text/plain") return
        val before = ProbeStore.report(this).optJSONObject("share_ui_test")
        val accepted = ProbeStore.acceptSharedLink(this,value.getStringExtra(Intent.EXTRA_TEXT))
        ShareUiService.instance?.finish(if (accepted) "source_link_received" else "not_a_track_link")
        val r = ProbeStore.report(this)
        val after = r.optJSONObject("media")
        val id = after?.optJSONArray("sessions")?.optJSONObject(0)?.optString("media_id")
        ProbeStore.put(this,"share_link_result", JSONObject().put("status",if (accepted) "source_link_received" else "invalid_link")
            .put("source_track_id",r.optJSONObject("shared_track")?.optString("track_id"))
            .put("at_ms",System.currentTimeMillis()).put("before_media_id",before?.optString("before_media_id"))
            .put("after_media_id",id).put("player_observation_fresh",after?.optBoolean("fresh") == true)
            .put("automatic_current_track_verified",false))
    }
    override fun onNewIntent(intent: Intent?) { super.onNewIntent(intent); setIntent(intent); accept(intent) }
    private fun report(): JSONObject = ProbeStore.report(this).put("share_probe_version","0.1.0")
    private fun render() {
        val r=report(); val media=r.optJSONObject("media"); val song=media?.optJSONArray("sessions")?.optJSONObject(0)
        status.text="Доступ к кнопкам: ${if (ShareUiService.instance!=null) "включён" else "не включён"}\nПлеер: ${r.optJSONObject("public_browser")?.optString("status")}\nСвежие данные: ${media?.optBoolean("fresh")}\nПесня: ${song?.optJSONObject("metadata")?.optString("title")}\nТест: ${r.optJSONObject("share_ui_test")?.optString("status","не запускался")}\nСсылка: ${r.optJSONObject("share_link_result")?.optString("source_track_id","не получена")}\nАвтоматический ID текущей песни: ещё не подтверждён"
    }
    override fun onResume() { super.onResume(); ShareUiService.instance?.finish("returned_without_source_link"); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
    private fun toast(message:String) { Toast.makeText(this,message,Toast.LENGTH_LONG).show() }
}
