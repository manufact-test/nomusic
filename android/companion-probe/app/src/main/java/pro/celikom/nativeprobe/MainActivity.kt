package pro.celikom.nativeprobe

import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ComponentName
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.view.View
import android.view.WindowInsets
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.NotificationManagerCompat
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class MainActivity : Activity() {
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var summary: TextView
    private lateinit var details: TextView
    private lateinit var toggle: Button
    private val refresh = object : Runnable {
        override fun run() { render(); handler.postDelayed(this, 1000) }
    }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        val scroll = ScrollView(this).apply {
            isFillViewport = true; setBackgroundColor(Color.rgb(11, 16, 19));
            scrollBarStyle = View.SCROLLBARS_OUTSIDE_INSET; setPadding(dp(20), dp(16), dp(20), dp(24))
        }
        scroll.setOnApplyWindowInsetsListener { v, insets ->
            val top: Int; val bottom: Int
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                val bars = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout())
                top = bars.top; bottom = bars.bottom
            } else {
                @Suppress("DEPRECATION")
                top = insets.systemWindowInsetTop
                @Suppress("DEPRECATION")
                bottom = insets.systemWindowInsetBottom
            }
            v.setPadding(dp(20), dp(16) + top, dp(20), dp(24) + bottom); insets
        }
        val column = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        scroll.addView(column)
        fun text(value: String, size: Float = 16f): TextView = TextView(this).apply {
            text = value; textSize = size; setTextColor(Color.rgb(225, 231, 231))
            setPadding(0, dp(8), 0, dp(12)); setTextIsSelectable(true)
            column.addView(this, LinearLayout.LayoutParams(-1, -2))
        }
        fun button(label: String, click: () -> Unit): Button = Button(this).apply {
            text = label; isAllCaps = false; minHeight = dp(52)
            column.addView(this, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) })
            setOnClickListener { click() }
        }
        text("CELIKOM", 30f).setTextColor(Color.rgb(102, 224, 191))
        text("Проверка Яндекс Музыки", 23f)
        text("Это диагностика подключения к установленному плееру. Подмена здесь ещё не включается. Вход в Яндекс и CELIKOM не нужен.")
        button("1. Разрешить доступ к уведомлениям") {
            try { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
            catch (_: android.content.ActivityNotFoundException) { toast("Открой настройки Android → Доступ к уведомлениям") }
        }
        text("В настройках выбери «CELIKOM: состояние Яндекс Музыки». Android даёт широкий доступ к уведомлениям, но эта сборка обрабатывает только состояние Яндекс Музыки. Другие уведомления не читаются и не сохраняются. Интернет и микрофон не используются. Отчёт передаётся только по твоему действию.")
        button("2. Открыть Яндекс Музыку") {
            val launch = packageManager.getLaunchIntentForPackage(ProbeStore.YANDEX)
            if (launch == null) toast("Установленная Яндекс Музыка не найдена") else startActivity(launch)
        }
        text("В Яндекс Музыке открой настройки эквалайзера. Если предложен выбор внешнего обработчика, выбери CELIKOM. Если его нет — просто продолжи: отсутствие подключения тоже важно. Запусти песню, переключи на следующую, поставь паузу и продолжи. Затем выключи экран на 30 секунд, вернись сюда и скопируй отчёт.")
        summary = text("Проверяем состояние…", 17f)
        button("Скопировать отчёт") {
            getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("CELIKOM diagnostic", report().toString(2)))
            toast("Отчёт скопирован. Вставь его в наш чат.")
        }
        button("Поделиться отчётом") {
            startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
                .putExtra(Intent.EXTRA_TEXT, report().toString(2)), "Передать отчёт CELIKOM"))
        }
        toggle = button("Остановить наблюдение") {
            ProbeStore.setEnabled(this, !ProbeStore.enabled(this))
            NotificationListenerService.requestRebind(ComponentName(this, MusicListener::class.java))
            render()
        }
        button("Очистить результаты") { ProbeStore.clear(this); render(); toast("Результаты очищены") }
        button("Показать / скрыть детали") { details.visibility = if (details.visibility == View.GONE) View.VISIBLE else View.GONE; render() }
        details = text("").apply { textSize = 13f; visibility = View.GONE }
        text("Состояние и сведения о песне — последние полученные события, а не доказательство готовой подмены. Отчёт может содержать название песни, исполнителя и её идентификатор. После проверки доступ к уведомлениям можно отключить в настройках Android.", 14f)
        setContentView(scroll)
    }
    private fun access() = NotificationManagerCompat.getEnabledListenerPackages(this).contains(packageName)
    private fun report(): JSONObject = ProbeStore.report(this).put("notification_access_enabled", access())
    private fun render() {
        val r = report(); val media = r.getJSONObject("media"); val sessions = media.optJSONArray("sessions")
        val events = r.getJSONArray("events")
        val last = if (events.length() > 0) events.getJSONObject(events.length() - 1) else null
        val time = media.optLong("observed_at_ms", 0)
        val formatter = SimpleDateFormat("dd.MM HH:mm:ss", Locale("ru")).apply { timeZone = TimeZone.getTimeZone("Europe/Moscow") }
        summary.text = "Телефон: ${r.getString("manufacturer")} ${r.getString("model")}\nAndroid: ${r.getString("android_release")}\nЯндекс Музыка: ${r.getString("yandex_version")}\nДоступ к уведомлениям: ${if (access()) "разрешён" else "не разрешён"}\nНаблюдение: ${if (ProbeStore.enabled(this)) "включено" else "остановлено"}\nСессий Яндекс Музыки: ${sessions?.length() ?: 0}\nПоследнее состояние: ${if (time > 0) formatter.format(Date(time)) + " МСК" else "ещё не получено"}\nСобытий эквалайзера: ${events.length()}\nПоследняя аудиосессия: ${last?.optInt("session_id", -1) ?: "не получена"}\nТочный ID песни: ещё не подтверждён\nПодмена: не включалась"
        toggle.text = if (ProbeStore.enabled(this)) "Остановить наблюдение" else "Возобновить наблюдение"
        if (details.visibility == View.VISIBLE) details.text = r.toString(2)
    }
    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
    private fun toast(message: String) { Toast.makeText(this, message, Toast.LENGTH_LONG).show() }
}
