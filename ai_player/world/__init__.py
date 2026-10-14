"""The AI's WORLD MODEL (build step 3, design draft §2.3 "world model / map memory"): a memory of every map the AI
has been on, built ONLY from its Observations (`memory.py`). Framework-free: it reads nothing; it is told what the
eyes saw, one look at a time, and what the AI's own steps did (a bump, a warp it used).

  memory.py  per map: every tile SEEN (as the eyes showed it on screen: walkable or blocked, ledge, water, tall
             grass, warp or door, elevation, and where the player stood when it was first seen), visit counts,
             people and item balls seen, tiles learned blocked by BUMPING; across maps: the warp graph (a door or
             stairs -> where it led, learned when used, and the way back inferred), the map connections learned
             by walking off an edge, and every map change; (build step 5) the doors the play brain RECOGNISED as a
             POKéMON CENTER's or a MART's. Persisted per run as JSON lines (`world.jsonl`).

It never reads the map's layout or the ROM's map data: the crop (design draft §10.7) is the point. A tile is known
only after it was on screen; the navigator (`ai_player/brain/navigator.py`) plans over what is known.
"""

__all__: list[str] = []
