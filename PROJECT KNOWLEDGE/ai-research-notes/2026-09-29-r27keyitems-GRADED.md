# 2026-09-29 — USER RULING 27, design v2 step 6 (KB) GRADED: with `POKEBOT_R27_KEYITEMS`, healing items are used only against key trainer classes; OFF is unchanged; the gate fails open

> Predictions: `2026-09-29-r27keyitems-PREDICTIONS.md` (`ccf218d1`, before the code). Code: `e1ddc4e7`. Evidence:
> `tools/story-dev/evidence/2026-09-29-r27keyitems-*.txt`; `-GRADER.txt` compares each arm with its M0 over every
> `[BATTLE]` line plus the identity, money and map lines. Every M0 and every OFF control was run TWICE (KI-112); every
> pair is identical.

## RESULTS — every prediction held

| Arm | Reading | Verdict |
|---|---|---|
| **A-OFF** ×2 | 205 of 205 lines identical to the Live A M0 (both runs); 0 `[KEYBATTLE]` lines; the Hyper Potion at f3196418 | ✅ OFF unchanged |
| **A-ON** ×2 (identical to each other) | identical to M0 before the Cooltrainer 767 battle. Then `f3196418 [KEYBATTLE] opp=767 class=0x05 key=False allow=False reason=not_a_key_class`, and the same turn becomes **`[TURN 0] Mightyena L43 30/127 [Paralysis] -> UseMove:Take Down`** where M0 used the Hyper Potion. One `[KEYBATTLE]` line per single battle (651, 300, 11, 767 and grunt 717, all `allow=False`); none on the doubles | ✅ the narrowing works |
| **A-RAISE** | 205 of 205 identical to M0 (the item still fires at f3196418); every `[KEYBATTLE]` line reads `allow=True reason=FAIL_OPEN(RuntimeError)` | ✅ fails open |
| **B1-ON** | 73 of 73 identical to the B1 M0. `f4320217 [KEYBATTLE] opp=261 class=0x1F key=True allow=True reason=key_class`, then the Full Heal and three Full Restores against Sidney | ✅ a key battle keeps its items |
| **B1-ORD** | `opp=261 class=0x05 key=False allow=False`. At f4320217 the frozen Sceptile tries `UseMove:Leaf Blade` instead of the Full Heal, and NO item is used against Sidney | ✅ the allowance is load-bearing |
| **B2-ON** | 162 of 162 identical to the B2 M0. Grunts 717, 718, 724, 731 and 726 read `allow=False` (they used no item anyway); Tabitha (0x31) and Maxie (0x35) read `allow=True`; the Hyper Potion against Maxie at f3282442 | ✅ |
| **B2-ORD** | identical up to Maxie. At f3282442 `UseMove:Slam` instead of the Hyper Potion | ✅ |

**Stale spec reading, re-measured first.** The spec's Live A discriminator ("f3191012, 39/127, against Marcel") no
longer occurs: Marcel's battle uses no item. The M0 pair found the real one, the Hyper Potion against Cooltrainer 767
at f3196418. It was pre-registered before the code.

## FOUND ALONG THE WAY

- **Class 0x32 is broader than Q3's wording.** The ROM calls it "PkMn TRAINER", and it also covers Steven's post-game
  battle (804) and Red/Leaf. The user was not shown this; it is added to the report.
- **Two-opponent battles never reach the item code.** They are always DOUBLE, and doubles take
  `decide_turn_in_double_battle`. So the gate is inert on them, as it is on Tate & Liza and every leader rematch
  (step 13). The verdict takes a list of sides for that step.
- The harness drivers `Ch24ProbeMode` and `MagmaHideoutMode` now log the step-5 `[TRAINER]` lines. That is how B1 and
  B2 could name Sidney, Tabitha and Maxie.

## WHAT THIS DOES NOT SHOW

- Whether key battles are won more often, or whether fewer items in ordinary battles cost whiteouts. That is the
  batch (step 14).
- Doubles (step 13), and Juan (inert until step 10's kit puts items above RULING 18's basket).
- The final key-class set: Q3.
