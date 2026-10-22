# W7 (spec S3-4): the adversarial pass over chapter packs 1-4, 2026-10-22

> **NOTES, not a source of truth.** One refuting recon agent per pack, each told to assume every load-bearing claim is
> wrong until the PINNED decomp (`_decomp/pokeemerald` at `731ad5bf`, checked) proves it; prompts rendered from
> `tools/workflows/templates/recon.md`. Each file quotes the decomp line for every verdict. Verify a claim before
> building on it.

## Outcome

- **No FALSE claim in any of the four packs.** ch1: 13 TRUE, 1 true only with a caveat; ch2: 1 TRUE; ch3: 4 TRUE; ch4: 5 TRUE.
- **The one wording error (ch1 claim 14):** "no one-way warps" is wrong for the truck. Its 3 exits go to `MAP_DYNAMIC`,
  and no map warps back into the truck: 27 of 30 warps are reciprocal. The generator must treat a `MAP_DYNAMIC` warp as
  one-way (queued as a fix in `04`; FIXED 2026-10-22, `07`: the truck's exits are one-way claims, and a
  secret base's exits lead back because C code records the way back, src/secret_base.c:450).
- **Load-bearing facts the packs do not carry yet.** Most are scripted events and story flags, which is slice 2 (NEEDS
  DESIGN), and the packs' headers already say so:
  - ch1: the story flag `FLAG_DEFEATED_RIVAL_ROUTE103` and `VAR_BIRCH_LAB_STATE`; the forced first battle; Oldale's west
    exit gated by `FLAG_ADVENTURE_STARTED`;
  - ch2: the gym doors locked until `VAR_PETALBURG_GYM_STATE` >= 6, and scripted `warpdoor` moves; Wally's tutorial battle
    (`special StartWallyTutorialBattle`, not a trainer battle); Petalburg's west-exit triggers (UNKNOWN whether they block);
  - ch3: the Petalburg Woods grunt is FORCED (no path avoids the trigger tiles, MEASURED); the rival battles are optional
    (a yes/no prompt) and arm only after Devon Corp 3F; Gina & Mia need two usable Pokémon;
  - ch4: beating Roxanne sets her gym trainers' defeat flags; her rematch is a double battle; her 2 Potions; Badge 1's
    Attack boost.
- These lists are the first input for slice 2's design: the command census should cover `special`, `warpdoor`,
  `MSGBOX_YESNO` and the gym `setflag` blocks.
