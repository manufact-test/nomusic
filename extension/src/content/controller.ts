const RESTORE_COMMAND = "CELIKOM_RESTORE_ORIGINAL";
const RESTORE_EVENT = "CELIKOM_RESTORE_ORIGINAL_REQUESTED";

chrome.runtime.onMessage.addListener((message: unknown, _sender, sendResponse) => {
  if (typeof message !== "object" || message === null || !("type" in message)) return false;
  if ((message as { type?: unknown }).type !== RESTORE_COMMAND) return false;

  document.dispatchEvent(new CustomEvent(RESTORE_EVENT, {
    detail: { reason: "extension-control" }
  }));
  sendResponse({ ok: true });
  return false;
});

if (document.documentElement) {
  document.documentElement.dataset.celikomController = "foundation";
}
