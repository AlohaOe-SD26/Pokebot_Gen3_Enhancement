# §Ch24 LOBBY FIXTURE — THE SPEC, AND TWO MEASUREMENTS TAKEN WHILE WRITING IT (2026-09-18)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** A 6-agent spec pass (3 angles, each adversarially
> refuted) produced the plan below. ✅ marks what I re-verified at FILE:LINE **in this round**.
> ⛔⛔ **NO DRIVE WAS RUN.** This specifies one, and records what was measured without driving.

---

## ⭐⭐ THE REFUTER KILLED THE INSTRUMENTATION BEFORE IT COST A FIXTURE

The spec's first draft read `FLAG_ENTERED_ELITE_FOUR` to confirm the guard talk. ✅ **I verified the
kill myself:**

* `grep -c "^[0-9]* FLAG_" modules/data/event_flags/emerald.txt` → **0 of 1,164 entries** carry a
  `FLAG_` prefix. The real rows are bare: `:211 263 ENTERED_ELITE_FOUR`, `:1105 2228 LANDMARK_POKEMON_LEAGUE`.
* `modules/memory.py:336-338` — `def get_event_flag(flag_name):` / `if flag_name not in _event_flags:`
  / **`return False`**. ⇒ an unknown name reads **False, silently and forever**, indistinguishable
  from a genuinely unset flag.

⇒ ⛔ **the talk arm would have looped waiting for a flag that could never read True, burned its bound
AFTER setting the flag in-game, and graded FAIL — paying the one irreversible cost on the route for a
reading it could never take.** This is the project's own "a guard that answers without asking" class.
✅ Our own code already knows: `victory_road.py:1605` — *"`get_event_flag` returns **False for any
unknown name** — a typo…"*.

---

## THE SPEC (ready to execute; not executed)

| item | value | why |
|---|---|---|
| start fixture | **`post_ch24_atdoor_L75.ss1`** | ⚠ NOT `post_ch24_atdoor.ss1` — same tile, but that one is **L47**; the manifest says *"Use THIS one."* |
| stop tile | **`LEAGUE_NURSE_STAND (3,4)`** on `POKEMON_LEAGUE_1F` | 9 tiles from the nearest gauntlet door, 5 from the escalator, 12 from the exit warps; already a named constant our own §Ch23 leg 10 stands on |
| ⛔ reject | `(9,3)` | post-talk it is TWO steps from a step-on warp into HALL5 |
| guard talk | **SKIP IT** | see below |
| flag reads | **bare names**, plus a pre-flight assert that the name is in `_event_flags` | otherwise vacuous |

### ⭐ SKIP THE GUARD TALK — AND THE REFUTER'S REASON IS BETTER THAN THE SPEC'S

The spec argued the talk is optional because *no code reads `FLAG_ENTERED_ELITE_FOUR`*, so the
predicates are bit-identical either way. The refuter added the stronger argument:
⇒ **while the flag is unset the guards stand ON `(9,2)/(10,2)`** — ✅ `victory_road.py:399-402` says
they are *"blocking the north doors positionally"* — so a no-talk fixture is **POSITIONALLY SEALED
against the gauntlet**: no future drive from it can reach the sealed rooms at all. A post-talk sibling
has those doors open **forever**, because the flag is permanent.
⇒ **mint `post_league_lobby.ss1` (no talk) first.** A post-talk sibling is owed separately, because
the settled ruling defines the lobby window as the POST-talk interval — but it should be a deliberate
second fixture, not a side effect.

⚠ **THE WINDOW IS TWO MAPS, AND THIS SPEC MEASURES ONE.** League 2F (16,14) is reachable from the
lobby by `LEAGUE_ESCALATOR (1,7)` — ✅ *"`MB_UP_ESCALATOR`, collision 0 — an accidental step-on warp"*
(`victory_road.py:410-412`). A complete answer needs a 2F reading too.

---

## ✅ MEASURED WITHOUT DRIVING: EVERY §Ch23 LEG GUARD, AT EVERY FIXTURE WE HOLD

