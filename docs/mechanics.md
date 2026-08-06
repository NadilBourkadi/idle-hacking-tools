# Idle Hacking — Mechanics and Strategy Handover

**Status:** Living reference  
**Last consolidated:** 20 July 2026

This document separates direct observations from inferred mechanics. It should be updated as new UI evidence, community documentation or controlled tests become available.

---

## 1. Current strategic frame

The user is in the high-hundreds hacking progression range and has reached at least:

- **Coffee Shop WiFi**
- **Small Business Server**

Observed failed fights include enemies at levels 483, 608 and 699. The current equipment includes items requiring levels up to 580, so the player is at least level 580 as of the current snapshot.

The build is a broadly offensive direct-hit build with substantial defensive and sustain support. Its main functional priorities have been:

1. **Accuracy / hit reliability**
2. **Attack damage**
3. **Attack speed**
4. **Crit chance**, especially because the current Payload supplies Crit Damage
5. **Enough defense, max HP, regeneration and barrier to sustain long streaks**
6. Armor penetration where available
7. Progression and resource stats when they do not undermine combat performance

This is not a glass-cannon setup. Long-streak survival matters because a run can end from accumulated attrition even when the final enemy is not an impossible one-on-one matchup.

---

## 2. Combat-stat working model

### Accuracy and evasion — verified at a behavioural level

- Accuracy and enemy evasion jointly determine whether attacks hit.
- Misses materially reduce effective damage and can extend fights enough to create a survival problem.
- Raw attack damage is not valuable when a meaningful fraction of attacks miss.
- Accuracy should be evaluated against the enemies currently being farmed or pushed, rather than maximised without context.

The exact hit-chance formula has not been established.

### Attack damage and defense — verified conceptually; exact formula unknown

- Attack Damage increases outgoing direct damage.
- Defense reduces incoming or outgoing damage as appropriate to the defender.
- Armor Penetration offsets some opposing defense.
- The exact mitigation formula and whether there are breakpoints/diminishing returns have not been proven.

### Attack speed — verified

Attack Speed increases attack frequency. It improves:

- direct DPS;
- the number of opportunities to crit;
- the speed at which an enemy barrier is removed;
- the chance to finish a fight before enemy regeneration or cumulative incoming damage matters.

It does not replace hit reliability.

### Crit chance and crit damage — verified conceptually

- Crit Chance controls critical-hit frequency.
- Crit Damage controls critical-hit multiplier/bonus.
- A stat is weaker when the matching half of the pair is absent.
- The current Payload has a Crit Damage implicit, making Crit Chance on the rest of the loadout unusually useful.

The exact baseline critical multiplier has not been established from the current handover.

### Max HP, defense, regeneration and barrier — verified roles

These form distinct layers:

- **Max HP:** larger loss buffer.
- **Defense:** lowers damage pressure.
- **Regeneration:** recovers HP during combat/round progression.
- **Damage Barrier:** a separate temporary damage buffer.
- **Evasion:** prevents some attacks entirely.

A good streak build needs enough total effective sustain, not necessarily the maximum of every defensive stat.

### Thorns and corruption — observed, exact formulas unresolved

Both appear in combat logs and item affixes.

- **Thorns** deals retaliatory damage when struck.
- **Corruption** causes an accumulating or periodic damage effect in the observed combat schema.

The precise scaling, caps and timing rules remain open questions. They are currently treated as secondary bonuses unless a deliberately specialised build is being considered.

### Enemy modifiers/classes — partly observed

Observed enemy labels include:

- **Mirrored**
- **Rooted**
- **Trojan Wall**
- **Rootkit**

Their exact mechanical modifiers are not fully decoded in this handover. Do not infer effects solely from the names; use combat logs or documented tooltips.

---

## 3. Streak attrition: an important established lesson

Three exported losses illustrate why the final result must be interpreted in the context of the streak:

| Zone | Enemy | Level | Streak ended | Starting HP | Max HP | Rounds |
|---|---|---:|---:|---:|---:|---:|
| Coffee Shop WiFi | Mirrored Unsecured IoT Device | 483 | 64 | 4,228 | 4,228 | 47 |
| Small Business Server | Mirrored Email Gateway | 608 | 66 | 2,989 | 5,658 | 28 |
| Coffee Shop WiFi | Rooted Open Hotspot | 699 | 85 | 1,141 | 5,586 | 13 |

The level-699 loss began at only about 20% HP; the level-608 loss began at about 53% HP. Therefore:

- the loss is not automatically evidence that the enemy is unbeatable from full health;
- recovery between fights and accumulated attrition are central to long-run performance;
- evaluating only the final fight’s enemy level can lead to the wrong upgrade recommendation;
- regeneration, defense, barrier, fight duration and any between-fight recovery mechanic must be considered together.

The `post_combat_heal` field is zero on these losses because the player died; this does not by itself establish that no post-combat recovery exists after victories.

### Streak recovery law — RESOLVED 22 July 2026 (exact, N=21 winning fights)

The 22 July rich capture exposed the full post-combat heal decomposition on victories:

```text
heal = heal_base × 0.99^(win_streak − 10), capped at missing HP
```

- Verified exact (float-precision) across 21 consecutive wins at streaks 38–58.
- `heal_base` = **5 × player hack level** (confirmed 22 July: `statsBreakdown.post_combat_heal` attributes the full amount to `level` — 4,470 at level 894, and the earlier 4,465 sample matches level 893 exactly; `equipment_flat`/`equipment_pct`/`homelab` components all 0). It does **not** scale with max HP or equipment; the Homelab `thermal_budget` upgrade (+1% max HP post-combat heal per level) would add the first max-HP-scaling component.
- No exhaustion for the first 10 wins; thereafter healing decays 1% compounding per win. A `post_combat_heal_exhaustion_relief` field exists (0 in all samples) — some relief mechanic exists but is unobserved.
- Attrition mechanism: heal shrinks while per-fight damage grows with enemy level. In the sample, damage taken crossed heal near streak ~50 — past that point HP ratchets down monotonically, which is why late-streak losses begin at 20–50% HP.
- Strategic frame: the equilibrium streak is where average damage taken per fight equals the decayed heal. Defense/Evasion/fight-shortening stats push the crossing point later; Max HP does not move it (it only widens the buffer being drained).
- Related survival mechanic: the Homelab **Snapshot Rollback** upgrade (currently level 0) recovers 25% HP on lethal damage once per 10 fights (−1 fight cooldown per level) — a direct anti-attrition tool worth evaluating against combat-stat homelab upgrades.

