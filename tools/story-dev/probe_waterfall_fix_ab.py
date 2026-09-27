# -*- coding: utf-8 -*-
"""⭐ WHAT WOULD THE `#24-waterfallcap` FIX ACTUALLY CHANGE? — an A/B measured BEFORE writing it.

WHY THIS EXISTS. `#24-waterfallcap` is a one-key fix to a SHARED production predicate
(`is_map_reachable`). The punch-list entry claims it is **safe to land on its own**, on the grounds
that no `TRAINING_GRASS` row names Victory Road, so no picker can propose it. ⛔ That is an
ARGUMENT, and this project's rule is that a claim of the form *"without X the behaviour is
unchanged"* is only worth an ARM THAT REMOVES X. So: run both arms and diff them.

⛔⛔ NOTHING IS WRITTEN TO PRODUCTION. Arm B monkeypatches `region_reach._resolve_caps` **in this
process only** — `_resolve_caps` is looked up as a module global at `:399` and `:488`, and only the
GRAPH is cached (`_get_graph`), while caps are resolved per call, so the patch takes effect without
touching the graph cache or any file. The process exits; nothing persists.

⭐ THE VACUITY GUARD IS THE POINT OF THE DESIGN, NOT A GARNISH. The result I am hoping for is
"almost nothing changed" — which is EXACTLY what a monkeypatch that silently failed to apply would
also produce. ⇒ arm B is only allowed to report anything if it can first prove it is a different
arm: the patched `_resolve_caps` must return a dict CONTAINING `"waterfall"`, and
`is_map_reachable(VICTORY_ROAD_1F)` must actually FLIP on at least one fixture. If neither holds,
the run declares itself VOID rather than reporting a comfortable "no difference".

READ-ONLY on disk: loads save states, reads memory, patches one function in RAM.
"""
import pathlib as _pl
import sys

_ROOT = _pl.Path(__file__).resolve().parents[2]
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

from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.story import region_reach
from modules.story.counter_plan import best_huntable, find_counter_candidates
from modules.story.training_areas import best_training_area, best_training_grass, hunt_ground_tile
from plugins.custom_modes.story_mode import _counter_area_allowed, _training_area_allowed

SAVES = _ROOT / "tools" / "story-dev" / "saves"
VR1F = MapRSE.VICTORY_ROAD_1F
EG = MapRSE.EVER_GRANDE_CITY

FIXTURES = ["post_ch24_atdoor_L75.ss1", "grind_stall_ppzero.ss1", "post_league_lobby.ss1"]
#: Levels spanning the range where a Victory Road row (36-40 wilds) would start to look attractive,
#: plus low ones where it must NEVER be chosen.
LEVELS = [10, 20, 30, 40, 53, 60, 75]

_ORIGINAL_RESOLVE = region_reach._resolve_caps


def _patched_resolve(can_surf, can_rock_smash, can_cut, can_strength, badges, can_waterfall=None):
    # ‼ `can_waterfall` EXISTS SO THIS STUB SURVIVES THE FIX. Once production threads the keyword
    # through, a 5-parameter stub raises TypeError -- which `reachable_maps` swallows into its
    # fail-safe empty result, so arm B silently became "0 maps reachable" and every reading
    # "changed". That reads as a dramatic delta and is really a dead arm. See the ARM-B-ALIVE check.
    """Arm B: exactly what the proposed fix does — resolve EVERY gate `_GATE_MOVE_NAMES` knows,
    instead of a hardcoded four. Deliberately written as the real fix would be, not as a stub that
    forces True: `_live_capability` must still require the move AND the badge."""
    caps = dict(_ORIGINAL_RESOLVE(can_surf, can_rock_smash, can_cut, can_strength, badges,
                                  can_waterfall=can_waterfall))
    for gate, move_name in region_reach._GATE_MOVE_NAMES.items():
        if gate not in caps:
            caps[gate] = region_reach._live_capability(move_name, badges)
    return caps


