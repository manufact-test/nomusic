import { COMMANDS, type ExtensionState } from "../shared/messages.js";
import { uploadTargetFromStatus, validMp3Selection, privateUploadApiOrigin } from "../upload/contract.js";

const status = document.querySelector<HTMLElement>("[data-status]");
const startButton = document.querySelector<HTMLButtonElement>("[data-action='start']");
const stopButton = document.querySelector<HTMLButtonElement>("[data-action='stop']");
const restoreButton = document.querySelector<HTMLButtonElement>("[data-action='restore']");
const diagnosticsButton = document.querySelector<HTMLButtonElement>("[data-action='diagnostics']");
const track = document.querySelector<HTMLElement>("[data-track]");
const testInput = document.querySelector<HTMLInputElement>("[data-test-track]");
let lastState: ExtensionState | null = null;

function render(state: ExtensionState): void {
  if (!status || !startButton || !stopButton) return;
  lastState = state;
  const labels: Record<ExtensionState["phase"], string> = {
    STOPPED: "Остановлен",
    CONNECTING: "Подключение…",
    OBSERVING: "Ищем трек…",
    READY: "Трек найден",
    ERROR: "Ошибка подключения",
    PREPARING: "Готовим подмену…",
    REPLACEMENT_ACTIVE: "Подмена активна",
    RESTORING: "Возвращаем оригинал…"
  };
  status.textContent = state.manualBypass ? "Оригинал" : state.replacementError ? "Оригинал · ошибка подмены" : labels[state.phase] || "Проверка…";
  status.dataset.active = String(state.enabled);
  startButton.disabled = state.enabled && state.phase !== "ERROR" && !state.manualBypass && !state.replacementError;
  startButton.textContent = state.phase === "ERROR" ? "Повторить" : "Старт";
  stopButton.disabled = !state.enabled;
  if (testInput && document.activeElement !== testInput) testInput.value = state.settings?.testTrackId || "";
  if (track) {
    const title = state.track?.metadata?.title?.trim();
    const artist = state.track?.metadata?.artist?.trim();
    track.textContent = state.track?.id
      ? [title || `Track ID ${state.track.id}`, artist].filter(Boolean).join(" — ")
      : state.connection?.detail || (state.enabled ? "Запустите трек в Яндекс Музыке" : "CELIKOM остановлен");
    track.dataset.detected = String(Boolean(state.track?.id));
    track.title = state.track?.id
      ? `Track ID ${state.track.id} · confidence ${state.track.confidence}`
      : "";
  }
}

async function send<T>(message: object): Promise<T> {
  return chrome.runtime.sendMessage(message) as Promise<T>;
}

startButton?.addEventListener("click", async () => {
  render(await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: true }));
});

const uploadPanel = document.querySelector<HTMLElement>("[data-upload-panel]");
const uploadTrack = document.querySelector<HTMLInputElement>("[data-upload-track]");
const uploadFile = document.querySelector<HTMLInputElement>("[data-upload-file]");
const uploadKey = document.querySelector<HTMLInputElement>("[data-upload-key]");
const uploadRights = document.querySelector<HTMLInputElement>("[data-upload-rights]");
const uploadProgress = document.querySelector<HTMLProgressElement>("[data-upload-progress]");
const uploadStatus = document.querySelector<HTMLElement>("[data-upload-status]");
const uploadButton = document.querySelector<HTMLButtonElement>("[data-upload-submit]");
let pinnedTrack: { id: string; durationMs: number; artist: string; title: string; album: string } | null = null;
let uploadRequestId: string | null = null;
let uploading = false;

function uploadMessage(value: string): void {
  if (uploadStatus) uploadStatus.textContent = value;
}
document.querySelector("[data-action='add']")?.addEventListener("click", async () => {
  if (!uploadPanel || uploading) return;
  uploadPanel.hidden = !uploadPanel.hidden;
  if (uploadPanel.hidden) return;
  pinnedTrack = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
  if (uploadTrack) uploadTrack.value = pinnedTrack?.id || "";
  if (uploadButton) uploadButton.disabled = !pinnedTrack;
  uploadMessage(pinnedTrack ? "MP3 будет отправлен со статусом pending, без публикации." :
    "Сначала запустите трек в Яндекс Музыке и дождитесь его точного определения.");
  void send({ type: "CELIKOM_ADD_TRACK_OPENED" });
});

uploadFile?.addEventListener("change", () => { uploadRequestId = null; if (uploadProgress) uploadProgress.value = 0; });

