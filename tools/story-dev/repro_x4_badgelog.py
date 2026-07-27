"""Prove the badge recorder: it fires once per badge, per run, with the team attached.

The trap this exists to catch: the endless mode HARD-RESETS between runs, taking every
badge flag back to 0. A recorder that remembers what it has seen across a reset would log
run 1's badges and silently never log another — in exactly the batch it was built for.
"""
import json
import sys
import tempfile
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

from modules import badge_log  # noqa: E402
from modules.pokemon import StatusCondition  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


# --- fakes -----------------------------------------------------------------
FLAGS: set[str] = set()


class _N:
    def __init__(self, name):
        self.name = name


class FakeMon:
    def __init__(self, name):
        self.name = name
        self.species_name_for_stats = name.title()
        self.level = 14
        self.current_hp, self.total_hp = 30, 41
        self.is_egg = self.is_shiny = self.is_anti_shiny = False
        self.status_condition = StatusCondition.Healthy
        self.exp_fraction_to_next_level = 0.1
        self.gender = "male"
        self.poke_ball, self.nature, self.ability = _N("Poké Ball"), _N("Timid"), _N("Blaze")
        self.held_item = None
        self.species = types.SimpleNamespace(name=name.title(), types=[_N("Fire")])
        self.ivs = types.SimpleNamespace(hp=1, attack=2, defence=3,
                                         special_attack=4, special_defence=5, speed=6)
        self.moves = [types.SimpleNamespace(move=_N("Ember"))]


PARTY = [FakeMon("TORCHIC")]

tmp = Path(tempfile.mkdtemp(prefix="badgelog-"))
fake_profile = types.SimpleNamespace(path=tmp)

fake_memory = types.ModuleType("modules.memory")
fake_memory.get_event_flag = lambda flag: flag in FLAGS
sys.modules["modules.memory"] = fake_memory

fake_party_mod = types.ModuleType("modules.pokemon_party")
fake_party_mod.get_party = lambda: list(PARTY)
sys.modules["modules.pokemon_party"] = fake_party_mod

import modules.context as ctx_mod  # noqa: E402

ctx_mod.context.profile = fake_profile


def poll(frame):
    badge_log.on_frame(frame)


print("== the first poll ADOPTS existing badges without inventing records ==")
badge_log.reset_for_new_run(0)
FLAGS = {"BADGE01_GET", "BADGE02_GET"}  # as if a mid-game save were loaded
poll(100)
check(badge_log.read_log(fake_profile) == [],
      "loading a save with 2 badges logged nothing (they were not 'just earned')")

print("\n== a badge earned after that IS recorded, with the team ==")
# ‼ TWO consecutive polls are required since the debounce landed (see
# repro_badge_transient.py): badge flags read GARBAGE for a frame or two during a map warp,
# so a flag seen on a single poll is not evidence of anything.
FLAGS.add("BADGE03_GET")
poll(100 + badge_log._POLL_INTERVAL)
poll(100 + 2 * badge_log._POLL_INTERVAL)
log = badge_log.read_log(fake_profile)
check(len(log) == 1, f"exactly one record (got {len(log)})")
if log:
    rec = log[0]
    check(rec["flag"] == "BADGE03_GET", "flag")
    check(rec["badge"] == "Dynamo" and rec["leader"] == "Wattson" and rec["city"] == "Mauville",
          f"badge/leader/city ({rec['badge']}/{rec['leader']}/{rec['city']})")
    check(len(rec["team"]) == 1 and rec["team"][0]["name"] == "TORCHIC", "the team was captured")
    check(rec["team"][0]["level"] == 14 and rec["team"][0]["moves"] == ["Ember"], "team detail captured")
    check("earned_at" in rec and "frame" in rec, "timestamp + frame recorded")

print("\n== the same badge is not recorded twice ==")
for i in range(5):
    poll(1000 + i * badge_log._POLL_INTERVAL)
check(len(badge_log.read_log(fake_profile)) == 1, "still one record after repeated polls")

print("\n== the poll interval is respected ==")
# The loop above last polled at 1000 + 4*interval, so anything before
# 1000 + 5*interval must be ignored.
last_polled = 1000 + 4 * badge_log._POLL_INTERVAL
FLAGS.add("BADGE04_GET")
poll(last_polled + badge_log._POLL_INTERVAL - 1)  # one frame too soon
check(len(badge_log.read_log(fake_profile)) == 1, "a poll inside the interval did nothing")
poll(last_polled + badge_log._POLL_INTERVAL)
check(len(badge_log.read_log(fake_profile)) == 1, "one eligible poll is not yet enough (debounce)")
poll(last_polled + 2 * badge_log._POLL_INTERVAL)
check(len(badge_log.read_log(fake_profile)) == 2, "the SECOND consecutive poll recorded it")

print("\n== !! AFTER A HARD RESET, run 2's badges are recorded AGAIN ==")
FLAGS = set()                      # the reset clears every flag
badge_log.reset_for_new_run(50_000)
poll(50_100)                       # first poll of run 2: adopts nothing
FLAGS.add("BADGE01_GET")
poll(50_100 + badge_log._POLL_INTERVAL)
poll(50_100 + 2 * badge_log._POLL_INTERVAL)
log = badge_log.read_log(fake_profile)
check(len(log) == 3, f"run 2's Stone Badge was recorded (total {len(log)})")
if len(log) == 3:
    check(log[2]["badge"] == "Stone", "it is the Stone Badge")
    check(log[2]["run_started_frame"] == 50_000, "records carry run_started_frame for grouping")
    check(log[0]["run_started_frame"] == 0, "run 1's records kept their own run marker")

print("\n== records accumulate across runs, never rewritten ==")
check([r["badge"] for r in badge_log.read_log(fake_profile)] == ["Dynamo", "Heat", "Stone"],
      "all three records survive in order")

print("\n== a broken party read costs the team, not the record ==")


def boom():
    raise RuntimeError("party memory mid-write")


fake_party_mod.get_party = boom
FLAGS.add("BADGE02_GET")
poll(60_000)
poll(60_000 + badge_log._POLL_INTERVAL)
log = badge_log.read_log(fake_profile)
check(len(log) == 4 and log[3]["badge"] == "Knuckle", "the badge was still recorded")
check(log[3]["team"] == [], "the team degraded to empty rather than losing the record")

print("\n== the file is valid JSON on disk ==")
raw = (tmp / "badge-log.json").read_text(encoding="utf-8")
check(isinstance(json.loads(raw), list), "badge-log.json parses as a list")

print("\n== the badge table matches the sprite assets that exist ==")
sprites = SANDBOX / "modules" / "web" / "static" / "sprites" / "badges"
missing = [b[4] for b in badge_log.BADGES if not (sprites / b[4]).is_file()]
check(not missing, f"every badge sprite exists (missing: {missing})")
check(len(badge_log.BADGES) == 8, "eight Hoenn badges")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
