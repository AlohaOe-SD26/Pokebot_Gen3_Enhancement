r"""DESIGN v2 STEP 14, T4b — the batch's DESCRIPTIVE tables (DESIGN §5 "Descriptive"). NO VERDICT WORD ANYWHERE.

⛔ THE CAVEAT IS THE HEADLINE: these are COUNTS, per arm, side by side. Nothing here is a test, a margin or a reading:
the confirmatory statistics are `compare_arms.py`'s (T3) and the correctness invariants `batch14_checks.py`'s (T4a).
A difference between the columns is a thing to look at, never a finding by itself. The only fixed phrase is the
spec's "NOT ASSESSED (n)" (the Elite Four, and a boss nobody fought).

THE SPEC (binding): `ai-research-notes/2026-10-01-batch14-T4-PREDICTIONS.md` (T4b); DESIGN §5 "Descriptive". Spec-silent
choices are marked `SPEC-SILENT` beside the code.

INPUT and CONTROLS: `batch14_checks.load` — compare_arms' loader, refusal and completeness; ONE read per log. The tables
read the USABLE runs (compare_arms' `usable`: not refused, not excluded), so a K* row here is computed over exactly
the runs T3 grades; D-funnel CROSS-CHECKS its K* rows against compare_arms' own run records and prints the result.

THE TABLES (per arm):
  D-funnel     runs started -> met X -> beat X on the first try -> beat X eventually, for EVERY key trainer; attempts of
               runs that stopped unbeaten; badges reached; frames to each badge; frame-cap ends; run status (cut / lost /
               capped / complete). KI-119: badges are the run's LEADER WINS (`batch14_checks.LEADER_BADGE`), printed
               with that source and the `[BADGE]` CONTROL — runs poisoned by a boot-loaded save, and un-poisoned runs
               whose `[BADGE]` set differs from the leader wins.
  D-attempt    won / (won + lost) per ATTEMPT, per key group (`battle_log.group_outcome_lines`).
  D-boss       Tate & Liza, Winona, Norman, Juan: first-attempt rates with run counts; the Elite Four NOT ASSESSED (n).
  D-lead       the share of key first attempts whose lead (the first `[TURN]` own species) was caught after the Stone
               Badge, and C2's per-trainer point rates without them (compare_arms' own estimator, no bootstrap).
  D-loss       Lost + Draw: non-key trainer battles / wild catch battles / other wild battles; Victory Road by map.
  D-leg11      runs that loaded EVER GRANDE CITY (16,10) and the money-refusal derails, BOTH texts.
  D-fence      `[DEXFENCE]` reasons as DISTINCT (species, reason) pairs per run, numbers stripped, by era.
  D-economy    `[BALLS-BUY]` (both prefixes) by why and by ball with ₽; `[KIT-BUY]` by why and by item; T1 delta per
               map; money at leg 11.
  D-rare       `[CATCH]` battles and their ends per rare species (B: the line's ` rare=`; A: the offline join).
  D-M1b        `[DMGAUDIT]` blocks pooled over both arms, de-duplicated by content; `--m1b-out FILE` writes them as one
               log `audit_damage_calc.py` reads, and prints its accepted-sample count.
  D-weaken     `[WEAKEN-OBS] would=` by verdict and stage.
  D-throughput frames per run, runs per lane-hour and frames/s (summary.json spawns), log sizes, capped logs.

EXIT: 0 the tables were computed; 1 an instrument control failed (no table); 2 usage.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 batch14_tables.py 20261001-090649 [--m1b-out POOL.log]
Gate: PYTHONUTF8=1 py -3.12 probe_batch14_checks.py
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import statistics as stats
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import batch14_checks as ck  # noqa: E402
import battle_log as bl  # noqa: E402
import compare_arms as ca  # noqa: E402

ARMS = (ck.ARM_A, ck.ARM_B)
#: The words a descriptive table must never print (the gate checks the rendered tables for each).
VERDICT_WORDS = ("PASS", "FAIL", "FINDING", "HIGHER", "LOWER", "INCONCLUSIVE", "REGRESSION", "IMPROVED",
                 "CONFIRMATORY", "VERDICT")
LEAD_LABEL = "conditioned on a post-treatment variable"
FENCE_LABEL = "distinct pairs, not frequency"


def usable_runs(runs, arm) -> list:
    """The runs a table reads: compare_arms' `usable` runs of `arm` that were read (a `t4` record)."""
    return [r for r in runs if ca.usable(r) and r["arm"] == arm and r.get("t4")]


def _med(xs):
    return stats.median(xs) if xs else None


def _n(x, fmt="") -> str:
    return "-" if x is None else format(x, fmt)


def _pct(num, den) -> str:
    return f"{num}/{den}" + (f" ({100.0 * num / den:.0f}%)" if den else "")


def _trainer_order(runs) -> list:
    """Every key trainer any usable run met: the named ones in `TRAINERS` order, then the unnamed ones sorted."""
    seen = {k for r in runs for k in r["t4"]["trainers"]}
    return [k for k in ck.TRAINERS if k in seen] + sorted(seen - set(ck.TRAINERS))


def _won(t) -> "bool | None":
    return None if t is None or t["first"] not in ("won", "lost") else t["first"] == "won"


