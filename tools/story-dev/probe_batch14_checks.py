r"""GATE G-B14 — design v2 step 14, T4: `batch14_checks.py` (E1-E5 + STOP-3) and `batch14_tables.py` (the tables).

WHY. Tonight's 13-hour batch is read for CORRECTNESS by these two files: a check that cannot fire reads a broken
package as clean, and a table that miscounts sends the descriptive reading the wrong way. The spec
(`ai-research-notes/2026-10-01-batch14-T4-PREDICTIONS.md`, "The gate") fixes the rows BEFORE the code: real line
shapes with a provenance check, one row per E rule in BOTH directions (a planted violation is reported, the clean case
reads PASS), STOP-3's yes and no, exact table counts on hand-built fixtures, and mutants with exact red sets. Every
expected value below was derived BY HAND from the fixture, never copied from the code's output.

ROWS (each a function; a row that raises is red)
  QS*   the real line shapes parse (`[MAP]`, the per-heal `[PC]` report, our side of `[TURN]`, `[BALLS-BUY]` /
        `[KIT-BUY]`, `[DEXFENCE]`, `[CATCH]` + ` rare=`, `[WEAKEN-OBS]`, a lane's `stdout.txt`).
  E1*-E5*  one rule each, both directions.      S3*  STOP-3: yes / no / the 200-line tail / the ACTING tags.
  T*    the tables on a hand-built 4-run fixture (`table_runs`), exact counts; the two labels; no verdict word.
  X*    the two CLIs end to end on batch directories (exit 0 / 1, NO CHECK / NO TABLE on a refused log, the M1b pool,
        E3 through the loader, the C1-C2 VOID header).
  R*    reuse: K* is compare_arms' by reference, the decomp ids, the loader's `visit` hook (one call per read log).
  TS*   KI-119 (`#27-gradeidentity`, `ai-research-notes/2026-10-02-gradeidentity-DESIGN.md`) on the REAL stale-boot run
        (L16 …-040658: a reset booted from a Hall-of-Fame save logs that save's 8 [BADGE] lines and party BEFORE the
        run's `Story: choosing X!` line): TS1 extract (badges from LEADER WINS, catch tags from each catch line's own
        badges=, the run POISONED), TS2 D-lead, TS3 PROGRESS before the start NOT read, TS4 CORRECTNESS before it STILL
        read, TS5 the [BADGE] CONTROL counts printed, TS6 D-funnel's badges from leader wins. QS4's [BADGE]-frame
        assertion moved to TS5 and T2's frame value / B maximum to TS6 (the design changed those values); T22's
        pre-Stone catch line now reads badges=0, as a real one does. Mutants K-SB1..K-SB16, TT1-TT6, MS1.
        THE INDEPENDENT REVIEW'S FOLD (`scratchpad/adv27/gihunt`, the coordinator's rulings): TS7-TS9 GS-5's badge
        controls (each catch line's badges= vs the leader wins, poisoned runs included; [BADGE] lines after the start
        compared in every run that has them; a run with no [TRAINER] telemetry but badge evidence reads 'unknown'), X7
        GS-6's choosing-line control in both headers, GK10-GK19 the mutant hunter's rows (GK14 quotes a REAL leader Draw
        from step 14). Mutants K-SB21..K-SB35, TT7-TT12 (the hunter's survivors are labelled [GH<n>]).

THE FOLD of the independent pass (`evidence/2026-10-01-batch14-T4-ADVERSARIAL.txt`, the coordinator's RULINGS 1-10):
  * the hunter's 24 killing rows are adopted (E1f E1g, E2c's production flag_off, E3c/d/g's added cases, E3h, E4a/c's
    added cases, E5a's listing, S3d's LITERAL, S3g, S3h, T17-T24, X5), and every survivor it listed is a mutant here
    under its own label in brackets, with the row that kills it;
  * one row per RULING with a REVERT mutant that reddens it: E4 on the qualifying first attempts (E4a E4b E4e), E5's
    context (E5b), STOP-3's acting tags (S3d-S3h, incl. the correction's why=mandatory / why=kit-none tails), the
    package ₽ row (T16, the REAL L10 joint errand), momentary map reads (E3i, T27), E2's fail-open tally (E2f), the
    headline caveats (E3j, X1), C1-C2 VOID (T15, X6), D-rare's comparable columns (T10), D-lead's label (T5);
  * the builder's 8 empty-set mutants: K40 T02 T07 T09 T23 are killed by rows; K51 and T04 turned out killable too
    (T26: a run cut inside a catch battle; T25: the cross-check fault-injected); only K48 stays EQUIVALENT (its reason
    is beside it). The fold's first run matched 136 of 141 sets; the 5 misses were my predictions (FOLD-PREDICTION).

THE LINES. Real lines are quoted VERBATIM (`QUOTES`) and the PROVENANCE check (not a row) re-reads each at its cited
line: the 16-lane smoke batch `x4-runs/20261001-090649` of the MAIN checkout (read-only; not committed — on a machine
without it those quotes are reported SKIPPED, never passed), committed evidence, the committed recon note, or (for the
two shapes no log has carried yet: `[CATCH] … end=lost` and `[CATCH] loss-filed`) the EMITTER's text in the sandbox
source. A `prefix` quote is the head of a long line (`[DMGAUDIT]`, `[WEAKEN-OBS]`, `[hb]`): the parsers read only it.
KI-119's stale-boot lines (source `stale`) are checked against the COMMITTED excerpt
`evidence/2026-10-02-gradeidentity-STALEBOOT.txt` always, and against step 14's raw batch log (20261001-210001, the MAIN
checkout) when it is here (else SKIPPED).

MUTANTS: source edits of `batch14_checks.py` / `batch14_tables.py` / `compare_arms.py`, exec'd in memory (never written
to disk), each with the EXACT set of rows it must turn red, written before its first run. COVERAGE fails if a row is
in no mutant's set. A process pool (`--serial` for one process).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_batch14_checks.py      (exit 1 on any failure; no ROM)
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import re
import sys
import tempfile
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # run_gates sets PYTHONUTF8=1 anyway
    pass

import audit_damage_calc  # noqa: E402,F401
import batch14_checks  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import batch14_tables  # noqa: E402,F401
import battle_log  # noqa: E402,F401
import compare_arms  # noqa: E402,F401
import x4_headless  # noqa: E402,F401

NAMES = {"ck": "batch14_checks", "tb": "batch14_tables", "ca": "compare_arms"}
PATHS = {k: HERE / f"{v}.py" for k, v in NAMES.items()}
#: The REAL compare_arms' frozen K*, captured once: R1 asserts identity against it (a `ca` mutant re-execs the module,
#: so the module in sys.modules then holds NEW tuples — comparing against it would redden R1 for the harness's sake).
_REAL_KSTAR = compare_arms.KSTAR


def CK():
    return sys.modules["batch14_checks"]


def TB():
    return sys.modules["batch14_tables"]


def CA():
    return sys.modules["compare_arms"]


def BL():
    return sys.modules["battle_log"]


ARMS_FILE = json.loads((HERE / "arms" / "batch14.json").read_text(encoding="utf-8"))
ARMS = ARMS_FILE["arms"]
MONITOR = ARMS_FILE["monitor"]
EVIDENCE = HERE / "evidence"
NOTES = REPO / "PROJECT KNOWLEDGE" / "ai-research-notes"
SANDBOX = REPO / "sandbox-pokebot"
SMOKE = None  # set in main(): the MAIN checkout's 16-lane smoke batch (read-only)
#: KI-119: the committed excerpt of step 14's stale-boot lines, and that batch in the MAIN checkout (set in main())
STALEBOOT = EVIDENCE / "2026-10-02-gradeidentity-STALEBOOT.txt"
BATCH14 = None
_L16S = "L16/Story_(ENDLESS_RESET)-debug-20261002-040658.log"   # arm B, a Hall-of-Fame boot (Torchic#759DE59A)

# ============================================================================================ the real lines
#: name -> (source, where, line number, text, mode). Sources: `smoke` (a lane's single debug log of the smoke batch),
#: `smoke-out` (its stdout.txt), `ev` (committed evidence), `note` (a committed research note, substring), `src` (the
#: emitter's text in the sandbox source, substring; no line number). Modes: `eq` byte for byte, `prefix` the line's
#: head, `sub` a substring of the line.
_L9, _DI = "L09", "2026-09-30-doubleitems13-ARMS.txt"
QUOTES = {
    "choose": ("smoke", _L9, 284, "f13047 [STEP] 'Story: choosing Torchic!'", "eq"),
    "hb": ("smoke", _L9, 297, "f14401 [hb] mode=Story (ENDLESS RESET) state=4 controllable=False map=ROUTE 101(0,16) pos=(6, 13) party=['Torchic:L5'] ids=['Torchic#C8E0A305:L5:exp135'] owned=1 balls=0 money=3000 box=0 badges=0", "prefix"),
    # a WILD battle (the rescue: no [TRAINER] line), with its [DMGAUDIT] block
    "w_started": ("smoke", _L9, 287, "f13263 [BATTLE] started hp=[('Torchic', 20, 20)]", "eq"),
    "w_fence": ("smoke", _L9, 288, "f13263 [DEXFENCE] skip #255 Torchic — no Pokédex yet rare=- tier=- note=no_data", "eq"),
    "w_ctl": ("smoke", _L9, 289, "f13263 [DMGAUDIT] CTL v=1", "eq"),
    "w_turn": ("smoke", _L9, 291, "f13724 [BATTLE] [TURN 0] Torchic L5 20/20 -> UseMove:Scratch(pp35)  vs Zigzagoon L2 13/13", "eq"),
    "w_before": ("smoke", _L9, 292, "f13737 [DMGAUDIT] BEFORE v=1 t=0 out=0 flags=00000014 act=0,0,255,255 mv=10,45,0,0 bide=0,0,0,0 weather=0 side=0,0 s3=00000000,00000000 dis=00000000000000000000000000000000000000000000010000000000,00000000000000000000000000000000000000000000010000000000 mons=18010c00090009000d000c000a002d0000000000cf2ebb2b0606060606060606420a0a00232800001400054614000000cec9ccbdc2c3bdff0b000000c2a2ffffffffffff8700000005a3e0c80000000000000000f906a9e1,20010600070006000600070021002d00000000006b54352d060606060606060635000000232800000d0002460d000000d4c3c1d4bbc1c9c9c8ff0000c2a2ffffffffffff08000000ce175b200000000000000000f906a9e1 ff=0,0 badges=0 pred=5,7,11,14 base=7,7 eff=HIT", "eq"),
    "w_after": ("smoke", _L9, 293, "f14217 [DMGAUDIT] AFTER v=1 kind=entry t=1 out=0 flags=00000014 act=255,255,255,255 mv=0,0,0,0 bide=0,6,0,0 weather=0 side=0,0 s3=00000000,00000000 dis=00000000000000000000000000000000000000000000000000000000,00000000000000000000000000000000000000000000000000000000 mons=18010c00090009000d000c000a002d0000000000cf2ebb2b0605060606060606420a0a00222800001400054614000000cec9ccbdc2c3bdff0b000000c2a2ffffffffffff8700000005a3e0c80000000000000000f906a9e1,20010600070006000600070021002d00000000006b54352d06060606060606063500000023270000070002460d000000d4c3c1d4bbc1c9c9c8ff0000c2a2ffffffffffff08000000ce175b200000000000000000f906a9e1 ff=0,0 party=205b17ce:7,00000000:0,00000000:0,00000000:0,00000000:0,00000000:0", "eq"),
    "w_ended": ("smoke", _L9, 301, "f15187 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Torchic:L5']", "eq"),
    "w_money": ("smoke", _L9, 302, "f15187 [MONEY] after Won at map (0, 16): money=₽3,000", "eq"),
    # the Route 103 rival (opp 535 = MAY_ROUTE_103_TORCHIC, class 0x32: KEY)
    "r_started": ("smoke", _L9, 842, "f64872 [BATTLE] started hp=[('Torchic', 30, 30)]", "eq"),
    "r_start": ("smoke", _L9, 843, "f64872 [TRAINER] start opp=535 class=0x32(PkMn_TRAINER) value=15 lvl_last=5 first=True base=300 double=False two=False money=3000 heal_stock=- map=0,18 enemy_alive=1", "eq"),
    "r_kb": ("smoke", _L9, 845, "f65445 [KEYBATTLE] opp=535 class=0x32 key=True allow=True reason=key_class", "eq"),
    "r_turn": ("smoke", _L9, 846, "f65445 [BATTLE] [TURN 0] Torchic L10 30/30 -> UseMove:Scratch(pp35)  vs Mudkip L5 20/20", "eq"),
    "r_ended": ("smoke", _L9, 854, "f67365 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Torchic:L10']", "eq"),
    "r_end": ("smoke", _L9, 857, "f67365 [TRAINER] end opp=535 class=0x32(PkMn_TRAINER) value=15 lvl_last=5 first=True base=300 res=Won money=3000->3300 delta=300 mult=1 heal_stock=- map=0,18", "eq"),
    "map_oldale": ("smoke", _L9, 975, "f76689 [MAP] ROUTE 101(0,16) -> OLDALE TOWN(0,10) pos=(9, -1)", "eq"),
    # a NON-KEY trainer (opp 318, YOUNGSTER)
    "n_started": ("smoke", _L9, 977, "f77542 [BATTLE] started hp=[('Torchic', 27, 30), ('Wurmple', 15, 15)]", "eq"),
    "n_start": ("smoke", _L9, 978, "f77542 [TRAINER] start opp=318 class=0x25(YOUNGSTER) value=4 lvl_last=5 first=True base=80 double=False two=False money=3300 heal_stock=- map=0,17 enemy_alive=1", "eq"),
    "n_kb": ("smoke", _L9, 980, "f78146 [KEYBATTLE] opp=318 class=0x25 key=False allow=False reason=not_a_key_class", "eq"),
    "n_turn": ("smoke", _L9, 981, "f78146 [BATTLE] [TURN 0] Torchic L10 27/30 -> UseMove:Ember(pp22)  vs Poochyena L5 18/18", "eq"),
    "n_ended": ("smoke", _L9, 983, "f79031 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Torchic:L10', 'Wurmple:L3']", "eq"),
    "n_money": ("smoke", _L9, 985, "f79031 [MONEY] after Won at map (0, 17): money=₽3,380", "eq"),
    "n_end": ("smoke", _L9, 986, "f79031 [TRAINER] end opp=318 class=0x25(YOUNGSTER) value=4 lvl_last=5 first=True base=80 res=Won money=3300->3380 delta=80 mult=1 heal_stock=- map=0,17", "eq"),
    "hb_money": ("smoke", _L9, 989, "f79201 [hb] mode=Story (ENDLESS RESET) state=7 controllable=True map=ROUTE 102(0,17) pos=(25, 13) party=['Torchic:L10', 'Wurmple:L3'] ids=['Torchic#C8E0A305:L10:exp726', 'Wurmple#5DF37700:L3:exp27'] owned=2 balls=4 money=3380 box=0 badges=0", "prefix"),
    "weaken_throw": ("smoke", _L9, 960, "f75394 [WEAKEN] [WEAKEN-OBS] would=THROW t=0 sp=Wurmple#265 pid=5DF37700 hp=15/15 st=0 tmv=33:35,81:40,-,- slot=- move=- ball=Poké_Ball reason=dmg:bound@0|st:no-status-move first=0", "prefix"),
    "oldale_in": ("smoke", _L9, 482, "f31032 [MAP] OLDALE TOWN(0,10) -> OLDALE TOWN(2,2) pos=(6, 16)", "eq"),
    "oldale_pc": ("smoke", _L9, 506, "f32227 [PC] Story: PC — none withdraw: SKIPPED — `_hunted_counter_pids` is empty. Normal when no counter was hunted; but if one WAS hunted, its registration upstream failed (the Slugma/Winona shape) and the counter is still sitting in the PC.", "eq"),
    "bb_mandatory": ("smoke", _L9, 1646, "f140110 [BALLS-BUY] why=mandatory mart=11,7 bought=30 spare=0->33 money=6824->824", "eq"),
    # the FIRST Pokémon Center heal in Rustboro and its errand (B, H9)
    "heal_in": ("smoke", _L9, 1840, "f159148 [MAP] RUSTBORO CITY(0,3) -> RUSTBORO CITY(11,5) pos=(16, 38)", "eq"),
    "heal_pc": ("smoke", _L9, 1865, "f160419 [PC] Story: PC — none withdraw: SKIPPED — `_hunted_counter_pids` is empty. Normal when no counter was hunted; but if one WAS hunted, its registration upstream failed (the Slugma/Winona shape) and the counter is still sitting in the PC.", "eq"),
    "heal_exit": ("smoke", _L9, 1866, "f160559 [MAP] RUSTBORO CITY(11,5) -> RUSTBORO CITY(0,3) pos=(7, 8)", "eq"),
    "heal_balls": ("smoke", _L9, 1867, "f160668 [BALLS] [BALLS-BUY] why=topoff-none mart=RustboroCity ball=Poké Ball bought=0 premier=0 spare=30->30 money=920->920 reason=before gym 1 (no kit, as no balls: the named RULING 26 gap)", "eq"),
    "heal_kit": ("smoke", _L9, 1868, "f160668 [BALLS] [KIT-BUY] why=kit-none mart=RustboroCity kit=[] bought=- money=920->920 wants=[('Super Potion', 4)] reason=before gym 1 (no kit, as no balls: the named RULING 26 gap)", "eq"),
    "heal_leave": ("smoke", _L9, 1869, "f161102 [MAP] RUSTBORO CITY(0,3) -> ROUTE 116(0,31) pos=(40, 9)", "eq"),
    # Roxanne (B, won)
    "x_started": ("smoke", _L9, 2118, "f195140 [BATTLE] started hp=[('Combusken', 48, 48), ('Silcoon', 24, 24), ('Poochyena', 21, 21), ('Whismur', 24, 24)]", "eq"),
    "x_start": ("smoke", _L9, 2119, "f195140 [TRAINER] start opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 double=False two=False money=1368 heal_stock=- map=11,3 enemy_alive=3", "eq"),
    "x_kb": ("smoke", _L9, 2121, "f195794 [KEYBATTLE] opp=265 class=0x20 key=True allow=True reason=key_class", "eq"),
    "x_turn": ("smoke", _L9, 2122, "f195794 [BATTLE] [TURN 0] Combusken L16 48/48 -> UseMove:Double Kick(pp26)  vs Geodude L12 33/33", "eq"),
    "x_ended": ("smoke", _L9, 2144, "f203335 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Combusken:L17', 'Silcoon:L7', 'Poochyena:L6', 'Whismur:L6']", "eq"),
    "x_end": ("smoke", _L9, 2147, "f203335 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Won money=1368->2868 delta=1500 mult=1 heal_stock=- map=11,3", "eq"),
    "badge": ("smoke", _L9, 2164, "f204181 [BADGE] n=1 party=4/6 box=0 owned=6 spare=30", "eq"),
    "fence_joins": ("smoke", _L9, 2242, "f211696 [DEXFENCE] CATCH #300 Skitty — dex catch #300 (joins the party) rare=rate tier=RARE note=-", "eq"),
    "catch_end": ("smoke", _L9, 2280, "f215016 [CATCH] end kind=dex sp=Skitty#300 end=caught res=Caught thrown=3 frames=3320 dest=party pid=8D0E1C63 party=5/6 box=0 spare=27 badges=1 bail=-", "eq"),
    "kit_bought": ("smoke", _L9, 2731, "f258683 [BALLS] [KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 2)] bought={'Super Potion': 2} money=4180->2780 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 2)] and 0 x Poké Ball (0 to the reserve + 0 after the kit); budget 1590, 190 left", "eq"),
    "fence_box": ("smoke", _L9, 2738, "f259465 [DEXFENCE] CATCH #63 Abra — dex catch #63 (goes to the PC box) rare=variant tier=ULTRA note=-", "eq"),
    "trainee": ("smoke", _L9, 2740, "f259465 [CATCH] trainee lead=Poochyena#DFF79C1B (a dex catch during swap-training)", "eq"),
    "catch_start": ("smoke", _L9, 2741, "f259465 [CATCH] start kind=dex sp=Abra#63 lv=7 attempt=2 badges=1 party=6/6 box=0 spare=24 exp_throws=3.1 map=0,31 rare=variant tier=ULTRA note=-", "eq"),
    "trainee_after": ("smoke", _L9, 2759, "f261265 [CATCH] trainee-after lead=Poochyena#DFF79C1B before=Poochyena#DFF79C1B same=True", "eq"),
    "weaken_damage": ("smoke", _L9, 2787, "f265433 [WEAKEN] [WEAKEN-OBS] would=DAMAGE t=0 sp=Taillow#276 pid=FC3C11D5 hp=22/22 st=0 tmv=64:35,45:40,116:30,- slot=0 move=Tackle ball=- reason=stage2:HIT first=1", "prefix"),
    "bb_topoff": ("smoke", _L9, 2975, "f280748 [BALLS] [BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=2 premier=0 spare=20->22 money=2080->1680 exit=16,39 back=16,39 facing=Down reason=kit none and 2 x Poké Ball (0 to the reserve + 2 after the kit); budget 540, 140 left", "eq"),
    "out_start": ("smoke-out", _L9, 4, "=== ENDLESS RESET: starting run 1/infinite ===", "eq"),
    # the line's head and its path BELOW the repo root (`probe_no_hardcoded_repo` H1: no code literal names the main
    # checkout); `out_log` rebuilds it on THIS tree's root
    "out_log_head": ("smoke-out", _L9, 7, "Story (DEBUG - RESET): debug logging ON -> ", "prefix"),
    "out_log_tail": ("smoke-out", _L9, 7, r"\sandbox-pokebot\profiles\endless-s14smoke-H9-torchic\debug-logs\Story_(ENDLESS_RESET)-debug-20261001-090657.log", "sub"),
    "nobail": ("smoke", "L12", 3757, "f377204 [DEXCATCH] [DEXCATCH-NOBAIL] a team member fainted — sending the next Pokémon and throwing on (fainted=1)", "eq"),
    "fence_reserve": ("smoke", "L13", 2209, "f224575 [DEXFENCE] skip #276 Taillow — only 2 spare balls — below the dex reserve of 10 rare=- tier=- note=-", "eq"),
    "runway": ("smoke", "L01", 2563, "f249862 [DEXFENCE] skip #63 Abra — party is 4/6 — a catch would consume the HM/counter runway", "eq"),
    # A (H7, Treecko): Roxanne LOST, with A's item use in it
    "a_started": ("smoke", "L07", 3963, "f453155 [BATTLE] started hp=[('Nincada', 33, 33), ('Treecko', 35, 35), ('Zigzagoon', 19, 19), ('Whismur', 25, 25)]", "eq"),
    "a_start": ("smoke", "L07", 3964, "f453155 [TRAINER] start opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 double=False two=False money=1368 heal_stock=Potion:2,Super_Potion:2,Full_Heal:1 map=11,3 enemy_alive=3", "eq"),
    "a_using": ("smoke", "L07", 3979, "f456670 [BATTLE] [ITEM] using Super Potion on Nincada 9/33 (use 1, worst hit 9)", "eq"),
    "a_ended": ("smoke", "L07", 4166, "f480710 [BATTLE] ended (outcome=BattleOutcome.Lost) party=['Nincada:L13', 'Treecko:L15', 'Zigzagoon:L5', 'Whismur:L6']", "eq"),
    "a_end": ("smoke", "L07", 4169, "f480710 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Lost money=1368->1368 delta=0 mult=0 heal_stock=Full_Heal:1 map=11,3", "eq"),
    # step 13 (committed): Tate & Liza (B, double, Potion:1 held) and a double battle with a [DBLITEM] use
    "tl_started": ("ev", _DI, 253, "f3452776 [BATTLE] started hp=[('Sceptile', 130, 130), ('Zigzagoon', 40, 40), ('Swellow', 112, 112), ('Skitty', 45, 45), ('Mightyena', 127, 127), ('Castform', 103, 103)]", "eq"),
    "tl_start": ("ev", _DI, 254, "f3452776 [TRAINER] start opp=271 class=0x20(LEADER) value=25 lvl_last=42 first=True base=8400 double=True two=False money=37654 heal_stock=Potion:1,Full_Heal:1 map=14,0 enemy_alive=4", "eq"),
    "tl_turn0": ("ev", _DI, 255, "f3453544 [BATTLE] [TURN 0] Sceptile L47 130/130 -> UseMove:Leaf Blade(pp9)  vs Claydol L41 112/112", "eq"),
    "tl_turn1": ("ev", _DI, 260, "f3456183 [BATTLE] [TURN 1] Mightyena L43 99/127 -> UseMove:Bite(pp25)  vs Claydol L41 22/112", "eq"),
    "tl_turn4": ("ev", _DI, 267, "f3462572 [BATTLE] [TURN 4] Sceptile L48 46/133 -> UseMoveAgainstRightSideOpponent:Strength(pp8)  vs ?", "eq"),
    "tl_ended": ("ev", _DI, 270, "f3464107 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Sceptile:L48', 'Zigzagoon:L15', 'Swellow:L40', 'Skitty:L17', 'Mightyena:L44', 'Castform:L36']", "eq"),
    "tl_end": ("ev", _DI, 271, "f3464107 [TRAINER] end opp=271 class=0x20(LEADER) value=25 lvl_last=42 first=True base=8400 res=Won money=37654->46054 delta=8400 mult=1 heal_stock=Potion:1,Full_Heal:1 map=14,0", "eq"),
    "d_started": ("ev", _DI, 117, "f3148510 [BATTLE] started hp=[('Mightyena', 0, 124), ('Sceptile', 21, 117), ('Swellow', 18, 109), ('Skitty', 0, 45), ('Zigzagoon', 16, 16), ('Castform', 0, 100)]", "eq"),
    "d_start": ("ev", _DI, 118, "f3148510 [TRAINER] start opp=106+13 class=0x0E(HEX_MANIAC)+0x07(COLLECTOR) value=6+15 lvl_last=30+30 first=True+True base=2520 double=True two=True money=14804 heal_stock=Hyper_Potion:1 map=0,38 enemy_alive=4", "eq"),
    "d_using": ("ev", _DI, 119, "f3149372 [BATTLE] [ITEM] using Hyper Potion on Sceptile 21/117 (use 1, worst hit 0)", "eq"),
    "d_use": ("ev", _DI, 120, "f3149372 [DBLITEM] use side=0 g=0 item=Hyper Potion target=Sceptile#863B0917 P=1 hp=21/117 self=1", "eq"),
    "d_turn": ("ev", _DI, 121, "f3149372 [BATTLE] [TURN 0] Sceptile L42 21/117 -> UseItem  vs Duskull L30 52/52", "eq"),
    "d_menu": ("ev", _DI, 129, "f3149596 [DBLITEM] menu g=0 battler_in_menu=0 layout=1 slot=0 menu_pid=863B0917 intended_pid=863B0917 ok=1 a_pressed=1 aim=0 self=1", "eq"),
    "d_after": ("ev", _DI, 132, "f3149839 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->117 status1=0->0 partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1 same=1", "eq"),
    "d_turn_p": ("ev", _DI, 133, "f3149862 [BATTLE] [TURN 0] Swellow L39 18/109 -> UseMove:Wing Attack(pp24)  vs Duskull L30 52/52", "eq"),
    "d_ended": ("ev", _DI, 114, "f3155931 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Mightyena:L42', 'Sceptile:L43', 'Swellow:L40', 'Skitty:L17', 'Zigzagoon:L3', 'Castform:L35']", "eq"),
    "d_end": ("ev", _DI, 115, "f3155931 [TRAINER] end opp=106+13 class=0x0E(HEX_MANIAC)+0x07(COLLECTOR) value=6+15 lvl_last=30+30 first=True+True base=2520 res=Won money=14804->17324 delta=2520 mult=1 heal_stock=Hyper_Potion:1 map=0,38", "eq"),
    "d_obs": ("ev", _DI, 100, "f3150994 [DBLITEM-OBS] side=1 g=2 turn=1 me=Swellow#0B30A747 P=2 hp=18/109 would=Hyper_Potion why=hp key=0 worst=0 uses=0 bpo=120345 bpo_pos=1 disc=1 cur=00000000", "eq"),
    "failopen": ("ev", "2026-09-29-r27keyitems-A-RAISE.txt", 49, "f3173266 [KEYBATTLE] opp=? class=? key=? allow=True reason=FAIL_OPEN(RuntimeError)", "eq"),
    "derail": ("ev", "2026-09-27-batch0926-P1r8-evgpcwedge.txt", 148, "f6046772 [STORY] DERAIL #1: Ch23 (Victory Road) failed after 3 attempts. attempt 1: ", "prefix"),
    "map_vr": ("ev", "2026-09-27-batch0926-P1r8-evgpcwedge.txt", 84, "f6034921 [MAP] VICTORY ROAD(24,43) -> EVER GRANDE CITY(0,8) pos=(2, 15)", "eq"),
    "leg11_new": ("ev", "2026-09-27-restock-RS3-poor-fix-final.stdout.txt", 31, "Ch23 leg 11: the missing basket lines [('Hyper Potion', 4), ('Full Restore', 2), ('Revive', 1)] cost ₽12,300 (the full basket is ₽54,300) but we hold ₽1,741 — short by ₽10,559", "sub"),
    "leg11_old": ("note", "2026-10-01-batch14-recon/b14_recon_expectations.md", 31, "Ch23 leg 11: the basket costs ₽54,300 but we hold", "sub"),
    # ---- added with the fold of the independent pass (`evidence/2026-10-01-batch14-T4-ADVERSARIAL.txt`)
    # the Skitty catch battle as it really CLOSES (Caught), and the Abra one (OpponentTeleported, `end=foe_fled`)
    "skitty_started": ("smoke", _L9, 2241, "f211696 [BATTLE] started hp=[('Combusken', 52, 52), ('Silcoon', 24, 24), ('Poochyena', 21, 21), ('Whismur', 24, 24)]", "eq"),
    "skitty_start": ("smoke", _L9, 2244, "f211696 [CATCH] start kind=dex sp=Skitty#300 lv=7 attempt=1 badges=1 party=4/6 box=0 spare=30 exp_throws=3.0 map=0,31 rare=rate tier=RARE note=-", "eq"),
    "caught_ended": ("smoke", _L9, 2278, "f215016 [BATTLE] ended (outcome=BattleOutcome.Caught) party=['Combusken:L18', 'Silcoon:L7', 'Poochyena:L6', 'Whismur:L6', 'Skitty:L7']", "eq"),
    "teleported": ("smoke", _L9, 2753, "f260876 [BATTLE] ended (outcome=BattleOutcome.OpponentTeleported) party=['Poochyena:L6', 'Silcoon:L8', 'Combusken:L19', 'Whismur:L6', 'Skitty:L7', 'Nincada:L6']", "eq"),
    "fled_end": ("smoke", _L9, 2756, "f260876 [CATCH] end kind=dex sp=Abra#63 end=foe_fled res=OpponentTeleported thrown=1 frames=1411 dest=none pid=- party=6/6 box=0 spare=23 badges=1 bail=-", "eq"),
    # a BUYING errand enters the mart and logs its lines on the way back (the hunter's KE3-mart)
    "mart_in": ("smoke", _L9, 2852, "f271059 [MAP] RUSTBORO CITY(0,3) -> RUSTBORO CITY(11,7) pos=(16, 45)", "eq"),
    "mart_out": ("smoke", _L9, 2883, "f272108 [MAP] RUSTBORO CITY(11,7) -> RUSTBORO CITY(0,3) pos=(3, 7)", "eq"),
    # ONE errand that bought balls AND kit: both lines share the frame and money=a->b (RULING 4, the recompute's F1)
    "joint_balls": ("smoke", "L10", 2484, "f267952 [BALLS] [BALLS-BUY] why=topoff mart=11,7 ball=Poké Ball bought=12 premier=1 spare=2->15 money=10180->5680 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 3)] and 12 x Poké Ball (9 to the reserve + 3 after the kit); budget 4590, 90 left", "eq"),
    "joint_kit": ("smoke", "L10", 2485, "f267952 [BALLS] [KIT-BUY] why=kit mart=11,7 kit=[('Super Potion', 3)] bought={'Super Potion': 3} money=10180->5680 exit=16,39 back=16,39 facing=Down reason=kit [('Super Potion', 3)] and 12 x Poké Ball (9 to the reserve + 3 after the kit); budget 4590, 90 left", "eq"),
    # RULING 5's momentary reads: a (255,255) pair one frame apart, and a (3,0) read
    "tr255_in": ("smoke", _L9, 1673, "f141715 [MAP] ROUTE 116(0,31) -> ROUTE 116(255,255) pos=(11, 7)", "eq"),
    "tr255_out": ("smoke", _L9, 1674, "f141716 [MAP] ROUTE 116(255,255) -> ROUTE 116(0,31) pos=(11, 7)", "eq"),
    "tr30": ("smoke", "L01", 1835, "f162619 [MAP] ROUTE 116(0,31) -> ROUTE 116(3,0) pos=(11, 7)", "eq"),
    # the emitters of the two shapes no log has carried yet (story_mode.py: on_battle_ended's C4 block, _r20_catch_end)
    "src_lossfiled": ("src", "plugins/custom_modes/story_mode.py", None, 'f"loss-filed kind={_c4_kind} map={key} catch_losses={counts[key]} "', "sub"),
    "src_endlost": ("src", "plugins/custom_modes/story_mode.py", None, 'elif nm == "Lost":\n            end = "lost"', "sub"),
    "src_runend": ("src", "plugins/custom_modes/story_mode.py", None, 'f"[cyan]=== ENDLESS RESET: run {label} -> {outcome} ({frames:,} frames) ===[/]"', "sub"),
    # flag_off's PRODUCTION shape is allow=True (key_battle_verdict returns (True, "flag_off")) — the hunter's F15
    "src_flagoff": ("src", "modules/story/trainer_identity.py", None, 'return True, "flag_off"', "sub"),
    # the acting errand outcomes RULING 3 counts, at their emitters (stock_topoff.py)
    "src_topoff_closed": ("src", "modules/story/stock_topoff.py", None, '_emit(log_line("topoff-closed",', "sub"),
    "src_topoff_recovery": ("src", "modules/story/stock_topoff.py", None, '_emit(log_line("topoff-recovery",', "sub"),
    "src_kit_closed": ("src", "modules/story/stock_topoff.py", None, '_emit(kit_log_line("kit-closed",', "sub"),
    "src_kit_recovery": ("src", "modules/story/stock_topoff.py", None, '_emit(kit_log_line("kit-recovery",', "sub"),
    # ---- KI-119 (`#27-gradeidentity`): the REAL stale-boot run L16 …-040658 (arm B; source `stale`: the committed
    # excerpt, and the raw log of step 14's batch when it is here). A Hall-of-Fame boot logs the SAVED game first.
    **{f"s16_b{n}": ("stale", _L16S, 30 + n, f"f301 [BADGE] n={n} party=6/6 box=11 owned=25 spare=24", "eq")
       for n in range(1, 9)},
    "s16_newgame": ("stale", _L16S, 39, 'f377 [STEP] "Intro: New Game + Professor Birch\'s welcome speech..."', "eq"),
    "s16_hold": ("stale", _L16S, 63, "f2808 [STEP] 'Intro: holding 97f before confirming (RNG decorrelation)...'", "eq"),
    "s16_hb_stale": ("stale", _L16S, 83, "f3601 [hb] mode=Story (ENDLESS RESET) state=10 controllable=False map=LITTLEROOT TOWN(16,11) pos=(7, 5) party=['Swellow:L65', 'Azumarill:L67', 'Skitty:L65', 'Sceptile:L65', 'Linoone:L66', 'Mightyena:L65'] ids=['Swellow#ED2C8CFD:L65:exp282113', 'Azumarill#D4DDD3B3:L67:exp241077', 'Skitty#0CB56F6D:L65:exp222768', 'Sceptile#274110E3:L65:exp285725', 'Linoone#71068797:L66:exp287893', 'Mightyena#5F4049F0:L65:exp282375'] owned=25 balls=25 money=35923 box=11 badges=8 msg='Intro: confirming the name and riding to Littleroot...'", "eq"),
    "s16_clear": ("stale", _L16S, 86, "f3882 [PARTY] size 6 -> 0: []", "eq"),
    "s16_choose": ("stale", _L16S, 298, "f13123 [STEP] 'Story: choosing Torchic!'", "eq"),
    "s16_hb": ("stale", _L16S, 311, "f14401 [hb] mode=Story (ENDLESS RESET) state=4 controllable=False map=ROUTE 101(0,16) pos=(6, 13) party=['Torchic:L5'] ids=['Torchic#759DE59A:L5:exp135'] owned=1 balls=0 money=3000 box=0 badges=8 msg='Received Torchic ♂.\\n\\nNature:\\xa0Brave | Ability:\\xa0Blaze | Item:\\xa0- | IV\\xa0sum:\\xa085 | SV:\\xa033,599'", "eq"),
    "s16_catch_pooch": ("stale", _L16S, 879, "f67594 [CATCH] end kind=team sp=Poochyena#261 end=caught res=Caught thrown=1 frames=1702 dest=party pid=9FF2BE0D party=2/6 box=0 spare=4 badges=0 bail=-", "eq"),
    "s16_roxanne": ("stale", _L16S, 1890, "f184413 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Won money=7368->8868 delta=1500 mult=1 heal_stock=- map=11,3", "eq"),
    "s16_catch_abra": ("stale", _L16S, 2398, "f234542 [CATCH] end kind=dex sp=Abra#63 end=caught res=Caught thrown=1 frames=1632 dest=party pid=CFF60025 party=5/6 box=0 spare=14 badges=1 bail=-", "eq"),
    # the review's fold (GK14): a REAL leader DRAW from step 14 (that run never beat Tate & Liza afterwards)
    "s13_tl_draw": ("stale", "L13/Story_(ENDLESS_RESET)-debug-20261002-043756.log", 31085, "f3814604 [TRAINER] end opp=271 class=0x20(LEADER) value=25 lvl_last=42 first=True base=8400 res=Draw money=2->2 delta=0 mult=0 heal_stock=- map=14,0", "eq"),
}
_STALE_ROW = re.compile(r"^(L\d+/\S+?\.log):(\d+): (.*)$")


def stale_excerpt() -> dict:
    """The committed excerpt: (`<lane>/<log>`, line number) -> the line."""
    out = {}
    for row in STALEBOOT.read_text(encoding="utf-8").splitlines():
        m = _STALE_ROW.match(row)
        if m:
            out[(m.group(1), int(m.group(2)))] = m.group(3)
    return out


def Q(name: str) -> str:
    return QUOTES[name][3]


def provenance() -> None:
    """Every quote is at its cited line (smoke / evidence / note) or in its emitter's source."""
    bad, skipped = [], []
    cache: dict = {}

    def lines_of(src, where):
        key = (src, where)
        if key not in cache:
            if src == "smoke":
                logs = sorted((SMOKE / where / "debug-logs").glob("*.log")) if SMOKE else []
                cache[key] = (logs[0].read_text(encoding="utf-8", errors="replace").splitlines()
                              if len(logs) == 1 else None)
            elif src == "smoke-out":
                p = SMOKE / where / "stdout.txt" if SMOKE else None
                cache[key] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                              if p and p.is_file() else None)
            elif src == "ev":
                cache[key] = (EVIDENCE / where).read_text(encoding="utf-8", errors="replace").splitlines()
            elif src == "note":
                cache[key] = (NOTES / where).read_text(encoding="utf-8", errors="replace").splitlines()
            else:
                cache[key] = (SANDBOX / where).read_text(encoding="utf-8", errors="replace")
        return cache[key]

    excerpt, raw, raw_skipped = stale_excerpt(), {}, []
    for name, (src, where, n, text, mode) in QUOTES.items():
        if src == "stale":
            # KI-119: the committed excerpt ALWAYS; the raw log when step 14's batch is on this machine
            if excerpt.get((where, n)) != text:
                bad.append(f"{name} (excerpt {where}:{n})")
            if where not in raw:
                p = BATCH14 / where.split("/")[0] / "debug-logs" / where.split("/", 1)[1] if BATCH14 else None
                raw[where] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                              if p is not None and p.is_file() else None)
            if raw[where] is None:
                raw_skipped.append(name)
            elif raw[where][n - 1] != text:
                bad.append(f"{name} (raw {where}:{n})")
            continue
        got = lines_of(src, where)
        if got is None:
            skipped.append(name)
            continue
        if src == "src":
            ok = text in got
        else:
            line = got[n - 1] if 0 < n <= len(got) else ""
            ok = (line == text if mode == "eq" else line.startswith(text) if mode == "prefix" else text in line)
        if not ok:
            bad.append(f"{name} ({src}:{where}:{n})")
    check("PROVENANCE every quoted line is at its cited line / in its emitter", not bad,
          f"{len(QUOTES) - len(skipped)} checked, mismatches {bad}"
          + (f"; SKIPPED (no smoke batch here) {skipped}" if skipped else "")
          + (f"; stale-boot quotes vs the RAW batch log SKIPPED (step 14's batch is not here; the committed excerpt "
             f"was checked) {raw_skipped}" if raw_skipped else ""))


