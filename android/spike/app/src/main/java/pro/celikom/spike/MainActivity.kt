package pro.celikom.spike

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.*
import org.json.JSONObject
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class MainActivity : ComponentActivity() {
    private lateinit var surface:MobileSurface
    private lateinit var playback:MobilePlayback
    private var playbackState by mutableStateOf("Звучит оригинал")
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val account=MobileAccount(this)
        surface=MobileSurface(this,{playbackState=it},{if(::playback.isInitialized)playback.stop()},
            {if(::playback.isInitialized)playback.guardReleased(it)})
        playback=MobilePlayback(account,surface,{playbackState=it})
        setContent {
            MaterialTheme {
                var accountOpen by remember{mutableStateOf(false)}
                var email by remember{mutableStateOf("")}
                var password by remember{mutableStateOf("")}
                var code by remember{mutableStateOf("")}
                var signedIn by remember{mutableStateOf(account.signedIn)}
                var accountState by remember{mutableStateOf(if(signedIn) "Проверяем доступ…" else "Войдите в аккаунт CELIKOM")}
                var busy by remember{mutableStateOf(false)}
                var register by remember{mutableStateOf(false)}
                var verification by remember{mutableStateOf(false)}
                var recovery by remember{mutableStateOf(false)}
                var emailCode by remember{mutableStateOf("")}
                val scope=rememberCoroutineScope()
                fun task(work:suspend ()->String){
                    if(busy)return
                    busy=true
                    scope.launch {
                        accountState=try{withContext(Dispatchers.IO){work()}}catch(e:Exception){e.message?.takeIf{it.length<120}?:"Не удалось выполнить запрос. Повторите позже"}
                        signedIn=account.signedIn;verification=account.verificationEmail!=null;busy=false
                    }
                }
                LaunchedEffect(Unit){if(signedIn)task{formatAccess(account.entitlement())}}
                BackHandler(enabled=accountOpen||(!surface.closed&&surface.view.canGoBack())) {
                    if(accountOpen)accountOpen=false else {playback.stop();surface.view.goBack()}
                }
                Surface(Modifier.fillMaxSize()) {
                    Column(Modifier.safeDrawingPadding()) {
                        Row(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=8.dp),horizontalArrangement=Arrangement.SpaceBetween) {
                            Text("CELIKOM",style=MaterialTheme.typography.titleLarge)
                            TextButton(onClick={if(!accountOpen)playback.stop();accountOpen=!accountOpen}){Text(if(accountOpen) "К плееру" else "Аккаунт")}
                        }
                        if(accountOpen){
                            Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()).padding(horizontal=20.dp,vertical=12.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
                                Text(accountState)
                                if(!signedIn){
                                    OutlinedTextField(email,{email=it},Modifier.fillMaxWidth(),label={Text("Почта")},singleLine=true)
                                    OutlinedTextField(password,{password=it},Modifier.fillMaxWidth(),label={Text("Пароль")},singleLine=true,visualTransformation=PasswordVisualTransformation())
                                    Button(enabled=!busy&&email.isNotBlank()&&password.isNotEmpty(),onClick={
                                        val submitted=password;password=""
                                        task{account.login(email,submitted,register);if(account.signedIn)formatAccess(account.entitlement()) else "Введите код подтверждения из письма"}
                                    }){Text(if(register) "Зарегистрироваться" else "Войти")}
                                    TextButton(onClick={register=!register},enabled=!busy){Text(if(register) "Уже есть аккаунт" else "Создать аккаунт")}
                                    if(verification||recovery){
                                        OutlinedTextField(emailCode,{emailCode=it},Modifier.fillMaxWidth(),label={Text("Код из письма")},singleLine=true)
                                    }
                                    if(verification){
                                        Button(enabled=!busy&&emailCode.isNotBlank(),onClick={val submitted=emailCode;emailCode="";task{account.verify(submitted);formatAccess(account.entitlement())}}){Text("Подтвердить почту")}
                                    }
                                    TextButton(enabled=!busy&&email.isNotBlank(),onClick={recovery=true;task{account.requestReset(email);"Если аккаунт существует, письмо с кодом отправлено"}}){Text("Восстановить пароль")}
                                    if(recovery){
                                        Text("Для восстановления введите код и новый пароль в поле «Пароль»")
                                        Button(enabled=!busy&&emailCode.isNotBlank()&&password.isNotEmpty(),onClick={
                                            val submitted=password;val resetCode=emailCode;password="";emailCode=""
                                            task{account.resetPassword(email,resetCode,submitted);"Пароль изменён. Войдите с новым паролем"}
                                        }){Text("Сохранить новый пароль")}
                                    }
                                }else{
                                    OutlinedButton(enabled=!busy,onClick={task{formatAccess(account.entitlement())}}){Text("Обновить доступ")}
                                    Text("Промокод",style=MaterialTheme.typography.titleMedium)
                                    OutlinedTextField(code,{code=it},Modifier.fillMaxWidth(),label={Text("Введите промокод")},singleLine=true)
                                    Button(enabled=!busy&&code.isNotBlank(),onClick={
                                        playback.stop();val submitted=code;task{account.redeem(submitted);formatAccess(account.entitlement())}
                                    }){Text("Активировать")}
                                    OutlinedButton(enabled=!busy,onClick={playback.stop();task{account.logout();"Вы вышли из аккаунта CELIKOM"}}){Text("Выйти")}
                                }
                                Text("Вход в Яндекс находится в самом плеере и не связан с паролем CELIKOM.")
                                Text("Android PoC 0.2.0 • даты по московскому времени",style=MaterialTheme.typography.bodySmall)
                            }
                        }else{
                            Text(playbackState,Modifier.padding(horizontal=16.dp,vertical=4.dp))
                            Row(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=8.dp),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                                Button(enabled=signedIn&&!busy,onClick={playback.start()}){Text("Подмена")}
                                OutlinedButton(onClick={playback.stop()}){Text("Оригинал")}
                            }
                            AndroidView(factory={surface.view},modifier=Modifier.weight(1f).fillMaxWidth())
                        }
                    }
                }
            }
        }
        surface.open()
    }
    override fun onStart(){super.onStart();if(::surface.isInitialized)surface.resume()}
    override fun onStop(){if(::playback.isInitialized)playback.stop("Приложение в фоне — подмена остановлена");if(::surface.isInitialized)surface.suspend();super.onStop()}
    override fun onDestroy(){if(::playback.isInitialized)playback.close();if(::surface.isInitialized)surface.close();super.onDestroy()}
    companion object {
        fun formatAccess(e:JSONObject):String {
            if(e.optString("reason")=="service_incident")return "Подмена временно приостановлена. Время действующего доступа заморожено"
            if(!e.optBoolean("allowed"))return "Доступ не активен. Пробные 3 дня начинаются при включении подмены"
            if(e.isNull("valid_until"))return "Доступ: навсегда"
            val until=runCatching{Instant.parse(e.getString("valid_until"))}.getOrNull()?:return "Доступ действует"
            return "Доступ до "+DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm").withZone(ZoneId.of("Europe/Moscow")).format(until)+" (МСК)"
        }
    }
}
