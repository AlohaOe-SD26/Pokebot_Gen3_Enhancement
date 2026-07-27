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