---

## 4. Equipment structure

### Slots — verified

There are eight software equipment slots:

1. Payload
2. Firewall
3. Analyzer
4. Shell
5. Driver
6. Router
7. Daemon
8. Kernel

### Item fields — verified

Observed tooltips can include:

- Name
- Rarity
- Slot
- Item Level
- Ratio
- Required Level
- Compiled percentage
- Stability current / maximum
- Found by
- Enhanced by
- Implicit stat
- Prefix affixes
- Suffix affixes
- Comparison deltas against current equipment

### Rarity and affix counts — verified for observed Rare/Epic items

- Observed **Rare** items have five affixes: generally two prefixes and three suffixes.
- Observed **Epic** items have six affixes: generally three prefixes and three suffixes.

Do not assume this exhaustively covers every rarity or special item type without further evidence.

### Affix tiers — verified direction

Lower tier numbers are stronger:

- **T1** is a top-tier roll.
- Higher numbers such as T8/T9 are weaker rolls.

This is the reverse of systems where larger tier numbers mean stronger affixes.

### Item name construction — observed

The visible item name appears to use:

- the first/naming prefix;
- the slot name;
- the first/naming suffix.

An Epic item still has additional prefixes and suffixes that are not represented in its display name.

### Item level, ratio and required level — partly understood

- Higher Item Level generally raises stat magnitude.
- Required Level constrains use.
- Ratio is displayed by the game and correlates with Item Level relative to Required Level.

The exact generation formula and how Ratio should be weighted are not fully established. Ratio and Item Level should never override the actual affix package.

**Update 22 July 2026:** the item-level → stat-magnitude relationship is now quantified — percentage affix values scale as `((ilvl+125)/1125)^0.391` around an ilvl-1000 reference, flat values more steeply (~0.785 exponent). See `static-analysis-2026-07-22.md` §1. Affix package still dominates, but the low-ilvl malus on the current Firewall (~-31%) is now a measurable, not rhetorical, replacement argument.

### Stability, enhancement and compilation — verified operational model

The full operational reference is in `crafting.md`.

Verified from the in-game help and the schema-4 crafting export:

- items normally drop with 25-30 Stability;
- most operations consume 1 Stability;
- Version Upgrade improves one tier on success and has success chance equal to `10 × current tier %` from T9 through T2;
- a failed Version Upgrade consumes resources and normally Stability, although Snapshot Backup can sometimes preserve Stability;
- Refactor rerolls values only inside the current tier and can roll worse;
- Augment fills the missing affix slot;
- only one affix may be crafting-locked;
- Prune removes a random unlocked affix;
- Compile permanently converts all remaining Stability into +0.5% non-signature affix values per point.

Strategic consequence: every Stability spent has two costs — the operation itself and 0.5 percentage points of forgone Compile. Candidate advice must therefore use explicit attempt caps and a Compile floor rather than assuming every useful line should be pushed to T1.

Default serious-project floor: finish with at least 8 Stability (+4% Compile), preferably 8-12.

## 5. How to evaluate an item properly

### Do not use Item Level as the decision

A higher-level item can be worse because it has:

- irrelevant resource affixes;
- weak T8/T9 combat rolls;
- poor stat distribution;
- fewer synergistic affixes;
- a worse implicit;
- no replacement for a critical accuracy, speed, damage or sustain stat.

Conversely, an older low-level Epic can remain excellent because it has multiple T1–T3 affixes in the correct package.

### Evaluate in this order

1. **Does it preserve hit reliability?**
2. **Does it improve effective damage, not merely a displayed percentage?**
3. **Does it damage streak sustain?**
4. **Does it strengthen the current crit/damage/speed package?**
5. **How much enhancement potential remains?**
6. **Are gains concentrated in useful stats or padded by resource stats?**
7. **Is it an immediate upgrade, sidegrade, alternate-set piece or future project?**

### Comparison-panel deltas are useful but incomplete

The game’s green/red comparison list answers:

> “What raw aggregate stats change if this item is equipped now?”

It does not automatically answer:

- whether accuracy is already above/below the needed threshold;
- whether shorter fights reduce damage taken enough to offset lost regeneration;
- whether the candidate is unenhanced;
- whether a stat has synergy with the rest of the loadout;
- whether the current goal is pushing, safe streak farming, XP or resources.

Use it as input, not the verdict.

---

## 6. Current loadout’s functional shape

See `current-state.md` for exact affixes.

### Offensive core

- **Payload:** very high Attack Damage, plus Accuracy, Armor Penetration and Attack Speed.
- **Analyzer:** exceptionally dense Crit Chance, Accuracy and Attack Speed.
- **Driver:** Attack Damage, Accuracy, Crit Chance and Attack Speed.
- **Daemon:** Attack Damage, Attack Speed, Accuracy and Evasion.

Together these pieces create the direct-hit/crit/speed core.

### Defensive and sustain core

- **Shell:** Max HP implicit, very high Defense and substantial Barrier.
- **Firewall:** Max HP, Defense and heavy Regeneration despite low Item Level.
- **Router:** strong Defense and Regeneration.
- **Kernel:** Max HP, Defense, Regeneration and a small Attack Speed/Accuracy contribution.

### Likely upgrade-search order

By Item Level alone, Firewall and Analyzer look old, followed by Router. By functional value:

1. **Firewall** is the clearest search target because it is Item Level 314, but a replacement must preserve its unusually valuable HP/Defense/Regen package.
2. **Router** is a plausible target, but its T1 Defense and T1 Regeneration are difficult to replace.
3. **Analyzer** is old by level but extremely strong by affix package; do not replace it casually.
4. **Kernel** is a possible refinement target if a newer item preserves sustain while adding more offense.
5. The Payload, Driver, Shell and Daemon are currently strong anchors.

This is a search priority, not an instruction to equip the next high-level drop in those slots.

---

## 7. Current candidate set: broad sense-check

The validated export contained six inventory candidates:

- Pinpoint Payload of Precision
- Resilient Firewall of Hardening
- Stalwart Analyzer of Accuracy
- Keen Daemon of the Wind
- Intangible Daemon of Light Speed
- Spectral Kernel of Perpetuity

None is an obvious immediate upgrade over the current loadout:

