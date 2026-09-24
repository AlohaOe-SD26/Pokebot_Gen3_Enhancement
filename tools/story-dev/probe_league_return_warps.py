# -*- coding: utf-8 -*-
"""§Ch24 M1 (part 2) — ARE THE LEAGUE'S BACKWARD WARPS INERT? READ FROM ROM, WITHOUT WALKING IN.

⛔⛔ THE QUESTION, AND WHY IT IS WORTH A PROBE OF ITS OWN.
`modules/story/pokemon_league.py:5-8` asserts *"the moment the bot steps on lobby tile (9,1) it is
committed to all five battles or a white-out"*, because every backward warp in the League interior
*"sits on an `MB_NORMAL` tile"* and the warp code rejects those. **That inference decides where a
readiness check can still act** — a guard past the commitment point can only report a problem it can
no longer fix, and the lobby is the last place a free nurse and a Mart exist.

⭐⭐ **AND THE OBVIOUS EXPERIMENT IS THE WRONG ONE.** The instinct is to walk through the lobby door
on a fixture and try to walk back. That experiment is *worse* than this one in three ways:
  1. **A false "COMMITTED" is cheap to produce and expensive to believe.** "We are still in the hall"
     reads identically whether the warp is inert, the bot never actually moved, the button cadence
     was wrong, a script was mid-flight, or a wait bound expired.
  2. It writes an in-gauntlet state into `current_state.ss1`, **which the real bot resumes from**
     (`libmgba.py:144` loads it at startup, `:226` overwrites it at shutdown — and `is_test_run`
     guards only the load, not the write).
  3. It answers for ONE tile. This reads **every backward warp in the interior** at once.
⇒ read the tile behaviour straight out of the ROM for maps we are not standing on. `get_map_data()`
does exactly that — it is how `probe_e4_entry_seal.py`'s `rom_collision()` already works.

────────────────────────────────────────────────────────────────────────────────────────────────────
⛔ WHAT MAKES THIS TRUSTWORTHY RATHER THAN JUST CONVENIENT — THE CONTROLS
────────────────────────────────────────────────────────────────────────────────────────────────────
A static read is only as good as its instrument, and this tree's own rule is that **a layout-swapped
map lies to every static reader**. So this probe does not merely report the tiles it cares about; it
reports **tiles whose answer is already known live**, in the same run:

  * `POKEMON_LEAGUE_1F (9,1)/(10,1)` — measured LIVE on 2026-09-24 as `Non-Animated Door`, collision
    0, with ROM and LIVE agreeing (`evidence/2026-09-24-league-lobby-facts.stdout.txt`).
  * `POKEMON_LEAGUE_1F (8,1)/(11,1)` — measured LIVE as collision 1.
  ⇒ if those four do not reproduce here, **the instrument is wrong and every other row is void.**
  The probe says so in its own verdict rather than leaving the reader to notice.

‼ **A FORWARD warp is printed beside every backward one.** `HALL5 (5,2)` is the door onward to
Sidney's room. If the forward warp reads as a door and the backward ones read as `Normal`, the
asymmetry is the finding. If BOTH read `Normal`, the probe is measuring nothing and says so — that is
the vacuity check, and without it "everything is Normal" would look like a dramatic result.

⛔⛔⛔ **THE ERROR THIS PROBE SHIPPED ONCE, AND THE REASON ITS SCOPE IS NOW NARROW.**
The first version also read the ELITE FOUR ROOM tiles and folded them into a single *"6 of 6
backward warps are Normal — CONFIRMED BY DATA"* verdict. **Two of those rows were void**, because
`elite_four.inc`'s `WalkInCloseDoor` **rewrites room tiles at runtime** with `setmetatile(..., TRUE)`
and re-applies them from `ON_LOAD`. `probe_e4_entry_seal.py` had ALREADY measured the truth live:
`SIDNEYS_ROOM (6,13)` is **ROM=0 but LIVE=3**, and the room's exit `(6,2)` is **ROM=1 but LIVE=0**.
‼ Worse, the first version cited that stale `(6,2)` read as an *"unplanned corroboration"* that the
data agreed with the script — **presenting an artifact of the staleness as evidence against it.**
⇒ `KI-74` states the rule by name: *"ANY League-interior reachability check must read
`_live_collision_grid`, never `get_map_data`"*. That rule is about the **rooms**, whose tiles a
script rewrites. It is satisfied here by **not reading room tiles at all** and deferring them, by
name, to the live gate — while the HALLS and the LOBBY keep the ROM read, with a stated warrant:
their `scripts.inc` contain **no `setmetatile`**, only `turnobject`, so nothing rewrites them.

⛔ THIS PROBE NEVER MOVES THE PLAYER. It loads a fixture only to have a live emulator to read ROM
through, presses nothing, and steps nowhere. It cannot commit a run, and it cannot poison
`current_state.ss1` with an in-gauntlet position.
"""
from __future__ import annotations

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
# ⛔ UNTHROTTLED (`probe_gate_unthrottled.py`).
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.map import get_map_data
from modules.map_data import MapRSE

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURE = "post_league_lobby.ss1"
BAR = "=" * 104

