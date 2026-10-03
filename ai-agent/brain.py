"""How the learner decides what to try next, and what it has learned so far.

A GENOME is one value for every knob in `knowledge.GENES`. A run's SCORE is its progress (badges + Elite Four +
Champion) out of 13. Each cycle runs several genomes side by side, one lane per starter for each.

Choosing (`choose_arms`) balances keeping what works against trying something new:
1. the INCUMBENT, the genome with the best estimated score, always runs: it is the control the others are compared
   against in the same cycle;
2. a Claude PROPOSAL from the inbox, if one is waiting;
3. a THOMPSON draw: each known genome draws a plausible score from its uncertainty, and the best draw runs. A genome
   with few runs is uncertain, so it gets retried;
4. MUTANTS of the incumbent (one or two knobs changed), preferring combinations never run before.

`gene_effects` estimates what each knob is worth by ridge regression over every run, with the starter as a
covariate. Knobs that have only ever changed together (step 14 changed all of them at once) cannot be told apart, and
the report says so.
"""
from __future__ import annotations

import hashlib
import json
import math
import random

import knowledge as K

BASE = K.STEP14_A


def canonical(genes: dict) -> dict:
    return {g: str(genes.get(g, BASE[g])) for g in K.GENES}


def genome_id(genes: dict) -> str:
    blob = json.dumps(canonical(genes), sort_keys=True).encode()
    return "g" + hashlib.sha1(blob).hexdigest()[:8]


def label(genes: dict) -> str:
    """The knobs that differ from the baseline, e.g. 'R25_CAP+R27_KEYITEMS'; 'baseline' when none do."""
    on = [g.removeprefix("POKEBOT_") for g, v in canonical(genes).items() if v != BASE[g]]
    if len(on) == len(K.GENES):
        return "ALL (step 14 arm B)"
    return "+".join(on) if on else "baseline (step 14 arm A)"


def full_env(genes: dict) -> dict:
    """The arm's complete, literal variable set for `x4_headless.py --arms`."""
    return {**K.FIXED, **canonical(genes)}


def summarize(records: list[dict]) -> dict:
    """genome id -> its stats over USABLE runs (complete, with a known starter)."""
    out: dict = {}
    for r in records:
        gid = genome_id(r["genome"])
        s = out.setdefault(gid, {"genes": canonical(r["genome"]), "label": label(r["genome"]), "scores": [],
                                 "champions": 0, "censored": 0, "starters": {}})
        if not r.get("usable"):
            s["censored"] += 1
            continue
        s["scores"].append(r["score"])
        s["champions"] += int(r["champion"])
        st = s["starters"].setdefault(r["starter"], [])
        st.append(r["score"])
    for s in out.values():
        n = len(s["scores"])
        s["n"] = n
        s["mean"] = sum(s["scores"]) / n if n else None
        s["sd"] = (math.sqrt(sum((x - s["mean"]) ** 2 for x in s["scores"]) / (n - 1)) if n > 1 else None)
        s["starters"] = {k: (len(v), round(sum(v) / len(v), 3)) for k, v in s["starters"].items()}
    return out


def prior_mean(summary: dict) -> float:
    scores = [x for s in summary.values() for x in s["scores"]]
    return sum(scores) / len(scores) if scores else 0.5


def posterior(s: dict, mu0: float, n0: float = 2.0, sd0: float = 0.30) -> tuple[float, float]:
    """(mean, sd) of a genome's expected score: its runs shrunk toward the overall mean by `n0` pseudo-runs."""
    n = s["n"]
    mean = (n0 * mu0 + n * (s["mean"] or 0.0)) / (n0 + n)
    spread = s["sd"] if s["sd"] is not None and n > 2 else sd0
    return mean, spread / math.sqrt(n0 + n)


def mutate(genes: dict, rng: random.Random, flips: int) -> dict:
    g = canonical(genes)
    for name in rng.sample(sorted(K.GENES), flips):
        g[name] = rng.choice([v for v in K.GENES[name][0] if v != g[name]])
    return g


