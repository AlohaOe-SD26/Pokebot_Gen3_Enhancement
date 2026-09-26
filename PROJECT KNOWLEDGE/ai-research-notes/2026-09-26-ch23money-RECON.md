# 2026-09-26: why organic runs reach §Ch23 leg 11 without enough money, and the re-entry defect (#26-ch23money)

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** A 6-agent Claude workflow (`ch23-money-recon`, 2026-09-26): five
> read-only recon angles (mechanics — Gemini fan-out then decomp validation; our code's money flow; log forensics of
> the live batch; the §Ch23 re-entry defect; an adversarial pass) and a synthesizer. Nothing was edited or driven.
> **VERIFIED BY ME before filing (Claude, main session):** (1) the three leg-11 refusals are in the live logs verbatim —
> `we hold ₽21,940` (P1), `₽33,492` (P2), `₽41,412` (P4), each `P*-Story_(ENDLESS_RESET)-debug-20260926-114734.log`;
> (2) P1 run 1 logs **33** `WHITEOUT recovery` events; (3) the Amulet Coin: `src/battle_util.c:3294-3296`
> (`case HOLD_EFFECT_DOUBLE_PRIZE: if (GetBattlerSide(battler) == B_SIDE_PLAYER) gBattleStruct->moneyMultiplier = 2;`
> under `ITEMEFFECT_ON_SWITCH_IN`) — ⇒ the **HOLDER** must switch in. Everything else below is the agents' and is
> UNVERIFIED unless it says otherwise; the authoritative doc is `03-PUNCH-LIST.md` `#26-ch23money`.

**Status: a NOTE, not truth.** This synthesizes five recon angles, all of them notes too:
- **M** = mechanics
- **C** = codeflow
- **F** = forensics
- **R** = reentry
- **A** = adversarial

**S** marks something the synthesizer re-read directly: the mart inventories, Mom's script, the Amulet Coin multiplier line, `victory_road.py:140,449,3750`, and the text of the rulings in `06`.

Log shorthand:
- **P1dbg** = `profiles/endless-P1-torchic/debug-logs/P1-Story_(ENDLESS_RESET)-debug-20260926-114734.log`
- **P1out** = `P1-stdout-20260926-114731.txt`

Nothing in any tree was edited.

## 1. The net

1. **This is systemic, not one bad run.** 3 of 3 organic arrivals at leg 11 today were refused:
   - P1: ₽21,940 [LOG P1dbg:30790]
   - P2: ₽33,492 [LOG P2 debug-114734:46191]
   - P4: ₽41,412 [LOG P4 debug-114734:45038]

   The sample is small. Source: F.
2. **The cause is money lost to whiteouts, not money that was never earned or was spent.**
   - Each whiteout calls `SetMoney(money/2)` [DECOMP src/overworld.c:358-366].
   - P1 run 1 whited out 33 times [LOG P1dbg:6066-21306].
   - The only purchase was 30 Poké Balls for ₽6,000 [LOG P1out:2150-2153].
   - All five angles agree.
3. **Only money earned after the last whiteout survives to leg 11.**
   - The 13 losses to Tate & Liza took the wallet to about ₽1. That holds for any starting wallet under ₽16,384.
   - Juan's 3 losses then cut the rebuilt money to one eighth.
   - [INFERENCE]; angles F and C.
4. **Victory Road pays this bot ₽13,020, not ₽35,676.** The leg-9 bypass fights only Wally plus 5 trainers [LOG P1dbg:30544,30691,30765; CODE victory_road.py:453-456].
   - This answers M's question of where the money went.
   - Angles F, C and A agree.
5. **The Amulet Coin works as described (S-checked).**
   - Mom's first talk after `FLAG_HAS_MATCH_CALL` registers her. A second talk with `FLAG_BADGE05_GET` set gives `ITEM_AMULET_COIN` [DECOMP data/scripts/players_house.inc:275-318].
   - ×2 applies only when a player-side **holder** switches in [DECOMP src/battle_util.c:3294-3296].
   - **Disagreement:** `03 #24-amuletcoin` says "any mon sent out locks the ×2". The decomp says the holder itself must enter. M and S side with the decomp.
6. **Leg 11 prices and buys the whole basket and ignores what the bag already holds** [CODE victory_road.py:449,3362,3486-3489]. Every check downstream counts bag totals by name [CODE :3497,:3638].
   - `bag_before` is recorded and never printed [CODE :3351].
   - Angles C, M and A agree.
7. **Money is never logged.** `money_gained` is computed and never read [CODE battle_handler.py:445]. Every ₽ figure below except the three leg-11 readings is a reconstruction.
8. **The re-entry defect.** The leg-5 guard at [CODE victory_road.py:3750] checks only which map the bot is on. It fires on the plateau and aims for `VR_APRON (18,42)` [CODE :140], which cannot be reached from there.
   - The result was 5 derails and 14 unreachable attempts. The punch list's "×4" undercounts [LOG P1dbg:30790-30810].
   - Angles C, F, R and A agree.
