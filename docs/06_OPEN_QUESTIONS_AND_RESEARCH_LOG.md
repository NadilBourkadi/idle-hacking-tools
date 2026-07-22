# Idle Hacking — Open Questions and Research Log

This file prevents working models from silently becoming facts.

## Confirmed crafting mechanics — 21 July 2026

### Stability and Compile

- items normally drop with 25-30 Stability;
- most craft actions cost 1 Stability;
- Compile consumes all remaining Stability;
- Compile grants +0.5% non-signature affix values per remaining point;
- Compile is permanent and should be last.

### Version Upgrade

The current schema-4 export showed a uniform chance table across 165 captured affix controls:

- T9→T8 90%;
- T8→T7 80%;
- T7→T6 70%;
- T6→T5 60%;
- T5→T4 50%;
- T4→T3 40%;
- T3→T2 30%;
- T2→T1 20%;
- T1 unavailable.

Failed attempts do not improve the tier and consume resources. Normal failures consume Stability; Snapshot Backup can sometimes prevent the Stability loss.

### Refactor

- rerolls numerical values within the same tier;
- can roll worse;
- bracketed ranges are the current tier's roll range;
- use after tier upgrades, not before.

### Augment / affix capacity

- normal cap is 3 prefixes and 3 suffixes;
- Augment fills the remaining affix slot;
- 3P/2S forces a suffix and 2P/3S forces a prefix;
- Augment's current UI cost can include primary resource plus Credits.

### Lock / Prune / Bias Reroll

- only one affix can be crafting-locked;
- Prune removes one random unlocked affix;
- Prune and Bias Reroll consume the active lock on success unless auto-relock succeeds;
- current Bias Reroll UI cost is primary resource + Credits + 20 Essence;
- the selected essence guarantees a category/orientation, not one exact affix.

## Priority open questions

### 1. Snapshot Backup

Known:

- it can prevent Stability loss on failed Version Upgrades.

Unknown:

- the player's current level and trigger chance;
- whether it affects any other failed craft action.

Test/capture:

- passively capture the Homelab branch tooltip;
- record a sequence of failed upgrades and whether Stability was retained.

### 2. Successful Version Upgrade roll behaviour

Unknown:

- whether the new-tier value is independently rerolled;
- whether relative roll percentile is preserved or transformed.

Test:

- export before one successful tier upgrade;
- export immediately after;
- compare old/new ranges and percentile.

### 3. Bias Reroll exact semantics

Unknown:

- how many affixes are rerolled;
- whether selection is prefix/suffix constrained;
- exact interaction with a full item and one lock;
- whether failed/successful operation consumes Stability in all cases.

Test only on a disposable item after enough Essence is available.

### 4. Compile coverage

Known:

- non-signature affixes are multiplied.

Unknown:

- whether the implicit affix is included;
- rounding order;
- interaction with an Optimization Pass base bonus.

Test:

- before/after compile export with at least one percent and one flat stat.

### 5. Augment distribution

Unknown:

- tier weighting;
- affix weighting within the forced side;
- whether item level or rarity affects the roll distribution beyond magnitude.

### 6. Complete affix pool and slot constraints

Need a durable table of:

- every prefix and suffix;
- stat outputs;
- supported slots;
- bias category;
- mutually exclusive families;
- tier availability/weighting.

The in-game Help Affixes table is authoritative but was not present in static export data. A passive structured capture of that visible table would make future Augment advice exact rather than based on observed names.

### 7. Exact hit-chance formula

Known: Accuracy and Evasion determine hit reliability.
Unknown: formula, caps/floors and modifier interactions.

### 8. Defense and Armor Penetration formula

Unknown: mitigation curve, penetration treatment and breakpoints.

### 9. Streak recovery model

Established: late-streak losses often begin far below maximum HP.
Unknown: full post-combat heal/exhaustion formula and which upgrades modify it.
Successful-fight exports remain required.

### 10. Corruption and Thorns formulas

Observed and behaviorally described, but exact scaling/rounding remains unresolved.

## Decision record

### 21 July 2026 — candidate requests redefined

Future candidate evaluations default to selecting and planning crafting projects. An immediate-equip comparison is secondary.

### 21 July 2026 — deterministic crafting protocol adopted

Every top recommendation must include Augment outcomes, target tiers, maximum attempt budgets and a Compile floor.

### 21 July 2026 — current Firewall priorities

- Primary: Citadel Firewall of Warding.
- Forced-suffix Augment probe: Fortified Firewall of the Giant.
- Alternate speed/barrier project: Aligned Firewall of Bastion.


---

## 21 July 2026 confirmed test outcomes

### Kernel trade rejected directionally

A trade of +11 listed Regeneration and +5.53% Max HP for -7.46% Defense, -1.57% Accuracy and -2.09% Attack Speed did not improve the observed streak range. This is a build-specific empirical veto, not a general stat-conversion formula.

### Augment operation details confirmed

A forced-suffix Augment:

- consumed one Stability;
- changed a five-affix Rare into a six-affix Epic;
- rolled T9;
- allowed a duplicate affix family.

### Newly prioritised open tests

1. Matched-enemy Hearty Kernel versus crafted Kernel comparison, preferably multiple samples per side.
2. Successful-fight exports to decode post-combat heal and exhaustion.
3. Version Upgrade before/after export to determine new-tier roll behaviour.
4. Snapshot Backup chance/trigger capture.
5. Bias Reroll before/after capture.
6. Recover and archive the actual 0.6.1 userscript source.
