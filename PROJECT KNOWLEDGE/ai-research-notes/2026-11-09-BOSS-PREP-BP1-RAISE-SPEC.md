# Boss preparation BP-1, round 2: the raise as USER RULING 59's mix - the build spec, 2026-11-09 (NOT built)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). One designer wrote it read-only against branch
> `wip/ch6-bp1` (`69ce148e`, BP-1 built, its verifier FAIL); no independent check has read it yet: the build round's
> verifier is the first. It folds in the verifier's V-M1 (a trainee under a third of its HP is never healed), V-M2
> (unsupported sentences in the live evidence), V-m3 (stall-counting tests) and V-m5 (the lead after a plan ends).
> Headline, with its caveats: the experience rule is cited from the pinned decomp (switch-training gives the trainee
> exactly half of each knockout); the designer PREDICTS the per-boss budget stops the raise at about L15-18, short of
> its L20 target: kept as designed, so the A/B measures it before any budget change. Its proposed seeds (6383-6385)
> are re-checked free in every ledger at build time. The yield numbers in sections 1.4-1.5 and the appended
> calculator are developer-side only: the AI never reads them.

## Boss preparation BP-1, round 2: the raise as a mix (USER RULING 59) - the build spec (2026-11-09, NOT built)

**What this is.** The next round of BP-1 (branch `wip/ch6-bp1`, worktree `wf_e7452923-f06-3` at `69ce148e`). It rebuilds
the RAISE so that a weak counter is raised the way USER RULING 59 says a seasoned player does it: "some mix that makes
logical sense" of switch-training, its own winnable fights, and healing at a POKéMON CENTER or with Potions. It also fixes
the verifier's V-M1 (the loop that spent the budget), V-m3 (the counting tests), V-m5 (the lead when a plan ends) and
V-m1 (fixed damage against an immune type, which the new safety check uses). It corrects V-M2's unsupported sentences.

**Inputs read (all read-only).** USER RULINGS 35, 40, 44, 58 and 59 (`06-DECISIONS-LOG.md`, lines 9420, 9582 and
10039-10070); the first spec (`ai-research-notes/2026-11-08-BOSS-PREP-BP1-SPEC.md`, sections 3.1-3.3 and 5.3-5.5);
`s53/bp1/result/verify_result.json` (FAIL: V-M1, V-M2, V-m1 to V-m6, V-n1) and `build_result.json`; the live evidence
`ai_player/evidence/2026-11-09-bossprep-bp1-live-ab.txt`; the BP-1 code at `69ce148e`; the pinned decomp
`C:/Remote Projects/_decomp/pokeemerald`. Developer-side numbers below come from `s53/bp1raise/exp_calc.py` (it reads the
decomp; it is never part of the AI).

**The rulings that bind this round.** The AI plays the game itself (RULING 35). It is a seasoned player: static game
knowledge is fair, including the game's own experience rule; live hidden state is not (RULING 40). Every loop stays
inside BP-1's one per-boss budget (M5; RULING 59's reading). ⛔ The experience YIELD of a species and its GROWTH RATE stay
HIDDEN from the AI (`gates/check_fairness.py:349-350`: `species[].base_exp`, `species[].growth_rate`). The AI uses the
experience RULE (who shares, how it splits) and the EXP the game SHOWS (the summary's EXP points, the "gained N EXP"
text). It never computes a yield.

---

### 1. The experience rule, cited from the pinned decomp

#### 1.1 Who has "faced" the foe: `gSentPokesToOpponent`

- `gSentPokesToOpponent[2]` is one bit per party slot, one byte per opposing flank (`src/battle_main.c:216`).
- **Battle start.** `TryDoEventsBeforeFirstTurn` calls `ResetSentPokesToOpponentValue()` (`src/battle_main.c:3906`). That
  function sets the bits of the player's battlers on the field (`src/battle_util.c:913-926`). In a single wild battle,
  that is the lead's slot.
- **A player switch-in ADDS a bit.** `UpdateSentPokesToOpponentValue(battler)` ORs the incoming member's slot into the
  mask for a player battler (`src/battle_util.c:947-958`). It is called from `CopyPlayerPartyMonToBattleData`
  (`src/pokemon.c:4719`) and `Cmd_switchineffects` (`src/battle_script_commands.c:5224`).
- **Nothing clears the bit of a member that was switched OUT** in a single wild battle. The mask is reset only:
  - at the battle's start;
  - when an OPPONENT battler comes in (`OpponentSwitchInResetSentPokesToOpponentValue`,
    `src/battle_util.c:928-945`, called at `:951` and `:1914`);
  - by the `resetsentmonsvalue` command (`data/battle_scripts_1.s:2882`). That command sits on the trainer-battle "shift"
    path only. When the player's Pokémon faints in a wild battle, `BattleScript_HandleFaintedMon` asks "Use next
    POKéMON?" (`:2830-2842`), and `BattleScript_FaintedMonTryChoose` jumps to `BattleScript_FaintedMonSendOutNew` for a
    non-trainer battle at `:2846`, before `:2882`.

#### 1.2 How the EXP is divided: `Cmd_getexp` (`src/battle_script_commands.c:3255-3454`)

- It runs once per fainted foe (`BattleScript_GiveExp`, `data/battle_scripts_1.s:2825-2828`).
- **E**, the foe's full experience, is `expYield x foe level / 7`, with integer arithmetic (`:3310`).
- **Who shares.** The count `viaSentIn` takes every party member that has the foe's bit AND HP above 0 (`:3292-3297`).
  A fainted member is skipped by the `continue` at `:3294`, so it does not reduce anyone's share.
- **The share.** With no Exp. Share held, each counted member gets `E / viaSentIn` (integer division, at least 1:
  `:3324-3326`).
- **The bonuses.** A trainer battle gives x1.5 (`:3378-3379`), a traded Pokémon x1.5 (`:3381-3392`), and a Lucky Egg
  x1.5 (`:3376-3377`). A member at level 100 gets nothing (`:3351-3356`).
- **A fainted member gets nothing.** The gain is set only when the member has HP (`:3367`), and the EXP update needs HP
  (`:3431`).
- **The receiver's level is not in the formula.** No term compares the member's level with the foe's. A trainee 2 to 10
  levels below the foe's band gets exactly what a member at the foe's level would get.
- **Exp. Share.** If any LIVING member holds one (counted at `:3299-3307`, after the HP `continue`), the members that were
  sent out split `E/2`, and each living holder also gets `E/2 / holders` (`:3312-3321`, `:3374-3375`).
  - In Emerald it comes from MR. STONE after the letter to STEVEN is delivered
    (`data/maps/RustboroCity_DevonCorp_3F/scripts.inc:158-162`, `giveitem ITEM_EXP_SHARE`, `FLAG_RECEIVED_EXP_SHARE`).
    The project's milestone is `ch7_exp_share`.
  - So it is NOT in the bag for the BRAWLY raise, and it plays no part in this round.
  - Recorded for BP-2 and later bosses: a holder earns `E/2` without being sent out. Switch-training while holding it
    gives `E/2 + E/4 = 3E/4`. Doing that needs a "give item" hand.

#### 1.3 The three questions, answered

- **A member sent out, then switched out before the foe fainted:** gets an EQUAL share, as long as it still has HP when
  the foe faints.
- **How it is divided:** evenly, by integer division, among the members that were sent out and are still standing
  (`E / viaSentIn`).
- **A fainted member:** gets nothing, and it does not dilute the others' shares.
- **Switch-training in a wild battle.** The trainee leads and is switched out on turn 1 for ONE partner, who knocks the
  foe out.
  - Both count, so the trainee gets exactly `floor(E/2)` = `floor(floor(Y x L / 7) / 2)`, where Y is the foe's yield and
    L its level. The partner gets the same.
  - This holds for any trainee level, 2 or 10 levels under the foe's band alike.
