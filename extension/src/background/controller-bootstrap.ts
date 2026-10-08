import { COMMANDS } from "../shared/messages.js";

export function isSupportedPage(rawUrl: unknown): boolean {
  try {
    const url = new URL(String(rawUrl || ""));
    return url.protocol === "https:" && url.hostname === "music.yandex.ru";
  } catch (_error) {
    return false;
  }
}

// All callers for one tab share one bootstrap. No remote code, extra hosts or
// navigation changes are needed: only manifest-declared packaged scripts run.
export function createControllerBootstrap(api, options = {}) {
  const pending = new Map();
  const injectionFailures = new Map();
  const wait = options.wait || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
  const attempts = options.attempts || 8;

  function staleController(status) {
    const manifest = api.runtime.getManifest();
    const replacementBuild = manifest.content_scripts?.some((group) => group.js?.includes("player/replacement-controller.js"));
    const oldStage = replacementBuild && typeof status?.stage === "number" && status.stage < 3;
    const oldCore = manifest.version && status?.buildVersion && manifest.version !== status.buildVersion;
    const oldMain = manifest.version && status?.bridge?.bridgeVersion && manifest.version !== status.bridge.bridgeVersion;
    if (!oldStage && !oldCore && !oldMain) return null;
    return { status, error: "stale-page-controller", detail: "Расширение обновлено, но вкладка использует прежний player controller. Обновите вкладку Яндекс Музыки один раз." };
  }

  async function readStatus(tabId) {
    try {
      const response = await api.tabs.sendMessage(tabId, { type: COMMANDS.getControllerStatus });
      if (response?.ok && response.status) return response.status;
    } catch (_error) {
      // Missing receiver is expected for a tab opened before install/reload.
    }
    return null;
  }

  async function bootstrap(tabId) {
    const tab = await api.tabs.get(tabId);
    if (!isSupportedPage(tab.url)) {
      return { status: null, error: "unsupported-page", detail: "Откройте вкладку Яндекс Музыки (music.yandex.ru)." };
    }
    const existing = await readStatus(tabId);
    if (existing?.bridge?.healthy) return staleController(existing) || { status: existing, error: null, recovered: false };

    const groups = api.runtime.getManifest().content_scripts;
    const main = groups?.find((group) => group.world === "MAIN");
    const isolated = groups?.find((group) => group.world === "ISOLATED");
    if (!main?.js?.length || !isolated?.js?.length) {
      return { status: existing, error: "invalid-bootstrap-manifest", detail: "В сборке отсутствуют файлы bridge/controller." };
    }

    // The MAIN listener must be present before the isolated client sends INIT.
    await api.scripting.executeScript({ target: { tabId }, files: main.js, world: "MAIN" });
    await api.scripting.executeScript({ target: { tabId }, files: isolated.js, world: "ISOLATED" });
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const status = await readStatus(tabId);
      if (status?.bridge?.healthy) return staleController(status) || { status, error: null, recovered: true };
      if (status?.startupError) return { status, error: "controller-start-failed", detail: status.startupError };
      await wait(75);
    }
    const status = await readStatus(tabId);
    return {
      status,
      error: status ? "bridge-connect-timeout" : "controller-start-timeout",
      detail: status
        ? "Content script запущен, но MAIN-world bridge не ответил. Обновите вкладку Яндекс Музыки."
        : "Chrome не запустил content script. Проверьте доступ расширения к music.yandex.ru и обновите вкладку."
    };
  }

  function ensure(tabId, retry = false) {
    if (pending.has(tabId)) return pending.get(tabId);
    if (retry) injectionFailures.delete(tabId);
    if (injectionFailures.has(tabId)) return Promise.resolve(injectionFailures.get(tabId));
    const promise = bootstrap(tabId)
      .catch((error) => {
        const failure = { status: null, error: "script-injection-failed", detail: String(error?.message || error) };
        // Do not repeatedly probe a denied/protected page from popup polling.
        // A user-initiated Start/Retry permits a fresh attempt after changing access.
        injectionFailures.set(tabId, failure);
        return failure;
      })
      .finally(() => pending.delete(tabId));
    pending.set(tabId, promise);
    return promise;
  }

  async function ensureOpenTabs() {
    const tabs = await api.tabs.query({ url: "https://music.yandex.ru/*" });
    return Promise.all(tabs.filter((tab) => Number.isInteger(tab.id)).map((tab) => ensure(tab.id)));
  }

  return Object.freeze({ ensure, ensureOpenTabs });
}
