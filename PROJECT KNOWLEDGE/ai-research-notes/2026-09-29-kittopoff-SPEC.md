# 2026-09-29 — design v2 step 10 (HK, the healing-kit top-off): the SPEC as it will be built, after a five-angle recon

> A NOTE refining `2026-09-29-r23-27-DESIGN-v2.md` step 10. It supersedes that step's body where they differ. A
> five-angle recon (code audit, decomp, battle policy, fixtures, adversarial) came first. Its output is a note, and
> every load-bearing fact below was re-read by the author at the cited place (marked ✔).
> Branch `wt/kittopoff`, cut from `main` `8c6d0da0`.
>
> ⚠ **AS BUILT for 10a (2026-09-29), superseding D7-D9 below where they differ** (the review; results in
> `2026-09-29-kittopoff10a-GRADED.md`):
> - **D8's line form was NOT built.** The line is `[KIT-BUY] why=<tag> mart=… kit=[(name, qty), …] bought={name:
>   delta} money=a->b [wants=[…]] reason=…`, with no `hp=`/`status=`. The tags add `kit-recovery`. The predictions
>   pinned this form byte for byte before the code commit. ⛔ **A 10b grader must be written from THIS form, not from
>   D8's.**
> - **A kit-only visit with the balls `1` still logs `[BALLS-BUY] why=topoff-none`** (the ball plan is empty) and
>   then walks for the kit. In 9a, `topoff-none` also meant "no walk"; it no longer does.
> - **D7/D9:**
>   - Each set is verified against its PLANNED lines, so a line the live list drops is a shortfall of its own set.
>   - Each set is LOGGED by its own verdict: the set that bought in full keeps its success line.
>   - A kit-only "sells none" is a walk failure and blocks both keys (unreachable at Rustboro, where the live list is
>     the static list).
> - **The kit is planned in its own try:** a raise in a kit-only read blocks only `<city>:kit`, and the balls stay
>   9a's. This keeps D6's "observe buys exactly the kit-OFF purchase" true under a fault.

## WHY THE v2 BODY CANNOT BE BUILT AS WRITTEN (the recon's two blockers)

1. **The step 9 errand cannot carry non-ball lines.**
   - The heal enters the errand only for the ball flag (`higher_level_actions.py:789`).
   - Verification assumes one ball: `ball = lines[0][0]` and `report["ok"] = report["bought"] == planned`
     (`stock_topoff.py:388-394`).
   - Kit lines appended to `lines` would read "short" on every visit, memoise the city, and silently switch off the
     graded 9a top-off.
   - At Sootopolis the early return and `ball_only` know only balls (`league_reserve.py:320`, `:413`).
2. **The Rustboro arm had no discriminator.**
   - Nothing recorded the Items pocket at the heal.
   - As built (balls fill first, the kit shares what is left) the kit gets ₽70 at Rustboro and ₽383 at Sootopolis, so
     an ON arm would buy nothing and be vacuous.

## VERIFIED FACTS (✔ = re-read by the author)

- ✔ **Rustboro sells no status cure.** Its basic and expanded lists both hold Poké Ball, **Potion**, **Super Potion**,
  Antidote, Parlyz Heal, Escape Rope, Repel and X items; the expanded list adds Timer and Repeat Balls
  (`data/maps/RustboroCity_Mart/scripts.inc:20-31, :40-53`; the flag `FLAG_MET_DEVON_EMPLOYEE` at `:9-10`). There is
  no Full Heal, Awakening or Ice Heal.
- ✔ **Sootopolis sells:** Ultra Ball, **Hyper Potion**, **Max Potion**, **Full Heal**, Revive, Max Repel, X Attack,
  X Defend and Shadow Mail (`SootopolisCity_Mart/scripts.inc:16-24`).
- ✔ **Prices and parameters** (`modules/data/items.json`):

  | Item | Price | HP |
  |---|---|---|
  | Potion | ₽300 | 20 |
  | Super Potion | ₽700 | 50 |
  | Hyper Potion | ₽1,200 | 200 |
  | Max Potion | ₽2,500 | 255 = full |
  | Full Heal | ₽600 | – |
  | Awakening | ₽250 | – |
  | Ice Heal | ₽250 | – |

- ✔ **The battle policy** (`modules/story/battle_items.py`):
  - it heals at ≤ 35% HP (`:43`), at most 4 item uses per battle (`:49`);
  - it cures only Sleep and Freeze, with the specific cure tried first (`:155-157`: Awakening or Ice Heal, then Full
    Heal, Lava Cookie, Full Restore);
  - the in-battle Revive is off (KI-100).
- ✔ **Items are used only in key battles when `POKEBOT_R27_KEYITEMS=1`** (`story_mode.py:812-817`); without it,
  every trainer battle may spend them.
- ✔ **RULING 26** (06:8072): *"maintaining its healing items and ball stock through out the game, focusing more
  hevily on ball stock post elite 4"*. RULING 23 (06:8062): bounded batches, the best ball, no per-run ceiling.

## THE SPEC (D1-D12; each is also a `06` decision)

- **D1, the flag.** `POKEBOT_R26_KITTOPOFF` ∈ {unset/`0`, `observe`, `1`}.
  - It is parsed by its own function, whose typo message names THIS flag (the recon's NIT 12; 9a's `parse_flag` is
    kept byte-identical).
  - Consumer (a) reads it before the heal's first yield, next to the ball flag (a third stated exception, like
    `[A-N6]`).
- **D2, the key-item coupling, enforced in code** (recon finding 8).
  - Kit `1` without `POKEBOT_R27_KEYITEMS=1` is a named SKIP: one `[KIT-BUY] why=kit-skip` line, nothing bought.
    Otherwise ordinary trainers drain the kit and force re-buys.
  - `observe` still logs its plan.
- **D3, the kit's contents.**
  - **HP line:** the best tier on the ladder **Potion < Super Potion < Hyper Potion** that the Mart sells, topped up to
    4 (`MAX_ITEM_USES_PER_BATTLE`, imported).
    - "Held" counts that tier AND every higher tier on the ladder, so 5 Hyper Potions at Rustboro buy no Super
      Potions.
    - ⭐ **Max Potion is EXCLUDED** (an interpretation stated to the user, reversible; the `#24-provisions` ladder,
      03:3556-3559, also omits it). It costs 2.1× a Hyper Potion for at most 55 more HP. The policy even spends it
      first on any Pokémon under 200 max HP (the battle angle, computed). Full Restore is League-only.
  - **Status line:**
    - Full Heal topped up to 2 where sold;
    - otherwise Awakening topped up to 1 where sold, AND Ice Heal topped up to 1 where sold;
    - a held Full Heal counts toward each specific line;
    - Antidote, Parlyz Heal, Burn Heal and Revive are never bought.
  - **Order inside the kit:** the HP line, then the status line.
  - **No line has a quantity ≤ 0** (recon finding 10). `buy_in_shop`'s quantity dial cannot reach 0.
