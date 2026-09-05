# §Ch24 — THE MOVESET PLAN: what to teach, what to sell, and which fight still loses

**Date:** 2026-09-04 · **Status:** ⚠ **AGENT NOTE — NOT TRUTH**, but an unusually well-sourced one:
TM compatibility was read from `src/data/pokemon/tmhm_learnsets.h` **at two revisions** (the macro form
and the post-`912a80e27a40` bitfield form) and diffed — identical for all six species — and
cross-checked against our own `modules/data/species.json`. ⛔ Verify before burning a single-use TM.

---

## ⭐ 0. THE HEADLINE

**Four move changes are FREE, already in the bag, and need no travel.** They are worth doing
immediately. Two more (Ice Beam, Dragon Claw) are free *pickups* that need a trip and turn **Drake
from a loss into a win**. And one fight — **Wallace** — is lost regardless, for a reason that is
arithmetic rather than opinion.

‼ **AND IT CORRECTED ME ON MY OWN CLAIM.** I had recorded Sceptile as carrying *"Rock Smash and
Strength — two dead slots"*. **`Slam` is 80 BP at 75% accuracy; `Strength` is 80 BP at 100%.** ⇒
Strength is Sceptile's *better* Normal move and **Slam is the wasted slot**. A "field move" is not
automatically a wasted slot — check the numbers before calling one dead.

---

## 1. THE TM/HM POCKET, RESOLVED

Read from `modules/data/moves.json`, cross-checked against `include/constants/tms_hms.h`
(the `FOREACH_TM` ordinal *is* the TM number — `src/party_menu.c:4688 ItemIdToBattleMoveId`).

| Item | move | type | pow | acc |
|---|---|---|---|---|
| TM03 | Water Pulse | Water | 60 | 100 |
| TM04 | **Calm Mind** | Psychic | — | — |
| TM08 | **Bulk Up** | Fighting | — | — |
| TM34 | Shock Wave | Electric | 60 | never misses |
| TM39 | Rock Tomb | Rock | 50 | 80 |
| TM40 | **Aerial Ace** | Flying | 60 | never misses |
| TM42 | **Facade** | Normal | 70 | 100 |
| TM47 | Steel Wing | Steel | 70 | 90 |
| TM50 | **Overheat** | Fire | 140 | 90 |
| HM02-08 | Fly / Surf / Strength / Rock Smash / Waterfall / Dive | | | |

## 2. COMPATIBILITY — decomp-verified, NOT guessed

| | TM03 | TM04 | TM08 | TM34 | TM39 | TM40 | TM42 | TM47 | TM50 |
|---|---|---|---|---|---|---|---|---|---|
| Sceptile | ✗ | ✗ | ✗ | ✗ | ✅ | ✅ | ✅ | ✗ | ✗ |
| Zigzagoon | ✅ | ✗ | ✗ | ✅ | ✗ | ✗ | ✅ | ✗ | ✗ |
| Swellow | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ | ✅ | ✅ | ✗ |
| Wailord | ✅ | ✗ | ✗ | ✗ | ✅ | ✗ | ✅ | ✗ | ✗ |
| Mightyena | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✅ | ✗ | ✗ |
| Castform | ✅ | ✗ | ✗ | ✅ | ✗ | ✗ | ✅ | ✗ | ✗ |

⛔ **THREE TMs ARE UNUSABLE BY THIS PARTY: TM04 Calm Mind, TM08 Bulk Up, TM50 Overheat.**

---

## 3. ✅ DO NOW — free, in the bag, zero travel

| # | change | why |
|---|---|---|
| A | **Sceptile: Aerial Ace (TM40) over SLAM** | Never-miss, and **four** opponents run Double Team (Shiftry L48, Sableye L50, Ludicolo L56, Glalie) plus Sand-Attack and Swagger. Also covers Sceptile's blind spot — Grass resists Grass, so Leaf Blade does only 30%/25% to Cacturne/Shiftry while Aerial Ace does 59%/47%. |
| B | **Swellow: Facade (TM42) over PECK** | Peck is **35 BP** — the worst move on the team. Facade is 70 with STAB. ⭐ And Wallace's Tentacruel *and* Milotic both carry **Toxic**: once poisoned, **Guts (×1.5) and Facade's doubling BOTH apply** → ~315 effective BP. |
| C | **Mightyena: Strength (HM04) over TACKLE** | 35 BP → 80 BP at 100%. **HMs are reusable**, so Sceptile keeps its copy. |
| D | **Zigzagoon: Rock Smash (HM06) over GROWL** | Victory Road needs Rock Smash AND Strength AND Surf AND Waterfall. If freeing Sceptile's slot later, the field-move coverage must not be lost. Growl is worthless. |

⭐ **AND A FREE ₽4,500:** TM04, TM08 and TM50 are unusable by anyone here and TMs sell at half price
(`src/item_menu.c:2070`; HMs are price 0 and cannot be sold). 3 × ₽1,500 → **₽6,241 total.**
⚠ The PC is empty (measured), so no boxed Pokémon could use them either.

## 4. ⭐⭐ THE TWO FREE PICKUPS THAT WIN DRAKE

**Wailord: ICE BEAM (TM13) over Dive** — *the single biggest change in this document.*
Flygon L53 **88%**, Salamence L55 **73%**, Altaria L54 **71%**, Shelgon L52 **71%**. **Flygon has
Levitate**, so Ice is the *only* super-effective type reachable on it. Drake carries **zero Ice
moves** and Wailord takes only 22-56% from his whole team.
📍 **TM13 IS FREE AND NEEDS NO DIVE** — traced through the warp tables, not folklore:
`item_ball_scripts.inc:433` in `AbandonedShip_Room_B1F`, door gated on `ITEM_STORAGE_KEY`
(`AbandonedShip_Corridors_B1F/scripts.inc:28-35`); the Storage Key is on the **top deck**
(`item_ball_scripts.inc:441`, `AbandonedShip_CaptainsOffice`). Dive leads to a *different* branch
entirely. Route: **Fly Slateport → R109 → Surf west to R108 → Deck → Captain's Office → Corridors 1F →
B1F.** ✅ Flag `ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM` measured **STILL THERE**.

