r"""GATE — a post-gym-1 Pokédex catch is not STARTED when the balls cannot afford it (USER RULING 20 Phase 0, 2026-09-26).

WHY: the fence guarded entry by ball COUNT only; a catch then threw until caught or empty. MEASURED: one Absol (catch
rate 30) took 23 balls, and the run later died with no balls for its Dive hunt. The dex bail (`probe_dexcatch_bail.py`)
stops a catch at the reserve; this stops a hopeless one from starting.

  R1  `dex_catch_expected_throws` (PURE) is Gen 3's own arithmetic (`Cmd_handleballthrow`, read from the decomp
      2026-09-26): rate 30 + Poké Ball ⇒ ~23 (the measured Absol); rate 255 + Poké Ball ⇒ ~3; a certain catch ⇒ 1; a
      better ball / higher rate never needs MORE throws.
  R2  THE FENCE: post-gym-1, above `DEX_CATCH_MAX_EXPECTED_THROWS` ⇒ refused and the reason NAMES the estimate; at the
      threshold ⇒ caught; `None` (unknown) ⇒ no effect; PRE-gym-1 ⇒ unchanged (still team building).
  R3  THE ADAPTER `_expected_throws_for`: the best ball the THROWER may use (a Great Ball ⇒ x15), NEVER the Master
      Ball, NEVER a ball outside the user's `catch_balls.yml` allowlist (the thrower's own filter — a held-but-disallowed
      Ultra Ball must not make a hopeless catch look cheap); a ball-less / unreadable bag ⇒ None.
  R4  WIRING: `_should_catch` passes `expected_throws=_expected_throws_for(species, bag)` to `decide_dex_catch`.
  R5  the skip-the-fix arm `POKEBOT_DEXCATCH_FAULT_NORATE` restores the old behaviour, is read in production and is
      registered in `29`.
  R6  PER-SPECIES VERDICT LOGGING (`dex_fence_log_line`): two species with the SAME reason ⇒ two lines (the old log
      reported only when the global reason string CHANGED — transitions, not species); the same (species, reason) ⇒
      one line per run; "already owned" / trainer battles ⇒ never; the adapter uses it and the set is per-run.
FAULT ARMS (built in): a formula without the full-HP `/ 3` (R1); a rate check that also fires PRE-gym-1 (R2); an adapter
that counts the Master Ball, and one that ignores the allowlist (R3); the old change-only logger (R6).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dexcatch_rate.py
"""
from __future__ import annotations

import io
import os
import pathlib
import sys
import tokenize
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import plugins.custom_modes.story_mode as SM  # noqa: E402

STORY = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []

BASE = dict(is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=False, party_slots_used=SM.PARTY_CAPACITY,
            battler_count=SM.PARTY_CAPACITY, party_target=4, resource_block=None,
            spare_balls=SM.DEX_CATCH_BALL_RESERVE + 5, hunt_armed=False, training=False, boxed_count=12,
            party_healthy=True, species_dex=359, owned_dex=frozenset({1, 4, 7}),
            party_dex=frozenset({1, 4, 7, 261, 183, 351}), attempts=0)


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def r1(fn, sink=None):
    absol = fn(30, 10)
    check(21 <= absol <= 25, f"R1 rate 30 + Poké Ball ⇒ ~23 expected throws (got {absol:.1f}; the measured Absol took 23)",
          sink)
    check(2.5 <= fn(255, 10) <= 3.5, f"R1 rate 255 + Poké Ball ⇒ ~3 (got {fn(255, 10):.2f})", sink)
    check(fn(255, 40) == 1.0, "R1 odds > 254 ⇒ a certain catch (1 throw)", sink)
    check(fn(45, 15) < fn(45, 10) and fn(45, 20) < fn(45, 15), "R1 a better ball never needs more throws", sink)
    check(all(fn(r + 15, 10) <= fn(r, 10) for r in range(3, 240, 15)), "R1 a higher catch rate never needs more throws",
          sink)


def r2(fence, sink=None):
    M = SM.DEX_CATCH_MAX_EXPECTED_THROWS
    catch, why = fence(**BASE, expected_throws=M + 1)
    check(catch is False and "expected throws" in why, f"R2 post-gym-1 above {M} ⇒ refused, and the reason names it "
                                                       f"({why!r})", sink)
    check(fence(**BASE, expected_throws=M)[0] is True, f"R2 exactly {M} ⇒ still caught (the boundary)", sink)
    check(fence(**BASE, expected_throws=None)[0] is True, "R2 None (unknown) ⇒ no effect — never a silent refusal", sink)
    pre = dict(BASE, pre_badge1=True, party_slots_used=2, battler_count=2)
    catch, why = fence(**pre, expected_throws=500)
    check(catch is True and "pre-gym-1" in why, f"R2 PRE-gym-1 is unchanged — still team building ({why!r})", sink)


class _Slot:
    def __init__(self, name, qty):
        self.item = types.SimpleNamespace(name=name)
        self.quantity = qty


