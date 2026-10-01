"""BATTLE-LEVEL ITEM OUTCOMES, per battle class and per outcome — read off a batch (or any set of logs).

⛔ THE NAME IS HISTORICAL; THE QUESTION IS NOT. Design v2 §Step 14 grades the key-battle item policy on "battle-level
metrics (`probe_item_index_space.py`, `probe_boss_healing.py`)", so the file keeps its name. Its ORIGINAL question
(which index space the item-target party menu uses — see HISTORY below) was ANSWERED by KI-101 (2026-09-16): the
driver resolves the menu slot after bag-open and the strategy always passes the party index. RE-PURPOSED 2026-09-30
(`#27-itemprobes`, `ai-research-notes/2026-09-30-itemprobes-DESIGN.md` D3), because on that day it counted three line
kinds that KI-101 retired (0 of each in the batch0927 corpus) and could not tell a key battle from any other.

WHAT IT REPORTS, per battle class (KEY / NON-KEY / WILD / UNCLASSIFIED, `battle_log.battle_class`; WILD is never
folded into NON-KEY; UNCLASSIFIED split by reason) and per outcome (won / lost / other; ⛔ a DRAW is LOST — the game
whites out on it, `battle_log.outcome_bucket`):
  * `[ITEM]` lines by kind (`battle_log.ITEM_KINDS`): requests (`using`), CONSUMED, landed (KI-101's HP-heuristic
    path), not-consumed retries and disables, no-effect (today's and legacy), status cures (worked / no change), the
    KI-101 fresh-read fallback, and `unknown` (an `[ITEM]` line no kind matches — COUNTED, never dropped);
  * from `[DBLITEM]` (design v2 step 13): `use` requests, `menu` passes and refusals by `ok` x `a_pressed` (a refusal
    whose A was pressed anyway exists only under the NOGUARD fault), every `after` line where the PARTNER's HP ROSE
    (the item landed on the wrong Pokémon — each one printed), every `after` where the BAG DROPPED but neither the
    target (`same=1`) nor the partner rose (a "lost item": a benched Pokémon or nowhere visible), and
    `[DBLITEM-OBS]` lines;
  * KEY battles PER KEY GROUP (design v2 §Step 14: leaders, Elite Four + Champion, rivals, Magma/Aqua): n, won, lost,
    other, won/(won+lost), requests and CONSUMED; per (log, trainer) the first attempt's outcome, eventually won, and
    attempts to the first win (a few looping runs dominate a per-attempt rate); and the HP items held at battle start
    (`[TRAINER] start heal_stock=`, HP items only — the production HP policy's own `parameter > 0` filter);
  * `[KEYBATTLE]`: the production verdict's `key=` against the battle's OFFLINE class (they must agree); a
    `[KEYBATTLE]` in a battle with no offline class is counted on its own line;
  * the LEGACY index-space verdict — ONLY when legacy-ONLY lines (`✔ landed using the X-order index`, `both index
    spaces failed`) exist, i.e. only on a batch from 2026-08-10..09-16.
⛔ The outcome tables and the `[KEYBATTLE]` check print REGARDLESS of item data (a log of refusals only is exactly what
step 14 must check).

‼ POSITIVE CONTROLS, printed before any result (exit 1 if one fails — a measurement, not a gate): logs READ (not
merely matched) and bytes read ("no data" must be distinguishable from "could not look"); per lane and outside the
window with --since/--until; `[ITEM]` / `[DBLITEM]` / `[KEYBATTLE]` line counts (zero of all three is NO DATA, not "the
feature does nothing"); unknown kinds and stray tag mentions (must be 0); and a batch with requests but NO verdict line
of any kind (it predates the outcome telemetry: a missing instrument, NOT "items never work").

READS these lines (each kind's exact text is in `battle_log.ITEM_KINDS`, taken from `story_mode._maybe_use_item`):
    [ITEM] using <item> on <mon> <hp>/<max> (use N, worst hit H)
    [ITEM] ✔ CONSUMED (bag count dropped) — the item applied. HP reads …
    [ITEM] ‼ not consumed — the item was NOT consumed — retrying once
    [ITEM] ‼ not consumed — the item was NOT consumed twice; disabling items for the rest of this battle
    [DBLITEM] menu g= battler_in_menu= layout= slot= menu_pid= intended_pid= ok= a_pressed= aim= self=
    [DBLITEM] after g= target=<Species#PID> hp=a->b status1= partner=<Species#PID> hp=a->b <item>=q0->q1 healed= same=
⚠ The CONSUMED line's own words ("the item applied") are the EMITTER's, quoted verbatim. What it proves is only that
the bag count dropped — SOME Pokémon took the item. Which one is known only in a double, from `[DBLITEM] after`.

HISTORY (kept as written in 2026-08; ⛔ HISTORICAL — the question below is CLOSED by KI-101):
  `TurnAction.use_item_on(item, index)` drives the in-battle party menu, and it was not knowable from the code which
  space that `index` lives in: `battle_handler`'s after-faint chooser converts with `map_battle_party_index()` and
  treats the result as MENU order (the KI-34 fix), while the `--driver normancounter` fixture proved the raw PARTY index
  right for the item menu (1-of-5 item uses landing -> 3-of-3). So `StoryItemBattleStrategy` decided EMPIRICALLY: if a
  use did nothing it flipped the space, retried once, and logged which one landed — this probe counted those lines.
  ‼ The fixture could not answer it: it always healed the ACTIVE mon at party slot 0, where the two spaces AGREE; real
  runs diverged constantly (`party 0` vs `battle-order 1` x19, `(1,0)` x12, `(3,0)` x7). ‼ The FIRST attempt was always
  party order, so raw landing counts were biased toward it; the flip-then-landed number was the unbiased signal.

Run (cd tools/story-dev; PYTHONUTF8=1 py -3.12 probe_item_index_space.py ...):
    probe_item_index_space.py 20260810-035733                      # an x4-runs/<stamp> batch (the old layout)
    probe_item_index_space.py --since 20260927 --until 20260928    # install_sandbox endless lanes (the main checkout)
    probe_item_index_space.py --since ... --profiles <dir>         # another profiles directory
    probe_item_index_space.py --since ... --lanes P1 --lanes P2    # only lanes whose name contains P1 or P2
    probe_item_index_space.py --logs "<glob>" [--logs "<glob>"]    # any logs, e.g. a driver's scratch arms
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

#: The per-class / per-outcome columns, in print order (`requests` is the `using` kind).
COLUMNS = ("battles", "item_battles", "requests", "consumed", "landed", "not_consumed_retry", "not_consumed_disable",
           "no_effect", "cure_worked", "cure_no_change", "fresh_read_failed", "unknown", "no_verdict")
DBL_COLUMNS = ("use", "menu", "menu_ok", "menu_ok_not_pressed", "menu_refused", "menu_refused_pressed", "after",
               "after_err", "wrong_target", "lost_item", "struggle-exit", "err", "other", "obs")
#: Per KEY GROUP (battle_log.KEY_GROUPS): n and the outcomes (Draw in `lost`), and the item requests / CONSUMED.
GROUP_FIELDS = ("n", "won", "lost", "other", "requests", "consumed")


def _row() -> dict:
    return dict.fromkeys(COLUMNS, 0)


def battle_row(battle) -> dict:
    """PURE: one battle's item columns (`COLUMNS`), from its `[ITEM]` lines."""
    kinds = bl.item_counts(battle)
    r = _row()
    r["battles"] = 1
    r["item_battles"] = int(bool(battle.items) or bool(battle.dblitem))
    r["requests"] = kinds["using"]
    for k in ("consumed", "landed", "not_consumed_retry", "not_consumed_disable", "cure_worked", "cure_no_change",
              "fresh_read_failed", "unknown"):
        r[k] = kinds[k]
    r["no_effect"] = sum(kinds[k] for k in bl.NO_EFFECT_KINDS)
    r["no_verdict"] = kinds["using"] - sum(kinds[k] for k in bl.VERDICT_KINDS)
    return r


