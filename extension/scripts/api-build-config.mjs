export function apiBuildConfig(raw = "") {
  if (!raw) return { baseUrl: "" };
  const url = new URL(raw);
  const local = url.protocol === "http:" && ["127.0.0.1", "localhost"].includes(url.hostname);
  if ((!local && url.protocol !== "https:") || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("API build URL must be one HTTPS origin (loopback HTTP is dev-only)");
  return { baseUrl: url.origin };
}
