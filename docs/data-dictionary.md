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

## Working hit-rate calculation

Current model:

`sum(ph) / (sum(ph) + count(pm == true))`

This is useful for relative diagnosis but is not a proven attack-attempt formula because rounds may aggregate multiple actions.

## Duplicate handling

The two Mirrored Network Monitor exports at 18:19:29 and 18:19:35 contain the same fight identifiers and round sequence. Count them once in analysis. The second copy is retained with a `DUPLICATE-` filename for provenance.

## Loadout completeness

A one-slot comparison export is sufficient for exact slot deltas but not for whole-loadout state. Use the schema-4 8/8 export as the baseline, then apply only confirmed equipment changes.
