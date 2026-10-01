r"""GATE G-IP — `#27-itemprobes` (`ai-research-notes/2026-09-30-itemprobes-DESIGN.md` D5): the shared parser
`battle_log.py` and the two item instruments built on it, `probe_boss_healing.py` and `probe_item_index_space.py`.

WHY. Design v2 §Step 14 grades the key-battle item policy on those two probes, and on 2026-09-30 both were blind on
current logs (an 8.5% `[TURN]` miss on foe status suffixes; three retired `[ITEM]` kinds; no battle classification).
A measurement that silently drops lines reports "zero" where it should report "could not look" — so every parser
decision here is pinned on REAL lines, and every pin is proven able to fail.

ROWS (each a function; a row that raises is red)
  RT*  routing: which part of a battle record a line belongs to (`[ITEM-FLOW]` is NOT an item line).
  TU*  `[TURN]`: the FIXED pattern (a foe status suffix parses; a player suffix is not the foe's; `vs ?` is NO FOE
       DATA, never parsed, never "missed").
  HE*  `foe_heals` (identity `(foe, max_hp)`; strict rise).
  IK*  `[ITEM]` kinds: every kind today's code prints, the legacy ones, `unknown` (counted, never dropped).
  TR*  `[TRAINER]` / `[KEYBATTLE]`: class ids, KEY from `trainer_identity.KEY_TRAINER_CLASSES` by IDENTITY (TR10).
  DB*  `[DBLITEM]`: menu `ok` x `a_pressed`; the PARTNER-rise wrong-target detector (P-NOG's 18->109).
  BA*  `split_battles` / `battle_class` / `outcome_bucket` on whole evidence slices (WILD needs `[TRAINER]` telemetry
       in the log; WILD is never NON-KEY; the pre-first-start segment keeps its turns).
  SB*  `probe_boss_healing.summarise`; SI* `probe_item_index_space.summarise`; RP* each `report`'s exit code (D4);
  SL*  the I/O helpers (`select_logs` = `analyze_endless_batch.analyse`'s rule, incl. `Old/`); CL* the CLIs.
  Every expected value was derived BY HAND from the evidence listing, never copied from the code's output.

THE LINES. Single lines are quoted VERBATIM in `QUOTES` with their committed evidence file and line number; whole
battles are read from committed evidence by line range (`FIXTURES`, each with first/last-line anchors). The PROVENANCE
check (not a row: it guards the gate's data, not the code) asserts every quote is at its cited line, byte for byte.
`SHAPES` are the few lines no committed log holds (legacy kinds, rare today-kinds, error shapes): each is built from
the EMITTING code's text, cited beside it.

MUTANTS: source edits of `battle_log.py` / `probe_boss_healing.py` / `probe_item_index_space.py`, exec'd in memory
(never written to disk), each with an EXACT expected red set written BEFORE its first run. Three mention-only edits
must turn NOTHING red. COVERAGE fails if any row is in no mutant's set.
  THE FOLD (the builder's own adversarial sweep, after the first 57 mutants ran green): 9 rows (TU10 IK17 DB11 DB12
  SB5 BA8 RP4 CL2 CL3) for behaviour the first rows left unasserted — so a plausible mutant survived — and 16 mutants
  (M61-M76) that each redden exactly one of them. `MUTANT_ADDITIONS` lists what an EXISTING mutant ALSO reddens on
  the new rows; both were written before the fold's first run. ⚠ This sweep is the BUILDER's, not an independent one.
  FOLD 2: a defect the builder found reviewing `battle_log.py` — an unreadable target (`target=? hp=?->117`) let the
  `.+?` label run into the partner's — fixed (`[^=]+?`), pinned by DB13, and M77 (the REVERT) reddens exactly DB13.
  FOLD 3 — THE INDEPENDENT PASS (`evidence/2026-09-30-itemprobes-ADVERSARIAL.txt`): the author's fold of B1, B2, S1-S7
  and the nits. 55 rows: the hunter's X1-X25 (X1D INVERTED: a Draw is now LOST) and OC*/KG*/AT*/KB*/LI*/RS*/DD1/SC*/HS*/
  RD1/UR1/NT1/RP5 for each fix. 65 of the hunter's real mutants (N*), re-anchored where the code moved (17 left out as
  equivalent with its own argument; N09 dropped — it IS the Draw fix). 35 fold-3 mutants (F01-F34 and M06b): a REVERT
  of each fix is RED on its rows (the unfixed code) while the baseline is GREEN (the fixed code). `MUTANT_ADDITIONS3`
  lists what each existing mutant ALSO reddens on the new rows. Seven existing mutants were RE-ANCHORED because their
  code moved (M17, M47, M71, M74, M75, M76; M71's set moved {RP4} -> {RP5, X9}, stated at its entry), and M06 is now
  REFUSED AT LOAD by B1's import-time partition check (expected "RAISES …"; its first-pass set lives on in M06b).
  KNOWN SURVIVORS, argued rather than run: `item_battles` counting a battle with `[DBLITEM]` but no `[ITEM]` line (every
  `[DBLITEM] use` follows an `[ITEM] using`, so it cannot occur); `split_battles` keeping the LAST `[BATTLE] ended` of a
  record instead of the first (no real log ends one battle twice).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_itemprobes.py      (exit 1 on any failure; no ROM)
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # a stream without reconfigure keeps its own encoding; run_gates sets PYTHONUTF8=1 anyway
    pass

import analyze_endless_batch  # noqa: E402
import battle_log  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import probe_boss_healing  # noqa: E402,F401
import probe_item_index_space  # noqa: E402,F401
from modules.story import trainer_identity  # noqa: E402

NAMES = {"bl": "battle_log", "bh": "probe_boss_healing", "ix": "probe_item_index_space"}
PATHS = {k: HERE / f"{v}.py" for k, v in NAMES.items()}


def BL():
    return sys.modules["battle_log"]


def BH():
    return sys.modules["probe_boss_healing"]


def IX():
    return sys.modules["probe_item_index_space"]


EV = "tools/story-dev/evidence/"
ARMS = EV + "2026-09-30-doubleitems13-ARMS.txt"
RERUN = EV + "2026-09-30-doubleitems13-RERUN.txt"
M0 = EV + "2026-09-29-r25cap-raw/M0-r1.debug.txt"
AOFF = EV + "2026-09-29-r27keyitems-A-OFF-r1.txt"
B1ON = EV + "2026-09-29-r27keyitems-B1-ON.txt"
W12 = EV + "2026-09-30-weaken12-ST-ON-debug.txt"

#: name -> (committed evidence file, line number, the line VERBATIM). The PROVENANCE check re-reads every one.
QUOTES = {
    # ARMS:54 — P-OFF1's battle start
    "started": (ARMS, 54, "f3148510 [BATTLE] started hp=[('Mightyena', 0, 124), ('Sceptile', 21, 117), ('Swellow', 18, 109), ('Skitty', 0, 45), ('Zigzagoon', 16, 16), ('Castform', 0, 100)]"),
    # ARMS:55 — a two-opponent [TRAINER] start (Hex Maniac + Collector, both non-key)
    "tr_two": (ARMS, 55, "f3148510 [TRAINER] start opp=106+13 class=0x0E(HEX_MANIAC)+0x07(COLLECTOR) value=6+15 lvl_last=30+30 first=True+True base=2520 double=True two=True money=14804 heal_stock=Hyper_Potion:1 map=0,38 enemy_alive=4"),
    # ARMS:56 — a plain [TURN]
    "turn_plain": (ARMS, 56, "f3149372 [BATTLE] [TURN 0] Sceptile L42 21/117 -> UseMove:Pursuit(pp19)  vs Duskull L30 52/52"),
    # ARMS:62 — `vs ?` (no foe data)
    "turn_vsq": (ARMS, 62, "f3153296 [BATTLE] [TURN 2] Sceptile L43 17/120 -> UseMoveAgainstRightSideOpponent:Slam(pp20)  vs ?"),
    # ARMS:68 / ARMS:69 — [BATTLE] ended, then the [TRAINER] end AFTER it
    "ended_won": (ARMS, 68, "f3155931 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Mightyena:L42', 'Sceptile:L43', 'Swellow:L40', 'Skitty:L17', 'Zigzagoon:L3', 'Castform:L35']"),
    "tr_two_end": (ARMS, 69, "f3155931 [TRAINER] end opp=106+13 class=0x0E(HEX_MANIAC)+0x07(COLLECTOR) value=6+15 lvl_last=30+30 first=True+True base=2520 res=Won money=14804->17324 delta=2520 mult=1 heal_stock=Hyper_Potion:1 map=0,38"),
    # ARMS:90 — observe mode's own category
    "dbl_obs": (ARMS, 90, "f3149372 [DBLITEM-OBS] side=0 g=0 turn=0 me=Sceptile#863B0917 P=1 hp=21/117 would=Hyper_Potion why=hp key=0 worst=0 uses=0 bpo=120345 bpo_pos=0 disc=1 cur=00000000"),
    # ARMS:119 — [ITEM] using
    "item_using": (ARMS, 119, "f3149372 [BATTLE] [ITEM] using Hyper Potion on Sceptile 21/117 (use 1, worst hit 0)"),
    # ARMS:120 — [DBLITEM] use
    "dbl_use": (ARMS, 120, "f3149372 [DBLITEM] use side=0 g=0 item=Hyper Potion target=Sceptile#863B0917 P=1 hp=21/117 self=1"),
    # ARMS:121 — a [TURN] whose action is UseItem
    "turn_useitem": (ARMS, 121, "f3149372 [BATTLE] [TURN 0] Sceptile L42 21/117 -> UseItem  vs Duskull L30 52/52"),
    # ARMS:129 — P-ON's menu pass
    "dbl_menu_ok": (ARMS, 129, "f3149596 [DBLITEM] menu g=0 battler_in_menu=0 layout=1 slot=0 menu_pid=863B0917 intended_pid=863B0917 ok=1 a_pressed=1 aim=0 self=1"),
    # ARMS:132 — P-ON's after: the TARGET rose, the partner did not
    "dbl_after_pon": (ARMS, 132, "f3149839 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->117 status1=0->0 partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1 same=1"),
    # ARMS:134 — [ITEM] ✔ CONSUMED
    "item_consumed": (ARMS, 134, "f3151053 [BATTLE] [ITEM] ✔ CONSUMED (bag count dropped) — the item applied. HP reads 110/117 (a post-turn value, NOT the heal's result — see KI-101 blocker 1)"),
    # ARMS:135 — a PLAYER-side [Confused] suffix (not the foe's)
    "turn_me_confused": (ARMS, 135, "f3151053 [BATTLE] [TURN 1] Sceptile L42 110/117 [Confused] -> UseMove:Pursuit(pp19)  vs Duskull L30 5/52"),
    # ARMS:147 — P-KEY's [KEYBATTLE] key=False
    "kb_false": (ARMS, 147, "f3149372 [KEYBATTLE] opp=106+13 class=0x0E+0x07 key=False allow=False reason=not_a_key_class"),
    # ARMS:196 — P-SLOT's refusal (no A)
    "dbl_menu_refused": (ARMS, 196, "f3149598 [DBLITEM] menu g=0 battler_in_menu=0 layout=1 slot=1 menu_pid=0B30A747 intended_pid=863B0917 ok=0 a_pressed=0 aim=1 self=1"),
    # ARMS:198 — P-SLOT's after: nothing moved
    "dbl_after_pslot": (ARMS, 198, "f3149715 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->21 status1=0->0 partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->1 healed=0->0 same=1"),
    # ARMS:199 / ARMS:212 — the not-consumed retry, then the disable
    "item_nc_retry": (ARMS, 199, "f3149738 [BATTLE] [ITEM] ‼ not consumed — the item was NOT consumed — retrying once"),
    "item_nc_disable": (ARMS, 212, "f3150014 [BATTLE] [ITEM] ‼ not consumed — the item was NOT consumed twice; disabling items for the rest of this battle"),
    # ARMS:237 — P-NOG's refusal WITH an A press (the NOGUARD fault)
    "dbl_menu_nog": (ARMS, 237, "f3149598 [DBLITEM] menu g=0 battler_in_menu=0 layout=1 slot=1 menu_pid=0B30A747 intended_pid=863B0917 ok=0 a_pressed=1 aim=1 self=1"),
    # ARMS:240 — P-NOG's after: the PARTNER rose 18->109 (the wrong target)
    "dbl_after_nog": (ARMS, 240, "f3149835 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->21 status1=0->0 partner=Swellow#0B30A747 hp=18->109 Hyper Potion=1->0 healed=0->1 same=1"),
    # ARMS:254 — Tate & Liza: LEADER 0x20
    "tr_leader": (ARMS, 254, "f3452776 [TRAINER] start opp=271 class=0x20(LEADER) value=25 lvl_last=42 first=True base=8400 double=True two=False money=37654 heal_stock=Potion:1,Full_Heal:1 map=14,0 enemy_alive=4"),
    # ARMS:330 — T-ON's [KEYBATTLE] key=True
    "kb_true": (ARMS, 330, "f3453544 [KEYBATTLE] opp=271 class=0x20 key=True allow=True reason=key_class"),
    # ARMS:348 — T-ON's after: Mightyena 99->119, partner unchanged
    "dbl_after_ton": (ARMS, 348, "f3456495 [DBLITEM] after g=2 target=Mightyena#5C96EA9B hp=99->119 status1=0->0 partner=Sceptile#863B0917 hp=116->116 Potion=1->0 healed=0->1 same=1"),
    # RERUN:124 — an [ITEM-FLOW] line (NOT an [ITEM] line)
    "itemflow": (RERUN, 124, "f3149438 [BATTLE] [ITEM-FLOW] A accepted after 2 press(es) — waiting up to 150 frames for the bag, pressing nothing (SF-2) state='CB2_BAG' item=Hyper Potion"),
    # RERUN:359 — a player [Confused] suffix on a `vs ?` line
    "turn_vsq_confused": (RERUN, 359, "f3464544 [BATTLE] [TURN 5] Sceptile L48 119/133 [Confused] -> UseMoveAgainstRightSideOpponent:Strength(pp8)  vs ?"),
    # M0-r1:73 — a FOE suffix [FocusEnergy]
    "turn_foe_focus": (M0, 73, "f143313 [BATTLE] [TURN 1] Mudkip L16 21/46 -> UseMove:Water Gun(pp11)  vs Machop L9 14/31 [FocusEnergy]"),
    # M0-r1:70 — YOUNGSTER 0x25 (in TRAINER_CLASS, NOT key)
    "tr_youngster": (M0, 70, "f142089 [TRAINER] start opp=322 class=0x25(YOUNGSTER) value=4 lvl_last=9 first=True base=144 double=False two=False money=8628 heal_stock=- map=0,31 enemy_alive=1"),
    # M0-r1:89 — SCHOOL_KID 0x21
    "tr_schoolkid": (M0, 89, "f146142 [TRAINER] start opp=280 class=0x21(SCHOOL_KID) value=5 lvl_last=9 first=True base=180 double=False two=False money=8772 heal_stock=- map=0,31 enemy_alive=1"),
    # M0-r1:98 — the post-battle re-entry's skip
    "tr_skip": (M0, 98, "f150064 [TRAINER] skip reason=no_enemy_alive (a post-battle scene re-entered the battle hook)"),
    # M0-r1:177 — TEAM_AQUA 0x03 (in TRAINER_CLASS, NOT key)
    "tr_aqua": (M0, 177, "f161895 [TRAINER] start opp=16 class=0x03(TEAM_AQUA) value=5 lvl_last=11 first=True base=220 double=False two=False money=9720 heal_stock=- map=24,4 enemy_alive=1"),
    # M0-r1:346 — the RIVAL: class 0x32, whose ROM NAME is PkMn_TRAINER (key BY ID, never by name)
    "tr_rival": (M0, 346, "f178292 [TRAINER] start opp=600 class=0x32(PkMn_TRAINER) value=15 lvl_last=15 first=True base=900 double=False two=False money=9940 heal_stock=- map=0,3 enemy_alive=2"),
    # M0-r1:366 — a [TRAINER] end res=Lost
    "tr_rival_end": (M0, 366, "f184993 [TRAINER] end opp=600 class=0x32(PkMn_TRAINER) value=15 lvl_last=15 first=True base=900 res=Lost money=9940->9940 delta=0 mult=0 heal_stock=- map=0,3"),
    # A-OFF-r1:72 — COOLTRAINER 0x05 (in TRAINER_CLASS, NOT key)
    "tr_cool": (AOFF, 72, "f3189301 [TRAINER] start opp=11 class=0x05(COOLTRAINER) value=12 lvl_last=29 first=True base=1392 double=False two=False money=12322 heal_stock=Hyper_Potion:1 map=0,36 enemy_alive=2"),
    # A-OFF-r1:89 — BOTH sides suffixed; the foe's is [Uproar/MultipleTurns]
    "turn_foe_uproar": (AOFF, 89, "f3199534 [BATTLE] [TURN 3] Mightyena L43 69/127 [Paralysis] -> UseMove:Take Down(pp12)  vs Vigoroth L29 24/88 [Uproar/MultipleTurns]"),
    # A-OFF-r1:106 — TEAM_MAGMA 0x09 (in TRAINER_CLASS, NOT key)
    "tr_magma": (AOFF, 106, "f3231535 [TRAINER] start opp=717 class=0x09(TEAM_MAGMA) value=5 lvl_last=29 first=True base=580 double=False two=False money=15106 heal_stock=- map=24,86 enemy_alive=1"),
    # B1-ON:5 — Sidney: [KEYBATTLE] key=True on ELITE_FOUR 0x1F
    "kb_e4": (B1ON, 5, "f4320217 [KEYBATTLE] opp=261 class=0x1F key=True allow=True reason=key_class"),
    # B1-ON:8 — [ITEM] status cure ✔ WORKED
    "item_cure_worked": (B1ON, 8, "f4320929 [BATTLE] [ITEM] status cure ✔ WORKED: Freeze -> Healthy"),
    # weaken12-ST-ON-debug:158 — a foe suffix on a different code path's log
    "turn_foe_whismur": (W12, 158, "f154091 [BATTLE] [TURN 1] Mudkip L14 29/42 -> UseMove:Seismic Toss(pp11)  vs Whismur L6 9/23 [Uproar/MultipleTurns]"),
    # --- FOLD 3 ---
    # M0-r1:363 — the rival battle's [BATTLE] ended res Lost
    "ended_lost": (M0, 363, "f184993 [BATTLE] ended (outcome=BattleOutcome.Lost) party=['Marshtomp:L18']"),
    # r27keyitems-B2-ON:73 — Tabitha: MAGMA_ADMIN 0x31
    "tr_tabitha": (EV + "2026-09-29-r27keyitems-B2-ON.txt", 73, "f3268955 [TRAINER] start opp=732 class=0x31(MAGMA_ADMIN) value=10 lvl_last=33 first=True base=1320 double=False two=False money=19166 heal_stock=Hyper_Potion:1 map=? enemy_alive=4"),
    # doubleitems13-STEP0:87 — the Space Center multi battle: Maxie 0x35 + Tabitha 0x31 (two opponents, one group)
    "tr_maxie_tabitha": (EV + "2026-09-30-doubleitems13-STEP0.txt", 87, "f3488931 [TRAINER] start opp=734+514 class=0x35(MAGMA_LEADER)+0x31(MAGMA_ADMIN) value=20+10 lvl_last=44+40 first=True+True base=5120 double=True two=True money=49214 heal_stock=Potion:1,Full_Heal:1 map=14,10 enemy_alive=6"),
}


def Q(name: str) -> str:
    return QUOTES[name][2]


#: Lines NO committed log holds, each built from the EMITTING code's text (cited). Not covered by PROVENANCE.
SHAPES = {
    # story_mode.py `_maybe_use_item` (status-cure branch, `[ITEM] status cure ... ‼ no change`)
    "item_cure_nochange": "f1000 [BATTLE] [ITEM] status cure ‼ no change: Sleep -> Sleep  (NOT counted against the "
                          "no-op detector — a cure that fails is a menu problem, not a wrong target)",
    # story_mode.py `_maybe_use_item` (`[ITEM] ✔ landed (KI-101: ...`, the HP-heuristic path)
    "item_landed": "f1000 [BATTLE] [ITEM] ✔ landed (KI-101: the DRIVER resolved the menu slot after bag-open; "
                   "`_index_space`='party' is a legacy LABEL and no longer selects the target) (HP now 120/120)",
    # story_mode.py `_maybe_use_item` (`[ITEM] KI-101 fresh-read failed (...)`)
    "item_fresh_fail": "f1000 [BATTLE] [ITEM] KI-101 fresh-read failed (TypeError); judging on the ENTRY SNAPSHOT — "
                       "this verdict may be a false negative",
    # story_mode.py `_maybe_use_item` (the unreadable-bag disable, worded 2026-09-16)
    "item_noeffect_disable": "f1000 [BATTLE] [ITEM] ‼ no effect (HP still 23/120) — HP did not rise on two attempts and "
                             "the bag count was unreadable; disabling items for the rest of this battle",
    # LEGACY (83a9e2f1 .. 96ed1ec7); quoted in 07-CHANGELOG.md:10271
    "item_leg_landed": "f1000 [BATTLE] [ITEM] ✔ landed using the party-order index (HP now 120/120)",
    # SHARED shape (legacy flip; today's unreadable-bag retry); quoted in 07-CHANGELOG.md:10272
    "item_retry": "f1000 [BATTLE] [ITEM] ‼ no effect (HP still 23/120) — retrying with the battle-order index",
    # LEGACY (83a9e2f1's note text; 05-KNOWN-ISSUES.md:1296 reports it at 23/144)
    "item_leg_both": "f1000 [BATTLE] [ITEM] ‼ no effect (HP still 23/144) — both index spaces failed; disabling items "
                     "for the rest of this battle",
    # LEGACY (706d6b4c); quoted in 07-CHANGELOG.md:10174
    "item_leg_notexec": "f1000 [BATTLE] [ITEM] ‼ no effect (HP still 23/120) — item use is not executing; disabling "
                        "items for the rest of this battle",
    # an [ITEM] line no emitter prints: must be `unknown`, never dropped
    "item_unknown": "f1000 [BATTLE] [ITEM] ✔ a line shape no emitter prints today",
    # a STORY line QUOTING an item line: stray (a tag outside its position), never item data
    "stray": "f1000 [STORY] quoting a log line: [ITEM] using Potion on Mudkip 5/20 (use 1, worst hit 0)",
    # battle_action_selection.py `_describe`: the getattr fallbacks print `L?` / `?/?`
    "turn_malformed": "f1000 [BATTLE] [TURN 3] Mudkip L5 20/20 -> UseMove:Tackle(pp35)  vs Zubat L? ?/?",
    # battle_action_selection.py `_dbl_after`'s except branch
    "dbl_after_err": "f1000 [DBLITEM] after g=0 err=TypeError: boom",
    # battle_action_selection.py `_dbl_after` with no partner: `_dbl_label(None)` = `?`, `_dbl_v(None)` = `?`
    "dbl_after_nopartner": "f1000 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->117 status1=0->0 partner=? "
                           "hp=?->? Hyper Potion=1->0 healed=0->1 same=1",
    # story_mode.py `_r27_key_gate` under POKEBOT_R27_FAULT_ALLORDINARY (class forced to 0x05) in a LEADER battle
    "kb_allordinary": "f3453544 [KEYBATTLE] opp=271 class=0x05 key=False allow=False reason=not_a_key_class",
    # battle_action_selection.py `_describe` with species names from modules/data/species.json: `Nidoran♀`, and
    # `Farfetch’d` with a TYPOGRAPHIC apostrophe (U+2019) — the old `[A-Za-z' .-]` name class missed both
    "turn_nidoran": "f1000 [BATTLE] [TURN 2] Mudkip L10 30/30 -> UseMove:Tackle(pp35)  vs Nidoran♀ L8 25/25",
    "turn_farfetchd": "f1000 [BATTLE] [TURN 3] Mudkip L10 30/30 -> UseMove:Tackle(pp34)  vs Farfetch’d L9 31/31 [Confused]",
    # battle_action_selection.py `_dbl_log("struggle-exit g=0 — ...")` (D11)
    "dbl_struggle": "f1000 [DBLITEM] struggle-exit g=0 — battler 2's action menu is open; no A pressed into it (D11)",
    # story_mode.py `decide_turn_in_double_battle`'s fail-open `err side= g=` line (D9)
    "dbl_err": "f1000 [DBLITEM] err side=0 g=0 RuntimeError: boom",
    # battle_action_selection.py `_dbl_after` with an UNREADABLE pre-read target (`t0` None): `_dbl_label(None)` = `?`,
    # `_dbl_v(None)` = `?`, `same=0`; the post-read and the partner are readable
    "dbl_after_unreadable_target": "f1000 [DBLITEM] after g=0 target=? hp=?->117 status1=?->0 partner=Swellow#0B30A747 "
                                   "hp=18->109 Hyper Potion=1->0 healed=0->1 same=0",
    # --- FOLD 3 (the independent pass) ---
    # battle_action_selection.py `_dbl_after`: the bag DROPPED, the target did NOT rise (same=1), the partner did not
    # rise — the independent pass's S3 example (an item gone to a benched Pokémon, or nowhere visible)
    "dbl_after_lost": "f1000 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->21 status1=0->0 "
                      "partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1 same=1",
    # the same with `same=0` (the target's identity changed between the reads): never a lost item
    "dbl_after_lost_same0": "f1000 [DBLITEM] after g=0 target=Sceptile#863B0917 hp=21->21 status1=0->0 "
                            "partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1 same=0",
    # story_mode.py `_t1_start`'s except branch (`start unreadable (<Exc>: <msg>)`; the hunter's X3)
    "tr_unread": "f1 [TRAINER] start unreadable (TypeError: boom)",
    # trainer_identity._side_fields with side B unreadable (cls None -> `?`; the hunter's X4)
    "tr_qside": "f1 [TRAINER] start opp=106+13 class=0x0E(HEX_MANIAC)+? value=6+? lvl_last=30+30 first=True+True base=? "
                "double=True two=True money=1 heal_stock=- map=0,38 enemy_alive=4",
    # a TwoOpponents start whose KEY class is opponent B (a Magma grunt + Tabitha's class; the hunter's X5)
    "tr_keyb": "f1 [TRAINER] start opp=570+514 class=0x09(TEAM_MAGMA)+0x31(MAGMA_ADMIN) value=5+10 lvl_last=30+30 "
               "first=True+True base=1 double=True two=True money=1 heal_stock=- map=0,0 enemy_alive=4",
    # debug_logger.py `_event(fc, f"[BATTLE] ended (outcome={_safe(_last_outcome)}) …")` with an unreadable outcome
    "ended_none": "f1 [BATTLE] ended (outcome=None) party=[]",
}

#: Lines a committed evidence file QUOTES inside other text (a markdown bullet): name -> (file, line, the text). The
#: PROVENANCE check asserts the text is CONTAINED in that line.
QUOTES_IN = {
    # ADVERSARIAL.txt:159 — a REAL Draw from batch0927 (`P1-…-20260927-102251.log:22346`, Tate & Liza; the next
    # line is `[STORY] WHITEOUT recovery #7`), quoted by the independent pass
    "draw": (EV + "2026-09-30-itemprobes-ADVERSARIAL.txt", 159, "f4082031 [BATTLE] ended (outcome=BattleOutcome.Draw)"),
}


def QI(name: str) -> str:
    return QUOTES_IN[name][2]

#: name -> (committed evidence file, first line, last line, first-line prefix, last-line prefix). Whole battles.
FIXTURES = {
    # A-OFF-r1:71-104 — 2 COOLTRAINER battles (one with using + CONSUMED and the foe-suffix line 89), then 4 WILD
    # battles (no [TRAINER] line), the last one Caught. 16 [TURN] lines, all with foe data.
    "A": (AOFF, 71, 104, "f3189301 [BATTLE] started", "f3230561 [BATTLE] ended (outcome=BattleOutcome.Caught)"),
    # A-OFF-r1:73-91 — the same log entered MID-BATTLE: 6 [TURN] lines + ended + [TRAINER] end before any start
    "ORPHAN": (AOFF, 73, 91, "f3190230 [BATTLE] [TURN 0]", "f3200706 [TRAINER] end opp=767"),
    # M0-r1:82-100 — a WILD battle (Nincada), then SCHOOL_KID with [TRAINER] end, skip, and [BATTLE] ended LAST
    "M_A": (M0, 82, 100, "f144426 [BATTLE] started", "f150066 [MONEY]"),
    # M0-r1:345-366 — the RIVAL (0x32) battle, Lost; 14 [TURN] lines with a PLAYER [Confused]
    "M_B": (M0, 345, 366, "f178292 [BATTLE] started", "f184993 [TRAINER] end opp=600"),
    # RERUN:184-223 — P-SLOT: two requests, the not-consumed retry and the disable; 13 [TURN] (7 + 6 `vs ?`)
    "PSLOT": (RERUN, 184, 223, "f3148510 [BATTLE] started", "f3155053 [BATTLE] [TURN 3] Swellow"),
    # RERUN:225-251 — P-NOG: 1 request, CONSUMED, menu ok=0 a_pressed=1, the partner rise; 11 [TURN] (7 + 4 `vs ?`)
    "PNOG": (RERUN, 225, 251, "f3148510 [BATTLE] started", "f3155322 [BATTLE] [TURN 4] Swellow"),
    # RERUN:328-361 — T-ON: LEADER, [KEYBATTLE] key=True, 1 request, CONSUMED, menu pass; 18 [TURN] (15 + 3 `vs ?`)
    "TON": (RERUN, 328, 361, "f3452776 [BATTLE] started", "f3464583 [BATTLE] [TURN 5] Mightyena"),
    # B1-ON:3-41 — Sidney (ELITE_FOUR): a cure + 3 Full Restores; 26 [TURN]; his Mightyena 25/134 -> 134/134 (+109)
    "E4": (B1ON, 3, 41, "f4319292 [BATTLE] started", "f4337854 [TRAINER] end opp=261"),
    # --- FOLD 3 ---
    # RERUN:253-271 — T-OFF1: Tate & Liza (LEADER, double), Won, with [BATTLE] ended AND [TRAINER] end; no item
    "TOFF1": (RERUN, 253, 271, "f3452776 [BATTLE] started", "f3464107 [TRAINER] end opp=271"),
    # RERUN:145-161 — P-KEY: a [KEYBATTLE] key=False refusal in a NON-KEY double, Won, and NO item line at all
    "PKEY": (RERUN, 145, 161, "f3148510 [BATTLE] started", "f3155931 [TRAINER] end opp=106+13"),
    # r27keyitems-B2-ON:72-118 — Tabitha (MAGMA_ADMIN, Won), then Maxie (MAGMA_LEADER, Lost, one item used)
    "MAGMA": (EV + "2026-09-29-r27keyitems-B2-ON.txt", 72, 118, "f3268955 [BATTLE] started",
              "f3294699 [TRAINER] end opp=601"),
}
_FX_CACHE: dict = {}
_EV_CACHE: dict = {}


def _evidence(rel: str) -> list:
    if rel not in _EV_CACHE:
        _EV_CACHE[rel] = (REPO / rel).read_text(encoding="utf-8").splitlines()
    return _EV_CACHE[rel]


def FX(name: str) -> list:
    if name not in _FX_CACHE:
        rel, a, b, _p, _q = FIXTURES[name]
        _FX_CACHE[name] = _evidence(rel)[a - 1:b]
    return list(_FX_CACHE[name])


def no_trainer(lines: list) -> list:
    """A pre-`[TRAINER]` log, derived: the same lines with every `[TRAINER]` line removed (DERIVED, labelled)."""
    return [line for line in lines if "[TRAINER] " not in line]


FAILURES: list = []
ROW_NAMES: set = set()
ROWS: list = []


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


def quiet(fn, *a, **k):
    """Call `fn` with stdout captured; returns its result."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


