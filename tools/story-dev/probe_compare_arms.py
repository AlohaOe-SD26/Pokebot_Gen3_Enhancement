r"""GATE G-CA — design v2 step 14's grading tools: T2 (`battle_log.py`'s run-level additions) and T3 (`compare_arms.py`).

WHY. Tonight's 13-hour batch is graded by these two files, and a grader that silently mis-reads a run, a cluster or a
verdict rule turns a night of data into a confident wrong answer. The spec (`ai-research-notes/2026-10-01-batch14-T23-
PREDICTIONS.md`) and its parent DESIGN §3 T3 / §5 fix every rule BEFORE the code; each row below pins one of them on
data whose expected value was derived BY HAND (or, for the statistical rows, against the spec's own pre-registered
bound), never copied from the code's output.

ROWS (each a function; a row that raises is red)
  CA1-CA10  the spec's rows, verbatim (`…-T23-PREDICTIONS.md`, "The gate").
            CA1-CA4 and CA8's planted half are STATISTICAL: synthetic runs with the real structure (`synth`), a FIXED
            seed list, and the spec's bound. They are slow (~15 s together) and are left out of the mutant runs.
  TB*       T2: `parse_env_all`, `arm_of`, `run_identity`, `log_capped`, `batch_logs` (any lane count), `x4_logs` and
            `live_logs` (the MAIN checkout), `resolve_sources` (zero logs is exit 2), `first_attempts`, `keys_met`.
  CR*       one run's record: status precedence, refusal vs exclusion, the non-key counts, `lost_logs`, the batch and
            live readers.
  CS*       the estimand on hand-built data: strata, species weighting, θ over the FROZEN K*, reach censoring, the
            composite, C1's per-run mean, and the WIRING of every verdict to its CI level.
  CK1       K* itself: the FROZEN decomp ids (re-read from opponents.h) and the three groups that partition it.
  CV*       the verdict functions at their boundaries (strict inequalities), and `ci`'s percentiles.
  CX*       the CLI: exit 0 / 1 / 2, the defaults (10,000 draws, seed 14, δ .08 on M-16), and NO statistic after a failed
            control.
  AH1-AH17  the INDEPENDENT mutant hunter's rows N1-N17 (`evidence/2026-10-01-batch14-T23-ADVERSARIAL.txt`), adopted;
            AH2 / AH3 / AH5 / AH10 / AH13 adapted where DECISION F2 or F10 changed the value they read.
  DV1-DV13  one row per coordinator DECISION on that pass (F1 the STOP void, F2 the frozen K*, F3 REACH DIFFERS on
            the C2 line, F4 completeness, F5 undefined draws printed, F6 the pre-registered δ / EXPLORATORY, F7 the
            JSON verdict, F8 the starter strata, F9 no-starter counts, F10 censored during a first attempt, F11 a lost
            headerless log, RC-3 C1 NOT ESTIMABLE).

THE SYNTHETIC MODEL (`synth`; spec: "8 lanes per arm, two per starter (the random lane's species drawn); 11-seed pools
per lane; same-species-PID replays; about 6 runs per lane; K* first-attempt rates from the baseline"):
  * 7 runs per lane: 6 COMPLETE + the lane's last run CUT at a random depth (§6's M-16: 56.6 runs per arm, 48.6
    completed, 45 clusters; this model gives ~45 clusters per arm);
  * a complete run meets every K* trainer with p .9, else only the three every baseline run met (reach 1.00);
  * ⭐ REPLAYS: a run whose (lane, species, seed) was seen before copies that seed's ROXANNE and BRAWLY outcomes and
    draws the later ones afresh ("same-PID runs diverge by the fifth key trainer in 13 of 14 groups", DESIGN §0, review
    S4/F1). The pool is shared by lane POSITION across the arms: A's lane i and B's lane i carry the same in-game name
    and so the same seed pool (DESIGN §2, review R10);
  * heal stock at a first attempt: A 0-2 HP items, B 1-3 (so C1 passes and C2 is confirmatory), unless a row plants
    otherwise.
  ⚠ MEASURED ON THIS MODEL (the builder, 2026-10-01): CA1 reads 309/400 = .772 (true SD of Δ .0278, 45.0 clusters per
  arm) and CA2 26/1000 — CA1 below §6's .82 (SD .026), which came from re-sampling the REAL baseline (per-species
  rates differ, and both pseudo-arms drew on one finite population). The spec gives only pooled rates, so this model's
  per-species rates are equal: the most variable case. The gap is the model's, not the estimator's: on this model the
  bootstrap SD is within ~5% of the true SD (calibration runs, scratch).
  ⚠ THE HEAVY ROWS ARE COARSE (measured once by the builder): the cluster, strata and species-weighting mutants (C01,
  C02, C03, C05, C06, C07) PASS all five of them; C22 (C2's word on the 90% CI) reddens only CA2 (52/1000) and C04
  (one cluster per draw) four of them. The estimand's details are pinned by the hand-built FAST rows (CA6, CS1-CS7).

THE LINES. Real lines are quoted VERBATIM in `QUOTES`; the PROVENANCE check (not a row: it guards the gate's data) re-reads
each at its cited line — in the committed spec, or in the 2026-10-01 16-lane smoke batch of the MAIN checkout (that
batch is not committed; on a machine without it those quotes are reported SKIPPED, never passed).

MUTANTS: source edits of `battle_log.py` / `compare_arms.py`, exec'd in memory (never written to disk), each with the
EXACT set of FAST rows it must turn red, written before its first run. Mention-only edits must turn NOTHING red.
COVERAGE fails if a fast row is in no mutant's set. They run in a PROCESS POOL (`--serial` for one process).
  B*/C* the builder's first 70 (C07 C19 C20 C36 C37 C45 re-anchored where the fold moved their code); H* the hunter's
  29 survivors, re-anchored; D* one REVERT per decision. THE FOLD'S FIRST RUN: 126 of 128 matched the sets written
  before it; the two misses were MY predictions (H40 also reddens DV5; D11 crashes the report, which reads the field)
  and are corrected beside them, with D11b added as D11's non-crashing form.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_compare_arms.py      (exit 1 on any failure; no ROM)
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import pathlib
import random
import sys
import tempfile
import time
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # run_gates sets PYTHONUTF8=1 anyway
    pass

import numpy as np  # noqa: E402

import battle_log  # noqa: E402,F401  (always read via sys.modules: a mutant is exec'd there)
import compare_arms  # noqa: E402,F401

NAMES = {"bl": "battle_log", "ca": "compare_arms"}
PATHS = {k: HERE / f"{v}.py" for k, v in NAMES.items()}


def BL():
    return sys.modules["battle_log"]


def CA():
    return sys.modules["compare_arms"]


#: The REAL arms (committed; `x4_headless --arms` read this file for the smoke batch and tonight's batch).
ARMS = json.loads((HERE / "arms" / "batch14.json").read_text(encoding="utf-8"))["arms"]
SPEC = REPO / "PROJECT KNOWLEDGE" / "ai-research-notes" / "2026-10-01-batch14-T23-PREDICTIONS.md"
SMOKE = None  # set in main(): the MAIN checkout's 16-lane smoke batch (read-only)

# ============================================================================================ the real lines
#: name -> (source, relative path or lane, line number, the line VERBATIM). `spec` = the committed spec file (the four
#: shapes it quotes); `L04` / `L07` = that lane's single debug log in the MAIN checkout's smoke batch 20261001-090649.
QUOTES = {
    "tr_end_532": ("spec", None, 30, "f58102 [TRAINER] end opp=532 class=0x32(PkMn_TRAINER) value=15 lvl_last=5 first=True base=300 res=Won money=3000->3300 delta=300 mult=1 heal_stock=- map=0,18"),
    "hold_7": ("spec", None, 31, "f2788 [STEP] 'Intro: holding 7f before confirming (RNG decorrelation)...'"),
    "choose_treecko": ("spec", None, 32, "f13041 [STEP] 'Story: choosing Treecko!'"),
    "tr_end_532_log": ("L04", None, 663, "f58102 [TRAINER] end opp=532 class=0x32(PkMn_TRAINER) value=15 lvl_last=5 first=True base=300 res=Won money=3000->3300 delta=300 mult=1 heal_stock=- map=0,18"),
    "hold_7_log": ("L04", None, 52, "f2788 [STEP] 'Intro: holding 7f before confirming (RNG decorrelation)...'"),
    "choose_treecko_log": ("L04", None, 284, "f13041 [STEP] 'Story: choosing Treecko!'"),
    "hb_empty": ("L04", None, 72, "f3601 [hb] mode=Story (ENDLESS RESET) state=10 controllable=False map=LITTLEROOT TOWN(0,0) pos=(-7, -7) party=[] ids=[] owned=0 balls=0 money=0 box=0 badges=0 msg='Intro: confirming the name and riding to Littleroot...'"),
    "hb_first": ("L04", None, 297, "f14401 [hb] mode=Story (ENDLESS RESET) state=4 controllable=False map=ROUTE 101(0,16) pos=(6, 13) party=['Treecko:L5'] ids=['Treecko#1304646B:L5:exp135'] owned=1 balls=0 money=3000 box=0 badges=0 msg='Received Treecko ♂.\\n\\nNature:\\xa0Bold | Ability:\\xa0Overgrow | Item:\\xa0- | IV\\xa0sum:\\xa072 | SV:\\xa06,295'"),
    "env_all_A": ("L07", None, 13, "    env-all:       {'POKEBOT_BOX_OVERFLOW_CATCH': '1', 'POKEBOT_MAINTAIN': '1', 'POKEBOT_R20_HUNTFIRST': '0', 'POKEBOT_R20_OPENFENCE': '0', 'POKEBOT_R20_TEAM6': '0', 'POKEBOT_R23_BALLRESTOCK': '0', 'POKEBOT_R24_CATCHHURT': '0', 'POKEBOT_R24_CATCHTRAIN': '0', 'POKEBOT_R24_NOFAINTBAIL': '0', 'POKEBOT_R24_OVERSURVIVAL': '0', 'POKEBOT_R25_CAP': '0', 'POKEBOT_R25_DMGAUDIT': '1', 'POKEBOT_R25_RARE': '0', 'POKEBOT_R25_WEAKEN': 'observe', 'POKEBOT_R25_WEAKEN_CALC': '1', 'POKEBOT_R26_KITTOPOFF': '0', 'POKEBOT_R27_DOUBLEITEMS': '0', 'POKEBOT_R27_KEYITEMS': '0'}"),
    # H7 (arm A, Treecko): Roxanne LOST, then WON — and the won battle's `[TRAINER] end` comes BEFORE its
    # `[BATTLE] ended` (an evolution intervened: Treecko -> Grovyle)
    "h7_started_1": ("L07", None, 3963, "f453155 [BATTLE] started hp=[('Nincada', 33, 33), ('Treecko', 35, 35), ('Zigzagoon', 19, 19), ('Whismur', 25, 25)]"),
    "h7_start_lost": ("L07", None, 3964, "f453155 [TRAINER] start opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 double=False two=False money=1368 heal_stock=Potion:2,Super_Potion:2,Full_Heal:1 map=11,3 enemy_alive=3"),
    "h7_ended_lost": ("L07", None, 4166, "f480710 [BATTLE] ended (outcome=BattleOutcome.Lost) party=['Nincada:L13', 'Treecko:L15', 'Zigzagoon:L5', 'Whismur:L6']"),
    "h7_end_lost": ("L07", None, 4169, "f480710 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Lost money=1368->1368 delta=0 mult=0 heal_stock=Full_Heal:1 map=11,3"),
    "h7_started_2": ("L07", None, 4265, "f486406 [BATTLE] started hp=[('Treecko', 37, 37), ('Zigzagoon', 19, 19), ('Nincada', 33, 33), ('Whismur', 25, 25)]"),
    "h7_start_won": ("L07", None, 4266, "f486406 [TRAINER] start opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 double=False two=False money=684 heal_stock=Full_Heal:1 map=11,3 enemy_alive=3"),
    "h7_end_won": ("L07", None, 4310, "f499537 [TRAINER] end opp=265 class=0x20(LEADER) value=25 lvl_last=15 first=True base=1500 res=Won money=684->2184 delta=1500 mult=1 heal_stock=Full_Heal:1 map=11,3"),
    "h7_ended_won": ("L07", None, 4319, "f501919 [BATTLE] ended (outcome=BattleOutcome.Won) party=['Grovyle:L16', 'Zigzagoon:L5', 'Nincada:L13', 'Whismur:L6']"),
}


def Q(name: str) -> str:
    return QUOTES[name][3]


def provenance() -> None:
    """Every quote is at its cited line, byte for byte (the spec: as a substring of that line, inside its backticks)."""
    spec_lines = SPEC.read_text(encoding="utf-8").splitlines()
    smoke = {}
    for lane in ("L04", "L07"):
        logs = sorted((SMOKE / lane / "debug-logs").glob("*.log")) if SMOKE else []
        smoke[lane] = logs[0].read_text(encoding="utf-8", errors="replace").splitlines() if len(logs) == 1 else None
    bad, skipped = [], []
    for name, (src, _rel, n, text) in QUOTES.items():
        if src == "spec":
            if text not in spec_lines[n - 1]:
                bad.append(f"{name} (spec:{n})")
        elif smoke[src] is None:
            skipped.append(name)
        elif smoke[src][n - 1] != text:
            bad.append(f"{name} ({src}:{n})")
    check("PROVENANCE every quoted line is at its cited line, byte for byte", not bad,
          f"{len(QUOTES) - len(skipped)} checked, mismatches {bad}" + (f"; SKIPPED (no smoke batch here) {skipped}"
                                                                        if skipped else ""))
    # the env-all quote must also be EXACTLY what the debug logger writes for arm A (`debug_logger.py:262-266`)
    check("PROVENANCE the arms file's A, rendered as the logger renders it, IS the real A header line",
          Q("env_all_A") == env_line(ARMS["A"]))


# ============================================================================================ helpers
FAILURES: list = []
ROWS: list = []
ROW_NAMES: set = set()
HEAVY: set = set()
TMP: dict = {}


def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def row(rid: str, label: str, heavy: bool = False):
    def deco(fn):
        ROWS.append((rid, label, fn))
        ROW_NAMES.add(rid)
        if heavy:
            HEAVY.add(rid)
        return fn
    return deco


def eq(got, want):
    return got == want, f"got {got!r}" + ("" if got == want else f" (want {want!r})")


def close(a, b, tol=1e-12):
    return a is not None and b is not None and abs(a - b) <= tol


def cli(argv) -> "tuple[int, str]":
    """(exit code, stdout) of `compare_arms.main`; an argparse exit is caught as its code."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = CA().main(argv)
        except SystemExit as stop:
            code = stop.code
    return code, buf.getvalue()


def render(runs, g) -> str:
    """The text report of a grade, with empty controls (the rows that read the report's wording)."""
    info = {"runs": len(runs), "refused": [], "excluded": [], "usable_per_arm": {}, "complete_no_starter_per_arm": {}}
    return "\n".join(CA().render({}, runs, [], info, g))


def env_line(env: dict) -> str:
    """The run header's `env-all:` line exactly as `debug_logger` writes it: `f"    {label:<14} {value}"` over a dict
    of the POKEBOT_* variables in sorted order."""
    return f"    {'env-all:':<14} {dict(sorted(env.items()))}"


def header(env, *, complete=True) -> list:
    out = ["=== DEBUG LOG START 2026-10-01T09:07:28 ===", "--- RUN HEADER (build, config, experiment) ---",
           "    build:         1f3872ac7a85 on branch main"]
    if env is not None:
        out.append(env_line(env))
    if complete:
        out.append("--- END RUN HEADER ---")
    return out


def hb(species, pid, frame=14401) -> str:
    """A non-empty `[hb]` line in the REAL shape (`hb_first`), with another species / PID."""
    return Q("hb_first").replace("f14401", f"f{frame}").replace("Treecko", species).replace("1304646B", pid)