9. **Disagreement on the counterfactual "no Juan losses" for P1:**
   - F's model gives about ₽45.7k cash plus ₽15k of Nuggets, about ₽60.7k: **leg 11 passes**.
   - C gives about ₽38–39k plus ₽15k: **borderline**.
   - C used a lower bound built from partly captured prize texts. F's model runs 1.5–7% low against the three logged wallets.
   - This stays unresolved until money is logged.
10. **Marts (S-checked).** Mossdeep and Sootopolis sell Hyper Potion, Full Heal and Revive. That is ₽45,300 of the basket. Full Restore is sold only at League 1F [DECOMP data/maps/{MossdeepCity_Mart,SootopolisCity_Mart,EverGrandeCity_PokemonLeague_1F}/scripts.inc].

## 2. Why P1 held ₽21,940 (F's model, [INFERENCE])

| Step | Wallet |
|---|---|
| Before the Tate & Liza streak | ≈₽13,951 |
| After 13 halvings | ≈₽1 |
| Rebuilt by Route 131: Tate & Liza ₽8,400 [LOG P1dbg:19456], Maxie+Tabitha ₽5,120 [LOG :19671], others | ≈₽27,481 |
| After 3 losses to Juan (÷8) | ≈₽3,435 |
| + Juan ₽4,600 [LOG :21382] + Route 128 ₽560 [LOG :21500] + Victory Road ₽13,020 | **model ₽21,615 vs logged ₽21,940** |

- With no whiteouts at all, the model gives about ₽151k.
- The pinned fixture's pre-Victory-Road wallet was ₽38,893 [CODE victory_road.py:455]. The organic run had about ₽7.7–8.9k (C and A).
- **Nuggets:** one came from the Aqua Hideout [LOG P1dbg:16245]. The other two are probably from Pickup [INFERENCE; the stats.db count is lifetime, not per run].
- The rest of the bag at leg 11 is unknown.

## 3. Ranked candidate fixes for the money gap

**F0 — Add money logging (prerequisite, ₽0).**
- What to log: the wallet at every battle end, every whiteout and every chapter boundary, plus `bag_before` in the leg-11 refusal.
- `03 #24-bosstrainingeconomics` already says "FIRST DELIVERABLE IS AN INSTRUMENT".
- Risk: none.
- **Verify:** the logged wallet equals the leg-11 reading on a fixture.

**F1 — Amulet Coin (`#24-amuletcoin`, already in flight under RULING 6).**
- **₽ impact:**
  - The ledger is linear in income, so doubling all income after badge 5 roughly doubles leg-11 cash.
  - P1 ≈ ₽43.9k cash + ₽15k Nuggets ≈ ₽58.9k, which **passes with about ₽4.6k to spare**.
  - P2 ≈ ₽67k; P4 ≈ ₽83k.
  - [INFERENCE; assumes the same whiteouts and that the holder enters every paying battle.]
- **Where and when:** Littleroot 1F, two talks in one visit. The cheapest point is right after the Petalburg Gym (4 maps away) [INFERENCE].
  - This answers the punch list's "most trainers already spent" worry: only income after the last loss matters for P1.
- **Risks:**
  - It is a backtrack.
  - It takes a held-item slot, which a Pickup holder needs empty.
  - Swap-training or a laggard lead may keep the holder off the field.
  - P1's margin is thin.
- **Verify live:**
  - (a) the two-talk gift on a save with badge 5;
  - (b) an A/B on one trainer, holder leading vs benched, reading the payout;
  - (c) which slot actually enters in boss and swap battles.

**F2 — Price the deliberate boss re-losses (`#24-bosstrainingeconomics`).**
- ₽ impact: removing the Juan losses adds about ₽17–24k for P1 (disputed, see item 9). P2 still fails; P4 passes (F).
- Risk: re-losing earns XP (that counter-argument is already filed), so changing the strategy could cost levels or add derails.
- **This is the user's decision**, and it needs F0 first.

**F3 — Buy only the missing quantities.**
- ₽ impact: equals the value of basket items already in the bag. For P1 this is probably about ₽0: only 8 Potion and Super Potion uses were logged [INFERENCE, A].
- It also removes the full re-buy after §Ch24 [CODE :3599-3604].
- The end state is identical by item name, so it is not a thinner basket. No ruling covers it, so confirm with the user.
- **Verify:** seed 5 Hyper Potions into the fixture's bag, then check that leg 11 buys 25 and `ch23_chapter_done()` is True.

**F4 — Buy Hyper Potion, Full Heal and Revive at Sootopolis before the Juan attempts.**
- This follows the 2026-09-16 rationale that items survive a whiteout and money does not. Up to ₽45,300 would be shielded.
- Risk: `battle_items` would spend them in gym fights (`MAX_ITEM_USES_PER_BATTLE=4` [CODE battle_items.py:46]), so a reserve lock is needed.
- This is a new decision for the user.