# ---------------------------------------------------------------------------------------------------- D-funnel
def d_funnel(runs, stdout: dict) -> dict:
    """PURE. Per arm: `started` (usable runs), `status`, `excluded`, `frame_cap`, `badges` (max badge per run ->
    runs), `badge_frames` ({n: [frames]}), and per trainer `met`, `eligible` (compare_arms' reach denominator: a
    complete run, or a censored run that met X and decided it — DECISION F10's `censored_during` is compare_arms'),
    `decided`, `first_won`, `eventually`, `unbeaten_stopped` (COMPLETE runs that met X and never beat it) and their
    `attempts`. `crosscheck`: the K* rows against compare_arms' run records (`[]` = equal). KI-119's [BADGE] CONTROL:
    `badge_poisoned` (runs with [BADGE] lines before their choosing line) and `badge_disagree` (un-poisoned runs whose
    [BADGE] set differs from their leader-win set, each as (log, [BADGE] set, leader-win set))."""
    out = {}
    order = _trainer_order([r for arm in ARMS for r in usable_runs(runs, arm)])
    for arm in ARMS:
        rs = usable_runs(runs, arm)
        rows = {}
        for key in order:
            row = {"met": 0, "eligible": 0, "decided": 0, "first_won": 0, "eventually": 0, "unbeaten_stopped": 0,
                   "attempts": []}
            for r in rs:
                t = r["t4"]["trainers"].get(key)
                won = _won(t)
                pseudo = {"status": r["status"], "keys": {key: {"reached": t is not None, "won": won}}}
                if t is not None:
                    row["met"] += 1
                if ca.censored_during(pseudo, key):
                    pass
                elif t is not None or r["status"] == "complete":
                    row["eligible"] += 1
                if won is not None:
                    row["decided"] += 1
                    row["first_won"] += won
                if t is not None and t["won_ever"]:
                    row["eventually"] += 1
                if t is not None and not t["won_ever"] and r["status"] == "complete":
                    row["unbeaten_stopped"] += 1
                    row["attempts"].append(len(t["attempts"]))
            rows[key] = row
        cross = []
        for key in ca.KEYS:
            mine = rows.get(key, {"met": 0, "decided": 0, "first_won": 0})
            theirs = {"met": sum(r["keys"][key]["reached"] for r in rs),
                      "decided": sum(r["keys"][key]["won"] is not None for r in rs),
                      "first_won": sum(r["keys"][key]["won"] is True for r in rs)}
            if any(mine[f] != theirs[f] for f in theirs):
                cross.append(f"{key}: here {[mine[f] for f in theirs]}, compare_arms {list(theirs.values())}")
        badge_frames: dict = collections.defaultdict(list)
        for r in rs:
            for n, f in r["t4"]["badges"].items():
                badge_frames[n].append(f)
        caps = sum(1 for lane, s in stdout.items() if s["arm"] == arm and s["runs"]
                   for x in s["runs"] if x["bucket"] == "frame_cap")
        # KI-119: the [BADGE] lines are a CONTROL on the leader-win badges
        poisoned = [r for r in rs if r["t4"]["badge_pre_start"]]
        disagree = [r for r in rs if not r["t4"]["badge_pre_start"]
                    and set(r["t4"]["badge_lines"]) != set(r["t4"]["badges"])]
        out[arm] = {"started": len(rs), "rows": rows, "crosscheck": cross,
                    "badge_poisoned": len(poisoned),
                    "badge_disagree": [(pathlib.Path(r["log"]).name, sorted(r["t4"]["badge_lines"]),
                                        sorted(r["t4"]["badges"])) for r in disagree],
                    "status": dict(collections.Counter(r["status"] for r in rs)),
                    "excluded": sum(1 for r in runs if r.get("lane_arm") == arm and r.get("excluded")),
                    "frame_cap": caps,
                    "badges": dict(sorted(collections.Counter(max(r["t4"]["badges"], default=0) for r in rs).items())),
                    "badge_frames": {n: sorted(v) for n, v in sorted(badge_frames.items())}}
    out["order"] = order
    return out


