"""What ERA is each save state in `tools/story-dev/saves/` actually from?

‼ WHY THIS EXISTS. `#24-r116sweep` has now burned TWO runs on anchors chosen by NAME:
`mauville_wedge.ss1` (right era, but parked INSIDE the gym at (10,0), so leg 1 could never
leave) and `wally_done.ss1` (a **lone Mudkip L14** — the PETALBURG tutorial Wally, not the
Mauville one, i.e. the wrong era entirely). `probe_counter_reachability.py`'s docstring had
already warned *"anchors are verified on load, never trusted by name"*, and the warning was
still not enough, because there was nowhere to LOOK UP what a save contains. This is that
lookup table: load every save once, read the era out of memory, print it.

It answers, per save: where you are standing, whether the overworld is actually controllable,
which badges are held, and what the party is. That is exactly the tuple that invalidated both
bad anchors, so a third bad pick should now cost seconds instead of a run.

‼ POSITIVE CONTROL (this project's standing rule — prove the instrument can see something
you already know before trusting what it reports). Two independent controls run first:
  * an EARLY save (`oldale.ss1` / `route103.ss1`) must read **0 badges**, and
  * a LATE save (`post_winona.ss1`) must read **>= 5 badges**.
If both sides do not separate, the badge reader is broken and EVERY row below is noise, so
the probe says so loudly rather than printing a confident table of zeros. A reader that
returns a constant looks identical to a game with no badges — that is the failure this
catches.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_anchor_inventory.py
      PYTHONUTF8=1 py -3.12 probe_anchor_inventory.py --filter mauville   # substring match
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE
from modules.memory import GameState, get_event_flag, get_game_state
from modules.player import get_player, get_player_avatar, player_avatar_is_controllable
from modules.pokemon_party import get_party

SAVES = REPO / "tools" / "story-dev" / "saves"

BADGES = [f"BADGE0{n}_GET" for n in range(1, 9)]


def read_anchor(save: pathlib.Path) -> dict:
    """Load `save` and read its era out of live memory. Never raises; reports instead."""
    row = {"save": save.name}
    try:
        context.emulator.load_save_state(save.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
    except Exception as error:
        row["error"] = f"could not load: {type(error).__name__}: {error}"
        return row

    try:
        state = get_game_state()
        row["state"] = state.name
        row["controllable"] = player_avatar_is_controllable() if state is GameState.OVERWORLD else False
    except Exception as error:
        row["error"] = f"could not read game state: {type(error).__name__}: {error}"
        return row

    try:
        avatar = get_player_avatar()
        row["map"] = tuple(avatar.map_group_and_number)
        row["tile"] = tuple(avatar.local_coordinates)
    except Exception as error:
        row["map"] = row["tile"] = None
        row["note"] = f"no avatar ({type(error).__name__})"

    # ‼ RESOLVE THE MAP ENUM FROM THE (group, number) TUPLE — do NOT report `map_name`.
    # `map_name` is the human LABEL and interiors carry their city's label: MAUVILLE_CITY_GYM
    # (10, 0) reads as "MAUVILLE CITY", which is precisely how `mauville_wedge.ss1` was first
    # written down as a city anchor when it is parked in the gym. The enum name cannot lie.
    try:
        row["map_enum"] = MapRSE(row["map"]).name
    except Exception:
        row["map_enum"] = f"UNKNOWN{row.get('map')}"
    try:
        row["map_name"] = getattr(get_map_data_for_current_position(), "map_name", "?")
    except Exception:
        row["map_name"] = "?"

    badges = []
    for index, flag in enumerate(BADGES, start=1):
        try:
            if get_event_flag(flag):
                badges.append(index)
        except Exception:
            pass
    row["badges"] = badges

    # ‼ HP IS PART OF WHAT AN ANCHOR *IS*, not a detail. `post_maxie.ss1` served as the §Ch16
    # build anchor for a whole day before anyone read its HP: it sits at **47/534 = 8.8%, with
    # FIVE OF SIX MEMBERS FAINTED**, because Ch15 ends four floors underground straight after
    # Maxie and nothing heals in between. Every Ch16 run then lost a fight and whited out on the
    # haul — and the chapter still reported PASS, because a whiteout HEALS. A table that shows
    # species and level only cannot tell "a mid-game party" from "a corpse", which is exactly the
    # class of bad-anchor mistake this probe exists to prevent.
    try:
        party = [mon for mon in get_party() if mon is not None]
        row["party"] = [(mon.species.name, mon.level) for mon in party]
        row["hp_cur"] = sum(mon.current_hp for mon in party)
        row["hp_max"] = sum(mon.total_hp for mon in party)
        row["fainted"] = sum(1 for mon in party if mon.current_hp == 0)
        # ⭐ NAME THE CASUALTIES, ADDED 2026-09-03 — A COUNT WAS NOT ENOUGH, AND IT COST A DAY.
        # This probe reported "1 FAINTED" for `post_waterfall.ss1` while `saves/FIXTURES.md5`
        # separately recorded that Wailmer is §Ch23's SINGLE POINT OF FAILURE — sole carrier of
        # Dive (the only exit from the Sootopolis crater) and Waterfall (the only way up). Both
        # statements were true and they AGREED, so no consistency check could see the problem:
        # the fainted one WAS Wailmer. ⇒ the hazard lived in a conjunction no sentence performed,
        # and no instrument in the tree could answer "WHICH member is down?".
        # ⛔ ASSERT IDENTITY, NEVER A COUNT — the rule this file now implements instead of citing.
        row["fainted_who"] = [f"{mon.species.name}#{mon.personality_value:08X}"
                              for mon in party if mon.current_hp == 0]
        row["weakest"] = min(
            ((mon.species.name, mon.current_hp, mon.total_hp) for mon in party if mon.total_hp),
            key=lambda t: t[1] / t[2], default=None)
    except Exception as error:
        row["party"] = []
        row["hp_cur"] = row["hp_max"] = row["fainted"] = None
        row["note"] = f"{row.get('note', '')} no party ({type(error).__name__})".strip()

    try:
        row["money"] = get_player().money
    except Exception:
        row["money"] = None

    return row


def fmt(row: dict) -> str:
    if "error" in row:
        return f"  {row['save']:<34} ‼ {row['error']}"
    badges = "".join(str(n) for n in row["badges"]) or "-"
    party = ", ".join(f"{name} L{level}" for name, level in row["party"]) or "EMPTY"
    where = f"{row.get('map_enum', '?')} {row.get('tile')}"
    flags = "" if row.get("controllable") else "  ‼ NOT a clean controllable overworld"
    cur, mx, fainted = row.get("hp_cur"), row.get("hp_max"), row.get("fainted")
    if cur is not None and mx:
        pct = 100 * cur / mx
        who = row.get("fainted_who") or []
        # ⛔ NAME THEM. "1 FAINTED" is the reading that hid Wailmer — §Ch23's sole Dive+Waterfall
        # carrier — being the casualty in that chapter's own start fixture.
        health = f"  HP {cur}/{mx} ({pct:.0f}%)" + (
            f", {fainted} FAINTED: {', '.join(who)}" if fainted else "")
        weakest = row.get("weakest")
        if not fainted and weakest and weakest[2] and weakest[1] / weakest[2] < 0.25:
            health += f"   ⚠ weakest {weakest[0]} {weakest[1]}/{weakest[2]}"
        # Say it where the anchor is CHOSEN, not three runs later in a whiteout log.
        if fainted or pct < 50:
            health += "   ‼ CANNOT SURVIVE A JOURNEY — heal before using this as a start point"
    else:
        health = "  HP unreadable"
    return (f"  {row['save']:<34} badges={badges:<9} {row['state']:<10} {where:<34}\n"
            f"  {'':<34} party: {party}{flags}\n"
            f"  {'':<34}{health}")


def main() -> int:
    argv = sys.argv[1:]
    needle = ""
    if "--filter" in argv:
        needle = argv[argv.index("--filter") + 1].lower()

    # ---- POSITIVE CONTROL: prove the badge reader separates two known eras ----
    print("=" * 88)
    print("POSITIVE CONTROL — the badge reader must separate a known-early from a known-late save")
    print("=" * 88)
    early = next((SAVES / n for n in ("oldale.ss1", "route103.ss1") if (SAVES / n).is_file()), None)
    late = next((SAVES / n for n in ("post_winona.ss1", "post_mtpyre.ss1") if (SAVES / n).is_file()), None)
    if early is None or late is None:
        print("  ‼ CONTROL IMPOSSIBLE — no early and/or late control save present. Results below are UNTRUSTED.")
        control_ok = False
    else:
        early_row, late_row = read_anchor(early), read_anchor(late)
        early_n, late_n = len(early_row.get("badges", [])), len(late_row.get("badges", []))
        print(f"  early  {early.name:<24} badges={early_n}  (expect 0)")
        print(f"  late   {late.name:<24} badges={late_n}  (expect >= 5)")
        control_ok = early_n == 0 and late_n >= 5
        print(f"  CONTROL {'PASS — the reader sees badges and their absence' if control_ok else 'FAIL ‼ every row below is NOISE'}")
    print()

    saves = sorted(p for p in SAVES.glob("*.ss1") if needle in p.name.lower())
    print("=" * 88)
    print(f"ANCHOR INVENTORY — {len(saves)} save(s) in {SAVES}")
    print("=" * 88)
    rows = []
    for save in saves:
        row = read_anchor(save)
        rows.append(row)
        print(fmt(row))

    # ---- the question that motivated this probe ----
    print()
    print("=" * 88)
    print("#24-r116sweep NEEDS: standing in MAUVILLE_CITY, badge03 NOT held, a mid-game party")
    print("=" * 88)
    hits = [r for r in rows
            if "error" not in r
            and r.get("map_enum") == "MAUVILLE_CITY"       # the CITY itself, not the gym
            and 3 not in r.get("badges", [])]
    if not hits:
        print("  NONE. A Mauville / pre-Dynamo anchor must be CAPTURED before the sweep can run.")
    for row in hits:
        party = row.get("party", [])
        top = max((level for _, level in party), default=0)
        verdict = "USABLE" if row.get("controllable") and len(party) >= 2 and top >= 15 else "NOT usable"
        print(f"  {row['save']:<34} {verdict}: controllable={row.get('controllable')} "
              f"party={len(party)} top=L{top} tile={row.get('tile')}")
    if not control_ok:
        print("\n‼ CONTROL FAILED — do not act on anything above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
