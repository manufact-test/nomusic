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

const addTrackButton = document.querySelector<HTMLButtonElement>("[data-action='add']");
const uploadPanel = document.querySelector<HTMLElement>("[data-upload-panel]");
const uploadForm = document.querySelector<HTMLFormElement>("[data-upload-form]");
const uploadTrack = document.querySelector<HTMLInputElement>("[data-upload-track]");
const uploadFile = document.querySelector<HTMLInputElement>("[data-upload-file]");
const uploadFilePicker = document.querySelector<HTMLElement>("[data-file-picker]");
const uploadFileTitle = document.querySelector<HTMLElement>("[data-file-title]");
const uploadFileName = document.querySelector<HTMLElement>("[data-file-name]");
const uploadKey = document.querySelector<HTMLInputElement>("[data-upload-key]");
const uploadRights = document.querySelector<HTMLInputElement>("[data-upload-rights]");
const uploadProgress = document.querySelector<HTMLProgressElement>("[data-upload-progress]");
const uploadStatus = document.querySelector<HTMLElement>("[data-upload-status]");
const uploadButton = document.querySelector<HTMLButtonElement>("[data-upload-submit]");
const uploadResult = document.querySelector<HTMLElement>("[data-upload-result]");
const uploadResultTitle = document.querySelector<HTMLElement>("[data-upload-result-title]");
const uploadResultNote = document.querySelector<HTMLElement>("[data-upload-result-note]");
let pinnedTrack: ReturnType<typeof uploadTargetFromStatus> = null;
let uploadRequestId: string | null = null;
let uploading = false;
let opening = false;

