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
