# Story-Mode Bot — Deep Design (Pass 1 + Pass 2 + Pass 3 + Pass 4 verified)

> **Pass 4 (2026-07-20)** re-derived every fact independently from ROM + two/three
> external walkthroughs and diffed against the doc. It **confirmed all five Pass-3
> corrections** (no regressions) and found **two NEW content-detail errors** (the
> Petalburg-Woods Devon-Goods flag misattribution and the Cut "Route 104 vs
> Rustboro" contradiction), now fixed and tagged **[P4]**. It also resolved two
> former verify-live items (Magma Emblem = key item, not a flag; `MT_PYRE_STATE`
> var). Full table + convergence verdict in the new **§10**. The strategic
> backbone has **converged**; residual unknowns are live-only where-to-stand/timing.

> **Pass 3 (2026-07-20)** independently triple-checked every factual claim
> against BOTH (A) the bot's own ROM ground truth (`event_flags/emerald.txt`,
> `event_vars/emerald.txt`, `symbols/pokeemerald.sym`, `menuing.py`,
> `map_path.py`, `higher_level_actions.py`) AND (B) an external Emerald
> walkthrough (Bulbapedia / Thonky / pokemondb / psypokes / GameFAQs). It caught
> a **Pass-2 regression** (Rock Smash location) plus a **chapter-order error**
> and a **flag misplacement**. Inline Pass-3 fixes are tagged **[P3]**; see the
> new **§9 "Pass 3 accuracy audit"** for the full claim-by-claim table.

