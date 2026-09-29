"""Roster management — put specific Pokémon in specific PARTY SLOTS, safely.

WHY THIS EXISTS. Deposit and withdraw answer "which Pokémon are in the party"; they cannot answer
"in what ORDER". Some content requires an order:
  * the **Regi tombs** need a specific species in the FIRST slot and another in the LAST — a hard
    gate, not a preference;
  * team building generally (lead the right matchup, bench the passengers) is an ordering problem.

‼ THE PRIMITIVE ALREADY EXISTS AND I ALMOST MISSED IT. `modules/menuing.py` `RotatePokemon(i, j)`
performs a TRUE two-slot swap of arbitrary slots via the party menu's SWITCH item. What did not
exist is anything that plans a sequence of swaps, or that drives one safely.

‼‼ AND THE PRIMITIVE IS NOT SAFE ON ITS OWN. `RotatePokemon`'s cursor drive sits on the **unfixed
side of KI-38** — the project's dominant battle hang — with FOUR unbounded `while` loops
(`menuing.py:1021-1026`, `:1028`, `:1031`, plus `navigate_to_mon:525` / `navigate_to_lead:530`) and
a `set_manual_mode()` trapdoor underneath (`menu_parsers.py:164-166` drops the bot to Manual on
`slot_id == -1` **and still returns**, so the caller's loop keeps pressing while the run is already
dead). ‼ `RotatePokemon(i, j)` with `j != 0` has **NEVER been driven** in this project. *(Corrected 2026-09-29: not
every story strategy returns `None` from `choose_new_lead_after_battle` — the catch strategies inherit the default,
which rotates when the lead has FAINTED; RULING 24 step 3 keeps the trainee during swap-training.)* Building on it raw would be re-walking KI-38 in a new place.

So everything here is wrapped in the harness `_rotate_lead_safely` already proves in production
(it runs every training round): refuse to open a menu while a field script is active, BOUND the
drive, close a half-open menu and retry on interruption, and give up gracefully.

‼ AND IT ADDRESSES BY PERSONALITY VALUE, NEVER BY SLOT. A slot index is stale the instant a swap
happens; a PID identifies the Pokémon itself. `pc_trip.find_in_box` and the counter chain both
learned this the hard way. Every step re-reads the party and re-finds the PID.
"""

from __future__ import annotations

from typing import Generator

#: How many swaps a 6-slot permutation can ever need. Selection sort places one slot per pass and
#: the last falls into place, so 5 is the true ceiling — a bound, not a guess.
MAX_SWAPS = 5

#: Frames to allow one party-menu swap before treating it as interrupted. Mirrors
#: `_rotate_lead_safely`'s 3000; the menu itself is fast, the risk is a script firing mid-drive.
SWAP_TIMEOUT_FRAMES = 3000


def plan_reorder(current_pids: list[int], target_pids: list[int]) -> list[tuple[int, int]]:
    """The swaps that turn `current_pids` into an order starting with `target_pids`. PURE.

    `target_pids` is a PREFIX SPEC, not a full permutation: it means "these Pokémon, in this order,
    starting at slot 0". Everything unnamed keeps its relative order and fills the rest. That is
    what real requirements look like — "Relicanth first" cares about slot 0 and nothing else.

    ‼ TO PIN THE **LAST** SLOT (which the Regi tombs need), pass a spec whose length equals the
    party size, e.g. `[relicanth_pid] + middles + [wailord_pid]`. `plan_last_slot` below builds that
    for the common "first and last are fixed" case so callers do not hand-roll it.

    Returns `[(i, j), ...]` — swap party slot i with slot j, applied in order. Empty means the
    party is already correct, which is the case worth making cheap: this runs before content that
    may already be satisfied.

    :raises ValueError: if a target PID is not in the party. That is a caller bug (asking for a
        Pokémon we do not have) and must not be silently reordered around.
    """
    order = list(current_pids)
    # ‼ DUPLICATES IN THE SPEC MUST BE REFUSED, NOT PLANNED AROUND. Asking for the same Pokémon
    # twice is unsatisfiable, and the failure is the worst kind: `order.index(pid)` returns the slot
    # it was ALREADY placed in, so `here < destination`, the swap undoes previous work, and the
    # plan never converges — the driver would perform real menu swaps for its whole budget and then
    # report failure with a scrambled party. `plan_last_slot` guards `first == last`, but a direct
    # `reorder_party([pid, pid])` reached this. Refusing costs one line.
    if len(set(target_pids)) != len(target_pids):
        raise ValueError(
            f"cannot reorder: the target spec {target_pids} repeats a personality value. "
            "One Pokémon cannot occupy two slots."
        )
    for pid in target_pids:
        if pid not in order:
            raise ValueError(
                f"cannot reorder: personality value {pid} is not in the party {order}. "
                "Withdraw it first — reordering cannot conjure a Pokémon."
            )

    swaps: list[tuple[int, int]] = []
    for destination, pid in enumerate(target_pids):
        if destination >= len(order):
            break
        here = order.index(pid)
        if here == destination:
            continue  # already in place — the cheap and common case
        order[destination], order[here] = order[here], order[destination]
        swaps.append((destination, here))
    return swaps


