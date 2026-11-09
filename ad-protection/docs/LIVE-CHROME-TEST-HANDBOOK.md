# Live Chrome test handbook — observer-only Stage 1

**Prerequisite:** Authorized Yandex Music browser use, especially a genuinely non-Plus test state when available. The ad module is **not active** as a blocker. Never bypass subscriptions, access rules, region controls, or copyrighted streaming protections.

## Install the independent observation extension

1. Get `manufact-test/nomusic` branch `feature/api-range` locally (Git checkout / GitHub ZIP). No change to the regular CELIKOM extension.
2. Open **a clean Chrome profile** with no overlapping blockers. Visit `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select the **`ad-protection/observer/` folder** containing its `manifest.json` — *not* `ad-protection/standalone/`.
3. Open `https://music.yandex.ru/` where your authorized account can normally play music. Reload the tab after installation. The independent extension popup is called *CELIKOM Ad Protection — Observation Lab*.
4. Click extension icon, confirm **Подключено. Режим только для наблюдения.** Record the Chrome version, broad region, Plus/non-Plus status, date/time and route in a private local test note (no login/account identity). If the popup reports no observer, ensure Chrome access to the correct tab and reload.
5. Use **Сбросить** before each trial. Mark **Обычная музыка** in controls, and **Звуковая реклама**, **Видеореклама**, or **Рекламное окно** only at the instant you personally observe the event. Do not mark CSS guesses as real ads.
6. Click **Скачать JSON** to save the limited, local `celikom-observation.json` report. It contains relative seconds and allowlisted labels only. Copy is also available. Data is transient in tab memory. Max 20 manual markers and 80 recent events; longer trials need multiple captures. If `droppedRoots` increases, that observation window is incomplete.

## Optional offline HAR comparison (sensitive local data)

- Browser DevTools Network > Preserve log; capture events in authorized baseline runs. **Raw HAR can contain cookies, bearer tokens, signed URLs, request bodies, account IDs and media links. NEVER attach raw HAR to GitHub, ChatGPT or a public ticket.** Store temporarily on a trusted local machine; securely remove when finished. An ordinary JSON export from the observer is not a HAR.
- `cd ad-protection`, then:
  - `node analysis/summarize-har.mjs "LOCAL.har" --mark=120`
  - `node analysis/align-observation.mjs "celikom-observation.json" "LOCAL.har" --offset=-30 --radius=12`
  - `node analysis/compare-har.mjs --ad="adA.har@120" --ad="adB.har@90" --normal="normalA.har@100" --normal="normalB.har@140"`
- Times are **relative to earliest HAR request** in each file, not wall clock. The observer timer is relative to script startup/reset. Supply explicit `--offset = HAR-relative seconds - observer-relative seconds` based on a known, independently observed shared event (example: a marker at observer 120s matching HAR 90s => `--offset=-30`). **Do not guess offset to force a desired correlation.** Aligning one isolated timepoint never proves causal identity.
- Compare at least two independent ad occurrences with normal-playback controls, where feasible. Request fingerprints are ephemeral and may differ between runs; a match only indicates a candidate, not an ad-blocking rule. The safety analysis must stay `HOLD`.

## Record and judge

For each genuine observed ad: date, Chrome version, broad region, plan state, Yandex route, specific UI/audio behavior, repetitions, song-to-ad-to-song transition, seek/next/queue behavior, no personal data. Compare negatives: login/paywall/consent, first-party music, playlists, HTTP Range / 206, network loss, multiple tabs and 2+ hours. Recheck any affected class selector in the current DOM. Do not copy account screenshots unredacted.

**GO/NO-GO:** No claim of ad blocking without a dedicated authorized end-to-end test, safe ad-only signal, no silent gap or stuck player, and policy/security review. If an ad signal cannot be separated from music or subscription logic, classify it **UNKNOWN or NO-GO**; fail open.

## Test matrix for next operator

- Load/unload independent observer; confirm regular CELIKOM is untouched and no broad Chrome permissions were requested.
- Open/close Yandex tab, SPA navigation, pagehide/pageshow, multiple tabs; observe popup marker continuity and resets.
- Trigger allowed visual cases and observe CSS candidates (not blockers), then test audio/video occurrences with ordinary songs in different sessions.
- Compare blank, short, long, wrong-schema and data-heavy exports; malformed JSON must not export unknown fields; never pass raw HAR to the JSON viewer.
- Note any skipped DOM roots (`droppedRoots`) and throttle-related gaps; absence of logged candidates is **not** absence of advertising.
