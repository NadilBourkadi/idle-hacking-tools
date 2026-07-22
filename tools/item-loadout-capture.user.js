// ==UserScript==
// @name         Idle Hacking Item & Loadout Capture
// @namespace    https://www.idlehacking.com/
// @version      0.6.1
// @description  Passively captures equipped/candidate item tooltips plus user-opened Enhancing panels. Never performs gameplay or crafting actions.
// @match        https://www.idlehacking.com/play*
// @match        https://idlehacking.com/play*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(() => {
  "use strict";

  const STORAGE_KEY = "idle-hacking-item-capture:v4";
  const LEGACY_STORAGE_KEY = "idle-hacking-item-capture:v3";

  const SLOT_NAMES = [
    "Payload",
    "Firewall",
    "Analyzer",
    "Shell",
    "Driver",
    "Router",
    "Daemon",
    "Kernel",
  ];

  const SLOT_SET = new Set(SLOT_NAMES);

  const RARITIES = new Set([
    "Basic",
    "Common",
    "Uncommon",
    "Rare",
    "Epic",
  ]);

  const ACTION_LINES = new Set([
    "EQUIP",
    "UNEQUIP",
    "ENHANCE ITEM",
    "LINK IN CHAT",
    "LOCK ITEM",
    "UNLOCK ITEM",
    "LIST ON MARKET",
    "REMOVE LISTING",
    "DECOMPILE",
  ]);

  const AFFIX_RE = /^(.*?)\s+\(T(\d+)\):\s*(.+)$/i;

  const CRAFT_OPERATIONS = [
    { key: "augment", label: "AUGMENT" },
    { key: "prune", label: "PRUNE" },
    { key: "refactor", label: "REFACTOR" },
    { key: "lockAffix", label: "LOCK AFFIX" },
    { key: "unlock", label: "UNLOCK" },
    { key: "compile", label: "COMPILE" },
    { key: "versionUpgrade", label: "VERSION UPGRADE" },
    { key: "biasReroll", label: "BIAS REROLL" },
  ];

  const CRAFT_RESOURCE_NAMES = [
    "Credits",
    "Snippets",
    "Cycles",
    "Hashes",
    "Packets",
    "Essences",
    "Essence",
    "Stabilizers",
    "Stabilizer",
    "Stability",
  ];

  const MAX_CRAFT_SNAPSHOTS = 60;
  const MAX_ITEM_REVISIONS = 100;

  let state = loadState();
  let autoCapture = true;
  let scanTimer = null;
  let status = "Ready";
  let pendingClickContext = null;
  let pendingClickExpiryTimer = null;
  let lastOpenedItemContext = null;
  let activeCraftContext = null;

  function emptyState() {
    return {
      schemaVersion: 4,
      candidates: [],
      equippedBySlot: {},
      craftingSnapshots: [],
      itemRevisions: [],
      loadoutScan: {
        active: false,
        startedAt: null,
      },
    };
  }

  function isValidBaseState(parsed) {
    return Boolean(
      parsed &&
      Array.isArray(parsed.candidates) &&
      parsed.equippedBySlot &&
      typeof parsed.equippedBySlot === "object"
    );
  }

  function migrateState(parsed) {
    if (!isValidBaseState(parsed)) {
      return null;
    }

    return {
      ...emptyState(),
      ...parsed,
      schemaVersion: 4,
      craftingSnapshots: Array.isArray(parsed.craftingSnapshots)
        ? parsed.craftingSnapshots.map(upgradeCraftSnapshot)
        : [],
      itemRevisions: Array.isArray(parsed.itemRevisions)
        ? parsed.itemRevisions
        : [],
      loadoutScan: parsed.loadoutScan || {
        active: false,
        startedAt: null,
      },
    };
  }

  function loadState() {
    for (const key of [STORAGE_KEY, LEGACY_STORAGE_KEY]) {
      try {
        const parsed = JSON.parse(
          localStorage.getItem(key) || "null",
        );
        const migrated = migrateState(parsed);

        if (migrated) {
          return migrated;
        }
      } catch (error) {
        console.warn(
          `[IH Capture] Could not restore saved state from ${key}:`,
          error,
        );
      }
    }

    return emptyState();
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      const quotaError =
        error?.name === "QuotaExceededError" ||
        error?.name === "NS_ERROR_DOM_QUOTA_REACHED";

      if (!quotaError) {
        console.error("[IH Capture] Could not save state:", error);
        status = "Could not save capture state";
        updatePanel();
        return;
      }

      // Preserve recent evidence if browser localStorage is full.
      state.craftingSnapshots = state.craftingSnapshots.slice(-30);
      state.itemRevisions = state.itemRevisions.slice(-50);

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        status =
          "Storage pruned to recent craft/revision history; export now";
      } catch (retryError) {
        console.error(
          "[IH Capture] State still exceeds localStorage quota:",
          retryError,
        );
        status = "Storage full — copy/download JSON before clearing";
      }
    }

    updatePanel();
  }

  function normalise(text) {
    return String(text || "")
      .replace(/\r/g, "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n[ \t]+/g, "\n")
      .replace(/[ \t]{2,}/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function canonicalLine(line) {
    const value = String(line || "").trim().toLowerCase();

    return value
      ? value[0].toUpperCase() + value.slice(1)
      : value;
  }

  function isElementVisible(element) {
    if (!(element instanceof HTMLElement)) {
      return false;
    }

    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();

    return (
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      Number(style.opacity) !== 0 &&
      rect.width > 0 &&
      rect.height > 0 &&
      rect.bottom > 0 &&
      rect.right > 0 &&
      rect.top < innerHeight &&
      rect.left < innerWidth
    );
  }

  function isVisible(element) {
    if (!isElementVisible(element)) {
      return false;
    }

    const rect = element.getBoundingClientRect();

    return rect.width > 130 && rect.height > 120;
  }

  function resemblesTooltip(text) {
    return (
      text.length >= 80 &&
      text.length <= 10000 &&
      text.includes("Item Level:") &&
      text.includes("Required Level:") &&
      text.includes("Stability:") &&
      SLOT_NAMES.some((slot) =>
        new RegExp(`(^|\\n)${slot}($|\\n)`, "i").test(text),
      )
    );
  }

  function findTooltipRoots() {
    const matches = [...document.querySelectorAll("body *")]
      .filter(isVisible)
      .filter((element) =>
        resemblesTooltip(normalise(element.innerText)),
      );

    // Keep the deepest matching wrapper so that parent page containers
    // are not mistaken for separate item tooltips.
    return matches.filter(
      (element) =>
        ![...element.children].some(
          (child) =>
            isVisible(child) &&
            resemblesTooltip(normalise(child.innerText)),
        ),
    );
  }

  function cleanLines(rawText) {
    const lines = normalise(rawText)
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const actionIndex = lines.findIndex((line) =>
      ACTION_LINES.has(line.toUpperCase()),
    );

    return actionIndex >= 0
      ? lines.slice(0, actionIndex)
      : lines;
  }

  function readNumber(line, regex) {
    const match = String(line || "").match(regex);

    return match
      ? Number(match[1].replaceAll(",", ""))
      : null;
  }

  function readFloat(line, regex) {
    const match = String(line || "").match(regex);

    return match ? Number(match[1]) : null;
  }

  function hashString(input) {
    let hash = 2166136261;

    for (let index = 0; index < input.length; index += 1) {
      hash ^= input.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }

    return (hash >>> 0).toString(16).padStart(8, "0");
  }

  function parseTooltip(element) {
    const rawText = normalise(element.innerText);

    // Detect equipped state before cleanLines() removes action buttons.
    // Directly opening an equipped item exposes an UNEQUIP action, while
    // comparison panels label the reference item CURRENT EQUIPPED.
    const rawLines = rawText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const equipped =
      rawLines.some(
        (line) => /^CURRENT EQUIPPED\b/i.test(line),
      ) ||
      rawLines.some(
        (line) => /^UNEQUIP\b/i.test(line),
      );

    const lines = cleanLines(rawText);

    const rarityIndex = lines.findIndex((line) =>
      RARITIES.has(canonicalLine(line)),
    );

    if (rarityIndex < 1) {
      return null;
    }

    const rarity = canonicalLine(lines[rarityIndex]);

    const slotIndex = lines.findIndex(
      (line, index) =>
        index > rarityIndex &&
        SLOT_SET.has(canonicalLine(line)),
    );

    if (slotIndex < 0) {
      return null;
    }

    const slot = canonicalLine(lines[slotIndex]);

    const name = lines
      .slice(0, rarityIndex)
      .filter((line) => {
        const upper = line.toUpperCase();

        return (
          upper !== "CURRENT EQUIPPED" &&
          upper !== "SHOW NOTES" &&
          upper !== "HIDE NOTES"
        );
      })
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();

    if (!name) {
      return null;
    }

    const itemLevelLine = lines.find((line) =>
      line.startsWith("Item Level:"),
    );

    const requiredLevelLine = lines.find((line) =>
      line.startsWith("Required Level:"),
    );

    const stabilityLine = lines.find((line) =>
      line.startsWith("Stability:"),
    );

    const compiledLine = lines.find((line) =>
      line.startsWith("Compiled:"),
    );

    const itemLevel = readNumber(
      itemLevelLine,
      /Item Level:\s*([\d,]+)/i,
    );

    const ratio = readFloat(
      itemLevelLine,
      /Ratio:\s*([\d.]+)/i,
    );

    const requiredLevel = readNumber(
      requiredLevelLine,
      /Required Level:\s*([\d,]+)/i,
    );

    const stabilityCurrent = readNumber(
      stabilityLine,
      /Stability:\s*(\d+)/i,
    );

    const stabilityMaximum = readNumber(
      stabilityLine,
      /Stability:\s*\d+\s*\/\s*(\d+)/i,
    );

    const compiledPercent = readFloat(
      compiledLine,
      /Compiled:\s*\+?([\d.]+)%/i,
    );

    const foundBy =
      lines
        .find((line) => line.startsWith("Found by:"))
        ?.replace(/^Found by:\s*/i, "") || null;

    const enhancedBy =
      lines
        .find((line) => line.startsWith("Enhanced by:"))
        ?.replace(/^Enhanced by:\s*/i, "") || null;

    const affixStart = lines.findIndex((line) =>
      AFFIX_RE.test(line),
    );

    if (affixStart < 0) {
      return null;
    }

    const affixes = [];

    for (
      let index = affixStart;
      index < lines.length;
      index += 1
    ) {
      const match = lines[index].match(AFFIX_RE);

      // Comparison deltas follow the uninterrupted affix block.
      if (!match) {
        break;
      }

      const affixName = match[1].trim();

      affixes.push({
        name: affixName,
        tier: Number(match[2]),
        kind: affixName.toLowerCase().startsWith("of ")
          ? "suffix"
          : "prefix",
        statsText: match[3].trim(),
        rawText: lines[index],
      });
    }

    const metadataEndCandidates = [
      lines.findIndex((line) => line.startsWith("Found by:")),
      lines.findIndex((line) =>
        line.startsWith("Enhanced by:"),
      ),
      lines.findIndex((line) =>
        line.startsWith("Stability:"),
      ),
    ].filter((index) => index >= 0);

    const metadataEnd =
      metadataEndCandidates.length > 0
        ? Math.max(...metadataEndCandidates)
        : slotIndex;

    const implicitText =
      lines
        .slice(metadataEnd + 1, affixStart)
        .find((line) => /^[+-][\d,.]+/.test(line)) || null;

    const coreLines = [
      name,
      rarity,
      slot,
      itemLevelLine,
      requiredLevelLine,
      compiledLine,
      stabilityLine,
      implicitText,
      ...affixes.map((affix) => affix.rawText),
    ].filter(Boolean);

    const key = hashString(coreLines.join("|"));
    const timestamp = new Date().toISOString();

    return {
      key,
      capturedAt: timestamp,
      lastSeenAt: timestamp,
      equipped,
      name,
      rarity,
      slot,
      itemLevel,
      ratio,
      requiredLevel,
      stabilityCurrent,
      stabilityMaximum,
      compiledPercent,
      foundBy,
      enhancedBy,
      implicitText,
      affixes,
      coreText: coreLines.join("\n"),
    };
  }

  function itemIdentityMatches(left, right) {
    if (!left || !right) {
      return false;
    }

    if (left.domItemId && right.domItemId) {
      return left.domItemId === right.domItemId;
    }

    return left.key === right.key;
  }

  function recordItemRevision(item, reason) {
    if (!item?.key) {
      return;
    }

    const revisionKey = hashString(
      [item.domItemId, item.key, item.coreText, reason].join("|"),
    );

    if (
      state.itemRevisions.some(
        (revision) => revision.revisionKey === revisionKey,
      )
    ) {
      return;
    }

    state.itemRevisions.push({
      revisionKey,
      recordedAt: new Date().toISOString(),
      reason,
      item: structuredClone(item),
    });

    if (state.itemRevisions.length > MAX_ITEM_REVISIONS) {
      state.itemRevisions.splice(
        0,
        state.itemRevisions.length - MAX_ITEM_REVISIONS,
      );
    }
  }

  function recordEquipped(item) {
    const previous = state.equippedBySlot[item.slot];
    const contentChanged =
      previous &&
      itemIdentityMatches(previous, item) &&
      previous.key !== item.key;

    if (contentChanged) {
      recordItemRevision(previous, "equipped-content-changed");
    }

    state.equippedBySlot[item.slot] = {
      ...item,
      domItemId: item.domItemId || previous?.domItemId || null,
      equipped: true,
      capturedAt: itemIdentityMatches(previous, item)
        ? previous.capturedAt
        : item.capturedAt,
    };

    // A currently equipped item is not also counted as a candidate.
    state.candidates = state.candidates.filter(
      (candidate) =>
        !itemIdentityMatches(candidate, item),
    );

    return !previous ||
      !itemIdentityMatches(previous, item) ||
      previous.key !== item.key;
  }

  function recordCandidate(item) {
    const currentForSlot = state.equippedBySlot[item.slot];

    if (itemIdentityMatches(currentForSlot, item)) {
      return "unchanged";
    }

    const existing = state.candidates.find(
      (candidate) => itemIdentityMatches(candidate, item),
    );

    if (existing) {
      if (existing.key === item.key) {
        existing.lastSeenAt = item.lastSeenAt;
        existing.domItemId =
          item.domItemId || existing.domItemId || null;
        return "unchanged";
      }

      recordItemRevision(existing, "candidate-content-changed");
      const originalCapturedAt = existing.capturedAt;
      Object.assign(existing, {
        ...item,
        domItemId: item.domItemId || existing.domItemId || null,
        equipped: false,
        capturedAt: originalCapturedAt,
      });
      return "updated";
    }

    state.candidates.push({
      ...item,
      domItemId: item.domItemId || null,
      equipped: false,
    });

    return "new";
  }

  function getVisibleParsedItems() {
    const unique = new Map();

    for (const root of findTooltipRoots()) {
      const item = parseTooltip(root);

      if (!item || !item.itemLevel || !item.affixes.length) {
        continue;
      }

      unique.set(item.key, item);
    }

    return [...unique.values()];
  }

  function normaliseName(value) {
    return normalise(value).toLowerCase();
  }

  function setPendingClickContext(context) {
    pendingClickContext = {
      ...context,
      capturedAt: Date.now(),
    };

    clearTimeout(pendingClickExpiryTimer);

    pendingClickExpiryTimer = setTimeout(() => {
      pendingClickContext = null;
    }, 3000);
  }

  function readClickedItemName(element, kind) {
    if (!element) {
      return null;
    }

    if (kind === "equipped") {
      return normalise(
        element.querySelector(".item-name")?.textContent || "",
      ) || null;
    }

    return normalise(
      element.getAttribute("aria-label") ||
      element.querySelector(
        ".inventory-list-item-name, .item-name",
      )?.textContent ||
      "",
    ) || null;
  }

  function captureClickOrigin(event) {
    const target =
      event.target instanceof Element
        ? event.target
        : null;

    if (!target) {
      return;
    }

    const clickedAction = normalise(
      target.closest("button, [role='button']")?.textContent || "",
    ).toUpperCase();

    if (clickedAction.startsWith("ENHANCE ITEM")) {
      const sourceContext =
        lastOpenedItemContext || pendingClickContext;

      activeCraftContext = sourceContext
        ? {
            itemId: sourceContext.itemId || null,
            itemKey: sourceContext.itemKey || null,
            name: sourceContext.name || null,
            slot: sourceContext.slot ||
              sourceContext.slotId || null,
            capturedAt: Date.now(),
          }
        : null;
      status = activeCraftContext?.name
        ? `Opening Enhancing: ${activeCraftContext.name}`
        : "Opening Enhancing panel";
      updatePanel();
      return;
    }

    const equippedSlot = target.closest(
      "#equipped-software-panel .equipment-slot",
    );

    if (equippedSlot) {
      const itemNode =
        equippedSlot.querySelector("[data-item-id]");

      setPendingClickContext({
        kind: "equipped",
        itemId:
          itemNode?.getAttribute("data-item-id") || null,
        name: readClickedItemName(
          equippedSlot,
          "equipped",
        ),
        slotId:
          equippedSlot.getAttribute("data-slot") || null,
      });

      status = pendingClickContext.name
        ? `Opening equipped: ${pendingClickContext.name}`
        : "Opening equipped item";

      updatePanel();
      return;
    }

    const inventoryItem = target.closest(
      "#inventory-grid [data-item-id]",
    );

    if (inventoryItem) {
      const slotSection = inventoryItem.closest(
        "[data-slot-id]",
      );

      setPendingClickContext({
        kind: "candidate",
        itemId:
          inventoryItem.getAttribute("data-item-id") || null,
        name: readClickedItemName(
          inventoryItem,
          "candidate",
        ),
        slotId:
          slotSection?.getAttribute("data-slot-id") || null,
      });

      status = pendingClickContext.name
        ? `Opening candidate: ${pendingClickContext.name}`
        : "Opening inventory item";

      updatePanel();
    }
  }

  function findContextItem(visibleItems, context) {
    if (!context || visibleItems.length === 0) {
      return null;
    }

    if (context.name) {
      const targetName = normaliseName(context.name);

      const exact = visibleItems.find(
        (item) =>
          normaliseName(item.name) === targetName,
      );

      if (exact) {
        return exact;
      }
    }

    if (visibleItems.length === 1) {
      return visibleItems[0];
    }

    return null;
  }

  function clearPendingClickContext() {
    pendingClickContext = null;
    clearTimeout(pendingClickExpiryTimer);
    pendingClickExpiryTimer = null;
  }

  function captureVisible({ manual = false } = {}) {
    const visibleItems = getVisibleParsedItems();

    let newCandidates = 0;
    let updatedCandidates = 0;
    let newEquippedSlots = 0;

    const context =
      pendingClickContext &&
      Date.now() - pendingClickContext.capturedAt < 3000
        ? pendingClickContext
        : null;

    const contextItem = findContextItem(
      visibleItems,
      context,
    );

    if (context && contextItem) {
      const enrichedItem = {
        ...contextItem,
        domItemId: context.itemId || contextItem.domItemId || null,
      };

      lastOpenedItemContext = {
        kind: context.kind,
        itemId: enrichedItem.domItemId,
        itemKey: enrichedItem.key,
        name: enrichedItem.name,
        slot: enrichedItem.slot,
        capturedAt: Date.now(),
      };

      if (context.kind === "equipped") {
        if (
          recordEquipped({
            ...enrichedItem,
            equipped: true,
          })
        ) {
          newEquippedSlots += 1;
        }
      } else {
        const result = recordCandidate(enrichedItem);

        if (result === "new") {
          newCandidates += 1;
        } else if (result === "updated") {
          updatedCandidates += 1;
        }
      }

      // A comparison tooltip may also expose the currently equipped
      // reference item explicitly. Capture that, but do not treat any
      // other unlabelled tooltip as another candidate.
      for (const item of visibleItems) {
        if (
          item.key !== contextItem.key &&
          item.equipped &&
          recordEquipped(item)
        ) {
          newEquippedSlots += 1;
        }
      }

      clearPendingClickContext();
    } else {
      for (const item of visibleItems) {
        if (item.equipped) {
          if (recordEquipped(item)) {
            newEquippedSlots += 1;
          }
        } else if (!context) {
          const result = recordCandidate(item);

          if (result === "new") {
            newCandidates += 1;
          } else if (result === "updated") {
            updatedCandidates += 1;
          }
        }
      }
    }

    if (visibleItems.length > 0) {
      maybeCompleteLoadoutScan();

      const messages = [];

      if (newCandidates > 0) {
        messages.push(
          `${newCandidates} new candidate${
            newCandidates === 1 ? "" : "s"
          }`,
        );
      }

      if (updatedCandidates > 0) {
        messages.push(
          `${updatedCandidates} crafted candidate${
            updatedCandidates === 1 ? "" : "s"
          } updated`,
        );
      }

      if (newEquippedSlots > 0) {
        messages.push(
          `${newEquippedSlots} equipped slot${
            newEquippedSlots === 1 ? "" : "s"
          } updated`,
        );
      }

      if (messages.length > 0) {
        status = `Captured ${messages.join(" · ")}`;
        saveState();
        return;
      }

      if (manual && (!context || contextItem)) {
        status = "Item already captured";
        updatePanel();
        return;
      }
    }

    if (manual) {
      status = context
        ? "Waiting for the clicked item's tooltip"
        : "No open item tooltip found";
      updatePanel();
    }
  }

  function captureOpenAsEquipped() {
    const visibleItems = getVisibleParsedItems();

    if (visibleItems.length === 0) {
      status =
        "No open tooltip found — open one equipped item first";
      updatePanel();
      return;
    }

    const explicitlyMarked = visibleItems.filter(
      (item) => item.equipped,
    );

    let item = null;

    if (visibleItems.length === 1) {
      item = visibleItems[0];
    } else if (explicitlyMarked.length === 1) {
      item = explicitlyMarked[0];
    }

    if (!item) {
      status =
        "Multiple unlabelled items are visible — close the comparison and open the equipped item directly";
      updatePanel();
      return;
    }

    const changed = recordEquipped({
      ...item,
      equipped: true,
    });

    maybeCompleteLoadoutScan();

    status = changed
      ? `Set equipped ${item.slot}: ${item.name}`
      : `${item.slot} already set to ${item.name}`;

    saveState();
  }

  function promoteSoleCandidatesForMissingSlots() {
    const promotions = [];

    for (const slot of missingEquippedSlots()) {
      const matches = state.candidates.filter(
        (candidate) => candidate.slot === slot,
      );

      if (matches.length === 1) {
        promotions.push(matches[0]);
      }
    }

    if (promotions.length === 0) {
      status =
        "No missing slot has exactly one stored candidate";
      updatePanel();
      return;
    }

    const summary = promotions
      .map((item) => `${item.slot}: ${item.name}`)
      .join("\n");

    if (
      !confirm(
        `Set these sole candidates as equipped?\n\n${summary}`,
      )
    ) {
      return;
    }

    for (const item of promotions) {
      recordEquipped({
        ...item,
        equipped: true,
      });
    }

    maybeCompleteLoadoutScan();

    status =
      `Set ${promotions.length} missing equipped slot${
        promotions.length === 1 ? "" : "s"
      }`;

    saveState();
  }

  function knownItems() {
    return [
      ...equippedItems(),
      ...state.candidates,
    ];
  }

  function operationForLine(line) {
    const upper = normalise(line).toUpperCase();

    return CRAFT_OPERATIONS.find(
      (operation) =>
        upper === operation.label ||
        upper.startsWith(`${operation.label} `) ||
        upper.startsWith(`${operation.label}:`),
    ) || null;
  }

  function resemblesEnhancingPanel(element) {
    const text = normalise(element?.innerText);

    if (text.length < 120 || text.length > 35000) {
      return false;
    }

    const upper = text.toUpperCase();
    const operationHits = CRAFT_OPERATIONS.filter(
      (operation) => upper.includes(operation.label),
    ).length;
    const knownNamePresent = knownItems().some(
      (item) =>
        item.name &&
        upper.includes(item.name.toUpperCase()),
    );
    const operationControlHits = [
      ...element.querySelectorAll(
        "button, [role='button'], input, select",
      ),
    ].filter((control) => {
      if (!isElementVisible(control)) {
        return false;
      }

      const controlText = normalise(
        control.textContent ||
        control.getAttribute("aria-label") ||
        control.getAttribute("title") ||
        control.getAttribute("value") ||
        "",
      ).toUpperCase();

      return CRAFT_OPERATIONS.some(
        (operation) => controlText.includes(operation.label),
      );
    }).length;
    const rootHint = [
      element.id,
      typeof element.className === "string"
        ? element.className
        : "",
      element.getAttribute("aria-label"),
    ].join(" ").toLowerCase();
    const hasItemIdentity = Boolean(
      element.querySelector("[data-item-id]") ||
      knownNamePresent ||
      activeCraftContext,
    );

    return (
      upper.includes("STABILITY") &&
      operationHits >= 3 &&
      hasItemIdentity &&
      (
        operationControlHits >= 1 ||
        /enhanc|craft/.test(rootHint)
      )
    );
  }

  function findEnhancingRoots() {
    const candidates = new Set(
      document.querySelectorAll(
        [
          "dialog",
          "[role='dialog']",
          "[aria-modal='true']",
          "[class*='enhanc']",
          "[class*='Enhanc']",
          "[id*='enhanc']",
          "[id*='Enhanc']",
          "[class*='craft']",
          "[class*='Craft']",
          "[id*='craft']",
          "[id*='Craft']",
        ].join(", "),
      ),
    );

    // Unknown markup fallback: walk upward from visible controls whose
    // labels clearly identify a crafting operation.
    for (const control of document.querySelectorAll(
      "button, [role='button'], input[type='button'], input[type='submit']",
    )) {
      if (!isElementVisible(control)) {
        continue;
      }

      const controlText = normalise(
        control.textContent ||
        control.getAttribute("aria-label") ||
        control.getAttribute("title") ||
        control.getAttribute("value") ||
        "",
      ).toUpperCase();

      if (
        !CRAFT_OPERATIONS.some(
          (operation) => controlText.includes(operation.label),
        )
      ) {
        continue;
      }

      let ancestor = control.parentElement;

      for (let depth = 0; ancestor && depth < 8; depth += 1) {
        if (isVisible(ancestor)) {
          candidates.add(ancestor);
        }
        ancestor = ancestor.parentElement;
      }
    }

    const matches = [...candidates]
      .filter(isVisible)
      .filter(resemblesEnhancingPanel);

    return matches.filter(
      (element) =>
        !matches.some(
          (other) =>
            other !== element && element.contains(other),
        ),
    );
  }

  function safeDataset(element) {
    const entries = Object.entries(element?.dataset || {})
      .slice(0, 30)
      .filter(([, value]) =>
        typeof value === "string" && value.length <= 300,
      );

    return Object.fromEntries(entries);
  }

  function controlLabel(control) {
    const aria = normalise(
      control.getAttribute("aria-label") ||
      control.getAttribute("title") ||
      "",
    );

    if (aria) {
      return aria;
    }

    if (control.id) {
      const escapedId = globalThis.CSS?.escape
        ? CSS.escape(control.id)
        : control.id.replace(/(["\\])/g, "\\$1");
      const labelled = document.querySelector(
        `label[for="${escapedId}"]`,
      );

      if (labelled) {
        return normalise(labelled.textContent);
      }
    }

    const wrappingLabel = control.closest("label");

    if (wrappingLabel) {
      return normalise(wrappingLabel.textContent);
    }

    return normalise(
      control.previousElementSibling?.textContent || "",
    );
  }

  function captureControls(root) {
    const controls = [];

    for (const control of root.querySelectorAll(
      "button, input, select, textarea, [role='button'], [role='checkbox'], [role='radio']",
    )) {
      if (
        !(control instanceof HTMLElement) ||
        !isElementVisible(control)
      ) {
        continue;
      }

      const record = {
        tag: control.tagName.toLowerCase(),
        type: control.getAttribute("type") ||
          control.getAttribute("role") || null,
        label: controlLabel(control) || null,
        text: normalise(control.textContent || "") || null,
        name: control.getAttribute("name") || null,
        id: control.id || null,
        disabled: Boolean(control.disabled) ||
          control.getAttribute("aria-disabled") === "true",
        dataset: safeDataset(control),
      };

      if (control instanceof HTMLInputElement) {
        record.checked = control.checked;
        record.value = control.type === "password"
          ? null
          : control.value;
      } else if (control instanceof HTMLSelectElement) {
        record.value = control.value;
        record.selectedText = normalise(
          control.selectedOptions[0]?.textContent || "",
        ) || null;
      } else if (control instanceof HTMLTextAreaElement) {
        record.value = control.value;
      } else {
        record.pressed = control.getAttribute("aria-pressed");
        record.checked = control.getAttribute("aria-checked");
      }

      const parsedCosts = parseCraftCostsDataset(
        control.dataset?.craftCosts,
      );

      if (parsedCosts.length > 0) {
        record.costs = parsedCosts;
      }

      controls.push(record);
    }

    return controls.slice(0, 150);
  }

  function parseCompactNumber(text) {
    const match = String(text || "")
      .replaceAll(",", "")
      .match(/^([\d.]+)\s*([KMBTQ])?$/i);

    if (!match) {
      return null;
    }

    const multipliers = {
      K: 1e3,
      M: 1e6,
      B: 1e9,
      T: 1e12,
      Q: 1e15,
    };
    const suffix = match[2]?.toUpperCase() || null;

    return Number(match[1]) * (suffix ? multipliers[suffix] : 1);
  }

  function parseCraftCostsDataset(value) {
    if (typeof value !== "string" || !value.trim()) {
      return [];
    }

    try {
      const parsed = JSON.parse(value);

      if (!Array.isArray(parsed)) {
        return [];
      }

      return parsed
        .map((cost) => ({
          resource: normalise(cost?.label) || null,
          amountText: normalise(cost?.amount) || null,
          amount: parseCompactNumber(normalise(cost?.amount)),
          hasEnough: typeof cost?.has === "boolean"
            ? cost.has
            : null,
        }))
        .filter((cost) => cost.resource && cost.amountText);
    } catch (error) {
      console.warn(
        "[IH Capture] Could not parse data-craft-costs:",
        error,
      );
      return [];
    }
  }

  function costsForControl(control) {
    if (!control) {
      return [];
    }

    if (Array.isArray(control.costs)) {
      return control.costs;
    }

    return parseCraftCostsDataset(
      control.dataset?.craftCosts,
    );
  }

  function parseCosts(lines) {
    const resourcePattern = CRAFT_RESOURCE_NAMES
      .map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("|");
    const regex = new RegExp(
      `([\\d,.]+\\s*[KMBTQ]?)\\s*(${resourcePattern})`,
      "gi",
    );
    const costs = [];

    for (const line of lines) {
      for (const match of line.matchAll(regex)) {
        costs.push({
          amountText: normalise(match[1]),
          amount: parseCompactNumber(normalise(match[1])),
          resource: match[2],
          rawText: line,
          hasEnough: null,
        });
      }
    }

    return costs;
  }

  function controlById(controls, id) {
    return controls.find((control) => control.id === id) || null;
  }

  function summariseCraftControl(control, operationKey) {
    if (!control) {
      return null;
    }

    const operationLabels = {
      lockAffix: "LOCK AFFIX",
      refactor: "REFACTOR",
      versionUpgrade: "VERSION UPGRADE",
      biasReroll: "BIAS REROLL",
      augment: "AUGMENT",
      prune: "PRUNE",
      compile: "COMPILE",
    };
    const summary = {
      operationKey,
      buttonId: control.id || null,
      label: operationLabels[operationKey] || control.text || null,
      domLabel: control.label || null,
      text: control.text || null,
      disabled: Boolean(control.disabled),
      available: !control.disabled,
      costs: costsForControl(control),
    };

    const chanceMatch = String(control.text || "")
      .match(/\((\d+(?:\.\d+)?)%\)/);

    if (chanceMatch) {
      const percent = Number(chanceMatch[1]);

      if (operationKey === "versionUpgrade") {
        summary.chancePercent = percent;
      } else {
        summary.displayedPercent = percent;
      }
    }

    return summary;
  }

  function operationRawLines(lines, operationLabel) {
    const index = lines.findIndex((line) =>
      line.toUpperCase().startsWith(operationLabel),
    );

    return index >= 0 ? [lines[index]] : [];
  }

  function controlsForSnapshotIdentity(controls) {
    return controls.map((control) => {
      const { costs, ...rawControl } = control;

      return rawControl;
    });
  }

  function parseGlobalCraftOperations(lines, controls) {
    const definitions = {
      biasReroll: {
        label: "BIAS REROLL",
        id: "craft-bias-btn",
      },
      augment: {
        label: "AUGMENT",
        id: "craft-augment-btn",
      },
      prune: {
        label: "PRUNE",
        id: "craft-annul-btn",
      },
      compile: {
        label: "COMPILE",
        id: "craft-compile-btn",
      },
    };
    const operations = {};

    for (const [key, definition] of Object.entries(definitions)) {
      const control = controlById(controls, definition.id);
      const summary = summariseCraftControl(control, key) || {
        operationKey: key,
        buttonId: definition.id,
        label: definition.label,
        text: null,
        disabled: null,
        available: null,
        costs: [],
      };

      summary.rawLines = operationRawLines(
        lines,
        definition.label,
      );
      summary.stabilityCost = null;
      summary.stabilityCostDisplayed = false;

      if (key === "compile") {
        const compileLine = summary.text || summary.rawLines[0] || "";
        const bonusMatch = compileLine.match(/\+(\d+(?:\.\d+)?)%/);

        summary.bonusPercent = bonusMatch
          ? Number(bonusMatch[1])
          : null;
        delete summary.displayedPercent;
      }

      if (key === "biasReroll") {
        const select = controlById(controls, "craft-bias-select");

        summary.selectedBias = select?.selectedText || null;
        summary.selectedBiasValue = select?.value || null;
      }

      operations[key] = summary;
    }

    return operations;
  }

  function numberFromCraftText(value) {
    const parsed = Number(
      String(value || "").replaceAll(",", ""),
    );

    return Number.isFinite(parsed) ? parsed : null;
  }

  function parseCraftStats(statsText) {
    const stats = [];
    const regex = /([+-]?\d[\d,.]*)(%)?\s+([^\[]+?)\s+\[\s*([+-]?\d[\d,.]*)(%)?\s*(?:-|–|to)\s*([+-]?\d[\d,.]*)(%)?\s*\]/gi;

    for (const match of String(statsText || "").matchAll(regex)) {
      const current = numberFromCraftText(match[1]);
      const rangeMin = numberFromCraftText(match[4]);
      const rangeMax = numberFromCraftText(match[6]);
      const isPercent = Boolean(match[2] || match[5] || match[7]);
      const rangeSpan = rangeMin != null && rangeMax != null
        ? rangeMax - rangeMin
        : null;
      const rangePosition = (
        current != null &&
        rangeMin != null &&
        rangeSpan != null &&
        rangeSpan > 0
      )
        ? Math.max(0, Math.min(1, (current - rangeMin) / rangeSpan))
        : null;

      stats.push({
        name: normalise(match[3]),
        current,
        rangeMin,
        rangeMax,
        unit: isPercent ? "percent" : "flat",
        rangePosition,
        rawText: normalise(match[0]),
      });
    }

    return stats;
  }

  function looksLikePanelAffixStart(lines, index) {
    const name = lines[index];
    const tier = lines[index + 1];
    const stats = lines[index + 2];

    return Boolean(
      name &&
      tier &&
      stats &&
      !operationForLine(name) &&
      !["PREFIXES", "SUFFIXES"].includes(name.toUpperCase()) &&
      /^T\d+$/i.test(tier) &&
      /\[[^\]]+\]/.test(stats),
    );
  }

  function parsePanelAffixCounts(lines) {
    const header = lines.find((line) =>
      /\b\d+P\s*\/\s*\d+S\b/i.test(line),
    );
    const match = String(header || "")
      .match(/\b(\d+)P\s*\/\s*(\d+)S\b/i);

    if (!match) {
      return null;
    }

    const prefix = Number(match[1]);
    const suffix = Number(match[2]);

    return {
      prefix,
      suffix,
      total: prefix + suffix,
    };
  }

  function parseCraftAffixes(lines, controls) {
    const affixes = [];
    const indexes = {
      prefix: 0,
      suffix: 0,
    };
    let kind = null;
    let index = 0;

    while (index < lines.length) {
      const upper = lines[index].toUpperCase();

      if (upper === "PREFIXES") {
        kind = "prefix";
        index += 1;
        continue;
      }

      if (upper === "SUFFIXES") {
        kind = "suffix";
        index += 1;
        continue;
      }

      if (!kind || !looksLikePanelAffixStart(lines, index)) {
        index += 1;
        continue;
      }

      const affixIndex = indexes[kind];
      const name = lines[index];
      const tier = Number(lines[index + 1].slice(1));
      const statsText = lines[index + 2];
      let end = index + 3;

      while (
        end < lines.length &&
        !["PREFIXES", "SUFFIXES"].includes(lines[end].toUpperCase()) &&
        !looksLikePanelAffixStart(lines, end)
      ) {
        end += 1;
      }

      const rawLines = lines.slice(index, end);
      const controlSuffix = `${kind}-${affixIndex}`;
      const lock = summariseCraftControl(
        controlById(
          controls,
          `craft-lock-btn-${controlSuffix}`,
        ),
        "lockAffix",
      );
      const refactor = summariseCraftControl(
        controlById(
          controls,
          `craft-masterwork-btn-${controlSuffix}`,
        ),
        "refactor",
      );
      const versionUpgrade = summariseCraftControl(
        controlById(
          controls,
          `craft-tier-promote-btn-${controlSuffix}`,
        ),
        "versionUpgrade",
      );
      const rawUpgradeLine = rawLines.find((line) =>
        line.toUpperCase().startsWith("VERSION UPGRADE"),
      );
      const chanceMatch = String(
        versionUpgrade?.text || rawUpgradeLine || "",
      ).match(/\((\d+(?:\.\d+)?)%\)/);
      const versionUpgradeChancePercent =
        versionUpgrade?.chancePercent ??
        (chanceMatch ? Number(chanceMatch[1]) : null);

      affixes.push({
        kind,
        index: affixIndex,
        reference: `${kind}-${affixIndex}`,
        name,
        tier,
        statsText,
        stats: parseCraftStats(statsText),
        versionUpgradeChancePercent,
        controls: {
          lock,
          refactor,
          versionUpgrade,
        },
        rawLines,
      });

      indexes[kind] += 1;
      index = end;
    }

    return affixes;
  }

  function buildCraftValidation(lines, affixes) {
    const expectedAffixCounts = parsePanelAffixCounts(lines);
    const parsedAffixCounts = {
      prefix: affixes.filter((affix) =>
        affix.kind === "prefix",
      ).length,
      suffix: affixes.filter((affix) =>
        affix.kind === "suffix",
      ).length,
      total: affixes.length,
    };
    const affixCountMatchesPanel = expectedAffixCounts
      ? expectedAffixCounts.prefix === parsedAffixCounts.prefix &&
        expectedAffixCounts.suffix === parsedAffixCounts.suffix
      : null;
    const perAffixControlsComplete = affixes.every((affix) =>
      affix.controls.lock &&
      affix.controls.refactor &&
      affix.controls.versionUpgrade,
    );
    const statRangesParsed = affixes.every((affix) =>
      affix.stats.length > 0,
    );

    return {
      parserVersion: "0.6.1",
      expectedAffixCounts,
      parsedAffixCounts,
      affixCountMatchesPanel,
      perAffixControlsComplete,
      statRangesParsed,
      structuredCaptureComplete:
        affixCountMatchesPanel !== false &&
        perAffixControlsComplete &&
        statRangesParsed,
    };
  }

  function upgradeCraftSnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== "object") {
      return snapshot;
    }

    const rawText = normalise(snapshot.rawText || "");

    if (!rawText) {
      return snapshot;
    }

    const lines = rawText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    const controls = Array.isArray(snapshot.controls)
      ? snapshot.controls.map((control) => {
          const costs = costsForControl(control);

          return costs.length > 0
            ? { ...control, costs }
            : control;
        })
      : [];
    const affixes = parseCraftAffixes(lines, controls);

    const snapshotKey = hashString(JSON.stringify({
      itemReference: snapshot.itemReference,
      rawText,
      controls: controlsForSnapshotIdentity(controls),
      rootProbe: snapshot.rootProbe,
    }));

    return {
      ...snapshot,
      snapshotKey,
      affixes,
      operations: parseGlobalCraftOperations(lines, controls),
      controls,
      validation: buildCraftValidation(lines, affixes),
    };
  }

  function resolveCraftItemReference(text, root) {
    const upper = text.toUpperCase();
    const known = knownItems().find(
      (item) =>
        item.name &&
        upper.includes(item.name.toUpperCase()),
    );
    const domNode = root.querySelector("[data-item-id]") ||
      root.closest("[data-item-id]");

    return {
      domItemId: domNode?.getAttribute("data-item-id") ||
        activeCraftContext?.itemId ||
        known?.domItemId ||
        null,
      itemKey: known?.key ||
        activeCraftContext?.itemKey ||
        null,
      name: known?.name ||
        activeCraftContext?.name ||
        null,
      slot: known?.slot ||
        activeCraftContext?.slot ||
        null,
      contextSource: known
        ? "panel-text-match"
        : activeCraftContext
          ? "enhance-click-context"
          : "unresolved",
    };
  }

  function parseEnhancingPanel(root) {
    const rawText = normalise(root.innerText);
    const lines = rawText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    const itemReference = resolveCraftItemReference(rawText, root);
    const stabilityLine = lines.find((line) =>
      /^Stability:/i.test(line),
    ) || lines.find((line) =>
      /stability\s*\d+\s*\/\s*\d+/i.test(line),
    );
    const stabilityMatch = String(stabilityLine || "")
      .match(/(?:Stability:\s*)?(\d+)\s*\/\s*(\d+)/i);
    const controls = captureControls(root);
    const affixes = parseCraftAffixes(lines, controls);
    const operations = parseGlobalCraftOperations(lines, controls);
    const validation = buildCraftValidation(lines, affixes);
    const rootProbe = {
      tag: root.tagName.toLowerCase(),
      id: root.id || null,
      className: typeof root.className === "string"
        ? root.className
        : null,
      role: root.getAttribute("role"),
      dataset: safeDataset(root),
    };
    const capturedAt = new Date().toISOString();
    const snapshotKey = hashString(JSON.stringify({
      itemReference,
      rawText,
      controls: controlsForSnapshotIdentity(controls),
      rootProbe,
    }));

    return {
      snapshotKey,
      capturedAt,
      lastSeenAt: capturedAt,
      itemReference,
      stabilityCurrent: stabilityMatch
        ? Number(stabilityMatch[1])
        : null,
      stabilityMaximum: stabilityMatch
        ? Number(stabilityMatch[2])
        : null,
      affixes,
      operations,
      controls,
      validation,
      rootProbe,
      rawText,
    };
  }

  function recordCraftSnapshot(snapshot) {
    const existing = state.craftingSnapshots.find(
      (entry) => entry.snapshotKey === snapshot.snapshotKey,
    );

    if (existing) {
      existing.lastSeenAt = snapshot.lastSeenAt;
      return false;
    }

    state.craftingSnapshots.push(snapshot);

    if (state.craftingSnapshots.length > MAX_CRAFT_SNAPSHOTS) {
      state.craftingSnapshots.splice(
        0,
        state.craftingSnapshots.length - MAX_CRAFT_SNAPSHOTS,
      );
    }

    activeCraftContext = {
      itemId: snapshot.itemReference.domItemId,
      itemKey: snapshot.itemReference.itemKey,
      name: snapshot.itemReference.name,
      slot: snapshot.itemReference.slot,
      capturedAt: Date.now(),
    };

    return true;
  }

  function captureEnhancingPanel({ manual = false } = {}) {
    const roots = findEnhancingRoots();
    let added = 0;

    for (const root of roots) {
      const snapshot = parseEnhancingPanel(root);

      if (recordCraftSnapshot(snapshot)) {
        added += 1;
      }
    }

    if (added > 0) {
      status = `Captured ${added} crafting snapshot${
        added === 1 ? "" : "s"
      }`;
      saveState();
      return;
    }

    if (manual) {
      status = roots.length > 0
        ? "Crafting panel already captured"
        : "No user-opened Enhancing panel found";
      updatePanel();
    }
  }

  function captureAllVisible() {
    captureVisible();
    captureEnhancingPanel();
  }

  function scheduleCapture() {
    if (!autoCapture) {
      return;
    }

    clearTimeout(scanTimer);
    scanTimer = setTimeout(
      () => captureAllVisible(),
      180,
    );
  }

  function equippedItems() {
    return SLOT_NAMES
      .map((slot) => state.equippedBySlot[slot])
      .filter(Boolean);
  }

  function missingEquippedSlots() {
    return SLOT_NAMES.filter(
      (slot) => !state.equippedBySlot[slot],
    );
  }

  function maybeCompleteLoadoutScan() {
    if (
      state.loadoutScan.active &&
      missingEquippedSlots().length === 0
    ) {
      state.loadoutScan.active = false;
      status = "Loadout scan complete: 8/8 slots";
    }
  }

  function beginLoadoutScan() {
    const existingCount = equippedItems().length;

    if (
      existingCount > 0 &&
      !confirm(
        `Reset the ${existingCount} captured equipped slots? Candidate items will be kept.`,
      )
    ) {
      return;
    }

    state.equippedBySlot = {};
    state.loadoutScan = {
      active: true,
      startedAt: new Date().toISOString(),
    };

    status =
      "Loadout scan started — click each equipped slot normally";

    saveState();
  }

  function stopLoadoutScan() {
    state.loadoutScan.active = false;
    status =
      `Loadout checklist stopped at ${equippedItems().length}/8`;
    saveState();
  }

  function clearCandidates() {
    if (
      state.candidates.length > 0 &&
      !confirm(
        `Clear ${state.candidates.length} candidate items? The equipped loadout and crafting snapshots will be kept.`,
      )
    ) {
      return;
    }

    state.candidates = [];
    status = "Candidates cleared";
    saveState();
  }

  function clearCraftingSnapshots() {
    if (
      state.craftingSnapshots.length > 0 &&
      !confirm(
        `Clear ${state.craftingSnapshots.length} crafting snapshots? Items and revision history will be kept.`,
      )
    ) {
      return;
    }

    state.craftingSnapshots = [];
    activeCraftContext = null;
    status = "Crafting snapshots cleared";
    saveState();
  }

  function clearEverything() {
    const total =
      state.candidates.length +
      equippedItems().length +
      state.craftingSnapshots.length;

    if (
      total > 0 &&
      !confirm(
        `Clear all ${state.candidates.length} candidates, ${equippedItems().length} equipped items, and ${state.craftingSnapshots.length} crafting snapshots?`,
      )
    ) {
      return;
    }

    state = emptyState();
    activeCraftContext = null;
    lastOpenedItemContext = null;
    status = "All captured data cleared";
    saveState();
  }

  function exportPayload() {
    const loadoutItems = equippedItems();
    const missingSlots = missingEquippedSlots();

    return {
      schemaVersion: 4,
      exportedAt: new Date().toISOString(),
      source: "idle-hacking-item-loadout-capture",
      sourceVersion: "0.6.1",
      sourceUrl: location.href,
      loadout: {
        complete: missingSlots.length === 0,
        capturedSlotCount: loadoutItems.length,
        missingSlots,
        items: loadoutItems,
      },
      candidates: state.candidates,
      crafting: {
        capturedSnapshotCount: state.craftingSnapshots.length,
        snapshots: state.craftingSnapshots,
      },
      itemRevisions: state.itemRevisions,
    };
  }

  function formatItem(item, heading) {
    return [
      heading,
      item.name,
      item.rarity,
      item.slot,
      `Item Level: ${item.itemLevel}${
        item.ratio != null
          ? ` (Ratio: ${item.ratio})`
          : ""
      }`,
      `Required Level: ${item.requiredLevel}`,
      item.compiledPercent != null
        ? `Compiled: +${item.compiledPercent.toFixed(2)}%`
        : null,
      `Stability: ${item.stabilityCurrent} / ${item.stabilityMaximum}`,
      item.implicitText,
      ...item.affixes.map((affix) => affix.rawText),
    ]
      .filter(Boolean)
      .join("\n");
  }

  function compactFullText() {
    const loadoutItems = equippedItems();
    const missingSlots = missingEquippedSlots();

    const header = [
      "IDLE HACKING LOADOUT & CANDIDATE EXPORT",
      `Exported: ${new Date().toISOString()}`,
      `Equipped: ${loadoutItems.length}/8`,
      `Candidates: ${state.candidates.length}`,
      `Craft snapshots: ${state.craftingSnapshots.length}`,
      missingSlots.length
        ? `Missing equipped slots: ${missingSlots.join(", ")}`
        : "Loadout complete",
    ].join("\n");

    const loadoutSection = loadoutItems.length
      ? [
          "CURRENT EQUIPPED LOADOUT",
          ...loadoutItems.map((item) =>
            formatItem(item, `[EQUIPPED: ${item.slot}]`),
          ),
        ].join("\n\n----------------------------------------\n\n")
      : "CURRENT EQUIPPED LOADOUT\nNo equipped items captured.";

    const candidateSection = state.candidates.length
      ? [
          "CANDIDATES",
          ...state.candidates.map((item, index) =>
            formatItem(
              item,
              `[CANDIDATE ${index + 1}: ${item.slot}]`,
            ),
          ),
        ].join("\n\n----------------------------------------\n\n")
      : "CANDIDATES\nNo candidate items captured.";

    return [
      header,
      loadoutSection,
      candidateSection,
    ].join("\n\n========================================\n\n");
  }

  function compactLoadoutText() {
    const loadoutItems = equippedItems();
    const missingSlots = missingEquippedSlots();

    const header = [
      "IDLE HACKING EQUIPPED LOADOUT EXPORT",
      `Exported: ${new Date().toISOString()}`,
      `Equipped: ${loadoutItems.length}/8`,
      missingSlots.length
        ? `Missing slots: ${missingSlots.join(", ")}`
        : "Loadout complete",
    ].join("\n");

    const body = loadoutItems.length
      ? loadoutItems
          .map((item) =>
            formatItem(item, `[EQUIPPED: ${item.slot}]`),
          )
          .join(
            "\n\n========================================\n\n",
          )
      : "No equipped items captured.";

    return `${header}\n\n${body}`;
  }

  async function copyText(text, successMessage) {
    try {
      await navigator.clipboard.writeText(text);
      status = successMessage;
    } catch (error) {
      console.error(
        "[IH Capture] Clipboard failed:",
        error,
      );
      status = "Clipboard failed; use Download JSON";
    }

    updatePanel();
  }

  function downloadJson() {
    const blob = new Blob(
      [JSON.stringify(exportPayload(), null, 2)],
      { type: "application/json" },
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download =
      `idle-hacking-capture-${new Date()
        .toISOString()
        .replace(/[:.]/g, "-")}.json`;

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);

    status = "Downloaded JSON";
    updatePanel();
  }

  function createPanel() {
    document.querySelector("#ih-capture-panel")?.remove();

    const panel = document.createElement("section");
    panel.id = "ih-capture-panel";

    panel.innerHTML = `
      <div class="ihc-header">
        <strong>IH Item Capture</strong>
        <button data-action="collapse" title="Collapse">−</button>
      </div>

      <div class="ihc-body">
        <div class="ihc-counts">
          <span data-role="candidate-count">Candidates: 0</span>
          <span data-role="loadout-count">Equipped: 0/8</span>
          <span data-role="craft-count">Craft: 0</span>
        </div>

        <div class="ihc-scan" data-role="scan-status"></div>
        <div class="ihc-missing" data-role="missing"></div>

        <div class="ihc-actions">
          <button data-action="capture">Capture item</button>
          <button data-action="capture-crafting">Capture crafting</button>
          <button data-action="set-equipped">Set open equipped (fallback)</button>
          <button data-action="scan-loadout">Reset/start loadout</button>
          <button data-action="fill-sole">Use sole missing candidates</button>
          <button data-action="copy-crafting">Copy crafting JSON</button>
          <button data-action="copy-full">Copy full export</button>
          <button data-action="copy-loadout">Copy loadout only</button>
          <button data-action="copy-json">Copy JSON</button>
          <button data-action="download">Download JSON</button>
          <button data-action="toggle-auto">Pause auto</button>
          <button data-action="clear-candidates">Clear candidates</button>
          <button data-action="clear-crafting">Clear crafting</button>
          <button data-action="clear-all" class="danger wide">Clear all</button>
        </div>

        <div class="ihc-status" data-role="status">Ready</div>
      </div>
    `;

    panel.addEventListener("click", (event) => {
      const button = event.target.closest(
        "button[data-action]",
      );

      if (!button) {
        return;
      }

      const action = button.dataset.action;

      if (action === "capture") {
        captureVisible({ manual: true });
      }

      if (action === "capture-crafting") {
        captureEnhancingPanel({ manual: true });
      }

      if (action === "set-equipped") {
        captureOpenAsEquipped();
      }

      if (action === "scan-loadout") {
        beginLoadoutScan();
      }

      if (action === "fill-sole") {
        promoteSoleCandidatesForMissingSlots();
      }

      if (action === "copy-full") {
        copyText(
          compactFullText(),
          `Copied ${equippedItems().length} equipped and ${state.candidates.length} candidates`,
        );
      }

      if (action === "copy-loadout") {
        copyText(
          compactLoadoutText(),
          `Copied equipped loadout (${equippedItems().length}/8)`,
        );
      }

      if (action === "copy-crafting") {
        copyText(
          JSON.stringify({
            schemaVersion: 4,
            exportedAt: new Date().toISOString(),
            sourceVersion: "0.6.1",
            crafting: {
              capturedSnapshotCount: state.craftingSnapshots.length,
              snapshots: state.craftingSnapshots,
            },
            itemRevisions: state.itemRevisions,
          }, null, 2),
          `Copied ${state.craftingSnapshots.length} crafting snapshots`,
        );
      }

      if (action === "copy-json") {
        copyText(
          JSON.stringify(exportPayload(), null, 2),
          "Copied structured JSON",
        );
      }

      if (action === "download") {
        downloadJson();
      }

      if (action === "toggle-auto") {
        autoCapture = !autoCapture;
        status = autoCapture
          ? "Automatic capture enabled"
          : "Automatic capture paused";
        updatePanel();
      }

      if (action === "clear-candidates") {
        clearCandidates();
      }

      if (action === "clear-crafting") {
        clearCraftingSnapshots();
      }

      if (action === "clear-all") {
        clearEverything();
      }

      if (action === "collapse") {
        panel.classList.toggle("collapsed");
        button.textContent =
          panel.classList.contains("collapsed")
            ? "+"
            : "−";
      }
    });

    document.body.appendChild(panel);
    updatePanel();
  }

  function updatePanel() {
    const panel = document.querySelector(
      "#ih-capture-panel",
    );

    if (!panel) {
      return;
    }

    const loadoutCount = equippedItems().length;
    const missingSlots = missingEquippedSlots();

    panel.querySelector(
      "[data-role='candidate-count']",
    ).textContent =
      `Candidates: ${state.candidates.length}`;

    panel.querySelector(
      "[data-role='loadout-count']",
    ).textContent =
      `Equipped: ${loadoutCount}/8`;

    panel.querySelector(
      "[data-role='craft-count']",
    ).textContent =
      `Craft: ${state.craftingSnapshots.length}`;

    panel.querySelector(
      "[data-role='scan-status']",
    ).textContent = loadoutCount === 8
      ? "Loadout complete"
      : state.loadoutScan.active
        ? "Loadout scan active: click equipped slots normally"
        : "Loadout incomplete";

    panel.querySelector(
      "[data-role='missing']",
    ).textContent = missingSlots.length
      ? `Missing: ${missingSlots.join(", ")}`
      : "All equipment slots captured";

    panel.querySelector(
      "[data-role='status']",
    ).textContent = status;

    panel.querySelector(
      "[data-action='toggle-auto']",
    ).textContent = autoCapture
      ? "Pause auto"
      : "Resume auto";

  }

  function addStyles() {
    const style = document.createElement("style");

    style.textContent = `
      #ih-capture-panel {
        position: fixed;
        left: 14px;
        bottom: 14px;
        z-index: 2147483647;
        width: 310px;
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

      #ih-capture-panel .ihc-counts {
        display: grid;
        grid-template-columns: repeat(3, auto);
        justify-content: space-between;
        gap: 5px;
        margin-bottom: 5px;
        color: #8ecbff;
      }

      #ih-capture-panel .ihc-scan {
        color: #c9d9e7;
        margin-bottom: 3px;
      }

      #ih-capture-panel .ihc-missing {
        color: #8fa7ba;
        margin-bottom: 7px;
        line-height: 1.35;
      }

      #ih-capture-panel .ihc-actions {
        display: grid;
        grid-template-columns: 1fr 1fr;
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

      #ih-capture-panel button.danger {
        border-color: #8a4a55;
      }

      #ih-capture-panel button.wide {
        grid-column: 1 / -1;
      }

      #ih-capture-panel .ihc-status {
        min-height: 1.2em;
        margin-top: 7px;
        color: #a9bac8;
      }
    `;

    document.head.appendChild(style);
  }

  const observer = new MutationObserver(scheduleCapture);

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: [
      "class",
      "style",
      "hidden",
    ],
  });

  document.addEventListener(
    "click",
    (event) => {
      captureClickOrigin(event);
      scheduleCapture();

      // Allow for tooltip and Enhancing-panel transitions.
      setTimeout(() => captureAllVisible(), 350);
      setTimeout(() => captureAllVisible(), 750);
      setTimeout(() => captureEnhancingPanel(), 1200);
    },
    true,
  );

  document.addEventListener("keydown", (event) => {
    if (event.altKey && event.code === "KeyC") {
      event.preventDefault();
      captureVisible({ manual: true });
    }

    if (event.altKey && event.code === "KeyE") {
      event.preventDefault();
      captureOpenAsEquipped();
    }

    if (event.altKey && event.code === "KeyH") {
      event.preventDefault();
      captureEnhancingPanel({ manual: true });
    }
  });

  window.ihItemCapture = {
    capture: () =>
      captureVisible({ manual: true }),
    captureCrafting: () =>
      captureEnhancingPanel({ manual: true }),
    getState: () => structuredClone(state),
    getExport: () => structuredClone(exportPayload()),
    getCraftingSnapshots: () =>
      structuredClone(state.craftingSnapshots),
    beginLoadoutScan,
    stopLoadoutScan,
    captureOpenAsEquipped,
    captureClickOrigin,
    promoteSoleCandidatesForMissingSlots,
    copyFull: () =>
      copyText(
        compactFullText(),
        "Copied full export",
      ),
    copyLoadout: () =>
      copyText(
        compactLoadoutText(),
        "Copied loadout",
      ),
    clearCandidates,
    clearCraftingSnapshots,
    clearEverything,
  };

  addStyles();
  createPanel();
  scheduleCapture();

  console.info(
    "[IH Capture] v0.6.1 loaded. Item click-origin classification and passive Enhancing-panel snapshots are enabled.",
  );
})();
