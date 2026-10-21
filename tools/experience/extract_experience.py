"""A6 EXPERIENCE RECORDS: what happened in each of the bot's games, kept after its raw logs are pruned (spec S3-3).

    py -3.12 tools/experience/extract_experience.py --incremental   # append the runs not yet extracted (the routine call)
    py -3.12 tools/experience/extract_experience.py --full          # first build of an EMPTY store (refuses otherwise)
    py -3.12 tools/experience/extract_experience.py --priors        # regenerate chapter_priors.json (INTERACTIVE only)
    py -3.12 tools/experience/extract_experience.py --check-priors <file>   # the E7 privacy gate on an AI-facing file

WHY. The bot tuner (`C:/Remote Projects/pokebot-learner`, the "clone") plays ~50 games a cycle and keeps only a small
row per game in `ai-agent/data/runs.jsonl`. Its raw logs said much more (every boss fight's money, healing stock, the
moves used, whiteouts, the team at each badge) and were DELETED after `keep_raw_cycles` cycles: on 2026-10-19 only 592
of 2,424 rows still had a log (fact 9). O3 (2026-10-21) now zips old cycles into `runs/<tag>/raw.zip` instead, but
nothing READ them. This script turns each game into one small record, once, BEFORE its raw data can go, and keeps it
in a git-ignored store. The AI player later reads a few numbers per boss from `chapter_priors.json` as a PRIOR ON
NEEDS ("the bot's teams that beat Norman had a median team level near 29"), never as a policy: the bot's games are
teaching material,
not the AI's hands (USER RULING 35), so the AI-facing file is labelled "bot corpus" on every block and carries NO
species shares (which species the bot chose is the bot's style, not a need). Its failure labels pass an ALLOWLIST of
fixed label names (`ALLOWED_LABELS`; anything else is counted as `<other>`), and the whole file then passes the E7
denylist gate, an independent second layer (USER RULING 40: no live hidden state, no species, PID, position or flag).

TWO TIERS (fact 8). Tier A comes from the `runs.jsonl` row (every row; survives pruning): per boss `won`, `losses`,
the parties at first loss and at the win (`ast.literal_eval` of the stored repr string), the win frame from
`milestones`, and the run's wall label. Tier B comes from the raw log, read line by line from the run folder or from
one member of `raw.zip` (`ZipFile.open`, never extracted to disk): every boss-class `[TRAINER] start/end` pair, the
team from the newest `[hb]` before the start (its age in frames is kept: heartbeats are 3,600 frames apart), the
moves used and the `UseItem` turns between start and end, `[BADGE]` frames, whiteouts, derail texts and `[GYM_TM]`
walls. The lane profile's `badge-log.json` (the team, levels, moves and held items at every badge) is joined to a run
by IDENTITY: its `run_index` must be the run's position in its lane AND every entry's frame must equal that run's
`[BADGE] n=` frame; anything else is not attached (session rule 3: identity, never position alone).

TIER B IS CROSS-CHECKED AGAINST TIER A (E2). `scoring.py` (the tuner's parser, read 2026-10-21, lines 53-100) defines:
a run starts at its first `Story: choosing X!` line (earlier lines are a stale save's boot and are ignored); a boss is
one of the 13 key trainer ids (`knowledge.KEY_TRAINERS`); `won` = some `[TRAINER] end opp=<id> ... res=Won` after the
start; `losses` = the number of such end lines whose `res` is anything else (an incomplete fight with no end line is
neither). This script re-derives both from start/end PAIRS with its own parser and writes `agrees_with_runs_jsonl`
per boss; any disagreement is listed in the record and makes the run exit 1. Never averaged away. One case is
adjudicated, not a disagreement: a boss whose only fights in the log are INCOMPLETE (started, never ended) has no
`boss_log` entry, because scoring.py makes one only on an end line; it is listed in `bosses_incomplete_only`.

CENSORING (the statistics rule). A game cut by the batch's time limit (`usable: false`) is a valid prefix for the bosses
it resolved, but its unresolved boss is NOT a failure. Boss statistics use rows where the boss was resolved (won, or
lost at least once in a `usable` game); failure and wall counts use `usable` rows only; every aggregate prints `n` and
`n_censored` (E4).

THE DIGEST RULE (critic fix, E10). `chapter_priors.json` lives in `ai_player/`, inside the AI's code-under-test digest
(`ai_player/gates/provenance.py`); a change during a graded sweep turns its verdict into FAIL "the tree changed
mid-run". So `--incremental` and `--full` write ONLY the store (refused, exit 2, if the store is pointed inside
`ai_player/` or into the clone), and only an interactive `--priors` call, between graded rounds, writes the priors.
Until the O1 watchdog task exists and is registered (that needs the user's OK), a session runs `--incremental` by hand;
since O3, a cycle's logs stay readable inside its `raw.zip`, so a late run still finds them.

THE WRITE GUARD compares RESOLVED paths (`realpath`: junctions, symlinks, 8.3 short names such as `C:\\REMOTE~1\\...`,
the `\\\\?\\` prefix, case, slashes) AND file identity (a UNC admin share such as `\\\\localhost\\C$\\...` reaches the
same folder under a spelling `realpath` keeps). It always protects the DEFAULT clone and this checkout's `ai_player/`,
not only the trees `--clone`/`--repo` name, and the raw-data folders the run reads (review 2026-10-21: an abspath
compare let a junction, the `\\\\?\\` prefix and the clone's 8.3 short name through, and pointing `--repo` or
`--clone` elsewhere switched the guard off).

THE O3 RACE. O3 renames `raw.zip` into a cycle and then deletes its folder; a cycle opened as a folder can lose a log
(or a lane profile) in the middle of a pass. So a record whose log is missing or fails to read, or that was built
while `raw.zip` appeared, in a cycle that HAD raw data, is rebuilt once on a freshly opened cycle (re-checking
`raw.zip`). If its log is still missing and the cycle is not in its final archived form (`raw.zip` readable, folder
gone), or its read still fails, the run is DEFERRED: not appended, not in the cursor, named in a warning, and the next
`--incremental` retries it (exit 6). An append-only store never revisits a key, so a tier-A-only record written
during the race would have lost tier B for good.

LIMITS (stated in the store header and the priors file, measured on the real logs 2026-10-19/21): `UseItem` turns do
not name the item, so "items used" is a count of UseItem turns plus the drop in `heal_stock` across a fight; no log
line carries the bot's move list or held item, so tier-B moves are "moves actually used" (a lower bound; the
badge-log has the full move list at each badge); the team is read from a heartbeat up to 3,600 frames old.

Exit codes: 0 ok; 1 at least one boss disagrees with runs.jsonl (records still written, each disagreement listed);
2 refused (a guard: see `Refused`); 3 the AI-facing file failed the privacy gate (nothing written); 5 CRASHED (an
uncaught error or an unreadable runs.jsonl line, named; never 1, which O1 or a reader would take for a disagreement);
6 some runs were DEFERRED by the O3 race (the rest written; the next `--incremental` retries them). With both a
disagreement and a deferral the exit is 1 and both are printed.
"""
from __future__ import annotations

import argparse
import ast
import collections
import json
import os
import re
import sys
import time
import traceback
import uuid
import zipfile
import zlib
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - the tuner and this checkout run on Windows
    import fcntl

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_CLONE = Path("C:/Remote Projects/pokebot-learner")
DEFAULT_STORE = HERE / "store"
PRIORS_REL = Path("ai_player/knowledge/experience/chapter_priors.json")
#: The AI's code-under-test digest scope (`ai_player/gates/provenance.py` PACKAGE_SCOPE). The routine paths
#: (`--incremental`, `--full`) never write inside it (E10).
DIGEST_SCOPE_REL = ("ai_player",)
STORE_FILE, CURSOR_FILE, LOCK_FILE = "runs_experience.jsonl", "cursor.json", ".lock"
#: The OS-locked sidecar that serialises taking `.lock` (see `StoreLock`). It stays in the store; it is never content.
MUTEX_FILE = ".lock.mutex"
#: A lock older than this is a crashed run's leftover (a full pass over ~900 logs measured about 4 minutes).
LOCK_STALE_S = 6 * 3600
#: How long a run waits for another run to finish TAKING the lock (milliseconds of work) before it gives up.
MUTEX_WAIT_S = 30.0
SCHEMA = 1
CORPUS = "bot corpus"
EXIT_OK, EXIT_DISAGREE, EXIT_REFUSED, EXIT_GATE, EXIT_CRASH, EXIT_DEFERRED = 0, 1, 2, 3, 5, 6

