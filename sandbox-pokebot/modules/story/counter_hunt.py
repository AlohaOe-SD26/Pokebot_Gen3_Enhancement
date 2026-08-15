"""Counter-species EXECUTOR — punch-list #24-counters phase 2, step 2.

`counter_plan` decides WHERE the answer to a boss lives; this module goes and gets it.
The split is deliberate and predates this file: `counter_plan`'s own docstring says
"PLANNING ONLY ... mixing planning with execution would make neither testable in
isolation." Planning stays pure and ROM-data-driven; everything that walks, presses a
button or spends a Poké Ball lives here.

THE PROBLEM THIS SOLVES. `_boss_plan_is_hopeless` correctly detects "no super-effective
answer to this boss", `counter_plan` correctly names one, and then the run ENDED — about
72% of all derails in the 2026-07-29 batch were this chain diagnosing itself to death
(Electric->needs Ground x17, Normal->needs Fighting x9, Winona x3).

THE THREE RUNGS (spec: `21-TEAM-POLICY-DESIGN.md` §5), each bounded, each falling
through to the SAME terminal raise:

  1. ARM      -- publish the target species to `COUNTER_CATCH_TARGET_DEX`, which
                 `StoryMode.on_battle_started` consults to catch them ON SIGHT. Mirrors
                 `early_game.HM_CATCH_TARGET_DEX` exactly, including its consumer's shape.
  2. HUNT     -- travel to the candidate's proven hunting tile and spin until one is
                 caught or the budget expires.
  3. TRAIN    -- bring the catch up to the team, because a counter that cannot survive
                 the boss is not an answer.

‼ RUNG 3 IS NOT OPTIONAL GARNISH. Catch a L15 Machop for a L30 team and leave it
untrained, and `_boss_plan_is_hopeless` answers "not hopeless" for ever after -- the
party now HAS a Fighting move, so the diagnosis that used to stop the run stops firing.
Today's bounded, honest stop would become an unbounded loop that only the 5M-frame run
budget ends. Bound the OUTCOME, not the frames (`14-AGENT-PLAYBOOK.md` rule 3).

‼ NEVER pick a destination with `candidates[0]`. Use `counter_plan.best_huntable()`.
The cost model prices "train it up to the team's level" at ~0 for a wild ALREADY ABOVE
the team, so it ranks endgame maps as CHEAPEST -- rank 1 for Norman is a Victory Road
Hariyama L38-42 (measured 2026-07-30). `best_huntable` applies the fail-closed
hunting-ground whitelist; ranking answers "which is cheapest", never "may I go there".
"""

from __future__ import annotations

import logging
from typing import Generator

_log = logging.getLogger("story_counter_hunt")


#: Species dex numbers the story's catch branch should catch ON SIGHT right now (a
#: counter hunt is in progress). Read by `StoryMode.on_battle_started`; empty = inactive.
#: ‼ Module state on purpose, exactly like `early_game.HM_CATCH_TARGET_DEX` — the battle
#: callback has no clean path to the hunt's local scope. It MUST be cleared in a
#: `finally`, or a finished hunt keeps spending balls on Machop for the rest of the run.
COUNTER_CATCH_TARGET_DEX: set[int] = set()

#: Human-readable names of what is armed, for logging only.
COUNTER_HUNT_TARGET_NAMES: list[str] = []

#: Frames to spin on the hunting ground before giving up on the catch. Sized against the
#: measured cost of the alternative, not guessed: Norman's Machop sits at a 15% encounter
#: slot on FIERY_PATH and a wild battle measures 1,433 frames (`FRAMES_PER_WILD_BATTLE`),
#: so meeting one costs ~9,600 frames on average and this allows roughly 12 expected
#: meetings plus catch failures. For scale, run05 spent ~399,000 frames LOSING to Norman
#: 21 times, so even a total failure here is cheap by comparison.
HUNT_SPIN_BUDGET_FRAMES = 120_000

#: How far above the fresh catch's own level we are willing to train it. The catch is a
#: TYPE answer, not a level answer — it does not need to out-level the boss, it needs to
#: land a super-effective hit and survive one. Kept as a gap from the TEAM's level rather
#: than an absolute so it scales across the game.
TRAIN_TO_TEAM_GAP = 2


def is_armed() -> bool:
    """Is a counter hunt currently publishing catch-on-sight targets?"""
    return bool(COUNTER_CATCH_TARGET_DEX)


def arm(species_names) -> set:
    """Publish `species_names` as catch-on-sight targets. Returns the dex-number set.

    Fail-safe: an unresolvable name is skipped rather than raising — arming a partial
    target list is strictly better than aborting a hunt the run needs.
    """
    global COUNTER_CATCH_TARGET_DEX, COUNTER_HUNT_TARGET_NAMES
    dex: set[int] = set()
    names: list[str] = []
    try:
        from modules.pokemon import get_species_by_name

        for name in species_names or []:
            try:
                dex.add(get_species_by_name(name).national_dex_number)
                names.append(name)
            except Exception:
                _log.warning("counter hunt: cannot resolve species %r — skipping", name)
    except Exception as error:
        _log.warning("counter hunt: arm failed (%s)", error)
    COUNTER_CATCH_TARGET_DEX = dex
    COUNTER_HUNT_TARGET_NAMES = names
    return dex


