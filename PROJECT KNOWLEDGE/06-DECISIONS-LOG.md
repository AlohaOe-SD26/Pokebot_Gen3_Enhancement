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