def render_funnel(f: dict) -> list:
    out = ["D-funnel — runs started -> met X -> beat X on the first try -> beat X eventually (per arm, every key "
           "trainer met)"]
    for arm in ARMS:
        a = f[arm]
        out.append(f"  arm {arm}: runs started {a['started']} (usable; {a['excluded']} excluded runs not counted); "
                   f"status {a['status']}; frame-cap ends {a['frame_cap']}")
    out.append(f"  {'trainer':<34}" + "".join(f"{'met/elig ' + arm:>13}{'1st W/dec ' + arm:>14}{'eventually ' + arm:>14}"
                                             f"{'unbeaten ' + arm:>12}" for arm in ARMS))
    for key in f["order"]:
        cells = []
        for arm in ARMS:
            r = f[arm]["rows"][key]
            att = r["attempts"]
            cells.append(f"{str(r['met']) + '/' + str(r['eligible']):>13}{str(r['first_won']) + '/' + str(r['decided']):>14}"
                         f"{r['eventually']:>14}{str(r['unbeaten_stopped']) + (f' (max {max(att)})' if att else ''):>12}")
        out.append(f"  {key:<34}" + "".join(cells))
    out.append("  (elig = compare_arms' reach denominator; 1st W/dec = first attempts won / decided, a Draw a loss; "
               "unbeaten = COMPLETE runs that met X and never beat it, with their most attempts)")
    for arm in ARMS:
        a = f[arm]
        out.append(f"  arm {arm}: badges reached (max per run -> runs) {a['badges']}")
        out.append(f"  arm {arm}: frames to each badge " + ("; ".join(
            f"#{n}: n={len(v)} median {_n(_med(v), ',.0f')} [{v[0]:,}..{v[-1]:,}]" for n, v in a["badge_frames"].items())
            or "none"))
        out.append(f"  arm {arm}: K* rows cross-checked against compare_arms' run records: "
                   + ("equal" if not a["crosscheck"] else "DIFFER — " + "; ".join(a["crosscheck"])))
    out.append("  badge source (KI-119): badge n = the run's first [TRAINER] end res=Won over gym leader n "
               "(opp 265-272) after its 'Story: choosing X!' line; D-lead's catch tag = the [CATCH] end line's own "
               "badges= field")
    out.append("  [BADGE] lines, a CONTROL only — runs with [BADGE] lines before their choosing line (badge telemetry "
               "poisoned by a boot-loaded save): " + "   ".join(f"{arm} {f[arm]['badge_poisoned']}" for arm in ARMS)
               + "; un-poisoned runs whose [BADGE] set differs from the leader-win set: "
               + "   ".join(f"{arm} {len(f[arm]['badge_disagree'])}" for arm in ARMS))
    for arm in ARMS:
        for name, got, wins in f[arm]["badge_disagree"]:
            out.append(f"    arm {arm} {name}: [BADGE] {got} vs leader wins {wins}")
    return out


# ---------------------------------------------------------------------------------------------------- D-attempt
def d_attempt(runs) -> dict:
    """PURE: per arm, per key group, every KEY battle (every attempt): n / won / lost (Draw included) / other."""
    out = {}
    for arm in ARMS:
        g: dict = {}
        for r in usable_runs(runs, arm):
            for rec in r["t4"]["battles"]:
                if rec["cls"] != bl.KEY or rec["group"] is None:
                    continue
                row = g.setdefault(rec["group"], {"n": 0, "won": 0, "lost": 0, "other": 0})
                row["n"] += 1
                row[rec["outcome"]] += 1
        out[arm] = g
    return out


def render_attempt(d: dict) -> list:
    out = ["D-attempt — won / (won + lost) per ATTEMPT, per key group (a summary: looping runs weigh more)"]
    for arm in ARMS:
        out.append(f"  arm {arm}:")
        out += bl.group_outcome_lines(d[arm])
    return out


# ---------------------------------------------------------------------------------------------------- D-boss
def d_boss(runs) -> dict:
    """PURE. SPEC-SILENT: a boss's rate is the POOLED won / decided first attempts (not C2's species weighting: these
    are descriptive, and few runs reach them)."""
    out = {}
    for arm in ARMS:
        rs = usable_runs(runs, arm)
        rows = {}
        for key in ck.BOSSES:
            ts = [r["t4"]["trainers"].get(key) for r in rs]
            won = [_won(t) for t in ts]
            rows[key] = {"met": sum(t is not None for t in ts), "decided": sum(w is not None for w in won),
                         "won": sum(w is True for w in won)}
        e4 = sum(1 for r in rs if any(k in r["t4"]["trainers"] for k in ck.ELITE_FOUR))
        out[arm] = {"rows": rows, "elite_four_runs": e4}
    return out


def render_boss(d: dict) -> list:
    out = ["D-boss — first-attempt rates with run counts (later bosses: DESCRIPTIVE only, DESIGN §5)"]
    for key in ck.BOSSES:
        cells = []
        for arm in ARMS:
            r = d[arm]["rows"][key]
            cells.append(f"{arm} " + (f"{r['won']}/{r['decided']} = {r['won'] / r['decided']:.2f} (met {r['met']})"
                                      if r["decided"] else f"NOT ASSESSED ({r['met']})"))
        out.append(f"  {key:<16}" + "   ".join(cells))
    out.append("  ELITE_FOUR      " + "   ".join(f"{arm} NOT ASSESSED ({d[arm]['elite_four_runs']})" for arm in ARMS))
    return out


# ---------------------------------------------------------------------------------------------------- D-lead
def post_badge_leads(run) -> dict:
    """PURE: key -> True when the run's first attempt at that key trainer was LED by a species the run CAUGHT after
    the Stone Badge (`[CATCH] end … end=caught` with >= 1 badge). SPEC-SILENT: the lead is a SPECIES (the first
    `[TURN]` line's own side, which carries no PID), so an evolved catch is not matched and an earlier catch of the
    same species is; both are documented in the label."""
    caught = {sp for sp, badges in run["t4"]["caught"] if badges >= 1}
    return {k: t["lead"] in caught for k, t in run["t4"]["trainers"].items()
            if t["first_k"] is not None and t["lead"] is not None}


