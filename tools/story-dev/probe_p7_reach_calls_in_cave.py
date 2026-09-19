# -*- coding: utf-8 -*-
"""⭐ P7: DOES ANYTHING CONSULT REACHABILITY WHILE THE BOT GRINDS INSIDE VICTORY ROAD?

WHY THIS EXISTS. Today's `#24-waterfallcap` fix changed one measured thing: standing INSIDE Victory
Road, `best_training_area(allow=_counter_area_allowed)` went from `None` to `ROUTE121`. I predicted
(P7) that this can never fire in production, because a caller census found **zero** `region_reach`
references in `victory_road.py` and `pokemon_league.py`. ⛔ **THAT IS AN ABSENCE CLAIM OVER A LARGE
CODEBASE, AND I GRADED IT UNTESTED RATHER THAN CONFIRMED.** This probe tests it.

\u203c AND IT MATTERS MORE NOW THAN IT DID THIS MORNING. `#24-trainingbrackets` proposes to promote
`VICTORY_ROAD_1F` into `TRAINING_GRASS` so the \u00a7Ch24 party grinds there for HOURS. A predicate that
is unreachable today because nothing stands in the cave becomes reachable the moment something does.
\u21d2 **P7 is a PREREQUISITE for that promotion, not a follow-up to it.**

\u26d4 THE METHOD IS "INSTRUMENT THE ACTION, NOT THE INPUT" \u2014 a project rule earned the hard way. A
census of call sites is a candidate list; a candidate is not a call. So this wraps the real
reachability functions, runs a REAL `train_team` grind from a fixture standing at `TRAIN_SPOT_1F`,
and records every call that actually happens, with the caller's own frame and the map the player was
standing on AT THE MOMENT OF THE CALL.

\u26d4\u26d4 THE VACUITY GUARD IS THE WHOLE DESIGN. The result I expect is "no calls from inside the cave" \u2014
which is EXACTLY what a grind that never started would also produce. \u21d2 the run is only allowed to
report a conclusion if it can first prove the grind RAN: battles fought > 0. Without that, a probe
that silently failed to drive anything would read as reassurance.

READ-ONLY on disk. It fights wild battles inside a save state and writes nothing to the repo.
"""
import collections
import pathlib as _pl
import sys
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(_ROOT / "sandbox-pokebot"))

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

from modules.map_data import MapRSE, PokemonCenter
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.story import early_game, region_reach

SAVES = _ROOT / "tools" / "story-dev" / "saves"
#: ⛔⛔ FIXTURE CHOICE IS LOAD-BEARING AND I GOT IT WRONG ONCE. `grind_stall_ppzero.ss1` is saved
#: MID-BATTLE (`game_state=BATTLE`, `controllable=False`, stable for 1200+ frames) — it is the
#: zero-PP STALL fixture. `train_team` is an OVERWORLD entry point, so it waited forever and the
#: run raised "Cutscene did not end after 8000 frames". The harness can drive that fixture because
#: the harness fights battles; a bare `next(gen)` loop cannot. ⇒ use an OVERWORLD fixture.
FIXTURE = "post_grind_L60.ss1"
VR_MAPS = {tuple(MapRSE.VICTORY_ROAD_1F.value), tuple(MapRSE.VICTORY_ROAD_B1F.value),
           tuple(MapRSE.VICTORY_ROAD_B2F.value)}
TRAIN_SPOT = (MapRSE.VICTORY_ROAD_1F, (15, 39))
#: Bounded. This is a correctness question, not a frequency one — a few battles is enough to
#: exercise the loop's decision points. ‼ `train_team` enforces no frame cap of its own.
#: ⚠ 6,000 IS DELIBERATE AND IS NOT A BUDGET FOR FINISHING THE JOB. At 90,000 this probe sat in a
#: single unfought battle for ~89,000 of them and learned nothing extra. The run is now only long
#: enough to DEMONSTRATE that the driver is inadequate; raising it buys nothing until the driver can
#: actually fight. ⇒ answering P7 needs a harness driver, not a bigger number here.
FRAME_BUDGET = 6_000