def disarm() -> None:
    """Stop catching hunt targets on sight. MUST be called from a `finally`."""
    global COUNTER_CATCH_TARGET_DEX, COUNTER_HUNT_TARGET_NAMES
    COUNTER_CATCH_TARGET_DEX = set()
    COUNTER_HUNT_TARGET_NAMES = []


def party_counter_slot(needed_type_names, exclude_pids=None) -> "int | None":
    """Party slot of a battle-capable mon whose OWN type is one of `needed_type_names`,
    or None. This is how the hunt knows it succeeded.

    ‼ NOT a re-implementation of `_boss_plan_is_hopeless`. That function asks the harder
    question ("do we have a CREDIBLE super-effective move right now?") and a freshly-caught
    L15 Machop may well fail it until it grows into its moves — which is precisely why rung 3
    exists. Using the strict test here would make a successful catch look like a failed hunt.

    ‼‼ IT ALSO ACCEPTS A MOVE ANSWER (fixed 2026-08-08). This used to test the mon's OWN TYPE
    only, and the docstring said so deliberately — which was right while every candidate WAS a
    type match, and became wrong the moment `#24-movepoolcounters` let the planner hunt a
    species that merely LEARNS a counter-type move.

    MEASURED, batch `20260808-131334`: the Winona rung fired 5 times, reached Fiery Path, and
    **encountered Slugma 34 times** (9.3% of 365 encounters there — exactly its 10% slot) while
    `counter hunt CAUGHT Slugma` stayed at **0**. Slugma is FIRE; Winona needs Rock/Ice/Dragon.
    So catch-on-sight caught it, this function did not recognise it, `_stop()` never fired, the
    spin ran to budget and the hunt reported nothing caught. In the same batch Machop (a TYPE
    match) converted 6 of 64 encounters and Numel 3 of 112 — so it was never the spin or the rate.
    **I taught the planner about movepools and left the success test behind; this is that half.**

    The move test stays LENIENT on purpose, matching the paragraph above: it asks only that the
    mon KNOW a damaging move of a needed type, not that the move clear the credible-power floor.
    A freshly caught L15 Slugma already knows Rock Throw, which is exactly the case that has to
    register as success.
    """
    try:
        from modules.pokemon_party import get_party

        needed = {str(n) for n in (needed_type_names or []) if n}
        if not needed:
            return None
        skip = set(exclude_pids or ())
        for index, mon in enumerate(get_party()):
            if mon is None or mon.is_egg:
                continue
            # ‼‼ IGNORE MONS THAT WERE ALREADY IN THE PARTY WHEN THE HUNT ARMED (2026-08-08).
            # This is the exact protection `before_box_pids` already gives the BOX side, and the
            # party side went without it. Measured cost in batch `20260808-174145`: **20 hunts,
            # 13 reported catches, only 3 real** — Marshtomp 6, Castform 3 and Combusken 1 were
            # "caught" without ever being hunt targets, and **Machop fell from 6-of-8 to 0-of-7**
            # because the hunt "succeeded" on a party mon before the Machop was ever caught.
            #
            # WHY IT ONLY BROKE NOW: the old test matched the mon's own TYPE, and a party mon of
            # the needed type would have made `_boss_plan_is_hopeless` return False so no hunt
            # would fire at all — the guard was implicit. Making the test accept a MOVE answer
            # (`#24-slugmaspin`) removed that accident, because `hopeless` uses the STRICT
            # credible-power test while this one is deliberately lenient: a mon carrying a
            # 20-power Rock Smash is "hopeless" to that function and "success" to this one.
            # Two tests with different thresholds over the same party need an explicit fence.
            try:
                if mon.personality_value in skip:
                    continue
            except Exception:  # noqa: BLE001
                pass
            try:
                if {t.name for t in mon.species.types} & needed:
                    return index
                # MOVE ANSWER: a damaging move of a needed type counts, even when the mon's own
                # type does not. Damaging only — a status/stat-change move answers nothing.
                for learned in (mon.moves or ()):
                    if learned is None or learned.move is None:
                        continue
                    if learned.move.base_power > 0 and learned.move.type.name in needed:
                        return index
            except Exception:
                continue
        return None
    except Exception as error:
        _log.warning("party_counter_slot failed: %s", error)
        return None


def _party_count() -> int:
    try:
        from modules.pokemon_party import get_party

        return len([m for m in get_party() if m is not None])
    except Exception:
        return 6  # fail-safe: assume FULL, so a read error never starts a doomed hunt