def d_lead(runs, void: "str | None" = None) -> dict:
    """PURE (numpy). `void` (compare_arms' `void_reason`, RULING 8) marks the C2 rates printed here as VOID."""
    out = {"share": {}, "void": void}
    excluded = {}
    for arm in ARMS:
        num = den = 0
        for r in usable_runs(runs, arm):
            pl = post_badge_leads(r)
            den += sum(1 for t in r["t4"]["trainers"].values() if t["first_k"] is not None)
            num += sum(pl.values())
            excluded[r["log"]] = {k for k, v in pl.items() if v}
        out["share"][arm] = (num, den)
    base = [r for arm in ARMS for r in usable_runs(runs, arm)]
    out["rates"] = None
    if ca.np is not None and {r["arm"] for r in base} >= set(ARMS):
        mod = []
        for r in base:
            keys = {k: (dict(v, won=None, attempted=False) if k in excluded.get(r["log"], set()) else v)
                    for k, v in r["keys"].items()}
            mod.append(dict(r, keys=keys))
        species = sorted({r["species"] for r in base})

        def point(rs):
            st = ca.statistics(ca.resample_sums(ca.build_strata(rs), 0, None), species)
            return {k: (st["pX_a"][0, j], st["pX_b"][0, j]) for j, k in enumerate(ca.KEYS)}

        out["rates"] = {"all": point(base), "without": point(mod),
                        "dropped": {k: {arm: sum(1 for r in base if r["arm"] == arm and k in excluded.get(r["log"], ()))
                                        for arm in ARMS} for k in ca.KEYS}}
    return out


def render_lead(d: dict) -> list:
    out = [f"D-lead (K3) — ⚠ {LEAD_LABEL} (OPENFENCE causes it; biased toward B, DESIGN §5); species-level: "
           f"evolved catches are missed"]
    out.append("  key first attempts led by a species caught after the Stone Badge: "
               + "   ".join(f"{arm} {_pct(*d['share'][arm])}" for arm in ARMS))
    out.append("  (a species match: the [TURN] line has no PID — evolved catches are missed, and an earlier catch of "
               "the same species counts)")
    if d["rates"] is None:
        out.append("  C2's per-trainer rates: not computed (numpy missing, or an arm has no usable run)")
        return out
    if d.get("void"):
        out.append(f"  ⛔ C1-C2 VOID: {d['void']} (DESIGN §4) — the C2 rates below are VOID: descriptive only")
    out.append("  C2's per-trainer point rates (compare_arms' estimator: species-weighted, no bootstrap), all first "
               "attempts vs without those" + (" [VOID]" if d.get("void") else "") + ":")
    out.append(f"  {'trainer':<20}{'p A':>8}{'p B':>8}{'p A w/o':>10}{'p B w/o':>10}{'dropped A/B':>13}")
    for k in ca.KEYS:
        (aa, bb), (aw, bw) = d["rates"]["all"][k], d["rates"]["without"][k]
        dr = d["rates"]["dropped"][k]
        out.append(f"  {k:<20}{_f3(aa):>8}{_f3(bb):>8}{_f3(aw):>10}{_f3(bw):>10}"
                   f"{str(dr[ck.ARM_A]) + '/' + str(dr[ck.ARM_B]):>13}")
    return out


def _f3(x) -> str:
    x = float(x)
    return "n/a" if x != x else f"{x:.3f}"


# ---------------------------------------------------------------------------------------------------- D-loss
def d_loss(runs) -> dict:
    """PURE. Lost + Draw (`outcome_bucket` 'lost') per battle class; a WILD battle with a `[CATCH]` line is a catch
    battle. Victory Road battles by the map the battle STARTED on."""
    out = {}
    for arm in ARMS:
        rows = {name: {"n": 0, "lost": 0} for name in ("non-key trainer", "wild catch", "other wild", "key trainer",
                                                         "unclassified")}
        catch_lost_lines = 0
        vr: dict = {}
        for r in usable_runs(runs, arm):
            for rec in r["t4"]["battles"]:
                if rec["cls"] == bl.NONKEY:
                    name = "non-key trainer"
                elif rec["cls"] == bl.WILD:
                    name = "wild catch" if rec["catch"] else "other wild"
                    catch_lost_lines += len(rec["catch_lost"])
                elif rec["cls"] == bl.KEY:
                    name = "key trainer"
                else:
                    name = "unclassified"
                lost = rec["outcome"] == "lost"
                rows[name]["n"] += 1
                rows[name]["lost"] += lost
                if rec["map"] in ck.VICTORY_ROAD:
                    v = vr.setdefault(ck.VICTORY_ROAD[rec["map"]], {"n": 0, "lost": 0, "classes": collections.Counter()})
                    v["n"] += 1
                    v["lost"] += lost
                    v["classes"][rec["cls"]] += 1
        out[arm] = {"rows": rows, "catch_end_lost": catch_lost_lines, "victory_road": vr}
    return out


