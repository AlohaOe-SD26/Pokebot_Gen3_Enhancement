"""Milestone save states — the story checkpoint library, surfaced for fast testing.

USER DIRECTIVE (2026-07-23): the repo's committed harness checkpoints
(`tools/story-dev/saves/*.ss1`) double as SHARED test entry points — instead of
relying solely on multi-hour fresh runs, the user can load a milestone in the GUI
("Load Milestone State") and test the frontier directly. The library lives in the
repo, so a `git pull` always yields checkpoints that match the code under test.

Two important properties, reflected in the GUI copy:
- These states are a DIFFERENT PLAYTHROUGH (the harness trainer, "NICK"). Loading
  one replaces the running game session; the profile's own save file on disk is
  untouched unless the game later saves in-game. Use a test profile.
- Milestones pair with the resume-anywhere Story modes ("Story", "Story (DEBUG)").
  "Story (DEBUG - RESET)" would discard the loaded state (it forces a NEW GAME).
"""

from dataclasses import dataclass
from pathlib import Path

# Curated, story-ordered registry: filename -> (title, where/what).  Files found on
# disk that aren't listed here still show up (generically labeled) so a freshly
# committed checkpoint is usable before anyone remembers to update this table.
_KNOWN: dict[str, tuple[str, str]] = {
    "oldale.ss1": ("Ch1 — Oldale Town", "Early game, pre-rival"),
    "route103.ss1": ("Ch1 — Route 103", "Before the first rival battle (pre-Pokédex)"),
    "pokedex_done.ss1": ("Ch1 ✓ — Pokédex received", "After Birch's lab, ready to travel"),
    "wally_done.ss1": ("Ch2 ✓ — Petalburg / Wally done", "Catch tutorial finished"),
    "woods_entered.ss1": ("Ch3 — Petalburg Woods", "Inside the Woods at (17,38)"),
    "route104_north.ss1": ("Ch3 — Route 104 north", "Woods crossed, Rustboro ahead"),
    "rustboro.ss1": ("Ch4 — Rustboro City", "Before Gym 1 (Roxanne)"),
    "route116team.ss1": ("Ch4 — Route 116", "Pre-gym team on the training route"),
    "gym1_done.ss1": ("Ch4 ✓ — STONE BADGE", "Roxanne beaten"),
    "post_theft.ss1": ("Ch5 — Devon goods stolen", "Chase toward Rusturf Tunnel"),
    "goods_recovered.ss1": ("Ch5 — Goods recovered", "Rusturf grunt beaten, Peeko freed"),
    "devon_done.ss1": ("Ch5 — Devon errand", "Goods returned to Devon Corp"),
    "pokenav_got.ss1": ("Ch5 ✓ — PokéNav received", "Devon Corp 3F done"),
    "fresh_rivalprep.ss1": ("Ch5 — Rival prep", "Team leveled, before the Rustboro rival"),
    "post_rival.ss1": ("Ch5 ✓ — Rustboro rival beaten", "Rustboro (16,53), ready to sail"),
    "dewford.ss1": ("Ch6 ✓ — Dewford Town", "First Briney sail done"),
    "brawly_done.ss1": ("Ch7 ✓ — KNUCKLE BADGE", "Brawly beaten, Letter delivered"),
    "slateport.ss1": ("Ch8a ✓ — Slateport City", "At the PC, healed"),
    "stern_done.ss1": ("Ch8b ✓ — Devon Goods delivered", "Museum done, Aqua cleared"),
    "wattson_done.ss1": ("Ch9 ✓ — DYNAMO BADGE", "Wattson beaten"),
    "rocksmash_got.ss1": ("Ch10a ✓ — HM06 in the bag", "Mauville, before the teach"),
    "rocksmash_taught.ss1": ("Ch10b ✓ — Rock Smash taught", "Ready to head north"),
    "fallarbor.ss1": ("Ch10c ✓ — Fallarbor Town", "Northern arc opened, healed"),
    "meteorfalls_done.ss1": ("Ch11a ✓ — Meteor Falls scene", "Team Magma encountered"),
    "lavaridge.ss1": ("Ch11c ✓ — Lavaridge Town", "Jagged Pass descended, healed"),
    "flannery_done.ss1": ("Ch11d ✓ — HEAT BADGE", "Flannery beaten (current frontier)"),
    "mauville_wedge.ss1": ("repro — Mauville gym mid-maze", "Debug state (KI class)"),
    "evostall.ss1": ("repro — evolve-mid-training", "Debug state (#24-evo-trainstall)"),
}
# Scratch states that must never be offered as milestones.
_EXCLUDE = {"midstuck.ss1", "current_state.ss1"}


@dataclass
class Milestone:
    path: Path
    title: str
    detail: str
    known: bool


def milestone_directory() -> Path | None:
    """The repo's checkpoint library, resolved robustly relative to this build
    (works for sandbox-pokebot AND a promoted custom-pokebot, both of which sit
    one level below the repo root). None if this checkout doesn't carry it."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "tools" / "story-dev" / "saves"
        if candidate.is_dir():
            return candidate
    return None


def get_milestones() -> list[Milestone]:
    """All milestone states, story-ordered (curated entries first, in registry
    order; any uncurated .ss1 files afterwards, alphabetically, generically
    labeled). Empty list when the library isn't present."""
    directory = milestone_directory()
    if directory is None:
        return []
    on_disk = {f.name: f for f in directory.glob("*.ss1") if f.name not in _EXCLUDE}
    result: list[Milestone] = []
    for name, (title, detail) in _KNOWN.items():
        if name in on_disk:
            result.append(Milestone(on_disk.pop(name), title, detail, known=True))
    for name in sorted(on_disk):
        result.append(
            Milestone(on_disk[name], name.removesuffix(".ss1"), "(uncatalogued checkpoint)", known=False)
        )
    return result
