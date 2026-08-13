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