**Sceptile: DRAGON CLAW (TM02) over Rock Smash** — Sceptile's **160 Speed outspeeds every Pokémon in
the League** (fastest is 132). Shelgon 86%, Flygon 52%, Kingdra 47%, Salamence 46%. Its Leaf Blade
does **7%** to Salamence.
📍 `item_ball_scripts.inc:397`, `MeteorFalls_B1F_2R`, needs Surf + Waterfall. Flag measured
**STILL THERE**.

## 5. ⛔ DO NOT

- ⛔ **Do not burn TM34 Shock Wave.** Only Castform (L36) and Zigzagoon (L19) can learn it, and
  Castform's Shock Wave does **21%** to Gyarados — the 4× target — while Gyarados's Surf does **106%**
  to Castform. ⭐ Consolation: **exactly one Pokémon in the entire League carries an Electric move**
  (Phoebe's 2nd Banette), so lacking Electric costs nothing defensively.
- ⛔ TM03 Water Pulse (Wailord already has Surf 95 and Water Spout 150) and TM39 Rock Tomb
  (20-31% everywhere at 80% accuracy).

---

## 6. ‼ THE HONEST VERDICT, FIGHT BY FIGHT

| fight | verdict |
|---|---|
| **Sidney** | ✅ WIN |
| **Phoebe** | ✅ WIN — the weakest offence in the League |
| **Glacia** | ✅ WIN, **but budget one dead Pokémon.** Her L52 Glalie carries **EXPLOSION** (250 BP, halves Defence in Gen 3) doing **235-468%** of *every* party member's max HP. We have no Ghost; it is an unavoidable 1-for-1 trade. |
| **Drake** | ⛔ **LOSS today. WIN with Ice Beam + Dragon Claw.** |
| **Wallace** | ⛔⛔ **LOSS, and no move change in this document fixes it.** |

### ⛔⛔ WHY WALLACE LOSES, AND IT IS ARITHMETIC
**Milotic L58: 196 HP, Recover = 98 HP/turn, Marvel Scale, a Sitrus Berry, and Wallace holds FOUR
Full Restores.** Our best single hit is Sceptile's Leaf Blade at **74**. Everything else: Swellow
Facade 38, Mightyena Take Down 34, Wailord Water Spout 27, Castform Shock Wave 16.
⇒ **74 < 98. It out-heals us.** Meanwhile Milotic's Ice Beam does 76% to Sceptile. Levelling does not
fix it — Sceptile at L60 still only reaches ~84.

### ⭐ WHAT WOULD FIX WALLACE — SolarBeam, and it is free
**TM22 SolarBeam + TM11 Sunny Day on Sceptile, both FREE pickups.** SolarBeam does **124** to Milotic
(63% — **beats Recover**), OHKOs Wallace's Wailord (101%) and Whiscash (199%), 90% on Walrein.
Sceptile outspeeds everything, so it sets sun turn 1 and then fires 1-turn SolarBeams.
📍 TM22: `item_ball_scripts.inc:465`, Safari Zone NW (₽500 entry). TM11: `item_ball_scripts.inc:461`,
Scorched Slab off Route 120 (Surf).

### ⭐ A FREE DEFENSIVE WIN
**Sheer Cold auto-fails against a Pokémon above the user's level** (`Cmd_tryKO`,
`battle_script_commands.c:7490`). Walrein is **L53**. ⇒ **one level-up makes Sceptile immune**, and
L54+ across the party removes the move entirely.

---

## 7. ⭐ WHERE THE USER'S CATCHING DIRECTIVE LANDS

This note independently reached the conclusion the 2026-09-04 catching directive enables:
**Zigzagoon L19 and Castform L36 contribute nothing.** Castform is OHKO'd by Milotic's Surf (136%),
Flygon's Earthquake (120%), Walrein's Surf (110%) and Salamence's Dragon Claw (114%), and **at 63
Speed it is outsped by everything except Phoebe's Dusclops — it never gets a turn.**
⚠ Its one real trick is genuine and verified (`Cmd_setweatherballtype` sets `TYPE_ICE` and
`dmgMultiplier = 2`; Forecast turns Castform Ice for STAB *and* hail immunity ⇒ ~100 BP Ice STAB,
62-71% on Drake's dragons) — **but it must survive a turn to set Hail, and against Drake it will not.**
⇒ **Two of six slots are dead weight, the PC is empty, and catching is now sanctioned.** See the
catch/Pokédex design work.

---

## 8. UNVERIFIED — read before acting

1. ⛔ **Our Atk / Def / SpA / SpD were NEVER MEASURED** — only HP and Speed. **Every damage number
   above is an IV-31 / EV-0 estimate, ±15%.** They calibrated within ~7% against measured HP/Speed,
   which is encouraging and is not proof.
2. **Intimidate is not applied in any number** — Sidney's Mightyena, Wallace's Gyarados and Drake's
   Salamence all have it. Subtract ~33% from physical moves on those turns.
3. **Reachability was read from decomp map warps, NOT walked.** ⛔ Per the project's own rule, confirm
   the Abandoned Ship and Meteor Falls routes with `calculate_path` from a real captured position
   **plus a control tile that does path**, before committing the bot to a trip.
4. Whether the Coin Case is held, New Mauville is cleared, and the Safari Zone bike area is open.
