# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `fixture`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 fixtures: where the observe-only index probe and the DOUBLEITEMS A/B can run

**Bottom line:**
- **No pinned fixture sits near Tate & Liza.** Everything between `post_maxie.ss1` and `post_dive_ki76.ss1` is either VOLATILE or has no manifest row at all.
- **The cheapest non-vacuous double is on a pinned save already.** It is `post_mtpyre.ss1` with `--driver storyresume`: three Route 123 two-trainer doubles, whose trajectory is already recorded in committed evidence.
- **For the Tate & Liza A/B,** copy `at_mossdeep_leaders.ss1` to a new name and pin that copy. It has three unknowns that must be read before any arm runs: the bag, the levels, and the HP.

## 1. Every fixture on the path to Tate & Liza (FIXTURES.md5, VERIFIED; on-disk md5s recomputed read-only today)

| Fixture | Manifest | md5 | What writes it |
|---|---|---|---|
| `post_mtpyre.ss1` | PINNED (:27) | 80602159694b | nothing |
| `magma_door_losing.ss1` | PINNED (:28) | 76ef84a3e70c | nothing |
| `magma_door_ki52.ss1` | PINNED (:29) | 273d19b34d96 | nothing |
| `post_maxie.ss1` | PINNED (:26) | 19399688e730 | nothing. **The nearest pinned save before the fight.** |
| `post_harbor.ss1` | VOLATILE (:35) | 32adff78b86b | `slateporttheft` |
| `post_aqua.ss1` | VOLATILE (:36) | 60588e960d13 | `aquahideout` |
| `in_mossdeep_gym.ss1` | VOLATILE (:37) | 1d38af994837 | `mossdeeptravel` on PASS unless `CH18_CAPTURE=0` (`story_harness.py:3261-3264`) |
| `at_mossdeep_leaders.ss1` | **no row** | 1d8f604694b9 | `mossdeepgym` on PASS unless `CH18B_CAPTURE=0` (`:3363-3366`); last written by commit dabb8148 on 2026-08-26 |
| `post_mossdeep_gym.ss1` | no row | e46706b5a706 | `mossdeepbadge` on PASS unless `CH18C_CAPTURE=0` (`:3472-3475`) |
| `at_steven_2f.ss1` | no row | 714ed3152123 | `spacecenter1` on PASS unless `CH19A_CAPTURE=0` (`:3762-3763`); unchanged since 4cc9e1b8 (2026-08-12) |
| `post_space_center.ss1` | no row | a9b92735822c | `spacecenter2` on PASS unless `CH19B_CAPTURE=0` (`:3907-3908`) |
| `post_dive_ki76.ss1` | PINNED (:30) | a00378595409 | nothing. It is after the fight (7 badges), so it is useless for the first battle. |

**Why `in_mossdeep_gym.ss1` is VOLATILE (VERIFIED):** `mossdeeptravel` overwrites it on every PASS (`story_harness.py:3261-3264`), and the manifest says a save any driver rewrites is a cache (`FIXTURES.md5:17-20`). Its bytes have not changed since 732aeb0b (2026-08-12); the manifest md5 matches the file on disk. `at_mossdeep_leaders.ss1` has the same property, and `verify_fixtures.py` cannot see it at all (`:218-231`, `#24-fixturecoverage`).

**How to pin one (story-drive skill, `SKILL.md:56,67`; manifest `:17-20`):**
1. Copy the file to a name nothing writes to, for example `tateliza_at_leaders.ss1` and `tateliza_gymdoor.ss1`.
2. Run `probe_anchor_inventory.py --filter tateliza`.
3. Add a PINNED row to the manifest.

Do not pin these files under their own names: the next driver PASS would turn the gate red.

## 2. The code that fights Tate & Liza (VERIFIED)

