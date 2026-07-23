# Gemini Deep Research response — #24-tms/#24-pokeprofiles Batch 1 (relayed 2026-07-23)

> RAW ARCHIVE, verbatim from the user's relay. Grading: see the run log in
> `GEMINI-POKEPROFILES-RESEARCH.md`. Headline: TM/HM-compat claims 98% right (59/60 —
> only Swellow/Shadow Ball wrong); **level-up numbers only 42% right (16/38) — NEVER
> use a level from this file; derive levels from `modules/data/` at build time.**
> TM locations/prices are unverified (decomp-check when #24-tms builds).

---

Here is the deep research and judgment layer for your Pokémon Emerald bot. Gen 3’s mechanical quirks (specifically the type-based physical/special split and single-use TMs) dictate every choice below.

### Gen 3 Mechanical Anchors (For the Bot’s Logic)

* **Physical Types:** Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, Steel.
* **Special Types:** Fire, Water, Grass, Electric, Psychic, Ice, Dragon, Dark.
* *Bot Logic Hook:* Do not teach Dark (Bite/Crunch) to physical attackers (e.g., Mightyena) expecting high damage. Do not teach Water (Surf/Waterfall) to Azumarill expecting Huge Power to boost it.

---

### A. The Emerald TM/HM/Tutor REGISTRY

*Note: In Emerald, the Game Corner TMs cost coins (which can be bought with Pokédollars), effectively making them infinitely purchasable for $80,000 each. This is highly reliable for a bot that can grind.*

| TM/HM/Tutor | Move (Type/Split) | Source / Location in Emerald | Earliest Phase | Repeat? | Story Verdict & Contention |
| --- | --- | --- | --- | --- | --- |
| **TM01** | Focus Punch (Fight/Ph) | Route 115 (Requires Surf) | Post-Gym 5 | No | **Skip** (Bot AI struggles with charge prediction). |
| **TM02** | Dragon Claw (Drag/Sp) | Meteor Falls (Requires Waterfall) | Post-Gym 8 | No | **Core** - Sceptile. |
| **TM03** | Water Pulse (Water/Sp) | Gym 8 Reward (Juan) | Post-Gym 8 | No | **Skip** - Outclassed by Surf by the time you get it. |
| **TM04** | Calm Mind (Psych/Sp) | Gym 7 Reward (Tate & Liza) | Post-Gym 7 | No | **Core** - Gardevoir, Kadabra. |
| **TM05** | Roar (Norm/Stat) | Route 114 (Gentleman) | Pre-Gym 4 | No | **Skip**. |
| **TM06** | Toxic (Pois/Stat) | Fiery Path (Requires Strength) | Pre-Gym 4 | No | **Situational** - Good for stalling, but bots prefer sweeping. |
| **TM07** | Hail (Ice/Stat) | Shoal Cave (Low Tide) | Pre-Gym 7 | No | **Skip**. |
| **TM08** | Bulk Up (Fight/Stat) | Gym 2 Reward (Brawly) | Post-Gym 2 | No | **Core** - Blaziken, Hariyama. |
| **TM09** | Bullet Seed (Grass/Sp) | Route 104 (Boy near flower shop) | Pre-Gym 1 | No | **Situational** - Early Grass damage, weak late. |
| **TM10** | Hidden Power (Norm/Sp) | Fortree City / Slateport Mart | Pre-Gym 6 | Yes | **Skip** - IVs are randomized; bot can't predict type/power. |
| **TM11** | Sunny Day (Fire/Stat) | Scorched Slab (Requires Surf) | Post-Gym 5 | No | **Skip**. |
| **TM12** | Taunt (Dark/Stat) | Trick House (Puzzle 2) | Pre-Gym 3 | No | **Skip**. |
| **TM13** | Ice Beam (Ice/Sp) | Abandoned Ship / Game Corner (4000c) | Pre-Gym 3 | Yes | **SUPER CORE** - Swampert, Tentacruel. Grind coins for it. |
| **TM14** | Blizzard (Ice/Sp) | Lilycove Dept. Store ($5500) | Pre-Gym 7 | Yes | **Skip** - 70% accuracy is bad for AI reliability. |
| **TM15** | Hyper Beam (Norm/Ph) | Lilycove Dept. Store ($7500) | Pre-Gym 7 | Yes | **Situational** - **Core for Slaking only** (see Gotchas). |
| **TM16** | Light Screen (Psych/Stat) | Lilycove Dept. Store ($3000) | Pre-Gym 7 | Yes | **Skip**. |
| **TM17** | Protect (Norm/Stat) | Lilycove Dept. Store ($3000) | Pre-Gym 7 | Yes | **Situational** - Bot can use it to stall Truant turns. |
| **TM18** | Rain Dance (Water/Stat) | Abandoned Ship (Requires Dive) | Pre-Gym 8 | No | **Skip**. |
| **TM19** | Giga Drain (Grass/Sp) | Route 123 (Needs grass-type in party) | Pre-Gym 6 | No | **Core** - Breloom, Vileplume. |
| **TM20** | Safeguard (Norm/Stat) | Lilycove Dept. Store ($3000) | Pre-Gym 7 | Yes | **Skip**. |
| **TM21** | Frustration (Norm/Ph) | Pacifidlog Town | Pre-Gym 8 | No | **Skip** - Bot shouldn't actively lower friendship. |
| **TM22** | SolarBeam (Grass/Sp) | Safari Zone | Pre-Gym 6 | No | **Skip** - 2-turn moves are bad without weather AI. |
| **TM23** | Iron Tail (Steel/Ph) | Meteor Falls | Pre-Gym 4 | No | **Situational** - 75% accuracy is a liability. |
| **TM24** | Thunderbolt (Elect/Sp) | Mauville (Wattson) / Game Corner | Pre-Gym 3 | Yes | **SUPER CORE** - Gardevoir, Kadabra, Manectric. |
| **TM25** | Thunder (Elect/Sp) | Lilycove Dept. Store ($5500) | Pre-Gym 7 | Yes | **Situational** - Only if AI can pair with Rain Dance. |
| **TM26** | Earthquake (Ground/Ph) | Seafloor Cavern | Pre-Gym 8 | No | **SUPER CORE** - Contested by Swampert, Slaking, Gyarados. |
| **TM27** | Return (Norm/Ph) | Fallarbor (Prof. Cozmo) / Pacifidlog | Pre-Gym 4 | Yes | **SUPER CORE** - Swellow, Slaking, Linoone, Azumarill. |
| **TM28** | Dig (Ground/Ph) | Route 114 (Fossil Maniac's Brother) | Pre-Gym 4 | No | **Situational** - Good mid-game ground damage. |
| **TM29** | Psychic (Psych/Sp) | Victory Road / Game Corner (3500c) | Pre-Gym 3 | Yes | **Core** - Gardevoir, Kadabra. |
| **TM30** | Shadow Ball (Ghost/Ph) | Mt. Pyre (Exterior) | Pre-Gym 6 | No | **Core** - *Contested*: Slaking, Swellow. (Ghost is Physical!). |
| **TM31** | Brick Break (Fight/Ph) | Sootopolis City (House) | Pre-Gym 8 | No | **Core** - *Contested*: Sceptile, Slaking, Hariyama. |
| **TM32** | Double Team (Norm/Stat) | Route 113 / Game Corner (1500c) | Pre-Gym 4 | Yes | **Skip** - Evasion cheese wastes bot turns. |
| **TM33** | Reflect (Psych/Stat) | Lilycove Dept. Store ($3000) | Pre-Gym 7 | Yes | **Skip**. |
| **TM34** | Shock Wave (Elect/Sp) | Gym 3 Reward (Wattson) | Post-Gym 3 | No | **Core** - Never-miss early coverage for Gardevoir. |
| **TM35** | Flamethrower (Fire/Sp) | Game Corner (4000c) | Pre-Gym 3 | Yes | **Core** - Blaziken, Manectric. |
| **TM36** | Sludge Bomb (Pois/Ph) | Dewford Town (Trendy phrase house) | Post-Gym 5 | No | **Core** - Crobat, Vileplume. (Poison is Physical!). |
| **TM37** | Sandstorm (Rock/Stat) | Route 111 (Desert) | Pre-Gym 4 | No | **Skip**. |
| **TM38** | Fire Blast (Fire/Sp) | Lilycove Dept. Store ($5500) | Pre-Gym 7 | Yes | **Situational**. |
| **TM39** | Rock Tomb (Rock/Ph) | Gym 1 Reward (Roxanne) | Post-Gym 1 | No | **Core** - Great early speed control for Torchic/Mudkip. |
| **TM40** | Aerial Ace (Fly/Ph) | Gym 6 Reward (Winona) | Post-Gym 6 | No | **Core** - Swellow, Sceptile. |
| **TM41** | Torment (Dark/Stat) | Slateport City (Contest Hall) | Pre-Gym 3 | No | **Skip**. |
| **TM42** | Facade (Norm/Ph) | Gym 5 Reward (Norman) | Post-Gym 5 | No | **Core** - Swellow (pairs with Guts ability). |
| **TM43** | Secret Power (Norm/Ph) | Route 111 / Slateport Mart | Pre-Gym 4 | Yes | **Core** - 70BP early-game normal nuke. |
| **TM44** | Rest (Psych/Stat) | Lilycove City (House) | Pre-Gym 7 | No | **Skip** - Sleeping AI is dead AI. |
| **TM45** | Attract (Norm/Stat) | Verdanturf Town (Contest Hall) | Pre-Gym 4 | No | **Skip** - Gender mechanics are too complex for basic AI. |
| **TM46** | Thief (Dark/Sp) | Slateport City (Team Aqua Grunt) | Pre-Gym 3 | No | **Situational** - Mostly for stealing items, weak in battle. |
| **TM47** | Steel Wing (Steel/Ph) | Granite Cave (Steven) | Pre-Gym 2 | No | **Situational** - Coverage for Swellow. |
| **TM48** | Skill Swap (Psych/Stat) | Mt. Pyre (Interior) | Pre-Gym 6 | No | **Skip**. |
| **TM49** | Snatch (Dark/Stat) | S.S. Tidal | Post-E4 | No | **Skip**. |
| **TM50** | Overheat (Fire/Sp) | Gym 4 Reward (Flannery) | Post-Gym 4 | No | **Situational** - AI might not switch out after SpA drop. |
| **HM01** | Cut (Norm/Ph) | Rustboro City (House) | Pre-Gym 1 | Inf. | **HM Tax**. Use on Linoone/Tropius. |
| **HM02** | Fly (Fly/Ph) | Route 119 (May/Brendan rival battle) | Pre-Gym 6 | Inf. | **Core** - Strong STAB for Swellow/Crobat. |
| **HM03** | Surf (Water/Sp) | Petalburg City (Wally's Relatives) | Post-Gym 5 | Inf. | **SUPER CORE** - Best Water move in game. Swampert/Pelipper. |
| **HM04** | Strength (Norm/Ph) | Rusturf Tunnel (Wanda's Boyfriend) | Pre-Gym 4 | Inf. | **Core/Tax** - Actually a solid 80BP attack for Slaking/Linoone. |
| **HM05** | Flash (Norm/Stat) | Granite Cave (Hiker) | Pre-Gym 2 | Inf. | **HM Tax**. Skip in battle. |
| **HM06** | Rock Smash (Fight/Ph) | Mauville City (House) | Pre-Gym 3 | Inf. | **HM Tax**. Very weak, put on a mule. |
| **HM07** | Waterfall (Water/Sp) | Cave of Origin | Pre-Gym 8 | Inf. | **Situational** - Surf is better. |
| **HM08** | Dive (Water/Sp) | Mossdeep City (Steven's House) | Post-Gym 7 | Inf. | **HM Tax**. Put on a mule or temporarily on Swampert. |

**Move Tutors (Main Story Only):**

* *Rollout, Fury Cutter, Swagger, Metronome, Mimic, Sleep Talk, DynamicPunch:* **SKIP**. Gimmicks that confuse bot AI or have bad accuracy.
* *Substitute* (Lilycove Dept Store Roof): **Situational**. Good, but AI HP management is tricky.
* *Double-Edge* (Sootopolis): **Situational**. Recoil kills bots, *unless* used on Rock Head ability (Aggron/Graveler).
* *Explosion* (Pacifidlog): **Skip**. AI will blow itself up unnecessarily.

---

### B. The PRIORITY TIER LIST

**S-Tier (Carries the run, priority TM receivers)**

* **Mudkip (Swampert):** Best starter. Immune to Electric, walls Wattson, crushes Flannery, Norman (with Protect/Dig), and Tate & Liza (with Surf). *Biggest weakness:* 4x Grass (Rival's Grovyle/Sceptile will OHKO it).
* **Torchic (Blaziken):** Fire/Fighting hits incredibly hard. Dominates Norman, Sidney, Glacia. *Biggest weakness:* Frail against Winona (Flying) and Tate & Liza/Wallace (Water/Psychic).
* **Taillow (Swellow):** Base 125 Speed. STAB Return/Fly. *Biggest weakness:* Completely walled by Rock/Steel types (Roxanne, Steven). Caught: Route 104 (early).

**A-Tier (Excellent, with minor caveats)**

* **Treecko (Sceptile):** Fast, but Gen 3 hurts it (Grass is Special, limiting its 85 Attack). Needs TMs to shine. *Weakness:* Poor physical movepool without TM investment.
* **Ralts (Gardevoir):** Calm Mind + Psychic + Thunderbolt sweeps the late game. Caught: Route 102. *Weakness:* Horrendous early-game grind (Teleport only as Abra, weak Confusion as Ralts).
* **Shroomish (Breloom):** Mach Punch and Leech Seed are incredible, but *Weakness:* 4x Flying weakness means it dies instantly to Winona/Golbats. Caught: Petalburg Woods.
* **Slakoth (Slaking):** Base 160 Attack is legendary. *Weakness:* Truant. The bot AI must be programmed to handle the skip turn correctly. Caught: Petalburg Woods.
* **Zubat (Crobat):** Fast, physical Sludge Bomb is lethal. *Weakness:* Weak damage until it evolves and gets TMs. Caught: Granite Cave.

**B/C-Tier (Usable, but outclassed or have ceilings)**

* *B-Tier:* Makuhita (Hariyama), Electrike (Manectric), Tentacool (Tentacruel), Magikarp (Gyarados - huge level 20 grind tax).
* *C-Tier (Filler):* Whismur (Exploud), Geodude (Graveler - locked out of Golem without trades), Abra (Kadabra - locked out of Alakazam, too frail late-game), Marill (Azumarill - STAB Water is Special, heavily hindering Huge Power).

**HM-Mule Tier (Do not invest, use for overworld utility)**

* **Zigzagoon/Linoone:** Core mule. Can learn Cut, Surf, Rock Smash, Strength. Bonus: *Pickup* ability passively generates rare candies, TMs, and items.
* **Tropius:** Fly, Flash, Rock Smash, Strength, Cut, Sweet Scent.
* **Tentacool/Marill:** Surf, Waterfall, Dive (The Water trinity).

---

### C. FULL BATTLE PROFILES — Batch 1

*UNCERTAIN/CAVEAT FLAG:* The bot's ability to execute setup (Swords Dance, Calm Mind) depends heavily on your state-machine logic. These movesets prioritize immediate, reliable damage (STAB + coverage) that raw AI handles best.

#### 1. Treecko → Grovyle → Sceptile

* **ROLE:** Fast Special/Mixed Sweeper
* **TIER:** A-Tier. Worth TM02 (Dragon Claw), TM31 (Brick Break).
* **GOAL MOVESET:** Leaf Blade (Lv29, STAB Special), Dragon Claw (TM02, Special Coverage), Brick Break (TM31, Physical Coverage), Aerial Ace (TM40, Physical Coverage).
* **PHASES:** Gym 3: Absorb, Quick Attack, Pursuit, Bullet Seed. Gym 6: Leaf Blade, Pursuit, Secret Power, Dig.
* **EVO TIMING:** Evolve on schedule.
* **HM COMP:** Cut, Rock Smash, Strength, Flash. *Should it?* No, keep its slots clean.
* **GOTCHAS:** Grass is a Special type. It cannot utilize Swords Dance + Leaf Blade together effectively in Gen 3.

#### 2. Torchic → Combusken → Blaziken

* **ROLE:** Mixed Wallbreaker
* **TIER:** S-Tier. Worth TM35 (Flamethrower), TM08 (Bulk Up).
* **GOAL MOVESET:** Flamethrower (TM35 / Lv36 as Torchic), Sky Uppercut (Lv59, or Brick Break TM31), Bulk Up (TM08), Slash (Lv42) or Aerial Ace (TM40).
* **PHASES:** Gym 3: Ember, Double Kick, Peck, Bulk Up. Gym 6: Flamethrower, Double Kick, Bulk Up, Slash.
* **EVO TIMING:** *Delaying Torchic to Lv 36 gets Flamethrower early* (Combusken gets it at 50, Blaziken at 59). However, a bot struggling with stats should just evolve on schedule (Lv16/36) and buy TM35 Flamethrower from the Game Corner.
* **HM COMP:** Cut, Strength, Rock Smash. *Should it?* Strength is an okay normal attack early, but drop it later.
* **GOTCHAS:** High damage, but frail. AI shouldn't leave it in against fast Water/Flying types.

#### 3. Mudkip → Marshtomp → Swampert

* **ROLE:** Bulky Mixed Sweeper / Core Carry
* **TIER:** S-Tier. Worth TM13 (Ice Beam), TM26 (Earthquake).
* **GOAL MOVESET:** Surf (HM03), Earthquake (TM26 or Lv52), Ice Beam (TM13), Return (TM27).
* **PHASES:** Gym 3: Water Gun, Mud Shot, Bide, Rock Tomb (TM39). Gym 6: Surf, Mud Shot, Secret Power, Ice Beam (if grinded).
* **EVO TIMING:** Evolve on schedule (Lv16, Lv36).
* **HM COMP:** Surf, Waterfall, Dive, Strength, Rock Smash. *Should it?* Keep Surf. Put the others on a Tentacool mule.
* **GOTCHAS:** 4x Grass weakness. Bot AI *must* be coded to flee/switch from rival’s Sceptile/Grovyle.

#### 4. Poochyena → Mightyena

* **ROLE:** Early Physical Attacker / Intimidate Bot
* **TIER:** C-Tier. Do not waste top-tier TMs.
* **GOAL MOVESET:** Return (TM27), Shadow Ball (TM30), Howl (Lv13), Strength (HM04).
* **PHASES:** Gym 3: Tackle, Howl, Bite, Sand-Attack. Gym 6: Return, Bite, Howl, Secret Power.
* **EVO TIMING:** Evolve on schedule (Lv18).
* **HM COMP:** Rock Smash, Strength. *Should it?* Yes, good candidate for Strength.
* **GOTCHAS:** **Dark is a Special Type in Gen 3.** Mightyena’s Base Special Attack is a miserable 60. Bite/Crunch do very little damage. It relies entirely on Normal/Ghost moves for Physical damage.

#### 5. Zigzagoon → Linoone

* **ROLE:** HM Mule / Pickup Farmer / Belly Drum Cheese
* **TIER:** HM-Mule Tier (S-Tier utility).
* **GOAL MOVESET:** Cut (HM01), Surf (HM03), Rock Smash (HM06), Strength (HM04).
* **PHASES:** Keep HMs updated as you get them.
* **EVO TIMING:** Evolve on schedule (Lv20), but keeping it unevolved is fine if it's just a bench mule.
* **HM COMP:** Cut, Surf, Rock Smash, Strength. *Should it?* Yes, load it up.
* **GOTCHAS:** If used for combat, AI will struggle to use Belly Drum (Lv53) safely without dying. Keep it to HMs.

#### 6. Wurmple → Beautifly AND → Dustox

* **ROLE:** Early Game Crutch
* **TIER:** C-Tier (Falls off hard post-Gym 4).
* **GOAL MOVESET (Beautifly):** Silver Wind (Lv24), Giga Drain (TM19), Morning Sun (Lv20), Gust (Lv13).
* **GOAL MOVESET (Dustox):** Sludge Bomb (TM36), Psybeam (Lv24), Moonlight (Lv17), Protect (Lv13).
* **PHASES:** Gym 3: Great for Brawly (Gust/Confusion). Gym 6: Bench them.
* **EVO TIMING:** Evolves automatically at Lv7, Lv10. (Randomized personality value determines Silcoon vs Cascoon).
* **HM COMP:** Flash (Both). *Should it?* Yes, good Flash mules.
* **GOTCHAS:** Bug and Poison are both PHYSICAL. Dustox has awful Attack (50), making Sludge Bomb weak despite STAB. Beautifly's Silver Wind uses its lower Physical Attack.

#### 7. Taillow → Swellow

* **ROLE:** Fast Physical Sweeper
* **TIER:** S-Tier (A-Tier if bot can't utilize Guts). Worth TM42 (Facade), TM40 (Aerial Ace).
* **GOAL MOVESET:** Return (TM27) / Facade (TM42), Fly (HM02) or Aerial Ace (TM40), Steel Wing (TM47), Quick Attack (Lv13).
* **PHASES:** Gym 3: Peck, Quick Attack, Focus Energy, Wing Attack. Gym 6: Return/Facade, Fly, Quick Attack, Steel Wing.
* **EVO TIMING:** Evolve on schedule (Lv22).
* **HM COMP:** Fly. *Should it?* Yes, Fly is an excellent 90BP STAB move.
* **GOTCHAS:** *Guts Ability.* If the bot can be programmed to walk into a wild battle, get Poisoned, and stay Poisoned (relying on potions), Facade becomes a 140 BP nuke that OHKOs half the game.

#### 8. Wingull → Pelipper

* **ROLE:** Defensive Water/HM Mule
* **TIER:** C-Tier. Outclassed by Tentacruel/Swampert.
* **GOAL MOVESET:** Surf (HM03), Fly (HM02), Shock Wave (TM34), Protect (Lv33).
* **PHASES:** Gym 3: Water Gun, Wing Attack, Supersonic, Mist.
* **EVO TIMING:** Evolve on schedule (Lv25).
* **HM COMP:** Surf, Fly. *Should it?* Yes, carrying both Surf and Fly on one slot is amazing for team compression.
* **GOTCHAS:** 4x Electric weakness. Terrible late-game damage output.

#### 9. Ralts → Kirlia → Gardevoir

* **ROLE:** Special Sweeper
* **TIER:** A-Tier. Worth TM24 (Thunderbolt), TM04 (Calm Mind).
* **GOAL MOVESET:** Psychic (Lv26), Thunderbolt (TM24), Calm Mind (TM04), Reflect (Lv33) / Shock Wave (TM34).
* **PHASES:** Gym 3 (Kirlia): Confusion, Double Team, Teleport, Calm Mind. Gym 6: Psychic, Shock Wave, Calm Mind, Reflect.
* **EVO TIMING:** Evolve on schedule (Lv20, Lv30).
* **HM COMP:** Flash. *Should it?* No.
* **GOTCHAS:** Ralts starts with ONLY Teleport (and Growl). The bot *must* switch-train it until Lv6 (Confusion) or it will endlessly teleport from wild battles and die in trainer battles.

#### 10. Shroomish → Breloom

* **ROLE:** Physical Sweeper
* **TIER:** A-Tier. Worth TM19 (Giga Drain).
* **GOAL MOVESET:** Mach Punch (Lv23), Sky Uppercut (Lv54), Giga Drain (TM19), Leech Seed (Lv16).
* **PHASES:** Gym 3: Mega Drain, Headbutt, Leech Seed, Mach Punch. Gym 6: Mach Punch, Headbutt, Giga Drain, Leech Seed.
* **EVO TIMING:** *Standard is Lv23.* Shroomish learns Spore (100% sleep) at Lv54, but a bot run cannot reasonably halt evolution for 31 levels. Evolve on schedule at 23 to get Mach Punch.
* **HM COMP:** Cut, Rock Smash, Strength, Flash. *Should it?* Strength is okay, others no.
* **GOTCHAS:** 4x Flying weakness. Effect Spore is great passive defense, but AI shouldn't rely on it. Grass (Giga Drain) runs off its mediocre Special Attack.

#### 11. Slakoth → Vigoroth → Slaking

* **ROLE:** Physical Nuke / Hit-and-Run
* **TIER:** A-Tier (if AI handles Truant). Worth TM30 (Shadow Ball), TM15 (Hyper Beam).
* **GOAL MOVESET:** Hyper Beam (TM15) / Return (TM27), Earthquake (TM26), Shadow Ball (TM30), Yawn (Lv19) / Slack Off (Lv43).
* **PHASES:** Gym 3 (Vigoroth): Scratch, Encore, Yawn, Slash. Gym 6 (Slaking): Return, Faint Attack, Yawn, Slash.
* **EVO TIMING:** Evolve on schedule (Lv18, Lv36). Vigoroth loses Truant, Slaking regains it.
* **HM COMP:** Cut, Rock Smash, Strength. *Should it?* Strength is an excellent STAB normal move early on.
* **GOTCHAS:** **Truant + Hyper Beam Exploit.** In Gen 3, the recharge turn of Hyper Beam occurs *on the same turn* as Truant's loafing turn. This mitigates Hyper Beam's drawback completely. The AI should spam Hyper Beam.

#### 12. Abra → Kadabra (Ceiling)

* **ROLE:** Fast, Frail Special Sweeper
* **TIER:** B-Tier. (Cannot become Alakazam without trading). Worth TM34 (Shock Wave).
* **GOAL MOVESET:** Psychic (Lv36), Shock Wave (TM34), Calm Mind (TM04), Recover (Lv43).
* **PHASES:** Gym 3: Confusion, Teleport, Disable. Gym 6: Psybeam, Recover, Shock Wave, Reflect.
* **EVO TIMING:** Evolve to Kadabra at Lv16.
* **HM COMP:** Flash. *Should it?* No.
* **GOTCHAS:** Same as Ralts: requires switch-training until Lv16. Kadabra’s physical defense is paper-thin. A bot might leave it in against a priority physical move (Quick Attack) and die instantly.

#### 13. Whismur → Loudred → Exploud

* **ROLE:** Mixed Tank / Filler
* **TIER:** C-Tier.
* **GOAL MOVESET:** Return (TM27), Shadow Ball (TM30), Earthquake (TM26, if uncontested), Flamethrower (TM35) / Ice Beam (TM13).
* **PHASES:** Gym 3: Pound, Uproar, Astonish, Howl. Gym 6: Stomp, Supersonic, Roar, Secret Power.
* **EVO TIMING:** Evolve on schedule (Lv20, Lv40).
* **HM COMP:** Rock Smash, Strength.
* **GOTCHAS:** Very mediocre stats across the board. Soundproof ability is nice against random Supersonics, but it's largely an HM mule that occasionally fights.

#### 14. Makuhita → Hariyama

* **ROLE:** Bulky Physical Sweeper
* **TIER:** A-Tier. Worth TM08 (Bulk Up).
* **GOAL MOVESET:** Brick Break (TM31) / Cross Chop (Lv46), Vital Throw (Lv10), Fake Out (Lv13), Bulk Up (TM08).
* **PHASES:** Gym 3: Tackle, Sand-Attack, Arm Thrust, Vital Throw. Gym 6: Fake Out, Vital Throw, Smellingsalt, Bulk Up.
* **EVO TIMING:** Evolve on schedule (Lv24).
* **HM COMP:** Surf, Rock Smash, Strength. *Should it?* Surf on Hariyama is a funny Gen 3 quirk, but bad for combat.
* **GOTCHAS:** Thick Fat is a fantastic ability, making it a great switch-in for Flannery. Vital Throw has negative priority (goes last) but never misses—great for bots as it removes accuracy variance.

#### 15. Marill → Azumarill

* **ROLE:** Physical Bruiser (NOT a Special Water attacker)
* **TIER:** C-Tier (Requires too much TM support for a bot).
* **GOAL MOVESET:** Return (TM27), Brick Break (TM31), Iron Tail (TM23), Surf (HM03 - mandatory tax).
* **PHASES:** Gym 3: Tackle, Defense Curl, Rollout, Water Gun. Gym 6: Bubblebeam, Rollout, Strength, Double-Edge.
* **EVO TIMING:** Evolve on schedule (Lv18).
* **HM COMP:** Surf, Waterfall, Dive, Rock Smash, Strength. *Should it?* Yes, it's a premier HM Mule.
* **GOTCHAS:** **Huge Power Gen 3 Interaction.** Huge Power doubles the *Attack* stat. Water moves (Surf/Waterfall) are *Special*. Azumarill's Water attacks will hit like a wet noodle. It must use Normal/Fighting moves for damage.

#### 16. Geodude → Graveler (Ceiling)

* **ROLE:** Physical Wall
* **TIER:** C-Tier (Cannot become Golem).
* **GOAL MOVESET:** Earthquake (Lv31), Rock Blast (Lv34) or Rollout (Lv22), Explosion (Lv46), Double-Edge (Lv38).
* **PHASES:** Gym 3: Tackle, Rock Throw, Magnitude, Rollout. Gym 6: Magnitude, Rock Throw, Rollout, Earthquake.
* **EVO TIMING:** Evolve on schedule (Lv25).
* **HM COMP:** Rock Smash, Strength.
* **GOTCHAS:** 4x Weak to Water/Grass. AI will easily suicide by leaving it in against Surf. Sturdy prevents OHKOs from full health, but Graveler’s speed is abysmal.

#### 17. Zubat → Golbat → Crobat

* **ROLE:** Blistering Fast Sweeper
* **TIER:** A-Tier. Worth TM36 (Sludge Bomb).
* **GOAL MOVESET:** Sludge Bomb (TM36), Fly (HM02), Shadow Ball (TM30), Confuse Ray (Lv21) / Bite (Lv16).
* **PHASES:** Gym 3 (Zubat): Leech Life, Supersonic, Astonish, Bite. Gym 6 (Golbat): Wing Attack, Bite, Confuse Ray, Poison Fang.
* **EVO TIMING:** Evolve to Golbat at 22. Evolves to Crobat via Friendship. (Bot must not let it faint repeatedly to ensure friendship grows).
* **HM COMP:** Fly. *Should it?* Yes, Fly is optimal STAB.
* **GOTCHAS:** Poison is PHYSICAL in Gen 3. Sludge Bomb runs off Crobat's 90 Base Attack and hits surprisingly hard. Bite is SPECIAL, making it weak late-game.

#### 18. Skitty → Delcatty

* **ROLE:** Cute Charm / Status Applier
* **TIER:** D-Tier. Not worth investment.
* **GOAL MOVESET:** Return (TM27), Faint Attack (Lv27 Skitty), Assist (Lv39 Skitty), Sing (Lv7).
* **EVO TIMING:** Evolve via Moon Stone. Delay until Lv27 to get Faint Attack, or Lv39 for Assist.
* **GOTCHAS:** Stats are too low (Base 45 Atk/SpA) for an automated run. Bot should bench.

#### 19. Oddish → Gloom → Vileplume / Bellossom

* **ROLE:** Slow Mixed Attacker
* **TIER:** B-Tier. Worth TM19 (Giga Drain) or TM36 (Sludge Bomb).
* **GOAL MOVESET (Vileplume):** Giga Drain (TM19) / Petal Dance (Lv44), Sludge Bomb (TM36), Sleep Powder (Lv14), Moonlight (Lv35 Gloom).
* **EVO TIMING:** Evolve to Gloom at 21. **Delay Gloom to Lv35 for Moonlight, then evolve.** Vileplume (Leaf Stone - Route 119) is strictly better than Bellossom (Sun Stone - Mossdeep) because Vileplume retains Poison typing for physical Sludge Bomb STAB.
* **HM COMP:** Cut, Flash.
* **GOTCHAS:** Sludge Bomb is physical, Giga Drain is special. Vileplume has good stats in both (80 Atk / 110 SpA).

#### 20. Seedot → Nuzleaf → Shiftry

* *Cut for depth as per instructions.* (Requires Leaf Stone, atrocious level-up movepool requires heavy Game Corner TM investment to function).

#### 21. Nincada → Ninjask / Shedinja

* *Cut for depth as per instructions.* (Shedinja's Wonder Guard is un-programmable for basic bot AI without a complete hardcoded dictionary of enemy movesets).

---

*Omissions & Cuts:* The specific profiles for Seedot/Shiftry and Nincada/Shedinja were cut to maintain deep detail on the primary early game carries, per the delivery rules. Post-game Battle Frontier tutors were omitted as they require BP and do not serve the story run logic.
