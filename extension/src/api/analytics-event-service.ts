const events = new Set(["celikom_started", "celikom_stopped", "replacement_available", "replacement_started", "replacement_completed", "fail_open", "manual_original", "add_track_opened"]);
const errors = new Set(["api_unavailable", "media_error", "play_blocked", "binding_changed", "bridge_timeout", "asset_missing", "unknown"]);

// Discrete counters only. Never currentTime, filenames, URLs or per-user tracks.
export class AnalyticsEventService {
  constructor(api, getClient, options = {}) {
    this.api = api; this.getClient = getClient; this.uuid = options.uuid || (() => crypto.randomUUID());
    this.lock = Promise.resolve();
  }
  enqueue(name, properties = {}) {
    if (!events.has(name) || Object.keys(properties).some(k => !["service", "error_code"].includes(k))
      || (properties.service && properties.service !== "yandex") || (properties.error_code && !errors.has(properties.error_code))) return Promise.resolve(false);
    const task = this.lock.then(async () => {
      const client = await this.getClient();
      if (!client || (await client.config()).features.analytics !== true) return false;
      const stored = await this.api.storage.local.get(["analyticsInstallationId", "analyticsQueue"]);
      const installation = stored.analyticsInstallationId || this.uuid();
      const queued = Array.isArray(stored.analyticsQueue) ? stored.analyticsQueue : [];
      const recent = queued.filter(event => Date.now() - Date.parse(event.occurred_at) < 86400000).slice(-49);
      const event = { event_id: this.uuid(), event_name: name, occurred_at: new Date().toISOString(), properties };
      const batch = { schema_version: 1, installation_id: installation, client_version: this.api.runtime.getManifest().version, platform: "chromium", events: [...recent, event] };
      await this.api.storage.local.set({ analyticsInstallationId: installation, analyticsQueue: batch.events });
      try {
        const result = await client.events(batch);
        const finished = new Set(result.results.map(r => r.event_id));
        await this.api.storage.local.set({ analyticsQueue: batch.events.filter(e => !finished.has(e.event_id)) });
      } catch (_error) { /* retry same UUIDs on the next discrete event */ }
      return true;
    });
    this.lock = task.catch(() => false); return this.lock;
  }
}