def r3(adapter, sink=None):
    sp = types.SimpleNamespace(catch_rate=45)
    bag = types.SimpleNamespace(poke_balls=[_Slot("Poké Ball", 10), _Slot("Great Ball", 3), _Slot("Master Ball", 1)])
    check(adapter(sp, bag) == SM.dex_catch_expected_throws(45, 15),
          "R3 the best ORDINARY ball held counts (a Great Ball ⇒ x15), never the Master Ball", sink)
    check(adapter(sp, types.SimpleNamespace(poke_balls=[_Slot("Master Ball", 1)])) is None,
          "R3 only a Master Ball ⇒ None (a discretionary catch must never plan on it)", sink)
    check(adapter(None, bag) is None, "R3 an unreadable species ⇒ None", sink)
    held_ultra = types.SimpleNamespace(poke_balls=[_Slot("Poké Ball", 10), _Slot("Ultra Ball", 1)])
    check(adapter(sp, held_ultra, allowed={"Poké Ball", "Great Ball"}) == SM.dex_catch_expected_throws(45, 10),
          "R3 a held Ultra Ball OUTSIDE the allowlist is ignored — the estimate uses the ball the thrower may throw", sink)
    check(adapter(sp, held_ultra, allowed={"Premier Ball"}) is None,
          "R3 no allowed ball held ⇒ None (the fence ignores it; the thrower has nothing to throw)", sink)

    class _Broken:
        @property
        def poke_balls(self):
            raise RuntimeError("bag unreadable")

    check(adapter(sp, _Broken()) is None, "R3 an unreadable bag ⇒ None (the fence then ignores it)", sink)


def r6(fn, code, sink=None):
    logged: set = set()
    a = fn(logged, 359, "Absol", False, "only 8 spare balls — below the dex reserve of 10")
    b = fn(logged, 335, "Zangoose", False, "only 8 spare balls — below the dex reserve of 10")
    check(bool(a) and bool(b) and "Absol" in a and "Zangoose" in b,
          "R6 two species with the SAME reason ⇒ two lines, each naming its species", sink)
    check(fn(logged, 359, "Absol", False, "only 8 spare balls — below the dex reserve of 10") is None,
          "R6 the same (species, reason) ⇒ one line per run", sink)
    check(fn(logged, 359, "Absol", True, "dex catch #359 (goes to the PC box)") is not None,
          "R6 the same species with a NEW reason ⇒ logged again", sink)
    check(fn(logged, 1, "Bulbasaur", False, "#1 already owned") is None and fn(logged, None, "?", False,
                                                                                  "trainer battle") is None,
          "R6 'already owned' and trainer battles ⇒ never logged", sink)
    if code is not None:
        check("line = dex_fence_log_line(logged, dex, getattr(species, \"name\", \"?\"), catch, reason)" in code
              and "self._dex_catch_logged: set = set()" in code,
              "R6 the adapter logs through it, and the logged set is reset per run", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — a post-gym-1 Pokédex catch is not started when the balls cannot afford it")
    print("=" * 92)
    src = STORY.read_text(encoding="utf-8")
    code = _strip_comments(src)
    print("\n== R1 the formula ==")
    r1(SM.dex_catch_expected_throws)
    print("\n== R2 the fence ==")
    r2(SM.decide_dex_catch)
    print("\n== R3 the adapter ==")
    r3(SM._expected_throws_for)
    print("\n== R4 wiring ==")
    check("expected_throws=_expected_throws_for(species, bag)," in code,
          "R4 `_should_catch` passes `expected_throws=_expected_throws_for(species, bag)` to the fence")
    print("\n== R5 the skip-the-fix arm ==")
    arm = "POKEBOT_DEXCATCH_FAULT_NORATE"
    check(f'.environ.get("{arm}") != "1"' in code and f"`{arm}`" in REGISTRY.read_text(encoding="utf-8"),
          f"R5 {arm} is read in production and registered in 29")
    os.environ[arm] = "1"
    try:
        check(SM.decide_dex_catch(**BASE, expected_throws=500)[0] is True, "R5 with the arm set, the old behaviour returns")
    finally:
        os.environ.pop(arm, None)

    print("\n== R6 per-species verdict logging ==")
    r6(SM.dex_fence_log_line, code)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []

    def no_third(rate, bonus):
        from math import isqrt

        odds = rate * bonus // 10
        if odds > 254:
            return 1.0
        b = 1048560 // isqrt(isqrt(16711680 // max(odds, 1)))
        return 1.0 / min(1.0, (b / 65536) ** 4)

    r1(no_third, sink)
    check(bool(sink), f"FAULT a formula without the full-HP `/ 3` FAILS R1 ({len(sink)} caught)")
    sink = []

    def fires_pre(**kw):
        et = kw.pop("expected_throws", None)
        if et is not None and et > SM.DEX_CATCH_MAX_EXPECTED_THROWS:
            return False, f"~{et:.0f} expected throws"
        return SM.decide_dex_catch(**kw)

    r2(fires_pre, sink)
    check(bool(sink), f"FAULT a rate check that also fires PRE-gym-1 FAILS R2 ({len(sink)} caught)")
    sink = []

    def counts_master(species, bag, allowed=None):
        best = max((SM._BALL_BONUS_X10.get(s.item.name, 10) if s.item.name != "Master Ball" else 255
                    for s in bag.poke_balls), default=None)
        return None if best is None or species is None else SM.dex_catch_expected_throws(species.catch_rate, best)

    try:
        r3(counts_master, sink)
    except Exception as error:  # noqa: BLE001 - a crash is also a failure of the thing under test
        sink.append(f"raised {type(error).__name__}")
    check(bool(sink), f"FAULT an adapter that counts the Master Ball FAILS R3 ({len(sink)} caught)")
    sink = []

    def ignores_allowlist(species, bag, allowed=None):
        return SM._expected_throws_for(species, bag, allowed=set(SM._BALL_BONUS_X10) | {"Premier Ball"})

    r3(ignores_allowlist, sink)
    check(bool(sink), f"FAULT an adapter that ignores the allowlist FAILS R3 ({len(sink)} caught)")
    sink = []
    last = {"reason": ""}

    def change_only(logged, dex, name, catch, reason):
        if last["reason"] == reason:
            return None
        last["reason"] = reason
        return None if reason.endswith("already owned") else f"{'CATCH' if catch else 'skip'} — {reason}"

    r6(change_only, None, sink)
    check(bool(sink), f"FAULT the old change-only logger FAILS R6 ({len(sink)} caught)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
