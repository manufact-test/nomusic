"use strict";
const status = document.getElementById("status"), result = document.getElementById("result"), copy = document.getElementById("copy"), refresh = document.getElementById("refresh");
async function check() {
  refresh.disabled = true; copy.disabled = true; status.textContent = "Проверяю…";
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id || new URL(tab.url).origin !== "https://music.yandex.ru") throw Error("Открой вкладку Яндекс Музыки, затем нажми на значок проверки.");
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, world: "MAIN", files: ["reader.js"] });
    const [answer] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, world: "MAIN",
      func: () => window.__CELIKOM_ENGINE_READONLY_PROBE__?.inspect() || null });
    const data = { check: "CELIKOM native engine", readOnly: true, at: new Date().toISOString(), engine: answer?.result || null };
    result.value = JSON.stringify(data, null, 2); copy.disabled = false;
    status.textContent = data.engine?.found ? "Интерфейс плеера найден. Скопируй результат в чат." : "Плеер пока не найден. Включи песню и повтори проверку. Если не найдётся — тоже пришли результат.";
  } catch (error) { status.textContent = String(error?.message || "Не удалось проверить вкладку."); result.value = ""; }
  finally { refresh.disabled = false; }
}
refresh.addEventListener("click", check);
copy.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(result.value); status.textContent = "Скопировано. Можно отправить в чат."; }
  catch { result.focus(); result.select(); status.textContent = "Выделила результат: нажми Ctrl+C."; }
});
void check();
