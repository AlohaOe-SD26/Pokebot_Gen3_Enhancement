# 2026-09-28 — `#27-ki47range` (KI-47: the faint chooser freezes on a 4-member party): PRE-REGISTERED PREDICTIONS

> Filed BEFORE the graded drives. Branch `wt/ki47range`. Mechanism from the recon workflow (5 agents incl. a refuter;
> `ai-research-notes/2026-09-27-batch0927-FINAL.md` wedges angle, and the refuter's plan), a NOTE until driven:
> `handle_fainted_pokemon` snapshots `gBattlePartyCurrentOrder` at entry (`battle_handler.py` ~:485), BEFORE the game
> copies the PLAYER's order back (`PlayerHandleChoosePokemon`, when its menu opens). After an ENEMY switch the global
> holds the ENEMY's order. The sweep then maps `alive_slots` (already in MENU order, because the menu's
> `UpdatePartyToBattleOrder` permuted the party) through that stale order a SECOND time. At party size 4 that can
> produce menu slots 4/5, which the cursor can never reach; the refusal-learning fallback fires only on an EMPTY
> candidate set, so the loop presses Down until the 3,000-frame KI-47 watchdog.
> Only the C0 staging was run before this file (to check the staging reaches the chooser: 148 frames, sent the chosen
> Whismur#7E9BB3BA). No discriminating arm has been run.

## THE DRIVE — `--driver ki47oor`, `r20_pregym1_party4_r116.ss1` (PINNED)

The lead is replaced by a burned 1-HP Growl-only Shedinja; it faints at the end of its first turn and the chooser runs
with the fixture's own 3 bench mons (Poochyena#5815089E, Nincada#4457D0FB, Whismur#7E9BB3BA): a 4-member party.
`KI47_ARM` writes `gBattlePartyCurrentOrder` on the FIRST faint, before the handler's snapshot.

**Discriminator (computed from `map_battle_party_index`):** living slots {1,2,3}. `Foor` O=[1,0,4,5,2,3] maps them to
{0,4,5}: slot 0 is the fainted Shedinja (refused), 4 and 5 do not exist in a 4-slot menu. The fixed code does not map
through the snapshot at all, so its candidates are {1,2,3}. The arms therefore differ on the same injected bytes.

## PREDICTIONS

| Arm | Unfixed code (Step 0 logging only) | Fixed code | Fixed + `POKEBOT_KI47_FAULT_STALEMAP=1` |
|---|---|---|---|
| C0 (no write) | resolves (~148 frames), sends the chosen mon | resolves in <= 1.5x the unfixed frames, same PID | (not run) |
| Wid (true order written) | identical to C0 (the injection is faithful) | identical to C0 | (not run) |
| Foor (stale enemy order) | FREEZES: `[KI47-OBS] ... out_of_range=[4, 5]`, a KI-47 fault claimed after >= 3,000 frames, presses mostly Down | resolves in < 3x C0 frames; no fault; sends a living bench mon | FREEZES again (the arm restores the bug) |
| Finr (O=[0,2,1,3,4,5]) | resolves, but may send a mon other than the strategy's choice | resolves AND sends the strategy's chosen PID | (not run) |

## FALSIFIERS

- Unfixed `Foor` resolves: the unreachable-candidate mechanism is wrong. Stop and re-think; do not build the fix.
- `Wid` differs from `C0`: the injection is not faithful; the staging proves nothing.
- Fixed `Foor` freezes, or sends a mon not on the bench: the fix is wrong.
- Fixed `Finr` sends a different PID than the strategy chose: fix (b) (a fresh map at ~:585) is wrong.
- Fixed `C0` slower than 1.5x: the ordinary path regressed.

## WHAT THIS DOES NOT SHOW

- A natural enemy switch (the order is injected). The batch's four logged freezes supply the natural evidence.
- Double battles: `Wid`/`C0` here are singles. The KI-66 multi-battle driver (`--driver ki66faint`) is the regression
  arm for doubles, graded by sent PID == chosen PID.
- Frequency.
