r"""DESIGN v2 STEP 14, T3 — the batch A/B's GRADE (B − A): DESIGN §5's statistics on T2's per-run records.

⛔ THE CAVEAT IS THE HEADLINE: a MEASUREMENT tool (tools/story-dev only). It grades one night's batch and decides nothing
about the bot by itself; "a non-significant result is NOT confirmation" (DESIGN §5), and a missing harm flag is NOT
"no harm".

THE SPEC (binding): `ai-research-notes/2026-10-01-batch14-T23-PREDICTIONS.md`, and its parent
`…-batch14-DESIGN.md` §3 T3 + §4 + §5. §5's statistics are FROZEN there (K*, δ, the C1 → C2 sequence, the harm flags at
one-sided .05): this file IMPLEMENTS them and must never improve them. Where the spec was silent, the simplest reading
was taken and is marked `SPEC-SILENT` beside the code; the coordinator's rulings on the independent adversarial pass
(`evidence/2026-10-01-batch14-T23-ADVERSARIAL.txt`, decisions F1-F11 and RC-1..RC-3) are marked `DECISION Fn`.

INPUT. A batch directory: `x4-runs/<stamp>` (a stamp resolves under the MAIN checkout, `battle_log.main_story_dev`) or
any path, holding T1's `ARMS.json` (the arms, each lane's arm, the design's size) and, once the batch has ended,
`summary.json` (its verdict and stop, each lane's CUT log, spawns and collected-log count). Or `--tag TAG` for a
RUNNING batch: its logs from the lane profiles (`battle_log.live_logs`), its `ARMS.json` found by `profile_tag`.

EACH LOG IS ONE RUN (`run_record`):
  * its lane (tag, slot) from its directory; its arm from the header's `env-all:` (`battle_log.arm_of`).
    ⛔ A log whose arm DISAGREES with its lane's `ARMS.json` arm is REFUSED (counted and listed), never re-assigned —
    a CUT log included: a run that loaded the wrong flags must void the grade, not move to the other arm;
  * species + PID (`battle_log.run_identity`: the first non-empty `[hb]` AFTER the run's `Story: choosing X!` line —
    KI-119, a reset booted from a Hall-of-Fame save logs that save's party before it); the CLUSTER is (arm, species,
    PID): replays of one seed are one unit. Only Torchic, Mudkip and Treecko form strata, and the species must agree
    with the run's `Story: choosing X!` (a log with no such line is `no_starter`, KI-119's decision);
  * status: `cut` (the lane's `cut_log`), `lost` (the log a DYING spawn had open), `capped` (the 30 MiB cap), else
    `complete`. The first three are CENSORED: they say nothing about a trainer they never met;
  * per K* trainer: met (any `[TRAINER] start`), the FIRST attempt's outcome (`battle_log.first_attempts`; a Draw is
    a loss; ⛔ never `first=`) and its `heal_stock` HP-item count (`battle_log.hp_item_count`);
  * the NON-KEY trainer battles' outcomes (`battle_log.battle_class` == NON-KEY).

THE STATISTICS (DESIGN §5; `statistics` computes every one of them from per-cluster sums, ONE function for the point
estimate and for every bootstrap draw, so the two can never disagree):
  C1  per run, the mean HP-item count over its K* first attempts; per arm, the mean over runs. PASS iff the lower bound
      of B − A's two-sided 95% CI is above 0; otherwise C2 is DESCRIPTIVE.
  C2  p[a,X,s] = won first / fought, per realized species s; p[a,X] = the equal-weight mean over the species with such
      a run in BOTH arms; θ[a] = the mean over the FROZEN K* — undefined unless all 7 are estimable (DECISION F2);
      Δ = θB − θA. NOT LOWER if lower95 > −δ; then HIGHER if lower95 > 0; else INCONCLUSIVE; "NOT LOWER, but
      statistically lower" when the 95% CI lies inside (−δ, 0). δ is the PRE-REGISTERED one for the design.
  C2 LOWER (harm flag): upper90 < 0.      C5 (harm flag): (Lost + Draw) / battles over NON-KEY trainer battles, a
  ratio of sums per arm: REGRESSION if lower90 of B − A > 0, IMPROVED if upper90 < 0.
  REACH per X: the meet rate over runs NOT censored before X (a cut / lost / capped run that never met X is out, and
  so is one censored DURING its first attempt at X); B − A with a 90% CI; REACH DIFFERS (on the C2 line) if any CI
  excludes 0. COMPOSITE (always printed): P(met X and won the first attempt) over the same runs, species-weighted as
  C2. PER GROUP (descriptive): θ over each group's K* trainers.
  THE BOOTSTRAP: `--draws` (10,000) seeded (`--seed`, 14); clusters resampled WHOLE, with replacement, within strata of
  arm × species; percentile CIs; a draw in which a statistic is undefined is dropped, and the count is printed.
THE STATUS of C1 / C2 (DESIGN §4, DECISIONS F1 F6 F7): CONFIRMATORY only with none of — a STOP that voids them
  (an automated abort in summary.json, or `--void`), a LIVE read without summary.json (PROVISIONAL), a non-pre-
  registered draws / seed / δ (EXPLORATORY), a GRADER revised after the batch started (`GRADER_REVISIONS`, fail-
  closed: EXPLORATORY), K* not fully estimable, C1 not passing. The JSON carries the rule's word (`rule_reading`)
  apart from the `verdict`, which is that word only when CONFIRMATORY — or OPERATIVE: a grader revision a recorded
  user ruling made operative for that batch (`GRADER_RULINGS`); the status then names the ruling AND the revision.

EXIT: 0 the grade was computed (whatever the verdicts); 1 an INSTRUMENT CONTROL failed (zero runs, a refused log, an
arm with no usable runs, an INCOMPLETE batch directory) — then NO statistic is printed, so no verdict word can be read
as confirmatory; 2 usage (incl. a design with no pre-registered δ and no `--delta`).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 compare_arms.py 20261001-090649 [--json OUT]
      PYTHONUTF8=1 py -3.12 compare_arms.py --tag s14            (LIVE, during the batch: PROVISIONAL)
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import battle_log as bl  # noqa: E402

try:
    import numpy as np
except ImportError:  # pragma: no cover - numpy is installed here; the CLI refuses cleanly without it (exit 2)
    np = None

# ---------------------------------------------------------------------------------------------------- K* (FROZEN)
#: DESIGN §5 step 2: K* is FROZEN, never re-derived from step 14's data. The ids are pret/pokeemerald
#: `include/constants/opponents.h` (:269-272 the leaders; :525-540 the Route 110 rival, Brendan and May x the three
#: starters; :601 Tabitha, :606 Maxie at Mt. Chimney), re-read with `gh api` by the builder on 2026-10-01.
#: Order = the spec's table (it does not affect any statistic).
KSTAR = {
    "ROXANNE": (265,),
    "BRAWLY": (266,),
    "WATTSON": (267,),
    "FLANNERY": (268,),
    "RIVAL_ROUTE_110": (521, 524, 527, 530, 533, 536),
    "TABITHA_MT_CHIMNEY": (597,),
    "MAXIE_MT_CHIMNEY": (602,),
}
KEYS = tuple(KSTAR)
#: DESIGN §5 "Per-group" (leaders, rivals, Magma/Aqua), each restricted to K*.
GROUPS = {
    "leaders": ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY"),
    "rivals": ("RIVAL_ROUTE_110",),
    "magma_aqua": ("TABITHA_MT_CHIMNEY", "MAXIE_MT_CHIMNEY"),
}
#: DESIGN §5: the strata are arm x REALIZED starter, s in {Torchic, Mudkip, Treecko} (DECISION F8: nothing else).
STARTERS = ("Torchic", "Mudkip", "Treecko")
DEFAULT_DRAWS = 10_000
DEFAULT_SEED = 14
#: DESIGN §5's margin, by the design T1 recorded in ARMS.json (lanes_n, number of arms): M-16 .08, M-8 .11. Any other
#: design has no pre-registered δ: `--delta` is then required and the grade is EXPLORATORY (DECISION F6).
PREREG_DELTA = {(16, 2): 0.08, (8, 2): 0.11}
ARM_A, ARM_B = "A", "B"   # B − A is the one confirmatory comparison (DESIGN §2)
#: DESIGN §4: "any STOP voids C1-C2". x4_headless's automated aborts (its `aborted` texts, the part of the verdict
#: after "FAILED — "); an "x4h error: …" abort voids too. ⛔ A user park does NOT void: "a user park stands".
AUTOMATED_STOPS = ("ARM LEAK", "VACUITY", "ARM HEADER ASSERTION FAILED", "EMULATION ASSERTION FAILED", "FREEZE BROKEN")
USER_PARK = "interrupted by user (Ctrl-C)"
#: ⛔ FAIL-CLOSED (`#27-gradeidentity`, KI-119; the review's GS-1 / GS-2): every revision of how THIS grader reads a
#: log — a UNIQUE `id`, the LOCAL time it took effect (`at`: naive ISO at second precision, the build commit's time)
#: and `what` changed. A batch whose ARMS.json `started` (the same clock, the same precision) is NOT AFTER a revision's
#: `at` was graded by a grader revised after its data began: its C1-C2 are EXPLORATORY naming the revision (DESIGN §4:
#: no read may change "any analysis choice"), unless a recorded user ruling for EXACTLY that batch names the
#: revision's id (`GRADER_RULINGS`). A batch whose data began after the change cannot have shaped it; an unreadable
#: `started` predates every revision.
GRADER_REVISIONS = (
    {"id": "KI-119/#27-gradeidentity", "at": "2026-10-02T12:48:21",
     "what": "a run's identity and progress are read after its 'Story: choosing X!' line; badges from leader wins"},
)
#: (stamp, code_commit, started) -> the recorded user ruling that makes that batch's grade OPERATIVE despite the
#: revisions it names BY ID. GS-8: all three are ARMS.json's, matched EXACTLY (never a pattern), so a re-run or a
#: re-collected directory under the same stamp is not covered. The status then reads "OPERATIVE BY <ruling> — graded
#: by a grader revised after the batch (…)": the revision stays visible, and the verdict is the rule's word. A
#: revision the ruling does not name stays EXPLORATORY.
GRADER_RULINGS = {
    ("20261001-210001", "f4509da1", "2026-10-01T21:00:01"): {
        "ruling": "USER RULING 30", "revisions": ("KI-119/#27-gradeidentity",),
        "why": "06-DECISIONS-LOG 2026-10-02: the KI-119 identity repair fixes a MISREAD; the corrected grade is the "
               "operative result"},
}
_AT_SHAPE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def at_second(text) -> "datetime.datetime | None":
    """`#27-gradeidentity` (GS-2): a naive local ISO timestamp at SECOND precision (`YYYY-MM-DDTHH:MM:SS`) -> a
    datetime; anything else (None, a date alone, a fraction, a zone, an impossible date) -> None, which the revision
    rule reads as UNKNOWN (fail-closed)."""
    if not isinstance(text, str) or not _AT_SHAPE.fullmatch(text):
        return None
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def check_revisions(revisions) -> None:
    """Raise unless every grader revision has a UNIQUE id (GS-1) and an `at` at second precision (GS-2)."""
    seen: set = set()
    for rev in revisions:
        if rev["id"] in seen:
            raise AssertionError(f"grader revision id {rev['id']!r} is listed twice")
        seen.add(rev["id"])
        if at_second(rev["at"]) is None:
            raise AssertionError(f"grader revision {rev['id']!r}: at {rev['at']!r} is not YYYY-MM-DDTHH:MM:SS")


check_revisions(GRADER_REVISIONS)
#: Per-cluster fields: (C, K) matrices, then (C,) vectors. N/W = decided first attempts fought / won; RN/RD = reach
#: numerator / denominator; CN = composite numerator (denominator RD); H/Hn = C1's per-run means summed / counted;
#: L5/B5 = non-key trainer battles lost (Draw included) / decided; NR = runs.
FIELDS_K = ("N", "W", "RN", "RD", "CN")
FIELDS_1 = ("H", "Hn", "L5", "B5", "NR")


# ---------------------------------------------------------------------------------------------------- one run (pure)
def run_record(lines, *, log: str, lane: dict, arms: dict, cut: bool = False, lost: bool = False,
               param_of=bl.item_parameter) -> dict:
    """PURE: ONE run log -> its record (see the module docstring). `lane` is its `ARMS.json` lane row (tag, slot, arm);
    `cut` / `lost` come from T1's records. `refused` is a reason or None; `excluded` a reason (a run that cannot enter
    the grade but is no instrument failure) or None, with `excluded_kind` naming which rule excluded it."""
    arm = bl.arm_of(lines, arms)
    header = bl.has_header(lines)
    ident = bl.run_identity(lines)
    capped = bl.log_capped(lines)
    status = "cut" if cut else "lost" if lost else "capped" if capped else "complete"
    battles = bl.split_battles(lines)
    first = bl.first_attempts(battles, KSTAR)
    met = bl.keys_met(battles, KSTAR)
    keys = {}
    for key in KEYS:
        fa = first[key]
        hp, unknown = bl.hp_item_count(fa["heal_stock"], param_of) if fa else (None, [])
        won = None if fa is None or fa["outcome"] not in ("won", "lost") else fa["outcome"] == "won"
        keys[key] = {"reached": key in met, "attempted": fa is not None, "outcome": fa["outcome"] if fa else None,
                     "won": won, "hp": hp, "hp_unknown": unknown}
    telemetry = bl.has_trainer_telemetry(lines)
    nonkey = collections.Counter({"won": 0, "lost": 0, "other": 0})
    for battle in battles:
        if bl.battle_class(battle, telemetry) == bl.NONKEY:
            nonkey[bl.outcome_bucket(battle)] += 1
    refused = excluded = kind = None
    species, chosen = ident["species"], ident["chosen"]
    if (cut or lost) and not header:
        # DECISION F11 (SPEC-SILENT before it): a log the deadline cut — or a dying spawn left — before its header
        # was written holds no run at all; refusing it would void a 13-hour grade over an empty file.
        excluded, kind = "cut or lost before its run header was written", "no_header"
    elif arm != lane.get("arm"):
        refused = f"env-all reads arm {arm!r}; the lane's ARMS.json arm is {lane.get('arm')!r}"
    elif species is None:
        # SPEC-SILENT: a run with no starter cannot be stratified, so it is EXCLUDED and listed (normally a run cut
        # seconds after it began, before any trainer; the RUNS table still shows anything it did fight).
        # ⛔ KI-119 DECISION (`#27-gradeidentity`; supersedes T23-PREDICTIONS.md:49-50): a log with NO choosing line is
        # no_starter too — its identity is never read from an earlier `[hb]` (`battle_log.run_identity`)
        excluded, kind = "no starter read (no non-empty [hb] after 'Story: choosing X!')", "no_starter"
    elif species not in STARTERS:
        excluded, kind = f"species {species!r} is not one of the three starters (DECISION F8)", "not_a_starter"
    elif chosen != species:
        excluded, kind = (f"species {species!r} disagrees with its 'Story: choosing {chosen}!' line (DECISION F8)",
                          "chosen_mismatch")
    return {"log": log, "lane": lane.get("tag"), "slot": lane.get("slot"), "lane_arm": lane.get("arm"), "arm": arm,
            "refused": refused, "excluded": excluded, "excluded_kind": kind, "species": species, "pid": ident["pid"],
            "hold": ident["hold"], "chosen": chosen, "status": status, "capped": capped, "header": header,
            "keys": keys, "nonkey": dict(nonkey), "choosing_lines": bl.choosing_lines(lines)}   # GS-6's control


def usable(run: dict) -> bool:
    return not run["refused"] and not run["excluded"]


def run_c1(run: dict) -> "float | None":
    """C1's per-run value: the mean HP-item count over the run's K* FIRST attempts whose `heal_stock` was readable
    (`heal_stock=-` is 0; a missing or unreadable field is excluded and counted). None with no such attempt."""
    vals = [k["hp"] for k in run["keys"].values() if k["attempted"] and k["hp"] is not None]
    return sum(vals) / len(vals) if vals else None


def censored_during(run: dict, key: str) -> bool:
    """True for a run CENSORED (cut, lost or capped) DURING its first attempt at `key`: it met the trainer and has no
    won/lost first attempt. DECISION F10 / RC-2 — THE CHOSEN READING of DESIGN §5's "a run cut by the deadline
    contributes only the first attempts it completed": such a run leaves the trainer's reach AND composite
    denominators (it was never observed to win or lose there), exactly like a cut run that never met the trainer.
    (Capped is censored like cut: DESIGN T2(c) reports a capped tail "as cut".)"""
    k = run["keys"][key]
    return run["status"] != "complete" and k["reached"] and k["won"] is None


def lost_logs(names, spawns) -> set:
    """The log a DYING spawn had open: for every spawn that ended neither by x4h's own stop nor with exit 0, the newest
    log (by its name's local timestamp) created during that spawn. Spawn times are epoch seconds (`time.time()` in
    `x4_headless`); a log name carries the local time it was opened (`…-debug-YYYYMMDD-HHMMSS.log`)."""
    stamps = {}
    for name in names:
        m = re.search(r"debug-(\d{8}-\d{6})\.log$", name)
        if m:
            stamps[name] = datetime.datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").timestamp()
    out = set()
    for sp in spawns or []:
        if sp.get("end") is None or sp.get("stopped_by") == "x4h" or sp.get("exit") == 0:
            continue
        # A name's stamp is FLOORED to the second, so a log opened in the spawn's first second may read up to 1 s
        # before `start`; nothing it opened can be stamped after `end` (and the RESTART's first log can be one second
        # later, so there is no slack there — the gate's CR3 pins exactly that).
        inside = [n for n, t in stamps.items() if sp.get("start", 0) - 2 <= t <= sp["end"]]
        if inside:
            out.add(max(inside, key=lambda n: (stamps[n], n)))
    return out


# ---------------------------------------------------------------------------------------------------- the batch (pure)
def void_reason(summary: "dict | None", manual: "str | None" = None) -> "str | None":
    """DESIGN §4 / DECISION F1: why C1-C2 are VOID, or None. A `--void` (a manual STOP-3 park) always voids; else a
    summary.json verdict "FAILED — <abort>" voids when the abort is an automated STOP (`AUTOMATED_STOPS`) or an
    "x4h error". A user park (`USER_PARK`) does NOT void ("a user park stands"); an "OK" or "OK — DEGRADED" verdict
    does not. SPEC-SILENT, fail-closed: a FAILED verdict this list does not know also voids."""
    if manual:
        return f"STOP-3 (manual --void): {manual}"
    verdict = (summary or {}).get("verdict") or ""
    if not verdict.startswith("FAILED"):
        return None
    abort = verdict.split("—", 1)[1].strip() if "—" in verdict else ((summary or {}).get("stop_reason") or "")
    if abort == USER_PARK:
        return None
    if abort in AUTOMATED_STOPS or abort.startswith("x4h error"):
        return f"STOP {abort}"
    return f"STOP (an unrecognised FAILED verdict: {verdict!r})"


def preregistered_delta(manifest: dict) -> "float | None":
    """DECISION F6: the pre-registered δ for the design T1 recorded (`lanes_n`, else the lane count; the arm count)."""
    raw = manifest.get("raw") or {}
    lanes_n = raw.get("lanes_n") or len(manifest.get("lanes") or [])
    return PREREG_DELTA.get((lanes_n, len(manifest.get("arms") or {})))


def exploratory_reasons(draws: int, seed: int, delta: float, prereg: "float | None") -> list:
    """DECISION F6: every analysis choice that differs from the pre-registered one (DESIGN §4: "no read may change δ
    … or any analysis choice"). Non-empty -> C1 and C2 are EXPLORATORY."""
    out = []
    if draws != DEFAULT_DRAWS:
        out.append(f"draws {draws} (pre-registered {DEFAULT_DRAWS})")
    if seed != DEFAULT_SEED:
        out.append(f"seed {seed} (pre-registered {DEFAULT_SEED})")
    if prereg is None:
        out.append(f"δ {delta} (this design has no pre-registered δ)")
    elif delta != prereg:
        out.append(f"δ {delta} (pre-registered {prereg})")
    return out


def grader_revision_reasons(started, stamp=None, code_commit=None) -> "tuple[list, list]":
    """`#27-gradeidentity`, FAIL-CLOSED: (EXPLORATORY reasons, OPERATIVE notes) for a batch, by its ARMS.json `started`
    (local ISO, second precision), `stamp` and `code_commit`. Each grader revision (`GRADER_REVISIONS`) the batch did
    not start strictly AFTER is a reason its grade is not the one designed: an EXPLORATORY reason — or, when the
    recorded user ruling keyed by EXACTLY this (stamp, code_commit, started) names that revision's ID
    (`GRADER_RULINGS`), an OPERATIVE note that keeps the revision visible."""
    when = at_second(started)
    key = (stamp, code_commit, started)
    ruling = GRADER_RULINGS.get(key) if all(isinstance(x, str) for x in key) else None
    exploratory, operative = [], []
    for rev in GRADER_REVISIONS:
        if when is not None and when > at_second(rev["at"]):
            continue                          # the batch's data began AFTER this revision: graded as designed
        since = (f"started {started}" if when is not None
                 else "its start is unknown: ARMS.json has no 'started' at second precision")
        text = f"graded by a grader revised after the batch ({since}; revision {rev['id']} at {rev['at']}: {rev['what']})"
        if ruling is not None and rev["id"] in ruling["revisions"]:
            operative.append(f"OPERATIVE BY {ruling['ruling']} — {text} [{ruling['why']}]")
        else:
            exploratory.append(text)
    return exploratory, operative


def completeness_failures(lanes, logs_per_lane: dict, summary: "dict | None", live: bool, tag=None) -> list:
    """DECISION F4 / RC-1: why the logs read are NOT the whole batch (each an instrument failure: exit 1, no grade).
    Every ARMS.json lane must yield a log. From a batch DIRECTORY (not live: the profiles hold every log), the
    collection must have finished — not interrupted, not only the PROVISIONAL summary — and each lane's logs read must
    equal summary.json's `debug_logs_collected` when it is there. The recovery path is the lane profiles: `--tag`."""
    out = []
    hint = f"grade from the lane profiles instead: compare_arms.py --tag {tag or '<profile_tag>'}"
    if not live and summary is not None:
        if summary.get("collect_interrupted"):
            out.append(f"log collection was INTERRUPTED (summary.json collect_interrupted): the batch directory is "
                       f"INCOMPLETE — {hint}")
        if summary.get("provisional"):
            # SPEC-SILENT (the same rule): only the provisional summary exists, so the collection never finished.
            out.append(f"summary.json is the PROVISIONAL one (written before log collection): the batch directory may "
                       f"be INCOMPLETE — {hint}")
    for ln in lanes:
        n = logs_per_lane.get(ln["tag"], 0)
        if n == 0:
            out.append(f"lane {ln['tag']} (arm {ln.get('arm')}) yielded ZERO logs")
        elif not live and summary is not None:
            want = ((summary.get("lanes") or {}).get(ln["tag"]) or {}).get("debug_logs_collected")
            if want is not None and n != want:
                out.append(f"lane {ln['tag']}: {n} log(s) read, summary.json says {want} collected — {hint}")
    return out


def controls(runs, arm_names=(ARM_A, ARM_B), completeness=()) -> "tuple[list, dict]":
    """(failures, info). An instrument control FAILS on: zero runs; any refused log; an arm with no usable run; any
    `completeness` failure (`completeness_failures`)."""
    failures = list(completeness)
    if not runs:
        failures.append("ZERO runs: no log was read")
    refused = [r for r in runs if r["refused"]]
    if refused:
        failures.append(f"{len(refused)} REFUSED log(s): the header's arm disagrees with the lane's ARMS.json arm")
    per_arm = collections.Counter(r["arm"] for r in runs if usable(r))
    for arm in arm_names:
        if not per_arm.get(arm):
            failures.append(f"arm {arm} has NO usable runs")
    # DECISION F9: a COMPLETE run that never got a starter is out of every denominator; DESIGN's funnel starts at
    # "runs started", so the count is reported per arm.
    no_starter = collections.Counter(r["arm"] for r in runs
                                     if r.get("excluded_kind") == "no_starter" and r["status"] == "complete")
    # GS-6 (KI-119): a CONTROL, never a failure — every read log whose count of choosing lines is not exactly 1
    choosing = [(r["log"], r["choosing_lines"]) for r in runs
                if r.get("choosing_lines") is not None and r["choosing_lines"] != 1]
    info = {"runs": len(runs), "refused": [(r["log"], r["refused"]) for r in refused],
            "excluded": [(r["log"], r["excluded"]) for r in runs if r["excluded"]],
            "usable_per_arm": dict(per_arm), "complete_no_starter_per_arm": dict(no_starter),
            "choosing_not_one": choosing}
    return failures, info


# ---------------------------------------------------------------------------------------------------- the statistics
def build_strata(runs) -> dict:
    """(arm, species) -> {"keys": [cluster keys], "C": n, <FIELDS_K>: (C, K), <FIELDS_1>: (C,)}. One cluster per
    (arm, species, PID): every run of a cluster is SUMMED into it, so the bootstrap resamples it whole (DESIGN §5:
    resampled together, NEVER de-duplicated)."""
    K = len(KEYS)
    acc: dict = {}
    for r in runs:
        stratum = acc.setdefault((r["arm"], r["species"]), {})
        c = stratum.get((r["arm"], r["species"], r["pid"]))
        if c is None:
            c = {**{f: [0.0] * K for f in FIELDS_K}, **{f: 0.0 for f in FIELDS_1}}
            stratum[(r["arm"], r["species"], r["pid"])] = c
        for j, key in enumerate(KEYS):
            k = r["keys"][key]
            if k["won"] is not None:
                c["N"][j] += 1
                c["W"][j] += 1 if k["won"] else 0
            if censored_during(r, key):
                continue          # DECISION F10: out of X's reach and composite denominators (`censored_during`)
            if k["reached"]:
                c["RN"][j] += 1
                c["RD"][j] += 1
                c["CN"][j] += 1 if k["won"] is True else 0
            elif r["status"] == "complete":
                # ⛔ REACH CENSORING: only a COMPLETE run that never met X says "did not reach X". A cut, lost or
                # capped run that never met X is out of the denominator: its tail was never observed.
                c["RD"][j] += 1
        v = run_c1(r)
        if v is not None:
            c["H"] += v
            c["Hn"] += 1
        c["L5"] += r["nonkey"]["lost"]
        c["B5"] += r["nonkey"]["won"] + r["nonkey"]["lost"]
        c["NR"] += 1
    out = {}
    for skey, stratum in acc.items():
        cl = list(stratum.values())
        out[skey] = {"keys": list(stratum), "C": len(cl),
                     **{f: np.array([c[f] for c in cl], dtype=float) for f in FIELDS_K + FIELDS_1}}
    return out


def resample_sums(strata: dict, draws: int, rng) -> dict:
    """(arm, species) -> {field: weighted sums}, leading dim D. `rng` None -> the POINT estimate (every cluster once,
    D = 1); else D = `draws` rows of multinomial cluster counts, drawn WITHIN each stratum (with replacement)."""
    out = {}
    for skey in sorted(strata, key=lambda k: (str(k[0]), str(k[1]))):
        st = strata[skey]
        C = st["C"]
        if rng is None:
            wt = np.ones((1, C))
        else:
            wt = rng.multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)
        out[skey] = {f: wt @ st[f] for f in FIELDS_K + FIELDS_1}
    return out


