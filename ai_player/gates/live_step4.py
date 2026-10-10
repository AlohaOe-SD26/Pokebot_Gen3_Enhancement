"""LIVE PROOF of AI-player build step 4: the AI's OWN BATTLES (HUMAN-PLAY-DESIGN pillar 3). Test side.

    py -3.12 ai_player/gates/live_step4.py [--arms WILD,CATCH,...] [--evidence-tag step4]
    exit 0 = every arm PASS and no leftover emulator process

Every launcher arm runs the REAL package through the real launcher (`py -3.12 -m ai_player run`: the purity gate first,
the instrument, the verdict file), brain `battle` (`mode.py` HandsBrain._battles: the decider `brain/battle.py`, the skill
`skills/battle.py`), and is graded three ways, every check quoting both values:
  PURITY  CLEAN, every breach counter 0, `ai_presses` == 2 x the pad's presses, the pad's frames == `real_frames`,
          `ai_bot_calls` 0 (the bot's battle code never ran), the run ended by itself;
  HANDS   every press has its gate; every A is a WAIT, a MENU confirm (that menu, taking input, on its look) or a TALK;
          no stretch standing still under the catch-all reason;
  THE GAME by a SECOND PATH from the state the run left (`hands_harness.py truth`: the framework's party decoder by PID
          with each Pokemon's experience, level, moves and OT id; the PC boxes' PIDs and OT ids; `gBattleOutcome`; the
          trainers' DEFEATED flags and the story flags in save block 1; the game's own battle counters), never the AI's
          eyes; the state asserted to be THIS run's.

THE ARMS (fixtures: `gates/make_step4_fixtures.py`, every one made by button presses; md5s pinned in `FIXTURES`)
  WILD       `route101_south.ss1` (Route 101, Mudkip L8 19/28, 5 Poke Balls, only Mudkip owned), Story, 4 battles: it roams the
             grass and fights what comes (a species it has not caught may be caught: Story wants one 60 % of the time, a
             seeded draw); CLAIM: at least one wild battle WON by fighting, and the Mudkip's experience (by PID) rose.
  CATCH      the same start, Catcher (it wants every species it has not caught), 1 battle; CLAIM: the battle ends CAUGHT
             (`gBattleOutcome` 7), a NEW PID is in the party or a box with the PLAYER's visible OT id, the balls in the bag
             fell by exactly the balls the AI threw, and a weakening move came first while the foe's bar was above half.
  TRAINER    `trainer_battle_r116.ss1` (YOUNGSTER JOEY's battle just begun: Grovyle L16 against his Machop), Story;
             CLAIM: won, Joey's DEFEATED flag (322) clear -> set, Grovyle's experience rose.
  RIVAL      `rival_r103.ss1` (MAY's battle on Route 103 just begun, after the AI's OWN walk up to her and talk: Mudkip L6
             13/23 against her Treecko), Story, seed 5; CLAIM: won, DEFEATED_RIVAL_ROUTE103 and May's trainer flag (529)
             clear -> set. ‼ At 13/23 HP the battle is close: 1 of 8 seeds won in development, 2 of 10 in the seed sweep
             (`rate_step4.py` RIVAL); seed 5 is a won one, CHOSEN FOR IT and SAID so: this arm proves the battle can be played
             to a win and the game agrees, not how often. A person would heal first (step 5 chains a heal).
  CHALLENGE  `route103.ss1` (Route 103 BEFORE the rival: DEFEATED_RIVAL_ROUTE103 clear), Story, `AI_PLAYER_TALK_TO` 10,3:
             the AI walks up to May by its own navigator and talks to her; CLAIM: the rival's battle BEGAN after the AI's
             talk A (the game's trainer-battle count +1), was played by the decider to its end, and the game's result and
             the rival flag agree (won <-> set). The outcome itself is the RIVAL rate's business.
  TYPE       `geodude_grovyle.ss1` (a DOUBLE battle: HIKER CLARK's Geodude and YOUNGSTER JOHNSON's Shroomish, Grovyle L17
             and Nincada out), Story; CLAIM: every move Grovyle chose while the Geodude stood is ABSORB aimed at the
             Geodude (Grass x4: worth 120 against Pursuit 40 and Quick Attack 20).
  TYPEX      FAULT of TYPE (`AI_PLAYER_FAULT_IGNORE_TYPES=1`: the decider values every matchup as neutral, no STAB):
             CLAIM: Absorb is NEVER chosen against the Geodude (Pursuit and Quick Attack are), and purity still CLEAN.
  FAINT      `faint_r116.ss1` (SCHOOL KID KAREN's battle just begun, Mudkip L14 29/42 against her Shroomish), Story,
             seed 1; CLAIM: the lead Mudkip (PID 550a9be6) FAINTS (HP 0 by the second path), the AI chooses who goes in
             by PID through the party menu and SEND OUT, and the battle goes on to its end: won, Karen's flag (280) set.
             (The step-4 verifier's round: "the README says ... best matched against the foe ... the live party menu has
             no battle view, so `replacement` ranks by level x HP share only".) CLAIM since: the choice is made AGAINST the
             foe the decider REMEMBERS ("Taillow L6 (11/21 HP) is the best left against Shroomish (the field REMEMBERED
             ...)": Flying against Grass, where step 4 sent the full-HP Nincada), and the GAME (the replay) shows that
             Taillow come onto battler 0.
  DFAINT     (the step-4 verifier's FAILURE: "in a DOUBLE battle, when the partner faints, the AI sends in the Pokemon that
             is already on the field, and the battle gets stuck") `geodude_grovyle.ss1`, seed 6 with
             `AI_PLAYER_FAULT_IGNORE_TYPES=1` (the verifier's own reproduction: the types fault only makes the partner
             Nincada fall; the replacement rule under test is the real one). CLAIM: the decider names a Pokemon that is
             NOT the Grovyle standing on the field ("not Grovyle on the field ... REMEMBERED"), the game refuses nothing,
             the battle is WON (Clark's 631 and Johnson's 754 set), and the GAME (the replay) shows Nincada's HP 0 at
             position 2, then the named Pokemon come onto position 2 while the Grovyle stands at 0.
  DFAINTX    FAULT of DFAINT: the step-4 code (`AI_PLAYER_FAULT_FORGET_FIELD=1`: the party menu's look alone;
             `AI_PLAYER_FAULT_IGNORE_REFUSAL=1`: the refusal watched): CLAIM: "who goes in: Grovyle", and the run ends
             "stuck: the battle: no Pokemon could be sent in" (the verifier's bug, through the real launcher); purity CLEAN.
  REFUSE     `ki17_partymenu_wedge.ss1` (a story-bot save stopped ON the battle party menu's "SKITTY is already in
             battle!", Mauville's gym), Story, seed 1: the backstop of the fix, from a state the AI did not make. CLAIM: the
             AI reads the words and presses A on their WAIT (gate `text printer 6 WAIT`, a busy party list), the decider is
             told Skitty was refused, Mightyena goes in (the GAME, by the replay: its PID onto the field), and the battle is
             WON (`gBattleOutcome` 1). Its fault half is `rate_step4.py` REFUSE-FAULT (5 of 5 stuck).
THE REPLAY (the step-4 verifier's round: "live_step4 makes no game read of the move or its target"): every arm that starts
IN a battle (TYPE, TYPEX, FAINT, DFAINT, DFAINTX, REFUSE) is replayed in-process from the same fixture, seed, personality
and faults (`hands_harness.py --battle-log`, the cartridge's clock pinned), reading the GAME's battle after every frame
(`BattleRecorder`: each battler's chosen move, each HP change with its user, move and target, each Pokemon that came
onto a position). It counts only if its frames and presses EQUAL the launcher's: then it is the launcher's trajectory,
replayed (one trajectory, CLAUDE.md rule 8), and its game record is the second path for the moves and the send-ins.
  LEARN      `learn_r116.ss1` (a wild battle on Route 116 begun with the Mudkip at 1,978 experience, 57 short of level
             15, where it learns BIDE), Story, seed 1; CLAIM: the Mudkip (PID) reaches level 15, BIDE is in its moves and
             GROWL is not (the decider's reason logged: Bide worth 40, Growl a status move worth 4), forgotten on the
             summary screen by reading its cursor.
The RECOIL proof is a RECORDED case (`test_battle.py` RecordedRecoilTests, on `fixtures/recoil_r102.look.json`, the AI's own
look in a real battle: Take Down never chosen at 3 HP, where its recoil would knock the Marshtomp out) with the unit tests
(a sturdy Taillow: never at 20 % HP), and the seed sweep's live A/B (`rate_step4.py` RECOIL: the same battle, the recoil
charged on what the hit can take, against the step-4 rule; the game's own recoil read).

PRE-REGISTERED (`PREDICTED`, machine-checked): each arm's claims above, and, for the arms that start IN a battle (where the
game reads no clock), its frames and presses from a development run of the same code in-process with the cartridge's clock
pinned (`hands_harness.py --game-clock`), written BEFORE the graded runs. The roaming arms (WILD, CATCH, CHALLENGE) walk the
overworld, where the game reads the HOST's clock (the step-3.1 finding): their claims are registered, not their frames.

STEP 4.1 (2026-10-09, the step-4 verifier's and adversarial review's findings): seven new arms, each from a fixture PLAYED
by button presses (`gates/make_step41_fixtures.py`) and each REPLAYED for the game's own record:
  SHIFT      `rival_rustboro.ss1` (Rustboro's rival: Wingull L13 then Treecko L15 against the Marshtomp put first), Trainer,
             seed 1 (a YES seed, CHOSEN and said so: the sweep's SHIFT plan says how often); CLAIM: "about to use TREECKO.
             Will ... change POKéMON?" judged about the TREECKO its words name (x4 on the Water/Ground Marshtomp; the battle
             view still holds the fainted Wingull), YES, the party menu gets the Taillow chosen THERE, and BY THE GAME the
             Taillow came onto position 0 by its PID before the Treecko came out; won, MAY's flag (600) set.
  SHIFTX     FAULT of SHIFT (`AI_PLAYER_FAULT_SHIFT_FAINTED=1`, step 4's answer): judged about the fainted Wingull, NO; BY
             THE GAME nobody came onto position 0 between the Wingull's faint and the Treecko's send-out.
  HEAL       `heal_r103.ss1` (Route 103's rival after the AI bought two Potions at Oldale's mart), Story, seed 1; CLAIM: a
             Potion used with the Mudkip low (the told decision), one Potion fewer BY THE TRUTH, the Mudkip's HP up at
             position 0 BY THE GAME (its max HP unchanged: not a level-up), won, May's flag (529) set. The heal path's
             DEVELOPMENT RUN found a bug no unit test had: after the Potion the party menu's message waited for A and the
             skill gave up ("the Potion could not be given"); fixed (`skills/battle.py` _give_item).
  SWITCH     `switch_joey.ss1` (the Poochyena put first, Joey's Machop: Fighting x2 on Dark), Story, seed 1; CLAIM: the
             decider SWITCHED, and BY THE GAME the Mudkip came onto position 0 by its PID with the Poochyena still standing;
             won, Joey's flag set.
  RUN        `run_r116.ss1` (a wild battle begun with the Poochyena at 29 % while training), Story, seed 1; CLAIM: the
             decider RAN, gBattleOutcome 4 BY THE TRUTH, and the Poochyena never fell BY THE GAME. (Step 4.1 round 2, the
             verifier: "the gBattleOutcome check never records the value before the run ... The fixture's start state
             already reads 4") and BY THE GAME every frame: gBattleOutcome on the replay's first frame, already 0 (the
             battle's own clear, `BattleStartClearSetData`, runs in that frame), then 4, the last; the stale 4 is what the
             TRUTH reads in the fixture before the run (round 3: this line called the first recorded value "the fixture's
             old 4").
  REFUSED    (step 4.1 round 2, the verifier's weak proof: "Finding 2 has no live arm (no fixture has a Disabled move)")
             `grind_stall_ppzero.ss1` (a story-bot save in a wild battle: Wailord L61 against a Zubat L36, its Surf, Water
             Spout and Waterfall at 0 PP, Dive at 10), Story, seed 1, the decider made BLIND TO PP
             (`AI_PLAYER_FAULT_IGNORE_PP=1`): it chooses moves with none, and the GAME refuses each through the code that
             refuses a Disabled move (`src/battle_util.c` TrySetCantSelectMoveBattleScript: Disable, Torment, Taunt,
             Imprison, a Choice item, then `pp == 0`); CLAIM: the grid came back for at least two different moves in one
             turn, each with 0 PP BY THE TRUTH, and BY THE GAME the moves it TOOK (gChosenMoveByBattler) all have PP; won.
             REFUSEDX: `_FORGET_UNUSABLE` too (step 4): the grid back again and again, no move taken until a bound (the
             40,000-frame budget, before the skill's 150-menu bound).
  CATCHS     (its weak proof: "The catch's sleep or paralysis move is never exercised live") `sing_r117.ss1`
             (`make_step41_fixtures.py --only sing`: strength_boxfirst_mauville.ss1, a Skitty L17 with SING put first by
             START-menu presses, the AI's explore brain to Route 117, its battle brain roaming; the first frame of a wild
             battle against an Oddish the Pokedex has not got), Catcher, seed 1; CLAIM: Sing chosen, BY THE GAME taken
             and the Oddish ASLEEP (gBattleMons[1].status1) before the catch, caught by the truth (one new PID, the
             player's OT). CATCHSX: `AI_PLAYER_FAULT_NO_CATCH_STATUS=1` (step 4): no Sing, never asleep.
  OVERKILL   `ch13_r119_wedge.ss1` (the recorded recoil case: every damaging move finishes the 15-HP Poochyena), Story,
             seed 1; CLAIM: the told values say the finishers are worth as the strongest, and BY THE GAME the first move is
             not Take Down. OVERKILLX: FAULT (`AI_PLAYER_FAULT_OVERKILL=1`, step 4's valuation): Take Down.
Every in-battle arm's frames and presses were RE-REGISTERED from development runs of the step-4.1 code (`PREDICTED`).

THE STEP-4 VERIFIER'S SECOND ROUND (2026-10-09): no arm and no number changes. Two things moved under them: each told fight
line now ends with the battler position and what the type chart changed in the choice (`brain/battle.py` TypeSay: the
sweep's TYPE-DECISIONS reads it; TYPE's and TYPEX's checks read the move and the values before it, unchanged), and the
explorer that WILD, CATCH and CHALLENGE walk with carries its decisions on (`brain/explore.py` carry_on, the doormat, the
way back to a map seen all of): those three register claims, not trajectories, as before.

STEP 4.1 ROUND 2 (2026-10-09): the arms REFUSED, REFUSEDX, CATCHS and CATCHSX are new (their numbers from a development pass
of this round's code, moved out of the evidence folder before the graded run); RUN's check reads gBattleOutcome every frame;
the replay's recorder (`hands_harness.py` BattleRecorder) also records gBattleOutcome and every battler's status1, and the
truth each move's PP (`party_pp`). The walk under WILD, CATCH and CHALLENGE now waits for someone in its way and bends its
detours (`brain/navigator.py` STEP 4.1 ROUND 2): those three register claims, not trajectories.

STEP 4.1 ROUND 3 (2026-10-09, the step-4.1 verifier's second round):
  SHIFTC     (its weak proof: "Finding 1, the PID carried to the party menu, cannot fail live ... the by-level fallback ...
             also picks the L17 Taillow") `rival_rustboro_hurt.ss1` (`make_step41_fixtures.py --only rival_hurt`: the
             Taillow hurt by the AI's own battles on Route 116 to 36/45, so a party menu that ranks AGAIN by level puts the
             Poochyena, 42/42 L16, above it), Trainer, seed 2 (a YES seed, CHOSEN and said so); CLAIM: YES about the
             TREECKO, "who goes in: Taillow ... decided at the question", and BY THE GAME the Taillow (a8dbcf1b) came onto
             position 0 before the Treecko. SHIFTCX: `AI_PLAYER_FAULT_FORGET_SHIFT=1` (decided at the question, NOT carried):
             the same YES, the party menu by level, and BY THE GAME the POOCHYENA (2b19ca91) came in: the carry's A/B.
  The damage estimate no longer reads the foe's species' base stats (`brain/battle.py` STEP 4.1 ROUND 3: a typical
  Pokemon of the foe's level, corrected by the hits seen), so every in-battle arm's frames and presses were RE-REGISTERED
  from a development pass of this round's code, moved out of the evidence folder before the graded run. REFUSEDX's title
  and RUN's check line were corrected (the verifier: a title naming the wrong bound; three labels for two values).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.live_step2 import check_purity, classify_a, clean_env, truth_of  # noqa: E402
from ai_player.gates.provenance import keep_earlier, provenance as tree_provenance  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.gates.live_step2 import run_json  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BATTLES, ENV_BRAIN, ENV_FAULT_FORGET_FIELD, ENV_FAULT_FORGET_UNUSABLE, ENV_FAULT_IGNORE_PP, ENV_FAULT_IGNORE_REFUSAL,
    ENV_FAULT_IGNORE_TYPES, ENV_FAULT_NO_CATCH_STATUS, ENV_FAULT_OVERKILL, ENV_FAULT_SHIFT_FAINTED, ENV_FAULT_UNCAPPED_RECOIL,
    ENV_PERSONALITY, ENV_SEED, ENV_TALK_TO, ENV_FAULT_FORGET_SHIFT,
)

GATES = Path(__file__).resolve().parent
SAVES = REPO / "tools" / "story-dev" / "saves"
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step4"
PROFILE = "ai-step4-battle"
FRAME_SLACK = 5
SELFTEST_LINE = "[SELFTEST] not run"
FIXTURES: dict[str, tuple[Path, str]] = {
    "route101_south.ss1": (GATES / "fixtures" / "route101_south.ss1", "81bf318a1532c5364f60064530f9984b"),
    "trainer_battle_r116.ss1": (GATES / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
    "route103.ss1": (SAVES / "route103.ss1", "0d951fe21be35a6eafade207ddff5961"),
    "rival_r103.ss1": (GATES / "fixtures" / "rival_r103.ss1", "a5a1624d7cf617ed731070a7569ff986"),
    "geodude_grovyle.ss1": (GATES / "fixtures" / "geodude_grovyle.ss1", "0e22cfda06a8bcf7f53b21aacc51a94d"),
    "faint_r116.ss1": (GATES / "fixtures" / "faint_r116.ss1", "14c714d4e2a34633a577a132f85665fb"),
    "learn_r116.ss1": (GATES / "fixtures" / "learn_r116.ss1", "d9f9c6dfdcdec46b08243df38828e98b"),
    # (the step-4 verifier's round) a story-bot save stopped on the battle party menu's refusal (KI-17's wedge)
    "ki17_partymenu_wedge.ss1": (SAVES / "ki17_partymenu_wedge.ss1", "0103bfe9881ba83eb8919a06a952938f"),
    # (step 4.1) `gates/make_step41_fixtures.py`, each PLAYED by button presses
    "rival_rustboro.ss1": (GATES / "fixtures" / "rival_rustboro.ss1", "862025959e9a879c729eda359e24b8ff"),
    "heal_r103.ss1": (GATES / "fixtures" / "heal_r103.ss1", "7c8f131345d801cdc3fee5a150930607"),
    "switch_joey.ss1": (GATES / "fixtures" / "switch_joey.ss1", "89cbe4e0fd256311a427f506713422e4"),
    "run_r116.ss1": (GATES / "fixtures" / "run_r116.ss1", "5f7e8b23495c1533030619cc27943e1e"),
    # the recorded recoil case's save (a wild Poochyena L3 with 15 HP against a Marshtomp L32 with Take Down)
    "ch13_r119_wedge.ss1": (SAVES / "ch13_r119_wedge.ss1", "b04d3e4cb7d8c8e2a3b82225548906ef"),
    # (step 4.1 round 2) a story-bot save IN a wild battle: Wailord L61 against a Zubat L36, its Surf, Water Spout and
    # Waterfall at 0 PP, Dive at 10 (arms REFUSED, REFUSEDX)
    "grind_stall_ppzero.ss1": (SAVES / "grind_stall_ppzero.ss1", "9ca6c133e2977f5459c7393af27662ef"),
    # (step 4.1 round 2) `make_step41_fixtures.py --only sing`: a wild Oddish L14 (not caught yet) against a Skitty L17 with
    # SING, put first by START-menu presses (arms CATCHS, CATCHSX)
    "sing_r117.ss1": (GATES / "fixtures" / "sing_r117.ss1", "679341be1d3f3557eae74f95d65bfffc"),
    # (step 4.1 round 3) `make_step41_fixtures.py --only rival_hurt`: Rustboro's rival with the Taillow hurt into the window
    # where the party menu's by-level ranking puts it under the Poochyena (arms SHIFTC, SHIFTCX)
    "rival_rustboro_hurt.ss1": (GATES / "fixtures" / "rival_rustboro_hurt.ss1", "baa0a5c385c538f4dede8ffd2f9447c7"),
}
HARNESS = GATES / "hands_harness.py"
#: The replay's cartridge clock (the in-battle arms read none; pinned so the replay is the same whenever it is played).
REPLAY_CLOCK = "2026-10-08T06:00"
#: The fault switches of an arm's env, as the harness names them.
FAULT_NAMES = {ENV_FAULT_IGNORE_TYPES: "ignore_types", ENV_FAULT_UNCAPPED_RECOIL: "uncapped_recoil",
               ENV_FAULT_FORGET_FIELD: "forget_field", ENV_FAULT_IGNORE_REFUSAL: "ignore_refusal",
               ENV_FAULT_OVERKILL: "overkill", ENV_FAULT_SHIFT_FAINTED: "shift_fainted",
               # (step 4.1 round 2)
               ENV_FAULT_FORGET_UNUSABLE: "forget_unusable", ENV_FAULT_IGNORE_PP: "ignore_pp",
               ENV_FAULT_NO_CATCH_STATUS: "no_catch_status",
               # (step 4.1 round 3)
               ENV_FAULT_FORGET_SHIFT: "forget_shift"}
#: The arms replayed in-process for the game's own battle record (the module docstring, THE REPLAY).
REPLAYED = ("TYPE", "TYPEX", "FAINT", "DFAINT", "DFAINTX", "REFUSE", "SHIFT", "SHIFTX", "HEAL", "SWITCH", "RUN", "OVERKILL",
            "OVERKILLX", "REFUSED", "REFUSEDX", "CATCHS", "CATCHSX", "SHIFTC", "SHIFTCX")
#: (step 4.1) the PIDs of the step-4.1 fixtures' Pokemon (the framework's decoder, `make_step41_fixtures.py`'s printouts)
TAILLOW_RUSTBORO, POOCHYENA_116 = "a8dbcf1b", "5815089e"
#: (step 4.1 round 3) the rival-prep party's Poochyena: the one a party menu ranking again by level sends in the hurt fixture
POOCHYENA_RUSTBORO = "2b19ca91"
MAY_RUSTBORO = "600"
MUDKIP = "550a9be6"  # the starter's PID in every Route 101-116 fixture (the same playthrough)
GROVYLE = "550a9be6"  # trainer_battle_r116 / geodude_grovyle: the same Pokemon, evolved in another playthrough
#: Trainers (`include/constants/opponents.h`): TRAINER_JOEY, TRAINER_KAREN_1, TRAINER_MAY_ROUTE_103_MUDKIP.
JOEY, KAREN, MAY = "322", "280", "529"
#: The PRE-REGISTERED numbers (module docstring), written from the development runs (2026-10-08, in-process, this code,
#: `hands_harness.py battle ... --game-clock 2026-10-08T06:00`) BEFORE the graded runs. The arms that start IN a battle
#: register their frames and presses (the game reads no clock in a battle); the roaming arms only their claims (checks).
PREDICTED: dict[str, dict] = {
    "TRAINER": {"outcomes": ["won"], "frames": 3811, "presses": 14},
    "RIVAL": {"outcomes": ["won"], "frames": 6103, "presses": 21},
    # (step 4.1, development runs in-process with this round's code, 2026-10-09, before the graded runs: TYPE 11458 / 48
    # and DFAINT 17536 / 95 under step 4: the rough damage and the finishers moved their later turns; the other step-4
    # arms' trajectories did not move)
    "TYPE": {"outcomes": ["won"], "frames": 12243, "presses": 49, "first": ["Absorb", "Geodude"]},
    "TYPEX": {"outcomes": ["won"], "frames": 9468, "presses": 49, "first": ["Quick Attack", "Shroomish"]},
    # (the step-4 verifier's round, development runs in-process with this round's code, 2026-10-08) FAINT's replacement is
    # now chosen against the remembered Shroomish: Taillow, where step 4 sent the Nincada (11113 frames, 28 presses then)
    "FAINT": {"outcomes": ["won"], "frames": 9503, "presses": 30, "sent": ["Taillow"]},
    # (step 4.1 round 3, the development pass of this round's code: the typical-Pokemon damage guess moved DFAINT's later
    # turns back to step 4's trajectory, 17536 / 95; step 4.1's rough species-based estimate gave 15640 / 82; no other
    # in-battle arm's numbers moved)
    "DFAINT": {"outcomes": ["won"], "frames": 17536, "presses": 95, "sent": ["Skitty"]},
    "DFAINTX": {"outcomes": ["the battle: no Pokemon could be sent in"], "frames": 8200, "presses": 39, "sent": ["Grovyle"]},
    "REFUSE": {"outcomes": ["won"], "frames": 10182, "presses": 52, "sent": ["Mightyena"]},
    "LEARN": {"outcomes": ["won"], "frames": 3918, "presses": 19},
    "CATCH": {"outcomes": ["caught"]},
    # (step 4.1, the same development runs)
    # ⚠ RE-REGISTERED AFTER OBSERVATION (2026-10-09, the coordinator's step-4.1 review fixes): finding 3 (a move FINISHES
    # only on its LOW estimate) changed the MOVES chosen in these three battles (SWITCH: Water Gun for Mud-slap on turn 4;
    # SHIFT: Tackle, Water Gun, Focus Energy, Wing Attack where Water Gun, Wing Attack were), so their trajectories moved:
    # SHIFT 10689/36 -> 12162/46, SHIFTX 11693/43 -> 12817/49, SWITCH 5981/28 -> 6020/27. Outcomes and the Pokemon sent
    # held unchanged. These three numbers are a replay check from here on, NOT predictions made before a look.
    "SHIFT": {"outcomes": ["won"], "frames": 12162, "presses": 46, "sent": ["Taillow"]},
    "SHIFTX": {"outcomes": ["won"], "frames": 12817, "presses": 49},
    "HEAL": {"outcomes": ["won"], "frames": 6978, "presses": 28, "heals": 1},
    "SWITCH": {"outcomes": ["won"], "frames": 6020, "presses": 27},
    "RUN": {"outcomes": ["ran"], "frames": 1063, "presses": 5},
    "OVERKILL": {"outcomes": ["won"], "frames": 1702, "presses": 6},
    "OVERKILLX": {"outcomes": ["won"], "frames": 1762, "presses": 6},
    # (step 4.1 round 2, the development pass of this round's code, `--evidence-tag step4dev41b`, moved out before the graded
    # run; the in-process replays agreed)
    "REFUSED": {"outcomes": ["won"], "frames": 3222, "presses": 17, "refused": ["Waterfall", "Water Spout", "Surf"],
                "taken": ["Dive"]},
    "REFUSEDX": {"outcomes": [], "frames": 40000, "presses": 385, "refused_count": 134},
    "CATCHS": {"outcomes": ["caught"], "frames": 7162, "presses": 24, "sings": 2},
    "CATCHSX": {"outcomes": ["caught"], "frames": 4752, "presses": 19},
    # (step 4.1 round 3, the development pass of this round's code, `--evidence-tag step4dev41c`, moved out of the evidence
    # folder before the graded run; the in-process replays agreed)
    "SHIFTC": {"outcomes": ["won"], "frames": 13149, "presses": 43, "sent": ["Taillow"]},
    "SHIFTCX": {"outcomes": ["won"], "frames": 15648, "presses": 57, "sent": ["Poochyena", "Taillow"]},
}


@dataclass
class Arm:
    name: str
    title: str
    fixture: str
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    seed: int = 3
    doc: str = ""


@dataclass
class Run:
    arm: Arm
    command: list[str] = field(default_factory=list)
    exit_code: int = -1
    elapsed: float = 0.0
    started: float = 0.0
    stdout: str = ""
    run_dir: Path | None = None
    verdict: dict | None = None
    records: list[dict] = field(default_factory=list)
    ai_log: str = ""
    before: dict | None = None
    after: dict | None = None
    state_mtime: float | None = None
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    measures: dict = field(default_factory=dict)
    predictions: list = field(default_factory=list)
    #: (the step-4 verifier's round) the in-process replay with the game's battle read each frame (THE REPLAY)
    replay: dict | None = None

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    def measure(self, name: str, value) -> None:
        self.measures[name] = value

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or ""


def story(battles: int = 1, **extra: str) -> dict[str, str]:
    return {ENV_PERSONALITY: "Story", ENV_BATTLES: str(battles), **extra}


ARMS: list[Arm] = [
    Arm("WILD", "roam Route 101's grass and fight what comes: a wild battle WON by fighting, experience gained",
        "route101_south.ss1", 40000, 1500.0, story(4), doc="gates/make_step3_fixtures.py (route101_south.build.json)"),
    Arm("CATCH", "a species it has not caught, weakened then caught: a NEW PID with the player's OT id, balls spent",
        "route101_south.ss1", 20000, 900.0, {ENV_PERSONALITY: "Catcher", ENV_BATTLES: "1"}, doc="as WILD"),
    Arm("TRAINER", "YOUNGSTER JOEY's battle on Route 116 fought to the end: won, his defeated flag set", "trainer_battle_r116.ss1",
        12000, 600.0, story(), doc="gates/make_trainer_fixture.py: Joey's battle just begun"),
    Arm("RIVAL", "MAY's battle on Route 103 (after the AI's own walk up to her and talk): won, the rival flag set",
        "rival_r103.ss1", 12000, 600.0, story(), seed=5,
        doc="gates/make_step4_fixtures.py --only rival (rival_r103.build.json): route103.ss1 played on by the AI's own battle "
            "brain, talk to (10,3), seed 1; saved on the battle's first frame"),
    Arm("CHALLENGE", "Route 103 before the rival: the AI walks up to May, talks, and the rival's battle is played to its end",
        "route103.ss1", 20000, 900.0, story(1, **{ENV_TALK_TO: "10,3"}), seed=1,
        doc="tools/story-dev/saves/route103.ss1: Route 103, DEFEATED_RIVAL_ROUTE103 clear, May at (10,3)"),
    Arm("TYPE", "a double battle against a hiker's GEODUDE: Grovyle's every move against it is ABSORB (Grass x4)",
        "geodude_grovyle.ss1", 30000, 1200.0, story(),
        doc="gates/make_step4_fixtures.py --only type (geodude_grovyle.build.json): trainer_battle_r116.ss1 played on by the "
            "AI's own battle brain (Story, seed 3) until a trainer's Geodude engaged it"),
    Arm("TYPEX", "FAULT of TYPE: type effectiveness ignored (AI_PLAYER_FAULT_IGNORE_TYPES=1): Absorb never chosen",
        "geodude_grovyle.ss1", 30000, 1200.0, story(**{ENV_FAULT_IGNORE_TYPES: "1"}), doc="as TYPE"),
    Arm("FAINT", "KAREN's battle on Route 116: the lead Mudkip FAINTS, the AI sends in the next by PID, and wins",
        "faint_r116.ss1", 20000, 900.0, story(), seed=1,
        doc="gates/make_step4_fixtures.py --only faint (faint_r116.build.json): route116team.ss1 played on by the AI's own "
            "battle brain (Story, seed 2) until a trainer engaged it with the Mudkip below 85 % HP"),
    Arm("LEARN", "a wild battle that takes the Mudkip to level 15: BIDE learned, GROWL forgotten, the reason logged",
        "learn_r116.ss1", 12000, 600.0, story(), seed=1,
        doc="gates/make_step4_fixtures.py --only learn (learn_r116.build.json): route116team.ss1 played on by the AI's own "
            "battle brain (Story, seed 5) until a wild battle began with the Mudkip one battle short of level 15"),
    # (the step-4 verifier's round)
    Arm("DFAINT", "a double battle's PARTNER faints: the one sent in is not the Grovyle still on the field, and it wins",
        "geodude_grovyle.ss1", 30000, 1200.0, story(**{ENV_FAULT_IGNORE_TYPES: "1"}), seed=6,
        doc="as TYPE; seed 6 with the types fault is the verifier's own reproduction (rate_step4 TYPE-FAULT seed 6)"),
    Arm("DFAINTX", "FAULT of DFAINT, the step-4 code (field forgotten, refusal watched): the battle STUCK, as the verifier found",
        "geodude_grovyle.ss1", 30000, 1200.0,
        story(**{ENV_FAULT_IGNORE_TYPES: "1", ENV_FAULT_FORGET_FIELD: "1", ENV_FAULT_IGNORE_REFUSAL: "1"}), seed=6,
        doc="as DFAINT"),
    Arm("REFUSE", "resumed ON the party menu's 'SKITTY is already in battle!': read, A on its wait, Mightyena in, won",
        "ki17_partymenu_wedge.ss1", 30000, 1200.0, story(), seed=1,
        doc="tools/story-dev/saves/ki17_partymenu_wedge.ss1: the story bot's KI-17 wedge, saved on the battle party "
            "menu's refusal (Mauville gym)"),
    # (step 4.1)
    Arm("SHIFT", "Rustboro's rival: 'about to use TREECKO. Will ... change?' judged about the TREECKO, YES, the Taillow chosen "
                 "there sent in before it", "rival_rustboro.ss1", 30000, 1200.0, {ENV_PERSONALITY: "Trainer", ENV_BATTLES: "1"},
        seed=1, doc="gates/make_step41_fixtures.py --only rival (rival_rustboro.build.json): fresh_rivalprep.ss1, the "
                    "Marshtomp put first, Potions bought by the AI's mart brain, the rival met by walking; the battle's first "
                    "frame. Trainer (switch_willing 0.8), seed 1: a YES seed, CHOSEN and said so"),
    Arm("SHIFTX", "FAULT of SHIFT (AI_PLAYER_FAULT_SHIFT_FAINTED=1, step 4's answer): judged about the FAINTED Wingull: NO",
        "rival_rustboro.ss1", 30000, 1200.0, {ENV_PERSONALITY: "Trainer", ENV_BATTLES: "1", ENV_FAULT_SHIFT_FAINTED: "1"},
        seed=1, doc="as SHIFT"),
    Arm("HEAL", "Route 103's rival with two Potions the AI bought: its Mudkip low, a Potion used (one fewer, HP up), won",
        "heal_r103.ss1", 20000, 900.0, story(), seed=1,
        doc="gates/make_step41_fixtures.py --only heal (heal_r103.build.json): route103.ss1, Oldale's mart (the AI's mart "
            "brain: 2 Potions), back to May and talked to by the AI's battle brain; the battle's first frame"),
    Arm("SWITCH", "a forced bad matchup (the Poochyena, Dark, against Joey's Machop): SWITCH to the Mudkip by PID, by the game",
        "switch_joey.ss1", 20000, 900.0, story(), seed=1,
        doc="gates/make_step41_fixtures.py --only switch (switch_joey.build.json): route116team.ss1, the Poochyena put first "
            "(START menu presses), Joey talked to by the AI's battle brain; the battle's first frame"),
    Arm("RUN", "training, the Poochyena at 29 % HP: an unwanted wild battle RUN from (gBattleOutcome 4)", "run_r116.ss1", 12000,
        600.0, story(), seed=1,
        doc="gates/make_step41_fixtures.py --only run (run_r116.build.json): route116team.ss1, the Poochyena put first, the "
            "AI's battle brain roaming; the first frame of a wild battle begun with the Poochyena under 30 %"),
    Arm("OVERKILL", "every move FINISHES the 15-HP Poochyena: not Take Down (85 %, recoil), by the game", "ch13_r119_wedge.ss1",
        8000, 600.0, story(), seed=1,
        doc="tools/story-dev/saves/ch13_r119_wedge.ss1: a wild Poochyena L3 against a Marshtomp L32 74/99 with Take Down "
            "(the recorded look of `fixtures/recoil_r102.look.json`)"),
    Arm("OVERKILLX", "FAULT of OVERKILL (AI_PLAYER_FAULT_OVERKILL=1, step 4's valuation): Take Down", "ch13_r119_wedge.ss1",
        8000, 600.0, story(**{ENV_FAULT_OVERKILL: "1"}), seed=1, doc="as OVERKILL"),
    # (step 4.1 round 2, the verifier's weak proof: "Finding 2 has no live arm (no fixture has a Disabled move)")
    Arm("REFUSED", "finding 2 LIVE: the decider made blind to PP (AI_PLAYER_FAULT_IGNORE_PP=1) chooses moves with none; the "
                   "GAME refuses each (the code that refuses a Disabled move) and gives the grid back; each is out for the "
                   "turn, and the move with PP, Dive, is the one the game takes", "grind_stall_ppzero.ss1", 12000, 600.0,
        story(**{ENV_FAULT_IGNORE_PP: "1"}), seed=1,
        doc="tools/story-dev/saves/grind_stall_ppzero.ss1: a story-bot save in a wild battle, Wailord L61 against a Zubat L36, "
            "its Surf, Water Spout and Waterfall at 0 PP, Dive at 10"),
    # (step 4.1 round 3, the verifier: the title said "until the 150-menu bound" while the run ends at the frame bound)
    Arm("REFUSEDX", "FAULT of REFUSED, the step-4 rule (AI_PLAYER_FAULT_FORGET_UNUSABLE=1 too): a refused move chosen again "
                    "and again, the game takes no move until a bound ends the run (here the 40,000-frame budget, before "
                    "the skill's 150-menu bound)", "grind_stall_ppzero.ss1", 40000, 1200.0,
        story(**{ENV_FAULT_IGNORE_PP: "1", ENV_FAULT_FORGET_UNUSABLE: "1"}), seed=1, doc="as REFUSED"),
    # (step 4.1 round 2, the verifier's weak proof: "The catch's sleep or paralysis move is never exercised live")
    Arm("CATCHS", "a CATCH helped by SLEEP: the Skitty's SING on a wild Oddish it has not caught, the Oddish asleep by the "
                  "game, then the ball: caught", "sing_r117.ss1", 20000, 900.0, {ENV_PERSONALITY: "Catcher", ENV_BATTLES: "1"},
        seed=1, doc="gates/make_step41_fixtures.py --only sing (sing_r117.build.json): strength_boxfirst_mauville.ss1, the "
                    "Skitty put first (START menu presses), the AI's explore brain to Route 117, its battle brain roaming; "
                    "the first frame of a wild battle against a species the Pokedex has not got"),
    Arm("CATCHSX", "FAULT of CATCHS (AI_PLAYER_FAULT_NO_CATCH_STATUS=1, step 4: no status move to help a catch): no Sing, the "
                   "ball thrown at the foe awake", "sing_r117.ss1", 20000, 900.0,
        {ENV_PERSONALITY: "Catcher", ENV_BATTLES: "1", ENV_FAULT_NO_CATCH_STATUS: "1"}, seed=1, doc="as CATCHS"),
    # (step 4.1 round 3, the verifier's weak proof: "Finding 1, the PID carried to the party menu, cannot fail live")
    Arm("SHIFTC", "the CARRY live: the Taillow hurt so a by-level party menu would send the Poochyena; YES about the TREECKO, "
                  "and BY THE GAME the Taillow (its PID, carried from the question) comes in", "rival_rustboro_hurt.ss1",
        30000, 1200.0, {ENV_PERSONALITY: "Trainer", ENV_BATTLES: "1"}, seed=2,
        doc="gates/make_step41_fixtures.py --only rival_hurt (rival_rustboro_hurt.build.json): fresh_rivalprep.ss1, the "
            "Taillow put first and hurt by the AI's battle brain on Route 116 to 36/45 (by level 15.3 under the Poochyena's "
            "16.0), the Marshtomp put first, Potions bought, the rival met. Trainer, seed 2: a YES seed, CHOSEN and said "
            "so (the sweep's SHIFT-CARRY says how often)"),
    Arm("SHIFTCX", "FAULT of SHIFTC (AI_PLAYER_FAULT_FORGET_SHIFT=1): YES about the TREECKO, the member chosen there NOT "
                   "carried: the party menu ranks by level and BY THE GAME the POOCHYENA comes in",
        "rival_rustboro_hurt.ss1", 30000, 1200.0,
        {ENV_PERSONALITY: "Trainer", ENV_BATTLES: "1", ENV_FAULT_FORGET_SHIFT: "1"}, seed=2, doc="as SHIFTC"),
]


# ---------------------------------------------------------------------- running
def run_arm(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.before, raw = truth_of(FIXTURES[arm.fixture][0])
    if run.before is None:
        run.notes.append(f"truth of the fixture failed: {raw[-1500:]}")
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir),
                   "--state", str(FIXTURES[arm.fixture][0])]
    env = clean_env({ENV_BRAIN: "battle", ENV_SEED: str(arm.seed), **arm.env})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    run.started = time.time()
    began = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw_out, _ = proc.communicate(timeout=arm.wall + 240)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        raw_out, _ = proc.communicate()
        raw_out = (raw_out or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
    run.elapsed = time.monotonic() - began
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw_out.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    state = profile_dir / launcher.STATE_FILE
    if state.is_file():
        run.state_mtime = state.stat().st_mtime
        run.after, raw = truth_of(state)
        if run.after is None:
            run.notes.append(f"truth of the state left behind failed: {raw[-1500:]}")
    return run


def replay_arm(run: Run) -> None:
    """THE REPLAY (module docstring): the arm in-process from the same fixture, seed, personality and faults, the game's
    battle read after every frame (`hands_harness.py --battle-log`)."""
    arm = run.arm
    faults = ",".join(name for env, name in FAULT_NAMES.items() if arm.env.get(env) == "1")
    folder = Path(tempfile.mkdtemp(prefix=f"ai_step4_replay_{arm.name}_"))
    command = [sys.executable, str(HARNESS), "battle", "--state", str(FIXTURES[arm.fixture][0]), "--seed", str(arm.seed),
               "--frames", str(arm.frames), "--personality", arm.env.get(ENV_PERSONALITY, "Story"),
               "--battles", arm.env.get(ENV_BATTLES, "1"), "--run-dir", str(folder), "--game-clock", REPLAY_CLOCK,
               "--battle-log", *(["--fault", faults] if faults else [])]
    try:
        data, raw = run_json(command, "HANDS", clean_env({}), arm.wall + 240)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    run.replay = data
    if data is None:
        run.notes.append(f"the replay gave no result: {raw[-1500:]}")


def check_replay(run: Run) -> dict | None:
    """The replay counts only as THIS run's trajectory: its frames and presses equal the launcher's. Returns its game
    record (`BattleRecorder.result`), or None (the check failed)."""
    data = run.replay or {}
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames")
    presses = run.measures.get("presses")
    same = bool(data) and data.get("frames") == frames and data.get("presses") == presses
    run.check(same, f"THE REPLAY is this run's trajectory: in-process (`hands_harness.py --battle-log`, the same fixture, seed "
                    f"{run.arm.seed} and faults) {data.get('frames')} frames and {data.get('presses')} presses == the launcher's "
                    f"{frames} and {presses} (one trajectory replayed, not a second sample); its outcome {data.get('reason')!r}")
    return (data.get("game_battle") or {}) if same else None


def game_hits(game: dict, attacker: int | None = None) -> list[tuple[str, str, str]]:
    """(the user's species, the move, the species hit) of every HP change one battler's move made on ANOTHER battler, in
    order, by the GAME (`gBattleMons`, `gBattlerAttacker`, `gCurrentMove`, `gBattlerTarget`)."""
    return [(e["attacker_species"], e["move"], e["species"]) for e in game.get("events") or []
            if e["kind"] == "hp" and e["battler"] != e["attacker"] and (attacker is None or e["attacker"] == attacker)
            and e["hp"][1] < e["hp"][0]]


def game_replacements(game: dict) -> list[dict]:
    """Every Pokemon that came onto a PLAYER's position (0, 2) where the one before it had fainted (HP 0), by the GAME,
    with the PID and HP standing on the player's other position at that frame (`rate_step4.game_sent_in`'s rule)."""
    here = {s["battler"]: (s["pid"], s["hp"][0], s.get("species")) for s in game.get("start") or []}
    out = []
    for event in game.get("events") or []:
        if event["kind"] == "in" and event["battler"] in (0, 2):
            before = here.get(event["battler"])
            if before is not None and before[0] != "00000000" and before[1] == 0:
                out.append({**event, "replaced": before, "beside": here.get(2 - event["battler"])})
        if event["kind"] in ("in", "hp"):
            hp = event["hp"][0] if event["kind"] == "in" else event["hp"][1]
            here[event["battler"]] = (event["pid"], hp, event["species"])
    return out


def told_sent(run: Run) -> list[str]:
    """The species the decider named at each party menu ("who goes in: Taillow L6 ...")."""
    return re.findall(r"who goes in: (.+?) L\d+ ", "\n".join(battle_lines(run)))


# ---------------------------------------------------------------------- shared checks
def check_after_is_this_run(run: Run) -> None:
    """The state graded is the one THIS run wrote: written after the run started, its frame the start's plus the run's
    real frames (+-FRAME_SLACK), not the fixture's bytes (as `live_step3.check_after_is_this_run`)."""
    after = run.after or {}
    before_md5 = FIXTURES[run.arm.fixture][1]
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    run.check(bool(after) and written and near and after.get("state_md5") != before_md5,
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER'}; frame {frame} "
              f"== start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} (fixture {before_md5})")