> Design-only document. NO code was written or changed producing this. **Pass 2
> (2026-07-19)** adversarially re-audited the Pass-1 skeleton against the bot's
> own ground-truth data (`modules/data/event_flags/emerald.txt`,
> `event_vars/emerald.txt`, `modules/data/symbols/pokeemerald.sym`,
> `modules/menuing.py`, `modules/map_path.py`) and caught several errors and
> missed mandatory beats — see **§8 "Pass 2 verification"** at the end for the
> full change list. Inline Pass-2 corrections are tagged **[P2]**. This remains
> a design doc for punch-list **#24** (Story-Mode Bot), grounded in the **real**
> capabilities of the working fork at `sandbox-pokebot/`, cited as `file:line`.
> Emerald-only for v1 (profile `Nick - Emerald`, game code `BPE`).
>
> **[P2] Headline corrections:** (1) **Gym 8 leader is JUAN, not Wallace** —
> Wallace is the *Champion*. (2) **Fly's field-use gate is the Feather Badge
> (BADGE06), code-confirmed** — the doc's earlier uncertainty is resolved, and a
> real fork bug was found in `fly_to`. (3) Three **mandatory late-game beats were
> missing** from the skeleton: **Mt. Pyre**, the **Slateport Harbor submarine
> theft**, and the **Magma Hideout / Groudon awakening**. (4) **Mr. Briney &
> the Peeko rescue** (the gate to the Dewford/Slateport boat) needed to be made
> explicit. (5) HM04 **Strength comes from Rusturf Tunnel, not Mt. Chimney**.
> (6) **Brawly's gym IS a puzzle** (dark room). All resolved below.
>
> **Reading note on citations:** all `modules/...:NNN` paths are relative to
> `C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot\`. Line numbers
> were read on 2026-07-19; treat them as anchors, not guarantees across future
> upstream pulls.

---

## 0. TL;DR for a future agent

The bot is a **shiny-hunting automation** whose primitives happen to be exactly
what a story-player needs: it already **auto-wins wild AND trainer battles to
completion**, **pathfinds across connected maps** (auto-surfs/waterfalls),
**advances scripted dialogue by reading the game's own task/script scheduler
(not pixels)**, **types on the naming keyboard**, **teaches HMs/TMs**, **uses
every field move**, **shops, heals, talks to NPCs, manages the PC**, and can
**read every story flag/var/badge/item** to know where in the plot a save is.

The story bot is therefore **mostly a composition + sequencing layer**, plus a
handful of genuinely-new pieces:

1. **Intro automation** — Birch speech, **gender select**, **player-name entry**
   (none exist; keyboard typer exists but is wired only to nicknames).
2. **A chapter/objective orchestrator** — every existing mode is a self-contained
   map-specific routine; there is no cross-map "advance the plot" driver.
3. **Per-obstacle field-move routing on the critical path** — the *execution*
   of Cut/Strength/etc. exists, but nothing routes the avatar to the specific
   story-critical tree/boulder and detects it. `puzzle_solver.py` only covers
   end-game puzzle maps.
4. **Cross-region warp navigation is built but unwired** (`navigate_to_anywhere`)
   and cannot open locked/HM/story-gated doors — it fails at runtime instead.
5. **Better boss-battle AI** — move selection is competent but naive (pure
   max-damage; no status/setup/switching). Serviceable for most trainers;
   risky for gyms/Elite Four without a stronger `decide_turn`.

---

## 1. Goal + Approach

### 1.1 Goal
From a **fresh save** (or a **continued** one), drive Pokémon Emerald all the way
to **beating the Elite Four + Champion Wallace** (endgame flag `SYS_GAME_CLEAR`
/ `IS_CHAMPION`). Full living-dex completion is explicitly a *later* concern
(punch-list #45); v1 stops at Hall of Fame.

### 1.2 Fresh-or-continue + user-set identity
- **Fresh:** start a New Game, drive Birch's intro, set **gender** (user choice)
  and **player name** (user string), through to stepping out in Littleroot.
- **Continue:** load an existing save and **detect the current chapter** from
  event flags/badges, then jump into the correct chapter mid-stream.
- **Character name/gender** are stored as story-mode config, applied only on the
  fresh-start path. They are readable back afterward via `Player.name`
  (`modules/player.py:187`) and `Player.gender` (`modules/player.py:191`).

### 1.3 The Chapter model (discrete, resumable milestones)
Progress is modeled as an **ordered list of Chapters**, each a small state
machine with:

- **`is_complete()`** — a predicate over event flags/vars/badges/items/party/map
  that returns true when the chapter's outcome already exists in the save. This
  is what makes the bot **resumable**: on start, walk the chapter list and skip
  every already-complete chapter; begin at the first incomplete one.
- **`preconditions()`** — asserts that must hold to *run* the chapter (right
  badge, HM taught, key item in bag, party can battle). Reuses `modules/modes/
  _asserts.py` helpers.
- **`run()`** — a generator that performs the chapter (navigate, battle, talk,
  teach HM, heal, shop), exactly like an existing `BotMode.run()`.
- **`on_battle_started()` / listeners** — inherited from the `BotMode` contract
  so involuntary events (battles, whiteouts, eggs, repel) are handled by the
  existing reflex listeners (`modules/modes/_listeners.py`).

**Progress detection** is read-only and cheap — no separate save file is
strictly required because *the game's own flags are the source of truth*:
- `get_event_flag(name)` — `modules/memory.py:336` (returns False for unknown).
- `get_event_var(name)` — `modules/memory.py:393` (returns -1 for unknown).
- Badges are **not** a Player field — they are the eight flags
  `BADGE01_GET`…`BADGE08_GET` (`modules/data/event_flags/emerald.txt`, numbers
  2151–2158); badge count = number of those flags true.
- Endgame: `SYS_GAME_CLEAR` (flag 2148), `IS_CHAMPION` (2175).

**Progress persistence:** the bot's own bookkeeping (which sub-step inside a
chapter it was on, retry counts, chosen starter) is small and can live in a
JSON in the profile dir (mirrors how `hunt_target.json` / `soft_reset_frames.json`
already sit in `profiles/<name>/`). But the **authoritative** resume signal is
always re-derived from game flags on launch — the JSON is only a within-chapter
optimization, never trusted over the ROM state (matches the CLAUDE.md
"trust-but-verify" doctrine).

### 1.4 Why this fits the existing architecture
The upstream/dev docs already bless this shape: *"An AI agent playing Emerald can
be implemented as just another `BotMode`: `run()` becomes the policy loop
(observe → decide → `yield from` an action helper), and the existing listeners
already handle the involuntary events"* (`40cakes repo/DOCUMENTATION/
03-bot-modes-and-battle.md:686-691`). Story-mode is that agent, but with a
scripted (not learned) policy: a hand-authored chapter list.

---

## 2. FULL CHAPTER SKELETON (new-game → Champion)

**Legend:** *Gate* = the hard requirement to leave the chapter. *Key flag* =
the Emerald event flag that proves completion (names from
`modules/data/event_flags/emerald.txt`). HM **badge gates** that are
**confirmed in code** are marked ✅ (from `modules/map_path.py` /
`modules/menuing.py` / `modules/modes/rock_smash.py`).

### Overview table — 8 gyms, HM tie-ins, endgame

| # | Chapter | City / Area | Boss / Key battle | Badge | HM unlocked (field-use gate) | Key completion flag |
|---|---------|-------------|-------------------|-------|------------------------------|---------------------|
| 0 | Intro & Identity | Truck → Littleroot | (none) | — | — | `ADVENTURE_STARTED` (116) |
| 1 | Starter & first steps | Route 101 / Oldale / Rt 102-103 | Birch rescue; Rival (Rt 103) | — | — | `RESCUED_BIRCH` (82), `DEFEATED_RIVAL_ROUTE103` (130), var `STARTER_MON` (35), `RECEIVED_POKEDEX_FROM_BIRCH` (2276) |
| 2 | Petalburg & Wally | Petalburg City | Catch tutorial w/ Wally | — | — | (meet Dad/Wally scripts) |
| 3 | Woods (researcher rescue) & Cut | Rt 104 / Petalburg Woods / Rustboro | **[P4 FIX]** Aqua Grunt in Petalburg Woods is a **RESEARCHER-RESCUE, NOT a goods theft** — grunt flees, researcher gives a Great Ball (Bulbapedia Part 2) | — | **Cut** (HM01) obtained in **Rustboro City** (Cutter's House, W of the PC) **[P4]** | **[P4 FIX]** `RECEIVED_HM_CUT` (137). **`DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143) do NOT belong here** — the theft (Rustboro) & recovery (Rusturf) happen AFTER Gym 1, in row 5 |
| 4 | **Gym 1 — Roxanne** | Rustboro City | Roxanne (Rock) | **Stone** | **Cut usable** ✅ (`menuing.py:812`) | `DEFEATED_RUSTBORO_GYM` (1264), `BADGE01_GET` (2151) |
| 5 | Devon errand, **Peeko rescue** & Rival | Rustboro / Rt 116 / **Rusturf Tunnel** | Aqua grunt (Rusturf); Rival (Rustboro) | — | — | **[P3 FIX]** `RETURNED_DEVON_GOODS` (144 — returned to Devon Corp Rustboro; the Rusturf grunt also drops the goods & frees Peeko, `RECOVERED_DEVON_GOODS` 143), `RECEIVED_POKENAV` (188), `DEFEATED_RIVAL_RUSTBORO` (211). **149 does NOT belong here** — that's the Slateport delivery (row 8) |
| **5b** | **[P2 MADE EXPLICIT] Mr. Briney & Peeko** — MANDATORY gate to the boat | Rt 116 → Rusturf Tunnel → Briney's cottage (Rt 104) | rescue Peeko from Aqua grunt | — | — | `MR_BRINEY_SAILING_INTRO` (147); Peeko/Briney hide-flags 738-744, 879-881 — *verify exact gate ordering live* |
| 6 | To Dewford + Steven letter (**Briney's boat**) | Rt 104/105 (Mr. Briney sails) / Granite Cave | (cave; Steven) | — | **Flash** (HM05) in Granite Cave | `DELIVERED_STEVEN_LETTER` (189), `RECEIVED_HM_FLASH` (109) |
| 7 | **Gym 2 — Brawly** | Dewford Town | Brawly (Fighting) | **Knuckle** | **Flash usable** | `DEFEATED_DEWFORD_GYM` (1265), `BADGE02_GET` (2152) |
| 8 | Slateport & Oceanic Museum | Rt 109 / Slateport | **[P2]** Aqua grunts (Museum) + Archie; deliver Devon parts to Capt. Stern | — | — | **[P3 FIX]** `DELIVERED_DEVON_GOODS` (**149** — delivered to Capt. Stern **here**, moved from row 5; dock-rejected first, `DOCK_REJECTED_DEVON_GOODS` 148); `OCEANIC_MUSEUM_MET_REPORTER` (105); Museum Aqua-grunt hide-flag 883. EARLY Slateport visit; the sub theft is the LATE beat 16c |
| 9 | Mauville & Bike | Rt 110 / Mauville | Rival (Rt 110) | — | **[P3 FIX] Rock Smash (HM06) from a man in the SOUTHEAST HOUSE of MAUVILLE CITY** (east of the Poké Mart) — **the Pass-2 "Route 111" was a REGRESSION and is WRONG** (pokemondb/Thonky/PokéCoders, §2.3); **Bike** from Rydel's, Mauville | `RECEIVED_BIKE` (90), `RECEIVED_HM_ROCK_SMASH` (107) |
| 10 | **Gym 3 — Wattson** | Mauville City | Wattson (Electric) | **Dynamo** | **Rock Smash usable** ✅ (`rock_smash.py:143` = `BADGE03_GET`) | `DEFEATED_MAUVILLE_GYM` (1266), `BADGE03_GET` (2153), `GOT_BASEMENT_KEY_FROM_WATTSON` (208) |
| 11 | Rt 111/112, Mt. Chimney (Magma) | Rt 111 desert / Fiery Path / Rt 112 / Mt. Chimney | Team Magma; Maxie | — | **Go-Goggles** (Lavaridge, for Rt 111 desert); **Meteorite** event. **[P2] HM04 Strength is from RUSTURF TUNNEL, not here** (available earlier once the tunnel is opened) | `DEFEATED_EVIL_TEAM_MT_CHIMNEY` (139), `RECEIVED_METEORITE` (115), `RECEIVED_GO_GOGGLES` (221); `RECEIVED_HM_STRENGTH` (106) — obtained at Rusturf |
| 12 | **Gym 4 — Flannery** | Lavaridge Town | Flannery (Fire) | **Heat** | **Strength usable** (`SYS_USE_STRENGTH`) | `DEFEATED_LAVARIDGE_GYM` (1267), `BADGE04_GET` (2154) |
| 13 | **Gym 5 — Norman (Dad)** | Petalburg City | Norman (Normal) — **needs 4 badges to challenge** (var `PETALBURG_GYM_STATE`, event_vars 133; door greeter blocks until then) | **Balance** | **Surf** (HM03) from a house in Petalburg **after** the gym | `DEFEATED_PETALBURG_GYM` (1268), `BADGE05_GET` (2155), `RECEIVED_HM_SURF` (122) |
| 14 | Rt 118/119, Weather Institute, Rival | Rt 118 (Surf) / 119 / Weather Inst. | **Aqua** at Weather Inst. (Emerald = Aqua, get Castform); Rival (Rt 119) | — | **[P3] Fly (HM02) is GIVEN BY THE RIVAL** (May/Brendan) after the Rt 119 battle — **not** a generic NPC (pokemondb/GameFAQs) | `RECEIVED_HM_FLY` (110) |
| **14b** | **[P3 REORDER — PREREQUISITE TO GYM 6]** Devon Scope & Fortree Kecleon | Fortree City / **Route 120** (east of Fortree) | **Steven** gives **Devon Scope** (after a Lv30 Kecleon battle on Rt 120); then reveal & battle the **invisible Kecleon blocking the Fortree Gym door** | — | **Devon Scope** (reveals Kecleon) | `RECEIVED_DEVON_SCOPE` (285), `KECLEON_FLED_FORTREE` (295) — **the Fortree Gym CANNOT be entered until this is done** (Bulbapedia/Thonky/PokéBase) |
| 15 | **Gym 6 — Winona** | Fortree City | Winona (Flying) — **rotating-gate gym puzzle** (§2.4) — **[P3] gym entry is GATED behind row 14b (Devon Scope + Kecleon reveal)** | **Feather** | **Fly usable** ✅ **[P2] Feather/BADGE06** (`menuing.py:826`; NOT `fly_to`'s BADGE03 — that's a fork bug, §2.1) | `DEFEATED_FORTREE_GYM` (1269), `BADGE06_GET` (2156) |
| 16 | Rt 120/121 → Lilycove (post-Winona travel) | Rt 120 / 121 / Lilycove | route trainers; Team Magma/Aqua sighting in Lilycove | — | (Devon Scope/Kecleon already done in row 14b) | reach Lilycove (Mt. Pyre & Aqua-Hideout arc begins next) |
| **16b** | **[P2 ADDED] Mt. Pyre** (was MISSING) | Rt 122/123 (Surf) / Mt. Pyre | Team Magma/Aqua at summit; orb theft; **summit caretaker gives the Magma Emblem** | — | Surf to reach | `HIDE_MT_PYRE_SUMMIT_MAXIE` (856). **[P4]** Progress tracked by **var `MT_PYRE_STATE` (185)**; the summit yields the **Magma Emblem key item** (gates row 16d). Exact completion value still *verify live* |
| **16c** | **[P2 ADDED] Slateport Harbor submarine theft** (was MISSING) | Slateport Harbor | Team Aqua grunts + Archie steal sub | — | — | `EVIL_TEAM_ESCAPED_STERN_SPOKE` (271); NPC-hide flags 845-848, 860 |
| **16d** | **[P2 ADDED] Magma Hideout — Groudon** (was MISSING) | Jagged Pass / Route 112 → Magma Hideout | Team Magma; Maxie; **Groudon awakened** | — | **[P3] Entry gated by the MAGMA EMBLEM** obtained at Mt. Pyre summit (row 16b); Rock Smash/Strength used inside | `GROUDON_AWAKENED_MAGMA_HIDEOUT` (111); `HIDE_MAGMA_HIDEOUT_4F_GROUDON` (853). **[P4 RESOLVED] The Magma Emblem is a KEY ITEM, not a flag** — `items.json` "Magma Emblem" (index `MAGMAEMBLEM`); the Jagged Pass entrance auto-appears when it is in the bag (Bulbapedia). Gate via `get_item_bag()`, not a flag. Mt. Pyre progress is tracked by **var `MT_PYRE_STATE` (185)** |
| 17 | Team Aqua — Hideout & Submarine | Lilycove / Aqua Hideout | Team Aqua; room-key + Electrode puzzle | — | — | `TEAM_AQUA_ESCAPED_IN_SUBMARINE` (112), `USED_ROOM_1/2/4/6_KEY` (240-243), `DEFEATED_ELECTRODE_1/2_AQUA_HIDEOUT` (452/453) |
| 18 | Mossdeep + Space Center | Rt 124/125 (Surf) / Mossdeep | Magma at Space Center; Steven tag (**DOUBLE**) | — | **Dive** (HM08) given in **Steven's house, Mossdeep** (`ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133) | `DEFEATED_MAGMA_SPACE_CENTER` (117), `RECEIVED_HM_DIVE` (123), `INTERACTED_WITH_STEVEN_SPACE_CENTER` (205) |
| 19 | **Gym 7 — Tate & Liza** | Mossdeep City | Tate & Liza (Psychic, **DOUBLE**) | **Mind** | **Dive usable** ✅ (`map_path.py:690` = `BADGE07_GET`) | `DEFEATED_MOSSDEEP_GYM` (1270), `BADGE07_GET` (2157) |
| 20 | Seafloor Cavern (Kyogre) | Rt 128 (Dive) / Seafloor Cavern | Team Aqua; Archie; Kyogre wakes | — | **Dive** required to enter (`can_dive` gate) | `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (129) |
| 21 | Sootopolis crisis & Rayquaza | Sootopolis (**Dive under Rt 126** to enter) / Cave of Origin / Sky Pillar | (Rayquaza quells legendaries) | — | Dive to enter Sootopolis; **Mach Bike** for Sky Pillar crumbling floor | `LEGENDARIES_IN_SOOTOPOLIS` (83), `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` (307), `DEFEATED_RAYQUAZA` (448), `RECEIVED_RED_OR_BLUE_ORB` (212), `WALLACE_GOES_TO_SKY_PILLAR` (311) |
| 22 | **Gym 8 — JUAN** **[P2 FIX: not Wallace]** | Sootopolis City | **Juan** (Water) — `SootopolisCity_Gym_1F_EventScript_Juan` | **Rain** | **Waterfall** (HM07) given by **Wallace in Sootopolis** (around crisis resolution; *verify exact trigger live*) | `DEFEATED_SOOTOPOLIS_GYM` (1271), `BADGE08_GET` (2158), `RECEIVED_HM_WATERFALL` (312) |
| 23 | Victory Road | Rt 128/132-134 (Surf/Dive/Waterfall) → Ever Grande | Rival Wally (Victory Road) | — | Surf+Waterfall+Dive to reach; **Strength**+Rock Smash+Flash inside | `DEFEATED_WALLY_VICTORY_ROAD` (126) |
| 24 | **Elite Four + Champion** | Ever Grande / Pokémon League | Sidney→Phoebe→Glacia→Drake→Wallace | — | — | `DEFEATED_ELITE_4_SIDNEY/PHOEBE/GLACIA/DRAKE` (1275-1278), `IS_CHAMPION` (2175), `SYS_GAME_CLEAR` (2148) |

### 2.1 HM → badge field-use gate table (the "stuck bot" prevention list)

The bot must not attempt a field HM before its badge exists; `use_field_move`
and the pathfinder already enforce this and will raise `BotModeError` if the
badge is missing (which the orchestrator must catch and re-sequence, never
crash on).

**[P2] ALL EIGHT badge gates are now code-confirmed** in `modules/menuing.py`
`use_field_move()`, the Emerald branch, lines **810-833** (one authoritative
`case` per HM). This is ground truth and settles every earlier "verify" note:

| HM | Move | Badge required to USE in field | Code-confirmed gate |
|----|------|-------------------------------|---------------------|
| HM01 | Cut | **Stone** (Gym 1, BADGE01) | ✅ `menuing.py:811` |
| HM05 | Flash | **Knuckle** (Gym 2, BADGE02) | ✅ `menuing.py:814` |
| HM06 | Rock Smash | **Dynamo** (Gym 3, BADGE03) | ✅ `menuing.py:817` + `rock_smash.py:143` |
| HM04 | Strength | **Heat** (Gym 4, BADGE04) | ✅ `menuing.py:820` |
| HM03 | Surf | **Balance** (Gym 5, BADGE05) | ✅ `menuing.py:823` + `map_path.py:687` (`can_surf`) |
| HM02 | Fly | **Feather** (Gym 6, BADGE06) | ✅ `menuing.py:826` **[P2 RESOLVED]** |
| HM08 | Dive | **Mind** (Gym 7, BADGE07) | ✅ `menuing.py:829` + `map_path.py:693` (`can_dive`) |
| HM07 | Waterfall | **Rain** (Gym 8, BADGE08) | ✅ `menuing.py:832` + `map_path.py:701` (`can_waterfall`) |

> ⚠️ **[P2] FORK BUG found — do NOT rely on `fly_to()` for the Fly gate.**
> `higher_level_actions.py:52,55` (`fly_to`) checks **`BADGE03_GET` for BOTH the
> RSE and FRLG branches**. That is correct only for FRLG (Fly = Thunder Badge 3);
> for **Emerald it is wrong** — Emerald Fly needs **BADGE06** (per the
> authoritative `use_field_move` at `menuing.py:826`). The story bot must gate
> Fly on `BADGE06_GET` itself (or fix `fly_to`), not trust `fly_to`'s check.
> Logged as a candidate upstream/fork fix; noted in §8.

### 2.2 HM criticality (hard gate vs shortcut)

Not every HM is mandatory to *finish the game*; missing a hard-gate HM =
permanently stuck. Priority for the bot to obtain + teach:

- **Surf (HARD)** — required for essentially all post-Gym-5 travel (Rt 118/119,
  Mossdeep, Sootopolis, Victory Road approach).
- **Dive (HARD)** — required to enter Seafloor Cavern and to reach Sootopolis
  underwater (Rt 126/128).
- **Waterfall (HARD)** — required to climb to Ever Grande City / Victory Road.
- **Strength (HARD)** — mandatory boulder pushes in Victory Road (and caves).
- **Rock Smash (semi)** — clears mandatory rocks in some caves/routes.
- **Cut (semi)** — a few mandatory trees; many are optional shortcuts.
- **Flash (optional-ish)** — makes Granite Cave / Victory Road navigable; the
  pathfinder can sometimes route dark caves without it, but obtaining it is cheap.
- **Fly (optional but huge)** — pure convenience/time-saver; not a gate.

### 2.3 [P2] HM & key-item HANDOFF table (WHO gives it / WHERE)

Every progression item, its giver/location, and the flag that proves receipt.
**Flag numbers verified** in `modules/data/event_flags/emerald.txt`. Locations
marked **(code-anchored)** are confirmed by a symbol/flag; **(established)** are
well-documented Emerald facts I could not fully pin to an in-repo symbol, so the
exact NPC/tile is marked *verify live*.

| Item | Giver / Location | Receipt flag | Confidence |
|------|------------------|--------------|-----------|
| **HM01 Cut** | Cutter's House, **Rustboro City** (man) | `RECEIVED_HM_CUT` (137) | established (solid) |
| **HM05 Flash** | Hiker in **Granite Cave** (Dewford) | `RECEIVED_HM_FLASH` (109) | established |
| **HM06 Rock Smash** | **[P3 FIX]** Man in the **SOUTHEAST house of Mauville City** (east of the Poké Mart) — **Pass 2 wrongly moved this to "Route 111"; it IS Mauville** (pokemondb/Thonky/PokéCoders). Given once you have 2 badges; field-use still needs Dynamo (BADGE03) | `RECEIVED_HM_ROCK_SMASH` (107) | **confirmed (external)** |
| **HM04 Strength** | **Rusturf Tunnel** (the man after the tunnel is opened) — **[P2 FIX: doc said "near Mt. Chimney" — WRONG]** | `RECEIVED_HM_STRENGTH` (106); `RUSTURF_TUNNEL_OPENED` (199) | established, corrected |
| **HM03 Surf** | House in **Petalburg City**, **after beating Norman** (Wally's father / the man) | `RECEIVED_HM_SURF` (122) | established, *verify exact house/NPC live* |
| **HM02 Fly** | **[P3 FIX] Given by the RIVAL** (May/Brendan) after the **Route 119** rival battle (north Rt 119, en route to Fortree) — not a generic NPC | `RECEIVED_HM_FLY` (110) | **confirmed (external)** |
| **HM08 Dive** | **Steven's house, Mossdeep** (after Space Center) | `RECEIVED_HM_DIVE` (123); item `ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` (1133) | **code-anchored** |
| **HM07 Waterfall** | **Wallace, Sootopolis** (around the legendary-crisis resolution) | `RECEIVED_HM_WATERFALL` (312) | established, *verify exact trigger live* |
| **Devon Goods** (steal→recover→return→deliver) | **[P3 clarified]** stolen by Aqua grunt → grunt caught in **Rusturf Tunnel** (also frees Peeko) → **RETURNED** to Devon Corp Rustboro (**144**) → later **DELIVERED to Capt. Stern, Slateport** (dock-rejected **148** → **149**) | 142→143→144→148→149 chain | **code-anchored** |
| **Letter (for Steven)** | Devon president, Rustboro → deliver in Granite Cave | `DELIVERED_STEVEN_LETTER` (189) | **code-anchored** |
| **PokéNav** | Devon president, Rustboro | `RECEIVED_POKENAV` (188) | **code-anchored** |
| **Devon Scope** | **Steven, Route 120** (→ reveal Kecleon) | `RECEIVED_DEVON_SCOPE` (285) | **code-anchored** |
| **Go-Goggles** | **Lavaridge Town** (Cozmo's wife), after Mt. Chimney — needed for Rt 111 desert sandstorm | `RECEIVED_GO_GOGGLES` (221) | established, *verify NPC live* |
| **Wailmer Pail** | **Route 104** flower shop (Pretty Petal) — berries only | `RECEIVED_WAILMER_PAIL` (94) | established — **OPTIONAL** |
| **Mach/Acro Bike** | **Rydel's Cycles, Mauville** (pick one; swappable) — **Mach Bike required for Sky Pillar** | `RECEIVED_BIKE` (90) | **code-anchored** |
| **Meteorite** | Prof. Cozmo (Meteor Falls / post-Chimney) | `RECEIVED_METEORITE` (115) | established — **OPTIONAL** |
| **Basement Key** | **Wattson**, after Gym 3 (opens New Mauville) | `GOT_BASEMENT_KEY_FROM_WATTSON` (208) | **code-anchored** — New Mauville is **OPTIONAL** |
| **Room Keys 1/2/4/6** | Aqua Hideout interior (puzzle items) | `USED_ROOM_*_KEY` (240-243) | **code-anchored** |
| **Scanner** | Abandoned Ship (Rt 108) → exchange w/ Capt. Stern | `EXCHANGED_SCANNER` (294) | established — **OPTIONAL** |
| **Rods** (Old/Good/Super) | Dewford / Route 118 / Mossdeep fishermen | 257 / 227 / 152 | established — **OPTIONAL** |
| **Coin Case** | Mauville (Game Corner area) | `RECEIVED_COIN_CASE` (258) | established — **OPTIONAL** |
| **Red/Blue Orb** | Cave of Origin / Sootopolis crisis | `RECEIVED_RED_OR_BLUE_ORB` (212) | **code-anchored** |
| **Eon Ticket** | Mystery-Gift event → Southern Island (Lati@s) | `SHOWN_EON_TICKET` (430) | **OPTIONAL / event-only** |

### 2.4 [P2] GYM-INTERIOR PUZZLE enumeration (each grounded in a real script)

Pass 1 left these "un-enumerated." Each gym's puzzle mechanic is now confirmed by
an actual symbol in `pokeemerald.sym`, so the routing/authoring cost is scoped:

| Gym | Leader | Puzzle | Grounding symbol | Authoring need |
|-----|--------|--------|------------------|----------------|
| 1 Rustboro | Roxanne | **None** — straight trainer corridor | (no puzzle script) | waypoints only |
| 2 Dewford | Brawly | **[P2 FIX: NOT "none"]** **Dark room** — beat trainers to brighten the room progressively | `DewfordTown_Gym_EventScript_BrightenRoom` (+ per-trainer `…BrightenRoom`) | order-sensitive route: must beat trainers to reveal path |
| 3 Mauville | Wattson | **Switches → raise/lower electric barriers/doors** | `MauvilleGymPressSwitch`, `MauvilleGymSetDefaultBarriers` | authored switch-press sequence |
| 4 Lavaridge | Flannery | **Warp trapdoors** (hot-sand holes) between 1F/B1F | `DoLavaridgeGym1FWarp`, `DoLavaridgeGymB1FWarp`, `StartLavaridgeGymB1FWarp` | authored warp-tile path map |
| 5 Petalburg | Norman | **Room-choice doors** — pick a challenge room per door; correct rooms open the path | `PetalburgGymSlideOpenRoomDoors`, `PetalburgGymUnlockRoomDoors` | authored door/room routing |
| 6 Fortree | Winona | **Rotating-gate puzzle** (push gates to align a path) | `RotatingGate_*` (`GetCurrentMapRotatingGatePuzzleType`, `RotatingGate_RotateInDirection`) | authored gate-push solution |
| 7 Mossdeep | Tate & Liza | **Warp-tile teleport maze** + **DOUBLE battle** | `MetatileBehavior_IsMossdeepGymWarp`, `DoMossdeepGymWarp` | authored warp path + double-battle AI |
| 8 Sootopolis | **Juan** | **Cracked-ice floor** — step pattern; ice cracks/breaks per step | `SetSootopolisGymCrackedIceMetatiles`, `SootopolisGymIcePerStepCallback` | authored no-repeat step path |

`puzzle_solver.py` covers **none** of these gym interiors — all eight need
per-map authored navigation (six are genuine puzzles; gyms 1 has none and 2 is a
"beat-trainers-to-progress" variant).

---

## 3. DEEP DETAIL — First buildable chunk: Intro → Gym 1 (Rustboro)

This is the proof-of-approach and the first thing to build. It exercises every
hard new piece (intro, naming, gender, first HM teach, first gym) at small scale.

### Chapter 0 — Intro & Identity  (NEW WORK is concentrated here)
Goal: New Game → controllable in Littleroot with the user's name+gender set.

**[P2] The intro task/script symbols DO exist in `pokeemerald.sym` — the intro
automation can key off them directly (not pixels). Real names below.**

1. **Boot to title / New Game.** From a fresh ROM, mash through copyright/title.
   `soft_reset(mash_random_keys=True)` exists (`modules/modes/util/soft_reset.py`)
   but **no New-Game menu driver** — build. **[P2] Main-menu tasks to key off:**
   `Task_MainMenuCheckSaveFile`, `Task_DisplayMainMenu`, `Task_HandleMainMenuInput`,
   `Task_HandleMainMenuAPressed` (menu-item order: NEW GAME / CONTINUE / OPTIONS,
   CONTINUE only present if a save exists — drives the fresh-vs-continue branch).
2. **Birch intro speech + the entire boy/girl/name flow is ONE task chain**
   (`Task_NewGameBirchSpeech_*`). **[P2] Ordered symbols:** `…_Init` →
   `…_ThisIsAPokemon` → `…_MainSpeech` → `…_AndYouAre` → `…_BoyOrGirl` →
   `…_WaitToShowGenderMenu` → `…_ChooseGender` → `…_WhatsYourName` →
   `…_StartNamingScreen` → (`CB2_NewGameBirchSpeech_ReturnFromNamingScreen`) →
   `…_SoItsPlayerName` → `…_CreateNameYesNo` → `…_ProcessNameYesNoMenu` →
   `…_AreYouReady` → `…_ShrinkPlayer` → `…_Cleanup`. `sBirchSpeechMainTaskId`
   (0x03000dd0) holds the active sub-task id. Advance with the existing
   `wait_until_task_is_active` / `wait_for_task_to_start_and_finish`
   (`tasks_scripts.py`).
3. **Gender select.** Cursor at `Task_NewGameBirchSpeech_ChooseGender`; the chosen
   value lives in the var **`sIntroCharacterGender`** (0x0203bcc8). **No gender
   helper exists** — build: at `…_ChooseGender`, move cursor to the user's choice,
   confirm A, then read `sIntroCharacterGender` back to verify. (Reuse the
   cursor-scroll idiom `menuing.get_scroll_direction`, `menuing.py:27`.)
4. **Name entry.** At `Task_NewGameBirchSpeech_StartNamingScreen` the naming
   keyboard (`sNamingScreen`, 0x02039f94) opens. **The typer exists**:
   `type_in_naming_screen(name, max_length)` (`keyboard.py:146`) /
   `handle_naming_screen` (`keyboard.py:226`) — wired today only to Pokémon
   nicknames. Reuse it for the player name. Then confirm the "So it's <name>?"
   yes/no at `…_CreateNameYesNo` / `…_ProcessNameYesNoMenu`. *Low-risk reuse.*
5. **Clock set.** After the truck (`WarpToTruck`), set the bedroom wall clock.
   **[P2] Symbols:** the clock script is `ScrCmd_initclock` → `StartWallClock`
   (returns via `ReturnFromStartWallClock`); state in `sClockInfo` (0x0203bcfe).
   Build: `navigate_to` the clock, press A to open `StartWallClock`, set hour/
   minute (D-pad), confirm. `modules/clock.py` only *reads* time — the intro
   *setter* is new but the script boundary (`StartWallClock`/`ReturnFrom…`) gives
   a clean wait target.
6. **Downstairs, meet Mom, TV, exit house.** Scripted movement + dialogue;
   navigate to the door, advance scripts.
7. **Meet Rival (May/Brendan) next door** (Prof. Birch's kid) — scripted.
   Completion signal: `ADVENTURE_STARTED` (flag 116) becomes true.

`is_complete()` for Ch0: `get_event_flag("ADVENTURE_STARTED")`.

### Chapter 1 — Starter & first steps
1. **Route 101 — rescue Birch.** Walk north from Littleroot onto Route 101; a
   scripted event triggers where Birch is chased by a wild Poochyena and drops his
   bag. `navigate_to(MapRSE.ROUTE101, <bag coords>)` with
   `avoid_scripted_events=False` / `expecting_script=True` so the pathfinder
   *does not route around* the trigger tile (default `avoid_scripted_events=True`
   would dodge it — `walking.py:314`, `map_path.py:924-927`).
2. **Choose starter from Birch's bag.** This is the *exact* mechanic
   `starters.py` already automates (RSE Hoenn path): it opens the bag via
   `wait_until_task_is_active("Task_HandleStarterChooseInput"/"Task_StarterChoose2",
   "A")` and presses Left/Right to pick (`modules/modes/starters.py:80-144`).
   Story mode reuses this selection logic (but keeps the mon instead of soft-
   resetting). Starter choice = story-mode config; readable back via var
   `STARTER_MON` (event_vars 35). **Team-building note:** default recommend
   **Mudkip** (Water/Ground line resists the first two gyms' problem types and
   trivializes several; see §4).
3. **Win the tutorial battle** (Poochyena) — auto-handled: BattleListener coerces
   tutorial battles to `CustomAction` but the fight itself runs; the strongest-
   move brain wins trivially.
4. **Oldale Town.** Walk north; scripted Birch/rival intro to catching; get the
   **Pokédex** (`RECEIVED_POKEDEX_FROM_BIRCH`, 2276) and **Poké Balls** from Birch
   in Littleroot lab (the "deliver to Mom's" loop). Navigate lab, advance scripts.
5. **Route 103 — beat the Rival.** Navigate onto Route 103, trigger the rival
   battle (auto-won by `handle_battle`; trainer battles are *always fought*,
   `_listeners.py`). Completion: `DEFEATED_RIVAL_ROUTE103` (130).
6. Return to Birch's lab → receive Pokédex/Running Shoes/Balls if not already;
   Mom gives Running Shoes.

`is_complete()` Ch1: `get_event_flag("DEFEATED_RIVAL_ROUTE103")` AND party size ≥ 1.

### Chapter 2 — Petalburg City (Dad + Wally)
1. Navigate Route 102 → Petalburg City (auto-battle any trainers en route,
   catch nothing required). Route 102 has trainers + tall grass (encounter
   avoidance on for travel: `avoid_encounters=True` default).
2. Enter **Petalburg Gym**, talk to **Norman (Dad)** — scripted; he won't battle
   yet. Then the **Wally catching tutorial**: Wally borrows a Zigzagoon and
   catches a Ralts; the player watches/advances a scripted sequence
   (`talk_to_npc` + script waits). No battle input needed.
3. Optional but recommended: heal at Petalburg PC
   (`heal_in_pokemon_center(PokemonCenter.PetalburgCity)`,
   `higher_level_actions.py:172`; PC door coords from `PokemonCenter` enum,
   `map_data.py:1524`).

### Chapter 3 — Route 104 / Petalburg Woods / Devon Goods + Cut
1. Route 104 (south) → **Petalburg Woods**. Auto-battle trainers/bug-catchers.
2. **[P4 FIX] Team Aqua Grunt event = a RESEARCHER RESCUE, not the Devon-Goods
   theft:** a Devon researcher is accosted; a scripted battle vs an Aqua Grunt
   triggers; on win the **grunt flees** and the researcher hands you a **Great
   Ball**. **The `DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143) flags
   are NOT set here** — the actual theft (a grunt bolts from the Devon Corp
   building in Rustboro) and recovery (Rusturf Tunnel, which also frees Peeko)
   both happen AFTER Gym 1, in Chapter 5 (Bulbapedia Emerald Part 2).
