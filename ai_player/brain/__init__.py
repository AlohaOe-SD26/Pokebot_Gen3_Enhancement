"""The AI's BRAIN parts (build step 3 on; design draft §2.3), each the AI's OWN code (RULING 35: the bot's
`map_path.py`, `walking.py`, `global_navigation.py` and `story/*` are teaching material, never imported; the purity
gate refuses them). Framework-free: they see the game through the hands' `Eyes` and press through their pad.

  navigator.py  walking: A* over the tiles the AI has SEEN (unknown tiles optimistic but costly), ledges one way,
                warps and doors used by stepping or pressing the right way, a person in the way waited for and walked
                round, seeded path variation; every INTENT bounded by a frame budget that progress does not reset;
                progress is NOVELTY only; "stuck:<reason>" instead of a hang or a door ping-pong
  explore.py    where to go next: the frontier of what it has seen, its exits, grass and people, weighed by the
                PERSONALITY (Catcher grass, Story exits toward unexplored maps, Trainer grass and people)
  battle.py     BUILD STEP 4: the battle decider (a move by its worth against this foe, switch, heal, run, catch)
  goals.py      BUILD STEP 5: the GOAL MANAGER: where the story is (the milestone marks), and ONE goal at a time with its
                reason: the milestone's next step (go where the game SAID, ask people, talk, use a thing, follow a scene)
                or a person's errand (heal, buy POKé BALLS, train before a known fight, an item ball in view, catch new
                species, chat), by the personality's weights; and the GoalRunner that plays it with the skills
  bossprep.py   BOSS PREPARATION BP-1 (USER RULING 58, 2026-11-09): the readiness verdict for the next gym leader (a
                deterministic duel scored with battle.py's own move valuation both ways) and, when NOT READY, the plan to
                raise ONE of the party's own Pokemon as a counter (goals.py plays it as a `raise` goal)
"""

__all__: list[str] = []
