# Poké Center inventory + existing reachability machinery — RECON NOTE, 2026-09-25

> ⚠ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). It was produced by a Claude recon
> subagent over our own `sandbox-pokebot/` tree. On any contradiction the authoritative doc wins.
> ✅ The **load-bearing** claim — §5, that a reachability oracle already exists and is wired — was
> **re-opened and verified by me** before anything was written into `03-PUNCH-LIST.md`. The
> per-chapter usage table in §3 is **NOT** individually verified; treat it as a search index.

**Why this recon happened.** The user's 2026-09-25 directive: *"This would require possibly wiring
in the locations of all pokemon, hardening map traversal (also knowledge of what is traversable
depending on what part of the story its at/chapter its on) as well as knowing how to use the
pokemon pc (withdraw/deposit) and knowing where all the pokemon pcs are that it can use."*
The withdraw/deposit half shipped and is driven (`#24-hmpcfirst`). This note addresses **"knowing
where all the pokemon pcs are"** and **"what is traversable depending on the chapter"**.

---

## ⭐⭐ THE HEADLINE: DO NOT BUILD A REACHABILITY ENGINE — ONE EXISTS, AND IT IS ALREADY WIRED

✅ **VERIFIED BY ME, 2026-09-25** (not taken from the agent):

* `sandbox-pokebot/modules/story/region_reach.py` exists — 25,910 bytes.
* `is_map_reachable(target_map, from_map=None, *, max_hops: int | None = None, **caps) -> bool`
  at `region_reach.py:483`. Its own docstring: *"Fail-safe: any read error, or an unrecognised
  `target_map`, returns False."*
* It is **already consumed by production**: `story_mode.py:1259` imports it and `:1269` calls
  `region_reach.is_map_reachable(map_enum, max_hops=_MAX_TRAINING_TRAVEL_LEGS)`.
* The choice of this module over `calculate_path` is a **recorded user decision of 2026-07-25**
  (`story_mode.py:1183`), with the asymmetry spelled out at `:1193` — *"A wrong YES from
  `region_reach` costs ONE wasted walk, which navigation then [handles]"*.

⇒ **The user's "hardening map traversal / knowledge of what is traversable" is substantially
BUILT.** It is capability-gated (`**caps`), so it already answers *"can I get there with the HMs I
currently have"* — which is the chapter-dependence the directive asks for, expressed as
capabilities rather than as a chapter number.

⛔ **A per-chapter reachability TABLE does not exist, and should not be built.** Reachability is
computed on demand from live state. A static per-chapter table would be a second source of truth
that drifts the moment the story code changes — and it would be *less* correct than the live query,
because a run can arrive at a chapter having taken a different route.

⇒ **THE ACTUAL REMAINING GAP IS SMALL AND SPECIFIC:** `heal_centers` is a hand-written tuple at
each call site, and nothing consults `region_reach` when choosing between them.

---

## 1. The `PokemonCenter` enum — `modules/map_data.py:1524-1557`

**27 members: 15 Emerald (RSE) + 12 FireRed/LeafGreen.** The Emerald set, each
`(MapRSE.<MAP>, (x, y))`:

| Line | Member | Map | Tile |
|---|---|---|---|
| 1525 | OldaleTown | OLDALE_TOWN | (6, 16) |
| 1526 | PetalburgCity | PETALBURG_CITY | (20, 16) |
| 1527 | RustboroCity | RUSTBORO_CITY | (16, 38) |
| 1528 | DewfordTown | DEWFORD_TOWN | (2, 10) |
| 1529 | SlateportCity | SLATEPORT_CITY | (19, 19) |
| 1530 | MauvilleCity | MAUVILLE_CITY | (22, 5) |
| 1531 | VerdanturfTown | VERDANTURF_TOWN | (16, 3) |
| 1532 | LavaridgeTown | LAVARIDGE_TOWN | (9, 6) |
| 1533 | FallarborTown | FALLARBOR_TOWN | (14, 7) |
| 1534 | FortreeCity | FORTREE_CITY | (5, 6) |
| 1535 | LilycoveCity | LILYCOVE_CITY | (24, 14) |
| 1536 | MossdeepCity | MOSSDEEP_CITY | (28, 16) |
| 1537 | EvergrandeCity | EVER_GRANDE_CITY | (27, 48) |
| 1538 | PacifidlogTown | PACIFIDLOG_TOWN | (8, 15) |
| 1544 | SootopolisCity | SOOTOPOLIS_CITY | (43, 31) |