def summarise(logs, param_of=None) -> dict:
    """PURE: `logs` is an iterable of line lists (one per log) -> every count the report prints. `param_of` (an item
    name -> its `parameter`, default `battle_log.item_parameter`) decides which `heal_stock` items are HP items.
    Beyond the class / outcome / `[DBLITEM]` tables: `by_group[g]` (`GROUP_FIELDS`), `key_records`
    `(log_id, opp, group, outcome)` per KEY battle, `stock[g]` the HP-item counts at each KEY battle's start,
    `stock_unread[g]`, `stock_unknown` (item names the data does not know), `kb_no_offline` (`[KEYBATTLE]` lines in a
    battle with no offline class) and `reasons` (why battles are UNCLASSIFIED)."""
    param_of = param_of or bl.item_parameter
    s = {"logs": 0, "t1_logs": 0, "stray": [], "item_lines": 0, "dbl_lines": 0, "kinds": collections.Counter(),
         "unknown": [], "by_class": {c: _row() for c in bl.BATTLE_CLASSES},
         "by_outcome": {(c, o): _row() for c in bl.BATTLE_CLASSES for o in bl.OUTCOMES},
         "dbl": {c: dict.fromkeys(DBL_COLUMNS, 0) for c in bl.BATTLE_CLASSES}, "wrong_target": [], "lost_item": [],
         "keybattle": collections.Counter(), "kb_disagree": [], "kb_no_offline": [],
         "legacy_landed": collections.Counter(), "legacy_flips": collections.Counter(), "legacy_both": 0,
         "by_group": {g: dict.fromkeys(GROUP_FIELDS, 0) for g in bl.KEY_GROUPS}, "key_records": [],
         "stock": {g: [] for g in bl.KEY_GROUPS}, "stock_unread": collections.Counter(), "stock_unknown": set(),
         "reasons": collections.Counter()}
    for lines in logs:
        s["logs"] += 1
        t1 = bl.has_trainer_telemetry(lines)
        s["t1_logs"] += int(t1)
        s["stray"].extend(bl.stray_lines(lines))
        for battle in bl.split_battles(lines):
            cls = bl.battle_class(battle, t1)
            out = bl.outcome_bucket(battle)
            facts = bl.battle_facts(battle, t1)
            r = battle_row(battle)
            for k in COLUMNS:
                s["by_class"][cls][k] += r[k]
                s["by_outcome"][(cls, out)][k] += r[k]
            if facts["reason"]:
                s["reasons"][facts["reason"]] += 1
            if facts["group"]:
                g = s["by_group"][facts["group"]]
                g["n"] += 1
                g[out] += 1
                g["requests"] += r["requests"]
                g["consumed"] += r["consumed"]
                s["key_records"].append((s["logs"], facts["opp"], facts["group"], out))
                count, unknown = bl.hp_item_count(facts["heal_stock"], param_of)
                s["stock_unknown"].update(unknown)
                if count is None:
                    s["stock_unread"][facts["group"]] += 1
                else:
                    s["stock"][facts["group"]].append(count)
            s["item_lines"] += len(battle.items)
            s["dbl_lines"] += len(battle.dblitem) + len(battle.dblobs)
            for line in battle.items:
                kind = bl.item_kind(line)
                s["kinds"][kind] += 1
                if kind == "unknown":
                    s["unknown"].append(line)
                elif kind == "legacy_landed":
                    s["legacy_landed"][bl.index_space(line)] += 1
                elif kind == "no_effect_retry":
                    s["legacy_flips"][bl.index_space(line)] += 1
                elif kind == "legacy_both_failed":
                    s["legacy_both"] += 1
            d = bl.dbl_counts(battle)
            for k in DBL_COLUMNS:
                s["dbl"][cls][k] += d[k]
            for line in battle.dblitem:
                if bl.partner_rose(bl.parse_dblitem(line)):
                    s["wrong_target"].append((cls, out, line))
                if bl.lost_item(bl.parse_dblitem(line)):
                    s["lost_item"].append((cls, out, line))
            for line in battle.keybattle:
                kb = bl.parse_keybattle(line)
                s["keybattle"][f"key={kb.get('key', '?')}"] += 1
                offline = {bl.KEY: True, bl.NONKEY: False}.get(cls)   # the battle's class, from its [TRAINER] lines
                said = {"True": True, "False": False}.get(kb.get("key"))
                if said is not None and offline is not None and said != offline:
                    s["kb_disagree"].append((cls, line))
                if offline is None:
                    s["kb_no_offline"].append((cls, line))
    return s


