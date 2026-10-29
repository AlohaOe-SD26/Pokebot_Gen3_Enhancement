"""R5 FIXTURE PROBE (TEST SIDE, development; never the AI's code): is the screen FREE when an AI-player run ends "done"?

    py -3.12 probe_end_screen.py run --root ROOT --seed N --target T --out DIR [--frames F] [--after K]
    py -3.12 probe_end_screen.py selftest --root ROOT --fixtures DIR --out DIR [--after K]

WHY (R5 build spec section 4, "compute the discriminator FIRST"; CLAUDE.md Tier 2 (4)): an R5 A/B is VACUOUS when both
arms end on a free screen. This probe plays ONE run of the AI's play brain from a REAL New Game (`--fresh` as
`gates/play_harness.py` plays it: in-process, the cartridge clock PINNED to `rate_step5.GAME_CLOCK`, the wall clock set to
`rate_step5.WALL_CLOCK`, the personality and starter of `rate_step5.plan_of(seed)`), with the code under `--root` (a
FROZEN COPY of the tree, so the worktree can be edited meanwhile), and then reads the GAME's screen on the frame the brain
returned, by the harness's OWN free read (`game_screen`), never the AI's `nav_free` (LESSONS PF-19).

THE FREE READ (`game_screen`; R5 recon 03-game-facts section 4): the screen is FREE when ALL of
  * `gMain.callback2 == CB2_Overworld` (raw RAM vs the symbol table's address; `src/overworld.c:1459-1463`: only then does
    the overworld read input at all),
  * `sGlobalScriptContextStatus == CONTEXT_SHUTDOWN` (2: no script; `src/script.c:17-21`),
  * `sLockFieldControls == 0` (a running script holds the lock from setup to shutdown; `src/script.c:228-245`),
  * the message box shut: `sFieldMessageBoxMode == 0` AND text printer 0 not active (`src/field_message_box.c:40-44`;
    the mode alone is NOT "no box": it is 0 again once the text has printed, so the script status and the lock are what
    see the box of a `waitbuttonpress`),
hold on the frame the brain returned AND on each of `--after` K more frames with NO input (one free read is not
"settled": 03-game-facts section 4.3 (d)). The palette fade, the AI's own `nav_free` and the decoded message are RECORDED
beside it for the reader, never part of the verdict.

THE SELFTEST (the read must be able to FAIL and to PASS, PF-10): from the committed fixture `house_2f_clockset.ss1` (the
wall clock just set; MOM's upstairs scene follows, `data/scripts/players_house.inc:58-66`) the frames run with no input
until the game shows MOM's text: the read must say NOT free there; then A is pressed ONLY when the game waits for it
(`play_harness.text_waits_now`) until the scene ends: the read must say FREE, held. A BEHAVIOURAL check confirms both
verdicts by the game itself: a direction tapped on that frame (in a throwaway copy of the state) TURNS the player only when
the game takes input. And the free fixture `route101_south.ss1` must read free, held, and turn.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

#: `include/main.h` struct Main: callback2 @0x04
MAIN_CALLBACK2 = 0x04
#: `src/script.c:17-21`
CONTEXT_SHUTDOWN = 2
#: `include/text.h` struct TextPrinter: active @0x1B, state @0x1C (as `play_harness.text_waits_now` reads them)
PRINTER_ACTIVE, PRINTER_STATE = 0x1B, 0x1C
#: `include/palette.h` struct PaletteFadeControl: `active` is bit 7 of byte 7 (as `host/eyes.py` reads it, for the record)
FADE_BYTE, FADE_BIT = 0x07, 0x80
DEFAULT_AFTER = 10
OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}


def u32(data) -> int:
    return int.from_bytes(bytes(data[:4]), "little")


def game_screen() -> dict:
    """The harness's own read of the screen, from RAM and the symbol table (module docstring). `free` is the verdict."""
    from modules.game import get_symbol, get_symbol_name_before
    from modules.memory import read_symbol

    callback2 = u32(read_symbol("gMain", MAIN_CALLBACK2, 4))
    overworld = get_symbol("CB2_Overworld")[0]
    status = read_symbol("sGlobalScriptContextStatus", size=1)[0]
    lock = read_symbol("sLockFieldControls", size=1)[0]
    box = read_symbol("sFieldMessageBoxMode", size=1)[0]
    printer = read_symbol("sTextPrinters", PRINTER_ACTIVE, 2)
    fade = bool(read_symbol("gPaletteFade", FADE_BYTE, 1)[0] & FADE_BIT)
    on_overworld = (callback2 & ~1) == (overworld & ~1)
    free = on_overworld and status == CONTEXT_SHUTDOWN and lock == 0 and box == 0 and printer[0] == 0
    return {"free": free, "callback2": get_symbol_name_before(callback2 & ~1, pretty_name=True) if callback2 else None,
            "overworld": on_overworld, "script_status": status, "lock": lock, "box_mode": box, "printer0_active": printer[0],
            "printer0_state": printer[1], "fade": fade}


