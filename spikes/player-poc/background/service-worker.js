"use strict";

const DEFAULT_SETTINGS = {
  enabled: true,
  automaticReplacement: true,
  testTrackId: "",
  driftThresholdMs: 350,
  showOverlay: true
};

const SUPPORTED_URLS = [
  "https://music.yandex.ru/*",
  "https://music.yandex.com/*",
  "https://music.yandex.by/*",
  "https://music.yandex.kz/*",
  "http://localhost/*",
  "http://127.0.0.1/*"
];

const MAIN_WORLD_FILES = [
  "src/shared/core.js",
  "src/main-world-bridge.js"
];

const ISOLATED_WORLD_FILES = [
  "src/shared/core.js",
  "src/overlay.js",
  "src/content.js"
];
const UPGRADE_CLEANUP_FILES = ["background/upgrade-cleanup.js"];
const STATUS_MESSAGE = "CELIKOM_GET_STATUS_V4";

const injections = new Map();

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function isSupportedUrl(rawUrl) {
  try {
    const url = new URL(String(rawUrl || ""));
    if (url.protocol === "https:" && ["music.yandex.ru", "music.yandex.com", "music.yandex.by", "music.yandex.kz"].includes(url.hostname)) {
      return true;
    }
    return url.protocol === "http:" && ["localhost", "127.0.0.1"].includes(url.hostname);
  } catch (_error) {
    return false;
  }
}

async function readStatus(tabId) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, { type: STATUS_MESSAGE });
    return response?.ok ? response : null;
  } catch (_error) {
    return null;
  }
}

async function waitForStatus(tabId) {
  for (let attempt = 0; attempt < 12; attempt += 1) {
    const response = await readStatus(tabId);
    if (response) return response;
    await delay(75);
  }
  return null;
}

async function injectController(tabId) {
  const existing = await readStatus(tabId);
  if (existing) return { ...existing, injected: false };

  const tab = await chrome.tabs.get(tabId);
  if (!isSupportedUrl(tab.url)) {
    return { ok: false, error: "unsupported-page" };
  }

  await chrome.scripting.executeScript({
    target: { tabId },
    files: UPGRADE_CLEANUP_FILES,
    world: "ISOLATED"
  });
  await delay(100);
  await chrome.scripting.executeScript({
    target: { tabId },
    files: MAIN_WORLD_FILES,
    world: "MAIN"
  });
  await chrome.scripting.executeScript({
    target: { tabId },
    files: ISOLATED_WORLD_FILES,
    world: "ISOLATED"
  });

  const response = await waitForStatus(tabId);
  return response ? { ...response, injected: true } : { ok: false, error: "controller-start-timeout" };
}

function ensureController(tabId) {
  if (injections.has(tabId)) return injections.get(tabId);
  const pending = injectController(tabId)
    .catch((error) => ({ ok: false, error: String(error?.message || error) }))
    .finally(() => injections.delete(tabId));
  injections.set(tabId, pending);
  return pending;
}

async function injectIntoOpenSupportedTabs() {
  const tabs = await chrome.tabs.query({ url: SUPPORTED_URLS });
  await Promise.allSettled(tabs.filter((tab) => tab.id).map((tab) => ensureController(tab.id)));
}

chrome.runtime.onInstalled.addListener(() => {
  (async () => {
    const current = await chrome.storage.local.get(DEFAULT_SETTINGS);
    await chrome.storage.local.set({ ...DEFAULT_SETTINGS, ...current });
    await chrome.action.setBadgeBackgroundColor({ color: "#11151B" });
    await chrome.action.setBadgeText({ text: "POC" });
    await injectIntoOpenSupportedTabs();
  })().catch(() => {});
});

chrome.runtime.onStartup.addListener(() => {
  injectIntoOpenSupportedTabs().catch(() => {});
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "CELIKOM_ENSURE_INJECTED" || !Number.isInteger(message.tabId)) return false;
  ensureController(message.tabId).then(sendResponse);
  return true;
});

chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "emergency-restore") return;
  const tabs = await chrome.tabs.query({ url: SUPPORTED_URLS });
  await Promise.allSettled(tabs.map((tab) => {
    if (!tab.id) return Promise.resolve();
    return chrome.tabs.sendMessage(tab.id, { type: "CELIKOM_EMERGENCY_RESTORE" });
  }));
});