# ============================================================================================ helpers
FAILURES: list = []
ROWS: list = []
ROW_NAMES: set = set()
TMP: dict = {}


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def row(rid: str, label: str):
    def deco(fn):
        ROWS.append((rid, label, fn))
        ROW_NAMES.add(rid)
        return fn
    return deco


def eq(got, want):
    return got == want, f"got {got!r}" + ("" if got == want else f" (want {want!r})")


def env_line(env: dict) -> str:
    """The run header's `env-all:` line exactly as `debug_logger` writes it."""
    return f"    {'env-all:':<14} {dict(sorted(env.items()))}"


def header(arm) -> list:
    return ["=== DEBUG LOG START 2026-10-01T21:00:00 ===", "--- RUN HEADER (build, config, experiment) ---",
            "    build:         1f3872ac7a85 on branch main", env_line(ARMS[arm]), "--- END RUN HEADER ---"]


def B(*names) -> list:
    return [Q(n) for n in names]


def no_rare(line: str) -> str:
    """The line as arm A prints it: A has no ` rare=… tier=… note=…` suffix (`_r25_log_suffix` is OFF there)."""
    return line.split(" rare=")[0]


def wild_a() -> list:
    """The WILD block as arm A prints it."""
    return [no_rare(line) for line in B(*WILD)]


def for_a(lines) -> list:
    """Lines as arm A prints them: no `[KEYBATTLE]` (KEYITEMS is OFF in A, so the gate never runs) and no ` rare=`."""
    return [no_rare(line) for line in lines if "[KEYBATTLE]" not in line]


WILD = ("w_started", "w_fence", "w_ctl", "w_turn", "w_before", "w_after", "w_ended", "w_money")
NONKEY = ("n_started", "n_start", "n_kb", "n_turn", "n_ended", "n_money", "n_end")
RIVAL = ("r_started", "r_start", "r_kb", "r_turn", "r_ended", "r_end")
ROX_WON = ("x_started", "x_start", "x_kb", "x_turn", "x_ended", "x_end")
ROX_LOST = ("a_started", "a_start", "a_using", "a_ended", "a_end")
TL = ("tl_started", "tl_start", "tl_turn0", "tl_turn1", "tl_turn4", "tl_ended", "tl_end")
DOUBLE = ("d_started", "d_start", "d_using", "d_use", "d_turn", "d_menu", "d_after", "d_turn_p", "d_ended", "d_end")
HEAL = ("heal_in", "heal_pc", "heal_exit", "heal_balls", "heal_kit", "heal_leave")
_SEQ = [0]


def lines_of(arm, body) -> list:
    return header(arm) + B("choose", "hb") + list(body) + ["=== DEBUG LOG END ==="]


def rec(arm, body, *, lane="H1", log=None, cut=False, lost=False, m1b=None) -> dict:
    """ONE run, exactly as `batch14_checks.load`'s visit builds it: compare_arms' record + `extract` on the same
    lines (the lane arm's monitor `forbid`)."""
    _SEQ[0] += 1
    log = log or f"r{_SEQ[0]}-debug-20261001-210000.log"
    lines = lines_of(arm, body)
    r = CA().run_record(lines, log=log, lane={"tag": lane, "slot": 0, "arm": arm}, arms=ARMS, cut=cut, lost=lost)
    r["t4"] = CK().extract(lines, forbid=MONITOR[arm]["forbid"], m1b=m1b)
    return r


#: KI-119 (`#27-gradeidentity`): the REAL stale-boot run's lines before its choosing line, in log order — the SAVED
#: game's 8 [BADGE] lines, the New Game step, the run's hold, the champion's [hb] (money=35923), the party clear
STALE_PRE = tuple(f"s16_b{n}" for n in range(1, 9)) + ("s16_newgame", "s16_hold", "s16_hb_stale", "s16_clear")


def stale_lines(arm="B", pre=(), mid=(), body=()) -> list:
    """KI-119's REAL stale-boot run (L16 …-040658): a header for `arm`, the boot-loaded save's lines (`STALE_PRE`),
    `pre` (planted BEFORE the choosing line), the choosing line, `mid`, the run's first [hb], then `body`."""
    return (header(arm) + B(*STALE_PRE) + list(pre) + [Q("s16_choose")] + list(mid) + [Q("s16_hb")] + list(body)
            + ["=== DEBUG LOG END ==="])


def rec_lines(arm, lines, *, lane="H16", m1b=None) -> dict:
    """ONE run from EXPLICIT lines (the stale fixtures), built exactly as `rec` builds one."""
    _SEQ[0] += 1
    r = CA().run_record(lines, log=f"s{_SEQ[0]}-debug-20261002-040658.log",
                        lane={"tag": lane, "slot": 15, "arm": arm}, arms=ARMS)
    r["t4"] = CK().extract(lines, forbid=MONITOR[arm]["forbid"], m1b=m1b)
    return r


def sub(line: str, old: str, new: str) -> str:
    if old not in line:
        raise AssertionError(f"fixture edit: {old!r} not in {line[:80]!r}")
    return line.replace(old, new)


def lost_dex_end() -> str:
    """`[CATCH] end … end=lost` in the emitter's shape (`src_endlost`): the real dex end with its outcome Lost."""
    return sub(Q("catch_end"), "end=caught res=Caught", "end=lost res=Lost")


def loss_filed() -> str:
    """`[CATCH] loss-filed kind=dex …` in the emitter's shape (`src_lossfiled`)."""
    return "f215016 [CATCH] loss-filed kind=dex map=(0, 31) catch_losses=1 defeats=0"


def run_end(n, outcome, frames=412004) -> str:
    """A stdout run-end line in the emitter's shape (`src_runend`; rich strips the markup)."""
    return f"=== ENDLESS RESET: run {n}/infinite -> {outcome} ({frames:,} frames) ==="


def out_log(log: str) -> str:
    """The real `debug logging ON -> <profile path>` stdout line, on this tree's root, naming `log`."""
    return (Q("out_log_head") + str(REPO)
            + Q("out_log_tail").replace("Story_(ENDLESS_RESET)-debug-20261001-090657.log", log))


def stdout_text(runs) -> str:
    """A lane's stdout: per run (log basename, outcome or None for a run still open)."""
    out = []
    for i, (log, outcome) in enumerate(runs, 1):
        out.append(Q("out_start").replace("run 1/", f"run {i}/"))
        out.append(out_log(log))
        if outcome:
            out.append(run_end(i, outcome))
    return "\n".join(out) + "\n"


def E(n, runs, *extra):
    return getattr(CK(), f"check_e{n}")(runs, *extra)


# ============================================================================================ QS — real line shapes
@row("QS1", "[MAP]: the first numeric pair, ' -> ', the next (the label may lag its ids); a heal marker is the per-heal "
            "[PC] withdraw report, never its 'withdraw result' line")
def _qs1():
    ck = CK()
    msg = lambda q: ck._CAT.match(Q(q)).group(3)  # noqa: E731
    return eq((ck.parse_map(msg("heal_exit")), ck.parse_map(msg("map_vr")), bool(ck._HEAL_MARK.match(msg("heal_pc"))),
               bool(ck._HEAL_MARK.match("Story: PC — counter withdraw result: landed"))),
              (((11, 5), (0, 3)), ((24, 43), (0, 8)), True, False))