def sample(label):
    """Every reading that could plausibly change, taken identically in both arms."""
    out = {
        "reach_vr": region_reach.is_map_reachable(VR1F),
        "reach_eg": region_reach.is_map_reachable(EG),
        "n_maps": len(region_reach.reachable_maps()),
    }
    for lvl in LEVELS:
        out[f"area_none_L{lvl}"] = best_training_area(lvl, allow=None)
        out[f"grass_none_L{lvl}"] = best_training_grass(lvl, allow=None)
        out[f"area_allow_L{lvl}"] = best_training_area(lvl, allow=_training_area_allowed)
        out[f"grass_allow_L{lvl}"] = best_training_grass(lvl, allow=_training_area_allowed)
        out[f"area_counter_L{lvl}"] = best_training_area(lvl, allow=_counter_area_allowed)

    # ⭐⭐ THE CONSUMER THE 2026-07-26 GATE COMMENT WAS ACTUALLY WORRIED ABOUT.
    # That comment says Victory Road's Hariyama "ranks #1 the instant anything calls the map
    # reachable", and `hunt_ground_tile`'s docstring records the same measurement for Norman's
    # Fighting counter. `best_huntable` is the ONLY function an executor may act on, and it
    # requires `reachable AND hunt_tile is not None` — so measure BOTH the ranking and the
    # action, because they can disagree and the disagreement IS the safety margin.
    for types in (["Fighting"], ["Ghost"], ["Dark"]):
        key = "+".join(types)
        cands = find_counter_candidates(types, allow=_counter_area_allowed, max_results=5)
        out[f"cand_top_{key}"] = tuple(
            (c.get("species_name"), getattr(c.get("map_enum"), "name", None), c.get("reachable"),
             c.get("huntable")) for c in (cands or [])[:5])
        pick = best_huntable(cands)
        out[f"hunt_pick_{key}"] = (pick.get("species_name"),
                                   getattr(pick.get("map_enum"), "name", None)) if pick else None

    # Is Victory Road a legal hunting ground at all? (The whitelist that fails CLOSED.)
    out["vr_hunt_tile"] = hunt_ground_tile(VR1F)
    return out


def fmt(v):
    if isinstance(v, tuple) and len(v) == 3 and hasattr(v[0], "name"):
        return f"{v[0].name}{tuple(v[1])}{tuple(v[2])}"
    if isinstance(v, tuple) and len(v) == 2 and hasattr(v[0], "name"):
        return f"{v[0].name}{tuple(v[1])}"
    return str(v)


print("=" * 108)
print("A/B: WHAT WOULD THE WATERFALL CAP FIX CHANGE?  \u2014 arm B is an IN-PROCESS patch, nothing written")
print("=" * 108)

all_deltas = {}
flipped_anywhere = False
proved_patched = False
#: Arm C state — see the ARM C block in the loop.
armc_rows = {}
armc_lenient = {}
armc_patch_proved = False

