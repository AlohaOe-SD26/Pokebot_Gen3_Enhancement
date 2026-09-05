# KI-90 — the full evidence chain, and the root cause I got wrong first (2026-09-05)

> ⚠ **RESEARCH NOTE, NOT TRUTH** — see `00-READ-THIS-FIRST.md`. Produced by a 10-agent adversarial
> workflow (5 angles, each refuted by an independent verifier). ⛔ **BUT the load-bearing halves were
> then re-verified BY ME, by reading the code and the decomp directly**, and those are marked ⭐
> VERIFIED below. Where this note and `05-KNOWN-ISSUES.md` disagree, the KI wins.
>
> ⭐ **THIS NOTE'S HEADLINE IS THAT IT REFUTED MY OWN COMMITTED ROOT CAUSE.** That is the strongest
> argument in this project's files for adversarial fan-out: a second agent asked the same question
> would have produced a second guess; agents asked to REFUTE produced a correction.

## 1. The verified chain

⭐ **VERIFIED (I read it):** `modules/battle_state.py:396-402` —
```python
@property
def left_battler(self) -> "BattlePokemon | None":
    if self._side == 0 and self._absent_battler_flags & 0b0001 == 0:
        return self._battle_state.battling_pokemon[0]
    elif self._side == 1 and self._absent_battler_flags & 0b0010 == 0:
        return self._battle_state.battling_pokemon[1]
    else:
        return None
```
⇒ for the opponent side, `left_battler is None` **iff** bit 1 of `gAbsentBattlerFlags` is set. There
is no other path to `None` (a short list would raise `IndexError`).

⭐ **VERIFIED (I read it):** `modules/battle_state.py:245` stores `_absent_battler_flags` as a plain
`int`, sourced at `:821` from `read_symbol("gAbsentBattlerFlags", size=0x01)[0]`. It is a **frozen
byte snapshot**, taken at `battle_action_selection.py:23` / `:247` — both **before**
`battle_action_use_move`'s A-press loop. ⇒ **nothing during those presses can change it.**

⭐ **VERIFIED (I read the decomp):** `src/battle_util.c:2271-2272` —
```c
bool8 HasNoMonsToSwitch(u8 battler, u8 partyIdBattlerOn1, u8 partyIdBattlerOn2)
{
    ...
    if (!(gBattleTypeFlags & BATTLE_TYPE_DOUBLE))
        return FALSE;
```
Every writer of `gAbsentBattlerFlags` outside link battles is gated on this. ⇒ **in a SINGLE battle
the byte is identically 0 for the entire battle**, so **the raise itself proves a DOUBLE battle.**

⭐ **VERIFIED (I read it):** `modules/main.py:151-158` — BOTH `except BotModeError` and the bare
`except Exception` call `context.set_manual_mode()`.

**Reported by agents, consistent with the above, NOT independently re-verified by me:**
* a fainted battler's slot is not zeroed — `FaintClearSetData` (`src/battle_main.c:3264`) resets
  status/stat-stage state but never species/hp/level, so the slot is never "empty" mid-faint;
* `HandleInputChooseMove` already defaults the cursor to OPPONENT_RIGHT when the left is absent
  (`src/battle_controller_player.c:535-536`) — i.e. **the game handles the case our code raises on**;
* Victory Road produces doubles from face-to-face `trainerbattle_single` pairs
  (`gNoOfApproachingTrainers == 2`), with no double-battle trainer flag needed;
* `BattleScript_FaintTarget` cannot be concurrent with our action selection, because our loop only
  runs while the main callback is `HandleTurnActionSelectionState`. ⇒ the two faint messages in the
  log BRACKET the raise rather than causing it.

## 2. The forensics

⚠ **AGENT-REPORTED, NOT INDEPENDENTLY RE-VERIFIED BY ME** — this whole section, tagged explicitly because the note's own two-tier convention demands it and a Tier 1 reviewer noticed it was the one untagged block. It is consistent with the log I read, but I did not re-derive the frame counts or confirm it was the run's only double battle.

