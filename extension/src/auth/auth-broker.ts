// Customer tokens are kept in extension-origin IndexedDB, not shared chrome.storage.local.
// Page/content scripts have no access to this extension-origin database.
export function createSecretStore() {
  const open = () => new Promise((resolve, reject) => {
    const req = indexedDB.open("celikom-user-auth-v1", 1);
    req.onupgradeneeded = () => req.result.createObjectStore("secrets");
    req.onerror = () => reject(new Error("auth_storage_unavailable"));
    req.onsuccess = () => resolve(req.result);
  });
  async function transact(mode, action) {
    const db = await open();
    try {
      return await new Promise((resolve, reject) => {
        const tx = db.transaction("secrets", mode);
        const request = action(tx.objectStore("secrets"));
        let result;
        request.onsuccess = () => { result = request.result; };
        tx.oncomplete = () => resolve(result);
        tx.onabort = () => reject(new Error("auth_storage_unavailable"));
        request.onerror = () => reject(new Error("auth_storage_unavailable"));
        tx.onerror = () => reject(new Error("auth_storage_unavailable"));
      });
    } finally { db.close(); }
  }
  return {
    get: () => transact("readonly", (store) => store.get("active")),
    set: (value) => transact("readwrite", (store) => store.put(value, "active")),
    clear: () => transact("readwrite", (store) => store.delete("active"))
  };
}