def _box_count() -> int:
    """How many Pokémon are in the PC, across all 14 boxes.

    ‼ WHY THIS EXISTS (`#24-pcoverflow`, wired 2026-08-06). With a FULL party the game sends a
    catch straight to the PC (`GiveMonToPlayer` -> `CopyMonToPC`, no prompt), so `_party_count()`
    does NOT change and the hunt's old success test could never see the catch. Measured
    consequence: `withdrawing` logged **0 times** in every batch — not bad luck, a disconnected
    path. The hunt travelled, armed, spun the full 120,000-frame budget, caught the counter into
    the box, and reported "found nothing".

    Fail-safe direction is the OPPOSITE of `_party_count()`'s: an unreadable box must read as
    UNCHANGED (so a read error cannot fake a success), whereas an unreadable party reads as FULL
    (so a read error cannot start a doomed hunt). Both choices fail toward "do less".
    """
    try:
        from modules.pokemon_storage import get_pokemon_storage

        return int(get_pokemon_storage().pokemon_count)
    except Exception:
        return -1  # unreadable -> callers treat as "no change"


def _box_pids() -> frozenset:
    """Every personality value currently in the PC. Used to snapshot the box BEFORE a hunt so
    a pre-existing stored mon cannot be mistaken for this hunt's catch.

    Returns an EMPTY set when unreadable — combined with `_box_count()`'s -1, an unreadable PC
    means the box path simply never claims a success. Both fail toward "do less".
    """
    out = set()
    try:
        from modules.pokemon_storage import get_pokemon_storage

        for box in get_pokemon_storage().boxes:
            for slot in box.slots or []:
                mon = getattr(slot, "pokemon", None)
                pid = getattr(mon, "personality_value", None) if mon is not None else None
                if pid is not None:
                    out.add(pid)
    except Exception:
        return frozenset()
    return frozenset(out)


def box_counter_pid(needed_type_names, exclude_pids=frozenset()) -> "int | None":
    """PERSONALITY VALUE of a mon IN THE PC that answers the boss — BY TYPE **OR BY MOVE** — or None.

    The box-side twin of `party_counter_slot`, and deliberately keyed on PID rather than
    (box, slot): `pc_trip.withdraw_from_box(pids)` already finds a stored mon by PID, and box
    indices shift as mons are added or removed.

    ‼‼ IT ACCEPTS A MOVE ANSWER (fixed 2026-08-14). This docstring used to say *"Same
    TYPE-not-moves test as the party version"* — and that was WRONG, not a deliberate choice.
    `party_counter_slot` was taught the move test on 2026-08-08 (`#24-slugmaspin`); **this twin
    was left behind, and the fix that named Slugma in its own docstring did not reach the half
    that handles a Slugma caught into the BOX.**

    MEASURED LIVE by the user, 2026-08-14 — the whole failure falls out of this one function:
    a Winona hunt caught **Slugma into the PC box** (the party was full because a Nincada had
    evolved and SPAWNED a Shedinja into the last slot). Winona needs Rock/Ice/Dragon/Electric;
    Slugma is **pure FIRE** and was hunted for its **Rock Throw**. Type-only ⇒ this returned
    None ⇒ `hunt()` reported "found nothing" ⇒ `_hunted_counter_pids` stayed empty ⇒ the heal's
    withdraw block (`higher_level_actions.py:246`, gated `if _pids:`) had nothing to do ⇒ the
    ladder raised and the run dropped to Manual ⇒ on continue, `_counter_hunts` said "already
    hunted" and the gym was re-fought with the counter still in the box.

    ‼ THE PAIR IS NOW GATED, because prose did not catch the first drift:
    `tools/story-dev/repro_box_counter_move_test.py` asserts this test and `party_counter_slot`
    accept the SAME set, and it is fault-tested (its ARM A reproduces the type-only behaviour and
    must fail to see the Slugma, or the repro is not measuring anything).

    The move test is LENIENT on purpose, exactly as the party twin's is: it asks only that the mon
    KNOW a **damaging** move of a needed type, not that the move clear the credible-power floor.
    A freshly caught L15 Slugma already knows Rock Throw, and that is the case that must register.
    ⚠ A boxed mon has no readable HP/status (those live past byte 80 of the 80-byte box record),
    so "can it survive a hit" is unanswerable here by construction — level and moves are all there
    is, which is another reason the strict test does not belong on this side.
    """
    try:
        import os as _os

        from modules.pokemon_storage import get_pokemon_storage

        needed = {str(n) for n in (needed_type_names or []) if n}
        if not needed:
            return None
        # ‼ `boxes` is a PROPERTY (no parens) and `box.slots` holds `PokemonStorageSlot`
        # WRAPPERS, not Pokémon — the mon is `slot.pokemon`. Getting either wrong is silent
        # here: this whole function is inside a `try`, so a TypeError/AttributeError would
        # just return None and read as "no counter in the box". `pc_trip.box_views` shipped
        # with exactly that bug (calling the property) and it is why `withdrawing` was 0.
        for box in get_pokemon_storage().boxes:
            for slot in box.slots or []:
                mon = getattr(slot, "pokemon", None)
                if mon is None or getattr(mon, "is_egg", False):
                    continue
                pid = getattr(mon, "personality_value", None)
                if pid is None or pid in exclude_pids:
                    continue
                if {str(t.name) for t in mon.species.types} & needed:
                    return pid
                # MOVE ANSWER — the half this function was missing until 2026-08-14. A damaging
                # move of a needed type counts even when the mon's own type does not; that is the
                # whole point of `#24-movepoolcounters`, which lets the planner hunt a species
                # that merely LEARNS the answer. Damaging only: a status/stat-change move answers
                # nothing, which is why `base_power > 0` is required and not merely the type.
                # ‼ Kept structurally identical to `party_counter_slot`'s loop (`:169-173`) on
                # purpose — these two are a pair, they drifted once, and the parity gate now
                # asserts they accept the same set.
                #
                # ⛔ FAULT INJECTION — `POKEBOT_BOXCOUNTER_TYPEONLY_A=1` RESTORES THE PRE-2026-08-14
                # TYPE-ONLY BEHAVIOUR by skipping this loop, so the user-observed Slugma/Winona
                # derail can be reproduced ON DEMAND without reverting code. Default (unset) = the
                # fix. This is a PERMANENT, DOCUMENTED HOOK, not a temporary edit: "the error
                # stopped" is not proof a fix worked; an arm that reproduces the bug on request is
                # (the `POKEBOT_LEADCANTBATTLE_A` precedent, `battle_strategies/default.py:328`).
                # ‼ READ INSIDE THE FUNCTION, never at import: a module-scope read is unresettable
                # within a process and silently ignores a driver that sets the variable after
                # import (`training_areas.py:432` is that anti-pattern).
                if _os.environ.get("POKEBOT_BOXCOUNTER_TYPEONLY_A", "0") == "1":
                    continue
                for learned in (getattr(mon, "moves", None) or ()):
                    if learned is None or getattr(learned, "move", None) is None:
                        continue
                    move = learned.move
                    if move.base_power > 0 and str(move.type.name) in needed:
                        return pid
    except Exception:
        return None
    return None