def selftest_after_check() -> list[str]:
    """FAULT-TEST of `check_after_is_this_run` (CLAUDE.md rule 6): its own state passes; a stale one, a frame off by
    3000, no file and the fixture's own bytes fail."""
    arm = ARMS[0]
    md5 = FIXTURES[arm.fixture][1]

    def verdict(mtime, frame, state_md5) -> bool:
        run = Run(arm, started=1000.0, state_mtime=mtime, verdict={"counters": {"real_frames": 3344}},
                  before={"frame": 15268}, after=None if frame is None else {"frame": frame, "state_md5": state_md5})
        check_after_is_this_run(run)
        return run.passed

    cases = [("its own state", verdict(1500.0, 18612, "abc"), True),
             ("a stale state (mtime before the start)", verdict(900.0, 18612, "abc"), False),
             ("a frame +3000", verdict(1500.0, 21612, "abc"), False),
             ("no state file", verdict(None, None, "abc"), False),
             ("the fixture's own bytes", verdict(1500.0, 18612, md5), False)]
    return [f"{name}: passed={got}, want {want}" for name, got, want in cases if got != want]


def check_hands(run: Run, walking: bool) -> None:
    """Every press has its gate; every A is a WAIT, a MENU confirm (the battle's menus included: the action menu, the
    move grid, the target, the battle's yes/no, the bag and its USE, the party and its SHIFT / SEND OUT, the forget-a-move
    list) or a TALK, by its look; walking holds only in the arms that walk; no catch-all idle."""
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"{len(presses)} presses in the action log, every one with its gate (without: {len(no_gate)})")
    kinds: dict[str, int] = {}
    menus: dict[str, int] = {}
    wrong = []
    for press in (p for p in presses if p["action"].startswith("press A ")):
        kind, ok = classify_a(press)
        kinds[kind] = kinds.get(kind, 0) + 1
        if kind == "menu":
            name = str(press.get("reason")).split(" cursor on")[0]
            menus[name] = menus.get(name, 0) + 1
        if not ok:
            wrong.append((press["frame"], kind, press["reason"][:60], (press.get("digest") or "")[:90]))
    run.check(not wrong, f"EVERY A press is a WAIT, a MENU confirm or a TALK by its look: {dict(sorted(kinds.items()))}, "
                         f"the menus {dict(sorted(menus.items()))}; any other: {wrong[:4] or 'none'}")
    blind = [p for p in presses if "NONE" in str(p.get("reason"))]
    run.check(not blind, f"no press without the eyes asked (a 'NONE' gate): {len(blind)}")
    walks = [p for p in presses if str(p.get("reason", "")).startswith(("walk ", "keep walking ", "use the ", "roam "))]
    run.check(bool(walks) == walking, f"{len(walks)} walking holds (want {'some' if walking else 'none'}: this arm "
                                      f"{'walks' if walking else 'starts in a battle'})")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:3] or 'none'}")


