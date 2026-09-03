# §Ch22 CHAPTER ASSEMBLY — RECON + BUILD SPEC ✅ **SPENT: THE CHAPTER WAS BUILT FROM THIS, SAME DAY**

> ✅✅ **SHIPPED 2026-09-03.** This file is the SPEC the chapter was built from, kept because its
> recon is still the reference for the map; the STATUS line below said "the CHAPTER is not built"
> and is now spent. What was built and driven is in `07-CHANGELOG.md` 2026-09-03 (chapter) and
> graded against pre-registered predictions in `2026-09-03-ch22-CHAPTER-RESULTS.md`.
> ⛔ **DO NOT REBUILD FROM THIS FILE.** Two of its own recommendations were overtaken within hours:
> the "XP run" leg must NOT be built (the victory script flags all ten B1F trainers), and
> `_climb_to`'s missing southward twin is now `_descend_to()`.

> ‼ **COUNT, stated once so it stops drifting: FOUR DRIVERS = one read-only recon PROBE
> (`ch22probe`) + THREE STORY LEGS (`ch22ice`, `ch22juan`, `ch22exit`).** A Tier 1 reviewer
> found this file saying "four legs" while the handoff said "three legs deep" over the same
> four items.

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). A **✅** marks a claim I re-opened the
> source and confirmed MYSELF. Produced 2026-09-03 from four concurrent agents (decomp recon,
> our-code template audit, an ADVERSARIAL refuter, and a capability sweep). The refuter's verdict
> was **REFUTED — the chapter is not glue**, and it found a blocker no driver had ever reached.

---

## §0. THE HEADLINE — TWO FINDINGS THAT CHANGE THE DESIGN

### ✅✅ F1. THE JUAN VICTORY SCRIPT FLAGS ALL TEN B1F TRAINERS AS DEFEATED. THE EXIT IS FREE.

`data/maps/SootopolisCity_Gym_1F/scripts.inc`, inside `..._EventScript_JuanDefeated`:

```
	setvar VAR_0x8008, 8
	call Common_EventScript_SetGymTrainers
```
and `data/scripts/set_gym_trainers.inc`:
```
SootopolisCity_Gym_SetGymTrainers::
	settrainerflag TRAINER_ANDREA
	settrainerflag TRAINER_CRISSY
	settrainerflag TRAINER_BRIANNA
	settrainerflag TRAINER_CONNIE
	settrainerflag TRAINER_BRIDGET
	settrainerflag TRAINER_OLIVIA
	settrainerflag TRAINER_TIFFANY
	settrainerflag TRAINER_BETHANY
	settrainerflag TRAINER_ANNIKA
	settrainerflag TRAINER_DAPHNE
	return
```
✅ **Both blocks read and quoted by me from the decomp, not recalled.**

⇒ **THE POST-BADGE DESCENT COSTS ZERO BATTLES**, so:
* there is **no XP run**, and the "the chapter NEEDS the XP" comment in `sootopolis_gym.py` was
  arguing for a leg that should not exist (it was also resting on the refuted "cannot win" claim);
* the chapter needs **ONE** descent, not two;
* ⛔ **`--driver ch22exit`'s headline numbers were measured in a premise the chapter never enters.**
  It ran with `badge8=False` and so fought 3 trainers for 629/694 → 332/694. Real, reproducible,
  and **not transferable**. The driver is still the right instrument for the fall and the route —
  just not for the HP cost. *(That is a mistake shape, filed in `08-MISTAKES.md` 2026-09-03.)*

### ⛔⛔ F2. `_climb_to` WALKS NORTH ONLY, AND THE CHAPTER'S ONLY UNTESTED SEAM NEEDS SOUTH

✅ **Verified by reading the function myself.** `sootopolis_gym.py`'s `_climb_to` computes
`nxt = (here[0], here[1] - 1)` unconditionally. `fight_juan` leaves the bot on `JUAN_STAND (8,3)`;
`fall_to_b1f` then calls `_climb_to(FALL_STAGING = (8,5))` — **two tiles SOUTH**. The first `nxt`
would be `(8,2)`, which is **Juan's own tile**: plain floor, so neither the locked-stair guard nor
the cracked-ice guard fires. It would press "Up" into Juan for 3 × 900 frames and then blame its
step budget.

