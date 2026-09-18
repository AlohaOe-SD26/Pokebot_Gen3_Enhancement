# §Ch24 LOBBY FIXTURE — THE SPEC, AND TWO MEASUREMENTS TAKEN WHILE WRITING IT (2026-09-18)

> ⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** A 6-agent spec pass (3 angles, each adversarially
> refuted) produced the plan below. ✅ marks what I re-verified at FILE:LINE **in this round**.
> ⛔⛔ **NO DRIVE WAS RUN** *(true when written)*. This specifies one, and records what was
> measured without driving.
>
> ✅✅ **SUPERSEDED IN PART, 2026-09-18 (same day): THE DRIVE RAN AND THE SPEC WAS EXECUTED.**
> `--driver ch24lobby` minted and pinned **`post_league_lobby.ss1` = `5a75ea37ed5cc07ae8b0b0a75da5e909`**.
> The graded predictions, the four arms and the three unanticipated results are in
> `2026-09-18-ch24lobby-PREDICTIONS.md`. **Read the corrections below before quoting anything here.**
>
> ⛔⛔ **CORRECTION 1 — THE HEADLINE TABLE IN THIS NOTE COUNTED NINE OF TEN CALL SITES.** An
> adversarial review found the dispatch has **ten** guarded `yield from`s: the **TRAINING leg**
> (`victory_road.py:3430-3431`) carries no `LEG N` banner, and **leg 11 is NESTED** (`:3462-3467`).
> Both instruments were corrected and re-run. **The sealed-map verdict (NONE) survived; two CONTROL
> rows did not** — see the table.
>
> ⛔⛔ **CORRECTION 2 — “SELF-SKIP” IS THE WRONG WORD, AND THE DRIVE MEASURED WHY.** With no call
> site reached and `ch23_chapter_done()` **False** (it requires `_on_map(EG)`, the OUTDOOR map),
> `do_victory_road_chapter` consumes its 3 attempts and **RAISES** `BotModeError`
> (`:3486-3488`), and `story_mode.py:5172-5173` re-enters it every pass. ⇒ inside the League the
> bot can neither finish §Ch23 nor skip it ⇒ **the §Ch24 marker is load-bearing, not tidy-up.**

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

✅✅ **SUPERSEDED 2026-09-18 (later): THE SECOND MAP IS NOW READ TOO — `#24-league2f`.** `post_league_2f.ss1` is pinned (`d3c09e7af349`), all ten §Ch23 call sites read False on 2F, and the escalator round trip is measured in BOTH directions, so a stray step on `(1,7)` is **recoverable**. ‼ `(1,6)` is the DELIVERED tile and `(2,6)` the RESTING tile — do not confuse them. *(Original text, kept as the record:)* ⚠ **THE WINDOW IS TWO MAPS, AND THIS SPEC MEASURES ONE.** League 2F (16,14) is reachable from the
lobby by `LEAGUE_ESCALATOR (1,7)` — ✅ *"`MB_UP_ESCALATOR`, collision 0 — an accidental step-on warp"*
(`victory_road.py:410-412`). A complete answer needs a 2F reading too.

---

## ✅ MEASURED WITHOUT DRIVING: EVERY §Ch23 LEG GUARD, AT EVERY FIXTURE WE HOLD

The marker design rested on a claim that had only ever been TRACED: *"inside the sealed League every
§Ch23 leg self-skips."* We hold a sealed-map fixture, so it was measurable today. Guards transcribed
from `do_victory_road_chapter` (`victory_road.py:3327-3485`) and evaluated live — **guards only; no leg
was ever run.**

⛔ **THE TABLE BELOW IS THE CORRECTED ONE (TEN CALL SITES, re-run 2026-09-18).** The
❗ struck-through values are what this note originally published from the nine-site instrument.