def _nanmean(x, axis=1):
    ok = ~np.isnan(x)
    n = ok.sum(axis=axis)
    s = np.where(ok, x, 0.0).sum(axis=axis)
    return np.where(n > 0, s / np.where(n > 0, n, 1), np.nan)


def _ratio(num, den):
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)


def statistics(sums: dict, species, a: str = ARM_A, b: str = ARM_B) -> dict:
    """EVERY statistic of DESIGN §5 from per-stratum sums (leading dim D: 1 for the point estimate, `draws` for the
    bootstrap). ONE implementation of the estimand for both, so the CI is always the CI of the statistic reported."""
    D = next(iter(sums.values()))["NR"].shape[0]
    K = len(KEYS)

    def g(arm, sp, f):
        s = sums.get((arm, sp))
        if s is not None:
            return s[f]
        return np.zeros((D, K)) if f in FIELDS_K else np.zeros(D)

    out = {}
    # C2 — p[a,X,s] = W/N; species weighted equally among those with a decided first attempt in BOTH arms.
    num = {a: np.zeros((D, K)), b: np.zeros((D, K))}
    cnt = np.zeros((D, K))
    for sp in species:
        na, nb = g(a, sp, "N"), g(b, sp, "N")
        ok = (na > 0) & (nb > 0)
        num[a] += np.where(ok, _ratio(g(a, sp, "W"), na), 0.0)
        num[b] += np.where(ok, _ratio(g(b, sp, "W"), nb), 0.0)
        cnt += ok
    px = {arm: _ratio(num[arm], cnt) for arm in (a, b)}
    out["pX_a"], out["pX_b"] = px[a], px[b]
    out["pX_diff"] = px[b] - px[a]
    # ⛔ DECISION F2: θ is the mean over the FROZEN K* (DESIGN §5: "never re-derived from step 14's data"). A row —
    # the point or one draw — in which ANY K* trainer is not estimable has NO θ (a plain mean propagates the NaN);
    # averaging the estimable subset would reopen S1's truncation by death.
    out["theta_a"], out["theta_b"] = px[a].mean(axis=1), px[b].mean(axis=1)
    out["delta"] = out["theta_b"] - out["theta_a"]
    out["n_estimable"] = (cnt > 0).sum(axis=1).astype(float)
    for gname, members in GROUPS.items():
        cols = [KEYS.index(k) for k in members]
        # the same frozen rule per group: every one of the group's K* trainers, or no group θ
        out[f"group_{gname}"] = px[b][:, cols].mean(axis=1) - px[a][:, cols].mean(axis=1)
    # REACH — a pooled ratio of sums per arm over the runs not censored before X.
    rn = {arm: sum(g(arm, sp, "RN") for sp in species) for arm in (a, b)}
    rd = {arm: sum(g(arm, sp, "RD") for sp in species) for arm in (a, b)}
    out["reach_a"], out["reach_b"] = _ratio(rn[a], rd[a]), _ratio(rn[b], rd[b])
    out["reach_diff"] = out["reach_b"] - out["reach_a"]
    # COMPOSITE — P(met X and won the first attempt) over the reach denominator, species-weighted as C2 (among the
    # species with such runs in BOTH arms), then the mean over the K* trainers that have such a denominator.
    cnum = {a: np.zeros((D, K)), b: np.zeros((D, K))}
    ccnt = np.zeros((D, K))
    for sp in species:
        da, db = g(a, sp, "RD"), g(b, sp, "RD")
        ok = (da > 0) & (db > 0)
        cnum[a] += np.where(ok, _ratio(g(a, sp, "CN"), da), 0.0)
        cnum[b] += np.where(ok, _ratio(g(b, sp, "CN"), db), 0.0)
        ccnt += ok
    out["comp_a"] = _nanmean(_ratio(cnum[a], ccnt))
    out["comp_b"] = _nanmean(_ratio(cnum[b], ccnt))
    out["comp_diff"] = out["comp_b"] - out["comp_a"]
    # C1 — the mean over runs of each run's mean (a ratio of sums over clusters).
    for arm, tag in ((a, "a"), (b, "b")):
        out[f"c1_{tag}"] = _ratio(sum(g(arm, sp, "H") for sp in species), sum(g(arm, sp, "Hn") for sp in species))
        out[f"c5_{tag}"] = _ratio(sum(g(arm, sp, "L5") for sp in species), sum(g(arm, sp, "B5") for sp in species))
    out["c1_diff"] = out["c1_b"] - out["c1_a"]
    out["c5_diff"] = out["c5_b"] - out["c5_a"]
    return out