#: The 13 key bosses in story order, by the names `runs.jsonl` uses, and the decomp constant each one is.
BOSS_ORDER = ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY", "NORMAN", "WINONA", "TATE_AND_LIZA", "JUAN",
              "SIDNEY", "PHOEBE", "GLACIA", "DRAKE", "WALLACE")
BOSS_DECOMP = {k: f"TRAINER_{k}_1" for k in BOSS_ORDER[:8]} | {k: f"TRAINER_{k}" for k in BOSS_ORDER[8:]}
#: Used only when the pinned decomp is absent (the header says so). When it IS present, the decomp's ids must equal
#: these or the run is refused: `runs.jsonl` names bosses by these ids (`knowledge.KEY_TRAINERS`), so a drift would
#: make every E2 comparison wrong.
BOSS_IDS_FALLBACK = {265: "ROXANNE", 266: "BRAWLY", 267: "WATTSON", 268: "FLANNERY", 269: "NORMAN", 270: "WINONA",
                     271: "TATE_AND_LIZA", 272: "JUAN", 261: "SIDNEY", 262: "PHOEBE", 263: "GLACIA", 264: "DRAKE",
                     335: "WALLACE"}
LEADER_KEYS = BOSS_ORDER[:8]
#: Trainer classes (as logged, `class=0x20(LEADER)`) whose fights tier B keeps besides the 13: rematches, the team
#: bosses. Measured classes in ai0034 L1-3: LEADER, TEAM_AQUA, COOLTRAINER, TEAM_MAGMA, MAGMA_LEADER.
BOSS_CLASSES = frozenset({"LEADER", "ELITE_FOUR", "CHAMPION", "MAGMA_LEADER", "AQUA_LEADER"})
#: Tags this parser reads, the ones `scoring.py` reads, the 2026-10-19 census of one log, and the nine more found by
#: the first full pass over all 754 raw logs (2026-10-21: KEYBATTLE ... STALL). Any other tag is COUNTED in
#: `unknown_tags`, so a tag the bot starts writing later shows up there (format drift, E8); never fatal.
KNOWN_TAGS = frozenset({"BATTLE", "DMGAUDIT", "PARTY", "MAP", "hb", "BALLS", "STEP", "MONEY", "TRAINER", "PC", "LEARN",
                        "STORY", "GYM_TM", "BADGE", "RESUMED", "CATCH", "DEX", "DEXFENCE", "EARLY_BASKET",
                        "KEYBATTLE", "WEAKEN", "MAINTAIN", "DEXCATCH", "CATCHTEAM", "DBLITEM", "RESERVE",
                        "AMULET_COIN", "STALL"})
#: E8: a log this long with no `[TRAINER] start` at all is format drift, not an empty game.
SUSPECT_MIN_LINES = 1000
#: The tags whose line is decoded and parsed (every other line costs one regex match and a counter bump).
PARSED_TAGS = frozenset({"hb", "TRAINER", "BADGE", "STORY", "GYM_TM"})

LIMITS = [
    "UseItem turns do not name the item: items used = a count of UseItem turns per fight plus the heal_stock drop "
    "across the fight",
    "no log line carries the bot's move list or held items: tier-B moves are moves actually used (a lower bound); the "
    "badge-log holds the full move list at each badge",
    "tier B reads the team from the newest heartbeat before a fight STARTS, up to 3,600 frames old "
    "(party_age_frames); tier A's parties (party_first_loss, party_win) are scoring.py's newest heartbeat before the "
    "fight ENDED, so they can include levels gained in that fight",
    "a game cut by the time limit (usable false) is censored: its unresolved boss is not a failure",
]

STARTER_RE = re.compile(r"Story: choosing (\w+)!")
FRAME_TAG_RE = re.compile(rb"^f(\d+) \[([A-Za-z_]+)\]")
KV_RE = re.compile(r"(\w+)=(\S+)")
CLASS_RE = re.compile(r"\bclass=0x[0-9a-fA-F]+\((\w+)\)")
MONEY_PAIR_RE = re.compile(r"\bmoney=(\d+)->(\d+)")
TURN_RE = re.compile(r"\[TURN (\d+)\] (.+?) L\d+ \S+ -> (UseMove:(.+?)\(pp\d+\)|UseItem)")
HB_PARTY_RE = re.compile(r"\bparty=(\[[^\]]*\])")
MON_RE = re.compile(r"""['"]([^'":]+):L(\d+)['"]""")
BADGE_RE = re.compile(r"\[BADGE\] n=(\d+) party=(\d+)/")
WHITEOUT_RE = re.compile(r"\[STORY\] WHITEOUT recovery #(\d+) at \((-?\d+), (-?\d+)\)")
DERAIL_RE = re.compile(r"\[STORY\] DERAIL #(\d+): (.*)")
GYM_TM_RE = re.compile(r"\[GYM_TM\] boss=(.+?) losses=(\d+) .*?\bwall=(\S+) outcome=('[^']*'|\S+)")


class Refused(Exception):
    """A guard refused the run (exit 2): nothing unsafe was written."""


class BadInput(Exception):
    """An input the run cannot read (exit 5, EXIT_CRASH), named with its line: never a disagreement's exit 1."""


# ============================================================================================ boss names

def boss_tables(decomp: Path | None = None) -> tuple[dict[int, str], dict[int, str], str]:
    """(boss id -> runs.jsonl key, every opponents.h id -> its TRAINER_ name, where they came from).

    Reuses `tools/decomp_lookup.py` (its pin check, CRLF-tolerant reader and `trainer()` lookup) on the PINNED clone.
    Without a pinned clone: the fallback table and an empty name map, and the returned label says why. With one whose
    ids differ from the fallback: Refused (the tuner's rows are keyed by the fallback's ids)."""
    sys.path.insert(0, str(REPO / "tools"))
    try:
        import decomp_lookup as dl  # noqa: PLC0415
        root = dl.decomp_root(decomp)
    except Exception as exc:  # noqa: BLE001 - no clone, a wrong commit, or no pin: the fallback, said out loud
        return dict(BOSS_IDS_FALLBACK), {}, f"fallback table (decomp not used: {str(exc).splitlines()[0][:160]})"
    ids: dict[int, str] = {}
    for key, const in BOSS_DECOMP.items():
        info = dl.trainer(root, const)
        if info is None:
            raise Refused(f"{const} is not defined in the pinned decomp's opponents.h")
        ids[info["id"]] = key
    if ids != BOSS_IDS_FALLBACK:
        raise Refused(f"the pinned decomp's boss ids {sorted(ids.items())} differ from the ids runs.jsonl uses "
                      f"{sorted(BOSS_IDS_FALLBACK.items())}")
    names: dict[int, str] = {}
    for ln in dl.read_lines(root / "include/constants/opponents.h"):
        m = re.match(r"^\s*#define\s+(TRAINER_\w+)\s+(\d+)\b", ln)
        if m:
            names.setdefault(int(m.group(2)), m.group(1))
    return ids, names, f"pinned decomp {dl.read_pin()[:8]} include/constants/opponents.h"


# ============================================================================================ small parsers

def parse_party(text: str | None) -> list[dict] | None:
    """`"['Combusken:L17', ...]"` -> [{species, level}]. `ast.literal_eval` first; a value cut at 200 characters by
    `scoring.py` falls back to the whole `'X:Ln'` items it still holds."""
    if text is None:
        return None
    try:
        items = ast.literal_eval(text)
        out = []
        for it in items:
            sp, _, lv = str(it).rpartition(":L")
            out.append({"species": sp, "level": int(lv)})
        return out
    except (ValueError, SyntaxError, TypeError):
        return [{"species": s, "level": int(lv)} for s, lv in MON_RE.findall(text)]


def parse_stock(text: str | None) -> dict[str, int] | None:
    """`Revive:3,Full_Heal:8` -> {"Revive": 3, "Full_Heal": 8}; `-` -> {}; absent -> None."""
    if text is None:
        return None
    if text == "-":
        return {}
    out = {}
    for part in text.split(","):
        name, _, n = part.rpartition(":")
        if name and n.isdigit():
            out[name] = int(n)
    return out


def _kv(line: str) -> dict[str, str]:
    return dict(KV_RE.findall(line))


def _maybe_int(v: str | None) -> int | None:
    return int(v) if v is not None and v.lstrip("-").isdigit() else None


def _bool(v: str | None) -> bool | None:
    return {"True": True, "False": False}.get(v or "")


# ============================================================================================ tier B: one log

