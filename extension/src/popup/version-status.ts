import { withDeadline } from "../shared/request-deadline.js";
import { readDisplay, writeDisplay, clearDisplay, stableText } from "./display-cache.js";
const labels = {
  none: "Версия песни CELIKOM ещё не загружена",
  pending: "Версия песни CELIKOM на проверке",
  approved: "Версия песни CELIKOM доступна для подмены"
};
export function initVersionStatus(transport) {
  const send = message => withDeadline(() => transport(message));
  const node = document.querySelector("[data-version-status]");
  // The previous UI persisted "pending"/"approved" for 24 hours. A track
  // can be moderated or revoked meanwhile, so never present that cached
  // presence as a current fact. Only this popup's fresh server response or
  // the actual active playback state may authoritatively set a label.
  let cached = null;
  const rememberedTrack = readDisplay("track");
  const noTrack = rememberedTrack?.id === null;
  let trackId = cached?.trackId || "", checkedAt = 0, request = 0, loading = false;
  if (node) node.hidden = noTrack;
  stableText(node, noTrack ? "" : "Проверяем наличие версии CELIKOM…", false);
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
      cached = null;
      stableText(node, id ? "Проверяем наличие версии CELIKOM…" : "");
    }
    node.hidden = !id;
    if (!id) { cached = null; clearDisplay("version"); stableText(node, ""); return; }
    if (state.phase === "REPLACEMENT_ACTIVE") {
      request++; loading = false; checkedAt = Date.now();
      cached = { trackId: id, status: "approved" }; writeDisplay("version", cached);
      stableText(node, "Подмена активна · версия CELIKOM"); return;
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
