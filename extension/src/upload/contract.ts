import type { ExtensionState } from "../shared/messages.js";

// Only a confident exact Track ID may be submitted. Never accept a typed ID.
export function uploadTargetFromStatus(state: ExtensionState | null) {
  const track = state?.track;
  const durationMs = track?.metadata?.durationMs;
  if (!track?.id || !/^[1-9]\d{0,23}$/.test(track.id) ||
    track.ambiguous !== false || !Number.isFinite(track.confidence) || track.confidence < 100 ||
    !Number.isSafeInteger(durationMs) || !durationMs || durationMs < 1000 || durationMs > 86400000) return null;
  const safe = (value: unknown) => typeof value === "string" ? value.slice(0, 240) : "";
  return { id: track.id, durationMs, artist: safe(track.metadata?.artist),
    title: safe(track.metadata?.title), album: safe(track.metadata?.album) };
}

export function validMp3Selection(file: { name: string; size: number } | null, maxBytes = 31457280): boolean {
  return Boolean(file && file.size >= 1024 && file.size <= maxBytes && /\.mp3$/i.test(file.name));
}

export function privateUploadApiOrigin(raw: unknown): string {
  if (typeof raw !== "string") throw new Error("invalid_upload_origin");
  const url = new URL(raw);
  if ((url.protocol !== "https:" && !(url.protocol === "http:" && url.hostname === "127.0.0.1")) ||
    url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("invalid_upload_origin");
  return url.origin;
}