The failing fight was the **only double battle in the entire run** — a Victory Road 1F trainer pair
entered with Wailord and Sceptile already fainted. The bot's own turn telemetry recorded the raise
condition (`vs ?`, i.e. `opponent.left_battler is None`) **29 frames before** the exception, on a turn
where our last living Pokémon, Mightyena, was told to attack an opponent slot the game had marked
absent. ⇒ the condition was observable ahead of time, which is what makes a deterministic repro
possible.

## 3. ⛔ What I got wrong, and what it would have cost

**My committed KI-90 said:** *"The order of operations is the bug — it presses A through
`HandleInputChooseMove` first and only then reads the target, so a faint during those presses turns a
normal turn into a fatal raise."*

**That is causally impossible** (the snapshot is frozen before the presses), which means:
* the fix it implied — **reorder the check before the A-presses — would have changed nothing**, and
  would have been "verified" by a run that simply did not hit a double battle;
* the repro it implied — hunt a faint-during-move-selection timing window — **does not exist**, and
  could have been chased indefinitely.

**And the blast-radius reason was also wrong.** I wrote that the problem was the exception TYPE (a
bare `RuntimeError` where recoveries catch `BotModeError`). In fact `handle_battle` is only ever
reached from `BattleListener`, a **sibling** generator on the controller stack, so from that position
**every** exception — `BotModeError` included — ends at `main.py` and sets Manual.
⇒ ⭐ **A RECOVERY LOOP ONLY CATCHES WHAT REACHES ITS OWN STACK. Changing the exception type would not
have made this recoverable** — which is precisely the fix a reader of my old text would have tried.

## 4. ⛔ Not ours, and the agent claim that had to be refuted

One angle concluded *"THIS IS OUR CODE, NOT UPSTREAM — our `_fight_on` KI-52 fork emits the
left-targeted action."* **Its own verifier refuted the causal half, and I confirmed both dates:** the
identical `RuntimeError` appears in
`tools/story-dev/livetest-runs/archive/20260722-204645/run01/run.log:18254`, dated **2026-07-22** —
three weeks BEFORE `_fight_on` landed (`72e938d2`, 2026-08-11 11:09). Our fork may raise exposure; it
did not create the defect.
⇒ ⭐ **the same rule that governs Gemini governs Claude agents: grade their ENUMERATION highly and
their CAUSAL CONCLUSIONS not at all.**

## 5. What is still NOT established
* **How often it fires.** One occurrence in 2026-09-05 plus one in 2026-07-22 is an existence proof
  across seven weeks, not a rate. This is a CORRECTNESS question, so the instrument is a repro.
* Whether other double-battle trainer pairs on the §Ch23/§Ch24 route reach the same state.
* Whether the candidate fix (fall back to the RIGHT opponent when the left is absent, as
  `HandleInputChooseMove` does) is safe for every caller of `battle_action_use_move` — **UNVERIFIED**,
  and the file is shared hot-path code. ⚠ *(This read "the `KI-83`/`KI-88`/`KI-89` ruling applies" — that ruling **does not exist**; see `06-DECISIONS-LOG.md` 2026-09-05.)* Build the repro FIRST (done — gate #38), then decide the fix on
  EVIDENCE: a failing repro, an argument that the change is ADDITIVE to states that work
  today, and the full suite. ⛔ **NOT "route around rather than casually patch"** — that was
  the retracted ruling's own conclusion, and it stood here as the sentence's LAST WORDS for one
  revision after the citation above was corrected. ‼ Caught by Tier 1: **retracting a claim
  means retracting what it CONCLUDED, not just the sentence that cited it** — the headline
  carries the caveat, and a reader reaches the END of the sentence.

📌 Related: `05-KNOWN-ISSUES.md` KI-90 (the live entry), `03-PUNCH-LIST.md` `#24-ch23chain`.