‼ **(SPENT) No driver had ever run `walk_the_ice → fight_juan → fall_to_b1f` composed** — `ch22exit`
never fights Juan and `ch22juan` stops on the island, so the seam the chapter is made of had zero
coverage. ✅ **`--driver ch22chapter` now runs it**, and it was worth the caution: the composed arm
found three defects in its own acceptance line. Also **mitigated** by a refusal naming the problem (a
descent helper is still owed) — see `07-CHANGELOG.md`.

---

## §1. THE ORDER, AND WHY

**heal → (stock, optional) → enter gym → ice (64) → climb 3 → JUAN → fall (8,6) → B1F 19 steps
(0 battles) → ladder (11,22) → 1F → out to the city → can-continue check.**

| step | owner today | status |
|---|---|---|
| heal at the Poké Center | `heal_in_pokemon_center(PokemonCenter.SootopolisCity)` ✅ exists, `map_data.py:1544` | ⚠ see §3 hazard H1 |
| stock at the Mart | **nothing** — `buy_in_shop` exists but has ZERO callers; `buy_poke_balls` is the proven path and is hardcoded to Poké Balls + Rustboro | OPTIONAL, and now *insurance*, not readiness |
| city → gym warp (31,32) → `GYM_ENTRANCE (8,25)` | **driver only** (`story_harness.py`) | ⛔ chapter must own it |
| the ice walk | `walk_the_ice()` ✅ driven | ends on **(8,6)**, not Juan's tile |
| the 3-step stair climb (8,6)→(8,3) | **driver only** | ⛔ chapter must own it |
| the fight | `fight_juan()` ✅ driven, 4/4 wins | see §2 |
| the descent (8,3)→(8,5) | **nothing** | ⛔ F2 — a descent helper is owed |
| the fall | `fall_to_b1f()` ✅ driven | requires (8,6) already cracked |
| B1F → ladder | `walk_b1f_to_ladder()` ✅ driven | route is battle-free post-badge (F1) |
| ladder → 1F → city | **driver only** | ⛔ chapter must own it |
| `ch22_chapter_done()` | **nothing** | ⛔ `juan_defeated()` alone returns True *while stranded on the island* |

## §2. THE FIGHT IS SAMPLED — ⛔ **UPDATED: 5 WINS AND 1 LOSS OVER SIX DRAWS**

> ⛔ **THIS HEADING READ "4 WINS OUT OF 4".** The chapter drive, built from this very spec, > then LOST its first Juan fight and won the one after recovering. The four arms below are > still correct; they are four of six. ⇒ "CAN win" is measured, "wins reliably" is FALSE.

| arm | `POKEBOT_CH22JUAN_JITTER` | frames | outcome | survivors |
|---|---|---|---|---|
| control | 0 | 32,891 | **Won** | 5/6 |
| A | 181 | 25,508 | **Won** | 5/6 |
| B | 1013 | 21,386 | **Won** | 5/6 |
| C | 47 | 24,565 | **Won** | 5/6 |

⛔ **The first three runs I did (all unjittered) were BYTE-IDENTICAL and were NOT a sample** — that
is a determinism reading, and reporting it as 3/3 would have been a fabricated confidence interval
(`08-MISTAKES.md` 2026-09-03). The jitter knob idles N frames before the talk; ✅ MEASURED to
actually perturb (`gRngValue` 0x008c33fa → 0xfbf1b389 at N=181), and the differing frame counts
confirm three genuinely different battles.

**Swellow faints in every single arm.** Sceptile's end HP swings wildly (141/141 in two arms,
**32/141** in another) and Wailmer ends at 14–19/160 every time. ⇒ **the post-Juan party is
chewed and unpredictable** — but with F1 the walk out costs nothing, so that is survivable.
✅ Swellow carries **no HM** (Peck / Wing Attack / Aerial Ace / Quick Attack); Dive is Wailmer's
(sole carrier) and Surf is on Zigzagoon + Wailmer. A fainted Swellow blocks nothing.

## §3. HAZARDS, RANKED — each with its source

* **H1 ⚠ THE HEAL CAN SHRINK THE PARTY.** `heal_in_pokemon_center` calls
  `deposit_dead_weight_if_worth_it()`, and `team_policy.DEAD_WEIGHT_LEVEL_GAP = 8` makes Swellow
  (L41) and Zigzagoon (L19) deposit-eligible against Sceptile L50/L51 — Zigzagoon is **not** exempt
  because its Surf is shared with Wailmer. A heal before the gym could hand Juan a 4-mon party.
  §Ch21 leg 3 already re-checks its HMs by PID after every heal (`sootopolis.py:1547-1554`);
  ⇒ **copy that, and assert the party COUNT as well.**
