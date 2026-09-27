# -*- coding: utf-8 -*-
"""⛔ GATE: the §Ch24 run-latch must settle §Ch23, clear between runs, and gate BOTH halves.

‼‼ WHY THE LATCH EXISTS. `ch23_chapter_done()` is `FLAG ∧ POSITION ∧ BAG`
(`modules/story/victory_road.py:3315-3322`): it requires `_on_map(EVER_GRANDE)` **and** that we are
not on any Victory Road floor. **§Ch24 breaks the position conjunct BY DESIGN** — its training leg
flies to ROUTE117 within seconds, and later grinds INSIDE Victory Road, which trips the other half
of the same line. ⇒ without a latch, every run after training starts finds §Ch23 "unfinished",
re-runs `do_victory_road_chapter()`, and `_guard` then **stops the bot with a diagnostic**.
`victory_road.py:3308-3313` predicted this and called it a forward dependency.

WHAT THIS ASSERTS — four arms, each a distinct way a plausible implementation goes wrong:
  A. SETTLES. Latch set ⇒ `_ch23_settled()` is True even when `ch23_chapter_done()` is False.
  B. ⭐ CLEARS BETWEEN RUNS, AND THIS IS THE ARM WITH A BODY COUNT. The latch MUST be reset in
     `reset_per_run_state()` and NOT in `__init__`. `StoryEndlessResetMode.run()` loops on the SAME
     mode object, so `__init__` runs once per BATCH — a latch set there would make run 2 of an
     overnight batch believe §Ch24 had already started and **skip §Ch23 entirely**. That is the
     exact shape of the `_rival_attempts` bug documented at `story_mode.py:1849-1872`, which
     **killed 16 of 20 P1 runs, 6 of 9 P2, 5 of 8 P3**.
  C. INERT WHEN UNSET. Latch clear ⇒ `_ch23_settled()` is exactly `ch23_chapter_done()`. A latch
     that changed behaviour before anything set it would silently skip §Ch23 for every existing run.
  D. ⛔ BOTH HALVES GATED. `_guard` is ASSERT-not-skip (`story_mode.py:3981` returns on success,
     `:3991` raises), so making only the SKIP latch-aware would move the failure one line down
     instead of fixing it. This arm reads the source and fails if `_guard` is still handed the bare
     predicate.

FAULT ARM: `POKEBOT_CH24OWNS_FAULT=init` simulates the fatal mistake — a latch that is set once and
never cleared. ⇒ it must go RED on **every arm that depends on the latch being clearable** (B, and
C too, since 'inert when unset' has no unset state under this fault) while the SOURCE-reading arms
(D1-D4) stay green.
‼ The grading is deliberately structural rather than a list of expected failures: a fault breaks
EVERY arm depending on the invariant it destroys, and enumerating them by hand is what this
session got wrong twice.

NO EMULATOR: arms A-C exercise the latch logic directly and arm D is a source read, so this runs in
milliseconds. ‼ Arms A/C model `_ch23_settled` rather than importing it (it is a closure inside
`_play`, not reachable from outside) — which is WHY arm D exists: it checks the REAL source still
matches the model, so the model cannot drift into a comforting fiction.
"""
import os
import pathlib as _pl
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(__file__).resolve().parents[2]
_BUILD = ("custom" if "--build" in sys.argv
          and sys.argv[sys.argv.index("--build") + 1] == "custom" else "sandbox")
SRC = _ROOT / f"{_BUILD}-pokebot" / "plugins" / "custom_modes" / "story_mode.py"

BAR = "=" * 100
print(BAR)
print(f"GATE: the §Ch24 run-latch settles §Ch23, clears between runs, gates BOTH halves"
      f"   [build={_BUILD}]")
print(BAR)

_FAULT = os.environ.get("POKEBOT_CH24OWNS_FAULT", "").strip()
if _FAULT:
    print(f"  ⚠ FAULT ARM ACTIVE: {_FAULT!r}")

text = SRC.read_text(encoding="utf-8")
failures = []


class _FakeMode:
    """The latch's lifetime, modelled. ⛔ Arm D checks this model against the real source."""

    def __init__(self):
        # ‼ THE FAULT INJECTION IS HERE ON PURPOSE: `init` reproduces a latch that is set once per
        # OBJECT rather than once per RUN — i.e. assigned in `__init__` and never cleared.
        self._ch24_owns_run = (_FAULT == "init")
        self.reset_per_run_state()

    def reset_per_run_state(self):
        if _FAULT != "init":
            self._ch24_owns_run = False

    def mark_ch24_owns_run(self):
        self._ch24_owns_run = True

    def settled(self, ch23_done: bool) -> bool:
        return self._ch24_owns_run or ch23_done


def _check(label, got, want, why):
    if got == want:
        print(f"  ✅ {label:<7} {got!s:<5} (expected {want})")
    else:
        print(f"  ⛔ {label:<7} {got!s:<5} (expected {want}) — {why}")
        failures.append(f"{label}: got {got}, expected {want}. {why}")