- **The fight itself:**
  - The game side is `trainerbattle_double TRAINER_TATE_AND_LIZA_1` (`data/maps/MossdeepCity_Gym/scripts.inc:52`).
  - The trainer is class LEADER, `doubleBattle = TRUE`, and carries 4 Hyper Potions (`src/data/trainers.h:3256-3266`).
  - Its team is Claydol 41, Xatu 41, Lunatone 42 and Solrock 42 (`trainer_parties.h:3546-3575`).
  - It is one trainer id, so TwoOpponents is not set. Step 6's gate reads side A only (`story_mode.py:6384-6388`), finds LEADER, and returns key.
- **Our side:**
  - `fight_the_leaders()` (`mossdeep_gym.py:363-441`) only mashes A/B. The battle belongs to the listener.
  - The chapter is `do_mossdeep_gym_chapter()` (`:519-616`), with 3 attempts. A whiteout means re-solving the 117-step puzzle (`:417-423`).
- **Strategy:**
  - Production returns `StoryItemBattleStrategy()` (`story_mode.py:4357`), and so do all three Mossdeep drivers (`story_harness.py:3183, 3308, 3408`).
  - A double calls `decide_turn_in_double_battle(state, 0)` and, for the right battler, `(state, 1)` (`battle_action_selection.py:201-212`).
  - `StoryItemBattleStrategy` (`story_mode.py:739`) overrides only `decide_turn` (`:796`). A double therefore falls through to `LevelUpTravelBattleStrategy.decide_turn_in_double_battle` at `story_mode.py:563`. **The spec's `:518` is stale.**
- **Drivers:**
  - `mossdeeptravel` (from `post_aqua`, budget 500k).
  - `mossdeepgym` (from `in_mossdeep_gym`). Measured at about 21,000 frames after the speed fix, including 6 single-battle gym trainers (`evidence/2026-08-26-mossdeep-speed-AB.txt`; the singles are at `scripts.inc:199-254`).
  - `mossdeepbadge` (from `at_mossdeep_leaders` or `in_mossdeep_gym`, budget 300k, `story_harness.py:3372-3380`).
- **How long the battle takes is UNMEASURED.** "BADGE07_GET after 754 frames" (`07-CHANGELOG.md:11817`) counts the frames of the mash loop. The driver is suspended for the whole battle (`06-DECISIONS-LOG.md:5736-5740`). An INFERRED estimate is 15–25k frames, by analogy with the Steven multi below.
- **Production fidelity:**
  - On the gym map, production skips `_prepare_for_fight`, `_lead_best_matchup` and the heal (`story_mode.py:5817-5845`).
  - `mossdeepbadge` calls the chapter directly, and its `on_battle_started` never calls `_t1_start`, so it logs no `[TRAINER] ... heal_stock=` line.
  - ⇒ Prefer `--driver storyresume` (`story_harness.py:29175`, which runs production `StoryMode`) on the gym saves. That this resumes cleanly into Segment 18 is INFERRED.

## 3. Cheaper and earlier doubles (VERIFIED in the decomp and committed evidence)

- **Route 123 two-trainer doubles.** Source: `evidence/2026-09-29-r27keyitems-M0-liveA.txt:11-24`; the map id is from `map_data.py:832`.
  - Setup: `post_mtpyre.ss1` (PINNED 80602159694b), `--driver storyresume`, seed 1, a 90,000-frame run.
  - The three doubles, all with `double=True two=True`:
    - Hex Maniac + Collector at f3148510.
    - Guitarist + Bird Keeper at f3156846.
    - Psychic + Expert at f3168023, which is **LOST**.
  - None of these classes is key. Step 6 refuses items there when `KEYITEMS=1`, which makes a composition control.
  - `heal_stock=Hyper_Potion:1`, so the bag holds one item.
  - At the first double, party slots 0, 3 and 5 are fainted. The actives should therefore be slots 1 and 2 (INFERRED). The battle order would then be [1,2,0,3,4,5], built at `party_menu.c:5895-5911`. **So the index discriminator is not vacuous from turn 1.**
  - Sceptile is at 21/117 and Swellow at 18/109, both under `HEAL_AT_FRACTION = 0.35` (`battle_items.py:43`). The singles policy's "would" column is therefore non-trivial.
  - The three doubles span 23,216 frames. How far into the run they start is not in the committed file.
  - Measured on main 7dcd69fd. It must be re-measured on HEAD first (KI-112; the two runs are one trajectory replayed, not two measurements).