def fight(frame, opp, cls, res, stock="-", end=True, ended=None) -> list:
    """One trainer battle in the real line shapes (`tr_end_532` / the H7 lines): started, `[TRAINER] start`, then (when
    `end`) `[BATTLE] ended` + `[TRAINER] end`."""
    out = [f"f{frame} [BATTLE] started hp=[('Treecko', 35, 35)]",
           f"f{frame} [TRAINER] start opp={opp} class={cls} value=25 lvl_last=15 first=True base=1500 double=False "
           f"two=False money=1368 heal_stock={stock} map=11,3 enemy_alive=3"]
    if end:
        out += [f"f{frame + 100} [BATTLE] ended (outcome=BattleOutcome.{ended or res}) party=['Treecko:L15']",
                f"f{frame + 100} [TRAINER] end opp={opp} class={cls} value=25 lvl_last=15 first=True base=1500 res={res} "
                f"money=1368->1368 delta=0 mult=0 heal_stock={stock} map=11,3"]
    return out


LEADER, RIVAL, YOUNGSTER = "0x20(LEADER)", "0x32(PkMn_TRAINER)", "0x25(YOUNGSTER)"


def log_text(env, species="Treecko", pid="1304646B", battles=(), complete=True, cap=False) -> list:
    lines = header(env, complete=complete)
    if not complete:
        return lines
    lines += [Q("hb_empty"), Q("hold_7"), Q("choose_treecko").replace("Treecko", species or "Treecko")]
    if species:
        lines.append(hb(species, pid))
    for b in battles:
        lines += b
    if cap:
        lines.append("... (event log size cap reached — only STUCK dumps from here) ...")
    return lines


def rec(arm, species, pid, *, status="complete", keys=None, nonkey=(0, 0, 0), lane="H1", slot=0) -> dict:
    """A run RECORD in `run_record`'s shape. `keys`: key -> (reached, won, hp); unnamed keys were not met."""
    ks = {}
    for k in CA().KEYS:
        reached, won, hp = (keys or {}).get(k, (False, None, None))
        ks[k] = {"reached": reached, "attempted": won is not None or hp is not None, "outcome": None, "won": won,
                 "hp": hp, "hp_unknown": []}
    return {"log": f"{arm}-{species}-{pid}-{status}-{id(ks)}", "lane": lane, "slot": slot, "lane_arm": arm, "arm": arm,
            "refused": None, "excluded": None, "species": species, "pid": pid, "hold": 0, "chosen": species,
            "status": status, "capped": status == "capped", "header": True, "keys": ks,
            "nonkey": {"won": nonkey[0], "lost": nonkey[1], "other": nonkey[2]}}


# ============================================================================================ the synthetic model
RATES = {"ROXANNE": .92, "BRAWLY": .75, "WATTSON": .15, "FLANNERY": .46, "RIVAL_ROUTE_110": .36,
         "TABITHA_MT_CHIMNEY": .97, "MAXIE_MT_CHIMNEY": .72}
#: The order a run meets K* (the rival on Route 110 before Mauville's gym; Mt. Chimney before Lavaridge).
ORDER = ("ROXANNE", "BRAWLY", "RIVAL_ROUTE_110", "WATTSON", "TABITHA_MT_CHIMNEY", "MAXIE_MT_CHIMNEY", "FLANNERY")
EARLY = 3                      # a complete run that ends early still met the first three (baseline reach 1.00)
COPY = (1, 1, 0, 0, 0, 0, 0)   # a replay repeats Roxanne and Brawly, then diverges (review S4/F1)
SPECIES = ("Torchic", "Mudkip", "Treecko")
STARTERS = ("Torchic", "Mudkip", "Treecko", None) * 2
THETA = sum(RATES.values()) / len(RATES)


def synth(seed, *, rpl=7, flip_win=0.0, flip_loss=0.0, wattson_drop=0.0, heal="planted", c5=(0.0305, 0.0305),
          nonkey=0) -> list:
    """Two arms x 8 lanes of synthetic run RECORDS (the module docstring's model). Plants act on arm B only."""
    rnd = random.Random(seed)
    per_lane = list(rpl) if isinstance(rpl, (list, tuple)) else [rpl] * len(STARTERS)
    pool: dict = {}
    runs = []
    for arm, rate in (("A", c5[0]), ("B", c5[1])):
        for i, fixed in enumerate(STARTERS):
            n = per_lane[i]
            for r in range(n):
                s = rnd.randrange(11)
                sp = fixed or SPECIES[rnd.randrange(3)]
                base = pool.get((i, sp, s))
                won = {k: (base[k] if base is not None and rnd.random() < COPY[j] else rnd.random() < RATES[k])
                       for j, k in enumerate(ORDER)}
                if base is None:
                    pool[(i, sp, s)] = dict(won)
                cut = r == n - 1
                depth = rnd.randrange(len(ORDER) + 1) if cut else (len(ORDER) if rnd.random() < .9 else EARLY)
                met = set(ORDER[:depth])
                if arm == "B" and wattson_drop and "WATTSON" in met and rnd.random() < wattson_drop:
                    met.discard("WATTSON")
                keys = {}
                for k in ORDER:
                    if k not in met:
                        continue
                    w = won[k]
                    if arm == "B" and w and flip_win and rnd.random() < flip_win:
                        w = False
                    elif arm == "B" and not w and flip_loss and rnd.random() < flip_loss:
                        w = True
                    hp = 1 if heal == "equal" else (rnd.randint(1, 3) if arm == "B" else rnd.randint(0, 2))
                    keys[k] = (True, w, hp)
                battles = round(nonkey * (depth / len(ORDER) if cut else 1))
                lost = sum(1 for _ in range(battles) if rnd.random() < rate)
                runs.append(rec(arm, sp, f"{i:02X}{s:02X}0000", status="cut" if cut else "complete", keys=keys,
                                nonkey=(battles - lost, lost, 0), lane=f"H{i + 1 + (8 if arm == 'B' else 0)}",
                                slot=i + (8 if arm == "B" else 0)))
    return runs


# ============================================================================================ CA — the spec's rows
@row("CA1", "Δ = 0, 400 seeds x 400 draws: P(NOT LOWER) in [.70, .93] (§6: about .82 at 45 clusters)", heavy=True)
def _ca1():
    nl, deltas, clusters = 0, [], []
    for k in range(400):
        g = CA().grade(synth(1000 + k), draws=400, seed=k)
        nl += g["c2"]["rule_not_lower"]
        deltas.append(g["c2"]["point"])
        clusters.append(g["clusters_per_arm"]["A"])
    p = nl / 400
    return .70 <= p <= .93, (f"P(NOT LOWER) {nl}/400 = {p:.3f}; Δ mean {np.mean(deltas):+.4f}, true SD "
                             f"{np.std(deltas):.4f}; clusters per arm {np.mean(clusters):.1f}")


@row("CA2", "Δ = −.08 (B's first-attempt wins flipped w.p. .08/θ), 1,000 seeds x 400 draws: NOT LOWER at most 41",
     heavy=True)
def _ca2():
    nl, deltas = 0, []
    for k in range(1000):
        g = CA().grade(synth(5000 + k, flip_win=.08 / THETA), draws=400, seed=k)
        nl += g["c2"]["rule_not_lower"]
        deltas.append(g["c2"]["point"])
    return nl <= 41, f"NOT LOWER {nl}/1000 (bound 41 = binomial 99.9% at p .025); realized Δ mean {np.mean(deltas):+.4f}"


@row("CA3", "Δ = −.20: C2 LOWER (upper90 < 0) in >= 45 of 50; Δ = +.20: HIGHER in >= 45 of 50", heavy=True)
def _ca3():
    low = sum(CA().grade(synth(7000 + k, flip_win=.2 / THETA), draws=400, seed=k)["c2"]["lower_flag"]
              for k in range(50))
    high = sum(CA().grade(synth(8000 + k, flip_loss=.2 / (1 - THETA)), draws=400, seed=k)["c2"]["rule_reading"] == "HIGHER"
               for k in range(50))
    return low >= 45 and high >= 45, f"LOWER {low}/50, HIGHER {high}/50"


@row("CA4", "B's reach of Wattson cut by .35: REACH DIFFERS on WATTSON in >= 40 of 50", heavy=True)
def _ca4():
    hits = sum("WATTSON" in CA().grade(synth(9000 + k, wattson_drop=.35 / .9), draws=400, seed=k)["reach_differs"]
               for k in range(50))
    return hits >= 40, f"REACH DIFFERS on WATTSON {hits}/50"


@row("CA5", "a run that loses Roxanne TWICE, then wins (real H7 lines; first=True on all three): first attempt = LOST, "
            "its heal stock 4 HP items (Potion:2, Super_Potion:2; Full_Heal is not one)")
def _ca5():
    lost = [Q("h7_started_1"), Q("h7_start_lost"), Q("h7_ended_lost"), Q("h7_end_lost")]
    lost2 = [line.replace("f453155", "f460000").replace("f480710", "f470000") for line in lost]
    won = [Q("h7_started_2"), Q("h7_start_won"), Q("h7_end_won"), Q("h7_ended_won")]
    lines = log_text(ARMS["A"], battles=[lost, lost2, won])
    r = CA().run_record(lines, log="x", lane={"tag": "H7", "slot": 6, "arm": "A"}, arms=ARMS)
    k = r["keys"]["ROXANNE"]
    fa = BL().first_attempts(BL().split_battles(lines), CA().KSTAR)["ROXANNE"]
    return eq((k["reached"], k["attempted"], k["outcome"], k["won"], k["hp"], fa["index"]),
              (True, True, "lost", False, 4, 0))


@row("CA6", "two runs with ONE (species, PID) are ONE cluster: summed into it, and resampled together (no bootstrap "
            "value of p is 1/3)")
def _ca6():
    ws = {"ROXANNE": (True, True, 0)}
    ls = {"ROXANNE": (True, False, 0)}
    runs = [rec(arm, "Torchic", pid, keys=keys) for arm in ("A", "B")
            for pid, keys in (("AAAA0001", ws), ("AAAA0001", ws), ("BBBB0002", ls))]
    strata = CA().build_strata(runs)
    st = strata[("A", "Torchic")]
    bs = CA().statistics(CA().resample_sums(strata, 400, np.random.default_rng(3)), ["Torchic"])
    values = set(np.round(bs["pX_a"][:, 0], 9))
    return eq((st["C"], list(st["N"][:, 0]), values <= {0.0, round(2 / 3, 9), 1.0}, len(values)),
              (2, [2.0, 1.0], True, 3))


