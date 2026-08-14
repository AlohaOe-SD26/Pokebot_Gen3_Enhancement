# §Ch20 Room 9 drive — PRE-REGISTERED predictions (2026-08-14)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. Written BEFORE the first
> `--driver ch20room9` run. Sources: a fresh decomp recon by an independent agent (2026-08-14,
> every claim cited to `SeafloorCavern_Room9/scripts.inc`, `Route128/scripts.inc`, `map.json`s,
> `battle_setup.c`, `overworld.c`, `trainer_parties.h`, `wild_encounters.json`; local copies in
> the session scratchpad `decomp/`), our own
> `2026-08-13-ch20-decomp-blockers-and-room8.md` (Blocker 2: the atoll, measured 9/9 by
> `probe_route128_landing.py`), and the live results of `--driver ch20room1/2/6/3/8`.

## The thing under test

`--driver ch20room9` (NEW): re-prove Rooms 1→2→6→3→8, enter Room 9 at `(5,4)`, walk to the
trigger `(17,42)` (⛔ NOT `(16,42)` — that is the sparkle target, `Room9/scripts.inc:38`), ride
out the Archie battle + the Kyogre awakening + the forced warp + the Route 128 Steven scene,
grade on **`VAR_ROUTE128_STATE == 2`**, then execute the measured atoll escape: step SOUTH to
`(38,23)`, face Down, Surf onto `(38,24)`, and prove "the bot can continue" on the OPEN ocean.