def render_loss(d: dict) -> list:
    out = ["D-loss — Lost + Draw per battle, split three ways (and the two other classes, for completeness)"]
    for name in ("non-key trainer", "wild catch", "other wild", "key trainer", "unclassified"):
        out.append(f"  {name:<18}" + "   ".join(f"{arm} {d[arm]['rows'][name]['lost']}/{d[arm]['rows'][name]['n']}"
                                                for arm in ARMS))
    out.append("  wild catch battles' `[CATCH] end … end=lost` lines: "
               + "   ".join(f"{arm} {d[arm]['catch_end_lost']}" for arm in ARMS))
    for arm in ARMS:
        vr = d[arm]["victory_road"]
        out.append(f"  Victory Road, arm {arm}: " + ("; ".join(
            f"{m} lost {v['lost']}/{v['n']} {dict(v['classes'])}" for m, v in sorted(vr.items())) or "no battle"))
    return out


# ---------------------------------------------------------------------------------------------------- D-leg11
def d_leg11(runs) -> dict:
    out = {}
    for arm in ARMS:
        rs = usable_runs(runs, arm)
        loaded = [r for r in rs if r["t4"]["leg11_loaded"]]
        refused = [r for r in rs if r["t4"]["leg11_old"] or r["t4"]["leg11_new"]]
        out[arm] = {"loaded": len(loaded), "refused_runs": len(refused),
                    "refused_loaded": sum(1 for r in refused if r["t4"]["leg11_loaded"]),
                    "old_lines": sum(len(r["t4"]["leg11_old"]) for r in rs),
                    "new_lines": sum(len(r["t4"]["leg11_new"]) for r in rs)}
    return out


def render_leg11(d: dict) -> list:
    out = ["D-leg11 — runs that loaded EVER GRANDE CITY (16,10), and money-refusal derails (both texts)"]
    for arm in ARMS:
        a = d[arm]
        out.append(f"  arm {arm}: loaded (16,10) {a['loaded']}; runs with a refusal derail {a['refused_runs']} (of "
                   f"them loaded (16,10) {a['refused_loaded']}); derail lines: old 'the basket costs ₽' "
                   f"{a['old_lines']}, current 'the missing basket lines … short by' {a['new_lines']}")
    return out


# ---------------------------------------------------------------------------------------------------- D-fence
def d_fence(runs) -> dict:
    out = {}
    for arm in ARMS:
        by = {"before": collections.Counter(), "after": collections.Counter()}
        total = {"before": 0, "after": 0}
        unparsed = 0
        for r in usable_runs(runs, arm):
            unparsed += r["t4"]["fence_unparsed"]
            for era, verb, _species, reason in r["t4"]["fence"]:
                by[era][f"{verb}: {reason}"] += 1
                total[era] += 1
        out[arm] = {"by": by, "total": total, "unparsed": unparsed}
    return out


def render_fence(d: dict) -> list:
    out = [f"D-fence — [DEXFENCE] reasons as DISTINCT (species, reason) pairs per run, numbers stripped — "
           f"{FENCE_LABEL}"]
    for era in ("before", "after"):
        out.append(f"  era: {era} Sootopolis (the first load of SOOTOPOLIS CITY (0,7))   distinct pairs: "
                   + "   ".join(f"{arm} {d[arm]['total'][era]}" for arm in ARMS))
        reasons = sorted(set(d[ck.ARM_A]["by"][era]) | set(d[ck.ARM_B]["by"][era]),
                         key=lambda x: (-(d[ck.ARM_A]["by"][era][x] + d[ck.ARM_B]["by"][era][x]), x))
        for reason in reasons:
            out.append(f"    {d[ck.ARM_A]['by'][era][reason]:>5} {d[ck.ARM_B]['by'][era][reason]:>5}  {reason[:150]}")
    out.append("    (columns: A, B)   unparsed [DEXFENCE] lines: " + "   ".join(f"{arm} {d[arm]['unparsed']}" for arm in ARMS))
    return out


# ---------------------------------------------------------------------------------------------------- D-economy
def d_economy(runs) -> dict:
    """PURE. RULING 4 (the recompute's F1): ONE errand that buys balls AND kit logs a ball line and a kit line with
    the SAME frame and the SAME `money=a->b` (`stock_topoff.py:661-668`), so a per-line sum counts its money twice.
    The PACKAGE row (DESIGN §5's joint ball+kit budget) is therefore de-duplicated per errand — key (log, frame,
    money a->b) over the top-off and kit lines. The per-why / per-ball rows keep the LINE's money and are labelled
    "errand money, joint errands counted in both" (no line carries a unit price); per item, the bought COUNT."""
    out = {}
    for arm in ARMS:
        balls: dict = {}
        by_ball: dict = {}
        kit: dict = {}
        items = collections.Counter()
        t1: dict = {}
        money = []
        errands: dict = {}
        for r in usable_runs(runs, arm):
            t4 = r["t4"]
            for x in t4["balls_buy"]:
                row = balls.setdefault(x["why"], {"lines": 0, "bought": 0, "spent": 0, "spent_unknown": 0})
                row["lines"] += 1
                row["bought"] += x["bought"]
                if x["spent"] is None:
                    row["spent_unknown"] += 1
                else:
                    row["spent"] += x["spent"]
                if x["why"].startswith("topoff"):
                    b = by_ball.setdefault(x["ball"], {"bought": 0, "spent": 0})
                    b["bought"] += x["bought"]
                    b["spent"] += x["spent"] or 0
                    e = errands.setdefault((r["log"], x["frame"], x["money"]), {"kinds": set(), "spent": x["spent"]})
                    e["kinds"].add("ball")
            for x in t4["kit_buy"]:
                row = kit.setdefault(x["why"], {"lines": 0, "spent": 0, "spent_unknown": 0})
                row["lines"] += 1
                if x["spent"] is None:
                    row["spent_unknown"] += 1
                else:
                    row["spent"] += x["spent"]
                items.update(x["items"])
                if x["why"].startswith("kit"):
                    e = errands.setdefault((r["log"], x["frame"], x["money"]), {"kinds": set(), "spent": x["spent"]})
                    e["kinds"].add("kit")
            for rec in t4["battles"]:
                for delta, m in rec["t_ends"]:
                    row = t1.setdefault(m or "?", {"n": 0, "delta": 0})
                    row["n"] += 1
                    row["delta"] += delta or 0
            if t4["leg11_loaded"] and t4["leg11_money"] is not None:
                money.append(t4["leg11_money"])
        paying = [e for e in errands.values() if e["spent"]]
        package = {"spent": sum(e["spent"] for e in paying), "errands": len(paying),
                   "joint": sum(1 for e in paying if e["kinds"] == {"ball", "kit"}),
                   "unreadable": sum(1 for e in errands.values() if e["spent"] is None)}
        out[arm] = {"balls": balls, "by_ball": by_ball, "kit": kit, "items": dict(items), "t1": t1,
                    "money_leg11": sorted(money), "package": package}
    return out


