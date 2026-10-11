// Toolbar presentation only. Color never authorizes playback or extends access.
export function createActionIcon(api, clock = {}) {
  const schedule = clock.schedule || ((fn, delay) => setTimeout(fn, delay));
  const cancel = clock.cancel || ((timer) => clearTimeout(timer));
  const active = new Map();
  let shown = null, pending = Promise.resolve();
  function paint() {
    const enabled = active.size > 0;
    const color = enabled ? "green" : "gray";
    const path = Object.fromEntries([16,32,48,128].map(size => [size, `/assets/icons/${color}-${size}.png`]));
    pending = pending.catch(() => {}).then(async () => {
      if (shown === enabled) return;
      // MV3 resolves paths against background/service-worker.js; root paths
      // keep icon lookup out of the background/assets directory.
      await api.action?.setIcon({ path });
      shown = enabled;
      await api.action?.setTitle({ title: enabled ? "CELIKOM · включён и подключён к Яндекс Музыке" : "CELIKOM · не подключён" });
    }).catch(() => {
      console.warn("CELIKOM: toolbar icon could not be loaded; next heartbeat will retry.");
    });
  }
  function update(tabId, connected) {
    if (!Number.isInteger(tabId)) return;
    if (active.has(tabId)) cancel(active.get(tabId));
    active.delete(tabId);
    if (connected) {
      const timer = schedule(() => { active.delete(tabId); paint(); }, 6000);
      timer?.unref?.();
      active.set(tabId, timer);
    }
    paint();
  }
  function clear() { for (const timer of active.values()) cancel(timer); active.clear(); paint(); }
  paint();
  api.tabs.onRemoved?.addListener(tabId => update(tabId, false));
  api.tabs.onUpdated?.addListener((tabId, change) => { if (change.status === "loading") update(tabId, false); });
  api.storage.onChanged?.addListener((changes, area) => { if (area === "local" && changes.enabled?.newValue === false) clear(); });
  return { update, clear };
}
