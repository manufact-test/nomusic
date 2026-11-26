import { ApiClient } from "./api-client.js";
import { AnalyticsEventService } from "./analytics-event-service.js";

export function createApiBroker(api, options = {}) {
  let configWarmer = null; let client = null; let accessToken = null; const networkHistory=[];
  const readConfig = options.readConfig || (async () => (await fetch(api.runtime.getURL("api/config.json"))).json());
  const withAccess = options.withAccess || (async () => { throw new Error("invalid_session"); });
  async function getClient(session) {
    const config = await readConfig();
    if (!config.baseUrl) return null;
    if (!client || accessToken !== session.access_token) {
      accessToken = session.access_token;
      client = new ApiClient(config.baseUrl, { ...options, onNetwork:item=>{networkHistory.push(item);if(networkHistory.length>16)networkHistory.shift();}, accessToken, clientVersion: api.runtime.getManifest().version });
    }
    return client;
  }
  function publicClient(origin) {
    if (!configWarmer || configWarmer.origin !== origin) configWarmer = new ApiClient(origin,
      {...options, clientVersion:api.runtime.getManifest().version,
        onNetwork:item=>{networkHistory.push(item);if(networkHistory.length>16)networkHistory.shift();}});
    return configWarmer;
  }
  let warming = null, warmRetryAt = 0;
  function warmPublicConfig() {
    if (options.warmPublicConfig !== true) return Promise.resolve(false);
    if (warming) return warming;
    if ((options.now || Date.now)() < warmRetryAt) return Promise.resolve(false);
    const pending = (async()=>{
      const config = await readConfig();
      if (!config.baseUrl) return false;
      await publicClient(config.baseUrl).config({refreshAheadMs:15000});
      return true;
    })().catch(()=>{warmRetryAt=(options.now || Date.now)()+5000;return false;})
      .finally(()=>{if(warming===pending)warming=null;});
    warming=pending;return pending;
  }
  const analytics = new AnalyticsEventService(api, async () => ({ config: () => withAccess(async (session) => (await getClient(session))?.config()), events: (batch) =>
    withAccess(async (session) => (await getClient(session))?.events(batch)) }));
  const handle = async (message, sender) => {
    let senderOrigin = null;
    try { senderOrigin = new URL(sender?.url).origin; } catch (_error) { /* reject */ }
    if (sender?.id !== api.runtime.id || senderOrigin !== "https://music.yandex.ru") return { ok: false, error: "invalid_api_sender" };
    if (message?.type === "CELIKOM_API_EVENT") {
      await analytics.enqueue(message.name, message.properties || {}); return { ok: true };
    }
    if (message?.service !== "yandex" || typeof message.trackId !== "string" || !/^[1-9]\d{0,23}$/.test(message.trackId)) return { ok: false, error: "invalid_track" };
    try {
      const config = await readConfig();
      if (!config.baseUrl) return { ok: true, asset: { found: false, retryAfterMs: 60000 }, configured: false };
      /* Only public configuration warms before authority checks. No signed
         descriptor or audio request is sent until withAccess has accepted. */
      let configReady;
      if (options.warmPublicConfig === true) {
        publicClient(config.baseUrl);
        if (message.forceRefresh === true) configWarmer.resetTransport();
        configReady = configWarmer.config();
        configReady.catch(()=>{});
      }
      return await withAccess(async (session) => {
        if (options.entitlement && !(await options.entitlement()).allowed) throw new Error("api_forbidden");
        const active = await getClient(session);
        return { ok: true, configured: true, asset: await active.resolve(message.service, message.trackId, { forceRefresh: message.forceRefresh === true, configReady }) };
      });
    } catch (error) {
      let code = String(error?.message || "");
      if(["auth_network_error","auth_timeout","auth_route_blocked"].includes(code))code="api_network_error";
      else if(code==="auth_unavailable")code="api_server_error";
      if (code === "invalid_session") return { ok: false, error: "api_access_missing" };
      const safeErrors = new Set(["api_access_denied", "api_forbidden", "api_network_error", "api_server_error",
        "api_http_error", "invalid_api_response", "invalid_audio_url", "invalid_api_config", "extension_update_required"]);
      return { ok: false, error: safeErrors.has(code) ? code : "api_unavailable" };
    }
  };
  return Object.assign(handle, { warmPublicConfig, networkDiagnostics:()=>networkHistory.map(item=>({...item})), resetTransport: () => { warmRetryAt=0; client?.resetTransport(); configWarmer?.resetTransport(); } });
}