def battle_lines(run: Run) -> list[str]:
    return [line for line in run.ai_log.splitlines() if "[AI-HANDS] battle" in line]


def decisions(run: Run) -> list[dict]:
    """The decider's every decision at the action menu (the action log's `decide` records)."""
    return [r for r in run.records if r.get("decision") == "decide" and str(r.get("action", "")).startswith("battle ")]


def outcomes(run: Run) -> list[str]:
    found = re.search(r"battles: \d+ played:? (\[.*?\])", run.outcome)
    return json.loads(found.group(1).replace("'", '"')) if found else []


def party_of(truth: dict | None) -> dict[str, list]:
    """PID -> [species, total experience, level] by the framework's decoder (the second path)."""
    return {row[0]: row[1:] for row in (truth or {}).get("party_exp") or []}


def moves_of(truth: dict | None) -> dict[str, list[str]]:
    return {row[0]: row[2] for row in (truth or {}).get("party_moves") or []}


def balls_of(truth: dict | None) -> int:
    return sum((truth or {}).get("balls", {}).values()) if isinstance((truth or {}).get("balls"), dict) else -1


def stat(truth: dict | None, key: str) -> int | None:
    return ((truth or {}).get("game_stats") or {}).get(key)


def flag(truth: dict | None, name: str) -> bool | None:
    return ((truth or {}).get("flags") or {}).get(name)


