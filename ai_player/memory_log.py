"""The AI's MEMORY OF ITS OWN PLAY: the action log, and the lines the learner's scorer reads.

TWO OUTPUTS, BOTH BUILT FROM THE AI'S OWN OBSERVATIONS (build step 1, design draft §7):

1. The ACTION LOG (`<run_dir>/actions.jsonl`, one JSON object per line): every record has `frame`,
   `digest` (the observation in one line), `decision`, `action`, `reason`, and, when the caller passes
   it, the whole `observation`. It is the AI's recorder: §3 makes the AI's own runs its training data,
   and a later step's brain reads back what it saw and did. The file is written by
   `ai_player/runlog.py` `RecordFile` (one of the two files the purity gate lets write files).

2. SCORER LINES, printed into the run's log (`<run_dir>/ai_player.log`), so the learner's scorer
   (`ai-agent/scoring.py` `parse_log`) scores an AI run EXACTLY like a bot run. The formats copy the
   bot's own lines, and `gates/test_eyes.py` feeds them through `scoring.parse_log` itself:
     `f<frame> [AI-STARTER] Story: choosing <Species>! (...)`  STARTER_RE  `Story: choosing (\\w+)!`
     `f<frame> [MAP] <NAME>(g,n) -> <NAME>(g,n) pos=(x, y)`      MAP_RE      (the bot's `debug_logger._fmt_map`)
     `f<frame> [TRAINER] end opp=<id> ... res=<Won|Lost|...> money=a->b ...`  TRAINER_END_RE, MONEY_RE
     `f<frame> [CATCH] end kind=wild sp=<Species>#<dex> end=caught res=Caught ...`  CATCH_OK_RE
     `f<frame> [DEX] owned a -> b: +#n, #m`                     DEX_RE
     `f<frame> [hb] mode=AI Player state=... controllable=... map=NAME(g,n) pos=(x, y) party=[...] ...`
                                                                 HB_RE (the bot's heartbeat: every 3600
       frames, `debug_logger._HEARTBEAT_EVERY`; the scorer takes the run's END map, position and party
       from it, the party a boss was fought with, and, from the last line it reads, the run's length).
       The AI also writes one when its brain ends (`final`, marked `end=1`), so `frames` is the run's
       last look rather than its last event.
   The scorer ignores every line before the starter line, so the AI writes it FIRST:
   * OBSERVED: the party went from empty to one Pokemon (a New Game run picks its starter);
   * INFERRED at run start, when the run starts from a save that already has a party: the first party
     Pokemon of a starter family (Treecko, Torchic, Mudkip and their evolutions) whose original trainer
     is the player. The line says which of the two it is. With no such Pokemon it says `Unknown`, so the
     run is still scored (and visibly so).
   ‼ The watcher observes every N frames, so an event shorter than N frames (a map visited for less
   than N frames) can be missed. Each line is emitted when the CHANGE is seen, at that frame.

BATTLES (step 1.1, the step-1 adversarial review). A battle is one record from its first look that
shows both sides to the first look AFTER it that has a RESULT:
   * the record is REFRESHED on every in-battle look (the foe, the opponent, the kind): the first look
     of a battle can show the PREVIOUS battle's foe, because `gBattleMons` is filled a few frames into
     the battle (`src/battle_main.c` BattleIntroGetMonsData), so the lines name the foe of the LAST look;
   * it ENDS only on a look out of the battle screen whose `gBattleOutcome` is not 0 and whose party,
     PC boxes and money could be read (between two screens the eyes withhold them: `host/eyes.py`
     _save_blocks_may_be_moving; the next look ends it then). The step-1 rule
     ended it at the first look with `in_battle` False and wrote whatever the byte held: `res=InProgress`
     if 0, which the scorer counts as a LOSS (`res != "Won"`). So `res=InProgress` is never written.
     (Measured 2026-10-07 on a real catch through the nickname screen, `gates/probe_step11.py catch`:
     `in_battle` stays True on NAMING_SCREEN, since gMain.callback1 stays BattleMainCB1, and the result is
     set before `in_battle` first reads False. No natural look of that kind was found; the rule makes the
     order of the two irrelevant instead of relying on it);
   * a CATCH is logged only when a NEW Pokemon of the PLAYER's (a PID not owned at the battle's start,
     whose OT id is the player's VISIBLE id) is in the party or a PC box afterwards, and `dest` is where
     THAT PID is. `gBattleOutcome == Caught` alone is not a catch: Wally's tutorial ends Caught and the
     Ralts is Wally's (`eyes/view.py` OUTCOME_CAUGHT). (Until step 1.1 `dest` came from the party COUNT.)
"""

