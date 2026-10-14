import { COMMANDS, normalizeEnabled, type ExtensionState } from "../shared/messages.js";
import { createControllerBootstrap } from "./controller-bootstrap.js";
import { createApiBroker } from "../api/api-broker.js";
import { createAuthBroker } from "../auth/auth-broker.js";
import { createActionIcon } from "./action-icon.js";
import { createMusicTabs } from "./music-tabs.js";
import { registerTabRecovery } from "./tab-recovery.js";

const VERSION = chrome.runtime.getManifest().version;
const DEFAULT_STATE: ExtensionState = Object.freeze({
  enabled: false,
  phase: "STOPPED",
  version: VERSION
});
const bootstrap = createControllerBootstrap(chrome);
const musicTabs = createMusicTabs(chrome, bootstrap);
const userAuth = createAuthBroker(chrome);
const actionIcon = createActionIcon(chrome);
const resolveApi = createApiBroker(chrome, { withAccess: userAuth.withEntitledAccess });
let intentGeneration = 0;
let accessCheck: Promise<string> | null = null;
let accessValidUntil = 0;
let accessRetryAt = 0;
let accessEpoch = 0;
async function playbackAccess(): Promise<string> {
  if (accessValidUntil > Date.now()) return "allowed";
  if (accessRetryAt > Date.now()) return "unavailable";
  const generation = intentGeneration;
  const epoch = accessEpoch;
  if (!accessCheck) {
    const pending = userAuth.entitlement().then((result) => {
    if (generation !== intentGeneration || epoch !== accessEpoch) return "unavailable";
    if (!result.allowed) return result.reason === "service_incident" ? "incident" : "denied";
    accessValidUntil = result.source === "promo" && result.valid_until === null ? Date.now() + 10000 : Math.min(Date.now() + 10000, Date.parse(result.valid_until));
    return accessValidUntil > Date.now() ? "allowed" : "denied";
  }).catch((error) => {
    if (generation !== intentGeneration || epoch !== accessEpoch) return "unavailable";
    if (["invalid_session", "account_disabled", "email_unverified", "access_denied"].includes(error?.message)) return "denied";
    accessRetryAt = Date.now() + 5000; return "unavailable";
  }).finally(() => { if (accessCheck === pending) accessCheck = null; });
    accessCheck = pending;
  }
  return accessCheck;
}

function resetConnectivity() {
  actionIcon.clear();
  accessEpoch++; accessValidUntil = 0; accessRetryAt = 0; accessCheck = null;
  userAuth.resetTransport?.(); resolveApi.resetTransport?.();
  const epoch = accessEpoch;
  void (async () => {
    if (!await readEnabled() || epoch !== accessEpoch) return;
    await musicTabs.send({ type: "CELIKOM_ACCESS_STATE", state: "unavailable" }).catch(() => undefined);
    const access = await playbackAccess();
    if (epoch !== accessEpoch || !await readEnabled()) return;
    if (access === "denied") { actionIcon.clear(); await chrome.storage.local.set({ enabled: false }); return; }
    await musicTabs.send({ type: "CELIKOM_ACCESS_STATE", state: access }).catch(() => undefined);
  })().catch(() => undefined);
}
// Connectivity events are hints to revalidate, never permission to play offline.
if (typeof globalThis.addEventListener === "function") {
  globalThis.addEventListener("online", resetConnectivity);
  globalThis.addEventListener("offline", resetConnectivity);
}

async function readEnabled(): Promise<boolean> {
  const stored = await chrome.storage.local.get("enabled");
  return normalizeEnabled(stored.enabled);
}

registerTabRecovery(chrome, bootstrap, readEnabled);

async function readControllerStatus(retry = false) {
  return musicTabs.connection(retry);
}

async function readState(retry = false): Promise<ExtensionState> {
  const enabled = await readEnabled();
  const connection = await readControllerStatus(retry);
  const controller = connection.status;
  const state: ExtensionState = {
    ...DEFAULT_STATE,
    ...controller,
    enabled,
    phase: enabled ? connection.error ? "ERROR" : controller?.phase || "CONNECTING" : "STOPPED",
    version: VERSION,
    network: userAuth.networkDiagnostics?.() || [],
    connection: {
      controllerPresent: Boolean(controller),
      recovered: connection.recovered || false,
      error: connection.error || null,
      detail: connection.detail || null
    },
    bridge: controller?.bridge || { ready: false, healthy: false },
    track: controller?.track || null
  };
  actionIcon.showFor(connection.tabId,enabled && !connection.error && state.bridge?.healthy===true && !state.startupError && !state.replacementError && !state.suspended && !["ERROR","CONNECTING","PREPARING","RESTORING"].includes(state.phase));
  return state;
}

