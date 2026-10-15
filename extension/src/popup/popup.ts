import { withDeadline } from "../shared/request-deadline.js";
import { inspectM4a } from "../upload/m4a.js";
import { mp3DurationMs, durationNotice } from "../upload/mp3-duration.js";
import { initScrollSpacing } from "./scroll-spacing.js";
import { COMMANDS, type ExtensionState } from "../shared/messages.js";
import { uploadTargetFromStatus, validAudioSelection, privateUploadApiOrigin } from "../upload/contract.js";
import { initAuthPanel } from "../auth/auth-popup.js";
import { initAccessStatus } from "../auth/access-status.js";
import { initVersionStatus } from "./version-status.js";
import { readDisplay, writeDisplay, stableText } from "./display-cache.js";
import { initSupport } from "./support.js";
import { initIncidentStatus } from "./incident-status.js";

const status = document.querySelector<HTMLElement>("[data-status]");
const startButton = document.querySelector<HTMLButtonElement>("[data-action='start']");
const stopButton = document.querySelector<HTMLButtonElement>("[data-action='stop']");
const restoreButton = document.querySelector<HTMLButtonElement>("[data-action='restore']");
const diagnosticsButton = document.querySelector<HTMLButtonElement>("[data-action='diagnostics']");
const track = document.querySelector<HTMLElement>("[data-track]");
let lastState: ExtensionState | null = null;
const incidentStatus = initIncidentStatus({ onChange: () => { if (lastState) render(lastState); } });
const refreshVersion = initVersionStatus(send);
const cachedTrack = readDisplay("track");
if (/^[1-9]\d{0,23}$/.test(cachedTrack?.id || "") && typeof cachedTrack.label === "string" && cachedTrack.label.length <= 512) {
  stableText(track, cachedTrack.label, false);
  if (track) track.dataset.detected = "true";
}

function render(state: ExtensionState): void {
  if (!status || !startButton || !stopButton) return;
  lastState = state;
  incidentStatus.updateController(state);
  // Retire the old song's form, selected file and request ID together.
  if (pinnedTrack && pinnedTrack.id !== state.track?.id && !uploading && !opening) {
    resetUploadPanel();
    if (uploadPanel) uploadPanel.hidden = true;
    addTrackButton?.setAttribute("aria-expanded", "false");
  }
  const labels: Record<ExtensionState["phase"], string> = {
    STOPPED: "Остановлен",
    CONNECTING: "Подключение…",
    OBSERVING: "Ищем трек…",
    READY: "Трек определён",
    ERROR: "Ошибка подключения",
    PREPARING: "Готовим подмену…",
    REPLACEMENT_ACTIVE: "Подмена активна",
    RESTORING: "Возвращаем оригинал…"
  };
  status.textContent = incidentStatus.active() ? "Сбой интеграции" : !state.enabled ? labels.STOPPED : state.suspended ? state.replacementError === "service_incident" ? "Сбой интеграции" : "Восстанавливаем связь…" : state.manualBypass ? "Оригинал" : state.replacementError ? state.recovering ? "Оригинал · восстанавливаем связь" : "Оригинал · ошибка подмены" : labels[state.phase] || "Проверка…";
  const connected=state.enabled && !incidentStatus.active() && state.phase!=="ERROR" && !state.connection?.error && state.bridge?.healthy===true && !state.suspended && !state.replacementError && !state.startupError;
  status.dataset.active = String(connected);
  document.querySelector<HTMLElement>(".mark")?.setAttribute("data-active",String(connected));
  startButton.disabled = state.enabled && state.phase !== "ERROR" && !state.manualBypass && !state.replacementError;
  if (starting) startButton.disabled = true;
  startButton.textContent = state.phase === "ERROR" ? "Повторить" : "Старт";
  stopButton.disabled = !state.enabled && !starting;
  if (track) {
    const title = state.track?.metadata?.title?.trim();
    const artist = state.track?.metadata?.artist?.trim();
    const label = state.track?.id
      ? [title || `Track ID ${state.track.id}`, artist].filter(Boolean).join(" — ")
      : state.connection?.detail || (state.enabled ? "Запустите трек в Яндекс Музыке" : "CELIKOM остановлен");
    stableText(track, label);
    writeDisplay("track", { id: state.track?.id || null, label: label.slice(0, 512) });
    track.dataset.detected = String(Boolean(state.track?.id));
    track.title = state.track?.id
      ? `Track ID ${state.track.id} · confidence ${state.track.confidence}`
      : "";
  }
  void refreshVersion(state);
}