- **Pinpoint Payload:** loses too much of the current Payload’s damage package.
- **Resilient Firewall:** much higher Item Level, but lacks the current Firewall’s deep regeneration/defense/HP package.
- **Stalwart Analyzer:** loses the current Analyzer’s large Attack Speed and Crit Chance package.
- **Keen Daemon:** lacks the current Daemon’s damage and speed density.
- **Intangible Daemon:** useful speed/evasion alternate, but substantially weaker than the current offensive Daemon.
- **Spectral Kernel:** has attractive Max HP and Regeneration, but is older and loses some of the current Kernel’s broader package.

These are provisional qualitative conclusions; use a fresh export if any item is enhanced or the loadout changes.

---

## 8. Homelab / Command Workstation observations

A screenshot of Command Workstation showed these upgrades:

- **Macro Pad:** +0.5% Attack Speed per level
- **Mechanical Keyboard:** +1% Attack Damage per level
- **Script Runner:** +3% Cycles gain per level
- **Virtual Desktops:** +3% Snippets gain per level

At that snapshot:

- Macro Pad was level 3 with level 4 queued.
- Mechanical Keyboard was level 4 with level 5 queued.
- Script Runner and Virtual Desktops were level 0.
- Session Recorder was shown as the next Command Workstation unlock at Homelab level 9.

Strategic working rule:

- choose combat upgrades when progression is constrained by fights;
- choose resource upgrades when the resource economy is the actual bottleneck;
- do not buy resource throughput merely because it is cheap if combat progression is currently limiting unlocks.

---

## 9. Research method

When a mechanic is uncertain:

1. Capture the current loadout.
2. Change one variable only.
3. Export before and after.
4. Run comparable fights or collect combat logs.
5. Compare observed values.
6. Record the conclusion and confidence level.

Good controlled tests include:

- one enhancement step on a full-Stability item;
- one compiled percentage change;
- a single Accuracy change against a fixed enemy;
- one Attack Speed change with the same damage/accuracy;
- swapping only a sustain item and measuring starting HP across long streaks.

Avoid interpreting a noisy multi-item swap as proof of a formula.


---

## 10. 21 July 2026 crafting and combat update

The latest structured export is schemaVersion 4 / sourceVersion 0.6.1. It contains a complete 8/8 loadout, 34 inventory candidates and 32 complete crafting snapshots with affix ranges, operation costs and Version Upgrade probabilities.

Three current losses ended at streak 90-92 and began at approximately 49%, 21% and 30% HP. This confirms that the primary upgrade objective is accumulated-streak sustain. Accuracy remains a secondary requirement because the Mirrored level-1179 fight showed poor hit reliability and ran for 34 rounds.

The current evaluation default is therefore:

1. identify craftable sustain bases rather than immediate equipment swaps;
2. favour suffix structures containing Regeneration, Max HP and Defense;
3. preserve enough Accuracy or fight-shortening damage/speed for Mirrored targets;
4. require explicit Augment outcomes, target tiers, attempt caps and a final Compile floor.

Current primary deterministic project: `Citadel Firewall of Warding`.
Current high-variance forced-suffix probe: `Fortified Firewall of the Giant`.
Current speed/barrier alternate project: `Aligned Firewall of Bastion`.


---

## 11. 21 July 2026 equipment-test update

A crafted Kernel was tested against the existing Hearty Kernel. The candidate gained +11 listed Regeneration, +5.53% Max HP and +3.46% Evasion, while losing 7.46% Defense, 1.57% Accuracy and 2.09% Attack Speed. Two unique post-swap losses ended at streaks 89 and 90, compared with the recent baseline range of 90-92. This is not a matched-enemy formula test, but it is sufficient directional evidence to reject that trade for the present build.

Durable interpretation:

- Defense lowers pressure before regeneration has to repair it.
- Accuracy and Attack Speed are sustain-adjacent because they shorten fights.
- Max HP increases the buffer but does not improve net recovery.
- Listed Regeneration must be checked against realised `prg` and the resulting streak trajectory.

See `equipment-tests.md` for exact logs and limitations.

## 12. Augment observations now verified

The Fortified Firewall probe directly showed:

- Augment consumed exactly one Stability (26 to 25).
- A 3-prefix/2-suffix item received a forced suffix.
- Five explicit affixes became six and the item became Epic.
- Augment can roll T9.
- Duplicate affix families are possible: two `of Sandboxing` suffixes coexisted.

This result did not prove the full Augment tier distribution or exact affix weighting.

## 13. Stat composition — RESOLVED formula-level, 27 July 2026

Decoded from `hardwareInfo.stats_breakdown` in the 27 Jul 14:48Z capture; every
stat closes exactly. **Hardware %, homelab % and equipment % occupy one shared
additive pool** (open-questions §13 resolved). Four families:

| Family | Stats | Formula |
|---|---|---|
| **Scaling** | max_hp, defense, accuracy, evasion, **attack_damage**, **post_combat_heal** | `(base + level + equipment_flat) × (1 + equipment_pct + hardware + homelab)` |
| **Direct multiplier** | attack_speed, crit_chance, crit_damage | `base + equipment_pct + hardware + homelab` (no scaling term) |
| **Gear-flat** | regeneration, corruption, thorns, damage_barrier, armor_penetration | `equipment_flat × (1 + equipment_pct + hardware + homelab)` |
| **Economy** | credits, cycles, hashes, packets, snippets | different schema — `equipment` (not `equipment_pct`), no `level`; `(base + additive components) × (1 + participation_bonus) × (1 + firewall_cache) × (1 + homelab_mult)` — the `homelab_mult` term appeared 31 Jul 2026 when Container Runtime L1 ("×1.01, multiplicative" per its own description) first populated it; confirmed formula-level, all four gathering stats reproduce to <1e-9 with it and sit +0.52% off without it |

**Family membership is not guessable from the stat name.** `attack_damage` was
absent from all three families until 27 July 2026, so `ihlib.stat_total`
silently returned **0** for it against a real total of 2,050 — and it is exactly
the stat the multiplicative-AtkDmg guardrail depends on. `post_combat_heal` and
the five economy stats were wrong the same way. The docstring claiming the
function "reproduces every stat" was never checked against the capture.
`ihlib.validate_stat_totals(capture)` now checks all of them against the game's
own `total` and `ih.py audit` reports any miss as a `MODEL` flag; membership is
detected by key (`equipment` vs `equipment_pct`), so a new economy stat is
handled automatically.

