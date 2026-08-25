"""probe_ch21_npcs.py — WHO is on the Sootopolis map, WHERE, and can the bot actually reach them?

‼ THIS ANSWERS §Ch21 LEG 2's BIGGEST UNKNOWN — where Steven stands — from OUR OWN ROM, not recall.

⛔⛔ THE METHOD ERROR THIS PROBE EXISTS TO PREVENT, WHICH I MADE FIRST.
A `calculate_path` to an NPC's OWN tile ALWAYS fails: the tile is occupied. My first pass pathed to
each NPC's coordinate, got "refuses" for all 18, and read that as geography — concluding the whole
north of the city was unreachable and that an earlier agent's "Steven is at (20,36)" was wrong. It
was not wrong. Re-measured to the FOUR ADJACENT tiles, **15 of 18 NPCs are approachable** and Steven
is 27 waypoints away.
⇒ **A BOT NEVER STANDS ON AN NPC; IT STANDS BESIDE ONE AND FACES IT.** Any reachability question
about an NPC must be asked of its NEIGHBOURS.

⛔ AND THE OTHER ERROR IT PREVENTS — the one Tier 1 caught. `get_map_objects()` reads only what the
game has LOADED, which is a CAMERA-RANGE window: from the arrival tile it returns exactly ONE object
(the player) even though eighteen are stationed on the map. An earlier note argued "ZERO NPCs loaded,
so the Expert body-block is not the cause" — an invalid inference, because the reader could not have
seen an NPC 30+ tiles away whether or not it was there.
⇒ **THIS PROBE READS `map_data.objects` — the ROM's OBJECT-EVENT TEMPLATES — which are range-free.**
⚠ Templates are the map's DEFAULT stations. Scripts reposition some NPCs by state
(`setobjectxyperm`), so a template coordinate is where an NPC starts, not necessarily where it is
now. Treat template positions as HIGH confidence and state-dependent positions as needing a live
check.

WHAT IT ASSERTS (each fails loudly, exit 1):
  1. Sootopolis has the expected cast, identified by GRAPHICS ID, not by guessing:
     STEVEN(134), WALLACE(133), EXPERT_M(21), MAXIE(196), ARCHIE(195).
  2. STEVEN is APPROACHABLE from the leg-1 arrival tile — leg 2 is possible at all.
  3. MAXIE and ARCHIE are both approachable — leg 5 (HM07 needs BOTH) is possible at all.
  4. ⛔ The Cave of Origin approach column is NOT walkable, which is why leg 2 must go through
     Steven's escort rather than walking to the door.

FAULT HOOK: `POKEBOT_CH21NPC_FAULT=wrongtile` looks for Steven at a tile he is not on, which MUST
make assertion 2 fail — proving these assertions can fail at all.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch21_npcs.py
"""

import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))

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

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "post_sootopolis_arrival.ss1"
if not ANCHOR.exists():
    print("  MISSING ANCHOR: %s" % ANCHOR)
    print("  Capture it with: CH21_CAPTURE=post_sootopolis_arrival.ss1 ... --driver ch21dive")
    sys.exit(2)
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import calculate_path
from modules.memory import get_event_var
from modules.player import get_player_avatar

# Resolved from the decomp's include/constants/event_objects.h, not guessed.
GFX = {21: "EXPERT_M", 133: "WALLACE", 134: "STEVEN", 195: "ARCHIE", 196: "MAXIE",
       207: "RAYQUAZA", 221: "KYOGRE_SIDE", 222: "GROUDON_SIDE", 19: "MAN_1"}
FAILURES = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
    if not ok:
        FAILURES.append(label)


avatar = get_player_avatar()
AT = tuple(avatar.local_coordinates)
print("SOOTOPOLIS NPCs — from the ROM's object-event TEMPLATES (range-free), not get_map_objects()")
print("=" * 98)
print("  anchor : post_sootopolis_arrival.ss1")
print("  player : SOOTOPOLIS_CITY %s   SOOTOPOLIS_CITY_STATE=%s   flags=%s"
      % (AT, get_event_var("SOOTOPOLIS_CITY_STATE"), [f.name for f in avatar.flags]))


