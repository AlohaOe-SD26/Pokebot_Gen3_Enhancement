# Route 110 rival — decomp ground truth (2026-09-13)

⚠ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). It is a Claude-agent report against
pret/pokeemerald @ `5eff7864`, cross-checked in places by a second agent and by me. The *damage
numbers and level thresholds are CALCULATIONS*, not emulator measurements — the author flagged that
explicitly. **Verify anything load-bearing in our own harness before code depends on it.**

⚠ **AND THE ITEM IT WAS COMMISSIONED FOR IS DOWNGRADED.** This was research for `#24-rival110`,
filed as "the largest defect" on PRE-`#24-wallydecline` data. On the current build Route 110 is
**6.3% of losses, 6th site**. ⇒ read this for its MECHANISM, which very likely generalises to the
current #1 (Norman, 24.0%) and #2 (Winona, 18.8%), not for its priority.

---

## ⛔ THE HEADLINE: Grovyle vs Marshtomp is an ATTRITION LOSS WITH NO HP THRESHOLD

Gen-3 formula, from verified base stats / IVs (ace `.iv=100` → 12 per stat; 0 EV; neutral nature):

```
Grovyle L20  HP 52  SpA 41  Spe 45          Marshtomp L20  HP 61  Atk 42  Spe 28
Grovyle ABSORB (20 BP) is 4x on Water/Ground  -> 30-36 dmg, and HEALS 15-18
Marshtomp MUD SHOT (55 BP) is 0.5x on Grass   -> 12-15 (14-16 with the Stone Badge)
⇒ NET GROVYLE HP PER ROUND: +0 to +6.  Grovyle also moves first (45 vs 28).
```

⇒ **Marshtomp deals less per turn than Grovyle heals.** Starting HP is irrelevant, level parity is
irrelevant, and "chip it down with the rest of the party" cannot work because the drain refuels on
every Water/Ground switch-in. **Marshtomp has no move that is not resisted** (Water Gun is also
0.5× and runs off its worst stat). It needs **L29** to flip the arithmetic.

All three mirror matchups lose at level parity *by construction* — the ace IS the counter to your
starter. Levels needed for the bare starter to win 1v1: **Marshtomp L29, Grovyle L30, Combusken L23**
— an exact match for our measured **Mudkip 12.0% < Treecko 20.3% << Torchic 43.8%**.

## ⭐ THE FIX IS ONE POKÉMON, NOT NINE LEVELS

> *"A **L17 Taillow with Wing Attack** beats the Grovyle that a **L28 Marshtomp** still loses to."*

| our starter | ace | the counter, catchable BEFORE the trigger | wins 1v1 from |
|---|---|---|---|
| Mudkip | Grovyle | **Taillow + Wing Attack** (Route 104/116, WA at L13) | **L17** |
| Treecko | Combusken | Taillow (Flying 2×) or Wingull + Water Gun | L18 |
| Torchic | Marshtomp | **Lombre + Absorb (4×)** | **L16** |

Absorb's drain scales with the fuel, which is why the counter matters so much:
Marshtomp 30-36 (heals 15-18) · Marill 22-26 · Wingull/Poochyena 13-16 · **Taillow 6-8 (heals 3-4)**.

## ⛔ THE ACE IS SENT OUT **SECOND**, NOT THIRD
`GetMostSuitableMonToSwitchInto` re-orders on every KO (`AI_monToSwitchIntoId` is reset at battle
start), and in **all three** variants the L20 ace follows the lead immediately. ⇒ any "hold the
counter for the last slot" heuristic mis-fires. And once the ace is in with an SE move it **never
switches out** (`ShouldSwitch` returns FALSE).

## Other facts worth keeping
* **Trigger:** coord_events at ROUTE110 **(33,56) (34,56) (35,56)**, gated `VAR_ROUTE110_STATE == 0`,
  set to 1 only on the win. ⛔ **MANDATORY** — proven by flood fill of `map.bin`: x=32/36 are
  collision-blocked, and blocking the three trigger tiles drops reachability from 786 tiles (min
  y=0) to 390 (min y=57). It is the only land route north. Surf needs badge 5; Cycling Road needs
  the bike, which is *in* Mauville.
* ⚠ **I briefed the agent with the WRONG gate** (`VAR_RUSTBORO_CITY_STATE == 7`, y=53) — that is the
  **Route 104** rival. Two different rivals; do not conflate them again.
* **Loss is free but not cheap:** `SetBattledTrainersFlags()` never runs, `CB2_WhiteOut` calls
  `ScriptContext_Init()` and **discards the parked script**, so no Itemfinder and no var write.
  Unlimited retries; each costs **half the player's money** (silent) and a walk back from the last
  Center *entered* (normally Slateport (19,20)). ‼ With 530 losses that halving bottoms the wallet
  out — worth checking whether our money is at 0, since that also blocks Potion purchases elsewhere.
* **The fight is fair** — no accuracy/crit/damage asymmetry. The only edge is ours: the Stone Badge
  gives **+10% physical Attack**, slightly favouring physical answers (Wing Attack, Double Kick).
* **The AI has no HP awareness and no items** — nothing to bait, nothing to outlast.
* **Grovyle's only Grass move is 20-BP Absorb**, not Leaf Blade (that is L29). The "4× advantage" is
  4× on 20 BP — which is exactly why the *drain*, not the damage, is what makes it unwinnable.

## ⇒ WHAT TO CARRY TO THE CURRENT QUEUE HEAD
1. **Type coverage beats levels, and our machinery already knows this** — `_boss_plan_is_hopeless`
   asks precisely "does any battler hold a ≥2.0 move?" The problem there is it accepts a 20-BP move
   on a L16 mon as a "credible answer" (`CREDIBLE_ANSWER_POWER = 75` against BP×eff×STAB, so Gust on
   a L16 bird passes). ⇒ **a type answer that cannot survive is not an answer** — the same shape that
   makes Marshtomp's 0.5× Mud Shot useless.
2. **Model the send-out order from the AI, not from the party data.** This is a general Gen-3 fact,
   not a Route 110 one.
3. **Check the money.** If repeated whiteouts have zeroed it, that is a cross-cutting defect.
