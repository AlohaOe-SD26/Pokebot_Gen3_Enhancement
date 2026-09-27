# 2026-09-26 (~22:00) — batch `#26-batch0926`: the funnel and the top derail signatures — a NOTE, not truth

> ⚠ **AI RESEARCH NOTE — NOT A SOURCE OF TRUTH.** Four read-only Claude agents over the LIVE batch's logs (the batch was
> still running; counts are a ~22:00 snapshot), the code on `main` (the build the batch runs) and the decomp. Nothing was
> driven; every mechanism below is a hypothesis until a drive reproduces it. The interim read is
> `2026-09-26-batch0926-INTERIM.md`; the final park numbers supersede this — `2026-09-26-batch0926-FINAL.md`, which reproduces this note's 27 runs exactly and corrects two of its claims (the hard-plateau split is 6 of 14 boss stops; the build header).

## THE FUNNEL (for the park report)

PARK FUNNEL for the 2026-09-26 4-lane endless batch (build 1a31c3e427ad on main; logs read ~22:00 PDT, batch still running). The analyzer reports 35 runs, but 4 of those are the 1.5 KB `*-20260926-114733.log` stubs written at batch start, so there are 31 real runs. 31 started, 27 ended, 4 still running. Per lane: P1-torchic 8 started / 7 ended (r8 running, 2 badges, Route 117); P2-mudkip 7/6 (r7 running, 2 badges, Route 114); P3-treecko 8/7 (r8 running, 1 badge, Route 116); P4-random 8/7 (r8 running, 6 badges, Mossdeep). All 27 ends print `-> derailed:`, meaning 5 derails in a row with no party-EXP progress. None ended as finished, crashed, frame-cap or 'handed to Manual'. 0 entered the Elite Four (analyzer: elite_four MEASURED 0, `§Ch24 COMPLETE` 0). BADGE FUNNEL over the 27 ended runs, from the stdout `BADGE:` lines: ≥3 badges 26, ≥4 24, ≥5 23, ≥6 17, ≥7 14, 8 badges 10. 10 runs reached §Ch23 leg 11. 8 were refused on money there. The other 2 passed and died at the §Ch24 plateau walk-off. END SIGNATURES (27): §Ch23 leg-11 money 8 | Winona 5 | Juan 4 | Tate & Liza 3 (2 honest stops + 1 battle wedge) | §Ch24 walk-off 2 | Flannery era 2 (1 honest stop + 1 Lavaridge heal loop) | Norman 1 | Route 101 after a Petalburg Woods bounce 1 | faint-chooser battle wedge 1. The Petalburg Woods signature itself (the analyzer's #1, 67 derails in 25 runs) ended 0 runs. PER RUN (lane rN: badges / furthest map / end / frames / whiteouts): P1 r1 8/victory_road/money ₽21,940/5.59M/33; r2 7/sootopolis/Juan/4.33M/62; r3 5/fortree/Winona(24 losses)/2.97M/33; r4 8/league_lobby/money ₽20,079/6.75M/36; r5 6/mossdeep/T&L in-battle wedge/4.98M/39; r6 7/sootopolis/Juan/3.93M/42; r7 3/lavaridge/Lavaridge heal loop/2.39M/15. P2 r1 8/league_lobby/money ₽33,492/8.05M/25; r2 8/league_lobby/money ₽18,332/6.17M/23; r3 2/mauville/faint-chooser wedge/1.07M/2; r4 8/league_lobby/§Ch24 walk-off/4.23M/11; r5 8/league_lobby/money ₽37,446/7.67M/27; r6 6/mossdeep/T&L(25)/3.58M/54. P3 r1 5/fortree/Winona(12)/3.73M/24; r2 5/fortree/Winona(18)/3.83M/33; r3 3/lavaridge/Flannery(12)/3.20M/16; r4 8/league_lobby/§Ch24 walk-off/6.51M/22; r5 8/victory_road/money ₽22,900/5.17M/19; r6 8/league_lobby/money ₽41,426/6.83M/18; r7 4/lavaridge(Petalburg)/Norman(12)/3.04M/22. P4 r1 8/league_lobby/money ₽41,412/8.08M/32; r2 5/lavaridge/Route101 nav/2.23M/8; r3 5/fortree/Winona(25)/3.70M/39; r4 7/sootopolis/Juan/3.77M/42; r5 6/mossdeep/T&L(24)/3.19M/37; r6 5/fortree/Winona(24)/3.92M/39; r7 7/sootopolis/Juan/5.24M/40. COMPARED WITH THE INTERIM: the note's own header says ~17:30, not 14:15. It counted 16 ended runs and every one of its classes still holds. There are 11 new ends: +3 money (P2r5, P3r5, P3r6), +1 Winona (P4r6), +2 Juan (P1r6, P4r7), +2 T&L honest stops (P2r6, P4r5), +1 T&L battle wedge (P1r5), +1 Lavaridge heal loop (P1r7), +1 Norman (P3r7). Three things the interim did not have: (a) Its whiteout correlation no longer separates the groups. The two runs that passed leg 11 had 11 and 22 whiteouts, but P3r5 (19) and P3r6 (18) were refused with FEWER whiteouts than 22. (b) 'X losses with no super-effective answer' is printed even when the code never checked the party's answers (the hard-plateau path, see root_cause). That describes about 7 of the 13 boss stops, including both T&L stops, where the party held Swampert's Muddy Water. (c) Two runs ended in a new shape: a derail raised while a battle is still active leaves no battle handler on the controller stack.

**Run-ending:** All 27 ended runs ended the same way: 5 consecutive derails with no party-EXP progress. Each one's stdout end line reads '-> derailed:'. There are 0 'stopped: handed to Manual', 0 crashed, 0 frame-cap, 0 finished. By signature: money at §Ch23 leg 11 8; Winona 5; Juan 4; Tate & Liza 3 (2 honest stops + 1 in-battle wedge); §Ch24 plateau walk-off 2; Flannery era 2 (1 honest stop + 1 Lavaridge heal loop); Norman 1; Route 101 after a Petalburg Woods bounce 1; faint-chooser battle wedge 1. The total is 27. 4 runs are still running and are not counted: P1 r8, P2 r7, P3 r8, P4 r8. The Petalburg Woods derail, the heal-walk BLOCKED derails (Lavaridge 9 runs, Petalburg City 12, Fortree 6) and the 'Teach flow … does not know Surf' derails (7 runs) are mostly non-ending. Of these, only the Lavaridge heal walk ended a run (P1r7), and only through the unreset budget. Evidence for each end: its stdout 'ENDLESS RESET: run N/infinite -> derailed:' line plus the 'derail #1..#5' lines just before it (line numbers in the evidence list).

**Mechanism:** Five mechanisms, most runs first.
(1) MONEY, 8 runs. victory_road.py:3371 raises `Ch23 leg 11: the basket costs ₽54,300 but we hold ₽N … Refusing to buy a thinner basket silently` (LEAGUE_BASKET at victory_road.py:440-445). That is derail #1. On main the §Ch23 re-entry then fires leg 5 from the plateau, which gives derails #2-#5 `Could not reach (18, 42) on EVER_GRANDE_CITY … still at (18, 6)`: the §Ch23 leg-5 re-entry defect, fixed on the branch. Wallets were ₽18,332-₽41,426. Why the wallets are that low was not re-measured here: [MONEY] telemetry is not in this build (0 `[MONEY]` lines in any of today's logs). The interim's 'whiteouts halve the wallet' explanation does not sort the runs cleanly: refused runs had 18-36 whiteouts, passed runs 11 and 22.
(2) BOSS HONEST STOPS, 13 runs (Winona 5, Juan 4, T&L 2, Flannery 1, Norman 1). _boss_plan_is_hopeless (story_mode.py:2321) returns hopeless in two ways. One is a real answer-test miss. The other is the HARD PLATEAU (story_mode.py:2366-2372: ≥12 losses and a flat KO count over 12). The hard plateau SKIPS the answer test (`for i in (battlers if not hard_plateau else ())`, story_mode.py:2393). Either way, _counter_catch_message (story_mode.py:1397) prints '<boss>: N losses with no super-effective answer … Grinding levels will not fix this.' The hard-plateau stops are marked in the stdout by the printed line 'N losses here and the KO count has not improved across the last 12'. It appears in P1r3, P2r6, P3r2, P4r3, P4r5 and P4r6, and once in P1r2 (at '17 losses'; that run's final message says 12, so which path fired there is UNVERIFIED). P1r6, P3r1, P3r3, P3r7, P4r4 and P4r7 stopped at exactly 12 losses with no plateau print, which means the answer test did run. So in roughly half the stops the 'no super-effective answer' text is not a measured claim. MEASURED counter-example, P2r6: in the Tate & Liza fights Swampert L40 used Muddy Water 22 times (Water ×2 vs Rock/Psychic), yet the stop says 'no super-effective answer to Rock/Psychic'.
(3) A DERAIL WHILE A BATTLE IS STILL ACTIVE, 2 runs (P1r5, P2r3). P1r5 (Tate & Liza, a Shedinja/Wonder Guard stall): debug_logger.py:826-838 `_progress_signature` holds only map, position, game_state, controllable, battle_active, party_exp and message. It holds no HP and no turn count. So the KI-36 in-battle fault (debug_logger.py:373-386, 60,000 frames) fired while TURN 31→38 was still taking Lunatone from 102 to 5 HP. P2r3: the faint chooser gave up (KI-47) after `alive_slots=[2, 3](party-order) -> [1, 5](menu-order) [orders DIVERGE]` on a 4-member party. In both runs, every dump after the derail shows `battle: active=True` with `controllers=['StoryEndlessResetMode.run']` (no BattleListener), and the recovery at story_mode.py:3766-3830 only presses B and waits for control. The watchdog (18k frames) and cutscene derails followed until the budget ran out. Why no battle handler re-attaches after a derail is UNVERIFIED at the code level; it is shown only by the dumps.
(4) THE DERAIL BUDGET IS NEVER RESET IN A 'RECOVERED' LOOP, 1 run (P1r7). Each of derails #1-#5 is `heal_in_pokemon_center: the walk to LavaridgeTown is BLOCKED … (28/28 @ ROUTE112) … ROUTE112_CABLE_CAR_STATION`. After each one the bot descends Jagged Pass and logs 'reached Lavaridge Town!', so the recovery WORKS. Then it logs `[MAINTAIN] ABANDONED pid=E0D46375 — ROUTE111(25, 55) unreachable` and walks back into the same block. story_mode.py:3780-3784 resets the budget only when `_progress_sig()` changes, and `_progress_sig` (story_mode.py:2049-2064) is party size, lead level and total EXP. No EXP was gained between derails, so five recoveries ended the run.
(5) NAVIGATION, 3 runs.
- §Ch24 walk-off (P2r4, P3r4): derails alternate between `(15, 39) VICTORY_ROAD_1F … still at (39, 5)` and `(27, 49) EVER_GRANDE_CITY … still at (18, 28)`, the gap 2/4 shape.
- P4r2: the log shows `ROUTE 104 -> PETALBURG WOODS` and back to ROUTE 104 (a door bounce), then `Could not reach (9, 9) on ROUTE101 … not walkable from ROUTE104`. The bot is stranded on Route 104's north half. Why it was heading to Route 101 after Norman is UNVERIFIED.

**On branch `wt/ch24organic`?** PARTLY. The running build is 1a31c3e427ad on main (run header of every debug log), and none of the branch's functions are in main's sandbox-pokebot (grep for leg5_should_fire, _plateau_walkoff_refused, gym_tm_teach and league_reserve returns nothing). So nothing from the branch was exercised by this batch.
- Money (8 runs): BUILT, NOT MEASURED. RULING 16 buys only what is missing, RULING 17 fetches the Amulet Coin after badge 5, RULING 18 buys the basket early at Sootopolis and reserves it, and the §Ch23 leg-5 re-entry fix removes the wasted derails #2-#5. Branch 07-CHANGELOG itself says 'NOT SETTLED: whether early buying leaves enough'. F0 [MONEY] logging will measure it.
- §Ch24 walk-off (2 runs): YES for the walk-off, via #26-ch24organic gap 4 (plateau walk-off refused) and gap 2 (return bridge). The R1 readiness refusal could still end such a run under a different signature.
- Winona (5 runs): PARTLY. RULING 19 #26-gymtmteach is built, but teach-then-fight was never driven. Also, 4 of the 5 Winona stops came through the hard plateau, which the teach does not change (a taught move is excluded from the credible-answer scan by design).
- Juan (4 runs): effectively NO. RULING 19 covers Juan, but its own docstring says 'nothing we own is super-effective on Kingdra, so Juan is mostly out of reach'. The honest stop itself is the user's call (the 2026-07-30 ruling). In this batch 10 of the 14 runs that reached Juan beat him.
- Tate & Liza (3 runs): NO. #24-tateliza-attrition is open, and gym_tm_teach.py:84 deliberately excludes the double battle.
- Flannery / Norman (2 honest stops): NO, because RULING 19 is scoped to Winona and Juan.
- Honest-stop message defect (story_mode.py:1397 vs :2393): NO. The branch diff does not touch it.
- Derail during an active battle (KI-36 false positive; KI-47 faint chooser): NO. The branch changes debug_logger.py only to add money=.
- Lavaridge heal loop (1 run): NO. #26-healmap-lavaridge is open and says 'a frame-cost, NOT a run-killer … IT RECOVERS'. P1r7 recovered 5 times and still died, because the budget never reset.
- Route 101 / Petalburg Woods bounce (1 run): NO. #26-destreachability is open.
- The non-ending 'Teach flow finished but Marshtomp does not know Surf' (7 runs) is KI-105, fixed on the branch. It is live now in P4 r8: `DERAIL #1: Teach flow finished but Swampert does not know Surf`.

**Candidates (a NOTE — each needs a pre-registered A/B):**
* §Ch23 leg-11 money refusal (victory_road.py:3371): 8 runs ended — P1r1, P1r4, P2r1, P2r2, P2r5, P3r5, P3r6, P4r1. Branch wt/ch24organic: RULINGS 16/17/18 + the §Ch23 leg-5 re-entry fix (`#26-ch23money`) are BUILT, not batch-measured. The re-entry fix only removes the 4 wasted derails; the refusal still ends the run unless the money fixes raise the wallet. F0 [MONEY] logging will measure it.
* Winona honest stop: 5 runs ended — P1r3, P3r1, P3r2, P4r3, P4r6. Branch: RULING 19 `#26-gymtmteach` (built; teach-then-fight never driven). 4 of the 5 were hard-plateau stops, which a taught move does not change.
* Juan honest stop: 4 runs ended — P1r2, P1r6, P4r4, P4r7. Branch: RULING 19 names Juan, but its docstring says Kingdra has no owned SE answer, so probably no effect. Changing the stop is the USER's call (2026-07-30 ruling; interim N4). 10 of the 14 runs that reached Juan beat him.
* Tate & Liza: 3 runs ended — 2 hard-plateau honest stops (P2r6, P4r5) and 1 in-battle wedge (P1r5). Nothing on the branch (`#24-tateliza-attrition` open; RULING 19 excludes doubles).
* §Ch24 plateau walk-off (VR1F (15,39) / EG (27,49)): 2 runs ended — P2r4, P3r4. Branch: `#26-ch24organic` gap 4 (walk-off guard) + gap 2 (return bridge), guarded and driven. The R1 readiness refusal may still end these runs by name.
* Derail raised while a battle is still active (no battle handler afterwards; KI-36 false positive on a Shedinja stall in P1r5, KI-47 faint-chooser with '[1, 5] menu-order' on a 4-mon party in P2r3): 2 runs ended. Not on the branch. Candidates: (a) put HP/turn in debug_logger._progress_signature (debug_logger.py:830-838); (b) make the story's derail recovery (story_mode.py:3766+) re-enter a battle handler when battle_active is True.
* Flannery era: 2 runs ended — P3r3 honest stop (12 losses, answer-test path; not addressed) and P1r7 Lavaridge-heal BLOCKED loop with ROUTE111 counter top-up ABANDONED. Not on branch; `#26-healmap-lavaridge` is open and its 'not a run-killer' claim is contradicted by P1r7, because the derail budget resets only on a party-EXP change (story_mode.py:2049-2064, 3780-3784).
* Norman honest stop: 1 run ended — P3r7 (12 losses, answer-test path). Not addressed (RULING 19 is scoped to Winona/Juan).
* Route 101 unreachable after a Petalburg Woods door bounce (stranded on Route 104's north half): 1 run ended — P4r2. `#26-destreachability` open, not on branch.
* Petalburg Woods 'Could not reach (x,y)' (analyzer's #1 signature, 67 derails in 25 runs): 0 runs ended directly (all recovered). Its only run-ending descendant is P4r2 above.
* Cross-cutting, not a run count of its own: the honest-stop text 'no super-effective answer … Grinding levels will not fix this' (story_mode.py:1397) is printed on the hard-plateau path, which skips the answer test (story_mode.py:2393). That is 6 definite (+1 ambiguous) of the 13 boss stops. P2r6 had Swampert Muddy Water. Not on branch. Worth fixing the message before anyone reads the stop counts as type walls.

<details><summary>Evidence (agent-quoted log lines)</summary>

* Analyzer (tools/story-dev/analyze_endless_batch.py --since/--until 20260926): 'ENDLESS-RESET BATCH ANALYSIS — 35 runs across 4 lanes'. 4 of these are stubs, e.g. P1-Story_(ENDLESS_RESET)-debug-20260926-114733.log (1,571 bytes, 'build: 1a31c3e427ad on branch main', no party), so 31 real runs. 'elite_four MEASURED 0', 'cleared MEASURED 0'.
* All four P*-stdout-20260926-114731.txt: 27 lines match 'ENDLESS RESET: run N/infinite -> derailed'. No other outcome kinds. Starts: P1 8, P2 7, P3 8, P4 8.
* P1-stdout L148719: 'derail #1: Ch23 (Victory Road) failed after 3 attempts. attempt 1: BotModeError: Ch23 leg 11: the basket costs ₽54,300 but we hold ₽21,940 — short by ₽32,360, and the sellable items in the bag would only raise ₽15,000 ([('Nugget', 3)])'. L148772-L148931 derails #2-#5: 'Could not reach (18, 42) on MapRSE.EVER_GRANDE_CITY … still at (18, 6)'.
* Leg-11 refusals, derail #1 of the final chain: P1-stdout L539265 ₽20,079; P2-stdout L185249 ₽33,492, L301611 ₽18,332, L629342 ₽37,446; P3-stdout L577348 ₽22,900, L775550 ₽41,426; P4-stdout L225186 ₽41,412. Code: victory_road.py:3371.
* Leg 11 passed: P3-Story_(ENDLESS_RESET)-debug-20260926-143951.log 'leg 11: ₽824 short — will sell [('Nugget', 1)] for ₽5,000'. P2 …-155401.log has no leg-11 line and reaches §Ch24 training ('Story: training the team to Lv 65 in the grass…'), so its pass is INFERRED.
* Whiteouts per run (analyzer _WHITEOUT regex on each debug log): refused runs 33, 36, 25, 23, 27, 19, 18, 32; passed runs 22 (P3 143951), 11 (P2 155401). The interim's '11 and 22 vs refused 23-36' split is broken by P3 162600 (19) and P3 174950 (18).
* Hard-plateau prints ('N losses here and the KO count has not improved across the last 12 (best a -> b)') found by joining wrapped stdout lines within each run: P1r3 Winona 7 prints (last 24, 3->3); P2r6 T&L 8 (last 25, 1->1); P3r2 Winona 5 (18, 4->3); P4r3 Winona 6 (25, 4->4); P4r5 T&L 6 (24, 3->2); P4r6 Winona 6 (24, 4->4); P1r2 Juan 1 (17, 3->2). None in P1r6, P3r1, P3r3, P3r7, P4r4, P4r7.
* P2-Story_(ENDLESS_RESET)-debug-20260926-193750.log f3577516: 'DERAIL #1: Tate & Liza: 25 losses with no super-effective answer to Rock/Psychic. Need one of: Ground, Bug, Ghost, Steel, Water, Grass, Dark…'. The same log's TURN lines vs Lunatone/Solrock show 'Swampert -> UseMove:Muddy Water' 22 times (14 vs Solrock, 8 vs Lunatone). Last heartbeat party: Swampert L40, Loudred L35, Mightyena L30, Swellow L42, Castform L27, Machoke L36. Side note, cause UNVERIFIED: Mightyena used only Tackle vs Lunatone (189 lines); its last Bite was f2255178.
* Code: story_mode.py:2393 `for i in (battlers if not hard_plateau else ()):` skips the answer test. story_mode.py:1397 always prints 'with no super-effective answer to'. Constants: HARD_PLATEAU_LOSS_THRESHOLD = 12 (story_mode.py:1782), PLATEAU_LOSS_THRESHOLD = 6, CREDIBLE_ANSWER_POWER = 75.
* P1-Story_(ENDLESS_RESET)-debug-20260926-171104.log: TURN 31→38 show Lunatone L42 going 102/123 → 5/123 while DUMPs say 'STUCK — 51000/54000/57000 frames no progress'. f4857447 '[STALL] handing a recoverable derail to the mode — in-battle wedge: state unchanged for 60,000 frames (KI-36…)'. The dumps that follow show 'battle: active=True … battle_text='What will MIGHTYENA do?'' and 'controllers=['StoryEndlessResetMode.run']'. f4981054 'DERAIL #5: Story: global watchdog — nothing progressed for 18,000 frames'. Code: debug_logger.py:826-838 (signature has no HP or turn count).
* P2-Story_(ENDLESS_RESET)-debug-20260926-153755.log: f988202 '[FAINT-CHOOSER] index spaces: alive_slots=[2, 3](party-order) -> [1, 5](menu-order) on_field=[0](party-order) [orders DIVERGE]' (party of 4). f991135 'DERAIL #1: Story: battle handler gave up — KI-47: battle sub-handler 'handle_fainted_pokemon' ran 3001 frames … BattleScript_FaintedMonTryChoose'. Dump before DERAIL #2: battle active=True, controllers=['StoryEndlessResetMode.run']. #2/#3/#5 'Cutscene did not end after 8000 frames', #4 KI-36.
* P1-Story_(ENDLESS_RESET)-debug-20260926-202738.log: derails #1-#5 at f2353959, f2363696, f2373444, f2383188, f2392934, each 'heal_in_pokemon_center: the walk to LavaridgeTown is BLOCKED … Source (28/28 @ ROUTE112) and destination (6/11 @ ROUTE112_CABLE_CAR_STATION) are not on connected maps'. Each is followed by '[STEP] 'Story: reached Lavaridge Town!'' and then '[MAINTAIN] ABANDONED pid=E0D46375 — ROUTE111(25, 55) unreachable from here'. The Lavaridge Gym was entered 11 times. Code: story_mode.py:3780-3784 resets the budget only on a `_progress_sig` change; _progress_sig is story_mode.py:2049-2064 (party size, lead level, total EXP).

</details>

## PETALBURG WOODS — `Could not reach (26, 5)` (the analyzer's #1 derail)

All 67 occurrences as of about 22:00 (25 runs; the batch is still running, so this is up from the 62/23 in the brief) are the same message: `Could not reach (26, 5) on MapRSE.PETALBURG_WOODS … still at (14, 5)`. It always comes from one place: the Ch12 `travel_lavaridge_to_petalburg` leg, step 'Story: to Petalburg — through Petalburg Woods...' (early_game.py:6780). It is 100% deterministic: in every run log, the number of times that step ran equals the number of these derails (67 = 67). Every time, the bot enters the Woods by the north door (Route 104 (10,30) → Woods (14,5)), fails about 280 frames later, and recovers on the next attempt, leaving by the south-east door (36,38) and reaching Petalburg City. No run ended because of it. The cause is a bad hardcoded destination: (26,5) is a solid tree tile. The tile below it, (26,6), sits in a pocket that is sealed off by the two Cut trees at (19,10)/(19,11) and by one-way ledges. So no path to (26,5) can exist from any Woods entrance. It is not caused by an NPC, a trainer, a Team Aqua scene or a KI-103 template over-block. It is already tracked as the PETALBURG_WOODS member of the open punch-list item `#26-destreachability` (78/99 runs on 2026-09-16), and it is not fixed on branch wt/ch24organic.

**Run-ending:** 0 runs ended because of this signature.
- The highest derail number it ever reached was #2 (26 at #1, 41 at #2). Nothing further happened before the next success.
- In all 67 cases the next event was a successful south-east exit and `-> PETALBURG CITY(0,0)`, and the next derail afterwards was always `DERAIL #1`, so EXP was gained in between and the budget was reset.
- None of the run-ending `DERAIL #5` lines in today's logs are this signature. They are Ch23 Victory Road/EVER_GRANDE, VICTORY_ROAD_1F, Juan/Winona counters and the global watchdog.

Caveat: 41 of the 67 were DERAIL #2 because they followed a no-progress derail (37 heal-to-PetalburgCity BLOCKED, 4 ROUTE102/ROUTE101 '(10,29)'). So each one does use up budget, but it never came close to Manual in this batch.

**Mechanism:** MECHANISM (checked against the ROM data and the bot's own planner, not only inferred from logs):
1. early_game.py:6775-6781: while on the north half of Route 104 (y<38), `travel_lavaridge_to_petalburg` calls `_navigate_riding_out(MapRSE.PETALBURG_WOODS, (26, 5), tries=8)`. The comment at :6683 says legs use 'a SAFE interior tile'. This one was never checked: it arrived in commit f9fe80f8, an unwired WIP draft whose own message lists 'validated Mauville->Petalburg tiles' as work still to do.
2. (26,5) is a WALL:
   - Decomp: `data/layouts/PetalburgWoods/map.bin` (48x44) gives (26,5) collision=1, metatile 0x1e4. Its neighbours (25,5) and (27,5) are also collision 1. On row 5 only the north arrow warps (14,5)/(15,5) are open.
   - The bot's own reader agrees (scratch observe-only probe, booted `flannery_done.ss1` like ch12_static_recon.py): `TILE (26, 5) collision 1 elevation 0 type Normal`.
3. Even the tile below it can't be reached. (26,6) (collision 0, where the hidden Tiny Mushroom is) is in the north-east pocket, which also holds the Girl at (33,5) and the Great Ball at (45,7). That pocket is sealed by two things:
   - The only westward link is rows 10-11, x=18..23, and the Cut trees sit at (19,10)/(19,11) (map.json; flags FLAG_TEMP_11/12, so they come back on every map load).
   - The east side is closed by south-facing one-way ledges at row 8 (x41-45) and row 20 (x42-45).
   - My collision BFS: with the trees blocked, (26,6)/(33,6)/(45,7) are unreachable from both the north landing (14,6) and the south-east landing (36,37). With the trees removed, (26,6) becomes reachable but (26,5) still does not.
   - The planner treats a template tile whose flag is clear as blocked (map_path.py:843-848), which is correct here.
   - Probe with the bot's `calculate_path`: `(14,5)->(26,5) FAIL`, `(14,5)->(26,6) FAIL`, `(14,5)->(14,6) OK 1 waypoints`, `(14,5)->(36,38) OK 56 waypoints`.
   - `calculate_path` has no check that the destination is passable. It just runs the search out and raises 'Could not find a path' (map_path.py:1059).
4. How it fails and recovers:
   - navigate_to_anywhere crosses the Route 104 north door into the Woods and only then plans inside the Woods. It lands on (14,5) and the plan fails.
   - `_navigate_riding_out` (early_game.py:266-340) records last_where=(Woods,(14,5)) and rides out a scene. The second try fails at the same tile, so the fail-fast raises UnreachableDestinationError (early_game.py:333-338). That is 279-284 frames after entering in all 67 cases.
   - The StoryMode derail handler (plugins/custom_modes/story_mode.py:3767-3829) recovers and runs the function again. Now the map is PETALBURG_WOODS, so the Route-104-north block is skipped and the south-east exit block (early_game.py:6782-6796, `_enter_warp_by_navigation(..., (36,38))`) runs and succeeds.
   - In effect, the derail is the only way this code ever gets to its own working south-east exit block.
NOT the cause: the Aqua grunt (26,17) and Devon employee (26,20) are hidden by FLAG_HIDE_* flags after Ch3 and are not on any route to (26,5). The Girl (33,5) is inside the sealed pocket. No ledge sits between (14,5) and the south doors in the direction of travel.

**On branch `wt/ch24organic`?** no. The branch still has the same line at early_game.py:6902 in C:/Remote Projects/pokebot-wt-ch24 (`yield from _navigate_riding_out(MapRSE.PETALBURG_WOODS, (26, 5), tries=8)`). `git diff main` on branch early_game.py only touches the header and the HM-teach hunks (@@ -5214, -5284, -5304). None of today's branch changelog entries (KI-104, KI-105, #26-organiccatch, #26-gymtmteach, #24-dexcatch-battlebail, rulings 15-20, and the rest) mention Petalburg Woods or `_navigate_riding_out`. The item is still open as the PETALBURG_WOODS member of `#26-destreachability` (03-PUNCH-LIST.md:963).

**Candidates (a NOTE — each needs a pre-registered A/B):**
* Minimal fix (early_game.py:6780): replace (26, 5) with a tile that is actually reachable on the southbound route. Options:
- (14, 6): one tile below the landing; `calculate_path` from (14,5) returns 1 waypoint.
- Better: a tile further south on the way to (36,38), so the next block's walk is shorter.
Pre-register an A/B before changing it:
- Arm A (current): must show `DERAIL ... (26, 5) ... still at (14, 5)` about 284 frames after the Woods `[MAP]` line.
- Arm B: no derail, and Petalburg City reached.
The arm needs a fixture on the north half of Route 104 or in Rustboro with the Ch12 travel pending. Confirm with the DRIVEN navigator, not just `calculate_path` (KI-48).
* Structural alternative: drop the 'navigate to a Woods interior tile' hop and go from Route 104 north straight to the existing `_enter_warp_by_navigation(... PETALBURG_WOODS, (36,38) ...)` exit (the planner found (14,5)->(36,38) in 56 waypoints). Caveat: that would bypass `_navigate_riding_out`'s scene handling for the entry hop. Check whether `_enter_warp_by_navigation` can plan a route across the north-door warp from Route 104.
* Class-level gate, fitting `#26-destreachability`: a static probe that collects every hardcoded `_navigate_riding_out` / `navigate_to_anywhere` (map, tile) literal in modules/story/* and asserts `get_map_data(map, tile).collision == 0` and not a warp/ledge tile. Ideally it also asserts `calculate_path` from that leg's known entry tile. Fault-test it by showing it flags (26,5) and does not flag (14,6).
* Planner-side guard (optional, shared path, so it needs an A/B on ordinary navigation): in `calculate_path`, raise a distinct 'destination tile is impassable (collision=1)' error before the search, so logs tell a wall target apart from a blocked route. Today both produce 'Could not find a path'.
* Deprioritise on cost: about 580 frames per occurrence and 39,097 frames in total (about 0.03% of the batch). The real harm is that it takes one slot of the 5-derail budget (41 of 67 were #2) and adds noise to the derail tables. The heal-to-Petalburg BLOCKED derail it usually pairs with, which comes from Rustboro and targets RUSTBORO_CITY_FLAT1_1F, is a separate and costlier signature and should be analysed on its own.

<details><summary>Evidence (agent-quoted log lines)</summary>

* Signature is one exact string, 67/67: `Could not reach (26, 5) on MapRSE.PETALBURG_WOODS: the field is idle and we are still at (14, 5), so retrying cannot change the result (Could not find a path from (14/5 @ PETALBURG_WOODS) to (26/5 @ PETALBURG_WOODS).).` (grep over endless-P*/debug-logs/*debug-20260926-*.log | uniq -c). The four lane stdout files also total 11+22+7+27=67.
* P2-Story_(ENDLESS_RESET)-debug-20260926-114734.log, full cycle: `f1741612 [STEP] 'Story: to Petalburg — through Petalburg Woods...'` → `f1742030 [MAP] ROUTE 104(0,19) -> PETALBURG WOODS(24,11) pos=(10, 30)` → L9296 `f1742314 [STORY] DERAIL #1: Could not reach (26, 5) on MapRSE.PETALBURG_WOODS ... still at (14, 5)` → `f1742614 [STEP] 'Story: heading to Petalburg — the long road to Norman...'` → `f1743200 [MAP] PETALBURG WOODS(24,11) -> ROUTE 104(0,19) pos=(36, 38)` → `f1743521 [MAP] ROUTE 104(0,19) -> PETALBURG CITY(0,0) pos=(40, 62)`
* Deterministic: in every one of the 25 affected run logs, the count of `[STEP] 'Story: to Petalburg — through Petalburg Woods` equals the count of this derail (e.g. P2 114734 steps=7 derails=7, P4 185402 steps=6 derails=6). Total 67 = 67.
* Time from entering the Woods to the derail is 279-284 frames in all 67 cases (the two failed plans with one ride-out between them).
* Recovery: 67/67 reach `-> PETALBURG CITY(0,0)` before another Woods derail, and 0 repeat without getting there. The next derail after each is always `DERAIL #1`, so EXP was gained in between and the budget was reset.
* DERAIL-number distribution: #1 ×26, #2 ×41. None higher.
* Preceding derails within 5000 frames:
- 37× `heal_in_pokemon_center: the walk to PetalburgCity is BLOCKED`
- 4× `Could not reach (9, 2) on MapRSE.ROUTE102 / (9, 9) ROUTE101 ... still at (10, 29)`
- 26× none
* Paired example, P4-Story_(ENDLESS_RESET)-debug-20260926-185402.log: `f2050032 [STORY] DERAIL #1: heal_in_pokemon_center: the walk to PetalburgCity is BLOCKED ... Source (13/31 @ RUSTBORO_CITY) and destination (6/7 @ RUSTBORO_CITY_FLAT1_1F) are not on connected maps` → `f2050814 [STEP] 'Story: to Petalburg — through Petalburg Woods...'` → `f2051516 [STORY] DERAIL #2: Could not reach (26, 5) on MapRSE.PETALBURG_WOODS ...`
* ROUTE102 pairing, P1-Story_(ENDLESS_RESET)-debug-20260926-152025.log:
- `f2757074 [MAP] ROUTE 104(0,19) -> PETALBURG WOODS(24,11)` then `f2757230 [MAP] PETALBURG WOODS(24,11) -> ROUTE 104(0,19) pos=(14, 5)`: a different navigator went in and straight back out the north door.
- Then `f2757535 DERAIL #1: Could not reach (9, 2) on MapRSE.ROUTE102 ... still at (10, 29)` → `f2758231 DERAIL #2: ... PETALBURG_WOODS ...`.
* Decomp `pret/pokeemerald data/maps/PetalburgWoods/map.json`:
- North warps only at (14,5) and (15,5); south doors at (16,38), (17,38), (36,38), (37,38).
- Cut trees `OBJ_EVENT_GFX_CUTTABLE_TREE` at (19,10) FLAG_TEMP_11 and (19,11) FLAG_TEMP_12.
- Hidden item at (26,6); Girl at (33,5); Great Ball at (45,7).
- Aqua grunt at (26,17) and Devon employee at (26,20), both behind FLAG_HIDE_* flags.
* Decomp `data/layouts/PetalburgWoods/map.bin` (48x44, raw download, 4224 bytes):
- (26,5) collision 1, metatile 0x1e4; (25,5) and (27,5) collision 1.
- (26,6) and (26,7) collision 0, elevation 3.
- BFS with the Cut-tree tiles blocked: (26,6) is unreachable from (14,6) and from (36,37); (36,38) is reachable.
- BFS with the trees removed: (26,6) reachable, (26,5) still not.
* Bot's own reader and planner (scratch observe-only probe booting tools/story-dev/saves/flannery_done.ss1):
- `TILE (26, 5) collision 1 elevation 0 type Normal`
- `PATH (14,5)-> (26, 5) FAIL Could not find a path ...`
- `PATH (14,5)-> (26, 6) FAIL`
- `PATH (14,5)-> (14, 6) OK 1 waypoints`
- `PATH (14,5)-> (36, 38) OK 56 waypoints`
- ⚠ These are `calculate_path` results, not a driven walk (KI-48).

</details>

## ROUTE 111 — `Could not reach (25, 55)` from Route 116

This is one deterministic derail, and every run recovers from it. Every occurrence is byte-identical: "DERAIL #1: Could not reach (25, 55) on MapRSE.ROUTE111: the field is idle and we are still at (47, 9) ... (Source (47/9 @ ROUTE116) and destination (4/10 @ RUSTURF_TUNNEL) are not on connected maps (note that warps don't count.))". The batch is still running, so the count keeps growing: 24 when the task was set, 27 runs / 27 derails in the analyzer when I ran it, and 28 runs / 28 derails in the logs when I grepped them (P3 run 20260926-214626 has since added f633353).

It is NOT a Route 111 terrain problem. The desert, ledges, Winstrate house and trainers are never touched: the bot never leaves Route 116 or the west end of Rusturf Tunnel.

Where it happens: story stage "5b: Mr. Briney & the boat", during prep for the Rustboro rival fight (`rival_fight`, band (16,19), grass = RUSTBORO_TRAINING_GRASS = ROUTE116 (11,7)). The bot's own relocation rule (FODDER_RULE xp_rate) decides that "ROUTE116 (max L8) is fodder for a L18-20 team" and picks ROUTE111 (25,55), L19-22, as the training area. That tile is unreachable at this stage for three independent reasons:
1. The Rusturf Tunnel mid-wall rocks are still present.
2. There is no Rock Smash and no Badge 3.
3. The tile is north of the Go-Goggles desert.

What the bot then does: it walks into Rusturf Tunnel at Route 116 (47,8), immediately walks back out, does this twice, and fail-fasts.

Outcome and cost:
- Recovered 28 of 28 times. 0 runs ended by it.
- About 3.1k frames median per occurrence, about 108k frames in total (≈0.08% of the batch).
- Side effect: each derail uses up one of the 3 Rustboro-rival attempts without a fight.

This is the ROUTE111 member of the open punch-list item `#26-destreachability` (84/99 runs on 2026-09-16), and it is still unfixed.

**Run-ending:** 0 of 28 runs were ended by it.
- Every occurrence is 'DERAIL #1'.
- In 25 runs the next derail is another 'DERAIL #1' with a different signature: PETALBURG_WOODS in 15 runs, heal_in_pokemon_center LavaridgeTown in 10. That shows the consecutive-derail counter reset.
- In the 3 runs where it is the only derail so far (P1 212850, P2 210840, P3 214626), each run kept going for hundreds of thousands of frames or more.
- Every run that did go to Manual got there on a different DERAIL #5 signature: Ch23 Victory Road / EVER_GRANDE (18,42), Winona, Juan, Tate & Liza, the global watchdog, VICTORY_ROAD_1F, ROUTE101, or heal Lavaridge. Examples: P1 114734 "f5587807 DERAIL #5: Ch23 (Victory Road) ..."; P4 135925 "f2232065 DERAIL #5: Could not reach (9, 9) on MapRSE.ROUTE101".

Latent risk: each occurrence uses one of the 3 Rustboro-rival attempts (floor 10 → 12). A run would reach Manual through this path only if it then lost the rival twice more. That happened 0 times today.

**Mechanism:** Four steps. The first two are the chooser; the last two are the walker and the handler.

(1) THE CHOOSER ASKS FOR AN UNREACHABLE AREA.
- `_prepare_for_fight(rival_fight)` is called at plugins/custom_modes/story_mode.py:4265.
- Under the xp_rate rule it probes `best_training_area(team_max_now, min_wild_max=local_max, allow=_allow)` (story_mode.py:3235-3252), then picks at :3278. The message comes from :3290.
- The pick is ROUTE111 (25,55) (19,22), whose prereq is "region" (modules/story/training_areas.py:91 and :319).
- `_training_area_allowed` (story_mode.py:1168) has no extra gate for "region".
- The Go-Goggles item gate (AREA_ITEM_PREREQ) is OFF by default (POKEBOT_AREA_ITEM_GATE=0, story_mode.py ~1222-1250). It was deliberately switched off on 2026-08-04 because it zeroed every ROUTE111 relocation, including the successful ones.
- The only remaining check is `region_reach.is_map_reachable(ROUTE111, max_hops=_MAX_TRAINING_TRAVEL_LEGS=4)` (story_mode.py:1101 and :1269).

(2) WHY region_reach SAYS YES. This part is derived, not live-probed: I did not run `hops_to` on a live ROM. The derivation:
- The decomp ROUTE116 map.json declares a MapConnection {'map': 'MAP_VERDANTURF_TOWN', 'offset': 80, 'direction': 'down'}.
- `_build_graph` turns every N/S/E/W connection into a 1-hop two-way edge (modules/story/region_reach.py:~300-315).
- That gives ROUTE116 → VERDANTURF_TOWN (1) → ROUTE117 (2) → MAUVILLE_CITY (3) → ROUTE111 (4), which is within 4 hops.
- `KNOWN_GATES` (region_reach.py:81) holds only the Dewford sea edges and the Victory Road entrance.
- The project already knows this connection is a phantom: 07-CHANGELOG ~line 5812 says "0 of 40 sampled ROUTE116 tiles are walkable from Verdanturf".
- The real link, the Rusturf warps, is sealed at this stage. The decomp RusturfTunnel map has breakable rocks at (24,5) FLAG_HIDE_RUSTURF_TUNNEL_ROCK_1 and (24,4) FLAG_HIDE_RUSTURF_TUNNEL_ROCK_2. The code says the same in modules/modes/util/global_navigation.py:347: "Rusturf Tunnel's middle is sealed by the Wanda-quest rocks, so from just inside it the ONLY walkable warp leads straight back out".
- The tile (25,55) is also north of the desert, per the heal-map comment at story_mode.py ~1440.

(3) THE WALKER. The call chain is `train_team` → `_goto_training_area` (modules/story/early_game.py:2257) → `_navigate_riding_out` → `navigate_to_anywhere` (global_navigation.py:426).
- On Route 116 the direct walk fails, so the executor takes the warp at Route 116 (47,8) and arrives in RUSTURF_TUNNEL (4,10), standing on the door back out.
- `pick_leg` (global_navigation.py:255) finds no walkable door to a NEW map (the Verdanturf door (29,16) is behind the rocks). Its second pass therefore takes the door it is standing on: (4,10) → ROUTE116.
- That navigate is a zero-step no-op, so the "step off and back on" fork runs (global_navigation.py:635-650). It presses "Down" first, which carries the avatar out through the cave mouth to Route 116 (47,9).
- The fork then calls `navigate_to(RUSTURF_TUNNEL, (4,10))` while on ROUTE116, and `calculate_path` raises the "not on connected maps (note that warps don't count.)" text (modules/map_path.py:771).
- Confidence on this fork step is INFERRED from code plus log, not instrumented. The log fits it exactly: tunnel stays of about 95-130 frames, and the error's destination (4/10 @ RUSTURF_TUNNEL) equals that door leg's from_coords.
- `_navigate_riding_out` records where=(ROUTE116,(47,9)), rides out a scene, and retries. The retry repeats the whole walk-in/walk-out, and the second identical failure at the same tile trips the fail-fast `raise UnreachableDestinationError` at early_game.py:334-338. That is why every occurrence shows exactly 2 tunnel entries.

(4) THE HANDLER.
- story_mode.py ~3316-3329 catches it, calls `_note_training_unreachable(ROUTE111,(25,55))` (story_mode.py:2613; keyed on the standing map ROUTE116), and re-raises. The result is DERAIL #1.
- On resume `_training_blocked` hides ROUTE111 from ROUTE116. The xp_rate probe then returns None, the local patch is judged not-fodder, and prep trains on ROUTE116 instead ("prepping — training 3 battler(s) to Lv 17 in ROUTE116").
- The re-entry into the rival block also runs `self._rival_attempts += 1` (story_mode.py ~4229), which raises the level floor from 10 to 12 and uses one of RIVAL_MAX_ATTEMPTS=3 (story_mode.py:1768).

**On branch `wt/ch24organic`?** No. `git diff main...wt/ch24organic --stat -- sandbox-pokebot` touches none of region_reach.py, training_areas.py or global_navigation.py. The story_mode.py and early_game.py hunks on the branch are about the gym TM teach, dex catch, HM teach, the League and Amulet Coin; none touches `_training_area_allowed`, the relocation block, `_navigate_riding_out` or pick_leg. The branch's 07-CHANGELOG entries for 2026-09-25/26 have no mention of ROUTE111, Rusturf, relocation, destreachability or region_reach (grep of lines 35509-36003 is empty). `#26-destreachability` is still `[ ]` open in the branch 03-PUNCH-LIST.md:963. The only other change on the branch is an unstaged tools/story-dev/party_accounting_ledger.jsonl, which is unrelated.

**Candidates (a NOTE — each needs a pre-registered A/B):**
* (Chooser, narrowest) Gate the ROUTE116<->VERDANTURF_TOWN MapConnection as impassable in region_reach (e.g. a KNOWN_GATES 'never' entry). The repo already calls it a phantom (07-CHANGELOG ~5812). After that the region path must use the Rusturf warps: ROUTE116→RUSTURF(1)→VERDANTURF(2)→ROUTE117(3)→MAUVILLE(4)→ROUTE111(5) exceeds the 4-hop budget, so it would be refused from ROUTE116. This also changes hop counts for `_counter_area_allowed` (COUNTER_MAX_HOPS=8), which needs checking with repro_region_reach.py.
* (Chooser, stage-aware) Model the Rusturf wall in region_reach: make the RUSTURF_TUNNEL<->VERDANTURF_TOWN edge conditional on FLAG_HIDE_RUSTURF_TUNNEL_ROCK_1/2 being set (rocks gone), not on a move capability. Without this, candidate 1 still leaves the 5-hop warp route open to any caller with a bigger hop budget.
* Do NOT simply flip POKEBOT_AREA_ITEM_GATE=1. story_mode.py ~1222-1250 records that this gate cut ROUTE111 relocations from ~43% success to zero in batches b8-b12. Any narrower Go-Goggles/north-desert condition must first count the Mauville/Fallarbor-side relocations that it would remove. There were zero today, but earlier batches had them.
* (Walker, cost-only) In navigate_to_anywhere, when pick_leg's second pass returns the door the avatar is standing on (the arrival door) and there is no other candidate, raise immediately with an explicit 'only exit is back the way we came' reason instead of running the step-off fork. That halves the wasted walk (one tunnel round-trip instead of two) and gives an honest error text. Low value (a few hundred frames).
* (Handler) Stop counting a derailed prep as a rival attempt: increment `_rival_attempts` only when fight_rustboro_rival actually starts or loses, not on every re-entry of the not-resolved block (story_mode.py ~4229). This removes the latent Manual path. It must be A/B-driven, because the escalating level floor is keyed to that counter.
* Before building any of these, note the punch-list rule on `#26-destreachability`: counts are events, not costs. Today's per-derail classification is 28/28 RECOVERED, about 3.9k frames each, so this is a low-cost item. Any reachability pre-check must use the same instrument the walker uses (KI-48).

<details><summary>Evidence (agent-quoted log lines)</summary>

* P1-Story_(ENDLESS_RESET)-debug-20260926-114734.log L2221: "f347432 [STORY] Story: ROUTE116 (max L8) is fodder for a L19 team — relocating to ROUTE111 (L19-22) to train for real. [rule=xp_rate]"
* Same file, the walk: "f350210 [MAP] ROUTE 116(0,31) -> RUSTURF TUNNEL(24,4) pos=(47, 8)" / "f350243 ... -> RUSTURF TUNNEL(24,4) pos=(4, 10)" / "f350337 [MAP] RUSTURF TUNNEL(24,4) -> ROUTE 116(0,31) pos=(4, 10)" (back out after 94 frames) / "f350747 [MAP] ROUTE 116(0,31) -> RUSTURF TUNNEL(24,4) pos=(47, 8)" / "f350874 [MAP] RUSTURF TUNNEL(24,4) -> ROUTE 116(0,31) pos=(4, 10)" / L2247 "f350946 [STORY] DERAIL #1: Could not reach (25, 55) on MapRSE.ROUTE111: the field is idle and we are still at (47, 9), so retrying cannot change the result (Source (47/9 @ ROUTE116) and destination (4/10 @ RUSTURF_TUNNEL) are not on connected maps (note that warps don't count.))."
* P1-stdout-20260926-114731.txt: "Story: prepping — training 1 battler(s) to Lv 18 in ROUTE111" → "Story: ROUTE111 (25, 55) is not reachable from here — dropping it as a training option for the rest of this run." → "Story localization — derail #1: Could not reach (25, 55) on MapRSE.ROUTE111 ... | stage: 5b: Mr. Briney & the boat | map (0, 31)" → "Story: leveling the whole team to ≥ Lv 12 before the rival…" → "Story: prepping — training 3 battler(s) to Lv 17 in ROUTE116"
* All 28 occurrences across the 4 stdout files carry 'stage: 5b: Mr. Briney' (P1 8, P2 5, P3 7, P4 8). Each is preceded by exactly one 'relocating to ROUTE111' in the same debug log, for a team of L18-20, and each shows 2 Route116→Rusturf entries before the derail (checked by script; the one-entry string mismatches were verified by eye, e.g. P1 202738 f657985 and f658522).
* Batch-wide relocation tally (grep of every 20260926 debug log): 27× 'ROUTE116 (max L8) ... relocating to ROUTE111' and 96× 'local grass (max L4) ... no better area is available'. No other relocation exists, so the ROUTE111 relocation succeeded 0 times today.
* Rival-attempt side effect: across the 4 stdouts, 'leveling the whole team to ≥ Lv 10 before the rival…' ×31 and '≥ Lv 12' ×28. The 28 matches the derail count; each re-entry is `_rival_attempts += 1` (story_mode.py ~4229). 'couldn't beat the Rustboro rival' appears 0 times.
* Decomp (gh api pret/pokeemerald): Route116 map.json connections [{'map':'MAP_VERDANTURF_TOWN','offset':80,'direction':'down'}, {'map':'MAP_RUSTBORO_CITY','direction':'left'}] and warps (47,8)->RUSTURF_TUNNEL, (65,10)->RUSTURF_TUNNEL. VerdanturfTown connections: up ROUTE116, right ROUTE117. MauvilleCity: up ROUTE111. RusturfTunnel warps (4,10)->ROUTE116, (29,16)->VERDANTURF_TOWN, (18,20)->ROUTE116, plus BREAKABLE_ROCK objects at (24,5) FLAG_HIDE_RUSTURF_TUNNEL_ROCK_1 and (24,4) FLAG_HIDE_RUSTURF_TUNNEL_ROCK_2.
* Code: sandbox-pokebot/plugins/custom_modes/story_mode.py:1101 (_MAX_TRAINING_TRAVEL_LEGS = 4), :1269 (region_reach.is_map_reachable), :3235/:3247/:3278/:3290 (xp_rate probe, pick, message), ~:3316-3329 (except UnreachableDestinationError -> _note_training_unreachable, re-raise), :2613/:2624 (blacklist keyed on standing map); modules/story/region_reach.py:81 (KNOWN_GATES lacks ROUTE116<->VERDANTURF); modules/modes/util/global_navigation.py:255 (pick_leg two passes), :347 (the code's own statement that the tunnel is sealed), :635-650 (step-off fork presses Down, then navigate_to(leg.from_map=RUSTURF_TUNNEL,(4,10))); modules/story/early_game.py:334 (fail-fast raise); modules/map_path.py:771 (error text).
* Next derail after each occurrence is again 'DERAIL #1' of a different signature (PETALBURG_WOODS or heal_in_pokemon_center LavaridgeTown), so the consecutive counter was reset by progress. In 3 runs (P1 212850, P2 210840, P3 214626) it is the only derail so far, and those runs continued (e.g. P1 212850's last line is f1187302; P2 210840's is f2011443).
* Prior measurement: PROJECT KNOWLEDGE/03-PUNCH-LIST.md:963 `#26-destreachability` (open) — 'ROUTE111 (84/99 runs — relocation picks it from ROUTE116; the path needs RUSTURF_TUNNEL...)'; ai-research-notes/2026-09-16-endless-batch-REVIEW.md §2.

</details>

## HEAL WALKS — `heal_in_pokemon_center: the walk to <town> is BLOCKED`

NOTE, not truth. Snapshot at 22:09 PDT; the batch is still running. There are 98 derails with this signature: PetalburgCity 38 in 12 runs, LavaridgeTown 54 in 10 runs, FortreeCity 6 in 6 runs. Together they hit 19 of the 31 real runs (the analyzer's "35 runs" includes four 28-line *-114733.log stubs).

**Where the walk starts.** Not at the whiteout respawn, and not blocked by an NPC, Wally's family, the Lavaridge hot springs or a Surf need. It starts after `_prepare_for_fight` has taken the team to a distant area, and the heal back to the boss town (story_mode.py:4726 Norman, :4675 Flannery, :4884 Winona) then runs `navigate_to_anywhere` across a map split it cannot plan. The distant area is either a MAINTAIN training ground or a Fiery Path counter hunt:
- ROUTE116(11,7) for Norman
- ROUTE111(25,55) or ROUTE117(31,16) for Flannery
- Fiery Path counter hunts for Norman, Flannery and Winona

The walk fails in three ways.

**(A) Dead-end-building bounce: 87 of 98 events.** The staged-progress step picks a building door as "progress":
- Rustboro Flat1: 37
- Route 112 cable car station: 40
- Mauville Poké Center: 8
- Glass Workshop: 1
- Meteor Falls: 1

The bot arrives standing on the exit mat. The step-off-and-back-on fallback in `navigate_to_anywhere` presses Down first, which walks it straight back out. It then tries to navigate to the mat inside the building from outside, and gets "not on connected maps".

**(B) "Cannot reach LAVARIDGE_TOWN" from Route 112: 5 events.** The warp graph thinks Route 112 is 1 hop from Lavaridge, so the cable car (2 hops) is filtered out.

**(C) Sealed Desert Ruins door: 4 events.** The Desert Ruins door at ROUTE111(29,87) is sealed with rock unless FLAG_REGI_DOORS_OPENED. The warp graph still offers it, and the pathfinder validates it. The bot bumps into the rock at (29,88) and gets "made no progress".

**Recovery.** It usually recovers, through the story's own travel legs:
- Lavaridge: "descending Jagged Pass to Lavaridge" by cable car, about 2.8k frames.
- Petalburg: "the long road to Norman", about 3.0k frames. It throws a PETALBURG_WOODS derail on the way every time (38 of 38).

**Run endings.** It ended exactly 1 run: P1 run 7 (P1-...-202738.log), with 5 consecutive Lavaridge cable-car derails. The loop there is:
1. MAINTAIN re-picks ROUTE111(25,55).
2. The Rock Smash spot at (19,100) causes a scripted-event failure, and MAINTAIN is abandoned.
3. The heal walk from Route 111 bounces.
4. The derail recovery goes back to Lavaridge, and the cycle repeats.

The "drop this ground for the rest of the run" blacklist is keyed by the map the bot is standing on, so it never matches the next pick. That ground was abandoned 19 times in that run.

**Branch.** Not fixed on wt/ch24organic: the navigation and heal files are identical there.

**Run-ending:** It ended 1 run: P1 run 7 (P1-Story_(ENDLESS_RESET)-debug-20260926-202738.log). The evidence:
- **Console:** P1-stdout-20260926-114731.txt:849660 reads "=== ENDLESS RESET: run 7/infinite -> derailed: heal_in_pokemon_center: the walk to LavaridgeTown is BLOCKED ... Source (28/28 @ ROUTE112) and destination (6/11 @ ROUTE112_CABLE_CAR_STATION)".
- **Debug log:** DERAIL #1 through #5 are all this signature (f2353959, f2363696, f2373444, f2383188, f2392934), followed by "=== DEBUG LOG END ===".
- **No other run:** the last 5 DERAIL lines of every complete debug log were checked; no other run's final streak contains a BLOCKED derail. Grep counts of "ENDLESS RESET: run N/infinite -> derailed: heal_in" are P1:1, P2:0, P3:0, P4:0.

Everywhere else it recovered, and whiteouts often reset the derail budget ("moved on since the last whiteout — budget reset"). Petalburg and Fortree events never ended a run. Four runs are still in progress; P4-...-205921 and P2-...-210840 each already have BLOCKED derails.

**Mechanism:** Main mechanism, (A): 87 of 98 events, derived from the code plus the error text, not probed live.

1. **The call.** `heal_in_pokemon_center` (sandbox-pokebot/modules/modes/util/higher_level_actions.py:492) calls `navigate_to_anywhere(door)`. In each case the target is not walkable from the current map because of a split the ROM warp graph does not model: the Petalburg Woods split of Route 104, the scripted cable car, one-way Jagged Pass.
2. **No candidate validates.** `warp_candidates()` for PETALBURG, LAVARIDGE and FORTREE only returns doors that start in the target town itself (offline replay against sandbox-pokebot/cache/warp_graph_BPEE0.json). None are reachable, so `pick_leg` returns None and `_staged_progress_warp` decides (modules/modes/util/global_navigation.py:328-364).
3. **Staged progress picks a building.** It only looks at the current map plus its direct connections (`nearby`, line 335). It accepts `distance <= here_distance` (line 342) and breaks ties by `onward_exits`. A town building's own exit mats count as 2-3 "exits". So the top pick is a dead-end interior. Replay, where d is the map-hop distance to the target town:
   - ROUTE116 to Petalburg: RUSTBORO_CITY(13,30) -> RUSTBORO_CITY_FLAT1_1F(6,7), d=3, same as here.
   - ROUTE117 to Lavaridge: MAUVILLE_CITY(22,5) -> POKEMON_CENTER_1F(7,8).
   - ROUTE111 to Lavaridge: ROUTE112(28,27) -> CABLE_CAR_STATION(6,11). The JAGGED_PASS door ranks higher but was not taken, so it presumably failed validation (UNVERIFIED).
   - FALLARBOR to Fortree: ROUTE113(33,5) -> GLASS_WORKSHOP(3,8).
   - ROUTE114 to Petalburg: METEOR_FALLS_1F_1R(27,18).
4. **Re-plan picks the mat under its feet.** After warping in, the bot stands on the arrival exit mat. The re-plan's first candidate is `plan()`'s door back out, which is that same tile. It "validates" with zero steps, so `navigate_to` does nothing and `_warp_fired` is False.
5. **The step-off fallback (global_navigation.py:629-651) walks it out.** It presses "Down" first (line 636). On an exit mat that press IS the exit warp, so the player walks out to the tile below the door. The fallback then unconditionally calls `_navigate_when_ready(navigate_to, leg.from_map, leg.from_coords)` (lines 643-649), which asks to reach a tile inside the building from outside.
6. **The error.** That gives the PathFindingError "Source (...) and destination (...) are not on connected maps" (modules/map_path.py:771), re-raised as BotModeError at modules/modes/util/walking.py:456-457.
7. **The classifier.** At higher_level_actions.py:583-590 the message lacks `_SCRIPTED_EVENT_MARKER` (line 402). It is re-raised as HealWalkFailedError "BLOCKED" and the story derails.

**The signature fits every (A) case.** The error's destination is always the arrival tile inside, and its source is always the tile below the door:

| building | error source | error destination |
|---|---|---|
| Rustboro Flat1 | 13/31 @ RUSTBORO_CITY | 6/7 @ FLAT1_1F |
| Route 112 cable car station | 28/28 @ ROUTE112 | 6/11 @ CABLE_CAR_STATION |
| Mauville Poké Center | 22/6 @ MAUVILLE_CITY | 7/8 @ POKEMON_CENTER_1F |
| Glass Workshop | 33/6 @ ROUTE113 | 3/8 @ GLASS_WORKSHOP |
| Meteor Falls | 8/64 @ ROUTE114 | 27/18 @ METEOR_FALLS_1F_1R |

**(B) "Cannot reach LAVARIDGE_TOWN", 5 events.** These come after a Fiery Path counter hunt exits to ROUTE112 (11,37). The graph has a ROUTE112<->LAVARIDGE connection, which in the game is a one-way ledge. So `here_distance` is 1, the cable car (d=2) is excluded at line 342, no Lavaridge door validates, and global_navigation.py:595 raises.

**(C) Sealed Desert Ruins door, 4 Fortree events.** Staged progress from ROUTE112/ROUTE113/MAUVILLE picks ROUTE111(29,87) -> DESERT_RUINS. The decomp (pret/pokeemerald data/maps/Route111/scripts.inc, `Route111_OnLoad`) does `call_if_unset FLAG_REGI_DOORS_OPENED, Route111_EventScript_CloseDesertRuins`, which does `setmetatile 29, 87, METATILE_General_RockWall_SandBase, TRUE`. `_walk_is_possible` still validates the door, because map_path.py:841 exempts a warp destination tile from collision. The walk then bumps at (29,88) and raises NavigationStuckError.

**What keeps it going.** The heal calls come right after `_prepare_for_fight`, whose MAINTAIN top-up (or a counter hunt) left the team far away (plugins/custom_modes/story_mode.py:4722-4726, :4673-4675, :4882-4884). In the run that ended, the ROUTE111(25,55) blacklist entry is keyed by `_here_map()` at failure time (story_mode.py:2613-2628). Failure is recorded from ROUTE111, but the next pick is made from LAVARIDGE_TOWN, so `_training_blocked` never matches and the same ground is re-picked. This keying mechanism is inferred from the code, not instrumented.

**UNVERIFIED.** Why the Route 111 MAINTAIN walk hits a scripted event at the Rock Smash rock at (19,100).

**On branch `wt/ch24organic`?** No.
- **Navigation code is unchanged.** `diff --strip-trailing-cr` shows these files identical between sandbox-pokebot and C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot: modules/modes/util/global_navigation.py, modules/warp_graph.py, modules/modes/util/walking.py, modules/modes/util/higher_level_actions.py.
- **The branch diff doesn't touch them.** `git diff --stat main...HEAD -- sandbox-pokebot` lists 13 files, none of those four.
- **Today's changelog doesn't mention it.** The worktree 07-CHANGELOG entries for 2026-09-26 (lines ~35509-35986) cover endlesscap, carleestage, ch23training, ch24organic R1/gaps, ch23money, rulings 15-20, dexcatch, gymtmteach, organiccatch and KI-104/105. None mention heal walk, staged progress, dead-end warps, the cable car, the Desert Ruins or the training blacklist.
- **story_mode.py does differ on the branch.** The differences are dex-catch bail, gym TM teach, league reserve and similar. A grep of the diff for heal/maintain/navigate/training found nothing touching `_prepare_for_fight`'s MAINTAIN or the heal call sites. That check was not exhaustive (UNVERIFIED).

**Candidates (a NOTE — each needs a pre-registered A/B):**
* 1. Stop the bounce (global_navigation.py:629-651). After the step-off key presses, re-read `tuple(get_player_avatar().map_group_and_number)`; if `_warp_fired(leg, that_map)` is true, count the leg and `continue` instead of re-navigating to `leg.from_map`/`leg.from_coords`. The Down press on an exit mat IS the warp. Equivalently, skip a candidate whose `from_coords` is the tile the bot just arrived on. This addresses the 87 'not on connected maps' events. For Petalburg the offline replay then picks ROUTE104(10,30) -> PETALBURG_WOODS next. It does NOT fix Lavaridge: back on ROUTE112 the planner hits variant B. Per the playbook it needs a pre-registered A/B on the Route116 -> Petalburg heal, with the unfixed code as the control arm.
* 2. Make `_staged_progress_warp` refuse dead-end interiors (global_navigation.py:328-364). Compute `onward_exits` excluding exits that return to the map the door is on: FLAT1_1F, CABLE_CAR_STATION, MAUVILLE PC_1F and GLASS_WORKSHOP each score 2-3 'exits' today that are only their own door mats. Alternatively, require a strict distance decrease for a warp into an indoor map. Used alone, this turns the bounce into an immediate honest 'Cannot reach X', so it is cheaper but still derails.
* 3. Fall back to the story's own travel leg (the same routine the derail recovery uses) when `heal_in_pokemon_center(PetalburgCity|LavaridgeTown)` gets HealWalkFailedError: 'the long road to Norman' for Petalburg, 'descending Jagged Pass to Lavaridge' by cable car for Lavaridge. Both demonstrably reach the town, at a median of about 3k frames. This saves a derail slot per event and would have broken P1 run 7's 5-derail streak. Caveat: the Petalburg travel itself throws a PETALBURG_WOODS derail first in 38 of 38 cases, and the 2026-09-12 changelog warns not to break the working recovery.
* 4. Make the MAINTAIN / counter-hunt return path explicit. When the boss's heal town is not reachable from the training ground with the generic navigator (ROUTE116 -> Petalburg, ROUTE111/ROUTE117 -> Lavaridge, Fiery Path -> Lavaridge/Fortree), either heal at the local PC first (Rustboro for Route 116, Mauville/Verdanturf for Route 117) or exclude that ground. The story_mode.py comment near :4655 already records that Route 112's lower grass has no return path to Lavaridge.
* 5. Fix the keying of `_note_training_unreachable` / `_training_blocked` (story_mode.py:2613-2628). It is keyed by `_here_map()` at failure time (ROUTE111), while the next pick happens from LAVARIDGE_TOWN, so ROUTE111(25,55) was re-picked 19 times in P1 run 7. Key it by (target map, tile), or also record it under the town it is picked from. Also investigate (UNVERIFIED) why the walk to ROUTE111(25,55) trips a scripted event at the Rock Smash rock (19,100); the stuck dump shows scripts=['EventScript_RockSmash','Std_MsgboxDefault'].
* 6. Gate the ROUTE111(29,87) -> DESERT_RUINS warp edge on FLAG_REGI_DOORS_OPENED (decomp Route111_OnLoad), or stop map_path.py:841's warp-destination collision exemption from applying when `_walk_is_possible` is only validating a candidate. Addresses 4 Fortree events.
* 7. Mark the ROUTE112 <-> LAVARIDGE_TOWN connection one-way (ledge) in the warp graph's distance, so `here_distance` from ROUTE112 is not 1 and staged progress may consider the cable car. The cable car ride is scripted, so this only helps together with #3 or #4. Addresses 5 events.

<details><summary>Evidence (agent-quoted log lines)</summary>

* Bounce mechanism, Petalburg variant, full sequence (P4-Story_(ENDLESS_RESET)-debug-20260926-114734.log): 'f1801050 [STORY] WHITEOUT recovery #1 at (0, 0)' -> 'f1801064 [MAINTAIN] start Shedinja pid=FCE880F2 L20->L21 on ROUTE116(11, 7)' -> 'f1817555 [MAINTAIN] done pid=FCE880F2 L20->L24' -> 'f1817936 [MAP] ROUTE 116(0,31) -> RUSTBORO CITY(0,3) pos=(-1, 8)' -> 'f1818451 [MAP] RUSTBORO CITY(0,3) -> RUSTBORO CITY(11,8) pos=(13, 30)' (map (11,8) = RUSTBORO_CITY_FLAT1_1F, map_data.py:957) -> 'f1818512 [MAP] RUSTBORO CITY(11,8) -> RUSTBORO CITY(0,3) pos=(6, 7)' -> 'f1818586 [STORY] DERAIL #1: heal_in_pokemon_center: the walk to PetalburgCity is BLOCKED, not interrupted — ... Underlying error: Source (13/31 @ RUSTBORO_CITY) and destination (6/7 @ RUSTBORO_CITY_FLAT1_1F) are not on connected maps'
* Call site, console (P4-stdout-20260926-114731.txt ~line 26760): 'Story: lead vs Normal -> ShedinjaL21 ...' immediately followed by 'Story localization — derail #1: heal_in_pokemon_center: the walk to PetalburgCity is BLOCKED ... | stage: 13: Gym 5 — Norman (Dad) | map (0, 3)'. This matches story_mode.py:4725 (_lead_best_matchup(['Normal'])) then :4726 heal_in_pokemon_center(PokemonCenter.PetalburgCity).
* Recovery of the Petalburg variant (same P4 log): 'f1818886 [STEP] 'Story: heading to Petalburg — the long road to Norman...'', then 'f1820077 [STORY] DERAIL #2: Could not reach (26, 5) on MapRSE.PETALBURG_WOODS ... still at (14, 5)', then 'f1821545 [STEP] "Story: reached Petalburg City — Norman's gym awaits."'. Across the batch, the next derail after a Petalburg BLOCKED was the PETALBURG_WOODS signature 38 of 38 times.
* Run-ending loop (P1-Story_(ENDLESS_RESET)-debug-20260926-202738.log): 'f2382248 [MAINTAIN] ABANDONED pid=E0D46375 — ROUTE111(25, 55) unreachable from here (... We unexpectedly triggered a scripted event while trying to reach (25, 55) @ (0, 26)' -> 'f2383091 [MAP] ROUTE 112(0,27) -> ROUTE 112(19,0) pos=(28, 27)' (19,0 = cable car station) -> 'f2383153 [MAP] ROUTE 112(19,0) -> ROUTE 112(0,27) pos=(6, 11)' -> 'f2383188 [STORY] DERAIL #4: ... walk to LavaridgeTown is BLOCKED ... Source (28/28 @ ROUTE112) and destination (6/11 @ ROUTE112_CABLE_CAR_STATION) are not on connected maps'. Derails #1-#5 are at f2353959, f2363696, f2373444, f2383188 and f2392934, with no whiteout between them, then '=== DEBUG LOG END ==='.
* Run ending, console (P1-stdout-20260926-114731.txt:849660): '=== ENDLESS RESET: run 7/infinite -> derailed: heal_in_pokemon_center: the walk to LavaridgeTown is BLOCKED ...'. The lines just before it read: 'Story: ROUTE111 (25, 55) is not reachable from here — dropping it as a training option for the rest of this run.' ... 'Story: lead vs Fire -> NumelL18' ... 'derail #5 ... | stage: 12: Gym 4 — Flannery (Fire) | map (0, 27)'. No other run's final 5-derail streak contains this signature: all complete debug logs were checked.
* Blacklist does not stick: `[MAINTAIN] ABANDONED ... ROUTE111(25, 55)` appears 19 times in P1-...-202738.log and 45 times batch-wide (P1-152025:4, P2-114734:4, P2-155401:2, P2-170218:3, P2-210840:1, P3-134903:8, P3-143951:4). The MAINTAIN start is re-issued each cycle, e.g. 'f2377943 [MAINTAIN] start Numel ... on ROUTE111(25, 55)' and 'f2387688 [MAINTAIN] start Numel ... on ROUTE111(25, 55)'. This contradicts the 'measured max 1 per run ... self-healing via _note_training_unreachable' claim in the story_mode.py:2710-2714 comment.
* Recovery of the Lavaridge variant each cycle (P1 202738): 'f2383488 [STEP] 'Story: descending Jagged Pass to Lavaridge...'', then a stuck dump with scripts=['Route112_CableCarStation_EventScript_RideCableCar'], then 'f2386028 [STEP] 'Story: reached Lavaridge Town!''. Across 53 Lavaridge events, the median time from BLOCKED to 'reached Lavaridge Town' was 2,840 frames.
* Mauville variant (P1-...-152025.log): 'f2471969 [MAINTAIN] done pid=E3DBBCD8 L15->L20' (training on ROUTE117(31,16)) -> 'f2472800 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5) pos=(22, 5)' -> 'f2472934 [MAP] MAUVILLE CITY(10,5) -> MAUVILLE CITY(0,2) pos=(7, 8)' -> 'f2473024 [STORY] DERAIL #1: ... LavaridgeTown ... Source (22/6 @ MAUVILLE_CITY) and destination (7/8 @ MAUVILLE_CITY_POKEMON_CENTER_1F) are not on connected maps'.
* Variant B (P1-...-152025.log): 'f2367233 [BATTLE] ended (outcome=BattleOutcome.Caught)' (Numel counter on Fiery Path) -> 'f2375343 [MAP] FIERY PATH(24,14) -> ROUTE 112(0,27) pos=(26, 36)' -> 'f2375431 [STORY] DERAIL #1: ... LavaridgeTown ... Underlying error: Cannot reach LAVARIDGE_TOWN: it is not walkable from ROUTE112, and none of the 6 candidate warp route(s) start at a tile that can be walked to from here'. The dump shows pos=(11, 37).
* Variant C (P3-...-124727.log): 'f3430801 [hb] ... controllable=True map=ROUTE 111(0,26) pos=(29, 88)' -> 'f3433858 [STORY] DERAIL #1: ... FortreeCity ... Navigation to (29, 87) @ (0, 26) made no progress (avatar stuck near (ROUTE111, (29, 88)))'. Decomp check (`gh api repos/pret/pokeemerald/contents/data/maps/Route111/scripts.inc`): 'Route111_OnLoad: call_if_unset FLAG_REGI_DOORS_OPENED, Route111_EventScript_CloseDesertRuins' and 'setmetatile 29, 87, METATILE_General_RockWall_SandBase, TRUE'. map_path.py:841 exempts a warp destination tile from collision: `elif not tile.accessible_from_direction[from_direction] and not (tile == destination_tile and tile.warps_to): return False`.
* Offline replay of the `_staged_progress_warp` scoring against sandbox-pokebot/cache/warp_graph_BPEE0.json (read-only; scratchpad scripts wg2.py/wg4.py). Top picks:
- ROUTE116->PETALBURG_CITY (here=3): 'd=3 exits=3 RUSTBORO_CITY(13, 30) -> RUSTBORO_CITY_FLAT1_1F(6, 7)'
- ROUTE117->LAVARIDGE (here=4): 'MAUVILLE_CITY(22, 5) -> MAUVILLE_CITY_POKEMON_CENTER_1F(7, 8)'
- ROUTE111->LAVARIDGE: 'ROUTE112(6, 46) -> JAGGED_PASS' then 'ROUTE112(28, 27) -> ROUTE112_CABLE_CAR_STATION(6, 11)'
- FALLARBOR->FORTREE: 'ROUTE113(33, 5) -> ROUTE113_GLASS_WORKSHOP(3, 8)'
- ROUTE112->FORTREE: 'ROUTE111(29, 87) -> DESERT_RUINS(8, 29)'
- ROUTE112->LAVARIDGE: here=1, so the cable car (d=2) is excluded.
For all three targets, `warp_candidates()` returns only doors located in the target town. `plan(RUSTBORO_CITY_FLAT1_1F, PETALBURG_CITY)` = [Flat1 (6,7) -> RUSTBORO_CITY (13,30)], which is the mat the bot is standing on.
* Offline replay of the corrected path: from RUSTBORO_CITY with visited={ROUTE116, FLAT1_1F, RUSTBORO}, the top staged pick is 'ROUTE104(10, 30) -> PETALBURG_WOODS(14, 5)', the correct Woods door. So a bounce fix would give the Petalburg walk a real next leg. Whether it then gets through the Woods is UNVERIFIED: the PETALBURG_WOODS '(14,5)->(26,5)' derail is the batch's top signature.

</details>
