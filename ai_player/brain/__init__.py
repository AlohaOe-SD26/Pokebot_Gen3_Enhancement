"""The AI's BRAIN parts (build step 3 on; design draft §2.3), each the AI's OWN code (RULING 35: the bot's
`map_path.py`, `walking.py`, `global_navigation.py` and `story/*` are teaching material, never imported; the purity
gate refuses them). Framework-free: they see the game through the hands' `Eyes` and press through their pad.

  navigator.py  walking: A* over the tiles the AI has SEEN (unknown tiles optimistic but costly), ledges one way,
                warps and doors used by stepping or pressing the right way, a person in the way waited for and walked
                round, seeded path variation; every INTENT bounded by a frame budget that progress does not reset;
                progress is NOVELTY only; "stuck:<reason>" instead of a hang or a door ping-pong
  explore.py    where to go next: the frontier of what it has seen, its exits, grass and people, weighed by the
                PERSONALITY (Catcher grass, Story exits toward unexplored maps, Trainer grass and people)
"""

__all__: list[str] = []