# ============================================================================================ RT — routing
@row("RT1", "every routed kind on a real line: start, end, turn, item, trainer, keybattle, dblitem, dblobs")
def _rt1():
    r = BL().route
    got = [r(Q(n)) for n in ("started", "ended_won", "turn_plain", "item_using", "tr_two", "kb_true", "dbl_menu_ok",
                             "dbl_obs")]
    return eq(got, ["start", "end", "turn", "item", "trainer", "keybattle", "dblitem", "dblobs"])


@row("RT2", "an [ITEM-FLOW] line is NOT an [ITEM] line (routes None)")
def _rt2():
    return eq(BL().route(Q("itemflow")), None)


@row("RT3", "a STORY line quoting an [ITEM] line is STRAY, and stray_lines lists exactly it")
def _rt3():
    lines = [Q("started"), SHAPES["stray"], Q("item_using")]
    return eq((BL().route(SHAPES["stray"]), BL().stray_lines(lines)), ("stray", [SHAPES["stray"]]))


# ============================================================================================ TU — [TURN]
# `Turn` is a namedtuple: rows compare `tuple(t)`, so a mutant module's own `Turn` class compares by value.
@row("TU1", "a plain foe: (0, Duskull, 30, 52, 52, None)")
def _tu1():
    t = BL().parse_turn(Q("turn_plain"))
    return eq(tuple(t) if t else t, (0, "Duskull", 30, 52, 52, None))


@row("TU2", "a PLAYER [Confused] is not the foe's status: (1, Duskull, 30, 5, 52, None)")
def _tu2():
    t = BL().parse_turn(Q("turn_me_confused"))
    return eq(tuple(t) if t else t, (1, "Duskull", 30, 5, 52, None))


@row("TU3", "a FOE suffix with both sides suffixed: (3, Vigoroth, 29, 24, 88, 'Uproar/MultipleTurns')")
def _tu3():
    t = BL().parse_turn(Q("turn_foe_uproar"))
    return eq(tuple(t) if t else t, (3, "Vigoroth", 29, 24, 88, "Uproar/MultipleTurns"))


@row("TU4", "a FOE suffix [FocusEnergy]: (1, Machop, 9, 14, 31, 'FocusEnergy')")
def _tu4():
    t = BL().parse_turn(Q("turn_foe_focus"))
    return eq(tuple(t) if t else t, (1, "Machop", 9, 14, 31, "FocusEnergy"))


@row("TU5", "`vs ?` -> parse_turn None, turn_shape 'no_foe'")
def _tu5():
    return eq((BL().parse_turn(Q("turn_vsq")), BL().turn_shape(Q("turn_vsq"))), (None, "no_foe"))


@row("TU6", "`vs ?` after a PLAYER [Confused] -> None, 'no_foe'")
def _tu6():
    return eq((BL().parse_turn(Q("turn_vsq_confused")), BL().turn_shape(Q("turn_vsq_confused"))), (None, "no_foe"))


@row("TU7", "turn_shape of the two foe-suffix lines (two code paths) is 'parsed'")
def _tu7():
    return eq([BL().turn_shape(Q(n)) for n in ("turn_foe_uproar", "turn_foe_whismur", "turn_foe_focus")],
              ["parsed", "parsed", "parsed"])


@row("TU8", "a [TURN] line WITH malformed foe data is 'unparsed' (counted); a non-[TURN] line is None")
def _tu8():
    return eq((BL().turn_shape(SHAPES["turn_malformed"]), BL().turn_shape(Q("item_using"))), ("unparsed", None))


@row("TU9", "a UseItem turn: (0, Duskull, 30, 52, 52, None)")
def _tu9():
    t = BL().parse_turn(Q("turn_useitem"))
    return eq(tuple(t) if t else t, (0, "Duskull", 30, 52, 52, None))


# ============================================================================================ HE — foe_heals
def _t(n, foe, hp, mx):
    return BL().Turn(n, foe, 30, hp, mx, None)


@row("HE1", "a rise of the same (foe, max) is one heal event (SYNTHETIC turns; Norman's Slaking 27 -> 136)")
def _he1():
    return eq(BL().foe_heals([_t(1, "Slaking", 27, 143), _t(2, "Slaking", 136, 143)]), [(2, "Slaking", 27, 136)])


@row("HE2", "identity is (foe, max_hp): same name, different max is NOT a heal (SYNTHETIC)")
def _he2():
    return eq(BL().foe_heals([_t(1, "Slaking", 27, 143), _t(2, "Slaking", 136, 150)]), [])


@row("HE3", "equal or falling HP is no heal (SYNTHETIC: 50, 50, 40)")
def _he3():
    return eq(BL().foe_heals([_t(1, "Absol", 50, 137), _t(2, "Absol", 50, 137), _t(3, "Absol", 40, 137)]), [])


# ============================================================================================ IK — [ITEM] kinds
def _kind_row(rid, name, src, want):
    @row(rid, f"item_kind({name}) == {want!r}")
    def _fn():
        line = Q(name) if src == "Q" else SHAPES[name]
        return eq(BL().item_kind(line), want)
    return _fn


_kind_row("IK1", "item_using", "Q", "using")
_kind_row("IK2", "item_consumed", "Q", "consumed")
_kind_row("IK3", "item_nc_retry", "Q", "not_consumed_retry")
_kind_row("IK4", "item_nc_disable", "Q", "not_consumed_disable")
_kind_row("IK5", "item_cure_worked", "Q", "cure_worked")
_kind_row("IK6", "item_cure_nochange", "S", "cure_no_change")
_kind_row("IK7", "item_landed", "S", "landed")
_kind_row("IK8", "item_fresh_fail", "S", "fresh_read_failed")
_kind_row("IK9", "item_retry", "S", "no_effect_retry")
_kind_row("IK10", "item_noeffect_disable", "S", "no_effect_disable")
_kind_row("IK11", "item_leg_landed", "S", "legacy_landed")
_kind_row("IK12", "item_leg_both", "S", "legacy_both_failed")
_kind_row("IK13", "item_leg_notexec", "S", "legacy_not_executing")
_kind_row("IK14", "item_unknown", "S", "unknown")