def parse_log_stream(lines, boss_ids: dict[int, str], opp_names: dict[int, str]) -> dict:
    """Tier B of one run from an iterable of raw byte lines (a file or a zip member, streamed: never held whole).

    Pure reading; never raises on an odd line. Mirrors `scoring.py`'s start rule (see the module docstring) so the
    per-boss `won`/`losses` can be compared with `runs.jsonl`."""
    tags: collections.Counter = collections.Counter()
    n_lines = untagged = trainer_starts_total = pre_start_trainer = 0
    started, starter, start_frame = False, None, None
    last_hb: tuple[int, list[dict] | None] | None = None
    cur: dict | None = None
    fights: list[dict] = []
    badges: list[dict] = []
    whiteouts: list[dict] = []
    derails: collections.Counter = collections.Counter()
    derail_first: dict[str, int] = {}
    derail_max = 0
    gym_tm: list[dict] = []
    won_frame: dict[str, int] = {}
    max_frame = 0

    def boss_key(opp: int | None) -> str | None:
        return boss_ids.get(opp) if opp is not None else None

    def close(fight: dict) -> None:
        fight["moves_used"] = sorted(fight.pop("_moves"))
        fight["use_item_turns"] = len(fight.pop("_items"))
        before, after = fight.get("heal_stock_before"), fight.get("heal_stock_after")
        fight["heal_spent"] = ({k: before[k] - after.get(k, 0) for k in sorted(before) if before[k] > after.get(k, 0)}
                               if before is not None and after is not None else None)
        if fight["boss"] is not None or fight["class"] in BOSS_CLASSES:
            fights.append(fight)

    def new_fight(opp: int | None, frame: int, kv: dict, cls: str | None) -> dict:
        return {"opp": opp, "opp_name": opp_names.get(opp) if opp is not None else None, "boss": boss_key(opp),
                "class": cls, "start_frame": None, "end_frame": None, "lvl_last": _maybe_int(kv.get("lvl_last")),
                "first": _bool(kv.get("first")), "double": _bool(kv.get("double")), "res": None,
                "incomplete": False, "orphan_end": False, "money_before": None, "money_after": None,
                "heal_stock_before": None, "heal_stock_after": None, "enemy_alive": _maybe_int(kv.get("enemy_alive")),
                "party": None, "party_age_frames": None, "_moves": set(), "_items": set()}

    for raw in lines:
        n_lines += 1
        if not started and b"choosing" in raw:
            s = STARTER_RE.search(raw.decode("utf-8", "replace"))
            if s:
                started, starter = True, s.group(1)
                fm = re.match(rb"^f(\d+) ", raw)
                start_frame = int(fm.group(1)) if fm else None
        m = FRAME_TAG_RE.match(raw)
        if m is None:
            untagged += 1
            continue
        frame, tag = int(m.group(1)), m.group(2).decode("ascii")
        max_frame = max(max_frame, frame)
        tags[tag] += 1
        if tag == "DMGAUDIT":
            continue
        if tag == "TRAINER" and raw.startswith(b" start", m.end()):
            trainer_starts_total += 1
        if not started:
            if tag == "TRAINER":
                pre_start_trainer += 1
            continue
        if tag == "BATTLE":
            if cur is not None and b"[TURN " in raw:
                t = TURN_RE.search(raw.decode("utf-8", "replace"))
                if t:
                    if t.group(4) is not None:
                        cur["_moves"].add(t.group(4).strip())
                    else:
                        cur["_items"].add((int(t.group(1)), t.group(2)))
            continue
        if tag not in PARSED_TAGS:
            continue
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if tag == "hb":
            p = HB_PARTY_RE.search(line)
            if p:
                last_hb = (frame, parse_party(p.group(1)))
        elif tag == "TRAINER":
            body = line[m.end():].lstrip()
            kv = _kv(body)
            opp = _maybe_int(kv.get("opp"))
            c = CLASS_RE.search(body)
            cls = c.group(1) if c else None
            if body.startswith("start"):
                if cur is not None:
                    cur["incomplete"] = True
                    close(cur)
                cur = new_fight(opp, frame, kv, cls)
                cur["start_frame"] = frame
                cur["money_before"] = _maybe_int(kv.get("money"))
                cur["heal_stock_before"] = parse_stock(kv.get("heal_stock"))
                if last_hb is not None:
                    cur["party"], cur["party_age_frames"] = last_hb[1], frame - last_hb[0]
            elif body.startswith("end"):
                if cur is None or cur["opp"] != opp:
                    if cur is not None:
                        cur["incomplete"] = True
                        close(cur)
                    cur = new_fight(opp, frame, kv, cls)
                    cur["orphan_end"] = True
                cur["end_frame"], cur["res"] = frame, kv.get("res")
                mp = MONEY_PAIR_RE.search(body)
                if mp:
                    if cur["money_before"] is None:
                        cur["money_before"] = int(mp.group(1))
                    cur["money_after"] = int(mp.group(2))
                cur["heal_stock_after"] = parse_stock(kv.get("heal_stock"))
                if cur["boss"] and cur["res"] == "Won":
                    won_frame.setdefault(cur["boss"], frame)
                close(cur)
                cur = None
        elif tag == "BADGE":
            b = BADGE_RE.search(line)
            if b:
                badges.append({"n": int(b.group(1)), "frame": frame, "party_n": int(b.group(2))})
        elif tag == "STORY":
            w = WHITEOUT_RE.search(line)
            if w:
                nxt = next((k for k in BOSS_ORDER if k not in won_frame), None)
                whiteouts.append({"frame": frame, "at": [int(w.group(2)), int(w.group(3))], "boss_next": nxt})
                continue
            d = DERAIL_RE.search(line)
            if d:
                derail_max = max(derail_max, int(d.group(1)))
                text = d.group(2)[:200]
                derails[text] += 1
                derail_first.setdefault(text, frame)
        elif tag == "GYM_TM":
            g = GYM_TM_RE.search(line)
            if g and len(gym_tm) < 20:
                gym_tm.append({"frame": frame, "boss": g.group(1), "losses": int(g.group(2)), "wall": g.group(3),
                               "outcome": g.group(4).strip("'")})
    if cur is not None:  # the log ends inside a fight: never a result (E1, E3b)
        cur["incomplete"], cur["res"] = True, None
        close(cur)

    bosses: dict[str, dict] = {}
    for f in fights:
        if f["boss"] is None:
            continue
        b = bosses.setdefault(f["boss"], {"won": False, "losses": 0, "fights": 0, "incomplete": 0})
        b["fights"] += 1
        if f["incomplete"]:
            b["incomplete"] += 1
        elif f["res"] == "Won":
            b["won"] = True
        else:
            b["losses"] += 1
    numbers: collections.Counter = collections.Counter()
    for f in fights:
        key = f["boss"] or f["opp_name"] or str(f["opp"])
        numbers[key] += 1
        f["fight_no"] = numbers[key]
    top_derails = sorted(derails, key=lambda t: (-derails[t], derail_first[t]))[:3]
    return {
        "started": started, "starter": starter, "start_frame": start_frame, "lines": n_lines, "frames_max": max_frame,
        "trainer_starts": trainer_starts_total, "pre_start_trainer_lines": pre_start_trainer,
        "parse_suspect": n_lines > SUSPECT_MIN_LINES and trainer_starts_total == 0,
        "unknown_tags": dict(sorted((t, n) for t, n in tags.items() if t not in KNOWN_TAGS)),
        "untagged_lines": untagged, "fights": fights, "bosses": dict(sorted(bosses.items())),
        "badges": badges, "whiteouts": whiteouts, "derails_n": derail_max,
        "derail_texts": [{"text": t, "count": derails[t]} for t in top_derails], "gym_tm": gym_tm,
    }


# ============================================================================================ raw sources