def _map_key(m: str):
    try:
        g, n = m.split(",")
        return (0, int(g), int(n))
    except ValueError:
        return (1, 0, 0)


def render_economy(d: dict) -> list:
    out = ["D-economy — [BALLS-BUY] (both prefixes), [KIT-BUY], T1 money per map, money at leg 11"]
    joint = "errand money, joint errands counted in both"
    for arm in ARMS:
        a = d[arm]
        p = a["package"]
        out.append(f"  arm {arm} PACKAGE (top-off + kit errands, de-duplicated per errand: the joint ball+kit budget): "
                   f"₽{p['spent']:,} over {p['errands']} paying errand(s), {p['joint']} of them joint ball+kit"
                   + (f"; {p['unreadable']} errand(s) with unreadable money" if p["unreadable"] else ""))
        out.append(f"  arm {arm} [BALLS-BUY] by why ({joint}): " + ("; ".join(
            f"{w} lines {v['lines']} bought {v['bought']} ₽{v['spent']:,}"
            + (f" (+{v['spent_unknown']} unreadable)" if v["spent_unknown"] else "") for w, v in sorted(a["balls"].items()))
            or "none"))
        out.append(f"  arm {arm} why=topoff… by ball: " + ("; ".join(
            f"{b} bought {v['bought']} ({joint}: ₽{v['spent']:,})" for b, v in sorted(a["by_ball"].items())) or "none"))
        out.append(f"  arm {arm} [KIT-BUY] by why ({joint}): " + ("; ".join(
            f"{w} lines {v['lines']} ₽{v['spent']:,}" + (f" (+{v['spent_unknown']} unreadable)" if v["spent_unknown"] else "")
            for w, v in sorted(a["kit"].items())) or "none") + f"; items bought (counts) {a['items'] or 'none'}")
        m = a["money_leg11"]
        out.append(f"  arm {arm} money at leg 11 (the last reading before the first (16,10) load): n={len(m)}"
                   + (f" median ₽{_med(m):,.0f} [₽{m[0]:,}..₽{m[-1]:,}]" if m else ""))
    maps = sorted(set(d[ck.ARM_A]["t1"]) | set(d[ck.ARM_B]["t1"]), key=_map_key)
    out.append(f"  T1 [TRAINER] end delta per map: {'map':<8}" + "".join(f"{'battles ' + arm:>11}{'₽ ' + arm:>11}"
                                                                         for arm in ARMS))
    for m in maps:
        out.append(f"  {'':<31}{m:<8}" + "".join(
            f"{d[arm]['t1'].get(m, {}).get('n', 0):>11}{d[arm]['t1'].get(m, {}).get('delta', 0):>11,}" for arm in ARMS))
    return out


# ---------------------------------------------------------------------------------------------------- D-rare
def _offline_rare(dex) -> bool:
    """A's join (no ` rare=` suffix in A): the SPECIES-level verdict of `sandbox-pokebot/modules/rarity.py` (gender
    unknown, so the ULTRA `variant` reason cannot be seen — recon §B E10)."""
    from modules import rarity

    return dex is not None and rarity.classify(rarity._table().get(dex), gender=None).rare


def d_rare(runs) -> dict:
    """PURE. `species`: BOTH arms under ONE rule — the offline species-level join (RULING 9: the comparable column
    pair; it cannot see the gender-decided `variant`). `line`: arm B by its own line's ` rare=` (variant included;
    arm A prints no suffix, so it has no such column)."""
    out = {"species": {}, "line": {}}
    for arm in ARMS:
        rows: dict = {}
        line_rows: dict = {}
        for r in usable_runs(runs, arm):
            for sp, dex, rare, _k, end in r["t4"]["rare"]:
                for table, is_rare in ((rows, _offline_rare(dex)),
                                       (line_rows, arm == ck.ARM_B and rare not in (None, "-"))):
                    if not is_rare:
                        continue
                    row = table.setdefault(f"{sp}#{dex}", {"battles": 0, "ends": collections.Counter(),
                                                           "rare": collections.Counter()})
                    row["battles"] += 1
                    row["ends"][end] += 1
                    row["rare"][rare or "offline"] += 1
        out["species"][arm] = rows
        if arm == ck.ARM_B:
            out["line"][arm] = line_rows
    return out


