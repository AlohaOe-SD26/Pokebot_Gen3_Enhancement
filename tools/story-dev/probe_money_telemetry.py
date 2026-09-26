r"""PROBE — `#26-ch23money` F0: does the wallet reach the debug log, and is the logged value the REAL one?

WHY (2026-09-26): the first three organic League arrivals were all refused at §Ch23 leg 11 on money, and their
wallets had to be RECONSTRUCTED from prize texts because money was never logged. F0 adds `money=` to every
heartbeat (gated by `repro_heartbeat_emits.py`) and a `[MONEY]` line after every battle
(`StoryMode.on_battle_ended`). This probe drives the REAL hook against a real save's memory:

  M1  the `[MONEY]` line appears, and its ₽ equals `get_player().money` read independently (a line that printed a
      constant or a stale value would fail);
  M2  CONTROL: the same call with the debug logger DISABLED writes nothing and raises nothing (the hook must be a
      no-op when telemetry is off — production runs without it).
Two fixtures with different wallets (`post_league_shop` ₽1,741; `post_ever_grande` ₽38,893) so a hardcoded
value cannot pass both.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_money_telemetry.py
"""
import pathlib
import re
import sys
import tempfile
import types

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "probe-money"
if not profile_directory_exists(PROFILE):
    create_profile(PROFILE, list_available_roms()[0])
profile = load_profile_by_name(PROFILE)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0   # ⛔ UNTHROTTLED — a registered gate must be (`probe_gate_unthrottled.py`)
context.bot_mode = "Story"

SAVES = REPO / "tools" / "story-dev" / "saves"


def main() -> int:
    from modules import debug_logger
    from modules.battle_state import BattleOutcome
    from modules.player import get_player
    from plugins.custom_modes.story_mode import StoryMode

    fails = []
    stub = types.SimpleNamespace(_location_key=lambda: (0, 8), _defeat_counts={}, _loss_seq=0,
                                 _loss_ko_history={}, _last_defeat_key=None)
    seen = set()
    for name in ("post_league_shop.ss1", "post_ever_grande.ss1"):
        context.emulator.load_save_state((SAVES / name).read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
        real = get_player().money
        tmp = pathlib.Path(tempfile.mkdtemp()) / "money.log"
        debug_logger.enable(profile, name_prefix="MONEYPROBE")
        log_file = pathlib.Path(debug_logger.log_path())
        StoryMode.on_battle_ended(stub, BattleOutcome.Won)
        debug_logger.disable()
        text = log_file.read_text(encoding="utf-8", errors="replace")
        m = re.findall(r"\[MONEY\] after Won at map \(0, 8\): money=₽([\d,]+)", text)
        logged = int(m[-1].replace(",", "")) if m else None
        ok = logged == real
        seen.add(logged)
        print(f"  {'ok  ' if ok else 'FAIL'} M1 {name}: logged ₽{logged} vs memory ₽{real:,}")
        if not ok:
            fails.append(name)
        # M2 — disabled logger: nothing written, nothing raised
        before = log_file.read_text(encoding="utf-8", errors="replace")
        try:
            StoryMode.on_battle_ended(stub, BattleOutcome.Won)
            raised = None
        except Exception as error:  # noqa: BLE001 - the probe REPORTS a raise; it must not hide it
            raised = error
        after = log_file.read_text(encoding="utf-8", errors="replace")
        ok2 = raised is None and before == after
        print(f"  {'ok  ' if ok2 else 'FAIL'} M2 {name}: logger disabled ⇒ no write, no raise ({raised!r})")
        if not ok2:
            fails.append(name + " (M2)")
    if len(seen) < 2:
        fails.append("the two fixtures logged the SAME wallet — the probe cannot tell a constant from a reading")
        print("  FAIL two different wallets must log two different values")
    print("PASS" if not fails else f"FAIL {fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