from __future__ import annotations

import json

from ai_player.eyes.observation import Observation
from ai_player.eyes.view import BATTLE_TYPE_WALLY_TUTORIAL, OUTCOME_CAUGHT, OUTCOME_NAMES

__all__ = ["HEARTBEAT_EVERY", "ActionLog", "ScorerLines", "STARTER_FAMILIES", "owned_pids", "starter_family"]

#: Frames between two heartbeat lines: the bot's (`modules/debug_logger.py` `_HEARTBEAT_EVERY`).
HEARTBEAT_EVERY = 3600

#: National Pokedex number -> the starter it evolved from (Hoenn starters and their evolutions).
STARTER_FAMILIES: dict[int, str] = {
    252: "Treecko", 253: "Treecko", 254: "Treecko",
    255: "Torchic", 256: "Torchic", 257: "Torchic",
    258: "Mudkip", 259: "Mudkip", 260: "Mudkip",
}


def starter_family(dex: int) -> str | None:
    return STARTER_FAMILIES.get(dex)


def owned_pids(observation: Observation) -> dict[int, str] | None:
    """The player's OWN Pokemon by identity: PID -> "party" or "box", for every Pokemon in the party or a
    PC box whose OT id is the player's visible id. None when any of the three was not read (None is
    never "nothing": step 1.1)."""
    player, party, storage = observation.player, observation.party, observation.storage
    if player is None or party is None or storage is None:
        return None
    mine = {mon.pid: "box" for mon in storage if mon.ot_id == player.trainer_id}
    mine.update({mon.pid: "party" for mon in party if mon.ot_id == player.trainer_id})
    return mine


class ActionLog:
    """Writes one JSON record per decision. `sink` is `ai_player.runlog.RecordFile` (or anything with an
    `append(line)` method); the log never opens a file itself."""

    def __init__(self, sink) -> None:
        self._sink = sink
        self.records = 0

    def record(self, observation: Observation | None, decision: str, action: str, reason: str,
               full: bool = False, frame: int | None = None, extra: dict | None = None) -> dict:
        entry: dict = {
            "frame": observation.frame if observation is not None else frame,
            "digest": observation.digest() if observation is not None else None,
            "decision": decision,
            "action": action,
            "reason": reason,
        }
        if extra:
            entry["extra"] = extra
        if full and observation is not None:
            entry["observation"] = observation.to_dict()
        self._sink.append(json.dumps(entry, separators=(",", ":"), sort_keys=False))
        self.records += 1
        return entry