Verifications (27 Jul capture): defense `518.5 × 2.05260 = 1064.27`; accuracy
`3181 × 1.96780 = 6259.71`; evasion `2104 × 1.85898 = 3911.29`; max_hp
`10370 × 1.35358 = 14036.61`; attack_speed `1 + 0.5471 + 0.065 + 0.03 = 1.6421`;
crit_chance `0.05 + 0.3939 + 0.066 = 0.5099`; regeneration `194 × 1.24 = 240.56`.
`post_combat_heal` carries `5 × hack_level` in its `level` term (5,270 at level
1,054) and is pool-multiplied like any other scaling stat — currently
indistinguishable from a constant only because nothing grants it pool.

**The economy family is not purely additive** (corrected 27 Jul 2026, 21:07Z
capture). Two of its components — `participation_bonus` and `firewall_cache` —
**multiply** the additive bracket rather than joining it. Treating them as
additive under-read every economy stat by 11–23%, which `validate_stat_totals`
flagged and nothing else would have: the error is invisible in `potential`'s
econ deltas because those are ratios and it very nearly cancels.

    credits  (1 + 0.46825) × 1.5 × 1.00 = 2.20238   (game: 2.20238)
    snippets (1 + 0.06 + 0.99026) × 1.5 × 1.15 = 3.53670   (game: 3.53670)

The two terms are separately identifiable because the same capture carries a
`firewall_cache = 0.15` case (the four gathering resources) and a
`firewall_cache = 0` case (credits) against a constant
`participation_bonus = 0.5`; every additive reading of either term fails one of
them. All five economy stats now close to <1e-9 across all 58 captures.
Regime: only these two values have ever been observed — a capture with
different ones re-tests the form automatically via `validate_stat_totals`.

**Corollaries.**

- A hardware or homelab track whose gear-flat multiplicand is **0 produces
  exactly 0**. On 27 Jul, Packet Shield (L40, damage_barrier) and Exploit
  Framework (L41, armor_penetration) were multiplying zero — 81,295 chips of
  dead weight, invisible in the shop UI.
- Tracks granting `additive_per_level` 0.001 (attack_speed, crit_chance,
  crit_damage) cost the same per level as the 0.005 tracks and deliver one
  fifth of the pool.
- Homelab combat upgrades are +0.01 pool per level ≈ **+0.5% of the realized
  stat** — inside the noise of a 10-death A/B.
- **Hardware shop chip cost**: `cost(L) = 27.97 × L^1.177` for combat tracks,
  `10.97 × L^1.082` for economy tracks (fit spread 1.001 across six and four
  tracks). Cumulative over the whole build predicts 1,012,105 chips against the
  game's own reset refund of 1,002,284 — **+1.0%**. Cumulative to level N is
  `A/(p+1) × N^(p+1)`.
- `prg` (regeneration) and enemy damage are both **per round**; attack speed is
  wall-clock throughput. Trading attack speed for regeneration therefore
  improves per-fight attrition even though it lengthens real time — unless
  attack speed also governs the player:enemy action ratio, which is untested.

## 14. Hardware shop reset — refunds are LOCKED to the shop (27 July 2026)

A hardware reset refunds every resource spent (`reset_preview_loss` is all zeros
for the free monthly reset), but the refund arrives **locked to the Hardware
Shop** and can never be spent anywhere else. `hardwareInfo.locked_resources`
carries the locked balance; the top-level `chips`/`hackcoin`/resource fields in
`hardwareInfo` report the **free** balance only, so total shop spending power is
`locked + free`.

Observed 27 Jul after the free reset: locked chips 89,900, snippets 665,832,
cycles 126,811, hashes 725,401, packets 169,536, **hackcoin 8**. Resetting again
simply re-locks the refund — locked resources can never escape the shop.

**Consequences.**

- **A reset's hackcoin refund cannot fund Homelab install gates.** Budget the
  install reserve from *free* hackcoin only.
- Locked snippets/cycles/hashes/packets are spendable only on CPU / RAM / GPU /
  Network / Loot Filter / Drop Rate Amplifier — the only tracks that consume
  them. Everything else costs chips + credits.
- Chips have no use outside the shop, so their lock is immaterial.
- Cooldown is `monthly_utc`: `reset_available_at_ms` gave 1 Aug 2026 immediately
  after the 27 Jul free reset. A **paid** reset (`can_paid_reset`) was available
  at once and costs credits only — 346.6M for All Hardware at 418 held levels,
  with sectioned options (Combat / Resources) priced separately. Suboptimal
  allocations are therefore cheap to undo.
- All tracks restart at level 0 after a reset, and cost curves are convex
  (`cost(L) ∝ L^~1.15`), so early levels are far cheaper per point than the tail
  — a reset is the moment to abandon over-levelled low-value tracks rather than
  rebuild them.

## 15. Hacking zones (27 July 2026)

`hackingZones` carries the full ladder. Fields: `min_level` (gate), `level_offset`
(added to enemy level, so a higher-offset zone is harder *and* pays more per
fight), `reward_streak_soft_cap`, `credit_multiplier`, `rarity_multiplier`.

| Zone | min level | offset | soft cap | credit × | rarity × |
|---|---|---|---|---|---|
| Local Network | 1 | 0 | 50 | 1.00 | 1.00 |
| Coffee Shop WiFi | 50 | 10 | 75 | 1.10 | 1.15 |
| **Small Business Server** | 250 | 50 | 120 | 1.20 | 1.30 |
| **Corporate Network** | 600 | 100 | 200 | 1.35 | 1.50 |
| Data Center | 1,500 | 250 | 400 | 1.50 | 1.70 |
| Government Mainframe | 4,000 | 600 | 800 | 1.75 | 1.90 |
| Megacorp Nexus | 10,000 | 800 | 1,200 | 2.00 | 2.20 |
| ReBooted Mainframe | 30,000 | 1,500 | 1,500 | 2.10 | 2.40 |
| s-Kai.Net | 75,000 | 3,000 | 2,000 | 2.20 | 2.60 |

**Measured reward scaling** (5,325 winning fights): credits per fight track
**enemy level**, at a near-constant **≈8.3–8.45 credits per enemy level** across
every streak band from 60 to 129. Enemy level itself rises **≈12 per streak** at
hack level ~1,037. So a zone's `level_offset` is a reward multiplier as much as a
difficulty one: +50 offset means higher-level enemies at the same streak, and
higher-level enemies pay proportionally more.