def catch_confirmed(*, party_count_now, party_count_before, party_pids_now, before_party_pids,
                    box_count_now, box_count_before, box_pids_now, before_box_pids) -> bool:
    """Did THIS hunt actually catch something? A COUNT is the trigger; an IDENTITY is the verdict.

    ‼ EXTRACTED FROM `hunt()._stop()` 2026-08-14 SO IT CAN BE PROVEN. The logic was a closure and
    therefore untestable, which meant the Shedinja fix below was *reasoned* rather than *proven* —
    and this project's first rule is that a fix you cannot demonstrate is a hypothesis. It is now
    covered by `tools/story-dev/repro_box_counter_move_test.py`, including the laziness property.

    ‼ WHY IDENTITY. A Nincada evolving at L20 **SPAWNS A SHEDINJA into a free party slot**
    (`CreateShedinja`, `src/evolution_scene.c:548-583`) with no catch, no ball and no bot action —
    in Gen 3 the ONLY precondition is a free slot (there is NO spare-ball rule; that is Gen 4+, and
    our own `obtainability.py:88` display string is wrong about it). A bare count delta therefore
    reports a catch that never happened, ending the spin with nothing caught.
    ✅ And the Shedinja case resolves correctly *because* `CopyMon` is a memcpy that does not
    overwrite personality: the twin carries its Ninjask's PID, so it can never look like a NEW
    identity. (That PID sharing is a hazard elsewhere — see KI-78 — but here it is exactly right.)

    ‼ `party_pids_now` and `box_pids_now` are CALLABLES, and that is load-bearing, not style.
    The caller runs this on EVERY frame of a 120,000-frame spin; reading every party PID (and worse,
    iterating 14x30 box slots) per frame would be a real regression. They are invoked ONLY on the
    branch where the cheap count has already moved.
    ⚠ HONEST COST NOTE (adversarial review, 2026-08-14): once the count has risen it STAYS risen,
    so on a spawn-then-keep-hunting spin the party callable runs on every subsequent frame, not
    once. That is <=6 party members and is accepted; the earlier comment here claimed "pays ONCE"
    and was simply wrong — the code wins, the comment was the bug.
    """
    if party_count_now > party_count_before:
        if party_pids_now() - before_party_pids:
            return True
        # Count rose, no new identity => an evolution spawn, not a catch. Keep hunting.
    # A box catch is a SUCCESS, not a miss. `_box_count()` returns -1 when unreadable, so the
    # `>= 0` guard keeps a read error from faking one — and it does double duty, because an
    # unreadable SNAPSHOT would otherwise make every stored mon look new.
    if box_count_before >= 0 and box_count_now > box_count_before:
        if box_pids_now() - before_box_pids:
            return True
    return False


