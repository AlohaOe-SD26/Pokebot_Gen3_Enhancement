# -*- coding: utf-8 -*-
"""`#24-fixturelineage` — WHICH save should the L75 grind actually run from, and can it get back?

⛔⛔ WHY THIS EXISTS, AND WHY IT PRINTS MOVESETS. The §Ch24 grind ran for ~2.4 HOURS on
`post_grind_L60.ss1` before anyone checked that its Wailord has **no Ice Beam** and its Swellow has
**no Fly** — the two moves the whole chapter is prepared around. `FIXTURES.md5` claimed that save was
*"verified by reloading the file"*, and it was — with `probe_anchor_inventory.py`, **which does not
print movesets.** ⇒ a fixture can be verified and still be the wrong one. This probe answers the
fixture question and the ROUTE question in the same breath, offline, in seconds.

⭐⭐ THE LINEAGE, MEASURED (this is the finding `#24-fixturelineage` was groping at):

    post_training.ss1  (§Ch23, L47-51 — NO Ice Beam, NO Fly, pre-prep)
      |
      +-- post_wally -> ... -> post_league_shop -> post_moveset -> post_fly -> post_slateport
      |     -> post_icebeam -> post_teachice -> post_ch24ready -> post_ch24_atdoor   <- §Ch24 LINEAGE
      |
      +-- post_grind_L60.ss1   <- ⛔ BRANCHED STRAIGHT OFF post_training, SKIPPING THE WHOLE PREP CHAIN

⇒ `post_grind_L60.ss1` is not a §Ch24 save that lost its moves. It is a **§Ch23 save that never had
them**, grown to L60 on a dead branch. ⛔ So "repair it" means re-running the ENTIRE prep chain on it,
including the ~700,000-frame Abandoned Ship trip for TM13 — to arrive at a party the OTHER branch
already has. **The levels are the only thing it owns, and levels cannot be transplanted.**

⭐ AND THE RETURN TRIP IS ALREADY SOLVED ON THE OTHER BRANCH, WHICH IS WHAT MAKES THIS CHEAP.
`post_ch24_atdoor.ss1` was captured from `post_ch24ready.ss1` by **ONE Fly** — `src/region_map.c`
`CB_ExitFlyMap` special-cases Ever Grande, so with `FLAG_LANDMARK_POKEMON_LEAGUE` set, flying to
`PokemonLeague` lands on the **League door apron (18,6)**, not the Poké Center. ⇒ a party parked at
the Poké Center side can always get back to the League door in one move.

‼‼ THE ONE THING THAT IS *NOT* YET MEASURED, AND THE REASON THIS FILE EXISTS RATHER THAN A PLAN:
    can the §Ch24-prepped party, standing at the Poké Center **(27,49)**, WALK TO VICTORY ROAD'S
    DOOR APRON **(18,42)** — the way in to the proven grind tile VICTORY_ROAD_1F (15,39)?
`Ch24GrindMode`'s own docstring says *"The League fixtures cannot be used: from the League door
`calculate_path` reaches neither grass nor a Poké Center"* — ⛔ that is a true statement about
**(18,6)**, the OTHER side of the plateau, and it says nothing about (27,49). Do not read it as
covering this question; that is how a ruled-out claim gets over-applied.

‼ HOW TO READ A RESULT — THE THREE OUTCOMES ARE NOT INTERCHANGEABLE (lifted from
`probe_heal_reachability.py`, which learned it the hard way):
  * `OK, N waypoints`        => genuinely walkable. STRONG evidence, safe to act on.
  * `NEEDS A WARP`           => `calculate_path` plans only across DIRECTLY CONNECTED maps. Says
                                NOTHING about reachability — wrong tool, not a map fact.
  * `FAIL on connected maps` => real, but still not proof of unreachable (KI-24: the tile planner
                                reads dual-elevation bridges as WALLS).

⛔ THE CONTROL IS TWO-SIDED ON PURPOSE. A probe that only shows FAILs cannot distinguish "the map
says no" from "the instrument is broken", and a probe that only shows OKs cannot distinguish a real
route from a planner that says yes to anything. So it asserts BOTH:
  * POSITIVE — the Poké Center door must come back OK from the tile we are standing on;
  * NEGATIVE — the League door (18,5) must come back NOT-OK, reproducing the reading already in
    `FIXTURES.md5`: *"PathFindingError ... (27/49) to (18/5)"*.
If those two do not separate, every row below is noise and the probe says so instead of printing a
confident table.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_grind_lineage_route.py
Exit 0 if both controls hold (whatever the verdict); 1 if either fails, because then nothing here
can be trusted.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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
# ⛔ UNTHROTTLED, OR THE SUITE PAYS FOR IT AT 1x REAL TIME — enforced by
# `probe_gate_unthrottled.py`, which caught this file missing the line.
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player_avatar, player_avatar_is_controllable
from modules.pokemon_party import get_party

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 100

#: The two candidate grind starts. ⛔ Names are NOT trusted — the party is re-read from each file.
CANDIDATES = ("post_ch24ready.ss1", "post_grind_L60.ss1")

#: The moves the whole chapter is prepared around. Checked BY NAME against what is actually in the
#: party, because "the fixture is verified" has already meant "verified by a probe that could not
#: see this" once.
REQUIRED = ("Ice Beam", "Fly")

#: Targets measured from wherever the save actually parks us. ⛔ The tile we stand on is READ, never
#: assumed — a fixture that moved would otherwise silently re-point every query below.
TARGETS = (
    ("VR door apron   (18,42)", MapRSE.EVER_GRANDE_CITY, (18, 42), "THE LOAD-BEARING ONE — the way in to the grind tile"),
    ("VR exit landing (18,28)", MapRSE.EVER_GRANDE_CITY, (18, 28), "the Victory Road EXIT side, for orientation"),
    ("Poke Center door(27,48)", MapRSE.EVER_GRANDE_CITY, (27, 48), "POSITIVE CONTROL — must be OK"),
    ("League door     (18,5) ", MapRSE.EVER_GRANDE_CITY, (18, 5), "NEGATIVE CONTROL — must NOT be OK (FIXTURES.md5, 2026-09-06)"),
)


def path_result(src, dst):
    """Classify one `calculate_path` attempt into the THREE outcomes, never two."""
    try:
        path = calculate_path(src, dst, avoid_encounters=False, avoid_scripted_events=False)
        return "OK", f"OK, {len(path)} waypoints"
    except PathFindingError as error:
        text = str(error)
        if "not on connected maps" in text:
            return "WARP", "NEEDS A WARP — calculate_path cannot cross warps (wrong tool, not a map fact)"
        return "FAIL", f"FAIL on connected maps (real, but see KI-24) — {text[:90]}"
    except Exception as error:  # noqa: BLE001 — a probe must report, never crash the report
        return "ERROR", f"ERROR — {type(error).__name__}: {error}"


def load(name: str):
    """Load a save and settle it. Returns (avatar, map_group_and_number, local_tile) or None."""
    save = SAVES / name
    if not save.is_file():
        print(f"  ⛔ no such save: {name}")
        return None
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    avatar = get_player_avatar()
    return avatar


def describe_party(name: str) -> "tuple[list, set]":
    """Print every battler's level AND MOVES, and return the flat set of move names."""
    rows, known = [], set()
    for i, mon in enumerate(get_party()):
        if mon is None or getattr(mon, "species", None) is None:
            continue
        moves = [m.move.name for m in mon.moves if m is not None and m.move is not None]
        known.update(moves)
        rows.append((i, mon.species.name, mon.level, moves))
    for i, species, level, moves in rows:
        print(f"      {i}  {species:<11} L{level:<3} {', '.join(moves)}")
    return rows, known


