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
| `post_rival.ss1` | **frontier**: Rustboro (16,53), `DEFEATED_RIVAL_RUSTBORO`, `RUSTBORO_CITY_STATE=8` |

## Recon / probe scripts (standalone; edit + rerun)
- `maprecon.py` / `maprecon2.py` — static ROM map recon (`get_map_data`): warps, objects
  (NPC/item `script_symbol`), connections, sizes. How Area Atlases are built. Reliable data.
- `repro_double_faint.py` — the fault-injected **A/B proof** for the double-battle after-faint
  chooser (no emulator). The template for battle-strategy / pure-logic bug proofs.
- `doorprobe.py` — resolve a map's warp destinations (which door is which).
- `routeprobe.py` — reachability probe (which tiles a navigator can reach from a start).
- `sailprobe.py` — walk-and-log a route (used to validate the Rustboro→Route104 crossing).

## Conventions
- Prove fixes: reproduce first, prefer an A/B. Don't commit a state you can't reload.
- New drivers/saves live here; keep this README's tables current.
- Full craft + bug-patterns: `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md`.