3. Exit Woods north → Route 104 (north) → **Rustboro City**.
4. **[P4 FIX] Cutter's House is in RUSTBORO CITY** (west of the Pokémon Center,
   not on Route 104 — corrects the earlier "Route 104" claim; matches §2.3):
   talk to the man to receive **HM01 Cut** (`RECEIVED_HM_CUT`, 137). Cut's item
   can be obtained now; **field use still waits on the Stone Badge** (Gym 1).
5. **Teach Cut** to a party member with `teach_hm_or_tm(get_item_by_name("HM01"),
   party_index, move_index_to_replace)` (`modules/modes/util/items.py:160`). The
   helper validates `can_learn_tm_hm` and refuses to overwrite existing HM slots.
   Choose a bulky non-lead HM-mule or the starter (see §4 move policy).

`is_complete()` Ch3: `get_event_flag("RECEIVED_HM_CUT")` AND a party mon
`has_pokemon_with_move("Cut")` (`pokemon_party.py:76`).

### Chapter 4 — Gym 1: Roxanne (Rock) → Stone Badge
1. Navigate to **Rustboro Gym** (`MapRSE.RUSTBORO_CITY_GYM = (11,3)`,
   `map_data.py:952`). The Rustboro gym has **no puzzle** — just a straight
   corridor of trainers, then Roxanne. Route: `navigate_to` to each trainer's
   line-of-sight tile (they auto-initiate: `TrainerApproachListener`,
   `_listeners.py:288`), or walk straight to Roxanne and let approaches fire.
