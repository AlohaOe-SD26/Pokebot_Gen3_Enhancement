"""KI-69 Phase A — the four cheap unknowns the Regi arc rests on, answered from OUR save.

‼ WHY THIS RUNS BEFORE ANY REGI CODE. The research (KI-69) established the whole chain, but four of
its gates could not be checked without a save, and every one of them is capable of stopping the arc
dead after a long trek:
  * **Super Rod** — Wailmer is ROD-ONLY (39 Super Rod + 27 Good Rod encounters, zero surf/grass).
    No rod, no Wailmer, no Wailord, no tomb.
  * **TM28 Dig** — the Sealed Chamber's inner room is opened by standing on (9/10/11, 3) and using
    DIG. It is a TM, not an HM, and has **no badge gate** — but it must be OWNED and TAUGHT.
  * **Go-Goggles** — Route 111's desert physically pushes the player back out without them
    (`Route111/scripts.inc:190`), so Regirock is unreachable.
  * **Flash / Rock Smash knowers** — Registeel needs FLASH on (8,25); Regirock needs ROCK SMASH on
    (5/6/7, 23). `use_field_move` selects `first_pokemon_with_move(...)`, so the move must be KNOWN
    by a party member, not merely learnable.

‼ It also re-checks the two things that gate everything upstream — Surf (to reach any of it) and a
DIVE knower (Relicanth is a dive-only encounter, and the Sealed Chamber is underwater).

‼ CHEAPNESS IS THE POINT. Every one of these is a flag read or a party scan. Discovering a missing
Go-Goggles after driving to the desert is the expensive version of the same question.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_regi_capabilities.py
      PYTHONUTF8=1 py -3.12 probe_regi_capabilities.py --anchor post_dive.ss1
"""

import argparse
import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)  # ‼ is_test_run: without it the
    # emulator registers an atexit that OVERWRITES shared `profiles/<name>/current_state.ss1`
    # and writes a states/ snapshot. Pass 2 fixed this for the two KI-76 probes; PASS 4
    # (2026-08-22) found SEVEN MORE still writing — `profiles/repro-ml/states/` had reached
    # 2,820 files / 160 MB. A probe that mutates shared state is not observe-only.
context.audio = False
context.video = False

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_dive.ss1")
args = parser.parse_args()

context.emulator.load_save_state(
    (REPO / "tools" / "story-dev" / "saves" / args.anchor).read_bytes()
)
for _ in range(4):
    context.emulator.run_single_frame()

from modules.items import get_item_bag, get_item_by_name
from modules.map_data import MapRSE
from modules.memory import get_event_flag
from modules.player import get_player_avatar
from modules.pokemon_party import get_party

BAR = "=" * 100
rows = []


def record(label, ok, detail=""):
    rows.append((label, ok, detail))
    mark = "HAVE" if ok else "‼ MISSING"
    print(f"  {mark:<10} {label:<44} {detail}")


avatar = get_player_avatar()
print(f"anchor: {args.anchor}")
print(f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)")

party = get_party()
known_moves = {}
for index, mon in enumerate(party):
    if mon is None:
        continue
    for learned in mon.moves:
        if learned is not None:
            known_moves.setdefault(learned.move.name, []).append(
                f"{mon.species.name}(slot {index})"
            )

print(f"\nparty ({len([m for m in party if m is not None])}/6): "
      + ", ".join(f"{m.species.name} L{m.level}" for m in party if m is not None))

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n1 — KEY ITEMS AND FLAGS (a flag read each; the cheap half)\n{BAR}\n")

record("Super Rod (flag RECEIVED_SUPER_ROD)", get_event_flag("RECEIVED_SUPER_ROD"),
       "Wailmer is ROD-ONLY — no rod, no Wailord, no tomb")
record("Good Rod (fallback)", get_event_flag("RECEIVED_GOOD_ROD"),
       "27 Wailmer encounters, lower rate/levels than Super")
