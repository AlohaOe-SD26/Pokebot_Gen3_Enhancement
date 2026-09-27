# -*- coding: utf-8 -*-
"""READ which §Ch23 legs would fire at each position we hold a pinned fixture for.

The §Ch24 marker design rests on a claim that has only ever been TRACED, never read:
*"inside the sealed League, every one of §Ch23's legs self-skips."*
⚠ “SELF-SKIPS” IS THE WRONG WORD AND THE DRIVE PROVED IT — see the header note in
`2026-09-18-ch24-lobby-fixture-SPEC.md`: with no leg firing and `ch23_chapter_done()`
False, `do_victory_road_chapter` RAISES after 3 attempts (`victory_road.py:3486-3488`). We hold a SEALED-map
fixture (`post_hall4_door.ss1`, HALL4), so that claim is measurable today.

⛔ THIS EVALUATES GUARDS ONLY. It never runs a leg. Every guard below is a pure position/party read
(`_on_map`, `at_*`, `party_is_healthy`), transcribed from `do_victory_road_chapter`
(`victory_road.py:3327-3488`) — the guard expressions are quoted beside each leg so a reader can check
the transcription rather than trust it. ⭐ A reader DID, and found two defects — see below.

⛔⛔ **CORRECTED 2026-09-18 — v1 ENUMERATED NINE OF THE TEN GUARDED CALL SITES AND PUBLISHED
"ALL NINE FALSE" AS THOUGH IT COVERED THE DISPATCH.** An adversarial reviewer read the dispatch
against this list and found two real transcription defects:
  1. ⭐ **THE TRAINING LEG WAS MISSING ENTIRELY.** `victory_road.py:3430-3431` is a guarded
     `yield from train_for_victory_road(report)` sitting BETWEEN leg 4 and leg 5. It carries no
     `LEG N` banner — only `--- THE TRAINING LEG ---` — so an enumeration built by reading the
     numbered banners walks straight past it. It is now `4b-train` below.
  2. **LEG 11's GUARD IS NESTED AND v1 READ ONLY THE OUTER HALF.** The real shape is
     `if _on_map(EG): stock = bag_healing_stock(); if any(stock < qty): yield from ...`
     (`:3462-3467`). v1 transcribed `_on_map(EG)` alone, and I then published the conclusion
     *"leg 11 fires even after the basket is bought — its self-skip must live inside the leg body"*.
     ⛔ **THAT CONCLUSION WAS FALSE.** The self-skip IS the inner `if`, at the call site, one line
     below the outer one — not in the leg body at all.
‼ THE RULE, already in `CLAUDE.md`: **instrument the ACTION, not the input to the action.** An outer
`if` that merely CONTAINS the call is an input. Transcribe the condition under which the `yield from`
actually EXECUTES — for a nested call site that is the CONJUNCTION of both tests.
‼ AND: **a checklist protects exactly what it enumerates.** Nine rows reading False cannot speak for
a tenth row that was never written down.

⭐ CONTROLS ARE THE POINT. `post_ch24_atdoor` (outdoors at EVER_GRANDE) MUST fire some legs — if every
position comes back "all skip", the instrument is simply returning False and the sealed-map row means
nothing.
⚠ `inside_vr` is a CACHED local in the real dispatch (computed at :3378, before leg 4). It is
recomputed fresh here; for a single evaluation at a fixed position that is equivalent.
"""
import pathlib as _pl
import sys

sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.player import get_player_avatar
from modules.map_data import MapRSE
from modules.story import victory_road as VR

SAVES = (_pl.Path(__file__).resolve().parent / "saves")

#: (leg, the guard exactly as written in the dispatch, a callable evaluating it)
GUARDS = [
    ("1-3", "any(_on_map(m) for m in _PRE_DEPARTURE_MAPS)",
     lambda: any(VR._on_map(m) for m in VR._PRE_DEPARTURE_MAPS)),
    ("4", "not inside_vr and not at_ever_grande_top()",
     lambda: (not any(VR._on_map(m) for m in VR.VICTORY_ROAD_MAPS)) and not VR.at_ever_grande_top()),
    # ⭐ THE TENTH CALL SITE, MISSING FROM v1. `victory_road.py:3430-3431`.
    # ⛔ It is NOT numbered in the dispatch — its banner reads `--- THE TRAINING LEG ---`, which is
    # exactly why an enumeration of "legs 1-11" missed it.
    ("4b-train", "not inside_vr and not wally_beaten() and not team_is_ready(TRAIN_TARGET)[0]",
     lambda: (not any(VR._on_map(m) for m in VR.VICTORY_ROAD_MAPS)) and not VR.wally_beaten()
             and not VR.team_is_ready(VR.TRAIN_TARGET)[0]),
    # ⭐ 2026-09-26: the dispatch now calls ONE named predicate — read it, never a hand copy (the old guard re-fired from
    # the League plateau on a re-entry; `probe_ch23_leg5_reentry.py` gates the fix).
    ("5", "leg5_should_fire()  [= old guard and not (wally_beaten() and on_league_plateau())]",
     lambda: VR.leg5_should_fire()),
    ("6", "_on_map(VR1F) and at_b1f_doorstep()",
     lambda: VR._on_map(VR.VR1F) and VR.at_b1f_doorstep()),
    ("7", "_on_map(B2F)", lambda: VR._on_map(VR.B2F)),
    ("8", "_on_map(B1F)", lambda: VR._on_map(VR.B1F)),
    # ⚠ Legs 9 and 10 each carry an extra `not <fault flag>` conjunct read from the environment
    # (`POKEBOT_CH23_FAULT_STRANDED` / `POKEBOT_CH23_FAULT_NOLEAGUEHEAL`, `victory_road.py:3364-3365`).
    # Both are False in any ordinary run, so dropping them is equivalent HERE — but it is dropped
    # DELIBERATELY and is now annotated on BOTH rows. v1 annotated only leg 9.
    ("9", "_on_map(VR1F) and not fault_stranded   [arm off => conjunct dropped]",
     lambda: VR._on_map(VR.VR1F)),
    ("10", "_on_map(EG) and not fault_noheal and not party_is_healthy()[0]   [arm off => dropped]",
     lambda: VR._on_map(VR.EG) and not VR.party_is_healthy()[0]),
    # ⛔ NESTED CALL SITE — the `yield from` runs only if BOTH tests pass (`:3462-3467`).
    ("11", "_on_map(EG) AND any(bag_healing_stock()[n] < qty for n, qty in LEAGUE_BASKET)",
     lambda: VR._on_map(VR.EG) and any(
         VR.bag_healing_stock().get(n, 0) < q for n, q in VR.LEAGUE_BASKET)),
]

