// ==UserScript==
// @name         Idle Hacking Item & Loadout Capture
// @namespace    https://www.idlehacking.com/
// @version      1.6.0
// @description  One-click read-only capture of the full game state (loadout, inventory, crafting data, resources) plus Hacking Simulator runs. Never performs gameplay or crafting actions.
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
// boundary: reads only, no synthetic input, no game function calls, no
// requests except POSTing to the user's own localhost hub. Since v1.5.0
// an OPT-IN auto-stream timer may also POST a lightweight combat-only
// payload on an interval (boundary amended 23 Jul 2026 at the player's
// request — still zero game interaction, localhost only).
//
// v1.6.0 adds Hacking Simulator capture. The player clicks RUN in the
// game's own Simulator panel; this script only *observes* the result the
// game has already computed, by reading the page-scope result bindings
// and the game's own IndexedDB history store. It never sends
// RUN_HACKING_SOFTWARE_PROFILER (or any other message) itself — the
// no-game-interaction boundary is unchanged.

(() => {
  "use strict";

  const TOOL_VERSION = "1.6.0";
  const HUB_EXPORT_URL = "http://localhost:8123/export";

  // Auto-stream: combat-only payload pushed on a timer while enabled.
  // 150s comfortably out-paces the ~50-fight combat-log window (~5 min at
  // observed fight tempo), so no fights are lost between pushes.
  const STREAM_SCHEMA = "idle-hacking-combat-stream-v1";
  const STREAM_BINDINGS = ["combatLog", "recentLossStreaks", "hackingState"];
  const STREAM_INTERVAL_MS = 150000;
  const STREAM_PREF_KEY = "ihc-auto-stream-enabled";

  // Sim capture: watches the two page-scope result bindings the game fills
  // in when the player runs a simulation, and pushes each NEW result once.
  // Polled at 2s against the profiler's own 5s cooldown, so back-to-back
  // runs can never be missed. Nothing is sent while the results are
  // unchanged, so leaving this on during normal play is silent.
  const SIM_SCHEMA = "idle-hacking-sim-runs-v1";
  const SIM_BINDINGS = [
    "homelabSoftwareProfilerResult",
    "homelabPipelineSimulationResult",
    "homelabSimulatorFormState",
  ];
  const SIM_POLL_MS = 2000;
  const SIM_PREF_KEY = "ihc-sim-capture-enabled";
  const SIM_DB_NAME = "idlehack.hacking-simulator-history";
  const SIM_DB_STORE = "runs";

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
  // hardwareInfo is likewise lazy: it hydrates from the HARDWARE_INFO
  // WS push when the Hardware Shop tab is opened.

  const GAME_STATE_BINDINGS = [
    "currentPlayer",
    "equipmentData",
    "inventoryData",
    "statsBreakdown",
    "extendedStats",
    "recentLossStreaks",
    "combatLog",
    "lastCombatStatusPayload",
    "hackingState",
    "hackingZones",
    "multiplierData",
    "homelabInfo",
    "hardwareInfo",
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

  function injectReaderAndListen(bodySource, useGmAddElement) {
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
        const read = () => { ${bodySource} };
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

  // Strategies, in preference order: page Function constructor (sees
  // global lexical bindings; blocked only if page CSP forbids
  // unsafe-eval), inline script element (blocked if CSP forbids
  // inline), GM_addElement (Tampermonkey's privileged injection,
  // usually CSP-exempt). The first method that works is cached so
  // periodic readiness polling doesn't retry failing strategies.
  const READ_METHODS = [
    "function-constructor",
    "inline-script",
    "gm-add-element",
  ];
  let preferredReadMethod = null;

  async function evaluateInPage(bodySource) {
    const attempt = async (method) => {
      if (method === "function-constructor") {
        return JSON.parse(new pageWindow.Function(bodySource)());
      }
      return injectReaderAndListen(bodySource, method === "gm-add-element");
    };

    const order = preferredReadMethod
      ? [
          preferredReadMethod,
          ...READ_METHODS.filter((m) => m !== preferredReadMethod),
        ]
      : READ_METHODS;

    let lastError;
    for (const method of order) {
      try {
        const parsed = await attempt(method);
        preferredReadMethod = method;
        return { readMethod: method, ...parsed };
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError ?? new Error("all read strategies failed");
  }

  function readGameBindings(names) {
    return evaluateInPage(buildStateReaderBody(names));
  }

  // ---- Capture readiness --------------------------------------------------
  // Lightweight page-scope poll (counts/booleans only, no serialization
  // of the full state) so the panel shows BEFORE capturing which lazy
  // stores are hydrated.

  function buildReadinessBody() {
    return `
      const out = {};
      out.inventory =
        typeof inventoryData !== "undefined" && inventoryData &&
        Array.isArray(inventoryData.items)
          ? inventoryData.items.length : 0;
      out.fights =
        typeof combatLog !== "undefined" && Array.isArray(combatLog)
          ? combatLog.length : 0;
      out.losses =
        typeof recentLossStreaks !== "undefined" &&
        Array.isArray(recentLossStreaks)
          ? recentLossStreaks.length : 0;
      out.homelab = typeof homelabInfo !== "undefined" && !!homelabInfo;
      out.hardware = typeof hardwareInfo !== "undefined" && !!hardwareInfo;
      out.stats =
        (typeof statsBreakdown !== "undefined" && !!statsBreakdown) ||
        (typeof extendedStats !== "undefined" && !!extendedStats);
      const fightsList =
        typeof combatLog !== "undefined" && Array.isArray(combatLog)
          ? combatLog
          : [];
      const hasDetail = (f) =>
        f && Array.isArray(f.combat_log) && f.combat_log.length > 0;
      out.roundDetail = fightsList.filter(hasDetail).length;
      // combatLog is newest-first: detailGap = how many fights ago the last
      // detailed one ran. 0 = recording live; large = modal closed since.
      out.detailGap = fightsList.findIndex(hasDetail);
      const nowMs =
        Date.now() +
        (typeof serverTimeOffsetMs === "number" ? serverTimeOffsetMs : 0);
      const lastLoss =
        typeof recentLossStreaks !== "undefined" &&
        Array.isArray(recentLossStreaks) && recentLossStreaks.length
          ? recentLossStreaks[0].ended_at_ms
          : 0;
      out.lastLossMin = lastLoss
        ? Math.max(0, Math.round((nowMs - lastLoss) / 60000))
        : null;
      return JSON.stringify(out);`;
  }

  async function updateReadiness() {
    const element = document.querySelector(
      "#ih-capture-panel [data-role='readiness']",
    );
    if (!element || document.hidden) {
      return;
    }

    try {
      const r = await evaluateInPage(buildReadinessBody());
      // live = the newest (or next-to-newest, to allow an in-flight fight)
      // combat-log entry carries round detail
      const detailLive = r.roundDetail > 0 && r.detailGap >= 0 && r.detailGap <= 1;
      const roundsPart = !r.fights
        ? "fights ✗"
        : detailLive
          ? `rounds ${r.roundDetail}/${r.fights} LIVE`
          : r.roundDetail
            ? `rounds ${r.roundDetail}/${r.fights} STALE`
            : `rounds 0/${r.fights}`;
      const parts = [
        r.inventory ? `inv ${r.inventory}` : "inv ✗",
        roundsPart,
        r.losses
          ? `losses ${r.losses}` +
            (r.lastLossMin !== null ? ` (${r.lastLossMin}m ago)` : "")
          : "losses ✗",
        r.homelab ? "homelab ✓" : "homelab ✗",
        r.hardware ? "hw ✓" : "hw ✗",
        r.stats ? "stats ✓" : "stats ✗",
      ];
      const complete = r.inventory && r.fights && r.homelab && r.stats && r.losses;
      const detailWarning = !r.fights
        ? ""
        : !r.roundDetail
          ? "\n⚠ no round detail — enable Detailed Logs (Hacking panel)"
          : detailLive
            ? ""
            : `\n⚠ round detail stopped ${r.detailGap} fights ago — re-enable Detailed Logs (Hacking panel)`;
      element.textContent =
        (complete ? "RICH — " : "PARTIAL — ") + parts.join(" · ") + detailWarning;
      element.classList.toggle("ok", !!complete && detailLive);
    } catch {
      element.textContent = "readiness unavailable";
      element.classList.remove("ok");
    }
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

    const missing = [];
    if (!inventoryCount) missing.push("inventory (open Inventory tab)");
    if (!state.homelabInfo) missing.push("homelab (open Homelab tab)");
    if (!Array.isArray(state.combatLog) || !state.combatLog.length) {
      missing.push("combat log (let fights run after page load)");
    }
    if (!state.statsBreakdown && !state.extendedStats) {
      missing.push("stats (open stats panel)");
    }

    let summary = `${equipmentCount} equipped, ${inventoryCount} items`;
    if (missing.length) {
      summary += ` — THIN: missing ${missing.join("; ")}`;
    }
    // Informational only — hardware data is useful but its absence does
    // not make a capture THIN for loadout/crafting analysis.
    if (!state.hardwareInfo) {
      summary += " — no hardware data (open Hardware Shop tab to include)";
    }

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
      summary,
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

  // ---- Auto-stream -------------------------------------------------------

  let streamTimer = null;

  function streamEnabled() {
    try {
      return localStorage.getItem(STREAM_PREF_KEY) === "1";
    } catch {
      return false;
    }
  }

  function setStreamStatus(message) {
    const element = document.querySelector(
      "#ih-capture-panel [data-role='stream-status']",
    );
    if (element) {
      element.textContent = message;
    }
  }

  // Light scalar slice of currentPlayer — the full save is ~1MB and fully
  // recoverable from any click-capture, but these few time-varying fields
  // let the hub log combat-stat changes (automatic A/B segmentation).
  function buildPlayerLiteBody() {
    return `
      const p = typeof currentPlayer === "undefined" ? null : currentPlayer;
      return JSON.stringify(!p ? null : {
        hack_level: p.hack_level,
        credits: p.credits,
        chips: p.chips,
        hackcoin: p.hackcoin,
        current_win_streak: p.current_win_streak,
        current_zone: p.current_zone,
        combat_stats: p.combat_stats,
      });`;
  }

  async function pushStream() {
    const result = await readGameBindings(STREAM_BINDINGS);
    const state = result.bindings ?? {};
    try {
      state.playerLite = await evaluateInPage(buildPlayerLiteBody());
    } catch {
      state.playerLite = null;
    }
    const payload = {
      schema: STREAM_SCHEMA,
      capturedAt: new Date().toISOString(),
      sourceVersion: TOOL_VERSION,
      readMethod: result.readMethod,
      state,
    };
    const stamp = new Date().toLocaleTimeString();
    if (typeof GM_xmlhttpRequest !== "function") {
      setStreamStatus("stream: GM_xmlhttpRequest unavailable");
      return;
    }
    GM_xmlhttpRequest({
      method: "POST",
      url: HUB_EXPORT_URL,
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify(payload),
      timeout: 5000,
      onload: (response) =>
        setStreamStatus(
          response.status === 200
            ? `${stamp} ${response.responseText.trim()}`
            : `stream: hub HTTP ${response.status}`,
        ),
      onerror: () => setStreamStatus("stream: hub unreachable"),
      ontimeout: () => setStreamStatus("stream: hub timed out"),
    });
  }

  function applyStreamState() {
    const button = document.querySelector(
      "#ih-capture-panel [data-action='toggle-stream']",
    );
    const enabled = streamEnabled();
    if (button) {
      button.textContent = `Auto-stream: ${enabled ? "ON" : "OFF"}`;
    }
    if (enabled && !streamTimer) {
      streamTimer = setInterval(() => {
        pushStream().catch((error) =>
          setStreamStatus(`stream failed: ${error}`),
        );
      }, STREAM_INTERVAL_MS);
      pushStream().catch((error) => setStreamStatus(`stream failed: ${error}`));
    }
    if (!enabled && streamTimer) {
      clearInterval(streamTimer);
      streamTimer = null;
      setStreamStatus("stream: off");
    }
  }

  function toggleStream() {
    try {
      localStorage.setItem(STREAM_PREF_KEY, streamEnabled() ? "0" : "1");
    } catch {
      // private mode etc. — timer still applies for this page lifetime
    }
    applyStreamState();
  }

  // ---- Hacking Simulator capture ------------------------------------------
  // The game stores each simulation result in a page-scope binding and
  // mirrors the last 10 per mode into its own IndexedDB store. Both are
  // read-only observations of a result the player already asked the game
  // to compute.

  let simTimer = null;
  const simSeen = new Set();

  function simEnabled() {
    try {
      return localStorage.getItem(SIM_PREF_KEY) === "1";
    } catch {
      return false;
    }
  }

  function setSimStatus(message) {
    const element = document.querySelector(
      "#ih-capture-panel [data-role='sim-status']",
    );
    if (element) {
      element.textContent = message;
    }
  }

  // Stable fingerprint so an unchanged binding is pushed exactly once. The
  // hub dedupes authoritatively too; this only keeps the wire quiet.
  function fingerprint(value) {
    const text = JSON.stringify(value);
    let hash = 5381;
    for (let i = 0; i < text.length; i += 1) {
      hash = ((hash << 5) + hash + text.charCodeAt(i)) | 0;
    }
    return `${text.length}:${hash}`;
  }

  // A sim result is only interpretable next to the stats it was run with:
  // gear_set_items says which items a "gear set" run used, and combat_stats
  // pins the currently-equipped baseline.
  function buildSimContextBody() {
    return `
      const p = typeof currentPlayer === "undefined" ? null : currentPlayer;
      return JSON.stringify(!p ? null : {
        hack_level: p.hack_level,
        current_zone: p.current_zone,
        current_win_streak: p.current_win_streak,
        combat_stats: p.combat_stats,
        gear_sets: p.gear_sets,
        gear_set_items: p.gear_set_items,
        gear_set_capacity: p.gear_set_capacity,
        hacking_simulator: p.hacking_simulator,
      });`;
  }

  // Read the game's own history store. Never opens with a version number
  // (that would trigger an upgrade transaction) and never writes.
  function readSimHistoryFromIDB() {
    return new Promise((resolve) => {
      let db;
      try {
        db = pageWindow.indexedDB;
      } catch {
        resolve({ records: [], note: "indexedDB unavailable" });
        return;
      }
      if (!db) {
        resolve({ records: [], note: "indexedDB unavailable" });
        return;
      }

      let settled = false;
      const done = (value) => {
        if (!settled) {
          settled = true;
          resolve(value);
        }
      };
      setTimeout(() => done({ records: [], note: "indexedDB timed out" }), 4000);

      const request = db.open(SIM_DB_NAME);
      request.onerror = () => done({ records: [], note: "indexedDB open failed" });
      request.onsuccess = () => {
        const handle = request.result;
        try {
          if (!handle.objectStoreNames.contains(SIM_DB_STORE)) {
            handle.close();
            done({ records: [], note: "no simulation history yet" });
            return;
          }
          const store = handle
            .transaction(SIM_DB_STORE, "readonly")
            .objectStore(SIM_DB_STORE);
          const all = store.getAll();
          all.onsuccess = () => {
            handle.close();
            done({ records: Array.isArray(all.result) ? all.result : [] });
          };
          all.onerror = () => {
            handle.close();
            done({ records: [], note: "indexedDB read failed" });
          };
        } catch (error) {
          try {
            handle.close();
          } catch {
            // already closing
          }
          done({ records: [], note: String(error) });
        }
      };
    });
  }

  async function collectSimRuns(includeHistory) {
    const result = await readGameBindings(SIM_BINDINGS);
    const bindings = result.bindings ?? {};

    const runs = [];
    const add = (mode, payload, source) => {
      if (!payload || typeof payload !== "object") {
        return;
      }
      runs.push({ mode, source, result: payload });
    };
    add("software_profiler", bindings.homelabSoftwareProfilerResult, "live");
    add("cicd_pipeline", bindings.homelabPipelineSimulationResult, "live");

    let historyNote = null;
    if (includeHistory) {
      const history = await readSimHistoryFromIDB();
      historyNote = history.note ?? null;
      for (const record of history.records) {
        if (record && typeof record === "object" && record.result) {
          runs.push({
            mode: record.mode || "unknown",
            source: "history",
            recorded_at_ms: record.recorded_at_ms || null,
            result: record.result,
          });
        }
      }
    }

    let context = null;
    try {
      context = await evaluateInPage(buildSimContextBody());
    } catch {
      context = null;
    }

    return {
      runs,
      historyNote,
      form: bindings.homelabSimulatorFormState ?? null,
      readMethod: result.readMethod,
      context,
    };
  }

  async function pushSimRuns({ includeHistory, quiet }) {
    const collected = await collectSimRuns(includeHistory);

    const fresh = collected.runs.filter((run) => {
      const key = `${run.mode}:${fingerprint(run.result)}`;
      if (simSeen.has(key)) {
        return false;
      }
      simSeen.add(key);
      return true;
    });

    if (!fresh.length) {
      if (!quiet) {
        setSimStatus(
          collected.historyNote
            ? `sim: nothing new (${collected.historyNote})`
            : "sim: nothing new to send",
        );
      }
      return;
    }

    const payload = {
      schema: SIM_SCHEMA,
      capturedAt: new Date().toISOString(),
      sourceVersion: TOOL_VERSION,
      readMethod: collected.readMethod,
      state: {
        runs: fresh,
        form: collected.form,
        context: collected.context,
      },
    };

    if (typeof GM_xmlhttpRequest !== "function") {
      setSimStatus("sim: GM_xmlhttpRequest unavailable");
      return;
    }

    const stamp = new Date().toLocaleTimeString();
    GM_xmlhttpRequest({
      method: "POST",
      url: HUB_EXPORT_URL,
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify(payload),
      timeout: 8000,
      onload: (response) =>
        setSimStatus(
          response.status === 200
            ? `${stamp} ${response.responseText.trim()}`
            : `sim: hub HTTP ${response.status}`,
        ),
      onerror: () => setSimStatus("sim: hub unreachable"),
      ontimeout: () => setSimStatus("sim: hub timed out"),
    });
  }

  function applySimState() {
    const button = document.querySelector(
      "#ih-capture-panel [data-action='toggle-sim']",
    );
    const enabled = simEnabled();
    if (button) {
      button.textContent = `Sim capture: ${enabled ? "ON" : "OFF"}`;
    }
    if (enabled && !simTimer) {
      simTimer = setInterval(() => {
        pushSimRuns({ includeHistory: false, quiet: true }).catch((error) =>
          setSimStatus(`sim failed: ${error}`),
        );
      }, SIM_POLL_MS);
      setSimStatus("sim: watching for runs…");
      pushSimRuns({ includeHistory: true, quiet: true }).catch((error) =>
        setSimStatus(`sim failed: ${error}`),
      );
    }
    if (!enabled && simTimer) {
      clearInterval(simTimer);
      simTimer = null;
      setSimStatus("sim: off");
    }
  }

  function toggleSim() {
    try {
      localStorage.setItem(SIM_PREF_KEY, simEnabled() ? "0" : "1");
    } catch {
      // private mode etc. — timer still applies for this page lifetime
    }
    applySimState();
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
        <div class="ihc-ready" data-role="readiness">checking readiness…</div>
        <div class="ihc-actions">
          <button data-action="capture-state" class="wide">
            Capture all (full state)
          </button>
          <button data-action="capture-download" class="wide">
            Download instead (hub offline)
          </button>
          <button data-action="toggle-stream" class="wide">
            Auto-stream: OFF
          </button>
          <button data-action="toggle-sim" class="wide">
            Sim capture: OFF
          </button>
          <button data-action="capture-sim" class="wide">
            Send sim history now
          </button>
        </div>
        <div class="ihc-status" data-role="stream-status">stream: off</div>
        <div class="ihc-status" data-role="sim-status">sim: off</div>
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

      if (action === "toggle-stream") {
        toggleStream();
      }

      if (action === "toggle-sim") {
        toggleSim();
      }

      if (action === "capture-sim") {
        setSimStatus("sim: reading results…");
        pushSimRuns({ includeHistory: true, quiet: false }).catch((error) => {
          console.error("[IH Capture] Sim capture failed:", error);
          setSimStatus(`sim failed: ${error}`);
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
        white-space: pre-wrap;
      }

      #ih-capture-panel .ihc-ready {
        margin-bottom: 7px;
        line-height: 1.4;
        color: #e0b36a;
        white-space: pre-wrap;
      }

      #ih-capture-panel .ihc-ready.ok {
        color: #7fd18a;
      }
    `;

    document.head.appendChild(style);
  }

  addStyles();
  createPanel();
  applyStreamState();
  applySimState();
  updateReadiness();
  setInterval(updateReadiness, 3000);

  console.info(
    `[IH Capture] v${TOOL_VERSION} loaded. One-click full-state capture; no DOM scraping, no gameplay actions.`,
  );
})();
