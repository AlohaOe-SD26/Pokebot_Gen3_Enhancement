# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `history`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 history note: what doubles cost the story bot today, and whether healing items would have helped

## Bottom line

Step 13 matters in the story for **one fight, Tate & Liza**. The Space Center multi-battle was almost never a problem. Tate & Liza is a large, measured, recurring cost. The evidence that healing items would change its outcome is weak, because the bag at Mossdeep is thin and nothing refills it between losses. The measurable outcome value of step 13 is mostly post-game (the 32 leader rematches), plus any Tate & Liza attempt made with a stocked bag. The A/B should therefore be framed as a **correctness A/B**: does the item land on the right Pokémon, judged by identity? A win-rate A/B at Tate & Liza cannot be graded on today's evidence; that is a frequency question for step 14.

## Method (what I ran; nothing was run in the emulator and no file in the worktree was written)

- **Where the logs are.** The batch debug logs are in the MAIN checkout (`C:/Remote Projects/Pokebot_Gen3_Enhancement/sandbox-pokebot/profiles/endless-P{1..4}-*/debug-logs/Old/`), not in the worktree.
- **The parser.** It is a scratch script and is not committed: `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/t13hist/parse_doubles.py` (plus `parse_doubles2.py`).
- **How a Tate & Liza battle is recognised.** Map (14,0) plus a foe in {Claydol L41, Xatu L41, Lunatone L42, Solrock L42}. That roster is from pret `src/data/trainer_parties.h:3546-3575`.
- **The counts reconcile.**
  - The loss counts match the stdout lines `lost a battle at map (14, 0)` exactly: 419, 200 and 155.
  - The battle counts match the `[STEP] … challenging Tate & Liza` lines: 473, 223 of 225 (0926), and 174.
- **How a Space Center battle is recognised.** Map (14,10) plus the Maxie/Tabitha rosters (pret `trainer_parties.h:6681-6695`, `:9822-9836`).
- **How other doubles are recognised (heuristic, INFERRED).** Two different own Pokémon decide on the same turn number within 100 frames.
- **Corpora.**
  - "0915" is the 99-run batch of 2026-09-15/16.
  - "0926" is 38 logs (34 ended runs plus 4 in progress).
  - "0927" is 35 logs (31 ended plus 4 in progress).

## 1. The story's key-class doubles are exactly two fights (VERIFIED against the decomp)

- **Key-class trainers with `doubleBattle = TRUE`.** In pret `src/data/trainers.h` there are 33 of them: `TATE_AND_LIZA_1` (`:3256-3265`, `.doubleBattle = TRUE` at `:3263`) and the 32 rematches ROXANNE_2-5 … JUAN_2-5. No Elite Four, Champion, rival, Magma or Aqua entry is a double.
- **The Space Center multi is built from two SINGLE entries.**
  - `MAXIE_MOSSDEEP` has `.doubleBattle = FALSE` at `trainers.h:8819`; `TABITHA_MOSSDEEP` has it at `:6179`.
  - `SPECIAL_BATTLE_STEVEN` forces `TRAINER|DOUBLE|TWO_OPPONENTS|MULTI|INGAME_PARTNER` (`battle_tower.c:2122-2133`).
  - The party is cut to 3 (`MossdeepCity_SpaceCenter_2F/scripts.inc:228,234`).
  - Battler 2 is Steven's partner controller (`battle_controllers.c:116-143`), so the bot decides only for battler 0.
  - Items are usable there. The block covers only LINK, FRONTIER_NO_PYRAMID, EREADER and RECORDED_LINK (`battle_main.c:4221-4232`).
- **Tate & Liza heal themselves.** They carry 4 Hyper Potions (`trainers.h:3262`), and Lunatone and Solrock each hold a Sitrus Berry (`trainer_parties.h:3565`, `:3572`).

## 2. The hole is still open in the code (VERIFIED)

- `StoryItemBattleStrategy` (`sandbox-pokebot/plugins/custom_modes/story_mode.py:739`) overrides only `decide_turn` (`:796`).
- It inherits `LevelUpTravelBattleStrategy.decide_turn_in_double_battle` (`:563-618`), which only attacks.
- The dispatcher sends every double to that method (`modules/battle_action_selection.py:198-212`).
- The design v2 note's cite `story_mode.py:518` is stale; the line is now `:563`.
- The logs confirm it: **0 `[ITEM] using` lines in any Tate & Liza, Space Center or detected double battle, in all three corpora.** Whole-batch item uses were 272 (0915), 201 (0926) and 96 (0927).

## 3. Tate & Liza, measured (VERIFIED from logs unless marked)