2. **Beat the gym trainers + Roxanne** — all auto-won by `handle_battle`. Roxanne
   uses Geodude/Geodude/Nosepass (~Lv 12-15). **Level target: ~14-16.** With
   Mudkip (Water Gun/Mud-Slug) this is trivial; with Treecko fine; with Torchic
   bring a caught Water/Grass mon (see §4).
3. Receive **Stone Badge** (`BADGE01_GET`, 2151) + TM39 Rock Tomb. Stone Badge
   also **enables Cut in the field**.
4. Heal at Rustboro PC before moving on.

`is_complete()` Ch4: `get_event_flag("BADGE01_GET")`.

### Detailed primitive-call map for Chapter 4 (illustrative)
```
preconditions: assert_party_has_damaging_move(...); party lead can battle
run():
  yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, <gym door coords>)   # cross-region
  yield from navigate_to(MapRSE.RUSTBORO_CITY_GYM, <inside spawn>)           # warp through door
  for trainer_line_tile in gym_trainer_route:            # authored waypoints
      yield from navigate_to(gym_map, trainer_line_tile, avoid_encounters=False)
      # TrainerApproachListener + BattleListener auto-run the fight to completion
      yield from wait_for_no_script_to_run("B")
  yield from navigate_to(gym_map, <tile in front of Roxanne>)
  yield from talk_to_npc(roxanne_object_id)              # start boss battle
  # handle_battle auto-plays; on win, badge script runs
  yield from wait_until_event_flag_is_true("BADGE01_GET", "B")
  yield from heal_in_pokemon_center(PokemonCenter.RustboroCity)
```
Every symbol above exists today except the **authored `gym_trainer_route`
waypoint list** and the **`roxanne_object_id`** — i.e. the per-map data, not the
engine. That is the recurring shape of ALL story chapters: **engine ready,
per-map data authored.**

---

## 4. TEAM BUILDING & MAINTENANCE

### 4.1 Starter choice
Configurable; **default recommendation: Mudkip** (→ Marshtomp → Swampert).
Rationale: Water/Ground typing walls Roxanne (Rock), Wattson (Electric — Ground
immunity is huge), and gives Surf/Dive/Waterfall STAB later. Treecko and Torchic
are supported but flag more gym-matchup work. Starter is picked with the
existing `starters.py` selection logic (§3, Ch1).

### 4.2 What to catch and when
The bot is already a **catching machine** (`CatchStrategy`, `catch.py:23`;
opportunistic-catch scaffolding from living-dex #43). Story team plan:
- **Route 102 / 104:** catch a cheap utility mon early (e.g. a Taillow for a
  flyer, a Zigzagoon as a Pickup/HM-mule and future Fly/Cut carrier). Wurmple/
  Poochyena optional.
- **HM-mule strategy:** dedicate 1-2 low-value party members (Zigzagoon/Linoone,
  Tentacool later) to carry Cut/Rock Smash/Strength/Flash/Dive so the *combat*
  slots keep strong offensive movesets. `teach_hm_or_tm` protects HM slots from
  being overwritten (`items.py:160`).
- Keep 3-4 real battlers leveled; the rest are mules/box.

### 4.3 Leveling & healing per gym (level targets)
Suggested "party lead level ≥" gates before each gym (conservative, since the
battle AI is naive — see §5):

| Gym | Boss | Target level | Notes |
|-----|------|-------------|-------|
| 1 Roxanne | Rock | 14-16 | Water/Grass/Fighting coverage |
| 2 Brawly | Fighting | 16-19 | Flying/Psychic; avoid Normal leads |
| 3 Wattson | Electric | 20-24 | Ground immunity ideal |
| 4 Flannery | Fire | 26-29 | Water/Rock/Ground |
| 5 Norman | Normal | 30-33 | Fighting; watch Slaking Truant |
| 6 Winona | Flying | 33-36 | Electric/Rock/Ice |
| 7 Tate&Liza | Psychic (double) | 38-42 | **Double battle** — see §5 risk |
| 8 Juan | Water | 42-46 | Grass/Electric (**[P2] leader is Juan, not Wallace**) |
| E4+Champ | mixed | 50-58 | broad coverage; heal items |

**Grinding** reuses the proven loop brains: `PokecenterLoopController`
(`pokecenter_loop.py:23`) or `LevelBalancingBattleStrategy`
(`level_balancing.py:17`, keeps the low-level mon as lead but shares EXP) to
bring under-leveled members up between chapters. Route-trainer XP en route is
often enough; a dedicated grind sub-step triggers only when a level gate is unmet.

**Healing decision:** no global `needs_healing` flag exists — derive it. After
each battle, if `party.first_non_fainted is None` (`pokemon_party.py:68`) or the
lead's `current_hp_percentage` (`pokemon.py:1230`) < threshold, route to the
nearest center via `find_closest_pokemon_center` (`modes/util/map.py:86`) +
`heal_in_pokemon_center`. Between-chapter policy: **always heal + save at each
new town's PC** (cheap insurance; `save_the_game`, `higher_level_actions.py:244`).

### 4.4 Move-learning policy — reconciling with #39
- **#39 flipped the leveling-bot default** `battle.new_move` from `stop` → `cancel`
  so hunts don't get interrupted (changelog 2026-07-19; config default at
  `modules/config/schemas_v1.py:29`; decision point
  `DefaultBattleStrategy.which_move_should_be_replaced`,
  `modules/battle_strategies/default.py:25-103`).
- **Story mode wants GOOD movesets**, so it must NOT run with `cancel`. The
  cleanest fix uses the **already-existing `learn_best` branch**
  (`default.py:44-103`): it computes an "effective power" (base × attacking-stat ×
  STAB) per move, protects HM moves, and replaces the weakest / a redundant-type
  move for coverage. The docstring explicitly calls this the "future-intelligence
  seam" (`default.py:26-35`).
- **Recommendation:** the Story `BotMode` runs with `battle.new_move = "learn_best"`
  and `battle.stop_evolution = false`, either by setting these in the story
  profile's `battle.yml` or (cleaner) by supplying a **`StoryBattleStrategy`**
  subclass of `DefaultBattleStrategy` from `on_battle_started()` that (a) forces
  `learn_best` semantics regardless of config, (b) allows evolution, and (c) —
  as a later upgrade — overrides `decide_turn` for boss fights (§5).
- **Evolution:** default B-cancels every evolution (`battle_evolution_scene.py:17`;
  `should_allow_evolution` returns `... and not stop_evolution`, and
  `stop_evolution` defaults True, `schemas_v1.py:30`). Story mode must set
  `stop_evolution=false` so the starter and team evolve on schedule.

### 4.5 TMs / items / PC-box management
- **HMs/TMs** are taught with `teach_hm_or_tm` (`items.py:160`). Gym-reward TMs
  (Rock Tomb from Roxanne, etc.) can be taught to appropriate mons.
- **Bag/item queries:** `get_item_bag().quantity_of(get_item_by_name("HM01"))`
  (`items.py:427,529`); key items live in the `key_items` pocket.
- **PC/box management:** `interact_with_pc([PCAction...])`
  (`pc_interaction.py:730`) deposits/withdraws party↔box; read boxes via
  `get_pokemon_storage()` (`pokemon_storage.py:140`). Used to park HM-mules or
  swap in a type-matchup mon before a gym. `assert_boxes_or_party_can_fit_pokemon`
  (`_asserts.py:170`) guards against a full PC.

---

## 5. FEASIBILITY MAP vs current capabilities

Honest COVERED / PARTIAL / NEW per needed ability.

| Ability | Status | Evidence (file:line) |
|---|---|---|
| **Navigate within connected maps** (auto surf/waterfall/bike) | **COVERED** | `navigate_to` `walking.py:314`; waypoint actions `map_path.py:589`, exec `walking.py:209-291`; re-plans on timeout `walking.py:377-405` |
| **Navigate across regions through warps** | **PARTIAL** | `navigate_to_anywhere` `global_navigation.py:51` + `warp_graph.py:113` exist BUT not exported/wired, and **cannot open locked/HM/story-gated doors** (fails at runtime `global_navigation.py:127-132`) |
| **Auto-win wild battles** | **COVERED** | `handle_battle` `battle_handler.py:36`; `DefaultBattleStrategy` `default.py:12` |
| **Auto-win TRAINER/gym battles** | **COVERED** | trainer battles "always fought", flee blocked (`_listeners.py`; `_util.py:55` escape=0 for Trainer; `battle_action_selection.py:110`) |
| **Move-selection QUALITY for bosses** | **PARTIAL/NAIVE** | `get_strongest_move_against` `_util.py:244` is type/STAB/damage-model aware but pure max-damage: no accuracy, status, setup, PP, or switch logic; reactive switching only |
| **Send-out next / faint handling** | **COVERED** (naive pick) | `handle_fainted_pokemon` `battle_handler.py:154`; new lead = highest-HP `default.py:128` |
| **Double battles (Tate&Liza, some plot)** | **PARTIAL** | `decide_turn_in_double_battle` exists (`_interface.py`) and default fills it, but tuned less than singles — verify vs gym 7 |
| **Advance scripted dialogue / cutscenes** | **COVERED** | task/script waiters `tasks_scripts.py:11-158`; `is_waiting_for_input` `tasks.py:199` — event-driven off RAM, not OCR |
| **Yes/No + multiple-choice prompts** | **COVERED** | `wait_for_yes_no_question` `tasks_scripts.py:52`, `wait_for_multiple_choice_question` `:110` |
| **Player NAME entry (intro)** | **PARTIAL** | typer exists `keyboard.py:146,226` but wired only to nicknames — reuse for player name = small new glue |
| **GENDER selection (intro)** | **NEW** | no gender code anywhere in repo (confirmed) |
| **New-Game / title-menu driver + Birch speech + clock set** | **NEW** | no New-Game menu handler, no Birch-speech handler, no intro-clock setter |
| **Choose starter from Birch's bag** | **COVERED** | `starters.py:80-144` (RSE Hoenn selection) |
| **Talk to NPC / interact** | **COVERED** | `talk_to_npc` `higher_level_actions.py:513` |
| **Field-move EXECUTION (Cut/Strength/Flash/Rock Smash/Surf/Dig/Fly)** | **COVERED** | `use_field_move` `menuing.py:804` (badge-checked); wrappers `use_strength`/`use_rock_smash` `puzzle_solver.py:52,61`; Surf/Waterfall/Dive auto via pathfinder |
| **Field-move ROUTING to a specific story tree/boulder + detection** | **NEW (partial)** | only end-game puzzle maps are authored (`puzzle_solver.py:107`); critical-path Cut trees / Strength boulders / Rock Smash rocks on routes are **not** authored |
| **Teach HM/TM to party** | **COVERED** | `teach_hm_or_tm` `items.py:160` (validates learnability, protects HMs) |
| **Item pickup (overworld balls / hidden items)** | **NEW** | no composable `pick_up_item` helper; done ad hoc in some modes only |
| **Shopping (buy/sell)** | **COVERED** | `buy_in_shop` `higher_level_actions.py:301`, `sell_in_shop` `:399` (expects mart menu open) |
| **Healing at Pokémon Center** | **COVERED** | `heal_in_pokemon_center` `:172`; center lookup `map.py:86` |
| **When-to-heal orchestration across overworld story** | **NEW** | heal is only wired into grind loops today; a story-level heal policy must be added |
| **Catch team members** | **COVERED** | `CatchStrategy` `catch.py:23`; opportunistic-catch scaffolding (#43) |
| **Evolution management** | **COVERED (config)** | `battle_evolution_scene.py:17`; set `stop_evolution=false` |
| **Gym puzzles** | **PARTIAL** | `puzzle_solver.py` covers end-game puzzles, **not** gym interiors (e.g. Mauville switches, Petalburg rooms, Fortree gym, Mossdeep) — each needs authoring |
| **Read badges/flags/vars/items/party/map for progress** | **COVERED** | `get_event_flag` `memory.py:336`; flag table `data/event_flags/emerald.txt`; `MapRSE` `map_data.py:792`; `_asserts.py` |
| **The chapter orchestrator itself** | **NEW** | no cross-map plot driver exists; every mode is self-contained |

**Big new pieces, ranked:** (1) chapter orchestrator + per-map data authoring
(the bulk of the work — dozens of authored routes/NPC-ids/waypoints); (2) intro
automation (New Game + gender + name + clock); (3) critical-path field-move
routing (Cut trees, Strength/Rock Smash obstacles, gym-interior puzzles);
(4) wiring + hardening `navigate_to_anywhere` and teaching it to *satisfy* gates
(or letting the orchestrator sequence gate-satisfaction); (5) stronger boss AI.

---

## 6. RISKS / UNKNOWNS / OPEN QUESTIONS + Build order

### 6.1 Top risks
1. **Naive battle AI loses winnable boss fights.** Max-damage-only selection with
   no status/setup/switch handling can lose to Norman's Slaking, Tate&Liza's
   double battle, or the Elite Four. Mitigation: (a) level buffers (§4.3), (b) a
   `StoryBattleStrategy.decide_turn` upgrade for flagged boss encounters, (c) heal-
   item usage in-battle (the engine supports `UseItem` turns).
2. **`navigate_to_anywhere` can't pass gated warps** — it *fails at runtime* when a
   door is locked/HM/story-gated (`global_navigation.py:127-132`). The orchestrator
   must own gate-sequencing (do the plot event that unlocks the door *before*
   trying to path through it), and catch/retry on `BotModeError` rather than crash.
   It's also **not exported** from `modes/util/__init__.py` and **unused** today —
   needs wiring + real-world testing.
3. **Massive per-map data authoring surface** — every gym interior, every
   critical-path tree/boulder, every plot NPC id and trigger tile must be
   authored and verified per map. This is the true cost, and it's brittle (NPC
   object ids, coords). Mitigation: build incrementally, one chapter at a time,
   each independently testable from a save parked at its start.
