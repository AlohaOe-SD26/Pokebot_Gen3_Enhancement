"""Prove the badge case's data layer, and the integrity of its decomp-derived table.

Two halves:
  * `build_case()` logic, exercised against a SYNTHETIC table so it does not depend on the
    real one's contents;
  * the real `BADGES` table's integrity — eight badges, the right flags, sprites that
    actually exist on disk.
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

from modules import badge_case  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


REAL = badge_case.BADGES
SYNTH = (
    badge_case.BadgeInfo("BADGE01_GET", "Alpha", "Ann", "Aville", "Rock", "Nosepass", 15, "Stone.png"),
    badge_case.BadgeInfo("BADGE02_GET", "Beta", "Bob", "Bville", "Fighting", "Makuhita", 16, "Knuckle.png"),
)

print("== build_case with nothing known ==")
badge_case.BADGES = SYNTH
try:
    entries = badge_case.build_case(None, None)
    check(len(entries) == 2, "one entry per badge in the table")
    check(all(not e.earned for e in entries), "nothing is earned")
    check(all(e.records == [] for e in entries), "no records")
    check(badge_case.earned_count(entries) == 0, "earned_count is 0")
    check(entries[0].latest is None and entries[0].team_summary() == "",
          "latest/team_summary are safe when empty")

    print("\n== earned from live flags ==")
    entries = badge_case.build_case(["BADGE01_GET"], [])
    check(entries[0].earned and not entries[1].earned, "only the flagged badge is earned")
    check(badge_case.earned_count(entries) == 1, "earned_count is 1")

    print("\n== a recorded win implies the badge even with no flag ==")
    # A lane that has not published its flags yet must not show a badge it demonstrably won.
    records = [{"flag": "BADGE02_GET", "badge": "Beta",
                "team": [{"name": "COMBUSKEN", "level": 18}]}]
    entries = badge_case.build_case([], records)
    check(entries[1].earned, "the recorded badge shows as earned")
    check(entries[1].team_summary() == "COMBUSKEN L18", f"team_summary: {entries[1].team_summary()}")

    print("\n== many wins per badge (an endless batch replays the story) ==")
    records = [
        {"flag": "BADGE01_GET", "earned_at": "2026-07-26T10:00:00",
         "team": [{"name": "TORCHIC", "level": 14}]},
        {"flag": "BADGE01_GET", "earned_at": "2026-07-26T11:00:00",
         "team": [{"name": "COMBUSKEN", "level": 17}, {"name": "ZIGZAGOON", "level": 9}]},
        {"flag": "BADGE02_GET", "earned_at": "2026-07-26T12:00:00", "team": []},
    ]
    entries = badge_case.build_case(["BADGE01_GET", "BADGE02_GET"], records)
    check(len(entries[0].records) == 2, f"two wins recorded for badge 1 (got {len(entries[0].records)})")
    check(entries[0].latest["earned_at"].endswith("11:00:00"), "latest is the most recent")
    check(entries[0].team_summary() == "COMBUSKEN L17, ZIGZAGOON L9",
          f"team_summary uses the latest: {entries[0].team_summary()}")
    check(entries[0].team_summary(entries[0].records[0]) == "TORCHIC L14",
          "an explicit record can be summarised too")
    check(entries[1].team_summary() == "", "an empty team summarises to nothing, not a crash")

    print("\n== junk input degrades, never raises ==")
    for junk in (None, [], "nonsense", [None, 3, "x"], [{"no_flag": 1}]):
        try:
            entries = badge_case.build_case([], junk)
            check(len(entries) == 2, f"junk records {junk!r} -> a full, empty case")
        except Exception as exc:
            check(False, f"junk records {junk!r} raised {type(exc).__name__}: {exc}")
    check(len(badge_case.build_case("not-a-set", [])) == 2, "junk flags -> a full case")
finally:
    badge_case.BADGES = REAL

print("\n== the REAL table's integrity ==")
check(len(badge_case.BADGES) == 8, f"eight Hoenn badges (got {len(badge_case.BADGES)})")
flags = [b.flag for b in badge_case.BADGES]
check(flags == [f"BADGE0{i}_GET" for i in range(1, 9)],
      f"flags are BADGE01_GET..BADGE08_GET in gym order (got {flags})")
check(len({b.badge for b in badge_case.BADGES}) == len(badge_case.BADGES), "badge names are unique")
check(len({b.leader for b in badge_case.BADGES}) == len(badge_case.BADGES), "leader names are unique")

sprites = SANDBOX / "modules" / "web" / "static" / "sprites" / "badges"
missing = [b.sprite for b in badge_case.BADGES if not (sprites / b.sprite).is_file()]
check(not missing, f"every badge sprite exists on disk (missing: {missing})")
check(all(b.ace and b.ace_level > 0 for b in badge_case.BADGES), "every badge names an ace with a level")
check(all(b.type for b in badge_case.BADGES), "every gym has a type")

print("\n== the overlay builds, re-opens and tears down against a real Tk root ==")
import tkinter  # noqa: E402

from modules.gui.dashboard_gui import DashboardScreen  # noqa: E402

badge_case.BADGES = SYNTH
try:
    root = tkinter.Tk()
    root.withdraw()
    screen = DashboardScreen(root)
    screen._log_event = lambda *a, **k: None
    # No profile and no batch: the case must still open (a fresh install looks like this).
    import modules.gui.dashboard_gui as dg  # noqa: E402

    dg.context.profile = None

    check(screen._bag_icon() is not None, "the Bag icon renders")
    check(screen._bag_icon() is screen._bag_icon(), "and is cached, not redrawn per paint")

    screen.open_badge_case()
    check(screen._badge_case_frame is not None, "open_badge_case built the overlay")
    check(screen._badge_case_entries_cache is not None, "entries were snapshotted, not re-read per hover")

    screen._show_badge_detail(0)
    check(True, "hovering a badge renders its detail without raising")
    screen._show_badge_detail(1, pin=True)
    check(screen._badge_case_selected == 1, "clicking pins the selection")
    screen._show_badge_detail(99)
    check(True, "an out-of-range index is ignored rather than raising")

    screen.toggle_badge_case()
    check(screen._badge_case_frame is None, "toggle closes it")
    check(screen._badge_case_entries_cache is None, "and drops the snapshot")
    screen.toggle_badge_case()
    check(screen._badge_case_frame is not None, "toggle re-opens it")
    screen.close_badge_case()
    screen.close_badge_case()
    check(screen._badge_case_frame is None, "closing twice is safe")

    print("\n== an unearned badge renders as a silhouette, not the colour sprite ==")
    earned_icon = screen._badge_sprite("Stone.png", True)
    silhouette = screen._badge_sprite("Stone.png", False)
    check(earned_icon is not None and silhouette is not None, "both variants render")
    check(earned_icon is not silhouette, "they are distinct images")
    check(screen._badge_sprite("Stone.png", False) is silhouette, "and are cached per (sprite, earned)")
    check(screen._badge_sprite("does-not-exist.png", True) is None,
          "a missing sprite degrades to None instead of raising")

    root.destroy()
finally:
    badge_case.BADGES = REAL

print("\n== badge_log reuses the SAME table (no second copy to drift) ==")
from modules import badge_log  # noqa: E402

check(len(badge_log.BADGES) == len(badge_case.BADGES), "badge_log exposes the same number of badges")
check([b[0] for b in badge_log.BADGES] == flags, "and the same flags, in the same order")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
