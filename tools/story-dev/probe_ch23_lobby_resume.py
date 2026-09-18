# -*- coding: utf-8 -*-
"""CALL `do_victory_road_chapter()` from inside the League and see what it actually does.

`#24-ch23lobbyresume`. `06-DECISIONS-LOG.md` DERIVED the consequence — *"all self-skip, three times,
then raises ⇒ 4 derails ⇒ Manual, parked in a sealed Elite Four room"* — and the 2026-09-18 lobby
drive MEASURED its two inputs (all ten call sites False; `ch23_chapter_done()` False) but **never
called the function**. This calls it. Predictions were filed first:
`PROJECT KNOWLEDGE/ai-research-notes/2026-09-18-ch23-lobby-resume-PREDICTIONS.md`.

⭐ WHY THIS IS SAFE, AND THE REASON IS WORTH STATING.
With every guard False the chapter body **yields nothing**: the 3-attempt loop runs, every `if` is
False, `ch23_chapter_done()` stays False, and it raises. ⇒ ONE `next()` on the generator executes the
whole body and consumes **zero emulator frames**. The bot cannot move, so it cannot wander into the
un-fleeable gauntlet. `frames_consumed` is REPORTED, not assumed — if it is ever non-zero the safety
argument is void and this probe must be re-thought before it is run again.

⛔⛔ THE CONTROL IS THE DANGEROUS HALF, AND IT IS GUARDED RATHER THAN TRUSTED.
The control makes the SAME call from an OUTDOOR fixture to show the instrument can see a non-raise.
But out there `enter_victory_road` (leg 5) has a TRUE guard — so if `ch23_chapter_done()` were False,
the call would walk the bot into the cave. ⇒ the control **tests `ch23_chapter_done()` FIRST and
refuses to call the chapter unless it is already True**, in which case the function returns at
`victory_road.py:3361-3362` having run nothing. An unguarded version of this control must never be
written.

⛔⛔ THIS IS NOT A GATE, AND IT MUST NOT BE ADDED TO `run_gates.py` AS IT STANDS.
It currently records a DEFECT: the raise is the present behaviour, not the desired one. A gate
asserting today's output would ratchet the bug in place and fail the day someone fixes it — the
opposite of what a gate is for.
⇒ ‼ WHEN `#24-ch23lobbyresume` IS FIXED, INVERT IT AND *THEN* GATE IT: the lobby case must stop
raising while the CONTROL must still return cleanly. Both halves matter — a "fix" that makes every
call return cleanly, everywhere, would satisfy the first half and have broken the chapter.
"""
import pathlib as _pl
import sys