def ci(draws, level: float) -> "tuple[float, float]":
    """The percentile CI of `draws` (NaN draws dropped: a draw in which the statistic is undefined); (nan, nan) when
    every draw is NaN."""
    d = np.asarray(draws, dtype=float)
    d = d[~np.isnan(d)]
    if d.size == 0:
        return math.nan, math.nan
    lo, hi = np.percentile(d, [50 - level / 2, 50 + level / 2])
    return float(lo), float(hi)


def c2_reading(lo95: float, hi95: float, delta: float) -> str:
    """DESIGN §5 step 2's verdict word from the two-sided 95% CI of Δ. Strict inequalities ("above", "below")."""
    if not (math.isfinite(lo95) and math.isfinite(hi95)):
        return "NOT ESTIMABLE"
    if lo95 > 0:
        return "HIGHER"
    if lo95 > -delta:
        return "NOT LOWER, but statistically lower" if hi95 < 0 else "NOT LOWER"
    return "INCONCLUSIVE"


def c5_flag(lo90: float, hi90: float) -> "str | None":
    """C5's harm flag from the two-sided 90% CI of B − A (one-sided α = .05). None = no flag (NOT "no harm")."""
    if lo90 > 0:
        return "REGRESSION"
    if hi90 < 0:
        return "IMPROVED"
    return None


