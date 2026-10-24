"""TEST SIDE (build step 5.3, stage A2): THE MEASUREMENT of a development sweep, before any B1-debt row is decided.

    py -3.12 ai_player/gates/measure_step5.py <sweep root or run folders ...> [--json out.json]
        (the sweep: `rate_step5.py --purpose development --keep-runs ...`; its root is on its `RUN FOLDERS:` line)

WHAT IT IS FOR (`PROJECT KNOWLEDGE/ai-research-notes/2026-10-22-BUILD-SPEC-step5.3-B1-N8.md`, stage A2): 39 GRADED checks of
the step-5 graders still read an AI input (`gates/b1_debt.json`). Stage A2 gives the harness game reads (party HP at each
battle's start, one start per battle, and at its end, the tile under the player at every move, a press log with the game's facing, the frame equality,
who ended the run: `play_harness.py`), and this module MEASURES what those reads, and the reads the harness already made,
say about each plan, so the coordinator can decide each debt row from numbers: re-source it to the game where a control
SEPARATES, keep it HONESTY, or make it DIAGNOSTIC. WHY measure first: the spec's critic MEASURED on ledger #34 that a
curiosity yield over game windows is likely VACUOUS (GREEDY 85.9 % productive against the real code's 90.2 %; a beeline
has no curiosity to be unproductive) and that wild battles won do not tell NOTRAIN from training (13 of 18 seeds), so no
bound is set before the controls are seen.

WHAT IT IS NOT: it grades nothing, registers nothing, writes no bound, and no grader imports it. It prints, and with
`--json` writes the same numbers. It imports nothing from the AI's code (`ai_player.brain`, `personality`, `mode`,
`hands`): the G-3 rule of `check_grader_imports.py` holds for it too (`test_measure_step5.ImportRuleTests`).

THE INPUTS, per kept run folder: `run.json` (the run's whole PLAY record and its plan and seed, written by
`rate_step5.run_one`), `game_reads.json` (the five A2 reads), `places.json` (the places recorder). Every quantity is read
from the GAME by the harness (memory, the emulator, the framework's map and player objects), with exactly two exceptions,
each said on its own line below: the AI's curiosity SPANS (from `actions.jsonl`, used as DATA to split the game's slices
into inside and outside them, because "the real code's base rate outside its curiosity spans" is defined against the AI's
own spans), and the AI's REPORTED losses (the AI half of an HONESTY quantity, L5.OWN_LOSSES).

THE QUANTITIES (the spec's A2 list), per run and per plan:
  windows    the NON-BATTLE frames of every inter-mark window: the run cut at every confirmed mark change of the story
             recorder (`story.changes`), less the frames the places recorder saw a battle (`places.battles`)
  slices     the run cut into fixed slices of `SLICE` frames of the recorder's clock ([k*SLICE, (k+1)*SLICE), the last one
             partial); a slice is productive BY CRITERION: tiles (at least `SLICE_TILES` tiles the screen showed for the
             first time, or a map first stood on), page (a text began in it that showed a page never shown before in the
             run), battle (a battle overlapped it), capture (the game's capture counter rose in it), item (an item-ball
             flag rose in it). `yield` = the slices with no battle that are productive by tiles, page, capture or item,
             over the slices with no battle (a battle slice is neither: the critic's point that loafing in grass meets
             battles); `loaf` = the slices with no battle productive by none of the four
  base rate  `yield` over the slices OUTSIDE the AI's curiosity spans (a slice is inside when at least half of it lies in
             one), and inside them beside it
  grass      the steps onto tall grass (the tile recorder, read ii) between the starter's mark (VAR_BIRCH_LAB_STATE 2) and
             the rival's flag (DEFEATED_RIVAL_ROUTE103); None when the rival's flag never went up
  below      the battles STARTED with the party's HP (sum over the party, read i) under each of `HP_FRACTIONS`, wild battles
             only (a start is paired with the next battle end, which says whether a trainer fought); and under the run's
             own personality's heal_below (the grader-owned `rate_step5.ERRANDS`). Only when the run's starts and ends
             ALTERNATE (`alternate`: start, end, ..., at most one final open start); otherwise "NO NUMBER: starts and ends
             do not alternate (n starts, m ends)", never a count (the A2 verifier MEASURED a start recorded again after
             each in-battle menu, so one end was paired with several starts)
  spins      the game's spins (a facing change with no position change between two overworld presses, read iii,
             `play_harness.spins_of`) and moves, recomputed from the press log beside the harness's own count
  gap        real minus control, per paired seed and pooled (each plan's mean), for every pair the decision table uses
THE DECISION TABLE: one row per `b1_debt.json` entry (all of them; a debt id with no rule here RAISES), with the quantity
its plan names, the real plan's values, the named control's values, and whether that control SEPARATES by the plan's own
rule (`ROW_RULES`), else "NO NUMBER: <why>", or "RULING" where the plan is a coordinator's ruling. Counts at its end.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.rate_step5 import (BOUNDS, CURIOSITY_KINDS, ERRANDS, REAL_PLANS, RUN_FILE, SMALL_PATIENCE,  # noqa: E402
                                        STOP_WITHIN, YIELD_TILES, goal_spans)

GATES = Path(__file__).resolve().parent
DEBT = GATES / "b1_debt.json"
#: the slice length, frames of the recorder's clock: the grader's own yield rate is per 1,000 frames (`YIELD_TILE_RATE`)
SLICE = 1000
#: the new tiles that make a slice productive by its tiles: the grader's own `YIELD_TILES`
SLICE_TILES = YIELD_TILES
#: the party-HP fractions a battle's start is counted under: the three personalities' heal_below (the Trainer's 0.45, the
#: Catcher's 0.5, the Story's 0.6: `rate_step5.ERRANDS`) and a quarter, where a person surely rests
HP_FRACTIONS = (0.25, 0.45, 0.5, 0.6)
#: the files of a run folder besides `RUN_FILE` (the harness's names: `play_harness.READS_FILE`, `PLACES_FILE`)
READS_FILE, PLACES_FILE, ACTIONS_FILE = "game_reads.json", "places.json", "actions.jsonl"
TALL_GRASS = "Tall Grass"
RIVAL, STARTER, DEX, WALLY = (("DEFEATED_RIVAL_ROUTE103", 1), ("VAR_BIRCH_LAB_STATE", 2),
                              ("RECEIVED_POKEDEX_FROM_BIRCH", 1), ("VAR_PETALBURG_GYM_STATE", 2))


# ------------------------------------------------------------------------------------------------------------- loading
def _json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_run(folder: Path) -> dict | None:
    """One kept run folder, or None when it holds no `RUN_FILE` (a folder from before stage A2, or a run that printed no
    PLAY line). The reads come from their own files, the PLAY record's copies only when a file is missing."""
    folder = Path(folder)
    record = _json(folder / RUN_FILE)
    if not isinstance(record, dict) or "play" not in record:
        return None
    play = record["play"] or {}
    actions = []
    path = folder / ACTIONS_FILE
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                actions.append(json.loads(raw))
            except ValueError:
                pass
    return {"folder": str(folder), "plan": record["plan"], "seed": record["seed"], "base": record.get("base"),
            "personality": record.get("personality") or play.get("personality"), "play": play,
            "reads": _json(folder / READS_FILE) or play.get("game_reads") or {},
            "places": _json(folder / PLACES_FILE) or play.get("places") or {}, "actions": actions}


