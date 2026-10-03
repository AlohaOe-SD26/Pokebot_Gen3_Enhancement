"""Turn one batch's raw debug logs into small per-RUN records (about 1 KB each), so the 2 GB of logs can be deleted.

A batch directory (`x4_headless.py --out`) holds `ARMS.json` and `L01..Lnn/debug-logs/*.log`, one log per run.
Lane `Lnn` is `ARMS.json["lanes"][nn-1]`, which names its arm and starter.

Rules (each one is a lesson the grader learned, see KI-119):
- a run STARTS at its first `Story: choosing X!` line. Anything before it (a stale save's boot) is ignored.
- badges are counted from LEADER WINS (`[TRAINER] end opp=265..272 ... res=Won`), not from the party or a save.
- a run is COMPLETE if it became Champion, if a later log follows it in the same lane, or if it reached the fifth
  derail. Otherwise the batch's time limit cut it off: it is CENSORED and kept out of the scores.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import knowledge as K

STARTER_RE = re.compile(r"Story: choosing (\w+)!")
TRAINER_END_RE = re.compile(r"\[TRAINER\] end opp=(\d+)\b.*?\bres=(\w+)")
DERAIL_RE = re.compile(r"\[STORY\] DERAIL #(\d+): (.*)")
HB_RE = re.compile(r"\[hb\] mode=(.+?) state=\S+ controllable=\S+ map=(.+?)\(\d+,\d+\) pos=\((\d+), (\d+)\) "
                   r"party=(\[[^\]]*\])")
FRAME_RE = re.compile(r"^f(\d+) ")
#: A run is ended by its fifth derail (every finished run in step 14's logs ends on `DERAIL #5`).
DERAIL_CAP = 5


def parse_log(path: Path) -> dict:
    """One run's record from one log. Pure reading; never raises on odd lines."""
    rec = {"log": path.name, "starter": None, "badges": [], "e4": [], "champion": False, "wins": {}, "losses": {},
           "derails": 0, "last_derail": None, "end_map": None, "end_pos": None, "end_party": None, "frames": 0,
           "mode_at_end": None}
    started = False
    with open(path, "rb") as fh:
        for raw in fh:
            if not (b"choosing" in raw or b"[TRAINER] end" in raw or b"DERAIL #" in raw or b"[hb]" in raw):
                continue
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            m = FRAME_RE.match(line)
            if m:
                rec["frames"] = max(rec["frames"], int(m.group(1)))
            if not started:
                s = STARTER_RE.search(line)
                if s:
                    started, rec["starter"] = True, s.group(1)
                continue
            if (t := TRAINER_END_RE.search(line)):
                opp, res = int(t.group(1)), t.group(2)
                name = K.KEY_TRAINERS.get(opp)
                if name is None:
                    continue
                bucket = rec["wins"] if res == "Won" else rec["losses"]
                bucket[name] = bucket.get(name, 0) + 1
                if res == "Won":
                    if opp in K.LEADERS and name not in rec["badges"]:
                        rec["badges"].append(name)
                    elif opp in K.ELITE_FOUR and name not in rec["e4"]:
                        rec["e4"].append(name)
                    elif opp in K.CHAMPION:
                        rec["champion"] = True
            elif (d := DERAIL_RE.search(line)):
                rec["derails"] = max(rec["derails"], int(d.group(1)))
                rec["last_derail"] = d.group(2)[:240]
            elif (h := HB_RE.search(line)):
                rec["mode_at_end"], rec["end_map"] = h.group(1), h.group(2).strip()
                rec["end_pos"] = [int(h.group(3)), int(h.group(4))]
                rec["end_party"] = h.group(5)[:200]
    rec["progress"] = len(rec["badges"]) + len(rec["e4"]) + (1 if rec["champion"] else 0)
    rec["score"] = round(rec["progress"] / K.MAX_PROGRESS, 4)
    rec["wall"] = "CHAMPION" if rec["champion"] else K.classify_wall(rec["last_derail"])
    return rec


def genome_of_env(env: dict) -> dict:
    """The learner's view of an arm: every GENE's value (a knob the arm did not set counts as its baseline value)."""
    return {g: str(env.get(g, vals[0])) for g, (vals, _) in K.GENES.items()}


def parse_batch(batch_dir: Path, source: str) -> list[dict]:
    """Every run record of one finished batch. `source` labels where it came from (a cycle tag or 'ingest')."""
    batch_dir = Path(batch_dir)
    meta = json.loads((batch_dir / "ARMS.json").read_text(encoding="utf-8"))
    arms = json.loads(meta["arms_text"])["arms"]
    records = []
    for i, lane in enumerate(meta["lanes"]):
        logs = sorted((batch_dir / f"L{i + 1:02d}" / "debug-logs").glob("*.log"))
        for j, path in enumerate(logs):
            rec = parse_log(path)
            last_in_lane = j == len(logs) - 1
            rec["complete"] = bool(rec["champion"] or not last_in_lane or rec["derails"] >= DERAIL_CAP)
            rec["usable"] = rec["complete"] and rec["starter"] is not None
            rec.update(source=source, batch=meta.get("stamp"), code_commit=meta.get("code_commit"),
                       lane=i + 1, lane_starter=lane.get("starter"), arm=lane.get("arm"),
                       genome=genome_of_env(arms[lane["arm"]]))
            records.append(rec)
    return records
