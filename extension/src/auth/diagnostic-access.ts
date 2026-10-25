// Support export rights only; this does not grant server/admin/audio authority.
const allowed = new Set(["18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572", "50bc7e488885f21b0af751f8e2ed3bc622d3bc097c6541817c9ef742cdf7777e"]);
export async function diagnosticsIdentity(user, digest = async text => {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(bytes)].map(x => x.toString(16).padStart(2, "0")).join("");
}) {
  if (!Number.isSafeInteger(user?.id) || user.id < 1 || user.status !== "active" || typeof user.email !== "string") return false;
  return allowed.has(await digest(user.email.trim().toLowerCase()));
}
export function redactDiagnostics(value) {
  if (Array.isArray(value)) return value.map(redactDiagnostics);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k,v]) => [k,
    /password|authorization|cookie|refresh.?token|access.?token|secret/i.test(k) ? "[REDACTED]" : redactDiagnostics(v)]));
  if (typeof value === "string") return value.replace(/Bearer\s+[A-Za-z0-9._~+\/=-]+/gi,"Bearer [REDACTED]").replace(/https?:\/\/[^\s"<>]+/g, raw => {try {const u=new URL(raw);u.search="";u.hash="";u.username="";u.password="";return u.toString();}catch{return "[URL]";}});
  return value;
}

export function publicPlaybackState(s) {
  const out = {};
  for (const key of ["enabled","phase","version","settings","startupError","accessError","manualBypass","replacementError","availability","suspended","recovering","track","bridge"]) if (key in s) out[key]=s[key];
  if (s.player) out["player"]={paused:s.player.paused};
  if (s.connection) out["connection"]={controllerPresent:s.connection.controllerPresent,recovered:s.connection.recovered,error:s.connection.error};
  if (s.preparation) out["preparation"]={stage:s.preparation.stage,elapsedMs:s.preparation.elapsedMs};
  return out;
}
