(function registerCelikomOverlay(root) {
  "use strict";

  const dictionary = {
    ru: {
      title: "CELIKOM · ПРОТОТИП",
      phase: "Состояние",
      track: "Track ID",
      source: "Источник ID",
      player: "Плеер",
      drift: "Drift",
      lastEvent: "Событие",
      candidates: "Кандидаты",
      original: "ОРИГИНАЛ",
      emergency: "Вернуть оригинал",
      copy: "Копировать диагностику",
      copied: "Скопировано",
      collapse: "Свернуть",
      expand: "Развернуть",
      missing: "не найден"
    },
    en: {
      title: "CELIKOM · PROTOTYPE",
      phase: "State",
      track: "Track ID",
      source: "ID source",
      player: "Player",
      drift: "Drift",
      lastEvent: "Event",
      candidates: "Candidates",
      original: "ORIGINAL",
      emergency: "Restore original",
      copy: "Copy diagnostics",
      copied: "Copied",
      collapse: "Collapse",
      expand: "Expand",
      missing: "not detected"
    }
  };

  function language() {
    return String(navigator.language || "en").toLowerCase().startsWith("ru") ? "ru" : "en";
  }

  function escapeText(value) {
    return String(value ?? "");
  }

  function createOverlay(options = {}) {
    const strings = dictionary[language()];
    document.getElementById("celikom-poc-overlay-host")?.remove();
    const host = document.createElement("div");
    host.id = "celikom-poc-overlay-host";
    host.dataset.celikomUi = "true";
    const shadow = host.attachShadow({ mode: "closed" });

    const style = document.createElement("style");
    style.textContent = `
      :host { all: initial; }
      *, *::before, *::after { box-sizing: border-box; }
      .panel {
        --accent: #77f2c4;
        --danger: #ff6b6b;
        position: fixed;
        z-index: 2147483647;
        left: 16px;
        bottom: 16px;
        width: min(390px, calc(100vw - 32px));
        color: #f6f7f8;
        background: rgba(12, 14, 18, .96);
        border: 1px solid rgba(255, 255, 255, .13);
        border-radius: 16px;
        box-shadow: 0 18px 60px rgba(0, 0, 0, .45);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 12px;
        line-height: 1.4;
        overflow: hidden;
        backdrop-filter: blur(14px);
      }
      .head { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,.09); }
      .mark { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 5px rgba(119,242,196,.12); }
      .title { flex: 1; color: #fff; font-size: 11px; font-weight: 800; letter-spacing: .12em; }
      .phase { padding: 3px 7px; border-radius: 999px; background: rgba(119,242,196,.13); color: var(--accent); font-size: 10px; font-weight: 800; letter-spacing: .04em; }
      .toggle { border: 0; color: rgba(255,255,255,.65); background: transparent; cursor: pointer; font: inherit; padding: 3px 0; }
      .body { padding: 12px 14px 14px; }
      .panel.collapsed .body { display: none; }
      dl { display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 7px 10px; margin: 0 0 12px; }
      dt { color: rgba(255,255,255,.47); }
      dd { min-width: 0; margin: 0; color: #fff; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
      .candidate-list { max-height: 64px; overflow: auto; color: rgba(255,255,255,.62); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; }
      .log { height: 86px; margin: 10px 0 12px; padding: 8px 9px; overflow: auto; border-radius: 9px; background: #07090c; color: rgba(255,255,255,.63); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 10px; white-space: pre-wrap; }
      .actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      button.action { min-height: 36px; border: 1px solid rgba(255,255,255,.14); border-radius: 9px; background: rgba(255,255,255,.07); color: #fff; cursor: pointer; font: 700 11px/1.2 Inter, ui-sans-serif, system-ui, sans-serif; }
      button.action:hover { background: rgba(255,255,255,.12); }
      button.danger { border-color: rgba(255,107,107,.4); color: #ffb4b4; }
      .panel[data-phase="ERROR_RECOVERY"] .mark,
      .panel[data-phase="ERROR_RECOVERY"] .phase { background: rgba(255,107,107,.15); color: var(--danger); }
      .panel[data-phase="REPLACEMENT_ACTIVE"] .mark { animation: pulse 1.4s ease-in-out infinite; }
      @keyframes pulse { 50% { box-shadow: 0 0 0 9px rgba(119,242,196,0); } }
      @media (prefers-reduced-motion: reduce) { .panel[data-phase="REPLACEMENT_ACTIVE"] .mark { animation: none; } }
    `;

    const panel = document.createElement("section");
    panel.className = "panel";
    panel.dataset.phase = "IDLE";
    panel.innerHTML = `
      <div class="head">
        <span class="mark"></span>
        <span class="title"></span>
        <span class="phase"></span>
        <button class="toggle" type="button"></button>
      </div>
      <div class="body">
        <dl>
          <dt data-label="track"></dt><dd data-value="track"></dd>
          <dt data-label="source"></dt><dd data-value="source"></dd>
          <dt data-label="player"></dt><dd data-value="player"></dd>
          <dt data-label="drift"></dt><dd data-value="drift"></dd>
          <dt data-label="lastEvent"></dt><dd data-value="lastEvent"></dd>
          <dt data-label="candidates"></dt><dd class="candidate-list" data-value="candidates"></dd>
        </dl>
        <div class="log"></div>
        <div class="actions">
          <button class="action danger" data-action="emergency" type="button"></button>
          <button class="action" data-action="copy" type="button"></button>
        </div>
      </div>
    `;

    shadow.append(style, panel);
    (document.documentElement || document).append(host);

    const title = panel.querySelector(".title");
    const phase = panel.querySelector(".phase");
    const toggle = panel.querySelector(".toggle");
    const logNode = panel.querySelector(".log");
    const emergencyButton = panel.querySelector("[data-action='emergency']");
    const copyButton = panel.querySelector("[data-action='copy']");
    const values = Object.fromEntries([...panel.querySelectorAll("[data-value]")].map((node) => [node.dataset.value, node]));

    title.textContent = strings.title;
    toggle.textContent = strings.collapse;
    emergencyButton.textContent = strings.emergency;
    copyButton.textContent = strings.copy;
    panel.querySelectorAll("[data-label]").forEach((node) => {
      node.textContent = strings[node.dataset.label] || node.dataset.label;
    });

    let collapsed = false;
    let logs = [];
    let latestDiagnostics = {};

    function renderLogs() {
      logNode.textContent = logs.slice(-12).join("\n") || strings.original;
      logNode.scrollTop = logNode.scrollHeight;
    }

    function log(message) {
      const time = new Date().toLocaleTimeString([], { hour12: false });
      logs.push(`${time} ${escapeText(message)}`);
      logs = logs.slice(-60);
      renderLogs();
    }

    async function copyDiagnostics() {
      const text = JSON.stringify(latestDiagnostics, null, 2);
      try {
        await navigator.clipboard.writeText(text);
      } catch (_error) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.documentElement.append(textarea);
        textarea.select();
        document.execCommand("copy");
        textarea.remove();
      }
      const original = copyButton.textContent;
      copyButton.textContent = strings.copied;
      setTimeout(() => { copyButton.textContent = original; }, 1200);
      options.onCopy?.(text);
    }

    toggle.addEventListener("click", () => {
      collapsed = !collapsed;
      panel.classList.toggle("collapsed", collapsed);
      toggle.textContent = collapsed ? strings.expand : strings.collapse;
    });
    emergencyButton.addEventListener("click", () => options.onEmergency?.());
    copyButton.addEventListener("click", copyDiagnostics);

    function update(view = {}) {
      const currentPhase = String(view.phase || "IDLE");
      const player = view.player;
      const track = view.track;
      panel.dataset.phase = currentPhase;
      phase.textContent = currentPhase;
      values.track.textContent = track?.id || strings.missing;
      values.source.textContent = track?.source ? `${track.source} · ${track.confidence}` : strings.missing;
      values.player.textContent = player
        ? `${player.mediaId} · ${player.paused ? "pause" : "play"} · ${Number(player.currentTime || 0).toFixed(1)}s`
        : strings.missing;
      values.drift.textContent = Number.isFinite(view.driftMs) ? `${view.driftMs} ms` : "—";
      values.lastEvent.textContent = view.lastEvent || "—";
      values.candidates.textContent = (track?.candidates || [])
        .map((candidate) => `${candidate.id} (${candidate.score}, ${candidate.source})`)
        .join("\n") || "—";
      latestDiagnostics = view.diagnostics || view;
    }

    function setVisible(visible) {
      host.style.display = visible ? "block" : "none";
    }

    function destroy() {
      host.remove();
    }

    renderLogs();
    update();
    return Object.freeze({ destroy, log, setVisible, update });
  }

  Object.defineProperty(root, "__CELIKOM_POC_OVERLAY__", {
    value: Object.freeze({ createOverlay }),
    configurable: true,
    enumerable: false,
    writable: false
  });
})(globalThis);