@row("IK15", "item_kind of an [ITEM-FLOW] line and of a [TURN] line is None")
def _ik15():
    return eq((BL().item_kind(Q("itemflow")), BL().item_kind(Q("turn_plain"))), (None, None))


@row("IK16", "the kind table is exactly the 13 kinds + unknown, and the legacy flip/landed words parse")
def _ik16():
    want = ("using", "consumed", "landed", "not_consumed_retry", "not_consumed_disable", "no_effect_retry",
            "no_effect_disable", "cure_worked", "cure_no_change", "fresh_read_failed", "legacy_landed",
            "legacy_both_failed", "legacy_not_executing", "unknown")
    got = (BL().ITEM_KIND_NAMES, BL().index_space(SHAPES["item_leg_landed"]), BL().index_space(SHAPES["item_retry"]))
    return eq(got, (want, "party", "battle"))


# ============================================================================================ TR — [TRAINER] / key
def _classes(name):
    return BL().parse_trainer(Q(name))["classes"]


@row("TR1", "two opponents: classes [0x0E, 0x07], kind start, two=True, double=True")
def _tr1():
    t = BL().parse_trainer(Q("tr_two"))
    return eq((t["kind"], t["classes"], t["two"], t["double"]), ("start", [0x0E, 0x07], "True", "True"))


@row("TR2", "Hex Maniac + Collector is NON-KEY (key_class False)")
def _tr2():
    return eq(BL().key_class(_classes("tr_two")), False)


@row("TR3", "LEADER 0x20 is KEY")
def _tr3():
    return eq((_classes("tr_leader"), BL().key_class(_classes("tr_leader"))), ([0x20], True))


@row("TR4", "the RIVAL 0x32 (ROM name PkMn_TRAINER) is KEY — by ID, never by name")
def _tr4():
    return eq((_classes("tr_rival"), BL().key_class(_classes("tr_rival"))), ([0x32], True))


@row("TR5", "SCHOOL_KID 0x21 is NON-KEY")
def _tr5():
    return eq((_classes("tr_schoolkid"), BL().key_class(_classes("tr_schoolkid"))), ([0x21], False))


@row("TR6", "COOLTRAINER 0x05, YOUNGSTER 0x25, TEAM_AQUA 0x03, TEAM_MAGMA 0x09 are NON-KEY (named classes, not key)")
def _tr6():
    return eq([BL().key_class(_classes(n)) for n in ("tr_cool", "tr_youngster", "tr_aqua", "tr_magma")],
              [False, False, False, False])


@row("TR7", "a [TRAINER] skip: kind skip, no classes")
def _tr7():
    t = BL().parse_trainer(Q("tr_skip"))
    return eq((t["kind"], t["classes"]), ("skip", []))


@row("TR8", "key_class: [] -> None; [?, non-key] -> None; [?, LEADER] -> True")
def _tr8():
    k = BL().key_class
    return eq((k([]), k([None, 0x07]), k([None, 0x20])), (None, None, True))


@row("TR9", "KEY_CLASSES IS trainer_identity.KEY_TRAINER_CLASSES (the single source of truth, not a copy)")
def _tr9():
    return eq(BL().KEY_CLASSES is trainer_identity.KEY_TRAINER_CLASSES, True)


@row("TR10", "[KEYBATTLE]: key=True classes [0x20]; key=False classes [0x0E, 0x07]; ELITE_FOUR [0x1F] key=True")
def _tr10():
    p = BL().parse_keybattle
    got = [(p(Q(n))["key"], p(Q(n))["classes"]) for n in ("kb_true", "kb_false", "kb_e4")]
    return eq(got, [("True", [0x20]), ("False", [0x0E, 0x07]), ("True", [0x1F])])


@row("TR11", "[TRAINER] end: res Won (two opponents) and res Lost (the rival)")
def _tr11():
    p = BL().parse_trainer
    return eq([(p(Q(n))["kind"], p(Q(n))["res"]) for n in ("tr_two_end", "tr_rival_end")],
              [("end", "Won"), ("end", "Lost")])


# ============================================================================================ DB — [DBLITEM]
def _d(name, src="Q"):
    return BL().parse_dblitem(Q(name) if src == "Q" else SHAPES[name])


@row("DB1", "menu pass: ok=1 a_pressed=1")
def _db1():
    d = _d("dbl_menu_ok")
    return eq((d["kind"], d["ok"], d["a_pressed"]), ("menu", 1, 1))


@row("DB2", "menu refusal: ok=0 a_pressed=0")
def _db2():
    d = _d("dbl_menu_refused")
    return eq((d["kind"], d["ok"], d["a_pressed"]), ("menu", 0, 0))


@row("DB3", "P-NOG's refusal pressed anyway: ok=0 a_pressed=1")
def _db3():
    d = _d("dbl_menu_nog")
    return eq((d["kind"], d["ok"], d["a_pressed"]), ("menu", 0, 1))


@row("DB4", "P-NOG's after: target 21->21, PARTNER 18->109 -> partner_rose True")
def _db4():
    d = _d("dbl_after_nog")
    return eq((d["target_hp"], d["partner_hp"], BL().partner_rose(d)), ((21, 21), (18, 109), True))


@row("DB5", "P-ON's after: target 21->117, partner 18->18 -> partner_rose False")
def _db5():
    d = _d("dbl_after_pon")
    return eq((d["target_hp"], d["partner_hp"], BL().partner_rose(d)), ((21, 117), (18, 18), False))


@row("DB6", "T-ON's after: target 99->119, partner 116->116 -> False")
def _db6():
    d = _d("dbl_after_ton")
    return eq((d["target_hp"], d["partner_hp"], BL().partner_rose(d)), ((99, 119), (116, 116), False))


@row("DB7", "P-SLOT's after: nothing moved -> False")
def _db7():
    d = _d("dbl_after_pslot")
    return eq((d["target_hp"], d["partner_hp"], BL().partner_rose(d)), ((21, 21), (18, 18), False))


@row("DB8", "a use line is kind 'use'")
def _db8():
    return eq(_d("dbl_use")["kind"], "use")


@row("DB9", "an `after ... err=` line: err True, no rise; a `partner=? hp=?->?` line: no rise")
def _db9():
    a, b = _d("dbl_after_err", "S"), _d("dbl_after_nopartner", "S")
    return eq((a["kind"], a["err"], BL().partner_rose(a), b["partner_hp"], BL().partner_rose(b)),
              ("after", True, False, (None, None), False))


@row("DB10", "dbl_counts over P-NOG's use + menu + after + an observe line")
def _db10():
    b = BL().Battle(started=True, dblitem=[Q("dbl_use"), Q("dbl_menu_nog"), Q("dbl_after_nog")], dblobs=[Q("dbl_obs")])
    c = BL().dbl_counts(b)
    got = {k: c[k] for k in ("use", "menu", "menu_ok", "menu_refused", "menu_refused_pressed", "after", "wrong_target",
                             "obs")}
    return eq(got, {"use": 1, "menu": 1, "menu_ok": 0, "menu_refused": 1, "menu_refused_pressed": 1, "after": 1,
                    "wrong_target": 1, "obs": 1})


# ============================================================================================ BA — battles
def _cls(lines):
    t1 = BL().has_trainer_telemetry(lines)
    return [BL().battle_class(b, t1) for b in BL().split_battles(lines)]


@row("BA1", "split FX A: 6 battles (turns, items, outcome) by hand")
def _ba1():
    got = [(b.started, len(b.turns), len(b.items), b.outcome) for b in BL().split_battles(FX("A"))]
    return eq(got, [(True, 6, 0, "Won"), (True, 5, 2, "Won"), (True, 1, 0, "Won"), (True, 1, 0, "Won"),
                    (True, 2, 0, "Won"), (True, 1, 0, "Caught")])


@row("BA2", "classes of FX A (a log WITH [TRAINER] telemetry): 2 NON-KEY, then 4 WILD (never NON-KEY)")
def _ba2():
    b = BL()
    return eq(_cls(FX("A")), [b.NONKEY, b.NONKEY, b.WILD, b.WILD, b.WILD, b.WILD])


@row("BA3", "FX A without its [TRAINER] lines (a pre-T1 log): no telemetry, all 6 UNCLASSIFIED")
def _ba3():
    lines = no_trainer(FX("A"))
    return eq((BL().has_trainer_telemetry(lines), _cls(lines)), (False, [BL().UNCLASSIFIED] * 6))


@row("BA4", "FX M (wild, SCHOOL_KID with end+skip before [BATTLE] ended, RIVAL): WILD, NON-KEY, KEY; won, won, lost")
def _ba4():
    lines = FX("M_A") + FX("M_B")
    battles = BL().split_battles(lines)
    got = (_cls(lines), [BL().outcome_bucket(b) for b in battles], [len(b.trainer) for b in battles])
    return eq(got, ([BL().WILD, BL().NONKEY, BL().KEY], ["won", "won", "lost"], [0, 3, 2]))


@row("BA5", "a log entered MID-BATTLE: the segment before the first start keeps its 6 turns, is UNCLASSIFIED")
def _ba5():
    battles = BL().split_battles(FX("ORPHAN"))
    got = [(b.started, len(b.turns), b.outcome, BL().battle_class(b, True)) for b in battles]
    return eq(got, [(False, 6, "Won", BL().UNCLASSIFIED), (True, 5, "Won", BL().NONKEY)])


@row("BA6", "outcome buckets: Caught -> other; no ended line (P-NOG) -> other; [TRAINER] end res=Won fallback -> won")
def _ba6():
    a = BL().split_battles(FX("A"))[-1]
    nog = BL().split_battles(FX("PNOG"))[0]
    fallback = BL().split_battles([Q("started"), Q("tr_two"), Q("tr_two_end")])[0]
    return eq([BL().outcome_bucket(b) for b in (a, nog, fallback)], ["other", "other", "won"])


@row("BA7", "T-ON is KEY, P-NOG and P-SLOT are NON-KEY, Sidney is KEY")
def _ba7():
    b = BL()
    return eq([_cls(FX(n)) for n in ("TON", "PNOG", "PSLOT", "E4")], [[b.KEY], [b.NONKEY], [b.NONKEY], [b.KEY]])


# ============================================================================================ SB — boss healing
def _sb(logs):
    return BH().summarise(logs)


def _brief(s, cls):
    r = s["by_class"][cls]
    return (r["battles"], r["turns"], r["no_foe"], r["big_battles"], r["big_events"], r["any_battles"],
            r["any_events"])


@row("SB1", "FX A: 16 [TURN] lines, 16 parsed (incl. the foe-suffix line), NON-KEY 2 battles/11 turns, WILD 4/5, 0 heals")
def _sb1():
    s = _sb([FX("A")])
    b = BL()
    got = (s["turn_lines"], s["parsed"], s["no_foe"], len(s["unparsed"]), s["t1_logs"], _brief(s, b.NONKEY),
           _brief(s, b.WILD), len(s["events"]))
    return eq(got, (16, 16, 0, 0, 1, (2, 11, 0, 0, 0, 0, 0), (4, 5, 0, 0, 0, 0, 0), 0))


@row("SB2", "P-NOG + T-ON: 29 [TURN] lines, 22 parsed, 7 `vs ?`; KEY 15 turns/3 vs ?, NON-KEY 7/4; 0 heals")
def _sb2():
    s = _sb([FX("PNOG"), FX("TON")])
    b = BL()
    got = (s["turn_lines"], s["parsed"], s["no_foe"], len(s["unparsed"]), _brief(s, b.KEY), _brief(s, b.NONKEY))
    return eq(got, (29, 22, 7, 0, (1, 15, 3, 0, 0, 0, 0), (1, 7, 4, 0, 0, 0, 0)))


@row("SB3", "FX A as a pre-T1 log: all 6 battles and 16 turns UNCLASSIFIED; 0 KEY/NON-KEY/WILD")
def _sb3():
    s = _sb([no_trainer(FX("A"))])
    b = BL()
    got = (s["t1_logs"], _brief(s, b.UNCLASSIFIED)[:2], [s["by_class"][c]["battles"] for c in (b.KEY, b.NONKEY, b.WILD)])
    return eq(got, (0, (6, 16), [0, 0, 0]))


@row("SB4", "Sidney (real): 26 turns, KEY, ONE LARGE heal — Mightyena 25 -> 134 (+109)")
def _sb4():
    s = _sb([FX("E4")])
    got = (_brief(s, BL().KEY), [e[1:] for e in s["events"]])
    return eq(got, ((1, 26, 0, 1, 1, 1, 1), [(109, "Mightyena", 25, 134)]))


# ============================================================================================ SI — item outcomes
def _si(logs):
    return IX().summarise(logs)


def _ibrief(row_):
    return tuple(row_[k] for k in ("battles", "item_battles", "requests", "consumed", "not_consumed_retry",
                                   "not_consumed_disable", "cure_worked", "unknown", "no_verdict"))


@row("SI1", "P-NOG: NON-KEY 1 request, 1 consumed; [DBLITEM] use 1, menu refused-but-pressed 1, after 1, WRONG TARGET 1")
def _si1():
    s = _si([FX("PNOG")])
    d = s["dbl"][BL().NONKEY]
    got = (_ibrief(s["by_class"][BL().NONKEY]),
           (d["use"], d["menu"], d["menu_ok"], d["menu_refused"], d["menu_refused_pressed"], d["after"],
            d["wrong_target"]), len(s["wrong_target"]), dict(s["kinds"]))
    return eq(got, ((1, 1, 1, 1, 0, 0, 0, 0, 0), (1, 1, 0, 1, 1, 1, 1), 1, {"using": 1, "consumed": 1}))


@row("SI2", "T-ON: KEY 1 request, 1 consumed; menu pass 1, 0 wrong target; [KEYBATTLE] key=True agrees")
def _si2():
    s = _si([FX("TON")])
    d = s["dbl"][BL().KEY]
    got = (_ibrief(s["by_class"][BL().KEY]), (d["menu_ok"], d["wrong_target"]), dict(s["keybattle"]),
           len(s["kb_disagree"]), dict(s["kinds"]))
    return eq(got, ((1, 1, 1, 1, 0, 0, 0, 0, 0), (1, 0), {"key=True": 1}, 0, {"using": 1, "consumed": 1}))


@row("SI3", "FX A by outcome: NON-KEY/won 2 battles, 1 request, 1 consumed; WILD/won 3; WILD/other 1 (the catch)")
def _si3():
    s = _si([FX("A")])
    b = BL()
    o = s["by_outcome"]
    got = (_ibrief(o[(b.NONKEY, "won")]), o[(b.WILD, "won")]["battles"], o[(b.WILD, "other")]["battles"],
           o[(b.NONKEY, "lost")]["battles"])
    return eq(got, ((2, 1, 1, 1, 0, 0, 0, 0, 0), 3, 1, 0))


@row("SI4", "Sidney: KEY 4 requests = 1 cure worked + 3 consumed, 0 without a verdict; key=True")
def _si4():
    s = _si([FX("E4")])
    got = (_ibrief(s["by_class"][BL().KEY]), dict(s["keybattle"]))
    return eq(got, ((1, 1, 4, 3, 0, 0, 1, 0, 0), {"key=True": 1}))


@row("SI5", "FX A as a pre-T1 log: the request is UNCLASSIFIED, WILD 0")
def _si5():
    s = _si([no_trainer(FX("A"))])
    b = BL()
    return eq((_ibrief(s["by_class"][b.UNCLASSIFIED]), s["by_class"][b.WILD]["battles"]),
              ((6, 1, 1, 1, 0, 0, 0, 0, 0), 0))


@row("SI6", "P-SLOT: NON-KEY 2 requests, the retry and the disable, 0 consumed, 0 without a verdict; 2 refusals")
def _si6():
    s = _si([FX("PSLOT")])
    d = s["dbl"][BL().NONKEY]
    got = (_ibrief(s["by_class"][BL().NONKEY]), (d["use"], d["menu_refused"], d["menu_refused_pressed"],
                                                 d["wrong_target"]), dict(s["kinds"]))
    return eq(got, ((1, 1, 2, 0, 1, 1, 0, 0, 0), (2, 2, 0, 0),
                    {"using": 2, "not_consumed_retry": 1, "not_consumed_disable": 1}))


def _legacy_log(*extra):
    return [Q("started"), Q("tr_two"), Q("item_using")] + list(extra)


@row("SI7", "legacy-only lines turn the legacy verdict ON: landed {party: 1}, flips {battle: 1}, both 1")
def _si7():
    s = _si([_legacy_log(SHAPES["item_retry"], SHAPES["item_leg_landed"], SHAPES["item_leg_both"])])
    got = (IX().legacy_present(s), dict(s["legacy_landed"]), dict(s["legacy_flips"]), s["legacy_both"])
    return eq(got, (True, {"party": 1}, {"battle": 1}, 1))


@row("SI8", "the SHARED retry shape alone does NOT turn the legacy verdict on")
def _si8():
    s = _si([_legacy_log(SHAPES["item_retry"])])
    return eq((IX().legacy_present(s), dict(s["legacy_flips"])), (False, {"battle": 1}))


@row("SI9", "a [KEYBATTLE] key=False inside a LEADER battle (the ALLORDINARY shape) is ONE disagreement")
def _si9():
    s = _si([[Q("started"), Q("tr_leader"), SHAPES["kb_allordinary"]]])
    return eq((dict(s["keybattle"]), len(s["kb_disagree"])), ({"key=False": 1}, 1))


# ============================================================================================ RP — exit codes (D4)
@row("RP1", "boss report: a clean summary exits 0; an UNPARSED-with-foe-data line exits 1")
def _rp1():
    clean = quiet(BH().report, _sb([FX("TON")]), "x", 1, 1)
    bad = quiet(BH().report, _sb([FX("TON") + [SHAPES["turn_malformed"]]]), "x", 1, 1)
    return eq((clean, bad), (0, 1))


@row("RP2", "boss report: no logs -> 1; logs but no turn parsed -> 1; a stray line -> 1")
def _rp2():
    none = quiet(BH().report, _sb([]), "x", 0, 0)
    noturn = quiet(BH().report, _sb([[Q("started"), Q("item_using")]]), "x", 1, 1)
    stray = quiet(BH().report, _sb([FX("TON") + [SHAPES["stray"]]]), "x", 1, 1)
    return eq((none, noturn, stray), (1, 1, 1))


@row("RP3", "item report: clean -> 0; an unknown kind -> 1; NO DATA -> 1; requests with no verdict line -> 1")
def _rp3():
    r = IX().report
    clean = quiet(r, _si([FX("TON")]), "x", 1, 1)
    unknown = quiet(r, _si([FX("TON") + [SHAPES["item_unknown"]]]), "x", 1, 1)
    nodata = quiet(r, _si([FX("M_A")]), "x", 1, 1)
    noverdict = quiet(r, _si([[Q("started"), Q("tr_leader"), Q("item_using")]]), "x", 1, 1)
    return eq((clean, unknown, nodata, noverdict), (0, 1, 1, 1))


# ============================================================================================ SL — I/O helpers
TMP: dict = {}