document.querySelector<HTMLFormElement>("[data-upload-form]")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (uploading || !pinnedTrack || !uploadFile?.files?.[0] || !uploadRights?.checked || !uploadKey?.value) return;
  const file = uploadFile.files[0];
  if (!validMp3Selection(file)) {
    uploadMessage("Выберите MP3 не более 30 МиБ."); return;
  }
  const now = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
  if (!now || now.id !== pinnedTrack.id) {
    uploadMessage("Трек изменился. Откройте «Добавить трек» снова."); return;
  }
  // Requests execute from the trusted extension popup, not inside the music website.
  // The owner key stays in memory for this popup lifetime, never chrome.storage.
  let origin: string;
  try {
    const conf = await fetch(chrome.runtime.getURL("api/config.json")).then((r) => r.json());
    origin = privateUploadApiOrigin(conf.baseUrl);
  } catch (_error) { uploadMessage("Сервер загрузки не настроен."); return; }

  if (!uploadRequestId) uploadRequestId = crypto.randomUUID();
  const data = new FormData();
  data.append("service", "yandex");
  data.append("track_id", pinnedTrack.id);
  data.append("duration_ms", String(pinnedTrack.durationMs));
  data.append("artist", pinnedTrack.artist);
  data.append("title", pinnedTrack.title);
  data.append("album", pinnedTrack.album);
  data.append("declaration", "1");
  data.append("request_id", uploadRequestId);
  data.append("file", file, file.name);
  uploading = true;
  if (uploadButton) uploadButton.disabled = true;
  if (uploadProgress) { uploadProgress.hidden = false; uploadProgress.value = 0; }
  uploadMessage("Отправка…");
  const xhr = new XMLHttpRequest();
  xhr.open("POST", origin + "/api/v1/uploads");
  xhr.timeout = 120000;
  xhr.setRequestHeader("Authorization", "Bearer " + uploadKey.value);
  xhr.upload.addEventListener("progress", (progress) => {
    if (progress.lengthComputable && uploadProgress) uploadProgress.value = Math.floor(progress.loaded / progress.total * 100);
  });
  xhr.addEventListener("loadend", () => {
    uploading = false;
    if (uploadButton) uploadButton.disabled = !pinnedTrack;
    if (xhr.status === 202) {
      try {
        const result = JSON.parse(xhr.responseText);
        if (result.status === "pending" && Number.isSafeInteger(result.replacement_id)) {
          uploadMessage(result.duplicate ? "Дубликат найден. Запись уже ожидает проверки." : "Загружено. Ожидает ручной проверки.");
          uploadRequestId = null;
          return;
        }
      } catch (_error) { /* safe generic message */ }
    }
    const errors: Record<string, string> = {
      uploads_disabled: "Приватный приём файлов пока выключен.",
      unauthorized: "Неверный код владельца.",
      rate_limited: "Слишком много попыток. Попробуйте позже.",
      upload_too_large: "Файл превышает допустимый размер.",
      invalid_mp3: "Файл не прошёл проверку MP3.",
      already_approved: "Эта версия уже одобрена.",
      idempotency_conflict: "Повтор запроса не совпадает с исходным.",
      rights_declaration_required: "Подтвердите права на файл."
    };
    let code = "";
    try { code = JSON.parse(xhr.responseText)?.error || ""; } catch (_error) { /* no-op */ }
    uploadMessage(errors[code] || "Загрузка не завершена. Повторите попытку.");
  });
  xhr.send(data);
});
document.querySelector("[data-action='use-current']")?.addEventListener("click", async () => {
  if (lastState?.track?.id) render(await send<ExtensionState>({ type: COMMANDS.setTestTrack, trackId: lastState.track.id }));
});
document.querySelector("[data-action='clear-test']")?.addEventListener("click", async () => {
  render(await send<ExtensionState>({ type: COMMANDS.setTestTrack, trackId: "" }));
});
testInput?.addEventListener("change", async () => {
  if (testInput.value && !/^\d{1,24}$/.test(testInput.value.trim())) { testInput.setCustomValidity("Только цифры Track ID"); testInput.reportValidity(); return; }
  testInput.setCustomValidity("");
  render(await send<ExtensionState>({ type: COMMANDS.setTestTrack, trackId: testInput.value.trim() }));
});

document.querySelector("[data-action='save-api-access']")?.addEventListener("click", async () => {
  const input = document.querySelector<HTMLInputElement>("[data-api-access]");
  const note = document.querySelector<HTMLElement>("[data-api-note]");
  if (!input || !note) return;
  note.textContent = "Проверяем доступ…";
  try {
    const response = await send<{ ok: boolean; error?: string }>({ type: "CELIKOM_SET_API_ACCESS", token: input.value });
    if (response?.ok) {
      input.value = "";
      note.textContent = "Сервер подтвердил код";
    } else {
      const explanations: Record<string, string> = {
        invalid_access_code: "Неверная длина кода",
        api_access_denied: "Сервер отклонил код",
        api_forbidden: "Доступ запрещён",
        api_network_error: "Нет связи с сервером",
        api_server_error: "Ошибка сервера",
        api_http_error: "HTTP ошибка",
        invalid_api_response: "Некорректный ответ API",
        invalid_api_origin: "Неверный адрес API"
      };
      note.textContent = explanations[response?.error || ""] || "Не удалось проверить доступ";
    }
  } catch (_error) { note.textContent = "Не удалось проверить доступ"; }
});

stopButton?.addEventListener("click", async () => {
  render(await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: false }));
});

restoreButton?.addEventListener("click", async () => {
  await send({ type: COMMANDS.restoreOriginal });
  if (status) status.textContent = "Оригинал восстановлен";
});

diagnosticsButton?.addEventListener("click", async () => {
  const state = await send<ExtensionState>({ type: COMMANDS.getStatus });
  lastState = state;
  await navigator.clipboard.writeText(JSON.stringify(lastState, null, 2));
  if (diagnosticsButton) diagnosticsButton.textContent = "Скопировано";
});

async function refresh(): Promise<void> {
  try {
    render(await send<ExtensionState>({ type: COMMANDS.getStatus }));
  } catch (_error) {
    if (status) status.textContent = "Нет связи";
  }
}

void refresh();
window.setInterval(() => void refresh(), 1000);
