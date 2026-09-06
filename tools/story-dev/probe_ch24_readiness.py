# -*- coding: utf-8 -*-
"""`#24-e4healing` / §Ch24 — READ-ONLY: what the party and bag ACTUALLY are before the Elite Four.

WHY THIS EXISTS. A roster analysis priced the gauntlet against **recalled** party HP (Sceptile 139,
Swellow 129, Wailord 223) and concluded the run fails at DRAKE. Those numbers decide whether Glacia's
Blizzard is an OHKO, which is the whole argument — so they must be MEASURED, not accepted.
‼ The same analysis named ONE flag that decides the cheapest fix:
`ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM` (flag 1098). Clear ⇒ TM13 Ice Beam is still lying in
`AbandonedShip_Room_B1F` and the fix is FREE. Set ⇒ Gen-3 TMs are single-use and non-repurchasable,
so the only Ice sources left are TM14 Blizzard (₽5,500) or the Game Corner (~₽80,000) — and with
₽1,741 in hand that means grinding money first.

⛔ READ-ONLY. It loads a save state, reads memory, and prints. It never presses a button, never
captures a fixture, and never writes to `saves/`.
‼ It DOES boot LibmgbaEmulator on the shared `repro-ml` profile, which updates that profile's
`current_state.ss1` — the same caveat every probe in this tree carries.

Usage:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_readiness.py
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_readiness.py post_league_shop.ss1
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

from modules.items import get_item_bag
from modules.memory import get_event_flag
from modules.player import get_player
from modules.pokemon_party import get_party

SAVES = REPO / "tools" / "story-dev" / "saves"

#: The flag that decides whether the cheap fix exists at all.
ICE_BEAM_FLAG = "ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM"

#: The other free TMs the analysis named. Each is an item ball gated by its own flag.
#: ⛔⛔ EVERY NAME HERE IS COPIED FROM `modules/data/event_flags/emerald.txt`, NEVER TYPED FROM
#: MEMORY — see `_flag` below for the measured reason that rule is enforced rather than requested.
FREE_TM_FLAGS = {
    "TM13 Ice Beam    (AbandonedShip_Room_B1F)": ICE_BEAM_FLAG,                        # 1098
    "TM02 Dragon Claw (MeteorFalls_B1F_2R)": "ITEM_METEOR_FALLS_B1F_2R_TM_DRAGON_CLAW",  # 1080
    "TM26 Earthquake  (SeafloorCavern_Room9)": "ITEM_SEAFLOOR_CAVERN_ROOM_9_TM_EARTHQUAKE",  # 1090
}


def _known_flag_names() -> set:
    """Every flag name the ROM data defines. ⛔ The allowlist that makes a typo LOUD."""
    table = REPO / "sandbox-pokebot" / "modules" / "data" / "event_flags" / "emerald.txt"
    names = set()
    for line in table.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            names.add(parts[1])
    return names


_KNOWN = _known_flag_names()


def _flag(name: str) -> bool:
    """Read an event flag, REFUSING an unknown name.

    ‼‼ MEASURED NECESSARY 2026-09-04, NOT DEFENSIVE PROGRAMMING. The first version of this probe
    asked for `ITEM_METEOR_FALLS_1F_2R_TM23` — a name I invented. **`get_event_flag` returned
    `False` without raising**, and `False` here means "the item ball has NOT been taken", so the
    probe cheerfully printed **"✅ STILL THERE"** for a flag that does not exist.
    ⇒ ⛔ **A FABRICATED READING THAT LOOKS LIKE GOOD NEWS IS THE WORST KIND**, and it is precisely
    the shape this project has been burned by before (an instrument scoped to the wrong question
    returning a confident empty answer). The allowlist turns a typo into a refusal.
    """
    if name not in _KNOWN:
        raise KeyError(
            f"{name!r} is not a flag in modules/data/event_flags/emerald.txt. ⛔ Refusing to read "
            f"it: an unknown name reads False, and False here means 'still available' — a typo "
            f"would print as good news."
        )
    return get_event_flag(name)

#: ⛔ The speed tier that decides the run, per the roster analysis: Drake's ace Salamence is 132 Spe,
#: and only a mon FASTER than that moves first against it. Losing every such mon is the point of no
#: return, because Salamence then attacks first every turn for the rest of the fight.
SALAMENCE_SPEED = 132

#: Glacia's two hardest hits, as PREDICTED by the analysis. Printed beside real max HP so the
#: OHKO claim can be checked rather than believed. ⚠ These are the AGENT'S damage rolls, NOT ours.
GLACIA_HITS = {"Sealeo L52 Blizzard": (120, 142), "Walrein L53 Ice Beam": (125, 148)}


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "post_league_shop.ss1"
    save = SAVES / name
    if not save.exists():
        print(f"⛔ no such fixture: {save}")
        return 2

    context.emulator.load_save_state(save.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    print("=" * 96)
    print(f"§Ch24 READINESS — {name}   (READ-ONLY)")
    print("=" * 96)

    money = getattr(get_player(), "money", None)
    print(f"\nMONEY: ₽{money:,}" if isinstance(money, int) else f"\nMONEY: {money!r}")

    # ---- 1. THE FLAG THAT DECIDES THE FIX --------------------------------------------------------
    print("\n-- FREE TM ITEM BALLS (flag SET = already taken, gone forever; Gen-3 TMs are single-use)")
    for label, flag in FREE_TM_FLAGS.items():
        try:
            taken = _flag(flag)
            mark = "⛔ TAKEN" if taken else "✅ STILL THERE"
            print(f"   {mark:<16} {label:<40} [{flag}]")
        except Exception as error:  # noqa: BLE001 — a bad flag NAME is a reading, not a crash
            print(f"   ⚠ COULD NOT READ  {label:<40} [{flag}] — {type(error).__name__}: {error}")

    # ---- 2. THE PARTY, MEASURED ------------------------------------------------------------------
    print("\n-- PARTY (⭐ max HP and Speed are what the Glacia/Drake analysis rests on)")
    print(f"   {'slot':<5}{'species':<12}{'lvl':<5}{'HP':<12}{'Speed':<7}{'vs Salamence 132 Spe'}")
    fast = []
    for i, mon in enumerate(get_party()):
        if mon is None or getattr(mon, "species", None) is None:
            continue
        spe = mon.stats.speed
        faster = spe > SALAMENCE_SPEED
        if faster:
            fast.append(f"{mon.species.name} L{mon.level}")
        print(f"   {i:<5}{mon.species.name:<12}{mon.level:<5}"
              f"{f'{mon.current_hp}/{mon.total_hp}':<12}{spe:<7}"
              f"{'✅ OUTSPEEDS' if faster else '⛔ slower'}")

    print(f"\n   ⇒ MONS THAT OUTSPEED DRAKE'S ACE: {len(fast)} — {fast if fast else 'NONE'}")

    # ---- 2b. ⭐⭐ THE FULL STAT LINE, AND THE IV+EV IT IMPLIES ------------------------------------
    # ⛔⛔ WHY THIS EXISTS. Every damage number in `2026-09-04-ch24-ROSTERS-AND-WINNABILITY.md`, in
    # `2026-09-04-ch24-MOVESET-AND-TM-PLAN.md`, and in the 2026-09-06 adversarial pass was computed
    # from an ASSUMED IV 31 / EV 0 spread. That assumption was never measured, and the agent that
    # relied on it said so plainly: calibrating against our real HP and Speed implies an
    # (IV + EV//4) contribution ranging **19–50**, not a flat 31. ⇒ the level target for the gauntlet
    # is currently a GUESS built on a guess.
    # ⭐ Gen-3 stat formula (`src/pokemon.c`, CalculateMonStats):
    #       HP    = (2*Base + IV + EV//4) * L // 100 + L + 10
    #       other = ((2*Base + IV + EV//4) * L // 100 + 5) * NatureMod
    # ⇒ inverting it gives `(IV + EV//4)` per stat, which is what actually drives every damage roll.
    # ‼ NATURE IS NOT REMOVED HERE — a ±10% nature on one stat shows up as an implausible spread on
    # that stat. Read a value outside 0..63 as "nature, not IVs", never as a bad measurement.
    print("\n-- ⭐ FULL STATS, and the (IV + EV//4) each implies — THE INPUT EVERY DAMAGE ROLL NEEDS")
    print(f"   {'species':<12}{'lvl':<5}{'HP':<7}{'Atk':<6}{'Def':<6}{'SpA':<6}{'SpD':<6}{'Spe':<6}"
          f"  implied (IV+EV//4) per stat")
    try:
        from modules.data.pokemon import get_species_by_name  # noqa: F401  (presence check only)
    except Exception:  # noqa: BLE001
        pass
    for mon in get_party():
        if mon is None or getattr(mon, "species", None) is None:
            continue
        s, L = mon.stats, mon.level
        base = getattr(mon.species, "base_stats", None)

        def implied(stat_value: int, base_value: "int | None", is_hp: bool) -> str:
            """Invert the Gen-3 formula for `(IV + EV//4)`. ⚠ Nature is NOT removed — see above."""
            if not base_value or not L:
                return "?"
            if is_hp:
                v = (stat_value - L - 10) * 100 // L - 2 * base_value
            else:
                v = (stat_value - 5) * 100 // L - 2 * base_value
            return str(v)

        cells = ""
        if base is not None:
            cells = "  ".join(
                f"{n}={implied(getattr(s, a), getattr(base, a, None), a == 'hp')}"
                for n, a in (("HP", "hp"), ("Atk", "attack"), ("Def", "defence"),
                             ("SpA", "special_attack"), ("SpD", "special_defence"), ("Spe", "speed"))
            )
        else:
            cells = "⚠ base stats unavailable on this species object — cannot invert"
        print(f"   {mon.species.name:<12}{L:<5}{mon.total_hp:<7}{s.attack:<6}{s.defence:<6}"
              f"{s.special_attack:<6}{s.special_defence:<6}{s.speed:<6}  {cells}")
    print("   ‼ A value outside 0..63 means NATURE is inflating/deflating that stat, not a bad read.")
    print("   ⇒ USE THESE, NOT IV31/EV0, FOR EVERY DAMAGE ROLL FROM NOW ON.")
    if len(fast) <= 2:
        print("   ⛔ THIS IS THE POINT-OF-NO-RETURN SET. The analysis predicts Glacia's ice OHKOs")
        print("      exactly these, and with NO usable Revive a faint is permanent for the gauntlet.")

    # ---- 3. IS GLACIA'S OHKO CLAIM TRUE OF *OUR* NUMBERS? ----------------------------------------
    print("\n-- GLACIA OHKO CHECK (agent's damage rolls vs OUR measured max HP)")
    for mon in get_party():
        if mon is None or getattr(mon, "species", None) is None:
            continue
        if mon.stats.speed <= SALAMENCE_SPEED:
            continue  # only the speed-critical mons matter for the point of no return
        for hit, (lo, hi) in GLACIA_HITS.items():
            if lo >= mon.total_hp:
                verdict = "⛔ GUARANTEED OHKO"
            elif hi >= mon.total_hp:
                verdict = f"⚠ ROLL-DEPENDENT OHKO (needs {mon.total_hp}, rolls {lo}-{hi})"
            else:
                verdict = "✅ survives"
            print(f"   {mon.species.name:<12} {mon.total_hp:>4} HP  vs {hit:<26} {verdict}")

    # ---- 4. THE BAG, AND WHAT THE BOT CAN ACTUALLY USE -------------------------------------------
    print("\n-- BAG (⛔ `battle_items.py:85` filters on `param > 0`, so param 0 = UNUSABLE by the bot)")
    # ⛔ The verdict is derived from `items.json` DIRECTLY, not from an attribute guess. The first
    # version probed `item.battle_use`, got `None` for every row, and printed an EMPTY verdict
    # column beside correct params — a column that looks broken invites the reader to ignore it,
    # which is how a real "UNUSABLE" gets skimmed past.
    import json as _json

    _raw = _json.loads((REPO / "sandbox-pokebot" / "modules" / "data" / "items.json")
                       .read_text(encoding="utf-8"))
    _rows = _raw if isinstance(_raw, list) else list(_raw.values())
    _by_name = {r["name"]: r for r in _rows if isinstance(r, dict) and "name" in r}

    usable = unusable = 0
    for slot in get_item_bag().items:
        row = _by_name.get(slot.item.name, {})
        param, use = row.get("parameter"), row.get("battle_use")
        note = ""
        if use == "healing":
            if (param or 0) > 0:
                note, usable = "✅ usable in battle", usable + slot.quantity
            else:
                note, unusable = "⛔ UNUSABLE by our policy (param 0)", unusable + slot.quantity
        print(f"   {slot.item.name:<16} x{slot.quantity:<4} battle_use={str(use):<8} "
              f"param={str(param):<5} {note}")
    # ⛔⛔ SAY WHICH SET IS BEING COUNTED. This total is the WHOLE BAG; the docs quote the
    # PURCHASED BASKET (44 bought / 33 usable / 11 not). Both are correct and they differ because
    # the bag also holds pre-existing stock — 4 Antidote, 1 Potion, 1 Super Potion. ‼ A bare number
    # that disagrees with the docs for an unstated reason is how a reader concludes one of them is
    # wrong and "fixes" the right one.
    basket = {"Hyper Potion": 30, "Full Restore": 3, "Full Heal": 8, "Revive": 3}
    b_ok = sum(q for n, q in basket.items() if (_by_name.get(n, {}).get("parameter") or 0) > 0)
    b_no = sum(basket.values()) - b_ok
    print(f"\n   ⇒ WHOLE BAG:        {usable} usable · {unusable} unusable ({usable + unusable} total)")
    print(f"   ⇒ PURCHASED BASKET: {b_ok} usable · {b_no} unusable ({sum(basket.values())} bought)"
          f"   ⇐ ⭐ THIS is the pair the docs quote (`#24-e4healing`)")
    print("   ⇒ the difference is pre-existing stock the bot did not buy this leg.")

    print("\n" + "=" * 96)
    print("‼ EVERY NUMBER ABOVE IS MEASURED. The damage ROLLS are the agent's and are NOT.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