4. **Version/symbol fragility** — modes lean on Emerald-specific task/script symbol
   names; three-way `is_rs/is_emerald/is_frlg` branches abound
   (`DOCUMENTATION/03:680-682`). v1 is Emerald-only to contain this.
5. **Scripted-event avoidance vs triggering** — the pathfinder defaults to
   *avoiding* scripted tiles (`avoid_scripted_events=True`); story mode frequently
   needs the opposite (`expecting_script=True` / `avoid_scripted_events=False`).
   Getting this wrong = the bot walks *around* the event it needs to trigger.
6. **Softlocks / unexpected dialogue** — Match Call, Pokénav, wild double battles,
   rival surprise battles. Many are covered by listeners (`PokenavListener` etc.),
   but story mode must be robust to "an unexpected script is running" (watchdog
   #E1 synergy).

### 6.2 Open questions (for the user / later passes)
- Should the bot **grind for items/money** (buy Potions/Revives, Great Balls) or
  run lean? Affects shopping sub-steps.
- **Catch quotas:** does the user want a specific team, or "whatever works"?
- **Fly usage:** obtain + use Fly for fast travel (big time saver, needs Feather
  Badge) or walk everything?
- **Post-game scope:** stop at Champion (v1) vs continue to Rayquaza-caught /
  National Dex / Battle Frontier. #45 defers this.
- **In-battle item use policy** for bosses (buy & use X-items / Full Restores?).

### 6.3 Recommended CHUNKED build order (each independently testable)
1. **Read-only progress detector + chapter registry** — ✅ **DONE 2026-07-20**
   (`modules/story/`: `chapters.py` registry of 30 chapters + `progress.py`
   `detect_progress()`; unit battery `tests/test_story_progress.py`, 12/12).
   Live-tested on the real `Nick - Emerald` save (read-only; `.sav` md5
   unchanged). **See §12 for the detection-model finding — this chunk did its
   job and reshaped the model.**
2. **Chapter 4 (Gym 1) in isolation** — start from a save parked in Rustboro;
   author the gym route + Roxanne id; prove "navigate → auto-win gym → badge
   detected → heal." This exercises the core loop with the least new work.
3. **Intro (Chapter 0)** — ✅ **DONE 2026-07-20** (built ahead of step 2, per
   user request to start with the intro). `modules/story/intro.py`
   (`run_intro(name, gender)`) drives title → New Game → Birch's speech →
   gender → name → **lands controllable INSIDE the moving truck**.
   `plugins/custom_modes/story_mode.py` = the `StoryMode` bot (fresh boot →
   intro; existing save → detect & report). Name/gender from
   `<profile>/story.yml` (`modules/story/config.py`). Verified on fresh
   throwaway profiles: boy/NICK, girl/MAY, config/ASH — all land in the truck
   with correct name+gender, deterministic (~4600 frames). **Key live facts
   learned (§13).** Still TODO for the intro: the "existing save" Continue path
   from the title screen (currently the intro path assumes a save-less boot).
4. **Chapters 2-3** — fill Petalburg/Woods/Cut, including the **first HM teach**
   (`teach_hm_or_tm`) and first field-move routing (Cut). Proves the HM pipeline.
5. **Wire + harden `navigate_to_anywhere`** — export it, add gate-aware retry,
   test cross-region routing on the real world graph.
6. **Chapters 5-10** — Dewford/Slateport/Mauville; introduces Flash, Rock Smash,
   Bike, first mid-game gym puzzles.
7. **Chapters 11-16** — Chimney/Magma, Strength, Lavaridge, Norman (Surf), Fortree
   (Fly), Devon Scope/Kecleon. The HM-gate-heavy stretch.
8. **Chapters 17-22** — Aqua arc, Dive, Mossdeep double gym, Seafloor, Sootopolis/
   Rayquaza, Wallace (Waterfall).
9. **Chapters 23-24** — Victory Road (Strength puzzles) + Elite Four + Champion.
   Boss-AI upgrade lands here if not earlier.

**Where the progressed save helps:** every chapter after 0 can be tested by
starting from a save (or savestate) parked at its beginning — the `Nick - Emerald`
profile and its many savestates (`profiles/Nick - Emerald/states/`) let a
developer jump straight to a mid-game chapter without replaying the intro. Build
a small library of "parked at chapter N" savestates as a test fixture.

---

## 7. SELF-SANITY-CHECK (re-read against known Emerald progression)

Things I am **confident** about (code-confirmed or well-established):
- The 8 gym order, cities, types, and badge flags (`DEFEATED_*_GYM` 1264-1271,
  `BADGE0N_GET` 2151-2158) — flag names verified in
  `modules/data/event_flags/emerald.txt`.
- Endgame flags `IS_CHAMPION` (2175) + `SYS_GAME_CLEAR` (2148), Elite Four flags
  (1275-1278) — verified.
- HM field-use badge gates for **Surf (Badge5), Dive (Badge7), Waterfall (Badge8),
  Rock Smash (Badge3), Cut (Stone)** — CONFIRMED IN CODE (`map_path.py:684,690,698`;
  `rock_smash.py:143`; `menuing.py:812`).
- All HM-received flags exist (`RECEIVED_HM_CUT/FLASH/FLY/STRENGTH/SURF/DIVE/
  WATERFALL/ROCK_SMASH`) — verified in the flag table.
- Key-item flags exist: `RECEIVED_WAILMER_PAIL` (94), `RECEIVED_GO_GOGGLES` (221),
  `RECEIVED_DEVON_SCOPE` (285), `RECEIVED_POKENAV` (188), `RECEIVED_BIKE` (90),
  `RECEIVED_METEORITE` (115), `RECEIVED_SS_TICKET` (291), rods (152/227/257),
  `GOT_BASEMENT_KEY_FROM_WATTSON` (208), room keys (240-243), Devon Goods chain
  (142/143/144/148/149 — 144 = Rustboro return, 149 = Slateport/Stern delivery
  **[P3]**) — verified.
- Team arc flags: `MET_ARCHIE_METEOR_FALLS` (207), `DEFEATED_EVIL_TEAM_MT_CHIMNEY`
  (139), `TEAM_AQUA_ESCAPED_IN_SUBMARINE` (112), `GROUDON_AWAKENED_MAGMA_HIDEOUT`
  (111), `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (129), `DEFEATED_MAGMA_SPACE_CENTER`
  (117), `LEGENDARIES_IN_SOOTOPOLIS` (83), `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` (307),
  `DEFEATED_RAYQUAZA` (448), `DEFEATED_WALLY_VICTORY_ROAD` (126) — verified.

**[P2] RESOLVED in Pass 2** (was "unsure" in Pass 1 — now settled against
in-repo ground truth):
1. **All 8 HM field-use badge gates** — RESOLVED, code-confirmed (`menuing.py:
   810-833`); see §2.1. Fly = Feather (BADGE06). A `fly_to` **fork bug** was found
   (checks BADGE03 for Emerald — wrong).
2. **HM/key-item handoff locations** — filled in §2.3 with receipt flags. HM04
   **Strength corrected to Rusturf Tunnel** (was wrongly "near Mt. Chimney"). HM08
   Dive code-anchored to Steven's house (`ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133).
   Softer NPC/tile facts are tagged *verify live* in the §2.3 table.
3. **Norman prerequisite** — 4 badges; var `PETALBURG_GYM_STATE` (event_vars 133)
   confirmed present (semantics: gates the challenge until 4 badges). Row 13.
4. **Gym-interior puzzles** — all 8 ENUMERATED and grounded in real scripts, §2.4.
   Correction: **Brawly (Gym 2) IS a puzzle** (dark room), not "none". **Gym 8 =
   Juan**, cracked-ice floor.
5. **Missed mandatory beats** — added: **Mt. Pyre (16b)**, **Slateport Harbor sub
   theft (16c)**, **Magma Hideout / Groudon (16d)**, and made **Mr. Briney + Peeko
   rescue (5b)** explicit as the boat gate.
6. **Intro symbols** — RESOLVED: the full `Task_NewGameBirchSpeech_*` chain +
   `Task_*MainMenu*`, `sIntroCharacterGender`, `sNamingScreen`, `StartWallClock`/
   `ScrCmd_initclock`/`sClockInfo`, `WarpToTruck` all exist in `pokeemerald.sym`
   (§3 Ch0). Only the *exact cursor positions/timing* need live observation.
7. **`navigate_to_anywhere`** — re-read (`global_navigation.py:51-139`): it
   **raises `BotModeError` on any gated/locked warp** (lines 127-132) and
   **cannot route through Dive or dynamic warps** (lines 108-111). Confirmed
   unwired/ungated. See "still needs work" below.

Things that **genuinely still need LIVE discovery / testing** (cannot be settled
from in-repo data alone):
1. **Exact NPC object-ids and trigger tiles** for every *verify live* item in
   §2.3 (Surf house in Petalburg, Fly NPC on Rt 119, Rock Smash house on Rt 111,
   Go-Goggles giver in Lavaridge, Waterfall trigger in Sootopolis). Flags prove
   *receipt*; the *where-to-stand* must be read off a live/parked save.
2. **[P3 RESOLVED] The late-game chapter ORDERING** (Mt. Pyre → Slateport sub
   theft → Magma Hideout/Groudon → Aqua Hideout → Mossdeep → Tate&Liza) is now
   **CONFIRMED against an external Emerald walkthrough** (psypokes / Neoseeker /
   Bulbapedia) — §2 rows 16b→16c→16d→17→18→19 match the canonical order exactly.
   The Mt. Pyre summit yields the **Magma Emblem** that gates the Magma Hideout.
   No live check is needed for the ordering itself.
3. **Mandatory-vs-shortcut field-move obstacles** — which specific Cut tree /
   Strength boulder / Rock Smash rock / Surf/Dive/Waterfall spot is on the *only*
   path vs a shortcut. Late-game water HM sequence (Surf→Dive→Waterfall to reach
   Sootopolis/Seafloor/Ever Grande) is asserted from `can_surf/dive/waterfall`
   gating but the exact required tiles on Rt 126/128/132-134 must be confirmed live.
4. **`navigate_to_anywhere` real-world leg coverage** — export it, add gate-aware
   retry, and test **leg-by-leg**; it definitely cannot open story-gated doors or
   route Dive segments, so the orchestrator must own gate-sequencing.
5. **Double-battle AI quality** (Tate&Liza Gym 7, Steven Space-Center tag) —
   `decide_turn_in_double_battle` exists but is untuned; test on a parked save.
6. **Intro cursor/timing** — the symbols are known (§3 Ch0); the exact cursor
   deltas and frame waits for gender/name/clock must be observed on a live New Game.

**Net:** engine feasibility remains high and well-cited. Pass 2 removed the
"soft-fact" risk from HM gates, item sources, gym puzzles, intro symbols, and the
late-game beat list (all now grounded). Residual risk is concentrated in (a) the
large per-map authoring surface (NPC ids / trigger tiles / puzzle solutions), (b)
the exact late-game ordering, (c) critical-path obstacle identification, and (d)
wiring/hardening `navigate_to_anywhere`. None are blockers.

---

## 8. PASS 2 VERIFICATION — what changed / was caught

Adversarial re-audit on **2026-07-19** against the bot's own ground truth
(`event_flags/emerald.txt`, `event_vars/emerald.txt`, `symbols/pokeemerald.sym`,
`menuing.py`, `map_path.py`, `global_navigation.py`).

### 8.1 ERRORS corrected
- **Gym 8 leader = JUAN, not Wallace.** Wallace is the **Champion** (Ch24). Both
  the overview table (Ch22) and the §4.3 level table wrongly named Wallace as the
  gym leader. Confirmed by `SootopolisCity_Gym_1F_EventScript_Juan` and
  `ENABLE_JUAN_MATCH_CALL` (473) in the flag/sym data. **Fixed.**
- **HM04 Strength source was WRONG** — the doc said "NPC near Mt. Chimney"; it is
  the **Rusturf Tunnel** man (`RUSTURF_TUNNEL_OPENED` 199 context). **Fixed (§2.3).**
- **Brawly's gym (Gym 2) was implied to have no puzzle** — it is a **dark-room
  puzzle** (`DewfordTown_Gym_EventScript_BrightenRoom`). **Fixed (§2.4).**
- **Fly badge gate uncertainty** — RESOLVED to **Feather (BADGE06)**
  (`menuing.py:826`), and a **fork bug** was found: `fly_to`
  (`higher_level_actions.py:52,55`) checks BADGE03 for Emerald too (only right for
  FRLG). **Documented (§2.1).**

### 8.2 MISSED mandatory beats added
- **Mr. Briney & the Peeko rescue (Rusturf Tunnel)** — the gate that unlocks
  Briney's boat to Dewford/Slateport. Was only glancingly mentioned; now an
  explicit mandatory beat (row **5b**, `MR_BRINEY_SAILING_INTRO` 147).
