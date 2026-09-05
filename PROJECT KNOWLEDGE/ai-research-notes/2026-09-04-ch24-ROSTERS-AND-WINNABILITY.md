# §Ch24 — THE ELITE FOUR ROSTERS, AND WHETHER THIS PARTY CAN BEAT THEM

**Date:** 2026-09-04 · **Status:** ⚠ **MIXED — READ THE HEADER OF EACH SECTION.**
§1 (rosters) is decomp-cited agent output, unverified by us. **§2 is MEASURED by
`probe_ch24_readiness.py` against the live fixture and REFUTES several of §3's inputs.** §3 is the
agent's analysis, preserved *with its refuted premises marked*.

⛔ **THE ORDER MATTERS: read §2 before §3.** §3 is a careful argument built on recalled stats, and
three of those stats are wrong.

---

## ⭐ 0. THE HEADLINE, IN ONE PARAGRAPH

An adversarial roster analysis concluded **"this party loses at DRAKE, fight 4 of 5"**, on the
argument that Glacia's ice OHKOs both of our fast Pokémon and that nothing left outspeeds Drake's
Salamence. **Measuring our actual party partly refutes that: Swellow was never fast enough to matter
(129 Spe vs Salamence's 132), and Sceptile SURVIVES the hit that was supposed to kill it (147 HP vs a
120-142 roll).** What survives the correction is a *different* and still-serious problem: **exactly
ONE Pokémon in the party outspeeds Salamence, and it cannot be revived if it faints.**
✅ **AND THE FIX IS FREE AND AVAILABLE** — all three relevant TM item balls are confirmed untouched.

---

## ✅ 2. WHAT WE ACTUALLY HAVE — MEASURED, `probe_ch24_readiness.py`, fixture `post_league_shop.ss1`

*(Numbered §2 deliberately: it outranks §3, which is why it is placed first.)*

```
MONEY: ₽1,741

-- FREE TM ITEM BALLS (flag SET = already taken; Gen-3 TMs are single-use)
   ✅ STILL THERE  TM13 Ice Beam    [ITEM_ABANDONED_SHIP_ROOMS_B1F_TM_ICE_BEAM]
   ✅ STILL THERE  TM02 Dragon Claw [ITEM_METEOR_FALLS_B1F_2R_TM_DRAGON_CLAW]
   ✅ STILL THERE  TM26 Earthquake  [ITEM_SEAFLOOR_CAVERN_ROOM_9_TM_EARTHQUAKE]

   slot species     lvl  HP        Speed   vs Salamence 132 Spe
   0    Sceptile    53   147/147   160     ✅ OUTSPEEDS
   1    Zigzagoon   19    48/48     33     ⛔ slower
   2    Swellow     48   139/139   129     ⛔ slower
   3    Wailord     47   226/226    72     ⛔ slower
   4    Mightyena   48   144/144    97     ⛔ slower
   5    Castform    36   103/103    63     ⛔ slower
   ⇒ MONS THAT OUTSPEED DRAKE'S ACE: 1 — Sceptile L53

   ⇒ PURCHASED BASKET: 33 usable · 11 unusable (44 bought)
```

### ⛔ THREE OF THE ANALYSIS'S INPUTS ARE WRONG

| stat | analysis assumed | **MEASURED** | consequence |
|---|---|---|---|
| Sceptile HP | 139 | **147** | Sealeo's Blizzard (120-142) **no longer OHKOs** |
| Sceptile Spe | 134 | **160** | outspeeds Salamence far more comfortably |
| **Swellow Spe** | **138** | **129** | ⛔ **it NEVER outsped Salamence (132). The "lose both fast mons" argument rests on a mon that was never fast.** |
| Swellow HP | 129 | **139** | still OHKO'd by Glacia's ice — that half stands |
| Wailord HP | 223 | **226** | immaterial |

⇒ **THE POINT-OF-NO-RETURN SET IS ONE POKÉMON, NOT TWO** — and it is a *narrower but sharper* risk
than the analysis described. Losing Sceptile means **nothing** we own moves before Salamence.

### ‼ AND THE GLACIA OHKO CLAIM, CHECKED AGAINST REAL HP
- Sceptile 147 HP vs **Sealeo L52 Blizzard (120-142)** → ✅ **SURVIVES** *(analysis said OHKO)*
- Sceptile 147 HP vs **Walrein L53 Ice Beam (125-148)** → ⚠ **ROLL-DEPENDENT** — kills only on a
  near-max roll. Not the near-certainty the analysis implied.