export function createAuthBroker(api, options = {}) {
  const store = options.store || createSecretStore();
  const request = options.fetch || globalThis.fetch.bind(globalThis);
  const readConfig = options.readConfig || (async () => (await fetch(api.runtime.getURL("api/config.json"))).json());
  let installationPromise = null;
  let refreshPromise = null;
  let sessionVersion = 0;

  async function installationId() {
    if (!installationPromise) {
      installationPromise = (async () => {
        const saved = await api.storage.local.get("celikomInstallationId");
        if (typeof saved.celikomInstallationId === "string" &&
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(saved.celikomInstallationId)) {
          return saved.celikomInstallationId;
        }
        const id = crypto.randomUUID();
        await api.storage.local.set({ celikomInstallationId: id });
        return id;
      })().catch((error) => { installationPromise = null; throw error; });
    }
    return installationPromise;
  }

  async function origin() {
    const c = await readConfig();
    const url = new URL(c.baseUrl);
    if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash || url.pathname !== "/") {
      throw new Error("auth_unavailable");
    }
    return url.origin;
  }

  async function apiRequest(path, method = "GET", data = null, access = "") {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);
    try {
      const response = await request((await origin()) + "/api/v1/" + path, {
        method, credentials: "omit", redirect: "error", cache: "no-store", signal: ctrl.signal,
        headers: { ...(data ? { "Content-Type": "application/json" } : {}), ...(access ? { Authorization: "Bearer " + access } : {}) },
        body: data ? JSON.stringify(data) : undefined
      });
      if (!response.headers.get("content-type")?.startsWith("application/json")) throw new Error("auth_unavailable");
      if (Number(response.headers.get("content-length")) > 16384) throw new Error("auth_unavailable");
      const parsed = await response.text();
      if (parsed.length > 16384) throw new Error("auth_unavailable");
      const result = JSON.parse(parsed);
      if (!response.ok) {
        const safe = new Set(["invalid_credentials", "account_disabled", "account_unavailable", "weak_password", "rate_limited", "invalid_session", "invalid_request", "email_unverified", "email_unavailable", "invalid_code", "access_denied", "uploads_disabled"]);
        throw new Error(safe.has(result?.error) ? result.error : "auth_unavailable");
      }
      return result;
    } finally { clearTimeout(timer); }
  }

  async function isAvailable() {
    try {
      const response = await apiRequest("config");
      return response?.features?.auth === true;
    } catch (_error) { return false; }
  }

  async function refresh(stored) {
    if (!refreshPromise) {
      const version = sessionVersion;
      refreshPromise = (async () => {
        const data = await apiRequest("auth/refresh", "POST", {
          refresh_token: stored.refresh_token, installation_id: await installationId()
        });
        if (!validAuth(data)) throw new Error("auth_unavailable");
        if (version !== sessionVersion || (await store.get())?.refresh_token !== stored.refresh_token) throw new Error("invalid_session");
        await store.set(data);
        return data;
      })().finally(() => { refreshPromise = null; });
    }
    return refreshPromise;
  }

  function validAuth(value) {
    return /^[0-9a-f]{64}$/.test(value?.access_token || "") &&
      /^[0-9a-f]{64}$/.test(value?.refresh_token || "") &&
      typeof value?.user?.id === "number" && typeof value?.user?.email === "string";
  }

  async function current() {
    const saved = await store.get();
    if (!saved) throw new Error("invalid_session");
    try {
      await apiRequest("auth/me", "GET", null, saved.access_token);
      return saved;
    } catch (error) {
      // Refresh only when the server explicitly rejects the access token.
      // Transport errors must not rotate an otherwise valid session or lose credentials.
      if (error?.message !== "invalid_session") throw error;
      return refresh(saved);
    }
  }

  // Only extension-owned callers receive credentials; never content/page messages.
  async function withAccess(callback) {
    const version = sessionVersion;
    const saved = await current();
    if (version !== sessionVersion) throw new Error("invalid_session");
    const result = await callback(saved);
    if (version !== sessionVersion) throw new Error("invalid_session");
    return result;
  }

  function validEntitlement(value) {
    return typeof value?.allowed === "boolean" && typeof value?.reason === "string"
      && typeof value?.source === "string" && (value.valid_until === null ||
        (typeof value.valid_until === "string" && /Z$/.test(value.valid_until) && Number.isFinite(Date.parse(value.valid_until))));
  }
  async function withEntitledAccess(callback) {
    return withAccess(async (saved) => {
      const access = await apiRequest("entitlement", "GET", null, saved.access_token);
      if (!validEntitlement(access)) throw new Error("auth_unavailable");
      if (!access.allowed) throw new Error("api_forbidden");
      return callback(saved);
    });
  }
  async function entitlement(activate = false) {
    return withAccess(async (saved) => {
      const response = activate
        ? (await apiRequest("auth/activate", "POST", {}, saved.access_token)).entitlement
        : await apiRequest("entitlement", "GET", null, saved.access_token);
      if (!validEntitlement(response)) throw new Error("auth_unavailable");
      return response;
    });
  }

  async function perform(action, message = {}) {
    if (action === "installation") return { ok: true, installation_id: await installationId() };
    if (action === "status") {
      const saved = await store.get();
      if (!await isAvailable()) {
        if (saved?.user?.email) return { ok: true, available: true, signedIn: false,
          localSession: true, user: saved.user, error: "auth_unavailable" };
        return { ok: true, available: false, signedIn: false };
      }
      if (!saved) return { ok: true, available: true, signedIn: false };
      try {
        const active = await current();
        return { ok: true, available: true, signedIn: true, user: active.user };
      } catch (error) {
        if (error?.message !== "invalid_session" && saved?.user?.email)
          return { ok: true, available: true, signedIn: false, localSession: true,
            user: saved.user, error: "auth_unavailable" };
        return { ok: true, available: true, signedIn: false,
          error: "session_expired" };
      }
    }
    if (!await isAvailable()) return { ok: false, error: "auth_disabled" };
    try {
      if (action === "login" || action === "register") {
        if (typeof message.email !== "string" || typeof message.password !== "string" ||
            message.email.length > 254 || message.password.length > 128) return { ok: false, error: "invalid_request" };
        const credentials = await apiRequest("auth/" + action, "POST", {
          email: message.email, password: message.password, installation_id: await installationId()
        });
        if (credentials?.verification_required === true) {
          return { ok: true, verification_required: true, email: credentials.email };
        }
        if (!validAuth(credentials)) throw new Error("auth_unavailable");
        sessionVersion++;
        await store.set(credentials);
        return { ok: true, user: credentials.user };
      }
      if (action === "verify-email") {
        const payload = await apiRequest("auth/verify-email", "POST", {
          email: message.email, code: message.code, installation_id: await installationId()
        });
        if (!validAuth(payload)) throw new Error("auth_unavailable");
        sessionVersion++;
        await store.set(payload);
        return { ok: true, user: payload.user };
      }
      if (action === "resend-verification") {
        const payload = await apiRequest("auth/resend-verification", "POST", {
          email: message.email, password: message.password, installation_id: await installationId()
        });
        return { ok: true, verification_required: payload.verification_required === true };
      }
      if (action === "request-reset" || action === "reset-password") {
        const payload = await apiRequest("auth/" + action, "POST",
          action === "request-reset"
            ? { email: message.email }
            : { email: message.email, code: message.code, new_password: message.new_password });
        return { ok: payload?.ok === true };
      }
      if (action === "logout") {
        const saved = await store.get();
        sessionVersion++;
        await store.clear();
        if (saved) {
          await apiRequest("auth/logout", "POST", {
            refresh_token: saved.refresh_token, installation_id: await installationId()
          });
          await store.clear();
        }
        return { ok: true };
      }
      if (action === "entitlement") return { ok: true, entitlement: await entitlement() };
      if (action === "contribution-access") {
        // Short-lived access only, to the verified extension popup. No refresh token.
        const access = await entitlement();
        if (!access.allowed) return { ok: false, error: "access_denied" };
        const config = await apiRequest("config");
        if (config.upload_enabled !== true) return { ok: false, error: "uploads_disabled" };
        return withAccess(async (saved) => ({ ok: true, access_token: saved.access_token }));
      }
      if (action === "sessions" || action === "activate" || action === "revoke") {
        const saved = await current();
        const endpoint = action === "sessions" ? "auth/sessions" : action === "activate" ? "auth/activate" : "auth/sessions/revoke";
        const body = action === "revoke" ? { session_id: message.session_id } : {};
        const data = await apiRequest(endpoint, action === "sessions" ? "GET" : "POST", action === "sessions" ? null : body, saved.access_token);
        if (action === "revoke" && Number.isInteger(message.session_id)) {
          // The server owns revocation; the client never assumes an unrelated device is revoked.
        }
        return { ok: true, ...data };
      }
      return { ok: false, error: "invalid_request" };
    } catch (error) {
      const safe = new Set(["invalid_credentials", "account_disabled", "account_unavailable", "weak_password", "rate_limited", "invalid_session", "invalid_request", "email_unverified", "email_unavailable", "invalid_code", "access_denied", "uploads_disabled"]);
      return { ok: false, error: safe.has(error?.message) ? error.message : "auth_unavailable" };
    }
  }
  return { perform, installationId, withAccess, withEntitledAccess, entitlement };
}