⚠ `FortreeCity = (FORTREE_CITY, (5, 6))` is the one `--driver hmpcfirst` drove against, and the
drive succeeded — so at least this row is confirmed usable end to end.

## 2. What the tuple MEANS — the OUTDOOR door tile

`higher_level_actions.py:557` passes it straight to
`navigate_to_anywhere(member.value[0], member.value[1])`, and the function then walks to `(7, 4)`
(`:610`) to reach the nurse **inside**. ⇒ the enum tile is the **outdoor door**, not an interior
tile. Corroborated by the SootopolisCity comment (`map_data.py:1539-1543`), which says `(43,31)` is
*"the city-side PC door warp"* and was *"convention-checked against Mossdeep/Pacifidlog/Lilycove
... and live-pathed (38 wp)"*.

⚠ This also explains the harness signature `(7, 4)` seen mid-run in the hmpcfirst drive: that is
the nurse-counter tile, not a stuck bot.

## 3. Which centres the story actually uses — ⚠ SEARCH INDEX, NOT VERIFIED

Agent-reported; each row needs its own check before being relied on. Reported call sites:
`story_mode.py` — Rustboro `:4259`, Dewford `:4327`, Slateport `:4432`, Mauville `:4468`,
**(Mauville, Slateport) `:4534`**, Fallarbor `:4597`, Lavaridge `:4664`, Petalburg `:4715`,
**(Petalburg, Lavaridge, Fallarbor) `:4747`**, Fortree `:4873`, Mossdeep `:5027`,
**(Mossdeep,) `:5109`**. Story modules — `early_game.py` `:1321 :1336 :1573 :2010 :3698 :3746
:3806 :3911 :6057 :6297 :7033 :9618`, `seafloor_cavern.py:884`, `sootopolis.py:409 :1519`,
`sootopolis_gym.py:965`, `space_center.py:185`, `victory_road.py:1041 :1070 :1564 :2330`.

**Reported as NEVER referenced by story code:** VerdanturfTown, PacifidlogTown, and all 12 FRLG
members. ⚠ Unverified — but if true it means the enum is a superset of what the bot can currently
choose from, which is the right direction for the open work.

## 4. How the ORDER of a `heal_centers` tuple is chosen — a JUDGEMENT CALL, admitted in the source

`early_game.py`'s `ensure_hm_learner_making_room` docstring, quoted exactly:

> *"candidate Poké Centres, NEAREST FIRST, tried in order and skipped on failure — the
> `SLATEPORT_ROUTE_HEALS` pattern. ‼ The ORDER is a judgement call taken from what each calling
> segment already heals at, **not** a measured distance."*

⭐ The source already flags its own weakness. That is the hook for the open work — and note the
honest framing to preserve: replacing a judgement call with a *measured* one is an improvement only
if the measurement is real, so any change here needs its own before/after.

## 5. Reachability machinery — see the headline above

`region_reach.py`: `reachable_map_distances` `:410`, `reachable_maps` `:441`, `hops_to` `:469`,
`is_map_reachable` `:483`. Graph built from ROM MapConnections + warps, capability-gated.
`hops_to` returning a COUNT is what would let centre selection rank candidates by something
measured instead of by hand.

---

## ⛔ WHAT THIS NOTE DOES **NOT** SAY

Per the standing rule that Gemini/agent **architecture advice** is to be graded *not at all* and
its **names** graded highly: this note deliberately recommends no design. It establishes that the
oracle exists, that it is wired, that no per-chapter table exists, and that the gap is confined to
centre selection. **What to do about that is a separate decision, to be taken with its own A/B.**