⚠ **The damage ROLLS are still the agent's and are NOT ours.** What is measured is our HP; what is
assumed is the damage. ⇒ the honest statement is *"the OHKO claim does not survive contact with our
real HP"*, **not** *"Sceptile is safe"*.

---

## 1. THE ROSTERS — decomp-cited (`src/data/trainer_parties.h`, `src/data/trainers.h`), UNVERIFIED BY US

⭐ **There is no separate "rematch team".** One party symbol and one trainer entry per member;
`gRematchTable` points all five tiers at the same id (`battle_setup.c:335-339`) and
`IsRematchForbidden()` excludes the E4 outright (`:1576-1586`).
⚠ **Nature and EVs are not in the struct at all** (`TrainerMonItemCustomMoves`, `include/data.h:58-65`
carries only `iv`, `lvl`, `species`, `heldItem`, `moves[4]`). EVs are 0; `iv` 250 → 30, 255 → 31.
† = ability DERIVED from `personality & 1`, not read from a table.

| trainer | line | `aiFlags` | `items[]` |
|---|---|---|---|
| SIDNEY | 3136 | `CHECK_BAD_MOVE \| TRY_TO_FAINT \| CHECK_VIABILITY \| SETUP_FIRST_TURN` | Full Restore ×2 |
| PHOEBE | 3148 | `CHECK_BAD_MOVE \| TRY_TO_FAINT \| CHECK_VIABILITY` | Full Restore ×2 |
| GLACIA | 3160 | same | Full Restore ×2 |
| DRAKE | 3172 | same | Full Restore ×2 |
| **WALLACE** | 4024 | same | **Full Restore ×4** |

**SIDNEY** (`:3215-3251`) — Mightyena L46 (Roar/Double-Edge/Sand-Attack/Crunch) · Shiftry L48 † ·
Cacturne L46 · Crawdaunt L48 † · **Absol L49 + Sitrus Berry** (Aerial Ace/Rock Slide/Swords
Dance/Slash)

**PHOEBE** (`:3253-3289`) — Dusclops L48 · Banette L49 · Sableye L50 · Banette L49 ·
**Dusclops L51 + Sitrus** (Shadow Ball/**Ice Beam**/Rock Slide/Earthquake)

**GLACIA** (`:3291-3327`) — Sealeo L50 · Glalie L50 · Sealeo L52 (**Blizzard**) ·
Glalie L52 (**Explosion**) · **Walrein L53 + Sitrus** (Surf/Body Slam/Ice Beam/**Sheer Cold**)

**DRAKE** (`:3329-3365`) — Shelgon L52 · Altaria L54 · Kingdra L53 · Flygon L53 (**Levitate**) ·
**Salamence L55 + Sitrus** (Flamethrower/Dragon Claw/Rock Slide/Crunch)

**WALLACE** (`:4414-4459`) — **SIX** — Wailord L57 † · Tentacruel L55 † · Ludicolo L56 † ·
Whiscash L56 · Gyarados L56 · **Milotic L58 + Sitrus** (**Recover**/Surf/Ice Beam/Toxic)

All five Sitrus Berries are `HOLD_EFFECT_RESTORE_HP` param **30** (`src/data/items.h:1747-1760`).

---

## 3. THE ANALYSIS — preserved, with its refuted premises marked

⛔ **Read §2 first. The struck premises are refuted by measurement.**