| | 0927 (build d21c0c3c) | 0926 (1a31c3e4) | 0915/16 |
|---|---|---|---|
| Runs reaching T&L | 19 (17 ended + P1r9, P3r8 in progress) | 25 | 59 |
| T&L battles: won / lost / draw | 16 / 155 / 3 | 22 / 200 / 1 | 53 / 419 / 1 |
| Runs that eventually won | 16 (5 on the first try; median 1 loss before winning) | 22 (3 first try; median 2.5) | 53 (17 first try; median 2) |
| Runs that never won | P1r5 27 L, P1r7 29 L, P1r9 19 L (in progress at the park) | P1r5 19 L (wedge), P2r6 25 L, P4r5 24 L | 6 runs, 26-32 L each |
| Share of all whiteouts | 155 / 769 = **20%** (769 from `batch0927-FINAL.md:79`) | 200 / 1,121 = **18%** (my sum of the FINAL's per-run table) | 419 / 2,537 = **16.5%** (`endless-batch-REVIEW.md:40`) |
| Run-ends at T&L | 2 of 31 (`batch0927-FINAL.md:90`) | 3 of 34 (`batch0926-FINAL.md:61-62`) | the review's derail family: 5 runs / 25 occurrences (`REVIEW.md:65`) |

- **How concentrated the losses are.** In 0927 the 3 never-won runs account for 75 of the 155 losses, and the top 5 runs for 119 of 155. In 0926 the top 5 runs account for 116 of 200.
- **How lopsided the losses are.** From the stdout `KO'd K of theirs first` lines:

  | Foes KO'd before losing | 0 | 1 | 2 | 3 | Close losses (3 of 4 KO'd) |
  |---|---|---|---|---|---|
  | 0927 | 30 | 83 | 28 | 14 | 9% |
  | 0926 | 38 | 91 | 57 | 14 | 7% |
  | 0915 | 86 | 189 | 103 | 41 | 10% |

  About 73% of 0927's losses KO'd at most 1 of the 4.
- **Frame cost (INFERRED proxy).** The span from the first to the last Tate & Liza battle, summed over runs, is 4.2% of 0927's battle-span frames, 4.3% of 0926's and 5.1% of 0915's. Each loss re-solves the 117-step statue puzzle (`03-PUNCH-LIST.md:3867-3873`).
- **What killed the runs (from the notes):**
  - **"Right types, too weak."** The guard grades only type coverage (`03:3874-3879`).
  - **An in-battle wedge.** A KI-36 false positive during a Shedinja stall (`batch0926-FINAL.md:62`; `FORENSICS.md:17,60`).
  - **Hard-plateau honest stops whose text is misleading.** P2r6's stop says "no super-effective answer" although Swampert used Muddy Water 22 times (`FORENSICS.md:16,58`).
  - **Xatu's sun and sleep stalls** (`batch0927-FINAL.md:325`).
  - The #24-tateliza-attrition hypotheses — (a) the team is under-powered, (b) KI-96 is incomplete in doubles — are **still undiscriminated** (`03:3879-3887`). I found no drive that separates them.
  - A simple level proxy did not separate winners from losers in my parse: the second-best level ≥ 40 vs < 40 split gave no consistent pattern.

## 4. Did the bot hold healing items at Tate & Liza?

The logs carry no bag lines, so this cannot be answered directly. The debug logs have `[ITEM] using` only; I checked the tag census of one run.

- **Proxy: items used anywhere in the run before the first Tate & Liza battle.**
  - In 0927, 15 of 19 runs used 3 or fewer.
  - The 3 never-won runs used 0, 2 (Potions) and 3 (Super Potion, Potion, Hyper Potion).
  - Item-rich runs did not fare consistently better. Runs with 10 or more items had a mean of 22 losses in 0927 (one run), 2.8 in 0926 and 11 in 0915.
- **Where item-rich runs got their items (INFERRED, unverified).** All 6 runs with 15 or more uses before Tate & Liza had a Linoone. Pickup has `sPickupItems` at pret `battle_script_commands.c:784-798`, and the `pickup: true` template is at `modules/config/templates/battle.yml:10`.
- **The builds that ran bought no healing items before Sootopolis.**
  - `#24-provisions` is still open (`03:3547`).
  - Design v2 §5 says "Before Sootopolis, every healing item is found or gifted".
  - Mossdeep Mart sells Hyper Potion, Full Heal and Revive (`MossdeepCity_Mart/scripts.inc:15-25`), but no step buys there.
  - Step 10a buys 4 Super Potions at Rustboro, and only with both flags on (`kittopoff10a-GRADED.md`, K-ON row).
  - Step 10b is at Sootopolis, which comes after Tate & Liza.
