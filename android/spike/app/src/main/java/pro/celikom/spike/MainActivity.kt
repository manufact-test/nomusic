package pro.celikom.spike

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*

class MainActivity : ComponentActivity() {
    private lateinit var playback: FixturePlayback
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        playback = FixturePlayback(this)
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    val scope = rememberCoroutineScope()
                    val account = remember { AccountProbe() }
                    var email by remember { mutableStateOf("") }
                    var password by remember { mutableStateOf("") }
                    var accountState by remember { mutableStateOf("Вход необязателен для локальной диагностики") }
                    var busy by remember { mutableStateOf(false) }
                    var tick by remember { mutableIntStateOf(0) }
                    LaunchedEffect(Unit) { while (true) { delay(250); tick++ } }
                    Column(Modifier.safeDrawingPadding().padding(20.dp).verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text("CELIKOM • Android PoC", style = MaterialTheme.typography.headlineSmall)
                        Text("Локальные тестовые звуки. Яндекс Музыка не подключена.")
                        val position = tick.let { playback.position }
                        Text("Трек: " + playback.policy.trackId + " · " + (position / 1000) + " с")
                        Text(if (playback.policy.replacement) "Звучит тестовая подмена" else "Тестовый оригинал")
                        Button(onClick = { playback.start(); tick++ }) { Text("Старт подмены") }
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            OutlinedButton(onClick = { playback.pause(); tick++ }) { Text("Пауза") }
                            OutlinedButton(onClick = { playback.resume(); tick++ }) { Text("Продолжить") }
                        }
                        OutlinedButton(onClick = { playback.original(); tick++ }) { Text("Вернуть оригинал") }
                        Slider(value = playback.position.toFloat(), onValueChange = { playback.seek(it.toInt()); tick++ },
                            valueRange = 0f..(playback.duration - 1).toFloat())
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            OutlinedButton(onClick = { playback.track("fixture:1"); tick++ }) { Text("Предыдущий") }
                            OutlinedButton(onClick = { playback.track("fixture:2"); tick++ }) { Text("Следующий") }
                        }
                        OutlinedButton(onClick = { playback.failOpen(); tick++ }) { Text("Сбой подмены") }
                        Text("Уход в фон и потеря аудиофокуса останавливают демо. Возобновление — вручную.")
                        HorizontalDivider()
                        Text("Проверка общего аккаунта", style = MaterialTheme.typography.titleMedium)
                        OutlinedTextField(email, { email = it }, label = { Text("Почта") }, singleLine = true)
                        OutlinedTextField(password, { password = it }, label = { Text("Пароль") },
                            visualTransformation = PasswordVisualTransformation(), singleLine = true)
                        Text(accountState)
                        Button(enabled = !busy && email.isNotBlank() && password.isNotEmpty(), onClick = {
                            busy = true
                            val submitted = password; password = ""
                            scope.launch {
                                accountState = try { withContext(Dispatchers.IO) { account.login(email, submitted) } }
                                    catch (_: Exception) { "Не удалось проверить вход. Повторите позже." }
                                busy = false
                            }
                        }) { Text("Войти и проверить доступ") }
                        OutlinedButton(enabled = !busy, onClick = {
                            busy = true
                            scope.launch {
                                runCatching { withContext(Dispatchers.IO) { account.logout() } }
                                accountState = "Локальный вход завершён"; busy = false
                            }
                        }) { Text("Выйти") }
                        Text("Версия 0.1.0-spike. Вход не запускает trial. Пароль и токены не сохраняются.")
                    }
                }
            }
        }
    }
    override fun onStop() { playback.suspend(); super.onStop() }
    override fun onDestroy() { playback.close(); super.onDestroy() }
}
