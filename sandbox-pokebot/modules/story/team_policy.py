"""Team policy — dead-weight detection and PC rotation planning (punch-list #24-trainmap+).

Design: `PROJECT KNOWLEDGE/21-TEAM-POLICY-DESIGN.md` §2 and §4. User ruling 2026-07-29.

‼ WHY THIS EXISTS — measured, not assumed. Across the user's 2026-07-29 x4 bundle
(363 badge-moment team snapshots):

  * **35% of badge moments carried at least one mon 15+ levels below the team max**, and
    parties carried up to FIVE such mons at once.
  * P1 reached the Feather Badge with a team max of L48 while still carrying a **Zigzagoon
    L8**.
  * P1 caught a **Makuhita — a FIGHTING type, exactly the counter Norman needs — and carried
    it from L8 to L9 across FIVE badges** while the rest of the team went L22 → L42. The
    answer was in the party the whole time and never became usable.
  * 12 derails in that one bundle were *"No party mon can learn Surf and the party is full"* —
    the run ending because a full party of dead weight left no room for an HM carrier.

The cause is structural: `_catch_team_target = 4` means the bot catches four early mons
(often Zigzagoon/Wurmple-grade), story GIFTS then push the party to 5-6, and **no story code
path has ever touched the PC** — the only `interact_with_pc` caller in the whole repo is the
stock `modules/modes/daycare.py`, which merely releases. So nothing can ever leave the party.

PURE MODULE ON PURPOSE. Nothing here reads memory, walks, or presses a button — it takes a
plain view of the party and returns decisions. That makes the whole policy testable with no
emulator (§7 of the design), which matters because this dev box has none.

The bench/deposit ACTION and the PC trip are deliberately NOT here; this module only decides.
"""

from __future__ import annotations

#: Levels behind the lead at which a mon is unrecoverable BY CONSTRUCTION.
#: `_prepare_for_fight` stops catching a mon up at `TRAIN_CATCHUP_GAP = 6`
#: (story_mode.py:705), so anything further behind will never be trained by the existing
#: machinery. 8 gives that threshold a small margin rather than sitting exactly on it.
DEAD_WEIGHT_LEVEL_GAP = 8

#: Battles sent out with nothing to show before "technically able but never contributes"
#: becomes a judgement we are willing to act on.
MIN_BATTLES_BEFORE_CONTRIBUTION_CALL = 6

#: ‼ MEASURED CAPS — the difference between "is dead weight" (a FACT about a mon) and
#: "box it now" (a DECISION under constraints). Design §2 defines only the fact.
#:
#: Replaying the predicate over all **363 real badge-moment parties** from the user's
#: 2026-07-29 bundle showed the fact alone is far too aggressive as a deposit rule:
#:     box 3 mons: 148 parties (41%)      box 4: 23      box 5: 6
#:     59% of parties would be left with FEWER THAN 3 mons
#:     132 parties of four would be cut to a SINGLE Pokémon
#: A one-mon party is the "lone starter can't rotate" condition that produced the Roxanne
#: party-menu hang (KI-8). The predicate is not wrong — the starter takes most of the XP,
#: so the whole bench really is 10-20 levels behind by mid-game — but "will never be caught
#: up" does not imply "box it this visit".
#:
#: The PURPOSE of a rotation is to free ONE OR TWO slots for an HM carrier or a counter, so
#: two deposits per visit is sufficient; worst-first converges over successive heal trips
#: without ever gutting the team.
MIN_PARTY_AFTER_ROTATION = 3
MAX_DEPOSITS_PER_ROTATION = 2

#: HM move names (Gen 3). Used ONLY to protect a carrier from being boxed — never to
#: decide that a mon is useful. A mon whose sole value is an HM is still dead weight in a
#: fight, but boxing the only Surf carrier soft-locks the run (design §6).
HM_MOVES = frozenset({"Cut", "Fly", "Surf", "Strength", "Flash", "Rock Smash", "Waterfall", "Dive"})


class MonView:
    """A plain, emulator-free view of one party member.

    Built from a real `Pokemon` by `view_from_party()`, or by hand in a test. Keeping the
    predicate off the live object is what makes this module provable without a ROM.
    """

    __slots__ = ("species", "level", "moves", "is_egg", "battles", "kos", "survivals", "is_favourite")

    def __init__(self, species, level, moves=(), *, is_egg=False,
                 battles=0, kos=0, survivals=0, is_favourite=False):
        self.species = species
        self.level = level
        #: iterable of (move_name, base_power)
        self.moves = tuple(moves)
        self.is_egg = is_egg
        self.battles = battles
        self.kos = kos
        self.survivals = survivals
        self.is_favourite = is_favourite

    def has_damaging_move(self) -> bool:
        return any(bp > 0 for _, bp in self.moves)

    def hm_moves(self) -> set:
        return {name for name, _ in self.moves if name in HM_MOVES}

    def __repr__(self):  # pragma: no cover - diagnostics only
        return f"<{self.species} L{self.level}>"


