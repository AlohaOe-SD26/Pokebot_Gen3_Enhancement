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

    # ‼ OFF BY DEFAULT SINCE 2026-08-05 — MEASURED TO COST MORE THAN IT SAVES.
    #
    #   batch                    PC deposits   avg team size at Feather   Balance->Feather
    #   b3/b4/b5 (feature off)             0      5.65 / 5.72 / 5.81         83 / 75 / 70%
    #   b8       (feature on)             14                    4.45                   52%
    #   b13      (feature on)             18                    4.75                   57%
    #
    # It removes ~ONE WHOLE TEAM MEMBER permanently, and the last funnel rung fell over
    # exactly that transition. A thinner team post-Norman has less depth for Winona — which
    # is the rung that collapsed.
    #
    # WHAT IT BOUGHT: the counter chain was blocked by a full party 5 times in batch5. So the
    # trade was ~1 mon of team depth on EVERY run, to unblock 5 hunts per batch. That is a bad
    # trade and the numbers were available before I built it.
    #
    # ‼ THIRD TIME IN A WEEK — see `#24-leadpolicy` (c) and `#24-areaitemgate`. All three were
    # features that REMOVE something, justified by counting what they saved and never what
    # they cost. `POKEBOT_PC_ROTATION=1` restores it.
    import os as _os

    if _os.environ.get("POKEBOT_PC_ROTATION", "0").strip() not in ("1", "true", "yes"):
        return {"deposit": [], "withdraw": [], "reasons": {}, "worth_it": False}

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
        # USER RULING 19: a mon that received a single-use gym TM this run sits at the dead-weight level boundary by
        # design (`gym_tm_teach.LEVEL_WINDOW`) — boxing it would box the TM's move with it. Until that boss is beaten.
        from modules.story.gym_tm_teach import protected_taught_pids

        protected |= protected_taught_pids(context.bot_mode_instance)
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
        # ⛔⛔ KI-81 — A WHITEOUT IS NOT "A PC FAILURE". `StoryAbort` is a `BotModeError` is an
        # `Exception`, so this handler used to swallow one and let the run walk on DEAD. The latch
        # is cleared ONLY by `StoryMode.run`, so continuing here cannot recover — it just launders
        # the cause. ‼ MUST BE THE FIRST STATEMENT (its own docstring says so) and it is LATCH-keyed,
        # not type-keyed, so it also catches an abort whose identity an inner loop already destroyed.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        # A PC failure must never destroy a successful heal. The caller re-checks the party
        # either way and the counter chain's own resource gate still reports honestly.
        console.print(
            f"[yellow]Story: PC rotation failed ({error!r}) — carrying on with the party "
            f"we have.[/]"
        )


