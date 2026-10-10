import { COMMANDS, type ExtensionState } from "../shared/messages.js";
import { uploadTargetFromStatus, validMp3Selection, privateUploadApiOrigin } from "../upload/contract.js";
import { initAuthPanel } from "../auth/auth-popup.js";

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
  const state = await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: true });
  render(state);
  const access = document.querySelector<HTMLElement>("[data-access-status]");
  if (access && state.accessError) {
    access.textContent = state.accessError === "track_required"
      ? "Сначала запустите песню в Яндекс Музыке."
      : state.accessError === "sign_in_required" ? "Войдите в аккаунт перед стартом."
      : "Доступ недоступен. Проверьте аккаунт и соединение.";
  } else await refreshAccess();
});

const addTrackButton = document.querySelector<HTMLButtonElement>("[data-action='add']");
const uploadPanel = document.querySelector<HTMLElement>("[data-upload-panel]");
const uploadForm = document.querySelector<HTMLFormElement>("[data-upload-form]");
const uploadTrack = document.querySelector<HTMLInputElement>("[data-upload-track]");
const uploadFile = document.querySelector<HTMLInputElement>("[data-upload-file]");
const uploadFilePicker = document.querySelector<HTMLElement>("[data-file-picker]");
const uploadFileTitle = document.querySelector<HTMLElement>("[data-file-title]");
const uploadFileName = document.querySelector<HTMLElement>("[data-file-name]");
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

