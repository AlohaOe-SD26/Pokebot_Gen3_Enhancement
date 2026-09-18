# `--driver ch24drake` — PREDICTIONS, FILED BEFORE THE RUN (2026-09-17, late)

> ⛔ Written and committed **before** the driver was executed (`story-drive` §1). Anything the run
> contradicts is a **RESULT**, not a driver failure.

## THE QUESTION

**Does the §Ch24 repeating unit compose a FOURTH time — and does it survive a start state that is
DAMAGED?** Rooms 1→3 all began from a healthy party. `post_glacia_L75.ss1` does not: it carries a
**fainted Mightyena (0/230)** and a Wailord at 188/396. This is the first room entered on a party the
previous room broke, and it is the last room the unit shape applies to at all.

## WHAT IS ALREADY ESTABLISHED (verified by me at source/measurement, not assumed)

| # | fact | how |
|---|---|---|
| E1 | `DEFEATED_ELITE_4_DRAKE` is a REAL flag — id **1278** | `modules/data/event_flags/emerald.txt:1029` |
| E2 | Drake's `OnFrame` gates the entry cutscene on **`VAR_ELITE_4_STATE, 3`** and sets **4** | decomp `EverGrandeCity_DrakesRoom/scripts.inc`, read at source |
| E3 | `post_glacia_L75.ss1` reads `VAR_ELITE_4_STATE = 3` | MEASURED by reload, with controls |
| E4 | Warp chain: `GLACIAS_ROOM (6,2) → HALL3`; `HALL3 (5,12) → GLACIAS_ROOM`, `(5,2) → DRAKES_ROOM`; `DRAKES_ROOM (6,13) → HALL3`, `(6,2) → HALL4` | MEASURED from the ROM warp table, `probe_e4_warp_chain.py`, HALL1 as a control |
| E5 | HALL3 is **10 steps**, `(5,12)→(5,2)`, like HALL1/HALL2 | MEASURED, `probe_e4_halls.py` |
| E6 | DRAKES_ROOM is **13×14**, door tiles (6,1)/(6,2) ROM-BLOCKED, end tile (6,7), trainer tile (6,5) | MEASURED, `probe_e4_door_rom_view.py`, controls PASS |
| E7 | Drake's team: Shelgon L52, Altaria L54, Kingdra L53, Flygon L53, **Salamence L55 @ Sitrus** | decomp `src/data/trainer_parties.h` |
| E8 | The between-rooms heal plan for THIS exact state is `[(0,'Revive',…), (0,'Hyper Potion',…), (4,'Full Restore','Wailord at 188/396')]` | MEASURED offline, with a healthy-party CONTROL that plans nothing |

### ‼ THE ONE STRUCTURAL DIFFERENCE FROM ROOMS 1–3 — read before calling this a rename

Drake's `EventScript_Defeated` runs **two extra instructions before `setflag`**:

```
setvar VAR_0x8004, FANCOUNTER_DEFEATED_DRAKE
special Script_TryGainNewFanFromCounter
setflag FLAG_DEFEATED_ELITE_4_DRAKE
call PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles
msgbox ..._Text_PostBattleSpeech, MSGBOX_DEFAULT
```

Rooms 1–3 have no such prelude (the Trainer Fan Club counter). ✅ It does not disturb this driver:
the flag is still set **before** the door opens, which is exactly what the step-8 capture guard
conjuncts on. ⚠ Drake's room also reuses **Sidney's** `OnWarp` table — the decomp itself comments
*"Unused, Drake uses Sidneys identical OnWarp for some reason"*. Benign.

### Text counts, read at source — they bite the NEXT driver, not this one

| text | Glacia | Drake |
|---|---|---|
| in-battle `Text_Defeat` | 2 `\p` → 3 pages | **0 `\p` → 1 page** |
| `Text_PostBattleSpeech` | 1 `\p` → 2 pages | **5 `\p` → 6 pages** (the longest in the gauntlet) |

⇒ Drake's *in-battle* load is the lightest of any room; his *post-battle* speech is the heaviest, and
it parks for **room 5's** dismiss loop. At the measured rate (77 presses cleared a 4-page speech)
that is ~110 presses against a 500-press budget.

## ARMS

