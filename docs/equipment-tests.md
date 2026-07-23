# Equipment Test Results — 21 July 2026

**Purpose:** Preserve exact measured evidence from equipment trials without converting noisy A/B data into invented formulas.

## Test 1 — Aggressive Kernel of Renewal versus Hearty Kernel of Decay

### Item delta

| Stat | Hearty Kernel | Aggressive Kernel | Delta |
|---|---:|---:|---:|
| Max HP | 6.93% | 12.46% | +5.53% |
| Regeneration | 53 | 64 | +11 |
| Defense | 10.02% | 2.56% | -7.46% |
| Evasion | 0 | 3.46% | +3.46% |
| Accuracy | 1.57% | 0 | -1.57% |
| Attack Speed | 2.09% | 0 | -2.09% |
| Attack Damage | 0 | 0.80% | +0.80% |
| Corruption | 4 | 0 | -4 |
| Thorns | 0 | 5 | +5 |

The swap increased observed maximum HP from roughly 9,980-9,993 in the prior baseline losses to 10,510-10,524, approximately +5.3%.

### Unique post-swap losses

The two Mirrored Network Monitor exports describe the same fight and were deduplicated.

| Metric | Mirrored Network Monitor | Rooted Backup Daemon |
|---|---:|---:|
| Enemy level | 1163 | 1170 |
| Streak ended | 89 | 90 |
| Starting HP | 4,075 / 10,524 (38.7%) | 7,044 / 10,510 (67.0%) |
| Rounds | 23 | 33 |
| Player hits | 31 | 28 |
| Miss events (`pm=true`) | 5 | 15 |
| Modelled hit rate | 86.1% | 65.1% |
| Player direct damage | 11,573 | 9,873 |
| Total player `prg` | 2,072 | 2,719 |
| `prg` per round | 90.1 | 82.4 |
| Enemy direct damage | 4,628 | 7,899 |
| Player thorns/corruption damage taken | 1,229 | 1,183 |
| Enemy HP remaining | 1,389 / 14,031 (9.9%) | 1,808 / 12,673 (14.3%) |

Working hit-rate model: `sum(ph) / (sum(ph) + count(pm=true))`. Exact event semantics remain unknown.

### Prior high-level baseline losses

| Enemy | Level | Streak | Starting HP | Rounds | Modelled hit rate | `prg` / round |
|---|---:|---:|---:|---:|---:|---:|
| Explosive Network Monitor | 1163 | 90 | 3,031 / 9,993 (30.3%) | 13 | 77.8% | 140.5 |
| Fortified VPN Endpoint | 1180 | 92 | 2,092 / 9,980 (21.0%) | 19 | 73.1% | 153.9 |
| Mirrored VPN Endpoint | 1179 | 92 | 4,923 / 9,967 (49.4%) | 34 | 56.1% | 93.4 |

These are not matched enemies/modifiers, so they cannot establish a Defense or Regeneration formula. They do show that the post-swap sample did not improve the observed streak range and that +11 listed Regeneration did not guarantee higher realised `prg` per round.

### Decision

Reject the Aggressive Kernel as the main streak item and restore/prefer Hearty Kernel of Decay.

### Durable learning

- Defense, Accuracy and Attack Speed protect sustain indirectly through lower damage per hit and shorter fights.
- Max HP is a buffer, not recovery.
- Listed Regeneration must be validated using combat-log `prg`; its realised value varies by encounter and round state.
- A trade of +11 Regeneration and +5.53% Max HP for -7.46% Defense, -1.57% Accuracy and -2.09% Attack Speed is empirically unfavourable in the current build.
- Confidence: directional, not formula-level, because the sample is small and enemies/modifiers were not matched.

## Test 2 — Fortified Firewall forced-suffix Augment

### Before

- Rare, item level 859;
- 3 prefixes / 2 suffixes;
- 26/26 Stability.

### After

- Epic, 3 prefixes / 3 suffixes;
- 25/26 Stability;
- added `of Sandboxing` T9: +25 Damage Barrier;
- an existing `of Sandboxing` suffix remained, so duplicate affix families are directly observed.

### Main-set comparison against Brutal Firewall of Perpetuity

| Stat | Delta |
|---|---:|
| Max HP | +3.32% |
| Evasion | +8.60% |
| Accuracy | +1.20% |
| Damage Barrier | +47 |
| Defense | -15.23% |
| Regeneration | -52 |
| Attack Damage | -2.01% |

### Decision

Abort. The Augment did not supply Regeneration, the item is now full, and further tier work cannot repair the missing sustain package. Random Prune/re-Augment is not resource-efficient.

## Testing methodology learnings — 22 July 2026 (Storm Daemon A/B)

- **Death streak is a low-power metric.** Session variance was ±8 streaks (84–104 over 8 baseline runs); a 2-streak test only detects revolutionary changes. Judge *crafts* on mechanism metrics — rounds/fight and damage/round at matched enemy level, damage taken/fight, attrition-onset streak (first start <90%) — which moved detectably (−5%, +8%, −6.5%, +5 streaks) while the death streak showed nothing.
- **Baselines must be same-session.** Player levels (+8 = +40 heal, HP/def growth) and completing homelab jobs shift stats within hours; compare against streaks from the same session and log completed jobs as confounds.
- **Model components validated so far:** tier-midpoint landing assumption (4/4 lines at/above mid), independent re-roll on Version Upgrade (6/6), ilvl scaling and cost model (exact). Weakest link: unknown hit-chance formula — the naive +13% output estimate realized as +8% largely through the unmodeled Accuracy interaction. The Hawk instrument streak (open questions §7) is the cheapest fix; the Hacking Simulator (homelab 10) is the real one.
