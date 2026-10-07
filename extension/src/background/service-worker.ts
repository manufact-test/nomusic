import { COMMANDS, normalizeEnabled, type ExtensionState } from "../shared/messages.js";

const VERSION = chrome.runtime.getManifest().version;
const DEFAULT_STATE: ExtensionState = Object.freeze({
  enabled: false,
  phase: "STOPPED",
  version: VERSION
});

async function readState(): Promise<ExtensionState> {
  const stored = await chrome.storage.local.get("enabled");
  const enabled = normalizeEnabled(stored.enabled);
  return {
    enabled,
    phase: enabled ? "IDLE" : "STOPPED",
    version: VERSION
  };
}

async function restoreOriginalInActiveTab(): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  await chrome.tabs.sendMessage(tab.id, { type: COMMANDS.restoreOriginal }).catch(() => undefined);
}

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await chrome.storage.local.get("enabled");
  if (typeof stored.enabled !== "boolean") {
    await chrome.storage.local.set({ enabled: DEFAULT_STATE.enabled });
  }
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
      if (!enabled) await restoreOriginalInActiveTab();
      sendResponse(await readState());
    });
    return true;
  }

  if (type === COMMANDS.restoreOriginal) {
    void restoreOriginalInActiveTab().then(() => sendResponse({ ok: true }));
    return true;
  }

  return false;
});
