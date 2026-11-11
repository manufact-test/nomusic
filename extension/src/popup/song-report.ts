import { uploadTargetFromStatus } from "../upload/contract.js";

export const reportCategories = {
  not_replacing: "Не включается версия CELIKOM",
  wrong_version: "Играет неправильная версия",
  audio_issue: "Звук обрывается или рассинхронизируется",
  other: "Другая проблема"
};

// Deliberately exclude URLs, raw logs, free-form connection details and account data.
export function buildSongReport(state, category, version) {
  const target = uploadTargetFromStatus(state);
  if (!target || !Object.hasOwn(reportCategories, category)) throw new Error("track_required");
  return { category, version, track: { id: target.id, title: target.title, artist: target.artist, album: target.album }, diagnostics: buildSupportReport(state, version).diagnostics };
}

// Collected only when the user submits support; never contains the full admin dump.
export function buildSupportReport(state, version) {
  state = state && typeof state === "object" ? state : {};
  const target = uploadTargetFromStatus(state);
  const diagnostics: any = {};
  const code = value => typeof value === "string" && /^[a-zA-Z0-9_:.-]{1,96}$/.test(value) ? value : null;
  const values = {
    phase: code(state.phase), replacementError: code(state.replacementError),
    connectionError: code(state.connection?.error), restoreReason: code(state.playback?.lastRestore?.reason),
    enabled: state.enabled, suspended: state.suspended, recovering: state.recovering,
    bridgeReady: state.bridge?.ready, bridgeHealthy: state.bridge?.healthy,
    controllerPresent: state.connection?.controllerPresent, paused: state.player?.paused,
    activationCount: state.playback?.activationCount, restoreCount: state.playback?.restoreCount,
    currentTime: state.player?.currentTime, duration: state.player?.duration,
    durationMs: target?.durationMs, readyState: state.player?.readyState
  };
  for (const [key, value] of Object.entries(values)) {
    if (typeof value === "boolean" || typeof value === "string" || (typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1e9)) diagnostics[key] = value;
  }
  diagnostics.network = (Array.isArray(state.network) ? state.network : []).slice(-12)
    .filter(row => ["config", "auth/me", "entitlement", "tracks/version-status", "resolve", "rewards"].includes(row?.endpoint) && /^[a-z_]{1,64}$/.test(row.result))
    .map(row => ({ endpoint: row.endpoint, httpStatus: Number.isInteger(row.httpStatus) && row.httpStatus >= 100 && row.httpStatus <= 599 ? row.httpStatus : null,
      result: row.result, elapsedMs: Number.isFinite(row.elapsedMs) && row.elapsedMs >= 0 && row.elapsedMs <= 300000 ? Math.round(row.elapsedMs) : null }));
  // Short, explicitly submitted support timeline; never include console logs or URLs.
  const now = Date.now();
  const trace = (Array.isArray(state.network) ? state.network : []).slice(-20)
    .filter(row => ["config","auth/me","entitlement","tracks/version-status","resolve","rewards"].includes(row?.endpoint))
    .map(row => ({
      event: "backend_http", endpoint: row.endpoint,
      ageMs: Number.isFinite(row.at) ? Math.max(0, Math.min(86400000, Math.round(now - row.at))) : 0,
      elapsedMs: Number.isFinite(row.elapsedMs) ? Math.max(0, Math.min(86400000, Math.round(row.elapsedMs))) : 0,
      httpCode: Number.isInteger(row.httpStatus) && row.httpStatus>=100 && row.httpStatus<=599 ? row.httpStatus : undefined,
      result: code(row.result) || undefined
    }));
  trace.push({event:"status",ageMs:0,phase:code(state.phase) || undefined,
    reason:code(state.replacementError) || undefined});
  for (const row of (Array.isArray(state.playback?.startupHistory) ? state.playback.startupHistory : []).slice(-6)) {
    if (!row || !Number.isFinite(row.prepareMs)) continue;
    trace.push({event:"replacement_prepared",ageMs:Number.isFinite(row.at)?Math.max(0,Math.min(86400000,Math.round(now-row.at))):0,
      elapsedMs:Math.max(0,Math.min(86400000,Math.round(row.prepareMs))),
      sourcePositionMs:Number.isFinite(row.masterTimeMs)?Math.max(0,Math.min(86400000,Math.round(row.masterTimeMs))):0});
  }
  diagnostics.trace=trace.slice(-32);
  const report = { schema_version: 1, platform: "chromium", version, ...(target ? { track: { id: target.id, title: target.title, artist: target.artist, album: target.album } } : {}), diagnostics };
  // Stay below the support HTTP body limit even with the maximum user comment.
  while (new TextEncoder().encode(JSON.stringify(report)).length > 6500 && diagnostics.trace.length > 1) diagnostics.trace.shift();
  return report;
}