The marker design rested on a claim that had only ever been TRACED: *"inside the sealed League every
§Ch23 leg self-skips."* We hold a sealed-map fixture, so it was measurable today. Guards transcribed
from `do_victory_road_chapter` (`victory_road.py:3327-3485`) and evaluated live — **guards only; no leg
was ever run.**

| position | legs whose guard FIRES |
|---|---|
| **`post_hall4_door` — HALL4, SEALED** | ⭐ **NONE** (all nine False) |
| `post_ch24_atdoor` — EVER_GRANDE, degraded party *(control)* | 5, 10, 11 |
| `post_league_shop` — EVER_GRANDE, basket bought *(control)* | 5, 11 |

⇒ ⭐ **CONFIRMED BY READING: inside the sealed zone not one §Ch23 leg is even INVOKED.** That is
stronger than the design claimed — the legs are not merely inert there, they are **unreachable from the
dispatch**.
⇒ The controls separate, so the instrument works. ✅ **RE-RUNNABLE AND COMMITTED** (a reviewer noted the first version had no artifact): `tools/story-dev/probe_ch23_leg_guards.py`, output at `tools/story-dev/evidence/2026-09-18-ch23-leg-guards-BY-POSITION.stdout.txt`. They are informative too: **leg 10 fires on the
degraded-party fixture and not the healthy one**, which is the heal guard behaving exactly as written.
⚠ **A nuance reading exposed that tracing had blurred:** **leg 11's guard is bare `_on_map(EG)` with no
basket conjunct**, so it fires at Ever Grande *even after the basket is bought* — its self-skip must
live inside the leg body. ⇒ "legs don't re-fire" is true for two DIFFERENT reasons in two places, and
only the sealed-zone case is guaranteed by the dispatch itself.

---

## ⚠ AND A SEPARATE FINDING, FILED NOT FIXED: FOUR PHANTOM NAMES IN THE HARNESS

Applying the same table-check to the harness (which `audit_flag_names.py` does **not** scan):
✅ **302 harness files · 86 `get_event_flag` + 68 `get_event_var` literal calls · 4 phantom names**,
all in `story_harness.py`:

* `:592` — `get_event_flag('FLAG_ADDED_MATCH_CALL_TO_POKENAV')` ⇒ **fixable**: the bare name exists
  (`event_flags/emerald.txt:252`, `304 ADDED_MATCH_CALL_TO_POKENAV`).
* `:396`, `:508`, `:551` — `get_event_var('VAR_RESULT')` ⇒ ⚠ **not a prefix bug**: our var table has
  **no RESULT entry at all** (256 entries, zero matches). Needs a decision, not a rename.

✅ **SEVERITY IS LOW, AND I CHECKED RATHER THAN ASSUMED: all four are DIAGNOSTICS.** `_var()` feeds a
log f-string at `:408`; `_dump` is a dump; `:551` is a log line. **Zero feed an acceptance, assert or
raise** — so this is misleading log output, not a false PASS.

⚠ **THE GATE'S SCOPE IS DELIBERATE, NOT A DEFECT** — I checked before claiming one.
`audit_flag_names.py`'s docstring says *"every flag/var name string used by **story code**"*, and it
globs `modules/story/*.py` + `story_mode.py`. The harness is out of scope **by design**.
⇒ The argument for extending it is not "the gate is broken" but: **the harness is where drivers produce
EVIDENCE, and a phantom name there corrupts a reading silently.** ‼ Note the gate's own history — it
*"ran for weeks against exactly two hand-written paths"* while chapters moved out from under it, and
the fix was a glob. This is the same shape, one directory over.

---

## ⛔ WHAT THIS DOES NOT ESTABLISH

* **No drive was run and no fixture was minted.** The spec is ready; executing it is the next item.
* The lobby window remains **TRACED, not READ** — that is exactly what the fixture would fix.
* A 2F reading is owed as well as a lobby one.
* The four phantom names are **filed, not fixed** — the `VAR_RESULT` trio needs a decision about
  whether the var belongs in our table at all.
* Prerequisites (2), (3) and (4) are untouched. **Segment 24 stays unwired.**
