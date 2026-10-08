"""TEST SIDE: the step-1.1 scenarios PLAYED in a throwaway emulator, the AI's eyes looking at EVERY frame.

    py -3.12 ai_player/gates/probe_step11.py SCENARIO [--state PATH] [--delay N]
    prints one line: PROBE11 {json}

WHY: the watcher presses nothing, so some of what step 1.1 fixed never happens in a watcher run: a warp, the
end of a dialogue, the end of a battle, a catch. Here THIS file presses buttons in its own emulator (never in
an AI run; the purity audit does not apply to the test side), feeds every frame's Observation from the AI's
OWN eyes (`ai_player.host.eyes.FrameworkEyes`) to the AI's OWN scorer lines (`ai_player.memory_log`), and
records beside each look the GROUND TRUTH it reads by a second path (raw bytes and this file's decoders,
the framework's decoders, the ROM's map table, the game's battle text). Every press that advances a text is
GATED on the eyes' `waits_for_button` (the project's museum-greeter lesson: A on every frame is holding it),
or on a named menu state; presses are at least `PRESS_GAP` frames apart, and every loop is bounded.

SCENARIOS (each graded by `gates/live_step1.py`):
  warp      `dewford.ss1`: walk left to x = 8, then up into the door at (8, 8) (Dewford's window shows it at
            dx -3, dy -1). Finding 4: the frames where the player object's tile (- 7) and save block 1's
            `pos` differ, and what the eyes report on each; the live `gMapHeader` matched against the ROM's
            map table (`probe_eyes.RomMaps`, independent of the save block) names the map loaded.
  warp_y    STEP 2.1: `post_league_lobby.ss1`: down and left onto the League's 1F escalator at (1, 7), arriving on
            2F at (1, 6): a warp whose two tiles differ in y ONLY (the Dewford door's differ in x only), the same
            record.
  sign      `dewford.ss1`: one step left, face down, A on the sign at (10, 10). Finding 6: the script's
            `waitbuttonpress` at the end of a sign (`Std_MsgboxSign`), and BEHAVIOUR: 300 idle frames move
            nothing, one A press moves the script. Also the fixture's FIRST frame: a finished script
            (status 2) with WaitForAorBPress left behind, where nothing waits.
  trainer   `trainer_defeat_text_r116.ss1` (arm E10's fixture): A on every text wait until the battle is over
            and the overworld is back. Finding 2: the [TRAINER] end line, against the money the probe decodes
            from the save block before and after, and the battle's own "got X for winning!" text.
  catch     `oldale.ss1` (a wild Wurmple): BAG, the Poke Ball pocket, A on the ball, until a ball holds; YES
            to the nickname, the naming screen confirmed with the default name. Findings 1, 2, 5: the
            [CATCH] line's PID and dest against the foe's PID read before the battle ends (gEnemyParty) and
            the framework's party afterwards; every frame's (state, in_battle, outcome), so a look out of the
            battle with no result would show. `--delay N` idles N frames first (the catch is decided by the
            RNG, which advances every frame; the arm pins the N it uses).
  start     `route116team.ss1`: one step down into the tall grass, then left and right until a wild battle
            starts, then RUN. Finding 2: on every frame of the battle, the foe battler `gBattleMons` holds
            (raw: species, PID) against the occupied slots of `gEnemyParty` (raw PIDs, `hasSpecies`): a
            battler whose PID is not one of them is the PREVIOUS battle's, still in memory; the eyes must not
            report it, and the battle's lines must name THIS battle's foe.
  replay    `trainer_battle_r116.ss1` + the presses `make_defeat_text_fixture.py` recorded: the battle that
            made E10's fixture, REPLAYED, recording every battle text shown (`gDisplayedStringBattle`, this
            file's charmap). Finding 3: the foe's moves "seen on screen" ("Foe MACHOP used LEER!") are the
            truth for the eyes' foe moves at E10; the replay ends with the pinned fixture's md5 or says not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.probe_eyes import RomMaps, _s16, _symbol, _u16, _u32, boot, own_text, screen_snapshot  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROFILE = "ai-step0-fixture"
PRESS_GAP = 8  # frames between two presses: each press is a NEW press (JOY_NEW), never a hold
STALL = 120  # nothing changed this long in a battle and no rule applies: press B (a page that waits for A or B)
OBJECT_EVENT_SIZE = 0x24


# ---------------------------------------------------------------------------------------------- reads
def save_block_place(context) -> tuple[tuple[int, int], tuple[int, int]]:
    """Save block 1 `pos` (x, y) and `location` (group, number): struct SaveBlock1 @0 and @4."""
    from modules.memory import read_symbol

    raw = context.emulator.read_bytes(_u32(read_symbol("gSaveBlock1Ptr", size=4), 0), 6)
    return (_s16(raw, 0), _s16(raw, 2)), (raw[4], raw[5])


def player_object_xy() -> tuple[int, int]:
    from modules.memory import read_symbol

    avatar = read_symbol("gPlayerAvatar", size=0x24)
    me = read_symbol("gObjectEvents", avatar[5] * OBJECT_EVENT_SIZE, OBJECT_EVENT_SIZE)
    return _s16(me, 0x10) - 7, _s16(me, 0x12) - 7


def money(context) -> int:
    """Save block 1 money XOR save block 2's key (struct SaveBlock1 money @0x490, SaveBlock2 key @0xAC)."""
    from modules.memory import read_symbol

    sb1 = _u32(read_symbol("gSaveBlock1Ptr", size=4), 0)
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    return _u32(context.emulator.read_bytes(sb1 + 0x490, 4), 0) ^ _u32(context.emulator.read_bytes(sb2 + 0xAC, 4), 0)