| arm | env / fixture | expected |
|---|---|---|
| **TREATMENT** | `post_glacia_L75.ss1` | `ACCEPTANCE: PASS`, `missing=[]` |
| **VACUITY — wrong room** | `post_phoebe_L75.ss1` | ✅ **ALREADY RUN** (it doubled as the import smoke test): refused, zero readings, `ACCEPTANCE: FAIL` |
| **VACUITY — own output** | `post_drake_L75.ss1` (after the treatment mints it) | refuse, naming `DEFEATED_ELITE_4_DRAKE=True` |
| **FAULT `NOENGAGE`** | `POKEBOT_CH24_FAULT_NOENGAGE=1` | FAIL with `D-ENGAGED`/`D-OUTCOME` missing, for its own reason |

## PREDICTIONS

| # | reading | prediction | falsifier |
|---|---|---|---|
| P1 | `PRE at` | `((16,2), (6,6))` — GLACIAS_ROOM | any other tile ⇒ the capture point is not what the Glacia run recorded |
| P2 | `PRE hp` | **Mightyena 0/230 — FAINTED**, Wailord 188/396 | a healthy party ⇒ the wrong fixture is loaded |
| P3 | `dismiss_presses` | **10–60** (Glacia's PostBattleSpeech is only 2 pages, vs the 77 measured for Phoebe's 4) | 500 (budget) ⇒ B is not clearing this box |
| P4 | `D-HEAL` | ⭐ **THE INTERESTING ONE: `heal_actions = 3`**, Mightyena **revived** and topped up, Wailord → 396/396, and **Revive 3 → 2** | `heal_actions=0` ⇒ the readiness predicate tolerates a FAINTED mon, which would be a defect worth filing. A raise ⇒ the sealed-zone rule was violated |
| P5 | `after_door` | `((16,7), (5,12))` — HALL3 landing | anything else ⇒ E4/E5 wrong |
| P6 | `room_landing` | DRAKES_ROOM, y between 7 and 13 (cutscene mid-`WalkUp6`) | not DRAKES_ROOM ⇒ E4's far door is wrong |
| P7 | `objects_seen` | exactly `[(6,5)]` — Drake alone | more than one ⇒ the "first object north" heuristic is picking blind |
| P8 | `elite4_state_in_room` | **2 or 3** — RECORDED, not asserted; the cutscene writes 4 late (trap 2, reproduced 3× already) | 4 on arrival would be new information |
| P9 | `drake_flag` | **True** | False ⇒ a RESULT (lost or fled), not a failure. The grade does not require it |
| P10 | `exit_door_live` | `{(6,1):0,(6,2):0}` — OPEN | blocked ⇒ sealed in, room 5 unreachable ⇒ FAIL however the fight went |
| P11 | `entry_seal_live` | `{(5,13):3,(6,13):3,(7,13):3}` | 0s ⇒ the entry cutscene never ran ⇒ E2/E3 wrong |
| P12 | run totals | `battles=1`, `whiteouts=0` | `whiteouts=1` ⇒ a RESULT; `ResetEliteFour` has spent the fixture and it must be RELOADED |

### Battle-shape predictions (from E7 + our own type data)

| # | prediction |
|---|---|
| B1 | ⭐ **Ice Beam is 4× on THREE of five** (Altaria, Flygon, Salamence), 2× on Shelgon, **1× on Kingdra** — the one it does not answer. Flygon's LEVITATE makes Ice the only super-effective type reachable on it |
| B2 | **No OHKO moves and no Attract** in Drake's set — mechanically simpler than Glacia |
| B3 | The threats are **Salamence L55** (Flamethrower/Dragon Claw/Rock Slide/Crunch, + Sitrus), **Dragon Dance** setup on Altaria and Kingdra, and **Flygon's Earthquake** |
| B4 | ⚠ **Kingdra's Smokescreen** drops accuracy — a plausible cause of a long fight or a missed KO. Not handled by our status policy (it is a volatile, not a PSS status) |
| B5 | **0–2 of our mons faint.** ⛔ A faint here is worse than in Glacia: Revives are unusable IN battle (`KI-100`), so a mon that goes down stays down until room 5's heal, and only **2 Revives** remain after this room's |

⚠ B1–B5 are **CALCULATED FROM SOURCE DATA, NOT MEASURED.** They are here to be graded, not relied on.

## HOW THIS GETS GRADED

A **GRADED** section is appended after the runs: every P/B row marked ✅ met, ❌ refuted, or
⚠ unreadable, with the literal log line beside it. A row that cannot be quoted was not measured.

