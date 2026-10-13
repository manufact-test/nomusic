import { readDisplay, writeDisplay, clearDisplay, stableText } from "./display-cache.js";
const labels = {
  none: "Версия песни CELIKOM ещё не загружена",
  pending: "Версия песни CELIKOM на проверке",
  approved: "Версия песни CELIKOM доступна для подмены"
};
export function initVersionStatus(send) {
  const node = document.querySelector("[data-version-status]");
  let cached = readDisplay("version");
  if (!/^[1-9]\d{0,23}$/.test(cached?.trackId || "") || !labels[cached?.status]) cached = null;
  const rememberedTrack = readDisplay("track");
  const noTrack = rememberedTrack?.id === null;
  if (noTrack) cached = null;
  if (rememberedTrack?.id && rememberedTrack.id !== cached?.trackId) cached = null;
  let trackId = cached?.trackId || "", checkedAt = 0, request = 0, loading = false;
  if (node) node.hidden = noTrack;
  stableText(node, noTrack ? "" : cached ? labels[cached.status] : "Загрузка версии песни…", false);
  const remember = (id, status) => { cached = { trackId: id, status }; writeDisplay("version", cached); stableText(node, labels[status]); };
  document.addEventListener?.("celikom-account-logout", () => {
    request++; loading = false; checkedAt = 0; cached = null; clearDisplay("version");
    stableText(node, "Войдите, чтобы проверить версию песни CELIKOM");
  });
  let latestState = null;
  document.addEventListener?.("celikom-account-login", () => {
    request++; loading = false; checkedAt = 0;
    if (latestState) void refreshVersion(latestState);
  });
  async function refreshVersion(state) {
    latestState = state;
    if (!node) return;
    const id = state.track?.id || "";
    if (id !== trackId) {
      trackId = id; checkedAt = 0; loading = false; request++;
      stableText(node, id ? cached?.trackId === id ? labels[cached.status] : "Загрузка версии песни…" : "");
    }
    node.hidden = !id;
    if (!id) { cached = null; clearDisplay("version"); stableText(node, ""); return; }
    if (state.phase === "REPLACEMENT_ACTIVE") {
      request++; loading = false; checkedAt = Date.now(); remember(id, "approved");
      stableText(node, state.player?.paused === true ? "Версия CELIKOM на паузе" : "Играет версия CELIKOM"); return;
    }
    if (cached?.trackId === id) stableText(node, labels[cached.status]);
    if (loading || (checkedAt && Date.now() - checkedAt < 15000)) return;
    const current = ++request; loading = true;
    try {
      const result = await send({ type: "CELIKOM_AUTH", action: "track-status", track_id: id });
      if (current !== request || trackId !== id) return;
      if (result?.ok && labels[result.status]) remember(id, result.status);
      else if (result?.error === "invalid_session") {
        cached = null; clearDisplay("version"); stableText(node, "Войдите, чтобы проверить версию песни CELIKOM");
      } else if (cached?.trackId !== id) stableText(node, "Не удалось проверить версию песни CELIKOM");
    } catch (_) {
      if (current === request && cached?.trackId !== id) stableText(node, "Не удалось проверить версию песни CELIKOM");
    } finally {
      if (current === request) { loading = false; checkedAt = Date.now(); }
    }
  }
  return refreshVersion;
}
