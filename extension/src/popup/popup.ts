import { COMMANDS, type ExtensionState } from "../shared/messages.js";

const status = document.querySelector<HTMLElement>("[data-status]");
const startButton = document.querySelector<HTMLButtonElement>("[data-action='start']");
const stopButton = document.querySelector<HTMLButtonElement>("[data-action='stop']");
const restoreButton = document.querySelector<HTMLButtonElement>("[data-action='restore']");

function render(state: ExtensionState): void {
  if (!status || !startButton || !stopButton) return;
  status.textContent = state.enabled ? "Готов к работе" : "Остановлен";
  status.dataset.active = String(state.enabled);
  startButton.disabled = state.enabled;
  stopButton.disabled = !state.enabled;
}

async function send<T>(message: object): Promise<T> {
  return chrome.runtime.sendMessage(message) as Promise<T>;
}

startButton?.addEventListener("click", async () => {
  render(await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: true }));
});

stopButton?.addEventListener("click", async () => {
  render(await send<ExtensionState>({ type: COMMANDS.setEnabled, enabled: false }));
});

restoreButton?.addEventListener("click", async () => {
  await send({ type: COMMANDS.restoreOriginal });
  if (status) status.textContent = "Оригинал восстановлен";
});

void send<ExtensionState>({ type: COMMANDS.getStatus }).then(render);