@row("QS2", "our side of [TURN]: name and hp/max; a '?' own side never borrows the FOE's numbers")
def _qs2():
    ck = CK()
    got = [ck._TURN_ME.search(Q(q)).group(2, 4, 5) for q in ("w_turn", "tl_turn4", "d_turn")]
    unread = ck._TURN_ME.search("f1 [BATTLE] [TURN 3] ? -> UseMove:Tackle(pp30)  vs Zigzagoon L2 13/13")
    return eq((got, unread), ([("Torchic", "20", "20"), ("Sceptile", "46", "133"), ("Sceptile", "21", "117")], None))


@row("QS3", "[BALLS-BUY] (both prefixes) and [KIT-BUY]: why, ball, bought, ₽ spent; the kit's item dict")
def _qs3():
    b = CK()._buy
    return eq([b(Q("bb_mandatory"), False), b(Q("bb_topoff"), False, frame=280748), b(Q("heal_balls"), False),
               b(Q("kit_bought"), True), b(Q("heal_kit"), True)],
              [{"why": "mandatory", "spent": 6000, "frame": None, "money": ("6824", "824"), "ball": "-", "bought": 30},
               {"why": "topoff", "spent": 400, "frame": 280748, "money": ("2080", "1680"), "ball": "Poké Ball",
                "bought": 2},
               {"why": "topoff-none", "spent": 0, "frame": None, "money": ("920", "920"), "ball": "Poké Ball",
                "bought": 0},
               {"why": "kit", "spent": 1400, "frame": None, "money": ("4180", "2780"), "items": {"Super Potion": 2}},
               {"why": "kit-none", "spent": 0, "frame": None, "money": ("920", "920"), "items": {}}])


@row("QS4", "one run's extraction on real lines: [DEXFENCE] pairs (numbers stripped, suffix dropped), [CATCH] + rare=, "
            "[WEAKEN-OBS] stage, the trainee / NOBAIL counts (the [BADGE] line's reading is TS5's since KI-119)")
def _qs4():
    # KI-119 (`#27-gradeidentity`): the [BADGE] line is a CONTROL now (badges are leader wins), so its frame moved to
    # TS5's assertions; the line stays in the fixture
    t = rec("B", B("w_started", "w_fence", "w_turn", "w_ended", "fence_reserve", "badge", "trainee", "catch_start",
                   "trainee_after", "weaken_damage", "weaken_throw", "nobail"))["t4"]
    return eq((sorted(t["fence"]), t["rare"], dict(t["weaken"]), (t["trainee"], t["trainee_after"], t["nobail"])),
              ([("before", "skip", "#255 Torchic", "no Pokédex yet"),
                ("before", "skip", "#276 Taillow", "only N spare balls — below the dex reserve of N")],
               [["Abra", 63, "variant", 0, "?"]], {("DAMAGE", "stage2"): 1, ("THROW", "-"): 1}, (1, 1, 1)))


@row("QS5", "a lane's stdout.txt: each run end -> its outcome bucket, signature (x4_headless._derail_reason) and the "
            "log it opened (the last 'debug logging ON' before it); a run still open has no end")
def _qs5():
    txt = stdout_text([("a.log", "derailed: Tate & Liza: 27 losses with no super-effective answer"),
                       ("b.log", "finished"), ("c.log", None)])
    got = CK().parse_stdout(txt)
    return eq([(r["run"], r["bucket"], r["signature"], r["log"]) for r in got],
              [(1, "derailed", x4_headless._derail_reason("derailed: Tate & Liza: 27 losses with no super-effective "
                                                          "answer"), "a.log"), (2, "finished", None, "b.log")])


# ============================================================================================ E1
@row("E1a", "E1: a B NON-KEY battle with [ITEM] using -> FINDING listing the line; the same battle clean -> PASS")
def _e1a():
    bad = E(1, [rec("B", B(*NONKEY[:4], "a_using", *NONKEY[4:]))])
    good = E(1, [rec("B", B(*NONKEY))])
    return eq((bad["status"], len(bad["violations"]), "[ITEM] using Super Potion" in bad["violations"][0],
               good["status"], good["nonkey_b"]), ("FINDING", 1, True, "PASS", 1))


@row("E1b", "E1: a fail-open [KEYBATTLE] (FAIL_OPEN(…) or fail_open_*) EXEMPTS the battle, listed; not_a_key_class does not")
def _e1b():
    fo = E(1, [rec("B", B("n_started", "n_start", "failopen", "n_turn", "a_using", "n_ended", "n_end"))])
    fo2 = E(1, [rec("B", [Q("n_started"), Q("n_start"), sub(Q("n_kb"), "reason=not_a_key_class",
                                                            "reason=fail_open_unreadable"), Q("a_using"), Q("n_ended"),
                          Q("n_end")])])
    nk = E(1, [rec("B", B("n_started", "n_start", "n_kb", "a_using", "n_ended", "n_end"))])
    return eq((fo["status"], len(fo["exempt"]), fo2["status"], len(fo2["exempt"]), nk["status"], len(nk["exempt"])),
              ("PASS", 1, "PASS", 1, "FINDING", 0))


@row("E1c", "E1: a WILD battle with an item -> FINDING in arm A too; A's items in KEY and NON-KEY battles -> PASS. "
            "(WILD needs the log's [TRAINER] telemetry — battle_log's rule — so each log fights the rival first.)")
def _e1c():
    wild = E(1, [rec("A", B(*RIVAL, "w_started", "w_turn", "a_using", "w_ended"))])
    a_ok = E(1, [rec("A", B(*ROX_LOST, *NONKEY[:4], "a_using", *NONKEY[4:]))])
    return eq((wild["status"], wild["wild"], a_ok["status"]), ("FINDING", 1, "PASS"))


@row("E1d", "E1: a [DBLITEM] use in a B NON-KEY battle -> FINDING (the real double battle is NON-KEY: Hex Maniac + "
            "Collector); the [ITEM] using there is a second violating line")
def _e1d():
    r = E(1, [rec("B", B(*DOUBLE))])
    return eq((r["status"], len(r["violations"]), sum("[DBLITEM] use" in v for v in r["violations"])),
              ("FINDING", 2, 1))


@row("E1e", "E1: an UNCLASSIFIED battle (a '?' side) is not judged: PASS, and listed as not judged")
def _e1e():
    r = E(1, [rec("B", [Q("n_started"), sub(Q("n_start"), "class=0x25(YOUNGSTER)", "class=0x25(YOUNGSTER)+?"),
                        Q("a_using"), Q("n_ended"), Q("n_end")])])
    return eq((r["status"], sum("not judged" in d for d in r["detail"])), ("PASS", 1))


@row("E1f", "E1 (the hunter's KE1-key): a B KEY battle (Roxanne, its real key=True line) with [ITEM] using is NOT a "
            "violation — the package is SUPPOSED to use items there")
def _e1f():
    r = E(1, [rec("B", B("x_started", "x_start", "x_kb", "a_using", "x_turn", "x_ended", "x_end"))])
    return eq((r["status"], r["violations"]), ("PASS", []))


@row("E1g", "E1 (the hunter's KE1-bwild): an item in a B WILD battle is a violation in arm B too")
def _e1g():
    r = E(1, [rec("B", B(*RIVAL, "w_started", "w_turn", "a_using", "w_ended"))])
    return eq((r["status"], r["wild"], [v.split(" ", 2)[:2] for v in r["violations"]]), ("FINDING", 1, [["B", "WILD"]]))


# ============================================================================================ E2
@row("E2a", "E2: two [KEYBATTLE] lines in one battle -> FINDING; one -> PASS")
def _e2a():
    two = E(2, [rec("B", B("n_started", "n_start", "n_kb", "n_kb", "n_turn", "n_ended", "n_end"))])
    one = E(2, [rec("B", B(*NONKEY))])
    return eq((two["status"], len(two["violations"]), one["status"]), ("FINDING", 1, "PASS"))


@row("E2b", "E2: key=False on a battle the offline class calls KEY -> FINDING; key=True on a NON-KEY -> FINDING; the "
            "real lines -> PASS")
def _e2b():
    k = E(2, [rec("B", [Q("r_started"), Q("r_start"), sub(Q("r_kb"), "key=True", "key=False"), Q("r_turn"),
                        Q("r_ended"), Q("r_end")])])
    n = E(2, [rec("B", [Q("n_started"), Q("n_start"), sub(Q("n_kb"), "key=False", "key=True"), Q("n_turn"),
                        Q("n_ended"), Q("n_end")])])
    real = E(2, [rec("B", B(*RIVAL, *NONKEY))])
    return eq((k["status"], n["status"], real["status"], real["lines"]), ("FINDING", "FINDING", "PASS", 2))


@row("E2c", "E2: reason=flag_off is a violation even when key= agrees — in its PRODUCTION shape allow=True "
            "(`src_flagoff`: key_battle_verdict returns (True, 'flag_off')), the hunter's F15")
def _e2c():
    r = E(2, [rec("B", [Q("n_started"), Q("n_start"),
                        sub(Q("n_kb"), "allow=False reason=not_a_key_class", "allow=True reason=flag_off"),
                        Q("n_turn"), Q("n_ended"), Q("n_end")])])
    return eq((r["status"], len(r["violations"])), ("FINDING", 1))


@row("E2f", "RULING 6: a fail-open [KEYBATTLE] (key=False reason=fail_open_unreadable) on a battle the offline class "
            "calls KEY is TALLIED, not compared: PASS, tallied {'key=False': 1}")
def _e2f():
    line = sub(Q("r_kb"), "key=True allow=True reason=key_class", "key=False allow=True reason=fail_open_unreadable")
    r = E(2, [rec("B", [Q("r_started"), Q("r_start"), line, Q("r_turn"), Q("r_ended"), Q("r_end")])])
    return eq((r["status"], r["fail_open_keys"], r["violations"]), ("PASS", {"key=False": 1}, []))


@row("E2d", "E2: a trainer battle with NO [KEYBATTLE] is counted by offline class (a summary, PASS); the real "
            "FAIL_OPEN(RuntimeError) key=? line is tallied; an UNCLASSIFIED battle is not comparable; a B run with no "
            "trainer battle is NOT ASSESSED")
def _e2d():
    miss = E(2, [rec("B", B("n_started", "n_start", "n_turn", "n_ended", "n_end", *RIVAL))])
    fo = E(2, [rec("B", B("r_started", "r_start", "failopen", "r_turn", "r_ended", "r_end"))])
    unc = E(2, [rec("B", [Q("n_started"), sub(Q("n_start"), "class=0x25(YOUNGSTER)", "class=0x25(YOUNGSTER)+?"),
                          Q("n_kb"), Q("n_ended"), Q("n_end")])])
    none = E(2, [rec("B", B(*WILD))])
    return eq((miss["status"], miss["missing"], fo["status"], fo["fail_open_keys"], unc["status"],
               "not comparable (key=? or UNCLASSIFIED) 1" in unc["detail"][0], none["status"]),
              ("PASS", {"NON-KEY": 1}, "PASS", {"key=?": 1}, "PASS", True, "NOT ASSESSED"))


@row("E2e", "E2 reads arm B only: a doubled [KEYBATTLE] in an A run is not E2's (A's leak is E3's)")
def _e2e():
    r = E(2, [rec("A", B("n_started", "n_start", "n_kb", "n_kb", "n_turn", "n_ended", "n_end"))])
    return eq((r["status"], r["lines"]), ("NOT ASSESSED", 0))


# ============================================================================================ E3
@row("E3a", "E3: an A run printing a B-only text ([KIT-BUY]) -> FINDING; a B run printing an A-only text (the runway "
            "refusal) -> FINDING; each arm's own texts -> PASS")
def _e3a():
    a_bad = E(3, [rec("A", B("heal_kit"))], MONITOR)
    b_bad = E(3, [rec("B", B("runway"))], MONITOR)
    ok = E(3, [rec("A", B("runway")), rec("B", B("heal_kit", "r_kb"))], MONITOR)
    return eq((a_bad["status"], len(a_bad["findings"]), b_bad["status"], ok["status"]),
              ("FINDING", 1, "FINDING", "PASS"))


@row("E3b", "E3: a LIST monitor entry needs EVERY string on ONE line ('dex catch #' + '(joins the party)'), as the live "
            "monitor matches")
def _e3b():
    both = E(3, [rec("A", [Q("fence_joins").split(" rare=")[0]])], MONITOR)
    one = E(3, [rec("A", [Q("fence_box").split(" rare=")[0]])], MONITOR)
    split = E(3, [rec("A", ["f1 [DEXFENCE] skip — dex catch #300", "f1 [DEXFENCE] skip — (joins the party)"])], MONITOR)
    return eq((both["status"], one["status"], split["status"]), ("FINDING", "PASS", "PASS"))


@row("E3c", "E3: a B dex catch LOST with no [CATCH] loss-filed kind=dex after it -> FINDING; with one -> PASS; a "
            "loss-filed BEFORE the end does not count; a lost TEAM catch needs none")
def _e3c():
    w = [Q("w_started"), Q("catch_start"), Q("w_turn")]
    missing = E(3, [rec("B", w + [lost_dex_end(), Q("w_ended")])], MONITOR)
    filed = E(3, [rec("B", w + [lost_dex_end(), Q("w_ended"), loss_filed()])], MONITOR)
    before = E(3, [rec("B", w + [loss_filed(), lost_dex_end(), Q("w_ended")])], MONITOR)
    team = E(3, [rec("B", w + [sub(lost_dex_end(), "kind=dex", "kind=team"), Q("w_ended")])], MONITOR)
    orphan = "loss-filed lines with no lost end before them 1" in "\n".join(before["detail"])
    # the hunter's KE3-caught (a CAUGHT dex end needs no filing) and KE3-twolost (two losses, one filing: one miss)
    caught = E(3, [rec("B", [Q("skitty_started"), Q("skitty_start"), Q("w_turn"), Q("caught_ended"),
                             Q("catch_end")])], MONITOR)
    lost_battle = w + [lost_dex_end(), sub(Q("w_ended"), "Won", "Lost")]
    two = E(3, [rec("B", lost_battle + lost_battle + [loss_filed()])], MONITOR)
    return eq((missing["status"], missing["loss_missed"], filed["status"], before["status"], orphan, team["status"],
               caught["status"], caught["loss_missed"], two["status"], two["loss_missed"]),
              ("FINDING", 1, "PASS", "FINDING", True, "PASS", "PASS", 0, "FINDING", 1))


@row("E3d", "E3: B's FIRST Rustboro heal (the real errand) -> PASS; without its [KIT-BUY] -> FINDING; its lines after "
            "leaving Rustboro -> FINDING; a heal outside Rustboro is not that heal")
def _e3d():
    ok = E(3, [rec("B", B(*HEAL))], MONITOR)
    nokit = E(3, [rec("B", B("heal_in", "heal_pc", "heal_exit", "heal_balls", "heal_leave"))], MONITOR)
    late = E(3, [rec("B", B("heal_in", "heal_pc", "heal_exit", "heal_leave", "heal_balls", "heal_kit"))], MONITOR)
    oldale = E(3, [rec("B", B("oldale_in", "oldale_pc", "heal_balls", "heal_kit"))], MONITOR)
    # the hunter's KE3-mart: a BUYING errand enters the mart (real L09 lines) and logs both lines on the way back
    mart = E(3, [rec("B", B("heal_in", "heal_pc", "heal_exit", "mart_in", "mart_out", "heal_balls", "heal_kit",
                            "heal_leave"))], MONITOR)
    return eq((ok["status"], ok["rustboro_healed"], nokit["status"], late["status"], oldale["status"],
               oldale["rustboro_healed"], mart["status"], mart["rustboro_healed"], mart["rustboro_missed"]),
              ("PASS", 1, "FINDING", "FINDING", "PASS", 0, "PASS", 1, 0))


@row("E3e", "E3: only the FIRST Rustboro heal is judged: a silent first heal and a logging second heal -> FINDING; a "
            "logging first heal and a silent second -> PASS")
def _e3e():
    silent = ["heal_in", "heal_pc", "heal_exit", "heal_leave"]
    first_silent = E(3, [rec("B", B(*silent, *HEAL))], MONITOR)
    second_silent = E(3, [rec("B", B(*HEAL, *silent))], MONITOR)
    return eq((first_silent["status"], second_silent["status"]), ("FINDING", "PASS"))


@row("E3g", "E3: a CUT run whose log ENDS inside the first Rustboro errand is censored (not judged, PASS); the same "
            "run COMPLETE -> FINDING; a cut run whose errand window had CLOSED -> FINDING")
def _e3g():
    open_end = ("heal_in", "heal_pc", "heal_exit")
    cut = E(3, [rec("B", B(*open_end), cut=True)], MONITOR)
    complete = E(3, [rec("B", B(*open_end))], MONITOR)
    closed = E(3, [rec("B", B(*open_end, "heal_leave"), cut=True)], MONITOR)
    lost = E(3, [rec("B", B(*open_end), lost=True)], MONITOR)          # the hunter's KE3-lostcens: LOST is censored too
    return eq((cut["status"], cut["rustboro_healed"], "censored inside that errand" in "\n".join(cut["detail"]),
               complete["status"], closed["status"], lost["status"], lost["rustboro_healed"]),
              ("PASS", 0, True, "FINDING", "FINDING", "PASS", 0))


@row("E3h", "E3 (the hunter's KE3-counter): a first Rustboro heal whose withdraw source is 'counter' "
            "(higher_level_actions.py:714-730) IS the first heal: silent there, logging at the second -> FINDING")
def _e3h():
    counter_pc = sub(Q("heal_pc"), "PC — none withdraw:", "PC — counter withdraw:")
    r = E(3, [rec("B", [Q("heal_in"), counter_pc, Q("heal_exit"), Q("heal_leave")] + B(*HEAL))], MONITOR)
    return eq((r["status"], r["rustboro_healed"], r["rustboro_missed"]), ("FINDING", 1, 1))


def _rb_read(line_q: str, frm: str, to: str, frame: str) -> str:
    """A [MAP] read in the real shape of `line_q`, re-pointed (ids) and re-timed (frame) for RULING 5's rows."""
    pos = Q(line_q).split(" pos=", 1)[1]
    return f"f{frame} [MAP] RUSTBORO CITY{frm} -> RUSTBORO CITY{to} pos={pos}"


@row("E3i", "RULING 5: inside the first Rustboro errand a (255,255) read and its return, a (3,0) read, or a read that "
            "REVERTS to its origin within 2 frames do NOT close the window (PASS); a read reverting after 3 frames does "
            "(FINDING)")
def _e3i():
    def heal(extra):
        return E(3, [rec("B", B("heal_in", "heal_pc", "heal_exit") + extra + B("heal_balls", "heal_kit",
                                                                               "heal_leave"))], MONITOR)
    p255 = heal([_rb_read("tr255_in", "(0,3)", "(255,255)", "160600"),
                 _rb_read("tr255_out", "(255,255)", "(0,3)", "160601")])
    p30 = heal([_rb_read("tr30", "(0,3)", "(3,0)", "160600"), _rb_read("tr255_out", "(3,0)", "(0,3)", "160650")])
    rev2 = heal([_rb_read("tr30", "(0,3)", "(28,0)", "160600"), _rb_read("tr30", "(28,0)", "(0,3)", "160602")])
    rev3 = heal([_rb_read("tr30", "(0,3)", "(28,0)", "160600"), _rb_read("tr30", "(28,0)", "(0,3)", "160603")])
    return eq((p255["status"], p30["status"], rev2["status"], rev3["status"]), ("PASS", "PASS", "PASS", "FINDING"))


@row("E3j", "RULING 7: E3's HEADLINE names its untried halves — 'PASS (loss-filing half had 0 trials; Rustboro half NOT "
            "ASSESSED)' — and a tried half drops out of it")
def _e3j():
    bare = E(3, [rec("B", B(*NONKEY))], MONITOR)
    tried = E(3, [rec("B", B(*HEAL, "w_started", "catch_start", "w_turn") + [lost_dex_end(), Q("w_ended"),
                                                                              loss_filed()])], MONITOR)
    return eq((CK().headline(bare), CK().headline(tried)),
              ("PASS (loss-filing half had 0 trials; Rustboro half NOT ASSESSED)", "PASS"))


@row("E3f", "E3: [CATCH] trainee (trainee-after apart) and [DEXCATCH-NOBAIL] are COUNTS per arm, never a finding in B")
def _e3f():
    r = E(3, [rec("B", B("trainee", "trainee_after", "trainee", "nobail"))], MONITOR)
    return eq((r["status"], r["counts"]["B"]), ("PASS", {"trainee": 2, "trainee_after": 1, "nobail": 1}))


# ============================================================================================ E4
def _tl_runs(n, arm="B", body=TL):
    return [rec(arm, B(*body), lane=f"H{i}") for i in range(n)]


_TL_USE = ("tl_started", "tl_start", "tl_turn0", "d_use", "tl_turn1", "tl_turn4", "tl_ended", "tl_end")
_TL_CALM = ("tl_started", "tl_start", "tl_turn0", "tl_turn1", "tl_ended", "tl_end")


@row("E4a", "RULING 1: 4 qualifying B runs -> NOT ASSESSED; 5 with 0 uses in those first attempts -> FINDING (READ BY "
            "HAND), PER BATTLER: Sceptile 46/133 (.35) 'yes' with the rule-3 caveat, Mightyena 99/127 'no' — and the "
            "listing is of the T&L FIRST attempt even when the run fought on (the hunter's KE4-index)")
def _e4a():
    four = E(4, _tl_runs(4))
    five = E(4, [rec("B", B(*TL, "w_started", "w_turn", "w_ended"), lane=f"H{i}") for i in range(5)])
    yes = [d for d in five["detail"][1:] if "Sceptile lowest 46/133 (0.35); HP item held: yes (1); at or below 0.35: "
           "yes — production may decline under its rule 3 (a losing race) — read the battle" in d]
    no = [d for d in five["detail"][1:] if "Mightyena lowest 99/127 (0.78)" in d and d.endswith("at or below 0.35: no")]
    return eq((four["status"], four["qualifying"], five["status"], len(yes), len(no), five["reached"]),
              ("NOT ASSESSED", 4, "FINDING (READ BY HAND)", 5, 5, 5))


@row("E4b", "RULING 1: a [DBLITEM] use INSIDE a qualifying T&L first attempt -> PASS; one in an unrelated double (the "
            "recompute's V2) or in a T&L RE-attempt (V3) does not: still FINDING, with the global count printed beside")
def _e4b():
    ok = E(4, _tl_runs(4) + [rec("B", B(*_TL_USE), lane="H9")])
    v2 = E(4, _tl_runs(4) + [rec("B", B(*TL, *DOUBLE), lane="H9")])
    lost_first = [sub(Q(n), "outcome=BattleOutcome.Won", "outcome=BattleOutcome.Lost") if n == "tl_ended"
                  else sub(Q(n), "res=Won", "res=Lost") if n == "tl_end" else Q(n) for n in TL]
    v3 = E(4, _tl_runs(4) + [rec("B", lost_first + B(*_TL_USE), lane="H9")])
    return eq((ok["status"], ok["uses"], v2["status"], v2["uses"], v2["uses_all"], v3["status"], v3["uses"],
               v3["uses_all"]), ("PASS", 1, "FINDING (READ BY HAND)", 0, 1, "FINDING (READ BY HAND)", 0, 1))


@row("E4e", "RULING 1: a zero where NO battler reached .35 (the recompute's V4) reads 'ZERO EXPLAINED BY THE 0.35 "
            "THRESHOLD (0 of 5 reached it with an HP item)'; a battle with NO own-HP read keeps it FINDING (READ BY HAND)")
def _e4e():
    calm = E(4, _tl_runs(5, body=_TL_CALM))
    blind = E(4, _tl_runs(4, body=_TL_CALM) + [rec("B", B("tl_started", "tl_start", "tl_ended", "tl_end"), lane="H9")])
    return eq((calm["status"], sum(d.endswith("at or below 0.35: no") for d in calm["detail"]), blind["status"],
               blind["unread"]),
              ("ZERO EXPLAINED BY THE 0.35 THRESHOLD (0 of 5 reached it with an HP item)", 10,
               "FINDING (READ BY HAND)", 1))


@row("E4c", "E4's denominator: a first attempt with NO HP item (Full_Heal only) does not qualify; only the FIRST "
            "attempt counts; A runs never count; an UNREADABLE bag never qualifies (KE4-unread); 4 runs that each tried "
            "T&L twice are 4, not 8 (KE4-distinct)")