print("=" * 108)
print("P7: does ANY reachability call happen while the bot grinds inside Victory Road?")
print("=" * 108)

path = SAVES / FIXTURE
if not path.exists():
    raise SystemExit(f"⛔ MISSING FIXTURE: {path}")
context.emulator.load_save_state(path.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

av = get_player_avatar()
here0 = tuple(av.map_group_and_number)
print(f"  fixture   : {FIXTURE}")
print(f"  standing  : {MapRSE(here0).name} {tuple(av.local_coordinates)}")
if here0 not in VR_MAPS:
    raise SystemExit(f"⛔ fixture is not inside Victory Road (it is on {here0}) — wrong premise")

party0 = [(m.species.name, m.level) for m in get_party()]
print(f"  party     : {', '.join(f'{n} L{l}' for n, l in party0)}")
target = max(l for _n, l in party0) + 2
print(f"  target    : L{target}  (max+2, so the loop keeps grinding for the whole budget)")

# --- the instrumentation ------------------------------------------------------------------------
CALLS = []


def _where():
    """The first frame OUTSIDE region_reach and outside this probe — i.e. the real caller."""
    for fr in traceback.extract_stack()[::-1]:
        f = fr.filename.replace("\\", "/")
        if "region_reach" in f or "probe_p7_reach" in f:
            continue
        short = "/".join(f.rsplit("/", 3)[-3:])
        return f"{short}:{fr.lineno} in {fr.name}()"
    return "<unknown>"


def _wrap(name):
    original = getattr(region_reach, name)

    def wrapper(*a, **kw):
        result = original(*a, **kw)
        try:
            here = tuple(get_player_avatar().map_group_and_number)
        except Exception:  # noqa: BLE001 - a failed read is still a recorded call
            here = None
        CALLS.append({"fn": name, "caller": _where(), "map": here,
                      "inside_vr": here in VR_MAPS,
                      "arg": getattr(a[0], "name", str(a[0])) if a else None,
                      "result": (len(result) if isinstance(result, (set, dict)) else result)})
        return result

    setattr(region_reach, name, wrapper)


for _fn in ("is_map_reachable", "reachable_maps", "reachable_map_distances", "why_unreachable"):
    _wrap(_fn)
print(f"  wrapped   : is_map_reachable, reachable_maps, reachable_map_distances, why_unreachable")
print()

# --- drive a REAL grind ---------------------------------------------------------------------------
gen = early_game.train_team(
    target, scope="whole", grass=TRAIN_SPOT, heal_center=PokemonCenter.EvergrandeCity,
)
frames = 0
yields = 0
battles = 0
stuck_in_battle = 0
in_battle = False
maps_seen = collections.Counter()
error = None
try:
    while frames < FRAME_BUDGET:
        try:
            next(gen)
        except StopIteration:
            print("  (train_team returned — target reached or loop ended)")
            break
        yields += 1
        context.emulator.run_single_frame()
        frames += 1
        if frames % 2000 == 0:
            try:
                maps_seen[tuple(get_player_avatar().map_group_and_number)] += 1
            except Exception:  # noqa: BLE001
                pass
        # ⛔ COUNT BATTLES FROM `get_game_state()`, NOT `get_battle_state()`. The first version
        # used `get_battle_state() not in (None, BattleState.OVERWORLD)` and reported `battles=0`
        # through 90,000 frames during which `get_game_state()` said BATTLE the whole time — the
        # counter was simply wrong, on top of the arm being stuck. Two instrument defects at once.
        from modules.memory import GameState, get_game_state
        now = get_game_state() == GameState.BATTLE
        if now:
            stuck_in_battle += 1
        if now and not in_battle:
            battles += 1
        in_battle = now
except Exception as exc:  # noqa: BLE001 - an exception IS a reading; report it, do not hide it
    error = f"{type(exc).__name__}: {exc}"
    print(f"  ⚠ the grind raised: {error}")

party1 = [(m.species.name, m.level) for m in get_party()]
print()
print(f"  frames={frames}  yields={yields}  battles={battles}")
print(f"  party after : {', '.join(f'{n} L{l}' for n, l in party1)}")
print(f"  maps sampled: {[MapRSE(m).name for m in maps_seen]}")
print()
print("=" * 108)

# ⛔ VACUITY GATE FIRST. "No calls" from a grind that never ran proves nothing at all.
if stuck_in_battle > frames * 0.5:
    print(f"  ⛔⛔ THE RUN SAT IN AN UNFOUGHT BATTLE FOR {stuck_in_battle} OF {frames} FRAMES.")
    print("     ⇒ THIS PROBE'S DRIVER IS INADEQUATE, AND THAT IS THE FINDING, NOT A BUG TO HIDE.")
    print("     A bare `next(gen)` loop advances `train_team` but provides NO battle handling, so")
    print("     the first wild encounter starts and nothing ever fights it. MEASURED: the spin")
    print("     found an encounter within ~1,000 frames and `get_game_state()` read BATTLE for")
    print("     every sample thereafter. ⇒ P7 CANNOT be answered this way — it needs the real")
    print("     harness (`story_harness.py` + a driver), which runs the bot's battle handling.")
    print("     ‼ Note what this probe did NOT do: report a comfortable 'no reachability calls'.")
    raise SystemExit(1)
if battles == 0:
    print("  ⛔⛔ THE GRIND NEVER FOUGHT A BATTLE, so 'no reachability calls' is VACUOUS — it is")
    print(f"     equally consistent with 'nothing consults it' and 'the loop never ran'.")
    if error:
        print(f"     The run raised: {error}")
    print("     ⇒ THIS RUN MEASURED NOTHING about P7.")
    raise SystemExit(1)
print(f"  ✅ THE GRIND RAN: {battles} wild battle(s) fought ⇒ the loop reached its decision points,")
print(f"     so an absence of calls below is a REAL absence.")
print()

inside = [c for c in CALLS if c["inside_vr"]]
outside = [c for c in CALLS if not c["inside_vr"]]
print(f"  reachability calls TOTAL          : {len(CALLS)}")
print(f"  ... made while INSIDE Victory Road: {len(inside)}")
print(f"  ... made while elsewhere          : {len(outside)}")
print()

if not inside:
    print("  ✅✅ P7 CONFIRMED BY MEASUREMENT, NOT BY CENSUS: across a real grind inside the cave,")
    print("     NOTHING consulted reachability. The `None -> ROUTE121` delta the A/B measured has no")
    print("     live caller on this path ⇒ the waterfall fix changes no behaviour here.")
else:
    print("  ⛔⛔ P7 IS REFUTED — reachability IS consulted from inside Victory Road:")
    by_caller = collections.Counter(c["caller"] for c in inside)
    for caller, n in by_caller.most_common():
        sample = next(c for c in inside if c["caller"] == caller)
        print(f"     {n:>4}x  {caller}")
        print(f"            e.g. {sample['fn']}({sample['arg']}) -> {sample['result']}")
    print("     ⇒ the counter-picker delta CAN fire during a Victory Road grind. Re-open P7 and")
    print("       decide whether `#24-trainingbrackets` needs a companion guard.")

print()
print("  ‼ SCOPE, STATED: this drives `train_team` only. It does NOT exercise `_prepare_for_fight`,")
print("    a counter hunt, or a whiteout recovery — those have their own entry conditions and are")
print("    the subject of the caller census. A clean result here is evidence about THE GRIND LOOP,")
print("    not about every code path that could ever run in this cave.")
print("=" * 108)
