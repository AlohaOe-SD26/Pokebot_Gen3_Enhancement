"""Regression test for KI-52: when the lead cannot battle, the bot must FIGHT IT OUT rather than
stop dead inside a battle. NO EMULATOR — the decision ladder is read out of the source.

WHAT WENT WRONG (measured 2026-08-11, twice, byte-identically). Driving the Magma Hideout, a wild
**Torkoal** ground the lead down and the bot stopped with FIVE HEALTHY POKÉMON ON THE BENCH:

    Bot stopped: Your Pokémon cannot battle due to HP below threshold, and escape is not possible.
    party=['Sceptile L46 10/128', 'Zigzagoon 24/24', 'Swellow 112/112',
           'Skitty 45/45', 'Mightyena 127/127', 'Castform 100/100']

It then sat in Manual, **mid-battle**, for 18,000+ frames.

‼ THE POLICY ONLY EVER ASKED ABOUT THE LEAD. `lead_cannot_battle_action` defaults to `flee`
(upstream) and asks "can the LEAD fight?", never "can ANYONE fight?". When flee turned out to be
impossible there was no third option, so it raised — inside built story content.

‼ WHY A RAISE IS THE WORST OF THE THREE OUTCOMES. A LOST battle is recoverable — this project
already has whiteout recovery. A bot frozen INSIDE a battle is not recoverable by anything: the
derail riders ride SCRIPTS, and a battle is not a script.

THE USER'S DIRECTIVE (2026-08-11): "maybe we add a fallback for it to simply carry out the fight
until it wins/loses so it does not get wedged/stuck".

‼ AND THE FALLBACK MUST NOT BECOME AN UNBOUNDED LOOP (the KI-34 shape that burned 23.9M frames).
It does not: `_fight_on` returns ONE action for ONE turn, exactly like every other branch. The
bound is the battle, which always ends in a win, a loss or an escape.

THE GEN 3 TRAPPING SET, decomp-verified against `pret/pokeemerald` (`src/battle_util.c`
`TryRunFromBattle`; `src/battle_script_commands.c` `Cmd_jumpifcantswitch`) — both switching AND
fleeing are blocked by:
  * STATUS2_ESCAPE_PREVENTION — `EFFECT_MEAN_LOOK`: **Mean Look, Block, Spider Web**
  * STATUS2_WRAPPED — **Wrap, Bind, Fire Spin, Clamp, Whirlpool, Sand Tomb**
  * STATUS3_ROOTED — **Ingrain** (traps the USER)
  * abilities: **Shadow Tag** (all), **Arena Trap** (not Flying / not Levitate), **Magnet Pull**
    (Steel only)
Guaranteed ESCAPE: the **Run Away** ability, or a held **Smoke Ball**.

MESSAGES the game prints (`src/battle_message.c`, exact strings), so a log is readable:
    "{MON} prevents\\nescape with {ABILITY}!"   <- a trapping ABILITY
    "Can't escape!"                             <- a failed run attempt
    "{MON} can't escape!"                       <- attacker trapped
    "{MON} can't\\nescape now!"                 <- target just trapped

‼ SUCTION CUPS IS DELIBERATELY NOT IN THE TRAPPING SET. It prevents being FORCED out (Roar /
Whirlwind), not voluntary switching or running — and `get_best_escape_method` already models that
correctly by refusing to use Roar against a Suction Cups holder. **UNVERIFIED**: its Gen 3
implementation was not located in the decomp during this pass, so that is the working model, not
a decomp-confirmed fact.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_lead_cannot_battle.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BUILD = os.environ.get("REPRO_BUILD", "sandbox").strip().lower()
if BUILD not in ("sandbox", "custom"):
    raise SystemExit(f"REPRO_BUILD must be 'sandbox' or 'custom', got {BUILD!r}")
SRC = REPO / f"{BUILD}-pokebot" / "modules" / "battle_strategies" / "default.py"
print(f"(build: {BUILD} -> {SRC.relative_to(REPO)})")

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


if not SRC.exists():
    raise SystemExit(f"repro cannot run: missing {SRC}")
src = SRC.read_text(encoding="utf-8")


def body_of(name: str) -> str:
    # ‼ THE TERMINATOR MUST INCLUDE END-OF-FILE. The first draft ended the match only at the next
    # `def`, so the LAST method in the file extracted as "" — and an empty body then passed the
    # "no unguarded raise" check trivially while failing "can be located". A structural test whose
    # extraction can silently return nothing reports a green fix as broken and vice versa.
    m = re.search(rf"\n    def {name}\(.*?(?=\n    (?:@staticmethod\n    )?def |\Z)", src, re.S)
    return m.group(0) if m else ""


def raises_in(body: str) -> list[str]:
    """Actual `raise` STATEMENTS — not the word 'raises' in a docstring.

    ‼ The first draft tested `"raise" not in body`, and `_fight_on`'s own docstring says "Never
    raises." So the test failed on the very sentence promising the behaviour it was checking.
    Match the statement, not the substring.
    """
    return [ln.strip() for ln in body.splitlines() if re.match(r"\s*raise\s+\w", ln)]


print("1. the three handlers this test reasons about exist")
for fn in ("_handle_lead_cannot_battle", "_handle_flee", "_handle_rotate", "_fight_on"):
    check(f"{fn} can be located", bool(body_of(fn)))

print("2. THE FIX: not one of the three paths can end the run by default")

# ‼ Every remaining `raise BotModeError` in these handlers MUST be guarded by the legacy switch.
# A bare raise is the bug. Checking "no raise at all" would be wrong too — the OLD arm has to
# stay reproducible on demand.
for fn in ("_handle_lead_cannot_battle", "_handle_flee", "_handle_rotate"):
    b = body_of(fn)
    raises = [r for r in raises_in(b) if "BotModeError" in r]
    # Walk the body and confirm each raise sits under an `if legacy` guard.
    guarded = True
    seen_legacy = False
    for ln in b.splitlines():
        if re.match(r"\s*if legacy\b", ln):
            seen_legacy = True
        elif "raise BotModeError" in ln and not seen_legacy:
            guarded = False
        elif ln.strip() and not ln.strip().startswith(("#", '"')) and "raise" not in ln and seen_legacy:
            # any statement at or below the guard's level ends its scope for our purposes
            if not ln.startswith("                "):
                seen_legacy = False
    check(
        f"{fn} has no UNGUARDED raise",
        guarded,
        f"{len(raises)} raise(s), all behind `if legacy`" if guarded else "a bare raise remains",
    )
    check(f"{fn} falls back to fighting", "_fight_on(" in b or "rotate_lead(" in b)

print("3. ORDER: rotate (keep fighting healthy) -> flee (leave cheaply) -> fight on (never freeze)")

flee = body_of("_handle_flee")
rot_at, fight_at = flee.find("rotate_lead("), flee.find("_fight_on(")
check("_handle_flee prefers a healthy rotation before fighting on", 0 <= rot_at < fight_at)
check(
    "a TRAINER battle no longer raises — it rotates or fights",
    "is_trainer_battle" in flee and "_fight_on(" in flee,
    "gyms, rivals and bosses can NEVER be fled; that is normal, not an error",
)

print("4. the fallback cannot itself wedge")

fo = body_of("_fight_on")
check("_fight_on never raises", raises_in(fo) == [], f"found: {raises_in(fo)}")
check(
    "_fight_on always returns an executable action",
    "TurnAction.use_move(" in fo and re.search(r"if move is None:\s*\n\s*move = 0", fo) is not None,
    "an unrankable move table must not become a wedge; the game substitutes Struggle",
)
check(
    "_fight_on returns ONE action, it does not loop",
    not re.search(r"^\s*(while|for)\s", fo, re.M),
    "a loop here would recreate the KI-34 shape this fix exists to avoid",
)
check("_fight_on is logged so a batch can count it", "debug_logger" in fo and "KI-52" in fo)

print("5. the OLD arm is still reproducible, and the fix is the DEFAULT")

m = re.search(r'_os\.environ\.get\("POKEBOT_LEADCANTBATTLE_A", "(\d)"\) == "1"', src)
check("the legacy switch exists", m is not None)
check("…and defaults to OFF", m is not None and m.group(1) == "0")

print("6. the trapping model is present AND its names actually resolve")

reason = body_of("_escape_block_reason")
check("_escape_block_reason exists", bool(reason))
for token in ("EscapePrevention", "Wrapped", "Rooted"):
    check(f"it recognises the {token} temporary status", token in reason)
for ability in ("Shadow Tag", "Arena Trap", "Magnet Pull"):
    check(f"it recognises the {ability} ability", ability in reason)
check(
    "Mean Look / Block / Spider Web are named for the reader",
    "Mean Look" in reason and "Block" in reason and "Spider Web" in reason,
)
check(
    "the partial-trapping moves are named",
    all(mv in reason for mv in ("Wrap", "Bind", "Fire Spin", "Clamp", "Whirlpool", "Sand Tomb")),
)
check("Ingrain is named", "Ingrain" in reason)
check(
    "the game's own 'can't escape' strings are recorded for log-reading",
    "prevents" in reason and "Can't escape!" in reason,
)
check(
    "Suction Cups is explicitly EXCLUDED and flagged unverified",
    "Suction Cups" in reason and "UNVERIFIED" in reason,
    "it blocks FORCED switches only; asserting more than was verified is how this project gets burned",
)

# ‼ THE SILENT-NameError TRAP. `_escape_block_reason` calls `get_ability_by_name` inside a
# `try/except: continue`. If the import were missing, every ability lookup would raise NameError,
# be swallowed, and the function would confidently report "no trap found" for a Shadow Tag.
check(
    "get_ability_by_name is IMPORTED (or the ability branch is silently dead)",
    re.search(r"^from modules\.pokemon import .*get_ability_by_name", src, re.M) is not None,
    "a guard that cannot tell 'no' from 'I broke' is worse than no guard",
)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
