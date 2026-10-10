"""TEST SIDE: build the fixtures of build step 4.1's live arms (`gates/live_step4.py` SHIFT, SHIFTX, HEAL, SWITCH, RUN) by
PLAYING, with button presses only (no memory write), in a throwaway emulator, the cartridge's clock pinned.

    py -3.12 ai_player/gates/make_step41_fixtures.py [--only rival|heal|switch|run|sing|rival_hurt] [--seeds 1-20]

WHY NEW FIXTURES (the step-4 adversarial review: "switch, heal and run never ran live"; "the SHIFT prompt is answered about
the FAINTED foe ... make a fixture by button presses"): no save starts a battle against a trainer with two Pokemon where
the next one matters, none has a Potion in an early party's bag, and none starts a wild battle with a badly matched or
low lead. Each fixture below is PLAYED to: the party ORDER is changed by test-side presses on the START menu's POKéMON
screen (every cursor read by the AI's eyes, `FrameworkEyes`, read only), and every walk, purchase and battle before the
saved frame is the AI's own brain (`ai_player.mode.HandsBrain`: goto, mart, battle) or a test-side press that is named.

  rival_rustboro.ss1  (arms SHIFT, SHIFTX; `--only rival`) from `tools/story-dev/saves/fresh_rivalprep.ss1` (pinned below: Route 116
                      at (11,7), next to Rustboro; VAR_RUSTBORO_CITY_STATE 7, the Rustboro rival not met; a boy who chose
                      Mudkip; Poochyena L16, Marshtomp L18, Taillow L17, Dustox L12; no items; 4084 money; it is saved IN
                      a wild battle against a Nincada L7, which the AI's own battle brain plays first):
                      (1) the MARSHTOMP is put first (START, POKéMON, the Marshtomp, SWITCH, the first slot);
                      (2) the AI's GOTO brain walks to Route 116's west edge (0,8) and a test-side Left crosses into Rustboro
                      (`data/maps/Route116/map.json`: Rustboro to the left, offset 0); the goto brain walks to (16,46), below
                      the Poke Mart's door (`data/maps/RustboroCity/map.json` warp (16,45)); test-side Up goes in and four Ups
                      reach the counter (as `make_mart_fixture.py`);
                      (3) the AI's own MART brain buys POTIONS (`HandsOptions.mart_item`), so the bag holds them;
                      (4) test-side Downs leave the mart; the goto brain walks to (16,52) and a test-side Down steps onto the
                      rival's trigger row (y 53, `RustboroCity_EventScript_RivalTrigger0-7`); MAY's words are pressed through
                      (A on the eyes' waits) and her "want to battle?" answered YES by the cursor read; the state is saved on
                      the FIRST frame of the battle: TRAINER_MAY_RUSTBORO_MUDKIP, Wingull L13 then Treecko L15
                      (`src/data/trainer_parties.h` sParty_MayRustboroMudkip): the second foe is Grass, x4 on the Marshtomp.
  rival_rustboro_hurt.ss1  (step 4.1 round 3, arms SHIFTC, SHIFTCX; `--only rival_hurt`, `build_rival_hurt`) the same road
                      to the same battle, but the TAILLOW first hurt by the AI's own battle brain on Route 116's wild
                      Pokemon into a WINDOW: at least half its HP (the shift question still finds it much better against the
                      Treecko) and under the Poochyena by the party menu's by-level ranking (L x (0.5 + 0.5 x HP share)), so a
                      party menu that ranks again sends the Poochyena and only the carried PID sends the Taillow.
  heal_r103.ss1       (arm HEAL; `--only heal`; the step-4.1 verifier's minor: this docstring named rival_rustboro.ss1 for HEAL)
                      from `tools/story-dev/saves/route103.ss1` (Route 103 (5,7) BEFORE the rival: Mudkip L6, no items):
                      the AI's goto brain into Oldale, its own MART brain buys 2 POTIONS, the goto brain back to (5,7), then
                      its battle brain walks up to MAY and talks; saved on the first frame of the battle (`build_heal`).
  switch_joey.ss1     (arm SWITCH; `--only switch`) from `tools/story-dev/saves/route116team.ss1` (pinned: Route 116 (11,7), YOUNGSTER JOEY at
                      (12,7) undefeated; Mudkip L13, Poochyena L4, Nincada L6, Whismur L6): the POOCHYENA (Dark) is put
                      first; the AI's battle brain walks up to Joey (`AI_PLAYER_TALK_TO` 12,7) and talks; saved on the first
                      frame of the battle: Joey's Machop L9 (Fighting, x2 on Dark) against the Poochyena: a forced bad matchup.
  run_r116.ss1        (arm RUN; `--only run`) from `route116team.ss1` with the POOCHYENA first (as above): the AI's battle brain roams Route
                      116's grass and fights (training); saved on the first frame of a WILD battle that begins with the
                      Poochyena under 30 % of its HP (the Story temperament's `run_low`) while the strongest Pokemon (the
                      Mudkip) is healthy, so training goes on (`needs_rest`).
Each is saved with a `.build.json` printout (every test-side press, the brains' told lines, the second-path truth at the
end). A rebuild does not reproduce the bytes (the emulator's clock state is in a save state): re-pin the md5s in
`live_step4.py` after one.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.hands_harness import HarnessControls, pin_game_clock, truth  # noqa: E402
from ai_player.gates.make_step4_fixtures import GAME_CLOCK, PROFILE, Presser, _battle_start, check, md5  # noqa: E402
from ai_player.gates.probe_eyes import boot, resolve_build_root  # noqa: E402

if str(resolve_build_root()) not in sys.path:
    sys.path.insert(0, str(resolve_build_root()))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SAVES = REPO / "tools" / "story-dev" / "saves"
RIVALPREP = (SAVES / "fresh_rivalprep.ss1", "606e86c24dde32de5359566e3d4ce8f8")
ROUTE116TEAM = (SAVES / "route116team.ss1", "9710585350be10534737c4362c33189e")
ROUTE103 = (SAVES / "route103.ss1", "0d951fe21be35a6eafade207ddff5961")
RIVAL = FIXTURES / "rival_rustboro.ss1"
SWITCH = FIXTURES / "switch_joey.ss1"
RUN = FIXTURES / "run_r116.ss1"
HEAL = FIXTURES / "heal_r103.ss1"
HEAL_POTIONS = 2
MARSHTOMP, POOCHYENA_116 = 0x550A9BE6, 0x5815089E
#: `include/constants/opponents.h`
TRAINER_JOEY, TRAINER_MAY_RUSTBORO_MUDKIP, TRAINER_MAY_ROUTE103_MUDKIP = 322, 600, 529
POTIONS = 3
RUN_LOW = 0.30


def pin(source: tuple[Path, str | None]) -> str:
    """The source's md5, checked against its pin (pinned here: these saves are not in FIXTURES.md5)."""
    if source[1] is not None:
        check(source)
    return md5(source[0])


