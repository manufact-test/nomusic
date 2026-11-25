export function apiBuildConfig(raw = "https://api.celikom.com") {
  if (!raw) raw = "https://api.celikom.com";
  const url = new URL(raw);
  const local = url.protocol === "http:" && ["127.0.0.1", "localhost"].includes(url.hostname);
  if ((!local && url.protocol !== "https:") || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("API build URL must be one HTTPS origin (loopback HTTP is dev-only)");
  if (url.hostname === "hostingersite.com" || url.hostname.endsWith(".hostingersite.com")) throw new Error("Legacy Hostinger API is retired for new extension builds");
  return { baseUrl: url.origin };
}

