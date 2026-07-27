"""Regression: training must not leave the WEAKEST battler leading.

FROM REAL DATA — user batch `20260726-201838`, lane P2 (Mudkip). **19 losses and 44
whiteouts**, every one of them at the SAME tile, ROUTE 110 (34,56), with an identical
party each time:

    f799201 [hb] ... map=ROUTE 110(0,25) pos=(34, 56)
             party=['Dustox:L13', 'Nincada:L12', 'Marshtomp:L21', 'Poochyena:L11']
    f799353 [BATTLE] ended (outcome=BattleOutcome.Lost)
    f799474 [MAP] ROUTE 110(0,25) -> SLATEPORT CITY(0,1)      <- whiteout, respawn
    ... walk back, identical rotation, identical loss, forever.

`train_team` rotates the LOWEST-level trainee into slot 0 so it shares XP (swap-training),
and never put the good mon back — so the bot left the grind with **Dustox L13 leading while
its L21 starter sat in slot 2** and opened every trainer ambush with it.

Survival mode cannot cover this: it is scoped to WILD battles because a trainer battle
cannot be fled. The fix is `_lead_strongest_battler()` at the end of `train_team`.

No emulator needed — this drives the generator against a fake party/rotation layer.
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

from modules.story import early_game  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class Mon:
    def __init__(self, name, level):
        self.name, self.level, self.is_egg = name, level, False


# P2's actual party at the moment of every loss.
PARTY = [Mon("Dustox", 13), Mon("Nincada", 12), Mon("Marshtomp", 21), Mon("Poochyena", 11)]
rotations = []


def fake_rotate(target_slot, attempts=3):
    """Mimic change_lead_party_pokemon: swap slot 0 with target_slot."""
    rotations.append(target_slot)
    PARTY[0], PARTY[target_slot] = PARTY[target_slot], PARTY[0]
    return
    yield  # make it a generator


early_game.get_party = lambda: list(PARTY)
early_game._battler_slots = lambda: list(range(len(PARTY)))
early_game._rotate_lead_safely = fake_rotate

print("== the situation from the logs: weakest mon leading after a grind ==")
check(PARTY[0].name == "Dustox" and PARTY[0].level == 13, "lead starts as Dustox L13")
check(max(m.level for m in PARTY) == 21, "the party's best is Marshtomp L21 in slot 2")

print("\n== _lead_strongest_battler puts the best mon back in front ==")
list(early_game._lead_strongest_battler())
check(PARTY[0].name == "Marshtomp", f"lead is now Marshtomp (got {PARTY[0].name})")
check(PARTY[0].level == 21, f"lead level is 21 (got {PARTY[0].level})")
check(rotations == [2], f"it rotated slot 2 exactly once (got {rotations})")

print("\n== it is a no-op when the best mon already leads (no pointless menu churn) ==")
rotations.clear()
list(early_game._lead_strongest_battler())
check(rotations == [], "no rotation issued when the lead is already strongest")
check(PARTY[0].name == "Marshtomp", "and the lead is unchanged")

print("\n== an empty / egg-only party does not raise ==")
saved = early_game._battler_slots
early_game._battler_slots = lambda: []
try:
    list(early_game._lead_strongest_battler())
    check(True, "no battlers -> returns quietly")
except Exception as exc:  # noqa: BLE001
    check(False, f"raised {type(exc).__name__}: {exc}")
early_game._battler_slots = saved

print("\n== ‼ train_team RESTORES the lead before returning ==")
# Assert against the SOURCE, because driving the whole generator would need an emulator.
# The property that matters: the restore is inside `train_team`, after its loop, and
# BEFORE the `finally` (a yield inside finally raises if the generator is being closed).
src = (SANDBOX / "modules" / "story" / "early_game.py").read_text(encoding="utf-8")
start = src.index("def train_team(")
end = src.index("\ndef ", start + 10)
body = src[start:end]
check("_lead_strongest_battler()" in body, "train_team calls _lead_strongest_battler")
i_restore = body.index("yield from _lead_strongest_battler()")
i_finally = body.index("\n    finally:")
check(i_restore < i_finally, "the restore happens BEFORE the finally block")
i_loop = body.index("while True:")
check(i_loop < i_restore, "and AFTER the training loop, not inside it")
check("set_swap_train(False)" in body[i_finally:], "the finally still clears the swap-train flag")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
