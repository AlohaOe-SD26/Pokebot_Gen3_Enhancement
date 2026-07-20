"""
Analytics helpers for the dashboard's Stats tab (#11).

Pure, GUI-free functions so they can be unit-tested without Tk or a running
emulator: the luck-meter math, the encounter-rate trend ring buffer, and the
stats-table row assembly / sort / filter from a GlobalStats-like object.

The GUI (modules/gui/dashboard_gui.py) draws these; nothing here touches Tk.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Gen-3 full-odds shiny rate (1 in 8192). This is the documented baseline the
# luck meter compares against; the bot does not manipulate the game's RNG, so
# real hunts are drawn from this rate.
FULL_ODDS_DENOMINATOR = 8192


@dataclass
class LuckResult:
    encounters: int
    shinies: int
    denominator: int
    expected: float
    sigma: float
    z: float              # (actual - expected) / sigma  (0 when undefined)
    verdict: str          # "lucky" | "unlucky" | "on track" | "—"
    summary: str


def luck_meter(encounters: int, shinies: int, denominator: int = FULL_ODDS_DENOMINATOR) -> LuckResult:
    """Compare actual shiny count against the binomial expectation.

    Each encounter is an independent Bernoulli trial with p = 1/denominator.
    Expected shinies = N*p; sigma = sqrt(N*p*(1-p)). The z-score says how many
    standard deviations the real count sits above/below expectation.
    """
    encounters = max(0, int(encounters))
    shinies = max(0, int(shinies))
    denominator = max(1, int(denominator))
    p = 1.0 / denominator
    expected = encounters * p
    sigma = math.sqrt(encounters * p * (1.0 - p)) if encounters > 0 else 0.0

    if encounters == 0:
        return LuckResult(0, 0, denominator, 0.0, 0.0, 0.0, "—", "No encounters yet.")

    z = (shinies - expected) / sigma if sigma > 0 else 0.0
    # Verdict band: within ~0.75 sigma of expectation reads as "on track".
    if abs(z) < 0.75:
        verdict = "on track"
    elif z >= 0.75:
        verdict = "lucky"
    else:
        verdict = "unlucky"

    summary = (
        f"{encounters:,} encounters · {shinies} shiny vs {expected:.1f} expected "
        f"(1/{denominator:,}) · {verdict}"
    )
    return LuckResult(encounters, shinies, denominator, expected, sigma, z, verdict, summary)


@dataclass
class TrendBuffer:
    """A fixed-size ring buffer of recent numeric samples (e.g. enc/hr)."""

    capacity: int = 120
    _values: list = field(default_factory=list)

    def add(self, value: float) -> None:
        try:
            value = float(value)
        except (TypeError, ValueError):
            return
        self._values.append(value)
        if len(self._values) > self.capacity:
            # Drop the oldest to keep a bounded, O(capacity) window.
            del self._values[: len(self._values) - self.capacity]

    def samples(self) -> list:
        return list(self._values)

    def clear(self) -> None:
        self._values.clear()

    def latest(self) -> "float | None":
        return self._values[-1] if self._values else None

    def peak(self) -> float:
        return max(self._values) if self._values else 0.0


# Column keys usable for sorting the stats table.
STATS_COLUMNS = ("species", "total", "shinies", "catches", "best_iv", "best_sv")


def build_stats_rows(global_stats) -> list:
    """Assemble per-species rows from a GlobalStats-like object.

    `global_stats.encounter_summaries` is a dict of {species_id: summary};
    each summary exposes species_name, total_encounters, shiny_encounters,
    catches, total_highest_iv_sum, total_lowest_sv. Returns plain dicts so
    the caller (and tests) never need the real objects.
    """
    rows: list = []
    summaries = getattr(global_stats, "encounter_summaries", None) or {}
    for summary in summaries.values():
        try:
            rows.append(
                {
                    "species": getattr(summary, "species_name", "?"),
                    "total": int(getattr(summary, "total_encounters", 0) or 0),
                    "shinies": int(getattr(summary, "shiny_encounters", 0) or 0),
                    "catches": int(getattr(summary, "catches", 0) or 0),
                    "best_iv": int(getattr(summary, "total_highest_iv_sum", 0) or 0),
                    # Lowest shiny value = "rarest" seen; 0 is best.
                    "best_sv": int(getattr(summary, "total_lowest_sv", 0) or 0),
                }
            )
        except Exception:
            continue
    return rows


def sort_rows(rows: list, key: str = "total", reverse: bool = True) -> list:
    """Sort rows by a column key. Species sorts alphabetically; others numeric.
    Unknown key falls back to 'total'."""
    if key not in STATS_COLUMNS:
        key = "total"
    if key == "species":
        return sorted(rows, key=lambda r: str(r.get("species", "")).lower(), reverse=reverse)
    return sorted(rows, key=lambda r: r.get(key, 0), reverse=reverse)


def filter_rows(rows: list, needle: str) -> list:
    """Case-insensitive substring filter on species name. Empty needle = all."""
    needle = (needle or "").strip().lower()
    if not needle:
        return list(rows)
    return [r for r in rows if needle in str(r.get("species", "")).lower()]
