"""The learner's written findings: `findings/LATEST.md` for people and Claude, `findings/latest.json` for code.

The report is the learner's half of the conversation with Claude. It must be readable cold, with no chat context, so
every number says what it counts and every hint says where it came from.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
from pathlib import Path

import brain
import knowledge as K
import scoring


def _pct(a: int, b: int) -> str:
    return f"{a}/{b} ({100 * a / b:.0f}%)" if b else "0/0"


#: What each learner objective ranks by, in words.
OBJECTIVE_WORDS = {
    "score": "PROGRESS only (out of 13)",
    "human_score": "the provisional BALANCED human score: half progress out of 13, half Pokedex owned out of 202 "
                   "(USER RULINGS 32/33: the more caught the better; a placeholder for one personality)",
}


def build(records: list[dict], cycles: list[dict], status: str, key: str = "score") -> tuple[str, dict]:
    summary = brain.summarize(records, key)
    mu0 = brain.prior_mean(summary)
    usable = [r for r in records if r.get("usable")]
    effects = brain.gene_effects(records, key=key)
    now = dt.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    lines = [
        "# Emerald AI strategy learner: findings",
        "",
        f"Generated {now}. Status: **{status}**.",
        f"Runs: {len(records)} logged, {len(usable)} complete and scored, "
        f"{len(records) - len(usable)} cut off by a batch's time limit (not scored). "
        f"Cycles run by the learner: {sum(1 for c in cycles if c.get('source') == 'cycle')}.",
        f"Champions: {_pct(sum(r['champion'] for r in usable), len(usable))} of scored runs.",
        "",
        "**THE GOAL IS HUMAN-LIKE PLAY** (the user, 2026-10-03): follow the story, catch Pokemon along the way, pick "
        "up items, explore, train sensibly, work on the Pokedex. Never a speedrun. A run's SCORE below counts only "
        "PROGRESS (out of 13: eight badges, four Elite Four members, the Champion). Read it together with the "
        "human-like columns, and never prefer a strategy that wins by playing less like a person. How the two "
        "combine into one ranking is the user's call (`#28-aiagent-v2`).",
        "",
        "## Strategies ranked (best estimate first)",
        "",
        f"**Ranked by:** {OBJECTIVE_WORDS.get(key, key)}. The 'mean score' and 'estimate' columns use it; so do the "
        f"knob effects below.",
        "",
        "| genome | knobs changed from baseline | runs | mean score | estimate +/- sd | champions | species caught "
        "/ run | Pokedex owned / run | places explored / run | by starter (n, mean) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    ranked = sorted((s for s in summary.values() if s["n"]), key=lambda s: -brain.posterior(s, mu0)[0])
    organic = _organic(usable)
    for s in ranked[:15]:
        m, sd = brain.posterior(s, mu0)
        o = organic.get(brain.genome_id(s["genes"]), {})
        lines.append(f"| `{brain.genome_id(s['genes'])}` | {s['label']} | {s['n']} | {s['mean']:.3f} | "
                     f"{m:.3f} +/- {sd:.3f} | {s['champions']} | {_avg(o.get('species'))} | {_avg(o.get('dex'))} | "
                     f"{_avg(o.get('maps'))} | {s['starters']} |")
    lines += _humanlike_check(ranked, organic)
    lines += _skip_table(usable)
    lines += ["", "## What each knob seems worth", "",
              "Ridge regression of score on every knob plus the starter. **Effect** is the change in score (out of "
              "1.0) from turning the knob away from baseline. Only a SEPARABLE knob's number means anything: a knob "
              "that has always changed together with another cannot be told apart from it.", "",
              "| knob | meaning | effect | se | runs on / off | separable |", "|---|---|---|---|---|---|"]
    for e in effects:
        sep = "yes" if e["separable"] else f"no (moves with {len(e['confounded_with'])} others)"
        lines.append(f"| {e['gene'].removeprefix('POKEBOT_')} | {K.GENES[e['gene']][1]} | {e['effect']:+.3f} | "
                     f"{e['se']:.3f} | {e['runs_on']} / {e['runs_off']} | {sep} |")
    if not effects:
        lines.append("_Not enough scored runs yet._")
    lines += _design_line(records)
    walls = collections.Counter(r["wall"] for r in usable)
    lines += ["", "## Where runs end", "", "| how the run ended | runs | share | hint from our research |",
              "|---|---|---|---|"]
    for wall, n in walls.most_common(12):
        hint = ""
        if wall.startswith("boss wall: "):
            hint = K.BOSS_HINTS.get(wall.removeprefix("boss wall: "), "")
        else:
            hint = next((h for name, _, h in K.WALLS if name == wall), "")
        lines.append(f"| {wall} | {n} | {100 * n / len(usable):.0f}% | {hint} |")
    lines += _boss_table(usable)
    losses = collections.Counter()
    for r in usable:
        losses.update(r["losses"])
    lines += ["", "## Losses to key trainers (all scored runs)", "",
              ", ".join(f"{name} {n}" for name, n in losses.most_common()) or "_none_", "",
              "## Questions for Claude", ""]
    lines += _questions(walls, len(usable), effects, ranked) or ["_None this cycle._"]
    lines += ["", "## Recent cycles", "",
              "A cycle with 0 scored runs carries NO strategy information: either it was a short smoke test, or the "
              "batch was abandoned early (exit 3 = the batch runner's freeze watch saw the code's commit move). "
              "Only scored runs feed the rankings and knob effects.", "",
              "| cycle | when | lanes | exit | runs logged | scored | what it was | arms |", "|---|---|---|---|---|---|---|---|"]
    for c in cycles[-8:]:
        lines.append(f"| {c.get('tag')} | {c.get('finished', '')} | {c.get('lanes', '-')} | {c.get('exit')} | "
                     f"{c.get('runs')} | {c.get('usable')} | {_cycle_kind(c)} | {c.get('arms_label', '')} |")
    data = {"generated": now, "status": status, "runs": len(records), "scored": len(usable),
            "ranked": [{"genome": brain.genome_id(s["genes"]), "label": s["label"], "n": s["n"],
                        "mean": s["mean"], "estimate": brain.posterior(s, mu0)[0], "genes": s["genes"]}
                       for s in ranked],
            "effects": effects, "walls": walls.most_common(), "losses": losses.most_common()}
    return "\n".join(lines) + "\n", data


def _organic(usable: list[dict]) -> dict:
    """genome id -> per-run lists of species caught and distinct places entered (records parsed by parser v2+)."""
    out: dict = collections.defaultdict(lambda: {"species": [], "maps": []})
    for r in usable:
        if "maps_visited" in r:
            o = out[brain.genome_id(r["genome"])]
            o["species"].append(len(r.get("species_caught", [])))
            o["maps"].append(r["maps_visited"])
            if "dex_owned" in r:
                o.setdefault("dex", []).append(r["dex_owned"])
    return out


def _skip_table(usable: list[dict]) -> list[str]:
    """Why the bot passed up new species. Each reason is a rule a person would not follow, and a knob candidate."""
    rows = [r for r in usable if "catch_skips" in r]
    if not rows:
        return []
    total = collections.Counter()
    for r in rows:
        total.update(r["catch_skips"])
    out = ["", "## New species the bot chose NOT to catch (scored runs)", "",
           f"Over {len(rows)} runs. A person catches most new species when first met; each reason below is a bot rule.",
           "", "| reason | skips | per run |", "|---|---|---|"]
    out += [f"| {reason} | {n} | {n / len(rows):.1f} |" for reason, n in total.most_common(8)]
    return out


def _avg(xs) -> str:
    return f"{sum(xs) / len(xs):.1f}" if xs else "-"


def _humanlike_check(ranked: list[dict], organic: dict) -> list[str]:
    """Flag strategies that play LESS like a person than the baseline: fewer species caught or fewer places
    explored. A progress gain that comes with one of these flags is suspect, not a win."""
    base = organic.get(brain.genome_id(brain.BASE), {})
    if not base.get("species"):
        return ["", "_Human-like check: no baseline runs with play data yet._"]
    b_sp, b_mp = sum(base["species"]) / len(base["species"]), sum(base["maps"]) / len(base["maps"])
    flags = []
    for s in ranked:
        o = organic.get(brain.genome_id(s["genes"]), {})
        if len(o.get("species", [])) < 3:
            continue
        sp, mp = sum(o["species"]) / len(o["species"]), sum(o["maps"]) / len(o["maps"])
        why = [f"catches fewer species ({sp:.1f} vs {b_sp:.1f})"] if sp < 0.8 * b_sp else []
        why += [f"explores fewer places ({mp:.1f} vs {b_mp:.1f})"] if mp < 0.9 * b_mp else []
        if why:
            flags.append(f"- ⚠ `{brain.genome_id(s['genes'])}` {s['label']}: plays LESS like a person than "
                         f"baseline: {'; '.join(why)}.")
    return ["", "## Human-like check (vs baseline)", ""] + (flags or ["_No strategy plays noticeably less like a "
                                                                      "person than the baseline._"])


def _cycle_kind(c: dict) -> str:
    if c.get("source") == "ingest":
        return "prior data (step 14's batch)"
    if c.get("usable"):
        return "a real cycle"
    if str(c.get("exit")) == "3":
        return "ABANDONED early (commit moved), no data"
    if (c.get("lanes") or 0) <= 8:
        return "smoke test, no data"
    return "no scored runs (see data/learner.log)"


def _design_line(records: list[dict]) -> list[str]:
    """How far the screening design has got: rows with at least one scored run."""
    name, rows = brain.screen_rows()
    if not rows:
        return []
    scored = collections.Counter(brain.genome_id(r["genome"]) for r in records if r.get("usable"))
    done = [i + 1 for i, row in enumerate(rows) if scored.get(brain.genome_id(row))]
    return ["", f"Screening design ({name}): {len(done)} of {len(rows)} rows have scored runs "
                f"({', '.join(map(str, done)) or 'none yet'}). Knob effects become separable as rows fill in.", ""]


def _mean(xs: list[float]) -> str:
    return f"{sum(xs) / len(xs):.1f} (n={len(xs)})" if xs else "-"


def _boss_table(usable: list[dict]) -> list[str]:
    """Per key trainer: who reached it, who beat it, and the team's level when it lost first and when it won."""
    out = ["", "## Boss by boss (scored runs)", "",
           "Average team level comes from the newest heartbeat before the battle ended (a heartbeat is periodic, so "
           "it is the party shortly before). A big gap between 'first loss' and 'win' means the bot wins by "
           "grinding, not by planning.", "",
           "| trainer | its levels (decomp) | runs that fought | beat it | losses per run (mean) | never beat it | "
           "avg team level at first loss | at the win |", "|---|---|---|---|---|---|---|---|"]
    order = list(K.LEADERS.values()) + list(K.ELITE_FOUR.values()) + list(K.CHAMPION.values())
    for name in order:
        logs = [r["boss_log"][name] for r in usable if name in r.get("boss_log", {})]
        if not logs:
            continue
        won = [b for b in logs if b["won"]]
        lv_loss = [sum(lv) / len(lv) for b in logs if (lv := scoring.party_levels(b.get("party_first_loss")))]
        lv_win = [sum(lv) / len(lv) for b in won if (lv := scoring.party_levels(b.get("party_win")))]
        lv = K.BOSS_LEVELS.get(name)
        boss = f"{min(lv)}-{max(lv)}" if lv else "-"
        out.append(f"| {name} | {boss} | {len(logs)} | {len(won)} ({100 * len(won) / len(logs):.0f}%) | "
                   f"{sum(b['losses'] for b in logs) / len(logs):.1f} | {len(logs) - len(won)} | {_mean(lv_loss)} | "
                   f"{_mean(lv_win)} |")
    if len(out) == 6:
        out.append("_No per-boss data yet (records from before the parser upgrade: run `learner.py reparse`)._")
    else:
        out += ["", "For scale, a typical HUMAN first playthrough is estimated (Gemini, unverified; "
                "`ai-research-notes/2026-10-03-human-reference-NOTE.md`) to reach Tate & Liza at about Lv 37-43 and "
                "the Champion with about 65-95 species owned."]
    return out
    return out