def view_from_party(party) -> list:
    """Adapt live `Pokemon` objects to `MonView`. Battle stats are not tracked live yet,
    so they default to 0 — the contribution test simply never fires until a caller supplies
    them. That is deliberate: a test that cannot see the data must not guess."""
    out = []
    for p in party:
        if p is None:
            continue
        try:
            moves = tuple(
                (lm.move.name, lm.move.base_power)
                for lm in getattr(p, "moves", ())
                if lm is not None and lm.move is not None
            )
        except Exception:  # noqa: BLE001 - a malformed move list must not break planning
            moves = ()
        out.append(MonView(getattr(p.species, "name", "?"), p.level, moves,
                           is_egg=bool(getattr(p, "is_egg", False))))
    return out


def _only_hm_carrier(views, i) -> set:
    """HM moves for which `views[i]` is the party's ONLY carrier."""
    mine = views[i].hm_moves()
    if not mine:
        return set()
    others = set()
    for j, v in enumerate(views):
        if j != i:
            others |= v.hm_moves()
    return mine - others


def dead_weight(views, i) -> "str | None":
    """Return a REASON string if `views[i]` is dead weight, else None.

    Design §2. Fails if ANY of: level gap, uselessness, or zero contribution.
    Type redundancy is deliberately NOT a test in v1 — weakest signal, hardest to
    falsify offline.
    """
    mon = views[i]
    if mon.is_egg:
        return None  # an egg is not dead weight, it is pending

    # --- EXEMPTIONS FIRST. A wrong deposit costs a PC visit; boxing the only Surf
    #     carrier soft-locks the run outright (design §6), so protection outranks
    #     every heuristic below.
    if mon.is_favourite:
        return None
    sole = _only_hm_carrier(views, i)
    if sole:
        return None

    battlers = [v for v in views if not v.is_egg]
    lead_level = max((v.level for v in battlers), default=mon.level)

    if mon.level < lead_level - DEAD_WEIGHT_LEVEL_GAP:
        return (f"level {mon.level} is {lead_level - mon.level} behind the team's best "
                f"(L{lead_level}); >{DEAD_WEIGHT_LEVEL_GAP} is unrecoverable by construction "
                f"— _prepare_for_fight stops catching a mon up at TRAIN_CATCHUP_GAP=6")

    if not mon.has_damaging_move() and not mon.hm_moves():
        return "no damaging move and no HM — cannot battle and cannot open a route"

    if (mon.battles >= MIN_BATTLES_BEFORE_CONTRIBUTION_CALL
            and mon.kos == 0 and mon.survivals == 0):
        return (f"sent out {mon.battles} times for 0 KOs and 0 survivals "
                f"— able but not contributing")

    return None


def find_dead_weight(views) -> list:
    """[(index, reason)] for every dead-weight party member, worst level gap first."""
    found = [(i, r) for i in range(len(views)) if (r := dead_weight(views, i)) is not None]
    found.sort(key=lambda t: views[t[0]].level)
    return found


def rotation_plan(party_views, box_views=(), *, needed_types=(), sweep_score=None,
                  sweep_floor=0.0) -> dict:
    """Decide a PC rotation. PURE — returns a plan, executes nothing.

    Design §4: *piggyback, do not detour.* The caller runs this **on arrival at a Poké
    Centre for a heal that was happening anyway**, and executes only if the plan is
    non-empty.

    Returns `{"deposit": [i…], "withdraw": [j…], "reasons": {…}, "worth_it": bool}`.

    `worth_it` is True only when the plan deposits ≥1 dead-weight mon, OR withdraws a mon
    clearing `sweep_floor` when nothing in the party does — the exact condition in §4. A
    caller that ignores `worth_it` and rotates anyway will burn PC visits for nothing.
    """
    dead = find_dead_weight(party_views)          # already worst (lowest level) first
    reasons = {i: r for i, r in dead}

    # ‼ CAP THE DEPOSIT. `find_dead_weight` reports the FACT; this is the DECISION.
    # Uncapped, this rule would leave 59% of real parties below three mons and cut 132
    # observed four-mon parties to one (see MIN_PARTY_AFTER_ROTATION). Free a slot or two,
    # worst-first, and let successive heal trips converge.
    alive = sum(1 for v in party_views if not v.is_egg)
    room_to_spare = max(0, alive - MIN_PARTY_AFTER_ROTATION)
    budget = min(MAX_DEPOSITS_PER_ROTATION, room_to_spare)
    deposit = [i for i, _ in dead[:budget]]
    reasons = {i: reasons[i] for i in deposit}

    withdraw = []
    if box_views and sweep_score is not None:
        party_best = max((sweep_score(v) for v in party_views), default=0.0)
        if party_best < sweep_floor:
            scored = sorted(
                ((sweep_score(v), j) for j, v in enumerate(box_views)),
                reverse=True,
            )
            for s, j in scored:
                if s >= sweep_floor:
                    withdraw.append(j)
                    break

    # Never deposit more than we can spare: keep at least one battle-capable mon.
    capable = [i for i, v in enumerate(party_views)
               if not v.is_egg and v.has_damaging_move()]
    keepers = set(capable) - set(deposit)
    if not keepers and capable:
        strongest = max(capable, key=lambda i: party_views[i].level)
        deposit = [i for i in deposit if i != strongest]
        reasons.pop(strongest, None)

    worth_it = bool(deposit) or bool(withdraw)
    return {"deposit": deposit, "withdraw": withdraw,
            "reasons": reasons, "worth_it": worth_it}