async function sendToActiveTab(message: object): Promise<unknown> {
  return musicTabs.send(message);
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

  // Only the extension-owned popup may inspect or change user intent.
  // Content scripts have a separate, narrowly scoped heartbeat/API channel.
  const popupCommand = [COMMANDS.getStatus, COMMANDS.setEnabled, COMMANDS.setTestTrack,
    COMMANDS.restoreOriginal, "CELIKOM_ADD_TRACK_OPENED", "CELIKOM_AUTH"].includes(type as string);
  if (popupCommand && (sender?.id !== chrome.runtime.id
    || sender?.url !== chrome.runtime.getURL("popup/popup.html"))) {
    sendResponse({ ok: false, error: "invalid_sender" }); return false;
  }

  if (type === "CELIKOM_AUTH") {
    if (sender?.id !== chrome.runtime.id || sender?.url !== chrome.runtime.getURL("popup/popup.html")) {
      sendResponse({ ok: false, error: "invalid_sender" }); return false;
    }
    const m = message as { action?: unknown };
    if (typeof m.action !== "string") { sendResponse({ ok: false, error: "invalid_request" }); return false; }
    if (m.action === "logout" || m.action === "login" || m.action === "verify-email") {
      intentGeneration++;
      actionIcon.clear();
      accessValidUntil = 0;
      accessRetryAt = 0;
      void chrome.storage.local.set({ enabled: false });
    }
    if (m.action === "promo-redeem") { accessValidUntil = 0; accessRetryAt = 0; }
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
    // Worker liveness must not wait for network authorization. MAIN's safety
    // lease continues only while this installed worker answers; denial still
    // asynchronously disables the controller and restores original playback.
    sendResponse({ ok: true, version: VERSION });
    const pulse = message as { enabled?: unknown; healthy?: unknown; phase?: unknown; replacementError?: unknown; suspended?: unknown; startupError?: unknown };
    const connected=pulse.enabled === true && pulse.healthy === true && pulse.replacementError !== true && pulse.suspended !== true && !pulse.startupError && !["ERROR","CONNECTING","PREPARING","RESTORING"].includes(String(pulse.phase));
    // An unhealthy page must turn gray immediately, even while auth is pending.
    if(!connected)actionIcon.update(sender.tab?.id,false);
    void (async () => {
      if (!await readEnabled()) { actionIcon.clear(); return; }
      const epoch = accessEpoch;
      const access = await playbackAccess();
      if (epoch !== accessEpoch || !await readEnabled()) return;
      if (access === "denied") { actionIcon.clear(); await chrome.storage.local.set({ enabled: false }); return; }
      await chrome.tabs.sendMessage(sender.tab?.id, { type: "CELIKOM_ACCESS_STATE", state: access }).catch(() => undefined);
      if (access !== "allowed") { actionIcon.update(sender.tab?.id, false); return; }
      actionIcon.update(sender.tab?.id, connected);
    })().catch(() => actionIcon.update(sender.tab?.id, false));
    return false;
  }

  if (type === "CELIKOM_API_RESOLVE" || type === "CELIKOM_API_EVENT") {
    void resolveApi(message, sender).then(sendResponse).catch(() => sendResponse({ ok: false, error: "api_unavailable" }));
    return true;
  }

  if (type === COMMANDS.getStatus) {
    void readState().then(sendResponse);
    return true;
  }
  if (type === COMMANDS.setEnabled) {
    const enabled = normalizeEnabled((message as { enabled?: unknown }).enabled);
    const generation = ++intentGeneration;
    void (async () => {
      accessValidUntil = 0;
      accessRetryAt = 0;
      if (enabled) {
        const preview = await userAuth.perform("account-preview", {});
        if (preview.localSession === false) {
          sendResponse({ ...DEFAULT_STATE, accessError: "sign_in_required" }); return;
        }
        const connection = await readControllerStatus(true);
        if (!connection.status?.track?.id || !connection.status?.player) {
          sendResponse({ ...await readState(), accessError: "track_required" }); return;
        }
        try {
          const result = await userAuth.entitlement(true);
          if (!result.allowed && result.reason !== "service_incident") { sendResponse({ ...await readState(), accessError: result.reason }); return; }
          if (result.reason === "service_incident") await musicTabs.send({ type: "CELIKOM_ACCESS_STATE", state: "incident" });
        } catch (error) { sendResponse({ ...await readState(), accessError: (error as Error)?.message === "invalid_session" ? "sign_in_required" : "auth_unavailable" }); return; }
      }
      // A delayed Start must never undo a later Stop/login/logout.
      if (generation !== intentGeneration) { sendResponse(await readState()); return; }
      await chrome.storage.local.set({ enabled });
      if (!enabled) actionIcon.clear();
      if (enabled) await sendToActiveTab({ type: COMMANDS.retryReplacement });
      sendResponse(await readState(enabled));
    })().catch(() => sendResponse({ ...DEFAULT_STATE, accessError: "auth_unavailable" }));
    return true;
  }
  if (type === COMMANDS.setTestTrack) {
    const raw = String((message as { trackId?: unknown }).trackId || "").trim();
    if (raw && !/^\d{1,24}$/.test(raw)) { sendResponse({ ok: false, error: "invalid-track-id" }); return false; }
    void chrome.storage.local.set({ testTrackId: raw }).then(async () => sendResponse(await readState()));
    return true;
  }
  if (type === COMMANDS.restoreOriginal) {
    // Preserve the latest explicit bypass even if an earlier Start is awaiting access.
    intentGeneration++;
    void sendToActiveTab({ type: COMMANDS.restoreOriginal }).then((result) => sendResponse(result || { ok: true }));
    return true;
  }
  if (type === "CELIKOM_ADD_TRACK_OPENED") { void sendToActiveTab({ type }).then(sendResponse); return true; }
  return false;
});