def render_rare(d: dict) -> list:
    out = ["D-rare — [CATCH] battles and their ends per rare species",
           "  both arms under ONE rule (the offline species-level join; `variant` is not visible to it):"]
    sp_rows = d["species"]
    for sp in sorted(set(sp_rows[ck.ARM_A]) | set(sp_rows[ck.ARM_B])):
        out.append(f"    {sp:<20}" + "   ".join(
            f"{arm} battles {sp_rows[arm].get(sp, {}).get('battles', 0):>3} ends "
            f"{dict(sp_rows[arm].get(sp, {}).get('ends', {}))}" for arm in ARMS))
    if not (sp_rows[ck.ARM_A] or sp_rows[ck.ARM_B]):
        out.append("    none")
    rows = d["line"].get(ck.ARM_B, {})
    out.append(f"  arm B by its own line's ` rare=` (variant included; A prints no suffix): "
               f"{sum(v['battles'] for v in rows.values())} catch battle(s) over {len(rows)} species")
    for sp, v in sorted(rows.items()):
        out.append(f"    {sp:<20} battles {v['battles']:>3}  ends {dict(v['ends'])}  rare {dict(v['rare'])}")
    return out


# ---------------------------------------------------------------------------------------------------- D-M1b, D-weaken
def render_m1b(pool: "ck.M1bPool", out_path, accepted) -> list:
    out = ["D-M1b — [DMGAUDIT] blocks (CTL to CTL) pooled over BOTH arms, de-duplicated by content (frames stripped)",
           f"  lines read {pool.lines}; blocks {pool.blocks}; unique blocks {pool.unique} ({pool.unique_lines} lines); "
           f"BEFORE records in the unique blocks (candidate samples) {pool.befores}"]
    if out_path:
        out.append(f"  written: {pathlib.Path(out_path).absolute()}  (audit_damage_calc.py reads it as one log); its "
                   f"accepted samples: {accepted}")
    else:
        out.append("  not written (give --m1b-out FILE to write the pool and count audit_damage_calc's samples)")
    return out


def d_weaken(runs) -> dict:
    return {arm: dict(sum((r["t4"]["weaken"] for r in usable_runs(runs, arm)), collections.Counter()))
            for arm in ARMS}


def render_weaken(d: dict) -> list:
    out = ["D-weaken — [WEAKEN-OBS] would= by verdict and stage (stage1/stage2 from the reason; '-' = no stage)"]
    keys = sorted(set(d[ck.ARM_A]) | set(d[ck.ARM_B]))
    for k in keys:
        out.append(f"  would={k[0]:<8} stage {k[1]:<7}" + "   ".join(f"{arm} {d[arm].get(k, 0)}" for arm in ARMS))
    if not keys:
        out.append("  no [WEAKEN-OBS] line")
    return out


# ---------------------------------------------------------------------------------------------------- D-throughput
def d_throughput(runs, summary, lanes) -> dict:
    """PURE but for the log sizes (`os.path.getsize`). SPEC-SILENT: a run's frames are its log's last `f<frame>` (the
    same source for complete, cut and lost runs); lane-hours are the arm's spawns' (end - start) from summary.json
    (none for a LIVE read); runs per lane-hour = COMPLETE runs / lane-hours."""
    out = {}
    for arm in ARMS:
        rs = usable_runs(runs, arm)
        allr = [r for r in runs if r.get("lane_arm") == arm and r.get("t4")]
        secs = None
        if summary is not None:
            secs = 0.0
            for ln in lanes:
                if ln.get("arm") != arm:
                    continue
                for sp in ((summary.get("lanes") or {}).get(ln["tag"]) or {}).get("spawns") or []:
                    if sp.get("start") is not None and sp.get("end") is not None:
                        secs += sp["end"] - sp["start"]
        sizes = []
        for r in allr:
            try:
                sizes.append(os.path.getsize(r["log"]))
            except OSError:
                pass
        complete = [r["t4"]["frames"] for r in rs if r["status"] == "complete"]
        frames_all = sum(r["t4"]["frames"] for r in allr)
        out[arm] = {"runs": len(rs), "complete": len(complete), "frames_complete": sorted(complete),
                    "frames_other": sorted(r["t4"]["frames"] for r in rs if r["status"] != "complete"),
                    "lane_hours": None if secs is None else secs / 3600.0, "frames_all": frames_all,
                    "fps": (frames_all / secs) if secs else None,
                    "runs_per_lane_hour": (len(complete) / (secs / 3600.0)) if secs else None,
                    "sizes": sorted(sizes), "capped": [pathlib.Path(r["log"]).name for r in allr if r.get("capped")]}
    return out


