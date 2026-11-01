import { ApiClient } from "./api-client.js";

// Only the extension's trusted popup may invoke this via its background worker.
// Never return a token or signed audio URL to the popup or content scripts.
export async function validateApiAccess(api, rawToken, options = {}) {
  const token = typeof rawToken === "string" ? rawToken.trim() : "";
  if (token.length < 24 || token.length > 512) return { ok: false, error: "invalid_access_code" };
  try {
    const readConfig = options.readConfig || (async () => (await fetch(api.runtime.getURL("api/config.json"))).json());
    const config = await readConfig();
    const client = new ApiClient(config.baseUrl, {
      ...options, accessToken: token, clientVersion: api.runtime.getManifest().version
    });
    // Valid but currently unmapped ID: this verifies genuine Bearer auth
    // without exposing a signed URL or initiating an audio download.
    const result = await client.request("/api/v1/resolve?service=yandex&track_id=1");
    if (typeof result?.found !== "boolean") throw new Error("invalid_api_response");
    return { ok: true, token };
  } catch (error) {
    const code = String(error?.message || "");
    const safe = ["api_access_denied", "api_forbidden", "api_network_error", "api_server_error",
      "api_http_error", "invalid_api_response", "invalid_api_origin"];
    return { ok: false, error: safe.includes(code) ? code : "api_unavailable" };
  }
}