// Chrome automatically sizes extension popups. Animating panel height caused
// a visible expand-shrink bounce when the form exceeded the popup viewport.
// Render only the final resolved content and softly fade it in without
// animating layout size (including when result replaces the form).
function transitionUploadPanel(update: () => void): void {
  const panel = uploadPanel;
  update();
  if (!panel || panel.hidden || typeof panel.animate !== "function" ||
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  panel.animate([
    { opacity: 0.72 },
    { opacity: 1 }
  ], { duration: 150, easing: "ease-out" });
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

async function contributionAccess(): Promise<string> {
  const result = await send<{ ok: boolean; access_token?: string; error?: string }>({ type: "CELIKOM_AUTH", action: "contribution-access" });
  if (!result.ok || !/^[a-f0-9]{64}$/.test(result.access_token || "")) throw new Error(result.error || "invalid_session");
  return result.access_token!;
}
function contributionError(error: unknown): string {
  const code = (error as { message?: string })?.message;
  if (code === "uploads_disabled") return "Приём версий и предложений пока выключен. Доступ к музыке работает отдельно.";
  if (code === "invalid_session") return "Войдите в аккаунт, чтобы отправить версию или предложение.";
  if (code === "access_denied") return "Доступ завершён. Проверьте статус аккаунта.";
  return "Не удалось связаться с сервером. Повторите попытку.";
}

async function trackUploadStatus(origin: string, trackId: string): Promise<"none" | "pending" | "approved"> {
  const response = await fetch(origin + "/api/v1/tracks/upload-status?service=yandex&track_id=" + encodeURIComponent(trackId), {
    method: "GET", redirect: "error", credentials: "omit", cache: "no-store",
    headers: { Authorization: "Bearer " + await contributionAccess() },
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
  } catch (error) {
    note = contributionError(error);
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
    addTrackButton.textContent = "Загрузить версию";
    addTrackButton.setAttribute("aria-expanded", "true");
  }
  void send({ type: "CELIKOM_ADD_TRACK_OPENED" }).catch(() => {});
});

uploadFile?.addEventListener("change", () => {
  uploadRequestId = null;
  if (uploadProgress) uploadProgress.value = 0;
  setPickerState();
  uploadMessage("");
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
    !uploadFile?.files?.[0] || !uploadRights?.checked) return;

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
      uploadMessage("Трек изменился. Закройте и откройте «Загрузить версию» заново.", "error");
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
    xhr.setRequestHeader("Authorization", "Bearer " + await contributionAccess());
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
        uploads_disabled: "Приём файлов пока выключен.",
        access_denied: "Доступ завершён. Проверьте статус аккаунта.",
        unauthorized: "Войдите в аккаунт ещё раз.",
        invalid_session: "Войдите в аккаунт ещё раз.",
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
const suggestButton = document.querySelector<HTMLButtonElement>("[data-action='suggest']");
const suggestPanel = document.querySelector<HTMLElement>("[data-suggest-panel]");
const suggestSubmit = document.querySelector<HTMLButtonElement>("[data-suggest-submit]");
const suggestNote = document.querySelector<HTMLElement>("[data-suggest-note]");
let suggestTrack: ReturnType<typeof uploadTargetFromStatus> = null;
let suggesting = false;
suggestButton?.addEventListener("click", async () => {
  if (!suggestPanel || suggesting) return;
  if (!suggestPanel.hidden) { suggestPanel.hidden = true; suggestButton.setAttribute("aria-expanded", "false"); return; }
  suggestTrack = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
  const label = document.querySelector<HTMLElement>("[data-suggest-track]");
  if (label) label.textContent = suggestTrack ? [suggestTrack.title || "Track ID " + suggestTrack.id, suggestTrack.artist].filter(Boolean).join(" — ") : "Сначала запустите песню в Яндекс Музыке.";
  if (suggestSubmit) suggestSubmit.disabled = !suggestTrack;
  if (suggestNote) suggestNote.hidden = true;
  suggestPanel.hidden = false;
  suggestButton.setAttribute("aria-expanded", "true");
});
suggestSubmit?.addEventListener("click", async () => {
  if (!suggestTrack || suggesting || !suggestNote) return;
  suggesting = true;
  suggestSubmit.disabled = true;
  suggestNote.hidden = false;
  suggestNote.textContent = "Отправляем…";
  try {
    const current = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (!current || current.id !== suggestTrack.id) throw new Error("track_changed");
    const body = new FormData();
    for (const [name, value] of Object.entries({ service: "yandex", track_id: suggestTrack.id, artist: suggestTrack.artist, title: suggestTrack.title })) body.append(name, value);
    const response = await fetch((await uploadApiOrigin()) + "/api/v1/track-requests", {
      method: "POST", body, credentials: "omit", redirect: "error", cache: "no-store", signal: AbortSignal.timeout(15000),
      headers: { Authorization: "Bearer " + await contributionAccess() }
    });
    const result = await response.json();
    if (response.status !== 202 || !["pending", "reviewed", "rejected"].includes(result.status)) throw new Error(result.error || "request_failed");
    suggestNote.textContent = result.status === "pending" ? "Предложение отправлено на рассмотрение." : "Это предложение уже рассмотрено.";
    suggestTrack = null;
  } catch (error) {
    const code = (error as Error)?.message;
    suggestNote.textContent = code === "track_changed" ? "Трек изменился. Закройте и откройте предложение заново." : code === "rate_limited" ? "Слишком много попыток. Попробуйте позже." : contributionError(error);
    suggestSubmit.disabled = false;
  } finally { suggesting = false; }
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

async function refreshAccess(): Promise<void> {
  const label = document.querySelector<HTMLElement>("[data-access-status]");
  if (!label) return;
  try {
    const state = await send<{ ok: boolean; entitlement?: { allowed: boolean; valid_until: string | null; reason: string } }>({ type: "CELIKOM_AUTH", action: "entitlement" });
    const access = state.entitlement;
    if (!state.ok || !access) { label.textContent = "Войдите в аккаунт, чтобы начать"; return; }
    if (access.allowed && access.valid_until) {
      label.textContent = "Пробный доступ до " + new Date(access.valid_until).toLocaleString("ru-RU", { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" });
    } else label.textContent = access.reason === "trial_not_started" ? "3 дня пробного доступа начнутся после «Старт»" : "Пробный доступ завершён";
  } catch (_error) { label.textContent = "Нет связи. Оригинальная музыка доступна."; }
}
void refreshAccess();
window.setInterval(() => void refreshAccess(), 15000);

// Account UI retains the accepted email/recovery flow.
initAuthPanel(send);
