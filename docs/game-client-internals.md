# Game Client Internals (recon findings, 22 July 2026)

How the Idle Hacking web client is built, from the source-probe runs and a read of the client JS. Basis for the v0.9.0 full-state capture. Local reference copies of the client scripts live in `vendor/game-js/` (git-ignored — their code, not ours to redistribute; re-fetch from `https://idlehacking.com/static/js/<name>.js` when stale).

## Architecture

- Plain unbundled JavaScript, one file per feature (`state.js`, `inventory.js`, `hacking.js`, `homelab.js`, `actions.js`, `ui.js`, ...), whitespace-minified with original identifiers intact. No React/Vue/webpack for game code.
- All client state arrives over a WebSocket (`openManagedWebSocket` in `state.js`) as JSON messages `{type, payload}`; gameplay actions are sends like `{type:"EQUIPMENT_AUGMENT", payload:{item_id}}`. The capture tool must never call these.
- State lives in **top-level `let`/`const` bindings** — global *lexical* bindings, not `window` properties. They are invisible to `Object.getOwnPropertyNames(window)` and to sandbox `unsafeWindow` property reads; reading them requires code evaluated in page scope (see `capture-tool.md`).

## Key state bindings (capture targets)

| Binding | File | Contents |
|---|---|---|
| `currentPlayer` | `state.js` | Whole save: `credits`, `stabilizers`, `hack_level`, `hack_exp`, `inventory`, `equipment`, `gear_sets`, `extended_stats`, homelab/premium/settings fields |
| `equipmentData` | `inventory.js` | Object keyed by slot name → equipped item object |
| `inventoryData` | `inventory.js` | `{items: [...], max_slots}` — every inventory item |
| `statsBreakdown` | `state.js` | Aggregated stat summary |
| `recentLossStreaks` | `hacking.js` | Loss-streak history entries (lazy-loaded; open the loss history UI once to populate) |

## Item object schema (fields observed in client code)

`item_id`/`id`, `name`, `rarity`, `slot`, `item_level`, `base_type`, `stability`/`stability_max`, `implicit_info`, `prefixes[]`, `suffixes[]`, `signature_id`/`signature_name`, `locked_affix_group`/`locked_affix_type`, `decompile_locked`, `market_listed`.

Affix entries carry `tier`, `value_min`/`value_max` (current-tier roll range), `type`, `resource`, `affix_group`, and `tier_promotion_chance` — i.e. **everything the enhance panel displays is client-side on the item**; craft costs are computed locally (`calcTierPromotion*Cost`). Nothing extra is fetched when the enhance screen opens, so full-state capture supersedes both tooltip-clicking and enhance-panel visits.

Combat-log exports (`last_10_losses` files) come from the game's own `buildCombatLogExportPayload` in `hacking.js`.

## Implications for the capture tool

- One page-scope read of the five bindings captures loadout + all inventory items + crafting data + resources in one action (`Capture all (full state)`, schema `idle-hacking-state-capture-v1`).
- The auth token is NOT in these bindings (it lives in `localStorage.idlehack_auth_token` and cookies) — state captures are safe to store in the repo.
- Stat-key naming in item effects: `hp_regen`, `damage_barrier`, `max_hp`, `crit_chance`, `*_multi` XP keys, etc. (see `formatTooltipStatLabel` in `inventory.js` for the display-name map).
