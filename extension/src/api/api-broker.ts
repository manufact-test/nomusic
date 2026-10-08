import { ApiClient } from "./api-client.js";
import { AnalyticsEventService } from "./analytics-event-service.js";

export function createApiBroker(api, options = {}) {
  let client = null; let accessToken = null;
  const readConfig = options.readConfig || (async () => (await fetch(api.runtime.getURL("api/config.json"))).json());
  const getClient = async () => {
    const config = await readConfig();
    if (!config.baseUrl) return null;
    const stored = await api.storage.local.get("apiTestToken");
    if (!client || accessToken !== stored.apiTestToken) {
      accessToken = stored.apiTestToken || "";
      client = new ApiClient(config.baseUrl, { ...options, accessToken, clientVersion: api.runtime.getManifest().version });
    }
    return client;
  };
  const analytics = new AnalyticsEventService(api, getClient);
  return async (message, sender) => {
    let senderOrigin = null;
    try { senderOrigin = new URL(sender?.url).origin; } catch (_error) { /* reject malformed sender */ }
    if (sender?.id !== api.runtime.id || senderOrigin !== "https://music.yandex.ru") return { ok: false, error: "invalid_api_sender" };
    if (message?.type === "CELIKOM_API_EVENT") {
      await analytics.enqueue(message.name, message.properties || {}); return { ok: true };
    }
    if (message?.service !== "yandex" || typeof message.trackId !== "string" || !/^[1-9]\d{0,23}$/.test(message.trackId)) return { ok: false, error: "invalid_track" };
    try {
      const active = await getClient();
      if (!active) return { ok: true, asset: { found: false, retryAfterMs: 60000 }, configured: false };
      if (!active.accessToken) return { ok: false, error: "api_access_missing" };
      return { ok: true, configured: true, asset: await active.resolve(message.service, message.trackId) };
    } catch (error) {
      const code = String(error?.message || "");
      const safeErrors = new Set(["api_access_denied", "api_forbidden", "api_network_error", "api_server_error",
        "api_http_error", "invalid_api_response", "invalid_audio_url", "invalid_api_config", "extension_update_required"]);
      return { ok: false, error: safeErrors.has(code) ? code : "api_unavailable" };
    }
  };
}
