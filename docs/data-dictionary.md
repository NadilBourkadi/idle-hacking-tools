# Data Dictionary and Analysis Notes

## Combat round fields used in current analysis

- `r`: round index.
- `pa`: aggregate player direct attack damage recorded in the round.
- `ph`: player hits recorded in the round.
- `pc`: player critical hits/events recorded in the round.
- `pm`: boolean miss-containing event/round marker.
- `ea`, `eh`, `ec`, `em`: enemy analogues.
- `php`, `ehp`: ending player/enemy HP for the round.
- `prg`, `erg`: player/enemy regeneration-like logged values.
- `ptd`, `pcd`: damage to player associated with thorns/corruption fields.
- `etd`, `ecd`: damage to enemy associated with thorns/corruption fields.
- `pbs`/`pbf`, `ebs`/`ebf`: starting/final barrier values when present.

Exact semantics are not fully decoded. Preserve raw logs.

**Round detail records only while the "Detailed Logs" checkbox in the Hacking panel is enabled** (corrected 23 July 2026 — an earlier working model blamed the combat-log modal; the checkbox is the real switch and it keeps recording even while other screens are visible, verified by capture). Fight-level fields — `rounds`, `damage_dealt/taken`, `starting_hp`, `enemy_stats`, streak — are always present regardless. For any hit-rate or corruption analysis, ensure the checkbox is on; the userscript readiness line shows `rounds N/M LIVE` when detail is flowing and warns when it stops. The in-log order is newest-first, and **fight `id`s are per-session** (the counter resets on page reload), so cross-capture analysis must not treat ids as global — `ihlib.experiment_status` dedupes by content key. `recentLossStreaks` is the reliable record of death depth.

## Fight-level damage accounting (23 July 2026, Phoenix Shell A/B)

- **`damage_taken` is gross incoming damage, not net HP drain** (verified: deep-streak fights show `damage_taken` exceeding summed `prg` while start→final HP is unchanged). Never compare it across a mitigation↔recovery equipment change without netting out recovery — use `damage_taken − Σprg − barrier absorption`.
- **`pbs` working model revised:** per-round sums run ~10–25/round (265–705/fight on the 221-Barrier Shell) — absorption-sized, not "starting barrier value" as previously guessed. Treat Σ`pbs` as probable per-round barrier absorption (working model, not verified).
- The identity `damage_taken − Σprg − Σpbs = HP drop` does **not** close exactly (residuals −235 to +2,000/fight; suspected overheal capping under-reporting `prg` at full HP). Treat net-drain figures as directional; corroborate with attrition onset (`starting_hp/max_hp` trajectory), which is exact.
- `Σprg/rounds` is the realized-regen measure (listed Regen ≠ realized; e.g. +46 listed moved deep-streak realized regen 130.6 → ~167–177/round).

## Working hit-rate calculation

Current model:

`sum(ph) / (sum(ph) + count(pm == true))`

This is useful for relative diagnosis but is not a proven attack-attempt formula because rounds may aggregate multiple actions.

## Duplicate handling

The two Mirrored Network Monitor exports at 18:19:29 and 18:19:35 contain the same fight identifiers and round sequence. Count them once in analysis. The second copy is retained with a `DUPLICATE-` filename for provenance.

## Loadout completeness

A one-slot comparison export is sufficient for exact slot deltas but not for whole-loadout state. Use the schema-4 8/8 export as the baseline, then apply only confirmed equipment changes.