def choose_arms(k: int, summary: dict, proposals: list[dict], rng: random.Random,
                two_flip_prob: float = 0.3, max_proposals: int = 1) -> list[tuple[dict, str]]:
    """k distinct genomes for the next cycle, each with the reason it was picked."""
    mu0 = prior_mean(summary)
    tested = {gid: s for gid, s in summary.items() if s["n"] > 0}
    picks: list[tuple[dict, str]] = []
    seen: set[str] = set()

    def add(genes: dict, why: str) -> bool:
        gid = genome_id(genes)
        if gid in seen or len(picks) >= k:
            return False
        seen.add(gid)
        picks.append((canonical(genes), why))
        return True

    if tested:
        best = max(tested, key=lambda gid: posterior(tested[gid], mu0)[0])
        m, sd = posterior(tested[best], mu0)
        add(tested[best]["genes"], f"incumbent: best estimate {m:.3f} +/- {sd:.3f} over {tested[best]['n']} runs")
    else:
        add(BASE, "baseline: nothing measured yet")
    incumbent = picks[0][0]
    for p in proposals[:max_proposals]:
        add(p["genes"], f"inbox proposal '{p.get('name', '?')}': {p.get('why', '')}"[:200])
    if len(picks) < k and len(tested) > 1:
        draws = {gid: rng.gauss(*posterior(s, mu0)) for gid, s in tested.items() if gid not in seen}
        if draws:
            gid = max(draws, key=draws.get)
            add(tested[gid]["genes"], f"Thompson draw {draws[gid]:.3f} (estimate "
                                      f"{posterior(tested[gid], mu0)[0]:.3f} over {tested[gid]['n']} runs)")
    for _ in range(200):
        if len(picks) >= k:
            break
        flips = 2 if rng.random() < two_flip_prob else 1
        cand = mutate(incumbent, rng, flips)
        novel = genome_id(cand) not in summary
        if novel or _ > 100:
            changed = [g.removeprefix("POKEBOT_") for g in K.GENES if cand[g] != incumbent[g]]
            add(cand, f"mutant of the incumbent: changed {', '.join(changed)}" + ("" if novel else " (retest)"))
    return picks


# ------------------------------------------------------------------------------------------------------- regression
def _solve(a: list[list[float]], b: list[float]) -> tuple[list[float], list[list[float]]]:
    """(x, inverse of a) by Gauss-Jordan with partial pivoting. `a` is small (one row per knob)."""
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        piv = m[c][c]
        if abs(piv) < 1e-12:
            raise ValueError("singular system")
        m[c] = [v / piv for v in m[c]]
        for r in range(n):
            if r != c and m[r][c]:
                f = m[r][c]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[c])]
    return [row[-1] for row in m], [row[n:2 * n] for row in m]


def gene_effects(records: list[dict], ridge: float = 1.0) -> list[dict]:
    """Per knob: the estimated change in score from turning it away from baseline, with a standard error."""
    rows = [r for r in records if r.get("usable")]
    genes = sorted(K.GENES)
    if len(rows) < len(genes) + 5:
        return []
    starters = sorted({r["starter"] for r in rows})[1:]
    names = ["(intercept)"] + genes + [f"starter={s}" for s in starters]
    xs = [[1.0] + [float(canonical(r["genome"])[g] != BASE[g]) for g in genes]
          + [float(r["starter"] == s) for s in starters] for r in rows]
    ys = [r["score"] for r in rows]
    p = len(names)
    xtx = [[sum(x[i] * x[j] for x in xs) + (ridge if i == j and i > 0 else 0.0) for j in range(p)] for i in range(p)]
    xty = [sum(x[i] * y for x, y in zip(xs, ys)) for i in range(p)]
    beta, inv = _solve(xtx, xty)
    resid = [y - sum(b * xi for b, xi in zip(beta, x)) for x, y in zip(xs, ys)]
    s2 = sum(e * e for e in resid) / max(1, len(rows) - p)
    # A knob whose on/off column is IDENTICAL to another knob's over every run cannot be told apart from it: the
    # ridge then just splits their joint effect evenly. Step 14 alone confounds all eleven.
    cols = {g: tuple(x[1 + j] for x in xs) for j, g in enumerate(genes)}
    out = []
    for i, name in enumerate(genes, start=1):
        twins = [g.removeprefix("POKEBOT_") for g in genes if g != name and cols[g] == cols[name]]
        out.append({"gene": name, "effect": round(beta[i], 4), "se": round(math.sqrt(max(0.0, s2 * inv[i][i])), 4),
                    "runs_on": int(sum(cols[name])), "runs_off": len(rows) - int(sum(cols[name])),
                    "confounded_with": twins,
                    "separable": not twins and 0 < sum(cols[name]) < len(rows)})
    return sorted(out, key=lambda e: -abs(e["effect"]))
