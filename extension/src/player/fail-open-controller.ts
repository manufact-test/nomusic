(function registerFailOpenController(root) {
  "use strict";
  const KEY = "__CELIKOM_FAIL_OPEN_V1__";
  if (root[KEY]) return;
  class FailOpenController {
    constructor(bridge, log) { this.bridge = bridge; this.log = log; }
    async restore(operation, reason) {
      // Silence and dispose replacement synchronously, before any bridge await.
      try { operation?.player?.destroy(); } catch (error) { this.log(`replacement cleanup: ${error.message}`); }
      if (!operation) return;
      try {
        await this.bridge.request("GUARD_RELEASE", { token: operation.token, reason });
      } catch (error) {
        this.log(`restore acknowledgement missing: ${error.message}`);
        // Token-scoped immediate signal is safe even after another generation starts.
        this.bridge.post("RELEASE_NOW", { token: operation.token, reason });
      }
    }
  }
  Object.defineProperty(root, KEY, { value: Object.freeze({ FailOpenController }), writable: false });
})(globalThis);