~~Transition cost is therefore small and computable: +50 offset ≈ 4 streaks of
lost depth (50 levels ÷ 12 levels per streak).~~ **Wrong — measured 27 July 2026.**

The Small Business → Corporate move cost **−17.9 death streaks** (131.0 → 113.1),
4.5× the predicted 4. Two errors:

1. **`level_offset` is not a simple additive term on enemy level.** Fitted
   separately per zone, both the intercept *and* the slope differ, and enemy
   level is non-linear in streak — the ~12/streak figure came from a handful of
   high-streak fights in one zone and does not generalise.
2. **Enemy level is not a sufficient statistic for difficulty across zones.**
   Deaths in Corporate happen at enemy level **~1,730**, *below* the ~1,880 of
   Small Business deaths — the player dies to weaker-on-paper enemies. At
   matched streak (≥80) Corporate enemies carry ~6% more HP and fights run ~7%
   longer, and the class mix differs (Stealth Worm appears).

**Rule going forward: do not predict a zone transition's streak cost from
`level_offset`. Measure it after the fact.** The reward side of the arithmetic
held up — credits per enemy level rose 8.81 → 11.47 (+30%) against a
`credit_multiplier` ratio of only 1.125, so zone rewards scale by more than the
stated multiplier.

`reward_streak_soft_cap` semantics are **not yet measured** — see
`open-questions.md` §17. No break is visible in credits at the 120 cap, but only
34 fights past it exist so far.


## 14. Fight cadence is a fixed real-time tick — measured 27 July 2026

**Fights resolve on a constant ~4.872 s wall-clock interval, independent of every combat stat.** Measured from game-supplied death timestamps (elapsed between consecutive deaths ÷ `streak_ended`+1), Corporate Network, 27 July: **n=29, median 4.872 s/fight, sd 0.053, range 4.858–5.001 → 739 fights/hour.** Flat across every hourly bucket 17:00–22:00Z.

The decisive test: the Driver equip at 21:50Z moved attack speed **1.819 → 1.999 (+9.9%)** and the next death clocked **4.87 s/fight** — zero change.

**Consequences.**

- **Rewards per hour are set by streak depth, not tempo.** Credits/xp/chips scale with enemy level, which scales with streak. Anything that deepens the streak is income; attack speed is not income by itself.
- **Attack speed pays in `rounds` per fight.** Post-equip, rounds/fight fell **−5.0%** at streak 60–85 (z −2.27), **−2.3%** at 86–105 and **−3.7%** at 106–115 (Session 9, larger sample; the −8.3% first reported at 106–130 was small-sample noise — direction holds, magnitude was overstated). At a fixed wall clock, fewer rounds means fewer enemy attacks per fight, so **attack speed is a mitigation stat that acts by shortening fights** — it reduces damage taken per fight rather than increasing fights taken.
- `rounds` is therefore a *simulated* combat count resolved inside the fixed tick, not a wall-clock measure. Do not read rounds as duration.
- This puts the 22 July "tempo does not move the death ceiling" law in question — see `open-questions.md`. `driver-ab-2026-07-27` tests it directly.

**Re-read 1 August 2026: the tick ERA-STEPS.** Daily medians ran **4.873 → 4.750 → 4.788 → 4.605 → 4.641 → 4.666** over 27 Jul–1 Aug, with within-era sd ~0.01 — the tick is very tight inside an era but has moved −4.5% across them. The mover is unidentified: it is **not** rounds/fight (r = 0.42 across daily pairs, and the most-rounds day, 29 Jul at 39.1 rounds, sat at mid cadence) and not attack speed (the +9.9% equip test above moved it 0% within-window; no step aligns with the shell equip boundary either — 4.644 pre vs 4.655 post). The law survives in refined form: **within an era the tick is fixed and attack speed still buys no fights per hour**, but the constant is era-local. `ihlib.FIGHT_CADENCE_S` is re-fit to 4.65 (30 Jul–1 Aug era) and its register check now reads a trailing 50-death window so the next step fires DRIFT instead of averaging into history. Open question: what steps it (`open-questions.md`).

One unexplained ~2.7% step (5.000 → 4.867 s/fight) sits between the 17:00 and 18:00Z buckets. It did not recur at the 21:50 attack-speed change, so it is not tempo-driven. Cause unknown — logged in `open-questions.md`.

## 15. Homelab build throughput is a fixed pool, split across active jobs (verified 29 July 2026)

**Corrected the same day it was written.** The first version of this section claimed slot count did not affect build speed. That was wrong — it came from reading `homelabBuildSpeedBreakdown()` (which computes the global multiplier `o` and genuinely has no slot term) and generalising from one function without reading where `o` is *applied*. The Build Scheduler upgrade states the true behaviour in its own in-game description: **"Adds an additional active Homelab build slot (splits progress, doesn't speed up building)."**

The division happens in `homelabJobEstimates()` (`vendor/game-js/homelab.js`), where `n` is the number of **active jobs**:

```js
const n = Math.max(1, e.length);          // e = active jobs
e.remaining -= l * o * t / n;             // each job gets 1/n of the pool
```

So:

- **Total throughput** = `o / tick_seconds` ticks per second, where `o = clamp((1 + upgradeEffects + global_build_speed_bonus) * global_multiplier, 1, 20)`.
- **Per-job rate** = `o / (n * tick_seconds)`.
- **Total is independent of `n`.** Slots split the pool; they never add to it.

Verified against the capture, exactly (`ihlib.homelab_build_speed`):

| quantity | measured | predicted |
|---|---|---|
| per job, n=2 | 0.1580 ticks/s | `1.58 / (2 x 5)` = 0.1580 |
| total, n=2 | 0.3161 ticks/s | `1.58 / 5` = 0.3160 |

### Consequences (these overturn the previous homelab policy)

