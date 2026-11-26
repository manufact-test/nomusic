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
  let reloadPending = false;
  async function reloadMismatchedPlayer(expected) {
    if (reloadPending) return {ok:false,error:"reload_pending"};
    if (!/^[1-9]\d{0,23}$/.test(expected?.trackId) || !Number.isFinite(expected?.since))
      return {ok:false,error:"invalid_recovery"};
    reloadPending = true;
    try {
      const target = await connection();
      const mismatch = target.status?.track?.playbackMismatch;
      if (target.error || !mismatch || mismatch.trackId !== expected.trackId || mismatch.since !== expected.since)
        return {ok:false,error:"player_changed"};
      // The popup supplies no URL or tab ID. Revalidate the selected tab after
      // all asynchronous controller discovery, so a navigated page is untouched.
      const tab = await api.tabs.get(target.tabId);
      if (!isSupportedPage(tab.url)) return {ok:false,error:"player_changed"};
      await api.tabs.reload(target.tabId);
      return {ok:true};
    } catch (_) { return {ok:false,error:"reload_failed"}; }
    finally { reloadPending = false; }
  }
  return { connection, send, reloadMismatchedPlayer };
}
