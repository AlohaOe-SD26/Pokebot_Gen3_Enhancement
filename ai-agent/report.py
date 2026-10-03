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


def build(records: list[dict], cycles: list[dict], status: str) -> tuple[str, dict]:
    summary = brain.summarize(records)
    mu0 = brain.prior_mean(summary)
    usable = [r for r in records if r.get("usable")]
    effects = brain.gene_effects(records)
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
        "A run's SCORE is its progress out of 13: eight badges, four Elite Four members, the Champion.",
        "",
        "## Strategies ranked (best estimate first)",
        "",
        "| genome | knobs changed from baseline | runs | mean score | estimate +/- sd | champions | by starter (n, mean) |",
        "|---|---|---|---|---|---|---|",
    ]
    ranked = sorted((s for s in summary.values() if s["n"]), key=lambda s: -brain.posterior(s, mu0)[0])
    for s in ranked[:15]:
        m, sd = brain.posterior(s, mu0)
        lines.append(f"| `{brain.genome_id(s['genes'])}` | {s['label']} | {s['n']} | {s['mean']:.3f} | "
                     f"{m:.3f} +/- {sd:.3f} | {s['champions']} | {s['starters']} |")
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
    lines += ["", "## Recent cycles", "", "| cycle | when | exit | runs logged | scored | arms |", "|---|---|---|---|---|---|"]
    for c in cycles[-8:]:
        lines.append(f"| {c.get('tag')} | {c.get('finished', '')} | {c.get('exit')} | {c.get('runs')} | "
                     f"{c.get('usable')} | {c.get('arms_label', '')} |")
    data = {"generated": now, "status": status, "runs": len(records), "scored": len(usable),
            "ranked": [{"genome": brain.genome_id(s["genes"]), "label": s["label"], "n": s["n"],
                        "mean": s["mean"], "estimate": brain.posterior(s, mu0)[0], "genes": s["genes"]}
                       for s in ranked],
            "effects": effects, "walls": walls.most_common(), "losses": losses.most_common()}
    return "\n".join(lines) + "\n", data


def _mean(xs: list[float]) -> str:
    return f"{sum(xs) / len(xs):.1f} (n={len(xs)})" if xs else "-"


def _boss_table(usable: list[dict]) -> list[str]:
    """Per key trainer: who reached it, who beat it, and the team's level when it lost first and when it won."""
    out = ["", "## Boss by boss (scored runs)", "",
           "Average team level comes from the newest heartbeat before the battle ended (a heartbeat is periodic, so "
           "it is the party shortly before). A big gap between 'first loss' and 'win' means the bot wins by "
           "grinding, not by planning.", "",
           "| trainer | runs that fought | beat it | losses per run (mean) | never beat it | avg team level at first "
           "loss | at the win |", "|---|---|---|---|---|---|---|"]
    order = list(K.LEADERS.values()) + list(K.ELITE_FOUR.values()) + list(K.CHAMPION.values())
    for name in order:
        logs = [r["boss_log"][name] for r in usable if name in r.get("boss_log", {})]
        if not logs:
            continue
        won = [b for b in logs if b["won"]]
        lv_loss = [sum(lv) / len(lv) for b in logs if (lv := scoring.party_levels(b.get("party_first_loss")))]
        lv_win = [sum(lv) / len(lv) for b in won if (lv := scoring.party_levels(b.get("party_win")))]
        out.append(f"| {name} | {len(logs)} | {len(won)} ({100 * len(won) / len(logs):.0f}%) | "
                   f"{sum(b['losses'] for b in logs) / len(logs):.1f} | {len(logs) - len(won)} | {_mean(lv_loss)} | "
                   f"{_mean(lv_win)} |")
    if len(out) == 6:
        out.append("_No per-boss data yet (records from before the parser upgrade: run `learner.py reparse`)._")
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


def write(findings: Path, records: list[dict], cycles: list[dict], status: str) -> Path:
    text, data = build(records, cycles, status)
    findings.mkdir(parents=True, exist_ok=True)
    (findings / "LATEST.md").write_text(text, encoding="utf-8")
    (findings / "latest.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    return findings / "LATEST.md"