- **The trainee is never hit on its switch-out turn.** In the turn order, every switch and item action goes before every
  move (`src/battle_main.c:4817-4825`). Pursuit is the one exception.
  - No land Pokémon of ROUTE101-104, PETALBURG_WOODS, ROUTE115 or ROUTE116 knows Pursuit at its levels. This was computed
    from `level_up_learnsets.h` with the game's initial-moveset rule (the last four level-up moves:
    `GiveBoxMonInitialMoveset`, `src/pokemon.c:2991-3011`). Test R4e checks it.
- **The field party order is not changed by an in-battle switch.**
  - `SwitchPartyOrder` (`src/battle_main.c:4086-4097`) changes only `gBattlePartyCurrentOrder`, through
    `SwitchPartyMonSlots` (`src/party_menu.c:6051-6056`).
  - `gPlayerParty` is in battle order only while the in-battle party menu is open: `OpenPartyMenuInBattle` calls
    `UpdatePartyToBattleOrder` (`:5774-5779`), and closing the menu calls `UpdatePartyToFieldOrder` (`:1231-1236`).
  - So after a switch-trained battle the trainee is still in slot 0. Live check: P1(c).

#### 1.4 What switch-training yields per battle near RUSTBORO (developer side; the AI never reads these numbers)

`src/data/wild_encounters.json`, the first group `gWildMonHeaders`, land slot rates 20,20,10,10,10,10,5,5,4,4,1,1. Each
cell shows E, then E/2 (the switch-trained share of each of the two participants).

| ROUTE116, land L6-8 | share | yield | E | E/2 |
|---|---|---|---|---|
| Poochyena L6 | 20% | 55 | 47 | 23 |
| Whismur L6 | 20% | 68 | 58 | 29 |
| Nincada L6 / L7 | 10% / 10% | 65 | 55 / 65 | 27 / 32 |
| Abra L7 (its only move is Teleport, which ends a wild battle: `BattleScript_EffectTeleport`, `data/battle_scripts_1.s:1925-1931`) | 10% | 73 | 73 | 36, in practice 0 |
| Taillow L6 / L7 / L8 | 10% / 5% / 5% | 59 | 50 / 59 / 67 | 25 / 29 / 33 |
| Poochyena L7 / L8 | 4% / 4% | 55 | 55 / 62 | 27 / 31 |
| Skitty L7 / L8 | 1% / 1% | 65 | 65 / 74 | 32 / 37 |

The expected EXP per battle, as an own fight / switch-trained (the second pair without Abra's teleports):

| Map | Land levels | Own fight | Switch-trained | Without Abra (own / switch) |
|---|---|---|---|---|
| ROUTE116 | L6-8 | 57.7 | 28.5 | 50.4 / 24.9 |
| PETALBURG_WOODS | L5-6 | 45.1 | 22.3 | |
| ROUTE104 | L3-5 | 34.8 | 17.0 | |
| ROUTE102 | L3-4 | 28.7 | 14.0 | |
| ROUTE103 | L2-4 | 22.9 | 11.1 | |
| ROUTE101 | L2-3 | 18.6 | 8.8 | |
| ROUTE115 | L23-26 | 261.3 | 130.4 | |

ROUTE115 is out of a L21 partner's safe range (section 2.5). RUSTURF_TUNNEL has no grass, so the raise map rule never
picks it.

#### 1.5 The arithmetic for C1's Wurmple 55cfbff3 (developer side: the prediction's basis, never the AI's)

- **Growth.** The Wurmple line is `GROWTH_MEDIUM_FAST` (`EXP_MEDIUM_FAST(n) = n^3`, `experience_tables.h:6`). Total EXP
  by level:

  | Level | 3 | 4 | 5 | 7 | 10 | 14 | 16 | 18 | 19 | 20 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Total EXP | 27 | 64 | 125 | 343 | 1,000 | 2,744 | 4,096 | 5,832 | 6,859 | 8,000 |

  Wurmple evolves at L7 into Silcoon or Cascoon by PID (`evolution.h:133`), and at L10 into Beautifly or Dustox. C1's
  Wurmple became a Cascoon.
- **Phase 1: switch-trained on ROUTE116 (24.9 a battle).** From 27 EXP:
  - about 13 battles to L7;
  - about 39 battles to L10.
  - A Wurmple or Cascoon never wins safely (section 2.2).
- **Phase 2: mostly its own fights (about 45 a battle).** This counts Taillow switch-trained and Abra lost. Totals from
  the start:
  - about 78 battles to L14;
  - about 108 to L16;
  - about 146 to L18;
  - about 195 to L20.
- **Story's bounds** (`bossprep.py:105-109`):
  - 160 battles reach about L18.
  - 450,000 frames, heals included (section 2.6), at 2,500-4,000 frames a battle, allow 112-180 battles: L16-L18.
  - If Dustox needs 4 hits until L12-13, phase 1 lasts longer and the reach is L15-L17.
- ⇒ **The raise is expected to be SPENT at L15-L18, not DONE at its L20 target.** The target stays the verdict's. A run
  that ends a raise at L15-18 is the design working within M5, not a failure. The plan's cost `L^2-l^2` underestimates
  cubic EXP; that is input for BP-2, not changed here.
- **The partner's share, by design (not a leak).**
  - Phase 1 gives the partner about 39 x 25 = 970 EXP. Phase 2's Taillow switches give about 650 more. That is roughly
    1,600 EXP in all.
  - Grovyle is `GROWTH_MEDIUM_SLOW` (`experience_tables.h:7`; species_info.h `[SPECIES_GROVYLE]`). It needs 1,248 EXP from
    L22 to L23 and 2,631 from L22 to L24 (7,577 to 10,208).
  - ⇒ Expect B's Grovyle about **+1 level** over A's from switch-training itself.

---

### 2. The raise as a mix, decided per battle and per moment

**The mix in one paragraph.** A person raising a weak Pokémon:
- leads with it on a route its strong Pokémon clears easily;
- lets it fight a wild Pokémon itself only when it would win and still be standing well;
- otherwise switches to the strong Pokémon on the first turn, so the weak one shares the EXP without being hit;
- never takes it into the next battle at a sliver of HP;
- when it is low, heals it at a nearby POKéMON CENTER, or with a Potion when the centre is far and the bag has one;
- stops when the time it allowed is up.

Nothing below is a fixed recipe. Every choice follows the situation through the rules that follow.

#### 2.1 Constants (exact; homes in brackets)

| Name | Value | Meaning |
|---|---|---|
| `TRAINEE_FLOOR` [bossprep] | 1/3 | No raise battle, session or own fight is begun, or continued, with the trainee under 1/3 of its max HP or fainted. This is the line `trainee_rest` already stops at (`bossprep.py:526-537`). |
| `RAISE_MAX_HITS` [bossprep] | 3 | Its own fight only when it needs at most 3 of its hits. |
| `PARTNER_MARGIN` [bossprep] | `battle.OUTLEVELS` (5, `battle.py:151`) | The raise map's top land level is at most the KO-er's level minus this. |
| `CENTRE_NEAR_LINKS` [goals] | 2 | A heal place this many known links away or fewer is "near" (`world_distance`, `goals.py:740-768`). |
| `FIELD_POTIONS` [goals] | ("Potion", "Super Potion") | The field items the potion goal uses, weakest first. A seasoned player knows they heal 20 and 50. |
| `POTION_TO` [goals] | 2/3 | A potion goal stops once the trainee is at or above 2/3 of its max HP... |
| `POTIONS_PER_GOAL` [goals] | 2 | ...or after 2 items, whichever comes first. |
| `RELEAD_FAILS_MAX` [bossprep] | 2 | Failed lead goals per plan record (V-m5). |
| `LEADS_MAX` [bossprep] | 6 | Lead goals of any outcome per plan record (V-m5). |

#### 2.2 "Safely": `bossprep.fight_safe` (new), built only from the battle brain's own functions

```
fight_safe(member: Member, foe_species: str, foe_level: int, bar_share: float, hp: int,
           seen_moves=(), faults=NO_FAULTS) -> tuple[bool, str]
```

1. **The foe's moves.** Call `knowledge/seasoned.py` `wild_moves(foe_species, foe_level)` (new, beside `level_up`,
   `seasoned.py:96-101`). It returns the last four distinct level-up moves at or below the level: the game's
   `GiveBoxMonInitialMoveset`, `src/pokemon.c:2991-3011`. Learnsets are static, AI-allowed knowledge. Add any move the foe
   was SEEN to use (`foe.moves`). Build the foe as `BossMon(foe_species, foe_level, moves, None)` (`atlas.py:107-116`).
