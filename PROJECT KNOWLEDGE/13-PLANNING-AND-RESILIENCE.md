# 13 — Planning & Resilience (Story bot intelligence)
> Design doc for HOW the bot decides and stays robust. Companion to
> `12-STORYMODE-DESIGN.md` (§AA Area Atlas, §DR defeat, §RS resume, §SC
> self-correction). Applies to Story mode first, but the METHOD is general — use
> it for any function we add. Established 2026-07-21 (user directive: plan the
> situations up front, provision-or-fall-back, never break; no cheats — clean run).

## §0. The core principle
Reactive bug-fixing lags reality. Instead, every task is designed so it **provisions
what it needs, falls back gracefully when it can't, and never just halts**. When the
bot can't do a thing, it should either (a) go get what it needs, or (b) take a sane
alternative and keep playing — dropping to Manual is the LAST resort, not the first.

## §1. The task model — goal-oriented planning
Design every task (a story beat OR any bot function) as:

> **Goal → Preconditions → (provision missing, or fall back) → Execute → Verify → Recover**

- **Goal** — the postcondition we want (usually a flag or a state: `BADGE01_GET`,
  "party has 4 mons", "HP full").
- **Preconditions** — what must be true to *attempt* it (resources, location, team
  state, prior flags). Declared explicitly per task (the retrofit, §6).
- **Provision-or-fallback** — for each unmet precondition, run its provisioning
  sub-task (which is itself a task with its own preconditions — recursion), or, if
  it can't be satisfied, take the declared fallback.
- **Execute** — do the task.
- **Verify** — confirm the postcondition; if not met, it derailed.
- **Recover** — re-localise (§SC) and retry/escalate; never silent-fail.

This is goal-oriented action planning (GOAP). The rule-based version below is the
**placeholder for the future decision "brain"** (§8) — the brain will just be what
*chooses* which provisioning/fallback to run.

## §2. Resource Ledger — "what do I have / where am I"
A single snapshot the planner reads before deciding. All read-only (no cheats).

| Resource | How to read | Used for |
|---|---|---|
| **Poké Balls** (by type) | `sum(s.quantity for s in get_item_bag().poke_balls)` | catching |
| **Money** | `get_player().money` | buying (balls, potions) |
| **Party HP** | `get_party()[i].current_hp_percentage` | heal decision |
| **Party PP** | `get_party()[i].moves[].pp` (per move) | heal / move choice |
| **Team levels** | `get_party()[i].level` | fight-readiness / training |
| **Team species/types** | `get_party()[i].species(.types)` | type matchup (future) |
| **HMs / TMs** | `get_item_bag().tms_hms` | field obstacles (Cut/Surf/…) |
| **Key items** | `get_item_bag().key_items` | story gates (Devon Goods, PokéNav) |
| **Position** | `get_map_data_for_current_position()` + `get_player_avatar()` | routing / localization |
| **Story stage** | `modules.story.detect_live()` (flags) | objective / localization |

Implementation: a small `modules/story/resources.py` (or `ledger.py`) exposing named
accessors + a `snapshot()` for logging. Cheap, called on demand.

## §3. Contingency Catalog — resource/state gap → provision → fallback
The heart of "plan the situations up front". Enumerated for the early game; extend
as we reach new mechanics. **Every entry ends in a sane state, never a halt.**

| Situation | Provision (preferred) | Fallback (if provision impossible) |
|---|---|---|
| **Out of Poké Balls** while catching | finish the battle, route to nearest **accessible mart**, buy as many balls as money allows | **skip catching** for now (log it), keep current team |
| **Money too low** to buy needed balls/items | earn (sell found/hidden items, Pickup — §5) | skip the money-gated action (skip catching / skip that purchase) |
| **Party HP low** | heal at the area's **respawn PC** (Atlas §AA) | if no PC reachable, press on / retreat |
| **Party PP depleted** (no usable damaging move) | heal at PC (restores PP) | switch to a mon with PP; else flee wild / lose→recover |
| **Team too weak** for a major fight | **train** to boss-ace+margin (built) | attempt anyway once, then retrain on loss (§DR) |
| **Type-disadvantaged** vs a fight | catch/train a favourable type; lead the best matchup (future §7) | rely on level advantage + strongest move |
| **Field obstacle** (tree/rock/water/ledge) needs an HM | the HM is a story item — get it in story order | if not yet owned, this path is genuinely gated → take the intended alt route |
| **Lost / derailed** (wrong map, nav error) | re-localise from flags+position, retry resume (built §SC) | Manual only after repeated failures |
| **Whited out** | recover from respawn, route back to objective (built §DR/§AA) | Manual only after the recovery bound |
| **Out of a key consumable** (Repel, etc.) | buy at mart if worth it | proceed without it |

**Design rule:** a task must not *assume* a resource — it must query the ledger,
and if short, invoke the catalog. Catching is the first retrofit (out-of-balls).

## §4. Mart Atlas — buying (region covered so far)
Marts in Littleroot→Rustboro→Rusturf. Stock is **badge-gated** (ROM confirms
`RustboroCity_Mart_EventScript_PokemartBasic` vs `...Expanded`). Prices are fixed.

