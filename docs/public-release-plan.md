# Public-release plan — audit findings, decisions, and execution checklist

Written 6 Aug 2026 (late night), from the public-readiness audit run that evening
(two parallel agent audits — Python code quality; hub/userscript security — plus
an inline privacy sweep). This document is the persistent capture of everything
found and decided, per the owner's instruction, so the work survives any session
boundary. Check items off as they land; anything unchecked is still owed.

## Decisions (owner, 6 Aug 2026)

1. **License: MIT.**
2. **Data is excluded from the public repo entirely — no manifest.** The
   codebase must be **portable**: a stranger (or a fresh machine) starts with a
   completely fresh save and an empty `data/`, and everything works. The
   historical context (decision log, mechanics docs, equipment tests) stays in
   the repo as the research record, but the **campaign is quarantined from the
   code**: player-specific records (A/B experiment declarations) move out of
   the library core into a clearly-labelled campaign module; docs are framed as
   one campaign's research log.
3. **Anonymize, unrecoverable from git history**: commit author email → GitHub
   noreply form; in-game player name, personal email, and home paths scrubbed
   from every historical blob (`git filter-repo` replace-text + path purge);
   data trees purged from history entirely. Author *name* stays (the repo is
   published for professional credit). ⚠️ Before the first push, the owner
   should supply their real GitHub noreply address (`ID+user@users.noreply.
   github.com`) for a final 30-second mailmap pass — until then a placeholder
   noreply is used.
4. **Fix everything identified, now** — all seven task-list workstreams, not
   just the publish-blockers.

## Audit findings — condensed but complete

### Fixed on discovery during the audit session itself (done, verified)

- `credit_runway` crashed `audit` on captures lacking `homelabInfo` (3 archive
  captures) — guarded.
- `cmd_audit` CREDITS flag hardcoded "~12M/hr" beside numbers computed at the
  re-fitted 24M — now interpolates `ihlib.CREDITS_PER_HOUR`.
- `hit_chance` docstring + a `SUSPECT_WEIGHTS` comment quoted the retired
  pm-biased hit fit (0.532/1.208) while code used −0.164/1.420 — restated.
- `_chk_hardware_curve` unpacked a possible `None` → opaque `[ERROR]` — SKIPs.

### Security (hub + userscript) — agent report, prioritized

