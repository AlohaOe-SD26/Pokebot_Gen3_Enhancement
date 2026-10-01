# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): recon angle `flags`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `step14-batch-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Arm-B flag set for design v2 step 14: verified flag facts, env blocks and open questions

This is a note, not a source of truth. Everything was checked read-only on HEAD `28db1cf0`. The worktree branch `wt/batch14` and the main checkout's `main` are both at that commit.

**Answer up front:**
- **OPENFENCE** is `POKEBOT_R20_OPENFENCE`. All three Phase 3 plans turn it ON in the treatment arm, so it is `=1` in arm B.
- **TEAM6 and HUNTFIRST are not settled.** The plans disagree on whether `POKEBOT_R20_TEAM6` and `POKEBOT_R20_HUNTFIRST` join it.
- **Every other flag on the v2 list exists, is built, graded, reviewed and merged.**
- **Q1-Q9 are in v2 §4 (lines 748-791), not §8.**

## 1. Each flag in the v2 list (VERIFIED)

Code citations are `story_mode.py` (SM) unless stated. "Merged" means the reader is in HEAD code.

| Flag | Accepted values, and when it is read | Default | Status | What it does | Requires / interacts | Fault flags (unset in both arms) |
|---|---|---|---|---|---|---|
| `POKEBOT_R24_CATCHHURT` | exactly `"1"`, no strip (SM:2439); per run | OFF | graded (`r24catchhurt-GRADED`); review KICK-BACK, then fixed in `9d24eb97` (07:36781); merged | Skips the post-gym-1 "not at full strength" refusal. C4 files a lost dex catch apart from map defeats (`[CATCH] loss-filed`) (29:171) | OVERSURVIVAL and NOFAINTBAIL require it | `R24_FAULT_LIFTEARLY`, `KINDLATE`, `TEAMLOSS` (29:172-174) |
| `POKEBOT_R24_CATCHTRAIN` | `"1"` (SM:2442); per run | OFF | graded; review KICK-BACK, then fixed in `135ecaa3` (07:36803); merged | Skips the training refusal and keeps the trainee as lead (`[CATCH] trainee` / `trainee-after`) | With OPENFENCE, a party join mid-grind adds a member the grind must also train (29:175; v1 DESIGN:605) | `R24_FAULT_ROTATE` (29:176) |
| `POKEBOT_R24_OVERSURVIVAL` | `"1"` (SM:2445); per run | OFF | graded `639b13ba`; reviewed (07:36829); merged | A wanted species is caught before survival mode applies (SM:4344) | **Run WITH CATCHHURT** (29:177; v2:8) | `R24_FAULT_SKIPSURVIVAL` (29:178) |
| `POKEBOT_R24_NOFAINTBAIL` | `"1"` (SM:2448); per run | OFF | graded; review APPROVE (07:36868); merged | A faint no longer bails a dex catch, on both paths (`[DEXCATCH-NOBAIL]`) | **Run WITH CATCHHURT** (29:179; v2:9) | `R24_FAULT_HALFBAIL` (29:180) |
| `POKEBOT_R25_CAP` | `"1"` (SM:2452); per run | OFF | graded `r25cap-GRADED`; review BLOCK, all findings taken (07:37048); merged | Ordinary species get 3 attempts per run instead of 2 | Trapinch goes from 2 to 3 trapped throw-into-reserve entries (06:8365) | no dedicated fault env (v1's `…CAP2` was never built) |
| `POKEBOT_R25_RARE` | `"1"` (SM:2453); per run | OFF | same as CAP | A rare target is exempt from the cap and the expected-throws refusal. The 10-ball reserve, runway, hunts and PC-full still apply. Adds `rare= tier= note=` fields | With CATCHHURT, faint-bail attempts are unbounded. With OVERSURVIVAL, a rare species is a catch battle on every encounter on a 3+-defeat map (06:8366-8369). On its own it changes almost nothing: the runway is the top refuser, and "never give up" comes from OPENFENCE (v2:419-421) | `R25_FAULT_RAREWRAPPER` (29:193) |
| `POKEBOT_R23_BALLRESTOCK` | `{unset, 0, observe, 1}` after strip. Any other value is OFF **with a printed error** (`stock_topoff.py:75`, `:88-95`). Read per heal (`higher_level_actions.py:526`) and at the Sootopolis visit (`stock_topoff:780`) | OFF | 9a and 9b graded and reviewed (07:37082, 07:37164); merged | Tops off the best ball sold at Rustboro after a heal, and Ultra Balls in RULING 18's Sootopolis visit. Amounts: trigger 20 / target 30 / at most ₽6,000 and half of (money − floor) | Shares one budget with the kit when both are `1`. Edits an upstream-derived heal (needs a DIVERGENCE-LOG entry on promotion) | `R23_FAULT_FLOOR`, `BALLRAISE`, `ERRANDFRAMES` (29:195-196, :213); the 9b visit also rides `RESERVE_FAULT_*` (29:137-142) |
| `POKEBOT_R27_KEYITEMS` | `"1"`, read **per call** (SM:880) | OFF | graded; review all three lenses PASS (07:36964); merged | In-battle items only against key classes. One `[KEYBATTLE]` verdict per battle; fails open | Required by KITTOPOFF. Gates DOUBLEITEMS too, because the doubles path calls `_maybe_use_item` (SM:880). The key set is a proposal pending Q3 (29:184) | `R27_FAULT_RAISE`, `ALLORDINARY` (29:185-186) |
| `POKEBOT_R26_KITTOPOFF` | same vocabulary as BALLRESTOCK, with its own error (`stock_topoff:210-216`) | OFF | 10a and 10b graded and reviewed (07:37223, 07:37268); merged | Healing kit: 4 of the best HP tier (no Max Potion); Full Heal ×2, otherwise Awakening + Ice Heal | **`=1` without `KEYITEMS=1` is a named skip** (`[KIT-BUY] why=kit-skip`, `stock_topoff:308-314`). Independent of BALLRESTOCK: the errand runs if either is set (`hla:796`; `stock_topoff:393`) | `R26_FAULT_RAWBAG` (29:198) |
| `POKEBOT_R27_DOUBLEITEMS` | **exactly** `"1"` acts and exactly `"observe"` only logs. `" 1"`, `"ON"` and `"0"` are all OFF (`double_items.py:63-71`; SM:825). Read per call | OFF | graded; reviewed (07:37446); merged 2026-09-30 | Items in non-multi trainer doubles: each battler heals itself, HP items only, with a PID guard | Added to arm B by 06:8789-8791. Orthogonal to KEYITEMS: with it, only key classes. The C1 cursor change is unconditional, so it is in both arms | `R27_FAULT_DBL_CURSOR0`, `DBL_WRONGSLOT`, `DBL_NOGUARD` (29:188-190) |
| `POKEBOT_R25_DMGAUDIT` | `"1"` after strip (`dmgaudit.py:30-31`) | OFF | graded inert: ON = OFF on all 371 lines, but **one trajectory** (dmgcalc11-GRADED:26-27, :44); reviewed (07:37313); merged | Observe-only raw reads (`[DMGAUDIT] CTL / BEFORE / AFTER`) | Set in both arms (29:199) | `R25_FAULT_DMGAUDIT_BIDE0` (29:200) |
| `POKEBOT_R25_WEAKEN` | `{unset, observe, 1}` after strip; anything else OFF (SM:2459-2460); per run | OFF | graded: W-OBS = W-OFF gameplay after the D15 re-run (weaken12-GRADED:33, :44); reviewed and merged (07:37384) | `observe` logs one `[WEAKEN-OBS]` line per in-scope catch decision | `WEAKEN_KINDS` defaults to `dex,team` (SM:2462); `WEAKEN_CALC` gates stage 2 (29:202) | `R25_FAULT_WEAKEN_{NOFLOOR, NOENCORE, CALCLEAK, ACTIVEONLY, NOPP, MASTERBALL, SPECIESID, NETGAIN, NAMEDISPATCH}` (29:204-212) |
| `POKEBOT_R20_OPENFENCE` | `"1"` (SM:2432); per run | OFF | graded `r20P2b`; review SHIP-WITH-FIXES (07:36689); merged 2026-09-28 | After gym 1, a new species met below a full party joins the party. Every later gate still applies (29:167; 06:7967-7969) | Prerequisite `#27-enroutejoin` is fixed, as unconditional code keyed on `open_fence` (06:7987). It makes RARE and CAP effective | `R20_FAULT_OPENEARLY` (29:168), `ENROUTE_FAULT_NOWALK` (29:169) |

## 2. Names that do not exist or were renamed (VERIFIED by grepping the code)

- **"OPENFENCE"** is `POKEBOT_R20_OPENFENCE`.
- **`POKEBOT_R20_BALL_RESTOCK`** (BUILDSPEC:75) was renamed to `POKEBOT_R23_BALLRESTOCK`.
- **`POKEBOT_R20_PREGYM_BAIL` and `_PREGYM_CAP`** (P2-a2, which is part of the BUILDSPEC's Phase 3 A2 arm) were never built. The bail was dropped under RULING 24 and the cap deferred (07:36765, 07:37061).
- **Fault names in the specs that the code does not have:**
  - v2 §Step 12 names `…WEAKEN_NOCRIT/NOHAZARD/LATE/SANDTYPEONLY` (v2:663-667); the built names are the ones in the table above.
  - v1 names `…RAREEARLY/RAREALL/RAREUNGATED/CAP2`, `R20_FAULT_OPENNORESERVE` and `R20_FAULT_RESTOCKLATE`.
- **v1 step 1's "throw-first"** has no code at all.

## 3. What "OPENFENCE per the Phase 3 plan" means

There are three Phase 3 plans:
- **(a) PLAN 2026-09-26, lines 69-74:** arms A = HEAD, B = P2, C = P1+P2. Here P2 is OPENFENCE and P1 is the pre-gym-1 target of 6 (TEAM6). Its pre-registered rule is "an HM rung −20 pts with z ≥ 2 ⇒ revert P1 first".
- **(b) phase1-DESIGN, lines 241-244:** A2 is "fence open, using the user's answer to question 1". That answer is YES, catches join the team (06:7681), which means OPENFENCE=1.
- **(c) BUILDSPEC, lines 136-139:** A1 (all new flags off) against A2 (B, P2-a, P2-a2, P2-b, P2-c). That is BALLRESTOCK + TEAM6 + (P2-a2, never built) + OPENFENCE + HUNTFIRST.

**VERIFIED:** all three put OPENFENCE=1 in the treatment arm.

**Not settled:** TEAM6 (and HUNTFIRST). Plan (a) isolates TEAM6 in its own arm, plan (c) bundles it in, and v2 names only OPENFENCE.

## 4. Merged flags not on the list

- **`POKEBOT_R20_TEAM6`** (29:165; SM:2428; default OFF; fault `R20_FAULT_TARGETLOOP`).
  - For: the user's observation 1, "stops catching once team reaches 4 … around Rustboro gym area" (06:7638-7641), is the pre-gym-1 target. OPENFENCE only acts after gym 1, so arm B without TEAM6 leaves that symptom unchanged (INFERRED).
  - Against: `#24-partycap` measured −36 points for exactly this change (29:165). Bundling it makes a finish-rate loss impossible to attribute (v2:707).
- **`POKEBOT_R20_HUNTFIRST`** (29:170; SM:2435; no fault env, 06:8003-8009).
  - It acts only before gym 1. It matters "rarely at the default target of 4; more with TEAM6" (r20P2c-GRADED:41-42).
  - INFERRED: put it in or leave it out together with TEAM6.
- **`POKEBOT_R25_WEAKEN_CALC`:** pin OFF unless the user rules otherwise (Q-B below).
- **Hold at production defaults in both arms:**
  - `POKEBOT_MAINTAIN` defaults to `"1"` (SM:3415). `Run-Maintain-AB-Batch.bat` sets it to 0 for its OFF arm, so a leaked 0 is a real risk; pin `1` in both arms.
  - `POKEBOT_BOX_OVERFLOW_CATCH` defaults to `"1"` (SM:4304).
- **Leave unset in both arms:**
  - `POKEBOT_HEAL_AT_FRACTION`, `POKEBOT_FAINT_GIVEUP_LIMIT` and `POKEBOT_WEAKEN_KINDS` (defaults apply).
  - `POKEBOT_RNG_DECORRELATION_FRAMES`, which must never be 0.
  - The §A harmful flags: `PC_ROTATION`, `AREA_ITEM_GATE`, `LEAD_DEMOTE_WONDER_GUARD`, `HUNT_ANYGROUND`.
  - `KI93_CENSUS`, `KI96_CENSUS`, `RECORD_TURNS`.
  - Every `*_FAULT_*` flag.
  - The registry §B switches that have no "FAULT" in their names: `HMTEACH_POSTLEARN_A`, `TEACHWINDOW_A`, `LEADCANTBATTLE_A`, `BOXCOUNTER_TYPEONLY_A`, and every `*_ARM` (29:284-292). A filter on "_FAULT" alone misses these.

## 5. Env blocks (cmd form, as in the precedent `.bat` with `setlocal`)

Use `set "VAR=value"` with the quotes. Most readers compare `== "1"` without stripping, so a trailing space from `set X=1 & …` silently reads as OFF. Only BALLRESTOCK and KITTOPOFF print an error on a bad value. Every reader treats `0` as OFF without error, so arm A sets each flag to 0 explicitly; that protects against shell leaks.

**Arm A:**
```
set "POKEBOT_R24_CATCHHURT=0"
set "POKEBOT_R24_CATCHTRAIN=0"
set "POKEBOT_R24_OVERSURVIVAL=0"
set "POKEBOT_R24_NOFAINTBAIL=0"
set "POKEBOT_R25_CAP=0"
set "POKEBOT_R25_RARE=0"
set "POKEBOT_R23_BALLRESTOCK=0"
set "POKEBOT_R27_KEYITEMS=0"
set "POKEBOT_R26_KITTOPOFF=0"
set "POKEBOT_R27_DOUBLEITEMS=0"
set "POKEBOT_R20_OPENFENCE=0"
set "POKEBOT_R20_TEAM6=0"
set "POKEBOT_R20_HUNTFIRST=0"
set "POKEBOT_R25_WEAKEN_CALC=0"
set "POKEBOT_R25_DMGAUDIT=1"
set "POKEBOT_R25_WEAKEN=observe"
set "POKEBOT_MAINTAIN=1"
set "POKEBOT_BOX_OVERFLOW_CATCH=1"
```

**Arm B:** the same lines, except these 12 are `=1`:
- `CATCHHURT`, `CATCHTRAIN`, `OVERSURVIVAL`, `NOFAINTBAIL`
- `R25_CAP`, `R25_RARE`
- `R23_BALLRESTOCK`
- `R27_KEYITEMS`, `R26_KITTOPOFF`, `R27_DOUBLEITEMS`
- `R20_OPENFENCE`

`TEAM6` and `HUNTFIRST` stay `0` under v2's literal list, pending Q-A. `WEAKEN_CALC` stays `0` pending Q-B. `DMGAUDIT=1`, `WEAKEN=observe`, `MAINTAIN=1` and `BOX_OVERFLOW_CATCH=1` are the same as arm A.

**Pre-flight:** abort if any `POKEBOT_*` variable containing `FAULT`, or any §B `*_A` / `*_ARM` switch, is set.

**How a lane gets these:** `endless_x4.py:173` and `x4_headless.py:629` both copy `os.environ`, so every lane inherits the launching shell. Nothing prints the flag set at startup (I grepped for one), so arm identity has to be proven from the logs:
- **Both arms must show** `[DMGAUDIT] … CTL` at battle starts, and `[WEAKEN-OBS]` on dex/team catches.
- **Arm A must have zero of:** `[KEYBATTLE]`, `[KIT-BUY]`, `[BALLS-BUY] why=topoff*`, `[DBLITEM`, the `rare=` field, `[DEXCATCH-NOBAIL]`, `[CATCH] trainee`, `[CATCH] loss-filed`.
- **Arm B must show** `[KEYBATTLE]` in trainer battles and `rare=` on `[DEXFENCE]` lines.

Each of these strings is in the code; that each is printed only with its flag on rests on the registry text (VERIFIED in the registry, not traced line by line).

## 6. Open questions

- **Q-A:** TEAM6 and HUNTFIRST in arm B (section 4)? Plans (a) and (c) disagree.
- **Q-B:** should both arms run `observe` plus `POKEBOT_R25_WEAKEN_CALC=1`?
  - Why it matters: without CALC, `observe` measures only stage 1. That "WILL ALMOST NEVER ACT" (29:201), so the "weaken-frequency data" v2:696 expects would be close to empty.
  - For: W-OBSCALC was graded with the same gameplay as W-OBS (weaken12-GRADED:34), and the registry calls observe+CALC "sanctioned now" (29:202).
  - Against: weaken12-DESIGN:76 says stage 2 "stays OFF in every acting arm and batch".
- **Q-C:** `#27-dmgcalcfix` is NOT STARTED (03:84). So the DMGAUDIT data measures the unfixed calculator, and clearing stage 2 then needs either a second batch or an ACCEPT_MARGIN ruling (dmgcalc11-DESIGN:244-246, :271).
- **Q-D:** per-lane flags or two batches (06:8805-8810). Per-lane flags need a mechanism that is not built yet.
- **v2 §4 questions that change arm B's behaviour if answered first:**
  - Q1 (BALLRESTOCK amounts) and Q2 (which ball to throw or buy).
  - Q3 (the key class set). It changes which battles use items under KEYITEMS and DOUBLEITEMS, the kit's value, and the per-group grading partition.
  - Q5 and Q6 (the rare set).
  - Q8 (throw past the reserve for a rare species). "Throw past" is not built, so answering yes needs code first.
  - Q7 and Q9 are not built, so they change nothing; Q4 is withdrawn.
  - The kit amounts (v2 §3) are also still proposals.
  - None of these has an answer in 06 after 8057 (grep).
- **Q-E (optional):** run `observe` for BALLRESTOCK, KITTOPOFF and DOUBLEITEMS in arm A, to get counterfactual frequencies? It departs from "everything OFF", and each observe mode was shown inert on a single trajectory (ballrestock-GRADED:19-20; doubleitems13-GRADED:91).

## 7. INFERRED, not verified

- Whether double-battle item use also prints `[ITEM] using` was not traced. Step 14's "0 item uses in non-key battles" check should count `[DBLITEM] use` lines too.
- OVERSURVIVAL has no flag-only log line (grep shows only SM:4344/4396).
- batch0927 ran `d21c0c3c` (batch0927-FINAL:59), and many always-on changes have merged since. Arm A, not that baseline, is the true control.
