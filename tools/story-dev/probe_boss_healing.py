"""How often does an opponent HEAL mid-battle, and does the bot lose those fights?

WHY. `--driver normancounter` showed Norman restoring **Vigoroth 1 -> 53** and **Slaking 27 -> 136**
while the party chipped 6-8 damage a turn. Chip damage into a healing 143-HP boss cannot win
whatever type it is — so "the bot has no answer to boss item usage" is a candidate explanation for
the counter chain's *"N losses with no super-effective answer"* stop, which ends **~88% of all
non-finishing runs**.

‼ THE COMPANION HYPOTHESIS IS ALREADY DEAD, and this exists partly because of that. The same run
also showed the bot entering Norman with its ace at 0 HP, which looked like the bigger lever —
until `probe_fainted_ace.py`, reading the direct `hp=` field over a whole batch, measured **6.4%**
of battles starting with any mon fainted and **2.9%** with the ace down, against a mean party
health of **90.6%**. That anchor was not representative. **Do not assume this one is either** —
that is the whole point of measuring it over a batch.

HOW IT READS. `#24-bosstelemetry` logs the opponent every turn:

    [TURN 12] Ninjask L27 80/80 -> UseMove:Scratch(pp34)  vs Slaking L31 130/143
    [TURN 3] Mightyena L43 69/127 [Paralysis] -> UseMove:Take Down(pp12)  vs Vigoroth L29 24/88 [Uproar/MultipleTurns]

A HEAL is the same opponent's current HP going UP between consecutive turns of one battle.
Identity is `(name, max_hp)`, so a switch to a different species — or to the same species with
different bulk — is not mistaken for healing.

‼ FIXED 2026-09-30 (`#27-itemprobes`, `ai-research-notes/2026-09-30-itemprobes-DESIGN.md` D2). The
pattern used to end `L(\\d+) (\\d+)/(\\d+)\\s*$`, so every turn whose FOE carried a status suffix (the
second example above) was DROPPED: ~6,600 of 134,768 `[TURN]` lines in the batch0927 corpus. Parsing
now lives in `battle_log.py` (shared with `probe_item_index_space.py` and pinned by
`probe_itemprobes.py`). A `vs ?` line has NO foe data: it is counted as such, never parsed and never
called "missed".

‼ TWO CLASSES OF HEAL, AND ONLY ONE OF THEM IS UNDERSTOOD — do not let a claim mix them.
Across 2,565 events in two batches the magnitudes split cleanly:
  * **LARGE (>= `BIG_HEAL_HP`, default 50)** — `Slaking` dominates, at **+106 / +108 / +119** and a
    median of +81. That is a trainer using a Full Restore / Hyper Potion, and it is the only class
    any conclusion in this project rests on.
  * **SMALL (mostly +1 / +2 / +3, decaying smoothly)** — **UNEXPLAINED.** It was investigated on
    2026-08-10 and the obvious candidate was RULED OUT: held berries would spike at exactly +10
    (Oran) and +30 (Sitrus), and the histogram shows no such spike — it is a smooth decay
    (`+1` x374, `+2` x139, `+3` x127, …). Leftovers-style per-turn regen fits the tiny values for
    small wild mons but not the +14/+15/+16 cluster on `Illumise`. A reading artifact is possible
    and has not been excluded.
So the probe reports the two classes SEPARATELY, and the headline number is the large-heal one.
Anyone extending this should either explain the small class or leave it quarantined — folding it
into a total would silently inflate every "bosses heal" statement.
  * **REST is neither** (2026-09-30, the independent pass, S4): a rise whose record NEWLY gains
    `[Sleep]` is the foe using Rest (16 of batch0927's 558 LARGE rises — Juan's Kingdra). It is
    tagged "rest" by `battle_log.foe_heal_events` and reported apart, never as an item heal.

PER BATTLE CLASS (design D2). Every battle is KEY / NON-KEY (from its `[TRAINER]` class ids against
`trainer_identity.KEY_TRAINER_CLASSES`), WILD (a started battle with no `[TRAINER]` line, in a log that
HAS `[TRAINER]` telemetry), or UNCLASSIFIED (anything else — including every battle of a log that
predates `[TRAINER]`, design v2 step 5, 2026-09-29, where the absence of the line says nothing; the
report splits UNCLASSIFIED by reason). WILD is never folded into NON-KEY.

DOES THE BOT LOSE THOSE FIGHTS? (the question in this file's first line — answered, not just asked).
Each class reports won / lost / other for its battles WITH a LARGE heal and WITHOUT one, and the KEY
battles are split by KEY GROUP (leaders, Elite Four + Champion, rivals, Magma/Aqua; `battle_log
.KEY_GROUPS`) with n, won, lost, other and won/(won+lost). ⛔ A DRAW IS A LOSS (the game whites out on
it; `battle_log.outcome_bucket` cites the decomp). Per group it also reports, per (log, trainer), the
FIRST attempt's outcome, whether it was EVENTUALLY won and how many attempts that took — because a few
runs that loop on one trainer (28 whiteouts at Tate & Liza in one batch0927 run) dominate a
per-attempt rate.

‼ POSITIVE CONTROLS, printed before any result (exit 1 if one fails — a measurement, not a gate):
  * files READ (successful reads, not paths matched) and bytes read ("no data" must be
    distinguishable from "could not look"); with --since/--until, logs per lane and how many the
    window left out before and after;
  * `[TURN]` lines: parsed / no foe data / UNPARSED WITH FOE DATA (must be 0 — each is real data
    lost) and stray tag mentions (must be 0 — a format drift). If NOTHING parses, the regex is wrong;
    that is never a rate of zero (a batch that predates `#24-bosstelemetry`, 2026-08-09, has no turns).

‼ WHAT IT CANNOT SAY (each also printed under the report):
  * A run that ends on the counter chain's stop ends without a final battle at all, and a
    pre-`[TRAINER]` log cannot mark boss battles: there the longest battles are a labelled PROXY.
  * "Turn records" are `[TURN]` LINES, and one decision can render 2-3 identical lines, so the
    >=12-record proxy is ~4-6 real turns. Lines are NOT de-duplicated (the filed counts are lines).
  * Two IDENTICAL foes (same species and max HP: Phoebe's two Banette, Roxanne_1's two Geodude) are
    one identity, so the second one coming in can read as a heal. The fix — the foe's PID on the
    `[TURN]` line — is a PRODUCTION change, out of scope here.
  * In a DOUBLE battle the `[TURN]` line describes only the LEFT foe: the doubles column is labelled
    "left foe only", and a right-side heal is invisible.

Run (cd tools/story-dev; PYTHONUTF8=1 py -3.12 probe_boss_healing.py ...):
    probe_boss_healing.py 20260809-155844                      # an x4-runs/<stamp> batch (the old layout)
    probe_boss_healing.py --since 20260927 --until 20260928    # install_sandbox endless lanes (the main checkout)
    probe_boss_healing.py --since ... --profiles <dir>         # another profiles directory
    probe_boss_healing.py --since ... --lanes P1 --lanes P2    # only lanes whose name contains P1 or P2
    probe_boss_healing.py --logs "<glob>" [--logs "<glob>"]    # any logs, e.g. a driver's scratch arms
"""
from __future__ import annotations