def _ball_count() -> int:
    try:
        from modules.items import get_item_bag

        return sum(slot.quantity for slot in get_item_bag().poke_balls)
    except Exception:
        return 0


def resource_blocker() -> "str | None":
    """Why NO hunt can be attempted right now, regardless of destination — or None.

    ‼ Kept separate from `destination_blocker` because the two have different
    consequences for the ladder's fallback loop: a resource wall applies to every
    candidate, so trying the next destination is pure waste and the ladder must stop
    immediately; a destination problem applies to ONE place, so the ladder should move
    down its ranked list. Collapsing them into one predicate (as this module originally
    did) makes "the party is full" and "that one tile is unreachable" indistinguishable.

    Both walls below are real derail classes from the 2026-07-29 batch (`#24-pc`, and
    "no Poké Balls and no money to buy any"), not hypotheticals.
    """
    # ‼ #24-pcoverflow (user ruling 2026-08-05) — A FULL PARTY NO LONGER REFUSES THE CATCH.
    #
    # This used to `return "the party is full, so a catch would go to the PC box (needs
    # #24-pc)"`, and that refusal fired 5 times in batch5, blocking the counter chain outright.
    # The ruling was to build the real thing rather than raise a constant: **let the catch
    # happen, let it land in the box, and retrieve it** — see `pc_trip.withdraw_from_box`.
    #
    # A caught-to-box counter is not lost: `_hunted_counter_pids` records it by PID (which
    # survives the box), `pc_trip.find_in_box` locates it, and the next Poké Centre heal
    # withdraws it. The mon being in the box is a LOGISTICS problem, not a reason to skip the
    # only answer to a boss we keep losing to.
    #
    # ‼ What is still true: a catch needs a BALL. That gate stays below, unchanged.
    # > 1 rather than > 0: the LAST ball is reserved, the same rule the HM hunt uses.
    # Randomising or relaxing this reintroduces the catch-without-balls bug
    # (21-TEAM-POLICY-DESIGN.md §6 lists it as never-randomise).
    if _ball_count() <= 1:
        return "no spare Poké Balls (the last ball is reserved)"
    return None


def destination_blocker(candidate) -> "str | None":
    """Why THIS destination cannot be hunted, or None. Per-candidate: the ladder may try
    the next one down its ranked list."""
    if candidate is None or candidate.get("hunt_tile") is None:
        return "no huntable counter candidate (nothing reachable with a proven spin tile)"
    return None


def hunt_blockers(candidate) -> "str | None":
    """Both gates in one call — the single-destination entry point. Destination first, so
    the caller sees the most specific reason."""
    return destination_blocker(candidate) or resource_blocker()