CASES = [
    ("post_hall4_door.ss1", "SEALED map (HALL4) \u2014 the claim under test"),
    ("post_ch24_atdoor.ss1", "OUTDOORS at EVER_GRANDE  [CONTROL: must fire something]"),
    ("post_league_shop.ss1", "OUTDOORS, basket bought   [CONTROL]"),
    # ⭐ MINTED 2026-09-18 by `--driver ch24lobby` — the first fixture this repo has ever held
    # inside the League, and the position the §Ch24 marker actually has to cover.
    ("post_league_lobby.ss1", "THE LOBBY (LEAGUE_1F 3,4) — the marker's real subject"),
    # ⭐ MINTED 2026-09-18 by `--driver ch24lobby2f`. The lobby window is TWO maps and this is the
    # second one. Loading it here also RE-VERIFIES the fixture by reload, which is the only
    # verification this project accepts for a capture.
    ("post_league_2f.ss1", "LEAGUE 2F (1,6) — the Cable Club floor, the window's other half"),
]

print("=" * 116)
print("WHICH \u00a7Ch23 LEGS WOULD FIRE?  (guards evaluated, legs NEVER run)")
print("=" * 116)
summary = []
for name, note in CASES:
    p = SAVES / name
    if not p.exists():
        print(f"  {name}: MISSING")
        continue
    context.emulator.load_save_state(p.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    av = get_player_avatar()
    try:
        mname = MapRSE(tuple(av.map_group_and_number)).name
    except ValueError:
        mname = str(tuple(av.map_group_and_number))
    print(f"\n  {name}  \u2014  {mname} {tuple(av.local_coordinates)}")
    print(f"      {note}")
    fired = []
    for leg, expr, fn in GUARDS:
        try:
            v = fn()
        except Exception as e:
            v = f"ERR:{type(e).__name__}"
        mark = "\u26a0 FIRES" if v is True else ("skip  " if v is False else str(v))
        if v is True:
            fired.append(leg)
        print(f"        leg {leg:<5} {mark:<9} {expr}")
    print(f"      \u21d2 legs that would FIRE: {fired or 'NONE'}")
    summary.append((name, mname, fired))

print("\n" + "-" * 116)
sealed = next((s for s in summary if "HALL4" in s[1]), None)
ctrls = [s for s in summary if "HALL4" not in s[1]]
if sealed and ctrls:
    ctrl_ok = any(c[2] for c in ctrls)
    print(f"  CONTROL: at least one outdoor position fires a leg -> {'PASS' if ctrl_ok else 'FAIL'}")
    if not ctrl_ok:
        print("  \u26d4 INCONCLUSIVE: no position fires anything, so the sealed-map row means nothing.")
    else:
        print(f"  SEALED MAP (HALL4): legs firing = {sealed[2] or 'NONE'}")
        print("  \u21d2 " + ("\u2b50 CONFIRMED: NOT ONE of the ten \u00a7Ch23 call sites is reached inside the "
                         "sealed zone \u2014 READ, not traced."
                         if not sealed[2] else
                         f"\u26d4 REFUTED: leg(s) {sealed[2]} WOULD FIRE from inside the sealed zone."))
    lobby = next((s for s in summary if "LEAGUE_1F" in s[1]), None)
    if lobby:
        print(f"  THE LOBBY (LEAGUE_1F):  legs firing = {lobby[2] or 'NONE'}")
    # \u26d4\u26d4 AND DO NOT LET THE READER LEAVE WITH THE WORD "SELF-SKIP". It is the wrong word and this
    # project measured why on 2026-09-18: `do_victory_road_chapter`'s ONLY quiet exit is
    # `if ch23_chapter_done(): return` (`victory_road.py:3361-3362`), and in the League that
    # predicate is False because it requires `_on_map(EG)` \u2014 the OUTDOOR map.
    print("  \u203c BUT \u2018EVERY LEG SKIPS\u2019 IS NOT \u2018NOTHING HAPPENS\u2019. With no call site reached and")
    print("    `ch23_chapter_done()` False (it needs the OUTDOOR map), the dispatch exhausts its 3")
    print("    attempts and RAISES BotModeError (`victory_road.py:3486-3488`). Inside the League,")
    print("    \u00a7Ch23 can neither complete nor be skipped \u2014 which is what the \u00a7Ch24 marker is FOR.")
print("=" * 116)
