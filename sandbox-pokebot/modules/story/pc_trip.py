"""PC trip — the ACTION half of `#24-pc`. Deposits dead weight while already at a Poké Centre.

`modules/story/team_policy.py` decides WHAT to rotate and is deliberately pure ("this module
only decides"). This module is the part it excludes: walk to the PC, face it, deposit.

‼ WHY THIS EXISTS — measured, not assumed. In batch5 (`x4-runs/20260801-075805`) the counter
chain was blocked outright **5 times** by:

    Story: cannot hunt a counter — the party is full, so a catch would go to the PC box
           (needs #24-pc). Stopping honestly.

A full party forbids catching the counter, and 13 of that batch's 18 non-finishes (72%) were
the counter chain stopping for want of an answer it could not go and get. `team_policy`'s own
header records how the party fills up: P1 *"caught a Makuhita — a FIGHTING type, exactly the
counter Norman needs — and carried it from L8 to L9 across FIVE badges"* while the rest of the
team went L22 → L42. The answer was in the party the whole time and never became usable.

‼ PIGGYBACK, DO NOT DETOUR (`21-TEAM-POLICY-DESIGN.md` §4). This runs on arrival at a Poké
Centre for a heal **that was happening anyway**, between the nurse and the exit. It never
starts a journey of its own: a special trip to a PC costs more than the dead weight does.

‼ THE TILE IS PROVEN, NOT RECALLED. `probe_pc_tile.py` scanned six Poké Centre 1F maps from
the ROM's own map headers: every one has its PC at **(10, 1)**, approachable only from
**(10, 2)** facing **Up** (the PC sits against the north wall). Upstream's `daycare.py`
independently navigates to (10, 2) and faces Up for the same interaction, which corroborates
it. `interact_with_pc()` refuses unless the faced tile really is a PC, so a wrong tile fails
loudly rather than silently doing nothing.
"""

from __future__ import annotations

from typing import Generator

#: Proven by `tools/story-dev/probe_pc_tile.py` across six centres (2026-08-02).
PC_TILE = (10, 1)
PC_STAND_TILE = (10, 2)
PC_FACING = "Up"


def plan_deposits(party) -> dict:
    """The rotation plan for `party`, or an empty plan. Pure apart from reading the party."""
    from modules.story.team_policy import rotation_plan, view_from_party

    try:
        views = view_from_party(party)
    except Exception:  # noqa: BLE001 - a malformed party must not break the heal
        return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}
    try:
        return rotation_plan(views)
    except Exception:  # noqa: BLE001
        return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}


def deposit_dead_weight_if_worth_it() -> Generator:
    """Deposit dead weight at the Poké Centre PC. Assumes we are INSIDE a centre, healed.

    Does nothing at all unless `rotation_plan` says `worth_it` — a caller that rotates anyway
    burns PC visits for nothing (design §4). Never raises: a PC hiccup must not destroy a
    heal that already succeeded, so every failure degrades to "carry on with the party we
    have", which is exactly today's behaviour.
    """
    from modules.console import console
    from modules.context import context
    from modules.player import get_player_avatar
    from modules.pokemon_party import get_party

    party = get_party()
    plan = plan_deposits(party)
    if not plan.get("worth_it") or not plan.get("deposit"):
        return

    slots = list(plan["deposit"])
    reasons = plan.get("reasons", {})
    named = ", ".join(
        f"{getattr(party[i].species, 'name', '?')} L{party[i].level}"
        f" ({reasons.get(i, 'dead weight')})"
        for i in slots
        if i < len(party) and party[i] is not None
    )
    console.print(f"[bold cyan]Story: PC rotation — depositing {named}.[/]")

    try:
        from modules.modes.util.pc_interaction import PCAction, interact_with_pc
        from modules.modes.util.walking import ensure_facing_direction, navigate_to

        here = get_player_avatar().map_group_and_number
        yield from navigate_to(here, PC_STAND_TILE)
        yield from ensure_facing_direction(PC_FACING)

        # ‼ Resolve the Pokemon OBJECTS before the first deposit. Depositing shifts every
        # later party index down by one, so a list of indices computed up front goes stale
        # the moment the first one lands — the classic way this kind of loop deposits the
        # wrong mon. `interact_with_pc` takes objects, so capture them now.
        party = get_party()
        targets = [party[i] for i in slots if i < len(party) and party[i] is not None]
        if not targets:
            return
        yield from interact_with_pc([PCAction.deposit_pokemon_to_box(mon) for mon in targets])

        after = len(get_party())
        console.print(f"[green]Story: PC rotation done — party is now {after}.[/]")
        context.message = f"Story: deposited {len(targets)} — party {after}."
    except Exception as error:  # noqa: BLE001
        # A PC failure must never destroy a successful heal. The caller re-checks the party
        # either way and the counter chain's own resource gate still reports honestly.
        console.print(
            f"[yellow]Story: PC rotation failed ({error!r}) — carrying on with the party "
            f"we have.[/]"
        )