def battle_text() -> str:
    from modules.memory import read_symbol

    raw = bytes(read_symbol("gDisplayedStringBattle", 0, 0x12C))
    return own_text(raw)


def script_state() -> dict:
    """The global script context, raw: status (`sGlobalScriptContextStatus`), mode @1, the native function
    @4 named by the symbol table, the script pointer @8."""
    from modules.memory import read_symbol

    raw = read_symbol("sGlobalScriptContext", size=12)
    return {"status": read_symbol("sGlobalScriptContextStatus", size=1)[0], "mode": raw[1],
            "native": _symbol(_u32(raw, 4)), "script_ptr": _u32(raw, 8)}


def tasks() -> list[str]:
    from modules.memory import read_symbol

    raw = read_symbol("gTasks", size=40 * 16)
    return sorted({_symbol(_u32(raw, 40 * i) - 1) for i in range(16) if raw[40 * i + 4] and _u32(raw, 40 * i)})


def look_row(look) -> dict:
    p = look.player
    return {"frame": look.frame, "state": look.screen.game_state, "screen": look.screen.screen, "in_battle": look.screen.in_battle,
            "outcome": look.last_battle_outcome, "waits": look.screen.waits_for_button, "reason": look.screen.wait_reason,
            "map": None if p is None else [p.map_group, p.map_number], "xy": None if p is None or p.x is None else [p.x, p.y],
            "settling": None if p is None else p.settling, "view": look.view is not None,
            "party": None if look.party is None else [f"{m.pid:08X}" for m in look.party], "problems": list(look.problems)}