# --- LEAD SELECTION (#24-leadpolicy, user ruling A+C, 2026-08-01) ----------------------
#
# ‼ WHY. `_lead_best_matchup` scored ONLY defence — `min(incoming_multiplier, -level)` —
# and that benched the mon the whole counter chain existed to produce. Measured in batch5
# (`x4-runs/20260801-075805`): the bot caught a Machop, trained it L15 -> L29, watched it
# evolve into MACHOKE, and then led **SHEDINJA into Norman 9 times out of 9**. Machoke was
# led ZERO times. Shedinja is Bug/Ghost, so Normal -> 0x, which wins a purely defensive
# score outright — and then Slaking's Faint Attack (Dark) is 2x on Ghost and one-shots its
# single hit point. The model cannot see that, because it does not read movepools.
#
# Catching, travelling for, and training a type counter and then not fielding it is the
# cost of the entire chain with the benefit of none of it. Batch5's badge funnel did not
# move at all (Heat->Balance 83% -> 79%) despite the chain working end to end.
#
# THE RULING WAS A+C, and this implements exactly that — no more:
#   (a) require the lead to also have a >=neutral attacking option;
#   (c) special-case 1-HP Wonder Guard mons.
# ‼ Option (b) — "weight the level gap so a resistant chaff mon can't bench a much stronger
# one" — was NOT selected, so the Route 110 rival case (Whismur L15 led over Marshtomp L24)
# is deliberately UNCHANGED. Do not quietly fix it here; re-ask if it matters.
#
# ‼ THESE ARE SORT TERMS, NOT FILTERS. A filter could empty the candidate set and leave the
# bot with no lead at all; ordering always yields an answer and degrades to today's choice
# when nothing better exists.
#
# ‼ ORDERING IS DELIBERATE — `incoming` stays AHEAD of the level tie-break so the proven
# Rustboro-rival behaviour is preserved (Marshtomp is 4x weak to Grovyle and must stay
# benched). (a) and (c) only reorder mons that the old rule considered equivalent, plus the
# Wonder Guard trap it considered ideal.


def lead_rank_key(*, incoming: float, can_attack: bool, glass_wonder_guard: bool,
                  level: int) -> tuple:
    """Sort key for choosing a lead before a type-countered fight. LOWER is better.

    ``incoming``            worst-case STAB multiplier the foe can hit this mon for.
    ``can_attack``          does it have a damaging move that is >=1x on the foe?
    ``glass_wonder_guard``  Wonder Guard on a 1-HP body (Shedinja) — immune to most things
                            and deleted by anything super-effective, which the type model
                            cannot predict.
    """
    return (
        1 if glass_wonder_guard else 0,   # (c) never the default lead into a boss
        0 if can_attack else 1,           # (a) a lead that cannot damage the foe cannot win
        float(incoming),                  # unchanged original criterion
        -int(level),                      # unchanged original tie-break
    )


def best_lead_index(candidates) -> "int | None":
    """Index of the best lead among ``candidates``.

    Each candidate is a mapping with ``incoming``, ``can_attack``, ``glass_wonder_guard``
    and ``level``. Returns None for an empty list. Pure — no memory reads, no buttons.
    """
    items = list(candidates)
    if not items:
        return None
    return min(
        range(len(items)),
        key=lambda i: lead_rank_key(
            incoming=items[i]["incoming"],
            can_attack=items[i]["can_attack"],
            glass_wonder_guard=items[i]["glass_wonder_guard"],
            level=items[i]["level"],
        ),
    )
