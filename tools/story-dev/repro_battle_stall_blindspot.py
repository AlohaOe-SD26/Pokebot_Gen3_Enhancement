"""Regression: the stall detector must be able to SEE an in-battle wedge (KI-32).

FROM REAL DATA — user log `Story_(ENDLESS_RESET)-debug-20260729-122709`.

That run was a good one: a single playthrough cleared Roxanne, Brawly, Wattson, Flannery and
Norman and reached Winona — 310 battles won. Then, inside a Fortree Gym trainer battle, a
mid-battle rotation wedged the PARTY MENU:

    f1791402 [BATTLE] started
    f1793385 [PARTY] slot0 Marshtomp:L35 -> Castform:L25    <- rotation applied
    f1793407 [PARTY] slot0 Castform:L25 -> Marshtomp:L35    <- and reverted, 22 frames later
    f1799232 [PARTY] slot0 Marshtomp:L35 -> Castform:L25    <- applied again
    f1800001 [hb] state=3 controllable=False pos=(9, 10)    <- PARTY_MENU, and then...
    ... ~280,000 frames of IDENTICAL heartbeats ...
    f2779018 [MODE] Story (ENDLESS RESET) -> Manual

**ZERO stuck dumps in that entire stretch**, so there is no generator call stack to diagnose
the wedge from — the single most useful artefact this logger produces.

Cause: stall detection did `if st.get("battle_active"): _stall_frames = 0` on every frame.
The intent was right (a battle legitimately holds still mid-turn and during the EXP fill, so a
300-frame threshold would false-trigger every turn) but the implementation made the detector
STRUCTURALLY BLIND: no in-battle wedge could ever be reported, however long it lasted.

This is the same shape as the Weather Institute hang (KI-27), where the watchdog was itself
the thing that could not fire. A guard must not share its subject's failure mode.

Fix: a battle gets a much LARGER threshold, not an exemption.

No emulator needed — this drives the real `on_frame` state machine with synthetic frames.
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

from modules import debug_logger as dl  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


def drive(frames, *, battle, changing=False):
    """Feed `frames` synthetic states through the real stall machine.

    Returns the list of dump labels produced. `changing=True` varies the signature each
    frame (a healthy battle); otherwise the state is frozen (a wedge).
    """
    dumps = []
    state = {"n": 0}

    def fake_light_state():
        state["n"] += 1
        return {"frame": state["n"], "battle_active": battle,
                "map": "FORTREE CITY(12,1)", "pos": (9, 10),
                "sig_extra": state["n"] if changing else 0}

    def fake_sig(st):
        return (st["map"], st["pos"], st["sig_extra"])

    saved = (dl._light_state, dl._progress_signature, dl._dump, dl._event, dl._enabled, dl._file)
    dl._light_state = fake_light_state
    dl._progress_signature = fake_sig
    dl._dump = lambda label, st=None: dumps.append(label)
    dl._event = lambda fc, msg: None
    dl._enabled = True
    dl._file = object()
    dl._stall_frames = 0
    dl._last_sig = None
    dl._last_dump_stall = 0
    dl._prev = None
    dl._start_frame = None
    try:
        for _ in range(frames):
            dl.on_frame()
    finally:
        (dl._light_state, dl._progress_signature, dl._dump, dl._event,
         dl._enabled, dl._file) = saved
    return dumps


OW = dl._STALL_DUMP_AFTER
BT = dl._BATTLE_STALL_DUMP_AFTER

print(f"== thresholds: overworld={OW}, in-battle={BT} ==")
check(OW == 300, f"the overworld threshold is unchanged at 300 (got {OW})")
check(BT > OW * 10,
      f"the in-battle threshold is much larger, so normal turns cannot cry wolf (got {BT})")
check(BT == 18_000, f"in-battle threshold is 18,000 frames = 5 min at 60fps (got {BT})")

print("\n== ‼ THE BUG: a frozen BATTLE used to produce NOTHING, forever ==")
dumps = drive(BT + 200, battle=True, changing=False)
check(len(dumps) >= 1,
      f"a battle frozen for {BT}+ frames now produces a stuck dump (got {len(dumps)})")
check(any("STUCK" in d for d in dumps), f"and it is a STUCK dump (got {dumps[:2]})")
print(f"     -> the real log froze for ~280,000 frames and produced 0 dumps.")

print("\n== a HEALTHY battle is not disturbed ==")
dumps = drive(50_000, battle=True, changing=True)
check(dumps == [], f"a battle whose state keeps changing never dumps (got {len(dumps)})")

print("\n== a battle quiet for a NORMAL turn/EXP-fill is not disturbed ==")
for quiet in (300, 3_000, 10_000):
    dumps = drive(quiet, battle=True, changing=False)
    check(dumps == [],
          f"{quiet} frames of in-battle quiet is below the threshold — no dump ({len(dumps)})")

print("\n== the OVERWORLD detector keeps its original sensitivity ==")
dumps = drive(OW + 10, battle=False, changing=False)
check(len(dumps) >= 1,
      f"an overworld freeze still dumps at {OW} frames (got {len(dumps)})")
dumps = drive(OW - 50, battle=False, changing=False)
check(dumps == [], "and does not dump before the threshold")

print("\n== a stalled state re-dumps periodically, so a long wedge is time-stamped ==")
dumps = drive(BT + dl._STALL_REDUMP_EVERY * 3, battle=True, changing=False)
check(len(dumps) >= 3,
      f"a long in-battle wedge re-dumps every {dl._STALL_REDUMP_EVERY} frames (got {len(dumps)})")

print("\n== the exemption is GONE from the source ==")
src = (SANDBOX / "modules" / "debug_logger.py").read_text(encoding="utf-8")
i = src.index("# --- stall detection ---")
block = src[i:i + 1400]
check("_stall_frames = 0\n        _last_sig = sig" not in block.split("if sig == _last_sig")[0],
      "there is no longer an unconditional in-battle reset before the comparison")
check("threshold = _BATTLE_STALL_DUMP_AFTER if in_battle else _STALL_DUMP_AFTER" in block,
      "the battle case selects a THRESHOLD rather than exempting itself")
check("never flag a stall while one is active" not in src,
      "the old comment asserting the exemption is removed (it would now contradict the code)")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