def deposit_one_dead_weight() -> Generator:
    """Free EXACTLY ONE party slot at the Poké Centre PC. Assumes we are INSIDE a centre.

    ‼‼ WHY THIS HAS TO EXIST WHEN TWO DEPOSIT PATHS ALREADY DO (measured 2026-08-13).
    **Neither of them can free a slot BEFORE a catch**, which is exactly what
    `ensure_hm_learner` needs — it raises on a full party *before* it ever looks for a hunting
    ground (`early_game.py:4342-4348`).
      * `withdraw_from_box` (below) opens with
        `target = find_in_box(pids); if target is None: return` (:314-315). With nothing yet
        boxed it **returns having done nothing** — its deposit block is reachable only as a
        SIDE EFFECT of withdrawing an already-boxed PID.
      * `deposit_dead_weight_if_worth_it` (above) *is* a standalone one-deposit primitive, but
        routes through `plan_deposits`, whose first act is to return `worth_it: False` unless
        `POKEBOT_PC_ROTATION` is set (:83). That flag is pinned **0** and is **measured
        harmful** (~1 team member/run, a 5.4% VOID batch) — so calling it today prints nothing,
        deposits nothing and returns cleanly. **A silent no-op.**
    ‼ `04-HANDOFF.md`/KI-54 named the FIRST of those as "the path to use, live-proven". It is
    not. That claim is retracted; this function is the answer.

    ‼ THE CONTRACT IS A POSTCONDITION, NOT AN ACTION: "there is now room in the party".
    Returns **True** only after re-reading the party and seeing room — never on the strength of
    "the PC call returned". If the party already has room this is a no-op success and costs no
    PC visit at all.

    ‼ CAPPED AT ONE, DELIBERATELY. Thinning the team is what made `#24-pc` a regression
    (~1 mon/run, ~19 pts of the last funnel rung; 08-MISTAKES 2026-08-05). `find_dead_weight`
    also EXEMPTS the party's sole carrier of any HM (`team_policy.py:119-149`), so our only
    Surf user cannot be boxed by this — verified on `post_dive.ss1`: it picks Skitty L17 and
    spares Zigzagoon L15.

    Never raises. A PC hiccup returns False and the caller decides — unlike the heal
    piggybacks, whose failures must not destroy a heal that already succeeded.
    """
    from modules.console import console
    from modules.player import get_player_avatar
    from modules.pokemon_party import get_party

    def _occupied(party):
        """‼ SLOT OCCUPANCY, NOT "alive". AN EGG OCCUPIES A PHYSICAL PARTY SLOT, so it counts.

        This MUST use the same definition as the caller it exists to satisfy —
        `ensure_hm_learner` tests `len([m for m in get_party() if m is not None]) >= 6`
        (`early_game.py:4342-4343`), which includes eggs.

        ‼ IT DID NOT, AND THAT WAS A REAL BUG (found by adversarial review, 2026-08-13, before
        this ever ran against an egg). Excluding eggs meant a party of **5 mons + 1 egg** —
        FULL by the caller's test — reported *"already has room"* and returned **True having
        deposited nothing**. That is precisely the silent-no-op shape this whole function was
        written to replace, reintroduced inside the replacement. An egg cannot be deposited
        either (`team_policy.dead_weight` returns None for one), so the honest answer for that
        party is False, not True.
        """
        return [i for i, p in enumerate(party) if p is not None]

    party = get_party()
    if len(_occupied(party)) < 6:
        console.print("[green]Story: PC — the party already has room; no deposit needed.[/]")
        return True

    from modules.story.team_policy import find_dead_weight, view_from_party

    try:
        dead = find_dead_weight(view_from_party(party))  # worst-first; exempts sole HM carriers
    except Exception as error:  # noqa: BLE001 - a scoring failure must not wedge the caller
        console.print(f"[yellow]Story: PC — could not score dead weight ({error!r}).[/]")
        return False

    victim, reason = None, ""
    for index, why in dead:
        if index < len(party) and party[index] is not None:
            victim, reason = party[index], why
            break
    if victim is None:
        # ‼ SAY WHY, and say it as the FINDING it is. Every party member being worth keeping is
        # a legitimate answer, not an error — but the caller must not read it as "deposited".
        console.print(
            "[yellow]Story: PC — nothing is safe to deposit (every slot is either a sole HM "
            "carrier, a favourite, or not dead weight). The party stays full.[/]"
        )
        return False

    name = f"{getattr(victim.species, 'name', '?')} L{victim.level}"
    console.print(f"[bold cyan]Story: PC — depositing ONE mon to free a slot: {name} ({reason}).[/]")

    try:
        from modules.modes.util.pc_interaction import PCAction, interact_with_pc
        from modules.modes.util.walking import ensure_facing_direction, navigate_to

        here = get_player_avatar().map_group_and_number
        yield from navigate_to(here, PC_STAND_TILE)
        yield from ensure_facing_direction(PC_FACING)
        # ‼ Pass the OBJECT, never an index. A deposit shifts every later party index down by
        # one, which is the classic way this kind of code boxes the wrong Pokémon.
        yield from interact_with_pc([PCAction.deposit_pokemon_to_box(victim)])
    except Exception as error:  # noqa: BLE001 - report, do not wedge
        # ⛔ KI-81 — but a WHITEOUT is not a wedge to report, it is a dead run. See the rotation
        # handler above; the latch is cleared only by `StoryMode.run`.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        console.print(f"[yellow]Story: PC — the deposit failed ({error!r}).[/]")

    # ‼ VERIFY BY RE-READING THE PARTY. `interact_with_pc` returning is not proof.
    after = _occupied(get_party())
    freed = len(after) < 6
    console.print(
        f"[{'green' if freed else 'yellow'}]Story: PC — party is now {len(after)}; "
        f"room for a catch: {freed}.[/]"
    )
    return freed


