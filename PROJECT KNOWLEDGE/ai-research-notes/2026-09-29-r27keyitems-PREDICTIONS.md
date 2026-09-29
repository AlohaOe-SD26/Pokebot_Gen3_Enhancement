# 2026-09-29 — USER RULING 27, design v2 step 6 (KB: healing items only in KEY battles): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the code is committed and before any graded drive. Branch `wt/r27keyitems`, cut from `main` `7dcd69fd`.
> Spec: `ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` step 6 (a NOTE). Ruling: `06`, USER RULING 27 (*"use
> healing items during battles (gym leaders, story "bosses" and elite 4 only)"*). A code audit and the M0 measurements
> below were made first. The spec's line numbers and its Live A reading were STALE, and are re-measured here.

## THE CHANGE (planned)

- **`trainer_identity.KEY_TRAINER_CLASSES`** = LEADER 0x20, ELITE_FOUR 0x1F, CHAMPION 0x26, RIVAL 0x32, MAGMA_LEADER
  0x35, AQUA_LEADER 0x0D, MAGMA_ADMIN 0x31, AQUA_ADMIN 0x0B. ⚠ A PROPOSAL pending the user's Q3. The ROM scan (all 854
  trainers) puts every configured and named boss in it. **0x32 also covers Steven's post-game battle (804) and
  Red/Leaf, which Q3 did not name.**
- **PURE `key_battle_verdict(flag_on, sides)`** over `[(id, cls), …]`. It FAILS OPEN: it refuses only when the flag
  is on and every side was read and none is key.
  - A list, because a two-opponent battle has two sides. Today those are always DOUBLE and never reach
    `_maybe_use_item` (doubles take `decide_turn_in_double_battle`), so the list form is for step 13.
- **`StoryItemBattleStrategy._maybe_use_item`:** right after the Trainer-battle return,
  `if _os.environ.get("POKEBOT_R27_KEYITEMS") == "1" and not _r27_key_gate(self, battle_state): return None`.
  - The flag test comes FIRST, so OFF does zero reads.
  - It is an early return, so gate #59's pinned indentation is untouched.
  - It is INSIDE the method, so the harness drivers that build the strategy themselves are gated too.
- **Module-level `_r27_key_gate`:**
  - one verdict per battle, cached on the instance;
  - one `[KEYBATTLE] opp= class= key= allow= reason=` line;
  - it never raises, and fails OPEN (`reason=FAIL_OPEN(...)`).
  - Fault arms: `POKEBOT_R27_FAULT_RAISE` (the reader raises: the item must still fire) and
    `POKEBOT_R27_FAULT_ALLORDINARY` (every class reads 0x05).
- **Harness:** `Ch24ProbeMode` and `MagmaHideoutMode` call the step-5 `_t1_start/_t1_end`, so their battles name the
  trainer. This is log-only.
- **NEW gate `repro_key_battle_items.py`:**
  - V1, the pure rows;
  - V2, the ROM boss reconciliation by trainer ID;
  - I1-I4 on the REAL `_maybe_use_item` with gate #60's fakes;
  - A1 (placement by AST) and A2 (the registry);
  - F1-F5 with exact red sets.

## THE M0 MEASUREMENTS (flag OFF; each run TWICE per KI-112 — every pair IDENTICAL)

Evidence: `tools/story-dev/evidence/2026-09-29-r27keyitems-M0-{liveA,liveB1,liveB2}.txt`.

**Live A — `post_mtpyre.ss1` (`80602159`), `storyresume`, 90,000 frames, seed 1 (`main` `7dcd69fd`), 205/205 lines
identical.**
- Single trainer battles before the discriminator used NO item: Ninja Boy 651, Pokéfan 300, Cooltrainer 11 (Marcel).
  The two-opponent doubles never reach the item code.
- **The discriminator:** `f3195397 [TRAINER] start opp=767 class=0x05(COOLTRAINER)`, then **`f3196418 [BATTLE]
  [ITEM] using Hyper Potion on Mightyena 30/127`**. 30/127 = 0.24 ≤ 0.35, against a NON-key class.