class CycleRaw:
    """The raw files of ONE cycle, from its folder or, once O3 archived it, from `runs/<tag>/raw.zip` (a member read
    with `ZipFile.open`, streamed). A file is looked for in the folder first and then in the zip. Read-only."""

    def __init__(self, runs_dir: Path, profiles_dir: Path, tag: str):
        self.tag, self.cdir, self.profiles_dir = tag, runs_dir / tag, profiles_dir
        self._zip: zipfile.ZipFile | None = None
        self._names: set[str] | None = None
        zpath = self.cdir / "raw.zip"
        if zpath.is_file():
            try:
                self._zip = zipfile.ZipFile(zpath)
                self._names = set(self._zip.namelist())
            except (OSError, zipfile.BadZipFile) as exc:
                self.zip_error = f"raw.zip unreadable: {exc!r}"[:160]
        self._arms: dict | None | bool = False

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()

    def archived_since_open(self) -> bool:
        """True when `raw.zip` is on disk but this object did not load it: O3 archived the cycle after it was opened,
        and it may have deleted folder files (a log, a lane listing, a profile) in the middle of a record."""
        return self._zip is None and (self.cdir / "raw.zip").is_file()

    def settled(self) -> bool:
        """The cycle is in its FINAL archived form: `raw.zip` loaded and the batch folder gone. Only then is a member
        missing from it missing for good (O3 zips EVERY original before it deletes any)."""
        return self._zip is not None and not (self.cdir / "batch").exists()

    def _folder_or_zip(self, folder_path: Path, member: str):
        """An open binary stream of the file, or None."""
        if folder_path.is_file():
            return open(folder_path, "rb")
        if self._zip is not None and member in (self._names or ()):
            return self._zip.open(member)
        return None

    def open_log(self, lane: int, log: str):
        rel = f"batch/L{lane:02d}/debug-logs/{log}"
        return self._folder_or_zip(self.cdir / rel, rel)

    def lane_logs(self, lane: int) -> list[str]:
        """The lane's log names, sorted (the order `scoring.parse_batch` gives runs in a lane)."""
        names: set[str] = set()
        d = self.cdir / "batch" / f"L{lane:02d}" / "debug-logs"
        if d.is_dir():
            names |= {p.name for p in d.glob("*.log")}
        prefix = f"batch/L{lane:02d}/debug-logs/"
        for n in self._names or ():
            if n.startswith(prefix) and n.endswith(".log") and "/" not in n[len(prefix):]:
                names.add(n[len(prefix):])
        return sorted(names)

    def arms(self) -> dict | None:
        if self._arms is False:
            fh = self._folder_or_zip(self.cdir / "batch" / "ARMS.json", "batch/ARMS.json")
            try:
                self._arms = json.loads(fh.read().decode("utf-8")) if fh else None
            except ValueError:
                self._arms = None
            finally:
                if fh:
                    fh.close()
        return self._arms  # type: ignore[return-value]

    def badge_log(self, profile: str) -> list | None:
        """The lane profile's badge-log.json: from the live profile folder, else the zip's STORED `profiles/` member."""
        fh = self._folder_or_zip(self.profiles_dir / profile / "badge-log.json", f"profiles/{profile}/badge-log.json")
        if fh is None:
            return None
        try:
            data = json.loads(fh.read().decode("utf-8"))
            return data if isinstance(data, list) else None
        except ValueError:
            return None
        finally:
            fh.close()


def join_badge_log(entries: list | None, run_index: int, tier_b: dict | None) -> tuple[list | None, str]:
    """The badge-log entries of THIS run, or None, and why. Joined only when every entry with `run_index` (the run's
    1-based position among its lane's sorted logs) has a frame equal to this run's `[BADGE] n=<k>` frame for its
    BADGE0k flag (identity, not position alone). Entries before the run's `Story: choosing` frame are a stale save's
    boot (the previous game's badges, re-read at f301) and are dropped, counted in the reason."""
    if entries is None:
        return None, "absent"
    if tier_b is None:
        return None, "unverified (no raw log to match frames against)"
    mine = [e for e in entries if isinstance(e, dict) and e.get("run_index") == run_index]
    frames = {b["n"]: b["frame"] for b in tier_b["badges"]}
    start = tier_b.get("start_frame")
    # A lane that boots the previous game's save writes that save's badges at the boot frame (measured: eight entries
    # at f301, ai0034 lane 2), BEFORE this run's `Story: choosing` line: they are not this run's badges. A log that
    # never reached `Story: choosing` (measured: ai0035 lane 9) has no badge of its own, so every entry is stale.
    stale = [e for e in mine if not tier_b["started"] or start is None or
             (isinstance(e.get("frame"), int) and e["frame"] < start)]
    mine = [e for e in mine if e not in stale]
    if not mine and frames:
        return None, f"no entries for this run, but its log has {len(frames)} [BADGE] lines"
    out = []
    for e in mine:
        fm = re.fullmatch(r"BADGE0(\d)_GET", str(e.get("flag", "")))
        n = int(fm.group(1)) if fm else None
        if n is None or frames.get(n) != e.get("frame"):
            return None, f"mismatch: {e.get('flag')} frame {e.get('frame')} vs log {frames.get(n)}"
        out.append({"n": n, "frame": e["frame"], "leader": e.get("leader"),
                    "team": [{"species": t.get("species"), "level": t.get("level"), "moves": t.get("moves"),
                              "item": t.get("item")} for t in e.get("team", []) if isinstance(t, dict)]})
    return out, "ok" + (f" ({len(stale)} stale-boot entries before the run's start dropped)" if stale else "")


# ============================================================================================ one record

def tier_a(row: dict) -> dict | None:
    bl = row.get("boss_log")
    if not isinstance(bl, dict):
        return None
    win_frames = {}
    for item in row.get("milestones") or []:
        if isinstance(item, list) and len(item) == 2:
            win_frames.setdefault(item[0], item[1])
    out = {}
    for k in sorted(bl):
        b = bl[k]
        out[k] = {"won": bool(b.get("won")), "losses": int(b.get("losses") or 0),
                  "party_first_loss": parse_party(b.get("party_first_loss")), "party_win": parse_party(b.get("party_win")),
                  "win_frame": win_frames.get(k)}
    return out


def row_key(row: dict) -> str:
    return f"{row.get('source')}/{row.get('lane')}/{row.get('log')}"


ROW_FIELDS = ("source", "lane", "log", "batch", "code_commit", "arm", "genome_id", "lane_starter", "starter", "usable",
              "complete", "champion", "progress", "frames", "wall", "derail_walls", "money_last", "catches", "dex_owned")


def build_record(row: dict, raw: CycleRaw | None, boss_ids: dict[int, str], opp_names: dict[int, str]) -> dict:
    rec = {"key": row_key(row), **{k: row.get(k) for k in ROW_FIELDS}}
    ta = tier_a(row)
    rec["tier_a"], rec["tier_a_missing"] = ta, (None if ta is not None else "no boss_log in the runs.jsonl row")
    tb, raw_missing = None, None
    lane, log = row.get("lane"), row.get("log")
    if raw is None:
        raw_missing = "no raw cycle folder or raw.zip"
    elif not isinstance(lane, int) or not log:
        raw_missing = "the row has no lane or log name"
    else:
        try:
            fh = raw.open_log(lane, log)
            if fh is None:
                raw_missing = "log not in the cycle folder or raw.zip"
            else:
                with fh:  # a file or a ZipExtFile: both iterate line by line, streamed
                    tb = parse_log_stream(fh, boss_ids, opp_names)
        except (OSError, zipfile.BadZipFile, EOFError, zlib.error) as exc:  # pruned mid-read, or a corrupt member
            tb, raw_missing = None, f"read failed: {exc!r}"[:200]  # (a bad deflate stream raises zlib.error)
    rec["tier_b"], rec["raw_missing"] = tb, raw_missing
    rec["tier"] = {(True, True): "A+B", (True, False): "A", (False, True): "B", (False, False): "none"}[
        (ta is not None, tb is not None)]

    badge, why = None, "no raw cycle"
    if raw is not None and isinstance(lane, int):
        arms = raw.arms()
        lanes = (arms or {}).get("lanes") or []
        profile = lanes[lane - 1].get("profile") if 0 < lane <= len(lanes) and isinstance(lanes[lane - 1], dict) else None
        logs = raw.lane_logs(lane)
        if profile is None:
            why = "no profile name in ARMS.json"
        elif log not in logs:
            why = "the log is not among the lane's logs"
        else:
            badge, why = join_badge_log(raw.badge_log(profile), logs.index(log) + 1, tb)
    rec["badge_log"], rec["badge_log_join"] = badge, why

    agrees, disagreements, incomplete_only = {}, [], []
    if ta is not None and tb is not None:
        for k in sorted(set(ta) | set(tb["bosses"])):
            a, b = ta.get(k), tb["bosses"].get(k)
            if a is None and b is not None and not b["won"] and b["losses"] == 0:
                # Adjudicated 2026-10-21 (3 of 5,959 bosses in the first full pass): the log STARTED this fight and
                # never ended it (a crash or the time limit). scoring.py makes a boss_log entry only on an end line,
                # so its absence there is the same fact; listed, not a disagreement.
                incomplete_only.append(k)
                continue
            ok = a is not None and b is not None and a["won"] == b["won"] and a["losses"] == b["losses"]
            agrees[k] = ok
            if not ok:
                disagreements.append({"boss": k, "runs_jsonl": None if a is None else {"won": a["won"],
                                                                                        "losses": a["losses"]},
                                      "log": None if b is None else {"won": b["won"], "losses": b["losses"],
                                                                     "incomplete": b["incomplete"]}})
    rec["agrees_with_runs_jsonl"], rec["disagreements"] = agrees, disagreements
    rec["bosses_incomplete_only"] = incomplete_only
    return rec


