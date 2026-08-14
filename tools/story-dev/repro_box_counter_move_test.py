"""REPRO + GATE — the BOX-side counter test must accept a MOVE answer, not only a TYPE match.

‼‼ THIS IS THE BUG THE USER WATCHED ON 2026-08-14, AND THE FIX WAS ALREADY WRITTEN — ON THE OTHER
HALF OF THE PAIR. `party_counter_slot` was taught on 2026-08-08 that a mon which merely LEARNS a
counter-type move is a successful catch (`#24-slugmaspin`; its docstring names Slugma and Winona
explicitly and cites batch `20260808-131334`). Its box-side twin `box_counter_pid` was NOT, and its
docstring still asserts "Same TYPE-not-moves test as the party version" as though that were correct.

THE OBSERVED RUN (user, live): a Winona counter-hunt caught **Slugma into the PC box** (the party
was full — a Nincada had evolved and SPAWNED a Shedinja into the last slot, so the catch overflowed
to storage), and then:
  * `box_counter_pid` returned None, because Slugma's own type is FIRE and Winona needs
    Rock/Ice/Dragon/Electric — the Rock Throw it was hunted FOR is invisible to a type-only test;
  * so `hunt()` reported "found nothing", `_hunted_counter_pids` was never populated, and the
    heal's withdraw block (`higher_level_actions.py:246`, `if _pids:`) had nothing to do;
  * so the ladder raised, the run dropped to Manual, and on continue the boss was re-fought with
    the counter still sitting in the box.
Every symptom follows from this one function.

WHAT THIS PROVES, AND HOW. Fault-injected A/B on the SAME fabricated storage, no emulator,
in milliseconds:
  * ARM A (the OLD rule — type only): must return None for the Slugma fixture. If it does NOT,
    this repro is not reproducing the bug and its PASS would be meaningless.
  * ARM B (the SHIPPED code): must return the Slugma's PID.
  * NEGATIVE CONTROL: a mon with neither a needed type NOR a needed damaging move must return None
    under BOTH arms — otherwise "the fix" is just "accept everything", which would make the hunt
    claim success on any catch at all.
  * STATUS-MOVE CONTROL: a mon whose only needed-type move has `base_power == 0` must NOT count.
    The party twin is explicit that a status move answers nothing.

AND THE PARITY GATE, which is the durable half. The two success tests are a PAIR over the same
question, they have already drifted once, and prose did not catch it. This asserts they agree on
every fixture — so the next author who teaches one and forgets the other fails here instead of in
a batch six weeks later.

Exit 0 = all checks pass. Exit 1 = a check failed (details printed).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_box_counter_move_test.py
"""

import argparse
import pathlib
import sys

#: ‼ BUILD-AWARE ON PURPOSE (added 2026-08-14, during the promotion this gate's fix was part of).
#: The gate originally hard-coded `sandbox-pokebot`, which meant that after a PROMOTION **nothing
#: verified the fix had actually landed in `custom-pokebot`** — the promoted tree could regress or
#: be copied incompletely and every gate would still read green. That is precisely the
#: "a chain of correct parts with one link missing" shape `repro_hm_slot_wiring.py` exists for.
#: `run_gates.py` runs the default (sandbox); `--build custom` is the promotion check.
_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / f"{_ARGS.build}-pokebot"))

BAR = "=" * 96

#: Winona's real needed set, derived in production by `_boss_plan_is_hopeless` from the type chart
#: against her aces ("Dragon", "Flying") — `story_mode.py:3536`, `:1600-1607`.
WINONA_NEEDED = {"Rock", "Ice", "Dragon", "Electric"}


class FakeType:
    def __init__(self, name):
        self.name = name


class FakeMove:
    def __init__(self, name, type_name, base_power):
        self.name = name
        self.type = FakeType(type_name)
        self.base_power = base_power


class FakeLearnedMove:
    def __init__(self, move):
        self.move = move


class FakeSpecies:
    def __init__(self, name, type_names):
        self.name = name
        self.types = [FakeType(t) for t in type_names]


class FakeMon:
    """Only the attributes the two counter tests actually read."""

    def __init__(self, name, type_names, moves, pid, is_egg=False):
        self.species = FakeSpecies(name, type_names)
        self.moves = [FakeLearnedMove(m) for m in moves]
        self.personality_value = pid
        self.is_egg = is_egg


class FakeSlot:
    def __init__(self, pokemon):
        self.pokemon = pokemon


class FakeBox:
    def __init__(self, mons):
        self.slots = [FakeSlot(m) for m in mons]


class FakeStorage:
    def __init__(self, mons):
        # ‼ `boxes` is a PROPERTY on the real class, not a method — the production bug that hid
        # `withdrawing = 0` for multiple batches was calling it. Mirroring it as a plain attribute
        # keeps this fixture honest about the access shape.
        self.boxes = [FakeBox(mons)]
        self.pokemon_count = len(mons)


