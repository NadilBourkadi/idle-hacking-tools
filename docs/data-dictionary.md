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

## Working hit-rate calculation

Current model:

`sum(ph) / (sum(ph) + count(pm == true))`

This is useful for relative diagnosis but is not a proven attack-attempt formula because rounds may aggregate multiple actions.

## Duplicate handling

The two Mirrored Network Monitor exports at 18:19:29 and 18:19:35 contain the same fight identifiers and round sequence. Count them once in analysis. The second copy is retained with a `DUPLICATE-` filename for provenance.

## Loadout completeness

A one-slot comparison export is sufficient for exact slot deltas but not for whole-loadout state. Use the schema-4 8/8 export as the baseline, then apply only confirmed equipment changes.
