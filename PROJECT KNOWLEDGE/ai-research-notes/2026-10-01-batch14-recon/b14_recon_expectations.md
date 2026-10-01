# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): recon angle `expectations`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `step14-batch-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# NOTE: v2 §Step 14's pre-registered expectations, checked against today's instruments

Both checkouts are on `28db1cf0`. I wrote nothing to either checkout: the probes ran with `PYTHONDONTWRITEBYTECODE=1 -B`, and the scratch scripts live only in the scratchpad.

## A. Baselines the spec flags, re-derived from the batch0927 logs

The batch0927 logs are in the main checkout under `endless-P*/debug-logs/Old/`. I took the 35 logs stamped 20260927 from 081746 onward, which is the FINAL report's rule.

**Item uses: 96 is the true total, and "67" is the wrong number.**
- **VERIFIED.** There are 96 `[ITEM] using` lines in 68 battles. Both my scratch parser and the rebuilt `probe_item_index_space.py` agree on this. The probe printed `using: 96, consumed: 94, cure_worked: 2` and `UNCLASSIFIED 37,478 battles, 68 item btl, 96 requests`.
- **VERIFIED.** 0 of the 35 logs carry `[TRAINER]` lines, so the instruments cannot classify any batch0927 battle as key or ordinary.
- **INFERRED** (from foe rosters and maps), key battles: 26 uses in 19 battles.
  - rival ×3 (6 uses), Maxie ×4 (4), Tabitha ×3 (3), Archie ×3 (3), Winona ×2 (2)
  - Phoebe ×1 (4), Norman ×1 (2 Full Heals), Wally ×1 (1)
  - one lost Mauville-gym battle against a Voltorb L20 (1), which I took to be Wattson
  - Wally counts as key because he is class 0x32, per `trainer_identity.py:60`.
- This matches the spec's "26 in 19 key" exactly. Ordinary battles therefore hold **70 uses in 49 battles**, not 67 in 47.
  - §5's "67 of 96" should read **70 of 96 (72.9%)**. Its "about 70%" still holds.
  - If the Voltorb battle was a gym trainer rather than Wattson, the split becomes 25/18 key and 71/50 ordinary.
- **INFERRED.** 30 of the 70 ordinary uses were in Victory Road, in 14 battles, and all 14 were won. 7 lost battles had item uses (13 uses); 6 of them were key battles.
- I could not find where 67/47 came from.

**Leg-11 money refusals: the spec's figures re-derived.**
- **batch0927: VERIFIED 1 of 11.** P1 `…102251` is the only refusal (5 derail lines in one run). 12 logs loaded `EVER GRANDE CITY(16,10)`, and 11 of those are ended runs (P3r8 was still in progress).
- **batch0926: VERIFIED 12 of 15** lobby-loading runs (stamps 0926-114733 to 0927-030532).
- The two batches print **different refusal text**, which any tool spanning both must handle:
  - batch0926: `Ch23 leg 11: the basket costs ₽54,300 but we hold …`. This text no longer exists anywhere in the code.
  - today, and batch0927: `Ch23 leg 11: the missing basket lines … short by` (`victory_road.py:3522-3525`).
- Both arrive wrapped in `[STORY] DERAIL #n: Ch23 (Victory Road) failed after 3 attempts. attempt 1: BotModeError: …`.
- I did not re-derive "12 of 34"; that needs the console end classes.

## B. Measurability table

Every emitter below was found by grep in the current code.

