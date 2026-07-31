# Hacking Simulator — experiment protocol

Unlocked 29 July 2026 (Homelab install "Hacking Simulator", 5B cr + 3 hc).
This file is the operating manual: what the tool actually is, how its output
reaches the workspace, and the ordered experiments that use it.

## 1. What we actually have

The install ships two tools. **Only one of them is live.**

| Tool | Level | Status | What it does |
|---|---|---|---|
| **Software Profiler** | **1** | **LIVE** | 100 fights vs a **chosen enemy level** in a chosen zone, with the equipped loadout **or a saved gear set** |
| CI/CD Pipeline | 0 | **LOCKED — homelab 12** | Full-**streak** simulation with gear/zone customisation; 5 runs/day per level |

`hacking_simulator.daily_limit = 0` in the capture is the *pipeline's* budget,
not the profiler's. The Software Profiler has **no daily limit** — only a
**5-second cooldown** (`profiler_cooldown_ms: 5000`). That is ~720 runs/hour =
**72,000 simulated fights per hour, free**. It is by far the largest
measurement instrument this workspace has ever had.

Costs nothing per run. Uses no Stability, no credits, no hackcoin.

### Per-run output

Each run returns, and the userscript banks, all of:

- `wins`, `losses`, `win_rate` over `simulation_count` (100) fights
- `requested_enemy_level`, `zone_name`
- `most_common_loss_enemy_archetype` — which class killed you most
- **`first_victory`** and **`first_loss`** — two *fully logged* fights, each
  with `combat_log_compact` (every round: hits, misses, crits, damage,
  `prg`, `pcd`/`ecd`, barrier) **and `enemy_stats`** (the enemy's effective
  accuracy / evasion / defense / attack)

That last item is what makes the tool decisive: **`enemy_stats` gives us the
other side of every combat formula**, which the live ledger only ever had
incidentally.

### The regime constraint — read before fitting anything

The profiler simulates **fights at a chosen enemy level**, not a streak.
Whether HP carries between those fights is **unknown until measured**, and it
decides what the tool may be used for:

- if fights start at **full HP**, the profiler measures *single-fight win
  probability* and is **blind to attrition** — it may not be used to price
  Regen, Barrier or Max HP, whose whole value is across a streak;
- if HP **carries**, it models attrition too.

