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
import android.view.View
import android.view.WindowInsets
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class MainActivity : Activity() {
    private val handler = Handler(Looper.getMainLooper())
    private lateinit var publicProbe: PublicMediaProbe
    private lateinit var summary: TextView
    private lateinit var details: TextView
    private lateinit var toggle: Button
    private val refresh = object : Runnable {
        override fun run() { render(); handler.postDelayed(this, 1000) }
    }
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    override fun onCreate(state: Bundle?) {
        super.onCreate(state)
        if (intent.action == Intent.ACTION_SEND && intent.type == "text/plain") {
            val link = intent.getStringExtra(Intent.EXTRA_TEXT)
            if (!ProbeStore.acceptSharedLink(this, link)) toast("Ссылка на песню Яндекса не распознана")
        }
        publicProbe = PublicMediaProbe.shared(applicationContext)
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
        if (!BuildConfig.PANEL_ONLY) {
        button("1. Разрешить доступ к уведомлениям") {
            AlertDialog.Builder(this)
                .setTitle("Доступ к состоянию плеера")
                .setMessage("Android выдаёт широкий доступ к уведомлениям. CELIKOM использует его только для состояния Яндекс Музыки: песни, позиции и команд плеера. Содержимое других уведомлений не читается и не сохраняется. Данные остаются на телефоне; отчёт передаётся только кнопками копирования или отправки. Доступ можно отключить в настройках Android.")
                .setNegativeButton("Отмена", null)
                .setPositiveButton("Перейти в настройки") { _, _ ->
                    try { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
                    catch (_: android.content.ActivityNotFoundException) { toast("Открой настройки Android → Доступ к уведомлениям") }
                }.show()
        }
        text("В настройках выбери «CELIKOM: состояние Яндекс Музыки». Android даёт широкий доступ к уведомлениям, но эта сборка обрабатывает только состояние Яндекс Музыки. Другие уведомления не читаются и не сохраняются. Интернет и микрофон не используются. Отчёт передаётся только по твоему действию.")
        } else {
            text("Этот режим не запрашивает доступ к уведомлениям. Он проверяет передачу аудиосессии через эквалайзер. Сведения о песне здесь возможны только если Яндекс разрешит подключение к своему публичному медиасервису. Автоматический точный ID пока не подтверждён. Ссылку на песню можно передать из Яндекса через «Поделиться» → CELIKOM; она не доказывает, что песня сейчас играет.")
        }
        if (BuildConfig.PANEL_ONLY) text("Проверка плеера сохраняет соединение до двух минут после нажатия. За это время можно вернуться в Яндекс, поставить паузу или сменить песню, затем вернуться и скопировать отчёт. Повторное нажатие обновляет данные без разрыва рабочего соединения.")
        if (BuildConfig.PANEL_ONLY) button("Проверить состояние плеера Яндекса") { publicProbe.start(); render() }
        button("Проверить приглушение на 7 секунд") {
            val session = AttenuationService.verifiedSession(ProbeStore.report(this), System.currentTimeMillis())
            if (session == null) toast("Сначала открой эквалайзер из Яндекса. Проверка доступна одну минуту после открытия.")
            else AlertDialog.Builder(this).setTitle("Короткая проверка звука")
                .setMessage("Вернись в Яндекс сразу после запуска. Через 3 секунды CELIKOM попробует приглушить только переданную аудиосессию на 7 секунд, затем отпустит эффект. Громкость телефона не меняется. После теста скопируй отчёт и напиши, исчез ли звук и вернулся ли сам.")
                .setNegativeButton("Отмена", null).setPositiveButton("Запустить") { _, _ ->
                    try { startForegroundService(Intent(this, AttenuationService::class.java)) }
                    catch (_: RuntimeException) { toast("Android не разрешил запустить тест") }
                }.show()
        }
        button("Проверить замену тестовым звуком") {
            if (AttenuationService.verifiedSession(ProbeStore.report(this),System.currentTimeMillis()) == null)
                toast("Сначала открой эквалайзер из Яндекса. Проверка доступна одну минуту после открытия.")
            else AlertDialog.Builder(this).setTitle("Короткий тест замены звука")
                .setMessage("Песня должна уже играть. Через 3 секунды CELIKOM приглушит Яндекс и включит тихий прерывистый сигнал примерно на 7 секунд. Затем сигнал остановится и оригинал вернётся. Вернись в Яндекс после запуска; не переключай песню во время теста. Это проверка звука, без синхронизации песни.")
                .setNegativeButton("Отмена",null).setPositiveButton("Запустить") { _, _ ->
                    try { startForegroundService(Intent(this,AttenuationService::class.java).putExtra("play_tone",true)) }
                    catch (_: RuntimeException) { toast("Android не разрешил запустить тест") }
                }.show()
        }
        button("Остановить проверку звука") { stopService(Intent(this, AttenuationService::class.java)); render() }
        button("Открыть Яндекс Музыку") {
            val launch = packageManager.getLaunchIntentForPackage(ProbeStore.YANDEX)
            if (launch == null) toast("Установленная Яндекс Музыка не найдена") else startActivity(launch)
        }
        text("Сначала запусти песню в Яндекс Музыке, затем открой настройки эквалайзера. Если предложен выбор внешнего обработчика, выбери CELIKOM. Если его нет — просто продолжи: отсутствие подключения тоже важно. Запусти песню, переключи на следующую, поставь паузу и продолжи. Затем выключи экран на 30 секунд, вернись сюда и скопируй отчёт.")
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
            MusicObservation.rebind(this)
            if (!ProbeStore.enabled(this)) { publicProbe.stop(); stopService(Intent(this, AttenuationService::class.java)) }
            render()
        }
        button("Очистить результаты") { publicProbe.stop();stopService(Intent(this, AttenuationService::class.java)); ProbeStore.clear(this); render(); toast("Результаты очищены") }
        button("Показать / скрыть детали") { details.visibility = if (details.visibility == View.GONE) View.VISIBLE else View.GONE; render() }
        details = text("").apply { textSize = 13f; visibility = View.GONE }
        text("Состояние и сведения о песне — последние полученные события, а не доказательство готовой подмены. Отчёт может содержать название песни, исполнителя и её идентификатор. Приглушение проверяется отдельной кнопкой и автоматически заканчивается.", 14f)
        setContentView(scroll)
        if (android.os.Build.VERSION.SDK_INT >= 30) window.insetsController?.setSystemBarsAppearance(0,
            android.view.WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or android.view.WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS)
    }
    private fun access() = MusicObservation.access(this)
    private fun report(): JSONObject = ProbeStore.report(this).put("notification_access_enabled", access())
    private fun render() {
        val r = report(); val media = r.getJSONObject("media"); val sessions = media.optJSONArray("sessions")
        val events = r.getJSONArray("events")
        val last = if (events.length() > 0) events.getJSONObject(events.length() - 1) else null
        val browser = r.optJSONObject("public_browser")?.optString("status", "not_checked") ?: "not_checked"
        val time = media.optLong("observed_at_ms", 0)
        val formatter = SimpleDateFormat("dd.MM HH:mm:ss", Locale("ru")).apply { timeZone = TimeZone.getTimeZone("Europe/Moscow") }
        summary.text = "Телефон: ${r.getString("manufacturer")} ${r.getString("model")}\nAndroid: ${r.getString("android_release")}\nЯндекс Музыка: ${r.getString("yandex_version")}\nДоступ к уведомлениям: ${if (BuildConfig.PANEL_ONLY) "не требуется" else if (access()) "разрешён" else "не разрешён"}\nНаблюдение: ${if (ProbeStore.enabled(this)) "включено" else "остановлено"}\nПубличный медиасервис: $browser\nСессий Яндекс Музыки: ${sessions?.length() ?: 0}\nПоследнее состояние: ${if (time > 0) formatter.format(Date(time)) + " МСК" else "ещё не получено"}\nСобытий эквалайзера: ${events.length()}\nПоследняя аудиосессия: ${last?.optInt("session_id", -1) ?: "не получена"}\nТочный ID песни: ещё не подтверждён\nПроверка приглушения: ${r.optJSONObject("attenuation_test")?.optString("status", "не запускалась")}\nПодмена: не включалась"
        toggle.text = if (ProbeStore.enabled(this)) "Остановить наблюдение" else "Возобновить наблюдение"
        if (details.visibility == View.VISIBLE) details.text = r.toString(2)
    }
    override fun onResume() { super.onResume(); handler.post(refresh) }
    override fun onPause() { handler.removeCallbacks(refresh); super.onPause() }
    override fun onDestroy() { handler.removeCallbacksAndMessages(null); super.onDestroy() }
    private fun toast(message: String) { Toast.makeText(this, message, Toast.LENGTH_LONG).show() }
}