2. **Its HP left.** `foe_hp = max(1, round(bar_share x battle.typical_stat("hp", foe_level)))`. The bar is shown on screen,
   and the foe is a typical Pokémon of its level (rule 4.1, as in `hit_points`).
3. **Its hits.** `own = max(_own_points(member, foe, m) for m in member.moves)`. `_own_points` is `bossprep.py:358-363`,
   built on `battle.rough_share` (`battle.py:504-514`), and returns 0 for a status move. With V-m1's fix, it returns 0
   when the move's type multiplier on the foe is 0.
   - `own == 0`: return `(False, "nothing it knows hurts <foe>")`.
   - Otherwise `hits = ceil(foe_hp / own)`.
4. **Their hits.** `their = max(hit_points(foe, member, m, bar_share, True, hp) for m in foe.moves)`, or 0 when it has
   none. `hit_points` is `bossprep.py:327-355`, built on `battle.rough_share` and `type_multiplier`.
5. **A person's worst case.** The foe strikes first on every turn: `left = hp - their x hits`.
6. **The verdict.** `safe = hits <= RAISE_MAX_HITS and left >= member.max_hp x TRAINEE_FLOOR`. The reason names hits,
   their points and left, as a log line. `member` comes from `members_of(look)` (`bossprep.py:220-229`), and `hp` is its
   CURRENT HP from `look.party`, not the full HP `members_of` uses.

**Expected classes.** The discriminator must print and hash these. They are expectations, not measured.
- Wurmple L3-4 (Tackle, String Shot) is NOT safe against any ROUTE116 slot (Tackle takes 1/8 of a typical L6: about 9
  hits).
- Cascoon (Harden plus Wurmple's moves) is never safe.
- Dustox L12 at full HP (with Confusion) is safe against Poochyena, Whismur and Nincada.
- Dustox L12 is NOT safe against Taillow, because Peck hits Bug x2.

#### 2.3 In battle (`brain/battle.py`): the raise purpose, changed

M4 point 2 of the first spec ("`_switch` returns None: a switch splits the experience") is SUPERSEDED for the one
switch-training switch by USER RULING 59. The general `_switch` (`better_member`, `battle.py:1296-1339`) stays off in
purpose "raise".

1. **Per-battle memory** (reset by `begin`, `battle.py:800`):
   - `raise_mode: str | None`, one of "own", "switch", "rescue", "run", "not the trainee" or None;
   - `raise_switched: bool`.
   - The mind keeps `raise_modes: list[str]` (one entry per battle), which the raise runner reads and clears.
2. **New `_raise_turn(look, own, foe, hp_share) -> Decision | None`.** It returns None unless `self.purpose == "raise"`,
   `self.trainee` is set, the battle is wild and single, and `not mem.raise_switched`. It imports `bossprep.fight_safe`
   inside the function, because `bossprep` imports `battle` at module level (the pattern `trainee_rest` uses with
   `goals`).
   - **Turn 1** (`mem.turns == 1`, `raise_mode` None):
     - If `own.pid != self.trainee`: set "not the trainee" and return None (`RaiseWatch` handles it).
     - Else run `fight_safe(trainee, foe.species, foe.level, foe.hp_bar / HP_BAR_PIXELS, trainee.hp, foe.moves)`. If safe:
       set "own" and return None, so the battle goes on as an own fight.
     - Else take `partner = raise_partner(look, foe)`. If there is one: set "switch" and `raise_switched`, then return
       `Decision("switch", "<trainee> L<l> cannot win safely (<why>): <partner> knocks it out; <trainee> keeps its share
       (Cmd_getexp: every member sent out and standing shares)", switch_pid=partner.pid)`.
     - With no partner: set "run" and return `Decision("run", ...)`.
   - **Any later turn in "own" mode, the RESCUE.** If the trainee's `hp_share < TRAINEE_FLOOR` and a partner exists: set
     "rescue" and `raise_switched`, then switch once. The trainee keeps its share, and a run would earn nothing.
   - **After the switch, never again.** This is the one switch, so exactly two members share.
3. **New `raise_partner(look, foe) -> tuple[MonSummary, str] | None`**, the strong member's choice.
   - Candidates: party members other than the trainee, with no eggs, `hp >= max_hp / 2` (the same health rule as
     `better_member`, `battle.py:1329`), not refused, and passing `fight_safe(member, foe..., member.hp)` against the
     foe's bar.
   - Choose by the highest `battle.matchup(member.types, member.moves, member.level, foe)[0]` (`battle.py:557-575`, the
     score `replacement` uses). Ties go to the higher level, then the lower slot.
4. **The order in `_decide` (`battle.py:875-881`).** For a wild battle, call `_raise_turn` FIRST, then `_run_or_not`,
   then `_switch`. The old order would RUN a L3 trainee from a foe 6 levels up (`battle.py:1278`) where the partner wins.
   `_run_or_not` then applies to whoever is out, as for "train".
5. **`replacement` (`battle.py:1366-1407`), purpose "raise".** It never chooses the trainee while another member that can
   fight is left.
6. **`answer` to "Use next POKéMON?"** (`STRINGID_USENEXTPKMN`, a wild battle, `battle_scripts_1.s:2835-2839`), purpose
   "raise". Answer NO when the trainee is the only member that can still fight: a person runs rather than sending the
   weak one against what beat its strong one. The game's own "Can't escape!" path then forces the choice.
7. **No catch, as now** (`battle.py:820`).
8. **Log one line a battle:** `[AI-BOSSPREP] raise battle: <trainee> L<l> (<hp>/<max>) vs <foe> L<fl>: own|switch to
   <partner>|run: <why>`.

#### 2.4 Between battles (`brain/goals.py`): the trainee's floor (V-M1) and the heal choice

**V-M1, the cause.** `next_goal` derives `hurt` from the party share and `needs_rest`, which is keyed on the STRONGEST
(`goals.py:1397-1398`, `battle.py:597-612`). The trainee at 1/18 HP never made the party "hurt". The raise was chosen
again, the trainee ran from every battle at 1/18, and the result was 12 sessions of +0 EXP (3, 10 and 11 such sequences
on 6377, 6378 and 6379).

1. **Move `bp_plan = self.boss_prep(look, index)`** (`goals.py:1401`) above the `must_rest` line (`:1397`). It reads
   nothing those lines set.
2. **New `GoalManager._trainee_low(look, bp_plan) -> str | None`.** It returns "fainted" or "low (<hp>/<max>)" when the
   plan's record has `status == "active"`, the trainee is in the party, and its HP is 0 or under `TRAINEE_FLOOR` of its
   max. Otherwise it returns None. It is always None in chapters 1-5, where there is no plan.
3. **`must_rest = has_party and (fainted or needs_rest(look.party) is not None or trainee_low is not None)`.** `hurt`
   follows as today. The existing heal step (`:1408-1482`) then heals: a known place gives `heal`, none gives
   `find_center`, and `DANGER_RETRIES` applies. These are the goals the verifier asked for (V1a, V1b).
4. **The POTION branch.** Insert it in step 1, before the `heal` goal is returned. Return
   `Goal("potion", "<trainee> is low (<hp>/<max>) and the nearest POKéMON CENTER is <d> links away: a Potion here",
   boss_id, key="potion", pid=trainee_pid)` only when ALL of these hold:
   - (a) `trainee_low` starts with "low" (a Potion cannot revive a fainted Pokémon);
   - (b) nothing else needs the heal: no other member fainted, `needs_rest` is None, and `share >= heal_below`
     (Potions are for the trainee alone);
   - (c) the heal place is not near. Take `where = heal_place(world, reachable=True)` (`goals.py:1998-2019`). It is near
     when `where` is not None and `world_distance(world, _place_key(world, where)) <= CENTRE_NEAR_LINKS`. A `_place_key`
     of None counts as not near.
   - (d) the bag holds a `FIELD_POTIONS` item (`look.bag.healing`);
   - (e) `self._allowed("potion")`.

   Otherwise the heal step's goal stands: a Centre when one is near, when the trainee fainted, or when the bag has
   nothing.
5. **The second guard.** `_raise_goal` (`goals.py:2154-2176`) returns None, logging "the raise waits: the trainee is low",
   while `_trainee_low` is set. The raise never begins under the floor, even when no heal goal could be made.
6. **`Goal` gains `pid: int | None = None`** (frozen dataclass, `goals.py:435-449`; the default keeps every existing
   call).
7. **The potion goal's runner** (beside `goal.kind == "lead"`, `goals.py:2847`) calls the new hand.
8. **New hand `hands/field_item.py` `use_on(hands, pid, items, up_to, most, why) -> Generator[..., tuple[bool, int,
   str]]`.** Every press is gated and named, as in `hands/party_order.py` `lead_with`.
   - **The path.** The player must be free. START opens the menu; choose "BAG" (`START_MENU_ACTIONS`). Press LEFT/RIGHT
     until the eyes' bag pocket is "items" (`BAG_POCKETS`, `eyes/screens.py:331`), at most 5 presses. `move_cursor` to
     the item. A opens `bag_action`; choose "USE" (`BAG_MENU_ACTIONS`, `:360`, `:750-755`). On the field party screen
     ("Use on which POKéMON?"), `move_cursor` to the trainee's slot, found by PID in `look.party`. A. Advance the message
     until the bag list is back. Repeat while `hp < up_to x max_hp`, fewer than `most` items are used, and the item
     remains. Then B, and `_close` (`party_order.py:46`).
   - **Success** needs all three: the trainee's HP rose (by the game's party read, by PID); the item's count fell by the
     number used; the PID multiset is unchanged.
   - **If the eyes do not classify the use-item party screen,** extend the eyes as BP-1 did for `slotId2`, and prove it
     live (P2).
   - **A failed potion goal** counts `FAIL_LIMIT`, then cooldown (`goals.py:2223-2235`). While it is on cooldown, (e)
     fails and the Centre is used.