def _e4c():
    noitem = [Q(n) if n != "tl_start" else sub(Q(n), "heal_stock=Potion:1,Full_Heal:1", "heal_stock=Full_Heal:1")
              for n in TL]
    edits = {"tl_start": [("heal_stock=Potion:1,Full_Heal:1", "heal_stock=-")],
             "tl_ended": [("outcome=BattleOutcome.Won", "outcome=BattleOutcome.Lost")],
             "tl_end": [("res=Won", "res=Lost"), ("heal_stock=Potion:1,Full_Heal:1", "heal_stock=-")]}
    lost_first = []
    for n in TL:
        line = Q(n)
        for old, new in edits.get(n, ()):
            line = sub(line, old, new)
        lost_first.append(line)
    a = E(4, [rec("B", noitem, lane=f"H{i}") for i in range(5)])
    b = E(4, [rec("B", lost_first + B(*TL), lane=f"H{i}") for i in range(5)])
    c = E(4, _tl_runs(5, arm="A"))
    unread = [sub(Q(n), " heal_stock=Potion:1,Full_Heal:1 map=14,0 enemy", " map=14,0 enemy") if n == "tl_start"
              else Q(n) for n in TL]
    d = E(4, [rec("B", unread, lane=f"H{i}") for i in range(5)])
    twice = [sub(Q(n), "outcome=BattleOutcome.Won", "outcome=BattleOutcome.Lost") if n == "tl_ended"
             else sub(Q(n), "res=Won", "res=Lost") if n == "tl_end" else Q(n) for n in TL]
    e = E(4, [rec("B", twice + B(*TL), lane=f"H{i}") for i in range(4)])
    return eq((a["status"], a["qualifying"], b["qualifying"], c["status"], c["qualifying"], d["qualifying"],
               e["status"], e["qualifying"]), ("NOT ASSESSED", 0, 0, "NOT ASSESSED", 0, 0, "NOT ASSESSED", 4))


# ============================================================================================ E5
def _rise(line: str) -> str:
    return sub(line, "partner=Swellow#0B30A747 hp=18->18", "partner=Swellow#0B30A747 hp=18->109")


#: g=2's `use` in the real `use` shape (`d_use`), aimed at its own Swellow
_USE_P = "f3149862 [DBLITEM] use side=0 g=2 item=Hyper Potion target=Swellow#0B30A747 P=2 hp=18/109 self=1"


@row("E5a", "E5: the real `after` (partner 18->18) lists nothing (PASS); a planted partner rise is READ BY HAND (1 "
            "listed, never a FINDING) and the LISTING carries the battle, its turn and both HP readings (KE5-list); no "
            "`after` at all is NOT ASSESSED")
def _e5a():
    real = E(5, [rec("B", B(*DOUBLE))])
    rise = E(5, [rec("B", [Q(n) if n != "d_after" else _rise(Q(n)) for n in DOUBLE])])
    none = E(5, [rec("B", B(*NONKEY))])
    hit = [d for d in rise["detail"][1:] if "battle #0 turn 0 g=0" in d and "target Sceptile#863B0917 (21, 117)" in d
           and "partner Swellow#0B30A747 (18, 109)" in d]
    return eq((real["status"], real["afters"], rise["status"], rise["listed"], len(hit), none["status"]),
              ("PASS", 1, "READ BY HAND", 1, 1, "NOT ASSESSED"))


def _e5_body(second_turn: str) -> list:
    """The REAL order (evidence ARMS.txt:119-133; the spec reviewer's F2): g=0 heals ITSELF and logs its `after`, THEN
    g=2 decides — here g=2's Hyper Potion, aimed at Swellow, lands on Sceptile, g=2's PARTNER (its `after` shows the
    partner rising). `second_turn` is the [TURN] word of g=2's decision."""
    after2 = ("f3150100 [DBLITEM] after g=2 target=Swellow#0B30A747 hp=18->18 status1=0->0 partner=Sceptile#863B0917 "
              "hp=117->160 Hyper Potion=1->0 healed=1->2 same=1")
    head = [Q(n) for n in DOUBLE[:DOUBLE.index("d_after") + 1]]           # up to and including g=0's own `after`
    return head + [_USE_P, sub(sub(Q("d_turn_p"), "UseMove:Wing Attack(pp24)", "UseItem"), "[TURN 0]", second_turn),
                   after2, Q("d_ended"), Q("d_end")]


@row("E5b", "RULING 2: a partner rise is ALWAYS listed — a same-turn use on the partner (g=0 healed Sceptile itself) "
            "is printed as CONTEXT, never an exclusion; on another turn it is listed with no context")
def _e5b():
    same = E(5, [rec("B", _e5_body("[TURN 0]"))])
    other = E(5, [rec("B", _e5_body("[TURN 1]"))])
    ctx = [d for d in same["detail"][1:] if "[context: a same-turn [DBLITEM] use by g=0 targeted the partner]" in d]
    return eq((same["listed"], len(ctx), other["listed"], sum("[context:" in d for d in other["detail"])),
              (1, 1, 1, 0))


@row("E5c", "E5 reads arm B only: a partner rise in an A run is not listed")
def _e5c():
    r = E(5, [rec("A", [Q(n) if n != "d_after" else _rise(Q(n)) for n in DOUBLE])])
    return eq((r["status"], r["listed"]), ("NOT ASSESSED", 0))


# ============================================================================================ STOP-3
FILL = "map_oldale"


def _s3(lanes) -> dict:
    """lanes = [(lane, arm, [(log, outcome, tail body)])] -> STOP-3's result (records + stdout built alike)."""
    runs, stdout = [], {}
    for lane, arm, items in lanes:
        for log, _outcome, body in items:
            if body is not None:
                runs.append(rec(arm, body, lane=lane, log=log))
        stdout[lane] = {"arm": arm, "runs": CK().parse_stdout(stdout_text([(log, o) for log, o, _b in items]))}
    return CK().stop3(runs, stdout)


def _tagged(fill=0, acting="a_using"):
    """A derail tail: the rival (its `[KEYBATTLE]` is allow=True: NOT acting), then ONE acting line, then `fill`
    fillers — the acting line is `fill + 1`-th from the log's end."""
    return B(*RIVAL) + [Q(acting)] + [Q(FILL)] * fill


#: RULING 3's acting tags, as a LITERAL (the hunter's F1: a row comparing the module's tuple with itself can never fail)
ACTING_LITERAL = ["[ITEM] using", "[DBLITEM] use", "[DBLITEM] menu", "[DBLITEM] after", "[BALLS-BUY] acting why=",
                  "[KIT-BUY] acting why=", "[DEXCATCH-NOBAIL]", "[CATCH] trainee", "[KEYBATTLE] allow=False"]


_TL1 = "derailed: Tate & Liza: 27 losses with no super-effective answer to Rock/Psychic"
_TL2 = "derailed: Tate & Liza: 31 losses with no super-effective answer to Rock/Psychic"


@row("S3a", "STOP-3: one signature in 2 B runs (loss counts differ: one signature) and 0 A runs, an acting tag in the "
            "tails -> 'yes' (with 0 untagged qualifying signatures printed beside it); the same signature also in ONE "
            "A run -> 'no'")
def _s3a():
    yes = _s3([("H9", "B", [("b1.log", _TL1, _tagged())]), ("H10", "B", [("b2.log", _TL2, _tagged())]),
               ("H1", "A", [("a1.log", "finished", B(*WILD))])])
    no = _s3([("H9", "B", [("b1.log", _TL1, _tagged())]), ("H10", "B", [("b2.log", _TL2, _tagged())]),
              ("H1", "A", [("a1.log", _TL1, B(*WILD))])])
    return eq((yes["pattern"], len(yes["qualifying"]), yes["detail"][-1], no["pattern"], len(no["qualifying"])),
              (True, 1, "STOP-3 pattern: yes (0 of 1 qualifying signature(s) had NO acting tag in any tail)", False, 0))


@row("S3b", "STOP-3: ONE B run with the signature -> 'no'; FINISHED runs are no signature")
def _s3b():
    one = _s3([("H9", "B", [("b1.log", _TL1, _tagged())]), ("H10", "B", [("b2.log", "finished", _tagged())])])
    fin = _s3([("H9", "B", [("b1.log", "finished", _tagged())]), ("H10", "B", [("b2.log", "finished", _tagged())])])
    return eq((one["pattern"], one["ends"], fin["pattern"], fin["ends"]), (False, {"A": 0, "B": 1}, False,
                                                                            {"A": 0, "B": 0}))


@row("S3c", "STOP-3's tail is the LAST 200 lines (the END marker not counted): the acting line 200th from the end -> "
            "'yes', 201st -> 'no'")
def _s3c():
    at = _s3([("H9", "B", [("b1.log", _TL1, _tagged(199))]), ("H10", "B", [("b2.log", _TL2, _tagged(199))])])
    out = _s3([("H9", "B", [("b1.log", _TL1, _tagged(200))]), ("H10", "B", [("b2.log", _TL2, _tagged(200))])])
    return eq((at["pattern"], out["pattern"]), (True, False))


@row("S3d", "RULING 3: the ACTING tags are the LITERAL nine, each found ALONE on its real line, every acting why= "
            "kind counted; a near miss is none; a run whose log was not read is listed UNREADABLE and reads 'no'")
def _s3d():
    one_each = [Q("a_using"), Q("d_use"), Q("d_menu"), Q("d_after"), Q("bb_topoff"), Q("kit_bought"), Q("nobail"),
                Q("trainee"), Q("n_kb")]
    got = [CK().tags_in([ln]) for ln in one_each]
    whys = ([sub(Q("bb_topoff"), "why=topoff ", f"why={w} ") for w in ("topoff-failed", "topoff-closed",
                                                                      "topoff-recovery")]
            + [sub(Q("kit_bought"), "why=kit ", f"why={w} ") for w in ("kit-failed", "kit-closed", "kit-recovery")])
    near = CK().tags_in(["f1 [BATTLE] [ITEM] used Potion", Q("catch_start"), Q("w_turn")])
    unread = _s3([("H9", "B", [("b1.log", _TL1, None)]), ("H10", "B", [("b2.log", _TL2, None)])])
    return eq((list(CK().ACTING_TAGS), got, [CK().tags_in([w]) for w in whys], near, unread["pattern"],
               sum("UNREADABLE" in d for d in unread["detail"])),
              (ACTING_LITERAL, [[t] for t in ACTING_LITERAL], [["[BALLS-BUY] acting why="]] * 3
               + [["[KIT-BUY] acting why="]] * 3, [], False, 2))


@row("S3e", "RULING 3 + its correction: NOT acting — why=mandatory (printed in BOTH arms, early_game.py:2730-2735), "
            "every -none / -skip / -observe / -flag / -forecast why= (a WHOLE token: topoff never matches topoff-none), "
            "[KEYBATTLE] allow=True, [CATCH] trainee-after, a [DBLITEM-OBS] row (its why=hp)")
def _s3e():
    noop = ([Q("bb_mandatory"), Q("heal_balls"), Q("heal_kit"), Q("r_kb"), Q("x_kb"), Q("trainee_after"), Q("d_obs"),
             Q("failopen")]
            + [sub(Q("bb_topoff"), "why=topoff ", f"why={w} ") for w in ("topoff-observe", "topoff-skip",
                                                                       "topoff-flag")]
            + [sub(Q("kit_bought"), "why=kit ", f"why={w} ") for w in ("kit-observe", "kit-skip", "kit-forecast",
                                                                     "kit-flag")])
    return eq([CK().tags_in([ln]) for ln in noop], [[]] * len(noop))


@row("S3f", "STOP-3 (the correction's rows): a B derail tail whose only package-shaped line is why=mandatory, or "
            "why=kit-none, or [KEYBATTLE] allow=True -> no acting tag: 'no'")
def _s3f():
    reads = []
    for q in ("bb_mandatory", "heal_kit"):
        body = B(*NONKEY[:2]) + [Q(q)] + B(*NONKEY[4:])          # a trainer battle with NO [KEYBATTLE] line
        reads.append(_s3([("H9", "B", [("b1.log", _TL1, body)]), ("H10", "B", [("b2.log", _TL2, body)])]))
    reads.append(_s3([("H9", "B", [("b1.log", _TL1, B(*RIVAL))]), ("H10", "B", [("b2.log", _TL2, B(*RIVAL))])]))
    return eq([(r["pattern"], r["no_tag"], r["detail"][-1]) for r in reads],
              [(False, 1, "STOP-3 pattern: no (1 qualifying signature(s), none with an acting tag in a tail)")] * 3)


@row("S3g", "STOP-3 (the hunter's KS3-onelane): TWO runs of ONE B lane with one signature (0 A runs) qualify -> 'yes'")
def _s3g():
    r = _s3([("H9", "B", [("b1.log", _TL1, _tagged()), ("b2.log", _TL2, _tagged())]),
             ("H1", "A", [("a1.log", "finished", B(*WILD))])])
    return eq((r["pattern"], len(r["qualifying"])), (True, 1))


@row("S3h", "STOP-3's 'ANY tail' rule, PINNED (the hunter's KS3-any): one tagged tail of two -> 'yes'; with a second "
            "qualifying signature with NO acting tag, the line says so: '1 of 2 … had NO acting tag'")
def _s3h():
    any1 = _s3([("H9", "B", [("b1.log", _TL1, _tagged())]), ("H10", "B", [("b2.log", _TL2, B(*RIVAL))])])
    two = _s3([("H9", "B", [("b1.log", _TL1, _tagged()), ("b3.log", "derailed: Norman: 6 losses", B(*RIVAL))]),
               ("H10", "B", [("b2.log", _TL2, B(*RIVAL)), ("b4.log", "derailed: Norman: 8 losses", B(*RIVAL))])])
    return eq((any1["pattern"], two["pattern"], two["no_tag"], two["detail"][-1]),
              (True, True, 1, "STOP-3 pattern: yes (1 of 2 qualifying signature(s) had NO acting tag in any tail)"))