1. **Progress points per hour do not depend on how many slots are busy.** Running one job earns exactly what running four earns. The long-standing "4 slots sat empty 23–27 Jul, that is the real loss" framing was wrong in mechanism, and overstated: an empty slot costs nothing as long as **at least one** job is running.
2. **The real failure is throughput reaching zero** — nothing active *and* nothing queued. That is the only state that actually loses points, and it is what `ih.py audit` now flags (`IDLE`); free slots are reported as `COVERAGE` with the hours of work still buffered.
3. **Rank jobs by points per tick (= points per slot-hour), not by total points.** Ticks are the fixed resource, so point-efficiency per tick is the whole question. `ihlib.homelab_fill_suggestions` sorted by *total points* on the opposite rationale and has been corrected; total points now only breaks ties, because a longer job buffers more unattended work at the same rate.
4. **Slots are a buffer against idling, not a throughput purchase.** Their value is that work keeps flowing while nobody is refilling.
5. **Adding a job actively slows every job already running.** To finish one specific target soonest — an install gate, say — run it with as few concurrent jobs as possible. With `n=2`, the Hacking Simulator's remaining 2,257 ticks take ~4.0h; alone it would take ~2.0h. That is a real trade against point-efficiency: VLAN Rules earns 0.109 pts/tick against the Simulator's 0.035, so concentrating on the Simulator costs points to buy time.
6. **Overclock is the only genuine speed purchase**, and it is priced steeply: `HOMELAB_OVERCLOCK_COST_MULTIPLIERS = {1:1, 2:5, 3:15, 4:25, 5:40}` — 2x speed for 5x resources. `max_build_overclock` is currently **1**, so none is available.

## 16. Corruption damage bypasses Defense, and it is what sets the death ceiling (measured 29 July 2026)

Segmenting post-Kernel fights (streak 106–145, n=381 victories) by enemy class splits them cleanly in two, on the enemy's own `corruption` stat:

| | enemy `corruption` | direct `ea`/rnd | corruption `ecd`/rnd | `ea+ecd` | realized `prg`/rnd | **NET/rnd** |
|---|---|---|---|---|---|---|
| **Trojan Wall** | 31.8 | 225 | **104** | 329 | 316 | **+34.8** |
| **Rootkit** | 31.3 | 233 | **108** | 341 | 290 | **+15.0** |
| **Stealth Worm** | 31.0 | 228 | **104** | 332 | 302 | **+11.1** |
| Spike Router | 4.6 | 339 | 14 | 354 | 401 | −19.6 |
| Logic Bomb | 6.8 | 302 | 20 | 322 | 367 | −22.0 |
| Zero-Day | 7.2 | 309 | 22 | 331 | 335 | −22.2 |
| Glitch Phantom | 4.7 | 345 | 15 | 360 | 368 | −28.8 |
| Siege Daemon | 4.9 | 347 | 16 | 363 | 364 | −31.6 |
| Brute Force | 6.9 | 295 | 20 | 316 | 328 | −45.1 |

**Total incoming damage is nearly identical across all nine classes** (`ea+ecd` = 316–363). What differs is the **channel**: the three lethal classes deliver about a third of their damage as corruption DoT, and the other six deliver almost all of it as direct attacks.

**Defense only reduces the direct channel.** That is visible in the table — direct `ea`/round against the corruption classes is *lower* (225–233) than against the safe ones (295–347), which is Defense working exactly as expected. The corruption third simply goes around it.

Consequences:

1. **These three classes caused 11 of 11 post-craft deaths.** They are the only ones with positive net drain. The death ceiling is set by them alone, and by the length of the worst *run* of them — the mean across classes is ≈ −12/round, but two or three Trojan Walls in a row cost ~2,000 HP each against a 17.6K pool.
2. **Defense is now a low-value stat at the margin.** It is blind to the channel that kills. This is why the +37.4 Kernel craft — overwhelmingly Defense and Barrier — bought only **+3.8 death streaks**: it spent almost all of its value on the two-thirds of incoming damage that was never the constraint.
3. **CORRECTED 29 July 2026 (evening): a corruption-resistance upgrade DOES exist.** The original claim -- "there is no corruption-resistance stat" -- was made by reading `statsBreakdown`, which only shows stats the player already has. **Isolated Sandbox** [Virtualization Cluster] "divides incoming corruption damage by 1.01 (+0.01/level)", max level 200 (up to ÷3.00), **gated at homelab 11** and therefore invisible in the UI at homelab 10. Virtualization Cluster is already installed and the upgrade costs 25M credits at base with no hackcoin. This is the same accessibility trap `CLAUDE.md` warns about, run in reverse: absence from the current stat block is not absence from the game. The other counters stand: (a) **fewer rounds**, since corruption is charged per round, and (b) **regeneration and Max HP**.
4. **RESOLVED 29 July 2026 (evening) — corruption carries a healing-reduction rider, and it is exact.** `prg = clamp(Regeneration − 1.5 × ecd, 0, max_hp − php)`, verified on **288/288 rounds (100%)** of Software Profiler logs across 4 fights, 4 enemy classes and 2 enemy levels. Each point of incoming corruption damage destroys **1.5 HP/round of regeneration on top of the damage it deals**, so incoming corruption costs **2.5× its face value**. See §17.

**Method note:** this was found by comparing the two cohorts' full `enemy_stats` vectors, which surfaced `corruption` at 5.4x separation while every other field sat within 20% — including `attack_damage`, which is *lower* for the lethal classes. Do this before theorising about a matchup: the ledger already carries the enemy's whole stat line.


## 17. Regeneration is exact, and corruption suppresses it 1.5:1 (measured 29 July 2026, Software Profiler)

**`prg = clamp(Regeneration − 1.5 × ecd, 0, max_hp − php)`**

Verified on **288 of 288 rounds (100.0%, residual ≤ 1.0)** from four fully-logged
Software Profiler fights — Siege Daemon and Trojan Wall at enemy level 2537,
Zero-Day and Trojan Wall at 2300. `Regeneration` is the listed total from
`statsBreakdown.regeneration.total` (537.85 at measurement); the uncapped term
fits with residual **exactly 0.0** over 190 non-capped rounds.

Three separate long-standing questions collapse into this one line:

1. **Corruption is a healing-reduction effect, not just a DoT.** Each point of
   `ecd` removes **1.5 HP/round of regeneration** *in addition to* the damage it
   deals, so incoming corruption costs **≈2.5× face value**. Against Trojan Wall
   at profiler level 2537 (`ecd` ≈ 200/round) that is **300/round of a 537.85
   pool destroyed — 56% of the build's regeneration**, which is precisely why
   Trojan Wall / Rootkit / Stealth Worm cause ~72% of all deaths (88 of 123 in
   the ledger) while dealing *less* direct damage than the safe classes.
2. **Overheal capping is real and exact.** `prg` is truncated to `max_hp − php`,
   so a listed-Regeneration buy realizes **nothing** while near full HP and
   **1:1** once depleted. This confirms the 28 July working model at formula
   level and explains its band pattern (+0.4% / +4.7% / +11.5% realized at
   streak 60-85 / 86-105 / 106-130) without needing any extra mechanism.