## ⚠ AMENDED BEFORE THE RUN (still pre-drive) — the grade gained a HEAL conjunct

A 4-angle recon's adversarial arm landed while this file was being written and found that **the
grade could not FAIL on a broken heal**: `taken.add("D-HEAL")` is unconditional (it must be — an
empty plan is the common case between easy rooms) and a raising heal is deliberately swallowed into
`R["heal_error"]` (the zone is sealed; refusing there strands the bot). Both halves were blind to it.

⇒ `ok` now also requires **`R["heal_ready"] is True`**. It is **not vacuous and not retroactive**:
rooms 1–3 all measured `heal_ready=True` (room 3 with an *empty* plan, which `plan_healing` reports
ready for), so it could not have failed them. Room 4 is the **first room whose heal plan is
non-empty**, so it is the first room where this can bite.

⇒ **P4 is upgraded from a reading to a GRADE-BEARING assertion**, and a new prediction follows:

| # | prediction | falsifier |
|---|---|---|
| P13 | `POKEBOT_CH24_FAULT_NOROOMHEAL=1` now **FAILS**, with `heal_ready=None` named in the log | if it PASSES, the conjunct is not wired |

⭐ **AND THAT ARM IS WORTH RUNNING FOR THE FIRST TIME.** On room 3 it was **measured-vacuous** —
`heal_plan = []`, so the arm and the treatment were the same run, and no room-3 NOROOMHEAL evidence
file exists. Room 4's plan is `Revive → Hyper Potion → Full Restore`, so the arm finally discriminates.

## ⚠ TWO DEFECTS THE RECON SURFACED — FILED, NOT FIXED HERE (they are not room 4's scope)

1. **`plan_healing` burns a FULL RESTORE on a scratch.** It picks "cheapest sufficient" by
   `effective_heal`, which returns `total_hp` for a Full Restore — so on any mon with `total_hp < 200`
   (Castform 103, Zigzagoon 48) a Full Restore outranks a Hyper Potion. Reported measured:
   `Castform 90/103 → ['Full Restore']`. Gate #36 cannot see it because its hand-made bag holds
   Potion/Super Potion that the real gauntlet basket does not. ⛔ NOTE: this is an agent's
   measurement and is **a NOTE until reproduced here**.
2. **Revive target is ranked by LEVEL alone**, so a fainted **Wailord L75** loses the tiebreak to
   Mightyena L76 — and Wailord is the Ice Beam carrier, i.e. the answer to Drake.

⭐ **AND ONE FACT THAT HARDENS A STANDING RULING:** Wallace's `object_event` carries
`"script": "0x0"` and `"flag": "0"` — **he is not interactable at all**. Room 5 therefore cannot be
"the fifth instance of the unit" in an even stronger sense than the docs already say: there is no
trainer to walk up to and press A on.

---

# GRADED — 2026-09-17 (late), AFTER THE RUNS

**Evidence (committed):** `tools/story-dev/evidence/2026-09-17-ch24drake-{TREATMENT,VACUITY-WRONG-ROOM,VACUITY-OWN-OUTPUT,FAULT-NOROOMHEAL}.stdout.txt`
and `...-FIXTURE-VERIFY-BY-RELOAD.txt`.

## HEADLINE: ✅✅✅ **DRAKE IS BEATEN — FOUR OF FIVE ROOMS. THE UNIT COMPOSED A FOURTH TIME, ON A DAMAGED PARTY.**
`ACCEPTANCE: PASS`, `missing=[]`, `battles=1`, `whiteouts=0`, `drake_flag=True`.
`post_drake_L75.ss1` minted and pinned (`51cd43a8e427`, `VAR_ELITE_4_STATE=4`).

## THE FOUR ARMS

| arm | result | |
|---|---|---|
| TREATMENT | `ACCEPTANCE: PASS`, `missing=[]` | ✅ |
| VACUITY — wrong room | refused, zero readings | ✅ |
| VACUITY — **own output** | refused naming `DEFEATED_ELITE_4_DRAKE=True`, zero readings | ✅ |
| FAULT `NOROOMHEAL` | `ACCEPTANCE: FAIL`, `missing=['D-HEAL']`, and the new conjunct fired by name: `⛔ GRADE: heal_ready=None — the party was NOT brought to fighting shape` | ✅ |

## P-ROW GRADES

