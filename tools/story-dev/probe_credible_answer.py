"""RAW, LIVE check of `_boss_plan_is_hopeless`'s "no-answer" test (KI-23) against a real
captured save. Read-only.

‼ WHY THIS EXISTS. KI-23 needs a fixture save whose PARTY has NO credible super-effective
answer to Winona's ace (Altaria L33, Dragon/Flying). This probe does not re-derive or
approximate that rule — it copies it VERBATIM from `plugins/custom_modes/story_mode.py`'s
`_boss_plan_is_hopeless` (the "no-answer test" block, ~lines 1573-1596) and drives it against
a live save's real party, using production's own type chart
(`modules.pokemon.get_type_by_name` / `Type.get_effectiveness_against`) and production's own
`_battler_slots()` (`modules/story/early_game.py`) to decide which party members even count.
No matchup table is hardcoded here.

Boots the emulator exactly like `probe_box_contents.py` (same profile, same
`LibmgbaEmulator`, same `load_save_state` + frame-advance idiom).

⛔⛔ **IT IS A COPY OF THE PREDICATE, NOT A CALL INTO IT — AND THAT IS A REAL LIMITATION, STATED
RATHER THAN HIDDEN.** This project has been burned by exactly this shape before
(`repro_box_counter_move_test` fault-injected by RE-CODING type-only against fakes, so the REAL
hook could have rotted unnoticed). It is a copy here because `_boss_plan_is_hopeless` is a METHOD
on a live `StoryMode` instance and short-circuits on loss history (`losses < PLATEAU_LOSS_THRESHOLD
-> return False, []`) long before it reaches the no-answer test, so it cannot be called standalone
to answer "does this party have an answer?".
⇒ **What keeps the copy honest:** it imports production's own type chart and `_battler_slots()`,
and it mirrors production's GATE ORDERING exactly — `i in battlers`, then `eff >= 2.0` (which
`continue`s), then `score >= CREDIBLE_ANSWER_POWER`. That ordering matters and is easy to get
wrong: several saves here hold moves scoring **97.5** (Loudred/Stomp) and **90.0** (Mightyena/Bite)
that never count, because `eff` is 1.0 and the `eff < 2.0` branch fires first. A probe that checked
"score >= 75" alone would call those saves HAS_ANSWER and be silently, confidently wrong.
⇒ **If `_boss_plan_is_hopeless`'s no-answer block or `CREDIBLE_ANSWER_POWER` (currently 75) ever
changes, THIS FILE MUST BE UPDATED WITH IT.** Both constants are duplicated below on purpose so a
reader can diff them by eye against `story_mode.py:1087` and `:1573-1596`.

⛔ READ-ONLY. No writes to any save, no edits to `modules/`, `plugins/`, or `story_mode.py`.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_credible_answer.py [save_name.ss1]
      (defaults to ch13_fortree_door.ss1)
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

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
context.bot_mode = "Story"

from modules.pokemon import get_type_by_name
from modules.pokemon_party import get_party
from modules.story.early_game import _battler_slots

SAVES = REPO / "tools" / "story-dev" / "saves"

# Copied verbatim from story_mode.py: winona_fight cfg's ace_types + CREDIBLE_ANSWER_POWER.
ACE_TYPE_NAMES = ("Dragon", "Flying")
CREDIBLE_ANSWER_POWER = 75


def check_save(save_path: pathlib.Path) -> int:
    print("=" * 100)
    print(f"SAVE: {save_path}")
    print("=" * 100)
    if not save_path.is_file():
        print(f"  FILE NOT FOUND: {save_path}")
        print("VERDICT: ERROR (file not found)")
        return 2

    try:
        context.emulator.load_save_state(save_path.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
    except Exception as error:
        print(f"  COULD NOT LOAD SAVE: {type(error).__name__}: {error}")
        print("VERDICT: ERROR (load failed)")
        return 2

    try:
        ace_types = [get_type_by_name(n) for n in ACE_TYPE_NAMES]
        party = get_party()
        battlers = _battler_slots()
    except Exception as error:
        print(f"  COULD NOT READ PARTY / TYPE CHART: {type(error).__name__}: {error}")
        print("VERDICT: ERROR (read failed)")
        return 2

    print(f"  ace_types = {ACE_TYPE_NAMES}   CREDIBLE_ANSWER_POWER = {CREDIBLE_ANSWER_POWER}")
    print(f"  battler slots (not egg, has a damaging move) = {battlers}")

    best_score = -1.0
    best_desc = "(none)"
    has_answer = False

    for i, mon in enumerate(party):
        if mon is None:
            continue
        battler_tag = "BATTLER" if i in battlers else "non-battler(skipped by rule)"
        print(f"  -- party[{i}] {mon.species.name} L{mon.level} egg={mon.is_egg} [{battler_tag}]")
        try:
            own_types = tuple(mon.species.types)
        except Exception:
            own_types = ()
        print(f"     own_types = {[t.name for t in own_types]}")

        for idx in range(4):
            lm = mon.move(idx)
            if lm is None:
                print(f"     move[{idx}] = None")
                continue
            mv = lm.move
            if mv.base_power == 0:
                print(f"     move[{idx}] = {mv.name:<16} type={mv.type.name:<10} base_power=0 (status, skipped)")
                continue
            if lm.pp == 0:
                print(f"     move[{idx}] = {mv.name:<16} type={mv.type.name:<10} base_power={mv.base_power:<4} pp=0 (skipped)")
                continue

            eff = 1.0
            for t in ace_types:
                eff *= mv.type.get_effectiveness_against(t)
            stab = 1.5 if mv.type in own_types else 1.0
            score = mv.base_power * eff * stab

            counts = (i in battlers) and eff >= 2.0 and score >= CREDIBLE_ANSWER_POWER
            print(
                f"     move[{idx}] = {mv.name:<16} type={mv.type.name:<10} base_power={mv.base_power:<4} "
                f"eff(vs {'/'.join(ACE_TYPE_NAMES)})={eff:<5} stab={stab}  score={score:<7.1f} "
                f"{'-> CREDIBLE ANSWER' if counts else ''}"
            )

            if score > best_score:
                best_score = score
                best_desc = f"{mon.species.name}[{i}]/{mv.name} (eff={eff}, stab={stab}, score={score:.1f})"

            # Reproduce the exact production predicate: only battler slots count, and
            # the eff<2.0 branch `continue`s before the score/stab math ever runs.
            if i in battlers and eff >= 2.0 and score >= CREDIBLE_ANSWER_POWER:
                has_answer = True

    verdict = "HAS_ANSWER" if has_answer else "NO_ANSWER"
    print(f"  best move overall (any slot, for reference) = {best_desc}")
    print(f"VERDICT: {verdict}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    save_names = argv if argv else ["ch13_fortree_door.ss1"]
    rc = 0
    for name in save_names:
        rc |= check_save(SAVES / name)
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