# ============================================================================================ T — the tables
def table_runs() -> list:
    """The hand-built fixture (expected values derived by hand in each row):
      A1 complete: rival W; Roxanne L (A's item); Roxanne W; badge 1; VR wild battle; a rare-at-species-level Skitty
         catch (no suffix, as A prints); a (16,10) load with ₽3,380 the last reading; an OLD leg-11 refusal; fences.
      A2 cut: rival W only.
      B1 complete: rival W; badge 1; Combusken caught; Roxanne W (Combusken leads); NON-KEY W; Sceptile caught; T&L W
         (Sceptile leads); the economy lines; a rare (variant) Abra catch battle that fled.
      B2 complete: rival W; Roxanne L (never won); a NON-KEY battle LOST; a wild dex catch LOST (filed); a CURRENT
         leg-11 refusal without a (16,10) load.
    Every catch battle CLOSES as the real ones do (the hunter's F11): Skitty `ended (outcome=…Caught)` then its
    `[CATCH] end`, Abra `ended (outcome=…OpponentTeleported)` then `end=foe_fled` (L09:2241-2280, 2753-2756)."""
    leg_old = Q("derail") + "BotModeError: " + Q("leg11_old") + " ₽1,741"
    leg_new = Q("derail") + "BotModeError: " + Q("leg11_new")
    fence_a = no_rare(Q("w_fence"))
    reserve_a = no_rare(Q("fence_reserve"))
    a1 = B(*RIVAL, *ROX_LOST, *ROX_WON, "badge") + [
        sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> VICTORY ROAD(24,43)"), *wild_a(),
        Q("skitty_started"), no_rare(Q("skitty_start")), Q("w_turn"), Q("caught_ended"), Q("catch_end"),
        fence_a, fence_a, reserve_a, sub(reserve_a, "only 2 spare", "only 3 spare"),
        Q("n_money"), sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> EVER GRANDE CITY(16,10)"), Q("hb_money"),
        leg_old, sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> SOOTOPOLIS CITY(0,7)"), fence_a]
    caught = lambda sp: sub(Q("catch_end"), "sp=Skitty#300", f"sp={sp}")  # noqa: E731
    b1 = B(*RIVAL, "badge") + [caught("Combusken#256")] + B(*ROX_WON, *NONKEY) + [caught("Sceptile#254")] + B(*TL) + B(
        "bb_mandatory", "bb_topoff", "heal_balls", "kit_bought", "heal_kit",
        "w_started", "catch_start", "w_turn", "teleported", "fled_end", "weaken_damage", "weaken_throw")
    nk_lost = [sub(Q(n), "Won", "Lost") if n in ("n_ended", "n_money") else Q(n) for n in NONKEY]
    nk_lost[NONKEY.index("n_end")] = sub(Q("n_end"), "res=Won money=3300->3380 delta=80 mult=1",
                                         "res=Lost money=3300->3300 delta=0 mult=0")
    # B2's lost catch is of a species B's own line calls NOT rare (`rare=- tier=- note=-`, the real B shape)
    pooch = sub(sub(Q("catch_start"), "sp=Abra#63", "sp=Poochyena#261"), "rare=variant tier=ULTRA", "rare=- tier=-")
    b2 = B(*RIVAL, *ROX_LOST) + nk_lost + [Q("w_started"), pooch, Q("w_turn"),
                                           lost_dex_end(), sub(Q("w_ended"), "Won", "Lost"), loss_filed(), leg_new]
    return [rec("A", for_a(a1), lane="H1", log="a1-debug-20261001-210000.log"),
            rec("A", for_a(B(*RIVAL)), lane="H2", log="a2-debug-20261001-210000.log", cut=True),
            rec("B", b1, lane="H9", log="b1-debug-20261001-210000.log"),
            rec("B", b2, lane="H10", log="b2-debug-20261001-210000.log")]


_TR: dict = {}


def TR() -> list:
    if "runs" not in _TR:
        _TR["runs"] = table_runs()
    return _TR["runs"]


def _stdout_fixture():
    return {"H1": {"arm": "A", "runs": CK().parse_stdout(stdout_text([("a1-debug-20261001-210000.log",
                                                                        "frame-cap (5,100,000 > 5,000,000)")]))},
            "H2": {"arm": "A", "runs": []},
            "H9": {"arm": "B", "runs": CK().parse_stdout(stdout_text([("b1-debug-20261001-210000.log", "finished")]))},
            "H10": {"arm": "B", "runs": CK().parse_stdout(stdout_text([("b2-debug-20261001-210000.log", _TL1)]))}}


@row("T1", "D-funnel: Roxanne A met/elig 1/1, first W/decided 0/1, eventually 1; B 2/2, 1/2, eventually 1, unbeaten 1 "
           "(1 attempt); the rival A 2/2 (a CUT run that met and decided it counts); T&L B met 1 of 2 eligible")
def _t1():
    f = TB().d_funnel(TR(), _stdout_fixture())
    pick = lambda arm, k: tuple(f[arm]["rows"][k][x] for x in ("met", "eligible", "decided", "first_won",  # noqa: E731
                                                                "eventually", "unbeaten_stopped"))
    return eq((pick("A", "ROXANNE"), pick("B", "ROXANNE"), f["B"]["rows"]["ROXANNE"]["attempts"],
               pick("A", "RIVAL_ROUTE_103"), pick("B", "TATE_AND_LIZA"), f["A"]["crosscheck"], f["B"]["crosscheck"]),
              ((1, 1, 1, 0, 1, 0), (2, 2, 2, 1, 1, 1), [1], (2, 2, 2, 2, 2, 0), (1, 2, 1, 1, 1, 0), [], []))


@row("T2", "D-funnel: runs started, status, frame-cap ends (stdout), A's badges reached and which badge has frames "
           "(the frame VALUE and B's maximum are TS6's since KI-119)")
def _t2():
    # KI-119 (`#27-gradeidentity`): badges are leader wins now, which moved A's badge-1 frame (204181 -> 203335) and
    # B1's maximum (its Tate & Liza win is badge 7; the fixture logs no [BADGE] n=7) — both asserted in TS6
    f = TB().d_funnel(TR(), _stdout_fixture())
    return eq(((f["A"]["started"], f["A"]["status"], f["A"]["frame_cap"], f["A"]["badges"],
                sorted(f["A"]["badge_frames"])),
               (f["B"]["started"], f["B"]["status"], f["B"]["frame_cap"])),
              ((2, {"complete": 1, "cut": 1}, 1, {0: 1, 1: 1}, [1]),
               (2, {"complete": 2}, 0)))


@row("T3", "D-attempt: every KEY battle per group — A leaders 2 (1 W 1 L), rivals 2 W; B leaders 3 (2 W 1 L), rivals 2")
def _t3():
    d = TB().d_attempt(TR())
    return eq((d["A"], d["B"]), ({"rivals": {"n": 2, "won": 2, "lost": 0, "other": 0},
                                  "leaders": {"n": 2, "won": 1, "lost": 1, "other": 0}},
                                 {"rivals": {"n": 2, "won": 2, "lost": 0, "other": 0},
                                  "leaders": {"n": 3, "won": 2, "lost": 1, "other": 0}}))


@row("T4", "D-boss: T&L B 1/1 (met 1), A NOT ASSESSED (0); the Elite Four NOT ASSESSED (0) in both")
def _t4():
    d = TB().d_boss(TR())
    text = "\n".join(TB().render_boss(d))
    return eq((d["B"]["rows"]["TATE_AND_LIZA"], d["A"]["rows"]["TATE_AND_LIZA"], "A NOT ASSESSED (0)   B 1/1 = 1.00 "
               "(met 1)" in text, "ELITE_FOUR      A NOT ASSESSED (0)   B NOT ASSESSED (0)" in text),
              ({"met": 1, "decided": 1, "won": 1}, {"met": 0, "decided": 0, "won": 0}, True, True))


@row("T5", "D-lead: B 2 of 5 key first attempts led by a post-Stone-Badge catch (Combusken at Roxanne, Sceptile at T&L), "
           "A 0 of 3; Roxanne's B rate .5 -> 0 without B1's; the post-treatment label and 'evolved catches are missed' "
           "are printed")
def _t5():
    d = TB().d_lead(TR())
    rox_all, rox_wo = d["rates"]["all"]["ROXANNE"], d["rates"]["without"]["ROXANNE"]
    text = "\n".join(TB().render_lead(d))
    return eq((d["share"], [round(float(x), 6) for x in rox_all], [round(float(x), 6) for x in rox_wo],
               d["rates"]["dropped"]["ROXANNE"], "conditioned on a post-treatment variable" in text,
               "evolved catches are missed" in text.splitlines()[0], "VOID" in text),
              ({"A": (0, 3), "B": (2, 5)}, [0.0, 0.5], [0.0, 0.0], {"A": 0, "B": 1}, True, True, False))


@row("T15", "RULING 8: D-lead marks its C2 rates VOID when compare_arms' void_reason applies")
def _t15():
    d = TB().d_lead(TR(), "STOP ARM LEAK")
    text = TB().render_lead(d)
    return eq((sum(ln == "  ⛔ C1-C2 VOID: STOP ARM LEAK (DESIGN §4) — the C2 rates below are VOID: descriptive only"
                   for ln in text), sum(ln.endswith("without those [VOID]:") for ln in text)), (1, 1))


@row("T6", "D-loss: non-key A 0/0 B 1/2; wild catch A 0/1 B 1/2 (one end=lost line); other wild A 0/1 B 0/0; key A "
           "1/4 B 1/5; Victory Road A 2 battles on VICTORY_ROAD_1F (the map a battle STARTED on: both after the load)")
def _t6():
    d = TB().d_loss(TR())
    rows = {arm: {k: (v["lost"], v["n"]) for k, v in d[arm]["rows"].items()} for arm in ("A", "B")}
    return eq((rows, d["A"]["catch_end_lost"], d["B"]["catch_end_lost"],
               {m: (v["lost"], v["n"]) for m, v in d["A"]["victory_road"].items()}, d["B"]["victory_road"]),
              ({"A": {"non-key trainer": (0, 0), "wild catch": (0, 1), "other wild": (0, 1), "key trainer": (1, 4),
                      "unclassified": (0, 0)},
                "B": {"non-key trainer": (1, 2), "wild catch": (1, 2), "other wild": (0, 0), "key trainer": (1, 5),
                      "unclassified": (0, 0)}}, 0, 1, {"VICTORY_ROAD_1F": (0, 2)}, {}))


@row("T7", "D-leg11: A loaded (16,10) 1, its OLD-text refusal 1; B a CURRENT-text refusal without a (16,10) load")
def _t7():
    d = TB().d_leg11(TR())
    return eq((d["A"], d["B"]), ({"loaded": 1, "refused_runs": 1, "refused_loaded": 1, "old_lines": 1, "new_lines": 0},
                                 {"loaded": 0, "refused_runs": 1, "refused_loaded": 0, "old_lines": 0,
                                  "new_lines": 1}))


@row("T8", "D-fence: DISTINCT pairs — A before Sootopolis 2 (a repeat and a number change are one pair), after 1; the "
           "'not frequency' label is printed")
def _t8():
    d = TB().d_fence(TR())
    text = "\n".join(TB().render_fence(d))
    return eq((d["A"]["total"], dict(d["A"]["by"]["before"]), dict(d["A"]["by"]["after"]),
               "distinct pairs, not frequency" in text),
              ({"before": 2, "after": 1}, {"skip: no Pokédex yet": 1,
                                           "skip: only N spare balls — below the dex reserve of N": 1},
               {"skip: no Pokédex yet": 1}, True))


@row("T9", "D-economy: B balls by why (mandatory 30 ₽6,000; topoff 2 ₽400; topoff-none 0), Poké Ball 2 ₽400 by ball, "
           "kit ₽1,400 Super Potion 2; the PACKAGE ₽1,800 over 2 paying errands (mandatory not in it); T1 per map; "
           "money at leg 11 A [3380]")
def _t9():
    d = TB().d_economy(TR())
    b = d["B"]
    return eq(({w: (v["lines"], v["bought"], v["spent"]) for w, v in b["balls"].items()}, b["by_ball"],
               {w: (v["lines"], v["spent"]) for w, v in b["kit"].items()}, b["items"], b["package"], b["t1"],
               d["A"]["money_leg11"], d["A"]["t1"]),
              ({"mandatory": (1, 30, 6000), "topoff": (1, 2, 400), "topoff-none": (1, 0, 0)},
               {"Poké Ball": {"bought": 2, "spent": 400}}, {"kit": (1, 1400), "kit-none": (1, 0)},
               {"Super Potion": 2}, {"spent": 1800, "errands": 2, "joint": 0, "unreadable": 0},
               {"0,18": {"n": 2, "delta": 600}, "11,3": {"n": 2, "delta": 1500}, "0,17": {"n": 2, "delta": 80},
                "14,0": {"n": 1, "delta": 8400}},
               [3380], {"0,18": {"n": 2, "delta": 600}, "11,3": {"n": 2, "delta": 1500}}))


@row("T16", "RULING 4: the REAL joint errand (L10 f267952: 12 Poké Balls + 3 Super Potions, ONE money=10180->5680) is "
            "₽4,500 ONCE in the package row, while each line's row keeps its errand money (labelled: counted in both)")
def _t16():
    d = TB().d_economy([rec("B", B(*RIVAL, "joint_balls", "joint_kit"), lane="H9"), rec("A", for_a(B(*RIVAL)))])
    b = d["B"]
    text = "\n".join(TB().render_economy(d))
    return eq((b["package"], b["balls"]["topoff"]["spent"], b["kit"]["kit"]["spent"], b["by_ball"], b["items"],
               "₽4,500 over 1 paying errand(s), 1 of them joint ball+kit" in text,
               "errand money, joint errands counted in both" in text),
              ({"spent": 4500, "errands": 1, "joint": 1, "unreadable": 0}, 4500, 4500,
               {"Poké Ball": {"bought": 12, "spent": 4500}}, {"Super Potion": 3}, True, True))


def _rare_runs():
    """A: Skitty (no suffix, as A prints); B: Skitty (rare=rate), Abra (variant) and Poochyena (rare=-)."""
    skitty = [Q("skitty_started"), Q("skitty_start"), Q("w_turn"), Q("caught_ended"), Q("catch_end")]
    abra = B("w_started", "catch_start", "w_turn", "teleported", "fled_end")
    pooch = [Q("w_started"), sub(sub(Q("catch_start"), "sp=Abra#63", "sp=Poochyena#261"), "rare=variant tier=ULTRA",
                                 "rare=- tier=-"), Q("w_turn"), Q("caught_ended"),
             sub(Q("catch_end"), "sp=Skitty#300", "sp=Poochyena#261")]
    return [rec("A", for_a(B(*RIVAL) + skitty), lane="H1"), rec("B", B(*RIVAL) + skitty + abra + pooch, lane="H9")]


@row("T10", "D-rare (RULING 9): BOTH arms under the ONE species-level rule (Skitty: A 1, B 1; Abra's variant is not "
            "visible to it), and B by its own line's rare= (Skitty rate, Abra variant; Poochyena rare=- is NOT rare)")
def _t10():
    d = TB().d_rare(_rare_runs())
    flat = lambda rows: {sp: (v["battles"], dict(v["ends"])) for sp, v in rows.items()}  # noqa: E731
    return eq(({arm: flat(d["species"][arm]) for arm in ("A", "B")}, flat(d["line"]["B"]), "A" in d["line"]),
              ({"A": {"Skitty#300": (1, {"caught": 1})}, "B": {"Skitty#300": (1, {"caught": 1})}},
               {"Skitty#300": (1, {"caught": 1}), "Abra#63": (1, {"foe_fled": 1})}, False))


@row("T11", "D-M1b: two runs with the SAME [DMGAUDIT] block at different frames -> 1 unique of 2 (1 BEFORE); the pool "
            "file is the unique block, which audit_damage_calc parses whole")
def _t11():
    pool = CK().M1bPool(io.StringIO())
    rec("A", B(*WILD), m1b=pool)
    rec("B", [Q(n) if n not in ("w_ctl", "w_before", "w_after") else "f9" + Q(n)[1:] for n in WILD], m1b=pool)
    text = pool.out.getvalue()
    rep = audit_damage_calc.audit_text(text)
    return eq((pool.blocks, pool.unique, pool.unique_lines, pool.befores, rep.raw_count, rep.parsed_count),
              (2, 1, 3, 1, 3, 3))


@row("T12", "D-weaken: would= by verdict and stage, per arm (B: DAMAGE stage2 1, THROW - 1; A none)")
def _t12():
    d = TB().d_weaken(TR())
    return eq(d, {"A": {}, "B": {("DAMAGE", "stage2"): 1, ("THROW", "-"): 1}})


@row("T13", "D-throughput: lane-hours from summary.json spawns (A 2 x 1800 s = 1.0; B 7200 s + one spawn still "
            "running = 2.0), complete runs per lane-hour (A 1.0, B 1.0), frames/s = all logs' frames / spawn seconds")
def _t13():
    summ = {"lanes": {"H1": {"spawns": [{"start": 0.0, "end": 1800.0}]}, "H2": {"spawns": [{"start": 0.0, "end": 1800.0}]},
                      "H9": {"spawns": [{"start": 0.0, "end": 7200.0}]}, "H10": {"spawns": [{"start": 10.0, "end": None}]}}}
    lanes = [{"tag": "H1", "arm": "A"}, {"tag": "H2", "arm": "A"}, {"tag": "H9", "arm": "B"}, {"tag": "H10", "arm": "B"}]
    d = TB().d_throughput(TR(), summ, lanes)
    fa = sum(r["t4"]["frames"] for r in TR()[:2])
    return eq((d["A"]["lane_hours"], d["A"]["runs_per_lane_hour"], d["A"]["fps"] == fa / 3600.0, d["B"]["lane_hours"],
               d["B"]["complete"], d["B"]["runs_per_lane_hour"], d["A"]["frames_other"] == [TR()[1]["t4"]["frames"]]),
              (1.0, 1.0, True, 2.0, 2, 1.0, True))


@row("T14", "the rendered tables carry NO verdict word, and every table title is printed")
def _t14():
    b = {"runs": TR(), "stdout": _stdout_fixture(), "summary": None, "manifest": {"lanes": []}}
    _data, lines = TB().all_tables(b, CK().M1bPool(), None, None)
    text = "\n".join(lines)
    words = [w for w in TB().VERDICT_WORDS if w in text.replace("NOT ASSESSED", "")]
    titles = [t for t in ("D-funnel", "D-attempt", "D-boss", "D-lead", "D-loss", "D-leg11", "D-fence", "D-economy",
                          "D-rare", "D-M1b", "D-weaken", "D-throughput") if not any(ln.startswith(t) for ln in lines)]
    return eq((words, titles), ([], []))


# ---- the hunter's table rows (`kill_rows.py`, adapted): each pins a rule no row above exercised
@row("T17", "D-funnel (KTF-cens, DECISION F10): a B run CUT during its Roxanne attempt (start, no end) is met but NOT "
            "eligible: met 2, eligible 1, decided 1")
def _t17():
    runs = [rec("B", B(*RIVAL, "x_started", "x_start", "x_kb", "x_turn"), lane="H9", cut=True),
            rec("B", B(*RIVAL, *ROX_WON), lane="H10"), rec("A", for_a(B(*RIVAL)), lane="H1")]
    row_ = TB().d_funnel(runs, {})["B"]["rows"]["ROXANNE"]
    return eq((row_["met"], row_["eligible"], row_["decided"]), (2, 1, 1))


@row("T18", "D-loss (KTL-other): a wild CATCH battle ending OpponentTeleported (the real L09 lines) is not a loss")
def _t18():
    d = TB().d_loss([rec("B", B(*RIVAL, "w_started", "catch_start", "w_turn", "teleported", "fled_end")),
                     rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq((d["B"]["rows"]["wild catch"]["lost"], d["B"]["rows"]["wild catch"]["n"]), (0, 1))


@row("T19", "D-fence (KTD-perrun): the SAME pair in TWO runs is TWO distinct-per-run pairs")
def _t19():
    fence = no_rare(Q("w_fence"))
    d = TB().d_fence([rec("A", for_a(B(*RIVAL)) + [fence], lane="H1"),
                      rec("A", for_a(B(*RIVAL)) + [fence], lane="H2"), rec("B", B(*RIVAL), lane="H9")])
    return eq(d["A"]["total"]["before"], 2)


@row("T20", "D-funnel 'unbeaten' (KBT02): a CUT run that lost Roxanne and never beat her is not an unbeaten COMPLETE run")
def _t20():
    f = TB().d_funnel([rec("B", B(*RIVAL, *ROX_LOST), lane="H9", cut=True), rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    return eq(f["B"]["rows"]["ROXANNE"]["unbeaten_stopped"], 0)


@row("T21", "D-boss (KBT07): a run cut mid-T&L met it but did not DECIDE it -> NOT ASSESSED (1), never '0/1'")
def _t21():
    d = TB().d_boss([rec("B", B(*TL[:3]), lane="H9", cut=True), rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq((d["B"]["rows"]["TATE_AND_LIZA"], "B NOT ASSESSED (1)" in "\n".join(TB().render_boss(d))),
              ({"met": 1, "decided": 0, "won": 0}, True))


@row("T22", "D-lead (KBT09): a lead caught BEFORE the Stone Badge is not a post-badge lead")
def _t22():
    # KI-119 (`#27-gradeidentity`): the catch line reads badges=0, as a real catch before Roxanne's win does (its own
    # field is the tag now; the real L16 line :879 is one)
    caught = sub(sub(Q("catch_end"), "sp=Skitty#300", "sp=Combusken#256"), " badges=1 ", " badges=0 ")
    d = TB().d_lead([rec("B", B(*RIVAL) + [caught] + B("badge", *ROX_WON), lane="H9"),
                     rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq(d["share"]["B"], (0, 2))


@row("T23", "the tables read USABLE runs (KBT23): a run with no starter (compare_arms excludes it) is not 'started'")
def _t23():
    lines = header("B") + [Q("choose")] + B(*RIVAL) + ["=== DEBUG LOG END ==="]
    excl = CA().run_record(lines, log="x-debug-20261001-210000.log", lane={"tag": "H10", "slot": 1, "arm": "B"},
                           arms=ARMS)
    excl["t4"] = CK().extract(lines, forbid=MONITOR["B"]["forbid"])
    f = TB().d_funnel([rec("B", B(*RIVAL), lane="H9"), excl, rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    return eq((bool(excl["excluded"]), f["B"]["started"]), (True, 1))


@row("T24", "D-lead's denominator (KTLd-den) is key FIRST ATTEMPTS: a trainer met in a run cut mid-attempt is not one")
def _t24():
    d = TB().d_lead([rec("B", B(*RIVAL, "x_started", "x_start", "x_kb", "x_turn"), lane="H9", cut=True),
                     rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq(d["share"]["B"], (0, 1))


@row("T25", "the K* CROSS-CHECK fires (a fault-injected control): a run record whose compare_arms keys disagree with "
            "the lines -> D-funnel names the trainer (builder T04 is killed here, not called equivalent)")
def _t25():
    runs = [rec("B", B(*RIVAL, *ROX_WON), lane="H9"), rec("A", for_a(B(*RIVAL)), lane="H1")]
    runs[0]["keys"]["ROXANNE"] = dict(runs[0]["keys"]["ROXANNE"], won=False)        # the planted disagreement
    f = TB().d_funnel(runs, {})
    return eq((len(f["B"]["crosscheck"]), f["B"]["crosscheck"][0].split(":")[0] if f["B"]["crosscheck"] else None,
               f["A"]["crosscheck"]), (1, "ROXANNE", []))


@row("T26", "D-loss: a run CUT inside a wild catch battle (a [CATCH] start, no end) still counts it as a CATCH battle "
            "(builder K51 is killed here: the start alone marks it)")
def _t26():
    d = TB().d_loss([rec("B", B(*RIVAL, "w_started", "catch_start", "w_turn"), lane="H9", cut=True),
                     rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq((d["B"]["rows"]["wild catch"]["n"], d["B"]["rows"]["other wild"]["n"]), (1, 0))


@row("T27", "RULING 5 (D-fence's era): a momentary (0,7) read that reverts within 2 frames, and a (255,255) pair, keep "
            "the era 'before'; a REAL Sootopolis load moves it to 'after'")
def _t27():
    fence = no_rare(Q("w_fence"))
    flick = [sub(Q("map_vr"), "VICTORY ROAD(24,43) -> EVER GRANDE CITY(0,8)", "ROUTE 128(0,43) -> ROUTE 128(0,7)"),
             sub(sub(Q("map_vr"), "f6034921 ", "f6034922 "), "VICTORY ROAD(24,43) -> EVER GRANDE CITY(0,8)",
                 "ROUTE 128(0,7) -> ROUTE 128(0,43)")]
    pair = [Q("tr255_in"), Q("tr255_out")]
    real = [sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> SOOTOPOLIS CITY(0,7)")]
    d = TB().d_fence([rec("A", for_a(B(*RIVAL)) + flick + pair + [fence], lane="H1"),
                      rec("A", for_a(B(*RIVAL)) + real + [fence], lane="H2"), rec("B", B(*RIVAL), lane="H9")])
    return eq(d["A"]["total"], {"before": 1, "after": 1})


# ============================================================================================ TS — KI-119 (stale boot)
@row("TS1", "KI-119: extract on the REAL stale-boot run (L16 …-040658: 8 [BADGE] lines at f301, the champion's [hb], "
            "then 'Story: choosing Torchic!'): its start is that line; badges from the FIRST leader win (Roxanne "
            "f184413; a second win line does not move it); catch tags from each line's own badges= (Poochyena 0, Abra "
            "1); the run POISONED (8 [BADGE] lines before its start, none after); a catch line with no badges= takes "
            "the highest leader-win badge at the catch (1)")
def _ts1():
    again = sub(Q("s16_roxanne"), "f184413 ", "f190000 ")
    t = rec_lines("B", stale_lines(body=B("s16_catch_pooch", "s16_roxanne") + [again, Q("s16_catch_abra")]))["t4"]
    nofield = rec_lines("B", stale_lines(body=B("s16_catch_pooch", "s16_roxanne")
                                         + [sub(Q("s16_catch_abra"), " badges=1 ", " ")]))["t4"]
    return eq((t["start"], t["badges"], t["caught"], t["badge_pre_start"], t["badge_lines"], nofield["caught"]),
              (17, {1: 184413}, [("Poochyena", 0), ("Abra", 1)], 8, {}, [("Poochyena", 0), ("Abra", 1)]))


def _brawly_led_by(species: str) -> list:
    """Brawly (opp 266) in the real Roxanne battle's lines (L09, arm B), led by `species`."""
    edits = {"x_start": [("opp=265", "opp=266")], "x_kb": [("opp=265", "opp=266")],
             "x_turn": [("Combusken L16", f"{species} L16")], "x_end": [("opp=265", "opp=266")]}
    out = []
    for n in ROX_WON:
        line = Q(n)
        for old, new in edits.get(n, ()):
            line = sub(line, old, new)
        out.append(line)
    return out


@row("TS2", "KI-119 D-lead on the stale-boot run: a key first attempt LED by Abra (caught at badges=1) is post-Stone; "
            "one led by Poochyena (caught at badges=0) is not — B 1 of 2 (the frozen reader tagged both catches 8)")
def _ts2():
    rival = [sub(Q(n), "Torchic L10", "Poochyena L10") if n == "r_turn" else Q(n) for n in RIVAL]
    body = [Q("s16_catch_pooch")] + rival + B("s16_roxanne", "s16_catch_abra") + _brawly_led_by("Abra")
    d = TB().d_lead([rec_lines("B", stale_lines(body=body)), rec("A", for_a(B(*RIVAL)), lane="H1")])
    return eq(d["share"], {"A": (0, 1), "B": (1, 2)})


@row("TS3", "KI-119: PROGRESS before the choosing line is NOT read (planted after the stale run's party clear): the "
            "champion's [hb] money=35923 (a (16,10) load right after the start reads money None), a (16,10) load, a "
            "Sootopolis load (the era stays 'before'), a Rustboro Pokémon Center heal (no errand), a leader win (no "
            "badge), a catch (not caught)")
def _ts3():
    leg11 = sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> EVER GRANDE CITY(16,10)")
    soot = sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> SOOTOPOLIS CITY(0,7)")
    pre = [leg11, soot] + B("heal_in", "heal_pc", "heal_balls", "heal_kit", "x_end", "catch_end")
    t = rec_lines("B", stale_lines(pre=pre, mid=[leg11], body=[Q("w_fence")]))["t4"]
    return eq((t["leg11_loaded"], t["leg11_money"], sorted(t["fence"])[0][0], t["rustboro"], t["badges"], t["caught"]),
              (True, None, "before", None, {}, []))


@row("TS4", "KI-119: CORRECTNESS reads the WHOLE log — planted before the choosing line: a B NON-KEY battle's item use "
            "(E1 FINDING), a lost dex catch (E3 sees it: filed by the loss-filed line after the start), a [DMGAUDIT] "
            "block (counted and pooled), a [WEAKEN-OBS] line, the tail's acting tag (STOP-3), and an A run's B-only "
            "[KIT-BUY] text (E3's monitor FINDING)")
def _ts4():
    pre_b = (B("n_started", "n_start", "n_kb", "n_turn", "a_using", "n_ended", "n_money", "n_end",
               "w_started", "catch_start", "w_turn") + [lost_dex_end(), Q("w_ended")]
             + B("w_ctl", "w_before", "w_after", "weaken_damage"))
    pool = CK().M1bPool()
    rb = rec_lines("B", stale_lines(pre=pre_b, body=[loss_filed()]), m1b=pool)
    ra = rec_lines("A", stale_lines(arm="A", pre=[Q("heal_kit")]), lane="H1")
    e1, e3, t = E(1, [rb]), E(3, [ra, rb], MONITOR), rb["t4"]
    return eq((e1["status"], len(e1["violations"]), len(t["loss_lost_dex"]), len(t["loss_missed"]), t["loss_matched"],
               t["dmg_lines"], pool.blocks, dict(t["weaken"]), "[ITEM] using" in CK().tags_in(t["tail"]),
               e3["status"], len(e3["findings"])),
              ("FINDING", 1, 1, 0, 1, 3, 1, {("DAMAGE", "stage2"): 1}, True, "FINDING", 1))


@row("TS5", "KI-119 the [BADGE] CONTROL, printed by D-funnel with the badge source: a run with [BADGE] lines BEFORE its "
            "choosing line is POISONED (the stale run: B 1); an un-poisoned run whose [BADGE] set differs from its "
            "leader wins is listed (a Roxanne win, no [BADGE] line: B 1); one whose sets agree is not (its [BADGE] "
            "n=1 f204181 read as the control)")
def _ts5():
    stale = rec_lines("B", stale_lines(body=[Q("s16_roxanne")]))
    nobadge = rec("B", B(*ROX_WON), lane="H9")
    agree = rec("B", B(*ROX_WON, "badge"), lane="H10")
    f = TB().d_funnel([stale, nobadge, agree, rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    text = "\n".join(TB().render_funnel(f))
    control = ("poisoned by a boot-loaded save): A 0   B 1; runs whose [BADGE] set after the start differs from the "
               "leader-win set (every un-poisoned run, and any run with such lines): A 0   B 1")
    source = "badge source (KI-119): badge n = the run's first [TRAINER] end res=Won over gym leader n"
    listed = [ln for ln in text.splitlines() if ln.startswith("    arm B ") and ln.endswith(": [BADGE] [] vs leader wins [1]")]
    return eq((f["B"]["badge_poisoned"], f["A"]["badge_poisoned"], [d[1:] for d in f["B"]["badge_disagree"]],
               f["A"]["badge_disagree"], agree["t4"]["badge_lines"], control in text, source in text, len(listed)),
              (1, 0, [([], [1])], [], {1: 204181}, True, True, 1))


@row("TS6", "KI-119: D-funnel's badges are LEADER WINS — A's frames to badge 1 are Roxanne's [TRAINER] end (f203335, not "
            "its [BADGE] line's f204181); B1's Tate & Liza win is badge 7 (its fixture logs no [BADGE] n=7)")
def _ts6():
    f = TB().d_funnel(TR(), _stdout_fixture())
    return eq((f["A"]["badge_frames"], f["B"]["badges"], f["B"]["badge_frames"]),
              ({1: [203335]}, {0: 1, 7: 1}, {1: [203335], 7: [3464107]}))


# ---- the independent review's fold: GS-5 (the badge CONTROLS)
@row("TS7", "GS-5 CONTROL: each [CATCH] end badges= beside the leader wins at that line, over EVERY run (the poisoned "
            "stale run included): B 3 lines, 1 differs (a catch reading badges=1 before any leader win); printed")
def _ts7():
    stale = rec_lines("B", stale_lines(body=B("s16_catch_pooch", "s16_roxanne", "s16_catch_abra")))
    early = rec("B", B(*RIVAL, "catch_end"), lane="H9")          # badges=1 on the line, no leader win yet
    f = TB().d_funnel([stale, early, rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    text = "\n".join(TB().render_funnel(f))
    return eq((f["B"]["catch_tags"], f["A"]["catch_tags"], "included): A 0 lines, 0 differ   B 3 lines, 1 differ" in text),
              ((3, 1), (0, 0), True))


@row("TS8", "GS-5: [BADGE] lines AFTER the start are compared with the leader wins in EVERY run that has them, a POISONED "
            "one included (the stale run + a [BADGE] n=1 line after its start, no leader win: listed)")
def _ts8():
    f = TB().d_funnel([rec_lines("B", stale_lines(body=B("badge"))), rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    return eq((f["B"]["badge_poisoned"], [d[1:] for d in f["B"]["badge_disagree"]]), (1, [([1], [])]))


@row("TS9", "GS-5: a run with NO [TRAINER] telemetry whose own lines say it holds badges (a [BADGE] line, or a catch at "
            "badges=1, after its start) reads badges 'unknown', never 0; one with no such line reads 0; counted in "
            "D-funnel")
def _ts9():
    runs = [rec("B", B("badge"), lane="H9"),
            rec("B", B("skitty_started", "skitty_start", "w_turn", "caught_ended", "catch_end"), lane="H10"),
            rec("B", B(*WILD), lane="H11"), rec("A", for_a(B(*RIVAL)), lane="H1")]
    f = TB().d_funnel(runs, {})
    text = "\n".join(TB().render_funnel(f))
    return eq((f["B"]["badges"], f["B"]["badges_unknown"], f["A"]["badges"],
               "read 'unknown', never 0): A 0   B 2" in text, [r["t4"]["badges_unknown"] for r in runs]),
              ({0: 1, "unknown": 2}, 2, {0: 1}, True, [True, True, False, False]))


# ---- the mutant hunter's rows (`scratchpad/adv27/gihunt/killing_rows.py`), adopted
def _leg11():
    return sub(Q("map_vr"), "-> EVER GRANDE CITY(0,8)", "-> EVER GRANDE CITY(16,10)")


@row("GK10", "extract with NO choosing line reads NO progress ('none at all without one'): a Roxanne win, a catch and a "
             "(16,10) load -> no badge, no catch, leg 11 not loaded")
def _gk10():
    lines = header("B") + B("hb", *ROX_WON) + [Q("catch_end"), Q("n_money"), _leg11()] + ["=== DEBUG LOG END ==="]
    t = CK().extract(lines, forbid=MONITOR["B"]["forbid"])
    return eq((t["start"], t["badges"], t["caught"], t["leg11_loaded"]), (None, {}, [], False))


@row("GK11", "a [MONEY] line BEFORE the choosing line is not the run's money: a (16,10) load right after the start reads "
             "money None")
def _gk11():
    t = rec_lines("B", stale_lines(pre=[Q("n_money")], mid=[_leg11()]))["t4"]
    return eq((t["leg11_loaded"], t["leg11_money"]), (True, None))


@row("GK12", "a (16,10) load ONLY before the choosing line: leg 11 NOT loaded (TS3's load after the start masks this)")
def _gk12():
    t = rec_lines("B", stale_lines(pre=[_leg11()]))["t4"]
    return eq((t["leg11_loaded"], t["leg11_money"]), (False, None))


@row("GK13", "a whole wild CATCH battle (started ... caught) before the choosing line is not a catch of the run")
def _gk13():
    pre = B("skitty_started", "skitty_start", "w_turn", "caught_ended", "catch_end")
    return eq(rec_lines("B", stale_lines(pre=pre))["t4"]["caught"], [])


@row("GK14", "a leader DRAW is not a badge: the REAL Tate & Liza res=Draw line (L13 …-043756:31085, live on step 14: "
             "that run never beat Tate & Liza after it), and Roxanne's real end line with res=Draw -> no badge")
def _gk14():
    rox_draw = sub(Q("x_end"), "res=Won money=1368->2868 delta=1500 mult=1", "res=Draw money=1368->1368 delta=0 mult=0")
    body = [Q(n) for n in ROX_WON if n != "x_end"] + [rox_draw]
    return eq((rec("B", body)["t4"]["badges"], rec("B", B("s13_tl_draw"))["t4"]["badges"]), ({}, {}))


@row("GK15", "LEADER_BADGE is the decomp's gym order: TRAINER_ROXANNE_1 265 .. TRAINER_JUAN_1 272 -> badges 1..8 "
             "(pret/pokeemerald include/constants/opponents.h:269-276)")
def _gk15():
    return eq(CK().LEADER_BADGE, {265: 1, 266: 2, 267: 3, 268: 4, 269: 5, 270: 6, 271: 7, 272: 8})


@row("GK16", "extract's start is the FIRST choosing line: a second one later does not move it (progress between them is "
             "read)")
def _gk16():
    lines = (header("B") + B("choose", "hb", *ROX_WON) + [Q("choose").replace("Torchic", "Mudkip")]
             + ["=== DEBUG LOG END ==="])
    t = CK().extract(lines, forbid=MONITOR["B"]["forbid"])
    return eq((t["start"], t["badges"]), (5, {1: 203335}))


@row("GK17", "a catch's tag is its OWN badges= even when it is LOWER than the leader wins so far")
def _gk17():
    caught0 = sub(Q("catch_end"), " badges=1 ", " badges=0 ")
    return eq(rec("B", B(*ROX_WON) + [caught0])["t4"]["caught"], [("Skitty", 0)])


@row("GK18", "a catch line WITHOUT badges= takes the HIGHEST leader-win badge so far, not their count (a Brawly-only win "
             "-> 2)")
def _gk18():
    nofield = sub(Q("catch_end"), " badges=1 ", " ")
    t = rec("B", _brawly_led_by("Combusken") + [nofield])["t4"]
    return eq((t["badges"], t["caught"]), ({2: 203335}, [("Skitty", 2)]))


@row("GK19", "the [BADGE] CONTROL compares SETS: an un-poisoned run whose [BADGE] lines read {1, 2} and whose leader wins "
             "read {2} is listed, though the highest badge agrees")
def _gk19():
    badge2 = sub(Q("badge"), "n=1", "n=2")
    r = rec("B", _brawly_led_by("Combusken") + [Q("badge"), badge2], lane="H9")
    f = TB().d_funnel([r, rec("A", for_a(B(*RIVAL)), lane="H1")], {})
    return eq([d[1:] for d in f["B"]["badge_disagree"]], [([1, 2], [2])])


# ============================================================================================ X — the CLIs end to end
def make_batch(name, lanes, verdict="OK") -> pathlib.Path:
    """A batch directory in T1's layout (`compare_arms` reads it): ARMS.json (the REAL arms file text, so the monitor
    lists are the real ones), `L<nn>/debug-logs/*.log`, `L<nn>/stdout.txt`, summary.json. `lanes` = [(arm, [(log,
    lines, outcome or None)])]."""
    d = TMP["root"] / name
    d.mkdir()
    rows, per = [], {}
    for slot, (arm, logs) in enumerate(lanes):
        tag = f"H{slot + 1}"
        rows.append({"tag": tag, "slot": slot, "arm": arm, "starter": "x", "name": tag, "profile": f"endless-t-{tag}-x"})
        ld = d / f"L{slot + 1:02d}"
        (ld / "debug-logs").mkdir(parents=True)
        for log, lines, _o in logs:
            (ld / "debug-logs" / log).write_text("\n".join(lines) + "\n", encoding="utf-8")
        (ld / "stdout.txt").write_text(stdout_text([(log, o) for log, _l, o in logs]), encoding="utf-8")
        per[tag] = {"cut_log": logs[-1][0] if logs[-1][2] is None else None, "spawns": [{"start": 0.0, "end": 1800.0}],
                    "debug_logs_collected": len(logs)}
    (d / "ARMS.json").write_text(json.dumps({"stamp": name, "profile_tag": "t", "arms_sha256": "0" * 64,
                                             "code_commit": "test", "arms_text": json.dumps(ARMS_FILE),
                                             "lanes_n": len(rows), "lanes": rows}), encoding="utf-8")
    (d / "summary.json").write_text(json.dumps({"verdict": verdict, "stop_reason": "deadline", "lanes": len(rows),
                                                "lanes_detail": per, "lanes_lost": [], "collect_interrupted": False}),
                                    encoding="utf-8")
    return d


def cli(mod, argv) -> "tuple[int, str]":
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = mod.main(argv)
        except SystemExit as stop:
            code = stop.code
    return code, buf.getvalue()


def _good_batch(name, verdict="OK", a_extra=()):
    """A: the rival, a wild battle and the REAL runway refusal every real A lane prints (the hunter's F5); B: the
    rival, its first Rustboro heal and a wild battle."""
    a = lines_of("A", for_a(B(*RIVAL, *WILD)) + [Q("runway")] + list(a_extra))
    b = lines_of("B", B(*RIVAL, *HEAL, *WILD))
    return make_batch(name, [("A", [("a-debug-20261001-210000.log", a, None)]),
                             ("B", [("b-debug-20261001-210000.log", b, None)])], verdict=verdict)


@row("X1", "the checks CLI on a good batch (A prints its real runway refusal): exit 0, all six check lines with their "
           "caveats (E3's loss-filing half had 0 trials), 'C1-C2 not void'; the tables CLI: exit 0, every table")
def _x1():
    d = _good_batch("x1")
    code, out = cli(CK(), [str(d)])
    lines = [ln for ln in out.splitlines() if ln[:3] in ("E1 ", "E2 ", "E3 ", "E4 ", "E5 ") or ln.startswith("STOP-3")]
    tcode, tout = cli(TB(), [str(d)])
    titles = sum(1 for t in ("D-funnel", "D-attempt", "D-boss", "D-lead", "D-loss", "D-leg11", "D-fence", "D-economy",
                             "D-rare", "D-M1b", "D-weaken", "D-throughput") if f"\n{t} " in tout)
    return eq((code, [ln.split(" — ")[0] for ln in lines], "  C1-C2         not void" in out.splitlines(), tcode, titles),
              (0, ["E1  PASS (B had 0 NON-KEY battles)", "E2  PASS", "E3  PASS (loss-filing half had 0 trials)",
                   "E4  NOT ASSESSED", "E5  NOT ASSESSED", "STOP-3  no"], True, 0, 12))


@row("X5", "E3 through the LOADER (the hunter's KE3-loaderA): an A lane printing a B-only text ([KIT-BUY]) -> the "
           "checks CLI reads E3 FINDING — the visit hook hands each lane ITS arm's forbidden list")
def _x5():
    code, out = cli(CK(), [str(_good_batch("x5", a_extra=[Q("heal_kit")]))])
    return eq((code, [ln.split(" — ")[0].split(" (")[0] for ln in out.splitlines() if ln.startswith("E3 ")]),
              (0, ["E3  FINDING"]))


@row("X6", "RULING 8: a batch whose summary reads 'FAILED — ARM LEAK' prints 'C1-C2  VOID: STOP ARM LEAK (DESIGN §4)' "
           "in BOTH tools (compare_arms' void_reason), D-lead marks its rates VOID; --void REASON voids a good batch")
def _x6():
    d = _good_batch("x6", verdict="FAILED — ARM LEAK")
    code, out = cli(CK(), [str(d)])
    tcode, tout = cli(TB(), [str(d)])
    mcode, mout = cli(CK(), [str(_good_batch("x6m")), "--void", "park"])
    want = "  C1-C2         VOID: STOP ARM LEAK (DESIGN §4)"
    return eq((code, want in out.splitlines(), tcode, want in tout.splitlines(), "⛔ C1-C2 VOID: STOP ARM LEAK" in tout,
               mcode, "  C1-C2         VOID: STOP-3 (manual --void): park (DESIGN §4)" in mout.splitlines()),
              (0, True, 0, True, True, 0, True))


@row("X2", "a log whose env-all is the OTHER arm: both CLIs REFUSE like compare_arms (exit 1, NO CHECK / NO TABLE, no "
           "check or table printed)")
def _x2():
    wrong = lines_of("B", B(*RIVAL))
    d = make_batch("x2", [("A", [("a-debug-20261001-210000.log", wrong, None)]),
                          ("B", [("b-debug-20261001-210000.log", lines_of("B", B(*RIVAL)), None)])])
    code, out = cli(CK(), [str(d)])
    tcode, tout = cli(TB(), [str(d)])
    return eq((code, "NO CHECK" in out, "E1 " in out, tcode, "NO TABLE" in tout, "D-funnel" in tout),
              (1, True, False, 1, True, False))


@row("X3", "STOP-3 end to end: two B lanes ending in one signature with an ACTING tag (a why=topoff purchase) in their "
           "tails, A finished -> 'STOP-3  yes'")
def _x3():
    b1 = lines_of("B", B(*RIVAL, "bb_topoff"))
    d = make_batch("x3", [("A", [("a-debug-20261001-210000.log", lines_of("A", for_a(B(*RIVAL, *WILD))), "finished"),
                                 ("a2-debug-20261001-220000.log", lines_of("A", for_a(B(*RIVAL, *WILD))), None)]),
                          ("B", [("b-debug-20261001-210000.log", b1, _TL1),
                                 ("b2-debug-20261001-220000.log", lines_of("B", B(*WILD)), None)]),
                          ("B", [("c-debug-20261001-210000.log", b1, _TL2),
                                 ("c2-debug-20261001-220000.log", lines_of("B", B(*WILD)), None)])])
    code, out = cli(CK(), [str(d)])
    return eq((code, "STOP-3  yes" in out, "STOP-3 pattern: yes" in out), (0, True, True))


@row("X4", "--m1b-out writes the pooled blocks (both arms, de-duplicated) and prints audit_damage_calc's sample count")
def _x4():
    d = _good_batch("x4")
    out_file = TMP["root"] / "x4-pool.log"
    code, out = cli(TB(), [str(d), "--m1b-out", str(out_file)])
    text = out_file.read_text(encoding="utf-8")
    return eq((code, text.count("[DMGAUDIT] CTL"), "blocks 2; unique blocks 1" in out, "accepted samples:" in out),
              (0, 1, True, True))


@row("X7", "GS-6: the checks AND the tables headers print the INSTRUMENT CONTROL 'logs with != 1 Story: choosing X! "
           "line' and list each (a B log with a second choosing line: 1, listed with its count 2)")
def _x7():
    a = lines_of("A", for_a(B(*RIVAL, *WILD)) + [Q("runway")])
    b = header("B") + B("choose", "hb", *RIVAL, "choose") + ["=== DEBUG LOG END ==="]
    d = make_batch("x7", [("A", [("a-debug-20261001-210000.log", a, None)]),
                          ("B", [("b-debug-20261001-210000.log", b, None)])])
    code, out = cli(CK(), [str(d)])
    tcode, tout = cli(TB(), [str(d)])
    want = "  logs with != 1 'Story: choosing X!' line (the run's start, KI-119): 1"
    return eq((code, want in out.splitlines(), "    - b-debug-20261001-210000.log: 2" in out.splitlines(), tcode,
               want in tout.splitlines()), (0, True, True, 0, True))


# ============================================================================================ R — reuse
@row("R1", "K* in TRAINERS is compare_arms' FROZEN KSTAR by reference; the bosses and the Elite Four are the decomp's "
           "ids (opponents.h :265-276, :339); no id is named twice")
def _r1():
    ck = CK()
    same = all(ck.TRAINERS[k] is _REAL_KSTAR[k] for k in _REAL_KSTAR)
    ids = {k: ck.TRAINERS[k] for k in ck.BOSSES + ck.ELITE_FOUR}
    flat = [i for v in ck.TRAINERS.values() for i in v]
    return eq((same, ids, len(flat) == len(set(flat))),
              (True, {"TATE_AND_LIZA": (271,), "WINONA": (270,), "NORMAN": (269,), "JUAN": (272,), "SIDNEY": (261,),
                      "PHOEBE": (262,), "GLACIA": (263,), "DRAKE": (264,), "WALLACE": (335,)}, True))


@row("R2", "compare_arms.collect_runs' visit hook: called ONCE per read log, with that log's lines, after its record")
def _r2():
    d = _good_batch("r2")
    seen = []
    runs, _facts = CA().collect_runs(d, visit=lambda r, lines: seen.append((r["lane"], len(lines), "arm" in r)))
    want = sorted((ln.parent.parent.name, len(ln.read_text(encoding="utf-8").splitlines()))
                  for ln in d.glob("L*/debug-logs/*.log"))
    return eq((sorted((("L01" if t == "H1" else "L02"), n) for t, n, _a in seen), all(a for _t, _n, a in seen),
               len(runs)), (want, True, 2))


# ============================================================================================ mutants
#: (label, target, [(old, new)], the EXACT set of rows it must turn red). Written before the first run.
MUTANTS: list = [
    # ---- E1
    # FIRST RUN (the builder): 77 of 91 matched the sets written before it. Each miss is marked beside its mutant:
    # "PREDICTION" = my set was wrong (the row behaves as specified); "GAP" = a row was added or tightened.
    # THE FOLD of the independent pass (2026-10-01, `evidence/2026-10-01-batch14-T4-ADVERSARIAL.txt`): every survivor
    # the hunter listed is here (its label in brackets) with the row that now kills it, and every RULING has a REVERT
    # mutant. Sets marked "FOLD-PREDICTION" were corrected after the fold's first run (my set was wrong, the row right).
    ("K01 E1 ignores [ITEM] using", "ck",
     [('            "using": [line for line in battle.items if bl.item_kind(line) == "using"],',
       '            "using": [],')], {"E1a", "E1b", "E1c", "E1d", "E1e", "E1g", "TS4"}),
    # PREDICTION: E1d counts the double battle's [ITEM] using as its 2nd line; S3d reads raw lines, not `using`
    ("K02 E1 ignores [DBLITEM] use", "ck",
     [("                uses = rec[\"using\"] + rec[\"dbl_use\"]", "                uses = rec[\"using\"]")], {"E1d"}),
    ("K03 E1 exempts every keybattle reason", "ck",
     [("                    if uses and any(is_fail_open(x) for x in reasons):",
       "                    if uses and reasons:")], {"E1a", "E1b", "TS4"}),   # PREDICTION: E1a's battle has not_a_key_class
    ("K04 fail-open only FAIL_OPEN(", "ck",
     [('FAIL_OPEN_PREFIXES = ("fail_open_", "FAIL_OPEN(")', 'FAIL_OPEN_PREFIXES = ("FAIL_OPEN(",)')],
     {"E1b", "E2f"}),   # FOLD-PREDICTION: E2f's fail_open_unreadable line is then compared, and disagrees
    ("K05 E1 skips WILD battles", "ck",
     [("                if rec[\"cls\"] == bl.WILD:\n                    wild += 1\n                    viol +=",
       "                if rec[\"cls\"] == bl.WILD:\n                    wild += 1\n                    viol = viol +[] or viol;_x =")],
     {"E1c", "E1g"}),
    ("K06 E1 judges A's NON-KEY battles too", "ck",
     [("                elif arm == ARM_B and rec[\"cls\"] == bl.NONKEY:", "                elif rec[\"cls\"] == bl.NONKEY:")],
     {"E1c"}),
    ("K70 [E1-01] E1 judges B KEY battles too", "ck",
     [('                elif arm == ARM_B and rec["cls"] == bl.NONKEY:',
       '                elif arm == ARM_B and rec["cls"] in (bl.NONKEY, bl.KEY):')],
     {"E1f", "X1"}),   # FOLD-PREDICTION: X1's B rival is then counted as NON-KEY, so E1's zero-battle caveat drops
    ("K71 [E1-09] B's WILD battles ignored", "ck",
     [('                if rec["cls"] == bl.WILD:', '                if rec["cls"] == bl.WILD and arm == ARM_A:')], {"E1g"}),
    # ---- E2
    ("K07 E2 allows two [KEYBATTLE] lines", "ck", [("            if len(kb) > 1:", "            if len(kb) > 2:")],
     {"E2a"}),
    ("K08 E2 never compares key=", "ck",
     [("                    if key != offline:", "                    if False:")], {"E2b"}),
    ("K09 E2 flag_off not a violation", "ck",
     [('FLAG_OFF = "flag_off"', 'FLAG_OFF = "flag-off"')], {"E2c"}),
    ("K10 E2 does not count trainer battles without a line", "ck",
     [("            if rec[\"trainer_start\"] and not kb:", "            if False:")], {"E2d"}),
    ("K11 E2 reads arm A too", "ck",
     [("    for run in _arm_runs(runs, ARM_B):\n        for rec in run[\"t4\"][\"battles\"]:\n            kb = rec",
       "    for run in _arm_runs(runs, ARM_A) + _arm_runs(runs, ARM_B):\n        for rec in run[\"t4\"][\"battles\"]:\n            kb = rec")],
     {"E2e"}),
    ("K72 RULING 6 REVERTED: a fail-open line's key= is compared", "ck",
     [('                if is_fail_open(p.get("reason")):\n                    fail_open_keys[f"key={key}"] += 1\n'
       '                    continue\n', "")], {"E2d", "E2f"}),
    ("K73 [E2-07] flag_off a violation only when allow=False (never production's shape)", "ck",
     [('                if p.get("reason") == FLAG_OFF:',
       '                if p.get("reason") == FLAG_OFF and p.get("allow") == "False":')], {"E2c"}),
    # ---- E3
    ("K12 E3 monitor reads the OTHER arm's list", "ck",
     [("        forbid = (monitor.get(record.get(\"lane_arm\")) or {}).get(\"forbid\", [])",
       "        forbid = (monitor.get({'A': 'B', 'B': 'A'}.get(record.get(\"lane_arm\"))) or {}).get(\"forbid\", [])")],
     {"X1"}),
    # [E3-01]: X1's A lane now prints its REAL runway refusal (a B-forbidden text), so B's list on every lane reddens X1
    ("K74 [E3-01] every lane scanned with monitor.B.forbid", "ck",
     [("        forbid = (monitor.get(record.get(\"lane_arm\")) or {}).get(\"forbid\", [])",
       "        forbid = (monitor.get(ARM_B) or {}).get(\"forbid\", [])")], {"X1"}),
    ("K75 the loader hands every lane an EMPTY forbidden list", "ck",
     [("        forbid = (monitor.get(record.get(\"lane_arm\")) or {}).get(\"forbid\", [])", "        forbid = []")],
     {"X5"}),
    ("K13 E3 ignores the monitor hits", "ck",
     [('        hits = [(run, e, ln) for run in rs for e, ln in run["t4"]["monitor_hits"]]', "        hits = []")],
     {"E3a", "E3b", "X5", "TS4"}),
    ("K14 the monitor matches ANY string of a list entry", "ck",
     [('"telemetry": telemetry, "battles": recs, "monitor_hits": x4.scan_lines(lines, list(forbid), ())[0],',
       '"telemetry": telemetry, "battles": recs, "monitor_hits": x4.scan_lines(lines, [s for e in forbid for s in '
       '([e] if isinstance(e, str) else e)], ())[0],')], {"E3b"}),
    ("K15 loss-filed matches before the end too", "ck",
     [("                    if pending_loss:\n                        pending_loss.pop(0)",
       "                    if True:\n                        pending_loss.pop(0) if pending_loss else None")],
     {"E3c"}),   # GAP (first run: survived): E3c now pins the ORPHAN count the report prints
    ("K16 any lost catch needs a loss-filed (team too)", "ck",
     [('                    if kind and kind.group(1) == "dex" and end_v == "lost":',
       '                    if end_v == "lost":')], {"E3c"}),
    ("K17 loss-filed pairing ignored", "ck",
     [('    finds += [f"B {_name(r)}: no [CATCH] loss-filed kind=dex after: {ln.strip()[:240]}" for r, ln in missed]',
       "    pass")], {"E3c"}),
    ("K76 [E3-07] every dex END (caught too) needs a loss-filed", "ck",
     [('                    if kind and kind.group(1) == "dex" and end_v == "lost":',
       '                    if kind and kind.group(1) == "dex":')], {"E3c"}),
    ("K77 [E3-08] one loss-filed clears EVERY pending loss", "ck",
     [("                        pending_loss.pop(0)", "                        pending_loss.clear()")], {"E3c"}),
    ("K18 a heal anywhere counts as Rustboro's", "ck",
     [("            if out[\"rustboro\"] is None and cur_map == RUSTBORO_PC:",
       "            if out[\"rustboro\"] is None:")], {"E3d", "TS3"}),   # TS3: its heal BEFORE the start has no map
    ("K19 the errand window never closes on leaving Rustboro", "ck",
     [("                if heal_window and cur_map not in (RUSTBORO_PC, RUSTBORO_CITY, RUSTBORO_MART):",
       "                if False:")], {"E3d", "E3g", "E3i"}),   # E3g, E3i (added later): a window that never closes
    ("K78 [E3-10] the errand window closes on entering the Rustboro MART", "ck",
     [("(RUSTBORO_PC, RUSTBORO_CITY, RUSTBORO_MART):", "(RUSTBORO_PC, RUSTBORO_CITY):")], {"E3d"}),
    ("K20 the LAST Rustboro heal is judged, not the first", "ck",
     [("            if out[\"rustboro\"] is None and cur_map == RUSTBORO_PC:",
       "            if cur_map == RUSTBORO_PC:")], {"E3e", "E3h"}),
    ("K80 [E3-17] a heal = the 'none' withdraw source only", "ck",
     [('_HEAL_MARK = re.compile(r"^Story: PC — \\S+ withdraw: ")', '_HEAL_MARK = re.compile(r"^Story: PC — none withdraw: ")')],
     {"E3h"}),
    ("K21 the kit half of the Rustboro rule dropped", "ck",
     [('    miss = [r for r in healed if not (r["t4"]["rustboro"]["topoff"] and r["t4"]["rustboro"]["kit"])]',
       '    miss = [r for r in healed if not r["t4"]["rustboro"]["topoff"]]')], {"E3d"}),
    ("K79 [E3-12] censoring only for CUT runs (lost not excused)", "ck",
     [('    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] != "complete"',
       '    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] == "cut"')],
     {"E3g"}),
    ("K81 RULING 5 REVERTED: momentary map reads move the errand window and the era", "ck",
     [("                if pos not in transient:", "                if True:")], {"E3i", "T27"}),
    ("K82 a read reverting after 3 frames is momentary too", "ck", [("TRANSIENT_FRAMES = 2", "TRANSIENT_FRAMES = 3")],
     {"E3i"}),
    ("K83 a (3,0) read is a real arrival", "ck",
     [("TRANSIENT_DESTS = frozenset({(255, 255), (3, 0)})", "TRANSIENT_DESTS = frozenset({(255, 255)})")], {"E3i"}),
    ("K84 RULING 7 REVERTED: the headline drops its caveats", "ck",
     [("""    return r["status"] + (f" ({'; '.join(r['caveats'])})" if r.get("caveats") else "")""",
       '    return r["status"]')], {"E3j", "X1"}),
    ("K85 the loss-filing half's zero-trial caveat dropped", "ck",
     [('    if not lost:\n        caveats.append("loss-filing half had 0 trials")\n', "")], {"E3j", "X1"}),
    ("K86 the Rustboro half's NOT ASSESSED caveat dropped", "ck",
     [('    if not healed:\n        caveats.append("Rustboro half NOT ASSESSED")\n', "")], {"E3j"}),
    # E3g's three (added after the first run, with the censoring rule they pin)
    ("K67 a log ending inside the errand never excuses", "ck",
     [('    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] != "complete"',
       '    censored = [r for r in healed if False and r["status"] != "complete"')], {"E3g"}),
    ("K68 any censored run is excused, window closed or not", "ck",
     [('    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] != "complete"',
       '    censored = [r for r in healed if r["status"] != "complete"')], {"E3g"}),
    ("K69 a COMPLETE run ending inside the errand is excused", "ck",
     [('    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] != "complete"',
       '    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end")')], {"E3g"}),
    ("K22 trainee-after counted as trainee", "ck",
     [('            elif msg.startswith("trainee lead="):', '            elif msg.startswith("trainee"):')],
     {"E3f", "QS4"}),   # PREDICTION: QS4 pins the same counts
    ("K23 trainee lines are a finding in B", "ck",
     [('    head = (f"{len(finds)} miss(es)', '    finds += ["t"] * counts["B"]["trainee"]\n    head = (f"{len(finds)} miss(es)')],
     {"E3f"}),
    # ---- E4
    ("K24 E4 assessed at 4 runs", "ck", [("E4_MIN_RUNS = 5", "E4_MIN_RUNS = 4")], {"E4a", "E4c"}),
    ("K25 [E4-03] the denominator counts T&L ATTEMPTS, not distinct runs", "ck",
     [("            qual.append((run, t))", '            qual.extend([(run, t)] * max(1, len(t["attempts"])))')],
     {"E4c"}),
    ("K26 E4 reads A runs", "ck", [("    rb = _arm_runs(runs, ARM_B)\n    qual = []",
                                    "    rb = _arm_runs(runs, ARM_A) + _arm_runs(runs, ARM_B)\n    qual = []")],
     {"E4c"}),
    ("K87 [E4-06] an UNREADABLE bag (hp None) qualifies", "ck",
     [('        if t and t["first_k"] is not None and t["hp"] is not None and t["hp"] >= 1:',
       '        if t and t["first_k"] is not None and (t["hp"] is None or t["hp"] >= 1):')], {"E4c"}),
    ("K27 the heal gate strict (< .35)", "ck",
     [("            hit = held and frac <= HEAL_FRACTION", "            hit = held and frac < 0.345")],
     {"E4a", "E4b"}),   # FOLD-PREDICTION: E4b's V2/V3 battles are the same Sceptile 46/133 (.346), so they read EXPLAINED
    ("K28 own HP read from the FOE", "ck",
     [('_TURN_ME = re.compile(r"\\[TURN (\\d+)\\] ([^>]+?) L(\\d+) (\\d+)/(\\d+)(?: \\[[^\\]]*\\])? -> ")',
       '_TURN_ME = re.compile(r"\\[TURN (\\d+)\\] (?:.*vs )?(.+?) L(\\d+) (\\d+)/(\\d+)")')],
     {"QS2", "E4a", "E4e", "T5", "TS2"}),
    ("K29 RULING 1 REVERTED: E4 graded on the GLOBAL B use count (V2/V3 mask the list)", "ck",
     [('    uses_q = sum(len(run["t4"]["battles"][t["first_k"]]["dbl_use"]) for run, t in qual)',
       '    uses_q = sum(len(rec["dbl_use"]) for run in rb for rec in run["t4"]["battles"])')], {"E4b"}),
    ("K88 [E4-08] the zero listing reads the run's LAST battle", "ck",
     [('        rec = run["t4"]["battles"][t["first_k"]]\n        held', '        rec = run["t4"]["battles"][-1]\n        held')],
     {"E4a"}),
    ("K89 RULING 1 REVERTED: every zero is a FINDING (an explained zero too)", "ck",
     [("    if reached or unread:", "    if True:")], {"E4e"}),
    ("K90 a battle with NO own-HP read lets the zero read EXPLAINED", "ck",
     [("    if reached or unread:", "    if reached:")], {"E4e"}),
    ("K91 the rule-3 caveat dropped from a 'yes' row", "ck",
     [('RULE3_CAVEAT = "production may decline under its rule 3 (a losing race) — read the battle"',
       'RULE3_CAVEAT = "read the battle"')], {"E4a"}),
    # ---- E5
    ("K30 E5 lists every after", "ck",
     [("        if e[0] != \"after\" or not bl.partner_rose(e[3]):", "        if e[0] != \"after\":")], {"E5a", "E5b"}),
    ("K31 RULING 2 REVERTED: a same-turn use on the partner EXCLUDES the reading", "ck",
     [('        out.append({"turn": turn, "g": g,', '        if context:\n            continue\n'
                                                  '        out.append({"turn": turn, "g": g,')], {"E5b"}),
    ("K32 the context ignores the turn (any use on the partner)", "ck",
     [("if u is not action and turn is not None and u[3] == partner and use_turn.get(u[1]) == turn]",
       "if u is not action and u[3] == partner]")], {"E5b"}),
    ("K33 E5 counted as a FINDING", "ck",
     [('    status = "READ BY HAND" if listed else', '    status = "FINDING" if listed else')], {"E5a"}),
    ("K34 E5 reads A", "ck", [("    rb = _arm_runs(runs, ARM_B)\n    afters",
                               "    rb = _arm_runs(runs, ARM_A) + _arm_runs(runs, ARM_B)\n    afters")],
     {"E5c"}),
    ("K93 [E5-01] E5 counts the readings but lists none", "ck",
     [("    for run, rec, e in listed:\n        detail.append(", "    for run, rec, e in []:\n        detail.append(")],
     {"E5a", "E5b"}),
    # ---- STOP-3
    ("K35 STOP-3 qualifies at 1 B run", "ck", [("        if len(hits) < 2 or per[ARM_A].get(sig):",
                                               "        if len(hits) < 1 or per[ARM_A].get(sig):")], {"S3b"}),
    ("K36 STOP-3 ignores A runs", "ck", [("        if len(hits) < 2 or per[ARM_A].get(sig):",
                                         "        if len(hits) < 2:")], {"S3a"}),
    ("K100 [S3-02] STOP-3 needs 2 distinct B LANES", "ck",
     [("        if len(hits) < 2 or per[ARM_A].get(sig):",
       "        if len({l for l, _r in hits}) < 2 or per[ARM_A].get(sig):")], {"S3g"}),
    ("K37 STOP-3 counts finished runs", "ck",
     [('"signature": None if bucket == "finished" else x4._derail_reason(outcome), "log": log})',
       '"signature": x4._derail_reason(outcome), "log": log})')], {"QS5", "S3b"}),
    ("K38 the tail is 201 lines", "ck", [("TAIL_LINES = 200", "TAIL_LINES = 201")], {"S3c"}),
    ("K39 the tail counts the END marker", "ck",
     [("    while end and (not lines[end - 1].strip() or lines[end - 1].startswith(LOG_END)):", "    while False:")],
     {"S3c"}),
    # [BK40 / S3-07 / S3-08]: the old list's survivors; the LITERAL in S3d now kills any tag dropped from the list
    ("K40 an acting tag dropped ([BALLS-BUY] acting why=)", "ck",
     [('"[DBLITEM] after", "[BALLS-BUY] acting why=",', '"[DBLITEM] after",')], {"S3d", "X3"}),
    ("K111 an acting tag dropped ([CATCH] trainee)", "ck",
     [('"[DEXCATCH-NOBAIL]", "[CATCH] trainee", "[KEYBATTLE] allow=False")', '"[DEXCATCH-NOBAIL]", "[KEYBATTLE] allow=False")')],
     {"S3d"}),
    ("K94 an acting errand outcome dropped (topoff-recovery)", "ck",
     [('ACTING_WHY = frozenset({"topoff", "topoff-failed", "topoff-closed", "topoff-recovery",',
       'ACTING_WHY = frozenset({"topoff", "topoff-failed", "topoff-closed",')], {"S3d"}),
    ("K95 the correction REVERTED: why=mandatory (both arms) counts as acting", "ck",
     [('                        "kit", "kit-failed", "kit-closed", "kit-recovery"})',
       '                        "kit", "kit-failed", "kit-closed", "kit-recovery", "mandatory"})')], {"S3e", "S3f"}),
    ("K96 why= matched as a PREFIX (topoff matches topoff-none)", "ck",
     [("        if why and why.group(1) in ACTING_WHY:", '        if why and why.group(1).startswith(("topoff", "kit")):')],
     {"S3e", "S3f"}),
    ("K97 RULING 3 REVERTED: every [KEYBATTLE] line is acting (allow=True too)", "ck",
     [('        return "[KEYBATTLE] allow=False" if (bl.parse_keybattle(line) or {}).get("allow") == "False" else None',
       '        return "[KEYBATTLE] allow=False"')], {"S3e", "S3f", "S3h"}),
    ("K98 [CATCH] trainee-after counted as trainee", "ck",
     [('    if m and m.group(2) == "CATCH" and m.group(3).startswith("trainee "):',
       '    if m and m.group(2) == "CATCH" and m.group(3).startswith("trainee"):')], {"S3e"}),
    ("K41 STOP-3 a run end maps to the FIRST log opened", "ck",
     [("            if start < m.start():\n                log = name", "            if start < m.start() and log is None:\n                log = name")],
     {"QS5", "S3h"}),   # PREDICTION: QS5's second run maps to the first log; FOLD-PREDICTION: so does S3h's lane H9
    ("K42 STOP-3 the raw outcome is the signature", "ck",
     [('"signature": None if bucket == "finished" else x4._derail_reason(outcome), "log": log})',
       '"signature": None if bucket == "finished" else outcome, "log": log})')],
     {"QS5", "S3a", "S3c", "S3d", "S3f", "S3g", "S3h", "X3"}),   # every pair differs only in its loss count
    ("K43 STOP-3 'yes' without a tag", "ck", [("        found = any(t for _l, _r, t in rows)", "        found = True")],
     {"S3c", "S3d", "S3f", "S3h"}),
    ("K101 [S3-10] the pattern needs a tag in EVERY qualifying tail", "ck",
     [("        found = any(t for _l, _r, t in rows)", "        found = all(t for _l, _r, t in rows)")], {"S3h"}),
    ("K102 the count of untagged qualifying signatures not printed (always 0)", "ck",
     [('    no_tag = sum(1 for q in qualifying if not q["tags_found"])', "    no_tag = 0")], {"S3f", "S3h"}),
    # ---- extraction (the tables' inputs)
    ("K44 D-fence keeps the numbers", "ck", [('    return re.sub(r"\\d[\\d,]*", "N", text)', "    return text")],
     {"QS4", "T8"}),
    ("K45 D-fence era never switches", "ck", [("                        era = \"after\"", "                        pass")],
     {"T8", "T27"}),
    ("K46 leg 11 money read AFTER the load", "ck",
     [('                    out["leg11_loaded"], out["leg11_money"] = True, money', '                    out["leg11_loaded"] = True')],
     {"T9"}),
    ("K47 the old leg-11 text not matched", "ck", [('LEG11_OLD = "Ch23 leg 11: the basket costs ₽"',
                                                   'LEG11_OLD = "Ch23 leg 11: the basket cost ₽"')], {"T7"}),
    # EQUIVALENT (documented, the hunter's TG-03 reason): the current refusal has ONE emitter (victory_road.py:3524)
    # and its "short by" falls at characters 179-187, inside the derail message's 200-character cut (:3949) — no real
    # line carries the first half without the second, so no real log can tell these apart.
    ("K48 the current text needs only its first half", "ck",
     [('LEG11_NEW = ("Ch23 leg 11: the missing basket lines", "short by")', 'LEG11_NEW = ("Ch23 leg 11: the missing basket lines",)')],
     set()),
    # RE-ANCHORED with KI-119 (the tag is the catch line's own badges= now)
    ("K49 a catch's badge count not recorded", "ck",
     [('int(bg.group(1)) if bg else max(out["badges"], default=0)))', "0))")],
     {"T5", "TS1", "TS2", "GK18", "TS9"}),   # FOLD: + GK18 (adoption), TS9 (a catch at 0 is no badge evidence)
    ("K50 the battle map not recorded", "ck", [('            recs[k]["map"] = cur_map', "            pass")], {"T6"}),
    # NOT equivalent after all (the builder, on the fold): a run CUT inside a catch battle has its start and no end
    ("K51 a WILD battle with a [CATCH] start is not a catch battle", "ck",
     [('                    if k >= 0:\n                        recs[k]["catch"] = True\n                else:',
       '                    if False:\n                        recs[k]["catch"] = True\n                else:')], {"T26"}),
    ("K52 [KIT-BUY] items not parsed", "ck", [('        if bm and bm.group(1).startswith("{"):', "        if False:")],
     {"QS3", "T9", "T16"}),
    ("K53 money spent sign flipped", "ck",
     [('"spent": (a - b) if a is not None and b is not None else None,', '"spent": (b - a) if a is not None and b is not None else None,')],
     {"QS3", "T9", "T16"}),
    ("K54 weaken stage ignored", "ck", [('            stage = reason.split(":", 1)[0] if reason.startswith(("stage1:", "stage2:")) else "-"',
                                        '            stage = "-"')], {"QS4", "T12", "TS4"}),
    ("K55 M1b de-dup keeps the frames", "ck",
     [('        key = hashlib.sha1("\\n".join(re.sub(r"^f\\d+ ", "", s) for s in block).encode("utf-8")).hexdigest()',
       '        key = hashlib.sha1("\\n".join(block).encode("utf-8")).hexdigest()')],
     {"T11"}),   # PREDICTION: X4's two blocks carry the SAME frames, so they de-duplicate anyway
    ("K56 M1b the last block dropped", "ck", [("    if block and m1b is not None:\n        m1b.add(block)", "    pass")],
     {"T11", "X4", "TS4"}),
    ("K57 the first attempt = the LAST attempt", "ck",
     [('        fa = first[key]\n', '        fa = None\n        for _k2 in range(len(battles) - 1, -1, -1):\n'
                                   '            if fa is None and recs[_k2]["starts"] & idset and recs[_k2]["ends"] & idset:\n'
                                   '                fa = {"index": _k2, "outcome": recs[_k2]["outcome"], "heal_stock": recs[_k2]["heal_stock"]}\n')],
     {"T1", "E4b", "E4c"}),   # PREDICTION: D-lead's rates read compare_arms' records, and no fixture lead depends on it
    ("K58 a rival's six ids are six trainers (only the first kept)", "ck",
     [('    "RIVAL_ROUTE_103": (520, 523, 526, 529, 532, 535),', '    "RIVAL_ROUTE_103": (520,),')], {"T1"}),
    # FIRST RUN: (270,) — Winona's id — made the module refuse to IMPORT (`_check_trainers`); that guard is K66 now
    ("K59 Tate & Liza's id wrong", "ck", [('"TATE_AND_LIZA": (271,)', '"TATE_AND_LIZA": (273,)')],
     {"E4a", "E4b", "E4c", "E4e", "R1", "T1", "T4", "T21", "TS6", "GK15"}),   # TS6 / GK15: LEADER_BADGE reads 271
    ("K66 two trainers share an id -> the module refuses to import", "ck",
     [('"TATE_AND_LIZA": (271,)', '"TATE_AND_LIZA": (270,)')], "RAISES"),
    ("K63 the heal marker also matches the 'withdraw result' line", "ck",
     [('_HEAL_MARK = re.compile(r"^Story: PC — \\S+ withdraw: ")', '_HEAL_MARK = re.compile(r"^Story: PC — \\S+ withdraw")')],
     {"QS1"}),
    ("K64 [MAP] from and to swapped", "ck",
     [("    return (int(m.group(1)), int(m.group(2))), (int(m.group(3)), int(m.group(4)))",
       "    return (int(m.group(3)), int(m.group(4))), (int(m.group(1)), int(m.group(2)))")],
     {"QS1", "E3d", "E3e", "E3g", "E3h", "E3i", "E3j", "T7", "T8", "T9", "X1", "TS3", "GK11"}),   # no Rustboro heal is seen
    # FOLD-PREDICTION (K64): T27 survives it by symmetry — swapped, the flick's RETURN read lands on (0,7) and the real
    # Sootopolis load lands on (24,43), so the two runs trade eras and the totals stay 1 / 1 (T8 still kills it)
    ("K65 K* COPIED into TRAINERS (equal values, not compare_arms' objects)", "ck",
     [("    **ca.KSTAR,", "    **{k: list(v) for k, v in ca.KSTAR.items()},")], {"R1"}),
    # ---- the loader
    ("K60 the loader never extracts", "ck",
     [("        record[\"t4\"] = extract(lines, forbid=forbid, m1b=m1b)", "        pass")],
     {"X1", "X3", "X4", "X5", "X6"}),
    ("K61 a control failure still checks", "ck",
     [('    results = None if b["failures"] else run_checks(b)', "    results = run_checks(b)")], {"X2"}),
    ("K62 the stdout of the wrong lane", "ck",
     [('        p = batch_dir / f"L{lane[\'slot\'] + 1:02d}" / "stdout.txt"', '        p = batch_dir / f"L{lane[\'slot\'] + 2:02d}" / "stdout.txt"')],
     {"X3"}),
    ("K103 RULING 8 REVERTED: the header has no C1-C2 VOID line", "ck",
     [("""            f"  C1-C2         {'VOID: ' + b['void'] + ' (DESIGN §4)' if b.get('void') else 'not void'}"]""",
       "            ]")], {"X1", "X6"}),
    ("K104 --void ignored (only summary.json's verdict voids)", "ck",
     [('            "void": ca.void_reason(summ, manual_void)}', '            "void": ca.void_reason(summ)}')], {"X6"}),
    # ---- the tables
    ("T01 funnel eligible counts every run", "tb",
     [("                elif t is not None or r[\"status\"] == \"complete\":", "                else:")], {"T1"}),
    ("T111 [TF-02] D-funnel: a run censored DURING its attempt counts as eligible", "tb",
     [("                if ca.censored_during(pseudo, key):\n                    pass", "                if False:\n                    pass")],
     {"T17"}),
    ("T02 [BT02] funnel counts unbeaten CUT runs", "tb",
     [("                if t is not None and not t[\"won_ever\"] and r[\"status\"] == \"complete\":",
       "                if t is not None and not t[\"won_ever\"]:")], {"T20"}),
    ("T03 funnel eventually = first", "tb",
     [('                if t is not None and t["won_ever"]:', '                if won is True:')], {"T1"}),
    ("T04 the K* cross-check never differs (killed by its fault-injected row, not called equivalent)", "tb",
     [("            if any(mine[f] != theirs[f] for f in theirs):", "            if False:")], {"T25"}),
    ("T05 frame-cap ends not counted", "tb",
     [('                   for x in s["runs"] if x["bucket"] == "frame_cap")', '                   for x in s["runs"] if x["bucket"] == "frame-cap")')],
     {"T2"}),
    ("T06 D-attempt counts first attempts only", "tb",
     [('                if rec["cls"] != bl.KEY or rec["group"] is None:', '                if rec["cls"] != bl.KEY or rec["group"] is None or rec["outcome"] == "lost":')],
     {"T3"}),
    ("T07 [BT07] D-boss counts met as decided", "tb",
     [('            rows[key] = {"met": sum(t is not None for t in ts), "decided": sum(w is not None for w in won),',
       '            rows[key] = {"met": sum(t is not None for t in ts), "decided": sum(t is not None for t in ts),')],
     {"T21"}),
    ("T08 D-boss prints a rate for nobody", "tb",
     [('if r["decided"] else f"NOT ASSESSED ({r[\'met\']})"))', 'if r["decided"] else f"0/0 ({r[\'met\']})"))')],
     {"T4", "T21"}),
    ("T09 [BT09] D-lead counts PRE-badge catches", "tb",
     [('    caught = {sp for sp, badges in run["t4"]["caught"] if badges >= 1}', '    caught = {sp for sp, badges in run["t4"]["caught"]}')],
     {"T22", "TS2"}),
    ("T113 [TLd-01] D-lead's denominator = every key trainer MET", "tb",
     [('            den += sum(1 for t in r["t4"]["trainers"].values() if t["first_k"] is not None)',
       '            den += len(r["t4"]["trainers"])')], {"T24"}),
    ("T109 RULING 8 REVERTED: D-lead's C2 rates never marked VOID", "tb",
     [('    if d.get("void"):\n        out.append(f"  ⛔ C1-C2 VOID:', '    if False:\n        out.append(f"  ⛔ C1-C2 VOID:')],
     {"T15", "X6"}),
    ("T110 RULING 9 REVERTED: 'evolved catches are missed' dropped from D-lead's label", "tb",
     [('           f"evolved catches are missed"]', '           f"species-level"]')], {"T5"}),
    ("T10 D-lead never drops", "tb",
     [('            keys = {k: (dict(v, won=None, attempted=False) if k in excluded.get(r["log"], set()) else v)',
       '            keys = {k: (v if k in excluded.get(r["log"], set()) else v)')], {"T5"}),
    ("T11 D-lead label dropped", "tb", [('LEAD_LABEL = "conditioned on a post-treatment variable"', 'LEAD_LABEL = "post-catch leads"')],
     {"T5"}),
    ("T12 D-loss: a Draw is not a loss", "tb", [('                lost = rec["outcome"] == "lost"', '                lost = False')],
     {"T6"}),
    ("T105 [TL-02] D-loss: 'other' outcomes (Caught, OpponentTeleported) counted as losses", "tb",
     [('                lost = rec["outcome"] == "lost"', '                lost = rec["outcome"] != "won"')], {"T6", "T18"}),
    ("T13 D-loss: catch battles folded into other wild", "tb",
     [('                    name = "wild catch" if rec["catch"] else "other wild"', '                    name = "other wild"')],
     {"T6", "T18", "T26"}),
    ("T14 D-leg11 counts any refusal as loaded", "tb",
     [('                    "refused_loaded": sum(1 for r in refused if r["t4"]["leg11_loaded"]),',
       '                    "refused_loaded": len(refused),')], {"T7"}),
    ("T15 D-fence label dropped", "tb", [('FENCE_LABEL = "distinct pairs, not frequency"', 'FENCE_LABEL = "pairs"')],
     {"T8"}),
    ("T16 D-economy topoff… by ball counts mandatory too", "tb",
     [('                if x["why"].startswith("topoff"):', '                if True:')], {"T9"}),
    ("T17 D-economy T1 per map ignored", "tb", [('                    row["delta"] += delta or 0', '                    row["delta"] += 0')],
     {"T9"}),
    ("T18 D-rare: the species-level column read from the line's suffix (A has none)", "tb",
     [("                for table, is_rare in ((rows, _offline_rare(dex)),",
       "                for table, is_rare in ((rows, rare not in (None, '-')),")], {"T10"}),
    ("T19 D-rare: B rare=- counted as rare", "tb",
     [('                                       (line_rows, arm == ck.ARM_B and rare not in (None, "-"))):',
       '                                       (line_rows, arm == ck.ARM_B and rare is not None)):')],
     {"T10"}),   # GAP (first run: survived — no B catch read rare=-): the fixture now holds a rare=- Poochyena
    ("T106 RULING 9 REVERTED: B's species-level column uses B's own suffix (not comparable with A)", "tb",
     [("                for table, is_rare in ((rows, _offline_rare(dex)),",
       "                for table, is_rare in ((rows, _offline_rare(dex) if arm == ck.ARM_A else rare not in (None, '-')),")],
     {"T10"}),
    ("T112 [TD-02] D-fence distinct over the whole ARM, not per run", "tb",
     [('        unparsed = 0\n        for r in usable_runs(runs, arm):\n            unparsed += r["t4"]["fence_unparsed"]\n'
       '            for era, verb, _species, reason in r["t4"]["fence"]:\n',
       '        unparsed = 0\n        _seen = set()\n        for r in usable_runs(runs, arm):\n'
       '            unparsed += r["t4"]["fence_unparsed"]\n'
       '            for era, verb, _species, reason in sorted(r["t4"]["fence"] - _seen):\n'
       '                _seen.add((era, verb, _species, reason))\n')], {"T19"}),
    ("T107 RULING 4 REVERTED: the package row sums LINES (a joint errand counted twice)", "tb",
     [('                    e = errands.setdefault((r["log"], x["frame"], x["money"]), {"kinds": set(), "spent": x["spent"]})\n'
       '                    e["kinds"].add("ball")',
       '                    e = errands.setdefault((r["log"], x["frame"], x["money"], "b"), {"kinds": set(), "spent": x["spent"]})\n'
       '                    e["kinds"].add("ball")')], {"T16"}),
    ("T108 the 'joint errands counted in both' label dropped", "tb",
     [('    joint = "errand money, joint errands counted in both"', '    joint = "money"')], {"T16"}),
    ("T20 D-weaken: A and B merged", "tb",
     [('    return {arm: dict(sum((r["t4"]["weaken"] for r in usable_runs(runs, arm)), collections.Counter()))',
       '    return {arm: dict(sum((r["t4"]["weaken"] for r in runs if r.get("t4")), collections.Counter()))')],
     {"T12"}),
    ("T21 D-throughput: spawns of the other arm", "tb",
     [('                if ln.get("arm") != arm:', '                if ln.get("arm") == arm:')],
     {"T13"}),   # GAP (first run: survived — both arms had 1.0 lane-hours): B's lane-hours are now 2.0
    ("T22 a verdict word in a table", "tb",
     [('    out = ["D-weaken — [WEAKEN-OBS] would= by verdict and stage', '    out = ["D-weaken — PASS [WEAKEN-OBS] would= by verdict and stage')],
     {"T14"}),
    ("T23 [BT23] the tables read EXCLUDED runs", "tb",
     [('    return [r for r in runs if ca.usable(r) and r["arm"] == arm and r.get("t4")]',
       '    return [r for r in runs if r.get("lane_arm") == arm and r.get("t4")]')], {"T23"}),
    ("T24 a control failure still prints tables", "tb",
     [('    if b["failures"]:\n        print("\\n".join(head + ["=" * 100]))\n        return 1', "    pass")], {"X2"}),
    ("T25 the M1b pool is never written", "tb",
     [('    handle = open(args.m1b_out, "w", encoding="utf-8", newline="\\n") if args.m1b_out else None',
       "    handle = None")], {"X4"}),
    # ---- compare_arms' visit hook (the one refactor)
    # FIRST RUN: both also reddened R1 — a harness artifact (R1 compared against the RE-EXEC'D compare_arms); R1 now
    # compares against the real module's K*, captured at import
    ("C01 the visit hook never called", "ca",
     [("            if visit is not None:\n                visit(runs[-1], got[0])", "            pass")],
     {"R2", "X1", "X3", "X4", "X5", "X6"}),
    ("C02 the visit hook called twice", "ca",
     [("            if visit is not None:\n                visit(runs[-1], got[0])",
       "            if visit is not None:\n                visit(runs[-1], got[0])\n                visit(runs[-1], got[0])")],
     {"R2", "X4"}),   # PREDICTION: the M1b pool counts each block twice
    # ---- KI-119 (`#27-gradeidentity`): one REVERT per rule of the build, sets written before the fix's first run
    ("K-SB1 REVERT: whole-log [BADGE] setdefault + the max-badge catch tag (the frozen reader)", "ck",
     [('        elif r == "trainer" and progress:', '        elif r == "trainer" and False:'),
      ('                if progress:\n                    out["badge_lines"].setdefault(int(bm.group(1)), frame)\n'
       '                else:\n                    out["badge_pre_start"] += 1\n',
       '                out["badges"].setdefault(int(bm.group(1)), frame)\n'),
      ('int(bg.group(1)) if bg else max(out["badges"], default=0)))', 'max(out["badges"], default=0)))')],
     {"TS1", "TS2", "TS3", "TS5", "TS6", "GK16", "GK18", "GK19", "TS7", "TS8", "TS9"}),   # FOLD: + GK16 GK18 GK19
    ("K-SB2 KI-119's LITERAL fix: [BADGE] read after the start, no leader-win source, no poison count", "ck",
     [('        elif r == "trainer" and progress:', '        elif r == "trainer" and False:'),
      ('                if progress:\n                    out["badge_lines"].setdefault(int(bm.group(1)), frame)\n'
       '                else:\n                    out["badge_pre_start"] += 1\n',
       '                if progress:\n                    out["badges"].setdefault(int(bm.group(1)), frame)\n'),
      ('int(bg.group(1)) if bg else max(out["badges"], default=0)))', 'max(out["badges"], default=0)))')],
     {"TS1", "TS2", "TS5", "TS6", "GK16", "GK18", "GK19", "TS7", "TS8", "TS9"}),   # FOLD: + GK16 GK18 GK19, TS7-9
    ("K-SB3 money read before the start", "ck",
     [('        elif cat == "MONEY" and progress:', '        elif cat == "MONEY":'),
      ('        elif cat == "hb" and progress:', '        elif cat == "hb":')], {"TS3", "GK11"}),
    ("K-SB4 the boundary applied to CORRECTNESS: the battles", "ck",
     [("    battles = [b for b in bl.split_battles(lines) if b.started]",
       "    battles = [b for b in bl.split_battles(lines[start + 1:] if start is not None else []) if b.started]")],
     {"TS4", "GK10", "GK13"}),   # FOLD: GK10 / GK13's battles sit before (or without) a start
    ("K-SB4b the boundary applied to CORRECTNESS: the monitor", "ck",
     [("x4.scan_lines(lines, list(forbid), ())[0]",
       "x4.scan_lines(lines[start + 1:] if start is not None else [], list(forbid), ())[0]")], {"TS4"}),
    ("K-SB4c the boundary applied to CORRECTNESS: [DMGAUDIT]", "ck",
     [('        elif cat == "DMGAUDIT":', '        elif cat == "DMGAUDIT" and progress:')], {"TS4"}),
    ("K-SB4d the boundary applied to CORRECTNESS: [WEAKEN-OBS]", "ck",
     [('        elif cat == "WEAKEN" and "[WEAKEN-OBS] " in msg:',
       '        elif cat == "WEAKEN" and "[WEAKEN-OBS] " in msg and progress:')], {"TS4"}),
    ("K-SB4e the boundary applied to CORRECTNESS: the whole [CATCH] reader (E3's dex-loss filing)", "ck",
     [('        elif cat == "CATCH":', '        elif cat == "CATCH" and progress:')], {"TS4"}),
    ("K-SB4f the boundary applied to CORRECTNESS: STOP-3's tail", "ck",
     [('"tail": tail_of(lines),', '"tail": tail_of(lines[start + 1:] if start is not None else []),')], {"TS4"}),
    ("K-SB5 the map (era, leg 11, the Rustboro heal) read before the start", "ck",
     [('        elif cat == "MAP" and progress:', '        elif cat == "MAP":')], {"TS3", "GK10", "GK12"}),
    ("K-SB5b only cur_map read before the start (era and leg 11 still bounded)", "ck",
     [('        elif cat == "MAP" and progress:',
       '        elif cat == "MAP" and not progress:\n            mm = parse_map(msg)\n            if mm:\n'
       '                cur_map = mm[1]\n        elif cat == "MAP":')], {"TS3"}),
    ("K-SB7 leader wins read before the start", "ck",
     [('        elif r == "trainer" and progress:', '        elif r == "trainer":')], {"TS3", "GK10"}),
    ("K-SB8 catches read before the start", "ck",
     [('                    if end_v == "caught" and progress:', '                    if end_v == "caught":')],
     {"TS3", "GK10", "GK13"}),
    ("K-SB9 the catch tag from the leader-win count, not the line's own badges= (equal on 723/723 REAL lines)", "ck",
     [('int(bg.group(1)) if bg else max(out["badges"], default=0)))', 'max(out["badges"], default=0)))')],
     {"T5", "GK17", "TS9"}),
    ("K-SB10 a catch line with no badges= is tagged 0", "ck",
     [('int(bg.group(1)) if bg else max(out["badges"], default=0)))', "int(bg.group(1)) if bg else 0))")], {"TS1", "GK18"}),
    # FOLD: adoption.txt adds GK19 here, measured on the PRE-fold rule; under GS-5 a run WITH [BADGE] lines after its
    # start is compared even when poisoned, so GK19's run stays listed — the set stays {TS5} (a prediction)
    ("K-SB11 the poison count reads [BADGE] lines AFTER the start too", "ck",
     [('                else:\n                    out["badge_pre_start"] += 1\n',
       '                out["badge_pre_start"] += 1\n')], {"TS5"}),
    ("K-SB12 a badge's frame is the LAST win over its leader", "ck",
     [('                        out["badges"].setdefault(LEADER_BADGE[i], frame)',
       '                        out["badges"][LEADER_BADGE[i]] = frame')], {"TS1"}),
    ("K-SB13 a LOST leader battle counts as the badge", "ck",
     [('            if t and t["kind"] == "end" and t["res"] == "Won" and frame is not None:',
       '            if t and t["kind"] == "end" and frame is not None:')], {"TS6", "GK14"}),
    ("K-SB14 the leaders' badge numbers off by one (Roxanne = badge 0)", "ck",
     [("LEADER_BADGE = {TRAINERS[name][0]: n for n, name in enumerate(BADGE_LEADERS, 1)}",
       "LEADER_BADGE = {TRAINERS[name][0]: n for n, name in enumerate(BADGE_LEADERS)}")],
     {"T2", "TS1", "TS5", "TS6", "GK15", "GK16", "GK18", "GK19"}),
    ("K-SB15 extract's boundary = the 'Intro: New Game' step (else the choosing line)", "ck",
     [("    start = bl.run_start(lines)",
       '    start = next((i for i, s in enumerate(lines) if "Intro: New Game" in s), bl.run_start(lines))')],
     {"TS1", "TS3", "GK11", "GK12", "GK13"}),
    ("K-SB16 extract's boundary = the LAST party clear (else the choosing line)", "ck",
     [("    start = bl.run_start(lines)",
       '    start = ([i for i, s in enumerate(lines) if re.search(r"\\[PARTY\\] size \\d+ -> 0:", s)]'
       " or [bl.run_start(lines)])[-1]")], {"TS1", "TS3", "GK11", "GK12", "GK13"}),
    ("TT1 the poisoned count reads any run with a [BADGE] line", "tb",
     [('        poisoned = [r for r in rs if r["t4"]["badge_pre_start"]]',
       '        poisoned = [r for r in rs if r["t4"]["badge_pre_start"] or r["t4"]["badge_lines"]]')], {"TS5"}),
    ("TT2 the disagreement list never fills", "tb",
     [('                    and set(r["t4"]["badge_lines"]) != set(r["t4"]["badges"])]', "                    and False]")],
     {"TS5", "TS8", "GK19"}),
    # RE-ANCHORED with GS-5 (the disagreement also reads a poisoned run that has [BADGE] lines after its start)
    ("TT3 the disagreement read on POISONED runs too", "tb",
     [('        disagree = [r for r in rs if (r["t4"]["badge_lines"] or not r["t4"]["badge_pre_start"])\n',
       "        disagree = [r for r in rs if True\n")],
     {"TS5"}),
    ("TT4 the control counts not printed", "tb",
     [("""\"poisoned by a boot-loaded save): " + "   ".join(f"{arm} {f[arm]['badge_poisoned']}" for arm in ARMS)""",
       """\"poisoned by a boot-loaded save): " + "   ".join(f"{arm} -" for arm in ARMS)""")], {"TS5"}),
    ("TT5 the badge source not printed", "tb",
     [("""    out.append("  badge source (KI-119): badge n = the run's first [TRAINER] end res=Won over gym leader n \"""",
       """    _unused = ("  badge source (KI-119): badge n = the run's first [TRAINER] end res=Won over gym leader n \"""")],
     {"TS5"}),
    ("TT6 the disagreeing runs not listed", "tb",
     [('            out.append(f"    arm {arm} {name}: [BADGE] {got} vs leader wins {wins}")', "            pass")],
     {"TS5"}),
    ("MS1 MENTION ONLY: a comment quoting the frozen [BADGE] reader and f301", "ck",
     [("#: are a CONTROL only: a boot-loaded Hall-of-Fame save logs all 8 at f301, and the bot's recorder then never logs the",
       '#: are a CONTROL only (never `out["badges"].setdefault(int(bm.group(1)), frame)`; f301 [BADGE] n=8); the bot never logs the')],
     set()),
    # ---- THE INDEPENDENT REVIEW'S FOLD (2026-10-02): the mutant hunter's survivors ([GH<n>], `adv27/gihunt/hunt.py`)
    # and one REVERT per GS-5 / GS-6 rule; every set written BEFORE the fold's first run
    ("K-SB21 [GH33] progress FAIL-OPEN without a choosing line", "ck",
     [("        progress = start is not None and pos > start", "        progress = start is None or pos > start")],
     {"GK10"}),
    ("K-SB22 [GH34] the [MONEY] line read before the start ([hb] money still bounded)", "ck",
     [('        elif cat == "MONEY" and progress:', '        elif cat == "MONEY":')], {"GK11"}),
    ("K-SB23 [GH36] leg 11 (the (16,10) load) read before the start; era / cur_map / Rustboro still bounded", "ck",
     [('        elif cat == "MAP" and progress:',
       '        elif cat == "MAP" and not progress:\n            mm = parse_map(msg)\n'
       '            if mm and mm[1] == LEAGUE_1F and not out["leg11_loaded"]:\n'
       '                out["leg11_loaded"], out["leg11_money"] = True, money\n'
       '        elif cat == "MAP" and progress:')], {"GK10", "GK12"}),
    ("K-SB24 [GH39] a catch before the start counted when it sits inside a battle", "ck",
     [('                    if end_v == "caught" and progress:',
       '                    if end_v == "caught" and (progress or k >= 0):')], {"GK10", "GK13"}),
    ("K-SB25 [GH40, LIVE on step 14] a leader DRAW counts as the badge", "ck",
     [('            if t and t["kind"] == "end" and t["res"] == "Won" and frame is not None:',
       '            if t and t["kind"] == "end" and t["res"] != "Lost" and frame is not None:')], {"GK14"}),
    ("K-SB26 [GH41, LIVE] BADGE_LEADERS: Flannery and Norman swapped (badges 4 <-> 5)", "ck",
     [('"FLANNERY", "NORMAN", "WINONA"', '"NORMAN", "FLANNERY", "WINONA"')], {"GK15"}),
    ("K-SB27 [GH42, LIVE] BADGE_LEADERS: Wattson and Flannery swapped (badges 3 <-> 4)", "ck",
     [('"WATTSON", "FLANNERY", "NORMAN"', '"FLANNERY", "WATTSON", "NORMAN"')], {"GK15"}),
    ("K-SB28 [GH44, LIVE] BADGE_LEADERS: Juan dropped (no badge 8 from a win)", "ck",
     [('"TATE_AND_LIZA", "JUAN")', '"TATE_AND_LIZA")')], {"GK15"}),
    ("K-SB29 [GH45] extract's boundary = the LAST choosing line", "ck",
     [("    start = bl.run_start(lines)",
       "    start = max((i for i, s in enumerate(lines) if bl._CHOSEN.search(s)), default=None)")], {"GK16"}),
    ("K-SB30 [GH46] the catch tag = max(the line's badges=, the leader wins so far)", "ck",
     [('int(bg.group(1)) if bg else max(out["badges"], default=0)))',
       'max(int(bg.group(1)), max(out["badges"], default=0)) if bg else max(out["badges"], default=0)))')],
     {"GK17"}),
    ("K-SB31 [GH47] a catch line without badges= takes the COUNT of leader-win badges, not the highest", "ck",
     [('int(bg.group(1)) if bg else max(out["badges"], default=0)))', 'int(bg.group(1)) if bg else len(out["badges"])))')],
     {"GK18"}),
    ("K-SB32 GS-5: the catch-tag control compares the line's field with ITSELF (never differs)", "ck",
     [('out["catch_badges"].append((int(bg.group(1)), len(out["badges"])))',
       'out["catch_badges"].append((int(bg.group(1)), int(bg.group(1))))')], {"TS7"}),
    ("K-SB33 GS-5: badges never 'unknown' (a run without telemetry reads 0)", "ck",
     [('    out["badges_unknown"] = not telemetry and bool(', '    out["badges_unknown"] = False and bool(')], {"TS9"}),
    ("K-SB34 GS-5: badges 'unknown' for EVERY run without telemetry (evidence of badges not required)", "ck",
     [("""    out["badges_unknown"] = not telemetry and bool(out["badge_lines"] or any(t >= 1 for _s, t in out["caught"]))""",
       '    out["badges_unknown"] = not telemetry')], {"TS9"}),
    ("K-SB35 GS-6: the checks / tables headers drop the choosing-line control", "ck",
     [('    odd = info.get("choosing_not_one") or []', "    odd = []")], {"X7"}),
    ("TT7 GS-5 REVERT: a POISONED run's [BADGE] lines after its start are never compared", "tb",
     [('        disagree = [r for r in rs if (r["t4"]["badge_lines"] or not r["t4"]["badge_pre_start"])\n',
       '        disagree = [r for r in rs if not r["t4"]["badge_pre_start"]\n')], {"TS8"}),
    ("TT8 GS-5: the catch-tag control skips POISONED runs", "tb",
     [('        tags = [x for r in rs for x in r["t4"]["catch_badges"]]',
       '        tags = [x for r in rs if not r["t4"]["badge_pre_start"] for x in r["t4"]["catch_badges"]]')], {"TS7"}),
    ("TT9 GS-5: the catch-tag control not printed", "tb",
     [("""f"{arm} {f[arm]['catch_tags'][0]} lines, {f[arm]['catch_tags'][1]} differ\"""", '''f"{arm} -"''')], {"TS7"}),
    ("TT10 GS-5: an 'unknown' run counted as 0 badges", "tb",
     [('"unknown" if r["t4"]["badges_unknown"] else max(r["t4"]["badges"], default=0)', 'max(r["t4"]["badges"], default=0)')],
     {"TS9"}),
    ("TT11 [GH52] the disagreement compares the HIGHEST badge only, not the sets", "tb",
     [('                    and set(r["t4"]["badge_lines"]) != set(r["t4"]["badges"])]',
       '                    and max(r["t4"]["badge_lines"], default=0) != max(r["t4"]["badges"], default=0)]')],
     {"GK19"}),
    ("TT12 GS-5: the 'unknown' count not printed", "tb",
     [("""" + "   ".join(f"{arm} {f[arm]['badges_unknown']}" for arm in ARMS))""",
       """" + "   ".join(f"{arm} -" for arm in ARMS))""")], {"TS9"}),
    # ---- mention-only edits turn NOTHING red
    ("M01 MENTION ONLY: a comment quoting a mutant's text", "ck",
     [("#: E2: DESIGN AI-6 — `flag_off` cannot reach a log line, so one that does is a violation.",
       "#: E2: DESIGN AI-6 — never `if len(kb) > 2:`; `flag_off` cannot reach a log line, so one that does is one.")],
     set()),
    ("M02 MENTION ONLY: a docstring naming a tag", "tb",
     [("    \"\"\"The runs a table reads: compare_arms' `usable` runs of `arm` that were read (a `t4` record).\"\"\"",
       "    \"\"\"The runs a table reads (never `[ITEM] using` lines): compare_arms' `usable` runs of `arm` (a `t4` record).\"\"\"")],
     set()),
]


def _apply(src: str, edits) -> str:
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise AssertionError(f"mutant anchor found {n} times: {old[:90]!r}")
        src = src.replace(old, new)
    return src


def _install(key: str, source: str, i: int) -> None:
    mod = types.ModuleType(NAMES[key])
    mod.__file__ = str(PATHS[key])
    sys.modules[NAMES[key]] = mod
    exec(compile(source, f"<mutant {i}>", "exec"), mod.__dict__)
    if key == "ck":
        sys.modules["batch14_tables"].ck = mod
    elif key == "ca":
        sys.modules["batch14_checks"].ca = mod
        sys.modules["batch14_tables"].ca = mod


def all_rows(verbose: bool) -> set:
    reds = set()
    _TR.clear()
    for rid, label, fn in ROWS:
        try:
            ok, detail = fn()
        except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
            ok, detail = False, f"raised {type(error).__name__}: {error}"
        if not ok:
            reds.add(rid)
        if verbose:
            check(f"{rid} {label}", ok, detail)
    return reds


def run_mutant(i: int, target: str, edits) -> "tuple[set | None, str]":
    real = {k: sys.modules[v] for k, v in NAMES.items()}
    saved_tmp = dict(TMP)
    try:
        src = _apply(PATHS[target].read_text(encoding="utf-8"), edits)
        _install(target, src, i)
        with tempfile.TemporaryDirectory(prefix="b14-mut-") as tmp:
            TMP["root"] = pathlib.Path(tmp)
            return all_rows(False), ""
    except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
        return None, f"{type(error).__name__}: {error}"
    finally:
        for k, v in NAMES.items():
            sys.modules[v] = real[k]
        real["tb"].ck = real["ck"]
        real["ck"].ca = real["ca"]
        real["tb"].ca = real["ca"]
        TMP.clear()
        TMP.update(saved_tmp)


def _pool_job(i: int):
    _label, target, edits, _want = MUTANTS[i]
    red, err = run_mutant(i, target, edits)
    return i, (sorted(red) if red is not None else None), err


def run_all_mutants(serial: bool) -> list:
    if serial:
        return [run_mutant(i, t, e) for i, (_l, t, e, _w) in enumerate(MUTANTS)]
    import concurrent.futures
    import os
    out: list = [None] * len(MUTANTS)
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
        for i, red, err in pool.map(_pool_job, range(len(MUTANTS)), chunksize=2):
            out[i] = (set(red) if red is not None else None, err)
    return out


def main() -> int:
    global SMOKE, BATCH14
    t0 = time.perf_counter()
    SMOKE = BL().main_story_dev() / "x4-runs" / "20261001-090649"
    BATCH14 = BL().main_story_dev() / "x4-runs" / "20261001-210001"
    with tempfile.TemporaryDirectory(prefix="b14-gate-") as tmp:
        TMP["root"] = pathlib.Path(tmp)
        print("PROVENANCE — the gate's own data")
        provenance()
        print("\nROWS — the real modules")
        baseline = all_rows(True)
        if "--rows-only" in sys.argv:
            print("\n‼ --rows-only: the MUTANTS were NOT run. THIS IS NOT THE GATE.")
            FAILURES.append("--rows-only (the mutant half was skipped)")
        else:
            print(f"\nMUTANTS — each must turn EXACTLY its named rows red ({len(MUTANTS)}; a process pool)")
            covered: set = set()
            for (label, target, edits, want), (red, err) in zip(MUTANTS, run_all_mutants("--serial" in sys.argv)):
                if want == "RAISES":         # the mutant must make the module refuse to load (an import-time guard)
                    check(label, red is None and "AssertionError" in err, err or f"loaded; red {sorted(red)}")
                    continue
                if red is None:
                    check(label, False, err)
                    continue
                red = set(red) - baseline
                want_now = set(want) - baseline
                covered |= set(want)
                check(label, red == want_now, f"red {sorted(red)}" + ("" if red == want_now else f" (want {sorted(want_now)})"))
            uncovered = sorted(ROW_NAMES - covered)
            check("COVERAGE every row is in at least one mutant's expected red set", not uncovered,
                  f"{len(ROW_NAMES)} rows; uncovered {uncovered}")
    wall = time.perf_counter() - t0
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s) in {wall:.1f} s:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL PASS ({len(ROW_NAMES)} rows, {len(MUTANTS)} mutants, {len(QUOTES)} quoted lines) in {wall:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
