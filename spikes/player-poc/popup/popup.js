(function initPopup() {
  "use strict";

  const DEFAULT_SETTINGS = {
    enabled: true,
    automaticReplacement: true,
    testTrackId: "",
    driftThresholdMs: 350,
    showOverlay: true
  };
  const STATUS_MESSAGE = "CELIKOM_GET_STATUS_V4";

  const elements = {
    form: document.getElementById("settings-form"),
    enabled: document.getElementById("enabled"),
    automatic: document.getElementById("automatic-replacement"),
    testTrackId: document.getElementById("test-track-id"),
    drift: document.getElementById("drift-threshold"),
    driftOutput: document.getElementById("drift-output"),
    showOverlay: document.getElementById("show-overlay"),
    currentTrack: document.getElementById("current-track"),
    trackMeta: document.getElementById("track-meta"),
    phase: document.getElementById("phase"),
    useCurrent: document.getElementById("use-current"),
    restore: document.getElementById("restore"),
    copy: document.getElementById("copy"),
    feedback: document.getElementById("feedback")
  };

  let activeTabId = null;
  let latestStatus = null;

  function t(key, substitutions) {
    return chrome.i18n.getMessage(key, substitutions) || key;
  }

  function localize() {
    document.documentElement.lang = chrome.i18n.getUILanguage().toLowerCase().startsWith("ru") ? "ru" : "en";
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
  }

  function feedback(message, error = false) {
    elements.feedback.textContent = message;
    elements.feedback.style.color = error ? "#ff9999" : "#77f2c4";
  }

  async function getActiveTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    activeTabId = tab?.id || null;
    return tab;
  }

  function sendToActiveTab(message) {
    if (!activeTabId) return Promise.reject(new Error(t("playerUnavailable")));
    return chrome.tabs.sendMessage(activeTabId, message);
  }

  async function getStatusWithRecovery() {
    try {
      const response = await sendToActiveTab({ type: STATUS_MESSAGE });
      if (response?.ok) return response;
    } catch (_error) {
      // A tab opened before installation is repaired by the service worker below.
    }

    const recovered = await chrome.runtime.sendMessage({
      type: "CELIKOM_ENSURE_INJECTED",
      tabId: activeTabId
    });
    if (!recovered?.ok) {
      throw new Error(recovered?.error || t("playerUnavailable"));
    }
    return recovered;
  }

  async function loadSettings() {
    const settings = await chrome.storage.local.get(DEFAULT_SETTINGS);
    elements.enabled.checked = settings.enabled !== false;
    elements.automatic.checked = settings.automaticReplacement !== false;
    elements.testTrackId.value = settings.testTrackId || "";
    elements.drift.value = String(settings.driftThresholdMs || 350);
    elements.driftOutput.textContent = `${elements.drift.value} ms`;
    elements.showOverlay.checked = settings.showOverlay !== false;
  }

  async function loadStatus() {
    try {
      await getActiveTab();
      const response = await getStatusWithRecovery();
      latestStatus = response.status;
      const track = latestStatus.track;
      elements.phase.textContent = latestStatus.phase || "—";
      elements.currentTrack.textContent = track?.id || "—";
      elements.trackMeta.textContent = track?.id
        ? `${track.metadata?.artist || ""}${track.metadata?.artist && track.metadata?.title ? " — " : ""}${track.metadata?.title || ""} · ${track.source || "unknown"} · ${track.confidence || 0}`
        : t("trackNotDetected");
      elements.useCurrent.disabled = !track?.id;
    } catch (_error) {
      latestStatus = null;
      elements.phase.textContent = "OFFLINE";
      elements.currentTrack.textContent = "—";
      elements.trackMeta.textContent = t("openPlayerHint");
      elements.useCurrent.disabled = true;
    }
  }

  async function saveSettings(event) {
    event.preventDefault();
    const rawTrackId = elements.testTrackId.value.trim();
    if (rawTrackId && !/^\d{1,24}$/.test(rawTrackId)) {
      feedback(t("invalidTrackId"), true);
      return;
    }

    const settings = {
      enabled: elements.enabled.checked,
      automaticReplacement: elements.automatic.checked,
      testTrackId: rawTrackId,
      driftThresholdMs: Number(elements.drift.value),
      showOverlay: elements.showOverlay.checked
    };
    await chrome.storage.local.set(settings);
    try {
      await sendToActiveTab({ type: "CELIKOM_RELOAD_SETTINGS" });
    } catch (_error) {
      // Settings remain saved and will be picked up when a supported tab opens.
    }
    feedback(t("saved"));
    await loadStatus();
  }

  elements.form.addEventListener("submit", saveSettings);
  elements.drift.addEventListener("input", () => {
    elements.driftOutput.textContent = `${elements.drift.value} ms`;
  });
  elements.useCurrent.addEventListener("click", () => {
    if (!latestStatus?.track?.id) return;
    elements.testTrackId.value = latestStatus.track.id;
    feedback(t("currentSelected"));
  });
  elements.restore.addEventListener("click", async () => {
    try {
      await sendToActiveTab({ type: "CELIKOM_EMERGENCY_RESTORE" });
      feedback(t("restored"));
      await loadStatus();
    } catch (_error) {
      feedback(t("playerUnavailable"), true);
    }
  });
  elements.copy.addEventListener("click", async () => {
    if (!latestStatus) {
      feedback(t("playerUnavailable"), true);
      return;
    }
    await navigator.clipboard.writeText(JSON.stringify(latestStatus, null, 2));
    feedback(t("copied"));
  });

  localize();
  Promise.all([loadSettings(), loadStatus()]).catch((error) => feedback(error.message, true));
})();