for fixture in FIXTURES:
    path = SAVES / fixture
    print()
    print(f"\u2500\u2500\u2500 {fixture}")
    if not path.exists():
        print(f"  \u26a0 SKIPPED \u2014 no such fixture")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    avatar = get_player_avatar()
    try:
        here = MapRSE(tuple(avatar.map_group_and_number)).name
    except ValueError:
        here = str(tuple(avatar.map_group_and_number))
    print(f"  standing : {here} {tuple(avatar.local_coordinates)}")

    region_reach._resolve_caps = _ORIGINAL_RESOLVE
    arm_a = sample("A")

    region_reach._resolve_caps = _patched_resolve
    # \u26d4 PROVE THIS IS A DIFFERENT ARM BEFORE TRUSTING ANYTHING IT SAYS.
    probe_caps = region_reach._resolve_caps(None, None, None, None, None)
    if "waterfall" in probe_caps:
        proved_patched = True
    print(f"  arm B caps keys : {sorted(probe_caps)}  "
          f"{'\u2705 patch is live' if 'waterfall' in probe_caps else '\u26d4 PATCH DID NOT APPLY'}")
    print(f"  arm B waterfall resolved to : {probe_caps.get('waterfall')!r}")
    arm_b = sample("B")
    # \u2b50\u2b50 ARM C \u2014 THE COUPLING TEST. Arm B keeps `huntable` False only because
    # `hunt_ground_tile` is a WHITELIST sourced from TRAINING_GRASS, and Victory Road is not in it.
    # But `#24-trainingbrackets` proposes to ADD exactly that row. \u21d2 does adding it dissolve the
    # second guard and make Hariyama an ACTIONABLE counter-catch? Measure it; do not reason about it.
    import modules.story.training_areas as _ta
    _orig_rows = _ta.TRAINING_GRASS
    _ta.TRAINING_GRASS = tuple(_orig_rows) + ((VR1F, (15, 39), (36, 40)),)
    _applied_rows = _ta.TRAINING_GRASS
    try:
        arm_c = sample("C")
    finally:
        _ta.TRAINING_GRASS = _orig_rows          # \u203c restore before anything else reads it
        region_reach._resolve_caps = _ORIGINAL_RESOLVE
    c_delta = {k: (arm_b[k], arm_c[k]) for k in arm_b if arm_b[k] != arm_c[k]}
    armc_rows[fixture] = c_delta
    # ⛔⛔ VALIDATE THE ARM BY ITS APPLICATION, NEVER BY ITS EXPECTED EFFECT.
    # The first version of this check set `armc_patch_proved` only if `vr_hunt_tile` became
    # non-None — i.e. only if the HYPOTHESIS was true. When the hypothesis turned out FALSE the
    # probe declared itself vacuous and threw away a real finding. "Arm dead" and "arm alive,
    # hypothesis wrong" are different facts and a validity check that cannot tell them apart is
    # worthless. ⇒ prove the patch APPLIED (the row is in the table), then report the effect.
    armc_patch_proved = any(r[0] is VR1F for r in _applied_rows)
    # ⭐ And demonstrate the table WOULD have been read but for the stricter guard: ask the same
    # function with `require_driven=False`, which is the only difference between the two answers.
    _ta.TRAINING_GRASS = tuple(_orig_rows) + ((VR1F, (15, 39), (36, 40)),)
    try:
        lenient = _ta.hunt_ground_tile(VR1F, require_driven=False)
    finally:
        _ta.TRAINING_GRASS = _orig_rows
    armc_lenient[fixture] = lenient
    hunt_flips = {k: v for k, v in c_delta.items() if k.startswith("hunt_pick_")}
    print(f"  [arm C = arm B + the proposed TRAINING_GRASS row] vr_hunt_tile "
          f"{fmt(arm_b['vr_hunt_tile'])} -> {fmt(arm_c['vr_hunt_tile'])}; "
          f"{len(hunt_flips)} actionable hunt pick(s) changed")
    for k, (b, c) in sorted(hunt_flips.items()):
        print(f"      \u26d4 {k}: {fmt(b)} -> {fmt(c)}")

    region_reach._resolve_caps = _ORIGINAL_RESOLVE  # \u203c always restore, even mid-loop

    # ⛔⛔ AN ARM THAT RETURNS THE FAIL-SAFE EMPTY RESULT IS BROKEN, NOT INFORMATIVE.
    # `reachable_maps` swallows ANY exception and returns set(), so a stub whose signature has
    # drifted from production shows up as "every reading changed" -- the loudest possible output
    # for the least meaningful cause. Catch it here rather than reporting a 309->0 "finding".
    if arm_b["n_maps"] == 0 and arm_a["n_maps"] > 0:
        print("  ⛔⛔ ARM B COLLAPSED TO THE FAIL-SAFE EMPTY RESULT (n_maps=0) while arm A saw "
              f"{arm_a['n_maps']}. That is an EXCEPTION being swallowed, not a measurement -- almost "
              "certainly this stub's signature has drifted from production's `_resolve_caps`. VOID.")
        raise SystemExit(1)

    delta = {k: (arm_a[k], arm_b[k]) for k in arm_a if arm_a[k] != arm_b[k]}
    all_deltas[fixture] = delta
    if delta.get("reach_vr") == (False, True):
        flipped_anywhere = True

    if not delta:
        print("  \u2192 NO READING CHANGED.")
    else:
        print(f"  \u2192 {len(delta)} reading(s) changed:")
        for k, (a, b) in sorted(delta.items()):
            print(f"      {k:<22} A={fmt(a):<34} B={fmt(b)}")

print()
print("=" * 108)

# \u26d4 VACUITY GATE FIRST \u2014 a comfortable "nothing changed" is exactly what a dead arm produces.
if not proved_patched:
    print("  \u26d4\u26d4 THE ARM NEVER APPLIED: patched `_resolve_caps` returned no `waterfall` key. Every")
    print("     'no difference' below is VACUOUS. This run measured NOTHING.")
    raise SystemExit(1)
if not flipped_anywhere:
    print("  \u26d4\u26d4 THE ARM APPLIED BUT `is_map_reachable(VICTORY_ROAD_1F)` NEVER FLIPPED False->True on")
    print("     any fixture. The patch is not doing what the real fix would do \u21d2 this A/B cannot")
    print("     support a 'safe to land alone' conclusion. VOID.")
    raise SystemExit(1)
print("  \u2705 ARM VALIDITY PROVEN: the patch applied AND flipped the reachability it was meant to.")
print("     \u21d2 a 'no change' on any OTHER reading below is a real result, not a dead arm.")
print()

# --- the question the punch list actually rests on ----------------------------------------------
# --- ⭐⭐ THE COUNTER-HUNT QUESTION: does Victory Road become an ACTIONABLE destination? ---------
hunt_changed = {f: {k: v for k, v in d.items() if k.startswith(("cand_", "hunt_pick_", "vr_hunt"))}
                for f, d in all_deltas.items()}
hunt_changed = {f: d for f, d in hunt_changed.items() if d}
print("  ⭐⭐ THE CONSUMER THE 2026-07-26 GATE COMMENT WAS WRITTEN FOR — counter-catch candidates:")
if not hunt_changed:
    print("     ✅ NO counter-candidate ranking and NO `best_huntable` pick changed, on any fixture.")
    print("        ⇒ the second guard holds: `hunt_ground_tile` is a WHITELIST sourced from")
    print("          TRAINING_GRASS/HUNTING_GROUNDS, and Victory Road is in NEITHER — so even when")
    print("          the map becomes REACHABLE it does not become HUNTABLE. Ranking is not a gate.")
