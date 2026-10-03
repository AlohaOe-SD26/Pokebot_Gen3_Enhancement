# Human reference for the Emerald AI: boss levels (VERIFIED) and typical human play (ESTIMATES), 2026-10-03

> Two kinds of content, kept apart on purpose:
> - **§1 is VERIFIED.** Two Claude agents read the pret/pokeemerald decomp independently, the second one
>   adversarially, and agree 13 of 13.
> - **§2 is a NOTE: Gemini's recall of "typical human" play.** It is useful for scale, NEVER a source of truth, and
>   it must not set a code threshold without the user's agreement.
>
> Context: USER RULING 32 (`06`). The AI's goal is to play like a person.

## 1. Boss first-battle levels in Emerald (VERIFIED, decomp)

Every party below comes from `src/data/trainer_parties.h`, linked by `src/data/trainers.h`, with the opponent ids
from `include/constants/opponents.h`. These are the ids the learner keys on.

| trainer (opponent id) | party levels | ace | decomp |
|---|---|---|---|
| Roxanne (265) | 12, 12, 15 | 15 Nosepass | `sParty_Roxanne1` (trainer_parties.h:3367-3387; trainers.h:3184) |
| Brawly (266) | 16, 16, 19 | 19 Makuhita | `sParty_Brawly1` (:3391-3412) |
| Wattson (267) | 20, 20, 22, 24 | 24 Manectric | `sParty_Wattson1` (:3415-3444) |
| Flannery (268) | 24, 24, 26, 29 | 29 Torkoal | `sParty_Flannery1` (:3446-3475) |
| Norman (269) | 27, 27, 29, 31 | 31 Slaking | `sParty_Norman1` (:3477-3506) |
| Winona (270) | 29, 29, 30, 31, 33 | 33 Altaria | `sParty_Winona1` (:3508-3544) |
| Tate & Liza (271) | 41, 41, 42, 42 (DOUBLE battle) | 42 Lunatone / Solrock | `sParty_TateAndLiza1` (:3546-3575) |
| Juan (272) | 41, 41, 43, 43, 46 | 46 Kingdra | `sParty_Juan1` (:3577-3611) |
| Sidney (261) | 46, 48, 46, 48, 49 | 49 Absol | `sParty_Sidney` (:3215-3247) |
| Phoebe (262) | 48, 49, 50, 49, 51 | 51 Dusclops | `sParty_Phoebe` (:3253-3285) |
| Glacia (263) | 50, 50, 52, 52, 53 | 53 Walrein | `sParty_Glacia` (:3291-3323) |
| Drake (264) | 52, 54, 53, 53, 55 | 55 Salamence | `sParty_Drake` (:3329-3361) |
| Wallace (335) | 57, 55, 56, 56, 56, 58 | 58 Milotic | `sParty_Wallace` (:4414-4452) |

The learner now prints these beside its boss table (`knowledge.BOSS_LEVELS`).

## 2. Typical human first playthrough (Gemini 3.1 Pro estimate, UNVERIFIED NOTE)

Gemini was asked through `tools/story-dev/gemini_relay.py` (default model, no `--model`) by a Claude agent. It
gave these ranges and its own confidence:

| milestone | team level (Gemini: high confidence) | species caught by then (low-medium confidence) |
|---|---|---|
| Roxanne | 10-16 | 5-10 |
| Brawly | 14-20 | 10-20 |
| Wattson | 20-25 | 15-30 |
| Flannery | 24-30 | 25-40 |
| Norman | 27-33 | 30-50 |
| Winona | 30-36 | 40-60 |
| Tate & Liza | 37-43 | 50-75 |
| Juan | 40-47 | 60-85 |
| Elite Four | about 42-52 (often under-levelled; healing items bridge the gap) | about 60-85 |
| Wallace | 45-54 | **65-95 species owned** (of 202 in the Hoenn Dex) |

**Human habits it named**, with its own confidence:
- **High confidence:**
  - an over-levelled starter carrying the team, plus one weak Pokémon kept only for field moves (Cut, Surf, ...).
    Gemini called this the strongest human-vs-bot signal;
  - hoarding rare items;
  - walking back to heal;
  - imperfect movement and menuing.
- **Medium confidence:**
  - fighting most optional trainers;
  - picking Pokémon by preference rather than value;
  - indecisive PC box management.
- ⚠ **Its own caveat:** a player who stays on a route until EVERY species is caught reads as MORE bot-like
  (completionist), not more human.

## 3. The bot, measured against this (step 14, 62 scored runs, learner parser v3)

| signal | the bot (median) | human (§2 estimate) |
|---|---|---|
| species caught, whole run | **9.5** (range 3-17); Champion runs: 11 | 65-95 owned at the Champion |
| Pokédex owned at run end | **18.5** (max 26); Champion runs: 21 | 65-95 |
| team average level at Tate & Liza | about **33** at the first loss and **33.7** at the win (learner boss table) | 37-43 (the leaders' own Pokémon are 41-42, §1) |
| distinct places entered | 58 | (no estimate) |

Why the bot passes up new species (`[DEXFENCE] skip` reasons, per run):
- **running low on Poké Balls**, about 23 (15.3 + 4.9 + 2.5), the largest by far: "only N spare balls — below the
  dex reserve", in two spellings, plus "the last ball is reserved";
- **party slots reserved for an HM/counter "runway"**, about 14;
- a training grind in progress, about 4.5;
- the party not at full strength, about 3.

**Reading (coordinator's, a hypothesis to test, not a finding):**
- The bot ends with about a QUARTER of the Pokédex a person would own (18.5 vs 65-95, owned against owned), and
  fights its 7th gym about 4-10 levels lower than a person's estimated range.
- The largest single lever toward human-like catching looks like **ball supply** (buying and restocking balls),
  ahead of the catch-rule knobs the learner already screens. `R23_BALLRESTOCK` covers Rustboro only.
- The level gap is what the boss-mode knob (`POKEBOT_BOSSMODE_TOPUP`) and a pre-gym training target would address.
