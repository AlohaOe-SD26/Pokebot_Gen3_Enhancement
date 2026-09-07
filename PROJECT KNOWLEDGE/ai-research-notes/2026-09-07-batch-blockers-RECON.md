# The 2026-09-07 batch's real blockers — a 9-agent recon. ⚠ A NOTE, NOT TRUTH.

**Produced 2026-09-07** from the live 8-lane batch (`x4-runs/20260907-073620`, `--build custom`) by
FOUR independent investigations: a 6-agent adversarial workflow on the routing failure, a
forward-walk audit of `_play` after the fix, a counter-guard audit, and a triage of the
whiteout-recovery cluster (§4). ⛔ Per
`ai-research-notes/00-READ-THIS-FIRST.md` this is a **NOTE**: the authoritative docs win on any
contradiction until a claim is verified. Claims marked ✅ were re-verified BY ME in the tree.

**Why this file exists rather than inline entries:** `03`/`04`/`05` are at 3578/3600, 899/900 and
2935/3000 lines. Detail lives here; those files carry pointers.

---

## THE MEASURED FAILURE MIX (9 ended runs, partial batch — a running figure, NOT a rate)

| runs | cause | status |
|---|---|---|
| 4 | `Could not reach (19,6) on MAUVILLE_CITY` from Sootopolis/Mossdeep | ✅ ROOT-CAUSED → `KI-97`, fixed in sandbox |
| 3 | `no super-effective answer` → 5 derails | ✅ ROOT-CAUSED, three distinct sub-causes below |
| 2 | too many whiteout recoveries in a row | ✅ INVESTIGATED — **Tate & Liza**, see §4 |

‼ The Mauville share read **4/6 (67%)**, then **4/9 (44%)**, then **6/14 (43%)** as the batch
ran on. ⇒ **always quote it with its `n`, never as "the" rate.** Navigation-class failures
together were **8 of 14** at the last reading.

---

## 1. `KI-97` — Segment 13a marched to Mauville from post-Fortree positions ✅ FIXED (sandbox)

**Chain (✅ re-verified by me):** `_play()` re-entry (whiteout **or** derail) walks the linear segment
list from the top → Segment 13a's `else` calls `travel_to_fortree()` with no completion gate →
`_rank()` (`early_game.py:6325-6326`) returns **-1** for any map absent from `order`
(`:6306-6313`), and SOOTOPOLIS_CITY / MOSSDEEP_CITY_GYM are absent → `-1 > tgt` and `-1 == tgt` are
both False → **every leg runs**, starting `LEGS[0] = (MAUVILLE_CITY, (19,6))` (`:6314`) →
`_navigate_riding_out` fail-fasts: Sootopolis has no land route out.

⭐ **THE SHAPE WORTH REMEMBERING — THIS BUG WAS ALREADY PAID FOR ONCE, IN THIS FUNCTION.**
`early_game.py:6303-6305` carries the author's own note: *"an unranked map = rank -1 = 'run every
leg' = a backwards march to Mauville and a NO-PATH Manual"* — written after ROUTE120 hit it. The fix
then was to add ROUTE120 to `order`. That could only cover maps that existed in the story build at
the time; Sootopolis/Mossdeep became reachable later, via §Ch21-23.
⇒ **AN ENUMERATION-BASED GUARD SILENTLY ROTS EVERY TIME THE STORY GROWS PAST IT.** The durable fix is
a gate on the segment's own COMPLETION FLAG, which cannot rot.

**Fix applied:** wrap Segment 13a — imports, body **and its trailing `_guard`** — in
`if not _done("BADGE06_GET")`, with an `else` that prints.
* The `_guard` is inside on purpose: it asserts Fortree-side, which is FALSE once legitimately past
  Fortree, so excluding it would convert a navigation derail into a guard derail and fix nothing.
* ⛔ **Rejected: adding the two maps to `order`.** It only moves the failure to the `_guard`, and the
  `-1` default is load-bearing for genuine Ch13 whiteout respawns at earlier PC interiors
  (`early_game.py:6030-6034`).
* ⛔ **Rejected: mirroring the guard at `:3597`.** That set is `(ROUTE119, FORTREE_CITY)`; neither
  offending map is in it, so the copy is a **no-op**.
* The `else` print is not decoration: the acceptance check is that a string DISAPPEARS, and an
  absence proves nothing on a run that never got there. It is the positive control.

**Acceptance (gradeable from any lane log):** `Story: Route 119 already cleared — heading to
Fortree.` and `Could not reach (19, 6) on MapRSE.MAUVILLE_CITY` must both appear **zero** times;
`Story: Fortree arc already complete (BADGE06) — Ch13a skipped.` must appear at least once; and a
pre-BADGE06 lane must still print `Story: to Fortree — Mauville City...`.

