import { createReadRecovery } from "../shared/read-recovery.js";
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
  const previewKey = "celikom-entitlement-display-v1";
  let displayPreview = null;
  const networkHistory = [];
  const pendingReads = new Map();
  const recovery = createReadRecovery();
  let transportEpoch = 0;

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

  function apiRequest(path, method = "GET", data = null, access = "") {
    // Share only concurrent read checks; never cache authority or replay writes.
    // Session generation and token prevent a login/logout/refresh crossing callers.
    const key = method === "GET" && ["config", "auth/me", "entitlement"].includes(path)
      ? `${transportEpoch}:${sessionVersion}:${path}:${access}` : null;
    if (key === null) return sendRequest(path, method, data, access);
    if (pendingReads.has(key)) return pendingReads.get(key);
    const pending = sendRequest(path, method, data, access).finally(() => {
      if (pendingReads.get(key) === pending) pendingReads.delete(key);
    });
    pendingReads.set(key, pending);
    return pending;
  }

  async function sendRequest(path, method, data, access) {
    try { return await recovery.run(signal => apiRequestOnce(path, method, data, access, signal), method); }
    catch (error) { if (error?.message === "network_changed") throw new Error("auth_network_error");
      if (error?.message === "request_timeout") throw new Error("auth_timeout"); throw error; }
  }

  function resetTransport() {
    transportEpoch++;
    pendingReads.clear();
    recovery.reset();
  }

  async function apiRequestOnce(path, method, data, access, signal) {
    const limit = path.startsWith("support") ? 65536 : 16384;
    const started = Date.now(); let httpStatus = null; let outcome = "ok";
    try {
      const response = await request((await origin()) + "/api/v1/" + path, {
        method, credentials: "omit", redirect: "error", cache: "no-store", signal,
        headers: { ...(data ? { "Content-Type": "application/json" } : {}), ...(access ? { Authorization: "Bearer " + access } : {}) },
        body: data ? JSON.stringify(data) : undefined
      });
      httpStatus = response.status;
      if ([502,503,504].includes(httpStatus)) {
        try { await response.body?.cancel(); } catch (_) { /* response is unusable */ }
        throw new Error("auth_unavailable");
      }
      if (!response.headers.get("content-type")?.startsWith("application/json"))
        throw new Error([401,403,429].includes(response.status) ? "auth_route_blocked" : "auth_unavailable");
      if (Number(response.headers.get("content-length")) > limit) throw new Error("auth_unavailable");
      // Enforce the byte limit while streaming, including chunked responses
      // without Content-Length; never buffer an unlimited auth response.
      if (!response.body) throw new Error("auth_unavailable");
      const reader = response.body.getReader();
      const chunks = []; let size = 0;
      try {
        for (;;) {
          const { value, done } = await reader.read(); if (done) break;
          size += value.byteLength;
          if (size > limit) throw new Error("auth_unavailable");
          chunks.push(value);
        }
      } finally { await reader.cancel(); }
      const bytes = new Uint8Array(size); let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      const result = JSON.parse(new TextDecoder().decode(bytes));
      if (!response.ok) {
        const safe = new Set(["auth_timeout", "auth_network_error", "auth_route_blocked", "invalid_credentials", "account_disabled", "account_unavailable", "weak_password", "rate_limited", "invalid_session", "invalid_request", "email_unverified", "email_unavailable", "invalid_code", "access_denied", "uploads_disabled", "invalid_referral_code", "referrals_disabled", "invalid_promo", "promo_unavailable", "promo_payment_pending", "promo_lifetime_active"]);
        throw new Error(safe.has(result?.error) ? result.error : "auth_unavailable");
      }
      return result;
    } catch (error) {
      outcome = signal.reason === "network_changed" ? "auth_network_error" : signal.aborted || error?.name === "AbortError" ? "auth_timeout" : error instanceof TypeError ? "auth_network_error" : error?.message || "auth_unavailable";
      throw Object.assign(new Error(outcome), { retryable: signal.reason !== "network_changed"
        && ([502,503,504].includes(httpStatus) || outcome === "auth_network_error" || outcome === "auth_timeout") });
    } finally {
      networkHistory.push({ endpoint: path.split("?")[0], method, httpStatus, result: signal.reason === "network_changed" ? "request_cancelled" : ["ok", "auth_timeout", "auth_network_error", "auth_route_blocked"].includes(outcome) ? outcome : "api_response_error", elapsedMs: Date.now() - started, at: Date.now() });
      if (networkHistory.length > 8) networkHistory.shift();
    }
  }

  async function isAvailable() {
    const response = await apiRequest("config");
    return response?.features?.auth === true;
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
    const snapshot = await withAccess(async (saved) => {
      const response = activate
        ? (await apiRequest("auth/activate", "POST", {}, saved.access_token)).entitlement
        : await apiRequest("entitlement", "GET", null, saved.access_token);
      if (!validEntitlement(response)) throw new Error("auth_unavailable");
      return { userId: saved.user.id, access: response, checkedAt: Date.now() };
    });
    displayPreview = snapshot;
    try { await api.storage.session?.set({ [previewKey]: snapshot }); } catch (_) {}
    return snapshot.access;
  }

  async function perform(action, message = {}) {
    if (action === "access-preview") {
      const saved = await store.get();
      let preview = displayPreview;
      try { preview = (await api.storage.session?.get(previewKey))?.[previewKey] || preview; } catch (_) {}
      return { ok: true, entitlement: saved?.user?.id === preview?.userId &&
        validEntitlement(preview?.access) && Date.now() - preview.checkedAt < 86400000 ? preview.access : null };
    }
    if (action === "installation") return { ok: true, installation_id: await installationId() };
    if (action === "status") {
      const saved = await store.get();
      let available;
      try { available = await isAvailable(); }
      catch (error) { return { ok: true, available: true, signedIn: false, localSession: Boolean(saved?.user?.email), ...(saved?.user ? { user: saved.user } : {}), error: error?.message || "auth_unavailable" }; }
      if (!available) {
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
    if (action === "support-contact") {
      try { const config = await apiRequest("config"); return { ok: true, email: config.support_email || "" }; } catch (_) { return { ok: false }; }
    }
    if (action === "account-preview") {
      // Presence only; never authority to start a trial, resolve or play audio.
      const saved = await store.get();
      return { ok: true, localSession: Boolean(saved?.refresh_token && saved?.user?.email) };
    }
    try {
      if (action !== "contribution-access" && action !== "track-status" && !await isAvailable()) return { ok: false, error: "auth_disabled" };
      if (action === "support-send" || action === "support-list" || action === "support-thread") {
        if (action === "support-send" && (typeof message.message !== "string" || message.message.length > 3000 || typeof message.request_key !== "string" || !/^[a-f0-9-]{36}$/.test(message.request_key))) return { ok: false, error: "invalid_request" };
        if (action === "support-thread" && !/^[1-9][0-9]{0,17}$/.test(String(message.ticket_id))) return { ok: false, error: "invalid_request" };
        const kind=message.kind??"general";
        if(action==="support-send"&&(!["general","song"].includes(kind)|| (kind==="song"&&(!message.report||typeof message.report!=="object"||JSON.stringify(message.report).length>12000))))return {ok:false,error:"invalid_request"};
        const path = action === "support-thread" ? "support/" + message.ticket_id + "?message_page=" + (Number.isSafeInteger(message.message_page) && message.message_page > 0 && message.message_page <= 100000 ? message.message_page : 1) : action === "support-list" ? "support?page=" + (Number.isSafeInteger(message.page) && message.page > 0 && message.page <= 100000 ? message.page : 1) : "support";
        const data = await withAccess((saved) => apiRequest(path, action === "support-send" ? "POST" : "GET", action === "support-send" ? { message: message.message, request_key: message.request_key, kind, ...(kind==="song"?{report:message.report}:{}) } : null, saved.access_token));
        return { ok: true, ...data };
      }
      if (action === "promo-redeem") {
        if (typeof message.code !== "string" || !/^[A-Za-z0-9_-]{8,64}$/.test(message.code.trim())) return { ok: false, error: "invalid_promo" };
        const result = await withAccess((saved) => apiRequest("promos/redeem", "POST", { code: message.code.trim() }, saved.access_token));
        if (!validEntitlement(result.entitlement)) throw new Error("auth_unavailable");
        await entitlement();
        return { ok: true, ...result };
      }
      if (action === "referral-settings") {
        const config = await apiRequest("config");
        return { ok: true, enabled: config.features?.referrals === true };
      }
      if (action === "benefits" || action === "referral-code") {
        return await withAccess(async (saved) => {
          const config = await apiRequest("config");
          const available = config.features?.referrals === true;
          if (action === "referral-code" && !available) return { ok: false, error: "referrals_disabled" };
          let referrals = null;
          if (available) {
            referrals = await apiRequest(action === "referral-code" ? "referrals/code" : "referrals",
              action === "referral-code" ? "POST" : "GET", action === "referral-code" ? {} : null, saved.access_token);
            if (!(referrals.code === null || /^[A-F0-9]{32}$/.test(referrals.code || "")) ||
                !Number.isSafeInteger(referrals.registered_count) || referrals.registered_count < 0 ||
                referrals.qualification_available !== false || referrals.qualified_count !== 0 ||
                referrals.discount_active !== false || referrals.reward_available !== false || referrals.share_url !== null)
              throw new Error("auth_unavailable");
          }
          let rewards = null;
          if (config.features?.rewards === true) {
            rewards = await apiRequest("rewards", "GET", null, saved.access_token);
            for (const key of ["earned_contributions", "earned_discount_percent", "available_discount_percent", "carried_discount_percent", "monthly_cap_percent"])
              if (!Number.isSafeInteger(rewards[key]) || rewards[key] < 0) throw new Error("auth_unavailable");
            if (rewards.available_discount_percent > 100 || rewards.monthly_cap_percent > 100 ||
                rewards.expiry_starts !== "payment" || rewards.application_available !== false || rewards.discount_active !== false ||
                !(rewards.next_available_from === null || /^\d{4}-\d{2}-\d{2}$/.test(rewards.next_available_from))) throw new Error("auth_unavailable");
          }
          return { ok: true, referrals_available: available, referrals, rewards_available: rewards !== null, rewards };
        });
      }
      if (action === "track-status") {
        if (typeof message.track_id !== "string" || !/^[1-9]\d{0,23}$/.test(message.track_id)) {
          return { ok: false, error: "invalid_request" };
        }
        return await withAccess(async (saved) => {
          const result = await apiRequest("tracks/version-status?service=yandex&track_id=" + encodeURIComponent(message.track_id), "GET", null, saved.access_token);
          if (!["none", "pending", "approved"].includes(result?.status)) throw new Error("auth_unavailable");
          return { ok: true, status: result.status };
        });
      }
      if (action === "login" || action === "register") {
        if (typeof message.email !== "string" || typeof message.password !== "string" ||
            message.email.length > 254 || message.password.length > 128) return { ok: false, error: "invalid_request" };
        let referral = "";
        if (action === "register" && message.referral_code) {
          if (typeof message.referral_code !== "string" || !/^[A-F0-9]{32}$/.test(message.referral_code))
            return { ok: false, error: "invalid_referral_code" };
          if ((await apiRequest("config")).features?.referrals !== true) return { ok: false, error: "referrals_disabled" };
          referral = message.referral_code;
        }
        const credentials = await apiRequest("auth/" + action, "POST", {
          email: message.email, password: message.password, installation_id: await installationId(),
          ...(referral ? { referral_code: referral } : {})
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
        displayPreview = null;
        try { await api.storage.session?.remove(previewKey); } catch (_) {}
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
        return await withAccess(async (saved) => {
          const [access, config] = await Promise.all([
            apiRequest("entitlement", "GET", null, saved.access_token),
            apiRequest("config")
          ]);
          if (config.features?.auth !== true) return { ok: false, error: "auth_disabled" };
          if (!validEntitlement(access)) throw new Error("auth_unavailable");
          if (!access.allowed) return { ok: false, error: "access_denied" };
          if (config.upload_enabled !== true) return { ok: false, error: "uploads_disabled" };
          return { ok: true, access_token: saved.access_token };
        });
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
      const safe = new Set(["auth_timeout", "auth_network_error", "auth_route_blocked", "invalid_credentials", "account_disabled", "account_unavailable", "weak_password", "rate_limited", "invalid_session", "invalid_request", "email_unverified", "email_unavailable", "invalid_code", "access_denied", "uploads_disabled", "invalid_referral_code", "referrals_disabled", "invalid_promo", "promo_unavailable", "promo_payment_pending", "promo_lifetime_active"]);
      return { ok: false, error: safe.has(error?.message) ? error.message : "auth_unavailable" };
    }
  }
  return { perform, installationId, withAccess, withEntitledAccess, entitlement, resetTransport, networkDiagnostics: () => networkHistory.map(item => ({ ...item })) };
}