def trainer(truth: dict | None, tid: str) -> bool | None:
    return ((truth or {}).get("trainer_defeated") or {}).get(tid)


def grade_common(run: Run, walking: bool) -> None:
    check_purity(run, None)
    check_after_is_this_run(run)
    check_hands(run, walking)
    run.measure("outcomes", outcomes(run))
    run.measure("frames", ((run.verdict or {}).get("counters") or {}).get("real_frames"))
    summary = next((line for line in run.stdout.splitlines() if line.startswith("[AI-HANDS] outcome=")), "")
    pad = re.search(r"presses=(\d+)", summary)
    run.measure("presses", int(pad.group(1)) if pad else None)
    for line in battle_lines(run):
        run.notes.append(line[:600])


def exp_rose(run: Run, pid: str) -> tuple[bool, str]:
    before, after = party_of(run.before).get(pid), party_of(run.after).get(pid)
    ok = before is not None and after is not None and after[1] > before[1]
    return ok, f"{pid}: {before} -> {after}"


# ---------------------------------------------------------------------- the arms
def grade_WILD(run: Run) -> None:
    grade_common(run, walking=True)
    results = outcomes(run)
    run.check("won" in results, f"a wild battle WON by fighting among the battles played: {results}")
    ok, text = exp_rose(run, MUDKIP)
    run.check(ok, f"the Mudkip's experience rose, by PID (the framework's decoder): {text}")
    fights = [d for d in decisions(run) if d.get("action") == "battle fight"]
    run.check(bool(fights), f"the AI chose FIGHT {len(fights)} times; its moves {sorted({(d.get('extra') or {}).get('move') for d in fights})}")
    played, wild = len(results), (stat(run.after, "wild_battles") or 0) - (stat(run.before, "wild_battles") or 0)
    run.check(wild == played, f"the game's own wild-battle count rose by {wild} == the battles the AI played {played}")
    run.measure("won", results.count("won"))