import argparse
import collections
import sys

import battle_log as bl

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:  # a stream without reconfigure keeps its own encoding; printing still works under PYTHONUTF8=1
    pass

#: Heals at or above this are the understood class (trainer item usage). Below it lies the
#: unexplained small class — see the module docstring. Quarantined, never folded into a total.
BIG_HEAL_HP = 50
#: The boss-length PROXY (only meaningful where battles cannot be classified).
LONG_BATTLE_TURNS = 12

_CLASS_FIELDS = ("battles", "with_turns", "turns", "no_foe", "big_battles", "big_events", "any_battles",
                 "any_events", "long", "long_big", "won", "lost", "other", "big_won", "big_lost", "big_other",
                 "doubles", "big_doubles", "rest_battles", "rest_events")
#: Per KEY GROUP (battle_log.KEY_GROUPS): n, the outcomes, the LARGE-heal battles and their outcomes, doubles.
_GROUP_FIELDS = ("n", "won", "lost", "other", "big_battles", "big_won", "big_lost", "doubles")


def summarise(logs) -> dict:
    """PURE: `logs` is an iterable of line lists (one per log) -> every count the report prints.
    `by_class[cls]` holds `_CLASS_FIELDS`; `by_group[g]` holds `_GROUP_FIELDS`; `events` holds
    `(cls, delta, foe, before, after)` for every NON-Rest rise; `rests` the same for Rest rises; `key_records`
    `(log_id, opp, group, outcome)` per KEY battle (for `battle_log.attempt_summary`); `reasons` counts why
    battles are UNCLASSIFIED."""
    s = {"logs": 0, "t1_logs": 0, "turn_lines": 0, "parsed": 0, "no_foe": 0, "unparsed": [], "stray": [],
         "by_class": {c: dict.fromkeys(_CLASS_FIELDS, 0) for c in bl.BATTLE_CLASSES},
         "by_group": {g: dict.fromkeys(_GROUP_FIELDS, 0) for g in bl.KEY_GROUPS}, "events": [], "rests": [],
         "key_records": [], "reasons": collections.Counter()}
    for lines in logs:
        s["logs"] += 1
        t1 = bl.has_trainer_telemetry(lines)
        s["t1_logs"] += int(t1)
        s["stray"].extend(bl.stray_lines(lines))
        for battle in bl.split_battles(lines):
            cls = bl.battle_class(battle, t1)
            facts = bl.battle_facts(battle, t1)
            row = s["by_class"][cls]
            row["battles"] += 1
            out = facts["outcome"]
            row[out] += 1
            row["doubles"] += int(bool(facts["double"]))
            if facts["reason"]:
                s["reasons"][facts["reason"]] += 1
            grp = s["by_group"][facts["group"]] if facts["group"] else None
            if grp is not None:
                grp["n"] += 1
                grp[out] += 1
                grp["doubles"] += int(bool(facts["double"]))
                s["key_records"].append((s["logs"], facts["opp"], facts["group"], out))
            turns = []
            for line in battle.turns:
                shape = bl.turn_shape(line)
                s["turn_lines"] += 1
                if shape == "parsed":
                    turns.append(bl.parse_turn(line))
                elif shape == "no_foe":
                    s["no_foe"] += 1
                    row["no_foe"] += 1
                else:
                    s["unparsed"].append(line)
            s["parsed"] += len(turns)
            row["turns"] += len(turns)
            if not turns:
                continue
            row["with_turns"] += 1
            all_events = bl.foe_heal_events(turns)
            events = [e[:4] for e in all_events if e[4] != "rest"]       # REST is a move, never an item heal
            rests = [e[:4] for e in all_events if e[4] == "rest"]
            big = [e for e in events if e[3] - e[2] >= BIG_HEAL_HP]
            row["any_battles"] += int(bool(events))
            row["any_events"] += len(events)
            row["big_battles"] += int(bool(big))
            row["big_events"] += len(big)
            row["rest_battles"] += int(bool(rests))
            row["rest_events"] += len(rests)
            if big:
                row["big_" + out] += 1
                row["big_doubles"] += int(bool(facts["double"]))
                if grp is not None:
                    grp["big_battles"] += 1
                    if out in ("won", "lost"):
                        grp["big_" + out] += 1
            if len(turns) >= LONG_BATTLE_TURNS:
                row["long"] += 1
                row["long_big"] += int(bool(big))
            s["events"].extend((cls, e[3] - e[2], e[1], e[2], e[3]) for e in events)
            s["rests"].extend((cls, e[3] - e[2], e[1], e[2], e[3]) for e in rests)
    return s