`ihlib.sim_regime_check()` answers this from the first run and `ih.py sims`
prints the verdict as its first line. **Experiment 0 exists solely to settle
it.** Do not skip it — this is the same class of error as the T3 tier cap and
the zone transition cost (`CLAUDE.md`, "state the regime a model was fitted
in").

Mitigation and hit reliability are measurable under *either* regime.

## 2. Getting the results into the workspace

One-time setup, then it is automatic.

1. **Update the userscript to v1.6.0.** Tampermonkey → dashboard → the IH
   Capture script → check for updates (it pulls from the hub at
   `localhost:8123`). Confirm the panel header reads `IH Capture v1.6.0`.
2. **Restart the hub** so it knows the new schema:
   `systemctl --user restart idle-hacking-capture-hub`
3. In the capture panel, press **`Sim capture: OFF`** so it reads **ON**.
   It persists across reloads.

From then on: every time the player presses **RUN** in the game's own
Simulator panel, the result is banked to `data/sim-runs/YYYY-MM-DD.jsonl`
within ~2 seconds. Nothing else to click.

- **`Send sim history now`** does a one-shot push that also reads the game's
  own IndexedDB store (`idlehack.hacking-simulator-history`, last 10 runs per
  mode). Use it to backfill runs made with sim capture off.
- Runs are deduped by a hash of the result body, so re-sending is harmless.
- **Safety boundary is unchanged.** The script only *observes* results the
  player asked the game to compute — it reads two page-scope bindings and a
  local IndexedDB store. It never sends `RUN_HACKING_SOFTWARE_PROFILER` or any
  other message. The player presses RUN; the tool never does.

Read it back with **`python3 scripts/ih.py sims`**.

## 3. Experiment 0 — establish the regime (2 minutes, MANDATORY FIRST)

**Do:** one profiler run. Zone `Corporate Network`, gear `CURRENTLY EQUIPPED`,
enemy level **2300**. Press RUN once.

**Then:** `python3 scripts/ih.py sims`

**Reads out:** the `REGIME:` line.

- `full-hp` → the profiler measures single-fight strength. Everything in §5
  and §6 is valid; **Regen/Barrier/MaxHP weights stay off-limits** until the
  CI/CD Pipeline lands.
- `carried-hp` → attrition is modelled; every weight becomes fittable.
- `mixed` / `unknown` → stop and report; something is not as assumed.

Also confirms plumbing works before any long sweep.

**Second check in the same run:** run the *same* configuration twice and
compare the two `first_victory.enemy_stats` blocks. If they match, enemy stats
are a pure function of enemy level and the sweep in §5 is clean. If they vary,
there is a hidden roll and we need more runs per level.

## 4. Experiment 1 — validate against the live ledger — **DONE 29 Jul 2026: deaths are ~100% attrition**

**Result: the player dies at median enemy level 1,798 (streak 117), where the profiler wins 300/300 at full HP.** Single-fight win probability stays at 100% until level ~2,300. So win rate is the WRONG A/B outcome for this build — use HP lost per fight and rounds per fight from the logged victory. See `decision-log.md`.

(original design below)

The profiler is a model until it reproduces something we already measured.
The stream ledger gives observed win rate by enemy level over 14,932 fights:

| enemy level | live win rate | n |
|---|---|---|
| 1900–1999 | 99.0% | 416 |
| 2000–2099 | 99.5% | 378 |
| 2100–2199 | 97.8% | 313 |
| 2200–2299 | 91.9% | 210 |
| 2300–2399 | 85.6% | 90 |

**Do:** one run each at enemy level **1950, 2050, 2150, 2250, 2350** (gear
`CURRENTLY EQUIPPED`, zone Corporate Network). 5 runs, ~30 seconds.

**Reads out:** profiler win rate vs live win rate at matched level.

This is not a pass/fail — **the gap is itself the measurement**:

- If the profiler starts fights at full HP (Exp 0), profiler win rate **minus**
  live win rate at the same enemy level **is the attrition penalty** — the
  share of the death ceiling caused by accumulated damage rather than by the
  final matchup being unwinnable. That decomposition is exactly what
  `CLAUDE.md` demands of long-streak loss analysis and has never been
  quantified.
- If the two curves coincide, attrition is negligible at these depths and the
  death ceiling is a pure matchup problem — which would redirect the whole
  build away from regeneration.

Either result changes standing advice. Record it in `decision-log.md`.

## 5. Experiment 2 — enemy-level sweep (5 minutes, 20 runs)

**Do:** one run at each enemy level **1400, 1600, 1800, 2000, 2100, 2200,
2300, 2400, 2450, 2500** (gear `CURRENTLY EQUIPPED`), then repeat the sequence
a second time. 20 runs, ~2 minutes of clicking plus cooldowns.

Corporate Network's profiler cap is **2534** — above the deepest enemy the
player has ever fought (2399), so this reaches genuinely new territory.

**Resolves, directly:**

- **The hit-chance formula (open question §7), and `CRAFT_WEIGHTS_PCT["Acc"]`.**
  Each run yields two fully logged fights with the enemy's
  `effective_evasion`. Player accuracy is fixed across the sweep, so hit rate
  plotted against enemy evasion traces the curve with no confounds. `Acc` was
  cut 1.0 → **0.14** on 27 Jul, but 0.14 is a placeholder sized to "nearly
  saturated", **not a fit**, and its regime is Corporate Network evasion at
  streak 60–130. The sweep reaches enemy level 2534 — above anything the
  player has ever fought — so it tests precisely the case the placeholder was
  never validated against: whether accuracy starts binding again at higher
  evasion.
- **The mitigation curve (open question §8), and `CRAFT_WEIGHTS_PCT["Def"]`.**
  Enemy `effective_attack_damage` rises with level while player Defense is
  fixed; damage taken per enemy attack against enemy attack gives the
  mitigation law, not just the local elasticity. Def is the other joint-highest
  weight and has been withdrawn and republished twice.
- **Where win rate is sensitive** — needed to site Experiment 3.

**Branch, pre-declared:** if win rate is still ≥95% at level 2500, win rate is
saturated and cannot serve as the A/B outcome. Switch the outcome metric to
**rounds per fight** and **HP lost per fight** from the logged victory (both
already parsed by `ihlib.sim_rows`). Do not push the enemy level past the cap
to chase a 50% point that the zone cannot produce.

## 6. Experiment 3 — gear A/B, and the live Payload decision

This is the payoff: **stat weights become measurable instead of asserted**,
and A/B tests that used to cost hours of live play now cost minutes.

`gear_set_capacity` is **2** and `gear_sets` is **empty** — two sets are
available right now at no cost. Profiling a gear set does **not** equip it, so
these tests cost zero disruption to the live streak.

### 6.1 First test: which Payload?

Two *finished* (0 Stability) Payloads both out-score the equipped
`Bastioned Payload of Perfect Strike` (27.8):

| candidate | score | carries |
|---|---|---|
| Targeted Payload of Perfect Strike | 39.4 | Acc +1.56%, AtkDmg +20.00%, AtkSpd +8.69%, CritCh +12.62%, **ArmorPen +107**, MaxHP +1.49%, Eva +2.46% |
| Enduring Payload of Armageddon | 35.9 | Acc +3.70%, **AtkDmg +28.19%**, AtkSpd +6.20%, CritDmg +7.43%, ArmorPen +51, MaxHP +2.10%, Def +3.86% |

The ranking between them rests almost entirely on weights that have **never
been validated**: `ArmorPen 0.05` (inherited; its multiplicand was 0 until 28
Jul, so it has never even been exercised — and the loadout's whole ArmorPen
total is currently +10, so +107 is a step change), `CritCh 0.7`, `AtkDmg 0.7`,
`CritDmg 0.35`. A scalar ranking cannot audit its own weights. The profiler
can.

**Do:**

1. Equip **Targeted Payload of Perfect Strike** now — it is the higher-scoring
   finished upgrade over what is worn, so the swap is positive under either
   answer, and it makes the sim baseline the loadout that is actually running.
2. Create gear set **A** = the current loadout as equipped.
3. Create gear set **B** = identical, except Payload = **Enduring Payload of
   Armageddon**.
4. Pick the enemy level from Experiment 2 where win rate is nearest 50%.
5. Alternate runs A, B, A, B … **20 runs per arm** (~4 minutes).

**Reads out:** `ih.py sims` groups by the `gear` column. 20 runs/arm = 2,000
fights/arm, standard error on the difference ≈ **1.6 percentage points**;
enough to resolve a 4.4pp win-rate difference at 80% power. Push to 50
runs/arm (~9 minutes) for 2.8pp.

Alternating arms rather than running A×20 then B×20 protects against any drift
in the player's level or server state during the session.

### 6.2 Then: fit the weight table properly

Repeat 6.1's shape with set B rewritten each time to move **one stat family**
against set A. Each configuration is one row: a known stat vector (computable
from the capture with `ihlib.stat_total`) and a measured win rate. After ~8–10
configurations, regress win rate on the stat deltas and **replace the asserted
`CRAFT_WEIGHTS_*` table with fitted values.**

Priority order, worst-provenance first (`ih.py assumptions`):

1. `Eva` 1.0 — **never validated**, joint-highest, only ever moved bundled
   with Regen
2. `Acc` 0.14 — a placeholder sized to "nearly saturated", not a fit; §5
   measures it directly
3. `AtkSpd` 0.9 — contested: mitigation stat or worthless (open question)
4. `AtkDmg` 0.7, `CritCh` 0.7 — never validated
5. `MaxHP` 0.5, `CritDmg` 0.35 — never validated
6. `ArmorPen` 0.05, `Thorns` 0.05 — inherited, never exercised

**Regen, Barrier and Max HP stay out of this list while the regime is
`full-hp`** — a full-HP single-fight sample cannot see what they are for.

## 7. What the profiler cannot answer

State these rather than letting the tool's confidence leak into them:

- **Death depth / streak ceiling.** That is the CI/CD Pipeline's job, and it
  is gated at **homelab 12**. It also reports `final_streak`, `xp_per_hour`,
  `credits_per_hour` and `chips_per_hour` directly — i.e. the true objective
  function this workspace has been approximating with a guessed weight vector
  the entire time.
- **Attrition-stat pricing**, while the regime reads `full-hp`.
- **Reward/economy questions** (`reward_streak_soft_cap`, drop rates) — the
  profiler reports combat outcomes only.

## 8. Getting the CI/CD Pipeline

Homelab is level **10** with 11,510 points; level 12 needs **17,000** —
**5,490 points away** at ~85–110 points/hour, so roughly **50–65 hours** of
continuous building. The install itself then costs 10B credits + 1 hackcoin
and ~2 days of build time.

The homelab was **idle** (0 active, 0 queued) when this was written, which
directly delays the only tool that can answer the attrition questions. Keep
the queue full; `ih.py audit` names the jobs.
