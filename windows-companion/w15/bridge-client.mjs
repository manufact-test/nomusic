/**
 * Exact-origin local transport only. Bridge session token lives in add-on
 * storage, NEVER in Yandex cookies, URL query strings or CELIKOM server logs.
 * Resolve grants are short-lived audio bearer URLs, not account tokens.
 */
export const LOCAL_ORIGIN = "http://127.0.0.1:21471";
const TOKEN_KEY = "celikom-w15-bridge-token";
const HEX = /^[a-f0-9]{64}$/;
export function createCompanionBridge({ net, storage }) {
  if (typeof net?.json !== "function" ||
      typeof storage?.get !== "function" ||
      typeof storage?.set !== "function") throw Error("W15_BRIDGE_NOT_SUPPORTED");
  let secret = "";
  const endpoint = (path) => LOCAL_ORIGIN + path;
  const headers = () => ({ "X-Celikom-Bridge-Token": secret });
  async function initialize() {
    const saved = await storage.get(TOKEN_KEY);
    secret = typeof saved === "string" && HEX.test(saved) ? saved : "";
  }
  async function health() {
    try {
      const h = await net.json(endpoint("/v1/health"), {
        credentials:"omit", cache:"no-store", timeoutMs:2500
      });
      return h?.companion === true && h?.version === 15;
    } catch { return false; }
  }
  async function pair(code) {
    if (!/^[0-9]{6}$/.test(code)) return false;
    try {
      const response = await net.json(endpoint("/v1/pair"), {
        method:"POST", credentials:"omit", cache:"no-store", timeoutMs:3000,
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({code})
      });
      if (!HEX.test(response?.bridgeToken || "")) return false;
      secret = response.bridgeToken;
      await storage.set(TOKEN_KEY, secret);
      return true;
    } catch { return false; }
  }
  async function state() {
    if (!HEX.test(secret)) return {paired:false, enabled:false};
    try {
      const s = await net.json(endpoint("/v1/state"), {
        credentials:"omit", cache:"no-store", timeoutMs:2500, headers: headers()
      });
      return {paired:true, enabled:s?.enabled===true, signedIn:s?.signedIn===true};
    } catch { return {paired:false, enabled:false}; }
  }
  async function resolve(id, signal) {
    if (!HEX.test(secret) || !/^[1-9][0-9]{0,23}$/.test(id)) return null;
    try {
      const result = await net.json(endpoint("/v1/resolve?track_id="+id), {
        credentials:"omit", cache:"no-store", timeoutMs:6000,
        headers:headers(), signal
      });
      return result?.found === true ? result.grant ?? null : null;
    } catch { return null; }
  }
  async function heartbeat(trackId, status) {
    if (!HEX.test(secret)) return;
    try {
      await net.json(endpoint("/v1/heartbeat"), {
        method:"POST", credentials:"omit", cache:"no-store", timeoutMs:2500,
        headers:{...headers(), "Content-Type":"application/json"},
        body:JSON.stringify({trackId, status})
      });
    } catch { /* UI heartbeat is advisory, never an audio control path */ }
  }
  return Object.freeze({
    initialize, health, pair, state, resolve, heartbeat,
    get pairedLocally(){return HEX.test(secret);}
  });
}
