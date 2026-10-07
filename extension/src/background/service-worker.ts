import { COMMANDS, normalizeEnabled, type ExtensionState } from "../shared/messages.js";

const VERSION = chrome.runtime.getManifest().version;
const DEFAULT_STATE: ExtensionState = Object.freeze({
  enabled: false,
  phase: "STOPPED",
  version: VERSION
});

async function readEnabled(): Promise<boolean> {
  const stored = await chrome.storage.local.get("enabled");
  return normalizeEnabled(stored.enabled);
}

async function activeTabId(): Promise<number | null> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab?.id ?? null;
}

async function readControllerStatus(): Promise<Partial<ExtensionState> | null> {
  const tabId = await activeTabId();
  if (!tabId) return null;
  const response = await chrome.tabs.sendMessage(tabId, { type: COMMANDS.getControllerStatus }).catch(() => null);
  return response?.ok && response.status ? response.status : null;
}

async function readState(): Promise<ExtensionState> {
  const enabled = await readEnabled();
  const controller = await readControllerStatus();
  return {
    ...DEFAULT_STATE,
    ...controller,
    enabled,
    phase: enabled ? controller?.phase || "CONNECTING" : "STOPPED",
    version: VERSION
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
      await sendToActiveTab({ type: COMMANDS.controllerPing });
      sendResponse(await readState());
    });
    return true;
  }
  if (type === COMMANDS.restoreOriginal) {
    void sendToActiveTab({ type: COMMANDS.restoreOriginal }).then((result) => sendResponse(result || { ok: true }));
    return true;
  }
  return false;
});
