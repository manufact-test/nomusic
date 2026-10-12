import { privateUploadApiOrigin } from "../upload/contract.js";
import { readDisplay, writeDisplay } from "./display-cache.js";

// Global incident presentation is public and independent of login, trial,
// enabled state and the health/presence of the Yandex tab. Never grants access.
export function initIncidentStatus(options = {}) {
  const doc = options.document || document;
  const banner = doc.querySelector("[data-incident-banner]");
  const controls = doc.querySelector("[data-music-controls]");
  const hiddenDuringIncident = [controls, doc.querySelector("[data-music-details]")];
  let serverActive = readDisplay("incident")?.active === true ? true : null;
  let controllerActive = false, active = false, busy = false;
  const request = options.fetch || globalThis.fetch.bind(globalThis);
  const readConfig = options.readConfig || (async () => (await request(chrome.runtime.getURL("api/config.json"))).json());
  function paint() {
    const next = serverActive ?? controllerActive;
    if (banner) banner.hidden = !next;
    for (const node of hiddenDuringIncident) if (node) node.hidden = next;
    const changed = active !== next; active = next;
    if (changed) options.onChange?.();
  }
  async function refresh() {
    if (busy || !banner || !controls) return;
    busy = true;
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), 6000);
    try {
      const config = await readConfig();
      if (!config.baseUrl) return;
      const response = await request(privateUploadApiOrigin(config.baseUrl) + "/api/v1/config", {
        credentials: "omit", redirect: "error", cache: "no-store", signal: abort.signal
      });
      if (!response.ok) return;
      const data = await response.json();
      if (data?.incident?.service !== "yandex" || typeof data.incident.active !== "boolean") return;
      serverActive = data.incident.active;
      writeDisplay("incident", { active: serverActive });
      paint();
    } catch (_) { /* A transport error is not a declared incident; retain last confirmed presentation. */ }
    finally { clearTimeout(timer); busy = false; }
  }
  paint();
  return {
    active: () => active,
    updateController: (state) => { controllerActive = state?.suspended === true && state?.replacementError === "service_incident"; paint(); },
    refresh
  };
}
