(function (root) {
  "use strict";
  const proto = root.__CELIKOM_YANDEX_ADAPTER_V1__?.YandexMusicAdapter?.prototype;
  if (!proto || proto.__celikomNativeMetadata) return;
  const original = proto.trackState, port = new root.__CELIKOM_NATIVE_ENGINE_PORT__.EnginePort();
  proto.trackState = function (master) {
    const result = Reflect.apply(original, this, [master]), binding = port.binding();
    if (!binding || binding.audio !== master) return result;
    const durationMs = Number(binding.entity.data.meta.durationMs), catalog = this.trackCatalog?.get(binding.id);
    if (!Number.isFinite(durationMs) || durationMs <= 0) return result;
    /* The legacy observer deliberately invalidates unchanged metadata after
       any src change. Here the real native queue proves same-track identity. */
    const metadata = { ...result.metadata, durationMs };
    for (const key of ["title", "artist", "album", "coverUri"]) if (typeof catalog?.[key] === "string") metadata[key] = catalog[key];
    return { ...result, id: binding.id, confidence: 100, ambiguous: false,
      source: "native-engine", evidence: "native-queue", metadata };
  };
  Object.defineProperty(proto, "__celikomNativeMetadata", { value: true });
})(globalThis);