# ============================================================================================ store, cursor, guards

def _canon(p: Path | str) -> str:
    """The path as the filesystem resolves it: `realpath` follows junctions and symlinks and expands 8.3 short names
    (`C:\\REMOTE~1\\PO7209~1` is the clone), `normcase` folds case and slashes. `realpath` KEEPS a `\\\\?\\` prefix it was
    given, so it is stripped here, or `\\\\?\\C:\\...` would never compare inside `C:\\...` (measured 2026-10-21)."""
    try:
        r = os.path.realpath(p)
    except (OSError, ValueError):
        r = os.path.abspath(p)
    if r.startswith("\\\\?\\UNC\\"):
        r = "\\\\" + r[8:]
    elif r.startswith("\\\\?\\"):
        r = r[4:]
    return os.path.normcase(r)


def _file_id(p: Path | str) -> tuple[int, int] | None:
    try:
        st = os.stat(p)
    except (OSError, ValueError):
        return None
    return (st.st_dev, st.st_ino) if st.st_ino else None


def _chain_ids(path: Path | str) -> set[tuple[int, int]]:
    """The identities (volume, file id) of `path`'s nearest EXISTING ancestor and all of ITS ancestors, walked on the
    resolved path (a junction's lexical parent is not its target's parent). A folder not yet created is created inside
    that ancestor, so this chain is where a write would land."""
    q = Path(_canon(path))
    while not q.exists() and q.parent != q:
        q = q.parent
    return {i for i in map(_file_id, [q, *q.parents]) if i is not None}


def _inside_by_path(path: Path | str, root: Path | str) -> bool:
    try:
        return Path(_canon(path)).is_relative_to(Path(_canon(root)))
    except ValueError:
        return False


def _inside_by_identity(path: Path | str, root: Path | str) -> bool:
    rid = _file_id(root)
    return rid is not None and rid in _chain_ids(path)


def _inside(path: Path | str, root: Path | str) -> bool:
    """`path` is `root` or below it, by EITHER of two checks: the resolved spellings (`_canon`), or file identity,
    which also sees a spelling `realpath` does not rewrite (a UNC admin share `\\\\localhost\\C$\\...` reaches the same
    folder; measured 2026-10-21: same volume and file id, while `realpath` keeps the UNC form)."""
    return _inside_by_path(path, root) or _inside_by_identity(path, root)


def refuse_protected_write(path: Path, repo: Path, clone: Path, allow_digest_scope: bool = False,
                           read_roots: tuple[Path, ...] = ()) -> None:
    """THE WRITE GUARD. Refuse a write into the clone (read-only: a live batch runs there), into the raw-data folders
    this run READS (`read_roots`), and, unless this is the interactive `--priors` call, into the AI's digest scope
    (`ai_player/`):
    a routine run there would change the code-under-test tree in the middle of a graded sweep (E10).

    The DEFAULT clone and THIS checkout's `ai_player/` are always protected as well, whatever `--clone` and `--repo`
    say: those arguments choose what to read, and pointing either one elsewhere must not switch the guard off (review
    2026-10-21). `REPO` and `DEFAULT_CLONE` are read at call time, so a test can point them into a scratch tree."""
    for root in dict.fromkeys([clone, DEFAULT_CLONE, *read_roots]):
        if _inside(path, root):
            raise Refused(f"{path} is inside {root}, which this run must only read (the learner clone is read-only)")
    if not allow_digest_scope:
        for base in dict.fromkeys([repo, REPO]):
            for rel in DIGEST_SCOPE_REL:
                if _inside(path, base / rel):
                    raise Refused(f"{path} is inside the AI's digest scope {base / rel}: only an interactive --priors "
                                  f"call may write there, between graded rounds")


def _lock_byte(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
    else:  # pragma: no cover
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_byte(fd: int) -> None:
    if os.name == "nt":
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:  # pragma: no cover
        fcntl.flock(fd, fcntl.LOCK_UN)


class _OsMutex:
    """An OS byte-range lock on `MUTEX_FILE`, held only while a `StoreLock` is being TAKEN. WHY: with no mutex, two
    runs that both see a stale `.lock` can each retire it, and the later retire then removes the EARLIER run's fresh
    lock (review 2026-10-21: both acquired). Serialising the take makes "is it stale?" and "retire it" one step. The
    OS drops the lock when its process dies, so this mutex can never go stale itself."""

    def __init__(self, path: Path):
        self.path = path
        self.fd: int | None = None

    def __enter__(self) -> "_OsMutex":
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT)
        deadline = time.monotonic() + MUTEX_WAIT_S
        while True:
            try:
                _lock_byte(fd)
                self.fd = fd
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise Refused(f"{self.path} stayed locked for {MUTEX_WAIT_S:.0f} s: another extractor is "
                                  f"taking the store lock") from None
                time.sleep(0.05)

    def __exit__(self, *exc) -> None:
        if self.fd is not None:
            try:
                _unlock_byte(self.fd)
            finally:
                os.close(self.fd)
                self.fd = None


class StoreLock:
    """One extractor at a time per store (the O1 task and a session must not both append). `.lock` is created with
    O_EXCL and holds a unique token; one older than LOCK_STALE_S is a crashed run's. Taking it happens under
    `_OsMutex`; a stale lock is retired by `os.replace` to a unique name and checked to BE the stale lock that was read
    (its token), so a fresh lock is never removed. `create=False` (a read-only `--priors` run) refuses a missing store
    instead of creating it. On exit a run removes `.lock` only if it still holds ITS token."""

    def __init__(self, store: Path, create: bool = True):
        self.store, self.create = store, create
        self.path = store / LOCK_FILE
        self.token = f"{os.getpid()} {time.time():.0f} {uuid.uuid4().hex}".encode()

    def __enter__(self) -> "StoreLock":
        if not self.store.is_dir():
            if not self.create:
                raise Refused(f"the store {self.store} does not exist: run --full or --incremental first")
            self.store.mkdir(parents=True, exist_ok=True)
        with _OsMutex(self.store / MUTEX_FILE):
            for _ in range(3):
                try:
                    fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                except FileExistsError:
                    self._retire_if_stale()
                    continue
                try:
                    os.write(fd, self.token)
                finally:
                    os.close(fd)
                return self
        raise Refused(f"could not take {self.path}")

    def _retire_if_stale(self) -> None:
        try:
            seen = self.path.read_bytes()
            age = time.time() - self.path.stat().st_mtime
        except FileNotFoundError:
            return  # its owner released it: take it on the next try
        if age < LOCK_STALE_S:
            raise Refused(f"{self.path} is held ({age:.0f} s old): another extractor is running")
        aside = self.path.with_name(f"{LOCK_FILE}.stale.{uuid.uuid4().hex}")
        try:
            os.replace(self.path, aside)
        except FileNotFoundError:
            return
        if aside.read_bytes() != seen:
            # Not the lock judged stale: someone's FRESH lock was moved. Put it back (never over a new one) and stop.
            try:
                os.rename(aside, self.path)
            except OSError:
                pass
            raise Refused(f"{self.path} changed while being retired: another extractor took it")
        aside.unlink(missing_ok=True)

    def __exit__(self, *exc) -> None:
        try:
            mine = self.path.read_bytes() == self.token
        except OSError:
            mine = False
        if mine:
            self.path.unlink(missing_ok=True)


def _dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def header(boss_source: str) -> dict:
    return {"_header": {"schema": SCHEMA, "what": "one record per bot-tuner game (spec S3-3 A6); bot corpus, not the "
                        "AI's play", "key": "source/lane/log", "boss_ids_from": boss_source, "limits": LIMITS}}