- **Magma Hideout grunt double.** Source: `M0-liveB2.txt:38-41`.
  - Setup: `magma_door_losing.ss1` (PINNED 76ef84a3e70c), `--driver magmahideout`, seed 1, 120k frames.
  - The grunt pair 727+728 (TEAM_MAGMA) fight at f3261768, about 29.5k frames after the first logged battle.
  - **It is weak for the probe:** the actives are slots 0 and 1 (Mightyena 51/130 = 0.39, and an L3 Zigzagoon). The order is the identity until a faint, and HP is above the 0.35 threshold.
- **Victory Road, Katelynn + Quincy (COOLTRAINER, not key).** Source: `07-CHANGELOG.md:22966-22985`; the sight cones are at `victory_road.py:3151-3157`.
  - Setup: `post_return.ss1` (PINNED 259177d049ce), `--driver ch23exit`, `POKEBOT_CH23_FAULT_NOBYPASS=1`, budget 120k.
  - Measured: Edgar (a single), then the double at (31,17).
  - The party enters with Sceptile and Wailord at 0 HP, so the order is probably not the identity.
  - The driver already wraps its strategy in `_maybe_record`, which logs `decide_turn_in_double_battle[i]` when `POKEBOT_RECORD_TURNS` is set (`story_harness.py:15699, 16155-16158`).
- **The KI-90 seed.** `ki90_double_absent_seed.ss1` (PINNED 38673954cf2d) is already inside a Victory Road double, so it needs no travel.
  - It has never been opened (`FIXTURES.md5:66`).
  - Loading a save mid-battle should still start a strategy: the listener fires on the first BATTLE frame (`_listeners.py:84-120`). This is INFERRED.
  - Its opponent left slot is absent, so the probe covers only one foe.
- **Space Center multi, Maxie (0x35) + Tabitha (0x31), both key.** Items are usable there (`battle_main.c:4221-4225`), because INGAME_PARTNER (bit 22) is not in `FRONTIER_NO_PYRAMID` (`constants/battle.h:81,92`).
  - Fixture: `at_steven_2f.ss1`, which has no manifest row. Driver: `spacecenter2`, budget 600k. The battle measured f3823→f22352, with acceptance at about f24000 (`evidence/2026-08-17-ki66faint-RUN6-*.txt:35,94-95`).
  - Things that make it different from Tate & Liza:
    - Steven's Metang, Skarmory and Aggron sit in `gPlayerParty[3..5]` (`battle_tower.c:2969-2995`; RUN6:34).
    - Only 3 of our mons fight (`ChooseHalfPartyForBattle`, `SpaceCenter_2F/scripts.inc:228`).
    - The battle order is the fixed multi interleave (`party_menu.c:5869-5885`), and the logged orders diverge (RUN6:46).
    - We control battler 0 only; this is INFERRED from the controller-2 check at `battle_action_selection.py:210`.
  - This case is necessary for RULING 27, but it cannot stand in for Tate & Liza.
- **Route 113, Tori & Tia.** A scripted TWINS double, listed as on-path (`12-STORYMODE-DESIGN.md:421`; `Route113/scripts.inc:107`). It is reachable only from saves with no manifest row, so no pinned fixture.
- **Magma and Aqua fights:** every one has `doubleBattle=FALSE`. Their doubles arise only from two trainers spotting at once, and grunts are not a key class.
- **Leader rematches:** gated on `FLAG_SYS_GAME_CLEAR` plus `Random()%100<=30`, rolled every 20th trainer or 60th wild battle (`gym_leader_rematch.c:32-41`, `battle_setup.c:956-966`). Not a fixture path.
- **Doc claim to correct:** "Tate & Liza is the story's only double" (`03-PUNCH-LIST.md:3881`; `2026-09-07-batch-blockers-RECON.md:183`) is refuted by the evidence above. It is the only scripted double against a key class, other than the Maxie + Tabitha multi.

