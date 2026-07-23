# Decisions Log — Pokebot_Gen3_Enhancement
> APPEND-ONLY. New entries at the end. Never rewrite history — if a decision
> is reversed, append a NEW entry that supersedes the old one and says so.

---

## 2026-07-17 — Adopted the Claude Code Project Kit
- **Decision:** Standardize on the kit's CLAUDE.md directives + PROJECT
  KNOWLEDGE structure + per-item commit/push definition of done.
- **Context:** Make every session resumable by any agent with zero context.
- **Alternatives rejected:** Ad-hoc per-chat context pasting (doesn't scale,
  loses history).

## 2026-07-17 — Vendor upstream via git subtree (squashed), not clone/submodule
- **Decision:** Import 40Cakes/pokebot-gen3 into `pokebot-gen3/` with
  `git subtree add --squash` and keep an `upstream-pokebot` remote.
- **Context:** The enhanced fork must live IN this repo (user requirement),
  while still being able to absorb upstream fixes.
- **Alternatives rejected:** plain clone kept as nested repo (files not
  tracked in our repo); git submodule (poor fit for a fork we edit
  heavily); copy-without-history (loses the cheap upstream-update path).
- **Consequence:** upstream updates come via
  `git subtree pull --prefix pokebot-gen3 upstream-pokebot main --squash`;
  our edits to vendored files should prefer extension points (plugins,
  bot modes, HTTP API) to keep those merges cheap.

