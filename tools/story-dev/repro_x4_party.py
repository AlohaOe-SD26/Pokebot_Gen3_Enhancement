"""Prove the ENDLESS LOOP x4 party hand-off: lane -> status blob -> dashboard strip.

The party the user sees during a batch belongs to a LANE (another process), so it travels
as JSON and is rebuilt by `modules/remote_party.py` into stand-ins the existing party
renderer can read. This checks the whole chain, and in particular:

  * every attribute the party UI actually reads survives the trip (the list was measured
    off dashboard_gui, not guessed — see modules/remote_party.py);
  * `status_condition` comes back as the REAL enum member, because dashboard_gui:3239
    compares it with `is not StatusCondition.Healthy` and any look-alike fails that;
  * a full 6-Pokemon team with moves and IVs FITS in STATUS_BYTES (it did not at the
    original 1 KiB, which would have silently dropped the whole blob to its fallback);
  * the dashboard reads the FOCUSED lane, and re-focusing swaps the party.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

import json  # noqa: E402

import PIL.Image  # noqa: E402

from modules.gui.tile_child import PokebotTileChild  # noqa: E402
from modules.pokemon import StatusCondition  # noqa: E402
from modules.remote_party import party_from_status  # noqa: E402
from modules.tile_bridge import STATUS_BYTES, TileBridge  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class _N:
    def __init__(self, name):
        self.name = name


class _IVs:
    hp, attack, defence, special_attack, special_defence, speed = 31, 12, 7, 25, 3, 30


class _Move:
    def __init__(self, name):
        self.move = _N(name)


class _Species:
    def __init__(self, name, types):
        self.name, self.types = name, [_N(t) for t in types]


class FakeMon:
    """Exposes exactly the attribute surface `_mon_payload` reads off a real Pokemon."""

    def __init__(self, name="TORCHIC", level=5, hp=18, total=21, status="Burn", shiny=False, egg=False):
        self.name = name
        self.species_name_for_stats = name.title()
        self.level = level
        self.current_hp = hp
        self.total_hp = total
        self.is_egg = egg
        self.is_shiny = shiny
        self.is_anti_shiny = False
        self.status_condition = StatusCondition[status]
        self.exp_fraction_to_next_level = 0.4321
        self.gender = "male"
        self.poke_ball = _N("Great Ball")
        self.nature = _N("Adamant")
        self.ability = _N("Blaze")
        self.held_item = _N("Oran Berry")
        self.species = _Species(name.title(), ["Fire", "Fighting"])
        self.ivs = _IVs()
        self.moves = [_Move(m) for m in ("Scratch", "Growl", "Ember", "Peck")]


print("== one Pokemon survives the round trip ==")
payload = PokebotTileChild._mon_payload(FakeMon())
party = party_from_status({"team": [payload]})
check(len(party) == 1, "one member rebuilt")
mon = party[0]
check(mon.name == "TORCHIC", "name")
check(mon.species_name_for_stats == "Torchic", "species_name_for_stats (drives the sprite)")
check(mon.level == 5, "level")
check((mon.current_hp, mon.total_hp) == (18, 21), "current_hp / total_hp")
check(mon.is_egg is False and mon.is_shiny is False and mon.is_anti_shiny is False, "egg / shiny / anti-shiny flags")
check(mon.is_empty is False, "is_empty (the strip reads it via getattr)")
check(abs(mon.exp_fraction_to_next_level - 0.4321) < 1e-6, "exp_fraction_to_next_level")
check(mon.gender == "male", "gender")
check(mon.poke_ball.name == "Great Ball", "poke_ball.name")
check(mon.nature.name == "Adamant", "nature.name")
check(mon.ability.name == "Blaze", "ability.name")
check(mon.held_item.name == "Oran Berry", "held_item.name")
check([t.name for t in mon.species.types] == ["Fire", "Fighting"], "species.types")
check((mon.ivs.hp, mon.ivs.attack, mon.ivs.defence) == (31, 12, 7), "ivs.hp/attack/defence")
check((mon.ivs.special_attack, mon.ivs.special_defence, mon.ivs.speed) == (25, 3, 30), "ivs.spa/spd/spe")
check([m.move.name for m in mon.moves] == ["Scratch", "Growl", "Ember", "Peck"], "moves[].move.name")

print("\n== status_condition is the REAL enum member (identity, not equality) ==")
check(mon.status_condition is StatusCondition.Burn, "a burned mon IS StatusCondition.Burn")
healthy = party_from_status({"team": [PokebotTileChild._mon_payload(FakeMon(status="Healthy"))]})[0]
check(healthy.status_condition is StatusCondition.Healthy,
      "a healthy mon IS StatusCondition.Healthy (dashboard_gui:3239 uses `is not`)")

print("\n== a held item of None round-trips as None, not the string 'None' ==")
bare = FakeMon()
bare.held_item = None
check(party_from_status({"team": [PokebotTileChild._mon_payload(bare)]})[0].held_item is None,
      "held_item is None when nothing is held")

print("\n== an unreadable attribute costs that FIELD, not the team ==")


class Exploding:
    """Reads fine except for `ivs`, which raises — as party memory does mid-write."""

    def __init__(self):
        self._inner = FakeMon()

    def __getattr__(self, item):
        if item == "ivs":
            raise RuntimeError("party memory was mid-write")
        return getattr(self._inner, item)


payload = PokebotTileChild._mon_payload(Exploding())
rebuilt = party_from_status({"team": [payload]})
check(len(rebuilt) == 1, "the member still made it across")
check(rebuilt[0].name == "TORCHIC", "the readable fields are intact")
check(rebuilt[0].ivs.hp == 0, "the unreadable field degraded to a default")

print("\n== a FULL six-mon team fits in STATUS_BYTES ==")
team = [PokebotTileChild._mon_payload(FakeMon(name=n, level=55)) for n in
        ("BLAZIKEN", "SWAMPERT", "SCEPTILE", "GARDEVOIR", "AGGRON", "FLYGON")]
status = {"lane": "P1", "message": "Story: " + "x" * 150, "mode": "Story (ENDLESS RESET)",
          "frame": 2_400_000, "log": "P1-Story_(ENDLESS_RESET)-debug-20260726-153527.log",
          "log_bytes": 4_193_402, "party": "BLAZIKEN L55  151/151",
          "where": "MapRSE.EVER_GRANDE_CITY (12, 34)", "team": team}
blob = json.dumps(status, separators=(",", ":")).encode("utf-8")
print(f"  full 6-mon status blob: {len(blob):,} bytes / {STATUS_BYTES:,} available")
check(len(blob) < STATUS_BYTES, f"it fits ({len(blob)} < {STATUS_BYTES})")

print("\n== through shared memory, and the dashboard reads the FOCUSED lane ==")
SHM = "pkbtilepartytest"
bridge = TileBridge(SHM, 4, create=True)
pixels = PIL.Image.new("RGB", (240, 160), (20, 20, 20)).tobytes()
for slot, lead in enumerate(("TORCHIC", "MUDKIP", "TREECKO", "ZIGZAGOON")):
    bridge.publish(slot, pixels, slot + 1, 100 + slot, slot,
                   {"lane": f"P{slot + 1}", "message": f"lane {slot}",
                    "team": [PokebotTileChild._mon_payload(FakeMon(name=lead, level=10 + slot))]})

frame = bridge.read(0)
check(frame is not None and len(frame.status.get("team", [])) == 1, "the team survived shared memory")

import tkinter  # noqa: E402
from tkinter import Canvas  # noqa: E402

from modules.gui.dashboard_gui import DashboardScreen  # noqa: E402


class FakeLane:
    def __init__(self, slot, tag, starter):
        self.slot, self.tag, self.starter = slot, tag, starter
        self.is_alive, self.restarts = True, 0
        self.profile_name = f"endless-{tag}-{starter}"


class FakeBatch:
    max_restarts = 20

    def __init__(self, bridge):
        self.bridge = bridge
        self.lanes = [FakeLane(i, f"P{i + 1}", s) for i, s in
                      enumerate(("torchic", "mudkip", "treecko", "random"))]

    def poll(self):
        pass


root = tkinter.Tk()
root.withdraw()
screen = DashboardScreen(root)
screen.canvas = Canvas(root, width=960, height=640)
screen._video_size = (960, 640)
screen._x4_batch = FakeBatch(bridge)
screen._log_event = lambda *a, **k: None
screen._refresh_party_strip = lambda: None  # needs widgets we did not build

for slot, expected in enumerate(("TORCHIC", "MUDKIP", "TREECKO", "ZIGZAGOON")):
    screen._x4_focus = slot
    party = screen._x4_focused_party()
    check(len(party) == 1 and party[0].name == expected,
          f"focus {slot} -> lead is {expected} (got {[p.name for p in party] or '<none>'})")

print("\n== clicking a quadrant swaps the party ==")
offset_x, offset_y, size = screen._video_draw_rect()
screen._x4_click(types.SimpleNamespace(x=offset_x + size[0] - 10, y=offset_y + size[1] - 10))
check(screen._x4_focus == 3, "clicked bottom-right")
check(screen._x4_focused_party()[0].name == "ZIGZAGOON", "the party followed the click")

print("\n== a lane that has published no team yields an empty party, not a crash ==")
bridge.publish(1, pixels, 99, 101, 0, {"lane": "P2", "message": "booting"})
screen._x4_focus = 1
check(screen._x4_focused_party() == [], "no team -> []")
check(party_from_status(None) == [] and party_from_status({"team": "nonsense"}) == [],
      "junk status -> [] rather than raising")

bridge.close()
root.destroy()
print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