9. **`potion` joins neither `ERRAND_KINDS` nor any grader list** (the BP-1 precedent for `raise` and `lead`: the graders
   keep their own copy).

#### 2.5 Where the raise trains (BP1-L1) and what a failed walk does (BP1-L2, in part)

- **BP-1's rule** was "the highest land top level <= trainee level + 2" (`goals.py:2133-2152`). It sent a L4 trainee to
  PETALBURG_WOODS (L5-6), where every battle was one it could neither win nor switch out of.
- **The new `raise_maps(world, cap) -> list[str]`** (ranked).
  - **Candidates:** maps it has visited with grass of their own and a known way there, with a `land_levels` entry
    (unchanged filters).
  - **The cap:** `cap = max(trainee.level, partner.level) - PARTNER_MARGIN`, where the partner is the strongest other
    member by (level, max HP), with no eggs. "The strongest map the party's knock-out Pokémon clears with room to
    spare." The trainee's level counts only when it is the stronger one (a strong trainee fights its own battles).
  - **The ranking:** maps whose top level is at most `cap`, by the highest top (higher-level foes give more EXP, which a
    seasoned player knows from the rule, not from yields), then the nearer, then the name. Then every other candidate, by
    the lowest top.
  - **Expected for C1:** ROUTE116 (top 8 <= 21 - 5), if its memory has visited it. The discriminator prints it.
- **Per-map keys.** The raise goal's key becomes `f"raise:{map}"`. `_raise_goal` takes the first ranked map with
  `_allowed(f"raise:{map}")`.
  - A map that fails twice is put aside, and the next one is tried, instead of the whole raise.
  - No candidate at all spends the plan ("no grass within reach").
  - Every candidate on cooldown returns None that decision ("the raise waits"), counted nowhere.
  - The case where the story then sails away (6377) stays a known stop for BP-2. Nothing here blocks the story.

#### 2.6 The budget: every loop, its bound, and what a stall is

The bounds are unchanged (`bossprep.py:105-109`):

| | Story | Catcher |
|---|---|---|
| `battles` | 160 | 200 |
| `frames` | 450,000 | 550,000 |
| `stalls` | 12 | 12 |
| `reorder_fails` | 3 | 3 |

What changes is what they count.

| Loop | Bounded by |
|---|---|
| raise session -> session | `battles`, `frames`, `stalls`, `reorder_fails` (as BP-1) |
| raise -> heal or find_center -> raise | `frames`: NEW, the frames of every heal, find_center and potion goal BEGUN while the plan is `active` are added to `record["frames"]`. This was the first spec's 3.3 intent; BP-1's build counted only the raise goal. The goal runner measures `hands.pad.frames` around the goal, keyed on `manager.bp_boss` and that record's status at the goal's start. |
| raise -> potion -> raise | `frames` (as above), the bag's count, `POTIONS_PER_GOAL`, the potion goal's FAIL_LIMIT |
| a failed walk to the grass | per-map cooldown; each one is a 0-EXP session, so `stalls` |
| the one switch in a battle | `raise_switched` (at most 1) |
| re-leads (section 3) | `RELEAD_FAILS_MAX`, `LEADS_MAX`, `reorder_fails` |

- **A STALL** is a raise session (one raise goal, start to end) in which the trainee's summary EXP did not rise. BP-1
  counted "no level gained" (`goals.py:2988-2990`); the new rule is `exp_after - exp_before <= 0`.
  - A session that gained EXP resets `stalls` to 0, with or without a level.
  - Why: at L15 and above, a 7-10 battle session gains about 300-450 EXP, while a level needs 721-1,141. Under BP-1's
    rule, honest progress would be read as a stall.
  - The EXP is the summary's EXP points, which the screen shows (`_raise_exp`, `goals.py:2997-3005`).
- **New record fields** (`new_record`, `bossprep.py:485-491`), read with `.get(key, default)` so an older persisted
  record still loads:
  - `lead_before` (int or None);
  - `settle` ("none", "pending", "done", "kept" or "gave up");
  - `settle_after` (the same values);
  - `relead_fails`, `leads`, `own_fights`, `switch_fights`, `raise_runs`, `heals`, `potions`, `exp_gained`,
    `partner_exp` (all int).
- **The session's log line** (`goals.py:2992-2995`) adds: `own N, switch-trained M, run R; trainee <hp>/<max> at start`.
  `lead_before` is set ONCE, at the first raise session, before its `lead_with`: `record.setdefault("lead_before",
  slot-0 PID)`.
- The run's BASE personality decides the plan and the budget (`state.base`, as built). V-m3 asks for a test of it (R7g).

---

### 3. V-m5: the lead when a plan ends, with a bound

