"""The AI's KNOWLEDGE of the game's facts (build step 4): what a person who plays Pokemon knows, as DATA.

  types.json, moves.json, species.json  extracted from the bot's game-fact data (RULING 35: teaching material) by the
                 TEST-side `ai_player/gates/extract_knowledge.py`, every entry checked against pret/pokeemerald by
                 `ai_player/gates/verify_knowledge.py`; each file names its source and that source's sha256
  facts.py       reads them (read only) and answers: the type chart, a move's facts (recoil class included), a species'
                 types, base stats and catch rate. Framework-free: no bot code, no bot file, only these JSON files.
  milestones.json  BUILD STEP 5: the story to badge 1 in 4 chapters plus chapter 5, RUSTBORO after the badge, and chapters 6-7, MR. BRINEY's boat to DEWFORD and the DEWFORD GYM (36 milestones), each with its proving flags and vars
                 (numbers checked against pret/pokeemerald), its maps, its steps, the HINT the game itself gives (the words
                 said and by whom), the levels of the fight ahead; written by `ai_player/gates/extract_milestones.py` from
                 the bot's `story/early_game.py` (teaching material, named with its sha256) and checked by its `--verify`
  wild_species.json  BUILD STEP 5: the species a person can meet in the wild (the favourite Pokemon is drawn from them),
                 from pret/pokeemerald's `wild_encounters.json`
  story.py       reads milestones.json: which milestone the marks prove done, for the player's own gender's houses
  atlas.py       (KI-128, 2026-10-31) the world folder's LOADER, its first slice: each map's STATIC map type (open country
                 or not), and nothing else of the world files; its docstring names the one file it reads, and
                 `gates/check_fairness.py` declares it (LOADERS) and classifies every key path of that file; (BP-1,
                 2026-11-09) also a boss's team (`boss_party`)
  seasoned.py    (boss preparation BP-1, 2026-11-09) the seasoned/ folder's LOADER: how a species evolves, the moves it
                 learns by level, the wild levels of a map's grass; declared and classified like atlas.py
"""

__all__: list[str] = []
