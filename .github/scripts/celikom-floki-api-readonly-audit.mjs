import { pathToFileURL } from "node:url";

const origin = "https://api.celikom.com";
const timeoutMs = 12000;

async function readLimited(response, maxBytes) {
  if (!response.body) return "";
  const reader = response.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > maxBytes) throw new Error("response_too_large");
      chunks.push(Buffer.from(value));
    }
  } finally {
    await reader.cancel().catch(() => {});
  }
  return Buffer.concat(chunks, size).toString("utf8");
}

async function request(name, path, inspect = null) {
  const started = Date.now();
  let response;
  try {
    response = await fetch(origin + path, {
      method: "GET",
      redirect: "manual",
      cache: "no-store",
      headers: { accept: "application/json, text/html;q=0.9" },
      signal: AbortSignal.timeout(timeoutMs)
    });
    const status = response.status;
    const contentType = response.headers.get("content-type") || "";
    const result = {
      endpoint: name,
      status,
      elapsedMs: Date.now() - started,
      ok: false
    };
    if (inspect === "json") {
      if (status !== 200 || !contentType.toLowerCase().includes("application/json")) {
        await response.body?.cancel();
        return result;
      }
      const body = JSON.parse(await readLimited(response, 16384));
      result.ok = body !== null && typeof body === "object" && !Array.isArray(body);
      if (name === "health") {
        result.ok = result.ok && body.status === "ok" && body.service === "celikom-api";
      }
      if (name === "config" && body.features && typeof body.features.replacements === "boolean") {
        result.replacementsEnabled = body.features.replacements;
      }
      return result;
    }
    if (inspect === "admin-login") {
      if (status !== 200 || !contentType.toLowerCase().includes("text/html")) {
        await response.body?.cancel();
        return result;
      }
      const html = await readLimited(response, 131072);
      const form = /<form[^>]+action=["']\/admin\/login["'][^>]*>/i.test(html);
      const csrf = /name=["']csrf["']/i.test(html);
      const login = /name=["']login["']/i.test(html);
      const password = /name=["']password["'][^>]*type=["']password["']|type=["']password["'][^>]*name=["']password["']/i.test(html);
      const cookie = (response.headers.get("set-cookie") || "").includes("__Host-celikom_login=");
      result.formPresent = form;
      result.csrfFieldPresent = csrf;
      result.loginFieldPresent = login;
      result.passwordFieldPresent = password;
      result.loginCookieIssued = cookie;
      result.ok = form && csrf && login && password && cookie;
      return result;
    }
    if (inspect === "admin-redirect") {
      const location = response.headers.get("location") || "";
      let pathname = "";
      try { pathname = new URL(location, origin).pathname; } catch {}
      result.redirectPath = pathname || "none";
      result.ok = status === 303 && pathname === "/admin/login";
      await response.body?.cancel();
      return result;
    }
    if (inspect === "unauthorized") {
      let code = "";
      if (contentType.toLowerCase().includes("application/json")) {
        try {
          const body = JSON.parse(await readLimited(response, 8192));
          code = typeof body.error === "string" ? body.error : "";
        } catch {}
      } else await response.body?.cancel();
      result.errorCode = code || "not_json";
      result.ok = status === 401;
      return result;
    }
    await response.body?.cancel();
    return result;
  } catch (error) {
    await response?.body?.cancel().catch(() => {});
    return {
      endpoint: name,
      status: response?.status ?? 0,
      elapsedMs: Date.now() - started,
      ok: false,
      reason: error?.name === "TimeoutError" ? "timeout" :
        error?.message === "response_too_large" ? "response_too_large" :
        "transport_or_invalid_response"
    };
  }
}

export async function audit() {
  const checks = [];
  checks.push(await request("floki_health", "/api/v1/health", "json"));
  checks.push(await request("floki_config", "/api/v1/config", "json"));
  checks.push(await request("owner_admin_login_page", "/admin/login", "admin-login"));
  checks.push(await request("owner_admin_root_redirect", "/admin", "admin-redirect"));
  checks.push(await request("anonymous_auth_me", "/api/v1/auth/me", "unauthorized"));
  checks.push(await request("anonymous_resolve", "/api/v1/resolve?service=yandex&track_id=144530503", "unauthorized"));
  const report = {
    origin,
    generatedAt: new Date().toISOString(),
    credentialsUsed: false,
    secretsRead: false,
    checks,
    ok: checks.every(check => check.ok)
  };
  console.log(JSON.stringify(report, null, 2));
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const result = await audit();
  if (!result.ok) process.exitCode = 1;
}
