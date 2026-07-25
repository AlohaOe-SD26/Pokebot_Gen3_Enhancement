# 18 — Research dossier: healing points & legendaries (Gemini fleet, 2026-07-24)

**STATUS: LEADS, NOT FACTS.** Ten Gemini research passes (5 angles × 2 topics) commissioned at
the user's request so that future punch-list items start with deep information instead of a
cold research round. Raw answers live in `tools/story-dev/research/`:
`heal-a1..a5.md`, `legend-b1..b5.md`; the prompts are in `tools/story-dev/research/prompts/`.

Every prompt carried a primer demanding decomp citations (`data/maps/**/scripts.inc`, `src/*.c`),
`FLAG_`/`VAR_` names, local coordinates, Emerald-vs-RS differences, and an explicit
**VERIFIED / INFERENCE / UNSURE** marking per claim. **The project's standing rule applies: a
Gemini answer is a LEAD.** Every flag/var/coord goes through `audit_flag_names.py` or a live
probe, and every learnset/TM claim through `modules/data`, before any code is written.

## Why these two topics

* **Healing points** are load-bearing for training: `story_mode.py` will only designate a wild
  area as a training area when a healing point is reachable **from that area's tile** (the
  cave-heal lesson, 2026-07-22). A missed healing point means a whole level band stays
  unusable — which is exactly the situation that produced the ~2,000,000-frame fodder grind.
* **Legendaries** are groundwork for a future hunt/living-dex feature, where the cost of a
  wrong assumption is unusually high: defeating a one-time static can destroy an irreplaceable
  encounter permanently.

## ‼ Correction already earned from this round

The user reported a heal-NPC house "between Route 113 and 112". Gemini angle 1 concluded
**(INFERENCE)** that the user was misremembering and that no such house exists on that corridor,
offering the Lavaridge hot-springs Old Woman instead and dismissing the Route 111 rest stop as
"a bed, not an NPC".

**Our own `modules/map_data.py` contains `ROUTE111_OLD_LADYS_REST_STOP = (18, 1)`**, and Route 111
runs north–south between Routes 112 and 113 — i.e. the user's recollection matches a real map that
Gemini downgraded. A live probe is verifying what is actually inside that building
(`tools/story-dev/probe_route111_rest_stop.py`, punch-list `#24-healverify`). **Do not act on
angle 1's conclusion.** This is a clean example of why Gemini output is treated as a lead: the
model was confident, structured, and wrong about the thing that mattered.

If the rest stop does heal, it is a much closer heal for the Route 111 L19-22 training band
(currently paired with FallarborTown's Poké Center only because that was the sole heal I could
verify) — see `training_areas.py` and `_training_area_heal_map()`.

## Angle index

| file | topic |
|---|---|
| `heal-a1.md` | identify the Route 112/113 heal house (‼ conclusion contradicted above) |
| `heal-a2.md` | complete list of non-Poké-Center full heals in Emerald |
| `heal-a3.md` | land encounter tables + levels + base exp for Routes 111/112/113/114, Fiery Path, Jagged Pass |
| `heal-a4.md` | automation mechanics: dialogue flow, how to CONFIRM a heal from memory, repeatability |
| `heal-a5.md` | story gating + on-foot routing from Petalburg at the Badge-4 moment |
| `legend-b1.md` | Regi trio: Sealed Chamber, Relicanth/Wailord slots, per-chamber puzzles, flags |
| `legend-b2.md` | Rayquaza / Groudon / Kyogre, Sky Pillar crumbling floors, Emerald-vs-RS |
| `legend-b3.md` | Latias/Latios, the TV-question mechanic, roamer tracking in memory |
| `legend-b4.md` | event-only mythicals (Mew/Deoxys/Jirachi/Lugia/Ho-Oh) and what is IMPOSSIBLE without event data |
| `legend-b5.md` | full obtainability matrix + which encounters can be permanently LOST by defeating them |

## Verification debt before any of this becomes code

1. Confirm the Route 111 Old Lady's Rest Stop heal live (in progress).
2. Run every claimed `FLAG_`/`VAR_` name through `audit_flag_names.py` — a phantom flag name
   silently reads False forever and gates a segment into an eternal derail loop (ML: the Ch9a
   `DEFEATED_RIVAL_ROUTE_110` incident).
3. Cross-check every encounter table and base-exp figure against `modules/data` rather than
   trusting the prose.
4. For legendaries specifically: before building ANY hunt, confirm the "can be permanently lost"
   column against the ROM. An automated hunt that KOs a one-time legendary is unrecoverable.