def _build_tree(root: pathlib.Path) -> dict:
    """A synthetic profiles tree for `select_logs`: in-window logs in `debug-logs/` AND `Old/`, a name present in both
    (Old wins), out-of-window days, a non-endless lane, a non-.log file; plus an x4 layout and a worktree `.git`."""
    prof = root / "profiles"
    files = [
        "endless-P1-Mudkip/debug-logs/Story-debug-20260927-100000.log",
        "endless-P1-Mudkip/debug-logs/Old/Story-debug-20260928-110000.log",
        "endless-P1-Mudkip/debug-logs/Story-debug-20260928-120000.log",
        "endless-P1-Mudkip/debug-logs/Old/Story-debug-20260928-120000.log",
        "endless-P2-Torchic/debug-logs/Old/Story-debug-20260926-090000.log",
        "endless-P2-Torchic/debug-logs/Story-debug-20260929-000000.log",
        "endless-P2-Torchic/debug-logs/Old/Story-debug-20260927-230000.log",
        "endless-P3-Treecko/debug-logs/Story-debug-20260927-050000.txt",
        "repro-ml/debug-logs/Story-debug-20260927-010101.log",
    ]
    for f in files:
        p = prof / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(FX("TON")) + "\n", encoding="utf-8")   # real content, so CL2 can run the CLIs on it
    want = [prof / "endless-P1-Mudkip/debug-logs/Story-debug-20260927-100000.log",
            prof / "endless-P1-Mudkip/debug-logs/Old/Story-debug-20260928-110000.log",
            prof / "endless-P1-Mudkip/debug-logs/Old/Story-debug-20260928-120000.log",
            prof / "endless-P2-Torchic/debug-logs/Old/Story-debug-20260927-230000.log"]
    x4 = root / "x4"
    for f in ("x4-runs/S1/L01/debug-logs/a.log", "x4-runs/S1/L02/debug-logs/b.log", "x4-runs/S1/M01/debug-logs/c.log",
              "x4-runs/S2/L01/debug-logs/d.log"):
        p = x4 / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    wt = root / "wt"
    wt.mkdir()
    (wt / ".git").write_text(f"gitdir: {(root / 'main' / '.git' / 'worktrees' / 'wt').as_posix()}\n", encoding="utf-8")
    plain = root / "plain"
    (plain / ".git").mkdir(parents=True)
    log = root / "one.log"
    log.write_bytes("a\nb ✔\n".encode("utf-8"))
    # FOLD 3: a lane that is NOT `endless-P*` (the hunter's X20: `endless-old` must stay out), two T-ON log copies and
    # a DIRECTORY whose name matches the same glob (SC4: --logs reads files only, repeatable, de-duplicated)
    old = prof / "endless-old" / "debug-logs" / "Story-debug-20260927-000000.log"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_text("\n".join(FX("TON")) + "\n", encoding="utf-8")
    for name in ("ton.debug.txt", "ton2.debug.txt"):
        (root / name).write_text("\n".join(FX("TON")) + "\n", encoding="utf-8")
    (root / "dir.debug.txt").mkdir()
    return {"root": root, "prof": prof, "want": want, "x4": x4, "wt": wt, "plain": plain, "log": log}


@row("SL1", "select_logs reads debug-logs/ AND Old/ (Old wins a name in both), the window, endless-P* lanes, *.log only")
def _sl1():
    got = BL().select_logs(TMP["prof"], "20260927", "20260928")
    return eq([p.relative_to(TMP["prof"]).as_posix() for p in got],
              [p.relative_to(TMP["prof"]).as_posix() for p in TMP["want"]])


@row("SL2", "select_logs == analyze_endless_batch.analyse on the same tree (the same rule)")
def _sl2():
    saved = analyze_endless_batch.PROFILES
    try:
        analyze_endless_batch.PROFILES = TMP["prof"]
        theirs = [log for _lane, _stamp, log in analyze_endless_batch.analyse("20260927", "20260928")]
    finally:
        analyze_endless_batch.PROFILES = saved
    ours = BL().select_logs(TMP["prof"], "20260927", "20260928")
    return eq(ours, theirs)


@row("SL3", "main_checkout: a worktree's .git FILE -> the main root; a .git DIRECTORY -> itself")
def _sl3():
    got = (BL().main_checkout(TMP["wt"]), BL().main_checkout(TMP["plain"]))
    return eq(got, (TMP["root"] / "main", TMP["plain"]))


@row("SL4", "x4_logs reads x4-runs/<stamp>/L<nn>/debug-logs/*.log only; read_lines gives (lines, bytes), a missing file ([], 0)")
def _sl4():
    x4 = [p.relative_to(TMP["x4"]).as_posix() for p in BL().x4_logs("S1", TMP["x4"])]
    got = (x4, BL().read_lines(TMP["log"]), BL().read_lines(TMP["root"] / "missing.log"))
    return eq(got, (["x4-runs/S1/L01/debug-logs/a.log", "x4-runs/S1/L02/debug-logs/b.log"], (["a", "b ✔"], 8), ([], 0)))


@row("CL1", "both CLIs on --logs <a T-ON file> exit 0; on a glob matching nothing exit 1")
def _cl1():
    f = TMP["root"] / "ton.debug.txt"
    if not f.exists():
        f.write_text("\n".join(FX("TON")) + "\n", encoding="utf-8")
    nothing = str(TMP["root"] / "no-such-*.txt")
    got = (quiet(BH().main, ["--logs", str(f)]), quiet(IX().main, ["--logs", str(f)]),
           quiet(BH().main, ["--logs", nothing]), quiet(IX().main, ["--logs", nothing]))
    return eq(got, (0, 0, 1, 1))


# ============================================================================================ FOLD — the builder's sweep
# Rows added by the builder's own adversarial sweep (2026-09-30), after the first 57 mutants ran green: each pins a
# behaviour the first rows left unasserted, so a plausible mutant survived. Existing rows are untouched; what an
# EXISTING mutant now also reddens on these rows is in `MUTANT_ADDITIONS`, written before the fold's first run.
@row("TU10", "non-ASCII / typographic species names parse: Nidoran♀, Farfetch’d (with a foe suffix)")
def _tu10():
    a, b = BL().parse_turn(SHAPES["turn_nidoran"]), BL().parse_turn(SHAPES["turn_farfetchd"])
    return eq((tuple(a) if a else a, tuple(b) if b else b),
              ((2, "Nidoran♀", 8, 25, 25, None), (3, "Farfetch’d", 9, 31, 31, "Confused")))


@row("IK17", "the kind SETS are pinned: VERDICT, NO_EFFECT, LEGACY_ONLY")
def _ik17():
    b = BL()
    got = (sorted(b.VERDICT_KINDS), sorted(b.NO_EFFECT_KINDS), sorted(b.LEGACY_ONLY_KINDS))
    want = (sorted(["consumed", "landed", "not_consumed_retry", "not_consumed_disable", "no_effect_retry",
                    "no_effect_disable", "cure_worked", "cure_no_change", "legacy_landed", "legacy_both_failed",
                    "legacy_not_executing"]),
            sorted(["no_effect_retry", "no_effect_disable", "legacy_both_failed", "legacy_not_executing"]),
            sorted(["legacy_landed", "legacy_both_failed"]))
    return eq(got, want)


@row("DB11", "dbl_counts: an `after ... err=` (after 1, after_err 1), a struggle-exit, an err")
def _db11():
    b = BL().Battle(started=True, dblitem=[SHAPES["dbl_after_err"], SHAPES["dbl_struggle"], SHAPES["dbl_err"]])
    c = BL().dbl_counts(b)
    return eq({k: c[k] for k in ("after", "after_err", "struggle-exit", "err", "other", "wrong_target")},
              {"after": 1, "after_err": 1, "struggle-exit": 1, "err": 1, "other": 0, "wrong_target": 0})


@row("DB12", "dbl_counts over a real menu PASS (ok=1 a_pressed=1): menu_ok 1, menu_ok_not_pressed 0, refused 0")
def _db12():
    c = BL().dbl_counts(BL().Battle(started=True, dblitem=[Q("dbl_menu_ok")]))
    return eq((c["menu"], c["menu_ok"], c["menu_ok_not_pressed"], c["menu_refused"]), (1, 1, 0, 0))


@row("SB5", "boss probe: with_turns and the >=12-turn PROXY — Sidney: KEY 1/1 long, 1 long with a LARGE heal; FX A: "
            "NON-KEY 2, WILD 4 with turns, 0 long")
def _sb5():
    e, a = _sb([FX("E4")]), _sb([FX("A")])
    b = BL()
    k = e["by_class"][b.KEY]
    got = ((k["with_turns"], k["long"], k["long_big"]), a["by_class"][b.NONKEY]["with_turns"],
           a["by_class"][b.WILD]["with_turns"], sum(r["long"] for r in a["by_class"].values()))
    return eq(got, ((1, 1, 1), 2, 4, 0))


@row("BA8", "a battle whose only [TRAINER] line is its END is classified from it (NON-KEY)")
def _ba8():
    return eq(_cls([Q("started"), Q("tr_two_end")]), [BL().NONKEY])


@row("RP4", "item report: singles Sidney (no [DBLITEM]) -> 0, never NO DATA; + a stray -> 1; a [KEYBATTLE] "
            "disagreement is a FINDING -> 0")
def _rp4():
    r = IX().report
    got = (quiet(r, _si([FX("E4")]), "x", 1, 1), quiet(r, _si([FX("TON") + [SHAPES["stray"]]]), "x", 1, 1),
           quiet(r, _si([FX("TON") + [SHAPES["kb_allordinary"]]]), "x", 1, 1))
    return eq(got, (0, 1, 0))


def _cli(main, argv) -> "tuple[object, str]":
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as stop:
            code = ("SystemExit", stop.code)
    return code, out.getvalue()


@row("CL2", "both CLIs with --since/--until/--profiles on the synthetic tree: 4 logs, exit 0; a window before it: 0, exit 1")
def _cl2():
    got = []
    for main in (BH().main, IX().main):
        code, out = _cli(main, ["--since", "20260927", "--until", "20260928", "--profiles", str(TMP["prof"])])
        got.append((code, "CONTROL: 4 debug log(s)" in out))
        code, out = _cli(main, ["--since", "20260101", "--until", "20260102", "--profiles", str(TMP["prof"])])
        got.append((code, "CONTROL: 0 debug log(s)" in out))
    return eq(got, [(0, True), (1, True), (0, True), (1, True)])


@row("DB13", "an UNREADABLE target (`target=? hp=?->117`): target '?', hp (None, 117); the partner's 18->109 stays "
             "the PARTNER's")
def _db13():
    d = _d("dbl_after_unreadable_target", "S")
    return eq((d["target"], d["target_hp"], d["partner"], d["partner_hp"], BL().partner_rose(d)),
              ("?", (None, 117), "Swellow#0B30A747", (18, 109), True))


@row("CL3", "both CLIs refuse a stamp AND --logs together (argparse exit 2)")
def _cl3():
    argv = ["20260809-155844", "--logs", str(TMP["root"] / "ton.debug.txt")]
    return eq([_cli(BH().main, argv)[0], _cli(IX().main, argv)[0]], [("SystemExit", 2), ("SystemExit", 2)])


# ============================================================================================ FOLD 3 — the independent pass
# `evidence/2026-09-30-itemprobes-ADVERSARIAL.txt` (two fresh agents: a mutant hunter and a correctness review). X1-X25
# are the hunter's proposed rows (X1D INVERTED by the fix it asked for); the rest pin each fix the author decided:
# B2 (a Draw is a defeat) OC*/X1D, B1 (key groups) KG*, S1 (per trainer) AT*, S2 (outcomes and [KEYBATTLE] regardless
# of item data) KB*, S3 (the item quantity, a lost item) LI*, S4 (Rest) RS*, S5 (doubles) DD1, S6 (selection) SC*,
# S7 (heal stock) HS*, the nits RD1 (N2), UR1 (N5), NT1 (N1), OC2 (N6), and RP5 (the NO-DATA rule's singles case).
def _ended(outcome: str) -> str:            # debug_logger.py:535's shape
    return f"f1 [BATTLE] ended (outcome=BattleOutcome.{outcome}) party=[]"


def _xturn(n: int, foe: str, hp: int, mx: int = 137, status: str = "") -> str:   # `_describe`'s shape, SYNTHETIC values
    return (f"f1 [BATTLE] [TURN {n}] Mudkip L30 90/90 -> UseMove:Tackle(pp30)  vs {foe} L30 {hp}/{mx}"
            + (f" [{status}]" if status else ""))


def _ob(lines) -> str:
    return BL().outcome_bucket(BL().split_battles(lines)[0])


@row("X1", "outcome: RanAway / OpponentTeleported / Caught -> other (no trainer battle ends that way)")
def _x1():
    return eq([_ob([Q("started"), _ended(o)]) for o in ("RanAway", "OpponentTeleported", "Caught")],
              ["other", "other", "other"])


@row("X1D", "outcome: a REAL Draw (ADVERSARIAL.txt:159, Tate & Liza) -> LOST (the game whites out on it; INVERTED "
            "from the hunter's pin of the old mapping)")
def _x1d():
    return eq(_ob([Q("started"), Q("tr_leader"), QI("draw")]), "lost")


@row("X2", "outcome: the [TRAINER] end res=Lost FALLBACK (no [BATTLE] ended) -> lost")
def _x2():
    return eq(_ob([Q("started"), Q("tr_rival"), Q("tr_rival_end")]), "lost")


@row("X3", "class: a battle whose only [TRAINER] line is `start unreadable` is UNCLASSIFIED; a LEADER battle stays KEY")
def _x3():
    return eq(_cls([Q("started"), SHAPES["tr_unread"], Q("started"), Q("tr_leader")]), [BL().UNCLASSIFIED, BL().KEY])


@row("X4", "class: a `?` side stays None; beside a non-key side the battle is UNCLASSIFIED")
def _x4():
    b = BL()
    return eq((b.parse_classes("0x0E(HEX_MANIAC)+?"), b.parse_classes("?"), _cls([Q("started"), SHAPES["tr_qside"]])),
              ([0x0E, None], [None], [b.UNCLASSIFIED]))


@row("X5", "class: two opponents with the KEY class in opponent B is KEY")
def _x5():
    return eq(_cls([Q("started"), SHAPES["tr_keyb"]]), [BL().KEY])


@row("X6", "class: a record naming two trainers is KEY if EITHER is (both orders)")
def _x6():
    return eq((_cls([Q("started"), Q("tr_two"), Q("tr_leader")]), _cls([Q("started"), Q("tr_leader"), Q("tr_two")])),
              ([BL().KEY], [BL().KEY]))


@row("X7", "both probes: a wild battle BEFORE the log's first [TRAINER] line is WILD (FX M_A)")
def _x7():
    s1, s2 = BH().summarise([FX("M_A")]), IX().summarise([FX("M_A")])
    b = BL()
    return eq(([s1["by_class"][c]["battles"] for c in (b.WILD, b.NONKEY, b.UNCLASSIFIED)],
               [s2["by_class"][c]["battles"] for c in (b.WILD, b.NONKEY, b.UNCLASSIFIED)]), ([1, 1, 0], [1, 1, 0]))


@row("X8", "item columns: landed 1, no_effect 2 (today + legacy), cure_no_change 1, fresh_read_failed 1, unknown 1")
def _x8():
    lines = [Q("started"), Q("tr_leader"), Q("item_using"), SHAPES["item_landed"], Q("item_using"),
             SHAPES["item_noeffect_disable"], Q("item_using"), SHAPES["item_leg_notexec"], Q("item_using"),
             SHAPES["item_cure_nochange"], SHAPES["item_fresh_fail"], SHAPES["item_unknown"]]
    r = IX().summarise([lines])["by_class"][BL().KEY]
    return eq({k: r[k] for k in ("landed", "no_effect", "cure_no_change", "fresh_read_failed", "unknown")},
              {"landed": 1, "no_effect": 2, "cure_no_change": 1, "fresh_read_failed": 1, "unknown": 1})


@row("X9", "item report: an observe-only log ([DBLITEM-OBS], no [ITEM]) is data, exit 0 — never NO DATA")
def _x9():
    return eq(quiet(IX().report, IX().summarise([[Q("started"), Q("tr_two"), Q("dbl_obs")]]), "x", 1, 1), 0)


@row("X10", "item report: P-SLOT (2 requests, 0 consumed, retry + disable) exits 0 — not-consumed IS a verdict")
def _x10():
    return eq(quiet(IX().report, IX().summarise([FX("PSLOT")]), "x", 1, 1), 0)


@row("X11", "item probe: a [KEYBATTLE] in an UNCLASSIFIED battle is never a disagreement")
def _x11():
    return eq(len(IX().summarise([[Q("started"), SHAPES["tr_unread"], Q("kb_true")]])["kb_disagree"]), 0)


@row("X12", "item probe: a battle with only a [DBLITEM] err line (fail-open, no [ITEM]) is an item battle")
def _x12():
    return eq(IX().battle_row(BL().Battle(started=True, dblitem=[SHAPES["dbl_err"]]))["item_battles"], 1)


@row("X13", "dbl_counts: two partner-rise afters in one battle are TWO wrong targets")
def _x13():
    return eq(BL().dbl_counts(BL().Battle(started=True, dblitem=[Q("dbl_after_nog"), Q("dbl_after_nog")]))
              ["wrong_target"], 2)


@row("X14", "boss probe: SMALL heals stay quarantined — KEY big 1/1, any 2 battles/3 events, events 3 (SYNTHETIC turns)")
def _x14():
    a = [Q("started"), Q("tr_leader"), _xturn(1, "Absol", 98), _xturn(2, "Absol", 100), _xturn(3, "Absol", 20),
         _xturn(4, "Absol", 137)]
    b = [Q("started"), Q("tr_leader"), _xturn(1, "Absol", 98), _xturn(2, "Absol", 100)]
    s = BH().summarise([a + b])
    r = s["by_class"][BL().KEY]
    return eq((r["big_battles"], r["big_events"], r["any_battles"], r["any_events"], len(s["events"])), (1, 1, 2, 3, 3))


@row("X15", "boss probe: a heal of EXACTLY +50 is LARGE (>=) (SYNTHETIC turns)")
def _x15():
    s = BH().summarise([[Q("started"), Q("tr_leader"), _xturn(1, "Absol", 10), _xturn(2, "Absol", 60)]])
    return eq(s["by_class"][BL().KEY]["big_events"], 1)


@row("X16", "boss probe: the >=12 PROXY counts PARSED records — P-SLOT (13 lines, 7 parsed) is not long")
def _x16():
    return eq(sum(r["long"] for r in BH().summarise([FX("PSLOT")])["by_class"].values()), 0)


@row("X17", "both CLIs: --since alone and --until alone mean ONE day (2 logs on the synthetic tree)")
def _x17():
    got = []
    for main in (BH().main, IX().main):
        for flag in ("--since", "--until"):
            _code, out = _cli(main, [flag, "20260927", "--profiles", str(TMP["prof"])])
            got.append("CONTROL: 2 debug log(s)" in out)
    return eq(got, [True] * 4)


