# -*- coding: utf-8 -*-
"""OFFLINE proof that §Ch23's leg 4 cannot fire an OCEAN CROSSING from inside the Pokémon League.

⛔⛔ THE DEFECT, and why it is worse than it sounds. §Ch23's leg 4 (`cross_to_ever_grande`) is guarded
twice, and BOTH guards read False from inside the League building:
    `inside_vr`            -> False: `VICTORY_ROAD_MAPS` is (VR1F, B1F, B2F); the League is not in it.
    `at_ever_grande_top()` -> False: it required `_on_map(EVER_GRANDE_CITY)`, and each League room is
                              its OWN map (`map_data.py:1037-1051`).
⇒ `if not inside_vr and not at_ever_grande_top():` fired, and the chapter aimed
`_navigate_riding_out(EG, EG_LANDING)` — a SURF LANDING — at a bot standing inside a building. It
cannot plan, so all three of the chapter's attempts burn and the chapter RAISES.
⇒ **one recoverable §Ch24 error became a HARD §Ch23 failure.** That is a derail AMPLIFIER: the class
of bug that turns a retryable fault into a run-ender.

⭐ WHY THE FIX IS IN THE PREDICATE, NOT THE GUARD. `at_ever_grande_top()` has exactly two call sites —
leg 4's own self-skip and the chapter's guard — and the chapter docstring REQUIRES they mirror, so
that no anti-vacuity guard can fire from the chapter path. Fixing the predicate keeps them mirrored
by construction; patching one guard would have split them.

‼ AND THE REPORT THAT SENT ME HERE HAD THE MECHANISM WRONG. An agent said the predicate returns False
"at the League door". It does NOT: `EG_LANDING = (18, 55)`, the door apron is `(18, 6)`, and
`6 <= 55` was already True — leg 4 correctly skipped there. The hole was one map further in.
⇒ C3/C4 below pin BOTH facts, so the wrong mechanism cannot be re-derived from this file.

⭐ WHAT EACH CASE PROVES:
  C1  inside SIDNEY'S ROOM -> the crossing is considered DONE (the defect case).
  C2  inside the LEAGUE 1F lobby -> same. This is where a §Ch24 derail most often leaves the bot.
  C3  ⛔ THE DOOR APRON (18,6) on EVER_GRANDE_CITY -> True, and it was ALREADY True before the fix.
      This is the case the bug report named, and it was never broken.
  C4  the VICTORY ROAD EXIT LANDING (18,28) -> True, also already True. C3+C4 together prove the
      y-threshold arm still works and the fix did not simply force True everywhere.
  C5  ⛔ THE CONTROL THAT MUST STAY FALSE — ROUTE 128, mid-ocean. If this ever returns True the
      chapter would SKIP a crossing it genuinely needs, stranding the run at sea.
  C6  ⛔ THE POKÉ CENTER IS *NOT* THE LEAGUE. `EVER_GRANDE_CITY_POKEMON_CENTER_1F` shares the
      `EVER_GRANDE_CITY_` prefix, so a `startswith` implementation would swallow it — and the map
      it would swallow is exactly the one leg 10's heal and the whiteout respawn care about.
      ‼‼ **C6 PINS THE PREFIX OBJECTION. IT DOES *NOT* ENDORSE `False` AS THE SEMANTICALLY RIGHT
      ANSWER, AND THIS DISTINCTION IS DELIBERATE** (raised by a Tier 1 reviewer, 2026-09-10).
      Standing INSIDE the Ever Grande Poké Center, the ocean crossing is unambiguously already done
      — Ever Grande is reachable only by surfing and a waterfall — so `at_ever_grande_top()`
      arguably ought to be True there too. It is False, for the SAME structural reason the League
      interior was: the PC is its own map, so `_on_map(EG)` fails and the y-arm never runs.
      ⇒ **the defect CLASS has one instance left, and it is FILED as `#24-egpc-leg4gap`, not fixed
      here**: it is pre-existing, not worsened by this change, and widening the predicate after the
      review that cleared it would ship an unreviewed behaviour change.
      ⛔ So read C6 as *"the prefix shortcut is wrong"*, NEVER as *"False is correct here"*. A probe
      that asserts current behaviour without saying which parts it ENDORSES turns a latent bug into
      a certified invariant, and the next reader has no way to tell them apart.
  C7  below the landing on EVER_GRANDE_CITY (y > 55) -> False: the y-threshold is a real test.
  C8  every map in `LEAGUE_INTERIOR_MAPS` resolves to a REAL `MapRSE` member (a wrong map name is a
      crash at runtime, and this project has shipped invented symbols twice).

‼ FAULT ARM (self-test — the reason this probe can be believed):
    POKEBOT_LEAGUELEG4_FAULT=prefix PYTHONUTF8=1 py -3.12 probe_league_leg4_guard.py
replaces the explicit map set with the CONVENIENT `startswith("EVER_GRANDE_CITY_")` implementation.
C6 must then go RED (the Poké Center is swallowed) and the script must exit 1.
⛔ That arm is chosen deliberately: it is not a strawman, it is the implementation a maintainer would
most plausibly "simplify" this into. A probe that only fails against nonsense protects nothing.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from modules.map_data import MapRSE  # noqa: E402
from modules.story import victory_road as vr  # noqa: E402

FAULT = os.environ.get("POKEBOT_LEAGUELEG4_FAULT", "").strip()

EG = MapRSE.EVER_GRANDE_CITY

#: (label, map, tile, expected at_ever_grande_top(), why it matters)
CASES = [
    ("C1  inside SIDNEY'S ROOM (a §Ch24 derail lands here)",
     MapRSE.EVER_GRANDE_CITY_SIDNEYS_ROOM, (6, 12), True),
    ("C2  inside the LEAGUE 1F lobby",
     MapRSE.EVER_GRANDE_CITY_POKEMON_LEAGUE_1F, (8, 15), True),
    ("C3  the LEAGUE DOOR APRON (18,6) — the case the bug report named, never broken",
     EG, (18, 6), True),
    ("C4  the VICTORY ROAD EXIT LANDING (18,28)",
     EG, (18, 28), True),
    ("C5  ⛔ CONTROL — mid-ocean on ROUTE 128 must stay FALSE",
     MapRSE.ROUTE128, (40, 20), False),
    # ⛔ ASSERTS CURRENT BEHAVIOUR, DOES NOT ENDORSE IT — see C6 in the docstring. `False` here is the
    # last instance of the same defect class, filed as `#24-egpc-leg4gap`.
    ("C6  ⛔ the POKÉ CENTER is NOT the League (prefix trap) — False is a KNOWN GAP, not an endorsement",
     MapRSE.EVER_GRANDE_CITY_POKEMON_CENTER_1F, (7, 8), False),
    ("C7  below the landing on EVER_GRANDE (y=60 > 55) — the y-threshold is real",
     EG, (18, 60), False),
]


#: The REAL position readers, captured before any case runs so they can be put back.
#: ‼ A probe that leaves a module monkeypatched is a trap for anything later in the same process.
#: It happens not to bite here (`run_gates.py` runs each gate as its own subprocess, and this file
#: exits immediately) — which is exactly why it would go unnoticed until the day something imports
#: it. Restored explicitly rather than relying on that.
_REAL_ON_MAP = vr._on_map          # noqa: SLF001
_REAL_HERE_TILE = vr._here_tile    # noqa: SLF001


def _install(map_enum, tile) -> None:
    """Point the module's position readers at a synthetic location."""
    vr._on_map = lambda m, _me=map_enum: m == _me          # noqa: SLF001
    vr._here_tile = lambda _t=tile: _t                      # noqa: SLF001


