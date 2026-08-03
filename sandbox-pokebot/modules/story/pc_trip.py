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


#: ‼ ONLY ROTATE WHEN THE PARTY IS FULL — added 2026-08-02 after this module CAUSED a
#: catastrophic regression in batch6 (`x4-runs/20260802-160603`): **2 of 37 runs finished,
#: down from 16 of 34**. The rotation ran on EVERY heal, and `MIN_PARTY_AFTER_ROTATION = 3`
#: means it deposits until three mons remain, so the log reads
#: `PC rotation done — party is now 3` **73 times out of 75**. The bot spent the whole batch
#: in a catch → deposit → catch cycle on a permanent three-mon party, and then wedged inside
#: gyms it could not win (`global watchdog` 1 → 67, most of them MAUVILLE_CITY_GYM).
#:
#: `team_policy` decides correctly — an early-game party genuinely IS four low catches more
#: than 8 levels behind, so they genuinely ARE dead weight by its rule. The error was mine, in
#: the WIRING: §4's "piggyback on a heal" assumed rotation is occasional, and every-heal makes
#: it continuous.
#:
#: The blocker this feature exists for is exactly one condition — `resource_blocker()` refuses
#: a counter hunt only when `_party_count() >= 6`. So that is the only time a slot must be
#: freed. A four-mon party has room already and rotating it buys nothing.
ROTATE_ONLY_WHEN_PARTY_AT_LEAST = 6


def plan_deposits(party) -> dict:
    """The rotation plan for `party`, or an empty plan. Pure apart from reading the party."""
    from modules.story.team_policy import rotation_plan, view_from_party

    # ‼ THE GATE. Without it this strips every party to the floor on every heal — see the
    # constant above and 08-MISTAKES 2026-08-02.
    try:
        alive = sum(1 for p in (party or []) if p is not None and not getattr(p, "is_egg", False))
    except Exception:  # noqa: BLE001
        return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}
    if alive < ROTATE_ONLY_WHEN_PARTY_AT_LEAST:
        return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}

    empty = {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}

    try:
        views = view_from_party(party)
    except Exception:  # noqa: BLE001 - a malformed party must not break the heal
        return empty
    try:
        plan = rotation_plan(views)
    except Exception:  # noqa: BLE001
        return empty

    # ‼ NEVER DEPOSIT A HUNTED COUNTER (measured batch8, `x4-runs/20260803-063939`):
    #
    #     Story: counter hunt CAUGHT Machop (slot 5).
    #     Story: training the counter — Machop L15 -> L29 (team is L39…).
    #     Story: PC rotation — depositing Cascoon L5 …, Machop L17 (25 behind the team's best)
    #
    # The rotation deposited the very mon the chain had just crossed Hoenn to catch, because
    # a fresh counter is ~25 levels behind the team BY CONSTRUCTION and so is textbook "dead
    # weight" by the level rule. 2 of the 5 counters caught that batch were thrown away, and
    # the Norman lead candidates then contained no counter at all.
    #
    # `team_policy` is right that it is dead weight *by level*; it simply cannot know the mon
    # has a ROLE. It already protects the party's only HM carrier for the same reason — this
    # is that idea, applied to the answer we went and fetched.
    #
    # ‼ Read from the LIVE mode instance, not a module global: `_hunted_counter_pids` is
    # per-RUN state, and a module-level copy would survive into the next run of an ENDLESS
    # RESET batch and protect a Pokémon that no longer exists (`#24-x4-staleslate`).
    protected = set()
    try:
        from modules.context import context

        protected = set(getattr(context.bot_mode_instance, "_hunted_counter_pids", ()) or ())
    except Exception:  # noqa: BLE001 - no mode instance (tests) simply means nothing protected
        protected = set()

    if protected and plan.get("deposit"):
        kept = []
        for i in plan["deposit"]:
            try:
                if party[i] is not None and party[i].personality_value in protected:
                    from modules.console import console

                    console.print(
                        f"[cyan]Story: NOT depositing "
                        f"{getattr(party[i].species, 'name', '?')} — it is this boss's hunted "
                        f"counter, not dead weight.[/]"
                    )
                    continue
            except Exception:  # noqa: BLE001 - an unreadable mon is not provably protected
                pass
            kept.append(i)
        plan = dict(plan, deposit=kept,
                    worth_it=bool(kept) or bool(plan.get("withdraw")))
    return plan


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
