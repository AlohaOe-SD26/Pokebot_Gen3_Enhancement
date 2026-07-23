# tools/story-dev — the Story-bot test harness & recon tools

The **faithful test harness**, focused **drivers**, **recon scripts**, and a **progression
sampler of checkpoint saves** used to build and prove the Story bot. Committed so any agent
(Fable 5 and beyond) inherits the whole test infrastructure instead of rebuilding it.
See `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md` for the method behind these tools.

## Prereqs
- Run with **Python 3.12** via `py` (the repo's `python` is 3.9 and fails on match statements).
- Always set `PYTHONUTF8=1` (Pokémon text has non-ASCII glyphs like `é`).
- A ROM must be registered in the profile you pass (`--profile`, default `repro-ml`). The
  harness reuses the bot's profiles under `<build>-pokebot/profiles/`; if the profile doesn't
  exist it auto-creates it from the first ROM in `roms/`.
- Paths are **repo-relative** (computed from `__file__`), so this works on any checkout.

## `story_harness.py` — the faithful main-loop harness
Replicates `modules/main.py`'s loop exactly (FrameInfo → listeners → controller-stack advance →
`run_single_frame`), so harness behaviour == the real bot.

```
PYTHONUTF8=1 py story_harness.py <state|fresh> --driver <name> [--frames N] [--video] \
    [--build sandbox|custom] [--profile P] [--log F]
```
- `<state>` = a `.ss1` basename in `saves/` (see below), a full path, or `fresh` (new game
  from the title screen — StoryMode handles the intro).
- `--driver story` = the REAL `StoryMode._play`. Focused drivers isolate one thing:
  `spin gymtest traintest martbuy martrecon healtest rival ch5recon`
  `pokenavtut pokenavclear pokenavskip pokenavfaith sailrecon rivalretry saildewford`
  `shinytest` (fault-injection: forces wilds to read as SHINY → verifies the always-catch
  branch throws balls until Caught) · `storydebugreset` (runs the "Story (DEBUG - RESET)"
  mode: hard reset → forced NEW GAME → intro) · `hmtest` (fault-injection: patches the
  party to "nobody can learn Rock Smash" → proves ensure_hm_learner hunts + catches a
  learner and teaches it — run from rocksmash_got.ss1)
  (see the `choices=[...]` list + the `if args.driver == ...` dispatch, and the `*Mode` classes).
  **Add your own** driver class + a dispatch line for whatever you're isolating.
- `--video` enables the BG/OBJ renderer — **required to drive app UIs** (PokéNav etc.); their
  looped tasks stall headless. Slower; use only when needed.
- Logs go to `--log` (default `harness_<build>.log` here). New states written by drivers land in
  `saves/`.
- **`SAVE_POST_RIVAL=1`** env gates the post-rival checkpoint auto-save (off by default so it
  never clobbers `saves/post_rival.ss1` during unrelated tests).

### Quick starts
```
# Prove the double-battle after-faint fix (no emulator needed):
PYTHONUTF8=1 py repro_double_faint.py

# Watch the story play from a checkpoint:
PYTHONUTF8=1 py story_harness.py pokenav_got.ss1 --driver story --frames 20000 --profile repro-fresh

# Drive the PokéNav Match-Call tutorial faithfully (needs the renderer):
PYTHONUTF8=1 py story_harness.py pokenav_got.ss1 --driver pokenavfaith --video --frames 20000

# Regenerate a clean post_rival.ss1 (fresh run beats the rival, saves on stable-defeat):
SAVE_POST_RIVAL=1 PYTHONUTF8=1 py story_harness.py fresh_rivalprep.ss1 --driver story \
    --frames 250000 --profile repro-fresh
```

## `saves/` — progression-sampler checkpoints (load by basename)
Tested states covering the built arc (all created during development; load with `--profile
repro-fresh` or `repro-ml`). Regenerate any by running the story to that point.
| save | where |
|------|-------|
| `oldale.ss1` | Oldale Town (early) |
| `route103.ss1` | Route 103 (pre-Pokédex rival) |
| `pokedex_done.ss1` | after the Pokédex |
| `wally_done.ss1` | after the Petalburg/Wally tutorial |
| `route116team.ss1` | Route 116, pre-gym team |
| `rustboro.ss1` | Rustboro City |
| `gym1_done.ss1` | after Roxanne (Stone Badge) |
| `devon_done.ss1` / `goods_recovered.ss1` | Devon Goods / Rusturf |
| `pokenav_got.ss1` | after the PokéNav (Devon Corp 3F) |
| `fresh_rivalprep.ss1` | rival-prep (team leveled, pre-rival) |
| `post_rival.ss1` | Rustboro (16,53), `DEFEATED_RIVAL_RUSTBORO`, `RUSTBORO_CITY_STATE=8` |
| `dewford.ss1` | Dewford Town (11,9), first Briney sail done (Ch6 ✅) |
| `brawly_done.ss1` | Dewford Gym (4,4), `DELIVERED_STEVEN_LETTER` + `BADGE02_GET` (Ch7 ✅) |
| `slateport.ss1` | Slateport City (19,20) at the PC, healed (Ch8a ✅) |
| `stern_done.ss1` | Slateport, `DELIVERED_DEVON_GOODS` set (Ch8b ✅) |
| `lavaridge.ss1` | Lavaridge Town (9,7), post-Jagged-Pass, healed (Ch11c ✅) |
| `flannery_done.ss1` | **frontier**: Lavaridge Gym, `BADGE04_GET` (Ch11d ✅; next: Go-Goggles → Ch12) |