# --- the fixtures -----------------------------------------------------------------------------
ROCK_THROW = FakeMove("Rock Throw", "Rock", 50)
EMBER = FakeMove("Ember", "Fire", 40)
#: A needed TYPE on a zero-power move — the status-move control.
SAND_ATTACK_ROCK = FakeMove("Fake Rock Status", "Rock", 0)

SLUGMA_PID = 0x11111111
DUD_PID = 0x22222222
STATUS_PID = 0x33333333
TYPEMATCH_PID = 0x44444444

#: The real case: FIRE type, hunted for its ROCK move. This is what the user's run caught.
SLUGMA = FakeMon("Slugma", ["Fire"], [ROCK_THROW, EMBER], SLUGMA_PID)
#: Neither a needed type nor a needed damaging move.
DUD = FakeMon("Zigzagoon", ["Normal"], [EMBER], DUD_PID)
#: Needed type on a 0-power move only.
STATUS_ONLY = FakeMon("StatusMon", ["Normal"], [SAND_ATTACK_ROCK], STATUS_PID)
#: A plain TYPE match — must work under BOTH arms (it always did).
TYPEMATCH = FakeMon("Nosepass", ["Rock"], [EMBER], TYPEMATCH_PID)


def _install_storage(mons):
    """Point `modules.pokemon_storage.get_pokemon_storage` at a fabricated PC.

    `box_counter_pid` imports the symbol INSIDE the function body, so patching the module
    attribute is enough and no import-order trickery is needed."""
    import modules.pokemon_storage as storage_mod

    storage_mod.get_pokemon_storage = lambda: FakeStorage(mons)


def _install_party(mons):
    """Same trick for the PARTY twin, so the parity gate can put both tests on one fixture."""
    import modules.pokemon_party as party_mod

    party_mod.get_party = lambda: list(mons)


def _old_rule_box(mons, needed):
    """ARM A — the type-only test exactly as `box_counter_pid` shipped before this fix.

    ‼ Reproduced here rather than reached by reverting the file, so the A/B is a single run and
    cannot drift out of sync with a stash."""
    for mon in mons:
        if mon is None or mon.is_egg:
            continue
        if {str(t.name) for t in mon.species.types} & needed:
            return mon.personality_value
    return None


