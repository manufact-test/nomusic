// Extension-origin presentation only. Never use these values to authorize audio.
const prefix = "celikom-popup-display-v1:";
export function readDisplay(key) {
  try {
    const value = JSON.parse(globalThis.localStorage?.getItem(prefix + key) || "null");
    const age = Date.now() - value?.at;
    return Number.isFinite(age) && age >= 0 && age < 86400000 ? value.data : null;
  } catch (_) { return null; }
}
export function writeDisplay(key, data) {
  try { globalThis.localStorage?.setItem(prefix + key, JSON.stringify({ at: Date.now(), data })); } catch (_) {}
}
export function clearDisplay(key) {
  try { globalThis.localStorage?.removeItem(prefix + key); } catch (_) {}
}
const animations = new WeakMap();
export function stableText(node, value, animate = true) {
  if (!node || node.textContent === value) return;
  animations.get(node)?.cancel();
  node.textContent = value;
  if (animate && value && typeof node.animate === "function" && !globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
    animations.set(node, node.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 160, easing: "ease-out" }));
  }
}