class Player:
    """One throwaway emulator, the state loaded and the clock pinned; test-side presses (`Presser`) and the AI's own
    brains (`brain`) take turns on it, and every step is logged."""

    def __init__(self, state: Path) -> None:
        self.context = boot(PROFILE)
        self.emulator = self.context.emulator
        self.emulator.load_save_state(state.read_bytes())
        pin_game_clock(self.emulator, GAME_CLOCK)
        self.presser = Presser(self.context)
        self.log: list[str] = []
        self.lines: list[str] = []

    def party_pids(self) -> list[int]:
        from modules.pokemon_party import get_party

        return [m.personality_value for m in get_party()]

    def where(self) -> tuple:
        look = self.presser.look()
        player = look.player
        return (player.map_const, player.x, player.y) if player is not None else (None, None, None)

    def brain(self, frames: int, stop=None, **options) -> dict:
        """The AI's own brain on this emulator (as `make_step4_fixtures.play_until`), one frame per `next`; `stop(context)`
        asked after every frame (a dict ends the play there)."""
        from ai_player.host.eyes import FrameworkEyes
        from ai_player.mode import BrainSettings, HandsBrain
        from ai_player.options import HandsOptions

        run_dir = Path(tempfile.mkdtemp(prefix="ai_step41_fixture_"))
        settings = dict(brain="battle", run_dir=run_dir, seed=1, personality="Story", mart_item="POKé BALL", mart_count=5,
                        clock=None, fault_ungated_a=False, fault_blind_count=False)
        settings.update(options)
        lines: list[str] = []
        brain = HandsBrain(BrainSettings(frames=frames), lines.append, HandsOptions(**settings))
        steps = brain.play(HarnessControls(self.emulator), FrameworkEyes())
        count, reason, found = 0, None, None
        while True:
            try:
                next(steps)
            except StopIteration as done:
                reason = done.value
                break
            self.emulator.run_single_frame()
            count += 1
            if stop is not None:
                found = stop(self.context)
                if found is not None:
                    break
            if count > frames + 10:
                reason = "the builder's bound"
                break
        self.lines += [f"[{settings['brain']}] {line}" for line in lines if "AI-HANDS" in line or "AI-EXIT" in line or "battle" in line]
        self.log.append(f"f{self.emulator.get_frame_count()} brain {settings['brain']} {options}: {count} frames -> {reason!r}"
                        f"{' (stopped: ' + json.dumps(found) + ')' if found else ''}")
        return {"reason": reason, "frames": count, "found": found}

    def step(self, button: str, why: str, frames: int = 40) -> tuple:
        """One test-side step: the button HELD until the player's tile or map changes (at most `frames`), then a settle."""
        before = self.where()
        self.emulator.hold_button(button)
        for _ in range(frames):
            self.emulator.run_single_frame()
            if self.where() != before and self.where()[1] is not None:
                break
        self.emulator.release_button(button)
        self.presser.wait(16)
        after = self.where()
        self.log.append(f"f{self.emulator.get_frame_count()} step {button} ({why}): {before} -> {after}")
        return after

    def settle(self, frames: int, why: str) -> None:
        self.presser.wait(frames)
        self.log.append(f"f{self.emulator.get_frame_count()} wait {frames} ({why}): {self.where()}")


