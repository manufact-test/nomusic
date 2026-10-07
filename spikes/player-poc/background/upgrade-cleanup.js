(function stopPreviousCelikomControllers() {
  "use strict";

  const controllerKeys = [
    "__CELIKOM_POC_CONTENT_CONTROLLER_V1__",
    "__CELIKOM_POC_CONTENT_CONTROLLER_V2__",
    "__CELIKOM_POC_CONTENT_CONTROLLER_V3__",
    "__CELIKOM_POC_CONTENT_CONTROLLER_V4__"
  ];

  for (const key of controllerKeys) {
    const runtime = globalThis[key];
    try {
      runtime?.controller?.shutdown?.();
    } catch (_error) {
      // Upgrade cleanup is best-effort; the new bridge still starts fail-open.
    }
    try {
      delete globalThis[key];
    } catch (_error) {
      // Earlier versions may have installed a non-configurable marker.
    }
  }
})();