def status_of(reasons) -> "tuple[str, str | None]":
    """(status text, verdict word) from the ORDERED non-confirmatory reasons [(word, text)]: ("CONFIRMATORY", None)
    with none; else the first reason's label ("DESCRIPTIVE" for VOID / NOT ESTIMABLE / C1, "PROVISIONAL",
    "EXPLORATORY") followed by EVERY reason, and the first reason's word as the verdict (DECISION F7).
    `#27-gradeidentity`: an OPERATIVE note (a grader revision a recorded user ruling made operative) is no reason
    against the verdict — with ONLY such notes the status is their text and the verdict stays the rule's word; beside
    any other reason it is listed, and that reason labels the status."""
    if not reasons:
        return "CONFIRMATORY", None
    hard = [r for r in reasons if r[0] != "OPERATIVE"]
    if not hard:
        return "; ".join(text for _w, text in reasons), None
    word = hard[0][0]
    label = word if word in ("PROVISIONAL", "EXPLORATORY") else "DESCRIPTIVE"
    return f"{label} — " + "; ".join(text for _w, text in reasons), word


def _f(x) -> "float | None":
    x = float(x)
    return x if math.isfinite(x) else None


def grade(runs, *, draws: int = DEFAULT_DRAWS, seed: int = DEFAULT_SEED, delta: float = PREREG_DELTA[(16, 2)],
          a: str = ARM_A, b: str = ARM_B, void: "str | None" = None, provisional: bool = False,
          exploratory=(), operative=()) -> dict:
    """PURE (numpy): the full §5 grade of the USABLE runs of arms `a` and `b`. `void` / `provisional` /
    `exploratory` are the batch-level reasons C1-C2 cannot be confirmatory (`void_reason`, no summary.json,
    `exploratory_reasons` + `grader_revision_reasons`); `operative` the OPERATIVE notes (`grader_revision_reasons`),
    which name a recorded user ruling and leave the verdict the rule's word. JSON-ready (NaN -> None)."""
    runs = [r for r in runs if usable(r) and r["arm"] in (a, b)]
    if not runs:
        raise ValueError("grade() needs usable runs; `controls` fails first on a batch without them")
    species = sorted({r["species"] for r in runs})
    strata = build_strata(runs)
    pt = statistics(resample_sums(strata, 0, None), species, a, b)
    bs = statistics(resample_sums(strata, draws, np.random.default_rng(seed)), species, a, b)

    def one(name, j=None):
        p = pt[name][0] if j is None else pt[name][0, j]
        d = bs[name] if j is None else bs[name][:, j]
        return {"point": _f(p), "ci95": [_f(x) for x in ci(d, 95)], "ci90": [_f(x) for x in ci(d, 90)],
                "nan_draws": int(np.isnan(d).sum())}

    def nz(v):
        return v if v is not None else math.nan

    batch_reasons = []
    if void:
        batch_reasons.append(("VOID", f"VOID: {void} (DESIGN §4)"))
    if provisional:
        batch_reasons.append(("PROVISIONAL", "PROVISIONAL: a LIVE read with no summary.json (the batch is running)"))
    if exploratory:
        batch_reasons.append(("EXPLORATORY", "EXPLORATORY: " + ", ".join(exploratory)))
    for note in operative:
        batch_reasons.append(("OPERATIVE", note))
    c1 = one("c1_diff")
    c1_pass = nz(c1["ci95"][0]) > 0
    c1_rule = "NOT ESTIMABLE" if c1["point"] is None else "PASS" if c1_pass else "FAIL"     # RC-3
    c1_status, c1_word = status_of(batch_reasons + ([("NOT ESTIMABLE", "C1 NOT ESTIMABLE")]
                                                    if c1_rule == "NOT ESTIMABLE" else []))
    c2 = one("delta")
    lo95, hi95 = nz(c2["ci95"][0]), nz(c2["ci95"][1])
    n_est = int(pt["n_estimable"][0])
    # DECISION F2: fewer than all 7 estimable at the POINT -> the rule cannot be applied over the frozen K*
    reading = (c2_reading(lo95, hi95, delta) if n_est == len(KEYS)
               else f"NOT ESTIMABLE over the frozen K* ({n_est} of {len(KEYS)})")
    c2_reasons = list(batch_reasons)
    if n_est < len(KEYS):
        c2_reasons.append(("NOT ESTIMABLE", reading))
    if not c1_pass:
        c2_reasons.append(("DESCRIPTIVE", "C1 NOT ESTIMABLE" if c1_rule == "NOT ESTIMABLE" else "C1 did not pass"))
    c2_status, c2_word = status_of(c2_reasons)
    c5 = one("c5_diff")
    trainers = {}
    for j, key in enumerate(KEYS):
        r = one("reach_diff", j)
        lo, hi = nz(r["ci90"][0]), nz(r["ci90"][1])
        trainers[key] = {
            "p_a": _f(pt["pX_a"][0, j]), "p_b": _f(pt["pX_b"][0, j]), "p_diff": one("pX_diff", j),
            "reach_a": _f(pt["reach_a"][0, j]), "reach_b": _f(pt["reach_b"][0, j]), "reach_diff": r,
            "reach_differs": bool(lo > 0 or hi < 0),
            "fought": {arm: sum(1 for x in runs if x["arm"] == arm and x["keys"][key]["won"] is not None)
                       for arm in (a, b)},
            "won_first": {arm: sum(1 for x in runs if x["arm"] == arm and x["keys"][key]["won"] is True)
                          for arm in (a, b)},
            "reach_n": {arm: int(sum(st["RD"][:, j].sum() for (arm2, _s), st in strata.items() if arm2 == arm))
                        for arm in (a, b)},
            "censored_during": {arm: [x["log"] for x in runs if x["arm"] == arm and censored_during(x, key)]
                                for arm in (a, b)},
        }
    groups = {}
    for gname in GROUPS:
        gr = one(f"group_{gname}")
        groups[gname] = {**gr, "lower_flag": bool(nz(gr["ci90"][1]) < 0)}
    reach_differs = sorted(k for k, t in trainers.items() if t["reach_differs"])
    clusters = collections.Counter(arm for (arm, _s) in strata for _ in strata[(arm, _s)]["keys"])
    return {
        "arms": [a, b], "draws": draws, "seed": seed, "delta_margin": delta, "species": species,
        "void": void, "provisional": provisional, "exploratory": list(exploratory), "operative": list(operative),
        "runs_per_arm": dict(collections.Counter(r["arm"] for r in runs)), "clusters_per_arm": dict(clusters),
        "species_per_arm": {arm: dict(collections.Counter(r["species"] for r in runs if r["arm"] == arm))
                            for arm in (a, b)},
        "status_per_arm": {arm: dict(collections.Counter(r["status"] for r in runs if r["arm"] == arm))
                           for arm in (a, b)},
        "c1": {**c1, "a": _f(pt["c1_a"][0]), "b": _f(pt["c1_b"][0]), "pass": bool(c1_pass), "rule_reading": c1_rule,
               "status": c1_status, "verdict": c1_rule if c1_word is None else c1_word,
               "runs_with_value": {arm: sum(1 for r in runs if r["arm"] == arm and run_c1(r) is not None)
                                   for arm in (a, b)}},
        "c2": {**c2, "theta_a": _f(pt["theta_a"][0]), "theta_b": _f(pt["theta_b"][0]), "rule_reading": reading,
               "rule_not_lower": bool(lo95 > -delta), "status": c2_status,
               "verdict": reading if c2_word is None else c2_word,
               "lower_flag": bool(nz(c2["ci90"][1]) < 0), "n_estimable": n_est, "reach_differs": reach_differs},
        "reach_differs": reach_differs,
        "composite": {**one("comp_diff"), "a": _f(pt["comp_a"][0]), "b": _f(pt["comp_b"][0])},
        "c5": {**c5, "a": _f(pt["c5_a"][0]), "b": _f(pt["c5_b"][0]),
               "flag": c5_flag(nz(c5["ci90"][0]), nz(c5["ci90"][1])),
               "lost": {arm: sum(r["nonkey"]["lost"] for r in runs if r["arm"] == arm) for arm in (a, b)},
               "battles": {arm: sum(r["nonkey"]["won"] + r["nonkey"]["lost"] for r in runs if r["arm"] == arm)
                           for arm in (a, b)},
               "undecided": {arm: sum(r["nonkey"]["other"] for r in runs if r["arm"] == arm) for arm in (a, b)}},
        "groups": groups, "trainers": trainers,
    }