class ScorerLines:
    """Turns consecutive Observations into the scorer's lines. Feed it every observation in order;
    `update` returns the lines to print for what changed since the previous one."""

    def __init__(self) -> None:
        self.started = False
        #: The last party that was READ (an Observation's party may be None: not read).
        self._last_party: tuple | None = None
        self._map: tuple[str, int, int] | None = None
        self._owned: tuple[int, ...] | None = None
        #: The open battle: {"start": its first look with both sides, "latest": its latest such look (the
        #: refresh), "owned": the player's own PIDs at its first look where they could be read}.
        self._battle: dict | None = None
        self._last_heartbeat: int | None = None
        #: The latest look with a settled position and a read party: the closing heartbeat's source.
        self._last_complete: Observation | None = None

    def update(self, observation: Observation) -> list[str]:
        lines: list[str] = []
        frame = observation.frame
        if not self.started:
            starter = self._starter_line(observation)
            if starter is not None:
                lines.append(starter)
                self.started = True
                self._last_heartbeat = frame
        if self.started:
            lines += self._map_lines(observation)
            lines += self._dex_lines(observation)
            lines += self._battle_lines(observation)
            if self._last_heartbeat is not None and frame - self._last_heartbeat >= HEARTBEAT_EVERY:
                lines += self._heartbeat(observation, final=False)
        if observation.party is not None:
            self._last_party = observation.party
        if self._complete(observation):
            self._last_complete = observation
        return [line if line.startswith("f") else f"f{frame} {line}" for line in lines]

    def final(self, observation: Observation | None) -> list[str]:
        """The heartbeat for the brain's LAST look, when it ends (marked `end=1`). If that look has no
        settled position or no party (mid-warp, a torn read), the heartbeat is the latest look that had
        both, at ITS frame: the scorer's end state is then what the AI last knew, never a mix."""
        if observation is None or not self.started:
            return []
        source = observation if self._complete(observation) else self._last_complete
        if source is None:
            return []
        return [f"f{source.frame} {line}" for line in self._heartbeat(source, final=True)]

    @staticmethod
    def _complete(observation: Observation) -> bool:
        player = observation.player
        return player is not None and not player.settling and observation.party is not None

    def _heartbeat(self, observation: Observation, final: bool) -> list[str]:
        if not self._complete(observation):
            return []  # no position (mid-warp) or no party read: a later look writes it
        player = observation.player
        self._last_heartbeat = observation.frame
        party = str([f"{m.species}:L{m.level}" for m in observation.party])
        progress, bag = observation.progress, observation.bag
        owned = progress.dex_owned if progress is not None else "?"
        money = progress.money if progress is not None else "?"
        badges = len(progress.badges) if progress is not None else "?"
        balls = bag.ball_total if bag is not None else "?"
        return [
            f"[hb] mode=AI Player state={observation.screen.game_state} controllable={observation.screen.screen == 'overworld'} "
            f"map={player.map_name}({player.map_group},{player.map_number}) pos=({player.x}, {player.y}) party={party} "
            f"owned={owned} balls={balls} money={money} badges={badges} source=ai-eyes" + (" end=1" if final else "")
        ]

    # ------------------------------------------------------------------ the starter
    def _starter_line(self, observation: Observation) -> str | None:
        """None while there is nothing to say yet: no party read (None), no Pokemon yet (()), or no player
        to compare the OT with. "Observed" needs the last party READ to have been EMPTY: an unread party
        (None) is not "0 Pokemon"."""
        if not observation.party or observation.player is None:
            return None  # not read, or no Pokemon yet: a New Game run keeps waiting for the starter
        frame = observation.frame
        if self._last_party == ():
            first = observation.party[0]
            name = starter_family(first.dex) or first.species
            return (f"f{frame} [AI-STARTER] Story: choosing {name}! (observed: the party went from 0 to 1 "
                    f"Pokemon, {first.species} Lv{first.level})")
        own = observation.player.trainer_id
        for mon in observation.party:
            family = starter_family(mon.dex)
            if family is not None and mon.ot_id == own:
                return (f"f{frame} [AI-STARTER] Story: choosing {family}! (inferred at run start: party slot "
                        f"{mon.slot + 1} {mon.species} Lv{mon.level} is the player's own {family}-family Pokemon)")
        return (f"f{frame} [AI-STARTER] Story: choosing Unknown! (inferred at run start: no starter-family "
                f"Pokemon of the player's own in the party)")

    # ------------------------------------------------------------------ maps
    def _map_lines(self, observation: Observation) -> list[str]:
        player = observation.player
        if player is None or player.settling:
            return []  # mid-warp: the line waits for the settled position (`pos=` is the new map's)
        current = (player.map_name, player.map_group, player.map_number)
        if current == self._map:
            return []
        before = "None" if self._map is None else f"{self._map[0]}({self._map[1]},{self._map[2]})"
        self._map = current
        return [f"[MAP] {before} -> {player.map_name}({player.map_group},{player.map_number}) pos=({player.x}, {player.y})"]

    # ------------------------------------------------------------------ the Pokedex
    def _dex_lines(self, observation: Observation) -> list[str]:
        progress = observation.progress
        if progress is None:
            return []
        owned = progress.owned_dex
        lines = []
        if self._owned is not None and owned != self._owned:
            gained = sorted(set(owned) - set(self._owned))
            if gained or len(owned) != len(self._owned):
                lines.append(f"[DEX] owned {len(self._owned)} -> {len(owned)}: +{', '.join(f'#{n}' for n in gained)}")
        self._owned = owned
        return lines

    # ------------------------------------------------------------------ battles
    def _battle_lines(self, observation: Observation) -> list[str]:
        """A battle STARTS at the first look that shows both sides, is REFRESHED by every later such look,
        and ENDS at the first look out of the battle screen whose `gBattleOutcome` is a result (not 0).
        The module docstring has the three reasons (step 1.1)."""
        record = self._battle
        if observation.battle is not None:
            if record is None:
                record = self._battle = {"start": observation, "latest": observation, "owned": None}
            if observation.battle.foe or not record["latest"].battle.foe:
                record["latest"] = observation  # the refresh: the first look can show the previous battle's foe
            if record["owned"] is None:
                record["owned"] = owned_pids(observation)
            return []
        if record is None or observation.screen.in_battle or observation.last_battle_outcome == 0:
            return []  # no battle open; still in it; or out of the battle screen with no result yet
        code = observation.last_battle_outcome
        owned_after = owned_pids(observation)
        if owned_after is None or observation.progress is None:
            return []  # who owns what, or the money, is not readable on this look (between screens): the next look ends it
        self._battle = None
        start, latest = record["start"], record["latest"]
        battle = latest.battle
        outcome = OUTCOME_NAMES.get(code, f"Outcome{code}")
        money_before = start.progress.money if start.progress is not None else -1
        money_after = observation.progress.money if observation.progress is not None else -1
        where = start.player.map_name if start.player is not None else "?"
        foe = battle.foe[0] if battle.foe else None
        foe_text = f"{foe.species}#{foe.dex}" if foe is not None else "?#0"
        if battle.kind == "trainer":
            return [
                f"[TRAINER] end opp={battle.opponent_trainer_id} last_seen={foe_text} lvl_last_seen={foe.level if foe else '?'} "
                f"res={outcome} money={money_before}->{money_after} delta={money_after - money_before} map={where} "
                f"source=ai-eyes"
            ]
        tutorial = " tutorial=wally" if battle.type_flags & BATTLE_TYPE_WALLY_TUTORIAL else ""
        if code != OUTCOME_CAUGHT:
            return [f"[AI-BATTLE] end kind=wild sp={foe_text} res={outcome} map={where}{tutorial}"]
        before = record["owned"]
        new = sorted(set(owned_after) - set(before)) if before is not None else None
        if not new:
            # Caught, and no NEW Pokemon of the player's anywhere: someone else's catch (Wally's tutorial),
            # or (before is None) who owned what at the start was never readable. No [CATCH] line either way.
            why = "none: no new Pokemon of the player's" if new is not None else "unknown: the start was not readable"
            return [f"[AI-BATTLE] end kind=wild sp={foe_text} res={outcome} map={where}{tutorial} player_catch={why}"]
        pid = new[0] if len(new) == 1 else None
        dest = owned_after[pid] if pid is not None else "?"
        party = observation.party or ()
        return [
            f"[AI-BATTLE] end kind=wild sp={foe_text} res={outcome} map={where}{tutorial} player_catch=yes",
            f"[CATCH] end kind=wild sp={foe_text} end=caught res=Caught dest={dest} pid={'-' if pid is None else f'{pid:08X}'} "
            f"party={len(party)}/6 map={where} source=ai-eyes",
        ]
