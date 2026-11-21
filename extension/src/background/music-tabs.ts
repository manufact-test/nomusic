import { isSupportedPage } from "./controller-bootstrap.js";

// One target for status and commands. Reading the popup never changes focus.
export function createMusicTabs(api, bootstrap) {
  let selected = null;
  async function connection(retry = false) {
    const active = (await api.tabs.query({ active: true, currentWindow: true }))[0];
    const music = await api.tabs.query({ url: "https://music.yandex.ru/*" });
    const candidates = music.filter((t) => Number.isInteger(t.id) && isSupportedPage(t.url));
    candidates.sort((a, b) => Number(b.id === active?.id) - Number(a.id === active?.id)
      || Number(b.id === selected) - Number(a.id === selected) || a.id - b.id);
    let fallback = null;
    for (const tab of candidates) {
      const result = { ...await bootstrap.ensure(tab.id, retry), tabId: tab.id };
      fallback ||= result;
      if (!result.error && result.status?.bridge?.healthy) {
        // Prefer active playback when the popup was opened on another website.
        if (tab.id === active?.id || (result.status?.player && !result.status.player.paused)) {
          selected = tab.id; return result;
        }
        if (!fallback.status?.bridge?.healthy) fallback = result;
      }
    }
    if (fallback) { selected = fallback.tabId; return fallback; }
    selected = null;
    return { status: null, tabId: null, error: "no-music-tab", detail: "Откройте вкладку Яндекс Музыки (music.yandex.ru)." };
  }
  async function send(message) {
    const target = await connection();
    if (target.tabId === null) return null;
    return api.tabs.sendMessage(target.tabId, message).catch(() => null);
  }
  return { connection, send };
}