# ---- ARM A: the latch settles Ch23 even when its own predicate says no ------------------------
m = _FakeMode()
m.mark_ch24_owns_run()
_check("ARM A", m.settled(ch23_done=False), True,
       "with §Ch24 owning the run, §Ch23 must be settled even though its position test fails — "
       "that failure is what training CAUSES, by flying away and by entering Victory Road.")

# ---- ARM B: it must CLEAR between runs -------------------------------------------------------
m.reset_per_run_state()
_check("ARM B", m.settled(ch23_done=False), False,
       "a latch that survives a run makes run 2 of an ENDLESS batch skip §Ch23 entirely. This is "
       "the `_rival_attempts` shape (story_mode.py:1849-1872) that killed 16 of 20 P1 runs.")

# ---- ARM C: inert when unset ------------------------------------------------------------------
fresh = _FakeMode()
ok_c = (fresh.settled(ch23_done=True) is True) and (fresh.settled(ch23_done=False) is False)
_check("ARM C", ok_c, True,
       "with the latch clear, `_ch23_settled()` must be EXACTLY `ch23_chapter_done()`; anything "
       "else changes behaviour for every run that never reaches §Ch24.")

# ---- ARM D: the REAL source must gate both halves ---------------------------------------------
# ⛔ THIS IS THE ARM THAT KEEPS THE MODEL HONEST. Arms A-C exercise a fake; only this one reads
# what actually ships.
skip_ok = re.search(r"if not _ch23_settled\(\):", text) is not None
guard_ok = re.search(r'_guard\(\s*"Victory Road \(Ch23\)",\s*_ch23_settled\s*\)', text) is not None
bare_guard = re.search(r'_guard\(\s*"Victory Road \(Ch23\)",\s*ch23_chapter_done\s*\)', text)
reset_ok = False
mm = re.search(r"def reset_per_run_state\(self\)(?:.|\n)*?\n    def ", text)
if mm:
    reset_ok = "_ch24_owns_run = False" in mm.group(0)
init_bad = re.search(r"def __init__\(self\)(?:.|\n)*?\n    def ", text)
init_sets = bool(init_bad and "_ch24_owns_run = True" in init_bad.group(0))

_check("ARM D1", skip_ok, True, "the SKIP half must call `_ch23_settled()`, not the bare predicate.")
_check("ARM D2", guard_ok and bare_guard is None, True,
       "the `_guard` half must ALSO use `_ch23_settled()`. `_guard` is assert-not-skip, so a bare "
       "predicate there moves the failure one line down instead of fixing it.")
_check("ARM D3", reset_ok, True,
       "`_ch24_owns_run = False` must appear inside `reset_per_run_state()` — that is the ONLY "
       "place with per-RUN lifetime.")
_check("ARM D4", init_sets, False,
       "`__init__` must NOT set the latch True: it runs once per BATCH, not once per run.")

print()
if _FAULT:
    # ⛔⛔ HOW TO GRADE A FAULT ARM, CORRECTED AFTER GETTING IT WRONG TWICE IN ONE SESSION.
    # My first version demanded that EXACTLY arm B go red. But the injected fault makes the latch
    # permanently True, and arm C tests "inert when UNSET" — under this fault there IS no unset
    # state, so C must fail too. It is a CONSEQUENCE of the fault, not a broken harness.
    # ‼ THE GENERAL RULE, because enumerating expected failures is what keeps going wrong:
    # A FAULT BREAKS EVERY ARM THAT DEPENDS ON THE INVARIANT IT DESTROYS. Listing them by hand
    # requires reasoning about dependencies at exactly the moment one is not reasoning carefully.
    # ⇒ grade on TWO structural questions instead, neither of which needs that list:
    #     (1) did the gate DETECT anything at all?            — else it cannot see its own bug
    #     (2) did the INDEPENDENT arms survive?               — the D* arms read the shipping
    #         SOURCE and share nothing with the injected model, so a fault in the model must not
    #         touch them. If they moved, the harness is what broke.
    model_failed = [f for f in failures if not f.startswith("ARM D")]
    source_failed = [f for f in failures if f.startswith("ARM D")]
    if source_failed:
        print("  ⛔⛔ THE FAULT REACHED THE SOURCE-READING ARMS — the harness is at fault, not the")
        print("     subject. D* read the shipping file and share nothing with the injected model.")
        for f in source_failed:
            print(f"     • {f}")
        print(BAR)
        raise SystemExit(1)
    if model_failed:
        names = ", ".join(sorted({f.split(":")[0] for f in model_failed}))
        print(f"  ✅ FAULT ARM BEHAVED — {names} went red (every arm depending on 'the latch can be")
        print("     unset'), and all source-reading arms stayed green. Exiting 1 as designed.")
        print(BAR)
        raise SystemExit(1)
    print("  ⛔⛔ FAULT ARM DID NOT FIRE — this gate CANNOT SEE the bug it exists to catch.")
    print(BAR)
    raise SystemExit(1)

if failures:
    print("⛔ FAIL:")
    for f in failures:
        print(f"  • {f}")
    print(BAR)
    raise SystemExit(1)

print("  ✅ PASS — the latch settles §Ch23, clears between runs, is inert unset, and BOTH")
print("     dispatch halves are gated in the shipping source.")
print(BAR)