## 4. The party at Tate & Liza

- **Composition** of Sceptile, Zigzagoon, Swellow, Skitty, Mightyena and Castform: VERIFIED in the recorded data (`probe_dive_learner.py:45-47`, measured on `post_mossdeep_gym.ss1`).
- **Leads** Sceptile L47 and Zigzagoon L15: written on 2026-08-12 about the *earlier* capture (`story_harness.py:3386-3388`).
- **Levels just after the fight**, read from `at_steven_2f`: Sceptile L48, Zigzagoon L15, Swellow L40, Skitty L17, Mightyena L44, Castform L36. Their moves (RUN6:12,121-126):
  - Sceptile: Rock Smash, Strength, Leaf Blade, Slam.
  - Zigzagoon: Tackle, Growl, Surf, Headbutt.
  - Swellow: Peck, Wing Attack, Aerial Ace, Quick Attack.
  - Skitty: Sing, Tackle, Tail Whip, Attract.
  - Mightyena: Tackle, Taunt, Take Down, Bite.
  - Castform: Powder Snow, Weather Ball, Sunny Day, Hail.
- **For the 2026-08-26 recapture, UNVERIFIED:** levels, HP and **the bag**.
  - If the bag holds no healing items, the A/B is vacuous by construction.
  - The fix is to stock the bag the way `NORMAN_ITEMS` does (`story_harness.py:1806-1825`), with the read-back asserted as at `:29019-29028`.

## Ranked fixtures

**For the observe-only index probe:**
1. `post_mtpyre.ss1` (80602159694b), `storyresume`, 90k frames: three non-key doubles, order not the identity from turn 1.
2. `post_return.ss1` (259177d049ce), `ch23exit` with NOBYPASS, 120k frames.
3. `at_steven_2f.ss1` (714ed3152123, no manifest row), `spacecenter2`, about 25k frames: the multi case.
4. `ki90_double_absent_seed.ss1` (38673954cf2d), 0 travel frames: never opened, one foe absent.
5. `magma_door_losing.ss1` (76ef84a3e70c), `magmahideout`, 120k frames: order is the identity at turn 1.

**For the DOUBLEITEMS A/B on the key double:**
1. A copy-pin of `at_mossdeep_leaders.ss1` (1d8f604694b9): the fight only, budget 300k.
2. A copy-pin of `in_mossdeep_gym.ss1` (1d38af994837): about 21k puzzle frames plus the fight.
3. `post_maxie.ss1` (19399688e730) through four drivers, with budgets of 500k, 400k and 300k plus §Ch16–17. Run-relative frames are unmeasured.

**Every arm must set:** `CH18C_CAPTURE=0` for Mossdeep, or `CH19B_CAPTURE=0` for the Space Center, so no committed save is rewritten.

**Hazards, and where they bite:**
- **KI-108** (`05-KNOWN-ISSUES.md:3066-3085`): a probe that calls `get_battle_state()` before the KI-101 item re-map in the same frame (`battle_action_selection.py:1113-1115`) makes that re-map read a stale order. The probe must read the `battle_state` argument it is given, or raw `gBattlePartyCurrentOrder`.
- **The instrument must hook the strategy, not the driver**, which is suspended during battles (`06-DECISIONS-LOG.md:5736-5740`). It must subclass `BattleStrategy`, or the listener silently swaps in `DefaultBattleStrategy()` (`story_harness.py:16104-16113`).
- **Rule 3:** log (PID, species) for the battler at each `battler_index` beside the order. In a plain double the order puts left at position 0 and right at position 1, then the rest (`party_menu.c:5895-5908`).
- **Stale line numbers:** the spec's `story_mode.py:518` is now `:563`. `FIXTURES.md5:30,38` cite `story_harness.py:3846-3849`, but the `post_dive` capture is now at `:4449-4450`.

This is a note, not truth. Every live claim above rests on committed evidence; nothing was run.
