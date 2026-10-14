import { isSupportedPage } from "./controller-bootstrap.js";

// Tab events wake MV3 without a permanent worker, focus changes or new permissions.
export function registerTabRecovery(api, bootstrap, readEnabled) {
  async function recover(tabId) {
    if (!Number.isInteger(tabId) || !await readEnabled()) return;
    const tab = await api.tabs.get(tabId);
    if (!isSupportedPage(tab.url) || tab.discarded || tab.status === "loading") return;
    // Bootstrap only restores the receiver. The controller reads persisted intent
    // and the existing heartbeat/API channel verifies access before replacement.
    if (await readEnabled()) await bootstrap.ensure(tabId);
  }
  const attempt = (tabId) => { void recover(tabId).catch(() => undefined); };
  api.tabs.onUpdated?.addListener((tabId, change, tab) => {
    if (change.status === "loading" || change.url || change.discarded === true) bootstrap.forget(tabId);
    if (change.status === "complete" || change.discarded === false) attempt(tabId);
  });
  api.tabs.onCreated?.addListener(tab => { if (isSupportedPage(tab.url)) attempt(tab.id); });
  api.tabs.onActivated?.addListener(info => attempt(info.tabId));
  api.tabs.onReplaced?.addListener((added, removed) => { bootstrap.forget(removed); attempt(added); });
  api.tabs.onRemoved?.addListener(tabId => bootstrap.forget(tabId));
}
