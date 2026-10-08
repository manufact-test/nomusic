import { COMMANDS, normalizeEnabled, type ExtensionState } from "../shared/messages.js";
import { createControllerBootstrap } from "./controller-bootstrap.js";

const VERSION = chrome.runtime.getManifest().version;
const DEFAULT_STATE: ExtensionState = Object.freeze({
  enabled: false,
  phase: "STOPPED",
  version: VERSION
});
const bootstrap = createControllerBootstrap(chrome);

async function readEnabled(): Promise<boolean> {
  const stored = await chrome.storage.local.get("enabled");
  return normalizeEnabled(stored.enabled);
}

async function activeTabId(): Promise<number | null> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab?.id ?? null;
}

async function readControllerStatus(retry = false) {
  const tabId = await activeTabId();
  if (tabId === null) return { status: null, error: "no-active-tab", detail: "Откройте вкладку Яндекс Музыки." };
  return bootstrap.ensure(tabId, retry);
}

async function readState(retry = false): Promise<ExtensionState> {
  const enabled = await readEnabled();
  const connection = await readControllerStatus(retry);
  const controller = connection.status;
  return {
    ...DEFAULT_STATE,
    ...controller,
    enabled,
    phase: enabled ? connection.error ? "ERROR" : controller?.phase || "CONNECTING" : "STOPPED",
    version: VERSION,
    connection: {
      controllerPresent: Boolean(controller),
      recovered: connection.recovered || false,
      error: connection.error || null,
      detail: connection.detail || null
    },
    bridge: controller?.bridge || { ready: false, healthy: false },
    track: controller?.track || null
  };
}

async function sendToActiveTab(message: object): Promise<unknown> {
  const tabId = await activeTabId();
  if (!tabId) return null;
  return chrome.tabs.sendMessage(tabId, message).catch(() => null);
}

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get("enabled");
  if (typeof stored.enabled !== "boolean") await chrome.storage.local.set({ enabled: DEFAULT_STATE.enabled });
  await bootstrap.ensureOpenTabs();
});

chrome.runtime.onStartup.addListener(() => {
  void bootstrap.ensureOpenTabs().catch(() => undefined);
});

chrome.runtime.onMessage.addListener((message: unknown, _sender, sendResponse) => {
  const type = typeof message === "object" && message !== null && "type" in message
    ? (message as { type?: unknown }).type
    : null;

  if (type === COMMANDS.getStatus) {
    void readState().then(sendResponse);
    return true;
  }
  if (type === COMMANDS.setEnabled) {
    const enabled = normalizeEnabled((message as { enabled?: unknown }).enabled);
    void chrome.storage.local.set({ enabled }).then(async () => {
      if (enabled) await sendToActiveTab({ type: COMMANDS.retryReplacement });
      sendResponse(await readState(enabled));
    });
    return true;
  }
  if (type === COMMANDS.setTestTrack) {
    const raw = String((message as { trackId?: unknown }).trackId || "").trim();
    if (raw && !/^\d{1,24}$/.test(raw)) { sendResponse({ ok: false, error: "invalid-track-id" }); return false; }
    void chrome.storage.local.set({ testTrackId: raw }).then(async () => sendResponse(await readState()));
    return true;
  }
  if (type === COMMANDS.restoreOriginal) {
    void sendToActiveTab({ type: COMMANDS.restoreOriginal }).then((result) => sendResponse(result || { ok: true }));
    return true;
  }
  return false;
});