**The defects.** A SPENT plan left the trainee first: a Cascoon L9 led all three lost BRAWLY fights (6377, BP1-L3,
confirmed by the verifier). `_lead_goal` (`goals.py:2178-2189`) re-leads a DONE plan with no bound but the
2-failure/12-decision cooldown: V4 gave a lead goal with `reorder_fails` at 99.

**E1: the plan becomes SPENT before its boss is beaten.**
- Every place that sets `status = "spent"` goes through a new `_spend(record, why)`: `_raise_goal`, `boss_lost`, and
  `_judge` when the trainee is gone. `_spend` sets `settle = "pending"`.
- **New `_settle_goal(look, index)`.** It is called at step 5a's place on every decision, whatever `bp_plan` is.
- **The re-judge.** Compute the verdict with `lead_pid = lead_before` and with `lead_pid = trainee`
  (`judge_party`, `goals.py:2088`). The trainee is kept first only when its verdict is strictly better: class rank
  READY > CLOSE > NOT READY, then `party_left`. That gives `settle = "kept"`, with no presses. A person still leads with a
  counter that fell short if it beats the usual lead on paper.
- **Otherwise the usual lead is restored:** `Goal("lead", "<boss>: the raise is over (<why>): <species> leads again, as
  before the plan", boss_id, key="lead:settle", pid=lead_before)`.
- **No restore when:** `lead_before` is None, equals the trainee, has left the party, or is fainted. Then
  `settle = "done"`.

**E2: the plan is DONE, on the boss's gym map.** `_lead_goal` as built, plus three bounds. It returns None when:
- `record["reorder_fails"] >= BUDGET[base]["reorder_fails"]`;
- `relead_fails >= RELEAD_FAILS_MAX`;
- `leads >= LEADS_MAX`.

**E3: the boss is beaten.** The record's milestone index is below the story's index, the status is done or spent, the
trainee is still first and `settle_after` is not final. Restore `lead_before` the same way: the plan's change ends with
the fight it was for. This is offline only, because the A/B ends at `ch7_brawly`.

**The lead goal's runner** (`goals.py:2847-2853`):
- The PID is `goal.pid if goal.pid is not None else record["trainee"]`.
- `leads += 1` on every run.
- A failure adds 1 to `relead_fails` and to `reorder_fails` (as today).
- When `relead_fails` reaches the bound: set `settle` or `settle_after` to "gave up" and log "the lead stays as it is".
- A success sets the settle field to "done".

---

### 4. V-M2: the sentences the records do not support, and the corrected wording

Evidence file `ai_player/evidence/2026-11-09-bossprep-bp1-live-ab.txt`. The records are the verifier's reads of the kept
logs: `v_raise_seq.py` and `v_goalcount.py`. The growth numbers are §1.5's, now looked up in the decomp.

