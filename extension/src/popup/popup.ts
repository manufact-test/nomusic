import { playbackPresentation } from "./playback-presentation.js";
import { withDeadline } from "../shared/request-deadline.js";
import { inspectM4a } from "../upload/m4a.js";
import { mp3DurationMs, durationNotice } from "../upload/mp3-duration.js";
import { createUploadJournal } from "../upload/upload-journal.js";
import { stageUploadFile, deleteStagedUpload } from "../upload/staging.js";
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
  const presentation=playbackPresentation(state);
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
  status.textContent = incidentStatus.active() ? "Сбой интеграции" : !state.enabled ? labels.STOPPED : state.suspended ? state.replacementError === "service_incident" ? "Сбой интеграции" : "Восстанавливаем связь…" : state.manualBypass ? "Оригинал" : state.replacementError ? state.recovering ? "Оригинал · восстанавливаем связь" : "Оригинал · ошибка подмены" : presentation.label || labels[state.phase] || "Проверка…";
  const connected=state.enabled && !incidentStatus.active() && state.phase!=="ERROR" && !state.connection?.error && state.bridge?.healthy===true && !state.suspended && !state.replacementError && !state.startupError && !["CONNECTING"].includes(state.phase);
  status.dataset.active = String(connected);
  document.querySelector<HTMLElement>(".mark")?.setAttribute("data-active",String(connected));
  startButton.disabled = presentation.startDisabled;
  if (starting) startButton.disabled = true;
  startButton.textContent = presentation.startLabel;
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
      startButton.disabled = Boolean(lastState && playbackPresentation(lastState).startDisabled);
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
const uploadTransferSlot = document.querySelector<HTMLElement>("[data-upload-transfer-slot]");
const uploadConfirm = document.querySelector<HTMLElement>("[data-upload-confirm]");
const uploadContinue = document.querySelector<HTMLButtonElement>("[data-upload-continue]");
const uploadStop = document.querySelector<HTMLButtonElement>("[data-upload-stop]");
let activeUploadXHR: XMLHttpRequest | null = null;
let manualUploadCancel = false;
let backgroundUploadMode = false;
const BACKGROUND_UPLOAD_KEY = "celikom_background_upload_v1";
const uploadResult = document.querySelector<HTMLElement>("[data-upload-result]");
const uploadResultTitle = document.querySelector<HTMLElement>("[data-upload-result-title]");
const uploadResultNote = document.querySelector<HTMLElement>("[data-upload-result-note]");
let pinnedTrack: ReturnType<typeof uploadTargetFromStatus> = null;
let uploadRequestId: string | null = null;
const uploadJournal = createUploadJournal(chrome.storage?.local);
let uploading = false;
let opening = false;
// Respect an explicit user close within this popup instance. The one-second
// background status poll must never reopen a panel the user just collapsed.
let uploadManuallyCollapsed = false;
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
    // Never scroll the popup on background validation: the user controls the viewport.
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