def read_store(store: Path) -> tuple[list[dict], set[str]]:
    """(records, their keys). Refused on a torn or unparsable line: the store is append-only and is never repaired
    by rewriting it."""
    path = store / STORE_FILE
    if not path.exists():
        return [], set()
    recs = []
    with open(path, "rb") as fh:
        for i, raw in enumerate(fh, 1):
            if not raw.endswith(b"\n"):
                raise Refused(f"{path} line {i} is torn (no newline): an interrupted append; inspect it by hand")
            try:
                obj = json.loads(raw)
            except ValueError as exc:
                raise Refused(f"{path} line {i} is not JSON ({exc})") from exc
            if "_header" not in obj:
                recs.append(obj)
    return recs, {r["key"] for r in recs}


def read_cursor(store: Path) -> set[str] | None:
    path = store / CURSOR_FILE
    if not path.exists():
        return None
    try:
        return set(json.loads(path.read_text(encoding="utf-8"))["extracted"])
    except (ValueError, KeyError, TypeError) as exc:
        raise Refused(f"{path} cannot be read ({exc})") from exc


def write_cursor(store: Path, keys: set[str]) -> None:
    tmp = store / (CURSOR_FILE + ".tmp")
    tmp.write_text(json.dumps({"schema": SCHEMA, "extracted": sorted(keys)}, indent=0), encoding="utf-8")
    os.replace(tmp, store / CURSOR_FILE)


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, "rb") as fh:
        for i, raw in enumerate(fh, 1):
            if raw.strip() and raw.endswith(b"\n"):  # a torn last line (the tuner appending right now) is skipped
                try:
                    rows.append(json.loads(raw))
                except ValueError as exc:
                    raise BadInput(f"{path} line {i} is not JSON ({exc})") from exc
    return rows


def _open_cycle(runs_dir: Path, profiles_dir: Path, src: str) -> CycleRaw | None:
    cdir = runs_dir / src
    return CycleRaw(runs_dir, profiles_dir, src) if (cdir / "batch").is_dir() or (cdir / "raw.zip").is_file() else None


#: `raw_missing` texts of `build_record` that can be a race with O3 (the log moved into raw.zip, or its folder file was
#: deleted mid-read), as opposed to a row with no lane/log or a cycle with no raw data at all.
RACE_MISSING = ("log not in the cycle folder or raw.zip", "read failed:")


def extract(rows: list[dict], skip: set[str], runs_dir: Path, profiles_dir: Path, boss_ids: dict[int, str],
            opp_names: dict[int, str]) -> tuple[list[dict], list[tuple[str, str]]]:
    """(a record for every row whose key is not in `skip`, in `rows` order; the DEFERRED (key, why)), opening each
    cycle's raw files once. See the module docstring's O3 RACE: a record built while O3 archived its cycle is rebuilt
    on a fresh open, and one whose tier B still fails in a cycle that is not in its final archived form is deferred."""
    todo = [r for r in rows if row_key(r) not in skip]
    caches: dict[str, CycleRaw | None] = {}
    out: list[dict] = []
    deferred: list[tuple[str, str]] = []
    try:
        for row in todo:
            src = str(row.get("source"))
            if src not in caches:
                caches[src] = _open_cycle(runs_dir, profiles_dir, src)
            raw = caches[src]
            rec = build_record(row, raw, boss_ids, opp_names)
            if raw is not None and (str(rec["raw_missing"]).startswith(RACE_MISSING) or raw.archived_since_open()):
                raw.close()
                raw = caches[src] = _open_cycle(runs_dir, profiles_dir, src)
                rec = build_record(row, raw, boss_ids, opp_names)
                missing = str(rec["raw_missing"])
                # Only an archive in its final form proves a MISSING member is gone for good. A failed READ is never
                # proof: a sharing violation passes, and a corrupt member of the only copy should stay loud.
                if raw is not None and (missing.startswith(RACE_MISSING[1]) or
                                        (missing.startswith(RACE_MISSING[0]) and not raw.settled())):
                    deferred.append((rec["key"], missing))
                    continue
            out.append(rec)
    finally:
        for c in caches.values():
            if c is not None:
                c.close()
    return out, deferred


def run_extract(mode: str, runs_jsonl: Path, runs_dir: Path, profiles_dir: Path, store: Path, repo: Path, clone: Path,
                decomp: Path | None = None) -> tuple[int, dict]:
    """`--full` (an EMPTY store only) or `--incremental`. Returns (exit code, summary)."""
    t0 = time.perf_counter()
    # The folders of raw data it reads. Not runs.jsonl's folder: a copy of runs.jsonl at a checkout's root would make
    # that root a "read tree" and refuse the default store inside it (the clone itself is guarded as the clone).
    reads = (runs_dir, profiles_dir)
    for target in (store, store / STORE_FILE, store / CURSOR_FILE, store / (CURSOR_FILE + ".tmp"), store / LOCK_FILE,
                   store / MUTEX_FILE):  # every path this run writes (a planted symlink at any of them is resolved)
        refuse_protected_write(target, repo, clone, read_roots=reads)
    boss_ids, opp_names, boss_source = boss_tables(decomp)
    with StoreLock(store):
        recs, have = read_store(store)
        cursor = read_cursor(store)
        if mode == "full" and (recs or cursor):
            raise Refused(f"--full needs an empty store and {store} holds {len(recs)} records: the store is the ONLY "
                          f"copy of tier-B data whose raw logs are gone; use --incremental (or a new --store)")
        if cursor is not None and not cursor <= have:
            raise Refused(f"{store / CURSOR_FILE} lists {len(cursor - have)} keys that are not in the store")
        rows = load_rows(runs_jsonl)
        new, deferred = extract(rows, have, runs_dir, profiles_dir, boss_ids, opp_names)
        path = store / STORE_FILE
        empty = not path.exists() or path.stat().st_size == 0
        with open(path, "ab") as fh:
            if empty:
                fh.write((_dumps(header(boss_source)) + "\n").encode("utf-8"))
            for r in new:
                fh.write((_dumps(r) + "\n").encode("utf-8"))
            fh.flush()
            os.fsync(fh.fileno())
        write_cursor(store, have | {r["key"] for r in new})
    tiers = collections.Counter(r["tier"] for r in new)
    dis = [(r["key"], d) for r in new for d in r["disagreements"]]
    summary = {"mode": mode, "rows": len(rows), "already": len(have), "new": len(new), "tiers": dict(tiers),
               "no_boss_log": [r["key"] for r in new if r["tier_a"] is None],
               "parse_suspect": [r["key"] for r in new if r["tier_b"] and r["tier_b"]["parse_suspect"]],
               "badge_join": dict(collections.Counter(r["badge_log_join"].split(":")[0].split(" (")[0] for r in new)),
               "bosses_compared": sum(len(r["agrees_with_runs_jsonl"]) for r in new),
               "disagreements": dis, "deferred": deferred, "boss_ids_from": boss_source,
               "seconds": round(time.perf_counter() - t0, 1)}
    return (EXIT_DISAGREE if dis else EXIT_DEFERRED if deferred else EXIT_OK), summary


# ============================================================================================ priors

def _q(values: list[float]) -> dict | None:
    """min, p10, p50, p90, max, mean and n of `values` (nearest-rank quantiles; deterministic)."""
    if not values:
        return None
    v = sorted(values)

    def at(p: float) -> float:
        return v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))]
    return {"n": len(v), "min": v[0], "p10": at(0.1), "p50": at(0.5), "p90": at(0.9), "max": v[-1],
            "mean": round(sum(v) / len(v), 2)}


def _team_stats(party: list[dict] | None) -> tuple[int, float, int] | None:
    lv = [m["level"] for m in party or [] if isinstance(m.get("level"), int)]
    return (min(lv), sum(lv) / len(lv), max(lv)) if lv else None


def _levels(parties: list[list[dict] | None]) -> dict:
    stats = [s for s in map(_team_stats, parties) if s]
    return {"team_min": _q([s[0] for s in stats]), "team_mean": _q([round(s[1], 2) for s in stats]),
            "team_max": _q([s[2] for s in stats])}


#: THE AI-FACING LABEL ALLOWLIST (USER RULING 40). A run's wall label reaches chapter_priors.json only if it is EXACTLY
#: one of these names; any other label is written as OTHER_LABEL and counted there. WHY an allowlist and not masks: the
#: masks it replaced matched exact-case single words and upper-case hex only, so 'boss wall: Mr. Mime', "Kingdra's",
#: 'kingdra', 'lead #3e751caf', 'x=12 y=7' and 'flag_badge07_get' all reached the AI-facing file (review 2026-10-21).
#: A fixed name cannot carry live state; `classify_wall`'s free-text fallback (the first 70 characters of any derail)
#: is exactly what must not pass. The names: `classify_wall`'s WALLS table and its "no derail recorded"
#: (`ai-agent/knowledge.py`, read 2026-10-21; the test fails if that table gains a name missing here); its
#: "boss wall: <name>" for the 13 bosses as the story bot names them in its loss message (`story_mode.py`, the
#: `{boss_name}: {losses} losses with no super-effective answer` line) and its default "this boss"; `scoring.py`'s
#: "CHAMPION"; and NO_WALL_LABEL, this file's own label for a row with no wall.
BOSS_DISPLAY = ("Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate & Liza", "Juan", "Sidney",
                "Phoebe", "Glacia", "Drake", "Wallace")