class Player:
    """The eyes and the scorer lines, looking at every frame, and a GATED press."""

    def __init__(self, context) -> None:
        from ai_player.host.eyes import FrameworkEyes
        from ai_player.memory_log import ScorerLines

        self.context = context
        self.emulator = context.emulator
        self.eyes = FrameworkEyes()
        self.scorer = ScorerLines()
        self.lines: list[str] = []
        self.presses: list[list] = []
        self.last_press = -PRESS_GAP
        self.step = 0
        self.look = None

    def see(self):
        self.look = self.eyes.look()
        self.lines += self.scorer.update(self.look)
        return self.look

    def press(self, button: str, why: str) -> bool:
        if self.step - self.last_press < PRESS_GAP:
            return False
        self.emulator.press_button(button)
        self.presses.append([self.look.frame if self.look else None, button, why,
                             bool(self.look and self.look.screen.waits_for_button), self.look.screen.wait_reason if self.look else None])
        self.last_press = self.step
        return True

    def frame(self) -> None:
        self.emulator.run_single_frame()
        self.step += 1


# ---------------------------------------------------------------------------------------------- warp
def scenario_warp(context, state: bytes) -> dict:
    """Finding 4 (module docstring)."""
    from modules.map_data import MapRSE
    from modules.memory import read_symbol

    context.emulator.load_save_state(state)
    play = Player(context)
    rom = RomMaps(context.emulator)
    header_maps: dict[bytes, list] = {}
    frames, phase = [], "left"
    for _ in range(700):
        look = play.see()
        saved_xy, saved_map = save_block_place(context)
        live = bytes(read_symbol("gMapHeader", size=0x1C))
        if live not in header_maps:
            found = []
            for member in MapRSE:
                key = tuple(member.value)
                try:
                    if rom.header(key) == live and list(key) not in found:
                        found.append(list(key))
                except Exception:  # noqa: BLE001 - a map the table does not hold
                    continue
            header_maps[live] = found
        row = look_row(look)
        row.update({"save_xy": list(saved_xy), "save_map": list(saved_map), "object_xy": list(player_object_xy()),
                    "header_maps": header_maps[live]})
        frames.append(row)
        # the walk is steered by the SAVE BLOCK (this file's read), never by the eyes under test
        if phase == "left":
            if saved_xy[0] > 8:
                play.emulator.hold_button("Left")
            else:
                play.emulator.release_button("Left")
                phase = "up"
        if phase == "up":
            play.emulator.hold_button("Up")
            if saved_map != tuple(frames[0]["save_map"]):
                play.emulator.release_button("Up")
                phase = "arrived"
        play.frame()
    play.emulator.release_button("Up")
    play.emulator.release_button("Left")
    return {"frames": frames, "lines": play.lines, "final": play.scorer.final(play.look)}


def scenario_warp_y(context, state: bytes) -> dict:
    """STEP 2.1 (the step-2 verifier: "no live warp that differs only in y"): `post_league_lobby.ss1` (the NURSE
    arm's fixture: EVER_GRANDE_CITY_POKEMON_LEAGUE_1F (3, 4), the player free), walked to the escalator warp at
    (1, 7), whose arrival is EVER_GRANDE_CITY_POKEMON_LEAGUE_2F (1, 6) (the ROM's warp events, found by a scratch
    search of every map for warps whose departure and arrival tiles share x; the tile is an escalator,
    `src/field_control_avatar.c` TryStartWarpEventScript -> DoEscalatorWarp). The walk is steered by the SAVE
    BLOCK (this file's read): Down to y 7, then Left until the save block's map changes. If a script's text is on
    screen first, A is pressed ONLY on the eyes' waits_for_button until the controls are free. (The 2F fixture
    `post_league_2f.ss1` was tried first: it starts inside a long scene that walks the player away from the
    escalator.) The same per-frame record as `scenario_warp`."""
    from modules.map_data import MapRSE
    from modules.memory import read_symbol

    context.emulator.load_save_state(state)
    play = Player(context)
    rom = RomMaps(context.emulator)
    header_maps: dict[bytes, list] = {}
    frames, phase = [], "text"
    for _ in range(1500):
        look = play.see()
        saved_xy, saved_map = save_block_place(context)
        live = bytes(read_symbol("gMapHeader", size=0x1C))
        if live not in header_maps:
            header_maps[live] = [list(tuple(m.value)) for m in MapRSE if _header_or_none(rom, tuple(m.value)) == live]
        row = look_row(look)
        row.update({"save_xy": list(saved_xy), "save_map": list(saved_map), "object_xy": list(player_object_xy()),
                    "header_maps": header_maps[live], "phase": phase})
        frames.append(row)
        if phase == "text":
            screen = look.screen
            if screen.waits_for_button:
                play.press("A", "the greeting waits")
            elif not (screen.script_running or screen.controls_locked or screen.text_box_open):
                phase = "walk"
        if phase == "walk":
            if saved_map != tuple(frames[0]["save_map"]):
                for button in ("Up", "Down", "Left"):
                    play.emulator.release_button(button)
                phase = "arrived"
            else:
                want = "Down" if saved_xy[1] < WARP_Y_TILE[1] else "Up" if saved_xy[1] > WARP_Y_TILE[1] else "Left"
                for button in ("Up", "Down", "Left"):
                    if button != want:
                        play.emulator.release_button(button)
                play.emulator.hold_button(want)
        play.frame()
        if phase == "arrived" and sum(1 for f in frames if f["phase"] == "arrived") >= 400:
            break
    for button in ("Up", "Down", "Left"):
        play.emulator.release_button(button)
    return {"frames": frames, "lines": play.lines, "final": play.scorer.final(play.look), "presses": play.presses}