3. **`prg` is a NET figure.** Any analysis that treated it as gross
   regeneration double-counted corruption. `Σprg/rounds` measures
   *regeneration after suppression*, which is why it looked like regeneration
   "under-performs against exactly three enemy classes".

Corollaries worth acting on:

- **A point of listed Regeneration is worth 1 HP/round while depleted** — over a
  ~55-70 round fight that is 55-70 HP, against **1 HP** for a point of Barrier
  (a once-per-fight shield equal to its value, §16 / `data-dictionary.md`).
  `CRAFT_WEIGHTS_FLAT` prices these at 0.6 and 0.043, a ratio of 14×, where the
  mechanism implies ~55-70× at depth. The gap is the overheal cap, which is
  *not* binding at the depths where runs actually end. **Treat the Regen:Barrier
  ratio as unresolved and measure it with a gear-set A/B** — do not re-fit from
  this alone.
- **The enemy's regeneration is already fully suppressed by ours.** `erg` is 0 in
  95%+ of rounds (player `pcd` 17-145/round × 1.5 exceeds every observed enemy
  regeneration of 30-104), so additional player Corruption buys **no further
  suppression** — only direct damage. `CRAFT_WEIGHTS_FLAT["Corrupt"] = 0.7`
  measured that direct share and needs no change on this account.
- The logged `php` appears to be the round's HP **before** regeneration is
  applied — that is the reading under which `prg = max_hp − php` at the cap.
  Working model; it also predicts that the long-standing "damage_taken − Σprg −
  Σpbs = HP drop does not close" residual is an off-by-one-round artefact.

**Update 6 Aug 2026 — the magnitude is measured (CI/CD Regen pair).** The
gear-set A/B the first corollary called for ran on the pipeline: +31 item-flat
Regen (+59 at loadout, composition ×1.905) bought **+3.69 ± 0.72 streaks** at
the ~176-arm faces — **~0.119 streaks per item-flat point**, 5σ, confounds
net-negative (so mildly conservative). It reproduces the Shell live close
exactly (+49 × 0.119 = +5.8). Regime-local to the deep-attrition era per the
overheal cap above. The Regen:Barrier half of the question sharpened the same
day: the driver A/B close + sim decomposition put a Barrier-carried +44-score
craft at ~+1.9 ± 2 live streaks, so at these faces measured Regen converts
**~5× more depth per score point than Barrier** (`open-questions.md` §15 — the
Barrier side still needs its own isolating pair).

**Method note.** This was found in the first two Software Profiler runs ever
taken, from `enemy_stats` + full round logs, in about ten minutes. The same
question had been open for a day against 381 live fights, because live logs
never carry a clean pairing of a known Regeneration total with a controlled
range of enemy corruption.


## 18. Hit chance and damage mitigation — RESOLVED formula-level, 29 July 2026 (Software Profiler sweep)

Both were open since 21 July (`open-questions.md` §7, §8). A 21-run sweep of enemy
levels 1400–2537 (2,100 simulated fights, 32 fully logged) settled them, because
every profiler fight carries the **enemy's own stat line** next to a full round log.

### Hit chance

**`logit(hit) = −0.164 + 1.420 × ln(Accuracy / Evasion)`** — `ihlib.hit_chance`

Fitted on the **unbiased 2-attack-round sample** (1,004 rounds, 32 fights) across
enemy evasion **3,002–7,699** at fixed player Accuracy 9,226.9.

> **Corrected 29 Jul 2026 (late).** A first fit of `0.532 + 1.208·ln(Acc/Eva)`
> was shipped from a **biased denominator**. `pm` flags only that the *first*
> attack of the round missed (client: "First hit misses, but N hits land"), so
> `hits/(hits+missflags)` cannot see a round whose first attack hits and second
> misses — it read 0.757 where the truth is **0.638**. The clean sample is
> 2-attack rounds, identifiable without knowing the attack count: `ph=2,pm=0`
> (both hit) vs `ph=1,pm=1` (first missed, second hit), so
> `p = n(2,0)/(n(2,0)+n(1,1))`. The model self-validates three ways —
> predicted `n(0,1)` 335 vs 354 observed, total rounds 1,930 vs 1,949, and
> implied attacks/round **1.815 against an AttackSpeed stat of 1.8458**. The obvious ratio-power form `acc^k/(acc^k+eva^k)` is
**rejected** (NLL 1666.8 vs 1622.6); a linear-in-`eva/acc` form and
`1 − c·eva/(eva+acc)` fit equally well and are indistinguishable on this data.

- **Accuracy is NOT saturated, and it is worth roughly double the biased fit
  implied.** At the evasion the deep bands actually face (4,857–5,386 at streak
  120–159) true per-attack hit rate is **65–68%**, and +1% of the Accuracy
  *stat* buys **+0.45–0.50% damage output**. The 27 July "accuracy is saturated" reading came
  from comparing pooled streak bands, where enemy evasion moves with composition.
- `CRAFT_WEIGHTS_PCT["Acc"]` settled at **0.21** after two corrections in one
  session (see §19). Covers the output channel only, so it remains a floor.

### Damage mitigation

**`damage_dealt = AttackDamage × K / (K + Defense − ArmorPen)`, K ≈ 205** —
`ihlib.damage_multiplier`

The same functional form fits **both directions independently**: K = **190.2**
outgoing (32 fights, enemy Defense 743–1,990) and K = **219.3** incoming (28
fights, our Defense 1,487, enemy ArmorPen 26–406). Two independent fits landing
within 15% is the strongest evidence available that this is the real law.

- **Defense elasticity is −Defense/(K+Defense) = −0.88** at our 1,487, close to
  the live readings of −0.93 to −0.96 and *below* the applied weight of 1.0.
- **ArmorPen is validated at its inherited 0.05.** +97 points (10 → 107) is
  **+6.1%** output vs enemy Defense 1,500 and **+7.0%** vs 1,300 — 0.044–0.051
  per point on the AtkDmg = 0.7 scale. The law is **convex**, so value per point
  *rises* as ArmorPen approaches enemy Defense; do not extrapolate far above the
  fitted range (our ArmorPen 10, enemy Defense 743–1,990).
