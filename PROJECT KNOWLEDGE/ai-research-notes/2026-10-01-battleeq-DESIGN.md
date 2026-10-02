# 2026-10-01 — `#27-battleeq` (KI-108): DESIGN + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** The fix makes every `get_battle_state()` caller in a frame see what the FIRST
caller sees, which is fresh memory. It does NOT:
- make a site correct that is wrong as a first caller (`battle_move_replacing.py:149` is KI-115's, see below);
- cover a memory write made WITHIN a frame (the early return at `battle_state.py:809` is unchanged).

**Headless, every ACTING site is already a first caller.** So an A/B on ordinary battles is identical by construction
at those sites: it is a regression check, never evidence that the fix works. The evidence is the offline gate and two
live arms that put a second caller in front of the subject on purpose.

## Recon (three Claude agents, one message; NOTES, verified below where load-bearing)

The angles: an audit of our callers, an adversarial refutation of "the fix is behaviour-neutral", and a test plan.
**Verified by the coordinator at FILE:LINE:**
- `BattleState.__eq__` (`sandbox-pokebot/modules/battle_state.py:249-263`) compares 9 of the 11 constructor fields
  (`:223-247`). It omits `_battler_party_order` and `_current_turn`. There is no `__ne__` and no `__hash__`.
- `get_battle_state()` (`:808-827`) returns the cached value when `age_in_frames == 0`. Otherwise it builds a new
  object, assigns it to the cache, and returns the NEW LOCAL object.
- The cache setter (`modules/state_cache.py:293-298`) keeps the OLD object when `old == new` and only calls `checked()`.
- ⇒ The first call in a frame is fresh. Every later call in that frame gets the cached object. Its 9 compared fields
  equal a fresh read, but its order and turn date from the last frame in which a compared field changed.
- Nothing reads the cache item's stamps: the only reader of `state_cache.battle_state` is `battle_state.py:809-810`.
  So replacing the cached object more often has no side channel. No code compares `BattleState` objects or relies
  on their identity (the agents' greps; the coordinator re-ran the stamp grep).
- Upstream (the mirror) is byte-identical in both files. Upstream HEAD has never fixed it.

**Where a second caller comes from (agents, VERIFIED by them; frame order `libmgba.py:584, :604`, `main.py:143-148`):**
- **The GUI debug Battle tab** (`gui/debug_tabs.py:427`) runs right after `run_frame()`, so it is always the first
  caller of its frame, and the bot then reads second. A menu refill changes only the order
  (`battle_controller_player.c:2661, :2669`), so the KI-96 re-map (`battle_action_selection.py:809`) and the KI-101
  re-map (`:1350`) would receive the PRE-refill order. Both exist only to get a fresh order. **Mechanism verified;
  the live effect is NOT measured** (this item's BE-4 measures it with a harness stand-in).
- **The ordinary path:** `:116` and `:578` can run in the same frame with no `yield` between them. `:578` then
  receives the cached object. It feeds `:613`, which only acts in the fallback where the menu never opens within
  120 frames, and the doubles `[TURN n]` line (`:538`).
- `battle_handler.py:492` is always second after `:407`. It reads the order only for a log line and for the fault
  arm `POKEBOT_KI47_FAULT_STALEMAP`.

**What the agents corrected in KI-108's own account:**
- **`battle_move_replacing.py:149` is NOT "correct as a first caller".** `:147` reads `gActionSelectionCursor[0]`
  (KI-115). `expGetterMonId` indexes `gPlayerParty` directly, so mapping it through the battle order may itself be
  wrong (INFERRED; rule 10). ⇒ It is graded here only for "the arms agree headless", and its correctness stays with
  `#27-battlestructptr`.
- **"Fresh" is not "the player's order".** `SwitchPartyOrder` runs for any battler, so after an enemy switch the
  global holds the enemy's order until the player's menu refills it. The fix makes second callers CURRENT, not
  correct.
- **In-frame writes are out of scope.** In the 2026-09-28 VOID evidence, Run A (a plain write after the dispatcher's
  read in the same frame) is unchanged by any `__eq__`. Only Run B (aged, then re-read) is KI-108.
- KI-108's line numbers drifted: `~:803` and `~:1107` are now `:809` and `:1350`.

**Found on the way, NOT in this item's scope** (to be filed as a KI when this item lands):
- `PlayerAvatar.__ne__` is INVERTED (`modules/player.py:82-89`: `or other._map_group_and_number ==
  self._map_group_and_number`). Upstream has it too.
  - With the map unchanged, the cache is replaced on every fresh read, which bumps `.frame`. The web stream
    (`http_stream.py`) then likely sends extra avatar events (INFERRED).
  - The other direction (keeping an old map) needs identical object-event bytes across a map change, and those bytes
    include the map fields. INFERRED unreachable.
- `EffectiveWildEncounterList.__eq__` omits the encounter lists, which depend on the lead's level (KI-108 already
  names it, lower stakes).

## The decision

- **Add both fields to `__eq__`, default ON, with a FAULT SWITCH that restores upstream's 9-field compare.** This is
  `29-DISABLED-FEATURES-REGISTRY.md` §B's standing idiom: *"The fix is always the default; the switch restores the
  bug."*
  - The switch is `POKEBOT_KI108_FAULT_OLDEQ`: `"1"` restores the old compare, anything else is the fix. It is read
    PER CALL inside `__eq__`, the per-module exception for upstream files (`29:187`).
  - It is a §B row in the registry. It is an UPSTREAM DIVERGENCE, logged in `DIVERGENCE-LOG` on promotion.
- **Rejected:**
  - A default-OFF opt-in flag. That shape is for new FEATURES (the R-series rows); a bug fix uses §B.
  - A pure read at the three sites. It misses every other second caller (`:578`, `:492`, future instruments). It
    turns `probe_dmgaudit.py`'s NH-gbs-count red (it pins exactly 5 `get_battle_state()` calls in the file). And it
    leaves the class of bug in place.
  - Re-reading on `age_in_frames == 0`. It would remove the per-frame cache for every reader, which is a different
    change with a performance cost, and nothing here measured a need.
- **Sequencing:** built on `wt/battleeq` while `main` is frozen for step 14's batch (9:00 PM to ~10:00 AM
  2026-10-02). The live arms run BEFORE 9:00 PM or AFTER the batch, never during it (contention). The merge waits for
  the batch to end. Tonight's batch therefore runs the UNFIXED code.
  - ⚠ A caveat for the batch grade: battler 2's doubles `[TURN n]` line can lag one turn after a turn in which no
    compared field changed (the adversarial pass's O6). E5's same-turn CONTEXT pairs uses with those lines. E5 is read
    BY HAND, and that reader must know the label can lag.

## What gets built

1. **`sandbox-pokebot/modules/battle_state.py`:** `__eq__` also compares `_battler_party_order` and `_current_turn`
   unless the fault switch is `"1"`. Nothing else in the file changes.
2. **`tools/story-dev/probe_battle_state_eq.py`** (an offline gate appended to `run_gates.py`).
   - **Setup:** a fake `read_symbol` and a SETTABLE frame counter starting at ≥ 1; a fresh `StateCache` per row.
   - **Rows:**
     - C0, the first call is fresh; C1, two calls with no change return the same object.
     - K1, the switch ON reproduces the bug: the second call returns the old order, and `is` the old object.
     - K2, fixed: the second call returns the new order.
     - K3, it persists into the next frame.
     - K4, the turn alone changes.
     - K5, order and HP change together, so both arms are identical (the vacuity witness).
     - K6, `__eq__` semantics: identical bytes are equal in both arms, and a non-`BattleState` gives `NotImplemented`.
     - K7, the switch is read per call, and only `"1"` restores.
     - K8, the bookkeeping `frame`.
     - K9, KI-108's Run-B shape offline.
     - W rows on the AST: the two reads are in `__eq__`, the switch guards them, its literal is in `battle_state.py`
       and in the registry, and `get_battle_state` still returns the local.
   - **Mutants**, each with an exact red set written before its first run:
     - revert to the mirror's `__eq__`;
     - drop only the turn, or only the order;
     - ignore the switch;
     - read the switch at import;
     - return the cache value;
     - make the setter always store;
     - a comment-only mention (must redden NOTHING);
     - rename the switch literal.
   - **Reproduce first:** the gate runs against the UNFIXED code before the fix lands, and its fix rows must be red.
3. **`tools/story-dev/story_harness.py` (driver-side only):**
   - `KI47_INSTALL=0` makes `--driver ki47oor` skip its direct cache install (`:396-402`), which leaves KI-108's
     Run-B shape. Its premise check is redefined for that mode.
   - `KI108_LEVER=1` adds a harness-only first reader: a listener that calls `get_battle_state()` every frame while
     `battle_is_active()`. It stands in for the GUI Battle tab.
   - `KI108_CENSUS=1` rebinds `get_battle_state` wherever it is bound, and logs every call. Each line carries the frame,
     the call's index within that frame, the caller's file:line, the order and turn RETURNED, and the order and turn in
     MEMORY. The memory read is pure: it never writes the cache.
   - None of these knobs uses the `POKEBOT_` prefix (they are driver knobs, like `KI47_ARM`).
4. **Docs on completion:**
   - the §B registry row;
   - KI-108's status, plus a new KI for `PlayerAvatar.__ne__`;
   - 03, 04, 06, 07 and 08.

## PREDICTIONS

The fixture is `r20_pregym1_party4_r116.ss1` (PINNED `9710585350be10534737c4362c33189e`; ROUTE116, 4 mons, no
badges), verified with `verify_fixtures.py --assert` first, at 30,000 frames per arm. "FAULT" means
`POKEBOT_KI108_FAULT_OLDEQ=1` and "FIX" means unset. Per KI-112, each graded live arm runs TWICE, and an identical
outcome is "one trajectory, replayed", never a replication.

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| BE-1 | `probe_battle_state_eq.py` on the UNFIXED code, then on the fixed code; `run_gates.py` | Unfixed: exactly the FIX rows (K2, K3-fix, K4-fix, K6-fix, K8-fix, K9-fix) are red, and every other row passes. Fixed: all rows pass, every mutant reddens exactly its set, the comment-only mention reddens nothing, and the full suite passes (`probe_dmgaudit.py` NH-gbs-count unchanged) | a fix row passing on unfixed code; any red row after the fix; a mutant set mismatch; any suite FAIL |
| BE-2 | `--driver ki47oor`, `KI47_INSTALL=0` (Run-B shape), arms Foor / Wid / C0 × FAULT / FIX | Foor FAULT: the handler's `snapshot_order=012345` while memory held `104523` (KI-108 reproduced). Foor FIX: `104523`. Wid and C0: `012345` in both arms (identical by construction, the controls). The chooser's action (`sent_the_chosen_mon`) is identical across FAULT and FIX in every arm (it decides by identity) | Foor FIX not `104523`; a control differing between arms; an action that differs. ⛔ VOID, not PASS, if Foor FAULT reads `104523` (the stale path was never reached) |
| BE-3 | the ordinary case: `--driver ki47oor` arm Swp (one natural RotateLead) with `KI108_CENSUS=1`, FAULT / FIX | Every ACTING-site call (`:809`, `:1350`, `battle_move_replacing:149`) has in-frame index 1 in both arms. The menu slot acted on is identical event by event (paired by battle, turn and PID). ACCEPTANCE is the same. Any second-caller difference appears only at log sites (`:492`, `:578`, `[TURN]`), and each is listed | an acting-site call at index ≥ 2 headless (the "first caller" premise is wrong); a different slot acted on |
| BE-4 | the lever: arm Swp with `KI108_LEVER=1` and `KI108_CENSUS=1`, FAULT / FIX | FAULT: at least one bot call at index ≥ 2 returns an order OR a turn that differs from memory; the order and turn counts are printed separately, and the order count may be 0 (the turn is the likelier one, since the counter advances without a compared field changing). FIX: zero calls at any index return an order or turn that differs from memory, except in a frame in which the HARNESS wrote memory after that frame's first read (listed separately; out of scope: the emulator does not run between two calls in one frame) | FIX with a returned-vs-memory difference not explained by a harness write. ⛔ VOID for the FAULT half if it shows zero differing calls of either kind, and the lever then needs a battle with a prior switch |
| BE-5 | an INDEPENDENT adversarial pass on the diff and the gate | every non-equivalent mutant of `__eq__`, the switch and `get_battle_state`'s return reddens a row | a non-equivalent survivor |

### BE-6 — ADDED 2026-10-01 ~4:10 PM LA, BEFORE its run (after the adversarial pass, before any BE-6 code or run)

**Why it was added:** the independent pass showed BE-3 and BE-4 never tested an ACTING site with discriminating
power. The only `:809` call came while the order was still identity, so a stale value and a fresh one were equal.
`:1350` and `battle_move_replacing:149` were never called. The design's motivating case is therefore UNMEASURED: a
GUI-shaped first reader handing a pre-refill order to the KI-96 / KI-101 re-map. KI-101's own evidence (`05` KI-101:
`KI-101 remap after 47 frame(s); pre-menu value was 1`) shows `--driver ch24probe` vs Sidney on the PINNED
`post_ch24_atdoor.ss1` (`82bc3125637d86dbbdd4d3a40d4f240e`) reaching the item re-map after an order change.

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| BE-6 | `--driver ch24probe` from `post_ch24_atdoor.ss1`, the folded harness's lever (it reads FIRST, before every listener, as the GUI does) and census, FAULT / FIX, twice each | **FAULT:** at least one call at `battle_action_selection.py:1350` (or `:809`) at in-frame index ≥ 2 returns a party order that differs from memory, and the menu slot acted on differs from the slot holding the target's PID (the KI-101 failure itself, now CAUSED by a first reader). **FIX:** every such call returns memory's order, and the slot acted on holds the target's PID | FIX with an acting-site call that differs from memory, or a slot that does not hold the target's PID. ⛔ **VOID** (not a pass, not a refutation) if the run reaches no `:1350` / `:809` call after an order change, i.e. no call where memory's order differs from the order the cache held before the refill; then the motivating case stays UNMEASURED and is written as such |

## GRADED (2026-10-01, ~5:05 PM LA; DONE on branch `wt/battleeq`, merged to `main` only after step 14's batch)

⛔ **Headline: the fix works, and BE-6 measured what it is for.** With a GUI-shaped first reader and upstream's
compare, the KI-101 item re-map aimed at the WRONG party member: the item was not consumed twice, and items were
disabled for the battle. With the fix it hit the target. **Two predictions FAILED AS FILED:** BE-1 (its row list and its
suite clause) and BE-5 (22 gate gaps, all folded).

**Evidence:**
- The FINAL runs: `tools/story-dev/evidence/2026-10-01-battleeq-final-*.txt` (24 files). They came from committed code
  (`2858fadd`), through a runner that refuses an uncommitted subject or harness, with every arm run twice.
- The adversarial pass: `tools/story-dev/evidence/2026-10-01-battleeq-ADVERSARIAL.txt`.
- The pre-fold runs (`…-battleeq-<ARM>.txt`) are kept, but are superseded. 8 of them used a harness that was never
  committed.

| # | Grade | What the evidence shows |
|---|---|---|
| BE-1 | **FAILED AS FILED (two clauses); substance held** | Unfixed: 12 rows red, not the 6 listed. All 12 need the item (K7-fix and the W rows also need the fix; W5 needed the registry row), and every fault, control and vacuity row passed. Fixed: all rows pass, and every mutant matches its set. ⚠ The first full suite read `FAILED: 2 of 145`: doc counts and citations moved by the build, fixed in the build commit. The coordinator's suite after the fold: see "Suite" below. |
| BE-2 | **HELD** | Foor (memory `104523`, cache held `012345`): `snapshot_order=012345` under FAULT, `104523` under FIX, ×2 each. The premises that replaced the tautology hold: `runb_premise_cache_differs` and `runb_setter_as_armed`. Wid and C0: `012345` in both arms (`runb_premise_cache_matches`). The chooser sent the chosen mon in every run (`handler_frames=148`). |
| BE-3 | **HELD, but it could not discriminate** | Every acting-site call was index 1. The only one (`:809`, f137502) had `mem_order_last_changed=never`, so a stale value would have matched memory. The slots acted on are identical across arms. FAULT's one order difference is at the log-only `battle_handler.py:492`. |
| BE-4 | **HELD** | The lever reads FIRST (index 1 in all 3,944 of its calls). Bot calls at index ≥ 2: 359. FAULT: 2 stale orders and 4 stale turns; FIX: 0 and 0. Both ×2. ⚠ The turn lags are at `:116` and `:578`, and `:116` feeds `decide_turn`, so turn-reading strategies (`catch.py`, `lose_on_purpose.py`) are exposed. |
| BE-5 | **FAILED AS FILED** | The mutant hunter: 71 tried, 22 non-equivalent survivors. The fake world varied one order pair, one turn step and one field. Folded with K10 (every order/turn change shape, both directions), K11 (each of upstream's 9 fields alone), K12 (the switch value compared with `"1"` only, exhaustively), K13 (the backwards frame) and R1 (the §B row exactly). The W rows that dead code fooled were removed. The hunter's own `hunt.py` re-run kills all 22. 34 built-in mutants, all on their pre-written sets. |
| BE-6 | **HELD (not VOID)** | `ch24probe` vs Sidney, lever + census, ×2 each. FAULT: `battle_action_selection.py:1350` at index 2 returned the cached `142305` while memory held `412305`. The menu refill at f4400528 had changed only the order. The Full Restore for Mightyena#5C96EA9B went to menu slot 1 (Zigzagoon): `‼ ACTED-ON SLOT != PID TRUTH`, then "NOT consumed twice; disabling items for the rest of this battle". FIX: every `:1350` call returned memory's order. Slot 0 was Mightyena and the item was `✔ CONSUMED`. Three later uses on Swellow#0B30A747 hit slot 0 = Swellow. Both arms won. |

### What this establishes, and what it does not

- **Established:** a `get_battle_state()` caller that reads second in a frame now gets the order and turn in memory.
  Shown three ways: offline (K-rows, X-rows), on KI-108's own Run-B shape (BE-2), and with a GUI-shaped first reader
  at an acting site, where the old compare caused a real wrong-target item use (BE-6).
- **Not established:**
  - How often a real first reader exists. The GUI debug Battle tab is the one found, and headless runs have none.
  - That `battle_move_replacing.py:149` is correct. It is KI-115's, and it was never called here.
  - Anything about in-frame writes (out of scope by design; K9-runA pins them).
- **One trajectory per arm, replayed:** the ×2 repeats are determinism checks, not replications.

### What the adversarial pass changed (folded `2858fadd`)

- **The gate:** K10-K13 and R1 added; W1-W6 removed (dead code satisfied them, or equivalent refactors false-positived).
- **The harness:**
  - H1, the tautological premise, is replaced.
  - H2: write-explained diffs are counted per field, with served-from-cache on every line.
  - H3: the lever reads first, like the GUI.
  - H4: rebinding by identity, with a loud failure if any reference survives.
  - H5: the acting sites are always listed.
  - H6: the slot actually reached is logged, beside a PID truth.
  - `mem_order_last_changed` makes a VOID run visible.
- **The process:** every graded arm was re-run from committed code.

### The design was wrong in three places (recorded in `08`)

- It dropped the recon table's "Turn: YES" for `:116`.
- BE-1's row list was written from memory.
- It called the controls "identical by construction". The harness reviewer showed a natural KI-108 could make a control
  differ; the new premise now checks it.

### Suite

The coordinator's full `run_gates.py` on the folded branch (`2858fadd` code + the final evidence), before these doc
edits: `ALL 141 ENFORCING GATES PASS  (591.6s total)   [+4 ADVISORY probe(s) — run, NOT gated]` (145 entries). This
clears BE-1's suite clause on the final code. The clause was still falsified as filed, by the first run.