async function send<T>(message: object): Promise<T> {
  const intent = message as { type?: string; enabled?: boolean };
  const startingPlayback = intent.type === COMMANDS.setEnabled && intent.enabled === true;
  return withDeadline(() => chrome.runtime.sendMessage(message) as Promise<T>, startingPlayback ? 60000 : 30000);
}

let starting = false, startGeneration = 0;
startButton?.addEventListener("click", async () => {
  if (starting || incidentStatus.active()) return;
  const generation = ++startGeneration;
  starting = true;
  startButton.disabled = true;
  if (stopButton) stopButton.disabled = false;
  const access = document.querySelector<HTMLElement>("[data-access-status]");
  if (access) { access.textContent = "Проверяем доступ…"; access.dataset.kind = "loading"; }
  try {
    const state = await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: true });
    if (generation !== startGeneration) return;
    if (state.accessError === "sign_in_required") accountPanel?.requireLogin();
    else render(state);
    if (access && state.accessError) {
      access.dataset.kind = "error";
      access.textContent = state.accessError === "track_required"
        ? "Сначала запустите песню в Яндекс Музыке."
        : state.accessError === "sign_in_required" ? "Войдите в аккаунт, чтобы включить подмену музыки."
        : "Доступ недоступен. Проверьте аккаунт и соединение.";
    } else { if (access) delete access.dataset.kind; await refreshAccess(); }
  } catch (_) {
    if (generation === startGeneration && access) { access.dataset.kind = "error"; access.textContent = "Проверка не завершена. Повторите «Старт»."; }
  } finally {
    if (generation === startGeneration) {
      starting = false;
      startButton.disabled = Boolean(lastState?.enabled && !lastState?.replacementError && !lastState?.manualBypass && lastState?.phase !== "ERROR");
      if (stopButton) stopButton.disabled = !lastState?.enabled;
    }
  }
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
const durationNote=document.querySelector<HTMLElement>("[data-upload-duration]");
let durationGeneration=0, measuredFile=null, durationPromise=null, durationBlocked=false;
function checkFileDuration(){
  const file=uploadFile?.files?.[0], target=pinnedTrack, generation=++durationGeneration;
  measuredFile=file;durationPromise=null;durationBlocked=false;
  if(!durationNote||!file||!target){if(durationNote)durationNote.hidden=true;return Promise.resolve();}
  if(uploadButton)uploadButton.disabled=true;
  durationNote.hidden=false;durationNote.dataset.kind="warning";durationNote.textContent="Проверяем длительность файла…";
  durationPromise=withDeadline(()=>file.arrayBuffer(),10000).then(bytes=>/\.m4a$/i.test(file.name)?inspectM4a(bytes).durationMs:mp3DurationMs(bytes)).catch(()=>null).then(ms=>{
    if(generation!==durationGeneration||pinnedTrack?.id!==target.id||uploadFile?.files?.[0]!==file)return;
    const notice=durationNotice(target.durationMs,ms);durationNote.textContent=notice.text;durationNote.dataset.kind=notice.kind;durationBlocked=notice.blocked===true;
    if(uploadButton&&!uploading)uploadButton.disabled=durationBlocked;
    if(notice.kind!=="ok")durationNote.scrollIntoView?.({block:"nearest",behavior:"smooth"});
  });
  return durationPromise;
}

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
  if(durationNote)durationNote.hidden=true;
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
  if (uploadFileTitle) uploadFileTitle.textContent = file ? "Файл выбран" : "Выбрать MP3 или M4A";
  if (uploadFileName) {
    uploadFileName.textContent = file
      ? file.name + " · " + (file.size / 1048576).toFixed(1).replace(".", ",") + " МиБ"
      : "Нажмите или перетащите файл сюда";
  }
}