def main() -> int:
    print(BAR)
    print("  #24-fixturelineage — which fixture should the L75 grind run from?")
    print(BAR)

    verdicts = {}
    for name in CANDIDATES:
        print(f"\n{'-' * 100}\n  {name}\n{'-' * 100}")
        avatar = load(name)
        if avatar is None:
            continue
        here = avatar.map_group_and_number
        tile = avatar.local_coordinates
        try:
            map_name = MapRSE(here).name
        except Exception:  # noqa: BLE001 — an unknown map id is a reading, not a crash
            map_name = str(here)
        print(f"    standing at: {map_name} {tile}   controllable={player_avatar_is_controllable()}")

        print("    party (⛔ THE READING `probe_anchor_inventory.py` CANNOT GIVE YOU):")
        _, known = describe_party(name)
        missing = [m for m in REQUIRED if m not in known]
        if missing:
            print(f"    ⛔ MISSING the chapter's prepared moves: {missing}  ⇒ WRONG LINEAGE for §Ch24")
        else:
            print(f"    ✅ carries every prepared move {list(REQUIRED)} ⇒ §Ch24 lineage")
        verdicts[name] = {"missing": missing, "map": map_name, "tile": tile}

        # ---- routes, from the tile we are ACTUALLY on ------------------------------------------
        print("    routes from here:")
        results = {}
        for label, dst_map, dst_tile, why in TARGETS:
            kind, text = path_result((here, tile), (dst_map, dst_tile))
            results[label] = kind
            print(f"      {label}  {text}")
            print(f"          ({why})")
        verdicts[name]["routes"] = results

    # ---- THE TWO-SIDED CONTROL --------------------------------------------------------------
    print(f"\n{BAR}\n  CONTROLS — the instrument must be able to say BOTH yes and no\n{BAR}")
    ready = verdicts.get("post_ch24ready.ss1", {}).get("routes", {})
    pos_label = "Poke Center door(27,48)"
    neg_label = "League door     (18,5) "
    pos_ok = ready.get(pos_label) == "OK"
    neg_ok = ready.get(neg_label) not in (None, "OK")
    print(f"    POSITIVE  {pos_label} -> {ready.get(pos_label)}   {'PASS' if pos_ok else 'FAIL'}")
    print("      ‼ Must be OK. If the planner cannot route to a door one tile away, a FAIL")
    print("        anywhere above is about the INSTRUMENT, not the map.")
    print(f"    NEGATIVE  {neg_label} -> {ready.get(neg_label)}   {'PASS' if neg_ok else 'FAIL'}")
    print("      ‼ Must NOT be OK — it reproduces the reading already pinned in FIXTURES.md5.")
    print("        If this came back OK, the planner says yes to anything and every OK is worthless.")

    if not (pos_ok and neg_ok):
        print(f"\n  ⛔⛔ CONTROLS DID NOT SEPARATE — nothing above can be trusted.\n{BAR}")
        return 1

    print(f"\n{BAR}\n  VERDICT\n{BAR}")
    apron = ready.get("VR door apron   (18,42)")
    if apron == "OK":
        print("  ✅ The §Ch24-prepped party CAN walk from the Poké Center to Victory Road's door.")
        print("     ⇒ GRIND `post_ch24ready.ss1`, not `post_grind_L60.ss1`: it already carries Ice Beam,")
        print("       Fly and the four free move changes, so the ~700k-frame Abandoned Ship trip and the")
        print("       whole prep chain are ALREADY PAID. Returning to the League door is ONE Fly.")
    else:
        print(f"  ⚠ VR door apron came back {apron!r} — NOT a walkable route by this instrument.")
        print("     ⛔ Do NOT conclude 'unreachable' from this alone (see the three-outcome note in the")
        print("        docstring). The next instrument is a live navigator drive, not another planner call.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