# --- PC OVERFLOW (#24-pcoverflow, user ruling 2026-08-05) ------------------------------
#
# ‼ WHY. Until now a FULL PARTY meant the bot simply REFUSED to catch:
#     `resource_blocker()` -> "the party is full, so a catch would go to the PC box"
# That is what capped teams at 4 and blocked the counter chain 5 times in batch5. The user's
# ruling is to build the real thing: **let the catch happen, let it go to the box, and manage
# the box** — rather than raise a constant and hope.
#
# The decision half already existed and was never wired up: `team_policy.rotation_plan()`
# takes `box_views` and returns a `withdraw` list. Upstream already ships
# `PCAction.withdraw_pokemon_from_box()`. What was missing is the middle: READING the box, and
# EXECUTING a withdraw. That is what this section is.


def box_views():
    """`MonView`s for everything in the PC, plus the live `Pokemon` objects, in one pass.

    Returns `(views, mons)` — parallel lists, so an index from `rotation_plan`'s `withdraw`
    maps straight to the Pokémon to act on. Empty on any read failure: a box we cannot read
    is a box we must not act on.
    """
    from modules.story.team_policy import MonView

    try:
        from modules.pokemon_storage import get_pokemon_storage

        storage = get_pokemon_storage()
    except Exception:  # noqa: BLE001
        return [], []

    views, mons = [], []
    # ‼ `storage.boxes` IS A PROPERTY, NOT A METHOD. This line used to read
    # `getattr(storage, "boxes", lambda: [])()` — calling the result — and
    # `PokemonStorage.boxes` is a `@cached_property` returning a LIST
    # (`modules/pokemon_storage.py:86`), so it raised `TypeError: 'list' object is not
    # callable` on EVERY call. `find_in_box` calls this unguarded, so `withdraw_from_box`
    # could never find anything.
    #
    # ‼ THIS IS WHY `withdrawing` LOGGED 0 IN EVERY BATCH — one of two independent breaks in
    # `#24-pcoverflow` (the other: both catch-on-sight branches still required `party < 6`, so
    # a full-party catch never happened either). The defensive `getattr(..., lambda: [])`
    # DISGUISED the bug: it reads as "be safe if `boxes` is missing", and the fallback it
    # supplies is a callable, which is what made calling the real attribute look correct.
    # Proven live 2026-08-06 (`CAVE_BOXCHECK`): `boxes_type=list`, `box_views() RAISED
    # TypeError`. A defensive default that changes the SHAPE of the value is not defensive.
    for box in getattr(storage, "boxes", []) or []:
        for slot in getattr(box, "slots", []) or []:
            p = getattr(slot, "pokemon", None)
            if p is None:
                continue
            try:
                if getattr(p, "is_empty", False) or not getattr(p.species, "name", ""):
                    continue
                moves = tuple(
                    (lm.move.name, lm.move.base_power)
                    for lm in getattr(p, "moves", ()) or ()
                    if lm is not None and lm.move is not None
                )
                views.append(MonView(p.species.name, p.level, moves,
                                     is_egg=bool(getattr(p, "is_egg", False))))
                mons.append(p)
            except Exception:  # noqa: BLE001 - one unreadable slot must not lose the rest
                continue
    return views, mons


def find_in_box(pids):
    """The stored Pokémon whose personality value is in `pids`, or None.

    ‼ PID, never slot index. A box slot moves whenever anything is deposited or withdrawn, so
    a remembered index points at a different Pokémon later — the same hazard that made the
    deposit path resolve objects up front.
    """
    if not pids:
        return None
    _, mons = box_views()
    for mon in mons:
        try:
            if mon.personality_value in pids:
                return mon
        except Exception:  # noqa: BLE001
            continue
    return None