- ⚠ The spec's reading (`f3191012 … 39/127` against Marcel, id 11) is STALE: Marcel's battle now uses no item.

**Live B1 — `post_league_shop.ss1` (`1564948368f6`), `--driver ch24probe`, `POKEBOT_CH24_STAGE_FREEZE=1`, 120,000
frames, seed 1, 73/73 lines identical.**
- `f4319292 [TRAINER] start opp=261 class=0x1F(ELITE_FOUR)` (Sidney).
- **The first key-class item decision: `f4320217 … using Full Heal on Sceptile 147/147`** (the staged Freeze).
- Then Full Restores at f4325721, f4327762 and f4333720 (uses 2-4).

**Live B2 — `magma_door_losing.ss1` (`76ef84a3`), `--driver magmahideout`, 120,000 frames, seed 1, 162/162 lines
identical.**
- Grunts 717, 718, 724, 731 and 726 (TEAM_MAGMA 0x09), the grunt pair 727+728 (a double) and Tabitha 732 (0x31) all
  pass with NO item.
- `f3276879 [TRAINER] start opp=601 class=0x35(MAGMA_LEADER)` (Maxie).
- **The first key-class item decision: `f3282442 … using Hyper Potion on Sceptile 30/122`.**

## THE ARMS AND THEIR PREDICTED READINGS (on the committed code; same commands and seed)

| Arm | Env | Predicted |
|---|---|---|
| **A-OFF** ×2 | flag unset | both replay the Live A M0 exactly (205 tracked lines), including the Hyper Potion at f3196418; 0 `[KEYBATTLE]` lines |
| **A-ON** ×2 | `POKEBOT_R27_KEYITEMS=1` | identical to M0 before the Cooltrainer 767 battle. In it: `[KEYBATTLE] opp=767 class=0x05 key=False allow=False reason=not_a_key_class`, and **NO `[ITEM] using` in that battle**. Its first `[TURN]` decision after f3195397 is a move, not an item. Earlier single battles (651, 300, 11) log `key=False allow=False` too, but change nothing (OFF used no item there). The trajectory after the refused heal is RECORDED, not predicted |
| **A-RAISE** | flag + `POKEBOT_R27_FAULT_RAISE=1` | identical to A-OFF (the item still fires at f3196418), plus `[KEYBATTLE] … allow=True reason=FAIL_OPEN(RuntimeError)` lines |
| **B1-ON** | flag | identical to B1 M0: `[KEYBATTLE] opp=261 class=0x1F key=True allow=True reason=key_class`, then the Full Heal at f4320217 and the three Full Restores |
| **B1-ORD** | flag + `POKEBOT_R27_FAULT_ALLORDINARY=1` | `[KEYBATTLE] opp=261 class=0x05 key=False allow=False`, and **NO item in the Sidney battle** |
| **B2-ON** | flag | identical to B2 M0 in every `[BATTLE]` line: grunts and Tabitha log `allow=False` (grunts) or `allow=True` (Tabitha 0x31), but no item was used there anyway. At Maxie: `key=True allow=True`, and the Hyper Potion at f3282442 |
| **B2-ORD** | flag + `ALLORDINARY` | identical up to Maxie; **NO Hyper Potion at f3282442** |

## FALSIFIERS

- A-OFF differs from the M0 pair: OFF is not byte-identical.
- A-ON uses an item in the Cooltrainer 767 battle, or logs `allow=True` for class 0x05.
- B1-ON or B2-ON refuses an item at a key class (Sidney, Maxie), or differs from its M0 before the graded decision.
- B1-ORD or B2-ORD uses an item at the graded decision: the allowance is not what lets it through.
- A-RAISE refuses the item: the gate fails CLOSED.
- More than one `[KEYBATTLE]` line per battle, or a traceback.

## WHAT THIS DOES NOT SHOW

- Doubles, including every gym-leader rematch and Tate & Liza: the gate is inert there (step 13).
- Juan: RULING 18's reserve withholds the basket, so the gate is inert until step 10's kit.
- Whether key battles are won more often, or whether fewer items elsewhere costs whiteouts. That is the batch
  (step 14).
- Q3's final class set (Steven, Red/Leaf).