WALL_NAMES = ("E4 refused: League basket short", "E4 refused: team below level floor", "training ended below floor",
              "heal walk blocked", "unreachable target", "no derail recorded")
OTHER_LABEL, NO_WALL_LABEL = "<other>", "<no wall label>"
ALLOWED_LABELS = frozenset({*WALL_NAMES, "CHAMPION", NO_WALL_LABEL, "boss wall: this boss",
                            *(f"boss wall: {b}" for b in BOSS_DISPLAY)})


def priors_label(wall) -> str:
    """The label the AI-facing file may carry for a run's `wall`: the wall itself when allowlisted, else OTHER_LABEL."""
    if wall is None:
        return NO_WALL_LABEL
    return wall if isinstance(wall, str) and wall in ALLOWED_LABELS else OTHER_LABEL


#: THE E7 DENYLIST, the gate's second and INDEPENDENT layer (it never consults the allowlist, so one bug cannot open
#: both). Matched case-insensitively. A PID: eight hex digits standing alone, with or without `#` or `0x`. A position:
#: `(x, y)`, `[x, y]`, `x=`/`y=` with a number, `pos=`/`position:`/`coords=` with a number, `map=a,b`, `at (a,`.
#: A flag or var: `flag_`/`var_` in any case, or an ALL_CAPS_NAME (case-sensitive: the file's own keys are lower-case
#: snake_case, and the 13 boss keys are allowed as KEYS of the `bosses` block). Species: see `species_re`.
PID_RE = re.compile(r"(?i)(?:0x|(?<![0-9a-z]))[0-9a-f]{8}(?![0-9a-z])")
POS_RE = re.compile(r"(?i)\(\s*-?\d+\s*,\s*-?\d+\s*\)|\[\s*-?\d+\s*,\s*-?\d+\s*\]|(?<![0-9a-z])[xy]\s*[=:]\s*-?\d"
                    r"|\b(?:pos|position|coords?)\s*[=:]\s*[(\[]?\s*-?\d|\bmap\s*=\s*\d+\s*,\s*\d|\bat \(\s*-?\d+\s*,")
FLAGVAR_RE = re.compile(r"(?i)(?<![0-9a-z])(?:flag|var)_[0-9a-z_]")
CONST_RE = re.compile(r"\b[A-Z][A-Z0-9#]*(?:_[A-Z0-9#]+)+\b")


def _species_names(repo: Path) -> set[str]:
    try:
        d = json.loads((repo / "ai_player/knowledge/species.json").read_text(encoding="utf-8"))
        return set(d["species"])
    except (OSError, ValueError, KeyError):
        return set()


def species_re(species: set[str]) -> re.Pattern[str] | None:
    """One pattern for every species name, matched on CASEFOLDED text. Each name's letter-and-digit runs are joined by
    up to three other characters, so a name is matched as a phrase in any spelling: `Mr. Mime` / `mr mime`,
    `Farfetch'd` with either apostrophe (species.json holds the curly one), `Ho-Oh`, `Nidoran` for both symbols. Word
    boundaries on both ends; a possessive (`Kingdra's`), a `-type` suffix and an `s`/`es` plural still match."""
    alts = set()
    for name in species:
        toks = re.findall(r"[0-9a-z]+", name.casefold())
        if toks:
            alts.add(r"[^0-9a-z]{0,3}".join(map(re.escape, toks)))
    if not alts:
        return None
    return re.compile(r"(?<![0-9a-z])(?:" + "|".join(sorted(alts, key=lambda a: (-len(a), a))) +
                      r")(?:e?s)?(?![0-9a-z])")


def check_ai_facing(obj, species: set[str]) -> list[str]:
    """THE E7 GATE on an AI-facing file: [] or the problems. In every string value AND every dict key: no PID, no
    position, no flag- or var-shaped name (the 13 boss keys are allowed as KEYS of the `bosses` block), no species
    name (all as `PID_RE`, `POS_RE`, `FLAGVAR_RE`/`CONST_RE`, `species_re` define them); and every block of `bosses`
    and `runs` labelled `source: "bot corpus"`."""
    problems: list[str] = []
    allowed_keys = set(BOSS_ORDER)
    sp_re = species_re(species)

    def walk(x, path: str) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if not (path == "bosses" and k in allowed_keys):
                    check_text(str(k), f"{path}.<key {k}>")
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, str):
            check_text(x, path)

    def check_text(s: str, where: str) -> None:
        if PID_RE.search(s):
            problems.append(f"{where}: a PID in {s[:80]!r}")
        if POS_RE.search(s):
            problems.append(f"{where}: a position in {s[:80]!r}")
        if FLAGVAR_RE.search(s) or CONST_RE.search(s):
            problems.append(f"{where}: a flag- or var-shaped name in {s[:80]!r}")
        hit = sp_re.search(s.casefold()) if sp_re is not None else None
        if hit:
            problems.append(f"{where}: a species name {hit.group(0)!r} (species shares are the bot's style, withheld)")

    walk(obj, "")
    for block in ("bosses", "runs"):
        if not isinstance(obj, dict) or block not in obj:
            problems.append(f"no {block} block")
            continue
        if block == "bosses" and not isinstance(obj[block], dict):
            problems.append("bosses: not a block of bosses")
            continue
        items = obj[block].items() if block == "bosses" else [("runs", obj[block])]
        for name, b in items:
            if not isinstance(b, dict) or b.get("source") != CORPUS:
                problems.append(f"{block}.{name}: not labelled source {CORPUS!r}")
    return problems


