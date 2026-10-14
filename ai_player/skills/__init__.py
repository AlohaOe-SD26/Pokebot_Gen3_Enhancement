"""The AI's SKILLS (build step 2 on): whole tasks played with the hands, each a generator that yields once per
frame and RETURNS an outcome string. Framework-free.

  intro.py       from a fresh boot: title, New Game, Birch's speech, gender and name by the personality, the truck
  clock.py       set the wall clock in the player's room (the clock on the wall in front of the player)
  roam_train.py  BUILD STEP 3: train by ROAMING through a grass patch it has seen (never spinning on a tile), fleeing
                 what it meets; the spin ratio and the distinct tiles are its metrics
  flee.py        BUILD STEP 3: get away from a WILD battle by choosing RUN with the cursor read (a trainer battle is
                 out of scope until step 4's battle decider: it returns the reason)
  battle.py      BUILD STEP 4: play a battle with the decider (`brain/battle.py`): every battle menu by its cursor
  story.py       BUILD STEP 5: the story's person-level skills: TALK to someone seen (beside them or across a counter),
                 USE a thing (PROF. BIRCH's bag, the rival's POKé BALL), PICK UP an item ball, walk into a door, heal at a
                 POKéMON CENTER's nurse, shop at a MART's clerk, choose the starter in the bag by its cursor, answer a
                 scene's yes/no by its words, and play out a scene to its end
The Pokemon Center nurse and the Poke Mart are `hands/menus.py` nurse_heal and mart_buy (the brain calls them).
"""

__all__: list[str] = []
