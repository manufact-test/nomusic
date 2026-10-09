import { COMMANDS, normalizeEnabled, type ExtensionState } from "../shared/messages.js";
import { createControllerBootstrap } from "./controller-bootstrap.js";
import { createApiBroker } from "../api/api-broker.js";
import { validateApiAccess } from "../api/api-access-validation.js";
import { createAuthBroker } from "../auth/auth-broker.js";

const VERSION = chrome.runtime.getManifest().version;
const DEFAULT_STATE: ExtensionState = Object.freeze({
  enabled: false,
  phase: "STOPPED",
  version: VERSION
});
const bootstrap = createControllerBootstrap(chrome);
const resolveApi = createApiBroker(chrome);
const userAuth = createAuthBroker(chrome);

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
  await userAuth.installationId();
  await bootstrap.ensureOpenTabs();
});

chrome.runtime.onStartup.addListener(() => {
  void bootstrap.ensureOpenTabs().catch(() => undefined);
});

chrome.runtime.onMessage.addListener((message: unknown, sender, sendResponse) => {
  const type = typeof message === "object" && message !== null && "type" in message
    ? (message as { type?: unknown }).type
    : null;

  if (type === "CELIKOM_AUTH") {
    if (sender?.id !== chrome.runtime.id || sender?.url !== chrome.runtime.getURL("popup/popup.html")) {
      sendResponse({ ok: false, error: "invalid_sender" }); return false;
    }
    const m = message as { action?: unknown };
    if (typeof m.action !== "string") { sendResponse({ ok: false, error: "invalid_request" }); return false; }
    void userAuth.perform(m.action, message as object).then(sendResponse)
      .catch(() => sendResponse({ ok: false, error: "auth_unavailable" }));
    return true;
  }

  if (type === "CELIKOM_CONTEXT_PING") {
    // Respond only to the extension's own content script on Yandex Music.
    // The actual installed worker, not an abandoned content script, is the
    // authority for whether MAIN can keep the original audio muted.
    let validOrigin = false;
    try { validOrigin = new URL(sender?.url || "").origin === "https://music.yandex.ru"; }
    catch (_error) { /* denied */ }
    if (sender?.id !== chrome.runtime.id || !validOrigin) {
      sendResponse({ ok: false }); return false;
    }
    sendResponse({ ok: true, version: VERSION });
    return false;
  }

  if (type === "CELIKOM_API_RESOLVE" || type === "CELIKOM_API_EVENT") {
    void resolveApi(message, sender).then(sendResponse).catch(() => sendResponse({ ok: false, error: "api_unavailable" }));
    return true;
  }
  if (type === "CELIKOM_SET_API_ACCESS" && sender?.id === chrome.runtime.id && sender?.url === chrome.runtime.getURL("popup/popup.html")) {
    const rawToken = (message as { token?: unknown }).token;
    void validateApiAccess(chrome, rawToken)
      .then(async (result) => {
        if (!result.ok) { sendResponse({ ok: false, error: result.error }); return; }
        await chrome.storage.local.set({ apiTestToken: result.token });
        await sendToActiveTab({ type: COMMANDS.retryReplacement });
        sendResponse({ ok: true });
      })
      .catch(() => sendResponse({ ok: false, error: "api_unavailable" }));
    return true;
  }

  if (type === COMMANDS.getStatus) {
    void readState().then(sendResponse);
    return true;
  }
  if (type === COMMANDS.setEnabled) {
    const enabled = normalizeEnabled((message as { enabled?: unknown }).enabled);
    void chrome.storage.local.set({ enabled }).then(async () => {
      if (enabled) await sendToActiveTab({ type: COMMANDS.retryReplacement });
      const state = await readState(enabled);
      if (enabled && (state.phase === "READY" || state.phase === "REPLACEMENT_ACTIVE")) {
        void userAuth.perform("activate").catch(() => undefined);
      }
      sendResponse(state);
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
  if (type === "CELIKOM_ADD_TRACK_OPENED") { void sendToActiveTab({ type }).then(sendResponse); return true; }
  return false;
});
