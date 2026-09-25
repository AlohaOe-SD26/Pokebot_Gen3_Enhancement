# MEASURED — `#24-marthreachable`: THE LEAGUE MART **IS** REACHABLE, AND H7 IS REFUTED

**2026-09-25.** Instrument: `tools/story-dev/probe_mart_reachable.py` (NEW, **OBSERVE-ONLY** — no
button pressed, no step taken, nothing bought). Evidence:
`tools/story-dev/evidence/2026-09-25-marthreachable.stdout.txt`.

⚠ **NOT A GRADED DRIVE, AND NO PREDICTIONS WERE PRE-REGISTERED.** This is a fact-finding probe with
no acceptance verdict to game, so `.claude/skills/story-drive` §1 does not bite. Said out loud so
nobody later reads it as a leg that skipped the ritual.

---

## ⛔⛔ THE HEADLINE: A RECORDED BLOCKER WAS A WRONG COORDINATE, NOT A MAP LIMITATION

`#24-restockleg` (authorised by **USER RULING 12** — a lost run restocks and retries) was blocked on
build-spec hazard **H7**, recorded as: *"the Mart REFUSES (`PathFindingError`)… the clerk appears
not to be spawned in that fixture."*

**Both halves are refuted.**

| claim | measured |
|---|---|
| "the clerk is not spawned" | ⛔ **REFUTED.** The lobby map has **4 ROM-defined objects**, one at **`(16,2)`** |
| "the Mart REFUSES" | ⛔ **REFUTED — of the right tile.** `(16,3)` refuses because it is **the counter (a WALL)**. **`(16,4)` routes in 13 waypoints.** |

⇒ **THE LEAGUE MART IS REACHABLE.** `#24-marthreachable` is answered; `#24-restockleg` is unblocked
on this axis.

---

## ⭐ WHY THE ORIGINAL MEASUREMENT WENT WRONG — THE GENERALISABLE PART

A Gen-3 shop/centre NPC **stands behind a solid counter and is talked to ACROSS it.** The probe
measured this on the very same map, from the object the tree already trusts:

```
object @ (3, 2)  [NURSE]   adjacent: (3,3)=WALL (3,1)=WALL (4,2)=WALL (2,2)=WALL
                           counter-distance 2: (3,4)=0wp   <- and (3,4) IS `LEAGUE_NURSE_STAND`
object @ (16,2)  [CLERK]   adjacent: (16,3)=WALL (16,1)=WALL (17,2)/(15,2)=REFUSED
                           counter-distance 2: (16,4)=13wp  <- THE STAND TILE
```

**The nurse — which works — has ALL FOUR neighbours WALL.** So "adjacent" was never the right model
for a counter NPC on this map, and the evidence that it wasn't was sitting three tiles away the
whole time.

⇒ **PREVENTION RULE: when a reachability check refuses, test the MODEL before believing the
result.** A single hardcoded "approach tile" can only tell you whether *that guess* routes; it
cannot distinguish *"unreachable"* from *"you guessed the wrong tile"*. The probe now sweeps every
ROM-defined object at **both** adjacency and counter distance, so the reading is *"reachable from
X"* or *"reachable from nowhere"* — which are different findings.
‼ **And the camera-window trap was live here too:** `get_map_objects()` showed only 4 live objects
and **none near `(16,2)`**, because it is ~13 tiles away — outside the ~7-9 tile window. Concluding
"not spawned" from that list is exactly the documented misread. The probe prints **ROM templates
beside live objects** and refuses to conclude absence from the live list alone.

---

## ✅ AND THE SHOP IS REAL — CONFIRMED IN THE DECOMP, NOT INFERRED

`data/maps/EverGrandeCity_PokemonLeague_1F/scripts.inc`:

```
EverGrandeCity_PokemonLeague_1F_EventScript_Clerk::
	pokemart EverGrandeCity_PokemonLeague_1F_Pokemart

EverGrandeCity_PokemonLeague_1F_Pokemart:
	.2byte ITEM_ULTRA_BALL
	.2byte ITEM_HYPER_POTION
	.2byte ITEM_MAX_POTION
	.2byte ITEM_FULL_RESTORE
	.2byte ITEM_FULL_HEAL
	.2byte ITEM_REVIVE
	.2byte ITEM_MAX_REPEL
	pokemartlistend
```

### ⭐ WHAT THIS DECIDES FOR `#24-restockleg`

* ✅ **REVIVES ARE BUYABLE** — the item the gauntlet actually runs out of (USER RULING 2 prices the
  basket at 3 Revives, and the `glacia`→DRAKE leg spent one reviving Mightyena).
* ✅ Full Restore / Max Potion / Hyper Potion / Full Heal are all buyable ⇒ a restock leg can
  rebuild the healing basket entirely at the League itself, **without leaving Ever Grande.**
* ⛔⛔ **THERE IS NO ETHER, NO ELIXIR, NO LEPPA BERRY.** This **CONFIRMS BY MEASUREMENT** the PP
  objection (`#24-leg2spec` O3): **PP cannot be restored anywhere in the League — not even at its
  own shop.** ⇒ a restock leg fixes HP, status and faints, and **cannot fix PP**. Against ~25
  opposing Pokémon on one PP bar, that remains the unsolved half of the gauntlet economy.

---

## ⛔ WHAT THIS PROBE DOES **NOT** SETTLE

* **Whether the bot can AFFORD it.** The basket is ₽54,300 against a measured ₽1,741 wallet, and a
  whiteout **halves** what remains. Reachability does not touch the money problem, and wilds were
  measured to pay **₽0 over 1,056 battles** — so "grind for money" is already refuted.
* **Whether the buy MENU can be driven.** Routing to `(16,4)` is not a transaction. `#24-restockleg`
  needs a menu driver, and none exists.
* **The post-whiteout run.** The probe also read `post_ch24_atdoor_L75.ss1` (`EVER_GRANDE_CITY
  (18,6)` — **the respawn tile**): control passes, but no landmarks are recorded for that map yet,
  so the walk-in route from the respawn point to `(16,4)` is **not yet measured end to end**.
* **Whether `(16,4)` is where the bot should STAND to talk.** It is the reachable tile at counter
  distance and it mirrors the nurse exactly — but the TALK itself has not been driven.
