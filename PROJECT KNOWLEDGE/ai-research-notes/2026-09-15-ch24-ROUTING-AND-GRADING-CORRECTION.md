# §Ch24 — ROUTING, MAPPING, AND A GRADING CORRECTION THAT INVALIDATES THE QUEUE HEAD

> ⚠⚠ **THIS IS A NOTE, NOT TRUTH.** `ai-research-notes/00-READ-THIS-FIRST.md` governs. Where this
> note and an authoritative doc disagree, **the authoritative doc wins until the claim is verified
> here**. Everything below is tagged with how it was established, and the tags are load-bearing:
>
> * **[VERIFIED-BY-ME]** — I fetched the decomp file or read our own tree **in this session** and
>   quote what I saw. Build on these.
> * **[AGENT-DECOMP]** — a recon agent reports fetching the decomp and gives a path. Strong, and
>   still **NOT verified here**. Confirm before code depends on it.
> * **[AGENT-REPO]** — a recon agent reports reading our tree. Same caveat.
> * **[DISPUTED]** — two sources in our own tree disagree. ⛔ Do not build on either half.
>
> **Produced:** 2026-09-15, 5 parallel Claude subagents on 5 different angles (decomp mapping, our
> code's conventions, our own name vocabulary, an ADVERSARY told to refute the build spec, and
> prior-art/dead-ends). 0 errors, ~709k subagent tokens, 202 tool calls.
>
> ‼ **WHY A FRESH ROUND WAS RUN AT ALL, GIVEN 08-MISTAKES 2026-09-13.** That entry records a 9-agent
> workflow that re-derived an existing build spec and came back *less* accurate than it, because it
> never read this directory's index first. That warning is fair and I have no wish to repeat it.
> The difference here is the **adversarial angle**, which this project's own measured rules say is
> the one that produces information rather than a second guess: it returned **22 findings, and its
> single headline refutes the live `➡➡➡` NEXT ACTION in `04-HANDOFF.md`**. I then verified that
> headline myself against the decomp before writing it down. A round that changes what the next
> session does is not a re-derivation.

---

## A. ⛔⛔ THE CORRECTION THAT MATTERS: THE QUEUE HEAD'S GRADING SIGNAL IS BACKWARDS

`04-HANDOFF.md`'s live NEXT ACTION says: *"Grade per-room legs on `VAR_ELITE_4_STATE`, but grade
CHAPTER COMPLETION on `IS_CHAMPION`."*

**The first half is refuted. `VAR_ELITE_4_STATE` is written by the room-ENTRY script, never by a
victory.** A leg graded on it passes *the moment the bot walks through the door*, before the fight.

**[VERIFIED-BY-ME]** — `gh api repos/pret/pokeemerald/contents/data/maps/EverGrandeCity_SidneysRoom/scripts.inc`,
fetched and decoded in this session. Quoting what came back, unedited:

```
EverGrandeCity_SidneysRoom_OnFrame:
	map_script_2 VAR_ELITE_4_STATE, 0, EverGrandeCity_SidneysRoom_EventScript_WalkInCloseDoor
	.2byte 0

EverGrandeCity_SidneysRoom_EventScript_WalkInCloseDoor::
	lockall
	call PokemonLeague_EliteFour_EventScript_WalkInCloseDoor
	setvar VAR_ELITE_4_STATE, 1          <-- ON ENTRY. No fight has happened.
	releaseall
	end

EverGrandeCity_SidneysRoom_EventScript_Defeated::
	setflag FLAG_DEFEATED_ELITE_4_SIDNEY  <-- ON VICTORY. And there is NO setvar here.
	call PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles
	msgbox EverGrandeCity_SidneysRoom_Text_PostBattleSpeech, MSGBOX_DEFAULT
	release
	end
```

⇒ **`ELITE_4_STATE == 1` means "the bot is standing in Sidney's room". It does not mean "Sidney is
beaten".** This is precisely the vacuity shape `CLAUDE.md` names: *a check must assert something the
run does not already satisfy*. Graded this way, legs 5–8 would report PASS on a bot that walked in
and did nothing — and the failure would read as success.

**The per-room victory signal is `FLAG_DEFEATED_ELITE_4_<NAME>`** (set at the moment of victory, in
the `_Defeated` script quoted above). **[VERIFIED-BY-ME]** for Sidney; **[AGENT-DECOMP]** that
Phoebe / Glacia / Drake carry the identical `_Defeated` shape.

**⛔ THE BUILD-SPEC'S BLANKET BAN ON THOSE FLAGS IS TOO BROAD, AND THE BAN IS WHY THE WRONG SIGNAL
WAS CHOSEN.** The real constraint is narrower: `ResetEliteFour` clears them **on the whiteout path
and again on the final Hall-of-Fame win path**. It does **not** clear them between rooms. So:

