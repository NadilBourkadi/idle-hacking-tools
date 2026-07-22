# Idle Hacking Project — Operating Workflow

This workflow is designed for someone accustomed to Claude Code/Codex CLI sessions but new to ChatGPT Projects.

---

## 1. Project structure

Use the Project as the stable context layer. Use individual chats as focused sessions.

Recommended chats:

### Current build and next upgrade

Use for whole-loadout review and deciding the highest-value slot to target.

### Candidate evaluation

Upload/export a batch of newly opened candidates. Keep one chat per meaningful batch if the transcript becomes noisy.

### Combat log analysis

Upload failed and successful run logs. Ask for quantitative diagnosis: miss rate, damage rate, sustain, attrition and likely bottleneck.

### Mechanics research

Use for controlled tests, community/documentation research and formula hypotheses.

### Userscript development

Use only for the passive capture tool. Keep code changes and DOM diagnostics separate from game-strategy discussion.

### Progress journal

Record decisions:
- equipped/decompiled/kept item;
- scarce resource spent;
- target zone changed;
- mechanic confirmed;
- tool version updated.

---

## 2. Routine item workflow

1. Refresh the game and confirm v0.5 panel is present.
2. Click all equipped slots if the loadout counter is incomplete or stale.
3. Clear candidates when starting a new review batch.
4. Click each candidate item in the inventory.
5. Confirm:
   - Equipped is 8/8;
   - candidate count matches the intended batch.
6. Download or copy JSON.
7. Upload it to the Candidate evaluation chat.
8. State the current objective:
   - pushing;
   - safe long streaks;
   - Hack XP;
   - resource farming;
   - alternate set.
9. After making a change, export a new loadout snapshot.

---

## 3. Routine combat-analysis workflow

For a useful diagnosis, collect:

- several losses, not just one;
- representative successful fights if possible;
- enemy/zone/level;
- starting and maximum HP;
- streak length;
- round-by-round attacks, hits, misses, crits and damage;
- regeneration and barrier;
- any enemy modifier/class.

Ask the assistant to answer in this order:

1. Was the loss primarily attrition or matchup strength?
2. Was hit reliability adequate?
3. Was outgoing damage too low?
4. Was incoming damage/burst too high?
5. Which one or two stats would most likely change the result?
6. Which current slot is the least costly place to obtain those stats?

---

## 4. Updating the Project sources

Treat the Markdown files as maintained documentation.

When the state changes substantially:

1. Ask ChatGPT to produce an updated replacement file.
2. Save it into the local handover directory.
3. Optionally commit it to Git.
4. Replace the old Project source or upload the new dated version.
5. Avoid keeping many contradictory “current state” files.

The structured loadout JSON should usually be dated. The prose `03_CURRENT_STATE_AND_LOADOUT.md` should represent the latest reviewed baseline.

---

## 5. Using ChatGPT web/desktop versus CLI

### ChatGPT Project

Best for:

- shared long-term context;
- analysing uploaded game exports;
- keeping strategy, mechanics and tool design together;
- creating documents and summaries;
- branching into separate chats without repeating the background.

### Claude Code / Codex CLI

Best for:

- editing the userscript in a local folder;
- running linters/tests;
- Git history;
- diffs and code review;
- working with multiple source files directly.

A practical hybrid:

```text
~/projects/idle-hacking/
  docs/
  tools/
  data/
```

Use CLI agents against that folder. Upload stable releases and current data snapshots into the ChatGPT Project. The ChatGPT Project is the knowledge workspace; the local folder is the engineering workspace.

---

## 6. Prompt templates

### Evaluate a candidate batch

> Treat the uploaded structured export as the current source of truth. Confirm the loadout is complete, then evaluate every candidate against the current item in its slot. My current objective is [objective]. Classify each as immediate upgrade, enhancement project, sidegrade/alternate-set item, keep for later, or decompile. Do not use Item Level alone.

### Diagnose losses

> Analyse the uploaded combat logs quantitatively. Separate accumulated streak attrition from the strength of the final enemy. Estimate the main bottleneck among hit reliability, outgoing damage, incoming damage and sustain, then map that bottleneck onto the cheapest loadout slot to change.

### Research a mechanic

> Investigate [mechanic]. Separate direct evidence, community/documentation claims and inference. Give me a minimal controlled in-game test that would falsify the current working model.

### Update the handover

> Update the relevant Project source using the new evidence from this chat. Preserve verified facts, mark inferred mechanics clearly and remove stale current-state details.


---

## 7. Craft-aware candidate workflow update

For each serious candidate:

1. Capture a complete 8/8 loadout and the candidate's crafting snapshot.
2. Treat the current item as the benchmark and the candidate as an uncrafted base.
3. Declare forced Augment side and Continue/Conditional/Abort results before clicking.
4. After Augment, export immediately.
5. Use tier targets, maximum attempts and an explicit Compile floor.
6. Export the finished item before equipping.
7. For A/B tests, deduplicate identical logs and record the exact item delta.
8. Prefer matched enemies/settings; otherwise label conclusions directional.
9. Record the decision in `10_DECISION_LOG.md`.

Current observed capture runtime is 0.6.1/schema 4, although its source file is not archived in this pack.