def build_priors(recs: list[dict]) -> dict:
    """The AI-facing per-boss numbers (spec S3-3), from the store's records. Censoring as in the module docstring;
    every label through `priors_label` (the allowlist)."""
    bosses = {}
    usable = [r for r in recs if r.get("usable")]
    for k in BOSS_ORDER:
        resolved, censored, fails = [], 0, collections.Counter()
        for r in recs:
            a = (r.get("tier_a") or {}).get(k)
            if a is None:
                continue
            if a["won"] or (a["losses"] >= 1 and r.get("usable")):
                resolved.append((r, a))
            else:
                censored += 1  # fought, never won, the game cut by the time limit: not a failure
            if r.get("usable") and not a["won"]:
                fails[priors_label(r.get("wall"))] += 1
        first_party = [a["party_first_loss"] if a["losses"] else a["party_win"] for _, a in resolved]
        bands: dict[int, list[int]] = {}
        for (r, a), party in zip(resolved, first_party):
            s = _team_stats(party)
            if s:
                b = int(s[1] // 3) * 3
                bands.setdefault(b, [0, 0])
                bands[b][0] += 1
                bands[b][1] += 1 if (a["won"] and a["losses"] == 0) else 0
        tb_first = []
        whiteouts_before_win, items_turns, foe_top, heal_spent_n = [], [], [], []
        for r, a in resolved:
            tb = r.get("tier_b")
            if not tb:
                continue
            fs = [f for f in tb["fights"] if f["boss"] == k and not f["incomplete"]]
            if fs and fs[0]["money_before"] is not None:
                tb_first.append(fs[0]["money_before"])
            items_turns += [f["use_item_turns"] for f in fs]
            foe_top += [f["lvl_last"] for f in fs if f["lvl_last"] is not None]
            heal_spent_n += [sum(f["heal_spent"].values()) for f in fs if f["heal_spent"] is not None]
            if a["won"]:
                whiteouts_before_win.append(sum(1 for w in tb["whiteouts"] if w["boss_next"] == k))
        at_badge = []
        if k in LEADER_KEYS:
            n = LEADER_KEYS.index(k) + 1
            for r, a in resolved:
                for e in r.get("badge_log") or []:
                    if e["n"] == n:
                        at_badge.append(e["team"])
        wins_first = sum(1 for _, a in resolved if a["won"] and a["losses"] == 0)
        bosses[k] = {
            "source": CORPUS, "n_fought": len(resolved), "n_censored": censored,
            "first_try_wins": wins_first,
            "first_try_win_rate": round(wins_first / len(resolved), 4) if resolved else None,
            "losses_distribution": {str(n): c for n, c in sorted(collections.Counter(
                a["losses"] for _, a in resolved).items())},
            "party_size_first_attempt": {str(n): c for n, c in sorted(collections.Counter(
                len(p) for p in first_party if p).items())},
            "levels_at_first_loss": _levels([a["party_first_loss"] for _, a in resolved if a["losses"]]),
            "levels_at_win": _levels([a["party_win"] for _, a in resolved if a["won"]]),
            "levels_at_badge": _levels(at_badge) if k in LEADER_KEYS else None,
            "first_try_win_rate_by_team_mean_level": [
                {"band": f"{b}-{b + 2}", "n": v[0], "first_try_wins": v[1], "rate": round(v[1] / v[0], 4)}
                for b, v in sorted(bands.items())],
            "money_at_first_fight": _q(tb_first), "use_item_turns_per_fight": _q(items_turns),
            "heal_items_spent_per_fight": _q(heal_spent_n), "foe_top_level_logged": _q(foe_top),
            "whiteouts_before_win": _q(whiteouts_before_win),
            "failures": {"n": sum(fails.values()), "n_usable_rows_fought": sum(
                1 for r in usable if (r.get("tier_a") or {}).get(k)), "labels": dict(sorted(fails.items()))},
        }
    walls = collections.Counter(priors_label(r.get("wall")) for r in usable)
    return {
        "source": CORPUS, "schema": SCHEMA,
        "what": "per-boss numbers from the bot tuner's games: a PRIOR ON NEEDS for the AI player, never a policy or a "
                "style (USER RULING 35). Species shares are withheld (the bot's style); they stay in the git-ignored "
                "per-run store. Regenerated only by an interactive session between graded rounds (spec S3-3 E10).",
        "limits": LIMITS,
        "censoring": "boss stats use rows where the boss was won, or lost at least once in a usable game; failures "
                     "and wall labels use usable rows only; n_censored = fought, never won, game cut by the time limit",
        "inputs": {"records": len(recs), "usable": len(usable),
                   "tier_b_records": sum(1 for r in recs if r.get("tier_b")),
                   "badge_log_joined": sum(1 for r in recs if r.get("badge_log")),
                   "no_boss_log": sum(1 for r in recs if r.get("tier_a") is None)},
        "bosses": bosses,
        "runs": {"source": CORPUS, "n": len(recs), "n_usable": len(usable), "n_censored": len(recs) - len(usable),
                 "champions": sum(1 for r in usable if r.get("champion")),
                 "wall_labels": dict(sorted(walls.items(), key=lambda kv: (-kv[1], kv[0])))},
    }


def write_priors(store: Path, out: Path, repo: Path, clone: Path, force: bool = False) -> tuple[int, str]:
    """`--priors`: regenerate the AI-facing file from the store, only when there is none or the sample grew 10 %
    (or `force`). The E7 gate runs BEFORE the write; a file that fails it is never written (exit 3).

    The STORE is guarded too, before the lock touches it: taking the lock writes `.lock` files there, and a `--store`
    inside the clone or `ai_player/` used to get a folder and a lock created before the empty store was refused
    (review 2026-10-21). This run only READS the store, so a missing one is refused, never created."""
    for target in (store, store / LOCK_FILE, store / MUTEX_FILE):
        refuse_protected_write(target, repo, clone)  # no digest exemption: the store never belongs in ai_player/
    for target in (out, out.with_suffix(".json.tmp")):
        refuse_protected_write(target, repo, clone, allow_digest_scope=True)
    with StoreLock(store, create=False):  # never read a line the O1 task is appending
        recs, _ = read_store(store)
    if not recs:
        raise Refused(f"the store {store} is empty: run --full or --incremental first")
    if out.exists() and not force:
        try:
            old_n = json.loads(out.read_text(encoding="utf-8"))["inputs"]["records"]
        except (OSError, ValueError, KeyError, TypeError):
            old_n = 0
        if old_n and len(recs) < old_n * 1.1:
            return EXIT_OK, f"not regenerated: {len(recs)} records vs {old_n} in the file (< 10 % growth)"
    priors = build_priors(recs)
    problems = check_ai_facing(priors, _species_names(repo))
    if problems:
        return EXIT_GATE, "REFUSED by the privacy gate: " + "; ".join(problems[:5])
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(priors, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8",
                   newline="\n")
    os.replace(tmp, out)
    other = priors["runs"]["wall_labels"].get(OTHER_LABEL, 0)
    return EXIT_OK, (f"wrote {out} from {len(recs)} records; {other} usable runs' wall labels are outside the "
                     f"allowlist and counted as {OTHER_LABEL!r}")


# ============================================================================================ CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--incremental", action="store_true", help="append records for runs not yet in the store")
    mode.add_argument("--full", action="store_true", help="first build: extract every run into an EMPTY store")
    mode.add_argument("--priors", action="store_true", help="regenerate chapter_priors.json (interactive only)")
    mode.add_argument("--check-priors", type=Path, metavar="FILE", help="run the E7 privacy gate on FILE")
    ap.add_argument("--clone", type=Path, default=DEFAULT_CLONE)
    ap.add_argument("--runs-jsonl", type=Path)
    ap.add_argument("--runs-dir", type=Path)
    ap.add_argument("--profiles-dir", type=Path)
    ap.add_argument("--store", type=Path, default=DEFAULT_STORE)
    ap.add_argument("--repo", type=Path, default=REPO, help="the checkout whose ai_player/ is the digest scope")
    ap.add_argument("--priors-out", type=Path)
    ap.add_argument("--force-priors", action="store_true", help="regenerate even under 10 %% growth")
    ap.add_argument("--decomp", type=Path)
    args = ap.parse_args(argv)
    clone, repo = args.clone, args.repo
    try:
        if args.check_priors:
            try:
                obj = json.loads(args.check_priors.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                print(f"FAILED: {args.check_priors} cannot be read as JSON ({exc})")
                return EXIT_GATE
            problems = check_ai_facing(obj, _species_names(repo))
            for p in problems:
                print(f"FAIL {p}")
            print("PASS: no PID, position, flag/var name or species; every block labelled" if not problems else
                  f"FAILED: {len(problems)} problems")
            return EXIT_GATE if problems else EXIT_OK
        if args.priors:
            code, msg = write_priors(args.store, args.priors_out or repo / PRIORS_REL, repo, clone, args.force_priors)
            print(msg)
            return code
        code, s = run_extract("full" if args.full else "incremental",
                              args.runs_jsonl or clone / "ai-agent/data/runs.jsonl",
                              args.runs_dir or clone / "ai-agent/runs",
                              args.profiles_dir or clone / "sandbox-pokebot/profiles", args.store, repo, clone,
                              args.decomp)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return EXIT_REFUSED
    except BadInput as exc:
        print(f"CRASHED (unreadable input): {exc}")
        return EXIT_CRASH
    except Exception as exc:  # noqa: BLE001 - a crash must never exit 1, the code that means "a boss disagrees"
        traceback.print_exc()
        print(f"CRASHED: {type(exc).__name__}: {exc}")
        return EXIT_CRASH
    print(f"{s['mode']}: {s['rows']} rows in runs.jsonl, {s['already']} already in the store, {s['new']} new "
          f"records in {s['seconds']} s; tiers {s['tiers']}; badge-log joins {s['badge_join']}; boss ids from "
          f"{s['boss_ids_from']}")
    if s["no_boss_log"]:
        print(f"{len(s['no_boss_log'])} rows have no boss_log (tier A absent, kept and listed): "
              f"{', '.join(s['no_boss_log'][:40])}")
    if s["parse_suspect"]:
        print(f"PARSE SUSPECT (over {SUSPECT_MIN_LINES} lines, no [TRAINER] start): {', '.join(s['parse_suspect'])}")
    print(f"tier B vs runs.jsonl: {s['bosses_compared']} bosses compared, {len(s['disagreements'])} disagree")
    for key, d in s["disagreements"]:
        print(f"  DISAGREE {key} {d['boss']}: runs.jsonl {d['runs_jsonl']} vs log {d['log']}")
    if s["deferred"]:
        print(f"WARN DEFERRED {len(s['deferred'])} runs (not written, not in the cursor; the next --incremental "
              f"retries them): their cycle had raw data but the log could not be read, and the cycle is not yet "
              f"in its final archived form")
        for key, why in s["deferred"][:20]:
            print(f"  DEFERRED {key}: {why}")
    return code


if __name__ == "__main__":
    sys.exit(main())