# ---------------------------------------------------------------------------------------------------- the report
def _n(x, fmt="+.3f"):
    return "n/a" if x is None else format(x, fmt)


def _ci_text(c, nan_draws=0, fmt="+.3f"):
    """`[lo, hi]`, plus the undefined-draw count when there is one (DECISION F5: never silently dropped)."""
    return f"[{_n(c[0], fmt)}, {_n(c[1], fmt)}]" + (f" ({nan_draws} draws undefined, excluded)" if nan_draws else "")


def render(header: dict, runs, failures, info, result) -> list:
    """The text report. With `failures`, the controls are printed and NO statistic (exit 1)."""
    out = ["=" * 100,
           "DESIGN v2 STEP 14 — compare_arms (T3): B − A",
           "⛔ A MEASUREMENT. A non-significant result is NOT confirmation; a missing harm flag is NOT 'no harm'.",
           "=" * 100]
    for k, v in header.items():
        out.append(f"  {k:<14}{v}")
    out.append("")
    out.append("INSTRUMENT CONTROLS")
    out.append(f"  logs read: {info['runs']}   usable runs per arm: {info['usable_per_arm']}")
    out.append(f"  REFUSED (header arm ≠ the lane's ARMS.json arm): {len(info['refused'])}")
    for log, why in info["refused"]:
        out.append(f"    ⛔ {log}: {why}")
    out.append(f"  excluded (not refused): {len(info['excluded'])}")
    for log, why in info["excluded"]:
        out.append(f"    - {log}: {why}")
    out.append(f"  COMPLETE runs that never got a starter (out of every denominator), per arm: "
               f"{info.get('complete_no_starter_per_arm') or 'none'}")
    odd = info.get("choosing_not_one") or []
    out.append(f"  logs with != 1 'Story: choosing X!' line (the run's start, KI-119): {len(odd)}")
    out += [f"    - {pathlib.Path(log).name}: {n}" for log, n in odd]
    unread = sum(1 for r in runs if usable(r) for k in r["keys"].values() if k["attempted"] and k["hp"] is None)
    unknown = sorted({n for r in runs for k in r["keys"].values() for n in k["hp_unknown"]})
    undecided = sum(1 for r in runs if usable(r) for k in r["keys"].values() if k["attempted"] and k["won"] is None)
    out.append(f"  K* first attempts with an unreadable/missing heal_stock (excluded from C1): {unread}; item names "
               f"the item data does not know: {unknown or 'none'}; first attempts with no won/lost outcome "
               f"(excluded from C2): {undecided}")
    out.append("")
    out.append("RUNS (one log = one run)")
    for r in runs:
        mark = "REFUSED" if r["refused"] else "excluded" if r["excluded"] else ""
        firsts = " ".join(
            f"{key[:7]}:{'W' if k['won'] else 'L' if k['won'] is False else ('?' if k['attempted'] else ('m' if k['reached'] else '-'))}"
            f"{'' if k['hp'] is None else k['hp']}" for key, k in r["keys"].items())
        out.append(f"  {r['lane'] or '?':<4} {r['arm']:<3} {r['species'] or '?'}#{r['pid'] or '?':<8} "
                   f"hold={r['hold']:<3} {r['status']:<8} non-key W/L/? {r['nonkey']['won']}/{r['nonkey']['lost']}/"
                   f"{r['nonkey']['other']}  {firsts}  {pathlib.Path(r['log']).name} {mark}")
    out.append("  (per trainer: W/L = the first attempt's outcome, then its HP-item count; ? = an attempt with no "
               "won/lost outcome; m = met, no finished attempt; - = not met)")
    out.append("")
    if failures:
        out.append("⛔ INSTRUMENT CONTROL FAILED — NO GRADE (no statistic is computed or printed):")
        for f in failures:
            out.append(f"  ⛔ {f}")
        out.append("=" * 100)
        return out
    r = result
    a, b = r["arms"]
    out.append(f"THE DATA: runs {r['runs_per_arm']}; clusters (arm, species, PID) {r['clusters_per_arm']}; "
               f"species {r['species_per_arm']}; status {r['status_per_arm']}")
    out.append(f"  bootstrap: {r['draws']} draws, seed {r['seed']}, clusters resampled within arm × species; "
               f"percentile CIs; δ = {r['delta_margin']}")
    out.append("")
    c1 = r["c1"]
    out.append(f"C1 — the manipulation check (HP items held at K* first attempts; per run, then per arm)  "
               f"[{c1['status']}]")
    out.append(f"  A {_n(c1['a'], '.3f')}  B {_n(c1['b'], '.3f')}  (runs with a value {c1['runs_with_value']})   "
               f"B − A {_n(c1['point'])}  95% CI {_ci_text(c1['ci95'], c1['nan_draws'])}")
    then = ("C2 is DESCRIPTIVE" if c1["rule_reading"] != "PASS"
            else "the C1 -> C2 gate is open (C2's own status is below)")
    out.append(f"  → C1 {c1['rule_reading']}{' (lower95 > 0)' if c1['rule_reading'] == 'PASS' else ''}: {then}")
    out.append("")
    c2 = r["c2"]
    out.append(f"C2 — first-attempt win rate over the FROZEN K* ({c2['n_estimable']} of {len(KEYS)} trainers "
               f"estimable)  [{c2['status']}]")
    out.append(f"  θA {_n(c2['theta_a'], '.3f')}  θB {_n(c2['theta_b'], '.3f')}  Δ {_n(c2['point'])}  "
               f"95% CI {_ci_text(c2['ci95'], c2['nan_draws'])}  90% CI {_ci_text(c2['ci90'])}")
    word = (c2["rule_reading"] if c2["status"] == "CONFIRMATORY"
            else c2["status"] if c2["rule_reading"].startswith("NOT ESTIMABLE")
            else f"{c2['status']}. The rule reads '{c2['rule_reading']}'")
    reach = f"   ⚠ REACH DIFFERS ({', '.join(c2['reach_differs'])})" if c2["reach_differs"] else ""   # DECISION F3
    out.append(f"  → C2: {word}   (margin δ = {r['delta_margin']}){reach}")
    out.append(f"  C2 LOWER (harm flag, upper90 < 0): {'⛔ FLAGGED' if c2['lower_flag'] else 'no flag'}")
    out.append("")
    out.append(f"  {'trainer':<20}{'p A':>7}{'p B':>7}{'Δ':>8}  {'95% CI':<18}{'fought A/B':>12}{'won A/B':>9}"
               f"{'reach A':>9}{'reach B':>9}{'B − A':>8}  {'90% CI':<18}{'n A/B':>9}")
    for key, t in r["trainers"].items():
        out.append(f"  {key:<20}{_n(t['p_a'], '.3f'):>7}{_n(t['p_b'], '.3f'):>7}{_n(t['p_diff']['point']):>8}  "
                   f"{_ci_text(t['p_diff']['ci95']):<18}{str(t['fought'][a]) + '/' + str(t['fought'][b]):>12}"
                   f"{str(t['won_first'][a]) + '/' + str(t['won_first'][b]):>9}{_n(t['reach_a'], '.3f'):>9}"
                   f"{_n(t['reach_b'], '.3f'):>9}{_n(t['reach_diff']['point']):>8}  "
                   f"{_ci_text(t['reach_diff']['ci90']):<18}{str(t['reach_n'][a]) + '/' + str(t['reach_n'][b]):>9}"
                   f"{'  REACH DIFFERS' if t['reach_differs'] else ''}")
    cens = {key: t["censored_during"] for key, t in r["trainers"].items() if any(t["censored_during"].values())}
    out.append(f"  censored DURING a first attempt (out of that trainer's reach and composite, DECISION F10): "
               + ("; ".join(f"{key} " + ", ".join(f"{arm} {len(v)} ({', '.join(pathlib.Path(x).name for x in v)})"
                                                   for arm, v in d.items() if v) for key, d in cens.items())
                  if cens else "none"))
    out.append(f"  REACH: {'⚠ REACH DIFFERS at ' + ', '.join(r['reach_differs']) if r['reach_differs'] else 'no 90% CI excludes 0 (a WEAK check, DESIGN §6)'}")
    cp = r["composite"]
    out.append(f"  COMPOSITE P(met X and won the first attempt), species-weighted, mean over K*: A "
               f"{_n(cp['a'], '.3f')}  B {_n(cp['b'], '.3f')}  B − A {_n(cp['point'])}  95% CI "
               f"{_ci_text(cp['ci95'], cp['nan_draws'])}")
    out.append("")
    c5 = r["c5"]
    out.append("C5 — losses (Lost + Draw) per decided NON-KEY trainer battle (ratio of sums)")
    out.append(f"  A {c5['lost'][a]}/{c5['battles'][a]} = {_n(c5['a'], '.4f')}   B {c5['lost'][b]}/{c5['battles'][b]} = "
               f"{_n(c5['b'], '.4f')}   (undecided, not counted: {c5['undecided']})")
    out.append(f"  B − A {_n(c5['point'], '+.4f')}  90% CI {_ci_text(c5['ci90'], c5['nan_draws'], '+.4f')}"
               f"  → {c5['flag'] or 'no flag (its absence is NOT no harm)'}")
    out.append("")
    out.append("PER GROUP (descriptive): θB − θA over each group's K* trainers (all of them estimable, or n/a)")
    for gname, gr in r["groups"].items():
        out.append(f"  {gname:<11} {_n(gr['point'])}  95% CI {_ci_text(gr['ci95'], gr['nan_draws'])}  90% CI "
                   f"{_ci_text(gr['ci90'])}{'  LOWER (descriptive)' if gr['lower_flag'] else ''}")
    out.append("=" * 100)
    return out