| what you are grading | correct signal | why |
|---|---|---|
| "is the bot in room *k*" (a READOUT) | `ELITE_4_STATE` | written on entry — that is exactly what it means |
| "did the bot BEAT member *k*" (a LEG) | `DEFEATED_ELITE_4_<NAME>` | written on victory, survives until the gauntlet ends |
| "is the chapter DONE" | see §E — **[DISPUTED]** | `ResetEliteFour` wipes BOTH of the above on the win path |

‼ **AND `ELITE_4_STATE` NEVER REACHES 5.** **[AGENT-DECOMP]**: Drake's room sets it to 4 on entry,
and `EverGrandeCity_ChampionsRoom/scripts.inc` contains no `setvar VAR_ELITE_4_STATE` at all — so
during the Wallace fight it still reads 4, the same value as merely walking into Drake's room. Any
`state == 5` check is unreachable. ⚠ Not verified here; verify before writing a Wallace leg.

### A1. ‼ AND THE NAME IS WRONG IN THE SPEC — OURS HAS NO `VAR_` PREFIX

**[VERIFIED-BY-ME]** Our table calls it **`ELITE_4_STATE`** (var 156), not `VAR_ELITE_4_STATE`:

* `sandbox-pokebot/modules/data/event_vars/emerald.txt:157` → `156 ELITE_4_STATE`
* read with `get_event_var(name)` — `sandbox-pokebot/modules/memory.py:393`

⚠ `get_event_var` **returns `-1` for an unknown name** (**[AGENT-REPO]**, `modules/memory.py:393-397`).
That is *better* than `get_event_flag`'s silent `False`, because `-1` is not a plausible state value
— but only if the caller checks for it. **A predicate that compares `== 0` will read a typo'd name
as "not there yet", forever.** Use the same positive-control discipline the flags already demand.

---

## B. WHAT I VERIFIED MYSELF, THIS SESSION

Every row below I read in our own tree or fetched from the decomp. These are safe to build on.