function resetUploadPanel(): void {
  durationGeneration++;measuredFile=null;durationPromise=null;durationBlocked=false;if(durationNote)durationNote.hidden=true;
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
  const config = await withDeadline(() => fetch(chrome.runtime.getURL("api/config.json")).then((response) => response.json()), 10000);
  return privateUploadApiOrigin(config.baseUrl);
}

async function contributionAccess(): Promise<string> {
  const result = await send<{ ok: boolean; access_token?: string; error?: string }>({ type: "CELIKOM_AUTH", action: "contribution-access" });
  if (!result?.ok || !/^[a-f0-9]{64}$/.test(result.access_token || "")) throw new Error(result.error || "invalid_session");
  return result.access_token!;
}
function contributionError(error: unknown): string {
  const code = (error as { message?: string })?.message;
  if (code === "track_changed") return "Песня сменилась во время проверки. Нажмите «Загрузить версию» для текущей песни.";
  if (code === "uploads_disabled") return "Приём версий и предложений пока выключен. Доступ к музыке работает отдельно.";
  if (code === "invalid_session") return "Войдите в аккаунт, чтобы отправить версию или предложение.";
  if (code === "access_denied") return "Доступ завершён. Проверьте статус аккаунта.";
  return "Не удалось связаться с сервером. Повторите попытку.";
}

async function trackUploadStatus(origin: string, trackId: string): Promise<"none" | "pending" | "approved"> {
  // Retry only this read. Audio submission is never automatically replayed.
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const response = await fetch(origin + "/api/v1/tracks/upload-status?service=yandex&track_id=" + encodeURIComponent(trackId), {
        method: "GET", redirect: "error", credentials: "omit", cache: "no-store",
        headers: { Authorization: "Bearer " + await contributionAccess() },
        signal: AbortSignal.timeout(10000)
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        if (attempt === 0 && (response.status >= 500 || response.status === 401)) {
          await new Promise(resolve => setTimeout(resolve, 250)); continue;
        }
        throw new Error(error.error || "upload_status_unavailable");
      }
      const value = await response.json();
      if (!["none", "pending", "approved"].includes(value?.status)) throw new Error("invalid_upload_status");
      return value.status;
    } catch (error) {
      const transient = error instanceof TypeError || (error as Error)?.name === "TimeoutError" ||
        ["auth_timeout", "auth_network_error", "auth_unavailable"].includes((error as Error)?.message);
      if (attempt || !transient) throw error;
      await new Promise(resolve => setTimeout(resolve, 250));
    }
  }
  throw new Error("upload_status_unavailable");
}

