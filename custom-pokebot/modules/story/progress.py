"""Read-only story-progress detector (chunk 1 of #24).

Reads a save's event flags/vars and reports which ordered story Chapter it is
at, which badges/HMs it holds, and the current objective. It writes nothing to
the game and is safe to run against a real save.

Two entry points:
  * ``detect_live()`` — reads the live emulator memory (use inside a running
    bot / plugin).
  * ``detect_from_save_data()`` — reads the last-saved data (``SaveData``).

Both funnel through ``detect_progress(reader)``, where ``reader`` is anything
with ``get_event_flag(name)`` and ``get_event_var(name)`` (see
``chapters.FlagVarReader``)."""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.story.chapters import (
    CHAPTERS,
    Chapter,
    FlagVarReader,
    badge_level,
    completed_chapters,
    current_chapter,
    is_game_cleared,
    milestone_anomalies,
)

# HM "received" flags → the field move they grant, in field-move order.
HM_FLAGS: list[tuple[str, str]] = [
    ("RECEIVED_HM_CUT", "Cut"),
    ("RECEIVED_HM_FLASH", "Flash"),
    ("RECEIVED_HM_ROCK_SMASH", "Rock Smash"),
    ("RECEIVED_HM_STRENGTH", "Strength"),
    ("RECEIVED_HM_SURF", "Surf"),
    ("RECEIVED_HM_FLY", "Fly"),
    ("RECEIVED_HM_DIVE", "Dive"),
    ("RECEIVED_HM_WATERFALL", "Waterfall"),
]

# Badge flags → badge name, in gym order.
BADGE_FLAGS: list[tuple[str, str]] = [
    ("BADGE01_GET", "Stone"),
    ("BADGE02_GET", "Knuckle"),
    ("BADGE03_GET", "Dynamo"),
    ("BADGE04_GET", "Heat"),
    ("BADGE05_GET", "Balance"),
    ("BADGE06_GET", "Feather"),
    ("BADGE07_GET", "Mind"),
    ("BADGE08_GET", "Rain"),
]


@dataclass
class StoryProgress:
    chapter_key: str          # e.g. "16b"
    chapter_order: int        # global order of the CURRENT chapter
    chapter_name: str
    area: str
    objective: str            # what to do to finish the CURRENT chapter
    milestones_met: int       # how many chapter milestones are proven met
    badge_level: int          # highest badge number set (0-8) — the spine anchor
    total_chapters: int
    cleared: bool = False      # SYS_GAME_CLEAR is set
    badges: list[str] = field(default_factory=list)   # names earned
    hms: list[str] = field(default_factory=list)       # field moves owned
    anomalies: list[str] = field(default_factory=list)  # chapter keys met ahead of badge level
    verify_live: bool = False  # current chapter's milestone is a live-verify proxy

    @property
    def is_game_cleared(self) -> bool:
        return self.cleared

    def summary(self) -> str:
        lines = []
        if self.cleared:
            lines.append("Story: COMPLETE (Champion)!")
        else:
            lines.append(
                f"Story chapter {self.chapter_key} — {self.chapter_name}  "
                f"(chapter {self.chapter_order + 1} of {self.total_chapters})"
            )
            lines.append(f"  Area: {self.area}")
            lines.append(f"  Next objective: {self.objective}")
            if self.verify_live:
                lines.append("  (note: this chapter's completion check is a "
                             "verify-live proxy — see design doc §1.5)")
        lines.append(f"  Badges ({len(self.badges)}/8): "
                     + (", ".join(self.badges) if self.badges else "none"))
        lines.append(f"  HMs ({len(self.hms)}/8): "
                     + (", ".join(self.hms) if self.hms else "none"))
        if self.anomalies:
            lines.append(f"  [!] {len(self.anomalies)} milestone(s) met AHEAD of "
                         f"the badge count ({', '.join(self.anomalies)}) — likely a "
                         f"hand-edited/test save. Position is anchored on badges, "
                         f"so these are ignored for placement.")
        return "\n".join(lines)


def detect_progress(reader: FlagVarReader) -> StoryProgress:
    met = completed_chapters(reader)
    current = current_chapter(reader)
    cleared = is_game_cleared(reader)
    anomalies = milestone_anomalies(reader)

    badges = [name for flag_name, name in BADGE_FLAGS if _safe_flag(reader, flag_name)]
    hms = [name for flag_name, name in HM_FLAGS if _safe_flag(reader, flag_name)]

    return StoryProgress(
        chapter_key=current.key,
        chapter_order=current.order,
        chapter_name=current.name,
        area=current.area,
        objective=current.objective,
        milestones_met=len(met),
        badge_level=badge_level(reader),
        total_chapters=len(CHAPTERS),
        cleared=cleared,
        badges=badges,
        hms=hms,
        anomalies=[c.key for c in anomalies],
        verify_live=(not cleared) and current.complete.verify_live,
    )


def _safe_flag(reader: FlagVarReader, name: str) -> bool:
    try:
        return bool(reader.get_event_flag(name))
    except Exception:
        return False


class _LiveMemoryReader:
    """Adapts the module-level live-memory functions to the reader interface."""

    def get_event_flag(self, flag_name: str) -> bool:
        from modules.memory import get_event_flag

        return get_event_flag(flag_name)

    def get_event_var(self, var_name: str) -> int:
        from modules.memory import get_event_var

        return get_event_var(var_name)

    def get_item_bag(self):
        from modules.items import get_item_bag

        return get_item_bag()


def detect_live() -> StoryProgress:
    """Detect from the live emulator memory (current in-RAM game state)."""
    return detect_progress(_LiveMemoryReader())


def detect_from_save_data() -> StoryProgress | None:
    """Detect from the last-saved data. Returns None if the game has never
    been saved (no valid save block)."""
    from modules.save_data import get_save_data

    save_data = get_save_data()
    if save_data is None:
        return None
    return detect_progress(save_data)