def _restore_readers() -> None:
    vr._on_map = _REAL_ON_MAP          # noqa: SLF001
    vr._here_tile = _REAL_HERE_TILE    # noqa: SLF001


def _faulted_inside_league() -> bool:
    """The 'obvious simplification' a maintainer would reach for — and it is wrong."""
    for m in MapRSE:
        if m.name.startswith("EVER_GRANDE_CITY_") and vr._on_map(m):  # noqa: SLF001
            return True
    return False


def _prefix_top() -> bool:
    """`at_ever_grande_top` with the PREFIX implementation swapped in for the map set."""
    if _faulted_inside_league():
        return True
    return vr._on_map(EG) and vr._here_tile()[1] <= vr.EG_LANDING[1]  # noqa: SLF001


def _nofix_top() -> bool:
    """⛔ THE PRE-FIX PREDICATE, verbatim from before 2026-09-10.

    Restored so the claim *"without this fix the bot surfs from inside the League"* is an ARM and not
    a sentence. `08-MISTAKES.md`/CLAUDE.md rule 8: the only currency this project accepts for
    "without X the bug survives" is a run with X removed.
    """
    return vr._on_map(EG) and vr._here_tile()[1] <= vr.EG_LANDING[1]  # noqa: SLF001


def main() -> int:
    print("=" * 100)
    print("§Ch23 LEG 4 — the ocean crossing must not fire from inside the Pokémon League")
    if FAULT:
        _want = "C1+C2" if FAULT == "nofix" else "C6"
        print(f"  ⛔ FAULT ARM ACTIVE: {FAULT!r} — {_want} MUST go RED")
    print("=" * 100)

    real_inside = vr.inside_league
    real_top = vr.at_ever_grande_top
    if FAULT == "prefix":
        vr.inside_league = _faulted_inside_league
        vr.at_ever_grande_top = _prefix_top
    elif FAULT == "nofix":
        vr.at_ever_grande_top = _nofix_top

    failures: list[str] = []

    # C8 first — a bad map name makes every other case meaningless.
    bad = [m for m in vr.LEAGUE_INTERIOR_MAPS if not isinstance(m, MapRSE)]
    ok8 = not bad
    print(f"  [{'OK  ' if ok8 else 'FAIL'}] C8  all {len(vr.LEAGUE_INTERIOR_MAPS)} LEAGUE_INTERIOR_MAPS "
          f"are real MapRSE members")
    if not ok8:
        failures.append("C8")
        print(f"         ⛔ not MapRSE: {bad}")

    for label, map_enum, tile, want in CASES:
        _install(map_enum, tile)
        got = vr.at_ever_grande_top()
        ok = got == want
        if not ok:
            failures.append(label.split()[0])
        print(f"  [{'OK  ' if ok else 'FAIL'}] {label}")
        print(f"         at_ever_grande_top() = {got}  (expected {want})   [{map_enum.name} {tile}]")

    vr.inside_league = real_inside
    vr.at_ever_grande_top = real_top
    _restore_readers()

    print("\n" + "=" * 100)
    if FAULT == "nofix":
        need = {"C1", "C2"}
        reproduced = need & set(failures)
        if reproduced == need:
            print("  FAULT ARM OK — C1 and C2 went RED with the PRE-FIX predicate restored.")
            print("  ⇒ the fix is LOAD-BEARING: without it, leg 4 fires an ocean crossing from")
            print("    inside Sidney's room and the League lobby. Not a claim — an arm.")
            print(f"  ‼ And C3-C7 stayed GREEN ({sorted(set(failures) - need) or 'no others red'}),")
            print("    which is the half that matters: the bug was ONLY the League interior, so the")
            print("    'it returns False at the League door' report was wrong about the mechanism.")
            return 1
        print(f"  ⛔ FAULT ARM DID NOT REPRODUCE — expected C1+C2 red, got {sorted(failures)}.")
        return 1

    if FAULT:
        if "C6" in failures:
            print("  FAULT ARM OK — C6 went RED: the `startswith` simplification swallows the Poké Center.")
            print("  ⇒ the EXPLICIT map set is load-bearing, not stylistic.")
            return 1
        print("  ⛔ FAULT ARM DID NOT REACH THE CODE — C6 stayed green under the prefix implementation.")
        print("     This probe cannot be trusted.")
        return 1

    if failures:
        print(f"  ⛔ FAIL — {len(failures)} case(s) red: {failures}")
        return 1
    print(f"  PASS — all {len(CASES) + 1} cases. Leg 4 self-skips inside the League, and the")
    print("  y-threshold and the Poké Center exclusion both still work.")
    print("  ‼ This proves the PREDICATE. It does not prove the chapter drives correctly from the")
    print("    League — that needs a live §Ch24 derail, which does not exist yet.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