sys.path.insert(0, str(_pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement") / "sandbox-pokebot"))

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

from modules.map_data import MapRSE
from modules.map_path import calculate_path
from modules.player import get_player_avatar
from modules.story import victory_road as VR

SAVES = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\saves")

#: The lobby's entry/exit landing tile (`victory_road.py:396-397`). The CONTINUE target: if the bot
#: can path here from the stop tile it is not PHYSICALLY stranded, whatever the dispatch does.
LOBBY_EXIT_LANDING = (9, 11)

# (fixture, note, may_call_unguarded, CONTINUE target ON THAT MAP or None)
# \u26d4 THE CONTINUE TARGET IS PER-CASE, AND v1 OF THIS PROBE GOT IT WRONG: it asked for the LOBBY's
# (9,11) on HALL4 too \u2014 a tile that means nothing on that map \u2014 and printed "NO PATH", which reads as
# "the bot is physically stranded in HALL4" when it only means "I asked the wrong question".
# \u203c A control aimed at a different subject proves nothing (`CLAUDE.md`). None = not applicable here.
CASES = [
    ("post_league_lobby.ss1", "TREATMENT \u2014 THE LOBBY (LEAGUE_1F 3,4)", True, LOBBY_EXIT_LANDING),
    ("post_hall4_door.ss1", "VACUITY/SCOPE \u2014 HALL4, SEALED (is this LOBBY-only or LEAGUE-WIDE?)", True, None),
    ("post_league_shop.ss1", "CONTROL \u2014 OUTDOORS at EVER_GRANDE  [\u26d4 GUARDED: see module docstring]", False, None),
]

print("=" * 116)
print("DOES \u00a7Ch23 RAISE WHEN RE-ENTERED FROM INSIDE THE LEAGUE?  (the chapter is CALLED, not traced)")
print("=" * 116)

results = []
for name, note, expect_inside, cont_target in CASES:
    path = SAVES / name
    if not path.exists():
        print(f"\n  {name}: MISSING")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    av = get_player_avatar()
    try:
        mname = MapRSE(tuple(av.map_group_and_number)).name
    except ValueError:
        mname = str(tuple(av.map_group_and_number))
    before_tile = VR._here_tile()
    before_map = tuple(av.map_group_and_number)
    done_before = VR.ch23_chapter_done()

    print(f"\n  {name}  \u2014  {mname} {before_tile}")
    print(f"      {note}")
    print(f"      ch23_chapter_done() BEFORE = {done_before}")

    # ---- CONTINUE: is the bot PHYSICALLY free, whatever the dispatch does? ----------------------
    cont = None
    if cont_target is not None:
        try:
            pth = calculate_path((MapRSE(before_map), before_tile),
                                 (MapRSE(before_map), cont_target))
            cont = f"OK \u2014 {len(pth)} waypoints to {cont_target}"
        except Exception as e:  # noqa: BLE001 - a failed path IS the reading
            cont = f"NO PATH \u2014 {type(e).__name__}: {str(e)[:90]}"
        print(f"      CONTINUE (calculate_path -> {cont_target}): {cont}")
    else:
        print("      CONTINUE: n/a \u2014 no target is defined for this map, and borrowing another "
              "map's tile would answer the wrong question")

    # ---- ⛔ THE GUARDED CALL ----------------------------------------------------------------------
    if not expect_inside and not done_before:
        verdict = ("\u26d4 CONTROL ABANDONED \u2014 ch23_chapter_done() is False out here, so calling the "
                   "chapter would RUN leg 5 (enter_victory_road) and walk the bot into the cave. "
                   "REFUSING. A control is not worth a derail.")
        print(f"      {verdict}")
        results.append((name, done_before, "ABANDONED", cont, before_tile, before_tile, 0))
        continue

    f0 = context.emulator.get_frame_count()
    gen = VR.do_victory_road_chapter()
    outcome, detail = None, ""
    try:
        next(gen)
        outcome = "YIELDED"
        detail = ("\u26d4 THE GENERATOR YIELDED \u2014 a leg is doing WORK. The zero-frames safety argument "
                  "is VOID; stop and re-read the guards before running this again.")
    except StopIteration:
        outcome = "RETURNED"
        detail = "returned cleanly without running any leg (the early `if ch23_chapter_done(): return`)"
    except Exception as error:  # noqa: BLE001 - the raise IS the reading
        outcome = type(error).__name__
        detail = str(error)
    finally:
        gen.close()
    f1 = context.emulator.get_frame_count()

    after_tile = VR._here_tile()
    after_map = tuple(get_player_avatar().map_group_and_number)
    moved = (after_map != before_map) or (tuple(after_tile) != tuple(before_tile))

    print(f"      CALL -> {outcome}")
    for chunk in [detail[i:i + 100] for i in range(0, min(len(detail), 400), 100)]:
        print(f"          {chunk}")
    print(f"      frames consumed = {f1 - f0}   moved = {moved}   after = {after_map} {after_tile}")
    results.append((name, done_before, outcome, cont, before_tile, after_tile, f1 - f0))

print("\n" + "-" * 116)
lobby = next((r for r in results if "lobby" in r[0]), None)
hall4 = next((r for r in results if "hall4" in r[0]), None)
ctrl = next((r for r in results if "shop" in r[0]), None)

if lobby:
    raised = lobby[2] not in ("RETURNED", "YIELDED", "ABANDONED")
    print(f"  LOBBY:   ch23_chapter_done()={lobby[1]}  call -> {lobby[2]}  frames={lobby[6]}")
    print(f"           CONTINUE: {lobby[3]}")
    if raised and lobby[3] and lobby[3].startswith("OK"):
        print("  \u21d2 \u2b50\u2b50 PHYSICALLY FREE, LOGICALLY STUCK. The bot can path to the lobby's own exit")
        print("       landing, but the \u00a7Ch23 dispatch cannot make progress from there and burns its")
        print("       retry budget every pass. \u26d4 That is NOT the \u00a7Ch15/\u00a7Ch18/\u00a7Ch19 'stranded' shape \u2014")
        print("       do not describe it with the same word.")
if hall4:
    print(f"  HALL4:   ch23_chapter_done()={hall4[1]}  call -> {hall4[2]}  frames={hall4[6]}")
if lobby and hall4:
    same = lobby[2] == hall4[2]
    print("  \u21d2 SCOPE: " + ("\u26d4 LEAGUE-WIDE \u2014 the sealed map behaves identically, so naming this a "
                              "LOBBY defect is too narrow. RE-SCOPE the item."
                              if same else
                              "\u2b50 the lobby and the sealed map DIFFER \u2014 the lobby framing holds."))
if ctrl:
    print(f"  CONTROL: ch23_chapter_done()={ctrl[1]}  call -> {ctrl[2]}")
    if ctrl[2] == "ABANDONED":
        print("  \u26a0 THE CONTROL DID NOT RUN, SO THE INSTRUMENT IS UNCONTROLLED. A raise seen above is")
        print("    NOT yet shown to be position-specific \u2014 say so, and do not claim a clean A/B.")
    elif ctrl[2] == "RETURNED":
        print("  \u2705 CONTROL SEPARATES: the same call returns cleanly where the chapter IS done.")
    else:
        print("  \u26d4 CONTROL DID NOT SEPARATE \u2014 the instrument raises everywhere and proves nothing.")
print("=" * 116)