- **Defense only touches the direct channel, and that is now quantified.**
  Against the three classes causing ~72% of deaths, direct damage is 25,391 of an
  effective 52,131 per fight once corruption is counted at its measured 2.5×
  (§17) — Defense addresses **~49%** of what actually kills. `CRAFT_WEIGHTS_PCT["Def"]`
  is registered in `ihlib.PENDING_REFITS` for this reason: the mechanism says 1.0
  is roughly double any defensible value, but converting a mitigation elasticity
  into the weight scale needs an output↔mitigation exchange rate that only a
  gear-set A/B can supply.

**Regime.** Fitted in Corporate Network at enemy levels 1400–2537 against a
single loadout (Accuracy 9,226.9, Defense 1,487, ArmorPen 10). Enemy stats are
**not** a pure function of enemy level — at level 2300 a Zero-Day rolled evasion
7,221 against a Trojan Wall's 5,138, a wider spread than between levels 2300 and
2537 — so per-level replication is mandatory and single-run points are noise.


## 19. The craft weight table, re-fitted from measurement (29 July 2026)

Every `CRAFT_WEIGHTS_*` value except `AtkDmg` had been asserted or inherited.
The profiler sweep made most of them directly measurable, and the re-fit moved
almost all of them — several by more than 2×.

### The scale, and the error that had inflated half the table

A **"+1%" affix does not raise a stat by 1%.** It adds one point to that stat's
shared additive pool (§13), so the stat moves by **1/pool**:

| stat | additive pool | stat % per +1% affix |
|---|---|---|
| AttackDamage | 1.4580 | **0.686%** |
| MaxHP | 1.5435 | 0.648% |
| AttackSpeed | 1.8348 | 0.545% |
| Evasion | 2.1036 | 0.475% |
| Defense | 2.2983 | 0.435% |
| Accuracy | 2.3347 | 0.428% |

`AtkDmg` anchors the scale: 0.686% output per affix point against an applied
weight of **0.7**. So a weight means **"% output-equivalent per +1% affix"** —
and the pool-heavy stats (Defense, Evasion, Accuracy) had been priced as though
their affixes moved the stat a full 1%, which is why they were the most
over-weighted. This conversion is the single largest correction in the table.

### The two families, and their exchange rate

- **Output stats** (AtkDmg, CritCh, CritDmg, AtkSpd, Acc, ArmorPen, Thorns,
  Corrupt) shorten the fight. Rounds ∝ 1/output, and net drain = net-per-round ×
  rounds, so **+1% output = −1% net HP drain, exactly.**
- **Mitigation stats** (Def, Eva, Barrier, Regen) cut a gross term without
  changing fight length, so they are **leveraged by `gross / net`** — because
  net drain is a *difference* between gross incoming and regeneration.

Measured leverage against the three classes that cause ~72% of deaths:
**2.52× (Stealth Worm), 2.67× (Trojan Wall), 3.14× (Rootkit)**. Against the safe
classes it runs 4.5–20×, and at enemy level 1800 (where deaths actually happen)
it is higher still — so the values below are conservative.

### Re-fitted table

| weight | was | now | basis |
|---|---|---|---|
| `AtkDmg` | 0.7 | **0.7** | anchor; self-validates at 0.686 |
| `CritCh` | 0.7 | **0.7** | **validated** — crit rate 0.2631 on 954 single-hit rounds vs stat 0.2558 |
| `Def` | 1.0 | **0.45** | −0.88 elasticity × 0.435 pool × 0.41 channel × 2.7 leverage |
| `Eva` | 1.0 | **0.22** | same law, same slope, from the enemy side; Eva/Def = 0.497 |
| `AtkSpd` | 0.9 | **0.56** | 0.545% stat per affix point, linear in attacks/round |
| `CritDmg` | 0.35 | **0.22** | multiplier measured 1.883 vs stat 1.846; +1pp = +0.214% output |
| `Acc` | 0.14 | **0.21** | 0.428 pool × 0.45–0.50% output per stat-% (unbiased fit) |
| `Thorns` | 0.05 | **0.13** | `ptd` = 72.08 per enemy hit vs stat 73.4 — exact |
| `ArmorPen` | 0.05 | **0.068** | +97 pts = +6.1% output at enemy Defense 1,500 |
| `MaxHP` | 0.5 | 0.5 | **still unmeasured** — pure attrition buffer, invisible to a full-HP regime |
| `Regen` | 0.6 | 0.6 | **still unmeasured** — same reason |

**`Def` and `Eva` fell hardest** (2.2× and 4.5×), and both for the same two
reasons: the pool conversion, and the fact that neither touches the corruption
channel — Evasion does not even dodge it, since ticks land on missed rounds
(§16).

**`Thorns` rose 2.6×.** It is charged per enemy hit taken, so its value grows
with fight length: 0.120 at enemy level 1800, 0.157 at 2100, 0.141 at 2500.

### What is still unpriced

`MaxHP` and `Regen` are the two largest remaining holes, and they are the same
hole: both are pure attrition terms, and the Software Profiler runs **full-HP
single fights**. Neither can be measured until the **CI/CD Pipeline** (homelab
12). Given that deaths are ~100% attrition (`decision-log.md`, 29 Jul), these
are probably the two most valuable stats in the build and they are currently
carried on 22 July guesses.

## 20. Contract board reset: the ACTIVE contract carries through (player-observed 6 Aug 2026)

**A started (active) contract survives the daily UTC board reset and runs to
completion.** What the reset replaces is the rest of the board: unstarted
contracts and the clear-bonus opportunity. Provenance: direct player
observation at the 6 Aug 00:00 UTC reset (Marathon Elimination active and
mid-progress through the boundary), n=1. The prior model — "unfinished
progress is destroyed at reset" — was **asserted on 28 Jul and never
tested**; a 9-pair straddle scan of the capture archive cannot distinguish
the two models (every post-reset capture lands hours late, after a carried
contract would have completed and been claimed), so the live observation is
the only direct evidence in existence and it wins.

Consequences, encoded in `ih.py audit`:

- An active contract that cannot finish inside the board window is **not a
  loss** — it carries. Its real cost is **occupancy**: while it runs past
  reset, the new board's contracts idle (only one contract accrues, queue
  capacity 0). Price it against the new board's best rate (~3 hc/combat-h),
  not against the reset clock.
- The endgame play in the last hours of a board: clear the small fast
  contracts first (they die at reset if never started), then **start the
  largest-remaining contract just before reset** so it carries.
- The board-clear bonus still requires everything cleared before reset.

Residual unknowns in `open-questions.md` §16 (payout observation, inactive
partial progress, board state after a carried completion).