# ---------------------------------------------------------------------------------------------------- I/O
def load_manifest(batch_dir: pathlib.Path) -> dict:
    """T1's `ARMS.json`: `{"arms": {name: env dict}, "lanes": [...], "raw": the manifest}`. ValueError if unusable."""
    raw = json.loads((batch_dir / "ARMS.json").read_text(encoding="utf-8"))
    arms = json.loads(raw["arms_text"])["arms"]
    lanes = raw["lanes"]
    if not isinstance(arms, dict) or not isinstance(lanes, list):
        raise ValueError("ARMS.json has no arms dict / lanes list")
    return {"arms": arms, "lanes": lanes, "raw": raw}


def load_summary(batch_dir: pathlib.Path) -> "dict | None":
    """`summary.json`'s per-lane records (`lanes_detail`, or the PROVISIONAL `lanes` dict written before log
    collection), its verdict, stop and completeness facts; None when there is none (a running batch)."""
    try:
        s = json.loads((batch_dir / "summary.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    detail = s.get("lanes_detail")
    if not isinstance(detail, dict):
        detail = s.get("lanes") if isinstance(s.get("lanes"), dict) else {}
    return {"lanes": detail, "verdict": s.get("verdict"), "stop_reason": s.get("stop_reason"),
            "lanes_lost": s.get("lanes_lost"), "collect_interrupted": bool(s.get("collect_interrupted")),
            "provisional": bool(s.get("provisional"))}


def collect_runs(batch_dir: pathlib.Path, tag: "str | None" = None, param_of=bl.item_parameter,
                 visit=None) -> "tuple[list, dict]":
    """Every log of the batch (or, with `tag`, of its RUNNING lanes) -> its run record. Returns (runs, facts); facts
    carry the logs found per ARMS.json lane tag (`logs_per_lane`) for the completeness controls. `visit(record, lines)`,
    when given, is called once per READ log right after its record is built, with the same lines (design v2 step 14 T4:
    `batch14_checks.py` reads each log ONCE through this loader instead of re-implementing it)."""
    man = load_manifest(batch_dir)
    by_slot = {ln["slot"]: ln for ln in man["lanes"]}
    by_profile = {ln["profile"]: ln for ln in man["lanes"]}
    paths = bl.live_logs(tag) if tag else bl.batch_logs(batch_dir)
    per_lane: dict = collections.defaultdict(list)
    for p in paths:
        if tag:
            d = p.parent.parent if p.parent.name == "Old" else p.parent
            lane = by_profile.get(d.parent.name)
        else:
            m = re.fullmatch(r"L(\d+)", p.parent.parent.name)
            lane = by_slot.get(int(m.group(1)) - 1) if m else None
        per_lane[lane["tag"] if lane else None].append((p, lane))
    summary = load_summary(batch_dir)
    runs = []
    for lane_tag, items in per_lane.items():
        names = sorted(p.name for p, _l in items)
        rec = (summary or {}).get("lanes", {}).get(lane_tag) or {}
        if summary is None:
            # SPEC-SILENT: a RUNNING batch has no cut record yet; each lane's NEWEST log is the run still open.
            cut_name = names[-1] if names else None
        else:
            cut_name = rec.get("cut_log")
        lost = lost_logs(names, rec.get("spawns"))
        for p, lane in sorted(items, key=lambda it: it[0].name):
            got = bl.try_read(p)
            if lane is None or got is None:
                runs.append({"log": str(p), "lane": None, "slot": None, "lane_arm": None, "arm": "?",
                             "refused": "no lane in ARMS.json for this directory" if lane is None else "unreadable log",
                             "excluded": None, "excluded_kind": None, "species": None, "pid": None, "hold": 0,
                             "chosen": None, "status": "complete", "capped": False, "header": False,
                             "keys": {k: {"reached": False, "attempted": False, "outcome": None, "won": None,
                                          "hp": None, "hp_unknown": []} for k in KEYS},
                             "nonkey": {"won": 0, "lost": 0, "other": 0}})
                continue
            runs.append(run_record(got[0], log=str(p), lane=lane, arms=man["arms"], cut=p.name == cut_name,
                                   lost=p.name in lost, param_of=param_of))
            if visit is not None:
                visit(runs[-1], got[0])
    runs.sort(key=lambda r: (r["slot"] if r["slot"] is not None else 10 ** 6, r["log"]))
    facts = {"manifest": man, "summary": summary, "logs": len(paths),
             "logs_per_lane": {t: len(v) for t, v in per_lane.items() if t is not None}}
    return runs, facts


def find_batch(arg: "str | None", tag: "str | None", ap) -> pathlib.Path:
    """The batch directory: `arg` as a path if it is a directory, else a stamp under the MAIN checkout's x4-runs; with
    `--tag` alone, the ONE batch whose ARMS.json has that `profile_tag`."""
    runs_root = bl.main_story_dev() / "x4-runs"
    if arg:
        p = pathlib.Path(arg)
        d = p if p.is_dir() else runs_root / arg
    else:
        hits = []
        for f in sorted(runs_root.glob("*/ARMS.json")):
            try:
                if json.loads(f.read_text(encoding="utf-8")).get("profile_tag") == tag:
                    hits.append(f.parent)
            except (OSError, ValueError):
                continue
        if len(hits) != 1:
            ap.error(f"--tag {tag}: {len(hits)} batches under {runs_root} carry that profile_tag "
                     f"({[h.name for h in hits]}); name the batch directory as well")
        d = hits[0]
    if not (d / "ARMS.json").is_file():
        ap.error(f"{d.absolute()} has no ARMS.json (T1's start manifest): not an --arms batch")
    return d


def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="design v2 step 14 T3: grade an --arms batch (B − A, DESIGN §5).")
    ap.add_argument("batch", nargs="?", help="x4-runs/<stamp> under the MAIN checkout, or a batch directory path")
    ap.add_argument("--tag", help="LIVE: read a RUNNING batch's lane profiles (endless-<tag>-H*)")
    ap.add_argument("--draws", type=int, default=DEFAULT_DRAWS, help=f"bootstrap draws (default {DEFAULT_DRAWS})")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"bootstrap seed (default {DEFAULT_SEED})")
    ap.add_argument("--delta", type=float, default=None,
                    help="C2's margin δ (default: the PRE-REGISTERED one for the design in ARMS.json — 16 lanes x 2 "
                         "arms .08, 8 x 2 .11; any other value, or any other design, makes C1-C2 EXPLORATORY)")
    ap.add_argument("--void", metavar="REASON", help="a manual STOP (a STOP-3 park): C1 and C2 become DESCRIPTIVE — "
                                                     "VOID (DESIGN §4)")
    ap.add_argument("--json", metavar="OUT", help="also write the full grade as JSON")
    args = ap.parse_args(argv)
    if np is None:
        ap.error("numpy is required (py -3.12 -m pip install numpy)")
    if not args.batch and not args.tag:
        ap.error("give a batch (a stamp or a directory) or --tag")
    if args.draws < 1 or (args.delta is not None and not args.delta > 0):
        ap.error("--draws must be >= 1 and --delta > 0")
    batch_dir = find_batch(args.batch, args.tag, ap)
    try:
        runs, facts = collect_runs(batch_dir, args.tag)
    except (OSError, KeyError, ValueError, TypeError) as error:
        ap.error(f"{batch_dir / 'ARMS.json'} is not a usable T1 manifest: {type(error).__name__}: {error}")
    man = facts["manifest"]
    if not {ARM_A, ARM_B} <= set(man["arms"]):
        ap.error(f"ARMS.json arms {sorted(man['arms'])}: this grade compares {ARM_B} − {ARM_A}")
    prereg = preregistered_delta(man)
    delta = args.delta if args.delta is not None else prereg
    if delta is None:
        ap.error(f"this design ({man['raw'].get('lanes_n') or len(man['lanes'])} lanes, {len(man['arms'])} arms) has "
                 f"no pre-registered δ: give --delta (the grade is then EXPLORATORY)")
    summ = facts["summary"]
    void = void_reason(summ, args.void)
    exploratory = exploratory_reasons(args.draws, args.seed, delta, prereg)
    # ⛔ #27-gradeidentity, FAIL-CLOSED: a grader revised after the batch started makes C1-C2 EXPLORATORY, unless a
    # recorded user ruling for THIS batch made that revision's grade OPERATIVE (the status then says so)
    revised, operative = grader_revision_reasons(man["raw"].get("started"), man["raw"].get("stamp"),
                                                 man["raw"].get("code_commit"))
    exploratory += revised
    park = summ and (summ.get("verdict") or "").endswith(USER_PARK)
    header = {
        "source": (f"LIVE lanes endless-{args.tag}-H* under {bl.default_profiles().absolute()}" if args.tag
                   else f"batch {batch_dir.absolute()}"),
        "ARMS.json": f"{(batch_dir / 'ARMS.json').absolute()} (arms {sorted(man['arms'])}, sha256 "
                     f"{man['raw'].get('arms_sha256', '?')[:16]}…, commit {man['raw'].get('code_commit', '?')})",
        "batch": (f"verdict {summ['verdict']!r}; stop {summ['stop_reason']!r}; lanes lost {summ['lanes_lost'] or 'none'}"
                  + ("  (a user park STANDS, DESIGN §4)" if park else "")
                  if summ else "no summary.json (a RUNNING batch: each lane's newest log is CUT; C1-C2 PROVISIONAL)"),
        "C1-C2": (f"VOID: {void} (DESIGN §4)" if void else "not void"),
        "design": (f"{man['raw'].get('lanes_n') or len(man['lanes'])} lanes x {len(man['arms'])} arms; pre-registered δ "
                   f"{prereg if prereg is not None else 'NONE'}; used δ {delta}"
                   + (f"; EXPLORATORY: {', '.join(exploratory)}" if exploratory else "")
                   + (f"; {'; '.join(operative)}" if operative else "")),
        "grade": f"draws {args.draws}, seed {args.seed}, numpy {np.__version__}",
    }
    failures, info = controls(runs, completeness=completeness_failures(
        man["lanes"], facts["logs_per_lane"], summ, live=bool(args.tag), tag=man["raw"].get("profile_tag")))
    result = None if failures else grade(runs, draws=args.draws, seed=args.seed, delta=delta, void=void,
                                         provisional=summ is None, operative=operative, exploratory=exploratory)
    print("\n".join(render(header, runs, failures, info, result)))
    if args.json:
        slim = [{k: v for k, v in r.items()} for r in runs]
        pathlib.Path(args.json).write_text(json.dumps(_jsonable({
            "header": header, "controls": {"failures": failures, **info}, "runs": slim, "grade": result}),
            indent=2), encoding="utf-8")
        print(f"JSON written: {pathlib.Path(args.json).absolute()}")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