record("TM28 Dig received (flag)", get_event_flag("RECEIVED_TM_DIG"),
       "opens the Sealed Chamber inner room; a TM, NO badge gate")


def in_bag(name):
    try:
        return get_item_bag().quantity_of(get_item_by_name(name)) > 0
    except Exception:  # noqa: BLE001 - an unreadable bag is reported, never assumed stocked
        return False


record("Go-Goggles in bag", in_bag("Go-Goggles"),
       "‼ Route 111 desert EJECTS the player without them -> Regirock unreachable")
record("TM28 in bag", in_bag("TM28"), "owning the flag is not owning the TM")
record("HM08 in bag", in_bag("HM08"), "the Dive HM itself")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n2 — MOVES A PARTY MEMBER MUST *KNOW* (use_field_move picks the first knower)\n{BAR}\n")

for move, why in (
    ("Surf", "reach Routes 105/120/124/126/134 at all"),
    ("Dive", "‼ the Sealed Chamber AND Relicanth's only habitat"),
    ("Dig", "‼ opens the Sealed Chamber inner room"),
    ("Flash", "Registeel — stand on (8,25) and use it"),
    ("Rock Smash", "Regirock — stand on (5/6/7,23) and use it"),
    ("Strength", "not needed by the Regi arc (Emerald swapped it for Rock Smash)"),
):
    holders = known_moves.get(move, [])
    record(f"a party member KNOWS {move}", bool(holders), f"{holders or '-'}  ({why})")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n3 — THE TWO KEY SPECIES (are they already aboard?)\n{BAR}\n")

species_present = {m.species.name for m in party if m is not None}
record("WAILORD in the party", "Wailord" in species_present, "‼ must end up in slot 0 (Emerald order)")
record("RELICANTH in the party", "Relicanth" in species_present, "‼ must end up in the LAST slot")
record("WAILMER in the party (evolves at L40)", "Wailmer" in species_present,
       "‼ evolution fires on GAINING a level — catch at <=39 and level once")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\n4 — ARC PROGRESS FLAGS (all should be unset before the arc)\n{BAR}\n")

for flag, meaning in (
    ("SYS_BRAILLE_DIG", "the Sealed Chamber inner room is open"),
    ("REGI_DOORS_OPENED", "‼ the one-time Wailord/Relicanth check has passed"),
    ("SYS_REGIROCK_PUZZLE_COMPLETED", "Regirock's tomb is open"),
    ("SYS_BRAILLE_REGICE_COMPLETED", "Regice's tomb is open (note: BRAILLE, not PUZZLE)"),
    ("SYS_REGISTEEL_PUZZLE_COMPLETED", "Registeel's tomb is open"),
    ("DEFEATED_REGIROCK", "‼ set by a WIN **or a LOSS** — the encounter is GONE"),
    ("DEFEATED_REGICE", "‼ same"),
    ("DEFEATED_REGISTEEL", "‼ same"),
):
    value = get_event_flag(flag)
    print(f"  {'SET ':<10} {flag:<44} {meaning}" if value
          else f"  {'unset':<10} {flag:<44} {meaning}")

# ---------------------------------------------------------------------------------------------
print(f"\n{BAR}\nVERDICT — what must be acquired before the Regi arc can start\n{BAR}\n")

missing = [(label, detail) for label, ok, detail in rows if not ok]
have = [label for label, ok, _ in rows if ok]
print(f"  HAVE ({len(have)}): {', '.join(have) or '-'}\n")
if missing:
    print(f"  ‼ MISSING ({len(missing)}) — each one stops the arc:")
    for label, detail in missing:
        print(f"      {label:<44} {detail}")
else:
    print("  Nothing missing — every capability gate is satisfied.")

print("\n‼ THIS PROBE ANSWERS 'DO WE HAVE IT', NOT 'CAN WE GET THERE'. Reachability of Route 105,")
print("  the desert, the tomb islands and the underwater routes is a separate, DRIVEN question —")
print("  a static path is not a route, and this project demotes claims derived that way.")
