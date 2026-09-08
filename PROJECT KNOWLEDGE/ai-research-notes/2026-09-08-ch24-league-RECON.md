# §Ch24 (THE ELITE FOUR) — RECON, 2026-09-08

⛔⛔ **THIS IS A NOTE, NOT TRUTH.** It is the output of ONE Claude subagent, read-only, and it has
NOT been verified in our harness except where a line says **[I VERIFIED]**. On any contradiction the
authoritative doc WINS until the claim is checked. See `00-READ-THIS-FIRST.md` for the per-claim
verification gates. ⚠ Its most decision-relevant claims are exactly the ones a future session will be
tempted to act on, so they are marked individually below.

⭐ **WHY IT WAS COMMISSIONED:** §Ch24 is the only chapter with no dispatch at all, and the user asked
for routing/mapping recon so the build is not blind trial-and-error. **It is NOT next in the queue** —
the agent independently reached the same ordering the handoff already has (`#24-ch23training` first).

---

## THE FOUR FINDINGS THAT CHANGE A BUILD PLAN

### 1. ⛔ TRAINER DATA IS **NOT IN THE REPO** — teams are observable LIVE only
`modules/data/extract.py:1026-1050` extracts items, abilities, types, natures, moves and species from
the ROM — **no trainer data**. `pokeemerald.sym` has `gTrainers` at `08310030`; **nothing decodes it.**
`modules/pokemon_party.py:342-365` `get_opponent_party()` reads `gEnemyParty` **only during an active
battle**.
⇒ ⭐ **ANY Elite Four roster in this tree is RECALL, not data.** The one listing
(`ai-research-notes/2026-09-04-ch24-ROSTERS-AND-WINNABILITY.md:80-108`) is marked "decomp-cited,
UNVERIFIED BY US", and that same note's damage numbers are **REFUTED at its own head** (the IV31/EV0
assumption was measured wrong). ⛔ **Do not build a type plan on those rosters.** Either decode
`gTrainers`, read the decomp, or observe live — and say which.

### 2. ⭐⭐ `heal_party_from_bag` IS BUILT, DRIVEN, AND HAS **ZERO CALLERS**
A full-tree grep finds it at `modules/story/pokemon_league.py:221` (definition) and
`tools/story-dev/story_harness.py:15671,15674` (the `ch24heal` driver **and its fault arm**).
**No callers in `modules/`. None in `plugins/`.** ⇒ five fights, no nurse; the survival mechanism is
unreachable from production code. This is `#24-e4healing` steps 2-4.

### 3. ⛔⛔ NEVER GRADE §Ch24 ON `DEFEATED_ELITE_4_*` (this is `KI-22`, and it is a TRAP)
`ResetEliteFour` clears all four defeat flags **and** `VAR_ELITE_4_STATE`, from **both**
`EventScript_WhiteOut` **and the win path**. ⇒ those flags name a state reachable by **succeeding or
by failing**, so a predicate built on them cannot tell a Champion from a corpse.
‼ And `SYS_GAME_CLEAR` is set only at the Hall of Fame, so it cannot mark PROGRESS either. The build
spec argues the only usable first conjunct is `FLAG_ENTERED_ELITE_FOUR` — which means **committed**,
not **progressed**.

### 4. ⛔ THE LOBBY IS A ONE-WAY COMMITMENT
Every backward warp in the interior sits on `MB_NORMAL`, and all three warp paths in
`src/field_control_avatar.c` reject `MB_NORMAL` ⇒ **destination-only, they never fire**. Stepping on
the lobby tile `(9,1)` commits to all five battles **or a white-out**. There is no retreat, so
everything the party needs must be carried in.

---

## THE RESOURCE ARITHMETIC (decides whether a plan is even feasible)

§Ch23 leg 11 buys **Hyper Potion x30, Full Restore x3, Full Heal x8, Revive x3 = 44 items**.
`battle_items.py:85` filters `param > 0`, and Full Heal / Revive carry `parameter == 0`, so
**11 of the 44 are invisible in battle** — deliberately, per `battle_items.py:16-18`.
⇒ **In battle: Hyper Potion and Full Restore only. Out of battle: all 44** — via the function nothing
calls (finding 2).
⭐ **THE BINDING CONSTRAINT IS NOT THE POTION COUNT.** `MAX_ITEM_USES_PER_BATTLE = 4`
(`battle_items.py:46`) ⇒ **20 uses maximum across the whole gauntlet.**

## THE §Ch23 RE-ENTRY TRAP (verified in code by the agent; ⚠ CHECK BEFORE BUILDING)
`ch23_chapter_done()` conjuncts on the Elite Four basket being IN THE BAG. The moment §Ch24 spends
it, the predicate flips False, `story_mode.py:3791` re-enters all of Victory Road, leg 11 tries to
re-buy ₽54,300 while holding ₽1,741, and the **unconditional** `_guard` raises anyway.
⇒ **both the `if` and the `_guard` must be relaxed in ONE commit**, and §Ch24 must set its own marker.

## WHAT EXISTS vs WHAT DOES NOT
**EXISTS (all driven):** `heal_party_from_bag`, `teach_move_from_bag`, `apply_moveset_plan`,
`fetch_ice_beam`, `fly_to_destination`, plus eight `ch24*` harness drivers.
**ABSENT:** any `do_pokemon_league_chapter()`, any `ch24_chapter_done()`, any room/hall navigation,
any trainer engagement, any progress marker. `ch24probe` is the only code that has entered the
interior and it "sets no progress marker".

## ⚠ TWO CLAIMS I FLAG AS HIGH-RISK IF ACTED ON UNVERIFIED
* *"Only `FLAG_BADGE06_GET` is actually checked by the guards"* — sourced to a research note, not to
  our own probe. A wrong reading here strands a run in the lobby.
* The **moveset gap**: the agent reports `post_grind_L60.ss1` still carries ORIGINAL movesets
  (Sceptile with Slam not Aerial Ace, Swellow with Peck and **no Fly**, Mightyena with Tackle) ⇒
  `MOVESET_PLAN` has not been applied to the fixture. That is `KI-94` in concrete form and it means
  **every §Ch24 measurement so far used an under-prepared party.** ⭐ This one is cheap to check and
  worth checking FIRST.

## ORDERED BUILD LIST (the agent's, and it agrees with the existing queue)
0. **Not yet** — `#24-ch23training`, then the owed acceptance drives, then `#24-regimeb-noescalation`.
1. Resolve **`KI-94`**: ONE fixture at the League door with the moveset plan applied, Ice Beam
   taught, and the basket in the bag. Nothing else can be measured honestly until it exists.
2. Wire `heal_party_from_bag` into a chapter flow.
3. Relax the §Ch23 dispatch AND its `_guard` in one commit; give §Ch24 its own predicate.
4. `KI-74` (live grid for `setmetatile` doors) and `KI-89` (`scroll_to_item_in_bag` can land on the
   wrong item) — both on the critical path.
5. An OBSERVE-ONLY interior probe before any build.
6. Then the legs, dispatching on **position**, never a fixed list.
7. ⚠ **Unhandled mechanic, flagged and never addressed: Sidney's ROAR forced switch** — no handling
   found anywhere in our code.
