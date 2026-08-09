# Candidate and Craft Status — 9 August 2026

**This page holds only what the tool cannot compute.** Everything per-item —
ceilings, keep/discard verdicts, lock deltas, which bases are at risk — is
generated from the latest capture by `ih.py potential`, `ih.py locks` and
`ih.py brief`. Do not read a number off this page and do not add one.

That rule is not tidiness. Until 9 Aug 2026 this file hand-maintained a
candidate table, a "next craft" verdict, a live-decompile-lock line and a list
of five reserved CI/CD probe arms. On 9 Aug **every single item named in those
sections was checked against the capture and none of them existed any more** —
the inventory had turned over completely. The page still read as current, and
the `/advise` protocol reads it for "holds/locks". A hand-kept list of owned
items is a model fitted on currently-owned state, and it rots exactly as
`CLAUDE.md` says such models do.

## Main set (all eight slots)

Query it: `python3 scripts/ih.py loadout`. All eight slots are contract crafts.
Slot history lives in `decision-log.md`; grades in `ih.py calibration`.

## Standing holds — reasoning the tool does not encode

These are *arguments*, not items. Each names a condition, so it can be
discharged rather than quietly inherited.

- **Sustain-anchor guardrail (`mechanics.md` §21).** Firewall / Router / Kernel
  replacements must preserve the *function* of the current sustain anchors, not
  merely improve item level or score. Regeneration is this build's measured win
  condition (net drain per round went negative on the 27 Jul package, and the
  Regen law has now passed three out-of-sample forward tests), so a candidate
  that clears `UPGRADE_BAND` while spending Regen is still a hold. `potential`
  prints the `from:` decomposition precisely so this is checkable at a glance —
  read it before accepting a headline score in these three slots.
- **Corruption-carried candidates are extrapolation past ~72.** `Corrupt` is
  linear to a verified stat level of ~72 (30 Jul, paired profiler arms) and
  every large Corrupt ceiling on the current board sits well past it. This is
  why `SUSPECT_WEIGHTS` exists and why `locks` decides on the weaker of the raw
  and ex-suspect readings.
- **Reserved probe arms are declared in code, never here.** See below.

## Reserved CI/CD probe arms

**Declared in `scripts/experiments.py::RESERVED_PROBES`, by stat FAMILY, and
resolved against every fresh capture by `ihlib.probe_levers`.** `ih.py audit`
reports two findings against them: `PROBE-LOOSE` (an arm exists but is
unlocked, one sweep from deletion) and `PROBE-GONE` (no owned item is a pure
enough lever, so the measurement cannot run until a drop arrives).
`ih.py locks` prints the held arms with their purity and never offers one for
decompile.

A probe arm is chosen for what it **isolates**, so `plan_craft` scores it as
junk by construction and value-based lock advice sorts it straight into the
discard pile. That is the same blind spot `protected_revert_items` closes for
A/B revert paths, and it was open for instruments until 9 Aug 2026 — which is
how the previous five arms (`Pinpoint Kernel of Rejuvenation`,
`Assault Kernel of Penetration`, `Guided Kernel of Restoration`,
`Prolific Driver of Isolation`, `Slippery Driver of Sandboxing`) were lost
while this page still listed them as reserved.

Live reservations as of 9 Aug 2026 — read the current state off `ih.py audit`,
not off this list:

- **ArmorPen** — the one `PENDING_REFITS` row. Two arms held.
- **MaxHP** — asserted at 0.5, never validated, the largest unpriced term in
  the model. Currently **`PROBE-GONE`**: nothing owned clears the purity floor,
  so this measurement is waiting on a drop, not on a decision.

## Decompile protocol

**`ih.py locks` is the authority.** It prints deltas only — items whose flag
disagrees with their value — plus the `AT RISK` block (band-clearing bases
outside the depth cap that are already unlocked and will go silently).

- The operating model is that **anything not locked is regularly decompiled and
  lost**, so a missing lock is an irreversible loss and drift in either
  direction costs progress.
- Keep value is the **weaker** of raw Δ and Δ-ex-suspect; a discard needs
  **both** readings to agree. An item they disagree about is held, not ignored.
- Hold depth is `KEEP_DEPTH_PER_SLOT` bases per slot, sized on how long a base
  of **equal quality** takes to replace (~6.8 days top-decile), never on the
  rate at which any band-clearing base arrives.
- **Before decompiling, check the item is not a sole ladder anchor.** Since the
  archive-wide ladder fix (`crafting.md` §12.1.1) a decompile can no longer
  *lose* an observation — every past capture still counts — but an item
  carrying a tier no capture has ever recorded is still worth one capture
  before it goes.
- **Never reuse a static safe-decompile list**, including any that appear in
  the git history of this file. They were built against inventories that no
  longer exist; that is the failure this page was rewritten to stop.
