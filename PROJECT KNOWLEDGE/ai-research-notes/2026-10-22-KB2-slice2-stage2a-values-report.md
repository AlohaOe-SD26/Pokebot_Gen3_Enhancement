# KB2 slice 2 stage 2a, FIX ROUND 3, STAGE 3a (the values): builder report, 2026-10-22

## Verdict
Items 1-7 are BUILT and checked on the real output. test_kb2.py is NOT touched (stage 3b; it is known red). The chapter
packs are not regenerated and run_gates was not run (stage 3b). Nothing is committed.

‼ THE HEADLINE RISK (read first): the strict SOLE-WRITER rule (item 1, "NO writer anywhere ... other than the gift's
own continuation") moves 62 records from once / until_received to `unknown`. 13 of them are golden "known answers"
(HM Surf, Facade, the Mirage and Desert Underpass fossils, Steven's Dive, the Trick House Entrance tent, the Favor
Lady, ReturnGoods, Beldum, the SS Ticket, the Treecko doll, Rock Tomb). Spec-2 item 1 (which "still governs") names
Beldum `until_received` as a known answer, so the two specs CONTRADICT each other on Beldum. I followed spec-3's
explicit rule (newer, and its WHY says more `unknown` is the expected cost) and did NOT improvise a relaxation. The
golden entries now assert `unknown`, keep the hand-read value as `truth`, and pin the outside writer that makes the
rule say unknown (`other_writer`, checked against the record's dev.other_writers and the pin). The coordinator should
rule on it. A mechanical refinement that the verifier could also re-check: "a writer outside the continuation that
writes ONLY the blocking value (a `setflag` of a flag the path tests unset) cannot re-arm"; it would recover the gym
"2" TMs, the dolls, the bikes and the fossils, but it is NOT what the spec says, so it is not built.

## Files changed (working tree, uncommitted)
- `ai_player/gates/extract_items.py`
- `ai_player/knowledge/world/items_gifts.json` (regenerated)
- `ai_player/gates/verify_world.py`
Scratch: `kb2s2/fix3a-changes.txt` (every changed record, round 2 -> now). The work dir `work-fix3a/` is deleted.

## Measured (each after the last source edit)
- `py -3.12 ai_player/gates/extract_items.py --check` -> `[KB2-ITEMS] CHECK OK: items_gifts.json identical to a fresh
  extraction` (8.9 s real). A determinism check, not a replication.
- write: `gifts 176, marts 33, tm_hm 58, purchases 13, dead 5, excluded 10, when null 120`.
- `py -3.12 ai_player/gates/verify_world.py` -> `[VERIFY-WORLD] PASS: 0 mismatches (every record; checked {...
  'items': 274, ... 'items_golden': 40, ...})` (3.9 s real).
- `py -3.12 ai_player/gates/verify_world.py --selftest` -> last lines `[PASS] S2 FAULT (gw): ... reported` /
  `[VERIFY-WORLD] SELFTEST PASS`.
- Plants, all 26 in one process (7.4 s for the first 24; d3 + gw 3.4 s), each `ok=True lines=1` (its own line, one
  line): e, g, h, h2, i, j, k, l, m, n, o, p, q, a1, a2, a3, a4, a5, a6 (moved to the Lava Cookie: "a money 200
  possession check on every path, but `when` ... does not name it"), a7 ("until_received, but dev.blocked_by names
  no blocking flag/var a scan can check"), a8, NEW a7s ("until_received, but FLAG_RECEIVED_TM_BULK_UP has a writer
  outside its own continuation: script data/maps/DewfordTown_Gym/scripts.inc:174"), NEW a9 ("'no condition', but
  every path tests a value the gift itself writes that is FALSE at new game ..." on Rusturf), NEW a10 ("a special the
  verifier has not read (ShowEasyChatScreen) runs on the way in, but `when` is 'after badge 1'..."), NEW d3 (a Shoal
  shell said repeatable: the daily-re-arm check), NEW gw (a golden `unknown` record whose outside writer is gone).
- SPECIAL_EFFECTS load-bearing (item 3): every one of the 68 entries removed in turn, in-memory build compared:
  `entries 68, unused 0` (93 s, 8 workers). Smallest: 9 entries change exactly 1 record each.

## Counts (176 gifts), round 2 -> now
- repeat: once 60 -> 28; until_received 79 -> 41; daily 19 -> 27; repeatable 12 -> 11; weekly 2 -> 2;
  unknown 4 -> 67.
- when: no condition 49 -> 39; worded 30 -> 39; null 97 -> 98.
- 73 records changed: repeat only 61, repeat+when 10, when only 2, exclusive_with 0.
  repeat moves: once -> unknown 32; until_received -> unknown 30; until_received -> daily 8 (the Shoal salt/shells);
  repeatable -> unknown 1 (Slateport berry-powder vendor: an untabled special, DisplayBerryPowderVendorMenu, on its
  way in forbids the open-path repeatable). Full list: `kb2s2/fix3a-changes.txt` (lines `CH`).
- Why the unknowns (other writers by kind, records may count twice): script setflag 33, setvar 32, a trainer flag
  (not a name) 8, clearflag 6, removeobject 6, addvar 6, copyvar 6, special states (Favor / Quiz Lady) 2, C mentions
  (pokenav_match_call_data.c, lottery_corner.c, field_specials.c, field_tasks.c, record_mixing.c) 9.

## The known answers
- 8 Shoal gifts: `daily` (REARM), when "each new day it comes back, but only once you talk to the Shell Bell man in
  the cave's entrance room (he puts the day's shoal items back)".
- Contest Lobby counter Luxury Ball: `unknown` (other writer contest_hall.inc:1105). Contest Hall ball: `repeatable`
  (REARM VAR_CONTEST_HALL_STATE). Glass flute / decor: `repeatable` (open path, own :195 / :285).
- Exp Share: `unknown`, dev.c_uses "FLAG_RECEIVED_EXP_SHARE named by C code at src/pokenav_match_call_data.c:183".
- GivePrizeFromEarlier: when null, dev.tests ["VAR_POKELOT_PRIZE_ITEM ne ITEM_NONE"], repeat unknown.
- QuizLadyRecordCustomQuizData: `writes STATE_QUIZ_AUTHOR QUIZ_AUTHOR_PLAYER` (lilycove_lady.c:554, read :383/:386).
- Favor Lady: when "...you have not given her an item yet (she takes only one); the one item you give her is her
  single favourite thing for her request (she takes only one item from you, and only her favourite one earns her
  prize); ..." (no 5-item plan). repeat unknown (a SPECIAL_STATES state is no name a scan can re-check).
- Cozmo's TM: until_received (FLAG_RECEIVED_TM_RETURN sole), when "the giver is not there at first: they appear later
  in the story; needs 1 Meteorite". Quiz Lady: when null (accepted).
- Castform: when null (MAP_CONDITIONS "Route119_WeatherInstitute_2F").
- Deep Sea pair: still until_received (FLAG_EXCHANGED_SCANNER sole).

## Tables (all cited, every cite checked by check_cites at build time; the verifier's own by s2_table_cites)
REARM (extractor):
| name | decides | cites |
|---|---|---|
| FLAG_RECEIVED_SHOAL_SALT_1..4, _SHELL_1..4 | daily | src/clock.c:53, src/field_specials.c:1420, ShoalCave_LowTideEntranceRoom/scripts.inc:22, :90, and :82..:89 (one per flag) |
| VAR_CONTEST_HALL_STATE | repeatable | data/scripts/contest_hall.inc:181, data/maps/ContestHall/scripts.inc:58 |

C_RANGES (extractor, by numeric id; effect -> RANGE_DECIDES):
| key | members | effect | cites |
|---|---|---|---|
| new game flags / vars | all | start (never a writer) | src/event_data.c:34, :35, src/new_game.c:167 |
| daily flags | DAILY_FLAGS_START..END | daily | src/event_data.c:52, src/clock.c:44 |
| temp flags / temp vars | TEMP_FLAGS_START..END, TEMP_VARS_START..END | map_entry -> repeatable | src/event_data.c:41, :42, src/overworld.c:798 |
| trainer flags | TRAINER_FLAGS_START..END | none | src/battle_setup.c:1249, :1264, :1269 |
| match call registrations | TRAINER_REGISTERED_FLAGS_START + REMATCH_TABLE_ENTRIES | none | src/pokenav_match_call_data.c:1160, src/battle_setup.c:1748, :1760 |
| decoration flags | FLAG_DECORATION_1..14 | none | src/decoration.c:1291, src/secret_base.c:605, :649 |
| hidden item flags | prefix FLAG_HIDDEN_ITEM_ | none | src/field_specials.c:937 |
| union room players | FLAG_HIDE_UNION_ROOM_PLAYER_1..8 | none | src/union_room_player_avatar.c:161, :166 |
| frontier symbols | FLAG_SYS_TOWER_SILVER..FLAG_SYS_PYRAMID_GOLD | none | src/frontier_util.c:1922, :1924 |
| object graphics vars | VAR_OBJ_GFX_ID_0..F | none | src/field_specials.c:2772, src/union_room_player_avatar.c:171, src/secret_base.c:603, src/decoration.c:1298 |
| objects removed by C | Birth Island rock, Tower lobby reporter | none | src/field_effect.c:3734, BirthIsland_Exterior/scripts.inc:69, src/tv.c:3445 |
Plus WRITER_CMDS (10 mnemonics, each cited to its ScrCmd line) and REMOVEOBJECT_SETS (event_object_movement.c:1394).
CITED_READS is empty by choice (documented). Verifier's own: S2_RANGES (9, by name), S2_DAILY_SYS (clock.c:53,
field_specials.c:1420), S2_SPECIALS (68, each at its C definition), S2_REARMED (contest_hall.inc:181, ContestHall:58).