- **Mt. Pyre** (row **16b**) — the orb-theft / Magma-vs-Aqua summit beat, entirely
  absent from the Pass-1 skeleton.
- **Slateport Harbor submarine theft** (row **16c**) — `EVIL_TEAM_ESCAPED_STERN_
  SPOKE` (271); distinct from the *early* Oceanic-Museum visit; was absent.
- **Magma Hideout / Groudon awakening** (row **16d**) —
  `GROUDON_AWAKENED_MAGMA_HIDEOUT` (111); listed in Pass-1's "confident flags" but
  **never given a chapter**. Now a mandatory beat.

### 8.3 RESOLVED specifics now baked in
- **All 8 HM→badge field gates** code-confirmed, single source `menuing.py:810-833`
  (§2.1).
- **HM & key-item handoff table** with receipt flags + confidence (§2.3).
- **Gym-puzzle enumeration**, each grounded in a real `pokeemerald.sym` symbol
  (§2.4).
- **Intro automation symbols** — the whole `Task_NewGameBirchSpeech_*` chain +
  main-menu tasks + gender var + naming screen + wall-clock scripts identified in
  the .sym (§3 Ch0); only cursor/timing needs live observation.
- **Norman gate** — 4 badges via `PETALBURG_GYM_STATE` (var 133) (row 13).
- **`navigate_to_anywhere`** re-confirmed to raise on gated warps and to exclude
  Dive/dynamic warps (§7 item 7).

### 8.4 Per-chapter confidence (post-Pass-2)
| Chapters | Confidence | Why |
|----------|-----------|-----|
| 0 Intro | **High** on *what* to do (symbols known); **Medium** on cursor/timing (live) |
| 1-4 (Starter → Gym 1) | **High** — flags + puzzles (none) confirmed; primary build target |
| 5-6 (Devon/Peeko/Briney/Dewford/Flash) | **High** on beats/flags; **Medium** on Briney gate ordering (verify live) |
| 7-10 (Brawly→Slateport→Mauville→Wattson) | **High** on gyms/flags; gym puzzles enumerated |
| 11-13 (Chimney/Magma→Flannery→Norman) | **High** — Strength source & Norman gate corrected/confirmed |
| 14-16 (Rt118/Weather/Winona/Kecleon) | **High** on flags; **Medium** on Fly NPC + Weather Inst. ordering |
| 16b-16d (Mt. Pyre / Slateport sub / Magma Hideout) | **Medium** — beats+flags confirmed, exact **ordering verify live** |
| 17-19 (Aqua Hideout→Mossdeep→Tate&Liza) | **High** on flags; **Medium** on double-battle AI + hideout ordering |
| 20-22 (Seafloor→Sootopolis/Rayquaza→Juan) | **High** — Juan fixed; HM water-sequence gates confirmed; **Medium** on Waterfall trigger |
| 23-24 (Victory Road → E4 → Champion Wallace) | **High** on flags; **Medium** on boss-AI survivability + VR obstacle tiles |

---

## 9. PASS 3 ACCURACY AUDIT (2026-07-20)

Independent, skeptical triple-check. Every factual claim was cross-referenced
against **(A)** the bot's own ROM ground truth (in-repo) **and (B)** an external
Emerald walkthrough. "CONFIRMED" = both sources agree. "CORRECTED" = an error
was fixed (what→what + source). "VERIFY-LIVE" = neither source can settle it;
needs an in-game/parked-save read.

### 9.1 Claim-by-claim verdicts

