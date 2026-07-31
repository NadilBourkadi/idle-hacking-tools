# Data Dictionary and Analysis Notes

## Combat round fields used in current analysis

- `r`: round index.
- `pa`: aggregate player direct attack damage recorded in the round.
- `ph`: player hits recorded in the round.
- `pc`: player critical hits/events recorded in the round.
- `pm`: boolean miss-containing event/round marker.
- `ea`, `eh`, `ec`, `em`: enemy analogues.
- `php`, `ehp`: ending player/enemy HP for the round.
- `prg`, `erg`: player/enemy **realized** regeneration for the round — a NET figure, not the listed stat.
  **Exact law (measured 29 July 2026, 288/288 profiler rounds, `mechanics.md` §17):**
  `prg = clamp(Regeneration − 1.5 × ecd, 0, max_hp − php)`. Two consequences that have each caused a wrong
  reading here: incoming corruption **destroys 1.5 HP/round of regeneration per point on top of its damage**
  (so `Σprg` is depressed exactly where corruption is high — never read that as regeneration "under-performing"
  against a class), and `prg` is **truncated to missing HP**, so it reads near zero at full HP and a listed-regen
  buy realizes nothing until the player is depleted. To recover GROSS regeneration use
  `ihlib.gross_regen(prg, ecd)`.
- `ptd`, `pcd`: **the PLAYER'S OWN** thorns / corruption damage, i.e. dealt BY the player to the enemy.
- `etd`, `ecd`: **the ENEMY'S** thorns / corruption damage, i.e. dealt BY the enemy to the player.
  **Corrected 29 July 2026 — these two lines were reversed.** The `p*`/`e*` prefix is the actor throughout the
  log (`pa`/`ea`, `php`/`ehp`, `prg`/`erg`, `pbs`/`ebs`), and these follow it. Proof: `pcd` is flat at ~92-103
  per round across all nine enemy classes (it is the player's own corruption, which does not vary by opponent),
  while `ecd` runs 104-108 against Trojan Wall / Rootkit / Stealth Worm and 14-22 against everything else --
  tracking the enemy's own `corruption` stat (31 vs 5) exactly. Reading `pcd` as incoming damage inverts the
  single most important thing in the log.
- `pbs`/`pbf`, `ebs`/`ebf`: starting/final barrier values when present.

Exact semantics are not fully decoded. Preserve raw logs.

**Round detail records only while the "Detailed Logs" checkbox in the Hacking panel is enabled** (corrected 23 July 2026 — an earlier working model blamed the combat-log modal; the checkbox is the real switch and it keeps recording even while other screens are visible, verified by capture). Fight-level fields — `rounds`, `damage_dealt/taken`, `starting_hp`, `enemy_stats`, streak — are always present regardless. For any hit-rate or corruption analysis, ensure the checkbox is on; the userscript readiness line shows `rounds N/M LIVE` when detail is flowing and warns when it stops. The in-log order is newest-first, and **fight `id`s are per-session** (the counter resets on page reload), so cross-capture analysis must not treat ids as global — `ihlib.experiment_status` dedupes by content key. `recentLossStreaks` is the reliable record of death depth.

## Fight-level damage accounting (23 July 2026, Phoenix Shell A/B)

- **`damage_taken` is gross incoming damage, not net HP drain** (verified: deep-streak fights show `damage_taken` exceeding summed `prg` while start→final HP is unchanged). Never compare it across a mitigation↔recovery equipment change without netting out recovery — use `damage_taken − Σprg − barrier absorption`.
- **`pbs` is the barrier pool REMAINING at that round — a stock, not a flow. Never sum it.** (Resolved 29 July 2026, after two wrong readings.) It is logged only while the pool is above zero, so a larger pool appears in more rounds; that alone produced a fake "procs rise with the stat" effect (1.70 -> 3.15/fight) and then a fake super-linear absorption curve (apparent 1.68x -> 2.34x -> 5.26x of the stat) purely because Σ`pbs` accumulates more terms when the pool lasts longer. **Actual absorption is the pool DRAWDOWN**: `Σ max(0, pbs[i-1] − pbs[i])`, plus the last logged value when it drops out of the log. Measured that way it is **exactly 1.00× the Barrier stat per fight in both cohorts** (787.5 stat → 787 absorbed, n=879; 2,529.5 stat → 2,529 absorbed, n=477). Barrier is a **once-per-fight shield equal to its value**, and it absorbs every channel — direct, corruption and thorns (see `mechanics.md` §16).
- The identity `damage_taken − Σprg − Σpbs = HP drop` does **not** close exactly (residuals −235 to +2,000/fight; suspected overheal capping under-reporting `prg` at full HP). Treat net-drain figures as directional; corroborate with attrition onset (`starting_hp/max_hp` trajectory), which is exact.
- `Σprg/rounds` is the realized-regen measure (listed Regen ≠ realized; e.g. +46 listed moved deep-streak realized regen 130.6 → ~167–177/round). **Since 29 July 2026 the gap is fully explained** — it is the corruption suppression term plus the overheal cap, both exact (`mechanics.md` §17). Segment by enemy corruption before comparing realized regen across any two cohorts.

## Working hit-rate calculation

Current model:

`sum(ph) / (sum(ph) + count(pm == true))`

This is useful for relative diagnosis but is not a proven attack-attempt formula because rounds may aggregate multiple actions.

## Duplicate handling

The two Mirrored Network Monitor exports at 18:19:29 and 18:19:35 contain the same fight identifiers and round sequence. Count them once in analysis. The second copy is retained with a `DUPLICATE-` filename for provenance.

## Loadout completeness

A one-slot comparison export is sufficient for exact slot deltas but not for whole-loadout state. Use the schema-4 8/8 export as the baseline, then apply only confirmed equipment changes.
