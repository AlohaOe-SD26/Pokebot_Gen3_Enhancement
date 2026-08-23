"""§Ch21 UNBLOCK — MEASURE the three decisions the "free one party slot" plan depends on.

‼ WHY THIS EXISTS BEFORE THE CODE DOES. The plan is to stop `ensure_hm_learner` raising on a full
party and instead free exactly one slot, so a Dive learner can be caught. That means touching the
DEPOSIT path — and this project has a measured-harmful history there (`POKEBOT_PC_ROTATION` fires on
every heal, deposits up to 2 mons down to a floor of 3, and cost team-level-at-Feather 5.65 -> 4.45
and Balance->Feather 83% -> 52% across five batches; the 2026-08-02 wiring incident took finishes to
2/37). KI-54 records all of it.

So the three load-bearing claims get MEASURED against the live save rather than argued from code:

  1. **`ensure_hm_learner` really is the blocker** — `hm_learner_slot(HM08)` is None and the party is
     full, so it raises before ever looking for a hunting ground.
  2. **The victim chooser picks the right mon.** It must pick a genuine passenger and must SPARE
     Zigzagoon L15 — our ONLY Surf carrier, and Surf is how the bot reaches the Shoal Cave. Choosing
     Zigzagoon would trade one blocker for a worse one.
  3. **What the hunting-ground lookup returns TODAY**, so the value of adding a Shoal Cave row is a
     measured delta rather than a guess. (`_hm_hunting_grounds` reads `TRAINING_GRASS` only.)

‼ It also prints the BOX, because the whole plan assumes a deposit has somewhere to go.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_slot_free_plan.py
      PYTHONUTF8=1 py -3.12 probe_slot_free_plan.py --anchor post_dive.ss1
"""

import argparse
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None, is_test_run=True)  # ‼ is_test_run: without it the
    # emulator registers an atexit that OVERWRITES shared `profiles/<name>/current_state.ss1`
    # and writes a states/ snapshot. Pass 2 fixed this for the two KI-76 probes; PASS 4
    # (2026-08-22) found SEVEN MORE still writing — `profiles/repro-ml/states/` had reached
    # 2,820 files / 160 MB. A probe that mutates shared state is not observe-only.
context.audio = False
context.video = False

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_dive.ss1")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.items import get_item_bag, get_item_by_name
from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.story import team_policy
from modules.story.early_game import _hm_hunting_grounds, hm_learner_slot

BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


avatar = get_player_avatar()
print(f"anchor: {args.anchor}")
print(f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)")

party = get_party()
print(f"\nparty ({len([m for m in party if m is not None])}/6):")
for index, mon in enumerate(party):
    if mon is None:
        continue
    moves = ", ".join(m.move.name for m in mon.moves if m is not None)
    print(f"  {index}  {mon.species.name:<11} L{mon.level:<3} {mon.current_hp}/{mon.total_hp:<4} {moves}")

# ---------------------------------------------------------------------------------------------
head("1 — IS `ensure_hm_learner` REALLY THE BLOCKER?")

hm08 = get_item_by_name("HM08")
in_bag = get_item_bag().quantity_of(hm08)
slot = hm_learner_slot(hm08)
party_size = len([m for m in party if m is not None])
print(f"  HM08 in bag              : {in_bag}")
print(f"  hm_learner_slot(HM08)    : {slot}   (None = nobody in the party can learn it)")
print(f"  party size               : {party_size}/6")
blocked = slot is None and party_size >= 6
print(f"\n  [{'AS PREDICTED' if blocked else '‼ NOT BLOCKED'}] the full-party raise is what stops us: {blocked}")
print("  ‼ Note the ORDER: the raise happens BEFORE any hunting-ground lookup, so adding a ground")
print("    without freeing a slot changes nothing at all.")

# ---------------------------------------------------------------------------------------------
head("2 — WHICH MON WOULD BE DEPOSITED, and is our only Surf carrier spared?")

views = team_policy.view_from_party(party)
# ‼ `find_dead_weight` returns [(index, reason)] — TUPLES, not bare indices. The first draft of
# this probe treated them as ints and died with `list indices must be integers, not tuple`. Worth
# the comment: reading the return SHAPE rather than assuming it is the cheapest bug in this file.
worst = team_policy.find_dead_weight(views)
print("  find_dead_weight (worst level gap first):")
if not worst:
    print("    (none — nothing is considered a passenger)")
for index, reason in worst:
    name = party[index].species.name if party[index] is not None else "?"
    print(f"    slot {index}  {name:<11} {reason}")

# ‼ AND SHOW THE EXEMPTION WORKING, not just its outcome. `dead_weight` returns None for the sole
# carrier of any HM *before* any heuristic runs, which is the line that protects our Surf carrier.
print("\n  sole-HM-carrier exemption (the rule that outranks every heuristic):")
for index in range(len(views)):
    sole = team_policy._only_hm_carrier(views, index)
    if sole:
        name = party[index].species.name if party[index] is not None else "?"
        print(f"    slot {index}  {name:<11} EXEMPT — sole carrier of {sorted(sole)}")

surf_carriers = [
    index for index, mon in enumerate(party)
    if mon is not None and any(m is not None and m.move.name == "Surf" for m in mon.moves)
]
print(f"\n  Surf carriers in the party: {surf_carriers} "
      f"({[party[i].species.name for i in surf_carriers]})")

