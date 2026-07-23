"""Solve the Lavaridge Gym trapdoor maze STATICALLY, from the ROM's own data.

Model (proved by the warp dump + the run8 live trace):
  * 1F tile with metatile behaviour 104 (MB_LAVARIDGE_GYM_1F_WARP) = a HOLE.
    Falling through it lands you on B1F at the SAME coordinate (warp table is
    literally same-coord, verified: 1F(8,9) -> B1F(8,9) in ch11d_run8.log).
  * B1F tile with behaviour 41 (MB_LAVARIDGE_GYM_B1F_WARP) = a GEYSER; stepping
    onto it launches you to 1F at the SAME coordinate.
  * A warp event whose tile has behaviour 0 is INERT (a landing pad only) — it
    never fires by walking. This is why "landings don't auto-trigger".
  * Each floor is cut into sealed rooms; you only move between rooms by
    falling/erupting. A B1F room with NO geyser is a SOFTLOCK — never fall into
    the hole that leads there.

So: state = the 1F room you stand in; a move = (hole H in this room) -> B1F room
of H -> (geyser G in that B1F room) -> the 1F room of G. BFS that graph from the
entrance room to Flannery's room and print the canonical chain.
"""

import pathlib as _pl
import sys
from collections import deque

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-fresh")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(p, lambda: None)
context.audio = False
context.video = False

from modules.map import get_map_data
from modules.map_data import MapRSE

GYM1F = MapRSE.LAVARIDGE_TOWN_GYM_1F.value
GYMB1F = MapRSE.LAVARIDGE_TOWN_GYM_B1F.value
HOLE_MB = 104  # MB_LAVARIDGE_GYM_1F_WARP
GEYSER_MB = 41  # MB_LAVARIDGE_GYM_B1F_WARP
TOWN_EXITS = {(13, 18), (14, 18)}
FLANNERY_APPROACH = (13, 10)


LEDGE_SOUTH_MB = 59  # MB_JUMP_SOUTH — collision=1 but hoppable downward (2 tiles)


def scan(gnum):
    md = get_map_data(gnum, (0, 0))
    w, h = md.map_size
    passable, behav, ledge = set(), {}, set()
    for y in range(h):
        for x in range(w):
            t = get_map_data(gnum, (x, y))
            mb = t._metatile_attributes[0] & 0x1FF  # low bits = behaviour; high bits = layer type
            behav[(x, y)] = mb
            if not t.collision:
                passable.add((x, y))
            elif mb == LEDGE_SOUTH_MB:
                ledge.add((x, y))

    def moves(t):
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            n = (t[0] + dx, t[1] + dy)
            if n in passable:
                yield n
        # One-way ledge hop: step Down onto a jump-south tile, land two tiles below.
        below, landing = (t[0], t[1] + 1), (t[0], t[1] + 2)
        if below in ledge and landing in passable:
            yield landing

    # Rooms = strongly-walkable areas ignoring the one-way hops; the hops are the
    # DIRECTED edges between them (you can never climb back up a ledge).
    rooms, room_of = [], {}
    for start in sorted(passable):
        if start in room_of:
            continue
        comp, q = {start}, deque([start])
        while q:
            t = q.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                n = (t[0] + dx, t[1] + dy)
                if n in passable and n not in comp:
                    comp.add(n)
                    q.append(n)
        for t in comp:
            room_of[t] = len(rooms)
        rooms.append(comp)

    # Merge rooms reachable from each other by hops into a REACH map: from any tile,
    # which rooms can you get to on foot (hops included)?
    reach = {}
    for i, comp in enumerate(rooms):
        seen, q = set(comp), deque(comp)
        while q:
            t = q.popleft()
            for n in moves(t):
                if n not in seen:
                    seen.add(n)
                    q.append(n)
        reach[i] = seen
    return passable, behav, rooms, room_of, reach


p1, b1, rooms1, roomof1, reach1 = scan(GYM1F)
pb, bb, roomsB, roomofB, reachB = scan(GYMB1F)

holes = {t for t, mb in b1.items() if mb == HOLE_MB and t not in TOWN_EXITS}
geysers = {t for t, mb in bb.items() if mb == GEYSER_MB}

print("=== 1F rooms (holes reachable on foot, ledge hops included) ===")
for i, r in enumerate(rooms1):
    tag = "  <-- FLANNERY" if FLANNERY_APPROACH in r else ""
    tag += "  <-- ENTRANCE" if TOWN_EXITS & r else ""
    print(f"  1F room {i}: {len(r)} tiles, reachable holes={sorted(holes & reach1[i])}{tag}")
print("=== B1F rooms (geysers reachable on foot, ledge hops included) ===")
for i, r in enumerate(roomsB):
    gs = sorted(geysers & reachB[i])
    print(f"  B1F room {i}: {len(r)} tiles, reachable geysers={gs}{'   *** TRAP (no geyser) ***' if not gs else ''}")

start_room = roomof1[next(iter(TOWN_EXITS))]
goal_room = roomof1[FLANNERY_APPROACH]
print(f"\nstart 1F room={start_room}   goal 1F room={goal_room}")

# BFS over 1F rooms; an edge is (hole, geyser).
prev = {start_room: None}
q = deque([start_room])
while q:
    r = q.popleft()
    if r == goal_room:
        break
    for hole in sorted(holes & reach1[r]):
        broom = roomofB[hole]
        outs = sorted(geysers & reachB[broom])
        if not outs:
            continue  # softlock room — never fall here
        for g in outs:
            nr = roomof1.get(g)
            if nr is None:
                # The 1F landing tile reads as collision (e.g. (4,16), elevation 0).
                # You still arrive there and step off — attribute it to an adjacent room.
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nr = roomof1.get((g[0] + dx, g[1] + dy))
                    if nr is not None:
                        break
            if nr is None:
                continue
            if nr not in prev:
                prev[nr] = (r, hole, g)
                q.append(nr)

if goal_room not in prev:
    print("\nNO PATH under this model — the model is wrong somewhere.")
else:
    chain, node = [], goal_room
    while prev[node] is not None:
        r, hole, g = prev[node]
        chain.append((r, hole, g, node))
        node = r
    chain.reverse()
    print(f"\n=== CANONICAL CHAIN ({len(chain)} falls) ===")
    for i, (r, hole, g, nr) in enumerate(chain, 1):
        print(f"  {i}. in 1F room {r}: fall through hole {hole} -> B1F room {roomofB[hole]}"
              f" -> walk to geyser {g} -> 1F room {nr}")
    print(f"  then walk to Flannery approach {FLANNERY_APPROACH}")
    print("\nPY_CHAIN =", [(h, g) for _r, h, g, _n in chain])
    print("TRAP_HOLES =", sorted(h for h in holes if not (geysers & roomsB[roomofB[h]])))