#: STEP 2.1: the escalator warp of EVER_GRANDE_CITY_POKEMON_LEAGUE_1F that `scenario_warp_y` walks onto.
WARP_Y_TILE = (1, 7)


def _header_or_none(rom: RomMaps, key: tuple[int, int]) -> bytes | None:
    try:
        return rom.header(key)
    except Exception:  # noqa: BLE001 - a map the table does not hold
        return None


# ---------------------------------------------------------------------------------------------- sign
IDLE_FRAMES = 300


def scenario_sign(context, state: bytes) -> dict:
    """Finding 6 (module docstring)."""
    context.emulator.load_save_state(state)
    play = Player(context)
    first = play.see()
    out: dict = {"first": {**look_row(first), "script": script_state(), "printers": screen_snapshot()["printers"]}}
    # one step left (the sign is at (10, 10), below (10, 9)), face down, A: steered by the save block
    for _ in range(120):
        (x, _y), _map = save_block_place(context)
        if x > 10:
            play.emulator.hold_button("Left")
        else:
            play.emulator.release_button("Left")
            break
        play.see()
        play.frame()
    for _ in range(30):
        play.see()
        play.frame()
    play.press("Down", "turn to face the sign")
    for _ in range(30):
        play.see()
        play.frame()
    play.press("A", "read the sign")
    play.frame()
    found = None
    for _ in range(1500):
        look = play.see()
        if look.screen.wait_reason == "script waitbuttonpress":
            found = look
            break
        if look.screen.waits_for_button:
            play.press("A", "a text waits")
        play.frame()
    out["found"] = None if found is None else {**look_row(found), "script": script_state(), "printers": screen_snapshot()["printers"],
                                                "facing": found.player.facing if found.player else None}
    out["presses_before"] = list(play.presses)
    if found is None:
        out["lines"] = play.lines
        return out
    # BEHAVIOUR: IDLE_FRAMES frames with no input, the eyes looking at every one; then ONE press of A
    s0 = {**screen_snapshot(), **script_state()}
    idle = []
    for _ in range(IDLE_FRAMES):
        play.frame()
        look = play.see()
        snap = {**screen_snapshot(), **script_state()}
        idle.append([look.frame, look.screen.waits_for_button, look.screen.wait_reason, snap == s0])
    play.last_press = -PRESS_GAP
    play.press("A", "the behaviour test's one press")
    after = []
    for _ in range(120):
        play.frame()
        look = play.see()
        after.append([look.frame, look.screen.waits_for_button, look.screen.wait_reason, script_state()])
    moved = next((a for a in after if a[3]["status"] != s0["status"] or a[3]["script_ptr"] != s0["script_ptr"]), None)
    out.update({"before_idle": s0, "idle": idle, "after": after[:40], "press_moved_the_script": moved is not None,
                "moved_at": moved, "lines": play.lines})
    return out


