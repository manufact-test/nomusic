/*
 * W33 disposable CI ONLY, appended to compiled host.cjs by w23-host-smoke.ps1
 * ONLY when CELIKOM_W33_RUNTIME_PROBE=1. Never included in owner installer.
 * Checks a fixed deliberately INVALID token URL in a genuine Yandex renderer:
 * - An HTTP 403 with ACAO would be observable if network/CORS/CSP permit fetch.
 * - A generic FETCH_BLOCKED suggests a renderer boundary (CSP/network/redirect).
 * No Yandex account, real song, signed URL or token is accessed.
 */
(() => {
  // Prove that this CI-only appendix actually executed inside Electron main.
  try {
    const dev = process.env.CELIKOM_W23_DEV_DIAG || "";
    if (dev) require("node:fs").appendFileSync(dev,
      "W33_RT_BOOTSTRAP_" + (process.env.CELIKOM_W33_RUNTIME_PROBE === "1" ? "ON" : "OFF") + "\n");
  } catch {}
  if (process.env.CELIKOM_W33_RUNTIME_PROBE !== "1") return;
  const { webContents } = require("electron");
  const fs = require("node:fs");
  const log = process.env.CELIKOM_W23_DEV_DIAG || "";
  const checked = new Set();
  const began = Date.now();
  function note(value) {
    if (!log || !/^[A-Z0-9_]{8,96}$/.test(value)) return;
    try { fs.appendFileSync(log, "W33_RT_" + value + "\n"); } catch {}
  }
  async function rendererProbe() {
    const native = location.protocol === "musicapplication:";
    const type = native ? "NATIVE" :
      location.origin === "https://music.yandex.ru" ? "MUSIC_WEB" :
      location.origin === "https://next.music.yandex.ru" ? "NEXT_WEB" :
      location.origin === "https://desktop.app.music.yandex.net" ? "DESKTOP_WEB" :
      "OTHER";
    const base = "https://darkred-camel-588676.hostingersite.com";
    const url = base + "/api/v1/audio/7?token=" + "0".repeat(64) +
      "&expires=1800000180&sid=1";
    let csp = "NONE";
    const mark = event => {
      if (!event || typeof event.blockedURI !== "string") return;
      try {
        if (new URL(event.blockedURI).origin !== base) return;
        const directive = String(event.effectiveDirective || "");
        csp = directive === "connect-src" ? "CONNECT_SRC" :
          directive === "media-src" ? "MEDIA_SRC" : "OTHER";
      } catch {}
    };
    document.addEventListener("securitypolicyviolation", mark, true);
    const abort = new AbortController();
    const t = setTimeout(() => abort.abort(), 4500);
    let outcome = "UNKNOWN";
    try {
      const r = await fetch(url, {
        method: "GET", mode: "cors", credentials: "omit",
        redirect: "error", cache: "no-store",
        headers: { Range: "bytes=0-31" }, signal: abort.signal
      });
      outcome = r.status === 403 ? "HTTP_403_VISIBLE" :
        r.status === 200 ? "HTTP_200_VISIBLE" :
        r.status === 206 ? "HTTP_206_VISIBLE" : "HTTP_OTHER_VISIBLE";
      try { await r.body?.cancel(); } catch {}
    } catch (error) {
      outcome = error?.name === "AbortError" ? "TIMEOUT" :
        error instanceof TypeError ? "FETCH_BLOCKED_TYPEERROR" : "FETCH_OTHER_ERROR";
    } finally {
      clearTimeout(t);
      await new Promise(resolve => setTimeout(resolve, 180));
      document.removeEventListener("securitypolicyviolation", mark, true);
    }
    return { type, outcome, csp };
  }
  const clock = setInterval(() => {
    if (Date.now() - began > 19000) { clearInterval(clock); return; }
    for (const view of webContents.getAllWebContents()) {
      if (view.isDestroyed() || checked.has(view.id)) continue;
      let allowed = false;
      try {
        const u = new URL(view.getURL());
        allowed = [
          "https://desktop.app.music.yandex.net",
          "https://music.yandex.ru",
          "https://next.music.yandex.ru",
          "https://music.yandex.com"
        ].includes(u.origin) ||
          (u.protocol === "musicapplication:" && u.hostname === "desktop");
      } catch {}
      if (!allowed) continue;
      checked.add(view.id);
      note("APPROVED_RENDERER_FOUND");
      void view.executeJavaScript("(" + rendererProbe.toString() + ")()")
        .then(result => {
          const type = ["NATIVE", "MUSIC_WEB", "NEXT_WEB", "DESKTOP_WEB", "OTHER"]
            .includes(result?.type) ? result.type : "OTHER";
          const outcome = ["HTTP_403_VISIBLE", "HTTP_200_VISIBLE", "HTTP_206_VISIBLE",
            "HTTP_OTHER_VISIBLE", "TIMEOUT", "FETCH_BLOCKED_TYPEERROR",
            "FETCH_OTHER_ERROR"].includes(result?.outcome) ? result.outcome : "UNRECOGNIZED";
          const csp = ["NONE", "CONNECT_SRC", "MEDIA_SRC", "OTHER"]
            .includes(result?.csp) ? result.csp : "UNRECOGNIZED";
          note(type + "_" + outcome + "_CSP_" + csp);
        })
        .catch(() => note("RENDERER_EXECUTION_FAILED"));
    }
  }, 500);
})();