| position | legs whose guard FIRES (TEN sites) | originally published |
|---|---|---|
| **`post_hall4_door` — HALL4, SEALED** | ⭐ **NONE** (all TEN False) | NONE (all nine) — verdict unchanged |
| `post_ch24_atdoor` — EVER_GRANDE, degraded party *(control)* | **5, 10** | ~~5, 10, 11~~ ❗ leg 11 was a mis-transcription |
| `post_league_shop` — EVER_GRANDE, basket bought *(control)* | **5** | ~~5, 11~~ ❗ same cause |
| ⭐ **`post_league_lobby` — THE LOBBY (3,4)** *(NEW, minted by this spec's drive)* | ⭐ **NONE** | *(did not exist)* |

⇒ ⭐ **CONFIRMED BY READING: inside the sealed zone not one §Ch23 leg is even INVOKED.** That is
stronger than the design claimed — the legs are not merely inert there, they are **unreachable from the
dispatch**.
⇒ The controls separate, so the instrument works. ✅ **RE-RUNNABLE AND COMMITTED** (a reviewer noted the first version had no artifact): `tools/story-dev/probe_ch23_leg_guards.py`, output at `tools/story-dev/evidence/2026-09-18-ch23-leg-guards-TEN-CALL-SITES.stdout.txt` ‼ **CITE THIS ONE.** ⛔ The older `…-BY-POSITION.stdout.txt` is the NINE-site output and is SUPERSEDED — it is kept as the record of what the first instrument printed, and its two EVER_GRANDE control rows are WRONG (see the retraction above). They are informative too: **leg 10 fires on the
degraded-party fixture and not the healthy one**, which is the heal guard behaving exactly as written.
⛔⛔ **RETRACTED — THIS “NUANCE” WAS FALSE, AND IT WAS A MIS-READ OF THE INSTRUMENT, NOT OF THE
GAME.** It read: *“leg 11's guard is bare `_on_map(EG)` with no basket conjunct, so it fires at Ever
Grande even after the basket is bought — its self-skip must live inside the leg body.”* The dispatch
is **nested** — `if _on_map(EG): stock = bag_healing_stock(); if any(stock < qty): yield from …`
(`victory_road.py:3462-3467`) — so the self-skip **IS the inner `if`, at the call site**, one line
below the outer one, and leg 11 fires at **neither** Ever Grande fixture once the basket is stocked.
‼ The transcription had recorded the OUTER `if`, which merely CONTAINS the call — **an input to the
action, not the action** — and I reported its value as a statement about when the leg runs.

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

* ✅ **SUPERSEDED: the drive RAN and the fixture IS minted** (`post_league_lobby.ss1`, pinned
  `5a75ea37ed5cc07ae8b0b0a75da5e909`). The lobby window is now **READ**, at ten call sites, by two
  independent instruments (the driver live, and the probe by RELOAD).
* ✅✅ **DONE 2026-09-18 — THE 2F READING IS NO LONGER OWED** (`#24-league2f`; fixture `post_league_2f.ss1`, `d3c09e7af349`). ⚠ **A post-talk sibling fixture IS still owed.** *(Original text, kept as the record:)* ⚠ A 2F reading is STILL owed, and so is a post-talk sibling fixture. ✅ 2F is now scoped
  from the decomp: it is the **Cable Club** (`LAYOUT_POKEMON_CENTER_2F`; Union Room / Trade Center
  attendants), reachable from the lobby with `ENTERED_ELITE_FOUR` unset — the escalator is 1F warp
  **4** at `(1,7)` and the gauntlet doors are warps **2/3**, disjoint tiles — and standing on 2F
  still reads `inside_league()`/`at_ever_grande_top()` True (`victory_road.py:1380`).
  ⛔ **No fixture stands on 2F, and its arrival tile has never been measured in our emulator** (the
  decomp's reciprocal warp says `(1,6)`; treat that as decomp-sourced and unverified here).
* The four phantom names are **filed, not fixed** — the `VAR_RESULT` trio needs a decision about
  whether the var belongs in our table at all.
* Prerequisites (2), (3) and (4) are untouched. **Segment 24 stays unwired.**