def party_has_room_for_withdraw(party) -> bool:
    """Is there a free party slot for a withdraw — **by the predicate the WITHDRAW ITSELF USES**?

    ⛔⛔ **EGGS COUNT, AND THAT IS THE ENTIRE POINT (KI-102).** The consumer of this decision is
    `pc_interaction._do_withdraw_actions`, which refuses with
    *"Cannot withdraw any Pokémon because the party already contains 6 Pokémon"* when
    `get_party_size() == 6` — and `get_party_size()` is literally `len(get_party())`
    (`modules/pokemon_party.py`), which counts an egg like any other slot.

    ‼ **THIS IS THE CALLER'S PREDICATE COPIED VERBATIM, NOT AN EQUIVALENT-LOOKING ONE**, and the
    distinction is the whole bug. `withdraw_from_box` used to ask `not is_egg`, so a party of
    **5 mon + 1 egg** read as "room available", no deposit was queued, and the withdraw then RAISED
    — after the PC journey had already been spent.
    ⭐ It is the same defect `08-MISTAKES.md` records in `deposit_one_dead_weight`, caught there by
    adversarial review *before it ever met an egg*: *"'Alive' and 'occupies a slot' differ by
    exactly one case — an egg — and that case is invisible until it happens."*

    ⚠ **NO `p is not None` FILTER, DELIBERATELY.** `get_party_size()` does not filter either; it is
    `len(get_party())`. Adding a filter here would make this an *equivalent-looking* predicate again
    — the exact thing the rule above forbids — and would differ from the consumer on any list that
    ever did contain a `None`.

    PURE: takes the party list, touches no emulator state, returns a bool. Gated by
    `repro_withdraw_room.py`.
    """
    return len(party or []) < 6


