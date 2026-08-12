"""KI-56, question 1: if the bot used an Escape Rope inside the Magma Hideout, WHERE would it
land — and does it own one?

‼ WHY THIS EXISTS. KI-56 leaves the bot permanently stranded four floors inside the Magma
Hideout, and the leading fix (`04-HANDOFF` next-action #1) is Escape Rope support. But the
handoff also records the reason that fix was NOT simply started: **the hideout's four map scripts
contain no `setescapewarp`** (decomp-checked), so "an Escape Rope takes you to the entrance" was
an ASSUMPTION about a game the bot cannot ask. Building a rope-buying, rope-using item path on an
assumption about where it lands is exactly the shape of the 2026-08-10 mistake (*name the thing
that gates the content and assert it on the anchor BEFORE building anything*). This probe reads
the answer out of memory instead.

WHAT THE DECOMP SAYS (read 2026-08-11, `pret/pokeemerald`):
  * `MagmaHideout_1F/map.json` -> `"allow_escaping": true`, so `CanUseDigOrEscapeRopeOnCurMap()`
    (`src/item_use.c:911`) returns TRUE and the item is legal here.
  * The destination is `gSaveBlock1Ptr->escapeWarp` (`SetWarpDestinationToEscapeWarp`,
    `src/overworld.c:690`).
  * That field does NOT need a `setescapewarp`. `UpdateEscapeWarp` (`src/overworld.c:677`) is
    called from `src/field_control_avatar.c:826` on EVERY warp step, and writes the player's
    current tile whenever the map being LEFT is outdoors and the map being ENTERED is not.
  * So walking Jagged Pass -> Magma Hideout 1F should have stamped JAGGED_PASS into `escapeWarp`
    all by itself.
This probe tests that last sentence against the actual stranded save. The decomp says what the
code does; only memory says what THIS run's save block holds.

WHAT IT READS, per save, straight out of SaveBlock1 (offsets from `include/global.h`):
  * `+0x04 location`   — struct WarpData, 8 bytes: s8 mapGroup, s8 mapNum, s8 warpId, pad, s16 x, s16 y
  * `+0x24 escapeWarp` — same layout; "used by Dig and Escape Rope" per the decomp comment
  * the item bag's Escape Rope count

‼ CONTROLS, because a struct read at a guessed offset produces confident nonsense, and a plausible
map name is indistinguishable from a correct one:
  * DECODER CONTROL — `+0x04 location` must decode to the SAME map the live avatar reports on
    every single save. `location` is the one WarpData whose correct value is independently known,
    so it proves the offset, the field order and the padding all at once. If any row disagrees,
    the decoder is wrong, `escapeWarp` eight bytes later is noise, and the probe REFUSES to answer
    rather than printing a confident wrong warp.
  * CONTRAST CONTROL — `escapeWarp` must not read the same on every save. A reader that returns a
    constant looks exactly like a correct reader on a single row; the pre-hideout save must
    disagree with the in-hideout saves or the "it was stamped on entry" claim is unsupported.
  * DESTINATION CONTROL — the landing tile is looked up on its own map and its collision printed.
    A warp into a wall would still read as a lovely map name here.

THE NEGATIVE ARM is `magma_door.ss1`: standing on Jagged Pass, hideout NOT yet entered. Its
`escapeWarp` must be some EARLIER cave, not the hideout door — that is what makes the in-hideout
value evidence of the entry stamp rather than a coincidence.

‼ WHAT THIS PROBE DOES NOT PROVE. It does not prove an Escape Rope can be OBTAINED, and it does
not prove the warp executes — only where the game says it points. Driving it is the real proof.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_escape_warp.py
Exit: 0 = controls held and the answer is reported; 1 = a control failed, answer withheld.
"""

import pathlib
import struct
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

from modules.items import get_item_bag, get_item_by_name
from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.memory import get_save_block
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"
STRANDED = REPO / "sandbox-pokebot" / "profiles" / "ch16a" / "current_state.ss1"

# include/global.h struct SaveBlock1
OFF_LOCATION = 0x04
OFF_ESCAPE_WARP = 0x24
WARP_DATA_SIZE = 8

# The saves to read. (label, path, note)
TARGETS = [
    ("STRANDED (KI-56)", STRANDED, "the actual failure state — 1F (25,34), no reachable exit"),
    ("post_maxie.ss1", SAVES / "post_maxie.ss1", "the §Ch16 build anchor, 4F"),
    ("magma_door.ss1", SAVES / "magma_door.ss1", "NEGATIVE ARM: on Jagged Pass, hideout not entered"),
    ("post_mtpyre.ss1", SAVES / "post_mtpyre.ss1", "an unrelated late save, for spread"),
]


def read_warp(offset: int) -> dict:
    """Decode one `struct WarpData` out of SaveBlock1 at `offset`."""
    raw = get_save_block(1, offset=offset, size=WARP_DATA_SIZE)
    map_group, map_num, warp_id, x, y = struct.unpack("<bbbxhh", raw)
    try:
        name = MapRSE((map_group, map_num)).name
    except ValueError:
        name = f"UNKNOWN({map_group},{map_num})"
    return {
        "group": map_group,
        "num": map_num,
        "warp_id": warp_id,
        "x": x,
        "y": y,
        "name": name,
        "raw": raw.hex(),
    }


