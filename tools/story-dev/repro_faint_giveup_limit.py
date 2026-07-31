"""Proof for the KI-38/KI-40 interim mitigation: `FAINT_CHOOSER_GIVEUP_LIMIT`.

WHY. The after-faint chooser fails to select a living, valid replacement (KI-38 — measured
`NO ELIGIBLE REPLACEMENT` = 0 while `GAVE UP` runs at ~22/hour, so a target always existed).
KI-34 added `FAINT_CHOOSER_GIVEUP_LIMIT = 3` to bound a genuinely unbounded re-entry. The
bound is right; 3 is far too tight, and giving up ABANDONS AN ACTIVE BATTLE — the party menu
is left open and the mode's recovery cannot answer it, so the run wedges. Measured A/B:

    21b587f1  no limit, index bug present    0.4 watchdog/h   48% of runs finished
    d7d493d8  limit 3,  index bug fixed     ~20 watchdog/h     0 of 2 finished
    ffb062ce  limit 3,  index bug fixed     ~29 watchdog/h     0 of 30 finished

WHAT THIS PROVES (pure, no emulator):
  1. The default is 20, not 3 — restoring most of the pre-fix tolerance (~35 re-entries were
     measured in one battle) while still terminating.
  2. It stays FINITE. ‼ Unbounded is not an option: KI-36 — the per-run frame budget is a
     generator wrapper that cannot fire while a battle handler sits on the flat controller
     stack, so an unbounded chooser is bounded only by `debug_logger`'s 60,000-frame stall
     net, which exists only while debug logging is ON.
  3. `POKEBOT_FAINT_GIVEUP_LIMIT` overrides it, so the number can be tuned on the machine
     that actually runs batches without a code edit and without an installer round-trip.
  4. Junk or hostile env values fall back to the default and never raise — this runs inside
     battle code, where an exception drops the bot to Manual.
  5. The limit is what the give-up path actually compares against (it is read, not shadowed).

‼ THIS TESTS A MITIGATION. The real fix is `#24-menutext`: read the party-menu TEXT so the
bot knows what the cursor is on. KI-38's evidence (`presses={'Down': 3, 'A': 273}`,
`cursors_seen=[0,2,3,7]` in a 4-mon party, 7 probably CANCEL) says the cursor MODEL is wrong,
and no number of retries fixes a wrong model.

Run: py -3.12 tools/story-dev/repro_faint_giveup_limit.py
"""
import importlib
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


def limit_with_env(value):
    """Re-read the module-level default under a given env value."""
    original = os.environ.get("POKEBOT_FAINT_GIVEUP_LIMIT")
    if value is None:
        os.environ.pop("POKEBOT_FAINT_GIVEUP_LIMIT", None)
    else:
        os.environ["POKEBOT_FAINT_GIVEUP_LIMIT"] = value
    try:
        import modules.battle_handler as bh

        return bh._faint_giveup_limit_default()
    finally:
        if original is None:
            os.environ.pop("POKEBOT_FAINT_GIVEUP_LIMIT", None)
        else:
            os.environ["POKEBOT_FAINT_GIVEUP_LIMIT"] = original


print("=" * 78)
print("CASE 1 — the default is raised, and stays finite")
print("=" * 78)
default = limit_with_env(None)
check("1. default is 20 (was 3 — too tight, see KI-40)", default == 20, str(default))
check("2. ‼ still FINITE — unbounded is unsafe while a battle handler holds the stack (KI-36)",
      isinstance(default, int) and default < 10_000, str(default))
print(f"      worst case ≈ {default} × 6,000 = {default * 6000:,} frames inside one battle "
      f"({default * 6000 / 5_000_000:.1%} of the 5M per-run budget)")

print()
print("=" * 78)
print("CASE 2 — tunable on the machine that runs batches, without a code edit")
print("=" * 78)
check("3. POKEBOT_FAINT_GIVEUP_LIMIT=35 is honoured", limit_with_env("35") == 35)
check("   POKEBOT_FAINT_GIVEUP_LIMIT=1 is honoured (minimum sane value)", limit_with_env("1") == 1)

print()
print("=" * 78)
print("CASE 3 — fail-safe: this runs inside battle code, so it must never raise")
print("=" * 78)
import modules.battle_handler as _bh_for_max

MAX = _bh_for_max.FAINT_CHOOSER_GIVEUP_MAX
for bad in ("", "abc", "-5", "0", "3.7", "٣", " 12 ", "99999999999999999999", "10000"):
    try:
        got = limit_with_env(bad)
        # ‼ The clamp is the point, not just "no exception". The first version accepted any
        # positive int, so one fat-fingered env var on the batch machine gave an effectively
        # UNBOUNDED chooser and silently reintroduced the KI-36 hazard the finite limit exists
        # to prevent. This case caught it before it shipped.
        ok = isinstance(got, int) and 1 <= got <= MAX
        check(f"4. env={bad!r} -> usable AND clamped to <= {MAX}", ok, str(got))
    except Exception as error:  # noqa: BLE001
        check(f"4. env={bad!r} -> no exception", False, repr(error))

check("‼ 4b. a huge env value is CLAMPED, not accepted (KI-36 cannot be re-opened by a typo)",
      limit_with_env("99999999999999999999") == MAX, str(limit_with_env("99999999999999999999")))

print()
print("=" * 78)
print("CASE 4 — the constant is the one the give-up path actually reads")
print("=" * 78)
import modules.battle_handler as bh

importlib.reload(bh)
source = (REPO / "sandbox-pokebot/modules/battle_handler.py").read_text(encoding="utf8")
check("5. the give-up path compares against FAINT_CHOOSER_GIVEUP_LIMIT",
      "_faint_chooser_giveups >= FAINT_CHOOSER_GIVEUP_LIMIT" in source)
check("   the module-level constant is set from the env-aware default",
      "FAINT_CHOOSER_GIVEUP_LIMIT = _faint_giveup_limit_default()" in source)
check("   and it is still exported as an int", isinstance(bh.FAINT_CHOOSER_GIVEUP_LIMIT, int),
      str(bh.FAINT_CHOOSER_GIVEUP_LIMIT))
check("‼ 6. the give-up still hands the mode a recoverable fault (never `raise`)",
      "request_mode_recovery(_reason)" in source and "raise" not in source.split(
          "_faint_chooser_giveups >= FAINT_CHOOSER_GIVEUP_LIMIT")[1][:900],
      "battle code is a SIBLING of the mode on a flat stack — a raise would drop to Manual")

print()
print("=" * 78)
print(f"RESULT: {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
for f in failures:
    print(f"  FAILED: {f}")
print("=" * 78)
sys.exit(1 if failures else 0)