def main() -> int:
    failures = []

    def check(label, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        print(f"  {status}  {label}{('  — ' + detail) if detail else ''}")
        if not condition:
            failures.append(label)

    print(BAR)
    print("REPRO — the box-side counter test must accept a MOVE answer (the 2026-08-14 Slugma bug)")
    print(f"BUILD UNDER TEST: {_ARGS.build}-pokebot")
    print(BAR)
    # ‼ Prove we imported the fork we CLAIM to be testing. Without this the `--build custom` run
    # could silently exercise sandbox (a stale sys.path entry, a leftover import) and report a
    # promotion verified that never happened — an instrument that cannot see what it is pointed at
    # is this project's most-logged failure family.
    import modules.story.counter_hunt as _ch

    if f"{_ARGS.build}-pokebot" not in str(pathlib.Path(_ch.__file__).resolve()):
        print(f"  FAIL  imported counter_hunt from {_ch.__file__} — NOT the {_ARGS.build} build")
        return 1
    print(f"  (importing from {pathlib.Path(_ch.__file__).resolve().parents[3].name}"
          f"/{_ARGS.build}-pokebot — verified)")

    from modules.story.counter_hunt import box_counter_pid, party_counter_slot

    print("\n1 — ARM A: the OLD type-only rule MUST fail to see the Slugma (positive control)")
    print("    If this passes, the repro is not reproducing the bug and the run below means nothing.")
    arm_a = _old_rule_box([SLUGMA], WINONA_NEEDED)
    check("ARM A returns None for a FIRE Slugma that knows Rock Throw",
          arm_a is None, f"got {arm_a!r}")

    print("\n2 — ARM B: the SHIPPED code must return the Slugma's PID")
    _install_storage([SLUGMA])
    arm_b = box_counter_pid(WINONA_NEEDED)
    check("box_counter_pid finds the move answer",
          arm_b == SLUGMA_PID, f"got {arm_b!r}, expected {SLUGMA_PID:#010x}")

    print("\n3 — NEGATIVE CONTROL: a mon with no answer at all must still be refused")
    _install_storage([DUD])
    dud = box_counter_pid(WINONA_NEEDED)
    check("box_counter_pid returns None for an unrelated mon", dud is None, f"got {dud!r}")

    print("\n4 — STATUS-MOVE CONTROL: a needed TYPE on a 0-power move answers nothing")
    _install_storage([STATUS_ONLY])
    status = box_counter_pid(WINONA_NEEDED)
    check("box_counter_pid refuses a 0-power move of a needed type",
          status is None, f"got {status!r}")

    print("\n5 — the plain TYPE match must keep working (no regression on the old behaviour)")
    _install_storage([TYPEMATCH])
    type_hit = box_counter_pid(WINONA_NEEDED)
    check("box_counter_pid still accepts a type match",
          type_hit == TYPEMATCH_PID, f"got {type_hit!r}")

    print("\n6 — exclude_pids must still be honoured (the hunt's before-snapshot fence)")
    _install_storage([SLUGMA])
    excluded = box_counter_pid(WINONA_NEEDED, exclude_pids=frozenset({SLUGMA_PID}))
    check("a pre-existing boxed mon is not claimed as this hunt's catch",
          excluded is None, f"got {excluded!r}")

    print("\n" + BAR)
    print("7 — THE PARITY GATE: the party and box tests must agree on every fixture")
    print("    They are a PAIR over the same question, they DRIFTED ONCE (2026-08-08 taught the")
    print("    party half and left this one behind), and prose did not catch it.")
    print(BAR)
    for mon, expect in ((SLUGMA, True), (DUD, False), (STATUS_ONLY, False), (TYPEMATCH, True)):
        _install_party([mon])
        _install_storage([mon])
        party_answer = party_counter_slot(WINONA_NEEDED) is not None
        box_answer = box_counter_pid(WINONA_NEEDED) is not None
        check(f"{mon.species.name}: party={party_answer} box={box_answer} (expected {expect})",
              party_answer == box_answer == expect)

    print("\n" + BAR)
    print("8 — `catch_confirmed`: a COUNT is the trigger, an IDENTITY is the verdict")
    print("    A Nincada evolving SPAWNS a Shedinja into a free slot (no catch, no ball, no bot")
    print("    action), so a bare count delta reports a catch that never happened.")
    print(BAR)
    from modules.story.counter_hunt import catch_confirmed

    NINJASK_PID = 0xAAAA0001
    SHEDINJA_PID = NINJASK_PID   # ‼ decomp-verified: CopyMon does NOT overwrite personality
    CAUGHT_PID = 0xBBBB0002
    before_party = {NINJASK_PID, 0xCCCC0003}

    def _args(**over):
        base = dict(party_count_now=2, party_count_before=2,
                    party_pids_now=lambda: set(before_party), before_party_pids=before_party,
                    box_count_now=0, box_count_before=0,
                    box_pids_now=lambda: frozenset(), before_box_pids=frozenset())
        base.update(over)
        return base

    # (c) the Shedinja case — count rises, NO new identity
    check("SHEDINJA SPAWN: count 2->3 with no new PID does NOT confirm a catch",
          catch_confirmed(**_args(party_count_now=3,
                                  party_pids_now=lambda: before_party | {SHEDINJA_PID})) is False)
    # (a) a genuine catch into the party
    check("REAL PARTY CATCH: count 2->3 with a NEW PID confirms",
          catch_confirmed(**_args(party_count_now=3,
                                  party_pids_now=lambda: before_party | {CAUGHT_PID})) is True)
    # (b) a genuine catch into the box
    check("REAL BOX CATCH: box count 0->1 with a NEW box PID confirms",
          catch_confirmed(**_args(box_count_now=1,
                                  box_pids_now=lambda: frozenset({CAUGHT_PID}))) is True)
    # (d) an in-place evolution that does not change the count
    check("IN-PLACE EVOLUTION: no count change does NOT confirm",
          catch_confirmed(**_args()) is False)
    # unreadable box snapshot must never fake a catch
    check("UNREADABLE BOX SNAPSHOT (-1) cannot confirm",
          catch_confirmed(**_args(box_count_before=-1, box_count_now=1,
                                  box_pids_now=lambda: frozenset({CAUGHT_PID}))) is False)
    # (e) count going DOWN (a faint/deposit) must not confirm
    check("COUNT DECREASE does NOT confirm",
          catch_confirmed(**_args(party_count_now=1)) is False)
    # (f) an unreadable party read degrades to "keep hunting", never to a false catch
    check("UNREADABLE PARTY read does NOT fake a catch",
          catch_confirmed(**_args(party_count_now=3, party_pids_now=set)) is False)

    print("\n  LAZINESS — the expensive reads must NOT run when the cheap count did not move.")
    print("  `_stop` is called on EVERY frame of a 120,000-frame spin; this is a perf contract,")
    print("  not a style preference.")
    calls = {"party": 0, "box": 0}

    def _counting_party():
        calls["party"] += 1
        return set(before_party)

    def _counting_box():
        calls["box"] += 1
        return frozenset()

    catch_confirmed(**_args(party_pids_now=_counting_party, box_pids_now=_counting_box))
    check("no count movement => ZERO expensive reads",
          calls == {"party": 0, "box": 0}, f"got {calls}")
    catch_confirmed(**_args(party_count_now=3, party_pids_now=_counting_party,
                            box_pids_now=_counting_box))
    check("party count moved => the PARTY read runs, the BOX read still does not",
          calls == {"party": 1, "box": 0}, f"got {calls}")

    print("\n" + BAR)
    if failures:
        print(f"FAILED {len(failures)} check(s): " + "; ".join(failures))
        print(BAR)
        return 1
    print("ALL CHECKS PASS — the box test accepts move answers and agrees with the party test.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
