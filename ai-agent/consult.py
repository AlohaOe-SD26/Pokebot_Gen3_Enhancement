"""Asking Claude for help between cycles. OFF by default (`config.json` -> consult.enabled).

When enabled, after each cycle the learner runs the Claude Code CLI in print mode with READ-ONLY tools (it can read
files and search; it cannot edit, run commands or push). Claude reads `findings/LATEST.md` and replies with a short
diagnosis and up to two proposals. Proposals go to `inbox/` and are checked against `knowledge.GENES` before any is
run, so a reply can only choose among knob values that have already run.

Code changes, relaunches and anything that needs judgment stay with an interactive Claude session, where a person
can see them. Every call is logged in `data/consult_log.jsonl`, and a daily cap bounds the cost.

RESERVE BEFORE THE CALL (O5 round 4): a paid call must be impossible unless the daily cap already counts it. So the
consult appends a 'reserved' row (the row `_calls_today` counts) BEFORE it runs `claude`, and when that append fails
(the log is read-only, or another process holds it open for reading only) it does not call at all. After the call an
'outcome' row, joined to the reservation by its "id", records what happened; `_calls_today` does not count it. WHY:
round 3 wrote the only row AFTER the call, so a log that could be read but not appended to paid for a call every
cycle with no row (and no limit, once a consult failure no longer stopped the learner), and a learner killed during
the call (taskkill, Ctrl+C) left no row at all. A reservation is on disk before the money is spent.

The order of the checks (backlog O5, spec S2-2): enabled -> daily cap -> waiting-proposals cap -> NOVELTY -> claude.
The novelty gate asks again only when the learner has something new to show: the top 3 strategies changed, a wall's
share of scored runs moved, enough new scored runs arrived, or a week passed (`novelty`). WHY: from 2026-10-11 the
consult answered twice a day about findings that had barely moved, and its notes repeated themselves. A skip is
logged to `learner.log` and `data/consult_skips.jsonl`, never to `consult_log.jsonl`, whose reservation rows ARE the
daily cap (`_calls_today`): a skip must not use up a real call. Any doubt in the gate (an unreadable digest or state) FAILS
OPEN: the consult goes ahead, and the reason is in the outcome line.

`findings/DEVELOPER-NOTES.md` stays short: a note that repeats the last two (`repeat_line`) becomes one line, and
`roll_notes` (every cycle end) moves all but the newest `NOTES_KEEP` entries, byte for byte, to
`findings/DEVELOPER-NOTES-ARCHIVE.md`. Nothing is lost: every full reply is also in `findings/claude-<tag>.md`.

`py -3.12 consult.py --probe-context` is a one-time developer probe (two cheap Claude calls; never run by the
learner or the tests): does the consult's `claude -p ... --setting-sources user` still load the repo's CLAUDE.md?
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import knowledge as K

PROMPT = """THE GOAL: an AI that plays Pokemon Emerald the way a PERSON does: the story, catching Pokemon along the way,
picking up items, exploring, training sensibly, the Pokedex. Never a speedrun. The progress score is only part of
that: NEVER propose a strategy that gains progress by catching less, exploring less or skipping what a person would do,
and weigh LATEST.md's human-like columns and its "Human-like check" alongside the score.
You are advising the Emerald AI strategy learner (folder ai-agent/ of this repo). Read ai-agent/README.md
and ai-agent/findings/LATEST.md. You may also read PROJECT KNOWLEDGE/05-KNOWN-ISSUES.md for what each failure means,
and PROJECT KNOWLEDGE/ai-research-notes/2026-10-03-decision-points-MAP.md for where the bot makes each decision.
Do NOT edit any file. Base every claim on a number in LATEST.md and say which. A cycle with 0 scored runs is a smoke
test or an abandoned batch, never evidence about a strategy (LATEST.md's cycles table says which).
Reply with:
1. A diagnosis of at most 10 lines: which strategy is winning, where runs end, and what the knob effects suggest.
2. Exactly one fenced ```json block of the form
   {"proposals": [{"name": "short-name", "why": "one sentence", "genes": {"POKEBOT_...": "0 or 1"}}],
    "for_the_developer": "what code change or investigation would help most, one paragraph"}
   with at most 2 proposals, using ONLY the knobs and values in LATEST.md's knob table. A knob you leave out stays at
   its baseline value. Propose combinations the table has NOT already measured well.
"""
JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def _calls_today(log: Path) -> int:
    """Today's calls: the consult_log.jsonl lines that START with `{"day": "<today>"`. Those are the 'reserved' rows
    (and the single rows written before O5 round 4); an 'outcome' row starts with `{"kind": "outcome"` so the same
    call is never counted twice (`_outcome_row`). A log it cannot read raises, and the caller then makes no call."""
    if not log.exists():
        return 0
    today = dt.date.today().isoformat()
    return sum(1 for line in log.read_text(encoding="utf-8").splitlines() if line.startswith(f'{{"day": "{today}"'))


# ------------------------------------------------------------------------------------------------------ novelty gate
#: The novelty gate's thresholds and the inbox's proposal lifetime (backlog O5, spec S2-2), all `config.json` ->
#: `consult` keys; these are the defaults (`learner.DEFAULTS` takes them from here, so they live in one place).
#: - wall_move_points: a RAW difference in percentage points of one wall's share of scored runs. Not rounded buckets,
#:   which flap when a share sits on a bucket edge.
#: - new_runs 150, NOT the backlog's 40: a 12-lane cycle yields about 38-41 scored games, so "40 new runs" fires
#:   nearly every cycle and the gate would do nothing.
#: - forced_days: a consult goes ahead at least this often whatever the digest says; it bounds a real change the
#:   digest cannot see.
#: - proposal_ttl_days: a waiting inbox proposal older than this is moved to inbox/expired/ (`learner.read_inbox`).
NOVELTY_DEFAULTS = {"wall_move_points": 3.0, "new_runs": 150, "forced_days": 7, "proposal_ttl_days": 3}
STATE_NAME, SKIPS_NAME, LOG_NAME = "consult_state.json", "consult_skips.jsonl", "consult_log.jsonl"
#: Float shares computed from counts can land a hair under an exact threshold (3.0 as 2.9999999999); the threshold
#: is meant inclusively, so the comparison allows this much.
EPS = 1e-9


def digest_of(data: dict) -> dict:
    """The novelty digest of `findings/latest.json` (`report.build`'s data): the top 3 genome ids in rank order, each
    wall's share of scored runs in percentage points (count over the total of all walls), and the scored-run count.
    Raises on any shape it does not expect, so the caller can FAIL OPEN instead of comparing garbage."""
    ranked, walls, scored = data["ranked"], data["walls"], data["scored"]
    if not isinstance(ranked, list) or not isinstance(walls, list) or type(scored) is not int or scored < 0:
        raise ValueError("latest.json: 'ranked', 'walls' or 'scored' has the wrong type")
    top3 = [r["genome"] for r in ranked[:3]]
    if not all(isinstance(g, str) and g for g in top3):
        raise ValueError(f"latest.json: a ranked genome id is not a string: {top3!r}")
    counts: dict[str, int] = {}
    for row in walls:
        name, n = row  # a [name, count] pair; anything else raises
        if not isinstance(name, str) or type(n) is not int or n < 0:
            raise ValueError(f"latest.json: bad wall row {row!r}")
        counts[name] = counts.get(name, 0) + n
    total = sum(counts.values())
    return {"top3": top3, "walls": {w: 100.0 * n / total for w, n in counts.items()} if total else {},
            "scored": scored}


def read_digest(ai: Path) -> dict:
    """The digest of the learner's CURRENT findings. `report.write` runs just before the consult (`finish_cycle`), so
    `findings/latest.json` is the cycle that just ended."""
    return digest_of(json.loads((ai / "findings" / "latest.json").read_text(encoding="utf-8")))


def read_state(ai: Path) -> dict | None:
    """The digest and start time of the last consult that went ahead (`data/consult_state.json`), or None when there
    has been none. A file that exists but does not parse RAISES (the caller fails open)."""
    path = ai / "data" / STATE_NAME
    if not path.exists():
        return None
    st = json.loads(path.read_text(encoding="utf-8"))
    d = st["digest"]
    if not isinstance(d["top3"], list) or not isinstance(d["walls"], dict) or type(d["scored"]) is not int or \
            not all(isinstance(v, (int, float)) for v in d["walls"].values()):
        raise ValueError(f"{STATE_NAME}: the digest has the wrong shape")
    return {"digest": d, "at": dt.datetime.fromisoformat(st["at"]), "tag": st.get("tag")}


def write_state(ai: Path, digest: dict, started: dt.datetime, tag: str) -> None:
    path = ai / "data" / STATE_NAME
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({"digest": digest, "at": started.isoformat(timespec="seconds"), "tag": tag}, indent=1),
                   encoding="utf-8")
    os.replace(tmp, path)


def _threshold(c: dict, key: str) -> float:
    """A novelty threshold from the consult config, or RAISE unless it is a finite number > 0. Python's json reads NaN,
    Infinity and 1e400 (inf) from config.json, and `age >= inf` or `age >= nan` is never true: the weekly force would
    then never fire and a plateau would never be consulted again (fail CLOSED). Raising lets `maybe_consult` fail
    OPEN with the reason in its line, as `learner._ttl_seconds` guards the inbox TTL."""
    value = float(c.get(key, NOVELTY_DEFAULTS[key]))
    if not (math.isfinite(value) and value > 0):
        raise ValueError(f"consult.{key} {c.get(key)!r} is not a finite number > 0")
    return value


def novelty(c: dict, new: dict, prev: dict | None, now: dt.datetime) -> tuple[bool, str]:
    """(go, why). Go when there is no previous digest, the top 3 changed (order included: a new leader is news), a
    wall's share moved >= wall_move_points, scored runs grew >= new_runs, or forced_days passed since the last consult
    that went ahead. A bad threshold or state RAISES (the caller fails open)."""
    pts, days = _threshold(c, "wall_move_points"), _threshold(c, "forced_days")
    runs = int(_threshold(c, "new_runs"))
    if runs <= 0:  # 0.5 truncates to 0, and "grew >= 0" would then hold every cycle
        raise ValueError(f"consult.new_runs {c.get('new_runs')!r} is under 1")
    if prev is None:
        return True, "no previous digest"
    old, at = prev["digest"], prev["at"]
    age = (now - at).total_seconds() / 86400
    if age < -1:  # a state from the future would postpone the weekly force for ever
        raise ValueError(f"{STATE_NAME}: the last consult's time {at} lies in the future")
    if new["top3"] != old["top3"]:
        return True, f"the top 3 changed ({', '.join(old['top3'])} -> {', '.join(new['top3'])})"
    moves = [(abs(new["walls"].get(w, 0.0) - old["walls"].get(w, 0.0)), w)
             for w in set(new["walls"]) | set(old["walls"])]
    moved, wall = max(moves, default=(0.0, ""))
    if moved + EPS >= pts:
        return True, f"the share of '{wall}' moved {moved:.1f} points (>= {pts:g})"
    grew = new["scored"] - old["scored"]
    if grew >= runs:
        return True, f"{grew} new scored runs (>= {runs})"
    if age >= days:
        return True, f"{age:.1f} days since the last consult (one is forced every {days:g})"
    return False, (f"nothing new since {at:%Y-%m-%d %I:%M %p} ({prev.get('tag')}): top 3 unchanged, largest wall move "
                   f"{moved:.1f} points (< {pts:g}), +{grew} scored runs (< {runs}), a consult is forced in "
                   f"{days - age:.1f} days")


def record_skip(ai: Path, tag: str, why: str, digest: dict) -> str:
    """Log a novelty skip to `data/consult_skips.jsonl`, NEVER `consult_log.jsonl` (that file's reservation rows are
    the daily cap). Returns the outcome line for `learner.log`. A failed write is reported in it, never raised."""
    row = {"day": dt.date.today().isoformat(), "tag": tag, "at": dt.datetime.now().isoformat(timespec="seconds"),
           "why": why, "scored": digest["scored"], "top3": digest["top3"]}
    extra = ""
    try:
        (ai / "data").mkdir(parents=True, exist_ok=True)
        with open(ai / "data" / SKIPS_NAME, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError as exc:
        extra = f" (could not write {SKIPS_NAME}: {exc!r})"
    return f"consult: skipped, {why}{extra}"


# ------------------------------------------------------------------------------------------------- developer notes
NOTES, NOTES_ARCHIVE, NOTES_KEEP = "DEVELOPER-NOTES.md", "DEVELOPER-NOTES-ARCHIVE.md", 5
#: A note repeats when its key terms overlap each of the last REPEAT_WINDOW full notes by at least this (Jaccard).
REPEAT_JACCARD, REPEAT_WINDOW = 0.6, 2
#: One DEVELOPER-NOTES.md entry starts at a heading exactly as `write_note` writes it. A '## ' line inside a note
#: (Claude's own markdown) is not a boundary, so it stays with its entry. `\r?` because `roll_notes` reads the file
#: byte for byte (newline="") and the learner writes it in Windows text mode (CRLF).
ENTRY_HEAD = re.compile(r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2} [AP]M), after cycle (\S+)\r?$", re.M)
#: The one line a repeating note becomes (`repeat_line`), matched as a whole line so a note body can be read without
#: it and the next repeat can count it.
REPEAT_LINE = re.compile(r"^- \d{4}-\d{2}-\d{2} \d{2}:\d{2} [AP]M, after \S+: unchanged since [^\n]*?\(\d+ consults?\)"
                         r"[^\n]*$", re.M)
#: Key terms named outright: known-issue ids and knob names.
TERM = re.compile(r"\bKI-\d+\b|\bPOKEBOT_\w+")
#: Prefixes dropped from a wall name before matching it in prose ("boss wall: Norman" is written "Norman").
WALL_PREFIXES = ("boss wall:", "e4 refused:")


def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def wall_keys(walls: list[str]) -> set[str]:
    """The prose form of each wall name: lower case, punctuation folded, its kind prefix dropped. CHAMPION is the
    winning outcome, which nearly every note names, so it is not a key term."""
    keys = set()
    for name in walls:
        k = name.lower()
        for p in WALL_PREFIXES:
            k = k.removeprefix(p)
        k = _norm(k)
        if k and k != "champion":
            keys.add(k)
    return keys


def note_terms(text: str, keys: set[str]) -> set[str]:
    padded = f" {_norm(text)} "
    return {m.group(0).upper() for m in TERM.finditer(text)} | {f"wall:{k}" for k in keys if f" {k} " in padded}


def jaccard(a: set, b: set) -> float:
    """|a & b| / |a | b|, and 0.0 for two empty sets: a note with no key terms is never called a repeat."""
    return len(a & b) / len(a | b) if a | b else 0.0


def split_notes(text: str) -> tuple[str, list[str]]:
    """(preamble, entries), each entry from its ENTRY_HEAD line up to the next one, byte for byte:
    preamble + ''.join(entries) == text, always."""
    starts = [m.start() for m in ENTRY_HEAD.finditer(text)]
    if not starts:
        return text, []
    bounds = starts + [len(text)]
    return text[:starts[0]], [text[a:b] for a, b in zip(bounds, bounds[1:])]


def entry_body(entry: str) -> str:
    """An entry's note text: its heading line and its repeat lines removed."""
    return REPEAT_LINE.sub("", ENTRY_HEAD.sub("", entry, count=1))


def repeat_line(text: str, note: str, head: str, tag: str, walls: list[str]) -> str | None:
    """The ONE line to append instead of `note` when it repeats each of the last REPEAT_WINDOW full notes in `text`
    (Jaccard of key terms >= REPEAT_JACCARD), else None. Key terms: KI-n ids, POKEBOT_ knobs, the walls in
    latest.json. A KI id that neither of those notes names is news by itself, so such a note is always written in
    full: with 4 shared terms, one new id alone leaves the Jaccard at 0.8. The full reply stays in
    findings/claude-<tag>.md, so the line loses nothing."""
    _, entries = split_notes(text)
    if len(entries) < REPEAT_WINDOW:
        return None
    keys = wall_keys(walls)
    terms = note_terms(note, keys)
    recent = [note_terms(entry_body(e), keys) for e in entries[-REPEAT_WINDOW:]]
    new_ids = {t for t in terms if t.startswith("KI-")} - set().union(*recent)
    if new_ids or any(jaccard(terms, r) < REPEAT_JACCARD for r in recent):
        return None
    last = entries[-1]
    since = ENTRY_HEAD.match(last).group(1)
    n = len(REPEAT_LINE.findall(last)) + 1  # the consults since the last distinct note, this one included
    tail = text.rstrip("\r\n").rsplit("\n", 1)[-1].rstrip("\r")
    lead = "" if REPEAT_LINE.fullmatch(tail) else "\n"  # a blank line before the first repeat line only
    return (f"{lead}- {head}, after {tag}: unchanged since {since} ({n} consult{'' if n == 1 else 's'}); "
            f"full reply in claude-{tag}.md\n")


def write_note(findings: Path, note: str, started: dt.datetime, tag: str, walls: list[str]) -> str:
    """Append Claude's note for the developer to DEVELOPER-NOTES.md: the full paragraph, or ONE line when it repeats
    the last notes. Returns 'full' or 'repeat'. Any doubt in the comparison writes the full note."""
    path = findings / NOTES
    head = f"{started:%Y-%m-%d %I:%M %p}"
    try:
        line = repeat_line(path.read_text(encoding="utf-8") if path.exists() else "", note, head, tag, walls)
    except Exception:  # noqa: BLE001 - the collapse only saves reading time; it must never cost a note
        line = None
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line or f"\n## {head}, after cycle {tag}\n\n{note.strip()}\n")
    return "repeat" if line else "full"


def _read_exact(path: Path) -> str:
    """The file's text with its line endings untouched (newline=''), so a move is byte for byte."""
    if not path.exists():
        return ""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def roll_notes(findings: Path, keep: int = NOTES_KEEP) -> str:
    """Keep the newest `keep` entries in DEVELOPER-NOTES.md and move the older ones, VERBATIM, to the end of
    DEVELOPER-NOTES-ARCHIVE.md. The learner calls it at every cycle end, consult or not. Returns a line for the log
    ('' when there is nothing to move); RAISES on any doubt, leaving the notes file as it was.

    No loss, by order of writes: the archive is appended (and read back) BEFORE the notes file is replaced, so a crash
    in between leaves an entry in both files, never in neither. The next roll then sees that the archive already ends
    with those entries and does not append them twice."""
    path = findings / NOTES
    text = _read_exact(path)
    pre, entries = split_notes(text)
    if len(entries) <= keep:
        return ""
    moved, kept = entries[:-keep], entries[-keep:]
    if pre + "".join(moved) + "".join(kept) != text:
        raise RuntimeError(f"{NOTES}: the entry split is not lossless; nothing moved")
    arch = findings / NOTES_ARCHIVE
    old = _read_exact(arch)
    done = next((k for k in range(len(moved), 0, -1) if old.endswith("".join(moved[:k]))), 0)
    if done < len(moved):
        with open(arch, "a", encoding="utf-8", newline="") as fh:
            fh.write("".join(moved[done:]))
            fh.flush()
            os.fsync(fh.fileno())
    if not _read_exact(arch).endswith("".join(moved)):
        raise RuntimeError(f"{NOTES_ARCHIVE} does not end with the entries to move; {NOTES} left as it was")
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(pre + "".join(kept))
        fh.flush()
        os.fsync(fh.fileno())
    if _read_exact(path) != text:  # someone appended meanwhile: keep their text, roll again next cycle
        tmp.unlink()
        raise RuntimeError(f"{NOTES} changed while rolling; left as it was")
    os.replace(tmp, path)
    return f"notes: moved {len(moved)} older entr{'y' if len(moved) == 1 else 'ies'} to {NOTES_ARCHIVE}, kept {keep}"


# ----------------------------------------------------------------------------------------------------------- consult
def build_command(exe: str, c: dict, prompt: str = PROMPT, fmt: str = "text") -> list[str]:
    """The consult's command line. Each flag is a safety property:
    - `--setting-sources user` skips the PROJECT settings, and with them the session-start hook, which runs
      `git pull` when the checkout is behind. A pull that touches `sandbox-pokebot/` aborts the learner's running
      batch (the batch runner's freeze watch).
    - `--allowedTools Read,Grep,Glob`: it can read and search, never edit, run commands or push.
    - `--max-budget-usd`: a hard cap on what one consult can spend. `--model`: a cheaper model by default.
    - `--no-session-persistence`: no saved session clutters the user's session list."""
    return [exe, "-p", prompt, "--output-format", fmt, "--model", str(c.get("model", "sonnet")),
            "--max-budget-usd", str(c.get("max_usd_per_call", 0.75)), "--allowedTools", "Read,Grep,Glob",
            "--setting-sources", "user", "--no-session-persistence"]


def _append_row(log: Path, row: dict) -> None:
    """Append one JSON line to consult_log.jsonl (its folder made if missing). Raises on any failure: the caller
    decides what a failed write means (no call for a reservation; a note in the outcome line for an outcome row)."""
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def _reservation_row(rid: str, tag: str, started: dt.datetime, why: str) -> dict:
    """The row that COUNTS toward the daily cap: "day" is its first key, so its line starts `{"day": "<today>"`."""
    return {"day": dt.date.today().isoformat(), "kind": "reserved", "id": rid, "tag": tag,
            "started": started.isoformat(), "why": why}


def _outcome_row(rid: str, fields: dict) -> dict:
    """The row that records a call's result and is NOT counted: "kind" is its first key, so its line never starts
    with `{"day": `. `fields` are the result (day, tag, started, seconds, exit, proposals_accepted, note, failed?)."""
    return {"kind": "outcome", "id": rid, **fields}


def maybe_consult(cfg: dict, repo: Path, ai: Path, tag: str) -> str:
    """Run one consult if enabled, under the daily cap, not held back by a full queue, and there is something new to
    show (`novelty`). Returns a one-line outcome for the learner's log.
    Before `claude` runs, a counted 'reserved' row must be on disk; if it cannot be written, no call is made (the
    module docstring says why). After the call, an uncounted 'outcome' row with the same "id" records the result. An
    exception from the call itself (a kill, Ctrl+C) propagates, and the reservation already counts that call."""
    c = cfg.get("consult", {})
    if not c.get("enabled"):
        return "consult: off"
    log = ai / "data" / LOG_NAME
    if _calls_today(log) >= int(c.get("max_calls_per_day", 2)):
        return "consult: daily cap reached"
    # A queue that grows faster than one proposal per cycle is used only spends the user's Claude usage on ideas
    # that will wait days (2026-10-17: 12 waiting, 2 arriving and 1 used per cycle). Ask again once it drains.
    inbox = ai / "inbox"
    waiting = len(list(inbox.glob("*.json"))) if inbox.is_dir() else 0
    cap = int(c.get("max_waiting_proposals", 6))
    if waiting >= cap:
        return f"consult: skipped, {waiting} proposal(s) already waiting (cap {cap}); asking again once the queue drains"
    digest = None
    try:
        digest = read_digest(ai)
        go, why = novelty(c, digest, read_state(ai), dt.datetime.now())
    except Exception as exc:  # noqa: BLE001 - the gate only saves usage: on any doubt it must not withhold a consult
        go, why = True, f"the novelty gate failed open ({type(exc).__name__}: {exc})"
    if not go:
        return record_skip(ai, tag, why, digest)
    exe = shutil.which("claude")
    if not exe:
        return f"consult: the `claude` command is not on PATH (it would have gone ahead: {why})"
    cmd = build_command(exe, c)
    started = dt.datetime.now()
    rid = uuid.uuid4().hex[:12]
    # RESERVE BEFORE THE CALL: the counted row goes to disk first, and a call the cap cannot count is never made. A
    # learner killed during the call keeps this row, so the cap still counts the call it may have paid for.
    try:
        _append_row(log, _reservation_row(rid, tag, started, why))
    except Exception as exc:  # noqa: BLE001 - ANY doubt that the cap counts this call means no call
        return (f"consult: not asked, could not reserve the call in {log} ({type(exc).__name__}: {exc}); a call the "
                f"daily cap cannot count is never made, so this cycle has no consult (it would have gone ahead: {why})")
    try:
        proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=60 * float(c.get("timeout_minutes", 20)))
        reply, rc = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired:
        reply, rc = "", "timeout"
    accepted, note_kind, failures = 0, "none", []
    # The call is PAID now (and already counted by its reservation). Each side effect (the reply file, a proposal, the
    # notes append, e.g. a notes file locked by another process) is guarded on its own, so one failure costs no other
    # and none stops the outcome row or the baseline below (O5 round 3); the reasons go in the outcome row
    # ("failed"), and a note that could not be written is note 'failed'.

    def guarded(what: str, fn, *args):  # noqa: ANN001, ANN202
        try:
            return fn(*args)
        except Exception as exc:  # noqa: BLE001 - see above: the row below must be written after a paid call
            failures.append(f"{what}: {type(exc).__name__}: {exc}"[:300])
            return None

    findings = ai / "findings"

    def save_reply() -> None:
        findings.mkdir(exist_ok=True)
        (findings / f"claude-{tag}.md").write_text(reply or "(no reply)", encoding="utf-8")

    guarded(f"claude-{tag}.md", save_reply)
    m = JSON_BLOCK.search(reply or "")
    if m:
        try:
            body = json.loads(m.group(1))
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}

        def queue(i: int, p) -> bool:  # noqa: ANN001
            if not (isinstance(p, dict) and isinstance(p.get("genes"), dict)) or K.validate_genes(p["genes"]):
                return False
            (ai / "inbox").mkdir(exist_ok=True)
            (ai / "inbox" / f"claude-{tag}-{i + 1}.json").write_text(json.dumps(p, indent=1), encoding="utf-8")
            return True

        props = body.get("proposals")
        for i, p in enumerate(props[:2] if isinstance(props, list) else []):
            if guarded(f"proposal {i + 1}", queue, i, p):
                accepted += 1
        note = body.get("for_the_developer")
        if isinstance(note, str) and note.strip():
            # One running file for the next interactive session to read first; a repeat becomes one line.
            note_kind = guarded("note", lambda: write_note(findings, note, started, tag, list(digest["walls"])
                                                           if digest else [])) or "failed"
    failed = "; ".join(failures)
    fields = {"day": dt.date.today().isoformat(), "tag": tag, "started": started.isoformat(),
              "seconds": round((dt.datetime.now() - started).total_seconds()), "exit": rc,
              "proposals_accepted": accepted, "note": note_kind}
    if failed:
        fields["failed"] = failed
    extra = ""
    try:
        _append_row(log, _outcome_row(rid, fields))
    except Exception as exc:  # noqa: BLE001 - the reservation already counts the call; the baseline below must move
        extra = (f"; could not write its outcome row ({type(exc).__name__}: {exc}), the call is counted by its "
                 "reservation")
    if rc == 0 and digest is not None:
        # Only a call that went through moves the baseline: after a failed one (the usage ran out, a timeout) the next
        # cycle asks again, as it did before the gate.
        try:
            write_state(ai, digest, started, tag)
        except OSError as exc:
            extra += f"; could not save {STATE_NAME} ({exc!r})"
    if failed:
        extra += f"; a side effect failed after the call ({failed}), the call is still logged"
    return f"consult: exit {rc}, {accepted} proposal(s) queued, note {note_kind}; asked because {why}{extra}"


# ------------------------------------------------------------------------------------------------- dev probe (O5)
def _input_tokens(stdout: str) -> int:
    """Total input tokens of one `--output-format json` reply: input + cache creation + cache read."""
    u = json.loads(stdout)["usage"]
    return sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


def probe_context(repo: Path, c: dict, run=subprocess.run, which=shutil.which) -> int:
    """ONE-TIME developer probe (spec S2-2; about two cheap calls of the user's usage, so never run by the learner or
    the tests): does `claude -p ... --setting-sources user`, the consult's own flags, still load the repo's CLAUDE.md?
    Runs `claude -p "Reply OK" --output-format json` from the repo, then from an EMPTY temp dir with `--add-dir <repo>`,
    and prints the difference in total input tokens. A difference near CLAUDE.md's size (about 10k tokens) says the
    repo run loads it. It does NOT change the consult's cwd: that switch is a separate decision, after an A/B on
    proposal quality (it would also drop the project's rules from the consult's context)."""
    exe = which("claude")
    if not exe:
        print("the `claude` command is not on PATH")
        return 2
    totals = {}
    with tempfile.TemporaryDirectory(prefix="consult-probe-") as empty:
        for name, cwd, extra in (("from the repo", repo, []),
                                 ("from an empty dir with --add-dir", Path(empty), ["--add-dir", str(repo)])):
            cmd = build_command(exe, c, prompt="Reply OK", fmt="json") + extra
            proc = run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            if proc.returncode != 0:
                print(f"{name}: exit {proc.returncode}: {(proc.stderr or proc.stdout or '')[:300]}")
                return 1
            totals[name] = _input_tokens(proc.stdout)
            print(f"{name}: {totals[name]} input tokens (input + cache write + cache read)")
    a, b = totals.values()
    print(f"difference (repo minus empty dir): {a - b} tokens. Record it in 06 (spec S2-2).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="The learner's Claude consult. The learner imports it; run it directly "
                                             "only for the developer probe.")
    ap.add_argument("--probe-context", action="store_true",
                    help="one-time: does the consult's `claude -p --setting-sources user` load the repo CLAUDE.md? "
                         "(two cheap calls of the user's usage)")
    args = ap.parse_args(argv)
    if not args.probe_context:
        ap.print_help()
        return 2
    ai = Path(__file__).resolve().parent
    c = json.loads((ai / "config.json").read_text(encoding="utf-8")).get("consult", {})
    return probe_context(ai.parent, c)


if __name__ == "__main__":
    sys.exit(main())