- **D4, "held" is counted on top of the League reserve.** It is the raw bag (`league_reserve._stock_by_name`, which
  sums stacks) minus `reserved_quantities()`.
  - That is stage-dependent: `{}` outside the armed Juan era, so at Rustboro nothing is subtracted.
  - At Sootopolis, 8 Full Heals and 30 Hyper Potions held as the basket count as 0 held for the kit (recon finding 6).
- **D5, one budget per visit.** B = min(₽6,000, (money − floor)//2).
  - It is computed ONCE and debited by every phase.
  - A visit still spends at most half of what is spendable (06:8394), for balls and kit together.
  - The floor is the stage floor. At PRE_GYM1 it is None, so there is no kit before gym 1, as for balls: a build gap
    against RULING 26, already named by v2 (§4, "a pre-gym-1 top-off … a build gap").
- **D6, the order when the kit is ON** (v2's order, stated as an INTERPRETATION of RULING 26's "more heavily on balls
  post Elite 4", reversible):
  1. balls up to the reserve: spare → `DEX_CATCH_BALL_RESERVE` + 1, i.e. 11 (imported);
  2. the kit's HP line;
  3. the kit's status line;
  4. the rest of the balls, to TARGET 30.
  - ⚠ **Consequences, stated to the user:**
    - at Rustboro the balls come in lines under 10 and earn no Premier;
    - at Sootopolis (spare 18) the kit takes the budget first: 1 Hyper Potion instead of step 9b's 1 Ultra.
  - **With the kit OFF (or skipped) nothing changes:** one ball phase, exactly 9a/9b. That is a regression arm here.
  - **With the kit in `observe`:** the purchase is exactly the kit-OFF purchase, and the kit plan is only logged.
- **D7, verification by bag delta PER ITEM NAME** (lines of the same name summed: 22 Poké = [10, 12]). A visit is ok only
  if every name's delta equals its planned total. The ball's own `[BALLS-BUY]` figures are unchanged.
- **D8, logging.** (⚠ The line form was NOT built as written: see the AS-BUILT note at the top.)
  - A new `[KIT-BUY] why=kit|kit-observe|kit-none|kit-skip|kit-failed|kit-closed mart=… hp=<item>+<n> status=<…>
    bought={name: delta} money=a->b reason=…` line.
  - `[BALLS-BUY]` lines are unchanged in form, and are emitted only when balls were planned or bought.
- **D9, separate memo keys**: `<city>:kit` next to `<city>` (recon finding 9).
  - A kit-only bag-delta shortfall (e.g. "no more room" in the Items pocket) blocks only the kit.
  - A WALK failure (the bound, the recovery, a raise) blocks both, because the walk itself failed.
- **D10, consumer (a).** A kit-only walk at Rustboro is allowed: it rides the same heal, under the same contract as
  the ball errand.
  - The static kit list for the go/no-go is Rustboro's `("Potion", "Super Potion")`, with no status cure.
  - The counter re-reads the live list with the menu open.
- **D11, consumer (b).**
  - The forecast covers balls and kit (the kit part is `None` when its flag is OFF, adding no key).
  - The visit walks if the basket plan OR the ball walk OR the kit walk says so.
  - "Top-off only" generalizes `ball_only`, still decided from the caller's plan before the live filter (BB9B-1).
  - The counter phase runs D6's order from the live post-basket state, on one budget.
  - A wasted top-off-only visit is memoised (BB9B-2).
  - The static Sootopolis kit list is `("Hyper Potion", "Full Heal")`; Max Potion is excluded by D3.
- **D12, the drivers grade the kit by their OWN bag reads.**
  - The earlybasket driver gains the kit items in its PRE and END reads and a `ball_grade`-style pure helper.
  - The Rustboro arm grades from the debug log's `[KIT-BUY]` line and a Step-0 read of the Items pocket.

## ARMS TO PRE-REGISTER (after the Step-0 reads; `POKEBOT_R27_KEYITEMS=1` whenever the kit is `1`)

- **Rustboro** (`r20_badge1_party1_gym.ss1`, seed 1, `storyresume --set-balls 5`; the first heal: spare 7, ₽9,940,
  budget ₽4,470):
  - **K-OFF** equals 9a's M0.
  - **K-BALL** (balls `1`, kit unset) equals 9a's B-ON: 22 Poké, 2 Premier.
  - **K-OBS** (balls `1`, kit `observe`) equals B-ON's purchase, plus one `kit-observe` line.
  - **K-ON** (both `1`) buys, by item delta: Poké +8 (4 + 4), Premier +0, Super Potion +4, at ₽9,940 → 5,540 (the same
    money as B-ON; the ITEMS differ).
  - **K-ONLY** (kit `1`, balls unset): Super Potion +4, ₽9,940 → 7,140.
  - **K-SKIP** (kit `1`, KEYITEMS unset) equals K-OFF, plus one `kit-skip` line.
  - ✔ **Items pocket at the heal: no healing items.** The first battle after the heal is the rival, `f178292 [TRAINER]
    start opp=600 … money=9940 heal_stock=- …` (`evidence/2026-09-29-t1trainer-T1.txt:62`; the same line in 9a's
    B-OFF evidence).
    - `heal_stock` lists every raw Items-pocket slot whose battle use is Healing (`trainer_identity.py:199-206`).
    - Nothing is bought at that heal in M0.
    - ⇒ 0 Potions and 0 Super Potions held, so the HP line buys 4.
- **Sootopolis** (`post_hm07.ss1`, `earlybasket`):
  - **S-ON** (both `1`): the basket; no first ball phase (spare 18 > 10); 1 Hyper Potion (₽1,583 budget); no Full
    Heal (₽383 left); no Ultra. Money ₽67,466 → 20,966.
  - **S-BALL** (balls `1`, kit unset) equals the graded A2-ON (1 Ultra).
  - **S-KITONLY** on `eb_after_M0a.ss1` (basket complete, balls unset, kit `1`): a top-off-only walk for 1 Hyper Potion.
  - **S-RAW** (a fault that counts the raw bag, no reserve subtraction): Full Heal 8 ≥ 2 and Hyper 30 ≥ 4, so no kit.
    This is the live proof of D4.
  - A spare-threshold pair, `--set-balls 8` against `9` (spare 10 against 11), is optional.
- **Faults** (registered in 29):
  - `POKEBOT_R26_FAULT_RAWBAG=1` (D4);
  - `POKEBOT_R26_FAULT_KITFULL=1` (buys the full kit whatever is held; a gate arm only, because it is vacuous live on
    these fixtures, where nothing is held);
  - the live floor lever `POKEBOT_R23_FAULT_FLOOR` is shared.

## WHAT THIS STEP WILL NOT DO

- A kit before gym 1 (a named gap, as for balls).
- Items in double battles (step 13).
- Whether the kit wins key battles (step 14).
- Any Mart other than Rustboro and Sootopolis.
