# -*- coding: utf-8 -*-
"""OFFLINE proof that the faint chooser's replacement ranking is correct (`KI-95`).

⛔⛔ WHY THIS EXISTS. `choose_new_lead_after_faint` has had THREE index-space bugs (`KI-18`, `KI-34`,
`KI-66`) and a fourth is filed (`#24-faintchooser-fourthspace`). Every one of them needed a ROM, a live
battle, and a staged faint to see. That is why they kept happening: the function was **untestable**.
`KI-95` — the ranking scored on a bare type multiplier and ignored base power — is the first one caught
by READING rather than by losing a run, and the durable fix is not the four-line metric change, it is
that `rank_replacement` is now a PURE function this file can interrogate in milliseconds.

⭐ WHAT IT PROVES, and each case names the specific way the ranker can be wrong:
  C1  the KI-95 defect itself — a 40 BP super-effective move must NOT outrank a 100 BP neutral one.
  C2  the DEFENSIVE term still decides first — the key is lexicographic, and swapping a 0-4 multiplier
      for a 0-300 damage figure must not silently re-weight it.
  C3  a ZERO estimate is honoured — the Levitate / `banned_moves` case, where a big move does nothing.
  C4  ⭐ NEVER WORSE THAN BEFORE — when every estimate fails, the ranker must reproduce the LEGACY pick
      exactly, and must say so via `estimates_ok=0`.
  C5  the control fires — an ordinary rank reports `estimates_ok > 0`.
  C6  ⛔ MIXED SUCCESS MUST NOT MIX SCALES — the regression test for a bug that was in the FIRST
      version of this very fix: the fallback was decided per candidate, so a candidate measured
      before the first successful estimate was scored 0-4 while a later one was scored in damage,
      and the sort key compared them as if commensurable. Built so the two versions DISAGREE.
  C7  the report NAMES the metric that decided, so no log reader has to infer it.

‼ FAULT ARM (self-test, and the reason this probe can be believed):
    POKEBOT_KI95_PROBE_FAULT=legacy PYTHONUTF8=1 py -3.12 probe_faint_chooser_rank.py
feeds the ranker the OLD metric as its damage function. C1 must then go RED and the script must exit 1.
A probe that passes in both arms is measuring nothing — `08-MISTAKES.md`, and the rule that a gate with
no proven failure mode teaches the reader to bypass it.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from plugins.custom_modes.story_mode import _RankingFoe, rank_replacement  # noqa: E402

FAULT = os.environ.get("POKEBOT_KI95_PROBE_FAULT", "").strip()

# --------------------------------------------------------------------------------------------------
# Stand-ins. Deliberately the SMALLEST surface `rank_replacement` touches — if this list ever has to
# grow, the ranker has stopped being pure and that is itself the finding.
# --------------------------------------------------------------------------------------------------
_CHART = {
    ("FIRE", "GRASS"): 2.0,
    ("FIRE", "BUG"): 2.0,  # lets C6 build a 4x legacy multiplier against a GRASS/BUG foe
    ("GRASS", "WATER"): 2.0,
    ("WATER", "FIRE"): 2.0,
    ("GROUND", "ELECTRIC"): 2.0,
    ("GROUND", "FLYING"): 0.0,
    ("ELECTRIC", "WATER"): 2.0,
    ("ELECTRIC", "GROUND"): 0.0,
}


class T:
    """A type. `get_effectiveness_against` is the only thing the ranker asks of one."""

    def __init__(self, name: str) -> None:
        self.name = name

    def get_effectiveness_against(self, other: "T") -> float:
        return _CHART.get((self.name, other.name), 1.0)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return self.name


FIRE, GRASS, GROUND, WATER, NORMAL, ELECTRIC, BUG = (
    T("FIRE"), T("GRASS"), T("GROUND"), T("WATER"), T("NORMAL"), T("ELECTRIC"), T("BUG")
)


class Move:
    def __init__(self, name: str, type_: T, base_power: int) -> None:
        self.name, self.type, self.base_power = name, type_, base_power


class Learned:
    def __init__(self, move: Move, pp: int = 10) -> None:
        self.move, self.pp = move, pp


class Mon:
    """A party member. `hp`/`level` are held equal across a case unless the case is ABOUT them,
    so that a difference in the verdict can only be attributed to the term under test."""

    def __init__(self, name: str, types, moves, hp: int = 50, total: int = 100, level: int = 30):
        self.name, self.moves, self.level = name, moves, level
        self.current_hp, self.total_hp = hp, total
        self.species = type("S", (), {"types": types})()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return self.name


def candidates_of(*mons):
    return [(i, m, list(m.species.types)) for i, m in enumerate(mons)]


def foes_of(*type_lists):
    return [_RankingFoe(list(types), object()) for types in type_lists]


# --------------------------------------------------------------------------------------------------
# The two damage functions: the REAL shape (power x effectiveness), and the pre-KI-95 metric.
# --------------------------------------------------------------------------------------------------
def damage_real(mon, learned, foe_battler, foe_types):
    multiplier = 1.0
    for foe_type in foe_types:
        multiplier *= learned.move.type.get_effectiveness_against(foe_type)
    return float(learned.move.base_power) * multiplier


def damage_legacy(mon, learned, foe_battler, foe_types):
    """⛔ THE PRE-KI-95 METRIC — power is ignored entirely. Used only by the fault arm."""
    multiplier = 1.0
    for foe_type in foe_types:
        multiplier *= learned.move.type.get_effectiveness_against(foe_type)
    return multiplier


def make_damage_of(foes, fn=None, always_none: bool = False, zero_for: str | None = None,
                   none_for: str | None = None):
    """Bind a damage function to this case's foes. ⭐ `_RankingFoe.battler` is opaque to the ranker,
    so the probe recovers the defending types by identity — mirroring how production passes the real
    `BattlePokemon` straight through to `calculate_move_damage_range`."""
    by_battler = {id(foe.battler): foe.types_for_ranking for foe in foes}
    chosen = fn or (damage_legacy if FAULT == "legacy" else damage_real)

    def damage_of(mon, learned, foe_battler):
        if always_none:
            return None
        if none_for is not None and learned.move.name == none_for:
            return None  # this ONE move is unmeasurable; others still are
        if zero_for is not None and learned.move.name == zero_for:
            return 0.0  # banned, or nullified by an ability
        return chosen(mon, learned, foe_battler, by_battler[id(foe_battler)])

    return damage_of


# --------------------------------------------------------------------------------------------------
RESULTS: list[tuple[str, bool, str]] = []


def check(label: str, ok: bool, detail: str) -> None:
    RESULTS.append((label, ok, detail))
    print(f"  {'PASS' if ok else 'RED '}  {label}: {detail}")


print("=" * 96)
print("KI-95 — faint-chooser replacement ranking, offline" + (f"   [FAULT={FAULT}]" if FAULT else ""))
print("=" * 96)

# ---- C1: the defect. 40 BP super-effective must not beat 100 BP neutral. --------------------------
ember, quake = Move("Ember", FIRE, 40), Move("Earthquake", GROUND, 100)
a = Mon("A/Ember-40", [NORMAL], [Learned(ember)])
b = Mon("B/Quake-100", [NORMAL], [Learned(quake)])
foes = foes_of([GRASS])
best, report = rank_replacement(candidates_of(a, b), [GRASS], foes, make_damage_of(foes))
check(
    "C1 power beats a bare multiplier",
    best == 1,
    f"picked {[a, b][best]} (want B/Quake-100 — Ember is 2x but 80 dmg, Quake is 1x but 100 dmg)",
)

# ---- C2: the defensive term still decides first. --------------------------------------------------
spark, hydro = Move("Spark", ELECTRIC, 10), Move("Hydro", WATER, 200)
c = Mon("C/Ground-immune", [GROUND], [Learned(spark)])
d = Mon("D/Water-weak", [WATER], [Learned(hydro)])
foes = foes_of([ELECTRIC])
best, _ = rank_replacement(candidates_of(c, d), [ELECTRIC], foes, make_damage_of(foes))
check(
    "C2 defence still outranks offence",
    best == 0,
    f"picked {[c, d][best]} (want C — immune to the foe's STAB, despite D hitting ~20x harder)",
)

# ---- C3: a zero estimate is honoured (Levitate / banned_moves). -----------------------------------
e = Mon("E/Quake-100-banned", [NORMAL], [Learned(quake)])
f = Mon("F/Ember-40", [NORMAL], [Learned(ember)])
foes = foes_of([GRASS])
best, _ = rank_replacement(
    candidates_of(e, f), [GRASS], foes, make_damage_of(foes, zero_for="Earthquake")
)
check(
    "C3 a 0.0 estimate is respected",
    best == 1,
    f"picked {[e, f][best]} (want F — E's big move is banned/nullified, so it deals nothing)",
)

# ---- C4: never worse than before — all estimates fail => the LEGACY pick, and it says so. ---------
foes = foes_of([GRASS])
best, report4 = rank_replacement(
    candidates_of(a, b), [GRASS], foes, make_damage_of(foes, always_none=True)
)
check(
    "C4 degrades to the legacy pick",
    best == 0 and report4["estimates_ok"] == 0,
    f"picked {[a, b][best]} with estimates_ok={report4['estimates_ok']} "
    f"(want A — the pre-KI-95 answer — and ok=0 so the degradation is VISIBLE)",
)

# ---- C5: the control fires on an ordinary rank. ---------------------------------------------------
check(
    "C5 control: estimates actually ran",
    report["estimates_ok"] > 0 and report["estimates_failed"] == 0,
    f"estimates_ok={report['estimates_ok']} estimates_failed={report['estimates_failed']}",
)

# ---- C6: MIXED SUCCESS must not mix SCALES. -------------------------------------------------------
# ⛔⛔ THE REGRESSION TEST FOR A BUG THAT WAS IN THE FIRST VERSION OF THE FIX ITSELF. `ok` was counted
# across candidates but the fallback was applied per candidate, so a candidate measured BEFORE the
# first successful estimate was scored 0-4 (a multiplier) while a later one was scored in damage —
# and the sort key compared them as though they were the same quantity.
# ⭐ THIS CASE IS BUILT SO THE TWO VERSIONS DISAGREE, which is the only thing that makes it a test:
#   A (slot 0): Ember, 4x legacy multiplier vs a GRASS/BUG foe, but its estimate is UNMEASURABLE.
#   B (slot 1): Pebble, 2 BP, 1x — measurable, and a feeble 2.0 damage.
# old code -> A is scored 4.0 (a multiplier) vs B's 2.0 (damage) and A WINS on units alone.
# new code -> one metric for the whole ranking: A is unmeasured (0.0), B is 2.0, and B WINS.
pebble = Move("Pebble", NORMAL, 2)
g = Mon("A/unmeasurable-4x", [NORMAL], [Learned(ember)])
h = Mon("B/measurable-2dmg", [NORMAL], [Learned(pebble)])
foes = foes_of([GRASS, BUG])
best, report6 = rank_replacement(
    candidates_of(g, h), [GRASS, BUG], foes, make_damage_of(foes, none_for="Ember")
)
check(
    "C6 mixed success uses ONE scale",
    best == 1 and report6["metric"] == "damage" and report6["estimates_failed"] > 0,
    f"picked {[g, h][best]} metric={report6['metric']} ok={report6['estimates_ok']} "
    f"failed={report6['estimates_failed']} (want B — A's 4x multiplier must NOT be compared "
    f"against B's damage figure)",
)

# ---- C7: the metric is NAMED, not inferred. -------------------------------------------------------
check(
    "C7 the report names its metric",
    report4["metric"] == "legacy" and report["metric"] == "damage",
    f"all-fail run reports metric={report4['metric']!r}; ordinary run reports {report['metric']!r}",
)

# --------------------------------------------------------------------------------------------------
print("-" * 96)
failed = [label for label, ok, _ in RESULTS if not ok]
if FAULT == "legacy":
    # ‼ The fault arm must break C1 and ONLY C1 — C2-C5 do not depend on the offensive metric's
    # scale, so a fault that knocks them over too would mean the probe is coupled where it claims
    # not to be, and its green arm would be worth less.
    ok = failed == ["C1 power beats a bare multiplier"]
    print(f"FAULT ARM: {'PASS' if ok else 'BROKEN'} — expected exactly C1 to go red, got {failed}")
    print("RESULT: the probe detects the KI-95 defect." if ok else "RESULT: the probe is MISCALIBRATED.")
    sys.exit(0 if ok else 1)

print(f"RESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} pass" + (f" — RED: {failed}" if failed else ""))
print("ACCEPTANCE: " + ("PASS" if not failed else "FAIL"))
sys.exit(1 if failed else 0)