**Must fix (task #1, #2):**

- **Hub `POST /export` drive-by write vector**: content-type-blind +
  unauthenticated → a CORS *simple request* from any web page can plant fake
  captures (source-of-truth #1) or fill the disk (32 MB/request). Fix: require
  `Content-Type: application/json` exactly (forces failing preflight; real
  userscript unaffected — GM_xmlhttpRequest bypasses CORS, already sends it),
  plus optional shared-secret header.
- **Userscript IndexedDB create-on-open**: versionless `open(SIM_DB_NAME)`
  implicitly creates an empty v1 DB when absent — violates the read-only
  contract and could break the game's own sim-history store creation. Fix:
  `indexedDB.databases()` pre-check or abort the upgrade transaction.
- **`@updateURL`/`@downloadURL` point at plain-HTTP localhost:8123** — for
  strangers, auto-update-from-whatever-squats-the-port with GM privileges.
  Strip from published copy or repoint to GitHub raw HTTPS.
- **systemd unit hardcodes `~/...`** — template with `%h`; add
  hardening keys (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=strict` +
  `ReadWritePaths`); note restart-loop-on-port-squat.
- Safety-text nuance: `JSON.stringify` + dotted reads WOULD invoke
  getters/`toJSON` if game objects defined them — state the plain-data
  assumption explicitly in the header.

**Lower severity (task #1):** handler `timeout = 30` (Slowloris); wrap
malformed `Content-Length` → 400; `open(path, "xb")` retry in `unique_path`
(TOCTOU + symlink); skip-and-warn corrupt ledger lines in `_load_seen*` (one
truncated line 500s every later stream POST); stop echoing `str(error)`/paths;
fight-dedupe day-scope vs sim archive-scope asymmetry (fix or comment);
optionally decouple hub from full-ihlib import.

**Verified clean:** no game-function calls; no synthetic input; all traffic
localhost-pinned (`@connect`); filename sanitizer genuinely traversal-proof;
binds 127.0.0.1. Userscript minor: `{readMethod, ...parsed}` spread pollutes
payload schemas (→ `{readMethod, data}`); prefs in game-origin localStorage
(→ `GM_setValue`); `@version`/`TOOL_VERSION` two hand-synced sites.

### Python quality (ihlib.py + ih.py) — agent report, prioritized

**Must fix:** (1–3 and 5 done on discovery, above) plus **(4) `SystemExit`
raised from library code** (`load_capture`, `record_prediction`) — blocks
pytest, poisons importers (hub imports ihlib), conflates "panel missing" with
"precondition failed" in `_section_output`. → `FileNotFoundError`/`ValueError`
raised in ihlib; translated to `sys.exit` at the CLI boundary. (Task #5.)

**Library hygiene (task #5):** hardwired module-level paths with no injection
(`stream_records`, `fight_cadence`, `measured_credits_per_hour`,
`latest_stream_ms/player`, `record_prediction` lack the `dir_` override
`sim_records` already has); `_STREAM_CACHE` yields shared mutable dicts
(comment-guarded only) and `_LADDER_ARCHIVE_CACHE` unbounded; `cmd_audit` is a
~330-line inline function → extract `check_*(cap) → [flags]`; no capture-load
cache (144×1MB re-parsed by `captures`/`history`/`experiment_status`; `brief`
multiplies it).

**Correctness smells (task #7):** archive-ladder fit silently skips malformed
captures (count + surface); unregistered inline tunables violating the
register's own rule (enemy-growth 1.011/streak, `CORRUPT_STACK_CAP = 6`,
`5 × cicd_level`, "~3 hc/combat-h"); `stale_panels` attributes cross-section
credit disagreement to the *non*-min section (min is likelier stale); dead
code (`ENEMY_CLASSES_UNIFORM`, `latest_stream_player(before_ms)`); local-import
hacks (`__import__("re")`, shadowed `import math`, `import datetime as _dt`);
triplicated `capturedAt` parsing + `captured_ms` local shadowing the function +
duplicated filename regex → `captured_ms()` everywhere + one
`capture_filename_ts()`.

**Consistency (task #7):** `ih.py` module docstring omits `sims`/`brief`;
`cmd_sims` prints local times but groups UTC day-blocks; zero type hints —
annotate the pure numeric layer only (`mult_scale`, `stat_total`,
`hit_chance`, `vu_expected_*`, `ladder_value`, `hardware_cumulative`), never
the capture schema.

**Structure:** monolith "defensible but at its limit"; natural 8-module split
mapped (capture / craft / facilities / freshness / ledger / experiments /
sims / register with `__init__` re-exports). Decision: **only the experiments
extraction ships now** (it implements the campaign quarantine); the full split
stays optional. `_brief_*` stdout screen-scraping → structured rows is also
deferred-optional.

**Tests (task #6)** — repo has zero; the 8-test seed suite by confidence per
line: ① `stat_total`+`validate_stat_totals` vs a committed **sanitized,
trimmed** capture fixture (identity fields stripped — data is excluded from
the repo, the fixture is the one deliberate exception); ② seeded
`simulate_contract` with/without `baseline` (deepen-scale regression);
③ `plan_craft` on synthetic item/ladder; ④ `ladder_value` three regions +
`measured` flag; ⑤ `inflate_compact`+`unbiased_hit_rate` round-trip incl.
`bm` bitmask; ⑥ `record_prediction` realized-update (orphan-row regression);
⑦ `experiment_status` pre/post classification on synthetic ledger
(`boundary_fight_id` — subtlest code in the repo); ⑧ `audit` on a capture
lacking `homelabInfo` (crash regression). Written **unittest-style** (runs
with zero installs, matching the pure-stdlib ethos; pytest in CI runs them
fine). Plus `pyproject.toml` (ruff config, metadata) and a GitHub Action
(ruff + tests).

### Privacy sweep (inline) — findings

Captures contain **no secrets** (no tokens/JWTs/cookies/endpoints; only
in-game `username`, game-internal `player_id`, already-masked steam id).
Personal strings in the repo: commit author email; `~` in the
systemd unit; player name in `CLAUDE.md` + 4 doc mentions; the initial-commit
handover files (`00_START_HERE.md`, `01_PROJECT_INSTRUCTIONS.txt`,
`MANIFEST.json`, `SHA256SUMS.txt` — deleted at HEAD, alive in history).

## Execution checklist

- [x] 0. This plan committed; all outstanding work committed (pre-fix checkpoint).
- [x] 1. Hub hardening (task #1) + userscript fixes (task #2), `@version` bump, service template+hardening.
- [x] 2. LICENSE (MIT), README rewrite (portable-toolkit + campaign-log framing, quickstart from a fresh save), `.gitignore` (`data/`, `.mypy_cache/`), `pyproject.toml`.
- [x] 3. Library hygiene (task #5): exceptions at the boundary, ledger path injection, cache hygiene, `check_*` extraction, capture-load cache. **Campaign quarantine**: experiment dicts → `scripts/experiments.py` (pure data, re-exported by ihlib for compatibility).
- [x] 4. Fresh-save portability: every `ih.py` command degrades gracefully against an empty `data/` (friendly message, no traceback) — verified against a temp dir.
- [x] 5. Polish batch (task #7), full list above.
- [x] 6. Tests ×8 (task #6) green under `python -m unittest`; sanitized fixture; CI workflow file.
- [x] 7. Current-file anonymization: player name → "the player" in CLAUDE.md/docs; service path templated.
- [x] 8. `git rm --cached` all `data/` trees; commit.
- [x] 9. History rewrite (`git filter-repo`; fallback `filter-branch`): purge `data/` + handover manifest paths from all history; replace-text map (personal email → noreply, player name → "the player", `~` → `~`); author mailmap (name kept, email → placeholder noreply pending the real one). Verify: history-wide grep for the scrubbed strings comes back empty; `git gc`; sizes reported.
- [x] 10. Hub service restarted on the hardened code; full command matrix re-run against live data; final report.

## Post-release follow-ups (not blocking)

- Owner supplies real GitHub noreply → final mailmap pass → create remote, push.
- Optional: full 8-module package split; `_brief_*` structured-rows refactor;
  mypy on the numeric layer; `git maintenance start`.

## Completion record (7 Aug, ~00:15)

Every checklist item executed. History rewrite verified: all three identity
patterns CLEAN across every historical blob; single noreply author; data and
handover manifests purged; **repo 247M → 1.9M packed, 50 commits of full
code+docs history preserved**. Pre-rewrite safety bundle (contains the
un-anonymized history — keep it private) at
`~/Dev/idle-hacking-tools-prerewrite-20260807.bundle`. Hub restarted on the
hardened code (415 on the drive-by vector, userscript 1.7.0 served);
fresh-clone simulation passes (graceful empty-data messages, 16/16 tests on a
bare interpreter). Outstanding before push: the real GitHub noreply address
(30-second mailmap re-run), create the remote, one manual Tampermonkey update
to 1.7.0 (auto-update headers are gone by design).

## Addendum (7 Aug, during execution)

- Owner directive mid-execution: **human-readable naming conventions** —
  executed as a targeted rename of the cryptic minority (`composed_stat_total`
  / `item_stat_totals` disambiguated, `version_upgrade_expected_*`,
  `scale_percent_value` / `scale_flat_value`, `format_cost`,
  `inflate_compact_combat_log`, `_hackcoin_per_hour`) with living docs
  updated; history docs keep period names. `ih.py` retained as the typed CLI
  name (documented ergonomic exception); full package split remains optional.
- Audit-check extraction verified by byte-identical `audit` output pre/post.
- 16-test suite green; ruff clean; CI workflow added.
- New `CORRUPT` audit check (capture-truncation proxy) added with the
  extraction.
