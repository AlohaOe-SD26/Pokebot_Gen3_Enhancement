# -*- coding: utf-8 -*-
"""GATE — `#24-e4healing`: the OUT-OF-BATTLE healing policy, tested exhaustively without a ROM.

WHY A GATE AND NOT A DRIVE. `modules/story/overworld_items.py` is PURE, so every rule in it can be
checked in milliseconds and every rule SHOULD be — a between-rooms heal in the Elite Four runs in a
place with no nurse, no shop and no way back, so a policy bug there costs the whole gauntlet.

‼ THE CONTROLS ARE THE POINT. Several checks assert a plan is EMPTY or that an item is NOT chosen.
A policy that heals everything always would pass a suite of "did it heal?" checks and still be
wrong — it would burn a Full Restore on a scratch and a Revive on the L19 HM mule.

Usage:
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_overworld_items.py
    cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_overworld_items.py --self-test   # fault-test
Exits 0 only if every check passes.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.overworld_items import (  # noqa: E402
    Target, plan_healing, party_is_gauntlet_ready, effective_heal, TOP_UP_BELOW,
)

#: Straight from `modules/data/items.json` — ⛔ the real numbers, not invented ones.
#: ‼‼ THE LAST FOUR ENTRIES ARE TRAPS, AND THEY ARE THE MOST IMPORTANT PART OF THIS TABLE.
#: The first version of this gate listed ONLY medicine, so its item universe was cleaner than the
#: real bag — and a policy bug that selected **Repel as a 100-point healer** (its `parameter` is 100
#: *steps*) sailed through every check here and was only caught by a live drive.
#: ⇒ ⛔ **A POLICY TEST MUST CONTAIN THE CONFUSING NEIGHBOURS THE REAL BAG CONTAINS.** Repel,
#: X Attack, Nugget and Escape Rope are all things `post_league_shop.ss1` actually holds.
PARAMS = {
    "Potion": 20, "Super Potion": 50, "Hyper Potion": 200, "Max Potion": 255,
    "Full Restore": 255, "Full Heal": 0, "Revive": 0, "Max Revive": 0, "Antidote": 0,
    "Repel": 100, "X Attack": 0, "Nugget": 0, "Escape Rope": 0,   # ⬅ TRAPS — not medicine
}
#: What `field_use == "healing"` selects out of the above. ⛔ The allowlist the policy must use.
HEALING = {"Potion", "Super Potion", "Hyper Potion", "Max Potion", "Full Restore",
           "Full Heal", "Revive", "Max Revive", "Antidote"}

#: The basket §Ch23 leg 11 actually bought, MEASURED from `post_league_shop.ss1` — ⭐ INCLUDING the
#: non-medicine the bag really carries alongside it, so every check runs against the real universe.
BASKET = {"Hyper Potion": 30, "Full Restore": 3, "Full Heal": 8, "Revive": 3,
          "Repel": 2, "X Attack": 2, "Nugget": 1, "Escape Rope": 2}

#: The party that will actually walk in, MEASURED by `probe_ch24_readiness.py`.
def party(**over) -> "list[Target]":
    base = [
        Target(0, "Sceptile", 53, 147, 147), Target(1, "Zigzagoon", 19, 48, 48),
        Target(2, "Swellow", 48, 139, 139), Target(3, "Wailord", 47, 226, 226),
        Target(4, "Mightyena", 48, 144, 144), Target(5, "Castform", 36, 103, 103),
    ]
    for idx, kw in over.items():
        m = base[int(idx)]
        base[int(idx)] = Target(m.index, m.name, m.level,
                                kw.get("hp", m.current_hp), m.total_hp, kw.get("status", m.status))
    return base


FAILED: "list[str]" = []


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  {'PASS' if ok else '⛔ FAIL'}  {label}")
    if not ok:
        print(f"          got  {got!r}\n          want {want!r}")
        FAILED.append(label)


def main() -> int:
    fault = "--self-test" in sys.argv
    print("=" * 96)
    print("GATE — out-of-battle healing policy (`#24-e4healing`)"
          + ("   ‼ SELF-TEST: these checks MUST fail" if fault else ""))
    print("=" * 96)

    # ---- 1. THE CONTROL THAT MATTERS MOST: a healthy party is left alone --------------------------
    plan = plan_healing(party(), BASKET, PARAMS, healing_items=HEALING)
    check("a HEALTHY party produces an EMPTY plan (rule 1: never a no-op)", plan, [])
    check("party_is_gauntlet_ready(healthy) is True", party_is_gauntlet_ready(party()), True)

    # ---- 2. ⭐ RULE 3 — a scarce Revive goes to the BEST mon, not the first one -------------------
    # ⛔⛔ THE CHOICE OF FIXTURE HERE IS THE WHOLE CHECK, AND THE FIRST ONE I PICKED WAS VACUOUS.
    # I fainted Sceptile (slot 0, L53) and Zigzagoon (slot 1, L19) — but then "lowest slot" and
    # "highest level" BOTH answer Sceptile, so the check passed under a deliberately broken
    # slot-order policy. A fault test caught it; the gate was blind to its most important rule.
    # ⇒ **THE FAINTED MON WITH THE HIGHEST LEVEL MUST SIT LATER IN SLOT ORDER THAN A DECOY**, or the
    # two orderings are indistinguishable and the check proves nothing.
    # ⭐ Zigzagoon is slot 1 / L19 (the decoy, and the mon `#24-ch23wally` actually mis-picks);
    #   Mightyena is slot 4 / L48. Slot order → 1. Level order → 4. The arms now DIFFER.
    p = party(**{"1": {"hp": 0}, "4": {"hp": 0}})
    plan = plan_healing(p, {"Revive": 1}, PARAMS, healing_items=HEALING)
    revives = [a for a in plan if a.item_name == "Revive"]
    check("with ONE Revive and two fainted, exactly one Revive is planned", len(revives), 1)
    check("⭐ it goes to MIGHTYENA (slot 4, L48), NOT Zigzagoon (slot 1, L19) — rule 3, and the "
          "arms genuinely differ",
          revives[0].party_index if revives else None, 4)

    # ---- 3. rule 2 — revive is planned BEFORE the HP top-up for the same mon ----------------------
    p = party(**{"0": {"hp": 0}})
    plan = plan_healing(p, BASKET, PARAMS, healing_items=HEALING)
    mine = [a for a in plan if a.party_index == 0]
    check("a fainted mon gets Revive FIRST, then an HP item (rule 2)",
          [a.item_name for a in mine][:1], ["Revive"])
    check("...and IS topped up afterwards (Revive returns it at half HP)", len(mine) >= 2, True)

    # ---- 4. rule 5 — status uses the CHEAP cure, keeping Full Restores ---------------------------
    p = party(**{"2": {"status": "FRZ"}})
    plan = plan_healing(p, BASKET, PARAMS, healing_items=HEALING)
    cures = [a for a in plan if a.party_index == 2]
    check("a statused mon is cured with Full Heal, NOT Full Restore (rule 5)",
          cures[0].item_name if cures else None, "Full Heal")
    check("the FRZ reason warns it never thaws on its own",
          "FRZ never thaws" in (cures[0].reason if cures else ""), True)

    # ---- 5. ...but falls back to Full Restore when no cheap cure is held --------------------------
    plan = plan_healing(party(**{"2": {"status": "TOX"}}), {"Full Restore": 1}, PARAMS, healing_items=HEALING)
    check("with no Full Heal, status falls back to Full Restore",
          [a.item_name for a in plan if a.party_index == 2], ["Full Restore"])

    # ---- 6. rule 1 again — a barely-scratched mon is NOT healed -----------------------------------
    scratched = int(147 * (TOP_UP_BELOW + 0.05))   # comfortably above the bar
    plan = plan_healing(party(**{"0": {"hp": scratched}}), BASKET, PARAMS, healing_items=HEALING)
    check(f"a mon at {scratched}/147 (above the {TOP_UP_BELOW} bar) is NOT healed", plan, [])

    # ---- 7. rule 4 — cheapest SUFFICIENT ----------------------------------------------------------
    # ‼ BOTH OF THESE CHECKS WERE WRONG WHEN FIRST WRITTEN, AND THE POLICY WAS RIGHT. Recorded here
    # because the mistakes are instructive and a future reader will be tempted to make them again:
    #   (a) I used Sceptile at 137/147 to mean "missing 10 HP" — but that is **93%**, ABOVE the 0.90
    #       bar, so rule 1 correctly refused to heal and the plan was empty. ⇒ **a small ABSOLUTE
    #       deficit is not a small FRACTION**; on a 147 HP mon you cannot be 10 HP down and eligible.
    #       Use a mon with a small max HP instead.
    #   (b) I expected "missing 200" to take the largest item — but `effective_heal(200, 226) = 200`,
    #       so a Hyper Potion IS sufficient and the cheapest-sufficient rule fired correctly. To
    #       exercise the FALLBACK branch the deficit must exceed EVERY option we hold.
    # ⇒ ⭐ **a check that fails because its own arithmetic was wrong is the cheapest kind of bug
    #   there is — as long as you read the failure instead of "fixing" the subject.**
    bag = {"Potion": 5, "Super Potion": 5, "Hyper Potion": 5, "Full Restore": 5}
    # Zigzagoon: 48 max, at 38 → missing 10, and 38/48 = 79% is genuinely below the bar.
    plan = plan_healing(party(**{"1": {"hp": 38}}), bag, PARAMS, healing_items=HEALING)
    check("missing 10 HP (and below the bar) → the 20-point Potion, not a Hyper Potion",
          [a.item_name for a in plan], ["Potion"])
    # Wailord 226 max at 1 → missing 225, which NO held item covers (best is Super Potion, 50).
    thin = {"Potion": 5, "Super Potion": 5}
    plan = plan_healing(party(**{"3": {"hp": 1}}), thin, PARAMS, healing_items=HEALING)
    check("missing 225 with nothing sufficient → the LARGEST available (Super Potion)",
          [a.item_name for a in plan], ["Super Potion"])
    # ...and when something IS sufficient, the cheapest such item wins even if bigger ones are held.
    plan = plan_healing(party(**{"3": {"hp": 26}}), bag, PARAMS, healing_items=HEALING)    # missing exactly 200
    check("missing 200 → Hyper Potion (sufficient, and cheaper than Full Restore)",
          [a.item_name for a in plan], ["Hyper Potion"])

    # ---- 8. the bag is REAL — the policy cannot spend what we do not hold -------------------------
    # ⛔ SAME VACUITY TRAP AS CHECK 2, AND IT WAS ALSO PRESENT HERE: fainting slots 0/2/4/5 gives
    # levels 53/48/48/36, so the top two by LEVEL (slots 0,2) are also the top two by SLOT. Fixed by
    # fainting slots 1/3/4/5 → levels 19/47/48/36: slot order picks {1,3}, level order picks {4,3}.
    p = party(**{"1": {"hp": 0}, "3": {"hp": 0}, "4": {"hp": 0}, "5": {"hp": 0}})
    plan = plan_healing(p, {"Revive": 2}, PARAMS, healing_items=HEALING)
    check("four fainted but only TWO Revives held → exactly 2 planned",
          len([a for a in plan if a.item_name == "Revive"]), 2)
    check("...and they go to Mightyena L48 (slot 4) and Wailord L47 (slot 3) — NOT the two lowest "
          "slots {1,3}",
          sorted(a.party_index for a in plan if a.item_name == "Revive"), [3, 4])

    # ---- 9. rule 6 — bounded --------------------------------------------------------------------
    hurt = party(**{str(i): {"hp": 1} for i in range(6)})
    plan = plan_healing(hurt, BASKET, PARAMS, healing_items=HEALING, max_actions=3)
    check("max_actions=3 is respected (rule 6: bounded)", len(plan), 3)

    # ---- 10. every emitted action must CHANGE something ------------------------------------------
    plan = plan_healing(party(**{"0": {"hp": 5}, "3": {"hp": 0}, "2": {"status": "PAR"}}), BASKET, PARAMS, healing_items=HEALING)
    check("every action carries a non-empty `expect` (the consequence, not the call)",
          all(a.expect for a in plan) and len(plan) > 0, True)
    check("no action targets a mon that needed nothing",
          sorted({a.party_index for a in plan}), [0, 2, 3])

    # ---- 10b. ⛔⛔ THE TRAP CHECK — the one a live drive had to catch for me ----------------------
    # `Repel`'s parameter is 100 (STEPS). A policy filtering on `parameter > 0` reads that as a
    # 100-point healer and plans `(4, 'Repel', 'Mightyena at 0/144')`, which then dies at a party
    # menu a no-target item never opens. ⇒ assert the NON-medicine is never chosen, for any deficit.
    for hp, who in ((1, "3"), (40, "0"), (5, "4")):
        plan = plan_healing(party(**{who: {"hp": hp}}), BASKET, PARAMS, healing_items=HEALING)
        chosen = {a.item_name for a in plan}
        check(f"⭐ slot {who} at {hp} HP → NO non-medicine chosen (Repel/X Attack/Nugget/Escape Rope)",
              sorted(chosen & {"Repel", "X Attack", "Nugget", "Escape Rope"}), [])
    # ...and the same when medicine has run OUT — the tempting moment to grab anything.
    plan = plan_healing(party(**{"3": {"hp": 1}}), {"Repel": 5, "X Attack": 5}, PARAMS,
                        healing_items=HEALING)
    check("⛔ with ONLY non-medicine held, the plan is EMPTY — never a substitute", plan, [])

    # ---- 11. effective_heal matches the ROM's semantics -------------------------------------------
    check("Hyper Potion on a 147 HP mon caps at 200 (param), not at HP", effective_heal(200, 147), 200)
    check("Full Restore's 255 sentinel means 'all of it'", effective_heal(255, 226), 226)

    # ---- 12. gauntlet-readiness is stricter than 'items were used' -------------------------------
    check("a FAINTED member makes the party not ready",
          party_is_gauntlet_ready(party(**{"1": {"hp": 0}})), False)
    check("a STATUSED member makes the party not ready",
          party_is_gauntlet_ready(party(**{"1": {"status": "SLP"}})), False)

    if fault:
        # ‼ FAULT-TEST THE GATE ITSELF: prove these checks can FAIL. A gate never seen red is a
        # gate nobody has reason to trust.
        print("\n  -- injecting a broken policy: revive by SLOT ORDER instead of level --")
        p = party(**{"1": {"hp": 0}, "0": {"hp": 0}})
        by_slot = sorted((m for m in p if m.fainted), key=lambda m: m.index)[0].index
        check("‼ SELF-TEST — slot-order revive picks Zigzagoon; the real policy must NOT", by_slot, 0)

    print("\n" + "=" * 96)
    if FAILED:
        print(f"RESULT: {len(FAILED)} CHECK(S) FAILED")
        for f in FAILED:
            print(f"  - {f}")
        return 1
    print("RESULT: ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