@row("X18", "default_profiles is the MAIN checkout's (via main_checkout), never the worktree's")
def _x18():
    b = BL()
    saved = b.main_checkout
    try:
        b.main_checkout = lambda: TMP["root"] / "main"
        got = b.default_profiles()
    finally:
        b.main_checkout = saved
    return eq(got, TMP["root"] / "main" / "sandbox-pokebot" / "profiles")


@row("X19", "read_lines survives a log cut mid-character (no exception; bytes counted)")
def _x19():
    p = TMP["root"] / "cut.log"
    p.write_bytes(b"a\n\xe2\x9c")
    lines, n = BL().read_lines(p)
    return eq((len(lines), n), (2, 4))


@row("X20", "select_logs ignores a lane that is not `endless-P*` (endless-old)")
def _x20():
    got = [q.relative_to(TMP["prof"]).as_posix() for q in BL().select_logs(TMP["prof"], "20260927", "20260928")]
    return eq(any(g.startswith("endless-old/") for g in got), False)


@row("X21", "both CLIs refuse --profiles with --logs (argparse exit 2)")
def _x21():
    argv = ["--logs", str(TMP["root"] / "ton.debug.txt"), "--profiles", str(TMP["prof"])]
    return eq([_cli(BH().main, argv)[0], _cli(IX().main, argv)[0]], [("SystemExit", 2), ("SystemExit", 2)])


@row("X22", "boss report: [TURN] lines that are ALL `vs ?` -> exit 1 (nothing parsed is never a rate)")
def _x22():
    return eq(quiet(BH().report, BH().summarise([[Q("started"), Q("tr_leader"), Q("turn_vsq")]]), "x", 1, 1), 1)


@row("X23", "route: a [STORY] line quoting a [TURN] or a [TRAINER] line is STRAY")
def _x23():
    r = BL().route
    return eq((r("f1 [STORY] quoting: [TURN 3] Mudkip L5 20/20 -> UseMove:Tackle(pp35)  vs Zubat L4 10/20"),
               r("f1 [STORY] quoting: [TRAINER] start opp=1 class=0x20(LEADER)")), ("stray", "stray"))


@row("X24", "route: `ended (outcome=None)` (an unreadable outcome) is an END; with no [TRAINER] end it is other")
def _x24():
    return eq((BL().route(SHAPES["ended_none"]), _ob([Q("started"), SHAPES["ended_none"]])), ("end", "other"))


@row("X25", "split: a battle the log never ended, then a new start, is TWO records")
def _x25():
    bs = BL().split_battles([Q("started"), Q("tr_two"), Q("turn_plain"), Q("started"), Q("tr_leader"), Q("ended_won")])
    return eq([(len(b.turns), BL().outcome_bucket(b)) for b in bs], [(1, "other"), (0, "won")])


@row("OC1", "win_rate = won/(won+lost), None with no decided battle; the group table prints 100.0% / 0.0% / n/a")
def _oc1():
    b = BL()
    lines = b.group_outcome_lines({"leaders": {"n": 1, "won": 1}, "rivals": {"n": 1, "lost": 1}})
    got = (b.win_rate(1, 1), b.win_rate(0, 0), b.win_rate(0, 3),
           [line.split()[-1] for line in lines[1:]])
    return eq(got, (0.5, None, 0.0, ["100.0%", "n/a", "0.0%", "n/a"]))


@row("OC2", "outcome: `ended (outcome=None)` falls back to the [TRAINER] end res=Lost -> lost (N6)")
def _oc2():
    return eq(_ob([Q("started"), Q("tr_rival"), SHAPES["ended_none"], Q("tr_rival_end")]), "lost")


@row("KG1", "KEY_GROUPS pinned: leaders {0x20}, elite_four {0x1F, 0x26}, rivals {0x32}, magma_aqua {0x35, 0x0D, 0x31, "
            "0x0B}; their union IS the module's KEY_CLASSES")
def _kg1():
    g = BL().KEY_GROUPS
    got = ({k: sorted(v) for k, v in g.items()}, frozenset().union(*g.values()) == BL().KEY_CLASSES)
    return eq(got, ({"leaders": [0x20], "elite_four": [0x1F, 0x26], "rivals": [0x32],
                     "magma_aqua": sorted([0x35, 0x0D, 0x31, 0x0B])}, True))


@row("KG2", "check_key_groups raises on a MISSING key class and on an OVERLAP; returns on the real groups")
def _kg2():
    b, kc = BL(), trainer_identity.KEY_TRAINER_CLASSES
    missing = {k: (v - {0x26} if k == "elite_four" else v) for k, v in b.KEY_GROUPS.items()}
    overlap = {k: (v | {0x20} if k == "rivals" else v) for k, v in b.KEY_GROUPS.items()}
    got = []
    for groups in (missing, overlap, b.KEY_GROUPS):
        try:
            b.check_key_groups(groups, kc)
            got.append("ok")
        except AssertionError:
            got.append("raised")
    return eq(got, ["raised", "raised", "ok"])


@row("KG3", "key_group on REAL class lists: LEADER leaders; ELITE_FOUR elite_four; the rival rivals; Tabitha, Maxie + "
            "Tabitha and a KEY opponent B magma_aqua; Hex Maniac + Collector None")
def _kg3():
    b = BL()

    def grp(line):
        return b.key_group(b.parse_trainer(line)["classes"])
    got = [grp(Q("tr_leader")), grp(FX("E4")[1]), grp(Q("tr_rival")), grp(Q("tr_tabitha")),
           grp(Q("tr_maxie_tabitha")), grp(SHAPES["tr_keyb"]), grp(Q("tr_two"))]
    return eq(got, ["leaders", "elite_four", "rivals", "magma_aqua", "magma_aqua", "magma_aqua", None])


@row("KG4", "both probes per KEY GROUP on real battles (T-OFF1, Sidney, the rival, Tabitha + Maxie): (n, won, lost, "
            "other) leaders (1,1,0,0), elite_four (1,1,0,0), rivals (1,0,1,0), magma_aqua (2,1,1,0)")
def _kg4():
    logs = [FX("TOFF1"), FX("E4"), FX("M_B"), FX("MAGMA")]
    want = {"leaders": (1, 1, 0, 0), "elite_four": (1, 1, 0, 0), "rivals": (1, 0, 1, 0), "magma_aqua": (2, 1, 1, 0)}
    got = []
    for summ in (BH().summarise(logs), IX().summarise(logs)):
        got.append({g: tuple(r[k] for k in ("n", "won", "lost", "other")) for g, r in summ["by_group"].items()})
    return eq(got, [want, want])


@row("KG5", "boss probe answers 'does the bot lose those fights?': Sidney is KEY won with a LARGE heal (big_won 1, "
            "elite_four big 1/1); the rival is KEY lost with no LARGE heal")
def _kg5():
    e, r = BH().summarise([FX("E4")]), BH().summarise([FX("M_B")])
    k, g, k2 = e["by_class"][BL().KEY], e["by_group"]["elite_four"], r["by_class"][BL().KEY]
    got = ((k["won"], k["big_won"], k["big_lost"]), (g["big_battles"], g["big_won"]), (k2["lost"], k2["big_battles"]))
    return eq(got, ((1, 1, 0), (1, 1), (1, 0)))


@row("KG7", "the IMPORT-TIME check fires: this module's own source with CHAMPION dropped from elite_four refuses to load")
def _kg7():
    src = getattr(BL(), "__source__", None) or PATHS["bl"].read_text(encoding="utf-8")
    anchor = '"elite_four": frozenset({_TC["ELITE_FOUR"], _TC["CHAMPION"]}),'
    if src.count(anchor) != 1:
        return False, "the elite_four anchor is not in the source"
    mod = types.ModuleType("battle_log_kg7")
    mod.__file__ = str(PATHS["bl"])
    try:
        exec(compile(src.replace(anchor, '"elite_four": frozenset({_TC["ELITE_FOUR"]}),'), "<kg7>", "exec"),
             mod.__dict__)
    except AssertionError as error:
        return True, f"raised: {error}"
    return False, "loaded without raising"


@row("AT1", "attempt_summary per (log, opp): leaders 2 trainers (1st won 1, lost 1; both eventually won in 3 and 1 "
            "attempts; most 3); rivals 1 (1st lost, never won) — SYNTHETIC records")
def _at1():
    recs = [(1, "271", "leaders", "lost"), (1, "271", "leaders", "lost"), (1, "271", "leaders", "won"),
            (2, "271", "leaders", "won"), (2, "600", "rivals", "lost")]
    a = BL().attempt_summary(recs)
    got = {g: (r["pairs"], dict(r["first"]), r["eventually_won"], sorted(r["attempts_to_win"]), r["max_attempts"])
           for g, r in a.items()}
    return eq(got, {"leaders": (2, {"lost": 1, "won": 1}, 2, [1, 3], 3), "rivals": (1, {"lost": 1}, 0, [], 1)})


@row("AT2", "both probes record KEY attempts per log: real lines composed (LEADER lost then won in log 1, won in log "
            "2) -> leaders 2 trainers, 1st won 1 / lost 1, eventually 2, attempts [1, 2]")
def _at2():
    log1 = [Q("started"), Q("tr_leader"), Q("ended_lost"), Q("started"), Q("tr_leader"), Q("ended_won")]
    log2 = [Q("started"), Q("tr_leader"), Q("ended_won")]
    got = []
    for summ in (BH().summarise([log1, log2]), IX().summarise([log1, log2])):
        r = BL().attempt_summary(summ["key_records"])["leaders"]
        got.append((r["pairs"], dict(r["first"]), r["eventually_won"], sorted(r["attempts_to_win"])))
    want = (2, {"lost": 1, "won": 1}, 2, [1, 2])
    return eq(got, [want, want])


@row("KB1", "item report on P-KEY (a [KEYBATTLE] refusal, NO item line): prints the agreement verdict and exits 0")
def _kb1():
    code, out = _cli(lambda _a: IX().report(IX().summarise([FX("PKEY")]), "x", 1, 1), [])
    return eq((code, "[KEYBATTLE] production verdicts: {'key=False': 1}; disagreeing with the battle's offline class "
                     "(from its [TRAINER] lines): 0" in out, "NO ITEM DATA" in out), (0, True, True))


@row("KB2", "a [KEYBATTLE] in a battle with no offline class is counted on its OWN line (1), never a disagreement")
def _kb2():
    s = IX().summarise([[Q("started"), SHAPES["tr_unread"], Q("kb_true")]])
    _code, out = _cli(lambda _a: IX().report(s, "x", 1, 1), [])
    return eq((len(s["kb_no_offline"]), len(s["kb_disagree"]),
               "with NO offline class (WILD / UNCLASSIFIED — not comparable): 1" in out), (1, 0, True))


@row("KB3", "item report on a log with NO item and NO [KEYBATTLE] line: exit 1 (NO DATA) — but the outcome and "
            "key-group tables are PRINTED first")
def _kb3():
    code, out = _cli(lambda _a: IX().report(IX().summarise([FX("M_A")]), "x", 1, 1), [])
    return eq((code, "PER BATTLE CLASS x OUTCOME" in out, "KEY BATTLES PER GROUP x OUTCOME" in out), (1, True, True))


@row("LI1", "[DBLITEM] after: item, quantity and same= — P-NOG (Hyper Potion 1->0, same=1), T-ON (Potion 1->0), "
            "P-SLOT (1->1), an unreadable target (same=0)")
def _li1():
    def f(d):
        return d["item"], d["qty"], d["same"]
    got = [f(_d("dbl_after_nog")), f(_d("dbl_after_ton")), f(_d("dbl_after_pslot")),
           f(_d("dbl_after_unreadable_target", "S"))]
    return eq(got, [("Hyper Potion", (1, 0), 1), ("Potion", (1, 0), 1), ("Hyper Potion", (1, 1), 1),
                    ("Hyper Potion", (1, 0), 0)])


@row("LI2", "lost_item: bag dropped + target not raised + same=1 + no partner rise -> True; P-NOG (partner rose), "
            "P-ON (target rose), P-SLOT (bag kept), same=0, an unreadable target -> False")
def _li2():
    li = BL().lost_item
    got = [li(_d("dbl_after_lost", "S")), li(_d("dbl_after_nog")), li(_d("dbl_after_pon")), li(_d("dbl_after_pslot")),
           li(_d("dbl_after_lost_same0", "S")), li(_d("dbl_after_unreadable_target", "S"))]
    return eq(got, [True, False, False, False, False, False])


@row("LI3", "a lost item and a wrong target in one battle: dbl_counts lost_item 1, wrong_target 1; the item probe "
            "lists 1 lost-item line")
def _li3():
    lines = [Q("started"), Q("tr_two"), SHAPES["dbl_after_lost"], Q("dbl_after_nog")]
    c = BL().dbl_counts(BL().split_battles(lines)[0])
    return eq((c["lost_item"], c["wrong_target"], len(IX().summarise([lines])["lost_item"])), (1, 1, 1))


@row("RS1", "Rest: a rise that NEWLY gains Sleep is 'rest' (also as Sleep/Confused); a rise while ALREADY asleep is "
            "'heal'; foe_heals still lists every rise (SYNTHETIC turns)")
def _rs1():
    T = BL().Turn
    a = BL().foe_heal_events([T(1, "Kingdra", 46, 35, 151, None), T(2, "Kingdra", 46, 151, 151, "Sleep")])
    b = BL().foe_heal_events([T(1, "Kingdra", 46, 40, 151, "Sleep"), T(2, "Kingdra", 46, 90, 151, "Sleep")])
    c = BL().foe_heal_events([T(1, "Kingdra", 46, 35, 151, "Confused"), T(2, "Kingdra", 46, 151, 151, "Sleep/Confused")])
    d = BL().foe_heals([T(1, "Kingdra", 46, 35, 151, None), T(2, "Kingdra", 46, 151, 151, "Sleep")])
    return eq(([e[4] for e in a], [e[4] for e in b], [e[4] for e in c], d),
              (["rest"], ["heal"], ["rest"], [(2, "Kingdra", 35, 151)]))


@row("RS2", "boss probe: a Rest rise is reported apart (rest 1) and NEVER counted as a heal (big 0, any 0)")
def _rs2():
    s = BH().summarise([[Q("started"), Q("tr_leader"), _xturn(1, "Kingdra", 35, 151),
                         _xturn(2, "Kingdra", 151, 151, "Sleep")]])
    r = s["by_class"][BL().KEY]
    return eq((r["rest_battles"], r["rest_events"], r["big_events"], r["any_events"], len(s["events"]), len(s["rests"])),
              (1, 1, 0, 0, 0, 1))


@row("DD1", "boss probe doubles column (left foe only): T-ON is a KEY double (1 of 1); FX A's NON-KEY battles are not")
def _dd1():
    t, a = BH().summarise([FX("TON")]), BH().summarise([FX("A")])
    k = t["by_class"][BL().KEY]
    return eq(((k["battles"], k["doubles"]), a["by_class"][BL().NONKEY]["doubles"]), ((1, 1), 0))


@row("SC1", "scan_logs: per lane P1 3, P2 1; outside the window 1 before and 1 after; no lane left out")
def _sc1():
    sc = BL().scan_logs(TMP["prof"], "20260927", "20260928")
    return eq((dict(sc["per_lane"]), sc["before"], sc["after"], sc["lanes_skipped"]),
              ({"endless-P1-Mudkip": 3, "endless-P2-Torchic": 1}, 1, 1, []))


@row("SC2", "scan_logs --lanes P2: only P2's in-window log; P1 and P3 left out and NAMED")
def _sc2():
    sc = BL().scan_logs(TMP["prof"], "20260927", "20260928", ["P2"])
    return eq(([p.relative_to(TMP["prof"]).as_posix() for p in sc["paths"]], sc["lanes_skipped"]),
              (["endless-P2-Torchic/debug-logs/Old/Story-debug-20260927-230000.log"],
               ["endless-P1-Mudkip", "endless-P3-Treecko"]))


@row("SC3", "CLI notes: --since alone WARNS (one day) and prints per lane / outside the window; --lanes P2 reads 1 log "
            "and names the lanes it left out")
def _sc3():
    _c1, out1 = _cli(BH().main, ["--since", "20260927", "--profiles", str(TMP["prof"])])
    _c2, out2 = _cli(IX().main, ["--since", "20260927", "--until", "20260928", "--profiles", str(TMP["prof"]),
                                 "--lanes", "P2"])
    got = ("only --since given: the window is ONE day (20260927)" in out1,
           "per lane: {'endless-P1-Mudkip': 1, 'endless-P2-Torchic': 1}; outside the window: 1 before 20260927, "
           "3 after 20260927" in out1,
           "CONTROL: 1 debug log(s)" in out2, "lanes left out by --lanes: ['endless-P1-Mudkip', 'endless-P3-Treecko']"
           in out2)
    return eq(got, (True, True, True, True))


@row("SC4", "--logs is repeatable and reads FILES only: two globs -> 2 logs; one glob over *.debug.txt skips the "
            "directory dir.debug.txt; the same glob twice is one log")
def _sc4():
    root = TMP["root"]
    _c1, out = _cli(IX().main, ["--logs", str(root / "ton.debug.txt"), "--logs", str(root / "ton2.debug.txt")])
    names = [p.name for p in BL().glob_logs(str(root / "*.debug.txt"))]
    twice = BL().glob_logs([str(root / "ton.debug.txt"), str(root / "ton.debug.txt")])
    return eq(("CONTROL: 2 debug log(s)" in out, names, len(twice)), (True, ["ton.debug.txt", "ton2.debug.txt"], 1))


@row("HS1", "heal_stock parsed from REAL lines: Tate & Liza Potion 1 + Full Heal 1 -> 1 HP item; the rival `-` -> 0; "
            "Sidney's 7 lines -> 35 HP items (Potion, Super Potion, 30 Hyper Potion, 3 Full Restore); an unknown name "
            "is listed, not counted")
def _hs1():
    b = BL()
    lead = b.parse_trainer(Q("tr_leader"))["heal_stock"]
    riv = b.parse_trainer(Q("tr_rival"))["heal_stock"]
    e4 = b.parse_trainer(FX("E4")[1])["heal_stock"]
    got = (lead, riv, b.hp_item_count(lead, b.item_parameter), b.hp_item_count(riv, b.item_parameter),
           b.hp_item_count(e4, b.item_parameter), b.hp_item_count([("Mystery Tonic", 2)], lambda _n: None))
    return eq(got, ([("Potion", 1), ("Full Heal", 1)], [], (1, []), (0, []), (35, []), (0, ["Mystery Tonic"])))


@row("HS2", "item probe HP items at KEY-battle start per group: leaders [1] (T-ON), elite_four [35] (Sidney), "
            "magma_aqua [1, 1] (Tabitha, Maxie); none unreadable")
def _hs2():
    s = IX().summarise([FX("TON"), FX("E4"), FX("MAGMA")])
    return eq((s["stock"], dict(s["stock_unread"])),
              ({"leaders": [1], "elite_four": [35], "rivals": [], "magma_aqua": [1, 1]}, {}))