else:
    print("     ⛔⛔ IT DID CHANGE — the capability fix alters counter-catch behaviour:")
    for f, d in hunt_changed.items():
        for k, (a, b) in sorted(d.items()):
            print(f"        {f} {k}:\n          A={fmt(a)}\n          B={fmt(b)}")
print()

picker_keys = [k for d in all_deltas.values() for k in d
               if k.startswith(("area_", "grass_"))]
if picker_keys:
    print(f"  \u26d4\u26d4 A TRAINING PICKER CHANGED ITS ANSWER \u2014 THE \u201cSAFE TO LAND ALONE\u201d CLAIM IS REFUTED.")
    for fixture, delta in all_deltas.items():
        for k in sorted(delta):
            if k.startswith(("area_", "grass_")):
                a, b = delta[k]
                print(f"     {fixture} {k}: {fmt(a)} -> {fmt(b)}")
else:
    print("  \u2705\u2705 NO TRAINING PICKER CHANGED ITS ANSWER ON ANY FIXTURE OR LEVEL TESTED "
          f"({len(LEVELS)} levels x 5 predicates x {len(all_deltas)} fixtures).")
    print("     \u21d2 the \u201c`#24-waterfallcap` is safe to land ALONE\u201d claim SURVIVES a real arm, which is")
    print("       the only currency this project accepts for a 'without X, nothing changes' claim.")
    print("     \u26a0 SCOPE, STATED: this covers the training/counter pickers only. It does NOT cover")
    print("       every consumer of `is_map_reachable` \u2014 see the caller census for those.")

print()
for fixture, delta in all_deltas.items():
    reach = delta.get("reach_vr")
    n = delta.get("n_maps")
    bits = []
    if reach:
        bits.append(f"reach(VR1F) {reach[0]}->{reach[1]}")
    if n:
        bits.append(f"world {n[0]}->{n[1]} maps")
    if bits:
        print(f"  \u2b50 {fixture}: " + ", ".join(bits))

print()
print("  \u2b50\u2b50 ARM C \u2014 THE COUPLING TEST (`#24-waterfallcap` fix PLUS `#24-trainingbrackets`' row):")
if not armc_patch_proved:
    print("     ⛔ ARM C NEVER APPLIED: the row is not in the patched table. VOID.")
else:
    _flips = {f: {k: v for k, v in d.items() if k.startswith("hunt_pick_")}
              for f, d in armc_rows.items()}
    _flips = {f: d for f, d in _flips.items() if d}
    print("     ✅ ARM C APPLIED (the proposed row IS in the table for this arm).")
    _len = sorted({str(v) for v in armc_lenient.values()})
    print(f"     ⭐ THE IDENTICAL CALL WITH `require_driven=False` RETURNS: {_len}")
    if _flips:
        print("     ⛔⛔ THE ROW DISSOLVES THE GUARD — Victory Road becomes an ACTIONABLE "
              "counter-catch destination ⇒ a FOURTH REQUIREMENT for `#24-trainingbrackets`.")
        for f, d in _flips.items():
            for k, (b, c) in sorted(d.items()):
                print(f"        {f} {k}: {fmt(b)} -> {fmt(c)}")
    else:
        print("     ✅✅ MY “FOURTH REQUIREMENT” HYPOTHESIS IS REFUTED, AND THE REASON IS A "
              "STRONGER GUARD I DID NOT KNOW ABOUT: `hunt_ground_tile` defaults "
              "`require_driven=True`, and in that mode it consults `HUNTING_GROUNDS` and then "
              "RETURNS NONE — it never reads `TRAINING_GRASS` at all. ⇒ adding the row does "
              "NOT make Victory Road huntable.")
        print("     ⭐ THE CONTRAST ABOVE IS THE PROOF THE ARM WAS LIVE: the identical call at "
              "`require_driven=False` DOES return the tile, so the table really was patched and "
              "`require_driven` is what holds — not a dead arm.")
        print("     ⚠ ⇒ AND THE GUARD IS ONE ENV FLAG FROM OFF: `POKEBOT_HUNT_ANYGROUND=1` "
              "sets `require_driven=False`. That flag + the row + this cap fix WOULD send a hunt "
              "into Victory Road. Not a blocker; a thing to write down.")
print()
print("  \u203c WHAT THIS A/B DOES NOT SHOW: that the bot can WALK the opened edge, or that opening it")
print("    is FAITHFUL to the real game. It measures only what our own predicates would answer.")
print("=" * 108)
