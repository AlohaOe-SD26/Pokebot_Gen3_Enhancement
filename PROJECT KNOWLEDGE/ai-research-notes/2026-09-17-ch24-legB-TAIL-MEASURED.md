# §Ch24 LEG B — THE ENDGAME TAIL, MEASURED END TO END (2026-09-17, late)

> ⭐⭐⭐ **WALLACE IS BEATEN AND THE GAME IS CLEARED.** `--driver ch24tailprobe` from the pinned
> `post_hall4_door.ss1` ran from `HALL4 (5,3)` through the Champion, the Hall of Fame, the credits and
> a `SoftReset(RESET_ALL)`, and came back **controllable in Brendan's bedroom with
> `IS_CHAMPION=True` and `SYS_GAME_CLEAR=True` in BOTH RAM and FLASH.**
> Evidence: `tools/story-dev/evidence/2026-09-17-ch24tailprobe-FULL-TAIL.stdout.txt`.

⛔ **THIS IS A MEASUREMENT, NOT A CHAPTER.** The probe asserts nothing and grades no bot behaviour;
its `ACCEPTANCE` line is instrument health only. **Segment 24 is still NOT wired.** What this buys is
that every number in `2026-09-17-ch24-legB-BUILD-SPEC.md` is now observed instead of arithmetic.

## THE FRAME TABLE — the point of the probe

| stage | frames | Δ |
|---|---|---|
| step onto `(5,2)` → `CHAMPIONS_ROOM` (LOADMAP→DOCHANGEMAP→LOADMAP2→OVERWORLD) | 8495074 → 8495117 | **43** |
| scripted approach + the intro speech | 8495117 → 8496765 | **1,648** |
| ⚔ **THE WALLACE FIGHT** (`CB2_HANDLESTARTBATTLE`) | 8496840 → 8526799 | **29,959** |
| post-battle cutscene (rival → Birch → dex rating → Wallace) | 8527682 → 8530363 | **2,681** |
| warp to the Hall of Fame MAP | 8530363 → 8530372 | **9** |
| Hall of Fame MAP cutscene → `special GameClear` | 8530372 → 8531840 | **1,468** |
| `CB2_DOHALLOFFAMESCREEN` → `CB2_HALLOFFAME` | 8531840 → 8531870 | **30** |
| ⚠ Hall of Fame SCREEN (contains the full save-slot write) | 8531870 → 8534162 | **2,292** |
| ⚠ **CREDITS** (`CB2_CREDITS`) | 8534168 → 8544521 | **10,353** |
| reboot: copyright → intro → title → `CB2_MAINMENU` | 8544533 → 8544937 | **404** |
| ⭐ `CB2_MAINMENU` → **`CB2_CONTINUESAVEDGAME`** → LOADMAP → `CB2_OVERWORLD` | 8544937 → 8544947 | **10** |
| **TOTAL, door step → controllable again** | 8495074 → 8544947 | **49,873** |

‼ **THE NAMED ROWS SUM TO 48,897, NOT 49,873** — a Tier 1 reviewer added them up. The missing **976** frames are four small UNLABELLED boundary gaps (~75 / ~883 / ~6 / ~12) around the battle-start and battle-end markers and the credits/reboot edges, where a TRANSITION and a latch straddle each other. ⭐ The TOTAL and every figure used for budgeting (fight 29,959, credits 10,353, tail-minus-fight 19,914) are each independently correct against the evidence — this is a presentation gap, not a wrong number. It is written down rather than quietly reconciled, because a table whose rows do not add up invites a future reader to “fix” the total.

⇒ **~50 s of emulation.** Excluding the fight, the tail itself is **19,914 frames**. The spec
estimated ~12,950 for that portion — **~54 % low**, mostly in the credits (10,353 actual vs ~8,940)
and the post-battle cutscene. ⚠ Budget a leg-B driver at **`--frames ≥ 120000`**, not 30,000.

## THE QUESTIONS THE SPEC ASKED, NOW ANSWERED

* ⭐⭐ **Q7 — does flash written BY THE GAME survive `_core.reset()`? YES.** This was *the single
  unmeasured load-bearing fact in the whole spec.* The profile started with **`<no save data>`**
  (`start_flash_game_clear='<no save data>'`), the Hall of Fame wrote the save slot mid-run, and after
  the reboot the menu went **`CB2_MAINMENU` → `CB2_CONTINUESAVEDGAME`** — *not* `NAMING_SCREEN`.
  End state: `end_flash_game_clear=True`. ⇒ **the CONTINUE path works, and trap T17 does not bite on
  this path** because the game itself populates flash before the reboot.
