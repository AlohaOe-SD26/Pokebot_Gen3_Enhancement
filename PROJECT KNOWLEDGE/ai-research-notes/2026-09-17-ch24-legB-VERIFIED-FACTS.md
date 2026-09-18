# §Ch24 LEG B (WALLACE + THE ENDGAME TAIL) — FACTS I VERIFIED AT SOURCE MYSELF (2026-09-17, late)

> ⛔ **THIS FILE IS DIFFERENT FROM THE USUAL RESEARCH NOTE.** `ai-research-notes/00-READ-THIS-FIRST.md`
> says agent output is a NOTE, never truth. **Everything below was re-verified BY ME at FILE:LINE
> after an agent raised it**, precisely because it is all load-bearing for a leg that cannot be
> retried cheaply — the Wallace fight is un-fleeable and ends in a console reboot.
> A separate agent synthesis of the full 10-agent recon is being produced; where it disagrees with
> this file, **this file's citations are the ones that were checked by hand.**

## 0. WHERE THE BOT IS

`post_hall4_door.ss1` (PINNED `1f15cc400218`) — `HALL4 (5,3)`, **one tile from the Champion's door**,
party FULLY healed, Ice Beam intact, nothing fought, **1 Revive**, `VAR_ELITE_4_STATE=4`.
Stepping north onto `(5,2)` is the point of no return.

## 1. ⭐⭐ THE PARTY WAS BUILT FOR THIS FIGHT — AND I ALMOST MISSED IT

I started to write up "Toxic is an unhandled gap" and it is **wrong**. The move plan anticipated
Wallace by name.

`modules/story/pokemon_league.py` `MOVESET_PLAN`:
* **Swellow ← Facade (TM42)**, replacing Peck — *"Facade is 70 with STAB — and Wallace's Tentacruel
  AND Milotic both carry Toxic, after which **Guts (x1.5) and Facade's doubling BOTH apply**"*.
  ⇒ **Toxic on Swellow is an ADVANTAGE, not a threat.**
* **Sceptile ← Aerial Ace (TM40)**, replacing Slam — *"never-misses, and FOUR opponents run Double
  Team (Shiftry, Sableye, **Ludicolo**, Glalie)"*. Ludicolo is Wallace's #3.

✅ The pinned party carries **both**: Swellow `Facade, Fly, Aerial Ace, Quick Attack`; Sceptile
`Rock Smash, Strength, Leaf Blade, Aerial Ace` (verified by reload).

‼ **THE LESSON:** before filing "the bot cannot handle X", grep the tree for X. The answer had been
written down, with its reasoning, two work items earlier.

## 2. WALLACE'S TEAM (decomp `src/data/trainer_parties.h`, read at source)

| # | mon | lvl | moves |
|---|---|---|---|
| 1 | Wailord | 57 | Rain Dance, **Water Spout**, Double-Edge, Blizzard |
| 2 | Tentacruel | 55 | **Toxic**, Hydro Pump, Sludge Bomb, Ice Beam |
| 3 | Ludicolo | 56 | Giga Drain, Surf, Leech Seed, **Double Team** |
| 4 | Whiscash | 56 | Earthquake, Surf, Amnesia, Hyper Beam |
| 5 | Gyarados | 56 | Dragon Dance, Earthquake, Hyper Beam, Surf |
| 6 | Milotic | 58 @ **Sitrus** | **Recover**, Surf, Ice Beam, Toxic |

⛔⛔ **HE HAS SIX. EVERY ELITE FOUR MEMBER HAD FIVE.** A longer fight ⇒ more item uses, more PP drain,
more chances for the faint chooser to run. Do not size budgets from the E4 rooms.

