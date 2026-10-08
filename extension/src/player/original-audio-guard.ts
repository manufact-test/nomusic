(function registerOriginalAudioGuard(root) {
  "use strict";
  const KEY = "__CELIKOM_ORIGINAL_GUARD_V1__";
  if (root[KEY]) return;

  function descriptorFor(element, property) {
    for (let owner = element; owner; owner = Object.getPrototypeOf(owner)) {
      const descriptor = Object.getOwnPropertyDescriptor(owner, property);
      if (descriptor) return descriptor;
    }
    return null;
  }

  class OriginalAudioGuard {
    constructor(onIntent = () => {}) {
      this.current = null;
      this.onIntent = onIntent;
    }

    engage(element, mediaId, token) {
      if (this.current?.token === token && this.current.element === element) return this.state();
      if (this.current) throw new Error("Original guard is already leased");
      const descriptors = {};
      const own = {};
      for (const property of ["volume", "muted"]) {
        descriptors[property] = descriptorFor(element, property);
        own[property] = Object.getOwnPropertyDescriptor(element, property);
        if (!descriptors[property]?.get || !descriptors[property]?.set || own[property]?.configurable === false) {
          throw new Error(`Original ${property} cannot be guarded safely`);
        }
      }
      const read = (property) => descriptors[property].get.call(element);
      const write = (property, value) => descriptors[property].set.call(element, value);
      const lease = { element, mediaId, token, descriptors, own, read, write, volume: read("volume"), muted: read("muted") };
      this.current = lease;
      lease.listener = () => {
        if (this.current !== lease) return;
        // Prototype writes can bypass own setters. Capture volume and an attempted
        // unmute, but never interpret our forced physical mute as user intent.
        lease.volume = read("volume");
        if (!read("muted")) { lease.muted = false; write("muted", true); }
        this.onIntent(this.state());
      };
      try {
        for (const property of ["volume", "muted"]) {
          Object.defineProperty(element, property, {
            configurable: true,
            enumerable: descriptors[property].enumerable,
            get: () => lease[property],
            set: (value) => {
              // Let the native volume setter validate its range/type first.
              write(property, property === "muted" ? true : value);
              lease[property] = property === "muted" ? Boolean(value) : read(property);
              this.onIntent(this.state());
            }
          });
        }
        element.addEventListener("volumechange", lease.listener);
        write("muted", true);
        if (!read("muted")) throw new Error("Original mute was not applied");
        return this.state();
      } catch (error) {
        this.release(token);
        throw error;
      }
    }

    state() {
      const lease = this.current;
      return lease ? { active: true, mediaId: lease.mediaId, token: lease.token, volume: lease.volume, muted: lease.muted } : { active: false };
    }

    release(token = null) {
      const lease = this.current;
      if (!lease || (token && token !== lease.token)) return { released: false, ...this.state() };
      this.current = null;
      lease.element.removeEventListener("volumechange", lease.listener);
      // Restore the latest logical intent, not the initial values. Each cleanup
      // is independent so a failed descriptor restoration cannot keep audio muted.
      const errors = [];
      for (const property of ["volume", "muted"]) {
        try {
          if (lease.own[property]) Object.defineProperty(lease.element, property, lease.own[property]);
          else delete lease.element[property];
        } catch (error) { errors.push(String(error.message)); }
        try { lease.write(property, lease[property]); } catch (error) { errors.push(String(error.message)); }
      }
      return { released: true, token: lease.token, volume: lease.volume, muted: lease.muted, errors };
    }
  }

  Object.defineProperty(root, KEY, { value: Object.freeze({ OriginalAudioGuard }), writable: false });
})(globalThis);
