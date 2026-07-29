"""Acceptance: every DEBUG Story mode configures emulation like an x4 lane (user 2026-07-29).

USER: they cannot run ENDLESS LOOP x4 on their work machine (not enough power for four
emulators), but x4 lanes are configured much better for test runs — and they get there
automatically, while a hand-launched single bot inherits whatever the GUI happened to have:

    modules/endless_x4.py:160      "-s", "0",              # unthrottled
    modules/gui/tile_child.py:84   context.video = True    # REQUIRED

Real evidence of the gap: run `20260729-122709` logged `emulation: speed=1 video=True` —
THROTTLED — so a 2.78M-frame run took hours of wall-clock.

So the debug modes now set unthrottled + video ON themselves.

‼ VIDEO ON IS LOAD-BEARING, not cosmetic: the PokéNav Match-Call tutorial only advances with
the renderer on. That same run played it FAITHFULLY with no state-write fallback, while the
user's earlier video-off runs fell back 8 times out of 9.

‼ AND THIS SUPERSEDES the 2026-07-26 "SPEED ONLY — NEVER TOUCH `context.video`" rule. That
rule existed because the endless loop used to CAPTURE video at batch start and RE-PIN it every
run, so a batch begun with video off stayed off for ever. The harm was pinning to an arbitrary
value — not writing the field. Forcing it ON once is the value the faithful path requires.

No emulator needed.
"""
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

import os  # noqa: E402

from modules.context import context  # noqa: E402
from plugins.custom_modes import story_mode as sm  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


class FakeCtx:
    """Stands in for the bits of `context` the helper touches."""

    def __init__(self, speed=1, video=False):
        self.emulation_speed = speed
        self.video = video


def apply_with(speed, video, env=None):
    saved_env = os.environ.get(sm._TURBO_ENV)
    if env is None:
        os.environ.pop(sm._TURBO_ENV, None)
    else:
        os.environ[sm._TURBO_ENV] = env
    fake = FakeCtx(speed, video)
    real = sm.context
    sm.context = fake
    try:
        sm._apply_debug_emulation_config()
    finally:
        sm.context = real
        if saved_env is None:
            os.environ.pop(sm._TURBO_ENV, None)
        else:
            os.environ[sm._TURBO_ENV] = saved_env
    return fake


print("== the default: unthrottled + video ON, matching an x4 lane ==")
f = apply_with(speed=1, video=False)
check(f.emulation_speed == 0, f"speed forced to 0 = unthrottled (got {f.emulation_speed})")
check(f.video is True, f"video forced ON (got {f.video})")
print("     -> run 20260729-122709 had speed=1: throttled, hours for 2.78M frames.")

print("\n== it is idempotent and does not fight an already-correct config ==")
f = apply_with(speed=0, video=True)
check(f.emulation_speed == 0 and f.video is True, "already-correct settings are left alone")

print("\n== video ON is applied even when speed is already right, and vice versa ==")
f = apply_with(speed=0, video=False)
check(f.video is True, "video-off is corrected independently of speed")
f = apply_with(speed=4, video=True)
check(f.emulation_speed == 0, "a throttled speed is corrected independently of video")

print("\n== ‼ the escape hatch leaves BOTH untouched ==")
for val in ("0", "false", "NO", " off "):
    f = apply_with(speed=3, video=False, env=val)
    check(f.emulation_speed == 3 and f.video is False,
          f"POKEBOT_STORY_DEBUG_TURBO={val!r} -> nothing changed")
f = apply_with(speed=3, video=False, env="1")
check(f.emulation_speed == 0 and f.video is True, "any other value applies the config")

print("\n== it never raises, even if context is hostile ==")
class Hostile:
    @property
    def emulation_speed(self):
        raise RuntimeError("boom")

real = sm.context
sm.context = Hostile()
try:
    sm._apply_debug_emulation_config()
    check(True, "a failing context read is swallowed — a display setting cannot end a run")
except Exception as exc:  # noqa: BLE001
    check(False, f"raised {type(exc).__name__}: {exc}")
finally:
    sm.context = real

print("\n== ALL THREE debug modes call it ==")
src = (SANDBOX / "plugins" / "custom_modes" / "story_mode.py").read_text(encoding="utf-8")
for cls in ("class StoryDebugMode", "class StoryDebugResetMode", "class StoryEndlessResetMode"):
    i = src.index(cls)
    nxt = src.find("\nclass ", i + 10)
    body = src[i:nxt if nxt != -1 else len(src)]
    check("_apply_debug_emulation_config()" in body,
          f"{cls.split()[1]} applies the debug emulation config")

print("\n== ‼ EndlessReset applies it BEFORE capturing batch_speed ==")
# The capture is what each run's speed is RESTORED to after a set_manual_mode() drops it to
# 1x. Applying the config afterwards would pin the batch to the OLD speed and every run after
# the first would crawl — the 2026-07-25 bug, reintroduced from the other direction.
i = src.index("class StoryEndlessResetMode")
body = src[i:]
i_apply = body.index("_apply_debug_emulation_config()")
i_capture = body.index("batch_speed = context.emulation_speed")
check(i_apply < i_capture,
      "the config is applied before the batch_speed capture, so restores keep it unthrottled")

print("\n== plain 'Story' (the non-debug mode) is NOT forced ==")
# ‼ End the slice at the module-level HELPER, not at StoryDebugMode: the helper's own
# definition sits between the two classes, so a naive slice contains its name and the test
# passes/fails for the wrong reason. (Third instance of this anchoring mistake — see
# 08-MISTAKES 2026-07-29.)
i = src.index("class StoryMode(BotMode)")
i_end = src.index("_TURBO_ENV = ")
body = src[i:i_end]
check("_apply_debug_emulation_config()" not in body,
      "StoryMode itself does not force turbo — a human watching a normal run keeps control")
check(i_end > i, "and the slice really covers StoryMode's body")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f_ in failures:
        print("  " + f_)
    sys.exit(1)
print("PASS")