## 2026-07-17 — Installer enhancement will ADAPT, not literally apply, the base64 pattern
- **Decision (provisional, to finalize at punch-list #4):** The
  installer-as-codebase pattern (REFERENCE-INSTALLER-PATTERN.md) assumes a
  no-git, ~50-file pure-source program. This project is git-based and the
  bot is ~90 MB with thousands of binary assets, so a literal single-file
  base64 installer is infeasible; we will instead deliver its UX
  (one-script setup/update/heal, drift detection, protected user files)
  on top of git/subtree mechanics.
- **Alternatives:** literal base64 installer (rejected: size, binary
  assets, duplicates git's job); upstream's updater.py as-is (rejected:
  tied to upstream GitHub releases, no heal/verify step).
- **Status:** flagged for user sign-off when #4 is designed.

## 2026-07-17 — Two-folder fork layout + daily upstream sync (user directive)
- **Decision:** Restructure to (a) `40cakes repo/` holding a PRISTINE
  upstream mirror (`pokebot-gen3/`, git subtree re-added at the new
  prefix) plus all documentation about the original program
  (`DOCUMENTATION/`, with `_history/` snapshots and an append-only
  `UPDATE-LOG.md`); and (b) `custom-pokebot/` holding our enhanced fork
  with its own `DOCUMENTATION/` and `DIVERGENCE-LOG.md`. Upstream is
  checked DAILY (session-start directive in CLAUDE.md); updates are pulled
  into the mirror and its docs updated (old versions snapshotted), but
  NEVER auto-applied to the custom fork — they're listed for user review.
- **Context:** Direct user instruction 2026-07-17: keep a running,
  up-to-date record of the original repo separate from our custom version,
  with original-docs and custom-docs cleanly separated and historical doc
  versions retained.
- **Alternatives rejected:** single vendored copy enhanced in place
  (previous layout — conflated upstream tracking with our changes);
  git branches for original-vs-custom (invisible on disk, user wants
  folder-level separation).
- **Consequence:** the subtree prefix moved, so the pull command is now
  `git subtree pull --prefix="40cakes repo/pokebot-gen3" upstream-pokebot main --squash`.
  Custom and mirror start identical at upstream `5dd898f8` (git stores the
  duplicate blobs once, so repo size is unaffected).

## 2026-07-17 — Installer implemented as git-driven one-script (supersedes provisional entry)
- **Decision:** `install.py` at repo root implements the installer-as-
  codebase UX (one script = install + update + heal, colored 6-step output,
  SCRIPT_VERSION, idempotent) with git as the integrity mechanism instead
  of base64+SHA-256 dicts: drift detection = `git status --porcelain`
  against tracked files; heal = consent-gated `git checkout --`; update =
  `git fetch` + fast-forward-only pull; user data protected by being
  untracked/gitignored (profiles/, roms/, saves). It additionally locates
  (or offers to winget-install) the 64-bit Python 3.11-3.13 the bot needs
  — the installer itself runs on any Python 3.8+ — and pre-runs the bot's
  own `check_requirements()` bootstrap for dependencies.
- **Context:** REFERENCE-INSTALLER-PATTERN.md assumes a no-git ~50-file
  pure-source program; this repo is git-based, ~9,000 files with binary
  assets. Embedding as base64 was infeasible; git already provides
  hash-verified content.
- **Alternatives rejected:** literal base64 single-file (size, binary
  assets, duplicates git); upstream updater.py alone (release-zip based,
  no heal, self-disabled in git checkouts anyway).
- **Verified on this machine:** check-only, corrupt→heal→restore, full dep
  install into Python 3.12, fresh-empty-folder clone (caught and fixed the
  Windows MAX_PATH clone failure via core.longpaths), unattended --yes
  mode, EOF/BOM-safe prompts.

## 2026-07-18 — Emerald ROM stays tracked in the repo (user ruling)
- **Decision:** The user uploaded their Emerald ROM (`custom-pokebot/roms/`,
  SHA-1 matches the bot's whitelist) to the PRIVATE repo via GitHub web and,
  when presented with purge/untrack/keep options, chose **keep it as is**.
  Do not re-raise this for THIS file.
- **Context:** Convenience — every clone of the private repo is instantly
  runnable/testable. Risk (repo carries copyrighted game data; matters if
  the repo ever goes public) was explained and accepted by the user.
- **Consequences:** `.gitignore` still blocks accidental *local* ROM
  commits (`roms/*`); the tracked file is unaffected by ignore rules. If
  the repo is ever made public, this decision MUST be revisited first.
  Agents must still never commit additional ROMs/saves/profiles themselves.

## 2026-07-21 — Skip the forced PokéNav Match-Call tutorial via a targeted state-write
**Decision:** `skip_pokenav_match_call_tutorial()` clears Emerald's forced PokéNav/Match-Call
tutorial (the Rustboro Scientist, after the PokéNav) by WRITING the exact game state the
tutorial itself leaves on completion — `VAR_RUSTBORO_CITY_STATE=7`, `VAR_ROUTE104_STATE=1`,
flags `HAS_MATCH_CALL`/`ADDED_MATCH_CALL_TO_POKENAV`/`HIDE_RUSTBORO_CITY_SCIENTIST` — rather
than playing the tutorial through its PokéNav app UI.
**Why:** the tutorial ends only once you place a Match Call to Mr. Stone through the PokéNav
app (mode `POKENAV_MODE_FORCE_CALL_READY`). That app is graphics-driven and does NOT advance
in our headless faithful harness (empirically: ~150 A-presses over 1500 frames = zero
progress). So a UI-navigation solution (a) can't be proven with our reproduce/fault-inject
methodology and (b) would hang every full-flow harness run at that point. Match Call has no
bearing on story progress toward the Elite Four.
**Alternatives rejected:** (1) full PokéNav-app automation — un-provable in our harness,
brittle, and the app may be graphics-gated even on the real bot; (2) stopping the bot at the
tutorial for manual play — defeats the unattended-Story goal. (3) A/B/cursor mashing — proven
not to clear it.
**Faithfulness note (FLAG FOR USER):** this is a deliberate divergence — a memory-write, not
natural play. The RESULTING save is byte-equivalent to having watched the tutorial (same
vars/flags), so downstream story state is unaffected. If the user prefers a fully faithful
playthrough here, the alternative is real PokéNav-app automation (costly, currently
un-validatable headless). Revisit if faithfulness at this beat matters more than robustness.

## 2026-07-21 (revised) — PokéNav Match-Call tutorial: FAITHFUL primary, state-write fallback
**Supersedes the earlier same-day decision.** Per user directive ("try to be faithful; keep
the state-write as a fallback if it doesn't always work"), `handle_pokenav_match_call_tutorial()`
now FAITHFULLY plays the tutorial — it opens the PokéNav, navigates to Match Call, calls
Mr. Stone, and backs out — exactly as a player would. This became viable once we found the
real blocker: the PokéNav app's looped tasks only advance when the **BG/OBJ renderer is
enabled** (`context.video=True`); the user's real bot runs with video on. Proven end-to-end
via `_play` (screenshots confirmed every menu screen; the call places and the tutorial
completes with `VAR_RUSTBORO_CITY_STATE=7`, no fallback used).
**Fallback retained:** on a headless run (renderer off) or if the nav stalls, it falls back
to `skip_pokenav_match_call_tutorial()` (state-write to vanilla's exact end-state). So the
tutorial always clears and the bot never hangs — faithful when it can be, robust always.
**Why this is better than the pure state-write:** it preserves the bot's value as a faithful
reference (it actually performs the in-game actions) while keeping the deterministic fallback
for edge cases. The earlier "pure state-write" decision is retained only as that fallback.

## 2026-07-23 — Derive the Lavaridge maze from ROM data; don't explore it or hardcode it
**Decision.** `do_lavaridge_gym` scans both floors at run time (holes / geysers / ledges),
builds the chamber graph, and BFSes it from wherever the player actually stands.
**Alternatives rejected.**
- *Keep the live explorer* (walk to the nearest untried hole, blacklist duds). Rejected:
  it had already burned five runs and every added heuristic moved the failure rather than
  removing it — it had no model of what a productive move IS.
- *Hardcode the canonical chain* from the walkthrough (the previously queued plan).
  Rejected: it encodes no recovery. One battle knock-off or surprise landing puts the bot
  off-script with nothing to fall back on. Deriving costs ~650 `get_map_data` reads once
  and yields a plan from ANY position, which is exactly what recovery needs. The derived
  chain is printed by `tools/story-dev/lavaridge_gym_solve.py` for review either way.
**Why it matters beyond this gym.** Every remaining warp/terrain puzzle (Sky Pillar,
Mossdeep, Sootopolis ice) is the same shape: read the behaviours, build the graph, solve.

## 2026-07-23 — Research answers never supply numbers the ROM already knows
**Decision.** All external research (Gemini app relays, the new API relay, any future
source) is consumed as JUDGMENT + SOURCING only: which moves/mons/TMs matter and why.
Every machine-checkable number (learnset levels, TM/HM compatibility, stats) is derived
from `modules/data/` at build time, never copied from a research answer.
**Basis (measured, not vibes):** the Batch-1 grading — TM-compat claims 98% right but
level claims only 42% right, with some flatly invented; and the API relay's own first
test got both asked-for levels wrong. Three sources gave three different numbers for the
same fact; only the ROM extraction is authoritative.
**Alternative rejected:** trusting well-cited research numbers and spot-checking. Rejected
because the error rate is high enough that spot-checks would miss real errors, and the
machine check is nearly free (`grade_pokeprofiles.py` is the template).

## 2026-07-23 — Proactive prep is a hint; reactive escalation is the guarantee
**Decision.** The sweeper-sufficiency gate only governs FIRST attempts (losses < 2);
whenever the bot is losing, the reactive layer (escalation / boss-training) owns the
decision and the gate steps aside entirely.
**Why.** A wrong "sufficient" call then costs 1-2 self-correcting losses (cheap: Gen 3
whiteout ≈ level × badge-payout), while the old always-band-prep cost hundreds of
redundant encounters per gym per run — the measured #24-train-efficiency ceiling.
**Alternatives rejected.** (a) Perfect pre-battle damage simulation — needless
complexity when losses self-correct; (b) skipping team training unconditionally — the
adversarial consult's surviving objection (between-gym gauntlets hit the bench) argues
for keeping band prep whenever no sweeper exists.