def grade_CATCH(run: Run) -> None:
    grade_common(run, walking=True)
    results = outcomes(run)
    run.check(results == ["caught"] and (run.after or {}).get("battle_outcome") == 7,
              f"the battle ended CAUGHT: the AI's outcome {results}, gBattleOutcome {(run.after or {}).get('battle_outcome')} (7)")
    tid = (run.after or {}).get("player_tid")
    before = {row[0] for row in (run.before or {}).get("party_ot") or []} | {row[0] for row in (run.before or {}).get("boxes") or []}
    after = [(row[0], row[1], "party") for row in (run.after or {}).get("party_ot") or []] + \
            [(row[0], row[1], "box") for row in (run.after or {}).get("boxes") or []]
    new = [entry for entry in after if entry[0] not in before]
    run.check(len(new) == 1 and new[0][1] == tid,
              f"ONE new PID owned by the player: {new} (the player's visible id {tid}; a catch is a new PID with the player's OT)")
    throws = [d for d in decisions(run) if d.get("action") == "battle ball"]
    spent = balls_of(run.before) - balls_of(run.after)
    run.check(bool(throws) and spent == len(throws),
              f"the balls in the bag fell by {spent} == the balls the AI threw {len(throws)} ({balls_of(run.before)} -> {balls_of(run.after)})")
    first = decisions(run)[0] if decisions(run) else {}
    weakened = first.get("action") == "battle fight" and "weaken" in str(first.get("reason"))
    run.check(weakened or "bar is at" in str(first.get("reason")),
              f"it weakened the foe first while the bar was above half, or threw at once with the reason why: "
              f"{first.get('action')}: {str(first.get('reason'))[:160]}")
    run.measure("throws", len(throws))


def grade_TRAINER(run: Run) -> None:
    grade_common(run, walking=False)
    run.check(outcomes(run) == ["won"], f"the battle WON: {outcomes(run)}")
    run.check(trainer(run.before, JOEY) is False and trainer(run.after, JOEY) is True,
              f"YOUNGSTER JOEY's defeated flag (TRAINER_FLAGS_START + 322): {trainer(run.before, JOEY)} -> {trainer(run.after, JOEY)}")
    ok, text = exp_rose(run, GROVYLE)
    run.check(ok, f"the Grovyle's experience rose: {text}")


def grade_RIVAL(run: Run) -> None:
    grade_common(run, walking=False)
    run.check(outcomes(run) == ["won"], f"the rival battle WON: {outcomes(run)}")
    run.check(flag(run.before, "DEFEATED_RIVAL_ROUTE103") is False and flag(run.after, "DEFEATED_RIVAL_ROUTE103") is True,
              f"DEFEATED_RIVAL_ROUTE103: {flag(run.before, 'DEFEATED_RIVAL_ROUTE103')} -> {flag(run.after, 'DEFEATED_RIVAL_ROUTE103')}")
    run.check(trainer(run.before, MAY) is False and trainer(run.after, MAY) is True,
              f"MAY's trainer flag (TRAINER_MAY_ROUTE_103_MUDKIP 529): {trainer(run.before, MAY)} -> {trainer(run.after, MAY)}")


def grade_CHALLENGE(run: Run) -> None:
    grade_common(run, walking=True)
    talks = [p for p in run.presses if str(p.get("reason", "")).startswith("talk: facing ")]
    trainer_battles = (stat(run.after, "trainer_battles") or 0) - (stat(run.before, "trainer_battles") or 0)
    run.check(bool(talks) and trainer_battles == 1,
              f"the AI walked up to May and TALKED ({len(talks)} talk A: {[str(t.get('reason'))[:70] for t in talks][:2]}); the "
              f"game's trainer-battle count rose by {trainer_battles} (1)")
    results = outcomes(run)
    won = flag(run.after, "DEFEATED_RIVAL_ROUTE103")
    run.check(len(results) == 1 and results[0] in ("won", "lost") and (results[0] == "won") == bool(won),
              f"the battle played to its end by the decider: {results}; the game agrees: DEFEATED_RIVAL_ROUTE103 {won}")
    run.measure("result", results[0] if results else None)


def grovyle_turns(run: Run) -> list[tuple[str, str]]:
    """Grovyle's decisions, from the decider's TOLD lines (Grovyle's are the ones valuing Fury Cutter): (the move, the foe
    it was aimed at in the double battle: "at <species>" before the values; "" once one foe is left and nothing is aimed)."""
    found = []
    for line in battle_lines(run):
        hit = re.search(r"turn \d+: fight (.+?): ", line)
        if hit is None or "[Fury Cutter:" not in line:
            continue
        aim = re.search(r" at (\w+) \[Fury Cutter:", line)
        found.append((hit.group(1), aim.group(1) if aim else ""))
    return found


def grade_TYPE(run: Run) -> None:
    grade_common(run, walking=False)
    turns = grovyle_turns(run)
    against = [t for t in turns if t[1] == "Geodude"]
    run.check(bool(turns) and turns[0] == ("Absorb", "Geodude"),
              f"Grovyle's FIRST move, the Geodude on the field: {turns[:1]} (want Absorb aimed at the Geodude: Grass x4, worth "
              f"120, against Pursuit 40 and Quick Attack 20)")
    run.check(bool(against) and all(move == "Absorb" for move, _ in against),
              f"every move Grovyle aimed at the Geodude is ABSORB: {against}")
    run.check(outcomes(run) == ["won"], f"the battle won: {outcomes(run)}")
    run.check(trainer(run.after, "631") is True and trainer(run.after, "754") is True,
              f"the game's defeated flags of both trainers (CLARK 631, JOHNSON 754): {trainer(run.after, '631')}, "
              f"{trainer(run.after, '754')}")
    run.measure("first", list(turns[0]) if turns else None)
    game = check_replay(run)
    if game is not None:
        hits = game_hits(game, attacker=0)
        on_geodude = [move for _, move, hit in hits if hit == "Geodude"]
        run.check(bool(hits) and hits[0][1:] == ("Absorb", "Geodude") and on_geodude and set(on_geodude) == {"Absorb"},
                  f"BY THE GAME (the replay): Grovyle's first hit {hits[:1]} is ABSORB on the Geodude, and every hit it landed "
                  f"on the Geodude was Absorb: {on_geodude}")