def _pct(n: int, d: int) -> str:
    return f"{100.0 * n / d:.1f}%" if d else "n/a"


def report(s: dict, source: str, nfiles: int, nbytes: int, notes=(), matched=None) -> int:
    """Print the report; return the exit code (1 on a control failure). `nfiles` counts SUCCESSFUL reads; `matched`
    (default `nfiles`) the paths selected; `notes` the selection notes (per lane, the window's exclusions, warnings)."""
    bar = "=" * 96
    print(bar)
    print(f"OPPONENT MID-BATTLE HEALING — {source}")
    print(bar)
    matched = nfiles if matched is None else matched
    print(f"  CONTROL: {nfiles} debug log(s) read of {matched} selected, {nbytes:,} bytes read")
    for note in notes:
        print(f"  CONTROL: {note}")
    if matched != nfiles:
        print(f"  ‼ {matched - nfiles} selected log(s) could NOT be read — the counts below exclude them.")
    if not nfiles:
        print("  ‼ CONTROL FAILED — no debug logs matched. Check the stamp / --since/--until / --profiles / --logs.")
        return 1
    print(f"  CONTROL: {s['turn_lines']:,} [TURN] lines: {s['parsed']:,} turn records parsed, {s['no_foe']:,} with "
          f"NO FOE DATA (`vs ?`), {len(s['unparsed'])} UNPARSED WITH FOE DATA (must be 0)")
    print(f"  CONTROL: {len(s['stray'])} stray tag mention(s) (must be 0); "
          f"{s['t1_logs']} of {s['logs']} log(s) carry [TRAINER] telemetry")
    failed = False
    if s["unparsed"]:
        failed = True
        print("  ‼ CONTROL FAILED — [TURN] lines WITH foe data that the pattern missed (real data lost):")
        for line in s["unparsed"][:5]:
            print(f"      {line}")
    if s["stray"]:
        failed = True
        print("  ‼ CONTROL FAILED — lines mention a battle tag outside its position (a format drift):")
        for line in s["stray"][:5]:
            print(f"      {line}")
    if not s["parsed"]:
        print("  ‼ CONTROL FAILED — no turn record parsed. Either these logs predate `#24-bosstelemetry` "
              "(2026-08-09) or the pattern is wrong. Not a rate of zero.")
        return 1

    by = s["by_class"]
    total_b = sum(r["battles"] for r in by.values())
    total_wt = sum(r["with_turns"] for r in by.values())
    print()
    print(f"  PER BATTLE CLASS  ({total_b:,} battles, {total_wt:,} with turn records; WILD is never folded into NON-KEY)")
    print(f"      {'class':<13}{'battles':>9}{'w/turns':>9}{'turn recs':>11}{'vs ?':>8}"
          f"{'LARGE-heal battles (events)':>30}{'[quarantined] any heal (events)':>34}{'Rest (events)':>15}"
          f"{'doubles: left foe only':>24}")
    for cls in bl.BATTLE_CLASSES:
        r = by[cls]
        print(f"      {cls:<13}{r['battles']:>9,}{r['with_turns']:>9,}{r['turns']:>11,}{r['no_foe']:>8,}"
              f"{r['big_battles']:>14,} {_pct(r['big_battles'], r['with_turns']):>6} ({r['big_events']:,})"
              f"{r['any_battles']:>17,} {_pct(r['any_battles'], r['with_turns']):>6} ({r['any_events']:,})"
              f"{r['rest_battles']:>8,} ({r['rest_events']:,})"
              f"{r['doubles']:>11,} ({r['big_doubles']:,} w/ LARGE)")
    if s["reasons"]:
        print(f"      UNCLASSIFIED by reason: {dict(s['reasons'].most_common())}")
    print()
    print("  DOES THE BOT LOSE THOSE FIGHTS?  (won / lost / other; ⛔ a Draw is a loss — the game whites out)")
    print(f"      {'class':<13}{'with a LARGE heal: won/lost/other':>36}{'rate':>9}{'all battles: won/lost/other':>32}"
          f"{'rate':>9}")
    for cls in bl.BATTLE_CLASSES:
        r = by[cls]
        print(f"      {cls:<13}{str(r['big_won']) + ' / ' + str(r['big_lost']) + ' / ' + str(r['big_other']):>36}"
              f"{bl._fmt_rate(r['big_won'], r['big_lost']):>9}"
              f"{str(r['won']) + ' / ' + str(r['lost']) + ' / ' + str(r['other']):>32}"
              f"{bl._fmt_rate(r['won'], r['lost']):>9}")
    print()
    print("  KEY BATTLES PER GROUP x OUTCOME  (design v2 §Step 14: leaders, Elite Four + Champion, rivals, Magma/Aqua)")
    for line in bl.group_outcome_lines(s["by_group"]):
        print(line)
    print(f"      LARGE-heal key battles per group: "
          f"{ {g: (r['big_battles'], r['big_won'], r['big_lost']) for g, r in s['by_group'].items()} } "
          f"(battles, won, lost); doubles (left foe only): { {g: r['doubles'] for g, r in s['by_group'].items()} }")
    print("  KEY BATTLES PER TRAINER MET  (per (log, opp): a few looping runs dominate a per-attempt rate)")
    for line in bl.attempt_lines(bl.attempt_summary(s["key_records"])):
        print(line)
    big_b = sum(r["big_battles"] for r in by.values())
    big_e = sum(r["big_events"] for r in by.values())
    any_b = sum(r["any_battles"] for r in by.values())
    any_e = sum(r["any_events"] for r in by.values())
    print()
    print(f"  ⇒ battles with a LARGE heal (>= {BIG_HEAL_HP} HP — the understood class): "
          f"{big_b} of {total_wt} ({_pct(big_b, total_wt)}), {big_e} events")
    print(f"     [quarantined] battles with ANY heal incl. the unexplained small class: "
          f"{any_b} ({_pct(any_b, total_wt)}), {any_e} events")
    if by[bl.KEY]["with_turns"] or by[bl.NONKEY]["with_turns"]:
        k, n = by[bl.KEY], by[bl.NONKEY]
        print(f"  ⇒ KEY battles with a LARGE heal: {k['big_battles']} of {k['with_turns']} "
              f"({_pct(k['big_battles'], k['with_turns'])});  NON-KEY: {n['big_battles']} of {n['with_turns']} "
              f"({_pct(n['big_battles'], n['with_turns'])})")
    else:
        print("  ⇒ no battle is KEY or NON-KEY: these logs carry no readable [TRAINER] class. The boss-length "
              "PROXY below is the only boss signal they hold.")

    long_n = sum(r["long"] for r in by.values())
    if long_n:
        long_big = sum(r["long_big"] for r in by.values())
        print(f"  PROXY — battles of >={LONG_BATTLE_TURNS} turn records (boss-length): "
              f"{long_big} of {long_n} show a LARGE heal ({_pct(long_big, long_n)})")

    names = collections.Counter(foe for _c, _d, foe, _b, _a in s["events"])
    if names:
        print(f"  opponents most often healed: {names.most_common(8)}")
    biggest = sorted(((d, foe, b, a, c) for c, d, foe, b, a in s["events"]), reverse=True)
    if biggest:
        print("  largest single heals:")
        for delta, foe, before, after, cls in biggest[:6]:
            print(f"     +{delta:<4} {foe}  {before} -> {after}   [{cls}]")
    rest_n = len(s["rests"])
    if rest_n:
        print(f"  REST (a rise that newly gains [Sleep] — a move, never an item; NOT in the heal counts): {rest_n} "
              f"event(s), e.g. {[(foe, b, a) for _c, _d, foe, b, a in s['rests'][:3]]}")
    print()
    print("‼ A run that ends on the counter chain's stop ends WITHOUT a final battle, so boss battles are "
          "under-counted here; in a log without [TRAINER] telemetry the >=12-turn row is only a labelled PROXY.")
    print("‼ 'Turn records' are [TURN] LINES: one decision can render 2-3 identical lines, so the >=12-record proxy is "
          "~4-6 real turns (lines are deliberately NOT de-duplicated).")
    print("‼ Two IDENTICAL foes (same species and max HP, e.g. Phoebe's two Banette) are one identity: the second "
          "coming in can read as a heal. Only the foe's PID on [TURN] (a PRODUCTION change) would fix it.")
    print("‼ In a DOUBLE battle [TURN] describes only the LEFT foe: right-side heals are invisible ('left foe only').")
    return 1 if failed else 0


DEFAULT_STAMP = "20260809-155844"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Opponent mid-battle healing, per battle class and key group.")
    bl.add_source_args(ap, DEFAULT_STAMP)
    args = ap.parse_args(argv)
    paths, source, notes = bl.resolve_sources(args, ap, DEFAULT_STAMP)
    stats: dict = {}
    summary = summarise(bl.read_logs(paths, stats))      # one log in memory at a time (a batch is ~100 MB of text)
    return report(summary, source, stats["read"], stats["bytes"], notes=notes, matched=len(paths))


if __name__ == "__main__":
    sys.exit(main())