def load_sweep(paths: list[Path]) -> tuple[list[dict], list[str]]:
    """Every run under `paths` (a run folder itself, or a sweep root whose sub-folders are runs), and the folders skipped
    (no `RUN_FILE`), so a sweep that left nothing to measure says so instead of measuring nothing."""
    runs, skipped = [], []
    for path in paths:
        path = Path(path)
        folders = [path] if (path / RUN_FILE).is_file() else sorted(p for p in path.iterdir() if p.is_dir()) \
            if path.is_dir() else []
        for folder in folders:
            run = load_run(folder)
            if run is None:
                skipped.append(str(folder))
            else:
                runs.append(run)
    return runs, skipped


# ------------------------------------------------------------------------------------------------------------ the clock
def change_frame(story: dict, mark: tuple[str, int]) -> int | None:
    """The recorder frame of a mark's first confirmed change to at least its value (`StoryRecorder.changes`)."""
    name, value = mark
    return next((c["f"] for c in story.get("changes") or [] if c.get("mark") == name and (c.get("to") or 0) >= value), None)


def end_frame(run: dict) -> int:
    play = run["play"]
    return int((play.get("story") or {}).get("frames") or play.get("frames") or 0)


def battle_spans(places: dict) -> list[tuple[int, int]]:
    """The places recorder's battle stretches as [first, last + its period) on the recorder's clock."""
    every = int(places.get("every") or 10)
    return [(a, b + every) for a, b in places.get("battles") or ()]


def overlap(spans: list[tuple[int, int]], start: int, end: int) -> int:
    return sum(max(0, min(end, b) - max(start, a)) for a, b in spans)


def rose(timeline: list | None, start: int, end: int) -> bool:
    """A [frame, value] timeline (changes only) ROSE inside [start, end): a sample in it holds more than the value before
    it (the first sample is the baseline, not a rise)."""
    before = None
    for frame, value in timeline or ():
        if frame >= end:
            break
        if frame >= start and before is not None and value > before:
            return True
        before = value
    return False


# -------------------------------------------------------------------------------------------------------- quantities
def mark_windows(run: dict) -> list[dict]:
    """The NON-BATTLE frames of every inter-mark window: the run cut at each confirmed mark change (any mark; changes at
    one frame make one cut), the battle frames taken out."""
    story, end = run["play"].get("story") or {}, end_frame(run)
    battles = battle_spans(run["places"])
    cuts = sorted({c["f"] for c in story.get("changes") or [] if 0 < c["f"] < end})
    bounds = [0] + cuts + [end]
    marks = {}
    for c in story.get("changes") or []:
        marks.setdefault(c["f"], c["mark"])
    return [{"from": a, "to": b, "mark": marks.get(b), "frames": b - a, "non_battle": b - a - overlap(battles, a, b)}
            for a, b in zip(bounds, bounds[1:]) if b > a]


def slices(run: dict, size: int = SLICE) -> list[dict]:
    """Every slice of the run and the criteria it is productive by (module docstring, `slices`)."""
    places, story, end = run["places"], run["play"].get("story") or {}, end_frame(run)
    battles = battle_spans(places)
    stays = places.get("stays") or []
    first: dict[str, int] = {}
    for frame, stay in stays:
        if stay != stays[0][1]:  # the run's first map is where it began (and a return to it): no map first stood on
            first.setdefault(stay, frame)
    out = []
    for k in range(math.ceil(end / size) if end > 0 else 0):
        a, b = k * size, min(end, (k + 1) * size)
        tiles = sum(n for frame, n in places.get("new_tiles") or () if a <= frame < b)
        row = {"from": a, "to": b,
               "tiles": tiles >= SLICE_TILES or any(a <= frame < b for frame in first.values()),
               "page": any(a <= t[0] < b and len(t) > 2 and bool(t[2]) for t in places.get("texts") or ()),
               "battle": overlap(battles, a, b) > 0,
               "capture": rose(story.get("captures"), a, b),
               "item": rose(story.get("item_flags"), a, b)}
        row["game"] = row["tiles"] or row["page"] or row["capture"] or row["item"]
        out.append(row)
    return out


def slice_counts(rows: list[dict]) -> dict:
    """The slices by criterion, the non-battle ones, the productive and the loafing among them, and the yield."""
    calm = [r for r in rows if not r["battle"]]
    made = sum(1 for r in calm if r["game"])
    return {"n": len(rows), **{key: sum(1 for r in rows if r[key]) for key in ("tiles", "page", "battle", "capture", "item")},
            "any": sum(1 for r in rows if r["game"] or r["battle"]), "calm": len(calm), "productive": made,
            "loaf": len(calm) - made, "yield": round(made / len(calm), 4) if calm else None}


def curiosity_windows(run: dict) -> list[tuple[int, int]]:
    """(AI DATA, used only to split the game's slices: the base rate is defined against the AI's own spans) the AI's
    curiosity goals the story did not need (`rate_step5.goal_spans`), moved onto the recorder's clock by the harness's
    `frame0` (read iv: the emulator's counter before the loop; the AI stamps its records with that counter), or by the
    first record's frame for a run without it."""
    actions = run["actions"]
    frame0 = (run["reads"].get("frames") or {}).get("frame0")
    if frame0 is None:
        frame0 = (actions[0].get("frame") or 0) if actions else 0
    return [(s["frame"] - frame0, s["frame"] + s["frames"] - frame0) for s in goal_spans(actions)
            if s["kind"] in CURIOSITY_KINDS and not s["story_moved"]]


def inside_outside(rows: list[dict], windows: list[tuple[int, int]]) -> dict:
    """The slice counts INSIDE the curiosity windows (at least half the slice in one) and OUTSIDE them: the base rate."""
    inside = [r for r in rows if 2 * overlap(windows, r["from"], r["to"]) >= r["to"] - r["from"]]
    outside = [r for r in rows if r not in inside]
    return {"inside": slice_counts(inside), "outside": slice_counts(outside)}


def grass_before_rival(run: dict) -> int | None:
    """The steps onto tall grass between the starter's mark and the rival's flag (read ii); None: no rival's flag."""
    story = run["play"].get("story") or {}
    rival = change_frame(story, RIVAL)
    if rival is None:
        return None
    since = change_frame(story, STARTER) or 0
    return sum(1 for step in (run["reads"].get("tiles") or {}).get("steps") or ()
               if step[4] == TALL_GRASS and since < step[0] <= rival)


