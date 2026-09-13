# Norman / Slaking — decomp ground truth, and why the lead-policy fix was REFUTED (2026-09-13)

⚠ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). Claude-agent output against pret/pokeemerald,
cross-checked by a second agent and spot-verified by me. Stat lines are the author's CALCULATIONS.

⛔ **AND THE ITEM IT WAS COMMISSIONED FOR WAS REFUTED THE SAME DAY.** Keep it for the MECHANICS; do
not use it to re-open `#24-leadpolicy`. See "THE REFUTATION" at the bottom.

---

## ⛔ SHEDINJA IS STRUCTURALLY SUICIDAL AGAINST NORMAN — four independent mechanisms

Norman's party is `ITEM_CUSTOM_MOVES` (`trainer_parties.h:3477-3506`), so the movesets are **literal
and deterministic**, not a learnset walk:

| slot | mon | lvl | moves |
|---|---|---|---|
| 0 | Spinda | 27 | Teeter Dance, Psybeam, Facade, Encore |
| 1 | Vigoroth | 27 | Slash, Facade, Encore, **Faint Attack** |
| 2 | Linoone | 29 | Slash, Belly Drum, Facade, Headbutt |
| 3 | **Slaking** | 31 | **Counter**, Yawn, Facade, **Faint Attack** — holds **Sitrus Berry** |

1. **Faint Attack is Dark → 2× on Ghost** (`battle_main.c:436`) and has **`.accuracy = 0` /
   `EFFECT_ALWAYS_HIT`** (`battle_moves.h:2408`) ⇒ it passes Wonder Guard, **cannot miss**, and
   Shedinja has 1 HP. **Two of the four carry it.**
2. **Slaking outspeeds it** (Spe ~68 vs base 40) and **Truant never loafs on arrival**
   (`battle_script_commands.c:5256-5263` — the `switchineffects` hack sets the counter so the next
   real turn attacks) ⇒ Shedinja dies before acting.
3. **Spinda's Teeter Dance bypasses Wonder Guard entirely** — confusion self-damage runs
   `BattleScript_DoSelfConfusionDmg`, whose only damage opcode is `adjustnormaldamage2`: **no
   `typecalc`, no Wonder Guard check** (`battle_util.c:2159`, `battle_scripts_1.s:3801-3810`).
4. ⭐ **THE AI IS EXPLICITLY CODED TO HUNT IT.** `ShouldSwitchIfWonderGuard()`
   (`battle_ai_switch_items.c:35-117`) runs **unconditionally for every trainer** — there is no
   aiFlags gate — and on finding a party member with a super-effective move switches it in at
   `Random() % 3 < 2`, i.e. **2/3 per turn**. ⇒ Linoone (all-Normal, literally cannot touch
   Shedinja) does not get walled; it gets swapped out for a Faint Attack user.

⇒ Shedinja is safe against exactly one of the four, and the AI switches that one out.

## ⭐ WHY MACHOKE IS THE WORST LEAD (18%) — Counter, and Gen-3 physical/special split
`Cmd_counterdamagecalculator` (`battle_script_commands.c:7943`) returns
`gProtectStructs[attacker].physicalDmg * 2`, and **`Cmd_typecalc2` never modifies
`gBattleMoveDamage`** — it only sets result flags. ⇒ **Counter returns the full 2× even against a
Fighting type.** In Gen 3 category is by TYPE (`battle.h:466-467`), so every Machoke move is
physical. **The harder it hits, the harder Counter kills it back.**
⇒ **Special attackers are structurally immune to Counter** (it reads `physicalDmg` only) AND hit
Slaking's weaker side (SpD ~59 vs Def ~76). That is the mechanism behind the measured ordering
**Combusken 44% > Marshtomp 33% > Machoke 18%**.

## Other mechanics worth keeping
* **Truant is a flip-flop** (`battle_util.c:2072-2083` check, `:2639-2640` toggle) and the AI has
  **no model of it** — you get two turns per one, forever. ⛔ But switching your own mon does NOT
  bank a loaf: `SwitchInClearSetData` resets the counter.
* ⛔ **Do not chip.** Two **Hyper Potions heal a flat 200** (more than Slaking's whole bar) and fire
  below **25%** HP (`battle_ai_switch_items.c:864-872`); Sitrus adds 30 at ≤50%. **KO from above 25%.**
* ⛔ **Never poison/burn/paralyse Slaking for the speed** — **Facade doubles to 140 BP when *Slaking*
  is statused** (`battle_scripts_1.s:2252-2258`), off 160 base Attack.
* **Norman's badge is exactly the one that enables Surf**, and **HM03 is given only after the win**
  (`party_menu.c:117-135`; `PetalburgCity_Gym/scripts.inc:435`) ⇒ Surf is unobtainable before him.
* Two symbols an earlier agent invented do **not exist** in pokeemerald: `truantSwitchInRandomNumber`
  and `GetAIAbility`. ⛔ Do not build on either.

---

## ⛔ THE REFUTATION — read this before acting on any of the above

Everything above is mechanically sound and still does **not** justify changing the lead policy:

* **The "Shedinja 40% at Norman" figure that motivated this was an ARTIFACT.** It pooled Norman with
  the three gym trainers fought in the same map. Split by opponent: of 119 "Petalburg wins" only
  **27 are Norman**; Shedinja is **26W/5L vs the trainers** and **13W/79L (14%) vs Norman**.
* **Norman is the LEAST blocking boss measured** — **27 of 29 runs beat him**; conversion past the
  site is 97%.
* **The ceiling on a perfect lead fix is +12.8 wins = 1.7% of all losses and ZERO extra runs past
  badge 5.**
* **Option (a) is measurably inert** — 0 NOATK candidates in 264 logged decisions. Option (c) is
  pinned at `0` by the **2026-08-05 user ruling** ("regardless of what happens next") after measuring
  finish rate **47.1% → 26.9%**. Option (b) was rejected 2026-07-29.
* **Winona is the more expensive site on every frame measure** — 28,575 frames per loss vs Norman's
  18,800 (+52%).

⇒ **The bot's binding constraint is TIME, not this fight.** Per the user's 2026-08-05 directive, the
work went back to STORY CONTENT (`#24-e4healing`). If anyone revisits the lead policy, the cheapest
honest first step is the offline replay of the 264 recorded `lead vs Normal` decisions through
`team_policy.lead_rank_key` — with arm 0 required to reproduce the recorded pick on ≥99% of lines as
its fault gate, and a pre-registered kill criterion of **<10% of decisions changed**.