def ai_view(eyes) -> dict:
    """FOR THE RECORD ONLY (never the verdict): what the AI's own eyes say of the same frame."""
    from ai_player.brain.navigator import nav_free
    from ai_player.hands.dialogue import busy_reason

    look = eyes.look()
    return {"nav_free": nav_free(look), "busy_reason": None if nav_free(look) else busy_reason(look),
            "text": (look.screen.text or "")[:160] if look.screen.text else None}


def message_pages() -> list[str]:
    """The pages of the message the field's box shows (`play_harness.shown_pages`, the harness's own decode)."""
    from ai_player.gates.play_harness import shown_pages

    try:
        return shown_pages()
    except Exception as error:  # noqa: BLE001 - a record, not a verdict
        return [f"(unreadable: {type(error).__name__}: {error})"]


def facing() -> str | None:
    from modules.player import get_player_avatar

    try:
        return str(get_player_avatar().facing_direction)
    except Exception:  # noqa: BLE001
        return None


def accepts_input(emulator) -> dict:
    """BEHAVIOURAL ground truth (module docstring): in a throwaway copy of this frame's state, TAP the direction opposite
    the player's facing and let 12 frames run: the game took the input iff the facing changed. The state is restored."""
    saved = emulator.get_save_state()
    held = emulator.reset_held_buttons() if hasattr(emulator, "reset_held_buttons") else None
    try:
        before = facing()
        if before is None or before.capitalize() not in OPPOSITE:
            return {"facing_before": before, "turned": None, "why": "no player facing to turn from"}
        button = OPPOSITE[before.capitalize()]
        emulator.press_button(button)
        for _ in range(12):
            emulator.run_single_frame()
        after = facing()
        return {"facing_before": before, "pressed": button, "facing_after": after, "turned": after != before}
    finally:
        emulator.load_save_state(saved)
        if held:
            emulator.hold_button(inputs=held)


def settled(emulator, after: int) -> dict:
    """The free read on THIS frame and on each of `after` more frames run with NO input (the held buttons released for
    them and noted). The emulator moves on by `after` frames."""
    held = emulator.reset_held_buttons() if hasattr(emulator, "reset_held_buttons") else 0
    reads = [game_screen()]
    for _ in range(after):
        emulator.run_single_frame()
        reads.append(game_screen())
    first_not_free = next((at for at, read in enumerate(reads) if not read["free"]), None)
    return {"free_at_return": reads[0]["free"], "free_held": first_not_free is None, "first_not_free": first_not_free,
            "after": after, "held_buttons_released": held, "at_return": reads[0],
            "changes": [[at, read] for at, read in enumerate(reads) if at == 0 or read != reads[at - 1]]}


def boot_at(root: Path):
    sys.path.insert(0, str(root))
    from ai_player.gates.hands_harness import PROFILE
    from ai_player.gates.probe_eyes import boot

    return boot(PROFILE)