(`saves/midstuck.ss1` is a SCRATCH state some drivers overwrite when stuck — gitignored,
never rely on it across runs.)

## Recon / probe scripts (standalone; edit + rerun)
- `maprecon.py` / `maprecon2.py` — static ROM map recon (`get_map_data`): warps, objects
  (NPC/item `script_symbol`), connections, sizes. How Area Atlases are built. Reliable data.
- `repro_double_faint.py` — the fault-injected **A/B proof** for the double-battle after-faint
  chooser (no emulator). The template for battle-strategy / pure-logic bug proofs.
- `repro_shiny_noballs.py` — A/B proof (no emulator): out of balls MID-shiny → the shiny
  strategy FIGHTS ON while the ordinary catch strategy flees (both asserted).
- `repro_hm_learner.py` — part A of the HM-learner proof: compatible-pick + ROM-derived
  hunting grounds + fault-injected "nobody compatible" → hunt path. Part B = `--driver hmtest`.
- `repro_faint_matchup.py` — A/B: the stock after-faint chooser sends Thunderbolt-food
  (full-HP Swellow vs Magneton); the story chooser picks by matchup. Real Species/Type objects.
- `repro_boss_training.py` — drives the real `_prepare_for_fight` through the four
  boss-training scenarios (boss mode / 0-KO fallback / classic / grass-less).
- `repro_sufficiency.py` — the sweeper-sufficiency gate's 6-scenario A/B (skip /
  Torchic evolution-lookahead top-up / sufficient / no-sweeper / defensive veto /
  losses-bypass), all against real ROM data.
- `repro_phantom_script.py` — fault-injects the parked-script hang profile (Rock Smash's
  battle-interrupted field script): fixed rider escapes at ~600 frames, real scenes
  still time out honestly.
- `mapfacts.py PROBE_MAPS=ROUTE112_CABLE_CAR_STATION` — how the cable-car attendant's real
  tile (6,6) was found; the template for probing any interaction coordinate before trusting it.
- `repro_normalize.py` — A/B for `normalize_to_overworld` (resume-from-anywhere): 5
  fault-injected entry states (menu/message/yes-no/battle/clean) all settle B-only.
- `regen_rocksmash_taught.py` — re-capture a milestone checkpoint in a clean overworld
  (teach -> normalize -> verify -> round-trip). Template for fixing any menu-saved state.
- `petalburg_gym_probe.py` — Ch12 deep-map recon: Petalburg gym trainer objects + the
  internal room/door warp graph + a Route 111-connections check (proves the Go-Goggles
  desert is off the Norman path).
- `doorprobe.py` — resolve a map's warp destinations (which door is which).
- `routeprobe.py` — reachability probe (which tiles a navigator can reach from a start).
- `sailprobe.py` — walk-and-log a route (used to validate the Rustboro→Route104 crossing).
- `lavaridge_gym_probe.py` / `lavaridge_gym_solve.py` / `lavaridge_tiles_probe.py` /
  `lavaridge_objects_probe.py` — the Ch11d recon set. `..._tiles_probe` prints the raw
  collision/elevation/**behaviour** grid, which is what exposed the jump-south ledges;
  `..._solve` builds the chamber graph and prints the canonical fall chain. Template for
  any warp/terrain puzzle (Sky Pillar, Mossdeep, Sootopolis ice).
- `jaggedgrass_probe.py` — two-way training-tile sweep (`PROBE_MAP` / `PROBE_ANCHOR` env).
  Proves BOTH legs from the real entry tile before a grind tile is adopted.
- `gemini_relay.py` — query the Gemini API directly (`"question"` / `--file part.md ...` /
  `--model` / `--list-models` / `--out`). Key: gitignored `profiles/gemini.key` or
  `$GEMINI_API_KEY`. Surgical questions + cross-checks only — Deep Research commissions
  go through the user relay; game NUMBERS always come from modules/data (see 15-ESC §2).
- `grade_pokeprofiles.py` — the known-answer control for research responses: verifies
  learnset/TM-compat claims against the ROM-extracted data. Template for grading any
  future #24-pokeprofiles batch.

## Conventions
- Prove fixes: reproduce first, prefer an A/B. Don't commit a state you can't reload.
- New drivers/saves live here; keep this README's tables current.
- Full craft + bug-patterns: `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md`.