victim = worst[0][0] if worst else None
victim_name = party[victim].species.name if victim is not None else None
print(f"  ONE-SHOT victim would be  : slot {victim} ({victim_name})")

spared_ok = victim is not None and victim not in surf_carriers
print(f"\n  [{'AS PREDICTED' if spared_ok else '‼ DANGER'}] the deposit does NOT take a Surf carrier: {spared_ok}")
if not spared_ok:
    print("  ‼‼ STOP. Depositing our only Surf carrier trades one blocker for a worse one — Surf is")
    print("     how the bot REACHES the Shoal Cave in the first place.")

# ‼ THE SECOND-ORDER CHECK. A caught Spheal arrives at L26-32 against an L48 lead, so it may be
# 'dead weight' by the level rule the MOMENT it joins. If so, any later rotation would evict the
# very Pokémon the whole plan exists to acquire.
print("\n  second-order: would a freshly caught L28 Spheal itself be dead weight?")
levels = [m.level for m in party if m is not None]
print(f"    party levels {sorted(levels, reverse=True)}; best = {max(levels)}")
print(f"    a L28 catch is {max(levels) - 28} levels behind the best — compare team_policy's")
print("    dead-weight level rule. If it qualifies, the catch is safe ONLY while rotation is off.")

# ---------------------------------------------------------------------------------------------
head("3 — WHAT DOES THE HUNTING-GROUND LOOKUP RETURN TODAY?")

grounds = _hm_hunting_grounds(hm08)
if not grounds:
    print("  (none) — `TRAINING_GRASS` has no ground hosting a Dive learner.")
for row in grounds:
    print(f"  {row}")
print(f"\n  grounds today: {len(grounds)}")
print("  ‼ This is the MEASURED baseline. Adding a Shoal Cave row is only worth it as a delta")
print("    against this — and a row is worthless until the slot is freed (see section 1).")

# ---------------------------------------------------------------------------------------------
head("4 — IS THERE ANYWHERE TO DEPOSIT TO?")

try:
    from modules.story.pc_trip import box_views

    # ‼ `box_views()` RETURNS A 2-TUPLE `(views, mons)` — parallel lists, not a list of views.
    # The first version of this probe did `len(box_views())` and therefore printed "box
    # occupants: 2" **for an empty box, always**, because it was measuring the tuple. That wrong
    # number reached a commit message before an audit caught it. Unpack it.
    # ‼ And note the honest-failure contract: `box_views` returns `([], [])` on ANY read failure,
    # so "empty" and "unreadable" look identical from here — which is why the count is printed
    # with that caveat rather than asserted.
    views_in_box, mons_in_box = box_views()
    print(f"  box occupants: {len(mons_in_box)}")
    for view in views_in_box[:8]:
        print(f"    {view}")
    if not mons_in_box:
        print("    (empty — or unreadable; `box_views` cannot distinguish the two)")
except Exception as error:  # noqa: BLE001 - an unreadable box is reported, not assumed empty
    print(f"  <could not read the box: {type(error).__name__}: {error}>")
print("\n  (An empty box is FINE for a DEPOSIT — it only mattered for the withdraw direction,")
print("   which this plan deliberately avoids: `ensure_hm_learner` tests the PARTY, so routing")
print("   the catch through the box would need a stop-condition rewrite as well.)")

head("VERDICT")
print(f"  blocker confirmed         : {blocked}")
print(f"  victim                    : slot {victim} ({victim_name})")
print(f"  Surf carrier spared       : {spared_ok}")
print(f"  hunting grounds today     : {len(grounds)}")
print("\n‼ NOT ANSWERED HERE, and must not be assumed:")
print("  * whether freeing a slot is genuinely ONE-SHOT rather than per-heal (that is a control-flow")
print("    question about `ensure_hm_learner`'s callers, not a state question);")
print("  * whether the Shoal Cave tile is reachable and productive — that needs a LIVE two-way sweep,")
print("    not a static path (the Route 114 lesson).")

# ‼ THE EXIT CODE — added 2026-08-22, deep sanity check PASS 4 (INFRASTRUCTURE).
# This file sat in the STANDING GATE SUITE with **zero assertions and no exit call**: an agent
# monkeypatched `team_policy.find_dead_weight` to return our ONLY Surf carrier, the probe printed
# `[‼ DANGER] the deposit does NOT take a Surf carrier: False` and `‼‼ STOP.` — and still exited 0,
# so `run_gates.py` reported PASS over it. That is the same defect pass 3 found in
# `repro_whiteout_abort.py`, and three probes in this suite had it at once.
#
# ⛔ IT GATES ON `spared_ok` ONLY, DELIBERATELY. That is the invariant with a PROVEN RED ARM — the
# injection above flips it to False. `blocked` is also True today, but nothing has ever demonstrated
# its failing arm, and this project's rule is that an unproven arm is a CLAIM, not a guard: gating
# on it would be asserting something I have not shown can fail.
#   baseline MEASURED before wiring this up: blocked=True, spared_ok=True, victim=slot 3 (Skitty).
raise SystemExit(0 if spared_ok else 1)