def reorder(player: Player, lead: int) -> None:
    """TEST SIDE: put the Pokemon with PID `lead` first, through the START menu's POKéMON screen (START, POKéMON, the
    member, SWITCH, the first slot); then B out of both menus. The START menu's cursor is read by THIS file
    (`src/start_menu.c` sStartMenuCursorPos, sCurrentStartMenuActions: the eyes name the menu but build no cursor view of
    it, measured 2026-10-09), every later cursor by the AI's eyes, before each press."""
    from modules.memory import read_symbol

    presser = player.presser
    pids = player.party_pids()
    if pids[0] == lead:
        return
    index = pids.index(lead)
    presser.wait(30)
    for _ in range(6):
        if presser.look().screen.menu == "start_menu":
            break
        presser.press("Start", "open the START menu")
        presser.wait(20)
    else:
        raise SystemExit("the START menu did not open")
    actions = list(read_symbol("sCurrentStartMenuActions", size=9))[:read_symbol("sNumStartMenuActions", size=1)[0]]
    target = actions.index(1)  # MENU_ACTION_POKEMON (`src/start_menu.c`)
    for _ in range(10):
        cursor = read_symbol("sStartMenuCursorPos", size=1)[0]
        if cursor == target:
            break
        presser.press("Down" if cursor < target else "Up", f"START menu cursor {cursor} (sStartMenuCursorPos), POKéMON at {target}")
    presser.press("A", "the START menu's POKéMON")
    presser.until_ui("party")
    presser.list_to("party", index)
    presser.press("A", f"the member in slot {index}")
    look = presser.until_ui("party_action")
    presser.list_to("party_action", list(look.screen.ui.options).index("SWITCH"))
    presser.press("A", "SWITCH")
    presser.wait(20)
    # the switch's SECOND cursor is gPartyMenu.slotId2 (`include/party_menu.h` struct PartyMenu: slotId @9, slotId2 @10),
    # which the eyes' party view does not follow (it reads slotId): read here, test side
    for _ in range(12):
        second = read_symbol("gPartyMenu", size=12)[10]
        if second == 0:
            break
        presser.press("Up", f"the switch's second cursor (gPartyMenu.slotId2) on {second}, wanted 0")
    presser.press("A", "switch with the first slot")
    for _ in range(600):
        presser.wait(1)
        if player.party_pids()[0] == lead:
            break
    else:
        raise SystemExit(f"the party order did not change: {[f'{p:08x}' for p in player.party_pids()]}")
    presser.wait(60)
    from ai_player.hands.dialogue import player_free

    for _ in range(10):
        look = presser.look()
        if player_free(look):
            break
        if look.screen.menu is not None or look.screen.ui is not None:
            presser.press("B", f"close the menu ({look.screen.menu}, {look.screen.ui.kind if look.screen.ui else 'no view'})")
        presser.wait(30)
    else:
        raise SystemExit(f"the player is not free after the reorder: {presser.look().digest()[:200]}")
    player.log += presser.log
    presser.log.clear()
    player.log.append(f"f{player.emulator.get_frame_count()} party order now {[f'{p:08x}' for p in player.party_pids()]}")