def waypoints(coords):
    try:
        return len(calculate_path((MapRSE.SOOTOPOLIS_CITY, AT), (MapRSE.SOOTOPOLIS_CITY, coords)))
    except Exception:
        return None


def approach(coords):
    """The tiles BESIDE an NPC that the bot can actually stand on. Never the NPC's own tile."""
    x, y = coords
    out = []
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        n = waypoints((x + dx, y + dy))
        if n:
            out.append(((x + dx, y + dy), n))
    return sorted(out, key=lambda t: t[1])


md = get_map_data(MapRSE.SOOTOPOLIS_CITY, (0, 0))
objects = md.objects
print("\n  %d object-event templates on this map\n" % len(objects))
print("   id  gfx  who            tile       nearest approach (waypoints)")
print("   " + "-" * 78)
found = {}
for o in objects:
    c = tuple(o.local_coordinates)
    who = GFX.get(o.graphics_id, "?")
    if who != "?":
        found.setdefault(who, []).append((o.local_id, c))
    app = approach(c)
    best = "%s in %d" % (app[0][0], app[0][1]) if app else "⛔ NONE — unreachable"
    print("   %3d  %3d  %-14s %-10s %s" % (o.local_id, o.graphics_id, who, "%d,%d" % c, best))

print()
for who in ("STEVEN", "WALLACE", "EXPERT_M", "MAXIE", "ARCHIE"):
    check("the cast includes %s (identified by graphics id, not by guessing)" % who,
          who in found, str(found.get(who)))

# --- assertion 2: leg 2 is possible at all ------------------------------------------------------
steven = found.get("STEVEN", [(None, None)])[0][1]
if os.environ.get("POKEBOT_CH21NPC_FAULT") == "wrongtile":
    steven = (0, 0)
    print("  FAULT: looking for Steven at %s instead -- assertion 2 MUST fail." % (steven,))
app = approach(steven) if steven else []
check("⛔ LEG 2 IS POSSIBLE: STEVEN is APPROACHABLE from the leg-1 arrival tile",
      bool(app), ("nearest %s in %d waypoints" % (app[0][0], app[0][1])) if app else "no adjacent tile reachable")

# --- assertion 3: leg 5 is possible at all -------------------------------------------------------
for who in ("MAXIE", "ARCHIE"):
    c = found.get(who, [(None, None)])[0][1]
    a = approach(c) if c else []
    check("LEG 5 PRECONDITION: %s is approachable (HM07 needs BOTH)" % who,
          bool(a), ("nearest %s in %d" % (a[0][0], a[0][1])) if a else "unreachable")

# --- assertion 4: the cave really is sealed, which is WHY the escort exists ----------------------
column = [(31, y) for y in range(16, 23)] + [(30, 18), (32, 18)]
walkable = [c for c in column if waypoints(c)]
print()
check("⛔ the Cave of Origin approach column is NOT walkable (so leg 2 MUST use Steven's escort)",
      not walkable, "walkable tiles found: %s" % (walkable or "none"))
print("      ‼ (31,18) carries TWO templates — EXPERT_M and WALLACE — so the corridor is")
print("        body-blocked as our §Ch21 ATLAS says. ⚠ The whole column refuses, not just that tile,")
print("        so the block is not the ONLY reason; the ledge is unreachable from the water too.")

print("\n" + "=" * 98)
if FAILURES:
    print("  %d ASSERTION(S) FAILED:" % len(FAILURES))
    for f in FAILURES:
        print("      - " + f)
    sys.exit(1)
print("  ✅ ALL PASS — leg 2's target is STEVEN at %s, and he is reachable." % (steven,))
