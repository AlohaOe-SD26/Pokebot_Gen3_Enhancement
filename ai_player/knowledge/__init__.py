"""The AI's KNOWLEDGE of the game's facts (build step 4): what a person who plays Pokemon knows, as DATA.

  types.json, moves.json, species.json  extracted from the bot's game-fact data (RULING 35: teaching material) by the
                 TEST-side `ai_player/gates/extract_knowledge.py`, every entry checked against pret/pokeemerald by
                 `ai_player/gates/verify_knowledge.py`; each file names its source and that source's sha256
  facts.py       reads them (read only) and answers: the type chart, a move's facts (recoil class included), a species'
                 types, base stats and catch rate. Framework-free: no bot code, no bot file, only these JSON files.
"""

__all__: list[str] = []