| # | predicted | measured | |
|---|---|---|---|
| P1 | `((16,2),(6,6))` | `R start = ((16, 2), (6, 6))` | ✅ |
| P2 | Mightyena 0/230, Wailord 188/396 | exactly that | ✅ |
| P3 | 10–60 presses | `R dismiss_presses = 35` | ✅ ⭐ and it tracks the PREVIOUS room's speech: Glacia's 2 pages → 35, vs Phoebe's 4 pages → 77. The model holds across three rooms |
| P4 | `heal_actions=3`, Mightyena revived, Wailord full, Revive 3→2 | `heal_actions = 3`, `heal_ready = True`, `Mightyena 0/230 → 230/230`, `Wailord 188 → 396`, bag `HP 35→34, FR 3→2, Revive 3→2` | ✅✅ **the offline `plan_healing` projection matched the live run ACTION FOR ACTION** |
| P5 | `((16,7),(5,12))` | exactly that | ✅ |
| P6 | DRAKES_ROOM, 7≤y≤13 | `R room_landing = ((16, 3), (6, 11))` | ✅ |
| P7 | exactly `[(6,5)]` | `R objects_seen = [(6, 5)]` | ✅ |
| P8 | 2 or 3 | `R elite4_state_in_room = 3` (the fixture then reads **4**) | ✅ trap 2 reproduced a FOURTH time |
| P9 | True | `R drake_flag = True` | ✅ |
| P10 | `{(6,1):0,(6,2):0}` | exactly that, `open=True` | ✅ |
| P11 | `{(5,13):3,(6,13):3,(7,13):3}` | exactly that | ✅ |
| P12 | `battles=1, whiteouts=0` | exactly that | ✅ |
| P13 | NOROOMHEAL now FAILS with `heal_ready=None` named | exactly that | ✅ — **but see the honest scope note below** |

## B-ROW GRADES

| # | verdict |
|---|---|
| B1 | ✅ **Consistent and strongly suggested: Wailord came out of Drake at 396/396, UNTOUCHED.** Ice Beam swept. ⚠ Per-target effectiveness was not instrumented, so 4×-on-three is still CALCULATED, not measured |
| B2 | ✅ No OHKO/Attract behaviour observed |
| B3/B4 | ⚠ **UNTESTED in detail** — the driver is suspended across the fight, so no per-turn record exists. Kingdra-as-turn-sink was neither confirmed nor refuted |
| B5 | ✅ **1 faint (Mightyena), inside the predicted 0–2.** Sceptile also took 132 (205→73). 2 Hyper Potions used in battle |

## ‼ HONEST SCOPE — WHAT THE `NOROOMHEAL` ARM DOES *NOT* PROVE

It failed on **`missing=['D-HEAL']`**, which it would have done **with or without** the new
`heal_ready` conjunct — the reading lives inside the `else` branch the arm skips. ⇒ **this arm does
NOT establish that the conjunct is load-bearing.** The case the conjunct actually covers is *"the
heal RAN and left the party unready"* — where `D-HEAL` is added unconditionally and `missing` is
empty, so only `heal_ready` can catch it. **That case is still untested**, and testing it needs a
different arm (one that lets the heal run against an empty/insufficient bag). Filed rather than
claimed. *(Project rule 8: "without X the bug survives" is a CLAIM until an arm with X removed is run.)*

## ⭐ WHAT THE `NOROOMHEAL` ARM *DID* SHOW, AND IT IS WORTH MORE THAN THE GRADE

It is the **first room where the arm is not vacuous** (room 3's plan was `[]`, so arm ≡ treatment).
Skipping the heal still BEAT Drake, but the resource picture diverged sharply:

| | TREATMENT | NOROOMHEAL |
|---|---|---|
| Zigzagoon (mule) | `48/48` — never entered | **`0/48` — sent in and KO'd** |
| Full Restore | 3 → 2 (one, out of battle) | **3 → 0 — the ENTIRE stock burned IN battle** |
| Hyper Potion | 35 → 32 | 35 → 35 (**none used**) |

⇒ the between-rooms heal is not cosmetic: without it the in-battle policy spent every Full Restore
and still lost a mon. ‼ **AND THAT IN-BATTLE PATTERN — 3 Full Restores spent while 35 Hyper Potions
went untouched — is independently consistent with the recon's `#24-healfullrestorewaste` finding**,
though it is a DIFFERENT code path (in-battle item policy, not `plan_healing`), so the two must not
be conflated without a measurement that separates them.