* ⭐ **Q2 — does the tail exceed the 20,000-frame no-progress detector? NO, but it is closer than
  comfortable.** The longest in-tail constant-signature stretch reached the **x8000** rung
  (`sig=('Ch24TailProbeMode.run','UNKNOWN','','DialogueNotActive',…)`) and never reached 20,000.
  ‼ The `HANG CONFIRMED` in the log is at **f69937, AFTER the ACCEPTANCE line, with `ctrl='<none>'`** —
  the documented post-acceptance artifact every probe produces, not a hang.
  ⇒ **A leg-B driver does NOT need to defeat the detector**, and the spec's suggested
  sub-generator-cycling trick is unnecessary machinery. *(Measured, not assumed — and this is why the
  probe deliberately did not implement it.)*
* **Q4 — the CB2 symbol order**, now observed exactly:
  `CB2_OVERWORLD → LOADMAP → DOCHANGEMAP → LOADMAP2 → OVERWORLD → OVERWORLDBASIC → INITBATTLE →
  HANDLESTARTBATTLE → OVERWORLD → LOADMAP → … → OVERWORLD → DOHALLOFFAMESCREEN → HALLOFFAME →
  STARTCREDITSSEQUENCE → CREDITS → '' → INITCOPYRIGHTSCREENAFTERBOOTUP → MAINCB2_INTRO →
  MAINCB2_ENDINTRO → INITTITLESCREEN → MAINCB2 → GOTOMAINMENU → INITMAINMENU → MAINMENU →
  CONTINUESAVEDGAME → LOADMAP → DOCHANGEMAP → LOADMAP2 → OVERWORLD`.
  ⚠ Note the **empty-string symbol `''`** between CREDITS and the reboot — a reader that assumes a
  non-empty symbol will trip there.
* **Q8 — where the avatar actually rests:** `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` — map `(1,1)`,
  exactly as the spec read from the decomp. ⛔ Still derive it from the saved `continueGameWarp`
  rather than hardcoding: this run was a male save.
* **Q3 — does `_in_battle` clear after Wallace? YES.** `on_battle_ended` latched
  `outcome=<BattleOutcome.Won: 1>` at f8526799 and the generator resumed.

## ‼ THE PROBE'S OWN FIRST RUN WAS WRONG, AND THE BUG IS THE LESSON

v1's stop condition was `OVERWORLD ∧ controllable ∧ battle_ended`. It fired on the **first post-battle
overworld frame** — `end_where=((16,4),(6,6))`, still the **Champion's room**, `IS_CHAMPION=False` —
so the probe stopped pressing and measured **none** of the tail it exists to measure.
⛔ **`player_avatar_is_controllable()` READS TRUE UNDER `lockall`.** The `story-drive` skill says so in
as many words (*"a cutscene ends AFTER its var … `player_avatar_is_controllable()` reads True under
`lockall`"*), and I wrote the condition anyway.
✅ v2 requires three conjuncts, and the third is the one that matters: **the run must have LEFT the
Champion's room** (plus the script context idle). `IS_CHAMPION` was deliberately NOT used as the stop
signal, because if flash ever carried no save the reboot would land on NEW GAME and the flag would
read False forever. Both runs are committed — `...-v1-STOPPED-EARLY.stdout.txt` is kept because the
mistake is more instructive than the fix.

## WHAT THIS DOES **NOT** ESTABLISH

* ⛔ **It is not a chapter and not a leg.** Segment 24 is still unwired; this is a probe.
* ⛔ **One trajectory.** Wallace was beaten **once**, from a fully-healed party with 1 Revive. Nothing
  here is a win *rate*, and the fight's 29,959 frames are one sample.
* ⛔ **The press count is not a budget.** `presses=19056` is duty-cycle ticks the probe issued, not
  prompts the game consumed — the same distinction that cost a wrong reading in `#24-e4postbattlestall`.
* ⚠ **The gauntlet was driven as a CHAIN OF FIXTURES, not one continuous run**: every link
  (`post_ch24_atdoor_L75 → sidney → phoebe → glacia → drake → hall4_door → cleared`) is individually
  driven and pinned, but no single run has gone door-to-credits.
* ⚠ The profile's `current_save.sav` now contains a **cleared game**. That is expected (the Hall of
  Fame force-saves) and harmless — every fixture is a `.ss1` — but it means `get_save_data()` on this
  profile will read a champion save from now on.