def hunt(candidate, needed_type_names) -> Generator:
    """Travel to `candidate`'s hunting ground and spin until one is caught.

    ‼ RETURN CONTRACT CHANGED 2026-08-06 (`#24-pcoverflow` break 2). Was a bare party slot
    (`int | None`); is now `dict | None`:
        `{"slot": int,  "pid": int}`   caught into the PARTY  — train it, as before
        `{"slot": None, "pid": int}`   caught into the PC BOX — party was full; the PID is
                                       registered and `pc_trip.withdraw_from_box` collects it
                                       at the next heal. It CANNOT be trained while boxed.
        `None`                         the hunt ran out of budget and caught nothing.
    The dict is deliberate rather than a magic slot value: a boxed catch has no party slot, and
    a sentinel int would be indexed by the caller sooner or later. There is exactly one caller
    (`StoryMode._counter_ladder`), so widening the contract is cheap and explicit.

    Raises nothing that the caller has not already been given a chance to avoid — check
    `hunt_blockers` first.

    ‼ Shape cloned from `early_game.ensure_hm_learner`, which is the working precedent
    for "go and catch a specific species": provision balls -> navigate -> arm -> bounded
    spin -> disarm in a `finally` -> hand back a CLEAN overworld. The last step is not
    cosmetic: the spin stops the FRAME the catch registers, so the nickname YES/NO prompt
    is still on screen, and the caller's next menu action would open underneath it
    (ch13_run1 wedged on exactly that).
    """
    from modules.console import console
    from modules.context import context
    from modules.story.early_game import (
        _navigate_riding_out,
        _story_spin,
        normalize_to_overworld,
        provision_poke_balls,
        wait_until_truly_controllable,
    )

    map_enum = candidate["map_enum"]
    tile = tuple(candidate["hunt_tile"])
    species_name = candidate["species_name"]

    console.print(
        f"[bold cyan]Story: counter hunt — going to {map_enum.name} {tile} to catch "
        f"{species_name} ({'/'.join(candidate.get('types', []))}), "
        f"L{candidate.get('level_band')}, {candidate.get('encounter_rate')}% slot.[/]"
    )
    context.message = f"Story: hunting {species_name} on {map_enum.name}…"

    if _ball_count() <= 1:
        yield from provision_poke_balls()
        if _ball_count() <= 1:
            console.print("[yellow]Story: counter hunt abandoned — could not buy Poké Balls.[/]")
            return None

    # ‼ MORE TRIES THAN THE DEFAULT 10, and this is not a "just retry harder" band-aid.
    # A counter hunt is the LONGEST journey the bot ever makes: measured 2026-07-31, the
    # Norman ladder fires at PETALBURG_CITY and Fiery Path is 8 map-hops away across
    # several warp chains (Petalburg Woods, Rustboro, Route 116…). `navigate_to_anywhere`'s
    # staged progress crosses those one warp at a time, and each leg that ends in a
    # recoverable error costs one try — so a run of 10 was being exhausted WHILE THE BOT WAS
    # STILL ADVANCING (it reached Route 116 from Petalburg and then gave up). The retry
    # count is not what protects against a hopeless loop here; `_navigate_riding_out`'s
    # fail-fast guard is (it bails the moment the field is idle AND the position has not
    # changed, i.e. when retrying genuinely cannot help). So a bigger budget costs nothing
    # on a stuck journey and is the difference between arriving and not on a long one.
    yield from _navigate_riding_out(map_enum, tile, tries=24)

    before = _party_count()
    # ‼ SNAPSHOT THE BOX TOO (`#24-pcoverflow` break 2, 2026-08-06). With a full party the
    # catch lands in the PC and `_party_count()` never moves, so the old party-only test
    # reported "found nothing" while the counter sat in box 1. Snapshot the PIDs, not just the
    # count: `box_counter_pid` must not report a counter that was ALREADY stored before this
    # hunt (a previous boss's counter, or one collected and re-deposited) as this hunt's catch.
    before_box = _box_count()
    before_box_pids = _box_pids()
    # Party twin of `before_box_pids` — see `party_counter_slot`'s exclusion note.
    # ‼ IMPORT EXPLICITLY. `get_party` is imported locally per-function in this module and is
    # NOT in scope here; without this line the comprehension raises NameError, the `except`
    # swallows it, and the fence is silently EMPTY — i.e. the bug it exists to stop would still
    # be live while every test looked green. Same shape as `box_views` returning [] on a
    # TypeError (08-MISTAKES 2026-08-06).
    from modules.pokemon_party import get_party as _gp_snapshot

    try:
        before_party_pids = {m.personality_value for m in _gp_snapshot() if m is not None}
    except Exception:  # noqa: BLE001
        before_party_pids = set()
    arm([species_name])
    try:
        frames = {"n": 0}

        def _stop() -> bool:
            # ‼ Bound the OUTCOME *and* the frames. The outcome test ("do we now hold a
            # counter?") is the real goal; the frame budget only stops an unlucky hunt.
            # A budget alone would let a hunt that ALREADY succeeded keep spinning.
            frames["n"] += 1
            if frames["n"] > HUNT_SPIN_BUDGET_FRAMES:
                return True
            # ‼ A COUNT IS THE TRIGGER; AN IDENTITY IS THE VERDICT — see `catch_confirmed`, which
            # holds the reasoning and is GATED (this used to be inline and therefore unprovable).
            def _party_pids_now():
                try:
                    return {m.personality_value for m in _gp_snapshot() if m is not None}
                except Exception:  # noqa: BLE001 - an unreadable party must not fake a catch
                    return set()

            if catch_confirmed(
                party_count_now=_party_count(), party_count_before=before,
                party_pids_now=_party_pids_now, before_party_pids=before_party_pids,
                box_count_now=_box_count(), box_count_before=before_box,
                box_pids_now=_box_pids, before_box_pids=before_box_pids,
            ):
                return True
            return party_counter_slot(needed_type_names, before_party_pids) is not None

        yield from _story_spin(_stop)
    finally:
        disarm()

    # Clean overworld before the caller opens any menu (see the docstring).
    yield from normalize_to_overworld()
    yield from wait_until_truly_controllable()

    slot = party_counter_slot(needed_type_names, before_party_pids)
    if slot is not None:
        try:
            from modules.pokemon_party import get_party

            mon = get_party()[slot]
            caught_name, caught_pid = mon.species.name, mon.personality_value
        except Exception:
            caught_name, caught_pid = species_name, None
        console.print(f"[bold green]Story: counter hunt CAUGHT {caught_name} (slot {slot + 1}).[/]")
        context.message = f"Story: caught {caught_name} — the counter this boss needs."
        return {"slot": slot, "pid": caught_pid}

    # ‼ THE BOX PATH. Only PIDs that were NOT in the PC before this hunt count — otherwise a
    # previously-stored counter would be reported as this hunt's catch and the ladder would
    # "succeed" without having caught anything.
    boxed_pid = box_counter_pid(needed_type_names, exclude_pids=before_box_pids)
    if boxed_pid is not None:
        console.print(
            f"[bold green]Story: counter hunt CAUGHT {species_name} INTO THE PC BOX "
            f"(pid={boxed_pid:08X}) — the party was full; it will be collected at the next heal.[/]"
        )
        context.message = f"Story: caught {species_name} into the box — the counter this boss needs."
        return {"slot": None, "pid": boxed_pid}

    console.print(
        f"[yellow]Story: counter hunt for {species_name} found nothing in "
        f"{HUNT_SPIN_BUDGET_FRAMES} frames.[/]"
    )
    return None


