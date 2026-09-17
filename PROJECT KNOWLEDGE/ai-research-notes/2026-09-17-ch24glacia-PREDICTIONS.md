# `--driver ch24glacia` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-17)

> ⛔ Written and committed **before** the driver was executed (`story-drive` §1). Anything the run
> contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Does the §Ch24 repeating unit compose a THIRD time — Phoebe's room → Hall 2 → Glacia's room →
Glacia beaten → and the bot can still leave?**

Rooms 1→2 are driven and passing (`--driver ch24phoebe`, `ACCEPTANCE: PASS`, `missing=[]`,
`evidence/2026-09-17-ch24phoebe-ROOMS1-2.txt`). The claim under test is the one this project has
paid for repeatedly: **proven halves do not make a proven whole.** A third instance is the cheapest
evidence that the unit is a UNIT and not two lucky rooms.

## WHAT IS ALREADY ESTABLISHED (verified by me at source/measurement, not assumed)

| # | fact | how |
|---|---|---|
| E1 | `MapRSE.EVER_GRANDE_CITY_GLACIAS_ROOM` = (16,2), `..._HALL2` = (16,6) | `sandbox-pokebot/modules/map_data.py:1039,1043` |
| E2 | `DEFEATED_ELITE_4_GLACIA` is a REAL flag — id 1277 | `modules/data/event_flags/emerald.txt:1028` |
| E3 | HALL2 is **10 steps, (5,12)→(5,2)** — the corridor's SHAPE | MEASURED, `probe_e4_halls.py`, controls hold (door=0, corner=1) |
| E3b | HALL2's ENDPOINTS: warp 0 (5,12)→`PHOEBES_ROOM`, warp 1 (5,2)→`GLACIAS_ROOM`; `PHOEBES_ROOM` warp 1 (6,2)→`HALL2`; `GLACIAS_ROOM` warp 0 (6,13)→`HALL2`, warp 1 (6,2)→`HALL3` | MEASURED from the ROM warp table, `probe_e4_warp_chain.py` (NEW). **CONTROL: HALL1 → SIDNEYS_ROOM/PHOEBES_ROOM, reproducing the already-LIVE-DRIVEN result ⇒ the method works** |
| E4 | GLACIAS_ROOM is **13×14**, door tiles (6,1)/(6,2), end tile (6,7), trainer tile (6,5) — identical to PHOEBES_ROOM | MEASURED, `probe_e4_door_rom_view.py`, controls PASS |
| E5 | Glacia's room scripts are STRUCTURALLY IDENTICAL to Phoebe's: `EventScript_Defeated` = `setflag` → `SetAdvanceToNextRoomMetatiles` → `msgbox PostBattleSpeech` → `release` | decomp `data/maps/EverGrandeCity_GlaciasRoom/scripts.inc`, read at source |
| E6 | The door-open and entry-seal are **ONE SHARED SCRIPT** called by all four rooms — not "byte-identical layouts" | decomp `data/scripts/elite_four.inc`: `SetAdvanceToNextRoomMetatiles` sets (6,1)/(6,2) impassable=FALSE; `WalkInCloseDoor` does `Common_Movement_WalkUp6` then seals (5..7,12/13) impassable=TRUE |
| E7 | The auto-walk is a LADDER: Phoebe's `OnFrame` gates on `VAR_ELITE_4_STATE, 1`; Glacia's on `VAR_ELITE_4_STATE, 2` | decomp, both `scripts.inc` |
| E8 | `WalkUp6` from the entry warp (6,13) lands on **(6,7)** — the measured end tile, derived independently | decomp `elite_four.inc` |
| E9 | Glacia's team: Sealeo L50, Glalie L50, Sealeo L52, Glalie L52, Walrein L53 @ Sitrus Berry | decomp `src/data/trainer_parties.h:3291-3327` |
| E10 | `post_sidney_L75.ss1` is ITSELF a msgbox-parked post-victory state — which is why `Ch24PhoebeMode` step 1 dismisses | `evidence/2026-09-17-ch24phoebe-ROOMS1-2.txt:4` (`f0: ... WaitForButton scripts=['EverGrandeCity_SidneysRoom_EventScript_Defeated','Std_MsgboxDefault']`) |
| E11 | Gate baseline before any change: **all 63 enforcing gates PASS** | `run_gates.py`, 198.0s, this session |

### The one REAL difference, and why it is benign here