def plan_last_slot(current_pids: list[int], first_pid: int, last_pid: int) -> list[int]:
    """Build a full-length spec for "this one FIRST and that one LAST", order-preserving otherwise.

    ‼ THIS IS THE REGI SHAPE, and it is worth a named helper because getting it wrong is silent:
    the tombs check the first and last party slots, so a spec that only pins slot 0 leaves the last
    slot to chance. Everything not named keeps its current relative order, so a caller does not
    accidentally reshuffle a team it spent the whole run building.

    :raises ValueError: if either PID is missing, or if they are the same Pokémon (which cannot be
        both first and last, and would otherwise produce a plan that silently does nothing).
    """
    if first_pid == last_pid:
        raise ValueError(
            "the same Pokémon cannot be both first and last — the caller wants two different mons."
        )
    for pid in (first_pid, last_pid):
        if pid not in current_pids:
            raise ValueError(f"personality value {pid} is not in the party {current_pids}.")

    middle = [p for p in current_pids if p not in (first_pid, last_pid)]
    return [first_pid] + middle + [last_pid]


def _party_pids() -> list[int]:
    from modules.pokemon_party import get_party

    return [m.personality_value for m in get_party() if m is not None]


def reorder_party(target_pids: list[int], *, attempts_per_swap: int = 3) -> Generator:
    """Reorder the party so it starts with `target_pids`. Returns True only if VERIFIED.

    ‼ RETURNS A TRUTHFUL BOOLEAN. A reorder that half-completed is worse than one that did not
    start — content gated on party order would proceed against an order it never got. So this
    verifies by re-reading the party after every swap AND at the end, and reports what happened.

    ‼ RE-PLANS AFTER EVERY SWAP rather than replaying a precomputed list. The plan is computed from
    positions, and a swap that lands differently than intended (an interrupted menu, a mis-driven
    cursor) invalidates every later step. This is the same lesson as the Mossdeep gym route:
    *update the world model from what actually happened, never from what the plan intended.*
    """
    from modules.console import console
    from modules.menuing import RotatePokemon
    from modules.modes import BotModeError
    from modules.story.early_game import (
        _check_abort,
        _ride_out_scripted_scene,
        _yield_bounded,
        wait_until_truly_controllable,
    )
    from modules.tasks import get_global_script_context

    from modules.context import context
    from modules.story.early_game import reraise_if_aborting

    # ‼ ONE PASS PER *ATTEMPT*, NOT PER SWAP. The first version computed `current`/`source`/
    # `destination` once and then retried up to 3 times against those stale indices. If attempt 1
    # performed a WRONG swap — reachable: `navigate_to_mon` reads `gPartyMenu.slot_id` before the
    # party menu has initialised, and its loop can exit having pressed nothing, swapping
    # `0 <-> destination` instead of `source <-> destination` — then the party has moved and
    # attempts 2 and 3 drive indices that no longer mean anything. Re-reading every attempt is the
    # project's own rule: *update the world model from what actually happened.*
    # ‼‼ MEASURED ON THE FIRST LIVE DRIVE (2026-08-13): THIS FUNCTION USED TO HAND BACK AN
    # AVATAR THAT COULD NOT WALK. All four phases landed by PID, and the very next
    # `navigate_to` raised *"The player avatar is currently not controllable. Cannot navigate."*
    # The trace says why: the last thing the party menu does is re-show the START MENU
    # (`Task_ShowStartMenu` was still live at f660 of a 662-frame call), so `PartyMenuExit`
    # finishes, `plan_reorder` comes back empty, and we return True while the overworld is still
    # restoring control. `parse_start_menu()["open"]` is already False and the game state is
    # already OVERWORLD at that moment, so a caller checking either would be told everything is
    # fine. ⇒ Settle before returning, and only when we actually opened a menu, so the common
    # "already in the right order" path stays free.
    def _settle():
        if swapped:
            yield from wait_until_truly_controllable()

    failures = 0
    swapped = False
    for _pass in range(MAX_SWAPS * attempts_per_swap + 1):
        _check_abort()
        current = _party_pids()
        try:
            plan = plan_reorder(current, target_pids)
        except ValueError as error:
            raise BotModeError(f"Roster: {error}") from error
        if not plan:
            yield from _settle()
            return True  # verified in place — the party already starts with the wanted order

        if failures >= attempts_per_swap:
            console.print(
                f"[yellow]Story: roster — {failures} consecutive failed swaps; the party menu is "
                f"not doing what the plan expects (KI-38 territory). Party left as: {current}.[/]"
            )
            yield from _settle()
            return False

        destination, source = plan[0]
        console.print(
            f"[cyan]Story: roster — swapping party slots {source} <-> {destination} "
            f"({len(plan)} swap(s) still wanted).[/]"
        )

        _check_abort()
        # ‼ NEVER OPEN A MENU UNDER A FIELD SCRIPT. A trainer approach mid-menu is the exact
        # wedge `_rotate_lead_safely` exists for, and `RotatePokemon`'s loops are unbounded.
        if get_global_script_context().is_active:
            yield from _ride_out_scripted_scene("B")
            yield from wait_until_truly_controllable()
        # ‼ SET BEFORE THE DRIVE, NOT AFTER. `RotatePokemon` opens the Start menu on its very
        # first step, so even an attempt that raises has left menus on screen — and that is
        # exactly the case where the caller most needs us to settle before handing control back.
        swapped = True
        try:
            finished = yield from _yield_bounded(
                RotatePokemon(source, destination).step(), SWAP_TIMEOUT_FRAMES
            )
        except Exception as error:  # noqa: BLE001 - a wedged menu must not end the run here...
            reraise_if_aborting(error)  # ...but a WHITEOUT unwind must never be swallowed (KI-67)
            console.print(f"[yellow]Story: roster — swap attempt failed ({error!r}).[/]")
            finished = False

        # ‼‼ THE BOUND PROTECTS AGAINST HANGS, NOT AGAINST `set_manual_mode`. Four places in the
        # party-menu stack (`menuing.py:363, 380, 387`, and `PartyMenuExit`) drop the bot to Manual
        # WITHOUT raising — so `_yield_bounded` returns normally, the PID check might even pass, and
        # we would keep driving a run that is already dead. Fail honestly instead.
        if context.bot_mode == "Manual":
            raise BotModeError(
                "Roster: the party-menu navigator dropped the bot to MANUAL mid-swap (one of the "
                "menuing.py set_manual_mode paths). Not continuing against a dead run."
            )

        # ‼ VERIFY BY PID, NOT BY "the navigator finished". `finished` is kept as a DIAGNOSTIC:
        # finished=True with a failed PID check means the navigator completed and swapped the WRONG
        # PAIR (the stale-cursor bug above); finished=False means something interrupted us. Those
        # are different problems and the first drive should be able to tell them apart.
        after = _party_pids()
        if destination < len(after) and after[destination] == current[source]:
            failures = 0
            continue

        failures += 1
        console.print(
            f"[yellow]Story: roster — swap did not land (navigator {'completed' if finished else 'timed out'}); "
            f"party is now {after}.[/]"
        )
        # Close a half-open menu, ride out whatever interrupted us, then re-plan from reality.
        for _ in range(12):
            context.emulator.press_button("B")
            yield
        # ‼ The scene rider can RAISE (`_wait_until_cutscene_over` gives up after 8000 frames), and
        # a raise here would escape `reorder_party` instead of returning the truthful False this
        # function promises. A parked SELECTION submenu is the known way to reach that.
        try:
            yield from _ride_out_scripted_scene("B")
            yield from wait_until_truly_controllable()
        except Exception as error:  # noqa: BLE001
            reraise_if_aborting(error)
            console.print(f"[yellow]Story: roster — recovery ride failed ({error!r}); re-planning.[/]")

    # ‼ FALLING OUT MEANS THE PLAN NEVER CONVERGED. Report it rather than returning a bare True:
    # a reorder that keeps re-planning is a cursor that is not doing what we think.
    final = _party_pids()
    try:
        remaining = plan_reorder(final, target_pids)
    except ValueError as error:
        # ‼ SAY WHY. The first version set a magic `[(0, 0)]` sentinel here and printed a generic
        # "still N swaps short" — which would have blamed the cursor for what is actually an
        # unsatisfiable SPEC (a missing or repeated pid), sending the next reader after the wrong
        # bug. A guard that cannot tell "the menu misbehaved" from "you asked for the impossible"
        # is worse than no guard. (Caught by `repro_no_silent_except.py`, which is exactly what
        # that ratchet exists for.)
        console.print(
            f"[yellow]Story: roster — the target spec is unsatisfiable against the final party "
            f"{final}: {error}[/]"
        )
        yield from _settle()
        return False
    if remaining:
        console.print(
            f"[yellow]Story: roster — still {len(remaining)} swap(s) short after the full budget. "
            f"The party menu is not doing what the plan expects (KI-38 territory). "
            f"Party: {final}[/]"
        )
        yield from _settle()
        return False
    yield from _settle()
    return True
