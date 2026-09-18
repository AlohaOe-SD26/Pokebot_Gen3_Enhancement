# -*- coding: utf-8 -*-
"""READ which §Ch23 legs would fire at each position we hold a pinned fixture for.

The §Ch24 marker design rests on a claim that has only ever been TRACED, never read:
*"inside the sealed League, every one of §Ch23's eleven legs self-skips."* We hold a SEALED-map
fixture (`post_hall4_door.ss1`, HALL4), so that claim is measurable today.

⛔ THIS EVALUATES GUARDS ONLY. It never runs a leg. Every guard below is a pure position/party read
(`_on_map`, `at_*`, `party_is_healthy`), transcribed from `do_victory_road_chapter`
(`victory_road.py:3327-3485`) — the guard expressions are quoted beside each leg so a reader can check
the transcription rather than trust it.

⭐ CONTROLS ARE THE POINT. `post_ch24_atdoor` (outdoors at EVER_GRANDE) MUST fire some legs — if every
position comes back "all skip", the instrument is simply returning False and the sealed-map row means
nothing.
⚠ `inside_vr` is a CACHED local in the real dispatch (computed at :3378, before leg 4). It is
recomputed fresh here; for a single evaluation at a fixed position that is equivalent.
"""
import pathlib as _pl
import sys

sys.path.insert(0, str(_pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement") / "sandbox-pokebot"))

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

from modules.player import get_player_avatar
from modules.map_data import MapRSE
from modules.story import victory_road as VR

SAVES = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\saves")

#: (leg, the guard exactly as written in the dispatch, a callable evaluating it)
GUARDS = [
    ("1-3", "any(_on_map(m) for m in _PRE_DEPARTURE_MAPS)",
     lambda: any(VR._on_map(m) for m in VR._PRE_DEPARTURE_MAPS)),
    ("4", "not inside_vr and not at_ever_grande_top()",
     lambda: (not any(VR._on_map(m) for m in VR.VICTORY_ROAD_MAPS)) and not VR.at_ever_grande_top()),
    ("5", "not at_b1f_doorstep() and (_on_map(EG) or _on_map(VR1F))",
     lambda: (not VR.at_b1f_doorstep()) and (VR._on_map(VR.EG) or VR._on_map(VR.VR1F))),
    ("6", "_on_map(VR1F) and at_b1f_doorstep()",
     lambda: VR._on_map(VR.VR1F) and VR.at_b1f_doorstep()),
    ("7", "_on_map(B2F)", lambda: VR._on_map(VR.B2F)),
    ("8", "_on_map(B1F)", lambda: VR._on_map(VR.B1F)),
    ("9", "_on_map(VR1F)  [fault arm off]", lambda: VR._on_map(VR.VR1F)),
    ("10", "_on_map(EG) and not party_is_healthy()[0]",
     lambda: VR._on_map(VR.EG) and not VR.party_is_healthy()[0]),
    ("11", "_on_map(EG)", lambda: VR._on_map(VR.EG)),
]

CASES = [
    ("post_hall4_door.ss1", "SEALED map (HALL4) \u2014 the claim under test"),
    ("post_ch24_atdoor.ss1", "OUTDOORS at EVER_GRANDE  [CONTROL: must fire something]"),
    ("post_league_shop.ss1", "OUTDOORS, basket bought   [CONTROL]"),
]

print("=" * 116)
print("WHICH \u00a7Ch23 LEGS WOULD FIRE?  (guards evaluated, legs NEVER run)")
print("=" * 116)
summary = []
for name, note in CASES:
    p = SAVES / name
    if not p.exists():
        print(f"  {name}: MISSING")
        continue
    context.emulator.load_save_state(p.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    av = get_player_avatar()
    try:
        mname = MapRSE(tuple(av.map_group_and_number)).name
    except ValueError:
        mname = str(tuple(av.map_group_and_number))
    print(f"\n  {name}  \u2014  {mname} {tuple(av.local_coordinates)}")
    print(f"      {note}")
    fired = []
    for leg, expr, fn in GUARDS:
        try:
            v = fn()
        except Exception as e:
            v = f"ERR:{type(e).__name__}"
        mark = "\u26a0 FIRES" if v is True else ("skip  " if v is False else str(v))
        if v is True:
            fired.append(leg)
        print(f"        leg {leg:<5} {mark:<9} {expr}")
    print(f"      \u21d2 legs that would FIRE: {fired or 'NONE'}")
    summary.append((name, mname, fired))

print("\n" + "-" * 116)
sealed = next((s for s in summary if "HALL4" in s[1]), None)
ctrls = [s for s in summary if "HALL4" not in s[1]]
if sealed and ctrls:
    ctrl_ok = any(c[2] for c in ctrls)
    print(f"  CONTROL: at least one outdoor position fires a leg -> {'PASS' if ctrl_ok else 'FAIL'}")
    if not ctrl_ok:
        print("  \u26d4 INCONCLUSIVE: no position fires anything, so the sealed-map row means nothing.")
    else:
        print(f"  SEALED MAP (HALL4): legs firing = {sealed[2] or 'NONE'}")
        print("  \u21d2 " + ("\u2b50 CONFIRMED: every \u00a7Ch23 leg self-skips inside the sealed zone \u2014 READ, not traced."
                         if not sealed[2] else
                         f"\u26d4 REFUTED: leg(s) {sealed[2]} WOULD FIRE from inside the sealed zone."))
print("=" * 116)