⭐ **THE TYPE STORY INVERTS: SCEPTILE, NOT WAILORD, IS THE ANSWER.** Grass is super-effective on five
of the six (4× on Whiscash, Water/Ground); only Ludicolo (Water/**Grass**) resists it to neutral.
Wailord's **Ice Beam is 0.5× on most of this team** — it was the DRAKE counter, not this one.
⚠ But Sceptile is 2× to Ice Beam (Tentacruel, Milotic) and Blizzard (Wailord). It hits hardest and
dies fastest. *(CALCULATED from our own type data, not measured in battle.)*

## 3. ⛔ THE GRADE TRAP — THIS WOULD HAVE READ FALSE ON SUCCESS

The Hall of Fame script **clears `FLAG_DEFEATED_ELITE_4_SIDNEY/PHOEBE/GLACIA/DRAKE` and resets
`VAR_ELITE_4_STATE` to 0** *before* `special GameClear` (decomp `event_scripts.s`).
⇒ **a leg-B grade written on those flags reads FALSE ON SUCCESS.**
✅ Grade on **`IS_CHAMPION`** — flag **2175**, verified in `modules/data/event_flags/emerald.txt:1061`.
⛔ And `SYS_GAME_CLEAR` alone is not sufficient either (`#24-gameclearflag`): it is set ~54 lines
before `SetMainCallback2(CB2_DoHallOfFameScreen)`, i.e. while the Hall of Fame, the credits and a
`SoftReset(RESET_ALL)` are all still ahead.

## 4. ⛔⛔ TWO FRAMEWORK HAZARDS — BOTH CONFIRMED BY ME AT FILE:LINE

**(a) `soft_reset()` CAN PRESS "Up" ON THE MAIN MENU.**
`modules/modes/util/soft_reset.py:30` — `context.emulator.press_button(random.choice(["A","Start","Left","Right","Up"]))`
fires on `GameState.TITLE_SCREEN`. And `modules/memory.py:286-294` classifies **`CB2_INITMAINMENU`
as `TITLE_SCREEN`**, while only `CB2_MAINMENU` maps to `MAIN_MENU`. ⇒ during the `CB2_INITMAINMENU`
window the random-key arm is live *while the main menu is coming up*, and a stray **"Up"** moves the
cursor off CONTINUE.
⇒ **DO NOT use `soft_reset(mash_random_keys=True)` as the resume path.** If leg B presses anything
on the title/menu, press **A and B only, never a direction** — then the cursor cannot move and
CONTINUE stays selected. ‼ This is the one failure in the whole leg that could touch the save file.

**(b) THE RESET REBUILDS LISTENERS BUT NOT THE CONTROLLER STACK.**
`modules/main.py:119-130` — on `previous_frame_info.frame_count > frame_info.frame_count` it calls
`state_cache.reset()`, resets the badge log, and sets
`context.bot_listeners = get_bot_listeners(context.rom)`. It does **NOT** clear
`context.controller_stack`; the `elif len(context.controller_stack) == 0:` at `:136` only fires when
the stack is *already* empty. ⇒ **a generator suspended across the reset survives with stale listener
bindings** and can spin. ✅ The reset IS detected — that half of the framework works.

## 5. WHAT THE CHAMPION'S ROOM SCRIPT CONTAINS (decomp, counted)

`data/maps/EverGrandeCity_ChampionsRoom/scripts.inc` is **326 lines with 12 `msgbox` calls**, and the
post-battle cutscene runs through rival arrival, Birch arrival, a Pokédex-rating `special`, and
several `applywaitmovement` stages before the map ever changes.
⇒ **a short "no map change within N frames" watchdog will report a FALSE HANG.** Size for the whole
cutscene, not for a door transition.

## 6. WHAT IS STILL UNKNOWN — ONLY A LIVE RUN CAN SETTLE IT

1. Whether this party actually beats six Pokémon on one bag with **1 Revive** and no heal.
2. The real frame cost of victory → controllable-again (the credits are un-skippable on a first
   clear because the B-hold speed-up is gated on `gHasHallOfFameRecords`, which `GameClear` sets
   FALSE exactly then).
3. Whether the harness's **20,000-frame no-progress detector** fires during the Hall of Fame/credits
   — its signature is constant there, so it very likely does.
4. What a driver's generator actually experiences across `SoftReset(RESET_ALL)`.

⇒ **THE NEXT ACTION IS AN OBSERVE-ONLY PROBE, NOT A DRIVER.** It should cross `(5,2)`, let the fight
happen, and log state/tasks/frame on a duty cycle from the battle's end onward — asserting nothing,
grading nothing, and pressing **A/B only**. ⛔ Latch the outcome in `on_battle_ended()`, not in the
generator: the driver is starved for the whole battle and may never get another frame before the warp.
