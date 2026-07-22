// ==UserScript==
// @name         Idle Hacking Item & Loadout Capture
// @namespace    https://www.idlehacking.com/
// @version      1.0.0
// @description  One-click read-only capture of the full game state (loadout, inventory, crafting data, resources). Never performs gameplay or crafting actions.
// @match        https://www.idlehacking.com/play*
// @match        https://idlehacking.com/play*
// @run-at       document-idle
// @updateURL    http://localhost:8123/item-loadout-capture.user.js
// @downloadURL  http://localhost:8123/item-loadout-capture.user.js
// @grant        GM_xmlhttpRequest
// @grant        GM_addElement
// @connect      localhost
// @connect      127.0.0.1
// ==/UserScript==

// v1.0.0 replaces the legacy tooltip/enhance-panel click-scraping tool
// (≤v0.9.1, see git history) with a single full-state capture. Safety
// boundary is unchanged: reads only, no synthetic input, no game
// function calls, no requests except POSTing captures to the user's
// own localhost hub.

(() => {
  "use strict";

  const TOOL_VERSION = "1.0.0";
  const HUB_EXPORT_URL = "http://localhost:8123/export";

  // Page-context window. Under @grant the script runs in the
  // Tampermonkey sandbox; page globals are only visible via unsafeWindow.
  const pageWindow =
    typeof unsafeWindow === "undefined" ? window : unsafeWindow;

  let status = "Ready";

  // ---- Game state bindings ----------------------------------------------
  // The game keeps its client state in top-level let/const bindings —
  // global lexical bindings, not window properties — so they must be read
  // by code evaluated in page scope. See docs/game-client-internals.md.
  // statsBreakdown/extendedStats/recentLossStreaks are lazy: open the
  // stats panel / loss history once per session to populate them.

  const GAME_STATE_BINDINGS = [
    "currentPlayer",
    "equipmentData",
    "inventoryData",
    "statsBreakdown",
    "extendedStats",
    "recentLossStreaks",
  ];

  function buildStateReaderBody(names) {
    const grabs = names
      .map(
        (name) => `
          try {
            out[${JSON.stringify(name)}] =
              typeof ${name} === "undefined" ? null : ${name};
          } catch (error) {
            errors[${JSON.stringify(name)}] = String(error);
          }`,
      )
      .join("\n");

    return `
      const out = {};
      const errors = {};
      ${grabs}
      let json;
      try {
        json = JSON.stringify({ bindings: out, errors });
      } catch (error) {
        json = JSON.stringify({
          bindings: null,
          errors: { serialize: String(error) },
        });
      }
      return json;`;
  }

  function injectReaderAndListen(names, useGmAddElement) {
    return new Promise((resolve, reject) => {
      const eventName = `ih-state-read-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2)}`;

      const timer = setTimeout(() => {
        document.removeEventListener(eventName, onEvent);
        reject(new Error("page reader timed out"));
      }, 2000);

      const onEvent = (event) => {
        clearTimeout(timer);
        document.removeEventListener(eventName, onEvent);
        try {
          resolve(JSON.parse(event.detail));
        } catch (error) {
          reject(error);
        }
      };

      document.addEventListener(eventName, onEvent);

      const source = `(() => {
        const read = () => { ${buildStateReaderBody(names)} };
        document.dispatchEvent(
          new CustomEvent(${JSON.stringify(eventName)}, { detail: read() }),
        );
      })();`;

      let script;
      if (useGmAddElement) {
        if (typeof GM_addElement !== "function") {
          clearTimeout(timer);
          document.removeEventListener(eventName, onEvent);
          reject(new Error("GM_addElement unavailable"));
          return;
        }
        script = GM_addElement("script", { textContent: source });
      } else {
        script = document.createElement("script");
        script.textContent = source;
        (document.head || document.documentElement).appendChild(script);
      }
      script?.remove();
    });
  }

  async function readGameBindings(names) {
    // Strategy 1: page Function constructor — sees global lexical
    // bindings; blocked only if the page CSP forbids unsafe-eval.
    try {
      const json = new pageWindow.Function(buildStateReaderBody(names))();
      return { readMethod: "function-constructor", ...JSON.parse(json) };
    } catch {
      // fall through
    }

    // Strategy 2: inline script element (blocked if CSP forbids inline).
    try {
      const parsed = await injectReaderAndListen(names, false);
      return { readMethod: "inline-script", ...parsed };
    } catch {
      // fall through
    }

    // Strategy 3: GM_addElement — Tampermonkey's privileged injection,
    // usually exempt from page CSP.
    const parsed = await injectReaderAndListen(names, true);
    return { readMethod: "gm-add-element", ...parsed };
  }

  async function buildCapturePayload() {
    const result = await readGameBindings(GAME_STATE_BINDINGS);
    const state = result.bindings ?? {};

    const equipmentCount =
      state.equipmentData && typeof state.equipmentData === "object"
        ? Object.keys(state.equipmentData).length
        : 0;
    const inventoryCount = Array.isArray(state.inventoryData?.items)
      ? state.inventoryData.items.length
      : 0;

    return {
      payload: {
        schema: "idle-hacking-state-capture-v1",
        capturedAt: new Date().toISOString(),
        sourceVersion: TOOL_VERSION,
        url: location.href,
        readMethod: result.readMethod,
        readErrors: result.errors ?? {},
        state,
      },
      summary: `${equipmentCount} equipped, ${inventoryCount} items`,
    };
  }

  function hubExportName() {
    return `idle-hacking-state-${new Date()
      .toISOString()
      .replace(/[:.]/g, "-")}.json`;
  }

  // ---- Delivery ----------------------------------------------------------

  function postToHub(payload, exportName, sendingMessage) {
    if (typeof GM_xmlhttpRequest !== "function") {
      setStatus("GM_xmlhttpRequest unavailable — reinstall from the hub URL");
      return;
    }

    setStatus(sendingMessage);

    GM_xmlhttpRequest({
      method: "POST",
      url: HUB_EXPORT_URL,
      headers: {
        "Content-Type": "application/json",
        "X-Export-Name": exportName,
      },
      data: JSON.stringify(payload, null, 2),
      timeout: 5000,
      onload: (response) => {
        setStatus(
          response.status === 200
            ? `Workspace: ${response.responseText.trim()}`
            : `Hub rejected export (HTTP ${response.status})`,
        );
      },
      onerror: () =>
        setStatus("Hub unreachable — is capture-hub running in WSL?"),
      ontimeout: () =>
        setStatus("Hub timed out — is capture-hub running in WSL?"),
    });
  }

  async function captureToHub() {
    setStatus("Reading full game state…");
    const { payload, summary } = await buildCapturePayload();
    console.info(
      `[IH Capture] Full state read via ${payload.readMethod}: ${summary}.`,
    );
    postToHub(payload, hubExportName(), `Sending full state (${summary})…`);
  }

  async function captureToDownload() {
    setStatus("Reading full game state…");
    const { payload, summary } = await buildCapturePayload();

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = hubExportName();
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);

    setStatus(`Downloaded full state (${summary})`);
  }

  // ---- Panel --------------------------------------------------------------

  function setStatus(message) {
    status = message;
    const element = document.querySelector(
      "#ih-capture-panel [data-role='status']",
    );
    if (element) {
      element.textContent = status;
    }
  }

  function createPanel() {
    document.querySelector("#ih-capture-panel")?.remove();

    const panel = document.createElement("section");
    panel.id = "ih-capture-panel";

    panel.innerHTML = `
      <div class="ihc-header">
        <strong>IH Capture v${TOOL_VERSION}</strong>
        <button data-action="collapse" title="Collapse">−</button>
      </div>
      <div class="ihc-body">
        <div class="ihc-actions">
          <button data-action="capture-state" class="wide">
            Capture all (full state)
          </button>
          <button data-action="capture-download" class="wide">
            Download instead (hub offline)
          </button>
        </div>
        <div class="ihc-status" data-role="status">${status}</div>
      </div>
    `;

    panel.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) {
        return;
      }

      const action = button.dataset.action;

      if (action === "capture-state") {
        captureToHub().catch((error) => {
          console.error("[IH Capture] Capture failed:", error);
          setStatus(`Capture failed: ${error}`);
        });
      }

      if (action === "capture-download") {
        captureToDownload().catch((error) => {
          console.error("[IH Capture] Capture failed:", error);
          setStatus(`Capture failed: ${error}`);
        });
      }

      if (action === "collapse") {
        panel.classList.toggle("collapsed");
        button.textContent = panel.classList.contains("collapsed")
          ? "+"
          : "−";
      }
    });

    document.body.appendChild(panel);
  }

  function addStyles() {
    const style = document.createElement("style");

    style.textContent = `
      #ih-capture-panel {
        position: fixed;
        left: 14px;
        bottom: 14px;
        z-index: 2147483647;
        width: 250px;
        color: #dce8f5;
        background: rgba(10, 18, 27, 0.97);
        border: 1px solid #59a8e8;
        border-radius: 5px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
        font: 12px ui-monospace, SFMono-Regular, Menlo,
          Consolas, monospace;
      }

      #ih-capture-panel .ihc-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 9px;
        border-bottom: 1px solid rgba(89, 168, 232, 0.35);
      }

      #ih-capture-panel .ihc-header button {
        width: 25px;
        padding: 2px;
      }

      #ih-capture-panel .ihc-body {
        padding: 8px;
      }

      #ih-capture-panel.collapsed .ihc-body {
        display: none;
      }

      #ih-capture-panel .ihc-actions {
        display: grid;
        gap: 5px;
      }

      #ih-capture-panel button {
        cursor: pointer;
        border: 1px solid #4c6b84;
        border-radius: 3px;
        padding: 6px 5px;
        color: #dce8f5;
        background: #1b2b39;
        font: inherit;
      }

      #ih-capture-panel button:hover {
        background: #26465e;
      }

      #ih-capture-panel .ihc-status {
        min-height: 1.2em;
        margin-top: 7px;
        color: #a9bac8;
      }
    `;

    document.head.appendChild(style);
  }

  addStyles();
  createPanel();

  console.info(
    `[IH Capture] v${TOOL_VERSION} loaded. One-click full-state capture; no DOM scraping, no gameplay actions.`,
  );
})();
