r"""GATE — KI-107 F3 + F4: the whiteout recovery's waits are BOUNDED, and the evidence the idle hid is now logged (2026-09-27).

WHY (`ai-research-notes/2026-09-27-ki107-RECON.md`, a NOTE, adversarially checked): batch `#27-batch0927` run P1r2 idled
6,265,575 frames. A stale whiteout flag sent a battle fault into the whiteout recovery while a faint-chooser menu was up,
and the recovery then waited with the UNBOUNDED `wait_for_player_avatar_to_be_controllable()`. The KI-47 park that
started it left no log line, and every dump stopped at the `_run_with_frame_budget` wrapper, whose generator is named
`inner`.
⚠ This does NOT fix why the flag was stale (F1 in the note); it bounds the damage and makes the next one visible.

  K1  `early_game.wait_controllable_bounded`: returns as soon as the player is controllable; raises a NAMED
      `BotModeError` after `timeout_frames` when it never is; `POKEBOT_KI107_FAULT_UNBOUNDED=1` restores the
      unbounded wait (no raise).
  K2  WIRING: the whiteout-recovery block in `StoryMode.run` has NO unbounded wait and uses the bounded one twice.
  K3  `debug_logger`'s dump walker follows a driven generator named `inner`.
  K4  `battle_handler` logs a `KI-47 PARK` line when it parks a recoverable fault.
FAULT ARMS (built in; each must FAIL): the UNBOUNDED arm (K1); the unbounded wait restored in the recovery (K2);
`inner` removed from the walker (K3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ki107_bounded.py
"""
from __future__ import annotations

import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

import modules.story.early_game as EG  # noqa: E402
from modules.modes import BotModeError  # noqa: E402

SM_SRC = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
DL_SRC = ROOT / "sandbox-pokebot" / "modules" / "debug_logger.py"
BH_SRC = ROOT / "sandbox-pokebot" / "modules" / "battle_handler.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_KI107_FAULT_UNBOUNDED"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def k1(sink=None):
    import modules.modes.util.walking as W

    saved = (EG.player_avatar_is_controllable, W.wait_for_player_avatar_to_be_controllable)
    st = {"frame": 0, "ready_at": None}

    def ctl():
        return st["ready_at"] is not None and st["frame"] >= st["ready_at"]

    def unbounded():
        for _ in range(500):   # the stub "unbounded" wait gives up by itself after 500, so the arm cannot hang the gate
            if ctl():
                return
            yield

    def drive(timeout, ready_at):
        st.update(frame=0, ready_at=ready_at)
        err = None
        try:
            for _ in EG.wait_controllable_bounded(timeout, "probe"):
                st["frame"] += 1
        except BotModeError as error:
            err = str(error)
        return st["frame"], err

    EG.player_avatar_is_controllable, W.wait_for_player_avatar_to_be_controllable = ctl, unbounded
    try:
        n, err = drive(50, 10)
        check(err is None and n == 10, f"K1 controllable at frame 10 ⇒ returns after 10 frames ({n}, {err})", sink)
        n, err = drive(50, None)
        check(err is not None and "KI-107" in err and n == 50,
              f"K1 never controllable ⇒ a NAMED raise after the 50-frame bound ({n}, {err!r:.60})", sink)
    finally:
        EG.player_avatar_is_controllable, W.wait_for_player_avatar_to_be_controllable = saved


def recovery_block(sm: str) -> str:
    i = sm.index("recovered from the whiteout — re-orienting")
    j = sm.index("# loop → re-run the segmented resume from the respawn point", i)
    return sm[i:j]


def k2(sm: str, sink=None):
    blk = recovery_block(sm)
    check("wait_for_player_avatar_to_be_controllable()" not in blk and blk.count("wait_controllable_bounded(") == 2,
          "K2 the whiteout recovery has no unbounded wait and uses the bounded one twice", sink)


def k3(dl: str, sink=None):
    check('("_play_gen", "gen", "generator", "inner")' in dl, "K3 the dump walker follows a generator named `inner`", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — KI-107 F3 + F4: bounded whiteout-recovery waits; the park and the parked generator are visible")
    print("=" * 92)
    os.environ.pop(ARM, None)
    sm, dl, bh = (p.read_text(encoding="utf-8") for p in (SM_SRC, DL_SRC, BH_SRC))
    print("\n== K1 the bounded wait ==")
    k1()
    print("\n== K2 wiring ==")
    k2(sm)
    print("\n== K3 the dump walker ==")
    k3(dl)
    print("\n== K4 the park is logged ==")
    check('_dl_park.event(f"KI-47 PARK:' in bh, "K4 battle_handler logs a KI-47 PARK line")
    check(f'environ.get("{ARM}") == "1"' in EG_SRC_TEXT() and f"`{ARM}`" in REGISTRY.read_text(encoding="utf-8"),
          f"{ARM} is read in production and registered in 29")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    os.environ[ARM] = "1"
    try:
        k1(sink)
    finally:
        os.environ.pop(ARM, None)
    check(bool(sink), f"FAULT {ARM} FAILS K1 ({len(sink)} caught)")
    old = 'yield from wait_controllable_bounded(KI107_RECOVERY_WAIT_FRAMES, "Story: whiteout recovery")'
    check(sm.count(old) == 1, "(fault-arm mutation applied exactly once: the unbounded wait restored)")
    sink = []
    k2(sm.replace(old, "yield from wait_for_player_avatar_to_be_controllable()", 1), sink)
    check(bool(sink), f"FAULT the unbounded recovery wait FAILS K2 ({len(sink)} caught)")
    sink = []
    k3(re.sub(r', "inner"\)', ")", dl, count=1), sink)
    check(bool(sink), f"FAULT `inner` removed from the walker FAILS K3 ({len(sink)} caught)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


def EG_SRC_TEXT() -> str:  # noqa: N802 - a tiny reader kept beside its one use
    return (ROOT / "sandbox-pokebot" / "modules" / "story" / "early_game.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
