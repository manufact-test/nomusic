(function (root) {
  "use strict";
  class NativeSession {
    constructor({ port, resource, environment = root }) {
      this.port = port; this.resource = resource; this.environment = environment;
      this.assets = new Map(); this.enabled = false; this.generation = -1; this.epoch = 0;
      this.active = null; this.pending = null; this.lastError = null;
      resource.setEnabled(false);
    }
    owned(binding = this.port.binding()) {
      const url = binding?.audio?.currentSrc || binding?.audio?.src || "";
      return Array.from(this.assets.values()).find(item => url === item.url || url.startsWith(item.url + "#")) || null;
    }
    inspect() {
      const binding = this.port.binding(), audio = binding?.audio, owned = this.owned(binding);
      return { ...this.port.inspect(), enabled: this.enabled, generation: this.generation,
        activeTrackId: owned?.trackId === binding?.id ? binding.id : null,
        sourceMismatch: Boolean(owned && owned.trackId !== binding?.id), pending: Boolean(this.pending), lastError: this.lastError,
        position: Number(audio?.currentTime) || 0, paused: audio?.paused !== false,
        readyState: audio?.readyState || 0, ended: audio?.ended === true };
    }
    async configure(enabled, generation) {
      if (!Number.isSafeInteger(generation) || generation < this.generation) throw Error("native_generation_invalid");
      const epoch = ++this.epoch;
      this.confirmAbort?.abort();
      this.enabled = false; this.resource.setEnabled(false); this.port.cancel();
      for (const id of this.assets.keys()) this.resource.unregister(id);
      await this.pending?.catch(() => {});
      const binding = this.port.binding();
      if (this.owned(binding)) {
        try {
          await this.port.reload(binding.id);
          await this.confirmSource(binding.audio, null, new AbortController().signal);
        }
        catch (error) { this.lastError = "native_original_restore_failed"; throw error; }
        if (this.owned()) { this.lastError = "native_original_restore_failed"; throw Error(this.lastError); }
      }
      for (const item of this.assets.values()) this.environment.URL.revokeObjectURL(item.url);
      this.assets.clear(); this.active = null;
      if (epoch !== this.epoch) return;
      this.generation = generation; this.enabled = enabled === true; this.lastError = null;
      this.resource.setEnabled(this.enabled);
    }
    publish(message) {
      if (!this.enabled || message?.generation !== this.generation || !/^\d{1,24}$/.test(message?.trackId)
        || !message.blob || message.blob.type !== "audio/mpeg" || message.blob.size < 1024 || message.blob.size > 31457280
        || !Number.isFinite(message.durationMs) || message.durationMs <= 0
        || !Number.isFinite(message.expiresAt) || message.expiresAt <= Date.now() + 1000
        || message.expiresAt > Date.now() + 300000 || this.assets.size >= 2) throw Error("native_publish_rejected");
      if (this.assets.has(message.trackId)) throw Error("native_asset_already_present");
      this.assets.set(message.trackId, { ...message, blob: undefined, url: this.environment.URL.createObjectURL(message.blob) });
      /* A prepared file is not registered with Yandex until fresh admission. */
      return { prepared: true };
    }
    activate(trackId, generation) {
      if (this.pending) return Promise.reject(Error("native_switch_busy"));
      const record = this.assets.get(trackId), binding = this.port.binding(), epoch = this.epoch;
      if (!this.enabled || generation !== this.generation || !record || record.expiresAt <= Date.now() + 1000
        || binding?.id !== trackId || Math.abs(Number(binding.entity.data.meta.durationMs) - record.durationMs) > 1500) {
        return Promise.reject(Error("native_switch_not_admitted"));
      }
      const current = () => this.enabled && epoch === this.epoch && generation === this.generation;
      const confirmation = new AbortController(); this.confirmAbort = confirmation;
      this.resource.register(trackId, record.url, { expiresAt: record.expiresAt });
      this.pending = this.port.reload(trackId, { isCurrent: current }).then(async () => {
        await this.confirmSource(binding.audio, record, confirmation.signal);
        if (!current() || this.owned()?.trackId !== trackId) throw Error("native_source_not_applied");
        this.active = trackId; this.lastError = null;
        return { active: true, trackId };
      }).catch(error => {
        this.resource.unregister(trackId); this.lastError = String(error.message || "native_switch_failed");
        throw error;
      }).finally(() => { this.pending = null; if (this.confirmAbort === confirmation) this.confirmAbort = null; });
      return this.pending;
    }
    confirmSource(audio, record, signal) {
      return new Promise((resolve, reject) => {
        let timer;
        const finish = error => {
          this.environment.clearTimeout(timer);
          for (const event of ["loadedmetadata", "loadeddata", "canplay"]) audio.removeEventListener(event, check);
          audio.removeEventListener("error", failed); signal.removeEventListener("abort", cancelled);
          if (error) reject(error); else resolve();
        };
        const check = () => { if ((this.owned({ audio }) || null) === record && audio.readyState >= 1) finish(); };
        const failed = () => finish(Error("native_media_decode_error"));
        const cancelled = () => finish(Error("native_switch_cancelled"));
        for (const event of ["loadedmetadata", "loadeddata", "canplay"]) audio.addEventListener(event, check);
        audio.addEventListener("error", failed); signal.addEventListener("abort", cancelled, { once: true });
        timer = this.environment.setTimeout(() => finish(Error("native_source_confirmation_timeout")), 8000);
        if (signal.aborted) cancelled(); else check();
      });
    }
    async revoke(message) {
      if (message.generation !== this.generation) return;
      if (message.trackId && !this.assets.has(message.trackId)) return;
      /* Restore before revoking any URL the native audio may still reference. */
      return this.configure(false, this.generation);
    }
  }
  Object.defineProperty(root, "__CELIKOM_NATIVE_SESSION__", { value: { NativeSession }, configurable: true });
})(globalThis);