def grass_stint(run: dict) -> int | None:
    """The training STINT by the game: frames from the first to the last tall-grass step before the rival's flag (the
    run's end without one). None: no grass step there."""
    story = run["play"].get("story") or {}
    until = change_frame(story, RIVAL) or end_frame(run)
    since = change_frame(story, STARTER) or 0
    frames = [s[0] for s in (run["reads"].get("tiles") or {}).get("steps") or () if s[4] == TALL_GRASS
              and since < s[0] <= until]
    return frames[-1] - frames[0] if frames else None


def party_fraction(party: list | None) -> float | None:
    if not party:
        return None
    total = sum(m[3] for m in party)
    return sum(m[2] for m in party) / total if total else None


def alternate(starts: list, ends: list) -> bool:
    """(The A2 fix round) Do a run's battle starts and ends ALTERNATE: start, end, start, end, ..., with at most one final
    start left open (a run that ended inside a battle)? In frame order; a start and an end read at the same sample put the
    start first (the recorder appends a battle's start before its end). WHY: pairing each start with the next end is only
    one start to one battle when they alternate. The A2 verifier MEASURED the opposite on the smoke: the harness recorded a
    start again after each in-battle BAG or PARTY menu (fixed in `play_harness.StoryRecorder`), and 4 CH2/CH2_OFF runs
    held 18 starts more than ends, each paired with the SAME end, which inflated "battles started below each fraction". A
    run recorded that way, or by any other fault, is no number, never a count."""
    events = sorted([(s[0], 0) for s in starts] + [(e[0], 1) for e in ends])
    kinds = [kind for _, kind in events]
    return all(kind == index % 2 for index, kind in enumerate(kinds))


def battles_below(run: dict) -> dict:
    """The battles STARTED under each HP fraction (read i), wild only: a start is paired with the first battle end at or
    after it (its `trainer` field); a start whose party could not be read is counted apart (`unread`). A run whose starts
    and ends do not `alternate` gives NO NUMBER (`no_number` says why; `wild`, `unread`, `below` and `below_own` are None,
    never 0): its pairing would count one battle more than once."""
    hp = run["reads"].get("battle_hp") or {}
    ends = sorted(hp.get("ends") or [], key=lambda e: e[0])
    heal = ERRANDS.get(run.get("personality") or "Story", ERRANDS["Story"]).heal_below
    starts = hp.get("starts") or []
    if not alternate(starts, ends):
        return {"starts": len(starts), "ends": len(ends), "unread": None, "wild": None, "below": None, "below_own": None,
                "heal_below": heal, "no_number": f"NO NUMBER: starts and ends do not alternate ({len(starts)} starts, "
                                                f"{len(ends)} ends)"}
    out = {"starts": 0, "ends": len(ends), "unread": 0, "wild": 0, "below": {str(f): 0 for f in HP_FRACTIONS},
           "below_own": 0, "heal_below": heal, "no_number": None}
    for frame, party in starts:
        out["starts"] += 1
        end = next((e for e in ends if e[0] >= frame), None)
        if end is not None and end[2]:
            continue  # a trainer's battle: not a roam's
        out["wild"] += 1
        share = party_fraction(party)
        if share is None:
            out["unread"] += 1
            continue
        for f in HP_FRACTIONS:
            if share < f:
                out["below"][str(f)] += 1
        if share < heal:
            out["below_own"] += 1
    return out


def game_spins(run: dict) -> dict:
    """The game's spins and moves recomputed from the press log (`play_harness.spins_of`), beside the harness's count."""
    from ai_player.gates.play_harness import spins_of

    presses = run["reads"].get("presses") or {}
    again = spins_of(presses.get("log") or [])
    return {**again, "stored": presses.get("spins"), "agree": presses.get("spins") == again["spins"],
            "ratio": round(again["spins"] / again["moves"], 4) if again["moves"] else None}


def stood(run: dict) -> set[tuple]:
    """Every tile the game had the player stand on: the places recorder's moves and the tile recorder's steps."""
    tiles = {(m[1], m[2], m[3]) for m in run["places"].get("moves") or ()}
    reads = run["reads"].get("tiles") or {}
    tiles |= {(s[1], s[2], s[3]) for s in reads.get("steps") or ()}
    if reads.get("start"):
        tiles.add(tuple(reads["start"][1:4]))
    return tiles


def map_order(run: dict) -> list[str]:
    """The maps entered, in order (the places recorder's stays): the goal sequence's nearest game analog."""
    return [stay for _, stay in run["places"].get("stays") or ()]


def to_mark(run: dict, mark: tuple[str, int]) -> dict | None:
    """Frames to a mark's change by the game, and the same less the battle frames before it. None: never reached.
    MEASURED on the smoke (CH2 seed 1303): a run the AI ends AT its target can end before the recorder's second sample
    confirms the target's change (VAR_PETALBURG_GYM_STATE 1 -> 2 in the last 30 frames), so no change is recorded though
    the game's end marks (`story_truth`) hold it. Then the run's END is the frame (`at_end` True; one sample late at most),
    but only when the run's start marks (`start_story`, a chapter-2 run's) did not already hold it."""
    play = run["play"]
    frame, at_end = change_frame(play.get("story") or {}, mark), False
    if frame is None:
        name, wanted = mark
        ended = ((play.get("story_truth") or {}).get("marks") or {}).get(name) or 0
        began = ((play.get("start_story") or {}).get("marks") or {}).get(name) or 0
        if ended >= wanted > began:
            frame, at_end = end_frame(run), True
    if frame is None:
        return None
    return {"frame": frame, "no_battle": frame - overlap(battle_spans(run["places"]), 0, frame), "at_end": at_end}


def losses(run: dict) -> dict:
    """The game's battles LOST (gBattleOutcome 2), the harness's MAX_LOSSES for the run, the frames from the game's
    MAX_LOSSES-th loss to the run's end (None: never reached), and (AI DATA, the AI half of an HONESTY quantity) its
    report's losses."""
    play = run["play"]
    lost = [b["f"] for b in (play.get("story") or {}).get("battles") or [] if b.get("outcome") == 2]
    cap = play.get("max_losses")
    after = (end_frame(run) - lost[cap - 1]) if isinstance(cap, int) and 0 < cap <= len(lost) else None
    return {"game": len(lost), "max_losses": cap, "after_cap": after, "ai": (play.get("report") or {}).get("losses")}