// Keep the same full-width action in place throughout the operation.
function uploadAction(mode: "submit" | "preparing" | "cancel" | "complete" | "retry"): void {
  if (!uploadButton) return;
  uploadButton.dataset.uploadMode = mode;
  uploadButton.type = mode === "cancel" ? "button" : "submit";
  uploadButton.disabled = mode === "preparing" || mode === "complete"
    || ((mode === "submit" || mode === "retry") && durationBlocked);
  uploadButton.textContent = mode === "cancel" ? "Отменить загрузку"
    : mode === "preparing" ? "Подготавливаем загрузку…"
    : mode === "complete" ? "Отправлено на проверку"
    : mode === "retry" ? "Повторить отправку" : "Отправить на проверку";
}
function uploadProgressVisible(visible: boolean): void {
  if (uploadTransferSlot) uploadTransferSlot.hidden = !visible;
  if (uploadProgress) uploadProgress.hidden = !visible;
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
  uploadAction("submit");
  if (uploadButton) uploadButton.disabled = true;
  uploadProgressVisible(false);
  if (uploadProgress) uploadProgress.value = 0;
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
  if (code === "upload_busy") return "Другая песня уже загружается. Дождитесь завершения предыдущей отправки.";
  if (["upload_staging_unavailable","upload_background_unavailable","upload_staging_expired"].includes(code)) return "Не удалось подготовить фоновую загрузку. Закройте окно и попробуйте ещё раз.";
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
  if (incidentStatus.active() || !uploadPanel || opening) return;
  // Close immediately, regardless of success/error/upload state. No network
  // request, validation reset, or async completion is allowed to reopen it.
  if (!uploadPanel.hidden) {
    uploadManuallyCollapsed = true;
    uploadPanel.hidden = true;
    addTrackButton.setAttribute("aria-expanded", "false");
    return;
  }
  uploadManuallyCollapsed = false;
  // Reopen the same operation without resetting its request ID/file.
  // A user may collapse the panel while the hidden offscreen POST runs.
  if (uploading || backgroundUploadMode) {
    uploadPanel.hidden = false;
    addTrackButton.setAttribute("aria-expanded", "true");
    await syncBackgroundUpload();
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
    uploadProgressVisible(false);
    if (uploadProgress) uploadProgress.value = 0;
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

uploadButton?.addEventListener("click", (event) => {
  if (uploadButton?.dataset.uploadMode !== "cancel") return;
  event.preventDefault();
  if (!uploading || (!activeUploadXHR && !backgroundUploadMode) || !uploadConfirm) return;
  uploadConfirm.hidden = false;
  uploadContinue?.focus();
});
uploadContinue?.addEventListener("click", () => {
  if (uploadConfirm) uploadConfirm.hidden = true;
  uploadButton?.focus();
});
uploadStop?.addEventListener("click", () => {
  if (!uploading || (!activeUploadXHR && !backgroundUploadMode)) return;
  if (uploadConfirm) uploadConfirm.hidden = true;
  manualUploadCancel = true;
  if (activeUploadXHR) activeUploadXHR.abort();
  else if (backgroundUploadMode && uploadRequestId) {
    void chrome.runtime.sendMessage({type:"CELIKOM_UPLOAD_CANCEL", id:uploadRequestId});
    uploadMessage("Отменяем загрузку…", "checking");
  }
});

uploadForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (uploading || opening || !pinnedTrack || uploadForm.hidden) return;
  if (!uploadFile?.files?.[0]) {
    uploadMessage("Выберите MP3 или M4A перед отправкой.", "error");
    // Keep the popup at its current scroll position.
    return;
  }
  if (!uploadRights?.checked) {
    uploadMessage("Подтвердите, что у вас есть необходимые права на аудиофайл.", "error");
    return;
  }

  const file = uploadFile.files[0];
  if (!validAudioSelection(file)) {
    uploadMessage("Выберите MP3 или M4A не более 30 МиБ.", "error"); return;
  }
  if (!uploadRequestId) uploadRequestId = crypto.randomUUID();
  const attemptId = uploadRequestId;
  void uploadJournal.record(attemptId, "checking", {trackId: pinnedTrack.id, bytes: file.size});
  uploading = true;
  manualUploadCancel = false;
  if(uploadFile)uploadFile.disabled=true;
  uploadAction("preparing");
  uploadMessage("Проверяем трек и отправляем файл…", "checking");

  let origin: string;
  let transferStarted = false;
  try {
    if(measuredFile!==file)await checkFileDuration();else if(durationPromise)await durationPromise;
    if(durationBlocked){
      void uploadJournal.record(attemptId, "rejected", {code: "invalid_or_mismatched_audio"});
      uploadMessage("");
      return;
    }
    const now = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (!now || now.id !== pinnedTrack.id) {
      void uploadJournal.record(attemptId, "rejected", {code: "track_changed"});
      uploadMessage("Трек изменился. Закройте и откройте «Загрузить версию» заново.", "error");
      return;
    }
    origin = await uploadApiOrigin();
    const existing = await trackUploadStatus(origin, pinnedTrack.id);
    const checkedTarget = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (checkedTarget?.id !== pinnedTrack.id) throw new Error("track_changed");
    if (existing !== "none") {
      void uploadJournal.record(attemptId, "duplicate", {code: existing});
      showSubmitted(existing === "pending" ? "Трек уже добавлен" : "Версия уже доступна",
        "Заявка уже есть в CELIKOM. Повторно отправлять файл не нужно.");
      return;
    }

    // Chrome MV3 action popups are destroyed when focus changes. Stage the
    // Blob in extension-private IndexedDB, then delegate POST to an offscreen
    // document so blur/close never cancels an already accepted upload.
    if (chrome.runtime.getManifest?.().permissions?.includes("offscreen")) {
      const access = await contributionAccess();
      const finalTarget = uploadTargetFromStatus(await send<ExtensionState>({type:COMMANDS.getStatus}));
      if (finalTarget?.id !== pinnedTrack.id) throw new Error("track_changed");
      uploadMessage("Подготавливаем файл для фоновой загрузки…", "checking");
      await stageUploadFile(attemptId, file);
      let response;
      try {
        response = await chrome.runtime.sendMessage({
          type:"CELIKOM_UPLOAD_BEGIN",
          task:{
            id:attemptId, trackId:pinnedTrack.id, durationMs:pinnedTrack.durationMs,
            artist:pinnedTrack.artist, title:pinnedTrack.title, album:pinnedTrack.album,
            filename:file.name, origin, token:access
          }
        });
      } catch (error) {
        await deleteStagedUpload(attemptId).catch(()=>{});
        throw error;
      }
      if (!response?.ok) {
        await deleteStagedUpload(attemptId).catch(()=>{});
        throw new Error(response?.error || "upload_background_unavailable");
      }
      backgroundUploadMode = true;
      transferStarted = true;
      uploadAction("cancel");
      uploadProgressVisible(true);
      if (uploadProgress) uploadProgress.value = 0;
      uploadMessage("Загрузка продолжается в фоне. Можно закрыть окно CELIKOM.", "checking");
      void syncBackgroundUpload();
      return;
    }

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
    xhr.setRequestHeader("X-Celikom-Upload-Attempt", attemptId);
    const finalTarget = uploadTargetFromStatus(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    if (finalTarget?.id !== pinnedTrack.id) throw new Error("track_changed");
    let failure = "";
    let lastActivityAt = Date.now();
    let bytesMoved = false, waitNotice = false, lastPercent = -1;
    const watchdog = setInterval(() => {
      if (!uploading || bytesMoved) return;
      const idle = Date.now() - lastActivityAt;
      if (idle > 15000 && !waitNotice) {
        waitNotice = true;
        uploadMessage("Ожидаем начала передачи. Проверяем соединение…", "checking");
        void uploadJournal.record(attemptId, "waiting");
      }
      if (idle > 45000) { failure = "stalled"; xhr.abort(); }
    }, 3000);
    watchdog?.unref?.();
    xhr.upload.addEventListener("progress", (progress) => {
      lastActivityAt = Date.now();
      bytesMoved ||= progress.loaded > 0;
      const percent = progress.lengthComputable && progress.total > 0
        ? Math.floor(progress.loaded / progress.total * 100) : 0;
      if (uploadProgress && progress.lengthComputable) uploadProgress.value = percent;
      if (Math.floor(percent / 10) !== Math.floor(lastPercent / 10)) {
        lastPercent = percent;
        void uploadJournal.record(attemptId, "transferring", {sent: progress.loaded, percent});
      }
    });
    xhr.upload.addEventListener("load", () => {
      bytesMoved = true;
      void uploadJournal.record(attemptId, "server_wait");
      uploadMessage("Файл отправлен. Ждём подтверждения сервера…", "checking");
    });
    xhr.addEventListener("error", () => { failure = "network_error"; });
    xhr.addEventListener("timeout", () => { failure = "timeout"; });
    xhr.addEventListener("abort", () => { failure ||= "interrupted"; });
    uploadProgressVisible(true);
    if (uploadProgress) uploadProgress.value = 0;
    uploadMessage("Подключаемся и загружаем аудиофайл…", "checking");
    void uploadJournal.record(attemptId, "connecting");
    xhr.addEventListener("loadend", () => {
      clearInterval(watchdog);
      activeUploadXHR = null;
      uploadProgressVisible(false);
      if (uploadConfirm) uploadConfirm.hidden = true;
      uploading = false;
      if(uploadFile)uploadFile.disabled=false;
      if (xhr.status === 202) {
        try {
          const result = JSON.parse(xhr.responseText);
          if (result.status === "pending" && Number.isSafeInteger(result.replacement_id)) {
            void uploadJournal.record(attemptId, "completed", {httpStatus: 202});
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
        void uploadJournal.record(attemptId, "duplicate", {code, httpStatus: xhr.status});
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
      void uploadJournal.record(attemptId, "failed", {httpStatus: xhr.status, code: failure || code || "http_error"});
      const guidance = manualUploadCancel ? "Загрузка отменена по вашему запросу."
        : failure === "stalled" ? "Передача не началась за 45 секунд. Проверьте интернет или VPN."
        : failure === "timeout" ? "Сервер не ответил за две минуты. Проверьте статус песни."
        : xhr.status === 0 ? "Соединение прервалось. Проверьте сеть или VPN."
        : xhr.status >= 500 ? "Сервер временно недоступен. Повторите позже."
        : errors[code] || "Загрузка не завершена. Попробуйте ещё раз.";
      uploadMessage(guidance + " Код: " + attemptId.slice(0, 8).toUpperCase(), "error");
      uploadAction("retry");
    });
    activeUploadXHR = xhr;
    uploadAction("cancel");
    try { xhr.send(data); } catch (error) {
      clearInterval(watchdog);
      activeUploadXHR = null;
      uploadProgressVisible(false);
      throw error;
    }
    transferStarted = true;
  } catch (error) {
    void uploadJournal.record(attemptId, "failed", {
      code: (error as Error)?.message === "track_changed" ? "track_changed" : "preflight_failed"
    });
    uploadMessage(contributionError(error) + " Код: " + attemptId.slice(0, 8).toUpperCase(), "error");
  } finally {
    // The request completion handler is responsible for re-enabling the button
    // after xhr.send(). An early exit must never leave the UI stuck.
    if (!transferStarted) {
      activeUploadXHR = null;
      uploadProgressVisible(false);
      if (uploadConfirm) uploadConfirm.hidden = true;
      uploading = false;
      if(uploadFile)uploadFile.disabled=false;
      if (uploadButton && uploadForm && !uploadForm.hidden) {
        uploadAction("submit");
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
  await navigator.clipboard.writeText(JSON.stringify({
    ...lastState,
    uploadAttempts: await uploadJournal.snapshot()
  }, null, 2));
  if (diagnosticsButton) diagnosticsButton.textContent = "Скопировано";
});

// Reopened popup reconstructs progress from the offscreen uploader's small,
// sanitized status record. No original File or credentials leave IndexedDB.
async function syncBackgroundUpload(): Promise<void> {
  if (!chrome.storage?.local) return;
  let saved;
  try { saved = (await chrome.storage.local.get(BACKGROUND_UPLOAD_KEY))?.[BACKGROUND_UPLOAD_KEY]; }
  catch { return; }
  if (!saved || typeof saved.id !== "string" || Date.now()-saved.at > 600000) return;
  const target = uploadTargetFromStatus(lastState);
  if (!target || target.id !== saved.trackId) return;
  const active = ["connecting","waiting","transferring","server_wait"].includes(saved.phase);
  if (!active && !["completed","duplicate","failed","cancelled"].includes(saved.phase)) return;
  // Do not overwrite an unrelated newly selected file with an older result.
  if (!active && !backgroundUploadMode && uploadFile?.files?.length) return;
  // Neither a completed upload nor a periodic poll can reopen a panel the
  // user closed. A completed attempt in a fresh popup is shown on demand by
  // the server status check when "Загрузить версию" is clicked.
  if (uploadManuallyCollapsed || (uploadPanel?.hidden && !active && !backgroundUploadMode)) return;
  pinnedTrack = target;
  uploadRequestId = saved.id;
  backgroundUploadMode = active;
  uploading = active;
  if(uploadPanel) uploadPanel.hidden = false;
  if(addTrackButton) addTrackButton.setAttribute("aria-expanded","true");
  if(uploadTrack) uploadTrack.value = target.id;
  uploadProgressVisible(active);
  if(uploadProgress) uploadProgress.value = Number.isInteger(saved.percent) ? saved.percent : 0;
  if(uploadConfirm && !active) uploadConfirm.hidden = true;
  if(uploadFile) uploadFile.disabled = active;
  // Never collapse the form during the transfer or when it finishes:
  // the small Chrome popup must keep its layout and scroll position.
  if(uploadResult) uploadResult.hidden = true;
  if(uploadForm) uploadForm.hidden = false;
  uploadAction(active ? "cancel" :
    ["completed","duplicate"].includes(saved.phase) ? "complete" :
    ["failed","cancelled"].includes(saved.phase) ? "retry" : "submit");
  if(saved.phase==="completed" || saved.phase==="duplicate") {
    uploadMessage(saved.phase==="completed"?"Аудиофайл получен CELIKOM. Версия отправлена на модерацию."
      :"Версия уже есть на сервере. Повторная отправка не нужна.","success");
    return;
  }
  const descriptions = {
    connecting:"Подключаемся к серверу. Загрузка продолжается в фоне.",
    waiting:"Ожидаем начала передачи. Проверяем соединение…",
    transferring:"Загружаем аудиофайл: "+(saved.percent||0)+"%. Можно закрыть окно CELIKOM.",
    server_wait:"Файл передан. Ждём подтверждения сервера…",
    cancelled:"Загрузка отменена по вашему запросу.",
    failed: saved.code==="stalled"?"Соединение зависло. Проверьте интернет или VPN."
      : saved.code==="timeout"?"Сервер не ответил за две минуты. Проверьте статус трека."
      : saved.code==="invalid_mp3"?"Файл не прошёл проверку MP3."
      : "Загрузка не завершена. Попробуйте ещё раз."
  };
  uploadMessage((descriptions[saved.phase] || "Проверяем загрузку…") +
    (["failed","cancelled"].includes(saved.phase)?" Код: "+saved.id.slice(0,8).toUpperCase():""),
    ["failed","cancelled"].includes(saved.phase)?"error":"checking");
}
let refreshing = false;
async function refresh(): Promise<void> {
  if (refreshing) return;
  refreshing = true;
  try {
    render(await send<ExtensionState>({ type: COMMANDS.getStatus }));
    await syncBackgroundUpload();
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