def build_rival(seeds: range) -> dict:
    source_md5 = pin(RIVALPREP)
    from modules.memory import read_symbol

    def fail(player: Player, seed: int, why: str) -> None:
        print(f"[rival] seed {seed}: {why}; {player.log[-5:]}; {player.lines[-6:]}", flush=True)

    for seed in seeds:
        player = Player(RIVALPREP[0])
        # the save starts IN a wild battle (a Nincada L7, measured 2026-10-09): the AI's battle brain plays it first
        player.brain(15000, brain="battle", battles=1, seed=seed)
        reorder(player, MARSHTOMP)
        # (2) to Rustboro: the goto brain to Route 116's west edge, a Left across (row 8: the rows above it end in trees
        # at x 1, seen 2026-10-09)
        player.brain(12000, brain="goto", goto=((0, 8),), seed=seed)
        if player.where()[:3] != ("ROUTE116", 0, 8):
            fail(player, seed, f"not at Route 116 (0,8): {player.where()}")
            continue
        player.step("Left", "cross into Rustboro")
        if player.where()[0] != "RUSTBORO_CITY":
            fail(player, seed, f"not in Rustboro: {player.where()}")
            continue
        player.brain(20000, brain="goto", goto=((16, 46),), seed=seed)
        if player.where() != ("RUSTBORO_CITY", 16, 46):
            fail(player, seed, f"not below the mart's door: {player.where()}")
            continue
        player.step("Up", "the mart's door")
        player.settle(240, "the door's fade")
        for _ in range(4):
            player.step("Up", "to the counter (make_mart_fixture.py's walk)")
        # (3) the AI's own mart brain buys Potions
        player.brain(8000, brain="mart", mart_item="POTION", mart_count=POTIONS, seed=seed)
        items = _items(player)
        if items.get("POTION", 0) < POTIONS:
            fail(player, seed, f"the bag's items {items}")
            continue
        # (4) out, south to the rival's trigger row
        for _ in range(6):
            if player.where()[0] != "RUSTBORO_CITY_MART":
                break
            player.step("Down", "leave the mart")
        player.settle(240, "the door's fade")
        player.brain(12000, brain="goto", goto=((16, 52),), seed=seed)
        if player.where() != ("RUSTBORO_CITY", 16, 52):
            fail(player, seed, f"not at (16,52): {player.where()}")
            continue
        player.step("Down", "onto the rival's trigger row (y 53)")
        last: dict = {}
        found = _talk_into_battle(player, last)
        if found is None:
            fail(player, seed, "no battle after the trigger")
            continue
        opponent = int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")
        if opponent != TRAINER_MAY_RUSTBORO_MUDKIP:
            raise SystemExit(f"the battle's opponent is {opponent}, not MAY_RUSTBORO_MUDKIP {TRAINER_MAY_RUSTBORO_MUDKIP}")
        RIVAL.write_bytes(player.emulator.get_save_state())
        return {"fixture": RIVAL.name, "md5": md5(RIVAL), "source": [RIVALPREP[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"test-side reorder + the AI's goto / mart brains (seed {seed}), clock {GAME_CLOCK}",
                "at": found, "opponent": opponent, "steps": player.log, "ai_lines": player.lines, "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the rival's battle")


#: (step 4.1 round 3) the rival-prep party's Taillow and Poochyena (the framework's decoder, `rival_rustboro.build.json`)
TAILLOW_RIVALPREP, POOCHYENA_RIVALPREP = 0xA8DBCF1B, 0x2B19CA91
RIVAL_HURT = FIXTURES / "rival_rustboro_hurt.ss1"
#: wild battles the hurt Taillow may fight on Route 116 before the seed is given up
HURT_BATTLES = 12


def _by_level(member) -> float:
    """`brain/battle.py` replacement's score with no foe standing: the level x (0.5 + 0.5 x the HP share)."""
    return member.level * (0.5 + 0.5 * member.current_hp / max(1, member.total_hp))


def build_rival_hurt(seeds: range) -> dict:
    """(step 4.1 round 3, the step-4.1 verifier's weak proof: "Finding 1, the PID carried to the party menu, cannot fail
    live ... In this fixture the by-level fallback (the fainted Wingull leaves no foe standing) also picks the L17
    Taillow") `rival_rustboro_hurt.ss1`: the same road to Rustboro's rival as `rival_rustboro.ss1` (`build_rival`), but
    first the TAILLOW is put first and the AI's own battle brain fights Route 116's wild Pokemon with it until its HP is
    between half and the share where the by-level ranking puts it BELOW the Poochyena (L16, 39/42): the shift question
    still finds the Taillow much better against the Treecko (a member at half its HP or more counts), but a party menu
    that ranks again by level would send the POOCHYENA. Then the Marshtomp is put first and the road is `build_rival`'s.
    Every HP is read by the framework's decoder after each battle (`get_party`); a seed whose Taillow falls under half is
    given up."""
    source_md5 = pin(RIVALPREP)
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    def fail(player: Player, seed: int, why: str) -> None:
        print(f"[rival_hurt] seed {seed}: {why}; {player.log[-5:]}; {player.lines[-6:]}", flush=True)

    for seed in seeds:
        player = Player(RIVALPREP[0])
        player.brain(15000, brain="battle", battles=1, seed=seed)
        reorder(player, TAILLOW_RIVALPREP)
        hurt = None
        for battle in range(HURT_BATTLES):
            player.brain(20000, brain="battle", battles=1, seed=seed * 100 + battle)
            party = {m.personality_value: m for m in get_party()}
            taillow, poochyena = party.get(TAILLOW_RIVALPREP), party.get(POOCHYENA_RIVALPREP)
            if taillow is None or poochyena is None or taillow.current_hp < taillow.total_hp / 2:
                break
            if _by_level(taillow) < _by_level(poochyena):
                hurt = {"taillow": [taillow.level, taillow.current_hp, taillow.total_hp, round(_by_level(taillow), 2)],
                        "poochyena": [poochyena.level, poochyena.current_hp, poochyena.total_hp,
                                      round(_by_level(poochyena), 2)], "battles": battle + 1}
                break
        if hurt is None:
            fail(player, seed, f"the Taillow not hurt into the window: {[(m.species.name, m.current_hp, m.total_hp) for m in get_party()]}")
            continue
        player.log.append(f"f{player.emulator.get_frame_count()} the Taillow hurt into the window: {hurt}")
        reorder(player, MARSHTOMP)
        player.brain(12000, brain="goto", goto=((0, 8),), seed=seed)
        if player.where()[:3] != ("ROUTE116", 0, 8):
            fail(player, seed, f"not at Route 116 (0,8): {player.where()}")
            continue
        player.step("Left", "cross into Rustboro")
        if player.where()[0] != "RUSTBORO_CITY":
            fail(player, seed, f"not in Rustboro: {player.where()}")
            continue
        player.brain(20000, brain="goto", goto=((16, 46),), seed=seed)
        if player.where() != ("RUSTBORO_CITY", 16, 46):
            fail(player, seed, f"not below the mart's door: {player.where()}")
            continue
        why = _shop(player, seed, POTIONS)
        if why is not None:
            fail(player, seed, why)
            continue
        player.brain(12000, brain="goto", goto=((16, 52),), seed=seed)
        if player.where() != ("RUSTBORO_CITY", 16, 52):
            fail(player, seed, f"not at (16,52): {player.where()}")
            continue
        player.step("Down", "onto the rival's trigger row (y 53)")
        last: dict = {}
        found = _talk_into_battle(player, last)
        if found is None:
            fail(player, seed, "no battle after the trigger")
            continue
        opponent = int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")
        if opponent != TRAINER_MAY_RUSTBORO_MUDKIP:
            fail(player, seed, f"the battle's opponent is {opponent}")
            continue
        party = {m.personality_value: m for m in get_party()}
        taillow, poochyena = party[TAILLOW_RIVALPREP], party[POOCHYENA_RIVALPREP]
        if not (taillow.current_hp >= taillow.total_hp / 2 and _by_level(taillow) < _by_level(poochyena)):
            fail(player, seed, f"the window lost on the way: {taillow.current_hp}/{taillow.total_hp}")
            continue
        RIVAL_HURT.write_bytes(player.emulator.get_save_state())
        return {"fixture": RIVAL_HURT.name, "md5": md5(RIVAL_HURT),
                "source": [RIVALPREP[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"test-side reorders + the AI's battle (Route 116's wild Pokemon, the Taillow first) / goto / "
                             f"mart brains (seed {seed}), clock {GAME_CLOCK}",
                "at": found, "hurt": hurt, "opponent": opponent, "steps": player.log, "ai_lines": player.lines,
                "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the rival's battle with the Taillow in the window")


def _shop(player: Player, seed: int, count: int) -> str | None:
    """Standing below a Poke Mart's door: test-side Up into it and four Ups to the counter (every mart is `LAYOUT_MART`:
    the door mat (3,7), the clerk at (1,3), as `make_mart_fixture.py`), the AI's own MART brain buys `count` Potions,
    test-side Downs out. None when done, else why not."""
    player.step("Up", "the mart's door")
    player.settle(240, "the door's fade")
    mart = player.where()[0]
    for _ in range(4):
        player.step("Up", "to the counter (make_mart_fixture.py's walk)")
    before = _items(player).get("POTION", 0)
    player.brain(8000, brain="mart", mart_item="POTION", mart_count=count, seed=seed)
    items = _items(player)
    if items.get("POTION", 0) < before + count:
        return f"the bag's items {items}"
    for _ in range(6):
        if player.where()[0] != mart:
            break
        player.step("Down", "leave the mart")
    player.settle(240, "the door's fade")
    return None


def build_heal(seeds: range) -> dict:
    """HEAL: `route103.ss1` (Route 103 (5,7) BEFORE the rival: Mudkip L6 13/23, no items, 3000 money) -> the AI's goto
    brain to Route 103's south edge (9,21) and a test-side Down into Oldale (`data/maps/Route103/map.json`: Oldale below,
    offset 0); the goto brain to (14,7) below Oldale's Poke Mart (warp (14,6)); the AI's own MART brain buys 2 POTIONS
    (`_shop`); the goto brain to Oldale's north edge (9,0), a test-side Up into Route 103, the goto brain back to (5,7);
    then the AI's battle brain walks up to MAY (10,3) and talks (as `make_step4_fixtures.py --only rival`); saved on the
    first frame of the battle: Mudkip L6 at 13/23 HP against her full Treecko, two Potions in the bag."""
    source_md5 = pin(ROUTE103)
    from modules.memory import read_symbol

    def fail(player: Player, seed: int, why: str) -> None:
        print(f"[heal] seed {seed}: {why}; {player.log[-5:]}; {player.lines[-6:]}", flush=True)

    for seed in seeds:
        player = Player(ROUTE103[0])
        player.brain(12000, brain="goto", goto=((9, 21),), seed=seed)
        if player.where() != ("ROUTE103", 9, 21):
            fail(player, seed, f"not at Route 103's south edge: {player.where()}")
            continue
        player.step("Down", "cross into Oldale")
        player.brain(12000, brain="goto", goto=((14, 7),), seed=seed)
        if player.where() != ("OLDALE_TOWN", 14, 7):
            fail(player, seed, f"not below Oldale's mart: {player.where()}")
            continue
        why = _shop(player, seed, HEAL_POTIONS)
        if why is not None:
            fail(player, seed, why)
            continue
        player.brain(12000, brain="goto", goto=((9, 0),), seed=seed)
        if player.where() != ("OLDALE_TOWN", 9, 0):
            fail(player, seed, f"not at Oldale's north edge: {player.where()}")
            continue
        player.step("Up", "cross into Route 103")
        player.brain(12000, brain="goto", goto=((5, 7),), seed=seed)
        last: dict = {}

        def stop(context):
            # a TRAINER battle's first frame (a wild battle met on the way is played by the brain and the walk goes on)
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            return {"frame": context.emulator.get_frame_count()} if flags & 8 else None

        result = player.brain(30000, stop, brain="battle", talk_to=(10, 3), battles=1, seed=seed)
        if result["found"] is None:
            fail(player, seed, f"no battle: {result['reason']!r}")
            continue
        opponent = int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")
        if opponent != TRAINER_MAY_ROUTE103_MUDKIP:
            fail(player, seed, f"the battle's opponent is {opponent}")
            continue
        HEAL.write_bytes(player.emulator.get_save_state())
        return {"fixture": HEAL.name, "md5": md5(HEAL), "source": [ROUTE103[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"the AI's goto / mart / battle brains (seed {seed}), test-side edge and door steps, clock {GAME_CLOCK}",
                "at": result["found"], "opponent": opponent, "steps": player.log, "ai_lines": player.lines,
                "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the rival's battle with Potions")


def _items(player: Player) -> dict:
    from ai_player.gates.probe_eyes import _u32, own_progress
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    return {e["name"]: e["quantity"] for e in own_progress(player.context, sb1, sb2)["bag"].get("items", [])}


def _talk_into_battle(player: Player, last: dict, budget: int = 6000) -> dict | None:
    """TEST SIDE: the rival's scene: A on the eyes' waits, YES (the cursor read) at a yes/no, until the battle's FIRST
    frame (`_battle_start`)."""
    presser = player.presser
    for _ in range(budget):
        if _battle_start(player.context, last):
            from modules.pokemon_party import get_party

            lead = get_party()[0]
            return {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp],
                    "frame": player.emulator.get_frame_count()}
        look = presser.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == "yes_no" and ui.accepts_input:
            if ui.cursor != 0:
                presser.press("Up", f"yes_no cursor on {ui.cursor}: to YES")
                continue
            presser.press("A", "yes_no cursor on YES: battle")
            continue
        if ui is None and look.screen.waits_for_button:
            presser.press("A", f"a wait: {look.screen.wait_reason}")
            continue
        presser.wait(1)
    player.log += presser.log
    return None


def build_switch(seeds: range) -> dict:
    source_md5 = pin(ROUTE116TEAM)
    from modules.memory import read_symbol

    for seed in seeds:
        player = Player(ROUTE116TEAM[0])
        reorder(player, POOCHYENA_116)
        last: dict = {}

        def stop(context):
            return {"frame": context.emulator.get_frame_count()} if _battle_start(context, last) else None

        result = player.brain(12000, stop, brain="battle", talk_to=(12, 7), battles=1, seed=seed)
        if result["found"] is None:
            print(f"[switch] seed {seed}: no battle: {result['reason']!r}; {player.log[-6:]}; {player.lines[-8:]}", flush=True)
            continue
        opponent = int.from_bytes(read_symbol("gTrainerBattleOpponent_A", size=2), "little")
        if opponent != TRAINER_JOEY:
            continue
        SWITCH.write_bytes(player.emulator.get_save_state())
        return {"fixture": SWITCH.name, "md5": md5(SWITCH), "source": [ROUTE116TEAM[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"test-side reorder + the AI's battle brain (talk to 12,7; seed {seed}), clock {GAME_CLOCK}",
                "at": result["found"], "opponent": opponent, "steps": player.log, "ai_lines": player.lines,
                "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached Joey's battle")


def build_run(seeds: range) -> dict:
    source_md5 = pin(ROUTE116TEAM)
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    tried = []
    for seed in seeds:
        player = Player(ROUTE116TEAM[0])
        reorder(player, POOCHYENA_116)
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            party = get_party()
            lead = party[0]
            strongest = max(party, key=lambda m: m.level)
            facts = {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp],
                     "strongest": [strongest.species.name, strongest.current_hp, strongest.total_hp],
                     "trainer": bool(flags & 8)}
            tried.append({"seed": seed, **facts})
            if (not flags & 8 and lead.personality_value == POOCHYENA_116 and 0 < lead.current_hp < RUN_LOW * lead.total_hp
                    and strongest.current_hp * 3 >= strongest.total_hp):
                return facts
            return None

        result = player.brain(60000, stop, brain="battle", battles=30, seed=seed)
        if result["found"] is None:
            continue
        RUN.write_bytes(player.emulator.get_save_state())
        return {"fixture": RUN.name, "md5": md5(RUN), "source": [ROUTE116TEAM[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"test-side reorder + the AI's battle brain (Story, roaming, seed {seed}), clock {GAME_CLOCK}",
                "at": result["found"], "battle_starts_seen": tried, "steps": player.log, "ai_lines": player.lines,
                "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached the run condition: {tried}")


MAUVILLE = (SAVES / "strength_boxfirst_mauville.ss1", "ba23ca04f9d774e07ef65347700c2e65")
SING = FIXTURES / "sing_r117.ss1"
#: (step 4.1 round 2) the foe a sleep move may be used on for a catch: at most this many levels above the Skitty
#: (`brain/battle.py` OPENER_LEVELS) and of no type that hits a Normal type super-effectively (Fighting)
SING_LEVELS = 2


def build_sing(seeds: range) -> dict:
    """SING (step 4.1 round 2, arm CATCHS; finding 5's weak proof: "the catch's sleep or paralysis move is never exercised
    live"): `strength_boxfirst_mauville.ss1` (Mauville City (22,6); Sceptile L44 first, a SKITTY L17 with SING at 45/45 HP,
    16 Poke Balls; the Pokedex owns 10 species, none of Route 117's) -> the SKITTY put first (START menu presses, `reorder`)
    -> the AI's EXPLORE brain (Catcher) from Mauville to ROUTE117 (its own frontier exploration: no map knowledge) -> its
    battle brain (Story) roams Route 117's grass; saved on the FIRST frame of the first wild battle against a species the
    Pokedex has not got, at most `SING_LEVELS` above the Skitty, not a Fighting type, the Skitty at full HP."""
    source_md5 = pin(MAUVILLE)
    from modules.memory import read_symbol
    from modules.pokemon import get_opponent
    from modules.pokemon_party import get_party

    species_types = {name: entry["types"] for name, entry in
                     json.loads((REPO / "ai_player" / "knowledge" / "species.json").read_text(encoding="utf-8"))["species"].items()}
    tried = []
    for seed in seeds:
        player = Player(MAUVILLE[0])
        owned = set(player.presser.look().progress.owned_dex)
        skitty = next(m.personality_value for m in get_party() if m.species.name == "Skitty")
        reorder(player, skitty)
        player.brain(30000, lambda context: {"map": "ROUTE117"} if player.where()[0] == "ROUTE117" else None,
                     brain="explore", goal_map="ROUTE117", personality="Catcher", seed=seed)
        if player.where()[0] != "ROUTE117":
            print(f"[sing] seed {seed}: not on Route 117: {player.where()}; {player.log[-3:]}", flush=True)
            continue
        last: dict = {}

        def stop(context):
            if not _battle_start(context, last):
                return None
            flags = int.from_bytes(read_symbol("gBattleTypeFlags", size=4), "little")
            lead, foe = get_party()[0], get_opponent()
            facts = {"lead": [lead.species.name, lead.level, lead.current_hp, lead.total_hp, f"{lead.personality_value:08x}"],
                     "foe": [foe.species.name, foe.level, foe.species.national_dex_number, species_types.get(foe.species.name)],
                     "trainer": bool(flags & 8)}
            tried.append({"seed": seed, **facts})
            if (not flags & 8 and lead.personality_value == skitty and lead.current_hp == lead.total_hp
                    and foe.species.national_dex_number not in owned and foe.level <= lead.level + SING_LEVELS
                    and "Fighting" not in (species_types.get(foe.species.name) or ())):
                return facts
            return None

        result = player.brain(60000, stop, brain="battle", battles=30, seed=seed)
        if result["found"] is None:
            print(f"[sing] seed {seed}: no such battle: {tried[-3:]}", flush=True)
            continue
        SING.write_bytes(player.emulator.get_save_state())
        return {"fixture": SING.name, "md5": md5(SING), "source": [MAUVILLE[0].relative_to(REPO).as_posix(), source_md5],
                "played_by": f"test-side reorder + the AI's explore brain (Catcher) to ROUTE117 + its battle brain (Story, "
                             f"roaming, seed {seed}), clock {GAME_CLOCK}",
                "at": result["found"], "owned_dex": sorted(owned), "battle_starts_seen": tried, "steps": player.log,
                "ai_lines": player.lines, "truth": truth(player.context)}
    raise SystemExit(f"no seed of {list(seeds)} reached a wild battle for the Skitty's Sing: {tried}")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=("rival", "switch", "run", "heal", "sing", "rival_hurt"))
    parser.add_argument("--seeds", default="1-20")
    args = parser.parse_args()
    low, high = (int(p) for p in args.seeds.split("-"))
    seeds = range(low, high + 1)
    builders = {"rival": lambda: build_rival(seeds), "switch": lambda: build_switch(seeds), "run": lambda: build_run(seeds),
                "heal": lambda: build_heal(seeds), "sing": lambda: build_sing(seeds),
                "rival_hurt": lambda: build_rival_hurt(seeds)}  # (step 4.1 round 3)
    for name, builder in builders.items():
        if args.only and name != args.only:
            continue
        started = time.monotonic()
        out = builder()
        out["seconds"] = round(time.monotonic() - started, 1)
        path = FIXTURES / (Path(out["fixture"]).stem + ".build.json")
        path.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        print(f"[FIXTURE] {out['fixture']} md5 {out['md5']} ({out['seconds']} s): {path.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