# ---------------------------------------------------------------------------------------------- trainer
def scenario_trainer(context, state: bytes) -> dict:
    """Finding 2: a trainer battle played to its end (module docstring)."""
    context.emulator.load_save_state(state)
    play = Player(context)
    money_before = money(context)
    texts, rows, ended, last_snap, stall_from = [], [], None, None, 0
    for _ in range(4000):
        look = play.see()
        text = battle_text()
        if not texts or texts[-1][1] != text:
            texts.append([look.frame, text])
        snap = (look.screen.game_state, look.screen.in_battle, look.last_battle_outcome, look.screen.wait_reason)
        if snap != last_snap:
            rows.append(look_row(look))
            last_snap, stall_from = snap, play.step
        if ended is None and look.screen.game_state == "OVERWORLD" and look.last_battle_outcome != 0:
            ended = play.step
        if ended is not None and play.step - ended > 120:
            break
        if look.screen.waits_for_button:
            play.press("A", "a text waits")
        elif look.screen.in_battle and play.step - stall_from >= STALL:
            play.press("B", "stalled in the battle")
            stall_from = play.step
        play.frame()
    return {"money_before": money_before, "money_after": money(context), "texts": texts, "rows": rows, "lines": play.lines,
            "final": play.scorer.final(play.look), "presses": play.presses, "ended": ended is not None}


# ---------------------------------------------------------------------------------------------- catch
BALLS_POCKET = 1  # the bag's pockets: ITEMS 0, POKE_BALLS 1, TMHM 2, BERRIES 3, KEY_ITEMS 4
ACTION_BAG = 1  # the battle's action menu: FIGHT 0, BAG 1, POKEMON 2, RUN 3 (two by two)


