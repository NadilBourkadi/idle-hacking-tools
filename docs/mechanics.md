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