| Lines | As written | Status | Corrected wording |
|---|---|---|---|
| 32-34 | "in that win the trainee (Dustox L12, leading) took MACHOP, Grovyle MEDITITE, Poochyena MAKUHITA, and B's Grovyle was L24 against A's L22 (above A + 1: CONFOUNDED by leaked battles, the spec's M4 reading)" | NOT SUPPORTED, twice. The records give who was on the FIELD, not who knocked a foe out (the file's own lines 12-14). Poochyena took no turn (V-m6). The leaks gave the others +251 EXP on 6379, against the 2,631 EXP Grovyle needs from L22 to L24 (`EXP_MEDIUM_SLOW`, `experience_tables.h:7`) | "In that win the records put the trainee (Dustox L12, leading) on the field when MACHOP's bar reached 0, Grovyle L24 when MEDITITE's did (the battle brain had switched the Dustox out against MEDITITE by typing), and Poochyena L8 when MAKUHITA's did. Poochyena took no turn and the last recorded hit was Shroomish's Absorb (turn 20), so who knocked MAKUHITA out is not read. B's Grovyle was L24 against A's L22 (above A + 1: CONFOUNDED). The leaked raise battles do not explain it: they gave the others +251 EXP, a tenth of the 2,631 from L22 to L24. The extra levels came from B's far longer play after the spend (22-23 heal goals after it in B, 1 in A)." |
| 38 | "What carried those wins was the REORDER and the training after the spent raise, not the raise's target." | NOT SUPPORTED. 0 `train` goals in all six B runs, rounds 1 and 2 (`v_goalcount.py`) | "What carried those wins was the REORDER: the Wurmple, left first by the spent raise, led the story's own battles from first place and grew into a Dustox L14 there. No training goal ran in any B run (0 'train' goals in six)." |
| 36-37 | "...leading as a Dustox L14 and taking MACHOP and MEDITITE" | Same wording issue (on the field, not a knockout read) | "...leading as a Dustox L14, on the field when MACHOP's and MEDITITE's bars reached 0" |
| 28-29 | "by stalls (12 sessions with no level gained) on 6378 and 6379" | True but missing its cause | "by stalls on 6378 and 6379: 12 raise sessions in a row at L4 -> L4 with +0 EXP. The trainee sat at 1/18 HP and ran from every battle, because no heal came between a session that ended 'the trainee is low' and the next raise (the verifier's V-M1: 3, 10 and 11 such sequences on 6377, 6378 and 6379)" |
| 31-32 | "The trainee met BRAWLY as Cascoon L9, Dustox L10, Dustox L10" | True but read as the raise's work | Add: "The raise itself took it from L3 to L5 (6377), L4 (6378) and L4 (6379). It reached L9-L10 afterwards, leading the story's own battles from first place in the party." |

The same corrections apply to `build_result.json` and the report section:
- **BP1-L1:** "12 stalls at about L5-10" becomes "12 stalls at L4, each a session of +0 EXP with the trainee at 1/18 HP:
  V-M1's loop, not the session length".
- **BP1-L4:** "experience leaks ... plus step-5 training after the spent raise" becomes "B's longer play after the spent
  raise; the leaks gave a tenth of it and no training goal ran".
- **The #112 live summary:** "became a Dustox L14 through later training" becomes "through the story's own battles it
  led".
- Ledger #113 and #115: "4 of 7 played" becomes "all 7 played" (V-n1).

---

### 5. Tests

Every rule has a FAULT arm (a new `BossprepFaults` or `BattleFaults` field, or the BP-1 rule restored) beside a CONTROL.
Predictions are hashed (sha256) before every run, as in BP-1.

#### 5.1 Offline (`gates/test_bossprep.py` unless named)

**R1 TraineeFloorTests (V-M1 reproduced, then fixed).** The verifier's fixture: C1's plan active, the rest full, an EMPTY
bag.
- R1a: Wurmple at 1/18 gives `heal`, or `find_center` when no place is known.
- R1b: 5/18 gives the same.
- R1c (CONTROL): fainted gives `heal` or `find_center` (as before).
- R1d (CONTROL): 6/18, exactly a third and not under, gives `raise`.
- R1e (CONTROL): full gives `raise`.
- FAULT `trainee_floor_off` (BP-1's `hurt`): R1a and R1b give `raise`, which is the loop reproduced.
- R1f: `_raise_goal` at 5/18 returns None. FAULT `raise_guard_off`: a goal.
- R1g, the sequence: decision 1 runs a raise session that ends "the trainee ... is low (5/18)"; decision 2 must be a
  heal goal. FAULT: decision 2 is `raise`.
- ⚠ If the verifier's V1 fixture's bag holds a Potion and no centre is near, the rule's answer is `potion`. Pin the bag
  in the fixture.

**R2 ExpModelTests (gate-side model, `gates/` only, never imported by the AI).** The model is
`expected_gain(yields, foe_level, sent_alive, holders)`, mirroring `Cmd_getexp`. Hand values from §1.4:
- Poochyena L6 with 2 sent gives 23 each.
- Taillow L8 with 2 gives 33.
- 1 sent gives the full E.
- A fainted participant: the survivor gets the full E.
- FAULT `count_fainted`: 2 is counted instead of 1, so the share halves. This guards P1's expectation.

**R3 RaiseTurnTests (in `gates/test_bossprep.py`, with battle-view fixtures built as `test_battle` builds them).**

| Test | Setup | Expected | Killed by (FAULT) |
|---|---|---|---|
| R3a | Wurmple L4 18/18 vs Poochyena L6 (full bar), Grovyle L21 healthy, turn 1 | `switch` to Grovyle | `raise_never_switch` (fight or run) |
| R3b (CONTROL) | Dustox L12 full vs Poochyena L7 | `fight` | `raise_always_switch` |
| R3c | Dustox L12 vs Taillow L8 | `switch` | |
| R3d | turn 2 of an own fight, the trainee at 5/18 | the rescue switch, once | |
| R3e | no partner at half HP or more | `run` | |
| R3f | `own.pid` is not the trainee | None | |
| R3g | a trainer battle | None | |
| R3h | Dustox L12 at 14/40 vs Poochyena L7 | `switch` | `safe_full_hp` (`fight`) |
| R3i | a 5-hit own fight | not safe | `hits_unbounded` |
| R3j | Grovyle fainted; the trainee and Poochyena left | `replacement` gives Poochyena; CONTROL with only the trainee left: the trainee | `replacement_trainee_ok` |
| R3k | the trainee L3 vs a foe at L9 on turn 1 | `switch`, not run | `run_first` (the old `_decide` order) |
| R3l | "Use next POKéMON?" with only the trainee able to fight | NO; CONTROL with another member left: YES | `trainee_sent_last` |
| R3m | turn 2 with the partner out, badly matched | no second raise switch | `second_switch` |

**R4 FightSafeTests.**
- Pin the classes of §2.2 (R4a-d) with hashed predicted points.
- R4e: no `wild_moves` of any land slot of ROUTE101-104, PETALBURG_WOODS, ROUTE115 or ROUTE116 at its levels holds
  Pursuit. CONTROL: `wild_moves("Poochyena", 5)` equals `["Tackle", "Howl"]` (`level_up_learnsets.h`).

**R5 HealChoiceTests.** The trainee at 5/18 and the plan active, unless noted.

| Test | Setup | Expected | Killed by (FAULT) |
|---|---|---|---|
| R5a | the centre 2 links away, Potion x3 | `heal` | `potion_always` |
| R5b | the centre 3 or more links away, Potion x3 | `potion` with pid = the trainee | `centre_always` |
| R5c | far, no field item | `heal` | |
| R5d | the trainee fainted, far, Potion | `heal` | `potion_revives` |
| R5e | far, Potion, and Grovyle under a third | `heal` | |
| R5f | the potion goal on cooldown | `heal` | |
| R5g (CONTROL) | the trainee at 6/18 | `raise` | |
| R5h (CONTROL) | no plan (chapter 5), a member at 5/18, others full | exactly today's goal | |

**R6 RaiseMapTests (BP1-L1, BP1-L2).** The world has the seven maps, all visited and reachable.

| Test | Setup | Expected | Killed by (FAULT) |
|---|---|---|---|
| R6a | trainee L4, Grovyle L21 | ROUTE116 | `map_by_trainee` (PETALBURG_WOODS: BP1-L1 reproduced) |
| R6b (CONTROL) | partner L12 (cap 7) | PETALBURG_WOODS | |
| R6c | trainee Grovyle L21, partner L5 | ROUTE116 | |
| R6d | nothing under the cap | the lowest top | |
| R6e | ROUTE116 failed twice | PETALBURG_WOODS | `one_raise_key` (None: BP1-L2) |

**R7 BudgetCountingTests (V-m3).** A fake runner session.

| Test | Setup | Expected | Killed by (FAULT) |
|---|---|---|---|
| R7a | the session advances `pad.frames` by 12,345 | `frames` + 12,345 | `frames_uncounted` |
| R7b | +0 EXP | `stalls` + 1 | `stalls_never` |
| R7c | +EXP, no level | `stalls` back to 0 | `stall_by_level` |
| R7d | +level | 0 | |
| R7e | 12 stalls | `spent_reason` "stalls 12 of at most 12" | |
| R7f | a heal goal while the plan is active | adds its frames; CONTROL: with no active plan it adds none | `heal_frames_uncounted` |
| R7g | `state.base` Story, `state.active` Trainer | acted, on Story's budget | `base_to_active` (only logged) |

**R8 LeadAfterTests (V-m5).**

| Test | Setup | Expected | Killed by (FAULT) |
|---|---|---|---|
| R8a | spent, the trainee first, `lead_before` Grovyle, the verdict prefers Grovyle | `lead` with pid Grovyle | `restore_never` |
| R8b (CONTROL) | the verdict prefers the trainee | no goal, `settle` "kept" | `restore_always` |
| R8c | `relead_fails` 2 | no goal | `relead_unbounded` (a goal: V4) |
| R8d | done, on the gym map, the trainee not first | `lead` the trainee; with `reorder_fails` 3: None | `lead_ignores_budget` |
| R8e | the boss beaten (milestone passed), done, the trainee first | `lead` Grovyle | |
| R8f | `lead_before` None | nothing | |

**R9 OwnImmunityTests (V-m1).**
- Night Shade from a L20 against a Normal boss Pokémon: `_own_points` gives 0, and the verdict reads NOT READY.
- CONTROL: against Fighting it gives 20.
- FAULT `no_immunity_own`.

**Hands unit tests (`gates/test_hands.py`).** `use_on` on the hands harness:
- the path and its gates;
- no item: False, with no presses after the bag opens;
- a shifted target slot: FAIL.

#### 5.2 Mutants (`gates/revert_bossprep.py`; P0 control plus each one, predictions hashed)

| Mutant | Killed by |
|---|---|
| `trainee_floor_off` | R1a, R1b, R1g |
| `raise_guard_off` | R1f |
| `raise_never_switch` | R3a, and live by P1 |
| `raise_always_switch` | R3b |
| `safe_full_hp` | R3h |
| `hits_unbounded` | R3i, R4 |
| `run_first` | R3k |
| `replacement_trainee_ok` | R3j |
| `second_switch` | R3m |
| `trainee_sent_last` | R3l |
| `potion_always` | R5a |
| `centre_always` | R5b |
| `potion_revives` | R5d |
| `map_by_trainee` | R6a |
| `one_raise_key` | R6e |
| `frames_uncounted` | R7a |
| `stalls_never` | R7b |
| `stall_by_level` | R7c |
| `heal_frames_uncounted` | R7f |
| `base_to_active` | R7g |
| `restore_never` | R8a |
| `restore_always` | R8b |
| `relead_unbounded` | R8c |
| `lead_ignores_budget` | R8d |
| `no_immunity_own` | R9 |
| `count_fainted` | R2 |

- BP-1's 37 mutants stay.
- Register the new ones in `check_anchors` RUNNERS and `call_census` MUTANT_SOURCES. Re-anchor any older mutant whose
  anchor these edits move: the mistake recorded on 2026-11-09, "check every mutant runner's anchors".

#### 5.3 Live probes BEFORE the A/B (`gates/probe_bossprep.py`, new modes; development, never graded)

**P1 `--raise-battle --start probe-C1`.** `lead_with` the trainee, walk to the discriminator's raise map, and fight ONE
raise battle with the round's code. Re-roll on an Abra teleport, at most 5 battles.
- (a) The turn-1 decision is `switch` to the partner.
- (b) The trainee's summary EXP rises by exactly `floor(floor(Y x L / 7) / 2)`, and the partner's by the same. Y comes
  from `species_info.h` (gate side) and L is the foe's level from the battle view.
- (c) After the battle, the game's party slot 0 is still the trainee's PID (§1.3).
- **FAULT arm `no_switch_train`:** the partner is put first, so the trainee is never sent out. The trainee gains +0 and
  the partner the full E: the arms differ.
- **FAULT for (c):** `lead_with(partner)` before the read. The check must report FAIL.

**P2 `--potion`.** Run from P1's end, where Grovyle or another member is below max HP. If the bag has no Potion, buy one
first at RUSTBORO's mart (`menus.mart_buy`).
- `use_on` must raise the target's HP by `min(20, missing)`, lower the Potion count by 1, and leave the PID multiset
  unchanged.
- CONTROL: an item not in the bag gives False.
- FAULT: a shifted slot gives FAIL.

#### 5.4 The live A/B, after the offline gates and P1-P2 pass (development, never graded; one trajectory per seed and arm)

**The run setup.**
- **Start:** `probe-C1` (`s53/ch5stops/out/probe/probe-C1`, RUSTBORO (19,53), md5 e909e537, Story), target `ch7_brawly`.
- **Frames:** 1,200,000.
- **Wall:** 12,000 s, raised from 9,000 because B now plays up to about 1,000,000 frames.
- **Concurrency:** every job of a batch starts together (the host clock).
- **Harness:** `s53/bp1/armsbp1.py`, copied to a round-2 file.
- **Arms:** A = `18c3d51b` (the parent: no plan). B = this round's tree, its content digest recorded in the ledger entry.
- **Seeds:** **6383, 6384, 6385.** These are the first integers from 6380 up that no ledger entry has used on any start
  (6380-6382 were #115's control seeds; the verifier found 6383 and above free in all 186 ledgers).

**The discriminator, offline first** (`probe_bossprep.py --start probe-C1 --raise`, the built code on the start state).
It prints:
1. arm A's rule: no plan;
2. arm B's plan: Wurmple 55cfbff3, target in [16, 20];
3. the raise map from `raise_maps` with its cap and partner (expected ROUTE116 with Grovyle L21-22);
4. per land slot of that map, `fight_safe`'s class for the trainee at its start level (expected: all switch) and
   projected to Dustox L12 (expected: own against Poochyena, Whismur and Nincada; switch against Taillow);
5. the bag's `FIELD_POTIONS` count;
6. the nearest centre's links from the map (near or far);
7. gate side: §1.4's expected EXP a battle for that map, and §1.5's battles to L10, L16 and L20.

**STOP** if (2) is not Wurmple in [16, 20], or (3)'s top level is above the cap. The spec and the code disagree; reconcile
before spending a run. That is not a result.

**The pre-registered prediction (hashed before launch).**
- A: BADGE02 in 0 of 3.
- B:
  - the plan is made on 3 of 3;
  - the trainee's first raise battle is switch-trained on 3 of 3;
  - **V-M1 closed:** 0 raise goals follow a session that ended "the trainee ... is low" or "has fainted" without a heal,
    find_center or potion goal between, and no raise session starts with the trainee under a third (the session line
    shows its HP), on 3 of 3;
  - 0 "not the trainee" lead reads (the field order is unchanged, §1.3);
  - the raise ends SPENT on `frames` or `battles` (or DONE) with the trainee a Dustox at **L15-L19** at BRAWLY's first
    fight, on 3 of 3 (§1.5);
  - BADGE02 in at least 2 of 3;
  - in each B win, the trainee is on the field at 2 or more of the 3 knockouts;
  - B's Grovyle at BRAWLY's first record is at most A's + 2. Switch-training shares with it by design: about +1, §1.5.

**The claim, read from the GAME** (the AI's words only quoted beside it). Per run:
1. `FLAG_BADGE02_GET` and `DEFEATED_DEWFORD_GYM` (the launcher's after-truth).
2. Every battle with trainer 266 (TRAINER_BRAWLY_1) and its `gBattleOutcome`.
3. For each of BRAWLY's three Pokémon:
   - WHO WAS ON THE FIELD on the record where its bar first reads 0;
   - the own battler's last chosen MOVE before that record, as the KNOCKOUT;
   - "not attributed" when the last decision was a switch or an item.
   - Keep a compact per-battle KO extract before deleting the raw records (V-n1).
4. At BRAWLY's first record, in BOTH arms: slot 0's PID, species and level; the trainee's species and level; Grovyle's
   level.
5. The raise:
   - `bp.frames`, battles (own, switch-trained, run), heals, potions, sessions, stalls, and the ending (which bound, or
     done);
   - the trainee's and the partner's EXP in raise sessions;
   - for every switch-trained battle whose records show the foe's species and level, whether the trainee's EXP step
     equals §1.4's E/2 (a second path to the cited rule).

**How it reads.**
- **B wins, the trainee knocked out at least 1 of BRAWLY's Pokémon (its move the last before the bar read 0), and
  Grovyle is at most A's + 2:** the raise changed the outcome on these trajectories. That is not a rate.
- **B wins with every knockout Grovyle's:** the raise did not carry the fight; the partner's share is the confound to
  report.
- **B loses with the trainee at L15 or higher leading:** the verdict or the fight is the gap (BP-2: "fight smarter",
  calibration).
- **B's raise spent below L15:** report the counters; the budget or the map is the finding.
- **A run that ends on its frame or wall budget before BRAWLY is INCONCLUSIVE** (m12), never "B did not earn BADGE02".
- **Before trusting a B win,** confirm the trainee evolved in the game (Dustox or Beautifly at BRAWLY).

#### 5.5 The chapters 1-5 replay control (determinism, one trajectory replayed per pair)

- **Pairs:** A = `69ce148e` (BP-1) and B = this round, on L1 (New Game to `ch1_pokedex`), C1L4 and C2L4 (to
  `ch5_rival_meet`), seeds 6386-6388. Add an F arm: B plus one planted `:goals` draw.
- **Expected:** the A and B decision streams, end frames, end marks and framework parties are identical. F differs. Do
  not compare md5s (BP1-L5).
- **Name the coverage honestly (V-m4):** chapter 1 to the Pokédex, and chapter 5 after ROXANNE. Chapters 2-4 are covered
  by the guard: no plan is active there, and `_trainee_low` is None.

#### 5.6 Gates to pass, and registrations (the BP-1 list)

- **Test suites:** `test_bossprep`, `test_battle`, `test_goals`, `test_hands`, `test_eyes` (if the eyes change),
  `test_world`, `test_kb2`, `test_saving`, `test_host`, `test_check_purity`, `test_step53_a2`, `test_evidence`,
  `test_safety_gates`, `test_check_anchors`, `test_run_regression`.
- **Checks:**
  - `check_fairness`: `seasoned.wild_moves` reads learnsets, which are AI-classified. The gate-side `species_info.h`
    reads stay in `gates/`.
  - `check_purity`, `call_census` (new functions called, or waived with reasons), `check_paths`, `check_anchors`,
    `ledger --check`.
- **Mutant runners:** `revert_bossprep`, plus every re-anchored older runner with its control.
- `run_regression --full` is not required (as in BP-1).

---

### 6. The files to change

- **`ai_player/brain/bossprep.py`:**
  - the constants of §2.1;
  - `fight_safe`;
  - V-m1 in `_own_points`;
  - the new record fields;
  - `_spend`;
  - the new `BossprepFaults` fields.
- **`ai_player/knowledge/seasoned.py`:** `wild_moves`.
- **`ai_player/brain/battle.py`:**
  - the per-battle `raise_mode`, `raise_switched` and `raise_modes`;
  - `_raise_turn` and `raise_partner`;
  - the `_decide` order;
  - `replacement` and `answer` in purpose "raise";
  - the new `BattleFaults` fields.
- **`ai_player/brain/goals.py`:**
  - `Goal.pid`;
  - `bp_plan` moved up, `_trainee_low`, and `must_rest`;
  - the potion branch;
  - `_raise_goal`'s guard and its per-map keys;
  - `raise_maps`;
  - `_lead_goal`'s bounds;
  - `_settle_goal` (E1, E3);
  - the `_raise` runner: `lead_before`, stalls by EXP, the counters, and the session line;
  - the heal and potion frames counted while a plan is active;
  - the potion runner;
  - the lead runner's PID and counters.
- **`ai_player/hands/field_item.py`** (new): `use_on`. Change **`ai_player/eyes/screens.py`** only if the use-item party
  screen needs it.
- **`gates/`:** `test_bossprep.py`, `test_battle.py`, `test_hands.py`, `revert_bossprep.py`, `probe_bossprep.py`
  (`--raise`, `--raise-battle`, `--potion`), the round-2 copy of the A/B harness, `check_anchors.py`, `call_census.py`,
  `census_waivers.json`, `run_units.py`, `run_regression.py`, and `ledger.json` (the A/B, control and probe entries).
- **Evidence:** `ai_player/evidence/2026-11-09-bossprep-bp1-live-ab.txt` (the §4 corrections) and the round-2 evidence
  file.

### 7. Out of this round

- **V-m2** (the party's Low Kick and multi-hit moves): a BP-2 item before `ACT_ON` is widened. No raise trainee near
  RUSTBORO has such a move.
- **V-m6's second half** (the brain switched the counter out against MEDITITE by typing): BP-2's "fight smarter" input.
- **Exp. Share** use, which needs a give-item hand: BP-2 and later bosses (§1.2).
- **A story step that sails away from the raise maps while a plan is active** (BP1-L2's remainder): a known stop.
- **The plan's cost model** (`L^2-l^2` against cubic EXP): BP-2 calibration (§1.5).

## Appendix: `exp_calc.py` (developer side, as it ran)

```python
"""Read-only: switch-training yields from the pinned decomp (developer-side numbers for the BP-1 raise spec).

Cmd_getexp (src/battle_script_commands.c:3255-3333): E = expYield * foeLevel / 7 (integer); each ALIVE member whose bit is
in gSentPokesToOpponent gets E / viaSentIn (integer, min 1); no trainer bonus in a wild battle.
"""
import json
import math
import re
import sys
from pathlib import Path

D = Path("C:/Remote Projects/_decomp/pokeemerald")
MAPS = ["MAP_ROUTE101", "MAP_ROUTE102", "MAP_ROUTE103", "MAP_ROUTE104", "MAP_PETALBURG_WOODS", "MAP_ROUTE116",
        "MAP_RUSTURF_TUNNEL", "MAP_ROUTE115"]

info, cur = {}, None
for line in (D / "src/data/pokemon/species_info.h").read_text(encoding="utf-8", errors="replace").splitlines():
    m = re.match(r"\s*\[SPECIES_(\w+)\]\s*=", line)
    if m:
        cur = m.group(1)
        info.setdefault(cur, {})
        continue
    if cur is None:
        continue
    m = re.search(r"\.expYield\s*=\s*(\d+)", line)
    if m:
        info[cur]["y"] = int(m.group(1))
    m = re.search(r"\.growthRate\s*=\s*(GROWTH_\w+)", line)
    if m:
        info[cur]["g"] = m.group(1)

ptr = {}
for line in (D / "src/data/pokemon/level_up_learnset_pointers.h").read_text(encoding="utf-8").splitlines():
    m = re.match(r"\s*\[SPECIES_(\w+)\]\s*=\s*(\w+),", line)
    if m:
        ptr[m.group(1)] = m.group(2)
sets, cur = {}, None
for line in (D / "src/data/pokemon/level_up_learnsets.h").read_text(encoding="utf-8").splitlines():
    m = re.match(r"static const u16 (\w+)\[\]", line)
    if m:
        cur = m.group(1)
        sets[cur] = []
        continue
    m = re.search(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", line)
    if m and cur:
        sets[cur].append((int(m.group(1)), m.group(2)))


def wild_moves(species, level):
    """GiveBoxMonInitialMoveset: every level-up move at or below the level, the last four kept."""
    learned = [mv for lv, mv in sets.get(ptr.get(species, ""), []) if lv <= level]
    out = []
    for mv in learned:
        if mv in out:
            continue
        out.append(mv)
        if len(out) > 4:
            out.pop(0)
    return out


def total_exp(growth, n):
    if growth == "GROWTH_MEDIUM_FAST":
        return n ** 3
    if growth == "GROWTH_MEDIUM_SLOW":
        return int(6 * n ** 3 / 5 - 15 * n ** 2 + 100 * n - 140)
    if growth == "GROWTH_FAST":
        return 4 * n ** 3 // 5
    if growth == "GROWTH_SLOW":
        return 5 * n ** 3 // 4
    return None


data = json.loads((D / "src/data/wild_encounters.json").read_text(encoding="utf-8"))
group = data["wild_encounter_groups"][0]
rates = next(f["encounter_rates"] for f in group["fields"] if f["type"] == "land_mons")
print("group", group["label"], "land rates", rates)
for entry in group["encounters"]:
    if entry.get("map") not in MAPS or "land_mons" not in entry:
        continue
    mons = entry["land_mons"]["mons"]
    exp_full = exp_half = 0.0
    rows, pursuit = {}, []
    for rate, mon in zip(rates, mons):
        sp = mon["species"].replace("SPECIES_", "")
        y = info.get(sp, {}).get("y")
        levels = range(mon["min_level"], mon["max_level"] + 1)
        full = sum(y * lv // 7 for lv in levels) / len(levels)
        half = sum((y * lv // 7) // 2 for lv in levels) / len(levels)
        exp_full += rate / 100 * full
        exp_half += rate / 100 * half
        key = f"{sp} L{mon['min_level']}-{mon['max_level']}"
        rows[key] = rows.get(key, (0, y, [((y * lv // 7), (y * lv // 7) // 2) for lv in levels]))
        rows[key] = (rows[key][0] + rate, y, rows[key][2])
        for lv in levels:
            if "MOVE_PURSUIT" in wild_moves(mon["species"].replace("SPECIES_", ""), lv):
                pursuit.append(f"{sp} L{lv}")
    lo = min(m["min_level"] for m in mons)
    hi = max(m["max_level"] for m in mons)
    print(f"\n{entry['map']} land L{lo}-{hi}: expected E per battle {exp_full:.1f} (own fight), "
          f"{exp_half:.1f} (switch-trained, 2 alive participants); Pursuit users: {pursuit or 'none'}")
    for key, (rate, y, pairs) in rows.items():
        print(f"   {rate:>3}% {key:<22} expYield {y:>3}  (E, E//2) by level {pairs}  moves@max "
              f"{wild_moves(key.split()[0], int(key.split('-')[-1]))}")

for sp in ("WURMPLE", "SILCOON", "CASCOON", "BEAUTIFLY", "DUSTOX", "GROVYLE", "TREECKO", "SHROOMISH", "POOCHYENA",
           "COMBUSKEN"):
    print(sp, info.get(sp))
g = info["WURMPLE"]["g"]
print("Wurmple line growth", g, {n: total_exp(g, n) for n in (3, 4, 5, 7, 8, 10, 12, 14, 16, 18, 20)})
g = info["GROVYLE"]["g"]
print("Grovyle growth", g, {n: total_exp(g, n) for n in (21, 22, 23, 24)})
print("Cascoon moves L7-L9 after Wurmple L1-6:", sets.get(ptr.get("CASCOON", "")), "Wurmple:",
      sets.get(ptr.get("WURMPLE", "")), "Dustox:", sets.get(ptr.get("DUSTOX", ""))[:6])
sys.exit(0)
```