* **H2 ⚠ `FLAG_ENABLE_JUAN_MATCH_CALL` is set by the victory script.** Juan joins the PokéNav
  Match Call pool, so an unsolicited call can now interrupt overworld walking on the way out.
* **H3 ⛔ THE BADGE FLAG IS SET WITH THE SCRIPT STILL RUNNING** — 4 msgboxes, 2 fanfares and 60
  frames of `delay` come after `setflag FLAG_BADGE08_GET`, player still locked. ✅ `fight_juan`
  already grades on `juan_defeated() and not get_global_script_context().is_active`, which is the
  correct shape; do not weaken it to the flag alone.
* **H4 ⚠ A LOSS IS A WHITEOUT, and it unwinds past the chapter.** `StoryAbort` → `StoryMode.run`,
  which respawns at the Sootopolis Poké Center and re-enters `_play()` from the top. The in-chapter
  3-attempt loop never sees it. ⇒ every leg needs an `already`-style self-skip so a resume returns
  instead of raising; today only `fight_juan` has one.
* **H5 ⛔ A MID-GYM RETRY MISDIAGNOSES ITSELF.** On attempt 2 without leaving the map,
  `assert_route_matches_live_floor()` raises *"regenerate the table with solve_gym_ice.py"* — the
  table is fine, the ice is spent. The module's "a failed attempt costs only the walk" property is
  only real via a map exit + re-entry, which no production function implements.
* **H6 ⚠ `VAR_ICE_STEP_COUNT` IS SHARED STATE** — the same var drives Sky Pillar and Granite Cave
  cracked floors (`src/field_tasks.c`). Never treat its value as gym-scoped across maps.
* **H7** `0x20F` (locked stairs) is `MB_SLIDE_SOUTH` with **collision 0** — walkable, and it slides
  you back onto the ice. This is why `calculate_path` is banned in this gym; it is not a wall.
* **H8** `0x206` (broken ice) is `MB_CRACKED_FLOOR_HOLE` and fires `EventScript_FallDownHole` from
  the map's own OnFrame — a **second, independent** fall path. Both end in `warphole`.
* **H9 ✅ REFUTED, do not spend time on it:** the TM03 bag-full branch cannot happen — the TM/HM
  pocket holds 64 and there are only 58 distinct TMs+HMs. And even if it did, the badge is set
  BEFORE the give and the branch exits cleanly.
* **H10 ✅ REFUTED:** the Juan *rematch* (a double battle) cannot be triggered accidentally —
  `fight_juan` checks `juan_defeated()` first and returns `already=True`.

## §4. STATE 6's EFFECTS ON THE OUTSIDE MAP (✅ decomp-verified)

Wallace, Steven and five residents are **hidden**; Man_1 appears at (26,4); the Expert moves to
**(31,18)**, blocking the Cave of Origin warp; the layout and weather return to normal (both
already normal at state 5, so no-ops); no `ON_WARP` or `ON_FRAME` scene matches state 6, and the
map has **no coord_events at all** ⇒ **nothing ambushes the bot on the way out.**
⚠ The gym exit warp lands on **(31,32)**, the tile Wallace used to occupy — clear at state 6.
⭐ The real world-unlock is the BADGE, not the var: `field_control_avatar.c` gates field Waterfall
on `FLAG_BADGE08_GET`, which is what opens Route 132-134 → Ever Grande for §Ch23.

## §5. THE ORCHESTRATOR TEMPLATE (copy §Ch21's shape exactly)

Zero-arg generator, function-local imports, `if ch22_chapter_done(): return` first, one
caller-owned `report` dict, `for attempt in range(1, 4)` with `_check_abort()` as the loop's FIRST
statement, `except StoryAbort: raise` before `except BotModeError` (whose first statement is
`reraise_if_aborting(error)`), and a terminal `BotModeError` joining the attempt list. Wire it as
Segment 22 with the same three-line idiom and a `_guard("Gym 8 — Juan (Ch22)", ch22_chapter_done)`.
⛔ **Gate every leg on POSITION *AND* STATE**, never on vars alone.
⛔ **Re-read the state at the top of every attempt**, never once above the loop.
⛔ **`assert_ch21_preflight()` is never actually called by `do_sootopolis_chapter()`** — §Ch20 calls
its own preflight at `seafloor_cavern.py:975`; that is the placement to copy, not §Ch21's.
‼ `sootopolis_gym.py` has **no preflight, no readings set, no `_take()`, no acceptance ledger** —
all four exist in §Ch21 and all four are worth porting.