| Claim area | Verdict | Detail / source |
|---|---|---|
| **8 gym leaders, types, badges, order** (Roxanne/Rock/Stone → Brawly/Fighting/Knuckle → Wattson/Electric/Dynamo → Flannery/Fire/Heat → Norman/Normal/Balance → Winona/Flying/Feather → Tate&Liza/Psychic/Mind → Juan/Water/Rain) | **CONFIRMED** | pokemondb gym list + `DEFEATED_*_GYM` 1264-1271 & `BADGE0N_GET` 2151-2158 in `event_flags/emerald.txt` |
| **Gym 8 = JUAN; Wallace = Champion** (Pass-2 fix) | **CONFIRMED** | `SootopolisCity_Gym_1F_EventScript_Juan` + `EverGrandeCity_ChampionsRoom_EventScript_Wallace` in `pokeemerald.sym`; external gym list |
| **Badge→HM field-use gates** (Stone=Cut, Knuckle=Flash, Dynamo=RockSmash, Heat=Strength, Balance=Surf, Feather=Fly, Mind=Dive, Rain=Waterfall) | **CONFIRMED** | `menuing.py:810-833` (each `case`) + external gym list agree exactly; `map_path.py:687/693/701` (surf/dive/waterfall) + `rock_smash.py:143` |
| **Fly field gate = Feather/BADGE06** (Pass-2 fix) | **CONFIRMED** | `menuing.py:826` |
| **`fly_to()` fork bug** (checks BADGE03 for Emerald) | **CONFIRMED (bug real)** | `higher_level_actions.py:52,55` — both RSE & FRLG branches read `BADGE03_GET`; wrong for Emerald |
| **HM04 Strength from Rusturf Tunnel** (Pass-2 fix) | **CONFIRMED** | pokemondb ("Wanda's boyfriend after breaking rocks") + `RUSTURF_TUNNEL_OPENED` 199 |
| **Brawly Gym = dark-room puzzle** (Pass-2 fix) | **CONFIRMED** | `DewfordTown_Gym_EventScript_*BrightenRoom` symbols present |
| **All 8 gym puzzle mechanics** (§2.4) | **CONFIRMED** | every grounding symbol verified in `pokeemerald.sym` (BrightenRoom / MauvilleGymPressSwitch / DoLavaridgeGym1FWarp / PetalburgGymSlideOpenRoomDoors / RotatingGate_RotateInDirection / DoMossdeepGymWarp / SetSootopolisGymCrackedIceMetatiles) |
| **HM06 Rock Smash location** | **CORRECTED** | Pass 2 said "Route 111" → **Mauville City, SE house** (pokemondb / Thonky / PokéCoders). Pass-2 REGRESSION reverted. |
| **Fortree Gym order vs Devon Scope/Kecleon** | **CORRECTED** | Doc had Winona (Ch15) **before** Devon Scope/Kecleon (Ch16). Reality: the invisible **Kecleon blocks the Fortree Gym door**; **Devon Scope (Steven, Rt 120) is required to enter** → new row **14b** precedes Winona (Bulbapedia/Thonky/PokéBase). |
| **DELIVERED_DEVON_GOODS (149) chapter** | **CORRECTED** | Was on Ch5 (Rustboro). Reality: 149 = delivery to **Capt. Stern in Slateport** (Ch8); Rustboro return = **RETURNED_DEVON_GOODS (144)** (walkthrough + flag names 144/148/149) |
| **HM02 Fly giver** | **CORRECTED (refined)** | "generic NPC near Weather Institute" → **the RIVAL** (May/Brendan) after the Rt 119 battle (pokemondb/GameFAQs) |
| **Magma Hideout entry gate** | **CORRECTED (refined)** | Primary gate is the **Magma Emblem** from Mt. Pyre summit, not "Rock Smash/Strength inside" (psypokes/Neoseeker) |
| **Late-game order** (Mt.Pyre→Slateport sub→Magma Hideout/Groudon→Aqua Hideout→Mossdeep→Tate&Liza) | **CONFIRMED** | psypokes/Neoseeker/Bulbapedia match §2 rows 16b→16c→16d→17→18→19; upgraded from Pass-2 "verify live" |
| **Weather Institute = Team AQUA (Emerald), gives Castform** | **CONFIRMED** | external walkthrough (Emerald = Aqua; R = Magma) |
| **Norman is Gym 5, needs 4 badges** | **CONFIRMED** | external gym list (#5) + `PETALBURG_GYM_STATE` var 133 |
| HM01 Cut = Rustboro Cutter's house | **CONFIRMED** | pokemondb + `RECEIVED_HM_CUT` 137 |
| HM05 Flash = Granite Cave hiker | **CONFIRMED** | pokemondb + `RECEIVED_HM_FLASH` 109 |
| HM03 Surf = Petalburg, Wally's father, after Norman | **CONFIRMED** | pokemondb + `RECEIVED_HM_SURF` 122 |
| HM07 Waterfall = Wallace, Sootopolis, after crisis | **CONFIRMED** | pokemondb (Emerald) + `RECEIVED_HM_WATERFALL` 312 |
| HM08 Dive = Steven's house, Mossdeep | **CONFIRMED** | pokemondb + `ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133 |
| Devon Goods questline (Rusturf grunt frees Peeko, unlocks Briney's boat) | **CONFIRMED** | Thonky/StrategyWiki + `MR_BRINEY_SAILING_INTRO` 147, `HIDE_RUSTURF_TUNNEL_BRINEY` 879 |
| Slateport Oceanic Museum (Aqua grunts + Archie, deliver to Stern) | **CONFIRMED** | Bulbapedia + museum hide-flags 883-887 |
| All key-item / team-arc / endgame **flag numbers** cited (badges, gyms, HMs, orbs, room keys, Electrodes, E4 1275-1278, IS_CHAMPION 2175, SYS_GAME_CLEAR 2148, STARTER_MON var 35, PETALBURG_GYM_STATE var 133, etc.) | **CONFIRMED** | every number re-grepped in `event_flags/emerald.txt` / `event_vars/emerald.txt` — all exact |
| Intro/Birch-speech/clock/naming symbols (§3 Ch0) | **CONFIRMED (exist)** | previously grepped in Pass 2; symbol names valid; cursor/timing still **VERIFY-LIVE** |
| Exact NPC object-ids / trigger tiles for every *verify live* item | **VERIFY-LIVE** | flags prove receipt; where-to-stand needs a parked save (unchanged from Pass 2) |
| `RECEIVED_MAGMA_EMBLEM` flag | **VERIFY-LIVE** | no such flag in the repo table; Emblem gate is well-established externally but the exact flag/var must be read in-game |

### 9.2 Errors found & fixed in Pass 3 (summary)
1. **Rock Smash location** — Pass-2 regression "Route 111" → **Mauville City (SE house)**. (Overview row 9, §2.3.)
2. **Fortree Gym ordering** — Devon Scope + Kecleon reveal is a **prerequisite to Gym 6**; inserted row **14b** before Winona and flagged the gate. (Overview rows 14b/15/16.)
3. **DELIVERED_DEVON_GOODS (149)** — moved from Ch5 to Ch8 (Slateport/Stern); Ch5 now correctly uses **RETURNED_DEVON_GOODS (144)**. (Overview rows 5/8, §2.3.)
4. **HM02 Fly giver** — refined to **the Rival** after the Rt 119 battle. (Overview row 14, §2.3.)
5. **Magma Hideout gate** — refined to the **Magma Emblem** from Mt. Pyre. (Overview row 16d.)

### 9.3 Source-disagreements between (A) ROM and (B) walkthrough
**None of substance.** Every ROM flag/symbol and every external walkthrough fact
agreed once the doc's own three errors above were corrected. The only "gap" is
the Magma Emblem, which the external source documents but which has **no matching
flag** in the in-repo table (so it is marked VERIFY-LIVE, not a disagreement).

### 9.4 Final per-chapter accuracy verdict (post-Pass-3)
| Chapters | Verdict |
|---|---|
| 0 Intro / 1 Starter | **Accurate**; symbols exist; cursor/timing verify-live |
| 2-4 (Petalburg → Woods/Cut → Gym 1 Roxanne) | **Accurate** — no errors found |
| 5 (Devon/Peeko/Rusturf/Rival) | **Fixed** — flag 144 vs 149 corrected; beats accurate |
| 6-8 (Dewford/Flash/Gym 2 → Slateport) | **Fixed** — Slateport now carries flag 149; otherwise accurate |
| 9-10 (Mauville/Bike → Gym 3 Wattson) | **Fixed** — Rock Smash location corrected to Mauville |
| 11-13 (Chimney/Magma → Gym 4 Flannery → Gym 5 Norman) | **Accurate** — Strength source & Norman 4-badge gate hold up |
| 14 (Rt118/Weather/Fly) | **Fixed** — Fly giver = Rival |
| 14b-15 (Devon Scope/Kecleon → Gym 6 Winona) | **Fixed (reordered)** — Devon Scope now precedes Winona |
| 16-16d (Lilycove → Mt.Pyre → Slateport sub → Magma Hideout) | **Accurate + confirmed** — late-game order matches external walkthrough; Magma Emblem gate added |
| 17-19 (Aqua Hideout → Mossdeep/Space Center → Gym 7 Tate&Liza) | **Accurate** — order confirmed |
| 20-22 (Seafloor/Kyogre → Sootopolis/Rayquaza → Gym 8 Juan) | **Accurate** — Juan-after-crisis order correct; Waterfall from Wallace |
| 23-24 (Victory Road → E4 Sidney/Phoebe/Glacia/Drake → Champion Wallace) | **Accurate** — roster & flags correct |

### 9.5 Overall confidence statement
After three independent passes and a two-source cross-check, the story-mode
design's **factual backbone is now high-confidence**: all 8 gyms
(leader/type/badge/order/puzzle), all 8 HM field-use gates, all HM givers, the
key-item receipt flags, the villain-arc beats, and — newly — the **late-game
chapter ordering** are confirmed by both the ROM ground truth and an external
walkthrough. Pass 3 corrected **3 substantive errors** (one of them a Pass-2
regression) plus **2 refinements**. Residual uncertainty is **not** about the
plot/facts anymore — it is confined to (a) exact NPC object-ids & trigger tiles
(VERIFY-LIVE on a parked save), (b) the Magma Emblem's exact flag/var, and (c)
engineering risks unrelated to accuracy (per-map authoring surface, boss AI,
`navigate_to_anywhere` gating). The doc is safe to build against.

**Sources (external, Pass 3):** [pokemondb gym list](https://pokemondb.net/emerald/gymleaders-elitefour) · [pokemondb HM chart](https://pokemondb.net/ruby-sapphire/hms) · [Bulbapedia Emerald walkthrough](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald) · [Thonky RSE walkthrough](https://www.thonky.com/pokemon-ruby-sapphire-emerald/) · [psypokes Emerald walkthrough](https://www.psypokes.com/emerald/walkthrough.php) · [GameFAQs Emerald](https://gamefaqs.gamespot.com/gba/921905-pokemon-emerald-version) · [PokéCoders Rock Smash](https://www.pokemoncoders.com/how-to-get-rock-smash-in-pokemon-emerald/)

---

## 10. PASS 4 — INDEPENDENT RE-DERIVATION (2026-07-20)

**Method:** facts were re-derived **from scratch** — (A) directly from the bot's
in-repo ROM ground truth (`event_flags/emerald.txt`, `event_vars/emerald.txt`,
`menuing.py:810-833`, `modes/rock_smash.py:143`, `map_path.py:684-704`,
`modes/util/higher_level_actions.py:50-61`, `items.json`) and (B) two-to-three
independent external walkthroughs (Bulbapedia, Thonky, pokemondb, PokéBase,
StrategyWiki) — **without** reading the doc's own conclusions first, then diffed
against the doc. Goal: catch NEW errors AND re-check that Pass 3's own five
corrections were not themselves wrong.

### 10.1 Re-audit of Pass 3's five corrections (each independently re-derived)

| Pass-3 correction | Pass-4 verdict | Independent basis |
|---|---|---|
| HM06 Rock Smash = **Mauville City** SE house (reversing Pass-2's "Route 111") | **STILL CORRECT** | PokéCoders + Thonky Mauville page + Bulbapedia: house right/SE of the Poké Mart, needs Stone+Knuckle badges |
| **Fortree Gym gated by Devon Scope + Kecleon reveal** (row 14b before Winona) | **STILL CORRECT** | PokéBase + Thonky Fortree + StrategyWiki Rt 120: Steven gives Devon Scope after a Lv30 Kecleon battle on Rt 120; invisible Kecleon blocks the gym door until revealed |
| **`DELIVERED_DEVON_GOODS` (149) = Slateport/Capt. Stern** (not Rustboro); Rustboro = `RETURNED_DEVON_GOODS` (144) | **STILL CORRECT** | Flag table 142→143→144→148→149 chain matches Bulbapedia Part 4 / Neoseeker: Rustboro president = return (144); Stern at Slateport Oceanic Museum = deliver (149), Dock-rejected first (148) |
| **HM02 Fly given by the RIVAL** after the Rt 119 battle | **STILL CORRECT** | Bulbapedia Part 10 + StrategyWiki Rt 119: rival (Brendan/May) battle on the north Rt 119 bridge past the Weather Institute yields HM02 Fly |
| **Magma Hideout gated by the Magma Emblem** from Mt. Pyre summit | **STILL CORRECT (upgraded)** | Bulbapedia Magma Hideout + Mt. Pyre pages: summit caretaker gives the Emblem; the Jagged Pass entrance auto-appears only with it in the bag. **Upgraded**: the Emblem is a **KEY ITEM** (`items.json`), not a flag — see 10.3 |

**All five Pass-3 corrections independently reconfirmed. Pass 3 introduced no
new errors.**

### 10.2 Independently-derived facts → diff against the doc

| Independently-derived fact | Source | Verdict vs doc |
|---|---|---|
| 8 gyms: Roxanne/Rock/Stone → Brawly/Fighting/Knuckle → Wattson/Electric/Dynamo → Flannery/Fire/Heat → Norman/Normal/Balance → Winona/Flying/Feather → Tate&Liza/Psychic/Mind → Juan/Water/Rain | pokemondb + `DEFEATED_*_GYM` 1264-1271, `BADGE0N_GET` 2151-2158 | **AGREES** |
| HM field-use badge gates: Cut=B1, Flash=B2, RockSmash=B3, Strength=B4, Surf=B5, Fly=B6, Dive=B7, Waterfall=B8 | `menuing.py:811-833` (re-read every `case`) | **AGREES** |
| `can_surf`=BADGE05, `can_dive`=BADGE07, `can_waterfall`=BADGE08 | `map_path.py:687/693/701` | **AGREES** |
| Rock Smash field gate re-checked | `modes/rock_smash.py:143` = `BADGE03_GET` | **AGREES** |
| `fly_to()` fork bug: **both** RSE and FRLG branches read `BADGE03_GET` (wrong for Emerald, should be BADGE06) | `modes/util/higher_level_actions.py:52 & 55` (path is `modes/util/`, not repo root — doc's citation omits the subdir) | **AGREES** (bug real; minor citation-path nit noted) |
| Devon Goods chain 142 STOLEN / 143 RECOVERED / 144 RETURNED / 148 DOCK_REJECTED / 149 DELIVERED | `event_flags/emerald.txt:91-98` | **AGREES** |
| HM receipt flags: Cut 137, Flash 109, RockSmash 107, Strength 106, Surf 122, Fly 110, Dive 123, Waterfall 312 | `event_flags/emerald.txt` | **AGREES** |
| Key items: Bike 90, Meteorite 115, PokéNav 188, Steven Letter 189, Basement Key 208, Go-Goggles 221, Devon Scope 285, Kecleon-fled 295 | `event_flags/emerald.txt` | **AGREES** |
| Vars: STARTER_MON 35, PETALBURG_GYM_STATE 133, MT_PYRE_STATE 185 | `event_vars/emerald.txt` | **AGREES** |
| Endgame: E4 1275-1278, SYS_GAME_CLEAR 2148, IS_CHAMPION 2175 | `event_flags/emerald.txt` | **AGREES** |
| **Petalburg Woods grunt = researcher-rescue, NOT a Devon-Goods theft** (grunt flees, Great Ball reward); theft/recovery happen post-Gym-1 | Bulbapedia Part 2 | **DOC WRONG → FIXED [P4]** (overview row 3 + Ch3 step 2) |
| **HM01 Cut is in RUSTBORO CITY** (Cutter's House, W of the PC), not Route 104 | Thonky Rustboro + pokemondb | **DOC WRONG → FIXED [P4]** (Ch3 step 3 contradicted §2.3, which was right) |
| **Magma Emblem is a KEY ITEM** (`items.json` "Magma Emblem"), not a flag; no `RECEIVED_MAGMA_EMBLEM` flag exists | `items.json` + `event_flags/emerald.txt` (no match) | **NEW-RESOLUTION [P4]** (was VERIFY-LIVE; mechanism now known — gate on bag item) |
| Mt. Pyre progress var `MT_PYRE_STATE` (185) exists | `event_vars/emerald.txt:186` | **NEW-RESOLUTION [P4]** (var identified; exact completion value still live) |
| Exact NPC object-ids / trigger tiles (Surf house, Fly rival tile, Rock Smash house, Go-Goggles giver, Waterfall trigger, gym-interior waypoints) | — | **STILL-VERIFY-LIVE** (unchanged; flags prove receipt, not where-to-stand) |
| Intro cursor deltas / frame-timing (gender/name/clock) | — | **STILL-VERIFY-LIVE** (symbols known; timing needs a live New Game) |

### 10.3 NEW errors found & fixed in Pass 4

1. **Petalburg Woods Devon-Goods flag misattribution.** Overview row 3 and Ch3
   step 2 attributed `DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143)
   to the Petalburg Woods grunt. **Reality:** the Woods grunt is a *researcher
   rescue* — the grunt flees and the researcher gives a **Great Ball**; the
   Devon Goods theft (a grunt bolts from Devon Corp in Rustboro **after Gym 1**)
   and the Rusturf-Tunnel recovery (which also frees Peeko) both belong to
   **Chapter 5**. Fixed in both places, tagged **[P4 FIX]**. *(Source: Bulbapedia
   Emerald Part 2.)*
2. **HM01 Cut location — internal contradiction.** Ch3 step 3 said Cut comes
   from a "**Route 104** (north) → Cutter's House"; §2.3 said "**Rustboro City**".
   §2.3 was right — the Cutter's House is **in Rustboro City, west of the Poké
   Center**. Fixed Ch3 to Rustboro, tagged **[P4 FIX]**. *(Source: Thonky
   Rustboro + pokemondb.)*

Both are **content-detail** errors (mislabeled event / wrong town for one HM
giver); **neither changes the chapter spine** (Cut still before Gym 1; Devon
theft/recovery still after Gym 1) nor any of the 8-gym / 8-HM / late-game facts.

### 10.4 verify-live items newly resolved

- **Magma Emblem gate** — moved VERIFY-LIVE → **RESOLVED**: it is a **key item**
  (`items.json` "Magma Emblem"), so the bot gates the Magma Hideout on
  *item-in-bag* (`get_item_bag()`), not on a nonexistent flag. Rows 16b/16d updated.
- **Mt. Pyre progress** — the var **`MT_PYRE_STATE` (185)** exists and tracks the
  arc (exact completion value still to be read on a parked save). Row 16b updated.

### 10.5 Remaining genuine live-only unknowns (unchanged, small)

Exact NPC object-ids & trigger tiles for the "verify live" givers (Surf house in
Petalburg, Fly rival tile on Rt 119, Rock Smash house in Mauville, Go-Goggles
giver in Lavaridge, Waterfall trigger in Sootopolis) and all per-map gym-interior
waypoints/puzzle solutions; the Magma Emblem/Mt-Pyre exact completion value;
intro cursor deltas & frame-timing. These are **where-to-stand / timing** facts,
not plot facts — they need a parked save, exactly as Pass 3 concluded.

### 10.6 Source disagreements

**None.** Every external walkthrough agreed with every other and with the ROM
ground truth on all audited points. The only prior "gap" — the Magma Emblem
having no flag — is now explained (it is a key item, not a flag), so it is no
longer even a gap.

### 10.7 Convergence statement

Pass 4 **did find NEW errors** — **two content-detail mistakes** that survived
Passes 1-3 (the Petalburg-Woods Devon-Goods flag misattribution and the Cut
"Route 104 vs Rustboro" contradiction), now fixed. It **also confirmed** that
**all five Pass-3 corrections were correct** (Pass 3 introduced no regressions),
resolved **two former verify-live items** (Magma Emblem = key item; `MT_PYRE_STATE`
var), and re-verified the entire factual backbone (8 gyms, 8 HM gates, HM/key-item
givers & flags, villain-arc beats, late-game order) against ROM + two external
sources with **zero disagreements**.

**Verdict:** the doc's **strategic backbone has fully converged and is
high-confidence**; the two Pass-4 fixes were localized detail corrections, not
structural. After four passes the only residual uncertainty is live-only
where-to-stand/timing data, which cannot be settled from repo + walkthroughs and
is correctly flagged as such. **Confidence: HIGH — safe to build against.**

**Sources (external, Pass 4):**
[Bulbapedia Emerald Part 2](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_2) ·
[Bulbapedia Part 4](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_4) ·
[Bulbapedia Part 10](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_10) ·
[Bulbapedia Magma Hideout](https://bulbapedia.bulbagarden.net/wiki/Magma_Hideout_(Jagged_Pass)) ·
[Thonky Rustboro City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/rustboro-city) ·
[Thonky Mauville City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/mauville-city) ·
[Thonky Fortree City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/fortree-city) ·
[PokéBase Kecleon/Fortree](https://pokemondb.net/pokebase/406508/how-do-i-get-past-the-invisible-kecleon-blocking-fortree-gym) ·
[StrategyWiki Route 120](https://strategywiki.org/wiki/Pok%C3%A9mon_Ruby_and_Sapphire/Route_120) ·
[PokéCoders Rock Smash](https://www.pokemoncoders.com/how-to-get-rock-smash-in-pokemon-emerald/)

---

## §12 — Detection-model finding (from building chunk 1, 2026-07-20)

Building the read-only detector and running it against the real `Nick -
Emerald` save produced a model-shaping result — exactly what a read-only
chunk-1 is for.

**The save is a hand-built test save, not a natural playthrough:** party is
shiny Celebi Lv100 + Sceptile Lv100 alongside a Lv9 shiny Bulbasaur, Lv6
Lotad, etc.; `BADGE01_GET` (Stone) is set but the Wally-tutorial and Cut-HM
flags are NOT, and a stray **Magma Emblem** key item is in the bag. Its event
flags are therefore **non-linear** — no single naive scan places it correctly.

**Two detection strategies were tried and REJECTED:**
1. *First-incomplete scan* (current = first chapter whose flag is unmet) —
   placed the save at **ch2 (Wally)** because an early flag was unset, ignoring
   the Stone Badge that proves it's past ch2. Wrong.
2. *Furthest-proof* (current = after the highest-order met milestone) — the
   stray Magma Emblem threw it to **ch16c (chapter 21/30)**. Wrong the other
   way; a single stray item dominated.

**Adopted model — the badge spine.** The 8 gym badges are earned strictly in
order and can't be skipped in normal play, so they are the reliable anchor.
Detection: take the **highest badge set** → its **bracket** (the chapters
played while holding exactly that many badges) → the first chapter in the
bracket whose finer milestone is unmet. Finer flags/items only refine *within*
the bracket and can never move placement outside it. Anything met ahead of the
badge count is reported as an **anomaly** (the test-save signature), not used
for placement. Result on the real save: **ch5 (Devon errand), 1 badge**, with
the Magma Emblem flagged as an anomaly. Correct and honest.

**Two registry data corrections this surfaced:**
- `HIDE_MT_PYRE_SUMMIT_MAXIE` is an **unreliable** completion proxy (read True
  on a save nowhere near Mt. Pyre). ch16b now uses the **Magma Emblem key item
  in bag** (the [P4] authoritative signal), matching how the bot will gate the
  Magma Hideout.
- `badges_before` per chapter is **derived** from which chapter earns each
  badge (the `badge` field), not hand-entered — one source of truth.

**Implication for later chunks:** the bot must not trust any single non-badge
flag as ground truth for "where am I"; badge level is the coarse gate and fine
flags refine. This is the same discipline the HM→badge gate table (§2.1)
already encodes.

---

## §13 — Intro (Chapter 0) live facts learned (2026-07-20)

Built by driving the intro headlessly against fresh throwaway profiles and
watching `GameState` + named tasks. Facts that will matter for later chunks:

- **Drive by tasks, not flags.** The intro sets almost no event flags. The
  named tasks are the ground truth: `Task_NewGameBirchSpeech_BoyOrGirl` (just
  before the gender menu), `Task_NewGameBirchSpeech_ChooseGender` (the menu),
  naming via `GameState.NAMING_SCREEN`.
- **Birch's speech reports as `GameState.MAIN_MENU`**, not OVERWORLD — so
  "advance the speech" means "mash A while state is not OVERWORLD."
- **Gender is position-based, NOT `sIntroCharacterGender`.** Reading that byte
  live gave the wrong result; the reliable method is: menu opens on BOY (top),
  press Down once for a girl, then A. (Confirmed: boy→male, girl→female.)
- **Naming:** `GameState.NAMING_SCREEN` flips a few frames BEFORE the keyboard
  struct pointer is populated — wait for `get_naming_screen_data() is not None`
  before calling `type_in_naming_screen()` (which raises on a null struct).
  Player names cap at **7** characters.
- **Name confirm ("is this okay?") is consumed by mashing A** (default = YES);
  a separate `wait_for_yes_no_question` HUNG (the confirm had already passed).
  Lesson: for a linear cutscene, mash A to a state target, don't wait on a
  specific transient task.
- **First controllable moment = `INSIDE OF TRUCK`** (map name), before the
  truck auto-drives to Littleroot. This is the clean, detectable end of
  Chapter 0. `ADVENTURE_STARTED` (116) is still FALSE here — it sets later
  (chunk B territory: stepping off / entering Littleroot).
- The whole intro is deterministic (~4593 frames boy / ~4627 girl) with no RNG
  dependence, so it replays reliably.

---

## §14 — Early-game (post-intro) live facts (2026-07-20, chunk B in progress)

Building forward from the truck. Iteration uses save states parked at each
sub-step (scratchpad `truck_base.ss1`, `house1f_base.ss1`) so we don't replay
the whole intro every test. `modules/story/early_game.py`.

- **Step-off sequence** (`walk_off_truck_and_into_house()`, DONE + tested):
  from INSIDE OF TRUCK, walk **east** (player starts local (2,2); exit warps are
  the x=4 column) → LITTLEROOT TOWN → `LittlerootTown_EventScript_StepOffTruck
  Male` → `...GoInsideWithMom` (Mom escorts you) → **warp into the house** →
  `PlayersHouse_1F_EventScript_MomFacePlayerMovingInMale` + her "set the clock"
  speech → control returns **inside PlayersHouse_1F at local (8,7)**.
- **`map_name` is STALE across warps** (still reads "LITTLEROOT TOWN" inside the
  house). Use the map **group/number** instead: PlayersHouse_1F = **(1, 0)**;
  Littleroot Town = (0, 9).
- **Cutscene end-detection:** require `player_avatar_is_controllable()` AND
  `not get_global_script_context().is_active` for ~15 consecutive frames. A
  single-frame check stops too early — there's a window where Mom's script is
  "active" but the avatar isn't locked yet (would stop at (3,10), wrong).
- **House 1F (1,0) warps:** stairs to 2F = **(8,2)**; the front door = (8,8)/
  (9,8). Player lands at (8,7). So B2 = walk to (8,2) → 2F → clock.
- `ADVENTURE_STARTED` (116) is still FALSE through all of this — it sets later.
- **NEXT (B2):** up the stairs (8,2) → 2F → interact with the wall clock → set
  the time. Then downstairs → Route 101 → Birch's bag → starter → first battle.

### §14.1 — Clock + downstairs findings (2026-07-20, chunk B continued)
- **Upstairs + clock** (`go_upstairs_and_set_clock()`, DONE + tested): 1F
  stairs (8,2) → 2F. Wall clock bg_event at **(5,1)** = `..._EventScript_
  WallClock` (stand (5,2) facing North). Flow: interact → mash A to
  `Task_SetClock_HandleInput` → let it fade (~40f) → **A accepts the shown
  time** → `Task_SetClock_HandleConfirmInput` (**cursor DEFAULTS TO NO**) → so
  **Up then A picks Yes** → done. Ends controllable on 2F (5,2). "Accept the
  default time" = never touch the D-pad on HandleInput, just Up+A on confirm.
- **After the clock, MOM COMES UPSTAIRS** (`PlayersHouse_2F_EventScript_
  MomComesUpstairsMale`), triggered when the player moves — talk plays in the
  bedroom, not downstairs.
- **BLOCKER for next turn — the 1F "movers" scene:** on the ground floor the
  Vigoroth movers (`PlayersHouse_1F_EventScript_Vigoroth1/2`) + a script are
  active while moving in; `navigate_to` toward the front door
  ((8,8)/(9,8) warps) **consistently times out at waypoint (8,4)** even with
  `avoid_scripted_events=False` and retries — so (8,4) is a persistent block,
  not a transient one. The downstairs→exit step must handle this (likely wait
  the movers/Mom scene out until the floor clears, or find the real walkable
  route). Player's-house 1F objects: Mom (2,6), Vigoroth (1,3)/(4,5).
- **NEXT (this chunk):** downstairs → clear the 1F Mom/movers scene → out the
  front door → rival's house → rival's mom → 2F Poké Ball → rival talk →
  outside. (Save-state checkpoints: truck/house1f/house2f/clockset in scratch.)

### §14.2 — Downstairs + rival's house (2026-07-20, chunk B milestone DONE)
The whole "moved-in → met the rival → back outside" sequence now runs. Facts:
- **The 1F "block" was the Petalburg-Gym TV scene, not the movers.** Coming
  down to 1F auto-fires `PlayersHouse_1F_EventScript_PetalburgGymReport*`,
  which *walks the player to the TV at (4,5)* and plays Mom's dialogue. RULE:
  when a script auto-moves the player, RIDE IT OUT (`_ride_out_scripted_scene`)
  — never `navigate_to` during it, or the moving avatar fights the pathfinder
  (that was the phantom "(8,4) block"). Wait for the script to ENGAGE first,
  then for control to return.
- **Player's-house front door:** navigate to the tile ABOVE the door (8,7),
  then step South through the warp (`_walk_through_warp`). A warp tile can't be
  a `navigate_to` destination for your own house, but CAN be walked onto to
  ENTER another building (see rival house below). Exit → Littleroot (0,9) ~(5,9).
- **Littleroot warps:** (5,8)→player house (1,0); **(14,8)→rival house (1,2)**;
  (7,16)→Birch's Lab (1,4).
- **Rival's (May's) house:** enter by `navigate_to((0,9),(14,8))` (walks onto
  the door → warps in). **Mom's greeting is AUTOMATIC on entry**
  (`MaysHouse_1F_EventScript_YoureNewNeighbor`) — no need to walk to her. 1F
  stairs up = (2,2). 2F: the **Poké Ball is the object at (5,4)**
  (`MaysHouse_2F_EventScript_RivalsPokeBall`); stand (5,5) facing North + A →
  `MeetMay`/`MeetMayNorth` (rival rushes in, introduces themselves). 2F
  stairs-down = (1,1). Exit: navigate to (2,7) then step South through the door.
- Both houses have ambient Vigoroth "movers" that can transiently block
  pathing; sticking to the left-side routes (x≈2) avoids them here.
- **CHUNK B COMPLETE.** NEXT CHUNK: Route 101 → Birch's bag → **choose a
  starter** → **first battle** (vs the wild Poochyena). Then the config pass
  (starter choice + nickname; name already in story.yml).

---

## §15 — Chapter 1: Route 101 → starter → first battle → Birch's lab (2026-07-20)

Verified order of operations (confirmed IN-GAME before coding) and built. A
fresh game now auto-plays all the way from the title screen to standing in
Professor Birch's lab with a starter, first battle won. `early_game.py`.

**Order of operations (verified):**
1. From outside the rival's house, walk **north**. At Littleroot (11,1) the
   `GoSaveBirch` coord-trigger fires (brief "you hear a scream" dialogue); the
   game then crosses to **Route 101 (0,16)**.
2. `Route101_EventScript_StartBirchRescue` fires and **AUTO-WALKS** the player
   up the route (to ~(11,15)) while Birch yells, then returns control.
3. Walk to **Birch's bag at (7,14)** (stand (8,14) facing West) and open it →
   `Task_HandleStarterChooseInput`.
4. Choose starter: Left=Treecko, none=Torchic, Right=Mudkip; mash A to confirm
   "Do you choose this?" → the **first battle** (starter vs the wild Pokémon).
5. Win the battle (bot's normal BattleListener; `StoryMode.on_battle_started`
   returns Fight). Birch thanks you and **warps you to his lab (1,4)**.

**Functions (each has a full INTENT / STORY CONDITION / GOAL / HOW-IT-WORKS
docstring in early_game.py):**
- `_go_north_to_birch_rescue()` — INTENT: reach Route 101 in the bag-ready
  state. GOTCHA: there is a false "free control" window at (11,19) right after
  crossing the border, BEFORE StartBirchRescue fires — do NOT stop there (you
  get boxed in). We wait until the `StartBirchRescue` script is actually on the
  stack, then ride the auto-walk out. Ends controllable at ~(11,15).
- `_choose_starter(species)` — INTENT: pick the configured starter. The bag
  cursor starts on the middle ball (Torchic); Left/Right pick the sides;
  mashing A confirms into the battle.
- `help_birch_and_choose_starter(starter)` — orchestrates 1–5. The battle is
  fought by the framework while this generator is paused; on resume it advances
  Birch's thanks with **B** (B also answers "No" to any incidental Yes/No such
  as a nickname prompt, matching the default of keeping the species name) until
  arriving in the lab. GOAL/END STATE: starter in party, wild Pokémon beaten,
  standing controllable in Birch's lab (1,4). Config: `starter` = random |
  treecko | torchic | mudkip (from `<profile>/story.yml`).

**Config added** (`modules/story/config.py`, `story.yml`): `starter` (default
random) and `starter_nickname` (default none | random | literal). Starter
selection is live; **nickname application is TODO** — verify whether/where the
game offers a starter-nickname prompt (this early sequence did not appear to),
otherwise it needs the Name Rater later. `on_battle_started` → Fight added to
StoryMode so story battles are always fought.

**Verified:** full fresh run with real battle listeners → 15,425 frames →
NICK/male, random Torchic Lv5, in Birch's lab (1,4). Random selection also
produced Mudkip and Treecko across runs. Checkpoint `birch_lab.ss1` saved.

**NEXT (remaining in the user's chunk):** finish Birch's lab conversation →
head north to **Oldale Town (0,10)** → **train the starter to a random Lv 8-10**
→ Route 103 → **rival battle**. Order still to verify in-game for the lab
dialogue (watch for a possible nickname/Pokédex prompt) and the rival trigger.

### §15.1 — Birch's lab conversation (2026-07-20)
`finish_birch_lab(nickname_mode)` — INTENT: close the give-starter scene so the
player can leave. STORY: starts in the lab (1,4) with the starter, running
`GiveStarterEvent`. HOW: Birch asks "give a nickname?" (a Std_MsgboxYesNo that
**B does NOT dismiss** — needs the Yes/No handler). Then advance the rest by
waiting for the `GiveStarterEvent` script to leave the stack while mashing **A**
(B doesn't advance these boxes; and the wait stops the instant the script ends,
BEFORE another A could re-open Birch's repeatable talk — A while facing him
re-triggers `EventScript_Birch` in a loop, the bug that first stalled this).
- **NICKNAME feature GATED OFF for now:** the Yes→naming path reaches the
  keyboard and types, but the typed name does NOT persist (post-naming confirm
  subtlety unsolved), and the user deprioritised nicknames. So we always answer
  No (keep species name). Config (`starter_nickname`) + `_resolve_nickname()` +
  a nickname pool remain for the future fix. **TODO: nickname persistence.**
- Verified from the `birch_lab` checkpoint: "none" → Torchic Lv5, controllable
  in the lab (6,5). Checkpoint `lab_done.ss1` saved.

### §15.2 — Shiny contingency for story battles (2026-07-20)
`StoryMode.on_battle_started()` always returns `BattleAction.Fight`. If the wild
in a story battle (notably the scripted first Birch battle) is shiny — very rare
— we log it and fight through WITHOUT catching or stopping. WHY this is safe:
the default "shiny → stop the bot" (and any auto-catch) lives in
`modules/encounter.handle_encounter()`, which `_listeners.py` only calls when
`on_battle_started` returns None (line 114-115). Returning Fight bypasses it; the
first battle is also an `EncounterType.Tutorial`, which the framework forces to
`CustomAction` (also never calls handle_encounter). Unit-tested: shiny/normal/
None encounters all return Fight and never raise.
