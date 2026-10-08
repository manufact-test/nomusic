import { COMMANDS, type ExtensionState } from "../shared/messages.js";

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

document.querySelector("[data-action='add']")?.addEventListener("click", () => {
  const note = document.querySelector<HTMLElement>("[data-coming-soon]");
  if (note) note.hidden = !note.hidden;
  if (note && !note.hidden) void send({ type: "CELIKOM_ADD_TRACK_OPENED" });
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
  const response = await send<{ ok: boolean }>({ type: "CELIKOM_SET_API_ACCESS", token: input.value });
  input.value = "";
  note.textContent = response?.ok ? "Код сохранён" : "Проверьте код доступа";
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