// Animate the old measured panel height to its finished size on the same frame.
// Chrome popup resizes with this transition instead of snapping between layouts.
// Without DOM animation support (or with reduced motion), content remains usable.
function transitionUploadPanel(update: () => void): void {
  const panel = uploadPanel;
  if (!panel) { update(); return; }
  const oldHeight = panel.hidden ? 0 : panel.getBoundingClientRect?.().height;
  const entering = panel.hidden;
  update();
  const newHeight = panel.hidden ? 0 : panel.getBoundingClientRect?.().height;
  if (typeof oldHeight !== "number" || typeof newHeight !== "number" ||
      typeof panel.animate !== "function" || !panel.style ||
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  panel.style.overflow = "hidden";
  const anim = panel.animate([
    { height: oldHeight + "px", opacity: entering ? 0 : 1 },
    { height: newHeight + "px", opacity: panel.hidden ? 0 : 1 }
  ], { duration: entering ? 300 : 290, easing: "cubic-bezier(.2,.75,.25,1)" });
  const release = () => { panel.style.overflow = ""; };
  anim.onfinish = release;
  anim.oncancel = release;
}

function uploadMessage(value: string, kind = "info"): void {
  if (!uploadStatus) return;
  uploadStatus.textContent = value;
  uploadStatus.dataset.kind = kind;
  uploadStatus.hidden = !value;
}

function setSubmittedView(title: string, note: string): void {
  if (uploadResultTitle) uploadResultTitle.textContent = title;
  if (uploadResultNote) uploadResultNote.textContent = note;
  if (uploadResult) uploadResult.hidden = false;
  if (uploadForm) uploadForm.hidden = true;
  if (uploadStatus) uploadStatus.hidden = true;
  if (uploadButton) uploadButton.disabled = true;
  if (uploadKey) uploadKey.value = "";
}

function showSubmitted(title: string, note: string): void {
  transitionUploadPanel(() => setSubmittedView(title, note));
}

function setPickerState(): void {
  const file = uploadFile?.files?.[0];
  if (uploadFilePicker) uploadFilePicker.dataset.selected = String(Boolean(file));
  if (uploadFileTitle) uploadFileTitle.textContent = file ? "MP3 выбран" : "Выбрать MP3";
  if (uploadFileName) {
    uploadFileName.textContent = file
      ? file.name + " · " + (file.size / 1048576).toFixed(1).replace(".", ",") + " МиБ"
      : "Нажмите или перетащите файл сюда";
  }
}

function resetUploadPanel(): void {
  if (uploadResult) uploadResult.hidden = true;
  if (uploadForm) uploadForm.hidden = true;
  if (uploadButton) { uploadButton.disabled = true; uploadButton.textContent = "Отправить на проверку"; }
  if (uploadProgress) { uploadProgress.hidden = true; uploadProgress.value = 0; }
  if (uploadStatus) uploadStatus.hidden = true;
  if (uploadFile) uploadFile.value = "";
  if (uploadRights) uploadRights.checked = false;
  uploadRequestId = null;
  pinnedTrack = null;
  setPickerState();
}

async function uploadApiOrigin(): Promise<string> {
  const config = await fetch(chrome.runtime.getURL("api/config.json")).then((response) => response.json());
  return privateUploadApiOrigin(config.baseUrl);
}

async function trackUploadStatus(origin: string, trackId: string): Promise<"none" | "pending" | "approved"> {
  const response = await fetch(origin + "/api/v1/tracks/upload-status?service=yandex&track_id=" + encodeURIComponent(trackId), {
    method: "GET", redirect: "error", credentials: "omit", cache: "no-store",
    signal: AbortSignal.timeout(10000)
  });
  if (!response.ok) throw new Error("upload_status_unavailable");
  const value = await response.json();
  if (value?.status !== "none" && value?.status !== "pending" && value?.status !== "approved") {
    throw new Error("invalid_upload_status");
  }
  return value.status;
}

addTrackButton?.addEventListener("click", async () => {
  if (!uploadPanel || uploading || opening) return;
  if (!uploadPanel.hidden) {
    // Do not clear the accepted state until a new explicit open.
    transitionUploadPanel(() => { uploadPanel.hidden = true; });
    addTrackButton.setAttribute("aria-expanded", "false");
    return;
  }
  opening = true;
  addTrackButton.disabled = true;
  addTrackButton.dataset.loading = "true";
  addTrackButton.textContent = "Проверяем трек…";
  // Keep the panel hidden until the final server answer is ready.
  // No intermediate fragment of a form is ever displayed.
  resetUploadPanel();
  let view: "form" | "result" | "error" = "error";
  let title = "";
  let note = "";
  try {
    pinnedTrack = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (uploadTrack) uploadTrack.value = pinnedTrack?.id || "";
    if (!pinnedTrack) {
      note = "Сначала запустите песню в Яндекс Музыке и дождитесь определения Track ID.";
    } else {
      const origin = await uploadApiOrigin();
      const serverState = await trackUploadStatus(origin, pinnedTrack.id);
      if (serverState === "pending") {
        view = "result";
        title = "Трек уже добавлен";
        note = "Альтернативная версия ожидает проверки администратора. Повторная загрузка не требуется.";
      } else if (serverState === "approved") {
        view = "result";
        title = "Версия уже доступна";
        note = "Для этой песни уже есть одобренная версия. Повторная отправка не требуется.";
      } else {
        view = "form";
      }
    }
  } catch (_error) {
    note = "Не удалось проверить трек на сервере. Закройте форму и попробуйте снова.";
  } finally {
    transitionUploadPanel(() => {
      if (view === "form") {
        if (uploadForm) uploadForm.hidden = false;
        if (uploadButton) uploadButton.disabled = false;
      } else if (view === "result") {
        setSubmittedView(title, note);
      } else {
        uploadMessage(note, "error");
      }
      uploadPanel.hidden = false;
    });
    opening = false;
    addTrackButton.disabled = false;
    addTrackButton.dataset.loading = "false";
    addTrackButton.textContent = "Добавить трек";
    addTrackButton.setAttribute("aria-expanded", "true");
  }
  void send({ type: "CELIKOM_ADD_TRACK_OPENED" }).catch(() => {});
});

uploadFile?.addEventListener("change", () => {
  uploadRequestId = null;
  if (uploadProgress) uploadProgress.value = 0;
  setPickerState();
});

// Native file picker via <label> and optional drag-and-drop share one validated input.
uploadFilePicker?.addEventListener("dragover", (event) => {
  event.preventDefault();
  if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
  uploadFilePicker.dataset.dragging = "true";
});
uploadFilePicker?.addEventListener("dragleave", () => {
  uploadFilePicker.dataset.dragging = "false";
});
uploadFilePicker?.addEventListener("drop", (event) => {
  event.preventDefault();
  uploadFilePicker.dataset.dragging = "false";
  const file = event.dataTransfer?.files?.[0];
  if (!file || !uploadFile) return;
  if (!validMp3Selection(file)) {
    uploadMessage("Выберите MP3 не более 30 МиБ.", "error"); return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  uploadFile.files = transfer.files;
  uploadRequestId = null;
  if (uploadProgress) uploadProgress.value = 0;
  setPickerState();
  uploadMessage("");
});

uploadForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (uploading || opening || !pinnedTrack || uploadForm.hidden ||
    !uploadFile?.files?.[0] || !uploadRights?.checked || !uploadKey?.value) return;

  const file = uploadFile.files[0];
  if (!validMp3Selection(file)) {
    uploadMessage("Выберите MP3 не более 30 МиБ.", "error"); return;
  }
  uploading = true;
  if (uploadButton) { uploadButton.disabled = true; uploadButton.textContent = "Отправляем…"; }
  uploadMessage("Проверяем трек и отправляем файл…", "checking");

  let origin: string;
  let transferStarted = false;
  try {
    const now = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (!now || now.id !== pinnedTrack.id) {
      uploadMessage("Трек изменился. Закройте и откройте «Добавить трек» заново.", "error");
      return;
    }
    origin = await uploadApiOrigin();
    const existing = await trackUploadStatus(origin, pinnedTrack.id);
    if (existing !== "none") {
      showSubmitted(existing === "pending" ? "Трек уже добавлен" : "Версия уже доступна",
        "Заявка уже есть в CELIKOM. Повторно отправлять файл не нужно.");
      return;
    }

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
    const xhr = new XMLHttpRequest();
    xhr.open("POST", origin + "/api/v1/uploads");
    xhr.timeout = 120000;
    xhr.setRequestHeader("Authorization", "Bearer " + uploadKey.value);
    xhr.upload.addEventListener("progress", (progress) => {
      if (progress.lengthComputable && uploadProgress) uploadProgress.value = Math.floor(progress.loaded / progress.total * 100);
    });
    if (uploadProgress) { uploadProgress.hidden = false; uploadProgress.value = 0; }
    uploadMessage("Загружаем MP3…", "checking");
    xhr.addEventListener("loadend", () => {
      uploading = false;
      if (xhr.status === 202) {
        try {
          const result = JSON.parse(xhr.responseText);
          if (result.status === "pending" && Number.isSafeInteger(result.replacement_id)) {
            showSubmitted(result.duplicate ? "Трек уже добавлен" : "Отправлено на проверку",
              "MP3 получен CELIKOM. Статус: ожидает модерации. Дополнительных действий не требуется.");
            uploadRequestId = null;
            return;
          }
        } catch (_error) { /* display neutral error */ }
      }
      let code = "";
      try { code = JSON.parse(xhr.responseText)?.error || ""; } catch (_error) { /* no-op */ }
      if (code === "track_pending" || code === "track_already_approved" || code === "already_approved") {
        showSubmitted(code === "track_pending" ? "Трек уже добавлен" : "Версия уже доступна",
          "Заявка уже есть на сервере CELIKOM. Повторная отправка не требуется.");
        return;
      }
      const errors: Record<string, string> = {
        uploads_disabled: "Приватный приём файлов пока выключен.",
        unauthorized: "Неверный код владельца.",
        rate_limited: "Слишком много попыток. Попробуйте позже.",
        upload_too_large: "Файл превышает допустимый размер.",
        invalid_mp3: "Файл не прошёл проверку MP3.",
        idempotency_conflict: "Повтор запроса не совпадает с исходным.",
        rights_declaration_required: "Подтвердите права на файл."
      };
      uploadMessage(errors[code] || "Загрузка не завершена. Попробуйте ещё раз.", "error");
      if (uploadButton) { uploadButton.textContent = "Повторить отправку"; uploadButton.disabled = false; }
    });
    xhr.send(data);
    transferStarted = true;
  } catch (_error) {
    uploadMessage("Не удалось связаться с сервером. Повторите попытку.", "error");
  } finally {
    // The request completion handler is responsible for re-enabling the button
    // after xhr.send(). An early exit must never leave the UI stuck.
    if (!transferStarted) {
      uploading = false;
      if (uploadButton && uploadForm && !uploadForm.hidden) {
        uploadButton.disabled = false;
        uploadButton.textContent = "Отправить на проверку";
      }
    }
  }
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
