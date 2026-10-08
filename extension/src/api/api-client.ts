// API requests execute in the extension worker, never in the page's MAIN world.
export class ApiClient {
  constructor(baseUrl, options = {}) {
    const url = new URL(baseUrl);
    const local = url.protocol === "http:" && ["127.0.0.1", "localhost"].includes(url.hostname);
    if ((!local && url.protocol !== "https:") || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("invalid_api_origin");
    this.origin = url.origin;
    this.fetch = options.fetch || globalThis.fetch;
    this.now = options.now || Date.now;
    this.accessToken = options.accessToken || "";
    this.clientVersion = options.clientVersion || "0.4.0";
    this.cache = new Map(); this.pending = new Map(); this.configCache = null;
  }
  async request(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    try {
      const response = await this.fetch(this.origin + path, {
        credentials: "omit", redirect: "error", cache: "no-store", signal: controller.signal,
        method: options.method || "GET", body: options.body,
        headers: { ...(this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {}), ...(options.body ? { "Content-Type": "application/json" } : {}) }
      });
      if (!response.ok || !response.headers.get("content-type")?.startsWith("application/json")) throw new Error("api_unavailable");
      // Bound the body before parsing; do not buffer an untrusted response whole.
      const reader = response.body.getReader(); const chunks = []; let size = 0;
      try {
        for (;;) {
          const { value, done } = await reader.read(); if (done) break;
          size += value.byteLength; if (size > 65536) throw new Error("invalid_api_response"); chunks.push(value);
        }
      } finally { await reader.cancel(); }
      const merged = new Uint8Array(size); let offset = 0;
      for (const chunk of chunks) { merged.set(chunk, offset); offset += chunk.byteLength; }
      return JSON.parse(new TextDecoder().decode(merged));
    } finally { clearTimeout(timer); }
  }
  async config() {
    if (this.configCache?.until > this.now()) return this.configCache.value;
    const value = await this.request("/api/v1/config");
    if (value?.api_version !== 1 || typeof value.maintenance !== "boolean" || typeof value.features?.replacements !== "boolean"
      || !/^\d+\.\d+\.\d+$/.test(value.minimum_extension_version)) throw new Error("invalid_api_config");
    const parts = (s) => s.split(".").map(Number);
    const required = parts(value.minimum_extension_version); const current = parts(this.clientVersion);
    for (let i = 0; i < 3; i++) { if (current[i] < required[i]) throw new Error("extension_update_required"); if (current[i] > required[i]) break; }
    this.configCache = { value, until: this.now() + 60000 }; return value;
  }
  async resolve(service, trackId) {
    if (service !== "yandex" || !/^[1-9]\d{0,23}$/.test(trackId)) throw new Error("invalid_track");
    const key = `${service}:${trackId}`;
    if (this.cache.get(key)?.until > this.now()) return this.cache.get(key).value;
    if (this.pending.has(key)) return this.pending.get(key);
    const pending = this.resolveUncached(service, trackId).then((value) => {
      if (this.cache.size >= 200) this.cache.delete(this.cache.keys().next().value);
      const ttl = value.found ? Math.min(120000, value.expiresAt - this.now() - 30000) : 15000;
      this.cache.set(key, { value, until: this.now() + Math.max(0, ttl) }); return value;
    }).finally(() => this.pending.delete(key));
    this.pending.set(key, pending); return pending;
  }
  async resolveUncached(service, trackId) {
    const config = await this.config();
    if (config.maintenance || !config.features.replacements) return { found: false, retryAfterMs: 15000 };
    const result = await this.request(`/api/v1/resolve?service=${service}&track_id=${trackId}`);
    if (result?.found === false) return { found: false, retryAfterMs: 15000 };
    if (result?.found !== true || !Number.isSafeInteger(result.replacement_id) || result.replacement_id <= 0
      || !Number.isSafeInteger(result.duration_ms) || result.duration_ms <= 0 || result.duration_ms > 86400000
      || !Number.isSafeInteger(result.version) || result.version < 1 || !Number.isSafeInteger(result.expires_at)
      || result.expires_at * 1000 <= this.now() + 30000 || result.expires_at * 1000 > this.now() + 1800000
      || typeof result.audio_url !== "string") throw new Error("invalid_api_response");
    const url = new URL(result.audio_url, this.origin);
    if (url.origin !== this.origin || url.username || url.password || url.hash || url.pathname !== `/api/v1/audio/${result.replacement_id}`
      || !/^[a-f0-9]{64}$/.test(url.searchParams.get("token") || "") || url.searchParams.get("expires") !== String(result.expires_at)
      || [...url.searchParams.keys()].length !== 2) throw new Error("invalid_audio_url");
    return { found: true, url: url.href, durationMs: result.duration_ms, replacementId: result.replacement_id, version: result.version, expiresAt: result.expires_at * 1000, demoLoop: false };
  }
  async events(batch) {
    const result = await this.request("/api/v1/events/batch", { method: "POST", body: JSON.stringify(batch) });
    if (result?.schema_version !== 1 || !Array.isArray(result.results) || result.results.length !== batch.events.length
      || result.results.some((r, i) => r.event_id !== batch.events[i].event_id || !["accepted", "duplicate", "rejected"].includes(r.status))) throw new Error("invalid_event_response");
    return result;
  }
}