| Mart (map enum) | Reached from | Early stock (pre-Gym-1 "basic") | Notes |
|---|---|---|---|
| **OLDALE_TOWN_MART** (2,4) | Oldale Town | Poké Ball (200), Potion (300), Antidote/Paralyze Heal/Awakening/Burn Heal/Ice Heal | first mart; near Route 101-103 |
| **PETALBURG_CITY_MART** (8,6) | Petalburg City | Poké Ball, Potion, Super Potion(?), status heals | before the Woods |
| **RUSTBORO_CITY_MART** (11,7) | Rustboro City, warp (16,45) | Poké Ball, Potion, Super Potion, status heals; **Expanded** stock after a badge | nearest mart during Gym-1 prep/catching |
| — Great Balls (600) — | any mart | **NOT in stock until later badges** | early catching uses Poké Balls only |

Prices (Gen-3, fixed): Poké Ball **200**, Great Ball 600, Potion 300, Super Potion
700. Selling = half the buy price. **Verify exact per-mart stock live when building
the buy interaction** (read the mart EventScript / try the menu).

**Buy interaction (BUILT + verified 2026-07-21):** `buy_poke_balls(count, mart)` in
early_game.py. Rustboro mart: enter warp (16,45); clerk (id1) is at (1,3) in an
enclosed booth — talk ACROSS the counter from **(3,3) facing Left**. Flow: talk →
`Task_ShopMenu` → `Task_GoToBuyOrSellMenu` (BUY is default) → `Task_BuyMenu` item
list (**Poké Ball is index 0**, cursor default) → select → "How many?" message →
`Task_BuyHowManyDialogueHandleInput` quantity (Up = +1) → confirm → "That'll be ¥X.
OK?" → `Task_CallYesOrNoCallback` (Yes default). KEY LESSONS: (1) list-menu confirms
need `wait_until_task_is_not_active(task,"A")` — single-frame A presses DON'T
register; (2) selecting an item and confirming a quantity each show a MESSAGE that
must be advanced with A before the next task appears. `provision_poke_balls()` buys
`min(30, affordable)` keeping a ¥500 reserve; a hiccup is caught (non-fatal → skip).
Verified: buy 5 → balls 6→11 / money −¥1000; full out-of-balls flow (balls forced to
2 → caught → bought 30 → resumed catching → team of 4).

## §5. Money model (Emerald-specific — important)
- **No Vs Seeker in Emerald.** Regular-trainer/gym rematches exist ONLY via the
  **PokéNav Match Call** (registered trainers phone *you*, RNG-driven, mostly
  mid/late game) — **not a reliable early income source.** Do NOT build an
  early-game trainer-rematch grinder; note rematches as a *late* nice-to-have.
- **Realistic early income:** sell **found + hidden items** flagged sellable, the
  **Pickup** ability (free post-battle items on Pickup mons), one-time trainer prize
  money as we progress, and plain **economy** (don't waste balls). A "sellables"
  list (item → sell value, safe-to-sell?) is a future data table.
- **Immediate policy:** keep a **money reserve** (don't spend to 0); if too poor to
  provision, **skip the money-gated action** and continue. Clean run, no cheats.

## §6. Retrofit plan — declare preconditions/fallbacks on existing scripts
Make current tasks state their needs explicitly and route through the catalog:

| Task | Preconditions | Provision / Fallback |
|---|---|---|
| `catch_starter_team` | balls > reserve; party has room; pre-Gym-1 | out of balls → buy at Rustboro mart → broke → skip catching |
| `train_team` / `_prepare_for_fight` | a battler with a damaging move; HP heals available | low HP → heal at PC (already); PP out → heal |
| `do_rustboro_gym` (+ any fight) | team ≥ threshold; HP full | below threshold → train first (built); lost → retrain (built) |
| travel legs | correct prior flags; reachable route | scene → ride out (built); derail → re-localise (built) |
| healing | PC reachable | robust warp exit (built) |

The runner ensures preconditions before executing. Start with catching (the reported
break), then sweep the rest.

## §7. Type / matchup awareness (near-term, tie to #3 note)
The battle strategy already picks the strongest move *by effective power* (includes
type). Add: (a) **lead the best type matchup** vs a known gym leader; (b) when
catching, mild preference for a type useful for the next gym (still "random enough").
Keep as a small, explicit layer — not a full battle AI yet.

## §8. Future: decision brain(s) (noted, not built)
The rule-based planner above is a placeholder. Later: one or more specialised
decision modules the bot invokes per detected situation (GOAP planner and/or an
LLM-based planner) to choose provisioning/fallbacks and handle novel states. The
whole point of §1-§3 is to make that swap-in clean: the brain replaces the *choice*,
the ledger/catalog/atlas stay. Still no cheats — the AI plays the game legitimately.

## §9. The rule going forward (with §AA)
Before scripting ANY area or function: map its Atlas facts (respawn/grass/routing/
marts/events, §AA) AND declare its preconditions + fallbacks here. Plan the
situations, then code. This doc + the Atlas are the bot's "world model"; keep them
current as the source of truth for decisions and recovery.