def scenario_catch(context, state: bytes, delay: int) -> dict:
    """Findings 1, 2, 5: a wild Pokemon caught, nicknamed with the default name (module docstring)."""
    from modules.memory import read_symbol
    from modules.pokemon_party import get_party

    context.emulator.load_save_state(state)
    play = Player(context)
    foe_pid = _u32(read_symbol("gEnemyParty", size=4), 0)  # the wild Pokemon: gEnemyParty[0] personality @0
    party_before = [f"{m.personality_value:08X}" for m in get_party()]
    rows, last_snap, stall_from, ended = [], None, 0, None
    named = {"yes": False, "start": False}
    for _ in range(max(0, min(delay, 600))):
        play.see()
        play.frame()
    for _ in range(12000):
        look = play.see()
        state_name = look.screen.game_state
        controller = _symbol(_u32(read_symbol("gBattlerControllerFuncs", 0, 4), 0) - 1) or "?"
        running = tasks()
        snap = (state_name, look.screen.in_battle, look.last_battle_outcome, look.screen.wait_reason, controller, tuple(running))
        if snap != last_snap:
            rows.append({**look_row(look), "controller": controller, "tasks": running})
            last_snap, stall_from = snap, play.step
        if ended is None and state_name == "OVERWORLD" and look.last_battle_outcome != 0:
            ended = play.step
        if ended is not None and play.step - ended > 120:
            break
        balls = look.bag.ball_total if look.bag is not None else None
        fade = _u16(read_symbol("gPaletteFade", 0x07, 2), 0) & 0x80
        if state_name == "BATTLE" and controller == "HandleInputChooseAction":
            if balls == 0:
                break  # out of balls: the arm reports "not caught" (its delay must then change)
            cursor = read_symbol("gActionSelectionCursor", 0, 1)[0]
            play.press("A" if cursor == ACTION_BAG else ("Right" if cursor == 0 else "Up"), "the action menu: BAG")
        elif state_name == "BAG_MENU" and not fade and "Task_BagMenu_HandleInput" in running:
            pocket = read_symbol("gBagPosition", 0x05, 1)[0]
            chosen = _u16(read_symbol("gBagPosition", 8 + 2 * pocket, 2), 0) + _u16(read_symbol("gBagPosition", 18 + 2 * pocket, 2), 0)
            if pocket != BALLS_POCKET:
                play.press("Right" if pocket < BALLS_POCKET else "Left", "the bag: the Poke Ball pocket")
            else:
                play.press("Up" if chosen else "A", "the bag: the first ball")
        elif state_name == "BAG_MENU" and not fade and any("ItemContext" in t for t in running):
            play.press("A", "the item's menu: USE (its first entry)")
        elif state_name == "NAMING_SCREEN" and not fade:
            if play.press("A" if named["start"] else "Start", "the naming screen: keep the default name (START, then OK)"):
                named["start"] = True
        elif look.screen.waits_for_button:
            play.press("A", "a text waits")
        elif look.screen.in_battle and play.step - stall_from >= STALL:
            # the question is printed and the battle engine polls its YES / NO box (the text printer is done)
            asked = "nickname" in battle_text() and controller == "PlayerBufferRunCommand" and not named["yes"]
            if play.press("A" if asked else "B", "the nickname question: YES" if asked else "stalled in the battle"):
                named["yes"] = named["yes"] or asked
            stall_from = play.step
        play.frame()
    raw_party = read_symbol("gPlayerParty", size=600)
    after = [[f"{m.personality_value:08X}", m.species.name, _u32(raw_party, 100 * m.index + 4) & 0xFFFF] for m in get_party()]
    sb2 = _u32(read_symbol("gSaveBlock2Ptr", size=4), 0)
    return {"delay": delay, "foe_pid": f"{foe_pid:08X}", "party_before": party_before,
            "party_after": after, "player_visible_id": _u16(context.emulator.read_bytes(sb2 + 0x0A, 2), 0),
            "rows": rows, "lines": play.lines, "final": play.scorer.final(play.look), "presses": play.presses,
            "ended": ended is not None, "named": named}


# ---------------------------------------------------------------------------------------------- start
ACTION_RUN = 3


def scenario_start(context, state: bytes) -> dict:
    """Finding 2 at a battle's START (module docstring)."""
    from modules.memory import read_symbol
    from modules.pokemon import get_species_by_index

    context.emulator.load_save_state(state)
    play = Player(context)
    frames, started, ended = [], None, None
    for _ in range(9000):
        look = play.see()
        state_name = look.screen.game_state
        if started is None and state_name != "OVERWORLD":
            started = play.step
            for button in ("Down", "Left", "Right"):
                play.emulator.release_button(button)
        if started is None:
            walk = play.step // 32  # 32 frames = 2 steps: down into the grass, then right and left
            play.emulator.hold_button("Down" if walk == 0 else ("Right" if walk % 2 else "Left"))
            for button in ("Down", "Left", "Right"):
                if button != ("Down" if walk == 0 else ("Right" if walk % 2 else "Left")):
                    play.emulator.release_button(button)
            play.frame()
            continue
        mons = read_symbol("gBattleMons", size=0x58 * 2)
        enemy = read_symbol("gEnemyParty", size=600)
        present = [_u32(enemy, 100 * i) for i in range(6) if enemy[100 * i + 19] & 0x02]
        raw_pid = _u32(mons, 0x58 + 0x48)
        try:
            raw_species = get_species_by_index(_u16(mons, 0x58)).name
        except Exception:  # noqa: BLE001 - a species id outside the table
            raw_species = f"#{_u16(mons, 0x58)}"
        frames.append({**look_row(look), "battle_foe": None if look.battle is None else [m.species for m in look.battle.foe],
                       "raw_foe": raw_species, "raw_foe_pid": f"{raw_pid:08X}", "enemy_pids": [f"{p:08X}" for p in present],
                       "stale": raw_pid not in present})
        if ended is None and state_name == "OVERWORLD" and look.last_battle_outcome != 0:
            ended = play.step
        if ended is not None and play.step - ended > 120:
            break
        controller = _symbol(_u32(read_symbol("gBattlerControllerFuncs", 0, 4), 0) - 1) or "?"
        if state_name == "BATTLE" and controller == "HandleInputChooseAction":
            cursor = read_symbol("gActionSelectionCursor", 0, 1)[0]
            play.press("A" if cursor == ACTION_RUN else ("Right" if cursor in (0, 2) else "Down"), "the action menu: RUN")
        elif look.screen.waits_for_button:
            play.press("A", "a text waits")
        play.frame()
    first_species = None
    try:
        from modules.pokemon import Pokemon

        first_species = Pokemon(read_symbol("gEnemyParty", size=100)).species.name
    except Exception:  # noqa: BLE001
        pass
    return {"frames": [f for f in frames if f["state"] != "OVERWORLD" or f["outcome"] != 0][:1500], "lines": play.lines,
            "presses": play.presses, "ended": ended is not None, "started": started is not None,
            "enemy_first_species": first_species}


