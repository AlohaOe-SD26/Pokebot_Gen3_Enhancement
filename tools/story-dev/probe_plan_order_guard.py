# -*- coding: utf-8 -*-
"""`#24-planorder` — does `apply_moveset_plan` REFUSE the §Ch24 prep plans applied in the wrong order?

⛔⛔ THE DEFECT THIS GUARDS, AND WHY EVERY EXISTING CHECK MISSED IT.
`TRAVEL_PLAN` teaches **Fly** to Swellow over **Wing Attack**, and its stated reason is that Wing
Attack is *"strictly dominated by the Aerial Ace Swellow already knows"*. That is true only **after**
`MOVESET_PLAN` has replaced **Peck** with **Facade**. Apply the two the other way round and Swellow
still has **Peck — 35 BP, the worst move on the team** — so the teach destroys **Wing Attack (60 BP)**
and KEEPS Peck.

‼‼ AND `apply_moveset_plan` WOULD HAVE REPORTED SUCCESS. Its four existing refusals all pass: the
species is in the party, the doomed move IS known, the item IS in the bag, and the post-teach
verification confirms Fly was learned and Wing Attack lost. ⇒ **a silent wrong-slot teach** — the
exact failure the function exists to prevent (`KI-88`: two drives burned single-use TMs over the
wrong move), arrived at through a door it had no check on.

⭐ IT IS LATENT, NOT LIVE — WHICH IS THE ARGUMENT FOR A GUARD RATHER THAN A COMMENT. The §Ch24
lineage happens to have been built in the right order: `post_ch24ready.ss1`'s Swellow reads
`Facade, Fly, Aerial Ace, Quick Attack`. Nothing shipped is broken. The next lineage to run prep
from scratch is the one that pays, and by then the reasoning above will be a year old.

‼ THE ARMS ARE TWO REAL PINNED FIXTURES, NOT SYNTHETIC STATE — the failing input already exists:
  * FAILING ARM  `post_training.ss1`  — pre-prep. Swellow: `Peck, Wing Attack, Aerial Ace, Quick
    Attack`. `TRAVEL_PLAN` here MUST be refused, naming the outstanding `Peck -> Facade` change.
  * CONTROL      `post_moveset.ss1`   — `MOVESET_PLAN` applied, Fly NOT yet taught. Swellow:
    `Facade, Wing Attack, Aerial Ace, Quick Attack`. `TRAVEL_PLAN` here MUST be ACCEPTED and must
    plan exactly Swellow: Fly over Wing Attack.
⛔ THE CONTROL IS NOT OPTIONAL AND IT IS NOT THE OBVIOUS ONE. `post_ch24ready.ss1` would be the
tempting control, but its Swellow ALREADY KNOWS FLY, so the plan is skipped for an unrelated reason
and the run would pass without the guard ever being evaluated — a green light that measures nothing.
`post_moveset.ss1` is the only fixture where the guard must actively decide "this order is fine".

⛔ THE ACTUATOR IS STUBBED, DELIBERATELY. `teach_move_from_bag` is replaced with a recording no-op
generator so the REAL plan-building and refusal logic runs against the REAL saves without pressing a
single button. What is under test is the decision, not the menu driving — and a probe that actually
taught would consume HM/TM state and could not be re-run.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_plan_order_guard.py
Exit 0 only if BOTH arms behave as stated; 1 otherwise — a guard that fires on everything is as
useless as one that fires on nothing.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]

#: ⛔⛔ BUILD-AWARE ON PURPOSE — `--build custom` IS HOW A PROMOTION IS VERIFIED HERE.
#: `promote.py` says it out loud every time: *"a gate that only ever imports sandbox cannot see
#: whether the fix landed here"*, and *"A COPY IS NOT EVIDENCE"*. A byte-identical copy proves the
#: bytes moved; it does not prove the promoted tree BEHAVES. So this A/B can be pointed at either
#: fork, and the promotion of `#24-planorder` was accepted only after BOTH returned exit 0.
BUILD = "sandbox"
if "--build" in sys.argv:
    BUILD = sys.argv[sys.argv.index("--build") + 1]
if BUILD not in ("sandbox", "custom"):
    raise SystemExit(f"--build must be 'sandbox' or 'custom', not {BUILD!r}")
sys.path.insert(0, str(REPO / f"{BUILD}-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
# ⛔ UNTHROTTLED, OR THE SUITE PAYS FOR IT AT 1x REAL TIME — enforced by
# `probe_gate_unthrottled.py`, which caught this file missing the line.
context.emulation_speed = 0

from modules.modes import BotModeError
from modules.pokemon_party import get_party
from modules.story import pokemon_league as PL

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 100


def _stub_teach(item, party_index, move_index_to_replace):
    """Record the teach that WOULD have happened; press nothing."""
    _stub_teach.calls.append((item.name, party_index, move_index_to_replace))
    return
    yield  # noqa: unreachable — makes this a generator, which is what the caller yields from


_stub_teach.calls = []


def run_plan(save_name: str, plan, label: str):
    """Load `save_name` and run `apply_moveset_plan(plan)` with the actuator stubbed."""
    save = SAVES / save_name
    if not save.is_file():
        return None, f"no such save: {save_name}", []
    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    swellow = next((m for m in get_party()
                    if m is not None and getattr(m, "species", None)
                    and m.species.name == "Swellow"), None)
    moves = ([m.move.name for m in swellow.moves if m is not None and m.move is not None]
             if swellow is not None else [])
    print(f"\n  {label}  ({save_name})")
    print(f"      Swellow: {moves}")

    _stub_teach.calls = []
    real = PL.teach_move_from_bag
    PL.teach_move_from_bag = _stub_teach
    report, refusal = {"readings": set()}, None
    try:
        for _ in PL.apply_moveset_plan(report, plan=plan):
            pass
    except BotModeError as error:
        refusal = str(error)
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash the report
        refusal = f"UNEXPECTED {type(error).__name__}: {error}"
    finally:
        PL.teach_move_from_bag = real
    return report, refusal, list(_stub_teach.calls)


def main() -> int:
    print(BAR)
    print(f"  #24-planorder — is TRAVEL_PLAN refused when MOVESET_PLAN has not run yet?"
          f"   [build={BUILD}]")
    print(BAR)

    # ---- FAILING ARM ---------------------------------------------------------------------------
    report_a, refusal_a, calls_a = run_plan("post_training.ss1", PL.TRAVEL_PLAN,
                                            "FAILING ARM — prep has NOT run")
    refused = refusal_a is not None and "OUT OF ORDER" in (refusal_a or "")
    print(f"      refused: {refused}")
    if refusal_a:
        print(f"      message: {refusal_a[:300]}")
    print(f"      teaches that would have fired: {calls_a}")
    arm_ok = refused and not calls_a
    print(f"      ⇒ {'PASS' if arm_ok else 'FAIL'} — must refuse, naming the outstanding change, "
          f"and must teach NOTHING")

    # ---- CONTROL -------------------------------------------------------------------------------
    report_b, refusal_b, calls_b = run_plan("post_moveset.ss1", PL.TRAVEL_PLAN,
                                            "CONTROL — MOVESET_PLAN already applied")
    todo = (report_b or {}).get("plan_todo", [])
    print(f"      refusal: {refusal_b}")
    print(f"      plan_todo: {todo}")
    print(f"      teaches that would have fired: {calls_b}")
    # ⛔ THE ASSERTION IS "THE **ORDER GUARD** DID NOT FIRE", NOT "nothing raised" — and the
    # difference was caught by running it. With the actuator stubbed, Swellow never actually
    # learns Fly, so `apply_moveset_plan`'s OWN post-teach verification correctly raises
    # "taught Fly ... and it does NOT know it". ⭐ That raise is the function grading its
    # CONSEQUENCE rather than trusting that the helper returned — i.e. the arm incidentally
    # proves a second guard works. Asserting `refusal is None` would have scored a correct
    # subject as a failure. ‼ Read the failing line before touching the thing under test.
    order_fired = "OUT OF ORDER" in (refusal_b or "")
    ctrl_ok = (not order_fired) and any(t[0] == "Swellow" for t in todo)
    print(f"      order guard fired here: {order_fired}   (must be False)")
    print(f"      ⇒ {'PASS' if ctrl_ok else 'FAIL'} — the ORDER guard must NOT fire, and the "
          f"plan must contain Swellow's Fly.")
    print("        (The raise above is the POST-TEACH check catching the stub — correct "
          "behaviour, and not an order refusal.)")
    print("      ‼ This arm is what makes the other one mean something. Without it, a guard that")
    print("        refused EVERY input would look identical to a correct one.")

    print(f"\n{BAR}")
    if arm_ok and ctrl_ok:
        print("  ✅ THE ORDER GUARD SEPARATES: it refuses the wrong order and passes the right one.")
        print(BAR)
        return 0
    print("  ⛔ THE ORDER GUARD DID NOT SEPARATE — do not trust it.")
    print(BAR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