#: ⛔⛔ TWO CLASSES OF MAP, AND CONFLATING THEM IS EXACTLY THE ERROR THIS PROBE SHIPPED ONCE.
#:   HALLS + LOBBY  — no script writes their tiles, so the ROM view IS the runtime view.
#:   E4 ROOMS       — `elite_four.inc`'s `WalkInCloseDoor` REWRITES their tiles with `setmetatile`
#:                    on entry, and re-applies from ON_LOAD. ⇒ a ROM read of a room tile is the
#:                    PRE-SEAL snapshot and says NOTHING about the runtime state.
#: A first version of this probe read room tiles and folded them into a "6 of 6" verdict. That was
#: wrong: `probe_e4_entry_seal.py` had ALREADY measured `SIDNEYS_ROOM (6,13)` live as ROM=0 / LIVE=3.
#: ⇒ ROOM TILES ARE NOT READ HERE AT ALL. They are deferred to the live gate, by name.
ROWS = [
    ("CONTROL  lobby fwd door  ", MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (9, 1), "fwd"),
    ("CONTROL  lobby fwd door  ", MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (10, 1), "fwd"),
    ("CONTROL  lobby wall      ", MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (8, 1), "wall"),
    ("CONTROL  lobby wall      ", MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (11, 1), "wall"),
    ("HALL5    back to lobby   ", MapRSE.EVER_GRANDE_CITY_HALL5, (4, 12), "back"),
    ("HALL5    back to lobby   ", MapRSE.EVER_GRANDE_CITY_HALL5, (5, 12), "back"),
    ("HALL5    back to lobby   ", MapRSE.EVER_GRANDE_CITY_HALL5, (6, 12), "back"),
    ("HALL5    fwd to Sidney   ", MapRSE.EVER_GRANDE_CITY_HALL5, (5, 2), "fwd"),
    ("HALL1    back            ", MapRSE.EVER_GRANDE_CITY_HALL1, (5, 12), "back"),
    ("HALL1    fwd             ", MapRSE.EVER_GRANDE_CITY_HALL1, (5, 2), "fwd"),
    ("HALL4    back            ", MapRSE.EVER_GRANDE_CITY_HALL4, (5, 33), "back"),
    ("HALL4    fwd             ", MapRSE.EVER_GRANDE_CITY_HALL4, (5, 2), "fwd"),
]

#: ⛔ DELIBERATELY NOT READ — and the reason is printed in the output, so the omission is visible
#: rather than silent. These belong to `probe_e4_entry_seal.py`, which reads them LIVE.
DEFERRED_TO_LIVE_GATE = [
    ("SIDNEYS_ROOM (5..7,12) and (5..7,13)",
     "rewritten on entry by `elite_four.inc` WalkInCloseDoor (setmetatile ..., TRUE) and re-applied "
     "from ON_LOAD. MEASURED LIVE by probe_e4_entry_seal.py: ROM=0 but LIVE=3 on all six."),
    ("SIDNEYS_ROOM (6,1) and (6,2)",
     "the forward exit, OPENED at runtime by SetAdvanceToNextRoomMetatiles. MEASURED LIVE by "
     "probe_e4_entry_seal.py: ROM=1 but LIVE=0. ‼ A ROM read here says 'blocked as shipped' and "
     "that is NOT evidence of anything about the running game."),
]

#: What the LIVE run of 2026-09-24 already established. A mismatch voids the instrument.
LIVE_KNOWN = {
    (MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (9, 1)): ("Non-Animated Door", 0),
    (MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (10, 1)): ("Non-Animated Door", 0),
    (MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (8, 1)): ("Normal", 1),
    (MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (11, 1)): ("Normal", 1),
}


def read(map_enum, tile):
    try:
        d = get_map_data(map_enum, tile)
        return str(d.tile_type), d.collision
    except Exception as error:  # noqa: BLE001 — a failed read is a RESULT: this probe reports what
        # the ROM says, including "it would not say". Crashing would discard the rows that did read.
        return f"ERR:{type(error).__name__}", "?"