**F5 — Herb swap (A's decomp claims; not checked by S).**
- A herb basket costs about ₽41,100. P1 would still be about ₽4,160 short.
- The bot cannot use herbs today: `items.json` gives them parameter 0 and Heal Powder is not in `STATUS_CURE_ITEMS` [CODE battle_items.py:85,152].
- It changes the basket's identity, so this is the user's decision.

**F6 — Extend `LEAGUE_SELLABLE`, or collect the Victory Road Full Restore and Full Heal (₽3,600).**
- Ground items are behind the user's items gate.
- Each new sellable item needs a proof that nothing downstream uses it.
- The ₽ impact is small.

## 4. The re-entry defect and its minimal fix

- **What happens:** attempt 1 refuses at (18,6). On attempt 2:
  - legs 1–4 skip, because `at_ever_grande_top()` is true at y=6 [CODE :1519-1545];
  - training skips because Wally is beaten;
  - **leg 5 fires** [CODE :3750] and calls `_navigate_riding_out(EG, VR_APRON)` [CODE :1802-1805], which raises `UnreachableDestinationError`.
- **The plateau and the south half of the city are disconnected (measured):** from (18,28), `PathFindingError` to (18,42) and to the Poké Center at (27,49) [LOG tools/story-dev/evidence/2026-09-04-ch23-leg9-EXIT.txt:14].
- **Two tempting guards are wrong:**
  - `wally_beaten()` alone: a whiteout respawns the bot at the south Poké Center with Wally beaten, and there leg 5 must still fire [DECOMP src/data/heal_locations.json:64-67].
  - A y-threshold: no layout dump proves it (R).
- **Minimal fix (R):** add `on_league_plateau()`. It returns True if the bot is on EG and `calculate_path(here → (EG, VR_APRON))` raises `PathFindingError`. Then change the guard to `... and not (wally_beaten() and on_league_plateau())`.
  - Ever Grande has no NPCs, so nothing can make the path check falsely read "no path" [CODE :3168].
- **A/B plan (not run):** log the first navigation target.
  - Fixture: `post_league_heal.ss1`.
    - A (current code) predicts (18,42) ×3.
    - B (fix) predicts the League door and the basket bought.
    - C (fix, money set to ₽21,940) predicts the leg-11 message ×3 and no movement.
  - South controls, which must still fire leg 5: `ki90_whiteout_at_evergrande.ss1` and `post_ever_grande.ss1`.
  - Update the hand-copied guard in `probe_ch23_leg_guards.py:79`.
- **What it changes for this run:** only the error message, because leg 11 refuses before it moves [CODE :3362-3383].
- **What it protects in general:**
  - retries after transient failures on the plateau;
  - a lost `_ch24_owns_run` latch [CODE story_mode.py:1873-1878].
- **Related holes (R, not fixed):**
  - The exit side of Victory Road 1F has the same guard pattern. Its target (9,15) was not measured.
  - If leg 11 raises inside League 1F, no leg fires on the retry [CODE :3773,:3780].

## 5. Load-bearing claims that still need verification

- The Amulet Coin doubling in live battles, and whether the holder actually enters in the bot's boss and swap battles.
- The ₽ projection for F1, which rests on the linear ledger [INFERENCE].
- The counterfactual disagreement in item 9.
- The bag contents at leg 11.
- `VAR_LITTLEROOT_HOUSES_STATE==4` happens only after the Hall of Fame (M; not checked by S).
- M's claim that rematches start by talking to the trainer with no PokéNav menu. This contradicts `03 #24-pokenavrematch`, so it needs a live probe before the punch list is corrected.
- The herbs being equivalent to the basket items (A).
- Where the two Pickup Nuggets came from.
- The helper names and `calculate_path` signature in R's code sketch.
- Still UNVERIFIED Gemini claims:
  - which HM each item ball needs;
  - the Fan Club and Devon gift values;
  - how Match Call phone calls interact with rematch arming.

## 6. What NOT to do (already settled)

- **No thinner basket, adaptive re-stock, attempt cap, or "fly out, re-earn, return".**
  - [06 2026-09-16 USER RULING, "DO NOT RE-RAISE THEM"]
  - [06 2026-09-05, "Not reopened"]
- **No money-earning detour and no trainer-farming leg.**
  - [06 RULING 2, 2026-09-17]
  - For §Ch23, "No re-earning" [06 RULING 14, 2026-09-26].
  - That rules out rematch farming, despite M's payout table.
- **Do not loosen or move the leg-11 gate.** It stays the single money gate [06 2026-09-26 correction]. Deferring the basket into §Ch24 is also out, because §Ch24 has no purchase path (A).
- **Do not widen `LEAGUE_SELLABLE` as a money fix.** The 2026-09-05 entry says "ask what the route skipped".
- **Do not use the Amulet Coin errand to start general item work** [06:6415; 03:405].
- **Do not change the boss-training strategy before F0 exists** [03 #24-bosstrainingeconomics].
- **Do not grind wild battles.** They pay ₽0, and Pay Day cannot be obtained [DECOMP src/battle_main.c:5012; level_up_learnsets.h].
- ⚠ **Open tension, not resolved here:** RULING 12's restock leg (`#24-restockleg`) does not cite the 2026-09-16 decline, and it has no money source [06:6967-7019]. This is for the user.