@row("CA7", "a log whose env-all is the OTHER arm's is REFUSED and listed; exit 1; no statistic printed")
def _ca7():
    d = make_batch("ca7", [("A", [("a.log", log_text(ARMS["A"], battles=[fight(1000, 265, LEADER, "Won")]))]),
                           ("A", [("b.log", log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Won")]))]),
                           ("B", [("c.log", log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Won")]))])])
    code, out = cli([str(d), "--draws", "50", "--delta", "0.08"])
    refused = [line for line in out.splitlines() if "⛔" in line and "b.log" in line]
    return eq((code, len(refused) == 1 and "'B'" in refused[0], "C2 —" in out, "NO GRADE" in out), (1, True, False, True))


@row("CA8", "C5 on hand-built counts is EXACTLY the ratio of sums (6/50 and 2/40, never the mean of ratios)")
def _ca8():
    runs = [rec("A", "Torchic", "A1", nonkey=(9, 1, 0)), rec("A", "Torchic", "A2", nonkey=(30, 0, 0)),
            rec("A", "Mudkip", "A3", nonkey=(5, 5, 3)),
            rec("B", "Torchic", "B1", nonkey=(19, 1, 0)), rec("B", "Mudkip", "B2", nonkey=(19, 1, 7))]
    g = CA().grade(runs, draws=50, seed=1)["c5"]
    return eq((close(g["a"], 6 / 50), close(g["b"], 2 / 40), g["lost"], g["battles"], g["undecided"]),
              (True, True, {"A": 6, "B": 2}, {"A": 50, "B": 40}, {"A": 3, "B": 7}))


@row("CA8P", "C5: a planted +.03 (B .0605 vs A .0305), 30 seeds x 100 runs per arm: REGRESSION in all 30", heavy=True)
def _ca8p():
    rpl = [13] * 4 + [12] * 4
    flags = [CA().grade(synth(11000 + k, rpl=rpl, nonkey=100, c5=(.0305, .0605)), draws=400, seed=k)["c5"]["flag"]
             for k in range(30)]
    return flags.count("REGRESSION") == 30, f"REGRESSION {flags.count('REGRESSION')}/30"


@row("CA9", "C1 fails (no heal difference) -> C2 is DESCRIPTIVE (result AND report); a planted heal -> CONFIRMATORY")
def _ca9():
    got = []
    for heal in ("equal", "planted"):
        runs = synth(123, heal=heal)
        g = CA().grade(runs, draws=200, seed=1)
        text = render(runs, g)
        got.append((g["c1"]["pass"], g["c2"]["status"], g["c2"]["verdict"],
                    "→ C2: DESCRIPTIVE — C1 did not pass. The rule reads" in text,
                    "trainers estimable)  [CONFIRMATORY]" in text))
    return eq(got, [(False, "DESCRIPTIVE — C1 did not pass", "DESCRIPTIVE", True, False),
                    (True, "CONFIRMATORY", g["c2"]["rule_reading"], False, True)])


@row("CA10", "the real line shapes parse exactly: the [TRAINER] end, the hold, the choice, the FIRST non-empty [hb]")
def _ca10():
    t = BL().parse_trainer(Q("tr_end_532"))
    ident = BL().run_identity([Q("hb_empty"), Q("hold_7"), Q("choose_treecko"), Q("hb_first"), hb("Mudkip", "0BADF00D")])
    return eq((t["kind"], t["opp"], t["res"], t["heal_stock"], t["classes"], ident),
              ("end", "532", "Won", [], [0x32], {"species": "Treecko", "pid": "1304646B", "hold": 7, "chosen": "Treecko"}))


# ============================================================================================ TB — T2's additions
@row("TB1", "parse_env_all: the A header -> A's dict; '(no POKEBOT_*…)' -> None; none -> None; after the header end "
            "-> None; unparseable -> None; a non-dict -> None")
def _tb1():
    b = BL()
    after = header(None) + [env_line(ARMS["A"])]
    got = (b.parse_env_all(header(ARMS["A"])) == ARMS["A"],
           b.parse_env_all(["    env-all:       (no POKEBOT_* env vars set)", "--- END RUN HEADER ---"]),
           b.parse_env_all(header(None)), b.parse_env_all(after),
           b.parse_env_all(["    env-all:       {'POKEBOT_A': ", "--- END RUN HEADER ---"]),
           b.parse_env_all(["    env-all:       ['POKEBOT_A']", "--- END RUN HEADER ---"]))
    return eq(got, (True, None, None, None, None, None))


@row("TB2", "arm_of: A / B by EQUALITY; one leaked key (the fault's POKEBOT_X4H_LEAK) -> '?'; one missing -> '?'; "
            "two equal arms -> 'ambiguous'; no header -> '?'")
def _tb2():
    b = BL()
    leak = {**ARMS["A"], "POKEBOT_X4H_LEAK": "1"}
    missing = {k: v for k, v in ARMS["A"].items() if k != "POKEBOT_MAINTAIN"}
    got = (b.arm_of(header(ARMS["A"]), ARMS), b.arm_of(header(ARMS["B"]), ARMS), b.arm_of(header(leak), ARMS),
           b.arm_of(header(missing), ARMS), b.arm_of(header(ARMS["A"]), {"A": ARMS["A"], "C": dict(ARMS["A"])}),
           b.arm_of([], ARMS))
    return eq(got, ("A", "B", "?", "?", "ambiguous", "?"))


@row("TB3", "run_identity: the FIRST non-empty [hb] decides (a malformed first one -> None, never a later one); "
            "missing values None; hold 0 when absent; a double-quoted STEP repr parses")
def _tb3():
    b = BL()
    bad_first = Q("hb_first").replace("ids=['Treecko#1304646B:", "ids=['?:")
    got = (b.run_identity([bad_first, hb("Mudkip", "0BADF00D")]),
           b.run_identity([Q("hb_empty")]),
           b.run_identity(['f2788 [STEP] "Intro: holding 12f before confirming (RNG decorrelation)..."',
                           "f9 [STEP] \"Story: choosing Mudkip!\"", hb("Mudkip", "b4321ac5")]))
    return eq(got, ({"species": None, "pid": None, "hold": 0, "chosen": None},
                    {"species": None, "pid": None, "hold": 0, "chosen": None},
                    {"species": "Mudkip", "pid": "B4321AC5", "hold": 12, "chosen": "Mudkip"}))


@row("TB4", "log_capped: the debug logger's cap line -> True; a log without it -> False")
def _tb4():
    return eq((BL().log_capped(log_text(ARMS["A"], cap=True)), BL().log_capped(log_text(ARMS["A"]))), (True, False))


@row("TB5", "batch_logs reads L<nn> for ANY lane count (L01-L16, L100), never M01 / Lx1 / non-.log / a directory")
def _tb5():
    got = [p.relative_to(TMP["x4"]).as_posix() for p in BL().batch_logs(TMP["x4"] / "x4-runs" / "S16")]
    want = [f"x4-runs/S16/L{n:02d}/debug-logs/r.log" for n in range(1, 17)] + ["x4-runs/S16/L100/debug-logs/r.log"]
    return eq(got, sorted(want))


@row("TB6", "x4_logs resolves a stamp under the MAIN checkout's tools/story-dev (not the worktree's), 16 lanes")
def _tb6():
    b = BL()
    saved = b.main_checkout
    try:
        b.main_checkout = lambda: TMP["main"]
        got = b.x4_logs("S16")
    finally:
        b.main_checkout = saved
    return eq(len(got) == 17 and all(str(p).startswith(str(TMP["main"])) for p in got), True)


@row("TB7", "live_logs(tag): endless-<tag>-H* only (s14 never reads s14smoke), Old/ read once, the MAIN checkout's "
            "profiles by default")
def _tb7():
    b = BL()
    saved = b.main_checkout
    try:
        b.main_checkout = lambda: TMP["main"]
        got = [p.relative_to(TMP["main"]).as_posix() for p in b.live_logs("s14")]
    finally:
        b.main_checkout = saved
    prof = "sandbox-pokebot/profiles/"
    # (a SET: Windows orders paths case-insensitively, so `Old/` sorts after `b.log`; the order is not the point)
    return eq((len(got), set(got)), (3, {prof + "endless-s14-H1-torchic/debug-logs/Old/a.log",
                                         prof + "endless-s14-H1-torchic/debug-logs/b.log",
                                         prof + "endless-s14-H10-mudkip/debug-logs/c.log"}))


@row("TB8", "resolve_sources: --batch-dir / --tag read; ZERO logs from a stamp, --tag or --batch-dir is exit 2; a "
            "mode conflict is exit 2; --logs matching nothing still returns [] (the probes' own NO-DATA exit)")
def _tb8():
    import argparse as _argparse
    b = BL()

    def run(argv):
        ap = _argparse.ArgumentParser()
        b.add_source_args(ap, "NO-SUCH-STAMP")
        with contextlib.redirect_stderr(io.StringIO()):
            try:
                return len(b.resolve_sources(ap.parse_args(argv), ap, "NO-SUCH-STAMP")[0])
            except SystemExit as stop:
                return f"exit {stop.code}"
    saved = b.main_checkout
    try:
        b.main_checkout = lambda: TMP["main"]
        got = (run(["--batch-dir", str(TMP["x4"] / "x4-runs" / "S16")]), run(["--tag", "s14"]),
               run([]), run(["--tag", "nosuchtag"]), run(["--batch-dir", str(TMP["root"] / "empty")]),
               run(["S16", "--tag", "s14"]), run(["--logs", str(TMP["root"] / "no-such-*.log")]))
    finally:
        b.main_checkout = saved
    return eq(got, (17, 3, "exit 2", "exit 2", "exit 2", "exit 2", 0))


@row("TB9", "first_attempts: a start with NO end is not an attempt (the next one is); an end for ANOTHER trainer is "
            "not a match; the rival's six ids; a Draw is LOST; the earliest wins")
def _tb9():
    b = BL()
    battles = b.split_battles(fight(100, 265, LEADER, "Won", end=False) + fight(200, 265, LEADER, "Lost")
                              + fight(300, 265, LEADER, "Won")
                              + fight(400, 266, LEADER, "Won")[:2] + ["f450 [TRAINER] end opp=265 class=0x20(LEADER) "
                                                                    "res=Won heal_stock=- map=3,3"]
                              + fight(500, 533, RIVAL, "Draw") + fight(600, 530, RIVAL, "Won"))
    fa = b.first_attempts(battles, {"ROXANNE": (265,), "BRAWLY": (266,), "RIVAL_ROUTE_110": (521, 530, 533)})
    return eq((fa["ROXANNE"]["index"], fa["ROXANNE"]["outcome"], fa["BRAWLY"],
               fa["RIVAL_ROUTE_110"]["index"], fa["RIVAL_ROUTE_110"]["outcome"]),
              (1, "lost", None, 4, "lost"))


@row("TB10", "keys_met: a start with no end still MET the trainer; another trainer's battle did not")
def _tb10():
    b = BL()
    battles = b.split_battles(fight(100, 266, LEADER, "Won", end=False) + fight(200, 318, YOUNGSTER, "Won"))
    return eq(b.keys_met(battles, {"ROXANNE": (265,), "BRAWLY": (266,)}), {"BRAWLY"})


# ============================================================================================ CR — one run's record
LANE_A = {"tag": "H1", "slot": 0, "arm": "A"}


@row("CR1", "status precedence cut > lost > capped > complete; a cut log with no header is EXCLUDED (not refused); "
            "a complete one is REFUSED; no starter -> EXCLUDED")
def _cr1():
    c = CA()
    full = log_text(ARMS["A"], cap=True)
    got = (c.run_record(full, log="x", lane=LANE_A, arms=ARMS, cut=True, lost=True)["status"],
           c.run_record(full, log="x", lane=LANE_A, arms=ARMS, lost=True)["status"],
           c.run_record(full, log="x", lane=LANE_A, arms=ARMS)["status"],
           c.run_record(log_text(ARMS["A"]), log="x", lane=LANE_A, arms=ARMS)["status"])
    nohead = header(None, complete=False)    # the deadline cut it while the header was being written
    r_cut = c.run_record(nohead, log="x", lane=LANE_A, arms=ARMS, cut=True)
    r_done = c.run_record(nohead, log="x", lane=LANE_A, arms=ARMS)
    r_nosp = c.run_record(log_text(ARMS["A"], species=None), log="x", lane=LANE_A, arms=ARMS)
    flags = (bool(r_cut["excluded"]), bool(r_cut["refused"]), bool(r_done["refused"]), bool(r_nosp["excluded"]),
             bool(r_nosp["refused"]), c.usable(c.run_record(log_text(ARMS["A"]), log="x", lane=LANE_A, arms=ARMS)),
             r_nosp["excluded_kind"])
    return eq((got, flags), (("cut", "lost", "capped", "complete"), (True, False, True, True, False, True, "no_starter")))


@row("CR2", "the non-key counts: only NON-KEY trainer battles (a key battle and a wild battle are not counted); a "
            "Draw is lost; an unended battle is 'other'")
def _cr2():
    wild = ["f900 [BATTLE] started hp=[('Treecko', 35, 35)]",
            "f950 [BATTLE] ended (outcome=BattleOutcome.Lost) party=['Treecko:L15']"]
    battles = [fight(100, 318, YOUNGSTER, "Won"), fight(200, 318, YOUNGSTER, "Draw"), fight(300, 265, LEADER, "Lost"),
               wild, fight(400, 333, YOUNGSTER, "Won", end=False)]
    r = CA().run_record(log_text(ARMS["A"], battles=battles), log="x", lane=LANE_A, arms=ARMS)
    return eq(r["nonkey"], {"won": 1, "lost": 1, "other": 1})


@row("CR3", "lost_logs: a spawn that DIED marks the newest log it opened; x4h's own stop and exit 0 mark none")
def _cr3():
    import datetime as _dt
    names = [f"Story-debug-20261001-{h}.log" for h in ("210000", "220000", "230000", "235000")]
    t = lambda hms: _dt.datetime.strptime("20261001-" + hms, "%Y%m%d-%H%M%S").timestamp()  # noqa: E731
    spawns = [{"start": t("205959"), "end": t("225959"), "exit": 1},
              {"start": t("225959"), "end": t("233000"), "exit": 1, "stopped_by": "x4h"},
              {"start": t("233000"), "end": t("235959"), "exit": 0}]
    return eq(CA().lost_logs(names, spawns), {"Story-debug-20261001-220000.log"})


@row("CR4", "collect_runs: L<nn> -> its ARMS.json lane by slot (L10+ too); the cut log from summary.json (final AND "
            "provisional form); LIVE with no summary: each lane's NEWEST log is the cut one")
def _cr4():
    logs = {"A": [("r1-debug-20261001-210000.log", log_text(ARMS["A"])),
                  ("r2-debug-20261001-220000.log", log_text(ARMS["A"]))],
            "B": [("r3-debug-20261001-210000.log", log_text(ARMS["B"]))]}
    lanes = [("A", logs["A"])] * 9 + [("B", logs["B"])]   # ten lanes: H10 is the only B lane, in L10
    d1 = make_batch("cr4a", lanes, cut={"H1": "r1-debug-20261001-210000.log", "H10": "r3-debug-20261001-210000.log"})
    d2 = make_batch("cr4b", lanes, cut={"H2": "r2-debug-20261001-220000.log"}, provisional=True)
    r1, _ = CA().collect_runs(d1)
    r2, _ = CA().collect_runs(d2)
    d3 = make_batch("cr4c", lanes[:2], summary=False, profiles_tag="t4")
    saved = BL().main_checkout
    try:
        BL().main_checkout = lambda: TMP["root"] / "cr4c-main"
        r3, _ = CA().collect_runs(d3, tag="t4")
    finally:
        BL().main_checkout = saved

    def cuts(rs):
        return sorted((r["lane"], pathlib.Path(r["log"]).name[:2]) for r in rs if r["status"] == "cut")
    b10 = [(r["lane"], r["slot"], r["arm"], r["refused"]) for r in r1 if r["lane"] == "H10"]
    return eq((len(r1), b10, cuts(r1), cuts(r2), cuts(r3)),
              (19, [("H10", 9, "B", None)], [("H1", "r1"), ("H10", "r3")], [("H2", "r2")], [("H1", "r2"), ("H2", "r2")]))


# ============================================================================================ CS — the estimand
@row("CS1", "STRATA arm x species: data whose Δ is constant under within-species resampling has a ZERO-width CI "
            "(resampling across species would drop a species from some draws and move Δ)")
def _cs1():
    # A: Torchic won, Mudkip lost; B: both won. Stratified, every draw keeps both species in both arms: Δ = 1 − .5.
    # (FOLDED 2026-10-01: the first version had the SAME per-species rates in both arms, so a draw that lost a species
    # dropped it from both arms symmetrically and Δ stayed 0 — the pooled-resampling mutant C03 survived it.)
    # (FOLDED again with DECISION F2: θ needs all 7 K* trainers, so this one-trainer row now reads Roxanne's own Δ.)
    runs = [rec(arm, sp, f"{sp[:2]}{i}", keys={"ROXANNE": (True, arm == "B" or sp == "Torchic", 0)})
            for arm in ("A", "B") for sp in ("Torchic", "Mudkip") for i in range(2)]
    g = CA().grade(runs, draws=400, seed=5)["trainers"]["ROXANNE"]["p_diff"]
    return eq((g["point"], g["ci95"], g["nan_draws"]), (0.5, [0.5, 0.5], 0))


@row("CS2", "species weighting: p[a,X] is the EQUAL-weight mean over species fought in BOTH arms (never pooled, never "
            "a species only one arm fought)")
def _cs2():
    w, l_ = {"ROXANNE": (True, True, 0)}, {"ROXANNE": (True, False, 0)}
    runs = ([rec("A", "Torchic", f"T{i}", keys=w) for i in range(3)] + [rec("A", "Mudkip", "M0", keys=l_)]
            + [rec("A", "Treecko", "K0", keys=l_)]
            + [rec("B", "Torchic", "T9", keys=w)] + [rec("B", "Mudkip", f"M{i}", keys=l_) for i in range(3)])
    t = CA().grade(runs, draws=50, seed=1)["trainers"]["ROXANNE"]
    return eq((t["p_a"], t["p_b"], t["p_diff"]["point"]), (0.5, 0.5, 0.0))


def _all7(won_mask, hp=0, skip=()):
    """keys for a run that met and finished all 7 K* trainers; `won_mask` = the trainers it WON; `skip` never met."""
    return {k: (True, k in won_mask, hp) for k in KEYS7 if k not in skip}


KEYS7 = ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY", "RIVAL_ROUTE_110", "TABITHA_MT_CHIMNEY", "MAXIE_MT_CHIMNEY")


@row("CS3", "θ is the mean over the FROZEN K* (DECISION F2): all 7 estimable -> the plain mean (1/7 vs 1); one of 7 "
            "never fought by B -> θ UNDEFINED, 6 of 7 reported, and the rule reads NOT ESTIMABLE over the frozen K*")
def _cs3():
    runs = [rec("A", "Torchic", "P1", keys=_all7({"ROXANNE"})), rec("B", "Torchic", "P2", keys=_all7(KEYS7))]
    g = CA().grade(runs, draws=50, seed=1)["c2"]
    runs2 = [rec("A", "Torchic", "P1", keys=_all7({"ROXANNE"})),
             rec("B", "Torchic", "P2", keys=_all7(KEYS7, skip=("WATTSON",)))]
    h = CA().grade(runs2, draws=50, seed=1)["c2"]
    return eq((close(g["theta_a"], 1 / 7), g["theta_b"], g["n_estimable"], h["theta_a"], h["theta_b"],
               h["n_estimable"], h["rule_reading"]),
              (True, 1.0, 7, None, None, 6, "NOT ESTIMABLE over the frozen K* (6 of 7)"))


@row("CS4", "REACH CENSORING: a complete run that never met X is a 'no'; a cut / lost / capped run that never met X is "
            "OUT; any run that met X is a 'yes'")
def _cs4():
    met = {"ROXANNE": (True, True, 0)}
    runs = [rec("A", "Torchic", "P1", keys=met), rec("A", "Torchic", "P2"), rec("A", "Torchic", "P3", status="cut"),
            rec("A", "Torchic", "P4", status="cut", keys=met), rec("A", "Torchic", "P5", status="lost"),
            rec("A", "Torchic", "P6", status="capped"),
            rec("B", "Torchic", "P7", keys=met), rec("B", "Torchic", "P8"), rec("B", "Torchic", "P9"),
            rec("B", "Torchic", "PA", status="capped", keys=met)]
    t = CA().grade(runs, draws=50, seed=1)["trainers"]["ROXANNE"]
    return eq((close(t["reach_a"], 2 / 3), close(t["reach_b"], 2 / 4), t["reach_n"]), (True, True, {"A": 3, "B": 4}))


@row("CS5", "COMPOSITE: P(met X and won the first attempt) over the reach denominator, species-weighted, mean over K*")
def _cs5():
    won, lost = {"ROXANNE": (True, True, 0)}, {"ROXANNE": (True, False, 0)}
    runs = [rec("A", "Torchic", "P1", keys=won), rec("A", "Torchic", "P2"), rec("A", "Mudkip", "P3", keys=lost),
            rec("A", "Mudkip", "P4", status="cut"),
            rec("B", "Torchic", "P5", keys=won), rec("B", "Mudkip", "P6", keys=won), rec("B", "Mudkip", "P7")]
    g = CA().grade(runs, draws=50, seed=1)["composite"]
    # ROXANNE — A: Torchic 1/2, Mudkip 0/1 (P4 is cut and never met her: out) -> .25; B: Torchic 1/1, Mudkip 1/2 -> .75.
    # The other six K* trainers: every complete run is a "not met" in both arms -> 0. The mean over K* is /7.
    return eq((close(g["a"], .25 / 7), close(g["b"], .75 / 7), close(g["point"], .5 / 7)), (True, True, True))


@row("CS6", "C1: the per-RUN mean, then the mean over runs (4, not the pooled 10/3); an unreadable heal stock is "
            "excluded; a run with no K* attempt adds nothing")
def _cs6():
    r1 = rec("A", "Torchic", "P1", keys={"ROXANNE": (True, True, 0), "BRAWLY": (True, True, 4)})
    r2 = rec("A", "Torchic", "P2", keys={"ROXANNE": (True, True, 6), "BRAWLY": (True, True, None)})
    r3 = rec("A", "Torchic", "P3")
    rb = rec("B", "Torchic", "P4", keys={"ROXANNE": (True, True, 1)})
    g = CA().grade([r1, r2, r3, rb], draws=50, seed=1)["c1"]
    return eq((g["a"], g["b"], g["point"], g["runs_with_value"]), (4.0, 1.0, -3.0, {"A": 2, "B": 1}))


@row("CS7", "WIRING: C1 PASS reads lower95; C2's word reads the 95% CI; C2 LOWER, C5, REACH and the group flags read "
            "the 90% CI (a stubbed `ci` gives each level its own interval, in two configurations)")
def _cs7():
    c = CA()
    saved = c.ci
    got = []
    try:
        # the 95% CI straddles 0 in both; the 90% CI is ABOVE 0, then BELOW 0 — so every verdict that read the wrong
        # level answers differently in at least one of the two
        for ci90 in ((0.2, 0.4), (-0.4, -0.2)):
            c.ci = lambda draws, level, _c=ci90: (-0.5, 0.5) if level == 95 else _c
            g = c.grade(synth(1), draws=20, seed=1)
            got.append((g["c1"]["pass"], g["c2"]["rule_reading"], g["c2"]["lower_flag"], g["c5"]["flag"],
                        g["trainers"]["ROXANNE"]["reach_differs"], g["groups"]["leaders"]["lower_flag"]))
    finally:
        c.ci = saved
    return eq(got, [(False, "INCONCLUSIVE", False, "REGRESSION", True, False),
                    (False, "INCONCLUSIVE", True, "IMPROVED", True, True)])


@row("CK1", "K* is the FROZEN set: the decomp's ids by name (opponents.h, re-read 2026-10-01), and the three groups "
            "partition it")
def _ck1():
    want = {"ROXANNE": (265,), "BRAWLY": (266,), "WATTSON": (267,), "FLANNERY": (268,),
            "RIVAL_ROUTE_110": (521, 524, 527, 530, 533, 536), "TABITHA_MT_CHIMNEY": (597,),
            "MAXIE_MT_CHIMNEY": (602,)}
    members = [k for g in CA().GROUPS.values() for k in g]
    return eq((CA().KSTAR, sorted(members) == sorted(want), len(members)), (want, True, 7))


# ============================================================================================ CV — the verdict functions
@row("CV1", "c2_reading at its boundaries (strict): −δ itself is INCONCLUSIVE, 0 itself is NOT LOWER, inside (−δ, 0) "
            "is 'statistically lower', NaN is NOT ESTIMABLE, δ is a parameter")
def _cv1():
    r = CA().c2_reading
    got = (r(-.08, .1, .08), r(-.0799, .1, .08), r(0.0, .1, .08), r(1e-9, .1, .08), r(-.05, -.01, .08),
           r(-.05, 0.0, .08), r(math.nan, math.nan, .08), r(-.1, .1, .11), r(-.1, .1, .08))
    return eq(got, ("INCONCLUSIVE", "NOT LOWER", "NOT LOWER", "HIGHER", "NOT LOWER, but statistically lower",
                    "NOT LOWER", "NOT ESTIMABLE", "NOT LOWER", "INCONCLUSIVE"))


@row("CV2", "c5_flag at its boundaries: REGRESSION iff lower90 > 0, IMPROVED iff upper90 < 0, else no flag")
def _cv2():
    f = CA().c5_flag
    return eq((f(.001, .01), f(0.0, .01), f(-.01, -.001), f(-.01, 0.0)), ("REGRESSION", None, "IMPROVED", None))


@row("CV3", "ci: percentile CIs (0..100 -> 95%: [2.5, 97.5], 90%: [5, 95]); NaN draws dropped; all NaN -> NaN")
def _cv3():
    c = CA().ci
    d = np.arange(101, dtype=float)
    nan_mix = np.concatenate([d, [np.nan] * 50])
    allnan = c(np.full(5, np.nan), 95)
    return eq((c(d, 95), c(d, 90), c(nan_mix, 95), all(math.isnan(x) for x in allnan)),
              ((2.5, 97.5), (5.0, 95.0), (2.5, 97.5), True))


# ============================================================================================ CX — the CLI
@row("CX1", "exit codes: a good batch 0; an arm with NO usable run 1 (named); zero logs 1; no ARMS.json 2; an unknown "
            "--tag 2; --draws 0 2")
def _cx1():
    good = make_batch("cx1g", [("A", [("a.log", log_text(ARMS["A"], battles=[fight(1000, 265, LEADER, "Won")]))]),
                               ("B", [("b.log", log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Lost")]))])])
    nob = make_batch("cx1n", [("A", [("a.log", log_text(ARMS["A"]))]), ("B", [("b.log", log_text(ARMS["B"], species=None))])])
    empty = make_batch("cx1e", [("A", []), ("B", [])])
    (TMP["root"] / "cx1-noarms").mkdir(exist_ok=True)
    d = ["--draws", "50", "--delta", "0.08"]       # a 2-lane design has no pre-registered δ (DECISION F6)
    codes = (cli([str(good)] + d)[0], cli([str(nob)] + d),
             cli([str(empty)] + d), cli([str(TMP["root"] / "cx1-noarms")])[0],
             cli(["--tag", "no-such-tag-anywhere"])[0], cli([str(good), "--draws", "0"])[0])
    return eq((codes[0], codes[1][0], "arm B has NO usable runs" in codes[1][1], codes[2][0],
               "ZERO runs" in codes[2][1], codes[3], codes[4], codes[5]), (0, 1, True, 1, True, 2, 2, 2))


@row("CX2", "the defaults are the pre-registered ones on an M-16 batch: 10,000 draws, seed 14, δ .08 (from --json), "
            "and NOT exploratory")
def _cx2():
    good = batch16("cx2", log_text(ARMS["A"], battles=[fight(1000, 265, LEADER, "Won")]),
                   log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Won")]))
    out = TMP["root"] / "cx2.json"
    code, _ = cli([str(good), "--json", str(out)])
    g = json.loads(out.read_text(encoding="utf-8"))["grade"]
    return eq((code, g["draws"], g["seed"], g["delta_margin"], g["exploratory"]), (0, 10_000, 14, 0.08, []))


@row("CX3", "after a FAILED control nothing statistical is printed (no C1/C2/C5 line, no verdict word)")
def _cx3():
    d = make_batch("cx3", [("A", [("a.log", log_text({**ARMS["A"], "POKEBOT_X4H_LEAK": "1"}))]),
                           ("B", [("b.log", log_text(ARMS["B"]))])])
    code, out = cli([str(d), "--draws", "50", "--delta", "0.08"])
    words = [w for w in ("C1 —", "C2 —", "C5 —", "NOT LOWER", "HIGHER", "INCONCLUSIVE", "REGRESSION") if w in out]
    return eq((code, words), (1, []))


# ============================================================================================ AH — the hunter's rows
# The INDEPENDENT mutant hunter's proposed rows N1-N17 (`evidence/2026-10-01-batch14-T23-ADVERSARIAL.txt`, MH-1..MH-13;
# its runner `scratchpad/t23adv/mut/mut_runner.py`), adopted as AH<n> = N<n>. Each kills survivors of the first gate.
# ADAPTED where DECISION F2 (θ over the frozen K*) or F10 (censored during a first attempt) changed the expected value
# or made a θ-based check vacuous: AH2 (all 7 trainers), AH3 / AH10 / AH13 (per-trainer p, not θ), AH5 (reach_n 2).
@row("AH1", "N1 WIRING (straddle + status): a 90% CI that STRADDLES 0 raises no flag; C2's status follows C1's PASS")
def _ah1():
    c = CA()
    saved = c.ci
    got = []
    try:
        for ci90 in ((0.2, 0.4), (-0.4, -0.2), (-0.1, 0.1)):
            c.ci = lambda draws, level, _c=ci90: (-0.5, 0.5) if level == 95 else _c
            g = c.grade(synth(1), draws=20, seed=1)
            got.append((g["c1"]["pass"], g["c2"]["status"], g["c2"]["lower_flag"], g["c5"]["flag"],
                        g["trainers"]["ROXANNE"]["reach_differs"], g["groups"]["leaders"]["lower_flag"],
                        g["groups"]["rivals"]["lower_flag"]))
    finally:
        c.ci = saved
    d = "DESCRIPTIVE — C1 did not pass"
    return eq(got, [(False, d, False, "REGRESSION", True, False, False), (False, d, True, "IMPROVED", True, True, True),
                    (False, d, False, None, False, False, False)])


@row("AH2", "N2 EXACT-ZERO boundary: identical arms (every run met and won all 7) -> Δ and reach CIs are [0, 0]; no "
            "C2 LOWER, no REACH DIFFERS, no group flag")
def _ah2():
    w = _all7(KEYS7, hp=1)
    runs = [rec(arm, sp, f"{arm}{sp[:2]}{i}", keys=w) for arm in ("A", "B") for sp in ("Torchic", "Mudkip")
            for i in range(3)]
    g = CA().grade(runs, draws=200, seed=3)
    return eq((g["c2"]["ci90"], g["c2"]["lower_flag"], g["reach_differs"], g["groups"]["leaders"]["lower_flag"]),
              ([0.0, 0.0], False, [], False))


@row("AH3", "N3 C2 species weights are EQUAL even when the species' fought counts differ (Torchic 3+1, Mudkip 1+1)")
def _ah3():
    w, l_ = {"ROXANNE": (True, True, 0)}, {"ROXANNE": (True, False, 0)}
    runs = ([rec("A", "Torchic", f"T{i}", keys=w) for i in range(3)] + [rec("A", "Mudkip", "M0", keys=l_)]
            + [rec("B", "Torchic", "T9", keys=w)] + [rec("B", "Mudkip", "M9", keys=l_)])
    t = CA().grade(runs, draws=50, seed=1)["trainers"]["ROXANNE"]
    return eq((t["p_a"], t["p_b"]), (0.5, 0.5))


@row("AH4", "N4 COMPOSITE censoring: a CUT run that never met X is out of the denominator even where the stratum has "
            "wins; a species with reach runs in ONE arm only is out")
def _ah4():
    won = {"ROXANNE": (True, True, 0)}
    runs = [rec("A", "Torchic", "P1", keys=won), rec("A", "Torchic", "P2", status="cut"),
            rec("A", "Mudkip", "P3"),
            rec("B", "Torchic", "P5", keys=won), rec("B", "Torchic", "P6")]
    t = CA().grade(runs, draws=50, seed=1)["composite"]
    return eq((close(t["a"], 1.0 / 7), close(t["b"], 0.5 / 7)), (True, True))


@row("AH5", "N5 a run CUT mid-battle at X is not fought (no C2 denominator) and, DECISION F10, is OUT of X's reach "
            "denominator; an attempt that ended RanAway is undecided, not a loss")
def _ah5():
    c = CA()
    lane_a, lane_b = {"tag": "H1", "slot": 0, "arm": "A"}, {"tag": "H2", "slot": 1, "arm": "B"}
    r_cutmid = c.run_record(log_text(ARMS["A"], pid="00000001", battles=[fight(1000, 265, LEADER, "Won", end=False)]),
                            log="a1", lane=lane_a, arms=ARMS, cut=True)
    r_won = c.run_record(log_text(ARMS["A"], pid="00000002", battles=[fight(1000, 265, LEADER, "Won")]),
                         log="a2", lane=lane_a, arms=ARMS)
    r_ran = c.run_record(log_text(ARMS["A"], pid="00000003",
                                  battles=[fight(1000, 265, LEADER, "Won", ended="RanAway")]), log="a3", lane=lane_a,
                         arms=ARMS)
    r_b = c.run_record(log_text(ARMS["B"], pid="00000004", battles=[fight(1000, 265, LEADER, "Won")]),
                       log="b1", lane=lane_b, arms=ARMS)
    t = c.grade([r_cutmid, r_won, r_ran, r_b], draws=50, seed=1)["trainers"]["ROXANNE"]
    return eq((t["fought"], t["won_first"], t["p_a"], close(t["reach_a"], 1.0), t["reach_n"]["A"],
               t["censored_during"]["A"]), ({"A": 1, "B": 1}, {"A": 1, "B": 1}, 1.0, True, 2, ["a1"]))


@row("AH6", "N6 a CUT run's completed first attempt counts in C2 and C1 (DESIGN §5: it contributes the attempts it "
            "completed)")
def _ah6():
    runs = [rec("A", "Torchic", "P1", keys={"ROXANNE": (True, True, 2)}),
            rec("A", "Torchic", "P2", status="cut", keys={"ROXANNE": (True, False, 0)}),
            rec("B", "Torchic", "P3", keys={"ROXANNE": (True, True, 1)})]
    g = CA().grade(runs, draws=50, seed=1)
    return eq((g["trainers"]["ROXANNE"]["p_a"], g["c1"]["a"]), (0.5, 1.0))


@row("AH7", "N7 REACH is a POOLED ratio of sums over runs (3/4), never a species-weighted mean (.5)")
def _ah7():
    met = {"ROXANNE": (True, True, 0)}
    runs = ([rec("A", "Torchic", f"T{i}", keys=met) for i in range(3)] + [rec("A", "Mudkip", "M0")]
            + [rec("B", "Torchic", "T9", keys=met), rec("B", "Mudkip", "M9", keys=met)])
    t = CA().grade(runs, draws=50, seed=1)["trainers"]["ROXANNE"]
    return eq((close(t["reach_a"], 0.75), close(t["reach_b"], 1.0)), (True, True))


@row("AH8", "N8 C1 is the mean over RUNS (9/4), never a species-weighted mean (1.5)")
def _ah8():
    runs = ([rec("A", "Torchic", f"T{i}", keys={"ROXANNE": (True, True, 3)}) for i in range(3)]
            + [rec("A", "Mudkip", "M0", keys={"ROXANNE": (True, True, 0)})]
            + [rec("B", "Torchic", "T9", keys={"ROXANNE": (True, True, 1)})])
    return eq(CA().grade(runs, draws=50, seed=1)["c1"]["a"], 2.25)


@row("AH9", "N9 STRATA are arm x species, not finer: two clusters of one stratum in DIFFERENT lanes still resample "
            "against each other (pX_a takes 3 values)")
def _ah9():
    runs = [rec("A", "Torchic", "P1", keys={"ROXANNE": (True, True, 0)}, lane="H1"),
            rec("A", "Torchic", "P2", keys={"ROXANNE": (True, False, 0)}, lane="H2"),
            rec("B", "Torchic", "P3", keys={"ROXANNE": (True, True, 0)}, lane="H9")]
    strata = CA().build_strata(runs)
    bs = CA().statistics(CA().resample_sums(strata, 400, np.random.default_rng(3)), ["Torchic"])
    return eq(sorted(set(np.round(bs["pX_a"][:, 0], 9))), [0.0, 0.5, 1.0])


@row("AH10", "N10 the bootstrap draws each stratum INDEPENDENTLY: identical A and B strata do not give Δ ≡ 0")
def _ah10():
    runs = [rec(arm, "Torchic", f"{arm}{i}", keys={"ROXANNE": (True, i == 0, 0)}) for arm in ("A", "B")
            for i in range(2)]
    g = CA().grade(runs, draws=400, seed=2)["trainers"]["ROXANNE"]["p_diff"]
    return eq((g["point"], g["ci95"][0] < 0 < g["ci95"][1]), (0.0, True))


@row("AH11", "N11 grade() USES --draws and --seed: the bootstrap is called with the requested draws, and two seeds "
             "give different CIs")
def _ah11():
    c = CA()
    seen = []
    saved = c.resample_sums
    try:
        def spy(strata, draws, rng):
            seen.append(draws)
            return saved(strata, draws, rng)
        c.resample_sums = spy
        runs = synth(7)
        g1 = c.grade(runs, draws=1234, seed=1)
    finally:
        c.resample_sums = saved
    g2 = c.grade(runs, draws=1234, seed=2)
    return eq((1234 in seen, g1["c2"]["ci95"] != g2["c2"]["ci95"]), (True, True))


@row("AH12", "N12 a CUT log whose header is the OTHER arm's is REFUSED (the last log of every lane is cut)")
def _ah12():
    r = CA().run_record(log_text(ARMS["B"]), log="x", lane={"tag": "H1", "slot": 0, "arm": "A"}, arms=ARMS, cut=True)
    return eq((bool(r["refused"]), r["excluded"]), (True, None))


@row("AH13", "N13 an EXCLUDED run (no starter) in an otherwise good batch does not enter (or crash) the grade")
def _ah13():
    good = [rec("A", "Torchic", "P1", keys={"ROXANNE": (True, True, 1)}),
            rec("B", "Torchic", "P2", keys={"ROXANNE": (True, False, 1)})]
    bad = rec("A", None, None, keys={"ROXANNE": (True, False, 5)})
    bad["excluded"] = "no starter read"
    g1 = CA().grade(good, draws=50, seed=1)
    try:
        g2 = CA().grade(good + [bad], draws=50, seed=1)
    except Exception as error:  # noqa: BLE001 - the mutant this row exists for raises here
        return False, f"raised {type(error).__name__}: {error}"
    p = lambda g: g["trainers"]["ROXANNE"]["p_diff"]["point"]  # noqa: E731
    return eq((p(g2), g2["c1"]["a"], g2["runs_per_arm"]), (p(g1), g1["c1"]["a"], {"A": 1, "B": 1}))


@row("AH14", "N14 C5: an UNCLASSIFIED trainer battle (a '?' side beside a non-key one) is NOT a non-key battle")
def _ah14():
    unread = ["f100 [BATTLE] started hp=[('Treecko', 35, 35)]",
              "f100 [TRAINER] start opp=318+? class=0x25(YOUNGSTER)+? value=25 lvl_last=15 first=True base=1500 "
              "double=True two=True money=1368 heal_stock=- map=11,3 enemy_alive=3",
              "f200 [BATTLE] ended (outcome=BattleOutcome.Lost) party=['Treecko:L15']"]
    r = CA().run_record(log_text(ARMS["A"], battles=[unread, fight(300, 318, YOUNGSTER, "Won")]), log="x",
                        lane={"tag": "H1", "slot": 0, "arm": "A"}, arms=ARMS)
    return eq(r["nonkey"], {"won": 1, "lost": 0, "other": 0})


@row("AH15", "N15 GROUPS are DESIGN §5's: leaders = the four gym leaders, rivals = the Route 110 rival, Magma/Aqua = "
             "Tabitha + Maxie")
def _ah15():
    return eq({k: tuple(v) for k, v in CA().GROUPS.items()},
              {"leaders": ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY"), "rivals": ("RIVAL_ROUTE_110",),
               "magma_aqua": ("TABITHA_MT_CHIMNEY", "MAXIE_MT_CHIMNEY")})


@row("AH16", "N16 rule_not_lower (JSON) is the RULE's 'lower95 > −δ': True on HIGHER and on 'statistically lower', "
             "δ honoured")
def _ah16():
    c = CA()
    saved = c.ci
    got = []
    try:
        for ci95, ci90, delta in (((0.1, 0.3), (0.15, 0.25), 0.08), ((-0.05, -0.01), (-0.04, -0.02), 0.08),
                                  ((-0.1, 0.1), (-0.09, 0.09), 0.11), ((-0.1, 0.1), (-0.05, 0.05), 0.08)):
            c.ci = lambda draws, level, _a=ci95, _b=ci90: _a if level == 95 else _b
            g = c.grade(synth(1), draws=20, seed=1, delta=delta)["c2"]
            got.append((g["rule_reading"], g["rule_not_lower"]))
    finally:
        c.ci = saved
    return eq(got, [("HIGHER", True), ("NOT LOWER, but statistically lower", True), ("NOT LOWER", True),
                    ("INCONCLUSIVE", False)])


@row("AH17", "N17 COMPOSITE: a trainer with NO common-species denominator (every run censored before it) is dropped "
             "from the mean over K*, never counted as 0")
def _ah17():
    won = {"ROXANNE": (True, True, 0)}
    runs = [rec("A", "Torchic", "P1", status="cut", keys=won), rec("B", "Torchic", "P2", status="cut", keys=won)]
    t = CA().grade(runs, draws=50, seed=1)["composite"]
    return eq((t["a"], t["b"]), (1.0, 1.0))


# ============================================================================================ DV — the coordinator's rulings
# One row per DECISION (F1-F11, RC-3) on the adversarial pass; each is reddened by a REVERT mutant in `MUTANTS`.
@row("DV1", "F1 void_reason: every automated STOP and an x4h error VOID; a user park, OK and OK — DEGRADED do not; a "
            "FAILED verdict nobody listed voids (fail-closed); --void always voids")
def _dv1():
    v = CA().void_reason
    got = [v({"verdict": f"FAILED — {s}"}) for s in ("ARM LEAK", "VACUITY", "ARM HEADER ASSERTION FAILED",
                                                     "EMULATION ASSERTION FAILED", "FREEZE BROKEN",
                                                     "x4h error: ValueError: boom", "interrupted by user (Ctrl-C)",
                                                     "something new")]
    got += [v({"verdict": "OK"}), v({"verdict": "OK — DEGRADED: lanes lost: H3 (arm A) after 2 spawn(s)"}), v(None),
            v({"verdict": "OK"}, "park at 3 AM")]
    return eq(got, ["STOP ARM LEAK", "STOP VACUITY", "STOP ARM HEADER ASSERTION FAILED",
                    "STOP EMULATION ASSERTION FAILED", "STOP FREEZE BROKEN", "STOP x4h error: ValueError: boom", None,
                    "STOP (an unrecognised FAILED verdict: 'FAILED — something new')", None, None, None,
                    "STOP-3 (manual --void): park at 3 AM"])


@row("DV2", "F1 a VOID reaches C1 AND C2 ('DESCRIPTIVE — VOID: STOP <reason> (DESIGN §4)', verdict VOID, in the JSON); "
            "the same data without it is CONFIRMATORY")
def _dv2():
    runs = synth(1)
    g = CA().grade(runs, draws=50, seed=1, void="STOP ARM LEAK")
    h = CA().grade(runs, draws=50, seed=1)
    want = "DESCRIPTIVE — VOID: STOP ARM LEAK (DESIGN §4)"
    return eq((g["c1"]["status"], g["c1"]["verdict"], g["c2"]["status"].startswith(want), g["c2"]["verdict"],
               g["void"], h["c1"]["status"], h["c2"]["status"], h["c2"]["verdict"] == h["c2"]["rule_reading"]),
              (want, "VOID", True, "VOID", "STOP ARM LEAK", "CONFIRMATORY", "CONFIRMATORY", True))


@row("DV3", "F1 end to end on M-16 batches: an ARM LEAK abort VOIDS; a user park STANDS; --void voids; no summary.json "
            "is PROVISIONAL")
def _dv3():
    a = log_text(ARMS["A"], battles=[fight(1000, 265, LEADER, "Won")])
    b = log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Won")])
    got = {}
    for name, kw, extra in (("dv3leak", {"verdict": "FAILED — ARM LEAK", "stop": "ARM LEAK"}, []),
                            ("dv3park", {"verdict": "FAILED — interrupted by user (Ctrl-C)",
                                         "stop": "interrupted by user (Ctrl-C)"}, []),
                            ("dv3void", {}, ["--void", "STOP-3 park"]),
                            ("dv3live", {"summary": False}, [])):
        d = batch16(name, a, b, **kw)
        j = TMP["root"] / f"{name}.json"
        code, text = cli([str(d), "--json", str(j)] + extra)
        g = json.loads(j.read_text(encoding="utf-8"))["grade"]
        got[name] = (code, g["void"], g["provisional"], g["c2"]["verdict"], g["c1"]["status"].split(" — ")[0],
                     "VOID: STOP ARM LEAK (DESIGN §4)" in text, "a user park STANDS" in text)
    return eq(got, {"dv3leak": (0, "STOP ARM LEAK", False, "VOID", "DESCRIPTIVE", True, False),
                    "dv3park": (0, None, False, "NOT ESTIMABLE", "CONFIRMATORY", False, True),
                    "dv3void": (0, "STOP-3 (manual --void): STOP-3 park", False, "VOID", "DESCRIPTIVE", False, False),
                    "dv3live": (0, None, True, "PROVISIONAL", "PROVISIONAL", False, False)})


@row("DV4", "F2 + F5: B never meets Tabitha, Maxie, Flannery -> NOT ESTIMABLE over the frozen K* (4 of 7), DESCRIPTIVE; "
            "draws in which a K* trainer is not estimable are UNDEFINED, counted and printed")
def _dv4():
    full = _all7(KEYS7)
    trunc = [rec("A", "Torchic", f"A{i}", keys=_all7(KEYS7, hp=0)) for i in range(3)] + \
            [rec("B", "Torchic", f"B{i}", keys=_all7(KEYS7, hp=2, skip=("TABITHA_MT_CHIMNEY", "MAXIE_MT_CHIMNEY",
                                                                        "FLANNERY"))) for i in range(3)]
    gt = CA().grade(trunc, draws=50, seed=1)
    g = gt["c2"]
    part = ([rec("A", "Torchic", f"A{i}", keys=full) for i in range(3)] + [rec("B", "Torchic", "B0", keys=full)]
            + [rec("B", "Torchic", f"B{i}", keys=_all7(KEYS7, skip=("FLANNERY",))) for i in (1, 2)])
    h = CA().grade(part, draws=400, seed=4)
    text = render(part, h)
    # the per-group θ follows the same frozen rule: the leaders without Flannery in B have no θ
    return eq((g["rule_reading"], g["verdict"], g["status"], g["theta_b"], gt["groups"]["leaders"]["point"],
               h["c2"]["n_estimable"], h["c2"]["point"], h["c2"]["nan_draws"] > 50,
               f"({h['c2']['nan_draws']} draws undefined, excluded)" in text, h["c2"]["rule_reading"]),
              ("NOT ESTIMABLE over the frozen K* (4 of 7)", "NOT ESTIMABLE",
               "DESCRIPTIVE — NOT ESTIMABLE over the frozen K* (4 of 7)", None, None, 7, 0.0, True, True, "NOT LOWER"))


@row("DV5", "F3 REACH DIFFERS is ON the C2 verdict line and in the JSON c2 object")
def _dv5():
    runs = ([rec("A", "Torchic", f"A{i}", keys=_all7(KEYS7)) for i in range(4)]
            + [rec("B", "Torchic", f"B{i}", keys=_all7(KEYS7, skip=("WATTSON",))) for i in range(4)])
    g = CA().grade(runs, draws=200, seed=2)
    line = [ln for ln in render(runs, g).splitlines() if ln.strip().startswith("→ C2:")]
    return eq((g["c2"]["reach_differs"], len(line) == 1 and "⚠ REACH DIFFERS (WATTSON)" in line[0]), (["WATTSON"], True))


@row("DV6", "F4 completeness: an interrupted collection (with the --tag hint), a provisional summary, a lane with zero "
            "logs, a lane whose logs != debug_logs_collected all FAIL; LIVE ignores the collection; exit 1 end to end")
def _dv6():
    f = CA().completeness_failures
    lanes = [{"tag": "H1", "arm": "A"}, {"tag": "H2", "arm": "B"}]
    ok = {"lanes": {"H1": {"debug_logs_collected": 2}, "H2": {"debug_logs_collected": 1}},
          "collect_interrupted": False, "provisional": False}
    full = {"H1": 2, "H2": 1}
    got = (f(lanes, full, ok, live=False), len(f(lanes, full, {**ok, "collect_interrupted": True}, live=False)),
           "compare_arms.py --tag s14" in " ".join(f(lanes, full, {**ok, "collect_interrupted": True}, live=False,
                                                     tag="s14")),
           len(f(lanes, full, {**ok, "provisional": True}, live=False)), len(f(lanes, {"H1": 2}, ok, live=False)),
           len(f(lanes, {"H1": 1, "H2": 1}, ok, live=False)),
           f(lanes, {"H1": 1, "H2": 1}, {**ok, "collect_interrupted": True, "provisional": True}, live=True),
           len(f(lanes, {"H1": 1}, None, live=True)), f(lanes, full, None, live=False))
    a = log_text(ARMS["A"], battles=[fight(1000, 265, LEADER, "Won")])
    b = log_text(ARMS["B"], battles=[fight(1000, 265, LEADER, "Won")])
    code1, out1 = cli([str(batch16("dv6int", a, b, interrupted=True))])
    code2, out2 = cli([str(batch16("dv6col", a, b, collected={"H12": 2}))])
    ends = (code1, "INTERRUPTED" in out1 and "--tag" in out1, "C2 —" in out1, code2, "H12: 1 log(s) read" in out2)
    return eq((got, ends), (([], 1, True, 1, 1, 1, [], 1, []), (1, True, False, 1, True)))


@row("DV7", "F6 the pre-registered δ comes from the design (16x2 .08, 8x2 .11, anything else none); any draws / seed / "
            "δ off the pre-registration is EXPLORATORY; no pre-registered δ and no --delta is exit 2")
def _dv7():
    p, x = CA().preregistered_delta, CA().exploratory_reasons

    def m(n, arms=2, lanes_n=True):
        return {"raw": {"lanes_n": n} if lanes_n else {}, "lanes": [{}] * n, "arms": dict.fromkeys("ABC"[:arms])}
    table = (p(m(16)), p(m(8)), p(m(24, 3)), p(m(12)), p(m(16, lanes_n=False)), x(10000, 14, .08, .08),
             len(x(400, 14, .08, .08)), len(x(10000, 15, .08, .08)), len(x(10000, 14, .1, .08)),
             len(x(10000, 14, .08, None)))
    g = CA().grade(synth(1), draws=50, seed=1, exploratory=["seed 15 (pre-registered 14)"])
    small = make_batch("dv7small", [("A", [("a.log", log_text(ARMS["A"]))]), ("B", [("b.log", log_text(ARMS["B"]))])])
    j = TMP["root"] / "dv7.json"
    code, _ = cli([str(batch16("dv7", log_text(ARMS["A"]), log_text(ARMS["B"]))), "--draws", "2000", "--json", str(j)])
    cj = json.loads(j.read_text(encoding="utf-8"))["grade"]["c2"]
    return eq((table, g["c1"]["status"], g["c2"]["verdict"], cli([str(small)])[0], code,
               cj["status"].startswith("EXPLORATORY — EXPLORATORY: draws 2000"), cj["verdict"]),
              ((0.08, 0.11, None, None, 0.08, [], 1, 1, 1, 1),
               "EXPLORATORY — EXPLORATORY: seed 15 (pre-registered 14)", "EXPLORATORY", 2, 0, True, "EXPLORATORY"))


@row("DV8", "F7 the JSON carries rule_reading apart from verdict: verdict = the rule's word only when CONFIRMATORY; no "
            "bare `reading` / `not_lower` fields")
def _dv8():
    conf = CA().grade(synth(1), draws=50, seed=1)["c2"]
    desc = CA().grade(synth(1, heal="equal"), draws=50, seed=1)["c2"]
    return eq((conf["status"], conf["verdict"] == conf["rule_reading"], desc["verdict"],
               desc["rule_reading"] in ("NOT LOWER", "HIGHER", "INCONCLUSIVE", "NOT LOWER, but statistically lower"),
               "reading" in conf, "not_lower" in conf),
              ("CONFIRMATORY", True, "DESCRIPTIVE", True, False, False))


@row("DV9", "F8 only Torchic / Mudkip / Treecko are strata, and the species must match `Story: choosing X!` (a "
            "mismatch or a missing line is excluded and listed)")
def _dv9():
    c = CA()
    mism = [ln.replace("choosing Treecko", "choosing Mudkip") for ln in log_text(ARMS["A"])]
    nochoose = [ln for ln in log_text(ARMS["A"]) if "Story: choosing" not in ln]
    kinds = [c.run_record(lines, log="x", lane=LANE_A, arms=ARMS)["excluded_kind"]
             for lines in (log_text(ARMS["A"], species="Pikachu"), mism, nochoose, log_text(ARMS["A"]))]
    return eq(kinds, ["not_a_starter", "chosen_mismatch", "chosen_mismatch", None])


@row("DV10", "F9 complete runs that never got a starter are counted per arm (a CUT one is not)")
def _dv10():
    runs = []
    for arm, status in (("A", "complete"), ("A", "cut"), ("B", "complete"), ("B", "complete")):
        r = rec(arm, None, None, status=status)
        r["excluded"], r["excluded_kind"] = "no starter read", "no_starter"
        runs.append(r)
    return eq(CA().controls(runs)[1]["complete_no_starter_per_arm"], {"A": 1, "B": 2})


@row("DV11", "F10 a run CENSORED DURING its first attempt at X (cut or lost; met, undecided) is OUT of X's reach and "
             "composite denominators and listed; a COMPLETE run met-but-undecided stays a 'no'")
def _dv11():
    runs = [rec("A", "Torchic", "P1", keys={"ROXANNE": (True, True, 0)}),
            rec("A", "Torchic", "P2", status="cut", keys={"ROXANNE": (True, None, None)}),
            rec("A", "Torchic", "P3", status="lost", keys={"ROXANNE": (True, None, None)}),
            rec("A", "Torchic", "P4", keys={"ROXANNE": (True, None, None)}),
            rec("B", "Torchic", "P5", keys={"ROXANNE": (True, True, 0)})]
    g = CA().grade(runs, draws=50, seed=1)
    t = g["trainers"]["ROXANNE"]
    return eq((t["reach_n"]["A"], close(t["reach_a"], 1.0), len(t["censored_during"]["A"]),
               close(g["composite"]["a"], 0.5 / 7), close(g["composite"]["b"], 1.0 / 7)), (2, True, 2, True, True))


@row("DV12", "F11 a LOST log with no header is EXCLUDED, not refused (like a cut one)")
def _dv12():
    r = CA().run_record(header(None, complete=False), log="x", lane=LANE_A, arms=ARMS, lost=True)
    return eq((bool(r["excluded"]), bool(r["refused"]), r["excluded_kind"]), (True, False, "no_header"))


@row("DV13", "RC-3 C1 that cannot be computed reads C1 NOT ESTIMABLE (rule, status, report), never FAIL")
def _dv13():
    runs = [rec("A", "Torchic", "P1"), rec("B", "Torchic", "P2")]
    g = CA().grade(runs, draws=50, seed=1)
    text = render(runs, g)
    return eq((g["c1"]["rule_reading"], g["c1"]["status"], "C1 NOT ESTIMABLE" in g["c2"]["status"],
               "→ C1 NOT ESTIMABLE: C2 is DESCRIPTIVE" in text, "→ C1 FAIL" in text),
              ("NOT ESTIMABLE", "DESCRIPTIVE — C1 NOT ESTIMABLE", True, True, False))


# ============================================================================================ fixtures on disk
def make_batch(name, lanes, cut=None, provisional=False, summary=True, profiles_tag=None, verdict="OK",
               stop="deadline", interrupted=False, collected=None) -> pathlib.Path:
    """A batch directory in T1's layout: `ARMS.json` (the REAL arms; `lanes_n` = the lane count, as T1 writes it),
    `L<nn>/debug-logs/*.log`, `summary.json` (its verdict / stop / `collect_interrupted`, and per lane the cut log and
    `debug_logs_collected` = the logs written, unless `collected` overrides a lane's). `lanes` = [(arm, [(log name,
    lines)])] in slot order. With `profiles_tag`, the logs ALSO go to a fake MAIN checkout's lane profiles
    (`<root>/<name>-main/sandbox-pokebot/profiles/endless-<tag>-H<n>-x/debug-logs`)."""
    d = TMP["root"] / name
    d.mkdir()
    rows = []
    for slot, (arm, logs) in enumerate(lanes):
        tag = f"H{slot + 1}"
        profile = f"endless-{profiles_tag or 'p'}-{tag}-x"
        rows.append({"tag": tag, "slot": slot, "arm": arm, "starter": "x", "name": tag, "profile": profile})
        dirs = [d / f"L{slot + 1:02d}" / "debug-logs"]
        if profiles_tag:
            dirs.append(TMP["root"] / f"{name}-main" / "sandbox-pokebot" / "profiles" / profile / "debug-logs")
        for dd in dirs:
            dd.mkdir(parents=True)
            for log, lines in logs:
                (dd / log).write_text("\n".join(lines) + "\n", encoding="utf-8")
    (d / "ARMS.json").write_text(json.dumps({"stamp": name, "profile_tag": profiles_tag, "arms_sha256": "0" * 64,
                                             "code_commit": "test", "arms_text": json.dumps({"arms": ARMS}),
                                             "lanes_n": len(rows), "lanes": rows}), encoding="utf-8")
    if summary:
        per = {r["tag"]: {"cut_log": (cut or {}).get(r["tag"]), "spawns": [],
                          "debug_logs_collected": (collected or {}).get(r["tag"], len(lanes[r["slot"]][1]))}
               for r in rows}
        body = ({"provisional": True, "verdict": "OK (provisional)", "stop_reason": stop, "lanes": per} if provisional
                else {"verdict": verdict, "stop_reason": stop, "lanes": len(rows), "lanes_detail": per,
                      "lanes_lost": [], "collect_interrupted": interrupted})
        (d / "summary.json").write_text(json.dumps(body), encoding="utf-8")
    return d


def batch16(name, a_lines, b_lines, **kw) -> pathlib.Path:
    """A 16-lane, two-arm batch (M-16: the pre-registered δ .08 applies), one log per lane."""
    return make_batch(name, [("A", [("a-debug-20261001-210000.log", a_lines)])] * 8
                      + [("B", [("b-debug-20261001-210000.log", b_lines)])] * 8, **kw)


def build_tree(root: pathlib.Path) -> dict:
    x4 = root / "x4"
    for n in list(range(1, 17)) + [100]:
        p = x4 / "x4-runs" / "S16" / f"L{n:02d}" / "debug-logs"
        p.mkdir(parents=True)
        (p / "r.log").write_text("x\n", encoding="utf-8")
    for extra in ("M01/debug-logs/r.log", "Lx1/debug-logs/r.log", "L01/debug-logs/r.txt", "L02/stdout.log"):
        p = x4 / "x4-runs" / "S16" / extra
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    (x4 / "x4-runs" / "S16" / "L03" / "debug-logs" / "dir.log").mkdir()
    main = root / "main"
    (main / "tools").mkdir(parents=True)
    import shutil
    shutil.copytree(x4 / "x4-runs", main / "tools" / "story-dev" / "x4-runs")
    prof = main / "sandbox-pokebot" / "profiles"
    for f in ("endless-s14-H1-torchic/debug-logs/b.log", "endless-s14-H1-torchic/debug-logs/Old/a.log",
              "endless-s14-H1-torchic/debug-logs/a.log",
              "endless-s14-H10-mudkip/debug-logs/c.log", "endless-s14smoke-H1-torchic/debug-logs/d.log",
              "endless-s14-x/debug-logs/e.log", "endless-P1-Mudkip/debug-logs/f.log"):
        p = prof / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    (root / "empty").mkdir()
    return {"root": root, "x4": x4, "main": main}


# ============================================================================================ mutants
#: (label, target, [(old, new)], the EXACT set of FAST rows it must turn red). Written before the first run.
_POOLED_RESAMPLE = '''    for arm in sorted({k[0] for k in strata}):
        keys = sorted((k for k in strata if k[0] == arm), key=lambda k: str(k[1]))
        sizes = [strata[k]["C"] for k in keys]
        total = sum(sizes)
        big = np.ones((1, total)) if rng is None else rng.multinomial(total, np.full(total, 1.0 / total), size=draws).astype(float)
        at = 0
        for skey, C in zip(keys, sizes):
            st = strata[skey]
            wt = big[:, at:at + C]
            at += C
            out[skey] = {f: wt @ st[f] for f in FIELDS_K + FIELDS_1}
'''
_STRATIFIED_RESAMPLE = '''    for skey in sorted(strata, key=lambda k: (str(k[0]), str(k[1]))):
        st = strata[skey]
        C = st["C"]
        if rng is None:
            wt = np.ones((1, C))
        else:
            wt = rng.multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)
        out[skey] = {f: wt @ st[f] for f in FIELDS_K + FIELDS_1}
'''
_FIRST_IF = "            if out[key] is None and starts & set(ids) and ends & set(ids):"
_STATUS = '    status = "cut" if cut else "lost" if lost else "capped" if capped else "complete"'
MUTANTS: list = [
    # ---- T2: battle_log.py
    ("B01 a start with no end is a first attempt", "bl",
     [(_FIRST_IF, "            if out[key] is None and starts & set(ids):")], {"TB9"}),
    ("B02 the first attempt is the LAST match (first= is True on every attempt)", "bl",
     [(_FIRST_IF, "            if starts & set(ids) and ends & set(ids):")], {"CA5", "TB9"}),
    ("B03 a Draw is not a loss", "bl", [('    if res in ("Lost", "Draw"):', '    if res == "Lost":')], {"TB9", "CR2"}),
    ("B04 keys_met needs a finished battle", "bl",
     [("        met |= {key for key, ids in ids_of.items() if starts & set(ids)}",
       "        met |= {key for key, ids in ids_of.items() if starts & set(ids) and _ends & set(ids)}")], {"TB10", "AH5"}),
    ("B05 env-all read past the header's end", "bl",
     [("        if line.startswith(HEADER_END):\n            return None\n        m = _ENV_ALL_LINE",
       "        m = _ENV_ALL_LINE")], {"TB1"}),
    ("B06 a non-dict env-all accepted", "bl",
     [("            return got if isinstance(got, dict) else None", "            return got")], {"TB1"}),
    ("B07 the arm by SUBSET (a leaked key tolerated)", "bl",
     [("    hits = [name for name, spec in arms.items() if env is not None and env == spec]",
       "    hits = [name for name, spec in arms.items() if env is not None and "
       "all(env.get(k) == v for k, v in spec.items())]")], {"TB2", "CX3"}),
    ("B08 ambiguous resolved to the first match", "bl",
     [('    if len(hits) > 1:\n        return "ambiguous"\n', "")], {"TB2"}),
    ("B09 identity from a LATER [hb] when the first does not parse", "bl",
     [("        if not ids_seen and _HB_LINE.match(line):",
       '        if out["species"] is None and _HB_LINE.match(line):')], {"TB3"}),
    ("B10 the empty ids=[] heartbeat taken as the identity line", "bl",
     [('            if opened and opened.group(1) != "]":', "            if opened:")],
     {"CA10", "CR1", "CX1", "CX2", "AH5", "DV3", "DV7", "DV9"}),
    ("B11 hold None when absent", "bl",
     [('    out = {"species": None, "pid": None, "hold": 0, "chosen": None}',
       '    out = {"species": None, "pid": None, "hold": None, "chosen": None}')], {"TB3"}),
    ("B12 the PID not normalised to upper case", "bl",
     [('out["species"], out["pid"] = m.group(1), m.group(2).upper()',
       'out["species"], out["pid"] = m.group(1), m.group(2)')], {"TB3"}),
    ("B13 log_capped never fires", "bl",
     [("    return any(CAP_MARKER in line for line in lines)", "    return False")], {"TB4", "CR1"}),
    ("B14 batch_logs reads every directory", "bl",
     [('root.glob("L*") if p.is_dir() and _LANE_DIR.fullmatch(p.name)', 'root.glob("*") if p.is_dir()')],
     {"TB5", "TB6", "TB8"}),
    ("B15 the OLD L0* lanes (L10-L16 missed)", "bl",
     [('_LANE_DIR = re.compile(r"L\\d{2,}")', '_LANE_DIR = re.compile(r"L0\\d")')],
     {"TB5", "TB6", "TB8", "CR4", "CX2", "DV3", "DV6", "DV7"}),
    ("B16 x4_logs resolves under the WORKTREE", "bl",
     [('else main_story_dev()) / "x4-runs" / stamp)', 'else HERE) / "x4-runs" / stamp)')], {"TB6"}),
    ("B17 live_logs endless-<tag>* (s14 reads s14smoke)", "bl",
     [('root.glob(f"endless-{glob.escape(tag)}-H*")', 'root.glob(f"endless-{glob.escape(tag)}*")')], {"TB7", "TB8"}),
    ("B18 live_logs ignores Old/", "bl",
     [('        for sub in ("debug-logs", "debug-logs/Old"):', '        for sub in ("debug-logs",):')], {"TB7"}),
    ("B19 live_logs reads a name in both folders twice", "bl",
     [("                    found[(lane.name, q.name)] = q", "                    found[(lane.name, sub, q.name)] = q")],
     {"TB7", "TB8"}),
    ("B20 zero logs accepted", "bl",
     [('    if not paths:\n        ap.error(f"ZERO debug logs', '    if False:\n        ap.error(f"ZERO debug logs')], {"TB8"}),
    ("B21 --tag / --batch-dir are not modes (no conflict check)", "bl",
     [("    modes = sum(bool(x) for x in (args.stamp, args.since or args.until, args.logs, tag, batch_dir))",
       "    modes = sum(bool(x) for x in (args.stamp, args.since or args.until, args.logs))")], {"TB8"}),
    ("B22 every log has a header", "bl",
     [("    return any(line.startswith(HEADER_END) for line in lines)", "    return True")], {"CR1", "DV12"}),
    ("BM1 MENTION ONLY: a docstring quoting a `first=` filter turns NOTHING red", "bl",
     [("    read: it stays True on every lost re-attempt (`trainer_identity.is_first_fight`; review S10).",
       '    read: never `if t["first"] == "True"` (`trainer_identity.is_first_fight`; review S10).')], set()),
    # ---- T3: compare_arms.py — the estimand
    ("C01 the cluster is the RUN", "ca",
     [('        c = stratum.get((r["arm"], r["species"], r["pid"]))',
       '        c = stratum.get((r["arm"], r["species"], r["pid"], r["log"]))'),
      ('            stratum[(r["arm"], r["species"], r["pid"])] = c',
       '            stratum[(r["arm"], r["species"], r["pid"], r["log"])] = c')], {"CA6"}),
    ("C02 a cluster DE-DUPLICATED (its first run only)", "ca",
     [('        c = stratum.get((r["arm"], r["species"], r["pid"]))\n        if c is None:',
       '        c = stratum.get((r["arm"], r["species"], r["pid"]))\n        if c is not None:\n            continue\n'
       '        if c is None:')], {"CA6"}),
    ("C03 resampled within ARM (species not a stratum)", "ca", [(_STRATIFIED_RESAMPLE, _POOLED_RESAMPLE)], {"CS1"}),
    ("C04 one cluster per stratum per draw", "ca",
     [("            wt = rng.multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)",
       "            wt = rng.multinomial(1, np.full(C, 1.0 / C), size=draws).astype(float)")], {"CA6", "AH9"}),
    ("C05 species POOLED (a ratio of sums) instead of the equal-weight mean", "ca",
     [("    cnt = np.zeros((D, K))\n    for sp in species:\n        na, nb",
       "    den = {a: np.zeros((D, K)), b: np.zeros((D, K))}\n    cnt = np.zeros((D, K))\n    for sp in species:\n"
       "        na, nb"),
      ('        num[a] += np.where(ok, _ratio(g(a, sp, "W"), na), 0.0)\n'
       '        num[b] += np.where(ok, _ratio(g(b, sp, "W"), nb), 0.0)\n        cnt += ok\n'
       '    px = {arm: _ratio(num[arm], cnt) for arm in (a, b)}',
       '        num[a] += np.where(ok, g(a, sp, "W"), 0.0)\n        num[b] += np.where(ok, g(b, sp, "W"), 0.0)\n'
       '        den[a] += np.where(ok, na, 0.0)\n        den[b] += np.where(ok, nb, 0.0)\n        cnt += ok\n'
       '    px = {arm: _ratio(num[arm], den[arm]) for arm in (a, b)}')], {"CS2", "AH3"}),
    ("C06 a species ONE arm fought is included", "ca",
     [("        ok = (na > 0) & (nb > 0)", "        ok = (na > 0) | (nb > 0)")], {"CS2", "CS3", "DV4"}),
    # RE-ANCHORED with DECISION F2 (θ is now a plain mean over the frozen K*): the same idea, a NaN read as 0
    ("C07 θ counts an unestimable trainer as 0", "ca",
     [('    out["theta_a"], out["theta_b"] = px[a].mean(axis=1), px[b].mean(axis=1)',
       '    out["theta_a"], out["theta_b"] = np.nan_to_num(px[a]).mean(axis=1), np.nan_to_num(px[b]).mean(axis=1)')],
     {"CS3", "DV4"}),
    ("C08 REACH: a cut run that never met X is a 'no'", "ca",
     [('            elif r["status"] == "complete":', '            elif r["status"] in ("complete", "cut"):')],
     {"CS4", "AH4", "AH17"}),
    ("C09 REACH: only a COMPLETE run's meeting counts", "ca",
     [('            if k["reached"]:', '            if k["reached"] and r["status"] == "complete":')], {"CS4", "AH17"}),
    ("C10 COMPOSITE conditional on meeting X", "ca",
     [('        da, db = g(a, sp, "RD"), g(b, sp, "RD")', '        da, db = g(a, sp, "RN"), g(b, sp, "RN")')],
     {"CS5", "AH4", "DV11"}),
    ("C11 C1 pools the attempts (not the per-run mean)", "ca",
     [("    return sum(vals) / len(vals) if vals else None", "    return sum(vals) if vals else None"),
      ('            c["Hn"] += 1',
       '            c["Hn"] += sum(1 for k in r["keys"].values() if k["attempted"] and k["hp"] is not None)')],
     {"CS6"}),
    ("C12 C1 counts an unreadable heal stock as 0", "ca",
     [('    vals = [k["hp"] for k in run["keys"].values() if k["attempted"] and k["hp"] is not None]',
       '    vals = [k["hp"] or 0 for k in run["keys"].values() if k["attempted"]]')], {"CS6"}),
    ("C13 C5 = the mean of per-run ratios", "ca",
     [('        c["L5"] += r["nonkey"]["lost"]\n        c["B5"] += r["nonkey"]["won"] + r["nonkey"]["lost"]\n',
       '        c["L5"] += r["nonkey"]["lost"] / max(1, r["nonkey"]["won"] + r["nonkey"]["lost"])\n'
       '        c["B5"] += 1\n')], {"CA8"}),
    ("C14 C5 counts undecided battles in the denominator", "ca",
     [('        c["B5"] += r["nonkey"]["won"] + r["nonkey"]["lost"]\n',
       '        c["B5"] += r["nonkey"]["won"] + r["nonkey"]["lost"] + r["nonkey"]["other"]\n')], {"CA8"}),
    # ---- T3: refusal, controls, the sequence, the verdicts
    ("C15 the arm refusal is off (a wrong-arm log is re-assigned)", "ca",
     [('    elif arm != lane.get("arm"):', '    elif arm == "ambiguous":')], {"CA7", "CR1", "AH12"}),
    ("C16 a refused log does not fail the controls", "ca",
     [("    if refused:\n        failures.append(", "    if False:\n        failures.append(")], {"CA7"}),
    ("C17 an arm with no usable runs passes", "ca",
     [("        if not per_arm.get(arm):", "        if False:")], {"CX1"}),
    ("C18 zero runs passes", "ca",
     [('    if not runs:\n        failures.append("ZERO runs', '    if False:\n        failures.append("ZERO runs')], {"CX1"}),
    # C19 / C20 RE-ANCHORED with DECISIONS F1-F7 (the status is now composed from its reasons)
    ("C19 the C1 -> C2 gate removed (C2 always confirmatory)", "ca",
     [("    if not c1_pass:\n        c2_reasons.append(", "    if False:\n        c2_reasons.append(")],
     {"CA9", "AH1", "DV8", "DV13"}),
    ("C20 the report prints C2's word as if confirmatory", "ca",
     [('    word = (c2["rule_reading"] if c2["status"] == "CONFIRMATORY"', '    word = (c2["rule_reading"] if True')],
     {"CA9"}),
    ("C21 C1 PASS on the 90% CI", "ca",
     [('    c1_pass = nz(c1["ci95"][0]) > 0', '    c1_pass = nz(c1["ci90"][0]) > 0')], {"CS7", "AH1"}),
    ("C22 C2's word on the 90% CI", "ca",
     [('    lo95, hi95 = nz(c2["ci95"][0]), nz(c2["ci95"][1])', '    lo95, hi95 = nz(c2["ci90"][0]), nz(c2["ci90"][1])')],
     {"CS7", "AH16"}),
    ("C23 C2 LOWER on the 95% CI", "ca",
     [('"lower_flag": bool(nz(c2["ci90"][1]) < 0), "n_estimable"', '"lower_flag": bool(nz(c2["ci95"][1]) < 0), "n_estimable"')],
     {"CS7", "AH1"}),
    ("C24 C5's flag on the 95% CI", "ca",
     [('"flag": c5_flag(nz(c5["ci90"][0]), nz(c5["ci90"][1])),', '"flag": c5_flag(nz(c5["ci95"][0]), nz(c5["ci95"][1])),')],
     {"CS7", "AH1"}),
    ("C25 REACH on the 95% CI", "ca",
     [('        lo, hi = nz(r["ci90"][0]), nz(r["ci90"][1])', '        lo, hi = nz(r["ci95"][0]), nz(r["ci95"][1])')],
     {"CS7", "AH1"}),
    ("C26 the group LOWER flag on the 95% CI", "ca",
     [('"lower_flag": bool(nz(gr["ci90"][1]) < 0)}', '"lower_flag": bool(nz(gr["ci95"][1]) < 0)}')], {"CS7", "AH1"}),
    ("C27 NOT LOWER at lower95 == −δ (not strict)", "ca", [("    if lo95 > -delta:", "    if lo95 >= -delta:")], {"CV1"}),
    ("C28 HIGHER at lower95 == 0 (not strict)", "ca",
     [('    if lo95 > 0:\n        return "HIGHER"', '    if lo95 >= 0:\n        return "HIGHER"')], {"CV1", "DV4"}),
    ("C29 'statistically lower' precedence dropped", "ca",
     [('        return "NOT LOWER, but statistically lower" if hi95 < 0 else "NOT LOWER"', '        return "NOT LOWER"')],
     {"CV1", "AH16"}),
    ("C30 δ hard-coded (.08)", "ca", [("    if lo95 > -delta:", "    if lo95 > -0.08:")], {"CV1", "AH16"}),
    ("C31 REGRESSION at lower90 == 0 (not strict)", "ca",
     [('    if lo90 > 0:\n        return "REGRESSION"', '    if lo90 >= 0:\n        return "REGRESSION"')], {"CV2"}),
    ("C32 ci: one-sided tails", "ca",
     [("    lo, hi = np.percentile(d, [50 - level / 2, 50 + level / 2])", "    lo, hi = np.percentile(d, [100 - level, level])")],
     {"CV3"}),
    ("C33 ci keeps NaN draws", "ca", [("    d = d[~np.isnan(d)]\n", "")], {"CV3", "DV4"}),
    # ---- T3: the run's status and the readers
    ("C34 the status ignores the cut record", "ca", [(_STATUS, '    status = "lost" if lost else "capped" if capped else "complete"')],
     {"CR1", "CR4", "AH5"}),
    ("C35 capped outranks cut", "ca",
     [(_STATUS, '    status = "capped" if capped else "cut" if cut else "lost" if lost else "complete"')], {"CR1"}),
    # C36 / C37 RE-ANCHORED with DECISIONS F11 / F8 (the rules moved, their mutants did not change meaning)
    ("C36 a cut or lost log with no header is REFUSED", "ca", [("    if (cut or lost) and not header:", "    if False:")],
     {"CR1", "DV12"}),
    ("C37 a run with no starter is kept (then caught as not-a-starter: the KIND is what changes)", "ca",
     [("    elif species is None:", "    elif False:")], {"CR1"}),
    ("C38 lost_logs ignores x4h's own stop", "ca",
     [('        if sp.get("end") is None or sp.get("stopped_by") == "x4h" or sp.get("exit") == 0:',
       '        if sp.get("end") is None or sp.get("exit") == 0:')], {"CR3"}),
    ("C39 lost_logs marks the OLDEST log", "ca",
     [("            out.add(max(inside, key=lambda n: (stamps[n], n)))", "            out.add(min(inside, key=lambda n: (stamps[n], n)))")],
     {"CR3"}),
    ("C40 LIVE: the newest log is not the cut one", "ca",
     [("            cut_name = names[-1] if names else None", "            cut_name = None")], {"CR4"}),
    ("C41 the PROVISIONAL summary ignored", "ca",
     [('        detail = s.get("lanes") if isinstance(s.get("lanes"), dict) else {}', "        detail = {}")], {"CR4"}),
    ("C42 the lane slot off by one", "ca",
     [("            lane = by_slot.get(int(m.group(1)) - 1) if m else None",
       "            lane = by_slot.get(int(m.group(1))) if m else None")], {"CR4", "CA7", "CX1", "CX2", "DV3", "DV7"}),
    ("C43 K*: May's three Route 110 ids dropped", "ca",
     [('    "RIVAL_ROUTE_110": (521, 524, 527, 530, 533, 536),', '    "RIVAL_ROUTE_110": (521, 524, 527),')], {"CK1"}),
    ("C44 the default seed is not 14", "ca", [("DEFAULT_SEED = 14", "DEFAULT_SEED = 15")], {"CX2", "DV7"}),
    # RE-ANCHORED with DECISION F6 (δ now comes from the design table)
    ("C45 the M-16 δ is not .08", "ca",
     [("PREREG_DELTA = {(16, 2): 0.08, (8, 2): 0.11}", "PREREG_DELTA = {(16, 2): 0.10, (8, 2): 0.11}")], {"CX2", "DV7"}),
    ("C46 a FAILED control still prints a grade", "ca",
     [("    result = None if failures else grade(", "    result = grade("),
      ('    if failures:\n        out.append("⛔ INSTRUMENT CONTROL FAILED', '    if False:\n        out.append("⛔ INSTRUMENT CONTROL FAILED')],
     {"CA7", "CX1", "CX3", "DV6"}),
    # ---- the INDEPENDENT hunter's survivors (X<n>, `evidence/2026-10-01-batch14-T23-ADVERSARIAL.txt`), re-anchored
    # where the code moved; each must now be red on the AH row that was proposed for it
    ("H74 a CUT log's arm is not checked", "ca",
     [('    elif arm != lane.get("arm"):', '    elif arm != lane.get("arm") and not cut:')], {"AH12"}),
    ("H36 C2 LOWER read on lower90 < 0", "ca",
     [('"lower_flag": bool(nz(c2["ci90"][1]) < 0), "n_estimable"', '"lower_flag": bool(nz(c2["ci90"][0]) < 0), "n_estimable"')],
     {"AH1"}),
    ("H38 the group LOWER flag read on lower90 < 0", "ca",
     [('"lower_flag": bool(nz(gr["ci90"][1]) < 0)}', '"lower_flag": bool(nz(gr["ci90"][0]) < 0)}')], {"AH1"}),
    ("H39 REACH DIFFERS whenever the 90% CI is not exactly [0, 0]", "ca",
     [('            "reach_differs": bool(lo > 0 or hi < 0),', '            "reach_differs": bool(hi > 0 or lo < 0),')], {"AH1"}),
    ("H37 C2 LOWER at upper90 <= 0", "ca",
     [('"lower_flag": bool(nz(c2["ci90"][1]) < 0), "n_estimable"', '"lower_flag": bool(nz(c2["ci90"][1]) <= 0), "n_estimable"')],
     {"AH2"}),
    ("H40 REACH DIFFERS non-strict (a [0, 0] CI flags)", "ca",
     [('            "reach_differs": bool(lo > 0 or hi < 0),', '            "reach_differs": bool(lo >= 0 or hi <= 0),')],
     {"AH2", "DV5"}),   # DV5 FOUND BY THE RUN (my prediction missed it): DV5's six other trainers have [0, 0] CIs
    ("H31 C2 confirmatory when C1's POINT is > 0", "ca",
     [("    if not c1_pass:\n        c2_reasons.append(", '    if not nz(c1["point"]) > 0:\n        c2_reasons.append(')],
     {"AH1"}),
    ("H32 C2 confirmatory when C1's lower90 > 0", "ca",
     [("    if not c1_pass:\n        c2_reasons.append(", '    if not nz(c1["ci90"][0]) > 0:\n        c2_reasons.append(')],
     {"AH1"}),
    ("H47 REACH 'met' := a DECIDED first attempt", "ca",
     [('            if k["reached"]:\n                c["RN"][j] += 1', '            if k["won"] is not None:\n                c["RN"][j] += 1')],
     {"AH5", "DV11"}),
    ("H48 C2 'fought' := met (an undecided meeting counts as a loss)", "ca",
     [('            if k["won"] is not None:\n                c["N"][j] += 1', '            if k["reached"]:\n                c["N"][j] += 1')],
     {"AH5"}),
    ("H65 an 'other'-outcome first attempt counted as a loss", "ca",
     [('        won = None if fa is None or fa["outcome"] not in ("won", "lost") else fa["outcome"] == "won"',
       '        won = None if fa is None else fa["outcome"] == "won"')], {"AH5"}),
    ("H63 a CUT run's completed first attempts dropped from C2", "ca",
     [('            if k["won"] is not None:\n                c["N"][j] += 1',
       '            if k["won"] is not None and r["status"] == "complete":\n                c["N"][j] += 1')], {"AH6"}),
    ("H64 a CUT run dropped from C1", "ca",
     [("        v = run_c1(r)\n", '        v = run_c1(r) if r["status"] == "complete" else None\n')], {"AH6"}),
    ("H01 C2 species weighted by N_A + N_B", "ca",
     [("    cnt = np.zeros((D, K))\n    for sp in species:\n        na, nb",
       "    cnt = np.zeros((D, K))\n    wsum = np.zeros((D, K))\n    for sp in species:\n        na, nb"),
      ('        num[a] += np.where(ok, _ratio(g(a, sp, "W"), na), 0.0)\n'
       '        num[b] += np.where(ok, _ratio(g(b, sp, "W"), nb), 0.0)\n        cnt += ok\n'
       '    px = {arm: _ratio(num[arm], cnt) for arm in (a, b)}',
       '        num[a] += np.where(ok, _ratio(g(a, sp, "W"), na) * (na + nb), 0.0)\n'
       '        num[b] += np.where(ok, _ratio(g(b, sp, "W"), nb) * (na + nb), 0.0)\n'
       '        wsum += np.where(ok, na + nb, 0.0)\n        cnt += ok\n'
       '    px = {arm: _ratio(num[arm], wsum) for arm in (a, b)}')], {"AH3"}),
    ("H07 C1 species-weighted", "ca",
     [('        out[f"c1_{tag}"] = _ratio(sum(g(arm, sp, "H") for sp in species), sum(g(arm, sp, "Hn") for sp in species))',
       '        out[f"c1_{tag}"] = np.nanmean(np.stack([_ratio(g(arm, sp, "H"), g(arm, sp, "Hn")) for sp in species]), axis=0)')],
     {"AH8"}),
    ("H49 COMPOSITE denominator = ALL runs (censored included)", "ca",
     [('        da, db = g(a, sp, "RD"), g(b, sp, "RD")',
       '        da, db = g(a, sp, "NR")[:, None] + 0 * g(a, sp, "RD"), g(b, sp, "NR")[:, None] + 0 * g(b, sp, "RD")')],
     {"AH4", "AH17", "DV11"}),
    ("H04 COMPOSITE: a species with reach runs in ONE arm only included", "ca",
     [("        ok = (da > 0) & (db > 0)", "        ok = (da > 0) | (db > 0)")], {"AH4"}),
    ("H51 COMPOSITE: a trainer with no common denominator counted as 0", "ca",
     [('    out["comp_a"] = _nanmean(_ratio(cnum[a], ccnt))\n    out["comp_b"] = _nanmean(_ratio(cnum[b], ccnt))',
       '    out["comp_a"] = np.nan_to_num(_ratio(cnum[a], ccnt)).mean(axis=1)\n'
       '    out["comp_b"] = np.nan_to_num(_ratio(cnum[b], ccnt)).mean(axis=1)')], {"AH17"}),
    ("H56 C5 counts UNCLASSIFIED battles", "ca",
     [("        if bl.battle_class(battle, telemetry) == bl.NONKEY:",
       "        if bl.battle_class(battle, telemetry) in (bl.NONKEY, bl.UNCLASSIFIED):")], {"AH14"}),
    ("H82 grade() admits EXCLUDED runs", "ca",
     [('    runs = [r for r in runs if usable(r) and r["arm"] in (a, b)]',
       '    runs = [r for r in runs if not r["refused"] and r["arm"] in (a, b)]')], {"AH13"}),
    ("H13 the rng re-seeded per stratum (every stratum draws the same stream)", "ca",
     [("            wt = rng.multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)",
       "            wt = np.random.default_rng(14).multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)")],
     {"AH10", "AH11"}),
    ("H83 the bootstrap capped at 1,000 draws", "ca",
     [("    bs = statistics(resample_sums(strata, draws, np.random.default_rng(seed)), species, a, b)",
       "    bs = statistics(resample_sums(strata, min(draws, 1000), np.random.default_rng(seed)), species, a, b)")],
     {"AH11"}),
    ("H84 --seed ignored", "ca",
     [("    bs = statistics(resample_sums(strata, draws, np.random.default_rng(seed)), species, a, b)",
       "    bs = statistics(resample_sums(strata, draws, np.random.default_rng(DEFAULT_SEED)), species, a, b)")],
     {"AH11"}),
    ("H06 REACH species-weighted (not a pooled ratio of sums)", "ca",
     [('    rn = {arm: sum(g(arm, sp, "RN") for sp in species) for arm in (a, b)}\n'
       '    rd = {arm: sum(g(arm, sp, "RD") for sp in species) for arm in (a, b)}\n'
       '    out["reach_a"], out["reach_b"] = _ratio(rn[a], rd[a]), _ratio(rn[b], rd[b])\n',
       '    rr = {arm: np.stack([_ratio(g(arm, sp, "RN"), g(arm, sp, "RD")) for sp in species]) for arm in (a, b)}\n'
       '    out["reach_a"], out["reach_b"] = np.nanmean(rr[a], axis=0), np.nanmean(rr[b], axis=0)\n')], {"AH7"}),
    ("H27 rule_not_lower := (reading == 'NOT LOWER')", "ca",
     [('"rule_not_lower": bool(lo95 > -delta),', '"rule_not_lower": reading == "NOT LOWER",')], {"AH16"}),
    ("H28 rule_not_lower read on the 90% CI", "ca",
     [('"rule_not_lower": bool(lo95 > -delta),', '"rule_not_lower": bool(nz(c2["ci90"][0]) > -delta),')], {"AH16"}),
    ("H29 rule_not_lower with δ hard-coded .08", "ca",
     [('"rule_not_lower": bool(lo95 > -delta),', '"rule_not_lower": bool(lo95 > -0.08),')], {"AH16"}),
    ("H81 GROUPS: Roxanne and the Route 110 rival swapped", "ca",
     [('    "leaders": ("ROXANNE", "BRAWLY", "WATTSON", "FLANNERY"),\n    "rivals": ("RIVAL_ROUTE_110",),',
       '    "leaders": ("RIVAL_ROUTE_110", "BRAWLY", "WATTSON", "FLANNERY"),\n    "rivals": ("ROXANNE",),')], {"AH15"}),
    ("H11 STRATA arm x species x LANE", "ca",
     [('            c = {**{f: [0.0] * K for f in FIELDS_K}, **{f: 0.0 for f in FIELDS_1}}',
       '            c = {**{f: [0.0] * K for f in FIELDS_K}, **{f: 0.0 for f in FIELDS_1}, "lane": r["lane"]}'),
      ('        out[skey] = {"keys": list(stratum), "C": len(cl),',
       '        out[skey] = {"keys": list(stratum), "C": len(cl), "lanes": [c["lane"] for c in cl],'),
      ("            wt = rng.multinomial(C, np.full(C, 1.0 / C), size=draws).astype(float)\n",
       "            wt = np.zeros((draws, C))\n"
       "            for ln in sorted(set(st['lanes']), key=str):\n"
       "                idx = [i for i, x in enumerate(st['lanes']) if x == ln]\n"
       "                wt[:, idx] = rng.multinomial(len(idx), np.full(len(idx), 1.0 / len(idx)), size=draws)\n")],
     {"AH9"}),
    # ---- the coordinator's DECISIONS, each REVERTED (one mutant per rule; a rule with several clauses has several)
    ("D01 F1 a VOID never reaches the status", "ca",
     [('    if void:\n        batch_reasons.append(("VOID"', '    if False:\n        batch_reasons.append(("VOID"')], {"DV2", "DV3"}),
    ("D02 F1 a user park VOIDS", "ca", [("    if abort == USER_PARK:\n        return None\n", "")], {"DV1", "DV3"}),
    ("D03 F1 the batch's verdict is never read (main passes no void)", "ca",
     [("    void = void_reason(summ, args.void)", "    void = None")], {"DV3"}),
    ("D04 F1 a LIVE read without summary.json is not PROVISIONAL", "ca",
     [("provisional=summ is None", "provisional=False")], {"DV3"}),
    ("D05 F1 the automated STOPs not recognised", "ca",
     [('    if abort in AUTOMATED_STOPS or abort.startswith("x4h error"):\n        return f"STOP {abort}"',
       '    if False:\n        return f"STOP {abort}"')], {"DV1", "DV3"}),
    ("D06 F2 θ over the ESTIMABLE subset of K* (the pre-fold rule)", "ca",
     [('    out["theta_a"], out["theta_b"] = px[a].mean(axis=1), px[b].mean(axis=1)',
       '    out["theta_a"], out["theta_b"] = _nanmean(px[a]), _nanmean(px[b])')], {"CS3", "DV4"}),
    ("D07 F2 the rule word ignores the frozen K*", "ca",
     [("    reading = (c2_reading(lo95, hi95, delta) if n_est == len(KEYS)",
       "    reading = (c2_reading(lo95, hi95, delta) if True")], {"CS3", "DV4"}),
    ("D08 F2 the status ignores the frozen K*", "ca",
     [('    if n_est < len(KEYS):\n        c2_reasons.append(("NOT ESTIMABLE", reading))',
       '    if False:\n        c2_reasons.append(("NOT ESTIMABLE", reading))')], {"DV3", "DV4"}),
    ("D09 F2 a group's θ over its estimable subset", "ca",
     [('        out[f"group_{gname}"] = px[b][:, cols].mean(axis=1) - px[a][:, cols].mean(axis=1)',
       '        out[f"group_{gname}"] = _nanmean(px[b][:, cols]) - _nanmean(px[a][:, cols])')], {"DV4"}),
    ("D10 F3 REACH DIFFERS not on the C2 line", "ca",
     [('    reach = f"   ⚠ REACH DIFFERS ({\', \'.join(c2[\'reach_differs\'])})" if c2["reach_differs"] else ""',
       '    reach = ""')], {"DV5"}),
    # D11's set FOUND BY THE RUN (my prediction was {DV5}): `render` reads c2["reach_differs"], so dropping the field
    # crashes every row that renders a report. Kept as found; D11b is the non-crashing form of the same revert.
    ("D11 F3 REACH DIFFERS not in the JSON c2 object (the report then crashes)", "ca",
     [('"n_estimable": n_est, "reach_differs": reach_differs},', '"n_estimable": n_est},')],
     {"CA9", "CX1", "CX2", "DV13", "DV3", "DV4", "DV5", "DV7"}),
    ("D11b F3 the JSON c2 object carries no REACH DIFFERS", "ca",
     [('"n_estimable": n_est, "reach_differs": reach_differs},', '"n_estimable": n_est, "reach_differs": []},')],
     {"DV5"}),
    ("D12 F4 the completeness failures never reach the controls", "ca",
     [("    failures = list(completeness)", "    failures = []")], {"DV6"}),
    ("D13 F4 an interrupted collection accepted", "ca",
     [('        if summary.get("collect_interrupted"):', "        if False:")], {"DV6"}),
    ("D14 F4 debug_logs_collected not compared", "ca",
     [("            if want is not None and n != want:", "            if False:")], {"DV6"}),
    ("D15 F4 a lane with zero logs accepted", "ca",
     [("        if n == 0:\n            out.append(", "        if False:\n            out.append(")], {"DV6"}),
    ("D16 F4 the collection rules applied to a LIVE read too", "ca",
     [('    if not live and summary is not None:\n        if summary.get("collect_interrupted"):',
       '    if summary is not None:\n        if summary.get("collect_interrupted"):')], {"DV6"}),
    ("D17 F5 the undefined-draw count not printed", "ca",
     [('    return f"[{_n(c[0], fmt)}, {_n(c[1], fmt)}]" + (f" ({nan_draws} draws undefined, excluded)" if nan_draws else "")',
       '    return f"[{_n(c[0], fmt)}, {_n(c[1], fmt)}]"')], {"DV4"}),
    ("D18 F6 the exploratory reasons never reach the grade", "ca",
     [("exploratory=exploratory)", "exploratory=[])")], {"DV7"}),
    ("D19 F6 δ not derived from the design (always .08)", "ca",
     [("    delta = args.delta if args.delta is not None else prereg", "    delta = args.delta if args.delta is not None else 0.08")],
     {"DV7"}),
    ("D20 F6 a non-pre-registered seed is not exploratory", "ca",
     [("    if seed != DEFAULT_SEED:", "    if False:")], {"DV7"}),
    ("D21 F7 the C2 verdict is the rule's word whatever the status", "ca",
     [('"verdict": reading if c2_word is None else c2_word,', '"verdict": reading,')],
     {"CA9", "DV2", "DV3", "DV4", "DV7", "DV8"}),
    ("D22 F7 the C1 verdict is the rule's word whatever the status", "ca",
     [('"verdict": c1_rule if c1_word is None else c1_word,', '"verdict": c1_rule,')], {"DV2"}),
    ("D23 F8 any species forms a stratum", "ca", [("    elif species not in STARTERS:", "    elif False:")], {"DV9"}),
    ("D24 F8 the 'choosing' cross-check dropped", "ca", [("    elif chosen != species:", "    elif False:")], {"DV9"}),
    ("D25 F9 cut no-starter runs counted too", "ca",
     [('if r.get("excluded_kind") == "no_starter" and r["status"] == "complete")',
       'if r.get("excluded_kind") == "no_starter")')], {"DV10"}),
    ("D26 F10 a run censored DURING its first attempt stays in the denominators", "ca",
     [("            if censored_during(r, key):\n                continue", "            if False:\n                continue")],
     {"DV11", "AH5"}),
    ("D27 F10 a COMPLETE met-but-undecided run treated as censored too", "ca",
     [('    return run["status"] != "complete" and k["reached"] and k["won"] is None',
       '    return k["reached"] and k["won"] is None')], {"DV11", "AH5"}),
    ("D28 F11 only a CUT headerless log is excluded (a lost one is refused)", "ca",
     [("    if (cut or lost) and not header:", "    if cut and not header:")], {"DV12"}),
    ("D29 RC-3 an undefined C1 reads FAIL", "ca",
     [('    c1_rule = "NOT ESTIMABLE" if c1["point"] is None else "PASS" if c1_pass else "FAIL"',
       '    c1_rule = "PASS" if c1_pass else "FAIL"')], {"DV13"}),
    ("CM1 MENTION ONLY: a comment quoting the one-arm species rule turns NOTHING red", "ca",
     [('#: DESIGN §5 "Per-group" (leaders, rivals, Magma/Aqua), each restricted to K*.',
       '#: DESIGN §5 "Per-group" — never `ok = (na > 0) | (nb > 0)` (leaders, rivals, Magma/Aqua).')], set()),
]


def _apply(src: str, edits) -> str:
    for old, new in edits:
        n = src.count(old)
        if n != 1:
            raise AssertionError(f"mutant anchor found {n} times: {old[:90]!r}")
        src = src.replace(old, new)
    return src


def _install(key: str, source: str, i: int) -> None:
    mod = types.ModuleType(NAMES[key])
    mod.__file__ = str(PATHS[key])
    sys.modules[NAMES[key]] = mod
    exec(compile(source, f"<mutant {i}>", "exec"), mod.__dict__)
    if key == "bl":                      # compare_arms bound `bl` at import: point it at the mutant too
        sys.modules["compare_arms"].bl = mod


def all_rows(verbose: bool, skip=frozenset()) -> set:
    reds = set()
    for rid, label, fn in ROWS:
        if rid in skip:
            continue
        t0 = time.perf_counter()
        try:
            ok, detail = fn()
        except Exception as error:  # noqa: BLE001 - a row that raises is a red row, reported with its error
            ok, detail = False, f"raised {type(error).__name__}: {error}"
        if not ok:
            reds.add(rid)
        if verbose:
            check(f"{rid} {label}", ok, detail + (f"  [{time.perf_counter() - t0:.1f} s]" if rid in HEAVY else ""))
    return reds


def run_mutant(i: int, target: str, edits) -> "tuple[set | None, str]":
    real = {k: sys.modules[v] for k, v in NAMES.items()}
    saved_tmp = dict(TMP)
    try:
        src = _apply(PATHS[target].read_text(encoding="utf-8"), edits)
        _install(target, src, i)
        with tempfile.TemporaryDirectory(prefix="ca-mut-") as tmp:   # fresh fixture dirs per mutant
            TMP.update(build_tree(pathlib.Path(tmp)))
            return all_rows(False, skip=HEAVY), ""
    except Exception as error:  # noqa: BLE001 - a mutant that cannot even run is a failed check, reported
        return None, f"{type(error).__name__}: {error}"
    finally:
        for k, v in NAMES.items():
            sys.modules[v] = real[k]
        real["ca"].bl = real["bl"]
        TMP.clear()
        TMP.update(saved_tmp)


def _pool_job(i: int):
    """One mutant in a worker process (it builds its own fixture tree): (i, its red rows or None, the error)."""
    import warnings
    warnings.simplefilter("ignore", RuntimeWarning)    # a mutant's nanmean of an empty slice: noise, not a result
    _label, target, edits, _want = MUTANTS[i]
    red, err = run_mutant(i, target, edits)
    return i, (sorted(red) if red is not None else None), err


def run_all_mutants(serial: bool) -> list:
    """Every mutant's (red set or None, error), in MUTANTS order. ⭐ A process pool: each mutant re-runs every fast
    row, and 100+ mutants in one process would push the gate past a minute. `--serial` runs them in-process."""
    if serial:
        return [run_mutant(i, t, e) for i, (_l, t, e, _w) in enumerate(MUTANTS)]
    import concurrent.futures
    import os
    out: list = [None] * len(MUTANTS)
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 2)) as pool:
        for i, red, err in pool.map(_pool_job, range(len(MUTANTS)), chunksize=4):
            out[i] = (set(red) if red is not None else None, err)
    return out


def main() -> int:
    global SMOKE
    t0 = time.perf_counter()
    SMOKE = BL().main_story_dev() / "x4-runs" / "20261001-090649"
    with tempfile.TemporaryDirectory(prefix="compare-arms-") as tmp:
        TMP.update(build_tree(pathlib.Path(tmp)))
        print("PROVENANCE — the gate's own data")
        provenance()
        print("\nROWS — the real modules")
        baseline = all_rows(True)
        if "--rows-only" in sys.argv:
            print("\n‼ --rows-only: the MUTANTS were NOT run. THIS IS NOT THE GATE.")
            FAILURES.append("--rows-only (the mutant half was skipped)")
        elif MUTANTS:
            print(f"\nMUTANTS — each must turn EXACTLY its named FAST rows red ({len(MUTANTS)}; a process pool; the "
                  f"heavy rows {sorted(HEAVY)} are not re-run)")
            covered: set = set()
            results = run_all_mutants("--serial" in sys.argv)
            for (label, target, edits, want), (red, err) in zip(MUTANTS, results):
                if red is None:
                    check(label, False, err)
                    continue
                red = set(red) - baseline
                want_now = set(want) - baseline
                covered |= set(want)
                check(label, red == want_now,
                      f"red {sorted(red)}" + ("" if red == want_now else f" (want {sorted(want_now)})"))
            uncovered = sorted(ROW_NAMES - HEAVY - covered)
            check("COVERAGE every fast row is in at least one mutant's expected red set", not uncovered,
                  f"{len(ROW_NAMES - HEAVY)} fast rows; uncovered {uncovered}")
    wall = time.perf_counter() - t0
    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s) in {wall:.1f} s:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"ALL PASS ({len(ROW_NAMES)} rows, {len(MUTANTS)} mutants, {len(QUOTES)} quoted lines) in {wall:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