def _questions(walls, n, effects, ranked) -> list[str]:
    qs = []
    for wall, c in walls.most_common(3):
        if wall != "CHAMPION" and n and c / n >= 0.10:
            qs.append(f"- {wall} ends {100 * c / n:.0f}% of runs. Is there a knob, or a code fix, that addresses it?")
    for e in effects:
        if e["separable"] and abs(e["effect"]) >= 2 * e["se"] and e["se"] > 0:
            qs.append(f"- {e['gene'].removeprefix('POKEBOT_')} looks {'helpful' if e['effect'] > 0 else 'harmful'} "
                      f"({e['effect']:+.3f} +/- {e['se']:.3f}). Confirm before relying on it.")
    if ranked and ranked[0]["n"] >= 20:
        qs.append(f"- The leader `{brain.genome_id(ranked[0]['genes'])}` has {ranked[0]['n']} runs. Worth a "
                  f"pre-registered A/B in the story-bot workflow?")
    return qs


def write(findings: Path, records: list[dict], cycles: list[dict], status: str, key: str = "score") -> Path:
    text, data = build(records, cycles, status, key)
    findings.mkdir(parents=True, exist_ok=True)
    (findings / "LATEST.md").write_text(text, encoding="utf-8")
    (findings / "latest.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    return findings / "LATEST.md"