| # | claim | evidence |
|---|---|---|
| B1 | `ELITE_4_STATE` is set on room ENTRY; the victory script sets a FLAG and no var | decomp `data/maps/EverGrandeCity_SidneysRoom/scripts.inc`, quoted in §A |
| B2 | our var is named `ELITE_4_STATE` (no `VAR_` prefix), var 156 | `modules/data/event_vars/emerald.txt:157` |
| B3 | `get_event_var(var_name)` exists | `modules/memory.py:393` |
| B4 | all four `DEFEATED_ELITE_4_*` flags exist in our table | `modules/data/event_flags/emerald.txt:1026-1029` (1275–1278) |
| B5 | `SYS_GAME_CLEAR` = 2148, `IS_CHAMPION` = 2175, `LANDMARK_POKEMON_LEAGUE` = 2228 — all present | `modules/data/event_flags/emerald.txt:1034`, `:1061`, `:1105` |
| B6 | every League room resolves as a map enum, group 16 | `modules/map_data.py:1037` (Sidney), `:1041` (Champion), `:1042` (Hall1), `:1047` (League 1F), `:1048` (Hall of Fame), `:1051` (League 2F) |
| B7 | `modules/story/pokemon_league.py` EXISTS — 1,439 lines, self-labelled "§Ch24 — THE POKÉMON LEAGUE" | file read; carries `heal_party_from_bag`, `teach_move_from_bag`, `scroll_to_tm_verified`, `use_item_on_party_member` |
| B8 | `story_mode.py` has **no Segment 24** — a grep for `pokemon_league\|ch24\|elite_four\|do_pokemon_league` returns ONE hit, a comment | grep over `plugins/custom_modes/story_mode.py` |
| B9 | **the whole E4 spine is uniform**: every one of the four rooms has entry warp **(6,13)**, exit warp **(6,2)**, its trainer at **(6,5)**, and **zero `coord_events`** | `gh api` on `data/maps/EverGrandeCity_{Sidneys,Phoebes,Glacias,Drakes}Room/map.json` |
| B10 | **the defeated trainer is never removed** — Sidney's `_Defeated` is `setflag` / `call SetAdvanceToNextRoomMetatiles` / `msgbox` / `release`, with **no `removeobject` and no `applymovement`** | `data/maps/EverGrandeCity_SidneysRoom/scripts.inc`, quoted in §A |
| B11 | **Wallace's object script is literally `'0x0'`** and his room has **zero `coord_events`** ⇒ there is no A-press target and no coord trigger; the fight starts from `OnFrame` | `data/maps/EverGrandeCity_ChampionsRoom/map.json` |
| B12 | halls 1/2/3/5 each expose FOUR warps — `(5,12)`, `(5,2)`, `(4,12)`, `(6,12)` — and all three of the y=12 ones point BACK to the previous room. Hall4 has only two: `(5,33)` and `(5,2)` | `gh api` on `data/maps/EverGrandeCity_Hall{1,2,3,4,5}/map.json` |
| B13 | ⭐ **League 1F has a REAL POKÉMON CENTER NURSE at (3,2) and a MART at (16,2)** — `EventScript_Nurse` calls `Common_EventScript_PkmnCenterNurse`; the mart sells Ultra Ball, Hyper Potion, Max Potion, **Full Restore, Full Heal, Revive**, Max Repel | `data/maps/EverGrandeCity_PokemonLeague_1F/{map.json,scripts.inc}` |
| B14 | ⭐ **every transition into League 1F does `setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE`** ⇒ a mid-gauntlet whiteout lands in that lobby, beside the nurse and the mart | same `scripts.inc`, `_OnTransition` |
| B15 | the door guard gates on **`FLAG_BADGE06_GET` ONLY** (a decomp comment says Winona's is the only skippable badge), then sets `FLAG_ENTERED_ELITE_FOUR`; afterwards it short-circuits to `_GoForth`. It also MOVES the player (`call_if_ge VAR_TEMP_0, 11` / `call_if_le VAR_TEMP_0, 8`) | same `scripts.inc`, `_EventScript_DoorGuard` |
| B16 | `FLAG_IS_CHAMPION` is set at `hall_of_fame.inc:2`, and `call ...ResetEliteFour` is five lines later in the SAME script ⇒ the spec's "set BEFORE the reset" is CONFIRMED | `data/scripts/hall_of_fame.inc` |

⇒ **B7 + B8 together are the real shape of the remaining work:** the §Ch24 *prep layer* is built; the
**gauntlet sequencer is not**. ⛔ Do not rebuild `pokemon_league.py`.

---

## C. ROUTING / MAPPING — THE WARP BACKBONE

✅ **[VERIFIED-BY-ME] — the whole chain below was re-fetched map-by-map in this session** via
`gh api repos/pret/pokeemerald/contents/data/maps/<MAP>/map.json`, reading each `warp_events[]`
array directly (array index = the `dest_warp_id` other maps refer to). The agent's table was
correct in every hop I checked. **Build on this.**

**The chain, door by door.** Every hop is `<map> warp#<i> at (x,y)` → `<next map> warp#<j>`:

```
EVER_GRANDE_CITY        (18,5)  ->  POKEMON_LEAGUE_1F #0 = (9,11)     [the fixture stands at (18,6), one tile south]
POKEMON_LEAGUE_1F  #2/#3 (9,1)/(10,1) ->  HALL5 #0 = (5,12)
HALL5              #1   (5,2)   ->  SIDNEYS_ROOM  #0 = (6,13)
SIDNEYS_ROOM       #1   (6,2)   ->  HALL1  #0 = (5,12)
HALL1              #1   (5,2)   ->  PHOEBES_ROOM  #0 = (6,13)
PHOEBES_ROOM       #1   (6,2)   ->  HALL2  #0 = (5,12)
HALL2              #1   (5,2)   ->  GLACIAS_ROOM  #0 = (6,13)
GLACIAS_ROOM       #1   (6,2)   ->  HALL3  #0 = (5,12)
HALL3              #1   (5,2)   ->  DRAKES_ROOM   #0 = (6,13)
DRAKES_ROOM        #1   (6,2)   ->  HALL4  #0 = (5,33)      <-- HALL4 is 11x34, the long corridor
HALL4              #1   (5,2)   ->  CHAMPIONS_ROOM #0 = (6,12)   <-- note 12, not 13: that room is 13 tall, not 14
CHAMPIONS_ROOM     #1   (6,2)   ->  HALL_OF_FAME  #0
```

**Uniform facts across the four E4 rooms** — 13×14 each; the trainer sprite stands at **(6,5)**,
`TRAINER_TYPE_NONE`, sight radius 0 (**no ambush** — the battle starts only when the bot faces the
sprite and presses A, via `trainerbattle_no_intro`); zero `coord_events`; the entry auto-walk ends
the player at **(6,7)**.

**The Champion's room is the exception at every step**: 13×**13**; entry warp at (6,12); the
auto-walk is `Common_Movement_WalkUp4`, `delay 40`, then `Movement_PlayerApproachWallace`, ending at
**(6,6)** with Wallace at (6,5); **Wallace's object script is `0x0` — there is NO A-press trigger at
all**, the fight starts from an `OnFrame` script gated on `VAR_TEMP_1 == 0`. ⛔ A sequencer that
walks up and presses A at Wallace will press into nothing.

**The door guards on League 1F MOVE THE PLAYER.** `EventScript_DoorGuard` reads the player's x and
then `call_if_ge VAR_TEMP_0, 11 → PlayerMoveToFrontFromRight` / `call_if_le VAR_TEMP_0, 8 →
PlayerMoveToFrontFromLeft`. The guards sit at (9,2)/(10,2) — not the (8,2)/(11,2) in `map.json` —
because an `OnTransition` `setobjectxyperm`s them while `FLAG_ENTERED_ELITE_FOUR` is unset.
⇒ **do not hardcode a post-guard tile; read the position back.**

---

## D. TRAPS A NAIVE SEQUENCER WILL HIT

All **[AGENT-DECOMP]** unless marked. Each is cited in the agent's return; none is verified here.

1. ⚠⚠ **DEMOTED 2026-09-16 — THIS WAS RANKED #1 AND IT IS NOT THE KILLER.** An adversarial
   build-prep pass found that **our pathfinder already routes around NPCs**, so the standing
   sprite is a detour, not a wall. ⛔ **THE REAL FIRST-DRIVE KILLER IS §D''** — the exit door
   exists only in RAM and our pathfinder reads ROM. The fact below is still TRUE, it is just
   not the top risk, and ranking it there would have sent the first fix at the wrong target.
   *(original, and still verified:)* **THE DEFEATED E4 MEMBER STAYS STANDING AT (6,5) AND SITS ON THE STRAIGHT
   LINE.** I fetched both halves: `map.json` puts the trainer at **(6,5)** with the exit warp at
   **(6,2)**, and `_Defeated` (quoted in §A) contains **no `removeobject` and no `applymovement`**. The bot ends at (6,7)/(6,6) and the exit
   door is (6,2) — **directly through the sprite**. The path out must go around. *(This is the single
   most likely cause of a first-drive hang, and it is not in the build spec.)*
2. **The victory script's ORDER is flag → metatiles → message.** `setflag` runs FIRST, then
   `SetAdvanceToNextRoomMetatiles` (which itself begins with `applywaitmovement …Common_Movement_Delay32`),
   and only THEN the `msgbox … MSGBOX_DEFAULT`. ⇒ the flag is true *while a message is still
   pending*; a leg that sees the flag and immediately walks will fight the text printer.
3. **The door-opening script rewrites TWELVE tiles, not two** — (6,1) and (6,2) made passable, plus
   ten "spotlight" tiles along y=2 at x = 0,1,2,3,4,8,9,10,11,12. A cached collision grid must be
   re-read after a victory.
4. **Wallace's aftermath is ~12 msgboxes, not two.** Post-battle speech, two rival exchanges, Birch's
   intro, `ProfBirch_EventScript_RatePokedex` (two more), Birch's congratulations, "come with me",
   "wait outside", rival congratulations. The build spec's "exactly two `WaitForButton`-gated
   dismisses" is far short.
5. **⛔ THE HALL OF FAME HAS A BLOCKING A-PRESS THAT THE PROJECT'S OWN DISMISS RULE CANNOT SEE.**
   `Task_Hof_ExitOnKeyPressed` waits indefinitely on raw `JOY_NEW(A_BUTTON)` with **no text printer
   involved**. The standing rule — *dismiss only when `get_text_printer(0).state == WaitForButton`,
   never on a frame count* — detects nothing here and the bot will hang. This needs a deliberate,
   separately-justified exception, not a quiet one.
6. **The game FORCE-SAVES the full save slot at the Hall of Fame**, unprompted
   (`Task_Hof_TrySaveData` → `TrySavingData(SAVE_HALL_OF_FAME)` → `WriteSaveSectorOrSlot(FULL_SAVE_SLOT,…)`),
   and `GameClear()` calls `HealPlayerParty()` first.
7. **⛔⛔ AFTER THE CREDITS THE GAME CALLS `SoftReset(RESET_ALL)` AND NEVER RETURNS CONTROL.**
   `Task_Hof_HandleExit` → `StartCredits()` → `Task_CreditsSoftReset`. On a FIRST clear the credits
   **cannot be sped up** — the B-button 2× path is gated on `gHasHallOfFameRecords`, which
   `GameClear()` sets FALSE on a first clear. ⇒ **§Ch24 cannot "finish and hand back" the way every
   earlier chapter does.** Whatever the completion predicate is, it must be read *before* the
   credits roll, and the chapter's end-of-run behaviour needs designing, not assuming.
8. **Roster hazards, none handled in our battle code:** Sidney's lead Mightyena L46 knows **ROAR**
   (forced switch — a grep of `modules` for roar/whirlwind finds only the unrelated
   `TemporaryStatus.Uproar`); Glacia's Walrein L53 has **SHEER COLD** (OHKO); Glacia's Glalie L52 has
   **EXPLOSION**.
9. **Actual opposition levels** (refuting the spec's unsourced "~L75"): Sidney 46/48/46/48/49,
   Phoebe 48/49/50/49/51, Glacia 50/50/52/52/53, Drake 52/54/53/53/55, Wallace 57/55/56/56/56/58 —
   **26 opposing Pokémon**. Our party is L60. ⇒ the level gap is not the blocker the spec implies.
10. **`party_is_gauntlet_ready()` is not callable as the spec writes it** (**[AGENT-REPO]**,
    `modules/story/overworld_items.py`): the real signature takes a REQUIRED positional list of
    targets, and its body is `all(… for m in targets)` — **vacuously True on an empty list**.

---

## D'. ⭐⭐ THE FINDING NOTHING IN OUR TREE RECORDS: LEAGUE 1F IS A FULL RECOVERY POINT

✅ **[VERIFIED-BY-ME].** The standing user ruling (2026-09-04) — *"healing via a nurse is not
possible here but items can be used in and out of battle"* — **is correct, and it is about the
GAUNTLET.** I verified the gauntlet half: every E4 room's only object is its trainer, and halls
1–5 have `objects: []`. There is no nurse past the guards.

**But the LOBBY is not the gauntlet, and the lobby has everything:**

```
EverGrandeCity_PokemonLeague_1F_OnTransition:
	setrespawn HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE     <-- whiteout lands HERE
	setflag FLAG_LANDMARK_POKEMON_LEAGUE
	call_if_unset FLAG_ENTERED_ELITE_FOUR, ..._EventScript_GuardsBlockDoor

EverGrandeCity_PokemonLeague_1F_EventScript_Nurse::              <-- object at (3,2)
	setvar VAR_0x800B, LOCALID_LEAGUE_NURSE
	call Common_EventScript_PkmnCenterNurse                      <-- the STANDARD full heal

EverGrandeCity_PokemonLeague_1F_Pokemart:                        <-- clerk at (16,2)
	ULTRA_BALL, HYPER_POTION, MAX_POTION, FULL_RESTORE, FULL_HEAL, REVIVE, MAX_REPEL
```

⇒ **Three consequences the build should take account of, none of them recorded elsewhere:**

1. **A mid-gauntlet whiteout is recoverable ON THE SPOT.** `setrespawn` puts the bot back in this
   lobby — not in Mauville, not across the region — standing beside a free full heal and a mart
   whose stock list is almost exactly the gauntlet shopping list.
2. **The pre-gauntlet heal and re-stock need no travel at all.** Whatever `#24-e4healing` step 2
   ends up doing BETWEEN rooms, the step BEFORE room 1 is a nurse interaction in the same map the
   bot is already standing in.
3. **It bears directly on the open post-whiteout MONEY policy** (`06-DECISIONS-LOG.md` 2026-09-10,
   still unresolved): a whiteout halves money, but the heal here is FREE, so only the consumables
   have to be re-bought. The policy question is narrower than it was framed.

⚠ **NOT YET verified live in our harness** — this is decomp, not a drive. Two things in particular
are assumptions until measured: that our nurse-interaction code drives *this* nurse as it drives an
ordinary Pokémon Center one, and that the guards let the bot back OUT to the lobby mid-gauntlet.
⛔ The second is the one that could be false and expensive: **the gauntlet may be one-way.** Nothing
I read forbids walking back south through the hall warps, but nothing I read confirms it either.

---

## D''. ⛔⛔ THE PREREQUISITE — AND IT IS **KI-74**, ALREADY OPEN, NOT A NEW DISCOVERY

> ⛔ **FRAMING CORRECTED 2026-09-16, TWICE OVER, AND BOTH CORRECTIONS MATTER MORE THAN THE FINDING.**
> This section was first written as though it had found something new. It has not:
> * **This is `KI-74`** (`05-KNOWN-ISSUES.md:1276`) — *"`setmetatile` tiles are INVISIBLE to the
>   shared map model"* — filed 2026-08-13, **STILL OPEN**, and it has **already cost a drive**
>   (§Ch21 leg 3 jammed at `SOOTOPOLIS_CITY (31,42)` on 2026-09-01).
> * **The oracle already exists**, and `sootopolis.py:871`'s own docstring states this defect better
>   than my §D'' did: *"Every tile reader we own ultimately dereferences a LAYOUT's blockdata
>   pointer, which lives in ROM… The game walks on `sBackupMapData` in RAM… ⇒ USE THIS AS THE ORACLE
>   FOR 'CAN THE BOT ACTUALLY STEP THERE', never a `get_map_data` read."*
> * An offline instrument exists too: **`tools/story-dev/probe_live_mapgrid.py`**, which diffs the
>   ROM view against the live grid for a given save + map, with a CALIBRATED border offset.
> ⇒ **The genuinely new part is narrow and worth exactly its own sentence: the Elite Four doors are
> a NEW SITE of KI-74, and §Ch24 cannot be built without hitting it.** Everything else here was
> already known to this project and I re-derived it. *(Two sessions running, I have over-claimed
> novelty; the lesson is in `08-MISTAKES.md` 2026-09-16.)*

### ✅ THE ROM HALF IS NOW MEASURED — AND IT SURVIVED A DELIBERATE REFUTATION ATTEMPT

An adversarial review asked the one question that could have collapsed this entire plan: *what if
the ROM layout ALREADY marks the door tiles walkable?* Then our planner would route through them
unaided and the §Ch24 build order would have been reorganised around a defect that does not exist.

**`tools/story-dev/probe_e4_door_rom_view.py` answers it offline, without entering the rooms** — the
ROM layout is static, so `get_map_data` can be asked about any map from any save state. Measured on
`post_ch24_atdoor.ss1`, all five gauntlet rooms:

```
SIDNEY / PHOEBE / GLACIA / DRAKE / CHAMPION
    DOOR TILES                                  (6,1)=1   (6,2)=1     <- 1 = BLOCKED
    C1  (6,7) the player's auto-walk end tile   0  PASS   (must be walkable)
    C2  (0,0) the room corner                   1  PASS   (must be a wall)
    C3  (6,5) the trainer's tile                0          reported, not asserted — an NPC is an
                                                           object, not collision
```

⇒ **The premise holds: our ROM-reading planner sees the exit door as a WALL in all five rooms.**
The controls are what make that a measurement rather than an assertion — a reader that called the
player's own standing tile impassable would have invalidated every verdict, and it does not.

### ⭐⭐ THE FIRST MEASUREMENT DOES **NOT** NEED A VICTORY — THE ENTRY SEAL DIVERGES ON ENTRY

✅ **[VERIFIED-BY-ME] at the decomp, 2026-09-16.** `ScrCmd_setmetatile` (`src/scrcmd.c:2035-2049`)
adds `MAP_OFFSET` to x/y and then calls `MapGridSetMetatileIdAt(x, y, metatileId)` when its 4th
argument is FALSE, or `…(metatileId | MAPGRID_IMPASSABLE)` when TRUE. And
`MapGridSetMetatileIdAt` (`src/fieldmap.c:357-365`) is:

```c
gBackupMapLayout.map[…] &= MAPGRID_ELEVATION_MASK;          // keeps ONLY elevation
gBackupMapLayout.map[…] |= metatile & ~MAPGRID_ELEVATION_MASK;   // id AND collision from the arg
```

⇒ **two consequences, both load-bearing:**
1. **Collision IS a valid oracle for the E4 door.** The door write passes `FALSE`, so no impassable
   bit is ORed in and the mask has already cleared the old one ⇒ after the victory the live
   collision at (6,2) becomes **0**, against ROM's measured **1**. *(This is not automatic for every
   `setmetatile` — `KI-73` records that a map rewriting one PASSABLE tile to another changes the
   metatile ID and NOT the collision, which is why `_live_metatile_grid` exists. Our door happens to
   be the case where collision moves; read the metatile ID too, for identity.)*
2. ⛔ **A SEALED TILE READS COLLISION `3`, NOT `1`.** `MAPGRID_IMPASSABLE` sets BOTH collision bits.
   Any check written as `== 1` will miss a seal.

⭐⭐ **AND THE PAYOFF: THE ENTRY SEAL IS A ROM-vs-LIVE DIVERGENCE THAT IS ALREADY TRUE BEFORE THE
FIGHT.** `WalkInCloseDoor` runs on ENTRY and seals (5..7, 12) and (5..7, 13) with `TRUE`. Those tiles
are the room's entry WARP in the ROM layout — walkable. So the moment the bot stands in Sidney's
room, ROM and live already disagree at six tiles, with no battle involved.
⇒ **THE FIRST MEASUREMENT NEEDS A SAVE TAKEN ON ENTRY, NOT AFTER A VICTORY.** Walk in, save, run
`probe_live_mapgrid.py <save> EVER_GRANDE_CITY_SIDNEYS_ROOM`, and the entry seal should appear in
the "we think open, the game says wall" column. That is:
* a far cheaper drive (no battle, no item use, no faint handling, no win condition);
* a **positive control for the whole mechanism** — if the seal does NOT show up, the live reader or
  the offset is wrong and every later door verdict would have been worthless;
* and it de-risks the victory measurement, which can then be a second save from the same drive.

‼ **THIS IS THE ROM HALF ONLY, AND SAYING SO IS THE POINT.** It does not show what the LIVE grid
says after a victory. That needs a save taken AFTER beating a member — which does not exist yet —
and then `probe_live_mapgrid.py <save> EVER_GRANDE_CITY_SIDNEYS_ROOM`. The decomp makes the outcome
very likely (`setmetatile 6,2,…,FALSE` sets impassable FALSE), but *very likely* is precisely the
kind of claim this project requires to be driven rather than reasoned.



✅ **[VERIFIED-BY-ME], 2026-09-16, both halves.** This supersedes §D1 as the top risk and it
**reorders the build**: writing the sequencer first would fail on the first drive for this reason.

**Half 1 — the door is a RUNTIME write.** `data/scripts/elite_four.inc`, fetched and read:

```
PokemonLeague_EliteFour_SetAdvanceToNextRoomMetatiles::      (runs ON VICTORY)
	setmetatile 6, 1, METATILE_EliteFour_OpenDoor_Frame,   FALSE     <- impassable = FALSE
	setmetatile 6, 2, METATILE_EliteFour_OpenDoor_Opening, FALSE
	... ten spotlight tiles at y=2 ...
	special DrawWholeMapView
```

**Half 2 — our PATHFINDER reads ROM, and caches it forever.** `modules/map.py:748-755`: the
layout is fetched through `map_layout_pointer` (a ROM pointer) and stored in
`_map_layout_cache[rom][map]`, which is only ever populated once per map and never invalidated.

> ⛔⛔ **CORRECTION, 2026-09-16, by a Tier 2 cold-start audit.** This paragraph originally ended:
> *"A grep of `sandbox-pokebot/modules/` for `gBackupMapLayout` returns nothing but the symbol
> tables — no module code reads it."* **THAT IS FALSE, AND IT WAS MY OWN GREP THAT LIED TO ME:** I
> ran it with `| head -5`, and the five `modules/data/symbols/*.sym` hits consumed the entire
> output. I read a TRUNCATED result as an ABSENCE and then published it as `[VERIFIED-BY-ME]`.
> ‼ **Never conclude absence from a truncated grep. `head` answers "show me some"; it never answers
> "is there any".** Use `-c`, or exclude the noisy path, or count first.
> ⭐ **AND THE TRUTH IS BETTER NEWS THAN THE ERROR:** the live-grid reader **already exists**, built
> 2026-09-02 for the §Ch21 Sky Pillar crack floors — *the identical shape*, a runtime tile write
> invisible to our ROM-cached grid:
>   * `modules/story/sootopolis.py:871` `_live_collision_grid` — *"Collision per LOCAL tile, read
>     from `gBackupMapLayout` — THE GRID THE GAME ITSELF WALKS ON"*, and `:939` the METATILE-ID
>     sibling. Both carry the constraint that matters here: ⛔ *"ONLY VALID FOR THE MAP THE AVATAR IS
>     CURRENTLY STANDING ON"* — which is fine for an E4 room, where the bot is standing in it.
>   * `modules/story/early_game.py:4113` already states the problem in a comment — *"in the engine's
>     LIVE grid (`gBackupMapLayout`, rewritten by `setmetatile`)"* — and `:4147`/`:4349` read it.
> ⇒ **Do NOT build a live-grid reader from scratch.** The §Ch24 door fix is most likely a REUSE of
> `sootopolis.py`'s reader at the moment of the door query, not new machinery.

⇒ **`setmetatile` writes the RAM map (`gBackupMapLayout`); our tile grid comes from ROM and is
cached permanently. The opened door is therefore INVISIBLE to `calculate_path`, in every room, on
every victory.** A leg that beats Sidney and then asks the pathfinder for a route to (6,2) will be
told there is no path — correctly, according to a grid that is stale by design.

‼ **AND THE SAME BLINDNESS HAS A SECOND FACE:** the ENTRY script seals the way back —
```
PokemonLeague_EliteFour_EventScript_WalkInCloseDoor::        (runs ON ENTRY)
	setmetatile 5,12 / 6,12 / 7,12 -> EntryDoor_ClosedTop,    TRUE   <- impassable = TRUE
	setmetatile 5,13 / 6,13 / 7,13 -> EntryDoor_ClosedBottom, TRUE
```
⇒ ⭐ **THE GAUNTLET IS ONE-WAY, AND THIS ANSWERS §D''s OPEN QUESTION.** The bot cannot walk back to
the League 1F lobby to use the nurse. Whatever healing happens between rooms must come from the BAG
— which is exactly `#24-e4healing` step 2, and it is now a hard requirement rather than a nicety.
*(Our pathfinder is equally blind to this seal, in the opposite direction: it will believe the entry
is still open. A "walk back and heal" fallback would not fail loudly — it would path into a wall.)*

### ⇒ THE BUILD ORDER THIS FORCES
1. **Solve the door first.** Options, none yet chosen: read the tile from `gBackupMapLayout` at
   runtime; invalidate `_map_layout_cache` on a metatile-changing script; or bypass the pathfinder
   for these six doors and drive the warp directly with a fixed movement (the rooms are uniform —
   (6,7) -> (6,2) is a straight column, and §D1's sprite is the only thing on it).
2. ⛔ **Do NOT start the sequencer until a probe has walked one opened door.** That is the cheapest
   possible falsification of everything above, and it is one drive.

---

## E. OPEN CONTRADICTIONS — ⛔ DO NOT BUILD ON EITHER HALF

**E1. The completion predicate. THREE of our own documents disagree.**

* `chapters.py` **already ships** Chapter 24 graded on **`SYS_GAME_CLEAR`** (**[AGENT-REPO]**).
* the BUILD-SPEC's 2026-09-14 addendum says grade on **`IS_CHAMPION`**.
* the 2026-09-04 routing note says *"`FLAG_IS_CHAMPION` gates only link/trade compatibility — it is
  NOT the game-clear marker. Grade §Ch24 on `FLAG_SYS_GAME_CLEAR`."*

**[AGENT-DECOMP] dissolves the *stated* reason but not the choice:** both are set inside the SAME
Hall-of-Fame `OnFrame` script, nine lines apart — `setflag FLAG_IS_CHAMPION` via
`…SetGameClearFlags`, and `FlagSet(FLAG_SYS_GAME_CLEAR)` inside `special GameClear`. So the
addendum's justification ("IS_CHAMPION is set BEFORE the reset, SYS_GAME_CLEAR only at the Hall of
Fame") is **not a discriminator — they are both at the Hall of Fame**. ⇒ **the cheapest correct move
is to keep what `chapters.py` already ships (`SYS_GAME_CLEAR`) and DELETE the addendum's
instruction**, rather than churn the registry. ‼ But read both scripts live before deciding — and
note trap D7: whichever flag is chosen must be read before `SoftReset`.

**E2. Are the halls' side tiles really backward warps?**

* our BUILD-SPEC addendum (2026-09-13) says **YES**: halls 1/2/3/5 have warps at (5,12), (4,12),
  (6,12), so any lateral nudge while healing silently undoes a cleared room.
* the adversary says **UNCONFIRMABLE AS STATED**: it read the warp *table*, which only proves a
  destination exists. A warp fires only if the tile's **metatile BEHAVIOR** is a warp behavior —
  `TryStartWarpEventScript` / `TryArrowWarp` / `TryDoorWarp` all gate on
  `IsWarpMetatileBehavior` / `IsArrowWarpMetatileBehavior`. It also notes `pokemon_league.py`'s own
  header already says this.

⇒ **[DISPUTED]**. The conservative behaviour (do not step sideways in a hall) costs nothing and is
already assumed, so **keep it** — but do not write down either explanation as fact. The decisive
test is a live read of the metatile behaviour at (4,12)/(6,12) in a hall, which no one has run.

---

## F. DO NOT REBUILD / DO NOT RE-ASK

* **`modules/story/pokemon_league.py`** — the §Ch24 prep layer, 1,439 lines, exists and is partly
  driven-passing. **[VERIFIED-BY-ME]**
* **`chapters.py`'s Chapter 24 registry entry** — exists. **[AGENT-REPO]**
* **`KI-94`** (the fixture/Fly blocker) — RESOLVED 2026-09-14.
* **`#24-e4healing` steps 1, 3, 4** — DONE; step 3 driven live and promoted; step 4 measured and
  answered *do not raise the threshold*. Only **step 2 (heal between rooms)** remains, and it is
  blocked on the sequencer that does not exist.
* **Three §Ch24 entry-marker designs are already killed** with evidence in `06-DECISIONS-LOG.md`.
* **Standing user ruling (2026-09-04):** *"the elite 4 is a gauntlet … healing via a nurse is not
  possible here but items can be used in and out of battle while in here to heal."*
* **`MAX_ITEM_USES_PER_BATTLE = 4`**, and a fresh strategy instance per fight resets it — up to 20
  in-battle heals across the five fights. Measured, not assumed.
* **Balls are blocked in trainer battles** and no interior League map has an encounter table ⇒ the
  catching directive cannot apply inside the gauntlet.
* **Open and unresolved:** the post-whiteout **money / re-stock policy** (a mid-gauntlet whiteout
  halves money). Flagged in `06-DECISIONS-LOG.md` 2026-09-10; no later ruling found.

---

## G. WHAT THE NEXT SESSION SHOULD DO FIRST

1. **Fix the grading signal before writing any leg** — §A. This is done in `04-HANDOFF.md` as part of
   the same commit that created this note; if the queue head still says `VAR_ELITE_4_STATE`, that
   edit was lost and must be redone.
2. **Write an OBSERVE-ONLY probe before the sequencer.** Drive from `post_ch24_atdoor.ss1` into
   Sidney's room and print, every N frames: current map, `(x,y)`, `get_event_var("ELITE_4_STATE")`,
   `get_event_flag("DEFEATED_ELITE_4_SIDNEY")`, and the positive control
   `get_event_flag("LANDMARK_POKEMON_LEAGUE")`. ⛔ **A run whose control reads False has a broken
   reader and its verdict must be DISCARDED, not reported.** That one probe converts §C and §D from
   [AGENT-DECOMP] into measurements — in particular D1 (does the defeated sprite block the door?),
   which is the most likely first hang. ⭐ **And add one cheap extra reading while you are there:
   step back SOUTH through the hall warp and see whether the bot can return to the lobby** — §D'
   makes the whole recovery design hinge on it, and it is unmeasured.
3. Only then build the sequencer, one room at a time, each leg graded on
   `DEFEATED_ELITE_4_<NAME>` — a predicate the run does not already satisfy when it starts.