def affordable_training_target(current_level: int, wanted: int, budget: int, estimate) -> int:
    """The highest level ≤ `wanted` whose training estimate fits `budget`.

    Pure and injectable so it can be tested without an emulator.

    ‼ WHY THIS EXISTS — the gate used to be ALL-OR-NOTHING, and that is how the counter
    chain came to spend a whole journey and a Poké Ball and then gain nothing. Measured
    live in batch `20260731-170603`, three times, verbatim:

        Story: counter hunt CAUGHT Machop (slot 5).
        Story: training Machop to L35 rejected — estimated 1693806 frames exceeds the
               budget (250000). It joins the fight at L16.

    A fresh catch is ~15 levels below the team BY CONSTRUCTION (that is what a
    hunting-ground counter is), so "train it all the way to the team, or not at all"
    resolves to NOT AT ALL essentially every time. The bot then fielded a L16 Machop
    against Norman's L28-31 team and lost — Balance Badges earned that batch: **0**.

    ‼ This also contradicted the user's own ruling for `#24-counters` — *"price both, then
    catch-and-train a Fighting type for Norman"*. Catching and then declining to train is
    not the cheaper of the two options that were priced; it is the cost of one with the
    benefit of neither.

    So: spend the budget rather than refusing it. Returns `current_level` when not even one
    level is affordable, which is the honest decline the caller still handles.
    """
    best = current_level
    for level in range(current_level + 1, wanted + 1):
        cost = estimate(level)
        if cost is None or cost > budget:
            break  # costs rise monotonically with level, so the first miss ends it
        best = level
    return best


def counter_training_ground(counter_level: int, cfg: dict):
    """Where to train a freshly-caught counter, and where to heal. -> ((map, tile), heal)

    ‼ KI-44. THIS USED TO BE `cfg["grass"]` UNCONDITIONALLY, AND THAT IS THE BOSS'S PATCH,
    NOT THE COUNTER'S. Measured in batch4 (`x4-runs/20260731-201554`), Norman's config sends
    a Machop **caught in FIERY_PATH** to `PETALBURG_TRAINING_GRASS = (ROUTE102, (9, 2))`.
    Two independent things are wrong with that, and the log only ever showed the first:

    1. **It cannot get there.** Training failed **7 of 7**, six with the bot stranded on
       ROUTE103 (45, 7) — eight maps from the catch, across a corridor it cannot cross.
    2. **It would not be worth going.** Probed 2026-08-01 (`probe_counter_grass.py`):
       ROUTE102's land wilds are **L3-4**. `story_mode.py` already calls this patch
       "~25 xp a kill, i.e. never" — it is the pathological case `FODDER_LEVEL_GAP` exists
       for. A counter is L14-16 by construction (it came off a hunting ground's own table).

    The obvious repair — "just train where you caught it" — is WRONG and the codebase
    already says so: FIERY_PATH, ROUTE112 and JAGGED_PASS are all in `NO_RETURN_GROUNDS`.
    They can be reached and left (fine for a catch-and-leave hunt) but the heal leg back to
    Lavaridge FAILS, and a training loop needs that third leg. Measured 2026-07-26.

    So ask `best_training_area`, the picker the rest of the bot already uses: it refuses
    no-return grounds FIRST, applies the winnability guard (never a band whose low end is
    above the trainee), honours the reachability predicate, and prefers the band closest to
    the trainee's level. For a L15 counter it answers **ROUTE117 (31,16), L13-14** — a
    ground with a working heal loop — instead of L3-4 on the far side of Hoenn.

    Falls back to `cfg`'s pair when the picker has no answer, so a boss whose configured
    grass IS the right one keeps exactly today's behaviour.
    """
    fallback = (cfg.get("grass"), cfg.get("heal"))
    try:
        from modules.story.training_areas import best_training_area
        from plugins.custom_modes.story_mode import _counter_area_allowed, _training_area_heal_map

        best = best_training_area(counter_level, allow=_counter_area_allowed)
        if best is None:
            return fallback
        map_enum, tile, _band = best
        return ((map_enum, tile), _training_area_heal_map().get(map_enum, cfg.get("heal")))
    except Exception:
        # A picker failure must never destroy a successful CATCH — degrade to the
        # configured pair, which is what shipped before this function existed.
        return fallback