def run(args) -> dict:
    root = args.root.resolve()
    context = boot_at(root)
    from ai_player.gates.hands_harness import pin_game_clock, truth
    from ai_player.gates.play_harness import StoryRecorder, play, story_truth
    from ai_player.gates.rate_step5 import GAME_CLOCK, WALL_CLOCK, plan_of
    from ai_player.host.eyes import FrameworkEyes

    emulator = context.emulator
    if args.state is not None:
        emulator.load_save_state(args.state.read_bytes())
    pin_game_clock(emulator, GAME_CLOCK)
    personality, starter = plan_of(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    run_dir = args.out / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    recorder = StoryRecorder(context, 30, None)
    began = time.monotonic()
    data = play(context, args.seed, args.frames, run_dir, personality, None if args.state else starter, args.target, set(),
                WALL_CLOCK, str(args.world_in) if args.world_in else None, recorder)
    # the brain returned: `play`'s loop breaks on StopIteration BEFORE `run_single_frame`, so the emulator stands on the
    # frame the brain returned (`play_harness.play`)
    end_state = emulator.get_save_state()
    (args.out / "end_state.ss1").write_bytes(end_state)
    try:
        emulator.get_screenshot().save(args.out / "end_screen.png")
        shot = str(args.out / "end_screen.png")
    except Exception as error:  # noqa: BLE001 - a record only
        shot = f"(no screenshot: {type(error).__name__}: {error})"
    marks = story_truth(context)["marks"]
    end_truth = truth(context)
    seen_by_ai = ai_view(FrameworkEyes())
    pages = message_pages()
    behaviour = accepts_input(emulator)
    screen = settled(emulator, args.after)
    data["story"] = recorder.result()
    (args.out / "play.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return {"seed": args.seed, "target": args.target, "personality": personality, "starter": starter,
            "root": str(root), "reason": data["reason"], "frames": data["frames"], "seconds": round(time.monotonic() - began, 1),
            "stop": ((data.get("game_reads") or {}).get("stop") or {}),
            "end_screen": screen, "accepts_input": behaviour, "ai_eyes_for_the_record": seen_by_ai,
            "message_pages": pages[:6], "screenshot": shot,
            "end_state": str(args.out / "end_state.ss1"), "end_state_md5": hashlib.md5(end_state).hexdigest(),
            "end_map": end_truth.get("map"), "end_pos": end_truth.get("pos"), "end_game_state": end_truth.get("game_state"),
            "marks_at_end": {k: v for k, v in marks.items() if v}, "milestones": [m["id"] for m in
                                                                               (data.get("report") or {}).get("milestones", [])],
            "last_lines": data["lines"][-12:]}


def wall_clock_flag(context) -> int | None:
    """FLAG_SET_WALL_CLOCK (81, `knowledge/milestones.json` ch1_clock) by the harness's own second path."""
    from ai_player.gates.play_harness import story_truth

    try:
        return story_truth(context, guard=True)["marks"].get("SET_WALL_CLOCK")
    except RuntimeError:
        return None  # the save blocks may be moving this frame


def selftest(args) -> dict:
    """(module docstring) THE CLOCK SCENE, the ch1_clock fixture's own: from `clock_room.ss1` (BRENDAN's room, at (5, 2)
    below the wall clock at (5, 1), the clock not set) the harness turns Up and presses A on the clock: "The clock is
    stopped" is a TEXT BOX the read must call NOT free; then A on each wait and in the wall clock's own screen until
    FLAG_SET_WALL_CLOCK is set and MOM's "How do you like your room" waits: NOT free WITH the flag set (the state a
    `ch1_clock` run ends in if it ends "done" before the scene is over); then the scene played out: FREE, held."""
    root = args.root.resolve()
    context = boot_at(root)
    from ai_player.gates.play_harness import text_waits_now

    emulator = context.emulator
    out: dict = {"cases": [], "trace": []}

    def check_here(name: str, expect_free: bool) -> None:
        """Every read of THIS frame (the state restored after: the scene goes on from here)."""
        saved = emulator.get_save_state()
        pages = message_pages()
        behaviour = accepts_input(emulator)
        verdict = settled(emulator, args.after)
        emulator.load_save_state(saved)
        ok = (verdict["free_held"] is expect_free and verdict["free_at_return"] is expect_free
              and behaviour.get("turned") is expect_free)
        out["cases"].append({"case": name, "expect_free": expect_free, "flag_set_wall_clock": wall_clock_flag(context),
                             "frame": emulator.get_frame_count(), "read": verdict, "accepts_input": behaviour,
                             "message_pages": pages[:4] if not expect_free else "(not shown: the buffer holds the LAST "
                                                                                 "message, stale on a free screen)",
                             "ok": ok})

    def until(test, frames: int, press_a_on_waits: bool = False, press_a_off_field: bool = False) -> int | None:
        """Run frames until `test()` holds (bounded); A only when the game waits for it (`text_waits_now`) and, in a
        screen that is not the field (the wall clock's: A asks "is this the correct time?", whose YES/NO starts on NO,
        `src/wallclock.c:839` CreateYesNoMenu(..., 1), so Up then A), A and Up in turn every 30 frames."""
        for frame in range(frames):
            if test():
                return frame
            if press_a_off_field and not game_screen()["overworld"]:
                if frame % 60 == 0:
                    emulator.press_button("A")
                elif frame % 60 == 30:
                    emulator.press_button("Up")
            elif press_a_on_waits and text_waits_now():
                emulator.press_button("A")
            emulator.run_single_frame()
        return None

    # (1) BRENDAN's room, the clock not set: free
    emulator.load_save_state((args.fixtures / "clock_room.ss1").read_bytes())
    for _ in range(30):
        emulator.run_single_frame()
    check_here("clock_room.ss1, 30 frames in, no input: free", True)
    # (2) face the clock and press A: "The clock is stopped..." waits for A
    emulator.hold_button("Up")
    for _ in range(3):
        emulator.run_single_frame()
    emulator.release_button("Up")
    for _ in range(20):
        emulator.run_single_frame()
    emulator.press_button("A")
    emulator.run_single_frame()
    waited = until(text_waits_now, 600)
    out["trace"].append({"clock_text_waits_after_frames": waited})
    if waited is not None:
        check_here("the wall clock's 'The clock is stopped' text box, waiting for A (no input)", False)
        # (3) play on: A on each wait, A in the wall clock's screen, until the flag is set and MOM's text waits
        flagged = until(lambda: wall_clock_flag(context) == 1, 6000, press_a_on_waits=True, press_a_off_field=True)
        out["trace"].append({"flag_set_after_frames": flagged, "screen_when_flag_first_read_set": game_screen()})
        if flagged is not None:
            mom = until(text_waits_now, 2000)
            out["trace"].append({"mom_text_waits_after_frames": mom})
            if mom is not None:
                check_here("MOM's 'How do you like your room' text box, FLAG_SET_WALL_CLOCK set, waiting for A", False)
                # (4) the scene played out with A only on a wait: then free, held
                free = until(lambda: game_screen()["free"], 3000, press_a_on_waits=True)
                out["trace"].append({"free_after_frames": free})
                if free is not None:
                    for _ in range(30):  # a person takes in the room: well past any one-frame free read
                        emulator.run_single_frame()
                    check_here("after MOM's scene, played out with A only on a wait: free", True)
    # (5) a free overworld frame on ROUTE 101
    emulator.load_save_state((args.fixtures / "route101_south.ss1").read_bytes())
    for _ in range(30):
        emulator.run_single_frame()
    check_here("route101_south.ss1, 30 frames in, no input: free", True)
    # all five cases reached, each read as expected (two NOT free, three free), and the MOM case WITH the flag set
    out["ok"] = (len(out["cases"]) == 5 and all(c["ok"] for c in out["cases"])
                 and [c["expect_free"] for c in out["cases"]] == [True, False, False, True, True]
                 and out["cases"][2]["flag_set_wall_clock"] == 1)
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("run", "selftest"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--target")
    parser.add_argument("--frames", type=int, default=300000)
    parser.add_argument("--after", type=int, default=DEFAULT_AFTER)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--world-in", type=Path)
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--out", type=Path, default=Path(tempfile.mkdtemp(prefix="r5_probe_")))
    args = parser.parse_args()
    if args.mode == "run":
        if args.seed is None or not args.target:
            parser.error("run needs --seed and --target")
        result = run(args)
        print("PROBE " + json.dumps(result, ensure_ascii=False), flush=True)
        return 0
    if args.fixtures is None:
        parser.error("selftest needs --fixtures")
    result = selftest(args)
    print("SELFTEST " + json.dumps(result, ensure_ascii=False), flush=True)
    print(f"SELFTEST VERDICT: {'PASS' if result['ok'] else 'FAIL'}", flush=True)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
