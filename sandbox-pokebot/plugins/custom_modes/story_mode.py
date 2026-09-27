"""Story Mode (#24) — plays Emerald's story from a fresh save or continues an
existing one, building a team toward the Elite Four.

Built in verifiable chunks (see PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md):
  * Chapter 0 (the New Game intro) — IMPLEMENTED. Title -> New Game -> Birch's
    speech -> gender -> name -> lands in the moving truck.
  * Existing saves — the read-only detector reports the current chapter so the
    bot can resume at the right place (chapter execution beyond 0 is WIP).

On start:
  * If the game is still at the title/main menu (a fresh, save-less boot), the
    intro is run using the name/gender from ``<profile>/story.yml``.
  * If a game is already loaded (existing progress), the current chapter is
    detected and reported; execution of chapters > 0 is not built yet, so the
    bot hands back to manual after reporting.
"""

from types import SimpleNamespace
from typing import Generator

from modules.console import console
from modules.context import context
from modules.memory import GameState, game_has_started, get_game_state
from modules.modes import BattleAction, BotMode
from modules.battle_strategies import BattleStrategyUtil, TurnAction
from modules.battle_strategies.catch import CatchStrategy
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy
from modules.battle_strategies.run_away import RunAwayStrategy


class StoryFleeStrategy(RunAwayStrategy):
    """Flee a WILD battle without tripping the post-battle lead rotation.

    ‼ CRASHED A LIVE RUN (batch 20260726-052205 run03, fixed same day). Stock
    `RunAwayStrategy.choose_new_lead_after_battle()` returns **False**, though it is
    annotated `int | None`. The framework only ever drove that class from
    `BattleListener.run_away_from_battle()`, which does NOT rotate leads, so the odd
    return value was harmless and invisible. SURVIVAL MODE returns a flee strategy from
    `on_battle_started` instead, which routes it through `BattleListener.fight()` — and
    that path does:

        if strategy.choose_new_lead_after_battle() is not None:
            yield from self.rotate_lead_pokemon(...)

    `False is not None`, so it rotated to party index `False`, and `RotatePokemon`
    raised `RuntimeError: Cannot rotate Pokémon #False with itself` right after
    "Got away safely!" — dropping the run to Manual with no controller on the stack.

    Returning a proper `None` says "keep the current lead", which is what fleeing wants.
    Done as a SUBCLASS rather than by editing the upstream file, so the framework's own
    flee path keeps its existing behaviour exactly.
    """

    def choose_new_lead_after_battle(self) -> int | None:
        return None


class StoryCatchStrategy(CatchStrategy):
    """Catch strategy for the Story bot that NEVER drops to Manual when out of Poké
    Balls. The stock CatchStrategy calls `switch_to_manual()` the moment it can't
    throw a ball — but opportunistic catching can burn through the balls on bad catch
    RNG, which stranded the bot in Manual (user-seen). Here, if no ball can be thrown,
    we FLEE and carry on instead; the story then stops catching (the `_should_catch`
    floor) until balls are restocked. (User directive: out of balls → finish the
    battle, never break.)

    ‼ SCOPE WIDENED 2026-09-10 (`#24-dexhunt`). This docstring said "pre-gym catching"
    and "restocked at a mart BEFORE THE GYM"; both are now false. `_should_catch` also
    admits POST-badge dex catches at a full party, so this strategy runs on L30-45
    routes, not only L3-6 ones.

    ⛔⛔ AND THAT MATTERS, BECAUSE A CATCH BATTLE NEVER FIGHTS BACK. `CatchStrategy.decide_turn`
    (`catch.py:41-62`) only ever throws a ball or applies a status move — never a damaging
    move — and `should_flee_after_faint` is unconditionally False (`catch.py:38-39`), which
    removes the base strategy's "party can't battle → flee" escape. So the wild attacks for
    free and the bot does not leave until the balls run out. Pre-gym-1 that was bounded by
    weak wilds; it is not any more.
    ⇒ The fence bounds ENTRY (`party_healthy` in `decide_dex_catch`), so a dex catch only ever
    STARTS from full strength. It does NOT bound mid-battle degradation — that needs a
    faint-aware bail-out in a dex-only subclass, filed as `#24-dexcatch-battlebail`.
    ⛔ DO NOT "fix" it by editing this class: `StoryShinyCatchStrategy` INHERITS from it, and the
    shiny rule is an explicit user directive (2026-07-22) to attempt until success, whiteout or
    out of balls. A bail-out here would silently overrule that."""

    def decide_turn(self, battle_state):
        try:
            if self._get_best_poke_ball(battle_state) is None:
                context.message = "Story: out of Poké Balls — fleeing this catch and moving on."
                return TurnAction.run_away()
        except Exception:
            pass
        return super().decide_turn(battle_state)


def dex_catch_bail_reason(spare_balls: int, reserve: int, fainted_this_battle: bool) -> "str | None":
    """PURE: why a DISCRETIONARY (post-gym-1 Pokédex) catch should stop NOW, or None to keep throwing.

    `#24-dexcatch-battlebail` + USER RULING 20's Phase 0 (`ai-research-notes/2026-09-26-rulings19-20-PLAN.md`):
    the fence guards only ENTRY (`spare_balls > DEX_CATCH_BALL_RESERVE`, a healthy party), while a catch battle never
    fights back and throws until caught or empty — MEASURED: one Absol took 23 balls in 26,615 frames and the run later
    died "Cannot hunt a Dive learner: no Poké Balls and no money". ⇒ stop at the reserve (the mandatory hunts' balls),
    and stop the moment a team member faints (the wild attacks for free).
    """
    if fainted_this_battle:
        return "a team member fainted"
    if spare_balls <= reserve:
        return f"only {spare_balls} spare balls left — the rest are the mandatory hunts' reserve ({reserve})"
    return None


class StoryDexCatchStrategy(StoryCatchStrategy):
    """The DISCRETIONARY Pokédex catch after gym 1 — a dex-ONLY subclass, exactly as `#24-dexcatch-battlebail` specified.

    ⛔ NOT an edit of `StoryCatchStrategy`: `StoryShinyCatchStrategy` inherits it (the shiny rule — attempt until success,
    whiteout or out of balls — is a user directive), and the HM-learner and counter catches are MANDATORY. Only the
    fence's post-gym-1 call site returns this class; pre-gym-1 team building stays byte-identical.
    Bails (flees) on `dex_catch_bail_reason`: a faint this battle, or spare balls at the reserve. A reserve read that
    FAILS keeps the old behaviour (throw) — never a silent bail. `POKEBOT_DEXCATCH_FAULT_NOBAIL=1` restores the old
    behaviour entirely (the skip-the-fix arm, registered in 29).
    """

    def __init__(self):
        super().__init__()
        self._fainted_this_battle = False
        self.bail_reason = None

    def should_flee_after_faint(self, battle_state) -> bool:
        import os as _os_bail

        if _os_bail.environ.get("POKEBOT_DEXCATCH_FAULT_NOBAIL") == "1":
            return super().should_flee_after_faint(battle_state)
        self._fainted_this_battle = True
        # ⛔ Only when escape is POSSIBLE: trapped (Shadow Tag, Arena Trap — Trapinch is a Route 111 catch — Mean Look,
        # Wrap), "No" to "use next Pokémon?" cannot escape; keep the parent's answer (send the next mon, keep throwing).
        if self._escape(battle_state) is None:
            return super().should_flee_after_faint(battle_state)
        self._announce_bail("a team member fainted")
        return True

    @staticmethod
    def _escape(battle_state):
        """The best way out, or None when escaping is IMPOSSIBLE. An unreadable state falls back to Run (the plain
        strategy's own out-of-balls answer)."""
        try:
            from modules.battle_strategies import BattleStrategyUtil as _BSU_bail

            return _BSU_bail(battle_state).get_best_escape_method()
        except Exception:  # noqa: BLE001 - unreadable ⇒ Run, exactly what StoryCatchStrategy does at 0 balls
            return TurnAction.run_away()

    def _announce_bail(self, reason: str) -> None:
        if self.bail_reason is not None:
            return
        self.bail_reason = reason
        context.message = f"Story: abandoning this Pokédex catch — {reason}."
        try:
            _log_story_event(f"[DEXCATCH-BAIL] {reason}", "DEXCATCH")
        except Exception:  # noqa: BLE001 - telemetry must never break a battle; the flee itself still happens
            pass

    def decide_turn(self, battle_state):
        import os as _os_bail

        if _os_bail.environ.get("POKEBOT_DEXCATCH_FAULT_NOBAIL") != "1":
            try:
                from modules.items import get_item_bag as _bag_bail

                reason = dex_catch_bail_reason(_bag_bail().number_of_balls_except_master_ball,
                                               DEX_CATCH_BALL_RESERVE, self._fainted_this_battle)
            except Exception:  # noqa: BLE001 - an unreadable bag keeps the OLD behaviour (throw), never a silent bail
                reason = None
            if reason is not None:
                escape = self._escape(battle_state)
                if escape is not None:
                    self._announce_bail(reason)
                    return escape
                # ⛔ TRAPPED: choosing Run every turn would never leave — keep the old behaviour (throw) instead…
                fight = self._fight_if_trapped_and_empty(battle_state)
                if fight is not None:
                    return fight
        return super().decide_turn(battle_state)

    def _fight_if_trapped_and_empty(self, battle_state):
        """…and when NO ball is left to throw, the parent would pick Run, which a trapped battler can never do (review
        2026-09-26: Trapinch's Arena Trap on Route 111) — the wild would then attack for free until a whiteout. FIGHT
        instead: the strongest move ends the battle. None ⇒ no usable move (or unreadable): the parent decides."""
        try:
            if self._get_best_poke_ball(battle_state) is not None:
                return None
            from modules.battle_strategies import BattleStrategyUtil as _BSU_fight

            move = _BSU_fight(battle_state).get_strongest_move_against(
                battle_state.own_side.active_battler, battle_state.opponent.active_battler)
        except Exception:  # noqa: BLE001 - unreadable ⇒ the parent's turn, exactly the pre-change behaviour
            return None
        if move is None:
            return None
        self._announce_bail("trapped with no Poké Ball left — fighting out")
        return TurnAction.use_move(move)


class StoryShinyCatchStrategy(StoryCatchStrategy):
    """Catch strategy for a WILD SHINY in Story mode (user directive 2026-07-22: shinies
    are rare collectibles — a real run's debug log showed a Shiny Poochyena being FOUGHT
    with 32 balls in the bag, because the old contingency only ever fought through).

    ALWAYS attempts the catch while any allowed ball remains — even an already-owned
    species, even with a full party (the catch goes to the PC box, vanilla behavior),
    at any story stage. The ONE behavioral difference from the parent: if balls run out
    MID-battle, a shiny is NOT fled (the parent's rule for ordinary team-catching) and
    NEVER dropped to Manual (the stock base's rule) — it is fought through like a normal
    battle (attack with the strongest usable move; Struggle if nothing has PP), per the
    user's spec: attempt until success, whiteout, or out of balls — then just fight."""

    def decide_turn(self, battle_state):
        try:
            if self._get_best_poke_ball(battle_state) is None:
                context.message = "Story: ran out of usable Poké Balls mid-shiny — fighting it through."
                util = BattleStrategyUtil(battle_state)
                active = battle_state.own_side.active_battler
                move = util.get_strongest_move_against(active, battle_state.opponent.active_battler)
                if move is not None:
                    return TurnAction.use_move(move)
                if active is not None:
                    for i, learned in enumerate(active.moves):
                        if learned is not None and util.move_is_usable(learned):
                            return TurnAction.use_move(i)
                    # PP-only last resort — see the single-battle branch's comment.
                    for i, learned in enumerate(active.moves):
                        if learned is not None and learned.pp > 0:
                            return TurnAction.use_move(i)
                return TurnAction.use_move(0)  # every move truly at 0 PP → the game Struggles
        except Exception:
            pass
        # Balls available: the grandparent CatchStrategy does the real work (status move
        # when catch odds are poor, then throw the best ALLOWED ball — the #40 allowlist
        # already protects the Master Ball by default). Deliberately skip the parent's
        # decide_turn so its out-of-balls flee branch can never fire for a shiny.
        return CatchStrategy.decide_turn(self, battle_state)


def rank_replacement(candidates, foe_types, foes, damage_of):
    """Pick the best replacement after a faint. PURE — no globals, no battle state, no ROM.

    ``candidates``  : ``[(index, mon, mon_types), ...]`` — already filtered for alive/not-excluded.
    ``foe_types``   : every type on the field, flattened (the DEFENSIVE half's worst case).
    ``foes``        : the opposing battler objects, passed through to ``damage_of`` untouched.
    ``damage_of``   : ``(mon, learned_move, foe) -> float | None``. ``None`` means "could not
                      estimate"; ``0.0`` means "estimated, and it does nothing".

    Returns ``(best_index, report)``. ``report`` carries ``estimates_ok`` / ``estimates_failed`` so the
    caller can SEE which metric actually decided — ``08-MISTAKES.md``: *an instrument needs a control
    that must fire*, and a heuristic that silently degrades is the thing that rule exists to catch.

    ⭐ THE KEY IS ``(cannot_damage, incoming, -outgoing, -hp_fraction, -level)`` and stays
    lexicographic, so among mons that CAN act the DEFENSIVE term still decides first and only ties
    reach ``outgoing``. Two changes, both recorded at the sort site: ``outgoing`` was a bare type
    multiplier (`KI-95`) and is now expected damage; and ``cannot_damage`` was added 2026-09-17
    (`#24-ghostreplacement`) because a DEFENSIVE IMMUNITY WAS OUTRANKING THE ABILITY TO FIGHT AT ALL
    — measured against Phoebe's pure Ghosts, this function chose **Swellow (incoming 0.00, outgoing
    31)** over **Mightyena (incoming 0.50, outgoing 68)**, i.e. the mon that cannot hurt a Ghost
    beat the only one that hits it for double. ⇒ ``cannot_damage`` is a no-op unless some candidate
    deals literally zero.
    ‼ Because the tuple is lexicographic, the two terms never need to share a scale — which is why
    swapping a 0-4 multiplier for a 0-300 damage figure is safe rather than a silent re-weighting.
    """
    # ---- PASS 1: measure every candidate. Nothing is compared yet. -------------------------------
    rows, ok, failed = [], 0, 0
    for index, mon, mon_types in candidates:
        # Defensive: the worst the foe's STAB can do to this mon (lower = better). UNCHANGED.
        incoming = 0.0
        for foe_type in foe_types:
            multiplier = 1.0
            for own_type in mon_types:
                multiplier *= foe_type.get_effectiveness_against(own_type)
            incoming = max(incoming, multiplier)

        # Offensive, measured BOTH ways: the real damage estimate, and the pre-KI-95 multiplier kept
        # purely as the fallback. `max` over foes matches the pre-KI-95 semantics exactly.
        damage, legacy = 0.0, 0.0
        for learned in mon.moves:
            if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                continue
            for foe in foes:
                multiplier = 1.0
                for foe_type in foe.types_for_ranking:
                    multiplier *= learned.move.type.get_effectiveness_against(foe_type)
                legacy = max(legacy, multiplier)

                estimate = damage_of(mon, learned, foe.battler)
                if estimate is None:
                    failed += 1
                else:
                    ok += 1
                    damage = max(damage, estimate)

        rows.append((index, incoming, damage, legacy,
                     mon.current_hp / max(1, mon.total_hp), mon.level))

    # ---- PASS 2: ONE metric for the whole ranking, chosen only now that everything is measured. ---
    # ⛔⛔ THIS TWO-PASS SHAPE IS THE POINT, AND THE FIRST VERSION OF THIS FUNCTION GOT IT WRONG.
    # Deciding the fallback INSIDE the loop made the units depend on ITERATION ORDER: a candidate
    # measured before the first successful estimate was scored 0-4 (a multiplier) while a later one
    # was scored 0-300 (damage), and the sort key then compared them as if they were the same
    # quantity. ⇒ A RANKING IS ONLY MEANINGFUL IF EVERY ROW IS SCORED IN THE SAME UNITS, so the
    # choice of units must be made once, for all rows, after all measurements.
    use_damage = ok > 0
    best_index, best_key = None, None
    for index, incoming, damage, legacy, hp_fraction, level in rows:
        outgoing = damage if use_damage else legacy
        # ⛔⛔ `cannot_damage` LEADS THE KEY, AND IT IS THE ONLY TERM THAT MAY OUTRANK `incoming`.
        # MEASURED 2026-09-17 on the real §Ch24 fixture party against **Phoebe's pure Ghosts**:
        #     slot 2  Swellow   L48  incoming=0.00  best_outgoing=31.0   <- CHOSEN
        #     slot 4  Mightyena L48  incoming=0.50  best_outgoing=68.0   <- never considered
        # Ghost→Normal is **0x**, so our WORST attackers score a PERFECT defensive 0.00 and win at
        # the first term, while the one mon that resists Ghost *and* hits it for double loses there
        # and never reaches `outgoing`. ⇒ after every faint the bot sent in the battler with the
        # fewest usable moves, in the one fight where that is fatal.
        # ‼ A DEFENSIVE IMMUNITY IS NOT A REASON TO SEND A MON THAT CANNOT WIN. "Takes 0" and
        # "deals 0" are the SAME type relation read from opposite ends, so ranking on `incoming`
        # alone actively SEEKS the useless mon. In a fleeable fight that wastes turns; in the Elite
        # Four, which is five fights with no shop, no Centre and no retreat, it loses the run.
        # ⭐ WHY THIS SHAPE IS SAFE ON A SHARED PATH — it is a NO-OP unless some candidate deals
        # literally zero. When every candidate can damage the foe the term is 0 for all of them and
        # the tuple falls through to EXACTLY the previous key; when NO candidate can, it is 1 for
        # all and the ordering is likewise unchanged. It can only ever separate "can act" from
        # "cannot act", which is the one distinction `incoming` provably gets backwards.
        # ⛔ It does NOT reorder by damage — `incoming` still decides among mons that can fight, so
        # the defensive-first policy this function was built around is untouched.
        cannot_damage = 0 if outgoing > 0 else 1
        key = (cannot_damage, incoming, -outgoing, -hp_fraction, -level)
        if best_key is None or key < best_key:
            best_index, best_key = index, key
    return best_index, {
        "estimates_ok": ok,
        "estimates_failed": failed,
        # ⭐ NAME THE METRIC THAT ACTUALLY DECIDED. `estimates_ok=0` alone left a reader to infer it;
        # an inference is exactly what a log line should never require.
        "metric": "damage" if use_damage else "legacy",
        "key": best_key,
    }


class _RankingFoe:
    """The two things `rank_replacement` needs about a foe, so the ranker stays ROM-free."""

    __slots__ = ("types_for_ranking", "battler")

    def __init__(self, types_for_ranking, battler):
        self.types_for_ranking = types_for_ranking
        self.battler = battler


class LevelUpTravelBattleStrategy(LevelUpLeadBattleStrategy):
    """Fights to win like LevelUpLead, but NEVER flees a TRAINER battle.

    Story travel crosses routes that have trainers, and at this point the party
    is often a SINGLE Pokémon — so when its HP dips, the parent strategy tries
    to flee/rotate, and in a trainer battle (which you cannot flee) that raises
    ``RuntimeError: Tried to run away from a trainer battle`` (ML-8). Here a
    trainer battle always fights on with the strongest move instead; the caller
    heals to full first so the lead can win. WILD battles keep the parent
    behaviour (flee at low HP — the training loop heals for that)."""

    def choose_new_lead_after_faint(self, battle_state):
        """MATCHUP-AWARE replacement pick (user discussion 2026-07-23, Wattson analysis):
        the stock chooser sends the highest-HP living mon — which in the Wattson run
        meant full-HP Swellow and Ninjask (both Electric-weak) walking into
        Thunderbolts, attempt after attempt. The game asks us to CHOOSE, so choose
        like a player: prefer the mon the opponent hits least effectively (worst-case
        STAB from the opponent's types), then the one whose own usable moves hit the
        opponent hardest, then HP fraction, then level. Falls back to the stock pick
        on any surprise (missing data → the parent's HP rule)."""
        try:
            from modules.pokemon_party import get_party as _gp

            # Opponent type PAIRS on the field right now (both actives in a double).
            # Kept as per-battler pairs: effectiveness against a dual-type is the
            # PRODUCT over its two types (Ground vs Flying/Electric is 0x, not 2x).
            # ‼ KI-95 — KEEP THE BATTLER OBJECTS, not just their type lists. The old code discarded
            # them, which is exactly why the offensive term could only ever be a type multiplier:
            # the real damage formula needs the DEFENDER, and it had been thrown away.
            foes = []
            for battler in (
                getattr(battle_state.opponent, "left_battler", None),
                getattr(battle_state.opponent, "right_battler", None),
            ):
                if battler is not None:
                    try:
                        foes.append(_RankingFoe(list(battler.species.types), battler))
                    except Exception:
                        pass
            foe_types = [t for foe in foes for t in foe.types_for_ranking]
            if not foe_types:
                return super().choose_new_lead_after_faint(battle_state)

            # ‼‼ THE ALLY'S POKEMON ARE IN OUR PARTY ARRAY IN A MULTI BATTLE, and this ranking
            # PREFERS them. §Ch19's Space Center fight puts Steven's max-IV Metang L42 / Skarmory
            # L43 / Aggron L44 into the party array; the key below sorts on (incoming damage,
            # -outgoing, -hp_fraction, -level), and three fresh high-level mons win that comparison
            # against our damaged party outright. The game then refuses the switch, so the party
            # menu is handed a target it can never accept.
            # ‼ EXCLUDED BY ORIGINAL TRAINER, NOT BY INDEX. The first version of this cut at
            # `index >= 3` was measured WRONG: opening the battle party menu runs
            # `UpdatePartyToBattleOrder`, which physically permutes the array, so index 1 becomes
            # the ally's Metang and OUR mon moves to index 3 (`ch19d.log` f37745). A positional cut
            # inverts itself exactly when a replacement is needed. See `ally_party_indices`.
            from modules.battle_strategies.default import ally_party_indices

            _ally = ally_party_indices(battle_state)

            def _excluded(index) -> bool:
                if index in _ally:
                    return True
                if not battle_state.is_double_battle:
                    return False
                for battler in (battle_state.own_side.left_battler, battle_state.own_side.right_battler):
                    if battler is not None and battler.party_index == index:
                        return True
                return False

            candidates = []
            for index, mon in enumerate(_gp()):
                if mon is None or mon.is_egg or mon.current_hp <= 0 or _excluded(index):
                    continue
                try:
                    mon_types = list(mon.species.types)
                except Exception:
                    mon_types = []
                candidates.append((index, mon, mon_types))

            # ⭐⭐ KI-95 — SCORE BY EXPECTED DAMAGE, NOT BY A BARE TYPE MULTIPLIER. This reuses the
            # SHIPPED formula that `decide_turn` (a few lines below) already trusts, rather than
            # inventing a second one: base power, STAB, level, stats and the immunity abilities all
            # come along for free. ⛔ It also skips `banned_moves`, because `08-MISTAKES.md` says a
            # move's value is only real if the policy can deliver it — `battle.yml` bans Fly/Dive as
            # 2-turn moves, so ranking a mon highly for its Dive promised damage `decide_turn` would
            # then refuse to deal.
            _util = BattleStrategyUtil(battle_state)

            def _damage_of(mon, learned, foe):
                try:
                    if learned.move.name in context.config.battle.banned_moves:
                        return 0.0
                    return float(_util.calculate_move_damage_range(learned.move, mon, foe).max)
                except Exception:
                    return None  # "could not estimate" — counted, never silently read as 0 damage

            best_index, report = rank_replacement(candidates, foe_types, foes, _damage_of)
            if best_index is not None:
                # ⭐ THE CONTROL THAT MUST FIRE. `estimates_ok=0` in a real battle means the damage
                # formula never ran and the ranker silently fell back to the legacy multiplier — i.e.
                # `KI-95` is NOT actually fixed at runtime. It is logged rather than asserted because
                # instrumentation must never affect a battle, but it is now VISIBLE instead of mute.
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"[FAINT-CHOOSER] KI-95 rank -> slot {best_index} "
                        f"metric={report['metric']} "
                        f"estimates_ok={report['estimates_ok']} "
                        f"estimates_failed={report['estimates_failed']} key={report['key']}",
                        category="BATTLE",
                    )
                except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
                    pass
                return best_index
        except Exception:
            pass
        return super().choose_new_lead_after_faint(battle_state)

    def decide_turn(self, battle_state):
        if battle_state.is_trainer_battle:
            util = BattleStrategyUtil(battle_state)
            active = battle_state.own_side.active_battler
            move = util.get_strongest_move_against(active, battle_state.opponent.active_battler)
            if move is not None:
                return TurnAction.use_move(move)
            # No "strongest" (damaging, in-PP) move. A trainer / gym-leader / Elite-Four
            # battle CANNOT be fled and must NEVER stall (user directive 2026-07-21). Do NOT
            # fall through to the parent's rotate/flee path:
            #   • fleeing a trainer battle raises ("can't run from a trainer"), and
            #   • rotating into a weak/underlevelled bench can HANG the in-battle party-menu
            #     switch (battle_action_selection.py — "while PARTY_MENU: press A") — this is
            #     the Roxanne hang the user hit with Torchic (Fire) vs Rock + an L6-7 bench.
            # Instead keep ATTACKING with any move that still has PP (the game auto-uses
            # STRUGGLE if none), so the fight plays through to a win or a clean whiteout
            # (which triggers StoryMode's recovery). When the active mon faints,
            # handle_fainted_pokemon brings in the next one — we never proactively rotate in
            # a trainer battle, which sidesteps the party-menu-switch hang entirely.
            if active is not None:
                for i, learned in enumerate(active.moves):
                    if learned is not None and util.move_is_usable(learned):
                        return TurnAction.use_move(i)
                # ‼ SECOND PASS ON *PP ALONE* (2026-07-24, batch2 treecko hang at f1.2M:
                # `instr=BattleScript_SelectingMoveWithNoPP`,
                # `bt="There's no PP left for this move"`, inside
                # `EventScript_DoTrainerBattle` — 15,000 frames of no progress).
                # `move_is_usable` is STRICTER than "has PP" (it also rejects e.g.
                # disabled/zero-power moves), so a mon can fail every usability check
                # while still holding moves with PP. The old fallback then selected
                # SLOT 0 blindly — and Gen 3 does NOT silently substitute Struggle for
                # that: it prints "There's no PP left for this move!" and bounces
                # straight back to move selection. In an unfleeable trainer battle that
                # is an infinite loop. Struggle is only auto-used when EVERY move is out
                # of PP, in which case the game never shows the menu at all. So: pick
                # any move that genuinely has PP before falling back.
                for i, learned in enumerate(active.moves):
                    if learned is not None and learned.pp > 0:
                        return TurnAction.use_move(i)
            return TurnAction.use_move(0)  # every move truly at 0 PP → the game Struggles
        return super().decide_turn(battle_state)

    def decide_turn_in_double_battle(self, battle_state, battler_index):
        """Trainer DOUBLE battles must ATTACK THROUGH exactly like singles. They are very
        reachable: Emerald starts a TRUE double battle whenever TWO trainers spot you at
        once (e.g. walking between the Rustboro gym Youngsters), plus scripted pairs like
        Gabby & Ty. The inherited Default double path calls _handle_lead_cannot_battle
        when the actives are weak, and with the stock 'flee' config that RAISES in a
        trainer battle → Manual mid-battle (the user-reported "double battle bug";
        reproduced + chain-fixed via the KI-12 faint-bench repro 2026-07-22). Here:
        strongest usable move at whichever opponent is present; any in-PP move as
        fallback; Struggle at 0 PP; never flee, never rotate, never stall."""
        if not battle_state.is_trainer_battle:
            return super().decide_turn_in_double_battle(battle_state, battler_index)
        util = BattleStrategyUtil(battle_state)
        battler = (
            battle_state.own_side.left_battler if battler_index == 0 else battle_state.own_side.right_battler
        )
        left_opp = battle_state.opponent.left_battler
        right_opp = battle_state.opponent.right_battler
        # ALIVE, not merely present: a FAINTED opponent still has a battler object, and
        # targeting it raises "Cannot attack the left-side opponent Pokémon because
        # there isn't one" — an uncatchable mid-battle mode death (batch runs 01+03,
        # 2026-07-22, both at the same trainer pair once one opponent went down).
        left_alive = left_opp is not None and getattr(left_opp, "current_hp", 0) > 0
        right_alive = right_opp is not None and getattr(right_opp, "current_hp", 0) > 0

        def _default_target(move_index: int):
            if right_alive and not left_alive:
                return TurnAction.use_move_against_right_side_opponent(move_index)
            return TurnAction.use_move(move_index)

        if battler is None:
            return _default_target(0)
        if left_alive:
            move = util.get_strongest_move_against(battler, left_opp)
            if move is not None:
                return TurnAction.use_move(move)
        if right_alive:
            move = util.get_strongest_move_against(battler, right_opp)
            if move is not None:
                return TurnAction.use_move_against_right_side_opponent(move)
        for i, learned in enumerate(battler.moves):
            if learned is not None and util.move_is_usable(learned):
                return _default_target(i)
        # Same PP-only last resort as the single-battle branch above — see the long
        # comment there. Selecting a 0-PP move does NOT make the game Struggle; it
        # prints "There's no PP left for this move!" and re-opens the menu, which in an
        # unfleeable trainer DOUBLE battle (e.g. the Rustboro gym Youngster pair) is the
        # same infinite loop.
        for i, learned in enumerate(battler.moves):
            if learned is not None and learned.pp > 0:
                return _default_target(i)
        return _default_target(0)  # every move truly at 0 PP → the game Struggles

    def which_move_should_be_replaced(self, pokemon, new_move) -> int:
        """Story move-learning policy — keep every Pokémon COMBAT-CAPABLE.

        Called when a Pokémon with 4 moves is about to learn a new one (the stock
        config default `new_move: cancel` would just decline everything, so the
        starter would never improve — hence this override). Returns 0-3 to
        overwrite that slot, or 4 to DECLINE (keep the current moves).

        PRIORITY / RULES (in order):
          1. Never replace an HM move (can't anyway, and Cut/Surf/... are needed
             for field use); never learn a block-listed move.
          2. GUARANTEE combat capability: a damaging move is NEVER replaced by a
             status move, so a Pokémon can't end up with only non-combat moves.
             (Damaging-move count never decreases.)
          3. New STATUS move: accept it only by overwriting an existing (non-HM)
             STATUS slot; if every non-HM slot is a damaging move, DECLINE — don't
             trade attacking power for utility.
          4. New DAMAGING move: (a) upgrade a non-combat/status slot first (pure
             win). Else, among damaging slots, PRESERVE TYPE COVERAGE:
             - if the new move's type is ALREADY covered, only overwrite a WEAKER
               same-type move (a STAB/power upgrade); otherwise DECLINE — don't
               churn or lose a different type for a redundant one;
             - if the new move adds a type we LACK, free a redundant-type slot
               first (so no unique type is lost), else replace the weakest move.

        "Effective power" = base power x (Attack or Sp.Atk) x STAB — the same
        yardstick the stock `learn_best` uses, so choices stay sensible.
        Status-move *utility* ranking (e.g. valuing Sleep Powder over Growl) is a
        future refinement (punch-list #24-team); for now combat moves win."""
        DECLINE = 4
        if new_move.name in context.config.battle.banned_moves:
            return DECLINE

        moves = [lm.move if lm is not None else None for lm in pokemon.moves]

        def is_hm(m):
            return m is not None and m.tm_hm is not None and m.tm_hm.name.startswith("HM")

        def is_damaging(m):
            return m is not None and m.base_power > 0

        def effective_power(m):
            if m is None or not is_damaging(m):
                return 0.0
            if m.type.kind == "Physical":
                stat = pokemon.stats.attack
            elif m.type.kind == "Special":
                stat = pokemon.stats.special_attack
            else:
                stat = 1
            stab = 1.5 if m.type in pokemon.species.types else 1.0
            return m.base_power * stat * stab

        status_slots = [i for i, m in enumerate(moves) if m is not None and not is_damaging(m) and not is_hm(m)]
        damaging_slots = [i for i, m in enumerate(moves) if is_damaging(m) and not is_hm(m)]

        # New STATUS move: only ever replace another status slot (never a
        # damaging move or an HM). If no spare status slot, keep our attacks.
        if not is_damaging(new_move):
            return status_slots[0] if status_slots else DECLINE

        # New DAMAGING move.
        # (a) Overwrite a non-combat slot first — strictly upgrades the kit.
        if status_slots:
            return status_slots[0]
        # Every non-HM slot is now a damaging move; never touch an HM.
        if not damaging_slots:
            return DECLINE
        new_power = effective_power(new_move)
        # ⛔⛔ COVERAGE IS COUNTED OVER **EVERY** DAMAGING MOVE, HMs INCLUDED — AND COUNTING IT OVER
        # `damaging_slots` (which EXCLUDES HMs) COST THIS PROJECT THE ONE MOVE §Ch24 IS BUILT AROUND.
        # ‼ MEASURED 2026-09-17, exactly reproducible on the grind ladder: Wailord knew
        # `Dive (HM08), Surf (HM03), Ice Beam (TM13), Waterfall (HM07)` and hit **L59 / Hydro Pump**.
        # Three of its four moves are Water, but all three are HMs, so `damaging_slots` was `[Ice
        # Beam]` alone and the census read `current_types == [Ice]`. ⇒ Hydro Pump (Water) looked like
        # a type we **LACK**, the code "freed the weakest slot to gain coverage", and the team's ONLY
        # Ice move — fetched by a ~700,000-frame Abandoned Ship round trip specifically because the
        # analysis says the party LOSES to Drake without it — was traded for a FOURTH Water move.
        #     post_e4grind_L57.ss1  L57  Dive, Surf, Ice Beam,   Waterfall
        #     post_e4grind_L59.ss1  L59  Dive, Surf, Hydro Pump, Waterfall   <<< -Ice Beam +Hydro Pump
        # ⭐ ONE MECHANISM EXPLAINS THE OPPOSITE OBSERVATION TOO, WHICH IS WHY IT IS THE RIGHT ONE.
        # On the other lineage Wailord held **Water Spout** (a TM, so non-HM) in that slot: the census
        # read `[Water]`, Hydro Pump was REDUNDANT, Water Spout (150 BP) outranks it, and the policy
        # correctly DECLINED — keeping all four moves across the same level. Same code, same level,
        # opposite outcome, explained by which slot happened to be replaceable.
        # ⇒ **REPLACEABILITY AND COVERAGE ARE DIFFERENT QUESTIONS.** You cannot overwrite an HM, but
        # the Pokémon still KNOWS it, and coverage is about what it can DO. The replaceable set stays
        # `damaging_slots`; only the census widens.
        coverage_slots = [i for i, m in enumerate(moves) if is_damaging(m)]
        current_types = [moves[i].type for i in coverage_slots]

        if new_move.type in current_types:
            # Redundant type: only take it to UPGRADE a weaker same-type move;
            # otherwise decline (don't lose a different type for a redundant one).
            weaker_same_type = [
                i for i in damaging_slots
                if moves[i].type == new_move.type and effective_power(moves[i]) < new_power
            ]
            if weaker_same_type:
                return min(weaker_same_type, key=lambda i: effective_power(moves[i]))
            return DECLINE

        # New TYPE coverage: free a redundant-type slot first (keep every unique
        # type), else replace the weakest damaging move.
        type_counts: dict = {}
        for t in current_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        redundant_slots = [i for i in damaging_slots if type_counts[moves[i].type] > 1]
        pool = redundant_slots if redundant_slots else damaging_slots
        return min(pool, key=lambda i: effective_power(moves[i]))

    def should_allow_evolution(self, pokemon, party_index) -> bool:
        # A story auto-completer WANTS its team to evolve — stronger for gyms, and
        # it fixes the Lv-up handler collision the user hit at Treecko Lv16
        # (evolves + learns Pursuit at the same level): with the stock
        # `stop_evolution` default the evolution is force-CANCELLED, and the
        # cancelled-evolution + move-learn handoff can spin without stopping the
        # bot. Letting the evolution COMPLETE runs the well-tested evolve→learn
        # path instead. Always allow (this overrides `stop_evolution` for Story
        # battles). Ties to #24-evo / #24-team.
        return True


class StoryItemBattleStrategy(LevelUpTravelBattleStrategy):
    """`#24-battleitems` — fights like LevelUpTravel, but USES HEALING ITEMS in trainer battles.

    USER DIRECTIVE 2026-08-09: *"I want the bot to use items intelligently and strategically."*

    ‼ WHY, MEASURED. Batch `20260809-155844` (16,749 battles) found **the opponent healing and the
    bot never doing so**: Norman's `Slaking` was restored **27 times, median +81 HP, max +119**
    while the party did 6-8 chip damage a turn, and **61.8% of boss-length battles** show an
    opponent heal. Boss losses end **~88% of all non-finishing runs**. The counter chain answers
    "what type beats this" — which cannot beat an opponent that out-heals us.

    ‼ SCOPE IS TRAINER BATTLES ONLY, deliberately. Wild encounters keep the existing behaviour
    exactly: spending potions on a route wild is the opposite of "strategically", and narrowing
    the blast radius means a mistake here cannot touch the training/catching paths that are
    already measured and working.

    ‼ THE POLICY IS NOT IN THIS CLASS. It lives in `modules/story/battle_items.py` as a PURE
    function so it can be tested exhaustively without an emulator (`repro_battle_items.py`, 27
    checks). This class only supplies the facts the policy needs — current HP, what is in the bag,
    the biggest hit taken so far — and turns its answer into a `TurnAction`.

    ‼ AND IT FAILS OPEN. Every part of the decision is wrapped so that any error falls straight
    through to the normal strategy: a new feature must not be able to break a battle that worked
    before it existed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #: items used THIS battle — the bound that stops a heal-war with a healing boss
        self._item_uses = 0
        #: biggest single HP loss observed this battle, for the "don't heal into a losing race" rule
        self._worst_hit = 0
        #: last seen HP per party index, to derive the above
        self._hp_seen: dict = {}
        #: ‼ NO-OP DETECTOR (see `_maybe_use_item`). `(party_index, hp)` at the moment we last
        #: asked for an item — the INDEX is half the value: without it the check compares two
        #: different Pokémon. See `08-MISTAKES` 2026-08-10.
        self._hp_when_item_requested = None
        #: Set ONLY when the requested item was a STATUS CURE, so the HP-delta no-op
        #: detector never judges one. See the block in `_maybe_use_item`.
        self._status_when_item_requested = None
        #: set once BOTH index spaces have demonstrably done nothing; stops wasting more turns
        self._items_ineffective = False
        #: which index space to address the party menu in. ‼ NOT a constant: the FIRST choice is
        #: made per use by `_preferred_index_space()` from measured data, and the self-correcting
        #: block below flips it once if that guess is wrong.
        self._index_space = "party"
        #: only ever flip once per battle, so a failure costs one extra turn and not a loop
        self._index_space_flipped = False
        #: ‼ `KI-101` blocker-1 (2026-09-16, found by an adversarial review of the KI-101 fix):
        #: `(item, bag_quantity)` banked at REQUEST time so the verdict can ask the only question
        #: that actually has a crisp answer — WAS THE ITEM CONSUMED?
        self._item_qty_when_requested = None

    def decide_turn(self, battle_state):
        try:
            action = self._maybe_use_item(battle_state)
        except Exception:  # noqa: BLE001 - a battle that worked before must keep working
            action = None
        if action is not None:
            return action
        return super().decide_turn(battle_state)

    def _maybe_use_item(self, battle_state):
        # ⛔⛔ `_os` IS BOUND ONCE, HERE, AT THE TOP — AND THAT POSITION IS LOAD-BEARING.
        # `os` is NOT imported at module scope in this file (local-import convention). It was
        # previously imported deep inside the status-cure branch, and step 4's knob then read it
        # ~40 lines EARLIER. ‼ In Python a local `import` anywhere in a function makes that name
        # LOCAL FOR THE WHOLE FUNCTION, so the earlier read is an `UnboundLocalError` — which even
        # a module-level `os` would NOT have rescued. And `decide_turn` wraps this entire method in
        # `try/except Exception: action = None`, so the failure is SILENT: no item is ever used, in
        # any battle, with every gate still green.
        # ⇒ the prevention rule from 2026-09-13 ("a safe default on an unverified name is a silent
        # off-switch; verify the name is bound in YOUR scope") fired on its second day. Keep the
        # binding at the top; do not re-scatter it into branches.
        import os as _os

        from modules.battle_state import BattleType
        from modules.items import ItemBattleUse, get_item_bag
        from modules.story.battle_items import choose_healing_item

        if BattleType.Trainer not in battle_state.type:
            return None  # wilds keep the existing behaviour, untouched
        mon = battle_state.own_side.left_battler
        if mon is None or mon.total_hp <= 0:
            return None

        # Track the biggest hit we have actually taken, per mon, so the policy can refuse to
        # heal when healing would still lose the exchange.
        previous = self._hp_seen.get(mon.party_index)
        if previous is not None and previous > mon.current_hp:
            self._worst_hit = max(self._worst_hit, previous - mon.current_hp)
        self._hp_seen[mon.party_index] = mon.current_hp

        # ‼‼ NO-OP DETECTOR — MEASURED NECESSARY, NOT DEFENSIVE PROGRAMMING (2026-08-09).
        # The first live A/B of this feature selected `Hyper Potion` FOUR times on the SAME turn
        # of the Norman fight with HP frozen at `23/120`, and the bag afterwards showed **3 of 4
        # potions still there** — i.e. one of five requests actually consumed an item. The battle
        # menu flow does not reliably execute a `UseItem` action, and each failed request costs a
        # TURN. Without this guard the feature is a REGRESSION in exactly the fight it was built
        # for: four donated turns against a boss.
        # So: if a request did not raise our HP by the next decision, stop asking for this battle.
        # That bounds the damage to one wasted turn while the execution bug is still open.
        # ⛔⛔ A STATUS CURE IS JUDGED BY THE STATUS, NEVER BY HP (`#24-e4healing`, 2026-09-13).
        # THE BUG THIS PREVENTS, found by a Tier 1 reviewer before it shipped: the detector below is
        # purely HP-delta, and a Full Heal / Awakening / Ice Heal NEVER RAISES HP. So a SUCCESSFUL
        # cure reads as "the item did nothing" — the first one flips the index space, and the second
        # sets `_items_ineffective = True`, which disables ALL item use for the rest of the battle,
        # **including genuine HP-emergency healing**, in the Elite Four gauntlet this was built for.
        # Two cures in one battle is not exotic: `pokemon_league.py`'s own driver stages a FROZEN
        # Sceptile precisely because freeze and sleep both occur.
        # ⇒ this branch is checked FIRST and returns early, so the HP logic below is UNTOUCHED —
        # it took three measured iterations (KI-34, the 2026-08-10 same-subject fix, the index-space
        # flip) and must not be disturbed by a feature it knows nothing about.
        if self._status_when_item_requested is not None:
            cured_index, cured_status = self._status_when_item_requested
            self._status_when_item_requested = None
            if mon.party_index == cured_index and mon.current_hp > 0:
                now = getattr(mon.status_permanent, "name", str(mon.status_permanent))
                worked = now != cured_status
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"[ITEM] status cure {'✔ WORKED' if worked else '‼ no change'}: "
                        f"{cured_status} -> {now}"
                        + ("" if worked else "  (NOT counted against the no-op detector — a cure "
                                             "that fails is a menu problem, not a wrong target)"),
                        category="BATTLE",
                    )
                except Exception:  # noqa: BLE001 — TELEMETRY MUST NEVER BREAK A BATTLE. This block
                    # only writes a debug-log line saying whether the cure changed the status; if the
                    # logger is unavailable the CURE HAS ALREADY HAPPENED and the turn is already
                    # spent. Re-raising here would turn a logging failure into a lost Elite Four run.
                    # ⛔ Nothing is decided in this handler — the branch above has already cleared
                    # `_status_when_item_requested`, so a swallow here cannot change behaviour.
                    pass

        if self._hp_when_item_requested is not None:
            requested_index, requested_hp = self._hp_when_item_requested
            # ‼‼ `KI-101` HALF TWO (2026-09-16) — JUDGE A FRESH READ, NEVER THE ENTRY SNAPSHOT.
            # ⛔ WITHOUT THIS, A WORKING FIX LOOKS LIKE A FAILED ONE. `handle_battle_action_selection`
            #   captures `battle_state` ONCE on entry and re-reads it only when the BATTLER changes,
            #   and `BattlePokemon` holds the bytes it was built from — so every decision inside one
            #   action-selection entry sees the SAME pre-item HP. That is why the Sidney log printed
            #   `[TURN 13] Mightyena L48 23/144` three times identically: one frozen object, three
            #   renderings. Had the heal landed, this detector would STILL have read 23, flipped the
            #   index space, burned a second item and then disabled items for the battle.
            # ⇒ the verdict — and ONLY the verdict — is taken from a fresh read. `mon` above still
            #   drives the healing DECISION, untouched, because re-reading there would change a
            #   policy this change is not about.
            # ⚠ AND IT RETIRES SOME EVIDENCE: any "items never execute" reading taken inside one
            #   entry is void as proof of execution, including the 2026-09-14 STEP4 note
            #   ("the request DID NOT EXECUTE (HP 68 -> 68)"). Do not cite those as a baseline.
            judge = mon
            try:
                from modules.battle_state import get_battle_state as _ki101_state

                _judge_state = _ki101_state()
                _judge_mon = _judge_state.own_side.left_battler if _judge_state is not None else None
                if _judge_mon is not None:
                    judge = _judge_mon
            except Exception as _ki101_judge_error:  # noqa: BLE001
                # ‼ ADMITTED, NOT SILENT: fall back to the snapshot and SAY SO, because a verdict
                #   taken on stale bytes is exactly what this block exists to stop.
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"[ITEM] KI-101 fresh-read failed ({type(_ki101_judge_error).__name__}); "
                        f"judging on the ENTRY SNAPSHOT — this verdict may be a false negative",
                        category="BATTLE",
                    )
                except Exception:  # noqa: BLE001
                    pass
            # ‼‼ ONLY JUDGE THE SAME POKÉMON, AND ONLY IF IT IS STILL ALIVE (fixed 2026-08-10).
            # This check used to read `own_side.left_battler` at the next decision and compare it
            # against the HP recorded for whoever asked for the item — but after a faint that is
            # the REPLACEMENT mon, so the guard blamed the item for a death. Measured: **9 of the
            # 10 "both index spaces failed" verdicts** in batch `20260810-035733` were immediately
            # followed by a `[FAINT-CHOOSER]`. A before/after comparison must prove it is
            # comparing the same subject.
            # ‼‼ `KI-101` BLOCKER 1 (2026-09-16) — JUDGE **CONSUMPTION**, NOT AN HP DELTA.
            # ⛔ AN ADVERSARIAL REVIEW OF THE KI-101 FIX CAUGHT THIS USING THE FIX'S OWN EVIDENCE, and
            #   the measurement is worse than the review supposed. In the ARM-ON drive:
            #       use 1:  23/144 -> 144/144   (+121, clean)
            #       use 2:   2/147 ->   6/147   (+4)      <- verdict survived by FOUR HP
            #       use 3:   6/147 ->  80/147   (+74)
            #   A Full Restore MAXES HP, so uses 2 and 3 should read 147. And it was NOT a
            #   counter-hit: `worst hit` never rises above 81, so no 141-damage blow ever landed.
            #   ⇒ the post-turn HP read is a TRANSIENT, and the old verdict rested on its SIGN with a
            #   margin as thin as 4 HP. A slightly different timing flips a WORKING heal to
            #   "no effect", and two of those disable every item for the rest of the battle — in the
            #   five-fight one-way gauntlet this feature exists for.
            # ⭐ THE DECOMP ALREADY NAMED THE RIGHT OBSERVABLE: `RemoveBagItem(item, 1)` sits ONLY in
            #   the success branch of `ItemUseCB_Medicine` (`src/party_menu.c:4396-4435`), and a
            #   non-Revive HP item on a 0-HP mon is refused WITHOUT consuming it
            #   (`src/pokemon.c:5056-5060`). So "did the count drop" is exactly "did it apply", and it
            #   is immune to counter-hits, HP animations and index spaces alike.
            # ‼ THIS IS THE PROJECT'S OWN RULE — INSTRUMENT THE ACTION, NOT A PROXY FOR IT. HP was a
            #   proxy; the bag count is the action. HP is still REPORTED below, because it is useful
            #   to a reader, but it no longer DECIDES.
            _consumed = None
            if self._item_qty_when_requested is not None:
                _req_item, _req_qty = self._item_qty_when_requested
                if _req_qty is not None:
                    try:
                        _consumed = get_item_bag().quantity_of(_req_item) < _req_qty
                    except Exception:  # noqa: BLE001
                        _consumed = None  # unreadable -> fall through to the HP heuristic
            if _consumed is True:
                # The item applied. Clear the trackers and say so with BOTH readings, so the HP
                # transient stays visible as data without being load-bearing.
                # ‼ ROUTED THROUGH THE EXISTING `_log_story_event` RATHER THAN A NEW try/except.
                #   `repro_no_silent_except`'s per-root ratchet caught two new silent handlers here
                #   (plugins/custom_modes 81 > 79) and it was RIGHT: new debt may not be funded by
                #   another root's headroom. One shared safe logger is the paydown, not a budget bump.
                _log_story_event(
                    f"[ITEM] ✔ CONSUMED (bag count dropped) — the item applied. "
                    f"HP reads {judge.current_hp}/{judge.total_hp} "
                    f"(a post-turn value, NOT the heal's result — see KI-101 blocker 1)",
                    category="BATTLE",
                )
                self._hp_when_item_requested = None
                self._item_qty_when_requested = None
            elif judge.party_index != requested_index or judge.current_hp == 0:
                self._hp_when_item_requested = None
            elif _consumed is False:
                # NOT consumed: the menu flow completed but the game refused or we backed out. This
                # is the genuine failure the guard exists for, and it is now distinguishable from a
                # heal whose HP reading merely looked unconvincing.
                self._item_qty_when_requested = None
                if not self._index_space_flipped:
                    self._index_space_flipped = True
                    note = "the item was NOT consumed — retrying once"
                else:
                    self._items_ineffective = True
                    note = "the item was NOT consumed twice; disabling items for the rest of this battle"
                _log_story_event(f"[ITEM] ‼ not consumed — {note}", category="BATTLE")
                self._hp_when_item_requested = None
            elif judge.current_hp <= requested_hp:
                # ‼‼ SELF-CORRECTING INDEX SPACE (2026-08-10) — because the question cannot be
                # settled by reading the code. Measured: 85 targeted uses completed the FULL menu
                # flow and 32 battles saw no HP rise, so the potion lands on the WRONG MON; and
                # the two candidate spaces disagree constantly in the logs (`party 0` vs
                # `battle-order 1` x19, `(1,0)` x12). The after-faint chooser treats
                # `map_battle_party_index()` as MENU order and is right there (that is the KI-34
                # fix), while the fixture proved the PARTY index right for the item menu — so the
                # two menus are simply not ordered the same way, and a third guess would be a
                # guess. Instead: when a use demonstrably does nothing, FLIP the space and try
                # once more, and LOG which one worked. One wasted turn buys the answer, and a
                # batch of these lines settles the convention with data instead of argument.
                if not self._index_space_flipped:
                    self._index_space_flipped = True
                    self._index_space = "battle" if self._index_space == "party" else "party"
                    note = f"retrying with the {self._index_space}-order index"
                else:
                    self._items_ineffective = True
                    # ⛔ WORDING CORRECTED 2026-09-16: "both index spaces failed" is no longer
                    #   true — the index space stopped selecting the target when the driver took
                    #   over (KI-101). This branch is now only reachable when the bag count was
                    #   UNREADABLE and the HP heuristic fell through twice.
                    note = ("HP did not rise on two attempts and the bag count was unreadable; "
                            "disabling items for the rest of this battle")
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"[ITEM] ‼ no effect (HP still {judge.current_hp}/{judge.total_hp}) — {note}",
                        category="BATTLE",
                    )
                except Exception:  # noqa: BLE001
                    pass
            elif self._item_uses >= 1:
                # It WORKED — record which space did it. This is the line that answers the
                # question across a batch.
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"[ITEM] ✔ landed (KI-101: the DRIVER resolved the menu slot after bag-open; "
                        f"`_index_space`={self._index_space!r} is a legacy LABEL and no longer "
                        f"selects the target) "
                        f"(HP now {judge.current_hp}/{judge.total_hp})",
                        category="BATTLE",
                    )
                except Exception:  # noqa: BLE001
                    pass
            self._hp_when_item_requested = None
        if self._items_ineffective:
            return None

        # ⛔ TWO OPTION LISTS, BECAUSE `parameter` IS A UNION TYPE. `battle_use is Healing` is the
        # KIND check and does the real work (it already excludes a Repel, whose parameter is 100
        # *steps*). The extra `parameter > 0` is an HP filter and belongs ONLY to the HP policy —
        # it is exactly what made Full Heal / Revive / Antidote unusable (`#24-e4healing`).
        medicine = [
            (slot.item, slot.quantity, slot.item.parameter)
            for slot in get_item_bag().items
            if slot.item.battle_use is ItemBattleUse.Healing
        ]
        # ⛔ USER RULING 18 — THE LEAGUE RESERVE. Both policies below see `quantity − reserved` for every
        # `LEAGUE_BASKET` line while the reserve is armed (Juan era → entering the Elite Four; state-derived, see
        # `modules/story/league_reserve.py`). FILTERED HERE, BEFORE the policy — never a veto of its pick, which would
        # lose today's fallback to a Super Potion. ⛔ ONLY here: the bag readers (leg 11, R1, the Elite Four's
        # between-room heal) must keep reading the RAW bag. ⛔ FAILS UNLOCKED — even an import error leaves
        # `medicine` untouched, because `decide_turn` swallows exceptions from this method and a crash here once
        # disabled ALL item use with every gate green.
        try:
            from modules.story.league_reserve import filter_medicine_for_reserve as _league_reserve_filter

            medicine = _league_reserve_filter(medicine)
        except Exception:  # noqa: BLE001 - fail UNLOCKED: a broken reserve must never disable item use
            pass
        options = [opt for opt in medicine if opt[2] > 0]
        # ---- `#24-e4healing` step 4 — the A/B KNOB for `HEAL_AT_FRACTION`. --------------------
        # ⛔ DEFAULT UNCHANGED. Unset -> `heal_at_fraction` is not passed at all and the module
        # default (0.35) applies, byte-for-byte the behaviour that shipped.
        # ‼ WHY A KNOB AND NOT AN EDIT. This policy runs in EVERY battle of the run (~700), not
        # just the Elite Four, and this project's rule 9 is explicit: a change on a SHARED PATH is
        # decided by an A/B on the ORDINARY case, not by more samples of the exotic one. The knob
        # is how that A/B gets run without touching the default for everyone first.
        # ⭐ WHAT IT IS FOR — the defect, VERIFIED by executing the real policy 2026-09-14:
        #     at 53/147 (36.1%) -> None      ... the next 59-damage hit leaves -6  ☠
        #     at 51/147 (34.7%) -> Full Restore, and the mon lives.
        #   Generalised: a hit worth **50-64% of max HP** leaves the mon ABOVE the 0.35 gate, so it
        #   never heals, and the NEXT identical hit faints it. A guaranteed two-shot the policy does
        #   not try to prevent. Decomp rosters put Elite Four hits squarely in that band.
        # ⛔ 0.50 is the principled MINIMUM that closes it (heal at or below half). It is NOT yet
        # the default: see `29-DISABLED-FEATURES-REGISTRY.md` and the A/B this knob exists to run.
        _heal_frac = _os.environ.get("POKEBOT_HEAL_AT_FRACTION", "")
        _frac_kw = {}
        if _heal_frac:
            try:
                _frac_kw["heal_at_fraction"] = float(_heal_frac)
            except ValueError:
                # ⛔ A malformed knob must NOT silently become a different threshold. Ignore it and
                # keep the shipped default — the run then measures the DEFAULT, which is a wrong
                # answer to the A/B but never a wrong BEHAVIOUR.
                _frac_kw = {}
        # ⛔⛔ RECORD THE VALUE THE POLICY IS ACTUALLY CALLED WITH — session-discipline rule 7,
        # INSTRUMENT THE ACTION, NOT THE INPUT TO THE ACTION. Reading the env in the DRIVER would
        # only prove what was SET; this is what was USED. Without it, an A/B arm that silently ran
        # the default is indistinguishable from one that ran the override and lost — and the first
        # 0.50 arm produced exactly that ambiguity (it LOST, yet spent the same 2 items as the
        # default arm, which is not what a bound threshold should look like).
        from modules.story.battle_items import HEAL_AT_FRACTION as _DEFAULT_FRAC

        self._effective_heal_fraction = _frac_kw.get("heal_at_fraction", _DEFAULT_FRAC)
        item = choose_healing_item(
            mon.current_hp,
            mon.total_hp,
            options,
            worst_hit_taken=self._worst_hit,
            uses_so_far=self._item_uses,
            **_frac_kw,
        )
        if item is None:
            # ‼ `#24-e4healing` step 3 — the parameter==0 half. Asked ONLY after the HP policy has
            # declined, so an HP emergency always outranks a status cure.
            # ⛔ `allow_revive=False` IS LOAD-BEARING, NOT TIMIDITY (`KI-100`). A cure targets the
            # ACTIVE battler — `mon.party_index`, the exact index this method already lands (see the
            # comment below: party-order landed 19 of 19 when the target was slot 0). A REVIVE would
            # target a FAINTED, NON-ACTIVE member: a different index space, and the one behind
            # KI-18/KI-34/KI-66. Until `KI-100`'s observe-only index probe exists, we do not aim there.
            # ⛔⛔ IT IS `status_permanent`, NOT `status_condition`. `BattlePokemon` has NO
            # `status_condition` property (it is `Pokemon` that does) — an earlier draft of this
            # wiring used that name behind a safe `getattr(..., None)`, which would have made the
            # cure NEVER FIRE, silently, forever, with every gate still green. Verified by listing
            # BattlePokemon's properties: `status_permanent -> StatusCondition` is the real one
            # (Sleep/Freeze/Poison/Burn/Paralysis); `status_temporary` holds Confusion and friends.
            # ⛔ `_os` is bound at the TOP of this method — see the comment there for why the
            # position matters. It was imported HERE until 2026-09-14; that made it an unbound
            # local for every earlier read in the same function.
            from modules.pokemon_party import get_party as _party
            from modules.story.battle_items import choose_status_or_revive_item

            item = choose_status_or_revive_item(
                mon.status_permanent,
                sum(1 for m in _party() if m is not None and not m.is_egg and m.current_hp > 0),
                medicine,
                uses_so_far=self._item_uses,
                allow_revive=False,
            )
            # ⛔ FAULT ARM ONLY — `POKEBOT_E4_FAULT_NOCURE`, registered in
            # `29-DISABLED-FEATURES-REGISTRY.md` §B. Restores the PRE-step-3 behaviour: the status
            # cure never fires, while the HP policy above is left completely untouched.
            # ‼ WHY IT EXISTS AT ALL. The staged-freeze drive claims "the bot cured a frozen lead".
            # Emerald thaws freeze on its own, so the ONLY currency this project accepts for that
            # claim is an arm with the cure REMOVED (session-discipline rule 8). It lives here, at
            # the call site, and NOT inside `battle_items.py` — that module has zero imports by
            # design, which is exactly what lets gate #59 test it as a pure function.
            if item is not None and _os.environ.get("POKEBOT_E4_FAULT_NOCURE", "") == "1":
                item = None
        if item is None:
            return None

        self._item_uses += 1
        # ⛔ RECORD WHICH KIND WAS ASKED FOR. `parameter == 0` is the status/revive family (Full
        # Heal, Awakening, Ice Heal, Revive) — those never raise HP, so they must NOT be handed to
        # the HP-delta no-op detector, which would read a successful cure as a failure and
        # eventually disable every item for the battle.
        if getattr(item, "parameter", 0) > 0:
            self._hp_when_item_requested = (mon.party_index, mon.current_hp)
            # ‼ BANK THE BAG COUNT TOO — see the verdict block for why HP alone is not trustworthy.
            try:
                self._item_qty_when_requested = (item, get_item_bag().quantity_of(item))
            except Exception:  # noqa: BLE001
                # ADMITTED: an unreadable bag is not a reason to skip the heal; the verdict falls
                # back to the HP heuristic and SAYS SO in its log line.
                self._item_qty_when_requested = None
        else:
            self._status_when_item_requested = (
                mon.party_index,
                getattr(mon.status_permanent, "name", str(mon.status_permanent)),
            )
        try:
            from modules import debug_logger

            debug_logger.event(
                f"[ITEM] using {item.name} on {getattr(mon.species, 'name', '?')} "
                f"{mon.current_hp}/{mon.total_hp} (use {self._item_uses}, worst hit {self._worst_hit})",
                category="BATTLE",
            )
        except Exception:  # noqa: BLE001
            pass
        # ‼ THE STRATEGY OWNS THE INDEX SPACE, not the menu driver. `battle_action_use_item` now
        # uses whatever index it is given verbatim, so the choice — and the self-correction above
        # — belong here, where the outcome can actually be observed.
        # ‼ FIRST CHOICE IS NOW DATA-DRIVEN (batch `20260810-035733`, 29 landings). Cross-tabulating
        # which space LANDED against the target's party position gave a clean split:
        #     party-order landed  19 of 19  when the target was party slot 0, and 0 times above it
        #     battle-order landed  9 of 10  when the target was ABOVE slot 0
        # (Every one of those 9 is a case where party order had already failed and cost a turn.)
        # So guess accordingly instead of always opening with party order. The flip below is kept
        # as the safety net — the rule is empirical, from 29 observations, not a proof.
        if not self._index_space_flipped:
            self._index_space = "party" if mon.party_index == 0 else "battle"

        # ‼‼ `KI-101` (2026-09-16) — THE STRATEGY STATES *INTENT*; THE DRIVER RESOLVES THE SLOT.
        # ⛔ THE PRE-MAPPING THAT USED TO HAPPEN HERE WAS THE BUG, TWICE OVER: it mapped (a) from the
        #   FROZEN entry `battle_state` snapshot, and (b) BEFORE the bag was open — and
        #   `PlayerHandleChooseItem` refills `gBattlePartyCurrentOrder` AT bag-open
        #   (`src/battle_controller_player.c:2653-2663`). `battle_action_use_item` now re-reads the
        #   order once the party menu is actually up, which is the only moment the array is true.
        # ⇒ ALWAYS PASS THE PARTY INDEX. It is the one number that means the same thing on both
        #   sides of the menu, and identity is what this project asks assertions to carry.
        #
        # ⚠ `self._index_space` AND ITS FLIP ARE NOW INERT FOR TARGETING, AND THAT IS DELIBERATE
        #   RATHER THAN AN OVERSIGHT — saying so because a mechanism that LOOKS live and is not is a
        #   failure shape this project has paid for. They are kept, unremoved, for two reasons:
        #     1. they still label the log line, so the historical `[ITEM] ✔ landed using the
        #        <space>-order index` corpus stays comparable across the fix; and
        #     2. it still buys a SECOND ATTEMPT at a flaky menu before items are disabled.
        #   ⛔ BUT BE PRECISE ABOUT WHAT IT IS NOW, because an earlier draft of this very comment
        #     overclaimed and I caught it reading my own diff: the flip is a PLAIN RETRY, **not** a
        #     fallback that re-aims. Both attempts now resolve the same menu slot via the driver, so
        #     a genuine targeting failure costs two attempts and then disables items — where the old
        #     code at least tried a different space. That trade is accepted deliberately: the old
        #     "different space" was measured to be two readings of the SAME stale array, so it never
        #     corrected anything, and a retry that admits it is a retry beats one that pretends to
        #     be a correction.
        #   ⛔ Do NOT read `_index_space` as "which space we aim in" any more — the driver decides.
        #   The 29-observation rule above is now understood as the SIGNATURE of the stale array
        #   (at slot 0 the stale mapping is usually the identity), not as a convention.
        return TurnAction.use_item_on(item, mon.party_index)


class SwapTrainBattleStrategy(LevelUpTravelBattleStrategy):
    """SWAP-TRAINING (user directive 2026-07-21). Level a weak team member by having a
    stronger team-mate secure the KO while the trainee (which was sent out first)
    banks its Gen-3 shared-EXP — no fainting, minimal healing.

    Two triggers, both switching to a team-mate that can SAFELY finish the fight
    (out-levels the foe + healthy), preferring the strongest:

      1. UNDER-LEVELLED — the trainee is >= ``UNDERLEVEL_MARGIN`` levels below the
         foe: switch turn 1, before it takes any damage.
      2. CAN'T CONTINUE — the trainee fought a close-level foe and dropped to low HP
         (or ran out of usable moves): rather than FLEE for zero XP (old behaviour),
         switch so the team-mate finishes and the trainee keeps its XP share; the
         training loop then heals normally. (User: swap instead of flee.)

    If NO team-mate can safely finish, we fall through to the parent — which flees on
    low HP (safe) or solos a same-or-lower foe for FULL XP."""

    #: switch pre-emptively when the trainee is this many levels (or more) below the
    #: foe. Low (2) so it doesn't fight-and-flee winnable-looking-but-losing battles.
    UNDERLEVEL_MARGIN = 2

    def decide_turn(self, battle_state):
        try:
            active = battle_state.own_side.active_battler
            foe = battle_state.opponent.active_battler
            if active is not None and foe is not None:
                util = BattleStrategyUtil(battle_state)
                underleveled = active.level + self.UNDERLEVEL_MARGIN <= foe.level
                # Same tests the parent flees on: too little HP, or no usable move.
                cant_continue = not self._pokemon_has_enough_hp(active) or not any(
                    util.move_is_usable(move) for move in active.moves
                )
                if (underleveled or cant_continue) and util.can_switch():
                    finisher = self._capable_finisher(battle_state, util, foe.level)
                    if finisher is not None:
                        return TurnAction.rotate_lead(finisher)
                    # else: no safe finisher — fall through (parent flees / solos).
        except Exception:
            pass
        return super().decide_turn(battle_state)

    def _capable_finisher(self, battle_state, util, foe_level: int):
        """Party index of the strongest HEALTHY team-mate that can SAFELY finish this
        battle — it can damage the foe and has enough HP (both ensured by
        ``get_potential_rotation_targets``) AND out-levels the foe. ``None`` if none
        qualifies (caller then flees / lets the trainee solo)."""
        from modules.pokemon_party import get_party

        party = get_party()
        safe = [
            i
            for i in util.get_potential_rotation_targets(battle_state)
            if party[i].level >= foe_level
        ]
        if not safe:
            return None
        return max(safe, key=lambda i: (party[i].level, party[i].current_hp))


#: Max map transitions (`region_reach` hops — connections AND warps, 1 each) a TRAINING
#: detour may cost. Local hops (a route next door to the town we're in) pass; far-flung
#: treks do not. A sanity FILTER, never a rank — see _training_area_allowed.
_MAX_TRAINING_TRAVEL_LEGS = 4


def _wild_land_max(map_enum) -> "int | None":
    """Strongest LAND wild level on a map, or None if it has no land table / can't be
    read. Used to judge whether a training patch is fodder for the current team."""
    try:
        from modules.map import get_wild_encounters_for_map

        enc = get_wild_encounters_for_map(*map_enum.value)
        if enc is None or not enc.land_encounters:
            return None
        return max(e.max_level for e in enc.land_encounters)
    except Exception:
        return None


def _party_can_rock_smash() -> bool:
    """Can we actually USE Rock Smash in the field? Needs BOTH the move and the badge.

    ‼ DECOMP-VERIFIED (`pret/pokeemerald`, `src/party_menu.c:122`):
        FIELD_MOVE_ROCK_SMASH,  // FLAG_BADGE03_GET
    i.e. field use is gated on the **Dynamo Badge — Wattson's own badge**. This is not the same
    shape as `_party_can_surf`, which needs only the move; Surf's badge is earned long before the
    move is, so the move is the binding constraint there. For Rock Smash the badge binds.

    ‼ WHY THIS EXISTS (`#24-progressiongate`, user-identified 2026-08-08): FIERY_PATH is reachable
    only through ROUTE112, and the Mauville→Route 112 corridor is sealed by a Rock Smash rock at
    ROUTE111 (18,101) (measured, `#24-smashroute`). So every Fiery Path species — Numel, Slugma,
    Machop, Torkoal, Koffing — is unobtainable until BADGE03 is held. Without this gate the
    counter planner offered **Numel @ FIERY_PATH as Wattson's only answer**, which is circular:
    the counter for Wattson sits behind Wattson.

    Fails CLOSED, like every other gate that decides where the bot walks.
    """
    try:
        from modules.memory import get_event_flag
        from modules.pokemon_party import get_party as _gp

        if not get_event_flag("BADGE03_GET"):
            return False
        return any(
            learned is not None and learned.move.name == "Rock Smash"
            for mon in _gp()
            if mon is not None and not mon.is_egg
            for learned in mon.moves
        )
    except Exception:
        return False


def _party_can_surf() -> bool:
    """Does a party mon actually know Surf? (The field-move gate for the water routes —
    the badge alone is not enough, `map_path.can_surf()` requires the move too.)"""
    try:
        from modules.pokemon_party import get_party as _gp

        return any(
            learned is not None and learned.move.name == "Surf"
            for mon in _gp()
            if mon is not None and not mon.is_egg
            for learned in mon.moves
        )
    except Exception:
        return False


def _training_area_allowed(map_enum, tile, prereq) -> bool:
    """Reachability predicate for `training_areas.best_training_area`.

    TWO gates:
    1. **HM prerequisite** (learned the hard way 2026-07-24) — the richest bands (Routes
       115/118/119/121) sit across water; without Surf actually KNOWN by a party mon they
       are unreachable, and a level-fit-only picker happily proposed Route 121 (past
       Lilycove) to a pre-Surf team.
    2. **Reachable FROM WHERE WE STAND** — a static per-area flag is not enough, because a
       single map can be split into disconnected pieces: Route 111's grass sits NORTH of the
       Go-Goggles desert, so it is reachable from Fallarbor but NOT from Mauville or
       Petalburg (probed: no Mauville-side Route 111 grass exists at all). That question is
       answered by `region_reach.is_map_reachable(..., max_hops=_MAX_TRAINING_TRAVEL_LEGS)`
       — built from the ROM's own MapConnections + warps; a cheap graph search, no emulation.

    ‼ WHY `region_reach` AND NOT `calculate_path` (user decision, 2026-07-25 — KI-24, which
    was fixed for counter-candidate selection first and left open here). Both oracles are
    wrong sometimes; their failure modes are NOT symmetric, and that asymmetry IS the whole
    argument:
      * A wrong **NO** from `calculate_path` is INVISIBLE and costs a whole run. It reads the
        Route 118/119/120 dual-elevation bridges as WALLS (it fails even on a same-map walk
        inside Route 119, y=5 -> y=135), so it calls a genuinely-correct training band
        unreachable. Nothing raises, nothing is logged, the option is simply never proposed,
        and the bot quietly grinds the local fodder patch instead — that is what produced the
        ~2,000,000-frame L3-4 grind in front of Norman.
      * A wrong **YES** from `region_reach` costs ONE wasted walk, which navigation then
        fails RECOVERABLY and loudly. Its `KNOWN_GATES` table holds one hand-verified entry
        (the two Dewford sea edges), so any capability gate not yet tabled reads as passable
        — i.e. it errs toward yes, by construction.
    Cheap-and-visible beats invisible-and-fatal, so the training gate now uses the same
    oracle the counter gate already does (see `_counter_area_allowed`).

    ‼ RESIDUAL RISK, stated plainly: `KNOWN_GATES` MUST GROW. Every gate not yet in it is a
    potential wasted trek. Add an entry whenever a relocation is observed walking into a
    wall, and keep the hop budget small — 4 keeps the same-landmass cluster and cuts the
    far-flung (measured hop counts: tools/story-dev/repro_region_reach.py).

    Fails CLOSED on any error: if the oracle cannot answer, we do not relocate.
    """
    if prereq == "surf" and not _party_can_surf():
        return False
    if prereq == "rocksmash" and not _party_can_rock_smash():
        return False
    if prereq not in (None, "surf", "region", "rocksmash"):
        return False  # unknown prerequisite → fail closed
    # ‼ ITEM GATE (2026-08-02). `is_map_reachable` answers at MAP granularity, so it says YES
    # for ROUTE111 — its southern half really is walkable from Mauville — while the training
    # tile (25,55) sits NORTH of the Go-Goggles desert. Measured in batch5: **28 events** of
    # "ROUTE111 (25, 55) is not reachable from here — dropping it", about one wasted
    # cross-Hoenn trek per run, paid to discover a fact the codebase already knew in prose.
    # See `training_areas.AREA_ITEM_PREREQ`. Fails CLOSED, like every other gate here.
    # ‼ OFF BY DEFAULT SINCE 2026-08-04 — THIS GATE COST MORE THAN IT SAVED, AND THE NUMBERS
    # WERE AVAILABLE THE WHOLE TIME. I built it to stop 28 "dropping it as a training option"
    # events per batch. Measured across the batch evidence:
    #
    #   batch          relocations to ROUTE111      Balance->Feather
    #   b3 3875843c              19                       83%
    #   b4 92d220d5              12                       75%
    #   b5 b7345ffd              24                       70%
    #   b8..b12 (gate ON)         0                    52-59%
    #
    # **ROUTE111 (L19-22) is the ONLY training relocation this bot ever performs.** The gate
    # took its success rate from ~43% (24 successes against 32 failures in batch5) to ZERO,
    # the team stopped being levelled for the post-Norman band, and the last funnel rung fell
    # by ~20 points. I counted the wasted treks and never counted the successful ones.
    #
    # ‼ THIS IS THE SECOND TIME I MADE EXACTLY THIS MISTAKE IN A WEEK — the first was
    # `#24-leadpolicy` (c), which removed a Shedinja lead that was winning 39% of Norman
    # fights. 08-MISTAKES already carried the rule ("before removing a behaviour, count how
    # often it WINS") and I applied it to the lead policy and not to this.
    #
    # The failures it targeted are ALREADY handled: `_note_training_unreachable` records a
    # failed area for the rest of the run, so the cost is one trek per run, not per attempt.
    # `POKEBOT_AREA_ITEM_GATE=1` restores it.
    import os as _os

    if _os.environ.get("POKEBOT_AREA_ITEM_GATE", "0").strip() in ("1", "true", "yes"):
        try:
            from modules.items import get_item_bag, get_item_by_name
            from modules.story.training_areas import AREA_ITEM_PREREQ

            needed_item = AREA_ITEM_PREREQ.get(map_enum)
            if needed_item is not None:
                if get_item_bag().quantity_of(get_item_by_name(needed_item)) <= 0:
                    return False
        except Exception:  # noqa: BLE001
            return False
    # "region" carries no extra requirement here — it exists so the conservative
    # allow=None default refuses the area; the live reachability check below is its gate.
    try:
        from modules.map import get_map_data_for_current_position
        from modules.story import region_reach

        here = tuple(get_map_data_for_current_position().map_group_and_number)
        target = tuple(map_enum.value)
        if here == target:
            # Already on the map — nothing to travel, so nothing to prove. Deliberately NOT
            # tile-checked with `calculate_path`: it is unsound even WITHIN one map on the
            # bridge maps, so a "last mile" check here would re-import the exact false
            # negative this predicate just stopped trusting.
            return True
        if bool(region_reach.is_map_reachable(map_enum, max_hops=_MAX_TRAINING_TRAVEL_LEGS)):
            return True
        # ⭐⭐ THE FLY DISJUNCT (`#24-flyladder` Piece 2b, USER RULING 2026-09-19: train each mōn at
        # a level-appropriate ground, FLYING to reach it). Everything above is unchanged; this only
        # ADDS a second way to say yes, for an area the hop budget refuses.
        #
        # ⛔⛔ AND IT IS A DISJUNCT *BECAUSE* OF THE DECISION DOCUMENTED ABOVE, NOT IN SPITE OF IT.
        # The obvious design — "compute the last mile with `calculate_path(landing, tile)`" — was
        # written into the handoff on 2026-09-23 and is WRONG here: this predicate deliberately does
        # not use `calculate_path`, because a wrong NO from it is INVISIBLE and costs a run (it reads
        # the Route 118/119/120 bridges as walls). Gating Fly on a last-mile path would re-import
        # exactly that false negative — and ROUTE118 is one of the ladder's own rungs. ⇒ admit the
        # area on the FLY GUARDS ALONE and let navigation fail loudly if the last mile is bad, which
        # is the same cheap-and-visible trade the hop budget already makes.
        #
        # ‼ THE HOP BUDGET IS NOT WIDENED. `_MAX_TRAINING_TRAVEL_LEGS` still governs WALKING. A
        # flyable area skips it because Fly does not walk the graph at all — measured hop counts put
        # ROUTE121 at 6, ROUTE111/117 at 11 and ROUTE115 at 15 from Ever Grande, so under walking
        # alone a per-trainee ladder returns None for every trainee.
        #
        # ⛔ PAIRED WITH `_goto_training_area`'s FLY LEG (`early_game.py`) — THEY SHIP TOGETHER.
        # A Fly-aware YES here without that leg means the bot ADMITS a 15-hop area and then tries to
        # WALK it, on a bare `train_team` whose only bound is a 500-round guard (KI-28's
        # 19.9M-frame shape). Both callers resolve the anchor through `_training_area_heal_map()`
        # and the guards through `can_fly_to_anchor`, so they cannot disagree about a rung.
        from modules.story.training_areas import can_fly_to_anchor

        return can_fly_to_anchor(_training_area_heal_map().get(map_enum))
    except Exception:
        return False


#: Hop budget for COUNTER-CATCH candidates (`_counter_area_allowed`).
#: ‼ 8, RAISED FROM 4 ON MEASUREMENT (2026-07-26). From the real pre-Norman anchor
#: (`saves/prenorman_fodder_grind.ss1`, Route 102, party avg L27) every Fighting-counter
#: map sits at 5-7 hops — FIERY_PATH 7, JAGGED_PASS 7, GRANITE_CAVE_1F 5 — so a bound of
#: 4 admitted only the NEAREST one and excluded the cheap ones. That is the
#: encounter-rate error again: a proximity proxy overriding measured cost.
#: The arithmetic: reaching FIERY_PATH costs ~3 hops more walking than GRANITE_CAVE, and
#: even at a generous ~5,000 frames per map crossing that is ~15,000 frames — against a
#: **174,000-frame** difference in training cost (Makuhita 363,982 vs Machop 190,589).
#: The filter was off by an order of magnitude against its own purpose.
#: WHY 8 AND NOT MORE, measured from the same anchor: 8 admits FIERY_PATH/JAGGED_PASS (7)
#: and MT_PYRE (8) while still excluding SAFARI_ZONE (10-11) — a paid, step-limited
#: minigame area the bot cannot farm — and PACIFIDLOG (10 from ROUTE120), which is what
#: the original bound existed to cut. Maps admitted from this anchor: 4 -> 52, 6 -> 123,
#: 8 -> 175, 10 -> 226.
#: Safe to loosen only because two other guards now exist: candidates are ranked by
#: measured COST (so a far map must also be cheap to win), and `_training_unreachable`
#: bounds a wrong YES to one wasted walk instead of the run.
#: ‼ Travel cost is still NOT in the cost model — no measured frames-per-hop figure
#: exists in this codebase. Add one and fold it in, then this bound can go away.
COUNTER_MAX_HOPS = 8


def _counter_area_allowed(map_enum, tile, prereq) -> bool:
    """`allow=` predicate for `counter_plan.find_counter_candidates`, used ONLY from
    `_boss_plan_is_hopeless`'s counter-catch wiring (KI-23 -> #24-counters).

    Deliberately NOT `_training_area_allowed`: that predicate's same-region test is
    tile-level `calculate_path`, which reads the Route 118/119/120 dual-elevation
    bridges as WALLS and therefore reported Route 118 — the real Winona answer — as
    unreachable (KI-24). `region_reach.is_map_reachable` answers reachability from the
    ROM's own MapConnections + warps instead, which is sound at region scale.

    ‼ `max_hops` RAISED 4 -> 8 (2026-07-26, measured — see `COUNTER_MAX_HOPS`). At 4 the
    filter was excluding the CHEAP counters and admitting an expensive one purely because
    it sat nearer, which is the encounter-rate mistake wearing a different hat.

    The original note, still true about what the bound is FOR:
    a documented sanity FILTER, not a rank: measured hops from
    ROUTE120 are Fortree 1, Route119 2, Lilycove 2, Route118 3, Mossdeep 4,
    Pacifidlog 10 — 4 keeps the same-landmass cluster and cuts the far-flung.
    Hop count must NOT be used to rank; `counter_plan`'s own criteria (type coverage
    -> verified tile -> encounter rate -> level fit) do that (KI-24b). Fails safe:
    any oracle error is treated as unreachable, never lets an exception escape.
    """
    try:
        from modules.story import region_reach

        allowed = bool(region_reach.is_map_reachable(map_enum, max_hops=COUNTER_MAX_HOPS))
        if not allowed:
            # ‼ KI-42. SAY WHY A CANDIDATE WAS DROPPED. Measured 2026-07-31: FIERY_PATH —
            # the Machop that answers Norman, i.e. the ~72%-of-derails item — is EXACTLY 8
            # hops from PETALBURG_CITY against a limit of 8. Zero margin. One extra hop and
            # this predicate starts returning False, `best_huntable()` returns nothing, and
            # the ladder reports the generic "no huntable counter candidate" with no hint
            # that a distance bound is what did it. That is precisely the KI-24 failure
            # shape: a false negative that gives no reason at all, invisible in every log.
            # `why_unreachable` already distinguishes "reachable but N hops away (limit M)"
            # from "no path" and from "needs Surf", so the reason costs one call on a path
            # that has already decided to reject.
            try:
                from modules.console import console

                reason = region_reach.why_unreachable(map_enum, max_hops=COUNTER_MAX_HOPS)
                console.print(f"[dim]counter gate: {getattr(map_enum, 'name', map_enum)} "
                              f"rejected — {reason}[/]")
                from modules import debug_logger

                debug_logger.event(
                    f"counter gate rejected {getattr(map_enum, 'name', map_enum)}: {reason}",
                    category="STORY",
                )
            except Exception:  # noqa: BLE001 - a diagnostic must never change the verdict
                pass
        return allowed
    except Exception:
        return False


def _counter_catch_message(cfg: dict, losses: int, needed: list[str]) -> str:
    """Builds the `BotModeError` message for a hopeless boss plan (KI-23 -> #24-counters):
    the type-only diagnosis PLUS, if the counter-catch planner can name one, a concrete
    catch target (species + map + tile + level band) rather than just a type list.

    Connects the three previously-standalone pieces: `_boss_plan_is_hopeless` (the
    diagnosis) -> `counter_plan.find_counter_candidates` (ranks catch targets) ->
    `region_reach.is_map_reachable` (the reachability oracle, via `_counter_area_allowed`).
    PLANNING/LOGGING ONLY — this does not travel, catch, or train anything.

    Fails SAFE throughout: if the planner or the reachability oracle errors or returns
    nothing, this falls back to the type-only message. A crash here would turn a
    diagnosed stop into an undiagnosed one, which is strictly worse.
    """
    boss_name = cfg.get("name", "this boss")
    ace_desc = "/".join(cfg.get("ace_types", ())) or "its ace type(s)"
    base_msg = (
        f"{boss_name}: {losses} losses with no super-effective answer to "
        f"{ace_desc}. Need one of: {', '.join(needed)}. Grinding levels "
        f"will not fix this."
    )
    try:
        from modules.story import counter_plan

        # ‼ ASK FOR MORE THAN WE SHOW, THEN DEDUPE BY SPECIES. Live, four of Winona's five rows
        # were the same Geodude on four different Magma Hideout floors — one answer occupying 80%
        # of the list while other species never appeared. ⛔ The ladder's `huntable_candidates()`
        # dedupes by `(map, tile)` and does NOT collapse these (the floors are distinct maps); it
        # answers "where would the executor walk?", which is a different question from "what are
        # my options?". Different questions, different keys — so this does not reuse that helper.
        # ⛔ DISPLAY ONLY: this function builds the text of a BotModeError and feeds nothing the
        # ladder chooses. Ranking and huntability are untouched.
        candidates = counter_plan.find_counter_candidates(
            needed, allow=_counter_area_allowed, max_results=12
        )
        _seen_species: set = set()
        _deduped = []
        for _c in candidates or []:
            _name = _c.get("species_name")
            if _name in _seen_species:
                continue
            _seen_species.add(_name)
            _deduped.append(_c)
            if len(_deduped) >= 5:
                break
        candidates = _deduped
        if candidates:
            summary = counter_plan.summarise_candidates(candidates)
            # Full list to the debug log FIRST — it must land even if the raised
            # message ends up truncated somewhere downstream.
            console.print(
                f"[bold cyan]Story: counter-catch candidates for {boss_name} "
                f"({ace_desc}):[/]\n{summary}"
            )
            base_msg += " Nearest reachable counters: " + summary.replace("\n", "; ")
    except Exception as error:
        console.print(
            f"[yellow]Story: counter-catch planner failed ({error}) — "
            f"falling back to the type-only diagnosis.[/]"
        )
    return base_msg


#: Where to heal while training in each area. Training far from the boss's own Poké Center
#: means the heal trips must be LOCAL to the training ground, or the bot walks the region
#: every time HP dips (the cave-heal lesson, 2026-07-22). Unlisted areas fall back to the
#: boss's configured centre.
def _training_area_heal_map() -> dict:
    from modules.map_data import MapRSE, PokemonCenter

    return {
        MapRSE.ROUTE101: PokemonCenter.OldaleTown,
        MapRSE.ROUTE102: PokemonCenter.PetalburgCity,
        MapRSE.ROUTE103: PokemonCenter.OldaleTown,
        MapRSE.ROUTE116: PokemonCenter.RustboroCity,
        MapRSE.ROUTE117: PokemonCenter.VerdanturfTown,
        MapRSE.ROUTE110: PokemonCenter.MauvilleCity,
        # ‼ Fallarbor, NOT Mauville: Route 111's training tile is NORTH of the
        # Go-Goggles desert. Verified 2026-07-24 — Fallarbor is the ONLY Poké Center
        # reachable from that tile.
        MapRSE.ROUTE111: PokemonCenter.FallarborTown,
        MapRSE.ROUTE112: PokemonCenter.LavaridgeTown,
        # FIERY_PATH is a counter-hunting ground (Machop, the Norman answer). Its south
        # door is Route 112 (11,36), so Lavaridge is the natural heal — and it is the same
        # side `_CAVE_EXITS` surfaces the bot on, so the heal trip is a short walk rather
        # than a trek around the mountain.
        MapRSE.FIERY_PATH: PokemonCenter.LavaridgeTown,
        MapRSE.ROUTE113: PokemonCenter.FallarborTown,
        MapRSE.ROUTE114: PokemonCenter.FallarborTown,
        MapRSE.ROUTE115: PokemonCenter.RustboroCity,
        MapRSE.ROUTE118: PokemonCenter.MauvilleCity,
        # ⚠ ROUTE119/121 pairings are UNVALIDATED: both areas are Surf-gated, so no
        # pre-Surf save can path from their tiles to any Poké Center (verified: Route 119
        # (21,109) reaches NONE). Re-verify from a post-Surf checkpoint before trusting
        # these — the repro skips them for exactly this reason.
        MapRSE.ROUTE119: PokemonCenter.FortreeCity,
        MapRSE.ROUTE121: PokemonCenter.LilycoveCity,
        # ⭐ ADDED 2026-09-19 WITH THE `TRAINING_GRASS` PROMOTION, AND IT IS NOT OPTIONAL.
        # Two of this map's three consumers fall back to the BOSS's own heal centre on a miss
        # rather than refusing — `story_mode.py` (the relocation branch) and
        # `counter_hunt.py` both do `.get(map, cfg["heal"])` with no None-guard
        # (`#24-healmapfallback`). ⇒ promoting Victory Road without this row would silently aim
        # a heal across Hoenn. ✅ Ever Grande is the right centre and is MEASURED: a cave-heal
        # drive walked VICTORY_ROAD_1F → EVER_GRANDE_CITY → POKEMON_CENTER_1F and back,
        # restoring HP and PP (`#24-cavehealblind`).
        MapRSE.VICTORY_ROAD_1F: PokemonCenter.EvergrandeCity,
    }


# ======================================================================================================
# `#24-dexhunt` — THE CATCHING FENCE (user directive 2026-09-04, ruled 2026-07-31)
# ======================================================================================================
#: Poké Balls (EXCLUDING the Master Ball) that a DISCRETIONARY dex catch must leave behind.
#:
#: ⛔⛔ THIS IS NOT `resource_blocker()`'s FLOOR AND MUST NOT BE COLLAPSED INTO IT. That floor is 1 —
#: "the last ball is reserved" — and it is the right floor for a MANDATORY catch (an HM learner, a
#: boss counter): those are catches the run cannot proceed without.
#:
#: A dex catch is discretionary, and a boolean floor of 1 is measurably unsafe for it. MEASURED IN
#: CODE 2026-09-10: `counter_hunt.hunt()` checks its balls at `counter_hunt.py:471` BEFORE the
#: journey and only calls `arm()` at `:510` AFTER arriving — with `_navigate_riding_out(..., tries=24)`
#: at `:488` in between, which that function's own comment calls "the LONGEST journey the bot ever
#: makes … 8 map-hops away across several warp chains". So `is_armed()` is FALSE for the whole trek,
#: and a fence gated only on a boolean would happily spend the hunt's balls down to 2 en route. The
#: hunt does not re-check on arrival: it arms, spins its full `HUNT_SPIN_BUDGET_FRAMES` (120,000) and
#: reports "found nothing" while standing on the answer — the exact failure its own comment says the
#: feature already suffered once.
#: ⇒ THE FENCE MUST LEAVE A HUNT'S WORTH OF BALLS BEHIND, NOT A TOKEN.
#:
#: ‼ HOW THE NUMBER WAS CHOSEN, stated honestly because this project does not accept guessed
#: constants dressed as measurements: `HUNT_SPIN_BUDGET_FRAMES`' own comment sizes a hunt at
#: "roughly 12 expected meetings plus catch failures". Balls-per-successful-catch has NEVER been
#: measured here — nothing logs it — so 10 is a JUDGEMENT sized to that budget, deliberately below
#: 12 (a hunt that meets its target does not need a ball for every meeting) and far above 1.
#: ⇒ RE-DERIVE IT once `balls=` heartbeat telemetry (shipped 2026-09-10) has a batch behind it.
DEX_CATCH_BALL_RESERVE = 10

#: Attempts per species per run before the fence gives up on it.
#: ⛔ ATTEMPTS, NOT SUCCESSES. A catch that fails (break-out, the wild flees, our lead faints) leaves
#: the species un-owned, so the predicate that admitted it is TRUE again on the very next encounter —
#: and nothing else in this codebase remembers. Without a cap the only terminating condition is
#: draining the ball pool, which is precisely the resource the mandatory hunts share. 2 is one retry.
DEX_CATCH_MAX_ATTEMPTS = 2

#: USER RULING 20 Phase 0 (2026-09-26): a post-gym-1 Pokédex catch is not STARTED when a full-HP throw with our best
#: ball is expected to take more than this many balls. ⚠ A JUDGEMENT, not a measurement — sized so the 30-ball Rustboro
#: purchase covers ~3 hard catches, and logged per refusal so a batch can re-derive it. MEASURED motivation: one Absol
#: (catch rate 30) took 23 balls; this formula predicts ~25 for it.
DEX_CATCH_MAX_EXPECTED_THROWS = 10

#: `sBallCatchBonuses` (`src/battle_script_commands.c:841`): the multiplier each ordinary ball applies, x10.
_BALL_BONUS_X10 = {"Ultra Ball": 20, "Great Ball": 15, "Poké Ball": 10, "Safari Ball": 15}


def dex_fence_log_line(logged: set, dex, name: str, catch: bool, reason: str) -> "str | None":
    """PURE (mutates only `logged`). The DEXFENCE line for this verdict, or None: each (species, reason) once per run;
    "already owned" and trainer battles are never logged (a route full of owned mons must not spam the log)."""
    if (dex, reason) in logged:
        return None
    logged.add((dex, reason))
    if reason.endswith("already owned") or reason == "trainer battle":
        return None
    return f"{'CATCH' if catch else 'skip'} #{dex} {name} — {reason}"


def _expected_throws_for(species, bag, allowed=None) -> "float | None":
    """ADAPTER for `dex_catch_expected_throws`: the species' catch rate and the best ball the THROWER may use — held,
    never the Master Ball, and in the user's `catch_balls.yml` allowlist (`modules.catch_balls.allowed_ball_names()`,
    exactly the filter `CatchStrategy._get_best_poke_ball` applies; `allowed` is injectable for the gate). A special
    ball counts as a Poké Ball (its bonus is conditional — conservative). None when unreadable or ball-less — the fence
    then ignores it (the ball reserve check already refuses an empty bag).
    ⛔ The first version skipped the allowlist: a held-but-disallowed Ultra Ball made a rate-45 catch read 8.1 throws
    (admitted) while the thrower, barred from it, would throw Poké Balls at 16 (adversarial review, 2026-09-26)."""
    try:
        if allowed is None:
            try:
                from modules.catch_balls import allowed_ball_names

                allowed = allowed_ball_names()
            except Exception:  # noqa: BLE001 - the thrower's own fallback: every ball except the Master Ball
                allowed = None
        best = max((_BALL_BONUS_X10.get(slot.item.name, 10) for slot in bag.poke_balls
                    if slot.quantity > 0 and slot.item.name != "Master Ball"
                    and (allowed is None or slot.item.name in allowed)), default=None)
        if best is None or species is None:
            return None
        return dex_catch_expected_throws(int(species.catch_rate), best)
    except Exception:  # noqa: BLE001 - unknown ⇒ None ⇒ the fence ignores it (never a silent refusal)
        return None


def dex_catch_expected_throws(catch_rate: int, ball_bonus_x10: int) -> float:
    """PURE. Expected balls to catch a FULL-HP, status-free target — Gen 3's own arithmetic, integer steps included
    (`Cmd_handleballthrow`, `src/battle_script_commands.c`): `odds = (rate * bonus / 10) * (3*maxHP - 2*HP) /
    (3*maxHP)` (at full HP: `/ 3`); `odds > 254` ⇒ certain; else `b = 1048560 / Sqrt(Sqrt(16711680 / odds))` and all
    four shake checks `Random() < b` must pass, so p = (b / 65536)^4 and the expectation is 1 / p.
    ⚠ An UPPER bound for this bot: the catch strategy never damages, but may add a status (x1.5 / x2), which only
    lowers it. `odds == 0` (a rate so low the integer steps reach 0) returns infinity — never caught."""
    from math import isqrt

    odds = (catch_rate * ball_bonus_x10 // 10) // 3
    if odds > 254:
        return 1.0
    if odds <= 0:
        return float("inf")
    b = 1048560 // isqrt(isqrt(16711680 // odds))
    p = min(1.0, (b / 65536) ** 4)
    return 1.0 / p if p > 0 else float("inf")

#: Gen 3's party size. Named rather than inlined as `6` because this file already carries FOUR
#: separate hand-written `< 6` party tests and the fence's whole correctness rests on meaning the
#: same thing they do.
PARTY_CAPACITY = 6

#: 14 boxes x 30. Past this the game shows `gText_BoxFull`, does NOT consume the ball, and returns to
#: the bag menu — a state no caller here inspects, so the strategy would simply throw again.
#: ⛔ Unreachable from this feature alone (420 slots vs ~200 species) — it is guarded anyway because
#: the cost is one comparison and the failure mode is an in-battle loop that the frame budget cannot
#: see (KI-36: battles hold control, so the budget reports `frame-cap=0`).
PC_STORAGE_SLOTS = 14 * 30


def decide_maintenance(
    *,
    battler_levels: "dict[int, int]",
    boss_target: int,
    catchup_gap: int,
    ground_for: "callable",
    wild_max_for: "callable",
    estimate_for: "callable",
    heal_for: "callable",
    budget: int,
) -> "tuple[int | None, str]":
    """PURE. Which battler should be maintained before this fight, and to what? `(slot, reason)`.

    ⛔⛔ WHY THIS IS PURE AND NOT AN `if` CHAIN INSIDE THE GENERATOR. The same argument that made
    `decide_dex_catch` pure: the decision is the thing worth gating, and a decision entangled with
    `yield from` needs a ROM, a save state and ~100k frames to exercise ONE branch. Extracted, all
    of its branches are a table in `probe_maintenance_decision.py` that runs in milliseconds.
    ‼ The callables are injected for the same reason - `best_training_grass`,
    `estimate_frames_to_level` and the heal map are all real here, but a test can hand this
    function a two-line stub and ask what it would DO.

    Returns `(None, reason)` when nothing should happen, or `(slot, reason)` when `slot` should be
    rotated to lead and trained to `boss_target - catchup_gap`.

    THE RULES, in order, each answering a failure this project has already paid for:
      1. No battlers -> nothing. (An empty battler set once certified a broken run READY; gate #48.)
      2. Nobody below `catchup` -> nothing. ⛔ The predicate is the EXCLUSION's own quantity
         (`boss_target - catchup_gap`), not a gap against the party max: that is the number
         `_prepare_for_fight` actually decides on, so maintaining to it is exactly sufficient.
      3. Weakest excluded mon first. It is the one that will trigger §Ch23's refusal.
      4. No ground for its level -> SKIP with a reason (honest stop, never a guess).
      5. Unknown or over-budget estimate -> SKIP. ⛔ `estimate_frames_to_level` documents that a
         `None` means UNKNOWN and must never be read as cheap.
      6. No heal centre for that ground -> SKIP. Training somewhere unhealable is how an errand
         becomes a whiteout.
    """
    if not battler_levels:
        return None, "no battlers"

    catchup = boss_target - catchup_gap
    excluded = {slot: lvl for slot, lvl in battler_levels.items() if lvl < catchup}
    if not excluded:
        return None, f"every battler is already at or above the L{catchup} prep floor"

    slot = min(excluded, key=lambda s: (excluded[s], s))
    level = excluded[slot]

    ground = ground_for(level)
    if ground is None:
        return None, f"slot {slot} is L{level} (needs L{catchup}) but no ground serves that level"

    grass_map = ground[0]
    wild_level = wild_max_for(grass_map)
    est = estimate_for(slot, catchup, wild_level)
    if est is None:
        return None, f"slot {slot} L{level}->L{catchup}: cost UNKNOWN — refusing (fail safe)"
    if est > budget:
        return None, f"slot {slot} L{level}->L{catchup}: est {est} > budget {budget} — refusing"

    if heal_for(grass_map) is None:
        return None, f"slot {slot}: no heal centre mapped for {grass_map} — refusing"

    return slot, f"maintain slot {slot} L{level}->L{catchup} (est {est} <= budget {budget})"


def decide_dex_catch(
    *,
    is_wild: bool,
    is_shiny: bool,
    has_pokedex: bool,
    pre_badge1: bool,
    party_slots_used: int,
    battler_count: int,
    party_target: int,
    resource_block: "str | None",
    spare_balls: int,
    hunt_armed: bool,
    training: bool,
    boxed_count: int,
    party_healthy: bool,
    species_dex: "int | None",
    owned_dex: "frozenset[int]",
    party_dex: "frozenset[int]",
    attempts: int,
    expected_throws: "float | None" = None,
) -> "tuple[bool, str]":
    """PURE. Should this wild encounter become a catch attempt? Returns `(catch, reason)`.

    ⛔⛔ WHY THIS IS A PURE FUNCTION AND NOT AN `if` CHAIN INSIDE THE ADAPTER. `04-HANDOFF.md` says of
    this item: *"NO CHEAP FIXTURE TEST EXISTS — a Tier 2 auditor tried and could not compute a
    discriminator."* That is true of the fence's EFFICACY and stays true: only an hours-long batch
    can say whether catching raises the dex. It is NOT true of the fence's CORRECTNESS. Every input
    below is a plain value, so `probe_dex_catch_fence.py` can interrogate all sixteen conditions in
    milliseconds — which is the same move that made `rank_replacement` testable after
    `choose_new_lead_after_faint` had shipped THREE index-space bugs that each needed a ROM, a live
    battle and a staged faint to see.

    ‼ IT RETURNS A REASON, NOT A BARE BOOL, AND THAT IS LOAD-BEARING. The 2026-07-31 ruling requires
    that a skip SAY SO. The old `_should_catch` returned `bool` from inside a blanket
    `except Exception: return False`, so "the fence declined" and "the fence crashed" were the same
    observation — which is exactly how the draft spec's invented `counter_hunt.hunt_active()` would
    have failed: `AttributeError`, swallowed, feature never fires, and the A/B reads "no difference"
    as a REFUTATION of a feature that never ran.

    ⛔⛔ THREE PARTY FIGURES, DELIBERATELY, AND THEY ARE NOT INTERCHANGEABLE. Each answers a DIFFERENT
    question, and an egg is counted by one and not the others:
      * `party_slots_used` — RAW slots, EGGS INCLUDED. Answers *"will the game store this catch in
        the PC?"*, and the game's own answer counts an egg as an occupied slot. Same convention as
        `ensure_hm_learner` (`early_game.py:4505`) and the counter branch (`:2327`).
      * `battler_count` — EGG-FILTERED. Answers *"how big is the TEAM?"* for the pre-gym-1 target,
        which is a target for things that can FIGHT. An egg cannot.
      * `party_dex` — EGG-FILTERED. Answers *"do we already have this species?"*.
    ‼ THE FIRST DRAFT USED ONE COUNT FOR ALL THREE AND IT SILENTLY CHANGED THE ORDINARY CASE. Feeding
    the RAW count to the pre-gym-1 target made *3 battlers + 1 egg* read as a full team of 4 and
    refuse a catch the old code ALLOWED — a behaviour change in the one path this work promised not
    to touch, in a game where a Day-Care egg rides in a party slot. Caught by A/B-ing the new
    predicate against the old logic (`probe_dex_catch_fence.py` C19/C20 are that A/B, kept as a
    permanent regression test), NOT by reading it — the two counts differ only when an egg is aboard,
    which no amount of re-reading makes obvious.
    ⇒ And the mirror error is just as real: using the EGG-FILTERED count for FULLNESS would fire the
    fence at five mons + an egg, where the catch takes the sixth PARTY slot and consumes the
    HM/counter runway `#24-partycap` MEASURED as worth 36 points of finish rate.
    """
    # ---- gates that are true of any catch, at any stage -------------------------------------------
    if not is_wild:
        return False, "trainer battle"
    if is_shiny:
        # Pre-empted upstream by `StoryShinyCatchStrategy` (`on_battle_started`, the FIRST branch).
        # Returning False here is not a refusal to catch shinies — it is refusing to catch them TWICE.
        return False, "shiny — already handled by the shiny branch"
    if not has_pokedex:
        return False, "no Pokédex yet"
    if species_dex is None:
        return False, "species could not be read"
    if species_dex in owned_dex:
        return False, f"#{species_dex} already owned"
    if species_dex in party_dex:
        return False, f"#{species_dex} already in the party"
    # ‼ THE PINNED RESOURCE PREDICATE (2026-07-31 ruling: "reuse it rather than writing a second one
    # that can drift"). `counter_hunt.resource_blocker()` is the authority on whether ANY catch can be
    # attempted; the caller passes its verdict straight through, so this function cannot drift from it.
    if resource_block:
        return False, resource_block

    # ---- PRE-GYM-1: organic team building (user directive 2026-07-21) — UNCHANGED ------------------
    # ⛔ This branch must stay behaviourally identical. It is the ordinary case, it runs in every run,
    # and `#24-partycap` measured that disturbing the early party costs 36 points.
    if pre_badge1:
        # ⛔ `battler_count`, NOT `party_slots_used` — the target counts things that can FIGHT, and
        # this is the ordinary case that `#24-partycap` costs 36 points to disturb. See the docstring.
        if battler_count < party_target:
            return True, "pre-gym-1 team building (joins the party)"
        return False, f"pre-gym-1 team already at its target of {party_target}"

    # ---- POST-GYM-1: THE DEX FENCE ----------------------------------------------------------------
    if party_slots_used < PARTY_CAPACITY:
        # THE HEART OF THE FENCE. Below a full party the catch would take a PARTY slot, and the empty
        # slots are the runway HM and counter catches land on — `#24-partycap`, MEASURED: 52.0% ->
        # 15.8% finish rate, the ENTIRE loss on one badge rung, 10 of 16 non-finishes being
        # "No party mon can learn Surf and the party is full". At a FULL party there is no runway left
        # to consume, so `Cmd_givecaughtmon -> GiveMonToPlayer -> CopyMonToPC` stores it instead.
        return False, f"party is {party_slots_used}/{PARTY_CAPACITY} — a catch would consume the HM/counter runway"
    if hunt_armed:
        # ⛔ A catch-on-sight hunt is running. `counter_hunt.catch_confirmed`'s BOX path
        # (`counter_hunt.py:363-365`) is SPECIES-BLIND — any new box PID ends the spin. The hunt's
        # VERDICT is type-aware (`party_counter_slot`/`box_counter_pid` at `:546`/`:559`), so an
        # off-type dex catch is NOT mis-registered as the counter; it is worse in a quieter way: the
        # spin ENDS EARLY, the verdict finds nothing, and the ladder loses a 120,000-frame hunt and a
        # ball having caught the wrong thing.
        return False, "a catch-on-sight hunt is armed"
    if training:
        # A catch earns ZERO exp, and `train_team` exists only to gain exp. Worse, `#24-ch23training`
        # is the top run-ender (16 of 49 = 32.7%) precisely because a grind exceeds its frame ceiling.
        # ‼ And the no-progress watchdog counts OVERWORLD frames with unchanged party EXP
        # (`early_game.py:202-218`), resetting ONLY on an EXP change — so catches lengthen the
        # un-reset window without ever moving it.
        return False, "a training grind is in progress"
    if spare_balls <= DEX_CATCH_BALL_RESERVE:
        return False, f"only {spare_balls} spare balls — below the dex reserve of {DEX_CATCH_BALL_RESERVE}"
    if boxed_count >= PC_STORAGE_SLOTS:
        return False, "PC storage is full"
    if not party_healthy:
        # ⛔ A CATCH BATTLE NEVER FIGHTS BACK. `CatchStrategy.decide_turn` (`catch.py:41-62`) only ever
        # throws a ball or applies a status move, and `should_flee_after_faint` is unconditionally
        # False (`:38-39`) — so the wild attacks freely and the bot does not leave until the balls run
        # out. Pre-gym-1 that was bounded by L3-6 wilds; post-badge it runs against L30-45 ones.
        # Entering only from full strength is the part of that exposure a PURE predicate can bound.
        # ⚠ It does NOT bound mid-battle degradation — see `#24-dexcatch-battlebail`.
        return False, "party is not at full strength"
    if attempts >= DEX_CATCH_MAX_ATTEMPTS:
        return False, f"already attempted #{species_dex} {attempts}x this run"
    # USER RULING 20 Phase 0: do not START a catch the balls cannot afford. POST-gym-1 only — the pre-gym-1 branch
    # above returned already and stays byte-identical (`#24-partycap`). None = unknown ⇒ no effect (never a silent
    # refusal on a read failure). The skip-the-fix arm `POKEBOT_DEXCATCH_FAULT_NORATE` restores the old behaviour.
    import os as _os_rate  # ⛔ LOCAL: this module has no module-level `os`; a bare `os` here was a NameError that
    #                         the adapter's `except` would have filed as "fence errored" (caught before it shipped).

    if (expected_throws is not None and expected_throws > DEX_CATCH_MAX_EXPECTED_THROWS
            and _os_rate.environ.get("POKEBOT_DEXCATCH_FAULT_NORATE") != "1"):
        return False, (f"#{species_dex}: ~{expected_throws:.0f} expected throws at full HP with our best ball — above "
                       f"{DEX_CATCH_MAX_EXPECTED_THROWS}")
    return True, f"dex catch #{species_dex} (goes to the PC box)"


class StoryMode(BotMode):
    #: OPT IN to the battle-handler fault channel (#24-movelearn-recovery, 2026-07-25).
    #: A sub-handler that gives up (e.g. an unanswerable move-learn offer) records the
    #: fault via `modules.battle_fault` instead of raising across the controller stack
    #: into `main_loop` — which would drop the run to Manual, outside our recovery. We
    #: re-raise it inside run()'s try below, so it costs a DERAIL, not the whole run.
    #: This attribute is the promise that we consume it; nothing else may set it
    #: without also calling `take_pending_fault()` on every frame it holds control.
    handles_battle_faults = True

    #: Pre-gym training only readies a battler that's already within this many levels
    #: of the target band; fresh catches further below are left to level organically
    #: rather than grinding them up via half-XP swap-training (user 2026-07-21).
    TRAIN_CATCHUP_GAP = 6

    #: A boss's LOCAL grass counts as FODDER — worth relocating away from, or skipping
    #: entirely — once its strongest wild is this far below the team's best mon.
    #: ‼ Deliberately MORE conservative (12) than the reactive boss-training check (8):
    #: this fires PROACTIVELY, before any loss, so it must not disturb prep that already
    #: works. At 12 it stays silent for Roxanne (R116 L8 vs ~L17) and Wattson (R117 L14
    #: vs ~L24) — both validated across many runs — and fires for the pathological case
    #: it exists for: NORMAN, whose local patch is Route 102 at L4 against a L27-31 team
    #: (~25 xp a kill, i.e. never). User-reported 2026-07-24.
    FODDER_LEVEL_GAP = 12

    #: Frame budget for a SINGLE targeted grind decision (evo-lookahead or sweeper top-up) —
    #: ~3 minutes of emulator time, derived from the MEASURED FRAMES_PER_WILD_BATTLE (1433,
    #: see modules/story/training_areas.py) — roughly 174 wild battles' worth of budget.
    #: Both decisions used to be budgeted purely in LEVELS, but frames-per-level varies
    #: enormously with where you grind: a fresh run's evo-lookahead sent a L33 Combusken to
    #: Route 102's L3-5 wilds for 3 levels (~430,000 frames, measured) and helped blow the
    #: run's overall frame cap one level short. This constant is what lets that plan be
    #: REJECTED up front instead of committed to blind (punch-list #24).
    MAX_PREP_TRAINING_FRAMES = 250_000

    #: How many times to (re)train + attempt the Rustboro rival before giving up and handing
    #: to manual — bounds the whiteout→retrain loop so an underleveled/bad-matchup team can't
    #: spin forever (each attempt escalates the training band via `_prepare_for_fight`).
    RIVAL_MAX_ATTEMPTS = 3

    #: KI-23 (Winona): losses to the SAME boss before `_boss_plan_is_hopeless` will even
    #: consider calling the plan unwinnable. The observed failure ran to 41 losses (198
    #: attempts) grinding levels a Grass/Normal/Dark/Bug-Flying team could never spend on
    #: Flying; 6 is enough to separate bad luck from a wrong plan while costing far less
    #: than 41 whiteout cycles before we say so.
    PLATEAU_LOSS_THRESHOLD = 6
    #: `#24-whiteoutloop` RUNAWAY BACKSTOP (2026-08-07). Losses at ONE map after which a flat
    #: KO series overrides the type-chart "we have a credible answer" prediction entirely.
    #: Deliberately far above PLATEAU_LOSS_THRESHOLD: this is not the primary detector, it is
    #: the thing that stops a 32-loss run. Paired with a TWO-window (12-attempt) flatness test
    #: so a recovering run — KI-26's run that lost 13 times and then reached Fortree — cannot
    #: trip it. ‼ Never re-key this on attempt count alone; the KO series is the discriminator.
    HARD_PLATEAU_LOSS_THRESHOLD = 12

    #: Defeats on ONE map (this run) after which wild battles there are fled rather than
    #: fought — see the SURVIVAL MODE block in `on_battle_started`. 3, not 6: the boss
    #: threshold can afford patience because a lost boss attempt still banks EXP (Gen 3
    #: keeps mid-battle EXP through a whiteout), whereas a travel wipe banks almost
    #: nothing and costs the whole walk back from the respawn Poké Center. Measured
    #: worst case before this existed: **25 whiteouts on ROUTE110 in a single run**.
    SURVIVAL_WHITEOUT_THRESHOLD = 3

    #: Minimum EFFECTIVE power (base power x type effectiveness x STAB) for a move to
    #: count as a real answer to a boss's ace type in `_boss_plan_is_hopeless`.
    #: ‼ WITHOUT THIS THE DETECTOR IS POWER-BLIND AND SILENTLY DISABLES ITSELF ON
    #: NORMAN (measured, night5 run3, 2026-07-25). Norman's team is all NORMAL, and the
    #: only type super-effective against Normal is FIGHTING — so the party's sole
    #: "answer" was **Rock Smash**, the 20-base-power HM the bot is REQUIRED to carry to
    #: progress at all. 20 x 2.0 x 1.0 = 40: super-effective on paper, useless against a
    #: L31 Slaking. The old `eff >= 2.0` test accepted it, declared the plan not
    #: hopeless, and let the run make **27 losing attempts over 508,000 frames** with
    #: KOs flat at 1-2 of 4 the entire time. The boss most likely to plateau was the one
    #: the guard could never fire on.
    #: ‼ RAISED 60 -> 75 on measured evidence (batch 20260726-052205 run05). 60 was
    #: calibrated against Rock Smash on a NON-Fighting carrier (20 x 2.0 x 1.0 = 40) and
    #: missed the STAB case: **Combusken is Fire/FIGHTING**, so its Rock Smash scores
    #: 20 x 2.0 x 1.5 = **exactly 60** and passed on the boundary. The guard stayed
    #: silent and that run took **21 Norman losses** — the same failure the threshold
    #: exists to prevent, arriving through STAB instead of raw power.
    #: The two measured points bracket it: 60 (Combusken + Rock Smash) demonstrably does
    #: NOT beat Norman; 90 (Combusken + Double Kick) demonstrably does. 75 sits between
    #: them and still keeps ordinary answers — a plain 40-power super-effective move (80),
    #: Surf (285), Ice Beam into Altaria (380). ⛔ NOT Thunderbolt — Electric is NEUTRAL vs her ace.
    #: ‼ Do NOT "fix" this by excluding HM moves categorically: Surf/Strength/Waterfall
    #: are real attacking moves and are often the bot's best answer. Only Rock Smash and
    #: Cut are weak enough to be the problem, and the power floor already handles them.
    CREDIBLE_ANSWER_POWER = 75

    #: How many distinct counter DESTINATIONS one ladder invocation may try before giving
    #: up. Each rejected destination costs only a fail-fast navigation (~255 frames
    #: measured), so a small fallback list is nearly free — and it is necessary: driven
    #: navigation on 2026-07-30 showed the TOP huntable destination unreachable for two of
    #: the three measured bosses. Bounded because the ladder must terminate; the expensive
    #: failure (arrived, caught nothing) deliberately does NOT consume one of these.
    COUNTER_HUNT_MAX_DESTINATIONS = 3

    @staticmethod
    def name() -> str:
        return "Story"

    @staticmethod
    def is_selectable() -> bool:
        # Story mode can start from the title screen (fresh game) or in-game,
        # so it is always offered; run() sorts out which path applies.
        return True

    @staticmethod
    def is_selectable_from_title_screen() -> bool:
        # Unlike stock modes, Story Mode is MEANT to start at the title/main
        # menu — that's where it runs the New Game intro.
        return True

    def __init__(self):
        super().__init__()
        self.reset_per_run_state()

    def grant_ch23_training_allowance(self, frames: int) -> None:
        """§Ch23's chunked training leg announces its purse, so a batch run's frame cap cannot pre-empt
        the leg's own designed backstop (`#24-ch23training`, 2026-09-26). Idempotent (a retried
        attempt re-grants the same purse, never a second one). ⚠ Reset per RUN in
        `reset_per_run_state`, never here — the endless loop reuses this object across runs."""
        self._ch23_training_allowance = max(int(getattr(self, "_ch23_training_allowance", 0) or 0),
                                            int(frames))

    def mark_ch24_owns_run(self) -> None:
        """Latch: §Ch24 has started, so §Ch23 must not be re-entered for the rest of this run.

        ⛔⛔ WHY A LATCH IS NEEDED AT ALL — `ch23_chapter_done()` IS A POSITION TEST, AND §Ch24
        BREAKS IT BY DESIGN. That predicate is FLAG ∧ POSITION ∧ BAG
        (`modules/story/victory_road.py:3315-3322`): it requires `_on_map(EVER_GRANDE)` **and** that
        we are NOT on any Victory Road floor. §Ch24's training leg flies to ROUTE117 (position
        conjunct broken within seconds) and later grinds INSIDE Victory Road (broken again, by the
        other half of the same line). The bag conjunct breaks later still, when the League basket is
        spent.
        ⇒ without this latch, EVERY run after training starts would find `ch23_chapter_done()` False,
        re-run `do_victory_road_chapter()`, and `_guard` would then STOP the bot with a diagnostic.
        ‼ `victory_road.py:3308-3313` predicted exactly this and called it a forward dependency:
        *"when §Ch24 is built it MUST set its own progress marker so §Ch23 is not re-entered."*

        ⛔ WHY NOT THE `#24-markerwinstate` MARKER: that one is the GAUNTLET's, and it is a POSITION
        test too ("standing on a sealed League map") plus an `IS_CHAMPION` disjunct. Both read False
        on a training route. §Ch24 needs this EARLIER, third term — they are not substitutes.

        ⛔ WHY AN IN-PROCESS LATCH AND NOT AN EVENT FLAG: there is no Gen-3 flag meaning "the bot
        decided to start training", and inventing a use for an unrelated flag is how `KI-90` was
        filed. The lifetime we actually need is THE RUN, which is exactly this object's lifetime
        between resets.
        """
        self._ch24_owns_run = True

    def reset_per_run_state(self) -> None:
        """Clear every counter whose meaning is scoped to ONE playthrough.

        ‼ WHY THIS IS A METHOD AND NOT JUST `__init__` (real failure, user's x4 bundle
        `20260726-231412`). All of this state used to be assigned directly in `__init__`,
        under a comment that claimed "Instance state, not module state, so ENDLESS RESET's
        next run starts with a clean slate." **That was false.**
        `StoryEndlessResetMode.run()` loops `yield from super().run()` on the SAME mode
        object, so `__init__` runs once per BATCH — the counters accumulated across every
        run of an overnight batch. Two measured consequences:

          * `_rival_attempts` (cap 3) reached its cap after 3 runs, so **run 4 onward died
            at the Rustboro rival without ever fighting it** — P1 run 8's debug log contains
            ZERO `BattleOutcome.Lost` yet the run ended "couldn't beat the Rustboro rival in
            3 tries". It killed 16 of 20 P1 runs, 6 of 9 P2 runs, 5 of 8 P3 runs.
          * `_defeat_counts` carried each run's losses into the next, so the "give up on this
            boss" threshold tripped on borrowed losses: MT_CHIMNEY went `#7`(run 1) → `#8`
            (run 2), FORTREE_GYM `#8`(run 1) → `#9`(run 3), and P4 run 2 derailed as
            "6 losses" to Wattson after only THREE real losses that run.

        PREVENTION RULE: per-run state goes in here, never in `__init__`, and the endless
        loop calls this at the top of every run. A comment asserting a lifetime is not a
        mechanism that enforces it.
        """
        # DEFEAT RECOVERY (user directive 2026-07-21). Consecutive losses are counted
        # per LOCATION (map) so repeated faints at the same obstacle mean a power/level
        # problem → trigger a retrain. These survive whiteout restarts within a run,
        # because run() loops in place (it does NOT bounce through Manual).
        # Training grounds proven unreachable FROM a given standing map, this run
        # (#24-regionreach, 2026-07-25). Keyed (here_map, target_map, tile) because
        # reachability is directional and positional: Route 111's grass is genuinely
        # reachable from Fallarbor and genuinely not from Mauville, so a flat blacklist
        # would throw away a good area for the rest of the run.
        self._training_unreachable: set = set()
        self._defeat_counts: dict = {}
        self._loss_ko_history: dict = {}  # map key -> [(seq, opponent KOs) per lost attempt]
        #: USER RULING 19 (2026-09-26): map key -> [(seq, boss name, {foe species: our faints})] per lost LEADER battle —
        #: WHICH foe beats us, by identity, weighted by our faints (`battle_action_selection.TURN_FOE["log"]`). Only a
        #: battle whose enemy party IS a leader's roster is filed (`_boss_battle`, set at battle start): the gym's
        #: trainers share the leader's species. The gym-TM teach names its wall from this.
        self._loss_foe_history: dict = {}
        #: The boss whose roster is the CURRENT battle's enemy party (`gym_tm_teach.boss_for_enemy_party`), or None.
        self._boss_battle = None
        self._loss_seq: int = 0
        #: `#26-manualderails`: boss keys whose ONE "second wind" (below) has been consumed.
        #: Per-instance and per-run BY DESIGN — a fresh instance (the user's manual flip) and the
        #: endless loop's per-run reset both re-arm it, exactly like `_counter_hunts`.
        self._second_winds: set = set()
        #: USER RULING 19 (2026-09-26): (boss name, TM name) pairs the gym-TM teach has already TRIED this run.
        #: Written BEFORE the act (a TM is single-use), per-run so the next run of an endless batch re-arms it.
        self._gym_tm_taught: set = set()
        #: (pid, move) -> {"boss", "wall", "species", "used"} for every move the teach delivered this run. Excluded from
        #: `_boss_plan_is_hopeless`'s credible-answer scan (a teach must not switch off the counter ladder / honest stop)
        #: and protected from make-room deposits (`pc_trip`). `used` is set when the log shows it chosen vs its wall.
        self._gym_tm_taught_moves: dict = {}
        # ⛔ HERE, NOT IN `__init__` — the whole reason this method exists. `StoryEndlessResetMode.run()`
        # loops on the SAME mode object, so `__init__` runs once per BATCH. A latch set in
        # `__init__` would make run 2 of an overnight batch believe §Ch24 had already
        # started and SKIP §Ch23 entirely — the same shape as the `_rival_attempts` bug
        # documented below, which killed 16 of 20 P1 runs.
        self._ch24_owns_run = False
        #: `#24-ch23training`: extra per-run frames granted by §Ch23's chunked training leg (its own
        #: purse). Read ONLY by `StoryEndlessResetMode._frame_cap_for_this_run`; 0 until granted.
        self._ch23_training_allowance = 0
        self._whiteout_pending = False
        self._last_defeat_key = None
        self._derails = 0  # consecutive non-whiteout derails (self-correct before Manual)
        self._last_derail_sig = None  # progress fingerprint at the last derail (see run())
        # Boss/rival attempt caps. These are PER-RUN budgets: a thin team that cannot win
        # stops cleanly instead of looping forever, but the NEXT run must start fresh.
        self._rival_attempts = 0
        # Set only by the genuine end-of-built-content return, so the endless loop can tell
        # a real completion from a give-up — both hand to Manual and return normally.
        self._reached_end_of_content = False
        # Nudge debounce for the Ki15 wedge (see run()); positional, so per-run.
        self._ki15_nudge_stable = 0
        self._ki15_nudge_pos = None
        # Organic team-building (user directive 2026-07-21): catch NEW species while
        # travelling to Gym 1 until the party has this many members (starter + helpers).
        # ‼ 4 IS LOAD-BEARING — DO NOT RAISE IT AGAIN WITHOUT READING THIS.
        # Raised 4 -> 6 on 2026-08-05 (`#24-partycap`) and REVERTED the same day by batch
        # `20260805-122057` (be104e9c): finish rate 52.0% -> 15.8%, and the badge funnel put
        # the entire loss on ONE rung — Balance->Feather 76% -> 21% (z=3.06). Every earlier
        # rung was flat, so a deeper team is genuinely FREE through five badges.
        #
        # The cause is not team strength, it is **HM COVERAGE**. Filling the party with
        # early-route wilds (Skitty/Mightyena/Loudred/Ninjask/Taillow) leaves no Surf learner
        # and no slot to catch one, so the run derails at the Surf gate: "No party mon can
        # learn Surf and the party is full" — 10 of 16 non-finishes, and ZERO occurrences in
        # any of the 14 preceding batches.
        #
        # ‼ The empty slots were never waste — they are the RUNWAY the HM/counter catches
        # land on. Measured: at cap 4 the team still reaches a mean of 5.85 by the Feather
        # Badge. It fills up either way; letting wilds take the seats first is what breaks it.
        self._catch_team_target = 4
        # `#24-dexhunt`: national-dex number -> ATTEMPTS this run (not successes).
        # ⛔ ATTEMPTS IS THE ONLY COUNT THAT TERMINATES. A failed catch leaves the species un-owned,
        # so the predicate that admitted it is TRUE again on the very next encounter and nothing else
        # in this codebase remembers — without this dict the fence's only stopping condition is
        # draining the ball pool the MANDATORY hunts share.
        self._dex_catch_attempts: dict[int, int] = {}
        #: Last fence verdict string (kept for readers of the adapter's last answer).
        self._dex_catch_last_reason = ""
        #: USER RULING 20 Phase 0 (2026-09-26): (species dex, reason) pairs already LOGGED this run. The log used to
        #: report only when the reason CHANGED — one global string, so a batch could count TRANSITIONS, not species.
        #: Now every species' verdict is logged once per distinct reason per run: countable per species.
        self._dex_catch_logged: set = set()
        # #24-counters phase 2: boss key -> what the counter hunt did, ONE entry per boss
        # per run. This dict IS the bound (see `_counter_ladder`) — a retry or frame
        # budget cannot bound it, because `_prepare_for_fight` is re-entered by the run
        # loop after every lost attempt, which turns any per-call budget into a per-attempt
        # one. Per-RUN by construction, so the next run gets a fresh chance.
        self._counter_hunts: dict = {}
        #: PERSONALITY VALUES of mons the counter chain caught this run (`#24-leadcounter`,
        #: user ruling 2026-08-02). `_lead_best_matchup` promotes these over an EQUALLY SAFE
        #: mon so the answer we travelled for actually fights — batch5 trained a Machoke to
        #: L29 and then led Marshtomp L35 nine times.
        #:
        #: ‼ PER-RUN, and it lives on `self` for that reason. A module-level set would
        #: survive between runs of an ENDLESS RESET batch and start promoting a Pokémon that
        #: no longer exists — that is exactly the `#24-x4-staleslate` bug shape, where
        #: per-run state was never reset and one batch produced almost no usable data.
        #: ‼ PIDs, never slots: `#24-pc` now deposits mid-run, so a slot index goes stale.
        self._hunted_counter_pids: set = set()
        # A hunt that was interrupted mid-flight (whiteout, derail) must not leave the
        # catch-on-sight targets armed for the rest of the run.
        try:
            from modules.story import counter_hunt as _ch

            _ch.disarm()
        except Exception:
            pass

    def on_battle_ended(self, outcome) -> None:
        from modules.battle_state import BattleOutcome

        # ‼ `#26-ch23money` F0 (2026-09-26): the wallet after EVERY battle, so a run's money trajectory —
        # payouts, and (via the next heartbeat) whiteout halvings — is MEASURED, never reconstructed.
        # A pure read; it can never affect the battle or the story.
        try:
            from modules import debug_logger
            from modules.player import get_player

            debug_logger.event(f"after {getattr(outcome, 'name', outcome)} at map {self._location_key()}: "
                               f"money=₽{get_player().money:,}", category="MONEY")
        except Exception:  # noqa: BLE001 - telemetry must never break a battle hook; a missed line is visible
            pass

        if outcome is BattleOutcome.Lost:
            key = self._location_key()
            self._defeat_counts[key] = self._defeat_counts.get(key, 0) + 1
            self._last_defeat_key = key
            # BOSS-TRAINING telemetry (user design 2026-07-23): how many of the
            # opponent's mons did we KO before losing? Read from the game's own
            # battle-results struct (gBattleResults.opponentFaintCounter, offset 1 —
            # decomp include/battle.h). Gen 3 keeps the XP from those KOs through
            # the whiteout, so a lost boss attempt with KOs is real training — the
            # prep logic uses this to decide "keep re-attempting" vs "grind grass".
            kos = 0
            try:
                from modules.memory import read_symbol

                kos = read_symbol("gBattleResults", offset=0x01, size=1)[0]
            except Exception:
                pass
            self._loss_seq += 1
            self._loss_ko_history.setdefault(key, []).append((self._loss_seq, kos))
            foe = None
            try:
                from modules.battle_action_selection import TURN_FOE
                from modules.story.gym_tm_teach import faints_by_foe

                foe = TURN_FOE.get("species")
                if getattr(self, "_boss_battle", None):
                    self._loss_foe_history.setdefault(key, []).append(
                        (self._loss_seq, self._boss_battle, faints_by_foe(list(TURN_FOE.get("log") or ()))))
            except Exception:  # noqa: BLE001 - an unknown foe is filed as nothing and never names a wall
                pass
            console.print(
                f"[yellow]Story: lost a battle at map {key} "
                f"(defeat #{self._defeat_counts[key]} here; KO'd {kos} of theirs first; last foe {foe}"
                f"{'; ' + boss + ' (the leader)' if (boss := getattr(self, '_boss_battle', None)) else ''}).[/]"
            )
        # USER RULING 19: after a LEADER battle (won or lost), mark a taught move SEEN if its recipient chose it vs its
        # wall — the second teach for that boss waits for this. A pure read of the log; never raises into the hook.
        if getattr(self, "_boss_battle", None):
            try:
                from modules.battle_action_selection import TURN_FOE
                from modules.story.gym_tm_teach import note_boss_battle

                note_boss_battle(self, self._boss_battle, list(TURN_FOE.get("log") or ()))
            except Exception:  # noqa: BLE001 - a missed mark only delays a second teach; it is visible in [GYM_TM]
                pass
        self._boss_battle = None

    def on_whiteout(self) -> bool:
        # We handle the whiteout ourselves — do NOT drop to Manual (and the watchdog
        # is hands-off for Story, so no save-state reload). Flag an abort so the
        # running segment bails out promptly; run() then re-orients from the respawn
        # Poké Center and resumes the segmented playthrough from where we left off.
        from modules.story.early_game import set_story_abort

        self._whiteout_pending = True
        set_story_abort(True)
        console.print(
            "[bold yellow]Story: whited out — recovering (navigating the respawn and "
            "resuming from where I left off; no save-state reload).[/]"
        )
        return True

    def _location_key(self):
        try:
            from modules.map import get_map_data_for_current_position

            d = get_map_data_for_current_position()
            return (d.map_group, d.map_number)
        except Exception:
            return None

    def defeat_count_at(self, location_key) -> int:
        return self._defeat_counts.get(location_key, 0)

    def _progress_sig(self):
        """A MONOTONIC fingerprint of story progress from the PARTY structure:
        size, lead level, and total accumulated EXP. These only ever move forward
        and — unlike event flags, which flicker while read during a battle→overworld
        transition — read reliably at any moment. run() compares it across derails
        to tell a transient hiccup mid-progress (a battle finished, a level or a
        Pokémon was gained → reset the derail budget) from a truly stuck loop
        (nothing advances → escalate to Manual). Deliberately excludes flags so a
        flickering flag can never fake progress and mask a genuine freeze."""
        try:
            from modules.pokemon_party import get_party

            party = get_party()
            lead_level = party[0].level if party else 0
            total_exp = sum(getattr(p, "total_exp", 0) for p in party)
            return (len(party), lead_level, total_exp)
        except Exception:
            return None

    def _log_localization(self, note: str) -> None:
        """Report WHERE WE ARE — story stage (from the flag-based detector) + physical
        map — so a derail is diagnosable and self-correction is visible, instead of a
        silent drop to Manual (user directive 2026-07-21)."""
        try:
            from modules.story import detect_live

            prog = detect_live()
            stage = f"{prog.chapter_key}: {prog.chapter_name}"
        except Exception:
            stage = "unknown stage"
        console.print(f"[yellow]Story localization — {note} | stage: {stage} | map {self._location_key()}[/]")

    def _should_catch(self, encounter) -> bool:
        """ADAPTER: read live state, hand it to the PURE `decide_dex_catch`, log the reason.

        Two catching regimes live behind this one call, and the pure predicate keeps them apart:
          * PRE-GYM-1 organic team-building (user directive 2026-07-21) — catch a NEW species into
            the PARTY while there is room. Unchanged, and it must STAY unchanged.
          * POST-GYM-1 THE DEX FENCE (`#24-dexhunt`, user directive 2026-09-04) — catch a NEW species
            into the PC BOX, and ONLY at a full party, with no hunt armed, outside a training grind,
            above a ball reserve, from full strength, capped per species.

        ⛔ ALL DECISION LOGIC LIVES IN `decide_dex_catch`. Nothing here may decide anything: this
        function's ONLY jobs are reading the game and reporting. A condition added here instead of
        there is a condition `probe_dex_catch_fence.py` cannot see, and the reason the old version
        was untestable is that its sixteen conditions were welded to sixteen live reads.

        ‼ THE BLANKET `except` STAYS, BUT IT NO LONGER HIDES. It used to return a bare False, making
        "declined" and "crashed" indistinguishable — the shape that would have let the draft spec's
        invented `counter_hunt.hunt_active()` fail silently forever. It now SAYS so.
        """
        reason = "unevaluated"
        dex, species = None, None
        try:
            from modules.memory import get_event_flag
            from modules.pokemon_party import get_party
            from modules.pokedex import get_pokedex
            from modules.items import get_item_bag
            from modules.story import counter_hunt as _chunt
            from modules.story import early_game as _eg

            raw_party = [p for p in get_party() if p is not None]
            battlers = [p for p in raw_party if not p.is_egg]
            species = getattr(getattr(encounter, "pokemon", None), "species", None)
            dex = species.national_dex_number if species is not None else None
            bag = get_item_bag()

            catch, reason = decide_dex_catch(
                is_wild=encounter is not None,
                is_shiny=bool(getattr(encounter, "is_shiny", False)),
                has_pokedex=bool(get_event_flag("RECEIVED_POKEDEX_FROM_BIRCH")),
                pre_badge1=not get_event_flag("BADGE01_GET"),
                # RAW slots (eggs included) — this decides party-vs-box; see the pure docstring.
                party_slots_used=len(raw_party),
                # EGG-FILTERED — the pre-gym-1 target counts BATTLERS. Feeding the raw count here
                # changed the ordinary case (3 battlers + 1 egg read as a full team of 4).
                battler_count=len(battlers),
                party_target=self._catch_team_target,
                # ‼ THE PINNED PREDICATE, passed through rather than re-implemented (2026-07-31).
                resource_block=_chunt.resource_blocker(),
                # ⛔ EXCLUDES THE MASTER BALL (`items.py:447`). `poke_balls` is the whole pocket, so a
                # bag holding one Master Ball and one Poké Ball satisfies every `> 1` test in this
                # file — and a DISCRETIONARY dex catch must never be the thing that burns it.
                spare_balls=bag.number_of_balls_except_master_ball,
                # ⛔ BOTH ARMING SYSTEMS. `is_armed()` reads only `COUNTER_CATCH_TARGET_DEX`;
                # `early_game.HM_CATCH_TARGET_DEX` is a SECOND, independent one with no is_armed-style
                # reader. Today the HM hunt cannot arm at a full party (`early_game.py:4506` raises
                # before `:4566` assigns), so this OR is belt-and-braces — but that safety is an
                # accident of another function's control flow, not an assertion, and
                # `ensure_hm_learner_making_room` (`:4599`) exists specifically to reach party 6,
                # free a slot and retry.
                hunt_armed=bool(_chunt.is_armed()) or bool(_eg.HM_CATCH_TARGET_DEX),
                training=bool(_eg.swap_train_active()),
                boxed_count=_chunt._box_count(),
                party_healthy=all(p.current_hp == p.total_hp for p in battlers) if battlers else False,
                species_dex=dex,
                owned_dex=frozenset(s.national_dex_number for s in get_pokedex().owned_species),
                party_dex=frozenset(p.species.national_dex_number for p in battlers),
                attempts=self._dex_catch_attempts.get(dex, 0),
                expected_throws=_expected_throws_for(species, bag),
            )
        except Exception as error:  # noqa: BLE001
            # ⛔ NEVER let a read failure break a battle — but never let it be SILENT either.
            reason = f"fence errored ({type(error).__name__}: {error})"
            catch = False

        # Report each SPECIES' verdict once per distinct reason per run (RULING 20 Phase 0) — countable per species,
        # while a route full of owned mons still does not spam the log. `getattr` so a stand-in instance without the
        # per-run reset cannot turn a log line into a crash in the battle hook.
        self._dex_catch_last_reason = reason
        logged = getattr(self, "_dex_catch_logged", None)
        if logged is None:
            logged = self._dex_catch_logged = set()
        line = dex_fence_log_line(logged, dex, getattr(species, "name", "?"), catch, reason)
        if line:
            _log_story_event(line, "DEXFENCE")
        return catch

    # ------------------------------------------------------------------
    # Sweeper-sufficiency gate (user directive 2026-07-23; two-agent Gemini
    # consult archived in tools/story-dev/research-gemini-sufficiency-consult-*).
    # The proactive band prep over-trains whenever one mon already beats the gym
    # (the user's Combusken-L20-vs-Roxanne case). The gate asks, from data a
    # faithful player also has: "do we have a sweeper?" — and only trains when
    # the answer is no (or nearly-yes: a targeted top-up). The REACTIVE net
    # (loss escalation + boss-training) stays the correctness guarantee, so a
    # wrong 'sufficient' call costs 1-2 self-correcting losses, not a run.
    # ------------------------------------------------------------------
    SWEEP_SCORE_FLOOR = 80  # BP x STAB x pair-effectiveness (consult: Mud Shot 82, Double Kick 90)

    # Gen 3: damage category is decided BY TYPE, not by move. A high-BP move off
    # the mon's WEAK attacking stat is a mirage (the Poochyena-Bite trap: Dark is
    # SPECIAL and Poochyena's SpA is dreadful — BPxSTABxeff alone scores it 90).
    _PHYSICAL_TYPES = frozenset(
        {"Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel"}
    )

    @classmethod
    def _sweep_score(cls, mon_types, moves, ace_types, atk=None, spa=None) -> float:
        """Best damage-potential among usable damaging moves vs the ACE's full type
        pair: BP x 1.5 STAB x product-effectiveness x stat-fit. Ace pair, not gym
        primary — Altaria/Kingdra-class aces defeat primary-type reasoning. Stat-fit
        scales a move by (relevant attacking stat / better attacking stat), so a
        special-typed move on a physical attacker scores what it actually hits for."""
        best = 0.0
        for learned in moves:
            if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                continue
            eff = 1.0
            for t in ace_types:
                eff *= learned.move.type.get_effectiveness_against(t)
            stab = 1.5 if any(t.index == learned.move.type.index for t in mon_types) else 1.0
            fit = 1.0
            if atk and spa:
                relevant = atk if learned.move.type.name in cls._PHYSICAL_TYPES else spa
                fit = relevant / max(atk, spa)
            best = max(best, learned.move.base_power * stab * eff * fit)
        return best

    def _sufficiency_verdict(self, cfg: dict):
        """(kind, slot, level) — kind: 'sufficient' (skip prep), 'topup' (train ONE
        mon to `level`), or None (no sweeper in sight — band-prep as always)."""
        from modules.pokemon import get_species_by_index, get_type_by_name
        from modules.pokemon_party import get_party
        from modules.story.early_game import _battler_slots

        if "ace_types" not in cfg or cfg.get("double"):
            return None  # rivals/mixed fights + double battles: always band-prep
        try:
            ace_types = [get_type_by_name(n) for n in cfg["ace_types"]]
        except Exception:
            return None
        ace_level = cfg.get("ace_level", cfg["band"][1])
        need_level = ace_level - 1
        party = get_party()
        best = None  # (priority, -score, slot, kind, train_to)

        def _vulnerable(defender_types) -> bool:
            """Defensive veto (consult): a sweeper the ACE hits super-effectively is
            a coin-flip, not a plan — the Swellow-vs-Wattson trap."""
            for at in ace_types:
                eff = 1.0
                for t in defender_types:
                    eff *= at.get_effectiveness_against(t)
                if eff >= 2.0:
                    return True
            return False

        for i in _battler_slots():
            mon = party[i]
            try:
                mon_types = mon.species.types
            except Exception:
                continue
            entry = None
            if not _vulnerable(mon_types):
                atk = spa = None
                try:
                    atk, spa = mon.stats.attack, mon.stats.special_attack
                except Exception:
                    pass
                score = self._sweep_score(mon_types, mon.moves, ace_types, atk, spa)
                if score >= self.SWEEP_SCORE_FLOOR:
                    if mon.level >= need_level:
                        entry = (0, -score, i, "sufficient", None)
                    elif mon.level >= need_level - 2:
                        entry = (1, -score, i, "topup", need_level)  # close: top up JUST this mon
            if entry is None:
                # Imminent-threshold lookahead (the user's Torchic case): if this mon
                # EVOLVES within +3 levels and the EVOLVED FORM — judged on ITS types
                # (Torchic is Rock-weak and rightly vetoed; Combusken is Rock-neutral)
                # and its level-up moves by that level (Double Kick on evolution) —
                # would qualify, grind JUST this mon to the evolution level.
                try:
                    for evo in mon.species.evolutions:
                        if "LEVEL" not in str(evo.method).upper():
                            continue
                        evo_level = int(evo.method_param)
                        if not (mon.level < evo_level <= mon.level + 3):
                            continue
                        evolved = get_species_by_index(evo.target_species_index)
                        if _vulnerable(evolved.types):
                            continue
                        future = [
                            SimpleNamespace(move=e.move, pp=1)
                            for e in evolved.learnset.level_up
                            if e.level <= evo_level
                        ]
                        e_atk = e_spa = None
                        try:
                            e_atk = evolved.base_stats.attack
                            e_spa = evolved.base_stats.special_attack
                        except Exception:
                            pass
                        if self._sweep_score(evolved.types, future, ace_types, e_atk, e_spa) >= self.SWEEP_SCORE_FLOOR:
                            # FRAME-COST GATE (punch-list #24): `mon.level < evo_level <=
                            # mon.level + 3` above budgets in LEVELS, but the real cost is
                            # FRAMES — a fresh run's local grass was Route 102 L3-5 wilds,
                            # measured at 1433 frames/battle, and 3 "close" levels there
                            # cost ~430,000 frames. Estimate before committing to the plan;
                            # an unknown or over-budget estimate REJECTS it (fail safe).
                            from modules.story.training_areas import estimate_frames_to_level

                            wild_level = _wild_land_max(cfg["grass"][0]) if "grass" in cfg else None
                            est_frames = (
                                estimate_frames_to_level(mon, evo_level, wild_level)
                                if wild_level is not None
                                else None
                            )
                            if est_frames is None or est_frames > self.MAX_PREP_TRAINING_FRAMES:
                                console.print(
                                    f"[yellow]Story: evo-lookahead for {mon.species.name} -> "
                                    f"Lv{evo_level} rejected — estimated "
                                    f"{est_frames if est_frames is not None else 'UNKNOWN'} frames "
                                    f"exceeds budget ({self.MAX_PREP_TRAINING_FRAMES}).[/]"
                                )
                                continue
                            entry = (2, 0.0, i, "topup", evo_level)
                            break
                except Exception:
                    pass
            if entry is not None and (best is None or entry < best):
                best = entry
        if best is None:
            return None
        _prio, _negscore, slot, kind, train_to = best
        return (kind, slot, train_to)

    # ------------------------------------------------------------------
    # KI-23 — boss-training-mode plateau detector (Winona overnight run: 198
    # attempts, 41 losses, 41 whiteouts, never won; L42 Sceptile/L39 Loudred/
    # L36 Mightyena team had NO super-effective answer to Flying — Sceptile is
    # resisted, Ninjask is part-Flying itself, Shedinja is 1 HP — so grinding
    # more levels could never converge). Boss-training mode's existing "2
    # consecutive zero-KO attempts" guard never fires here because a strong
    # mon scores 1-2 KOs every time and still loses forever; this adds a
    # second, independent signal that catches exactly that case.
    # ------------------------------------------------------------------
    def _boss_plan_is_hopeless(self, cfg: dict) -> tuple[bool, list[str]]:
        """(hopeless, needed_type_names). True only when BOTH hold: (1) losses here have
        plateaued — the best KO count in the most recent 3 losses is not better than the
        best in the 3 before that — and (2) no battle-capable party mon has a damaging
        move that hits the boss's `ace_types` for >= 2.0 effectiveness. `needed_type_names`
        lists the attacking types that WOULD be super-effective, computed from the real
        type chart, never hardcoded. Fails safe: any read error returns (False, []) — a
        reader hiccup must never abort a fight."""
        try:
            losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
            if losses < self.PLATEAU_LOSS_THRESHOLD:
                return False, []

            # --- plateau test: best-of-recent-3 losses vs. best-of-previous-3 ---
            history = sorted(entry for k in cfg["keys"] for entry in self._loss_ko_history.get(k, ()))
            if len(history) < 6:
                return False, []  # not enough history to call it — never guess
            recent_best = max(kos for _seq, kos in history[-3:])
            previous_best = max(kos for _seq, kos in history[-6:-3])
            if recent_best > previous_best:
                return False, []  # improving — the existing escalation path is working

            # ‼‼ HARD PLATEAU (`#24-whiteoutloop`, added 2026-08-07). The party-answer test
            # below is a PREDICTION from the type chart: "you own a ≥2.0-effective move of
            # credible power, therefore this fight is winnable." A long flat KO series is a
            # MEASUREMENT that says otherwise, and the measurement has to win eventually —
            # otherwise an UNDERLEVELLED party holding a good move on paper never gives up.
            #
            # MEASURED (four batches, `analyse_defeat_loops.py`): of 53 sequences with >=3
            # defeats at one map, the best-KO trend is FLAT in 37, improving in 15, worse in 1.
            # The worst offender is exactly this shape — PETALBURG_CITY_GYM, **32 consecutive
            # losses**, kos hovering at 2-3 the whole way, with a credible answer in the party
            # the entire time. Whiteout-recovery exhaustion was the TOP end reason of batch
            # `20260807-102552` (4 of 14 non-finishes).
            #
            # ‼ WHY THIS IS KEYED ON FLAT KOs AND NOT ON AN ATTEMPT COUNT — this is the whole
            # design, not a detail. KI-26 records that a run lost **13 times** at ROUTE110 and
            # then went on to reach Fortree, so a plain "give up after N" would have killed a
            # recovering run. The KO series is the discriminator that warning lacked: a run
            # whose KOs are CLIMBING never reaches this branch (the `recent_best > previous_best`
            # return above fires first), and one flat across TWO six-attempt windows is not
            # recovering. Twelve losses is deliberately far above PLATEAU_LOSS_THRESHOLD (6):
            # this is the runaway backstop, not the primary detector.
            hard_plateau = False
            if losses >= self.HARD_PLATEAU_LOSS_THRESHOLD and len(history) >= 12:
                recent_six = max(kos for _seq, kos in history[-6:])
                previous_six = max(kos for _seq, kos in history[-12:-6])
                hard_plateau = recent_six <= previous_six
                if hard_plateau:
                    console.print(
                        # ‼ This prints BEFORE the answer test, so it must not claim anything
                        # about the party's moves — an early draft said "despite the party
                        # holding a type-effective move" and printed that on a party with no
                        # answer at all (repro case 10).
                        f"[bold yellow]Story: {losses} losses here and the KO count has not "
                        f"improved across the last 12 (best {previous_six} -> {recent_six}) — "
                        f"the plan is not working, so escalating instead of re-attempting.[/]"
                    )

            # --- no-answer test: does any battler have a super-effective damaging move? ---
            if "ace_types" not in cfg:
                return False, []
            from modules.pokemon import _types_by_name, get_type_by_name
            from modules.pokemon_party import get_party
            from modules.story.early_game import _battler_slots

            ace_types = [get_type_by_name(n) for n in cfg["ace_types"]]
            party = get_party()
            battlers = _battler_slots()
            if not battlers:
                return False, []
            # ‼ `hard_plateau` SKIPS THE WHOLE ANSWER TEST, it does not `break` out of the
            # inner move loop. The first draft used a break — which exits only the move loop,
            # so the NEXT battler could still `return False, []` and the escalation would fire
            # or not depending on party order. A guard that works for party slot 0 and not for
            # slot 3 is worse than none.
            for i in (battlers if not hard_plateau else ()):
                # STAB needs the carrier's own types; the decision repros pass
                # lightweight stand-ins with no `species`, so treat that as "no STAB"
                # rather than letting an AttributeError abort the whole diagnosis.
                try:
                    own_types = tuple(party[i].species.types)
                except Exception:
                    own_types = ()
                # USER RULING 19: a move the gym-TM teach delivered is NOT a credible answer here — the teach and the
                # honest stop are separate decisions, and a taught Rock Tomb (2x on Winona's Dragon/Flying ace) would
                # otherwise switch off the counter ladder and the 6-loss stop until the 12-loss hard plateau.
                _taught = {m for (p, m) in (getattr(self, "_gym_tm_taught_moves", None) or {})
                           if p == getattr(party[i], "personality_value", None)}
                for learned in party[i].moves:
                    if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                        continue
                    if learned.move.name in _taught:
                        continue
                    eff = 1.0
                    for t in ace_types:
                        eff *= learned.move.type.get_effectiveness_against(t)
                    if eff < 2.0:
                        continue
                    # ‼ SUPER-EFFECTIVE IS NOT THE SAME AS SUFFICIENT. Weight by real
                    # power before accepting it as an answer — a 20-power HM is 2.0x
                    # against Normal and still loses to Slaking 27 times running
                    # (see CREDIBLE_ANSWER_POWER). Being generous here does not make
                    # the bot try harder; it makes the bot never notice it is stuck.
                    stab = 1.5 if learned.move.type in own_types else 1.0
                    if learned.move.base_power * eff * stab >= self.CREDIBLE_ANSWER_POWER:
                        return False, []  # we DO have a credible answer — not hopeless

            # No answer in the party: work out what WOULD be super-effective by asking
            # the type chart directly (never hardcode a type-matchup table).
            needed = []
            for atk_name, atk_type in _types_by_name.items():
                eff = 1.0
                for t in ace_types:
                    eff *= atk_type.get_effectiveness_against(t)
                if eff >= 2.0:
                    needed.append(atk_name)
            return True, needed
        except Exception as error:
            # ‼ THIS `except` FAILS TOWARD "KEEP GRINDING FOREVER". Returning
            # "not hopeless" is the safe answer for a crash, but it is also exactly
            # what a WORKING detector returns — so a bug in here is indistinguishable
            # from a healthy boss plan and costs ~19,000 frames per losing attempt,
            # silently, forever. Caught once already: a stand-in `self` missing a class
            # constant swallowed an AttributeError and disabled the whole diagnosis.
            # Never let it be silent again.
            console.print(
                f"[yellow]Story: boss-plateau detector errored ({error!r}) — treating "
                f"the plan as viable, but this guard is NOT protecting the run.[/]"
            )
            return False, []

    def _counter_ladder(self, cfg: dict, losses: int, needed: list) -> Generator:
        """#24-counters phase 2 — ACT on a hopeless boss diagnosis. Yields as it works;
        returns True if it changed the party's answer to this boss, False to fall through
        to the honest terminal raise.

        THE BOUND, and why it is shaped this way. The hunt runs **once per boss per run**.
        That is not timidity — it is the only bound that actually terminates:

          * A retry budget would not work. The chain fires from inside `_prepare_for_fight`,
            which the run loop re-enters after every lost attempt, so "N tries" becomes N
            per re-entry, i.e. unbounded. (KI-34 burned 23.9M frames on exactly this shape:
            a bounded loop re-entered by its dispatcher is still infinite.)
          * A frame budget would not work either, for the same reason.

        So the bound is on the OUTCOME and recorded in per-run state: this boss gets one
        hunt, and whatever happens, the next hopeless verdict here falls straight through
        to the raise. `14-AGENT-PLAYBOOK.md` rule 3.

        ‼ The catch is only half the job — see `counter_hunt.train_counter`. Catching a
        L15 Machop for a L30 team and leaving it untrained would make
        `_boss_plan_is_hopeless` answer "not hopeless" for ever after (the party now has a
        Fighting move), converting this bounded stop into an unbounded loop.
        """
        from modules.story import counter_hunt, counter_plan
        from modules.story.early_game import UnreachableDestinationError

        key = tuple(cfg["keys"])[0] if cfg.get("keys") else cfg.get("name", "boss")
        if key in self._counter_hunts:
            console.print(
                f"[yellow]Story: already hunted a counter for {cfg.get('name', 'this boss')} "
                f"this run ({self._counter_hunts[key]}) — not trying again; stopping honestly.[/]"
            )
            return False
        # Record the attempt BEFORE doing any of it. If the hunt derails mid-way (a
        # whiteout, a navigation failure), the run recovers and re-enters here — and
        # without this the "once per run" bound would never be written down.
        self._counter_hunts[key] = "started"

        try:
            candidates = counter_plan.find_counter_candidates(
                needed, allow=_counter_area_allowed, max_results=10
            )
        except Exception as error:
            console.print(f"[yellow]Story: counter planner failed ({error!r}) — stopping honestly.[/]")
            self._counter_hunts[key] = "planner failed"
            return False

        # A resource wall applies to EVERY destination, so it ends the ladder outright —
        # walking somewhere else with a full party or one ball is pure waste.
        resource = counter_hunt.resource_blocker()
        if resource is not None:
            console.print(f"[yellow]Story: cannot hunt a counter — {resource}. Stopping honestly.[/]")
            self._counter_hunts[key] = f"blocked: {resource}"
            return False

        # ‼ huntable_candidates, NEVER candidates[0]. Rank 1 for Norman is a Victory Road
        # Hariyama L38-42 — the cost model prices a wild already above the team at ~0 to
        # train, so it ranks endgame maps as CHEAPEST. See counter_plan.huntable_candidates.
        #
        # ‼ AND NOT JUST THE BEST ONE EITHER. Measured 2026-07-30 by driving the real
        # navigation from real saves: Wattson's top huntable destination (ROUTE111 (25,55),
        # north of the Go-Goggles desert) and Winona's (ROUTE118 (29,15), the KI-24
        # dual-elevation-bridge case) BOTH fail to path, in 255 frames, while Norman's
        # FIERY_PATH (18,19) arrives in 2,922. Taking only the best meant two of three
        # bosses burned their one hunt on a place the bot cannot walk to.
        shortlist = counter_plan.huntable_candidates(candidates)[: self.COUNTER_HUNT_MAX_DESTINATIONS]
        if not shortlist:
            blocker = counter_hunt.destination_blocker(None)
            console.print(f"[yellow]Story: cannot hunt a counter — {blocker}. Stopping honestly.[/]")
            self._counter_hunts[key] = f"blocked: {blocker}"
            return False

        attempts = []
        for candidate in shortlist:
            map_enum, tile = candidate["map_enum"], candidate["hunt_tile"]
            # Already proven unreachable from where we stand, this run (#24-regionreach).
            if self._training_blocked(map_enum, tile):
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: known-unreachable")
                continue
            try:
                caught = yield from counter_hunt.hunt(candidate, needed)
            except UnreachableDestinationError as error:
                # ‼ A NAVIGATION failure is CHEAP (255 frames, fail-fast) and specific to
                # ONE place, so it earns a fallback rather than ending the ladder. Record
                # it so nothing re-walks it later this run.
                self._note_training_unreachable(map_enum, tile)
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: unreachable")
                console.print(
                    f"[yellow]Story: {map_enum.name} is not reachable from here "
                    f"({error}) — trying the next counter destination.[/]"
                )
                continue
            if caught is None:
                # ‼ ARRIVED AND CAUGHT NOTHING IS NOT THE SAME FAILURE, and must NOT
                # fall through to another destination. It already cost a full
                # HUNT_SPIN_BUDGET_FRAMES (120,000); doing it again somewhere else would
                # turn a bounded ladder into a multi-hundred-thousand-frame excursion.
                # Cheap failures cascade, expensive ones do not.
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: none found")
                self._counter_hunts[key] = "; ".join(attempts)
                return False

            self._counter_hunts[key] = f"caught {candidate['species_name']}"
            # ‼ #24-leadcounter — remember WHICH mon this is, by PID, so the lead picker can
            # actually field it. Recorded BEFORE training: training can evolve it (Machop ->
            # Machoke at L28, seen 8x in batch5) and can derail, and the PID survives both.
            # ‼ IMPORT IT HERE. `get_party` is NOT in this function's scope — every other
            # user in this file imports it locally — so the original version raised NameError
            # on every catch and the broad `except` below swallowed it. Result: the registry
            # was ALWAYS empty and `#24-leadcounter` could never fire. Batch8 printed
            # `hunted_pids=0` on all 684 lead decisions, which is how it was finally caught.
            # A bare `except Exception` around bookkeeping hid a plain typo for two batches.
            # ‼ `hunt()` returns a DICT since 2026-08-06: {"slot": int|None, "pid": int}.
            # `slot is None` means the party was FULL and the catch went to the PC box.
            slot = caught.get("slot")
            pid = caught.get("pid")

            # Register by PID for BOTH cases. This is what `#24-leadcounter` reads so the lead
            # picker fields the counter, AND what `pc_trip.withdraw_from_box` is gated on, so a
            # boxed catch is collected at the next heal. Registered BEFORE training: training
            # can evolve it (Machop -> Machoke at L28, 8x in batch5) and can derail; the PID
            # survives both.
            # ‼ The old version indexed `get_party()[slot]` here and raised NameError because
            # `get_party` was not in scope — the broad `except` swallowed it, the registry was
            # ALWAYS empty, and `#24-leadcounter` could never fire. Batch8 printed
            # `hunted_pids=0` on all 684 lead decisions. That is why the PID now comes from
            # `hunt()` itself rather than being re-derived here.
            if pid is not None:
                self._hunted_counter_pids.add(pid)
                where = "party" if slot is not None else "PC box"
                console.print(
                    f"[dim]Story: counter registered (pid={pid:08X}, in the {where}); "
                    f"it will lead this boss and is protected from PC deposit.[/]"
                )
            else:
                console.print("[yellow]Story: counter caught but its PID was unreadable — "
                              "it will not be preferred as lead.[/]")

            if slot is None:
                # ‼ A BOXED COUNTER CANNOT BE TRAINED — it earns no XP in the PC. Skip rung 3
                # rather than calling `train_counter(None, ...)`. The withdraw at the next heal
                # puts it in the party; it arrives UNTRAINED, which is a known gap and is worth
                # strictly more than the old behaviour (refuse the catch, end the run).
                console.print(
                    "[yellow]Story: the counter is in the PC box — skipping training; it is "
                    "collected at the next heal. (Boxed mons gain no XP.)[/]"
                )
                return True
            yield from counter_hunt.train_counter(slot, cfg)
            return True

        self._counter_hunts[key] = "; ".join(attempts) or "no destination attempted"
        console.print(
            f"[yellow]Story: no counter destination worked ({self._counter_hunts[key]}) "
            f"— stopping honestly.[/]"
        )
        return False

    def _here_map(self):
        """The map we are standing on, as a (group, number) tuple — None if unreadable."""
        try:
            from modules.map import get_map_data_for_current_position

            return tuple(get_map_data_for_current_position().map_group_and_number)
        except Exception:
            return None

    def _note_training_unreachable(self, map_enum, tile) -> None:
        """Record that `tile` on `map_enum` could NOT be reached from where we stand."""
        here = self._here_map()
        if here is None:
            return  # can't key it safely — better to retry later than to blacklist wrongly
        self._training_unreachable.add((here, tuple(map_enum.value), tuple(tile)))
        console.print(
            f"[yellow]Story: {map_enum.name} {tuple(tile)} is not reachable from here — "
            f"dropping it as a training option for the rest of this run.[/]"
        )

    def _training_blocked(self, map_enum, tile) -> bool:
        here = self._here_map()
        if here is None:
            return False
        return (here, tuple(map_enum.value), tuple(tile)) in self._training_unreachable

    #: `#24-maintain`. Frames one maintenance top-up may spend. Deliberately a FRACTION of
    #: `MAX_PREP_TRAINING_FRAMES` (250k): maintenance is a SIDE ERRAND before a boss, not the main
    #: event, and it may fire once per boss. MEASURED against the REAL bands read from the configs
    #: below (`(13,17) (14,16) (20,24) (24,29) (27,31) (29,33)`): the early/mid cases cost
    #: **4,299 - 63,052** frames, so this admits all of them comfortably.
    #: ⛔ AND IT REFUSES THE TAIL, WHICH IS THE POINT: a laggard facing Tate & Liza (41,42) or Juan
    #: (41,46) needs `catchup` 35-40 on the only ground its level allows, costing **581k-882k** —
    #: all four late cases REFUSED. That is the grind `06-DECISIONS-LOG.md` rejected on 2026-09-10,
    #: and this budget is what stops this design re-creating it.
    MAINTAIN_MAX_FRAMES = 150_000

    def _maintain_lagging_battler(self, target: int) -> Generator:
        """Lift any battler `_prepare_for_fight` is about to EXCLUDE back up to `catchup`.

        ‼ WHY THIS EXISTS (`#24-maintain`, measured). `_prepare_for_fight` builds `to_train` from
        ``party[i].level >= target - TRAIN_CATCHUP_GAP``, so a mon more than 6 levels below the
        boss target is dropped from prep training ENTIRELY. The target rises with every badge, so
        once a mon falls out it can never climb back in - 35% of badge moments were measured
        carrying a mon 15+ levels behind, and §Ch23 then REFUSES to train it at all because the
        estimated grind exceeds `MAX_TRAINING_FRAMES`.

        ⛔ THE EXCLUSION IS CORRECT AND IS NOT RELAXED HERE. Training a 30-levels-behind mon to the
        BOSS's level is the unwinnable grind rejected in `06-DECISIONS-LOG.md` 2026-09-10 (L40->L47
        on the only tabled ground = 285,167 frames against a 250,000 ceiling; and on a L33-40
        ground it cannot win at all - measured 69 battles, 0/43 HP, still L13). ⇒ this does the
        opposite: it stops the mon ever REACHING that state, by topping it up
          * to **`catchup`**, not to the boss's level - just enough to be re-admitted, after which
            the existing, already-budgeted prep path finishes the job; and
          * on a ground keyed to **its own** level via `best_training_grass`, so the fight is
            winnable. Measured across Roxanne->Winona, against the REAL bands: **4,299 - 63,052 frames**.

        ⚠ `scope="lead"`, NEVER `train_team(slots={i})` - KI-84: the slots path computes `need`
        from SLOT INDICES and then permutes the party via `_rotate_lead_safely`, so it silently
        no-ops. `scope="lead"` stops on `_lead_level()` and never touches that path.
        """
        import os as _os          # module convention here - `os` is not imported at module scope

        from modules.pokemon_party import get_party
        from modules.story.early_game import (
            _battler_slots,
            _lead_strongest_battler,
            _rotate_lead_safely,
            _yield_bounded,
            train_team,
        )
        from modules.story.training_areas import best_training_grass, estimate_frames_to_level
        # ‼ Both needed by the fail-soft handler below. `reraise_if_aborting` was NOT imported
        # anywhere in this file — using it without this line is a `NameError` raised while
        # ALREADY handling an exception, which would have turned a skippable errand into a crash.
        from modules.story.early_game import UnreachableDestinationError, reraise_if_aborting
        # ‼ The OTHER navigation failure this errand can hit. `heal_in_pokemon_center` launders every
        # walk error into a fresh exception after 8 ride-outs, so it can NEVER raise
        # `UnreachableDestinationError` — which is why the handler above could not see it and the
        # run died instead (MEASURED: 15 ON vs 3 OFF, 2026-09-12).
        from modules.modes.util.higher_level_actions import HealWalkFailedError

        # ⛔⛔ DEFAULT OFF UNTIL THE ACTION HAS BEEN DRIVEN. Gate #55 proves the DECISION; the code
        # below — rotate, train, restore lead — has never executed a frame. This project's promotion
        # standard is "verified by DRIVING", and `story_mode.py` also carries an urgent latent-crash
        # fix (gate #56) that should not wait. Those two facts conflict only if this feature is LIVE
        # on promotion, so it is not: unset ⇒ dormant, and promoting is behaviour-neutral for it.
        # ⭐ ONE FLAG, NOT TWO. `POKEBOT_MAINTAIN` unset IS the "remove X" arm CLAUDE.md rule 8 asks
        # for, so the separate `POKEBOT_MAINTAIN_FAULT=off` arm was deleted rather than kept beside
        # it — two switches controlling one behaviour is its own bug shape, and the A/B reads better
        # as "the production flag, on vs off" than as "on, vs on-but-sabotaged".
        # ⇒ FLIP THE DEFAULT TO ON in its own reviewable change once the drive passes.
        #
        # ‼‼ **FLIPPED TO ON, 2026-09-12 — USER RULING, and it OVERRULED MY RECOMMENDATION.**
        # I recommended OFF and said so plainly: two A/Bs measured the feature NEUTRAL (badges/run
        # 2.055 vs 2.030; derail rate 64.8% vs 68.0%), and it ELEVATES two other failure modes.
        # The user was shown all of that and ruled *"I like it, lets use the top up."* ⇒ enabled.
        # ⛔⛔ **DO NOT RE-ARGUE THE VALUE QUESTION FROM THIS LINE.** It was asked twice, measured
        # twice, put to the user WITH the recommendation to leave it off, and answered. A future
        # agent finding "this measures neutral, why is it on?" has found the RULING, not a defect —
        # `06-DECISIONS-LOG.md` 2026-09-12 (user ruling) carries the DO-NOT-REOPEN and the reasoning.
        # ⭐ SET `POKEBOT_MAINTAIN=0` to turn it OFF — the switch still works in both directions, so
        # the A/B arm is preserved: "the production flag, on vs off" still reads exactly as before.
        # ‼ THE PREREQUISITES THE RULING ATTACHED, both landed BEFORE this flip (not after):
        #   1. the heal-nav run-killer — `HealWalkFailedError` + the errand's fail-soft handler, and
        #      the retry narrowed so it no longer rides out cutscenes that were never there;
        #   2. ROUTE111 — mechanism FOUND (a successful top-up lands the mon at exactly `catchup`,
        #      which puts it in `need`, which is the precondition for the relocation block) and
        #      BOUNDED: measured **max 1 per run in BOTH arms**, non-fatal, self-healing via
        #      `_note_training_unreachable`. Bounded, not resolved — `#24-maintain-staletarget` and
        #      the ROUTE111 note in `07-CHANGELOG.md` 2026-09-12 carry the candidate fixes.
        if _os.environ.get("POKEBOT_MAINTAIN", "1").strip() not in ("1", "true", "yes", "on"):
            _log_story_event("dormant (POKEBOT_MAINTAIN unset) — decision gated, action UNDRIVEN",
                             "MAINTAIN")
            return

        catchup = target - self.TRAIN_CATCHUP_GAP
        party = get_party()
        battlers = _battler_slots()
        heal_map = _training_area_heal_map()
        budget = self.MAINTAIN_MAX_FRAMES
        if _os.environ.get("POKEBOT_MAINTAIN_FAULT") == "nobudget":
            budget = 10_000_000          # arm: proves the budget gate is what refuses the tail

        # ⛔⛔ ONE PREDICATE, SHARED BY THE DECISION AND THE PICK — they must never disagree.
        # `decide_maintenance` uses `ground_for` to ESTIMATE the cost (band → frames → budget).
        # If the decision saw an unfiltered ground and the pick then refused it, the errand would
        # be approved against ROUTE111's rich L19-22 band yet actually run on a poorer one, blowing
        # the very budget the decision had just checked. ⇒ both take `_maint_allow`.
        # ‼ It is the SAME lambda the relocation path uses (`_training_area_allowed` + the per-run
        # `_training_blocked` memory), NOT a second mechanism — see `_note_training_unreachable`.
        _maint_allow = lambda m, t, p: (  # noqa: E731 - shared by the decision and the pick
            _training_area_allowed(m, t, p) and not self._training_blocked(m, t)
        )
        _maint_ground = lambda lv: best_training_grass(lv, allow=_maint_allow)  # noqa: E731

        # ⛔ THE DECISION IS A PURE PREDICATE (`decide_maintenance`), for the reason its docstring
        # gives: a decision entangled with `yield from` needs a ROM and ~100k frames to exercise ONE
        # branch. This adapter only READS state, hands it over, and REPORTS - gate
        # `probe_maintenance_decision.py` owns the branches.
        slot, reason = decide_maintenance(
            battler_levels={i: party[i].level for i in battlers},
            boss_target=target,
            catchup_gap=self.TRAIN_CATCHUP_GAP,
            ground_for=_maint_ground,
            wild_max_for=_wild_land_max,
            estimate_for=lambda s, to, wild: estimate_frames_to_level(party[s], to, wild),
            heal_for=heal_map.get,
            budget=budget,
        )
        if slot is None:
            # ‼ Only NOISY when something was actually refused. "nobody is behind" is the common
            # case and must not spam a log that a human reads for anomalies.
            if "already at or above" not in reason and "no battlers" not in reason:
                _log_story_event(f"SKIPPED - {reason}", "MAINTAIN")
                console.print(f"[dim]Story: skipping maintenance - {reason}.[/]")
            return

        mon = party[slot]
        # ⛔ Capture IDENTITY now. The slot index is used only to rotate and is meaningless
        # afterwards; the PID is what the completion line asserts on.
        pid, name, level = mon.personality_value, mon.species.name, mon.level
        # ‼ THE SAME predicate the decision just used — see `_maint_ground` above.
        _ground = _maint_ground(level)
        if _ground is None:
            # ⛔ Cannot happen while the predicate is deterministic within one tick (the decision
            # only returned a slot because this same call answered non-None). Guarded anyway: the
            # old code unpacked the result directly, so a None here was a `TypeError` INSIDE a
            # best-effort errand — i.e. a crash where the honest answer is "skip it".
            _log_story_event(f"SKIPPED - ground vanished between decision and pick for {name}",
                             "MAINTAIN")
            return
        grass_map, grass_tile = _ground
        wild_level = _wild_land_max(grass_map)
        est = estimate_frames_to_level(mon, catchup, wild_level)
        heal_center = heal_map.get(grass_map)

        _log_story_event(
            f"start {name} pid={pid:08X} L{level}->L{catchup} on {grass_map.name}{grass_tile} "
            f"wild={wild_level} est={est} budget={budget} boss_target={target}",
            "MAINTAIN",
        )
        console.print(
            f"[cyan]Story: {name} (Lv {level}) is below the Lv {catchup} prep floor - "
            f"maintaining it at {grass_map.name} before this fight.[/]"
        )
        # ⛔⛔ NEVER `yield from` INSIDE A `finally` — MEASURED 2026-09-11, BEFORE THIS EVER RAN.
        # The obvious shape here is try/finally, so that the lead is restored whatever happens. It
        # is WRONG in a generator. When a generator is closed — which CPython does automatically
        # when an abandoned one is garbage-collected, e.g. after a mode switch or a discarded story
        # run — `GeneratorExit` is raised at the suspended yield, and a `finally` that yields again
        # gets **`RuntimeError: generator ignored GeneratorExit`**. Verified directly:
        #     normal completion            -> fine
        #     closed while suspended       -> RuntimeError: generator ignored GeneratorExit
        #     exception propagating out    -> fine
        # ‼ And the exposure is NOT a narrow window: `train_team` can run ~100k frames, so almost
        # all of this method's wall-clock is spent suspended inside that `try`.
        # ⇒ Restore the lead on BOTH paths explicitly, and let `GeneratorExit` through UNTOUCHED —
        # catching it and then yielding reproduces the very fault this avoids.
        # Gate #56 `probe_yield_in_finally.py` now forbids this shape across the story surface.
        # ⛔⛔ THE BUDGET IS ENFORCED AGAINST REAL FRAMES, NOT ONLY AGAINST THE ESTIMATE.
        # An adversarial review caught this: `MAINTAIN_MAX_FRAMES` above gates only the PRE-FLIGHT
        # `estimate_frames_to_level`, and that estimator is `battles * FRAMES_PER_WILD_BATTLE` with
        # **no term for heal round-trips** — a cost this very file measures elsewhere as dominant
        # ("78 heal round trips in one run … every HP dip is a full Poké Center walk"). So an
        # admitted-but-underestimated case had NO live ceiling: `train_team`'s own `guard > 500`
        # bounds ROUNDS, not frames. ⇒ a "budget" nothing checks at runtime is aspirational.
        # `_yield_bounded` drives it with a HARD frame cap and closes it on timeout.
        # ‼ That close is a `GeneratorExit` into `train_team` — which is safe only because no
        # story-surface generator yields from a `finally` any more (gate #56). The two fixes are
        # load-bearing for each other.
        finished = True
        landed = False
        try:
            # ⛔⛔ SLOT 0 IS ALREADY THE LEAD — ROTATING TO IT IS A DESTRUCTIVE NO-OP.
            # `_rotate_lead_safely` drives the party menu's SWITCH option, which is a **SWAP**
            # (`victory_road.py:2046-2059` documents this after it cost a 900k-frame run). And the
            # menu driver's slot arithmetic is `for _ in range(slot - 1)` — for `slot=0` that is
            # `range(-1)`, i.e. ZERO Downs, so the button sequence it sends is **byte-identical to
            # the `case 1:` branch** (Right, A) and therefore **deterministically swaps slot 0 with
            # SLOT 1** (`higher_level_actions.py:666-679`).
            # ‼ CORRECTED 2026-09-12: this comment first said "a swap against whatever the cursor
            # happens to be on". That was vaguer than the truth and would have sent a reader looking
            # for nondeterminism that does not exist. The victim is always slot 1 — which is what
            # makes the harm cheaply PROVABLE: `--driver rotzero` calls
            # `change_lead_party_pokemon(0)` in isolation and watches slots 0 and 1 exchange PIDs.
            # ‼ SLOT 0 IS REACHABLE, NOT HYPOTHETICAL: `decide_maintenance` picks
            # `min(excluded, key=lambda s: (excluded[s], s))` (`:1232`), which breaks ties toward the
            # LOWEST slot index — so slot 0 wins any tie, and trivially wins outright whenever the
            # lead is the weakest lagging battler (e.g. a one-Pokémon party before Roxanne).
            # ⇒ the swap would corrupt party order AND the PID check below would then report
            # "rotation did NOT land", misdiagnosing a self-inflicted swap as a menu failure and
            # abandoning maintenance for exactly the mon this feature exists to help.
            # ⭐ EVERY OTHER CALL SITE IN THE TREE ALREADY GUARDS THIS and this one did not copy it:
            # `counter_hunt.py:767` (`if slot != 0`), `early_game.py:1703`/`:1861` (`if best != 0`),
            # `early_game.py:2080` (`if target_slot != 0`), `victory_road.py:2061`
            # (`if slot_now != 0`). Found by an adversarial review BEFORE the feature shipped ON.
            if slot != 0:
                yield from _rotate_lead_safely(slot)
            # ⛔⛔ VERIFY BY PID THAT THE ROTATION LANDED — the defence `victory_road.py:2062-2081`
            # already carries and this method did not copy. `_rotate_lead_safely` "gives up
            # gracefully" after 3 attempts: it sets `context.message` and returns NORMALLY
            # (`early_game.py:1660`) — no exception, no return value. Without this check the
            # failure is SILENT AND MISREPORTED:
            #   slot 0 still holds the old lead (a high-level mon), so `train_team(scope="lead")`
            #   computes `need = [0] if party[0].level < target_level else []` (`early_game.py:2040`)
            #   → EMPTY → it returns at once → we would log `done … L13->L13 (wanted L14, SHORT)`,
            #   which is **byte-indistinguishable from "it trained and the ground was wrong"**.
            # ‼ Found by an adversarial agent BEFORE the first drive, i.e. before it could produce a
            # false reading. ⇒ two different diagnoses, one log line: that is the bug.
            # ⚠ We ABANDON maintenance rather than raising, unlike §Ch23. There it is the chapter's
            # whole purpose, so a wrong-mon grind must abort; here it is a best-effort errand before
            # a boss, and taking the run down over a missed optimisation would be worse than the
            # laggard it is trying to help. The log says ABANDONED so the two are never confused.
            lead = get_party()[0]
            landed = lead is not None and lead.personality_value == pid
            if not landed:
                holder = "nothing"
                if lead is not None:
                    holder = f"{lead.species.name}#{lead.personality_value:08X}"
                _log_story_event(
                    f"ABANDONED pid={pid:08X} — rotation did NOT land, slot 0 holds {holder}. "
                    f"Training now would grind the WRONG mon and report SHORT.",
                    "MAINTAIN",
                )
                console.print(
                    f"[yellow]Story: could not put {name} in the lead (slot 0 holds {holder}) — "
                    f"skipping maintenance rather than training the wrong Pokémon.[/]"
                )
            else:
                finished = yield from _yield_bounded(
                    train_team(
                        catchup, scope="lead", grass=(grass_map, grass_tile),
                        heal_center=heal_center,
                    ),
                    budget,
                )
        except GeneratorExit:
            # ⛔ We are being closed. Yielding now is exactly the RuntimeError above. Let it go.
            raise
        except UnreachableDestinationError as error:
            # ⛔⛔ ABANDON THE ERRAND — DO NOT TAKE THE RUN DOWN. MEASURED 2026-09-12.
            # This method already argues the case for the ROTATION failure twelve lines up:
            # *"here it is a best-effort errand before a boss, and taking the run down over a
            # missed optimisation would be worse than the laggard it is trying to help."* That
            # reasoning was simply never applied to the NAVIGATION failure, which re-raised into
            # `_play`'s derail recovery and killed the run. The A/B priced the omission:
            #   ARM-ON  552 runs, median run 99 KB, badge-7 in 0.9% of runs
            #   ARM-OFF 243 runs, median run 537 KB, badge-7 in 3.7% of runs
            # with **319** ROUTE102 deaths (plus ROUTE117/103/101) that the control never suffered.
            # ⇒ the feature was net-HARMFUL purely through this handler.
            # ‼ NARROW ON PURPOSE. `UnreachableDestinationError` is the specific "that tile cannot
            # be walked to from here" signal (`early_game.py:333`) — the same type the relocation
            # path catches at the bottom of `_prepare_for_fight`. A broad `except BotModeError`
            # here would swallow a whiteout, because `StoryAbort` IS a `BotModeError` (KI-67) —
            # that is gate #27's whole subject, and it is why the latch is re-checked first anyway.
            reraise_if_aborting(error)
            # Remember it, so the run SELF-HEALS: `_training_blocked` now refuses this ground for
            # the rest of the run FROM THIS MAP, `_maint_allow` filters it out of the very next
            # pick, and `decide_maintenance` then answers a clean "no ground serves that level"
            # instead of walking into the same wall. Without the memory this is the deterministic
            # death loop the relocation path documents.
            self._note_training_unreachable(grass_map, grass_tile)
            yield from _lead_strongest_battler()
            _log_story_event(
                f"ABANDONED pid={pid:08X} — {grass_map.name}{grass_tile} unreachable from here "
                f"({error}). Story continues WITHOUT this top-up.",
                "MAINTAIN",
            )
            console.print(
                f"[yellow]Story: could not reach {grass_map.name} to top up {name} — "
                f"skipping maintenance and carrying on.[/]"
            )
            return
        except HealWalkFailedError as error:
            # ⛔⛔ ABANDON THE ERRAND — the SAME argument the handler above makes, applied to the
            # OTHER navigation failure in this errand. Written as its own handler rather than folded
            # into that one because the two failures need DIFFERENT remedies (see below).
            # ‼ `reraise_if_aborting` FIRST, and here it is NOT ceremony: the 8-ride-out `raise`
            # sits at the TOP of the retry loop, OUTSIDE any `try`, so if the abort latch was set
            # during the preceding `_ride_out_scripted_scene("B")` the fresh error carries no abort
            # identity at all. That is precisely the laundered abort the TYPE cannot detect and the
            # LATCH can (`early_game.py:138-165`, KI-67).
            reraise_if_aborting(error)
            # ⛔ DELIBERATELY **NO** `_note_training_unreachable` HERE — and this is the whole reason
            # `HealWalkFailedError` is a sibling of `UnreachableDestinationError` rather than a
            # subclass of it. The GRASS was fine; the POKÉ CENTER walk broke. Recording the training
            # ground would strike an innocent tile out of `best_training_grass` for the rest of the
            # run — a false diagnosis with a run-long cost, and it would look like a real finding.
            yield from _lead_strongest_battler()
            _log_story_event(
                f"ABANDONED pid={pid:08X} — the heal walk to {heal_center.name} failed ({error}). "
                f"Story continues WITHOUT this top-up. ⚠ THE PARTY MAY BE AT LOW HP/PP: the heal it "
                f"needed did not happen.",
                "MAINTAIN",
            )
            console.print(
                f"[yellow]Story: could not reach the {heal_center.name} Poké Center to heal "
                f"mid-maintenance — skipping maintenance and carrying on.[/]"
            )
            # ⛔⛔ THE COST OF THIS `return`, STATED SO THE NEXT WHITEOUT IS NOT MISDIAGNOSED.
            # `train_team` heals exactly when HP is low or PP is out (`early_game.py:2047, 2111`),
            # so abandoning here walks a DAMAGED, possibly PP-dry party on toward the gym leader —
            # a real whiteout risk that re-raising did not have. It is still the better trade: today
            # the alternative is a CERTAIN derail, and 5 consecutive no-progress derails drop the run
            # to Manual, whereas a whiteout is recoverable and budgeted. ⇒ the log line above says
            # the party may be unhealed, so nobody debugs the resulting whiteout as a battle bug.
            return
        except BaseException:
            # ⛔ Hand the boss a strong lead on the FAILURE path too — leaving the laggard in slot 0
            # would send it out FIRST against the gym leader, strictly worse than not maintaining.
            # ‼ Re-raised unconditionally: this must never SWALLOW a StoryAbort/whiteout (gate #27).
            yield from _lead_strongest_battler()
            raise
        else:
            yield from _lead_strongest_battler()

        # ⛔ Assert on IDENTITY (PID), never a slot index or a party count: the party has just been
        # permuted twice, and a count that nets to zero reads TRUE when nothing happened.
        after = next((p for p in get_party() if p.personality_value == pid), None)
        reached = after is not None and after.level >= catchup
        # ⛔⛔ ONE LINE MUST DISTINGUISH EVERY WAY THIS CAN END, or the reader picks the wrong fix.
        # There are THREE distinct failures and they are not interchangeable:
        #   rotation=NO      → we never trained this mon at all (the silent give-up above)
        #   BUDGET EXHAUSTED → we trained it and ran out of frames ⇒ the ESTIMATE was optimistic
        #                      (it has no heal-round-trip term); the ground was fine
        #   SHORT, rotated, in budget → we trained it and the GROUND was wrong
        # ‼ Until 2026-09-11 all three printed the same `SHORT`. An adversarial review showed the
        # first is byte-indistinguishable from the third, which would have sent a reader to fix the
        # ground table for a bug that lives in the rotation.
        _log_story_event(
            f"done pid={pid:08X} L{level}->L{after.level if after else '?'} "
            f"(wanted L{catchup}, {'REACHED' if reached else 'SHORT'}"
            f", rotation={'landed' if landed else 'NO — never trained'}"
            f"{'' if finished else f', ⛔ LIVE BUDGET {budget} FRAMES EXHAUSTED'})",
            "MAINTAIN",
        )
        if not finished:
            console.print(
                f"[yellow]Story: maintenance for {name} hit its {budget}-frame ceiling before "
                f"reaching Lv {catchup} — stopping here rather than grinding on.[/]"
            )

    def _prepare_for_fight(self, cfg: dict) -> Generator:
        """Before a major fight, train the team to a sensible level (user directive
        2026-07-21). PROACTIVE: a target within the fight's level band (organic,
        randomized). REACTIVE: if we've already LOST here ≥2 times, escalate the
        target and train harder before re-attempting — the "+levels" strategy and
        the team scope are both randomized to look human/organic."""
        import random

        from modules.pokemon_party import get_party
        from modules.story.early_game import train_team, UnreachableDestinationError

        losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
        lo, hi = cfg["band"]
        target = random.randint(lo, hi)  # organic proactive target within the band

        # ‼ `#24-maintain` — MAINTAIN THE LAGGARD BEFORE THE EXCLUSION ABANDONS IT.
        # ⛔ Must run BEFORE the sufficiency gate below, which `return`s early whenever a sweeper
        # answers this gym: that verdict is about the SWEEPER, and the laggard rots regardless.
        yield from self._maintain_lagging_battler(target)

        # ⭐ USER RULING 19 (2026-09-26): LOSING HERE ⇒ TEACH AN OWNED TM THAT HITS THE FOE THAT BEATS US.
        # Before the boss-mode / hopeless / counter-ladder block below, so those judge the party WITH the new move.
        # Fails OPEN (a teach that cannot happen changes nothing) and is latched per (boss, TM) per run; only the
        # three named bosses have a roster (`gym_tm_teach.GYM_ROSTERS`).
        if losses >= 2 and cfg.get("name"):
            from modules.story.gym_tm_teach import maybe_teach_gym_tm

            yield from maybe_teach_gym_tm(self, cfg, losses)

        # --- SWEEPER-SUFFICIENCY GATE (proactive attempts only — once we are LOSING
        #     here, the reactive logic below owns the decision). ---
        if losses < 2:
            verdict = self._sufficiency_verdict(cfg)
            if verdict is not None:
                from modules.pokemon_party import get_party as _gp_v

                kind, slot, train_to = verdict
                name = _gp_v()[slot].species.name
                if kind == "sufficient":
                    console.print(
                        f"[cyan]Story: {name} already answers this gym (type + level "
                        f"sufficiency) — skipping team training.[/]"
                    )
                    return
                if kind == "topup" and "grass" in cfg:
                    # FRAME-COST GATE (punch-list #24): this branch used to call train_team
                    # with no cost estimate at all. Estimate first; an unknown or over-budget
                    # estimate SKIPS the top-up (fail safe) and falls through to the rest of
                    # `_prepare_for_fight` (boss-training mode etc.) instead of committing to
                    # a grind that could burn hundreds of thousands of frames.
                    from modules.story.training_areas import estimate_frames_to_level

                    wild_level = _wild_land_max(cfg["grass"][0])
                    est_frames = (
                        estimate_frames_to_level(_gp_v()[slot], train_to, wild_level)
                        if wild_level is not None
                        else None
                    )
                    if est_frames is None or est_frames > self.MAX_PREP_TRAINING_FRAMES:
                        console.print(
                            f"[yellow]Story: {name} top-up to Lv {train_to} rejected — "
                            f"estimated {est_frames if est_frames is not None else 'UNKNOWN'} "
                            f"frames exceeds budget ({self.MAX_PREP_TRAINING_FRAMES}); "
                            f"falling through to boss-training/band-prep.[/]"
                        )
                    else:
                        console.print(
                            f"[cyan]Story: {name} is the answer to this gym but needs "
                            f"Lv {train_to} — targeted top-up of just that mon.[/]"
                        )
                        yield from train_team(train_to, slots={slot}, grass=cfg["grass"], heal_center=cfg["heal"])
                        return

        # --- BOSS-TRAINING MODE (user design 2026-07-23, Wattson analysis + the Gemini
        #     consult): when we're LOSING here but the local grass is far below our
        #     level, wild grinding is the wrong tool — a L13 wild pays ~145 XP while
        #     KO'ing even two of the boss's mons in a LOST attempt pays ~1,200 XP
        #     (Gen 3 keeps mid-battle XP through a whiteout; there is no re-challenge
        #     limit). So: if
        #     ⛔⛔ CORRECTED 2026-09-08 FROM THE DECOMP — THIS COMMENT USED TO READ
        #     "whiteout money loss is level x badge-payout — cheap", WHICH IS **FIRERED'S**
        #     MODEL, NOT EMERALD'S, AND IT IS THE STATED JUSTIFICATION FOR THIS WHOLE
        #     STRATEGY. Emerald `src/overworld.c:358`:
        #         void DoWhiteOut(void) { ... SetMoney(&money, GetMoney(&money) / 2); ... }
        #     ⇒ **EVERY DELIBERATE LOSS HALVES ALL MONEY.** `MoneyLoss` has ZERO hits in
        #     `pret/pokeemerald`; the `sWhiteOutMoneyLossMultipliers` table this comment
        #     described lives in `pokefirered/src/overworld.c:227`. Our own
        #     `victory_road.py:446` already had it right — the two contradicted each other
        #     and THIS was the wrong half (`#24-regimeb-noescalation` recorded the
        #     contradiction as OPEN; it is now settled).
        #     ⚠ WHAT IS **NOT** ESTABLISHED: whether that cost actually hurts. Money is not
        #     logged, so the 1,477 measured boss-training engagements could not be priced.
        #     ⛔ DO NOT change this strategy on the strength of the corrected fact alone —
        #     see `#24-bosstrainingeconomics`. The premise is now honest; the decision is not
        #     yet made.
        #     recent lost attempts each KO'd at least one boss mon, keep re-attempting
        #     the boss as the PRIMARY training vehicle, with only a LIGHT top-up
        #     between attempts (+1 level cap, not the +5 escalation). The moment two
        #     consecutive attempts produce ZERO KOs, the boss can't teach us anything
        #     — fall through to the classic heavy escalation. ---
        boss_mode = False
        if losses >= 2:
            from modules.pokemon_party import get_party as _gp_levels

            _levels_now = [p.level for p in _gp_levels() if p is not None and not p.is_egg]
            team_max = max(_levels_now, default=0)
            wild_max = None
            try:
                from modules.map import get_wild_encounters_for_map

                if "grass" in cfg:
                    grass_map = cfg["grass"][0]
                    enc = get_wild_encounters_for_map(*grass_map.value)
                    if enc is not None and enc.land_encounters:
                        wild_max = max(e.max_level for e in enc.land_encounters)
            except Exception:
                pass
            recent = sorted(
                (entry for k in cfg["keys"] for entry in self._loss_ko_history.get(k, ())),
            )[-2:]
            recent_kos = [kos for _seq, kos in recent]
            # No grass configured at all (e.g. Lavaridge — no reachable training
            # grass exists) counts as fodder too: grass can't teach us either way.
            grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
            boss_teaches = bool(recent_kos) and any(k >= 1 for k in recent_kos)
            if boss_teaches:  # ⛔ KI-80: NOT `grass_is_fodder and ...` — see `boss_mode` below
                # KI-23 (Winona): a strong mon can KO 1-2 of the boss's mons EVERY attempt and
                # still lose forever if nothing in the party is super-effective against it — the
                # ZERO-KO guard never fires there, and boss-training mode would keep "teaching" us
                # nothing, run after run. Check BEFORE committing to another attempt.
                hopeless, needed = self._boss_plan_is_hopeless(cfg)
                if hopeless:
                    from modules.modes import BotModeError

                    # #24-counters PHASE 2: try to ACT on the diagnosis before stopping.
                    # Bounded to ONE attempt per boss per run (see `_counter_ladder`), and
                    # it falls through to the SAME raise below on every failure path.
                    acted = yield from self._counter_ladder(cfg, losses, needed)
                    if not acted:
                        # ‼ `#26-manualderails` SECOND WIND (2026-08-26). Once the ladder's one
                        # attempt has failed, every derail retry used to re-raise DETERMINISTICALLY
                        # — same instance, same history, zero new information — burning the
                        # 5-derail budget into Manual. MEASURED: the user's flip back to Story
                        # (a fresh instance: losses reset, ladder re-armed) then often WINS —
                        # batch 20260811/L01 lost twice and beat Winona with NO super-effective
                        # answer, refuting this raise's own "grinding will not fix this" premise.
                        # So grant ONE fresh boss-attempt cycle per boss per run: empty this
                        # boss's loss history (the derail retry now does what the flip does) and
                        # return. ⛔ ONCE — the marker below is checked-then-written exactly like
                        # `_counter_ladder`'s consumed-gate, and `_boss_plan_is_hopeless`'s own
                        # len(history) >= 6 gate means the honest stop re-arms after at most 6
                        # fresh flat losses. The 2026-07-30 honest-stop ruling is COMPLIED WITH,
                        # not reopened: the raise below is intact and fires on the next hopeless
                        # cycle. ⚠ Marker + pops BEFORE the print, no yields between — a tripwire
                        # or real derail mid-wind must not re-grant it (`:1655-1658`'s rule).
                        wind_key = tuple(cfg["keys"])[0] if cfg.get("keys") else cfg.get("name", "boss")
                        if wind_key not in self._second_winds:
                            self._second_winds.add(wind_key)
                            for k in cfg.get("keys", ()):
                                self._loss_ko_history.pop(k, None)
                            console.print(
                                f"[bold yellow]Story: counter hunt failed for {cfg.get('name', 'this boss')} "
                                f"— granting ONE second wind: loss history cleared, re-attempting the "
                                f"boss fresh (the honest stop re-arms after 6 fresh flat losses).[/]"
                            )
                            return
                        # ‼ NEVER DELETE THIS RAISE. Silent non-progress is worse than an
                        # honest stop: before phase 1 existed this boss looped for ever,
                        # and the whole value of the diagnosis is that it ENDS the run
                        # with the reason attached.
                        raise BotModeError(_counter_catch_message(cfg, losses, needed))
                    # A rung fired. Re-prepare from the top so the new party member is
                    # taken into account by the sufficiency/boss-mode logic rather than
                    # by this stale pass — the party is not what it was when we entered.
                    return
                if grass_is_fodder:  # ⛔⛔ KI-80: boss_mode STAYS behind the patch test. Removing
                    boss_mode = True  # this guard is KI-23's MIRROR regression (arm 4 catches it).
                    target = team_max + 1  # light top-up — the boss battle is the trainer
                    console.print(
                        f"[bold cyan]Story: boss-training mode — local wilds (max L{wild_max}) are "
                        f"far below the team (L{team_max}); re-attempting the boss is the real "
                        f"training (KO'd {recent_kos} of theirs). Light top-up to L{target} only.[/]"
                    )
            elif grass_is_fodder and recent_kos and not boss_teaches:
                console.print(
                    f"[yellow]Story: last {len(recent_kos)} boss attempts KO'd nothing — "
                    f"the boss can't teach us; falling back to grass escalation.[/]"
                )
        if losses >= 2 and not boss_mode:
            levels = [p.level for p in get_party() if p is not None and not p.is_egg]
            team_max = max(levels, default=0)
            team_avg = (sum(levels) // len(levels)) if levels else 0
            choice = random.choice(["plus5_max", "plus5_avg", "escalate_band"])
            if choice == "plus5_max":
                target = max(target, team_max + 5)
            elif choice == "plus5_avg":
                target = max(target, team_avg + 5)
            else:
                target = max(target, hi + 2 * (losses - 1))
            console.print(
                f"[bold yellow]Story: lost here {losses}× — training harder before "
                f"re-attempting (target Lv {target}, {choice}).[/]"
            )
        # READY THE BATTLERS, don't grind every catch (user 2026-07-21). Bringing a
        # fresh Lv4-6 catch to gym level via half-XP swap-training is a huge grind and
        # unnecessary — our primary mon sweeps the gym. So train only the mons worth
        # readying now: the STRONGEST battler (our primary), plus any battler ALREADY
        # within `TRAIN_CATCHUP_GAP` levels of the target (close enough to finish
        # cheaply). Fresh far-below catches are left to level organically (#24-team).
        # When we've been LOSING here, add depth — also ready the top backups.
        from modules.story.early_game import _battler_slots

        party = get_party()
        battlers = _battler_slots()
        if not battlers:
            return
        strongest = max(battlers, key=lambda i: party[i].level)
        catchup = target - self.TRAIN_CATCHUP_GAP
        to_train = {i for i in battlers if party[i].level >= catchup}
        to_train.add(strongest)
        if losses >= 2:
            ranked = sorted(battlers, key=lambda i: party[i].level, reverse=True)
            to_train.update(ranked[: min(3, len(ranked))])

        need = [i for i in to_train if party[i].level < target]
        if not need:
            console.print(f"[dim]Story: the team's battlers are already ≥ Lv {target} — no prep training.[/]")
        elif "grass" not in cfg:
            # No training grass exists for this boss (e.g. Lavaridge). The re-attempt
            # itself is the only trainer available — boss-training mode's whole point.
            console.print("[dim]Story: no training grass here — re-attempting is the training.[/]")
        else:
            # --- LEVEL-APPROPRIATE RELOCATION (user directive 2026-07-24) ---------------
            # The per-boss `grass` is the LOCAL patch, which is right for most gyms but
            # pathological for NORMAN: his gym is the geographically EARLIEST one yet is
            # fought 5th, so "local" is Route 102 at L3-4 against a L27-31 team — ~25 xp a
            # kill, i.e. effectively never. Rather than grind fodder, look for a training
            # area actually matched to the team and go there (train_team travels
            # warp-aware via _goto_training_area, so a distant area is fine); heal at the
            # PC nearest THAT area, not the boss's, or the bot walks the region every
            # time HP dips. If nothing better exists, do NOT grind fodder at all — skip
            # prep and let the fight + boss-training telemetry own the levelling (a lost
            # boss attempt that KOs 2 mons pays ~1,200 xp; a L4 wild pays ~25).
            grass_map, grass_tile = cfg["grass"]
            heal_at_center = cfg["heal"]
            levels_now = [p.level for p in party if p is not None and not p.is_egg]
            team_max_now = max(levels_now, default=target)
            local_max = _wild_land_max(grass_map)
            # ‼ THE FODDER TEST IS NOW A PURE FUNCTION (KI-31, 2026-07-29).
            # `training_areas.local_patch_is_fodder` holds BOTH rules behind
            # `FODDER_RULE`, which defaults to "legacy" — the expression that used to be
            # inline here, unchanged. Under the default this block behaves exactly as
            # before, including doing NO extra area lookup. The alternative "xp_rate" rule
            # fixes a measured hole (teams below ~L17 can never relocate, because
            # 5 + 12 = 17) but moves early-game prep that `repro_fodder_grass.py` records
            # as proven-good — and that repro needs a real mgba, so it cannot be validated
            # on the dev box. Flip the flag only alongside an A/B on the batch machine.
            _allow = lambda m, t, p: (  # noqa: E731 - shared by the probe and the pick
                _training_area_allowed(m, t, p) and not self._training_blocked(m, t)
            )
            _is_fodder = False
            if local_max is not None:
                from modules.story import training_areas as _ta

                _probe_hi = None
                if _ta.FODDER_RULE == "xp_rate":
                    # Only this rule needs to know the alternative BEFORE deciding, so the
                    # legacy path keeps its original single-lookup shape.
                    try:
                        _probe = _ta.best_training_area(
                            team_max_now, min_wild_max=local_max, allow=_allow
                        )
                        _probe_hi = _probe[2][1] if _probe else None
                    except Exception:  # noqa: BLE001 - a probe failure must not block prep
                        _probe_hi = None
                _is_fodder = _ta.local_patch_is_fodder(
                    local_max, team_max_now, self.FODDER_LEVEL_GAP,
                    best_available_max=_probe_hi,
                )
            if _is_fodder:
                better = None
                try:
                    from modules.story.training_areas import best_training_area

                    # The replacement must beat the local patch AND not be fodder itself
                    # — otherwise we'd walk somewhere new to grind equally-worthless xp.
                    # ‼ KEYED TO THE MONS BEING TRAINED, NOT THE TEAM MAX (#24-relocfloor).
                    # `team_max_now` is the strongest mon; `need` is the stragglers. Keying
                    # the floor to L35 when the trainees are L12/L20 rejected ROUTE111
                    # (L19-22) — the one reachable area — and printed "no better area is
                    # available" 167 times in batch4. See `relocation_floor`.
                    from modules.story.training_areas import relocation_floor

                    floor = relocation_floor(
                        local_max,
                        [party[i].level for i in need if party[i] is not None],
                        self.FODDER_LEVEL_GAP,
                    )
                    # Skip anything this run has ALREADY walked into a wall trying to
                    # reach from where we now stand — see `_training_unreachable`.
                    better = best_training_area(
                        team_max_now,
                        min_wild_max=floor,
                        allow=_allow,
                    )
                except Exception:
                    better = None
                if better is not None:
                    b_map, b_tile, (b_lo, b_hi) = better
                    local_name = grass_map.name
                    grass_map, grass_tile = b_map, b_tile
                    heal_at_center = _training_area_heal_map().get(b_map, cfg["heal"])
                    _msg = (f"Story: {local_name} (max L{local_max}) is fodder for a "
                            f"L{team_max_now} team — relocating to {b_map.name} "
                            f"(L{b_lo}-{b_hi}) to train for real. [rule={_ta.FODDER_RULE}]")
                    console.print(f"[bold cyan]{_msg}[/]")
                    # ‼ ALSO INTO THE DEBUG LOG (2026-07-29). This decision was `console.print`
                    # ONLY, so it never reached a debug log — and a debug log is what gets
                    # shared for review. It made the KI-31 xp_rate A/B unevaluable from a
                    # single-lane run: the effect of the experiment was invisible in the one
                    # artefact describing the run. (x4 bundles ship stdout too, which is why
                    # the control arm was still measurable there — but a debug log should not
                    # depend on that.)
                    _log_story_event(_msg)
                else:
                    _msg = (f"Story: local grass (max L{local_max}) is fodder for a "
                            f"L{team_max_now} team and no better area is available — skipping "
                            f"the grind; the boss attempt itself is the training. "
                            f"[rule={_ta.FODDER_RULE}]")
                    console.print(f"[yellow]{_msg}[/]")
                    _log_story_event(_msg)
                    need = []
            if need:
                console.print(
                    f"[cyan]Story: prepping — training {len(need)} battler(s) to Lv {target} "
                    f"in {grass_map.name} (fresh low catches left to level organically).[/]"
                )
                try:
                    yield from train_team(
                        target, slots=to_train, grass=(grass_map, grass_tile), heal_center=heal_at_center
                    )
                except UnreachableDestinationError:
                    # The reachability oracle said yes and the map disagreed. Remember it
                    # so the next pick differs, THEN re-raise so the normal derail recovery
                    # still runs. Without the memory this is a deterministic death loop:
                    # re-running `_play` re-picks the identical unreachable tile every
                    # derail until the budget drops the run to Manual (2/5 runs, batch
                    # 20260725-194810, Route 111 (25,55) from Mauville).
                    self._note_training_unreachable(grass_map, grass_tile)
                    raise

    def on_battle_started(self, encounter):
        # USER RULING 19: forget the previous battle's foe before this one's first turn, so a loss can never be
        # filed against a foe from an EARLIER battle. A plain write; it cannot affect the battle.
        try:
            from modules.battle_action_selection import TURN_FOE

            TURN_FOE["species"] = None
            TURN_FOE["log"] = []
        except Exception:  # noqa: BLE001 - telemetry reset; a failure only leaves the wall unknown
            pass
        # ...and name the battle: is this enemy party a gym LEADER's roster? (A trainer battle only — a wild encounter
        # is never a leader. Read at battle START, when `gEnemyParty` is certainly this battle's.)
        self._boss_battle = None
        if encounter is None:
            try:
                from modules.pokemon_party import get_opponent_party
                from modules.story.gym_tm_teach import boss_for_enemy_party

                enemy = get_opponent_party() or []
                self._boss_battle = boss_for_enemy_party(
                    [getattr(getattr(m, "species", None), "name", None) for m in enemy
                     if m is not None and not getattr(m, "is_empty", False)])
            except Exception:  # noqa: BLE001 - an unreadable enemy party just means "not a leader" (no wall filed)
                self._boss_battle = None
        # Story battles (the first Birch battle, training, the rival) are meant
        # to be FOUGHT and won with the default battle strategy — never run from
        # or auto-caught. The BattleListener handles the fight while run() pauses.
        #
        # SHINY (user directive 2026-07-22 — supersedes the old fight-through
        # contingency): a wild shiny is a rare collectible and is ALWAYS worth a
        # catch attempt — even an already-caught species, even with a full party
        # (→ PC box), at any story stage. This check runs FIRST so it pre-empts
        # swap-training and ordinary team-catching. With no usable ball we fight
        # through as before (the user's explicit fallback). Either way we return
        # a strategy, which bypasses handle_encounter()'s default "shiny → stop
        # the bot" halt — the story must never stop. The scripted first battle is
        # a Tutorial encounter (the framework forces its flow; no catch possible),
        # so it keeps the fight-through path.
        try:
            if encounter is not None and encounter.is_shiny:
                from modules.console import console
                from modules.items import get_item_bag

                species = getattr(getattr(encounter, "pokemon", None), "species", None)
                name = getattr(species, "name", "Pokémon")
                is_tutorial = getattr(getattr(encounter, "type", None), "name", "") == "Tutorial"
                have_balls = False
                try:
                    have_balls = sum(s.quantity for s in get_item_bag().poke_balls) > 0
                except Exception:
                    pass
                if not is_tutorial and have_balls:
                    console.print(
                        f"[bold yellow]Story Mode: ✨ a SHINY {name} appeared — "
                        f"attempting to CATCH it (shinies are always worth a ball)![/]"
                    )
                    context.message = f"Story: ✨ shiny {name} — attempting the catch!"
                    return StoryShinyCatchStrategy()
                console.print(
                    f"[bold yellow]Story Mode: a SHINY {name} appeared but "
                    f"{'this is the scripted tutorial battle' if is_tutorial else 'there are no usable Poké Balls'}"
                    f" — fighting through (not stopping).[/]"
                )
                context.message = f"Story: shiny {name} — no catch possible here, fighting through."
                return LevelUpTravelBattleStrategy()
        except Exception:
            pass
        # HM-LEARNER HUNT (user directive 2026-07-23): while ensure_hm_learner is
        # spinning for a species that can learn a needed HM, catch it on sight —
        # any story stage, needs only party room and a spare ball.
        try:
            from modules.story import early_game as _eg

            if _eg.HM_CATCH_TARGET_DEX and encounter is not None and not getattr(encounter, "is_shiny", False):
                from modules.items import get_item_bag
                from modules.pokemon_party import get_party as _gp

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                if (
                    sp is not None
                    and sp.national_dex_number in _eg.HM_CATCH_TARGET_DEX
                    and len([m for m in _gp() if m is not None]) < 6
                    and sum(sl.quantity for sl in get_item_bag().poke_balls) > 1
                ):
                    # ‼ local import required: later branches in this method import
                    # `console` locally, which makes the name function-local EVERYWHERE
                    # in the method — referencing the module-level one here raises
                    # UnboundLocalError (and the except silently ate the catch).
                    from modules.console import console

                    console.print(f"[bold green]Story: catching {sp.name} — it can learn the HM we need![/]")
                    return StoryCatchStrategy()
        except Exception:
            pass
        # COUNTER-CATCH HUNT (#24-counters phase 2): while `counter_hunt.hunt` is spinning
        # for the species that answers a boss we cannot beat, catch it on sight. Deliberate
        # clone of the HM branch above — same gates (party room, a SPARE ball, not a shiny),
        # same failure mode if they are skipped.
        try:
            from modules.story import counter_hunt as _chunt

            if (
                _chunt.COUNTER_CATCH_TARGET_DEX
                and encounter is not None
                and not getattr(encounter, "is_shiny", False)
            ):
                from modules.items import get_item_bag
                from modules.pokemon_party import get_party as _gp_c

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                # ‼ NO `party < 6` GATE HERE — deliberately, and unlike the HM branch above
                # (`#24-pcoverflow` break 2, wired 2026-08-06). A catch with a full party is
                # FULLY AUTOMATIC in Emerald: `Cmd_givecaughtmon` -> `GiveMonToPlayer` ->
                # `CopyMonToPC`, no prompt, no input, deterministic destination box. The shiny
                # branch at the top of this method already relies on exactly that.
                #
                # The old gate is why this feature never fired: the hunt would travel across
                # Hoenn, arm the target, spin the full 120,000-frame budget, and REFUSE the
                # catch — reporting "found nothing" while standing next to the answer. With
                # 14 boxes x 30 = 420 slots against ~202 species, overflow is not a real risk;
                # and if the PC ever were full the game simply refuses to throw the ball
                # (`gText_BoxFull`), which is a no-op, not a lost Pokémon.
                #
                # ‼ The BALL gate stays. Never attempt a catch without a spare — that is the
                # resource rule `resource_blocker` enforces, and it is unrelated to party space.
                # ‼‼ HISTORY ONLY — **THIS FEATURE IS ON.** The paragraph below describes why it
                # was gated OFF on 2026-08-06; it was RE-ENABLED on 2026-08-07 and the live default
                # is `"1"` — see the DEFAULT ON block ~35 lines down, immediately above the
                # `environ.get` that actually decides.
                # ‼ THIS COMMENT IS WHY THIS WARNING EXISTS. On 2026-08-11 four documents
                # (`29-DISABLED-FEATURES-REGISTRY.md`, KI-54, and `04-HANDOFF.md` twice) were
                # written FROM THIS PARAGRAPH instead of from the default below it, and recorded
                # the feature as disabled and "one unhandled text box away" from working. That
                # became the stated blocker on roster work — which is the blocker on §Ch21 — and
                # cost a full investigation on 2026-08-12 before the live default was read.
                # ⇒ **When a comment and the code beside it disagree, the code wins and the comment
                # is the bug.** Leaving the comment armed after retracting it in the docs is how
                # the same wrong conclusion gets re-derived a fifth time.
                #
                # (historical) GATED OFF (`POKEBOT_BOX_OVERFLOW_CATCH`, default 0) after batch
                # `20260806-142418` graded it against its own pre-registered target and it
                # FAILED: `withdrawing` **0** (target ≥1) and `INTO THE PC BOX` **0** — the
                # path NEVER FIRED in 26 runs. Same batch: finish rate 52.0% → 30.8% and
                # `global watchdog` 20 → 68.
                #
                # ‼ I am NOT claiming this change caused the regression — it is not supported.
                # Of 43 watchdog STUCK dumps, only **10** had a full party; 33 were at party
                # 4-5 where this gate has no effect. The wedges are battles with a mostly-dead
                # team on `BattleScript_PrintCantEscapeFromBattle`, which is a battle-handler
                # shape, not a catch shape. It is gated because it DELIVERED NOTHING, not
                # because it was proven harmful.
                #
                # ‼ WHAT IS MISSING, and it is the reason it cannot work yet (user-identified
                # 2026-08-06, then decomp-confirmed): a box-send shows an EXTRA TEXT BOX the
                # party-catch path never shows, and the bot has NO handling for it —
                # `grep` for `VAR_PC_BOX_TO_SEND_MON` or "sent to" across `modules/` returns
                # ZERO. `Cmd_givecaughtmon` picks one of FOUR variants
                # (`B_MSG_SENT_SOMEONES_PC` / `B_MSG_SOMEONES_BOX_FULL`, each +1 once
                # `FLAG_SYS_PC_LANETTE` is set). Until that message is dismissed — and the
                # destination box read from `VAR_PC_BOX_TO_SEND_MON` rather than parsed from
                # text — enabling this risks wedging the battle exit on every full-party catch.
                #
                # ‼ The same gap applies to `StoryShinyCatchStrategy`, which claims to catch
                # duplicates into the box and has almost certainly never been exercised.
                import os as _os

                # ‼ DEFAULT ON since 2026-08-07 — the CAPABILITY TEST PASSES.
                # `story_harness.py post_mtpyre.ss1 --driver boxcatch` (full party of 6, empty
                # box) measured, live:
                #     RESULT      caught=True box_before=0 box_after=1 exited_clean=True
                #                 exit_frames=120 box_var=0   (box_var 0 = BOX1, matches the
                #                                              on-screen "placed in BOX1")
                #     AFTER-CATCH usable=True second_catch=True frames=20 box_now=2
                # i.e. the catch stored the mon, the battle exit settled with ZERO forced
                # presses, and the bot then caught a SECOND mon into the box 20 frames later.
                # The overflow path is not broken; it simply never had a full party when the
                # counter hunt fired (batch `20260806-142418`: 10 counter catches, all to the
                # party). Set to "0" to disable.
                _allow_box_overflow = _os.environ.get(
                    "POKEBOT_BOX_OVERFLOW_CATCH", "1"
                ).strip() in ("1", "true", "True")
                _party_has_room = len([m for m in _gp_c() if m is not None]) < 6
                if (
                    sp is not None
                    and sp.national_dex_number in _chunt.COUNTER_CATCH_TARGET_DEX
                    and (_party_has_room or _allow_box_overflow)
                    and sum(sl.quantity for sl in get_item_bag().poke_balls) > 1
                ):
                    # ‼ LOCAL IMPORT REQUIRED — the same trap that silently ate the HM
                    # branch and survival mode (08-MISTAKES 2026-07-26, three times in one
                    # day). Other branches in this method import `console` locally, which
                    # makes the name function-local for the WHOLE method, so touching the
                    # module-level one here is an UnboundLocalError that the `except` below
                    # would swallow — the catch would simply never happen, silently.
                    from modules.console import console

                    console.print(
                        f"[bold green]Story: catching {sp.name} — it is the type counter "
                        f"this boss needs![/]"
                    )
                    return StoryCatchStrategy()
        except Exception:
            pass
        # ‼ SURVIVAL MODE (#24-whiteout, from live batch 20260725-194810). WILD battles
        # on a map that has already wiped us repeatedly stop being an XP opportunity and
        # become the thing to escape. run01 whited out **25 times on ROUTE110** — respawn
        # in Slateport, walk back north, wipe again — and nothing ever noticed, because
        # the default `LevelUpTravelBattleStrategy` fights every wild to level the lead.
        # Its own docstring says it "flees only at low HP, which the training loop covers
        # by healing" — but this is a TRAVEL leg, where no training loop and therefore no
        # healing exists, so HP only ever goes down across consecutive encounters.
        #
        # Scope is deliberately narrow:
        #   * WILD only (`encounter is not None`) — a trainer battle cannot be fled, and
        #     the boss/gym re-attempt path must stay exactly as it is.
        #   * NOT during `train_team` — there the swap strategy plus its heal loop are the
        #     correct answer, and fleeing would starve the grind it was sent to do.
        #   * Threshold is per-MAP defeats this run, so it cannot fire on a first bad
        #     encounter; it takes a demonstrated pattern.
        try:
            from modules.story.early_game import swap_train_active

            if (
                encounter is not None
                and not swap_train_active()
                and self._defeat_counts.get(self._location_key(), 0)
                >= self.SURVIVAL_WHITEOUT_THRESHOLD
            ):
                # ‼ StoryFleeStrategy, NOT the stock RunAwayStrategy — the stock one
                # returns False from choose_new_lead_after_battle(), which crashed a
                # live run through fight()'s rotation path. See the class docstring.
                # ‼ LOCAL IMPORT REQUIRED — same trap as the HM branch above, and it
                # caught this block too (2026-07-25): other branches in this method
                # import `console` locally, which makes the name function-local for the
                # WHOLE method, so touching the module-level one here is an
                # UnboundLocalError that the `except` below silently ate. The repro
                # showed survival mode simply "not firing"; nothing was logged.
                from modules.console import console

                console.print(
                    f"[bold yellow]Story: {self._defeat_counts.get(self._location_key(), 0)} "
                    f"defeats on this map already — fleeing wild battles to get through "
                    f"instead of levelling into another whiteout.[/]"
                )
                return StoryFleeStrategy()
        except Exception:
            pass
        # CATCHING — two regimes, one predicate (`decide_dex_catch`):
        #   PRE-GYM-1  organic team building (user directive 2026-07-21) -> joins the PARTY
        #   POST-GYM-1 the `#24-dexhunt` fence (user directive 2026-09-04) -> goes to the PC BOX
        try:
            if self._should_catch(encounter):
                from modules.console import console
                from modules.pokemon_party import get_party as _gp_dex

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                dex = getattr(sp, "national_dex_number", None)
                # ‼ INSTRUMENT THE ACTION, NOT THE INPUT TO IT (CLAUDE.md rule 7). Count the attempt
                # HERE — at the point the bot actually commits to a catch — not inside the predicate,
                # which is called for evaluation and must stay pure.
                if dex is not None:
                    self._dex_catch_attempts[dex] = self._dex_catch_attempts.get(dex, 0) + 1
                # ⛔ THE DESTINATION IS DERIVED, NOT ASSUMED. This line read "for the team!" until
                # 2026-09-10; at a full party the game stores the catch via
                # `Cmd_givecaughtmon -> GiveMonToPlayer -> CopyMonToPC` and the message was about to
                # start lying on the exact path the fence adds. Read the slot count the game reads.
                try:
                    _full = len([m for m in _gp_dex() if m is not None]) >= PARTY_CAPACITY
                except Exception:
                    _full = False
                _where = "into the PC box" if _full else "for the team"
                console.print(
                    f"[bold green]Story: catching a new {getattr(sp, 'name', '?')} {_where}![/]"
                )
                # ‼ A BOX CATCH IS INVISIBLE TO EVERY EXISTING INSTRUMENT: it changes neither the
                # party length nor its PID set, so `debug_logger`'s `[PARTY]` event never fires, and
                # the only other positive signal is the `[DEX]` delta computed once per 3,600-frame
                # heartbeat. An A/B grading "did the fence act?" would be reading a coarse, indirect
                # instrument on the one path it exists to measure.
                _log_story_event(
                    f"[DEXCATCH] attempt #{self._dex_catch_attempts.get(dex, 0)} on "
                    f"{getattr(sp, 'name', '?')} (#{dex}) -> {'box' if _full else 'party'}",
                    "DEXCATCH",
                )
                # Use the story catch strategy (flees when out of balls instead of
                # dropping to Manual — see StoryCatchStrategy).
                # ⭐ AFTER GYM 1 the catch is DISCRETIONARY (the fence regime): the dex-only subclass bails at the
                # ball reserve or on a faint (`#24-dexcatch-battlebail`, RULING 20 Phase 0). Pre-gym-1 team building
                # keeps the plain strategy, byte-identical.
                try:
                    # ⛔ ALIASED local import: `get_event_flag` is not a module-level name here, and an UN-aliased local
                    # import would make it function-local for this whole method (UnboundLocalError elsewhere, swallowed
                    # by an `except` — the silent-failure shape recorded in 08 more than once).
                    from modules.memory import get_event_flag as _gef_dexbail

                    _post_badge = bool(_gef_dexbail("BADGE01_GET"))
                except Exception:  # noqa: BLE001 - unreadable ⇒ the plain strategy, exactly the pre-change behaviour
                    _post_badge = False
                return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()
        except Exception:
            pass
        # SWAP-TRAINING: while train_team is running, use the swap strategy so an
        # under-levelled lead is switched out to a stronger team-mate (shares XP, no
        # fainting) instead of grinding itself to death against higher-level wilds.
        try:
            from modules.story.early_game import swap_train_active

            if swap_train_active() and encounter is not None:
                return SwapTrainBattleStrategy()
        except Exception:
            pass
        # Fight to WIN and level the lead (strongest move; flees only at low HP,
        # which the training loop covers by healing). The travel variant also
        # refuses to flee a TRAINER battle (single-mon party can't — see ML-8),
        # fighting on instead; used for training wilds, the rival, and route
        # trainers. The scripted first battle is a Tutorial (framework-handled).
        #
        # ‼ `#24-battleitems` (user directive 2026-08-09): this is now the ITEM-AWARE subclass.
        # It is a strict superset — `StoryItemBattleStrategy` only acts in TRAINER battles, and
        # falls through to exactly this behaviour everywhere else and whenever its policy says
        # no. Wild encounters, training and catching are therefore bit-identical to before.
        return StoryItemBattleStrategy()

    def run(self) -> Generator:
        # DEFEAT / WHITEOUT RECOVERY (user directive 2026-07-21): the segmented resume
        # (`_play`) runs inside a restart loop. On a whiteout, on_whiteout() flags an
        # abort → the running segment bails → we catch it here, re-orient from the
        # respawn point, and re-run `_play` (which skips finished segments and
        # re-attempts the failed one). GENUINE (non-whiteout) errors propagate to
        # Manual exactly as before. No save states are ever reloaded.
        from modules.modes import BotModeError
        from modules.story.early_game import set_story_abort, exit_building_after_whiteout
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable
        from modules.battle_fault import take_pending_fault, clear_pending_fault
        from modules.story.early_game import whiteout_budget

        # Never inherit a fault recorded just before this mode started.
        clear_pending_fault()

        recoveries = 0
        # `#24-whiteoutloop`: the respawn location at the PREVIOUS whiteout. `recoveries` is keyed to
        # CONSECUTIVE whiteouts at one place, so this is the half that says "did we move on?".
        last_whiteout_key = None
        while True:
            set_story_abort(False)
            self._whiteout_pending = False
            try:
                # GLOBAL NEVER-HANG WATCHDOG (#24-interrupt, real-HW log 2026-07-22):
                # a wedged primitive can spin the mode generator forever with no error
                # (a trainer-intro msgbox opened mid-turn and ensure_facing_direction
                # pressed direction keys at a locked avatar for 85k frames — only the
                # debug logger noticed). Drive _play frame by frame and watch a broad
                # stall signature (map, position, game state, party, message): if
                # NOTHING changes for 18k mode-driven frames (~5 min; battles don't
                # count — a listener holds control then), raise a derail so run()'s
                # own recovery (B-ride scripts, re-orient, re-enter) takes over.
                _play_gen = self._play()
                _stall_sig = None
                _stall_frames = 0
                while True:
                    # RECOVERABLE BATTLE FAULT (#24-movelearn-recovery, 2026-07-25).
                    # The battle handler runs as a SIBLING generator on the controller
                    # stack, so an error it raises goes straight to main_loop → Manual
                    # and never reaches the `except BotModeError` below. Instead it
                    # parks the reason in `battle_fault`; we claim it HERE, inside the
                    # try, so a battle we cannot finish costs one derail (with the
                    # normal B-ride/re-orient/resume) instead of the entire run.
                    _fault = take_pending_fault()
                    if _fault is not None:
                        try:
                            _play_gen.close()
                        except Exception:
                            pass
                        raise BotModeError(f"Story: battle handler gave up — {_fault}")
                    try:
                        next(_play_gen)
                    except StopIteration:
                        return
                    # KI-15 post-battle message nudge: an inline battle fought/fled
                    # during navigation or training can leave a battle message ("grew
                    # to LV. N!", "won $N", "Got away safely!") waiting for A in the
                    # overworld while the running primitive (navigate/spin/facing)
                    # doesn't press it — stranding the resume until the 18k watchdog.
                    # It is BATTLE text (A clears it; B does not, proven on the (14,5)
                    # capture) with NO field script active.
                    # ‼ The signature must hold for a SUSTAINED stretch before we
                    # press, and we press ONCE per stretch: `cb` stays
                    # "ReturnFromBattle..." (stale) until the NEXT battle, and a live
                    # NPC dialogue's script context flickers inactive between message
                    # boxes — an every-frame nudge A-mashed the Rustboro nurse's
                    # dialogue into an endless re-open loop (this session's (7,4)
                    # capture; the museum-greeter lesson). The genuine stale wedge is
                    # rock-stable for hundreds of frames (probe: 400+ unchanged), so
                    # 90 consecutive matching frames identifies it safely, and one A
                    # clears it instantly (proven frame-0 on the (14,5) capture).
                    try:
                        from modules.tasks import (
                            is_waiting_for_input as _iwfi,
                            get_global_script_context as _ggsc,
                            get_immediate_script_context as _gisc,
                        )
                        from modules.battle_state import battle_is_active as _bia
                        from modules.memory import get_game_state as _ggs0, GameState as _GS0
                        from modules.player import get_player_avatar as _gpa15

                        # NO reader distinguishes this wedge from a field dialogue's
                        # parked WaitForAorBPress tail (identical stale native; both
                        # ignore B — probed on the captures; two rider-side designs
                        # failed, see 08-MISTAKES 2026-07-24). The wedge's ONE unique
                        # property: it BLOCKS ALL MOVEMENT. So the signature demands
                        # waiting + no scripts + POSITION FROZEN for 240 consecutive
                        # frames → a single A → 1200-frame cooldown. A dialogue tail
                        # can't match (the story flow keeps walking → position
                        # changes reset the count); a live dialogue's script context
                        # going active resets it too (the every-frame ancestor of
                        # this nudge A-mashed the nurse — ki15_nurse_wedge.ss1).
                        try:
                            _pos15 = tuple(_gpa15().local_coordinates)
                        except Exception:
                            _pos15 = None
                        if (
                            _pos15 is not None
                            and _pos15 == getattr(self, "_ki15_nudge_pos", None)
                            and _ggs0() is _GS0.OVERWORLD
                            and not _bia()
                            and _iwfi()
                            and not _ggsc().is_active
                            and not _gisc().is_active
                        ):
                            self._ki15_nudge_stable = getattr(self, "_ki15_nudge_stable", 0) + 1
                            if self._ki15_nudge_stable >= 240:
                                context.emulator.press_button("A")
                                self._ki15_nudge_stable = -1200  # long cooldown
                                # breadcrumb for run-log forensics (run 8: a wedge
                                # this nudge should own sat 20k frames — prove
                                # in future logs whether it fired)
                                console.print("[dim]Story: KI-15 nudge fired (stale post-battle message).[/]")
                        else:
                            _n = getattr(self, "_ki15_nudge_stable", 0)
                            self._ki15_nudge_stable = 0 if _n > 0 else min(_n + 1, 0)
                        self._ki15_nudge_pos = _pos15
                    except Exception:
                        pass
                    yield
                    try:
                        from modules.map import get_map_data_for_current_position
                        from modules.memory import get_game_state as _ggs
                        from modules.player import get_player_avatar as _gpa

                        _md = get_map_data_for_current_position()
                        _cur = (
                            (_md.map_group, _md.map_number),
                            tuple(_gpa().local_coordinates),
                            str(_ggs()),
                            self._progress_sig(),
                            context.message,
                        )
                    except Exception:
                        _cur = None
                    if _cur is not None and _cur == _stall_sig:
                        _stall_frames += 1
                        if _stall_frames >= 18000:
                            try:
                                _play_gen.close()
                            except Exception:
                                pass
                            raise BotModeError(
                                "Story: global watchdog — nothing progressed for 18,000 frames "
                                "(the current step is wedged); derailing into recovery."
                            )
                    else:
                        _stall_sig = _cur
                        _stall_frames = 0
            except BotModeError as err:
                from modules.memory import game_has_started, get_game_state, GameState

                # ⛔⛔ EVERY RECOVERY STARTS FROM NO INPUT — KI-106 / `#27-evgpcwedge` (2026-09-27).
                # `_held_inputs` is Python-side state that is OR'd into the pad every frame
                # (`modules/libmgba.py:581`). The generator that just raised is abandoned mid-walk,
                # and navigators hold direction+B with no `finally:` (`walking.py`; §Ch23's
                # `_sampling` too), so whatever they held survives into this recovery.
                # ⭐ WHAT THAT COST (batch `#26-batch0926`, run P1r8, an 8-badge run): a trainer
                # interrupted leg 5's walk north, the party whited out, and B+Up survived the
                # whiteout. The listener's own release runs BEFORE `isolate_inputs` restores the
                # interrupted walk's mask. Held Up walked the respawn at Ever Grande (27,49)
                # straight through the Poké Center door to the counter. Emerald reads a held Up
                # before Down (`field_control_avatar.c`), so every later
                # `ensure_facing_direction(Down)` failed — five derails and the run was over.
                # ‼ THIS SEAM ON PURPOSE: both the whiteout and the derail recovery below begin
                # here, and the dead generator can no longer hold anything, so nothing is lost by
                # clearing. The recovery's own walks set their own held buttons afresh. (A hand-off
                # that never raises — a direct `context.set_manual_mode()` — is covered separately:
                # `set_manual_mode` releases held buttons itself, `modules/context.py`.)
                # ⛔ Do NOT move this to a per-frame path — navigation depends on held buttons
                # (the `#24-truckleak` note at the hard-reset seam says the same, for the same reason).
                # ‼ It ANNOUNCES the mask it released — a silent release cannot be graded.
                # Arm `POKEBOT_RECOVERY_FAULT_KEEPHELD=1` skips the release and still logs the mask it
                # WOULD have released, so both arms of the A/B record the same premise reading.
                import os as _os_held

                _held_keep = _os_held.environ.get("POKEBOT_RECOVERY_FAULT_KEEPHELD") == "1"
                # (`libmgba.py` is upstream-shared and has no mask getter, so the arm reads the
                # attribute `reset_held_buttons()` itself returns — read-only, never written here.)
                _held_mask = (getattr(context.emulator, "_held_inputs", 0) if _held_keep
                              else context.emulator.reset_held_buttons())
                if _held_mask:
                    try:
                        from modules import debug_logger

                        debug_logger.event(
                            f"RECOVERY-HELD: {'KEPT (fault arm)' if _held_keep else 'released'} "
                            f"leaked held inputs 0x{_held_mask:04x} at the start of "
                            f"{'whiteout' if self._whiteout_pending else 'derail'} recovery — KI-106"
                        )
                    except Exception as _held_log_err:  # the release above already happened; say the log failed
                        console.print(f"[yellow]RECOVERY-HELD (mask 0x{_held_mask:04x}, keep={_held_keep}): "
                                      f"its debug log line failed: {_held_log_err!r}[/]")

                if not self._whiteout_pending:
                    # NON-WHITEOUT DERAIL (user directive 2026-07-21): don't drop
                    # straight to Manual — re-localise (log where we are in the story
                    # AND on the map) and retry the segmented resume a bounded number
                    # of times. The resume re-detects the stage from flags + position,
                    # so a transient nav/scene hiccup self-corrects. Only hand to
                    # Manual if it keeps failing (a genuine, persistent problem).
                    # Reset the budget when we've made real progress since the last
                    # derail: a long segment (training, a chapter) can throw a few
                    # unrelated transient hiccups, and those must NOT accumulate into
                    # a false drop to Manual. Only CONSECUTIVE no-progress derails —
                    # a genuine stuck loop — escalate.
                    sig = self._progress_sig()
                    if sig != self._last_derail_sig:
                        self._derails = 0
                        self._last_derail_sig = sig
                    self._derails += 1
                    self._log_localization(f"derail #{self._derails}: {err}")
                    try:
                        from modules import debug_logger

                        debug_logger.event(f"DERAIL #{self._derails}: {err}")
                    except Exception:
                        pass
                    if self._derails > 4:
                        raise
                    set_story_abort(False)
                    try:
                        # FIRST close any OPEN scripted dialogue: waiting alone presses
                        # nothing, and an open msgbox (Briney's post-sail Letter reminder,
                        # real-HW 2026-07-22) keeps the avatar non-controllable FOREVER —
                        # the recovery itself was derail-looping on it. _ride_out_scripted_
                        # scene B-advances an active script and is a cheap no-op otherwise.
                        from modules.story.early_game import (
                            _ride_out_scripted_scene,
                            wait_until_truly_controllable,
                        )

                        yield from _ride_out_scripted_scene("B")
                        # Then patiently ride out the post-battle transition before
                        # retrying. These stalls SELF-HEAL (the overworld becomes
                        # controllable on its own) but the controllable flag flickers
                        # first, so waiting for a STABLE controllable window here lets a
                        # SINGLE recovery ride out the whole stall instead of burning many
                        # rapid derail cycles toward Manual.
                        # Close any STRAY MENU first (an open bag/party menu is not a
                        # script — nothing else in the recovery can close it, and a
                        # navigator driving under an open bag wedges forever; batch
                        # run02 2026-07-22). Bounded B-presses until the overworld.
                        from modules.memory import GameState as _GS
                        from modules.memory import get_game_state as _ggs2

                        for _f in range(900):
                            if _ggs2() is _GS.OVERWORLD:
                                break
                            context.emulator.press_button("B")
                            yield
                            yield
                        yield from wait_until_truly_controllable(timeout_frames=3000)
                        yield from exit_building_after_whiteout()
                        # Cave-stranded derails (a heal/nav plan-failed from INSIDE the
                        # training cave) must physically exit before the retry, or the
                        # segment re-fails identically forever (batch 20260722-182727).
                        # A cheap no-op anywhere else.
                        from modules.story.early_game import _exit_training_cave_if_inside

                        yield from _exit_training_cave_if_inside()
                        settle = 0
                        while settle < 300 and not (
                            game_has_started() and get_game_state() is GameState.OVERWORLD
                        ):
                            settle += 1
                            yield
                    # ⛔ ABORT-SWALLOW TRIAGE (gate #27, 2026-09-13): CORRECT AS WRITTEN.
                    # This settle-loop is INSIDE the derail recovery, AFTER that recovery has deliberately
                    # called `set_story_abort(False)` above it. There is no abort left to swallow — and adding
                    # `reraise_if_aborting` would re-raise the very abort this block exists to recover FROM,
                    # turning a recovered run into a dead one. It `yield`s rather than `pass`es, so the
                    # generator stays alive. ⇒ counted in the baseline; do NOT "fix" it.
                    except Exception:
                        yield
                    continue  # re-run _play(): re-localise from flags + position
                # --- WHITEOUT recovery ---
                # ⭐⭐ `#24-whiteoutloop` — THE BUDGET IS KEYED TO ONE LOCATION, NOT TO THE RUN.
                # This counter had NO reset site while its message said "in a row", so it was a
                # LIFETIME loss quota: 14 of 53 runs (26%) died on it, every one at exactly #41,
                # after whiteouts spread over a median of 13 different towns. Killed runs were
                # winning 86-96% of their battles. ⇒ a fuse on run LENGTH, not a diagnosis.
                # ⛔ See `whiteout_budget`'s docstring for the measurement AND for why
                # `_progress_sig()` — the signal `_derails` uses forty lines up — must NOT be used
                # here: it contains `total_exp`, which grows on the walk back, so it would reset
                # every time and delete the guard.
                _wo_key = self._location_key()
                recoveries, _wo_stop, _wo_moved = whiteout_budget(
                    recoveries, last_whiteout_key, _wo_key
                )
                last_whiteout_key = _wo_key
                self._derails = 0  # reaching a fight = progress; reset the derail budget
                try:
                    from modules import debug_logger

                    debug_logger.event(
                        f"WHITEOUT recovery #{recoveries} at {_wo_key}"
                        + (" (moved on since the last whiteout — budget reset)" if _wo_moved else "")
                    )
                except Exception:
                    pass
                if _wo_stop:
                    # ‼ CLEAR THE LATCH ON THE WAY OUT. `_STORY_ABORT` is a MODULE-GLOBAL in
                    # `early_game`, shared by every mode, probe and driver in the process — and
                    # this `raise` used to leave it SET. Whatever ran next (the endless loop's
                    # next run, another mode) would then abort at its first `_check_abort()` for
                    # no visible reason: a bug that would look like anything except this.
                    # The `derails > 4` exit above does not leak; this one did.
                    set_story_abort(False)
                    raise BotModeError(
                        f"Story: too many whiteout recoveries at one location "
                        f"({recoveries} without the story moving on, at {_wo_key}) — stopping so "
                        f"I don't loop forever. Check the team/route."
                    )
                self._whiteout_pending = False
                set_story_abort(False)
                console.print(
                    "[cyan]Story: recovered from the whiteout — re-orienting at the "
                    "respawn point and resuming.[/]"
                )

                try:
                    yield from wait_for_player_avatar_to_be_controllable()
                    # Respawn lands us INSIDE the Poké Center — step out to the town
                    # so the segmented resume's map checks work (else it backtracks).
                    yield from exit_building_after_whiteout()
                    # SETTLE: right after the exit warp the game is transiently
                    # "not started" / in a non-overworld state — re-running _play now
                    # would misfire its title check into the New-Game intro. Wait for
                    # a stable started+overworld state first.
                    settle = 0
                    while settle < 600 and not (
                        game_has_started() and get_game_state() is GameState.OVERWORLD
                    ):
                        settle += 1
                        yield
                    yield from wait_for_player_avatar_to_be_controllable()
                # ⛔ ABORT-SWALLOW TRIAGE (gate #27, 2026-09-13): AN ABORT CANNOT REACH THE BROAD HANDLER.
                # `except BotModeError: raise` is FIRST, and `StoryAbort` IS a `BotModeError` (KI-67) —
                # Python takes the first matching clause, so an abort re-raises here and never reaches the
                # `except Exception` below. The gate still flags the `try` because its exemption is
                # ALL-QUANTIFIED (every broad handler must re-raise) — the right rule in general, and a
                # false positive in this ORDERED case. ⇒ counted in the baseline; do NOT add a guard.
                except BotModeError:
                    raise
                except Exception:
                    yield
                # loop → re-run the segmented resume from the respawn point

    def _play(self) -> Generator:
        import random

        from modules.memory import get_event_flag, get_event_var
        from modules.map import get_map_data_for_current_position
        from modules.map_data import MapRSE
        from modules.story import detect_live
        from modules.story.config import get_story_config
        from modules.story.intro import run_intro
        from modules.story.early_game import (
            cross_petalburg_woods,
            descend_and_leave_players_house,
            do_petalburg_gym_and_wally_tutorial,
            do_rustboro_gym,
            finish_birch_lab,
            fight_route103_rival,
            go_upstairs_and_set_clock,
            help_birch_and_choose_starter,
            recover_devon_goods,
            return_devon_goods_and_get_pokenav,
            sail_to_dewford,
            deliver_stevens_letter,
            do_dewford_gym,
            sail_to_slateport,
            deliver_devon_goods_to_stern,
            travel_route110_and_fight_rival,
            fight_wally_mauville,
            do_mauville_gym,
            handle_pokenav_match_call_tutorial,
            fight_rustboro_rival,
            return_to_lab_and_get_pokedex,
            train_lead_to_level,
            travel_route104_north_to_rustboro,
            travel_to_petalburg,
            travel_to_petalburg_woods,
            travel_to_route103,
            visit_rivals_house,
            walk_off_truck_and_into_house,
        )

        cfg = get_story_config(context.profile.path)

        def _done(flag: str) -> bool:
            # FAIL LOUDLY on unknown flag names: get_event_flag() silently returns
            # False for a name that isn't in the table, which lets a typo'd/phantom
            # flag gate a segment into an eternal derail loop (Ch9a shipped with
            # "DEFEATED_RIVAL_ROUTE_110", which does not exist — run 5 hit Manual on
            # it). A wrong NAME is a build error, not a game state — surface it.
            from modules.memory import _event_flags

            if flag not in _event_flags:
                raise BotModeError(f"Story: flag name {flag!r} is not in the event-flag table (typo/phantom name).")
            try:
                return bool(get_event_flag(flag))
            except Exception:
                return False

        def _done_var(var: str, at_least: int) -> bool:
            # The `_done` treatment for event VARS, and it needs it MORE: `get_event_var`
            # returns **-1** for a name that isn't in the table, so a typo does not merely
            # read False — it reads a number that compares False against every threshold,
            # forever, with no error. Mt. Pyre is gated on `MT_PYRE_STATE`, so a phantom name
            # here would loop the last segment of the game silently.
            from modules.memory import _event_vars, get_event_var

            if var not in _event_vars:
                raise BotModeError(f"Story: event-var name {var!r} is not in the table (typo/phantom name).")
            try:
                return int(get_event_var(var)) >= at_least
            except Exception:
                return False

        def _cur_map():
            try:
                d = get_map_data_for_current_position()
                return (d.map_group, d.map_number)
            except Exception:
                return None

        def _has_starter() -> bool:
            """True once the player owns a (non-egg) Pokémon — i.e. we are PAST the
            scripted intro. Lets a mid-Segment-1 recovery skip the truck→lab cutscene
            and resume at training rather than trying (and failing) to re-run the
            intro from wherever we respawned."""
            try:
                from modules.pokemon_party import get_party

                return any(not getattr(p, "is_egg", False) for p in get_party())
            except Exception:
                return False

        from modules.modes import BotModeError

        def _guard(label: str, done_check) -> None:
            """SELF-CORRECTION (§SC): after a segment, confirm it actually reached
            its completion signal. If not, the bot silently derailed (a mis-warp,
            a lost battle/blackout, or a skipped beat) — STOP with a diagnostic
            rather than blindly marching on and compounding the error. Re-running
            Story then resumes correctly from the REAL state (§RS)."""
            if done_check():
                return
            try:
                prog = detect_live()
                where = f"{prog.chapter_key}: {prog.chapter_name}"
            except Exception:
                where = "unknown"
            raise BotModeError(
                f"Story self-check: '{label}' didn't reach its completion signal "
                f"(now {where}, map {_cur_map()}). Stopping so I don't derail "
                "further — just run Story again and it resumes correctly from here."
            )

        # RESUME MODEL: the story is linear, so we run each SEGMENT only if its
        # completion signal isn't already set — a fresh game runs everything; a
        # resumed save (or one you hand-played partway) skips what's done and
        # continues from the right place. See design §RS. (Segments self-locate
        # via navigation; the Woods segment also picks its sub-entry by current
        # map so a resume mid-Woods doesn't backtrack to Petalburg.) After each
        # segment a _guard() self-check confirms it truly completed (§SC).
        at_title = get_game_state() is GameState.TITLE_SCREEN or not game_has_started()
        if not at_title:
            # RESUME-FROM-ANYWHERE (user directive 2026-07-23): normalize whatever
            # state we were entered in — a milestone loaded mid-menu, an open dialogue,
            # a live battle, a cutscene — to a stable controllable overworld BEFORE any
            # segment navigates. Without this a menu-saved state (the rocksmash_taught
            # milestone) wedges the first navigator under the open menu.
            from modules.story.early_game import normalize_to_overworld

            yield from normalize_to_overworld()
            try:
                progress = detect_live()
                console.print(
                    f"[bold cyan]Story Mode — resuming[/] (detected {progress.chapter_key}: "
                    f"{progress.chapter_name}); skipping what's already done."
                )
            except Exception:
                pass

        # --- Chapter 0: New Game intro. Title screen only — mid-intro isn't a
        #     resumable point (it must run from the truck). A title screen WITH an
        #     existing save should be loaded via Continue first (TODO §RS). ---
        if at_title:
            console.print(
                f"[bold cyan]Story Mode — new game[/] as [bold]{cfg.character_name}[/] ({cfg.gender})."
            )
            yield from run_intro(cfg.character_name, cfg.gender)

        # --- Segment 1: truck → house → clock → rival → starter → first battle →
        #     lab → train → rival → Pokédex. Gated by the Pokédex flag so a resumed
        #     game past this point skips it. INTERNALLY split into two parts so a
        #     mid-Segment-1 recovery (whiteout/derail during training) resumes
        #     correctly instead of re-running the scripted intro from the truck —
        #     which can't navigate back to the house and loops/derails (user-seen
        #     "stuck at the Oldale Poké Center after respawn"). ---
        if not _done("RECEIVED_POKEDEX_FROM_BIRCH"):
            if not _has_starter():
                # Part A — the scripted intro (truck → clock → rival house →
                # starter → first battle → lab → up to Route 103). This is a linear
                # cutscene run that ONLY works from the truck, so it is NOT a
                # resumable point: run it only while the starter doesn't exist yet.
                yield from walk_off_truck_and_into_house()
                yield from go_upstairs_and_set_clock()
                yield from descend_and_leave_players_house()
                yield from visit_rivals_house()
                yield from help_birch_and_choose_starter(cfg.starter)
                yield from finish_birch_lab(cfg.starter_nickname)
                yield from travel_to_route103()
            else:
                console.print(
                    "[dim]Story: resuming with a starter but no Pokédex — skipping the "
                    "scripted intro, back to training on Route 103.[/]"
                )
            # Part B — train → rival → Pokédex. RESUMABLE from anywhere: each step
            # self-locates (navigate_to_anywhere / _navigate_through_scripts) and is
            # gated by its own flag, so a recovery here picks up at the right place.
            if not _done("DEFEATED_RIVAL_ROUTE103"):
                target_level = random.randint(8, 10)
                console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
                yield from train_lead_to_level(target_level)
                yield from fight_route103_rival()
            else:
                console.print("[dim]Story: rival already beaten — heading back for the Pokédex.[/]")
            yield from return_to_lab_and_get_pokedex()
        else:
            console.print("[dim]Story: already have the Pokédex — skipping the intro chapters.[/]")
        _guard("intro → Pokédex", lambda: _done("RECEIVED_POKEDEX_FROM_BIRCH"))

        # --- Segment 2: Petalburg City — Dad (Norman) + Wally catching tutorial.
        #     Completion signal: Wally's mum leaves Petalburg (HIDE_..._WALLYS_MOM);
        #     the "intended" THANKED_FOR_PLAYING_WITH_WALLY is never set (ML-9). ---
        if not _done("HIDE_PETALBURG_CITY_WALLYS_MOM"):
            yield from travel_to_petalburg()
            yield from do_petalburg_gym_and_wally_tutorial()
        else:
            console.print("[dim]Story: Petalburg / Wally tutorial already done — skipping.[/]")
        _guard("Petalburg / Wally", lambda: _done("HIDE_PETALBURG_CITY_WALLYS_MOM"))

        # --- Segment 3: Route 104 → Petalburg Woods → Rustboro. Enter at the
        #     right sub-step by current map so a mid-Woods resume doesn't backtrack. ---
        rustboro = MapRSE.RUSTBORO_CITY.value
        woods = MapRSE.PETALBURG_WOODS.value
        route116 = MapRSE.ROUTE116.value
        rusturf = MapRSE.RUSTURF_TUNNEL.value

        def _in_rustboro() -> bool:
            # Anywhere in the Rustboro AREA means the Woods crossing is already done:
            # Rustboro city, ANY Rustboro building (map group 11 — gym/Devon/PC/mart/…),
            # Route 116 (the pre-gym catching/training grass — only reachable THROUGH
            # Rustboro), or Rusturf Tunnel (the Devon errand). Route 116 was the miss —
            # a save mid-catching there re-ran the Woods travel and derailed.
            cur = _cur_map()
            if cur is None:
                return _done("BADGE01_GET")
            return (
                cur == rustboro
                or cur[0] == 11
                or cur == route116
                or cur == rusturf
                or _done("BADGE01_GET")
            )

        if _in_rustboro():
            console.print("[dim]Story: already in Rustboro — skipping the Woods travel.[/]")
        elif _cur_map() == woods:
            console.print("[cyan]Story: resuming inside Petalburg Woods — finishing the crossing.[/]")
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        else:
            yield from travel_to_petalburg_woods()
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        _guard("Route 104 → Rustboro", _in_rustboro)

        # --- Segment 4: Gym 1 — Roxanne (Stone Badge). Train the team to a sensible
        #     level FIRST (threshold ≈ boss ace + margin, plus a retrain if we've
        #     already lost here — user directive 2026-07-21). ---
        if not _done("BADGE01_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import RUSTBORO_TRAINING_GRASS, catch_starter_team

            roxanne_fight = {
                "keys": [MapRSE.RUSTBORO_CITY_GYM.value, MapRSE.RUSTBORO_CITY.value],
                "band": (13, 17),  # user: team between Lv 13-17 before Roxanne
                "ace_types": ("Rock",), "ace_level": 15,  # Nosepass L15
                "grass": RUSTBORO_TRAINING_GRASS,
                "heal": PokemonCenter.RustboroCity,
            }
            # Build an organic team (catch new species) BEFORE training + the gym.
            yield from catch_starter_team(self._catch_team_target)
            yield from self._prepare_for_fight(roxanne_fight)
            yield from do_rustboro_gym()
        else:
            console.print("[dim]Story: Stone Badge already earned — Gym 1 skipped.[/]")
        _guard("Gym 1 (Roxanne)", lambda: _done("BADGE01_GET"))

        # --- Segment 5a: Devon Goods errand — chase the thief to Rusturf Tunnel and
        #     recover the goods (+ free Peeko). Completion: RECOVERED_DEVON_GOODS.
        #     (The return leg — Devon Corp president → PokéNav — and the Rustboro
        #     rival are the next build; see design §Ch5.) ---
        if not _done("RECOVERED_DEVON_GOODS"):
            yield from recover_devon_goods()
        else:
            console.print("[dim]Story: Devon Goods already recovered — skipping.[/]")
        _guard("Devon Goods (Rusturf Tunnel)", lambda: _done("RECOVERED_DEVON_GOODS"))

        # --- Segment 5b: return the goods to Mr. Stone → PokéNav + Letter → clear the
        #     forced PokéNav Match-Call tutorial → train → Rustboro rival.
        #     Completion signals: RECEIVED_POKENAV, then DEFEATED_RIVAL_RUSTBORO. ---
        if not _done("RECEIVED_POKENAV"):
            yield from return_devon_goods_and_get_pokenav()
        else:
            console.print("[dim]Story: PokéNav already received — skipping the Devon Corp errand.[/]")
        _guard("Devon Corp → PokéNav", lambda: _done("RECEIVED_POKENAV"))

        # Clear the forced PokéNav/Match-Call tutorial (Rustboro Scientist, fired from the
        # map ON_FRAME table while VAR_RUSTBORO_CITY_STATE==6). FAITHFUL path: actually call
        # Mr. Stone through the PokéNav app; falls back to a state-write to vanilla's exact
        # end-state when the renderer is off (headless) or the nav stalls
        # (handle_pokenav_match_call_tutorial). Completing it sets VAR_RUSTBORO_CITY_STATE=7,
        # which also arms the rival trigger.
        if get_event_var("RUSTBORO_CITY_STATE") < 7:
            yield from handle_pokenav_match_call_tutorial()

        # --- Segment 5c: Rustboro rival (south exit, y=53; gated on VAR_RUSTBORO_CITY_STATE==7,
        #     which the tutorial-clear set). This rival is TYPE-COUNTERED: a Mudkip start makes
        #     it lead a grass Grovyle vs our 4×-weak Marshtomp, so we (1) TRAIN to a rival band,
        #     (2) pick a MATCHUP-based lead (not lead-strongest), and (3) cap attempts so a
        #     thin team that can't win stops cleanly instead of looping forever. ---
        def _rustboro_rival_resolved() -> bool:
            # VANILLA TRUTH (decomp + live probe 2026-07-22): the RivalTrigger row
            # fires only at VAR_RUSTBORO_CITY_STATE==7 and the MEETING sets it to 8 —
            # win or LOSE there is no rematch (her talk script is just the Briney
            # hint), and progression does NOT require the win. Two batch runs hit
            # honest-Manual retry loops on a met-and-lost state before this was
            # understood. Resolved = beaten, or met-and-spent.
            if _done("DEFEATED_RIVAL_RUSTBORO"):
                return True
            try:
                from modules.memory import get_event_var

                return _done("MET_RIVAL_RUSTBORO") and get_event_var("RUSTBORO_CITY_STATE") >= 8
            except Exception:
                return False

        if not _rustboro_rival_resolved():
            # PER-RUN budget — `reset_per_run_state()` zeroes this at every run boundary.
            # It used to be a `getattr(self, ..., 0) + 1` on state that was only ever
            # initialised in `__init__`, which is why an endless batch went permanently
            # over cap on run 4 and never fought this rival again.
            self._rival_attempts += 1
            if self._rival_attempts > self.RIVAL_MAX_ATTEMPTS:
                context.message = (
                    f"Story: couldn't beat the Rustboro rival in {self.RIVAL_MAX_ATTEMPTS} tries "
                    "(likely underleveled / bad matchup) — handing to manual so you can level up."
                )
                console.print(f"[bold yellow]{context.message}")
                context.set_manual_mode()
                return
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                RUSTBORO_TRAINING_GRASS,
                _lead_best_matchup,
                train_team,
                heal_in_pokemon_center,
            )

            rival_fight = {
                "keys": [MapRSE.RUSTBORO_CITY.value],
                "band": (16, 19),  # rival ace ≈ Lv15-16; small margin (escalates on losses)
                "grass": RUSTBORO_TRAINING_GRASS,
                "heal": PokemonCenter.RustboroCity,
            }
            # (1) LEVEL FLOOR (user directive 2026-07-21): make sure EVERY party mon is at
            #     least Lv 10 before the rival — a thin L6-8 bench gets swept and whites us
            #     out. The floor escalates on retries so each attempt fields a stronger team.
            level_floor = 10 + 2 * (self._rival_attempts - 1)
            console.print(f"[cyan]Story: leveling the whole team to ≥ Lv {level_floor} before the rival…[/]")
            yield from train_team(level_floor, scope="whole",
                                  grass=RUSTBORO_TRAINING_GRASS, heal_center=PokemonCenter.RustboroCity)
            # (2) Ready the primary/near-band battlers (organic band training + loss escalation).
            yield from self._prepare_for_fight(rival_fight)
            # (3) Mudkip start -> rival leads a grass Grovyle: lead the mon that best resists Grass
            #     (NOT our 4×-weak Marshtomp). Taillow/Flying both resists Grass AND hits it 2×.
            yield from _lead_best_matchup(["Grass"])
            # (4) SAFE HEAL right before the fight (user directive) — enter at full HP.
            yield from heal_in_pokemon_center(PokemonCenter.RustboroCity)
            # (5) Fight. A loss whites out -> StoryMode recovery -> we re-enter here (attempt+1,
            #     higher floor) until RIVAL_MAX_ATTEMPTS, then stop cleanly. The rival re-engages
            #     correctly on retries now (fight_rustboro_rival no longer keys off the MET flag).
            yield from fight_rustboro_rival()
        else:
            console.print("[dim]Story: Rustboro rival already resolved (beaten, or met-and-lost — vanilla offers no rematch) — skipping.[/]")
        _guard("Rustboro rival (resolved)", _rustboro_rival_resolved)

        # --- Segment 6: sail to Dewford (Chapter 6). Rustboro → south onto Route 104 →
        #     back through Petalburg Woods (Route 104 is river-split) → south beach →
        #     Mr. Briney's cottage → talk (first sail = YES/NO) → sail cutscene → Dewford.
        #     sail_to_dewford is idempotent + keyed off the LIVE map, so a resume from
        #     anywhere along the route picks up mid-leg. Once the Dewford-arc flags
        #     (DELIVERED_STEVEN_LETTER / BADGE02) exist they gate this out for good. ---
        pre_sail_maps = (
            MapRSE.RUSTBORO_CITY.value,
            MapRSE.ROUTE104.value,
            MapRSE.PETALBURG_WOODS.value,
            MapRSE.ROUTE104_MR_BRINEYS_HOUSE.value,
        )
        if not _done("DELIVERED_STEVEN_LETTER") and not _done("BADGE02_GET"):
            # WHITELIST the pre-sail maps: "not in Dewford" is WRONG as a gate — a resume
            # from Route 106 / Granite Cave / the gym is already on the Dewford side, and
            # running the sail leg there marches off toward a cottage that can't be
            # reached (live-hit 2026-07-22: a Granite Cave derail re-entered the sail and
            # spun into Manual). Off-whitelist maps skip straight to the Dewford segments.
            if _cur_map() in pre_sail_maps:
                yield from sail_to_dewford()
                _guard("Sail to Dewford (Ch6)", lambda: _cur_map() == MapRSE.DEWFORD_TOWN.value)
            elif _cur_map() != MapRSE.DEWFORD_TOWN.value:
                console.print("[dim]Story: already on the Dewford side — sail leg skipped.[/]")

        # --- Segment 7a: Steven's Letter (Granite Cave, TM47). The story reason we came
        #     to Dewford — and Briney waits for it before offering the Slateport sail. ---
        if not _done("DELIVERED_STEVEN_LETTER"):
            yield from deliver_stevens_letter()
        else:
            console.print("[dim]Story: Steven's Letter already delivered — skipping Granite Cave.[/]")
        _guard("Steven's Letter (Granite Cave)", lambda: _done("DELIVERED_STEVEN_LETTER"))

        # --- Segment 7b: Gym 2 — Brawly (Knuckle Badge). Heal + Fighting-resistant lead
        #     (Taillow-class); floor-band only — Dewford has NO reachable training grass
        #     before Surf (Route 106 is surf-only, Granite Cave wilds are L6-10), so the
        #     natural post-rival team (≥L16) skips proactive grinding and the cave spot is
        #     the (slow but bounded) loss-escalation fallback. See design §Ch7. ---
        if not _done("BADGE02_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                GRANITE_CAVE_TRAINING_SPOT,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            brawly_fight = {
                "keys": [MapRSE.DEWFORD_TOWN_GYM.value, MapRSE.DEWFORD_TOWN.value],
                "band": (14, 16),
                "ace_types": ("Fighting",), "ace_level": 19,  # Makuhita L19
                "grass": GRANITE_CAVE_TRAINING_SPOT,
                "heal": PokemonCenter.DewfordTown,
            }
            yield from self._prepare_for_fight(brawly_fight)
            # Training can END at the in-cave spin tile — thread the cave mouth first
            # or the direct heal plan-fails cross-warp ("not on connected maps") and
            # derail-loops to Manual (batch 20260722-182727: 3 of 5 runs died here).
            from modules.story.early_game import _exit_training_cave_if_inside

            yield from _exit_training_cave_if_inside()
            yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)
            yield from _lead_best_matchup(["Fighting"])
            yield from do_dewford_gym()
        else:
            console.print("[dim]Story: Knuckle Badge already earned — Gym 2 skipped.[/]")
        _guard("Gym 2 (Brawly)", lambda: _done("BADGE02_GET"))

        # --- Segment 8a: sail Dewford → Slateport (Briney at the dock; Route 109 beach
        #     gauntlet; ends healed at the Slateport PC). Gated on being on the DEWFORD
        #     side (whitelist — see the Segment-6 lesson); a Slateport-side resume skips. ---
        dewford_side = (
            MapRSE.DEWFORD_TOWN.value,
            MapRSE.ROUTE106.value,
            MapRSE.GRANITE_CAVE_1F.value,
            MapRSE.GRANITE_CAVE_B1F.value,
            MapRSE.GRANITE_CAVE_B2F.value,
            MapRSE.GRANITE_CAVE_STEVENS_ROOM.value,
            MapRSE.ROUTE109.value,
        )
        cur = _cur_map()
        on_dewford_side = cur in dewford_side or (cur is not None and cur[0] == 3)  # group 3 = Dewford interiors
        if cur != MapRSE.SLATEPORT_CITY.value:
            if on_dewford_side:
                yield from sail_to_slateport()
                _guard("Sail to Slateport (Ch8a)", lambda: _cur_map() == MapRSE.SLATEPORT_CITY.value)
            else:
                console.print("[dim]Story: not on the Dewford side — Slateport sail skipped.[/]")

        # --- Segment 8b: Devon Goods → Capt. Stern (Oceanic Museum). KI-11 RESOLVED
        #     (2026-07-22, walkthrough + decomp): the museum entrance is grunt-sealed until
        #     you visit Stern's Shipyard and talk to Dock (sets FLAG_HIDE_SLATEPORT_CITY_
        #     TEAM_AQUA) — `deliver_devon_goods_to_stern` now does that first. Two
        #     un-fleeable grunt battles inside the scene (attack-through strategy); the
        #     scene heals the party and removes the Route 110 blockade for Ch9. ---
        museum_maps = (
            MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F.value,
            MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F.value,
        )
        # Also (re-)enter the segment when RESUMING INSIDE the museum with the flag
        # already set (e.g. the stern_done checkpoint is captured on 2F the moment the
        # flag lands, before the exit legs) — the function then skips straight to its
        # museum-exit legs. Without this, a city-target heal from inside the museum
        # plan-fails ("not on connected maps") and derails to Manual (live-hit ch9_run1).
        if not _done("DELIVERED_DEVON_GOODS") or _cur_map() in museum_maps:
            yield from deliver_devon_goods_to_stern()
        else:
            console.print("[dim]Story: Devon Goods already delivered — museum skipped.[/]")
        _guard("Devon Goods → Capt. Stern (Ch8b)", lambda: _done("DELIVERED_DEVON_GOODS"))

        # --- Segment 9a: the Route 110 rival (mandatory choke-point; §Ch9). Heal + a
        #     type-aware lead first: the rival's ACE counters OUR starter (Mudkip start →
        #     their Grovyle/Grass; Torchic → Marshtomp/Water; Treecko → Combusken/Fire). ---
        # NOTE (2026-07-22): the rival's completion signal is VAR_ROUTE110_STATE >= 1 —
        # vanilla sets NO named flag here; "DEFEATED_RIVAL_ROUTE_110" was a phantom name
        # that silently read False forever and derail-looped this segment (run 5).
        from modules.story.early_game import route110_rival_beaten

        if not route110_rival_beaten():
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            # ‼ THE RIVAL'S ACE DEPENDS ON THE PLAYER'S STARTER — decomp-verified 2026-08-07
            # from `src/data/trainer_parties.h` (`sParty_MayRoute110{Treecko,Torchic,Mudkip}`;
            # the Brendan parties are identical in species and level):
            #     player Treecko -> Wingull 18, Lombre 18, COMBUSKEN 20   (Fighting/Fire)
            #     player Torchic -> Lombre 18, Slugma 18, MARSHTOMP 20    (Ground/Water)
            #     player Mudkip  -> Wingull 18, Slugma 18, GROVYLE 20     (Grass)
            # Type pairs re-checked against our own `modules/data/generated/pokedex_data.json`.
            #
            # ‼ THE OLD CODE NAMED ONLY THE PRIMARY TYPE ("Water" / "Fire" / "Grass"). That is
            # right as far as it goes but incomplete, and effectiveness against a dual-type is
            # the PRODUCT over BOTH types — the same reason Winona's cfg carries
            # ("Dragon", "Flying") rather than just "Dragon". Naming the pair is what lets the
            # boss machinery judge an answer correctly.
            ace_types = ("Grass",)
            try:
                from modules.pokemon_party import get_party as _gp

                names = " ".join(p.species.name for p in _gp() if p is not None)
                if any(s in names for s in ("Torchic", "Combusken", "Blaziken")):
                    ace_types = ("Ground", "Water")      # rival fields Marshtomp
                elif any(s in names for s in ("Treecko", "Grovyle", "Sceptile")):
                    ace_types = ("Fighting", "Fire")     # rival fields Combusken
            except Exception:
                pass

            # ‼ `#24-whiteoutloop` PART 1 (2026-08-07). This segment had NO `_prepare_for_fight`
            # cfg at all, so none of the boss machinery ran here — no sufficiency gate, no
            # plateau detection, no counter escalation, no give-up. ROUTE110 is the **#1 or #2
            # defeat map in 4 of 4 measured batches** (91-120 defeats each) and, with
            # LAVARIDGE_GYM, accounts for 48% of all defeats (1,079 / 2,236). KI-26 has flagged
            # "no prep and no attempt cap" here since 2026-07-27; this is that fix.
            #
            # ‼ NO `grass` KEY ON PURPOSE. `_prepare_for_fight` explicitly supports a grass-less
            # cfg ("No training grass exists for this boss … the re-attempt itself is the only
            # trainer available"), and inventing a Route 110 training tile would be writing a
            # game fact from recall — exactly what KI-44 punished. Everything that matters here
            # (the plateau detector and the escalation) needs only `keys`/`band`/`ace_*`.
            rival110_fight = {
                "keys": [MapRSE.ROUTE110.value],
                "band": (18, 20),  # Wingull/Lombre/Slugma 18, evolved starter 20
                "ace_types": ace_types, "ace_level": 20,
                "heal": PokemonCenter.SlateportCity,
            }
            yield from self._prepare_for_fight(rival110_fight)
            yield from heal_in_pokemon_center(PokemonCenter.SlateportCity)
            yield from _lead_best_matchup(list(ace_types), hunted_pids=self._hunted_counter_pids)
            yield from travel_route110_and_fight_rival()
        else:
            console.print("[dim]Story: Route 110 rival already beaten — skipping.[/]")
        _guard("Route 110 rival (Ch9a)", route110_rival_beaten)

        # --- Segment 9b: Mauville — Wally unblocks the gym door. ---
        if not _done("DEFEATED_WALLY_MAUVILLE"):
            yield from fight_wally_mauville()
        else:
            console.print("[dim]Story: Wally already beaten at Mauville — skipping.[/]")
        _guard("Wally at Mauville (Ch9b)", lambda: _done("DEFEATED_WALLY_MAUVILLE"))

        # --- Segment 9c: Gym 3 — Wattson (Dynamo Badge). PREP FIRST (KI-13: the maze
        #     solver was validated in run 10 but the unprepped team lost 8 straight
        #     challenges): band-train at Route 110's north grass, then an Electric-
        #     resistant lead (Marshtomp/Ground is immune), then a safe heal. The
        #     switch maze itself is solved by the live-grid solver. ---
        if not _done("BADGE03_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                ROUTE117_TRAINING_GRASS,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            wattson_fight = {
                "keys": [MapRSE.MAUVILLE_CITY_GYM.value, MapRSE.MAUVILLE_CITY.value],
                "band": (20, 24),  # Wattson: Voltorb 20 / Electrike 20 / Magneton 22 / Manectric 24
                "ace_types": ("Electric",), "ace_level": 24,  # Manectric L24
                "grass": ROUTE117_TRAINING_GRASS,
                "heal": PokemonCenter.MauvilleCity,
            }
            yield from self._prepare_for_fight(wattson_fight)
            yield from _lead_best_matchup(["Electric"], hunted_pids=self._hunted_counter_pids)
            yield from heal_in_pokemon_center(PokemonCenter.MauvilleCity)
            yield from do_mauville_gym()
        else:
            console.print("[dim]Story: Dynamo Badge already earned — Gym 3 skipped.[/]")
        _guard("Gym 3 (Wattson)", lambda: _done("BADGE03_GET"))

        # --- Segment 10a: HM06 Rock Smash (Mauville SE house; §Ch10). Gated only on
        #     the received flag; field use needs BADGE03, which Segment 9c earned. ---
        if not _done("RECEIVED_HM_ROCK_SMASH"):
            from modules.story.early_game import get_rock_smash_hm

            yield from get_rock_smash_hm()
        else:
            console.print("[dim]Story: HM06 Rock Smash already received — skipping.[/]")
        _guard("HM06 Rock Smash (Ch10a)", lambda: _done("RECEIVED_HM_ROCK_SMASH"))

        # --- Segment 10b: teach Rock Smash to a VALIDATED learner (user directive
        #     2026-07-23): pick the highest-level party mon that can actually learn it
        #     (the party menu shows an incompatible mon as NOT ABLE and refuses the
        #     selection — the old highest-level pick loops there). If nobody in the
        #     party qualifies, ensure_hm_learner hunts an accessible learner species
        #     (data-driven from the ROM's encounter tables + TM/HM learnsets) and
        #     catches one first. Seed of the HM-slave logic (#24-hm-slaves). ---
        def _party_knows_rock_smash() -> bool:
            try:
                from modules.pokemon_party import get_party as _gp

                return any(
                    learned is not None and learned.move.name == "Rock Smash"
                    for mon in _gp()
                    if mon is not None and not mon.is_egg
                    for learned in mon.moves
                )
            except Exception:
                return False

        if not _party_knows_rock_smash():
            from modules.items import get_item_by_name
            from modules.map_data import PokemonCenter
            from modules.pokemon_party import get_party
            from modules.story.early_game import (
                ensure_hm_learner_making_room,
                land_hm_learner_slot,
                teach_hm_move,
            )

            _hm06 = get_item_by_name("HM06")
            # ‼ KI-63 WIRING: a FULL PARTY used to end the run here — this call site had no error
            # handling, so the raise went straight to the mode handler and derailed to Manual.
            # Centres are the ones this era already heals at, nearest-first.
            # ⭐ `#24-hm07funnel` — PRE-PICK a learner that cannot also carry HM07.
            # MEASURED over all 412 species: Waterfall's and Dive's pools are strict SUBSETS of
            # Surf's (74 and 76 of 101, with ZERO Surf-incapable members), so the highest-level Surf
            # learner is ALWAYS also the Waterfall candidate — and `hm_learner_slot` hands it every
            # HM it is offered. On a Mudkip line that mon is the party's ONLY Waterfall carrier and
            # must hold Surf+Dive+Waterfall = 3 of 4 slots; adding both land HMs makes five HMs for
            # four slots and Waterfall, acquired last in §Ch21, is the one left out. HMs cannot be
            # forgotten in Gen 3, so the ORIGINAL teach is the only moment this is preventable.
            # ‼ REACHABILITY-IDENTICAL, and that is the safety argument: `ensure_hm_learner` opens
            # with `slot = hm_learner_slot(item); if slot is not None: return slot` — no yields, no
            # side effects — and `ensure_hm_learner_making_room` delegates straight to it. So
            # `_pref is None` ⟺ `hm_learner_slot` is None ⟺ the room-making path was genuinely
            # needed, and it is then called untouched. Only WHICH slot changes.
            _pref = land_hm_learner_slot(_hm06)
            if _pref is None:
                _slot = yield from ensure_hm_learner_making_room(
                    _hm06, (PokemonCenter.MauvilleCity, PokemonCenter.SlateportCity)
                )
            else:
                _slot = _pref
            console.print(
                f"[cyan]Story: teaching Rock Smash to {get_party()[_slot].species.name} "
                f"(slot {_slot})...[/]"
            )
            yield from teach_hm_move(_hm06, _slot)
        else:
            console.print("[dim]Story: someone already knows Rock Smash — teach skipped.[/]")
        _guard("Teach Rock Smash (Ch10b)", _party_knows_rock_smash)

        # --- Segment 10c: Route 111 south (smash the rocks) → Fiery Path → Route 113
        #     → Fallarbor, ending healed at its PC (§Ch10 route spec). ---
        from modules.story.early_game import travel_to_fallarbor

        # ORIGIN-side whitelist (the Segment-6 travel-gate lesson): run the travel only
        # when we're actually on the PRE-Fallarbor side — a resume from R114/Meteor
        # Falls or beyond must NOT backtrack (run 2026-07-22 overnight tried to walk
        # Route 114 → Route 111 and plan-failed to Manual).
        pre_fallarbor = (
            MapRSE.MAUVILLE_CITY.value,
            MapRSE.MAUVILLE_CITY_GYM.value,
            MapRSE.MAUVILLE_CITY_POKEMON_CENTER_1F.value,
            MapRSE.MAUVILLE_CITY_HOUSE1.value,
            MapRSE.ROUTE110.value,
            MapRSE.ROUTE111.value,
            MapRSE.ROUTE112.value,
            MapRSE.FIERY_PATH.value,
            MapRSE.ROUTE113.value,
        )
        # ALSO progress-gated: the corridor maps (R111/R112/Fiery/R113) are shared by
        # the LATER Fallarbor→Cable-Car return trip, so a mid-return derail would
        # re-trigger this travel on maps alone (seen 2026-07-22 overnight: it then
        # "shortcut" into the Go-Goggles-gated desert and plan-failed). Once Ch11a's
        # flag exists, the Fallarbor trip already happened — never travel again.
        if _cur_map() in pre_fallarbor and not _done("HIDE_ROUTE_112_TEAM_MAGMA"):
            yield from travel_to_fallarbor()
        else:
            console.print("[dim]Story: Fallarbor travel not applicable from here — skipped.[/]")
        _guard(
            "Fallarbor travel resolved (Ch10c)",
            lambda: _cur_map() not in pre_fallarbor or _done("HIDE_ROUTE_112_TEAM_MAGMA"),
        )

        # --- Segment 11a: the Meteor Falls Magma cutscene (unblocks the Cable Car). ---
        from modules.story.early_game import do_meteor_falls_scene

        if not _done("HIDE_ROUTE_112_TEAM_MAGMA"):
            yield from do_meteor_falls_scene()
        else:
            console.print("[dim]Story: Meteor Falls scene already done — skipping.[/]")
        _guard("Meteor Falls scene (Ch11a)", lambda: _done("HIDE_ROUTE_112_TEAM_MAGMA"))

        # --- Segment 11b: Cable Car → Mt. Chimney Magma chain (Maxie) + meteorite.
        #     Prep: heal + water-favoring lead (Camerupt ace is 4× to Water). ---
        from modules.story.early_game import do_jagged_descent, do_mt_chimney

        if not _done("DEFEATED_EVIL_TEAM_MT_CHIMNEY"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            yield from heal_in_pokemon_center(PokemonCenter.FallarborTown)
            yield from _lead_best_matchup(["Fire", "Poison"])
            yield from do_mt_chimney()
        else:
            console.print("[dim]Story: Mt. Chimney already cleared — skipping.[/]")
        _guard("Mt. Chimney (Ch11b)", lambda: _done("DEFEATED_EVIL_TEAM_MT_CHIMNEY"))

        # --- Segment 11c: Jagged Pass down to Lavaridge (heal = arrival). ---
        # Run whenever we're not yet at/past Lavaridge: do_jagged_descent now handles
        # BOTH origins — descend when on the mountain, and re-ride the cable car up
        # first when a mid-descent whiteout stranded us below (user's 2026-07-23 run).
        # ‼ The guard checks we actually REACHED Lavaridge (or already earned the Heat
        # Badge) — the old "off the mountain" guard falsely PASSED at the Fallarbor
        # respawn, so Flannery then ran from the wrong town and derailed.
        _at_or_past_lavaridge = lambda: _cur_map() == MapRSE.LAVARIDGE_TOWN.value or _done("BADGE04_GET")
        if not _at_or_past_lavaridge():
            yield from do_jagged_descent()
        else:
            console.print("[dim]Story: already at Lavaridge — Jagged descent skipped.[/]")
        _guard("Jagged descent resolved (Ch11c)", _at_or_past_lavaridge)

        # --- Segment 11d: Gym 4 — Flannery (Heat Badge). The trapdoor maze is solved
        #     from the ROM's map data (holes / geysers / jump-south ledges — see
        #     do_lavaridge_gym), so no hole-guessing remains.
        #     NO pre-grind here, deliberately: a two-way pathability sweep from
        #     Lavaridge (tools/story-dev/jaggedgrass_probe.py) found NO usable training
        #     grass — Jagged Pass cannot be re-entered from the town (one-way ledges)
        #     and Route 112's lower grass has no return path. Teams reach Lavaridge at
        #     L28-29 and Flannery's ace is L29, so we prep the cheap way: a WATER lead
        #     (all four of her mons are 2x to Water) and a full heal. If this proves
        #     thin in batches, the fix is a swept Lavaridge-area tile (#24-trainmap),
        #     not a blind grind target. ---
        if not _done("BADGE04_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                _lead_best_matchup,
                do_lavaridge_gym,
                heal_in_pokemon_center,
            )

            # ‼ `#24-whiteoutloop` PART 1 (2026-08-07). This segment had NO
            # `_prepare_for_fight` cfg, so none of the boss machinery ran here — no
            # sufficiency gate, no plateau detection, no counter escalation, no give-up.
            # LAVARIDGE_TOWN_GYM_1F is a **top-4 defeat map in 4 of 4 measured batches**
            # (87/57/53/73) and the single worst runaway observed anywhere: **17 consecutive
            # losses with a perfectly constant KO series, `kos=[3]*17`**.
            #
            # ‼ NO `grass` KEY — and that is not a gap, it is the documented state of this
            # town (see the header above): a two-way pathability sweep
            # (`tools/story-dev/jaggedgrass_probe.py`) found NO usable training grass, because
            # Jagged Pass cannot be re-entered from Lavaridge and Route 112's lower grass has
            # no return path. `_prepare_for_fight` supports exactly this shape — *"No training
            # grass exists for this boss (e.g. Lavaridge). The re-attempt itself is the only
            # trainer available"* — so the cfg buys the DETECTION and the ESCALATION without
            # inventing a tile. Adding a swept Lavaridge tile is still `#24-trainmap`.
            #
            # Team decomp-verified 2026-08-07 (`src/data/trainer_parties.h`, `sParty_Flannery1`):
            # Numel 24, Slugma 24, Camerupt 26, **Torkoal 29** (ace, holds a White Herb).
            # Torkoal is pure Fire — checked against our own `pokedex_data.json`, not recalled.
            flannery_fight = {
                "keys": [MapRSE.LAVARIDGE_TOWN_GYM_1F.value, MapRSE.LAVARIDGE_TOWN.value],
                "band": (24, 29),  # Numel 24 / Slugma 24 / Camerupt 26 / Torkoal 29
                "ace_types": ("Fire",), "ace_level": 29,  # Torkoal L29
                "heal": PokemonCenter.LavaridgeTown,
            }
            yield from self._prepare_for_fight(flannery_fight)
            yield from _lead_best_matchup(["Fire"], hunted_pids=self._hunted_counter_pids)
            yield from heal_in_pokemon_center(PokemonCenter.LavaridgeTown)
            yield from do_lavaridge_gym()
        else:
            console.print("[dim]Story: Heat Badge already earned — Gym 4 skipped.[/]")
        _guard("Gym 4 (Flannery)", lambda: _done("BADGE04_GET"))

        # --- Segment 12a: the long overland backtrack Lavaridge → Petalburg (§Ch12
        #     build spec; route static-probed 2026-07-24 — direct via Route 111 south,
        #     the desert is never on the path; the Rusturf wall opens via the Wanda
        #     quest's two Rock Smash rocks). ---
        from modules.story.early_game import do_petalburg_gym, travel_lavaridge_to_petalburg

        _at_petalburg = lambda: _cur_map() in (
            MapRSE.PETALBURG_CITY.value,
            MapRSE.PETALBURG_CITY_GYM.value,
            MapRSE.PETALBURG_CITY_POKEMON_CENTER_1F.value,
            MapRSE.PETALBURG_CITY_WALLYS_HOUSE.value,
            MapRSE.PETALBURG_CITY_MART.value,
        )
        if not _at_petalburg() and not _done("RECEIVED_HM_SURF"):
            yield from travel_lavaridge_to_petalburg()
        else:
            console.print("[dim]Story: already Petalburg-side (or Surf in hand) — travel skipped.[/]")
        _guard("Travel to Petalburg (Ch12a)", lambda: _at_petalburg() or _done("RECEIVED_HM_SURF"))

        # --- Segment 12b: Gym 5 — Norman (Balance Badge) + the HM03 Surf handoff.
        #     Slaking L31 (TRUANT) is the ace; attack-through + a Normal-answering
        #     lead. Route 102 grass is L3-4 fodder, so the sufficiency gate /
        #     boss-training telemetry owns the prep decision. ---
        if not _done("RECEIVED_HM_SURF"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                PETALBURG_TRAINING_GRASS,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            norman_fight = {
                "keys": [MapRSE.PETALBURG_CITY_GYM.value, MapRSE.PETALBURG_CITY.value],
                "band": (27, 31),  # Norman: Spinda 27 / Vigoroth 27 / Linoone 29 / Slaking 31
                "ace_types": ("Normal",), "ace_level": 31,  # Slaking L31 (Truant)
                "grass": PETALBURG_TRAINING_GRASS,
                "heal": PokemonCenter.PetalburgCity,
            }
            # Prep/heal only when OUTSIDE the gym: a mid-gym derail resume must walk
            # straight back up the (still-open) doors, not leave for the PC —
            # ch12_run3 looped to Manual healing from inside (pre the warp-aware
            # heal fix; the gate also spares pointless PC round-trips).
            if _cur_map() != MapRSE.PETALBURG_CITY_GYM.value:
                yield from self._prepare_for_fight(norman_fight)
                yield from _lead_best_matchup(["Normal"], hunted_pids=self._hunted_counter_pids)
                yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)
            yield from do_petalburg_gym()
        else:
            console.print("[dim]Story: Surf already received — Gym 5 skipped.[/]")
        _guard("Gym 5 + Surf handoff (Ch12b)", lambda: _done("RECEIVED_HM_SURF"))

        # --- Segment 12c: teach Surf (Marshtomp is the natural carrier); the whole
        #     Ch13+ water arc (Route 118, Weather Institute, Fortree) needs it. ---
        def _party_knows_surf() -> bool:
            try:
                from modules.pokemon_party import get_party as _gp

                return any(
                    learned is not None and learned.move.name == "Surf"
                    for mon in _gp()
                    if mon is not None and not mon.is_egg
                    for learned in mon.moves
                )
            except Exception:
                return False

        if not _party_knows_surf():
            from modules.items import get_item_by_name
            from modules.map_data import PokemonCenter
            from modules.story.early_game import ensure_hm_learner_making_room, teach_hm_move

            _hm03 = get_item_by_name("HM03")
            # ‼ KI-63 WIRING — and this is the one the measurements care about: "nobody can learn
            # Surf" is the recorded top non-finish cause, and a full party turned it from a costly
            # hunt into a hard derail. Centres are this era's own, nearest-first.
            _slot = yield from ensure_hm_learner_making_room(
                _hm03,
                (PokemonCenter.PetalburgCity, PokemonCenter.LavaridgeTown, PokemonCenter.FallarborTown),
            )
            yield from teach_hm_move(_hm03, _slot)
        else:
            console.print("[dim]Story: someone already knows Surf — teach skipped.[/]")
        _guard("Teach Surf (Ch12c)", _party_knows_surf)

        # --- Segment 12d: USER RULING 17 (2026-09-26) — Mom's AMULET COIN (badge 5), held by a battler.
        #     WHY: 3 of 3 organic League arrivals were refused on money that day; the coin doubles every
        #     later trainer prize. `modules/story/amulet_coin.py` has the decomp mechanics.
        # ⛔ FAILS SOFT — a coin is money, not a run: every coin problem is a named `AMULET_COIN` event.
        #   Only the END POSITION is guarded, because 13a's walk starts from Petalburg.
        # ⛔ GATED TO THE PETALBURG ERA (`not BADGE06` ∧ in Petalburg) — a post-Fortree re-entry must never
        #   walk back south; that is KI-97's shape.
        from modules.story.amulet_coin import run_ch12d

        _ac_report: dict = {}
        yield from run_ch12d(_ac_report, _at_petalburg, badge06=_done("BADGE06_GET"))
        if _ac_report.get("ran"):
            _guard("Amulet Coin errand ends in Petalburg (Ch12d)", _at_petalburg)

        # --- Segment 13a: the Surf arc — Mauville → Route 118 (Surf) → Route 119 →
        #     Weather Institute → rival (HM02 Fly) → Fortree (§Ch13 spec, flags
        #     audited; ⚠ SKELETON built 2026-07-24 overnight — the Surf crossing and
        #     interior tiles are first-run-validate leads, expect iteration). ---
        # ⛔⛔ KI-97 — GATE THE WHOLE SEGMENT ON ITS OWN COMPLETION FLAG. Without this, every
        # `_play()` re-entry from a POST-Fortree position (a Sootopolis/Mossdeep whiteout or
        # derail — i.e. all of §Ch21-23) walked back into `travel_to_fortree()`, whose leg
        # ranking returns -1 for any map not in its `order` list, ran LEG[0] = Mauville
        # (19,6), and fail-fast derailed: no land route exists out of Sootopolis.
        # MEASURED: 4 of the first 6 ended runs of the 2026-09-07 batch (67%) died here.
        # ‼ The `_guard` is INSIDE the gate on purpose — it asserts we are Fortree-side, which
        # is FALSE once we are legitimately past Fortree, so leaving it out would convert the
        # navigation derail into a guard derail and "fix" nothing.
        # ⛔ Do NOT instead add the two maps to `travel_to_fortree`'s `order`: that enumeration
        # already rotted once (see its own note at early_game.py:6303-6305, written after
        # ROUTE120 hit this) and it would only move the failure down to the `_guard`.
        if not _done("BADGE06_GET"):
            from modules.story.early_game import (
                do_weather_institute,
                fight_route119_rival_and_get_fly,
                travel_to_fortree,
            )

            _r119_cleared = lambda: _done("HIDE_ROUTE_119_TEAM_AQUA")
            if not _r119_cleared() or not _done("RECEIVED_HM_FLY"):
                # Travel runs first; if Route 119's content interrupts it (institute /
                # rival not yet done), the dedicated segments below own their pieces
                # from wherever the navigation stopped.
                if _cur_map() not in (MapRSE.ROUTE119.value, MapRSE.FORTREE_CITY.value):
                    yield from travel_to_fortree()
                if not _r119_cleared():
                    yield from do_weather_institute()
                _guard("Weather Institute (Ch13b)", _r119_cleared)
                if not _done("RECEIVED_HM_FLY"):
                    yield from fight_route119_rival_and_get_fly()
                _guard("Route 119 rival / HM02 Fly (Ch13c)", lambda: _done("RECEIVED_HM_FLY"))
                yield from travel_to_fortree()
            else:
                console.print("[dim]Story: Route 119 already cleared — heading to Fortree.[/]")
                yield from travel_to_fortree()
            _guard(
                "Travel to Fortree (Ch13a)",
                lambda: _cur_map() in (
                    MapRSE.FORTREE_CITY.value,
                    MapRSE.FORTREE_CITY_POKEMON_CENTER_1F.value,
                    MapRSE.FORTREE_CITY_GYM.value,
                    MapRSE.ROUTE120.value,  # a 13d resume (Steven) is Fortree-side too
                ),
            )
        else:
            # ‼ A POSITIVE CONTROL, not decoration. The acceptance check for this fix is that
            # the Mauville derail vanishes — but an absence proves nothing on a run that never
            # got here. This line is the evidence the gate actually FIRED.
            console.print("[dim]Story: Fortree arc already complete (BADGE06) — Ch13a skipped.[/]")

        # --- Segments 13d/13e: Devon Scope (Route 120 Steven) → Fortree Gym
        #     (Winona, BADGE06). ⚠ SKELETONS (2026-07-24 overnight) — tiles probed,
        #     scenes first-run-validate. ---
        from modules.story.early_game import (
            _leave_route120_north_bridge,
            do_fortree_gym,
            get_devon_scope,
        )

        # A resume with the Scope already set skips get_devon_scope; if that resume
        # lands on the Route 120 bridge, escape it before ANY navigation (the gym
        # prep heal would otherwise NO-PATH to the Fortree PC — ch13_run14).
        yield from _leave_route120_north_bridge()

        # ‼ TWO JOBS, TWO FLAGS (2026-07-24 — caught by the post-fix Ch13d validation run).
        # get_devon_scope() does TWO things: (1) get the Scope from Steven, and (2) FLUSH the
        # Fortree gym-path Kecleon. Gating the call on RECEIVED_DEVON_SCOPE alone meant any
        # resume that already had the Scope — including EVERY derail recovery near Fortree,
        # since recovery re-runs this resume — skipped the flush too. The Kecleon then still
        # occupies (25,8), the single chokepoint tile to the gym door, and do_fortree_gym
        # NO-PATHs to (22,11) forever ("Could not find a path from (5/7 @ FORTREE_CITY)").
        # The validation run derailed 5 times on exactly this. Both sub-steps are already
        # idempotent inside get_devon_scope (it checks _have_scope() and _city_kecleon_present()
        # separately), so calling it whenever EITHER job is outstanding is safe and correct.
        _kecleon_flushed = _done("HIDE_FORTREE_CITY_KECLEON")
        if not _done("RECEIVED_DEVON_SCOPE") or not _kecleon_flushed:
            yield from get_devon_scope()
        else:
            console.print("[dim]Story: Devon Scope in the bag and the Kecleon already flushed.[/]")
        _guard("Devon Scope (Ch13d)", lambda: _done("RECEIVED_DEVON_SCOPE"))
        _guard("Fortree Kecleon flush (Ch13d)", lambda: _done("HIDE_FORTREE_CITY_KECLEON"))

        if not _done("BADGE06_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            # ‼ WINONA MUST GO THROUGH _prepare_for_fight (KI-23, 2026-07-25). She previously
            # jumped straight to `do_fortree_gym()` with only a lead-swap and a heal, so she
            # never entered the prep/boss-training machinery at ALL — which meant the
            # non-convergence guard could not fire on the ONE boss that proved it was needed.
            # A user's overnight run made 198 attempts, lost 41 times and whited out 41 times
            # against her with a party that was far ABOVE her levels but had no
            # super-effective answer to Flying (Sceptile is resisted, Ninjask is itself part
            # Flying, Shedinja has 1 HP). Wiring her in gives that run a bounded, diagnosed
            # stop instead of an unbounded whiteout loop.
            #   `ace_types`: Altaria L33 is the ace — Dragon/Flying, and 4x weak to Ice.
            #   `heal`: Fortree has the PC.
            # ‼ CORRECTED 2026-09-10 — this comment read "`grass`/`heal`: Route 119 is the
            # Fortree-side band" and **there is no `grass` key in the dict below**. The comment
            # documented a key that does not exist, so Winona's prep has ALWAYS been the GRASS-LESS
            # shape in production — not a Lavaridge special case. That matters: it means the
            # grass-less path (detection + escalation + counter ladder + honest stop, no grinding)
            # is the one actually proven at badge 6, and it is the shape the late-boss configs below
            # deliberately copy.
            winona_fight = {
                "name": "Winona",
                "keys": [MapRSE.FORTREE_CITY_GYM.value, MapRSE.FORTREE_CITY.value],
                "band": (29, 33),  # Swablu 29 / Tropius 29 / Pelipper 30 / Skarmory 31 / Altaria 33
                "ace_types": ("Dragon", "Flying"), "ace_level": 33,
                "heal": PokemonCenter.FortreeCity,
            }
            if _cur_map() != MapRSE.FORTREE_CITY_GYM.value:
                yield from self._prepare_for_fight(winona_fight)
            yield from _lead_best_matchup(["Flying"], hunted_pids=self._hunted_counter_pids)
            yield from heal_in_pokemon_center(PokemonCenter.FortreeCity)
            yield from do_fortree_gym()
        else:
            console.print("[dim]Story: Feather Badge already earned — Gym 6 skipped.[/]")
        _guard("Gym 6 (Winona)", lambda: _done("BADGE06_GET"))

        # --- Segment 14: Mt. Pyre (§Ch14-PRE + §Ch14a, built 2026-08-06). Two COORD
        #     TRIGGERS, no conversations: Route 121's Aqua grunts move out, then the
        #     summit scene hands over the Magma Emblem and opens the Magma Hideout. ---
        from modules.story.early_game import do_mt_pyre_summit, open_route121_aqua_gate

        if not _done_var("MT_PYRE_STATE", 1):
            yield from open_route121_aqua_gate()
            yield from do_mt_pyre_summit()
        else:
            console.print("[dim]Story: Mt. Pyre summit already done — skipping.[/]")
        _guard("Mt. Pyre summit", lambda: _done_var("MT_PYRE_STATE", 1))

        # --- Segment 15: the MAGMA HIDEOUT (§Ch15, built 2026-08-10). Cross to Jagged
        #     Pass, fire the coord trigger that un-walls the entrance, push the two
        #     Strength boulders that seal 1F, then 1F -> 2F_1R -> 3F_1R -> 4F and beat
        #     Maxie. Completion is the FLAG the decomp's own script sets. ---
        from modules.story.early_game import do_magma_hideout_chapter

        if not _done("GROUDON_AWAKENED_MAGMA_HIDEOUT"):
            yield from do_magma_hideout_chapter()
        else:
            console.print("[dim]Story: Magma Hideout already done — skipping.[/]")
        _guard("Magma Hideout (Ch15)", lambda: _done("GROUDON_AWAKENED_MAGMA_HIDEOUT"))

        # --- Segment 16: the SLATEPORT HARBOR submarine theft (§Ch16, built 2026-08-11).
        #     A COORD TRIGGER, no battle: Maxie's defeat set VAR_SLATEPORT_HARBOR_STATE to 1,
        #     which arms four triggers at SLATEPORT_CITY_HARBOR x=8, y=11..14. Stepping on one
        #     runs the Aqua escape scene, which sets the var to 2 and clears the two grunts
        #     blocking the Lilycove Aqua Hideout - the next chapter's door. ---
        # ‼ `_done_var` RAISES on a phantom var name rather than returning False, which is
        #    deliberate: `get_event_var` returns -1 for an unknown name and -1 compares False
        #    against every threshold, for ever. Do not hand-roll this comparison.
        from modules.story.early_game import do_slateport_harbor_theft

        if not _done_var("SLATEPORT_HARBOR_STATE", 2):
            yield from do_slateport_harbor_theft()
        else:
            console.print("[dim]Story: Slateport Harbor theft already done — skipping.[/]")
        _guard("Slateport Harbor theft (Ch16)", lambda: _done_var("SLATEPORT_HARBOR_STATE", 2))

        # --- Segment 17: the LILYCOVE AQUA HIDEOUT (§Ch17, built 2026-08-11). ---
        #     Segment 16's harbor scene SET both
        #     `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_*_BLOCKING_ENTRANCE` (HIDE set = grunt gone), so
        #     the entrance is open. The chapter heals at Lilycove, walks an 18-hop WARP-PANEL
        #     maze solved from the ROM warp table (‼ 21 of B1F's 25 warps return to B1F, so no
        #     planner can cross it), and beats TRAINER_MATT on B2F — which runs
        #     `AquaHideout_B2F_EventScript_SubmarineEscape` and sets the flag below.
        # ‼ `_done` RAISES on a phantom flag name rather than returning False. Do not hand-roll.
        from modules.story.early_game import do_aqua_hideout_chapter

        if not _done("TEAM_AQUA_ESCAPED_IN_SUBMARINE"):
            yield from do_aqua_hideout_chapter()
        else:
            console.print("[dim]Story: Aqua Hideout already done — skipping.[/]")
        _guard("Aqua Hideout (Ch17)", lambda: _done("TEAM_AQUA_ESCAPED_IN_SUBMARINE"))

        # --- Segment 18: the MOSSDEEP GYM (§Ch18, built 2026-08-12). ---
        #     Surf from Lilycove to Mossdeep, then solve the gym's ROTATING-TILE STATUE PUZZLE
        #     and beat Tate & Liza for the Mind Badge.
        # ‼ THIS GYM IS NOT A MAZE AND NOT A WALK. Nine floor switches call
        #     `moverotatingtileobjects`, which rotates every object standing on a matching
        #     coloured arrow — including NINE OF THE TRAINERS. The corridors to three warp
        #     panels are sealed by statues, so a plain collision planner is CORRECT to say
        #     "no route" (that wrong answer cost four instruments and three write-ups; KI-58).
        #     The route is searched over (player tile x every object position) on a model
        #     validated against the live game, and re-solved after every interruption.
        # ‼ LOSING HERE IS EXPENSIVE: a whiteout leaves the gym, and leaving RESETS the puzzle,
        #     so the chapter re-enters and re-solves all 117 steps. It allows three attempts.
        # ‼ Graded on the BADGE **and** controllable — `BADGE07_GET` is set mid-script, so a
        #     flag-only test would call a `lockall`ed avatar a success.
        from modules.story.mossdeep_gym import do_mossdeep_gym_chapter, leave_the_gym

        # ‼‼ `#24-regimeb-noescalation` — THE FIRST LOSS-ADAPTATION AFTER WINONA (2026-09-10).
        # MEASURED: `_prepare_for_fight`'s last call site was Winona (badge 6), and all six late
        # chapter modules contain ZERO uses of it ⇒ from badge 7 on, **N whiteouts was N IDENTICAL
        # losses** — no escalation, no counter ladder, no honest stop.
        # ⛔ GRASS-LESS ON PURPOSE, AND THE OMISSION IS THE DESIGN, NOT AN OVERSIGHT.
        # `training_areas.TRAINING_GRASS` topped out at ROUTE121 **L25-28** when this was written — ‼ AS OF 2026-09-19 it also holds VICTORY_ROAD_1F **L36-40**, so re-read the arithmetic below before trusting it: Tate & Liza's band is L41-42, still ABOVE the new ceiling, so the conclusion survives **by one level** rather than by a wide margin while Tate & Liza are
        # L41-42, so there is no ground in the table that can train for this fight — a `grass` key
        # here would send a L40 mon to L28 grass. Without it `_prepare_for_fight` still buys
        # everything that was missing: defeat detection (`_defeat_counts` already increments here —
        # the loss corpus records 973 losses on this very map), target escalation, the counter-hunt
        # ladder, and the bounded honest stop instead of an unbounded whiteout loop.
        # ⭐ The shape is copied from `winona_fight`, which has NO `grass` key either — i.e. this is
        # the badge-6 production path, not a new pattern.
        # Levels read from the DECOMP (`src/data/trainer_parties.h::sParty_TateAndLiza1`), never recalled:
        # Claydol 41 / Xatu 41 / Lunatone 42 / Solrock 42. ‼ It is a DOUBLE battle.
        if not _done("BADGE07_GET"):
            # ⛔⛔ LOCAL IMPORT REQUIRED, AND IT MUST COVER **EVERY** NAME THE CONFIG TOUCHES.
            # `PokemonCenter` is bound at TWELVE places inside `_play`, every one of them inside an
            # `if not _done("BADGEnn_GET")` branch, so a RESUMED run (badges already held) executes
            # none of them. A function-local import makes the name function-local for the WHOLE of
            # `_play`, so touching it here without importing is an `UnboundLocalError`.
            # ‼ MEASURED, NOT HYPOTHETICAL: the first version of this block built the dict OUTSIDE
            # the guard below and crashed **11 runs at ~1.6M frames each** in batch `20260910-203458`
            # — `UnboundLocalError: cannot access local variable 'PokemonCenter'`. The A/B that was
            # meant to measure the dex fence caught this instead, which is what an A/B is for.
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            tate_liza_fight = {
                "name": "Tate & Liza",
                "keys": [MapRSE.MOSSDEEP_CITY_GYM.value, MapRSE.MOSSDEEP_CITY.value],
                "band": (41, 42),
                "ace_types": ("Rock", "Psychic"), "ace_level": 42,
                "heal": PokemonCenter.MossdeepCity,
                # ⛔ `"double": True` IS LOAD-BEARING, NOT DECORATION. `_sufficiency_verdict` excludes
                # double battles explicitly (`if "ace_types" not in cfg or cfg.get("double"): return None`)
                # because a single sweeper cannot answer a 2v2. Omitting it is INERT TODAY — grass-less
                # already no-ops every branch it gates — but it becomes a live misjudgement the moment
                # `TRAINING_GRASS` gains an entry above L28, which `#24-maintain` is explicitly waiting on.
                # ✅✅ THAT TRIPWIRE FIRED ON 2026-09-19 — `TRAINING_GRASS` gained VICTORY_ROAD_1F
                # (L36-40) — AND THE FLAG WAS RE-CHECKED AS THIS COMMENT DEMANDS. `"double": True`
                # is still set below and is still load-bearing: `_sufficiency_verdict` continues to
                # exclude double battles, so a 2v2 is never judged by a single sweeper.
                # ‼ I did not notice this tripwire when I made the change that fired it — a Tier 1
                # review found it. **A dated tripwire is only worth the grep that finds it.**
                # ⇒ a flag that is only correct because a NEIGHBOURING limitation hides it is a latent bug.
                "double": True,
            }
            if _cur_map() != MapRSE.MOSSDEEP_CITY_GYM.value:
                yield from self._prepare_for_fight(tate_liza_fight)
                # ⛔⛔ THESE TWO LINES ARE NOT OPTIONAL, AND OMITTING THEM IS WORSE THAN NO ADAPTATION.
                # A Tier 1 review caught the first draft calling ONLY `_prepare_for_fight`.
                # `_lead_best_matchup` is the SOLE consumer of `_hunted_counter_pids` — the only thing
                # that FIELDS a hunted counter by moving it to slot 0. Without it the counter ladder
                # can spend its one-per-run hunt, catch and train a real answer, and never send it in;
                # then on the NEXT loss `_boss_plan_is_hopeless`'s party-wide type scan sees that
                # BENCHED counter as a "credible answer", returns not-hopeless, and SUPPRESSES further
                # escalation and the honest stop — while the unchanged lead keeps losing the same way.
                # ⇒ the counter-hunt's entire payoff discarded AND the safety valve disabled.
                # ⭐ Flannery is ALSO grass-less and still gets all three lines (`:3842-3844`) — so
                # "grass-less" never implied "prep alone". Precedent, not preference.
                # ⛔⛔ LOCAL IMPORT REQUIRED — NOT STYLE. Every binding of these two names inside
                # `_play` sits INSIDE an `if not _done("BADGEnn_GET")` branch, so a run that
                # RESUMES at badge 7 (a pinned fixture, an ENDLESS-RESET continuation, or simply
                # earlier badges already held) executes NONE of them — and a function-local import
                # makes the name function-local for the WHOLE of `_play`, so the call below would
                # raise `UnboundLocalError` on exactly the runs this change exists to help.
                # ‼ Same shadowing/scope trap that has bitten `console` three times in this file.
                yield from _lead_best_matchup(
                    list(tate_liza_fight["ace_types"]), hunted_pids=self._hunted_counter_pids
                )
                # ‼ AND THE HEAL IS OWED FROM HERE, not from the chapter. `mossdeep_gym.py` contains
                # ZERO `heal_in_pokemon_center`/`PokemonCenter` references; its own comment calls
                # "heal before challenging them" an externally-owed precondition. Unlike Sootopolis,
                # which heals itself, nothing else on this path does — so without this the bot enters
                # the hardest scripted DOUBLE battle in the game at whatever HP it arrived with.
                yield from heal_in_pokemon_center(PokemonCenter.MossdeepCity)
            yield from do_mossdeep_gym_chapter()
        else:
            # ⛔⛔ #24-mossdeepstrand — "ALREADY DONE" IS NOT "ALREADY OUT". Winning BADGE07 leaves
            # the avatar on the leaders' platform (23,8): an ELEVEN-TILE COLLISION ISLAND whose only
            # exit is a **coord_event** at (21,6) that no warp-graph solver can ever offer
            # (`mossdeep_gym.py:460-461`). With the badge set this branch used to only PRINT, so
            # nothing ever stepped on that exit and the run was stranded — every later segment then
            # fail-fast derailed on a navigation it could not possibly satisfy.
            # ‼ `leave_the_gym()` is resume-safe by construction (`mossdeep_gym.py:471-472`
            # `if not _on_gym_map(): return`), so on every ordinary re-entry — anywhere else in
            # Hoenn — this costs one call and changes nothing.
            # ⇒ A "DONE" FLAG IS NOT A "TIDY" FLAG: `BADGE07_GET` answers *did we win?*, not *is
            # there nothing left to do?*, and the gap between those two questions is this island.
            yield from leave_the_gym()
            console.print("[dim]Story: Mossdeep Gym already done — skipping.[/]")
        _guard("Mossdeep Gym (Ch18)", lambda: _done("BADGE07_GET"))

        # --- Segment 19: the MOSSDEEP SPACE CENTER + HM08 DIVE (§Ch19, built 2026-08-12). ---
        #     Ride the forced Team Magma cutscene, cross the Space Center, beat the three grunts,
        #     fight the MULTI BATTLE alongside Steven, then collect HM08 Dive at Steven's house.
        # ‼ GRADED ON `RECEIVED_HM_DIVE`, NOT on `MOSSDEEP_SPACE_CENTER_STATE == 3`, because that
        #     is what `chapters.py` grades chapter 19 on and the two are set in DIFFERENT
        #     BUILDINGS. A segment that stopped at the battle would pass its own guard while
        #     `current_chapter()` returned 19 for ever — and on the re-run the 2F Steven has been
        #     `removeobject`'d, so there would be nobody left to talk to.
        # ‼ THE CITY IS CUT IN TWO until the cutscene runs: the gym victory SPAWNS five Team Magma
        #     NPCs onto the only land bridge (x=44, y=23-26), and our planner blocks loaded object
        #     tiles — so no route to the Space Center door exists until they leave. Measured, and
        #     it failed the first driven run exactly this way.
        # ‼ THE STAIR GRUNT MUST BE TALKED TO. It has `sight_radius = 0` and stands ON the only
        #     tile the stairs are reachable from, so navigating there can never succeed.
        # ‼ THE PARTY-SELECTION MENU IS DRIVEN, NOT MASHED. A on an already-chosen mon DESELECTS
        #     it, so A-mash toggles one slot for ever; each pick is verified against
        #     `gSelectedOrderFromParty`. It brings the strongest THREE — bringing fewer is strictly
        #     worse, because the loss condition sums HP over the player's picks only.
        # ‼ LOSING IS A RETRY, NOT AN ERROR: the script calls `SetCB2WhiteOut` itself, halves the
        #     money and warps to the last heal location, but leaves the var at 2. Three attempts.
        from modules.story.space_center import do_space_center_chapter

        if not _done("RECEIVED_HM_DIVE"):
            yield from do_space_center_chapter()
        else:
            console.print("[dim]Story: Mossdeep Space Center already done — skipping.[/]")
        _guard("Mossdeep Space Center + Dive (Ch19)", lambda: _done("RECEIVED_HM_DIVE"))

        # --- Segment 19b: TEACH DIVE. HM08 is in the bag after Ch19, but at this point in a real
        #     run the party is FULL and NOBODY can learn Dive (measured on `post_space_center.ss1`:
        #     Sceptile/Zigzagoon/Swellow/Skitty/Mightyena/Castform, `hm_learner_slot(HM08)` -> None).
        #     §Ch20 REFUSES to start without a Dive user, so this must be acquired by PLAYING.
        #     ‼ The ch20 drivers cheat here — `_inject_dive_fixture` `debug_write_party`s a Wailmer
        #     into slot 3. Production does NOT fabricate; it hunts, makes room, and teaches.
        #     ⚠ Route 117 Marill (10%, L13, ~1055 waypoints) is what `_hm_hunting_grounds` picks
        #     today. Route 120 Marill (15%, L25-27, ~379 waypoints) is measurably better on every
        #     axis and is filed as `#24-divegroundroute120` — it needs ONE live sweep first, because
        #     this project demotes statically-derived grounds (the Route 114 lesson).
        #     ⛔ Shoal Cave is NOT an option and must not be re-proposed: ruled out 2026-08-13
        #     (`06-DECISIONS-LOG.md`) because at HIGH TIDE its reachable on-foot encounter tiles drop
        #     to ZERO, so the hunt would silently burn its whole budget and read as bad luck.
        def _party_knows_dive() -> bool:
            try:
                from modules.pokemon_party import get_party as _gp

                return any(
                    learned is not None and learned.move.name == "Dive"
                    for mon in _gp()
                    if mon is not None and not mon.is_egg
                    for learned in mon.moves
                )
            except Exception:
                return False

        if not _party_knows_dive():
            from modules.items import get_item_by_name
            from modules.map_data import PokemonCenter
            from modules.story.early_game import ensure_hm_learner_making_room, teach_hm_move

            _hm08 = get_item_by_name("HM08")
            # ‼ `ensure_hm_learner_making_room` is safe with a full party: it deposits ONLY on the
            # specific "party is full" failure, and `find_dead_weight` EXEMPTS the sole carrier of
            # any HM — driven evidence on this exact party picks Skitty and spares the Zigzagoon
            # carrying Surf, which the run needs to reach Route 128 at all.
            _slot = yield from ensure_hm_learner_making_room(_hm08, (PokemonCenter.MossdeepCity,))
            yield from teach_hm_move(_hm08, _slot)
        else:
            console.print("[dim]Story: someone already knows Dive — teach skipped.[/]")
        _guard("Teach Dive (Ch19b)", _party_knows_dive)

        # --- Segment 20: the SEAFLOOR CAVERN — dive in, nine rooms, Kyogre, off the atoll. ---
        #     ⛔ GRADED ON `ROUTE128_STATE >= 2`, NEVER on `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`: that
        #     flag is set at `Room9/scripts.inc:128`, BEFORE the warp at `:138` and before a SECOND
        #     lock-all cutscene on Route 128 — so a flag-graded segment would report success from
        #     inside two nested scenes, standing on a sandbar it cannot leave.
        #     ‼ `_done_var` is used rather than a raw `get_event_var` because `get_event_var`
        #     returns -1 for a phantom name and would compare False against every threshold forever.
        #     The decomp spells it `VAR_ROUTE128_STATE`; our table's key is the bare `ROUTE128_STATE`.
        from modules.story.seafloor_cavern import do_seafloor_cavern_chapter

        if not _done_var("ROUTE128_STATE", 2):
            yield from do_seafloor_cavern_chapter()
        else:
            console.print("[dim]Story: Seafloor Cavern already done — skipping.[/]")
        _guard("Seafloor Cavern / Kyogre (Ch20)", lambda: _done_var("ROUTE128_STATE", 2))

        # --- Segment 21: SOOTOPOLIS / CAVE OF ORIGIN / SKY PILLAR / RAYQUAZA / HM07 ---------------
        # ⛔⛔ GRADED ON `ch21_chapter_done()`, WHICH IS THE FLAG **AND**
        # `SOOTOPOLIS_WALLACE_STATE != 0` — NOT the flag alone, even though `chapters.py:250` grades
        # the progress READOUT on the flag alone (deliberately; see `chapters.py:240-248`).
        # `giveitem`/`setflag` and the `call_if_eq VAR_FACING` tail that walks Wallace OFF the
        # (31,33) tile blocking the (31,32) GYM warp are different decomp lines, and a run that dies
        # between them holds HM07 with §Ch22's entrance SEALED. MEASURED: leg-5 drive 1 printed
        # `ACCEPTANCE: PASS` in exactly that state (`08-MISTAKES.md` 2026-09-02).
        from modules.story.sootopolis import ch21_chapter_done, do_sootopolis_chapter

        if not ch21_chapter_done():
            yield from do_sootopolis_chapter()
        else:
            console.print("[dim]Story: Sootopolis / Rayquaza already done — skipping.[/]")
        _guard("Sootopolis / Rayquaza / HM07 (Ch21)", ch21_chapter_done)

        # --- Segment 22: GYM 8 — JUAN (SOOTOPOLIS) -------------------------------------------------
        # ⛔⛔ GRADED ON `ch22_chapter_done()`, WHICH IS THE BADGE **AND A POSITION** — never the
        # badge alone. `BADGE08_GET` is set by `SootopolisCity_Gym_1F_EventScript_JuanDefeated`
        # while the bot still stands on JUAN_STAND (8,3), on a 20-TILE ISLAND, with the exit warp
        # AND the 1F ladder both unreachable and `allow_escaping` false on BOTH floors. Grading on
        # the flag would hand the next segment a stranded run — the §Ch15 / §Ch18 / §Ch19 shape,
        # each of which PASSED its own test while stranded.
        # ‼ `chapters.py:255-256` grades the progress READOUT on the flag alone, deliberately: the
        # readout answers "which chapter is this run in", not "may the next segment start".
        # ⛔ AND THE FALL TO B1F IS PART OF THIS CHAPTER, NOT AN ACCIDENT. After the ice is walked
        # there is no other way off Juan's platform; the chapter breaks (8,6) on purpose. Because
        # the victory script `settrainerflag`s all ten B1F trainers, that descent is BATTLE-FREE.
        from modules.story.sootopolis_gym import ch22_chapter_done, do_sootopolis_gym_chapter

        # ‼‼ `#24-regimeb-noescalation` — loss adaptation for badge 8, same shape as Tate & Liza.
        # GRASS-LESS for the same measured reason: the training table's ceiling is L28 and Juan's
        # ace is **Kingdra L46**, so no tabled ground can prepare for this fight.
        # Levels from the DECOMP (`src/data/trainer_parties.h::sParty_Juan1`), never recalled:
        # Luvdisc 41 / Whiscash 41 / Sealeo 43 / Crawdaunt 43 / **Kingdra 46**.
        # ⚠ The band's TOP is the ace, five levels above the rest — a band of (41, 43) would read
        # the roster's bulk and miss the mon that actually wins the fight.
        if not ch22_chapter_done():
            # ⛔⛔ LOCAL IMPORT REQUIRED, AND IT MUST COVER **EVERY** NAME THE CONFIG TOUCHES.
            # `PokemonCenter` is bound at TWELVE places inside `_play`, every one of them inside an
            # `if not _done("BADGEnn_GET")` branch, so a RESUMED run (badges already held) executes
            # none of them. A function-local import makes the name function-local for the WHOLE of
            # `_play`, so touching it here without importing is an `UnboundLocalError`.
            # ‼ MEASURED, NOT HYPOTHETICAL: the first version of this block built the dict OUTSIDE
            # the guard below and crashed **11 runs at ~1.6M frames each** in batch `20260910-203458`
            # — `UnboundLocalError: cannot access local variable 'PokemonCenter'`. The A/B that was
            # meant to measure the dex fence caught this instead, which is what an A/B is for.
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            juan_fight = {
                "name": "Juan",
                "keys": [MapRSE.SOOTOPOLIS_CITY_GYM_1F.value, MapRSE.SOOTOPOLIS_CITY.value],
                "band": (41, 46),
                "ace_types": ("Water", "Dragon"), "ace_level": 46,
                "heal": PokemonCenter.SootopolisCity,
            }
            if _cur_map() != MapRSE.SOOTOPOLIS_CITY_GYM_1F.value:
                yield from self._prepare_for_fight(juan_fight)
                # ⛔ SAME REASON AS TATE & LIZA: `_lead_best_matchup` is the only consumer of
                # `_hunted_counter_pids`, so without it a hunted counter is caught, trained, and
                # never fielded — and the benched mon then makes `_boss_plan_is_hopeless` read
                # not-hopeless, suppressing escalation. Caught by a Tier 1 review.
                # ⛔⛔ LOCAL IMPORT REQUIRED — NOT STYLE. Every binding of these two names inside
                # `_play` sits INSIDE an `if not _done("BADGEnn_GET")` branch, so a run that
                # RESUMES at badge 7 (a pinned fixture, an ENDLESS-RESET continuation, or simply
                # earlier badges already held) executes NONE of them — and a function-local import
                # makes the name function-local for the WHOLE of `_play`, so the call below would
                # raise `UnboundLocalError` on exactly the runs this change exists to help.
                # ‼ Same shadowing/scope trap that has bitten `console` three times in this file.
                yield from _lead_best_matchup(
                    list(juan_fight["ace_types"]), hunted_pids=self._hunted_counter_pids
                )
                # ‼ NO `heal_in_pokemon_center` HERE, AND THAT IS DELIBERATE — the one place this
                # block differs from Tate & Liza. `sootopolis_gym.py:872` calls `_heal_before_the_gym`
                # internally on every non-resumed entry, so an external heal would be a REDUNDANT
                # round trip across Sootopolis. ⇒ copying the precedent's third line here would be
                # cargo-culting: the precedent exists because the chapter does NOT heal itself.
            yield from do_sootopolis_gym_chapter()
        else:
            console.print("[dim]Story: Sootopolis Gym / Juan already done — skipping.[/]")
        _guard("Gym 8 — Juan (Ch22)", ch22_chapter_done)

        # --- Segment 22b: TEACH WATERFALL (§Ch23 leg 1, which existed only as a harness driver).
        #     ⛔⛔ THIS IS WHY NO RUN HAS EVER FINISHED. Across 37 stored batches the 8th badge was
        #     reached SIX times — all six on 2026-09-07 — and all six died on §Ch23's preflight
        #     because nothing in production ever taught HM07. The chapter's own build spec recorded
        #     the gap ("driver only, production module absent") and every §Ch23 fixture is
        #     downstream of that driver's teach, so the chapter passed its driven tests for days
        #     while the route to it was impassable.
        #     ⭐ PLACED AT 22b, NOT 21b, DELIBERATELY: a 21b stop would fire BEFORE badge 8, and
        #     badge 8 has been reached six times in the project's whole recorded history. Failing
        #     earlier would erase the only evidence that §Ch21 and §Ch22 work end to end. 22b is
        #     still strictly before the preflight — nothing between here and `depart_sootopolis`
        #     touches the party.
        #     ‼ HM07 is in the bag from §Ch21; only field USE needs BADGE08, the same
        #     flag-vs-badge split Segment 10b documents for Rock Smash.
        from modules.story.victory_road import ensure_waterfall_learner, field_move_carriers

        yield from ensure_waterfall_learner()
        _guard("Teach Waterfall (Ch22b)",
               lambda: field_move_carriers()["Waterfall"] is not None)

        # --- Segment 23: VICTORY ROAD ---------------------------------------------------------------
        # ⛔⛔ GRADED ON `ch23_chapter_done()`, WHICH IS THE FLAG **AND A POSITION** — never the flag
        # alone. `chapters.py:280-286` grades Segment 23's READOUT on `DEFEATED_WALLY_VICTORY_ROAD`,
        # and that flag is set at **LEG 5 OF 11**, while the bot stands at the B1F ladder apron with
        # the boulder interlock, B2F, the return climb, the exit, the League heal and the shop all
        # still ahead of it. Grading the GATE on it would hand §Ch24 a run buried two floors
        # underground — the §Ch15 / §Ch18 / §Ch19 shape, each of which PASSED its own test while
        # stranded, and which §Ch22's predicate exists because it was nearly the fourth.
        # ‼ The readout answers "which chapter is this run in"; the gate answers "may the next
        # segment start". Both are correct. Do not collapse them.
        from modules.story.victory_road import ch23_chapter_done, do_victory_road_chapter

        def _ch23_settled() -> bool:
            """§Ch23 is settled if it finished NORMALLY, or if §Ch24 has taken over the run.

            ⛔⛔ BOTH HALVES BELOW USE THIS, AND THAT IS NOT TIDINESS. `_guard` is
            ASSERT-not-skip (`:3981` returns on success, `:3991` raises): leaving it on the bare
            predicate while only the skip became latch-aware would stop the bot with a diagnostic
            on the very first re-entry — the failure would simply move one line down.
            """
            return self._ch24_owns_run or ch23_chapter_done()

        if not _ch23_settled():
            yield from do_victory_road_chapter()
        else:
            console.print("[dim]Story: Victory Road already done — skipping.[/]")
        _guard("Victory Road (Ch23)", _ch23_settled)

        # ---- §Ch24 LEG 1 — TRAINING (`#24-flyladder` Piece 3) --------------------------------
        # ⭐ USER RULING 12 (2026-09-23): train ALL SIX to L65-75; the party is NOT reduced.
        # ⛔ IT MUST RUN BEFORE ANY GAUNTLET CONTENT: the Elite Four is ONE-WAY (the doors seal,
        # the bag is the only healing), so arriving under-levelled is unrecoverable.
        # ‼ The leg SELF-SKIPS when nobody is below the floor, so this is safe to re-enter after a
        # derail — it re-reads the party each pass and does only what is left. There is therefore
        # no `_guard` here yet: §Ch24's own completion marker is `#24-markerwinstate`'s work, and
        # guarding on "everyone is L65" would STOP the bot on a party that simply ran out of
        # reachable ground — a survivable shortfall, not a derail.
        from modules.story.pokemon_league import (
            ch24_chapter_done,
            ensure_fly_learner,
            run_the_gauntlet,
            train_for_league,
        )

        # ⛔⛔ THE SHORT-CIRCUIT, AND ITS PREMISE IS **NOT** THE ONE I FIRST WROTE DOWN.
        # I originally justified this as "otherwise §Ch23 re-runs and re-buys the Elite Four
        # basket". THAT IS REFUTED: `ch23_chapter_done()` already returns True forever once
        # `IS_CHAMPION` is set (`victory_road.py`, fixed 2026-09-24 under `#24-markerwinstate` —
        # "Success was the failure case"). The basket problem was solved before I got here.
        # ⇒ THE REAL REASON, verified in the tree: nothing stops `train_for_league()` from running
        # again on a CLEARED save, and the §Ch24 party carries mon UNDER the L65 floor
        # (`Zigzagoon L19`, `Castform L36` in the pinned fixture). Without this gate a FINISHED game
        # re-entering `_play` would start GRINDING FOR HOURS and then walk into a gauntlet it had
        # already won. ‼ A cleared game is exactly the state that must do nothing at all.
        if ch24_chapter_done():
            console.print("[dim]Story: §Ch24 already done — the game is CLEARED. Skipping.[/]")
        else:
            # ⭐ `#26-ch24organic` GAP 3 — LATCH, THEN TEACH FLY, THEN TRAIN (the recon's placement).
            # Without a Fly knower the per-trainee ladder offers only WALKABLE ground (from the League
            # plateau: Victory Road 1F, band 36-40) and the return bridge cannot fly home.
            # ⛔ LATCH FIRST: owning the run is what keeps a derail from re-entering §Ch23; the teach is a
            # menu flow that may raise, and `train_for_league` would only latch after it.
            self.mark_ch24_owns_run()
            _ch24_fly_report: dict = {}
            yield from ensure_fly_learner(_ch24_fly_report)
            if _ch24_fly_report.get("fly_teach") not in ("already", "taught"):
                _log_story_event(
                    f"Story: §Ch24 continues WITHOUT Fly ({_ch24_fly_report.get('fly_teach')}) — only "
                    f"walkable ground can train, and the return bridge will refuse by name off the plateau.")
            _ch24_train_report: dict = {}
            yield from train_for_league(_ch24_train_report)
            if _ch24_train_report.get("still_below"):
                _log_story_event(
                    f"Story: §Ch24 training ended with mon still below the floor: "
                    f"{_ch24_train_report['still_below']}")

            # ⭐ THE GAUNTLET — lobby → Sidney → Phoebe/Glacia/Drake → HALL4 → Wallace → cleared.
            # ‼‼ **NO `floor=` OVERRIDE.** It defaults to `CH24_LEVEL_FLOOR` (65). Every proven drive
            # used a LOW floor through `CH24_ENTRY_FLOOR`, and copying a test invocation to here
            # would quietly lower the readiness bar for a ONE-WAY, NURSE-LESS chapter with no error
            # raised anywhere. The readiness guard the comment below demands IS step 1 of this call —
            # R1 in `prepare_and_open_the_league` (`#26-ch24organic`; until 2026-09-26 it was a reading only).
            # ⛔ It does not catch, retry or recover: from the moment it crosses `(9,1)` the zone is
            # SEALED, so every failure propagates loudly rather than leaving the bot in a corridor
            # it cannot leave. Re-entry after a loss is `#24-restockleg` (USER RULING 12), UNBUILT.
            _ch24_report: dict = {}
            yield from run_the_gauntlet(_ch24_report)
            _log_story_event(
                f"Story: §Ch24 COMPLETE — the game is cleared. "
                f"end_at={_ch24_report.get('end_at')} pairs={_ch24_report.get('pairs')}")

        # ‼ ASSERT, DO NOT ASSUME — the same shape as §Ch23's `_guard` above. If the gauntlet
        # returned without the chapter actually being done, stop HERE with a diagnostic rather than
        # printing a completion banner over a run that did not finish.
        _guard("The Pokémon League (Ch24)", ch24_chapter_done)

        # END OF BUILT CONTENT — ‼ RETARGETED 2026-09-24, BECAUSE §Ch24 NOW BEGINS **ABOVE**
        # THIS LINE. The §Ch24 TRAINING leg (`train_for_league`) runs a few lines up, so the
        # old text — *“Next build: the Elite Four gauntlet”* — is no longer the first missing
        # thing. A stale pointer here misdirects every cold start, which is exactly what P4
        # exists to catch.
        # ✅ RETARGETED 2026-09-25 — **THE §Ch24 GAUNTLET IS NOW BUILT AND WIRED ABOVE.**
        # (superseded: "WHAT IS ACTUALLY NEXT: the §Ch24 GAUNTLET — Training is BUILT; the
        # fights are not.") Sidney, Phoebe, Glacia, Drake and Champion Wallace are all
        # fought by `run_the_gauntlet`, driven end to end and evidenced.
        # ⇒ WHAT IS ACTUALLY NEXT: **POKÉDEX HUNTING** (`#24-dexhunt`) — the post-game.
        # ⚠ The forward dependency below is now SATISFIED, not pending: the gauntlet's
        # first act IS a readiness guard (`prepare_and_open_the_league` decides readiness
        # OUTSIDE the League, because all three remedies are measured non-functional from
        # inside the lobby). The text is kept because the HAZARD it describes is permanent.
        # ⛔⛔ AND A FORWARD DEPENDENCY THAT MUST NOT BE FORGOTTEN WHEN THEY ARE WIRED:
        # `train_for_league` deliberately has **no floor `_guard`** after it — a party can
        # fall through still BELOW L65 if it runs out of reachable ground or a purse
        # expires. That is safe ONLY while nothing is wired past this point. The moment the
        # gauntlet is reachable, an under-levelled party would walk into a ONE-WAY,
        # NURSE-LESS fight. ⇒ the gauntlet's first act must be a readiness guard. ⛔ NO NURSE BETWEEN ROOMS —
        # the doors seal behind you, so the BAG is the only healing, and items are legal in those
        # battles (decomp-verified). §Ch23 leg 11 already buys the basket for exactly this reason.
        # ✅ §Ch23 IS NOW WIRED (2026-09-05) — the orchestrator dispatches on POSITION because six of
        # its legs RAISE when their work is already done (anti-vacuity guards written for standalone
        # drivers, which invert into a liability on a whiteout resume).
        # ⛔ THE CITATION BELOW USED TO READ `chapters.py:259-262` FOR CHAPTER 23. It is
        # **`chapters.py:280-286`** — 259-262 is Segment 21's neighbourhood. Verified 2026-09-05.
        # (superseded heading: "Next build: VICTORY ROAD — Chapter 23", graded on
        # `DEFEATED_WALLY_VICTORY_ROAD`: Surf/Waterfall/Dive to Ever Grande, then clear Victory Road
        # and beat Wally.)
        # ⭐ Badge 8 is what makes field WATERFALL usable (`src/field_control_avatar.c` gates
        # `EventScript_UseWaterfall` on `FLAG_BADGE08_GET`), which is exactly what opens Routes
        # 132-134 — so §Ch22 landing is what unblocks §Ch23.
        # ✅ §Ch22 IS NOW WIRED (2026-09-03). ✅ §Ch21 IS NOW WIRED (2026-09-02);
        # the Ch21 leads below are retained because their TRAPS still apply to anyone touching it.
        # ⛔ This heading has been wrong twice before — it is a BANNER, and a banner is a claim about
        # every clause under it; retarget it in the SAME commit as the next segment that lands.
        # (superseded heading: "Next build: SOOTOPOLIS / RAYQUAZA — **Chapter 21**".)
        # ✅ §Ch20 IS NOW WIRED (2026-08-24) — the text below is retained for its Ch21 leads and for
        # the traps, which still apply. Sootopolis is driven by `VAR_SOOTOPOLIS_CITY_STATE == 1`,
        # which Room 9 sets in the SAME block that sets `ROUTE128_STATE` — so Ch21 is enterable the
        # moment Ch20 completes. (Superseded text follows.)
        # OLD: END OF BUILT CONTENT. Next build: the SEAFLOOR CAVERN — which is **Chapter 20**
        # (`chapters.py:233`, graded on `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`). Chapter 21 is
        # Sootopolis/Rayquaza and has not been touched.
        # ✅ **KI-63 IS RESOLVED (2026-08-13) — this comment used to say the cavern was BLOCKED by
        # it, and that is no longer true.** The bot acquires Dive by playing (`--driver divelearner`
        # PASS: frees a slot, catches a learner, teaches Dive, keeps Surf), and the two HM call
        # sites above are wired to `ensure_hm_learner_making_room`. The dive leg itself is also
        # driven end to end (`--driver ch20dive` → `legs=6/6 at_entrance=True got_out=True`).
        # ⇒ What remains is BUILDING the chapter: the cavern INTERIOR (rooms 1-9), Archie, Kyogre.
        # ‼ Two traps recorded before anyone starts: **KI-72** — never let the planner choose where
        # you surface, hand-pick the tile and assert its `tile_type`; and **do not end the chapter
        # at `ROOM9 (17,42)`**, which is the ONLY coord trigger in the cavern (‼ NOT (16,42) — that
        # is plain floor and fires nothing; upstream's puzzle_solver stops one tile short of it).
        # ‼ And the real release point is `VAR_ROUTE128_STATE == 2`, NOT the Kyogre flag: the flag is
        # set BEFORE a forced warp to ROUTE128 (38,22) that starts a SECOND lockall cutscene, and
        # (38,22) is a shallow-water SANDBAR — the bot must Surf off it. The standing rule is "and the bot
        # can continue", and three chapters have already shipped stranded.
        # ⭐⭐ RETARGETED 2026-09-25, IN THE SAME COMMIT AS THE DISPATCH ABOVE — because this
        # banner is a CLAIM ABOUT EVERY CLAUSE UNDER IT, and the old text said Ch24 was "NEXT
        # (WIP)" on a run that has just cleared the game. It has been wrong twice before.
        context.message = (
            "Story: THE GAME IS CLEARED (Ch24) - the Elite Four (Sidney, Phoebe, Glacia, Drake) "
            "and Champion Wallace are beaten, the Hall of Fame is recorded, and the bot is back "
            "in control. End of built content. NEXT (WIP): POKEDEX HUNTING - catching to fill "
            "the dex. Handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        # ‼ Mark a GENUINE completion. Both this path and the give-up paths call
        # `set_manual_mode()` and return normally, so the endless loop cannot tell them
        # apart from the outside — and without this flag it would relabel real successes
        # as "stopped" (P2 run 1 of bundle `20260726-231412` reached exactly here and
        # earned the Feather Badge).
        self._reached_end_of_content = True
        context.set_manual_mode()
        return


def _log_story_event(message: str, category: str = "STORY") -> None:
    """Mirror a console decision into the DEBUG LOG.

    ‼ `console.print` and `modules/debug_logger.py` are SEPARATE STREAMS — the debug logger
    never sees console output. Any decision that only reaches the console is invisible in the
    artefact people actually share for review. Bitten three times now: the training-relocation
    rule banner, the relocation decision itself, and the after-faint chooser's filter state.
    If a decision matters to a reviewer, it goes through here as well.
    """
    try:
        from modules import debug_logger

        debug_logger.event(message, category=category)
    except Exception:  # noqa: BLE001 - logging must never end a run
        pass


#: Set to "0" to leave emulation speed/video exactly as the GUI or CLI configured them.
#: Anything else (or unset) applies the debug-run config below.
_TURBO_ENV = "POKEBOT_STORY_DEBUG_TURBO"


def _apply_debug_emulation_config() -> None:
    """Give a SINGLE-LANE debug Story run the same emulation config an x4 lane gets.

    ‼ WHY (user directive 2026-07-29): the user cannot run ENDLESS LOOP x4 on their work
    machine — it lacks the power for four emulators — but x4 lanes are configured far better
    for test runs than a hand-launched single bot, and they get there automatically:

        modules/endless_x4.py:160   "-s", "0",   # unthrottled, as requested
        modules/gui/tile_child.py:84  context.video = True  # REQUIRED

    A hand-launched debug run inherited whatever the GUI happened to have — the
    `20260729-122709` log shows `speed=1 video=True`, i.e. throttled, which made a
    2.78M-frame run take hours. So the debug modes now configure themselves.

    ‼ VIDEO IS FORCED **ON**, AND THAT IS DELIBERATE — it is what makes the FAITHFUL path
    work. The PokéNav Match-Call tutorial only advances with the renderer on; run
    `20260729-122709` (video=True) played it faithfully with no state-write fallback, while
    the user's earlier video-off runs fell back 8 times out of 9.

    ‼ THIS SUPERSEDES the 2026-07-26 "SPEED ONLY — NEVER TOUCH `context.video`" directive,
    and the distinction matters. That rule was written because the endless loop used to
    CAPTURE video at batch start and RE-PIN it every run — so a batch begun with video off
    kept it off for ever, silently degrading the faithful path. The harm was PINNING TO AN
    ARBITRARY VALUE, not writing the field. Forcing it ON, once, is the opposite: it is the
    value the faithful path requires, and it is what x4 already does.
    Ruling recorded in `06-DECISIONS-LOG.md` 2026-07-29.

    Escape hatch: `POKEBOT_STORY_DEBUG_TURBO=0` leaves both settings untouched. The resulting
    values are printed in every debug log's RUN HEADER (`emulation: speed=… video=…`), so
    there is never any doubt about what was applied.
    """
    import os

    from modules.console import console

    if os.environ.get(_TURBO_ENV, "1").strip().lower() in ("0", "false", "no", "off"):
        console.print(f"[dim]Story (DEBUG): {_TURBO_ENV}=0 — leaving speed/video as configured.[/]")
        return
    try:
        if context.emulation_speed != 0:
            context.emulation_speed = 0
        if not context.video:
            context.video = True
        console.print("[dim]Story (DEBUG): emulation set to unthrottled + video ON "
                      "(matches an x4 lane; POKEBOT_STORY_DEBUG_TURBO=0 to opt out).[/]")
    except Exception:  # noqa: BLE001 - never let a display setting stop a run
        pass


class StoryDebugMode(StoryMode):
    """"Story (DEBUG)" (user request 2026-07-22): exactly Story, but with the opt-in
    Debug Logging switched ON automatically at start. Runs from ANY point — the title
    screen, a loaded save, or mid-route — via Story's native segmented resume (flags +
    position); nothing else differs. Exists to make real-hardware test runs one click."""

    @staticmethod
    def name() -> str:
        return "Story (DEBUG)"

    def run(self):
        _apply_debug_emulation_config()
        try:
            from modules import debug_logger
            from modules.console import console

            path = debug_logger.enable()
            console.print(f"[bold cyan]Story (DEBUG): debug logging ON -> {path}[/]")
        except Exception:
            pass
        yield from super().run()


class StoryDebugResetMode(StoryMode):
    """"Story (DEBUG - RESET)" (user request 2026-07-22): debug logging ON, then a HARD
    EMULATOR RESET to the title screen, then Story from scratch — and NEW GAME is selected
    explicitly even when a save file exists (the plain intro's A-mash would pick CONTINUE,
    which sits on top of the main menu whenever there is a save). The existing save file is
    NOT erased by this — Emerald only overwrites it if/when the game saves in-game later.
    Exists to make fresh-run testing one click."""

    @staticmethod
    def name() -> str:
        return "Story (DEBUG - RESET)"

    def run(self):
        from modules.console import console
        from modules.memory import read_symbol
        from modules.modes import BotModeError
        from modules.modes.util.sleep import wait_for_n_frames
        from modules.tasks import task_is_active

        _apply_debug_emulation_config()
        try:
            from modules import debug_logger

            path = debug_logger.enable()
            console.print(f"[bold cyan]Story (DEBUG - RESET): debug logging ON -> {path}[/]")
        except Exception:
            pass

        # ⛔⛔ A HARD RESET MUST START FROM NO INPUT — `#24-truckleak`, MEASURED 2026-09-07.
        # `_held_inputs` is PYTHON-SIDE state on the emulator wrapper (`modules/libmgba.py:157`)
        # and `reset()` (`:198-199`) does not touch it, so any D-pad key still held when a run is
        # KILLED is re-OR'd into the pad every frame of the NEXT run (`libmgba.py:581`).
        # ⭐ WHAT THAT COST: batch lane L03 lost **146 runs** to
        # "Could not step off the truck (still INSIDE OF TRUCK)". Run 2 died on the frame budget
        # mid-walk, `GeneratorExit` unwound the navigator (which has no `finally:`), and a leaked
        # `Up` then beat the truck loop's `press_button("Right")` for the rest of the batch.
        # The separation is total: 867 dumps with `held_buttons=[]` exit the truck in ~67 frames;
        # 719 dumps with `['B','Up']` sit at (2,1) facing Up — 858 failures, ZERO escapes.
        # ‼ THIS SEAM ON PURPOSE: `StoryEndlessResetMode` reaches it through `super().run()` every
        # iteration, and the standalone "Story (DEBUG - RESET)" menu entry gets it too — one line,
        # both modes. It is also UPSTREAM of the main-menu drive below, which presses A/Down and is
        # equally corrupted by a stale hold.
        # ⛔ DO NOT move this to a per-frame or per-wait path: navigation DEPENDS on held buttons
        # (`modules/modes/util/walking.py`), and clearing them there would stop the avatar moving
        # and fill the batch with "Could not reach …" derails instead. That is the inverse failure.
        # ‼ It ANNOUNCES itself — a silent release is an un-gradeable fix, and the printed mask is
        # what makes a fault-armed acceptance run readable.
        _leaked = context.emulator.reset_held_buttons()
        if _leaked:
            console.print(f"[yellow]DEBUG-RESET: released leaked held inputs (0x{_leaked:04x}) "
                          f"before the reset — see #24-truckleak.[/]")

        # Hard reset to the boot screen. (State after this: copyright/intro -> title.)
        context.emulator.reset()
        yield

        # Drive to the MAIN MENU (bounded): A skips the copyright/intro/title screens.
        frames = 0
        while not task_is_active("Task_HandleMainMenuInput"):
            if frames % 4 == 0:
                context.emulator.press_button("A")
            frames += 1
            if frames > 3000:
                raise BotModeError("DEBUG-RESET: never reached the main menu after reset.")
            yield

        # With a save on file the menu is CONTINUE / NEW GAME / ... with the cursor on
        # CONTINUE — one Down puts it on NEW GAME. Without a save, NEW GAME is already on
        # top and pressing Down would select OPTION instead, so only move when a save
        # exists (gSaveFileStatus == 1 means SAVE_STATUS_OK, set by the menu itself).
        save_ok = False
        try:
            save_ok = int.from_bytes(read_symbol("gSaveFileStatus", size=2), "little") == 1
        except Exception:
            pass
        if save_ok:
            console.print("[cyan]Story (DEBUG - RESET): save file present — selecting NEW GAME explicitly.[/]")
            yield from wait_for_n_frames(10)
            context.emulator.press_button("Down")
            yield
            yield from wait_for_n_frames(6)

        # Hand over to Story: _play sees "at title / not started" and runs the intro,
        # whose A-mash now confirms the pre-selected NEW GAME.
        yield from super().run()


#: How many chained DEBUG-RESET runs "Story (ENDLESS RESET)" performs. 0 = run forever.
#: Set by the GUI's "Endless Debug-Reset Runs…" dialog before it selects the mode; defaults to
#: 10 so picking the mode straight from the dropdown still does something sensible.
ENDLESS_RESET_TARGET = 10

#: How many runs of the CURRENT batch have FINISHED. Read across the process boundary by
#: ENDLESS LOOP x4 (`modules/gui/tile_child.py`) so each tile can show its lane's run count
#: — a lane's progress is otherwise invisible from the dashboard, which has no access to a
#: child's `context`. Reset at batch start; purely informational, never a control input.
ENDLESS_RESET_COMPLETED = 0


class StoryEndlessResetMode(StoryDebugResetMode):
    """"Story (ENDLESS RESET)" (user request 2026-07-25): chained DEBUG-RESET runs, IN-PROCESS.

    ‼ WHY IN-PROCESS. The first attempt at this feature shelled out to
    `tools/story-dev/endless_runs.py` from a menu item; the dialogs appeared and nothing
    happened, because a separate headless harness is not what "endless debug reset runs" means.
    The user wants exactly what `Story (DEBUG - RESET)` already does — hard reset → NEW GAME →
    play the story — repeated back to back in THIS emulator: "effectively chained debug reset
    bots". So this mode just loops the parent's run().

    Each iteration ends when the story finishes (end of built content), derails with a
    `BotModeError`, or trips one of StoryMode's own bounds. `BotModeError` is SWALLOWED on
    purpose: a crash in run 3 must not cost runs 4..N of an overnight batch. The next run then
    begins with a hard reset, which is a clean slate by construction.

    Failsafes beyond the parent's:
      * a per-run FRAME CAP, so a run that neither finishes nor raises cannot hold the batch
        forever — StoryMode's global watchdog normally catches that, but not if the watchdog
        itself is what wedged;
      * the bot mode is forced back to this mode after every run, because a derail deep inside
        StoryMode can call `set_manual_mode()`, which would otherwise silently end the batch;
      * a per-run outcome line, so the console shows progress without opening a log.
    """

    #: Hard per-run frame cap, ENFORCED DURING the run (see `_run_with_frame_budget`).
    #:
    #: ‼ RAISED 3.5M -> 5M on 2026-07-29 (KI-35) BECAUSE IT WAS ABOUT TO KILL GOOD RUNS.
    #: The old value came with the note "the deepest real run to date reached the end of built
    #: content in ~2.24M frames, so this is ~1.5x headroom". Runs have since got much longer:
    #:     20260729-151635  3,058,007 frames — COMPLETED (six leaders incl. Winona, 462 wins)
    #:     20260727 bundle  3,117,110 / 3,063,506 / 2,946,810 / 2,932,778 — near-complete runs
    #: So a SUCCESSFUL run was using 87% of the cap and the real headroom was 1.14x, not 1.5x.
    #: One unluckier run — a few more heal round trips — and the budget would have terminated a
    #: winning run and reported it as wedged, throwing away exactly the data it exists to
    #: protect. 5M restores ~1.6x over the deepest observed run (3.12M).
    #:
    #: WHY RUNS GREW, measured in the same log: **78 heal round trips in one run**
    #: (Route 116<->Rustboro x34, Dewford<->Granite Cave x29, Route 117<->Mauville x15). With no
    #: potion layer every HP dip is a full Poké Center walk — `#24-provisions`. Expect to raise
    #: this again as more content is built, and re-derive it from the deepest COMPLETED run
    #: rather than guessing.
    #:
    #: ‼ Raising it is cheap NOW in a way it was not before: since KI-32, an in-battle wedge
    #: produces a STUCK dump (with the generator stack) after 18,000 frames, so the frame cap is
    #: no longer the only thing that notices a hang — it is just the thing that ENDS one. A
    #: wedge is diagnosed ~270x sooner than the cap fires.
    #:
    #: ‼ RAISED 5M -> 7M on 2026-09-26, AGAIN BECAUSE IT WAS KILLING RUNS SHORT OF THE CONTENT.
    #: In the 99-run endless corpus of 2026-09-15, all SIX `per-run frame budget exhausted` runs
    #: were MID-TO-LATE GAME when the cap fired — the Mossdeep Space Center (§Ch19), Tate & Liza
    #: twice, Juan twice, Sootopolis (§Ch21 leg 5) — i.e. 5M was being reached BEFORE §Ch23, and §Ch23 + §Ch24
    #: lie beyond that point. 7M is ~1.4x the frame count at which those runs were still
    #: progressing. ⛔ It is still a guess from a KILL point, not from a completed run; re-derive
    #: it from the deepest COMPLETED run as soon as one exists (the rule above still stands).
    #: ⚠ The §Ch24 league grind is NOT covered by this number — see
    #: `_frame_cap_for_this_run`, which extends the cap only once §Ch24 owns the run.
    MAX_FRAMES_PER_RUN = 7_000_000

    #: Extra budget, on top of `pokemon_league.CH24_TRAIN_PURSE_FRAMES`, for everything §Ch24 does
    #: AFTER training: the step-out, the League entry, five fights, HALL4, the credits and the
    #: SoftReset. MEASURED: the proven chain (`evidence/2026-09-25-ch24gauntlet-PASS.txt`) spent
    #: ~114k frames from Sidney's first battle to Wallace's end, inside a 600k driver budget.
    #: 1M is ~6x the fights and deliberately loose — this is a wedge backstop, not a scheduler.
    CH24_GAUNTLET_ALLOWANCE_FRAMES = 1_000_000

    def _frame_cap_for_this_run(self) -> int:
        """The per-run frame cap in force RIGHT NOW: the base cap, extended once §Ch24 owns the run.

        ⛔⛔ WHY THE BASE CAP ALONE MADE A HALL OF FAME STRUCTURALLY IMPOSSIBLE IN THIS MODE.
        This mode starts every run from a NEW GAME, so nothing earned in one run survives into the
        next (`pokemon_league.py` documents it: the story bot never saves). The §Ch24 league grind
        alone is measured at ~4.5M frames (`probe_ladder_economics.py`, 22.3 h for the two
        stragglers) and its purse is sized at 6M — on top of the millions a run has already spent
        reaching Ever Grande. Under a flat cap every run that got as far as the League would be
        KILLED MID-GRIND and logged as "wedged", which is the worst possible outcome for the one
        run a batch exists to observe.
        ⇒ The extension is granted ONLY after `mark_ch24_owns_run()` — the first act of
        `train_for_league()` — so early-game livelocks (the 13-27M-frame shapes documented on
        `_run_with_frame_budget`) are still ended at the base cap. From the latch on, the
        training purse is the designed backstop, and this cap must not pre-empt the FIRST purse.
        ⚠ It CAN pre-empt a SECOND one, deliberately: `prepare_and_open_the_league` calls
        `train_for_league` again when anyone is still below the floor, so two full purses (12M) are
        possible in principle. A run that spends one whole purse without reaching the floor is not
        one worth another 6M frames of an unattended batch; ending it here is the intended outcome.
        """
        cap = self.MAX_FRAMES_PER_RUN
        # ⭐ §Ch23's chunked training leg grants its own purse once it starts (`#24-ch23training`):
        # the 2026-09-15 corpus arrives at §Ch23 at a median 3.93M frames and a chunked climb can take
        # several million more — the same "never pre-empt a leg's designed backstop" rule as §Ch24.
        cap += int(getattr(self, "_ch23_training_allowance", 0) or 0)
        if getattr(self, "_ch24_owns_run", False):
            try:
                from modules.story.pokemon_league import CH24_TRAIN_PURSE_FRAMES
            except Exception:  # noqa: BLE001 — a budget read must never end a batch
                return cap
            cap += CH24_TRAIN_PURSE_FRAMES + self.CH24_GAUNTLET_ALLOWANCE_FRAMES
        return cap

    @staticmethod
    def name() -> str:
        return "Story (ENDLESS RESET)"

    #: How often (in yields ~= frames) to re-check the per-run frame budget. The check is a
    #: single memory read; sampling keeps it free even at unthrottled speed.
    BUDGET_CHECK_INTERVAL = 2048

    def _run_with_frame_budget(self, inner, start_frame: int):
        """Drive the story generator, ENFORCING `MAX_FRAMES_PER_RUN` while it runs.

        ‼ WHY THIS EXISTS (user's x4 bundle `20260727-063751`). `MAX_FRAMES_PER_RUN` was
        only evaluated AFTER `super().run()` returned, so it could report a runaway run but
        never stop one — despite its own docstring promising "a run that neither finishes
        nor raises cannot hold the batch forever". In that bundle three of four lanes did
        exactly that, and the batch lost more than half its wall-clock to them:

          * P3 run 1 — HARD HUNG at the Weather Institute: `state=3 controllable=False`,
            position frozen at ROUTE 119(32,1) (10, 10), for **27 million frames / ~6.5 h**.
            Not one STUCK dump fired in that whole stretch, so the global watchdog never
            saw it either — the watchdog is exactly what wedged.
          * P1 run 7 — 19.9M frames spinning Route 103 and healing at Oldale, forever.
          * P2 run 35 — 13.4M frames doing the same on Route 116.
            (P1/P2 are LIVELOCKS, not hangs: they generate real encounters and battles, so
            no "no progress" detector can ever fire. Only a budget catches them.)

        P4 run 12 shows the old behaviour's other half: it did report `frame-cap
        (7,545,828 > 3,500,000)` — after burning more than twice the cap.

        The framework advances bot-mode generators with a bare `next()` (`modules/main.py`
        drives `context.controller_stack`), so stepping `inner` by hand is safe; there are
        no `send()` values to lose. `close()` is forwarded in a `finally` so a parked batch
        still unwinds the story generator cleanly.
        """
        from modules.modes import BotModeError

        budget_base = start_frame
        ticks = 0
        # ⭐ THE RUN'S TRUE LENGTH, published for the outcome line. It is the SAME re-based count
        # the budget enforces, so the report and the enforcement can no longer disagree.
        self._run_elapsed_frames = 0

        def _elapsed() -> int | None:
            nonlocal budget_base
            try:
                now = context.emulator.get_frame_count()
            except Exception:
                return None
            # The hard reset happens INSIDE the run, and `get_frame_count()` restarts
            # with the emulator — so the counter legitimately goes backwards early on.
            # Re-base instead of measuring a negative elapsed (the same trap that made
            # the old post-hoc cap silently unenforceable after a mid-run reset).
            if now < budget_base:
                budget_base = 0
            self._run_elapsed_frames = now - budget_base
            return self._run_elapsed_frames

        try:
            while True:
                try:
                    next(inner)
                except StopIteration:
                    return
                yield
                ticks += 1
                if ticks % self.BUDGET_CHECK_INTERVAL:
                    continue
                elapsed = _elapsed()
                if elapsed is None:
                    continue
                cap = self._frame_cap_for_this_run()
                if elapsed > cap:
                    raise BotModeError(
                        f"per-run frame budget exhausted ({elapsed:,} > "
                        f"{cap:,}) — the run is wedged or looping; "
                        "resetting to the next run"
                    )
        finally:
            _elapsed()  # the final reading, on EVERY exit path (finish, derail, park)
            try:
                inner.close()
            except Exception:  # noqa: BLE001
                pass

    def run(self):
        from modules.console import console
        from modules.modes import BotModeError

        global ENDLESS_RESET_COMPLETED

        target = int(ENDLESS_RESET_TARGET)
        completed = 0
        ENDLESS_RESET_COMPLETED = 0
        outcomes: list[str] = []

        # ‼ CAPTURE AND RE-APPLY THE SPEED/VIDEO SETTINGS EVERY RUN (user report 2026-07-25:
        # "on its second run it was at normal speed, it should have been set to unlimited").
        # A derail calls `context.set_manual_mode()`, whose `enable_video_and_slow_down` default
        # sets `emulation_speed = 1` AND `video = True` (modules/context.py:128-139) — that is
        # correct for a human taking over, but it silently throttles the rest of an unattended
        # batch. The first version of this loop restored `bot_mode` and not the speed, so run 1
        # ran unthrottled and every run after it crawled at 1x. Remember what the batch STARTED
        # with and restore exactly that, rather than forcing a value the user did not choose.
        # ‼ SPEED ONLY — NEVER TOUCH `context.video` (user directive 2026-07-26).
        # This used to capture and re-apply `video` alongside the speed, which had two
        # bad effects. (1) It PINNED the renderer to whatever it was at batch start, so a
        # batch begun with video off kept it off for every subsequent run — and the
        # FAITHFUL PokéNav Match-Call tutorial only advances with the renderer ON, so it
        # silently degraded to the last-resort state-write fallback in **8 of 9** of the
        # user's real-hardware runs (#24-pokenav-faithful; the 1 success was a run whose
        # renderer was still on). (2) Worse, the `except` fell back to
        # `batch_video = False`, so a single failed read of `context.video` would force
        # the renderer OFF for the entire batch.
        # The SPEED restore stays — it fixes a real user report ("on its second run it was
        # at normal speed, it should have been set to unlimited"): a derail calls
        # `set_manual_mode()`, whose `enable_video_and_slow_down` default sets
        # `emulation_speed = 1`, which throttles the rest of an unattended batch.
        # Video is the user's to control; if they turn it on mid-batch it stays on.
        # ‼ APPLY THE DEBUG CONFIG **BEFORE** CAPTURING `batch_speed`. The capture below is
        # what every run's speed gets restored to after a `set_manual_mode()` drops it to 1x,
        # so if the config were applied afterwards the batch would be pinned to the OLD speed
        # and every run after the first would crawl — the exact 2026-07-25 bug this capture
        # was written to fix, reintroduced from the other direction.
        _apply_debug_emulation_config()
        try:
            batch_speed = context.emulation_speed
        except Exception:
            batch_speed = 0

        def _restore_speed() -> None:
            try:
                if context.emulation_speed != batch_speed:
                    context.emulation_speed = batch_speed
            except Exception:
                pass

        while target == 0 or completed < target:
            completed += 1
            label = f"{completed}/{'infinite' if target == 0 else target}"
            console.print(f"[bold cyan]=== ENDLESS RESET: starting run {label} ===[/]")
            # ‼ NAME THE EXPERIMENT IN THE LOG. An A/B whose variable is invisible in the
            # output is not an A/B — without this line a bundle gives no way to tell which
            # training-relocation rule produced it, and the comparison cannot be attributed
            # after the fact. Printed per run so it survives log rotation.
            try:
                from modules.story.training_areas import active_fodder_rule_banner

                _banner = active_fodder_rule_banner()
                console.print(f"[dim]{_banner}[/]")
                # ‼ ALSO INTO THE DEBUG LOG. `console.print` and the debug log are SEPARATE
                # STREAMS — `modules/debug_logger.py` never sees console output. The first
                # version of this banner printed to the console only, so a debug log (which
                # is what gets shared for review) carried NO record of which rule produced
                # it. A run's own log must be able to describe the run.
                try:
                    from modules import debug_logger

                    debug_logger.event(_banner, category="STORY")
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001 - a banner must never end a batch
                pass
            context.message = f"Endless reset: run {label}"
            start_frame = context.emulator.get_frame_count()
            # ‼ AUTHORITATIVE RUN BOUNDARY for the badge recorder. `modules/main.py` also
            # watches for the frame counter going backwards, but that proved unreliable —
            # the user's 2026-07-26 x4 bundle had P4 complete two runs with every badge
            # record still stamped `run_started_frame=0`. This mode KNOWS when a run
            # starts, so it says so, and per-run badge de-duplication becomes trustworthy.
            try:
                from modules import badge_log

                # `authoritative=True`: this mode KNOWS where its run boundaries are, so
                # main.py's frame-counter fallback must stand down. Without it both fired
                # and `run_index` advanced by two per run (1, 3, 5 … 37 across 19 runs).
                badge_log.reset_for_new_run(start_frame, authoritative=True)
            except Exception:
                pass
            # ‼ CLEAN SLATE PER RUN. Every counter scoped to one playthrough is zeroed
            # here. Without this the batch silently degrades: `_rival_attempts` hit its
            # cap of 3 after three runs and every later run gave up at the Rustboro rival
            # WITHOUT FIGHTING (P1: 16 of 20 runs), and `_defeat_counts` carried losses
            # forward so boss give-up thresholds tripped on borrowed defeats.
            # See `StoryMode.reset_per_run_state` for the measured evidence.
            self.reset_per_run_state()
            outcome = "finished"
            try:
                # The parent does the hard reset + NEW GAME, then hands to StoryMode.run().
                yield from self._run_with_frame_budget(super().run(), start_frame)
            # ⛔ ABORT-SWALLOW TRIAGE (gate #27, 2026-09-13): CATCHING IS THE WHOLE POINT.
            # This is the ENDLESS-RESET BATCH loop, OUTSIDE `StoryMode.run`. A `StoryAbort` arriving
            # here means the RUN ended (a whiteout), which is exactly what it records before starting
            # the next run. Re-raising would kill the BATCH over one run's EXPECTED outcome — the
            # opposite of what this loop exists to do.
            # ⇒ counted in the baseline; do NOT add `reraise_if_aborting` here.
            except BotModeError as exc:
                outcome = f"derailed: {exc}"  # EXPECTED — never ends the batch
            except Exception as exc:  # noqa: BLE001
                outcome = f"crashed: {type(exc).__name__}: {exc}"
            else:
                # ‼ "finished" MUST MEAN FINISHED (user's x4 bundle `20260726-231412`).
                # `outcome` defaults to "finished" and only a raised BotModeError changed
                # it — but a derail deep inside StoryMode can instead call
                # `context.set_manual_mode()` and `return` normally. Every one of those
                # was reported as a SUCCESS: all 16 P1 "finished" runs in that bundle were
                # dead runs, several printed as "finished (0 frames)", and any summary of
                # the batch read ~80% success against a true ~20%. A run that handed
                # itself to Manual did not finish — say so.
                # ‼ The genuine end-of-content return ALSO calls set_manual_mode(), so the
                # mode flags a real completion explicitly — otherwise this would relabel
                # true successes as failures, which is the same crime in the other
                # direction. P2 run 1 of that bundle really did reach the Feather Badge.
                try:
                    handed_to_manual = context.bot_mode != self.name()
                except Exception:
                    handed_to_manual = False
                if handed_to_manual and not getattr(self, "_reached_end_of_content", False):
                    outcome = "stopped: handed to Manual mid-run (see the run's log for why)"
            # ‼ CLAMP. `get_frame_count()` is "frames since this emulation session began" and
            # it RESETS with the emulator, so if a reset happens inside a run this
            # subtraction goes negative — the user's 2026-07-26 20:18 bundle recorded
            # "finished (-959,198 frames)". A negative value also silently disabled the
            # MAX_FRAMES_PER_RUN wedge guard below, since nothing is ever > the cap.
            # ⛔⛔ AND THE CLAMP WAS NOT ENOUGH — FIXED 2026-09-26. The hard reset happens inside
            # EVERY run of this mode, so `start_frame` (read BEFORE it) belongs to the PREVIOUS
            # emulator session. From run 2 on, `get_frame_count() - start_frame` was therefore
            # "this run's end minus the last run's end": negative (clamped to 0) or a small
            # meaningless positive. MEASURED in the 2026-09-15 corpus: `derailed: Ch23 (Victory
            # Road) failed ... (187,804 frames)` — impossible from a NEW GAME, which cannot reach
            # §Ch23 in 188k frames. Every per-run frame figure after run 1 in every endless batch
            # before this date is that difference, NOT a run length. ⇒ Report the budget wrapper's
            # own re-based count instead: the number that is ENFORCED is now the number that is
            # REPORTED, so the two can no longer disagree.
            frames = int(getattr(self, "_run_elapsed_frames", 0) or 0)
            run_cap = self._frame_cap_for_this_run()
            if frames > run_cap:
                outcome = f"frame-cap ({frames:,} > {run_cap:,})"
            outcomes.append(f"run {completed}: {outcome} ({frames:,} frames)")
            ENDLESS_RESET_COMPLETED = completed
            console.print(f"[cyan]=== ENDLESS RESET: run {label} -> {outcome} ({frames:,} frames) ===[/]")

            # A derail deep inside StoryMode can flip us to Manual; restore ourselves or the
            # next iteration runs under the wrong mode (or the batch just stops). Restore the
            # SPEED too — set_manual_mode() drops to 1x and turns video on, which is right for a
            # human but throttles an unattended batch for every remaining run.
            try:
                if context.bot_mode != self.name():
                    context.bot_mode = self.name()
            except Exception:
                pass
            _restore_speed()

        console.print("[bold green]=== ENDLESS RESET: batch complete ===[/]")
        for line in outcomes:
            console.print(f"  [green]{line}[/]")
        context.message = f"Endless reset: {completed} run(s) complete"