def legacy_present(s: dict) -> bool:
    """The legacy verdict runs ONLY when a legacy-ONLY line exists (design D3). The shared `no_effect_retry` shape
    alone does not turn it on: today's code prints it on the unreadable-bag fallback."""
    return bool(sum(s["legacy_landed"].values()) or s["legacy_both"])


def _legacy_verdict(s: dict) -> None:
    landed, flips, both = s["legacy_landed"], s["legacy_flips"], s["legacy_both"]
    total = sum(landed.values())
    print("  LEGACY INDEX-SPACE VERDICT (⛔ HISTORICAL — the question is closed by KI-101; printed only because "
          "legacy lines exist):")
    print(f"      landed, by index space : {dict(landed)}  (total {total})")
    print(f"      flips (first try failed): {dict(flips)}")
    print(f"      both spaces failed      : {both}")
    lb, lp, fb = landed.get("battle", 0), landed.get("party", 0), flips.get("battle", 0)
    if fb:
        print(f"      ⇒ of {fb} flips to battle-order, {lb} landed ({100.0 * lb / fb:.0f}%) — every one is a case "
              f"where PARTY order was WRONG")
    if lb == 0 and lp:
        print("      VERDICT: party-order landed every time and battle-order never did.")
    elif lb and lp:
        print("      VERDICT: BOTH spaces land in different situations — the menu ordering is CONDITIONAL.")
    elif lb and not lp:
        print("      VERDICT: battle-order is the real convention; the fixture was the special case.")
    else:
        print("      VERDICT: no landing recorded in the legacy lines.")
    print("      ‼ The first attempt was ALWAYS party-order, so raw landing counts are biased toward it.")


