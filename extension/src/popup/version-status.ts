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
  // A short display preview is never used for authorization or upload decisions.
  const rememberedTrack=readDisplay("track"), preview=readDisplay("version");
  const age=Date.now()-preview?.displayCheckedAt;
  let cached=preview&&preview.trackId===rememberedTrack?.id&&Object.hasOwn(labels,preview.status)&&Number.isFinite(age)&&age>=0&&age<300000?preview:null;
  const noTrack=rememberedTrack?.id===null;
  let trackId=cached?.trackId||"",checkedAt=0,request=0,loading=false;
  let verifiedAt=0,pendingRead=null;
  const FRESH_FOR_MS=15000;
  if(node)node.hidden=noTrack;
  stableText(node,noTrack?"":cached?labels[cached.status]:"Версия песни CELIKOM",false);
  const remember = (id, status) => {
    cached = { trackId: id, status, displayCheckedAt: Date.now() };
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
      stableText(node, id ? "Версия песни CELIKOM" : "");
    }
    node.hidden = !id;
    if (!id) { cached = null; verifiedAt = 0; clearDisplay("version"); stableText(node, ""); return; }
    if (state.phase === "REPLACEMENT_ACTIVE") {
      request++; loading = false; checkedAt = Date.now();
      cached = { trackId: id, status: "approved", displayCheckedAt: Date.now() }; verifiedAt = 0; writeDisplay("version", cached);
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
    const generation = request;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const status = await presenceRead(id);
        // A logout, song switch or explicit invalidation may occur while
        // awaiting the server; never publish that older response afterward.
        if (generation !== request || latestState?.track?.id !== id) throw new Error("track_changed");
        remember(id, status);
        checkedAt = Date.now();
        return status;
      } catch (error) {
        const code = String(error?.message || "");
        if (code === "track_changed") throw error;
        if (attempt === 0 && ["auth_unavailable", "auth_network_error", "auth_timeout",
             "upload_status_unavailable", "request_timeout"].includes(code)) {
          await new Promise(resolve => setTimeout(resolve, 150));
          if (generation !== request || latestState?.track?.id !== id) throw new Error("track_changed");
          continue;
        }
        throw error;
      }
    }
    throw new Error("upload_status_unavailable");
  };
  refreshVersion.invalidate = id => {
    if (id && id !== trackId) return;
    request++; checkedAt = 0; verifiedAt = 0; cached = null;
    loading = false; pendingRead = null;
  };
  return refreshVersion;
}