@row("RD1", "N2: read_logs counts SUCCESSFUL reads (2 of 3; a missing file is not a log) and the report says so")
def _rd1():
    root, stats = TMP["root"], {}
    logs = list(BL().read_logs([root / "ton.debug.txt", root / "missing.log", root / "ton2.debug.txt"], stats))
    _code, out = _cli(lambda _a: BH().report(BH().summarise(logs), "x", stats["read"], stats["bytes"],
                                             matched=3), [])
    return eq((len(logs), stats["read"], BL().try_read(root / "missing.log"),
               "1 selected log(s) could NOT be read" in out), (2, 2, None, True))


@row("UR1", "N5: UNCLASSIFIED by reason — pre-start (a log entered mid-battle), no-telemetry (FX A without [TRAINER]), "
            "unreadable (`start unreadable`); a classified battle has no reason; both probes count them")
def _ur1():
    b = BL()
    orphan = b.split_battles(FX("ORPHAN"))[0]
    pre_t1 = no_trainer(FX("A"))
    got = (b.unclassified_reason(orphan, True), b.unclassified_reason(b.split_battles(pre_t1)[0], False),
           b.unclassified_reason(b.split_battles([Q("started"), SHAPES["tr_unread"]])[0], True),
           b.unclassified_reason(b.split_battles([Q("started"), Q("tr_leader")])[0], True),
           dict(BH().summarise([pre_t1])["reasons"]), dict(IX().summarise([pre_t1])["reasons"]))
    return eq(got, ("pre-start", "no-telemetry", "unreadable", None, {"no-telemetry": 6}, {"no-telemetry": 6}))


@row("NT1", "N1: the source header names ABSOLUTE paths — a relative --profiles and a relative --logs glob")
def _nt1():
    import argparse as _argparse
    got = []
    for argv, rel in ((["--since", "20260101", "--profiles", "relprof"], "relprof"), (["--logs", "rel*.log"], "rel*.log")):
        ap = _argparse.ArgumentParser()
        BL().add_source_args(ap, "S")
        _paths, source, _notes = BL().resolve_sources(ap.parse_args(argv), ap, "S")
        got.append(str(pathlib.Path(rel).absolute()) in source)
    return eq(got, [True, True])


@row("RP5", "item report on a SINGLES log with items and no [DBLITEM] / [KEYBATTLE] (FX A) exits 0 — data, not NO DATA")
def _rp5():
    return eq(quiet(IX().report, IX().summarise([FX("A")]), "x", 1, 1), 0)


# ============================================================================================ the run
def all_rows(verbose: bool) -> set:
    reds = set()
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


def provenance() -> None:
    """Every QUOTE is at its cited line, byte for byte; every FIXTURE starts and ends where its anchors say."""
    bad = []
    for name, (rel, n, text) in QUOTES.items():
        lines = _evidence(rel)
        if n > len(lines) or lines[n - 1] != text:
            bad.append(f"{name} ({rel}:{n})")
    for name, (rel, n, text) in QUOTES_IN.items():
        lines = _evidence(rel)
        if n > len(lines) or text not in lines[n - 1]:
            bad.append(f"{name} ({rel}:{n}, contained)")
    for name, (rel, a, b, p, q) in FIXTURES.items():
        lines = _evidence(rel)
        if not (b <= len(lines) and lines[a - 1].startswith(p) and lines[b - 1].startswith(q)):
            bad.append(f"fixture {name} ({rel}:{a}-{b})")
    check(f"PROVENANCE {len(QUOTES)} quoted lines at their cited evidence lines (+{len(QUOTES_IN)} contained), "
          f"{len(FIXTURES)} fixture slices anchored", not bad, f"mismatched: {bad}" if bad else "")


# ---------------------------------------------------------------------------------------------- mutants
#: (label, target, [(old, new), ...], the EXACT expected red set). Written BEFORE each mutant's first run.
def _drop(kind: str) -> list:
    """A dropped `[ITEM]` kind: its `ITEM_KINDS` entry commented out (so its lines fall to `unknown`)."""
    return [(f'    ("{kind}", re.compile(', f'    # ("{kind}", re.compile(')]


MUTANTS: list = [
    # ---- [TURN]
    ("M01 the OLD `\\s*$` anchor: a foe status suffix no longer parses", "bl",
     [(r'(\d+)/(\d+)(?: \[([^\]]*)\])?\s*$")', r'(\d+)/(\d+)(?: \[([^\]]*)\]){0}\s*$")')],
     {"TU3", "TU4", "TU7", "SB1", "SB3"}),
    ("M12 a `vs ?` line PARSED as data (parse_turn returns a record)", "bl",
     [("        return None\n    m = TURN_RE.search(line)", '        return Turn(0, "?", 0, 0, 0, None)\n    m = TURN_RE.search(line)')],
     {"TU5", "TU6"}),
    ("M13 a `vs ?` line COUNTED as parsed (turn_shape)", "bl",
     [('        return "no_foe"', '        return "parsed"')],
     {"TU5", "TU6", "SB2", "RP1", "RP2", "CL1"}),
    ("M44 the level read as the HP", "bl",
     [("int(lvl), int(hp), int(mx)", "int(lvl), int(lvl), int(mx)")],
     {"TU1", "TU2", "TU3", "TU4", "TU9", "SB4"}),
    ("M46 a malformed [TURN] line counted as NO FOE DATA instead of unparsed", "bl",
     [('    return "unparsed"', '    return "no_foe"')],
     {"TU8", "RP1"}),
    # ---- heals
    ("M22 heal identity by NAME only (a different-bulk switch reads as a heal)", "bl",
     [("key = (t.foe, t.max_hp)", "key = t.foe")],
     {"HE2"}),
    ("M23 an UNCHANGED HP counted as a heal (>=)", "bl",
     [("t.hp > last[key]", "t.hp >= last[key]")],
     {"HE3", "SB1", "SB2", "SB4"}),
    ("M47 no heal event ever recorded", "bl",           # RE-ANCHORED in fold 3: the event tuple gained `kind`
     [("            events.append((t.turn, t.foe, last[key], t.hp, kind))", "            pass")],
     {"HE1", "SB4"}),
    ("M24 the LARGE threshold moved (50 -> 150)", "bh",
     [("BIG_HEAL_HP = 50", "BIG_HEAL_HP = 150")],
     {"SB4"}),
    # ---- [ITEM] kinds (a dropped kind falls to `unknown`)
    ("M42 dropped kind: using", "bl", _drop("using"),
     {"IK1", "IK16", "SI1", "SI2", "SI3", "SI4", "SI5", "SI6", "RP3", "CL1"}),
    ("M02 dropped kind: consumed", "bl", _drop("consumed"),
     {"IK2", "IK16", "SI1", "SI2", "SI3", "SI4", "SI5", "RP3", "CL1"}),
    ("M50 dropped kind: landed (KI-101)", "bl", _drop("landed"), {"IK7", "IK16"}),
    ("M48 dropped kind: not_consumed_retry", "bl", _drop("not_consumed_retry"), {"IK3", "IK16", "SI6"}),
    ("M03 dropped kind: not_consumed_disable", "bl", _drop("not_consumed_disable"), {"IK4", "IK16", "SI6"}),
    ("M52 dropped kind: no_effect_retry (the shared shape)", "bl", _drop("no_effect_retry"),
     {"IK9", "IK16", "SI7", "SI8"}),
    ("M53 dropped kind: no_effect_disable", "bl", _drop("no_effect_disable"), {"IK10", "IK16"}),
    ("M04 dropped kind: cure_worked", "bl", _drop("cure_worked"), {"IK5", "IK16", "SI4"}),
    ("M49 dropped kind: cure_no_change", "bl", _drop("cure_no_change"), {"IK6", "IK16"}),
    ("M51 dropped kind: fresh_read_failed", "bl", _drop("fresh_read_failed"), {"IK8", "IK16"}),
    ("M05 dropped kind: legacy_landed", "bl", _drop("legacy_landed"), {"IK11", "IK16", "SI7", "SI8"}),
    ("M54 dropped kind: legacy_both_failed", "bl", _drop("legacy_both_failed"), {"IK12", "IK16", "SI7"}),
    ("M55 dropped kind: legacy_not_executing", "bl", _drop("legacy_not_executing"), {"IK13", "IK16"}),
    ("M18 an unknown [ITEM] line DROPPED (None) instead of counted", "bl",
     [('    return "unknown"', "    return None")],
     {"IK14", "RP3"}),
    ("M56 item_kind's guard loosened to `[ITEM` ([ITEM-FLOW] becomes an unknown item)", "bl",
     [('    if "[ITEM] " not in line:', '    if "[ITEM" not in line:')],
     {"IK15"}),
    # ---- key / non-key
    # ⛔ FOLD 3: B1's import-time partition check now REFUSES this mutant (the module cannot load), which is the
    # stronger kill; its first-pass set {TR6, TR9, BA2, BA5, SB1, SI3} (+SB5) is pinned by its twin M06b below, which
    # also removes the check.
    ("M06 KEY from the WRONG list (every TRAINER_CLASS value)", "bl",
     [("KEY_CLASSES = _trainer_identity.KEY_TRAINER_CLASSES",
       "KEY_CLASSES = frozenset(_trainer_identity.TRAINER_CLASS.values())")],
     "RAISES AssertionError: KEY_GROUPS != KEY_TRAINER_CLASSES"),
    ("M07 KEY derived BY NAME (the parenthesised ROM name looked up in TRAINER_CLASS)", "bl",
     [("out.append(int(m.group(1), 16) if m else None)",
       'out.append(_trainer_identity.TRAINER_CLASS.get(tok.strip().partition("(")[2].rstrip(")")) if m else None)')],
     {"TR1", "TR2", "TR4", "TR5", "TR10", "BA4", "BA7", "SB2", "SI1", "SI6"}),
    ("M08 a local COPY of the key list (equal values, not the source of truth)", "bl",
     [("KEY_CLASSES = _trainer_identity.KEY_TRAINER_CLASSES",
       "KEY_CLASSES = frozenset({0x20, 0x1F, 0x26, 0x32, 0x35, 0x0D, 0x31, 0x0B})")],
     {"TR9"}),
    ("M57 KEY never recognised", "bl",
     [("    if any(c is not None and c in KEY_CLASSES for c in classes):\n        return True",
       "    if any(c is not None and c in KEY_CLASSES for c in classes):\n        return False")],
     {"TR3", "TR4", "TR8", "BA4", "BA7", "SB2", "SB4", "SI2", "SI4", "SI9"}),
    ("M19 key_class fails CLOSED on an unreadable side", "bl",
     [("    if any(c is None for c in classes):\n        return None\n    return False",
       "    if any(c is None for c in classes):\n        return False\n    return False")],
     {"TR8"}),
    ("M40 only the FIRST opponent's class read (two-opponent B dropped)", "bl",
     [('for tok in field.split("+"):', 'for tok in field.split("+")[:1]:')],
     {"TR1", "TR10"}),
    ("M41 every [TRAINER] line read as kind start", "bl",
     [("        kind = word\n", '        kind = "start"\n')],
     {"TR7", "TR11", "BA6"}),
    # ---- battle classes / outcomes / splitting
    ("M09 WILD folded into NON-KEY (battle_class)", "bl",
     [("return WILD if trainer_telemetry else UNCLASSIFIED", "return NONKEY if trainer_telemetry else UNCLASSIFIED")],
     {"BA2", "BA4", "SB1", "SI3"}),
    ("M30 WILD folded into NON-KEY in the boss probe's aggregation", "bh",
     [("            cls = bl.battle_class(battle, t1)\n",
       "            cls = bl.battle_class(battle, t1)\n            cls = bl.NONKEY if cls == bl.WILD else cls\n")],
     {"SB1"}),
    ("M26 WILD folded into NON-KEY in the item probe's aggregation", "ix",
     [("            cls = bl.battle_class(battle, t1)\n",
       "            cls = bl.battle_class(battle, t1)\n            cls = bl.NONKEY if cls == bl.WILD else cls\n")],
     {"SI3"}),
    ("M20 [TRAINER] telemetry always assumed (a pre-T1 log's battles called WILD)", "bl",
     [('return any(route(line) == "trainer" for line in lines)', "return True")],
     {"BA3", "SB3", "SI5"}),
    ("M16 the segment before the first start DROPPED (its turns lost)", "bl",
     [("            cur = Battle(started=False)\n            battles.append(cur)", "            continue")],
     {"BA5"}),
    ("M17 Lost read as other", "bl", [('if res in ("Lost", "Draw"):', 'if res in ("Loss", "Draw"):')],  # RE-ANCHORED
     {"BA4"}),
    ("M38 no [TRAINER] end res= fallback for an outcome", "bl",
     [("    if res is None:\n        for line in battle.trainer:", "    if False:\n        for line in battle.trainer:")],
     {"BA6"}),
    ("M60 the outcome keeps its `BattleOutcome.` prefix", "bl",
     [(r'_OUTCOME = re.compile(r"ended \(outcome=(?:BattleOutcome\.)?([^)]*)\)")',
       r'_OUTCOME = re.compile(r"ended \(outcome=([^)]*)\)")')],
     {"BA1", "BA4", "BA5", "SI3"}),
    # ---- routing
    ("M15 [ITEM-FLOW] routed as an item line", "bl",
     [('if msg.startswith("[ITEM] "):', 'if msg.startswith("[ITEM"):')],
     {"RT2", "SI1", "SI2", "SI6"}),
    ("M34 stray tag mentions not detected", "bl", [('        return "stray"', "        return None")], {"RT3", "RP2"}),
    ("M35 [DBLITEM-OBS] routed as [DBLITEM]", "bl", [('            return "dblobs"', '            return "dblitem"')],
     {"RT1"}),
    # ---- [DBLITEM]
    ("M10 a partner rise MISSED: the first `hp=` (the target's) read as the partner's", "bl",
     [(r'_AFTER_PARTNER = re.compile(r"\bpartner=([^=]+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")',
       r'_AFTER_PARTNER = re.compile(r"()\bhp=(\S+?)->(\S+)")')],
     {"DB4", "DB5", "DB6", "DB7", "DB9", "DB10", "SI1", "SI2"}),
    ("M11 an UNCHANGED partner counted as a rise (>=)", "bl",
     [("now is not None and now > before", "now is not None and now >= before")],
     {"DB5", "DB6", "DB7", "SI2", "SI6"}),
    ("M36 a_pressed ignored", "bl", [('a_pressed=_int(f.get("a_pressed"))', "a_pressed=0")],
     {"DB1", "DB3", "DB10", "SI1"}),
    ("M58 ok read from the wrong field (aim=)", "bl", [('ok=_int(f.get("ok"))', 'ok=_int(f.get("aim"))')],
     {"DB1", "DB2", "DB3", "DB10", "SI1", "SI6"}),
    ("M59 a `use` line not recognised", "bl",
     [('("use", "menu", "after", "struggle-exit", "err")', '("menu", "after", "struggle-exit", "err")')],
     {"DB8", "DB10", "SI1", "SI6"}),
    # ---- the legacy verdict, the controls (D4), the I/O
    ("M27 the legacy verdict turned on by the SHARED retry shape", "ix",
     [('return bool(sum(s["legacy_landed"].values()) or s["legacy_both"])',
       'return bool(sum(s["legacy_landed"].values()) or s["legacy_both"] or sum(s["legacy_flips"].values()))')],
     {"SI8"}),
    ("M25 the boss report does not fail on an UNPARSED-with-foe-data line", "bh",
     [('    if s["unparsed"]:\n        failed = True', '    if s["unparsed"]:\n        failed = False')],
     {"RP1"}),
    ("M31 `vs ?` lines counted as UNPARSED in the boss probe", "bh",
     [('elif shape == "no_foe":', 'elif shape == "no_foe_":')],
     {"SB2", "RP1", "CL1"}),
    ("M28 requests with NO verdict line reported as data", "ix",
     [("    if requests and not verdicts:", "    if False:")],
     {"RP3"}),
    ("M14 select_logs IGNORES Old/", "bl",
     [('        logs.update({q.name: q for q in (lane / "debug-logs" / "Old").glob("*.log")})\n', "")],
     {"SL1", "SL2"}),
    ("M33 main_checkout returns the worktree itself", "bl",
     [('                return pathlib.Path(*parts[:parts.index("worktrees") - 1])', "                return repo")],
     {"SL3"}),
    # RE-ANCHORED 2026-10-01 (design v2 step 14 T2): `x4_logs` now reads `L<nn>` lanes through `batch_logs` (the old
    # `L0*` glob missed L10-L16 of a 16-lane batch); the mutant is the same idea — every directory is read as a lane.
    ("M32 x4_logs reads every lane directory, not only L<nn>", "bl",
     [('root.glob("L*") if p.is_dir() and _LANE_DIR.fullmatch(p.name))', 'root.glob("*") if p.is_dir())')], {"SL4"}),
    # ---- mention-only: a gate that fires on a comment teaches the reader to bypass it
    ("MM1 MENTION ONLY: a comment writing `return NONKEY if trainer_telemetry` turns NOTHING red", "bl",
     [("#: Report order. ⛔ WILD is its own class, never folded into NON-KEY (design D2)",
       "#: Report order. ⛔ WILD is its own class — never `return NONKEY if trainer_telemetry` (design D2)")],
     set()),
    ("MM2 MENTION ONLY: a comment writing `failed = False` turns NOTHING red", "ix",
     [("# print ok,A and ok,noA as disjoint columns",
       "# print ok,A and ok,noA as disjoint columns; never `failed = False` on an unknown kind")],
     set()),
    ("MM3 MENTION ONLY: a docstring writing `return \"no_foe\"` turns NOTHING red", "bh",
     [("pattern used to end", 'pattern (never `return "no_foe"` for data) used to end')],
     set()),
]

#: THE FOLD (the builder's own sweep, after the 57 above ran green). What each EXISTING mutant ALSO reddens on the
#: fold's new rows (TU10 IK17 DB11 DB12 SB5 BA8 RP4 CL2 CL3); its exact set is its own UNION this. Written before
#: the fold's first run.
MUTANT_ADDITIONS = {
    "M01": {"TU10"},                # the Farfetch’d line carries a foe suffix
    "M44": {"TU10", "SB5"},         # hp = level: the names row's HP, and Sidney's heal vanishes
    "M47": {"SB5"}, "M24": {"SB5"},  # no LARGE heal -> long_big 0
    "M06": {"SB5"}, "M09": {"SB5"}, "M30": {"SB5"},   # FX A's NON-KEY / WILD with-turns move
    "M57": {"SB5"},                 # Sidney is no longer KEY
    "M36": {"DB12"}, "M58": {"DB12"},
    "M07": {"BA8"},                 # by name, HEX_MANIAC/COLLECTOR read as unreadable
    "M42": {"RP4", "CL2"}, "M02": {"RP4", "CL2"},     # Sidney / T-ON gain an unknown kind
    "M04": {"RP4"},                 # Sidney's cure becomes unknown
    "M34": {"RP4"},                 # the stray no longer fails the item report
    "M14": {"CL2"},                 # 2 logs, not 4
    "M13": {"CL2"}, "M31": {"CL2"},  # the boss CLI on T-ON raises / exits 1
    # FOLD 2 (DB13, the `_AFTER_TARGET` label fix): the first `hp=` is the unreadable target's `?->117`
    "M10": {"DB13"},
}

