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

## 2026-07-24 — KI-15: clear the post-battle input wedge at the RUN-LOOP seam, not in the rider
**Decision:** the stale post-battle battle-text wedge (blocks all input, only A clears it)
is cleared by StoryMode.run's per-frame nudge — signature (OVERWORLD + no battle + waiting
+ no scripts + PLAYER POSITION FROZEN) held 240 consecutive frames → ONE A → 1200-frame
cooldown. `_wait_until_cutscene_over` keeps its old museum-green behavior (parked waits =
free) and `navigate_to` gets only a fast no-progress bail (`NavigationStuckError`).
**Rationale:** the wedge is indistinguishable from a field dialogue's parked
WaitForAorBPress tail on EVERY memory reader, and both ignore B — three rider-side designs
(broad 40-frame B→A, narrow sTextPrinters signal, 450-frame B→A) all failed against the
museum-greeter regression probe or the captured wedge. The wedge's only unique property is
FUNCTIONAL (nothing can move), and the run loop is the only seam that persists across
primitives and can observe "frozen for seconds" regardless of which primitive is stuck.
**Rejected:** rider-side reader discrimination (no discriminating reader exists); rider-side
behavioral escalation (the tail never expires either, so it loops); patching the battle
handler (KI-15 was never a battle-handler bug — per the diagnosis).

## 2026-07-24 — Orchestration: premium orchestrator + cheap workers, gated by the HARNESS (not by model opinion)
**Decision:** adopt a tiered orchestration pattern (doc 16 + `/orchestrate` + four
`.claude/agents/`): a PREMIUM model (Fable 5; Opus 4.8 as the fallback tier) plans, writes
the spec, writes timing-critical code, and runs the gate; MID (Sonnet 5) implements and
builds proofs; CHEAP (Haiku 4.5) does recon and log triage; Gemini does external research
and an advisory second opinion. Roles name TIERS — the model per tier is one config table,
so a new top model slots in by editing one row.
**Rationale:** the user's constraint is premium-quota exhaustion, and multi-agent work does
NOT reduce total tokens — it moves work off the expensive tier and isolates worker context
from the orchestrator's. Researched with a 4-way Gemini cross-check; the ADVERSARIAL pass
materially changed the design: it argued (correctly, and matching this project's own bug
history) that cheap models produce confidently-wrong code on intermittent timing/state
bugs, that LLM-on-LLM review is theatre, and that a reviewer who must re-read the codebase
erases the entire saving. So the governing rule became: **delegate only what a
harness/probe/test can PROVE without the premium model re-reading the codebase** — which
works here specifically because this project already has that deterministic harness
(story_harness, repro_*, probe_*, livetest, audit_flag_names). Diagnosis of intermittent
wedges is explicitly NOT delegated.
**Rejected:** (a) pure-orchestrator/never-code — the tricky 20-line fixes are exactly where
premium judgment pays, and handing them down is where quality drops; (b) Gemini or a Claude
reviewer as the BLOCKING gate — advisory only, the harness wins ties; (c) unlimited
kick-back loops — capped at 1, because the ping-pong tax ends with premium reading the
whole failure transcript anyway; (d) hardcoding model IDs in the roles.
**Honest caveats recorded in the doc:** Gemini is badly STALE on model/pricing facts (it
claimed no Claude 5 family exists) — never use it for those; and an "Opus 5" is NOT in the
authoritative catalog (cached 2026-06-24) with no live Models API access from this machine
to check, so §7 gives a verify-then-edit-one-row procedure instead of wiring an unverified id.

## 2026-07-24 — Fodder grass: SKIP the grind rather than travel, and keep the trigger conservative
**Decision:** `_prepare_for_fight` treats a boss's local grass as fodder only when its
strongest wild is >12 levels below the team (`FODDER_LEVEL_GAP = 12`), and then prefers
RELOCATING to a better area but SKIPS training entirely when none is genuinely reachable.
Training detours are restricted to the CURRENT REGION (cross-region hops fail closed) and
each relocated area heals at its own nearest Poké Center.
**Rationale:** (a) 12, not the reactive boss-training check's 8 — this fires proactively,
before any loss, so it must not disturb prep that already works; measured, 8 would have
changed Wattson (R117 L14 vs L24) and left Roxanne borderline, while 12 fires only on the
pathological Norman case (R102 L4 vs L27-31) the user reported. (b) SKIP over travel because
recon proved there is nowhere better at that moment: pre-Surf, everything reachable from
Petalburg is L2-5 and every L19-28 band is across water or on the far side of the Go-Goggles
desert — and a lost boss attempt that KOs two of Norman's mons pays ~1,200 xp vs ~25 for a
Route 102 wild, so the re-attempt IS the better trainer. (c) Cross-region fails closed
because `calculate_path` cannot tile-check another region, and allowing a hop on the warp
graph's word alone would reintroduce the disconnected-pocket bug the same-region branch
exists to prevent (reviewer catch).
**Rejected:** level-fit-only selection (proposed Route 121, past Lilycove, to a pre-Surf
team); trusting same-map two-way path as proof of reachability (Route 111's tile is
desert-north, Route 114's is unreachable from every anchor — both caught by anchor testing);
hand-picked heal centres without verification (two of ten were wrong — Route 111 needed
Fallarbor, not Mauville).
**Open follow-up (user, 2026-07-24):** WATER training tiles once Surf is taught — surf
encounters are an untapped band and there is a lot of water. Logged as #24-watertrain.

## 2026-07-24 — Budget training in FRAMES, not levels (punch-list #24)

**Decision.** Gym-prep grind decisions are budgeted in estimated FRAMES
(`StoryMode.MAX_PREP_TRAINING_FRAMES = 250_000`) via a new
`training_areas.estimate_frames_to_level()`, instead of in levels
(`mon.level + 3`). An unknown estimate is treated as over-budget (fail safe).

**Why.** "Within 3 levels" reads as cheap but is a unit error: cost is frames, and
frames-per-level varies ~40× with the wild band. Measured on the real captured save that
produced the failure: Route 102's L3-5 wilds pay **28.7 xp/battle** at **1433 frames/battle**,
so taking a L33 Combusken to L36 (Blaziken) costs an estimated **502,983 frames**. A live run
committed to exactly that plan, spent ~2,000,000 frames, and hit its cap one level short.

**Alternatives rejected, and why — all three were measured, not assumed:**
1. *Relocate to a level-appropriate area.* This was my leading candidate and the data killed
   it: from the real captured position `calculate_path` reaches ONLY Routes 101/102/103, and
   production's own `_training_area_allowed` independently agrees. There is nothing better to
   relocate TO at that moment, so an area-picker would find nothing.
2. *Cap boss re-attempts.* Addresses the opposite failure (35 Norman whiteouts) but not this
   one, and the handoff's own record (~333,000 frames per boss cycle, approximate) suggests
   boss-refighting is more expensive per XP than the fodder grind it would replace.
3. *Raise/lower the level window.* Any level-denominated threshold is wrong for the same
   reason the current one is: it cannot see the XP rate. Tuning it just moves which map it is
   wrong on.

**Verified not to disturb proven-good prep:** `repro_fodder_grass.py` passes unchanged —
Wattson still trains locally on Route 117, Roxanne on Route 116, Norman still skips the grind.

**Known limitation (documented in code):** `estimate_frames_to_level` takes a scalar
`wild_level`, not a map, so it models xp/battle with a single calibrated average
base_exp_yield (50.2, tuned to reproduce the measured 28.7 at wild_level≈4) rather than
reading a real per-area encounter table. Marked MODELLED, not measured; callers holding a real
map should read the table directly.

## 2026-07-25 — Ground decomp research in a LOCAL SPARSE CLONE, not per-file `gh api` fetches

**Decision.** The default method for grounding a claim against the pokeemerald decomp is a local
partial clone, not the GitHub contents API:
```
git clone --depth 1 --filter=blob:none --sparse https://github.com/pret/pokeemerald
git -C pokeemerald sparse-checkout set src data include     # ~44 MB
```

**Why.** The immediate trigger was a GitHub **403 after ~8 `gh api search/code` calls** in
validation round 3, but rate limiting is the least of it:
1. **ABSENCE claims become checkable.** "There is no warp to Birth Island outside
   `LilycoveCity_Harbor`" is provable by one whole-tree grep and *fundamentally unprovable* by
   fetching files one at a time — you can only ever confirm what you thought to look at. This
   project has been burned repeatedly by categorical absence claims, and this is the fix.
   Round 3 used it to settle several claims that earlier rounds could only mark UNRESOLVED,
   including that `src/pokeball.c` **does not exist** (ball logic lives in
   `battle_script_commands.c`) and that Jirachi has zero scripts and zero encounter entries.
2. **Whole-tree grep is free**, so lookups stop being rationed — which is what made earlier
   rounds stop at "unresolved" instead of pushing to an answer.

**Alternatives rejected.** *Keep `gh api repos/pret/pokeemerald/contents/<path>`* — still fine for
one already-known path, but it cannot answer absence and it rate-limits mid-round; it is now
marked SUPERSEDED in the handoff rather than removed. *A full clone* — unnecessary; `src data
include` is ~44 MB and holds everything cited so far.

## 2026-07-25 — `region_reach` is a NEW predicate, not a repair of `calculate_path`

**Decision.** Region-scale reachability is answered by a new module,
`modules/story/region_reach.py`, built on the ROM's own `MapConnections` + warps. `calculate_path`
was left exactly as it is.

**Why.** `calculate_path` is a tile-level A* and is *correct for what it does*; the bug was asking
it a question it cannot answer. It reads the Route 118/119/120 dual-elevation bridges as WALLS —
which is also why `_hold_walk_route()` and the hand-written `_leave_route120_north_bridge` exist —
so it reported ROUTE118, the real answer to Winona, as unreachable from ROUTE120, and it failed
even on a same-map Route 119 walk (y=5 to y=135, no map crossing at all). A reachability oracle
must be sound for the SCALE it is asked about; "can I get to that map" is a connectivity question,
and tile pathing is only correct for the final leg once we are already on the map.

**Alternatives rejected.**
1. *Fix `calculate_path` to understand dual-elevation bridges.* This is the tempting one. Rejected:
   it is a change to the shipped navigator that every existing mode depends on, to fix a caller
   that is asking the wrong question anyway — high blast radius, and it would still leave a tile
   pathfinder answering a region question.
2. *Widen `_training_area_allowed`'s tolerance (retry, relax, fall back).* Rejected: it papers over
   a wrong oracle with heuristics, and the failure mode is INVISIBLE (a false "no" raises nothing —
   the option is simply never proposed), so a heuristic would be untestable in practice.

**Consequence accepted.** The new oracle fails OPEN where the old one failed CLOSED (its
`KNOWN_GATES` table holds one hand-verified entry, so an underivable gate reads as passable). For a
*planner* that is the safer direction — a wrong "yes" costs a wasted walk that navigation fails
recoverably; a wrong "no" costs a whole run and says nothing. It must be grown before it gates
anything irreversible.

## 2026-07-25 — Hop count is a FILTER (`max_hops=4`), never a RANK

**Decision.** `region_reach` prices every edge — connection OR warp — at exactly 1 hop, and callers
use `max_hops=4` as a sanity bound only. Ranking stays with `counter_plan`'s own criteria (type
coverage, then verified tile, then encounter rate, then level fit).

**Why — measured, not assumed.** I expected "the answer is a handful of hops, the far cities are
many". Measured from ROUTE120 on the Winona-era save:

| target | hops |
|---|---|
| FORTREE_CITY | 1 |
| ROUTE119 | 2 |
| **LILYCOVE_CITY** | **2** |
| **ROUTE118** (the real answer) | **3** |
| MOSSDEEP_CITY | 4 |
| PACIFIDLOG_TOWN | 10 |

**Lilycove is CLOSER than Route 118 by this metric**, because a single ROM connection can span an
entire sea route. So uniform weighting compresses the whole same-landmass cluster into 1-4 and only
separates the genuinely far-flung. That is a perfectly good *filter* (`max_hops=4` cuts
Pacifidlog-class targets while keeping Fortree/119/118) and a useless *rank*.

**Alternatives rejected.** *Rank candidates by hops* — the measurement above kills it outright.
*Weight edges by map traversal length, or price travel in FRAMES* (so it composes with
`training_areas.estimate_frames_to_level`) — both are real, both are defensible, neither is needed
until hop count demonstrably mis-ranks something. Deferred as `#24-edgecost` rather than built
speculatively.

**Meta-rule this produced.** When you introduce a cost metric, MEASURE it against known-good and
known-bad cases before trusting it to rank. "Reachable" was a boolean that hid a cost; "hops" is a
cost that hides map size.

## 2026-07-25 — The Gemini Pro-3.1+ requirement is enforced in CODE, not by a doc rule

**Decision.** `tools/story-dev/gemini_relay.py` **refuses** any model that is not Gemini Pro 3.1 or
newer (`_is_pro_31_or_newer`, fail-closed on anything it cannot parse; Flash/Flash-Lite/Gemma
rejected regardless of version number). The escape hatch is an explicit `--allow-weak-model` flag
that names the consequence.

**Why a code guard and not a standing directive.** Because a standing directive is exactly what
failed. The relay's default was **already** `gemini-3.1-pro-preview`, and an agent still overrode
it to `gemini-2.5-pro` on ~35 research calls — by copying a stale example out of the module's own
docstring — and then spent a day concluding "Gemini is inaccurate" instead of checking its own
invocation. The tainted output was not subtly wrong: a hallucinated item with invented coordinates
AND an invented flag, HM07 placed in the wrong cave, a fabricated bike prerequisite. Calibration
afterwards showed 3.1-pro answered correctly the exact claims 2.5-pro got wrong twice.

**Alternatives rejected.** *Write the rule in `CLAUDE.md` / the playbook* — that is the thing that
just failed; a rule that can be skim-read past is not a control. *Fix the docstring example only* —
necessary but not sufficient; it removes one route to the mistake, not the mistake. *Remove the
`--model` flag entirely* — rejected: cheap factual one-liners genuinely do not need Pro, and
removing the choice would push people to edit the constant instead, which is worse.

**Follow-on rule kept live** (it generalises and has NO structural guard): when a tool gives bad
answers, check YOUR INVOCATION before concluding the tool is bad.

## 2026-07-25 — "Endless reset runs" ships as an IN-PROCESS bot mode, reversing the shipped launcher

**Decision.** `Story (ENDLESS RESET)` (`StoryEndlessResetMode`) is a real bot mode that loops
`Story (DEBUG - RESET)`'s `run()` inside the running emulator. **This REVERSED an already-shipped
implementation** — the first version was a GUI menu item that shelled out to
`tools/story-dev/endless_runs.py` as a separate headless process.

**Why the reversal.** The launcher version failed in the user's hands in the most literal way: the
dialogs appeared and *nothing happened*. The requirement was never "run a batch somewhere" — it was
"effectively chained debug reset bots", i.e. exactly what the user is already watching, repeated
back to back in THIS emulator. A separate headless harness satisfies the words and not the request.

**What the in-process form had to add** (a subprocess launcher gets these for free; a mode does
not): a `BotModeError` in run 3 is SWALLOWED so runs 4..N still happen; a hard 3.5M-frame per-run
cap (StoryMode's own watchdog cannot catch a wedged watchdog); the bot mode is re-asserted after
every run, because a derail can call `set_manual_mode()` and would otherwise silently end the
batch; and the batch's emulation speed + video are captured once and restored each run — the first
cut restored `bot_mode` but not the speed, so run 1 ran unthrottled and every run after it crawled
at 1x.

**Alternatives rejected.** *Keep the subprocess launcher.* Rejected on the user's direct report,
but note it was NOT deleted — `endless_runs.py` keeps the two failsafes an in-process mode
structurally cannot have (a fresh profile per run, and wall-clock + log-growth timeouts that
survive a wedged emulator process), so it remains the right tool for a scripted batch. *Make the
menu item block until the subprocess finishes.* Rejected: it would freeze the GUI and still not be
"this emulator".

**Prevention rule.** When a feature request names something the user is already looking at
("chained debug reset bots"), build it where they are looking. A functionally-equivalent thing
somewhere else reads as broken.

## 2026-07-25 — The TRAINING gate switches to `region_reach` too (KI-24 closed on both consumers)

**Decision.** `_training_area_allowed` — the `allow=` predicate `best_training_area` uses to decide
whether a training area is reachable — now answers the region question with
`region_reach.is_map_reachable(map_enum, max_hops=_MAX_TRAINING_TRAVEL_LEGS)` instead of tile-level
`calculate_path`. The counter gate already worked this way; the two are now consistent, and
`calculate_path` no longer answers any region-scale question in the story bot.

**Why — the failure modes are ASYMMETRIC, and that is the entire argument.** Both oracles are wrong
sometimes. What matters is what a wrong answer COSTS:
* A wrong **NO** from `calculate_path` is **invisible and costs a whole run.** It reads the Route
  118/119/120 dual-elevation bridges as WALLS — it fails even on a same-map Route 119 walk, y=5 to
  y=135 — so it declares a genuinely-correct training band unreachable. Nothing raises, nothing is
  logged; the option is simply never proposed and the bot quietly grinds the local fodder patch.
  That is what produced the ~2,000,000-frame L3-4 grind in front of Norman.
* A wrong **YES** from `region_reach` costs **one wasted walk**, which navigation then fails
  RECOVERABLY and loudly. Its `KNOWN_GATES` table holds one hand-verified entry (the two Dewford
  sea edges), so any capability gate not yet tabled reads as passable — it errs toward yes by
  construction.

Cheap-and-visible beats invisible-and-fatal. **Residual risk accepted and written into the code
comment: `KNOWN_GATES` must GROW**, and the hop budget stays small (4 keeps the same-landmass
cluster, cuts the far-flung).

**Measured effect** (`repro_counter_plan.py`, same live Winona-era position, same candidate list,
ONLY the predicate swapped):

| `_training_area_allowed` | reachable flags over the 10 Winona candidates |
|---|---|
| before (`calculate_path`) | `[False × 10]` — every candidate rejected |
| after (`region_reach`) | `[True × 5, False × 5]`, incl. **Route 118 Electrike: reachable** |

**Alternatives rejected.**
1. *Keep `calculate_path`.* Rejected on the measurement above: it returns all-unreachable from a
   position where the correct answer demonstrably exists, and its wrong answers are the silent kind.
2. *Require BOTH oracles to agree.* Superficially the "safe" option, and it is the trap. An AND of
   the two is exactly as restrictive as its most restrictive member, so it re-imports every
   `calculate_path` false negative — the ~2,000,000-frame grind included — while looking rigorous.
   Rigour that only ever subtracts candidates is not rigour.
3. *Keep a same-map `calculate_path` tile check as a "last mile".* Rejected for the same reason at
   smaller scale: `calculate_path` is unsound even WITHIN one map on the bridge maps. The same-map
   branch now short-circuits to True (we are already standing there; there is nothing to travel).

**‼ The most useful part of this story: implementing it exposed a bug in the test that had been
guarding the whole area.** The first attempt failed `repro_fodder_grass.py` case 5 and was
REVERTED rather than forced. Investigating the failure — instead of adjusting the expectation —
showed that `_stand_at()` patched only one of the two position readers, so case 5 had been
asserting a verdict for a position it never simulated (full write-up in 08-MISTAKES). That guard
had been the regression gate for every training-logic change of the preceding two days, including
the frames-based budget gate and the fodder-skip itself.

The order that produced this — *refuse to adjust the test → investigate why it disagrees → find the
test is wrong → fix the test → prove the fix alone is green → only then land the feature* — is the
process lesson worth keeping. Adjusting the expectation at step one would have shipped the right
feature and left a mock leak silently certifying future work.

**Verification.** `repro_fodder_grass.py` 5/5 green; `repro_region_reach`, `repro_counter_wiring`,
`repro_boss_plateau` green. `repro_counter_plan` is RED on a non-vacuity scaffold (line 200) that
was relying on the old predicate's false negatives to supply a `False`; left unadjusted pending a
ruling, documented in KI-24b.

## 2026-07-25 — Battle-handler faults reach the mode by an OPT-IN channel, not by an exception

**Context.** The battle handler cannot raise a recoverable error. `BattleListener` pushes `fight()`
onto `context.controller_stack`, and `main_loop` advances only the TOP of that stack — so the bot
mode's generator and the battle handler are SIBLINGS, not nested. Any `BotModeError` from battle
code lands in `main_loop`, which sets Manual. `StoryMode.run()`'s `except BotModeError` is
structurally unable to see it, no matter how it is written. Cost: 2 of 5 cold-start runs
(#24-movelearn-recovery).

**Decision.** Stop raising across that boundary. `modules/battle_fault.py` holds one pending fault;
the battle handler records it and returns; the mode claims it on the next frame it holds control
and re-raises inside its own recoverable scope. Participation is **opt-in via a class attribute**
(`handles_battle_faults = True`), and the attribute is a promise to call `take_pending_fault()`
every frame.

**Why opt-in rather than universal.** An unconsumed fault is worse than a Manual drop:
`handle_battle` short-circuits while one is pending, so a fault nobody claims would make every
future battle exit instantly. Gating on an explicit declaration means the failure mode of a mode
that forgets to participate is *today's behaviour*, not a new silent one. Proven both ways in
`repro_movelearn_fault_recovery.py`: the same fault, one frame apart, drops a stock mode to Manual
and is claimed by an opted-in mode.

**Alternatives rejected.**
- *Catch it in `main_loop` and re-dispatch to the mode.* Puts mode-specific recovery policy in the
  shared loop, and `main_loop` has no way to resume a generator it did not suspend.
- *Have `fight()` swallow the error and clear `_in_battle`.* Clearing `_in_battle` re-arms
  `handle_frame()`, which pushes a fresh `fight()` next frame — straight back into the same wedge.
  The listener now returns while deliberately LEAVING `_in_battle` set.
- *Let the mode poll for a wedged battle itself.* The mode is starved of frames precisely while the
  battle handler holds the stack, which is exactly when it would need to notice.

## 2026-07-26 — ENDLESS RESET restores SPEED but never touches VIDEO (user directive)

**Context.** `StoryEndlessResetMode` captured `context.video` at batch start and re-applied it
after every run, alongside `emulation_speed`. The speed half exists for a real reported problem
(a derail calls `set_manual_mode()`, which drops to 1x and throttled the rest of an unattended
batch). The video half was collateral.

**User directive, verbatim intent:** "I think that's due to the infinite run feature turning off the
video toggle upon reset — can we make it not mess with that and have it stay in whatever state it's
currently in."

**Decision.** Speed is restored; **video is never written**. The renderer belongs to the user; if
they turn it on mid-batch it stays on.

**Why it mattered more than a preference.** The FAITHFUL PokeNav Match-Call tutorial only advances
with the renderer ON, so pinning video off silently demoted it to the documented last-resort
state-write in **8 of 9** real-hardware runs (`#24-pokenav-faithful`). Worse, the `except` fell back
to `batch_video = False`, so one failed read of `context.video` would force the renderer off for a
whole batch. A setting captured "to be helpful" overrode a live user choice and degraded a
faithfulness guarantee — the general lesson: restore only what YOU changed, and never latch a
user-facing toggle for the duration of a batch.

## 2026-07-26 — Hard-won map/route facts live in the DECISION CODE, not in prose (user directive)

**Context.** The Lavaridge one-way-ledge constraint ("Jagged Pass not re-enterable; Route 112's
lower grass has no return path") was recorded 2026-07-23 in 03-PUNCH-LIST and 04-HANDOFF, and was
still re-derived from scratch by a ~30-minute probe cycle on 2026-07-26 — by a session that had
quoted half of it that same morning.

**User directive:** "make notes about training areas ... ensure all this gets noted."

**Decision.** Such facts go into the module that MAKES the decision, as data the code consults,
plus a test — not into a narrative document alone. Implemented as
`training_areas.NO_RETURN_GROUNDS` (evidence + date per entry), enforced in BOTH training pickers
*before* the reachability predicate, and pinned by `repro_no_return_grounds.py`. The punch-list
paragraph now points at the table as the authority rather than being the authority.

**Rejected:** "write it down more prominently in the handoff". It was already written down twice
and prominently; prominence was not the failure mode. The decision point was the wrong place to be
looking for it.

## 2026-07-26 — Validation runs are BATCHED across fixes, not run per fix (user directive)

**User directive:** "I will run some tests but only if you think it's worth running now. otherwise
lets continue working ... and when those fixes land I'll do the test then so we can test for more
than just a single bug."

**Decision.** Real-hardware validation runs accumulate several landed fixes and are run once, rather
than one run per fix. Corollaries: (1) intermittent bugs are proven by REPRO, not by a clean run —
a run that does not trigger them proves nothing; (2) when a fix can ONLY be validated on the user's
setup (anything needing the renderer, the GUI, or ENDLESS RESET — none of which the headless
livetest harness exercises), say so explicitly rather than implying a batch covered it; (3) a cheap
smoke check is still worth proposing when a fix is a PRECONDITION for the next run being
informative, so that run is not spent re-answering a known unknown.

## 2026-07-26 — ENDLESS LOOP ×4 runs as four CHILD PROCESSES, not four emulators in one process

**Decision.** An x4 batch is four `pokebot.py` processes, one emulator each, sharing nothing but a
`SharedMemory` framebuffer block. The dashboard is a supervisor that reads that block and paints a
2×2 grid.

**Why.** `modules/context.py:188` is a module-level `context = BotContext()` singleton with exactly
one `context.emulator`, and **116 files** import it. `modules/main.py` adds two more non-emulator-scoped
mutable globals (`work_queue:19`, `inputs_each_frame:24`), and `modules/state_cache.py:301` is another
singleton. Four emulators in one process means threading a context object through the whole codebase —
a fork-wide refactor that would also make every future `git subtree pull` from upstream painful.

**Rejected alternatives.**
- *Four cores in one process.* The refactor above. Cost is enormous, and it is paid again on every
  upstream merge, forever.
- *Four separate OS windows arranged by the GUI.* Cheap, but fails the actual request ("within the
  emulator window space") and cannot work in handheld mode.
- *Headless-only batch, no tiles (i.e. extend `tools/story-dev/livetest.py`).* This is the FASTEST way
  to generate logs and was my first recommendation — withdrawn on evidence. The original endless-runs
  feature already shelled out to a headless `tools/story-dev/endless_runs.py` and was abandoned because
  "the dialogs appeared and nothing appeared to happen". A headless batch gives the user nothing to
  watch, and that is precisely what made the first attempt unusable. The visual channel is the feature.

**Consequence, stated plainly.** A lane must run with `context.video = True` (an unrendered screen
publishes as blank, and `get_screenshot()`'s save-state-and-step workaround is far too expensive on
the hot path). So an x4 batch is the WATCHABLE mode, not the fastest one — a headless `livetest.py`
lane still produces more frames per second. Both exist on purpose.

## 2026-07-26 — Lane profiles are BOT-MANAGED: `story.yml` is rewritten on every batch launch

**Decision.** `ensure_lane_profile()` overwrites each lane's `story.yml` every time a batch starts,
rather than creating it once and leaving it alone.

**Why.** The batch's entire value is "P2 is always the Mudkip lane". A stale hand-edit silently
turning P2 into a second Torchic would corrupt the starter coverage the feature exists to provide,
and **nothing would report it** — the logs would still say P2, and the bug would be invisible in
every summary. Predictable clobbering of a bot-managed file beats silent, undetectable drift. The
file says so in its own header, and the lane table lives in `modules/endless_x4.py`.

**Rejected.** Write-once-if-absent (the pattern `modules/story/config.py` uses for real user
profiles). Correct there, wrong here: these profiles are disposable test rigs, not saves.

## 2026-07-26 — Separate profiles per lane, not one shared profile with tagged logs

**Decision.** Four profiles (`endless-P1-torchic` …), not one profile with `P1`-prefixed log names,
which is what the user first proposed.

**Why.** Two bot processes sharing a profile directory clash on `current_save.sav`,
`current_state.ss1` and the stats DB — `tools/story-dev/livetest.py` already carries this scar
("two harness processes must never share a profile directory"). Separate profiles ALSO deliver
the organisational benefit that motivated the original request for free, because debug logs are
already written per profile; the `P1-`/`P2-` filename prefix (new `debug_logger.enable(name_prefix=)`)
is kept on top so a folder of collected logs is self-identifying.

## 2026-07-26 — A lane's party travels as JSON and is rebuilt as stand-ins, rather than forking the party renderer

**Decision.** `modules/remote_party.py` rebuilds objects that expose the exact attribute
surface the dashboard's party UI reads, from JSON the lane publishes. `_refresh_party()`
swaps its SOURCE when a batch is running; every line of rendering below that is unchanged.

**Why.** The alternative — a second "remote party" renderer — would have to be kept in step
with the real one forever, and the party UI is not small (strip icons with ball compositing,
tab rows with HP/XP bars, a themed hover tooltip with types, IVs and moves). One renderer
with two data sources is strictly less to maintain than two renderers.

**The contract, and why it is written down.** The attribute list was measured off the code
(strip 1145-1240, tab row 3209-3290, tooltip 1530-1700), not guessed. It is recorded in
`remote_party.py`'s docstring because a missing attribute DEGRADES QUIETLY — the tooltip
wraps its reads in `safe()` — so drift would show up as blanks nobody attributes to this.

**One trap worth remembering:** `status_condition` must be the real `StatusCondition` enum
member. `dashboard_gui:3239` compares it with `is not StatusCondition.Healthy` — an IDENTITY
test that any string or look-alike fails, which would render every healthy Pokémon as
though it were statused. Covered by a test that asserts identity, not equality.

## 2026-07-26 — The badge recorder ships BEFORE the trainer-card UI that motivated it

**Decision.** `modules/badge_log.py` (capture) is built and running now; the badge-case
overlay the user asked for is deferred.

**Why.** The two halves have opposite time profiles. The overlay can be built at any point
and loses nothing by waiting. The capture can only ever record badges earned AFTER it is
switched on — nothing in a save reconstructs what the party looked like at the instant a
flag flipped. Every ENDLESS LOOP x4 run between now and the UI would have produced badge
wins that are gone for good. Shipping the recorder first turns waiting into data collection.

**Rejected.** Building both together (delays capture for no benefit), and deriving the team
retroactively from save states (the endless mode hard-resets between runs, so the states
are gone; and a mid-run party is not the party at the moment of victory).

## 2026-07-26 — Log collection is park → copy → VERIFY → archive, and never reorders

**Decision.** `modules/x4_logs.collect()` will not move a single original until it has
reopened the finished zip and proved every file is in it. On any verification failure it
leaves the originals exactly where they are and reports the reason.

**Why.** The archive step exists for convenience — a clean slate for the next batch. The
originals are the only copy of data that took hours of emulation to produce. Convenience
must never be able to destroy the irreplaceable thing, so the destructive step is gated on
positive proof rather than on "the write didn't raise".

**Why parking is part of it, not a nicety.** Lanes are separate processes. A log open for
append can be copied mid-line, and on Windows cannot be moved at all. So the collector
first posts `CMD_PARK` and WAITS for each lane to acknowledge `parked: true`. A lane that
has already died counts as parked — its file is closed by definition.

**Consequence accepted:** `park_all()` blocks the window briefly. The dashboard has no Tk
mainloop (the event queue is pumped from the emulator frame callback), so pumping Tk inside
that wait would re-enter the frame callback. A bounded, honest freeze on an explicit user
action beats a re-entrancy bug.

## 2026-07-26 — The parent→child command channel is a SEPARATE shared-memory region

**Decision.** `tile_bridge` slots are `[header][status][command][frame]`, where the child
writes header/status/frame and the parent writes ONLY command. Commands are not header
fields.

**Why.** The child rewrites its entire header on every publish (20×/s). A command stored
there would be erased almost immediately, intermittently, and only under load — the worst
class of bug to diagnose across a process boundary. With disjoint regions the existing
lock-free scheme (write pixels → status → header, re-check `sequence` on read) holds in
both directions with no locking anywhere. A lane acts on a CHANGE of command sequence, so a
re-sent command is idempotent. Covered by a test that publishes a frame over a pending
command and asserts the command survives.

## 2026-07-26 — Cold-start runs decorrelate via a random pause on the NAMING SCREEN

**Decision.** `modules/story/intro.py` idles a random 0-120 frames after typing the player
name and before confirming it. `POKEBOT_RNG_DECORRELATION_FRAMES` overrides it; `0` restores
fully deterministic cold starts.

**Why there specifically.** Verified in the pokeemerald decomp: the only single-player
reseed is `SeedRng(REG_TM1CNT_L)` (`src/main.c:208-214`), reading a cycle-exact timer that
starts when the naming screen OPENS (`src/naming_screen.c:412`) and is read when the name is
CONFIRMED (`:701`). `SeedRng` OVERWRITES the state, so a delay anywhere earlier in the intro
is discarded — this is not one option among many, it is the only externally reachable input
to the seed on a new game.

**Why random per RUN, not a fixed per-lane offset.** A fixed offset would decorrelate the
four lanes from each other while leaving every run of a given lane identical to the last —
`gRngValue` is not saved, so the hard reset between endless runs puts each lane back on the
same rails. Per-run randomness fixes both axes at once.

**Why 0-120.** One idle frame shifts the seed by 280,896 mod 65,536 = 18,752, and
`gcd(18752, 65536) = 64`, so reachable seeds repeat every 1,024 frames. 0-120 stays well
inside one cycle (121 distinct seeds), and costs at most two seconds per run. A larger range
buys more seeds at a wall-clock cost that is not worth it at four lanes.

**Rejected.** (a) Relying on the RTC — Emerald's RTC seeding is compiled out
(`//#define BUGFIX`), unlike Ruby's. (b) Relying on lane names differing (P1..P4 type
different characters, which does perturb the timer) — real but accidental, unmeasured, and
it would break silently the moment someone made the names uniform. (c) Idle frames after
boot — discarded by the `SeedRng` at naming. (d) Leaving it deterministic and treating
lanes as replicates — that is just admitting the feature does not do what it claims.

**Accepted cost.** Cold-start runs are no longer bit-reproducible by default. This is the
right default for a sampler, and the env var restores determinism for bug reproduction; no
existing `repro_*.py` is affected, as they all load save states rather than running the intro.

## 2026-07-26 — Per-run state gets an explicit reset method, not a fresh object

**Decision.** Keep the endless loop reusing ONE mode instance, and give `StoryMode` an
explicit `reset_per_run_state()` that the loop calls at every run boundary.

**Rejected: construct a fresh `StoryMode` per run.** It is the more obviously-correct
lifetime, but the endless mode IS the mode object the bot framework holds — it is registered,
its `run()` is the generator being driven, and `on_battle_ended` / `on_whiteout` are dispatched
to it. Swapping the instance mid-batch would mean re-registering listeners and re-entering the
framework's mode machinery on every run, which is a far larger blast radius than the bug.

**Rejected: move the counters to module globals cleared by the loop.** Same clearing problem,
plus it would break the x4 batch, where four lanes share a process only by accident of
imports today but must never share counters.

**Why explicit-and-named beats implicit.** The failure was not that the state was in the wrong
place — it was that `__init__` was silently assumed to be the run boundary, and a comment said
so where no code enforced it. A method whose name IS the lifetime ("per run") makes the next
counter's correct home unambiguous, and gives the repro something to assert against.

## 2026-07-26 — `run_index` dedupe by ownership, not by adjacency

**Decision.** `reset_for_new_run(..., authoritative=True)` lets a mode that knows its own run
boundaries permanently disable `modules/main.py`'s frame-counter heuristic for that process.

**Rejected: adjacency ("no poll since the last reset").** This was the PREVIOUS fix and it
could never fire — the mode signals before `super().run()` and the hard reset happens inside
it, so thousands of polls always separate the two calls. Retained only for the
non-authoritative path, where two detections with nothing played between them genuinely are
one boundary (`repro_badge_transient.py` encodes that contract).

**Rejected: dedupe on frame distance.** Actively wrong — `get_frame_count()` resets with the
emulator, so every run starts near 0 and an entire batch would collapse into one run.

**Rejected: dedupe on wall clock.** Works in production, untestable without sleeping.

**Principle.** When two components both detect the same event, the one with real knowledge
should claim ownership and silence the heuristic — rather than both guessing and a filter
trying to spot the duplicate after the fact.

## 2026-07-26 — Lead policy and the Route 110 rival cap are NOT fixed autonomously

**Decision.** Log `#24-leadpolicy` and `#24-route110cap` with full evidence and leave them for
a user ruling.

**Why.** Both are genuine design tradeoffs, not defects with a correct answer:
- The matchup lead benching a stronger mon is sometimes exactly right (Marshtomp is 4× weak
  to the rival's Grovyle; leading it really would feed a sweep). "Also require an attacking
  option" is a policy change to how the bot plays, and the project's standing rule is that
  research/agents enumerate what to check and never decide what the bot should DO.
- A cap on the Route 110 rival looks obviously right until you check the data: P2 lost there
  **13 times and then went on to reach Fortree**. A cap at 6 would have killed a run that
  recovered. Adding prep instead needs a Route 110 training-grass tile — a game fact that must
  be probed or read from the decomp, never recalled from memory (see the standing directive).

## 2026-07-27 — The per-run frame budget is enforced by stepping the generator, not by a timer

**Decision.** `StoryEndlessResetMode` drives the story generator itself
(`_run_with_frame_budget`) and checks elapsed frames every 2048 yields, raising
`BotModeError` into the existing derail path.

**Rejected: keep the post-hoc check and rely on the global watchdog.** The bundle disproves
it — P3 hung for 27M frames with ZERO STUCK dumps, i.e. the watchdog was itself what wedged,
which is the exact scenario the frame cap was written for and could not cover.

**Rejected: a wall-clock timer on a background thread.** Frames are the right unit (the batch
runs unthrottled and speed varies), and a thread cannot safely interrupt a generator mid-yield
in this framework.

**Rejected: making the STUCK/no-progress detector stricter.** It cannot work for P1/P2, which
are LIVELOCKS — real encounters, real battles, real healing trips, no story progress. A
progress detector is blind to a loop that is genuinely busy, by construction.

**Why stepping is safe.** `modules/main.py` advances bot modes with a bare
`next(context.controller_stack[-1])` and discards the yielded value, so there are no `send()`
values to lose and yielding `None` is equivalent. `close()` is forwarded in a `finally`.

**The detail that would have silently disabled it.** The hard reset happens INSIDE the run and
`get_frame_count()` restarts with the emulator, so the counter legitimately goes backwards.
Measuring `now - start_frame` yields a negative number, nothing is ever over budget, and the
bound is inert — the same trap that had already produced `finished (-959,198 frames)` in an
earlier bundle. The budget re-bases to 0 when it sees the counter go backwards, and the repro
covers that case explicitly.

## 2026-07-27 — Documentation audits use read-only agents; only the main thread writes

**Decision.** When fanning out subagents to check documentation, they get READ-ONLY roles and
must report `file:line` evidence with an explicit `VERIFIED / WRONG / UNVERIFIABLE` verdict.
The main thread makes every edit, and independently re-checks any load-bearing claim first.

**Why.** The user's constraint was "cross reference so we don't get poison in the
documentation". An agent that can write can introduce a confident falsehood into the
project's source of truth, and nothing downstream would catch it. An agent that can only read
can at worst waste a verification.

**It paid for itself immediately.** Of four agents, two produced claims that were wrong on
re-check: one asserted `CLAUDE.md` has "zero occurrences of sandbox" (it has a whole
§"Sandbox area" directive at line 185) and that `02-ARCHITECTURE.md` had zero (it had two).
Both were `grep`-count claims. Their FILE-EXISTENCE and line-reference findings, by contrast,
were reliable across the board. **Calibration to reuse: trust an agent's "does X exist at
line N" and distrust its "X appears zero/N times" without re-running the grep.**

**Rejected: let agents edit their assigned docs directly.** Faster, and it is how the volume
would normally get done — but the failure mode is silent and lands in the one place the
project treats as truth. Not worth it.

**Rejected: skip verification and just rewrite the stale docs from the code.** That is how
the wrong facts got in: someone confident, writing prose. Every corrected number in this pass
came with a re-run command.

## 2026-07-27 — Fixed-in-sandbox issues stay in 05-KNOWN-ISSUES until promotion (PROVISIONAL)

**Decision (provisional, needs the user's ruling).** Entries fixed in `sandbox-pokebot/` but
not yet promoted to `custom-pokebot/` are RETAINED in `05-KNOWN-ISSUES.md`, marked
`✅ FIXED` with the fixing `file:line`, rather than deleted.

**The conflict.** `05`'s own header says "Open problems only — when an issue is fixed, remove
it here". But an issue fixed only in sandbox is *still open for the production copy*, and
deleting it loses the only signal that a promotion is owed.

**Why provisional.** This is a documentation-policy call that belongs to the user, not a fact
code can settle. Flagged at the top of `05` as an open question. Until it is answered,
retaining-and-marking is the safer default: a reader can see both the fix and the outstanding
promotion, whereas deletion is irreversible information loss.

**What is NOT provisional:** entries whose bodies actively instruct future sessions to do
already-completed work are dangerous regardless of the policy, and are now marked as such at
the top of the file — KI-18 in particular said "Do NOT patch on the hypothesis. Reproduce
first" for a shipped, repro-proven fix.

## 2026-07-29 — USER RULINGS on the six open questions

All six answered by the user. Recorded verbatim in intent so no future session re-asks.

**1. Norman counter — `#24-counters` phase 2 → OPTIONS A + C.** Price both approaches with the
frame-cost model, then **catch-and-train a Fighting type**. Not "buy potions and out-level".

**‼ The user added scope here, and it is the important part.** Their observation: the bot trains
in whatever grass is next to the objective — often *severely* below level 5 — so XP per battle is
near worthless. Norman is the 5th gym but sits in the STARTING region, so "train near the gym"
is actively wrong there. Their directive:
  * **Map areas → species → types → level ranges**, and use that map for BOTH "where do I catch a
    Fighting type for Norman" AND "where should I train right now".
  * **Raise the party cap above 4** (up to 6) and **allow catching on a full party**, with the
    catch going to the **PC**, so the bot can bank Pokémon and **rotate them in to train and to
    fight specific gyms/bosses**. Explicitly framed as *intelligent PC/party management* and
    flagged by the user as needing further discussion.

**2. `#24-leadpolicy` → OPTIONS A + C.** The lead must also have a ≥neutral attacking option
(A), and 1-HP Wonder Guard mons get a special case (C). Level-gap weighting (B) NOT adopted.

**3. `#24-route110cap` → OPTION A.** Add `_prepare_for_fight` (proactive band training +
loss escalation). **No attempt cap** — the evidence that a 13-loss run went on to reach Fortree
stands, so the run is not to be truncated.

**4. KI-24b → OPTION A.** Patch the `_stand_at()` mock to cover `get_player_location` too and
re-baseline the acceptance test; show the diff before it lands.

**5. `#doc-policy-05` → OPTION A.** Keep-and-mark sandbox-fixed entries in
`05-KNOWN-ISSUES.md` until they are promoted to `custom-pokebot/`. The provisional behaviour
is now the ruling; the "OPEN QUESTION" banner in `05` is resolved.

**6. Repo size → LEAVE IT.** No `filter-repo`, no force-push. The ~61 MB stays.

### ‼ What the audit found BEFORE building anything for ruling 1
Per the standing rule ("the fact is usually already known and in the wrong place"), the data
layer the user asked for **largely already exists**:
  * `modules/encounter_index.py` — whole-game REVERSE wild-encounter index, built from the ROM's
    `gWildMonHeaders`: species → [{map, map_name, method, rate%, level range}], cached per ROM.
    Built for the Hunt Planner (#9). This IS the species/level/location map.
  * `modules/story/training_areas.py` — `TRAINING_GRASS` (verified spin tiles + wild level bands),
    `best_training_grass(mon_level)`, `best_training_area(team_level, min_wild_max=…)`,
    `AREA_PREREQ`, `NO_RETURN_GROUNDS`, `estimate_frames_to_level`, `FRAMES_PER_WILD_BATTLE=1433`.
  * `modules/story/counter_plan.py` — already turns "I need Ground" into ranked, reachable,
    cost-priced concrete encounters.

**The gap is WIRING and POLICY, not data:**
  1. `train_team(target, scope, grass=RUSTBORO_TRAINING_GRASS, …)` (`early_game.py:1738`) takes
     the grass as a **caller-supplied constant** and never consults `best_training_area`. Its own
     module docstring says so: *"NOT yet wired into train_team … punch-list #24-trainmap."*
  2. `_prepare_for_fight` DOES relocate (`story_mode.py:1423`) — but only when
     `local_max + FODDER_LEVEL_GAP < team_max_now`, and `FODDER_LEVEL_GAP = 12`
     (`story_mode.py:715`). So a L15 team on L3-5 grass (5+12=17 > 15) **stays put and grinds
     fodder**. That threshold is the direct cause of the user's observation.
  3. `self._catch_team_target = 4` (`story_mode.py:845`), enforced in `_should_catch`
     (`:960`) — the 4-mon cap.

## 2026-07-29 — Debug Story modes force unthrottled + video ON; this SUPERSEDES the 2026-07-26 "never touch video" rule

**Decision (user directive).** `Story (DEBUG)`, `Story (DEBUG - RESET)` and
`Story (ENDLESS RESET)` now set `emulation_speed = 0` and `video = True` themselves, matching
what an x4 lane gets for free (`endless_x4.py:160`, `gui/tile_child.py:84`). Plain `Story` is
NOT touched — a human watching a normal run keeps control.

**Why.** The user cannot run x4 on their work machine (not enough power for four emulators),
but x4's config is far better for test runs and a hand-launched bot inherited whatever the GUI
had. Run `20260729-122709` logged `emulation: speed=1 video=True` — throttled — so 2.78M
frames took hours.

**‼ THIS SUPERSEDES the 2026-07-26 directive "SPEED ONLY — NEVER TOUCH `context.video`", and
the distinction is the whole point.** That rule was written because the endless loop used to
CAPTURE video at batch start and RE-PIN it on every run, so a batch begun with video off kept
it off for ever and silently degraded the faithful PokéNav path to a state-write in 8 of 9
runs. **The harm was pinning to an ARBITRARY value, not writing the field.** Forcing it ON,
once, is the opposite: `video = True` is the value the faithful path REQUIRES, and it is
already what x4 does. Evidence: `20260729-122709` ran with video on and played the Match-Call
tutorial faithfully with no fallback.

**Rejected: tell the user to set it in the GUI each time.** It is a launch-time setting they
would have to remember on every run, on a machine they use for work; and the ordering is
subtle — `ENDLESS RESET` captures `batch_speed` at batch start and restores it after every
`set_manual_mode()`, so setting the speed *after* starting the mode pins the batch to the old
value. Making the mode own it removes a foot-gun rather than documenting one.

**Rejected: a new CLI flag.** The lesson from `POKEBOT_FODDER_RULE` (2026-07-29) applies —
anything the operator must supply on a remote machine every time will eventually be forgotten
or reverted by the installer. A default that is right, plus an escape hatch, is better.

**Escape hatch:** `POKEBOT_STORY_DEBUG_TURBO=0` leaves both settings exactly as configured.
The applied values appear in every debug log's RUN HEADER (`emulation: speed=… video=…`), so
what actually happened is never in doubt.

**Ordering constraint, encoded in a test:** `ENDLESS RESET` must apply this BEFORE it captures
`batch_speed`, or every run after the first is restored to the OLD speed — the 2026-07-25
"second run crawled at 1x" bug, reintroduced from the other direction.
`repro_debug_emulation_config.py` asserts the order.

---

## 2026-07-30 — Counter hunting grounds are a WHITELIST, and huntability is separate from reachability

**Decision.** `#24-counters` phase 2 may only send the bot to a map listed in
`TRAINING_GRASS` (two-way swept) or the new `training_areas.HUNTING_GROUNDS`
(reach-and-leave proven). Every candidate carries `huntable`, and executors must select
with `counter_plan.best_huntable()` — never `cands[0]`.

**Why a whitelist and not a blacklist of endgame maps.** The blacklist version is an
ever-growing list of assertions about which Hoenn interiors are story-locked — i.e. exactly
the *game facts written from memory* the standing directive forbids, and a list that is wrong
the moment it is incomplete. The whitelist requires no claim about Mirage Tower or the Magma
Hideout at all: they are refused because nobody has swept them, which is a fact about OUR
evidence, not about the game. It also fails CLOSED, the correct direction for a predicate that
decides where the bot physically walks (KI-24's lesson, in the safe direction).

**Rejected: rank by cost and trust the ranking.** The cost model prices "train it up to the
team's level" at ~0 for a wild already above the team, so it ranks deep-endgame encounters as
CHEAPEST. Measured: rank 1 for Norman is a Victory Road Hariyama L38-42. **Ranking answers
"which is cheapest", never "may I go there".**

**Rejected: let `region_reach` be the gate.** It cannot be. Run live from the Winona-era save,
`_counter_area_allowed` calls the Magma Hideout, Shoal Cave and the Safari Zone **reachable**
(10/10 candidates reachable) — which is arguably TRUE as connectivity and useless as
permission. `KNOWN_GATES` holds two hand-verified entries; anything not derivable from ROM
connection data reads as ungated, and the module is documented as failing OPEN on purpose.

**Rejected: reuse `NO_RETURN_GROUNDS` as the hunt test.** It encodes a *training-loop*
requirement (must walk back to a Poké Center to heal). A hunt is walk-in/catch/walk-out and
needs no heal leg, so that table refuses grounds a hunt may legitimately use — Fiery Path is
precisely such a ground, and `NO_RETURN_GROUNDS`' own entry says so in prose. Hence a separate
table for a separate requirement rather than weakening the existing one, which would have
quietly re-admitted Fiery Path to `train_team` and reintroduced the stranding bug it exists
to prevent.

**Consequence accepted.** Real answers get refused for lack of a sweep, not for being wrong —
Wattson's Jagged Pass Numel, Norman's Granite Cave Makuhita. The unblock is field work
(promote a swept tile), and the refusal is loud, so the cost is visible rather than silent.

---

## 2026-07-30 — The counter hunt is bounded by PER-RUN STATE, not by retries or frames

**Decision.** `#24-counters` phase 2 attempts **one hunt per boss per run**, recorded in
`StoryMode._counter_hunts` and cleared by `reset_per_run_state()`. The attempt is written
down BEFORE the hunt runs.

**Why not a retry budget ("try 3 times")?** The chain fires from inside
`_prepare_for_fight`, which the run loop re-enters after every lost boss attempt. A counter
scoped to the call becomes 3 tries *per attempt*, which is unbounded. **This is precisely
the KI-34 shape** — "a bounded loop re-entered by its dispatcher is still infinite" — which
burned 23.9M frames. A frame budget fails identically, and for the same reason.

**Why record the attempt BEFORE hunting?** A hunt can derail mid-flight (whiteout,
navigation failure). The run recovers and re-enters `_prepare_for_fight`; without the
early write, the bound would never be persisted and the hunt would restart for ever. This
costs one thing — a hunt interrupted by an unrelated whiteout does not get a second try
this run — and that is the right trade: the next run gets a fresh chance, and the failure
mode of the alternative is an infinite loop.

**Rejected: let the hunt run until it succeeds.** The tempting version, since the run ends
anyway if it fails. But "the run ends anyway" is exactly the assumption that makes an
unbounded loop look free, and the honest stop has real value: it names the missing counter
in the derail log, which is how the derail classes were measured in the first place.

**Rejected: skip rung 3 (training) for now and ship the catch.** Shipping the catch alone
would have been a REGRESSION, not a partial win: with a Fighting type in the party,
`_boss_plan_is_hopeless` stops firing, so the diagnosis that currently ends the run cleanly
would go quiet and the bot would re-attempt Norman with an untrained L15 Machop until the
5M-frame run budget killed it. A half-built ladder is worse than none here.

**Rejected: rely on `_prepare_for_fight`'s normal training to level the catch.** It readies
"the strongest battler plus any battler already within `TRAIN_CATCHUP_GAP` levels" — a fresh
catch is outside that gap BY DESIGN (`#24-team`: fresh catches level organically). So the
counter needed an explicit, separately-budgeted training step.

---

## 2026-07-30 — Menu entries keep a FIXED position; a disabled entry beats a missing one

**Decision.** In the dashboard's Bot-mode popup, the Story block and the ×4 batch controls
occupy the same slots regardless of game state or whether a batch is running. Entries that
cannot be used right now are shown **greyed out in place**, never hidden and never moved to
a different section.

**Why.** The user's complaint was findability — *"I have to scroll around to activate them
and end/park them"* — and the fix for that is not merely "put them higher", it is "put them
somewhere that does not change". Two behaviours were making the layout move:
* a Story mode that failed `is_selectable()` dropped from its normal position into the
  disabled block at the bottom of the menu;
* `Park ×4 & Collect Logs` was hidden entirely unless a batch was running, so the block's
  height changed and every entry below it shifted.

**Rejected: keep hiding `Park ×4` when no batch is running** (the 2026-07-26 choice, whose
stated reason was that it "is only meaningful during a batch"). That reasoning is sound for
tidiness and wrong for muscle memory: a menu the user reaches for mid-batch must be in the
same place as when they last looked at it. A greyed entry also *teaches* that the feature
exists and when it applies, which a hidden one cannot.

**Rejected: a hand-written list of Story mode names to hoist.** Story modes are matched by
the `STORY_MODE_PREFIX` instead, so a new `Story (…)` variant is hoisted the day it is
added. Hand-listed collections rotted twice in this project on this same day
(`08-MISTAKES` 2026-07-30 — stub constants, and the "environmental" repro list).

**Consequence accepted.** The menu is slightly longer, and shows a few entries that cannot
be clicked. That is the price of a stable layout, and it is the cheaper error: a missing
entry reads as a missing feature.

---

## 2026-07-31 — The headless batch runner ASSERTS the emulation config; it does not set it

**Decision.** `tools/story-dev/x4_headless.py` does not force `speed=0` / `video=True` itself.
It passes `-s 0 -hl` (never `-nv`) and then **verifies the result** by reading every run's
debug-log RUN HEADER, aborting the batch loudly if any header is not `speed=0 video=True`.

**Why.** Three mechanisms already produce the right config (`PokebotHeadless.run()` from the
CLI flags, and `_apply_debug_emulation_config()` which forces both and re-pins the speed after
every `set_manual_mode()`). A fourth, in the runner, would be a *second source of truth* that
can drift from the bot's — and would MASK the exact regression worth catching: if
`_apply_debug_emulation_config` ever stops re-pinning, a runner that pins it too would hide
that from every future batch. Verification catches the regression; duplication conceals it.

**Why every header, not just the first.** The historical bug (2026-07-25) was *"run 1 ran
unthrottled and every run after it crawled at 1x"* — a derail calls `set_manual_mode()`, which
drops the speed to 1. Checking once at start would have passed on the broken build.

**Rejected: warn and continue.** Default is ABORT. A lane at 1x is ~20x slower and looks
exactly like a hang from the outside, so one mis-configured lane does not just lose its own
sample — it manufactures fake hang evidence in the batch it was meant to measure.
`--on-bad-header warn` exists for the case where a user knowingly wants the degraded run.

**Rejected: reusing the GUI's `endless-P{n}-…` lane profiles.** The user may be running their
own x4 batch on the same box; two bot processes sharing a profile directory clash on
`current_save.sav` / `current_state.ss1` / `stats.db`. Headless lanes use `endless-H{n}-…`.

## 2026-07-31 — Headless lanes keep the RENDERER on (`-hl`, never `-nv`)

**Decision.** Headless batches pass `-hl` and never `-nv`.

**Why.** `-hl` selects `PokebotHeadless`, which removes the GUI **window**; the renderer is a
separate thing and `PokebotHeadless.run()` sets `context.video = not no_video`. The faithful
PokéNav Match-Call path only advances with the renderer ON — with video off it degraded to its
state-write fallback in **8 of 9** of the user's real-hardware runs. Keeping video on is also
what makes a headless batch comparable to the user's GUI x4 batches, which have it on.

**Cost accepted.** Rendering is not free, but measured throughput is ~1,211 fps/lane — the
same as the documented ~1,250 — so the cost is inside the noise at these speeds.

---

## 2026-07-31 — Warp planning becomes MAP-granular, but the walk decision stays with `calculate_path`

**Decision.** `WarpGraph` gains a map-level BFS (`warp_candidates`), but `navigate_to_anywhere`
does not trust it. It asks `calculate_path` "can I walk there?" first, and validates each
candidate warp's first leg with `calculate_path` before committing to it.

**Why not trust the graph.** The graph is built from ROM map headers, and those headers lie in
a way that matters: VERDANTURF declares a North connection to ROUTE116 that **cannot be
walked**. Any planner that believes the headers will confidently produce routes that do not
exist — and a wrong YES sends the bot on a long walk to nowhere, which this project has
already paid for twice (KI-24b; the refuted gateway waypoints). `calculate_path` is the only
oracle that sees collision, elevation, dynamic obstacles and capability gates, so it gets the
final say. The graph's job is to SUGGEST; the pathfinder's job is to RULE.

**Rejected: replace `plan()` outright.** The region planner still runs first for cross-region
trips and its choice is still tried unvalidated as a last resort, so no journey that works
today can start failing. Strictly additive beats strictly better when the function is called
from around 40 places across the story.

**Rejected: build the full leg-list journey planner KI-39 sketched** (BFS to ordered legs to
execute with re-planning). The executor already re-plans from the real position after every
warp, so a full leg list would be re-derived and thrown away each iteration. One warp at a
time, validated, is less code and self-corrects when the world disagrees with the graph.

> ‼ **CORRECTION, same day (2026-07-31 PM).** That rejection was wrong, and the reasoning
> above shows exactly how: *"the executor already re-plans after every warp"* is only true
> **once the first warp is reachable**. Measured from `norman_done.ss1` (PETALBURG_CITY,
> which is where the Norman counter ladder actually fires — not Mauville, where I had been
> testing): `warp_candidates(PETALBURG -> FIERY_PATH)` returns only the two ROUTE112 doors,
> because the ROM headers describe ROUTE104 as one connected map. It is not —
> **PETALBURG_WOODS is a separate map entered by a warp and splits Route 104 in two** — so
> both candidates sit behind a split we have not crossed, neither validates, and the
> executor has nothing to do. From Petalburg: ROUTE104 31/200 tiles reachable,
> **PETALBURG_WOODS 0/132, RUSTBORO_CITY 0/150, ROUTE116 0/125.**
>
> The fix is `_staged_progress_warp`: when nothing on a route to the goal is reachable, take
> any reachable warp that does not INCREASE the distance to the target, and re-plan. It is
> still not a precomputed leg list — the objection to that stands — but it is the "make
> partial progress and re-plan" half of KI-39's shape, which I dismissed along with it.
>
> **What I should have done:** tested from the position where the feature actually fires.
> Every measurement behind the original decision was taken from Mauville, one hop from the
> obstacle, which is the easy case. See `08-MISTAKES` 2026-07-31.


**Consequence accepted.** One extra `calculate_path` per `navigate_to_anywhere` call on the
happy path. It is the same call `navigate_to` makes microseconds later, so the cost is one
extra plan per navigation, not per frame.

## 2026-07-31 — The candidate progress filter rejects only moves AWAY, never "not strictly closer"

**Decision.** A warp candidate is discarded only if it *increases* the map-graph distance to
the target. Equal distance is accepted.

**Why.** The obvious criterion — "must be strictly closer" — is wrong for the exact case the
feature exists for. The phantom Verdanturf-to-Route116 connection puts the target **1 hop**
away, so no candidate can beat it and the Rusturf Tunnel (also 1) would be filtered out; the
fix would silently do nothing. The graph distance is untrustworthy *because* of phantom
connections, so it is used only as a coarse junk filter, and `repro_journey_planner.py` pins
the non-increasing rule so that "tightening" it is a loud failure rather than a silent revert.

**What the filter is actually for.** Banning the previous answer to get a diverse candidate
list produces junk: Verdanturf-to-Route116 offered the BATTLE TENT LOBBY and the MART as
candidates 5 and 6 — genuine routes (walk in, walk out, then take the tunnel) that go nowhere.

---

## 2026-07-31 — USER RULING: `#24-dexhunt` is "always catch new, WHEN IT IS CHEAP"

**The question.** `#24-dexhunt` wanted ALWAYS-catch-new; `21-TEAM-POLICY-DESIGN.md` §1 wanted
a SCORED RANDOM ROLL. The user said "catch all new pokemon" in discussion on 2026-07-30 but
had never been asked to confirm it as a ruling, so it sat as the one outstanding decision.

**The ruling (user, 2026-07-31).** Catch every unseen species **except when doing so would
block progress**. Dex-complete intent, with a resource guard, so a dex hunt can never become
the thing that ends a run. The two alternatives were put explicitly and both rejected:
* *unconditional always-catch* — rejected: it makes `#24-pc` (box trips) and the party-cap
  work load-bearing rather than optional, and turns a nice-to-have into a new run-killer;
* *the scored random roll in `21-TEAM-POLICY-DESIGN.md` §1* — rejected: slow dex, and it adds
  run-to-run variance to **every batch measurement**, which is expensive in a project whose
  main instrument is batch comparison.

‼ **This SUPERSEDES `21-TEAM-POLICY-DESIGN.md` §1 for new-species catching.** Update that
section rather than leaving two documents disagreeing — a contradiction between design docs is
how the same question gets re-litigated a third time.

**"Cheap" is defined, not left to judgement.** The user flagged that the word needed pinning
down, and the codebase already has the right predicate: `counter_hunt.resource_blocker()`.
Reuse it rather than writing a second one that can drift:
1. **Spare balls** — `_ball_count() > 1`. The LAST ball stays reserved; that is the same rule
   the HM hunt uses, and `21-TEAM-POLICY-DESIGN.md` §6 already lists relaxing it as a
   never-randomise item (it reintroduces the catch-without-balls bug).
2. **Party space, or a PC within reach** — `_party_count() < 6`. Until `#24-pc` exists, a full
   party means the catch would go to a box the bot cannot manage, so it must skip.
3. **Not mid boss-prep** — a dex catch must never interleave with a boss attempt-cap sequence
   or a level-floor grind. Those already have their own state; the dex check goes AFTER them.

**And it must SAY when it skips.** A skipped catch has to log the specific reason, for exactly
the KI-24/KI-42 reason: a silent "no" is indistinguishable from "the feature is not running",
and this project has now lost time to that shape three times. `resource_blocker()` already
returns a reason string rather than a bool — keep that.

**Gating.** Both navigational blockers (`#24-journey`, `#24-smashroute`) are cleared, so the
travel this needs exists. It is still sequenced behind the `#24-counters` measurement: do not
add a new source of ball spend and party churn to the build being measured until that
measurement is in.

## 2026-08-02 — Lead policy: super-effectiveness outranks level ONLY for a hunted counter

**Question.** `#24-leadpolicy` A+C stopped the bot leading a 1-HP Wonder Guard Shedinja into
Norman (9 of 9 runs in batch5). But `can_attack` is binary, so on the real party —
Shedinja L20 / **Machoke L29** / Marshtomp L35 — Machoke and Marshtomp tie on every term the
key measures and **level breaks it**. The freshly-trained counter was benched again, now by a
stronger neutral mon. Should 2× STAB outrank raw level?

**RULING (user, 2026-08-02): YES, but ONLY when the counter chain caught that mon for THIS
boss.** Not as a general rule.

**Why this option.** It is scoped to exactly the case that motivated it. The counter chain
only fires after ~6 losses, so for that boss the strongest mon is *already proven
insufficient* — which is the entire premise of travelling to catch a counter, and benching it
makes the catch-travel-train chain pointless. Everywhere else the existing behaviour is left
alone, so the proven Rustboro / Route 110 picks cannot regress.

**Rejected, with reasons:**
* **A general `outgoing` term.** Simpler and more consistent, but it changes lead selection in
  every fight, including ones that currently work — a L29 2× attacker is not automatically
  better than a L35 neutral one, and this model reads neither bulk nor movepool. Marshtomp led
  4 of batch5's Norman wins.
* **Leave as-is.** Safest, but the catch-travel-train chain would rarely change who actually
  fights, and batch5 already showed the funnel does not move while the counter sits in the bag.
* **"Prefer super-effective unless more than N levels below the strongest."** Close in spirit
  to option **(b)** of `#24-leadpolicy` ("weight the level gap"), which the same user had
  already ruled OUT — so it was not re-proposed as a live option.

**Implementation (agreed shape).** A new `is_hunted_counter` term in
`team_policy.lead_rank_key()`, ranked **after `incoming` and before the level tie-break**:

    (glass_wonder_guard, not can_attack, incoming, not is_hunted_counter, -level)

‼ Ordering matters and is deliberate. Placing it *after* `incoming` means a hunted counter
that is 4× weak to the boss still loses on defence — the term promotes the counter over an
equally-safe mon, it does not override type safety.

‼ **The edit was deliberately NOT applied when the ruling was given** — batch
`20260802-160603` was mid-flight and `x4_headless.py:843` relaunches dead lanes, which
re-import from disk and would mix two code versions into one measurement.

## 2026-08-05 — USER DIRECTIVE: stop bisecting after this batch; get back to STORY CONTENT

**User, verbatim intent:** *"I don't want to focus too hard on this if you keep going back and
forth unless you are actually solving a logic breaking bug. I want to eventually get back to
working on the rest of the story."*

**The ruling.** Regression-hunting is now TIME-BOXED. The last several days chased funnel
differences of ~5 points on n≈25 samples — noise-adjacent — while the actual goal (story
content past Winona, the end of built content) sat untouched.

### THE STOPPING RULE — apply it literally
Batch `20260805-*` is the LAST bisect batch.
* **If Balance→Feather ≥ 65%** → the regression is closed. Move to story content.
* **If it is < 65%** → **STOP ANYWAY.** Log the residual as a KNOWN ISSUE with the evidence,
  and move to story content. Do NOT open a fourth revert.

### What counts as "worth stopping the story for" from here
Only a **logic-breaking bug**: a hang, a crash, a run-ending derail, a feature that provably
does not do what it says. **Not** a few points of funnel movement on a small sample.

### Why this ruling is right, recorded so it is not re-litigated
Three regressions were found and reverted (`#24-leadpolicy` (c), `#24-areaitemgate`,
`#24-pc`) — all real, all measured, all worth fixing. But each was found by a 3-hour batch, and
the marginal value fell each time: the first was worth ~20 points of finish rate, the third
~5 points of one rung. Meanwhile the bot has reached **Winona = end of built content** since
2026-07-30 and no new content has been written in six days.

‼ The three revert flags stay `0` regardless of what happens next:
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD`, `POKEBOT_AREA_ITEM_GATE`, `POKEBOT_PC_ROTATION`.

## 2026-08-05 — `#24-hmslots`: RESERVE SLOTS. Deeper teams are deferred to an organic-play pass.

**USER RULING.** After `#24-partycap` measured a 36-point loss and was reverted, the user was
given four options for how to get visibly deeper teams. Ruling: **option 1, reserve slots** —
keep the pre-Gym-1 wild fill at **4** and let HM learners and counter catches claim the
remaining seats.

**‼ WHAT THIS MEANS CONCRETELY: NO CODE CHANGE. This ratifies the current behaviour.** The
reverted state already IS "reserve slots": the party fills to 4 with early wilds and then grows
organically to a measured mean of **5.85 by the Feather Badge** as the mons the run actually
needs come aboard. Nothing is being built. Recording it as a ruling so the next agent does not
read the open item as unfinished work and re-raise the cap — which is exactly how this cost
36 points once already.

### The user's stated intent, which is the important half
> "note that we want to revisit this in the future to make the bot play more organically like a
> regular player would (once we finish mapping the story out and can dedicate more time to this
> sort of thing)"

So this is explicitly a **HOLDING POSITION, not the end state.** The accepted cost is that teams
look thin EARLY — which was the user's original complaint and is deliberately not being solved
now. Tracked as `#24-organicteam`.

### Why the other three were rejected
* **Cap 5 (one free seat)** — plausible, and the funnel says a deeper team is free through five
  badges, but entirely unmeasured; it would cost a 3-hour batch to learn something cosmetic
  while the actual progress blocker (`#24-cavethread`) is unstarted.
* **Deposit to make room** — the real fix for a genuine 6-mon team, and what the Surf guard's own
  message asks for ("needs PC box management"). Rejected FOR NOW because it is the shape of
  `POKEBOT_PC_ROTATION`, which is disabled for costing ~19 points by depositing team members.
  It belongs in the organic-play pass, with a batch, not as a quick win.
* **Drop it entirely** — rejected only in framing; the effort does go to `#24-cavethread`, but
  the user wants the team-quality goal kept on the books rather than closed.

### Why this is the right call
The bot has sat at Winona = end of built content since 2026-07-30. Team depth is cosmetic;
the cave ladder gates Mt. Pyre, Magma Hideout and everything after. Spending the next batch on
seat allocation would repeat the pattern the 2026-08-04 ruling above was written to stop.

## 2026-08-06 — `#24-roster`: USER RULINGS on the PC roster / duplicate-catch exemption

Three rulings, given after a four-agent research round. Recorded so they are not re-litigated.

### RULING 1 — the `#24-organicteam` GATE IS LIFTED. Build this now.
The 2026-08-05 deferral ("once we finish mapping the story out") is **reversed knowingly**. The
user's reason is that it is story-ENABLING infrastructure, in their words:
> "if we implement this feature… it will help the story in the long run (less chance for failure,
> less errors with incompatible pokemon for bosses/gym leaders or missing HMs to travel, etc…)
> would make it easier to traverse the world mid-late game. We need this."

‼ This justification is **supported by measurement**, which is why the reversal is sound rather
than a preference: `no super-effective answer` accounts for **8 of 15 non-finishes** in batch
`20260806-055947`, and `nobody can learn Surf — hunting…` fires **~42 times per batch** in 16 of
17 stored batches. Both named failure classes are real and quantified.

### RULING 2 — round one does NOT change catch policy (user deferred to recommendation)
The roster operates on the catch stream the bot already produces. **No `#24-dexhunt`, no party-cap
change, no deposit path.** Rationale: `#24-partycap` + `#24-pcoverflow` shipped together, the batch
measured the BUNDLE, and the second is still unproven today. Catch policy gets its own round on a
clean baseline. ‼ Note this leaves the `#24-dexhunt` ruling of 2026-07-31 INTACT — it is not
reversed, merely not exercised.

### RULING 3 — "rare" (the duplicate-catch exemption) = THREE OR'd rules
> "Shiny, rare species (like a Male Skitty, Bagon, low encounter rate pokemon if that makes sense)"

and, after being shown that Bagon is statistically median:
> "Bagon although not considered rare per your explanation should be considered 'sudo-rare' as its
> gated to a specific location"

| rule | status |
|---|---|
| **shiny** | ALREADY WORKS — `StoryShinyCatchStrategy` catches duplicates into the box with a full party; both shiny paths pre-empt `custom_catch_filters`, so a duplicate rule cannot regress it |
| **rare gender variant** ("Male Skitty") | Computable PRE-CATCH (`personality_value & 0xFF` vs `Species.gender_ratio`). ‼ Gen 3 has only **7** gender ratios, so only 4 cutoffs exist; the only one including Skitty (25.4%) admits **86 species** |
| **rare species** | TWO sub-rules OR'd: **low encounter rate** (Skitty 2%, rank 11/132 — expressible) **OR access-gated / "pseudo-rare"** (Bagon 25%, rank 56/132 — NOT expressible by rate; rare because its only location is `METEOR_FALLS_B1F_2R` L25-35 behind Surf+Waterfall) |

## 2026-08-12 — §Ch19 is ONE segment covering TWO beats, graded on `RECEIVED_HM_DIVE`

**Decision.** Segment 19 does the Space Center defence *and* the HM08 Dive hand-over at Steven's
house, and the ladder guard is `RECEIVED_HM_DIVE` rather than `MOSSDEEP_SPACE_CENTER_STATE == 3`.

**Why.** `chapters.py` already defines chapter 19 as *"Defend the Space Center … then get HM08 Dive
from Steven's house"* with `flag("RECEIVED_HM_DIVE")` as its milestone. Grading the segment on the
Space Center var instead would have been a **silent ladder wedge**: the segment passes its own
`_guard`, but `current_chapter()` keeps returning 19 because its milestone is unmet, so the
dispatcher re-runs the chapter — and on the re-run the 2F Steven has been `removeobject`'d, leaving
nobody to talk to. Green acceptance, wedged run.

**Alternatives rejected.** *Two segments (19 = battle, 20 = Dive).* Rejected: it would need a second
milestone the registry does not have, and the two beats are separated by one warp and no decision.
*Grade on `VAR_STEVENS_HOUSE_STATE == 2`.* Rejected: set by the same script one line from the flag,
so it adds nothing and is not what the registry reads.

**And the acceptance asserts the ITEM, not only the flag** — `EventScript_StevenGivesDive` does
`giveitem` then `setflag` with no result check, so a full TM/HM pocket would set the flag while HM08
was never received. Cheap insurance against a green chapter that breaks §Ch21.

## 2026-08-12 — the party-selection menu is DRIVEN AND VERIFIED, not mashed

**Decision.** `choose_battle_party()` moves the cursor by reading it, presses A twice per pick, and
**verifies every pick against `gSelectedOrderFromParty`** (the game's own record, stored as `slot + 1`).

**Why.** Blind A-mashing cannot work here even in principle: A on an already-chosen mon opens
`ACTIONS_NO_ENTRY`, whose first item DESELECTS it, so a mash toggles one slot on and off for ever
with a healthy screen, no error and no flag movement. Two independent agents derived that from cited
decomp; the driven run then confirmed it by matching `INTENDED-PICKS [0,4,2]` to a measured
`gSelectedOrderFromParty=[1,5,3,0]` exactly.

**And it always brings THREE.** `Cmd_checkteamslost` has an explicit case for `TRAINER_STEVEN_PARTNER`
that sums HP over `gPlayerParty[0..2]` **only**, declaring the battle lost the moment the player's
own picks are down — regardless of Steven's health. So "bring fewer and let the ally carry it" is
exactly backwards: every mon left behind is a life removed from the loss condition. Selection is by
level then HP among mons the GAME considers eligible (non-egg, HP > 0), which also avoids the
fainted-mon submenu whose first item is SUMMARY.

## 2026-08-12 — gates must REFUSE, and their scope is chosen so they stay believed

**Decision.** `audit_flag_names.py` now exits 1 on a phantom name (it used to print its findings and
exit 0), and the new `repro_undefined_names.py` holds **only our own code** (`modules/story`,
`plugins/custom_modes`) to zero undefined names.

**Why the narrow scope.** Upstream `modules/` reports ~10 `TYPE_CHECKING`-only annotation names that
are harmless at runtime. A gate that prints ten known-benign findings every run gets ignored within a
week — this project has already documented that failure mode — and an ignored gate is worse than
none, because it looks like coverage. The wider tree's one REAL finding was filed as **KI-65**
instead, with a note that widening the gate means fixing KI-65 first.

**Alternative rejected.** *Whole-tree enforcement with a ratchet count* (the
`repro_no_silent_except.py` pattern). Reasonable, but a ratchet on a number nobody can attribute
invites tuning the number; zero-on-our-code is a claim that can be defended line by line.

‼ **The "pseudo-rare" ruling introduces a new dimension: ACCESS GATING, not scarcity.** It likely
makes the unresearched "where is each field move first required" recon a PREREQUISITE for that
sub-rule — under investigation. The encounter METHOD may be a cheap sufficient proxy (a species
available only via `surf_encounters` is Surf-gated by definition).

**Rejected: a single composite rarity score.** The three kinds have different data sources and
different failure modes, and with the two example species at ranks 11 and 56 of 132, no single
score ranks both above a common species without ranking half the dex above it. OR'd rules also
each log WHICH rule fired, which a composite cannot — and opacity of exactly this kind has already
cost this project a diagnosis.

### Sequencing agreed
1. `#24-hmteachloop` FIRST — `teach skipped` fires **611×/24 runs (~25/run)**; it burns frames and
   contaminates every HM counter that would serve as a baseline.
2. Live-prove `#24-pcoverflow`'s withdraw path IN ISOLATION (`withdrawing` = **0** to date).
3. Re-baseline one clean batch (the 52.0% baseline predates Mt. Pyre).
4. Then the slice — serving BOTH targets, since the withdraw primitive is identical for an HM
   carrier and a type counter.

---

## 2026-08-10 — RETIRE the finish rate as a grading metric; grade content BINARY

**Decision.** Stop using the cold-start finish rate to judge whether a change helped. Grade
mechanism work on **battle-level** metrics (~800 samples per batch) and content on **the story
flag the chapter sets** (1 run, yes/no).

**Why.** Four batches read **25.0 → 33.3 → 16.1 → 28.6%** at n≈30 runs each — mean ≈25.8%, not one
pair resolvable, ~12 hours of machine time spent to learn nothing. The arithmetic predicted it:
resolving a 10-point move needs ~300 runs ≈ **30 hours per question**. A week of genuine mechanism
wins produced no provable outcome win *because the instrument cannot resolve one*.

**Rejected — run much longer batches.** 30 hours per question, for a bot whose behaviour changes
daily. The answer would be stale before it arrived.
**Rejected — keep quoting it directionally.** That is how three separate readings this week became
"improvements" that were noise. Directional finish-rate claims are now explicitly disallowed.

---

## 2026-08-10 — PROMOTE `#24-battleitems` with NO resolved outcome metric

**Decision.** Promote the healing-item feature to `custom-pokebot` even though no outcome metric
moved resolvably.

**Why.** The MECHANISM is proven (policy unit-tested 27 ways; item use verified landing 3-of-3
after a real index-space bug was fixed; index guess derived from batch data; flips 20 → 2 and
both-spaces-failed 10 → 0 on the validation batch), and every failure mode is BOUNDED — the no-op
guard costs at most one turn per battle and then disables items for that battle. Given the
decision above, waiting for a resolved finish-rate improvement would mean waiting ~30 hours per
question, i.e. never.

**Rejected — hold until an outcome resolves.** Under the retired metric that is indefinite.
**Rejected — promote and claim it improves outcomes.** The DIVERGENCE-LOG entry states plainly
that it must NOT be quoted as a finish-rate improvement.

---

## 2026-08-10 — SPEND ON CONTENT (coverage), not on optimising the first six badges

**Decision.** The next work is the **Magma Hideout chapter**, not further reliability tuning.

**Why.** `01-VISION-AND-DESIGN.md` says the Story bot exists to be a *"known-good, repeatable
trajectory"* — a **reference/scaffold for the separate Pokémon Emerald AI project** — and that
*"complete the story unattended is step 1"*. The bot has reached six badges for a week; coverage
has not moved. **A failed run can be re-run; content that does not exist cannot be.** Coverage is
also binary and instantly verifiable, which sidesteps the measurement problem entirely.

**Rejected — keep optimising reliability first.** The vision's own status note says failures are
already *"bounded and diagnosable rather than fatal and silent"*, which was the stated bar; more
finish-rate work is past diminishing returns.
‼ **What would reverse this:** if the user would rather have ~90% reliability to Gym 6 than a
shakier path to Gym 8. That is a product call, and it was put to the user explicitly.

---

## 2026-08-10 — KEEP the self-correcting index space rather than hard-coding one rule

**Decision.** `StoryItemBattleStrategy` picks its first party-menu index space from the target's
position and **flips once, logging which space landed**, rather than committing to one convention.

**Why.** Measured over a batch, party-order landed **19/19** when the target was party slot 0 and
**never** above it, while every landing above slot 0 was battle-order — i.e. the ordering is
**conditional**, and the after-faint chooser uses the opposite convention *correctly* in its own
context. A single hard-coded rule would be wrong somewhere, and the flip both fixes it at runtime
and produces the data to settle it.

**Rejected — hard-code party-order** (fails above slot 0) **or battle-order** (fails at slot 0).
**Rejected — "fix" the planner.** It was modelling the game correctly; the bug was ours.

---

## 2026-08-10 — Ch15 is built as THREE separately-graded increments, not one chapter function

**Decision.** The Magma Hideout ships as `travel_to_magma_hideout_door()` →
`open_magma_hideout_entrance()` → `enter_magma_hideout()` → `do_magma_hideout()`, each with its
own binary acceptance and its own harness driver, with a thin
`do_magma_hideout_chapter()` composing them.

**Why.** The first driven run of the travel leg failed for **two independent reasons at once** —
a party that Ch14 hands over 3/6 fainted, and a driver that inherited `BotMode.on_whiteout()`'s
default of False. As one monolithic chapter both would have surfaced as a single opaque
"chapter failed at frame N" and the second (an instrument bug) would very likely have been
written down as the first (a route blocker). Separately-graded increments made each one name
itself. This is the §Ch14a "explicit short legs" principle applied one level up.

**Rejected — one `do_magma_hideout()` that does everything**, matching some earlier chapters.
Cheaper to write, and it hides exactly the distinction that cost this chapter three wrong
conclusions already.

---

## 2026-08-10 — grade Jagged Pass reachability by VAR_JAGGED_PASS_STATE, never by calculate_path

**Decision.** The hideout entrance's availability is tested with
`get_event_var("JAGGED_PASS_STATE") >= 2`, and the harness driver's acceptance is that var —
not "are we standing next to the door".

**Why.** `JaggedPass_OnLoad` walls the door shut with `setmetatile`, and `calculate_path` reads
the ROM **layout**, so it reports "2 waypoints" to a tile the running game has made solid. Three
separate conclusions about this door across three weeks were that wall, misread. The var is
written by the very script that opens the metatiles, so it cannot disagree with reality.

**Generalised (now also in `08-MISTAKES`):** on any map whose decomp `OnLoad`/`OnResume`/
`OnTransition` calls `setmetatile`, a static path result is not evidence in either direction.

**Rejected — trust the static planner and step at the door.** That is what the pre-Emblem
`--driver magmadoor` run effectively did; it pressed Up twelve times, did not move, and the
result was recorded as "a real south-facing ledge".

---

## 2026-08-10 — the en-route heals are best-effort; the chapter does not die on a nice-to-have

**Decision.** Ch15's Lilycove, Mauville and Lavaridge heals are wrapped and logged on failure;
only the journey legs themselves are allowed to end the chapter.

**Why.** Measured: the live navigator refuses `LAVARIDGE_TOWN` from `ROUTE112` 3 times out of 3
("it is not walkable from ROUTE112") even though `calculate_path` scores that span at 66
waypoints — and by then the bot is already **standing on the cable-car station's approach tile**,
i.e. the trip has succeeded. Letting an optional top-up abort a completed haul would have thrown
away ~70,000 frames of correct work on every attempt.
‼ **But never silently:** each skipped heal prints, because a skipped heal is the most likely
cause of a later whiteout and the two must not be confused.

**Rejected — require every heal** (throws away successful hauls). **Rejected — drop the heals**
(the party arrives 3/6 fainted; the first build with a single late heal whited out at f23674).

---

## 2026-08-11 — menu detectors watch the INPUT HANDLER, not just the display task

**Decision.** Where the bot waits on a Gen 3 yes/no prompt, it matches a **tuple** of task names
covering both the display task (`Task_XxxYesNo`) and the input handler
(`Task_HandleXxxYesNoInput`) — `_PROMPT_TASKS` and `_STOP_TASKS` in `teach_hm_move`, shared by
both loops that read them so the two can never drift apart.

**Why.** The decomp's yes/no tasks set their own function pointer to the input handler in the
same frame they display the menu, so the display task is observable for exactly one frame.
Measured on a live trace: `f3232735` it is there, `f3232736` it is gone for ever.

**Alternatives rejected.**
* *Poll faster / raise the budget.* Four rounds of budget tuning already failed on this bug; the
  window is one frame wide, so no budget fixes it.
* *Read the menu TEXT instead* (`#24-menutext`). Correct in the long run and still open, but it is
  a much larger change and this fix needs none of it.
* *Stop pressing A in the post-select loop.* The A presses are what carry the "…can't learn more
  than four moves…" chain to its end (41 presses over 489 frames, measured). Removing them trades
  a wedge for a stall.

## 2026-08-11 — a fault injection that models a TIMING miss must fire exactly once

**Decision.** `TEACH_CANCEL_FORGET` is latched to one shot; fault-injection switches in this
project model a single mistimed event unless the bug is genuinely repetitive.

**Why.** The fix's mechanism is retry. An always-on fault makes recovery impossible by
construction, so the corrected arm looks worse than the broken one — which is what the first run
of this A/B reported.

**Alternative rejected.** Grading the arms on "did it wedge" rather than "did it learn". That
hides the difference: both arms wedge under an unsatisfiable fault.

## 2026-08-11 — every button in the teach flow goes through a recording `_press()` wrapper

**Decision.** `teach_hm_move` presses only via `_press()`, which appends to a trace buffer;
`TEACH_TRACE=1` then emits one line per observable change carrying the buttons pressed since the
previous line.

**Why.** A menu ping-pong that our own A-mash is driving is indistinguishable, in a plain
per-frame task dump, from one the game is driving. Pairing cause with effect on the same line is
what cracked this bug after three summary-only records could not.

**Cost accepted.** Structural repros that pinned the literal `context.emulator.press_button(...)`
text went red and were updated to match meaning rather than spelling — noted as the risk of
spelling-based structural tests.

## 2026-08-11 — KI-56 is fixed with the Escape Rope the DUNGEON provides, not a shopping detour

**Decision.** Unstrand the bot from the Magma Hideout by picking up the **Escape Rope item ball
already inside it** — `MAGMA_HIDEOUT_3F_3R (9,19)`, approached from `(9,20)` facing Up — and using
it. It lands at `JAGGED_PASS (16,19)`.

**Why.** The strand is real: the eight-map warp graph reaches **18 of 20 nodes** from the stranded
tile, and the two it misses are the exit warp and Jagged Pass. So the fix must leave the map
without walking, which means Dig or an Escape Rope, and the bot has no Dig. The ball sits in a room
§Ch15 **already walks through**, is still reachable from the stranded tile, and its flag reads
unset — so the escape costs no travel at all. It is also almost certainly the intended answer:
Game Freak could only ship a one-way boulder puzzle here *because* they put an escape inside it.

**Alternatives rejected.**
* **A return-route study (KI-56 option 2)** — formally DEAD. The warp graph shows no walk-out
  exists once the Strength pushes reset; only the 44-tile entrance pocket holds the exit.
* **Re-pushing on the way out (option 3)** — already dead: both push-from tiles sit in the pocket.
* **Buying Escape Ropes before entering.** Works, and the bot already has `buy_in_shop()`, but
  ‼ **Lavaridge Mart does not stock them.** The nearest that do are Fallarbor, Slateport,
  Rustboro, Petalburg and Lilycove Dept. 2F — every one a long detour off the Jagged Pass
  approach, added to a leg that has already produced a measured whiteout. Kept as the FALLBACK if
  the pickup proves unreliable.
* **Whiting out on purpose.** It is what a cornered human could do and it always works, but it
  costs money and is a derail, not a route. Against the north star.

**Cost accepted.** Escape Rope support is new capability the bot has never had (0 hits across
`modules/story/` and `modules/modes/util/`). It is built once and every future dungeon wants it.

## 2026-08-11 — §Ch17's route is SOLVED BY THE WARP GRAPH, and each hop is graded on the TILE

**Decision.** Build the Lilycove Aqua Hideout as an explicit **18-hop warp route** derived from the
ROM warp table by `probe_aqua_hideout_graph.py`, and grade every hop on **(map AND arrival tile)**,
not on "the map changed".

**Why the warp graph.** B1F is a warp-panel maze: **21 of its 25 warps lead back to B1F itself**
(including a 3x4 panel grid at x=42/45/48, y=3..17), and B2F has six more same-map panels.
`calculate_path` "is not able to use warps", so no planner can cross these floors — the same shape
that made KI-56 look like a strand. The instrument built for the Magma Hideout answered it
unchanged, which is the second time that graph has paid for itself.

The solved route bounces **B1F -> B2F -> B1F -> B2F**, which is not a bug in the search: it is how
the dungeon is built.

**‼ Why the success test changes.** §Ch15 grades each warp hop with `_enter_warp_by_navigation`'s
"did the MAP change?" — the correct test there, because every hop crossed floors. **It is useless
here**: most hops in this maze are `B1F -> B1F`. A panel that dumped us in the wrong corner would
read as success and the next leg would navigate from a false position. Every hop therefore asserts
the exact arrival tile the warp table predicts.

**‼ The hazard this creates, recorded before it bites.** Walking ACROSS a panel tile fires it, and
`calculate_path` treats panels as ordinary walkable ground — so a plotted walk may teleport
mid-leg. The tile-level assertion is also the detector for that: an unexpected position means a
panel was crossed, and the leg re-plans from where it actually is rather than continuing on a
false assumption.

**Alternatives rejected.**
* *Let `navigate_to_anywhere` route the dungeon.* It cannot: the maze is same-map warps.
* *Grade on the map only (the Ch15 pattern).* Cannot distinguish the 21 same-map panels.
* *Hard-code a movement script.* Brittle, and blind to the six grunts standing in the corridors.

**Cost accepted.** The route is STATIC — six Aqua grunts (`FLAG_HIDE_AQUA_HIDEOUT_GRUNTS`) are
invisible to the planner, and §Ch15 was bitten three times trusting a static answer about a
dungeon. The route means "worth driving", and the driven run is the proof.

## 2026-08-12 — the warp-maze solver is now a TOOL, and its control is a route we already drove

**Decision.** Generalise the one-off hideout probes into `tools/story-dev/probe_warp_maze.py`,
parameterised by a `MAZES` table (anchor, maps, start, goal tiles, planner control), and make its
self-check **reproduce the §Ch17 Aqua Hideout route that has already been driven to a PASS**.

**Why.** Three dungeons in a row have had the same shape — rooms joined by warps rather than
corridors, which no planner here can cross (`calculate_path` "is not able to use warps"): the Magma
Hideout (KI-56), the Aqua Hideout (§Ch17), and now the Mossdeep Gym. Rule of three; the method was
already written twice.

**Why that control and not a fresh assertion.** A regenerated route is only trustworthy if the
generator still produces a route we know works in the real game. Comparing against a **driven**
prefix turns the tool's own refactoring into a testable claim. ‼ It earned its keep immediately:
the first version of the check compared bare TILES after filtering maze maps in, and reported FAIL
on a route that was perfectly correct. It now compares full `(map, tile)` nodes — *a control that
is ambiguous about what it compares cries wolf, and a control that cries wolf gets ignored.*

**Carried into the tool:** the panel-crossing rule (a walk edge only counts if the path's
intermediate waypoints avoid warp tiles) and the reason `Waypoint.is_warp` cannot express it
(`map_path.unroll_path` sets it only on the final waypoint).

**Cost accepted / what it does NOT do.** It solves **warp-EVENT** mazes. It did **not** solve the
Mossdeep Gym — see `05-KNOWN-ISSUES` KI-58: that gym's tiles carry a distinct metatile behaviour,
`MB_MOSSDEEP_GYM_WARP`, and are a different mechanic. The tool refused rather than guessing, which
is the behaviour that matters.

## 2026-08-12 — Claude subagents are STANDING-APPROVED for research and assistance

**Decision.** The user granted open-ended approval to use Claude subagents for research, recon and
assistance, now and in future sessions. Recorded in  as a project directive so it does
not have to be re-asked.

**Why.** Measured, not assumed: five parallel agents resolved **KI-58** in one round after four of
my own offline models had each concluded the Mossdeep Gym had no route to its own gym leaders — an
impossibility none of them could see, because all four modelled the gym as *walk + warp* and the
gym has a third primitive (floor switches that relocate 21 statues). The same round surfaced
**KI-59** and **KI-60**, two latent bugs in our shared pathfinder, as a side effect.

**What makes them work (from that round).** Different ANGLES rather than one broad question — the
five were decomp mechanics, human-play walkthrough, an audit of our own code, a live tile dump, and
one explicitly ADVERSARIAL. **The adversarial one found the answer.** Launch them in a single
message so they run concurrently, and hand them the already-ruled-out list with citations.

**Constraint, carried over from the Gemini rules.** Their output is a NOTE, never truth. KI-58's
mechanic was believed only after stepping on the switch in our own harness and watching the statues
move. Three agents agreeing is a strong search signal and still not proof.

**Alternative rejected:** asking per-use. The approval is standing precisely because the cost of
asking exceeded the cost of the tokens.

## 2026-08-12 — §Ch18's chapter function lives in `mossdeep_gym.py`, not `early_game.py`

**Decision.** `do_mossdeep_gym_chapter()` is defined in `modules/story/mossdeep_gym.py` alongside
the puzzle executor, and `plugins/custom_modes/story_mode.py` imports it from there. Every previous
chapter (§Ch1-§Ch17) is defined in `modules/story/early_game.py`.

**Why.** `early_game.py` is already 8,769 lines. All of §Ch18's logic — the puzzle model, the BFS
solver, the executor, the leader fight — is gym-specific and already lives in its own module, so
putting the chapter anywhere else would separate it from the only code it drives. The import site in
the ladder is one line either way.

**Alternatives rejected.**
* *Put it in `early_game.py` for consistency.* Rejected: consistency with a file that is already too
  large is not a virtue, and the chapter would then reach across modules for every helper it uses.
* *Put the whole gym in `early_game.py`.* Rejected outright — it would add ~600 lines to the file the
  project most needs to stop growing.

**Consequence to watch.** There are now two places a chapter can live. If a third such module
appears, the convention should be made explicit in `02-ARCHITECTURE.md` rather than left as
precedent — a split that nobody wrote down is how the next agent ends up looking in the wrong file.

---

## 2026-08-13 — RULING: **Shoal Cave is NOT adopted as a hunting ground.** Route 117 stays.

**Decision delegated to me by the user**, with the explicit caution that *"tide levels [change at]
certain times of in-game time and [change] the cave"*. That caution was correct and is what the
ruling turns on.

### The decision
* **Do NOT add Shoal Cave to `TRAINING_GRASS`, and do NOT build the separate HM-ground table yet.**
* **Keep `ROUTE117 (31,16) ['Marill']`**, which `_hm_hunting_grounds(HM08)` already returns and
  which was **driven end-to-end to an `ACCEPTANCE: PASS` today** (`--driver divelearner`).

### Why — the decisive reason is KI-73, not the tide table
The attraction was real: Spheal is **50% of the land table at L26-32 with catch rate 255**, against
Marill's **10% at L13, catch rate 190**, and Shoal Cave is 103 waypoints + one door away versus
**1,055 waypoints** to Route 117. On paper it wins on every axis.

**But we cannot see the room we would be hunting in.** `get_map_data` builds `_map_header_cache`
**once, from the static compile-time `gMapGroups` ROM pointer table** (`map.py:1766-1785`), which
can only ever yield the **compiled low-tide** layout for map (24,46). The high-tide floor is
installed at runtime by `setmaplayoutindex` patching the live `gMapHeader` RAM struct — which that
table never reads — and **nothing in `modules/` ever clears either cache**. Filed as **KI-73**.

Three consequences, in increasing order of how much they settle the question:
1. At high tide the planner routes over the **wrong floor plan**, and ‼ **`calculate_path` does not
   raise** — it returns a confident path across tiles that are water or wall in the live room. That
   failure is **invisible to a run that reports success**.
2. ⇒ **KI-54's own supporting figure is compromised.** Its *"65 walkable tiles at high tide (332 at
   low)"* was almost certainly measured through the same lens, making it very likely two views of
   the **same low-tide layout**. So the claim *"the Spheal table is live at both tides, no tide
   handling needed"* rests on evidence that cannot see high tide. That section is now retracted in
   `05-KNOWN-ISSUES.md`.
3. The decomp claim that the tide is *"sampled only on `ON_TRANSITION` and frozen for the visit"* —
   the thing that would make an entry-time check sufficient — **has never been audited here**;
   `src/time_events.c` is not vendored in this repo.

**⇒ We would be choosing a hunting ground inside the one room whose geometry our tools are
structurally unable to observe, gated on an in-game clock, to obtain a better HM slave for a
capability we already have working.** That is a bad trade, and I am not making it.

### Alternatives considered and rejected
| option | rejected because |
|---|---|
| Add a Shoal row to `TRAINING_GRASS` | `best_training_area` (`training_areas.py:346-364`) reads the **same list** as `_hm_hunting_grounds`, with no per-consumer filter. A Shoal row becomes the highest band and **redirects ordinary training for every team from ~L26 up**, into a dead-end cave that has **no `NO_RETURN_GROUNDS` entry** |
| Build the separate HM-ground table now | It cleanly decouples the two consumers, but it does **nothing** about KI-73 — we would ship a correct table pointing at an unobservable room |
| Adopt it but gate on `FLAG_SYS_SHOAL_TIDE` | The flag is readable and this is the right *shape* — but it fences the ENTRY, not the PLANNING. KI-73 corrupts the geometry regardless of when we enter |
| Wait for low tide | Emerald's RTC is real time; low tide is a subset of hours. Nothing in this codebase detects, waits for, or skips a tide (`modules/story/*` has **zero** references to tide or shoal), and `ensure_hm_learner`'s 40,000-frame deadline would simply burn |

### What would unlock it — all three, in order
1. **Fix or fence KI-73** — key the layout cache on the live layout pointer, or invalidate on map
   transition. ‼ This touches shared pathfinding every mode depends on, so it needs its own A/B.
2. **Re-measure the high-tide geometry** once (1) makes that possible, and find a spin tile that is
   walkable **and** encountering at **both** tides.
3. **Live two-way sweep** that tile — static evidence is not enough here (the Route 114 demotion),
   and it must avoid `(20,30)` and its south neighbour (`MB_SHOAL_CAVE_ENTRANCE`, a south-arrow warp).
Only then is the separate HM-ground table worth building.

### What this costs us
Nothing we have. The Dive learner is already acquired by playing. The cost is that the learner is a
**Marill L13** rather than a Spheal L26-32, and the trip is long. Both are quality, not capability —
and a quality upgrade is exactly the kind of thing that should wait behind a correctness fix.

‼ **Revisit trigger:** if KI-73 is ever fixed for other reasons, re-open this ruling — most of the
objection dissolves with it.

### ⚠ AMENDED the same day (2026-08-13) — the RULING STANDS, but my stated reason was partly WRONG

A live measurement (`probe_shoal_tide.py`, re-run and confirmed by me) landed after the ruling
above. **The verdict does not change. Two of its supporting claims do, and both were mine.**

**WRONG #1 — "we cannot see the room."** Overstated. `get_map_data_for_current_position()`
(`map.py:1750`) reads the **live** `gMapHeader` and *does* follow `setmaplayoutindex`; only
`get_map_data(map, coords)` is locked to the static ROM header. KI-73's real defect is that **both
write the same `_map_layout_cache` keyed on `(group, number)`, so the first writer wins for the
session** — cache poisoning, not blanket blindness. Still real, still unfixed, but narrower.

**WRONG #2 — "KI-54's 65-tile figure is probably a second view of the low-tide layout."**
**Refuted.** The probe reproduced the 65 **exactly**: a genuine high-tide component of 65 tiles,
all `Cave`, all with encounters. **The count was right.** What nobody had checked was its
**reachability** — it is an **island**, not on-foot connected to the entrance warp.

**⇒ THE REAL REASON, and it is better than the one I gave:**

```
spin tiles (on foot + has encounters + REACHABLE from the arrival warp (20,30))
    LOW tide : 278
    HIGH tide:   0
```
All three of KI-54's candidates — (25,30), (14,30), (20,24) — become `Shallow Water` with
`has_encounters=False` at high tide. ‼ **The failure mode is a SILENT STALL, not a crash:** the tile
is still *standable*, so `ensure_hm_learner` spins out its full 40,000-frame budget meeting nothing
and then fails for what looks like bad luck. The 181-tile region the bot can actually reach at high
tide contains **zero** encounter tiles.

**⇒ AND THE TIDE GATE IS CHEAPER THAN I ASSUMED.** Decomp-confirmed against `pret/pokeemerald`
(the only caller of `UpdateShoalTideFlag` is `ShoalCave_LowTideEntranceRoom/scripts.inc`
`MAP_SCRIPT_ON_TRANSITION`): the tide is sampled **once on entry from outdoors and frozen for the
visit**. LOW = hours **03–08 and 15–20**. And the bot can both **predict** it
(`modules/clock.py` → `get_clock_time().hours`) and **assert** it after the transition
(`get_event_flag("SYS_SHOAL_TIDE")`, set = HIGH). So "check the clock, then verify the flag" is a
handful of lines, not a subsystem.

### The ruling still stands — on the two objections that survived
1. **The 278 low-tide candidates are STATIC evidence only.** No live two-way sweep. This project
   demotes statically-derived grounds (the Route 114 lesson), and that rule is not waived because
   the numbers are pretty.
2. **KI-73 is unfixed.** Cache poisoning across a tide boundary is exactly the kind of defect that
   makes a spin tile behave differently on the second visit than the first.
3. And unchanged: **Route 117 already works**, driven end-to-end today. The gain remains **quality,
   not capability**.

**Revised unlock conditions** (shorter than before, because the tide half is now solved):
fix/fence **KI-73** → **live two-way sweep** one of the 278 low-tide candidates → ship it behind the
clock+flag gate above, in a **separate HM-ground table** so `best_training_area` is untouched.

‼ **A METHOD NOTE I do not want lost.** I inferred "the tool is broken, therefore its numbers are
untrustworthy" and nearly discarded a correct measurement. The tool *was* broken; the number was
still right; the error was in what had been concluded from it. **Re-derive the number before
throwing it away.**

### 📌 User note, 2026-08-13 — Shoal Cave's encounters vary by ROOM (like Granite Cave), and land ≠ surf

Checked against `probe_shoal_tide.py` / `probe_dive_learner_plan.py` output rather than agreed from
memory. **Both halves are right, and both reinforce the ruling.**

**By room** — each Shoal Cave room is its own map with its own header, exactly like Granite Cave's
floors:
| room | map | land table |
|---|---|---|
| `LOW_TIDE_ENTRANCE_ROOM` | (24,46) | Spheal ~50%, Zubat ~45%, Golbat 5% |
| `LOW_TIDE_INNER_ROOM` | (24,47) | same |
| `LOW_TIDE_STAIRS_ROOM` | (24,48) | same |
| `LOW_TIDE_LOWER_ROOM` | (24,49) | same |
| **`LOW_TIDE_ICE_ROOM`** | (24,83) | **Spheal 45%, Zubat 40%, SNORUNT 10%, Golbat 5%** ← differs |

So "different Pokémon walking around the cave" is real at the **room** granularity (the Ice Room
adds Snorunt); within a single room Gen 3 has one land table, so it does not vary tile-to-tile.

**Land vs surf** — and this is the half that matters for the ruling. The entrance room carries
**both** tables (`land_rate=10, surf_rate=4`), and they are very different: Spheal is ~**50% of the
LAND** table but only **10% of the SURF** table (Tentacool 60%, Zubat 30%).

‼ **Why that strengthens the "not adopted" ruling rather than weakening it.** At high tide the
floor of the entrance room *becomes water*. So the room does not merely lose its land tiles — the
encounters that remain are fired from the **surf** table, i.e. a different, Spheal-poor species mix
that also requires Surf and a water-capable spin. `_hm_hunting_grounds` reads **land encounters
only** (`early_game.py:4319`), so it cannot price or use that. This is a second, independent reason
the room is a low-tide-only ground — on top of the measured **0 reachable land encounter tiles at
high tide**.

⇒ No change to the ruling. Added to the unlock conditions: any future spin tile must be validated
as a **LAND** tile (on foot, `elevation != 1`), in a **named room**, at **low tide** — three
qualifiers, not one.

## 2026-08-13 — KI-59: land the MEASUREMENT as its own item; the fix is FIX-A + a new exit-blocking concept, A/B'd on a LIVE map

**Decision 1 — split the work: measurement now, fix next.**
`map_path.py` is shared by every bot mode. The session's measurement produced a *retraction* of an
instruction sitting in four documents, which is independently valuable and carries no code risk, so
it ships as a completed item on its own rather than riding along with a pathfinding change. Rejected:
doing both in one commit (a doc correction bundled with a shared-code change cannot be reverted
independently, and this project's own rule is "steps 2-6 per completed item, not batched").

**Decision 2 — the fix direction is FIX-A ("the named direction is a walled EDGE"), not FIX-B.**
Two candidate readings existed and the codebase alone could not choose between them, because the
array is a whitelist indexed by **direction of travel**:
* **FIX-A** — `Impassable North` = the tile's north EDGE is a wall ⇒ clear `[opposite(D)]` ⇒ `[NE-W]`.
* **FIX-B** — `Impassable North` = "you may not travel north onto it" ⇒ clear `[D]` ⇒ `[-ESW]`.
They agree on `"… North and South"` and disagree on every single-direction string — and **347 of the
401 live tiles are single-direction `Impassable North`**, so guessing was not an option.
**Chosen: FIX-A**, on decomp ground truth: `IsMetatileDirectionallyImpassable`
(`event_object_movement.c:4715-4722`) consults `gOppositeDirectionBlockedMetatileFuncs` on the tile
you STAND ON and `gDirectionBlockedMetatileFuncs` on the DESTINATION (`:893-905`), which makes
`MB_IMPASSABLE_<D>` a symmetric **edge wall** — blocking entry across that edge *and* exit across it.
Corroborated by an independent derivation before the decomp was read, and by the geometry (live
tiles form horizontal runs consistent with cliff edges). Rejected FIX-B: it contradicts the decomp's
array pairing and would have inverted the most common case in the game.

**Decision 3 — the fix is NOT complete without a new exit-blocking concept.**
`PathTile` has no way to express "may not LEAVE in direction D"; `is_tile_accessible` only ever
inspects the *neighbour*. Entry-only would still let the planner walk north off a wall — real, not
theoretical: **22 of Island Cave's 48 live tiles have open floor to their north**. So the fix adds a
per-tile blocked-exit set checked on the SOURCE tile in the A* expansion loop. Rejected: shipping
the one-line entry fix alone (a strict improvement, but it trades a known wrong model for a
half-right one and would be recorded as "fixed").

**Decision 4 — the A/B runs on `VICTORY_ROAD_1F`, with a Seafloor room as the NEGATIVE control.**
Zero of the cavern's 115 tiles reach the branch, so the A/B four documents prescribed would have
shown no delta. ⚠ **First choice was ISLAND_CAVE (48 live) — and an adversarial review rejected it**:
Island Cave, Desert Ruins, Ancient Tomb, Shoal Cave Low Tide Inner Room and the Lilycove Contest
Lobby all rewrite their own tiles at runtime (`setmetatile` — in the tombs that *is* the braille wall
opening — and `setmaplayoutindex` in both Shoal Cave low-tide rooms), so a static-layout A/B there
measures a floor plan the game may replace. **Chosen: `VICTORY_ROAD_1F` (29 live tiles), which uses
neither command**, plus a **negative control on a Seafloor room** to demonstrate the branch is inert
there, and assertions on **both** directions (entry and exit). Rejected: the Regi tombs (runtime
rewrite), Shoal Cave (same, and it is entangled with the tide question).

**Decision 5 — the "Shoal Cave is NOT adopted" ruling is NOT reopened here.**
`probe_shoal_tide.py:364-367` replicates the inversion and produced the number behind that
user-delegated ruling, over rooms carrying 89 live tiles. Reopening a decision the user delegated
and received is the user's call, not an agent's. Recorded as a flag with the re-derivation named, so
it happens deliberately after the fix instead of by surprise.

## 2026-08-13 — the next BUILD is §Ch20 (Seafloor Cavern), NOT the Regi arc — and KI-59 was never the arc's blocker

**The claim I was about to act on**, and it was **REFUTED** by an adversarial review plus a decomp
recon: *"KI-59 blocked the Regi arc (144 of the 401 live tiles are the tombs); I fixed it, so the
arc is unblocked — start building."*

**Why it is wrong, in three independent ways.**
1. **The tombs barely use the pathfinder where those tiles are.** `puzzle_solver.py` walks its laps
   with `follow_path`, whose docstring (`modes/util/walking.py:78-83`) says *"There is no collision
   checking"*. `calculate_path` is used only for the approach and the exit.
2. **The 144 tiles describe a room that is not on screen.** The tombs `setmetatile` themselves —
   that *is* the braille wall opening — and our reader takes the **compile-time ROM layout**
   (`map.py:770`). Filed as **KI-74**.
3. **Empirical.** Upstream, `custom-pokebot` and the 40cakes mirror all still carry the inversion
   and ship a working Regi Puzzle Solver. Had the inversion made tomb routing impossible, that mode
   would be dead for every upstream user.
⇒ ‼ **This was the same error I had logged that morning** — counting tiles a bug applies to without
checking whether anything REACHES them — committed a second time in one day, in the opposite
direction (counting tiles a FIX applies to).

**The arc's real cost, measured, not guessed.** `probe_regi_capabilities.py` reports **10 missing
gates**, and the audit found they need ~7 subsystems that do not exist: fishing as a *story*
capability (`fish()` is an input masher with zero story callers, and rod choice goes through a
**human GUI prompt**), underwater wild encounters (`EncounterType` has no Underwater member), TM
acquisition + `use_tm` (`teach_hm_move` is HM-only), Flash acquisition, a no-KO/no-whiteout
legendary catch policy, a **bounded** exact-tile path executor, and the arc has **no chapter entry**
in `chapters.py` at all. Plus a hard serial prefix: Dive → TM28 → Dig → Super Rod → Wailmer →
evolve → Relicanth → reorder → Sealed Chamber, before a single tomb entrance physically exists.

**DECISION — the order is:**
1. **`#24-ch20rename`** (small, safe, the punch list already says do it at the start of a session):
   `--driver ch21dive`, `probe_ch21_topology.py` and two note filenames are misnomers pinned to
   **Chapter 20**. Every hour it survives raises the odds the next agent builds the wrong chapter.
2. **§Ch20 Seafloor Cavern / Kyogre — the real next build.** It IS the ladder
   (`chapters.py:233`, graded on `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`; `story_mode.py:3654` is "END OF
   BUILT CONTENT"), it is uniquely de-risked (the dive leg is **driven 6/6**, KI-63 is wired in
   sandbox, `puzzle_solver.py` supplies room coordinates free), and its blast radius is **additive**
   — one module, one segment, no shared code. Two known traps, both cheap: apply **KI-72**'s rule
   (hand-pick the surfacing tile and assert its `tile_type`; never let the planner choose), and do
   **not** stop at `ROOM9 (16,42)` — that is Archie's cutscene tile, and the standing rule is
   *"and the bot can continue"*.
3. **`#24-r110mauville` / KI-48** — the highest-frequency *observed* defect (72 `could not reach`
   events in one batch, 3/3 deterministic, ~1,400-frame repro). Budget a MEASUREMENT, not a fix:
   its root cause is still a hypothesis.
4. **The Regi arc** — after §Ch20/§Ch21, or as an explicitly costed multi-session project.

**Rejected:** starting the Regi arc now (a 7-subsystem side quest whose first payoff is 9 serial
steps away, on a map model that is wrong about the door). **Also rejected:** fixing KI-70/KI-71/KI-73
now — all three are code-verified and **never observed**, and KI-70 costs ~30 frames per rotation on
the hottest path in the bot to fix something measured *passing*. Paying premium risk on shared code
for zero measured events is exactly the trade this project keeps regretting.

**Left explicitly to the USER:** promoting `map_path.py` (and the KI-63 wiring) to `custom-pokebot`.
‼ Note that **KI-59 promotion is a hard prerequisite of the Regi arc in `custom-pokebot`**, so that
decision and decision 4 are linked.

## 2026-08-13 — USER RULING: `stash@{0}` is KEPT PERMANENTLY as a record. Do not drop it.

**The decision.** The three-week-old stash found on 2026-08-13 (`WIP on main: e0f723e4`, 2026-07-24,
a 14-line Fortree Gym "only ride out a scene that exists" guard) **stays**. The user's words:
*"lets keep the stash as a record so its not destructive."*

**Why this is worth writing down rather than just not-acting.** I had reported the stash as
"functionally superseded and safe to drop" — its substance IS already in today's `early_game.py`,
reimplemented during the rotating-gate rewrite. That made "drop it" the obvious tidy-up, and the
next agent to notice a stale stash would reach for `git stash drop` for exactly that reason.
**They must not.** The ruling is that a superseded stash is still a RECORD, and dropping it is a
destructive act that buys nothing: a stash costs no space that matters, breaks no gate, and cannot
affect a build.

**Standing rule that follows:** ⛔ **never `git stash drop`, `git stash clear`, or `git stash pop`
in this repo.** `pop` is separately banned because it mutates a global stack (that is how this stash
was disturbed in the first place — see `08-MISTAKES.md`). If a stash's content is ever needed,
inspect it read-only with `git stash show -p "stash@{N}"` and apply the change by hand.

**What to do instead of dropping:** the stash is documented in `04-HANDOFF.md`'s STATE table with
what it contains, why it is superseded, and this ruling — so it reads as an intentional artefact
rather than as unfinished business a future session must resolve.

---

## 2026-08-13 — §Ch20 Room 1: DRIVE UPSTREAM'S SEQUENCE, not our own build spec's — and treat that spec's "exhaustive" claims as unaudited

**The decision.** Where upstream 40Cakes' shipped Emerald Seafloor route and our decomp-derived
build spec disagree on a push, **upstream wins until arbitrated**, and our spec's *optimality /
uniqueness* claims carry no weight at all.

**What forced it.** Room 1. Upstream (`40cakes repo/pokebot-gen3/modules/modes/puzzle_solver.py:373`)
pushes boulder `(5,11)` **DOWN** from `(5,10)`. Our spec
(`ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`) says an **exhaustive** Sokoban
search proves *"the only route into the row-11 corridor requires pushing boulder `(5,11)` north"*
and that *"every alternative was searched and fails"*. Both cannot be true.

**How it was settled — two independent authorities, neither of them recall.** The decomp
(`data/maps/SeafloorCavern_Room1/map.json` via `gh api`) and, separately, our own ROM reader:
`(5,10)` and `(5,12)` are **both** `collision=0 elevation=3 'Cave'`. The boulder is legally pushable
in either direction and both leave the player on `(5,11)` with the corridor open. ⇒ the spec's
**uniqueness claim is false; the search was not exhaustive.** Then confirmed LIVE by
`--driver ch20room1`: the south push moved boulder `local_id=1` to `(5,12)` and
`calculate_path((5,11) → (11,11))` went from `PathFindingError` to `OK len=6`.

**Rejected alternatives.**
1. *Trust the spec because it is ours and newer.* Rejected — provenance is not evidence, and this
   project has already been burned by an authored note that was confident and wrong.
2. *Trust upstream wholesale and copy its code.* Rejected — upstream's second push is a bare
   `walk_one_tile("Right")`, **unbounded by its own docstring**, judging nothing. We take its
   **coordinates** and drive them through our own `strength_push`, which is bounded and verifies the
   boulder by `local_id`. ⇒ **Copy upstream's ROUTE, never upstream's CONTROL FLOW.**
3. *Re-run our own exhaustive search, fixed.* Rejected as unnecessary work: a search is only needed
   where no shipped route exists, and upstream ships one for every room on the Kyogre path.

**The general rule this establishes** (and the reason it is worth a decision entry rather than a
footnote): **grade a research note's NAMES, COORDINATES and TILE FACTS highly, and its claims of
OPTIMALITY or UNIQUENESS at zero.** That is the same split `CLAUDE.md` already prescribes for
Gemini output, arrived at independently here for a *Claude*-authored note — so it is a property of
generated research, not of one vendor.

**Consequence, carried forward:** the same spec's **Room 2** and **Room 8** (nine-push) sequences
come from the same search and are now **unaudited**. Arbitrate each against the decomp *and*
upstream's Emerald branch (`puzzle_solver.py:395-454`) **before** driving it.

---

## 2026-08-13 — an acceptance test asserts the OUTCOME, not the position you expected to see it from

**The decision.** `Ch20Room6Mode`'s `crossed` test accepts **either** "the avatar is on
`ROOM6 (4,1)`" **or** "the avatar is now in `SEAFLOOR_CAVERN_ROOM3`":

```python
crossed = (where == ("SEAFLOOR_CAVERN_ROOM6", self.ROOM6_EXIT)
           or where[0] == "SEAFLOOR_CAVERN_ROOM3")
```

**What forced it.** The driver exists to answer one question: *can the executor actually WALK a
current maze, or only plan one?* The current carried the avatar **straight through the `(4,1)`
transition** into Room 3 without stopping. A strict positional test would have printed
**`ACCEPTANCE: FAIL` over a crossing that worked perfectly** — and the natural next move would have
been to "fix" a driver that was already right.

**Why the widened test is not a weaker test.** Reaching Room 3 is a **strictly stronger** proof of
the crossing than standing on `(4,1)`: `(4,1)` is the only tile in Room 6 that reaches Room 3, so
being in Room 3 *implies* having been there. ‼ **Checked against the reviewer's objection** that
another Room 6 → Room 3 warp could launder a false positive: Room 3 has exactly three warps
(`(8,1)`→Room 8, `(9,13)`→Room 7, `(4,15)`→Room 6) and only `(4,15)` pairs with Room 6, so there is
no second door. And the phase ordering means the only code that can move us between the `in_room6`
check and the `crossed` check is the crossing call itself.

**Alternatives rejected.**
1. *Keep the strict positional test and stop the walk short of the warp.* Rejected: it would test
   our ability to halt on a specific tile inside a forced-movement chain — a **harder and
   different** question than the one being asked, and one the game may not even permit.
2. *Grade on the plan instead of the walk.* Rejected outright — that is the exact conflation
   (`a plan is not a walk`) the increment was built to break.

**The cost, stated rather than buried.** The tile-name-derived arrow-warp branch added alongside it
(`_walk_through_warp` with a direction derived from the tile's own name) **never executed and is
therefore UNTESTED**. It is bounded (240 frames, raises `BotModeError`, caught) so it cannot hang,
but it must not be described as proven.

**The general rule this establishes:** *an acceptance test names the OUTCOME it wants, not the
coordinate it expects to observe it from. When a run can legitimately overshoot the checkpoint,
a positional assertion measures the checkpoint, not the outcome.* (This project has now paid for
the inverse twice: §Ch18 passed `badge + controllable` while stranded on an island, and §Ch19
passed every completion signal from inside a living room.)

## 2026-08-14 — §Ch20 Room 8: the jam response is EXIT-AND-RE-ENTER with ONE retry, wired and fault-tested — never improvised pushes, never unbounded retries

**Decision.** `Ch20Room8Mode`'s only response to ANY failed push (or a completed sequence whose
exit path does not open) is: exit to Room 3 via the `(5,12)` arrow warp, re-enter through Room 3's
`(8,1)` door so every `FLAG_TEMP_*` boulder respawns from the map header, and retry the whole
9-push sequence exactly ONCE. A second failure is a FAIL with the recovery at least proven. The
handler is exercised by a permanent fault hook (`POKEBOT_CH20_FAULT=room8`), following the
`room1` hook precedent — and in fault mode `recovered=True` is GRADED, not just reported.

**Why.** (a) The adjudication note is explicit that a jam is recoverable by re-entry and that
improvising near `(5,3)` is how the room gets permanently sealed — the side-push stands are
occupied late in the sequence. (b) `strength_push` raises loud on a refused push; KI-34 warns the
caller must not re-enter it in a loop of its own. A hard 2-attempt cap around a world reset is
bounded twice over. (c) Room 3's trainer flags persist, so the retry costs no battle.

**Alternatives rejected.** Improvised side-pushes to free a jammed boulder (the exact hazard the
adjudication names); unbounded retry-until-solved (KI-34's shape); no retry at all (throws away a
recovery the map gives us for free and that a wild-encounter desync could someday need).

**Also decided:** the arrow-warp hold direction in the recovery is DERIVED from the live tile
name (`_cross_room6`'s rule), never hardcoded — adopted from adversarial review before the first
run; the fault run then showed the warp fires during the navigate itself, a case the hardcode
would have hit blindly. And the 9-vs-10-push adjudication (OURS, from the 2026-08-13 note) was
re-verified before driving by an independent offline simulation over our ROM + the decomp, whose
checker was itself fault-tested.

## 2026-08-14 — §Ch20 Room 9: release is gated on VAR_ROUTE128_STATE == 2, never on "looks controllable"; scene-riding presses are gated, never mashed

**Decision.** `Ch20Room9Mode` treats `VAR_ROUTE128_STATE == 2` as the ONLY release signal after
the forced warp, and rides the whole cutscene chain with three bounded, loud-on-failure
milestones (battle seen → map==ROUTE128 → var==2) instead of a single "wait until controllable".
All mid-warp state assertions (Kyogre flag, `VAR_SEAFLOOR_CAVERN_STATE`, `VAR_ROUTE128_STATE`,
position) fire at the map-change instant, where they are invariants, not completion signals.

**Why.** Decomp recon (independent agent, cited) showed Room 9''s script tail executes its
`releaseall` ON ROUTE 128, before the OnFrame scene re-locks — so there is a genuine
controllability window that is NOT the end of the chapter. A controllability-gated driver would
act inside the Steven scene. The var is written one command before the final `releaseall` and
has exactly two writers in the whole ROM (1 pre-warp, 2 at scene end), making it a clean binary.

**Alternatives rejected.** Waiting on `wait_until_truly_controllable` alone (acts in the seam);
grading on `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (set BEFORE the forced warp — reports success
from inside two nested cutscenes; the build spec called this out and the recon confirmed it);
a single global frame budget with no milestones (a stall would be unattributable).

**Also decided:** the milestone loop''s button is `A` only when `is_waiting_for_input()`, else
`B` — adopted from adversarial review before the first run (see `08-MISTAKES.md` 2026-08-14,
the museum-greeter recurrence).

## 2026-08-14 — §Ch20: losing to Archie is a VALID BRANCH the chapter must handle, not a defect a driver should prevent

**The measurement.** Three full `--driver ch20room9` runs: 2 wins, 1 loss on the Archie fight —
the ONLY stochastic element in an otherwise deterministic chain (identical milestone frame
counts across both passing runs). The party reaches Archie CHIPPED (run 3: one mon fainted,
lead at 96/135, usable=5) because no heal exists inside the cavern and Rooms 1-8 cost a grunt
fight, a forced DOUBLE, and wild encounters. A loss whiteouts to the last heal location with
the script context dead: no vars/flags written, `VAR_SEAFLOOR_CAVERN_STATE` still 0, the
trigger re-armed, all `FLAG_TEMP_*` boulders reset (they reset on every warp anyway), cavern
grunts STAY defeated. The mode generator is dropped (Manual), so a lost run leaves no RESULT —
only the `PRE-ARCHIE PARTY` telemetry line.

**Decision.** The recon DRIVER treats a loss as an honestly-reported terminal outcome (bail
loud, transcript is the record). The CHAPTER, when assembled, must treat it as a RETRY branch:
bounded N attempts (the Mossdeep Gym precedent), each retry a full re-dive of Rooms 1-8
(~25 min), plus a pre-boss readiness policy (heal/potions/party order before entering Room 9)
to push the win rate up before the retry loop is ever needed.

**Alternatives rejected.** Making the driver prevent the loss (a recon driver measures the
world, it does not fight the odds); grading the driver's PASS on winning every time (turns a
measured 1-in-3 game outcome into fake flakiness); healing mid-dungeon by state-write in the
chapter (violates faithful-play; the sanctioned fixture heal exists only in the harness driver,
documented as such).

## 2026-08-14 — USER RULING: the `#24-organicteam` gate is LIFTED (re-confirmed), and the punch list was contradicting the ruling record

**The ruling.** Asked to settle a contradiction between our own documents, the user said:
> "Yes lift the gate as I believe it will help with other progress with this bot!"

⇒ **`#24-organicteam` is NOT deferred. Building it is approved.** This CONFIRMS rather than
changes RULING 1 of 2026-08-06 (*"the `#24-organicteam` GATE IS LIFTED. Build this now"*, which
already called the 2026-08-05 deferral "reversed knowingly").

**Why this entry exists at all — a documentation defect, not a decision change.** The 2026-08-10
punch-list triage recorded the 2026-08-05 DEFERRAL as *"the live instruction"* (`03-PUNCH-LIST.md`
entry + consolidation table) **four days after the user reversed it**, and never referenced
Ruling 1. Both statements then sat in the docs simultaneously. Measured cost: on 2026-08-14 the
contradiction misled THIS agent twice inside one conversation — first into telling the user their
own directive needed a deferral lift it had already been given, then into an agent briefing that
carried the same error onward. **A deferral and its reversal must never both read as live.**

**Scope note, recorded because two agents read it differently.** One reading: Ruling 1's heading
sits under *"`#24-roster`: USER RULINGS"* and Ruling 2 the same day says *"round one does NOT
change catch policy"*, so only roster infrastructure was approved. The other (and the plain text
of Ruling 1): the deferral was reversed outright. **The user's 2026-08-14 ruling above settles it
in favour of the broad reading** — the gate is lifted, full stop. Ruling 2's *"catch policy gets
its own round on a clean baseline"* is not contradicted by this: the user is now CALLING that
round (see the catch-policy discussion opened 2026-08-14).

**Still standing, untouched by this ruling:** `#24-rarepredicate` remains NOT READY (its dataset
does not reproduce and its warp-depth rule fails Bagon, its own motivating example), so the
"rare" leg of any catch policy cannot be built on it yet; and the 2026-07-31 *"catch every unseen
species except when doing so would block progress"* ruling remains the governing definition of
cheap-catching, with `resource_blocker()` as its pinned predicate.

## 2026-08-14 — USER RULINGS: the LIVING-DEX goal, resumable runs, and a sanctioned trade-evolution deviation

Given during the catch-policy discussion opened the same day. Recorded verbatim where the wording
carries the intent, because two of these change what "faithful" means in this project.

### RULING A — "catch them all" means a LIVING DEX, and it serves TWO goals at once
> "I want it to be like the living-dex where its every species being caught and logged in the
> pokedex (or through evolution to unlock them in the pokedex/mark them as caught works too…)
> the idea is to kill 2 birds with 1 stone: Bot captures potential future counters AND chips at
> completing the pokedex at the same time, more efficient this way."

⇒ The objective is **breadth (one of every species, dex-credited) with depth as the payoff**
(the same catches supply counters and HM slaves). ✅ **This ALIGNS with the code that already
exists** rather than fighting it: `_should_catch` is already new-species-only, so "don't catch
duplicates" is both the dex rule and the ball-economy rule. Evolution counting for dex credit is
the user's explicit position, and it is cheaper than catching every stage.

### RULING B — per-run dex filling (option A) **AND** resumable long-lived saves (option B)
> "currently we are using the reset feature for testing from fresh saves… the goal would be
> every run (Option A) but since the goal is to have the bot have the option through my
> intervention to pick up where it left off… the idea would be to get it to also be able to
> continue where it left off in the event that the bot gets turned off during sudden power loss
> OR I turn it off for a period of time and turn it back on to have it continue (So option A
> and B maybe?)"

⇒ ‼ **These are TWO SEPARATE FEATURES and must not be conflated.** (1) Dex-filling is a
**per-run behaviour** — every fresh run collects as it plays. (2) "Pick up where it left off" is
a **RESUME/DURABILITY capability** (a named profile's save resumed after power loss or a
deliberate shutdown, at the user's intervention), which is *orthogonal to the dex* and applies to
the whole bot. Treating (2) as "a different dex model" would build the wrong thing.
⚠ The reset gate itself ("resets once it completes the game as we logged") is explicitly marked
by the user as **to be revisited and refined later** — do not harden it now.

### RULING C — ⛔ A SANCTIONED DEVIATION FROM FAITHFUL PLAY: trade evolutions may be forced
> "I think we can bend the rules to allow it to evolve trade evolutions in some way (we can
> determine this later by adding our own level the pokemon must be at to enable the auto evolve
> for trade evolution lock 'hack' which breaks organic/faithful gameplay but as far as I am
> aware there would be no other way around it)"

⇒ **APPROVED IN PRINCIPLE, PARAMETERS DEFERRED.** The user is correct that there is no faithful
solo path: Gen 3 trade evolutions require a second console/cartridge, so a living dex is
otherwise capped short by Alakazam/Machamp/Golem/Gengar and friends.
‼ **This is a REAL deviation from the north star's "faithful to natural gameplay" rule and must
be documented as one, not slipped in.** It fits the project's existing framework only as the
sanctioned last-resort shape: *a state-write is allowed when the faithful path is impossible and
it reproduces vanilla's EXACT end-state* — forcing the evolution does reproduce exactly what a
traded-and-returned Pokémon would be. Requirements when built: (a) a user-chosen LEVEL threshold
gates it (the user's own design), (b) it is FLAGGED and OFF by default, registered in
`29-DISABLED-FEATURES-REGISTRY.md`, (c) the run log states plainly that a non-faithful evolution
was performed, so no future measurement mistakes it for organic play.
**Deferred:** the level threshold, which species are in scope, and whether it applies outside
dex-completion contexts.

### RULING D — party accounting must count SLOTS, not the bot's beliefs (user-designed)
Prompted by the user identifying the real party-state hazard in their failing run: **no egg, but
a NINJASK and a SHEDINJA** — i.e. a Nincada evolution SPAWNED a sixth party member with no
catch, no menu and no bot action.
> "maybe we robustly enhance the Party detection/count logic so it counts filled spaces vs empty
> spaces (not whether it logs the pokemon as caught or moved to the party, that is still
> valuable for knowing whats in its party when its not looking but should be a separate function
> if this makes sense)"

⇒ **Split the concern:** (1) an AUTHORITATIVE "how many slots are filled vs empty" reader taken
from live game state, used by every fullness/space decision; (2) a SEPARATE bookkeeping function
for "what the bot believes/tracked" (still valuable — it is how the bot knows what it has when it
is not looking). ‼ **This is the same failure family the project has logged repeatedly** (state
sampled from a moving frame of reference; assert identity, never a count) and it explains a class
of bug wider than Shedinja: ANY party change the bot did not initiate desynchronises a derived
count. Under investigation as of this entry; the egg-blind `withdraw_from_box` test
(`pc_trip.py:429-438`) is a known instance of exactly this shape.

## 2026-08-14 — KI-78 Stage 1: identity is `(personality, species)`, and an evolved-since-capture mon is RE-RESOLVED rather than raising — except when it is ambiguous

**Decision.** `Party.get_index_for_pokemon` and `PokemonStorage.contains_pokemon` now match on
`(personality, species)` through one shared predicate `modules/pokemon.same_pokemon`.
`get_slot_for_pokemon` already used that key and is refactored onto the same predicate so the trio
cannot drift apart again. ⛔ `counter_hunt.py`'s PID sets and the protected/hunted PID sets are
DELIBERATELY excluded — see below.

**Why a composite key at all.** `CreateShedinja` copies the Ninjask with a memcpy and never
rewrites the personality, so the twins are PID-identical for life and the spawned twin always sits
in the LATER slot. A first-PID-match scan therefore resolved a Shedinja request to the Ninjask —
on a lookup whose callers are DEPOSIT and **RELEASE (permanent)**.

### The real decision: R6 — what to do when the species disagrees

The composite key introduces a failure mode PID-only did not have: a mon that EVOLVES between the
caller capturing its object and the lookup running no longer matches. Three options were live:

1. **Always RAISE on a species mismatch.** Rejected as the blanket rule: it converts flows that
   used to work (a mon evolved en route; the caller still means *that* mon) into hard aborts, and
   the callers largely do not catch `RuntimeError`. Trading a wrong-target bug for a run-killer is
   not obviously a win, and this project has twice deleted winning behaviour by counting only
   failures.
2. **Fall back to the first PID match.** ⛔ Rejected outright — that IS the original bug.
3. ✅ **CHOSEN — split on ambiguity.** Exactly ONE mon carrying that PID ⇒ unambiguous; it evolved;
   re-resolve to it and report LOUD. TWO OR MORE PID hits with no species match ⇒ genuinely
   ambiguous ⇒ **RAISE**, because the caller may be about to destroy something and a guess is not
   recoverable. The asymmetry is deliberate: *recover where the answer is unique, refuse where it
   is not.*

**Cost, stated rather than buried.** R6 is **unexercised by any live caller today** — every current
caller re-captures its target immediately before entering the PC menu, with no encounter-capable
movement in between. It is defensive coding proven only by the gate, and it should not be described
as battle-tested.

### Why `counter_hunt.py` must KEEP the PID-only semantics

`catch_confirmed()` (shipped hours earlier the same day) works *because* the twins share a PID: a
Shedinja spawn cannot look like a NEW identity, which is the correct answer for "did this hunt
catch something?". Adding species there would reintroduce the bug that function was written to fix.
The protected/hunted PID sets are the same shape — they mean "do not touch anything in this
family", so a twin SHOULD inherit its sibling's protection. **Widening is safe there; narrowing is
not.** This is recorded at the definition site of `same_pokemon` as well, so a future consistency
sweep does not "tidy" it back.

**Alternatives rejected for the KEY itself:** `(personality, nickname)` — the user's proposal, and
the objection raised against it (a stale nickname after evolution) was **refuted** by the decomp;
it would have worked for this pair. Species wins because the game keeps default nickname and
species in lockstep, so the name adds no discriminating power while bringing its own failure modes
(eggs share one nickname, it changes at hatch, trades ship preset names, foreign-language mons
never rename) — and because `starter_nickname` is already wired end to end, one hard-coded "No"
away from making that field arbitrary. `(personality, party_index)` — rejected: the index is the
unstable thing the identity key exists to replace.

## 2026-08-14 — Party accounting Stage 0: observe from INSIDE the reader, ship no consumer, and say which classes are sampled

**Decision.** Implement RULING D as a **measurement-only Stage 0**: readers plus a divergence log,
**zero call sites re-pointed**, with the observation hung off `get_party()`'s own branches.

**Why observe from inside `get_party()` rather than from a caller or a polling loop.** The
divergence IS the compaction: `get_party()` reads A, loops it, and `continue`s the near-empty
slots. At that exact branch both numbers are already in hand, so a HOLE is observed **exhaustively
and at zero extra memory reads**. Any external observer would have to re-read memory on its own
cadence and would therefore SAMPLE the one class we can otherwise get for free — and would sample
it from a different frame of reference than the reader it is measuring, which is the
"state sampled from a moving frame" family this project has logged repeatedly.

**Why STALE is sampled anyway, and why that is written into the output.** An occupied slot at or
past A cannot be seen without reading slots `get_party()` never touches. Rejected: scanning all six
every recompute (600 extra bytes ~60x/second for a class we have never once observed). Chosen:
1-in-300, **with the sample count printed beside the result**. ⛔ The alternative explicitly refused
is printing a bare `STALE: 0` — that is a claim the instrument may not have been able to falsify,
and believing exactly that kind of negative is item 4 of the playbook's pre-flight.

**Why STALE is measured at all, given the game ignores those bytes.** Because the obvious way to
write the "filled vs empty spaces" reader the user asked for is to count non-empty slots — and that
reader would COUNT them and be wrong. Measuring how often they exist is what justifies making A the
capacity authority instead. `occupied_count` is exported for this and carries a warning in its
docstring saying it is not a party size.

**Why no call site was wired, when 35 of them are capacity-shaped and arguably wrong today.**
Rejected: migrate them now. The honest state is that **nobody has ever measured whether A differs
from B in a real run** — the first run to look reported 25,523 recomputes and zero divergences. A
migration justified by an unmeasured hazard could only be graded on "nothing broke", which is not a
result. Stage 1 is gated on accumulating summaries from long runs.
‼ And the migration is **not symmetric**: index/menu-cursor sites must stay on B forever, because
if A > B an index from A is out of range for the list that exists — surfacing mid-battle, in the
faint chooser. "Use the authoritative number everywhere" would be an actively harmful tidy-up.

**Why C (the belief ledger) is not in Stage 0.** The user called it valuable and it is. But a
ledger disagreeing with the game is only diagnosable once the two GAME numbers can be told apart;
building all three at once would mean debugging a three-way disagreement with no trusted leg.

**Alternatives rejected for the observer's failure behaviour.** Letting it raise — rejected: every
party read in the bot goes through here. Swallowing quietly — ⛔ rejected outright: a silently
broken observer reports "no divergence" forever and the negative gets believed, which is the exact
shape of five entries in `08-MISTAKES.md`. **Chosen: swallow, but announce ONCE and loudly**, and
have the gate assert the announcement fires.

## 2026-08-15 — `party_accounting_ledger.jsonl` IS COMMITTED, not gitignored (and harness logs stay ignored)

**Decision.** The (P3b) measurement ledger is tracked in git. `tools/story-dev/.gitignore` ignores
`*.log`, so the harness transcripts it was originally read from are NOT shared between machines —
and the ledger deliberately breaks that pattern.

**Why.** ‼ **This project is worked on from multiple computers** (the standing sync directive in
`CLAUDE.md` exists for exactly that). (P3b)'s criterion is *cumulative* — "≥5 drives across ≥3
drivers AND ≥250,000 recomputes". A per-machine ledger would make that criterion depend on which
laptop happened to run the drives, and a machine that had run four drives would silently start
again from zero. Committing it makes the population the PROJECT's, not the machine's.
Cost: a few hundred bytes per drive, append-only, human-readable, one JSON object per line.

**Alternatives rejected.** *Gitignore it like the logs* — that is what makes the criterion
un-earnable across machines, and it is the shape of the bug that prompted the ledger in the first
place (a data source that does not survive). *Aggregate into a single summary file the harness
rewrites* — a read-modify-write on a shared file is a merge conflict per drive AND reintroduces the
round-trip corruption hazard logged twice this month; append-only JSONL merges cleanly because two
machines' drives are independent lines.

**The sharp edge, accepted knowingly.** A drive killed mid-append leaves a truncated last line, and
the collector REFUSES the whole population rather than skipping the row — silently dropping a row
would bias a count whose entire purpose is to say "there is enough evidence now". ⇒ the failure
message now names the line and states the repair (delete that line, re-run that driver; never
hand-write a row). *A conservative check with an obvious repair is fine; one without is a blocker.*

**What is NOT in the ledger, on purpose.** No timestamps beyond the local wall clock, no machine
identity, no save hash. If cross-machine attribution ever matters, add it then — the file is
append-only and a new key is backward-compatible, whereas a schema nobody needed is dead weight.

## 2026-08-15 — USER APPROVED TWO PROMOTIONS, and the second established the evidence bar for a BEHAVIOUR promotion

**The rulings.** The user said "promote" twice this session, in response to two separate asks:
1. **`modules/story/counter_hunt.py`** — a COMMENT-ONLY correction (the "Winona needs …/Electric"
   error). Restore point `restore/2026-08-15-pre-promotion-counterhunt-comment`.
2. **`modules/story/pc_trip.py`** — the **KI-79 fix, a BEHAVIOUR change**: the PC withdraw stops
   announcing an identity from `len(get_party())` and verifies `(personality_value, species)` plus
   `contains_pokemon`. Restore point `restore/2026-08-15-pre-promotion-ki79-pctrip`.

**Why they were asked separately, and why that stands as the rule.** The standing directive is that
promotion is the USER's call. A comment-only change and a behaviour change are not the same ask:
the first cannot alter what the bot does, the second can. The second approval was therefore
requested explicitly rather than inferred from the first — even in a session where the user had
twice said "proceed autonomously". ⇒ **Blanket autonomy does not extend to promoting a behaviour
change; ask again.**

**‼ THE METHODOLOGY DECISION THIS FORCED — the one worth keeping.** For the behaviour promotion,
`promote.py`'s "1/1 byte-identical, drift 0" was **explicitly rejected as sufficient evidence**,
because a byte-compare proves a file was COPIED and says nothing about which branch EXECUTES.
The accepted standard is a **THREE-POINT A/B using the feature's own fault hook**:

| # | run | result | proves |
|---|---|---|---|
| 1 | **BEFORE** the copy, fault var set | PASS (inert) | the hook is ABSENT in custom |
| 2 | **AFTER**, identical command | FAIL (`‼ THE WITHDRAW DID NOT LAND`) | **the new code is LIVE in custom** |
| 3 | **AFTER**, unfaulted | PASS | no regression on the happy path |

‼ **Run 1 is unrepeatable** — it exists only before the copy — so it must be run and COMMITTED
first. Transcripts live under `tools/story-dev/evidence/`.
⚠ **Alternatives rejected:** (a) byte-compare alone — see above; (b) a diff review — reads intent,
not execution; (c) trusting the earlier comment-only precedent, which had SKIPPED the drive on the
reasoning that a comment cannot change behaviour. That reasoning is sound for comments and does not
generalise, so it was not reused.

**Also ruled, implicitly, by the same round:** `promote.py` REFUSING a dirty tree is the tool
working, not an obstacle. The baseline evidence was committed first and the promotion re-run from
clean, rather than routing around the refusal (e.g. with an escape hatch).

## 2026-08-15 — KI-80's repro is THREE arms terminated by a tripwire, not a two-arm A/B run to completion

**Decision 1 — THREE arms, not two.** `--driver ki80ladder` runs `NOGRASS`, `GRASS_FODDER`
(Route 102, `wild_max` 4) and `GRASS_STRONG` (Route 119, `wild_max` 27) on one fixture.
*Rationale:* `grass_is_fodder` is a DISJUNCTION — `("grass" not in cfg) or (wild_max + 8 < team_max)`
— so a two-arm A/B cannot tell whether the ladder vanished because a key APPEARED or because the
ARITHMETIC flipped. Only the second is the defect. `GRASS_FODDER` shows a patch that IS fodder keeps
the machinery, which turns the finding from "adding a key breaks it" into the actual conflation.
*Rejected:* the two-arm version — cheaper, and it would have supported a wrong causal story.

**Decision 2 — terminate each arm AT its discriminator, from inside the console proxy.**
*Rationale:* forced by measurement. The obvious design ("call `next()` once, read which line
printed") was REFUTED: `story_mode.py:1949`'s print is not the end of the arm, and one `next()` runs
on into `:2087 train_team(...)`, which calls `set_swap_train(True)` and `press_button("Start")`
**before its first yield**. A tripwire that raises from the proxy unwinds `_prepare_for_fight` at
`:1948`, so `train_team` is never reached. *Rejected:* (a) `gen.close()` alone — it runs too late,
the button is already queued; (b) widening the invariance snapshot and tolerating the mutation —
that detects the damage instead of preventing it, and the snapshot cannot see a module global or a
pending input anyway. Both are kept as belt-and-braces, neither as the mechanism.
*Cost accepted:* the arm proves the gate is REACHED and nothing about what the ladder then does.
Stated as a scope limit everywhere it is reported, rather than left to be discovered.

**Decision 3 — the ladder spy REPLACES the ladder body; the hopeless observer DELEGATES.**
*Rationale:* the two have different jobs. `_counter_ladder` is downstream of the gate under test and
travels, so substituting it removes risk without touching the subject. `_boss_plan_is_hopeless` is
ON the path and its verdict is part of what we are measuring, so it must be the REAL predicate —
the observer calls it and only records. *Rejected:* stubbing the predicate to force `hopeless=True`,
which would have made the fixture's condition-7 property untested and the run meaningless.

**Decision 4 — the anti-vacuity check is computed from the RUNNING game and BLOCKS the verdict.**
*Rationale:* this project has twice specified an A/B whose arms were identical. The driver measures
`team_max` and both maps' `wild_max` through production's own readers and refuses to grade unless
`wild119 + 8 >= team_max` AND `wild102 + 8 < team_max`. *Proven, not asserted:* against
`ch13_fortree_door.ss1` it FAILS with `THE A/B WOULD BE VACUOUS` and all three arms return `LADDER`.
*Rejected:* trusting the `team_max` table in the docs — which is exactly how the vacuous fixture got
prescribed in the first place.

**Decision 5 — the fix's expectation flips by env var (`POKEBOT_KI80_DECOUPLED`), so ONE driver is
both the BEFORE and the AFTER.** *Rationale:* KI-80 requires the repro driven before AND after, and
two separate drivers would drift apart. *Rejected:* a second driver written after the fix — it could
not be run against the pre-fix code at all, which is the half that cannot be redone later.

## 2026-08-16 — KI-80's decoupling: the MINIMAL split, and the two things deliberately NOT done

**Decision 1 — remove `grass_is_fodder` from the ladder's gate, and put `boss_mode` behind its own
`if grass_is_fodder:`.** `story_mode.py:1901` becomes `if boss_teaches:`, and `:1925`'s
`boss_mode = True` (plus its target bump and message) is nested under a fresh `grass_is_fodder`
test. *Rationale:* the two halves of the old boolean answer different questions — *"is this fight
hopeless"* (the ladder's business) and *"is the local patch too weak to train on"* (boss-training
mode's business). *Rejected:* the one-line version that simply deletes `grass_is_fodder and` from
`:1901`. **MEASURED, not feared:** that version makes the three-arm suite report
`ACCEPTANCE: PASS` while KI-23's mirror regression lands — arm 4 catches it with
`OUTCOME=BOSS_TRAINING_MODE`.

**⛔ THE EDIT WAS MADE NET-ZERO ON LINE COUNT** (13 lines changed, 13 added) by tightening an
adjacent comment block to pay for the new `if`. Verified after: `grass_is_fodder` still `:1899`,
the `elif` still `:1932`, `not boss_mode` still `:1937`, the escalation message still `:1949`,
`winona_fight` still `:3532`. *Rationale:* `06`/`07`/`08` are append-only and full of
`story_mode.py:NNNN` citations that may not be rewritten to follow a shift.

**BLAST RADIUS — the ARITHMETIC is measured; the resulting BEHAVIOUR is INFERRED. Read the
distinction, because it is the honest limit of this table.** Every `wild_max` below was read
from the live ROM and every band from the cfg, so which side of `wild_max + 8 < team_max` each
boss falls on is **measured**. That those bosses then behave differently is **inferred from
shared code paths** — only Winona's fixtures were actually DRIVEN. ‼ No Brawly/Roxanne/Wattson
run exists. The inference is strong (`_boss_plan_is_hopeless` and `_counter_ladder` are the
same code for every boss, and are driven for Winona) but it is not a measurement, and an
adversarial reviewer was right to flag it. Only bosses with BOTH a `grass` key and
`ace_types` can change behaviour (no `ace_types` short-circuits `_boss_plan_is_hopeless` to
*not hopeless*, so the ladder can never fire):

| boss | grass map | `wild_max` | band | effect of this fix |
|---|---|---|---|---|
| **Brawly** | GRANITE_CAVE_1F | 10 | (14,16) | ⚠ **FULLY changed** — never fodder, so he had NO counter machinery at any level in his band |
| **Roxanne** | ROUTE116 | 8 | (13,17) | ⚠ changed at `team_max` **13-16** |
| **Wattson** | ROUTE117 | 14 | (20,24) | ⚠ changed at `team_max` **20-22** |
| Norman | ROUTE102 | 4 | (27,31) | ✅ unchanged — always fodder already (his patch is the FODDER TRIGGER *by design*) |
| Rival (Rustboro) | ROUTE116 | 8 | (16,19) | ✅ unaffected — **no `ace_types`**, so the ladder can never fire for it |
| Winona / Flannery / Rival110 | *(none)* | — | — | ✅ unchanged — no `grass` key, so already on the ladder path |

⇒ **the fix gives Brawly, Roxanne and Wattson the counter machinery they silently lacked**, which is
exactly KI-80. ‼ It also means a hopeless diagnosis at those three can now end a run with KI-23's
honest `BotModeError` instead of grinding — **that is the intended behaviour** (KI-23 measured the
grinding path at 198 attempts / 41 losses / 41 whiteouts without converging), but it is a real
expansion of where that stop can occur and is recorded here so it is not a surprise later.

**Decision 2 — `boss_teaches` STAYS on the gate, and that is deliberate.** KI-80's text ("gated on
*is this fight hopeless*, which `_boss_plan_is_hopeless` already answers alone") can be read as
removing both conjuncts. *Rejected for now, on evidence grounds:* **no arm can discriminate it** —
all four seed `kos = 1`, so `boss_teaches` is True in every test we have. Shipping it would be
changing behaviour we cannot observe. ‼ The open question is real and worth answering: a party that
KOs **nothing** and has no type answer is the *most* hopeless case, and it currently gets the
"boss can't teach us" message and plain escalation rather than a counter hunt. **Filed as a tracked
residual, not silently dropped.**

**Decision 3 — the `elif` at `:1932` is left untouched.** *Rationale:* its firing condition is
provably unchanged. It reads `grass_is_fodder and recent_kos and not boss_teaches`; previously it
was reached when `not (grass_is_fodder and boss_teaches)`, now when `not boss_teaches` — and in both
cases the guard's own `not boss_teaches` plus `grass_is_fodder` select the identical set of states.
Its body is `console.print` only. *Rejected:* "tidying" the now-redundant `not boss_teaches`
conjunct — redundancy that documents the reachable state is cheaper than a behaviour question.

**Not promoted.** This is a BEHAVIOUR change and it lands in `sandbox-pokebot` only. The user's
2026-08-16 "promote" ruling covered the comment-only correction, which is done; a behaviour change
needs its own approval, and when it comes it needs a **three-point A/B against `--build custom`**
(`POKEBOT_KI80_DECOUPLED=1` must go FAIL→PASS there), because a byte-compare only proves a copy.

## 2026-08-16 — a SELF-RETIRED gate is LEFT retired, not deleted

**Decision.** `repro_boss_grass_gate.py` (suite #24) detected that the coupling it guarded is gone
and printed *"this gate now enforces nothing … RETIRE THIS GATE."* **It stays in the suite, and its
own message has been rewritten to say why.**

*Rationale:* the gate re-derives the coupling **from the live AST on every run**. It is inert today,
but it is **self-ARMING as well as self-retiring** — if anyone ever re-introduces the coupling by a
revert, a bad merge, or by "simplifying" the two-level split back into one boolean, the gate starts
enforcing again **on its own, for free, in 0.1s**. Deleting it buys nothing (0.1s of suite time) and
removes exactly the net that would catch a regression of the defect we just spent a session fixing.

*Rejected:* following the gate's own advice and removing it, plus dropping the suite to 23. That
advice was written when the coupling still stood, and it assumed a retired gate is dead weight. A
gate whose ARMING CONDITION is computed rather than hardcoded is not dead weight — it is a latch.

*Rejected also:* leaving the "RETIRE THIS GATE" line in place and merely noting the ruling in the
docs. The next agent reads the GATE'S OUTPUT, not this log, at the moment they are deciding — so the
superseded advice had to be replaced at the point of use, with the old wording quoted as superseded
so the change reads as deliberate rather than as drift.

‼ **Generalised rule worth reusing:** *when a gate's guard condition is derived at runtime, retiring
it means letting it go quiet — never deleting it. Delete only gates whose arming condition is
hardcoded and therefore cannot come back.*

## 2026-08-16 — unique harness log names: unbounded (gitignored) growth accepted over ANY retention cap

**Decision.** `story_harness.py`'s default log becomes
`harness_<build>_<driver>_<timestamp>_<pid>.log`, one file per run, **with no rotation, no cleanup
and no cap.** Raised by an adversarial reviewer as an unnamed tradeoff, and it is one: the OLD
scheme self-capped at **two** files per build precisely BECAUSE it overwrote them.

*Rationale, with the numbers measured rather than guessed:* `tools/story-dev/` already holds **229
`.log` files totalling 26 MB** — an average of ~113 KB, and the two `ki80ladder` transcripts this
change produced are **6.2 KB and 5.3 KB**. `*.log` is gitignored (`tools/story-dev/.gitignore:2`),
so nothing reaches the repository. Months of work have produced 26 MB. That is not a cost worth
engineering against.

*Rejected — and this is the substantive half: an age-based retention sweep* ("delete logs older
than N days"). ⛔ **Auto-deleting transcripts is the SAME defect this change exists to fix, only
slower.** The bug was an instrument silently destroying evidence; a cleanup job is an instrument
silently destroying evidence on a timer. The 2026-08-15 Tier 1 kick-back happened because a
transcript that proved a TRUE claim no longer existed — a retention policy would reproduce that
outcome and be harder to notice, because nothing would be overwritten in front of you.
‼ If disk ever genuinely matters, the correct move is a MANUAL, reviewed sweep — never an automatic
one. Deleting evidence should require a human deciding to delete evidence.

*Rejected also:* keeping a stable `harness_<build>-latest.log` alongside the unique file, as a
convenience for the "tail the flushed log while it hangs" workflow. It reintroduces a fixed name
that two concurrent runs would fight over, and it is unnecessary: **the run prints its own path as
its first line**, which serves that workflow exactly and cannot go stale.

⇒ **Anything you intend to CITE belongs in `evidence/`, committed.** A gitignored log is a working
artifact, not evidence — that rule predates this change and is why it is safe to be relaxed about
the logs themselves.

## 2026-08-16 — USER RULING: how production reacts to a failed PC withdraw

**The ruling, in the user's words (2026-08-16):** *"how to react to a failed pc withdraw: reattempt
but after intelligently processing the data (text boxes it reads to determine why it failed)"*.

**What it settles.** `#24-orphans` item (1) — the highest-cost residual of KI-79 — was blocked
because *"react HOW?"* was undefined everywhere in the docs, and inventing a policy would have been
building behaviour unilaterally. It is no longer blocked. The instrumentation half was already
specified; this supplies the missing half.

**What it requires, read carefully — it is TWO things, and the second is the load-bearing one:**
1. **Reattempt** rather than tolerate the failure silently (today's behaviour: the message is
   honest, and nothing acts on it).
2. ⛔ **But NOT a blind retry.** The reattempt must be *informed by a DIAGNOSIS read from the
   on-screen text*. ‼ **A retry that repeats the same failing action without knowing why is the
   PING-PONG pattern this project has already been burned by twice** — `#24-movelearn-recovery`'s
   8-frame A/B ping-pong, and the loop traced in KI-65's recon. The ruling's *"after intelligently
   processing"* is precisely what separates a fix from that failure.

**Constraints this project's own rules impose on any implementation, recorded now so they are not
re-litigated later:**
* ⛔ **BOUND THE RETRY.** "Never hang / never silently derail" is a standing directive. An
  unbounded reattempt is worse than the current silent tolerance, because it converts a visible
  wrong outcome into a stall.
* ⛔ **AN UNKNOWN REASON MUST NOT RETRY.** If the text does not match a known cause, the honest
  action is to stop loudly, not to guess. *Absence of a recognised reason is not evidence that a
  retry will help* — and this project has been caught by absence-as-signal repeatedly.
* ⛔ **THE REASON MUST BE READ, NOT ASSUMED.** The ruling says *text boxes it reads*. A reason
  inferred from internal state rather than from what the game SHOWED is the same class of error as
  `pc_trip.py`'s original bug — announcing an identity derived from a COUNT.
* ‼ **Different reasons imply different actions**, and some imply NOT retrying at all (a genuinely
  empty box, or a Pokémon that is not there, cannot be fixed by trying again).

**Not yet decided, and deliberately left open:** the reason taxonomy itself, the retry bound, and
which reasons are retryable. Those follow from measurement — what the game actually prints — not
from preference. Recon is in flight; the design will be recorded here before any code lands.

## 2026-08-16 — DESIGN for the failed-PC-withdraw reaction: FOUR PREREQUISITES BEFORE ANY RETRY

Follows the user ruling above. Recon (2026-08-16) changed the shape of this work substantially, so
the design is recorded before code, and it is **phased** — because a retry added today would
amplify four existing defects rather than fix one.

### ⛔⛔ THE BLOCKER: THE TEXT THE RULING DEPENDS ON IS NOT WHERE ANY EXISTING READER LOOKS

The ruling says *"text boxes it reads"*. ‼ **The Storage System does NOT use `gStringVar4` or
`gDisplayedStringBattle`** — every text reader in this repo reads one of those. PC messages go to
`sStorage->messageText` (`u8 messageText[40]` inside a **heap-allocated** struct;
`pokemon_storage_system.c:4273-4312`, struct at `:403/:540`). Our symbol table has only the POINTER
(`sStorage` at `02039d08`). ⇒ **the offset of `messageText` within that struct is not known anywhere
in this repo and MUST BE MEASURED.** The technique is established — `pc_interaction.py:135-182`
already reads other fields of that same struct by hand-derived offsets (`+0xC74`, `+0x6FA`,
`+0x20A0`) — but ⛔ **the number must not be guessed.** A robust alternative needing no offset:
dump a window of the struct and `bytes.find()` the canonical ROM bytes inside it.

**⇒ Until that offset is measured, every failure classifies as UNKNOWN, and UNKNOWN must not retry.
The feature would ship INERT.** Measuring it is therefore prerequisite 0, not an optimisation.

### ✅ AND THE STRINGS ARE ALREADY VERIFIED — DO NOT HARDCODE ENGLISH

The refusal strings were cross-checked against **our own committed symbol table's byte sizes**, and
every one matches `len(text)+1`: `gText_YourPartysFull` `"Your party's full!"` (0x13),
`gText_BoxIsFull2` `"The BOX is full."` (0x11), `gText_ThatsYourLastPkmn`
`"That's your last POKéMON!"` (0x1a), `gText_YouCantReleaseAnEgg` (0x1a), `gText_PartyFull` (0x14).
⇒ compare **ROM bytes vs the live buffer**, exactly as `menu_parsers.py:357` does
(`read_symbol("sText_UseNextPkmn") in read_symbol("gDisplayedStringBattle")`). That is
language-independent and cannot drift from the ROM.
❌ **Correction to a Gemini research note in this repo:** *"There's only one POKéMON with you!"*
**does not exist in Emerald.** The real refusal is `gText_ThatsYourLastPkmn`. (Which is the standing
rule about those notes, demonstrated again.)

### ⛔ FOUR PREREQUISITES — a retry added before these AMPLIFIES them

1. **`withdraw_from_box:432-433` counts `alive` EXCLUDING EGGS, and that is a live latent bug.**
   Its own sibling `deposit_one_dead_weight._occupied` (`pc_trip.py:248-263`) documents this exact
   exclusion as *"a REAL bug (found by adversarial review, 2026-08-13)"* — **an egg occupies a
   physical party slot** — and was fixed. `withdraw_from_box` never got that fix. On **5 mons + 1
   egg**: `len(alive) == 5`, the make-room block is SKIPPED, and `pc_interaction.py:418` (which
   counts the egg) then raises. ‼ **A retry over this ping-pongs forever** — precisely what the
   ruling forbids.
2. **`interact_with_pc` contains UNBOUNDED `while … press A` loops** (`pc_interaction.py:424-433`,
   and four more at `:466-492`, `:332-344`, `:363-376`). Per the decomp, `Task_WithdrawMon` on a
   full party sets `state = 1` and **never reaches the state 4 that loop waits for**
   (`pokemon_storage_system.c:2798-2818`). ⇒ **wrapping a retry around an unbounded wait multiplies
   a hang; it does not recover from one.** *(The loop's behaviour under repeated A is INFERENCE from
   the decomp, not observed — but "no bound + a state the game may never reach" is enough.)*
3. **The capacity guard uses the wrong quantity.** `pc_interaction.py:418` tests `get_party_size()`
   = **B**, while the game uses **A** (`CalculatePlayerPartyCount()`), and `pokemon_party.py:184-193`
   says outright that capacity questions must use A. With a **HOLE** (A=6, B=5 — the divergence
   `collect_party_accounting.py` has already OBSERVED, 30x in `boxcounter2`) the bot proceeds and the
   GAME refuses. ‼ **This is the case that proves the ruling's second clause: the diagnosis must
   change the ACTION (deposit), not repeat it.**
4. **`withdraw_from_box`'s blanket `except Exception` has no `StoryAbort` guard**, so **a whiteout
   during a PC visit is being LAUNDERED today.** Both retry precedents in this codebase guard it
   explicitly (`space_center.py:962-977`, `mossdeep_gym.py:534-551`: `except StoryAbort: raise` PLUS
   `reraise_if_aborting(error)`). A retry loop without that would hammer a dead run.

### THE DESIGN (to build once the prerequisites are done)

* **A pure classifier, OUTSIDE the generator:** `classify_withdraw_failure(buf) -> (CODE, retryable,
  detail)`. House precedent is explicit — `counter_withdraw_outcome`'s docstring says *"logic that
  decides an outcome must be reachable by a test"*. Codes in `party_accounting.py`'s register (SHORT
  ALL-CAPS, one per decomp message): `PARTY_FULL`, `BOX_FULL`, `LAST_POKEMON`, `CANT_RELEASE_EGG`,
  `MAIL_HELD`, `HOLDING_MON`, `UNKNOWN`.
* **`withdraw_from_box` returns a verdict** `(ok, CODE, detail)` instead of `None`. Its ONE caller is
  `higher_level_actions.py:344`, which discards it today.
* **Retry policy — bounded, reason-driven, and NOT uniform:** `PARTY_FULL` ⇒ **deposit, then retry**
  (the action differs); `BOX_FULL`/`LAST_POKEMON`/`CANT_RELEASE_EGG`/`MAIL_HELD` ⇒ **do NOT retry**,
  report; `UNKNOWN` ⇒ **do NOT retry**, report loudly. House idiom: `for attempt in range(1, 4)`,
  accumulate `attempts: list[str]`, re-read reality every pass, and report exhaustion with **every**
  reason joined by `" | "` — never a bare count (`space_center.py:953-989`, `roster.py:169-249`).
* ⛔ **Make room AT MOST ONCE across all attempts.** Re-running the make-room deposit each pass
  thins the team, which is the measured `#24-pc` regression (~1 mon/run, ~19 funnel points).
* ⛔ **Yield before re-reading.** Party and storage are cached PER FRAME (`pc_trip.py:499-501`), so a
  same-frame retry re-reads pre-withdraw state and the verification becomes the new false negative.
* ✅ **A retry after the honest-failure path is CHEAP:** `interact_with_pc` ends with
  `_close_pc_menu` + `wait_for_player_avatar_to_be_controllable`, so the avatar is already on the PC
  tile facing Up and controllable. After an EXCEPTION path it may be mid-menu — so a retry must
  first do `roster.py:239-248`'s cleanup (press B ~12x, ride out the scene, re-plan from reality).
* ⛔ **Retries live INSIDE the existing `try` at `higher_level_actions.py:332` and BEFORE the exit
  walk at `:350`** — after that the bot has left the PC. And the budget must stay small: the heal is
  a piggyback, and `early_game.py:320-325` records 14,400 frames of retry churn letting the 18k
  global watchdog kill two otherwise-healthy runs.

## 2026-08-16 — `withdraw_from_box`'s "Never raises" contract is narrowed, not abandoned (KI-81)

**Decision.** `withdraw_from_box`'s documented contract changes from *"Never raises: a PC hiccup
must not destroy a heal that already succeeded"* to **"never raises FOR A PC PROBLEM"** — a
`StoryAbort` (a whiteout) now propagates. The docstring moved in the same edit as the code.

*Rationale:* the contract's PURPOSE is to protect a heal that already succeeded. After a whiteout
**there is no heal left to protect** — the player has respawned elsewhere, and the abort latch is
cleared ONLY by `StoryMode.run`, so continuing cannot recover. Swallowing it means the bot keeps
driving a PC menu that is no longer on screen, and then **launders** the cause into a confident,
plausible, wrong one.

*Rejected:* keeping the absolute contract and letting `StoryMode.run` notice later. It cannot — the
whole point of the latch is that nothing downstream clears it, so every subsequent operation fails
for reasons that name the wrong thing.

*Rejected also:* using `except StoryAbort: raise` alone. **Latch-keyed beats type-keyed**: a retry
loop that catches an error and raises a fresh one destroys `StoryAbort`'s identity, and only the
latch survives that conversion. `reraise_if_aborting` reads the latch, so it catches the laundered
case too — which is the case that actually bites.

⛔ **THIS ENTRY SUPERSEDES ONE LINE OF THE PC-RETRY DESIGN ENTRY EARLIER IN THIS FILE** (search
*"is being LAUNDERED today"*, ~line 2714). That was TRUE when written and was FIXED later the same
day. This file is append-only, so the earlier line stays — ‼ **read it as dated, not as current.**

‼ **The same narrowing applies to the two deposit helpers and the three heal piggybacks**, which
carried the same absolute wording. It does NOT apply to `PathFindingError` — see the mistakes entry;
routing a `RuntimeError` through the guard would have leaked a stuck global latch.

## 2026-08-16 — the abort probe stays a PROBE, and `--build` is what makes a promotion measurable

**Decision 1 — `probe_abort_swallowing.py` is NOT added to `run_gates.py`** while 45 candidate sites
remain. *Rationale:* a gate that is red on arrival over pre-existing debt teaches everyone to ignore
gates, and an ignored gate is strictly worse than no gate. `repro_no_silent_except.py` took exactly
this path — measure, record the pre-existing count, fix, then enforce. *Rejected:* adding it with a
"no worse than N" threshold now; that bakes 45 known-bad sites into the definition of green.

**Decision 2 — the probe gained `--build`, and that is how the KI-81 promotion was proven.**
*Rationale:* KI-79 established that `1/1 byte-identical` proves a file was COPIED, never that its new
branch RUNS — and its answer, a three-point fault-hook A/B, **does not apply to a guard**, which has
no branch to flip. The question for a guard is whether the FORK'S OWN handlers now have the
property, so the instrument must be able to look at the other fork. Measured: **53 → 45**, with
per-file guarded-handler counts moving **0→3 / 0→4 / 1→2**. *Rejected:* accepting the byte-compare
because "it is only a guard" — that is precisely the reasoning KI-79 exists to forbid.

## 2026-08-16 — A SAFETY VETO THAT CANNOT EVALUATE MUST FAIL **CLOSED** (KI-65)

**Decision.** When the HM veto in `handle_move_replacement_dialogue` (`battle_move_replacing.py`)
cannot determine which party slot is learning the move — i.e. `party_index is None` because
`_read_offered_move` raised — it now **DECLINES the offer** and says so, instead of letting the
read crash into `except: pass` and confirming whatever slot the fallback picked.

**Why this and not the alternatives.**
* *Alternative A — keep "learning is the safe default" and confirm slot 0 anyway.* Rejected. That
  is the shipped bug. The `except` fallback at `:377-381` hardcodes slot 0, so the confirmed slot
  has had **no policy applied at all**; when slot 0 holds an HM the game refuses it and the
  dialogue ping-pongs until the 3-strike valve kills the run. **REPRODUCED**, not theorised.
* *Alternative B — guard the read but leave the action unchanged (report, don't decline).* Rejected
  as half a fix. It makes the failure visible while still confirming an unverified slot, so the
  wedge remains reachable. The veto's entire purpose is that "nothing can route around it".
* *Chosen — fail closed.* Declining is an ANSWER, so the "never stall on the prompt" property that
  motivated the original default is preserved, and declining is **measured to resolve cleanly in
  ~430 frames**. The cost is bounded and small: on a transient read failure the mon keeps its
  current moves and is offered the move again on its next level-up.

**The trade, stated honestly.** This makes the bot slightly more conservative on an error path: a
move that could have been learned safely is sometimes declined. That is deliberate — an un-learned
move costs one level-up, whereas confirming an HM slot historically cost **2 of 5 overnight runs**
(`#24-movelearn-recovery`). ⚠ It changes behaviour ONLY when the offer read fails; the control arm
of the gate proves normal operation is untouched.

**Scope note.** The fix does NOT claim to explain the reopened `#24-teachmsgstall`. KI-65 remains a
*candidate* cause; proving that connection needs its own repro.

## 2026-08-17 — MEASURE an index-space conversion's DIRECTION before applying it (KI-66)

**Decision.** Before changing `_on_field` to map through `BattleState.map_battle_party_index`, run an
OBSERVE-ONLY probe that logs the raw and mapped values side by side and compare both against a
ground truth derived independently (the party dump: which mon has 0 HP, and which is the ally).
Only then apply the conversion.

**Why.** The filter runs in EVERY battle, not just the multi battle under test. The two index spaces
(`gBattlerPartyIndexes` field order vs a `get_party()` that `UpdatePartyToBattleOrder` has permuted)
are easy to state and easy to get backwards, and a backwards conversion would have been *worse than
the bug*: it would corrupt the on-field exclusion in ordinary single battles, where the existing
behaviour is correct. Reasoning about which direction `map_battle_party_index` converts, from its
docstring, was available and was NOT trusted — the same function's docstring had already been the
source of two prior index-space bugs (KI-18, KI-34).

**Alternative rejected.** "Apply the mapping and see if the gates stay green." Rejected because the
gates would not have caught a wrong direction here: the multi-battle gate is a logic repro, and no
gate drives a real faint inside a partner double battle — that is precisely the gap `ki66faint` was
built to fill, and it did not exist until this session.

**Cost.** One extra ~3-minute driver run. **Result:** the probe showed `mapped` matching ground truth
on both faints and `raw` wrong on both, so the direction was settled by measurement rather than by
argument, and the change went in once.

**Generalisation.** ⇒ *When a fix is a COORDINATE CONVERSION, the cheapest correct step is a run that
prints both coordinates beside the ground truth. Never reason it out from a docstring — this codebase
has now had three index-space bugs in one function.*

## 2026-08-17 — Drift claims are PARSED AS CLAIMS (polarity + currency marker), not pattern-matched as tokens (`#24-driftassertions`)

**The question this settles.** `03-PUNCH-LIST.md`'s `#24-driftassertions` demanded a ruling before
any code: should `audit_doc_consistency.py::check_drift` treat a NEGATED drift figure
(*"NOT ZERO"*) as a claim to evaluate, or keep pattern-matching the number token? The docs pointed
both ways — `04-HANDOFF.md` listed `NOT ZERO` among the MISSES the gate should have caught, while
its own STATE row recorded the gate FIRING on that phrasing as a FALSE POSITIVE to be written
around ("phrase any future caveat here carefully").

**Both could not be true, so it was MEASURED, not argued** (scratch probes, `real_drift` stubbed so
the ground truth was controlled rather than trusted). The six VERBATIM historical strings — recovered
from the commits that introduced and corrected them (`938c4a43` → `535e88e2`) — were run through the
SHIPPED gate at drift **0 and 1**:

| phrasing (verbatim) | drift=0 | drift=1 |
|---|---|---|
| `⚠ **NOT ZERO as of 2026-08-17** — … a ruling is owed` | quiet | quiet |
| `it is **1** again as of 2026-08-17` | quiet | quiet |
| `✅ **0 as of 2026-08-16 (LATEST) — EVERYTHING IS PROMOTED**` | quiet | quiet |
| `…drift figure is NOT 0 / NOT ZERO — a ruling is owed` | quiet | quiet |

⇒ **The FALSE-POSITIVE record is FALSE OF THE CODE.** Every `check_*` function in the file was then
run against those strings at both drift values; **none fired**. `check_drift` cannot fire on a
negation, because `NOT` sits between `drift is` and the number and no pattern admits it. The
negation is a **FALSE NEGATIVE in both directions** — and the STATE row's advice to "phrase the
caveat carefully" was steering authors *toward* the blind spot, not away from a noisy gate.

**Decision.** Parse the negation and EVALUATE it as a claim; never pattern-match the token.
A drift assertion is stale iff its truth value is false:
* plain (`drift is N`) → stale iff `N != measured`
* negated (`NOT N`, `no longer N`) → stale iff `N == measured`

**And the companion ruling — WHICH claims get evaluated at all.** Scoping by the `expect` vocabulary
was the original blind spot, but scoping by *nothing* is worse: the corpus carries **67** windows
mentioning a drift figure, and most are deliberately-preserved history that MUST stay quiet.
The rule is therefore **marker attachment**: a figure is a claim about NOW only when a CURRENCY
MARKER is attached to the number itself — `(LATEST)`, or `is/it is <N> AGAIN` — or when it is
negated, or when it is an `expect`ation (the 2026-08-16 rule). A bare figure in prose asserts
nothing about today and is left alone.

**Alternatives rejected.**
* *Check every number near the word "drift".* Rejected on MEASUREMENT: 67 candidate windows, the
  overwhelming majority historical ("took drift to 0 AT THAT MOMENT", "0 as of 2026-08-15
  (earlier)"). A gate that red-flags the docs' own history gets bypassed within a day — this
  project's own rule 6.
* *Anchor on LOCATION — "everything in the STATE table's drift row is current".* Rejected on
  measurement too: that row is a single ~10-line cell that deliberately carries several dated
  HISTORICAL figures inline. Location does not separate claim from history here; marker attachment
  does.
* *Exempt a whole UNIT that contains a quotation.* Rejected: the 60-second bullet carries a CURRENT
  claim and a QUOTED past one in the same unit, so unit-level exemption would blind the gate to the
  half that matters. Quotation exemption is **span-based**, by match position.

**Why this is worth code at all.** The figure flipped `0→1→0→1→0` in one session; three stale
claims survived hand sweeps AND the gate, each caught by a different audit agent. A stale drift
figure sends a rollback to the wrong commit.

## 2026-08-17 — `#24-orphans` (5): fix the AXIS, do not build the WRAPPER

**The decision.** The item asked for *"`compare_runs.py` pairing for the (P4) matrix"*. We did
**not** build a pairing wrapper. We added an **`ACCEPTANCE:` axis plus an `A/B DISCRIMINATION`
section** to `compare_runs.py` itself.

**Why.** The spec was one sentence in a research note — *"Still NOT built: `compare_runs.py`
pairing … Neither blocks anything today"* — with no design, no consumer, and no acceptance
criterion. Building from it would have been **inventing a spec**, which this project's own rule
forbids. So the first move was to RUN the existing tool on a real A/B instead of reading it, and
that produced the actual finding: fed two arms that differ (`ACCEPTANCE: FAIL` vs `PASS`), the tool
clustered them as identical on all four axes with `<<< SPANS LABELS`. **The pairing was not missing
plumbing; the instrument could not see the discriminator.** A wrapper would have shipped that
blindness behind a convenience command and made it routine.

**Alternatives rejected.**
1. **Build the wrapper as written.** Rejected: it would emit "the arms agree" over a discriminating
   matrix. A tool that is confidently wrong is worse than one that does not exist.
2. **Close (5) as WON'T-BUILD ("blocks nothing today").** Rejected *after* the measurement — the
   premise "never built" was false and the tool was actively misleading, so closing it unexamined
   would have left a live trap filed as a non-issue. ‼ **The item was worth doing for a reason
   nobody had written down.**
3. **Re-engineer the failure taxonomy** so a finished driver run stops classifying as `hang`.
   Rejected as out of scope and riskier than the problem: the `hang` classification is *correct*
   (the marker really is in the log), it is simply CONSTANT across arms. Naming it blind is
   honest and cheap; re-deriving the taxonomy would put every historical cross-machine cluster
   this tool has ever produced back in question.

**The general rule this leaves behind.** ⇒ **When a backlog item says a tool is "never built",
RUN the nearest existing tool on a real case before writing any code.** Twice now the answer has
not been "build it" but "the thing that exists is pointed the wrong way" — and only running it
says which.

## 2026-08-17 — `#24-ki76correctness`: MEASURE the arming before touching shared pathfinding, and let PRODUCTION be the oracle

**Decision 1 — measure, do not patch.** KI-76's correctness half has been open since 2026-08-13 with
a specified fix. We did NOT write it. Both defects change SHARED pathfinding that every mode depends
on (the KI-59 shape), each needs its own A/B, and KI-76 itself requires live confirmation first. So
the deliverable was a measurement plus a properly-shelved item, not a patch.

**Why that is the right call and not timidity.** The measurement changed what the fix should
prioritise. The docs treated KI-76 as one issue "armed chiefly on Routes 132-134"; measured, the two
defects are armed in *different places* — the dismount defect 1,852 times, overwhelmingly on those
routes, and the ends-on-a-warp defect **9 times, all inside Room 6 and zero on the routes**. A
session that had started patching from the old header would have hunted the warp defect where it
does not exist. ⇒ **The cheapest thing you can do to a long-open issue is find out how big it is.**

**Decision 2 — production is the ORACLE; the replica reports agreement.** The first probe
re-implemented `map_path.py`'s slide loop. That is the obvious design and it is wrong here: the
replica could not follow a map connection, so 14.7% of chains were unmeasured and the cap-margin
claim was unprovable exactly where the risk is. Rejected in favour of classifying on
`PathTile.forced_movement_to` — the endpoint production itself computes — with the replica retained
ONLY to supply the break reason production does not record, and its disagreement rate PRINTED.
**Alternatives rejected:** (a) ship v1 with a caveat — rejected, a caveat that a reader must carry
in their head is not a measurement; (b) build cross-map following into the replica — rejected, the
positive control is two INTERIOR cavern chains and so could not validate that code, which would have
shipped unvalidated logic to close a gap caused by unvalidated logic.

**Decision 3 — correct the code comment even though it costs drift.** `map_path.py`'s cap comment
asserted three things measurement refuted ("longest real chain is 32 / ~16x margin / Routes 132-134
unmeasured"). Fixing it takes sandbox↔custom drift 4 → 5 while a promotion decision is already owed.
Taken anyway: a false statement in production code is how the 32 — which was only ever the CAVERN's
longest — became a ROM-wide claim in the first place. ‼ Proven comment-only by **AST equality**
(fault-tested), and written **net-zero on line count** so no `map_path.py:NNN` citation in the
append-only logs moved.

**The rule this leaves behind.** ⇒ **A header that covers two defects must state each one's status
separately.** P2 already says a heading is a claim about every bullet beneath it; this is the same
rule applied to defects inside one issue, and it cost nothing to find once someone counted.

## 2026-08-17 — promote all five in ONE round, but prove them in THREE groups

**Decision.** The user approved promoting all five drifted files together. We did NOT treat that as
one promotion with one proof. The five files implement three unrelated changes, so the round carries
**three independent before/after discriminators** — a verdict gate that flips 1 → 0, an abort-site
count that falls 44 → 36, and a byte/AST pair for the comment-only file.

**Why.** A single shared proof ("promote.py reports 5/5 byte-identical") is exactly the evidence this
project has ruled insufficient twice: *a copy is not evidence, and a byte-compare only proves a file
was COPIED, never that its new branch is what RUNS*. With three changes in one round, one shared
proof is worse still — it cannot distinguish "all three landed" from "one landed and two are inert".

**Alternatives rejected.** (a) Promote in three separate rounds — safer in principle, but each round
needs its own restore point and its own unrepeatable BEFORE capture, and the three changes do not
interact (different files except `higher_level_actions.py`, which carries two of them and is covered
by both discriminators). The extra ceremony would have bought nothing measurable. (b) Accept
`promote.py`'s byte-equality as sufficient — rejected on the standing rule above.

**The ordering rule this round re-earned.** ⛔ **The BEFORE half is unrepeatable and therefore gets
its own commit, pushed, before `promote.py` runs.** It also became the *arm* that justified
attributing the abort-count drop to the promotion rather than asserting it — the probe demands
exactly that arm, and it existed only because the BEFORE capture was a deliberate first step.

**One follow-up it created, recorded rather than left implicit.** A per-fork RATCHET must be
re-based after a promotion: custom's baseline moved 44 → 36. ⇒ **promoting a fix that a ratchet
counts is not finished until the ratchet is turned**, or the gain silently unlocks.

## 2026-08-22 — PASS 4 rulings: an ADVISORY gate tier, and three things deliberately NOT done

**RULING — a probe that cannot fail becomes ADVISORY, it is not deleted and not forced to exit.**
Pass 4 found three suite entries with zero assertions. Three dispositions were possible:
* *Delete them from `GATES`.* **REJECTED** — gate ordinals are append-only here; removing #21-#23
  would renumber every later citation, which is precisely the mistake logged on 2026-08-17 when
  INSERTING one silently renumbered six.
* *Give each an exit code.* **REJECTED for two of the three** — `probe_regi_capabilities.py` reports
  a KNOWN-blocked arc (the Regi work is not started) and `probe_dive_routing.py` says of itself that
  it "does NOT prove the route works". Gating either would red the suite permanently over a
  documented, accepted state, and a gate that cries wolf is rated worse here than no gate at all.
* **CHOSEN — a third tier.** They stay in `GATES`, they RUN, their output is kept, and they print
  `ADVIS`. The closing banner now separates `27 ENFORCING` from `+2 ADVISORY`, so no reader can
  mistake a measurement for enforcement.
‼ **The exemption ships with a CONTROL**, because a mechanism that can swallow any failure is worse
than the bug it hides: the identical failing stub, NOT marked advisory, still fails the suite. That
control is a permanent part of the fault test.

**RULING — gate on the invariant with a PROVEN red arm, never on the one that merely looks right.**
`probe_slot_free_plan.py` publishes two booleans, `blocked` and `spared_ok`, both True today. It now
exits on `spared_ok` **only**, because that is the one an agent actually drove to False. Gating on
`blocked` as well would assert something never demonstrated to be able to fail — a CLAIM wearing a
guard's clothes. *(Same rule the project already applies to "without X the bug survives" statements.)*

**RULING — do NOT gate flag names in documentation. The obvious fix is refuted by measurement.**
`audit_flag_names.py` never reads docs, and CLAUDE.md names docs as exactly where hallucinated flag
names have landed — so extending it looked obviously right. Measured before building: **438
unresolvable mentions across 49 files sit in `ai-research-notes/`**, which is explicitly "RECALL
ONLY, never authoritative" and where unverified names are the entire point; and of the **15 in 7
authoritative docs**, most are prose PLACEHOLDERS (`FLAG_NAME`, `FLAG_BADGE`, `VAR_TEMP`,
`FLAG_MOSSDEEP_GYM_SWITCH_X`). A gate firing on those teaches the reader to bypass it.
⇒ The residue is a small ADJUDICATION job (~8 names against the decomp), not a gate. `#24-flagnamedocscan`.

**RULING — fix the 7 `is_test_run` sites inside the suite; do NOT sweep the other 98.**
`is_test_run=True` stops the atexit that overwrites shared profile state — but it *also* suppresses
LOADING `current_state.ss1` (`libmgba.py:144`), so it is a behaviour change, not a hygiene flag. The
7 in the standing suite run on every commit and were verified individually (state count and mtime
unchanged, all still exit 0). A blind mass-edit of 98 more could silently change what a probe boots
from, and `story_harness.py` probably SHOULD keep profile state. Batched under `#24-testrunsweep`.

**RULING — the fixture-coverage gap is REPORTED, not FAILED.** 66 of 77 fixtures have no manifest
row. Failing on them would block every commit from the moment it shipped. The gate now prints the
gap at every run so it cannot be missed, and the classification work is filed with an explicit
warning not to PIN anything whose stability has not first been measured.

## 2026-08-22 — PASS 5 rulings: a scope that did not exist, and what NOT to fix

**RULING — PASS 5's SCOPE IS NOW ON THE RECORD, because it had none.** `#24-sanitycheck` said
outright that pass 5 had "no scope written anywhere beyond its title". It was defined as EIGHT
angles, one per agent: cold start from the handoff; cold start from `00-README`; can each filed
"startable" item actually be started; playbook currency; known-issues navigability; punch-list
navigability; plain-English accuracy; vision/architecture vs reality. ⛔ Recorded so the audit is
REPRODUCIBLE — an audit whose scope was improvised and never written down cannot be re-run or
compared against.

**RULING — the cold-start agent gets NO context, and that is the whole point.** It was given only
`04-HANDOFF.md` and `00-README.md`, and forbidden from reading the changelog or git log to work out
"what was really meant". It found FOUR contradictions the automated gates and a Tier 1 reviewer had
both missed. ⇒ **Keep starving it. The moment it is told what you believe, it stops being able to
find what the documents actually say.**

**RULING — reclaim budget by ARCHIVING VERBATIM, never by trimming live content.** The punch list had
7 free lines against its R3 limit. Four fully-closed blocks (165 lines) were moved to
`28-HANDOFF-ARCHIVE.md`, each script-verified to contain ZERO open markers before the move and each
leaving a stub carrying the rule later work leans on. ⛔ Rejected: deleting closed detail (it is the
evidence trail) and raising the R3 limit (the limit is what forces this hygiene).

**RULING — the three OPEN items filed under `## Done` were FLAGGED, not moved.** Marking the heading
MIXED and naming all three is a one-line change with no risk of corrupting a 3,500-line file; moving
three `###` blocks is a mechanical edit that can silently reorder or orphan content. ⚠ The move is
the better end state and is written into the heading as the next step — but a doc edit that could
lose content is not worth doing at the end of a long session.

**RULING — `#24-ki76correctness` gets a STOP block, not a new fixture.** Its only save cannot arm the
defect it tests. The fix is to CAPTURE an anchor on ROUTE132/133/134 or ROOM7 with Surf — that is
emulator work with its own verification, not typing, and doing it hastily would produce a second
unverified fixture. The item now names the requirement, names the one sub-task that IS startable with
zero input today, and refuses to let a dismount A/B be planned on the vacuous save.

**RULING — where two honest measurements disagree, publish the COMMAND, not either number.** An agent
counted 71 distinct KI ids where my own grep gave 61; its flag-name figures differed from pass 4's.
Both populations are regex-defined and therefore definition-sensitive. ⇒ the affected lines now carry
the re-derivation command instead of a digit. ⛔ Picking a side would have created a fourth number to
go stale.

**RULING — fix the SCOPE, keep the fixture.** Committed fault-injection drivers made lint R6 fire on
their synthetic flag names. R6 now skips `evidence/`, with a control proving it still fires on real
code. ⛔ Rejected: not committing the drivers — they are the most reusable thing pass 4 produced.

## 2026-08-23 — RULING: the pair list gains **P5**, and a dead agent means an UNCOVERED ANGLE

**RULING — `CLAUDE.md`'s DOC CONSISTENCY LAYER now names a FIFTH pair: the work item's own status in
`03-PUNCH-LIST.md` ↔ what the handoff claims about it.** This is a change to a standing directive and
is recorded here so it never has to be re-argued. **Why:** having shipped pass 4 of the audit, I
updated both halves of P1 faithfully and a Tier 1 reviewer confirmed they agreed — while
`#24-sanitycheck`'s own entry still read *"3 of 5 DONE / PASSES 4 AND 5 REMAIN"* with a build spec,
so a cold reader was commanded to build work that had shipped in the previous commit.
⛔ **A checklist protects exactly what it enumerates.** Updating the two halves a checklist names,
when a fact lives in three places, is the WORST state — the pair check then returns PASS and the
third copy is invisible. ‼ **The reference in the Tier 1 AND Tier 2 instructions was updated to
"P1–P5" in the same edit**, because a pair the reviewers are never handed is prose, not a check.
⛔ Rejected: making it a GATE. A general "does an item claim its own work is unstarted" check is not
tractable without heavy false positives, and this project rates a noisy gate as worse than none.

**RULING — when an audit agent DIES, its angle is UNCOVERED, and the report must say so.** The eighth
pass-5 agent was killed by an API session limit, not by a finding. ⇒ the pass was NOT complete at
seven angles; the angle was RE-RUN the next day, and the changelog carries an explicit correction to
its own "8 agents" heading. ‼ It turned out to be the most productive angle of the pass (17 findings,
including six commands in `02-ARCHITECTURE.md` that could not be run as written) — **so "seven of
eight is close enough" would have been expensively wrong.**
⇒ **Standing rule: report the number of angles that RETURNED, never the number LAUNCHED.**

**RULING — an agent's finding may be STALE ON ARRIVAL; re-check before acting.** The re-run angle
reported the standing suite RED on `audit_doc_citations.py`. True when it started; already fixed
while it ran. This is the second recorded instance. ⇒ **verify a finding against the CURRENT tree,
not against the agent's snapshot** — which is also why every finding in this audit was re-derived by
the orchestrator before anything was changed.

## 2026-08-23 — RE-AFFIRMED (not a new decision): the Emerald ROM stays tracked. ⛔ THIS IS THE SECOND RULING ON IT.

**Decision:** unchanged — **keep the tracked ROM as is; fix the documentation instead.** The user's
words: *"leave as-is, fix the docs."*

⛔ **THIS ENTRY EXISTS TO STOP A THIRD ASKING.** The original ruling is
**2026-07-18 — "Emerald ROM stays tracked in the repo (user ruling)"**, a few screens above, and it
already ended with *"Do not re-raise this for THIS file."* A PASS 4 audit surfaced the tracked ROMs
on 2026-08-22 and I filed **KI-82** as "awaiting a user ruling" **without checking this log** — so
the user was asked a question they had already answered five weeks earlier. The cost was small; the
process failure is the point, and it is recorded in `08-MISTAKES.md`.

**What this entry ADDS to the 2026-07-18 one (it is not a pure duplicate):**
* **SCOPE — the original names only `custom-pokebot/roms/`.** There are now **two tree entries**,
  `sandbox-pokebot/roms/` and `custom-pokebot/roms/`, created when the sandbox fork was set up. The
  ruling covers BOTH; they are the same dump.
* **COST — corrected.** KI-82 as filed said *"33 MB of a 146 MB `.git`"*. Wrong: both paths resolve
  to the **same git blob `21bfd6e0`**, so the repository stores **one copy, not two**. Git
  deduplicates identical content; two tree entries do not mean two objects.
* **IDENTITY — verified.** SHA-1 `f3ae0881…`, which is in the bot's own accepted-dump whitelist at
  `sandbox-pokebot/modules/roms.py:50`. This is the dump the program is built to load.
* **THE `.gitignore` "CONTRADICTION" IS NOT ONE, and the 2026-07-18 entry already said so** —
  `roms/*` blocks accidental **local** commits; ignore rules never apply to already-tracked paths.
  ⇒ any future audit that reports "ignored yet tracked" is reporting the intended design.

**Alternatives rejected, again:**
* *`git rm --cached` (untrack going forward).* ⛔ Rejected. It would make the next `git pull` on the
  project's OTHER computer DELETE the ROM that machine runs from, and every existing `restore/*` tag
  would stop being "a runnable program" — a promise `25-BACKUPS-AND-RESTORE.md` §3 makes explicitly.
* *Purge from history.* ⛔ Rejected and never seriously on the table: it rewrites published history,
  which this project's git-conduct rule forbids outright, and would invalidate all 19 pushed tags.

**The single condition that reopens this — carried forward verbatim in force:**
⛔ **If the repository is ever made PUBLIC, this decision MUST be revisited FIRST.** It is private
today, and the copyright exposure was explained and accepted on that basis.
⚠ Unchanged: agents must never commit ADDITIONAL ROMs, saves or profiles. The ruling covers THIS file.

## 2026-08-23 — RULING: the whiteout-RECOVERY path is permanently exempt from `_check_abort()`

**Decision.** `#24-loopheadabort`'s head checks were applied to **14** nav retry loops and
**DELIBERATELY WITHHELD from 3**: `exit_building_after_whiteout` (loop 373),
`_exit_training_cave_if_inside` (1934) and `_enter_warp_by_navigation` (3227).
⇒ **INVARIANT: no function reachable from the whiteout-recovery entry points may contain a
`_check_abort()`.** Enforced by gate #30 §1, not by memory.

**Why — and this is not a judgement call, it is the control flow.** `StoryMode` sets `_STORY_ABORT`
when the whiteout is detected and clears it only AFTER the recovery navigation has completed.
Between those two points the recovery runs `wait_until_truly_controllable()`,
`exit_building_after_whiteout()` and `_exit_training_cave_if_inside()` — **with the latch set**. A
head check in any of them raises on iteration 1, so the recovery aborts ITSELF, every recovery
fails, and `recoveries > 40` stops the run. `exit_building_after_whiteout`'s docstring names the
exact user-visible failure it exists to prevent ("the user-seen derail").

**The corroboration that made this a rule rather than an opinion:** the recovery-reachable closure
(11 functions) contains **ZERO** `_check_abort()` calls today. The codebase already maintained this
property; nothing documented it, so nothing protected it. ⛔ **The punch-list item explicitly listed
two of those three functions among the sites to fix** — so the invariant was one careful reading away
from being destroyed by an agent following the instructions.

**Alternatives rejected:**
* *Patch all 17 and "handle" recovery separately (e.g. clear the latch before recovering).* ⛔
  Rejected: the latch is what MAKES the segment unwind; clearing it earlier re-opens KI-67, where a
  chapter caught the abort and retried in place. The recovery must run WITH the latch set.
* *Give the recovery functions a "recovering" flag to suppress the check.* ⛔ Rejected as a second
  latch to keep in sync — a whole new class of stale-state bug, for zero gain over simply not
  putting a check there.
* *Trust prose ("do not add a check here").* ⛔ Rejected. This project's own record is that a rule
  written down does not fire when you are building something else; that is why gate #30 §1 exists.

**Consequence, stated plainly:** the three excluded loops keep the OLD behaviour — after a whiteout
they may still burn their budget. That is the correct trade: they only run DURING recovery, where
burning a bounded budget is survivable and aborting is not.

## 2026-08-23 — RULING: this fix is NOT promoted. Drift is 1 and the decision is the user's.

`modules/story/early_game.py` now differs between the forks. Per standing policy a production
BEHAVIOUR change lands in `sandbox-pokebot` only and promotion is the USER's call. Every drift claim
in the docs was corrected from 0 to 1 with the file named and the reason given, rather than left to
be discovered. ⛔ Do not promote this without an explicit ruling, and when promoting, prove it with a
THREE-POINT A/B against `--build custom` — never a byte-compare.

## 2026-08-23 — ⛔ REVERSED, SAME DAY: the "recovery path is exempt from `_check_abort()`" ruling above is WITHDRAWN

**The ruling above is wrong and is superseded by this one.** It exempted
`exit_building_after_whiteout`, `_exit_training_cave_if_inside` and `_enter_warp_by_navigation` from
loop-head abort checks, on the stated ground that they run while `_STORY_ABORT` is set. **They do
not.** An adversarial review refuted it and an AST resolution of the enclosing branch chain in
`StoryMode.run` confirmed the refutation: both the DERAIL branch (`if not self._whiteout_pending`)
and the WHITEOUT branch call `set_story_abort(False)` BEFORE the recovery routines run.
⇒ **DECISION: the exemption is withdrawn. All 17 loops carry a head check.**

**What replaces it, and why it is worth keeping.** The hazard I described is real — it is simply not
present *today*. It becomes real the moment someone moves the latch clear below the recovery calls.
⇒ **NEW RULING: `StoryMode.run` must clear `_STORY_ABORT` BEFORE invoking any whiteout-recovery
routine**, and that ordering is now gate #30 §1, with a fault test that injects the actual hazard.
⛔ Do not "simplify" the handler by hoisting the recovery calls above the clear.

**Alternatives reconsidered now that the premise is corrected:**
* *Keep the exclusion anyway, defensively.* ⛔ Rejected. It protects against nothing that exists and
  it costs coverage at ~35 `_enter_warp_by_navigation` call sites — a real, unguarded exposure
  traded for an imagined one.
* *Exclude by CALL SITE rather than by function* (the reviewer's suggested `check_abort=False`
  parameter). ⛔ Rejected as unnecessary once the premise is corrected: with the latch clear during
  recovery there is nothing to exclude, and a per-call-site opt-out would add a second thing to keep
  in sync for no benefit. ‼ Worth revisiting ONLY if §1 ever has to be relaxed.

**The general rule this cost me, recorded because it is not specific to this fix:**
⛔ **A rationale that is about to be encoded in a GATE must be proven to the same standard as the
code the gate guards.** A gate built on a false premise does not merely fail to help — it reports
PASS with full confidence and makes the error permanent and self-confirming.

## 2026-08-23 — RULINGS from `#24-p4residuals`: two obvious fixes refuted, and why a DENYLIST beat an allowlist

**RULING — the silent-`except` justification test is a DENYLIST, not an allowlist.** The defect was
real (any 12-character comment laundered a silent handler), but the natural fix — require a
relevance KEYWORD — was measured first and rejected: all 60 comment-justified handlers are genuine,
43 would have newly failed, and the ratchet would have broken on all four roots.
⇒ **The reason is a property of this codebase, and it generalises:** justifications here are written
as DOMAIN PROSE ("an unreadable map must never end the fight"), not as keywords. **An allowlist
encodes a house style the house does not have.** A denylist encodes only what is definitely NOT a
justification, which is a far smaller and far more stable set.
⛔ Alternatives rejected: *allowlist of reporter-shaped words* (43 false positives); *drop the
comment escape entirely* (would fail 60 genuine handlers and red the suite permanently).

**RULING — the gate-count supersede exemption stays UNIT-SCOPED, with a proximity bound.** The item
proposed porting the drift check's SPAN exemption. Measured over 143 historical commits, that port
produces a false positive and fails 2 of 7 fault cases — **because the drift check requires the
marker to PRECEDE the claim, and this corpus retracts gate counts AFTER the figure.**
⇒ ‼ **A fix pattern that works elsewhere in the same file can still be wrong here, and the reason
can be as invisible as directionality.** "Copy the existing pattern" is good advice that still needs
measuring. ⇒ Shipped: unit scope + direction-agnostic proximity of **120 characters** (measured safe
band 40-250; deliberately not the file's `MAXDIST = 250`, which leaves an 8-char margin).
⛔ Alternatives rejected: *span port* (1 FP, 2 fault failures); *same-line only* (loses a true catch).

**RULING — `promote.py` gets `--strict`; plain `--check` keeps exiting 0.** Drift is a NORMAL state.
A sandbox-only fix awaiting a promotion ruling has drift ≥ 1 and nothing is wrong, so making
`--check` non-zero would convert "a decision is pending" into "the build is broken" — the cry-wolf
shape this project rates worse than no check. `--strict` serves callers that need a machine-readable
"the forks are identical".

**RULING — (f) is deferred deliberately, not forgotten.** Adding KI-65's ARM C means a real emulator
drive inside a 573-line gate that orchestrates arms as subprocesses. ⇒ **A gate change that cannot be
proven in the same sitting should not ship in that sitting.** Filed with its evidence intact.

## 2026-08-23 — RULING: the abort-swallow ratchet now carries DIFFERENT baselines per fork

`probe_abort_swallowing.py`'s baselines are `{"sandbox": 31, "custom": 36}`. They used to be equal.
**Decision: let them diverge, and treat that divergence as information rather than as a defect.**
The `#24-loopheadabort` fix and its (b) follow-up live in sandbox only, so sandbox genuinely has 5
fewer swallowing sites. Forcing both to 36 would hide a real improvement; forcing both to 31 would
red the suite against a fork that never received the fix.
⇒ **When the forks legitimately differ, a per-fork baseline is the honest instrument.** ⛔ On
promotion, custom's baseline must be lowered to 31 IN THE SAME COMMIT — otherwise the ratchet
silently re-permits 5 sites of debt in the fork that ships.

## 2026-08-23 — RULING: fix the debt you CREATED; file the debt you INHERITED

Re-deriving (b)'s population found 13 swallowing sites where the item named 5. Rather than fix all
13 or trust the 5, both populations were computed — against the commit before the loop-head fix —
and separated: **4 functions created by that change, 7 pre-existing.**
**Decision: fix the 4, file the 7 as (c).**
⛔ Rejected — *fix all 13 while I am in the file*: it would misattribute 7 pre-existing defects to
this change, inflate the commit, and (worse) make the ratchet drop unexplainable by any single arm.
⛔ Rejected — *fix only the 5 the item named, without re-deriving*: right by luck, and it would have
left me unable to say whether the number was complete.
⇒ **A count is only comparable against the criterion that produced it.** Where a reported figure and
a re-derived one differ, compute BOTH and report which is which — the gap is usually a scope
difference, not an error, and the scope is the useful part.

## 2026-08-23 — RULING: three design choices in `#24-p2headergate`, and why each alternative was rejected

**1. The control-character guard is a HARD ZERO, not a ratchet.** Every other numeric gate here is a
ratchet because its population is real debt that must shrink deliberately. This one measured **0 hits
across 725 `.py` files**, so there is no legitimate baseline to preserve and any hit is a defect.
*Rejected:* a ratchet at 0 — identical behaviour today, but it invites someone to "just raise the
baseline" when it fires, which is exactly the wrong response to a control character in source.

**2. The ratchet-claim check reads RAW text, not the fence-blanked text every other prose check uses.**
*Rejected:* reusing the shared fence-blanked corpus, which would have been consistent with its
neighbours and BLIND to the single most dangerous copy of the stale claim — the comment beside the
runnable command in the handoff's HOW TO RUN block, i.e. the line a cold session copy-pastes. ⇒ when
a check's target lives in fences, consistency with sibling checks is the wrong tiebreaker.

**3. THE QUOTING HEURISTIC IS DELETED. THE ONLY EXEMPTION IS AN EXPLICIT, AUTHOR-DECLARED MARKER.**
The check must not fire on prose that QUOTES the false claim rather than asserting it. Three
inferred heuristics were written to decide that, and **all three were broken by independent
reviewers**: *v1* mark parity (a stray backtick exempted a real claim); *v2* sequential pair
containment, which looked structural and was **measured identical to v1** (0 mismatches / 2517
trials); *v3* proximity bounds, defeated by two unrelated backticks that happened to sit close
enough. Each narrowed the hole; none closed it.
*Chosen:* **remove the heuristic entirely** and honour `SUPERSEDE_RE` — the retraction marker every
other check in that file already honours, and whose absence here was itself a review finding.
⇒ **PREFER AN EXPLICIT, AUTHOR-DECLARED EXEMPTION OVER AN INFERRED ONE.** An inferred exemption is a
guess about intent and can be triggered by punctuation nobody meant; a declared one IS the intent,
and no stray backtick can fake it.
⛔ **What actually settled it was SCOPE, not cleverness.** The check reads only `CURRENT_STATE`
files, and across all of them the phrase occurred exactly **ONCE**. Sixty lines of heuristic, three
broken implementations and three review rounds existed to exempt **a single sentence** — which was
then fixed by rewriting the sentence. ⇒ **BEFORE BUILDING AN EXEMPTION, COUNT WHAT IT WOULD EXEMPT.**
If the answer is "one", the exemption is the wrong tool.
*Also rejected:* keeping v3 with tighter bounds — it would have narrowed the hole a fourth time
without changing the fact that "is this phrase quoted?" is not reliably answerable from local
punctuation in a corpus saturated with backticked identifiers.
## 2026-08-23 — RULING: delete `check_ratchet_baseline_claims` rather than fix its 7 blockers

**Decision.** Remove the check entirely (289 lines incl. 17 self-tests) and keep the other two checks
of `#24-p2headergate`.

**Why, in the order the reasons actually weigh.**
1. **Blast radius.** It guards a stale FIGURE in a current-state doc. The probe is the authority and
   the docs say so. A defect here costs a stale sentence. Six adversarial review rounds had gone into
   it while the bot itself had open behavioural items — that is the wrong allocation, and noticing it
   required the user to ask what we were actually working on.
2. **Non-convergence, measured.** Three exemption implementations, three independent reviewers, three
   bypasses; v2 was *measured identical* to v1. Removing the exemption exposed a predicate that
   missed 7 of 7 real claims while firing on any nearby digit. Every fix opened the next hole.
3. **The general rule this yields:** ⇒ **when a predicate needs a THIRD exemption, the predicate is
   wrong.** Judging author INTENT from local punctuation is not solvable at this cost.

*Rejected:* fixing the 7 blockers — the synthesizer's own "smallest fix" for two of them required a
predication parser, which is more machinery again for the same nicety.
*Rejected:* keeping it as ADVISORY — an advisory that is wrong in both directions is noise, and noise
teaches readers to skip the gate output that also carries the real findings.
*Rejected:* keeping it and lowering the review bar — that is how an unmeasured gate ships, and this
file's history is made of those.

⇒ **STANDING RULE ADOPTED: review depth and implementation effort scale with BLAST RADIUS.**
Production code that drives the bot earns deep adversarial rounds; a gate earns one or two; a
doc-consistency helper earns one. "A reviewer found something" is a reason to fix it, not
automatically a reason to keep going.

## 2026-08-23 (logged 2026-08-24) — RULING: `#24-abortrecoveryresiduals` (a) — do NOT patch the whiteout-recovery path; close it on an ASSESSMENT

**Decision.** A second whiteout arriving during whiteout recovery would propagate a `StoryAbort` out
of `run()` and kill the mode (`story_mode.py:2628-2629`). **The fix was deliberately NOT made.** The
item is closed on a reachability assessment, not on code.

**Why.**
1. **A battle cannot start in the window.** Verified with the project's own
   `get_wild_encounters_for_map`, with POSITIVE CONTROLS so the reader is proven to work: **all 17
   towns/cities and all 32 Poké Center maps read land encounter rate 0**, while Routes 101/102 and
   Petalburg Woods read 12. Reproducible:
   `tools/story-dev/evidence/2026-08-23-abortrecovery-a-verify-landrate.py` (52 assertions, 0 BAD).
2. **`on_whiteout()` cannot fire twice on Emerald** — one dispatch site, gated behind a state
   mutually exclusive with its own triggers; `set_story_abort(True)` exists in exactly one place.
3. **Never observed** in 16,688 recorded recoveries across 1,049 logs (both counts re-derived by
   grep; they cross-check as 16,688 − 1,049 = 15,639 consecutive pairs).
4. **Blast radius of the FIX exceeds the blast radius of the BUG.** The whiteout-recovery path is
   this project's highest-risk area, and the change could not be proven without driving a double
   whiteout — which is hard to stage precisely because the scenario is so unreachable.

*Rejected:* shipping the proposed `except StoryAbort: yield` ahead of the `except BotModeError:
raise`. ‼ It is **correct in shape** — it would make the whiteout branch match the DERAIL branch,
which already swallows-and-continues around the SAME `exit_building_after_whiteout()` call bounded by
`_derails > 4`, and would hand control to the `recoveries > 40` bound that currently never gets used.
It is rejected as UNPROVEN, not as wrong. `StoryAbort` is not imported in `story_mode.py`.
*Rejected:* driving a double whiteout now to prove it — the setup cost is high and the assessment
says the payoff is a defect that has never occurred and structurally cannot in this ROM.
*Rejected:* leaving the item OPEN. An open item with no next action is a queue item that re-costs a
future agent the same investigation. Closing it WITH the evidence and explicit re-open triggers is
strictly better — which is the point of this log.

⛔ **RE-OPEN THIS RULING IF** either premise breaks:
* the bot is run on **FireRed/LeafGreen** — a live duplicate-callback path exists there (loop C can
  clear before `Task_RushInjuredPokemonToCenter` is created, re-arming the listener); or
* respawn ever moves to a map with a **non-zero land encounter rate** — re-run the evidence script.

‼ **This entry exists because a Tier 1 reviewer noticed (b) and (c) each got a ruling and (a) — the
bigger decision — did not.** SESSION DISCIPLINE rule 11 says a future agent greps THIS file before
re-raising a question; a decision recorded only in the changelog is not findable that way.
⇒ **The decision NOT to act is a decision, and it needs a ruling more than an action does** — an
action leaves a diff behind as evidence, an inaction leaves nothing.


## 2026-08-24 — §Ch21 leg 1's acceptance was RE-POINTED from the Cave of Origin to the Poké Center

**The choice.** `--driver ch21dive`'s "AND THE BOT CAN CONTINUE" check originally required a walkable
`calculate_path` to the Cave of Origin door `SOOTOPOLIS_CITY (31,16)`. Drive 2 failed on it. It now
requires a path to the **Poké Center `(43,31)`** instead, and `cave_path` is still measured and
printed — just not graded.

**Why, and why this is not lowering the bar.** The decisive fact is in the decomp and is independent
of any reachability measurement: `SootopolisCity_EventScript_StevenLeadPlayerCaveOfOrigin` ends
`warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20`. ⇒ **the game WARPS the player in; a free walk to the cave
is never required of anyone.** Grading leg 1 on it asserted something Pokémon Emerald does not
provide. The replacement is the bot's REAL next action: the fixture's party arrives with a **fainted
member at 54% HP** (the anchor inventory says so unprompted), so the Poké Center is where it must go.

**The alternative considered and REJECTED: keep grading on `cave_path` and "fix" the navigation.**
Rejected because there is nothing to fix — the requirement was invented by me, not by the game. Had
it been kept, leg 2 would have been designed around walking to a door the story warps you through,
and the failure would have been chased as a pathfinder bug. *(This project has burned days on exactly
that shape: a hazard-avoiding planner reporting an unreachable destination reads as "our tool is
broken".)*

⚠ **What is NOT decided, and must not be asserted as answered:** WHY `calculate_path` refuses that
column. Three candidate explanations survive — the `LOCALID_SOOTOPOLIS_EXPERT` body-block at
`(31,18)` (named in the §Ch21 ATLAS, and the LEADING one), an elevation-transition rule on the
dismount, or something else. ⛔ An earlier draft claimed "ZERO NPCs loaded, so it is NOT the Expert";
**that inference is invalid** — `get_map_objects()` is a camera-range window and the probe stood 30+
tiles away, so it is silent on the question. Settling it needs a live probe standing ADJACENT to
`(31,18)`. ‼ It is not required to approve leg 1, and it must not be written up as resolved.


## 2026-08-26 — The Winona SECOND WIND: one derail-retry may do what the manual flip does

**The choice.** After the counter ladder's one failed attempt, `_prepare_for_fight` used to re-raise
the hopeless-gate deterministically on every derail retry (same instance, same history), burning the
5-derail budget into Manual. Now it grants **ONE second wind per boss per run**: empty that boss's
`_loss_ko_history`, mark `_second_winds`, return — the retry re-attempts the boss fresh, exactly
what the user's manual flip achieves. If the fresh cycle also plateaus hopeless (≥6 fresh flat
losses re-satisfy `_boss_plan_is_hopeless`'s own gates), the raise fires as before.

**⛔ THIS COMPLIES WITH THE 2026-07-30 HONEST-STOP RULING; IT DOES NOT REOPEN IT.** The raise is
intact and measured firing (the arm's re-arm control RAISES in both eras). What changed is only how
many fresh attempts precede it: one more cycle, bounded by a checked-then-written marker in the
`_counter_hunts` pattern.

**Why.** Measured: the gate's own premise ("grinding will not fix this") is wrong often enough to
matter — batch 20260811/L01 beat Winona with NO super-effective answer right after losing twice;
111 runs corpus-wide burned their budget on deterministic re-raises carrying zero new information.

**Rejected: reset MORE state (defeat counts, the ladder) to mimic the flip fully.** Keeping
`_defeat_counts` keeps the reactive losses≥2 path armed and the honest re-arm gated purely on 6
fresh losses; NOT re-arming the ladder preserves its ruled one-per-run bound.
**Rejected: shipping without the arm.** The `--driver secondwind` two-era arm was built and measured
on unmodified code FIRST (era=TODAY matched the hand-trace exactly), per the standing rule that a
behaviour change no arm can see must not ship.

## 2026-08-26 — `#24-difftriggeredrules`: advisory-only, diff-indexed, and NO permissionDecision in the hook

**Decision 1: the reminders are indexed by DIFF SHAPE, not by artifact.** Four recall failures in
one session (08-MISTAKES 2026-08-23) proved prose rules filed under where they were LEARNED do not
fire while editing something else. The rule table keys each rule to an added-line pattern or a
touched path; adding a rule = one table entry + its two self-test arms (T25 enforces the pairing).
**Decision 2: ADVISORY FOREVER — exit 0 with and without findings.** Per the item's own filing: a
blocking version acquires false positives and gets bypassed, which this project rates worse than
nothing. The two false-positive classes the adversarial review found in v1 (two-line gate idiom,
see 07-CHANGELOG) are exactly why: had this been a blocking gate, it would have taught bypass on
day one.
**Decision 3: the PreToolUse hook emits `additionalContext` ONLY — ⛔ NO `permissionDecision`.**
A claude-code-guide research agent asserted `permissionDecision: "allow"` was "mandatory" for the
context to be injected. REFUTED by the safety analysis: an "allow" would AUTO-APPROVE the
`git commit` past the user's permission prompt — an advisory has no business changing permission
behavior. Worst case without it: on an older Claude Code the context is not injected and the
advisory silently degrades — the cheap failure direction. (Also the measured Gemini rule, applied
to Claude agents: grade an agent's NAMES highly and its ARCHITECTURE ADVICE not at all.)
**Rejected: wiring the advisor into `run_gates.py` as an ADVISORY gate.** The runner captures
gate output to `.gate-logs/<stem>.txt` and prints only a label line, so suite membership BURIES
the advisory — the opposite of "unmissable at the moment of the edit". The hook is the delivery.
**Rejected: hook exit 2 (stderr → model).** That is the BLOCKING channel; forbidden by Decision 2.

## 2026-08-26 — `#24-driftheadlineshape`: position-scoped exemption, not vocabulary

The drift cell holds ONE live figure and a long archive of historical ones. **Decision: the gate
reads only the FIRST `N as of <date>` per drift-labelled row** — enforcing the cell's own
documented convention ("today's number is at the TOP") — rather than classifying each figure as
live/historical by nearby words. **Rejected: vocabulary exemptions** (`Previously`, `historical`,
`ARCHIVE` proximity) — the 2026-08-23 entry measured exactly that shape silently exempting a live
fault injection because a common word co-occurred. **Rejected: the general "`<number> <noun>` vs
list length" form** the item offered — counting files inside a 4,000-char prose cell is an
inference engine (the "when a predicate needs a third exemption, delete the predicate" lesson,
pre-empted); the headline-vs-measurement compare needs no list parsing because `real_drift()`
already knows the truth.

---

## 2026-08-27 — THE POCKET-EXIT QUESTION IS ANSWERED STATIC-FIRST, WITH PRODUCTION'S PLANNER AS THE ORACLE AND THE DRIVE RESERVED FOR WHAT STATIC CANNOT SEE

**Decision.** Split §Ch21 leg 3's opening probe into two instruments instead of one drive:
`probe_ch21_pocket_exit.py` (static, no emulation loop, seconds) answers everything that is a
question about **the planner**, and `--driver ch21pocket` (live, ~4,200 frames) is spent only on
what a static query provably cannot reach.

**Why.** The build spec called the pocket exit *"the single largest un-measured risk in this whole
area"* and every number in it was a **re-implementation** — three BFS models over the decomp
binaries, agreeing to the tile. `#24-ch21anchor`'s own filing names the failure mode: *"every §Ch21
measurement pays a full Ch20 drive (~25 min) before it starts, which is precisely the cost that
makes people skip the measurement."* `calculate_path` answers about any `(map, tile)` pair off ROM
layout data **without the player being on that map**, so the pocket question is seconds of queries.
`probe_r116_east_grass.py` had already established that shape for "is this pocket reachable".

**What that bought, and it is not a small list:** the pocket's size **347 tiles** measured by the
oracle rather than a fourth re-implementation; the cause proven by **fault injection** (mark Steven
loaded at his state-3 tile → the exit re-opens) rather than argued; and the **90-of-122 re-plan
danger zone**, a number nobody had asked for and which a drive would not have produced at all — a
green drive shows the walk works, not how much of it is one interruption away from stranding.

**The rule this follows, and the one it adds.** Playbook §0d: *"before re-implementing production
logic in a probe, check whether production already PUBLISHES the value."* Added here: ⛔ **a static
counterfactual is only admissible if the rig is shown to reproduce a known LIVE reading** — CONTROL
3 requires the injection rig to return the 98 waypoints `--driver ch21leg2probe` measured live, and
`POKEBOT_POCKET_FAULT=rig` fault-tests that control both ways (red → the probe prints no
measurements and exits 1).

**Alternatives rejected.** (a) *Drive it and read the log* — would have answered "does the walk
work" (yes) and left the mechanism, the pocket size and the danger zone unmeasured, which is the
state the spec was already in. (b) *A fourth BFS re-implementation* — the project has measured that
agreement between re-implementations is not a confidence signal, and one of the three already
diverges from the bot on door tiles. (c) *Static only* — rejected, and the drive proved why: it
returned the one fact no static source could, that the avatar **rests on (31,17), not the warp
table's (31,16)**.

**⚠ What this decision does NOT settle.** The recommended walk-out design (plan once at the resting
tile; on a waypoint timeout walk back toward Steven at (32,18) to re-load him, then re-plan) is
**UNBUILT AND UNPROVEN**. The two walk arms that were run measured **identical** output, so they did
not discriminate between the safe and naive designs — that comparison still owes a forced-timeout
fault arm before anyone may claim `follow_waypoints` is safer in practice.

---

## 2026-08-28 — USER RULING: THE PREVENTION RULES ARE LIVING, AND I MAY UPDATE THEM — NOT ONLY APPEND

**The directive, in the user's words (2026-08-27/28, given twice):** *"implement strategic,
intelligent and robust safety measures from learned mistakes to avoid making the same mistakes
again as well as new ones (living adaptive mistakes avoidance logic, free to update mistakes logic
only to progress and only if they ensure no mistakes happen)."*

**What it settles.** `08-MISTAKES.md` is APPEND-ONLY as a *history* — that does not change. But the
ENFORCEMENT layer (`advise_on_diff.py` rules, gate checks, the prevention-rule text a rule cites)
is explicitly **mine to evolve**, in both directions:
* **SHARPEN** a rule when measurement shows it was too weak or aimed at the wrong thing.
* **SOFTEN or RETIRE** one when it is proven to produce false positives, or when a
  test/lint/refactor makes the mistake impossible — the `/reconcile` principle, now user-confirmed.
⛔ **THE BAR: a change may only make a mistake LESS likely.** Never relax a rule to make a red gate
go green, and never delete the history entry the rule came from.

**Why it was needed, and it is not theoretical.** On 2026-08-27 `R-WARPREST` shipped saying *"only a
live drive answers the resting tile"*. A decomp pass then showed the offset is DERIVABLE from the
metatile behaviour at the warp target, and it blind-tested 3/3 against our live readings including
the discriminating negative. Under an append-only reading of the rules I would have had to leave a
now-superseded instruction standing. Under this ruling the rule was REFINED in place and the
history kept. Three rules were born the same way that day (`R-WARPREST`, `R-SCANBOUND`,
`R-ACCEPTGRADE`), each fault-tested both ways and each verified FIRING on the real commit that
contained the mistake it exists to catch.

**Alternatives rejected.** *(a) Append-only prevention rules* — produces a growing pile of stale
"don't do X" lines that cost context and go unread; CLAUDE.md already warns a stale rule "keeps that
idea active and wastes context". *(b) Ask before every rule change* — the user explicitly delegated
this, and the round-trip would make the layer too slow to keep up with what measurement finds.

---

## 2026-08-28 — USER QUESTION, ANSWERED AND SETTLED: WHY `04-HANDOFF.md` IS NOT SPLIT INTO "PART 1 OF N"

**The question (user, 2026-08-28):** *"the document you are talking about trimming … what if we made
multiple documents 'part 1, part 2, part 3' … are we limited on space? is multiple documents a bad
idea?"*

**The answer, so it is never re-asked.** We are **not** limited on space — the 900-line cap in
`lint_docs.py`'s `LINE_BUDGET` is a **cognitive** budget, and the multi-document structure already
exists: `04-HANDOFF.md` (current-state) + `28-HANDOFF-ARCHIVE.md` (append-only), which
`00-README.md` lists in its reading order.

⛔ **It is an ASYMMETRIC PAIR on purpose, not numbered peers.** The failure this project actually
had is recorded in the archive's own header: `04-HANDOFF.md` grew to **3,240 lines of which only
~162 were current**, carrying **SIX** competing "YOU ARE HERE" banners, the oldest stale by two
weeks — a reader looking for "where are we" found six answers and no way to tell which was live.
**A part number tells you WHERE something is, never WHETHER it is still true.** "Part 3 of 5" would
institutionalise that failure rather than fix it.

⇒ **The split is by KIND, not SIZE:** CLAUDE.md defines 01-05 as current-state ("edit in place,
remove stale content") and 06/07/08 as append-only history. Splitting by size cuts across that line
and puts stale content inside a file labelled current-state.

**And the cap earns its keep as a forcing function.** Hitting it on 2026-08-27 is what surfaced
three REAL doc bugs rather than mechanical trimming: the 60-second summary was two arcs stale (it
opened *"the live arc is PC / PARTY ROBUSTNESS"*), a line claimed §Ch20's assembly was "parked,
finished and waiting" three days after it shipped, and the upstream row was four days behind its
own authority.

⚠ **The one caveat, recorded honestly:** 900 is tight and was hit twice in one day. **If it binds
every session, that is evidence the budget is wrong rather than the content** — revisit it with the
user then. On the day it was diagnosing rot correctly, so it was left alone.

---

## 2026-09-01 — §Ch21 LEG 3: FIVE DECISIONS THE BUILD SPEC LEFT TO THE BUILDER

The leg-3 BUILD SPEC deliberately shipped **two critics' build orders, unmerged**, on the grounds
that "agreement between two agents is not a confidence signal, and picking a winner is a design
decision that belongs to whoever builds the leg". These are those decisions, with what was rejected.

### D1 — THE DOOR TAIL: ship the x=36 column, keep the x=34 column as a documented fallback

**The two critics gave DIFFERENT 16-step tails**, each claiming production provenance: one runs up
the x=36 column and dismounts at `(36,8)`; the other up x=34, dismounting at `(34,8)`.

**Decided by MEASUREMENT first, then by preference.** `probe_ch21_route131_tail.py` adjudicated both
against our own ROM's SET B bytes: **both are contiguous, all 16 tiles are collision-0, and both end
on `(36,7)`.** So correctness does not choose. What chose it: **the surf dismount is the single
least-proven mechanic in the tail** (no arm of any recon pass had ever driven a blind step across
one), and the x=36 column leaves **one** step after the dismount versus the x=34 column's **three**.
Fewest steps downstream of the least-proven mechanic wins.

*Rejected but KEPT IN THE CODE as `DOOR_APPROACH_FALLBACK`*, because if the dismount stalls the
alternative is a one-line swap — and because critic 1 independently named the other column as its
own fallback. ⛔ The code does NOT switch to it automatically: a bot that silently tries a second
route hides the finding.

*Superseded by the drive:* the dismount worked first time, `tail_tiles_confirmed=16/16`.

### D2 — HEAL UNCONDITIONALLY, against critic 1's damage-gated heal

Critic 1 gated the heal on somebody being hurt and then had to invent a `FORCEHEAL` fault arm to
reach the branch at all (the pinned fixture is 687/687). Critic 2 made it unconditional and asked
for the same arm anyway — while removing the branch that arm would force.

**Decided: unconditional.** Two reasons, both safety: (1) healing **pins the whiteout respawn** to
Sootopolis immediately before the longest unbroken stretch in the chapter — ~392 water waypoints,
six routes, 39 undefeated trainers, **no Poké Center en route**; (2) a conditional heal is dead code
on the pinned fixture, and an unconditional one means the by-PID assertion runs on **every** drive.
⇒ the `FORCEHEAL` arm was **dropped**, because a fault arm for a branch that always executes is noise.

⚠ **The cost, recorded honestly** (an adversarial review raised it): `heal_in_pokemon_center` calls
`deposit_dead_weight_if_worth_it()`, which self-gates on a rotation plan and reads nothing off the
bot mode — so a brand-new driver inherits it, and a deposit writes to box data. The by-PID check
already catches that; the leg additionally **re-asserts Surf and Dive after the heal**, so the
failure is named in a Poké Center rather than discovered inside `dive()`'s unbounded A-mash.

### D3 — ⛔ PIN THE PLANNER TO THE LIVE LAYOUT, AND DO IT **AFTER** THE POCKET, NOT BEFORE

The first drive proved `calculate_path` was planning Sootopolis on the **static** layout while the
game ran `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE` (see `07-CHANGELOG.md` for the mechanism and the
A/B). The fix re-seeds `_map_layout_cache` from the live `gMapHeader` and drops the `map_path`
cache so the graph rebuilds.

**Placement was the real decision.** The pocket crossing above it is DRIVEN and PROVEN as it stands;
re-seeding the layout underneath it would change a step that already works, on a map where the
pocket allows **one crossing per visit**. ⇒ the pin happens **once the pocket is behind us**, and
affects only the walk that actually failed.

*Rejected:* pinning at leg start (cleaner-looking, but it silently alters the one proven step);
and the BUILD SPEC's `R-LAYOUTINJECT` follow-up, which patches ROM layout headers — far larger blast
radius, and it was filed as an experiment rather than built.

⚠ **Blast radius, stated rather than assumed:** `_map_layout_cache` is a process global with no
eviction path (KI-73). This touches exactly one map key, only while standing on that map, and it is
correct for as long as the map's layout does not change again — true for leg 3, whose whole run
happens at `SOOTOPOLIS_CITY_STATE 3`. The function returns a description the caller **logs**.

### D4 — LEG 3 ENDS AT `SKY_PILLAR_ENTRANCE`; the Wallace scene is leg 4's opening act

`SKY_PILLAR_ENTRANCE (14,4)` warps to `SKY_PILLAR_OUTSIDE`, whose ON_FRAME Wallace scene fires at
`SOOTOPOLIS_CITY_STATE == 3` with **no coordinate condition** and drives the player ~12 tiles under
`lockall`, then sets the var to 4. That is a **true one-shot**.

**Decided: leg 3 stops on the ENTRANCE mat and proves continuation with a NON-EXECUTING
`calculate_path` to `(14,3)`.** ⛔ Never `(14,4)`: MEASURED, the same call to `(14,4)` returns a path
of the same length with `is_warp=True` ending on SKY_PILLAR_OUTSIDE `(17,13)` — it would "prove"
continuation by walking into leg 4's cutscene. The leg also asserts both story vars are **unchanged**
at the end (3 and 0), which is the one end-state pair that is *not* vacuous: leg 3 could advance them.

*Recorded here so leg 4 does not re-open it:* leg 4 begins by RIDING that scene.

### D5 — THE ACCEPTANCE PREDICATE GRADES THE **METHOD**, NOT ONLY THE DESTINATION

Rejected the spec's end-state-only predicate. A leg that reached the door by re-planning north of
y=14 on Route 131 — where our planner returns a *confident* route through solid rock — has the same
end state as one that hand-walked it. ⇒ `method_ok` requires **exactly 2** planner calls on ROUTE131,
`blind_steps_taken >= 1`, `tail_tiles_confirmed == tail_tiles_expected`, and zero live-grid walls;
`premise_ok` requires the run to have STARTED on `CAVE_OF_ORIGIN_B1F` (the one conjunct that is false
at frame 0 on any other fixture, so pointing the driver at its own output cannot grade as a PASS);
and `R-CONTROL` requires the planner to still be able to **refuse** — a reachability assertion with
no matching refusal is a coin that only has heads.

⚠ **And the predicate says what it does NOT prove:** of the five continuation conjuncts only
`bool(path)` can fail today. The other four are a **regression guard** against someone re-aiming the
constant at `(14,4)`. Keeping them is right; claiming the run "proved" five things is not.

---

## 2026-09-01 (later) — READ THE SKY PILLAR'S CLEAN LAYOUTS FROM **OUR OWN ROM**, NOT BY EXTENDING THE NETWORK PROBE

**The decision.** Four Tier 2 audits named the same blocker — `SKY_PILLAR_TOP` is un-validated and
`probe_skypillar_clean_layout.py` cannot reach it — and the last one proposed the obvious fix:
*"extend it to `1F_Clean`, `5F_Clean`, `Top_Clean` — a 3-line change, cache the binaries."*
**Rejected.** A second, ROM-based reader was written instead.

**Why, in order of weight:**
1. ⛔ **THE PROPOSED FIX WOULD HAVE DECODED GARBAGE.** That probe hardcodes `W = H = 14` on the
   stated premise *"every Sky Pillar floor is 14x14"*. MEASURED: **TOP is 27x24**. The "3-line
   change" would have read 392 bytes of a 1,296-byte map. Its length guard would have caught it —
   but the point is that the premise, not the line count, was the obstacle.
2. **No network.** The playbook records that this environment silently corrupts binary HTTP fetches;
   that probe carries a length check precisely because of it. A ROM read has no such failure mode.
3. **Better evidence.** The decomp describes what pret ships. Our ROM is what the bot plays. For a
   claim that code will depend on, the second is the one that matters.
4. **It generalises.** The technique (enumerate `gMapLayouts`, match dimensions, identify by
   agreement) is the one `probe_ch21_route131_live.py` already uses and that four controls already
   vouch for.

**What was NOT done, deliberately:** the network probe is KEPT, not replaced. It is the independent
second instrument that control C2 checks against — and agreement between two instruments over two
different sources is the whole reason the six-floor result can be trusted. ⛔ Deleting it would
leave the new probe grading itself.

**The cost, recorded honestly:** the identification is by *content*, not by reading the layout
constant the game uses, so it is an inference — a strong one (five controls, a bijection, and an
exact match against an independent oracle on two floors), but an inference. The decisive alternative
would be to read `gSaveBlock1Ptr->mapLayoutId` while standing on each floor, which needs a save state
on every floor and is therefore circular until leg 4 exists.

---

## 2026-09-01 (later) — LEG 4's END BOUNDARY: **THE DESCENT IS IN SCOPE.** Not a judgement call — forced by a standing rule plus a measurement

**The question**, open since leg 3 shipped and flagged by three separate Tier 2 audits: does leg 4
stop at the summit (wake Rayquaza) or continue back down? The two authoritative docs DISAGREED — the
§Ch21 atlas said *"build the descent fall into the leg from the start"*, the queue head said only
*"the climb"* — and an audit called it *"arguably the user's call"*.

**It is not a call. It is forced, and here is the forcing.** MEASURED 2026-09-01 on the CLEAN (story)
layouts read from our own ROM, with cracked tiles banned as through-tiles because a walking bot
falls on entry (`probe_skypillar_rom_layouts.py` MEASUREMENT 2):

    5F (10,1) -> (3,1)    33 steps  OK
    4F (3,1)  -> (7,1)     6 steps  OK      <- the ONLY down-staircase reachable from 4F's arrival
    4F (3,1)  -> (11,1)   NO PATH
    3F (7,1)  -> (3,1)    NO PATH           <- ⛔ THE TRAP
    3F (11,1) -> (3,1)    28 steps  OK      (unreachable: you cannot get to 4F (11,1) coming down)

⇒ **A bot that summits and walks down is TRAPPED on 3F.** The only staircase it can reach lands it
in a sealed pocket with no walking exit to the floor below. Escaping needs a SECOND deliberate fall
(`4F (0,3)` from `(0,2)`, or `(1,3)` from `(1,2)` — both approachable, MEASURED).

**Why that settles it rather than merely informing it:** this project grades every leg on **"and the
bot can CONTINUE"** — a real `calculate_path` off the end tile — because §Ch15, §Ch18 and §Ch19 each
PASSED their own acceptance test while leaving the bot stranded. A summit-only leg 4 **cannot
satisfy that rule by construction**: its end state is a bot that cannot get down. ⇒ the descent is
in scope, and the alternative was never actually available.

**Rejected: "summit-only, descent as leg 5".** It reads tidier and it is what the queue head implied.
It fails because leg 4's acceptance would then have to either lie (grade on something other than
continuation) or fail every time. ‼ A leg boundary drawn where the bot cannot continue is not a
boundary, it is a strand.

**What this does NOT settle,** and leg 4 still owes: the acceptance predicate itself (the end-state
var — ⛔ NOT `SKY_PILLAR_STATE` at 4 or 5, those are `SOOTOPOLIS_CITY_STATE` values), and the
Rayquaza trigger coordinate, which three sources in this tree still disagree about.

---

## 2026-09-01 (later) — §Ch21 LEG 4: THE FALL IS ITS OWN PRIMITIVE, AND THE GRADE IS POSITION+PATH, NOT VARS

Two design choices leg 4 made against the obvious path, both forced by an adversarial recon pass
that measured the failure BEFORE a drive paid for it.

### D-A — `_fall_through_crack`, a NEW primitive, instead of `_bounded_step`

The obvious move was to reuse leg 3's `_bounded_step` for the deliberate fall. **Rejected — it
cannot express a fall, and worse, it fails a CORRECT one.** Its success predicate is
`_at(map_enum, expect)` — SAME map, expected tile. A fall CHANGES the map while PRESERVING (x,y)
(`warphole`). So `_bounded_step` either reports success the instant coordinates change (mid-cutscene,
under `lockall`) or, on a retry, takes UNCOMMANDED steps on the landing floor. The correct witness
for a fall is a MAP CHANGE and nothing else.

`_fall_through_crack` presses toward the crack ONLY while still on the launch tile (a held direction
after landing could start a second step onto the adjacent crack — (7,4) is also cracked), witnesses
`_on_map(to_map)`, and rides out the fall cutscene before anyone reads state. ⛔ It deliberately does
NOT assert the landing tile: a fall preserves (x,y), so a coordinate assert would pass even if the
fall never happened — the landing is proven instead by a `calculate_path` from it (R-FALLPROOF).

### D-B — grade on POSITION + a live path, with the three vars only CORROBORATING

The obvious predicate keys on the story vars (state 5, pillar 1). **Rejected — a whiteout after the
summit respawns the bot in Sootopolis, where the vars ALSO read (5,1,1).** A var-keyed predicate
would grade a WHITEOUT as a PASS. So the driver conjoins: the bot ends on the ENTRANCE, a live
`calculate_path` off the tile it reached succeeds (non-warp, to (6,15)), the negative control still
refuses, the readings-in-ORDER trace matches, and both fall witnesses fired — and whiteouts == 0.
The vars are logged and cross-checked but decide nothing alone.

### D-C — the crack oracle is `tile_type`, because `_live_wall_tiles` is crack-BLIND

`_live_wall_tiles` (built for leg 3) reads COLLISION; a cracked floor is collision 0, so it cannot
see a crack. Leg 4's per-floor gate `_pin_and_verify_floor` therefore checks
`get_map_data(...).tile_type` on the pinned floor, against BOTH `'Cracked Floor'` (intact) and
`'Fall Warp'` (a re-visited, already-crumbled crack — a guard grepping only 'Cracked' matches
nothing on the second pass). ⛔ Do not "simplify" leg 5 back to `_live_wall_tiles` on a floor with
cracks.

**What this does NOT settle, left for leg 5:** the Sootopolis layout at state 5 (the post-crisis
DIRTY one) has not been measured; the return route out of the tower and the HM07 giver are
un-reconned. All flagged in the queue head.

---

## 2026-09-02 — §Ch21 LEG 5: THE FOUR CHOICES THAT SHAPED IT

**1. The PART C A/B's discriminator is the SURF-ACTION COUNT, not the live-wall count.**
*Chosen because* `map_path.py:916` seeds the start node's elevation from the LAYOUT, so a
static "deep water" source makes the planner believe it is already surfing and emit no mount — the
Surf-action count is the value KI-73 actually moves. *Rejected:* counting live WALL tiles on the
planned path, which an adversarial refuter pointed out is **zero in both arms** (ocean is collision 0
in either layout) and would have read INCONCLUSIVE forever, on a gate the queue called load-bearing.
*Outcome:* the measured arms were even further apart than designed — un-pinned raises
`PathFindingError` outright. ⇒ **pick the discriminator from the MECHANISM, not from whatever is
easiest to count.**

**2. The arrival scene is waited out on FOUR conjuncts, not on its var and not on "controllable".**
*Chosen:* script quiet ∧ `SKY_PILLAR_STATE == 3` ∧ live `gMapHeader` back to the map's static
NORMAL layout ∧ controllable. *Because* the scene writes its var 309 frames and one `warpwhitefade`
before it ends (MEASURED), and the fault arm proved the danger rather than asserting it: mid-scene
the live layout pointer really is a different map (`0x08469200` vs `0x083E8624`), so an un-gated pin
would have planned on the crisis layout. *Rejected:* `_ride_summit_scene` + `wait_until_truly_
controllable()` alone, which is what leg 4 uses and which returns mid-scene here.

**3. The leg is graded on the GYM DOOR, not on "a path to somewhere".**
*Chosen:* `R-GYMDOOR` = `calculate_path(-> (31,32))`, the warp to `SOOTOPOLIS_CITY_GYM_1F`.
*Rejected:* the Poké Center (43,32), which was the original target and which **passed on a run that
had sealed the gym** — Wallace was still standing on (31,33). The PC reading is kept as `R-CONTINUE`
(a strict non-warp check) because it is still a real "the bot is not stuck" signal; it is simply not
the one that decides. ⇒ **name the continuation the NEXT WORK ITEM needs.**

**4. HM07 is graded by ITEM ID as well as by flag.**
*Chosen:* `RECEIVED_HM_WATERFALL` **and** `get_item_bag().quantity_of(get_item_by_name("HM07")) >= 1`.
*Because* `giveitem` and `setflag` are adjacent decomp lines but not the same fact — a full bag fails
the first and not the second, and §Ch15/§Ch18/§Ch19 each PASSED on a single script-written value while
stranded. *Rejected:* the flag alone (cheaper, and exactly the shape this project keeps paying for).

**What this does NOT settle, left for the chapter wiring:** §Ch21 is still NOT wired into `_play()`;
the five legs exist as separately-driven functions with no orchestrator, and the chapter's completion
flag (`RECEIVED_HM_WATERFALL`) is now produced by leg 5 but not yet consumed by `chapters.py`.

---

## 2026-09-02 (later) — CORRECTION to the entry above: `chapters.py` ALREADY consumes `RECEIVED_HM_WATERFALL`

⛔ **This file is append-only, so the entry above is left standing and corrected here.** Its closing
"What this does NOT settle" paragraph said *"the chapter's completion flag (`RECEIVED_HM_WATERFALL`)
is now produced by leg 5 but not yet consumed by `chapters.py`"*. **That is FALSE.** Verified by
opening the file: `chapters.py:249-250` is
`Chapter("21", 26, "Sootopolis crisis & Rayquaza", "Sootopolis / Sky Pillar", flag("RECEIVED_HM_WATERFALL"), …)`,
with a ten-line comment at `:240-248` explaining WHY that flag (and not a Rayquaza-defeated flag) is
the right marker; `progress.py:40` maps it to the "Waterfall" readout.

**Consequence for the next work item:** wiring §Ch21 into `_play()` needs **NO `chapters.py` edit**.
The remaining work is the orchestrator plus its dispatch site — a materially smaller item than the
superseded paragraph implied.

**Two facts the same verification pass established, which the orchestrator design depends on:**
1. **`enter_sootopolis()` has no resume guard.** After `assert_ch21_preflight()` it runs
   `_navigate_riding_out(MapRSE.ROUTE126, DIVE_TILE)` unconditionally (`sootopolis.py:194`), and
   Sootopolis has ZERO map connections — so on any post-whiteout resume, leg 1 is the FIRST thing
   that fails, before reaching whichever leg actually owns the state. ⇒ the orchestrator must gate
   leg 1 on "am I already in Sootopolis", not call it unconditionally.
2. **`sootopolis_reached()` (`sootopolis.py:99`) is DEAD CODE** — defined, never called anywhere in
   the tree. It is the obvious predicate for (1) and must be verified live before being trusted, not
   adopted because its name fits.

---

## 2026-09-02 (later still) — §Ch21 DISPATCH grades STRICTER than `chapters.py` does, on purpose

**Decision.** `ch21_chapter_done()` — the predicate the Segment 21 dispatch and `_guard` use — is
`RECEIVED_HM_WATERFALL` **AND** `SOOTOPOLIS_WALLACE_STATE != 0`. `chapters.py:250` keeps grading the
progress READOUT on the flag alone, and is deliberately NOT changed to match.

**Why they differ.** They answer different questions. `chapters.py` answers *"which chapter is the
run in?"*, and `chapters.py:240-248` argues at length that the flag is the right marker for that.
The dispatcher answers *"can the NEXT chapter start?"* — and there is a real state where the flag is
set and the answer is no: `giveitem`/`setflag` and the `call_if_eq VAR_FACING` tail that walks
Wallace off the (31,33) tile blocking the (31,32) GYM warp are different decomp lines, two msgboxes
apart. A run that dies in that window holds HM07 with §Ch22's entrance SEALED.
‼ **MEASURED, not theorised:** leg-5 drive 1 printed `ACCEPTANCE: PASS` in exactly that state, and
`calculate_path(-> (31,32))` raised `PathFindingError`.

**Alternatives rejected.** (a) Tightening `chapters.py` to match — it would make the progress readout
wrong for a state the player is legitimately in, to fix a dispatch concern. (b) Flag-only dispatch —
the §Ch15/§Ch18/§Ch19 stranding shape, and here it is not hypothetical. (c) Making leg 5 the only
place that checks — leg 5 DOES raise on `wallace_state == 0` at the end of its own run, but that
does not help a RESUME that starts inside the window, which is exactly where a whiteout can land.

**What this does NOT settle:** whether §Ch22 should heal first. The chapter ends with a chipped party
(measured: one fainted member, lead at 25/115) and there is no Poké Center after leg 3.


## 2026-09-03 — §Ch22's LEG ORDER, AND WHAT A CHAPTER DRIVER'S GRADE IS ALLOWED TO DEMAND

**DECISION 1 — the §Ch22 leg order is `heal → ice → Juan → fall → B1F → out`, with the fall AFTER
the badge, and there is NO XP run.**
*Alternatives rejected:* (a) an XP run first (clear B1F's trainers before Juan) — this was the
recon's own recommendation and it rested on two premises that both turned out false: that the party
could not beat Juan (a damage calculation, refuted by winning) and that the descent costs three
battles (true only at `badge8=False`); (b) two descents, clearing the trainers on the first so the
second is free — a real design, made pointless by the same decomp finding.
*Rationale:* `SootopolisCity_Gym_1F_EventScript_JuanDefeated` runs `setvar VAR_0x8008, 8` +
`call Common_EventScript_SetGymTrainers`, which `settrainerflag`s **all ten** B1F trainers. Read
from the decomp, then CONFIRMED live (`b1f_entered=True`, `battles_on_B1F=0`).
⇒ **the cheapest correct order is also the simplest one, and it was found by reading the game
rather than by measuring our bot harder.**

**DECISION 2 — a chapter driver grades the BOUND on a recoverable failure, never its ABSENCE.**
`whiteouts == 0` was rejected as a conjunct after it graded a healthy run FAIL: the run lost the
Juan fight, recovered exactly as production does, and finished the chapter. Production tolerates
forty whiteouts. The grade is now `recoveries <= 2` with the raw count REPORTED beside it.
*Alternative rejected:* keeping `whiteouts == 0` and treating a stochastic boss loss as a defect —
that makes the driver disagree with the system it is testing, and this project has already been
bitten once by an arm whose expectation was inverted by its own fix (KI-80).
⇒ **generalised, and now in `08-MISTAKES.md`: an acceptance conjunct asserting an ABSENCE must be
paired with one proving the OPPORTUNITY existed.** Three conjuncts in this one grade were
satisfiable by not doing the thing.


## 2026-09-03 — VICTORY ROAD B1F: A FIXED PUSH SEQUENCE WITH A REFUSAL GUARD, NOT A RUNTIME SOLVER

**Decision.** §Ch23 will clear the Victory Road B1F boulder puzzle with a **precomputed, fixed action
sequence** (PUSH WEST (4,7)→(3,7) from (5,7); PUSH EAST (9,10)→(10,10) from (8,10); SMASH (18,12)),
verified live per step, plus a **refusal guard that makes a SOUTH push on (4,7) or (9,10)
unreachable in code**. The guard lives in the §Ch23 module, NOT in `strength_push`.

**Why.** Two independent Sokoban solvers agree the floor has **891 dead states out of 70,442**, that
**exactly two actions** cross live→dead, and that the minimum solution is **3 actions and unique**.
⭐ Decisively, **only pushes can kill**: of 186,602 walk edges and 145 smash edges, **zero** cross
live→dead. So the entire hazard is expressible as a refusal inside one call, and the bot cannot lose
the floor by walking, laddering or smashing.
‼ A wrong push is unrecoverable **within the visit**; recovery costs a full exit and re-entry, and
`ClearTempFieldEventData` also clears `FLAG_SYS_USE_STRENGTH`, so the puzzle must be re-solved from
scratch each time. On a puzzle where one wrong move is unrecoverable, a precomputed table verified
per step beats a planner — the same reasoning that shipped §Ch22's ice route and §Ch20's Room 8
9-push sequence.

**Alternatives rejected.**
* ⛔ **A runtime solver.** It would have to model boulder pushes, elevation carry, order-dependent
  boulder-rock interlocks and directional edge blockers correctly — and our offline tooling has now
  been wrong about this floor **three times in one day** (the elevation model twice, then two false
  refutations from a reachability query over unreachable boards). A solver that is wrong once seals
  the floor; a table that is wrong once fails a per-step assertion and stops.
* ⛔ **Guarding inside `strength_push` (`early_game.py:7884`).** §Ch20 shares that function, so this
  would be a shared-path change requiring an A/B on the ordinary case (session-discipline rule 9),
  for no benefit — the hazard is specific to one map.
* ⛔ **Detecting the dead state and recovering.** Recovery is possible (exit + re-enter resets every
  boulder) but costs the whole visit and re-arms every trainer and encounter. Refusing is strictly
  cheaper, and a refusal is safe even if the model is over-cautious: a push that is merely redundant
  costs nothing to forbid, while permitting a fatal one costs the visit.

**Conditions on this ruling.** ⛔ It is adjudicated OFFLINE only — **nothing has touched a live
emulator.** The three checks in `ai-research-notes/2026-09-03-ch23-VICTORY-ROAD-B1F-B2F.md` §F are
owed first, and the guard must be built **fail-LOUD**: if a `MAP_OFFSET` (+7) coordinate mismatch
existed, a naive comparison would silently permit the fatal push, so the guard must also assert it
recognises the floor and raise if it does not.


## 2026-09-04 — §Ch23: generalise leg 6's ladder helpers rather than copy them into leg 7

**The choice.** Leg 7 needed the same two behaviours leg 6 already had: "can our planner reach tile X
on map M from here?" and "which neighbour of this ladder can we actually stand on, and which way do
we then step?". The options were (a) copy both into B2F-shaped twins, or (b) generalise them to take
a map and have the B1F versions delegate.

**Chosen: (b).** `_can_reach(map_enum, target)` and `_ladder_apron(map_enum, ladder, label)` are now
the single implementations; `b1f_can_reach` and `b1f_ladder_apron` are thin wrappers, the latter
still wrapping the error to append leg 6's obstacle-position detail.

**Why, and it is this project's own rule rather than a style preference.** `victory_road.py` already
carries the note *"IMPORTED, NOT RE-IMPLEMENTED — this package's transcription rule: the same fact in
two files is the P5 doc shape in code form, and it drifts."* Two copies of the apron-derivation logic
would be exactly that: a fact maintained in two places, where fixing one is the most dangerous state
(the pair check then returns PASS). ⇒ the same reasoning that makes P5 a doc rule makes this a code
rule.

**Rejected: (a) copy them.** Faster to write and lower-risk in the moment, but it would have doubled
a piece of logic that has *already* been subtle once — the apron derivation exists because two
independent agents named different aprons and the framing "at most one can be right" was itself
wrong. Logic that has surprised us once should have one home.

**Cost accepted.** The refactor touched leg 6, which was shipped and passing. ⇒ it was re-driven
rather than argued: `--driver ch23descend` after the change gives `ACCEPTANCE: PASS`, the same
derived apron `(31,25)/"Left"`, `battles=6`, `whiteouts=0`. ‼ A Tier 1 reviewer had flagged exactly
this — that the non-regression was argued structurally and not yet proven — and the re-drive is the
answer to it.


## 2026-09-04 — USER DIRECTIVE: the Elite Four is an ITEM-ONLY gauntlet

**The user's ruling, recorded so it is never re-derived or re-asked:**

> *"the elite 4 is a gauntlet of beating 4 elite 4 trainers/gym leaders and a champion, healing via a
> nurse is not possible here but items can be used in and out of battle while in here to heal."*

**Why this is load-bearing rather than background.** It settles the §Ch24 design question outright:
**the bag IS the healing system for the whole gauntlet.** Five consecutive fights, ~25 opposing
Pokémon, one party, no Poké Center — so every point of HP restored between Sidney and Wallace comes
out of the Items pocket.

⇒ **Consequences that follow directly, and that §Ch24 must be built around:**
1. ⛔ **STOCKING THE LEAGUE MART IS NOT OPTIONAL — it is the survival mechanism.** We hold ₽56,041
   and the bag currently contains **ONE Potion**. That is the single largest gap between here and a
   Champion attempt, larger than the level gap.
   ✅ **RESOLVED THE SAME DAY (§Ch23 leg 11):** bought **Hyper Potion ×30 · Full Restore ×3 ·
   Full Heal ×8 · Revive ×3** for ₽54,300, leaving ₽1,741.
   ‼ **The ₽38,893 first written on this line was the PRE-VICTORY-ROAD figure** — ₽17,148 short of
   the live reading, because Victory Road's own trainers paid out on the way through. Corrected
   before this entry was ever committed. ⇒ *re-measure a number at the moment you spend it.*
2. ⛔ **THE BOT MUST BE ABLE TO USE ITEMS IN BATTLE, OR THE MONEY IS WASTED.** Buying is worthless
   if no code path opens the bag mid-fight. **This is a CAPABILITY question about our own bot and it
   must be answered BEFORE the shopping trip** — otherwise we would spend the money to discover the
   feature does not exist. *(That is the "measure the dependency before pricing the remedy" rule from
   earlier today, applied before spending rather than after.)*
3. ⇒ **The Elite Four LEVEL gap and the ITEM gap are different problems with different fixes.** The
   cost curve in `#24-ch23attrition` (L50 ≈ 88 min … L55 ≈ 5 h, and Wallace is L58) answers the
   LEVEL gap. It does **not** answer the item gap, and stocking does not close the level gap.
   Neither substitutes for the other.

✅ **This CONFIRMS the independent decomp finding** already recorded in
`ai-research-notes/2026-09-04-ch24-POKEMON-LEAGUE.md`: every E4 room seals its own exit with
`setmetatile … impassable=TRUE`, Halls 1–5 contain zero objects, and the only healing before the
gauntlet is the League 1F Poké Center — which is also where the Mart is. ⇒ **one visit does both.**

⚠ **What is NOT settled by this directive** and must still be measured: whether our battle strategy
can select an item action at all, what the Mart's prices are, and what basket ₽56,041 actually buys.
Those are out with agents rather than assumed.

✅ **TWO OF THE THREE ARE NOW SETTLED (2026-09-04).** *The basket:* bought, ₽54,300 — see above.
*The capability:* **`StoryItemBattleStrategy` DOES open the bag mid-fight** — `decide_turn()` calls
`_maybe_use_item()`, which asks `choose_healing_item()` (`modules/story/battle_items.py`) and returns
a `TurnAction.use_item_on(...)` when the policy approves — and it acts in **TRAINER battles only**,
which is exactly where the Elite Four lives. So the money is not wasted.

✅ **AND THE PER-BATTLE CAP — WHICH I FLAGGED HERE AS THE FRIGHTENING UNKNOWN — WAS MEASURED THE
SAME HOUR, AND IT IS NOT THE PROBLEM.** `MAX_ITEM_USES_PER_BATTLE = 4` (`battle_items.py:46`), and
`on_battle_started` returns a FRESH strategy instance per fight, so the bound **resets every fight**
⇒ up to **20 in-battle heals across the gauntlet**. *(A research agent had reported the cap as "1+
per battle"; re-reading the constant refuted it — the standing rule that an agent claim is a NOTE
paid for itself again.)*

⛔⛔ **THE REAL BLOCKER TURNED OUT TO BE SOMETHING ELSE ENTIRELY, AND IT IS WORSE:** the policy
filters on `param > 0` (`battle_items.py:85`), and **Full Heal / Revive / Antidote all carry
`parameter == 0`** ⇒ **11 of the 44 items just bought are unusable by any code path we have**, in or
out of battle. ⇒ **HP carries across all five fights, a fainted Pokémon stays fainted for the whole
gauntlet, and status is entirely unhandled.** Filed as **`#24-e4healing`**, which is now the FIRST
thing §Ch24 needs. ⭐ *The lesson worth keeping: the question I was afraid of had a reassuring answer,
and the blocker was one line below it in the same file. **Fear is not a good prioritiser; reading
is.***


## 2026-09-04 — USER DIRECTIVE: the bot CATCHES and TRAINS, and fills the Pokédex

**The directive, verbatim:**
> *"I am fine with the bot catching and training pokemon, it should be doing this as well as
> collecting pokemon (new, rare, considered rare) to fill out the pokedex understood? continue what
> you were doing this but consider what I said"*

**What it settles.** Catching and training are **first-class goals**, alongside story progress —
not a distraction from it. **Pokédex completion is an explicit objective**, with a stated preference
for **new, rare, and "considered rare"** species. And *"continue what you were doing"* means this
composes with the §Ch24 work rather than replacing it.

⇒ **CONSEQUENCES THAT FOLLOW DIRECTLY:**
1. ⭐⭐ **THE EMPTY PC STOPS BEING A CONSTRAINT AND BECOMES A GAP TO FILL.** `probe_box_contents.py`
   measured **0 boxed Pokémon across all 14 boxes**. Every prior analysis treated "there is no bench"
   as a fact to design around — *"replacing Zigzagoon L19 or Castform L36 would mean catching and
   training something new"* was written as if that ruled it out. **It is now sanctioned.**
2. ⭐ **IT ANSWERS AN OPEN §Ch24 QUESTION.** Two of six party slots are dead weight (Zigzagoon L19,
   Castform L36 — the latter *"outsped by everything except Phoebe's Dusclops; it never gets a turn"*).
   The moveset analysis independently concluded that replacing them is one of the three things that
   would actually fix the Elite Four. Catching is the mechanism.
3. ⚠ **BALLS ARE BLOCKED IN TRAINER BATTLES** (`battle_script_commands.c:9915`), and **no interior
   League map has a wild-encounter table.** ⇒ catching happens OUTSIDE the gauntlet, never inside it.
   This directive does not change how §Ch24 itself is fought.
4. ⛔ **IT INTRODUCES A NEW CLASS OF RISK, AND THAT MUST BE DESIGNED FOR, NOT ASSUMED AWAY.** The
   story chapters were built against a party that only ever changed when *we* changed it. Catching
   mutates party composition, party ORDER, and party SIZE mid-chapter — and `#24-ch23wally` already
   records the faint-replacement chooser feeding a **L19 Zigzagoon** into fights. More Pokémon means
   more ways for that to bite. Several chapters assert members **by PID**.
   ⇒ **the integration is being designed before it is built**, with an explicit survey of what a
   changing party could break.

**What is NOT settled by this directive**, and is being measured rather than assumed: whether a
freshly caught Pokémon can be trained to L50+ in acceptable bot-time; which species are actually
reachable and rare from the bot's current position; and whether catching should run inside story
chapters or only between them. Those are out with a design workflow, not decided here.

⚠ **Do NOT read this as "catch everything, always".** The user asked for **new, rare, and considered
rare** — a policy that re-catches Zigzagoons satisfies the letter and wastes the run. The catch
policy is a real design problem and is being treated as one.


## 2026-09-05 — The 2026-09-04 catching directive is served BY `#24-dexhunt`, not by a new item

**The finding.** After the user's 2026-09-04 directive (*"catching and training… as well as
collecting pokemon (new, rare, considered rare) to fill out the pokedex"*), I designed a feature and
filed it as `#24-dexcatch`. An adversarial review found that **the question was already ruled**:
* **2026-07-31 — `#24-dexhunt`:** *"catch every unseen species except when doing so would block
  progress"*, with `counter_hunt.resource_blocker()` PINNED as the predicate and an explicit
  instruction not to write a second one.
* **2026-08-05 — `#24-pcoverflow`:** *"A FULL PARTY NO LONGER REFUSES THE CATCH"* — let it land in
  the box and retrieve it (`pc_trip.withdraw_from_box`).

⇒ **THE RULING IS `#24-dexhunt`. `#24-dexcatch` IS RETIRED BEFORE IT EVER SHIPPED** — one slug, one
record. The 2026-09-04 directive does not overturn the 2026-07-31 ruling; it **re-affirms and widens
it**, adding Pokédex COMPLETION as a first-class goal and an explicit preference for *new, rare and
considered-rare* species.

**What the new directive DOES change, and it is worth stating so it is not lost:** the 2026-07-31
ruling was about catching *encountered* species cheaply during ordinary play. The new one asks the
bot to **go and collect**, which makes rarity a selection criterion rather than an accident. That is
a genuine extension and belongs in `#24-dexhunt`'s body, not in a second item.

**What is measured and settled as of today:** dex is **seen 116 / owned 11** (105 free wins), the
bot holds **23 balls**, the PC is **empty**, and `resource_blocker()`'s only remaining gate is
`_ball_count() <= 1`. ⇒ **nothing in the ruled predicate blocks the work today.**


## 2026-09-05 — §Ch23's completion gate is FLAG **AND** POSITION, not the chapter table's milestone

**Decision.** `ch23_chapter_done()` = `wally_beaten()` AND on `EVER_GRANDE_CITY` AND on no Victory
Road floor. The Segment 23 dispatch in `story_mode.py` gates on THAT, never on
`DEFEATED_WALLY_VICTORY_ROAD`.

**Why.** `chapters.py:281` grades Segment 23's progress READOUT on that flag, and the flag is set at
**LEG 5 OF 11** — while the bot stands at the B1F ladder apron with the boulder interlock, B2F, the
return climb, the exit, the League heal and the shop all still ahead. A gate on the flag alone would
hand §Ch24 a run buried two floors underground.
⭐ **MEASURED, NOT ARGUED:** `POKEBOT_CH23_PREDICATE_ONLY=1` on `post_wally.ss1` printed
`inside_victory_road=True  flag_only=True  gate=False`. The wrong design is falsifiable and was
falsified.

**Alternatives rejected.**
* *Grade on the flag alone* — simplest, and it is the §Ch15/§Ch18/§Ch19 shape verbatim: three
  chapters that PASSED THEIR OWN TESTS while stranded. §Ch22's predicate exists because it was
  nearly the fourth.
* *Change `chapters.py` so the milestone matches the gate* — rejected: the readout and the gate
  answer genuinely different questions ("which chapter is this run in?" vs "may the next segment
  start?"). Collapsing them would break the progress display to fix a dispatch concern.
* *Add "healed" and "stocked" as conjuncts* — rejected: both are CONSUMABLE, so the predicate could
  flip back to False after a single battle or purchase and re-run a finished chapter for ever. Legs
  10 and 11 self-skip on their own readings instead.

**Precedent.** §Ch21 and §Ch22 made the same stricter-than-the-flag choice for the same reason; this
entry exists because a Tier 1 reviewer noticed those were logged and this one was not.


## 2026-09-05 — a repro for an OPEN bug may be a gate ONLY if it SELF-RETIRES

**Decision.** `repro_ki90_absent_left_slot.py` is registered as gate #38 even though it asserts that
an OPEN defect still reproduces — because it self-retires: if the raise disappears while its
discriminator still passes, it prints `SELF-RETIRED` and exits 0 instead of failing.

**Why.** A gate that asserts "the bug is still here" turns the suite RED the moment someone fixes the
bug. ⇒ it would punish exactly the work it exists to enable, and the rational response would be to
delete it — losing the evidence. ⭐ **A SAFETY MEASURE THAT PENALISES THE FIX IS NOT A SAFETY
MEASURE.**

**What makes it safe rather than merely convenient — AND THE VERSION OF THIS PARAGRAPH THAT WAS
WRONG.** Self-retirement can hide a live defect if the repro rots, so the retirement test must key on
something the defect cannot fake.
⛔ **IT FIRST KEYED ON THE EXCEPTION'S MESSAGE TEXT, AND A TIER 1 REVIEWER BROKE IT BY CONSTRUCTION**
(2026-09-05): reword the raise while leaving the defect completely untouched, and the gate printed
`SELF-RETIRED` and exited 0 — silently retiring a live defect, the one outcome this entry claimed was
impossible. ⇒ ⭐ **A GUARD KEYED ON A HUMAN-READABLE STRING IS NOT A GUARD ON BEHAVIOUR.**
✅ It now keys on BEHAVIOUR, three-way: *raised anything* → the defect is LIVE whatever the wording;
*returned cleanly* → SELF-RETIRED; *hit the step cap* → the repro is broken, fail loudly. Verified
against the reviewer's own counterexample: reworded-message → REPRODUCED (not retired); genuinely
fixed → SELF-RETIRED/exit 0.
‼ **The lesson is bigger than this gate:** my original fault test exercised only the direction I had
thought of (fixture rot). The reviewer attacked a direction I had not — and *that* is why the
adversarial pass is not optional. **Fault-testing proves the arms you wrote, never the arms you
didn't.**

**Alternatives rejected.**
* *Do not register it at all* — keeps the suite honest but leaves the repro un-run, so it rots
  silently and nobody notices until it is needed. The tree already shows what an unrun check is worth.
* *Register it inverted (assert the fix)* — it would fail today, for a bug that is real and open;
  a permanently-red gate is one people learn to ignore, which is the failure mode `CLAUDE.md` rule 6
  warns about.
* *Register it and accept it goes red on the fix* — that is the booby trap above.

**Precedent.** This project already has the concept (`repro_boss_grass_gate.py` "SELF-RETIRED"); this
entry makes the reasoning explicit and adds the requirement that BOTH directions be fault-proven.


## 2026-09-05 — modifying `modules/battle_*`: what is ACTUALLY decided (and the phantom ruling this replaces)

**Decision.** There is **no blanket prohibition** on modifying `sandbox-pokebot/modules/battle_*.py`.
The bar is EVIDENCE, not the filename: a change to a shared battle-path file requires (a) a repro or
A/B that fails first, (b) an argument for why the change is ADDITIVE to states that work today, and
(c) the full gate suite. That is the same bar as any other hot-path change.

**Why this entry exists — a correction to my own documentation.** Five live documents asserted *"the
`KI-83`/`KI-88`/`KI-89` ruling: route around, do not casually patch"*, and I used it to rule out
fixing `battle_action_selection.py` for `KI-90`. **That ruling does not exist.** MEASURED 2026-09-05:
* `grep -ic "route around" 06-DECISIONS-LOG.md` → **1**, and that hit is a VETO in an unrelated
  decision (*"nothing can route around it"*), not a policy on shared files;
* `git log --oneline -- .../battle_action_selection.py | wc -l` → **8** — we have modified that exact
  file eight times, including **`d8230560`, a HANG FIX in this very file**.
⇒ ⭐ **A KI-TO-KI CITATION CHAIN IS NOT A RULING.** KI-89 cited KI-88, KI-88 cited KI-83, and nothing
at the bottom was ever decided. `CLAUDE.md` puts rulings in THIS file so a question is not answered
twice; a chain with no root produces the opposite — a constraint nobody chose, that nobody can find,
and that silently narrows every later decision.

**What the KI-88 / KI-89 judgments DO stand for**, restated honestly and kept:
* they were case-by-case calls that ROUTING AROUND WAS CHEAPER *for those two defects*, and both had a
  concrete reason: a partial fix in that area destabilised a drive on 2026-09-05 (KI-88's own note records the attempt being reverted byte-identical);
* ⇒ **"prefer the smaller blast radius when both options work"** is good engineering and survives.
  **"Never touch these files"** was never decided and is contradicted by eight commits.

**Alternatives rejected.**
* *Keep citing the KI chain* — rejected: it is unfindable, unattributable, and factually wrong about
  the file's history.
* *Adopt "never modify battle_*" as a real rule now* — rejected: it would forbid `d8230560`, a fix
  this project already shipped and relies on, and it would push every future battle fix into
  producer-side shims. ‼ A workflow measured what that costs: the "three producers" for KI-90 are
  really **eight** unguarded sites across four files, and one of them returns **Teleport**, a
  `target=USER` move for which "aim right" is semantically meaningless. A rule that forces fig-leaf
  edits at eight sites to avoid one correct edit is a bad rule.
* *Declare the KI-90 fix approved* — rejected, and deliberately: see the entry below. This decision
  only removes a FALSE constraint; it does not choose the fix.


## 2026-09-05 — `KI-90` is fixed AT THE CHECKPOINT: aim at the RIGHT opponent when the LEFT is absent

**Decision.** `battle_action_use_move` (`modules/battle_action_selection.py`) no longer raises when
`opponent.left_battler is None`. It sets `target_index = 3` — the RIGHT opponent — and raises only if
BOTH opponent slots are absent. ⛔ This entry exists because the previous decision explicitly deferred
this choice (*"This decision only removes a FALSE constraint; it does not choose the fix"*), and an
adversarial reviewer correctly refused to let the code land without it.

**Why the checkpoint and not the producers.**
* ⭐ **THE CODEBASE ALREADY AGREED WITH THE GAME; ONLY THIS FUNCTION DISAGREED.**
  `battle_state.active_battler` (`battle_state.py:418-429`) documents the rule verbatim — *"in double
  battles it will return the left side, unless that is absent in which case it will return the right
  side"* — and the game does the same (`src/battle_controller_player.c:535-536` defaults the cursor to
  OPPONENT_RIGHT). ⇒ this is not new policy; it makes the checkpoint consistent with its own module.
* **The branch had exactly ONE outcome before: an unrecoverable raise.** Every exception from
  `BattleListener` — a sibling controller — reaches `modules/main.py:151-158` and sets Manual, so the
  run HANGS. Nothing that worked before changes; the change is additive to a dead branch.
* **Route-around would need EIGHT edits, and one is meaningless.** A workflow measured eight unguarded
  `TurnAction.UseMove` sites across four files (not the three first believed), and
  `use_move_against_left_side_opponent()` is a pure ALIAS for `use_move()`, so three more only LOOK
  left/right-aware. One site returns **Teleport**.

**The two findings carried forward from the deferral, both now CLOSED:**
1. *"The raise is load-bearing — deleting it yields an infinite Down-press loop."* ✅ **HONOURED, and it
   is why the fix RE-AIMS rather than deletes.** With `target_index` left at 1 the loop presses "Down"
   until the cursor reaches a slot it can never rest on — a SILENT hang, strictly worse than the raise.
2. *"Teleport is `target=USER`, so 'aim right' is semantically meaningless for it."* ✅ **CLOSED BY THE
   REVIEWER, WITH A CITATION I DID NOT HAVE:** `MOVE_TARGET_USER` moves never enter
   `HandleInputChooseTarget` at all (`src/battle_controller_player.c:510`), so `target_index` is never
   consulted for Teleport. The concern was real for a producer-side fix and is INERT for this one.
   ⭐ That asymmetry is itself an argument for the checkpoint: the fix sits after the game has already
   decided whether a target is needed.

**Alternatives rejected.**
* *Route around at the producers* — eight sites, no acceptance test (gate #38 drives the checkpoint, so
  a producer-only fix would not make it self-retire), and one edit that does nothing.
* *Delete the raise* — converts a loud failure into a silent Down-press hang. See finding 1.
* *Do nothing* — the §Ch23 chain hangs on it, and §Ch24 is five consecutive fights with the most
  turns-with-fainting in the game.

**⚠ WHAT THIS DECISION DOES NOT COVER.** The both-absent branch still raises, and a raise from this
stack position is still a hang — believed unreachable (the battle should be over), NOT traced to the
win-check. ⇒ the sibling-controller containment problem is untouched and remains open. And this lands
in `sandbox-pokebot/` only; **promotion to `custom-pokebot/` is the USER's call.**


## 2026-09-05 — REVERSAL: `ch23_chapter_done()` DOES require the Elite Four basket

**Decision.** The §Ch23 completion predicate now requires the chapter's WORK PRODUCT — the Elite Four
basket in the bag — in addition to the Wally flag and the position. ⛔ This REVERSES the reasoning
recorded in its own docstring earlier today.

**What the earlier reasoning said, and why it was wrong.** It said: *"DELIBERATELY NOT CONJUNCTS:
'healed' and 'stocked'. Both are CONSUMABLE … a done-predicate that can turn False again would re-run
a finished chapter forever."* The logic is sound in isolation and it built a hole: **a WHITEOUT
teleports the bot to the Ever Grande Poké Center**, which satisfies "on EG and not on a Victory Road
floor".
⭐ **MEASURED, not theorised** — `saves/ki90_whiteout_at_evergrande.ss1`
(md5 `96b666dd63a8d158734660cef51849b6`), captured by the harness from the live drive that lost the
leg-9 double: the party had just been wiped and the predicate returned **True**.

**Why that was worse than the stranding shape it was written to prevent.** `StoryMode.run` catches the
whiteout's `StoryAbort` and re-enters `_play()` from the top (`story_mode.py:2392-2426`). The dispatch
then asks this predicate, gets True, prints *"Victory Road already done — skipping"*, and advances —
**having skipped the League heal AND the basket**, the two legs whose entire purpose is surviving a
five-fight gauntlet with no nurse.
⇒ ⭐⭐ **A POSITION CAN BE REACHED BY SUCCEEDING *OR* BY FAILING. A WORK PRODUCT CANNOT.** That is the
general rule; the basket is merely this chapter's instance of it.

**The trade, stated rather than claimed away.** The basket IS consumable, so when §Ch24 spends it the
predicate flips False and the dispatch re-enters §Ch23 — costing a re-buy (every other leg self-skips
on position). ⚠ **FORWARD DEPENDENCY, now load-bearing: when §Ch24 is built it MUST set its own
progress marker so §Ch23 is not re-entered.** A wasteful re-buy is strictly better than walking into
the gauntlet wiped and unstocked.

**Alternatives rejected.**
* *Keep position-only* — measured False on a real drive; it is the defect.
* *Add "party is healthy"* — a whiteout HEALS the party at the Poké Center, so it is True in exactly
  the state we must exclude. ⛔ It would have looked like a fix and changed nothing.
* *Exclude the respawn tile by coordinate* — fragile, and it encodes a map detail instead of the
  chapter's meaning.


## 2026-09-05 — REJECTED: a gate for "two different next steps on one line"

**Decision.** I wrote `probe_one_live_step.py` — a gate to catch the defect that has now recurred
SEVEN times in one session ("I edited the half I named", most recently: new text PREPENDED to the
handoff banner while the sentence it superseded was left standing). **I am NOT shipping it**, and the
file is deleted rather than left disabled.

**Why, measured rather than guessed.** Run against the live tree it produced a **FALSE POSITIVE**: it
flagged the `➡➡➡` marker line for declaring two different steps, when the two were the SAME step in
different words —
```
- #24-CH23CHAIN: MAKE THE PARTY SURVIVE THE LEG-9
- MAKE THE PARTY SURVIVE THAT DOUBLE, NOT TO RE-DR
```
Its own self-test also failed its primary arm, and I found that cause: `(.{0,80})` is greedy, so the
first match swallowed the second declaration and `finditer` never saw it. **That part was fixable.**
The false positive is not: telling "the leg-9 double" from "that double" requires comparing free text
for MEANING, and any threshold I pick will flag honest rewordings.

⇒ ⭐ **`CLAUDE.md` RULE 6 CUTS BOTH WAYS.** It says anything enforceable belongs in a gate — and it
says *"a gate with false positives teaches the reader to bypass it, which is strictly worse than no
gate."* A doc gate that cries wolf on legitimate rewording would be bypassed within a day, and would
then also be ignored when it was right. **The rule "put it in a gate" does not license putting it in a
BAD gate.**

**What this leaves.** The seven instances stay as prose rules in `08-MISTAKES.md`. That is
unsatisfying and I am recording it as unsatisfying rather than dressing a flaky check as a safeguard.
⚠ **The honest state: this failure mode is NOT mechanically defended.** If a future agent finds a
crisp, low-false-positive signature for it, that is worth real effort — the candidates I rejected were
keyword-overlap scoring and negation-detection, both of which are thresholds, not edges.

**Alternatives rejected.**
* *Ship it anyway and tune later* — a gate that fires wrongly on its first live run has already lost
  the reader; there is no "later".
* *Ship it advisory-only* — the suite has two advisory gates and they are read as noise; adding a
  third that is wrong would make the advisory channel worse, not better.
* *Constrain the docs to identical wording so the gate works* — that is contorting the artefact to
  suit the instrument.


## 2026-09-05 — the leg-9 attrition fix will be a POKÉ CENTER heal, not bag items, and not grinding

**Decision.** `#24-ch23chain` step 4 heals the party at a **Poké Center before leg 9**, reusing the
shape `heal_before_descent()` already proves (1F → south arrow-warp (15,40) → EG (18,41) →
`heal_in_pokemon_center` → back in). ⛔ **Not** `heal_party_from_bag()`, and ⛔ **not** levelling.

**Why not levelling — measured, twice, independently.** The opposition is **level 43** (decomp:
`src/data/trainer_parties.h:4272-4300`, both trainers, both mons each) against our
**L52 / L48 / L47 / L47**. And the bot entered the fight with **Sceptile 0/145 and Wailord 0/226
already fainted** (`Story-debug-20260905-172610.log:318`). ⇒ a stronger party still walks in with its
two best mons dead. Grinding would have cost hours and fixed nothing.

**Why not the bag.** `#24-ch23attrition` (CLOSED 2026-09-04) records the wallet **spent down to ₽1,741
with ONE Potion** by leg 11. ⇒ bag-healing has nothing to spend here, and a null result from it would
have read as *"healing doesn't help"* — actively misleading the next session back toward grinding.

**Why the Poké Center, specifically.** `#24-ch23attrition` establishes that **there is nowhere to heal
inside Victory Road**, and that leg 6's heal is possible *only* because it runs from 1F, one warp from
the door. The leg-9 fight is at **(31,17), also on 1F** ⇒ the same escape is available, and the
mechanism is already built, driven and A/B-proven (**un-healed 32% / 3 fainted → healed 87% / 0**).

**⚠ Two things this decision deliberately does NOT do.**
* It does not close `#24-e4healing`. §Ch24's gauntlet has no nurse; the League basket remains its own
  problem, and a healthy party at the League door does not survive five fights unaided.
* It does not touch the DOUBLE-battle item hole (`StoryItemBattleStrategy` never overrides
  `decide_turn_in_double_battle`, `story_mode.py:417` / `:261`). That hole is real and stays open —
  it is simply not the cheapest lever for THIS fight.

**Alternatives rejected.**
* *Grind levels* — refuted above; the expensive option that fixes nothing.
* *`heal_party_from_bag()`* — empty bag; would have produced a misleading null result.
* *Route around via (33,17)* — decomp says it is free (**61 steps either way**) and it is worth doing,
  but it routes around ONE fight while attrition is draining the whole floor. ⚠ Also **not yet walked
  in our harness**; it is a decomp BFS result in decomp-local coordinates. Keep as a force-multiplier
  (option b), not as the fix.
* *Split the pair into two singles* — genuinely attractive because it also **re-enables our in-battle
  item policy** (the MRO hole is doubles-only), but it depends on the same unverified coordinates and
  still leaves the party arriving damaged. Keep as option (c).


## 2026-09-05 (evening) — REVERSAL: the leg-9 fix is TWO SINGLE BATTLES. The heal AND the bypass are measured dead.

⛔ **THIS SUPERSEDES THE ENTRY EARLIER TODAY TITLED *"the leg-9 attrition fix will be a POKÉ CENTER
heal, not bag items, and not grinding"*.** That entry is left intact (this file is append-only) and is
now WRONG in its conclusion; its reasoning about grinding and bag items still stands. ‼ It also listed
*"Route around via (33,17) — decomp says it is free (61 steps either way) and it is worth doing"* as a
live alternative. **That is refuted too.** Read this entry instead.

**Decision.** §Ch23 leg 9 will engage Katelynn and Quincy as **two separate SINGLE battles**, from
standpoints **(32,16)** (Quincy, 45 wp) and **(29,16)** (Katelynn, 46 wp), then continue to the exit.

**What killed the previous decision — a drive, not an argument.** `heal_before_exit()` was written
(106 lines + fault arm + registry row) and driven. It failed on its first navigation:
```
UnreachableDestinationError: Could not find a path from (21/32 @ VICTORY_ROAD_1F)
                                                     to (15/39 @ VICTORY_ROAD_1F)
[ch23exit] ACCEPTANCE: FAIL   battles=0   whiteouts=0
```
⇒ ⛔ **THERE IS NO HEAL REACHABLE BETWEEN LEG 8 AND LEG 10.** Leg 6 heals before descending; leg 10
heals at the League; in between the bot is committed. Fully reverted — `victory_road.py` is
byte-identical to `0b5e1707`. ‼ The design had rested on a homemade BFS over cached map data that
claimed one connected component; **the BFS was wrong and the decomp note it overrode was right.**

**What killed the bypass — the probe I should have run first.** `--driver ch23leg9probe`
(OBSERVE-ONLY, `ACCEPTANCE: PASS`, `battles=0`) asked `calculate_path` from the real leg-8 landing:
```
to_bypass_33_17   reachable, 43 wp
bypass_to_exit    ⛔ reachable=False, PathFindingError
split_standpoints (29,16) 46 wp · (32,16) 45 wp   ✅ both reachable
CONE VERDICT      the 62-wp route to the exit apron ENTERS the sight cones at [(31,17)]
```
⇒ **(33,17) is a dead end with respect to the exit**, so "61 steps either way" was wrong — the same
flood-fill error, a second time, on a different question.

**Why two singles is the right answer and not merely the last one standing.**
* ⭐ **It restores a capability the double battle silently removes.** `StoryItemBattleStrategy`
  (`story_mode.py:417`) overrides `decide_turn` but not `decide_turn_in_double_battle`, so in a DOUBLE
  the bot never reaches its item check. Singles turn our healing items back on — which matters
  *because* the heal is impossible.
* **It is legal by trainer data, not a trick.** Both trainers are `trainerbattle_single` with
  `.doubleBattle = FALSE` (`src/data/trainers.h:3899`, `:3911`); the double is emergent from both
  spotting on the same step (`gNoOfApproachingTrainers == 2`, `src/battle_setup.c:1274-1275`).
* **The row is safe afterwards** — a defeated trainer returns 0 from `CheckTrainer`
  (`src/trainer_see.c:275-277`).

**⚠ WHAT THIS DECISION DOES NOT SETTLE, stated so it is not read as a promise.**
1. **It is not yet driven.** Owed live: that interacting from (29,16)/(32,16) really starts a SINGLE.
2. **Attrition is NOT fixed, only un-worsened.** The party still arrives at leg 9 in whatever state
   leg 8 leaves it (`post_return.ss1` is 35% HP with three fainted) and **no heal is available to
   change that.** Two singles un-healed may still lose.
3. **The pathfinder's blindness to trainer sight cones is untouched** and is a general defect:
   `avoid_scripted_events` consults only `on_enter_event_triggers`, while spotting is a per-frame scan
   in `trainer_see.c`. This will recur wherever a route grazes a cone.

**Alternatives rejected.**
* *A Poké Center heal before leg 9* — **measured impossible** (above). Do not re-propose.
* *Route around via (33,17)* — **measured dead end** (above). Do not re-propose.
* *Grind levels* — the opposition is L43 against our L52/L48/L47/L47, and the party entered the fight
  with its two best mons already fainted. Levels were never the constraint.
* *Teach `calculate_path` about sight cones* — the correct general fix, and far too large a blast
  radius for this item: it is a shared upstream-derived pathfinding file, and leg 9 needs one route,
  not a new pathfinding feature. Worth filing separately.


## 2026-09-05 (late) — REVERSAL #2: leg 9 ROUTES AROUND the pair via (33,16). The split is shelved.

⛔ **THIS SUPERSEDES BOTH OF TODAY'S EARLIER LEG-9 DECISIONS** (the Poké Center heal, and the
split-singles reversal). Both are left intact above — this file is append-only — and both are now
wrong in their conclusions. ‼ The heal entry remains correct that grinding and bag-items are dead ends;
the split entry remains correct that the heal is impossible.

**Decision.** §Ch23 leg 9 will navigate **ladder landing → (33,16) → exit apron**, skipping Katelynn
and Quincy entirely.

**Why — measured, and it costs nothing.** `--driver ch23leg9probe` (`ACCEPTANCE: PASS`, `battles=0`):
```
to_bypass_33_16       reachable 44 wp   enters_cones []          SAFE
bypass_33_16_to_exit  reachable 18 wp   enters_cones []          SAFE     44 + 18 = 62
direct route          reachable 62 wp   ENTERS the cone (31,17)
```
⇒ **the same 62 waypoints, and it meets neither trainer.**

**What reversed the previous decision.** Two measurements, both of which contradict something I had
already committed:
1. **The split's approach routes enter the cone.** `(32,16)` 45 wp and `(29,16)` 46 wp both report
   `enters_cones [(31,17)], safe=False`. ⇒ walking to a standpoint **starts the double the split exists
   to avoid.** I selected that plan having measured the destinations and not the routes.
2. **"The (33,17) bypass is dead" was an artifact of my own probe.** `map_path.py:916` seeds the search
   with `source_tile.elevation`; `:859` then forbids any elevation change. (33,17) is on the
   elevation-15 bridge, so the query ran as a phantom player carrying 15. Re-seeding one tile north at
   (33,16) — elevation 3 — answers cleanly. The probe now keeps the bad call as a labelled CONTROL.

**⚠ WHAT THIS GIVES UP, STATED PLAINLY.** Skipping two trainers forfeits their EXP. On 2026-09-04
Swellow and Mightyena both reached L48 fighting this pair. ⇒ **this decision trades levels for
survival**, and it is the right trade *here* because the party arrives at leg 9 at 35% HP with three
fainted and **there is no heal available between leg 8 and leg 10** (measured). A party that dies at
leg 9 gets no EXP at all.
‼ **The Elite Four level gap is a real and separate problem** (`#24-e4healing` and the E4 gap notes).
⇒ **Do not let this decision be read as closing it.** If §Ch24 needs those levels, the place to get
them is somewhere a heal exists — not a no-heal corridor.

**Alternatives rejected.**
* *Split into two singles* — **available but not chosen.** Rescuable via (33,16) (hop 3 wp cone-free,
  exit 20 wp cone-free) and singles do re-enable the in-battle item policy that doubles disable by MRO.
  But it buys two L43 fights with no heal, for the same 62 waypoints the bypass costs. Revisit only if
  the E4 gap forces it.
* *A heal before leg 9* — measured impossible (no reachable Poké Center between legs 8 and 10).
* *Grinding* — the opposition is L43 against our L52/L48/L47/L47; levels were never the constraint.
* *Teach `calculate_path` about trainer sight cones* — the correct GENERAL fix and still open: the
  planner is structurally blind to them (`avoid_scripted_events` consults only
  `on_enter_event_triggers`, while spotting is a per-frame scan in `trainer_see.c`), which is exactly
  why it routed through (31,17). Too large a blast radius for this item; file separately.


## 2026-09-05 (late) — leg 11 may SELL to close a basket shortfall, from an ALLOW-LIST, never a deny-list

**Decision.** `stock_for_the_elite_four` may sell items to cover a shortfall on the Elite Four basket.
What it may sell is `LEAGUE_SELLABLE`, today exactly one entry: **Nugget (₽5,000)**.

**Why selling at all.** Routing leg 9 around Katelynn and Quincy fixed the whiteout and cost their
payouts — **₽4,128**, leaving the chain ₽2,387 short. The alternatives were priced:
* *Fight them as two singles* — yields ₽4,128 but **stakes ₽25,956**: a whiteout HALVES money
  (`overworld.c:358`), and our own logs have lost that fight once in three attempts — including in the
  chain run, which is the case that counts. ⇒ risking the chapter to win ₽4,128 is a bad trade.
* *A thinner basket* — the leg's existing guard refuses it, correctly. Not reopened.
* *Sell the Nugget* — ₽5,000, zero steps, zero battles, zero whiteout exposure.

**Why an ALLOW-LIST is the load-bearing safety property.** A deny-list ("sell anything that is not
medicine") would sell the **Master Ball**, a TM, or a key item the day someone adds an item this file
has never heard of. An allow-list can only ever sell what a human has cleared. ⇒ **adding an entry
requires proving the item has no downstream use**, not merely that it is not medicine.
⭐ The Nugget qualifies on evidence: its only role was as a STEPPING STONE — taking it frees `(15,10)`
so the Aqua Hideout Master Ball becomes standable (`early_game.py:8799-8801`) — a purpose served on
2026-08-12 (`#24-masterball`). Repo-wide search finds no other reader, and
`repro_overworld_items.py` classes it as a TRAP the healing chooser must never pick.

**Guards this decision requires, all shipped.**
1. The early affordability check now distinguishes **unaffordable** from **recoverable**, so the loud
   early refusal survives for the genuinely broke case — and its message names the likely cause
   (*"if this appeared after a ROUTING change, check what payouts the new route skips: ₽2,064 per
   Cooltrainer"*).
2. The sale **asserts the consequence**: the wallet is re-read and the leg refuses if it did not move.
   ‼ `sell_in_shop` had **no caller anywhere in this repo** before this, so a silent no-op was the
   likeliest failure and is now the named suspect in the refusal message.
3. `POKEBOT_CH23_FAULT_NOSELL` reproduces the shortfall on demand.
4. It sells the **minimum** that closes the gap, not the stack — an item kept is an option kept.

**⚠ What this does NOT license.** It is not a money-grinding feature and must not grow into one. There
is no money grind anywhere in `modules/story/` (verified), and `train_for_victory_road` grinds WILD
encounters, which pay ₽0. If a future chapter is short of cash, **the answer is not to widen this
list** — it is to ask what the route skipped.


## 2026-09-06 — KI-93 (Torment): the fix is DESIGNED AND VERIFIED, and deliberately NOT IMPLEMENTED YET

**Decision.** The Torment fix is fully researched and its facts are verified, but the edit is
**deferred to a fresh cycle** with an ordinary-case A/B specified first. Nothing in
`modules/battle_strategies/` or `modules/battle_action_selection.py` was touched.

**⭐ THE NUMBERS THAT DECIDE IT — both measured, not argued.**
```
blast radius of the BUG   : exactly ONE Pokémon in the whole game.
                            `grep -c MOVE_TORMENT src/data/trainer_parties.h` = 1  (Sidney's SHIFTRY)
blast radius of a WRONG FIX: EVERY battle the bot ever has.
```
⇒ **the asymmetry is enormous and points one way.** A defect that costs one fight does not justify a
hurried change to the code path every battle depends on — especially at the end of a long session,
which is exactly how this project acquired three index-space bugs (`KI-18`, `KI-34`, `KI-66`).

**✅ WHAT IS VERIFIED AND READY (so the next cycle does not re-derive it):**
1. **The bit is right.** `STATUS2_TORMENT = (1 << 31)`, `STATUS2_DEFENSE_CURL = (1 << 30)`
   (`include/constants/battle.h:154-155`, fetched). Our decode at `battle_state.py:157-159` matches.
   ⇒ a Torment-keyed filter **cannot misfire in ordinary battles**, which was the single highest risk.
2. **The forbidden thing is `gLastMoves[battler]` — a MOVE ID, not a slot** — tested at SELECTION time
   in `TrySetCantSelectMoveBattleScript` (`src/battle_util.c:999`). The refusal is a **pure re-prompt
   that never consumes the turn**, which is exactly why a chooser that re-picks spins forever.
3. **`gLastMoves` is readable in house style** — `pokeemerald.sym:150` (`02024248`, 8 bytes = 4
   battlers × u16), and `battle_state.py` already does `read_symbol(...)` reads of this shape.
4. **An exclusion filter already exists** at `_util.py:259` (0-PP and `disabled_move`), so Torment is
   one more clause rather than new machinery.

**⛔ AND THE TRAP THAT MAKES THE OBVIOUS FIX DANGEROUS — verified by reading the function.**
`get_strongest_move_against` (`_util.py:244-269`) does `moves = [m for m in pokemon.moves if m is not
None]` and then returns `move_strengths.index(max_strength)` — **an index into the COMPACTED list.**
The existing filters are safe only because they append `-1` and thereby PRESERVE position. ⇒ a Torment
filter written the natural way (skipping the move) would shift every later index and **mis-select in
ORDINARY battles**. ‼ This is the same index-space shape the project has paid for three times.

**⇒ THE CHOSEN APPROACH: the OBSERVED-REFUSAL variant, not the predictive one.** Rather than predict
which move the game will refuse, detect that it *did* refuse and pick differently. It is **vacuously
safe on the shared path** (it cannot fire unless the game actually refuses a selection), it needs no
`gLastMoves` read at all, and it closes **Taunt and Imprison** by the same mechanism. The action
selector already carries bounded no-progress counters (`KI-45`/`KI-46` idioms in
`battle_action_selection.py:22-60`), so it has a natural home.

**Alternatives rejected.**
* *The predictive filter at `_util.py:259`* — smallest-looking, and it is what three of four research
  angles proposed. Rejected because it fires in every battle, depends on the compacted-index behaviour
  above, and **does not actually fix the bug alone**: a four-layer fallback chain
  (`story_mode.py:239-241`, `:255-257`, `:101-107`, `default.py:254-263`) re-picks the forbidden slot,
  and it does not cover `decide_turn_in_double_battle` (`story_mode.py:261`).
* *Do nothing and let `KI-47`'s net stop the run* — honest, and it is the status quo, but it makes
  §Ch24 unreachable: the gauntlet cannot pass fight 1.
* *Implement now, verify next session* — rejected explicitly. The bar for a shared battle file is a
  repro that fails first (have it), an additive argument, **and the full suite**; and the project's own
  rule is that the decisive test for a shared path is an **A/B on the ORDINARY case**. None of that is
  finishable safely right now, and a half-verified hot-path change is worse than none.

**⚠ SEPARATE LATENT ISSUE FOUND WHILE VERIFYING, filed not fixed:** `get_strongest_move_against`
returns an index into the **compacted** move list. For a Pokémon with a gap in its moveset
(`[Move, None, Move]`), that index is not the real move slot. Most parties are contiguous so it rarely
bites — but it is a genuine index-space hazard in shared code, and it is now written down rather than
rediscovered a fourth time.

## 2026-09-06 — reuse the shipped damage formula, and make the faint ranking a PURE function

**Decision 1 — score with `BattleStrategyUtil.calculate_move_damage_range`, not a hand-rolled
`base_power × STAB × effectiveness`.**
*Rejected:* the approximation I had planned. It would have been a SECOND damage model in a codebase
that already has one, guaranteed to drift from it, and blind to the immunity abilities. The shipped
method already accepts a party `Pokemon` as attacker (`_util.py:165-174`) and `decide_turn` already
trusts it four lines below the chooser — so using anything else would have been choosing a worse
answer for no reason.
*Cost accepted:* it is heavier than a type lookup. Irrelevant — it runs once per faint, over ≤6 mons ×
≤4 moves × ≤2 foes.

**Decision 2 — extract the ranking into a pure `rank_replacement(...)` with an INJECTED damage
function, rather than fixing the metric in place.**
*Why:* `choose_new_lead_after_faint` has had THREE index-space bugs and every one required a ROM, a
live battle and a staged faint to observe. **The function's untestability is the root cause of its bug
history**, and a four-line metric fix would have left that untouched. The injected estimator is what
makes the probe possible without building fake `Pokemon`/`BattlePokemon` objects with stats, abilities
and a type chart.
*Rejected:* testing it through the live `ki66faint` driver only. That proves non-regression, not that
the new ranking is BETTER, and it costs a ROM plus ~10 minutes per question.
*Honest limit:* the probe therefore does NOT test the integration with the real formula. That is
argued from `decide_turn`'s existing call, and confirmed at runtime by the new `metric=`/
`estimates_ok=` fields in the `[FAINT-CHOOSER]` telemetry.

**Decision 3 — do NOT promote to `custom-pokebot/`.**
Standing project rule: promotion is the user's call. The user is asleep. Drift goes to 1 and every
doc that claimed 0 now says 1 and why. *Rejected:* promoting because "the gates are green" — green
gates bound a contract, not a permission.

## 2026-09-06 — `KI-93`: gate the dismiss on the PRINTER STATE, and hold the refusal memory at MODULE level

**Decision 1 — press only while `sTextPrinters[0].state == RENDER_STATE_CLEAR`, never on a timer.**
*Why:* a press delivered while glyphs are still printing is consumed as a text SPEED-UP
(`src/text.c:944-955`) and is therefore NOT the dismissal press. A frame-count trigger would burn its
edge and still hang — and would have looked like "the fix does not work".
*Rejected:* "wait N frames then press", which is what a fifth guess would naturally have been.
*Free win:* `modules/text_printer.py` already wrapped this and `_listeners.py:168-170` already used it,
so this is house style rather than a new mechanism.

**Decision 2 — press B, not A.**
*Why:* `gMoveSelectionCursor` is not reset when the menu re-opens, so a stray **A** re-commits the very
move that was refused. A stray **B** cancels to the action menu, where B is inert in a single battle.
⇒ the failure mode of a mistimed B is a no-op; of a mistimed A, another refusal.

**Decision 3 — `_ki93_refused_slots` is MODULE-LEVEL.**
*Why:* MEASURED — the handler is re-entered ~5x per refusal episode, so a function-local set is
destroyed between picks. *Rejected:* the function-local design this KI had carried for a day, which
reasoned (wrongly) that the function runs once per selection phase.
*Cost accepted:* module-level mutable state in a battle module. Bounded by a single clearing rule
(an ordinary script while parked) and a collapse guard, and a stale entry costs at most one turn of
second-best move choice — against a livelock that ends the run.

**Decision 4 — fix the CLASS, not Torment.**
61 battle strings end in `\p` and every one would hang in that branch. The vocabulary covers Torment,
Disable, Taunt, Imprison, Choice-lock and no-PP. *Rejected:* keying on `BattleScript_SelectingTormentedMove`
alone, which would have left five identical hangs armed.

## 2026-09-07 — `KI-93`: the refusal memory is keyed on the POKÉMON and expires when a turn executes

**Supersedes the "Cost accepted" clause of Decision 3 (2026-09-06), which was MEASURED FALSE the same
night.** That clause read *"a stale entry costs at most one turn of second-best move choice"*. Measured:
a fainted Swellow's vetoes reached Castform and forced it into Sunny Day for two turns in a battle that
then whited out. ‼ This file is append-only and SESSION DISCIPLINE #11 sends future agents to grep it
FIRST, so the correction is recorded here rather than left only in `05-KNOWN-ISSUES.md`.

**Decision — key `_ki93_refused_slots` on `personality_value`, and drop it when a turn executes.**
*Why identity:* a battler index is a POSITION; the thing that earns a refusal is a POKÉMON. Keyed by
slot, the memory outlived its owner. `CLAUDE.md` SESSION DISCIPLINE #3 already said this in capitals
and I broke it anyway — which is why the CHECKER (`grade_ki93_drive.py` C2) is now keyed on identity
too, so the same class of error cannot pass unnoticed again.
*Why the lifetime rule:* Torment forbids the **last move used** (`src/battle_util.c:999`), and that
changes every time a turn executes. A veto is therefore true only for the selection episode that
produced it — keeping it afterwards is wrong even for the same Pokémon, and leaked across battles.
*Rejected:* clearing at battle start/end only. It would have fixed the cross-battle leak and left the
cross-turn one, and there is no cheap battle-start signal in this module.
*Rejected:* per-candidate fallback to the legacy metric — that is the scale-mixing bug from `KI-95`
in another costume.

**⭐ ALSO SUPERSEDED: "the blast radius of the BUG is exactly ONE Pokémon in the whole game"**
(2026-09-06, from `grep -c MOVE_TORMENT src/data/trainer_parties.h` = 1). True of TORMENT, false of the
DEFECT: 61 battle strings end in `\p` and every one parks the printer identically, so the hang class
covers Disable, Taunt, Imprison, Choice-lock and no-PP as well. The fix is keyed on a vocabulary of
refusal scripts, not on Torment.

## 2026-09-07 — the grind: STEP the proven trainer, never re-implement it, and never raise its ceiling

**Context.** §Ch24 needs levels. Three things blocked an unattended grind, and only one was about speed.

**Decision 1 — measure throughput before sizing the work.**
MEASURED **1032 frames/sec** (99,138 frames / 96 s, clean: logging off, single process) ⇒ L60 ≈ 34 min,
L75 ≈ 1.8 h of WALL CLOCK. `03-PUNCH-LIST.md` prices training at "~5 hours", which is **emulator
minutes at 60 fps, never converted** — every training estimate in the docs carries that unit error.
‼ My own earlier figures (112-148 f/s) were **contaminated** — census logging on and two drives
overlapping — and were ~9× low. *A measurement taken while something else is running is not a
measurement of the thing you meant.*

**Decision 2 — reuse `train_for_victory_road`; do NOT call `train_team` directly.**
*Rejected, and reading the code is what killed it:* my first driver called
`train_team(scope="whole")`. That is wrong twice — `_battler_slots()` means "not an egg, has a damaging
move", so it would have ground **Zigzagoon 36 levels and Castform 19**; and `train_team(slots={i})`
with `i != 0` is BROKEN (`KI-84`: `need` is computed BY INDEX while `_rotate_lead_safely` SWAPS, so the
next iteration sees the old lead, `need` empties, and the call returns AS IF FINISHED — 8 battles
against an estimate of 306).
*Why the wrapper:* `train_for_victory_road` already rotates each battler to slot 0, **verifies by PID
that the rotation landed**, refuses a `train_team` call that returned without raising the level,
restores the lead in a `finally`, and re-checks the HM carriers. Duplicating ~50 lines of measured
logic would have been the real risk.

**Decision 3 — STEP the target rather than raise `MAX_TRAINING_FRAMES`.**
The ceiling (`victory_road.py:508`) is a PER-MON estimate checked before a frame is spent, and its own
comment says *"do NOT raise the ceiling to make the run start"*. So the driver closes the gap in 2-level
steps: every individual call stays under the ceiling and its refusal keeps protecting us, while the
driver bounds the whole run with `--frames`, a step cap and a retry cap.
*Rejected:* editing the constant (the comment forbids it) and adding an env bypass to production
(a permanent hole for a one-night need).

**Decision 4 — the driver's `on_whiteout` LATCHES THE ABORT.**
`Ch23TrainMode.on_whiteout` only counts and logs, so `train_team`'s `_check_abort()` can never fire and
a wipe leaves the generator running against a party that is at the Poké Center instead of in the grass.
**That is the single most likely way an unattended grind loses a night.** Production `StoryMode` latches
it (`story_mode.py:1350-1353`); the harness driver was the gap, and `ch24grind` closes it.

**Decision 5 — grade on LEVELS, and capture nothing by default.**
ACCEPTANCE requires a BATTLER to have actually gained a level (`train_team` returning is not evidence —
the `KI-84` shape). `GRIND_CAPTURE` is opt-in and refuses to overwrite an existing fixture.

## 2026-09-07 — `#24-hm07teach`: TEACH the move (not relax the preflight), and place it at Segment 22b

Two choices were argued at length while fixing the wall that ended every 8-badge run in project
history. Recorded so they are not re-litigated.

### DECISION 1 — TEACH HM07. Do NOT relax `assert_ch23_preflight`.
*Chosen:* add a production teach (`ensure_waterfall_learner`) and leave the preflight strict.

**Why, and it is mechanical rather than stylistic.** `data/scripts/field_move_scripts.inc:183-186`
gates `EventScript_UseWaterfall` on `checkpartymove MOVE_WATERFALL`. With no carrier,
`dofieldeffect FLDEFF_USE_WATERFALL` never runs, `Task_UseWaterfall` is never created, and §Ch23
leg 4's `wait_for_task_to_start_and_finish("Task_UseWaterfall", "A")` burns its entire
`CLIMB_BUDGET = 3_000`. ⇒ relaxing the preflight converts a **named refusal at frame 0** into a
**silent 3,000-frame timeout ~60,000 frames later, mid-ocean**, on maps recorded as
`allow_escaping: false` with no Poké Center until Ever Grande. Walking up is impossible —
`MetatileBehavior_IsWaterfall` maps to `ForcedMovement_PushedSouthByCurrent`.
*Rejected:* **relax the preflight to a warning.** It trades a diagnosable stop for an undiagnosable
one in the worst possible place, and this project has repeatedly paid for exactly that trade.

### DECISION 2 — the teach goes at Segment **22b** (after the Juan guard), not 21b.
*Chosen:* immediately after `_guard("Gym 8 — Juan (Ch22)")` and before Segment 23.

**Why.** Badge 8 has been reached **six times in the project's entire recorded history**, all on
2026-09-07. A 21b placement would fire BEFORE badge 8, so any failure there would **erase the only
evidence that §Ch21 and §Ch22 work end to end** — the deepest signal the project has ever had. 22b
is still strictly before the preflight: nothing between it and `depart_sootopolis` touches the party.
*Rejected:* **21b (immediately after §Ch21, where HM07 enters the bag).* It fails ~40,000 frames
earlier, which is cheaper per run — but it buys that cheapness by destroying the measurement. If the
teach later proves reliable, 21b becomes the better home and this entry is the reason it was not
chosen first.
*Rejected:* **inside `do_victory_road_chapter`.** The chapter's own preflight is the thing being
satisfied; satisfying a precondition from inside the code that asserts it makes the assertion
meaningless.

⚠ **HONEST SCOPE:** this decision is about WHERE and WHETHER to teach. It does not address the HM
funnel that leaves 5 of 6 measured parties with no spendable slot — that is `#24-hm07funnel`, filed
and unbuilt, and it is the reason Change A alone rescues only one of the six.

## 2026-09-08 — An accumulate-reasons predicate must handle the EMPTY input EXPLICITLY (`team_is_ready`)

**Decision.** `victory_road.team_is_ready` now REFUSES (returns `(False, [...])`) when
`battler_identities()` is empty, instead of falling out of its loop and returning `(True, [])`.

**Why this was a real defect and not a hypothetical.** The function decides readiness by APPENDING to
`reasons` while iterating the battler set. An empty set means the loop never runs, so `reasons` stays
empty, so the party is certified READY — **absence of evidence read as evidence of absence.** §Ch23
would then return early having trained nobody.
⭐ It is the **THIRD** defect of that exact shape in this one function, both others already recorded in
its own comments: the `POKEBOT_CH23_TRAIN_TARGET=53` parameter that reached only half the function,
and the Crunch test that stopped asking at exactly L47. **All three grade PASS by never evaluating.**

**Alternatives rejected.**
* *Leave it — an empty battler set "cannot happen".* Rejected: it is reachable today (a party of only
  eggs or only `BENCH_SPECIES`), and more importantly the ONLY untested fix direction left on
  `#24-lowlevelmules` is benching by ROLE in `battler_identities`. A role predicate one clause too
  broad empties the set, and the bug would then surface as a **PASSING run** — this project's most
  expensive failure mode (§Ch15/§Ch18/§Ch19 all PASSED their own acceptance tests while stranding the
  bot). ⇒ the guard must exist BEFORE that predicate is touched, not alongside it.
* *Raise instead of returning `(False, reasons)`.* Rejected: the caller's contract is a
  `(bool, list)` tuple and callers already render `reasons`; raising would bypass their reporting.
* *Warn and continue.* Rejected: that is the silent-pass this fixes, with extra text.

**Why it is safe to ship without a drive.** The change is **fail-safe by construction** — it can only
convert a silent `True` into a loud `False`, never the reverse, so it cannot mask a real readiness.
Its no-fire arm ("a genuinely ready team must still pass") is the one that proves this.

**Evidence — raw output of `py -3.12 probe_empty_battler_guard.py`, gate #48:**
```
    ==============================================================================================
    GATE — `team_is_ready` must never grade READY on an empty battler set
    ==============================================================================================
    
      arms: 4 (1 fault, 3 no-fire — incl. 'a ready team still passes')
    
    ----------------------------------------------------------------------------------------------
    ✅ PASS — an empty battler set refuses loudly; real verdicts are unchanged.
    ==============================================================================================
```
**Fault test (the arm that matters):** with `if not battlers:` replaced by `if False:` the gate exits
**1**; with the file restored byte-identical it exits **0**. ⇒ the gate is not inert.

## 2026-09-08 — Two Gen-3 facts settled FROM THE DECOMP, and what we did NOT do with them

**Decision.** Correct two false premises in sandbox code (comment/docstring only) and change NO
behaviour on the strength of them.

**Fact 1 — the whiteout respawn is armed by ENTERING a Poké Center, not by healing.**
`setrespawn HEAL_LOCATION_*` is the first statement of every Center's `MAP_SCRIPT_ON_TRANSITION`
handler, which `LoadMapFromWarp` runs during map load before the player can move
(`src/overworld.c:807/860`). `data/scripts/pkmn_center_nurse.inc` contains **no** `setrespawn` — the
nurse only does `HealPlayerParty`. There is no "registration" concept and no badge/flag gate.
⇒ our `ai-research-notes/2026-09-03-ch23-CHAPTER-BUILD-SPEC.md` already had this right;
`ai-research-notes/concept-notes-c10.md` has it WRONG (*"Set by healing at a Pokémon Center or Mom"*).

**Fact 2 — Emerald HALVES all money on a whiteout.** `src/overworld.c:358`
`DoWhiteOut() { ... SetMoney(&money, GetMoney(&money) / 2); ... }`. `MoneyLoss` has zero hits in
`pret/pokeemerald`; the level×badge multiplier table is FireRed's
(`pokefirered/src/overworld.c:227`). ⇒ `victory_road.py:446` was right, `story_mode.py`'s
boss-training comment was wrong, and `#24-regimeb-noescalation` recorded the contradiction as OPEN.
It is now settled.

**⛔ WHAT WE DELIBERATELY DID NOT DO, and why it is the whole decision.** Fact 2 is the stated
justification for boss-training mode, which fires **1,477 times** across two batches — each firing a
deliberate loss, i.e. a halving. It is *tempting* to conclude the strategy is ruinous and disable it.
**Rejected:** money is not logged anywhere, and the obvious proxy is unusable (`provision_poke_balls`
writes *"too low on money"* to `context.message`, a UI field, not to `console.print` — a zero count
means NOT LOGGED). The other half of the same comment is TRUE (a lost attempt that KOs two boss mons
really does pay ~1,200 XP vs ~145 for a local wild, and Gen 3 keeps mid-battle XP through a whiteout),
so the strategy may still be correct at half money.
⇒ **A corrected fact is not a licence to act. Filed as `#24-bosstrainingeconomics`, whose FIRST
deliverable is an instrument (log money at run start / whiteout / mart), not a fix.**

**Alternatives rejected for Fact 2:** *disable boss-training* — unmeasured, and it is the only
loss-adaptation the late game has. *Cap it at N engagements* — a number with no evidence behind it is
the same guess wearing a threshold.

## 2026-09-08 — Where the "run it bare" guarantee stops: the runner and its REGISTERED gates

**Decision.** Guard stdout in `run_gates.py` and in every gate it registers (plus `audit_encoding.py`),
and NOT in the ~120 other tools under `tools/story-dev`.

**Why a boundary at all.** A first attempt swept every file that prints non-ASCII — **155 of them** —
which is an unreviewable diff and touches dozens of one-off recon probes that only ever run from an
agent's shell with `PYTHONUTF8=1` already set. Rigour that produces a 155-file diff for a two-file
blocker is not rigour.

**Why THIS boundary.** The tree already draws it: `run_gates.py`'s `GATES` list *is* the set of tools
meant to be run by someone other than their author — by the suite, by a reviewer, by a future agent
following the handoff. Those must survive a bare invocation. An ad-hoc probe written for one
investigation has an author who is present and a shell that is configured.

**Alternatives rejected.**
* *Sweep everything* — rejected above. ⛔ It also hides the signal: 155 changed files means nobody
  reads any of them.
* *Fix only `run_gates.py`* (the literal blocker) — rejected: the same bug was already measured in
  three registered gates, so the instance-only fix had just been demonstrated to fail. The registered
  set is the smallest scope that closes the class for anyone who is not me.
* *Rely on `_GATE_ENV` alone* — rejected, and this is what the kick-back proved: a child environment
  cannot help the parent, and the parent is the thing a human runs.

**Verification standard adopted with it:** a tool claimed to work bare is tested bare —
`env -u PYTHONUTF8 PYTHONIOENCODING=cp1252` — not with the author's habitual flags. That is now the
settling command for anything in this class.

---

## 2026-09-10 — `#24-dexhunt`: four design rulings on the catching fence

**1. THE DEX-CATCH BALL FLOOR IS A SEPARATE CONSTANT FROM `resource_blocker()`'S, AND MUST STAY SO.**
*Chosen:* `DEX_CATCH_BALL_RESERVE = 10`, checked in addition to (never instead of) the pinned
`counter_hunt.resource_blocker()` verdict.
*Rejected:* reusing the pinned floor of 1 alone. The 2026-07-31 ruling says reuse that predicate
rather than writing a second one that can drift — and this DOES reuse it, passing its verdict
through verbatim. But the floor of 1 encodes *"the last ball is reserved"* for a catch the run
CANNOT PROCEED WITHOUT. A dex catch is discretionary. Sharing one floor between a mandatory and a
discretionary consumer lets the discretionary one starve the mandatory one, and `counter_hunt.hunt()`
arms only AFTER its journey (`:471` check, `:488` travel, `:510` arm) so no boolean can see it coming.
‼ *Honest limit:* 10 is sized to `HUNT_SPIN_BUDGET_FRAMES`' own "roughly 12 expected meetings"; it is
a JUDGEMENT, not a measurement — balls-per-catch has never been logged here. Re-derive it once
`balls=` telemetry has a batch behind it.

**2. THE FENCE IS DELIBERATELY NARROWER THAN THE RULING IT SERVES.**
*Chosen:* admit post-badge catches ONLY at a full party.
*Rejected:* the ruled policy in full (catch every unseen species unless something blocks), which
would admit at party 4 and 5, where `resource_blocker()` returns None and nothing blocks.
*Why:* `#24-partycap` MEASURED that consuming party slots costs 36 points of finish rate
(52.0% -> 15.8%), the entire loss on one badge rung, with 10 of 16 non-finishes reading *"No party
mon can learn Surf and the party is full"*. The empty slots are the RUNWAY that HM and counter
catches land on. At a FULL party there is no runway left to consume, so the catch is pure upside.
⛔ Recorded as a NARROWING, not as the ruling implemented — `#24-dexhunt` stays OPEN with the
party<6 case named as unbuilt, so nobody reads the item as shipped and drops the residual.

**3. THE DECISION IS A PURE FUNCTION; THE ADAPTER DECIDES NOTHING.**
*Chosen:* `decide_dex_catch(...) -> (catch, reason)`, with `_should_catch` reduced to reading live
state and reporting.
*Rejected:* an `if` chain inside `_should_catch` (the shape it had).
*Why:* the handoff says no cheap fixture test exists for this item. That is true of EFFICACY only.
Purity makes CORRECTNESS provable offline in milliseconds — the same move that made
`rank_replacement` testable after `choose_new_lead_after_faint` had shipped THREE index-space bugs
that each needed a ROM, a live battle and a staged faint to see. It also makes unshippable the
failure this feature nearly had: the draft spec called `counter_hunt.hunt_active()`, which does not
exist, and the blanket `except` would have swallowed that `AttributeError` forever.
*Corollary ruled at the same time:* the predicate returns a REASON, never a bare bool — the
2026-07-31 ruling requires that a skip SAY SO, and a bare bool makes "declined" and "crashed" the
same observation.

**4. THE MID-BATTLE BAIL-OUT IS DEFERRED, AND MUST NOT BE BUILT INTO `StoryCatchStrategy`.**
*Chosen:* bound ENTRY with a pure `party_healthy` conjunct now; file `#24-dexcatch-battlebail`.
*Rejected:* adding a faint-aware bail-out to `StoryCatchStrategy` in this commit.
*Why:* `StoryShinyCatchStrategy` INHERITS from it, and the shiny rule is an explicit user directive
(2026-07-22): attempt until success, whiteout, or out of balls. A bail-out there would silently
overrule a user directive. The surviving shape is a dex-ONLY subclass returned by the fence's call
site, leaving pre-gym-1 and shiny paths byte-identical. It is battle-strategy internals — where
`KI-18`/`KI-34`/`KI-66`/`KI-95` all lived — so it gets a probe first, never a drive first.
⛔ Recorded so it is not re-litigated: this deferral is a claim with an expiry, not a dismissal.

---

## 2026-09-10 — §Ch24's entry marker: THREE DESIGNS KILLED, and the question was the wrong one

**Context.** §Ch24 (Elite Four) is defined (`chapters.py:287`) but NOT wired. `victory_road.py`'s
`ch23_chapter_done()` and `06-DECISIONS-LOG.md` 2026-09-05 both record a forward dependency: *"when
§Ch24 is built it MUST set its own progress marker so §Ch23 is not re-entered."* A 4-angle decomp +
code + routing round with adversarial verification was run to settle what that marker should be.

### ⛔ D1 — gate on `FLAG_SYS_GAME_CLEAR`. **KILLED, twice over.**
Decomp: set in exactly ONE place (`src/post_battle_event_funcs.c:30`, inside `GameClear()`), never
cleared anywhere in the tree — genuinely write-once. **But only reachable via `special GameClear` at
`EverGrandeCity_HallOfFame/scripts.inc:54`/`:61`**, i.e. after Wallace AND after the Hall of Fame
cutscene. During Sidney→Drake→Wallace it is False. ⇒ it cannot gate the window that matters.
‼ **AND IT IS ALREADY THE READOUT MILESTONE** — `chapters.py:288` grades §Ch24's readout on it. Using
it as the GATE would collapse the distinction `ch23_chapter_done`'s own docstring forbids collapsing:
*"the readout answers 'which chapter is this run in'; the gate answers 'may the next segment start'.
Both are correct. Do not collapse them."*

### ⛔ D5 — gate on `FLAG_DEFEATED_ELITE_4_*`. **KILLED — decomp-confirmed whiteout-fragile.**
`EverGrandeCity_HallOfFame_EventScript_ResetEliteFour` (`data/event_scripts.s:628-634`) clears all
four flags AND `setvar VAR_ELITE_4_STATE, 0`. It is called from exactly TWO sites: the WIN path
(`data/scripts/hall_of_fame.inc:7`) and the LOSS path (`EventScript_WhiteOut`,
`data/event_scripts.s:586`, reached unconditionally from `DoWhiteOut`, `src/overworld.c:358-365`).
⇒ the punch list's warning was right, and is now decomp-cited rather than agent-reported.

### ⛔⛔ D-NEW — gate on `FLAG_ENTERED_ELITE_FOUR`. **THE RECOMMENDED SURVIVOR, AND THE ADVERSARY KILLED IT.**
Its decomp credentials are perfect and were verified twice: `0x107`, set at
`EverGrandeCity_PokemonLeague_1F/scripts.inc:70` when the door guards step aside, with **zero**
clear sites tree-wide. It is the one permanently-set marker in the whole league.
⛔ **And it is the WRONG SHAPE, by this project's own ⭐ rule.** It is set *before the first fight*,
and a mid-gauntlet whiteout leaves it SET. ⇒ **it is REACHED BY FAILING.** Gating on it re-creates
the exact 2026-09-05 defect — the bot advances with the basket spent — **relocated into the
five-fight no-nurse gauntlet, where it is strictly worse than the original.**
⇒ *A POSITION CAN BE REACHED BY SUCCEEDING OR BY FAILING. A WORK PRODUCT CANNOT* — and a flag set by
walking through a door is a position wearing a flag's clothing.
‼ **THIS DESIGN WAS ALREADY WRITTEN DOWN** (`ai-research-notes/2026-09-07-ch24-elite-four-BUILD-SPEC.md:70`,
`2026-09-08-ch24-league-RECON.md:39`) and my prior-art check reported NO prior art — because
`precheck_prior_art.py` did not search `ai-research-notes/`. Fixed the same day; see `07-CHANGELOG.md`.

### ⭐⭐ THE REFRAMING — the question itself was wrong
Chasing a marker assumes §Ch23 re-entry after a mid-gauntlet whiteout is a BUG TO SUPPRESS. Trace the
state a whiteout actually leaves: party healed, half the money gone (`DoWhiteOut` → `SetMoney(.../2)`),
items partly spent, all four E4 flags cleared, `VAR_ELITE_4_STATE` zeroed, respawn OUTSIDE the League.
⇒ **that run genuinely needs §Ch23's leg 10 (heal) and leg 11 (restock) again.** Re-entry is CORRECT.
⇒ **What is actually broken is not the predicate. It is that the re-entry cannot succeed:**
  * leg 11 cannot afford the basket (₽54,300 needed; the gauntlet leaves ~₽1,741, then a whiteout
    halves it again), and
  * leg 4 FIRES on re-entry and attempts an ocean crossing *from inside the League*, because
    `at_ever_grande_top()` is False at the League door — a latent routing bug the marker would have
    HIDDEN rather than fixed.
    ⛔⛔ **THE "because" IN THE LINE ABOVE IS WRONG — SEE THE CORRECTION ENTRY AT THE END OF THIS
    FILE (2026-09-10, later).** `at_ever_grande_top()` was **already True at the League door**
    (`EG_LANDING = (18,55)`, apron `(18,6)`, `6 <= 55`). The real hole was the League INTERIOR maps.
    The bug and the DECISION below are unaffected; only the mechanism was wrong. FIXED + gated #52.
    ‼ *Marked in place rather than rewritten: `06` is append-only, so not one word above was
    changed — but an append-only file still must not silently mislead the reader who lands HERE,
    and `03-PUNCH-LIST.md` points people at this very entry.*
⇒ **DECISION: do NOT ship an entry marker yet.** The next work on §Ch24 is (a) make §Ch23 re-entry
survivable from the League door (leg 4's precondition), and (b) decide the MONEY policy for a
post-whiteout re-stock. A marker chosen now would paper over both.
⚠ Recorded so it is not re-litigated: `FLAG_ENTERED_ELITE_FOUR` is still the right marker for
*"the gauntlet was begun"* if a future design needs that fact — it is only wrong as a **completion
gate**. Do not re-derive its decomp credentials; they are above.

---

## 2026-09-10 (later) — CORRECTION to the §Ch24 entry-marker entry above: its leg-4 mechanism was wrong

⛔ **READ THIS BEFORE ACTING ON THE PRECEDING ENTRY.** That entry (same date) closes with:

> "leg 4 FIRES on re-entry and attempts an ocean crossing *from inside the League*, because
> `at_ever_grande_top()` is False at the League door — a latent routing bug the marker would have
> HIDDEN rather than fixed."

**The conclusion is right. The "because" is FALSE, and the "because" is what a builder acts on.**

MEASURED, from the constants: `EG_LANDING = (18, 55)` (`victory_road.py:130`) and the League door
apron is `(18, 6)` (`victory_road.py:374`). The predicate was `_on_map(EG) and y <= 55`, and
**`6 <= 55` was ALREADY True** — so leg 4 skipped correctly at the door, and always had.

**The real hole is one map further in.** Every League room is its OWN map
(`map_data.py:1037-1051`), so `_on_map(EVER_GRANDE_CITY)` is False *inside the building*, and the
League is not in `VICTORY_ROAD_MAPS` either ⇒ both of leg 4's guards read False and the chapter aimed
a SURF LANDING at a bot standing indoors. FIXED 2026-09-10 in the PREDICATE (its two call sites must
mirror), gated as **#52** `probe_league_leg4_guard.py`, whose `=nofix` arm pins BOTH halves: **C1+C2
red, C3-C7 GREEN** — i.e. the interior was broken and the door never was.

‼ **WHY THIS CORRECTION EXISTS AT ALL, and it is the reusable part.** `03-PUNCH-LIST.md` tells the
reader *"Read `06-DECISIONS-LOG.md` 2026-09-10 before touching this."* I corrected the punch list and
appended the corrected mechanism to `07-CHANGELOG.md` and `08-MISTAKES.md` — and left the wrong claim
standing in the one file my own pointer sends people to. A Tier 1 reviewer caught it.
⇒ **P5, for the THIRD time in one session: a fact lived in FOUR places, I updated three, and the
missed one was the one under a "read this first" pointer.** Updating the halves you can NAME is the
most dangerous state, because the pair check then returns PASS.
⇒ ⭐ **STANDING RULE, ADOPTED NOW: when a claim is CORRECTED, run the `staleness-sweep` skill before
committing.** It searches the whole tree by MEANING rather than by exact wording, which is precisely
what a hand-grep for my own phrasing cannot do — I grepped for the numbers I had changed, not for the
sentence that asserted the old mechanism in different words.

---

## 2026-09-10 — Post-Winona loss adaptation: grass-less configs, and why `#24-maintain` cannot be built yet

**Decision.** Wire the EXISTING `_prepare_for_fight` machinery to Tate & Liza (badge 7) and Juan
(badge 8) with **grass-less** `*_fight` configs, copying the full three-line call shape every other
boss uses. Gate #53.

**Rejected: wiring `best_training_grass(mon_level)` (i.e. building `#24-maintain`).** It is the
per-mon maintenance primitive, it is already written and gate-tested, and it has **zero production
call sites** — so it looks like the cheapest possible fix. It is not buildable:
`training_areas.TRAINING_GRASS` tops out at **ROUTE121, L25-28**, while the post-Winona opposition is
**L41-46** and §Ch23's target is **L47**. Wiring it would send a L40 mon to L28 grass. Arithmetic on
the only tabled ground a post-Winona picker could choose: L40→L47 costs ~285,000 frames solo, ~570,000
with `set_swap_train(True)`, against a **250,000** ceiling.
⇒ ⭐ **THE PRIMITIVE IS NOT THE BLOCKER; THE TABLE IS.** `#24-maintain` is blocked on
`TRAINING_GRASS` gaining entries above L28 — a DATA task (sweep + verify late-game grounds), not a
wiring task. Recorded so the next agent does not re-derive "just call the function".

⚠ **SCOPE CLARIFIED 2026-09-11 — THIS RULING STANDS; see the dated entry at the END of this file.** In short: what is rejected above is LATE relocation to the BOSS's target level, and that stays rejected. A second, cheaper case (EARLY maintenance to `target - TRAIN_CATCHUP_GAP`, on a ground keyed to the LAGGARD's level) was measured separately and built. ⛔ This is NOT permission to add a `grass` key to a late-boss config — gate #53 case C2 exists to make that argue with the data first.

**Rejected: `grass` keys on the new configs.** Same measurement. ⛔ And do not "helpfully" add one
later — gate #53 case C2 exists to make that argue with the data first.

**Scope: Wally is deliberately NOT included.** His party was pinned from the decomp at the same time
(`sParty_WallyVR1`: Altaria 44 / Delcatty 43 / Roselia 44 / Magneton 41 / Gardevoir 45) but he lives
INSIDE §Ch23, not `_play()`, so wiring him needs a different mechanism. Recorded so the band does not
have to be re-fetched.

⚠ **What this does NOT decide:** whether adaptation raises the finish rate. Correctness is gated;
efficacy is a frequency question and needs a batch.


---

## 2026-09-11 — `#24-maintain` is TWO items in one slug; the early half is buildable and the late half stays dead

**Decision.** Build **early/mid-game per-mon maintenance**: at the top of `_prepare_for_fight`, lift
any battler the exclusion at `story_mode.py:2377` is about to abandon back up to `catchup`, training
it at a ground keyed to **its own** level. ⛔ Do NOT touch the late-game case — the 2026-09-10
rejection above stands unaltered.

**Why this is not reopening a settled question.** I found that ruling by running
`precheck_prior_art.py`, which is what it is for. The ruling's case and this one differ in the two
variables its arithmetic is most sensitive to, and the difference is MEASURED, not argued:

| | target | ground | frames | vs 250,000 |
|---|---|---|---|---|
| **ruled DEAD 2026-09-10** | the BOSS's level (L47) | the only tabled ground, ROUTE121 wild 28 | **285,167** | ⛔ over |
| **built 2026-09-11** | `target - 6` (`TRAIN_CATCHUP_GAP`) | keyed to the laggard's level | **4,299 – 63,052** | ✅ under |

⭐ **The instrument was CONTROLLED before it was believed:** it reproduces the 2026-09-10 entry's own
figure (285,167 vs "~285,000") using the same constants `estimate_frames_to_level` uses. A model that
could not reproduce the ruling would have been the thing to doubt.

**Why the seam is `_prepare_for_fight` and not a chapter loop.** `story_mode.py:2376-2377` is where
the laggard is abandoned:
```python
catchup = target - self.TRAIN_CATCHUP_GAP        # 6
to_train = {i for i in battlers if party[i].level >= catchup}
```
A mon more than 6 below the boss target is excluded from prep training entirely, so it can never
close the gap while the target rises with every badge. ‼ **That exclusion is CORRECT** — training it
to the boss's level is the unwinnable grind the 2026-09-10 ruling killed. ⇒ the fix is not to relax
it but to stop the mon reaching it, at the one place that already knows the number.

**Rejected: `train_team(slots={i})`.** KI-84 — that path computes `need` from SLOT INDICES and then
permutes the party via `_rotate_lead_safely`, so it silently no-ops. Use `scope="lead"`
(`early_game.py:2040`), which stops on `_lead_level()` and never touches the broken path.

**Rejected: a gap measured against the party MAX.** The exclusion's own quantity (`target - 6`) is
available at the seam, is the number that actually decides, and needs no new constant.

**Rejected: mapping a Meteor Falls spin tile to raise the table.** Separately refuted 2026-09-11 —
B1F is sealed behind Waterfall, which is badge 8. See `07-CHANGELOG.md` "METEOR FALLS B1F IS SEALED".
⇒ **`TRAINING_GRASS` above L28 remains a genuine DATA task and remains unstarted**; the 2026-09-10
ruling's closing sentence is still the live guidance for the LATE case.

---

## 2026-09-12 — `#24-maintain` stays DEFAULT-OFF after its A/B, and the A/B is kept rather than re-run

**Decision.** `POKEBOT_MAINTAIN` remains `0`. The unreachable-ground fix and gate #57 ship anyway.

**Why.** The 2026-09-12 two-arm batch measured the feature as net-harmful (median run duration **5.35 min
ON vs 35.18 min OFF**; **0.72 badges won per run vs 2.25** (n=945 badge events); 406 ARM-ON-only run deaths). The fix removes the
mechanism that caused those deaths, but *removing a harm is not the same as showing a benefit*, and
the benefit case now rests on a metric the same batch showed to be **confounded** (laggard-gap
episodes are not comparable across arms with different run lifetimes).

**Alternatives rejected.**
* *Flip it ON now that the cause is fixed.* Rejected: that reasons from a repaired mechanism to an
  outcome, which is exactly the inference this batch just falsified. The flip is its own reviewable
  change with its own A/B — never a side effect of a bug fix.
* *Delete the feature.* Rejected: the laggard it targets is real and measured (35% of badge moments
  carried a mon 15+ levels behind). The A/B indicted the *implementation*, not the premise.
* *Re-run the A/B immediately with the fix in.* Deferred, not rejected — and deliberately NOT
  started unattended. ⛔ **The next A/B must not reuse the old primary metric.** Run length and
  badge-rate are the honest comparators; laggard-gap-per-batch is not, until it is normalised
  per-run. Filing that as the precondition so the next session does not re-run a confounded design.

**Expiry.** This deferral expires the moment someone wants the flag ON: that request requires a
fresh two-arm batch reporting **median run length and badge rate**, not episode counts.

**⛔ DO NOT RE-RAISE "why not just train the laggard to the boss's level?"** — ruled 2026-09-10,
with arithmetic (L40→L47 = 285,167 frames against a 250,000 ceiling). Unchanged by this entry.

---

## 2026-09-12 (09:03) — `#24-maintain`: the benefit question is ANSWERED (no), and the flag stays OFF

**Decision.** `POKEBOT_MAINTAIN` remains `0`. This supersedes the *deferral* recorded earlier today
by ANSWERING it, not by extending it.

**What changed.** That entry set an expiry: *"that request requires a fresh two-arm batch reporting
median run length and badge rate, not episode counts."* The batch ran (32 lanes x 120 min per arm,
2026-09-12). The fix is fully vindicated — the 406-death family is **0**, and the fail-soft handler
was observed abandoning 77 errands in production rather than killing the runs. **But with the harm
removed, the feature measures as NEUTRAL:** badges/run 2.055 vs 2.030, derail rate 64.8% vs 68.0%.

**Why OFF rather than ON.** A neutral feature is not free: it adds a training detour, a lead
rotation, and ~295 extra decision points per 91 runs, and it measurably ELEVATES two residual
failure modes (heal-nav derails 15 vs 3; ROUTE111 derails 74 vs 36). ⇒ the burden of proof sits with
turning it on, and nothing has discharged it.

**⛔ WHAT WOULD CHANGE THIS RULING — stated so it is not re-litigated from intuition.** Not a longer
batch on its own: at n≈100 runs/arm this design cannot see a modest effect, so the honest next step
is (a) fix the heal-nav residual, then (b) a batch powered for the effect size actually worth
having. **If the answer to "how much better should this make the bot?" is "a few percent", this
feature is not worth turning on at any sample size** — that is the question to settle FIRST, before
spending another machine-night.

**Alternatives rejected.** *Turn it on because the fix worked* — rejected: the fix removed a harm the
feature itself created; that is a return to baseline, not evidence of value. *Delete it* — still
rejected: the laggard premise is measured, and the code is inert at zero cost while OFF.

---

## 2026-09-12 (user ruling) — ‼ `POKEBOT_MAINTAIN` WILL BE TURNED **ON**. This SUPERSEDES the two “stays OFF” entries above.

**Decision (the USER’s, not mine).** After being shown the full measurement — including that the
feature is NEUTRAL and that it aggravates two other failure modes — the user ruled: *“I like it, lets
use the top up.”* ⇒ the feature ships ENABLED.

⛔⛔ **DO NOT RE-RAISE THE VALUE QUESTION.** It was asked twice, measured twice (32×310 and 32×120 per
arm), put to the user in plain terms WITH the recommendation to leave it off, and answered. A future
agent rediscovering “this feature measures neutral, why is it on?” has found the RULING, not a defect.
The reasoning is recorded here precisely so that agent stops instead of re-running a machine-night.

**What I recommended and why it was overruled.** I recommended OFF: badges/run 2.055 vs 2.030 and
derail rate 64.8% vs 68.0% cannot be separated from neutral at n≈91 runs/arm, and the feature
elevates heal-nav derails (15 vs 3) and ROUTE111 derails (74 vs 36). The user’s call is a judgement
about what the bot should DO — prevent a Pokémon being permanently abandoned — not a claim about the
statistics, and that judgement is theirs. ⇒ **I argued the point once, in plain language, and then
executed the decision.** That is the correct shape; re-arguing it in code review would not be.

**‼ THE CONDITIONS I ATTACHED, AND WHY THEY ARE NOT NEGOTIABLE-AWAY.** Turning the feature on
MULTIPLIES the two failure modes it aggravates — the heal-nav run-killer runs **5× more often** with
maintenance enabled. Shipping ON before fixing that would knowingly ship a run-killer to the user
who asked for the feature. ⇒ **ORDER: (1) fix the heal-nav defect; (2) resolve or bound the ROUTE111
frequency; (3) flip the default as its OWN reviewable change; (4) verify by batch that ON is SAFE.**
⭐ Note step 4’s question has CHANGED: it is no longer *“is the feature better?”* (asked and answered)
but *“does enabling it make runs WORSE?”* — a safety question, with a different acceptance bar. The
batch must show ON ≤ OFF on run-enders, not ON > OFF on badges.

**Alternatives rejected.** *Flip it now and fix the residuals after* — rejected: the residuals are
elevated BY this feature, so enabling first is the one ordering that guarantees the user experiences
them. *Keep arguing for OFF* — rejected: the user reaffirmed after hearing the case; per this
project’s own conduct rule, a reaffirmed instruction is a decision to execute, not to re-litigate.

---

## 2026-09-12 — `#24-maintain-staletarget`: leave the ordering alone (measured zero cost; reordering has a CERTAIN harm)

**Decision.** Do NOT move `_maintain_lagging_battler(target)` after the reactive target escalation.
The item is DOWNGRADED and stays open only as a watch condition.

**Why.** The ordering defect is real (`story_mode.py:2613` runs the errand with the pre-escalation
target; `:2763`/`:2780` then raise it and `:2803` recomputes the exclusion floor). But measured across
**1,298 runs and BOTH escalation paths** (3,132 boss-mode + 67 heavy), **no approved errand ever spent
frames that the escalation then wasted**: of the 23 approvals adjacent to an escalation, 22 were
preempted by the ROTATION guard and 1 by a navigation failure.

**The decisive argument against fixing it is a NEW harm, not the absence of an old one.**
`_prepare_for_fight` has early-return paths (counter-ladder / second-wind) that skip the
READY-THE-BATTLERS section. Maintenance currently runs BEFORE them, so a laggard is topped up even on
attempts that return early. Reordering would remove maintenance from exactly those attempts — the
hardest bosses — a silent, structural regression. ⇒ trading a zero-occurrence defect for a
certain-mechanism regression is a bad trade.

**Alternatives rejected.**
* *Move the call after escalation* — rejected above.
* *Pass the escalated target to the errand* — rejected for now: the escalated target is not known at
  `:2613` without restructuring the function, and the defect it would fix has zero measured cost.
* *Close the item outright* — rejected: it is unreachable only by accident. Three unrelated gates
  screen it and none was designed to.

**⚠ WATCH CONDITION (the reason this stays open).** Re-run
`tools/story-dev/probe_staletarget_cost.py` after ANY change to `MAINTAIN_MAX_FRAMES` (150,000), to
the rotation guard, or to `decide_maintenance`'s refusal ORDER. Raising the frame budget is the most
plausible way to unmask this, and it is a change someone will reasonably want to make when arguing
the top-up should do more.

**⛔ DO NOT RE-DERIVE THIS FROM THE CODE ALONE.** Reading `:2613` against `:2780` makes the defect look
expensive and obvious; it is neither. The measurement is what settles it, and it is committed.


## 2026-09-13 — `#24-e4healing` step 3: four design choices in the in-battle item policy

**Decision 1 — a SIBLING function, not an extension of `choose_healing_item`.** *Rationale:* that
policy expresses every rule in HP (`missing`, `effective_heal`, `worst_hit_taken`); a status cure
restores no HP, so folding it in would make `effective_heal` return 0 for an item we DO want —
teaching the HP policy to lie. *Rejected:* one function with a mode flag, putting two unrelated
rule-sets behind one branch.

**Decision 2 — cure ONLY `{Sleep, Freeze}`.** *Rationale:* both PREVENT ACTING, so the turn spent
curing is strictly better than the turn lost — the trade is FREE. Poison/Burn/Paralysis chip but
still let the mon attack, so curing them trades a certain attack for a little HP, which rule 1 of
`battle_items.py` already rejects. Gen-3 freeze additionally never self-thaws. *Rejected:* curing
any status. ⛔ Widening this set is a NEW decision — gate #59 asserts the set's exact contents so it
cannot widen silently.

**Decision 3 — `allow_revive` defaults to `False`.** *Rationale:* a cure targets the ACTIVE battler
(the index the HP path lands 19/19 at slot 0); a REVIVE targets a FAINTED NON-ACTIVE member — the
index space behind KI-18/KI-34/KI-66 (`KI-100`). The POLICY is sound either way; the CALLER's aim is
unproven. A safe default costs the eventual probe-backed caller one keyword; an unsafe one costs a
silent regression. *Rejected:* default `True` with a docstring warning — a Tier 1 reviewer noted
nothing in the signature would then stop a future caller using the default. ⛔ The flag is checked at
the REVIVE branch, never at the top, so it can never disable the status cure as well.

**Decision 4 — accept the status as a string, an enum, or `"StatusCondition.Sleep"`.** *Rationale:*
MEASURED that two of those three forms returned None — silently no cure, no error. *Rejected:*
requiring `.name`, i.e. trusting a convention whose violation is invisible.

⚠ **DELIBERATELY NOT DECIDED HERE:** whether to WIRE any of it. `story_mode.py:679` still filters
`parameter > 0`; wiring changes every trainer battle in the game and needs its own reviewable change
and its own drive. Step 3 is half-shipped and labelled as such.


## 2026-09-13 — `#24-e4healing` step 3, the WIRING: three more choices

**Decision 5 — the HP policy is asked FIRST; the status policy only if it declines.** *Rationale:* an
HP emergency outranks a status cure — a fainted Pokémon cannot benefit from being awake. *Rejected:*
asking the status policy first, which would spend the shared per-battle budget on a cure while the
mon was about to faint.

**Decision 6 — the status policy receives the UNFILTERED `medicine` list.** *Rationale:* `parameter`
is a union type; `battle_use is Healing` is the KIND check and already excludes a Repel. Passing the
`parameter > 0` list would re-create the exact bug this item exists to remove. *Rejected:* one shared
list — it is what made Full Heal / Revive / Antidote unusable in the first place. ⛔ Gated statically.

**Decision 7 — a status cure is judged by STATUS CHANGE, never by HP delta, and that check runs
BEFORE the HP detector and returns early.** *Rationale:* the HP detector is proven code with three
measured iterations behind it; a new feature must not modify it. *Rejected:* teaching the existing
detector about kinds in place — a larger edit to the most safety-critical branch in the method, for
no additional benefit. ‼ A Tier 1 reviewer found this interaction; without the fix, two successful
cures would have disabled ALL item use for the remainder of an Elite Four battle.

⚠ **SCOPE, stated deliberately:** cures are inside the pre-existing `BattleType.Trainer` gate, so
wild battles are untouched — the same scope the HP policy has always had.


---

## 2026-09-15 — Fix the DRIFT METER, not the file's line endings (`#24-driftreduction`)

**Decision.** Teach the three drift instruments to hash newline-NORMALISED content and to report
line-ending-only differences as their own, separately-labelled category. Leave every file's bytes on
disk exactly as they are.

*Rationale:* a CRLF/LF difference in a `.py` file cannot change behaviour, and git already agrees —
both copies resolve to one blob under `core.autocrlf=true`. The meter was the only thing that
disagreed, and four documents call that meter *the authority*.

*Rejected — flip `higher_level_actions.py` to LF.* This is what the phantom invites, and it is
exactly what the 2026-09-14 session deliberately avoided: the promotion preserved custom's CRLF so
git shows its **91 real added lines** instead of a **1,173-line ending flip**. That call was right;
reversing it would trade a reviewable diff for a green number. ⛔ The *"do NOT fix it by flipping
endings"* advice in `04-HANDOFF.md` therefore STANDS.

*Rejected — `promote.py --go` it.* `shutil.copy2` would copy bytes git considers identical, so the
resulting commit would contain nothing — the no-op promotion this tool's own docstring says it
refuses to make because it *"inflates a commit and lies"*.

*Rejected — a repo-wide `.gitattributes` `text=auto eol=lf` normalisation.* It is the textbook fix
and it is wrong HERE: it would rewrite line endings across the whole tree, **including
`40cakes repo/pokebot-gen3/`, the PRISTINE upstream mirror that the project's own rules say must
never be edited** and that only changes via `git subtree pull`. A one-line convenience is not worth
touching a mirror whose value is being byte-faithful to upstream.

*Rejected — leave it and keep the prose caveat.* It had already been hand-copied into three places
in one file and re-stated in `DIVERGENCE-LOG.md`, and it was on its second day. `CLAUDE.md` rule 6:
a rule already restated that many times is evidence that prose failed — write the gate instead.

‼ **SCOPE, stated deliberately:** the normalisation applies to the fork-drift COMPARISON only. It
does not change how any file is written, read, committed, or executed, and `_raw_digest` preserves a
byte-exact check at the one site whose claim is literally *"byte-identical"* — the post-copy
verification inside a real promotion, which must stay strict.


---

## 2026-09-16 — USER RULING: the post-whiteout money policy is **SPEND DOWN BEFORE ENTERING**

**Decision (the user's, made 2026-09-16 after being shown four options).** Before the bot walks
through the Pokémon League door, it converts as much spare cash as possible into items. It does NOT
gain a post-whiteout re-stock behaviour, an attempt cap, or a re-earning trip.

**⭐ THE RATIONALE, AND IT IS A MECHANIC, NOT A PREFERENCE: items survive a whiteout; money does
not.** `DoWhiteOut` (`overworld.c:358`) does `SetMoney(money / 2)` and touches nothing in the bag.
⇒ cash left in the wallet at the door is **the only thing a whiteout can actually take**, and today
the bot walks in holding ₽1,741 idle against a ₽54,300 basket. Spending it converts a halvable asset
into an unhalvable one. It is also the cheapest of the four to build — it extends the EXISTING basket
purchase in `victory_road.py` rather than adding a post-whiteout code path, and it needs nothing
driven at the League 1F mart, which has never been driven.

**⛔ THE THREE REJECTED OPTIONS — OFFERED AND DECLINED. DO NOT RE-RAISE THEM.** *(Recorded per
`CLAUDE.md` rule 11: this log exists so a question is never asked twice, and that applies to a
question answered NO just as much as to one answered YES.)*
* **Adaptive re-stock** (relax *refuse-rather-than-under-buy* after a whiteout, buying the best
  partial basket the halved wallet affords). Declined.
* **Attempt cap** (allow N gauntlet attempts, then end the run). Declined.
* **Fly out, re-earn, return** (grind back to the full ₽54,300 and re-enter). Declined.

**⚠ A CONSEQUENCE THE USER WAS SHOWN AND ACCEPTED, recorded so it is diagnosed rather than
re-litigated if it bites.** Without an attempt cap, a whiteout loop has **no floor**:
`EventScript_WhiteOut` calls `ResetEliteFour`, which clears all four `DEFEATED_ELITE_4_*` flags and
sets `VAR_ELITE_4_STATE` to 0 (verified at the decomp, `data/event_scripts.s:585-586, 628-634`), so
every whiteout costs the ENTIRE gauntlet and the next attempt faces the same four fights with half
the money again. ⇒ **If an unattended run is ever seen looping in the League, this is the known
cause and it is BY DESIGN — the fix is a new ruling from the user, not a unilateral cap.**

**NOTES FOR WHOEVER BUILDS IT** (none of these are new decisions; they are constraints already
measured and recorded in `victory_road.py`):
* ⛔ **Order is load-bearing.** The shop's quantity selector caps at `min(money / price, 99)`
  recomputed from CURRENT money per transaction (`src/shop.c:1046-1051`), so the largest line must
  be bought FIRST or the selector silently caps it low. A spend-down pass runs AFTER the fixed
  basket and inherits this rule.
* **Buy Hyper Potion first, then Full Heal.** Hyper Potion (₽1,200) heals a flat 200 HP, which
  full-heals every member of this party (max HP ~115-231), so Max Potion (₽2,500) is strictly
  dominated. Full Heal (₽600) is the cheapest item on the board.
* ⛔ **Never buy Ultra Ball or Max Repel** — balls are blocked in trainer battles
  (`battle_script_commands.c:9915-9920`) and no map past the League door has a wild-encounter table.
* ⚠ **Mind the 99-per-stack cap** — a spend-down with a large wallet can hit it; the existing basket
  buys 30 Hyper Potions, so there is headroom, but the pass must not assume unlimited depth.
* ‼ **`LEAGUE_MIN_MONEY = 54_300` still gates ENTRY.** Spend-down is about what happens to the
  REMAINDER; it must not be allowed to eat into the basket itself or to make the
  *refuse-rather-than-under-buy* guard pass on a thinner basket.


---

## 2026-09-16 — USER RULING: 05-KNOWN-ISSUES gets ARCHIVE + RAISE + GUARD (not a bigger file, not "Part 2")

**The problem.** `05-KNOWN-ISSUES.md` hit exactly 3000/3000 lines, so the next known issue could not
be written at all. The user asked whether to raise the limit or split into Part 1 / Part 2, and asked
to settle it before more program work.

**Decision (the user's, after being shown four options and the measurements).** All three, in order:
**(1) archive** closed-AND-promoted issues to `31-KNOWN-ISSUES-ARCHIVE.md`; **(2) raise** the ceiling
3000 -> 4000 with the measurement recorded; **(3) guard** the intent directly by applying R7 to 05.

*Rationale — the project had already written the decision procedure.* `lint_docs.py` records that
`03-PUNCH-LIST.md` was raised 3600 -> 4200 on 2026-09-08 *"ON A MEASUREMENT, NOT A PREFERENCE"*,
because the line budget is only a PROXY for "an archive is forming" and for 03 that proxy was
measurably false — it was measuring BACKLOG. That block leaves an explicit instruction: *"If you are
tempted to raise it again, run R7 first: if the closed fraction has grown, the file really IS
becoming an archive and trimming is the right answer."*
**R7 WAS RUN. 05 measured 49.3% closed against the 41.1% on record — it HAD grown** ⇒ trimming was
required first, and a raise alone would have been the wrong answer.

*Why the retention condition had expired.* The **2026-07-29 user ruling** retains fixed issues *until
they are PROMOTED*. `promote.py --check` now measures **drift 0**, so KI-93/94/95/96/97 were promoted
and the condition no longer held. **The file grew because nothing re-checked that trigger after the
promotions happened** — not because anyone was careless. The durable fix is the R7 gate, which
notices next time.

*Rejected — "Part 1 / Part 2".* Splitting by SIZE is worse than the status quo: the split point
carries no meaning, a reader cannot know which part holds their issue, and KI numbers are cited from
code comments and gates, so references become ambiguous. The binding constraint is not storage — it
is that 3,000 lines is already past what an agent reads in full.

*Rejected — raise the ceiling only.* It overrides the project's own decision rule at the exact moment
that rule was designed to fire.

*Rejected FOR NOW — split by DOMAIN* (`05-...-BATTLE/NAVIGATION/STORY`). Genuinely better than Part
1/2 because the split would carry meaning, and it stays the right answer **if the OPEN backlog alone
ever outgrows one file**. Not yet: after trimming, 05 is 2675 lines with ~1,475 of open work.

**‼ WHY R7's BUDGET FOR 05 IS 0.55 AND NOT 0.25.** The old comment said 05 must NOT be gated because
41.1% closed "is CORRECT" under the 2026-07-29 ruling, and a gate there "would red the suite for a
user-approved state — a gate that cries wolf is worse than none." **That reasoning still stands**, and
is why the number is loose. What changed is that leaving it ungated let the share drift 41.1% ->
49.3% with nothing to notice. Post-trim it measures 44.9%, so 0.55 is ~10 points of headroom over a
state the user approved. ⛔ Do NOT tighten it to 0.25 to "match 03" — that would be red on arrival.


## 2026-09-16 — ⛔ DO **NOT** WIRE SEGMENT 24 YET, EVEN THOUGH LEG 1'S MECHANICS ARE FULLY DRIVEN

**Context.** Every mechanical step of §Ch24 leg 1 is now measured and A/B'd: `B` clears the
post-victory msgbox (297 frames, control arm proves it does not self-clear), `calculate_path` routes
to the runtime-opened door, the driven navigator walks it, the hall walks, and the bot arrives in
Phoebe's room with `ELITE_4_STATE 1→2`. The obvious next move was to wire it as production code with
a Segment 24 dispatch. **A 20-agent adversarial recon refuted that, and the decisive finding was then
confirmed at the source.**

**Decision — the wiring is BLOCKED on two prerequisites, not on more measurement.**

**REASON 1 (decisive, verified in code, and the §Ch23 author predicted it).**
`victory_road.py:3312` — `ch23_chapter_done()` conjuncts `_on_map(EG)`:

    if not _on_map(EG) or any(_on_map(m) for m in VICTORY_ROAD_MAPS):
        return False

Every League interior map is a SEPARATE map. ⇒ **the instant Segment 24 steps through the League's
front door, §Ch23's completion gate reads FALSE — and because the gauntlet is ONE-WAY, that position
can never be restored from inside.** Any raise past that door re-enters `do_victory_road_chapter()`,
whose eleven legs are all position-gated and all self-skip, three times, then raises ⇒ 4 derails ⇒
Manual, parked in a sealed Elite Four room.
⭐ **This is a FORWARD DEPENDENCY the §Ch23 author wrote down and the leg-1 plan did not honour.**
The same function's docstring already says: *"when §Ch24 is built it MUST set its own progress marker
so §Ch23 is not re-entered — a forward dependency, recorded here because it is now load-bearing."*
⚠ And its stated mitigation — *"a wasteful re-buy is strictly better"* — assumes the bot can get back
to re-buy. It cannot. That is what the one-way measurement adds.
‼ **THE FAILURE MODE IS CREATED BY THE WIRING, NOT PRE-EXISTING.** Today `_play()` ends immediately
after Segment 23's `_guard`, so the basket is never spent and the predicate is never re-evaluated.
⇒ wiring Segment 24 now would trade *a bot that stops cleanly at end-of-content* for *a bot that, on
any error past that door, burns three no-op Ch23 attempts and lands in Manual, sealed.* **Strictly
worse.**

**REASON 2. Leg 1's endpoint is a sealed room with no leg 2.** Arriving in Phoebe's room means the
entry script ran, which seals the door behind the bot, with an unfought Elite Four member in front.
That is the §Ch15 / §Ch18 / §Ch19 *"passed its own test while stranded"* shape — the exact thing
`ch22_chapter_done()` and `ch23_chapter_done()` were written to prevent.

**REASON 3. "Composed entirely from shipped helpers" was FALSE.** Only `VR._navigate_riding_out`,
`VR._walk_through_warp` and `early_game._pass_through_door` ship. **Nothing in
`sandbox-pokebot/modules/**` or `plugins/**` navigates the League interior at all** — the guard-talk
loop, the trainer-object read, the battle-engage mash and the post-victory dismiss exist ONLY in
`story_harness.py`. ⛔ And the harness's engage mash presses **A** one frame in three while facing the
trainer, which is precisely the hazard `e4dismiss` was built to avoid; copying it into production
would import it.

**PREREQUISITES before Segment 24 may be wired (both, not either):**
1. §Ch24 owns a **position-independent progress marker** so §Ch23 is not re-entered from inside the
   League — the forward dependency `ch23_chapter_done`'s docstring already names.
2. **Leg 2 exists**, so arriving in Phoebe's room is a continuation rather than a dead end.

**Alternatives rejected:**
* *Wire it anyway and accept the derails.* Rejected: it makes the bot strictly worse than today on
  every run that reaches the League, for no gain until leg 2 exists.
* *Relax `ch23_chapter_done()` to drop the position conjunct.* Rejected: that conjunct exists because
  a whiteout at the Ever Grande Poké Center satisfied the old predicate and advanced a wiped,
  unstocked party into the gauntlet — MEASURED on `ki90_whiteout_at_evergrande.ss1`. Removing it
  re-opens a hole the project already fell into.
* *Ship leg 1 as a harness driver only.* This is what we have, and it stays. The probes are honest
  about being probes.

**⭐ AND A WINNABILITY FINDING THAT CHANGES WHAT IS WORTH BUILDING.** Rosters re-verified against the
live decomp and cross-checked against our own symbol table (`sParty_Sidney` … `sParty_Wallace`, sizes
0x50/0x60 matching 5 and 6 mons): **Wallace is arithmetically out of reach for this party** — Milotic
(L58) carries `MOVE_RECOVER` and heals ~98/turn while our best measured hit is 66-78 — and **Glacia
OHKOs two of our six**. ⇒ §Ch24 is not one chapter of uniform difficulty; leg 1 is the best-evidenced
fight in the project and the last two are not currently winnable. Build order and party preparation
should follow that, not the room order.


## 2026-09-16 (later) — THE §Ch24 PROGRESS MARKER MUST BE A **POSITION ON THE SEALED SIDE**, and that is safe by EXHAUSTION

Prerequisite #1 of the "do not wire Segment 24" ruling above was: *§Ch24 must own a
position-independent progress marker so §Ch23 is not re-entered.* A recon answered it, and the answer
inverts the obvious candidates.

**EVERY ELITE FOUR FLAG/VAR IS DISQUALIFIED, AT THE DECOMP.**
* `data/event_scripts.s:585-587` — `EventScript_WhiteOut::` **calls** `ResetEliteFour`.
* `:628-634` — `ResetEliteFour` clears all four `FLAG_DEFEATED_ELITE_4_*` **and** `setvar
  VAR_ELITE_4_STATE, 0`.
* `data/scripts/hall_of_fame.inc` calls the same routine on the **winning** path.
⇒ `ELITE_4_STATE` and the four defeat flags read 0 whether you lose *or* win — useless as progress.

**AND THE TEMPTING CANDIDATE IS THE TRAP.** `FLAG_ENTERED_ELITE_FOUR` exists in our table
(`event_flags/emerald.txt:211` → `263 ENTERED_ELITE_FOUR`, matching the decomp's `0x107`), is set by
the door-guard script, and **nothing anywhere clears it** — `ResetEliteFour` does not touch it. So it
is PERMANENT and *survives a whiteout*. Used as §Ch23's disjunct it would flip that gate True forever
after the first guard-talk ⇒ a wiped party respawning outside would skip the League heal and the
basket on every later attempt. **That is `KI-90`'s measured hole wearing a new hat.**

**⭐⭐ THE ANSWER, AND IT IS PROVEN BY EXHAUSTION RATHER THAN ARGUED.** Walking into the lobby arms the
respawn (`EverGrandeCity_PokemonLeague_1F_OnTransition: setrespawn
HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE`), and that heal point is **OUTDOORS at
`MAP_EVER_GRANDE_CITY (18,6)`** (`src/data/heal_locations.json`). The recon then enumerated **every
distinct map in the whole heal-location table — 20 of them — and NOT ONE is a League interior map**;
the only indoor heal locations in the entire game are the two Littleroot bedrooms. ⇒ **a whiteout can
never place the avatar on a sealed League map, so a position there is the one signal a whiteout
cannot forge.** *(This also settles, in passing, where a mid-gauntlet whiteout lands: the outdoor
apron — by the respawn table, not by a log string.)*

**DECISION: the marker is "the bot is standing on a SEALED League map".**

⛔⛔ **TWO CAVEATS THAT MUST NOT BE LOST, BOTH RAISED BY THE RECON ITSELF:**
1. **`inside_league()` ALREADY EXISTS AND IS THE WRONG HELPER.** `victory_road.py:1372-1391`'s
   `LEAGUE_INTERIOR_MAPS` **includes the lobby (1F) and 2F** — and §Ch23's own heal and mart legs
   stand on the lobby (`LEAGUE_NURSE_STAND = (3,4)`, `LEAGUE_ENTRY_LANDING = (9,11)`). Reusing it
   would make `ch23_chapter_done()` return True the moment the bot walked in **to heal**, skipping
   the basket on re-entry. ⇒ §Ch24's marker needs its OWN tuple: the five rooms + Hall1-5 + Hall of
   Fame, **excluding 1F and 2F**.
2. **The lobby window is UNCOVERED.** Between the guard-talk and stepping into Hall5 the bot is on a
   NON-sealed map with the basket possibly spent. The recon did not trace that window end to end, and
   neither have I. ⇒ **not yet a complete design.**

**Alternatives rejected:** `ELITE_4_STATE` / the defeat flags (wiped by `ResetEliteFour` on both
paths); `FLAG_ENTERED_ELITE_FOUR` (permanent ⇒ re-opens KI-90); reusing `inside_league()` (includes
the lobby, see caveat 1).

## 2026-09-16 (later still) — ⛔ CORRECTION TO MY OWN WINNABILITY VERDICT: "WALLACE IS OUT OF REACH" IS AN **L53** RESULT, AND LEVELLING CONVERTS IT

Earlier today I recorded, in the do-not-wire ruling above and in `04-HANDOFF.md`, that **"Wallace is
arithmetically out of reach — Milotic L58 Recover ~98/turn vs our best measured hit of 66-78"** and
that "Glacia OHKOs two of our six". An adversarial agent challenged it and **the source refutes my
framing, not the numbers.**

`07-CHANGELOG.md:23307` — the same analysis those figures come from — says in full:

> *"Sceptile **L53** Leaf Blade does 66-78 ⇒ a net −20/turn losing race. **Break-even is L62.**"*

and gives the conversion curve directly:

    L53 (now)  0% Glacia          L57  87% Glacia, dies at Drake
    L60        99.7% Glacia       L75  88% CLEAR THE GAUNTLET

⇒ **"Out of reach" is true of the L53 party and FALSE as a general verdict.** The 66-78 figure is
Sceptile at L53; break-even is L62; and at L75 the same model gives **88% to clear the whole
gauntlet**. ‼ **I quoted a level-specific number as if it were a property of the matchup** — the same
shape as every other "measured X, concluded about Y" in `08-MISTAKES.md`, and I did it while writing
a ruling.

**WHAT THIS CHANGES.** The §Ch24 blocker is **party level**, and the tool to fix it already exists and
is proven: `--driver ch24grind` took the party from L47/51 to **L60 in 623 battles, ~30 minutes,
0 whiteouts**, checkpointing every two levels. ⇒ the cheapest path to a winnable gauntlet is not more
legs — it is **grinding past L62, toward ~L75** — and it is a capability we already shipped.

⚠ **BUT THESE ARE SIMULATION RESULTS, NOT DRIVES, AND THE NOTE SAYS SO:** the model uses our real
policy from source but approximates the enemy AI as max-expected-damage rather than Gen-3's score
table, and ignores crits, status, Attract/Encore/Double Team. ⇒ **treat L62/L75 as ESTIMATES**, and
expect the first real drive at a higher level to move them.

**THE RULING ABOVE IS UNCHANGED** — Segment 24 still must not be wired, for the `ch23_chapter_done()`
position reason, which has nothing to do with winnability. What changes is the *build order*
argument: legs 2-5 were being deprioritised partly because "it cannot be won", and that premise was
level-specific. **Grind first, then legs.**


## 2026-09-17 — ⛔ THE L75 GRIND RUNS ON `post_ch24ready.ss1`. `post_grind_L60.ss1` IS A DEAD BRANCH.

**DECISION.** The Elite Four grind starts from **`post_ch24ready.ss1`** (EVER_GRANDE_CITY (27,49),
battlers L47-53, fully prepped). ⛔ **`post_grind_L60.ss1` is NOT to be grinded from, NOT to be
repaired, and NOT to be cited as "13 levels we already paid for".** DO-NOT-REOPEN.

**WHY — the lineage, measured 2026-09-17 (`probe_grind_lineage_route.py`, both controls separating):**

    post_training.ss1  (§Ch23 training output, L47-51 — no Ice Beam, no Fly)
      ├─ post_wally → … → post_league_shop → post_moveset → post_fly → post_slateport
      │    → post_icebeam → post_teachice → post_ch24ready → post_ch24_atdoor    ← §Ch24 LINEAGE
      └─ post_grind_L60.ss1                                                      ← ⛔ DEAD BRANCH

`post_grind_L60.ss1` did not LOSE Ice Beam and Fly — it branched off **before the prep chain that
grants them** and therefore never had them. ⇒ "repair it" is not four teaches; it is re-running the
whole chain, including the **~700,000-frame Abandoned Ship trip** for TM13, to arrive at a party
`post_ch24ready.ss1` already is.

**THE NUMBERS THAT DECIDE IT.** The only thing the dead branch owns is 13 levels, and levels are the
cheap half. `estimate_frames_to_level` on VICTORY_ROAD_1F's L40 wilds, from L47-53, at the measured
1032 frames/s, already doubled for the measured **0.501 participant divisor** the estimator does not
model:

    target L62 (break-even)   ≈ 1.4 h
    target L75 (88% clear)    ≈ 3.7 h

⚠ Expect ~1.65× on top of that: the measured A/B runs ~2,368 frames per WIN against the estimator's
1,433 frames per BATTLE. Either way the grind is HOURS and the ship trip plus four teaches is not
obviously less — and it carries the risks the recon enumerated (a cave teach with an unexplained
failure precedent, an unbounded `fly_to` wait loop, and `apply_moveset_plan`'s all-or-nothing
refusal). ⇒ **pay the cheap half twice rather than the expensive half once.**

**THE ROUTE, MEASURED — this is what made the decision available at all:**
* `(27,49)` → `VR_APRON (18,42)` = **OK, 22 waypoints**; then `_walk_through_warp("Up")` into
  VICTORY_ROAD_1F, landing (15,40), one step from the grind tile **(15,39)**. ✅ DRIVEN, not planned:
  `ch24grind` logged `WALK: through the door -> ((24,43),(15,40))` then `standing at (15,39)`.
* Back to the League door is **ONE Fly**: `CB_ExitFlyMap` special-cases Ever Grande, so with
  `FLAG_LANDMARK_POKEMON_LEAGUE` set, flying to `PokemonLeague` lands on the door apron (18,6). That
  is precisely how `post_ch24_atdoor.ss1` was captured from `post_ch24ready.ss1`.

**ALTERNATIVES REJECTED.**
1. *Repair the L60 save* — rejected above. It was the plan a 4-angle recon was commissioned for; the
   recon's findings stand and are filed, but the plan is moot.
2. *Grind from `post_ch24_atdoor.ss1` (18,6) directly* — from the League door `calculate_path`
   reaches neither grass nor a Poké Center. ‼ That is a fact about **(18,6)**, and over-applying it
   to the whole plateau is what kept the grind pinned to the wrong lineage for a day. The Poké
   Center side is a different question and the answer is yes.
3. *Ask `best_training_area()` for the ground* — ⛔ MEASURED WRONG FOR THIS PARTY: it returns
   `(ROUTE117, (31,16), (13,14))` for a **L53** team. `TRAINING_GRASS` is an EARLY-GAME table (10
   entries, ceiling L19-22 at ROUTE111); VICTORY_ROAD_1F's L40 grass is not in it at all. The grind
   tile is NAMED (`TRAIN_SPOT_1F`), never chosen by the table.

**WHAT THIS COSTS US:** the ~2.4 h already spent grinding the dead branch. It is not recoverable and
it is not a reason to keep using it — that is the sunk-cost shape, and the measurement above is what
replaces the argument.


## 2026-09-17 (second) — THREE USER RULINGS ON §Ch24, PLUS A NEW STANDING CHANNEL

⭐ **NEW STANDING DIRECTIVE (user, 2026-09-17).** The user has offered themselves as a **gameplay
oracle** and asked to be used as one: *"if you have any questions about how the game is played from a
gamer perspective … you can ask me"* — when stuck, when repeatedly failing, before starting a piece
of work, while working, or in the wrap-up report. Named areas: **gameplay mechanics, mapping from a
visual standpoint, checkpoints, story logic.** Ask in **plain English with gameplay verbiage**, not
in code or decomp terms.
⇒ This is a THIRD research channel alongside Gemini (fan-out) and Claude subagents (validation), and
it is the only one that can answer *"what actually happens when a player does this"* from experience.
⛔ It does not replace verification: a gameplay answer is still a NOTE for anything code will depend
on — but it is an extremely cheap way to pick the right question to verify, and it settled three
things below in one exchange that would each have cost a research round.

### RULING 1 — ⛔ ICE BEAM IS GONE FOR GOOD ONCE LOST. RE-GRIND, DO NOT GO LOOKING FOR ANOTHER TM13.
**Asked because** the move-learning policy traded Wailord's **Ice Beam** for **Hydro Pump** at L59
(`#24-learnhmcoverage`), and Ice is **4x** on Salamence, Altaria and Flygon — the analysis says the
party loses to Drake without it.
**Ruled:** TM13 is a **single, one-time pickup** in the Abandoned Ship, is not sold anywhere, and the
Fallarbor Move Reminder only teaches LEVEL-UP moves — Ice Beam is not one of Wailord's. ⇒ **there is
no second copy**, and the only remedy is to re-grind from a save that still holds it.
⇒ **ACTED ON:** the re-grind resumes from **`post_e4grind_L57.ss1`**, the last checkpoint whose
Wailord still reads `Dive, Surf, Ice Beam, Waterfall` — 18 levels instead of 28, and no ship trip.
⛔ **DO NOT re-propose fetching another TM13, buying one, or tutoring an Ice move onto Wailord.**

### RULING 2 — ✅ 3 REVIVES IS ENOUGH AT L75. DO NOT SOLVE THE MONEY PROBLEM.
**Asked because** the recon's objection O8 priced the basket as short: `MAX_ITEM_USES_PER_BATTLE = 4`,
in-battle revival OFF by default (`KI-100`), **3 Revives for 5 one-way rooms**, and money MEASURED
flat at **₽1,941 across 1,056 wild battles** (wild Pokémon pay no prize money) against a ₽1,500
Revive — so the shortfall cannot be ground out.
**Ruled:** at **L75 against their L48-53 teams, faints should be rare enough that 3 Revives covers
it.** Do not spend effort restocking.
⇒ **O8 IS DOWNGRADED FROM A BLOCKER TO A WATCH ITEM.** ⛔ Do not build a money-earning detour, a
trainer-farming leg, or a bigger basket for §Ch24. ‼ If a live gauntlet drive shows repeated faints,
that is new evidence and the ruling can be revisited — but the *prediction* to test is "faints are
rare", not "we need more Revives".

### RULING 3 — ✅ DRIVE THROUGH THE ENDGAME TAIL TO THE POST-GAME SAVE. THE AUTOSAVE IS CONFIRMED.
**Asked because** room 5 ends in a Hall of Fame sequence, an **un-skippable first-clear credits roll**
(the B-hold speed-up is gated on `gHasHallOfFameRecords`, which is FALSE on a first clear) and then
**`SoftReset(RESET_ALL)`** to the title screen — and nothing in this tree handles any of it.
**Ruled:** *"yes drive through the post game save, but verify that the game auto saves once going
through the hall of fame (I believe it does)"*.
✅ **VERIFIED AT SOURCE, as asked** — `src/hall_of_fame.c:521-524`:
`static void Task_Hof_TrySaveData(u8 taskId) { gGameContinueCallback =
CB2_DoHallOfFameScreenDontSaveData; if (TrySavingData(SAVE_HALL_OF_FAME) == SAVE_STATUS_ERROR && …`
⇒ **the game DOES auto-save inside the Hall of Fame, BEFORE the credits and before the reboot**, and
`GameClear()` has already pointed the continue-warp at **Littleroot, the bedroom**
(`post_battle_event_funcs.c:36-41`). ⇒ **the soft reset is NON-DESTRUCTIVE**: progress is on the
cartridge before the screen goes black, so the tail is a matter of driving through it, not of racing
to save first.
‼ One narrow edge worth knowing: `gGameContinueCallback` is set to `CB2_DoHallOfFameScreenDontSaveData`
**before** the save, so a CONTINUE taken immediately after that point re-enters the Hall of Fame
screen rather than the overworld.
⇒ §Ch24 owns the tail: Hall of Fame → autosave → credits → soft reset → title → CONTINUE → Littleroot
bedroom, and `ch24_chapter_done()` is only true once the bot is CONTROLLABLE there. That is the third
prerequisite already recorded in `#24-gameclearflag`.

## 2026-09-17 (third) — USER RULING: §Ch24 HEALS FROM THE BAG BETWEEN ROOMS. IT IS NOT OPTIONAL.

**Asked because** the gauntlet is sealed — `probe_e4_entry_seal.py` CONFIRMED LIVE that the entry
tiles are impassable at runtime, the backward hall warps are inert, and every League map sets
`allow_escaping: false` ⇒ from HALL5 onward the nurse and the mart are unreachable. So "heal between
rooms" can only ever mean **from the bag**, and the question was whether it is needed at all at L75.

**RULED (user, 2026-09-17):** *"Potions, revives and healing are common to use between fights if
needed (full heal for status effects) so this should be in supply, but not as much as potions. Bag
heal (status heal, revive, hp heal if needed) between elite 4 fights."*

⇒ **LEG 2 PERFORMS A BAG HEAL BETWEEN EVERY ROOM**, covering all three needs in this order of
expected frequency: **HP top-up (most common) → status cure → revive (least common)**. ⛔ It is a
REQUIREMENT, not an optimisation, and not conditional on "if the party looks fine" — the next room
is unreachable-in-reverse, so a skipped heal cannot be repaired later.

‼ **THIS SUPERSEDES NOTHING AND CONTRADICTS NOTHING — READ IT WITH RULING 2 ABOVE.** Ruling 2 said
**3 Revives is enough at L75**; this ruling says revives are *used* between fights. Both hold: the
party is expected to need revives RARELY at this level advantage, and the 3 we carry are the budget.
⛔ Do NOT read this as licence to reopen the money/restock question — that is still closed.

**WHAT THIS MEANS FOR THE BUILD, CONCRETELY:**
* `heal_party_from_bag` (`pokemon_league.py:250`) already exists, is driven and fault-armed
  (`POKEBOT_CH24_FAULT_NOHEAL`), and has **ZERO production callers** — §Ch24 leg 2 is its first.
  ⇒ this closes `#24-e4healing` STEP 2, which has been blocked on "there are no rooms yet".
* ⚠ Its readiness predicate `party_is_gauntlet_ready()` (`overworld_items.py:240-249`) tests
  fainted / status / HP fraction — **PP is NOT a term**, and there is no PP item in the bag or in
  the League mart (`#24-leg2spec` O3). The bag heal therefore CANNOT restore PP, and a PP-exhausted
  party is a different failure that this ruling does not address. Leg 2 must not report "healed" as
  though it means "fight-ready" in the PP sense.
* ⛔ The heal must be BAG-ONLY. Any fallback that walks toward a Poké Center is fiction inside the
  sealed zone, and worse, the ROM collision grid will happily PLAN that walk (the mirror-`KI-74`
  divergence). Reachability checks in League interiors read `_live_collision_grid`, never
  `get_map_data`.

---

## 2026-09-17 (late) — Mint room 3's start fixture by adding a POST-FIGHT capture to the proven Phoebe driver, not by building a two-room driver

**THE PROBLEM.** Room 3 (Glacia) needed a post-Phoebe start state and none existed. The only Phoebe
artifact was `in_phoebe_battle_L75.ss1`, which is taken INSIDE the battle: `Ch24PhoebeMode`'s step-6
capture fires at "battle started", and because a driver is SUSPENDED for the whole fight
(`BattleListener` owns the controller — which is why `battle_frames_waited` measures 0) that call
actually lands at the fight's END, still in battle. It is a damage-table artifact, not a start state.

**THE DECISION.** Add a step-9 POST-FIGHT capture to `Ch24PhoebeMode` behind a new env var
(`CH24_PHOEBE_POST_CAPTURE`), re-run the already-proven driver, and build room 3 on the fixture that
falls out. ⭐ **And take it at the SAME LIFECYCLE POINT `post_sidney_L75.ss1` occupies** — post
victory, victory msgbox still parked, standing at (6,6) — so the new fixture is a DROP-IN analogue of
the one the template already consumes and the room-N copy handles it with the step-1 dismiss it
already has. Guarded on **won ∧ in-room ∧ exit-door-OPEN-in-the-LIVE-grid**.

**ALTERNATIVES REJECTED.**
* **A two-room driver (Sidney → Phoebe → Glacia in one run).** Rejected: it duplicates work that is
  already proven, makes every room-3 iteration pay for a full Phoebe fight, and — the deciding
  objection — a failure in the PROVEN half would waste the UNPROVEN half's measurement. It also
  leaves the fixture ladder with a permanent hole, so room 4 would face the same problem again.
* **Reuse `in_phoebe_battle_L75.ss1`.** Rejected: it is an in-battle state, as above.
* **Capture a "clean" state (msgbox cleared, script inactive, controllable).** Rejected, and this one
  was actively argued for by a recon agent proposing a nine-conjunct guard. ⛔ **An independent
  refuter loaded `post_sidney_L75.ss1` — the fixture this project already drives from successfully —
  and found it reads printer ACTIVE at `WaitForButton`, victory script ACTIVE, controllable FALSE.**
  Those conjuncts would have REFUSED to mint the very fixture the working driver consumes. ⇒ a gate
  demanding a clean frame is not "the safe version", it is a DIFFERENT fixture contract that breaks
  the existing one.

**WHY THE THREE CONJUNCTS ARE THE RIGHT THREE.** They are about whether the fixture is USABLE, not
about whether the frame is tidy: a fixture minted from a LOST fight, or from a room whose exit door
never opened, would send the next session to debug a driver against a poisoned start state. ⚠ SCOPE:
the door conjunct is meaningful at CAPTURE time only. Each room's `OnLoad` calls
`PokemonLeague_EliteFour_EventScript_ResetAdvanceToNextRoom` whenever its DEFEATED flag is set, so
merely RELOADING a post-victory save re-opens the door — which is why the driver must never be
graded from its own output, and why a VACUITY arm pointed at exactly that is run.

---

## 2026-09-17 (late) — the §Ch24 tail probe does NOT defeat the 20,000-frame no-progress detector, on purpose

**THE CHOICE.** The leg-B build spec's trap T1 says the harness's no-progress detector will see a
CONSTANT signature across the Hall of Fame and the credits (state reads `UNKNOWN`, position throws to
`None`, the party is frozen by `HealPlayerParty()`), and suggests **cycling a trivial sub-generator on
`context.controller_stack`** so that `ctrl` changes and `no_progress` resets.
**Decision: do NOT implement it in the probe.**

**WHY.** The probe exists to answer the spec's question **Q2 — does the tail exceed the detector's
budget?** Implementing the workaround would have *made the question unanswerable*: the detector could
no longer fire, so the run could not tell us whether it would have. ⇒ **a workaround installed before
the measurement destroys the measurement.** The cost of being wrong was bounded and acceptable: if the
detector fired, the run would stop with a partial transition table that *itself* answered Q2.

**THE RESULT VINDICATED IT, AND THE ANSWER IS USEFUL.** The longest in-tail constant-signature stretch
reached only the **x8000** rung; `HANG CONFIRMED` appears in the log only at f69937, **after** the
`ACCEPTANCE` line, with `ctrl='<none>'` — the post-acceptance artifact every probe in this tree
produces. ⇒ **a real leg-B driver does not need the workaround at all**, and the spec's T1 can be
downgraded from "defeat it" to "be aware of it". That is a piece of machinery this project now does
not have to write, review, fault-test or maintain.

**ALTERNATIVES REJECTED.**
* *Cycle a sub-generator on the controller stack (the spec's suggestion).* Rejected as above — and
  separately because manipulating `context.controller_stack` from inside a driver is novel machinery
  in this tree, and the first run through an irreversible, un-fleeable fight is the worst possible
  place to debut it.
* *Raise the detector's 20,000 constant.* Rejected: it is a shared safety net for every driver, and
  loosening it to suit one probe is the "a gate with false negatives" trade this project refuses.
* *Stuff `"end of built content"` into `context.message` to relabel the break.* Rejected, and the
  probe's docstring says why: `story_harness.py`'s `_finished` branch only **relabels** the stop as
  RUN COMPLETE — the loop still `break`s. It would have hidden the stop without preventing it.

⇒ **THE GENERAL RULE THIS SETTLES:** when a probe's purpose is to find out whether a guard fires,
**do not pre-emptively disarm the guard**. Measure first; harden second.


## 2026-09-17 (late) — ⛔ THE LEVEL FIX IS **NOT** “A CAPABILITY WE ALREADY SHIPPED”: IT IS SHIPPED IN THE HARNESS ONLY

**This entry exists because the sentence it corrects is the one a future agent will read.** The
2026-09-16 ruling *“CORRECTION TO MY OWN WINNABILITY VERDICT”* above is right that §Ch24’s blocker is
party level and that the cure is grinding past L62 toward ~L75. Its **final clause is wrong**:

> *“the cheapest path to a winnable gauntlet is not more legs — it is **grinding past L62, toward
> ~L75** — and it is a capability we already shipped.”*

**WHAT I MEASURED.** `--driver ch24grind` is `Ch24GrindMode`, and it lives in
`tools/story-dev/story_harness.py` — the harness. **Production has no path above L47.**
`sandbox-pokebot/modules/story/victory_road.py:492` sets `TRAIN_TARGET = 47`, a grep over
`modules/story/*.py` plus `story_mode.py` returns that as the *only* story training target (the one
other hit, `ENDLESS_RESET_TARGET`, is unrelated), and §Ch23’s eleven legs (`:3374-3460`) contain **no
post-Wally training leg** — legs 6–9 traverse B1F/B2F, legs 10–11 heal and shop.

⇒ **Every §Ch24 result this project has — five rooms driven, Wallace beaten, the game cleared — was
produced from a HARNESS-MINTED L75 party that production cannot grow.** A wired Segment 24 today
would enter a one-way sealed zone at L47 and lose every run.

**DECISION: a FOURTH prerequisite is added to the “do not wire Segment 24” ruling** — a post-Wally
B1F training leg to **L62 minimum** (L75 for the modelled 88%). Filed as `#24-levelgap` in
`03-PUNCH-LIST.md`, which is the correction of record and carries the full evidence and sizing.
The fix is already *designed* in `TRAIN_TARGET`’s own docstring (“the remaining gap is meant to be
closed on B1F after Wally”).

⛔⛔ **CORRECTED BEFORE THIS ENTRY WAS EVER COMMITTED (same day).** The sentence here originally read
*“and `target` has been a real parameter since 2026-09-04 — so this is a new LEG, not a re-plumbing
job.”* **That is false and is withdrawn.** `target` is a real parameter, but the call site hardcodes
`grass=TRAIN_SPOT_1F` (`victory_road.py:2088`) and `WILD_MAX = 40` is a hardcoded local (`:1988`), and
**no `TRAIN_SPOT_B1F` exists anywhere** — the very defect the 2026-09-04 fix cured, sitting one level
out. ⭐ **AND THE REAL BLOCKER IS NEITHER:** at true economics (950.8 xp/battle, ~3,192 frames/battle)
a L47→L62 climb on B1F costs **363,888–564,984 frames against the 250,000 per-call ceiling — every
growth curve refuses, by 1.46× to 2.26×** — and L75 costs 855k–1.34M. ⇒ **the open design question is
the BUDGET SHAPE** (a 15-level climb does not fit one `train_team` call, and the refusal message
forbids raising the ceiling), not the parameterisation and not the cost model.
‼ **A SECOND ITEM, `#24-trainestimatorcal`, WAS FILED AGAINST THAT COST MODEL AND WITHDRAWN THE SAME
DAY** — I had corrected the numerator and left the denominator; the estimator is only ~18% pessimistic
on FRAMES. See `07-CHANGELOG.md` (2026-09-08, `:24637-24641`) for the settled adjudication. ⛔ Do not
re-open it.

⚠ **PROVENANCE, STATED PLAINLY BECAUSE I GOT IT WRONG FIRST:** the L53/L57/L60/L75 win-rate curve is
**SIMULATED** (“Simulated over 400 runs per configuration”, `07-CHANGELOG.md:23285`), not measured; I
first wrote “the measured curve” in the punch-list item and the changelog and corrected both the same
day. Its top end is now corroborated by one real drive (the 2026-09-17 tail probe beat Wallace at
L75+), but “L47/L53 is hopeless” rests on simulation alone. The decision stands regardless: L47
against a break-even of L62 is a 15-level gap, far outside any plausible error bar.

**Alternatives rejected.** (a) *Wire Segment 24 anyway and let it lose* — the zone is one-way and
un-fleeable; a loss is a whiteout that wipes `VAR_ELITE_4_STATE`, so the bot would re-run the
gauntlet from room 1 forever. (b) *Promote `Ch24GrindMode` verbatim* — it is a harness driver: it
ends in `set_manual_mode()` (163 such calls in the harness; **zero** in
`sandbox-pokebot/modules/story/`), which hands the run to a human, the opposite of a production leg.
(c) *Train somewhere other than B1F* — settled against the decomp already
(`modules/story/training_areas.py:30-49`): every `MAP_ROUTE*` land table maxes at 28, so B1F is not a
preference but the only ground.


## 2026-09-17 (late) — THE RETRACTION-COVERAGE CHECK IS **ENFORCING**, NOT ADVISORY

**Context.** New gates are sometimes landed ADVISORY while their false-positive behaviour is learned.
This one is ENFORCING from the start, and the reason is a property, not confidence.

**DECISION: enforcing, because the check FAILS SAFE.** It harvests a retracted claim only from the
house idiom (retraction keyword + past-reference quotation). An idiom it does not recognise is never
harvested, so an unseen retraction produces a **MISS**, never a spurious failure. CLAUDE.md §6's
concern is one-directional — *"a gate with false positives teaches the reader to bypass it, which is
strictly worse than no gate"* — and this gate cannot produce one from an unrecognised idiom.

**What earned the trust: it failed its own fault test twice.** v1 produced 199 false positives on the
real tree (a regex that matched the prose BETWEEN quotations); v2 reported ZERO violations on an
injected defect (claims containing a keyword excused themselves). Only v3 passed all four arms.
⭐ **A gate is not proven by being written; it is proven by being broken on purpose and seen to fire.**

**Alternatives rejected.** (a) *Ship ADVISORY first* — rejected: an advisory that nobody reads would
not have caught today's misses, which were found by paid reviewer rounds. (b) *Retire the prose rule
in `08-MISTAKES.md` now that a gate exists* — rejected, and this matters: the gate covers the house
idiom only, so retiring the rule would trade a partial mechanical check for the loss of the general
one. The rule stays; the gate is a floor under it. (c) *Widen the marker window so a marker anywhere
in the same line counts* — rejected: the exact miss it was written for had a marker ~208,000
characters earlier in the same line.


## 2026-09-17 (late) — ⛔ REVERSAL OF THE ENTRY ABOVE: THE RETRACTION-COVERAGE CHECK IS **ADVISORY**, NOT ENFORCING

**The entry immediately above decided ENFORCING, and its stated reason was a PROPERTY: "the check
FAILS SAFE … this gate cannot produce [a false positive] from an unrecognised idiom." That property is
FALSE.** A Tier 1 reviewer refuted it from both directions within the hour; I reproduced both before
reversing.

* A keyword and an *unrelated* past-reference quotation sharing a window cause a **still-live sentence
  to be harvested as retracted**, and every honest copy is then reported. The idiom *is* recognised —
  it is the RELATEDNESS that is not checked.
* The harvester is blind to the **in-place marker** idiom, which is how its own motivating defect #3 is
  written ⇒ it misses the bug it was built for (2 occurrences, 0 harvested).

**DECISION: ADVISORY**, recorded in `run_gates.py`'s ADVISORY frozenset with both defects and their
repros. The suite is **67 entries = 63 ENFORCING + 4 ADVISORY**.

**⭐ THE RULE THIS SETTLES, which generalises past this gate: when a gate's ENFORCING status rests on a
PROPERTY ("fails safe", "cannot false-positive", "is monotone"), the fault test must contain an arm
that ATTACKS THAT PROPERTY.** Arms that merely exercise the mechanism will all pass while the property
is false — mine did, four for four. *A fault test proves the arms you thought of; it does not prove the
property you claimed.*

**Alternatives rejected.** (a) *Patch the harvester now and keep it ENFORCING* — rejected: the
in-place-marker fix means harvesting the sentence BEFORE a marker, which plausibly multiplies the
false-positive surface that just disqualified it. Fix it deliberately, with the repros as tests, not
under time pressure on the day it broke. (b) *Delete the gate* — rejected: the machinery and its
four-arm harness are sound and the ADVISORY run still surfaces real unmarked copies; the defect is in
the SAFETY ARGUMENT, not the concept. (c) *Keep ENFORCING and add the false-positive case to an
allow-list* — rejected: an allow-list papers over a harvester that cannot tell live text from dead.


## 2026-09-17 (late) — ENFORCING IS JUSTIFIED BY THE **INPUT DOMAIN**, NOT BY THE CHECKER

**Context.** Two gates were written the same day and given opposite statuses, which needs a recorded
reason so the next author picks correctly rather than by mood.

* `probe_retraction_coverage.py` → **ADVISORY.** It must DECIDE whether a sentence is retracted. A
  checker that judges can misjudge, and it did, in both directions (false positive on live text; blind
  to its own motivating defect).
* `probe_doc_control_chars.py` → **ENFORCING.** It asserts a property of the INPUT DOMAIN: a Markdown
  document has no legitimate use for any C0 control character except TAB and NEWLINE. There is nothing
  to judge, so there is nothing to misjudge; a hit is a defect by construction.

**DECISION / RULE: a gate may ship ENFORCING when its "no false positives" claim follows from the
INPUT DOMAIN. When the claim rests on the checker's own discrimination, ship ADVISORY until an arm
that ATTACKS that discrimination passes.** This is the operational form of the lesson from the same
day: *a fault test proves the arms you thought of; it does not prove the property you claimed.*

**Alternatives rejected.** (a) *Fold the control-character check into `lint_docs.py`* — rejected:
`lint_docs.py` is itself a gate under active edit, and a standalone probe can be fault-tested in
isolation and cited by slug. (b) *Warn instead of failing* — rejected: the character is invisible, so a
warning nobody sees is indistinguishable from no check; and unlike a judgement call, there is no
legitimate hit to be annoyed by. (c) *Scan only the current-state files* — rejected: the second
historical instance was found in `28-HANDOFF-ARCHIVE.md`, an archive, which is exactly where an
invisible defect survives longest because nobody re-reads it.


## 2026-09-17 (late) — ⛔ A THIRD CAVEAT ON THE §Ch24 MARKER RULING: IT DOES NOT COVER **WINNING**

**The 2026-09-16 ruling stands in its reasoning and is INCOMPLETE in its coverage.** It decided the
§Ch24 progress marker is *"the bot is standing on a SEALED League map"*, justified by exhaustion: no
whiteout can respawn on a League interior. ✅ **I re-measured that exhaustion argument and it holds** —
the decomp's heal table has 22 locations across 20 maps and not one is a League interior; the only
indoor heal points in the game are the two Littleroot bedrooms, and entering the lobby arms an
**outdoor** respawn at `MAP_EVER_GRANDE_CITY (18,6)`.

**⛔⛔ WHAT IT MISSES: THE WINNING END STATE.** A completed §Ch24 leaves the avatar at
`LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` — MEASURED by this project's own tail probe, and the ruling
predates that measurement. Littleroot is not a League map, so the marker reads FALSE after a win,
`ch23_chapter_done()` is consulted, returns False (it requires `_on_map(EG)`), and §Ch23 re-runs. Legs
1-3 self-skip, but **leg 4 fires**: its guard is `not inside_vr and not at_ever_grande_top()`, and
`at_ever_grande_top()` is False from Littleroot on both of its terms.
⇒ **a completed game becomes a hard §Ch23 failure, attempting an ocean crossing from a bedroom.**

**DECISION: the marker must be a DISJUNCT — "on a SEALED League map **OR** the game is cleared."**
The second term is `IS_CHAMPION` (flag 2175), chosen because it is **MONOTONE**: set in exactly one
decomp file and cleared nowhere, unlike `VAR_ELITE_4_STATE` and the four `DEFEATED_ELITE_4_*` flags,
which `ResetEliteFour` wipes on the WINNING path as well as the losing one. Filed as
`#24-markerwinstate`; prerequisite (1) is **not done**.

⚠ **THE OTHER TWO CAVEATS ON THAT RULING REMAIN OPEN** — `inside_league()` is the wrong helper (it
includes the lobby and 2F), and the lobby window is still untraced. This is the third.

**⭐ THE RULE THIS SETTLES, and it generalises past this marker: A COMPLETION MARKER MUST BE CHECKED
AGAINST THE *SUCCESS* PATH, NOT ONLY AGAINST THE FAILURE PATH.** The exhaustion argument was built
entirely around what a WHITEOUT can forge — a careful answer to "can this be reached by failing?" —
and never asked the cheaper question, *"where is the bot standing when it WINS?"* The project already
has the matching rule from 2026-09-05: *"A POSITION CAN BE REACHED BY SUCCEEDING **OR** BY FAILING."*
Here the position could be reached by neither, because winning moves the bot somewhere else entirely.

**Alternatives rejected.** (a) *Use `SYS_GAME_CLEAR` as the second term instead of `IS_CHAMPION`* —
rejected: it is set ~54 lines before the callback swap, with the Hall of Fame, the credits and a
`SoftReset(RESET_ALL)` still ahead (`#24-gameclearflag`). (b) *Add Littleroot to the marker's map set*
— rejected: Littleroot is where a NEW GAME starts, so it would grade a never-played save as done. (c)
*Leave it and rely on `ch23_chapter_done()`'s basket conjunct* — rejected: after a win the party is
whatever survived Wallace and the basket is likely spent, so that conjunct is False too.


## 2026-09-18 — BUILD THE STEPPED GRIND ON **1F** FIRST; CHOOSE THE GROUND **LAST**

**Context.** A 10-agent workflow priced the post-Wally grind. It refuted the question I asked, answered
the one I should have asked, and turned up a landmine.

**WHAT CHANGED THE DECISION.**
1. ✅ The per-call ceiling **already permits** a stepped grind — `victory_road.py:2012-2019` says so
   explicitly and tests `max()` over one mon per call. Nothing needs relaxing.
2. ✅ The shape **already exists and has run**: `Ch24GrindMode`'s stepped loop with a checkpoint after
   every step, ladder on disk.
3. ✅ `estimate_frames_to_level` has **no heal or travel term**, so the heal round-trip I set out to
   price is invisible to the guard that refuses the grind. The ground choice is worth 4.79% under that
   model against a required 2.05× cut.
4. ⛔ `_exit_training_cave_if_inside()` does not know Victory Road, so **a B1F heal is UNPROVEN** and
   may hit the documented Granite Cave navigation failure (`#24-cavehealblind`).

**DECISION: promote `Ch24GrindMode`'s stepped shape into a post-Wally production leg, using the PROVEN
`TRAIN_SPOT_1F`. Defer the ground choice until `#24-cavehealblind` is settled by a drive.**

**WHY 1F FIRST, GIVEN B1F IS AHEAD ON EVERY ECONOMIC ESTIMATE (+10% to +22% xp/frame).** Because every
part of the 1F path is already proven and measured — the spin tile, the cheap heal (~2,178 f median
over 278 real heals), the heal rate (1 per ~8.3 battles, 10% of run frames) — while B1F's advantage is
an *optimisation* whose enabling condition is unproven. ⇒ **ship the leg that certainly works, then
buy the 22% with a measurement.** A 22% speedup is not worth blocking the fourth prerequisite on.

**Alternatives rejected.** (a) *Build on B1F now* — rejected: `#24-cavehealblind` could make it unable to
heal at all, and the failure mode (navigating across warp levels) has already cost two real-hardware
Manual drops. (b) *Settle the ground first with a drive, then build* — rejected: it serialises a 22%
optimisation ahead of the blocker, and the same drive can be bought later at no extra cost. (c) *Relax
or raise `MAX_TRAINING_FRAMES`* — rejected, and now clearly unnecessary: the guard permits stepping as
written, and its own message forbids raising it. (d) *Fix the estimator first* — rejected: withdrawn
the previous day as ~18% pessimistic on the quantity that matters, and irrelevant here anyway since
stepping keeps each call under the ceiling.

⭐ **THE RULE THIS SETTLES: BEFORE OPTIMISING A VARIABLE, CHECK THAT THE DECIDING CODE CAN SEE IT.**
I priced a heal round-trip for a session; the guard that refuses the grind has no term for it. An
adversarial pass found that in one read of the function body.


## 2026-09-18 (later) — ⛔ REVERSAL: §Ch23 IS THE WRONG HOST FOR THE GRIND. THE DECISION ABOVE NAMED THE GROUND AND ASSUMED THE HOST

**The entry above decided "build the stepped leg on 1F first; choose the ground LAST."** A 10-agent
build recon then attacked the plan, and two independent angles converged on the half I had not
examined: **I chose the GROUND (1F, proven) and silently assumed the HOST (§Ch23, shipped).** The
engine survives; the location does not.

**✅ WHAT I VERIFIED MYSELF BEFORE REVERSING.**
1. **A whiteout HALVES money.** Decomp `src/overworld.c:358-366` — `DoWhiteOut()` calls
   `SetMoney(&gSaveBlock1Ptr->money, GetMoney(&gSaveBlock1Ptr->money) / 2)`. Our own tree already
   records it (*"Whiteout money is plainly `money / 2`"*).
2. **§Ch23's margin is 3.1%.** `victory_road.py:444` — *"₽54,300 total against a MEASURED ₽56,041"*,
   i.e. **₽1,741 of slack**.
⇒ **A GRIND PLACED BEFORE LEG 11 RISKS THE CHAPTER'S ENTIRE WORK PRODUCT ON ONE WHITEOUT.** Halving
₽56,041 gives ₽28,020 against a ₽54,300 basket, so leg 11 raises and the Elite Four's healing is never
bought. A multi-hundred-thousand-frame grind is exactly where a whiteout becomes likely.

**AND THE OTHER §Ch23 SLOT MAY BE NO BETTER — BUT THAT HALF IS UNPROVEN.**
⚠⚠ **HAZARD (b) IS UNVERIFIED AND OUR OWN CODE CONTRADICTS IT — DOWNGRADED 2026-09-18 AFTER A TIER 1 BLOCK.** *(This said, as settled fact: “AFTER leg 11 the grind and the basket SHARE ONE BAG — consuming healing items makes `ch23_chapter_done()`'s basket conjunct False, so the chapter can never grade done.”)* ✅ **MEASURED BY ME:** `train_team`'s 118-line body contains **ZERO** bag or item references in code, and its only healing call is `heal_in_pokemon_center(heal_center)` — a free Poké Center visit. The wild-battle handler `SwapTrainBattleStrategy` is pure switch logic; the item-using `StoryItemBattleStrategy` is scoped to TRAINER battles only. And `Ch24GrindMode._basket()`'s own comment states the opposite of my claim: *“THIS IS A READING, NOT A GUARD … the expectation is FLAT: `train_team` heals at a Poké Center (which also restores PP), not from the bag.”* No evidence file anywhere carries a `basket=` reading showing a drain. ⇒ **TREAT (b) AS THEORETICAL, pending a drive with `_basket()` logging.** ⛔ **THE REVERSAL DOES NOT DEPEND ON IT:** hazard (a), the money halving, is verified at the decomp and sufficient alone.

**DECISION: the grind does NOT go into §Ch23. `#24-levelgap`'s fix belongs on the §Ch24 side of the
boundary, and it is therefore part of what Segment 24 must contain — not a patch to a shipped chapter.**
⚠ This does NOT unblock wiring Segment 24, which stays ruled out with its prerequisites open. It moves
`#24-levelgap` from *"insert a leg into §Ch23"* to *"§Ch24's chapter must OPEN with a stepped grind"*.

**⭐ WHAT SURVIVES INTACT, AND IT IS MOST OF THE ENGINEERING.** The stepping engine is sound and
independently re-derived: every 2-level step fits the 250,000 per-call ceiling (my own arithmetic on
the REAL battlers of `post_wally.ss1` puts the worst step at **136,135 f, 1.8× headroom**; the recon's
independent simulation put its worst at 154,764, 62% of the ceiling — different assumptions, same
verdict). Resumability is **FREE**: `team_is_ready(target)` and both loops in `train_for_victory_road`
re-read the LIVE party and skip any battler already at target, so the grind's progress IS the party's
levels. `Ch24GrindMode`'s save-state checkpoints were never a resume mechanism — nothing reads one
back; they are operator fixture captures, and reloading one mid-run is forbidden in two places.

**⛔⛔ AND THE RECON CAUGHT THE THING THAT WOULD HAVE DONE REAL DAMAGE — VERIFIED BY ME AT SOURCE.**
The shape I was about to promote contains a **whiteout-swallowing retry loop**:
`story_harness.py:15646-15655` does `set_story_abort(False)` then `except Exception`, and
`class StoryAbort(BotModeError)` (`early_game.py:112`) means that `except` **catches the whiteout
unwind**. §Ch23's own dispatch docstring forbids precisely this (`victory_road.py:3342-3345`):
*"⛔ A WHITEOUT IS NOT RETRIED HERE … looping on it would burn all three attempts in a handful of
frames and report two invented failures (KI-67). The 3-attempt loop is for `BotModeError` and nothing
else."* ⇒ copying the harness shape verbatim would have reproduced **KI-67 inside the one chapter
written to forbid it** — and gate #27 `probe_abort_swallowing.py` scans `modules/story` for exactly
that pattern, so it would also have turned the suite red.

**Alternatives rejected.** (a) *Between legs 5 and 6* — the only mechanically viable §Ch23 slot, and
rejected on the money hazard above. (b) *After leg 11* — rejected: shares the bag with the basket.
(c) *Raise the money margin so a whiteout is survivable* — rejected: it treats a 3.1% slack as the
defect when the real problem is placing a long, whiteout-prone activity inside a chapter whose work
product is money-denominated. (d) *Accept the whiteout risk as low* — rejected: a grind is hundreds of
battles and the derail budget RESETS on every whiteout, so nothing bounds the attempts.

**⭐ THE RULE THIS SETTLES: A DECISION THAT NAMES A PARAMETER HAS NOT NECESSARILY CHOSEN THE THING IT
IS A PARAMETER OF.** I recorded "1F, not B1F" as *the* decision and never wrote down that §Ch23 was a
choice at all — so it was never attacked until an adversarial pass was pointed at the plan rather than
at its details. **State the host, not only the setting.**


## 2026-09-18 (later) — THE §Ch24 MARKER IS AN **EXPLICIT TUPLE**, NEVER A GROUP TEST — AND ALL THREE CAVEATS ARE CLOSED

**Context.** The 2026-09-16 ruling chose "standing on a SEALED League map" as §Ch24's progress marker
and left three caveats. A 6-agent trace closed them, and a refuter turned up a constraint that would
have re-opened a measured hole.

**⭐⭐ DECISION 1 — THE MARKER MUST BE AN EXPLICIT TUPLE. A GROUP OR RANGE TEST IS FORBIDDEN.**
✅ Verified by me at `map_data.py:1037-1051`: map group 16 contains, besides the sealed rooms and
halls, **`EVER_GRANDE_CITY_POKEMON_CENTER_1F (16,12)`**, **`_2F (16,13)`**, `POKEMON_LEAGUE_1F (16,10)`
and `POKEMON_LEAGUE_2F (16,14)`.
⛔⛔ **CITATION CORRECTED 2026-09-18 AFTER A TIER 1 BLOCK — I NAMED THE WRONG MAP AND MARKED IT “✅ verified by me”.** *(This said the Poké Center maps are “which §Ch23's leg 10 walks into to heal”.)* ✅ **LEG 10 HEALS ON `LEAGUE_1F` — `EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (16,10)`**: `heal_at_league` asserts `_on_map(LEAGUE_1F)` (`victory_road.py:2962`) and walks to `LEAGUE_NURSE_STAND = (3,4)` on that same map (`:2982`). ⛔⛔ **AND MY OWN CORRECTION OVER-REACHED — CAUGHT BY ME ON THE NEXT PASS.** *(It said the Poké Center maps are “never visited by our code (2 refs repo-wide)”.)* **That was a SYMBOL COUNT, not an occupancy test.** ✅ `PokemonCenter.EvergrandeCity = (MapRSE.EVER_GRANDE_CITY, (27, 48))` (`map_data.py:1537`) is a **DOOR** tile on the OUTDOOR map, and `heal_in_pokemon_center` walks through it ⇒ the avatar stands INSIDE `EVER_GRANDE_CITY_POKEMON_CENTER_1F (16,12)` during any Poké-Centre heal. The code simply never names that enum member — it detects such maps by SUBSTRING (`early_game.py:385`: `if cur is None or “POKEMON_CENTER” not in enum_name`), which is why my grep found 2 files for the symbol and 7 for the substring **within `modules/`** (8 across the whole sandbox — a reviewer counted the wider scope; both are right, which is why the scope is now stated). ⇒ ⭐ **BOTH `(16,10)` AND `(16,12)` ARE GENUINELY OCCUPIED, so the range-test hazard is STRONGER than either earlier version of this paragraph: two independent maps in group 16 that §Ch23 stands on while its work is unfinished.** ✅ **UPGRADED FROM INFERRED TO READ** — a Tier 1 reviewer found the direct evidence and I confirmed it at source: §Ch23 walks into that Poké Center **twice, both before the basket**. **Leg 4** (`victory_road.py:1556-1566`): *“⛔⛔ THIS IS LOAD-BEARING, NOT HOUSEKEEPING. Until the bot walks into the Ever Grande Poké Center, `lastHealLocation` is still SOOTOPOLIS”* — then `heal_in_pokemon_center(PokemonCenter.EvergrandeCity)`. **Leg 6** (`:2328-2333`) calls it again, *“heal before the B1F descent”*. ⇒ the occupancy of `(16,12)` is now a READ fact, not an inference. *(The docs previously UNDER-claimed this; the reviewer said so and was right.)* ⭐ **THE HAZARD IS UNCHANGED AND ACTUALLY MORE DIRECT:** the bot stands on **(16,10), a group-16 map**, while the heal prompt runs, so a range test grades §Ch23 done mid-heal. The Poké Center pair is a second, independent reason a range test is wrong — it would sweep in maps we never occupy. ⇒ the 11-member explicit tuple is unaffected; only the citation was wrong. ‼ I had verified the MAP TABLE and then attached an agent's sentence about leg 10 to it.
⇒ a range test grades §Ch23 **done in the middle of its own heal, before the basket is bought**. That
is KI-90's class of hole, re-introduced by a convenience.
‼ **The hazard came from MY OWN shorthand** — I wrote "sealed rooms are group 16" in the brief I handed
the agents, and a refuter asked what else lives in that range. *(Also `ROUTE4_POKEMON_CENTER_1F` shares
the raw tuple `(16,0)` in a different enum: compare enum MEMBERS, never bare `(group, number)` pairs.)*

**DECISION 2 — the marker is `on a CH24_SEALED_MAP` **OR** `IS_CHAMPION`.** The sealed half is safe by
exhaustion (no heal location is a League interior; the lobby arms an OUTDOOR respawn). The
`IS_CHAMPION` half covers winning, which the original marker missed — a completed §Ch24 ends in
Littleroot. `IS_CHAMPION` is monotone: set in one decomp file, cleared nowhere.

**DECISION 3 — `inside_league()` STAYS EXACTLY AS IT IS.** It has ✅ exactly one caller,
`at_ever_grande_top()` (`victory_road.py:1424`), where its WIDENESS (including 1F) is what makes leg 4
self-skip in the lobby. ⇒ caveats (1) and (2) interact: **the lobby is protected by the very property
that makes the helper wrong for the marker.** Give §Ch24 its own tuple; change nothing here.

**✅ AND THE MARKER IS NECESSARY, MEASURED NOT ARGUED:** on `post_hall4_door` — HALL4, sealed, one tile
from the Champion's door — `ch23_chapter_done()` returns **False**, with controls separating.

**Alternatives rejected.** (a) *A group-16 test* — rejected on the Poké Center hazard above. (b) *Reuse
`inside_league()`* — rejected: it includes 1F/2F where §Ch23's own legs work. (c) *`SYS_GAME_CLEAR`
instead of `IS_CHAMPION`* — rejected, set ~54 lines before the callback swap (`#24-gameclearflag`).
(d) *`FLAG_ENTERED_ELITE_FOUR`* — previously ruled out; permanent, re-opens KI-90.

⚠ **STILL OWED, and small:** the lobby window is TRACED (agent probe, refuter-reproduced), not READ by
me — **no fixture stands in the lobby**. Mint one and re-measure before implementation.


## 2026-09-18 (later) — THE LOBBY FIXTURE IS MINTED **WITHOUT** THE GUARD TALK

**Context.** `#24-lobbyfixture` needs a save state standing in the League lobby. Reaching it can
optionally include talking to the door guards, which sets `FLAG_ENTERED_ELITE_FOUR` — **permanent;
nothing in the game or `ResetEliteFour` clears it.** A Tier 1 reviewer noted this tradeoff was recorded
in the changelog and punch list but never logged as a DECISION. It is one, so here it is.

**DECISION: mint `post_league_lobby.ss1` WITHOUT the guard talk.**

**Why.** Two reasons, the second stronger and supplied by a refuter rather than by the spec:
1. **The readings are identical either way.** No code reads `FLAG_ENTERED_ELITE_FOUR` — every predicate
   the fixture exists to evaluate is bit-identical with or without the talk.
2. ⭐ **A no-talk fixture is POSITIONALLY SEALED against the gauntlet.** While the flag is unset the
   guards stand ON `(9,2)/(10,2)`, *“blocking the north doors positionally”* (`victory_road.py:399-402`)
   ⇒ no future drive from that fixture can reach a sealed room **at all**. A post-talk sibling has those
   doors open **forever**, because the flag never clears.

⚠ **A POST-TALK SIBLING IS STILL OWED, for a different reason than convenience:** the settled ruling
defines the §Ch24 “lobby window” as the **POST-talk** interval. ⇒ it should be minted deliberately, as
its own fixture with its own justification, never as a side effect of reaching the lobby.

**Alternatives rejected.** (a) *Talk by default* — rejected: it spends a permanent, irreversible flag to
obtain readings that do not depend on it, and it opens the gauntlet doors on every future drive from
that fixture. (b) *Mint only the post-talk fixture* — rejected: it forecloses the positionally-sealed
state, which cannot be recovered afterwards. (c) *Skip the fixture and keep tracing* — rejected: the
whole point is to convert the lobby window from TRACED to READ.

⭐ **THE RULE THIS SETTLES: when a route contains an irreversible step, mint the fixture on the
REVERSIBLE side of it first.** The sealed state can always be spent later; it can never be regained.


## 2026-09-18 — MINT THE LOBBY FIXTURE ON THE *REVERSIBLE* SIDE OF THE IRREVERSIBLE STEP

**DECISION: the League-lobby fixture is minted WITHOUT talking to the door guards**, and a post-talk
sibling is a SEPARATE deliberate artifact rather than a side effect.

**WHY.** Talking to the guards sets `ENTERED_ELITE_FOUR`, and **nothing in the game ever clears it**
— `ResetEliteFour` does not touch it. While it is unset the guards stand ON `(9,2)/(10,2)`,
*“blocking the north doors positionally”* (`victory_road.py:399-402`). ⇒ a no-talk fixture is
**positionally sealed**: no future drive launched from it can reach the un-fleeable Elite Four rooms
by accident, because the planner cannot route through the guards. A post-talk fixture has those doors
open **forever**. ⇒ Mint the reversible one first; it strictly dominates as an iteration base.

**REJECTED:** *talk first, so the fixture matches the settled definition of the “lobby window” as the
POST-talk interval.* That definition still stands and the post-talk sibling is still owed — but
minting it FIRST spends the irreversible step to get an artifact that is strictly more dangerous to
iterate from. The settled ruling defines what the window IS; it does not require the first fixture to
sit inside it.

**CONSEQUENCE, MEASURED THE SAME DAY:** the drive from that fixture found that with no §Ch23 call site
reached and `ch23_chapter_done()` False, `do_victory_road_chapter` **raises** after 3 attempts
(`:3486-3488`). ⇒ **the §Ch24 marker is not optional cleanup; without it the bot cannot leave §Ch23
once it steps into the League.** That reprioritises prerequisite (1) of wiring Segment 24.

## 2026-09-18 — A GUARD TRANSCRIPTION MUST NAME THE *CALL*, NOT THE ENCLOSING `if`

**DECISION:** when transcribing a dispatch's guards into a probe, the row is the condition under
which the `yield from` **executes** — for a nested call site, the CONJUNCTION of every enclosing test
— and every call site is enumerated by reading the **`yield from`s**, never by reading the numbered
`--- LEG N ---` banners.

**WHY:** both failure modes were found in one adversarial read of a probe already committed and
already cited in the punch list. The TRAINING leg (`victory_road.py:3430-3431`) has a banner reading
`--- THE TRAINING LEG ---` and no number, so a banner-driven enumeration missed it; leg 11's real
condition is the inner bag test (`:3462-3467`), and transcribing the outer `_on_map(EG)` produced a
published claim about when the leg runs that was simply false.
**ALTERNATIVE REJECTED:** *annotate the known exceptions in prose.* The prose already existed —
`03-PUNCH-LIST.md` said *“pre-Wally the training leg fires there”* four lines above the claim it
contradicted. Prose next to a checklist does not fix the checklist.


## 2026-09-18 — ⭐ USER RULINGS: THE LEVEL TARGET, THE GRIND LOCATION, AND WHERE §Ch24 HEALS

Asked as three plain-English gameplay questions while `#24-levelgap` recon was open. The user is the
gameplay oracle; these are RULINGS, and they retire three open questions.

### RULING 1 — **THE L62-75 TARGET IS CORRECT. `#24-levelgap` STANDS.**
User: *“Yes that level range is worthwhile … I do know some players get through the elite 4 with mid
50 level pokemon but thats serious strategy that we have not implemented into the bot yet (maybe in
the ai version of this program).”*
⇒ the simulated curve's CONCLUSION is accepted: production's L47 is not enough, and the grind is
required content for §Ch24. ⛔ **This does NOT rescue the refuted PLAN** — “every 2-level step fits
the ceiling” was measured false the same day (the worst step is the LAST one, 73→75, and the
estimator is ~3.3× optimistic). **The GOAL is ratified; the SCHEDULE must still be re-derived from
measured cost.**
⇒ ⭐ And the mid-50s route is explicitly **not** the cheaper alternative it might look like: it
depends on battle strategy this bot does not have. Do not propose “just play better” as a way to skip
the grind.

### RULING 2 — **GRIND AT THE VICTORY ROAD EXIT SIDE, AND HEAL AT A POKÉ CENTER (NOT ITEMS).**
User: *“Pokemon center if needed or healing items, but given healing items cost money, the pokemon
center is fine, but we should use the room right before we leave the victory road onto the other side
of the ever grande island where the elite 4 building is as it would be faster to go back and forth
from there.”*
⇒ ⭐⭐ **THIS SETTLES THE GROUND QUESTION AND KILLS THE B1F BRANCH.** The named location is the
Victory Road area immediately before the exit — which is exactly `TRAIN_SPOT_1F = (VICTORY_ROAD_1F,
(15,39))`, documented as *“1 step from the entrance warp”* (`victory_road.py:477`) and the ground the
only proven grind driver already uses.
⇒ ⛔ **B1F IS OFF THE TABLE** despite its better EXP/battle (950.8 vs 775.6). It is one warp deeper,
has **no verified spin tile anywhere in the repo** (`PENDING_GRASS` carries `None`), and the whole
point of the user's instruction is round-trip SPEED. **Do not reopen B1F without a new ruling.**
⇒ Healing items are rejected on COST, not on mechanics — relevant because §Ch23 leg 11 spends
₽54,300 on the Elite Four basket against a measured ₽56,041, i.e. ₽1,741 of slack.

### RULING 3 — **THE ELITE FOUR BUILDING HAS BOTH A NURSE AND A MERCHANT, BEFORE THE GUARD.**
User: *“There is a nurse and merchant in the elite 4 building right before you talk to the guard to
get through the door to the elite 4. Flying is still a fast way to get around but only to areas that
have been unlocked (visited the pokemon center or in the elite 4 building case, at least entered the
building once).”*
⇒ ✅ Corroborates our own code: `heal_at_league` navigates to `LEAGUE_NURSE_STAND (3,4)` on
`POKEMON_LEAGUE_1F`, and §Ch23 leg 11 shops in the same building.
⇒ **Fly is available to unlocked destinations only**, and entering the League building once unlocks
it — so a §Ch24 leg may use Fly for the long hop, but must not assume it before the first entry.

### ⭐ WHAT THESE RULINGS RESOLVE, AND ONE CONTRADICTION THEY DISSOLVE
✅ MEASURED by me the same day (`probe_vr_heal_roundtrip.py`): from `EVER_GRANDE_CITY (18,42)` — the
**Victory Road exit side** — the Poké Center door `(27,48)` is **OK, 23 waypoints**; from
`EVER_GRANDE_CITY (18,6)` — the **League door side** — it is **NO PATH on a same-map ask**.
⇒ **those two readings looked like a problem and are actually the ruling's justification**: the user
is telling us to grind on the side from which the Poké Center IS reachable. ⇒ `#24-cavehealblind`
shrinks from *“can a Victory Road grind heal at all?”* to *“does `train_team`'s heal actually execute
the short round trip from `TRAIN_SPOT_1F`?”* — still a DRIVE, but a far smaller one.

### ⚠ NOTED, EXPLICITLY NOT ADOPTED — THE LEGENDARY OPTION
User: *“we can catch legendary pokemon (rayquaza for example) … rayquaza also starts at level 75 and
has fly … so we could send the bot on a legendary hunt if needed or as a random decision it makes so
every run is different … this is just a thought not a suggestion of what we do as it may derail a
lot, we should focus on the battle and mapping mechanics of the elite 4 first.”*
⇒ **RECORDED AS A FUTURE OPTION, NOT SCHEDULED.** A L75 Rayquaza with Fly would sidestep the grind
entirely, and “random per run” is an interesting variability feature. ⛔ **Do not start it** — the
user scoped it out of the current work in the same breath. §Ch21 already reaches Rayquaza's map
(Sky Pillar), so the capability is closer than it looks; that makes it MORE important not to drift
into it before the Elite Four's battle and mapping mechanics are done.


## 2026-09-18 (second round) — ⭐ USER RULINGS: TIME IS NOT THE CONSTRAINT, LEVEL-APPROPRIATENESS IS

Follow-up questions on the §Ch24 grind. These change a premise several items were built on.

### RULING 4 — **TIME IS NOT A CONSTRAINT. LEVEL-APPROPRIATENESS IS.**
> *“Time is not really a problem so long as they are training in appropriate areas (best level
> location to level up for the pokemon being trained) … its fine if it takes a while to level up so
> long as they are not fighting super low level monsters (norman gym for example, level 30s should
> not be fighting level 3-5 for xp)”*

⇒ ⛔⛔ **THIS RETIRES “THE GRIND IS TOO EXPENSIVE” AS AN OBJECTION.** `#24-levelgap`'s whole
frame-budget analysis — including my own measurement that every 2-level step exceeds
`MAX_TRAINING_FRAMES` once the estimator's ~3.3× optimism is corrected — was answering a question
the user is not asking. **A long grind is acceptable.**
⇒ ⭐ **WHAT REPLACES IT AS THE QUALITY BAR: the level GAP between trainee and wild.** The refusal
that matters is not “this will take N frames” but “this party is 30 levels above this grass”.
⇒ ⛔ **AND THAT IS A DEFECT WE HAVE ALREADY MEASURED IN OUR OWN CODE.**
`best_training_area(team_level=53)` returns `(ROUTE117, (31,16), (13,14))` — **L13-14 wilds for a
L53 party**. Our recorded response was a comment saying *“⛔ never ‘improve’ this by asking the table
for the grind tile”*; the ruling says the TABLE is what should be fixed. Filed as
`#24-trainingbrackets`.
⚠ **WHAT THIS DOES *NOT* RETIRE:** the per-call ceiling still exists in
`train_for_victory_road`, and a leg calling `train_team` directly still inherits **no budget at
all** (KI-28 burned 19.9M frames that way). “Time is not a constraint” is a statement about the
USER'S patience, not a licence for an unbounded loop. **Bound the loop; just do not refuse on cost.**

### RULING 5 — **START THE ELITE FOUR TRAINING AFTER VICTORY ROAD, AFTER THE FIRST LEAGUE-NURSE HEAL.**
> *“the further the bot gets into the story, more of the map becomes available and that means more
> higher level areas appear for training so the arduous training task (training for elite 4) should
> really start when the bot finishes victory road after first healing at the elite 4 nurse”*

⇒ a precise placement: **after §Ch23 leg 10 (`heal_at_league`), not before.** That is the §Ch24
side of the boundary, which matches the 2026-09-18 reversal that moved the grind off §Ch23 — and it
now has a second, independent reason: **the map is at its largest there**, so the best grounds are
available. ⇒ the leg should be free to pick the best ground in the game at that point, not just
Victory Road's.

### RULING 6 — **LOSSES ARE ACCEPTABLE; MONEY IS A HIGH PRIORITY.**
> *“loses are fine, keep in mind the goal is to not constantly lose to the elite 4, but a few are
> acceptable as that is natural, but the goal is to win against the elite 4 as organically as
> possible so loses are expected but preserving money is another high priority as money is
> relatively limited (trainers take forever to refresh their battle state with the player, selling
> nuggets that are found gain a lot of money so are worth noting as well)”*

⇒ **THE OPTIMISATION TARGET IS NOT “MAXIMISE WIN RATE”.** A few losses are *expected and natural*.
⇒ ⛔ **BUT A LOSS COSTS MONEY** — `DoWhiteOut()` calls `SetMoney(money/2)` (decomp
`src/overworld.c:358-366`), and §Ch23 leg 11's Elite Four basket costs ₽54,300 against a MEASURED
₽56,041, i.e. **₽1,741 of slack**. ⇒ the real constraint on losing is the BANK, not pride.
⇒ ⭐ **NUGGETS ARE FLAGGED AS A MONEY SOURCE WORTH USING**, and trainers are noted as effectively
one-shot. Both are being researched (`#24-trainingbrackets` workflow).

### RULING 7 — **RESEARCH WHETHER POKENAV REMATCHES ARE USABLE.**
> *“also maybe look into if pokenav can be used for fighting trainers again either initiated by the
> user using the pokenav or if they call the player (log the calls to map to them if they are a
> viable training trainer or for money) … something to deliberate about and research”*

⇒ an explicit RESEARCH instruction, not a build instruction. If Match Call rematches are a
repeatable EXP/money source they would address rulings 4 and 6 simultaneously — level-appropriate
opponents that scale, and income that is not one-shot. Commissioned; **no code until the research
lands and its load-bearing claims are verified here.**


## 2026-09-18 — ⭐ USER RULING 8: “REGULAR SPEED” MEANS ×1 IN PRODUCTION; FAST-FORWARD IS FOR DATA

I recorded an INTERPRETATION of ruling 2 into `01-VISION-AND-DESIGN.md` (that regular speed is a
requirement and fast-forward a dev tool), then asked the user to confirm it before it drove any
engineering. **Confirmed, in these words:**
> *“yes you read that right, regular speed is ‘x1’ or normal speed for the actual production
> gameplay, speed up is for dev testing so we dont have to wait hours upon hours or even days to get
> data”*

⇒ **THE CARVE-OUT IS NARROW AND NAMED: fast-forward exists to collect DATA, never to play the game.**

### ✅✅ AND THE CODE ALREADY SATISFIES IT — MEASURED, SO NOBODY NEEDS TO RE-INVESTIGATE
| fact | evidence |
|---|---|
| the emulator defaults to ×1 | `modules/libmgba.py:103-104` — `_throttled: bool = True`, `_speed_factor: float = 1` |
| production story code NEVER changes speed | grep for `set_throttle(` / `set_speed_factor(` over `sandbox-pokebot/modules` + `plugins`: **zero** call sites outside the setter itself |
| the ONLY setter is config-driven | `modules/context.py:100-105` — `emulation_speed = 0` routes to `set_throttle(False)`; anything else throttles and sets the factor |
| every unthrottle is DEV TOOLING | `tools/story-dev/story_harness.py` and the batch lanes (`x4_headless.py -s 0`) |
| the project already treats “fast” as a harness property | gate `probe_gate_unthrottled.py` exists to ensure **dev probes** are unthrottled |

⇒ ⛔ **NO DEFECT, AND NO WORK ITEM.** Recorded precisely so this is not re-opened as a task.
⇒ ‼ **THE STANDING CONSEQUENCE:** a future change that unthrottles PRODUCTION is a **vision-level
regression**, not a performance tweak. If runtime ever becomes a problem the answer is not to speed
the game up — it is to change what the bot does, or to accept the duration (RULING 4 already says
time is not a constraint).

‼ **METHOD NOTE, because it nearly went the other way:** I had already written the interpretation
into the source-of-truth doc before asking. That was the wrong order — the doc was carrying an
unconfirmed reading of a user statement for several commits. It happened to be right. **Ask first
when the edit lands in `01-VISION-AND-DESIGN.md`**, which is the one file whose job is to be the
source of truth for intent.


## 2026-09-18 — ⭐ USER DIRECTIVE: A REMATCH LEDGER, AND A PER-CHAPTER MAP KNOWLEDGE BASE THAT IS *PRODUCT*

Two asks, plus a statement about what this project is FOR that extends
`01-VISION-AND-DESIGN.md` §2.

### THE ASKS
1. **Investigate PokeNav rematching properly**, including *“does the user call them, or does the
   trainer/gym leader call the user?”*, and produce **a LEDGER of every eligible trainer/gym leader
   with their Pokemon, stats and rewards**, so we can *“gauge who is actually worth fighting again
   for money/xp”*. ⭐ Two user recollections to verify: ordinary rematches unlock after **Norman (5th
   gym)**; gym-leader rematches unlock after **the Elite Four / Hall of Fame**.
2. **A per-chapter picture of the whole gameplay map** — walkable tiles, obstacles and what clears
   them (HMs, tasks), so the bot knows *“WHERE its able to go depending on what part of the story its
   at”*, feeding routing, training routes, rematch routes and possibly item pickups.

### ⭐⭐ THE PART THAT CHANGES THE VISION DOC
> *“as well as be a great resource for the future AI pilot version of this program … this program is
> an art piece that is also laying the foundation to help speed up training a ai agent to play the
> game as organically as possible to be the ‘v2’ of this art piece”*

⇒ §2 of the vision doc described the substrate as **documentation** — human-language intent. It now
also includes **machine-readable GAME KNOWLEDGE**. ⇒ **the map/traversability/ledger data is PRODUCT,
not tooling**, and is built to be handed forward.

### ⚠ THE SCOPE RULING I AM APPLYING UNTIL TOLD OTHERWISE
The bot **cannot yet beat the Elite Four**, and a full map knowledge base is a large detour from
that. ⇒ research first (an 11-agent workflow is running, briefed to say **what should wait**), then a
scope decision, then build. ⛔ **§Ch24 is not blocked on this**, and this is not started before the
research lands. If the user wants it prioritised ahead of §Ch24, that is a ruling I do not have.


## 2026-09-18 — ⭐ USER RULINGS 9 & 10: THE LEDGER IS TWO ARTIFACTS; OVERWORLD ITEMS ARE USER-GATED

### RULING 9 — **BUILD BOTH A STATIC LEDGER AND A RUNTIME “CALL LEDGER”.**
> *“A bit of both, having the ledger from the getgo is helpful but having a sort of ‘call ledger’ to
> know who has actually called and is available to fight would be the second piece to this.”*

| artifact | source | answers | limits |
|---|---|---|---|
| **static ledger** | generated from ROM/decomp | *who is worth fighting, and for how much* | cannot know who is ARMED |
| **call ledger** | written at runtime | *who has actually rung and is fightable now* | cannot know worth until they call |

⇒ ⭐ **AND THE STATIC TABLE DOUBLES AS THE CONTROL FOR THE RUNTIME ONE:** a logged call naming a
trainer that is ABSENT from the static table means our extraction is wrong. Without the pair, that
class of bug is invisible. ⇒ build the static half first (it needs no UI work); the runtime half is
gated on PokéNav menu-driving, for which appetite has been asked and not yet given.

### RULING 10 — **OVERWORLD ITEMS ARE DEFERRED, AND THE GATE IS A HUMAN JUDGEMENT.**
> *“Out for now but worth investigating in the future once we get the bot to complete the elite 4
> successfully **to my liking** … ground items/thief items/reward items/gifted items (like quick claw
> for example) … note **I may call for this earlier and that is ok** but for now it should be gated to
> be worked on AFTER the bot beats the elite 4 to my liking/standards.”*

⇒ Filed as `#24-overworlditems`, **DEFERRED**.
⛔⛔ **THE TRAP THIS RULING SETS FOR A FUTURE AGENT, STATED PLAINLY:** the gate is *“to my
liking/standards”* — **a judgement the bot cannot self-certify.** ‼ Do NOT open it by checking
`SYS_GAME_CLEAR` / `IS_CHAMPION`, and do NOT open it because a drive beat the Elite Four — **that has
already happened** (2026-09-17, `--driver ch24tailprobe`, from a pinned L75 fixture) and the gate is
still shut. Only an explicit user instruction opens it. The gate IS soft in one direction: the user
said they may call for it earlier, *“and that is ok”*.
⚠ **ONE ITEM ERRAND REMAINS IN FLIGHT AND IS NOT COVERED BY THIS DEFERRAL:** `#24-amuletcoin`, a
single targeted fetch justified by RULING 6 (money is a high priority). ⛔ It must not be used as a
wedge to start general item work.


## 2026-09-18 — ⭐⭐ USER RULING 11: THE §Ch24 ACCEPTANCE BAR, AND IT IS BIGGER THAN THE ITEM THAT PROMPTED IT

Asked what *“beats the Elite Four to my liking/standards”* means, since it gates
`#24-overworlditems`. The answer defines DONE for the whole §Ch24 arc:

> *“it beats the Elite 4/enters the hall of fame … so I guess the response **‘Wins organically — no
> fixture scaffolding, no harness driver, running as the real story mode at ×1’**”*

### ✅ THE BAR, AS FOUR CHECKABLE CONJUNCTS
| # | conjunct | how it is checked |
|---|---|---|
| 1 | the **Hall of Fame** is entered | the in-game signal (`SYS_GAME_CLEAR` / `IS_CHAMPION`) |
| 2 | from the **REAL story mode** | not a `--driver` in `story_harness.py` |
| 3 | **no fixture scaffolding** | not launched from a pinned `.ss1`; the bot got itself there |
| 4 | at **×1** | `emulation_speed` throttled — see RULING 8 |

⇒ ⭐⭐ **THIS IS THE §Ch24 DEFINITION OF DONE, not merely a gate on item work.** Every §Ch24 result
so far — all five Elite Four rooms, the Champion, the lobby fixtures — satisfies (1) at best and
fails (2), (3) and (4). ‼ **“The bot has beaten the Elite Four” is therefore TRUE of the harness and
FALSE of the product**, and every doc that says it should be read with that distinction in mind.

### ⛔ A CORRECTION OF RECORD TO RULING 10, MADE THE SAME DAY
Recording ruling 10 I wrote, on `#24-overworlditems`: *“DO NOT unlock this by checking
`SYS_GAME_CLEAR`, `IS_CHAMPION`, or a single winning drive … the bot cannot self-certify that”*.
‼ **Too strong, and now corrected.** The flag IS conjunct (1); it is simply **not sufficient alone**.
What I was reaching for — and should have written — is that the flag says WHAT happened and says
nothing about **HOW**, and the other three conjuncts are entirely about provenance.
✅ The substance survives: the 2026-09-17 win satisfies (1) and fails (2)-(4), so the gate is shut.

### ‼ WHY THIS RULING IS WORTH MORE THAN THE QUESTION THAT PRODUCED IT
It converts an unfalsifiable acceptance criterion (*“to my liking”*) into four conjuncts a gate could
one day assert. ⇒ **when §Ch24 is wired, its acceptance should be graded on these four**, not on
“the driver printed PASS”. That is the same lesson §Ch15/§Ch18/§Ch19 taught — three chapters that
passed their own tests while stranded — applied one level up: **the CHAPTER can pass its own test
while the PRODUCT has not done the thing.**


## 2026-09-18 — THE VICTORY ROAD TRAINING ROW IS NOT ADDED UNTIL `#24-waterfallcap` IS FIXED; THE CAP FIX ITSELF MAY LAND ALONE, AND FIRST

**THE DECISION.** Do **not** add `(VICTORY_ROAD_1F, (15,39), (36,40))` to `TRAINING_GRASS`, and
do not add `AREA_PREREQ[VICTORY_ROAD_1F]`, on today's code — they would be inert.
✅ **`#24-waterfallcap` (the capability fix) MAY BE DONE ON ITS OWN, AND FIRST.** Once it is in,
add the two data edits **together with each other** — the row must never ship without its
`AREA_PREREQ` row — and prove the result with a drive.
‼ *(This clause first read “add both edits and the cap fix as a single change”. That came from
the audit's ordering argument, which I refuted at source before committing — see below. A Tier 1
reviewer caught that the correction had reached the body and NOT this decision line or the
title, which is precisely the P2 “the headline carries the caveat” failure.)*

**WHY (verified, not asserted).** `is_map_reachable(VICTORY_ROAD_1F)` is False for every party at
every badge count: `region_reach.py:97` gates the only edge on `"waterfall"`, `:342` drops
gate-missing edges, and `_resolve_caps` (`:228-236`) only ever resolves `surf`, `rock_smash`, `cut`
and `strength`. ⇒ the `AREA_PREREQ` row would gate on a predicate that is already permanently
False, so the pair of edits would change nothing.

**⭐ THE PART THAT MAKES THIS AN ORDERING DECISION — AND THE AUDIT GOT ITS DIRECTION BACKWARDS.**
The audit argued the reachability bug is an *accidental safety net*, so fixing it alone would
expose Victory Road to `_training_area_allowed` / `_counter_area_allowed` for any L35+ party at
any story point. ⛔ **I verified that at source before committing, and it is refuted:** with no
Victory Road row in `TRAINING_GRASS`, `best_training_area` cannot return it at all, and the cap
resolves through `_live_capability` to **Badge 8 ∧ a party Waterfall user**, never
unconditionally True. ⇒ **the cap fix is safe alone and may land first.**
✅ **THE COUPLING THAT IS REAL RUNS THE OTHER WAY.** `best_training_area` under the production
default `allow=None` performs **no reachability check whatsoever** — it only skips areas that
HAVE an `AREA_PREREQ`. ⇒ the `TRAINING_GRASS` row must NEVER land without its `AREA_PREREQ`
row, or Victory Road is proposed to any L35+ party at any story point, ungated. **That pair is
inseparable** — not the cap.
⛔⛔ **AND A THIRD REQUIREMENT, ADDED THE SAME DAY AFTER A TIER 1 REVIEW READ THE AUDIT'S VERBATIM
§7 — THE PAIR ABOVE IS NECESSARY BUT **NOT SUFFICIENT**.** ✅ Verified at source:
**`best_training_grass` iterates the SAME `TRAINING_GRASS` table**, and its gate is
`training_areas.py:242` — `if allow is not None and not allow(…)`. At `allow=None` it does **no
prereq and no reachability filtering whatsoever**; `AREA_PREREQ` is never consulted there. ‼ That
asymmetry is DELIBERATE and documented at `:213-219`: it *"keeps its historical behaviour when
`allow is None` — no filtering at all"* because it is also injected as `decide_maintenance`'s
`ground_for`, where narrowing the default would change a pure decision's answers and gate #55's
expectations. ⇒ **adding the row requires THREE things, not two**, and ⛔ the third must NOT be
"make `best_training_grass` behave like its sibling" — that is the change its docstring warns
against. ⭐ **Recommended shape (the audit's own, and it leaves `decide_maintenance` untouched): a
regression gate asserting `best_training_grass(40) is not VICTORY_ROAD_1F`.**
⛔⛔ **MEASURED 2026-09-18 (LATER THE SAME DAY) — “SAFE ALONE” WAS TOO STRONG, AND MY OWN A/B IS WHAT REFUTED IT** (`probe_waterfall_fix_ab.py`, evidence `evidence/2026-09-18-waterfall-fix-AB.stdout.txt`). The fix DOES change a wired production predicate. ⇒ **THE ACCURATE STATEMENT, IN THREE PARTS:**
  * ✅ **AT THE EXECUTOR LEVEL, NOTHING CHANGES.** `best_huntable` — documented as *“the ONLY function an executor should use to pick where to go”* — is **identical in both arms**, on every fixture, for Fighting/Ghost/Dark. `huntable` stays **False** for every Victory Road candidate, because `hunt_ground_tile` is a strict whitelist. **The bot cannot be sent anywhere new.**
  * ⛔ **AT THE RANKING LEVEL, THINGS DO CHANGE.** Victory Road candidates flip `reachable=False -> True`, so they re-order in `find_counter_candidates`' list, and `best_training_area(allow=_counter_area_allowed)` goes **`None` -> `ROUTE121(44,14)`** — ⚠ **but ONLY from a position INSIDE Victory Road.** From Ever Grande and from the League lobby, **every picker answer is byte-identical**.
  * ✅ **AND NO PRODUCTION CODE IS KNOWN TO ASK FROM IN THERE:** a caller census found **zero** `region_reach` references in `victory_road.py` and `pokemon_league.py` — §Ch23 hardcodes `TRAIN_SPOT_1F` and uses `navigate_to_anywhere`. ⚠ That is an ABSENCE claim over a large codebase, so treat it as the weakest leg.
  ⇒ **THE RULING STANDS IN SUBSTANCE — the cap fix may still land alone — but NOT on the grounds originally given.** It is not “exposes nothing”; it is “changes ranking only, and only from inside the cave, with the executor guard measured intact.”
✅ **A CLAIMED FOURTH BLOCKER WAS MEASURED AND DISMISSED.** `_MAX_TRAINING_TRAVEL_LEGS = 4`
(`story_mode.py:1101`, passed as `max_hops` at `:1269`) was called a second blocker on an
**INFERRED-STRONG, never measured** hop count. Measured: Victory Road would sit **1 hop** from Ever
Grande and **2** from the League lobby, against a budget of **4** ⇒ not binding here.

**ALTERNATIVES REJECTED.**
* *Add the `TRAINING_GRASS` row alone.* Rejected: `VICTORY_ROAD_1F` has no prereq, so it would be
  proposed to any L35+ party at any story point immediately.
* *Add both data edits now and fix the cap later.* Rejected: inert today, and it leaves a row whose
  only guard is a predicate that silently flips from always-False to permissive the moment the cap
  is resolved — a landmine for whoever fixes `#24-waterfallcap` without reading this entry.
* *Fix `_resolve_caps` now as a one-key bug fix.* ✅ **NOT rejected** — this is `#24-waterfallcap`,
  it is safe on its own, and it may land first. `_live_capability` already resolves Waterfall
  correctly and fails safe (`_RSE_BADGE_BY_MOVE["Waterfall"] = "BADGE08_GET"` ∧ a live party
  move check). *(This bullet first read “rejected for the safety-net reason above”; that reason
  was the audit's and is refuted — see above.)*
* *Route around the picker, as we already did.* Rejected by USER RULING 2026-09-18 — *"maybe we need
  to map and mark training areas for pokemon for level brackets"*. The ruling says fix the table.

⛔⛔ **THE “DO NOT REOPEN” THAT WAS HERE HAS BEEN WITHDRAWN AND REPLACED — SAME DAY, BY EVIDENCE.**
It read: *“DO NOT REOPEN the question of adding the row alone, or of fixing the cap alone.”* ‼ I
attached that to a claim I had **argued** but never **measured**; an A/B an hour later showed the
cap fix does change `_counter_area_allowed`'s answers from inside Victory Road. An adversarial
review then caught that this entry had not been updated. ⇒ see the narrowed three-part claim above.

✅ **WHAT IS ACTUALLY SETTLED, AND MAY BE TREATED AS DO-NOT-REOPEN, BECAUSE IT IS MEASURED:**
* The `TRAINING_GRASS` row must never land without its `AREA_PREREQ` row *(source: `training_areas.py:504-505`)*.
* Adding that row does **not** make Victory Road huntable *(source: arm C — `hunt_ground_tile` defaults `require_driven=True` and never reads `TRAINING_GRASS` in that mode)*.
* `_MAX_TRAINING_TRAVEL_LEGS = 4` is not binding here *(source: measured 1-2 hops)*.
⚠ **WHAT IS NOT SETTLED AND MAY BE REOPENED FREELY:** whether the ranking-level change from inside Victory Road is acceptable, and whether the cap fix wants a companion narrowing of
`_counter_area_allowed`. **No fixture exercises a boss fought from inside Victory Road.**


## 2026-09-18 — A PRE-REGISTERED ABORT CONDITION FIRED AND I PROCEEDED ANYWAY — HERE IS THE REASONING, ON THE RECORD

**THE DECISION.** Land the `#24-waterfallcap` fix, even though abort condition 3 in
`ai-research-notes/2026-09-18-waterfallcap-PREDICTIONS.md` — *"the decomp pass shows exiting
Victory Road needs no field move"* — was **triggered**.

**WHAT FIRED IT.** A decomp pass decoded `data/layouts/EverGrandeCity/map.bin` and placed the
`MB_WATERFALL` block at x≈15-26, y≈60-67 — **inside Ever Grande City**, between the Route 128
arrival seam and the rest of the town. ✅ **Our own live-measured constants agree tile-for-tile:**
`victory_road.py:128-130` has `WATERFALL_BASE = (18, 68)`, `WATERFALL_TOP = (18, 59)`,
`EG_LANDING = (18, 55)`, and `VR_DOOR = (18, 41)` (`:138`) is dry land north of the landing, with
`ch23route` R11b measuring `(18,55) -> (18,41)` as a plain 16-waypoint walk.
⇒ **the gated edge needs no field move, and the edge that does (`ROUTE128 <-> EVER_GRANDE_CITY`)
has no entry at all.**

**WHY I PROCEEDED, AND WHY THIS IS NOT RATIONALISATION.**
1. ⭐ **The gate is a MAP-GRANULAR APPROXIMATION OF A TILE-GRANULAR FACT, and that is the only
   thing a map graph can express.** The falls split **one map**; "the northern half of Ever Grande"
   is not a node. Gating the Victory Road edge is correct by construction, and `0c1d6686`'s own
   comment says so: *"that entrance sits at the TOP OF A WATERFALL, so HM07 is mandatory to stand
   on it."* The author modelled the TILE requirement on the nearest available EDGE.
2. ✅ **It is observationally correct for every reachable game state.** No party can be north of
   the falls without Waterfall, so "can reach Victory Road" and "holds Waterfall + Badge 8" are the
   same predicate for anyone standing in town — and anyone inside Victory Road got there through
   town, so the symmetric seal is right for the same reason.
3. ✅ **It is strictly better than what it replaced.** Before, the gate could never open for
   anybody. After, it opens exactly for parties that really can pass.

**‼ WHAT I DID NOT DO, DELIBERATELY: move the gate to the correct edge.** That would change
`is_map_reachable(EVER_GRANDE_CITY)` from True to False for every pre-Badge-8 party — a
whole-game blast radius deserving its own A/B. Filed as `#24-gategranularity`, which also records
the genuinely missing `ROUTE128 <-> EVER_GRANDE_CITY` ocean edge (**ungated today**, so a no-Surf
party is told Ever Grande is reachable — the same shape as the two Dewford rows that WERE gated).
⛔ **Order matters: add the Route 128 surf gate FIRST.** Moving the waterfall gate first would
open Victory Road to anyone who can reach the town's southern shore.

**ALTERNATIVES REJECTED.**
* *Abandon the fix because the condition fired.* Rejected: the condition was written to catch "the
  fix makes the bot believe something false." It does not — it makes a permanently-false predicate
  answer correctly. Honouring the letter here would have preserved a strictly worse state.
* *Fix the placement in the same change.* Rejected for blast radius (above).
* *Quietly proceed without recording that the condition fired.* ⛔ Rejected outright — that would
  destroy the point of pre-registering, which is to stop me reinterpreting a result to suit what I
  already wanted. **The condition fired; this entry is the cost of overriding it.**

⚠ **REASONED, NOT MEASURED — reopen if you can test it:** claim 2's *"no party can be north of the
falls without Waterfall"* rests on the decomp's collision decode plus our own constants, **not on a
live probe of a Waterfall-less party standing in Ever Grande**. That probe is the way to settle it.


## 2026-09-18 — VICTORY ROAD IS NOT PROMOTED INTO `TRAINING_GRASS`, AND `#24-trainingbrackets` CLOSES WITHOUT A CODE CHANGE

**THE DECISION.** Do not add `(VICTORY_ROAD_1F, (15,39), (36,40))` to `TRAINING_GRASS`, do not add
`AREA_PREREQ[VICTORY_ROAD_1F]`, and do not build the proposed regression gate. Close the item.

**WHY — five reasons, each verified, any one sufficient.** Full working:
`ai-research-notes/2026-09-18-trainingbrackets-CLOSED.md`.
1. ✅ **The defect is a call shape production never makes.** `best_training_area(53) → ROUTE117
   (L13-14)` happens only at `allow=None`; all four production callers pass a real predicate. With
   one, the same table answers `ROUTE121 (25,28)`.
2. ✅ **The remedy already ships.** `victory_road.py:2087-2090` already grinds at
   `TRAIN_SPOT_1F = (15,39)` with the Ever Grande centre — the identical tile.
3. ⛔ **The proposed gate was self-refuting** — executed, it returns VICTORY_ROAD_1F the day the row
   lands, because `best_training_grass` does no filtering at `allow=None` by design.
4. ⛔ **The generic path lacks the hardcoded path's supports** — no heal-map row, no `_CAVE_EXITS`
   row, no frame cap.
5. ⛔ **`victory_road.py:3425-3429` already warned against it** and demanded an adversarial pass. It
   got one; it was refuted.

**⭐ WHAT THIS DOES NOT MEAN.** The user ruling that created the item stands and is SATISFIED: §Ch23
trains a ~L47 party on L36-40 wilds. The bracket map it asked for already exists at
`training_areas.py:27-61` and was independently re-corroborated dual-source today (decomp + our own
live-ROM cache, 38 rows, zero mismatches).

**⇒ WHAT REPLACES IT.** `#24-levelgap` — a purpose-built §Ch24 stepped leg driving
`train_team(..., grass=TRAIN_SPOT_1F)` with its own MEASURED frame budget. That was already the
ruling; this item was the wrong road to it.

**DO NOT REOPEN the promotion** — reason 1 and reason 2 are measurements I took myself, and reason 3
was reproduced by execution. ⚠ **REASONED, NOT MEASURED — reopen freely:** whether BOTH
`_training_area_heal_map` consumers should fail safe (`#24-healmapfallback`), and whether Victory
Road B1F's Rock Smash table (L30-40 at **rate 20**, twice any Victory Road grass table) is worth
using if USER RULING 2's B1F exclusion is ever revisited.


## 2026-09-18 — ⭐ USER RULING: EVERY TEAM MEMBER MUST BE L65-75, AND THEY NEED NOT MATCH

**THE RULING, VERBATIM:** *"I think all pokemon in the team need to be a level between 65-75, but
not all need to be the same level."*

**WHAT IT SETTLES.**
* The §Ch24 target is now a **BAND WITH A FLOOR ON EVERY MEMBER**, not a party average and not a
  single number: **every battler ≥ 65**, and **≤ 75** is sufficient — there is no requirement to
  push anyone to 75.
* **Per-mōn targets may differ.** ⇒ a stepped leg may train each member to its own stopping point;
  it does NOT need to level the party uniformly, which is the cheaper and more natural shape.
* It supersedes the looser "L62-75" framing: **62 is no longer acceptable for any member.** The
  earlier L62 figure was a measured *break-even* for the gauntlet; the ruling raises the floor.

**⚠ THE QUESTION IT IMMEDIATELY FORCES, AND I AM NOT ASSUMING THE ANSWER.** The pinned §Ch24
parties carry **Zigzagoon L19** and **Castform L36**. Read literally, "all pokemon in the team"
means both must reach L65 — and priced against the measured 3.30×-corrected model that is roughly
**31 h and 28 h at ×1 respectively**, i.e. the majority of the whole grind, for two mōn that
contribute little to the gauntlet.
⇒ **Two readings, and they differ by tens of hours:**
  (a) *train everyone* — literal, expensive, and keeps the party the user has seen; or
  (b) *the "team" is who fights* — box or drop the two stragglers, then train the rest to ≥65.
⛔ **DO NOT SILENTLY PICK (b).** Removing a Pokémon from the party changes what the art piece shows,
and this project has no user ruling permitting it. Research whether the bot even CAN deposit a mōn,
price both readings, and put the choice back to the user with numbers attached.

✅✅ **THE SAFETY HALF IS NOW MEASURED** (`probe_party_l65_audit.py`, evidence
`evidence/2026-09-18-party-l65-audit.stdout.txt`), read from the saves rather than from any doc —
party MOVES are recorded nowhere else. On `post_ch24_atdoor_L75.ss1`, **2 of 6** are below the
floor: **Zigzagoon L19 (≈20.4 h)** and **Castform L36 (≈17.1 h)**, ≈**37.5 h** summed.
* ✅ **BOTH ARE NAVIGATIONALLY FREE TO REMOVE.** Zigzagoon's `Rock Smash` and `Surf` are each held
  by another member (Sceptile, Wailord); Castform holds **no field move at all**.
* ⛔⛔ **THE THREE THAT CAN NEVER BE BOXED:** `Waterfall ← Wailord`, `Dive ← Wailord`, `Fly ← Swellow`
  — sole carriers. Waterfall is what reaches Ever Grande at all, so losing Wailord strands the run.
* ℹ Nobody holds `Cut` or `Flash` — fine only while no §Ch24 route needs them (Victory Road 1F does not; B1F/B2F, which do need Flash, are OFF THE TABLE per RULING 2).
⇒ **what remains open is only (i) whether the bot CAN deposit, and (ii) whether the USER wants the
party changed. The navigational objection to (b) is answered: there isn't one.**

**WHAT DOES NOT CHANGE.** The grind ground stays `TRAIN_SPOT_1F` (USER RULING 2), and the training
host stays a purpose-built §Ch24 leg rather than the generic picker (`#24-trainingbrackets` closed
2026-09-18) or §Ch23 (reversal, 2026-09-18). The wild-level ceiling is unchanged and proven: nothing
in the game exceeds L44 usable, so a L65 floor means the last stretch is fought against wilds ~25
levels below the trainee.


## 2026-09-19 — ⭐⭐ USER RULING: TRAIN EACH MŌN AT A LEVEL-APPROPRIATE GROUND, AND FLY TO REACH IT

**THE RULING, VERBATIM:** *"Training needs to be enhanced the way we discussed earlier as far as how
the bot decides to train the team member by going to a level appropriate area/zone for the pokemon
being trained so it can actually fight or be swap trained"* — and, asked how to reach grounds beyond
the walking budget: **"Fly there, per trainee."**

**⭐⭐ WHY THIS IS THE RIGHT ANSWER AND NOT MERELY A PREFERENCE — IT DISSOLVES A CONTRADICTION I HAD
JUST PROVED.** I had verified that the L65-75 ruling was unsatisfiable by training the mules at
Victory Road: `SwapTrainBattleStrategy` fires when the trainee is `UNDERLEVEL_MARGIN = 2` or more
below the foe, which puts TWO participants in the battle, so the finisher banks an equal share and
Wailord reaches **L89 (L94 with the ×1.5 trade boost)** — 14-19 levels over the cap.
✅ **A trainee fighting wilds AT ITS OWN LEVEL never triggers that switch**, so it solos for **FULL
xp as the only participant**. ⇒ **no exp leaks to a finisher, and the ceiling is preserved by the
mechanic instead of fought against.** The ruling is not a compromise; it removes the failure mode.

**✅ MEASURED, AND IT IS WHY THIS NEEDS NEW WORK.** From Ever Grande, `_training_area_allowed`'s
`_MAX_TRAINING_TRAVEL_LEGS = 4` refuses **every** route ground — ROUTE121 is **6** hops, ROUTE118/119
**9**, ROUTE111/117 **11**, ROUTE115 **15**. The only level-appropriate ground inside the budget is
**VICTORY_ROAD_1F at 1 hop**, and it is inert (`PENDING_GRASS`, `tile=None`).
⇒ **a per-trainee selector would return `None` for every trainee today.**

**WHAT THE RULING THEREFORE REQUIRES:**
1. **Promote `VICTORY_ROAD_1F` into `TRAINING_GRASS`** with `(15,39)` / `(36,40)` — it is the only
   in-budget ground for the L34-46 bracket, and the battlers live in that bracket.
2. **A per-trainee ground choice** — pick per mōn from its OWN level, not one ground for the party.
3. **Fly to reach out-of-budget grounds** for low-level trainees. The hop budget is a proxy for
   WALKING cost; Fly makes it the wrong measure, so the leg bypasses it deliberately and for a
   stated reason rather than by raising the constant game-wide.

**⚠ THE TENSION WITH USER RULING 2, AND ITS RESOLUTION.** Ruling 2 put the grind at the Victory Road
exit side *"as it would be faster to go back and forth from there"*. That still holds **for the
battlers** — Victory Road is 1 hop and is their level-appropriate ground. Only the low-level mōn
travel, and only until they are in band. **Nothing about ruling 2 is reversed.**

**⛔ AND IT PARTLY REVERSES MY OWN CLOSURE OF `#24-trainingbrackets` (2026-09-18).** I closed that
item the previous day, and one of its five reasons was *"the remedy already ships — §Ch23 already
grinds on that exact tile"*. ✅ True of §Ch23's hardcoded call, and **false of the selector this
ruling requires**, which does not exist yet and cannot work without the promotion. The other four
reasons stand and still constrain HOW it lands (see the item). ⇒ **the item is RE-OPENED, with its
scope corrected.**


## 2026-09-19 — `max_wild_max` TAKES A NUMBER, NOT A MARGIN, BECAUSE `modules/` MAY NOT IMPORT `plugins/`

**THE DECISION.** `best_training_area`'s new out-level cap is expressed as **a number** —
`max_wild_max=mon.level + 1` — rather than as the conceptually tidier `underlevel_margin=2`.

**WHY.** The margin that matters is `SwapTrainBattleStrategy.UNDERLEVEL_MARGIN`, which lives in
`plugins/custom_modes/story_mode.py`. `training_areas.py` is a `modules/` file. Importing a plugin
from a module would invert this project's layering, and a picker that reaches into a battle
strategy for a constant is the kind of coupling that makes both untestable.
⇒ **the caller already knows the margin; the picker only needs the resulting cap.**

**ALTERNATIVES REJECTED.**
* *Duplicate `UNDERLEVEL_MARGIN` as a constant in `training_areas.py`.* Rejected: two copies of a
  tuning constant is exactly the shape that produced `#24-waterfallcap` (three tables that had to
  agree and nothing enforcing it).
* *Make `best_training_grass` honour `AREA_PREREQ` at `allow=None` instead.* ⛔ **REFUTED BY
  MEASUREMENT** — it changes 83 of 99 levels and makes every one worse. See `07-CHANGELOG.md`
  2026-09-19.
* *Have the leg filter the picker's answer itself.* Rejected: the picker would still RETURN a
  leaking ground, so every future caller would have to remember to re-filter. The cap belongs where
  the scoring happens.

⚠ **REASONED, NOT MEASURED — reopen freely:** that `mon.level + 1` is the right cap. It follows
from `UNDERLEVEL_MARGIN = 2` (swap fires at `trainee + 2 <= foe`), but no drive has yet confirmed
that a trainee at exactly `hi - 1` never swaps for the OTHER reason (the "can't continue" low-HP
trigger). `#24-ladderleak`'s probe states that limit explicitly.


## 2026-09-23 — USER DIRECTIVE: FISHING AS AN HM-CARRIER SOURCE, A SIX-MŌN TEAM, AND WORKING PC SWAPS — SCOPED AFTER §Ch24

**THE DIRECTIVE, VERBATIM:** *"when looking for a surf/dive/waterfall hm user or even a water type
pokemon, we need to make the bot have more options because if we get the fishing rods we can use
the best fishing rod we have at the moment to get a better/higher level water pokemon from
different parts of the world… along with unlocking the team from 4 pokemon to 6 and
validate/wire/improve the pokemon pc mechanics so the bot can catch pokemon and swap them around
between the team and pc like a normal human would do organically."*

**SCOPE RULING, FROM THE USER'S OWN FRAMING:** *"This should be slated as something we focus on
later"* ⇒ **it does not interrupt §Ch24.** Filed as `#25-partyroster`, numbered `#25` rather than
`#24-*` deliberately: it is the next chapter of work, not a §Ch24 sub-task.

**⭐⭐ THE FINDING THAT SHAPES IT — THE THREE PARTS ARE ONE PROBLEM.** The team is not capped at 4
by a constant: `PARTY_CAPACITY = 6` already (`story_mode.py:1500`). What holds it lower is a
deliberate **runway reservation** — post-Badge-1 a dex catch is refused while
`party_slots_used < PARTY_CAPACITY` (`story_mode.py:1664`), because the empty slots are the runway
HM and counter catches land on. ⇒ **the team is small because the PC does not work**, and the
reservation is the workaround. Fix the PC and it becomes unnecessary; raise the cap without fixing
the PC and the reservation's failure returns.

**⛔ AND THAT FAILURE IS MEASURED, SO THE ORDER IS NOT OPTIONAL.** `#24-partycap`: disturbing the
early party moved the finish rate **52.0% → 15.8%**, the entire loss on one badge rung, with
**10 of 16 non-finishes** reading *"No party mōn can learn Surf and the party is full"*. That
string is the directive's own motivation arriving from the other direction — the user wants more
HM-carrier options precisely because the bot runs out of them.

**⇒ THE ORDER THIS IMPLIES (suggested, not yet decided):** prove a PC round trip with a NAMED PID
first (`#24-pcoverflow` shows the withdraw half has never worked — it logged 0 in every batch);
only then relax the reservation and re-measure `#24-partycap`'s finish rate; then add fishing.
⛔ Relaxing the reservation before the PC works is the documented failure, not a shortcut.

**⭐ AND IT ADDRESSES A MEASURED SINGLE POINT OF FAILURE.** On the pinned §Ch24 party, Waterfall and
Dive are held by exactly one mōn (Wailord) and Fly by one (Swellow). Losing Wailord strands the run
— Waterfall is how Ever Grande is reached at all. A fishing-sourced water mōn is redundancy for the
two moves §Ch24's geography depends on, not a convenience.


## 2026-09-23 — THE FLY-AWARE PREDICATE IS A **DISJUNCT** OVER `region_reach`, NOT A `calculate_path` LAST-MILE CHECK

**THE CHOICE.** `_training_area_allowed` had to admit training areas that Fly can reach. Two shapes
were available:

* **(A) REJECTED — compute the last mile:** `calculate_path(fly_landing, (map, tile))` and admit the
  area if a path exists. Appealing because the predicate and the traversal would share one
  computation and could not disagree, and because I had just measured every last mile.
* **(B) CHOSEN — a disjunct on the existing oracle:** keep
  `region_reach.is_map_reachable(area, max_hops=4)` exactly as-is and add
  *"OR `can_fly_to_anchor(heal_centre)`"*, which mirrors `fly_to_destination`'s own three guards.

**WHY (A) IS WRONG, AND IT IS NOT A NEW ARGUMENT — IT IS A STANDING DECISION (2026-07-25, KI-24)**
recorded in `_training_area_allowed`'s own docstring. The failure modes are asymmetric:
> *A wrong **NO** from `calculate_path` is INVISIBLE and costs a whole run* — it reads the Route
> 118/119/120 dual-elevation bridges as WALLS, and fails even a same-map walk inside Route 119 — so
> a genuinely-good band is silently never proposed and the bot grinds local fodder instead. *A wrong
> **YES** from `region_reach` costs ONE walk*, which navigation then fails loudly and recoverably.

‼ **AND THE NAMED FAILURE IS INSIDE THIS FEATURE'S OWN SCOPE: ROUTE118 IS ONE OF THE SIX RUNGS.**
Shipping (A) would have re-imported the exact false negative the 2026-07-25 decision exists to
avoid, into the ladder that decision's own reasoning would have protected. ⇒ cheap-and-visible beats
invisible-and-fatal, again.

**⛔ I WROTE (A) INTO THE HANDOFF BEFORE CHECKING.** The ruling was in the docstring of the function
I was extending; I had read its signature and not its reasoning. Corrected before any code was
written. ⇒ **the rule that applies is the existing one — `grep` the decisions the code itself
records — extended: a function's docstring is part of the decisions log when it carries a ruling.**

**WHAT IS GIVEN UP, HONESTLY.** (B) admits an area on the Fly guards alone, so it can say yes to a
rung whose last mile is genuinely broken; navigation then fails loudly and
`_note_training_unreachable` blocklists it for the run. That is the same trade the 4-hop walking
budget already makes, and the measured last miles say the risk is small: 3 of 6 walkable on foot,
2 are declared-`surf` spots the party can swim to, 1 is the known door-warp case.

**⛔ AND THE TWO PIECES SHIP IN ONE COMMIT.** A Fly-aware yes without the Fly traversal means the
bot ADMITS a 15-hop area and then WALKS at it, on a `train_team` with no frame cap. Gate #68 keeps
the disjunct honest; the traversal's `heal_center=None` default keeps every old caller unchanged.


## 2026-09-23 — ⭐⭐ USER RULING 12: TRAIN ALL SIX ON THE FLY LADDER. THE PARTY IS NOT REDUCED.

**THE QUESTION, PUT WITH NUMBERS AS `06-DECISIONS-LOG.md` 2026-09-18 INSTRUCTED.** That entry
raised two readings of the L65-75 ruling, marked one **"⛔ DO NOT SILENTLY PICK (b)"**, and told a
future agent to *"price both readings, and put the choice back to the user with numbers attached."*
It was never ruled. It is now.

**THE NUMBERS PUT TO THE USER** (all re-verified at source before asking, not quoted from an agent):
* On `post_ch24_atdoor_L75.ss1`, **4 of 6 are already L75**; the exceptions are **Zigzagoon L19
  (≈20.4 h)** and **Castform L36 (≈17.1 h)**, ≈**37.5 h** summed.
* Both are **navigationally free to remove** — Zigzagoon's `Rock Smash` and `Surf` are each also
  held by Sceptile/Wailord, and Castform carries **no field move at all**.
* Boxing them would satisfy the ruling **immediately, with zero grinding** (four mōn, all L75).

**⭐ THE RULING: (a) — TRAIN THEM, ON THE NEW PER-TRAINEE FLY LADDER.** The party stays at six.

**⇒ WHAT THIS SETTLES, AND WHAT IT DOES NOT.**
* ✅ SETTLED: the party is **not** reduced for §Ch24. Do not box Zigzagoon or Castform to make the
  level floor easier. Do not re-raise this.
* ⛔ **NOT SETTLED, AND IT IS A PRECONDITION OF THE LEG:** whether training all six is *achievable*
  under the swap-trainer. See the measurement gate below. The ruling says which outcome the user
  WANTS; it cannot make an impossible one possible, and the honest thing is to say so now rather
  than discover it in a 37-hour grind.

**⛔⛔ THE MEASUREMENT THAT MUST HAPPEN BEFORE THE LEG IS WRITTEN (`#24-swaptrigger2`).**
The ladder's whole escape from the L89-L94 overshoot is that a level-matched trainee never triggers
the swap, so it solos for full xp. ‼ **`max_wild_max` kills only TRIGGER 1.**
`SwapTrainBattleStrategy.decide_turn` fires on `(underleveled or cant_continue)`, and
**`cant_continue` = HP below `battle.hp_threshold` **OR** no usable move** — neither of which the
out-level rule touches. When it fires, `_capable_finisher` picks the **strongest** healthy mōn that
out-levels the foe, and at a level-matched ground the foe is LOW-level, so **almost any L75
qualifies** ⇒ an equal exp share leaks exactly as before.
* ✅ **The HP half looks survivable, by reading:** `hp_threshold` defaults to **20 %**
  (`modules/config/schemas_v1.py`), and a trainee that OUT-levels its wilds should rarely fall that
  far in a short wild battle. **Reading, not measurement — do not build on it.**
* ⚠ **The PP half is the real exposure.** `not any(util.move_is_usable(move))` fires on PP
  exhaustion, which is *certain* over a long grind and then fires on **every** battle until healed.
  ‼ This tree already has a fixture named `grind_stall_ppzero.ss1`, i.e. the state is known to occur.
  ⇒ the leg's heal cadence is not a comfort feature; it is **what bounds trigger 2**.
* ⇒ **MEASURE: the trigger-2 firing rate at a level-matched ground, split HP-driven vs PP-driven.**
  If it is rare and PP-bounded by healing, ruling 12 is achievable as stated. If it is common, the
  L65-75 ceiling cannot be met by training and the choice returns to the user — with real numbers
  instead of an estimate.

## 2026-09-23 — USER RULING 13: IF A MŌN IS EVER REMOVED, IT IS A PC DEPOSIT — AND THE ROUND TRIP IS PROVEN FIRST

**THE RULING:** removal, if it ever happens, uses the **Poké Center PC** — the organic, human
method, consistent with the 2026-09-23 directive about wiring up PC mechanics. ⛔ **And it is proven
before it is relied on:** a full **named-PID round trip** (deposit AND withdraw a specific PID) must
be demonstrated in a drive first.

**WHY THE PROOF IS NOT OPTIONAL.** `#24-pcoverflow` records that the **withdraw half has never
worked** — a `getattr(..., lambda: [])` fallback made `box_views()` raise on every call, so
`find_in_box` could never find anything and withdrawing *"logged 0 in every batch"*. A deposit that
cannot be undone is not a deposit, it is a discard.

**SCOPE:** this is a **contingency**, not a plan. Ruling 12 keeps all six, so nothing is boxed for
§Ch24. This ruling exists so that IF the measurement above forces the question back open, the method
is already decided and its precondition is already named. It also gives `#25-partyroster` its
method: the PC round trip is step 1 there too.


## 2026-09-24 — ⭐ USER RULING: THE ORDER IS ELITE FOUR → POKÉDEX → ORGANIC PLAY

User, verbatim in substance: *"I want to ensure the bot is able to complete the elite 4 and complete
the pokedex first before we fine tune the organic aspects of the bot."*

### WHAT THIS DECIDES
1. **§Ch24 (the Elite Four) is the live priority.** Everything else queues behind it.
2. ⭐ **POKÉDEX COMPLETION IS A MAIN-LINE GOAL, NOT AN ORGANIC NICETY.** This is a promotion:
   `#24-dexhunt` was previously bundled under "organic play" polish. It is now **objective #2**, and
   `#24-catchcap` (the party-size cap that blocks catching at starter + 3) sits on its critical path.
3. **`#25-organicplay` is DEFERRED, not rejected** — explicitly *"we will discuss soon"*. Its two
   open DECISIONS still block a build and must be settled in that discussion, not assumed:
   the L65-75 / no-bench ruling vs a growing roster, and the PC round-trip evidence gate.

### ⇒ CONSEQUENCE FOR SEQUENCING
The §Ch24 entry leg and gauntlet come first. Then dex completion, which needs `#24-catchcap`'s
one-line cause fixed (`_catch_team_target = 4` is a PARTY-SIZE target including the starter) and
`#24-dexhunt`'s fence proven in motion (its A/B has never been run). ⛔ Do NOT start organic-play
work ahead of those; the user asked for a discussion first and two of its five pieces are decisions.


## 2026-09-24 — ⭐ DESIGN RULING: §Ch24 LEG 1 STOPS **AT** THE LEAGUE DOOR; THE COMMITMENT BELONGS TO THE GAUNTLET LEG

**The choice.** `prepare_and_open_the_league()` gets the party ready, walks into the lobby, talks the
guards aside, asserts they vacated — and **stops on `(9,3)` facing an open door.** It does **not**
step onto `(9,1)`.

**THE ALTERNATIVE THAT WAS REJECTED, AND WHY.** The first design stepped through. A 4-agent review
killed it, and the reasoning is the record worth keeping:
* `(9,1)`/`(10,1)` are `MB_NON_ANIMATED_DOOR` and **step-on** — arriving IS the warp, and it is the
  point of no return (every backward warp in the interior is `MB_NORMAL`, which all three warp paths
  reject — measured, `evidence/2026-09-24-league-return-warps.stdout.txt`).
* On success the bot would stand in `HALL5`, whose **only firing warp is FORWARD** into Sidney's room.
* ⛔⛔ And `story_mode.py`'s next executable statement sets `_reached_end_of_content = True` and hands
  to manual ⇒ **`StoryEndlessResetMode` would score an in-gauntlet strand as a GENUINE COMPLETION**,
  poisoning every overnight batch, with `HALL5` written into `current_state.ss1` — which the real bot
  resumes from.
⇒ **a leg must not cross a one-way threshold when nothing is built on the other side.**

**CONSEQUENCES, ACCEPTED DELIBERATELY.**
* The leg ends somewhere **safe**: the lobby has a free nurse and a measured 14-waypoint exit.
* ⛔ It is **NOT wired into `_play`**. Wiring is a separate commit that must land **together with**
  the gauntlet leg and a retargeted END-OF-CONTENT banner.
* The gauntlet leg inherits the commitment step **and** the problem that comes with it:
  `ENTERED_ELITE_FOUR` is **permanent and never cleared**, so after a loss a free nurse heal would
  re-pass any health-based readiness gate forever while levels never change. **Re-entry must be
  gated on something material, not on health.**


## 2026-09-24 — ⭐ USER GOAL: **THE TEAM LINEUP SHOULD VARY BETWEEN RUNS** (organic play)

User, verbatim in substance: *"the teams should be somewhat unique for every run… at least that's
the end goal (as far as team lineup) so it adds more organic gameplay."*

**Recorded as a GOAL, not yet a work item.** It belongs with `#25-organicplay`, which the user has
deferred until the Elite Four and the Pokédex are done (ordering ruling, same date).

### ⛔⛔ THE TENSION THIS CREATES, STATED NOW SO §Ch24 DOES NOT BAKE IN THE OPPOSITE

§Ch24's preparation is **species-bound**, deliberately and expensively:
* **Wailord + Ice Beam is the designated DRAKE counter** — Flygon has **Levitate**, so Ice is the
  only super-effective type reachable on it. Two work items were spent obtaining and teaching it
  (`#24-icebeamtrip`, `#24-icebeamteach`), plus a ~700,000-frame Abandoned Ship trip.
* **Mightyena + Crunch is the PHOEBE answer**, and `post_training.ss1`'s row records the binding
  constraint: **Emerald has NO Dark TM**, so a Mightyena that reached L47 without the level-up learn
  **could never** answer her Ghosts.
* The whole `LEAGUE_BASKET` economy is priced against *this* party's HP bands.

⇒ **A run whose team differs may simply LACK THE COVERAGE THE ELITE FOUR REQUIRES**, and no amount
of training fixes a type hole. ‼ This is not an argument against the goal — it is the thing the goal
has to solve, and it is cheaper to know now than to discover it in a 21-hour grind.

### ⇒ WHAT THIS CHANGES **TODAY**, AND WHAT IT DOES NOT

* **It does NOT change the room loop.** `fight_one_room()` (S2) must be **species-agnostic** — it
  walks, engages, fights via the existing generic battle strategy, and asserts the outcome. Nothing
  in it should name a species or a move. That was already the plan and is now a requirement.
* **It DOES reshape the readiness question.** Today's implied check is *"does Wailord know Ice
  Beam?"*. Under this goal it becomes *"does THIS team have an answer to each of the five?"* — a
  **coverage** predicate over types and movesets, not an identity check.
* ⚠ **It interacts with the L65-75 / no-bench ruling** (2026-09-18) and with the PC round-trip
  evidence gate. A varying lineup implies catching, boxing and swapping — the three pieces
  `#25-organicplay` already lists as blocked on decisions.

⛔ **DO NOT START THIS AS A BUILD.** It is filed so that the gauntlet is not written in a way that
forecloses it, and so the eventual discussion begins from the type-coverage problem rather than from
"make the roster random".


## 2026-09-25 — ⭐⭐ USER RULING 12: ON LOSING THE ELITE FOUR, THE BOT **RESTOCKS AND RETRIES**

**THE QUESTION PUT TO THE USER** (asked because an adversarial review found no ruling covered it, and
`06-DECISIONS-LOG.md` was grepped first per SESSION DISCIPLINE #11 — there was none):
*"When the bot LOSES to the Elite Four, what should it do?"* Three options were offered — stop and
report; **restock then retry**; or retry immediately with whatever survived.

### ✅ THE RULING: **"Restock, then retry."**

The user chose the most human-like option, consistent with the organic-play direction
(`#25-organicplay`) — *a human who loses does not quit, and does not walk straight back in with an
empty bag; they go and re-equip.*

### WHAT THIS DECIDES, AND WHAT IT COSTS

⇒ **§Ch24 owes the tree a RESTOCK LEG OF ITS OWN**, and the re-entry predicate must carry **BAG and
MONEY conjuncts** — with **restock as the first remedy, not training**. This is exactly the
requirement the REJECTED re-entry-gate design ended with, and it is now authorised rather than
merely implied.

**Why the obvious cheap version is not available (all measured, all on file):**
* `ENTERED_ELITE_FOUR` is **permanent and never cleared**, so after a loss the guards stay vacated
  and **the door is still open**. ⇒ re-entry itself is nearly free; it is the *equipment* that is not.
* A whiteout **fully heals the party for free**. ⇒ **a health-based readiness gate would re-pass
  forever while levels never change** — the gate must be material (bag + money), not health.
* `ResetEliteFour` runs on the whiteout path too, so post-loss state is **byte-identical to never
  having tried**. ⇒ any attempt counter must be **our own run-scoped state**; the game will not
  tell us.
* The basket costs **₽54,300** against a measured post-shop wallet of **₽1,741**, and a whiteout
  **halves** what remains. ⇒ a retry that skips restocking is strictly weaker than the attempt that
  just failed, which is the case option 3 was rejected for.
* ⛔ The §Ch23 restock route was **closed as a side effect of a correct latch fix**
  (`train_for_league` now latches on its self-skip path). ⇒ §Ch24 cannot borrow it; it must own one.

### ⛔ THE UNMEASURED PREREQUISITE — SETTLE THIS BEFORE DESIGNING THE LEG

**The League Mart is not reachable as things stand.** `probe_league_lobby_facts.py` measured, from
`post_league_lobby.ss1`: nurse **0 wp**, south exit **14 wp**, and the **Mart REFUSES**
(`PathFindingError`) — build-spec hazard **H7**. The clerk appears not to be spawned in that
fixture. ⇒ **the first work item is a probe, not a leg**: establish where the bot can actually buy
from, from a position it can actually reach, before any restock code is written.
‼ And note the money question is separate and unanswered: **where does ₽54,300 come from?** Trainer
battles pay (Sidney alone paid ₽4,900) while wilds were measured flat at **₽0 over 1,056 grind
battles** — so a restock economy that assumes grinding for money is already refuted.

### ⛔ DO NOT RE-RAISE THIS QUESTION

The loss path is **decided**: restock, then retry. What remains open is the *implementation* and its
prerequisite measurement — not the policy. ‼ A future session finding no restock leg should read
this entry as "authorised and unbuilt", **never** as "undecided".
*(Composes with USER RULING 6 — losses are acceptable, money is a high priority — which pointed this
way but did not decide it; and with RULING 11, which defines §Ch24 DONE as the Hall of Fame from a
real story run at ×1.)*


## 2026-09-25 — ⭐ USER DIRECTION: THE HM-LEARNER SEARCH MUST USE THE **PC** AND THE **WHOLE MAP**

User, verbatim in substance: *"making the bot smarter when it needs a pokemon for hm moves —
currently it just looks for what it already has and if there is nothing that it has in the party
that can be taught the move, it breaks. I want the bot to be able to freely use pokemon in the
pokemon PC (ties in to the catch gate we are reviewing) as well as catch new pokemon (not
duplicates unless shiny) that it can use to teach it the hm move it needs. This would require
possibly wiring in the locations of all pokemon, hardening map traversal (also knowledge of what is
traversable depending on what part of the story its at/chapter its on) as well as knowing how to use
the pokemon pc (withdraw/deposit) and knowing where all the pokemon pcs are that it can use."*

### ✅ THE DIAGNOSIS IS CORRECT, AND THE BREAK IS EXACTLY WHERE THEY SAY
`ensure_hm_learner(item)` (`modules/story/early_game.py:4869`) ALREADY catches a compatible wild
when the party has none. It is crippled in two specific places:
1. **`_hm_hunting_grounds(item)` searches only hand-curated grass** (`training_areas.TRAINING_GRASS`)
   and RAISES *"no swept training grass hosts a learner species — extend
   `training_areas.TRAINING_GRASS` first"* when that curated subset misses. ⇒ **this is the
   observed break.**
2. **`hm_learner_slot(item)` looks at the PARTY ONLY.** A usable carrier sitting in a BOX is
   invisible, so the bot will catch (or derail) rather than withdraw one it already owns.
`ensure_hm_learner_making_room` deposits ONE dead-weight and retries, but only on the *party-full*
failure — deliberately, and that restraint is correct and should be kept.

### ⭐⭐ THE ARCHITECTURAL RULING THIS IMPLIES: **ONE HUNTER, TWO PREDICATES**
The HM hunter and the Pokédex hunter are the SAME MACHINE:
*find a species satisfying predicate P → locate it in `encounter_index` → route with
`navigate_to_anywhere()` → catch it.*
  * `P = "can learn <HM move>"` → HM coverage (this directive)
  * `P = "not yet owned"`        → dex completion (`#24-dexhunt`)
⇒ **DO NOT BUILD TWO.** Build the hunter once, parameterised by the predicate and by a
reachability filter, or the two will drift apart and the second will be built from memory.

### WHAT ALREADY EXISTS (⛔ do not rebuild — audited 2026-09-25)
* `modules/encounter_index.py` — inverts EVERY map's ROM wild tables into
  `species -> [{map, method, rate%, level range}]`, cached per-ROM. **The "locations of all
  pokemon" the user asks for already exists; it is simply not wired into the HM search.**
* `modules/modes/util/global_navigation.py::navigate_to_anywhere()` — CROSS-MAP routing through a
  warp graph, re-planned leg by leg. **"Hardening map traversal" starts from a real implementation.**
* `modules/living_dex.py` — already derives "every species with a wild encounter that I do not own",
  and reports the rest as `skipped`.
* `modules/story/pc_trip.py` — `deposit_one_dead_weight()` (built), `box_views()` (built, fixed
  2026-08-06), `find_in_box(pids)` (built).

### ⛔⛔ WHAT IS MISSING, AND THE ONE THAT IS A LANDMINE
1. ✅ **PC WITHDRAW IS LARGELY PROVEN — CORRECTED 2026-09-25, SAME DAY.** An audit agent reported
   it as BROKEN and "never fired in a batch", I wrote that down, and then I checked: **it is wrong.**
   `grep -rhaoE "verdict landed=(True|False) code=[a-z_]+" evidence/` returns **3 ×
   `landed=True code=landed`**; the only 2 failures come from
   `evidence/2026-08-17-withdrawverdict-ARMA-faulted.stdout.txt`, a DELIBERATE fault arm.
   `evidence/2026-08-17-PROMOTION-AFTER-custom-all5.stdout.txt` records a real landing via
   `--driver boxcounter2`: *"usable this fight — Slugma :: verdict landed=True code=landed"* and
   *"Story: PC — Slugma is in the party; party is now 6."*, `ACCEPTANCE: PASS` — **verified on both
   halves (in the party AND gone from the box).**
   ⛔ Nor is "returns without acting when the box is empty" a break: that is the documented
   `(False, "not_in_box", detail)` verdict, and the docstring says *"NOT a failure: most heals have
   nothing to collect."*
   ⇒ **THE HONEST RESIDUAL** is narrow: that evidence is `--build custom` and dated 2026-08-17, so
   a fresh named-PID round trip on the CURRENT sandbox build is worth one drive to prove no
   regression — but withdrawing a boxed carrier is **not** unproven capability, and must not be
   planned for as though it were.
2. **REACHABILITY-AT-STORY-POINT** — the user named it explicitly. `_hm_hunting_grounds` already
   prefers a REACHABLE ground and records a real case (after Norman the pick was Route 117, across
   Rusturf Tunnel from Petalburg). Widening to `encounter_index` makes this filter LOAD-BEARING
   rather than a nicety: the index knows where a species lives, not whether the bot may go there yet.
3. **WHERE THE POKÉ CENTRES / PCs ARE** — needed for a withdraw trip, as the user says.
4. **"not duplicates unless shiny"** — matches `decide_dex_catch`'s existing refusals
   (already-owned / already-in-party, shiny handled separately). ⇒ policy already agrees; it is the
   SEARCH that is narrow, not the gate.

### ‼ AND IT BEARS DIRECTLY ON AN OPEN, BLOCKING DECISION — FLAGGED, NOT ASSUMED
The standing ruling (2026-09-18, reaffirmed 09-23) is **"every team member L65-75, none benched"**.
This directive asks the bot to **freely swap mon in and out of the PC** and to catch HM carriers —
which is benching, and which grows the roster. `#25-organicplay` already records this collision as
*"a decision, not code"* and as the thing that BLOCKS the rest.
⇒ The new directive is strong evidence the user wants the roster/bench reading, **but it was given
in the HM context specifically and has NOT been put to them as a reconciliation.** ⛔ Do not silently
treat it as repealing the L65-75 ruling — ask, then record the answer here.


## 2026-09-25 — ⭐⭐ USER RULING 13: **THE BATTLE TEAM IS L65-75; THE ROSTER IS FREE**

**Asked because it BLOCKED the rest.** `#25-organicplay` recorded the collision as *"a decision, not
code"*: the standing ruling of 2026-09-18 (reaffirmed 09-23) said **every team member L65-75, none
benched**, while Pokédex completion and the 2026-09-25 HM directive both require a GROWING roster
with mon parked in the PC.

### THE RULING
**The six mon the bot FIGHTS with stay L65-75. Everything else — HM carriers, dex catches, spares —
lives in the PC at whatever level, and is swapped in as needed.**

### ✅ WHAT THIS REPEALS
The "none benched" clause, and the reading that "every team member" meant *every owned mon*. Boxing
a mon is now NORMAL behaviour, not a failure, and catching beyond six is expected.

### ⛔ WHAT THIS DOES **NOT** REPEAL — AND WHY THE ORIGINAL RULING EXISTED
The **battle team** level floor is untouched. The reason for the original ruling stands: §Ch24 is a
ONE-WAY, NURSE-LESS five-fight gauntlet, and arriving under-levelled is unrecoverable. ⇒
`CH24_LEVEL_FLOOR = 65` and `train_for_league`'s readiness bar are **unchanged**, and
`prepare_and_open_the_league` still decides readiness OUTSIDE the League.
‼ A future reader must not cite this ruling to lower the gauntlet's entry bar. It moves the
BOUNDARY of "team", not the FLOOR.

### ⇒ WHAT IT UNBLOCKS, IMMEDIATELY
1. `#24-catchcap` — raising `_catch_team_target` and allowing box overflow is no longer in tension
   with a standing ruling. (⚠ Still subject to the MEASURED runway reservation: the post-gym-1
   fence holds dex catches below a full party to preserve HM/counter slots, and disturbing it
   collapsed the finish rate 52.0% → 15.8%. **The ruling permits a bigger roster; it does not
   licence ignoring that measurement.**)
2. The 2026-09-25 HM directive — withdrawing a boxed carrier is now the PREFERRED fix, ahead of
   catching a new one.
3. `#24-dexhunt` — a completion-focused post-Elite-Four mode may grow the roster freely.

### ⛔ AND IT PUTS ONE THING ON THE CRITICAL PATH
**A fresh PC round-trip drive — but SMALLER than I first recorded.** ✅ CORRECTED same day:
withdraw is NOT unproven. `--driver boxcounter2` already landed a named mon box→party with
`ACCEPTANCE: PASS`, verified on both halves (3 × `landed=True code=landed` across `evidence/`).
⇒ what remains is a **regression check on the CURRENT sandbox build** (that evidence is
`--build custom`, 2026-08-17), not a first proof. The user's *"prove it first"* ruling is
substantially satisfied; one drive re-confirms it.

## 2026-09-25 (later still) — prove the PC-first HM block LOAD-BEARING from PRODUCTION, not from the driver

**Decision:** the `skipfix` fault arm reads its env flag **inside production code**
(`_hm_pcfirst_disarmed`, `modules/story/early_game.py`), and the PC-first block's condition consults
it. The driver does not skip its own call.

**Why.** A driver-side switch proves only that *the driver can skip its own call* — it says nothing
about what production does. The claim being made is *"without this block, the bot fails to use a
carrier it already owns"*, and this project's standing rule is that such a claim is only payable in
**an arm with X removed**.

**Rejected alternative — rely on the `nobox` arm alone.** It proves the guard's CONDITION is false
on an empty box, which is a *different and weaker* statement: it leaves open that the carrier in the
default run arrived via the pre-existing counter-hunt withdraw. ⭐ The decisive property is that the
READER (`boxed_hm_learner_pids`) is untouched by the disarm while the CONSUMER is disarmed — so
under `skipfix` the `H-BOXFOUND` reading **still takes**, and the grade then requires that a
*provably findable* carrier was *still* not withdrawn.

**Rejected alternative — a git-stash A/B against the pre-fix code.** It would prove the same thing
once and be unrepeatable, and it cannot be run by a gate or by a future agent. An env arm is
permanent, cheap and self-documenting.

**Cost accepted:** one conditional in a production hot-ish path, and a registry entry.

---

## 2026-09-25 (later still) — test the HM path with WATERFALL, never SURF

**Decision:** `--driver hmpcfirst` uses **HM07 (Waterfall)** on `fortree_gym_wedge.ss1`.

**Why.** The anchor's value is that **no** party member can learn the HM, making the PC-first branch
the only route to success — a REAL precondition instead of a fault hook. Surf, the obvious choice,
**breaks that**: Zigzagoon L3 learns Surf, so `hm_learner_slot` returns a party slot, the block is
never reached, and the run still prints `PASS`. ⇒ the test would have been **vacuous and green**,
the worst combination.

**Consequences recorded where they will be read:** the `FIXTURES.md5` entry states that the anchor's
worth is a property of its PARTY and forbids re-capturing it with a Water-type; the driver asserts
the premise at runtime and refuses to run if it does not hold.


## 2026-09-26 — ENDLESS-RESET CAP: RAISE THE BASE TO 7M, AND EXTEND IT ONLY ONCE §Ch24 OWNS THE RUN (`#26-endlesscap`)

**DECISION.** `StoryEndlessResetMode.MAX_FRAMES_PER_RUN` 5M → 7M, and `_frame_cap_for_this_run()`
adds `CH24_TRAIN_PURSE_FRAMES` + a 1M gauntlet allowance once `_ch24_owns_run` is latched.
**WHY.** In this mode every run starts from a NEW GAME, the §Ch24 grind alone is ~4.5M frames, and
the 2026-09-15 corpus shows 5M being reached mid-to-late game ⇒ a Hall of Fame was impossible in
the batch mode and any run reaching the League would have been killed mid-grind. Full evidence:
`07-CHANGELOG.md` 2026-09-26.
**ALTERNATIVES REJECTED.**
* **Keep 5M** — the user's 12-hour batch could then never observe a League run; it would measure
  only up to the kill point.
* **A flat ~14M cap** — loosens protection against the early-game LIVELOCKS that cost half a batch
  in July (19.9M-frame Route 103, 13.4M Route 116); a livelock would burn 2.8× the old budget
  before reset. The latch-keyed extension keeps early game at the base cap.
* **An env-var knob** — adds a flag to the registry and makes the batch's key variable invisible in
  its own logs unless separately printed; the cap is a property of the mode, not of an experiment.
* **Extend by badge count / chapter** — more states to get wrong. The §Ch24 latch already exists and
  marks exactly the moment the training PURSE (the designed wedge backstop) takes over.
**REOPEN IF:** a completed run exists (re-derive the base from its length, per the constant's own
rule), or a batch shows runs killed at 7M while still progressing.

## 2026-09-26 — USER RULING: THE UPSTREAM SYNC STAYS PARKED ("Not now, keep it parked")

Asked (with the facts: now **3** commits ahead at `f0a14cad`, including upstream #826 *"Reduce usage
of global state"* — a **28-file** refactor, no longer the 1-file Tk change; step 2 is a
`git subtree pull --squash` merge onto `main`; the mirror folder only, never `custom-pokebot/`).
Answer: **"Not now, keep it parked."**
⇒ Keep performing the daily CHECK and recording it in `40cakes repo/UPDATE-LOG.md`. **Do not run
step 2 without asking again.** ⚠ This is a "not now", not a "never": re-offer it at a quiet moment,
and do not treat this entry as a standing refusal.

## 2026-09-26 — HOLD THE USER'S OFFERED 12-HOUR x4 BATCH UNTIL THE TWO §Ch23 KILLERS ARE FIXED (`#26-batch0926`)

**DECISION.** The user offered to run a 12-hour ENDLESS LOOP x4 batch as the next step toward RULING 11.
I recommended HOLDING it (the user had asked *"if you think this is a good idea"*), shipped the cap fix it
would need anyway (`#26-endlesscap`), and queued the two §Ch23 fixes first.
**WHY.** A 5-angle recon with an adversarial verifier per angle
(`ai-research-notes/2026-09-26-organic-frontier-RECON.md`) found that **all 39 badge-8 runs** of the
previous 99-run corpus died INSIDE §Ch23 on two causes that are **unfixed at HEAD** — 30 on the training
refusal (`#24-ch23training`), 9 on a Route 128 staging tile occupied by a trainer (`#26-carleestage`).
CLAUDE.md rule 9: batches answer FREQUENCY questions, and a frequency already measured at 30/30 on an
unchanged mechanism is not a question. 12 hours of four lanes would re-measure it and could not see past it.
**ALTERNATIVES REJECTED.**
* **Run it now anyway** — the only new information would be early/mid-game frequencies on a build with few
  changes to those paths; and it would freeze `sandbox-pokebot/` for 12 hours (lanes import late-chapter
  modules from disk), blocking the very fixes it would be waiting on.
* **Run it from a frozen git worktree** so development continues — the recipe does not work as written
  (the `mgba/` bindings and `.last-requirements-check` are gitignored; `.git` is a FILE in a worktree, so
  every run header loses its build commit). Possible later, not free.
**REOPEN WHEN:** both §Ch23 fixes ship ⇒ signal the user that the batch is ready, on a build that can
see past Victory Road.


## 2026-09-26 — THE ENDLESS ANALYZER KEYS END-GAME MILESTONES ON NAME ∧ (GROUP, NUMBER) ∧ ≥2 SIGHTINGS, AND READS `debug-logs/` + `Old/`

**DECISION.** End-game milestones (`ever_grande (0,8)`, `victory_road (24,43-45)`, `league_lobby`, `elite_four`,
`champion`, `hall_of_fame`) require the map-section NAME **and** the id **and** `MIN_ID_SIGHTINGS = 2`; towns
stay name-only. The analyzer reads a lane's `debug-logs/*.log` and `debug-logs/Old/*.log`, deduplicated by
file name (a run's log is in one place or the other; `Old/` wins a collision).
**WHY.** Name alone cannot see the League (every room is `EVER GRANDE CITY`); id alone false-fires on
mid-warp mis-reads (`ROUTE 102(16,0)` is in the 2026-09-15 corpus — the logger reads name and id from two
memory sources); name ∧ id on ONE frame can still transiently mis-pair, and a genuine visit is always logged
more than once. Reading both folders means a PARKED batch whose last run has not rotated into `Old/` is still
counted.
**ALTERNATIVES REJECTED.** Id alone (false positives, measured); a per-map name table (the logger cannot print
room names — the section IS the name); ≥3 sightings (would risk missing the Hall of Fame's short credits
window for no measured gain). **REOPEN IF** a real League visit is ever logged fewer than twice.


## 2026-09-26 — ⭐ USER RULING 14: LOW-LEVEL HM CARRIERS MAY BE SWAP-TRAINED ON VICTORY ROAD 1F INSIDE §Ch23, IN BOUNDED CHUNKS

**THE QUESTION, AS ASKED (with the data):** the §Ch23 refusal ends 30 of 39 badge-8 organic runs because a
low-level HM carrier (usually Marill L13) cannot reach L47 inside one 250k call. Measured the same day
(`ai-research-notes/2026-09-26-ch23-swapprobe-GRADED.md`): with production swap-training the Marill leads,
switches out on turn 1, never takes a hit and went L13→17 in 5 battles; without swapping it fainted 56 times
and gained nothing. Given the 2026-09-19 ruling (*"a level appropriate area … so it can actually fight or be
swap trained"*), is it OK to swap-train such carriers on Victory Road 1F (L36-40) before the Elite Four, in
bounded chunks? **ANSWER: "Yes, swap-train there."**
⇒ **Build CHUNKED training** (`ai-research-notes/2026-09-26-ch23training-DESIGN.md`, Design 1 + the judges'
grafts). ✅ This SETTLES the tension with the 2026-09-19 ruling for §Ch23 — its "or be swap trained" clause
covers it. It does NOT change §Ch24's per-trainee Fly ladder (still the L65 mechanism), nor RULING 2 (1F,
never B1F), nor RULING 5 (the L65 grind stays after Victory Road).
**THE MONEY HAZARD (2026-09-18 REVERSAL) — DECIDED HERE, NOT ASKED:** the grind runs before leg 11's
₽54,300 basket (₽1,741 slack) and a whiteout halves money. ⇒ the chunk loop checks money against the basket
BEFORE the first chunk and AFTER every chunk, and raises LOUDLY on a shortfall rather than walking into the
League under-supplied. No re-earning (the MONEY ruling forbids re-raising it). **Why acceptable:** in
swap-training the strong finisher does the fighting (0 whiteouts in the probe), and the loud stop turns the
residual risk into a visible, diagnosable outcome.


## 2026-09-26 — ⛔ CORRECTION TO RULING 14's MONEY CLAUSE (same day, caught BEFORE any code used it)

The RULING 14 entry above says the chunk loop *"checks money against the basket BEFORE the first chunk and
AFTER every chunk, and raises LOUDLY on a shortfall"*. ⛔ **That clause would have refused EVERY organic run:**
`victory_road.py` records the pre-Victory-Road wallet at ~₽38,893 — already BELOW the ₽54,300 basket — and the
₽56,041 measured at leg 11 includes ~₽17k of Victory Road trainer payouts earned AFTER training. An absolute
check here tests the wrong moment.
**THE DECISION THAT SHIPS:** training never SPENDS money (Poké Center heals are free), so a drop can only be a
whiteout. The chunk loop records money before and after every chunk and, on a DROP, records
`train_money_dropped` and says so on `context.message`; **leg 11's existing sell-or-refuse guard stays the single
money GATE** (it already refuses loudly, with a sell plan, when the basket is unaffordable). The user's approval
(swap-train on VR1F in bounded chunks) is unaffected. ‼ The rule this teaches: *a threshold is a claim about a
MOMENT — check the quantity where it is spent, not where it happens to be convenient to read.*

## 2026-09-26 — §Ch23's CHUNKED TRAINING GRANTS ITS PURSE TO THE BATCH RUN CAP (`_ch23_training_allowance`)

**DECISION.** When `train_for_victory_road` starts training, it calls `grant_ch23_training_allowance(
CH23_TRAIN_PURSE_FRAMES)` on the mode; `StoryEndlessResetMode._frame_cap_for_this_run` adds it (reset per run,
idempotent on retry, composes with the §Ch24 extension; gated in `repro_endless_frame_budget.py`).
**WHY.** The 2026-09-15 corpus reaches §Ch23 at a median 3.93M frames; a chunked climb can take several
million more (the judges modelled ~14/30 runs overrunning the 7M base once legs 5-11 are counted). Under the
flat cap those runs would read as "wedged" mid-training — a false refusal of exactly the fix under test. Same
rule as the §Ch24 extension earlier today: a run cap must not pre-empt a leg's own designed backstop.
**ALTERNATIVES REJECTED.** Raising the base cap again (loosens early-game livelock protection for every run);
leaving it (turns the batch that measures this fix into a measurement of the cap). **REOPEN IF** a batch shows
§Ch23 training runs killed by the cap while still banking EXP.

## 2026-09-26 — `#26-ch24organic` R1 REFUSES AT THE PRODUCTION FLOOR (USER RULING 12 APPLIED LITERALLY) — ⚠ RELAXATION IS THE USER'S CALL, FLAGGED

**DECISION.** R1 (`prepare_and_open_the_league`) refuses to enter the Elite Four unless EVERY party member is at
`CH24_LEVEL_FLOOR` (65) and the full `LEAGUE_BASKET` is in the bag. Grepped first (rule 11): RULING 12 (2026-09-23)
sets the L65-75 target for all six and says the party is not reduced; RULING 12-b (2026-09-25) says a LOSS is
answered by restock-and-retry. **No ruling says whether an under-levelled party should enter anyway.**
**WHY STRICT, FOR NOW:** it is the literal reading of the only ruling on levels; it is cheap to relax (one predicate,
`ch24_readiness_shortfall`); a refusal is named, bounded and strands nothing (arm E), while a loss today ends the
run too (the restock leg `#24-restockleg` is unbuilt), so strict costs nothing that entering would have saved —
EXCEPT the chance that an under-levelled party wins.
**⚠ THE FACT THAT MAKES THIS THE USER'S CALL:** the only party ever to WIN the gauntlet (`post_ch24_atdoor_L75`,
`evidence/2026-09-25-ch24gauntlet-PASS.txt`, driven at `CH24_ENTRY_FLOOR=1`) was **4×L75 + Zigzagoon L19 + Castform
L36** — R1 at L65 would refuse it if training could not lift the two stragglers. Put to the user in the session
report; record the answer here.
**REJECTED:** (a) a "top four ≥ L65" rule — invented from ONE winning trajectory (rule 8); (b) basket-only (enter at
any level) — contradicts RULING 12's target without a ruling.

## 2026-09-26 — `#26-ch24organic` IS BUILT ON A WORKTREE BRANCH WHILE THE USER'S BATCH RUNS

**DECISION.** Code for `#26-ch24organic` is developed on branch `wt/ch24organic` (git worktree
`C:/Remote Projects/pokebot-wt-ch24`) and merged to `main` only after `#26-batch0926` is parked.
**WHY:** endless lanes import late-chapter modules (`pokemon_league.py`) from `main`'s `sandbox-pokebot/` the first
time a run reaches them, so a mid-batch edit would put two builds in one batch. **Doc edits** to the current-state
files (03/04) are made on `main` (docs are never imported by a lane) and merged into the branch; append-only logs
(06/07/08) are `merge=union` in `.gitattributes`, so both sides may append.
**REJECTED:** pausing development for 12 hours; editing `main`'s sandbox anyway.


## 2026-09-26 — THE RETURN BRIDGE RUNS AFTER R1, AND ONLY ONCE (`#26-ch24organic` gap 2)

**DECISION.** `return_to_league_door` is called once in `prepare_and_open_the_league`, AFTER the R1 readiness
refusal and BEFORE GET INSIDE. **WHY:** readiness (levels, basket) does not depend on position, so an unready
party is refused for READINESS wherever it stands, and only a ready party pays for the trip home — which also
kept all five proven R1 arms valid unchanged.
**REJECTED:** (a) the recon's order train → bridge → R1 (it would have made F1-shaped parties refuse on
"no Fly" before their real problem, readiness, was named); (b) a second bridge BEFORE the leg's own training
retry, so a party could re-train from (18,6) — the retry rarely helps (a `no_ground` stays `no_ground`) and the
`_play` derail re-entry already re-runs `train_for_league`.

## 2026-09-26 — `ensure_fly_learner` REPORTS A MISSING LEARNER, IT NEVER RAISES; THE WALK-OFF GUARD RUNS ONLY WITHOUT FLY

**DECISION 1.** A party that cannot be taught Fly (no compatible member, every candidate would lose its last usable
attack, or no HM02) continues WITHOUT Fly. **WHY:** R1 refuses an under-levelled party BY NAME and the return bridge
refuses a party stranded off the plateau BY NAME, so a raise here would add nothing but an earlier, less specific
stop. **REJECTED:** raising (it would end runs that are already at the door and need no training).
**DECISION 2.** Gap 4 is a NARROW, MEASURED return ticket — `_plateau_walkoff_refused`: no Fly + standing on the
League plateau + a `VICTORY_ROAD_*` ground ⇒ named `no_ground`. **WHY:** that is exactly the measured crash; nothing
else is touched. **REJECTED (by code review, before merge):** a general `calculate_path(here → ground)` pre-check —
`calculate_path` is WARP-BLIND, so it would refuse every warp-gated ground (Granite Cave, Fiery Path …); the KI-24
user decision (2026-07-25) already chose `region_reach` over it for training picks because its wrong NO is invisible.
## 2026-09-26 — ⭐⭐ USER RULINGS 15-18: §Ch24 READINESS AND THE LEAGUE-BASKET MONEY (asked with evidence; `06` grepped first — none was ruled)

Asked after the live batch showed 3 of 3 organic League arrivals refused on money (`#26-ch23money`,
`ai-research-notes/2026-09-26-ch23money-RECON.md`) and R1 was built strict (see the R1 entry above, "⚠ RELAXATION IS THE
USER'S CALL"). The user's answers, verbatim choices:

* **RULING 15 — R1: "Enter if 4+ are L65".** R1 refuses the Elite Four only if FEWER THAN FOUR party members are at the
  floor; stragglers ride along. (Evidence given: the only party ever to win the gauntlet was 4×L75 + L19 + L36.) The
  basket conjunct is unchanged. ⇒ supersedes the "all six at L65" reading of RULING 12 **for the gauntlet-entry gate
  only**; training still aims to lift everyone (RULING 12's training target is untouched).
* **RULING 16 — "Buy only what's missing".** §Ch23 leg 11 buys only the MISSING quantities of `LEAGUE_BASKET` so the bag
  ends with exactly the same basket by item name — explicitly NOT a thinner basket (that ruling stands).
* **RULING 17 — Amulet Coin: "Yes, fetch it after badge 5".** Mom in Littleroot (two talks, `FLAG_BADGE05_GET`); a
  battler that actually enters battles holds it (decomp: the ×2 is set only when the HOLDER switches in).
  Supersedes `#24-amuletcoin`'s "then decide whether to fetch it".
* **RULING 18 — Buy early: "Yes, buy early with a reserve lock".** Part of the basket (Hyper Potion / Full Heal /
  Revive — Mossdeep and Sootopolis sell them; Full Restore only at the League) is bought BEFORE the Juan attempts,
  locked so gym battles cannot spend it. Items survive a whiteout; money does not.
**RECOMMENDATIONS THE USER DECLINED:** "keep all-six-at-65" (R1) and "not yet — measure first" (buy early).
**BUILD ORDER (mine):** 15 and 16 first (small, gated), then 17 and 18 (story errand / purchase + lock), each
pre-registered and driven on branch `wt/ch24organic`.

## 2026-09-26 — RULING 17 IMPLEMENTATION CHOICES: SEGMENT 12d, FAIL SOFT, TOP-LEVEL HOLDER (v1)

**CHOSEN.** (1) Run the errand right after the Surf teach (Segment 12d), gated to `not BADGE06` ∧ on a Petalburg map —
the bot is 2 routes from Littleroot there, and a post-Fortree re-entry can never walk back south (KI-97's shape).
(2) FAIL SOFT for every coin problem (named reason, `AMULET_COIN` debug event); hard-guard only the END POSITION,
because Segment 13a starts in Petalburg. (3) Holder = the highest-level party member (ties → an empty held slot; never
an egg), identified by PID + species. (4) Give from the bag with a NEW sibling function, not an edit of
`use_item_on_party_member` (its USE wait is a measured-fragile line, `#24-itemcontextplural`).
**WHY.** A coin is money, not a run: a failure here must never cost a run that would have reached Fortree. The recon
replay put the top-level mon in 55 % of won battles and 47/58 bosses (vs 27 % for the badge-5 lead).
**ALTERNATIVES REJECTED.** Fetching later (after Fortree/Lilycove — a much longer detour, and Fly is not guaranteed);
a hard guard on receiving the coin (converts an optional income boost into a derail); giving it to the current lead
(sent out less often). **REOPEN IF** the batch's `[MONEY]` lines show the static holder is rarely sent out — then
"move the coin to the entrant" (recon D1) becomes its own item.

## 2026-09-26 — RULING 18 IMPLEMENTATION CHOICES: SOOTOPOLIS IN §Ch22 L1, RESERVE UNTIL THE ELITE FOUR, STATE-DERIVED

**CHOSEN.** (1) Buy at the SOOTOPOLIS Mart inside §Ch22 L1, after the Poké Center heal (the only point that guarantees
Sootopolis), re-running on every Juan attempt (only the missing lines), cheapest-to-leak first (Revive, Full Heal, then
Hyper Potion), ₽1,000 kept for Poké Balls, fail-open. (2) The reserve holds `LEAGUE_BASKET` quantities out of IN-BATTLE
use only, from the Juan-era flag until `ENTERED_ELITE_FOUR` / `IS_CHAMPION` / a sealed §Ch24 map — derived from game
state every call, never a latch. (3) SCOPE READING (mine): the ruling's text said "gym battles"; the reserve holds for
every trainer battle until the Elite Four.
**WHY.** (1) After the heal the bot is guaranteed in Sootopolis and the wallet is still whole; items survive the Juan
whiteouts that halve cash. (2) A reserve anywhere else starves leg 11, R1 and the Elite Four's healing (the adversarial
recon's top scenario); state-derived arming survives restarts, cannot leak into the next ENDLESS run, and releases for
every Elite Four battle even after a whiteout (the Elite-Four progress vars reset; the entry flag does not). (3) The
bot spent 0 items on Juan in every log, so a gym-only lock would protect nothing; today's bot carries no Hyper Potions
past Sootopolis, so the wider lock reproduces today's fights exactly.
**ALTERNATIVES REJECTED.** Mossdeep (earlier and a simpler walk, but before the Dive teach's possible ball purchase, and
it would not convert the cash left after each Juan whiteout); a veto of the policy's pick (loses the Super-Potion
fallback); an in-memory latch (lost on restart, leaks into the next run); a gym-only lock (protects nothing measured).
**REOPEN IF** the next batch shows runs short of the Full Restores at leg 11 after buying early, or Victory Road losses
that a held Hyper Potion would have prevented — then the scope or the floor is the user's call again.

## 2026-09-26 — §Ch23 LEG-5 RE-ENTRY: A PATH CHECK, NOT A y-THRESHOLD; FAIL TOWARD THE OLD GUARD

**CHOSEN.** `leg5_should_fire()` = the old guard AND `not (wally_beaten() and on_league_plateau())`, where
`on_league_plateau()` = on EVER_GRANDE_CITY and `calculate_path` to the Victory Road apron (18,42) raises
`PathFindingError`; any OTHER failure of that read returns False (leg 5 fires, as before).
**WHY.** The plateau and the south half are disconnected (measured: (18,28) cannot plan to (18,42) or to the Poké Center
(27,49)), but no layout dump proves where a y-line would fall; the path check asks the question directly. Ever Grande
has no object events (decomp), so the planner's unseen-object blocker (`KI-103`) cannot fake a "no path". `wally_beaten()`
alone is wrong: a whiteout respawns at the SOUTH Poké Center with Wally beaten, where leg 5 must fire. Failing toward the
old guard means the worst an unreadable position can do is reproduce the pre-fix behaviour.
**ALTERNATIVES REJECTED.** A y-threshold (unmeasured); `wally_beaten()` alone (wrong in the south); moving the leg-11 gate
or skipping §Ch23 on re-entry (settled NOT to be proposed by the money recon).
**REOPEN IF** a run on the plateau is seen firing leg 5 anyway (the path check then reads a path that does not exist), or
the Victory Road EXIT side's same-shaped guard is measured to misfire.
## 2026-09-26 — ⭐⭐ USER RULINGS 19-21: GYM ANSWERS FROM OWNED TMs; ORGANIC CATCHING INSTEAD OF CHAPTER FIXES; THE FLY SWAP

Asked after a 4-angle recon of the live batch's boss deaths (`ai-research-notes/2026-09-26-boss-counter-RECON.md`) and the
§Ch24 flyer gap (`#26-ch24organic` gap 5). `06` grepped first: no ruling covered teaching TMs for gyms, the Surf carrier,
or a catch policy for flyers.

* **RULING 19 — "Teach owned TM".** When the bot keeps losing to a gym leader, it may teach a TM it ALREADY OWNS (e.g.
  TM50 Overheat from Flannery, TM34 Shock Wave from Wattson) to a team member that can learn it, replacing that mon's
  weakest move. ⛔ The user did NOT select "Surf on a strong battler" or "protect answers from deposit" — do not build
  those under this ruling.
* **RULING 20 — ORGANIC CATCHING, NOT CHAPTER-SPECIFIC FIXES (the user's words, verbatim):** *"This shouldn't be an
  issue if we fix the catch logic, remove the catch 4 party 4 limit and allow the pokedex catching feature work as I
  explained (pokedex catching is always active so the bot is always catching new/shiny/rare pokemon to complete pokedex
  as well as catching a more diverse team for counters and hm teaching) so the bot has access to more pokemon (this
  would also include ensuring the pokemon pc withdraw/deposit logic works and is usable) does this make sense? We should
  not be hard coding this sort of logic for specific chapters as this is stupid, not organic and makes no sense if we can
  simply ensure the bot is allowed a full team, catching along the way as well as pc logic and access for nearby pc if
  it needs it for whatever reason"*
  ⇒ Supersedes the gap-5 options O2 (a Segment-13e flyer detour) and O3 (a Fly-only dex exemption): the flyer comes
  from ORGANIC catching. The target of the change is the dex-catch fence (`story_mode.decide_dex_catch`): the pre-gym-1
  team target of 4, and "catch only when the party is 6/6" (the HM/counter RUNWAY).
  ⚠ **THE RISK TO RE-MEASURE, NOT TO RE-LITIGATE:** `#24-partycap` measured the runway as worth ~36 points of finish rate,
  and disturbing the early party measured 52.0% → 15.8% (see the entries above). Those were measured BEFORE the PC-first
  HM withdraw and the make-room deposit were proven (2026-09-25). ⇒ build it with the PC paths as the runway's
  replacement, and A/B it on a batch before promotion.
* **RULING 21 — the Fly swap: "Yes, swap briefly".** During §Ch24 Fly training one fighter may sit in the PC while a
  Fly carrier trains; the same six fighters are restored and checked by PID before R1 (answers gap-5 decision U1).

* **CORRECTION (appended 2026-09-26, same day):** the RULING 20 entry above says the make-room deposit was proven
  2026-09-25. It was driven and wired 2026-08-13 (`KI-63`), with the ping-pong fix 2026-09-07; only the PC-FIRST HM
  withdraw is from 2026-09-25. The risk statement is unchanged: `#24-partycap` was measured before either path existed.
  Build plan: `ai-research-notes/2026-09-26-rulings19-20-PLAN.md`.

## 2026-09-26 — THE DEX-CATCH BAIL: STOP AT THE RESERVE; WHEN TRAPPED, THROW; TRAPPED AND EMPTY, FIGHT

**CHOSEN.** A post-gym-1 Pokédex catch flees (by the best escape method) at spare balls ≤ 10 or after any faint. When
escape is IMPOSSIBLE it keeps throwing — spending into the reserve is the lesser harm than a Run that loops until a
whiteout — and when no ball is left it fights with its strongest move. Only the dex-only subclass behaves this way.
**WHY.** The reserve exists for the MANDATORY hunts (HM learners, counters); a discretionary catch that drains it has
ended a run. A trapped battler has no legal escape in Gen 3, so the only choices are throw or fight.
**NOT CHANGED, STATED:** the plain `StoryCatchStrategy` still picks Run at 0 balls without a trap check. The shiny
strategy inherits it and its rule is a user directive (attempt until success, whiteout or out of balls), and the HM /
counter catches are mandatory — a trapped-and-empty mandatory catch still ends in a whiteout (pre-existing, rare).
**REOPEN IF** the batch shows `[DEXCATCH-BAIL]` never firing (then the wiring is wrong), or dex catches ending in
whiteouts anyway.

## 2026-09-26 — RULING 19 BUILT AS "TEACH ONLY WHERE THE TM CAN REACH AND WIN SOMETHING" (design 4)

**CHOSEN.** A gym TM is taught only when (1) the wall is named by identity from the leader's own lost battles (our
faints per foe, >= 2 losses), (2) the recipient is in the best-resisting group against the wall's types — the RULED
lead/replacement order's own defensive term, used as a predictor and not changed, (3) a Gen-3 duel estimate says it deals
at least half the wall's HP before it faints, and (4) the slot costs nothing the mon was trained on. One teach per boss
until the taught move is seen used. Taught moves are invisible to the hopeless test.
**WHY.** A TM is single-use and the user asked for teaches that help. Measured on real fixtures, the looser designs spent
the TM on a mon the ruled order fields last (Sceptile / Blaziken vs an all-Flying gym) or disabled the counter ladder
(a taught Rock Tomb reads as a credible answer to Winona's Dragon/Flying ace). The stricter design teaches less often and
says why each time (`[GYM_TM] why=`).
**REJECTED.** A KO-count wall (the decomp: replacements are the AI's pick, not party order); excluding HM carriers (it
excluded the lead); "prefer Shock Wave" as a rule (the duel estimate ranks Overheat higher on Loudred vs Skarmory, and
Shock Wave wins the tie when both reach 100%); Tate & Liza (a double battle — the turn record sees one foe).
**STATED TRADE.** Expected benefit is small (on the fixtures only the Torchic core's Loudred qualifies) and it is a
frequency question for a batch. ⚠ **THE REACH FILTER IS A HEURISTIC, KNOWINGLY CONSERVATIVE:** it predicts who is sent in
FIRST against the wall (the ruled key's defensive term), but a long fight cycles the whole party — in the real gym run
(R1) Sceptile, which it calls "never fielded" vs Skarmory, faced Skarmory as the LAST mon standing. It can only REFUSE a
teach (never misdirect one), so it errs toward "no plan"; the positive case (a best-resisting recipient taught, then SEEN
using the move vs the wall) is for the batch. **REOPEN IF** `[GYM_TM]` shows `taught` but no `[TURN] UseMove:<move> … vs <wall>` in
the same run (the reach predictor is wrong), or `deals only` refusals dominate on teams that go on to lose (MIN_SHARE).

## 2026-09-26 — RULING 20 PHASE 0: DO NOT START A POKÉDEX CATCH EXPECTED TO COST MORE THAN 10 BALLS

**CHOSEN.** The fence estimates the expected balls with Gen 3's exact integer arithmetic at FULL HP (the catch strategy
never damages, so this is an upper bound) and the best ordinary ball held, and refuses a post-gym-1 catch above 10.
**SIMPLIFICATIONS, STATED (all bias toward REFUSING, the safe side):** full HP and no status (the catch strategy may
add a status when its odds are low — x1.5/x2); every special ball (Net, Dive, Nest, Repeat, Timer, Luxury, Premier)
counted as a Poké Ball although the thrower gives Net/Dive/Repeat/Timer their conditional bonus (a Net Ball on a
Water/Bug target is x3). The ball is the best one the THROWER may use (held, not Master, in `catch_balls.yml`).
**WHY 10.** A JUDGEMENT, not a measurement: the one 30-ball Rustboro purchase then covers ~3 hard catches before the
ball reserve (10) bites; with Poké Balls it refuses catch rate ≤ 60 (Absol 23, rate-45 species 16, rate-60 12.4) and
admits rate ≥ 75 (9.4); with a Great Ball it refuses rate 45 (10.8) and admits rate 60 (8.1). Most early Hoenn wilds
are rate 120-255; the refused ones are the Sableye / Mawile / Absol / Bagon / Pelipper / Lunatone class. Every refusal logs its estimate, so a batch can
re-derive the number. **REJECTED:** a per-species blacklist (not organic, drifts), throwing until the reserve (the dex
bail already bounds that; this stops the start). **REOPEN IF** the batch's DEXFENCE lines show most post-gym-1 new
species refused on the estimate, refusals of species a human would call easy, or discretionary catches still draining
the reserve (then the threshold, the simplifications, or Phase 1's ball restock is wrong).

## 2026-09-26 — KI-104: THE HM TEACH'S SLOT PICKER IS TOTAL, AND TYPE PROTECTION IS A PREFERENCE, NEVER A REFUSAL

**CHOSEN.** `choose_hm_slot`: HMs excluded first; then status > banned > strictly dominated (same type, at least its
effective power — by a kept move OR the incoming HM) > weakest non-STAB > STAB as the last resort. Always an int 0-3 when
a non-HM slot exists. Multi-hit moves valued ×2/×3; power-1 (variable/fixed damage) moves valued 60.
**WHY.** The HM teach gates story progress, and every caller pre-selects its learner assuming any non-HM slot is
spendable — so the picker may PREFER to keep a mon's trained moves but may never REFUSE (a refusal stalls the story at a
field obstacle; None/4 crash or cancel inside the open summary screen — adversarial recon).
**REJECTED.** Reusing the level-up policy `which_move_should_be_replaced` (it DECLINES Fly, Dive, Flash and the Double
Kick case itself); counting an HM as type COVERAGE (it makes Double Kick "redundant" beside a 20-power Rock Smash — the
original bug); a hard "never delete the only move of a type" rule (Swampert with three HMs has only one spendable slot);
`gym_tm_teach.choose_slot` as is (it returns None when only STAB remains).
**STATED TRADE.** The 60 stand-in for power-1 moves is a judgment (Low Kick / Seismic Toss are real attacks at this
stage); the §Ch23 Waterfall teach now gives up Water Gun (dominated by Surf) instead of Rollout — re-driven.
**REOPEN IF** a batch shows `learned <HM> (lost <X>)` where X was a mon's only move of a type while a dominated or off-type
move was available.

## 2026-09-27 — KI-106: RELEASE LEAKED HELD INPUT AT THE STORY'S RECOVERY SEAM, not in `_sampling` or `isolate_inputs`

**Decision:** `StoryMode.run()`'s `except BotModeError` handler releases held buttons FIRST, before it branches into the
whiteout or the derail recovery, and announces the mask (`RECOVERY-HELD`). Arm: `POKEBOT_RECOVERY_FAULT_KEEPHELD`.

**Rationale:**
- It is the one place every abort-raised recovery unwinds to, and no navigator is running there. The generator that
  raised is dead, and the recovery's own walks set their buttons afresh.
- It covers every wrapper that can abandon a live navigator: `_sampling`, the watchdog and battle-fault closes, and
  `_yield_bounded*`. It does not have to find each one.
- A hand-off that never raises (`context.set_manual_mode()`) already releases on its own (`modules/context.py`).
- A/B-proven on the batch's exact path (`ai-research-notes/2026-09-27-evgpcwedge-GRADED.md`).

**Rejected:**
- (a) **A `finally: reset_held_buttons()` in `_sampling`**, as `_budgeted` has. It fixes one wrapper out of several,
  and the recovery seam alone is shown sufficient on this path. Adding it too would be an unmeasured second guard, and
  CLAUDE.md rule 8 says a guard claimed load-bearing needs its own arm.
- (b) **Skipping `isolate_inputs`' restore after a whiteout** (`_listeners.py` / `_util_helper.py`). Those files are
  upstream-shared, so it would be a DIVERGENCE with the widest blast radius. It also covers only one of the two re-hold
  routes; the navigator's own next frame is the other.
- (c) **Clearing held D-pad bits inside `ensure_facing_direction` / `follow_waypoints`.** That is also upstream-shared,
  and it sits on the per-frame path navigation depends on. `#24-truckleak` warns against exactly that.

## 2026-09-27 — RULING 20 Phase 0: the pre-gym-1 attempt cap is DEFERRED to Phase 2, and the full-HP pre-gym-1 health check is REJECTED

**Decision:**
- Build no pre-gym-1 per-species attempt cap now.
- Do not port the post-gym-1 full-HP entry check (`party_healthy`) to before gym 1.
- Both questions move to Phase 2, where the pre-gym-1 team target of 4 changes. There the cap is built and measured
  TOGETHER with the target change, under the constraints in `ai-research-notes/2026-09-27-pregym1-cap-RECON.md`.

**Rationale (measured by a four-agent recon, a NOTE):**
- **The cap.** At target 4, a cap of 2 refuses nothing: 0 of 140 attempts in the parked batch, and 3 of 3,196 (all Abra)
  in the 872-run H corpus. So an A/B of it would show no difference by construction. A cap of 1 would refuse 134
  "out of balls, then caught on retry" successes.
- **The full-HP check.** It would refuse about 79% of team-building catches, with no measured whiteout benefit (0.55%
  either way).
- **The real pre-gym-1 risk** is an in-battle loss, mostly Whismur's Uproar. Its fix is a first-faint bail, which a
  Phase 2 build should carry, since more pre-gym-1 catching means more such battles.

**Rejected:**
- (a) **Shipping a cap of 2 anyway, "for safety".** It is a guard with no measurable effect, and this project deletes
  those (CLAUDE.md rule 8).
- (b) **A cap of 1.** Measured harmful.
- (c) **Porting `party_healthy`.** Measured harmful.
- (d) **Lowering the expected-throws cap to about 5, to exclude Silcoon and Cascoon.** That is species targeting in
  disguise, and the 2026-09-26 decision rejected a per-species blacklist.

**Reopen if:** Phase 2 raises the pre-gym-1 target, or a batch shows pre-gym-1 catch-battle losses again. The H corpus
had 19; the last two batches had 0.

## 2026-09-27 — an unreachable training ground is remembered from BOTH the map where the walk died and the map it was chosen from

**Decision:** `_note_training_unreachable` writes two keys: the death map, which it always wrote, and the ORIGIN, the map
the ground was chosen from. Each of its three callers (counter hunt, MAINTAIN, relocation) captures `_here_map()` at its
pick. Arm: `POKEBOT_TRAINBLOCK_FAULT_DIEDKEY`.

**Rationale:** `_training_blocked` is read wherever the NEXT pick happens.
- After a RAISE (the relocation path) that is the death map: the derail recovery does not move the bot.
- After an ABANDON (MAINTAIN, a counter hunt) it is the origin.
- Only the death key was written, so the MAINTAIN memory never matched. ROUTE111 (25,55) was re-walked 19 times in
  P1r7, and each cycle ended in a heal derail, until the run ended.

**Rejected:**
- (a) **Origin only.** It breaks the relocation path, the one site where the old key worked; its comment records the
  deterministic death loop the memory was added to stop.
- (b) **Keying by the ground alone, from anywhere.** It breaks the deliberate "reachability depends on direction"
  intent: a ground unreachable from Lavaridge can be fine from Fallarbor.
- (c) **Turning on `AREA_ITEM_PREREQ`** so ROUTE111 is never picked before Go-Goggles. It is off by default by an
  earlier deliberate choice, and it fixes one ground, not the class.

## 2026-09-27 — the Lavaridge heal is fixed AT THE SEGMENT (F4), not in the navigator

**Decision:** the Flannery segment's heal is `early_game.heal_at_lavaridge()`. Outside the explicit `LAVARIDGE_MAPS` it
runs `do_jagged_descent()` (cable car up, Jagged Pass down, ending healed); inside it is the plain heal. Arm:
`POKEBOT_LAVAHEAL_FAULT_GENERIC`.

**Rationale** (`ai-research-notes/2026-09-27-healwalk-RECON.md`, a NOTE, plus the drive in
`2026-09-27-lavaheal-GRADED.md`):
- Before Flannery the generic navigator has NO route into Lavaridge from below. The cable car is a script, and Jagged
  Pass is one-way. So no navigator change can make the generic heal succeed.
- `do_jagged_descent` is the recovery the derail already ran, 53 of 54 times. Calling it directly is local: one call
  site, and the shared navigator is untouched.

**Rejected:**
- (F1) **Fix the step-off false failure.** It relabels the bounce as "Cannot reach", and it changes every navigator
  user.
- (F2) **Filter dead-end buildings.** It saves frames, not derail slots. The naive test is wrong both ways (it bans
  Petalburg Woods and Fiery Path, and misses Flat1).
- (F3) **Model split maps in the warp graph.** The largest regression surface, and it still cannot express the cable
  car.
- (F6) **Heal at a nearer centre.** `do_lavaridge_gym` next walks to Lavaridge with the same navigator, so the failure
  just moves.

## 2026-09-27 — the Norman heal TRIES the generic walk first and falls back only on failure (unlike Lavaridge's pre-check)

**Decision:** `heal_at_petalburg()` calls the generic heal first. Only on `HealWalkFailedError`, and only from a map in
`PETALBURG_ROAD_MAPS` (the maps `travel_lavaridge_to_petalburg` ranks), does it release held input and take that road.
Anything else re-raises as before. Arm: `POKEBOT_PETAHEAL_FAULT_GENERIC`.

**Rationale:**
- Unlike Lavaridge, Petalburg is walkable from many prep grounds: Route 102, Route 104's south half, Petalburg itself.
  A pre-check "outside Petalburg ⇒ take the road" would send those callers down a road that starts at its far end, since
  the road ranks unknown maps at -1 and runs every leg.
- Trying first keeps every working case byte-for-byte unchanged. The failing case costs one bounce, about 60 frames,
  before the fallback.

**Rejected:**
- (a) **A pre-check, as for Lavaridge.** It is wrong for the many walkable origins.
- (b) **Catching every `BotModeError`.** It would swallow a whiteout; `StoryAbort` is a `BotModeError`.
- (c) **Falling back without releasing held input.** KI-106's lesson: a raise abandons the walker mid-step. The gate's
  fault arm pins this.

## 2026-09-27 — USER OBSERVATIONS during batch `#27-batch0927`: catching still stops at 4 (re-affirms RULING 20), and a FUTURE fossil request

**Observation 1** (the user, watching the live batch): "It seems that the beginning still locks the party to 4
pokemon, bot stops catching once team reaches 4 pokemon (around Rustboro gym area, catches more when needing a counter
but thats about it, should be catching new pokemon constantly)".
⇒ **Ruling it re-affirms:** USER RULING 20 (2026-09-26), "catching always on; remove the catch-4/party-4 limit".
**What it tells us:** the fence is still closed. That is expected, because only Phase 0 (safety) is built; Phase 1
(the PC as the runway) and Phase 2 (open the fence behind a flag) are not.
**Consequence:** `#26-organiccatch` becomes the top BUILD priority. Design Phase 1 on a branch while the batch runs;
nothing merges before the park.

**Observation 2:** "it seems to explore and fight in the desert more often now, thats great! At some point in the future
we would need it to enter the desert cave random event to get a fossil (randomly chooses one each run)".
⇒ Filed as `#27-desertfossil` (FUTURE).
- The user's intent: get the desert fossil, choosing one at random each run.
- The referent is probably Mirage Tower on Route 111 (Root Fossil or Claw Fossil). The mechanics are UNVERIFIED; recon
  against the decomp comes first.
- ⛔ Do not re-ask the user what they meant: the intent is recorded here.

## 2026-09-27 — ⭐ USER RULING 22: A DEDICATED SHEDINJA SEQUENCE — THE ONLY DUPLICATE-CATCH EXCEPTION BESIDES RARE/SHINY; and two RULING 20 design points settled from the log (not re-asked)

**Asked because** the RULING 20 Phase 1 design (`ai-research-notes/2026-09-27-ruling20-phase1-DESIGN.md`) found that
with catching always on the party fills to 6 early, and a full party means Nincada's evolution produces no Shedinja.
Shedinja won about 39% of Norman fights in past runs.

**The user's answer (verbatim, typos as typed):** *"Make a specific shedinja hunting sequence when able to, either from
first nirvana or when doing another sweep after beating the elite 4, the goal is to catch all pokemon including shedinja
and shedinja will be the only exception to catching a duplicate outside of a rare/shiny in the event that the bot catches
a ninja dancing, evilces it to ninjas with no free pokemon slot, allow the duplicate catch and a specific nutcase training
sequence with an empty slot to get a shedinja. Does this make sense?"*

**Read as** (autocorrect: "nirvana" / "ninja dancing" / "nutcase" = Nincada, "evilces it to ninjas" = evolves it to
Ninjask):
1. A dedicated Shedinja sequence, run when able: at the first Nincada, or on a post-Elite-Four sweep. The goal is
   catching every species, Shedinja included.
2. Shedinja is the ONLY exception to "no duplicate catches", besides rare and shiny.
3. If a Nincada evolves into Ninjask with no free party slot, allow a duplicate Nincada catch and train it with an empty
   slot so Shedinja appears.

Confirmed back to the user in those terms. Filed as `#27-shedinjahunt`.

⚠ **To verify in the decomp before building:** that Shedinja needs a free party slot AND a Poké Ball in the bag at the
evolution, and that it consumes the ball.

**Two further design questions were settled FROM THIS LOG, not re-asked** (CLAUDE.md rule 11):
- **Do catches join the team?** YES. RULING 20's own words: "allowed a full team, catching along the way". Catches fill
  the party up to 6; the game boxes everything after that. RULING 13 (the L65-75 battle team, the roster is free) is
  the late-game rule and does not conflict.
- **Protect gym-TM recipients from deposit?** NO special protection. RULING 19's record says the user did not select
  "protect answers from deposit". Hunted counters stay protected until their badge; that is a design default, not a
  ruling, so it is open to change.

## 2026-09-27 — RULING 20 Phase 1, increment A: the REQUIRED-errand victim is the lowest-level unprotected member; counters expire at their badge

**Decisions** (design: `ai-research-notes/2026-09-27-ruling20-phase1-DESIGN.md`):
- (a) **One victim rule for both live make-room paths** (`pc_trip.make_room_victim`). Dead weight comes first, as today.
  Then, ONLY for a required errand (an HM learner, or a withdraw), the lowest-level member that is not protected or
  excluded, not an egg, not a sole HM carrier, and not the last living battler.
- (b) **A hunted counter is protected only while OWED**: from registration at badge count N until the count passes N.
  The mapping is generic, with no per-boss table.
- (c) **Gym-TM recipients get no protection** (RULING 19's recorded non-selection).

**Rejected:**
- A per-boss badge table: a table to maintain, and the generic count is the same thing for gym counters.
- Never falling back for required errands: that is `#24-partycap`'s dominant failure, "no free slot for a Surf learner".
- Falling back for ANY make-room: thinning the team without a required reason is what made `#24-pc` a regression.

**Known gap, stated:** the design's protection of the only compatible learner of a still-required HM is NOT built.
Increment B's box-first for Strength, Waterfall and Fly is the planned cover.

## 2026-09-27 — RULING 20 Phase 1, increment B (Strength): box-first only where a centre trip can come back; the boxed pick prefers a learner that cannot carry HM07

**Decisions** (recon: `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, a NOTE):
- (a) `ensure_strength_learner` gains `heal_centers=()`. Only the heal-stop caller in `travel_to_magma_hideout_door`
  offers a centre: `(center,)`, the one it stands next to (Lilycove, then Mauville).
- (b) The in-hideout caller (`open_magma_hideout_1f`) stays party-only. Its refusal now names any boxed learner.
- (c) The boxed pick is `boxed_hm_learner_pids(HM04, avoid=HM07)`: a mon that already knows Strength first, then one
  that cannot learn Waterfall, then level. That is `#24-hm07funnel`'s party rule applied to the box.
- (d) `POKEBOT_HMPCFIRST_FAULT=skipfix` (already registered) also disarms this site; `POKEBOT_R20_FAULT_NOLANDPREF`
  is new.

**Rejected:**
- Box-first at the in-hideout caller: the nearest centre is Lavaridge, reachable down the one-way Jagged Pass but not
  back up without the cable car, and the next step (`strength_push`) only walks the hideout map. Measured statically
  in the recon.
- Plain level order for the boxed pick: it would withdraw a Swampert/Marshtomp and spend a slot on the mon that must
  later carry Waterfall.

## 2026-09-27 — RULING 20 Phase 1, increment B (Waterfall): box-first INSIDE `ensure_waterfall_learner`, at Sootopolis only

**Decisions** (recon: `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, site "waterfall", a NOTE):
- (a) The box-first block lives in `ensure_waterfall_learner` and uses that function's own pick (compatible AND a non-HM
  slot to spend). A boxed mon qualifies if it already knows Waterfall or has a spendable slot
  (`_boxed_waterfall_learners`).
- (b) Segment 22b offers `(SootopolisCity,)`: the only centre reachable from the crater without Waterfall.
- (c) `_withdraw_hm_learner` returns and names the slot of the PID it was asked for, not `hm_learner_slot(item)`.
- (d) `POKEBOT_HMPCFIRST_FAULT=skipfix` disarms this site too; no new arm.

**Rejected:**
- Routing Waterfall through the generic `ensure_hm_learner_making_room`: its gate is `hm_learner_slot(item) is None`, which
  is False whenever a SATURATED compatible mon is in the party. That is 5 of the 6 measured 8-badge parties, so the
  generic path would never fire where it matters.
- Mossdeep or Ever Grande as centres: the planner refuses both from the crater, and Ever Grande's centre is above the
  waterfall (circular).

## 2026-09-27 — RULING 20 Phase 1, increment B (counters): box-first before the hunt with a NEW strict picker; the heal withdraws only OWED counters

**Decisions** (recon: `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, site "counter", a NOTE):
- (a) `_counter_ladder` asks `counter_hunt.box_counter_choice` AFTER its once-per-boss "started" mark (so the bound
  covers it) and BEFORE the planner and the ball check (a withdraw needs no ball; a planner failure must not hide an
  owned counter). On a pick it registers the PID through the shared `_register_counter`, which OVERWRITES the badge
  count, and returns True; the boss segment's own heal collects it.
- (b) `box_counter_choice` is NEW. It accepts an own-type match, or a damaging needed-type move with base power × 2 ×
  STAB ≥ 75. It ignores gym-TM-taught pairs (RULING 19) and party PIDs, and it ranks the candidates.
  `box_counter_pid` is left as it is, because a parity gate pins it to `party_counter_slot`.
- (c) The heal's counter withdraw collects `pc_trip.owed_counter_pids` only; `deposit_protected_pids` delegates to the
  same set, and its fault arms stay on the deposit side.
- (d) Recon H3 (the box-first counter arrives untrained) is NOT addressed: same as today's box-catch path.
- (e) Recon H2 is ACCEPTED, and it is a real behaviour change (review, 2026-09-27): every segment picks its lead
  BEFORE its heal, so a box-first counter is ALWAYS still boxed when the lead is chosen and first leads on the
  attempt after its collection. A party-caught hunted counter usually leads at once.

**Rejected:**
- Reusing `box_counter_pid`: lenient (a Rock Smash or Mud-Slap carrier qualifies) and first-in-box-order; it would spend
  the ladder's one action for the boss on a non-answer.
- Keeping the full-registry withdraw: after increment A, make-room may box an EXPIRED counter, and the next heal would
  collect it again (the C5 arm reproduces this).
- Training a box-first counter before its first attempt: a larger change to `_prepare_for_fight`; left for a design pass.

## 2026-09-27 — RULING 20 Phase 1, increment B (Fly) + USER RULING 21: the lobby PC; the lowest fighter sits out; the swap-back happens in the lobby, before the guards

**Decisions** (recon: `ai-research-notes/2026-09-27-ruling20-incB-RECON.md`, site "fly", a NOTE):
- (a) Box-first Fly uses the League LOBBY PC, the only PC reachable from the plateau without Fly. `pc_trip.pc_stand_for`
  gives (6,2)/Up there; every other map keeps (10,2)/Up.
- (b) **Which fighter sits out** (the question RULING 21 left open): increment A's make-room rule decides, so dead
  weight goes first, then the lowest-level unprotected member. In practice that is a mule (Zigzagoon on the fixture).
  It is the member whose missed training costs the least, and RULING 15 already lets R1 pass with 4 of 6 at the floor.
  The user was told this default before the build.
- (c) **The swap-back happens IN THE LOBBY, after `E1-INSIDE` and before the guard talk**, not before R1 as the
  ruling's wording ("restored and checked by PID before R1") suggests. R1 is decided wherever training ended, often
  off the plateau, and only the lobby has a reachable PC. To keep R1 honest, it counts only fighters: the carrier is
  left out of the trainees and of R1's head-count. The ruling's intent (the same six fighters, checked by PID, before
  the Elite Four) is kept; talking to the guards sets `ENTERED_ELITE_FOUR` permanently, so the lobby is the last point
  it can happen.
- (d) A swap-back that does not land REFUSES by name (it does not enter with the carrier).

**Rejected:**
- The standard (10,2) stand tile in the lobby: a guard's tile (no path), and under the step-on door to HALL5.
- Swapping back before R1: needs the lobby PC from wherever training ended, which may be off the plateau.
- Letting `withdraw_from_box`'s make-room choose the swap-back victim: it picks by rule, not the carrier.
  `swap_party_box` names both mons.

## 2026-09-27 — KI-107: bound the whiteout recovery's waits NOW; leave the root cause (F1) for a driven fix

**Decision:** ship F3 (bounded recovery waits, a named raise after 20,000 frames) and F4 (log the KI-47 park; dumps
follow the `inner` generator) from `ai-research-notes/2026-09-27-ki107-RECON.md`. F1 (unwind a pending whiteout at once
in `run()`'s per-frame loop) waits for a driver that reproduces the stale flag.
**Why:** F3/F4 change nothing on the ordinary path. A normal respawn is controllable in a few hundred frames, and the
real recovery path was re-driven (`--driver evgpcwedge`). They also cap a measured 79-lane-minute loss. F1 changes the
core loop every run goes through, and this project does not ship a core-loop change on a forensic reading alone.
**Rejected:** a silent timeout (the derail branch's `wait_until_truly_controllable` returns silently). The run would
continue into a battle menu and fail later under another name, which is how KI-107 hid in the first place.

## 2026-09-27 — `#24-restockleg` F1 (USER RULING 12): R1 restocks ONCE, inside itself, only when the basket is its ONLY reason

**Decision:** R1 in `prepare_and_open_the_league` runs §Ch23 leg 11's existing shop (`stock_for_the_elite_four`) once
and decides again, when every reason is the basket's and the bot is on Ever Grande or in the lobby
(`ch24_should_restock`). There is no separate §Ch24 restock leg with its own re-entry predicate.
**Why:**
- The measured failure (batch run P4r2) was R1 refusing five times on a basket it could afford. R1 already runs on
  every re-entry, including after a loss, so restocking at R1 covers the post-loss case without a new predicate.
- The shop already buys only the missing lines (RULING 16) and refuses by name when cash plus sellables cannot cover
  them. Reusing it keeps one buy path for the whole game.
- R1 decides again after the shop, so the RE-ENTRY GATE STAYS BAG + MONEY (the punch-list's rule: never health).
**Rejected:**
- Restocking alongside a level shortfall: R1 would still refuse on levels, so the purchase changes nothing now. The
  next R1, after training, restocks anyway.
- Restocking off Ever Grande/the lobby: no Mart is reachable from there without the return bridge.
- A retry loop around the shop: an unaffordable basket stays unaffordable, and the chapter's own retry already
  re-runs R1.
**Not decided here:** the bag heal's order (it spends Full Restores before Hyper Potions; the recon's F2) and the PP
problem (the League Mart sells no Ether/Elixir/Leppa).

## 2026-09-27 — RULING 21's identity check accepts an EVOLUTION on the same PID (not PID-only, not a re-record)

**Decision:** `ch24_fighters_restored` matches each recorded fighter to exactly one party member with the same PID whose
species is the recorded one or an evolution of it (walking `evolves_from`).
**Why:** the record is taken before §Ch24 training, and training evolves trainees. An exact `(pid, species)` equality
refused a correct party. Evolution is the only change training makes to a fighter's identity key.
**Rejected:**
- PID only: KI-78's Ninjask and Shedinja share a PID, which is why `(pid, species)` was used in the first place.
- Re-recording the fighters after training: the record exists to name WHO the fighters were at the swap. A re-record
  would accept whatever the party holds by then.

## 2026-09-28 — The destructive-git hook: Python with a shell-aware pre-scan; a hatch read from the COMMAND; every hook located via $CLAUDE_PROJECT_DIR

**Decision (the user approved the hook itself, 2026-09-28):** `.claude/hooks/block_destructive_git.py` denies git
commands that can silently discard uncommitted work, published history or a branch, and allows ordinary work and mere
mentions. The escape hatch is a LIVE `POKEBOT_ALLOW_DESTRUCTIVE_GIT=1` prefix on the git command itself. Every hook in
`.claude/settings.json` finds its script through `"$CLAUDE_PROJECT_DIR/.claude/hooks/..."` and ends in `|| true`.
**Why:**
- A reviewer's `git checkout --` deleted an uncommitted fix on 2026-09-27; CLAUDE.md already forbade it, in prose.
  The blocked set is CLAUDE.md's existing rules, so the hook adds no new policy.
- PYTHON, NOT POWERSHELL: the first (PowerShell) draft emitted INVALID JSON (a BOM-less .ps1 is read as Windows-1252),
  so it could never have blocked anything, and a hand-written PowerShell parser let 49 of 79 probes through. Python's
  `shlex` plus a small per-shell pre-scan (quotes, escapes, comments at a word start, continuations, heredocs,
  here-strings, `$( )`) survived two more adversarial rounds; its confirmation review found 0 false positives over
  200 real commit messages, 691 real branch/tag checkouts and 61 multi-line scripts, at ~85 ms per call.
- The hatch is read from the COMMAND because the hook runs in its own process: a variable in the command never reaches
  it (why the older hooks' documented prefix does not work, `#27-hookhatch`).
- `$CLAUDE_PROJECT_DIR`: with a relative path, a hook runs against the session's CURRENT directory. MEASURED: from
  `tools/story-dev` the new hook exited 2 (= block everything) and the old `git add -A` hook silently let a dry run
  through. `|| true` stops a path failure from ever exiting 2.
**Rejected:**
- Blocking every `git checkout`: it is also the branch switch. Operands are asked of the repo (a real ref is not a
  file); a `$var` or xargs operand counts as a path (so checking out a branch held in a variable is blocked: the deny
  message offers `git switch`).
- A sandbox-grade parser: the hook is a seat belt against habit. Deliberate evasion (splatting, `eval`, interpreters
  that shell out, GIT_* redirection, unicode look-alike whitespace) is listed as a known limit.

## 2026-09-28 — The after-faint chooser decides by IDENTITY (PID + species); every index conversion is confined to a fault arm (`#27-ki47range`, KI-47)

**Decision:** `handle_fainted_pokemon` records WHO the strategy chose, `(personality value, species index)`, and once
the in-battle menu is open finds that identity in `get_party()`. The sweep's candidates are the menu slots of living
non-egg mons whose identity is not on the field. The pure logic lives in `modules/faint_chooser.py`. The three old
conversions (the primary map through the entry snapshot, the KI-66 on-field map, KI-34's second map) run ONLY under
`POKEBOT_KI47_FAULT_STALEMAP=1`, and `probe_faint_chooser_identity.py` W1 fails if a conversion appears outside it.
**Why:**
- This function had FOUR index-space bugs (KI-18, KI-34, KI-66, KI-47). Each fix corrected one conversion and left
  the class alive. Identity removes the class: no order is consulted, so a stale or foreign
  `gBattlePartyCurrentOrder` cannot matter (CLAUDE.md rule 3).
- The premise that makes identity work is checked three ways:
  - the decomp (a NOTE: `OpenPartyMenuInBattle` calls `UpdatePartyToBattleOrder()` synchronously, so `gPlayerParty[i]`
    IS menu slot i while the menu is open);
  - KI-66's own measurement;
  - LIVE, by the fixed `Swp` arm (a natural non-identity order).
- Species is in the key because a Shedinja is a byte copy of its Nincada (`CreateShedinja`), so a Ninjask and its
  Shedinja share a PID and OT ID, and the story party carries a Nincada.
**Rejected:**
- The PRE-REGISTERED fix (b), "map the primary index through a FRESH `get_battle_state()`": UNSOUND.
  `BattleState.__eq__` omits the order, so a second call in a frame can return a stale-order object. Measured: the
  handler read `012345` while memory held `104523`.
- A raw `read_symbol` of the order at menu-open: correct today, but it keeps the conversion class alive, and that class
  has cost four bugs.
- Fixing `BattleState.__eq__` inside this item: it changes the inputs of the KI-96 swap, KI-101 item-target and
  move-replacement paths, and each needs its own A/B. Filed separately as `#27-battleeq`.
- A range guard ("drop candidates >= len(party)"), the registered part (c): candidates now come from
  `enumerate(party_in_menu)`, so it could never fire, and a guard that cannot fire is decoration.

## 2026-09-28 — The `#24-faintchooser-fourthspace` closure (2026-08-17) is SUPERSEDED by measured evidence

**Decision:** the closure's *"inert in behaviour. ⛔ DO NOT FIX IT, and do not re-commission the probe"* no longer
stands. The current-state text in `05` says so wherever it appears.
**Why:**
- RULE 11 WAS CHECKED FIRST. This log holds no USER ruling on the item. The closure was an agent's probe, n = 1, with
  stated limits.
- Its acceptance clause (*"the accepted cursor is in `alive_slots_menu`"*) holds by construction.
- The consequence it filed as a "residual" (Mightyena nominated, Swellow sent) was measured on 2026-09-28 as the bug:
  - arm `Swp` (a natural order after one switch): the WRONG mon sent;
  - arm `Foor` (the enemy's order): the chooser FROZE, which is the shape of the 4 faint-chooser wedges in batch
    `#27-batch0927`.
  - Evidence: `ai-research-notes/2026-09-28-ki47range-GRADED.md`.
- This is NOT a re-run of the old probe on the old evidence, which is what "do not re-commission" guarded against.
**Rejected:** leaving the closure text as it was. A current-state "DO NOT FIX IT" next to the fix is exactly what a
future agent would cite to revert it.

## 2026-09-28 — RULING 20's catch telemetry is ALWAYS ON (no flag), and it ships ahead of every behaviour change

**Decision:** the step T lines (`[CATCH]`, `[CATCHTEAM]`, `[BALLS-BUY]`, `[BADGE]`, heartbeat `box=`/`badges=`,
`env-all:`) are unconditional. The only env switch is the grader's fault arm `POKEBOT_R20_FAULT_NOCATCHEND`.
**Why:**
- Every Phase 2 arm, flag ON and flag OFF alike, is graded on them. A flag would make the control arm blind, which
  is the arm that matters most.
- Their cost is one PC read per catch plus one per heartbeat (both off the per-frame path).
- They were proven not to change a battle: 24 of 24 `[BATTLE]` lines are identical to a no-telemetry control.
**Rejected:**
- A flag, default off: the batch A/B would need it on in both arms anyway, so it is just a way to forget it.
- Rewriting the existing `env:` line to scan by prefix: `repro_debug_log_header.py` pins its text. A NEW `env-all:`
  line adds without breaking a reader.
- Emitting through a method: the gates call these hooks with stand-in `self` objects, and a missing method inside a
  catch branch's `except: pass` would silently cancel the catch.

## 2026-09-28 — `--set-balls N` sets the Poké Ball STACK only, and a failure aborts the run

**Decision:** the harness lever keeps every other ball stack (Premier, Great, Ultra, …) and re-raises on any failure.
**Why:**
- An arm that "sets 30 balls" should differ from its control in ONE thing. Silently deleting a fixture's special balls
  changes the thrower's sequence and the fence's expected-throws estimate (which scores the whole bag), a second
  difference nobody asked for.
- A test lever that fails and continues produces a run that is not the arm it claims to be. That is exactly how this
  one went unnoticed for two months.
**Rejected:**
- Keeping the replace-the-pocket behaviour: no committed evidence depended on it, and it confounds arms.
- Logging louder but continuing: the old code already logged, and nobody read it.

## 2026-09-28 — A hunt's spin tile is filtered and ASSERTED by tile type; the filter fails OPEN; no automatic retarget

**Decision:**
- `_hm_hunting_grounds` drops grounds whose spin tile cannot roll a LAND encounter. When the map data is unreadable, it
  KEEPS the ground.
- `ensure_hm_learner` raises a named error on arriving at a tile that cannot roll one, and does NOT try the next
  ground itself.
**Why:**
- Failing open matches the rule already written beside `_HM_HUNT_EXCLUDED`: a no-ROM context must not silently empty
  the list.
- A named raise is loud and bounded, and the story's recovery already retargets after a derail (the batch showed
  Route 103 after each Route 101 derail). An in-place retry would hide the defect a second time.
**Rejected:**
- Making the "prefer a reachable ground" check warp-aware, so an indoor start stops falling back to `grounds[0]`: the
  right long-term fix, but a larger change to shared navigation. The tile fix removes the harm without it.
- Counting real frames in `_story_spin`'s bail (the recon found it counts stop-condition CALLS): it touches every spin
  in the game and needs its own A/B on the ordinary grass case.
- Allow-listing the ocean rows silently: the gate lists them against `#27-waterrows` and FAILS if that list goes
  stale.

## 2026-09-28 — RULING 20 P2-a ships OFF, with its `none_left` exit active only under the flag

**Decision:** `POKEBOT_R20_TEAM6` defaults OFF. The new `none_left` exit and the catch-ends-the-spin clause run only
when the target is above 4. The spec's defensive egg bound is not built.
**Why:**
- `#24-partycap` measured this exact raise costing 36 points. Enabling it without the Phase 3 A/B would repeat an
  experiment with a known bad result.
- Keeping every new clause behind `target_size > 4` makes OFF byte-identical (verified by review: both short-circuit),
  which is the ordinary case `#24-partycap` warns about disturbing.
- A guard that cannot fire (no egg source before gym 1) is decoration.
**Rejected:**
- Enabling the `none_left` exit for target 4 too: it is a real improvement, but it changes the ordinary case.
- A flag default of ON: see the measurement.
## 2026-09-28 — RULING 20 P2-b lifts ONE refusal, behind a flag that ships OFF; its fault arm is "the open branch returns early"

**Decision:**
- `POKEBOT_R20_OPENFENCE` (default OFF) removes only the post-gym-1 "party is N/6 — runway" refusal. Every later gate
  still applies to a party join: hunt, training, ball reserve, a full PC, full strength, the attempt cap, expected throws.
- The fault arm is `POKEBOT_R20_FAULT_OPENEARLY` (the open branch admits before the later gates). It replaces the build
  spec's reserve-only arm.
- The PC-full gate stays for party joins, although a join needs no PC space.
**Why:**
- The likeliest wrong build of "open the fence" is `return True` at the fence, which skips all seven later gates at once,
  and a catch battle never fights back. The reserve-only arm would have proved one of the seven.
- OFF ships because `#24-partycap` measured the runway's value (−36 points when filled early). Whether the PC-first
  make-room paths absorb that is the Phase 3 batch's question.
- A story run with every PC slot full is practically unreachable, and one fewer special case keeps the predicate simple.
**Rejected:**
- The spec's `…FAULT_OPENNORESERVE`: it covers one gate of seven.
- A separate catch strategy for party joins: the post-badge `StoryDexCatchStrategy` (reserve and faint bail) already
  applies to every dex catch, and a join is no less discretionary than a box catch.
- Seeding the bot's organic RNG in production to make drives replayable: the randomness is deliberate ("organic"). The
  harness is seeded from outside instead (a `runpy` wrapper), for the A/B only.
## 2026-09-28 — `#27-enroutejoin`: refuse a PARTY JOIN while a hunt walks, rather than re-reading the party on arrival or arming before the walk

**Decision:** `early_game.hunt_walk(walk)` marks each HM or counter hunt's walk (the mart trip and `_navigate_riding_out`).
`decide_dex_catch` refuses a catch when `hunt_walking and open_fence and party < 6`. Flag OFF and the full-party box
path never reach that refusal.
**Why:**
- It removes the cause (a party that changes under a hunt's plan) at the one place the audit found it can change, for
  BOTH hunts at once.
- It is invisible to flag OFF, which is every real run today.
- It restores exactly what flag OFF already does on the walk: no party join there. So opening the fence costs a hunt
  nothing it had before.
**Rejected:**
- **Re-reading the party on arrival in `ensure_hm_learner`.** A 5 → 6 join still leaves the HM catch branch refusing
  the target (`len(party) < 6`), so the hunt spins to its deadline instead. It also fixes nothing in `counter_hunt`
  (the counter still goes to the box).
- **An identity-based stop condition:** the same 5 → 6 problem.
- **Arming each hunt before its walk:** catch-on-sight would then fire during the walk. That changes the ordinary
  hunt's behaviour and the counter hunt's snapshot semantics, which is a larger change than this defect needs.
- **Refusing only the hunt's own target species on the walk:** any new member breaks the HM hunt's count.
## 2026-09-28 — RULING 20 P2-c ships OFF, covers a WALKING hunt as well as an armed one, and has no production fault env

**Decision:**
- `POKEBOT_R20_HUNTFIRST` (default OFF) puts two refusals BEFORE the pre-gym-1 team-building branch, and only before gym
  1: an armed hunt, and a hunt walking to its ground.
- Flag OFF is the skip-the-fix arm. No `…_FAULT_…` env was added.
**Why:**
- The spec named only the armed case. But a pre-gym-1 team catch is a PARTY JOIN, which is exactly what
  `#27-enroutejoin` refuses on a hunt's walk after gym 1. Leaving the walk open before gym 1 would reopen that hazard
  for the counter hunt (the counter pushed into the box once team catches fill the party).
- After gym 1 the later checks already run in this order, so the flag is scoped to `pre_badge1`, and the post-gym-1
  path is byte-identical (gate H6/H7).
- The guard IS the flag: turning it off restores the old order exactly. The gate's order mutant (F1) covers "the flag
  is read but the order is wrong".
**Rejected:**
- The armed case only: leaves the walk open (above).
- Applying it after gym 1 too: at a full party it would refuse box catches during a hunt's walk, which harm nothing.
  That would be a behaviour change with no defect behind it.
- A production fault env: it would duplicate the flag.
## 2026-09-28 — USER RULINGS 23, 24 and 25: the answers to RULING 20's §8 questions (money for balls, catching while hurt or training, the attempt cap)

The user answered the three policy questions of `ai-research-notes/2026-09-27-ruling20-phase2-BUILDSPEC.md` §8
(2026-09-28, evening). ⛔ **Do not re-ask any of them.**

**USER RULING 23 — money for Poké Balls (§8 Q1).** The user's words: *"yes and a reasonable amount, I am not sure at
this moment but this also brings up more money making (seeking trainers for first time battle and re-battling)."*
- ⇒ The bot MAY spend money on Poké Balls for Pokédex catches before badge 7. This unblocks build step **B** (the
  ball restock at the dex reserve).
- ⇒ **The amount is NOT ruled.** The build must propose a concrete, bounded default and show it to the user. It must
  leave RULING 18's League basket and its ₽1,000 reserve untouched.
- ⇒ NEW DIRECTION, to be planned rather than built blind: **money-making** by battling trainers the bot has not fought
  yet, and re-battling them (rematches).

**USER RULING 24 — catching while hurt or training (§8 Q2).** The user's words: *"catching should always be available if
the bot encounters a pokemon that it wants to catch, even in training and wounded pokemon. If the bot whites out or the
training pokemon faints, thats ok because it can always heal or travel to heal, catching has a bit higher priority."*
- ⇒ The dex fence's "a training grind is in progress" and "party is not at full strength" refusals are to be REMOVED
  for a species the bot wants.
- ⇒ A faint or a whiteout during a catch is ACCEPTED: catching outranks avoiding them.
- ⇒ It narrows the 2026-09-26 design choice to port the full-strength check (`06`: "The health check is a design
  choice … not a ruling"). That choice is now overruled by the user.

**USER RULING 25 — the attempt cap (§8 Q3).** The user asked whether the cap is per encounter. It is not: it is per
SPECIES per RUN (`DEX_CATCH_MAX_ATTEMPTS = 2` catch battles started against one species in one run). The user's words:
*"I think bumping it up to 3 unless its rare/shiny/legendary. But ultimately the bot should try to catch the pokemon."*
- ⇒ **INTERPRETATION, stated to the user in the same reply** (reversible if they correct it): a cap of **3** catch
  battles per species per run for ordinary species, and **no cap** for a rare, shiny or legendary one. Shinies
  already take their own always-catch branch. "Rare" still needs a concrete definition, proposed in the design.
- ⇒ FUTURE DESIGN, to be DISCUSSED with the user before any build: **weakening the target before catching it**, done
  carefully. The design must account for indirect and self damage: weather, Spikes, and a target that knows
  Self-Destruct / Explosion, Double-Edge (recoil), Curse, or a weather move.

**Why these are recorded here:** CLAUDE.md rule 11. This file exists so a question is never asked twice. The three §8
questions are CLOSED.
## 2026-09-29 — USER RULINGS 23 and 25 CLARIFIED, and USER RULINGS 26 and 27: stocks kept all game, the best ball, never give up on a wanted rare, weaken-to-catch BUILT, healing items in key battles only

The user answered the five questions of `ai-research-notes/2026-09-28-r23-25-DESIGN.md` §5 (2026-09-29). ⛔ **Do not
re-ask any of them.**

**RULING 23, clarified (the ball budget).** Q1 asked about "₽20,000 per run". The user's words: *"What do you mean per
run? like per bot run or per hunting run? it should be unlimited if its per bot run (session) but limit it to buying the
balls in batches so it buys a reasonable amount of balls but doesnt spend too much per batch (that it
maintains/tops off periodically just like healing items)."* Also, from the Q4 answer: *"ensuring it buys the best
pokeball available to it at the respective shop."*
- ⇒ **NO per-run spending ceiling.**
- ⇒ **Purchases come in bounded BATCHES**, topped off periodically the way healing items are.
- ⇒ **Buy the BEST ball the current shop sells.** This supersedes the design's "Poké Balls only".
- ⇒ RULING 18's League basket and reserve still stand.

**USER RULING 26 (new, from the Q2 answer): keep stocks all game.** The user's words: *"Bot should be maintaining its
healing items and ball stock through out the game, focusing more hevily on ball stock post elite 4 (can also battle
elite 4, re-battle gym leaders and trainers for money if needed)."*
- ⇒ Healing items AND balls are maintained throughout the game. There is no badge-6 or badge-7 stop.
- ⇒ After the Elite Four the weight shifts to balls.
- ⇒ POST-GAME money: re-battling the Elite Four, gym leaders and trainers is allowed when money is needed.
- ⇒ The user approved the design's money-making plan (§4a): *"Your plan for "Money-making" makes sense."*

**RULING 25, clarified ("rare", hard catches, giving up).**
- **Q3, what "rare" means.** The user's words: *"We already talked about this a while ago, check the notes/documentation."*
  It is **ROSTER RULING 3** (`06`, 2026-08-06, "'rare' … = THREE OR'd rules"), refined by the user on 2026-08-14 (in
  `03-PUNCH-LIST.md` `#24-rarepredicate`). The rules:
  - shiny;
  - a rare gender variant ("Male Skitty");
  - a low encounter rate (Skitty 2%);
  - "pseudo-rare": field-move GATES plus few LOCATIONS (Bagon behind Surf and Waterfall, in one place);
  - explicit special cases (Feebas).
  ⛔ **The 2026-09-28 design proposed a NEW "≤ 10% rate" definition without finding this ruling. That is superseded.**
- **Q4, hard catches.** The user's words: *"It should still try to catch without limit if it wants to catch the pokemon
  but we should implement that weaken to catch pokemon logic so it increases its catch rate (also ensuring it buys the
  best pokeball available to it at the respective shop)."*
- **Q5, giving up.** The user's words: *"No it should continue to attempt to catch it, same answer as response to question
  4."*
- ⇒ **A wanted RARE species is never given up on:** no attempt cap, and no expected-throws refusal.
- ⇒ **WEAKEN-TO-CATCH IS TO BE BUILT, not only discussed.** It carries the safety concerns RULING 25 named: weather,
  Spikes, Self-Destruct/Explosion, recoil, Curse, weather moves.
- ⇒ **Interpretation, reversible if the user corrects it:** ORDINARY (non-rare) species keep RULING 25's cap of 3.

**USER RULING 27 (new): healing items during KEY battles only.** The user's words: *"also ensure that the bot can use
healing items during battles (gym leaders, story "bosses" and elite 4 only) so it has a better chance at winning those
key battles."*
- ⇒ In-battle healing-item use is allowed against gym leaders, story bosses and the Elite Four, and NOT in ordinary
  battles.
## 2026-09-29 — RULING 24 step 2: the health lift removes ONE refusal, and a lost DEX catch is filed apart from map defeats (team losses are not)

**Decision:**
- `POKEBOT_R24_CATCHHURT` (default OFF) skips only `decide_dex_catch`'s "party is not at full strength" refusal. Every
  other gate keeps its order.
- With the flag on, a LOST battle whose open catch kind is `dex` goes into `_catch_defeat_counts`, not
  `_defeat_counts` / `_loss_ko_history`.
- `team`, `hm`, `counter` and `shiny` losses are unchanged.
**Why:**
- RULING 24 accepts losing a catch battle. Counting that loss as a map defeat would then trigger survival mode (3+
  defeats on a map flees every wild, the wanted ones too), or count as a boss loss on that map (e.g. the Route 110
  rival's key). That would punish the behaviour the ruling asks for.
- Pre-gym-1 `team` catches are excluded because `#24-partycap` protects that regime, and the design's checker showed
  that including them would change survival-mode triggering there.
- `_last_defeat_key` is skipped along with the rest. It is written in one place and read nowhere (grep).
**Rejected:**
- Filing every catch kind apart: this changes pre-gym-1 behaviour.
- Leaving catch losses as map defeats: survival mode would then flee the very species RULING 24 says to catch.
## 2026-09-29 — RULING 24 C4 knowingly changes what a SHARED map key sees; `_catch_defeat_counts` is telemetry only

**Recorded from the step-2 adversarial review, to avoid a surprise later.**
- A boss's loss counters are keyed by MAP. The Route 110 rival uses `keys=[ROUTE110]`
  (`story_mode.py` `rival110_fight`), and `_boss_plan_is_hopeless` and the escalation ladder read them.
- With `POKEBOT_R24_CATCHHURT` on, a lost DEX catch against a wild Pokémon on such a map no longer adds to that
  counter. **Accepted, deliberately:** that loss was never the boss's. The boss's own losses cannot be diverted: a dex
  catch is only ever opened in a WILD battle, and `_boss_battle` is only set for trainer battles.
- `_catch_defeat_counts` is written and logged but read by nothing yet. It is telemetry until a consumer needs it.
## 2026-09-29 — RULING 24 step 3: the training lift removes ONE refusal; a training dex catch keeps the trainee as lead; the flag is read from the RUNNING mode

**Decision:**
- `POKEBOT_R24_CATCHTRAIN` (default OFF) skips only "a training grind is in progress".
- A `StoryDexCatchStrategy` built while swap-training, with the flag on, returns None from
  `choose_new_lead_after_battle`, so a faint in that catch does not rotate the lead.
- The strategy reads the flag from `context.bot_mode_instance._r24_catchtrain`, the running mode's per-run value. The
  pinned call site `return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()` is unchanged.
**Why:**
- `train_team` picks its trainee by SLOT. The inherited rotation (it fires when the lead has fainted) would put another
  mon in slot 0 and train the wrong one: the KI-84 early exit in `slots={0}` grinds. `train_team`'s own heal restores a
  fainted trainee.
- One source for the flag (the P2-a lesson: two readers of one setting must read it from one place).
- `probe_dexcatch_bail.py` pins the call site's exact text.
**Rejected:**
- Passing the flag through the constructor: this changes the pinned call site.
- Reading the env inside the strategy: that makes a second reader of the flag.
- Leaving the rotation: it defeats slot-based grinds exactly when RULING 24 accepts a faint.

## 2026-09-29 — RULING 24 step 4: a wanted species outranks SURVIVAL MODE; the dex commit is ONE helper called from two places, through the class

**Decision:**
- `POKEBOT_R24_OVERSURVIVAL` (default OFF) runs the dex-catch commit BEFORE survival mode, the flee-every-wild rule for a
  map with 3+ defeats. OFF runs it after, where it always ran.
- "Wanted" is OPERATIONAL here: `_should_catch` admits the encounter, so every other fence gate still applies. An
  unwanted species still meets survival mode. Shiny, HM and counter catches stay first.
- The commit is `StoryMode._dex_catch_commit`, the old block MOVED unchanged (AST-identical). Both call sites go through
  the class (`StoryMode._dex_catch_commit(self, …)`).
**Why:**
- RULING 24: *"catching should always be available if the bot encounters a pokemon that it wants to catch"*. Measured:
  M0 fled an unowned Poochyena at full HP on Route 110. Survival mode exists for #24-whiteout's 25-whiteout loop, which
  an unwanted species must still get past.
- One helper keeps ONE commit site: attempts, telemetry and the dex/team strategy choice. OFF is provably the old code.
- The class call: harness drivers and repros pass a stand-in `self` (08, 2026-09-29).
**Rejected:**
- Asking `_should_catch` inside survival mode's condition: that is a second evaluation site with the commit still
  AFTER, and its log/attempt effects are split across two places.
- Moving the call unconditionally: it changes default behaviour before the Phase 3 batch A/B.
- Exempting only RARE species: the ruling says any species the bot wants.
- Tying C4 (a lost dex catch filed apart from map defeats) to this flag too. C4 stays keyed on `POKEBOT_R24_CATCHHURT`,
  and the registry row says to run the two TOGETHER. Without CATCHHURT, a lost catch on a boss-key map (Route 110 is the
  rival's) counts toward that boss's give-up. Widening C4 here would change a gated step's contract inside another
  step.

## 2026-09-29 — RULING 24 step 5: no faint bail on a dex catch, on BOTH paths; the flag is read from the running mode; BAILWIDE became a gate mutant

**Decision:**
- `POKEBOT_R24_NOFAINTBAIL` (default OFF): a faint during a post-gym-1 DEX catch no longer bails.
  - (a) `should_flee_after_faint` returns the parent's answer (False: the handler sends the next able mon).
  - (b) `_fainted_this_battle` stays False, so `decide_turn` cannot flee "a team member fainted" on the next turn.
  - The reserve bail and the trapped-and-empty fight stay.
- `StoryDexCatchStrategy` reads the flag from `context.bot_mode_instance._r24_nofaintbail`, the running mode's per-run
  value.
- The design's `POKEBOT_R24_FAULT_BAILWIDE` is a SOURCE MUTANT in the gate (F2), not a production env read.
- The `[DEXCATCH-NOBAIL]` line is deduped per FAINT (keyed on the fainted-member count), because the handler calls the
  hook twice for one faint.
**Why:**
- RULING 24: *"If the bot whites out or the training pokemon faints, thats ok … catching has a bit higher priority"*.
- Both paths: HALF, the live fault arm, measured that (a) alone still flees exactly one turn later.
- One source for the flag: the P2-a lesson and the step-3 pattern.
- BAILWIDE only proves the gate reads the reserve row, and no live run would set it. A production env read with no live
  use is clutter a later reader must reason about.
**Rejected:**
- Only path (a): measured to flee a turn later.
- Clearing `_fainted_this_battle` in `decide_turn`: that is a second site for one rule.
- Keying the telemetry on the fainted battler: during the send-in the "active battler" is already the NEXT mon, so the
  key would differ between the handler's two calls.

## 2026-09-29 — READINGS OF THE RECORD that design v2 builds on (recorded so they are not re-derived or re-asked)

These are READINGS of existing rulings, made by the design v2 synthesis and its two adversarial checks
(`ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md`). They are not new user rulings. Each is reversible by the user.
- **"Wanted"** = the 2026-07-31 ruling's INTENT (06:1181-1182: *"Catch every unseen species … Dex-complete intent"*).
  - Its except/"cheap" clause is the GUARD, and parts of it are superseded: the boss-prep/grind parts (06:1202-1203) by
    RULING 24 (06:8039-8040); the full-party skip (06:1200-1201) by the box path (06:4895-4901).
  - The build's OPERATIONAL test is "`_should_catch` admits". The definitional "wanted" is used only for refusal
    telemetry and metrics.
- **The 10-ball dex reserve still applies to a wanted RARE species (the build default).**
  - 06:8095 lifts only the attempt cap and the expected-throws refusal, and says nothing about the reserve.
  - The reserve must stay a separate constant (06:4881) and exists for the mandatory hunts (06:7459-7460).
  - Whether to throw past it is open question Q8 in the v2 note. Record the user's answer HERE when it comes.
- **The Sootopolis (Juan) healing kit is not held back for a question.** RULING 26 (06:8075, *"no badge-6 or badge-7
  stop"*), RULING 27 (06:8103, gym leaders) and RULING 18's reserve, which withholds only the League basket
  (06:7391).
- **An uncapped rare species may cost repeated whiteouts.**
  - This consequence was shown to the user (v1 §5 Q5, `2026-09-28-r23-25-DESIGN.md:577-579`) and accepted ("No it
    should continue to attempt to catch it", 06:8093-8095). There is NO reopen trigger.
  - If an unattended run is seen looping on a rare species, *"this is the known cause and it is BY DESIGN — the fix is
    a new ruling from the user, not a unilateral cap"* (the 06:5358-5359 wording, carried over).
- **§Ch24 RULING 2's three clauses are all scoped "for §Ch24"** (06:5670-5671), and none is superseded. That the kit
  reaches the Elite Four rests on RULING 26 (06:8072-8073, 06:8075).
- **Rare = the archived rule's RATE half (`best_slot_rate <= 4%`, archive ~6149)**, because the user deferred "rare"
  to the notes (06:8081).
  - Its warp-depth half is REPLACED by the user's 2026-08-14 pseudo-rare reasoning (field-move gates + few locations;
    open question Q6 in the v2 note for the exact cut).
  - The warp-depth dataset itself now reproduces; see the next entry.

## 2026-09-29 — `#24-rarepredicate`: the 2026-08-07 "the dataset does not reproduce" verdict is RETRACTED (two script defects)

**Decision:**
- The retraction: `rare_species_dataset.py` had two defects.
  - It read `edge[1]`, a tile coordinate, as a warp's destination map (`warp_graph.py` `to_json` is
    `[from_map, from_coords, to_map, to_coords]`).
  - It seeded the underwater group-0 maps, (0,50)-(0,56) in `map_data.py`, at depth 0, under a false comment.
- With both fixed, it reproduces EVERY number of the 2026-08-06 record: the histogram, 13 at depth ≥ 3, 26 RARE,
  Bagon d3. Those numbers are now HARD, fault-tested checks in the script.
- The 2026-08-06 entry ("Still standing … its dataset does not reproduce and its warp-depth rule fails Bagon"), 03 and
  08 (2026-08-07) are CORRECTED by this entry. Old entries are not rewritten.
- **Warp depth is still NOT adopted as the pseudo-rare rule**; see the entry above.
**Why:**
- Both fixes follow what the DATA IS (the edge layout, the map group), not what answer Bagon needed. Each fix alone
  does NOT reproduce the record (fault arms, `evidence/2026-09-29-v2step0-rare-FAULT-*.txt`).
- Verified by an independent agent (`ai-research-notes/2026-09-29-v2step0-VERIFY.md`) and re-run by the orchestrator.
**Rejected:** leaving the verdict standing. Every later reader would keep believing the warp-depth dataset is
unverifiable, when it is two lines from exact.

## 2026-09-29 — design v2 step 5 (TID/T1): trainer telemetry is ALWAYS ON and log-only; B is read only in TwoOpponents; a post-battle re-entry is skipped by a MEASURED discriminator; a control is run more than once

**Decision:**
- `[TRAINER] start/end` lines (`modules/story/trainer_identity.py` plus `story_mode._t1_start/_t1_end`), with no
  flag: the 06:7902 precedent for telemetry.
- The facts they use, as the game computes them (decomp-cited):
  - who (A, and B only when the battle type has TwoOpponents);
  - the class and the money value (the 4-byte table);
  - the last ROM-party mon's level;
  - the payout formula (DOUBLE ×2 only without TWO_OPPONENTS);
  - first fight (flag 0x500+id at start).
- `_t1_start` skips a start with 0 living enemy mons: a post-battle scene re-entering the hook. It logs the skip.
- Graded A/Bs run their control more than once (KI-112).
**Why:**
- Steps 6 and 10 (key-battle items, the healing kit) and all money work need trainer identity, and nothing read it.
- B: a stale `gTrainerBattleOpponent_B` survives into single battles (decomp; an agent's finding).
- The skip: the phantom pair was MEASURED in a smoke run. `gBattleOutcome` was tried and refuted (it read `Won` at all
  6 starts); the living-enemy count separates 1-2 from 0.
- Controls: 1 of 3 identical control runs diverged at a warp.
**Rejected:**
- A feature flag: it is telemetry, per the 06:7902 precedent.
- Reading the last mon's level from `gEnemyParty`: a two-opponent battle caps each side at 3 there.
- `key=` on the line: that is step 6's decision, pending the user's Q3.
- Keying the skip on `gBattleOutcome`: refuted by measurement.
- One control run: KI-112.

## 2026-09-29 — RULING 27 / design v2 step 6 (KB): healing items only against KEY trainer classes, gated INSIDE `_maybe_use_item`, failing OPEN

**Decision:**
- `POKEBOT_R27_KEYITEMS` (default OFF): `StoryItemBattleStrategy._maybe_use_item` returns early, right after the
  Trainer-battle return, when `_r27_key_gate` refuses.
  - The key set is `trainer_identity.KEY_TRAINER_CLASSES`: LEADER, ELITE_FOUR, CHAMPION, RIVAL, MAGMA_LEADER,
    AQUA_LEADER, MAGMA_ADMIN and AQUA_ADMIN. It is a proposal pending the user's Q3.
  - The verdict is PURE and takes a list of sides.
  - It is read once per battle, logged once as `[KEYBATTLE]`, and FAILS OPEN on any unreadable side.
**Why:**
- RULING 27: *"use healing items during battles (gym leaders, story "bosses" and elite 4 only)"*.
- The gate is INSIDE the method, not in `on_battle_started`, because the harness drivers build the strategy
  themselves (59 constructions). A hook-level gate would leave them ungated, and the key arms would pass vacuously.
- The flag is tested first, so OFF does zero reads (gate I2).
- It is an early return, because gate #59 pins the policy block's exact indentation.
- It fails OPEN, because a reader bug must never cost a Juan or an Elite Four fight its items (A-RAISE: the item
  still fires).
**Rejected:**
- A gate in `on_battle_started`: the harness drivers would be ungated.
- Failing closed on an unreadable opponent.
- Judging only side A in the verdict: a two-opponent battle has two sides. None reaches this method today (doubles),
  but step 13 will.
- A `key=` field on the always-on `[TRAINER]` line: the classification is a pending policy, and it lives only on the
  flag-ON `[KEYBATTLE]` line.

## 2026-09-29 — design v2 step 7 (RP): what "rare" is, pinned in data (`#26-organiccatch`)

**Decision:**
- `modules/rarity.py` over a GENERATED `modules/data/emerald_rarity.json`:
  - RARE = legendary OR special (Feebas) OR rate (the best per-table SUMMED rate ≤ 4%) OR pseudo OR variant.
  - The variant is the minority gender, when best rate × P(minority) ≤ 4%.
- **Pseudo** = exactly 1 MAPSEC AND ≥ 2 gates on the EASIEST home. A gate is an HM or a rod needed to reach the
  encounter FROM THE STORY PATH (Q6's proposal). Members: **Bagon** `{surf, waterfall}` and **Snorunt**
  `{strength, surf}`.
- **Tier:** ULTRA with the variant or the shiny reason, otherwise RARE.
- **Shape:** a verdict carries a `note` (`no_data`, `no_species`, `adapter_error`), and species index 0 is guarded.
- **Data source:** the generator reads the ROM statically; it no longer reads the runtime cache.
**Why:**
- The user's words for pseudo-rare are field-move gating plus one location (03 `#24-rarepredicate`, the quote "For the Bagon instance …").
- Q6 is the text the user will be shown, and its "off the story path" beats the design's looser "LOCAL".
- Min over rows follows from "a species is only as gated as its easiest home": Solrock shares Bagon's room but also
  lives gate-free in 1F_1R.
- MAPSEC is counted by ID because UNDERWATER_124/126 share a NAME.
- Shiny is ULTRA because the ULTRA tier means "every encounter, even if owned", and the shiny branch already does
  exactly that.
- The ROM read replaces the cache because the cache is gitignored and holds a dead Altering Cave table (KI-113).
- Snorunt: production `calculate_path` shows the Lower Room boulder seals the Ice Room, and Route 125 needs Surf from
  Mossdeep.
**Rejected:**
- Warp depth as the pseudo axis. It stays a diagnostic column.
- Counting bikes as gates. The user named HMs and a rod; bikes would add Safari species on unmeasured tiles.
- Max or union over rows (it makes Solrock pseudo).
- Keying by the internal index (Skitty 300 is internal 315).
- Believing the verifier's flood as the citation after its pre-registered control failed (R3). It is supporting
  evidence only.

## 2026-09-29 — RULING 25 / design v2 step 8 (RC): the cap of 3 and the rare exemption, through two pure helpers, asking about `encounter.pokemon` (`#26-organiccatch`)

**Decision:**
- `POKEBOT_R25_CAP` gives an ordinary species 3 attempts per run. `POKEBOT_R25_RARE` exempts a RARE target from the
  attempt cap and the expected-throws refusal. Both are DEFAULT OFF and read per run.
- The inputs come from two module-level PURE helpers:
  - `r25_rarity_verdict(rare_on, rarity_fn, pokemon)` returns None when off (no read); a raising reader gives a
    not-rare verdict with a note.
  - `r25_catch_inputs(cap_on, verdict)` returns the two fence inputs.
  - They are passed to `decide_dex_catch` unchanged via `**`.
- The adapter asks about `getattr(encounter, "pokemon", None)`.
- The 10-ball reserve and every other gate are untouched.
**Why:**
- RULING 25: *"a cap of 3; a wanted rare species is never given up on"*.
- The helpers are split (the spec had one) so that the verdict is computed ONCE, and its note can be logged on
  `[DEXFENCE]`, `[DEXCATCH]` and `[CATCH] start` without a second call site that could diverge.
- The `.pokemon` wiring: the recon ran the spec's `rarity_fn(enc)` shape, and the EncounterInfo reads not-rare
  silently. Live arm F shows exactly that.
- The OFF cap is the constant `DEX_CATCH_MAX_ATTEMPTS`, so OFF cannot drift from the fence's own default.
- The reserve is not lifted, because Q8 is open and the record keeps the reserve separate for the mandatory hunts
  (06:4881).
**Rejected:**
- The spec's single helper taking the encounter.
- A literal 2 for the OFF cap.
- Logging the verdict by recomputing it in `_dex_catch_commit`.
- Changing `_r20_catch_start`'s signature (a gate stub pins it).
- A pure-only proof: a ~15-line harness lever made the live A/B possible.
**Accepted consequence (recorded; diagnosed, not re-litigated):** a trapped rare target can re-enter the
throw-into-reserve path more often than the old cap of 2 allowed (the graded note).

## 2026-09-29 — RULING 25 / design v2 step 8 (RC), after the review: the accepted consequences are WIDER than first recorded (`#26-organiccatch`)

**Decision (a record, not a change):** the step 8 entry above named one consequence. The review showed that the old
cap of 2 was the only per-species, per-run bound in more places. These are recorded in the same "diagnosed, not
re-litigated" way:
- CAP alone takes an ORDINARY trapper (Trapinch) from 2 to 3 trapped, throw-into-reserve entries.
- Faint-bail attempts spend no ball. With `POKEBOT_R24_CATCHHURT` also on, nothing but the encounter itself bounds
  them for a rare target.
- With `POKEBOT_R24_OVERSURVIVAL`, a rare species on a 3+-defeat map becomes a catch battle on every encounter
  instead of a flee.
- Telemetry: with RARE on, `[DEXFENCE]` dedups later exempted admissions; count them from `[DEXCATCH] attempt`.
**Why:** RULING 25 ("never given up on") and RULING 24 (catch whiteouts accepted) cover all of them. None loops
without a fresh encounter. Step 14 measures their frequency.
**Rejected:** a per-species rare cap (it contradicts RULING 25), and changing the `[DEXFENCE]` dedup key (it is pinned
by `probe_dexcatch_rate` R6, and `[DEXCATCH]` already carries the verdict).

## 2026-09-29 — RULINGS 23 + 26 / design v2 step 9a (BB): the ball top-off rides the heal, Rustboro first, with bounded defaults (`#26-organiccatch`)

**Decision:**
- `POKEBOT_R23_BALLRESTOCK` (default OFF; `observe`; `1`): after a Pokémon Center heal in a whitelisted city (9a:
  Rustboro), the bot walks to the mart and buys the best UNCONDITIONAL ball sold when spare ≤ 20. It buys up to 30
  spare, at most ₽6,000 and half of (money − floor) per visit. The floor is `CASH_FLOOR`, plus 2 × the missing League
  basket in the reserve era.
- **Bounded defaults, shown to the user as Q1** (every number is imported, never copied):
  - TRIGGER = reserve 10 + max throws 10;
  - TARGET = `MAX_BALLS_PER_TRIP`;
  - BATCH_CAP = ₽6,000.
- The piggyback is three small hunks at the END of the upstream-derived `heal_in_pokemon_center`. All logic is in the
  new `modules/story/stock_topoff.py`.
- Step 9 is split: 9a (this) and 9b (the Sootopolis basket consumer).
**Why:**
- RULING 23: "bounded batches, topped off periodically the way healing items are; the best ball the current shop
  sells". RULING 26: maintained all game.
- The heal piggyback is where the bot already stands in a city ("piggyback, do not detour").
- Half of (money − floor) per visit: a visit spends at most half of what is spendable, so repeated visits approach the
  floor geometrically instead of hitting it. (Corrected in review: it does NOT keep the floor through a whiteout, which
  halves ALL the money, and heals are free; the floor protects later mandatory purchases such as the League basket.)
- Rustboro first: its mart sells Poké Balls from the start, and the M0 trajectory reaches a post-badge-1 heal there.
**Rejected:**
- An unconditional second stable wait (it changes every OFF heal).
- A `bot_mode == "Story"` test (it misses the ENDLESS lanes and matches every harness driver).
- The spec's round-down to 10 (it loses balls and gains no Premier).
- A lazily-created memo (it leaks across ENDLESS runs).
- A stage that falls back to MID on an unreadable flag (it drops the basket floor).
- Buying Poké Balls with `buy_poke_balls` (a separate, unverified path; the errand buys only through `buy_in_shop`).

## 2026-09-29 — Design v2 step 9b (BB consumer b, Sootopolis): how the ball top-off rides RULING 18's visit (`#26-organiccatch`)

- **The forecast plans from the POST-basket wallet and floor.**
  - The go/no-go decision is made before any walk, when the basket is not yet bought. So the forecast models the
    moment after it: the wallet minus the plan's cost, and the floor from the basket still missing once the plan is in
    the bag.
  - The counter re-plans from the live state after the basket. A short basket purchase then raises the floor by
    itself.
  - Rejected:
    - the pre-basket wallet (step 0: 5 Ultras against the right 1);
    - the pre-basket floor (0: 1,000 + 2 × 54,300 is above any wallet here);
    - buying the balls in the SAME `buy_in_shop` call as the basket, which would plan them before the basket's
      delta is verified.
- **Two `buy_in_shop` calls in one menu session.** The first ends on the shop's main menu, and the basket block's
  1,800-frame wait presses nothing. The ball phase therefore buys from the same open menu, with no new walk. It fails
  safe: a missing `Task_ShopMenu` raises, and the raise is swallowed.
- **The ball phase never raises and writes only under `report["balls"]`.** RULING 18's report keys drive its walk back
  and its grade; step 9a's errand pattern writes `returned` and `bought`, and a truthy `returned` there would skip the
  walk back (recon F3).
- **A memo hit or a failed forecast BLOCKS the counter phase too**, not just the ball-only walk (recon F8). A
  Sootopolis failure is not retried in the same run.
- **The latent RULING 18 stranding (recon F1) is fixed inside this item.** It is a two-line archive at the top of
  `stock_basket_early`, and step 9b's periodic visits are what make it reachable. So it could not wait for a
  separate item without shipping a known path to a stranded bot behind the new flag.
  - Rejected: a fresh dict in the caller (`heal_and_stock_before_the_gym`). It fixes one caller only.
- **Deferred, named:** v2's split visit order ("basket, then balls while spare ≤ 10, then the kit, then the rest of the
  balls"; recon F13) needs the kit, which is step 10. Step 9b fills to the target in one phase.
- **Finding for Q1 and step 14, not a defect:** under RULING 18's floor (1,000 + 2 × the missing League basket, i.e.
  ₽19,000 in the Juan era), the Sootopolis visit buys 1 Ultra once, and a Juan loss halves the wallet below the floor.
  The periodic top-off at Sootopolis is therefore mostly theoretical until the League.

## 2026-09-29 — Design v2 step 9b review: where the driver's ball grade lives (`#26-organiccatch`)

- **The earlybasket driver's ball grade moved into `tools/story-dev/ball_grade.py`**, a pure module the gate
  executes (the review's G4: it had been pinned by text, and a hollowed check passed).
  - Rejected: a function in `stock_topoff.py`. It is test-only code, and a production module would carry it into
    `custom-pokebot` drift at promotion.
  - Rejected: executing the driver class in the gate. `story_harness.py` parses arguments and boots an emulator at
    import.
- **"Ball-only" is decided from the caller's basket plan, before the live stock filter**, not from the forecast's
  `walk` (BB9B-1). A basket visit's own failure mode (a Mart that sells none of the basket) must keep its named raise
  whatever the ball forecast says.
- **A ball-only visit that finds nothing to buy is memoised** (BB9B-2), like a failure: the forecast and the counter
  disagreed, and re-walking the crater on every Juan attempt cannot fix that.

## 2026-09-29 — Design v2 step 10 (HK, the healing-kit top-off): the spec as it will be built (`#26-organiccatch`)

**Context.**
- A five-angle recon (code audit, decomp, battle policy, fixtures, adversarial) found v2's step 10 body unbuildable
  as written: the step 9 errand cannot carry non-ball lines, and the Rustboro arm had no discriminator.
- The spec that replaces it is `ai-research-notes/2026-09-29-kittopoff-SPEC.md` (D1-D12). The load-bearing facts were
  re-read by the author: the decomp mart lists, `items.json` prices, `battle_items.py`, the key-item gate, and the
  Items pocket at the Rustboro heal (`heal_stock=-` on the first battle after it).

**Decisions:**
- **The kit's own flag, `POKEBOT_R26_KITTOPOFF`, coupled IN CODE to `POKEBOT_R27_KEYITEMS`.** Kit `1` without
  key-item mode is a named skip: ordinary trainers would otherwise drain the kit and force re-buys. v2 had this only as
  prose, and rule 6 says prose that guards is a gate waiting to be written.
- **HP tiers:** Potion < Super Potion < Hyper Potion, topped up to 4.
  - "Held" counts the tier and every higher tier.
  - **Max Potion is excluded.** It costs 2.1× a Hyper Potion for at most 55 more HP, and the battle policy spends it
    first on any Pokémon under 200 max HP. `#24-provisions`' ladder omits it too.
  - This is an INTERPRETATION, stated to the user and reversible.
- **Status:** Full Heal ×2 where sold; otherwise Awakening ×1 AND Ice Heal ×1 where sold. The policy cures only Sleep
  and Freeze, specific cure first. Never Revive, Antidote, Parlyz Heal or Burn Heal.
- **"Held" is the raw bag minus `reserved_quantities()`** (stage-dependent), not a constant basket subtraction. The
  constant reading would re-buy the basket's lines at a future mid-game Mart where nothing is reserved.
- **One budget per visit** (min(₽6,000, half the spendable), computed once and debited by every phase), so 06:8394's
  "at most half of what is spendable" holds for balls and kit together.
- **Order with the kit ON** (v2's, stated as an INTERPRETATION of RULING 26's "more heavily on balls post Elite 4"):
  1. balls up to the reserve + 1 (11);
  2. the kit's HP line;
  3. the kit's status line;
  4. the rest of the balls.
  - Ball quantities from the two ball phases are bought as ONE line set, so a total ≥ 10 still earns its Premier.
  - With the kit OFF or skipped, 9a/9b are unchanged: this is a regression arm.
  - Consequence, stated to the user: at Sootopolis the kit takes the budget first, so 1 Hyper Potion instead of
    step 9b's 1 Ultra.
- **Separate memo keys for the kit** (`<city>:kit`). A kit-only shortfall blocks only the kit; a failed walk blocks
  both.
- **No kit before gym 1**, like balls: the named build gap v2 already records, not a policy.

**Rejected:**
- appending kit lines to the ball lines (the single-ball verification would read "short" and memoise the city);
- the kit sharing what the balls leave (vacuous: ₽70 at Rustboro, ₽383 at Sootopolis);
- per-phase half-budgets (a visit could spend about 87.5% of the spendable);
- a constant basket subtraction.

## 2026-09-29 — Design v2 step 10a (HK at Rustboro) as built, and its review: how each set is logged, and where the kit is planned (`#26-organiccatch`)

**Context.** The spec (the entry above) was built as 10a, graded 20/20 live (`ai-research-notes/2026-09-29-kittopoff10a-GRADED.md`) and reviewed by three lenses. The review found that a one-sided shortfall logged the set that had succeeded as failed (R1), and that a kit-only raise under `observe` cancelled 9a's balls (R2).

**Decisions:**
- **Each set is logged by its OWN verdict.**
  - `_walk_buy_return` logs the success line of every set it verified in full, even when the other set fell short.
  - The errand logs as failed only the set that failed; a walk failure means both.
  - The fallback reason separates "not back on the exit tile" (the walk finished) from "the errand's frame bound
    expired" (it did not).
  - Recovery is logged under the prefix of a set that failed.
  - With the kit OFF this is 9a's output exactly: there `balls_ok` IS `ok`.
- **The kit is planned in its own try, after the ball plan.** A kit-only raise memoises only `<city>:kit`, logs one
  `kit-failed`, and leaves 9a's ball plan standing. A SHARED planning raise (`_inputs`) still blocks both. This makes
  D6's "observe buys exactly the kit-OFF purchase" true under a fault, not only on the happy path.
- **A planning failure memoises the ball key only when the balls are on.** With the kit OFF they always are, so 9a
  is unchanged. With the balls OFF, a ball key would block nothing, and it made the errand differ from 9a in a state 9a
  never reaches.
- **Verification is against the PLANNED lines; purchase is of the FILTERED lines.** A set the live list drops is a
  shortfall of that set (from the first adversarial pass).
- **The `[KIT-BUY]` line form is as built:** `kit=[…] bought={…} money=a->b [wants=[…]] reason=`, plus
  `kit-recovery`. D8's `hp=`/`status=` form was never built, and the predictions pinned the built form first. The
  spec now carries an AS-BUILT note, so 10b's grader is written from the real form.
- **Kept, NOT changed:** a kit-only visit whose live list sells none of the plan is a WALK failure that blocks both
  keys. The review's verifier refuted the finding against it: unreachable at Rustboro (its live list is its static
  list), and the comment at the memo says so.
- **"Kit OFF is 9a" is proven by a DIFFERENTIAL, not by rows alone.** The previous commit's module
  (`git show 61c6759e:…`) and the new one are exec'd side by side over 16,128 (state, kit-mode) pairs; 0 differ. The
  review's spec lens built it, and it found R2 (252 differences) where every row and every live arm saw nothing.

**Rejected:**
- keeping one shared try with a narrower except (a kit raise would still abandon 9a's plan mid-block);
- logging a one-sided shortfall as "both failed" (it contradicts the memo, which blocks one key);
- amending the code to D8's `hp=`/`status=` form (the built form was pre-registered, graded byte-exact, and has no
  consumer yet; changing it would invalidate evidence for no reader).

## 2026-09-30 — Design v2 step 10b (HK at Sootopolis) as built, and its review: the kit separated from the basket by TIME, the driver's lever rule completed, each set's line carrying only its own money (`#26-organiccatch`)

The design is `ai-research-notes/2026-09-29-kittopoff10b-DESIGN.md` (E1-E11, after a recon and an adversarial review).
The graded note is `ai-research-notes/2026-09-30-kittopoff10b-GRADED.md`, with its REVIEW section.

**As built (`ea75fe1f`):**
- **The kit rides RULING 18's League-basket visit at Sootopolis, bought AFTER the basket's lines, with its own
  `before`.** The kit and the basket buy the SAME names (Hyper Potion, Full Heal), and the basket verifies by a
  per-name delta. TIME is therefore the only separation that verification cannot see. Rejected: one merged purchase
  (the spec's D11-D12), where the basket would have counted the kit as its own.
- **9b's ball forecast is never overwritten.** The D6 split lives in `report["kit"]["split_balls"]`, and the
  effective ball walk is that split whenever the kit buys. Rejected: rebinding 9b's forecast. The design review showed
  it would INVERT the driver's check: the right build would fail and a build without it would pass.
- **`TOPOFF_ONLY_OUTCOMES` is exported by `league_reserve` and imported by production and the driver**, never copied.
- **The driver models every lever whose production response is defined**: the D2 skip, RESERVE_FAULT_RAISE,
  FAULT_FLOOR, NOBUY and, after the review, BALLRAISE. It never models RAWBAG, so S-RAW and S-RAWVAC fail by design,
  on sets pre-registered in the predictions.
- **The memo is made observable** (`self._ball_topoff_failed = set()` in the driver), because every memo write in
  that driver had been a silent no-op.

**The review's decisions (three lenses, each finding put to a refuter):**
- **DC1 (the driver).**
  - BALLRAISE is modelled: `R["kit_ballraise"]` means the kit walks and buys nothing.
  - `ballfail` is kit-aware:
    - its premise admits a kit-only walk;
    - its outcome label is the driver's `topoff_label` (the effective walks);
    - it asserts `kit_phase_failed` and `both_keys_memoised`.
  - `kit_as_forecast` is graded for every EXPECT except `budget`, appended after `common`, so every other arm's
    conjunct order is unchanged.
  - Rejected: keeping it in `common` and modelling the close, because where a close lands in the visit decides what
    was bought, so no single expectation is right.
  - Rejected: dropping it from `ballfail`, because with the lever modelled, "no kit bought" is exactly E5's response
    and worth asserting.
- **DC2 (production).**
  - A set that planned no line reads the wallet UNCHANGED on its line and in its report (9b's `topoff-none` X->X).
  - A set that bought reads the wallet after the ONE call, as 10a's combined line does.
  - Rejected: dropping the no-ball line, as E5's sentence said. P5/P1 had pre-registered the line, and 9b's log
    readers know `topoff-none`; E5 was amended instead.
  - Rejected: pricing each set's own cost into its line. It would be a computed number in a line of measured reads.
- **LI-2 (production).**
  - The kit is "wasted" only when its live wants are empty or the visit bought nothing.
  - Rejected: re-planning at the forecast's spare just to decide the memo.
  - Rejected: the rule as designed. After a spare drop en route, it blocked a legitimate kit for the rest of the run.
  - The loop bound still holds. A walk that buys the reserve balls raises the spare, so the next forecast re-plans. A
    walk that buys nothing is still memoised.
- **The gate's stub carries production's whole forecast dict (`FORECAST_KEYS`) and a floor that follows the bag.** A
  stub that cannot express a divergence cannot test for one.
- **Not taken:** a live arm that buys balls and kit in one call at Sootopolis. Neither fixture reaches a non-empty
  split next to a kit, because the kit's full want costs the whole ₽6,000 cap. The call is proven live at Rustboro
  (10a K-ON) and by gate row P4 here.

## 2026-09-30 — Design v2 step 11 (M1, damage-calculator fidelity) as built and graded: raw reads in production, every verdict offline, the faint rule, and how a diverged trajectory is graded (`#26-organiccatch`)

The design's F1-F10 (`ai-research-notes/2026-09-30-dmgcalc11-DESIGN.md`) are its decisions; this entry records the
choices made while BUILDING and GRADING it (the design's AS BUILT section, and `…-GRADED.md`).

- **Production logs RAW reads only; every verdict is offline and pure** (`audit_damage_calc.py`, gated by
  `probe_dmgaudit.py`). A classifier bug then costs a re-audit, never a re-run. The committed raw log
  (`evidence/…-M1B-ON-r1-debug.txt`) re-audits byte for byte.
  - Rejected: verdicts computed in the battle loop, which put judgement code in the every-battle path.
- **`base=` is logged beside `pred=`.** It is the calculator's own base term, plain and crit. It lets the audit replay
  the decomp-ordered port from the LIVE base, which makes SR-7's independent control a live check.
  - Rejected: controlling only against the calculator's own output. That is circular.
- **The FAINT RULE** (found by the live smoke). When the foe fainted, no per-mon foe comparison runs on the AFTER
  record, because the game resets it; the pair keys on the foe's chosen move.
  - Rejected: excluding KO pairs, which throws away the evidence B4 keeps and step 12 needs.
  - Rejected: reading the fainted foe's record from somewhere else. The reset is the game's own behaviour, and there
    is no second copy to read.
- **An absent left battler (a fainted slot in a double) logs `pred=err:Absent`**, never an exception name. Doubles
  are outside the acceptance anyway.
- **M1b-DIFF was built as AST equality with the hooks removed, plus 0 reads and 0 logs with the flag unset, plus 0
  `get_battle_state()` calls with it set.** That covers every path, not one driven path.
  - Rejected: only the filed form, identical yields through `repro_ki46`'s fake readers (that repro still passes in
    the suite).
  - M1b-EXEC is met by the exact CTL/BEFORE/AFTER sequence: each hook's `except` logs an `ERR` line, never silently.
- **When the live trajectory leaves the one the table was taken from,** the filed rule ("graded only on a reproducing
  trajectory") is applied as written: reached rows are graded, unreached rows are NOT REACHED (never PASS), and
  unregistered rows are reported.
  - The divergence is attributed only by an A/B filed BEFORE it runs: the base code's modules loaded in place of the
    build's in the SAME worktree (scratch `run_base_off.py`, now the tool `run_with_base_modules.py`), because a
    checkout or another worktree changes the untracked
    profile and caches too.
  - Rejected: re-deriving the table from the build's trajectory after the fact. That would be grading against a
    prediction written after the result.
- **The M1a gate keeps its no-pool fallback (~295 s) as a KNOWN LIMIT.** The pool works on this machine.
  - Rejected: trimming rows to get under 300 s. The rows are the ones the adversarial pass showed were needed.
- **`ACCEPT_MARGIN = 3` stays a PROPOSAL for the user, and step 12's stage 2 stays OFF** (F8). 8 samples cannot decide
  it. The verdict on the calculator needs step 14's batch with the flag on in both arms.

## 2026-09-30 — Design v2 step 11's review: which classifier exclusions to tighten, and which to RELAX (`#26-organiccatch`)

- **Tightened** (each could admit a sample the calculator is not comparable on, or hide an over):
  - the FOE's Marvel Scale with EITHER battler statused (ours never counts);
  - `foe-called-move` (Metronome, Mirror Move, Assist, Sleep Talk, Nature Power);
  - SECRET_POWER moved to Tier B;
  - `our-flash-fire-unobservable` at a battle-end read;
  - `ability-not-species`;
  - `our-burn-changed`;
  - Skull Bash as a foe self-state move;
  - False Swipe's band to crit_max + margin + 1;
  - Future Sight out of the self-check.
- **RELAXED, only after the decomp confirmed it** (F9a, pret/pokeemerald @ f90719c4): Tier B's faint and AFTER-status
  exclusions now apply only to a CONFUSING secondary (CONFUSE_HIT, SECRET_POWER).
  - A burn or poison tick runs in `DoBattlerEndTurnEffects` under HITMARKER_IGNORE_BIDE (battle_util.c:1464, re-entered
    per effect), and `Cmd_datahpupdate` skips the bide record under that flag (battle_script_commands.c:1905-1907). So
    Ember or Poison Sting can never move Δbide.
  - Rejected: keeping every Tier B exclusion. It drained samples for nothing, for example every Torchic-line Ember KO.
- **Superpower's -1 Atk and Overheat's -2 SpA no longer exclude,** but only when the change is EXACTLY that self-drop.
  Any other change still excludes, so a foe's Growl first is caught.
- **`ability-not-species` skips a fainted (HP 0) record.**
  - A faint resets the ability byte. On the graded log, all 20 mismatches were such records, including our own fainted
    Swellow.
  - Rejected: comparing every record. That would exclude every battle in which we fainted after our hit.
  - Unloadable species data fails the INSTRUMENT (exit 3). It is never a silent skip.
- **Nature Power joins `foe-called-move`** although in Gen 3 it calls only plain moves. Excluding a rare turn costs
  nothing, and unknown is the safe reading.
- **The status docs were held back while the reviewers read them.** That produced the grade lens's F1; the prevention
  rule is in `08`.

## 2026-09-30 — Design v2 step 12 (W, weaken-to-catch, RULING 25) as built: a BINARY no-self-harm rule, gain counted in BALLS, the kind read from the mode, a test lever, and the builder's gap decisions ruled (`#26-organiccatch`)

The design's D1-D15 (`ai-research-notes/2026-09-30-weaken12-DESIGN.md`) are the decisions; this entry records those
that were contested, and the rulings on the gaps the builder had to fill.

- **No-self-harm is BINARY, not a numeric floor.** Damage is admissible only if the target can hurt itself in NO way
  for the rest of the battle; then the only bound is the hit itself (hp − X ≥ 1).
  - Rejected: v2's per-turn hazard floor. The hazards repeat on every throw turn.
  - Rejected: a floor summed over the horizon. It is sound, but needs every hazard's per-turn cost.
- **E_gain counts expected BALLS saved:** E(hp) − E(hp − X) ≥ 1.0.
  - Rejected: the netted form E(hp) − (1 + E(hp − X)). Computed on the arm's own target, it rejected Seismic Toss
    against a full-HP Taillow (0.97).
  - RULING 25 constrains balls, and the damage turn spends none.
- **The kind comes from the mode's `_catch_ctx`, checked against the opponent's species at the first decision; the
  target is identified by PID.** Rejected: a constructor argument. It would rewrite three construction lines that four
  gates pin.
- **THROW is the parent's own ball** (`_get_best_poke_ball`, never the Master Ball), and a DEFER is the parent's whole
  turn.
- **A TEST lever (`--set-lead-move`) makes stage 1 live.** No pinned party lead holds a stage-1 move.
  - It is a state write, read back and asserted, and applied in BOTH arms.
  - Dragon Rage (40) was chosen by computation so that the KO bound BINDS; a fault arm that removes only the bound
    produced the KO.
- **Stage 2 is built and OFF.** Its observe verdicts were measured live (all THROW on the fixture). Its release waits
  on M1b's acceptance.
- **The builder's gap decisions, RULED ACCEPTED** (the adversarial pass judged each for safety):
  - the damage and status caps each block only their own branch;
  - "no progress" = an acting turn after which, at a later turn, the target's HP is not lower and it has no new status;
    two such turns ⇒ THROW-ONLY;
  - the battle-type DEFER covers every flag except IS_MASTER and RECORDED_IS_MASTER;
  - stage 2's divergence exclusions are the broader (conservative) forms;
  - among admissible moves, the largest guaranteed damage wins, and a tie goes to the lowest slot.
  - Each rule only ever adds a THROW or a DEFER, or chooses among moves that already cleared the bound.
- **After the gate's adversarial pass: five production fixes**, each with a row red on the old code:
  - PD1: a Trace member copying the target's ability; a real KO path;
  - PD2: Pain Split;
  - PD3: confusion berries;
  - PD4: a Sand Stream member;
  - PD5: RECHARGE moves are out of stage 2, and the horizon slack is 8.
  - Rejected: leaving the latent ones (PD2-PD4) for later. Each is one line, and each closes a KO path.
- **The Encore reader bug (KI-114) was filed, not fixed.** It is a shared, upstream path with no caller; the module
  reads the raw offset itself.

## 2026-09-30 — Design v2 step 12's BUILD REVIEW: its rulings, and a correction to the entry above (`#26-organiccatch`)

- **CORRECTION (review F5): the entry above over-justified one gap ruling.** It said "Each rule only ever adds a THROW
  or a DEFER". That is false for the per-branch caps: a spent damage cap still permits the status branch. One battle
  can therefore see one damage turn AND up to three status tries, where one reading of the design would have made it
  THROW-ONLY.
  - The ruling stands, on a different reason: a status move cannot KO, and any later damage is still held by
    hp − X ≥ 1 and the 50% rule.
  - 01 now says "one damage turn and up to three status tries per battle".
- **The Struggle horizon bounds the THROW phase only; the residual is RECORDED, not fixed** (review W12-S1).
  - A trapped Run costs no turn, and ordinary failed flees are unbounded (the u8 speedVar wrap). So after a catch is
    ABANDONED (out of balls, or the dex reserve/faint bail), a PP-exhausted target could Struggle into its own recoil.
  - Rejected: a finite slack. None covers unbounded flees.
  - Rejected: refusing damage whenever an abandonment is possible. That is every battle, since balls run out.
  - The KO risk exists only after the bot has given the catch up.
  - A future grader of an acting arm must separate a `res=Won` whose `[CATCH] end` carries a bail or out-of-balls mark
    from a weaken KO. `_r20_catch_end` already records that mark.
  - No acting arm here had any `res=Won` without a fault.
- **DAMAGE honours `banned_moves`** (review W12-N1). A move the user banned is never chosen, whether to damage or to
  put the target to sleep.
- **COVERAGE stays the weak form** (review F10; the adversarial pass's suggestion). Instead, each vacuous row names the
  row that isolates its rule.
  - The strong form needs a map from every rule to its rows, which the gate does not carry.
- **Seeds 2-3 (v2's L0) were DROPPED for the seed-1 arms plus a test lever** (review F6).
  - Stage 1 is vacuous on every pinned party, so more observe-only seeds show inertness again and nothing more.
  - The lever arms show the ACTING path, which L0 could not.

## 2026-09-30 — Design v2 step 13 (KB-2, items in DOUBLE battles): the design's rulings, and their rejected alternatives (`#26-organiccatch`)

Design: `ai-research-notes/2026-09-30-doubleitems13-DESIGN.md` (reviewed by three lenses, each finding put to a
refuter: `2026-09-30-doubleitems13-recon/d13_design_review.md`). The author's calls, recorded so they are not re-asked;
the user may overturn any of them.
- **D1. The Space Center multi is OUT of v1** (`super()` there). The bot controls battler 0 only, Steven's Pokémon sit in
  the party array, and it is measured low-value (0 losses of 16, 2 of 24, 4 of 56 in three batches). Rejected: including
  it now; its party layout and ownership need their own design.
- **D2. Self-only: each battler heals only its own active Pokémon.** Rejected: partner heals in v1. They need a
  cross-battler identity binding and reopen the stale-HP hazard (battler 2 decides on the state read before battler
  0's item).
- **D6. `POKEBOT_R27_DOUBLEITEMS` and `POKEBOT_R27_KEYITEMS` are ORTHOGONAL.** Doubles follow the singles item policy,
  including whatever KEYITEMS decides. Rejected: DOUBLEITEMS requiring KEYITEMS (the kit's D2 rule), because a flag
  whose meaning depends on another composes less safely. ⚠ With KEYITEMS unset, DOUBLEITEMS alone uses items in every
  trainer double (~856 per batch), as singles do today; step 14 runs both ON.
- **D7. The battler-aware action cursor (C1) is UNCONDITIONAL**, not behind the flag. It is a correctness fix of a
  latent upstream defect that never fired (0 of 4,520 batch logs), and it is inert with the flag unset because both
  cursor bytes stay 0. Rejected: gating it, which would leave the flag-unset build carrying a defect that any future
  double-battle item or switch would trip. It needs a `DIVERGENCE-LOG` entry when promoted.
- **D10. HP items only in doubles (v1).** Rejected: status cures in v1, because a guard refusal on a parameter-0 cure is
  not counted by the retry/disable logic (only the 4-use cap bounds it; review S13-P2). Tate & Liza's Hypnosis makes a
  cure reachable, so this is a real, recorded limit.
- **D11. The Struggle loop stops at battler 2's menu, behind the flag** (review S13-P1, upheld): with the flag unset the
  blind FIGHT for battler 2 stays byte for byte; with it set, battler 2 makes its own decision.
- **Dropped before any code:** the `--set-party-hp` and `--set-bag-item` levers. Step 0 showed both natural trajectories
  discriminate (Route 123's first double from turn 0; Tate & Liza from turn 1 after the faint replacement).

## 2026-09-30 — Design v2 step 13 BUILT and FOLDED: the builder's gap rulings, and the adversarial pass's (`#26-organiccatch`)

The design left these to the builder; the author accepts them, recorded so they are not re-asked:
- **NOGUARD skips only the PID comparison**; the range check and the self binding still hold, so `ok` is logged
  truthfully as 0 while `a_pressed=1` (P-NOG isolates exactly what the PID check prevents).
- **A failed self binding refuses at the party menu** (`self=0 ok=0`), not before the bag opens: one refusal path.
- **The guard also requires the PARTY_MENU state** when it reads: a stale `slotId` could otherwise match the intended
  PID in field order and send A into the bag.
- **The ledger key is (PID, species index)**, the `faint_chooser` identity convention.
- **Observe's `key=`** is `key_battle_verdict(True, …)` (1 key, 0 none key, ? unreadable); its `would=` applies
  `KEYITEMS` and fails open, as the acting path does.
- **Telemetry additions:** `[DBLITEM] err …` on the fail-open path; `struggle-exit` for D11; `menu … aim= self=` (both
  coordinates on one line, rule 10); `after … same=`; `bpo_pos=tailN`.
From the gate's adversarial pass (`tools/story-dev/evidence/2026-09-30-doubleitems13-ADVERSARIAL.txt`, folded in
`889b9319`, `-FOLD.txt`):
- **SF-1: a double asks NO status-cure policy.** The build's filter left a Full Restore in the cure list. Rejected:
  keeping cures with a narrower list, because D10's reason (a refused cure is not counted by the retry/disable) holds
  for any cure item.
- **SF-2's fix is FLAG-ON DOUBLES ONLY.** The measured 16-frame margin is in doubles; singles keeps its 3 × 30 loop press
  for press (one singles sample opened the bag in 43 frames). Rejected: changing the shared singles path without its
  own A/B (rule 9).
- **N2: the flag-unset path tests the env before importing anything.**
- **DQ14 is relabelled:** its refusal comes from the range check; X01 now pins the actual-slot PID read. The adversaries'
  real mutants joined the gate with their expected red sets written before their first run; the pre-registered fault
  sets did not change.
- **Not folded, recorded as residuals** (the graded note): the bag-count verdict is per item type; item names keep spaces
  in the `use` / `after` lines; a bag-did-not-open return logs no `menu` / `after` pair.

## 2026-09-30 — Design v2 step 13's BUILD REVIEW: its rulings, and step 14's arm B (`#26-organiccatch`)

The three-lens review (`tools/story-dev/evidence/2026-09-30-doubleitems13-REVIEW.txt`; every blocker/should-fix put to a
refuter) found no production defect. Rulings, recorded so they are not re-asked:
- **C1's "inert with the flag unset" is SCOPED, not withdrawn** (N2/F13): inert for Story's strategies, whose trainer
  doubles only FIGHT. Under upstream's `DefaultBattleStrategy` with the `rotate` config it changes flag-unset presses,
  turning a latent KI-45 into a working FIGHT. It stays unconditional: a fix there, not a regression. The
  `DIVERGENCE-LOG` entry at promotion must say so.
- **Observe uses a SILENT copy of the RULING 18 reserve filter** (N1): the same list, no `[RESERVE]` line, no latch.
  Rejected: qualifying the "observe changes nothing" claim instead, because a shared latch would silence a later
  singles line.
- **SF-2's after-acceptance give-up logs its own stage** (N3); the generic "will re-decide" line stays for the paths
  where it is true.
- **The graders count as-filed and corrected checks apart**, and a check that cannot fail is not a check (F5): the T3
  next-FIGHT check evaluates, and an absent observation is reported ABSENT, never PASS. The two arms evidence files were
  regenerated with the fixed grader; no run was repeated.
- **Step 14's arm B adds `POKEBOT_R27_DOUBLEITEMS=1`** to v2's list: step 13 composes with `KEYITEMS` (D6), so without
  it the batch would measure singles-only items. `#27-itemprobes` comes first: step 14's acceptance instruments match
  lines no current code prints.

## 2026-10-01 — `#27-itemprobes`: how step 14 will be measured, and the open question it leaves for the user (`#27-itemprobes`)

- **The key groups step 14 reports by are a PARTITION of `KEY_TRAINER_CLASSES`, checked at import:** leaders {LEADER},
  Elite Four {ELITE_FOUR, CHAMPION}, rivals {RIVAL}, Magma/Aqua {MAGMA_LEADER, AQUA_LEADER, MAGMA_ADMIN, AQUA_ADMIN}. A
  new key class therefore cannot silently fall outside every group. (RIVAL also covers Steven's post-game battle and
  Red/Leaf, as `trainer_identity` notes.)
- **The measurement counts a Draw as a LOSS** (the game whites out on a Draw). Production's defeat counting does not yet
  (KI-116, `#27-drawdefeat`); the two are recorded apart on purpose.
- **Kept the name `probe_item_index_space.py`** although it now measures item OUTCOMES, because design v2 §Step 14 names
  it; its docstring keeps the old question as history.
- **Did NOT de-duplicate the 2-3 identical `[TURN]` lines per decision:** that would move every filed count; the
  over-count is documented instead.
- **Open for step 14's design, and the user's call:** a CONCURRENT A/B needs per-lane flags, which `endless_x4.py` does
  not have (every lane inherits the dashboard's environment). The options are a small per-lane flag mechanism (built
  and proven like any other change) or two batches, one per arm, at twice the machine time. The probes' `--lanes` filter
  serves either.

## 2026-10-01 — design v2 step 14 (the Phase 3 batch): how the A/B is run and graded (`#26-organiccatch`, v2 step 14)

Full design: `ai-research-notes/2026-10-01-batch14-DESIGN.md` (recon and review under `…/2026-10-01-batch14-recon/`).
- **Concurrent headless lanes, arms balanced lane-for-lane, through `x4_headless.py --arms`** (recommended: 16 lanes,
  two arms × two lanes of each starter). Rejected:
  - a 2/2 split on the GUI's 4 lanes, which makes the arm the starter;
  - per-run alternation, a production change to the endless loop;
  - two GUI nights, which confounds the arm with the night (KI-112) and needs a two-night freeze. It is offered only as
    an option.

  The lane count and the window are the USER's call (the design's §7).
- **Arm B = v2's list + `POKEBOT_R27_DOUBLEITEMS=1`; `TEAM6` and `HUNTFIRST` stay OFF** in both arms. v2 names only
  OPENFENCE, and `#24-partycap` measured −36 points for that kind of change.
  **Both arms add `POKEBOT_R25_WEAKEN_CALC=1` to `observe`.** Without it the weaken-frequency data v2 wants is
  near-empty, and observe+CALC is the one sanctioned use (`29`:202).
  **Every arm lists all 18 variables explicitly**, enforced by an allowlist and a source check.
- **The acceptance metric is fixed BEFORE the data.** The first-attempt win rate over a FROZEN set K\* of seven early,
  high-reach, movable key trainers: Roxanne, Brawly, Wattson, Flannery, the Route 110 rival, Tabitha and Maxie at
  Mt. Chimney.
  - It is post-stratified by realized starter and clustered by (arm, species, starter PID).
  - The margin is δ = .08 at 16 lanes (80% power), .11 at 8.
  - Rejected: the first draft's mean over every trainer met by 5 runs per arm. Reaching a trainer is itself changed by
    the arm (truncation by death; the review's BLOCKER S1).
- **A fixed sequence, not Holm.** The manipulation check (HP items held at K\* first attempts, B > A) GATES the
  non-inferiority reading. The harm flags (C2 LOWER, C5 REGRESSION in non-key trainer battles) are read UNADJUSTED at
  one-sided .05, because adjusting them would weaken exactly the harm the batch exists to see.
- **Two v2 expectations are WITHDRAWN as tests and kept as reports.**
  - "Fewer `[DEXFENCE]` reserve refusals": the runway refusal returns first, and OPENFENCE moves encounters into the
    reserve gate.
  - "No more leg-11 money refusals": about 11 runs per arm reach it.

  The two v2 probes stay as cross-checks.
- **Stop rules are automated in the runner and their consequences are pre-registered.**
  - STOP-1 (an arm leak, including A-only refusal texts appearing in B) and STOP-2 (` rare=` and `[KEYBATTLE]` in every
    B lane within 60 min) abort the batch live.
  - STOP-3 (a new failure in B only) is manual.
  - Any STOP makes the confirmatory readings descriptive, and a restart is a new batch, never pooled.
- **The freeze:** the batch runs the main checkout, which stays dirty so its session hook never pulls. No merges and no
  Claude session there during the window. The runner aborts if HEAD or the code's porcelain moves.

## 2026-10-01 — USER RULING 28: step 14's batch — 16 lanes, two arms; start TONIGHT if the smoke run passes; Q1 and Q3 run AS BUILT (`#26-organiccatch`, v2 step 14)

Asked with the DESIGN's §7 (`ai-research-notes/2026-10-01-batch14-DESIGN.md`); the user chose the recommended option
on all three questions:
- **Lanes: "16 lanes, 2 arms"** (M-16), headless, with no dashboard window: progress is reported instead. Rejected:
  24 lanes / 3 arms, 8 lanes, and two GUI nights.
- **When: "Tonight if ready".** The tools are built and tested today. **If the 15-minute smoke run passes, the 13 h
  batch starts tonight WITHOUT asking again**, and is reported in the morning. A smoke FAILURE does not start it.
  Conditions: the PC on, no GUI batch running, and no Claude session opened in the main checkout until it ends.
- **Q1 and Q3: "Run as built".** The key set is `KEY_TRAINER_CLASSES` (leaders, the Elite Four and Champion, the rival
  and Wally, the Magma/Aqua leaders and admins; not grunts). The ball top-off is 20 → 30, at most ₽6,000 per visit. If
  the user changes either later, the affected readings are flagged as measured under the old answer.
- ⛔ This answers step 14's go-ahead ONLY. Q1-Q9 themselves stay open as questions; this ruling only lets the batch run
  the proposals.

## 2026-10-01 — design v2 step 14 T1: how the A/B runner refuses a contaminated batch (`#26-organiccatch`, v2 step 14)

- **Arms are literal and enforced at three points:** an allowlist plus a whole-token source check at the start; a
  FAIL-CLOSED `env-all:` + `build:` equality on every run header; and a live substring monitor in BOTH directions
  (B-only texts in A, A-only refusal texts in B). Rejected: trusting the launching shell, which is how both arms would
  silently get a leftover flag.
- **An arm violation aborts whatever `--on-bad-header` says.** A contaminated A/B is void, not noisy.
- **The freeze is HEAD + the scoped porcelain, strict,** and a dirty scoped tree refuses to start. Rejected: a
  tree-hash freeze that would tolerate docs commits. It is more code, and the rule is simpler: no commit, pull or
  merge in the main checkout during the window, announced by a banner and `ARMS.json`'s `do_not_touch_until`.
- **Lanes sit in a kill-on-close Windows job** (they die with x4h however x4h dies). **The night run is launched
  through WMI** (`Win32_Process.Create`, `python.exe -X utf8` directly) because this session's own processes sit in a
  kill-on-close job. Measured: a WMI-created python is in no job and its parent is `WmiPrvSE`. Rejected: a
  background task, which the session's end would kill along with the whole batch.
- **A lane lost for good makes the batch DEGRADED** (named in the verdict), never VACUITY, and `require` is checked
  only on live lanes.
- **The arms spawn interleaved** (H1, H9, H2, H10, …), so neither arm gets a head start.
- **The in-game name is paired across arms.** ⚠ This does not guarantee one seed pool per lane: P2 and P4 shared one in
  the baseline despite different names.

## 2026-10-01 — USER RULING 29: the heredoc / shell-text hook is APPROVED (`#27-shellhook`)

- **Asked:** a hook enforcing the written rule that documentation and code text never pass through a shell-quoted
  string. That rule failed FIVE times in two sessions (`08`, 2026-09-30 and 2026-10-01); all were verified harmless.
- **The user's words:** "I agree with approving the pending heredoc hook if you think it would be helpful."
- **Built as** `.claude/hooks/block_shell_text.py`, REUSING `block_destructive_git.py`'s parser (one parser, one place
  to fix). Its scope, gate and predictions: `ai-research-notes/2026-10-01-shellhook-PREDICTIONS.md`.
- **The hatch is a live `POKEBOT_ALLOW_SHELL_TEXT=1` prefix read from the COMMAND**, for an operation the user
  approved. Unlike the two older hooks' hatches (`#27-hookhatch`), this one works.
- ⛔ **It must reach `main` before 9:00 PM LA 2026-10-01** (the step-14 batch's freeze; no merge after that until the
  batch ends), or wait until then.

## 2026-10-01 — `#27-shellhook`: the hook's scope after its adversarial pass (USER RULING 29)

- **Scope widened from "heredocs" to "doc or code text written through the shell"**: in-place `sed`/`perl`/`awk`
  edits, PowerShell writers fed a literal, `git` messages, and literal pipes into writers.
  - WHY: the first build blocked heredocs only, and that would have pushed agents onto `git commit -m` with backticks,
    the exact shape that corrupted a pushed commit on 2026-09-16.
  - A seat belt that redirects habit onto a worse road is worse than none.
- **Measured, not guessed:** every widened rule was replayed over 18,484 real commands (294 transcripts). The bar was
  ZERO unexplained false positives; one is accepted by design (a `py -c` extractor writing a scratch `.md`).
- **`.txt` is never a doc/code target**, so log appends (`echo "exit=$?" >> run.txt`) stay free.
- **Rejected:** a scratch-path carve-out for `py -c` writes. Scratch `.md` files are later spliced into
  `PROJECT KNOWLEDGE`, so the carve-out would leak.

## 2026-10-01 — design v2 step 14 T2/T3: how the comparator handles what the DESIGN left to the tool (after its adversarial pass)

- **A STOP voids the confirmatory readings.** Any automated abort (ARM LEAK, VACUITY, an ARM or EMULATION header
  failure, FREEZE BROKEN, an x4h error) makes C1 and C2 "DESCRIPTIVE — VOID" (DESIGN §4). Any other FAILED verdict
  voids too (fail-closed). A user park and a lost lane do not void ("a user park stands"). `--void REASON` exists for a
  manual STOP-3.
- **K\* stays FROZEN in the code.** C2 is NOT ESTIMABLE unless all seven trainers are estimable, and so is a bootstrap
  draw. Rejected: averaging over the estimable subset, which re-derives K\* from the data and reopens S1.
- **A run cut, lost or capped DURING a first attempt is CENSORED for that trainer.** It leaves the reach and composite
  denominators and is never counted as a failure. DESIGN: a cut run "contributes only the first attempts it
  completed".
- **Only Torchic, Mudkip and Treecko form strata.** A run whose species disagrees with its `choosing` line is excluded
  and listed.
- **Overriding the seed, the draws or δ labels the grade EXPLORATORY.** δ is derived from the batch's own design:
  16 lanes × 2 arms → .08; 8 → .11.

## 2026-10-01 — design v2 step 14 T4: STOP-3 counts only ACTING package tags; E4 is a hand read, not a simulation (after its adversarial pass)

- **STOP-3's package-tag list is narrowed to ACTING tags** (DESIGN §4, amended before any batch data exists). The
  filed list (`[KIT-BUY]`, `why=topoff`, `[KEYBATTLE]`, …) matched the no-op forms its emit sites print at almost every
  B heal: `why=topoff-none`, `why=kit-skip`, `-observe`, `[KEYBATTLE] allow=True`. Nearly any B-only derail would
  have "had a package tag", so the stop could not separate a package fault from a coincidence. The acting list:
  - `[ITEM] using`;
  - `[DBLITEM]` use / menu / after;
  - `[BALLS-BUY]` or `[KIT-BUY]` whose `why=` is one of eight errand outcomes (whole token);
  - `[DEXCATCH-NOBAIL]`;
  - `[CATCH] trainee`;
  - `[KEYBATTLE] allow=False`.

  `why=mandatory` is excluded because both arms print it.
  - Rejected: keeping the broad list "to be safe". A stop that fires on nearly every B-only signature is no safety: it
    teaches the reader to dismiss it, the same failure as a noisy gate.
  - Rejected: requiring a tag in EVERY qualifying run's tail. One acting tag in any tail is still enough to park and
    look, and the tool prints how many signatures had none, so a reader sees what the narrowing left out.
- **E4's zero is read by hand, not by simulating production.** On a zero, every own battler's lowest HP fraction is
  listed. One at or below 0.35 while holding an HP item marks the battle for a hand read, with production's rule-3
  caveat (it declines a heal into a losing race).
  - Rejected: re-running `choose_healing_item` per battler. It would put a second copy of production's decision inside
    the grader, and that copy would drift from the real one.
- **E5 lists every partner rise; context never excludes.** An exclusion can only hide a wrong target, never reveal one.
- **T4 is merged before the 9:00 PM freeze, not after the batch** as its note's header planned, because it finished
  first. It changes only `tools/story-dev` and documentation, and the merge leaves `sandbox-pokebot/` byte-identical,
  so the batch runs the same code either way.

## 2026-10-01 — `#27-battleeq` (KI-108): fix `BattleState.__eq__` as the DEFAULT, with a fault switch; the evidence is a forced second caller, not an ordinary-battle A/B

- **The fix compares the party order and the turn in `__eq__`, and is ON by default.**
  `POKEBOT_KI108_FAULT_OLDEQ=1` restores upstream's 9-field compare. This is `29` §B's standing idiom ("the fix is
  always the default; the switch restores the bug"), so the user was not asked.
  - Rejected: a default-OFF opt-in flag. That shape is for new FEATURES; a bug fix uses §B.
  - Rejected: a pure read at the three acting sites. It misses every other second caller, it turns `probe_dmgaudit`'s
    NH-gbs-count red, and it leaves the class of bug in place.
  - Rejected: re-reading when `age_in_frames == 0`. That removes the per-frame cache for every reader, a different
    change that nothing measured a need for.
- **The ordinary-battle A/B that `#27-ki47range`'s deferral (2026-09-28) asked for is superseded.** Headless, every
  acting site is already the first caller in its frame, so an ordinary A/B is identical by construction: a regression
  check only. The evidence that decides is:
  - an offline gate on the real cache code;
  - KI-108's measured Run-B shape;
  - a harness first reader that reads like the GUI debug Battle tab (BE-6). It reproduced a real wrong-target item
    use under the old compare, and none under the fix.
- **`battle_move_replacing.py:149` stays with KI-115 / `#27-battlestructptr`.** The fix makes a second caller CURRENT,
  not correct. That site's mapping is itself suspect, and the fix does not change it for a first caller.
- **The merge waits for step 14's batch to end.** It changes `sandbox-pokebot/`, which the batch is frozen on. The
  batch therefore measures the UNFIXED code. Its lanes are headless, with no GUI first reader at the acting sites, so
  its confirmatory readings are not expected to move. The one known effect on its logs: `:578` can read second after
  `:116` in the same frame, so the doubles `[TURN n]` label can lag by one turn. That matters for E5's hand read.

## 2026-10-02 — design v2 step 14 graded: the registered verdict is REPORTED but not RELIED ON; the corrected re-grade is EXPLORATORY; promotion is blocked

- **Both grades are reported side by side** (`ai-research-notes/2026-10-02-batch14-GRADED.md`):
  - The frozen grader, as registered, reads C1 PASS and C2 HIGHER.
  - The same statistics with the run identity corrected read C1 PASS and C2 NOT LOWER. They are labelled EXPLORATORY,
    because the fix came after seeing the data and DESIGN §4 forbids any read changing an analysis choice.
  - The coordinator does not choose between them. Whether a repaired MISREAD (as opposed to a different analysis)
    may be confirmatory is put to the user.
  - Rejected: silently re-grading with the fix. That launders a post-hoc change into a confirmatory result.
  - Rejected: reporting HIGHER alone. The verdict exists only because 35% of the runs were dropped unevenly by a
    misread.
- **No `--void`:** nobody parked the batch, and STOP-1 and STOP-2 did not fire. STOP-3's one qualifying signature (the
  Norman wall) is diagnosed and attached to the readings as a note, which is DESIGN §4's rule for a pattern first seen
  after the batch.
- **The package is NOT recommended for promotion** while KI-118's wall stands. It is a real B-only harm in a key
  battle outside K\*, so neither C2 nor C5 measures it.
- **M1b's acceptance FAILS as pre-registered** (ACCEPT_MARGIN 3) on one sample at the known D1 bound (+4 HP). Stage 2
  stays OFF. Changing the margin is the user's call, and so is waiting for `#27-dmgcalcfix`. The coordinator did not
  change it.

## 2026-10-03 — USER RULING 31: the HYBRID direction. The story bot is parked; the Emerald AI strategy learner (`ai-agent/`) is built on top of it

- **The ruling (user, 2026-10-03).** After the step-14 review the coordinator offered three paths: keep going as-is,
  pause and start the AI version from scratch, or a hybrid. The user chose the hybrid: "Lets proceed with option 3:
  Hybrid approach." The goal is a learning agent that runs 24/7 on the user's PC and whose findings Claude improves
  from, starting 2026-10-07, when credits refresh. It lives in a separate folder of this repo so it can use the
  existing docs. The story bot is "not given up", only paused. A follow-up note: "able to launch multiple runs to
  train off of and learn from (with respect to available hardware limitations/availability)".
- **Why the hybrid.** Step 14 showed what fails now: strategy, meaning which counter, which lead, when to train,
  what to buy. Mechanics no longer fail; navigation, battles and menus are mature. Each strategic fix in the
  story-bot workflow costs a design, proof and review cycle, so a learner that tests strategies automatically
  attacks the actual failure mode at near-zero credit cost.
  - Rejected: an AI model playing live. It needs credits around the clock, beyond the user's $80 budget.
  - Rejected: training a network from pixels. It needs weeks of compute and engineering, and would relearn
    mechanics that already work.
  - Rejected: continuing as-is. Slow and expensive per gain.
- **v1 design decisions (coordinator, under this ruling):**
  - The knobs are ONLY the 11 step-14 flags whose arms differed, with ONLY the two values each ran for 13 hours.
    The other 7 arm variables are held fixed. So the learner can never send the bot an untested setting, and the
    batch runner's own preflight refuses a misspelt one (gate P1–P4).
  - Score = progress out of 13 (8 badges + 4 Elite Four + Champion). It is counted from key-trainer WINS after the
    run's first `Story: choosing` line: KI-119's identity lesson, applied from the start. A lane's last log without
    an end (Champion, or the fifth derail) is CENSORED and never scored.
    - Checked against step 14: the learner's reader reproduces the corrected grade's badge distributions for BOTH
      arms exactly, the 7 and 4 Champions, and the 62 complete runs.
  - Choice per cycle: an incumbent control, an inbox proposal, a Thompson draw, then mutants of one or two knobs.
    Knob effects come from ridge regression with the starter as a covariate. A knob confounded with another (all of
    step 14) is reported as NOT separable, never as an effect (gate E3).
  - Lanes are auto-sized in fours, one per starter for each strategy: logical threads minus 4, memory minus 8 GB,
    capped at 24. This is the user's multiple-runs authorization, kept inside the hardware.
    - Rejected: waiting for ANY other `pokebot.py`. A GUI window idle since 2026-09-27 would have blocked the learner
      forever. Now only another batch or harness drive makes it wait; an open single bot costs one thread.
  - Live output is git-ignored, and `learner.py publish` copies a small snapshot for a cloud session. Rejected:
    tracking the live files, which would leave the main checkout permanently dirty, the session-start ritual's STOP
    condition.
  - Claude consults are built but OFF by default, read-only tools only, with a daily cap. Proposals are validated
    against the knobs before they can run. Rejected: letting the 24/7 process edit code or relaunch itself. Those
    stay in interactive sessions a person can see.
- **Consequence for every session while the learner runs:** the batch runner's freeze watch aborts a cycle if
  `sandbox-pokebot/` changes mid-batch. So a `git pull` on main that touches it, or a sandbox edit, cuts the running
  cycle short. Its finished runs are still scored. Story-bot work goes in a WORKTREE.

## 2026-10-03 — The AI learner runs from its OWN deployment clone and updates itself between cycles (supersedes "never runs git" in the RULING 31 entry); its knobs are screened with a Plackett–Burman design

- **The trigger (measured, not theory):** cycle ai0002 (24 lanes, 12 hours) died 10 minutes in, with `batch exit 3`.
  The batch runner's freeze watch abandons a batch when HEAD moves, and the coordinator's docs-only commit
  `718a34c7` moved it. The watch is right to do that: it keeps a batch attributable to one commit. But it makes the
  development checkout an unsafe home for a 24/7 learner. Every commit there, from any session including the
  user's own on 2026-10-07, would kill the running cycle, and a third kill in a row pauses the learner.
- **Decision:** the learner runs from a separate FULL clone, `C:/Remote Projects/pokebot-learner`, whose origin is
  GitHub. A full clone is needed because `x4_headless.py --arms` refuses a worktree. Between cycles, and only then,
  the learner runs `git fetch` plus `git merge --ff-only origin/main` in that clone (`auto_update`). If its own code
  changed, it re-runs `test_agent.py` and restarts into the new code only on a pass.
  - Deploying a change is therefore commit + push, from anywhere, cloud sessions included.
  - A git-ignored `DEPLOYMENT` marker makes `run` and `once` refuse anywhere else (gate L6). The
    lock is per checkout, so without it two learners could run from two checkouts.
  - Rejected: teaching the freeze watch to ignore HEAD moves that leave `sandbox-pokebot/` unchanged. Lane headers
    record the build commit too, so that change spreads into header verification. It also edits a gate-pinned
    story-dev tool, and editing `x4_headless.py` is itself a freeze-scope change that would kill the running cycle.
  - Rejected: committing only at cycle boundaries. Unenforceable across sessions and machines.
  - The RULING 31 entry's "never runs git" is superseded by "only fetch plus fast-forward of its own clone,
    between cycles" (gate L5 pins the exact commands). A fast-forward cannot discard work, and the clone carries
    none.
- **Screening design (`design: pb12`, default):** after the control, each cycle runs the next rows of the
  12-genome Plackett–Burman design for the 11 knobs.
  - Every knob is ON in 6 rows and every pair ON together in 3 (gate B9; B11 proves one flipped cell fails it).
    So one pass of about 2 cycles estimates every knob's main effect. Step 14 changed all 11 together, which left
    them confounded.
  - Rejected: one-knob mutants of the incumbent. Each mutant informs one knob, so 11 knobs need about 11 arms of
    runs for what 12 PB rows give for all of them at once.
  - Interactions are aliased in a PB design. A knob that looks important gets a confirming A/B in the story-bot
    workflow before anything relies on it.
- **Raw logs are kept until the next interactive session** (`keep_raw_cycles` 12, about 4 GB a cycle; the
  `min_free_gb` guard still applies), so a better parser can re-read everything (`learner.py reparse`).
- **Consult hardening, still OFF by default:**
  - `--setting-sources user` skips the project's session-start hook, whose `git pull` would move HEAD;
  - `--max-budget-usd` is a hard per-call cap;
  - `--model sonnet`;
  - `--max-turns`, which this CLI version does not have, is removed.
  - "For the developer" notes accumulate in `findings/DEVELOPER-NOTES.md`.

## 2026-10-03 — The first WALL knob: `POKEBOT_BOSSMODE_TOPUP` (boss mode's +1 top-up becomes learnable); the screen grows to Hadamard-16; genome ids hash only changed knobs

- **Evidence:**
  - The learner's boss table: Tate & Liza were fought in 45 of 62 scored runs and beaten in 34, with 11.2 losses
    per run, and the team's average level at the first loss (33.0) was about the same as at the win (33.7).
  - The decision map, verified by the coordinator at `sandbox-pokebot/plugins/custom_modes/story_mode.py:3865`:
    after 2 or more losses, when the local wilds are fodder and the boss still loses mons, boss mode tops up only
    `team_max + 1` ("the boss battle is the trainer").
  - So the bot re-fights at the same strength until variance wins or the plateau stop (`:2230`, 12 losses) ends the
    run.
- **Decision:**
  - The top-up becomes an env knob with an UNCHANGED default:
    - unset = 1, the old behaviour exactly; integers 1-10 honoured; junk falls back to 1;
    - the pure helper is `modules/story/bossmode_topup.py`, gated by `test_agent.py` K1-K3.
  - The learner A/Bs `1` vs `4` inside its screening design.
  - The A/B itself is the measurement, which follows the playbook's split: batches answer frequency questions, and
    "does training more before a retry beat Tate & Liza more often?" is one. No driver proof is claimed or needed
    for the default path, which is byte-for-byte the old arithmetic.
- **An exception to "only values that already ran", made deliberately:** `4` never ran in step 14. It drives the
  same target-level training the non-boss retry path already runs every game (`team_max + 5`, `:3876-3890`), so it
  exercises no new machinery. A value that hurt would show up as lower scores, a safe failure the learner itself
  measures.
- **Faithful to organic gameplay:** training a few levels before re-challenging a gym that keeps beating you is what
  a human does. The knob changes how much, never the method.
- **Design:** 12 knobs no longer fit Plackett–Burman 12. The screen now picks PB12 for 11 knobs and Hadamard-16
  (Sylvester; balanced, pairwise orthogonal) for 12-15 (`design: screen`). A design change restarts the row pointer.
- **Genome ids now hash only the knobs that differ from baseline** (gate B2b), so a future knob, added at its
  default, renames nothing. Every id changed once with this commit; the records hold the genomes themselves, so
  nothing is lost.
- Rejected: shipping more wall knobs at once (the map's plateau thresholds, basket profile, box-first tier). Each
  one is a story-bot change with its own risk, and one knob with a clean default is the cheapest first test of
  the whole knob pipeline (bot → registry → learner → screen → report).

## 2026-10-03 — USER RULING 32: the AI's ultimate goal is HUMAN-LIKE, organic play, never a speedrun; the learner's progress-only score is a partial proxy

- **The ruling (user, 2026-10-03), verbatim:** "The ultimate goal for this ai agent is for it to be able to
  understand how to play pokemon emerald and play it faithfully as well as organically like a human, including
  completing the story, catching pokemon on the way, picking up items, exploring the world, training, completing
  the pokedex, etc... the goal is to make it play exactly as a human would and make sure it doesnt robotically speed
  run to the end ... the ultimate goal of this is to look and act as human as possible in the end".
- **Why it changes the learner now:** its score counts only PROGRESS (badges + Elite Four + Champion). On its own,
  that rewards whatever reaches the Champion fastest, including catching less and exploring less. The incumbent,
  baseline A, keeps the extra catch knobs OFF.
- **Decisions (coordinator, under this ruling):**
  - Record the human-like signals the logs already carry, per run: species caught (`[CATCH] end ... res=Caught`)
    and distinct places entered (`[MAP] ... -> X`). The parser is v2, and the learner re-reads every retained
    batch on its own when the parser version changes.
  - Show them beside the score in `LATEST.md`, with a "Human-like check" that flags a strategy catching under 80%
    of baseline's species or exploring under 90% of its places.
  - Put the goal first in the consult prompt: never propose progress bought by playing less like a person.
  - **NOT decided:** how the signals combine into one ranking score. What "human-like" weighs numerically
    (a species against a badge) is a value judgment for the user, and goes first in `#28-aiagent-v2` for 2026-10-07.
- **Not yet measurable from the logs:** overworld item pickups (only 6 `obtained` lines in a whole run; battle item
  use is `[ITEM-FLOW]`). A dedicated item-pickup signal is v2 work.
- **First reading:** step 14's first Champion run caught 8 species and entered 60 places in the whole game.

## 2026-10-03 — USER RULING 33: the human-play design. Personalities, catching, training with type and recoil awareness, no speedrunning, roaming (not spinning), a favourite-Pokémon shiny hunt, visible and gift items, and the post-game (event Pokémon, trade-only species, simulated trades)

- **The user's answers to the human-like-score brief (2026-10-03), VERBATIM:**
  > 1: the goal is not to get there insanely fast, it should be playing the game as realistically as possible but we
  > can create multiple personalities the ai starts with and maintains through out the playthrough or maybe allow it
  > to change personalities as it plays/over time but revert to what its starting personality was (periodically
  > changes personalities) like one more focused on catching Pokémon, one more focused on story mode, one more
  > focused on training, etc.. (we will come up with more) but post champion/elite 4 main personality should change
  > to focusing on completing the pokedex.
  >
  > 2: no real fixed target but the more it is able to catch, the better!
  >
  > 3: Yes and also consider type advantages (both pokemon type and move types) as well as recoil damage (to
  > consider when fighting)
  >
  > 4: Speed as in gameplay? The ai should not speed through the game (the personality that wants to beat the game
  > as fast as possible will focus on progressing the story as fast as it can but does not miss opportunities to get
  > money, items, stock up, training and catch pokemon)
  >
  > 5: Training/hunting pokemon (not spinning in place but running through areas that spawn pokemon like grass, sand
  > or water for a few examples) others are the obvious movement/exploration, "favorite pokemon" (gets assigned a
  > random pokemon catchable in the wild in pokemon emerald and periodically wants to shiny hunt it for random
  > periods of times until it gets one but does not laser focus on this, just another personality maybe? Makes it
  > seem more human)
  >
  > 6: Yes picking up visible items is what it should do if it can reach them, also gift items like Amulet Coin,
  > Quick Claw, Black Glasses to name a few (there are still many to name and for it to decide to try to get)
  >
  > Note: event pokemon (deoxys, jirachi, mew to name a few) would need to be cheated into the game and should be
  > post game content (we have taken notes on this as simulating the mystery gifts) and also pokemon that are
  > technically available in the national pokedex that are only obtainable via trade should be added to pokemon
  > spawn pools that make sense post game and after getting the national dex (i forget if this already happens
  > natively in the game but if not we should design and add this somehow in the game) and trade evolution locked
  > pokemon should be obtainable somehow (maybe simulate a trade with a trainer and make up a random but possible
  > pokemon the trainer wants to trade for the evolution trade pokemon like Machamp and Alakazam to name a few, we can
  > detail this later but worth mentioning)
- **Where it lives:** organised into five design pillars in `ai-agent/HUMAN-PLAY-DESIGN.md` (the living design
  doc), with what the bot does today against each.
- **Two gaps found while recording it (verified in code):**
  - Story training and hunting use `spin()`, walking in place on one tile (`modules/story/early_game.py`
    `_story_spin` :202). The user's answer 5 rules that out.
  - Dex catches are refused under 10 spare balls (`DEX_CATCH_BALL_RESERVE = 10`, `story_mode.py:1757`). That is the
    top catch-skip reason, about 23 a game.
- **Coordinator decisions under this ruling:**
  - **The 24/7 learner is NOT stopped.** Its screening design measures every knob's effect on every recorded signal,
    and the raw logs are kept, so personalities and their scores can be applied retroactively.
  - **The learner's ranking switches tonight from progress-only to a provisional "balanced" human score:** 0.5 x
    progress/13 + 0.5 x Pokédex owned/202. Per answers 1 and 2, more caught is better, with no target and no cap.
    It is one personality's placeholder, not the final design. `objective` in `config.json` can switch it back
    (`progress`).
  - **Not decided:**
    - the personality set and how it switches;
    - its score weights;
    - the roaming-training behaviour;
    - item-pickup measurement;
    - the post-game mechanics.

    These are `#28-aiagent-v2` and later, designed WITH the user.

## 2026-10-03 — USER RULING 33, addendum: PC team swapping for situations (hunting, legendaries, gym and Elite Four counters), VARIED across playthroughs; Game Corner as a future note

- **The user, VERBATIM (sent mid-session, the same day):**
  > I forgot to mention about a human trait is using the pokemon pc to swap pokemon out for different scenarios
  > (hunting pokemon that flee for example using arena trap or mean look, legendary pokemon/pokemon hunting teams with
  > moves to help catch pokemon), battle teams for countering specific gym leaders and or the elite 4 (variable to
  > prevent each ai playthrough looking too similar to eachother, teams should make sense but not always be the exact
  > same team, for example if it needs a water counter it should choose water type pokemon randomly so each water
  > counter team for each run are relatively unique) does this make sense? Also the ai should be able to gamble at the
  > game corner if it would like (work in progress, more of a note for a future feature than a demand)
- **Recorded as** pillars 5 and 6 of `ai-agent/HUMAN-PLAY-DESIGN.md`.
- **The design rule that follows:** choose AT RANDOM among options that are ALL good enough, never among bad ones.
  Variety must not cost competence.
- **Today's related code:** counter hunts and box-first (`counter_hunt`, `_counter_ladder`; KI-118's fix on
  `wt/boxfirst`) and `team_policy.lead_rank_key`. Whether they break near-ties at random is UNAUDITED.
- **Game Corner:** a future feature, not a requirement.

## 2026-10-03 — USER RULING 34: the focus is the AI version; the bot is parked, not abandoned; AI concepts reach the bot only when the user says so

- **The user, VERBATIM:** "Note we are focusing on the ai agent, the bot is not abandoned as we wil return to it in the future but our main focus is developing the AI version now since we got to a good point working on the bot version, just clarifying but once we settle the ai version some of the ai logic (concepts) should definitely be brought over to the bot version but at a later time when I mention it. Understood?"
- **How it is applied (coordinator, confirmed to the user in the same reply):** the AI version drives the story bot's code as its hands. So an AI behaviour that needs bot code (roaming training, buying more Poké Balls, varied counter teams, ...) ships behind an AI-only flag whose DEFAULT is the bot's current behaviour, as `POKEBOT_BOSSMODE_TOPUP` already does.
  - The bot version is unchanged unless the AI sets the flag.
  - Porting a concept to the bot later = changing a default, on the user's word.
  - Rejected: changing bot defaults to serve the AI (it would silently alter the parked bot version); forking the bot's code into `ai-agent/` (two copies of the same hands drift apart).
- Recorded in `CLAUDE.md` (project rules: FOCUS), `ai-agent/HUMAN-PLAY-DESIGN.md` and memory.

## 2026-10-03 — USER RULING 35: the AI PLAYS THE GAME ITSELF; the bot is only its TEACHER (supersedes ruling 34's "AI-only flags in the bot's code" and ruling 31's "the bot is the hands")

- **The user, VERBATIM:** "The AI should be doing the navigation of the map, battles, interfaces, decisions, etc... as I would like to not have any bot like movements or usage of the bot in the AI version, we are simply using the bot logic/scripts and documentation to help teach the ai what to do, how to do it and why to do it so it gets a head start with learning how to play, part of being human is the ai interacting with the game itself without any bot usage or bot like behaviors"
- **What it corrects:** the coordinator had framed the AI as driving the story bot's code as its "hands" (RULING 31's hybrid as implemented; RULING 34's application), and the 24/7 learner as "the AI". Both framings are WITHDRAWN.
  - The learner tunes the BOT. It is TEACHER-side: strategy knowledge (what works, where games fail, how levels and catching relate to success) plus a corpus of bot games.
  - The AI PLAYER, which perceives the game and presses the buttons itself, learning what/how/why from the bot as a head start, is NOT built yet. Designing it is `#28-aiagent-v2`.
- **Kept:** the learner runs until the user decides otherwise. It costs no credits, and its knowledge and games are teaching material. `POKEBOT_BOSSMODE_TOPUP` stays, since its default is the bot's old behaviour. Never change the bot's defaults for the AI.
- **Facts for the design (measured 2026-10-03):** the user's PC has an AMD Ryzen 9 5950X (16 cores, 32 threads), 128 GB RAM and an NVIDIA RTX 2060 (6 GB), enough to train a modest game-playing model locally.
- Recorded in `CLAUDE.md` (FOCUS), `ai-agent/README.md`, `ai-agent/HUMAN-PLAY-DESIGN.md`, `01`, `03`, `04` and memory.

## 2026-10-03 — USER RULING 36: the AI player's eyes and its Claude coach. Perception by memory injection (as the bot does); the first version asks Claude; later versions consult Claude only when toggled on with the USER'S OWN API key (shareable, no dependency on one person's setup)

- **The user, VERBATIM:** "1: the ai sees the game like the bot by injection as it makes more sense" and "2: first version should ask claude, all future training version should still be able to consult claude and potentially the final version but requires to be toggled on and an api key to be provided to the program so the user can use their own claude agent (prevents dependency on my claude setup, I plan to share this with friends) but for now we can focus on the first versions goal of how it uses claude"
- **The boundary, as confirmed to the user:** EYES = memory reading through the emulator (shareable with the bot's framework); CONTROLLER = the AI presses buttons itself; BRAIN = entirely the AI's own (no bot pathfinding, battle strategies or menu scripts while playing, RULING 35).
- **Build implications:**
  - Claude is reached through the Anthropic API with a user-supplied key (config or environment, never hard-coded), behind a toggle that is OFF without a key, every call capped and logged.
  - The teacher-side learner's `consult.py` (the `claude` CLI on this PC) stays as it is; it is not the portable path.
  - Current focus: how the FIRST version uses Claude.
- Recorded in `ai-agent/HUMAN-PLAY-DESIGN.md` (architecture table) and memory.

## 2026-10-03 — USER RULING 36, addendum: only the PRODUCTION version needs an API key; dev/prototype/test versions consult Claude through the chat (reports and logs); a standing setup prompt for the production version, later

- **The user, VERBATIM:** "keep in mind that the "development/prototype/testing" versions should still be able to consult you without the api, they can consult you through the chat and by you reading their reports/logs. Only production/final version would require api keys (we should also note and work on this later but we should also include some sort of initial prompt to send alongside the request for information/help from claude so claude is setup to be ready to be helpful to the ai in the final version)"
- **Applied:**
  - The dev/test path is the file mailbox (reports, logs, `inbox/`, `DEVELOPER-NOTES.md`) read in Claude sessions, plus the local `claude` CLI (`consult.py`), with no key.
  - The production path is the Anthropic API with the user's own key, behind a toggle, carrying a standing INITIAL PROMPT (the game, the AI's goals and personality, its state, the help needed). That prompt is to be written later.
  - Recorded in `ai-agent/HUMAN-PLAY-DESIGN.md` (architecture table) and memory.

## 2026-10-07 — USER RULING 37: the AI player v1 decisions (answers to the design draft's §9)

- **The user, VERBATIM:**
  > 1: Whatever you think is best for organization, I do plan to eventually split things up to the point where it would be a single program that would run as the ai and load the rom automatically and all that so keep that in mind so it would be easy to run as an art piece like I mentioned.
  > 2: Whatever you think is best.
  > 3: Go all the way to beating Roxanne, we should chunk these out into gym badges unless you think smaller "chapters/milestones" are better.
  > 4: Yes, for the official acceptance runs (including naming and clock setting)
  > 5: A daily cap of about 20 calls on a cheaper model, at most $0.50 each. I have my weekly credits refreshed again so I am not too worried about usage since the ai will be training and conversing with you so allow the ai or the chat agent its talking to to use a few other ai agents to deliberate and/or escalate to a higher model (opus 5.5) if needed for supervision/correction/intervention/deliberation assistance.
  > 6: Human pacing is fine, the AI should look more human like but not loafing around, should still be working towards the goal and not just standing around but can detour for training, exploring, item collecting, gift items, fishing, gambling at game corner (future maybe), etc... like a human would but should not really stand still at any point (for now anyways)
  > 7: Whatever you think is best.
  > 8: All three (Catcher, Story, Trainer) from day one, since it's cheap and gives variety immediately.
- **Coordinator decisions on the delegated questions (1, 2, 7):**
  - Q1: the `ai_player/` package at the repo root with its own entry point. It reaches the framework only through two thin adapters (eyes, controller) plus one thin hook file in `sandbox-pokebot/plugins/custom_modes/`, built from day one to become the standalone single program (loads the ROM itself; an art piece).
  - Q2: STRICT. The AI removes every listener it does not own, from its own side, and the framework is not edited.
  - Q7: the learner goes to `max_lanes` 16 while the AI is developed (`ai-agent/config.json`; it applies at the learner's next cycle boundary).
- **Chapters within badges:** badge 1 = Ch1 intro to the Pokédex; Ch2 to Petalburg (Wally); Ch3 Route 104, Petalburg Woods, Rustboro; Ch4 Roxanne. Each chapter is developed and accepted on its own. Smaller units localise failures, and the badge stays the user-facing milestone.
- Recorded in the design draft §11, which wins over §1-§10.

## 2026-10-07 — The AI player's purity hardening STOPS at step 0.1; the remaining residuals are documented limits, and work moves to the AI itself (step 1, EYES)

- **Why stop:** steps 0 and 0.1 took two workflow rounds (about 3 hours and 4.6M subagent tokens) and now defend against the AI's OWN code deliberately tampering with its instrument: 25 tamper attacks refused, sealed modules, frame fences, a `sys.monitoring` monitor.
  - The real threat is narrower: our own future code ACCIDENTALLY using bot logic, or the framework acting on its own. The static gate (framework doors only; no write/load/reset) and the live attribution of foreign presses, writes and loads cover that, and both are fault-tested.
  - Every further round costs hours and finds subtler self-tampering routes that our code will never take.
- **Documented limits, accepted:**
  - `vars(module)`/`object.__setattr__` on the registry (refused statically);
  - the GUI debug menu reassigning the listener list (counted, not silent);
  - a launcher Ctrl+C has no in-child verdict, because the child has no console (the launcher reports INTERRUPTED).
- **Rejected:** another hardening round before any AI behaviour exists. That trades progress on the user's goal for defence against an attacker that does not exist. Revisit only if a real bypass appears, e.g. when the AI's own code grows.

## 2026-10-14 — AI player step 5 is COMMITTED with the verifier's pacing failure OPEN; step 5.1 fixes it and the review's findings BEFORE chapters 3-4 are attempted

- **Decision:** commit step 5 now as a checkpoint, and make step 5.1 the next work item. Its scope:
  - the two pacing stalls, with a check on any stretch where a screen waits for a button, under any reason;
  - exploring, with an intent-mix metric and a seed-divergence metric;
  - `STORY_PATIENCE` reset on real progress;
  - person-fair errand triggers and fight levels;
  - story-goal cooldowns.
  Chapters 3-4 (to ROXANNE) come after it.
- **Why:**
  - Step 5's acceptance (CH1 from a real New Game, CH2 stretch) holds by independent game reads, and the full regression passed; committing protects that work.
  - The open items are behaviour the user ruled on (RULING 32 "no speedrun", RULING 37 Q6 "never idle"), and two of them (patience, exploring) change how chapters 3-4 would play, so they come first.
- **Rejected:**
  - Fixing them inside step 5: the workflow had used both of its fix rounds.
  - Going straight to chapters 3-4: they would be built on the beelining and the patience rule, which would then have to be re-proven.

## 2026-10-15 — USER RULING 38: the learner drops to 8 lanes, and goes back to 16 when the AI player gives it something new to test

- **The user's words:** "Reduce it to 8, scale it back to 16 when the AI player gives it something new to test."
- **Why (the evidence put to the user):** after 26 cycles and 2,031 runs, the learner's top 15 strategies all score 0.36-0.38 +/- 0.02 (`findings/LATEST.md`, 2026-10-15 02:25 AM), so they are statistically tied. It tunes the PARKED bot's knobs (teacher side, RULING 35), not the AI player. Half the lanes lose almost nothing and halve its heat, CPU and disk use; the C: drive had 76 GB free of 1.86 TB.
- **How:** `ai-agent/config.json` `max_lanes` 16 -> 8, committed here. The learner's deployment clone fast-forwards between cycles and re-reads the config at each cycle's start (`ai-agent/README.md`), so the change takes effect at the first cycle after the push. No restart is needed and no file in the clone is edited.
- **The trigger to scale back to 16:** the AI player hands the learner something NEW to test (a knob or strategy of the AI's that the screen can measure). A plateau on the bot's knobs is not a reason to scale up.
- **Also user-directed the same day (standing):** proceed autonomously, strategically and cautiously; use Claude agents for research, checking, reviewing and reporting; research the story's ROUTING and MAPPING with agents BEFORE testing (no blind testing); keep "living, adaptive" mistake avoidance (safety measures from past mistakes, updated only when that prevents mistakes).

## 2026-10-15 — The AI player's development rounds: a fix round only for a FAILURE; the full regression of every step at a CHAPTER boundary

- **Decision:**
  - Within a step's workflow, a fix round runs only when the verifier reports a FAILURE or a rule violation. Its "weak proof" notes go onto the NEXT step's list, where they are still fixed and proven.
  - Each step runs the suites of the code it touched, including every earlier step's suites for a shared file it changed. The full regression of all steps runs at each CHAPTER (badge) boundary and before any promotion.
- **Why:**
  - Step 5 took about 7.5 hours and step 5.1 about 15. A careful verifier always lists weak proofs, so the old loop ran a 1.5-2 hour fix round even when nothing failed: step 5's second round did.
  - The CPU was 37-79% busy, so the time goes to sequential stages, not to hardware.
  - The user asked for safe speed-ups that keep accuracy (2026-10-15).
- **What is kept:** the independent verifier, the planted-bug (revert) proofs, held-out seed sweeps, pre-registration, the adversarial review, and Tier 0/1/2 on the docs.
- **Risk accepted:** a break in an earlier step that no touched suite covers is caught at the next chapter boundary, not the same day.
- **Rejected:**
  - Dropping the verifier or the revert proofs: they caught every real defect in steps 4-5.1.
  - Fewer seeds: frequency questions need them.

## 2026-10-15 — The AI player's order of work: step 5.2 = safety gates + PRODUCTIVE curiosity (on chapters 1-2), then 5.3 = chapter 3, then 5.4 = chapter 4 with the full regression at the badge

- **Decision:**
  - **Step 5.2** (proven on chapters 1-2):
    - The lessons draft's five missing gates: a frozen-tree watch, a seed and bounds ledger, a call-site census, a person-fair data door, and a disk budget with harness cleanup. Also the evidence checker's code-line fix and a living `ai_player` LESSONS list whose every line names its gate.
    - Curiosity graded by what it YIELDS: new tiles, items, catches, words, talks.
    - Errands raised by smooth odds, not a bypassing quota; detours that arrive or report not reached; a check for pushing against a blocker.
    - A LOAFING fault arm that must FAIL.
  - **Step 5.3:** chapter 3. First the recon's probes, then the woods as a passage, DOUBLE battles, and the milestone fixes.
  - **Step 5.4:** chapter 4 (the gym, MARC and TOMMY, ROXANNE with type advantage, the Quick Claw), with the full regression at the badge boundary.
- **Why:**
  - Loafing and the gates' absence affect every chapter. Building chapter 3 on them would mean re-proving it.
  - The recon showed chapter 3 alone needs double battles and a navigation change, which is a full step.
- **Rejected:**
  - Going straight to chapter 3.
  - Chapters 3-4 in one step: about two days of sequential work, with no checkpoint between them.

## 2026-10-15 — Usage-safe operation: the learner needs no Claude (consult OFF), restarts itself at logon, and the AI player's rounds go LEAN from step 5.3

- **The user's direction (2026-10-15):** about 60 % of the weekly usage was spent. The user wants the learner to run safely without Claude responses, and work to resume easily after a usage cut-off or a power cut. Usage should not be burned for little STORY progress, without sacrificing intelligence, safety or meaningful results. The user's words: "proceed how you think we should proceed, SAFELY".
- **Done the same day:**
  - **Consult OFF:** `ai-agent/config.json` `consult.enabled` false, committed with step 5.2. Each consult spent the user's weekly usage, and the ranking has plateaued (USER RULING 38).
    - A failed consult was already harmless (`consult.py` returns a log line; it is not a cycle failure), so this removes a dependency, not a crash.
    - Claude still reads the learner's findings in sessions (USER RULING 36's dev path).
    - Turn it back ON with the learner's scale-up.
  - **Autostart:** Task Scheduler `Pokebot-AI-Learner-Autostart` starts the clone's `run_agent.ps1` 2 minutes after the user logs on, with no time limit and never a second instance.
    - Tested live: started while the learner ran, the new wrapper's learner found the lock (pid 41292) and exited with code 2, and the running learner was untouched.
    - After a power cut it returns only if the PC powers on and logs in by itself (BIOS restore-on-AC, Windows auto-login): the user's choice.
    - On restart the learner ADOPTS and scores the cut cycle (`adopt_unfinished`).
  - **Tidy-ups:**
    - Closed an idle wrapper window left from 2026-10-03, which ran from the DEV checkout and had no child.
    - Closed the live test's window.
    - Removed the expired one-time task `Pokebot-Batch14` (last run 2026-10-01, no next run).
  - **In flight:** the handoff's "if stopped mid-task" row says that step 5.2 is IN FLIGHT and what to do if the session dies.
- **Decision: the AI player's rounds go LEAN from step 5.3.** The safety bar is unchanged; the machinery is cheaper.
  - **Where the usage went:** about 11M agent tokens since 2026-10-14 (step 5 3.0M, 5.1 2.6M, the recon 2.7M, 5.2 under way). The story frontier has not moved since step 5 (chapter 2).
  - **The four big costs:**
    - agents babysitting long emulator runs (5.1 alone made about 1,900 tool calls);
    - agents running mechanical regressions;
    - three overlapping verifier and reviewer agents per step;
    - a very long main chat re-read on every status message.
  - **The lean rules:**
    1. Long runs (sweeps, regressions) are plain BACKGROUND SCRIPTS that write a summary. An agent reads only the summary, or investigates a failure. A regression script (`run_regression.py`) runs every suite and prints the verdict lines, with no agent tokens while it runs.
    2. STORY-FIRST steps. Each proves its chapter's story goal by game reads on held-out seeds, with one fault arm per new guard and the existing human-likeness floors. No new metric machinery unless a real defect shows up.
    3. ONE combined adversarial verify-and-review agent per step. A fix round only for a failure (06 2026-10-15, unchanged).
    4. Cheaper models for read-only extraction and doc checks; the strongest for building and the adversarial check.
    5. Fewer, shorter status turns, and a FRESH session at each clean boundary: the handoff exists so that resuming costs little.
- **Rejected:**
  - Stopping step 5.2 mid-build: about 20 half-edited files, and its gates and loafing fix are prerequisites anyway.
  - Dropping the verifier, the planted-bug proofs or held-out seeds: they caught every real defect so far.

## 2026-10-15 — USER RULING 38 follow-up: consult KEPT ON (it CORRECTS this day's "consult OFF" entry); the learner at 12 lanes; the lean process to start after step 5.2

- **The user's words:**
  - "1. The Claude advice: keep it on";
  - "2. Lanes: you decide, if 12 doesnt add to the cost and/or the benefits of 12 is better, then change it back to 12";
  - "3. The lean approach: go ahead with it once we settle the details and when you think the best time to change things over to it".
- **Consult ON: "consult OFF" earlier today was WRONG, so read this entry instead.**
  - That entry rested on the claim that consult was "not adding much". Measured afterwards: 10 of the 15 best-ranked strategies in `findings/LATEST.md`, including the top 5, entered as consult PROPOSALS (21 such genomes in `learner.log`). The learner's own screening only measures knobs; the proposals are its exploitation.
  - The OFF edit was never pushed, so the learner never lost consult.
  - Cost: about 2 cheap-model calls a day. A failed call, for example when the usage runs out, is logged and harmless.
- **12 lanes (Claude's call, as the user delegated):**
  - `max_lanes` 12 gives 3 arms a cycle: the incumbent, one proposal and one design row (`brain.choose_arms`; lanes come in fours).
  - 8 lanes gave 2 arms, and while proposals queue faster than one per cycle (9 were waiting; 2 arrive a day), the screening design got NO rows. That side effect was missed when 8 was recommended.
  - Lanes cost no Claude usage. 12 is 75 % of the old 16-lane load; disk is guarded by `min_free_gb` 25.
  - Scale to 16 when the AI player gives the learner something new to test (USER RULING 38).
- **The lean process starts at the next clean boundary,** after step 5.2 is committed. Its scripts (`run_regression.py`, a sweep-summary runner) are its first work.
- **The autostart task is never deleted:** when training ends it is DISABLED (`Disable-ScheduledTask -TaskName Pokebot-AI-Learner-Autostart`) and re-enabled when needed (`Enable-ScheduledTask`), per the user's 2026-10-15 request.
- **Lesson (`08` is for bugs; this is a judgment error, recorded here):** a recommendation to remove a component needs the measurement of what that component PRODUCES first. Here the measurement took one read-only script and reversed the recommendation.

## 2026-10-15 — USER RULING 39: the trainer runs and IMPROVES on its own when Claude or the internet is unavailable, QUEUES its questions and reconnects by itself; the user drives goals and design, and Claude owns technical decisions

- **The user's words:**
  - "I am not a programmer and rely alot on you to make these sorts of decisions, I am more driving the goal and design of the ai agent the trainer is creating for me to deploy."
  - "I want the trainer to be able to autonomously run as stated (without internet or claude in the event they go out/usage credits run out) as well as be able to self improve and progress on its own if the above mentioned happens but also be able to still use claude so it effectively pings it (once it detects claude is unreachable) whenever it has a question so it acts as a way to continue to use claude so when claude becomes available it will reconnect with it (or some way to know when tokens are available/token weekly usage limit awareness or internet connection reconnected so it knows when claude is available again)".
- **Roles:**
  - TECHNICAL decisions are Claude's: architecture, process, tooling, learner settings. Each is explained in plain English with its evidence and recorded here.
  - Decisions about what the AI IS and how it should BEHAVE go to the user.
- **The design (Claude's, recorded so any session builds the same thing):**
  - **A. Runs without Claude.** Play already does. IMPROVEMENT will continue too: when no Claude proposal is waiting, the learner fills that slot ITSELF from its existing exploit mode (a Thompson draw, then mutants of the best; `brain.choose_arms`). Later, the same engine tunes the AI PLAYER's own settings (item C of the order below).
  - **B. A QUESTION QUEUE.** Whatever the trainer would ask Claude goes into a persistent queue file (it survives a power cut), with a priority and an expiry, because a stale question is dropped.
    - When Claude is reachable, the top questions are sent within the EXISTING daily cap (2 calls).
    - A backlog NEVER bursts: a reconnect must not spend the user's freshly reset weekly usage.
    - Answers stay PROPOSALS that real runs test before anything is adopted.
  - **C. Knowing when Claude is back, without spending usage:**
    - First a FREE internet check (can `api.anthropic.com` be reached).
    - No "ping" calls that cost tokens: the real question IS the probe.
    - Each failure is classified as NETWORK, USAGE LIMIT or OTHER:
      - a network failure retries when the free check passes;
      - a usage-limit failure waits until the reset time if the error states one, else backs off exponentially (30 minutes doubling, up to 12 hours).
    - The state ("Claude unreachable since X, reason, N questions queued, next try at Y") is written to `findings/LATEST.md` and `learner.py status`, so a session sees it.
    - ⚠ To Claude's knowledge, the CLI does NOT expose the account's remaining WEEKLY usage to a script. So "usage awareness" is inferred from the errors and the trainer's own cap. If a reliable meter is found, use it, but never assume one.
  - **D. Safety, unchanged:**
    - The 24/7 process never edits code, never commits and never pushes.
    - Its only git is the clone's fast-forward.
    - Consults stay read-only.
    - Self-improvement means TUNING settings and strategies, tested by real runs. New SKILLS (new game mechanics) still come from development sessions.
- **The order (Claude's call):**
  1. In the lean phase right after step 5.2: A's fallback, B and C, in the learner.
  2. Chapters 3-4 (the skills that story progress needs).
  3. Self-tuning of the AI player on all of badge 1. The learner points at the AI player's knobs, scored by story progress plus the human-likeness floors. This is the "something new to test" that returns it to 16 lanes (USER RULING 38).
  4. The coach (step 6) reuses B and C for the AI's own in-game questions.
- **Open for the user, at item 3:** should the AI play every game as a first-time player, or as one who remembers past playthroughs (bosses' levels, what worked, the map)?

## 2026-10-15 — USER RULING 40: the AI is a SEASONED PLAYER (it knows Pokemon and Emerald and remembers past games) who still plays every new game like a person, with many personalities cycled so no two playthroughs feel alike; Claude controls how and when

- **The user's words:** "I think it would be nice if the AI was familiar with the game between each game run (fresh start) so it doesnt look dumb/stupid, it should look like a seasoned player that is aware of the mechanics of pokemon in general as well as pokemon emerald, but still have the "new game" logic where it still explores and plays like a human, still aware of all pokemon available in the game, levels, skills, abilities, moves, type weaknesses/advantages, move pools for each pokemon, item list and location in physical world on the ground and gifts as well as carried items by pokemon (including rarity of carried items so it knows they dont carry them all the time) as well as rarity of pokemon that we discussed and shiny pokemon and legendary/event pokemon (cheat to obtain items to encounter them as we discussed in the past) effectively act like a human (Me) who plays the game but with varying personalities (more aggressive, more defensive, more exploratory, more completionist, collector, etc... and other personalities we can come up with) that it uses and cycles through so each gameplay looks, plays and feels unique and organic and not cold and robotic." And: "I give you control over how and when we implement this and how we handle/adapt it as we go (you too need to be self improving based on logic, reason and evidence and input from me if needed but mostly autonomous/self sustaining and improving)". This also answers RULING 39's open question: the AI REMEMBERS across playthroughs.
- **What it means:**
  - **KNOWLEDGE: all allowed,** as a seasoned player has it from experience or a guide:
    - the mechanics;
    - every species with its levels, learnsets (move pools), abilities and types;
    - every item and WHERE it is: on the ground, hidden, gifts, and items wild Pokemon CARRY, with their held-item rarity;
    - each species' rarity by area, shiny odds, and legendaries and events (event Pokemon by the simulated mystery gift, post-game, RULING 33);
    - trainers and bosses and their teams, and the maps and their connections.
  - **EXPERIENCE: allowed.** It remembers across playthroughs what worked (the levels a boss needed, the moves that won, places it got stuck). It starts each New Game knowing more than the last time.
  - **BEHAVIOUR: must stay human.** Each new game is still PLAYED like a person: it explores, detours, takes opportunities, and makes human-like choices and mistakes.
    - Knowledge informs choices (a seasoned player detours for an item they remember). It must never produce a beeline, a scripted route or robotic perfection.
    - RULING 32 (no speedrun) and the step 5.1/5.2 human-likeness floors (no stalls, no loafing, no beeline) stand.
  - **STILL NOT ALLOWED: LIVE HIDDEN STATE a player cannot see.** That is the RNG, a wild Pokemon's PID, IVs, nature or held item before the game shows them, the foe's exact stats, upcoming encounters, and anything the screen does not show NOW. The eyes stay memory injection filtered to what is on screen (RULING 36).
- **What it SUPERSEDES:** the step 5-5.2 limits on KNOWLEDGE:
  - hints only at the level the dialogue gives;
  - fight levels only for fights the game names;
  - coordinates and trainer positions marked developer-only and refused by the brain.
  - ⇒ The step-5.2 person-fair data door (gate G4) is RE-SCOPED: it guards LIVE HIDDEN STATE, not static game knowledge. The dialogue hints stay as the human-flavoured reasons the AI tells in its log.
- **Personalities:** archetypes such as AGGRESSIVE, DEFENSIVE, EXPLORER, COMPLETIONIST, COLLECTOR ("and other personalities we can come up with"); today's Catcher/Story/Trainer map onto them.
  - Each archetype is a weight set over battles, errands, risk and pace.
  - Each run picks one, drifts and returns, and has its own name, team and favourite, so playthroughs feel distinct and organic.
- **How and when: Claude's call, recorded here.**
  1. **Step 5.2 finishes unchanged.** Its G4 is re-scoped in the next step, a classification change, so step 5.2 is not interrupted.
  2. **Lean phase:** the scripts, RULING 39's autonomy pieces, G4 re-scoped.
  3. **A SEASONED-KNOWLEDGE BASE, before chapters 3-4,** because it helps them directly: knowing that PETALBURG WOODS joins Route 104's halves removes the recon's run-stopper. Learnsets, abilities, encounter tables with rarity, held items with rarity, item and gift locations, trainer rosters, boss teams, map links, shiny, legendary and event data.
     - Extracted as DATA with provenance from the bot's data files and the decomp, verified against the decomp (Claude agents validate; Gemini only enumerates).
     - It makes curiosity PRODUCTIVE: detours go to items and Pokemon it knows about, which also answers step 5.1's loafing finding.
  4. **Chapters 3-4.**
  5. **Self-tuning with EXPERIENCE memory and the expanded personalities** (RULING 39 item 3).
- **Self-improvement of the PROCESS (the user: "you too need to be self improving"):** every step ends with a short evidence-based retro:
  - what it cost (the usage audit);
  - what the verifier and review found;
  - which lesson or gate that adds to `ai_player/LESSONS.md` (living; a lesson retires when a gate makes it impossible).
  The user is asked only about goals and design.

## 2026-10-15 — The CLOUD PHASE: the user's $250 promotional cloud credit buys THINKING work that needs no emulator. Nothing may get stuck there, and the setup reverts when the credit ends

- **The user's words:** "proceed but ensure nothing gets stuck on the cloud in the event that I run out of credits or go beyond the expiration date or an outage ... leverage these temporary credits while they are available then reverting back to how things were setup before".
- **What the cloud is good for here (measured by the pilot, `claude/practical-pascal-ye42tg`):**
  - Linux, 4 cores, 15 GB, Python 3.11.
  - The doc gates and `check_purity` PASS there. Three unit suites fail only on missing pip packages (`confz`, `numpy`).
  - There is no emulator: `sandbox-pokebot/mgba` is Windows-only and untracked.
  - ⇒ Use it for research, data extraction, offline-testable code, doc housekeeping and reviews. Live game runs, sweeps and the learner stay on the PC.
- **Rejected:**
  - Running the game in the cloud: a Linux emulator setup, 4 cores, a 10-minute idle cut-off, and throwaway work after the expiry.
  - Routing the learner's consults through the cloud: they are small, the learner must never push its data, and it would add a stored token and moving parts that are useless after the expiry.
- **Safety, learned the same day:**
  1. The repo's hooks do NOT run in the cloud: they call `powershell`, which is absent there, and end in `|| true`, so they fail open. The pilot proved it: `git add -A --dry-run` and `git stash` both RAN. Every job's instructions therefore carry the rules, and after each job the coordinator confirms that `origin/main` is unchanged.
  2. Creating a routine through the API attached ALL the account's connectors (Claude Docs, Higgsfield, Google Drive, Claude Code Remote), and an update with an empty list did NOT clear them. Only the routine the user made on the website has none.
     - ⇒ ONE routine, `pokebot-cloud-worker`, is reused: its instructions are updated and it is run ON DEMAND.
     - Before every run, a `get` must show `mcp_connections: []`.
     - The API-made routine was disabled and renamed "DISABLED-do-not-run", for the user to delete.
  3. No schedules (a cloud job never fires by itself). Each job is small, pushes after every step, and keeps a STATUS file, so a cut-off loses at most one step.
  4. Nothing merges to main without local verification.
- **Cost:**
  - Not yet measurable: the pilot (5.5 minutes on Sonnet) left the card at $250 and the weekly meter at 64 %.
  - KB1 is the first medium job; the user reads both meters after it.
  - If the WEEKLY meter carries the cost, the cloud phase stops.
- **The revert,** by 2026-11-01 or when the credit is spent: disable the routine, keep every branch (merged or archived), and drop the handoff's cloud note. Nothing in the AI or the learner depends on the cloud.

## 2026-10-16 — "P2" decided by Claude (USER RULING 39: technical): the shares of TIME stay REPORTED, never graded; human-likeness is graded by what curiosity YIELDS, run by run

- **The question** (`ai_player/README.md` "P2 needs a user ruling"): should the share of frames spent on errands and curiosity be a pass/fail bound?
- **Decision: NO.**
  - Step 5.1 measured the cost of that: a time quota is the exact quantity the AI learned to fill, and it LOAFED (`08` 2026-10-15).
  - Time shares stay REPORTED.
  - The graded human-likeness properties are:
    - a per-run yield floor, measured by the GAME's reads the AI never computes;
    - spacing;
    - no stall, no loafing, no pushing;
    - no beeline, as the time ratio against the beeline control.
- **Why it is not the user's call:** it is how to MEASURE "plays like a person", a technical choice under RULING 39. The user's goal (RULINGS 32 and 40) is unchanged.
- **Rejected:** grading time shares with a floor, because Goodhart was measured, not hypothetical.

## 2026-10-16 — USER RULING 41 (confirmation of the overall goal): a deployable AI agent that plays the WHOLE game on its own through the emulator, like a person, with NO bot programs; time is acceptable; the 24/7 learner is called "the bot tuner" until it tunes the AI player

- **The user's words:**
  - "my hope was to TRAIN an AI agent to PLAY the game by interacting with the Emulator and game ... it launches the emulator, loads the rom, creates a profile/uses an existing profile and plays the game from beginning to end (maybe some setup settings/steps before the ai takes over) so the ai is taking the drivers seat in place of the human, without any bot usage";
  - "so long as we are training an ai agent to deploy that can play the game entirely on its own the way I described without using bots, that is my goal ... I am fine with it taking time to complete".
- **What this confirms** (RULINGS 35-37 and 40):
  - The AI player (`ai_player/`) is that agent. It has its own eyes (memory reads filtered to the screen), hands (its own button presses) and brain.
  - It uses NO bot code, enforced by `check_purity` and the live attribution of foreign presses and writes.
  - The bot's work reaches it only as knowledge, lessons and experience data.
  - The shared part is the emulator host (the console, not the player).
  - The end state is the standalone program of RULING 37.
  - "Trained" means: knowledge from data, EXPERIENCE across games (RULING 40), and settings tuned by real games (RULING 39 item 3). A neural network is not the foundation (rejected: research-scale compute; imitating the bot would copy its robotic style). A small learned part may be added later only where it clearly helps.
  - Deployed, it is light: memory reads and button presses on the CPU at game speed.
- **The naming:** the 24/7 learner in `ai-agent/` is "THE BOT TUNER" until it is pointed at the AI player's settings. Its 15 % Champion rate is the scripted bot's, flat over four weeks (13.7 / 16.6 / 13.0 / 16.1 % by week-long blocks of cycles, measured 2026-10-16), so it is not evidence about the AI. Its growing corpus of finished games is teacher data for the AI's experience memory.
- **The plan addition (Claude's call):** after the KB1 merge, MINE THE BOT'S FINISHED GAMES into the AI's experience: per chapter, the levels and teams that beat each gym, where runs failed, and which routes and items mattered. This is data only, never code, and it is the largest available accelerator toward the whole game.

## 2026-10-21 — USER RULING 42 (the step-1 operations questions): backups go to Z:, the scheduled tasks are approved, compressed raw logs are kept forever, and a weekly-meter reading of 3 %

- **The questions** (asked 2026-10-21 about 4:46 AM and 5:31 AM; the backlog listed them under "Waits on the user"):
  - O4: where the nightly backup of the bot tuner's data goes (E:, a separate SSD, or Z:, the 4 TB HDD);
  - O4 + O1: may Claude register Windows scheduled tasks (the 1 AM backup, and later the 30-minute watchdog);
  - O3: keep the compressed raw logs forever (measured about 69 MB a 12-hour cycle, about 50 GB a year on C:), or cap them;
  - the current weekly usage meter, to calibrate the usage audit (P3).
- **The user's answers, verbatim:**
  - "1: 3% used right now."
  - "2: Z 4tb HDD is fine."
  - "3: That is fine if you deem it necessary."
  - "4: Whatever you recommend."
- **What follows:**
  - **Backups go to Z:** (`tools/ops/ops_config.json` `backup_dir`). E: was Claude's first suggestion; Z: has 181 GB free, and a nightly backup is about 1.2 MB.
  - **Scheduled tasks are APPROVED, at Claude's judgement.** Claude registers the backup task once O4 is reviewed and the clone holds `tools/ops/`, and the watchdog task once O1 is built and reviewed. Each goes in with a dry run first; `install_ops_tasks.ps1 -Uninstall -Apply` removes them. This approval covers these two ops tasks, not scheduled tasks in general.
  - **The compressed raw logs are KEPT FOREVER** (`ai-agent/config.json` `keep_archive_cycles` 0; nothing deletes an archive). They are the AI's experience input (USER RULING 41, backlog A6). Claude's plan, which the user accepted: the watchdog warns below 40 GB free on C:, and archives older than about a year move to Z: later (not built; a future item, by copy-verify-then-delete).
  - **Calibration:** the meter read 3 % when this session's input-equivalent total was 8.53 Mtok (`tools/usage_audit.py --session`). On that one point, a week is about 280 Mtok, against the older 143 Mtok = 36 % point (about 400 Mtok). The meter rounds to whole percent and also counts the bot tuner's consult calls, which leave no transcript, so this is one point of several to collect; the usage warnings (85 % warn, 90 % park) follow the meter whenever the user gives a reading.
- **Do not re-raise these four questions.**

## 2026-10-21 — Technical decisions of the O3 / O4 / P3 / KB1 / S3-2 round (Claude's calls; USER RULING 42 is the user's)

- **O3 archives as a zip, not a tar.gz.** One log can be read by name with `ZipFile.open` (the AI's experience reader, backlog A6, needs that), and the manifest records name, size and CRC32 per member. Rejected: tar.gz (a single log means decompressing the stream).
- **O3 HOLDS instead of rebuilding.** When the state is not provable (an unreadable manifest, a partial delete whose remaining originals no longer match), it touches nothing and flags it; the learner keeps running. Rejected: the first build's "quarantine the zip and rebuild from what is left", which lost 3 of 4 files in the review (`08` 2026-10-21).
- **Archives are kept forever** (`keep_archive_cycles` 0), per USER RULING 42. Nothing deletes an archive, and no archive file is ever overwritten.
- **The lane profiles are archived, with `dup_of`.** Their debug logs are byte-identical to the batch's, so only the unique files are stored (`badge-log.json`, `stats.db`, saves, `.yml`, screenshots). Rejected: deleting them as before (it loses the AI's experience data).
- **Accepted residual risks (documented, not fixed):** the small re-stat window between the last check and the delete (a writer that opens and closes per line holds no handle), and the non-atomic `acquire_lock`.
- **The canary deploy order: code first, config second.** Deploy with `keep_raw_cycles` still 20 and confirm "restarting into it" in the clone's `learner.log`; only then push the lowered value. Reason: if the code deploy is refused (the suite fails) while the config change still arrives, OLD code would apply the lowered window, and old code DELETES. K = (unpruned entries in `state.json` while cycle X runs) + 1.
- **O4 holds on record IDENTITY, and compares against the LARGEST earlier baseline.** A count is defeated by the learner's own growth (about 107 records a day). Rejected: the line-count shrink check (it held only until growth passed the old maximum).
- **KB1 merged as-is.** Nothing loads `seasoned/`, so the known semantic errors cannot change behaviour; the extractor is fixed and re-extracted in the next item, followed by the step-5 adversarial pass.
- **`run_gates.py` gained a WARN state** (`WARN_OK`, exit 4): a gate that ran but could not verify is counted out of the passing gates and named. Rejected: letting a skipped decomp check count as a pass.
- **P3's warnings follow the user's NEWEST meter reading.** Readings this week: 8.53 Mtok = 3 % (about 0.35 % per Mtok, but the meter rounds to whole percent, so 3 % spans 2.5-3.5 %) and 25.63 Mtok = 7 % (about 0.27 % per Mtok, a week about 365 Mtok; 7:19 AM 2026-10-21). The fit through the origin is dominated by the old 143 Mtok = 36 % point (about 400 Mtok a week). Rejected: quoting the fit, which understates the session's share. Also accepted as a residual risk: a profile file recorded as `dup_of` is matched to its batch twin by file name, size and CRC32, not byte for byte (a collision is about 1 in 4 billion per same-name, same-size pair; on real ai0028 every pair was sha256-identical).

## 2026-10-21 — Technical decisions of the O6 + O7 / O1 / KB1 step-5 round (Claude's calls)

- **O7's margin falls back to the default (15) and an early-archive failure never withholds a batch.** `early_margin()` takes a finite number >= 0 and otherwise uses the default, logged once; `early_archive()` has its own try, and its failure goes on to `disk_guard`. Rejected: the first build, where a bad `early_prune_margin_gb` (None, `'abc'`, `[15]`) silently skipped `disk_guard` and the batch on every pass, so a config typo could stop all play.
- **O6 + O7 ships as its own restart, after O3's deploy is confirmed.** It is committed locally and NOT pushed. Reason: one restart per change keeps a failure attributable (the O3 canary needs a clean read of "restarting into it"). Rejected: pushing it together with O3's deploy.
- **`gap_minutes` uses epochs by identity.** Ops rows carry `finished_epoch`, and the previous row's epoch is used when its tag matches the previous cycle. Rejected: parsing the time strings, which failed in the DST fall-back hour (gap 65.0 for a true 5.0).
- **The watchdog toasts only when a NEW problem joins the NEEDS set, and has hysteresis.** `disk_low` clears above the alarm + 2 GB; "recovered" needs 2 consecutive alive runs; a shrinking set updates the file with no toast. Rejected: the first build's toast on every change, which gave 8 toasts in 8 runs for a disk hovering at the 40 GB line (the line O7's early archive also acts on).
- **The watchdog checks progress, not just life.** A learner alive but with no cycle started or finished for `cycle_minutes` + 120 min is NEEDS YOU, because a process that is up can still be doing nothing (a false calm).
- **KB1 labels availability rather than deleting rows.** The raw decomp facts stay, and the semantics are added: `availability`, `requires=post_game`, `conditions`, plus `where_to_find_normal_play` and `where_to_find_main_story` indexes. Rejected: dropping the frontier, gift and post-game rows (a seasoned player knows they exist, and deleting loses the facts).
- **`post_game` is derived from the decomp, not typed in.** Each gate is a cited line (`FLAG_SYS_GAME_CLEAR` branches and the hall-of-fame flags), the extractor refuses when the cited text is gone, and the verifier reaches the same 26 tables by its own walk. Rejected: a hand-written list of post-game maps.

## 2026-10-21 — Technical decisions of the A6 and stage-template review rounds (Claude's calls)

- **A6's priors labels come from an ALLOWLIST, and the denylist is only the second layer.** Anything outside the label vocabulary (the `classify_wall` names, `boss wall: <one of the 13 bosses>`, the fixed failure labels, `CHAMPION`) becomes `<other>` and is counted. Rejected: the build's deny-mask, which passed case and phrase variants and dict keys. The cost is measured: 184 real wall labels (Victory Road failures, "Story: global watchdog") now count as `<other>`. A label joins the allowlist only by a code change with its test.
- **A6's write guard compares resolved paths AND directory identity, and refuses hard-linked targets.** It always guards the default clone and this repo's `ai_player/`, whatever `--clone` / `--repo` say. Rejected: `abspath` prefixes (junctions, 8.3 names and `\\?\` got past them).
- **A6's lock is an OS byte-range mutex around taking and releasing, plus a per-run token.** Rejected: `os.replace` to a unique name followed by `O_EXCL`; the round-1 harness ran it, and both runs acquired. The POSIX `fcntl` branch is untested (Windows only here).
- **A6 defers rather than guesses, and the deferral is bounded.** A tier-B source that is missing or unreadable while its cycle is not settled is DEFERRED (exit 6; not stored, not cursored), so a race with O3 never stores a run as tier A for good. A cycle the learner marked pruned, or a `batch/` with no log and no `raw.zip`, is settled at once (tier A, with the reason). Any other deferral ends after >= 3 passes AND >= 24 h as tier A marked `deferred-timeout`. Rejected: deferring forever (exit 6 on every run for a cycle that can never recover), and storing tier A at once (the round-1 defect).
- **refix's PASS is an allow-list of verify@2's keys.** With `all_pass: true`, any key outside `all_pass`, `complete`, `FAILURES`, `weak_proofs`, `rule_violations`, `summary` gives UNKNOWN, and `complete` must be true. Rejected: round 1's normalised variant spellings of `failures`, which missed `FAILURE`, `errors` and `failed_checks`.
- **regression_due covers what a suite's driver READS, not only what it imports** (`reads` in `suite_map.json`, measured per driver). Accepted cost: a docs commit makes units and revert_safety_gates DUE, because check_lessons quotes those docs.
- **'ok' stays unreachable until an evidence producer records a wider scope**, and regression_due says so in one NOTE line. Rejected: changing the `ai_player` evidence producers inside this item.
- **The in-flight notes folder (backlog E1) is `PROJECT KNOWLEDGE/in-flight/`, git-ignored except its README.** A note describes this machine's uncommitted working state, which no other computer has, and a committed note would outlive its run. Rejected: tracking the notes (stale resume points on other machines), and the scratchpad (lost with the session, which is exactly what E1 guards against).
- **Workflow prompts are rendered from the templates from now on** (`.claude/commands/orchestrate.md`). If a template does not fit, the template changes (and is linted); a stage prompt is not hand-typed. Rejected: keeping inline prompts, which is how the measured costs of backlog P11 arose.

## 2026-10-21 — Technical decisions of S2-1, the doc-size ratchet (Claude's calls)

- **R8 is a RATCHET:** each ceiling is today's size + 8 KB headroom, and lines over 1,200 characters are waived by head hash + last 60 characters. Both only shrink against HEAD, and growth needs a printed history record (`--rewaive --why`, `--raise --why`). Rejected: a hard 60 KB budget (red on arrival), and a ceiling at the exact size (the cheapest way past it is to trim a caveat, CLAUDE.md rule 2).
- **Table rows are waived like prose, not exempt; only fenced lines are exempt.** Rejected: the spec's row exemption, which hid 10 rows of up to 24,531 characters in 04's state table, the very grep-cost lines R8 exists for.
- **The test overrides are CLI flags** (`--docs-dir`, `--budget-dir`, `--repo-dir`, `--head-budget-dir`), not the spec's `POKEBOT_DOCS_DIR`. R6 treats any quoted `POKEBOT_` literal in `tools/story-dev` as a bot flag that needs a registry row.
- **The sweep errs toward SKIPPING.** Heading and body are both checked for open markers: upper-case status words, a narrow case-insensitive set (UNDRIVEN, UNTESTED, Unverified, NOT DONE, NOT PROMOTED, FOLLOW-UP, KNOWN GAP), unchecked boxes at any indent or in a table cell, and open subheadings. A skipped block costs bytes; a wrongly moved one hides live work. Even so, its MOVE list is read before any real `--apply` (05's 9 candidates first).
- **Every `--apply` rehearses the complete result and runs `lint_docs` on it before writing.** Rejected: checking afterwards. Round 2's split wrote a 04 that broke R3, and undoing that needs destructive git, which the hook blocks.
- **The handoff's 60 KB target is a SEPARATE design item, S2-1b (the handoff slim-down), not part of S2-1.** The `###` sweep reaches 0 B of 04. S2-1b must decide how 04's `##` sections, banner and state-table rows are retired verbatim, and how R3's 900-line budget and R8's bytes coexist: splitting 04's mega-lines alone is refused by R3 (883 -> 1,069 lines). Rejected: calling S2-1 done against its final acceptance, and building a `##` mode inside this item without its own design and review.

## 2026-10-21 — USER RULING 43 (the watchdog's human check): the test toast arrived; a brief window flash every 30 minutes is fine; the monitor stays off

- **The user, 4:51 PM, after `watchdog.ps1 -TestToast`:** "1: yes I saw it 2: that is fine, I am not going to be using this computer for anything other than this project for a while, note that I will have the monitor turned off so it does not burn the screen".
- **So:** the watchdog task (O1) is registered as built: every 30 minutes, in the user's session, in a hidden PowerShell window. It waits only for the clone to hold `tools/ops/watchdog.ps1`, which arrives with its next fast-forward (the end of ai0040, about 4:08 AM 2026-10-22), because the task runs the clone's copy.
- **The monitor being off changes nothing:** the tasks run in the logged-on session, a toast waits in the notification panel, and the Desktop status file and `tools/status.py` carry the state. Only sleep or signing out stops them.
- ⛔ **Do not re-ask** whether the toast reaches the user or whether the 30-minute flash is acceptable.

## 2026-10-21 — USER RULING 44 (the S3-4 boss-knowledge question): the AI KNOWS each boss Pokémon's held item; it does NOT know their exact stats (IVs, hidden stats) or the trainers' AI flags

- **The question, as put to the user:** should the AI know bosses' held items (Claude recommended yes) and their exact stats (Claude recommended no)?
- **The user, 2026-10-21 (after 4:54 PM):** "I approve what you recommend for the remaining questions".
- **So, for S3-4's generated knowledge (`trainers.json`):**
  - `heldItem` moves from WITHHELD to ALLOWED. A seasoned player knows or looks up what a gym leader's Pokémon hold; it is static game knowledge, RULING 40.
  - `iv` and `aiFlags` stay WITHHELD. They are hidden numbers a person playing cannot see.
  - The spec's default stands for moves and levels, which are KEPT. This answer did not change it.
- **Not decided by this ruling:** the S3-4 spec's two other "needs the user" items (the bot's species shares in the AI-facing statistics, and exact trainer sight ranges). They keep the spec's defaults until the user answers.
- ⛔ **Do not re-ask** whether bosses' held items are allowed or their exact stats withheld.

## 2026-10-21 — USER RULING 45 (S3-4's two other user items): the AI does NOT see which species the bot chose; it DOES know trainers' positions and sight ranges

- **The questions, as put to the user (with Claude's recommendations):**
  - (1) The AI sees the scripted bot's statistics (levels at first loss and at the win per gym, losses), labelled "bot corpus". Should it also see which Pokémon the bot chose? Recommended: no, so the AI picks its own team the way a person would.
  - (2) Should the AI know where each trainer stands and how far they see? Recommended: yes, static map knowledge a seasoned player has from past playthroughs (RULING 40 "maps").
- **The user, 2026-10-21 (after 4:56 PM):** "Whatever you recommend".
- **So, for S3-4:** the bot's species choices stay OUT of the AI-facing statistics, and `maps.json` KEEPS each trainer's tile and sight range (and each door's position). Both were the spec's defaults, so no build change follows.
- ⛔ **Do not re-ask** whether the AI sees the bot's species choices, or whether it knows trainer positions and sight ranges.

## 2026-10-21 — Technical decisions of S4-1, the regression runner (Claude's calls)

- **The runner records the scope regression_due checks:** a `covers:<suite>` code-line label, its digest computed by ONE function both tools call. This is the "producer records a wider scope" remedy regression_due's own docstring named. Rejected: changing the live/rate drivers' scope labels, which are graded code (with B1 at 5.3).
- **Graded and ROM suites are never run by it, and it refuses to start while a `rate_*`/`live_*` driver runs:** test_safety_gates compares the seed ledger's bytes, and a sweep writes it. Rejected: a lock file, which a crashed sweep would leave behind.
- **Shards come from `unittest.TestLoader`, in a subprocess, and their union is checked against it before running.** On any mismatch the module runs unsharded and the output says so. Rejected: the spec's AST planner (verify round 1 F1: it missed aliased methods, renamed TestCase imports, async cases and classes under an `if`, and a missed failing test read PASS).
- **A timeout kills through a Windows Job Object:** the suite is created suspended and joined before it runs, with KILL_ON_JOB_CLOSE. Rejected: `taskkill /T`, which misses a grandchild whose parent already exited (verify round 1 F5).
- **ONE suite runner:** `run_units.run_command` delegates to `run_regression.run_command`. Rejected: two copies (verify round 2: the second kept the old gap and a false docstring).
- **The full lane's real cost is accepted:** about 72 min of wall time under the bot tuner's 12 lanes, because revert_step3 (the floor) runs about 2x slower under contention. Its timeout is 3.5x its serial time (it used 86 % of 2.5x). Rejected: running the full lane serially (no faster: revert_step3 still dominates) and dropping revert_step3 from the lane (its 94 mutants are the step-3 world's only revert proof).
- **N8's grader half waits for step 5.3 with B1:** typed `Check` statuses and the forced-PASS sites in rate_step5 change the graded step-5 grader and re-grade it.

## 2026-10-21 — Evidence identity = the code under test (#28-evidence-identity; Claude's call)

- **An evidence file's identity is (label, the label's committed files at its HEAD, its diff digest), computed from its existing code line.** Rejected:
  - HEAD + digest, under which every docs-only commit would make all evidence stale;
  - a new code-line format, under which 216 old files would need rewriting or a second reader, against G6;
  - the digest alone (the bug).
- **What git cannot see is documented, not chased:** an assume-unchanged / skip-worktree edit, or a gitignored file inside the scope, keeps the identity. `regression_due.py` reports the first as unproven, and the purity gate covers ignored caches.
- **A diff later committed unchanged reads as ANOTHER tree.** The earlier evidence is archived, never lost: the safe direction.

## 2026-10-22 — Technical decisions of S3-4 slice 1, KB2 (Claude's calls)

- **`campaign.json` lives in `ai_player/knowledge/world/` with the other KB2 files.** Rejected: the spec's top-level path, which `check_fairness` globs and would flag as unclassified. The spec's intent is that nothing is read or checked until a loader and a `KNOWLEDGE_FIELDS` classification exist, and a schema now would have pre-empted that later, graded step.
- **`TRAINER_NONE` (`.partySize = 0`) is the one trainer exempt from W5's "party >= 1", by name.** Any other empty party fails.
- **A campaign entry's `fights` are derived from the `trainerbattle` lines of its area's scripts** (the skeleton's boss plus a multi-battle partner), and `area_bosses` (every boss the area's scripts battle) is kept apart. Rejected: "every boss in an area's scripts is in that entry", which would put Norman in ch2_dad.
- **The Space Center multi battle's `party_min` is 1, marked recon / decomp UNVERIFIED.** Recon 4.6 says 1-3 Pokémon; the spec's 3 was a reading of it.
- **test_kb2 stays out of the `--quick` lane** (about 15 s against its 5 s bar); it runs in every `run_units` and `--full`.

## 2026-10-22 — Technical decisions of the chapter-pack tool, A5 (Claude's calls)

- **A pack never refuses for size.** Over the 12 KB cap, the .md keeps every load-bearing item in full and summarises ordinary trainers per map, pointing to the .json. Rejected: refusing the chapter (4 of 24 chapters had no pack), and raising the cap (the cap is the reason the pack is cheap to read).
- **Input integrity is `verify_world.py`'s job, so the pack tool runs it first and refuses on any mismatch.** Rejected: having the pack tool detect missing input data itself; it cannot, because no other input names an ordinary trainer or a warp.
- **The pack's self-check reads the input files with its OWN loader.** Rejected: one shared reader, the same "a check that shares its input with the thing it checks is not a check" shape that `02` records for `archive_doc_block`; it recurred here and the round-3 verify found it.
- **Packs exist for every campaign chapter (1-24)**, generated and committed. They are read by agents (recon), never by the AI's play code.

## 2026-10-22 — Technical decisions of O5, the consult novelty gate (Claude's calls)

- **A paid call is impossible unless it is already counted:** a reservation row is appended to `consult_log.jsonl` BEFORE `claude` runs, and the outcome row is never counted. Rejected: writing the row after the call, under which a log that could be read but not appended to let a paid call go out every cycle (verify round 3), and a killed learner left the call uncounted.
- **The gate fails OPEN on its own errors and CLOSED only for one cycle when the reservation cannot be written.** The consult is advisory, so a broken gate must not silence it for good, and a broken log must not let calls go uncounted.
- **The wall rule stays as specced, with its measured limit recorded.** On cumulative shares it never fired in 21 replayed consults. Rejected for now: a windowed rule, which is a design change with its own replay.
- **O5 ships as its own restart, after O6+O7's was confirmed.** It deploys at the same boundary as the canary's first archive, which the OLD process does before updating, so the two stay attributable.

## 2026-10-22 — S2-1b (the handoff slim-down): SNAPSHOT, THEN REWRITE; and the queue order after it

- **Decision (the coordinator's technical call; the order follows the user's "backlog top-15 order"):** `04-HANDOFF.md` was slimmed from 403 KB to about 60 KB in two steps. The spec is `ai-research-notes/2026-10-22-BUILD-SPEC-S2-1b-handoff-slim.md`.
  - (1) The WHOLE old file was appended byte for byte to the end of `28-HANDOFF-ARCHIVE.md`, under one snapshot heading naming HEAD `95f8abed`.
  - (2) 04 was rewritten from the LIVE material only. That covers the AI player, the bot tuner, the session rules, a real `## If stopped mid-task` section, and every live story-bot rule quoted with its old line number.
- **WHY:** three read-only recon agents (`2026-10-22-S2-1b-recon-*.md`) measured it. The live pieces alone (the banner 24 KB, the STATE table 72 KB, the `➡➡➡` line 64 KB) were about 160 KB, each a mega-line mixing the present with months of history. So no verbatim move of whole lines or sections could reach 60 KB, and `archive_sweep.py` had moved 0 B.
- **How it keeps the earlier rulings:**
  - Ruling 2026-08-22 PASS 5 (archive verbatim, never trim live content): every byte is in 28, and an adversarial completeness verify hunted the rewrite for any LIVE item it dropped. It found 4 caveats and 1 false "rule"; all were fixed.
  - Ruling 2026-08-28 (no "part N of M"; split by KIND): no new numbered file; history goes to 28, its established home.
  - The rows pinned by rulings stay: the stash row (2026-08-13), the drift row with its "do not flip line endings" advice (2026-09-15), and the cloud note (2026-10-15).
- **Proof:**
  - Lossless: three independent scripts (the builder's, the verifier's, the coordinator's) show that 28 at HEAD is an untouched prefix, that the old 04 follows it byte for byte with nothing after it, and that one flipped byte is detected.
  - All gates pass, including `run_gates.py --quick` ("ALL 140 ENFORCING GATES PASS").
  - Two verify rounds plus a cold-start check.
- **The queue after it (the coordinator's ruling, in the backlog's order), as 04 now states it:**
  - (1) S2-1b part 2, the `03-PUNCH-LIST.md` slim-down, the last open half of backlog item 7, by the same method and with its own spec first;
  - (2) KB2 slice 2 stage 2a then 2b (item 11; spec `2026-10-22-BUILD-SPEC-S3-4-slice2.md`, READY);
  - (3) step 5.3, B1 + N8's grader half (items 12-13; recon `2026-10-22-B1-grader-recon.md`);
  - (4) the rest of the top 15.
- **Rejected:**
  - Splitting the mega-lines in place: refused by R3, 899 + 208 lines.
  - A new numbered snapshot file: it would make the asymmetric 04/28 pair a trio.
  - Condensing the live lines without a snapshot: it would not be verbatim, and loss could not be proved.
  - Doing slice 2 before 03's trim: against the backlog's order.

## 2026-10-22 — S2-1b part 2 (the `03-PUNCH-LIST.md` slim-down) DEFERRED after its recon; the queue reorders to KB2 slice 2 first

- **Decision (the coordinator's technical call; it revises this morning's queue ruling, same date):** part 2 is not built now. KB2 slice 2 (backlog item 11, spec ready) becomes queue item 1, then step 5.3.
- **WHY (three read-only recon agents, filed as `ai-research-notes/2026-10-22-S2-1b-part2-recon-{tools,content,adversarial}.md`):**
  - (1) Live AI-era work is about 7 % of 03 (5 open items, about 10.7 KB). By bytes, open items are 48 % and `[~]` items 17 %; DONE items are only 22 %, and 97 of the 179 `[x]` items still carry do-nots, pending checks or pointers to open work. So a slim 03 must STUB open, parked story-bot items. That is "trimming live content", which `06` 2026-08-22 PASS 5 forbids ("reclaim budget by ARCHIVING VERBATIM, never by trimming live content"), even with a verbatim snapshot. It was right for 04, where the live items were carried in full.
  - (2) The user's own lists (03:2942, 3012, 3047, 3070, 3196, 3230, 3246, 3281, 3302; about 30 KB) encode the user's order and cull rights, and must stay verbatim.
  - (3) 03 is not a whole session-start read: the kit hook prints its first five `- [ ]` lines. So the per-session saving that justified part 1 is small here.
  - (4) The archive choice is unsettled. `archive_sweep.py` reserves `32-PUNCH-LIST-ARCHIVE.md`, while every earlier 03 retirement went to 28, and part 1 rejected a new numbered file for 04.
- **Open design questions for whoever resumes it:**
  - stubs versus the 2026-08-22 ruling (or a by-KIND split, the parked story backlog in its own current-state file);
  - 28 versus a new 32, and which byte form each lossless check compares (03 is LF in git and CRLF in the tree);
  - the 37 `[~]` items;
  - `probe_closed_item_refs.py` goes vacuous (34 closed items today, about 0 after);
  - `wrapup.md:8` and 03:3-4 tell sessions to move done items into a Done section in 03;
  - the session brief shows whichever five open lines come first.
- **Done now, cheaply:** the `## Done` section's warning said THREE open items sit under it. The recon counted at least 25 (51 open boxes). The warning now says so, citing the recon, without moving any block.
- **Resume when:** the story bot resumes, or R3's 4,400-line budget blocks real work. Today new 03 text goes into existing lines, with `--rewaive`.
- **Rejected:** building it now by stubbing open items (the 2026-08-22 ruling); a done-items-only move (22 % of the bytes, and 97 of them carry live text).

## 2026-10-22 — KB2 extraction asserts only what an independent exhaustive scan re-checks; `unknown` accepted over fix-spec-2's Beldum answer

- **Decision (the coordinator's technical call; it binds stage 2b and every later KB2 file):**
  - The extractor writes a value for the AI only from one of two sources.
  - (1) A pattern that an independent whole-decomp scan can re-check on EVERY record. `once` and `until_received` need a SOLE writer of the blocking flag or var. That means scripts, every `src/` mention, and C range clears. A once-guard must also hold at new game. A special with no table entry gives `when: null` and repeat `unknown`. A possession check (`checkitem`) is a condition, not bag room.
  - (2) A small CITED hand table (`REARM`, `SPECIAL_EFFECTS` with 68 entries, `CHOOSER_OF`, `MAP_CONDITIONS`). Every cite (path:line plus token) is checked at build time and again at verify time.
  - Anything else is `unknown` or `when: null`, and is listed in the file's `_notes`.
- **Ruling inside it:** the strict sole-writer rule overrides fix-spec-2's named answer for Mossdeep's Beldum. The decomp says `until_received`: `hall_of_fame.inc:21` re-shows the ball only while it was never received. But a writer of the blocking flag exists outside the gift's own continuation (the record's `dev.other_writers`), and the scan cannot show that it never re-arms. So `unknown` is ACCEPTED for Beldum, for Rock Tomb (Roxanne's TM; W7 row 16's acceptance pin was loosened to `unknown` and says so in its docstring) and for the other records the rule moved (62 moved from `once` or `until_received`, 13 of them golden "known answers"). The golden list keeps the hand-read value as `truth` beside `unknown`, so a later refinement is checked against it.
- **WHY:**
  - Three adversarial verify rounds each closed their own failures and each found a NEW wrong value in a record nobody had looked at (`08` 2026-10-22). The hunt over 176 gift records did not converge, at about 2.3M agent tokens for rounds 0-2.
  - Every wrong value came from the same shape: a value asserted from the ABSENCE of something the extractor never looked for (a re-arming writer, a special's effect, a trigger-level condition, a possession check), or from a reachability shortcut.
  - Round 3 asserted only what an independent exhaustive scan re-checks, plus the cited tables. The final verifier then ran exhaustive scans over EVERY record and found NO wrong value the AI would read. All 519 table and golden cites hold at the pin.
  - `unknown` is honest and cheap. The AI is a SEASONED player (USER RULING 40) and knows these gifts. A wrong `once` or `until_received` is worse: it tells the AI something false.
- **Rejected:**
  - (a) Relaxing the rule by reachability reasoning ("this other writer ran before the gift, so the gift is once"). That shortcut (`one_shot`, the "spent" rule) produced round 2's wrong values.
  - (b) A fourth round now for a polarity refinement: "a writer that writes ONLY the blocking value cannot re-arm". It is mechanically checkable and would recover the gym TMs, the dolls, the bikes and the fossils. DEFERRED as a low-priority follow-up (04 queue item 5), not refused: it is the right next refinement if the AI ever misses those records.
- **Known weak proofs, said plainly in `07` 2026-10-22:** two verifier rules (h2 and gw-cite) can be deleted with every plant and test green; the `s2_merge` guard is inert at the pin; a Trick House hide flag is treated as a blocker although `addobject` ignores it (9 records, values still true); two physical gates nobody worded (the Slateport museum fee, Shoal Cave low tide).

## 2026-10-23 — Technical decisions of step 5.3 stage A1 (Claude's calls)

- **D1. R5.LEFT_NOT_NEW and R5.CH2_NEW_PLACE keep the honest n (the draws judged) and are WAIVED, each with a reason.** The evidence still prints them `VACUOUS (WAIVED)`, never PASS.
  - **WHY:** each is an ABSENCE guard (it judges each "a new place" draw), the look-around draw is the AI's optional choice, and the spec says A1 must change no outcome.
  - **Rejected:** (a) n = the runs. It prints PASS on zero judged draws, which overstates the evidence. (b) No waiver. It fails a healthy sweep for the AI's choice not to look around.
  - **Kept distinct:** a run that did not happen is not an absence of a draw. Stage B decides whether a sweep must exercise such draws (coverage) and then removes the waivers.
- **D2. The live twins L5.CATCH_ALL, L5.ASIDE_BACK and L5.GO_AFTER_PAGE are DIAGNOSTIC, like their rate twins (#6, #26, #27).** The spec says these properties have no game form, so a debt row could never be paid. Rejected: GRADED plus a debt row (builder A's conservative default).
- **D3. L5.PURITY_ENDED declares inputs `harness` and `ai`, and is a debt row.** Its A2 plan is the harness's own stop record (did the HARNESS stop it, on the frame budget or the wall clock), never the brain's text. WHY: the check reads `exit_reason`, which for a clean exit is the brain's own text.
- **D4. The ledger hash also covers `hands_harness`, `live_step2`, `probe_presses` and `probe_eyes`.** The fix-round verifier found them to be verdict inputs that were unhashed. Consequence, intended: any edit to a hashed file, even a docstring, invalidates a registration made before it.

## 2026-10-24 — Step 5.3 A2's decision addendum: the 39 B1-debt rows decided

- **Decision (the coordinator's call; `ai-research-notes/2026-10-24-step5.3-A2-decision-addendum.md`, revision 2, holds every row):** all 39 rows of `ai_player/gates/b1_debt.json` are decided from the 12-seed development sweep (ledger #39, seeds 1307-1318, 4 per personality): **RE-SOURCE 15, HONESTY 4, REPORTED 9, DIAGNOSTIC 11**. It changes no code and registers no bound. The re-sourcing build (`04` queue item 3 (4)) builds it, and stage B (item 3 (5)) sets the bounds.
- **How it was made:** a drafter, an adversarial critic (revision 1 was refuted on 4 counts), a reviser, and a focused adversarial re-check. The re-check confirmed the first three counts fixed and found ONE failure: the work list is still incomplete (items 14, 15 and 17 have no fault test, items 11-17 no sweep-control line or stated "none", items 2-8, 10 and 12-17 no mutant line). The coordinator ruled this does NOT block: the re-sourcing build's own rules already require a fault test, a control test and a caught deletion mutant for every guard, and the build's plan fills the gaps first.
- **The rules every row was decided by (the addendum's METHOD):**
  - USER RULING 35 binds all of it: the grader judges the AI by the GAME, never by the AI's own record, except an HONESTY check of a claim.
  - R-ABS (a bound on each run): every real run on the passing side, the named control failing in at least one run of each control arm, the bound strictly between the two, both margins stated. R-PAIR (paired by seed or pooled): the real code beats the control in at least 10 of 12 paired seeds and the pooled margin is at least 5 % of the real value; every per-personality share rule is ">= 60 %" (binomial false-FAIL about 1.6-2.6 % at p 0.9, against 11.4 % for ">= 70 %" at n = 6 and 47-52 % for "all n").
  - RE-SOURCE where a named control fails the game form; HONESTY where the row is the AI's own claim, judged against a record the AI cannot write; REPORTED where a game or harness form exists and no control separates it (printed with its controls, never counts); DIAGNOSTIC where there is no game form. A yield RATE is never the only curiosity check; spacing has no game form; a game-read check that no control fails is not registered.
  - The rules were written AFTER the measure's table was seen, which cannot be avoided; that is why stage B grades once, on held-out seeds.
- **WHY the decisions differ from the measure's own table (separates 15, does not 10, no number 8, ruling 6):** the table pooled every personality under one absolute bound and judged loafing on a slice count. Per personality and paired by seed, R5.CH1_TRAINED and R5.NOTRAIN_TRAINED_CHECK separate; R5.SEED_DIVERGENCE, R5.OFF_MOVES_DIVERGENCE and R5.NO_SPEEDRUN fail the paired rule (REPORTED); L5.STALL and L5.OWN_LOSSES are launcher checks whose table numbers were the SWEEP's checks (DIAGNOSTIC).
- **Rejected:**
  - (a) Revision 1's REPORTED for loafing (R5.NO_LOAFING and R5.LOAF), on the claim that no game read fails the LOAF control. The game's push read (`PlaceRecorder.push`) does: the LOAF control reads 4,640 and 4,030 frames (and 3,120), while all 72 real-plan runs stay at or under 1,910. Both rows are RE-SOURCED to it, preferred bound 3,000; stage B decides 3,000 or 4,000.
  - (b) A game training-stint guard "over 40,000 frames in at least one run" for R5.PATIENCE: no control fails it (PATIENCE_OLD is over in 2 of 4 runs, and NOTRAIN, which does not train, in 3 of 12). It is dropped from registration and printed; only the dex half is registered (reached in 4 of 4 PATIENCE runs against 0 of 4 for PATIENCE_OLD).
  - (c) A fixed Trainer floor of 175 grass steps for R5.CH1_TRAINED: overfit to four CH1 seeds, since a STALL2 training run scored 139, under NOTRAIN's 151. Replaced by a paired rule (pooled CH1/NOTRAIN at least 1.3 over the Trainer seeds, and CH1 above NOTRAIN in at least 60 % of them); Story keeps an absolute floor (candidate 70).
  - (d) Re-sourcing L5.PURITY_ENDED: no control in the sweep fails it (all 154 runs ended by the AI), so it is REPORTED, its read guarded by its known-answer unit tests.
- **AMENDMENT to the spec's A1-1 rule** (`2026-10-22-BUILD-SPEC-step5.3-B1-N8.md` line 43: "a HONESTY check must name both `ai` and `game`"): **a HONESTY check names `ai` and (`game` or `harness`).** The truth half may be an instrument of the harness that the AI cannot write. This entry is the log the addendum requires before the build uses the amendment.
  - **WHY (addendum row 16):** L5.PURITY_PRESSES and L5.PURITY_FRAMES are claims about the AI's hands (the pad's press and frame counts), and the only record of the presses that reached the emulator is the harness's instrument (`ai_presses`, twice the pad's presses; `real_frames`). The game has no press count. Without the amendment the purity proof would have to become DIAGNOSTIC and leave the grade, losing the proof that the AI played only through its own pad (USER RULING 35).
  - **Rejected for those rows:** DIAGNOSTIC (it drops the purity proof from the grade) and GRADED on a harness read (with no AI number there is nothing to compare). Confidence MEDIUM: it amends an A1 rule from inside an addendum.
- **Two technical decisions DEFERRED, each decided before anything registers: (1) in the re-sourcing build's plan, (2) in stage B:**
- **Narrows the 2026-10-16 ruling** (which listed a per-run yield floor as graded): after this addendum the grade no longer counts the rest rule, the curiosity yield RATE (chapters 1 and 2), a run's TOTAL loafing (one long stretch IS graded, rows 14-15), seed divergence, the raw frames to the POKeDEX (the battle-free form stays), spins, and who ended a launcher run; each is still PRINTED, and no control fails a game form of it on ledger #39 (the addendum's headline list).
  - (1) The asymmetry between the launcher's game-only achievement checks L5.CAUGHT, L5.HEALED and L5.ITEMS (GRADED with no control, spec line 57) and a game-only "it shopped" (not registered, spec line 102): ONE rule should cover all four. Until then L5.SHOPPED is HONESTY with a floor of one told purchase, and its game form is a printed REPORTED line. The plan must also grade "it shopped" from the GAME (the bag or the money changing), with the told purchases as HONESTY: grading it only from the AI's own told purchases is a grade from the AI's record, which USER RULING 35 forbids.
  - (2) R5.NO_LOAFING's bound value, 3,000 or 4,000 (row 14): stage B's, on the numbers in the addendum's row 14 and stage B plan.
- **Open weak proofs carried to that plan (not decisions):** (a) the ">= 60 %" per-personality share rule's p of about 0.90 counts dependent pairs (31 Catcher pairs share 4 NOTRAIN runs); the unpaired Catcher rate is 13 of 16, at which the rule falsely fails 8-13 %; (b) stage B's LOSE3 rule ">= 60 % of runs reach a third loss" is unargued and falsely fails 17-24 %; (c) "it shopped" graded from told purchases (above); (d) the pseudo-null leaves out LOAF/CH1 (1.067) without saying why.
- **The addendum's one AI-player finding:** R5.NO_LOAFING's only failing run (CH2 seed 1311) is an AI DEFECT, not a check fault: the AI learns a repeating scripted scene one tile at a time (KI-124 in `05`).

## 2026-10-25 — Step 5.3's re-sourcing plan: the addendum's open items decided

- **Decision (in the re-sourcing build's plan note, `ai-research-notes/2026-10-25-step5.3-resourcing-plan.md`; shipped by the build and its fix round, `07` 2026-10-25):** the open items (a)-(f) that the 2026-10-24 entry deferred are decided, from ledger #39's 154 kept run folders (development numbers only). Nothing is registered and no final bound is set: stage B does both, and may move each candidate constant below only within its development margins.
- **(a) The per-personality share rule is ">= 50 %", not ">= 60 %" (`TRAINED_SHARE_MIN = 0.5`; CH1 strictly above NOTRAIN on the same seed).** The addendum's p of about 0.90 counted dependent pairs (the 31 Catcher pairs share 4 NOTRAIN runs). The honest UNPAIRED Catcher rate is 13 of 16 (0.8125), at which ">= 60 %" falsely fails 8.4-12.7 % of 6-7 held-out seeds and ">= 50 %" 1.3-2.7 %, under the about 5 % target. Rejected: dropping the share (the pooled ratio alone can be carried by one heavy seed: Trainer 1308's CH1 373 against 151 is 21 % of the pooled numerator) and keeping ">= 60 %".
- **(b) LOSE3 gets a FLOOR of 2 runs that reached the cap (`LOSE3_REACH_MIN = 2`, a COUNT), not a share.** Reaching a third loss is coverage (the battles' dice), not a property of the AI: 3 of 4 development runs reached it, at which ">= 60 % of runs" falsely fails 17-24 %. What LOSE3 grades is that every run that reached the cap ended within STOP_WITHIN of it. Under the floor the check is VACUOUS, which fails the verdict (no waiver); the floor falsely fails 0.13-0.46 % at p 0.75. Rejected: a floor of 1 (one run is one trajectory) and the share.
- **(c) "It shopped" is GRADED from the GAME: new `L5.SHOPPED_GAME` reads the game's purchase counter GAME_STAT_SHOPPED (game stat 38; the pinned decomp's `BuyMenuSubtractMoney` in `src/shop.c` raises it once per purchase) through `play_harness.py`, and passes when it ROSE from the run's start to its end; a missing read is VACUOUS, unwaived.** The told purchases stay `L5.SHOPPED`, HONESTY (each told purchase must be true by the same read; its no-claim VACUOUS is WAIVED, because the achievement is graded by the game check and an AI that shops without saying so is not lying). WHY the counter: the first form (money fell AND POKé BALLS rose) misjudged three ways (a Catcher that buys 5 and throws 7, a run that wins more prize money than it spends, and, a false PASS, a whiteout's lost money plus an item-ball POKé BALL). ⚠ The counter read has NOT yet been checked against a live launcher run. Rejected: the addendum's row 19 (a REPORTED game line plus a HONESTY floor of 1, which graded the AI's word as the achievement), a money drop matched by a bag rise in one sample (the launcher has only start and end truths) and a mart-map condition (standing in a mart is not buying).
- **(d) The NO_SPEEDRUN_DICE pseudo-null omits LOAF/CH1 (1.067), GREEDY and NOHINTS; the bound stays 1.05 and the pseudo-null is {DEADREST 0.977, STALL1 1.028, STALL2 1.021}, a 0.022 margin.** A pseudo-null must differ from CH1 in a knob that does not change the time spent on curiosity, because curiosity time is what the check measures; LOAF's edit IS its curiosity (+48 calm slices, +41 loaf slices over 12 seeds), so its 1.067 is the check MOVING with curiosity time, not null spread. Rejected: raising the bound to 1.07 to clear LOAF (it would cut the margin to the real pooled 1.124 from 0.074 to 0.054 and sit above the real Catcher quarter's 1.060, for no null reason).
- **(e) ONE rule for achievement checks and bound checks.** An ACHIEVEMENT check (a game read that an event happened in the run, at a threshold of "at least one") is GRADED with no sweep control, provided its read has a known-answer FAULT test both ways and a call-deleting mutant the suite catches. A BOUND check (a threshold on a quantity that healthy and broken code both produce) needs a named control that fails it. WHY: an achievement's null (nothing happened) can be built by a fault test; a bound's null is unknown without a control. So L5.SHOPPED_GAME, L5.CAUGHT, L5.HEALED and L5.ITEMS are GRADED under one stated rule. Rejected: REPORTED for all four launcher checks (it drops the launcher's game proofs from the grade).
- **(f) The work list's gaps are filled** (plan section (f)): every guard has a fault test, a control test and a caught call-deleting mutant, or a stated "no sweep control" (a launcher check, which the sweep never runs).
- **R5.PUSH_PATHS_AGREE (work-list item 16(b)) is REDEFINED, and this SUPERSEDES the addendum's text** ("compare the matched STRETCH ... do not compare the two verdicts at the bound"). The matched-stretch premise is refuted: the AI's longest push and the game's longest are the SAME stretch (same presses, windows within 10 frames) in only 86 of 152 runs. The check now compares the two paths' VERDICTS at each graded push bound (PUSH_MAX 4,000 and LOAF_FRAMES_MAX 3,000): they agree unless the verdicts differ AND at least one value lies outside `PUSH_AGREE_BAND` = 5 % of the bound (the game path adds up to one 10-frame sample per free/not-free transition). On ledger #39 that reads 154 of 154 agree (the old rule's one split, LOAF 1310 with 3,950 against 4,030 at 4,000, now agrees); a disagreement far from the bound (AI 4,000, game 10; or AI 4,300, game 3,500) still splits. Rejected: matching stretches (refuted), a one-sided tolerance on matched stretches (no stretch identity in 66 runs) and re-typing the check (an honest comparison exists).
- **New and re-typed checks.** New: HONESTY `R5.LOSE3_WORD` (the AI's word that it stopped, against the game), DIAGNOSTIC `R5.BLOCKED_REACH` (the addendum's "the reach becomes DIAGNOSTIC text") and GRADED `L5.SHOPPED_GAME`. `R5.CH2_NOBATTLE`, `R5.NO_LOAFING`, `R5.LOAF`, `R5.PUSHING` and `R5.BLOCKED` are graded from the game alone, so `b1_debt.json` is EMPTY (39 of 39 rows left the debt) and no GRADED check reads the AI's own records. A check that reads the AI stays only as HONESTY (a claim judged against a record the AI cannot write) or DIAGNOSTIC.
- **Candidate constants (unregistered):** `LOAF_FRAMES_MAX` 4,000 to 3,000 (the addendum's preferred candidate, row 14; its quantity is now the game's push), `CH2_NOBATTLE_RATIO_MIN` 1.15 to 1.05 and `NOBATTLE_RATIO_MIN` 1.02 to 1.05. `PUSH_MAX` 4,000 and `BLOCKED_HITS_MIN` 1 are unchanged.
- **Open weak proofs carried to stage B or earlier (none changes the grade on ledger #39):** a MISSING game push read becomes 0 and is counted, never VACUOUS; `no_battle_pairs` rounds its ratio to 3 decimals before the `> 1` test; DIAGNOSTIC `L5.NO_LOAFING` applies the new 3,000 bound to the AI-windowed total; GAME_STAT_SHOPPED has never run against a live launcher; the synthetic differential cannot show PUSH_PATHS_AGREE flips (verified on #39 instead); LOSE3's control STOPDEAD reads VACUOUS (1 run against the floor of 2), so stage B needs 2 or more STOPDEAD runs that reach the cap.

## 2026-10-25 — Step 5.3's grader: a MISSING game read is left out of a check and named, never counted as a value

- **Decision (the small weak proofs, `07` 2026-10-25):** where a run has no game push read, the push checks (R5.NO_LOAFING, R5.PUSHING, R5.LOAF, R5.BLOCKED, R5.PUSH_PATHS_AGREE) leave that run out of their n and the first four name it in their text; every read missing reads VACUOUS (n 0, which fails the verdict unless waived). A read of no stretch at all stays a real 0. The same rule `L5.SHOPPED_GAME`'s missing counter already follows.
- **Why:** the old `or [0, 0, 0, 0]` let a run whose harness read nothing PASS every 'under the bound' check silently, the opposite of what a missing instrument means.
- **Rejected:** counting a missing read as a FAIL of the run (a harness fault is not the AI's play, and it would make a control 'fail' on no evidence); keeping 0 (a silent pass).

## 2026-10-27 — Step 5.3 stage B step 1: phase 2's STOP and STOPDEAD also replay LOSE3's runs; a re-grade judges phase 2 by the rule its sweep was played under

- **Decision (`ai-research-notes/2026-10-26-stageB-stop-runs-design.md`, DECISION (2026-10-27), option B):** LOSE3 leaves `NO_PHASE2`, so phase 2's STOP and STOPDEAD replay LOSE3's forced-loss runs as well as every natural loss, through one rule (`rate_step5.phase2_lost`) that both playing and grading use; the replays are matched by identity (base plan, seed); the checks' texts count replays by source (natural or forced).
- **Why:** natural losses have become rare (per sweep: 3 in 20 seeds on the graded ledger #34, 1 in 12 on #39, 0 in 48 DEADREST-only seeds on #40), so R5.STOP and R5.STOPDEAD might get no run in a graded sweep and LOSE3's control STOPDEAD could not reach its floor of 2. A STOP replay of a LOSE3 run still proves the stop: LOSE3 edits only the battle decider, upstream of the game's loss, and the stop rule reads the game's loss count, never why. The development check (ledger #41, seeds 1367-1384) gave R5.STOP and R5.STOPDEAD 6 runs each, and LOSE3's control FAILS in 6 of 6.
- **Rejected:** (A) a `LOSE3DEAD` phase-1 control (it fixes LOSE3's control only); (C) waiving R5.STOP and R5.STOPDEAD (a check that cannot run proves nothing). The old exclusion ('losses that are the fault itself', commit 75c2080a) had no recorded reason.
- **And (the verifier's FAILURE, fixed by the coordinator):** a re-grade of a sweep played BEFORE the rule judged it by the new one and read FAIL for replays it was never asked to play (ledger #39). `FORCED_REPLAYS_FROM_ENTRY = 41`: a re-grade of an earlier entry judges phase 2 by the rule it was played under (natural losses only), and says so on an evidence line. Rejected: inferring the rule from the rows (a crash mid-phase-2 would look the same).

## 2026-10-27 — Step 5.3 stage B step 3: the final bounds are the re-sourcing build's candidates, all 20 kept

- **Decision (`ai-research-notes/2026-10-27-step5.3-stageB-bounds.md`, DECIDED after an adversarial critic):** every graded bound the re-sourced step-5 checks read keeps its candidate value; each sits between the real code's worst development run and its named control on ledgers #39-#41 with the margin the note tabulates; every control FAILS its bound (or fails by construction, now labelled for R5.OFF_BEELINE too; R5.LOSE3's control reads VACUOUS on #39, which predates the stop-runs rule, and FAILS 6 of 6 on #41); no STOP. `LOAF_FRAMES_MAX` stays 3,000, not 4,000 (at 4,000 one of LOAF's failing runs, 4,030, sits inside the game path's sampling band).
- **Rejected:** moving any bound toward the real code's worst run (overfitting: ordinary seed-to-seed spread would then fail the real code on held-out seeds); registering a bound whose control could not be expected to fail it in 20 seeds (none).
- **Accepted risks (the critic's weak proofs, in the note):** R5.OFF_BEELINE's false-FAIL at 20 seeds is not estimable from 12 seeds; PATIENCE's could be about 12 %; the chance that the real code fails at least one check by chance is not stated. A graded FAIL is read check by check, never retuned on the held-out seeds.

## 2026-10-27 — Step 5.3's graded result is FAIL on 3 of 38 counted checks: accepted as information, not retuned; step 5.3 is done

- **Decision:** the graded sweep (ledger #42, held-out seeds 961-980) stands as recorded: verdict FAIL on R5.NO_LOAFING, R5.PUSH_PATHS_AGREE and R5.NOTRAIN_TRAINED_CHECK. No bound, check or code changes on these seeds (the spec's rule and the bounds decision of the same day). Step 5.3's purpose, a grader that judges the AI by the game, is met for the GRADED checks (whether KI-126 is a grader-side defect is open); its findings go where they belong: KI-125 (an AI weakness the loafing check caught), KI-126 (a split between the two push records, cause not determined), and the training check's limit (the game's grass steps include travel) for a later grader step.
- **Rejected:** retuning the bounds that failed (LOAF_FRAMES_MAX at 4,000 would have passed NOHINTS 963's 3,080; the Story floor above 75 would have passed NOTRAIN 961): that is fitting the bound to the held-out seeds; and re-running on new seeds to get a PASS (a second graded sweep is a new registration for a changed grader or AI, never a retry).

## 2026-10-27 — USER RULING 46: the launcher's "it shopped" means ANY purchase, not only POKé BALLs

- **The question** (`07` 2026-10-26: all 96 purchases in ledger #40 were POTIONs, because OLDALE's mart sells no POKé BALL before the POKéDEX): does the launcher's achievement "it shopped" mean any purchase, or POKé BALLs only?
- **The user's words:** "Any purchase really if you think thats a good idea". Claude agreed: buying a POTION is as human a use of a mart as buying a ball, and early in the game a ball cannot be bought at all.
- **What it means:** `L5.SHOPPED_GAME` (the game's purchase counter, GAME_STAT_SHOPPED) already counts any purchase and stays as it is. The HONESTY check `L5.SHOPPED` now judges only told BALL purchases ("done; POKé BALL in the bag"); it follows the ruling and judges EVERY told purchase ("done; <ITEM> in the bag ..., money A -> B") against the counter, and the launcher's achievement text says "something bought". A small change, with a fault and a control, before the next live_step5 grade.
- **Rejected:** balls only (it would fail every early-game run for a mart that sells none).

## 2026-10-27 — USER RULING 47: use the $250 cloud credit before it expires (2026-11-04) if a cloud job is billed to it; measure that first, and shelve it if the weekly meter pays or the setup costs too much

- **The user's words:** "If we could use the cloud credit before it expires, that would be great! If it proves to cost too much just to set it up, we can backburner it and work on it later before they expire."
- **What is known (`07` 2026-10-16, `06` 2026-10-15 cloud phase):** after the one medium cloud job (KB1), the credit card still read $250 while the weekly meter rose, so cloud jobs may be billed to the WEEKLY plan, not the credit; local work ran at the same time, so it was never a clean measurement. The 2026-10-15 rule stands: if the weekly meter carries the cost, the cloud phase stops.
- **The plan:** right after the weekly reset (2026-10-28), with nothing else running, ONE small cloud job on the existing worker `pokebot-cloud-worker` (its connectors checked empty first), the user reading the credit balance and the weekly meter before and after. If the CREDIT pays: queue useful no-emulator jobs through 2026-11-01 (decomp recon for chapters 3-4, the knowledge base's next slices, reviews), each small, pushed per step, merged only after a local check. If the WEEKLY meter pays: shelve it, and revert by 2026-11-01 as planned (disable the routine, keep the branches).
- **Supersedes** the standing instruction "cloud jobs stay paused" for this measurement and, if the credit pays, for the jobs after it.

## 2026-10-28 — USER RULING 47's measurement: the $250 credit did not move, and the official docs say the weekly plan pays for cloud jobs, so the cloud phase is SHELVED and the routine disabled

- **The measurement (the plan of USER RULING 47):** right after the weekly reset, one small cloud job, CH3-RECON (chapter 3's maps from the decomp; run 5:36 AM, about 2 minutes, 14 turns, Sonnet 5.5, pushed to `claude/ch3-recon-ux45kq`). The user's readings: before, "$250 cloud credit and 0%weekly usage, 4% current session usage"; after (8:01 AM), "Weekly usage: 1% / Session usage: 5% / Cloud credit: $250". This session's own local use between the readings: about 0.2% of a week (`tools/usage_audit.py`, an ESTIMATE: 0.5% to 0.7% since 12:00 UTC). The meter shows whole percents, so the 0 -> 1 move can be the local work alone; the credit did not move.
- **The deciding source (verified here, not only by the research agent):** the official page https://code.claude.com/docs/en/claude-code-on-the-web says a cloud session "counts toward your plan's usage limits alongside the rest of your Claude and Claude Code usage, and there's no separate charge for the cloud VM", and that scheduled and triggered runs (routines) "each run as a cloud session". With the credit unchanged after both cloud jobs (KB1 on 2026-10-16, CH3-RECON today), the weekly meter pays.
- **Decision (the ruling's own rule: "If the WEEKLY meter pays: shelve it"):** the cloud phase is SHELVED. A cloud job costs the same weekly allowance as local work and adds a check-before-merge, so it saves nothing. The routine `pokebot-cloud-worker` (`trig_011hasDZP5PDcUsyA5S4C3B2`) is DISABLED now (8:04 AM), not on 2026-11-01: no job remains for it. Its branches are kept; CH3-RECON's output is a NOTE until it is checked against the pinned decomp, before chapter 3 uses it.
- **Rejected:** a second, larger measuring job (the documentation answers the question, and the meter's whole percents could not read a small job anyway); running the weekly limit out to see whether the credit applies after it (it could draw the user's $50 extra credit, which the user keeps for emergencies; the official pages do not say what the $250 pays for). **Do not re-open without the user.**

## 2026-10-28 — L5.SHOPPED, built for ruling 46: a told purchase of ANY item, and one counted purchase per told purchase

- **What the ruling asked** (`06` 2026-10-27, USER RULING 46): the HONESTY check `L5.SHOPPED` judges every told purchase, not only POKé BALLs.
- **Two choices made in building it:**
  1. **A told purchase is a mart report whose own bag count ROSE** (`hands/menus.py` mart_buy tells "done; <ITEM> in the bag <before> -> <after>, money ..." whether or not the purchase went through). A report whose count did not rise claims nothing; with `before` unread, an `after` above 0 claims (an unread `after` never does). Rejected: every "done" report (it would call a failed purchase a lie, though the report states the failure).
  2. **The game's counter must rise at least once per told purchase** (GAME_STAT_SHOPPED rises once per purchase, `src/shop.c` BuyMenuSubtractMoney, pinned decomp 731ad5b). The old check passed on ANY rise, so its own words "each must be true" were not checked: two told purchases with one made passed. Rejected: any rise (the old form).
- **Proof** (`ai_player/evidence/2026-10-28-ruling46-SHOPPED-PROOF.txt`): fault tests and controls in `test_step53_rs.ShoppedTests` (a POTION lie FAILS, where the ball-only match read VACUOUS; two told with one counted FAILS; non-purchase tells are not counted); seven mutants of the new guard, each CAUGHT, and the unmutated copy passes (a scratch copy, fresh bytecode); the compiled pattern matched all 9 real mart-report lines in the evidence and fixtures (3 distinct reports: a POKé BALL purchase and two POTION purchases) and none of 143 other lines. The Tier 1 review found the first build counted "None -> 0" as a claim; fixed and tested.

## 2026-10-28 — USER RULING 48: games that finish before a crash COUNT toward the tuner's ranking; the 12 games lost on 2026-10-17 (ai0031) are NOT added back

- **The questions** (the E2 + O8 build spec, `ai-research-notes/2026-10-28-E2-O8-BUILD-SPEC.md` §6): U1, when the PC dies mid-cycle, should the games that finished before the crash count toward the strategy ranking like games from a normal cycle (which also marks that cycle's tested Claude-suggested proposals as done)? U2, should ai0031's 12 lost games be recovered from its `raw.zip` into the ranking?
- **The user's answers:** U1 "Yes, count them (Recommended)"; U2 "No, leave them out (Recommended)".
- **What it means:** E2's recovery case appends the recovered rows to `runs.jsonl` by today's rules (the spec's default, §2a INVARIANT (a)); no backfill tool is built for ai0031 (its games were played 11 days and 20+ cycles ago, and recovering them needs a one-off step).
- **Do not re-ask** whether crash-recovered games count (yes) or whether ai0031's games are backfilled (no).

## 2026-10-28 — USER RULING 49: PAUSE the project at the end of the bot tuner's round ai0053 (about 4:28 PM 2026-10-28): park the tuner, switch off its Windows auto-start, and wrap up for a cold start; resume only when the user says so

- **The user's words:** "when I tell you to safely pause or park the project, I want you to safely park the trainer and pause the windows restart setup where it turns itself on automatically when the pc gets turned back on until I tell you we are resuming everything, this also includes safely wrapping up everything in the local files and repo so a cleared context chat spun up in this project can continue where we left off"; then "4:28pm today works for me ... can you schedule this safe park/pause for that time but with safety checks ... it would need to be intelligent and robust to ensure that everything is parked/paused whenever its safe to do so".
- **The choice:** park at a ROUND BOUNDARY with the tuner's own documented off switch, `ai-agent/STOP` in the clone (git-ignored there), placed at 11:16:22 AM. `learner.py` `loop()` reads it only at the top of a cycle, before `auto_update`, so the running round finishes and is recorded, the learner exits 0, `run_agent.ps1` does not restart it, and a later logon exits at once. Then the three Windows tasks are DISABLED, never deleted: `Pokebot-AI-Learner-Autostart`, `Pokebot-Ops-Watchdog`, and `Pokebot-Ops-Backup` after one final backup verified byte for byte (a failed backup leaves the nightly task ON).
- **Rejected:** parking at once (the E2 + O8 build was mid-review); one more overnight round so E2 + O8 runs live before the pause (the park would end about 4:30 AM 2026-10-29 and need a session then); stopping mid-round (the running code records games only at a round's end, so that round's games would be lost). Accepted: E2 + O8, if on `main` by then, first runs live at the resume (the learner updates at its first loop).
- **Do not** delete `ai-agent/STOP`, re-enable the three tasks, or start the tuner until the user says to resume; do not re-ask when or how to pause.

## 2026-10-28 — E2 + O8 built: what the journal, the recovery case, the `.bak` check and the crash-loop breaker chose, and where the build departs from its spec

- **Context:** backlog E2 + O8 (`#28-trainer-improvements` item 1), built to `ai-research-notes/2026-10-28-E2-O8-BUILD-SPEC.md` after USER RULING 48; the evidence is `ai-research-notes/2026-10-28-E2-O8-BUILD-EVIDENCE.md`.
- **The journal and the recovery case (spec §2a), chosen:** the learner, not the batch runner or the bot, journals each finished game to `runs/<tag>/games.jsonl` (polled every 300 s; a log unmodified for 120 s; never a lane's newest log). A cycle with no copied logs is recovered from the lane profiles, with the journal's whole-parse record swapped in for each matching log, and its rows enter the ranking by today's rules (USER RULING 48). **Rejected:** appending games to `runs.jsonl` mid-cycle (more torn-write exposure; half cycles visible to the ranking); journaling in the batch runner or the bot (outside `ai-agent/`); the profiles alone (a power cut can cut a log's tail, while the fsynced journal was parsed whole).
- **The `.bak` check (spec §2b), chosen:** `state.json.bak` is restored only when its `cycle` is at least the newest started cycle (`runs/aiNNNN` or `endless-aiNNNN-*`, which both survive archiving); otherwise `StateUnreadable` names the gap and the breaker hands it to a person. **Rejected:** a save counter (old code copies the key unchanged, so it cannot reveal a rollback); an mtime rule (it refuses safe cases).
- **The breaker (spec §2c), chosen:** 5 crashes in a row, counted in `data/crashes.json` outside `state.json`. On a crash it first fetches pushed code and restarts into it if `test_agent.py` passes, so a fix or a revert can reach a crash-looping tuner. The count resets when a batch launches, on ATTENTION and on a clean exit. `run_agent.ps1` is unchanged.
- **Departures from the spec, accepted:** (1) `state.json.bak` is replaced through its own alias `_os_replace_bak`, because an existing check counts `_os_replace` calls exactly; (2) the shape check accepts a MISSING `cycle` key (a present one must be an int), because an existing fixture saves none; the `.bak` is still restored only with an int `cycle`; (3) a cycle row gains `recovered` only when the recovery produced at least one record; (4) the top ATTENTION check returns 0 without clearing the count (the in-loop ATTENTION return clears it); (5) the review's F4: `games.jsonl` is deleted only when every journaled game is in `runs.jsonl`, and otherwise kept as `games.jsonl.kept`; (6) the guards became small patchable helpers, so each FAULT arm can remove one.
- **Left open, by choice:** the review's F5 (after a rollback to pre-O8 code at count n < 5, a redeploy's crash loop reaches ATTENTION after 5 - n crashes). It errs toward stopping and asking, and a time window would change the spec's "in a row" rule. F6, the deploy-gate flake, is KI-127.
- **Deploy timing:** as the spec planned, at the next cycle boundary (the end of round ai0053, about 4:28 PM 2026-10-28): USER RULING 49 would have delayed it to a resume, and USER RULING 50 cancelled that park the same day.
- **One commit on `main`:** the branch's two commits (`b3a54290`, the build; `300ab630`, the fix round) were applied with `git cherry-pick --no-commit` and committed together with the docs, one commit for the item.

## 2026-10-28 — USER RULING 50: the PARK is CANCELLED; the user continues this project, and the safe park/pause stays available for when the user asks

- **The user (2026-10-28, just before 2:26 PM), verbatim:** "I have changed my mind, I do not want to work on the other project and park this one, I would like to continue working on this program understood? but I do want the safe pause/park feature in the event that I do want to safely park/pause working on the program understood? continue what you were doing but note that I do not want this to be paused/parked anymore until I say otherwise!"
- **Ruling:** USER RULING 49's park is cancelled, and work continues in the build order. The park stays a FEATURE, used only when the user says park or pause: the STOP file before a cycle boundary, a watcher that verifies the stop, then the three tasks switched off after a verified backup; RESUME reverses it (`04` PARK).
- **Done:** the STOP file was deleted at 2:26:36 PM. The watcher exited 30 at 2:26:38 PM ("the STOP file was removed: the park is CANCELLED; nothing was changed"). The three tasks had never been switched off (read after: `Settings.Enabled` True for all three), and the tuner kept running round ai0053 (PID 22464, its lock held, 12 lanes).
- **Consequence:** E2 + O8 deploys as its spec planned, at the end of round ai0053 (about 4:28 PM), if `test_agent.py` passes in the clone.
- **Chosen next (technical):** the park and resume become one committed, tested tool before R5, because today the watcher exists only in a session's scratch (its source is kept in `ai-research-notes/2026-10-28-PARK-EVIDENCE.md`). **Rejected:** keeping the scheduled park (the user no longer wants it); dropping the park tooling (the user wants the feature).
- ⛔ **Do not park or pause the tuner or the project (no STOP file, no disabled task) unless the user asks; do not re-ask whether to pause.**

## 2026-10-28 — The park tool (USER RULING 50): how `tools/ops/park_tuner.py` parks and resumes the bot tuner, and where it departs from its spec

- **Built:** `tools/ops/park_tuner.py` (`status`, `park`, `resume`) and its gate `tools/story-dev/selftest_park_tuner.py` (in `run_gates.py`). Spec `ai-research-notes/2026-10-28-PARK-TOOL-BUILD-SPEC.md`; the build, the sweep, the review and the fix round: `ai-research-notes/2026-10-28-PARK-TOOL-BUILD-REPORT.md` (the build departs from the spec in the ten places of its section 8.3; the code wins).
- **Chosen:** every command is a DRY RUN unless `--apply`, and `status` writes nothing. **Rejected:** acting by default (a cold session's first try would park a tuner the user wants running).
- **Chosen:** no `--now`: a park always waits for the round's end (STOP is read only between rounds), and the tool cannot kill or stop the learner, a batch or a lane, or register or delete a task (an AST check in the gate); the one thing it ends is `resume`'s old, proven-idle autostart window, through `Stop-ScheduledTask` (unmeasured live on the real task: watch the first resume). **Rejected:** a forced stop (it loses the round's games).
- **Chosen:** PARKED is read from each task's `Settings.Enabled`, never its State. **Why (measured 5:53 PM on a throwaway task, `probe_stop_disabled.ps1`, in the build report):** disabling a task does not end its running instance (State stays Running, Enabled False), so a parked tuner whose window is still open reads State Running; Stop-ScheduledTask does end a disabled task's running instance.
- **Chosen:** resume switches the three tasks ON first, still under STOP, then ends an idle old tuner window, deletes STOP and starts the task; it ends the old window ONLY while STOP exists, and places a STOP of its own for those seconds when there is none. **Why:** `run_agent.ps1`'s 10-minute crash wait looks exactly like an idle window, and a learner start racing the window's end would be killed or orphaned; with STOP present a racing start exits at once (the review's F8). **Rejected:** accepting that race (the build's open question 2).
- **Chosen:** `resume --apply` also CANCELS a `park --apply` still waiting for its round: it deletes STOP, the waiting park ends CANCELLED and releases its lock, and the resume goes on. **Why:** otherwise a park started by mistake could be stopped only by killing a process (the review's F1, MAJOR).
- **Chosen:** resume's "the tuner still runs" step is chosen by the clone's LEARNER, never by any tuner-like process, and a `learner.py run` counts as the clone's only under its window or through its agent.lock (the review's F2, MAJOR, and F3).
- **Chosen:** a clean stop needs no LIVE learner holding agent.lock (a dead PID's lock is a crash leftover), and two STOP exits that log no STOP line count as clean: the exit-3 restart, and a silent exit between rounds. **Rejected:** a learner change to log every STOP exit (out of scope; the learner deploys itself).
- **Chosen:** the status exit codes stay as built: 0 RUNNING, 61 PARK PENDING, 62 PARKED, 63 PARTLY PARKED, 64 STOPPED NOT PARKED, 65 INCONSISTENT, 50 unreadable. `--clone` is resolved to all its spellings (relative, 8.3, `\\?\`, a junction), not refused under `--apply`.
- **Chosen:** the gate reads `ai-agent/learner.py`'s own source (test X), so a learner that rewords a log line the tool waits for turns the gate RED. **Why:** the learner deploys its own code, so a silent drift would break every park while the selftest stayed green (the review's F10).
- ⛔ **Run `park --apply` or `resume --apply` only when the user asks to park or resume (USER RULING 50).** No `--apply` has run live: the first park and the first resume should be watched.

## 2026-10-29 — R5 (a free screen before "done"): what the settle chose, the rulings on the build's open questions, and where the build departs from its spec

- **Built:** `ai_player/mode.py` `_settle_before_done` (called when the target's proof holds, before the unchanged done check), `_settle_frames` (its frames, budget-aware), `_end_screen` (every "done" and "stuck" end records its screen; the frame budget's cut in ordinary play, made by `_bounded`, still has none), `DONE_SETTLE_ROUNDS = 6`, `DONE_BUDGET_MARGIN = 2`. Spec `ai-research-notes/2026-10-28-R5-BUILD-SPEC.md`; the build, the sweep, the review and the fix round: `ai-research-notes/2026-10-28-R5-BUILD-REPORT.md`.
- **D1 kept:** R5 alone, before R6's screen ladder. **Why:** R6 is not built, and R1's save needs a free screen now. **Rejected:** building R5 inside R6.
- **D2 kept, as a helper:** the settle runs BEFORE the done check, whose two lines are byte-identical (G226's anchor); `_play` gains one call (G347). **Rejected:** settling in `_play_end`, a plain function that cannot let frames pass.
- **D3 kept:** a screen that will not free still ends exactly "done: <target> reached" and SAYS so (a tell, an `end_screen` note, the end record). **Rejected:** ending "stuck": `live_step5`'s HONESTY check reads a stop over a proof that holds as a lie.
- **D4 and U1 AMENDED (build deviation 1, ratified):** on a FREE look the settle takes the loop's own decision pause (`Pacing.think`, 14-45 frames) and one more look before "done": one free look is not a free screen. **Why (measured):** on the tree before R5, `ch2_dad` ended on a ONE-frame free read (DAD's warp to PETALBURG CITY; WALLY's tutorial locks the controls on the next frame) that the AI's own `nav_free` reads free, so the spec's settle, gated on `not nav_free`, would not have run there (ledger #43). The pause is what discriminated in both live A/Bs (#45 and #49). **Cost:** the decision's pause on each free look the settle takes: one on a free end (measured 16 to 44 frames), three on the measured `ch2_dad` chain (60 to 112 frames in all). PL-1 (never idle while a screen waits for a press) holds: the pause is taken on a free screen. **Rejected:** (a) a map-change window (the measured gap, 39 frames, exceeds `SETTLE_FREE`'s 30, so it needs a new constant, and it covers only warps); (b) no pause (the natural fixture then does not discriminate, and the run still ends mid-scene).
- **D5 AMENDED:** the end record is a guard for the reader, never evidence, and no grader counts it: `report["end_screen"]` holds `free` (`nav_free`), `held_by` and `frame`; a "done" end adds `played_out` (True only when a screen was PLAYED out; renamed from `settled`, which read as "the screen settled"), `settle_frames`, `paused`, `settle_stop` and `passed`. It is read FIRST in `_play_end`, before the wait and push watchers close (the sweep's S56, pinned by G361), so frames that passed after the loop's last look with a box waiting reach the wait record. ⚠ It cannot see the measured failure: it read all 8 OLD ends of the two A/Bs free, which the game held not free.
- **D6 REWRITTEN (the review's R5-F1):** the settle's frames count against `settings.frames`, and the settle never lets the brain's bound cut a reached target: it hands frames on only while more than `DONE_BUDGET_MARGIN` (2) are left, then stops, says so (a tell, an `end_screen` note "budget", `report.settle.budget` True) and the run ends "done". **Rejected:** the build's first claim that a budget end is "reported, not hidden": it had no end record and no end note, and HONESTY read it as a lie.
- **D7 kept:** the play-out before a goal switch is the loop's own, unchanged (U3 CONTROL). **D8 kept:** no save here; the save is R1's.
- **D9 NEW (the review's R5-F5):** a MAX_LOSSES-th loss inside the settle ends the settle at once (no pause, no further play-out), its stop the loop's MAX_LOSSES reason, and the run ends "done" (D3). **Rejected:** fighting on to the settle's bound (a game loss past the cap); ending "stuck" (HONESTY). ⚠ **OPEN, unreachable on today's targets:** `rate_step5`'s R5.LOSE3_WORD (and R5.STOP, in its MAX_LOSSES-1 copy) expect the stop string whenever the game recorded the capped loss, and a capped loss inside a settle reads "done". Rule on it if a STOP or LOSE3 plan ever reaches a settle.
- **RULED (the builder's question 4): "done" for an intermediate target** means the target's proof held and what was on screen was then played out. The milestones the story passed meanwhile are told and kept in `passed`: a `ch2_dad` run's settle plays WALLY's tutorial and passes `ch2_wally`, because a person cannot stop mid-scene. `report["milestones"]` and the MILESTONE lines, which the graders read, are unchanged. **Rejected:** ending at the one-frame free read (mid-scene); naming the last milestone passed in the reason (HONESTY compares the exact target).
- **Chosen:** the harness's free read stays a TOOL, `ai_player/gates/probe_end_screen.py` (RAM, held over 10 more frames, an input check, a 5-case selftest; it needs the emulator and the ROM), not a lane suite. **Rejected for now:** a live R5 check in the regression lane (each `ch2_dad` run takes 5 to 9 minutes); `test_r5_the_measured_ch2_dad_chain_takes_three_rounds` pins the logic in the unit harness.
- **Chosen:** the live A/B was RE-RUN on the FINAL tree (ledger #49 and #50, new held-out seeds 5361-5365), because the fix round changed the settle after the first A/B (#45 and #46) had run. Its grader reads `played_out`; its other criteria are #45's.
- **Not done (the review's R5-F4, optional half):** the call census still does not trace calls inside an ADDED function; changing it widens a shared gate for every later round and needs its own fault test and a ruling. R5's own such calls are covered by revert mutants (G349, G352, G353, G359).

## 2026-10-29 — KB2's input hashes ignore line ends: folded in the hash, not fixed by an `eol` attribute

- **The defect** (found by R5's worktree build, `07` 2026-10-29): `ai_player/gates/extract_world.py` recorded each input's RAW-byte sha256 in the world files' `_inputs` headers, and two inputs have no `eol` attribute (`ai_player/gates/campaign_skeleton.json`, `ai_player/knowledge/milestones.json`), so a checkout whose git wrote their line ends another way failed `extract_world.py --check` and `test_kb2` (measured: a copy with the skeleton CRLF and the milestones file LF read `CHECK FAILED, differ/missing: bosses.json, campaign.json`).
- **Chosen:** `load_json` hashes the input's text with its line ends made "\n", the rule `rate_step5.file_sha256` and `tools/make_chapter_pack.py` already follow. One hash on every checkout; `campaign.json`'s `milestones.json` hash moved from the CRLF bytes' `0ccf6193` to `3320eed0`, and the 24 chapter packs' digest of `campaign.json` with it. Pinned by `test_kb2`'s `test_input_hashes_do_not_depend_on_line_ends` (LESSONS PR-14).
- **Rejected:** `text eol=lf` attributes on the two inputs (the KB1 way, which protects the OUTPUTS): it holds only after every checkout re-normalizes, it would rewrite `milestones.json`'s bytes here, and a new input without the attribute would bring the defect back. Folding in the hash holds for any input.
- **Not affected:** the decomp's own reads. Its `.gitattributes` makes its `.c`, `.h`, `.inc` and `.s` files LF, and its clone has `core.autocrlf` false.
