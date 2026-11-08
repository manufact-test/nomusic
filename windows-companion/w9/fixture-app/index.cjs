"use strict";
/* W9_GENERATED_TEST_APP_ONLY. Never copied from or loaded into Yandex Music. */
const { app, BrowserWindow } = require("electron");
/* W9_SYNTHETIC_HOOK_SLOT */
app.whenReady().then(async () => {
  let exitCode = 0, window;
  try {
    window = new BrowserWindow({
      show: false,
      webPreferences: { sandbox: true, contextIsolation: true,
        nodeIntegration: false, webSecurity: true }
    });
    await window.loadURL("data:text/html;charset=utf-8," + encodeURIComponent("<title>W9 original synthetic</title><audio></audio>"));
    const state = await window.webContents.executeJavaScript(
      "({ title: document.title, elements: document.querySelectorAll('audio,video').length })"
    );
    const injected = global.__CELIKOM_W9_SYNTHETIC_HOOK__ === "COPY_ONLY";
    if (state.elements !== 1 || state.title !== "W9 original synthetic") throw Error("INVALID_SYNTHETIC_RENDERER");
    process.stdout.write("W9_SYNTHETIC_BOOT=" + JSON.stringify({
      scope: "ISOLATED_ASAR_FIXTURE_ONLY",
      mode: injected ? "PATCHED_COPY" : "ORIGINAL",
      hookMarkerPresent: injected,
      nativeMediaElements: state.elements,
      didStartActualElectron: true,
      officialYandexUsed: false,
      officialExeModified: false
    }) + "\n");
  } catch (error) {
    exitCode = 1;
    process.stderr.write("W9_SYNTHETIC_BOOT_ERROR\n");
  } finally {
    window?.destroy();
    app.exit(exitCode);
  }
});