SPECIAL_EFFECTS changes (68 entries, all load-bearing):
| entry | was | now | cites |
|---|---|---|---|
| QuizLadyRecordCustomQuizData | inert | writes STATE_QUIZ_AUTHOR QUIZ_AUTHOR_PLAYER | lilycove_lady.c:547, :554, :386 |
| QuizLadyPickNewQuestion | inert | writes STATE_QUIZ_AUTHOR QUIZ_AUTHOR_LADY | :516, :311, :382 |
| GetQuizAuthor | inert | writes STATE_QUIZ_AUTHOR (runtime) | :358, :378, :383 |
| BufferTrendyPhraseString | (untabled) | inert | src/dewford_trend.c:290 |
| ShouldTryRematchBattle | (untabled) | inert | src/battle_setup.c:1839 |
New SPECIAL_READS GetQuizAuthor -> STATE_QUIZ_AUTHOR; SPECIAL_STATES STATE_QUIZ_AUTHOR (lilycove_lady.c:311, :397).
New SPECIALVAR_WORDS (GetFavorLadyState, READY) (lilycove_lady.c:143, :237, lilycove_lady.inc:14); the
IsFavorLadyThresholdMet words rewritten (lilycove_lady.c:237, :248, :250, :251, :270, lilycove_lady.h:13,
lilycove_lady.inc:15). New MAP_CONDITIONS Route119_WeatherInstitute_2F (:6, :12, :42, :60).