def grade_TYPEX(run: Run) -> None:
    grade_common(run, walking=False)
    turns = grovyle_turns(run)
    run.check(bool(turns) and turns[0][0] != "Absorb" and not any(t == ("Absorb", "Geodude") for t in turns),
              f"FAULT (types ignored): Grovyle's first move {turns[:1]} is not Absorb, and Absorb is NEVER aimed at the Geodude "
              f"({turns})")
    told = "\n".join(battle_lines(run))
    run.check("x1 type" in told and "x4 type" not in told and "x0.5 type" not in told,
              "the fault's decider weighed every matchup x1 (no 'x4 type' or 'x0.5 type' in its told values)")
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own decision rule: purity is still CLEAN")
    run.measure("first", list(turns[0]) if turns else None)
    game = check_replay(run)
    if game is not None:
        hits = game_hits(game, attacker=0)
        run.check(bool(hits) and hits[0][1] != "Absorb" and ("Grovyle", "Absorb", "Geodude") not in hits,
                  f"BY THE GAME (the replay), FAULT: Grovyle's first hit {hits[:1]} is not Absorb, and Absorb never hit the "
                  f"Geodude: {hits}")


def grade_FAINT(run: Run) -> None:
    grade_common(run, walking=False)
    lead = party_of(run.after).get(MUDKIP)
    hp = next((row[1] for row in (run.after or {}).get("party") or [] if row[0] == "Mudkip"), None)
    run.check(hp == 0, f"the lead Mudkip FAINTED: its HP by the second path {hp} (party {(run.after or {}).get('party')})")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    party = [p for p in run.presses if str(p.get("reason", "")).startswith("party cursor on ")]
    send = [p for p in run.presses if str(p.get("reason", "")).startswith("party_action cursor on") and "SEND OUT" in str(p.get("reason"))]
    run.check(bool(sent) and bool(party) and bool(send),
              f"the AI chose who goes in ({[s.split('who goes in: ')[-1][:80] for s in sent]}), pressed on the party menu by "
              f"reading its cursor ({[str(p.get('reason')) for p in party]}) and SEND OUT ({len(send)})")
    run.check(outcomes(run) == ["won"] and trainer(run.after, KAREN) is True,
              f"the battle went on to its end: {outcomes(run)}; KAREN's flag (280) {trainer(run.before, KAREN)} -> {trainer(run.after, KAREN)}")
    run.measure("lead", lead)
    # (the step-4 verifier's round) the replacement is chosen AGAINST the foe the decider remembers through the party menu
    run.check(bool(sent) and all(" against Shroomish" in s and "REMEMBERED" in s for s in sent),
              f"the replacement was chosen against the foe REMEMBERED through the party menu (it has no battle view): "
              f"{[s.split('who goes in: ')[-1][:160] for s in sent]}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        run.check([e["species"] for e in came] == told_sent(run) and all(e["battler"] == 0 for e in came)
                  and all(e["replaced"][2] == "Mudkip" for e in came),
                  f"BY THE GAME (the replay): after the Mudkip's HP 0 at position 0, {[(e['battler'], e['species'], e['pid']) for e in came]} "
                  f"came onto it == the decider's choice {told_sent(run)}")


def grade_DFAINT(run: Run) -> None:
    grade_common(run, walking=False)
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and "Grovyle on the field" in sent[0] and "REMEMBERED" in sent[0]
              and not sent[0].split("who goes in: ")[-1].startswith("Grovyle"),
              f"the PARTNER fell and the decider named a Pokemon NOT standing on the field, from the field it REMEMBERED: "
              f"{[s.split('who goes in: ')[-1][:200] for s in sent]}")
    refused = [line for line in battle_lines(run) if "already in battle" in line]
    run.check(not refused, f"the game refused nothing ('already in battle' never read): {refused[:2] or 'none'}")
    run.check(outcomes(run) == ["won"] and trainer(run.after, "631") is True and trainer(run.after, "754") is True,
              f"the battle WON: {outcomes(run)}; CLARK 631 {trainer(run.before, '631')} -> {trainer(run.after, '631')}, JOHNSON "
              f"754 {trainer(run.before, '754')} -> {trainer(run.after, '754')}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        ok = (len(came) == 1 and came[0]["battler"] == 2 and came[0]["replaced"][2] == "Nincada"
              and came[0]["species"] == told_sent(run)[0] and (came[0]["beside"] or ("", 0, ""))[2] == "Grovyle"
              and (came[0]["beside"] or ("", 0, ""))[1] > 0 and came[0]["pid"] != (came[0]["beside"] or ("",))[0])
        run.check(ok, f"BY THE GAME (the replay): the Nincada's HP 0 at position 2, then "
                      f"{[(e['battler'], e['species'], e['pid']) for e in came]} came onto position 2 while "
                      f"{[e['beside'] for e in came]} stood at position 0 (a different PID, HP above 0)")


def grade_DFAINTX(run: Run) -> None:
    grade_common(run, walking=False)
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and sent[0].split("who goes in: ")[-1].startswith("Grovyle"),
              f"FAULT (the step-4 code): the decider, seeing only the party menu, named the Grovyle standing on the field: "
              f"{[s.split('who goes in: ')[-1][:160] for s in sent]}")
    run.check(outcomes(run) == ["the battle: no Pokemon could be sent in"] and "stuck" in run.outcome,
              f"the run ended STUCK, as the verifier found the step-4 code: {run.outcome!r}")
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        run.check(not came, f"BY THE GAME (the replay): nobody came onto the field after the Nincada fell: {came}")