def withdraw_from_box(pids) -> Generator:
    """Retrieve a Pokémon from the PC box by PID, making room if the party is full.

    ‼ THIS IS THE OTHER HALF OF `#24-pcoverflow`. `resource_blocker` no longer refuses a catch
    when the party is full, so a hunted counter can now land in the BOX. Without this it would
    stay there — caught, paid for with a cross-Hoenn journey, and unusable. That is strictly
    worse than the old refusal, so the two changes must ship together.

    Assumes we are INSIDE a Poké Centre and healed (same piggyback contract as
    `deposit_dead_weight_if_worth_it`). Never raises **for a PC hiccup**: that must not destroy a
    heal that already succeeded.

    ⛔ **ONE EXCEPTION, ADDED 2026-08-16 (KI-81 / `#24-orphans` P4): A WHITEOUT PROPAGATES.**
    `StoryAbort` is a `BotModeError` is an `Exception`, so the blanket handler below used to
    swallow one and the run walked on DEAD. A whiteout is not a hiccup — the player has respawned
    elsewhere, there is no heal left to protect, and the abort latch is cleared ONLY by
    `StoryMode.run`, so continuing here cannot recover; it only launders the cause into a
    confident, plausible, wrong one. ‼ The contract is therefore *"never raises for a PC problem"*,
    not *"never raises"*, and this docstring moved in the same edit as the code.

    ⛔⛔ **RETURNS `(landed: bool, code: str)` — ADDED 2026-08-17 (`#24-orphans` (1)). BEFORE THIS,
    EVERY EXIT RETURNED `None`.** KI-79 made this function *say* the truth on the console; the
    caller still could not *read* it, so nothing downstream could ever act on a failed withdraw.
    Every exit was bare, which means "the counter is in the party", "there was nothing to collect"
    and "the withdraw did not land" were the SAME value to `yield from`.

    ‼ **THE CODE DISTINGUISHES "ATTEMPTED AND FAILED" FROM "NEVER ATTEMPTED", and that distinction
    is the point.** Collapsing the no-attempt cases into a plain failure would manufacture one out
    of the commonest case — most heals have nothing to collect — which is the same shape as the
    count-based lie KI-79 removed. `landed` answers ONLY *"is the counter usable this fight?"*:
        `(True,  "landed", name)`                in the party AND gone from the box (both halves)
        `(False, "not_in_box", detail)`          nothing matching the PIDs was there — NO attempt
        `(False, "party_full_no_deposit", name)` declined: full party, nothing safe to deposit — NO attempt
        `(False, "did_not_land", detail)`        ATTEMPTED and it failed; the counter is still boxed
        `(False, "error", repr(error))`          ATTEMPTED and it threw a non-abort error
    ‼ THE THIRD FIELD IS `detail`, AND IT IS THE SHAPE THE RECORDED DESIGN ASKS FOR
    (`06-DECISIONS-LOG.md`: *"returns a verdict `(ok, CODE, detail)`"*). It is free text TODAY.
    ⛔ It is NOT the failure taxonomy: `PARTY_FULL`/`BOX_FULL`/… must be READ from the PC message
    buffer, whose offset is UNMEASURED, so classifying here would be inferring a reason from
    internal state — the exact error class KI-79 removed. Shipping the third field now means the
    classifier can fill it without changing this contract a second time.
    ⛔ **A WHITEOUT STILL PROPAGATES AND YIELDS NO VERDICT AT ALL** — there is no run left to report
    to, and inventing a `False` here would let a caller "handle" a dead run.
    ⛔ **THIS FUNCTION DECIDES NOTHING NEW.** Reporting is the caller's job; REACTING is the USER's
    call (`06-DECISIONS-LOG.md`), and a verdict must not quietly become a retry loop.
    """
    from modules.console import console
    from modules.context import context
    from modules.player import get_player_avatar
    from modules.pokemon_party import get_party

    target = find_in_box(pids)
    if target is None:
        # ⛔ NOT a failure: most heals have nothing to collect. The caller must be able to tell
        # this from a withdraw that was tried and did not land — see the verdict table above.
        return False, "not_in_box", f"{len(pids or ())} hunted PID(s), none of them in the box"

    name = getattr(getattr(target, "species", None), "name", "?")
    try:
        from modules.modes.util import wait_for_n_frames
        from modules.modes.util.pc_interaction import PCAction, interact_with_pc
        from modules.modes.util.walking import ensure_facing_direction, navigate_to
        from modules.pokemon_storage import get_pokemon_storage

        party = get_party()
        # ⛔ KI-102: ROOM IS DECIDED BY THE CONSUMER'S PREDICATE, NOT AN EGG-FILTERED LOOKALIKE.
        # This used to be `alive = [... not is_egg]` and `if len(alive) >= 6`, so a party of
        # 5 mon + 1 egg read as "room available", no deposit was queued, and
        # `_do_withdraw_actions` then RAISED "already contains 6" — after the PC journey was
        # already spent. The egg-filtered list is GONE rather than kept: it had exactly one
        # reader, and a variable retained "for logging" that nothing logs is how a false comment
        # gets written. See `party_has_room_for_withdraw`.

        actions = []
        # ‼ MAKE ROOM FIRST, AND ONLY IF FULL. A withdraw into a full party silently fails, so
        # the deposit must be part of the SAME PC visit. We free exactly one slot — the worst
        # dead weight — never more: thinning the team is what made `#24-pc` a regression
        # (~1 mon/run, ~19 pts of the last funnel rung; 08-MISTAKES 2026-08-05).
        if not party_has_room_for_withdraw(party):
            from modules.story.team_policy import find_dead_weight, view_from_party

            worst = None
            try:
                dead = find_dead_weight(view_from_party(party))  # worst-first
                for i, _reason in dead:
                    if i < len(party) and party[i] is not None:
                        if party[i].personality_value in (pids or ()):
                            continue  # never deposit the very mon we came to collect
                        worst = party[i]
                        break
            except Exception:  # noqa: BLE001
                worst = None
            if worst is None:
                console.print(
                    f"[yellow]Story: {name} is in the PC but the party is full and nothing is "
                    f"safe to deposit — leaving it boxed.[/]"
                )
                # A DELIBERATE DECLINE, not a failed withdraw: thinning the team is what made
                # `#24-pc` a regression, so refusing here is correct behaviour, not an error.
                return False, "party_full_no_deposit", name
            console.print(
                f"[cyan]Story: PC — depositing {getattr(worst.species, 'name', '?')} "
                f"L{worst.level} to make room for {name}.[/]"
            )
            actions.append(PCAction.deposit_pokemon_to_box(worst))

        console.print(f"[bold cyan]Story: PC — withdrawing {name} from the box.[/]")
        actions.append(PCAction.withdraw_pokemon_from_box(target))

        here = get_player_avatar().map_group_and_number
        yield from navigate_to(here, PC_STAND_TILE)
        yield from ensure_facing_direction(PC_FACING)

        # ⛔ FAULT INJECTION (KI-79, permanent hook — never edit code to inject a fault).
        # `POKEBOT_PCWITHDRAW_FAULT=1` SKIPS the PC interaction entirely, so the withdraw
        # provably does not happen while everything around it still runs. It exists because the
        # verification below is an ERROR PATH, and a green happy-path run cannot exercise an
        # error path — before this hook, "the mon arrived" and "we never even tried" produced
        # the SAME green line. Read INSIDE the function, never at import.
        import os as _os

        if _os.environ.get("POKEBOT_PCWITHDRAW_FAULT", "0") == "1":
            console.print(
                "[magenta]Story: PC — ‼ POKEBOT_PCWITHDRAW_FAULT=1, SKIPPING the PC interaction "
                "on purpose. The withdraw will NOT happen; the check below must say so.[/]"
            )
        else:
            yield from interact_with_pc(actions)

        # ‼‼ KI-79 — VERIFY BY IDENTITY, NEVER BY COUNT. This block used to be:
        #       after = len(get_party())
        #       console.print(f"... {name} is in the party; party is now {after}.")
        #   which reads a COUNT and announces an IDENTITY. It could not fail: on the make-room
        #   path the deposit CANCELS the withdraw, so the count is UNCHANGED on success
        #   (measured: party 6 -> 6, box 2 -> 2), and it is equally unchanged when nothing
        #   happened at all. Combined with the blanket `except` below — which means this
        #   function NEVER RAISES — a silent PC failure printed a green success.
        # ⛔ Do NOT "fix" this by asserting the count CHANGED: on the make-room path it correctly
        #   does not. The count stays in the message as colour, never as evidence.
        # ‼ The party and the storage are cached PER FRAME, so a same-frame read after the PC
        #   interaction can still see the PRE-withdraw state. Yield before reading, or the
        #   verification itself becomes the new false negative.
        yield from wait_for_n_frames(2)

        # Identity = (personality_value, species) — ⛔ NOT the PID alone. A Shedinja carries its
        # Ninjask's PID (KI-78), so a bare-PID check is a latent collision bug.
        target_key = (target.personality_value, getattr(target.species, "name", None))
        in_party_now = any(
            (p.personality_value, getattr(p.species, "name", None)) == target_key
            for p in get_party()
            if p is not None
        )
        still_boxed = get_pokemon_storage().contains_pokemon(target)
        after = len(get_party())

        if in_party_now and not still_boxed:
            # BOTH halves: in the party AND gone from the box. Either alone is not a move —
            # in-party-only could be a copy, gone-from-box-only could be a release.
            console.print(f"[green]Story: PC — {name} is in the party; party is now {after}.[/]")
            context.message = f"Story: withdrew {name} — party {after}."
            return True, "landed", name
        else:
            # ‼ LOUD, NAMED, and it does NOT raise — the heal that already succeeded must survive
            # (same contract as before). What changes is that the caller is no longer LIED TO.
            console.print(
                f"[bold red]Story: PC — ‼ THE WITHDRAW DID NOT LAND. {name} "
                f"in_party={in_party_now} still_boxed={still_boxed} (party is {after}). "
                f"The counter is NOT usable this fight; this used to print as a SUCCESS.[/]"
            )
            context.message = f"Story: withdraw of {name} FAILED — it is still boxed."
            # ‼ THE ONE THE CALLER COULD NOT SEE. KI-79 made this branch SAY the truth; this
            # return is what finally lets something downstream READ it.
            return False, "did_not_land", (f"{name} in_party={in_party_now} still_boxed={still_boxed}")
    except Exception as error:  # noqa: BLE001
        # ⛔⛔ KI-81 / `#24-orphans` P4 — THE ONE EXCEPTION TO "NEVER RAISES", AND IT IS NOT A
        # HICCUP. A whiteout means the run is over and the player has respawned elsewhere; there is
        # no heal left to protect, and swallowing it lets the bot keep driving a PC menu that is no
        # longer on screen. Latch-keyed, so it also catches an abort already laundered into a plain
        # `BotModeError` by an inner loop.
        from modules.story.early_game import reraise_if_aborting

        reraise_if_aborting(error)
        console.print(
            f"[yellow]Story: could not withdraw {name} ({error!r}) — it stays in the box.[/]"
        )
        # ⛔ Reached ONLY for a genuine PC hiccup: `reraise_if_aborting` above has already let a
        # whiteout through, and a dead run gets no verdict at all (KI-81).
        return False, "error", repr(error)