def measure_run(run: dict) -> dict:
    """Every quantity of one run."""
    rows = slices(run)
    windows = mark_windows(run)
    places, play = run["places"], run["play"]
    reads = run["reads"]
    return {"plan": run["plan"], "seed": run["seed"], "base": run.get("base"), "personality": run.get("personality"),
            "frames": end_frame(run), "windows": [w["non_battle"] for w in windows], "slices": slice_counts(rows),
            "split": inside_outside(rows, curiosity_windows(run)), "grass_before_rival": grass_before_rival(run),
            "grass_steps": (reads.get("tiles") or {}).get("grass_steps"), "stint": grass_stint(run),
            "below": battles_below(run), "spins": game_spins(run),
            "await_game": ((play.get("waits_game") or {}).get("longest") or [0, 0, 0])[2],
            "push_game": ((places.get("push") or {}).get("longest") or [0, 0, 0])[2],
            "dex": to_mark(run, DEX), "wally": to_mark(run, WALLY), "losses": losses(run),
            "stop_by": (reads.get("stop") or {}).get("by"), "frames_equal": (reads.get("frames") or {}).get("equal"),
            "_stood": stood(run), "_maps": map_order(run)}


# ---------------------------------------------------------------------------------------------------------- the gaps
def by_plan(measured: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for m in measured:
        out.setdefault(m["plan"], []).append(m)
    return {plan: sorted(rows, key=lambda m: (m["seed"], str(m.get("base")))) for plan, rows in out.items()}


def value(m: dict, key: str):
    """A measured quantity by its path, e.g. "slices.yield", "below.below_own", "dex.no_battle"."""
    for part in key.split("."):
        if not isinstance(m, dict):
            return None
        m = m.get(part)
    return m


def gap(plans: dict, real: str, control: str, key: str) -> dict:
    """Real minus control: per paired seed (both measured) and pooled (each plan's mean over its runs with a value)."""
    a = {m["seed"]: value(m, key) for m in plans.get(real, [])}
    b = {m["seed"]: value(m, key) for m in plans.get(control, [])}
    pairs = [(s, a[s], b[s], round(a[s] - b[s], 4)) for s in sorted(a) if s in b and a[s] is not None and b[s] is not None]
    ra, rb = [v for v in a.values() if v is not None], [v for v in b.values() if v is not None]
    pooled = round(sum(ra) / len(ra) - sum(rb) / len(rb), 4) if ra and rb else None
    return {"real": real, "control": control, "key": key, "pairs": pairs, "pooled": pooled}


#: the gaps printed after the per-plan blocks: (real, control, quantity), every pair the decision table leans on
GAPS = (("CH1", "NOTRAIN", "grass_before_rival"), ("CH1", "DEADREST", "below.below_own"),
        ("CH1", "LOAF", "slices.yield"), ("CH1", "GREEDY", "slices.yield"), ("CH1", "ERRANDS_OFF", "slices.yield"),
        ("CH1", "LOAF", "slices.loaf"), ("CH1", "GREEDY", "slices.loaf"), ("CH1", "ERRANDS_OFF", "slices.loaf"),
        ("CH1", "LOAF", "split.outside.yield"), ("CH2", "CH2_OFF", "slices.yield"), ("CH2", "CH2_OFF", "slices.loaf"),
        ("CH1", "BLOCKED", "push_game"), ("CH1", "ERRANDS_OFF", "dex.frame"), ("CH1", "ERRANDS_OFF", "dex.no_battle"),
        ("CH2", "CH2_OFF", "wally.no_battle"), ("CH1", "STALL1", "await_game"), ("CH1", "STALL2", "await_game"),
        ("CH1", "STALL3", "await_game"))


# ------------------------------------------------------------------------------------------------ the decision table
def _vals(plans: dict, names, key: str) -> list:
    """(seed, value) per run of one plan; ("PLAN/seed", value) when several plans are pooled, so each value is named."""
    many = not isinstance(names, str) and len(names) > 1
    return [(f"{name}/{m['seed']}" if many else m["seed"], value(m, key))
            for name in ([names] if isinstance(names, str) else names) for m in plans.get(name, [])]


def _missing(plans: dict, names) -> list[str]:
    return [n for n in ([names] if isinstance(names, str) else names) if not plans.get(n)]


def rule_under(plans: dict, real, control, key: str, what: str) -> dict:
    """SEPARATES when every control run sits UNDER every real run (a per-run bound fits between them)."""
    r = [v for _, v in _vals(plans, real, key) if v is not None]
    c = [v for _, v in _vals(plans, control, key) if v is not None]
    row = {"quantity": what, "real": _vals(plans, real, key), "control": _vals(plans, control, key)}
    if not r or not c:
        return {**row, "verdict": f"NO NUMBER: no measured run of {_missing(plans, real) + _missing(plans, control) or 'a plan'}"
                                  f" (runs with no value are left out)"}
    return {**row, "verdict": "SEPARATES" if max(c) < min(r) else "DOES NOT",
            "rule": f"every control run under every real run: max control {max(c)} < min real {min(r)}"}


def rule_over(plans: dict, real, control, key: str, what: str) -> dict:
    """SEPARATES when every control run sits OVER every real run."""
    r = [v for _, v in _vals(plans, real, key) if v is not None]
    c = [v for _, v in _vals(plans, control, key) if v is not None]
    row = {"quantity": what, "real": _vals(plans, real, key), "control": _vals(plans, control, key)}
    if not r or not c:
        return {**row, "verdict": f"NO NUMBER: no measured run of {_missing(plans, real) + _missing(plans, control) or 'a plan'}"}
    return {**row, "verdict": "SEPARATES" if min(c) > max(r) else "DOES NOT",
            "rule": f"every control run over every real run: min control {min(c)} > max real {max(r)}"}


def rule_rest(plans: dict) -> dict:
    """The rest rule's own plan: GRADED only if the real code's count is 0 and DEADREST's over 0."""
    what = "wild battles STARTED under the run's own heal_below (read i, the game's party HP)"
    r, c = _vals(plans, "CH1", "below.below_own"), _vals(plans, "DEADREST", "below.below_own")
    row = {"quantity": what, "real": r, "control": c}
    if not r or not c:
        return {**row, "verdict": f"NO NUMBER: no measured run of {_missing(plans, ['CH1', 'DEADREST'])}"}
    # (the A2 fix round) a run with no number (its battle starts and ends do not alternate: `battles_below`) is LEFT OUT,
    # never read as 0: "real = 0" needs every real run counted, so a real run left out can only refute it, never prove it
    total_r, total_c = sum(v for _, v in r if v is not None), sum(v for _, v in c if v is not None)
    out_r, out_c = [s for s, v in r if v is None], [s for s, v in c if v is None]
    rule = (f"real = 0 and DEADREST > 0: real {total_r}, DEADREST {total_c}"
            + (f" (no number, left out: real {out_r}, DEADREST {out_c})" if out_r or out_c else ""))
    if total_r > 0 or (not out_r and not out_c) or (not out_r and total_c > 0):
        return {**row, "verdict": "SEPARATES" if total_r == 0 and total_c > 0 else "DOES NOT", "rule": rule}
    return {**row, "verdict": f"NO NUMBER: runs with no number decide it (real {out_r}, DEADREST {out_c})", "rule": rule}


def rule_stall(plans: dict, arms: list[str]) -> dict:
    """The game's path alone: every real run under AWAIT_MAX, each stall arm over it in STALL_ARM_HITS_MIN+ runs."""
    bound = BOUNDS["AWAIT_MAX"]
    what = f"the longest wait for a press with none, by the GAME's path alone (`waits_game`; bound {bound})"
    r = _vals(plans, list(REAL_PLANS), "await_game")
    c = _vals(plans, arms, "await_game")
    row = {"quantity": what, "real": r, "control": c}
    gone = _missing(plans, arms)
    if not r or gone:
        return {**row, "verdict": f"NO NUMBER: no measured run of {gone or list(REAL_PLANS)}"}
    hits = {arm: sum(1 for m in plans[arm] if (m["await_game"] or 0) >= bound) for arm in arms}
    ok = max(v or 0 for _, v in r) < bound and all(n >= BOUNDS["STALL_ARM_HITS_MIN"] for n in hits.values())
    return {**row, "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"every real run < {bound} (max {max(v or 0 for _, v in r)}); runs >= {bound} per arm {hits} (each >= "
                    f"{BOUNDS['STALL_ARM_HITS_MIN']})"}


def _pairs_divergence(rows: list[dict], key: str) -> list[float]:
    """Per pair of runs of one personality: the Jaccard distance of their stood tiles (`_stood`) or the normalized edit
    distance of their map order (`_maps`)."""
    from ai_player.gates.rate_step5 import edit_distance

    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["personality"] != b["personality"]:
                continue
            if key == "_stood":
                union = a[key] | b[key]
                out.append(round(1 - len(a[key] & b[key]) / len(union), 3) if union else 0.0)
            else:
                longest = max(len(a[key]), len(b[key]), 1)
                out.append(round(edit_distance(a[key], b[key]) / longest, 3))
    return out


def rule_divergence(plans: dict, key: str, bound: float | None) -> dict:
    """The game's paths (stood tiles) or map order diverge more between seeds of one personality under CH1 than under the
    beeline (ERRANDS_OFF); with `bound`, CH1's mean must also reach it."""
    what = ("the stood tiles' Jaccard distance between seeds of one personality (the game's moves)" if key == "_stood"
            else "the order of maps entered, edit distance between seeds of one personality (the goal sequence's nearest "
                 "game analog)")
    r, c = _pairs_divergence(plans.get("CH1", []), key), _pairs_divergence(plans.get("ERRANDS_OFF", []), key)
    row = {"quantity": what, "real": r, "control": c}
    if not r or not c:
        return {**row, "verdict": "NO NUMBER: no pair of runs of one personality in CH1 and ERRANDS_OFF (it needs 2+ seeds "
                                  "of a personality)"}
    mr, mc = sum(r) / len(r), sum(c) / len(c)
    ok = mr > mc and (bound is None or mr >= bound)
    return {**row, "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"CH1 mean {mr:.3f} > ERRANDS_OFF mean {mc:.3f}" + (f" and >= {bound}" if bound is not None else "")}


def rule_off_beeline(plans: dict) -> dict:
    """The tiles a CH1 run stood on that no ERRANDS_OFF run stood on, against each control run's own leave-one-out (the
    plan's rule, `rate_step5.off_beeline`, on the GAME's tiles): more in OFF_SEEDS_MIN of the paired seeds, pooled at least
    OFF_RATIO_MIN."""
    what = "tiles stood on (the game's moves) that no beeline run stood on; a control run against the other control runs"
    ch1, off = plans.get("CH1", []), plans.get("ERRANDS_OFF", [])
    if not ch1 or len(off) < 2:
        return {"quantity": what, "real": [], "control": [],
                "verdict": "NO NUMBER: it needs CH1 runs and 2+ ERRANDS_OFF runs (a leave-one-out)"}
    union = set().union(*(m["_stood"] for m in off))
    runs = {m["seed"]: len(m["_stood"] - union) for m in ch1}
    alone = {m["seed"]: len(m["_stood"] - set().union(*(o["_stood"] for o in off if o is not m))) for m in off}
    paired = [(s, runs[s], alone[s]) for s in sorted(runs) if s in alone]
    more = [p for p in paired if p[1] > p[2]]
    pooled = sum(p[1] for p in paired) / max(1, sum(p[2] for p in paired)) if paired else 0.0
    ok = bool(paired) and len(more) >= BOUNDS["OFF_SEEDS_MIN"] * len(paired) and pooled >= BOUNDS["OFF_RATIO_MIN"]
    return {"quantity": what, "real": sorted(runs.items()), "control": sorted(alone.items()),
            "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"CH1 more in {len(more)} of {len(paired)} (>= {BOUNDS['OFF_SEEDS_MIN']:.0%}), pooled {pooled:.2f} (>= "
                    f"{BOUNDS['OFF_RATIO_MIN']})"}


def rule_ratio(plans: dict, real: str, control: str, key: str, what: str, ratio_min: float,
               seeds_min: float | None) -> dict:
    """Paired by seed: real over control pooled at least `ratio_min`, and (with `seeds_min`) real the slower in that share
    of the pairs. The bound is the plan's to re-derive; this says whether the measured gap is on the right side of it."""
    a = {m["seed"]: value(m, key) for m in plans.get(real, [])}
    b = {m["seed"]: value(m, key) for m in plans.get(control, [])}
    pairs = [(s, a[s], b[s]) for s in sorted(a) if s in b and a[s] and b[s]]
    row = {"quantity": what, "real": sorted(a.items()), "control": sorted(b.items())}
    if not pairs:
        return {**row, "verdict": f"NO NUMBER: no seed with a value in both {real} and {control}"}
    pooled = sum(p[1] for p in pairs) / sum(p[2] for p in pairs)
    slower = [p for p in pairs if p[1] > p[2]]
    ok = pooled >= ratio_min and (seeds_min is None or len(slower) >= seeds_min * len(pairs))
    return {**row, "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"pooled {real}/{control} {pooled:.3f} (>= {ratio_min})"
                    + (f", {real} slower in {len(slower)} of {len(pairs)} (>= {seeds_min:.0%})" if seeds_min is not None else "")}


def rule_lose(plans: dict) -> dict:
    """LOSE3's game/harness half: the run ended within STOP_WITHIN frames of the game's MAX_LOSSES-th loss (MAX_LOSSES as
    the harness recorded it). The plan names no control for it; the nearest that exists is STOPDEAD (MAX_LOSSES 1 with
    the loop's count removed, which must go on past it), beside STOP (MAX_LOSSES 1, which must stop)."""
    what = f"frames from the game's MAX_LOSSES-th loss to the run's end (bound {STOP_WITHIN})"
    r = [(m["seed"], m["base"], value(m, "losses.after_cap")) for name in ("LOSE3", "STOP") for m in plans.get(name, [])]
    c = [(m["seed"], m["base"], value(m, "losses.after_cap")) for m in plans.get("STOPDEAD", [])]
    rr, cc = [v for *_, v in r if v is not None], [v for *_, v in c if v is not None]
    row = {"quantity": what, "real": r, "control": c}
    if not rr or not cc:
        return {**row, "verdict": "NO NUMBER: no LOSE3/STOP run that reached its MAX_LOSSES, or no STOPDEAD run that did "
                                  "(STOP and STOPDEAD replay only phase-1 runs the game recorded a loss in)"}
    return {**row, "verdict": "SEPARATES" if max(rr) <= STOP_WITHIN < min(cc) else "DOES NOT",
            "rule": f"LOSE3/STOP all <= {STOP_WITHIN} (max {max(rr)}), STOPDEAD all > it (min {min(cc)})"}


def rule_patience(plans: dict) -> dict:
    """PATIENCE's not-vacuous half by the game: a training stint (first to last grass step before the rival) longer than
    the copy's patience in at least one PATIENCE run (else the A/B tests nothing)."""
    what = f"the training stint by the game (first to last tall-grass step before the rival, frames; vs SMALL_PATIENCE {SMALL_PATIENCE})"
    r, c = _vals(plans, "PATIENCE", "stint"), _vals(plans, "PATIENCE_OLD", "stint")
    row = {"quantity": what, "real": r, "control": c}
    if not r:
        return {**row, "verdict": "NO NUMBER: no PATIENCE run (it plays only the Trainer's seeds)"}
    long_ = [s for s, v in r if (v or 0) > SMALL_PATIENCE]
    return {**row, "verdict": "SEPARATES" if long_ else "DOES NOT",
            "rule": f"a PATIENCE stint > {SMALL_PATIENCE} in {long_ or 'no run'} (the A/B is exercised)"}


def rule_yield(plans: dict, real: str, controls: list[str]) -> dict:
    """The slice yield (module docstring): each control under every real run (a per-run bound between them). The row
    SEPARATES only when every named control does; which ones do is on the rule."""
    what = f"the slice yield by the game ({SLICE}-frame slices with no battle productive by tiles/page/capture/item)"
    each = {c: rule_under(plans, real, c, "slices.yield", what) for c in controls}
    row = {"quantity": what, "real": _vals(plans, real, "slices.yield"),
           "control": {c: _vals(plans, c, "slices.yield") for c in controls}}
    numbers = {c: r["verdict"] for c, r in each.items()}
    if any(v.startswith("NO NUMBER") for v in numbers.values()):
        return {**row, "verdict": f"NO NUMBER: {[c for c, v in numbers.items() if v.startswith('NO NUMBER')]} not measured",
                "rule": str(numbers)}
    sep = [c for c, v in numbers.items() if v == "SEPARATES"]
    return {**row, "verdict": "SEPARATES" if len(sep) == len(controls) else "DOES NOT",
            "rule": f"separated: {sep or 'none'}; not: {[c for c in controls if c not in sep] or 'none'} (pooled: the gaps)"}


def rule_loaf(plans: dict) -> dict:
    """LOAF must fail a bound every real run meets: LOAF_FAILS_RUNS_MIN of its runs over the real code's most loafing."""
    what = f"loafing slices by the game ({SLICE}-frame slices with no battle productive by none of tiles/page/capture/item)"
    r, c = _vals(plans, list(REAL_PLANS), "slices.loaf"), _vals(plans, "LOAF", "slices.loaf")
    row = {"quantity": what, "real": r, "control": c}
    if not r or not c:
        return {**row, "verdict": f"NO NUMBER: no measured run of {_missing(plans, ['LOAF']) or list(REAL_PLANS)}"}
    top = max(v for _, v in r)
    over = [s for s, v in c if v > top]
    return {**row, "verdict": "SEPARATES" if len(over) >= BOUNDS["LOAF_FAILS_RUNS_MIN"] else "DOES NOT",
            "rule": f"LOAF runs over the real code's most ({top}): {over or 'none'} (>= {BOUNDS['LOAF_FAILS_RUNS_MIN']})"}


def rule_push(plans: dict) -> dict:
    """The game's pushing path alone: every real run under PUSH_MAX, BLOCKED_HITS_MIN BLOCKED runs at or over it."""
    bound = BOUNDS["PUSH_MAX"]
    what = f"the longest free stretch of pressing that brought nothing new, by the GAME (`places.push`; bound {bound})"
    r, c = _vals(plans, list(REAL_PLANS), "push_game"), _vals(plans, "BLOCKED", "push_game")
    row = {"quantity": what, "real": r, "control": c}
    if not r or not c:
        return {**row, "verdict": f"NO NUMBER: no measured run of {_missing(plans, ['BLOCKED']) or list(REAL_PLANS)}"}
    hits = [s for s, v in c if (v or 0) >= bound]
    ok = max(v or 0 for _, v in r) < bound and len(hits) >= BOUNDS["BLOCKED_HITS_MIN"]
    return {**row, "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"real max {max(v or 0 for _, v in r)} < {bound}; BLOCKED runs >= it {hits or 'none'} (>= "
                    f"{BOUNDS['BLOCKED_HITS_MIN']})"}


def rule_own_losses(plans: dict) -> dict:
    """HONESTY: the AI's reported losses (AI DATA) against the game's, every real run equal; STOPDEAD (its report says 0
    where the game lost) apart in at least one run."""
    what = "|the AI's reported losses - the game's losses| (AI report as DATA against gBattleOutcome LOST)"

    def apart(names):
        return [(f"{name}/{m['seed']}", None if value(m, "losses.ai") is None
                 else abs(value(m, "losses.ai") - value(m, "losses.game"))) for name in names for m in plans.get(name, [])]

    r, c = apart(list(REAL_PLANS)), apart(["STOPDEAD"])
    row = {"quantity": what, "real": r, "control": c}
    if not r or not c:
        return {**row, "verdict": "NO NUMBER: no STOPDEAD run (it replays only phase-1 runs the game recorded a loss in)"}
    ok = all(v == 0 for _, v in r) and any((v or 0) > 0 for _, v in c)
    return {**row, "verdict": "SEPARATES" if ok else "DOES NOT",
            "rule": f"every real run 0 ({[v for _, v in r]}); STOPDEAD apart in {[s for s, v in c if (v or 0) > 0] or 'none'}"}


def no_number(why: str, what: str = "-", show: tuple | None = None):
    """A row with nothing to separate; `show` = (plans, key, names) prints the values measured anyway."""
    def rule(plans: dict) -> dict:
        real = _vals(plans, show[2], show[1]) if show else []
        return {"quantity": what, "real": real, "control": [], "verdict": f"NO NUMBER: {why}"}
    return rule


def ruling(why: str):
    def rule(plans: dict) -> dict:
        return {"quantity": "-", "real": [], "control": [], "verdict": "RULING", "rule": why}
    return rule


#: (the A2 fix round) the controls a chapter-1 curiosity YIELD must separate from the real code (the critic's Q3); never
#: GREEDY, the spacing control
YIELD_CONTROLS = ("LOAF", "ERRANDS_OFF")
SPIN_CONTROL = ("no spin control exists (PLANS has none); its smallest form: a copy (an `EXTRA_EDITS` entry, as LOAF) whose "
                "training roam presses the direction it does not face and back on the spot before each step: the real "
                "code's game spins per move must sit under it")
#: every `b1_debt.json` id -> its rule (the plan's own words, made a function of the measured plans)
ROW_RULES = {
    "R5.CH1_TRAINED": lambda p: rule_under(p, "CH1", "NOTRAIN", "grass_before_rival",
                                           "tall-grass steps from the starter's mark to the rival's flag (read ii)"),
    "R5.NOTRAIN_TRAINED_CHECK": lambda p: rule_under(p, "CH1", "NOTRAIN", "grass_before_rival",
                                                     "tall-grass steps from the starter's mark to the rival's flag (read ii)"),
    "L5.TRAINED": lambda p: rule_under(p, "CH1", "NOTRAIN", "grass_before_rival",
                                       "the sweep's tall-grass steps before the rival (here DIAGNOSTIC)"),
    "R5.CH1_SPINS": no_number(SPIN_CONTROL, "the game's spins per move (read iii)", ("", "spins.ratio", "CH1")),
    "L5.SPINS": no_number(SPIN_CONTROL, "the game's spins per move (read iii)", ("", "spins.ratio", "CH1")),
    "R5.CH1_REST_RULE": rule_rest, "R5.DEADREST": rule_rest, "L5.REST_RULE": rule_rest,
    "R5.STALL": lambda p: rule_stall(p, ["STALL1", "STALL2", "STALL3"]),
    "R5.STALL1": lambda p: rule_stall(p, ["STALL1"]), "R5.STALL2": lambda p: rule_stall(p, ["STALL2"]),
    "R5.STALL3": lambda p: rule_stall(p, ["STALL3"]),
    "L5.STALL": lambda p: rule_stall(p, ["STALL1", "STALL2", "STALL3"]),
    "R5.SEED_DIVERGENCE": lambda p: rule_divergence(p, "_stood", BOUNDS["DIV_TILES_MIN"]),
    "R5.OFF_MOVES_DIVERGENCE": lambda p: rule_divergence(p, "_maps", None),
    "R5.OFF_BEELINE": rule_off_beeline,
    "R5.NO_SPEEDRUN": lambda p: rule_ratio(p, "CH1", "ERRANDS_OFF", "dex.frame", "frames to the POKéDEX by the game, paired",
                                           BOUNDS["SLOWER_THAN_BEELINE_MIN"], None),
    "R5.NO_SPEEDRUN_DICE": lambda p: rule_ratio(p, "CH1", "ERRANDS_OFF", "dex.no_battle",
                                                "frames to the POKéDEX less the game's battle frames, paired",
                                                BOUNDS["NOBATTLE_RATIO_MIN"], BOUNDS["NOBATTLE_SEEDS_MIN"]),
    "R5.CH2_NOBATTLE": lambda p: rule_ratio(p, "CH2", "CH2_OFF", "wally.no_battle",
                                            "frames to WALLY's tutorial less the game's battle frames, paired",
                                            BOUNDS["CH2_NOBATTLE_RATIO_MIN"], BOUNDS["CH2_NOBATTLE_SEEDS_MIN"]),
    "R5.LOSE3": rule_lose, "R5.PATIENCE": rule_patience,
    # (the A2 fix round) the YIELD controls only: LOAF and the beeline ERRANDS_OFF (the spec critic's Q3: "registered only
    # if LOAF and BEELINE fall below it ... AND GREEDY is acknowledged as not covered"). GREEDY is the SPACING control
    # (`grader_checks` R5.GREEDY, DIAGNOSTIC: goal KINDS in a row have no game form), and as a named control here its
    # values alone could force this row to DOES NOT; its yield gap is still printed (GAPS) as data
    "R5.CH1_YIELD": lambda p: rule_yield(p, "CH1", list(YIELD_CONTROLS)),
    "R5.CH2_YIELD": lambda p: rule_yield(p, "CH2", ["CH2_OFF"]),
    "R5.NO_LOAFING": rule_loaf, "R5.LOAF": rule_loaf,
    "R5.PUSHING": rule_push,
    "R5.BLOCKED": no_number("the reach (someone in the way of a curiosity walk) has no game read; its smallest form: the "
                            "harness reads the object events on the tile the player faces whenever a move press brought "
                            "no move", "the BLOCKED arm's game pushing (shown)", ("", "push_game", "BLOCKED")),
    "L5.PURITY_PRESSES": ruling("an instrument cross-check of the AI's own counter (the plan: a coordinator ruling)"),
    "L5.PURITY_FRAMES": ruling("as L5.PURITY_PRESSES"),
    "L5.PRESS_GATES": ruling("a property of the AI's own hands with no game form in a launcher run"),
    "L5.A_KINDS": ruling("as L5.PRESS_GATES"), "L5.BLIND": ruling("as L5.PRESS_GATES"),
    "L5.HAS_GOAL": ruling("as L5.PRESS_GATES"),
    "L5.PURITY_ENDED": no_number("a LAUNCHER property and no control in a sweep (every sweep run is ended by whoever the "
                                 "harness's stop record names: shown); builder 1's live known answers showed both ways "
                                 "(dev seeds 1305, 1306)", "who ended the run, by the harness's own record (read v)",
                                 ("", "stop_by", list(REAL_PLANS))),
    "L5.PURITY_OUTCOME": no_number("a reclassification, nothing to measure: the game's proofs of the target "
                                   "(L5.CH1_PROOFS / L5.CH2_WALLY) are its game half"),
    "L5.NEW_PLACE": no_number("no game half in a launcher run (the plan: DIAGNOSTIC; the sweep's R5.CH2_NEW_PLACE and "
                              "R5.LEFT_NOT_NEW are the HONESTY checks)"),
    "L5.OWN_LOSSES": rule_own_losses,
    "L5.OWN_TRAINING": no_number("the AI's fight-preparation claim has no game counterpart in a sweep beyond the grass "
                                 "read (R5.CH1_TRAINED's numbers); an honesty control (a copy that claims training it did "
                                 "not do) does not exist"),
    "L5.SHOPPED": no_number("a launcher re-sourcing (`truth_of` reads the bag and money there); the sweep's truth record "
                            "reads neither, and the plan names no control"),
}


def debt_ids(path: Path = DEBT) -> list[str]:
    return list(json.loads(path.read_text(encoding="utf-8"))["debt"])


def decision_table(plans: dict, ids: list[str] | None = None) -> tuple[list[dict], dict]:
    """One row per debt id, and the counts. RAISES on a debt id with no rule (a new debt row must get its measurement)."""
    ids = debt_ids() if ids is None else ids
    missing = [i for i in ids if i not in ROW_RULES]
    if missing:
        raise KeyError(f"b1_debt.json ids with no measurement rule in measure_step5.ROW_RULES: {missing}")
    rows = [{"id": i, **ROW_RULES[i](plans)} for i in ids]
    counts = {"separates": 0, "does not": 0, "no number": 0, "ruling": 0}
    for row in rows:
        v = row["verdict"]
        key = ("separates" if v == "SEPARATES" else "does not" if v == "DOES NOT" else "ruling" if v == "RULING"
               else "no number")
        counts[key] += 1
    return rows, counts


# ------------------------------------------------------------------------------------------------------------ printing
def run_line(m: dict) -> str:
    s, split = m["slices"], m["split"]
    below = m["below"]
    started = (f"started {below['starts']} (wild {below['wild']}, unread {below['unread']}) under {below['below']}, under "
               f"own heal_below {below['heal_below']}: {below['below_own']}" if not below.get("no_number") else
               f"started under each HP fraction: {below['no_number']}")
    return (f"  {m['plan']}{'(' + m['base'] + ')' if m.get('base') else ''} seed {m['seed']} ({m['personality']}): "
            f"frames {m['frames']}; windows {len(m['windows'])} non-battle {m['windows']}; slices {s['n']} (tiles "
            f"{s['tiles']}, page {s['page']}, battle {s['battle']}, capture {s['capture']}, item {s['item']}; no battle "
            f"{s['calm']}, productive {s['productive']}, loaf {s['loaf']}, yield {s['yield']}); inside curiosity "
            f"{split['inside']['calm']}/{split['inside']['productive']} yield {split['inside']['yield']}, OUTSIDE (base) "
            f"{split['outside']['calm']}/{split['outside']['productive']} yield {split['outside']['yield']}; grass before "
            f"the rival {m['grass_before_rival']} (all grass steps {m['grass_steps']}, stint {m['stint']}); battles "
            f"{started}; spins {m['spins']['spins']} / moves "
            f"{m['spins']['moves']} (harness's count {m['spins']['stored']}, agree {m['spins']['agree']}); await_game "
            f"{m['await_game']}; push_game {m['push_game']}; dex {m['dex']}; wally {m['wally']}; losses {m['losses']}; "
            f"stop by {m['stop_by']}; frames equal {m['frames_equal']}")


def plan_line(plan: str, rows: list[dict]) -> str:
    def pooled(part: str) -> tuple:
        calm = sum(value(m, f"{part}.calm") or 0 for m in rows)
        made = sum(value(m, f"{part}.productive") or 0 for m in rows)
        return made, calm, round(made / calm, 4) if calm else None

    grass = [m["grass_before_rival"] for m in rows]
    # (the A2 fix round) a run with no number (`battles_below`) is left out of the plan's sums and named, never added as 0
    counted = [m for m in rows if not m["below"].get("no_number")]
    apart = [m["seed"] for m in rows if m["below"].get("no_number")]
    below = {str(f): sum(m["below"]["below"][str(f)] for m in counted) for f in HP_FRACTIONS}
    spins = sum(m["spins"]["spins"] for m in rows), sum(m["spins"]["moves"] for m in rows)
    return (f"PLAN {plan}: runs {len(rows)}; pooled yield (productive, no-battle slices, yield) {pooled('slices')}; base "
            f"rate outside curiosity {pooled('split.outside')}, inside {pooled('split.inside')}; loaf slices "
            f"{[m['slices']['loaf'] for m in rows]}; grass before the rival {grass}; battles started under "
            + (f"{below}, under own heal_below {sum(m['below']['below_own'] for m in counted)}" if counted else "NO NUMBER")
            + (f" (NO NUMBER, left out: seeds {apart}, starts and ends do not alternate)" if apart else "")
            + f"; spins/moves {spins}; await_game "
            f"{[m['await_game'] for m in rows]}; push_game {[m['push_game'] for m in rows]}")


def report(measured: list[dict], skipped: list[str]) -> tuple[list[str], list[dict], dict]:
    plans = by_plan(measured)
    lines = [f"MEASURE STEP 5 (stage A2; measurement only: nothing graded or registered): {len(measured)} runs in "
             f"{len(plans)} plans; folders with no {RUN_FILE} skipped: {len(skipped)}",
             f"slice {SLICE} frames; tiles criterion >= {SLICE_TILES} new tiles or a map first stood on; HP fractions "
             f"{list(HP_FRACTIONS)}"]
    real = [m for plan in REAL_PLANS for m in plans.get(plan, [])]
    calm = sum(m["split"]["outside"]["calm"] for m in real)
    made = sum(m["split"]["outside"]["productive"] for m in real)
    lines.append(f"THE REAL CODE'S BASE RATE outside its curiosity spans ({list(REAL_PLANS)}, the AI's spans as DATA): "
                 f"{made} of {calm} no-battle slices productive ({round(made / calm, 4) if calm else None})")
    for plan, rows in plans.items():
        lines.append(plan_line(plan, rows))
        lines += [run_line(m) for m in rows]
    lines.append("GAPS (real - control; per paired seed (seed, real, control, gap); pooled = the plans' means):")
    for real_plan, control, key in GAPS:
        g = gap(plans, real_plan, control, key)
        lines.append(f"  {real_plan} - {control} {key}: pairs {g['pairs']}; pooled {g['pooled']}")
    rows, counts = decision_table(plans)
    lines.append(f"DECISION TABLE ({len(rows)} rows, one per b1_debt.json entry):")
    for row in rows:
        lines.append(f"  {row['id']}: {row['verdict']} | quantity: {row['quantity']} | real: {row['real']} | control: "
                     f"{row['control']}" + (f" | rule: {row['rule']}" if row.get("rule") else ""))
    lines.append(f"DECISION TABLE COUNTS: separates {counts['separates']}, does not {counts['does not']}, no number "
                 f"{counts['no number']}, ruling {counts['ruling']} (of {len(rows)})")
    return lines, rows, counts


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="+", type=Path, help="a sweep's run-folder root, or run folders")
    parser.add_argument("--json", type=Path, help="also write every measured number here")
    args = parser.parse_args(argv)
    runs, skipped = load_sweep(args.paths)
    if not runs:
        print(f"MEASURE STEP 5: NOTHING TO MEASURE: no folder under {[str(p) for p in args.paths]} holds a {RUN_FILE} "
              f"(skipped {len(skipped)})")
        return 1
    measured = [measure_run(r) for r in runs]
    lines, rows, counts = report(measured, skipped)
    print("\n".join(lines))
    if args.json:
        clean = [{k: v for k, v in m.items() if not k.startswith("_")} for m in measured]
        args.json.write_text(json.dumps({"runs": clean, "table": rows, "counts": counts}, default=str, ensure_ascii=False),
                             encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