- **What that means for a losing streak (INFERRED).** The bot uses at most 4 items per battle (`modules/story/battle_items.py:49`) and heals at 35% HP or below (`:43`). A thin bag is empty after 1-2 losses, so a 19-29-loss streak cannot be fixed by items. Under `POKEBOT_R27_KEYITEMS=1`, the uses that ordinary battles now drain (67 of 96 in 0927, design v2 §5) would reach Tate & Liza instead. That is still only 0-3 items in the stuck runs.
- **The one measured case of items swinging a key battle is the Sidney run, with a stocked bag.** B1-ORD lost; B1-ON won with a Full Heal and 3 Full Restores (`r27keyitems-GRADED.md:33-35`, one trajectory).

## 5. The Space Center multi and ordinary doubles (VERIFIED counts; the doubles detector is INFERRED)

- **Space Center.**
  - 0927: 16 won, 0 lost. 0926: 22 won, 2 lost. 0915: 52 won, 4 lost.
  - Every run that reached it eventually won it.
  - None of the three final reports lists it as a run-end.
  - My double-detector flagged 0 Space Center battles, which is consistent with the bot deciding for one battler only.
- **Ordinary-trainer doubles.**
  - 0927: about 856 detected, 20 lost. 0926: 1,081 detected, 31 lost. 0915: 2,613 detected, 46 lost.
  - The top maps are Route 110, the Mauville Gym, Route 123, Route 119 and the Fortree Gym.
  - Most of the losses entered the battle already attrited; for example, 7 of 0927's 20 started with 4 of 6 fainted.
  - These are non-key classes, so RULING 27 excludes items there whatever step 13 does. With `KEYITEMS` OFF, step 13 would instead add item use to all of them, so the flags' composition changes what the A/B measures.

## 6. The 06:4427 decision ("two singles")

- **What it was.** It is `06-DECISIONS-LOG.md:4392-4454`. It covered one *emergent* Victory Road double, Cooltrainers Katelynn and Quincy, both `.doubleBattle = FALSE`. It chose "two singles" partly because singles turn items back on (`:4427-4430`).
- **It was superseded the same day.** REVERSAL #2 (`:4456-4504`) routes around the pair via (33,16), and the split is "available but not chosen" (`:4494-4496`).
- **It never touched Tate & Liza or the Space Center.** The heal entry says the doubles hole "is real and stays open" (`:4376-4378`). It did **not** remove the problem for the story's forced doubles.

## 7. What the design v2 and graded notes say about doubles (VERIFIED)

- **Design v2:**
  - `:672-680`: step 13, a spec pointer with no proof.
  - `:674` and `:898`: G-S2, all 32 rematches are doubles and pay double.
  - `:308`: step 6 does not cover doubles.
  - `:759`: the Q3 caveat.
  - `:812`: §5, rematches get no items until step 13.
- **Step 6 graded note** (`r27keyitems-GRADED.md:43-45, 53`): the gate "is inert on them, as it is on Tate & Liza and every leader rematch". The predictions say the same (`r27keyitems-PREDICTIONS.md:16-17, 45, 86`). `trainer_identity.py:73` says the list form "is for step 13".
- **Kit spec** (`kittopoff-SPEC.md:176`): doubles are out of scope.
- **The 10a and 10b graded notes do not mention doubles.**

## 8. Fixture reality and where the known hazards bite

- **The fixtures.**
  - `in_mossdeep_gym.ss1` is marked VOLATILE (`tools/story-dev/saves/FIXTURES.md5:37`).
  - `at_mossdeep_leaders.ss1` is overwritten on every PASS of `MossdeepGymMode` (the class that logs `[ch18b]`) unless `CH18B_CAPTURE=0` (`tools/story-dev/story_harness.py:3362-3365`).
  - It, `post_mossdeep_gym.ss1` and `post_space_center.ss1` are **not in FIXTURES.md5 at all** (0 grep hits).
  - The only recorded Tate & Liza drive won with `whiteouts=0` (`07-CHANGELOG.md:11814`). That drive's docstring anchors Sceptile L47 and Zigzagoon L15 (`story_harness.py:3385-3390`).
  - **INFERRED:** a fixture that never drops below 35% HP makes an item A/B vacuous. That is the same trap as the vacuous-A/B note in CLAUDE.md.
- **Rule 3 (assert identity, not position).** `_maybe_use_item` reads only `own_side.left_battler` (`story_mode.py:833`) and keys its HP tracking on `party_index` (`:838-842`), which is position, not (PID, species).
- **Rule 10 (measure a conversion's direction first).** The item target goes through `map_battle_party_index` (`battle_state.py:332-354`) at `battle_action_selection.py:1115`. In doubles, "slot 0 encodes only the LEFT battler" (`03:3881-3883`), so which battler's refilled order the item menu uses has not been measured.
- **KI-108.** The `:1115` read is fresh only when it is the first `get_battle_state()` caller in its frame (`05-KNOWN-ISSUES.md:3066-3087`). A double calls the strategy twice per turn (`battle_action_selection.py:198-212`), which adds non-first-caller exposure (INFERRED).
