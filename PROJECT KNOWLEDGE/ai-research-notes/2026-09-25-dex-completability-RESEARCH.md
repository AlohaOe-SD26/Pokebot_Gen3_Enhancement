# CAN THE BOT COMPLETE THE POKÉDEX? — the number, and the traps

**Date:** 2026-09-25. **Why:** before building a dex hunter, find out whether *"complete the
Pokédex"* is even a well-posed goal for a bot on ONE cartridge with **no trading, no link cable, no
Mystery Gift / event distributions, no Colosseum/XD**.
**Status:** this is a NOTE (decomp research by a Claude agent, then adversarially reviewed).
✅ marks what **I verified myself in this repo or against the decomp**; ⚠ marks agent-reported.

---

## ⭐ THE BOTTOM LINE

> **On one Emerald cartridge with no trading and no events, the maximum achievable Hoenn dex is
> ~179 of 200. About 21 entries are permanently unreachable.**

⇒ **"Complete the Pokédex" must be redefined as "own every species obtainable on this cartridge".**
A goal of 200 is unachievable by construction and would make the bot chase entries forever. ‼ The
exact membership of the 21 is agent-reported and should be re-derived before any code depends on a
specific list — but the SHAPE of the answer (trade evolutions, the two starters you did not pick,
one of each fossil, event-only legendaries) is not in doubt.

---

## ⛔⛔ THE FINDING THAT CHANGES BOT BEHAVIOUR: **SIX BATTLES THE BOT MUST NEVER WIN**

⚠ Agent-reported, decomp-cited, and it is the single most actionable thing here:
`src/battle_main.c:5244` calls `SetRoamerInactive()` on **`B_OUTCOME_WON`** *or* `B_OUTCOME_CAUGHT`,
and `src/roamer.c:237` sets `active = FALSE` with no reachable path back (`CreateInitialRoamerMon`
runs once, from the `players_house.inc` cutscene; the second `special InitRoamer` in
`data/scripts/tv.inc` is, per the decomp's own comment, "a junk call" sealed inside one `lockall`).

⇒ **KO a one-shot legendary and its dex slot is gone for the run.** The list is the roaming
Latias/Latios **plus** Rayquaza, the three Regis, and Groudon/Kyogre — **six**, not five.

‼ **OUR BOT CURRENTLY FIGHTS TO WIN.** Nothing in the battle strategy knows that winning some
battles is a permanent loss. ⇒ a dex-completion run needs an explicit *never-KO* list, and it needs
it BEFORE it is ever pointed at a legendary. Filed as the first real hazard of `#24-dexhunt`.

---

## ⛔ A TRAP IN THE ENCOUNTER DATA — WE ARE HALF-SAFE, AND THE OTHER HALF IS A REAL GAP

⚠ `src/data/wild_encounters.json` also contains `gBattlePikeWildMonHeaders` and
`gBattlePyramidWildMonHeaders`. Anything that asks that FILE "is species X obtainable in the wild?"
gets **false positives** (Roselia / Medicham / Lunatone are Pyramid-only; Milotic / Breloom /
Dusclops Pike-only) and a **false negative for Feebas**, which is special-cased in
`src/wild_encounter.c` as `sWildFeebas` and is not in the file at all.

✅ **WE ARE SAFE ON THE FALSE POSITIVES.** `modules/map.py:1898` reads
`read_symbol("gWildMonHeaders")` — the map-table symbol only. The Frontier headers are separate
symbols and never enter our index. Verified by reading our own code.

⛔ **WE ARE *NOT* SAFE ON FEEBAS, AND IT IS A SILENT DROP.** `modules/encounter_index.py` is built
from those same map tables, and `modules/living_dex.py` states plainly that *"species with no wild
location … are excluded from the auto list and reported under `skipped`"*. ⇒ **Feebas has no entry
in `gWildMonHeaders`, so any hunt built on our index will skip it — and with it Milotic.**
‼ This is not hypothetical and it is not upstream's bug: it is ours to handle, with a special case
for Feebas's six tiles, exactly as the game does.

---

## ⭐ A CLOSURE PROOF WORTH KEEPING (⚠ agent-reported, cheap to re-derive)

Rather than enumerating every *giver* of a Pokémon, enumerate the only places the game sets the
OWNED flag — `grep -rn FLAG_SET_CAUGHT src/` gives six: catching
(`battle_script_commands.c`), hatching (`egg_hatch.c`), evolving (`evolution_scene.c`),
`ScriptGiveMon` (`script_pokemon_util.c`), trading (`trade.c`), and Mystery Event
(`mystery_event_script.c`, excluded by our no-events constraint).
⇒ **Nothing else in the game can register a species** — no Frontier prize, rental, Trainer Hill,
lottery, contest or minigame. That closes the question by construction instead of by exhaustion,
and it is the right shape of argument for this project.

---

## ⚠ MASS OUTBREAKS EXIST, AND THEY ARE USEFUL

The agent first said Emerald has no swarm system, then **retracted it**: the mechanic is called a
**mass outbreak**. `src/tv.c` holds `sPokeOutbreakSpeciesList[]` — **Seedot** (Routes 102/117/120),
**Nuzleaf** (Route 114), **Skitty** (Route 116) — delivered by a TV show and live for
`outbreakDaysLeft = 2`; `src/wild_encounter.c` tests for it BEFORE the normal table.
⇒ Those three are exactly three of the painful **1 %-slot** species, so an outbreak is by far the
cheapest way to get them. ‼ Worth teaching the hunter to notice, but **not** a blocker.
⛔ And the conclusion the retraction does NOT change: no outbreak can supply Surskit.

---

## WHAT THIS MEANS FOR THE BUILD

1. **Redefine the goal** to "every species obtainable on this cartridge" (~179), not 200.
2. **Build the never-KO list BEFORE any legendary hunt.** Six battles where winning is losing.
3. **Special-case Feebas** in `encounter_index`, or it is silently skipped forever.
4. Treat the specific membership of the 21 as UNVERIFIED until re-derived; the count is a planning
   figure, not a constant to hard-code.