addTrackButton?.addEventListener("click", async () => {
  if (incidentStatus.active() || !uploadPanel || uploading || opening) return;
  if (!uploadPanel.hidden) {
    // Query first: a click immediately after a song switch must open the
    // new song, even before the next one-second status poll.
    opening = true;
    try {
      const current = await send<ExtensionState>({ type: COMMANDS.getStatus });
      opening = false;
      render(current);
    } catch (error) {
      opening = false;
      resetUploadPanel();
      uploadMessage(contributionError(error), "error");
      return;
    }
    if (!uploadPanel.hidden && (uploadStatus?.hidden || uploadStatus?.dataset.kind !== "error")) {
      transitionUploadPanel(() => { uploadPanel.hidden = true; });
      addTrackButton.setAttribute("aria-expanded", "false");
      return;
    }
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
    const state = await send<ExtensionState>({ type: COMMANDS.getStatus });
    render(state);
    pinnedTrack = uploadTargetFromStatus(state);
    if (uploadTrack) uploadTrack.value = pinnedTrack?.id || "";
    if (!pinnedTrack) {
      note = "Сначала запустите песню в Яндекс Музыке и дождитесь определения Track ID.";
    } else {
      const target = pinnedTrack;
      const origin = await uploadApiOrigin();
      const serverState = await trackUploadStatus(origin, target.id);
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
      const current = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
      if (current?.id !== target.id) throw new Error("track_changed");
    }
  } catch (error) {
    view = "error";
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
  void checkFileDuration();
});

uploadFile?.addEventListener("cancel", () => {
  if (uploading) return;
  setPickerState();
  if (!uploadFile.files?.[0]) {
    uploadRequestId = null;
    if (uploadProgress) { uploadProgress.hidden = true; uploadProgress.value = 0; }
    uploadMessage("");
    void checkFileDuration();
  }
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
  if(uploading||opening)return;
  const file = event.dataTransfer?.files?.[0];
  if (!file || !uploadFile) return;
  if (!validAudioSelection(file)) {
    uploadMessage("Выберите MP3 или M4A не более 30 МиБ.", "error"); return;
  }
  const transfer = new DataTransfer();
  transfer.items.add(file);
  uploadFile.files = transfer.files;
  uploadRequestId = null;
  if (uploadProgress) uploadProgress.value = 0;
  setPickerState();
  uploadMessage("");
  void checkFileDuration();
});

uploadForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (uploading || opening || !pinnedTrack || uploadForm.hidden ||
    !uploadFile?.files?.[0] || !uploadRights?.checked) return;

  const file = uploadFile.files[0];
  if (!validAudioSelection(file)) {
    uploadMessage("Выберите MP3 или M4A не более 30 МиБ.", "error"); return;
  }
  uploading = true;
  if(uploadFile)uploadFile.disabled=true;
  if (uploadButton) { uploadButton.disabled = true; uploadButton.textContent = "Отправляем…"; }
  uploadMessage("Проверяем трек и отправляем файл…", "checking");

  let origin: string;
  let transferStarted = false;
  try {
    if(measuredFile!==file)await checkFileDuration();else if(durationPromise)await durationPromise;
    if(durationBlocked){uploadMessage("");durationNote?.scrollIntoView?.({block:"nearest",behavior:"smooth"});return;}
    const now = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (!now || now.id !== pinnedTrack.id) {
      uploadMessage("Трек изменился. Закройте и откройте «Загрузить версию» заново.", "error");
      return;
    }
    origin = await uploadApiOrigin();
    const existing = await trackUploadStatus(origin, pinnedTrack.id);
    const checkedTarget = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (checkedTarget?.id !== pinnedTrack.id) throw new Error("track_changed");
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
    const finalTarget = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (finalTarget?.id !== pinnedTrack.id) throw new Error("track_changed");
    xhr.upload.addEventListener("progress", (progress) => {
      if (progress.lengthComputable && uploadProgress) uploadProgress.value = Math.floor(progress.loaded / progress.total * 100);
    });
    if (uploadProgress) { uploadProgress.hidden = false; uploadProgress.value = 0; }
    uploadMessage("Загружаем аудиофайл…", "checking");
    xhr.addEventListener("loadend", () => {
      uploading = false;
      if(uploadFile)uploadFile.disabled=false;
      if (xhr.status === 202) {
        try {
          const result = JSON.parse(xhr.responseText);
          if (result.status === "pending" && Number.isSafeInteger(result.replacement_id)) {
            showSubmitted(result.duplicate ? "Трек уже добавлен" : "Отправлено на проверку",
              "Аудиофайл получен CELIKOM. Статус: ожидает модерации. Дополнительных действий не требуется.");
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
        invalid_m4a: "M4A не поддерживается или повреждён. Нужен M4A с кодеком AAC без защиты DRM.",
        duration_mismatch: "Длительность файла не подходит для подмены. Выберите подходящую версию.",
        idempotency_conflict: "Повтор запроса не совпадает с исходным.",
        rights_declaration_required: "Подтвердите права на файл."
      };
      uploadMessage(errors[code] || "Загрузка не завершена. Попробуйте ещё раз.", "error");
      if (uploadButton) { uploadButton.textContent = "Повторить отправку"; uploadButton.disabled = false; }
    });
    xhr.send(data);
    transferStarted = true;
  } catch (error) {
    uploadMessage(contributionError(error), "error");
  } finally {
    // The request completion handler is responsible for re-enabling the button
    // after xhr.send(). An early exit must never leave the UI stuck.
    if (!transferStarted) {
      uploading = false;
      if(uploadFile)uploadFile.disabled=false;
      if (uploadButton && uploadForm && !uploadForm.hidden) {
        uploadButton.disabled = durationBlocked;
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
let suggesting = false, suggestOpening=false, suggestGeneration=0;
const suggestResult=document.querySelector<HTMLElement>("[data-suggest-result]");
function suggestPresence(status){
  if(!["approved","pending"].includes(status))return false;
  if(suggestResult)suggestResult.hidden=false;
  const title=document.querySelector<HTMLElement>("[data-suggest-result-title]"),note=document.querySelector<HTMLElement>("[data-suggest-result-note]");
  if(title)title.textContent=status==="approved"?"Версия уже доступна":"Версия уже на проверке";
  if(note)note.textContent=status==="approved"?"Версия песни CELIKOM уже загружена и доступна. Предлагать её повторно не нужно.":"Версия песни уже отправлена на модерацию. Предлагать её повторно не нужно.";
  if(suggestSubmit)suggestSubmit.hidden=true;
  if(suggestNote)suggestNote.hidden=true;
  return true;
}
async function suggestionStatus(id){
  const result=await send<any>({type:"CELIKOM_AUTH",action:"track-status",track_id:id});
  if(!result?.ok||!["none","pending","approved"].includes(result.status))throw new Error(result?.error||"auth_unavailable");
  return result.status;
}
suggestButton?.addEventListener("click",async()=>{
  if(incidentStatus.active()||!suggestPanel||suggesting||suggestOpening)return;
  if(!suggestPanel.hidden){suggestGeneration++;suggestPanel.hidden=true;suggestButton.setAttribute("aria-expanded","false");return;}
  const generation=++suggestGeneration;suggestOpening=true;suggestButton.disabled=true;suggestButton.textContent="Проверяем…";suggestButton.setAttribute("aria-busy","true");
  suggestSubmit&&(suggestSubmit.disabled=true);if(suggestSubmit)suggestSubmit.hidden=false;
  if(suggestResult)suggestResult.hidden=true;if(suggestNote)suggestNote.hidden=true;
  try {
    suggestTrack=uploadTargetFromStatus(await send<ExtensionState>({type:COMMANDS.getStatus}));
    const label=document.querySelector<HTMLElement>("[data-suggest-track]");
    if(label)label.textContent=suggestTrack?[suggestTrack.title||"Track ID "+suggestTrack.id,suggestTrack.artist].filter(Boolean).join(" — "):"Сначала запустите песню в Яндекс Музыке.";
    if(suggestTrack){
      const presence=await suggestionStatus(suggestTrack.id);
      const current=uploadTargetFromStatus(await send<ExtensionState>({type:COMMANDS.getStatus}));
      if(current?.id!==suggestTrack.id)throw new Error("track_changed");
      if(generation!==suggestGeneration)return;
      if(!suggestPresence(presence)&&suggestSubmit)suggestSubmit.disabled=false;
    }
  }catch(error){if(suggestNote){suggestNote.hidden=false;suggestNote.textContent=(error as Error)?.message==="track_changed"?"Трек изменился. Откройте предложение заново.":contributionError(error);}}
  finally{suggestOpening=false;suggestButton.disabled=false;suggestButton.textContent="Предложить песню";suggestButton.setAttribute("aria-busy","false");if(generation===suggestGeneration){suggestPanel.hidden=false;suggestButton.setAttribute("aria-expanded","true");}}
});
suggestSubmit?.addEventListener("click",async()=>{
  if(!suggestTrack||suggesting||suggestOpening||!suggestNote)return;
  suggesting=true;suggestSubmit.disabled=true;suggestNote.hidden=false;suggestNote.textContent="Отправляем…";
  try {
    const current=uploadTargetFromStatus(await send<ExtensionState>({type:COMMANDS.getStatus}));
    if(!current||current.id!==suggestTrack.id)throw new Error("track_changed");
    if(suggestPresence(await suggestionStatus(suggestTrack.id)))return;
    const body=new FormData();
    for(const [name,value] of Object.entries({service:"yandex",track_id:suggestTrack.id,artist:suggestTrack.artist,title:suggestTrack.title}))body.append(name,value);
    const origin=await uploadApiOrigin(),access=await contributionAccess();
    const final=uploadTargetFromStatus(await send<ExtensionState>({type:COMMANDS.getStatus}));
    if(final?.id!==suggestTrack.id)throw new Error("track_changed");
    const response=await fetch(origin+"/api/v1/track-requests",{method:"POST",body,credentials:"omit",redirect:"error",cache:"no-store",signal:AbortSignal.timeout(15000),headers:{Authorization:"Bearer "+access}});
    const result=await response.json();
    if(response.status===409&&["track_pending","track_already_approved"].includes(result.error)){suggestPresence(result.error==="track_pending"?"pending":"approved");return;}
    if(response.status!==202||!["pending","reviewed","rejected"].includes(result.status))throw new Error(result.error||"request_failed");
    suggestNote.textContent=result.status==="pending"?"Предложение отправлено на рассмотрение.":"Это предложение уже рассмотрено.";suggestTrack=null;
  }catch(error){const code=(error as Error)?.message;suggestNote.textContent=code==="track_changed"?"Трек изменился. Закройте и откройте предложение заново.":code==="rate_limited"?"Слишком много попыток. Попробуйте позже.":contributionError(error);suggestSubmit.disabled=false;}
  finally{suggesting=false;}
});

stopButton?.addEventListener("click", async () => {
  const generation = ++startGeneration; starting = false;
  const access = document.querySelector<HTMLElement>("[data-access-status]");
  if (startButton) startButton.disabled = false;
  try {
    const state = await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: false });
    if (generation !== startGeneration) return;
    render(state);
    if (access?.textContent === "Проверяем доступ…") access.textContent = "Проверка остановлена. Можно нажать «Старт» снова.";
  } catch (_) {
    if (status) status.textContent = "Нет связи. Обновите расширение.";
  }
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

let refreshing = false;
async function refresh(): Promise<void> {
  if (refreshing) return;
  refreshing = true;
  try {
    render(await send<ExtensionState>({ type: COMMANDS.getStatus }));
  } catch (_error) {
    if (status) status.textContent = "Нет связи";
  } finally { refreshing = false; }
}

void refresh();
window.setInterval(() => void refresh(), 1000);
void incidentStatus.refresh();
window.setInterval(() => void incidentStatus.refresh(), 5000);

const refreshAccess = initAccessStatus(send);
void refreshAccess();
window.setInterval(() => void refreshAccess(), 15000);

// Account UI retains the accepted email/recovery flow.
const accountPanel = initAuthPanel(send);

initScrollSpacing();

void initSupport({ send, getState: () => lastState });