**The recon's three facts the driver is built around:**
1. The `(17,42)` trigger's gate is **`VAR_SEAFLOOR_CAVERN_STATE == 0`** (`map.json:130-131`) —
   assert it BEFORE the walk (it is both the re-arm condition after a loss and the "already
   done" guard).
2. **Room 9 has NO wild encounter table** and zero sight cones (`TRAINER_TYPE_NONE` on all
   objects; Archie is `addobject`-ed by the scene) — the 62-step walk is uninterruptible.
3. ⛔ **The first `releaseall` is a TRAP**: Room 9's script tail (`releaseall`, `:140`) executes
   on Route 128 BEFORE the OnFrame scene (`VAR_ROUTE128_STATE == 1`) re-locks. Post-cutscene
   movement is gated on **`VAR_ROUTE128_STATE == 2`** (`Route128/scripts.inc:77`, one command
   before the final `releaseall` `:78`), never on "controllable".

## Pre-registered predictions

| # | prediction | source |
|---|---|---|
| P1 | Rooms 1→8 re-prove (counts → R1 n=11, R2 n=8, R6 n=7, R3 n=6, R8 n=3); Room 9 arrival `(5,4)`. | 5 prior drivers |
| P2 | `VAR_SEAFLOOR_CAVERN_STATE == 0` on arrival (the trigger is armed). | `map.json:130` |
| P3 | The walk `(5,4) → (17,42)` completes with ZERO battles and ZERO interruptions (no wilds, no sight cones; only the sleeping-Kyogre tile `(17,38)` and TM26 ball `(14,5)` are solid). | recon fact 2 |
| P4 | Stepping on `(17,42)` fires the scene; exactly ONE trainer battle follows — **Archie, SINGLE** (`trainerbattle_no_intro`, `.doubleBattle=FALSE`): Mightyena L41, Crobat L41, Sharpedo L43, 2 Super Potions. We win (our L40-49). | `trainers.h:412-422`, `trainer_parties.h:360-376` |
| P5 | The map changes to `ROUTE128` at position `(38,22)` — and AT THAT INSTANT `FLAG_KYOGRE_ESCAPED_SEAFLOOR_CAVERN` is already set, `VAR_SEAFLOOR_CAVERN_STATE == 1`, `VAR_ROUTE128_STATE == 1` (all written `Room9/scripts.inc:115-137`, BEFORE the `warp` at `:138`). | recon table #8-9 |
| P6 | `VAR_ROUTE128_STATE` reaches **2** and only then does control durably return; between the warp and var==2 there is a second `lockall` scene (Archie/Maxie despair, Steven flies in). | `Route128/scripts.inc:10-78` |
| P7 | On release the player faces **Up/North** (last player movement `WalkInPlaceFasterUp`, `Route128/scripts.inc:61`) — ⚠ this is the one previously-unmeasured claim; it is REPORTED, not graded. | decomp, unmeasured live |
| P8 | The escape works exactly as measured: `(38,22)` → step `(38,23)` → Surf onto `(38,24)` = a real launch into the 1,766-tile OPEN ocean (not the 41-tile lagoon), and a real step/path continues from there. | `probe_route128_landing.py` 9/9 |
| P9 | No yes/no, multichoice, or naming screen anywhere in the chain — an A-riding loop with bounded milestones cannot hang on a prompt. Longest scripted delay ≈ 150 frames. | recon §6 |
| P10 | Abnormal weather is active on Route 128 after the warp (`FLAG_SYS_WEATHER_CTRL` set at `:127`) — cosmetic/battle-weather only; Route 128 has ZERO coord events, so nothing re-triggers while escaping. | recon §5 |

## Pre-registered failure modes

* **Losing to Archie** = whiteout to the last heal location: money halved, `VAR_SEAFLOOR_CAVERN_STATE`
  still 0 (the script context dies before `:115`), boulders reset (they reset on EVERY warp),
  grunt trainers stay defeated. The driver detects "map is neither ROOM9 nor ROUTE128" and bails
  LOUD with the loss named — recovery (re-diving the dungeon) is a design decision for the
  chapter, not something to improvise in a driver.
* **A milestone stall** (no map change / var stuck) = the bounded milestone loop fails loud with
  the milestone named and the live `(map, position, var, flag)` tuple printed — never a silent
  hang.
* **The trap on the first `releaseall`**: if the driver moves the instant the game looks
  controllable, it can desync the Steven scene. Guarded by construction (movement gated on
  var==2). If var==2 is reached but the avatar cannot move, that is a REAL finding about the
  release seam.
* **Isaiah** (swimmer, sight 3, patrolling ~`(35,33)`±2 on the water) sits near the southbound
  line. The escape leg only goes one tile south onto `(38,24)` — outside his box — but the
  can-continue path is planned, and if a battle fires there it is ridden out and REPORTED.

## Pre-run adversarial review (before the first drive)

**Verdict KICK-BACK → fixed.** The reviewer caught the milestone loop **mashing A across the
documented release seam** — the exact "museum greeter loop" from `08-MISTAKES.md` (A next to an
NPC *starts* a conversation; Archie/Maxie/Steven stand adjacent during the Route 128 scene),
which could burn the VAR2 budget on a self-inflicted dialogue and produce an unattributable
FAIL. Fixed before the run with the recorded prevention rule: **A only when
`is_waiting_for_input()`, B otherwise** (B advances identically but can never initiate). The
reviewer also verified all three event-name strings exist verbatim in
`modules/data/event_{vars,flags}/emerald.txt`, and noted `get_event_var`/`get_event_flag`
return `-1`/`False` on a typo rather than raising — a name typo would degrade silently, which
is why the names were verified rather than trusted.

## Run transcript & grading

### Run 1 — 2026-08-14 → `ACCEPTANCE: PASS`, first attempt

    [ch20room9] ROOMS 1+2+6+3+8 re-proven; standing in ('SEAFLOOR_CAVERN_ROOM9', (5, 4))
    [ch20room9] ARM-CHECK VAR_SEAFLOOR_CAVERN_STATE=0
    [ch20room9] WALK (5, 4) -> ('SEAFLOOR_CAVERN_ROOM9', (17, 42))
    [ch20room9] MILESTONE ARCHIE-BATTLE reached after ~1836 loop-frames
    [ch20room9] ARCHIE battles_r9=1 detail=[('trainer', False, ('SEAFLOOR_CAVERN_ROOM9', (17, 42)))]
    [ch20room9] MILESTONE WARP-TO-ROUTE128 reached after ~5844 loop-frames
    [ch20room9] MID-WARP kyogre_flag=True scs=1 r128=1 pos=(38, 22)
    [ch20room9] MILESTONE VAR2-CONTROL reached after ~5392 loop-frames
    [ch20room9] RELEASE var2=True facing='Up'
    [ch20room9] ESCAPE at=('ROUTE128', (38, 24)) surfing=True escaped=True
    [ch20room9] OCEAN-PATH (38, 24) -> (38, 27): OK len=5 (source collision=0)
    [ch20room9] CAN-CONTINUE stepping (38, 24) -> (38, 23) tile_type='Shallow Water'  moved=True
    [ch20room9] RESULT rooms_ok=True triggered=True battles_r9=1 kyogre_flag=True var2=True
                landed=True escaped=True ocean_path=True can_continue=True
    [ch20room9] ACCEPTANCE: PASS

**Grading — 10 of 10 pre-registered predictions HELD:**
P1 ✅ (rooms re-proven, Room 9 arrival `(5,4)`); P2 ✅ (`scs=0` armed); P3 ✅ (zero battles and
zero interruptions on the walk); P4 ✅ (exactly one trainer battle, `is_double=False` — Archie
SINGLE, and we won); P5 ✅ (map change → `kyogre_flag=True scs=1 r128=1 pos=(38,22)`, all
mid-warp invariants exact); P6 ✅ (`var2=True`, reached ~5,392 gated loop-frames after the
warp); P7 ✅ **and now MEASURED** — `facing='Up'` on release, the decomp's
`WalkInPlaceFasterUp` claim is live-confirmed; P8 ✅ (`(38,24)` surfing, `OCEAN-PATH OK len=5`
to the dive tile — open component, not the lagoon); P9 ✅ (no prompt hang; the gated A/B ride
never initiated a conversation across the release seam); P10 ✅ (no re-trigger while escaping).

⚠ The can-continue step went `(38,24) → (38,23)` — back onto the shallow sandbar tile it had
just launched from. Legitimate (a real step, tile derived live, not a warp), but worth noting:
the stronger continuation proof is the `OCEAN-PATH OK len=5` toward the dive tile.

### Run 2 — reproduction → **LOST TO ARCHIE. A measured negative result, not a flake.**

Everything mechanical reproduced exactly: Rooms 1→8 re-proven (9/9 pushes, `boulders_visible=8`
at arrival / `12` staged — the KI-77 window again), `ARM-CHECK 0`, the walk locked on `(17,42)`,
the Room 3 double read `is_double=True` again, and the Archie battle fired as BATTLE #5,
`kind=trainer is_double=False`. Then:

    f29914: battle_is_active -> True
    f49487: battle_is_active -> False  outcome=BattleOutcome.Lost
    f49617: ctrl=WhiteoutListener.handle_whiteout_dialogue  bt='NICK whited out!'
    f50844: <no controller on the stack (Manual mode / dropped out)>  pos=(28, 17)

**Two findings:**
1. **The Archie fight is the chain's one stochastic element, and its measured win rate is now
   1/2** (run 1 won; run 2 lost a 19,500-frame fight). The party enters after the Room 1 grunt,
   a Room 2 wild, the Room 3 DOUBLE and any Room 8 wilds, with no heal since Mossdeep — chapter
   design MUST budget for this: a whiteout-retry policy (the Mossdeep Gym "3 attempts"
   precedent — here each retry costs a full ~25-minute re-dive of Rooms 1-8) and/or a pre-boss
   readiness policy (potions from the bag; party order).
2. ‼ **A lost run prints NO RESULT LINE and cannot** — the WhiteoutListener sets Manual and the
   harness drops the mode generator (`main.py`'s KI-71 shape), so the driver's own whiteout
   guard in `_ride_until` never executes (the generator is frozen inside the battle when the
   loss happens and is never resumed). The transcript is the only record. The driver now logs a
   `PRE-ARCHIE PARTY` HP snapshot before the trigger walk so a silent loss is attributable to
   entering condition (added after run 2, before run 3).

The recon's loss model held: whiteout to the last heal location, script context dead (position
`(28,17)` post-respawn; the run-1 assertion that `VAR_SEAFLOOR_CAVERN_STATE` stays 0 could not
be read post-loss — the bot was in Manual — and remains decomp-derived).

### Run 3 — with pre-Archie HP telemetry → `ACCEPTANCE: PASS` (full chain n=2)

    [ch20room9] PRE-ARCHIE PARTY ['Sceptile L49 96/135', 'Zigzagoon L17 0/44',
                'Swellow L40 112/112', 'Wailmer L40 160/160', 'Mightyena L44 122/130',
                'Castform L36 103/103'] usable=5
    f47016: battle_is_active -> False  outcome=BattleOutcome.Won
    [ch20room9] MILESTONE ARCHIE-BATTLE reached after ~1836 loop-frames
    [ch20room9] MILESTONE WARP-TO-ROUTE128 reached after ~5844 loop-frames
    [ch20room9] MID-WARP kyogre_flag=True scs=1 r128=1 pos=(38, 22)
    [ch20room9] MILESTONE VAR2-CONTROL reached after ~5392 loop-frames
    [ch20room9] RELEASE var2=True facing='Up'
    [ch20room9] ESCAPE at=('ROUTE128', (38, 24)) surfing=True escaped=True
    [ch20room9] OCEAN-PATH (38, 24) -> (38, 27): OK len=5
    [ch20room9] RESULT rooms_ok=True triggered=True battles_r9=1 kyogre_flag=True var2=True
                landed=True escaped=True ocean_path=True can_continue=True
    [ch20room9] ACCEPTANCE: PASS

## The summary that matters

* **The chain is DETERMINISTIC and proven n=2**: milestone loop-frame counts are IDENTICAL
  across both passing runs (1836 / 5844 / 5392) and every mid-warp invariant read the same.
  `facing='Up'` measured twice — the last decomp-only claim is now live.
* **The Archie fight is the one stochastic element: 2W / 1L over three runs**, and the
  telemetry names why it is close: the party reaches Archie CHIPPED (run 3: Zigzagoon fainted,
  Sceptile 96/135, usable=5; no heal exists inside the cavern). ⇒ **Chapter design MUST carry:
  (a) a whiteout-retry policy** (Mossdeep Gym's "N attempts" precedent — here one retry costs a
  full re-dive of Rooms 1-8, ~25 min) **and/or (b) a pre-boss readiness policy** (potions from
  the bag / party order before entering Room 9). A 1-of-3 loss rate five badges deep is exactly
  the "rare but kills the best runs" shape KI-63 measured.
* ‼ **A lost run prints NO RESULT and structurally cannot** (whiteout → Manual → generator
  dropped). The `PRE-ARCHIE PARTY` line is the loss's attribution record. Grade any future
  silent transcript by its presence.
