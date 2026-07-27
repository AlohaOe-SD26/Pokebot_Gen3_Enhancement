"""Regression: badge flags read GARBAGE during map warps, and the recorder believed it.

FROM REAL DATA — the user's x4 bundle of 2026-07-26 (`P1 - P4 x4 LOGs 20260726_181825`):

  * P1 started exactly ONE run ("=== ENDLESS RESET: starting run 1/infinite ===", once)
    and its badge-log.json contained **Stone x10, Knuckle x5, Balance x1**. A badge cannot
    be earned twice in a playthrough, and Balance is the 5th badge in a run that reached
    the 2nd.
  * The debug log shows why. Badge flags live in the save block, and during a map warp the
    save-block reads return nonsense for a frame or two — visible directly as the MAP
    itself flipping to a garbage group and back:

        f1190097 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5)
        f1190101 [MAP] MAUVILLE CITY(10,5) -> MAUVILLE CITY(0,2)
        f1190102 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5)

    The badge poll landing in that window recorded BALANCE at f1,190,100 and then
    Stone+Knuckle together at f1,190,160 — one poll interval later.

Three independent filters now stand in the way: debounce over two consecutive polls,
once-per-run de-duplication, and a gym-order check. This test drives each one, and replays
the real trace end to end.
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


FLAGS: set[str] = set()


class _N:
    def __init__(self, name):
        self.name = name


class FakeMon:
    name = "COMBUSKEN"
    species_name_for_stats = "Combusken"
    level = 24
    current_hp, total_hp = 60, 60
    is_egg = is_shiny = is_anti_shiny = False
    status_condition = StatusCondition.Healthy
    exp_fraction_to_next_level = 0.5
    gender = "male"
    poke_ball = nature = ability = _N("x")
    held_item = None
    species = types.SimpleNamespace(name="Combusken", types=[_N("Fire")])
    ivs = types.SimpleNamespace(hp=1, attack=1, defence=1, special_attack=1,
                                special_defence=1, speed=1)
    moves = []


tmp = Path(tempfile.mkdtemp(prefix="badge-transient-"))
sys.modules["modules.memory"] = types.ModuleType("modules.memory")
sys.modules["modules.memory"].get_event_flag = lambda flag: flag in FLAGS
sys.modules["modules.pokemon_party"] = types.ModuleType("modules.pokemon_party")
sys.modules["modules.pokemon_party"].get_party = lambda: [FakeMon()]

import modules.context as ctx_mod  # noqa: E402

ctx_mod.context.profile = types.SimpleNamespace(path=tmp)

STEP = badge_log._POLL_INTERVAL
frame = [0]


def poll(times=1):
    for _ in range(times):
        frame[0] += STEP
        badge_log.on_frame(frame[0])


def log():
    return badge_log.read_log(types.SimpleNamespace(path=tmp))


def fresh_run():
    (tmp / "badge-log.json").unlink(missing_ok=True)
    badge_log.reset_for_new_run(frame[0])


print("== a genuine win is still recorded (the filters must not block real badges) ==")
FLAGS = set()
fresh_run()
poll(2)
FLAGS.add("BADGE01_GET")
poll(2)  # two consecutive polls with the flag set
records = log()
check(len(records) == 1 and records[0]["badge"] == "Stone", f"Stone recorded once (got {[r['badge'] for r in records]})")

print("\n== FILTER 1: a one-poll transient is ignored ==")
before = len(log())
FLAGS.add("BADGE05_GET")   # the exact garbage seen in the real bundle
poll(1)                    # appears for a single poll...
FLAGS.discard("BADGE05_GET")
poll(2)                    # ...and is gone again
check(len(log()) == before, "a Balance badge that appeared for ONE poll was not recorded")

print("\n== FILTER 3: a badge whose predecessors are unset is a corrupt read ==")
before = len(log())
FLAGS.add("BADGE05_GET")   # sustained this time, but 02/03/04 are not set
poll(3)
check(len(log()) == before,
      "Balance stayed unrecorded while Knuckle/Dynamo/Heat were unset (gym order is linear)")
FLAGS.update({"BADGE02_GET", "BADGE03_GET", "BADGE04_GET"})
poll(3)
badges = [r["badge"] for r in log()]
check("Balance" in badges, f"once the predecessors are set it IS recorded ({badges})")

print("\n== FILTER 2: the same badge cannot be recorded twice in one run ==")
before = len(log())
for _ in range(6):
    FLAGS.discard("BADGE01_GET")   # flag flickers off...
    poll(1)
    FLAGS.add("BADGE01_GET")       # ...and back, exactly as the warp transient did
    poll(2)
check(len(log()) == before, f"six flicker cycles produced no new records (got {len(log()) - before})")

print("\n== after a NEW RUN the same badge is recorded again ==")
before = len(log())
FLAGS = set()
badge_log.reset_for_new_run(frame[0])
poll(2)
FLAGS.add("BADGE01_GET")
poll(2)
after = log()
check(len(after) == before + 1, f"Stone recorded once for the new run (got {len(after) - before})")
check(after[-1]["run_index"] != after[0]["run_index"], "records carry a distinct run_index")

print("\n== THE REAL TRACE: P1's single run must yield ONE Stone, not TEN ==")
FLAGS = set()
fresh_run()
poll(2)
FLAGS.add("BADGE01_GET")
poll(2)                                   # the genuine Stone win
for _ in range(9):                        # nine warps, as the real run had
    FLAGS = {"BADGE05_GET"}               # garbage: flags read nonsense mid-warp
    poll(1)
    FLAGS = set()                         # ...then read empty...
    poll(1)
    FLAGS = {"BADGE01_GET"}               # ...then restore
    poll(2)
records = log()
badges = [r["badge"] for r in records]
check(badges == ["Stone"], f"exactly one Stone across nine warp transients (got {badges})")
check(not any(b == "Balance" for b in badges), "and no phantom Balance badge")

print("\n== the lane prefix now survives a re-enable by the story mode ==")
from modules import debug_logger  # noqa: E402

debug_logger.set_name_prefix("P1-")
path = debug_logger.enable(types.SimpleNamespace(path=tmp))   # no name_prefix argument
debug_logger.disable()
check(Path(path).name.startswith("P1-"),
      f"an enable() with NO prefix argument still tagged the file: {Path(path).name}")
debug_logger.set_name_prefix("")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