# ---------------------------------------------------------------------------------------------- replay
def scenario_replay(context) -> dict:
    """Finding 3's truth for E10: the battle that made the fixture, replayed, its texts recorded."""
    build = json.loads((FIXTURES / "trainer_defeat_text_r116.build.json").read_text(encoding="utf-8"))
    context.emulator.load_save_state((FIXTURES / "trainer_battle_r116.ss1").read_bytes())
    presses = {p[0]: p[1] for p in build["presses"]}
    texts = []
    for _ in range(20_000):
        frame = context.emulator.get_frame_count()
        if frame >= build["found_at_frame"]:
            break
        text = battle_text()
        if not texts or texts[-1][1] != text:
            texts.append([frame, text])
        if frame in presses:
            context.emulator.press_button(presses[frame])
        context.emulator.run_single_frame()
    data = context.emulator.get_save_state()
    return {"texts": texts, "end_frame": context.emulator.get_frame_count(), "end_md5": hashlib.md5(data).hexdigest(),
            "pinned_md5": build["out_md5"]}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scenario", choices=("warp", "warp_y", "sign", "trainer", "catch", "start", "replay"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--delay", type=int, default=0)
    args = parser.parse_args()
    defaults = {"warp": SAVES / "dewford.ss1", "warp_y": SAVES / "post_league_lobby.ss1", "sign": SAVES / "dewford.ss1",
                "catch": SAVES / "oldale.ss1",
                "start": SAVES / "route116team.ss1", "trainer": FIXTURES / "trainer_defeat_text_r116.ss1",
                "replay": FIXTURES / "trainer_battle_r116.ss1"}
    path = args.state or defaults[args.scenario]
    data = path.read_bytes()
    context = boot(PROFILE)
    import ai_player.host.eyes as eyes_module
    from ai_player.eyes import view as rules

    result: dict = {"scenario": args.scenario, "state_file": str(path), "md5": hashlib.md5(data).hexdigest(),
                    "eyes_code": {"module": eyes_module.__file__, "rules": rules.__file__}}
    if args.scenario == "warp":
        result.update(scenario_warp(context, data))
    elif args.scenario == "warp_y":
        result.update(scenario_warp_y(context, data))
    elif args.scenario == "sign":
        result.update(scenario_sign(context, data))
    elif args.scenario == "trainer":
        result.update(scenario_trainer(context, data))
    elif args.scenario == "catch":
        result.update(scenario_catch(context, data, args.delay))
    elif args.scenario == "start":
        result.update(scenario_start(context, data))
    else:
        result.update(scenario_replay(context))
    print("PROBE11 " + json.dumps(result), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