FOLD_MUTANTS: list = [
    ("M61 the OLD ASCII name class `[A-Za-z' .-]` (Nidoran♀ / Farfetch’d lost)", "bl",
     [(r"+vs (.+?) L(\d+)", r"+vs ([A-Za-z' .-]+?) L(\d+)")],
     {"TU10"}),
    ("M62 after_err not counted", "bl", [('                c["after_err"] += 1', "                pass")], {"DB11"}),
    ("M63 a struggle-exit line not recognised", "bl",
     [('("use", "menu", "after", "struggle-exit", "err")', '("use", "menu", "after", "err")')], {"DB11"}),
    ("M64 an err line not recognised", "bl",
     [('("use", "menu", "after", "struggle-exit", "err")', '("use", "menu", "after", "struggle-exit")')], {"DB11"}),
    ("M65 VERDICT_KINDS lacks `landed`", "bl",
     [('VERDICT_KINDS = frozenset({"consumed", "landed", ', 'VERDICT_KINDS = frozenset({"consumed", ')], {"IK17"}),
    ("M66 NO_EFFECT_KINDS lacks `legacy_not_executing`", "bl",
     [('NO_EFFECT_KINDS = frozenset({"no_effect_retry", "no_effect_disable", "legacy_both_failed", "legacy_not_executing"})',
       'NO_EFFECT_KINDS = frozenset({"no_effect_retry", "no_effect_disable", "legacy_both_failed"})')], {"IK17"}),
    ("M67 every menu pass counted as not-pressed", "bl",
     [('                if d["a_pressed"] != 1:', '                if d["a_pressed"] != 0:')], {"DB12"}),
    ("M68 with_turns double-counted (boss probe)", "bh",
     [('            row["with_turns"] += 1', '            row["with_turns"] += 2')], {"SB5"}),
    ("M69 the boss-length PROXY moved (12 -> 120 turns)", "bh",
     [("LONG_BATTLE_TURNS = 12", "LONG_BATTLE_TURNS = 120")], {"SB5"}),
    ("M70 classes read from [TRAINER] START lines only (an end-only battle unclassified)", "bl",
     [('if t and t["kind"] in ("start", "end"):', 'if t and t["kind"] == "start":')], {"BA8"}),
    # ⛔ FOLD 3 RE-ANCHORED, AND ITS SET MOVES {RP4} -> {RP5, X9}: S2 makes a [KEYBATTLE] line count as data, so Sidney
    # (which has one) no longer exits 1 under this mutant; a singles log with neither (RP5, FX A) and an observe-only
    # log (X9) do. Written before the fold's first run.
    ("M71 NO DATA when EITHER [ITEM] or [DBLITEM] is absent (every singles log)", "ix",
     [('    no_item_data = not s["item_lines"] and not s["dbl_lines"]',
       '    no_item_data = not s["item_lines"] or not s["dbl_lines"]')],
     {"RP5", "X9"}),
    ("M72 the item report does not fail on a stray line", "ix",
     [('    if s["stray"]:\n        failed = True', '    if s["stray"]:\n        failed = False')], {"RP4"}),
    ("M73 a [KEYBATTLE] disagreement fails the item report (a finding is not a probe failure)", "ix",
     [('print(f"      ‼ a FINDING about the production gate, not a probe failure: [{cls}] {line}")',
       'print(f"      ‼ a FINDING about the production gate, not a probe failure: [{cls}] {line}")\n'
       '            failed = True')],
     {"RP4"}),
    # FOLD 3 RE-ANCHORED: the CLI moved into `battle_log.resolve_sources` (S6), shared by both probes; CL2 / CL3 test
    # both CLIs, so the first-pass sets hold.
    ("M74 the CLI ignores --profiles", "bl",
     [("args.profiles or default_profiles()", "default_profiles()")],
     {"CL2"}),
    ("M75 the CLI ignores --until", "bl",
     [("        until = args.until or args.since", "        until = args.since")], {"CL2"}),
    ("M76 the CLI accepts a stamp AND --logs", "bl", [("    if modes > 1:", "    if False:")], {"CL3"}),
    # FOLD 2 — the REVERT of the `_AFTER_TARGET` label fix (the pre-fix source): DB13 must be red on it
    ("M77 REVERT: the target label back to `.+?` (runs into the partner's label)", "bl",
     [(r'_AFTER_TARGET = re.compile(r"\btarget=([^=]+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")',
       r'_AFTER_TARGET = re.compile(r"\btarget=(.+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")')],
     {"DB13"}),
]
#: FOLD 3 (the independent pass). What each EXISTING mutant ALSO reddens on the fold-3 rows (X1-X25, OC*, KG*, AT*,
#: KB*, LI*, RS*, DD1, SC*, HS*, RD1, UR1, NT1, RP5); its exact set is its own UNION this (UNION fold 1's). Written
#: before the fold's first run. (M71's set is REPLACED, not added to — see its entry.)
MUTANT_ADDITIONS3 = {
    "M01": {"RS2"},                                    # the Rest line's foe suffix [Sleep] no longer parses
    "M13": {"X22", "X16", "KG4", "DD1", "SC3", "X17", "RD1"},   # the boss probe raises on any `vs ?` battle
    "M44": {"X14", "X15", "KG5", "RS2"},               # hp = level: every rise vanishes
    "M47": {"X14", "X15", "KG5", "RS1", "RS2"},
    "M24": {"X14", "X15", "KG5"},
    "M42": {"X8", "X10", "RP5"}, "M02": {"RP5"},       # a dropped kind is `unknown`: the item report fails
    "M50": {"X8"}, "M53": {"X8"}, "M49": {"X8"}, "M51": {"X8"}, "M55": {"X8"}, "M18": {"X8"}, "M66": {"X8"},
    "M48": {"X10"}, "M03": {"X10"},
    "M07": {"X4", "X7", "KG3", "KG4", "KG5"},          # by name: HEX_MANIAC, SCHOOL_KID, PkMn_TRAINER read as None
    "M57": {"X3", "X5", "X6", "X8", "X14", "X15", "KG4", "KG5", "AT2", "DD1", "RS2", "HS2"},
    "M19": {"X4"}, "M40": {"X4", "X5", "KG3"},
    "M41": {"X2", "OC2"},                              # an end read as a start: no res= fallback
    "M09": {"X7"}, "M30": {"X7"}, "M26": {"X7"},
    "M20": {"UR1"}, "M16": {"UR1"},
    "M17": {"X2", "KG4", "KG5", "AT2", "OC2"}, "M38": {"X2", "OC2"},
    "M60": {"X1D", "KG4", "KG5", "AT2", "X25"},
    "M34": {"X23"},
    "M10": {"LI2", "LI3", "X13"}, "M11": {"LI2", "LI3"},
    "M14": {"X17", "SC1", "SC2", "SC3"},
    "M74": {"X17", "SC3", "NT1"},                      # --profiles ignored: the MAIN checkout's real corpus is read
    "M75": {"X17"},                                    # --until alone: until = None (a TypeError)
}

#: The INDEPENDENT mutant hunter's real mutants (N01-N83, `scratchpad/mut27/mutants.py`), RE-ANCHORED to the folded
#: code where it moved, each with the exact set written before its first run here. LEFT OUT, with the hunter's own
#: argument (equivalent or unreachable on every line the emitters print): N05 (0 of 228 [ITEM] lines fall outside
#: started..ended), N10 (start lines carry no res=), N11 (both read the same outcome), N22 (logs open fresh per run),
#: N28 (the class list is empty either way), N44 (`press = ok or …`), N46 (no move runs between the reads), N47 (`err=`
#: only in the except branch), N49 (observe lines never parse as [DBLITEM]), N50 (`ok=` is always an int), N51 (no
#: species name with a space in Emerald's trainer parties), N52 (`?` only when the mon is None), N53 (no ` vs ` in the
#: player's half), N55 (`[]` is never emitted), N56 (the probes call `turn_shape` on routed turns only), N62 (0 LARGE
#: non-adjacent rises), N63 (a foe's level is fixed in battle). DROPPED: N09 (Draw -> lost) — it IS the fix now; F01
#: reverts it.
HUNTER_MUTANTS: list = [
    ("N01 split: [BATTLE] ended CLOSES the record", "bl",
     [("            if cur.outcome is None and m:\n                cur.outcome = m.group(1)\n",
       "            if cur.outcome is None and m:\n                cur.outcome = m.group(1)\n            cur = None\n")],
     {"BA1", "BA2", "BA4", "BA5", "BA7", "OC2"}),
    ("N02 split: a 2nd start while the record has NO end is MERGED", "bl",
     [('        if kind == "start":\n            cur = Battle(started=True)\n            battles.append(cur)\n            continue',
       '        if kind == "start":\n            if cur is None or cur.outcome is not None or not cur.started:\n'
       '                cur = Battle(started=True)\n                battles.append(cur)\n            continue')],
     {"X3", "X14", "X25"}),
    ("N03 split: the pre-first-start segment marked started=True", "bl",
     [("            cur = Battle(started=False)\n", "            cur = Battle(started=True)\n")], {"BA5", "UR1"}),
    ("N04 split: [TRAINER] lines after [BATTLE] ended are dropped", "bl",
     [('        elif kind == "trainer":\n            cur.trainer.append(line)',
       '        elif kind == "trainer":\n            if cur.outcome is None:\n                cur.trainer.append(line)')],
     {"BA4", "OC2"}),
    ("N06 outcome: Caught -> won", "bl", [('    if res == "Won":', '    if res in ("Won", "Caught"):')],
     {"BA6", "SI3", "X1"}),
    ("N07 outcome: RanAway -> won", "bl", [('    if res == "Won":', '    if res in ("Won", "RanAway"):')], {"X1"}),
    ("N08 outcome: OpponentTeleported -> won", "bl",
     [('    if res == "Won":', '    if res in ("Won", "OpponentTeleported"):')], {"X1"}),
    # ⚠ CORRECTED after its first run: as filed {BA6, X25}; observed + X24 — N6's fix turns `outcome=None` into an
    # unreadable outcome (res None), which this mutant then calls lost. The observed set is the right one.
    ("N12 outcome: a battle the log never ends -> lost", "bl",
     [('    return "other"\n\n\ndef win_rate', '    return "lost" if res is None else "other"\n\n\ndef win_rate')],
     {"BA6", "X24", "X25"}),
    ("N13 outcome: the fallback takes an end only if res is Won", "bl",
     [('            if t and t["kind"] == "end" and t["res"]:', '            if t and t["kind"] == "end" and t["res"] == "Won":')],
     {"X2", "OC2"}),
    ("N14 class: [TRAINER] lines with NO class (unreadable / skip-only) -> WILD", "bl",
     [("    if battle.trainer:\n        verdict = key_class(battle_classes(battle))",
       "    if battle_classes(battle):\n        verdict = key_class(battle_classes(battle))")], {"X3", "UR1"}),
    ("N15 class: battle_classes reads only the FIRST start/end line", "bl",
     [('        if t and t["kind"] in ("start", "end"):\n            out.extend(t["classes"])',
       '        if t and t["kind"] in ("start", "end"):\n            out.extend(t["classes"])\n            break')], {"X6"}),
    ("N16 class: battle_classes reads only opponent A", "bl",
     [('            out.extend(t["classes"])', '            out.extend(t["classes"][:1])')], {"X4", "X5"}),
    ("N17 class: battle_classes keeps only the LAST line", "bl",
     [('            out.extend(t["classes"])', '            out[:] = t["classes"]')], {"X6"}),
    ("N18 class: a `?` side parsed as class 0", "bl",
     [("        out.append(int(m.group(1), 16) if m else None)", "        out.append(int(m.group(1), 16) if m else 0)")],
     {"X4"}),
    ("N19 class: a `?` side DROPPED", "bl",
     [("        out.append(int(m.group(1), 16) if m else None)", "        if m:\n            out.append(int(m.group(1), 16))")],
     {"X4"}),
    ("N20 class: an unreadable side ignored unless ALL are", "bl",
     [("    if any(c is None for c in classes):\n        return None\n    return False",
       "    if all(c is None for c in classes):\n        return None\n    return False")], {"TR8", "X4"}),
    ("N21 class: key_class([]) -> False", "bl",
     [("    if not classes:\n        return None", "    if not classes:\n        return False")],
     {"TR8", "X3", "X11", "UR1", "KB2"}),
    ("N23 class (boss probe): telemetry known only AFTER the first [TRAINER] line", "bh",
     [("        for battle in bl.split_battles(lines):\n            cls = bl.battle_class(battle, t1)\n"
       "            facts = bl.battle_facts(battle, t1)\n",
       "        seen_t1 = False\n        for battle in bl.split_battles(lines):\n"
       "            seen_t1 = seen_t1 or bool(battle.trainer)\n            cls = bl.battle_class(battle, seen_t1)\n"
       "            facts = bl.battle_facts(battle, seen_t1)\n")], {"X7"}),
    ("N24 class (item probe): telemetry known only AFTER the first [TRAINER] line", "ix",
     [("        for battle in bl.split_battles(lines):\n            cls = bl.battle_class(battle, t1)\n"
       "            out = bl.outcome_bucket(battle)\n            facts = bl.battle_facts(battle, t1)\n",
       "        seen_t1 = False\n        for battle in bl.split_battles(lines):\n"
       "            seen_t1 = seen_t1 or bool(battle.trainer)\n            cls = bl.battle_class(battle, seen_t1)\n"
       "            out = bl.outcome_bucket(battle)\n            facts = bl.battle_facts(battle, seen_t1)\n")], {"X7"}),
    ("N25 class: the pre-first-start segment classified from its [TRAINER] lines", "bl",
     [("    if not battle.started:\n        return UNCLASSIFIED\n    if battle.trainer:", "    if battle.trainer:")],
     {"BA5", "UR1"}),
    ("N26 class: a pre-T1 log's trainer-less battles called WILD", "bl",
     [("    return WILD if trainer_telemetry else UNCLASSIFIED", "    return WILD")], {"BA3", "SB3", "SI5", "UR1"}),
    ("N27 class: an unreadable verdict folded into NON-KEY", "bl",
     [("    return KEY if verdict is True else NONKEY if verdict is False else UNCLASSIFIED",
       "    return KEY if verdict is True else NONKEY")], {"X3", "X4", "X11", "UR1", "KB2"}),
    ("N29 class: a hex class id read with lowercase digits only", "bl",
     [(r'_CLASS_TOKEN = re.compile(r"^0x([0-9A-Fa-f]+)(?:\([^)]*\))?$")',
       r'_CLASS_TOKEN = re.compile(r"^0x([0-9a-f]+)(?:\([^)]*\))?$")')],
     {"BA7", "BA8", "SB2", "SB4", "SB5", "SI1", "SI4", "SI6", "TR1", "TR10", "TR2", "X4", "KG3", "KG4", "KG5", "HS2"}),
    ("N30 class: a [TRAINER] skip's absent class list read as [None]", "bl",
     [('"classes": parse_classes(f["class"]) if "class" in f else [],',
       '"classes": parse_classes(f["class"]) if "class" in f else [None],')], {"TR7"}),
    ("N31 items: no_effect column always 0", "ix",
     [('    r["no_effect"] = sum(kinds[k] for k in bl.NO_EFFECT_KINDS)', '    r["no_effect"] = 0')], {"X8"}),
    ("N32 items: no_effect counts today's kinds only", "ix",
     [('    r["no_effect"] = sum(kinds[k] for k in bl.NO_EFFECT_KINDS)',
       '    r["no_effect"] = kinds["no_effect_retry"] + kinds["no_effect_disable"]')], {"X8"}),
    ("N33 items: landed column dropped", "ix",
     [('    for k in ("consumed", "landed", "not_consumed_retry",', '    for k in ("consumed", "not_consumed_retry",')],
     {"X8"}),
    ("N34 items: cure_no_change column dropped", "ix",
     [('"not_consumed_disable", "cure_worked", "cure_no_change",\n              "fresh_read_failed"',
       '"not_consumed_disable", "cure_worked",\n              "fresh_read_failed"')], {"X8"}),
    ("N35 items: fresh_read_failed column dropped", "ix",
     [('              "fresh_read_failed", "unknown"):', '              "unknown",):')], {"X8"}),
    ("N36 items: the per-class unknown column dropped", "ix",
     [('              "fresh_read_failed", "unknown"):', '              "fresh_read_failed",):')], {"X8"}),
    ("N37 items: no_verdict ignores cure verdicts", "ix",
     [('    r["no_verdict"] = kinds["using"] - sum(kinds[k] for k in bl.VERDICT_KINDS)',
       '    r["no_verdict"] = kinds["using"] - sum(kinds[k] for k in bl.VERDICT_KINDS if not k.startswith("cure"))')],
     {"SI4"}),
    ("N38 items: [DBLITEM-OBS] lines not counted as data", "ix",
     [('        s["dbl_lines"] += len(battle.dblitem) + len(battle.dblobs)', '        s["dbl_lines"] += len(battle.dblitem)')],
     {"X9"}),
    ("N39 items: the NO-VERDICT control counts only CONSUMED", "ix",
     [('    verdicts = sum(s["kinds"][k] for k in bl.VERDICT_KINDS)', '    verdicts = s["kinds"]["consumed"]')], {"X10"}),
    ("N40 items: [KEYBATTLE] disagreement also counted in UNCLASSIFIED / WILD battles", "ix",
     [("        offline = {bl.KEY: True, bl.NONKEY: False}.get(cls)",
       "        offline = {bl.KEY: True, bl.NONKEY: False, bl.UNCLASSIFIED: False, bl.WILD: False}.get(cls)")],
     {"X11", "KB2"}),
    ("N41 items: requests counted from [DBLITEM] use lines too", "ix",
     [('    r["requests"] = kinds["using"]',
       '    r["requests"] = kinds["using"] + sum(1 for x in battle.dblitem if " [DBLITEM] use " in x)')],
     {"SI1", "SI2", "SI6"}),
    ("N42 items: item_battles counts only battles with a `using` request", "ix",
     [('    r["item_battles"] = int(bool(battle.items) or bool(battle.dblitem))', '    r["item_battles"] = int(kinds["using"] > 0)')],
     {"X12"}),
    ("N43 dbl: wrong_target counted once per battle", "bl",
     [('                c["wrong_target"] += 1', '                c["wrong_target"] = 1')], {"X13"}),
    ("N45 dbl: a refusal counted as pressed whenever a_pressed is present", "bl",
     [('                if d["a_pressed"] == 1:\n                    c["menu_refused_pressed"] += 1',
       '                if d["a_pressed"] is not None:\n                    c["menu_refused_pressed"] += 1')], {"SI6"}),
    ("N48 dbl: partner hp digits only (a `?` partner unparsed)", "bl",
     [(r'_AFTER_PARTNER = re.compile(r"\bpartner=([^=]+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")',
       r'_AFTER_PARTNER = re.compile(r"\bpartner=([^=]+?#[0-9A-F]{8}|\?) hp=(\d+)->(\d+)")')], {"DB9"}),
    ("N54 turn: hp and max swapped", "bl", [("int(lvl), int(hp), int(mx)", "int(lvl), int(mx), int(hp)")],
     {"SB4", "SB5", "TU2", "TU3", "TU4", "X14", "X15", "KG5", "RS2"}),
    ("N57 heal: every heal LARGE (the small class unquarantined)", "bh",
     [("            big = [e for e in events if e[3] - e[2] >= BIG_HEAL_HP]", "            big = list(events)")], {"X14"}),
    ("N58 heal: LARGE threshold strict (> 50)", "bh",
     [("            big = [e for e in events if e[3] - e[2] >= BIG_HEAL_HP]",
       "            big = [e for e in events if e[3] - e[2] > BIG_HEAL_HP]")], {"X15"}),
    ("N59 heal: LARGE judged on the post-heal HP", "bh",
     [("            big = [e for e in events if e[3] - e[2] >= BIG_HEAL_HP]",
       "            big = [e for e in events if e[3] >= BIG_HEAL_HP]")], {"X14"}),
    ("N60 heal: any_battles counts LARGE-heal battles only", "bh",
     [('            row["any_battles"] += int(bool(events))', '            row["any_battles"] += int(bool(big))')], {"X14"}),
    ("N61 heal: compared to the FIRST HP ever seen", "bl",
     [("        last[key] = t.hp", "        last.setdefault(key, t.hp)")], {"SB4", "SB5", "X14", "KG5"}),
    ("N64 heal: the events list keeps LARGE heals only", "bh",
     [('            s["events"].extend((cls, e[3] - e[2], e[1], e[2], e[3]) for e in events)',
       '            s["events"].extend((cls, e[3] - e[2], e[1], e[2], e[3]) for e in big)')], {"X14"}),
    ("N65 heal: the boss-length proxy counts [TURN] lines, not parsed records", "bh",
     [("            if len(turns) >= LONG_BATTLE_TURNS:", "            if len(battle.turns) >= LONG_BATTLE_TURNS:")],
     {"X16"}),
    ("N66 cli: --since alone reads to the end of time", "bl",
     [("        until = args.until or args.since", '        until = args.until or "99999999"')], {"X17", "SC3"}),
    ("N67 cli: --until alone reads from the beginning of time", "bl",
     [("        since = args.since or args.until", '        since = args.since or "00000000"')], {"X17"}),
    ("N68 io: default profiles = the WORKTREE's", "bl",
     [('    return main_checkout() / "sandbox-pokebot" / "profiles"', '    return REPO / "sandbox-pokebot" / "profiles"')],
     {"X18"}),
    ("N69 io: strict UTF-8 decode (a cut character raises)", "bl",
     [('    return data.decode("utf-8", errors="replace").splitlines(), len(data)',
       '    return data.decode("utf-8").splitlines(), len(data)')], {"X19"}),
    ("N70 io: split on \\n (a trailing empty line, \\r kept)", "bl",
     [('    return data.decode("utf-8", errors="replace").splitlines(), len(data)',
       '    return data.decode("utf-8", errors="replace").split("\\n"), len(data)')], {"SL4"}),
    ("N71 io: debug-logs/ wins over Old/ for a name in both", "bl",
     [('        logs = {q.name: q for q in (lane / "debug-logs").glob("*.log")}\n'
       '        logs.update({q.name: q for q in (lane / "debug-logs" / "Old").glob("*.log")})',
       '        logs = {q.name: q for q in (lane / "debug-logs" / "Old").glob("*.log")}\n'
       '        logs.update({q.name: q for q in (lane / "debug-logs").glob("*.log")})')], {"SL1", "SL2"}),
    ("N72 io: lanes `endless-*`", "bl",
     [('    for lane in sorted(p for p in root.glob("endless-P*") if p.is_dir()):',
       '    for lane in sorted(p for p in root.glob("endless-*") if p.is_dir()):')],
     {"CL2", "SL1", "SL2", "X17", "X20", "SC1", "SC2", "SC3"}),
    ("N73 io: the day read from the stamp's LAST field (HHMMSS)", "bl",
     [('            day = stamp.split("-")[0]', '            day = stamp.split("-")[-1]')],
     {"CL2", "SL1", "SL2", "X17", "SC1", "SC2", "SC3"}),
    ("N74 cli: --profiles / --lanes without --since accepted", "bl",
     [("    if (args.profiles or args.lanes) and not (args.since or args.until):", "    if False:")], {"X21"}),
    ("N75 control (boss): 'nothing parsed' judged on [TURN] lines", "bh",
     [('    if not s["parsed"]:\n        print("  ‼ CONTROL FAILED — no turn record parsed.',
       '    if not s["turn_lines"]:\n        print("  ‼ CONTROL FAILED — no turn record parsed.')], {"X22"}),
    ("N76 control (item): NO DATA exits 0", "ix",
     [("    return 1 if failed or nodata or noverdict else 0", "    return 1 if failed or noverdict else 0")],
     {"RP3", "KB3"}),
    ("N77 control (boss): a stray line does not fail", "bh",
     [('    if s["stray"]:\n        failed = True', '    if s["stray"]:\n        failed = False')], {"RP2"}),
    ("N78 control (item): an unknown kind does not fail", "ix",
     [('    if s["unknown"]:\n        failed = True', '    if s["unknown"]:\n        failed = False')], {"RP3"}),
    ("N79 control (boss): no logs exits 0", "bh",
     [('Check the stamp / --since/--until / --profiles / --logs.")\n        return 1',
       'Check the stamp / --since/--until / --profiles / --logs.")\n        return 0')], {"CL1", "CL2", "RP2"}),
    ("N80 route: a quoted [TURN] in another category is not stray", "bl",
     [('_TAG_MARKERS = ("[TURN ", "[ITEM] ",', '_TAG_MARKERS = ("[ITEM] ",')], {"X23"}),
    ("N81 route: a quoted [TRAINER] in another category is not stray", "bl",
     [('"[TRAINER] ", "[KEYBATTLE] ",', '"[KEYBATTLE] ",')], {"X23"}),
    ("N82 route: [ITEM-FLOW] reported as STRAY", "bl",
     [('_TAG_MARKERS = ("[TURN ", "[ITEM] ",', '_TAG_MARKERS = ("[TURN ", "[ITEM",')],
     {"CL1", "CL2", "RP1", "RP3", "RP4", "RT2", "X10"}),
    ("N83 route: [BATTLE] ended routed only for BattleOutcome.* values", "bl",
     [('            if msg.startswith("ended (outcome="):', '            if msg.startswith("ended (outcome=BattleOutcome."):')],
     {"X24"}),
]

