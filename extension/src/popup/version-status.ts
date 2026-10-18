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
  let verifiedAt = 0, pendingRead = null;
  const FRESH_FOR_MS = 15000;
  if (node) node.hidden = noTrack;
  stableText(node, noTrack ? "" : "Проверяем наличие версии CELIKOM…", false);
  const remember = (id, status) => {
    cached = { trackId: id, status };
    verifiedAt = Date.now();
    writeDisplay("version", cached);
    stableText(node, labels[status]);
  };
  // Share the already running presence check with the upload button. The
  // cache is for display only; submitting an audio file still performs a
  // fresh server check and server-side duplicate protection.
  function presenceRead(id) {
    if (pendingRead?.id === id) return pendingRead.promise;
    const promise = send({ type: "CELIKOM_AUTH", action: "track-status", track_id: id })
      .then(result => {
        if (result?.ok && Object.hasOwn(labels, result.status)) return result.status;
        throw new Error(result?.error || "upload_status_unavailable");
      });
    const entry = { id, promise };
    pendingRead = entry;
    void promise.finally(() => { if (pendingRead === entry) pendingRead = null; }).catch(() => {});
    return promise;
  }
  document.addEventListener?.("celikom-account-logout", () => {
    request++; loading = false; checkedAt = 0; cached = null; verifiedAt = 0; pendingRead = null; clearDisplay("version");
    stableText(node, "Войдите, чтобы проверить версию песни CELIKOM");
  });
  let latestState = null;
  document.addEventListener?.("celikom-account-login", () => {
    request++; loading = false; checkedAt = 0; cached = null; verifiedAt = 0; pendingRead = null;
    if (latestState) void refreshVersion(latestState);
  });
  async function refreshVersion(state) {
    latestState = state;
    if (!node) return;
    const id = state.track?.id || "";
    if (id !== trackId) {
      trackId = id; checkedAt = 0; loading = false; request++;
      cached = null; verifiedAt = 0;
      stableText(node, id ? "Проверяем наличие версии CELIKOM…" : "");
    }
    node.hidden = !id;
    if (!id) { cached = null; verifiedAt = 0; clearDisplay("version"); stableText(node, ""); return; }
    if (state.phase === "REPLACEMENT_ACTIVE") {
      request++; loading = false; checkedAt = Date.now();
      cached = { trackId: id, status: "approved" }; verifiedAt = 0; writeDisplay("version", cached);
      stableText(node, "Подмена активна · версия CELIKOM"); return;
    }
    if (cached?.trackId === id) stableText(node, labels[cached.status]);
    if (loading || (checkedAt && Date.now() - checkedAt < 15000)) return;
    const current = ++request; loading = true;
    try {
      const status = await presenceRead(id);
      if (current !== request || trackId !== id) return;
      remember(id, status);
    } catch (error) {
      if (current === request && trackId === id) {
        if (error?.message === "invalid_session") {
          cached = null; verifiedAt = 0; clearDisplay("version");
          stableText(node, "Войдите, чтобы проверить версию песни CELIKOM");
        } else if (cached?.trackId !== id) stableText(node, "Не удалось проверить версию песни CELIKOM");
      }
    } finally {
      if (current === request) { loading = false; checkedAt = Date.now(); }
    }
  }
  // Callers may await an existing in-flight check. An already verified status
  // is returned immediately without a second request or any transient UI.
  refreshVersion.lookup = async id => {
    if (!/^[1-9]\d{0,23}$/.test(id)) throw new Error("invalid_track");
    if (latestState?.phase === "REPLACEMENT_ACTIVE" && latestState.track?.id === id) return "approved";
    if (cached?.trackId === id && verifiedAt > 0 && Date.now() - verifiedAt < FRESH_FOR_MS)
      return cached.status;
    return presenceRead(id);
  };
  return refreshVersion;
}