def _stock_line(values: list) -> str:
    if not values:
        return "n 0"
    v = sorted(values)
    return f"n {len(v)}, mean {sum(v) / len(v):.1f}, median {v[len(v) // 2]}"


def report(s: dict, source: str, nfiles: int, nbytes: int, notes=(), matched=None) -> int:
    """Print the report; return the exit code (1 on a control failure, NO DATA, or requests with no verdict line).
    ⛔ The outcome / group / `[KEYBATTLE]` tables print BEFORE any of those verdicts, never skipped by them (S2).
    `nfiles` counts SUCCESSFUL reads; `matched` (default `nfiles`) the paths selected; `notes` the selection notes."""
    bar = "=" * 112
    print(bar)
    print(f"BATTLE-LEVEL ITEM OUTCOMES — {source}")
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
    print(f"  CONTROL: {s['item_lines']} [ITEM] line(s) by kind: {dict(s['kinds'].most_common())}")
    print(f"  CONTROL: {s['dbl_lines']} [DBLITEM]/[DBLITEM-OBS] line(s); {sum(s['keybattle'].values())} [KEYBATTLE] "
          f"line(s); {len(s['stray'])} stray tag mention(s) (must be 0); {s['t1_logs']} of {s['logs']} log(s) carry "
          f"[TRAINER] telemetry")
    failed = False
    if s["unknown"]:
        failed = True
        print(f"  ‼ CONTROL FAILED — {len(s['unknown'])} [ITEM] line(s) match NO known kind (the parser is behind the "
              f"code; they are counted as `unknown`, never dropped):")
        for line in s["unknown"][:5]:
            print(f"      {line}")
    if s["stray"]:
        failed = True
        print("  ‼ CONTROL FAILED — lines mention a battle tag outside its position (a format drift):")
        for line in s["stray"][:5]:
            print(f"      {line}")
    no_item_data = not s["item_lines"] and not s["dbl_lines"]
    nodata = no_item_data and not s["keybattle"]
    if no_item_data:
        print("  ‼ NO ITEM DATA — no [ITEM] or [DBLITEM] line: the logs predate `#24-battleitems`, or the bot never used "
              "an item. That is a missing measurement, not evidence the feature does nothing."
              + ("" if nodata else " The [KEYBATTLE] verdicts and the outcome tables below ARE data (exit 0)."))
    requests = sum(r["requests"] for r in s["by_class"].values())
    verdicts = sum(s["kinds"][k] for k in bl.VERDICT_KINDS)
    noverdict = False
    if requests and not verdicts:
        noverdict = True
        print("  ‼ NO VERDICT RECORDS — item requests but no outcome line of any kind: these logs predate the outcome "
              "telemetry. This is a missing instrument, NOT 'items never work'.")

    def table(rows: list) -> None:
        heads = ("battles", "item btl", "requests", "CONSUMED", "landed", "nc-retry", "nc-disable", "no-effect",
                 "cure ok", "cure =", "fresh-fail", "unknown", "no verdict")
        print(f"      {'':<24}" + "".join(f"{h:>11}" for h in heads))
        for label, r in rows:
            print(f"      {label:<24}" + "".join(f"{r[k]:>11,}" for k in COLUMNS))

    print()
    print("  PER BATTLE CLASS  (WILD is never folded into NON-KEY; UNCLASSIFIED includes every battle of a log "
          "without [TRAINER] telemetry)")
    table([(c, s["by_class"][c]) for c in bl.BATTLE_CLASSES])
    if s["reasons"]:
        print(f"      UNCLASSIFIED by reason: {dict(s['reasons'].most_common())}")
    print()
    print("  PER BATTLE CLASS x OUTCOME  (rows with no battle omitted; ⛔ a Draw is LOST — the game whites out on it)")
    table([(f"{c} / {o}", s["by_outcome"][(c, o)]) for c in bl.BATTLE_CLASSES for o in bl.OUTCOMES
           if s["by_outcome"][(c, o)]["battles"]])
    print()
    print("  KEY BATTLES PER GROUP x OUTCOME  (design v2 §Step 14: leaders, Elite Four + Champion, rivals, Magma/Aqua)")
    for line in bl.group_outcome_lines(s["by_group"]):
        print(line)
    print(f"      item requests / CONSUMED per group: "
          f"{ {g: (r['requests'], r['consumed']) for g, r in s['by_group'].items()} }")
    print("  KEY BATTLES PER TRAINER MET  (per (log, opp): a few looping runs dominate a per-attempt rate)")
    for line in bl.attempt_lines(bl.attempt_summary(s["key_records"])):
        print(line)
    print("  HP ITEMS HELD AT KEY-BATTLE START  ([TRAINER] start heal_stock=; HP items = the HP policy's parameter > 0)")
    for g in bl.KEY_GROUPS:
        print(f"      {g:<13}{_stock_line(s['stock'][g])}"
              + (f"; {s['stock_unread'][g]} unreadable" if s["stock_unread"][g] else ""))
    if s["stock_unknown"]:
        print(f"      ‼ item names the item data does not know (not counted): {sorted(s['stock_unknown'])}")
    print()
    print("  [DBLITEM] PER BATTLE CLASS  (menu: ok x a_pressed; WRONG TARGET = an `after` whose PARTNER's HP rose; LOST = "
          "the bag dropped, the target did not rise (same=1), the partner did not rise)")
    heads = ("use", "menu", "ok,A", "ok,noA", "refused", "refused,A!", "after", "after err", "WRONG TGT", "LOST item",
             "strug-exit", "err", "other", "observe")
    print(f"      {'':<14}" + "".join(f"{h:>11}" for h in heads))
    for c in bl.BATTLE_CLASSES:
        d = dict(s["dbl"][c])
        d["menu_ok"] -= d["menu_ok_not_pressed"]       # print ok,A and ok,noA as disjoint columns
        d["menu_refused"] -= d["menu_refused_pressed"]
        print(f"      {c:<14}" + "".join(f"{d[k]:>11,}" for k in DBL_COLUMNS))
    if s["wrong_target"]:
        print(f"  ‼ {len(s['wrong_target'])} WRONG-TARGET `after` line(s) — the item raised the PARTNER's HP:")
        for cls, out, line in s["wrong_target"]:
            print(f"      [{cls} / {out}] {line}")
    else:
        print("  ⇒ 0 wrong-target `after` lines.")
    if s["lost_item"]:
        print(f"  ‼ {len(s['lost_item'])} LOST-ITEM `after` line(s) — the bag dropped and no visible battler rose:")
        for cls, out, line in s["lost_item"]:
            print(f"      [{cls} / {out}] {line}")
    else:
        print("  ⇒ 0 lost-item `after` lines.")
    print()
    if s["keybattle"]:
        print(f"  [KEYBATTLE] production verdicts: {dict(s['keybattle'])}; disagreeing with the battle's offline "
              f"class (from its [TRAINER] lines): {len(s['kb_disagree'])}")
        for cls, line in s["kb_disagree"][:5]:
            print(f"      ‼ a FINDING about the production gate, not a probe failure: [{cls}] {line}")
        print(f"      [KEYBATTLE] in a battle with NO offline class (WILD / UNCLASSIFIED — not comparable): "
              f"{len(s['kb_no_offline'])}")
    if legacy_present(s):
        print()
        _legacy_verdict(s)
    else:
        print(f"  (no legacy-only [ITEM] line, so no legacy index-space verdict; `no_effect_retry` lines: "
              f"{sum(s['legacy_flips'].values())})")
    print()
    print("‼ `no verdict` = requests minus verdict lines in the same battle: the battle ended, the target switched or "
          "fainted (cleared silently), or the next decision never came. It is not a failure count.")
    print("‼ CONSUMED proves only that the bag count dropped — SOME Pokémon took the item; which one is known only in a "
          "double ([DBLITEM] after: WRONG TGT / LOST item).")
    if nodata:
        print("‼ NO DATA: no [ITEM], [DBLITEM] or [KEYBATTLE] line — exit 1.")
    return 1 if failed or nodata or noverdict else 0


DEFAULT_STAMP = "20260810-035733"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Battle-level item outcomes per battle class, key group and outcome.")
    bl.add_source_args(ap, DEFAULT_STAMP)
    args = ap.parse_args(argv)
    paths, source, notes = bl.resolve_sources(args, ap, DEFAULT_STAMP)
    stats: dict = {}
    summary = summarise(bl.read_logs(paths, stats))      # one log in memory at a time (a batch is ~100 MB of text)
    return report(summary, source, stats["read"], stats["bytes"], notes=notes, matched=len(paths))


if __name__ == "__main__":
    sys.exit(main())