#: FOLD 3's own mutants: a REVERT of each fix (each must redden exactly its fix's rows — the "red on the unfixed code"
#: half of the proof; the baseline is the "green on the fixed code" half), and the check M06 can no longer reach.
FOLD3_MUTANTS: list = [
    ("F01 REVERT B2: a Draw back to other", "bl", [('    if res in ("Lost", "Draw"):', '    if res == "Lost":')], {"X1D"}),
    ("F02 REVERT N6: `outcome=None` blocks the [TRAINER] end fallback", "bl",
     [('    res = battle.outcome if battle.outcome not in (None, "None") else None', "    res = battle.outcome")], {"OC2"}),
    ("F03 REVERT B1: the import-time partition check never called", "bl",
     [("\ncheck_key_groups(KEY_GROUPS, KEY_CLASSES)\n", "\n")], {"KG7"}),
    ("F04 the partition check ignores a MISSING key class", "bl",
     [("    if union != frozenset(key_classes):", "    if False:")], {"KG2", "KG7"}),
    ("F05 the partition check ignores an OVERLAP", "bl",
     [("    if sum(len(ids) for ids in groups.values()) != len(union):", "    if False:")], {"KG2"}),
    ("F06 key_group reads opponent A only", "bl",
     [("        if any(c is not None and c in ids for c in classes):",
       "        if any(c is not None and c in ids for c in classes[:1]):")], {"KG3"}),
    # ⚠ CORRECTED after its first run: as filed {KG1, KG7}; observed + KG2 — KG2's "missing" case removes 0x26 from
    # elite_four, which no longer holds it here, so the groups still partition and the check (rightly) does not raise.
    ("F07 the Champion grouped with the leaders (still a partition)", "bl",
     [('    "leaders": frozenset({_TC["LEADER"]}),\n    "elite_four": frozenset({_TC["ELITE_FOUR"], _TC["CHAMPION"]}),',
       '    "leaders": frozenset({_TC["LEADER"], _TC["CHAMPION"]}),\n    "elite_four": frozenset({_TC["ELITE_FOUR"]}),')],
     {"KG1", "KG2", "KG7"}),
    ("F08 REVERT S1: the 'first attempt' is the LAST", "bl",
     [('        g["first"][outcomes[0]] += 1', '        g["first"][outcomes[-1]] += 1')], {"AT1", "AT2"}),
    ("F09 attempts to win off by one", "bl",
     [('            g["attempts_to_win"].append(outcomes.index("won") + 1)',
       '            g["attempts_to_win"].append(outcomes.index("won"))')], {"AT1", "AT2"}),
    ("F10 attempts pooled across logs (per trainer, not per run)", "bl",
     [("        pairs.setdefault((group, log_id, opp), []).append(outcome)",
       "        pairs.setdefault((group, 0, opp), []).append(outcome)")], {"AT1", "AT2"}),
    ("F11 REVERT B1 (boss): outcomes of LARGE-heal battles not counted", "bh",
     [('                row["big_" + out] += 1', "                pass")], {"KG5"}),
    ("F12 REVERT S2: a [KEYBATTLE]-only log is NO DATA again", "ix",
     [('    nodata = no_item_data and not s["keybattle"]', "    nodata = no_item_data")], {"KB1"}),
    ("F13 REVERT S2: a [KEYBATTLE] with no offline class not counted", "ix",
     [('                if offline is None:\n                    s["kb_no_offline"].append((cls, line))',
       '                if False:\n                    s["kb_no_offline"].append((cls, line))')], {"KB2"}),
    ("F14 REVERT S2: NO DATA returns BEFORE the outcome tables", "ix",
     [('    requests = sum(r["requests"] for r in s["by_class"].values())',
       '    if nodata:\n        return 1\n    requests = sum(r["requests"] for r in s["by_class"].values())')], {"KB3"}),
    ("F15 lost_item ignores same=", "bl",
     [('    return q1 < q0 and h1 <= h0 and after.get("same") == 1 and not partner_rose(after)',
       "    return q1 < q0 and h1 <= h0 and not partner_rose(after)")], {"LI2"}),
    ("F16 lost_item ignores a partner rise (double-counts a wrong target)", "bl",
     [('    return q1 < q0 and h1 <= h0 and after.get("same") == 1 and not partner_rose(after)',
       '    return q1 < q0 and h1 <= h0 and after.get("same") == 1')], {"LI2", "LI3"}),
    ("F17 the item name label `.+?` (runs from the target's hp= field)", "bl",
     [(r'_AFTER_ITEM = re.compile(r" hp=\S+ ([^=]+?)=', r'_AFTER_ITEM = re.compile(r" hp=\S+ (.+?)=')], {"LI1"}),
    ("F18 REVERT S4: Rest never tagged", "bl",
     [('            kind = "rest" if _gains_sleep(last_status.get(key), t.status) else "heal"', '            kind = "heal"')],
     {"RS1", "RS2"}),
    ("F19 Rest = any rise while asleep (not NEWLY asleep)", "bl",
     [('    return "Sleep" in (now_status or "").split("/") and "Sleep" not in (before_status or "").split("/")',
       '    return "Sleep" in (now_status or "").split("/")')], {"RS1"}),
    ("F20 REVERT S4 (boss): Rest rises counted as heals", "bh",
     [('            events = [e[:4] for e in all_events if e[4] != "rest"]',
       "            events = [e[:4] for e in all_events]")], {"RS2"}),
    ("F21 REVERT S5: the doubles column never counts", "bh",
     [('            row["doubles"] += int(bool(facts["double"]))', '            row["doubles"] += 0')], {"DD1"}),
    ("F22 doubles read from two= instead of double=", "bl",
     [('            double = t["double"] == "True"', '            double = t["two"] == "True"')], {"DD1"}),
    ("F23 REVERT S6: logs before the window not counted", "bl",
     [('            elif day < since:\n                out["before"] += 1', '            elif False:\n                out["before"] += 1')],
     {"SC1", "SC3"}),
    ("F24 REVERT S6: --lanes ignored", "bl",
     [("        if lanes and not any(s in lane.name for s in lanes):", "        if False:")], {"SC2", "SC3"}),
    ("F25 REVERT S6: a repeated --logs keeps only the first glob", "bl",
     [("    patterns = [pattern] if isinstance(pattern, str) else list(pattern)",
       "    patterns = [pattern] if isinstance(pattern, str) else list(pattern)[:1]")], {"SC4"}),
    ("F26 REVERT N2: --logs matches directories too", "bl",
     [("    found = {pathlib.Path(p) for pat in patterns for p in glob.glob(pat) if pathlib.Path(p).is_file()}",
       "    found = {pathlib.Path(p) for pat in patterns for p in glob.glob(pat)}")], {"SC4"}),
    ("F27 REVERT S6: no warning for --since alone", "bl",
     [("        if not (args.since and args.until):", "        if False:")], {"SC3"}),
    ("F28 heal stock counts EVERY healing item (cures and Revives too)", "bl",
     [("        elif param > 0:", "        else:")], {"HS1", "HS2"}),
    ("F29 heal stock names keep the emitter's `_`", "bl",
     [('        out.append((name.replace("_", " "), int(qty)))', "        out.append((name, int(qty)))")], {"HS1", "HS2"}),
    ("F30 heal stock read at battle END, not start", "bl",
     [('        if t["kind"] == "start" and stock is None:', '        if t["kind"] == "end":')], {"HS2"}),
    ("F31 REVERT N2: an unreadable log counted as read", "bl",
     [("        if got is None:\n            continue", "        if got is None:\n            got = ([], 0)")], {"RD1"}),
    ("F32 UNCLASSIFIED reasons: an unreadable trainer battle reported as 'no-telemetry'", "bl",
     [('    if battle.trainer:\n        return "unreadable"', '    if battle.trainer:\n        return "no-telemetry"')],
     {"UR1"}),
    ("F33 REVERT N1: the profiles path printed as given (relative)", "bl",
     [("        profiles = pathlib.Path(args.profiles or default_profiles()).absolute()",
       "        profiles = pathlib.Path(args.profiles or default_profiles())")], {"NT1"}),
    ("F34 win_rate with no WIN is n/a (a 0% hidden)", "bl",
     [("    return won / (won + lost) if won + lost else None", "    return won / (won + lost) if won else None")],
     {"OC1"}),
    ("M06b KEY from the WRONG list AND the import check removed (M06's first-pass set, + KG1/KG7)", "bl",
     [("KEY_CLASSES = _trainer_identity.KEY_TRAINER_CLASSES",
       "KEY_CLASSES = frozenset(_trainer_identity.TRAINER_CLASS.values())"),
      ("\ncheck_key_groups(KEY_GROUPS, KEY_CLASSES)\n", "\n")],
     {"TR6", "TR9", "BA2", "BA5", "SB1", "SI3", "SB5", "KG1", "KG7"}),
]

_MUTANT_IDS = {label.split()[0] for label, _t, _e, _w in MUTANTS + FOLD_MUTANTS}
assert set(MUTANT_ADDITIONS) <= _MUTANT_IDS, sorted(set(MUTANT_ADDITIONS) - _MUTANT_IDS)
assert set(MUTANT_ADDITIONS3) <= _MUTANT_IDS, sorted(set(MUTANT_ADDITIONS3) - _MUTANT_IDS)


def _want(label: str, w, *additions):
    """The EXACT expected set: its own set UNION every fold's addition; a `RAISES …` string stays as it is."""
    if isinstance(w, str):
        return w
    mid = label.split()[0]
    out = set(w)
    for extra in additions:
        out |= extra.get(mid, set())
    return out


#: Every job: (label, target, edits, the EXACT expected set, or "RAISES <error text prefix>").
JOBS: list = ([(label, t, e, _want(label, w, MUTANT_ADDITIONS, MUTANT_ADDITIONS3)) for label, t, e, w in MUTANTS]
              + [(label, t, e, _want(label, w, MUTANT_ADDITIONS3)) for label, t, e, w in FOLD_MUTANTS]
              + [(label, t, e, set(w)) for label, t, e, w in HUNTER_MUTANTS]
              + [(label, t, e, set(w)) for label, t, e, w in FOLD3_MUTANTS])


def _apply(src: str, edits) -> str:
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise AssertionError(f"mutant anchor found {n} times: {old[:90]!r}")
        src = src.replace(old, new)
    return src


def _install(key: str, source: str, i: int) -> None:
    name = NAMES[key]
    mod = types.ModuleType(name)
    mod.__file__ = str(PATHS[key])
    mod.__source__ = source              # KG7 re-executes the module's OWN source (the mutant's, under a mutant)
    sys.modules[name] = mod
    exec(compile(source, f"<mutant {i}>", "exec"), mod.__dict__)
    if key == "bl":                      # the probes bound `bl` at import: point them at the mutant too
        sys.modules["probe_boss_healing"].bl = mod
        sys.modules["probe_item_index_space"].bl = mod


def run_mutant(i: int, target: str, edits) -> "tuple[set | None, str]":
    real = {k: sys.modules[v] for k, v in NAMES.items()}
    try:
        src = _apply(PATHS[target].read_text(encoding="utf-8"), edits)
        _install(target, src, i)
        return all_rows(False), ""
    except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
        return None, f"{type(error).__name__}: {error}"
    finally:
        for k, v in NAMES.items():
            sys.modules[v] = real[k]
        real["bh"].bl = real["bl"]
        real["ix"].bl = real["bl"]


def main() -> int:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="itemprobes-") as tmp:
        TMP.update(_build_tree(pathlib.Path(tmp)))
        print("PROVENANCE — the gate's own data")
        provenance()
        print("\nROWS — the real modules")
        baseline = all_rows(True)
        if baseline:
            print(f"\n⛔ BASELINE RED (no mutant): {sorted(baseline)} — a defect in the code under test. These rows are "
                  f"left out of every mutant comparison below until fixed.")
        print(f"\nMUTANTS — each must turn EXACTLY its named rows red ({len(JOBS)}: {len(MUTANTS)} first-pass, "
              f"{len(FOLD_MUTANTS)} from the builder's sweep, {len(HUNTER_MUTANTS)} from the independent hunter, "
              f"{len(FOLD3_MUTANTS)} for the fold-3 fixes; in-process)")
        covered: set = set()
        for i, (label, target, edits, want) in enumerate(JOBS):
            red, err = run_mutant(i, target, edits)
            if isinstance(want, str):          # "RAISES <prefix>": the mutant must be REFUSED at load, with that error
                ok = red is None and err.startswith(want[len("RAISES "):])
                check(label, ok, f"refused at load: {err[:110]}" if red is None else f"LOADED, red {sorted(red)}")
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
    print(f"ALL PASS ({len(ROW_NAMES)} rows, {len(JOBS)} mutants, {len(QUOTES) + len(QUOTES_IN)} quoted evidence lines) "
          f"in {wall:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