Our docs say *"Glacia is the first room whose in-battle lose-text carries `\p`"*. **True, and the
count is now exact — but the alarming reading of it is wrong:**

| text | Phoebe | Glacia |
|---|---|---|
| in-battle `Text_Defeat` | 0 `\p` → **1 page** | 2 `\p` → **3 pages** |
| `Text_PostBattleSpeech` | 3 `\p` → **4 pages** | 1 `\p` → **2 pages** |
| **total post-fight pages** | **5** | **5** |

⛔ **AND TOTALLING THOSE TWO ROWS WAS THE WRONG MOVE — an adversarial reviewer corrected me.** The
two halves are consumed by DIFFERENT machinery and must not be added: the in-battle text is printed
by the battle script (`printstring STRINGID_TRAINER1LOSETEXT`; `trainerbattle_no_intro` contains no
`msgbox` at all) and is cleared by `BattleListener`, while `Text_PostBattleSpeech` is an overworld
`msgbox` cleared by the NEXT room's dismiss. Stated correctly: **Glacia's IN-BATTLE load is heavier
(3 pages vs 1), and her POST-BATTLE dismiss load is LIGHTER (2 vs 4).**

✅✅ **AND THE IN-BATTLE HALF IS A CLOSED QUESTION — ON MEASURED PRECEDENT, NOT REASONING.** Two
independent facts retire it:
1. **This bot has already beaten far worse, live.** Every Gym Leader's in-battle lose text uses the
   same `STRINGID_TRAINER1LOSETEXT` slot. **Juan's carries SIX `\p` (7 stops, vs Glacia's 3)** and
   **Roxanne's four `\p` plus an `\l` (6 stops)** — both beaten in this harness.
2. **`BattleListener._wait_until_battle_is_over` is `while self._in_battle` — UNBOUNDED and
   SELF-EXTENDING.** `_in_battle` cannot clear until the battle script has finished printing, so
   longer text automatically buys MORE frames of B-pressing. The 51 frames Phoebe took is a
   consequence of her text length, not a cap on it.

⇒ the `\p` difference is **real and benign**, and the residue parks in the overworld exactly as
Phoebe's did for the next room's dismiss loop to clear (500 presses of headroom vs the 50 measured).

## FIXTURE AND METHOD

⛔ **There is no post-Phoebe fixture, and that is the first thing this work produces.**

**Step A — extend the fixture ladder.** Add a POST-FIGHT capture to the proven `Ch24PhoebeMode`,
gated on a NEW env var (`CH24_PHOEBE_POST_CAPTURE`) so that with the var unset the driver's
behaviour is byte-for-byte what it already was. Re-run `ch24phoebe` from the pinned
`post_sidney_L75.ss1` (md5 `fd61347c6fdd677c6bf42d1851a4e92e`) to produce `post_phoebe_L75.ss1`.
The whole Phoebe run costs **~15,600 frames (~16 s)**, so this is nearly free.

⭐ **The capture is taken at the SAME lifecycle point that `post_sidney_L75.ss1` occupies** —
post-victory, victory msgbox still parked, standing at (6,6). That is deliberate: it makes the new
fixture a DROP-IN analogue of the one the template already consumes, instead of a differently-shaped
state the copied driver would mishandle.

**Capture guard (all three conjuncts, or nothing is written):**
`DEFEATED_ELITE_4_PHOEBE == True` ∧ on `PHOEBES_ROOM` ∧ the live exit door (6,1)/(6,2) reads OPEN.
The third conjunct is the one that matters: it refuses to mint a fixture the next leg could not
leave. A fixture captured from a LOST fight, or from a room whose door never opened, is worse than
no fixture — it would send the next session to debug a driver against a poisoned start state.

**Step B — `--driver ch24glacia`**, a copy of `Ch24PhoebeMode` with the substitutions below, run
from `post_phoebe_L75.ss1`.

## THE ARMS

| arm | env | what it does | expected |
|---|---|---|---|
| **TREATMENT** | *(none)* | dismiss → bag heal → door → HALL2 → door → locate Glacia LIVE → engage → grade | `ACCEPTANCE: PASS`, `missing=[]` |
| **VACUITY** | *(none)*, but started from `post_sidney_L75.ss1` | wrong room | **refuses at the premise, takes NO readings**, `ACCEPTANCE: FAIL` |
| **FAULT `NOENGAGE`** | `POKEBOT_CH24_FAULT_NOENGAGE=1` | does everything but the A/B engage loop | `ACCEPTANCE: FAIL` with `missing=['P-ENGAGED','P-OUTCOME']` — for ITS OWN reason |

