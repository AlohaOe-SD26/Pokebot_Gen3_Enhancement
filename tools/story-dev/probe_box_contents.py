"""RAW, LIVE dump of PC box contents (and party) for a given save. Read-only.

‼ WHY THIS EXISTS. A test design decision (whether Stage 2's `sole` control can assert
`occupants == [pid]` against a real box) needs FACTS about what is actually sitting in a
captured `.ss1`, not inference from a save's name or from `story_harness.py` driver code.
This probe boots the emulator exactly like `probe_anchor_inventory.py` (same profile, same
`LibmgbaEmulator`, same `load_save_state` + frame-advance idiom), then reads
`get_pokemon_storage()` (see `story_harness.py`'s `BoxCounterMode` / `PartyPidsMode` for the
same idiom) and the party, and prints every occupied slot with species, level, PID, types,
and full move list — plus, per mon, whether it matches a NEEDED type set either by species
type or by a known move's type.

⛔ READ-ONLY. No writes to the save, no edits to `modules/`, no edits to `story_harness.py`.
It only loads a `.ss1`, reads memory, and prints.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_box_contents.py [save_name.ss1]
      (defaults to ch13_fortree_door.ss1)
"""
import pathlib
import sys

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

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

from modules.pokemon import Pokemon
from modules.pokemon_party import get_party
from modules.pokemon_storage import get_pokemon_storage

SAVES = REPO / "tools" / "story-dev" / "saves"

NEEDED = {"Rock", "Ice", "Dragon", "Electric"}


def dump_mon(label: str, mon: Pokemon) -> None:
    types = [t.name for t in mon.species.types]
    type_match = bool(set(types) & NEEDED)
    print(f"  {label:<24} {mon.species.name:<12} L{mon.level:<3} pid={mon.personality_value:08X} "
          f"types={types} egg={mon.is_egg}")
    print(f"    type_match={type_match}  (species types {types} vs NEEDED {sorted(NEEDED)})")

    move_hits = []
    for i in range(4):
        lm = mon.move(i)
        if lm is None:
            print(f"    move[{i}] = None")
            continue
        mv = lm.move
        in_needed = mv.type.name in NEEDED
        print(f"    move[{i}] = {mv.name:<16} type={mv.type.name:<10} in_NEEDED={in_needed}  "
              f"knows_move('{mv.name}')={mon.knows_move(mv.name)}")
        if in_needed:
            move_hits.append((mv.name, mv.type.name))

    move_match = bool(move_hits)
    print(f"    move_match={move_match}  hits={move_hits}")


def dump_save(save_path: pathlib.Path) -> int:
    print("=" * 100)
    print(f"SAVE: {save_path}")
    print("=" * 100)
    if not save_path.is_file():
        print(f"  ‼ FILE NOT FOUND: {save_path}")
        return 2

    try:
        context.emulator.load_save_state(save_path.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
    except Exception as error:
        print(f"  ‼ COULD NOT LOAD SAVE: {type(error).__name__}: {error}")
        return 2

    # ---- PARTY ----
    print("-" * 100)
    print("PARTY")
    print("-" * 100)
    try:
        party = [mon for mon in get_party() if mon is not None]
    except Exception as error:
        print(f"  ‼ COULD NOT READ PARTY: {type(error).__name__}: {error}")
        return 2

    print(f"  party size = {len(party)} (full party is 6)")
    party_pids: dict[int, list[str]] = {}
    for idx, mon in enumerate(party):
        label = f"party[{idx}]"
        dump_mon(label, mon)
        party_pids.setdefault(mon.personality_value, []).append(f"{mon.species.name}({label})")

    # ---- BOXES ----
    print("-" * 100)
    print("PC BOXES")
    print("-" * 100)
    try:
        storage = get_pokemon_storage()
    except Exception as error:
        print(f"  ‼ COULD NOT READ PC STORAGE: {type(error).__name__}: {error}")
        return 2

    box_pids: dict[int, list[str]] = {}
    n_boxed = 0
    for box in storage.boxes:
        occupied = box.slots
        if not occupied:
            continue
        print(f"  BOX {box.number} ({box.name!r}), {len(occupied)} occupied slot(s):")
        for slot in occupied:
            mon = slot.pokemon
            n_boxed += 1
            label = f"box{box.number}.slot{slot.slot_index}"
            dump_mon(label, mon)
            box_pids.setdefault(mon.personality_value, []).append(f"{mon.species.name}({label})")

    if n_boxed == 0:
        print("  (no occupied slots in any box — all 14 boxes empty)")

    # ---- SUMMARY ----
    print("-" * 100)
    print("SUMMARY")
    print("-" * 100)
    print(f"  party_size={len(party)}  boxed_count={n_boxed}  pokemon_count(reported)={storage.pokemon_count}")

    all_pids: dict[int, list[str]] = {}
    for pid, who in party_pids.items():
        all_pids.setdefault(pid, []).extend(who)
    for pid, who in box_pids.items():
        all_pids.setdefault(pid, []).extend(who)
    collisions = {pid: who for pid, who in all_pids.items() if len(who) > 1}
    for pid, who in collisions.items():
        print(f"  ‼‼ PID COLLISION {pid:08X} shared by {who}")
    if not collisions:
        print("  no PID collisions found across party+box")

    # explicit check for the reported Shedinja/Ninjask pid=42207D6F
    target_pid = 0x42207D6F
    if target_pid in all_pids:
        print(f"  pid=42207D6F present: {all_pids[target_pid]}")
    else:
        print(f"  pid=42207D6F NOT present in this save's party+box")

    return 0


def main() -> int:
    argv = sys.argv[1:]
    save_name = argv[0] if argv else "ch13_fortree_door.ss1"
    save_path = SAVES / save_name
    rc = dump_save(save_path)
    print()
    print(f"EXIT CODE: {rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
