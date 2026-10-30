"""R1 + R2 BUILD STEP 2 (TEST SIDE, development; in no lane): the AI's OWN EYES on the save dialog and the title, measured
against the harness's RAM truth (build spec `PROJECT KNOWLEDGE/ai-research-notes/2026-10-29-R1R2-BUILD-SPEC.md` section 8
step 2; finding F9).

    py -3.12 -B probe_save_eyes.py run --fixtures DIR --out DIR [--build-root DIR] [--arms EYES-SAVER,TRUNC,KM-FIRST]
                                       [--fault building_takes_input|playtime_seconds] [--child-timeout SECONDS]
    prints one `PROBE {json}` line per arm and `PROBE SUMMARY {json}`; exit 0 only when every check holds.

WHAT IT DRIVES (test-side presses; never the AI's hands or brain), every frame recording the AI's OWN look
(`host/eyes.py` FrameworkEyes) beside the harness's own reads (`probe_save_kill.py`'s Saver record: the callbacks by symbol,
text printer 0, the play time in RAM; the task list, `sStartMenuCursorPos`, `sMenu`):
  * arm EYES-SAVER, on `route101_south.ss1` with a FILE-BACKED cart (the probe's Saver; its profile under `--out`):
      1. the stale-callback sequence G1 names: open the start menu, close it with B, open it again, close it;
      2. save 1 with a NO first: SAVE, answer NO (the menu comes back, `sSaveDialogCallback` left at an input callback),
         SAVE again, answer YES (one question: the fixture's RAM says a different file, `gDifferentSaveFile` 1);
      3. one tile walked, then the menu OPENED AFTER A SUCCESSFUL SAVE (`gMenuCallback` stale at SaveCallback) and save 2
         (two questions); one more tile and save 3;
      4. then free on the overworld until the play time's minute TICKS (bounded), so a tick is among the recorded frames.
    Every press is paced as the AI's slowest (`hands/pad.py` HUMAN_PACING: a page read for `read_max`, a menu looked at for
    the longest `think`, a press held its longest and its longest gap), so "YES to free" is measured with the AI's pacing,
    the free screen held for the longest thinking pause (PL-18's second look).
  * arms TRUNC and KM-FIRST (the probe's own child A, `probe_save_kill.py child --role saver`, killed by ITS PID at its
    READY; TRUNC's file then cut to 64 KB): a continuer child boots the killed cart and records the AI's look at every
    frame of the title, the error page (A only once it is printed) and the main menu.

WHAT IT CHECKS (STOP rule of step 2: any check that does not hold, or a reading that cannot be made, fails the run):
  * the start menu: on every frame its task runs, the AI's view equals the harness's own rule (`expected_ui`): taking input
    only under `Task_ShowStartMenu` past data[0] 0 with `gMenuCallback` HandleStartMenuInput, the cursor
    `sStartMenuCursorPos`; NOT taking input on every STALE-callback frame (counted, and each kind must OCCUR, or the arm is
    vacuous); the save's yes/no `save_yes_no` with `sMenu`'s cursor;
  * each page's words (`skills/saving.py` save_page): CONFIRM / OVERWRITE at the yes/no, SAVING whole before the write, SAVED;
  * the AI's `play_time` equals RAM's (hours, minutes) on EVERY recorded frame it was read, a minute tick included, and
    neither moves through any write (e3 to e4);
  * the longest STILL stretch in the dialog (`hands/dialogue.py` seen_now unchanged) is at most 900 frames;
  * at the title: both error pages' words from printer 7 (the AI's text equals the harness's `printer_page(7)` and
    `error_page` names it), and the CONTINUE window's (hours, minutes) equal SaveBlock2's in RAM on every main-menu frame.
`--fault building_takes_input` plants the PRE-R1 start-menu rule in the AI's eyes (every start-menu view taking input, the
building `StartMenuTask` and the stale frames included) and `playtime_seconds` compares the AI's minutes with RAM's SECONDS:
each must FAIL.
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_player.gates import probe_save_kill as psk  # noqa: E402

#: `hands/pad.py` HUMAN_PACING's slowest: a page read (read_max), a menu looked at (think), a press held, its gap
READ_MAX, THINK_MAX, HOLD_MAX, GAP_MAX = 150, 45, 7, 18
#: the build spec's bound on a still stretch in the dialog (step 2's STOP rule)
STILL_LIMIT = 900
#: frames the free screen must hold before the save counts as closed: the AI's second look a thinking pause later (PL-18)
FREE_HOLD = THINK_MAX
MINUTE_WAIT = 4000
FAULTS = ("building_takes_input", "playtime_seconds")
STALE_KINDS = ("building", "first_frame", "before_init_save")


# ------------------------------------------------------------------ the harness's own rule (a second path, by symbol)
def expected_ui(tasks: set, data0: int | None, mcb: str | None, cb: str | None) -> tuple[str | None, bool | None]:
    """What the AI's view of the start menu SHOULD be, from the harness's reads (`fn_name`: the framework's symbol lookup,
    not the AI's table): (kind, accepts), or (None, None) when no start-menu task runs."""
    if "StartMenuTask" in tasks:
        return "start_menu", False
    if "Task_ShowStartMenu" not in tasks:
        return None, None
    if not data0:
        return "start_menu", False
    if mcb == "HandleStartMenuInput":
        return "start_menu", True
    if mcb in ("StartMenuSaveCallback", "SaveStartCallback"):
        return "save_dialog", False
    if mcb == "SaveCallback":
        return ("save_yes_no", True) if cb in psk.INPUT_CALLBACKS else ("save_dialog", False)
    return "start_menu", False


def stale_kind(tasks: set, data0: int | None, mcb: str | None, cb: str | None) -> str | None:
    """A frame on which a callback the game left behind would read as "takes input" under a callback-first rule."""
    if "StartMenuTask" in tasks and (mcb == "HandleStartMenuInput" or (mcb == "SaveCallback" and cb in psk.INPUT_CALLBACKS)):
        return "building"
    if "Task_ShowStartMenu" in tasks and not data0 and mcb in ("HandleStartMenuInput", "SaveCallback"):
        return "first_frame"
    if mcb in ("StartMenuSaveCallback", "SaveStartCallback") and cb in psk.INPUT_CALLBACKS:
        return "before_init_save"
    return None


def plant_fault(name: str | None) -> None:
    """`--fault building_takes_input`: the PRE-R1 rule planted in the AI's eyes (`eyes/screens.py` before R1 read the start
    menu as taking input whenever its menu bytes were read, `StartMenuTask` included, with no task or callback rule): every
    start-menu view reads as taking input. (`host/eyes.py` is sealed, so the fault is planted in the rule it calls.)"""
    if name != "building_takes_input":
        return
    from ai_player.eyes import screens
    from ai_player.eyes.observation import MenuView

    original = screens._start_menu_view

    def pre_r1(tasks, raw):
        view = original(tasks, raw)
        if view.kind == "start_menu" and not view.accepts_input and raw.get("start_menu") is not None:
            return MenuView(kind="start_menu", options=view.options, cursor=view.cursor, accepts_input=True)
        return view

    screens._start_menu_view = pre_r1


def harness_reads() -> dict:
    from modules.memory import read_symbol
    from modules.tasks import TaskList

    tasks = TaskList(read_symbol("gTasks"))
    names = {name for name in ("StartMenuTask", "Task_ShowStartMenu") if tasks[name] is not None}
    show = tasks["Task_ShowStartMenu"]
    menu = bytes(read_symbol("sMenu", 0, 12))
    return {"tasks": names, "data0": show.data_value(0) if show is not None else None,
            "start_cursor": psk.sym_u("sStartMenuCursorPos", 1), "smenu_cursor": menu[2] - 256 if menu[2] >= 128 else menu[2]}


# ------------------------------------------------------------------ child: the saver with the AI's eyes
class EyeSaver(psk.Saver):
    def __init__(self, args) -> None:
        super().__init__(args)
        atexit.unregister(self.emulator.shutdown)  # no `.ss1` left (test side; it changes nothing measured)
        from ai_player.host.eyes import FrameworkEyes

        plant_fault(args.fault)
        self.fault = args.fault
        self.eyes = FrameworkEyes()
        self.eyes_record = open(args.eyes_record, "w", encoding="utf-8", buffering=1)
        self.checks = {"frames": 0, "play_time_read": 0, "play_time_unread": [], "play_time_mismatch": [], "ticks": [],
                       "ui_frames": 0, "ui_mismatch": [], "cursor_mismatch": [], "input_frames": {},
                       "stale": {k: 0 for k in STALE_KINDS}, "stale_accepted": [], "pages": [], "page_mismatch": [],
                       "still": {"longest": 0, "at": None}, "write_play_time": [], "problems": []}
        self.counts: dict[str, int] = {}
        self.prev_seen = None
        self.still_from = None
        self.prev_ai_time = None
        self.prev_page = None
        self.presses: list[list] = []

    def note(self, key: str, item) -> None:
        """A failing frame: COUNTED always (`counts`), its details kept for the first 30 (the RESULT line stays bounded)."""
        self.counts[key] = self.counts.get(key, 0) + 1
        if len(self.checks[key]) < 30:
            self.checks[key].append(item)

    def observe(self, press: str | None, phase: str) -> dict:
        from ai_player.hands.dialogue import seen_now
        from ai_player.skills.saving import save_page

        rec = super().observe(press, phase)
        look = self.eyes.look()
        h = harness_reads()
        c = self.checks
        f = rec["f"]
        c["frames"] += 1
        ui = look.screen.ui
        ram = (rec["pt"][0], rec["pt"][2] if self.fault == "playtime_seconds" else rec["pt"][1])
        ai_time = look.progress.play_time if look.progress is not None else None
        in_dialog = bool(h["tasks"])
        if ai_time is None:
            if in_dialog:
                self.note("play_time_unread", f)
        else:
            c["play_time_read"] += 1
            if tuple(ai_time) != ram:
                self.note("play_time_mismatch", [f, list(ai_time), list(ram)])
            if self.prev_ai_time is not None and tuple(ai_time) != self.prev_ai_time:
                c["ticks"].append([f, list(self.prev_ai_time), list(ai_time), list(rec["pt"])])
            self.prev_ai_time = tuple(ai_time)
        kind, accepts = expected_ui(h["tasks"], h["data0"], rec["mcb"], rec["cb"])
        got = (ui.kind, ui.accepts_input) if ui is not None else (None, None)
        if kind is not None:
            c["ui_frames"] += 1
            if got != (kind, accepts):
                self.note("ui_mismatch", [f, [kind, accepts], list(got), rec["mcb"], rec["cb"], h["data0"], sorted(h["tasks"])])
            if accepts:
                key = f"{kind}:{rec['mcb']}:{rec['cb'] if kind == 'save_yes_no' else ''}"
                c["input_frames"][key] = c["input_frames"].get(key, 0) + 1
                want = h["start_cursor"] if kind == "start_menu" else h["smenu_cursor"]
                if ui is None or ui.cursor != want:
                    self.note("cursor_mismatch", [f, kind, want, ui.cursor if ui else None])
        elif ui is not None and ui.kind in ("start_menu", "save_yes_no", "save_dialog"):
            self.note("ui_mismatch", [f, [None, None], list(got), rec["mcb"], rec["cb"], h["data0"], []])
        stale = stale_kind(h["tasks"], h["data0"], rec["mcb"], rec["cb"])
        if stale:
            c["stale"][stale] += 1
            if ui is not None and ui.accepts_input:
                self.note("stale_accepted", [f, stale, ui.kind, rec["mcb"], rec["cb"]])
        page = save_page(look.screen.text) if ui is not None and ui.kind in ("save_yes_no", "save_dialog") else None
        if ui is not None and ui.kind == "save_yes_no" and ui.accepts_input:
            want = "CONFIRM" if rec["cb"] == "SaveConfirmInputCallback" else "OVERWRITE"
            if page != want:
                self.note("page_mismatch", [f, want, page, look.screen.text])
        if (got[0], page) != self.prev_page and got[0] in ("save_yes_no", "save_dialog"):
            c["pages"].append([f, got[0], page, look.screen.text])
        self.prev_page = (got[0], page)
        seen = seen_now(look)
        if in_dialog and seen == self.prev_seen:
            run = f - self.still_from + 1
            if run > c["still"]["longest"]:
                c["still"] = {"longest": run, "at": [self.still_from, f], "ui": got[0], "page": page}
        else:
            self.still_from = f
        self.prev_seen = seen if in_dialog else None
        if look.problems and in_dialog:
            self.note("problems", [f, list(look.problems)[:3]])
        self.eyes_record.write(json.dumps({
            "f": f, "ph": phase, "in": press, "ui": [got[0], got[1], ui.cursor if ui else None], "page": page,
            "text": look.screen.text if in_dialog else None, "wait": look.screen.wait_reason,
            "pt_ai": list(ai_time) if ai_time else None, "pt_ram": rec["pt"], "mcb": rec["mcb"], "cb": rec["cb"],
            "tasks": sorted(h["tasks"]), "d0": h["data0"], "exp": [kind, accepts], "stale": stale}, ensure_ascii=False) + "\n")
        return rec

    # presses at the AI's slowest pace
    def press(self, button: str, phase: str, hold: int = HOLD_MAX, gap: int = GAP_MAX) -> int:
        self.emulator.hold_button(button)
        first = None
        try:
            for _ in range(hold):
                rec = self.frame(phase=phase)
                first = rec["f"] if first is None else first
        finally:
            self.emulator.release_button(button)
        self.presses.append([first, button, phase])
        self.wait(gap, phase)
        return first

    def until_free(self, phase: str, bound: int) -> int:
        """Frames until the harness's free read holds FREE_HOLD frames (the AI's second look); returns the frame it held to."""
        since = None
        for _ in range(bound):
            rec = self.frame(phase=phase)
            if rec["free"]:
                since = rec["f"] if since is None else since
                if rec["f"] - since >= FREE_HOLD:
                    return rec["f"]
            else:
                since = None
        raise psk.ProbeAbort(f"{phase}: the screen was not free (held {FREE_HOLD}) within {bound} frames")

    def until_menu_input(self, phase: str) -> int:
        rec = self.until(lambda r: self.menu_open(), 200, "the start menu takes input", phase)
        self.wait(THINK_MAX, phase)
        return rec["f"]

    def cursor_to_save(self, phase: str) -> None:
        from modules.memory import read_symbol

        for _ in range(12):
            count = psk.sym_u("sNumStartMenuActions", 1)
            actions = list(bytes(read_symbol("sCurrentStartMenuActions", 0, 9)))[:count]
            cursor = psk.sym_u("sStartMenuCursorPos", 1)
            if psk.MENU_ACTION_SAVE not in actions:
                raise psk.ProbeAbort(f"no SAVE in the start menu: {actions}")
            target = actions.index(psk.MENU_ACTION_SAVE)
            if cursor == target:
                return
            self.press("Down" if cursor < target else "Up", phase, hold=5, gap=12)
        raise psk.ProbeAbort("the cursor never reached SAVE")

    def question(self, phase: str) -> dict:
        """Frames until a save question takes input (its page fully printed), then the AI's reading pause."""
        rec = self.until(lambda r: r["cb"] in psk.INPUT_CALLBACKS and not r["p0"][0], 1500, "a save question", phase)
        self.wait(READ_MAX + THINK_MAX, phase)
        return rec

    def start_save(self, index: int) -> psk.Timeline:
        flags = psk.save_flags()
        self.counter = flags["gSaveCounter"] + 1
        self.start_flash = bytes(self.emulator.read_save_data())
        bookkeeping = self.savedata()
        start = {"frame": self.emulator.get_frame_count(), "flags": flags, "flushes": self.flushes,
                 "saves": psk.saves_listing(self.saves_dir), "size": self.size_now(), "truth": psk.ram_truth(self.emulator),
                 "dirt": [bookkeeping["dirty"], bookkeeping["dirtAge"]]}
        timeline = self.timeline = psk.Timeline(index, self.counter, start, self.args.after)
        self.result["saves"].append(timeline)
        return timeline

    def paced_save(self, index: int, first_no: bool) -> dict:
        timeline = self.start_save(index)
        out: dict = {"save": index, "yes": [], "no": None}
        timeline.events["e1"] = self.press("Start", f"S{index}.start")
        self.until_menu_input(f"S{index}.menu")
        self.cursor_to_save(f"S{index}.cursor")
        self.wait(THINK_MAX, f"S{index}.cursor")
        self.press("A", f"S{index}.save")
        if first_no:
            asked = self.question(f"S{index}.no")
            self.press("Down", f"S{index}.no", hold=5, gap=12)
            out["no"] = {"asked": asked["f"], "pressed": self.press("A", f"S{index}.no")}
            self.until_menu_input(f"S{index}.after-no")
            self.cursor_to_save(f"S{index}.cursor2")
            self.wait(THINK_MAX, f"S{index}.cursor2")
            self.press("A", f"S{index}.save2")
        for _ in range(3):
            asked = self.question(f"S{index}.yes")
            out["yes"].append({"callback": asked["cb"], "asked": asked["f"], "pages": list(self.pages),
                               "pressed": self.press("A", f"S{index}.yes")})
            nxt = self.until(lambda r: r["cb"] in psk.INPUT_CALLBACKS + ("SaveDoSaveCallback",) and not r["p0"][0], 1500,
                             "the next question or the write", f"S{index}.yes")
            if nxt["cb"] == "SaveDoSaveCallback":
                break
        else:
            raise psk.ProbeAbort("more than three questions")
        out["free_held_at"] = self.until_free(f"S{index}.saving", 4000)
        ev = timeline.events
        if not all(k in ev for k in ("e1", "e2", "e3", "e4", "e5")):
            raise psk.ProbeAbort(f"save {index}: events missing {sorted(ev)}")
        out["events"] = dict(ev)
        out["write_frames"] = ev["e4"] - ev["e3"]
        out["yes_to_free_first"] = out["free_held_at"] - out["yes"][0]["pressed"]
        out["yes_to_free_last"] = out["free_held_at"] - out["yes"][-1]["pressed"]
        out["truth"] = timeline.truth
        return out

    def check_write_play_time(self, saves: list[dict]) -> None:
        """Neither the AI's play time nor RAM's (h, m, s, vblank) moves from e3 to e4 of each write (the eyes record)."""
        frames = {}
        with open(self.args.eyes_record, encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                frames[row["f"]] = row
        for save in saves:
            e3, e4 = save["events"]["e3"], save["events"]["e4"]
            ai = {tuple(frames[f]["pt_ai"]) for f in range(e3, e4 + 1) if f in frames and frames[f]["pt_ai"]}
            ram = {tuple(frames[f]["pt_ram"]) for f in range(e3, e4 + 1) if f in frames}
            self.checks["write_play_time"].append({"save": save["save"], "e3": e3, "e4": e4, "ai_values": sorted(ai),
                                                   "ram_values": sorted(ram), "frames": e4 - e3 + 1,
                                                   "recorded": sum(1 for f in range(e3, e4 + 1) if f in frames)})

    def classify_page_mismatches(self) -> None:
        """A yes/no taking input whose page is not its question, split by what the NEXT frame shows (the eyes record):
        a LAG frame is one on which the game had already TAKEN the answer (the callbacks differ on the next frame: the game's
        loop, acting on the answer, ran past the frame boundary, so the frame ended mid-way with the question's window gone
        and the old callbacks still set; measured on the NO path's `InitStartMenu`). Both paths read the same RAM there, so it
        is reported as a FINDING (`lag_frames`), never hidden; any other mismatch fails the run (`page_mismatch`)."""
        frames = {}
        with open(self.args.eyes_record, encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                frames[row["f"]] = row
        lag, other = [], []
        for item in self.checks["page_mismatch"]:
            f = item[0]
            now, nxt = frames.get(f), frames.get(f + 1)
            if now and nxt and (nxt["mcb"], nxt["cb"]) != (now["mcb"], now["cb"]):
                lag.append(item + [[nxt["mcb"], nxt["cb"]], [p for p in self.presses if 0 <= f - p[0] <= HOLD_MAX + 2]])
            else:
                other.append(item)
        self.checks["lag_frames"] = lag
        self.checks["page_mismatch"] = other
        self.counts["page_mismatch"] = len(other) if self.counts.get("page_mismatch", 0) <= 30 else self.counts["page_mismatch"]

    def run(self) -> None:
        self.load_fixture()
        seq: dict = {"stale_menu": []}
        for i in range(2):  # 1. open, close with B, twice
            opened = self.press("Start", "G1.open")
            self.until_menu_input("G1.menu")
            seq["stale_menu"].append({"opened": opened, "b": self.press("B", "G1.close")})
            self.until_free("G1.closed", 600)
        saves = [self.paced_save(1, first_no=True)]  # 2. NO, then YES
        self.result.setdefault("walks", []).append(self.walk_one_tile())
        saves.append(self.paced_save(2, first_no=False))  # 3. the menu opened after a successful save
        self.result["walks"].append(self.walk_one_tile())
        saves.append(self.paced_save(3, first_no=False))
        self.timeline = None
        start_minute = self.checks["ticks"][:]
        for _ in range(MINUTE_WAIT):  # 4. free until the minute ticks, then 60 frames more
            self.frame(phase="minute")
            if len(self.checks["ticks"]) > len(start_minute):
                self.wait(60, "minute")
                break
        self.eyes_record.flush()
        self.check_write_play_time(saves)
        self.classify_page_mismatches()
        payload = {**self.payload(), "paced_saves": saves, "sequence": seq, "checks": self.checks, "counts": self.counts,
                   "presses": self.presses, "fault": self.fault}
        self.record.flush()
        print("RESULT " + json.dumps(payload, ensure_ascii=False), flush=True)
        os._exit(0)


# ------------------------------------------------------------------ child: the continuer with the AI's eyes
def eye_continuer(args) -> dict:
    from ai_player.gates.hands_harness import pin_game_clock
    from ai_player.gates.rate_step5 import GAME_CLOCK
    from ai_player.skills.saving import error_page

    profile = Path(args.profile)
    context = psk.boot_profile(profile, file_backed=True)  # puts the framework on the path: the AI's eyes import it
    from ai_player.host.eyes import FrameworkEyes

    emulator = context.emulator
    atexit.unregister(emulator.shutdown)
    pin_game_clock(emulator, GAME_CLOCK)
    eyes = FrameworkEyes()
    out: dict = {"ss1_at_start": (profile / "current_state.ss1").exists(), "pages": [], "presses": [], "menu_frames": 0,
                 "time_mismatch": [], "text_mismatch": [], "menu": None, "frames": 0}
    record = open(args.eyes_record, "w", encoding="utf-8", buffering=1)
    answered: dict[str, int] = {}
    menu_since = None
    for i in range(6000):
        name, data0, data1 = psk.main_menu_task()
        press = None
        if name is None and i % 20 == 10:
            press = "Start"
        elif name in psk.ERROR_TASKS:
            page = psk.printer_page(7)
            if not page["active"]:
                key = f"{name}:{page['symbol']}"
                answered.setdefault(key, emulator.get_frame_count())
                if emulator.get_frame_count() - answered[key] in (READ_MAX, READ_MAX + 60):
                    press = "A"
        if press:
            emulator.press_button(press)
            out["presses"].append([emulator.get_frame_count() + 1, press, name])
        emulator.run_single_frame()
        look = eyes.look()
        out["frames"] += 1
        f = emulator.get_frame_count()
        name, data0, data1 = psk.main_menu_task()
        ui = look.screen.ui
        row = {"f": f, "in": press, "task": name, "d0": data0, "ui": [ui.kind, ui.accepts_input, ui.hours, ui.minutes]
               if ui else None, "text": look.screen.text, "wait": look.screen.wait_reason}
        if name in psk.ERROR_TASKS:
            page = psk.printer_page(7)
            row["p7"] = [page["active"], page["state"], page["symbol"], page["text"]]
            if not page["active"]:
                ai_page = error_page(look.screen.text)
                if not out["pages"] or out["pages"][-1]["symbol"] != page["symbol"]:
                    out["pages"].append({"frame": f, "task": name, "symbol": page["symbol"], "harness_text": page["text"],
                                         "ai_text": look.screen.text, "ai_page": ai_page})
                from ai_player.skills.saving import fold

                if fold(look.screen.text) != fold(page["text"]):
                    out["text_mismatch"].append([f, look.screen.text, page["text"]])
        if name == "Task_HandleMainMenuInput":
            sb2 = psk.sym_u("gSaveBlock2Ptr", 4)
            play = bytes(emulator.read_bytes(sb2 + psk.SB2_PLAY_TIME, 3))
            ram = (psk._u16(play, 0), play[2])
            out["menu_frames"] += 1
            want = ram if (data0 or 0) >= psk.HAS_SAVED_GAME else (None, None)
            got = (ui.hours, ui.minutes) if ui is not None and ui.kind == "main_menu" else ("no view",)
            if got != want:
                out["time_mismatch"].append([f, list(got), list(want)])
            row["ram_time"] = list(ram)
            if out["menu"] is None:
                out["menu"] = {"frame": f, "menu_type": data0, "cursor": data1, "options": list(ui.options) if ui else None,
                               "ai_time": [ui.hours, ui.minutes] if ui else None, "ram_time": list(ram),
                               "accepts": ui.accepts_input if ui else None, "status": psk.sym_u("gSaveFileStatus", 2),
                               "boot_truth": psk.ram_truth(emulator)}
            menu_since = f if menu_since is None else menu_since
        record.write(json.dumps(row, ensure_ascii=False) + "\n")
        if menu_since is not None and f - menu_since >= 60:
            break
    else:
        raise psk.ProbeAbort("the main menu did not take input for 60 frames within 6000 frames of power-on")
    record.close()
    return out


def child(args) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    try:
        if args.role == "eyes-saver":
            EyeSaver(args).run()
            return 0
        print("RESULT " + json.dumps(eye_continuer(args), ensure_ascii=False), flush=True)
        return 0
    except psk.ProbeAbort as error:
        print("ABORT " + json.dumps({"abort": str(error)}, ensure_ascii=False), flush=True)
        os._exit(3)


# ------------------------------------------------------------------ the parent
def grade_saver(result: dict) -> dict:
    c = result["checks"]
    n = result.get("counts") or {}
    saves = result["paced_saves"]
    questions = [[y["callback"] for y in s["yes"]] for s in saves]
    failures = []
    for key, words in (("play_time_mismatch", "the AI's play time differs from RAM's"),
                       ("play_time_unread", "the AI's play time was not read (dialog frames)"),
                       ("ui_mismatch", "the AI's start-menu view differs from the harness's rule"),
                       ("cursor_mismatch", "the cursor differs (input frames)"),
                       ("stale_accepted", "a stale callback read as input"),
                       ("page_mismatch", "a question's words not read as its page"),
                       ("problems", "the AI's look reported a problem (dialog frames)")):
        if n.get(key):
            failures.append(f"{words} on {n[key]} frames")
    if not c["ticks"]:
        failures.append("no minute tick among the recorded frames")
    missing = [k for k, count in c["stale"].items() if count == 0]
    if missing:
        failures.append(f"VACUOUS: no stale frame of kind {missing}")
    pages_seen = {p[2] for p in c["pages"]}
    for page in ("CONFIRM", "OVERWRITE", "SAVING", "SAVED"):
        if page not in pages_seen:
            failures.append(f"the page {page} was never read")
    if c["still"]["longest"] > STILL_LIMIT:
        failures.append(f"a still stretch of {c['still']['longest']} frames in the dialog (limit {STILL_LIMIT})")
    for w in c["write_play_time"]:
        if len(w["ai_values"]) != 1 or len(w["ram_values"]) != 1 or w["recorded"] != w["frames"]:
            failures.append(f"save {w['save']}: the play time moved, or was not read, through the write: {w}")
    keys = c["input_frames"]
    for needed in ("start_menu:HandleStartMenuInput:", "save_yes_no:SaveCallback:SaveConfirmInputCallback",
                   "save_yes_no:SaveCallback:SaveOverwriteInputCallback"):
        if keys.get(needed, 0) == 0:
            failures.append(f"VACUOUS: no input frame of {needed}")
    if questions != [["SaveConfirmInputCallback"], ["SaveConfirmInputCallback", "SaveOverwriteInputCallback"],
                     ["SaveConfirmInputCallback", "SaveOverwriteInputCallback"]]:
        failures.append(f"unexpected questions {questions}")
    timelines = {t["save"]: t for t in result["saves"]}
    first_sector = []
    for s in saves:
        frames = sorted((timelines[s["save"]].get("sector_complete_frames") or {}).values())
        first_sector.append(frames[0] - s["events"]["e3"] if frames else None)
    first_saving = []
    for s in saves:  # the AI's first look showing the WHOLE SAVING page, against e3 (the stamp's look, D4 / T1)
        seen = [p[0] for p in c["pages"] if p[2] == "SAVING" and s["events"]["e1"] <= p[0] <= s["events"]["e4"]]
        first_saving.append(seen[0] - s["events"]["e3"] if seen else None)
    # e5 = "saved the game." fully printed: the decomp's own mark, SaveSuccessCallback handing on to
    # SaveReturnSuccessCallback once printer 0 is idle (`e5_jingle`); probe_save_kill's Timeline `e5` can fire at e4 when the
    # message is expanded on the frame before its printer starts (measured here), so it is not used
    e3_to_e5 = [s["events"].get("e5_jingle", 0) - s["events"]["e3"] for s in saves]
    report = {  # the probe report's measured values (2026-10-29-R1R2-PROBE-REPORT.md FR4) against this trajectory's
        "write_frames 256-261": [[s["write_frames"], 256 <= s["write_frames"] <= 261] for s in saves],
        "first sector e3+19 (save 1), e3+18 (saves 2, 3)": [[n, n == (19 if i == 0 else 18)] for i, n in enumerate(first_sector)],
        "e3 to e5 339-343": [[n, 339 <= n <= 343] for n in e3_to_e5],
        "flush e6 - e4 = 16": [[s["events"].get("e6", 0) - s["events"]["e4"], s["events"].get("e6", 0) - s["events"]["e4"] == 16]
                               for s in saves],
    }
    contradicted = [name for name, rows in report.items() if not all(ok for _, ok in rows)]
    return {"failures": failures, "pass": not failures, "probe_report_contradicted": contradicted,
            "measured": {
                "vs_probe_report": report, "first_sector_after_e3": first_sector,
                "first_full_saving_look_minus_e3": first_saving, "lag_frames": c.get("lag_frames"),
                "write_frames": [s["write_frames"] for s in saves],
                "e3_to_e5": e3_to_e5,
                "yes_to_free_first": [s["yes_to_free_first"] for s in saves],
                "yes_to_free_last": [s["yes_to_free_last"] for s in saves],
                "start_to_free": [s["free_held_at"] - s["events"]["e1"] for s in saves],
                "longest_still": c["still"], "stale_frames": c["stale"], "input_frames": keys,
                "play_time_frames_compared": c["play_time_read"], "ticks": c["ticks"], "counts": n,
                "dialog_frames_compared": c["ui_frames"],
                "write_play_time": c["write_play_time"], "questions": questions,
                "pages": [[p[0], p[1], p[2]] for p in c["pages"]],
                "truths": {f"S{s['save']}": s["truth"] for s in saves}}}


def grade_continuer(result: dict, expect: str) -> dict:
    failures = []
    pages = result.get("pages") or []
    ai_pages = [p["ai_page"] for p in pages]
    if expect not in ai_pages:
        failures.append(f"the {expect} page was not read by its words: {ai_pages}")
    if result["text_mismatch"]:
        failures.append(f"the AI's text differs from printer 7's on {len(result['text_mismatch'])} frames")
    if result["time_mismatch"]:
        failures.append(f"the CONTINUE TIME differs from RAM's on {len(result['time_mismatch'])} frames")
    if result["menu_frames"] == 0:
        failures.append("no main-menu frame")
    return {"failures": failures, "pass": not failures}


def run_parent(args) -> int:
    from ai_player.gates.hands_harness import PROFILE
    from ai_player.host.launcher import ENV_BUILD_ROOT, resolve_build_root

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    build_root = Path(args.build_root or os.environ.get(ENV_BUILD_ROOT) or resolve_build_root()).resolve()
    env = psk.child_env(build_root)
    donor = build_root / "profiles" / PROFILE / "metadata.yml"
    fixtures = args.fixtures.resolve()
    script = Path(__file__).resolve()
    kill_script = script.parent / "probe_save_kill.py"
    children: list = []
    rows = []
    began = time.time()
    arms = [a.strip() for a in (args.arms or "EYES-SAVER,TRUNC,KM-FIRST").split(",") if a.strip()]
    print("PROBE START " + json.dumps({"out": str(out), "build_root": str(build_root), "arms": arms, "fault": args.fault,
                                       "started": time.strftime("%Y-%m-%d %I:%M:%S %p")}), flush=True)

    def profile_for(name: str) -> Path:
        folder = out / name
        if folder.exists():
            raise SystemExit(f"{folder} exists: a fresh --out is needed")
        profile = folder / "profile"
        profile.mkdir(parents=True)
        shutil.copy2(donor, profile / "metadata.yml")
        (profile / "current_save.sav").write_bytes(b"")
        return profile

    for arm in arms:
        row: dict = {"arm": arm}
        profile = profile_for(arm)
        folder = profile.parent
        base = [sys.executable, "-B", str(script), "child", "--profile", str(profile), "--fixtures", str(fixtures)]
        if arm == "EYES-SAVER":
            cmd = base + ["--role", "eyes-saver", "--record", str(folder / "a_frames.jsonl"),
                          "--eyes-record", str(folder / "eyes_frames.jsonl")] + (["--fault", args.fault] if args.fault else [])
            a = psk.Child(cmd, env, ROOT, folder / "child.out", arm, "eyes-saver")
            children.append(a)
            word, result = a.wait_for(("RESULT", "ABORT"), args.child_timeout)
            row["child"] = {"pid": a.pid, "word": word, "exit": a.finish(120)}
            if word != "RESULT":
                row.update({"pass": False, "failures": [f"the saver ended with {word}: {result}"]})
            else:
                graded = grade_saver(result)
                row.update(graded)
                (folder / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            stop, saves = ("S2.e4+40", 2) if arm == "TRUNC" else ("S1.e3+128", 1)
            cmd = [sys.executable, "-B", str(kill_script), "child", "--profile", str(profile), "--fixtures", str(fixtures),
                   "--role", "saver", "--record", str(folder / "a_frames.jsonl"), "--saves", str(saves), "--stop", stop,
                   "--end", "kill"]
            a = psk.Child(cmd, env, ROOT, folder / "child_a.out", arm, "saver")
            children.append(a)
            word, ready = a.wait_for(("READY", "RESULT", "ABORT"), args.child_timeout)
            row["child_a"] = {"pid": a.pid, "word": word}
            if word != "READY":
                row.update({"pass": False, "failures": [f"child A ended with {word}"]})
                a.finish(60)
                rows.append(row)
                print("PROBE " + json.dumps(row, ensure_ascii=False), flush=True)
                continue
            row["child_a"]["kill"] = a.kill()
            save = profile / "current_save.sav"
            if arm == "TRUNC":
                os.truncate(save, psk.TRUNC_BYTES)
            parse = psk.parse_image(save.read_bytes())
            row["file"] = psk.file_verdict(parse, ready.get("truths") or {})
            row["truths"] = ready.get("truths")
            for path in [profile / "current_state.ss1"] + sorted((profile / "states").glob("*.ss1")):
                if path.exists():
                    path.unlink()
            b = psk.Child(base + ["--role", "eyes-continuer", "--record", str(folder / "b_unused.jsonl"),
                                  "--eyes-record", str(folder / "eyes_title.jsonl")], env, ROOT, folder / "child_b.out", arm,
                          "eyes-continuer")
            children.append(b)
            word_b, result_b = b.wait_for(("RESULT", "ABORT"), args.child_timeout)
            row["child_b"] = {"pid": b.pid, "word": word_b, "exit": b.finish(120)}
            if word_b != "RESULT":
                row.update({"pass": False, "failures": [f"the continuer ended with {word_b}: {result_b}"]})
            else:
                expect = "corrupted" if arm == "TRUNC" else "erased"
                row.update(grade_continuer(result_b, expect))
                row["title"] = {k: result_b.get(k) for k in ("pages", "menu", "menu_frames", "frames", "presses",
                                                              "text_mismatch", "time_mismatch")}
                if arm == "TRUNC":
                    s2 = (ready.get("truths") or {}).get("S2") or {}
                    menu = result_b.get("menu") or {}
                    want = (s2.get("play_time") or [None, None])[:2]
                    row["continue_time_vs_S2"] = {"ai": menu.get("ai_time"), "S2_truth": want,
                                                  "equal": menu.get("ai_time") == want}
                    if menu.get("ai_time") != want:
                        row["failures"].append(f"the CONTINUE TIME {menu.get('ai_time')} is not S2's {want}")
                        row["pass"] = False
                row["expected_file"] = "S2+ERROR" if arm == "TRUNC" else "CORRUPT"
                if row["file"] != row["expected_file"]:
                    row["failures"].append(f"FILE {row['file']}, expected {row['expected_file']}")
                    row["pass"] = False
        rows.append(row)
        print("PROBE " + json.dumps(row, ensure_ascii=False), flush=True)
    time.sleep(1.0)
    alive = [c.pid for c in children if c.proc.poll() is None]
    descendants = [d for c in children for d in c.descendants_alive(2.0)]
    summary = {"arms": [[r["arm"], r.get("pass"), r.get("failures")] for r in rows], "children": [c.pid for c in children],
               "probe_report_contradicted": {r["arm"]: r["probe_report_contradicted"] for r in rows
                                             if r.get("probe_report_contradicted")},
               "children_alive": alive, "descendants_alive": descendants, "fault": args.fault,
               "seconds": round(time.time() - began, 1), "ended": time.strftime("%Y-%m-%d %I:%M:%S %p")}
    ok = all(r.get("pass") for r in rows) and not alive and not descendants
    print("PROBE SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)
    if summary["probe_report_contradicted"]:
        print("PROBE REPORT CONTRADICTED: " + json.dumps(summary["probe_report_contradicted"]), flush=True)
    print(f"PROBE VERDICT: {'PASS' if ok else 'FAIL'}", flush=True)
    return 0 if ok else 1


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("run", "child"))
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--build-root")
    parser.add_argument("--arms")
    parser.add_argument("--fault", choices=FAULTS)
    parser.add_argument("--child-timeout", type=float, default=900.0)
    parser.add_argument("--role", choices=("eyes-saver", "eyes-continuer"))
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--eyes-record", type=Path)
    args = parser.parse_args()
    if args.mode == "child":
        # what probe_save_kill's Saver reads from its args
        args.anon, args.noread, args.stop, args.end, args.saves, args.after = False, False, None, "clean", 3, psk.DEFAULT_AFTER
        return child(args)
    if args.fixtures is None or args.out is None:
        parser.error("run needs --fixtures and --out")
    return run_parent(args)


if __name__ == "__main__":
    sys.exit(main())