## Verifier rule-deletion diagonal (scratch copies, each guard's `if` made False; CONTROL = the real output)
| mutant | CONTROL | plants red | verdict |
|---|---|---|---|
| VM1 a7 deleted | 0 | a7, a7s | CAUGHT (both are a7's plants) |
| VM2 a9 deleted | 0 | a9 | CAUGHT |
| VM3 a10 way-in deleted | 0 | a10 | CAUGHT |
| VM4 a10 continuation deleted | 0 | none | SURVIVED the plants (no asserted record's continuation runs an unread special); STRENGTHENED: fault arm VM4g (healthy verifier, S2_SPECIALS without SetPacifidlogTMReceivedDay) -> CONTROL 2 mismatches (the Pacifidlog weekly TMs); VM4g+VM4 -> CONTROL 0. CAUGHT by that arm |
| VM5 S2_HAVE money alternative deleted | 0 | a6 | CAUGHT |
| VM6 daily re-arm clause deleted | 8 (the Shoal records) | all (control lines break the one-line rule) | CAUGHT by CONTROL (stronger than the d3 plant) |
| VM7 golden other_writer check deleted | 0 | gw | CAUGHT |
| VM10 control arm: s2_cont replaced by s2_after | 3 | all | CAUGHT by CONTROL (Petalburg Woods, Trick House End tents) |
| VM11 control arm: VAR_LAST_TALKED counted for every object | 2 | all | CAUGHT by CONTROL (Steven's Devon Scope, Secret Power) |
Not run as mutants (no plant can reach them; stage 3b): `why_has` golden check, `s2_table_cites` call, S2_ANSWER
split in s2_cond_kept, s2_item_sources (no ITEM: blocker is in the real output: the Deep Sea pair's sole blocker is
FLAG_EXCHANGED_SCANNER).

## Deviations from the spec
1. Item 1, "the gift's own continuation" = lines AFTER the gift line (its label's rest, branches, calls, falls, and a
   return in its own frame resuming after each call into it). A write before the gift line, even in the gift's own
   label, is an outside writer. This is the literal reading (e.g. the bikes: FLAG_RECEIVED_BIKE's other writer is
   MauvilleCity_BikeShop/scripts.inc:37, outside each bike gift's continuation).
2. Item 1, the C range effects `daily` / `map_entry` are allowed to DECIDE (daily / repeatable) when they are the
   only outside writers (RANGE_DECIDES). The spec names only REARM as deciding; the range table is cited and
   re-checkable, so I treated it as a cited hand table. No record at the pin uses map_entry; `daily` agrees with the
   existing daily-block override.
3. Item 1, ITEM:<X> blockers stay sole when the item has one source (kept from round 2); TRAINER: and SPECIAL_STATES
   blockers are never sole ("no name a scan can re-check").
4. Item 7 a10 is interpreted consistently with item 3: an unread special on the way in requires `when` null and no
   open-path `repeatable` (a REARM-read var, S2_REARMED, may still make it repeatable: the Contest Hall); on the
   continuation it requires repeat `unknown`. The literal "an asserted repeat" would contradict item 3 (once is allowed
   with an untabled trigger special: Steven's Devon Scope).
5. Item 3: GetQuizAuthor and QuizLadyPickNewQuestion were also not inert (they rewrite the quiz author); fixed with
   QuizLadyRecordCustomQuizData. Two specials were tabled (BufferTrendyPhraseString, ShouldTryRematchBattle) to keep
   the Sludge Bomb man's and Rock Tomb's `when` words; both pass the load-bearing test.
6. Item 4: the Favor Lady also gained a READY-state word rule ("you have not given her an item yet (she takes only
   one)"): without it her `when` turned null once the strict rule stopped dropping the READY test as a once-guard.

## Open risks
- The 62 new unknowns (see the headline): the strict rule is honest but loses true facts (gym leader TMs, HM Surf,
  Beldum). Coordinator ruling needed; the value-check refinement above is the cheapest mechanical fix.
- Tide: the Shoal Cave salt also needs low tide (separate low-/high-tide maps); `when` does not say so (not asked).
- The verifier's S2_SPECIALS is the same fact list as SPECIAL_EFFECTS (independently coded, not independently read).
- s2_before / s2_cont and the extractor's walks differ in detail; they agree on the real output (CONTROL 0) but a
  future decomp change could split them.

## For stage 3b: the new calls and branches to mutate (each a call-deleting mutant)
extract_items.py: continuation_refs (the `return` -> frame_callers branch; the in_call flag); sole_writer (ITEM:
branch, non-name branch, CITED_READS filter, REARM branch, RANGE_DECIDES branch, the final `sole` expression);
WriterIndex (WRITER_CMDS loop, removeobject loop incl. VAR_LAST_TALKED and other-var branches, members(), aliases(),
ranges_of()); name_ids / c_int; evidence() (the `trig` refusal of open-path repeatable; the sole / decided / others
split; the `len(decided) > 1` branch; rearm_words); repeat_of's trigger_specials call; trigger_specials (called-label
bodies); rearm_words (trigger_specials -> null; REARM words; 'no condition' replaced); holds_at_start (flag branch,
symbol via start_consts) and its calls in is_once_guard and once_guard; Graph.callee_producer and its two uses in
producer (plain call; opposite_call_ifs pair); the MAP_CONDITIONS Castform entry; SPECIALVAR_WORDS
(GetFavorLadyState, READY) and the rewritten IsFavorLadyThresholdMet words; table_cites' new rows (WRITER_CMDS,
REMOVEOBJECT_SETS, C_RANGES, REARM, CITED_READS).
verify_world.py: s2_rules_round2 a7 block (blocked_by empty; ITEM: count; FLAG/VAR outside writers; non-name), a9
block, a10 way-in (incl. called-label bodies) and continuation; s2_sole_tables (writer grep, getplayerxy,
removeobject + VAR_LAST_TALKED reach, rearmed_daily, alias, daily, start); s2_outside_writers (S2_RANGES branches);
s2_item_sources; s2_false_at_start (object, coord, set/unset, var ops, map_script_2/case); s2_cont / s2_frame_calls;
s2_target; the daily clause in verify_items; s2_golden other_writer / why_has; s2_table_cites call; S2_HAVE money /
coins / decor + s2_have_word; S2_ANSWER in s2_cond_kept. Plants to keep: a7s, a9, a10, d3, gw (and a6 on the Lava
Cookie); the strengthened arm VM4g (S2_SPECIALS minus SetPacifidlogTMReceivedDay -> 2 mismatches) belongs in
test_kb2 as the a10-continuation FAULT arm.
test_kb2 pins that change: the repeat / when counts above; the Favor Lady (now `unknown`); round-1 tests calling the
removed `after_gift` (unchanged since round 2).