def train_counter(slot: int, cfg: dict) -> Generator:
    """Rung 3 — bring the fresh catch up to the team, bounded by a frame estimate.

    Returns True if it trained (or was already high enough), False if it declined. A
    False here is NOT a failure to report as a crash: the caller still holds a type
    answer, it is just an under-levelled one, and the honest stop is still available.

    ‼ Why it must be a separate, DELIBERATE step rather than leaving it to the ordinary
    prep: `_prepare_for_fight` readies "the strongest battler, plus any battler already
    within TRAIN_CATCHUP_GAP levels of the target". A fresh L15 catch beside a L30 team
    is outside that gap by design (fresh catches are meant to level organically,
    `#24-team`), so nothing would ever train it and the hunt would have been for nothing.
    """
    from modules.console import console
    from modules.pokemon_party import get_party
    from modules.story.early_game import train_team
    from modules.story.training_areas import estimate_frames_to_level

    try:
        party = get_party()
        mon = party[slot]
        levels = [m.level for m in party if m is not None and not m.is_egg and m is not mon]
        team_level = max(levels, default=mon.level)
        target = max(mon.level, team_level - TRAIN_TO_TEAM_GAP)
        if target <= mon.level:
            console.print(
                f"[cyan]Story: {mon.species.name} is already within {TRAIN_TO_TEAM_GAP} "
                f"levels of the team — no counter training needed.[/]"
            )
            return True

        if "grass" not in cfg:
            console.print(
                f"[yellow]Story: no training grass configured for this boss — "
                f"{mon.species.name} goes in untrained at L{mon.level}.[/]"
            )
            return False

        # ‼ KI-44 — pick the ground for the COUNTER, not for the boss. See
        # `counter_training_ground` for the measurement that motivates this.
        grass, heal = counter_training_ground(mon.level, cfg)
        if grass is None:
            console.print(
                f"[yellow]Story: no training ground available for {mon.species.name} — "
                f"it goes in untrained at L{mon.level}.[/]"
            )
            return False
        if tuple(grass) != tuple(cfg["grass"]):
            console.print(
                f"[cyan]Story: training the counter at {grass[0].name} {grass[1]} rather than "
                f"the boss's own patch {cfg['grass'][0].name} — closer to L{mon.level} and it "
                f"has a working heal loop.[/]"
            )

        # FRAME-COST GATE, same contract as every other training entry point in this
        # file's neighbours: an UNKNOWN estimate is not a cheap one, so it declines.
        from plugins.custom_modes.story_mode import StoryMode, _wild_land_max

        wild_level = _wild_land_max(grass[0])
        estimate = (
            estimate_frames_to_level(mon, target, wild_level) if wild_level is not None else None
        )
        budget = StoryMode.MAX_PREP_TRAINING_FRAMES
        if estimate is None or estimate > budget:
            # ‼ SPEND THE BUDGET, DON'T REFUSE IT. Training all the way to the team is
            # unaffordable for essentially every fresh catch (see
            # `affordable_training_target`), and declining outright is what made three
            # successful Machop catches worthless in batch `20260731-170603`. Buy as many
            # levels as the budget covers instead — an L25 counter with a 2x type advantage
            # is a real answer where an L16 one is not.
            afford = affordable_training_target(
                mon.level, target, budget,
                lambda level: estimate_frames_to_level(mon, level, wild_level),
            ) if wild_level is not None else mon.level
            if afford <= mon.level:
                console.print(
                    f"[yellow]Story: training {mon.species.name} to L{target} rejected — "
                    f"estimated {estimate if estimate is not None else 'UNKNOWN'} frames "
                    f"exceeds the budget ({budget}), and not even ONE level is affordable. "
                    f"It joins the fight at L{mon.level}.[/]"
                )
                return False
            console.print(
                f"[cyan]Story: training {mon.species.name} to L{target} would cost "
                f"{estimate if estimate is not None else 'UNKNOWN'} frames (budget {budget}) "
                f"— training to L{afford} instead, which the budget covers.[/]"
            )
            target = afford
            estimate = estimate_frames_to_level(mon, target, wild_level)

        console.print(
            f"[bold cyan]Story: training the counter — {mon.species.name} "
            f"L{mon.level} -> L{target} (team is L{team_level}, est {int(estimate)} frames).[/]"
        )
        yield from train_team(
            target, slots={slot}, grass=grass, heal_center=heal
        )
        return True
    except Exception as error:
        # A failure to TRAIN must never destroy a successful CATCH. The caller re-checks
        # the party either way, and the terminal raise is still there behind it.
        console.print(f"[yellow]Story: counter training failed ({error!r}) — continuing untrained.[/]")
        return False
