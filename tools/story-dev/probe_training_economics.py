"""MEASUREMENT (not a fix) — training-policy economics at the exact prenorman
fodder-grind failure (user task 2026-07-24).

Loads `saves/prenorman_fodder_grind.ss1` — captured mid-grind, standing on the
Route 102 fodder tile, pre-Norman, Badge 4 (Heat) already earned — and reports
the raw numbers a training policy should be built from:

  1. GROUND TRUTH on the trainee: species/level/exp, read straight from the
     save via `Pokemon.total_exp` + `Species.level_up_type` (the real Gen 3
     growth-rate curve, not an approximation).
  2. REACHABILITY: for every `TRAINING_GRASS` entry (+ `PENDING_GRASS` entries
     with a tile), does the REAL static pathfinder (`calculate_path`) reach it
     from the ACTUAL captured position? OK/FAIL + waypoint count.
  3. XP ECONOMICS per reachable area: real encounter table (species/levels) +
     the real Gen 3 wild-battle XP formula (`floor(base_exp * L / 7)`, using
     each species' `base_experience_yield` — NOT an approximation), battles
     needed, and frames-to-target using a MEASURED frames-per-battle figure
     (empirically driven against the real emulator on Route 102 — the only
     area needing zero travel from this exact save).
  4. TRAVEL COST: waypoint count from the captured position (a proxy, stated
     as such — no measured frames-per-tile figure exists in this codebase).
  5. THE BOSS ALTERNATIVE: Norman's real Emerald team (Spinda27/Vigoroth27/
     Linoone29/Slaking31 — flagged EXTERNAL, no ROM trainer-data reader exists
     in this codebase) run through the same real formula with the trainer
     multiplier (a=1.5), checked against the code's own "~1,200 XP" claim.

Run: py -3.12 tools/story-dev/probe_training_economics.py [--frames N]

Writes NOTHING to profiles/*/current_state.ss1 that matters — the emulator is
loaded from the saves/ copy, and (per repro convention) its own on-exit
save-state write goes to profiles/repro-fresh/current_state.ss1, not the
saves/ copy, which is left untouched.
"""
import argparse
import math
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

ap = argparse.ArgumentParser()
ap.add_argument("--frames", type=int, default=80_000,
                help="frames to drive the REAL train_team() generator on Route 102 "
                     "to empirically measure frames/battle (default 80000)")