def main() -> int:
    save = SAVES / FIXTURE
    if not save.is_file():
        print(f"  ABORT (instrument, not a result) — no fixture: {FIXTURE}")
        return 1
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    print(BAR)
    print("  §Ch24 M1 (part 2) — ARE THE LEAGUE'S BACKWARD WARPS INERT?  ⛔ NO STEP IS TAKEN.")
    print("  Read from ROM for maps we are NOT standing on, with live-known tiles as controls.")
    print(BAR)
    print(f"    {'what':<26} {'map':<38} {'tile':>9}  {'coll':>4}  tile_type")

    rows = []
    for label, m, tile, kind in ROWS:
        tt, coll = read(m, tile)
        rows.append((label, m, tile, kind, tt, coll))
        print(f"    {label:<26} {m.name:<38} {str(tile):>9}  {str(coll):>4}  {tt}")

    # ---- CONTROL CHECK: does the instrument reproduce what we already measured LIVE? ----------
    print()
    bad = []
    for (m, tile), (want_tt, want_coll) in LIVE_KNOWN.items():
        tt, coll = read(m, tile)
        ok = (tt == want_tt) and (coll == want_coll)
        print(f"    CONTROL {m.name} {tile}: expected {want_tt}/coll {want_coll}, "
              f"got {tt}/coll {coll}  -> {'OK' if ok else '** MISMATCH **'}")
        if not ok:
            bad.append((m.name, tile))
    if bad:
        print("\n  ⛔ THE INSTRUMENT FAILED ITS OWN CONTROLS — every row above is VOID. Do not read a")
        print("     verdict out of this run; the static reader disagrees with a live measurement we")
        print("     already hold (evidence/2026-09-24-league-lobby-facts.stdout.txt).")
        print(BAR)
        return 1
    print("  ✅ CONTROLS REPRODUCE the 2026-09-24 LIVE measurement — the static reader is trustworthy here.")

    # ---- THE VACUITY CHECK ---------------------------------------------------------------------
    back = [r for r in rows if r[3] == "back"]
    fwd = [r for r in rows if r[3] == "fwd"]
    back_normal = [r for r in back if r[4] == "Normal"]
    fwd_doors = [r for r in fwd if "Door" in r[4]]
    print()
    print(f"  backward warp tiles reading `Normal`      : {len(back_normal)} of {len(back)}")
    print(f"  forward  warp tiles reading as a DOOR      : {len(fwd_doors)} of {len(fwd)}")
    if not fwd_doors:
        print("\n  ⛔ VACUOUS — no forward warp reads as a door either, so 'the backward ones are")
        print("     Normal' distinguishes nothing. The probe is measuring the wrong thing.")
        print(BAR)
        return 1

    print()
    print()
    print("  ⛔ NOT READ HERE — DEFERRED TO THE LIVE GATE `probe_e4_entry_seal.py`:")
    for what, why in DEFERRED_TO_LIVE_GATE:
        print(f"     {what}")
        print(f"        {why}")

    print()
    if len(back_normal) == len(back):
        print("  ✅ VERDICT, SCOPED TO THE HALLS: every HALL backward warp tile reads `Normal`, while")
        print("     forward warps read as DOORS. `MB_NORMAL` is behaviour 0 and every behaviour the")
        print("     warp paths accept is NON-ZERO, so a warp event on such a tile can never fire.")
        print("     ⇒ THE HALL-TO-LOBBY RETURN WARPS ARE INERT. Warrant for trusting ROM here: the")
        print("     halls' `scripts.inc` contain no `setmetatile`, only `turnobject`.")
        print("     ‼ THIS IS NOT, BY ITSELF, 'THE INTERIOR IS ONE-WAY'. The ROOMS are sealed by a")
        print("     RUNTIME rewrite that this reader cannot see; that half is live-confirmed by")
        print("     `probe_e4_entry_seal.py`. The two together make the claim — neither alone does.")
    else:
        live = [r for r in back if r[4] != "Normal"]
        print("  ⛔ VERDICT: NOT every backward warp is inert — these are not `Normal`:")
        for r in live:
            print(f"       {r[1].name} {r[2]}  ->  {r[4]}")
        print("     ⇒ a RETREAT MAY EXIST, and `pokemon_league.py:5-8` overstates the seal.")

    print()
    print("  ⛔ WHAT THIS STILL DOES NOT SETTLE: this is the ROM's static view. It is trustworthy here")
    print("     because the controls reproduce a live measurement on the SAME tileset — but the seal")
    print("     INSIDE a room is applied at runtime by `setmetatile` (already live-confirmed by")
    print("     `probe_e4_entry_seal.py`), and a runtime write is invisible to this reader by")
    print("     construction. ⇒ these rows describe the tiles AS SHIPPED, not as a script may leave them.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
