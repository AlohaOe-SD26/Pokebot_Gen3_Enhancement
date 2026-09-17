# -*- coding: utf-8 -*-
"""GATE — does the move-learning policy count HM moves when it asks "do I already cover this type?"

⛔⛔ THE DEFECT THIS PINS, AND IT COST THE ONE MOVE §Ch24 IS BUILT AROUND.
`which_move_should_be_replaced` (`plugins/custom_modes/story_mode.py`) has a rule it states plainly:
*"if the new move's type is ALREADY covered, only overwrite a WEAKER same-type move … otherwise
DECLINE — don't churn or lose a different type for a redundant one."* Good rule. But the census it
asked was built from `damaging_slots`, **which excludes HM moves**, so it could not see most of what
the Pokémon actually knew.

MEASURED on the real grind ladder, reproducible from the pinned fixtures:

    post_e4grind_L57.ss1  L57  Dive, Surf, Ice Beam,   Waterfall
    post_e4grind_L59.ss1  L59  Dive, Surf, Hydro Pump, Waterfall    <<< -Ice Beam  +Hydro Pump

Wailord knows THREE Water moves — `Dive` (HM08), `Surf` (HM03), `Waterfall` (HM07) — plus `Ice Beam`
(TM13). All three Water moves are HMs, so `damaging_slots` was `[Ice Beam]` alone and the census read
`current_types == [Ice]`. ⇒ **Hydro Pump (Water) looked like a type the party LACKED**, the policy
"freed the weakest slot to gain coverage", and the team's only Ice move went. That move was fetched
by a **~700,000-frame Abandoned Ship round trip**, taken specifically because the change analysis says
the party LOSES to Drake without it — and Ice is **4x** on Salamence, Altaria and Flygon.

⭐⭐ ONE MECHANISM ALSO EXPLAINS THE OPPOSITE OBSERVATION, WHICH IS WHY IT IS THE RIGHT ONE. On the
`post_grind_L60` lineage Wailord held **Water Spout** — a TM, therefore non-HM — in that slot. The
census read `[Water]`, Hydro Pump was REDUNDANT, Water Spout (150 BP) outranks it, and the policy
correctly DECLINED, keeping all four moves across the very same level. Same code, same level,
opposite outcome, decided entirely by which slot happened to be replaceable.
‼ That is also how I got this backwards: I observed the L60 lineage keeping its moves and wrote down
*"the bot DECLINES level-up moves"* as a general rule, then used it to dismiss the strongest
objection to a plan. **The objection was right.**

⇒ THE FIX: replaceability and coverage are DIFFERENT QUESTIONS. You cannot overwrite an HM, but the
Pokémon still KNOWS it, so the census must include it. The replaceable set stays `damaging_slots`;
only the census widens to every damaging move.

‼‼ THE ARMS USE THE **REAL** WAILORD AND THE **REAL** HYDRO PUMP, NOT FAKES — deliberately. Twice
today a hand-built fixture in a probe was wrong while its subject was right (a type chart missing a
resistance; a collision predicate asserting the wrong value). Loading the pinned save removes that
whole class of error: the party, the stats, the HM flags and the move data are the ones the game had.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_learn_hm_coverage.py
Exit 0 only if BOTH arms hold.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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
context.emulation_speed = 0

from modules.pokemon import get_move_by_name
from modules.pokemon_party import get_party

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 100
DECLINE = 4


def load_mon(save_name: str, species: str):
    f = SAVES / save_name
    if not f.is_file():
        return None, f"no such save: {save_name}"
    context.emulator.load_save_state(f.read_bytes())
    for _ in range(20):
        context.emulator.run_single_frame()
    mon = next((m for m in get_party()
                if m is not None and getattr(m, "species", None)
                and m.species.name == species), None)
    return mon, None


def moves_of(mon):
    return [lm.move.name for lm in mon.moves if lm is not None and lm.move is not None]


def main() -> int:
    from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

    strategy = LevelUpTravelBattleStrategy()
    print(BAR)
    print("  does the learn policy count HM moves when asking 'do I already cover this type?'")
    print(BAR)

    results = []

    # ---- THE FAILING ARM, REPRODUCED FROM THE REAL SAVE -----------------------------------------
    wailord, err = load_mon("post_e4grind_L57.ss1", "Wailord")
    if err or wailord is None:
        print(f"  ABORT (instrument) — {err or 'no Wailord'}")
        return 1
    hydro = get_move_by_name("Hydro Pump")
    have = moves_of(wailord)
    slot = strategy.which_move_should_be_replaced(wailord, hydro)
    victim = have[slot] if 0 <= slot < len(have) else "DECLINE"
    print(f"\n  ARM 1 — the real defect, from post_e4grind_L57.ss1")
    print(f"      Wailord L{wailord.level}: {have}")
    print("      three of those are Water, and ALL THREE ARE HMs (Dive/HM08, Surf/HM03,")
    print("      Waterfall/HM07) — only Ice Beam is replaceable.")
    print(f"      learning Hydro Pump (Water) -> slot {slot} ({victim})")
    ok1 = slot == DECLINE
    print(f"      ⇒ {'PASS' if ok1 else 'FAIL'} — must DECLINE ({DECLINE}); Water is ALREADY covered")
    print("        three times over, and Ice Beam is the party's only Ice move.")
    results.append(ok1)

    # ---- CONTROL A: the policy must still ACCEPT a genuine coverage gain -------------------------
    # ⛔ Without this, a policy that declined EVERYTHING would pass arm 1 and be catastrophic.
    thunder = get_move_by_name("Thunderbolt")
    slot_c = strategy.which_move_should_be_replaced(wailord, thunder)
    victim_c = have[slot_c] if 0 <= slot_c < len(have) else "DECLINE"
    print(f"\n  CONTROL A — a REAL coverage gain must still be taken")
    print(f"      learning Thunderbolt (Electric — genuinely absent) -> slot {slot_c} ({victim_c})")
    ok2 = slot_c != DECLINE
    print(f"      ⇒ {'PASS' if ok2 else 'FAIL'} — must NOT decline. A policy that refuses every")
    print("        new move would satisfy ARM 1 while making the team permanently worse.")
    results.append(ok2)

    # ---- CONTROL B: a same-type UPGRADE must still be taken --------------------------------------
    # The rule the defect broke is "only overwrite a WEAKER same-type move" — prove that half lives.
    mightyena, err = load_mon("post_e4grind_L57.ss1", "Mightyena")
    ok3 = False
    if mightyena is not None:
        mhave = moves_of(mightyena)
        crunch_up = get_move_by_name("Hyper Beam")   # Normal, 150 — beats Strength/Take Down/Bite
        slot_m = strategy.which_move_should_be_replaced(mightyena, crunch_up)
        victim_m = mhave[slot_m] if 0 <= slot_m < len(mhave) else "DECLINE"
        print(f"\n  CONTROL B — a same-type POWER UPGRADE must still be taken")
        print(f"      Mightyena L{mightyena.level}: {mhave}")
        print(f"      learning Hyper Beam (Normal 150, type already covered) -> slot {slot_m} ({victim_m})")
        ok3 = slot_m != DECLINE
        print(f"      ⇒ {'PASS' if ok3 else 'FAIL'} — must overwrite a WEAKER same-type move, so the")
        print("        widened census has not turned the policy into 'always decline'.")
    results.append(ok3)

    print(f"\n{BAR}")
    if all(results):
        print("  ✅ COVERAGE IS COUNTED OVER EVERY DAMAGING MOVE: the redundant Water move is")
        print("     refused, a genuine new type is accepted, and a same-type upgrade still lands.")
        print(BAR)
        return 0
    print("  ⛔ THE LEARN POLICY DOES NOT SEPARATE THESE CASES — do not trust it with a curated team.")
    print(BAR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