def read_save(label: str, path: pathlib.Path) -> dict:
    row: dict = {"label": label, "path": path}
    if not path.is_file():
        row["error"] = "missing"
        return row

    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    # ‼ the ENUM, never `map_name` — that is a display label (standing project rule).
    try:
        avatar = get_player_avatar()
        row["live_map"] = MapRSE(tuple(avatar.map_group_and_number)).name
        row["live_group_num"] = tuple(avatar.map_group_and_number)
        row["live_tile"] = tuple(avatar.local_coordinates)
    except Exception as error:  # noqa: BLE001 — a probe reports, it does not crash
        row["live_map"] = f"?({type(error).__name__})"
        row["live_group_num"] = None
        row["live_tile"] = None

    row["location"] = read_warp(OFF_LOCATION)
    row["escape"] = read_warp(OFF_ESCAPE_WARP)

    try:
        rope = get_item_by_name("Escape Rope")
        row["ropes"] = get_item_bag().quantity_of(rope)
    except Exception as error:  # noqa: BLE001
        row["ropes"] = f"?({type(error).__name__})"

    return row


def describe_destination(warp: dict) -> str:
    """DESTINATION CONTROL — is the landing tile a real, walkable tile on that map?"""
    try:
        tile = get_map_data((warp["group"], warp["num"]), (warp["x"], warp["y"]))
    except Exception as error:  # noqa: BLE001
        return f"could not read tile ({type(error).__name__})"
    return (
        f"collision={tile.collision} elevation={tile.elevation} "
        f"behaviour={tile.tile_type} encounters={tile.has_encounters}"
    )


def main() -> int:
    rows = [read_save(label, path) for label, path, _ in TARGETS]
    notes = {label: note for label, _, note in TARGETS}

    print("=" * 100)
    print("KI-56 / probe_escape_warp — where does an Escape Rope point, and do we own one?")
    print("=" * 100)

    print("\nRAW READ (SaveBlock1 +0x04 location, +0x24 escapeWarp)")
    print("-" * 100)
    for row in rows:
        print(f"\n  {row['label']}  — {notes[row['label']]}")
        if row.get("error"):
            print(f"      !! {row['error']}: {row['path']}")
            continue
        print(f"      live avatar   : {row['live_map']} {row['live_tile']}")
        loc, esc = row["location"], row["escape"]
        print(f"      +0x04 location: {loc['name']} ({loc['x']},{loc['y']}) warp_id={loc['warp_id']}  raw={loc['raw']}")
        print(f"      +0x24 escape  : {esc['name']} ({esc['x']},{esc['y']}) warp_id={esc['warp_id']}  raw={esc['raw']}")
        print(f"      Escape Ropes  : {row['ropes']}")

    present = [r for r in rows if not r.get("error")]
    if not present:
        print("\nNO SAVES READ — nothing to say.")
        return 1

    # ---------------------------------------------------------------- CONTROLS
    print("\n" + "=" * 100)
    print("CONTROLS")
    print("=" * 100)

    ok = True

    # DECODER CONTROL — `location` must match the live avatar's map on every save.
    print("\n  [1] DECODER CONTROL — +0x04 `location` must equal the live avatar's map")
    for row in present:
        loc = row["location"]
        want = row["live_group_num"]
        got = (loc["group"], loc["num"])
        agree = want is not None and tuple(want) == got
        print(f"      {'OK  ' if agree else 'FAIL'}  {row['label']:<20} live={row['live_map']:<28} +0x04={loc['name']}")
        if not agree:
            ok = False
    if not ok:
        print("      => the WarpData decoder is WRONG. Everything read at +0x24 is noise.")

    # CONTRAST CONTROL — escapeWarp must not be constant across saves.
    print("\n  [2] CONTRAST CONTROL — `escapeWarp` must differ across saves (not a constant)")
    distinct = {(r["escape"]["group"], r["escape"]["num"], r["escape"]["x"], r["escape"]["y"]) for r in present}
    print(f"      {len(distinct)} distinct escapeWarp value(s) across {len(present)} save(s)")
    for value in sorted(distinct):
        print(f"        {value}")
    if len(distinct) < 2:
        print("      FAIL — a reader that returns a constant is indistinguishable from a broken one.")
        ok = False
    else:
        print("      OK — the field tracks something.")

    # NEGATIVE ARM — the pre-entry save must not already point at the hideout entrance.
    stranded = next((r for r in present if r["label"].startswith("STRANDED")), None)
    door = next((r for r in present if r["label"] == "magma_door.ss1"), None)
    print("\n  [3] NEGATIVE ARM — `magma_door.ss1` (hideout NOT yet entered) vs the stranded save")
    if stranded and door:
        s, d = stranded["escape"], door["escape"]
        same = (s["group"], s["num"], s["x"], s["y"]) == (d["group"], d["num"], d["x"], d["y"])
        print(f"      stranded escapeWarp   : {s['name']} ({s['x']},{s['y']})")
        print(f"      pre-entry escapeWarp  : {d['name']} ({d['x']},{d['y']})")
        if same:
            print("      !! IDENTICAL — the value was NOT stamped by entering the hideout. Claim unsupported.")
            ok = False
        else:
            print("      OK — they differ, consistent with the stamp happening on the entry warp.")
    else:
        print("      SKIPPED — one arm missing.")

    if not ok:
        print("\n" + "=" * 100)
        print("A CONTROL FAILED — ANSWER WITHHELD. Do not build on the numbers above.")
        print("=" * 100)
        return 1

    # ---------------------------------------------------------------- ANSWER
    print("\n" + "=" * 100)
    print("ANSWER")
    print("=" * 100)
    if stranded:
        esc = stranded["escape"]
        print(f"\n  From the STRANDED state, an Escape Rope warps to:")
        print(f"      {esc['name']}  local tile ({esc['x']},{esc['y']})")
        print(f"      destination tile: {describe_destination(esc)}")
        print(f"\n  Escape Ropes currently in the bag: {stranded['ropes']}")
        if isinstance(stranded["ropes"], int) and stranded["ropes"] == 0:
            print("      => the ESCAPE is available but the ITEM is not. Acquisition is the open half.")
    print("\n" + "=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
