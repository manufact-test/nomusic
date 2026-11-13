/**
 * CELIKOM Windows W6 — conservative, read-only compatibility decision.
 *
 * This module NEVER returns permission to patch official Yandex Music.
 * A matching installed archive only establishes identity, NOT live hookability.
 */
const target = Object.freeze({
  windowsBuild: 19045,
  architecture: "X64",
  executableVersion: "5.126.1.0",
  packageVersion: "5.126.1",
  asarSha256: "5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215"
});

export function assessOfficialCompatibility(observation) {
  const errors = [];
  if (!observation || typeof observation !== "object" ||
      Array.isArray(observation)) errors.push("NO_OBSERVATION");
  const o = observation && typeof observation === "object" ? observation : {};
  if (o.osBuild !== target.windowsBuild || o.architecture !== target.architecture)
    errors.push("OS_OR_ARCH_MISMATCH");
  if (o.exeVersion !== target.executableVersion || o.packageVersion !== target.packageVersion)
    errors.push("YANDEX_VERSION_MISMATCH");
  if (o.asarSha256 !== target.asarSha256 || o.asarState !== "OK")
    errors.push("ASAR_IDENTITY_MISMATCH");
  if (o.installed !== true || o.running !== true)
    errors.push("OFFICIAL_APP_NOT_CONFIRMED_RUNNING");
  // Static markers and synthetic tests can NEVER fulfill live renderer proof.
  return Object.freeze({
    identity: errors.length === 0 ? "MATCHING_W3_IDENTITY_ONLY" : "NOT_COMPATIBLE_OR_UNKNOWN",
    canRunReadOnlyProbe: true,
    mayEditOfficialFiles: false,
    mayAttachToLiveRenderer: false,
    nativeSourceCompatibility: "UNPROVEN",
    rollbackOnOwnerMachine: "UNTESTED",
    reasons: errors
  });
}

export const W6_PINNED_OWNER_IDENTITY = target;