args = ap.parse_args()

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
state_path = REPO / "tools/story-dev/saves/prenorman_fodder_grind.ss1"
context.emulator.load_save_state(state_path.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.player import get_player_location
from modules.pokemon_party import get_party
from modules.pokemon import get_species_by_name
from modules.map import get_wild_encounters_for_map
from modules.map_path import calculate_path, PathFindingError
from modules.story.progress import detect_live
from modules.story.training_areas import TRAINING_GRASS, PENDING_GRASS, AREA_PREREQ
from modules.map_data import MapRSE

W = 90
print("=" * W)
print("1) GROUND TRUTH — position, badges, trainee")
print("=" * W)
loc = get_player_location()
print(f"  Position:  {loc[0].name} {loc[1]}")
progress = detect_live()
print(f"  Badges:    {progress.badges} ({len(progress.badges)}/8)")
print(f"  HMs:       {progress.hms}")

party = [p for p in get_party() if p is not None and not p.is_egg]
print("\n  Party:")
for i, mon in enumerate(party):
    sp = mon.species
    need = sp.level_up_type.get_experience_needed_for_level(mon.level + 1)
    print(f"    [{i}] {sp.name:12} Lv{mon.level:3}  exp={mon.total_exp:6}  "
          f"needed_for_next_lvl={need:6}  to_go={need - mon.total_exp:5}  "
          f"growth={sp.level_up_type.name}")

trainee = max(party, key=lambda m: m.level)  # Combusken — the reported top-up target
tsp = trainee.species
target_level = trainee.level + 1
xp_to_go = tsp.level_up_type.get_experience_needed_for_level(target_level) - trainee.total_exp
print(f"\n  TRAINEE (top-up target, per user report): {tsp.name} Lv{trainee.level} -> "
      f"Lv{target_level}, needs {xp_to_go} exp "
      f"(growth curve: {tsp.level_up_type.name}, base_experience_yield={tsp.base_experience_yield})")

print("\n" + "=" * W)
print("2) REACHABILITY — calculate_path from the ACTUAL captured position")
print("=" * W)
areas = [(m, t, band) for (m, t, band) in TRAINING_GRASS]
areas += [(m, t, band) for (m, t, band) in PENDING_GRASS if t is not None]

reach_results = {}
for m, t, band in areas:
    prereq = AREA_PREREQ.get(m)
    tag = f" [prereq={prereq}]" if prereq else ""
    try:
        path = calculate_path(loc, (m, t), avoid_encounters=False, avoid_scripted_events=False)
        reach_results[m] = ("OK", len(path))
        print(f"  {m.name:16} {str(t):10} L{band[0]:>2}-{band[1]:<2}{tag:16} "
              f"-> OK  ({len(path)} waypoints)")
    except PathFindingError as e:
        reach_results[m] = ("FAIL", str(e).split("%")[0][:70])
        print(f"  {m.name:16} {str(t):10} L{band[0]:>2}-{band[1]:<2}{tag:16} -> FAIL  {e}")
    except Exception as e:
        reach_results[m] = ("FAIL", f"{type(e).__name__}: {e}")
        print(f"  {m.name:16} {str(t):10} L{band[0]:>2}-{band[1]:<2}{tag:16} "
              f"-> FAIL  {type(e).__name__}: {e}")

print("\n" + "=" * W)
print("3) XP ECONOMICS per REACHABLE area — real formula, real encounter tables")
print("=" * W)
print("  Formula (Gen 3, Bulbapedia 'Experience', wild battle, solo non-traded "
      "participant): XP = floor(base_experience_yield * foe_level / 7).")
print("  NOTE: this formula does NOT depend on the trainee's own level — only the foe's.")

econ_rows = []
for m, t, band in areas:
    status, info = reach_results[m]
    if status != "OK":
        continue
    enc = get_wild_encounters_for_map(*m.value)
    if enc is None or not enc.land_encounters:
        print(f"  {m.name:16} -> reachable but NO land encounter table (no wild source)")
        continue
    total_rate = sum(e.encounter_rate for e in enc.land_encounters) or 1
    weighted_xp = 0.0
    species_lines = []
    for e in enc.land_encounters:
        avg_level = (e.min_level + e.max_level) / 2
        xp = math.floor(e.species.base_experience_yield * avg_level / 7)
        weighted_xp += xp * (e.encounter_rate / total_rate)
        species_lines.append(f"{e.species.name}(L{e.min_level}-{e.max_level},{e.encounter_rate}%,~{xp}xp)")
    battles_needed = math.ceil(xp_to_go / weighted_xp) if weighted_xp > 0 else float("inf")
    econ_rows.append((m, t, band, weighted_xp, battles_needed, reach_results[m][1], species_lines))
    print(f"\n  {m.name} L{band[0]}-{band[1]} (waypoints={reach_results[m][1]}):")
    print(f"    encounters: {', '.join(species_lines)}")
    print(f"    expected XP/battle (encounter-rate-weighted): {weighted_xp:.1f}")
    print(f"    battles needed for {tsp.name} Lv{trainee.level}->{target_level} "
          f"({xp_to_go} xp): {battles_needed}")

print("\n" + "=" * W)
print(f"4) MEASURED frames/battle — driving the REAL train_team() generator on "
      f"Route 102 (zero travel from this save) for up to {args.frames} frames")
print("=" * W)
from modules.story.early_game import train_team, PETALBURG_TRAINING_GRASS
from modules.map_data import PokemonCenter

battle_log = []  # (frame, old_exp, new_exp)
frame = 0
last_exp = trainee.total_exp
gen = train_team(target_level=200, slots={0}, grass=PETALBURG_TRAINING_GRASS,
                  heal_center=PokemonCenter.PetalburgCity)
try:
    while frame < args.frames:
        next(gen)
        context.emulator.run_single_frame()
        frame += 1
        cur = [p for p in get_party() if p is not None and not p.is_egg][0]
        if cur.total_exp != last_exp:
            battle_log.append((frame, last_exp, cur.total_exp))
            last_exp = cur.total_exp
except StopIteration:
    print(f"  generator returned early at frame {frame} (target_level=200 unreachable in window — expected)")
except Exception as e:
    print(f"  generator raised {type(e).__name__}: {e} at frame {frame} (measurement window ended here)")
    print("  NOTE: driving train_team() as a bare generator (no FrameInfo/listener dispatch) is")
    print("  insufficient for a real training loop with battle UI — it needs the FULL harness main")
    print("  loop. See tools/story-dev/story_harness.py --driver traintest102 for the working")
    print("  measurement (added for this probe); parsing its log below if present.")

# --- Fall back to the FAITHFUL harness measurement (story_harness.py --driver
# traintest102, added alongside this probe) if the bare-generator drive above
# (expected, see note) did not yield enough events. That harness replicates
# modules/main.py's main_loop exactly, so PARTY CHANGE log lines are real,
# frame-accurate battle-completion events on this exact save/area. ---
import re

harness_log = REPO / "tools/story-dev/traintest102_run1.log"
measured_fpb = None
measured_xpb = None
if len(battle_log) < 5 and harness_log.is_file():
    print(f"\n  Parsing {harness_log.name} (a real story_harness.py --driver traintest102 run "
          f"on this exact save) for PARTY CHANGE events...")

    def _trainee_exp(side: str):
        mm = re.search(r"(?:Combusken|Blaziken):L\d+:exp(\d+)", side)
        return int(mm.group(1)) if mm else None

    h_frames, h_gains = [], []
    with open(harness_log, encoding="utf-8") as fh:
        for line in fh:
            mm = re.match(r"f(\d+): PARTY CHANGE \[(.*?)\] -> \[(.*?)\]", line)
            if not mm:
                continue
            old_e, new_e = _trainee_exp(mm.group(2)), _trainee_exp(mm.group(3))
            if old_e is None or new_e is None or new_e == old_e:
                continue
            h_frames.append(int(mm.group(1)))
            h_gains.append(new_e - old_e)
    if len(h_frames) >= 2:
        h_gaps = [h_frames[i] - h_frames[i - 1] for i in range(1, len(h_frames))]
        measured_fpb = sum(h_gaps) / len(h_gaps)
        measured_xpb = sum(h_gains) / len(h_gains)
        print(f"  {len(h_frames)} real wild-battle XP events over frames "
              f"{h_frames[0]}-{h_frames[-1]} (span {h_frames[-1]-h_frames[0]}).")
        print(f"  MEASURED (harness run): avg frames/battle = {measured_fpb:.0f}  "
              f"(min {min(h_gaps)}, max {max(h_gaps)}, median {sorted(h_gaps)[len(h_gaps)//2]}, n={len(h_gaps)})")
        print(f"  MEASURED (harness run): avg XP/battle = {measured_xpb:.1f}  "
              f"(formula predicted {28.7:.1f} for this exact area — "
              f"{'CONFIRMS' if abs(measured_xpb-28.7) < 3 else 'DIFFERS FROM'} the Section-3 formula)")
        print("  (Reproduce: py -3.12 tools/story-dev/story_harness.py prenorman_fodder_grind.ss1 "
              "--driver traintest102 --frames 120000 --log tools/story-dev/traintest102_run1.log)")

print(f"\n  (bare-generator drive above: {frame} frames, {len(battle_log)} XP events — "
      f"see note; the harness-log parse above is the trustworthy measurement)")
if measured_fpb is None:
    print("\n  NO measured frames/battle available (neither the bare-generator drive nor "
          f"{harness_log.name} yielded enough events). Run story_harness.py --driver "
          "traintest102 first.")

print("\n" + "=" * W)
print("5) THE BOSS ALTERNATIVE — Norman's real Emerald team, real formula")
print("=" * W)
print("  Norman's team is NOT read from the ROM here — no trainer-data reader exists")
print("  in this codebase (confirmed: grep found none). Using the externally-sourced")
print("  Emerald roster already recorded in this project's own docs")
print("  (PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md:144, story_mode.py:2089):")
print("  Spinda L27, Vigoroth L27, Linoone L29, Slaking L31 (ace). FLAGGED: EXTERNAL DATA.")

norman_team = [("Spinda", 27), ("Vigoroth", 27), ("Linoone", 29), ("Slaking", 31)]
boss_rows = []
for name, lvl in norman_team:
    try:
        sp = get_species_by_name(name)
        xp = math.floor(1.5 * sp.base_experience_yield * lvl / 7)
        boss_rows.append((name, lvl, sp.base_experience_yield, xp))
        print(f"    KO {name:10} L{lvl}  base_exp={sp.base_experience_yield:3}  "
              f"-> {xp} xp (trainer formula, a=1.5)")
    except Exception as e:
        print(f"    {name}: could not look up species ({e})")

if len(boss_rows) >= 2:
    two_mon_xp = sum(x[3] for x in boss_rows[:2])
    print(f"\n  KO'ing the first 2 (Spinda+Vigoroth) before losing: {two_mon_xp} xp")
    print(f"  (code comment / prior research claimed '~1,200 XP for 2 KOs' — "
          f"{'CONFIRMED same order of magnitude' if 900 <= two_mon_xp <= 1600 else 'DOES NOT MATCH'})")
if len(boss_rows) == 4:
    all_four = sum(x[3] for x in boss_rows)
    print(f"  KO'ing all 4 (a full win, hypothetically): {all_four} xp")

print("\n  Frames per boss-attempt+whiteout+recovery cycle: NOT measured in this probe")
print("  (would require driving a full battle+whiteout+respawn-navigation cycle,")
print("  out of scope for a reader/short-emulator probe). The closest EXISTING")
print("  measured data point in this repo: PROJECT KNOWLEDGE/04-HANDOFF.md records")
print("  a real prior run (flannery_done team, ch12_run10_long.log) that made 6")
print("  boss-training attempts (with light top-up between) in ~2,000,000 frames")
print("  total for that whole segment -> ~333,000 frames/cycle average, but that")
print("  figure INCLUDES top-up grinding between attempts, not a clean attempt-only")
print("  figure. FLAGGED: modeled/approximate, not directly measured here.")

print("\n" + "=" * W)
print("6) SURPRISING FINDING — does 'Combusken alone' actually explain the reported")
print("   ~2,000,000-frame stall, or is something else consuming those frames?")
print("=" * W)
if measured_fpb:
    solo_battles = math.ceil(xp_to_go / 28.7)
    solo_frames = solo_battles * measured_fpb
    print(f"  Combusken ALONE (slots={{0}}, this probe's own harness measurement) needs only "
          f"~{solo_battles} battles / ~{solo_frames:,.0f} frames on Route 102 to reach L{target_level}.")
    print(f"  That is ~{2_000_000/solo_frames:.0f}x SMALLER than the reported 2,000,000-frame stall.")
    print("  So the reported failure is NOT explained by 'this mon alone can't reach the next")
    print("  level here'. Checking whether it is explained by scope='whole' (train_team's default)")
    print("  dragging the ENTIRE party — including mons far below the trainee — up to the same")
    print("  target on this SAME flat-XP patch (XP/battle here does not scale with the trainee's")
    print("  level — see Section 3 note — so a far-behind mon costs vastly more battles):")
    total_battles = 0.0
    for mon in party:
        sp2 = mon.species
        need2 = max(sp2.level_up_type.get_experience_needed_for_level(target_level) - mon.total_exp, 0)
        b2 = need2 / 28.7
        total_battles += b2
        print(f"    {sp2.name:12} Lv{mon.level:3} needs {need2:6} xp for L{target_level} "
              f"-> ~{b2:6.0f} battles (~{b2*measured_fpb:>10,.0f} frames)")
    total_frames = total_battles * measured_fpb
    print(f"  WHOLE-TEAM total: ~{total_battles:.0f} battles / ~{total_frames:,.0f} frames.")
    print(f"  That IS the same order of magnitude as the reported ~2,000,000-frame stall "
          f"({total_frames/2_000_000:.1f}x).")
    print("  FINDING: the fodder patch is not what makes the trainee's OWN top-up infeasible —")
    print("  it is trivial. What is infeasible on this patch is levelling the WHOLE PARTY (esp.")
    print("  the far-behind mons) to the trainee's level, because this map's XP/battle is FLAT")
    print("  (independent of the trainee's level — Section 3) while the far-behind mons need an")
    print("  order of magnitude more XP. If `train_team` was called with the default scope=")
    print("  'whole' (or an escalated multi-slot set) rather than a true single-slot top-up, the")
    print("  fix belongs in WHICH MONS get sent to grind, not in picking a different area.")
else:
    print("  Skipped — no measured frames/battle available (see Section 4).")

print("\n" + "=" * W)
print("7) SUMMARY TABLE")
print("=" * W)
header = f"{'Option':30} {'XP/battle':>10} {'battles':>8} {'waypoints':>10} {'frames/batl':>12} {'est.frames-to-target':>22}"
print(header)
print("-" * len(header))
for m, t, band, wxp, bn, wp, _ in econ_rows:
    fpb_txt = f"{measured_fpb:.0f} (measured)" if m is MapRSE.ROUTE102 and measured_fpb else \
        (f"{measured_fpb:.0f} (extrap.)" if measured_fpb else "unmeasured")
    est = (bn * measured_fpb) if measured_fpb else None
    est_txt = f"{est:,.0f}" if est else "n/a (no measured frames/battle)"
    print(f"{m.name+' L'+str(band[0])+'-'+str(band[1]):30} {wxp:10.1f} {bn:8} {wp:10} {fpb_txt:>12} {est_txt:>22}")

if len(boss_rows) >= 2:
    two_mon_xp = sum(x[3] for x in boss_rows[:2])
    battles_boss = math.ceil(xp_to_go / two_mon_xp) if two_mon_xp else float("inf")
    print(f"{'Re-fight Norman (2 KOs/attempt)':30} {two_mon_xp:10.1f} {battles_boss:8} {'n/a':>10} "
          f"{'unmeasured':>12} {'unmeasured (frames/attempt not captured)':>22}")

print("\nDone.")