**What still stands, and it is the useful part:**
- ⭐⭐ **THE BINDING CONSTRAINT IS THE 4-USES-PER-BATTLE CAP, NOT THE 30 POTIONS.** 4 × 5 = **20 item
  uses maximum**; we will finish the run with ~13 Hyper Potions unused. **Buying more would not have
  helped.** *(This retroactively justifies the basket's size and refutes any "buy more potions" fix.)*
- ⭐ **A Hyper Potion heals `min(200, missing HP)`.** Four of six mons cap under 200, so healing one
  at ~30% restores ~90-100 while eating a hit ⇒ **net gain of only ~5-12 HP.** Only Wailord (226)
  gets full value. ⇒ **healing a small mon mid-fight is close to a wasted turn.**
- **No Full Heal ⇒ no answer to** Glacia's Sealeo **Attract**, Phoebe's **Confuse Ray** /
  **Will-O-Wisp**, or Wallace's **Toxic** (Tentacruel and Milotic both carry it) — except by burning
  one of three Full Restores. `#24-e4healing`.
- **No Revive ⇒ every faint is permanent for the whole gauntlet.**

**~~Premise: Sceptile (139 HP, 134 Spe) and Swellow (129 HP, 138 Spe) both die to Glacia's ice, and
they are the only two mons that outspeed Salamence.~~** ⛔ **REFUTED IN PART** — see §2: Swellow at
**129 Spe never outsped Salamence**, and Sceptile at **147 HP survives** the Blizzard roll.

**Its supply/demand model** (supply ~3,075 vs demand ~5,168, deficit ~2,100, exhausted at the end of
Drake) is ⚠ **UNVERIFIED ARITHMETIC on partly-wrong inputs.** Recorded as a shape, not a number.

**Its verdict — "expected failure at DRAKE; point of no return at GLACIA"** — is ⚠ **NOT REFUTED and
NOT CONFIRMED.** The mechanism it named is narrower than described but real: **one Pokémon, Sceptile,
is the whole speed answer to Drake, and it cannot be revived.**

---

## 4. ✅ THE FIX IS FREE, AND IT IS AFFORDABLE AT ₽1,741

**All three TM item balls are confirmed untouched** (measured, §2). Gen-3 TMs are single-use and
non-repurchasable, so this was the question that decided everything — and the answer is the good one.

| item | cost | source |
|---|---|---|
| **TM13 Ice Beam** | **₽0** | `AbandonedShip_Room_B1F` item ball ✅ still there |
| TM02 Dragon Claw | ₽0 | `MeteorFalls_B1F_2R` item ball ✅ still there |
| TM26 Earthquake | ₽0 | `SeafloorCavern_Room9` item ball ✅ still there |
| TM31 Brick Break | ₽0 | Sootopolis House 1, NPC gift, no prerequisite |
| Double-Edge tutor | ₽0 | Sootopolis PC 1F — ⚠ **ONE Pokémon, ONCE per save** |
| 2× X Special | ₽700 | Lilycove Dept. 3F (the only mart with the full X set) |

⭐ **The agent's own re-prioritisation, and it is sound: do NOT buy the X Specials yet.** They exist
to beat Milotic, and if the failure point really is Drake we never reach Milotic. **Arm Wailord
first** — it is simultaneously the mon that *survives* Glacia (resists Ice, 226 HP) and the Ice Beam
carrier that answers Drake's four dragons. ⇒ one action fixes both fights.

⛔ **NOT sold anywhere:** Max Revive (no mart in the game). **Not at the League mart:** any X-item.
**Lilycove ferry** is gated `goto_if_unset FLAG_SYS_GAME_CLEAR` — post-Hall-of-Fame, so irrelevant.

---

## 5. ‼ WHAT THIS ROUND COST AND TAUGHT

1. ⛔⛔ **MY OWN PROBE FABRICATED A READING ON ITS FIRST RUN.** I asked `get_event_flag` for
   `ITEM_METEOR_FALLS_1F_2R_TM23` — a name I invented. **It returned `False` without raising**, and
   `False` means "not yet taken", so the probe printed **"✅ STILL THERE"** for a flag that does not
   exist. ⇒ the probe now validates every name against `event_flags/emerald.txt` (1,164 names) and
   **refuses** an unknown one, **and the guard was fault-tested both ways** (the fake name is
   refused; a real name still reads). ⭐ **The rule: when a lookup's failure mode is a valid-looking
   value, an allowlist is not defensive programming — it is the only thing making the output mean
   anything.**
2. ⭐ **Two agents contradicted each other and one was wrong** (see the routing note §0c). Overlapping
   questions are worth their cost precisely because the seam is where the error shows.
3. ‼ **A careful analysis on recalled numbers is still an analysis on recalled numbers.** Every
   structural insight in §3 was excellent; three of its input stats were wrong, and they were the
   ones the conclusion turned on. ⇒ **give an agent the MEASURED party next time** — this one was
   handed "L47 across the board", which was itself wrong.