The VACUITY arm is the mechanical test `story-drive` §2 demands: *point the driver at a state it did
not produce and confirm it cannot print PASS.* The `NOENGAGE` arm exists so "we ended up with the
Glacia flag set" cannot be satisfied by anything except actually fighting her.

## PREDICTIONS

| # | reading | prediction | falsifier — what it would mean |
|---|---|---|---|
| P1 | `PRE at` | `((16,1), (6,6))` — PHOEBES_ROOM, standing where the Phoebe fight was won | any other tile ⇒ the capture point is not what I read off the Phoebe log; re-derive E10 |
| P2 | `dismiss_presses` | **10–80** (Phoebe's measured 50; same 5 pages) | 0 ⇒ nothing was parked, so the fixture is NOT the post-victory shape ⇒ E10 is wrong. 500 (budget) ⇒ the box never cleared ⇒ B is not the right key here |
| P3 | `P-HEAL` | taken; `heal_ready=True`. HP delta SMALL — the Phoebe fight cost Mightyena only 13 HP (`214/230`) | a large heal ⇒ the fight was costlier than measured; a raise ⇒ ⛔ the sealed-zone rule was violated |
| P4 | `after_door` | `((16,6), (5,12))` — HALL2 landing | anything else ⇒ E3 wrong, or `_pass_through_door` picked a different warp |
| P5 | `room_landing` | GLACIAS_ROOM, y **between 7 and 13** — RECORDED not asserted (the entry cutscene is mid-`WalkUp6`) | not on GLACIAS_ROOM ⇒ E3's far door is wrong |
| P6 | `objects_seen` | exactly **`[(6,5)]`** — one NPC, Glacia, north of us | more than one object ⇒ the `next(... t[1] < here[1] ...)` heuristic is picking blind and must be tightened; zero ⇒ camera-window trap (§5) |
| P7 | `glacia_at` / `stand_at` | `(6,5)` / `(6,6)` | — |
| P8 | `battle_frames_waited` | **0** — recorded, but ⛔ **NOT a discriminator for anything.** A reviewer showed 0 is the ONLY value a healthy run can produce (the generator is not resumed until the fight ENDS), and on a *true* in-battle stall the driver is never resumed at all, so the key is **never written**. The real instrument for an in-battle stall is the harness's own `NO-PROGRESS`/`STUCK` dump | a non-zero value would mean the suspension model is wrong |
| P9 | `glacia_flag` | **True** (we expect to win at L75 vs L50-53) | False ⇒ a RESULT, not a failure: the party lost or fled. The grade does NOT require it |
| P10 | `exit_door_live` | `{(6,1):0, (6,2):0}` — OPEN, because `SetAdvanceToNextRoomMetatiles` ran (E6) | blocked ⇒ the victory script did not complete ⇒ the bot is SEALED IN and room 4 is unreachable — a FAIL however the fight went |
| P11 | `entry_seal_live` | `{(5,13):3, (6,13):3, (7,13):3}` — SEALED behind us (E6, `WalkInCloseDoor`) | 0s ⇒ the entry cutscene never ran ⇒ `VAR_ELITE_4_STATE` was not 2 on entry (E7) |
| P12 | whole run | `battles=1`, `whiteouts=0` | `battles>1` ⇒ something else engaged us; `whiteouts=1` ⇒ a RESULT (the party lost), and `ResetEliteFour` has spent the fixture |

### Battle-shape predictions (E9) — recorded so the fight is not a black box

| # | prediction | why |
|---|---|---|
| B1 | **No zero-damage loop** (the `#24-ghostzerodamage` shape does NOT recur) | every one of our battlers has a neutral-or-better move; Sceptile's **Rock Smash is Fighting, 2× on the whole team** |
| B2 | ⛔ **CORRECTED BY A REFUTER — "Sheer Cold is a structural zero" IS ONLY TRUE FOR THE FOUR L75+ BATTLERS.** The decomp gate is a level COMPARISON (`attacker.level >= target.level`), then `chance = accuracy + (attackerLvl - targetLvl)`. Walrein L53 vs our L75 ⇒ 53 ≥ 75 false ⇒ guaranteed miss. **But vs Castform L36 ⇒ ~47%, and vs Zigzagoon L19 ⇒ ~64%.** | ⇒ the mules are NOT safe, and they only ever enter via a faint cascade — i.e. **the `#24-ghostreplacement` path and Sheer Cold COMPOUND**: a bad replacement pick puts a mon on the field that Walrein can then OHKO outright |
| B3 | The most likely disruptors are **Explosion** (Glalie L52) and **Attract** (Sealeo L52) | Explosion can force a faint ⇒ exercises the OPEN `#24-ghostreplacement` chooser. ⛔ **Attract is a VOLATILE, not a PSS status — `Full Heal` does not cure it**, and it is not in `TURN_COSTING_STATUSES` |
| B4 | Freeze, if it lands, IS handled | `Full Heal`, in-battle, via `choose_status_or_revive_item` (18 in the bag) |
| B5 | 0 or 1 of our mons faint | L75 vs L50-53; Phoebe cost 13 HP total |
| B6 | ⚠ **A CRIT CAN ONE-SHOT A BATTLER — do not write "nothing can one-shot us".** Gen-3 crits are ×2 at ~1/16 per attack, and several no-crit HIGH rolls already exceed 50% max HP: Sealeo L52 Blizzard on Swellow ~67% ⇒ crit ~134%; Walrein L53 Ice Beam on Swellow ~70% ⇒ crit ~140% | ⇒ Swellow is the fragile battler here (Normal/Flying, 2× Ice) |
| B7 | ⭐ **Castform is LESS fragile than it looks, and only while Hail is up.** Forecast sets its battle type to **ICE** under Hail (3 of Glacia's 5 carry Hail), so Ice moves become 0.5× ⇒ a 2HKO not an OHKO, and it stops taking hail chip | if Castform is one-shot by an Ice move with Hail up, Forecast is not behaving as read |

⚠ B1–B5 are **CALCULATED FROM SOURCE DATA, NOT MEASURED.** They are here to be graded, not relied
on. If B3 fires and the chooser picks Zigzagoon, that is a live reproduction of
`#24-ghostreplacement` in a THIRD room and should be filed as such, not treated as a drive failure.

## THE SUBSTITUTION LIST (what actually changes from `Ch24PhoebeMode`)

⛔ **THE HANDOFF SAYS "THREE CHANGES". A REFUTER SHOWED THAT IS INCOMPLETE — HERE IS THE REAL LIST.**

1. `PHOEBES_ROOM`→`GLACIAS_ROOM`, `HALL1`→`HALL2`, premise map `SIDNEY`→`PHOEBE`.
2. `VICTORY_FLAG = "DEFEATED_ELITE_4_PHOEBE"` → `"..._GLACIA"` — **ONE class constant, two consumers.**
3. ‼ **THREE env vars, not two.** `CH24_PHOEBE_CAPTURE`, `POKEBOT_CH24_FAULT_NOROOMHEAL`, **and the
   new `CH24_PHOEBE_POST_CAPTURE`**. A copy that inherits the last one is the nastiest case: the
   capture REFUSES TO OVERWRITE, so a room-3 run would find `post_phoebe_L75.ss1` already present,
   log `SKIPPED`, and **silently produce no room-4 fixture on a successful run.**
4. ‼‼ **THE FOURTH DIFFERENCE THE HANDOFF OMITS, AND IT IS LOAD-BEARING:** the two rooms' `OnFrame`
   entry cutscenes gate on **different values** of `VAR_ELITE_4_STATE` (Phoebe `==1`→sets 2; Glacia
   `==2`→sets 3). That is a constraint on the FIXTURE'S LINEAGE, invisible to warp tables and
   collision grids. ✅ Verified True for `post_phoebe_L75.ss1` (reads **2**) before building.
5. Tag / driver name / class name / `--driver` choices list / dispatch `elif` / reading keys.

⭐ **TWO deliberate IMPROVEMENTS over the template, not a copy:**
* The premise gains a second conjunct, `DEFEATED_ELITE_4_GLACIA == False` — the anti-vacuity
  property stated directly rather than inferred from geography.
* ‼ **The step-9 capture guard now reads the FLAG via `VICTORY_FLAG`, never `R.get("<room>_flag")`.**
  A reviewer found that landmine in the version I had already shipped: a room-N copy that renames
  the dict key at its one obvious site gets `R.get(...) → None`, so `won` is silently `False` and the
  capture **refuses to mint the next room's fixture on a perfect run**, logging a refusal as if the
  run had failed. Fixed in `Ch24PhoebeMode` too, so the hazard cannot propagate.

## ⚠ A CAVEAT THAT LIMITS WHAT `P-CONTINUE` PROVES (found by a refuter, verified at source)

The open-door metatiles at (6,1)/(6,2) are written by **two** scripts, not one:
`PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles` (the victory) **and**
`PokemonLeague_EliteFour_EventScript_ResetAdvanceToNextRoom`, which each room's `OnLoad` calls via
`call_if_set FLAG_DEFEATED_ELITE_4_<NAME>`. ⇒ **merely RELOADING a fixture whose DEFEATED flag is
already set re-opens the door.** So `P-CONTINUE` is meaningful DURING a run (we are in the room, no
`OnLoad` re-runs) but would pass **vacuously** on a reloaded post-victory save. This is exactly why
the VACUITY arm exists and why the driver must never be graded from its own output.

## HOW THIS GETS GRADED

After the run, this file gets a **GRADED** section appended: every P/B row marked ✅ met, ❌ refuted,
or ⚠ unreadable, with the literal log line beside it. A row that cannot be quoted was not measured.

---

# GRADED — 2026-09-17, AFTER THE RUNS

**Evidence (committed):** `tools/story-dev/evidence/2026-09-17-ch24glacia-{TREATMENT,VACUITY-WRONG-ROOM,VACUITY-OWN-OUTPUT,FAULT-NOENGAGE}.{log,stdout.txt}`
and `...-FIXTURE-VERIFY-BY-RELOAD.txt`, `2026-09-17-e4-warp-chain-MEASURED.txt`.

## HEADLINE: ✅✅✅ **GLACIA IS BEATEN — THREE OF FIVE ROOMS. THE UNIT COMPOSES A THIRD TIME.**
`ACCEPTANCE: PASS`, `readings=[G-CONTINUE, G-DISMISS, G-ENGAGED, G-HALL2, G-HEAL, G-OUTCOME, G-ROOM]`,
`missing=[]`, `battles=1`, `whiteouts=0`. Room 4's start state `post_glacia_L75.ss1` is minted and pinned.

## THE THREE ARMS

| arm | result | verdict |
|---|---|---|
| TREATMENT (`post_phoebe_L75.ss1`) | `ACCEPTANCE: PASS`, `missing=[]` | ✅ |
| VACUITY — wrong room (`post_sidney_L75.ss1`) | refused at the premise, **zero readings**, `ACCEPTANCE: FAIL` | ✅ |
| VACUITY — **its own output** (`post_glacia_L75.ss1`) | refused, naming `DEFEATED_ELITE_4_GLACIA=True`, zero readings | ✅ the test `story-drive` §2 demands |
| FAULT `NOENGAGE` | walked the whole unit identically, then pressed nothing ⇒ `battles=0`, bounded loop expired, `missing=['G-CONTINUE','G-ENGAGED','G-OUTCOME']`, `ACCEPTANCE: FAIL` | ✅ fails for **its own** reason |

⚠ **HONEST SCOPE ON THE FAULT ARM:** `G-CONTINUE` is missing because execution **never reached it**
(the raise happens at the engage step), **not** because the exit door was measured shut. This arm does
NOT prove the door stays closed without a victory.

## P-ROW GRADES

| # | predicted | measured | |
|---|---|---|---|
| P1 | `((16,1),(6,6))` | `R start = ((16, 1), (6, 6))` | ✅ |
| P2 | 10–80 presses | `R dismiss_presses = 77` | ✅ ⭐ and it tracks the **previous** room's text (Phoebe's 4-page speech), not Glacia's |
| P3 | heal taken, `ready=True`, small delta | `heal_actions=0`, `heal_plan=[]`, `heal_ready=True` | ⚠ **MET BUT REFINED:** the delta was **zero**. At `Mightyena 214/230 (93%)` the readiness predicate plans nothing, where the Phoebe run planned a heal at `187/227 (82%)` ⇒ **the threshold lies between 82% and 93%**, measured |
| P4 | `((16,6),(5,12))` | `R after_door = ((16, 6), (5, 12))` | ✅ |
| P5 | GLACIAS_ROOM, 7 ≤ y ≤ 13 | `R room_landing = ((16, 2), (6, 11))` | ✅ |
| P6 | exactly `[(6,5)]` | `R objects_seen = [(6, 5)]` | ✅ — and it is safe *by construction*: Glacia is the only `object_event` in her map |
| P7 | `(6,5)` / `(6,6)` | `R glacia_at = (6, 5)`, `R stand_at = (6, 6)` | ✅ |
| P8 | 0, and uninformative | `R battle_frames_waited = 0` | ✅ (kept as a record, not a discriminator) |
| P9 | `True` | `R glacia_flag = True` | ✅ |
| P10 | `{(6,1):0,(6,2):0}` | `R exit_door_live = {(6, 1): 0, (6, 2): 0}`, `open=True` | ✅ |
| P11 | `{(5,13):3,(6,13):3,(7,13):3}` | exactly that | ✅ |
| P12 | `battles=1, whiteouts=0` | exactly that | ✅ |

## B-ROW GRADES (the fight)

| # | verdict |
|---|---|
| B1 | ✅ **No zero-damage loop.** The fight ran ~21,000 frames and was WON; the `#24-ghostzerodamage` shape does not recur against Ice |
| B2 | ⚠ **UNTESTED.** Sheer Cold never resolved against a mule because no mule ever entered. The corrected claim (structural zero for L75+ battlers only, ~47% vs Castform, ~64% vs Zigzagoon) stands as READ, not measured |
| B3 | ⚠ **PARTIAL.** A faint DID occur (Mightyena). ⛔ **The CAUSE is not in the log** — Explosion is the prime suspect but this run cannot distinguish it from accumulated Ice damage. Do not write "Explosion KO'd Mightyena" |
| B5 | ✅ **1 faint — the upper bound of the prediction.** ⛔ And the cost is far above Phoebe's: **Mightyena 0/230 KO'd and Wailord 396→188.** Glacia is the first genuinely expensive room |
| B6 | ⚠ UNTESTED — Swellow never entered |
| B7 | ⚠ UNTESTED — Castform never entered |

## ⭐ THE FINDINGS WORTH CARRYING FORWARD

1. ✅✅ **THE FAINT CHOOSER DREW CORRECTLY, LIVE, IN A THIRD ROOM.** Mightyena fainted and the
   replacement was **Wailord** (the Ice-resisting wall), not Zigzagoon. **How we know:** Zigzagoon
   ends `48/48` and Castform `103/103`, **both with zero EXP gained** ⇒ neither mule ever entered,
   and Wailord took the final KO (exp `583024 → 586292`) and all 208 points of damage.
   ‼ This is **one trajectory against an Ice specialist** — it does NOT refute `#24-ghostreplacement`,
   whose measured failure is specifically about a Ghost and `cannot_damage`. It is a data point that
   the chooser is not unconditionally broken.
2. ⛔ **`hp_entering_glacia` IS A FAKE READING, AND IT PROVED TRAP 1 AGAIN.** It is byte-identical to
   `hp_after_glacia` because a driver is suspended across the fight, so "before" was sampled *after*.
   The driver keeps it only as a record. **Anyone reading these logs must not treat it as a
   before/after pair.** (`Ch24PhoebeMode`'s docstring predicted exactly this.)
3. ⭐ **TRAP 2 REPRODUCED IN A THIRD ROOM.** `R elite4_state_in_room = 2` while standing in Glacia's
   room, but the captured fixture reads **3** — the entry cutscene had not finished writing it.
   ⇒ *never dispatch on `VAR_ELITE_4_STATE`*, now confirmed for Sidney, Phoebe **and** Glacia.
4. ‼ **ATTRITION IS NOW REAL AND `#24-leg2spec` NEEDS THIS NUMBER.** Sidney→Phoebe cost 13 HP total.
   Glacia cost **a KO plus 208 HP**, and repairing it spends **the first of only three Revives**
   (plus a Hyper Potion and a Full Restore) — measured offline from the captured state, with a
   healthy-party control that plans nothing.
5. ⭐ **THE HALL-ENDPOINT CLAIM IS NOW MEASURED, NOT ASSERTED.** A refuter caught that
   `probe_e4_halls.py`'s `HALL2  PHOEBE -> GLACIA` label is a hardcoded string in its own table —
   it reads collision only. New `probe_e4_warp_chain.py` reads the ROM warp table, with HALL1 as a
   control reproducing the already-driven result.
