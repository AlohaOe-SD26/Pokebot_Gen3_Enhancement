"""Which index space does the ITEM-target party menu actually use? Read the answer off a batch.

THE QUESTION. `TurnAction.use_item_on(item, index)` drives the in-battle party menu, and it was
not knowable from the code which space that `index` lives in:
  * `battle_handler`'s after-faint chooser converts with `map_battle_party_index()` and treats the
    result as MENU order — and is right there; that conversion is what fixed KI-34.
  * the `--driver normancounter` fixture proved the raw PARTY index right for the item menu
    (1-of-5 item uses landing -> 3-of-3 after the change).
Two menus, two conventions, and a third guess would have been a guess. So `StoryItemBattleStrategy`
now decides EMPIRICALLY: if a use demonstrably does nothing (HP did not rise by the next
decision) it flips the space, retries once, and logs which one landed. This probe counts those
lines.

‼ WHY THE FIXTURE COULD NOT ANSWER IT, and why only a batch can: the fixture always heals the
ACTIVE mon sitting at party slot 0, which is exactly the case where the two spaces AGREE. Real
runs heal whatever is hurt, wherever it sits — that is where they diverge, and the logged pairs
show them diverging constantly (`party 0` vs `battle-order 1` x19, `(1,0)` x12, `(3,0)` x7).

READS these lines, emitted by `plugins/custom_modes/story_mode.py`:
    [ITEM] using <item> on <mon> <hp>/<max> (use N, worst hit H)
    [ITEM] ✔ landed using the <party|battle>-order index (HP now …)
    [ITEM] ‼ no effect (…) — retrying with the <party|battle>-order index
    [ITEM] ‼ no effect (…) — both index spaces failed; disabling items …

‼ POSITIVE CONTROLS, printed before any result: logs opened and bytes read (`x4-runs/` is
gitignored, so "no data" must be distinguishable from "could not look"), and the count of
`[ITEM] using` requests. If requests are zero the batch predates the feature and the verdict is
"no data", NOT "the feature does nothing".

HOW TO READ THE VERDICT. A space that lands far more often is the menu's real convention. ‼ Note
the asymmetry deliberately: the FIRST attempt always uses `party` order, so `party` gets first
refusal on every battle. What is diagnostic is how often a FLIP to `battle` then LANDS — every one
of those is a case where party order was wrong and battle order was right.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_item_index_space.py 20260810-035733
"""
import collections
import glob
import os
import re
import sys

USING_RE = re.compile(r"\[ITEM\] using (.+?) on (\w+)")
LANDED_RE = re.compile(r"\[ITEM\] .*landed using the (\w+)-order index")
RETRY_RE = re.compile(r"\[ITEM\] .*retrying with the (\w+)-order index")
BOTH_RE = re.compile(r"\[ITEM\] .*both index spaces failed")


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else "20260810-035733"
    paths = sorted(glob.glob(os.path.join("x4-runs", stamp, "L0*", "debug-logs", "*.log")))

    total_bytes = 0
    using = 0
    landed = collections.Counter()
    retried = collections.Counter()
    both_failed = 0
    items_used = collections.Counter()

    for path in paths:
        try:
            total_bytes += os.path.getsize(path)
        except OSError:
            pass
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    m = USING_RE.search(line)
                    if m:
                        using += 1
                        items_used[m.group(1).strip()] += 1
                    m = LANDED_RE.search(line)
                    if m:
                        landed[m.group(1)] += 1
                    m = RETRY_RE.search(line)
                    if m:
                        retried[m.group(1)] += 1
                    if BOTH_RE.search(line):
                        both_failed += 1
        except OSError:
            continue

    print("=" * 84)
    print(f"ITEM-TARGET INDEX SPACE — batch {stamp}")
    print("=" * 84)
    print(f"  CONTROL: {len(paths)} debug log(s), {total_bytes:,} bytes read")
    if not paths:
        print("  ‼ CONTROL FAILED — no debug logs matched that stamp.")
        return 1
    print(f"  CONTROL: {using} `[ITEM] using` requests")
    if using == 0:
        print("  ‼ NO DATA — this batch predates `#24-battleitems`, or the bot never used an item. "
              "That is a missing measurement, not evidence the feature does nothing.")
        return 1
    print(f"  items used: {dict(items_used.most_common(6))}")
    print()

    total_landed = sum(landed.values())

    # ‼ A BATCH CAN HAVE ITEM USES AND STILL BE "NO DATA" FOR THIS QUESTION. The ✔/retry lines
    # were added AFTER `20260809-214515`, which has 86 `[ITEM] using` requests and zero landing
    # records. Without this branch the verdict below reads "items are not working at all" — a
    # confident, wrong statement produced by a MISSING INSTRUMENT rather than by the bot. That is
    # the single most repeated failure mode in this project's history; it gets an explicit guard.
    if total_landed == 0 and not retried and both_failed == 0:
        print("  ‼ NO LANDING RECORDS — this batch has item uses but predates the ✔/retry "
              "telemetry (added 2026-08-10). The index-space question CANNOT be answered from it. "
              "This is a missing instrument, NOT 'items never work'.")
        return 1

    print(f"  landed, by index space : {dict(landed)}  (total {total_landed})")
    print(f"  flips (first try failed): {dict(retried)}")
    print(f"  both spaces failed      : {both_failed}")
    print()

    # The diagnostic quantity: how often a FLIP to the other space then worked.
    flipped_to_battle = retried.get("battle", 0)
    landed_battle = landed.get("battle", 0)
    landed_party = landed.get("party", 0)
    if total_landed:
        print(f"  ⇒ of {total_landed} landings, {landed_party} were party-order and "
              f"{landed_battle} were battle-order")
    if flipped_to_battle:
        rate = 100.0 * landed_battle / flipped_to_battle
        print(f"  ⇒ of {flipped_to_battle} flips to battle-order, {landed_battle} landed "
              f"({rate:.0f}%) — every one is a case where PARTY order was WRONG")
    print()
    if landed_battle == 0 and landed_party:
        print("  VERDICT: party-order landed every time and battle-order never did. Make party "
              "order the fixed convention and delete the flip.")
    elif landed_battle and landed_party:
        print("  VERDICT: BOTH spaces land in different situations — the menu ordering is "
              "CONDITIONAL. Keep the self-correction, and find the condition (likely whether the "
              "target is the ACTIVE mon, or whether any party member has fainted).")
    elif landed_battle and not landed_party:
        print("  VERDICT: battle-order is the real convention; the fixture was the special case.")
    else:
        print("  VERDICT: no landings recorded — items are not working at all; do not tune the "
              "index space, fix execution first.")
    print()
    print("‼ The first attempt is ALWAYS party-order, so raw landing counts are biased toward it. "
          "The flip-then-landed number is the unbiased signal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