def grade_REFUSE(run: Run) -> None:
    grade_common(run, walking=False)
    said = [line for line in battle_lines(run) if "the party says" in line]
    run.check(len(said) == 1 and "SKITTY is already in battle!" in said[0] and "Skitty" in said[0].split(":")[-1],
              f"the AI READ the party menu's refusal and the decider was told who was refused: {said}")
    waits = [p for p in run.presses if p["action"].startswith("press A ") and p.get("reason") == "text printer 6 WAIT"
             and "ui=party(busy)[" in str(p.get("digest"))]
    run.check(len(waits) == 1, f"ONE A pressed on the refusal's WAIT, over the busy party list: "
                               f"{[(p['frame'], (p.get('digest') or '')[:110]) for p in waits]}")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(len(sent) == 1 and sent[0].split("who goes in: ")[-1].startswith("Mightyena") and "refused" in sent[0],
              f"the next choice is the other healthy member, the refused one named: {[s.split('who goes in: ')[-1][:200] for s in sent]}")
    run.check(outcomes(run) == ["won"] and (run.after or {}).get("battle_outcome") == 1,
              f"the battle WON: {outcomes(run)}, gBattleOutcome {(run.after or {}).get('battle_outcome')}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        came = game_replacements(game)
        mightyena = next((row[0] for row in (run.before or {}).get("party_exp") or [] if row[1] == "Mightyena"), None)
        run.check(len(came) == 1 and came[0]["pid"] == mightyena,
                  f"BY THE GAME (the replay): {[(e['battler'], e['species'], e['pid']) for e in came]} came onto the field: "
                  f"the Mightyena by its PID {mightyena}")


def grade_LEARN(run: Run) -> None:
    grade_common(run, walking=False)
    before, after = party_of(run.before).get(MUDKIP), party_of(run.after).get(MUDKIP)
    run.check(before is not None and after is not None and before[2] == 14 and after[2] == 15,
              f"the Mudkip (PID {MUDKIP}) reached level 15 (the second path): {before} -> {after}")
    moves = moves_of(run.after).get(MUDKIP) or []
    run.check("Bide" in moves and "Growl" not in moves and len(moves) == 4,
              f"its moves now {moves} (was {moves_of(run.before).get(MUDKIP)}): BIDE learned, GROWL forgotten")
    told = [line for line in battle_lines(run) if "would learn" in line]
    forget = [p for p in run.presses if str(p.get("reason", "")).startswith("move_forget cursor on") and "Growl" in str(p.get("reason"))]
    run.check(bool(told) and bool(forget),
              f"the decision told with its reason ({[t.split('would learn ')[-1][:160] for t in told]}) and pressed on the "
              f"summary screen on GROWL by reading the cursor ({[str(p.get('reason')) for p in forget]})")


# ---------------------------------------------------------------------- (step 4.1) the arms
def game_ins(game: dict, battler: int) -> list[dict]:
    return [e for e in game.get("events") or [] if e["kind"] == "in" and e["battler"] == battler]


def game_after_foe_faint(game: dict) -> tuple[dict | None, dict | None, list[dict]]:
    """(the first foe's faint at position 1, the foe the game sent onto position 1 after it, every Pokemon that came onto
    the player's position 0 between the two), by the GAME."""
    events = game.get("events") or []
    faint = next((e for e in events if e["kind"] == "hp" and e["battler"] == 1 and e["hp"][1] == 0), None)
    if faint is None:
        return None, None, []
    foe = next((e for e in game_ins(game, 1) if e["f"] > faint["f"]), None)
    mine = [e for e in game_ins(game, 0) if e["f"] > faint["f"] and (foe is None or e["f"] < foe["f"])]
    return faint, foe, mine


def game_first_choice(game: dict, battler: int = 0) -> str:
    return next((c["chosen"][battler] for c in game.get("chosen") or [] if c["chosen"][battler] != "-"), "")


def pp_of(truth: dict | None, species: str) -> dict[str, int]:
    """(step 4.1 round 2) move -> PP left of the party member `species`, by the framework's decoder (`truth` party_pp)."""
    row = next((r for r in (truth or {}).get("party_pp") or [] if r[1] == species), None)
    return {name: pp for name, pp in row[2]} if row else {}


def grade_REFUSED(run: Run) -> None:
    """(step 4.1 round 2, the verifier's weak proof: "Finding 2 has no live arm (no fixture has a Disabled move)") A move the
    GAME refuses: the decider is made blind to PP (FAULT `ignore_pp`), so it chooses moves with none; the game refuses each
    through the code that refuses a Disabled, Tormented, Taunted or Imprisoned move (`src/battle_util.c`
    TrySetCantSelectMoveBattleScript, read via gh api: its last check is `pp[...] == 0` -> BattleScript_SelectingMoveWithNoPP)
    and gives the move grid back; the skill tells the decider (`cannot_use`), the move is out for the turn, and the game
    takes the move WITH PP. Proven by the truth (the PP of each move the AI was refused) and the game (the moves it TOOK)."""
    grade_common(run, walking=False)
    pp = pp_of(run.before, "Wailord")
    refused = re.findall(r"the move grid came back: (.+?) cannot be used now", " ".join(battle_lines(run)))
    run.check(len(set(refused)) >= 2 and all(pp.get(move) == 0 for move in refused),
              f"THE REFUSALS, the AI's words against THE TRUTH (each move's PP at the start, by the framework's decoder: {pp}): "
              f"the grid came back {len(refused)} times, for {refused}, each a move with 0 PP; at least two different moves in "
              f"one turn (the per-turn set of unusable moves, not one move)")
    run.check(outcomes(run) == ["won"], f"the battle WON (ended by itself): {outcomes(run)}")
    game = check_replay(run)
    if game is not None:
        taken = [c["chosen"][0] for c in game.get("chosen") or [] if c["chosen"][0] != "-"]
        run.check(bool(taken) and all(pp.get(move, 0) > 0 for move in taken),
                  f"BY THE GAME (the replay's gChosenMoveByBattler[0]: a refused move never reaches it): the moves the game "
                  f"TOOK {taken}, each one with PP left ({ {m: pp.get(m) for m in taken} })")
        run.measure("taken", taken)
    run.measure("refused", refused)


def grade_REFUSEDX(run: Run) -> None:
    """(step 4.1 round 2) FAULT of REFUSED: the step-4 rule (`forget_unusable` too): "decide again" chooses a refused move
    again, the game takes no move, and only a bound ends the run: the skill's 150-menu bound or, first at this arm's
    budget, the run's 40,000 frames (round 3: this docstring and the arm's title said the 150-menu bound)."""
    grade_common(run, walking=False)
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    reason = run.outcome
    refused = re.findall(r"the move grid came back: (.+?) cannot be used now", " ".join(battle_lines(run)))
    # (a bound ends it: the skill's 150 menus, or the run's frame budget first: the development pass, 134 refusals in 40,000
    # frames, "stopped: not finished within 40000 frames")
    run.check(("did not end within 150 menus" in reason or "not finished within" in reason) and len(refused) >= 20,
              f"THE HARM (finding 2's loop, reproduced live): the outcome {reason[:200]!r} (a bound, not an end); the grid came "
              f"back {len(refused)} times ({sorted(set(refused))})")
    game = check_replay(run)
    if game is not None:
        taken = [c["chosen"][0] for c in game.get("chosen") or [] if c["chosen"][0] != "-"]
        run.check(not taken, f"BY THE GAME (the replay's gChosenMoveByBattler[0]): no move taken in all that time: {taken or 'none'}")
    run.measure("refused_count", len(refused))


def new_pids(run: Run) -> list[tuple]:
    """(step 4.1 round 2) the PIDs owned after the run that were not before (party and boxes), each with its OT id."""
    before = {row[0] for row in (run.before or {}).get("party_ot") or []} | {row[0] for row in (run.before or {}).get("boxes") or []}
    after = [(row[0], row[1], "party") for row in (run.after or {}).get("party_ot") or []] + \
            [(row[0], row[1], "box") for row in (run.after or {}).get("boxes") or []]
    return [entry for entry in after if entry[0] not in before]


def grade_CATCHS(run: Run) -> None:
    """(step 4.1 round 2, the verifier's weak proof: "The catch's sleep or paralysis move is never exercised live") A catch
    HELPED BY SLEEP (`brain/battle.py` _catch_status): the Skitty's SING chosen to catch a species it has not caught (by the
    game: gChosenMoveByBattler[0]), the foe ASLEEP by the game (gBattleMons[1].status1's sleep turns, the replay's every
    change) before the catch, and the catch by the truth (gBattleOutcome 7, one new PID with the player's OT)."""
    grade_common(run, walking=False)
    run.check(outcomes(run) == ["caught"] and (run.after or {}).get("battle_outcome") == 7,
              f"the battle ended CAUGHT: the AI's outcome {outcomes(run)}, gBattleOutcome {(run.after or {}).get('battle_outcome')} (7)")
    tid, new = (run.after or {}).get("player_tid"), new_pids(run)
    run.check(len(new) == 1 and new[0][1] == tid, f"ONE new PID owned by the player: {new} (the player's visible id {tid})")
    said = [line for line in battle_lines(run) if "fight Sing: to CATCH" in line]
    run.check(bool(said), f"the decider chose SING to help the catch: {[s.split('battle: ')[-1][:160] for s in said]}")
    game = check_replay(run)
    if game is not None:
        taken = [c["chosen"][0] for c in game.get("chosen") or [] if c["chosen"][0] != "-"]
        asleep = [s for s in game.get("statuses") or [] if s["battler"] == 1 and s["sleep"] > 0]
        caught_at = next((o["f"] for o in game.get("outcomes") or [] if o["value"] == 7), None)
        run.check("Sing" in taken and bool(asleep) and caught_at is not None and asleep[0]["f"] < caught_at,
                  f"BY THE GAME (the replay): the moves the game took {taken} include SING; the foe ASLEEP (status1 sleep turns) "
                  f"at f{asleep[0]['f'] if asleep else None} ({[(s['f'], s['species'], s['sleep']) for s in asleep][:3]}), "
                  f"before the catch (gBattleOutcome 7 at f{caught_at})")
        run.measure("sings", taken.count("Sing"))


def grade_CATCHSX(run: Run) -> None:
    """(step 4.1 round 2) FAULT of CATCHS: no status move to help a catch (step 4): no Sing; the foe never asleep by the game."""
    grade_common(run, walking=False)
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    said = [line for line in battle_lines(run) if "fight Sing" in line]
    run.check(not said, f"no Sing told: {said or 'none'}; the outcome {outcomes(run)}")
    game = check_replay(run)
    if game is not None:
        taken = [c["chosen"][0] for c in game.get("chosen") or [] if c["chosen"][0] != "-"]
        asleep = [s for s in game.get("statuses") or [] if s["battler"] == 1 and s["sleep"] > 0]
        run.check("Sing" not in taken and not asleep,
                  f"BY THE GAME (the replay): the moves taken {taken}, no Sing; the foe never asleep: {asleep or 'never'}")


def grade_SHIFT(run: Run) -> None:
    grade_common(run, walking=False)
    asked = [line for line in battle_lines(run) if "the question" in line and "change POK" in line]
    run.check(bool(asked) and "': YES" in asked[0] and "against Treecko" in asked[0]
              and "the words say TREECKO comes next" in asked[0],
              f"the shift question judged about the INCOMING Treecko its words named (x4 on the Marshtomp), answered YES: "
              f"{[a.split('battle: ')[-1][:300] for a in asked[:1]]}")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    run.check(bool(sent) and sent[0].split("who goes in: ")[-1].startswith("Taillow") and "decided at the question" in sent[0],
              f"the party menu got the member chosen AT THE QUESTION (not ranked again): {[s.split('who goes in: ')[-1][:200] for s in sent[:1]]}")
    run.check(outcomes(run) == ["won"] and trainer(run.before, MAY_RUSTBORO) is False and trainer(run.after, MAY_RUSTBORO) is True,
              f"the battle WON: {outcomes(run)}; MAY's flag ({MAY_RUSTBORO}) {trainer(run.before, MAY_RUSTBORO)} -> "
              f"{trainer(run.after, MAY_RUSTBORO)}")
    run.measure("sent", told_sent(run))
    game = check_replay(run)
    if game is not None:
        faint, foe, mine = game_after_foe_faint(game)
        run.check(faint is not None and faint["species"] == "Wingull" and foe is not None and foe["species"] == "Treecko"
                  and [e["pid"] for e in mine] == [TAILLOW_RUSTBORO],
                  f"BY THE GAME (the replay): the {faint and faint['species']} fainted at position 1, then "
                  f"{[(e['species'], e['pid']) for e in mine]} came onto position 0 BEFORE the {foe and foe['species']} came onto "
                  f"position 1: the Taillow ({TAILLOW_RUSTBORO}) the decider chose against the Treecko its words named")


def grade_SHIFTX(run: Run) -> None:
    grade_common(run, walking=False)
    asked = [line for line in battle_lines(run) if "the question" in line and "change POK" in line]
    run.check(bool(asked) and "': NO" in asked[0] and "FAULT shift_fainted" in asked[0] and "against Wingull" in asked[0],
              f"FAULT (step 4's answer): the question judged about the FAINTED Wingull, answered NO: "
              f"{[a.split('battle: ')[-1][:300] for a in asked[:1]]}")
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    game = check_replay(run)
    if game is not None:
        faint, foe, mine = game_after_foe_faint(game)
        run.check(faint is not None and faint["species"] == "Wingull" and foe is not None and foe["species"] == "Treecko"
                  and not mine,
                  f"BY THE GAME (the replay), FAULT: the {faint and faint['species']} fainted, the game sent out the "
                  f"{foe and foe['species']}, and nobody came onto position 0 between them: {mine}")


def grade_SHIFT_CARRY(run: Run, carried: bool) -> None:
    """(step 4.1 round 3, the verifier's weak proof: "Finding 1, the PID carried to the party menu, cannot fail live ... In
    this fixture the by-level fallback ... also picks the L17 Taillow") On `rival_rustboro_hurt.ss1` the Taillow is hurt so
    that a party menu ranking again by level sends the POOCHYENA: SHIFTC (the carry) must show the Taillow come in by the
    game, SHIFTCX (FAULT forget_shift: decided, not carried) the Poochyena."""
    grade_common(run, walking=False)
    want, other = (TAILLOW_RUSTBORO, POOCHYENA_RUSTBORO) if carried else (POOCHYENA_RUSTBORO, TAILLOW_RUSTBORO)
    asked = [line for line in battle_lines(run) if "the question" in line and "change POK" in line]
    run.check(bool(asked) and "': YES" in asked[0] and "against Treecko" in asked[0]
              and "the words say TREECKO comes next" in asked[0],
              f"the shift question judged about the INCOMING Treecko its words named, answered YES: "
              f"{[a.split('battle: ')[-1][:300] for a in asked[:1]]}")
    sent = [line for line in battle_lines(run) if "who goes in:" in line]
    if carried:
        run.check(bool(sent) and sent[0].split("who goes in: ")[-1].startswith("Taillow") and "decided at the question" in sent[0],
                  f"the party menu got the member chosen AT THE QUESTION: {[s.split('who goes in: ')[-1][:200] for s in sent[:1]]}")
    else:
        run.check(bool(sent) and sent[0].split("who goes in: ")[-1].startswith("Poochyena") and "by level" in sent[0],
                  f"FAULT forget_shift: the party menu ranked AGAIN, by level (no foe standing: the Wingull fainted), and named "
                  f"the Poochyena: {[s.split('who goes in: ')[-1][:200] for s in sent[:1]]}")
        run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    taillow = next((row for row in (run.before or {}).get("party") or [] if row[0] == "Taillow"), None)
    run.check(taillow is not None and taillow[1] * 2 >= taillow[2] and taillow[1] < taillow[2],
              f"THE FIXTURE (the truth before the run): the Taillow hurt but at half its HP or more {taillow}: the question "
              f"still finds it much better, and by level x HP share it is under the Poochyena (the build's printout)")
    run.measure("sent", told_sent(run))
    run.measure("outcomes", outcomes(run))
    game = check_replay(run)
    if game is not None:
        faint, foe, mine = game_after_foe_faint(game)
        run.check(faint is not None and foe is not None and foe["species"] == "Treecko" and [e["pid"] for e in mine] == [want],
                  f"BY THE GAME (the replay): the {faint and faint['species']} fainted at position 1, then "
                  f"{[(e['species'], e['pid']) for e in mine]} came onto position 0 BEFORE the {foe and foe['species']} came "
                  f"onto position 1: {want} ({'the Taillow, carried' if carried else 'the Poochyena, by level'}), never {other}")


def grade_SHIFTC(run: Run) -> None:
    grade_SHIFT_CARRY(run, carried=True)


def grade_SHIFTCX(run: Run) -> None:
    grade_SHIFT_CARRY(run, carried=False)


def grade_HEAL(run: Run) -> None:
    grade_common(run, walking=False)
    heals = [line for line in battle_lines(run) if re.search(r"turn \d+: item Potion", line)]
    run.check(bool(heals) and "is low" in heals[0], f"the decider healed in a trainer's battle with its Mudkip low: "
                                                    f"{[h.split('battle: ')[-1][:200] for h in heals]}")
    before = ((run.before or {}).get("items") or {}).get("POTION")
    after = ((run.after or {}).get("items") or {}).get("POTION")
    run.check(before is not None and after is not None and before - after == len(heals),
              f"BY THE TRUTH (the bag's items pocket, the probe's own decoder): POTION {before} -> {after} == the {len(heals)} told")
    run.check(outcomes(run) == ["won"] and trainer(run.after, MAY) is True,
              f"the battle WON: {outcomes(run)}; MAY's flag (529) {trainer(run.before, MAY)} -> {trainer(run.after, MAY)}")
    run.measure("heals", len(heals))
    game = check_replay(run)
    if game is not None:
        start_max = next((s["hp"][1] for s in game.get("start") or [] if s["battler"] == 0), None)
        rises = [e["hp"] for e in game.get("events") or [] if e["kind"] == "hp" and e["battler"] == 0
                 and e["hp"][1] > e["hp"][0] and e.get("max_hp") == start_max]
        run.check(len(rises) >= len(heals) >= 1, f"BY THE GAME (the replay): the Mudkip's HP ROSE at position 0 with its max HP "
                                                 f"unchanged (a Potion, not a level-up): {rises}")


def grade_SWITCH(run: Run) -> None:
    grade_common(run, walking=False)
    said = [line for line in battle_lines(run) if re.search(r"turn \d+: switch: Poochyena is badly matched against Machop", line)]
    run.check(len(said) == 1, f"a forced bad matchup: the decider SWITCHED (Fighting x2 on Dark): "
                              f"{[s.split('battle: ')[-1][:220] for s in said]}")
    run.check(outcomes(run) == ["won"] and trainer(run.after, JOEY) is True,
              f"the battle WON: {outcomes(run)}; Joey's flag (322) {trainer(run.before, JOEY)} -> {trainer(run.after, JOEY)}")
    game = check_replay(run)
    if game is not None:
        came = game_ins(game, 0)[1:2]
        fainted = any(e["kind"] == "hp" and e["battler"] == 0 and e["hp"][1] == 0 for e in game.get("events") or []
                      if came and e["f"] < came[0]["f"])
        run.check(bool(came) and came[0]["pid"] == MUDKIP and not fainted,
                  f"BY THE GAME (the replay): {[(e['species'], e['pid']) for e in came]} came onto position 0 with the Poochyena "
                  f"({POOCHYENA_116}) still standing (no HP 0 before it: a SWITCH, not a faint's send-in)")


def grade_RUN(run: Run) -> None:
    grade_common(run, walking=False)
    said = [line for line in battle_lines(run) if re.search(r"turn \d+: run: its Poochyena is low", line)]
    run.check(bool(said), f"training, the Poochyena low: the decider RAN: {[s.split('battle: ')[-1][:200] for s in said]}")
    run.check(outcomes(run) == ["ran"] and (run.after or {}).get("battle_outcome") == 4,
              f"BY THE TRUTH: gBattleOutcome {(run.after or {}).get('battle_outcome')} (4: ran); the AI's outcome {outcomes(run)}")
    game = check_replay(run)
    if game is not None:
        fainted = [e for e in game.get("events") or [] if e["kind"] == "hp" and e["battler"] == 0 and e["hp"][1] == 0]
        run.check(not fainted, f"BY THE GAME (the replay): the Poochyena never fell: {fainted}")
        # (step 4.1 round 2, the verifier: "the gBattleOutcome check never records the value before the run. The fixture's
        # start state already reads 4 ... valid only because BattleStartClearSetData sets gBattleOutcome = 0") the value on
        # the replay's first frame and every change after: the battle's own clear to 0, THEN 4, the last value
        seq = [game.get("outcome_start")] + [o["value"] for o in game.get("outcomes") or []]
        zeros = [i for i, v in enumerate(seq) if v == 0]
        stale = (run.before or {}).get("battle_outcome")
        # (step 4.1 round 3, the verifier: "three labels for two values") the sequence is the REPLAY's: its first value is
        # already the battle's own clear (that runs in the first frame); the stale 4 is the TRUTH's read of the fixture
        run.check(bool(zeros) and seq[-1] == 4 and zeros[-1] < len(seq) - 1,
                  f"BY THE GAME every frame (the replay's gBattleOutcome: its value on the first frame, then each change, with "
                  f"frames {[(o['f'], o['value']) for o in game.get('outcomes') or []]}): {seq}: 0 (the battle's own clear, "
                  f"`BattleStartClearSetData`, pret src/battle_main.c, already done in the replay's first frame), then 4 (ran), "
                  f"the last; the fixture BEFORE the run reads {stale} by the truth (a stale value from an earlier battle)")


def grade_OVERKILL(run: Run) -> None:
    grade_common(run, walking=False)
    first = [line for line in battle_lines(run) if re.search(r"turn \d+: fight ", line)][:1]
    run.check(bool(first) and "Take Down" in first[0] and "(finishes it" in first[0]
              and not re.search(r"turn \d+: fight Take Down:", first[0]),
              f"every damaging move FINISHES the Poochyena (told '(finishes it: worth as the strongest)'), so the choice is by "
              f"hit chance and recoil: not Take Down: {[f.split('battle: ')[-1][:260] for f in first]}")
    game = check_replay(run)
    if game is not None:
        chosen = game_first_choice(game)
        run.check(bool(chosen) and chosen != "Take Down", f"BY THE GAME (the replay): the Marshtomp's first move {chosen!r}")


def grade_OVERKILLX(run: Run) -> None:
    grade_common(run, walking=False)
    run.check((run.verdict or {}).get("verdict") == "CLEAN", "a FAULT switch is the AI's own rule: purity is still CLEAN")
    game = check_replay(run)
    if game is not None:
        chosen = game_first_choice(game)
        run.check(chosen == "Take Down", f"BY THE GAME (the replay), FAULT (step 4's valuation): the first move {chosen!r}")


GRADERS = {"WILD": grade_WILD, "CATCH": grade_CATCH, "TRAINER": grade_TRAINER, "RIVAL": grade_RIVAL,
           "CHALLENGE": grade_CHALLENGE, "TYPE": grade_TYPE, "TYPEX": grade_TYPEX, "FAINT": grade_FAINT, "LEARN": grade_LEARN,
           "DFAINT": grade_DFAINT, "DFAINTX": grade_DFAINTX, "REFUSE": grade_REFUSE,
           # (step 4.1)
           "SHIFT": grade_SHIFT, "SHIFTX": grade_SHIFTX, "HEAL": grade_HEAL, "SWITCH": grade_SWITCH, "RUN": grade_RUN,
           "OVERKILL": grade_OVERKILL, "OVERKILLX": grade_OVERKILLX,
           # (step 4.1 round 2)
           "REFUSED": grade_REFUSED, "REFUSEDX": grade_REFUSEDX, "CATCHS": grade_CATCHS, "CATCHSX": grade_CATCHSX,
           # (step 4.1 round 3)
           "SHIFTC": grade_SHIFTC, "SHIFTCX": grade_SHIFTCX}


# ---------------------------------------------------------------------- pre-registration
def check_predictions(run: Run) -> None:
    for name, want in PREDICTED.get(run.arm.name, {}).items():
        got = run.measures.get(name)
        held = got == want
        run.predictions.append((name, want, got, held))
        run.check(held, f"PRE-REGISTERED {name}: predicted {want}, measured {got}")


def md5_of(path: Path) -> str:
    import hashlib

    return hashlib.md5(path.read_bytes()).hexdigest()


def write_evidence(run: Run, code_ref: str, tag: str) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    fixture = FIXTURES[run.arm.fixture]
    env = " ".join(f"{k}={v}" for k, v in {ENV_BRAIN: "battle", ENV_SEED: str(run.arm.seed), **run.arm.env}.items())
    out = [
        f"AI PLAYER BUILD STEP 4 (BATTLES) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        f"fixture: {fixture[0].relative_to(REPO).as_posix()} md5={md5_of(fixture[0])}",
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command)}",
        f"env: {env}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        SELFTEST_LINE,
        "checks (pre-registered in ai_player/gates/live_step4.py's docstring and PREDICTED; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
        f"MEASURED: {json.dumps(run.measures, sort_keys=True, ensure_ascii=False, default=str)}",
    ]
    if run.notes:
        out += ["", "---- notes: the decider's told lines ----", *run.notes]
    if run.replay is not None:
        game = run.replay.get("game_battle") or {}
        out += ["", f"---- THE REPLAY in-process (hands_harness.py --battle-log): {run.replay.get('frames')} frames, "
                    f"{run.replay.get('presses')} presses, {run.replay.get('reason')!r}; the GAME's battle, read each frame "
                    f"(gBattleMons, gBattlerAttacker, gCurrentMove, gBattlerTarget, gChosenMoveByBattler) ----",
                f"at the start: {json.dumps(game.get('start'), ensure_ascii=False)}",
                *[json.dumps(e, ensure_ascii=False) for e in game.get("events") or []],
                *[f"chosen {json.dumps(c, ensure_ascii=False)}" for c in game.get("chosen") or []]]
    if run.verdict is not None:
        out += ["", "---- the instrument's verdict file (purity.json) ----", json.dumps(run.verdict, indent=2, sort_keys=True)]
    if run.before is not None:
        out += ["", "---- TRUTH of the fixture BEFORE the run (gates/hands_harness.py truth) ----", json.dumps(run.before, sort_keys=True, ensure_ascii=False)]
    if run.after is not None:
        out += ["", "---- TRUTH of the state the run LEFT (gates/hands_harness.py truth) ----", json.dumps(run.after, sort_keys=True, ensure_ascii=False)]
    if run.records:
        out += ["", f"---- the action log: {len(run.records)} records (frame | decision | action | gate or reason | digest) ----"]
        for r in run.records:
            if r.get("decision") in ("start", "end"):
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {r.get('reason')} | {r.get('digest')}")
            else:
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {str(r.get('reason'))[:220]} | "
                           f"{(r.get('digest') or '')[:200]}")
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]"))]
        out += ["", "---- evidence lines from stdout ([AI-*]) ----", *[line[:600] for line in keep]]
    keep_earlier(path)  # (step 4.1 round 3) an earlier tree's file is archived, not written over
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:  # noqa: BLE001
            continue
        if "pokebot.py" in cmd and PROFILE in cmd:
            found.append(f"{proc.info['pid']}: {cmd[:120]}")
    return found


def main() -> int:
    global SELFTEST_LINE
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 4 (battles).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    parser.add_argument("--evidence-tag", default=EVIDENCE_TAG)
    args = parser.parse_args()
    broken = selftest_after_check()
    SELFTEST_LINE = (f"[SELFTEST] check_after_is_this_run on 5 synthetic runs (its own: pass; a stale mtime, a frame +3000, no "
                     f"file, the fixture's md5: fail): {'PASS' if not broken else 'FAIL ' + str(broken)}")
    print(SELFTEST_LINE)
    if broken:
        return 2
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2
    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = tree_provenance(REPO)
    print(f"code: {code_ref}")
    results: list[Run] = []
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        run = run_arm(arm, build_root)
        if arm.name in REPLAYED:
            replay_arm(run)
        GRADERS[arm.name](run)
        check_predictions(run)
        evidence = write_evidence(run, code_ref, args.evidence_tag)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text[:400]}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<9} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    held = sum(1 for run in results for p in run.predictions if p[3])
    total = sum(len(run.predictions) for run in results)
    print(f"  PRE-REGISTERED NUMBERS: {held} of {total} held")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