def render_throughput(d: dict) -> list:
    out = ["D-throughput — frames per run (a log's last frame), lane-hours from summary.json spawns, log sizes"]
    for arm in ARMS:
        a = d[arm]
        fc, fo, sz = a["frames_complete"], a["frames_other"], a["sizes"]
        out.append(f"  arm {arm}: runs {a['runs']} (complete {a['complete']}); frames per complete run "
                   + (f"median {_med(fc):,.0f} [{fc[0]:,}..{fc[-1]:,}]" if fc else "-")
                   + "; cut / lost / capped runs " + (f"median {_med(fo):,.0f} [{fo[0]:,}..{fo[-1]:,}]" if fo else "-"))
        out.append(f"  arm {arm}: lane-hours {_n(a['lane_hours'], '.2f')}; complete runs per lane-hour "
                   f"{_n(a['runs_per_lane_hour'], '.3f')}; frames/s per lane {_n(a['fps'], ',.0f')} (all logs' frames "
                   f"{a['frames_all']:,})")
        out.append(f"  arm {arm}: log sizes " + (f"n={len(sz)} median {_med(sz) / 1e6:.2f} MB [{sz[0] / 1e6:.2f}.."
                                                 f"{sz[-1] / 1e6:.2f}] total {sum(sz) / 1e6:.1f} MB" if sz else "-")
                   + f"; capped logs {a['capped'] or 'none'}")
    return out


# ---------------------------------------------------------------------------------------------------- all
def all_tables(b: dict, pool=None, out_path=None, accepted=None) -> "tuple[dict, list]":
    runs = b["runs"]
    data = {"D-funnel": d_funnel(runs, b["stdout"]), "D-attempt": d_attempt(runs), "D-boss": d_boss(runs),
            "D-lead": d_lead(runs, b.get("void")), "D-loss": d_loss(runs), "D-leg11": d_leg11(runs), "D-fence": d_fence(runs),
            "D-economy": d_economy(runs), "D-rare": d_rare(runs), "D-weaken": d_weaken(runs),
            "D-throughput": d_throughput(runs, b["summary"], b["manifest"]["lanes"])}
    lines = []
    for name, fn in (("D-funnel", render_funnel), ("D-attempt", render_attempt), ("D-boss", render_boss),
                     ("D-lead", render_lead), ("D-loss", render_loss), ("D-leg11", render_leg11),
                     ("D-fence", render_fence), ("D-economy", render_economy), ("D-rare", render_rare)):
        lines += fn(data[name]) + [""]
    if pool is not None:
        lines += render_m1b(pool, out_path, accepted) + [""]
        data["D-M1b"] = {"lines": pool.lines, "blocks": pool.blocks, "unique": pool.unique,
                         "unique_lines": pool.unique_lines, "befores": pool.befores, "accepted": accepted}
    lines += render_weaken(data["D-weaken"]) + [""] + render_throughput(data["D-throughput"])
    return data, lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="design v2 step 14 T4b: the batch's descriptive tables (DESIGN §5).")
    ap.add_argument("batch", nargs="?", help="x4-runs/<stamp> under the MAIN checkout, or a batch directory path")
    ap.add_argument("--tag", help="LIVE: read a RUNNING batch's lane profiles (endless-<tag>-H*)")
    ap.add_argument("--m1b-out", metavar="FILE", help="write the pooled, de-duplicated [DMGAUDIT] blocks to FILE")
    ap.add_argument("--void", metavar="REASON", help="a manual STOP (a STOP-3 park): C1-C2 VOID in the header and on "
                                                     "D-lead's C2 rates, as compare_arms --void")
    ap.add_argument("--json", metavar="OUT", help="also write the tables as JSON")
    args = ap.parse_args(argv)
    if not args.batch and not args.tag:
        ap.error("give a batch (a stamp or a directory) or --tag")
    handle = open(args.m1b_out, "w", encoding="utf-8", newline="\n") if args.m1b_out else None
    pool = ck.M1bPool(handle)
    try:
        b = ck.load(args.batch, args.tag, ap, m1b=pool, manual_void=args.void)
    finally:
        if handle is not None:
            handle.close()
    head = ["=" * 100, "DESIGN v2 STEP 14 — batch14_tables (T4b): the DESCRIPTIVE tables, per arm (counts; no "
            "reading)", "=" * 100] + ck.header_lines(b) + [""] + ck.control_lines(b, "TABLE", "not in any table")
    if b["failures"]:
        print("\n".join(head + ["=" * 100]))
        return 1
    accepted = None
    if args.m1b_out:
        import audit_damage_calc as adc

        rep = adc.audit_text(pathlib.Path(args.m1b_out).read_text(encoding="utf-8", errors="replace"))
        accepted = len(rep.hits)
    data, lines = all_tables(b, pool, args.m1b_out, accepted)
    print("\n".join(head + [""] + lines + ["=" * 100]))
    if args.json:
        # compare_arms' `_jsonable` (str keys: D-weaken's are (verdict, stage) tuples); sets etc. via `default=str`
        pathlib.Path(args.json).write_text(json.dumps(ca._jsonable(data), indent=2, default=str), encoding="utf-8")
        print(f"JSON written: {pathlib.Path(args.json).absolute()}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
