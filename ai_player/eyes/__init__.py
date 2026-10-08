"""The AI's EYES, framework-free half (build step 1, design draft §2.1 / §10.7).

WHAT IS HERE, AND WHAT IS NOT
  observation.py  the vocabulary of what the AI can see: the immutable `Observation` (and the frozen
                  dataclasses inside it) that the eyes hand the brain once per look. Plain data, no
                  reads, no framework.
  view.py         the AI's own PERCEPTION RULES: the GBA's on-screen window (15 x 11 metatiles around
                  the player, derived from the decomp and measured live), what a tile behaviour MEANS
                  (grass, water, ledge, door), what an object graphic IS (an item ball, a cut tree), when
                  a text waits for A or B (`text_printer_wait`, the decomp's render states), and the CROP
                  that keeps everything off screen out of an Observation (§10.7: a person cannot see
                  it). Tables copied from pret/pokeemerald, each with its source.
  party.py        how a party Pokemon is stored (`struct Pokemon`, its encryption and checksum), decoded
                  by the AI's own code: the framework's party reader looks a frame AHEAD on a torn read.

The other half, the part that READS the game, is `ai_player/host/eyes.py`: it is the only file that
touches the framework (through the read-only doors `gates/check_purity.py` lists for it), so a
standalone build (RULING 37 Q1) replaces that one file and keeps everything here unchanged.
`gates/test_eyes.py` proves these files import neither the framework nor the host side.
"""

__all__ = []
