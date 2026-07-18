"""
Macro engine (sandbox enhancement A2, self-contained).

A macro is a frame-accurate sequence of button-hold steps recorded from
human play in Manual mode and replayed by the "Macro (Custom)" bot mode.
Stored per profile as human-editable YAML in `profiles/<name>/macros/`.

File format (one file per macro):

    # PokéBot macro — list of steps, each holds `buttons` for `frames` frames.
    # buttons: any of A, B, Select, Start, Right, Left, Up, Down, R, L
    # (an empty list is a wait). frames: whole number >= 1.
    name: my-macro
    steps:
      - buttons: [A]
        frames: 12
      - buttons: []
        frames: 30

The GUI stores which macro to replay (and whether to loop) in
`profiles/<name>/macros/_selected.yml`.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

from modules.context import context
from modules.libmgba import input_map, inputs_to_strings

SELECTION_FILE_NAME = "_selected.yml"

_FILE_HEADER = (
    "# PokéBot macro — list of steps, each holds `buttons` for `frames` frames.\n"
    "# buttons: any of A, B, Select, Start, Right, Left, Up, Down, R, L\n"
    "# (an empty list is a wait). frames: whole number >= 1.\n"
)


@dataclass
class MacroStep:
    buttons: tuple
    frames: int

    def to_bitfield(self) -> int:
        bitfield = 0
        for button in self.buttons:
            bitfield |= input_map[button]
        return bitfield


@dataclass
class Macro:
    name: str
    steps: list

    @property
    def total_frames(self) -> int:
        return sum(step.frames for step in self.steps)


class MacroError(Exception):
    """Raised with a user-friendly message when a macro file is invalid."""


def macros_dir(profile_path: Path) -> Path:
    return profile_path / "macros"


def _validate_step(entry, index: int, file_name: str) -> MacroStep:
    if not isinstance(entry, dict) or "buttons" not in entry or "frames" not in entry:
        raise MacroError(f"{file_name}: step #{index + 1} must be a mapping with `buttons` and `frames`.")
    buttons = entry["buttons"]
    frames = entry["frames"]
    if buttons is None:
        buttons = []
    if not isinstance(buttons, list) or not all(isinstance(b, str) for b in buttons):
        raise MacroError(f"{file_name}: step #{index + 1} `buttons` must be a list of button names.")
    unknown = [b for b in buttons if b not in input_map]
    if unknown:
        raise MacroError(
            f"{file_name}: step #{index + 1} has unknown button(s) {unknown}. "
            f"Valid: {', '.join(input_map.keys())}."
        )
    if not isinstance(frames, int) or isinstance(frames, bool) or frames < 1:
        raise MacroError(f"{file_name}: step #{index + 1} `frames` must be a whole number >= 1.")
    return MacroStep(buttons=tuple(buttons), frames=frames)


def load_macro(file_path: Path) -> Macro:
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise MacroError(f"{file_path.name} is not valid YAML: {error}")
    except OSError as error:
        raise MacroError(f"Could not read {file_path.name}: {error}")

    if not isinstance(data, dict) or not isinstance(data.get("steps"), list) or len(data["steps"]) == 0:
        raise MacroError(f"{file_path.name}: must contain a non-empty `steps` list.")
    steps = [_validate_step(entry, index, file_path.name) for index, entry in enumerate(data["steps"])]
    name = data.get("name") or file_path.stem
    return Macro(name=str(name), steps=steps)


def save_macro(profile_path: Path, macro: Macro) -> Path:
    directory = macros_dir(profile_path)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in macro.name if c.isalnum() or c in ("-", "_", " ")).strip()
    if not safe_name:
        raise MacroError("Macro name must contain at least one letter or digit.")
    file_path = directory / f"{safe_name}.yml"
    body = {
        "name": safe_name,
        "steps": [{"buttons": list(step.buttons), "frames": step.frames} for step in macro.steps],
    }
    file_path.write_text(_FILE_HEADER + yaml.safe_dump(body, sort_keys=False), encoding="utf-8")
    return file_path


def list_macros(profile_path: Path) -> list:
    """Names of this profile's saved macros (no extension), sorted."""
    directory = macros_dir(profile_path)
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.yml") if not p.name.startswith("_"))


def save_selection(profile_path: Path, macro_name: str, loop: bool) -> None:
    directory = macros_dir(profile_path)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / SELECTION_FILE_NAME).write_text(
        yaml.safe_dump({"macro": macro_name, "loop": bool(loop)}), encoding="utf-8"
    )


def load_selection(profile_path: Path) -> tuple:
    """-> (macro_name | None, loop: bool)"""
    file_path = macros_dir(profile_path) / SELECTION_FILE_NAME
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("macro"), str):
            return data["macro"], bool(data.get("loop", False))
    except (OSError, yaml.YAMLError):
        pass
    return None, False


def encode_input_history(bitfields: list) -> list:
    """Run-length-encode a per-frame list of input bitfields into MacroSteps.
    Leading and trailing idle (no-button) runs are trimmed — recordings
    usually start/end with the player's hands off the controller."""
    steps: list = []
    for bitfield in bitfields:
        buttons = tuple(inputs_to_strings(bitfield))
        if steps and steps[-1].buttons == buttons:
            steps[-1].frames += 1
        else:
            steps.append(MacroStep(buttons=buttons, frames=1))
    while steps and steps[0].buttons == ():
        steps.pop(0)
    while steps and steps[-1].buttons == ():
        steps.pop()
    return steps


class MacroRecorder:
    """Module-level singleton armed/stopped by the GUI; sampled every frame
    by the MacroRecorderListener (all on the main thread)."""

    def __init__(self):
        self.armed: bool = False
        self._history: list = []

    def start(self) -> None:
        self._history = []
        self.armed = True

    def sample(self, bitfield: int) -> None:
        if self.armed:
            self._history.append(bitfield)

    def stop(self) -> Macro | None:
        """-> the recorded Macro (unnamed yet), or None if nothing was pressed."""
        self.armed = False
        steps = encode_input_history(self._history)
        self._history = []
        if not steps:
            return None
        return Macro(name="", steps=steps)


recorder = MacroRecorder()


class MacroRecorderListener:
    """BotListener (duck-typed): feeds the recorder one input sample per frame.
    Recording is only meaningful in Manual mode (human at the controls)."""

    def handle_frame(self, bot_mode, frame) -> None:
        if recorder.armed:
            recorder.sample(context.emulator.get_inputs())