**Forward-walk audit (independent agent, ✅ spot-checked by me).** From SOOTOPOLIS_CITY (43,32) every
segment 13d→20 skips on its own flag, the single unconditional call
(`_leave_route120_north_bridge`, `story_mode.py:3649`) self-skips off Route 120, and `_play` reaches
`do_sootopolis_chapter()` with **zero navigation in between**. No later segment references the three
names the gate now scopes. ⇒ **for 3 of the 4 failures the fix is complete.**

---

## 2. ⚠ `#24-mossdeepstrand` — MOSSDEEP_CITY_GYM (23,8) is an ISLAND, and the badge LOCKS YOU IN

**The 4th failure. `KI-97` does NOT fix it — it moves the derail from 13a to Segment 19.**

* `(23,8)` is a leader-approach tile on an 11-tile collision island
  (`mossdeep_gym_puzzle.py:205`). `calculate_path((23,8) → (7,35))` raises; the **only** exit is a
  **coord_event** at `(21,6)` — *"not a warp event, so no warp-graph solver will ever offer it"*
  (`mossdeep_gym.py:460-461`).
* The only function that steps on it is `leave_the_gym()`, whose sole caller is
  `mossdeep_gym.py:596` — **after** the fight, inside `do_mossdeep_gym_chapter`.
* That chapter early-returns the moment the badge flag is set (`:548-549`, again `:556-557`), i.e.
  **before** reaching `leave_the_gym()`. And Segment 18 skips the chapter entirely once BADGE07 is
  set (`story_mode.py:3772`). **Double bypass.**
* The whiteout-recovery loop cannot help: it only exits Poké Centers (`early_game.py:367-368`).

⇒ **With BADGE07 set and the avatar on (23,8), no code path in the tree can move it.** The chapter's
own comment at `:590-593` already warns *"winning leaves the avatar on the leaders' platform, an
eleven-tile island; a chapter that returned here would pass its own test and strand the run"* — the
warning is correct and the early-return added later re-opened exactly that hole.

**✅ FIXED 2026-09-07 (sandbox, UNDRIVEN)** — commit `e458a29b`. BOTH halves, since either alone
leaves a hole: Segment 18's `else` now calls `leave_the_gym()` (that is the half that matters —
with the badge set the chapter is never called at all), and the chapter's own badge early-return
leaves before returning. Each is a no-op off the gym map (`:471-472` `if not _on_gym_map():
return`).
⛔ **The IDENTICAL early-return in `fight_the_leaders()` (`:382`) was deliberately LEFT ALONE** —
it is a SUB-STEP and correct as written: leaving is the CHAPTER's job, and the fight is retried
three times by the loop. ‼ That only surfaced because the edit asserted anchor uniqueness and
REFUSED when the two-line pattern matched twice; a blind replace would have patched the correct
copy and left the defect.

---

## 3. The `no super-effective answer` cluster — the machinery EXISTS, RAN, and failed three ways

