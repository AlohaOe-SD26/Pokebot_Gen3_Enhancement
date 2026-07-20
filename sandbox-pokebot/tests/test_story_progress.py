"""Unit battery for the story-mode progress detector (modules/story).

Uses synthetic in-memory readers (no emulator) so the badge-anchored placement
logic is exercised deterministically. A minimal ROM load (no emulator boot) is
done once so event-flag/var/item names resolve exactly as in production; if no
Emerald ROM is present the whole module is skipped.

Run standalone:  py -3.12 tests/test_story_progress.py
Or under pytest: py -3.12 -m pytest tests/test_story_progress.py
"""

from pathlib import Path

try:
    import pytest
except ImportError:  # standalone run without pytest installed
    pytest = None

from modules import game
from modules.roms import list_available_roms, load_rom_data


def _load_emerald_rom():
    for rom in list_available_roms():
        if rom.game_code == "BPE":
            return rom
    # fall back to the conventional path
    candidate = Path("roms/Pokemon - Emerald Version (USA, Europe).gba")
    if candidate.is_file():
        rom = load_rom_data(candidate)
        if rom.game_code == "BPE":
            return rom
    return None


_ROM = _load_emerald_rom()
if _ROM is None:
    if pytest is not None:
        pytest.skip("No Emerald (BPE) ROM available", allow_module_level=True)
    else:
        raise SystemExit("SKIP: No Emerald (BPE) ROM available")
game.set_rom(_ROM)


from modules.story.chapters import (  # noqa: E402  (import after set_rom)
    BADGES_BEFORE,
    CHAPTERS,
    BADGE_FLAG_NAMES,
    badge_level,
    chapters_in_bracket,
    current_chapter,
    validate_registry,
)
from modules.story.progress import detect_progress  # noqa: E402


class _FakeBag:
    def __init__(self, item_names: set[str]):
        self._names = item_names

    def quantity_of(self, item) -> int:
        return 1 if getattr(item, "name", None) in self._names else 0


class FakeReader:
    """A synthetic save: whatever flags/vars/items you declare are 'set'."""

    def __init__(self, flags=(), vars=None, items=()):
        self.flags = set(flags)
        self.vars = dict(vars or {})
        self.items = set(items)

    def get_event_flag(self, name: str) -> bool:
        return name in self.flags

    def get_event_var(self, name: str) -> int:
        return int(self.vars.get(name, 0))

    def get_item_bag(self):
        return _FakeBag(self.items)


def _badges(n: int) -> list[str]:
    """The first n badge flags."""
    return BADGE_FLAG_NAMES[:n]


# --------------------------------------------------------------------------
# Registry integrity
# --------------------------------------------------------------------------
def test_registry_validates_clean():
    assert validate_registry() == []


def test_badges_before_is_monotonic_and_spans_0_to_8():
    values = [BADGES_BEFORE[c.key] for c in CHAPTERS]
    assert values == sorted(values), "badges_before must be non-decreasing in order"
    # Gym 8 (ch22) earns the 8th badge, so ch23/24 are played holding all 8.
    assert min(values) == 0 and max(values) == 8
    assert BADGES_BEFORE["23"] == 8 and BADGES_BEFORE["24"] == 8
    assert BADGES_BEFORE["4"] == 0 and BADGES_BEFORE["5"] == 1  # Gym 1 boundary


def test_every_badge_level_has_a_nonempty_bracket():
    for level in range(0, 9):
        assert chapters_in_bracket(level), f"badge level {level} has no chapters"


# --------------------------------------------------------------------------
# Placement: fresh save
# --------------------------------------------------------------------------
def test_fresh_save_is_chapter_0():
    r = FakeReader()  # nothing set
    assert badge_level(r) == 0
    assert current_chapter(r).key == "0"
    p = detect_progress(r)
    assert p.chapter_key == "0"
    assert p.badges == [] and p.hms == []
    assert p.anomalies == []


def test_after_pokedex_but_no_badge_advances_within_bracket_0():
    r = FakeReader(flags=["ADVENTURE_STARTED", "RECEIVED_POKEDEX_FROM_BIRCH"])
    # bracket 0 = ch0..ch4; first unmet after these two is ch2
    assert current_chapter(r).key == "2"


# --------------------------------------------------------------------------
# Placement: legit progression stays within the badge bracket
# --------------------------------------------------------------------------
def test_one_badge_places_in_bracket_1():
    r = FakeReader(flags=_badges(1))  # Stone only, no fine flags
    assert badge_level(r) == 1
    c = current_chapter(r)
    assert BADGES_BEFORE[c.key] == 1
    assert c.key == "5"  # first chapter after Gym 1


def test_one_badge_with_early_bracket1_flags_advances():
    r = FakeReader(flags=_badges(1) + ["RECEIVED_POKENAV", "MR_BRINEY_SAILING_INTRO"])
    # ch5 + ch5b done -> current should be ch6
    assert current_chapter(r).key == "6"


def test_five_badges_places_in_bracket_5():
    r = FakeReader(flags=_badges(5))
    assert badge_level(r) == 5
    c = current_chapter(r)
    assert BADGES_BEFORE[c.key] == 5
    assert c.key == "14"  # first chapter after Gym 5


def test_current_chapter_never_leaves_its_badge_bracket():
    # For every badge level, with no fine flags, placement stays in that bracket.
    for level in range(0, 9):
        r = FakeReader(flags=_badges(level))
        c = current_chapter(r)
        if not r.get_event_flag("SYS_GAME_CLEAR"):
            assert BADGES_BEFORE[c.key] == level, f"level {level} escaped its bracket"


# --------------------------------------------------------------------------
# Placement: hacked/test save (the real 'Nick - Emerald' shape)
# --------------------------------------------------------------------------
def test_hacked_save_stone_plus_stray_magma_emblem():
    # 1 badge but a stray Magma Emblem key item (ch16b's milestone) — must NOT
    # jump to the endgame; badge spine holds it at ch5 and flags the anomaly.
    r = FakeReader(flags=_badges(1), items={"Magma Emblem"})
    c = current_chapter(r)
    assert c.key == "5", "stray key item must not move placement outside bracket 1"
    p = detect_progress(r)
    assert "16b" in p.anomalies
    assert p.badge_level == 1


def test_non_contiguous_badge_uses_highest():
    # Only BADGE05 set (hacked) -> highest set badge wins the spine.
    r = FakeReader(flags=["BADGE05_GET"])
    assert badge_level(r) == 5
    assert BADGES_BEFORE[current_chapter(r).key] == 5


# --------------------------------------------------------------------------
# Placement: game cleared
# --------------------------------------------------------------------------
def test_game_cleared():
    r = FakeReader(flags=_badges(8) + ["SYS_GAME_CLEAR"])
    p = detect_progress(r)
    assert p.cleared is True
    assert p.is_game_cleared
    assert "COMPLETE" in p.summary()


if __name__ == "__main__":
    import sys

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