| # | Expectation | Log line (emitter) | Tool and command today | Status |
|---|---|---|---|---|
| E1 | B has 0 `[ITEM] using` in non-key battles | `[BATTLE] [ITEM] using X on Y a/b (use N, worst hit H)` (`story_mode.py:1232`, the only emitter; doubles reach it too via `_dbl_act`, `:6497`). Battle class comes from `[TRAINER] start` (`trainer_identity.py:260-263`, always on per `story_mode.py:6629-6672`) | `probe_item_index_space.py --since D1 --until D2 --lanes <B lanes>`: the `requests` column of the PER BATTLE CLASS table, NON-KEY and UNCLASSIFIED rows (`probe_item_index_space.py:97`) | **MEASURABLE.** WILD is 0 in both arms by construction (`story_mode.py:874-875`), so it does not discriminate. The gate fails open (`story_mode.py:6450-6451`; `trainer_identity.py:77-81` allows on unreadable or no opponent), and the probe cannot attribute a non-key `using` line to a fail-open, because it never tallies `allow=`/`reason=` |
| E2 | B has more `heal_stock` at key-battle start | `[TRAINER] start … heal_stock=` (`trainer_identity.py:199-204,262`) | same probe, "HP ITEMS HELD AT KEY-BATTLE START" (`:293-296`); n, mean, median per group, one run per arm | **MEASURABLE, with caveats.** It counts per attempt, so looping runs dominate. It counts HP items only. It reads the raw bag, while in-battle use goes through the RULING 18 reserve filter (`story_mode.py:1107-1115`), so it over-counts usable stock in the Juan era |
| E3 | B's key win rate is not lower than A's, per key class | `[BATTLE] ended (outcome=…)` (`debug_logger.py:535`) plus `[TRAINER]` class ids | `probe_boss_healing.py` (`:257-265`) or `probe_item_index_space.py` (`:285-292`), once per arm with `--lanes` | **MEASURABLE per arm, but nothing does the comparison.** There is no interval or tolerance for "not lower". The Elite Four group is underpowered: batch0927 had 1 Elite Four entry in 35 runs (FINAL :466/:473) |
| E4 | Ordinary-battle whiteouts | Lost or Draw outcomes per class; `[STORY] WHITEOUT recovery #n at (g, n)` (`story_mode.py:4718-4720`) | `probe_boss_healing.py`, "DOES THE BOT LOSE THOSE FIGHTS?" (`:247-255`): NON-KEY and WILD rows. `analyze_endless_batch.py` gives totals only | **PARTLY MEASURABLE.** Three gaps: (1) B's catch flags raise WILD losses by design, and no tool splits catch battles from other wild battles; (2) no per-map view (the Victory Road risk); (3) recovery lines can carry the wrong map (FINAL :307). There is no class baseline in batch0927 (0 `[TRAINER]` lines), so arm A is the only baseline |
| E5 | B has fewer `[DEXFENCE]` reserve refusals | `[DEXFENCE] skip #dex Name — only N spare balls — below the dex reserve of 10` (`story_mode.py:2143`) and `… no spare Poké Balls (the last ball is reserved)` (`counter_hunt.py:478`, via `story_mode.py:2068`). Emitted at `:2790` | none (the FINAL used scratch scripts) | **NEEDS A NEW TOOL** for the line counts. **Frequency is NOT MEASURABLE:** each (species, reason) pair is logged once per run (`:1782-1790`), and the reason text contains the spare-ball count. B's restock moves that count around, which can create *more* distinct lines even when there are fewer refusals |
| E6 | B has no more leg-11 money refusals | derail wrapping `victory_road.py:3522`; denominator `[MAP] … -> EVER GRANDE CITY(16,10)` | `analyze_endless_batch.py` lists the top 18 derails (`:274`) with a 110-character signature (`:107`); by character count (INFERRED) all refusals collapse into one signature | **PARTLY MEASURABLE.** It has no `--lanes` (`:392-394`), and its log root is fixed relative to its own repo (`:35-36`): run from the worktree it reads nothing (the worktree has no `endless-P*`), so it must run from the main checkout. A ~10-line grep script measures this cleanly |
| E7 | `[BALLS-BUY] why=topoff` by ball, ₽ spent | top-off lines are written as `[BALLS] [BALLS-BUY] why=topoff … ball= bought= … money=a->b` (`stock_topoff.py:183,336-342`); mandatory buys as `[BALLS-BUY] why=mandatory …` (`early_game.py:2730-2736`); also `[KIT-BUY]` (`stock_topoff.py:289`) | none | **NEEDS A NEW TOOL** (small). It must match the substring, not a line-start pattern, because of the two prefixes |
| E8 | T1 income per map | `[TRAINER] end … res= money=a->b delta= mult= … map=g,n` (`trainer_identity.py:274-277`); `[MONEY] after X at map (g, n): money=₽` (`story_mode.py:2538-2539`) | none (`probe_money_telemetry.py` is an emulator gate) | **NEEDS A NEW TOOL** (small) |
| E9 | Refusals of WANTED species, by gate | Every logged `[DEXFENCE] skip` is for an unowned species, since "already owned" and trainer battles are never logged (`:1788-1789`). That matches the design's telemetry definition of "wanted" (unowned species). B adds a `rare=… tier=…` suffix (`:1965-1976`) | none | **NEEDS A NEW TOOL** (same parser as E5). It gives distinct-pair counts, not frequencies |
| E10 | Catch battles and whiteouts per rare species | `[CATCH] start kind= sp=Name#dex …[ rare= tier=]` (`story_mode.py:6713-6717`); `[CATCH] end … end=lost\|caught\|bail…` (`:6793-6796`) | none (`grade_r20_telemetry.py` checks one log's line honesty) | **NEEDS A NEW TOOL.** Arm A has no `rare=` suffix (`:1971-1972`), so it needs an offline species join to `modules/rarity.py`. The ULTRA "variant" tier is NOT MEASURABLE in A, because the line carries no PID or gender |
| E11 | `[KEYBATTLE]` agrees with the offline class | `[KEYBATTLE] opp= class= key= allow= reason=` (`story_mode.py:6462`) | `probe_item_index_space.py`, the disagreement count (`:172-180, 323-329`) | **MEASURABLE.** I confirmed it flags the forced-ordinary fault arm (ALLORDINARY): it reported 3 disagreements on the 09-29 step-6 logs. But: both sides use the same reader (`trainer_identity.py:217-226` vs `story_mode.py:6445-6449`), so agreement tests timing and plumbing only, never the classification itself. `key=?` lines are only tallied, never compared (`:176-177`). Key battles with no `[KEYBATTLE]` line at all are not reported |
| — | M1b damage-calculator audit (`POKEBOT_R25_DMGAUDIT`), both arms | `[DMGAUDIT]` (`dmgaudit.py:37`) | `audit_damage_calc.py` takes one log (`:1054`); its 300-sample threshold needs pooling across logs | **NEEDS** a multi-log pooling wrapper |
| — | Weaken frequency (`POKEBOT_R25_WEAKEN=observe`) | `[WEAKEN] [WEAKEN-OBS] would=…` (`story_mode.py:7004`, written by `:6814-6819`) | none | **NEEDS A NEW TOOL** |

## C. Risks to the instruments themselves

1. **Arm selection.**
   - `scan_logs` windows are whole days (`battle_log.py:748-750`). VERIFIED: the 20260927 day mixes batch0926's tail (00:23–03:05) with batch0927.
   - Splitting arms by lane needs `--since/--until` (`:810-811`).
   - No tool reads the `env-all:` header every log carries (`debug_logger.py:262-266`), which could check each log's flags against its arm.
2. **Log size cap.** Each log is capped at 30 MB, after which ordinary events are dropped (`debug_logger.py:44,463-468`).
   - INFERRED: DMGAUDIT adds about 594 bytes per line at about 2.2 lines per `[TURN]` line (measured on a 2026-09-30 repro log). The largest batch0927 log (4.9 MB, 7,384 `[TURN]` lines) would grow to about 14 MB, which is under the cap.
   - The `battle_log` probes never check for the cap marker, so a capped run would be undercounted silently.
3. **Starter confound (INFERRED).** The lanes are `endless-P1-torchic`, `P2-mudkip`, `P3-treecko`, `P4-random`, so a 2+2 per-lane split puts different starters in each arm. Avoiding that needs per-run alternation, which is a sandbox change, not a tool.
4. **Doubles.** `[TURN]` describes only the left foe (`battle_log.py:51`). The Space Center multi battle is out of scope for double items, so B can use no items in that Magma/Aqua battle.

## D. Missing tools, smallest first

1. A cap-marker control in the `battle_log` readers (about 5 lines).
2. `--lanes` and `--profiles` for `analyze_endless_batch.py`, reusing `battle_log.scan_logs` (about 10 lines).
3. In `probe_item_index_space.py`, tally `[KEYBATTLE]` `allow=`/`reason=` per offline class, list key battles that lack a `[KEYBATTLE]` line, and attach each non-key `using` line to its battle's verdict (about 20 lines).
4. Arm control from the `env-all:` header (`--arm-env`), refusing mixed logs. This also fixes the whole-day window problem (about 30 lines).
5. A leg-11 counter: logs that loaded `(16,10)` against logs with a money-refusal derail. It should match both refusal texts, per lane (about 30 lines).
6. A `[DEXFENCE]` reason tally with numbers stripped, labelled as distinct pairs and not frequency. It covers E5 and E9 (about 40 lines).
7. An economy tool: `[BALLS-BUY]` (both prefixes), `[KIT-BUY]`, T1 `delta` per map, and `[MONEY]` (about 60–80 lines).
8. Rare-species `[CATCH]` telemetry with an offline rarity join, reusing `grade_r20_telemetry`'s parser (about 60 lines).
9. A `[WEAKEN-OBS]` counter and an M1b pooling wrapper (about 30 + 40 lines).
10. A `battle_log` extension that routes `[CATCH]` and map lines, so wild losses split into catch battles and others, and losses can be tabulated per map (about 60 lines plus gate rows).
11. A two-arm comparator: per-group side by side, first-attempt and per-attempt, with Wilson intervals and a pre-registered tolerance (about 80 lines).
12. Medium effort:
    - an independent class check, `opp` id → class from the decomp `trainers.h`
    - a usable heal stock, which needs the reserve applied offline (stage-dependent)
    - reserve-refusal *frequency*, which needs either a per-encounter production line (sandbox) or a fragile reconstruction from `[TURN]`/`[DEX]`/`[BALLS]`.

Scratch scripts (read-only): `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\s14\uses0927.py` and `leg11.py`.