⭐ **MY OWN FIRST READING WAS WRONG AND IS RETRACTED HERE.** I claimed the recommender's top pick
violated its own constraint ("Winona needs Rock/Ice/Dragon, it recommends Slugma (Fire)").
**It does not.** `counter_plan.py:156,185-205` admits a species by its types **OR** a level-up move
of a needed type — deliberately, as `#24-movepoolcounters` (user directive 2026-08-07), because pure
type matching gave **Winona zero candidates**. Slugma learns **Rock Throw** (move #88, 50 BP, Rock)
at **L15** and Fiery Path Slugma is **L15**, so it is caught already knowing it.
⇒ **a legitimate Rock answer.** ‼ The lesson: *a list that looks wrong may be a list that is
under-explained.* I nearly filed a defect against correct code.

**The real defect is a DISPLAY one.** `counter_plan.py:331-335` computes `answer_via`
(`"type"` vs `"move:Rock Throw@L15"`) with a comment saying the log must be able to say which rule
fired — and `summarise_candidates` (`:474-477`) never prints it. Zero production consumers. Also, the
printed top-5 is the raw, **undeduped** list while the ladder acts on `huntable_candidates()`; live,
four of Winona's five printed rows are the same Magma Hideout destination.

**"NOT HUNTABLE … reachable" is not a contradiction.** `reachable` = map connectivity;
`huntable` = reachable **AND** a swept spin tile exists. `HUNTING_GROUNDS` has **one entry** —
Fiery Path (18,19). ⇒ every counter elsewhere is diagnosis-only. ⛔ **SETTLED** — `06-DECISIONS-LOG.md:958`,
*"Consequence accepted… The unblock is field work (promote a swept tile)."* Do not propose relaxing it.

### ⭐⭐ THE ONE UN-SETTLED, ACTIONABLE HOLE: the ball restock is DEAD CODE from its only caller

✅ **Verified by me.** `hunt()` contains the contingency (`counter_hunt.py:471-475`): if balls ≤ 1,
`provision_poke_balls()`, and only abandon if that fails. But the ladder checks
`resource_blocker()` FIRST (`story_mode.py:1778-1782`) and returns False — and `resource_blocker`
is now **only** a ball gate (`counter_hunt.py:405-407`). `story_mode.py:1809` is the sole production
caller of `hunt()`. ⇒ **`counter_hunt.py:471-475` can never execute in production.**

Live cost: `L03/stdout.txt:30690` — *"cannot hunt a counter — no spare Poké Balls… Stopping
honestly"*, repeated to 5 derails and the run ended. **The same lane bought 30 balls one run later**
(`L03:31932-31935`) — the bot was fully capable of clearing its own blocker.

⚠ **HONEST RISK, why this is not a one-liner:** `provision_poke_balls` defaults to `RUSTBORO_MART`
(`early_game.py:2299`, constant `:2133`) and **that is the only mart constant in the tree** — there
is no nearest-mart table. From Fortree, restocking is a cross-Hoenn trek that would spend the boss's
one ruled hunt attempt on shopping. ⇒ the honest minimum is *ordering fix **plus** a nearest-mart
lookup*, or gating the restock on the mart being near the hunt route.

### ⛔ SETTLED — DO NOT REOPEN (`06-DECISIONS-LOG.md`, checked before escalating, per rule 11)

* `:958` huntability is a whitelist, separate from reachability — consequence accepted.
* `:998` one hunt per boss per run, latched **before** the hunt. ⇒ the L07 `"started"` case (a
  mid-hunt derail burning the attempt) is a **ruled-on accepted cost, not a bug**.
* `:3423`/`:3431`/`:3443` the second wind does **not** re-arm the ladder. "Let it try again" is a
  settled NO.

**None of them covers the ball-restock ORDERING.** That gap is open.

### ⚠ NEEDS A USER RULING — untrained boxed counters

`story_mode.py:1867-1876` ships a boxed counter into a boss fight **untrained by design** (boxed mons
earn no XP). Live: `L07` caught a Numel, boxed it, and fielded it at **L16** beside an L33 party
against Gym 4 — and lost. Closing this touches `pc_trip`, the lead picker and the one-attempt bound,
i.e. it is adjacent to settled ground. ⛔ Do not build it without asking.

---

## 4. ⭐ THE DEEPEST RUNS DIE AT TATE & LIZA — a failure class no guard covers

Found by triaging the one cluster nobody had examined (`too many whiteout recoveries in a row`, 2 of
14 ended runs). Both are the DEEPEST runs of the batch (3,877,438 and 4,198,775 frames), and both die
in the Mossdeep Gym against Tate & Liza — L04 at `defeat #24 here`, L05 at `defeat #11`.

```
Story: Ch18 plan #1 from (6, 35) — 117 steps, 16 switch press(es)
Story: Ch18 reached the leaders' tile (23, 8)
Story: Ch18 challenging Tate & Liza from (23, 8) (5 able to battle)...
Story: lost a battle at map (14, 0) (defeat #24 here; KO'd 1 of theirs first).
Story: whited out — recovering ...
```

⛔ **THE NON-CONVERGENCE GUARD NEVER FIRED.** It grades a boss HOPELESS on TYPE coverage; against
Psychic the party really does hold Dark/Ghost/Bug, so it keeps trying. ⇒ **the guard catches "wrong
types" and is blind to "right types, too weak"** — and the blind case is the expensive one, because
every loss re-solves the 117-step statue puzzle.

⚠ **TWO HYPOTHESES, UNDISCRIMINATED:** (a) the party is under-powered; (b) `KI-96`'s freshness
invariant is incomplete in DOUBLES (slot 0 encodes only the LEFT battler, decomp-verified), and Tate
& Liza is the story's only double battle. ⭐ The `[KI96-REREAD]` drive against this fight
discriminates them cheaply — clean rotations ⇒ (a); wedges or `DIFFER` ⇒ (b) contributes.
⛔ Grinding levels first is the expensive arm AND would mask (b).

---

## TREE NOTE
All fixes applied to `sandbox-pokebot/` only — `custom-pokebot` is FROZEN while the batch measures it.
`counter_plan.py`, `counter_hunt.py`, `training_areas.py` are byte-identical across both forks; the
counter regions of `story_mode.py` are identical at identical line numbers.
