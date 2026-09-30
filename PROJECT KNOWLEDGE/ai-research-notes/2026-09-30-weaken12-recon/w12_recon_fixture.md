# 2026-09-30 — design v2 step 12 (weaken-to-catch) recon: the live proof's fixtures

⚠ **A NOTE, NOT TRUTH.** A Claude recon agent's report (model output), verbatim. Every load-bearing claim is re-checked by the author at its FILE:LINE before the design relies on it; the design note records which.

**Stage 1 is vacuous on every pinned fixture.** The spec's claim for `r20_pregym1_party4_r116.ss1` holds: I read the party live and it has no sleep, paralysis or exact-damage move. Across all 66 manifest rows (60 PINNED, 6 VOLATILE), the only stage-1 move anywhere is **Sing, on one Skitty (#5CCCD8BE, L17)**. That Skitty sits in party slot 3 in all 7 PINNED fixtures that carry it, and no ordinary story path ever puts it in the lead.

**Method (read-only).** I wrote `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\w12\dump_fixture_parties.py`, which follows `probe_anchor_inventory.py`'s load path.
- It uses `LibmgbaEmulator(..., is_test_run=True)`, so nothing is saved and there is no `current_state.ss1` write at exit (`sandbox-pokebot/modules/libmgba.py:127-150`).
- For each row it checks the md5, loads the state, runs 30 frames, and reads the map, badges, balls, owned dex, party (moves with effect and PP, ability, HP) and the wild table from the ROM (`modules/map.py:1885`).
- Output: `...\scratchpad\w12\all_fixtures.txt`. The worktree's `git status` was identical before and after.
- Every md5 matches except `magma_1f_fail.ss1` (VOLATILE, now d220ee594c3b). It was already ` M` in the worktree before my first run.

## (1) The step-12 fixture — VERIFIED
`r20_pregym1_party4_r116.ss1`, md5 MATCH 9710585350be. ROUTE116 (11,7), no badges, Pokédex yes, 28 balls not counting the Master Ball, 4 species owned.

| Slot | Mon | Ability | HP | Moves (PP) |
|---|---|---|---|---|
| 0 | Mudkip#550A9BE6 L13 | Torrent | 37/40 | Tackle 31/35, Growl 40/40, Mud-Slap 10/10, Water Gun 7/25 |
| 1 | Poochyena#5815089E L4 | Run Away | 16/17 | Tackle 31/35 |
| 2 | Nincada#4457D0FB L6 | Compoundeyes | 20/20 | Scratch, Harden 29/30, Leech Life 14/15 |
| 3 | Whismur#7E9BB3BA L6 | Soundproof | 23/23 | Pound, Uproar |

- **Wild table (from the ROM):** Poochyena 28%, Whismur 20%, Nincada 20%, Taillow 20% (not owned), Abra 10% (not owned), Skitty 2% (not owned).
- **Why stage 1 is vacuous by construction (VERIFIED from code):**
  - The OFF chooser only ever applies a SLEEP or PARALYZE move of the *active* battler (`sandbox-pokebot/modules/battle_strategies/catch.py:50-62`, `:186-210`); otherwise it throws.
  - With no stage-1 move, stage 1 also ends in a throw. So OFF and ON choose the same action every turn, and the throw-only classes change nothing.
- **Nothing gained during the 240k-frame run adds a stage-1 move** (decomp `src/data/pokemon/level_up_learnsets.h`, moves up to L35):
  - Mudkip :3676, Marshtomp :3692, Poochyena :3730, Nincada :3912, Whismur :4988, Taillow :3959, Abra :827 (Teleport only) — none.
  - A caught Skitty learns Sing only at L13 (:4131); the old run's Skitty was L7.
  - Nincada gets False Swipe at L25. That is Q9 and banned, and not a stage-1 move anyway.
- **Past run on this fixture** (`tools/story-dev/evidence/2026-09-28-r20P2a-ON-240k-window.txt`; code b325d257, seed not recorded):
  - It met Taillow (:28-31, caught), Abra (:67-70, `OpponentTeleported` after 1 throw) and Skitty L7 (:74-77, caught).
  - Mudkip/Marshtomp led every catch.
- **INFERRED risk for the stage-2 L1 prediction** ("ON shows `UseMove:Mud-Slap`"):
  - When the Skitty appeared, the lead was Marshtomp L17 (:48, :76).
  - Mudkip learns Bide at L15 (`level_up_learnsets.h`, Mudkip list :3676), evolves at L16 (`src/data/pokemon/evolution.h:129`), and Marshtomp learns Mud Shot at L16 (`level_up_learnsets.h:3700`).
  - So Mud-Slap may no longer be the chosen move by then. No log records it.

## (2) Scan of the other fixtures — VERIFIED
- **Every move in any party:** 49 distinct moves across all 66 rows. There is no LEVEL_DAMAGE, SONICBOOM, DRAGON_RAGE, SUPER_FANG, PARALYZE or YAWN effect anywhere; the only stage-1 move is `Sing[SLEEP]`.
- **Slot-0 species across the 60 PINNED rows:** Sceptile 27, Mightyena 15, Swellow 13, Mudkip 2, Wailord 2, Shedinja 1. Never Skitty.
- **Why a slot-3 Skitty never gets to act:**
  - The game leads with the first party slot that is alive and not an egg (pret `src/battle_controllers.c:590-606`, `SetBattlePartyIds`).
  - The catch strategy reads the moves of the active battler only (`catch.py:194-195`).
  - No story code moves Skitty to the lead:
    - training picks the strongest mon or those within `TRAIN_CATCHUP_GAP=6` of the target (`plugins/custom_modes/story_mode.py:3816-3821`, `:2112`);
    - the lead is rotated after a battle only if it fainted, and the replacement is chosen by current HP under `switch_strategy: first_available` (`modules/battle_strategies/default.py:211-216`, `_util.py:556-568`, `profiles/battle.yml:20`);
    - a grep finds no code that picks a catching lead;
    - none of the harness injection knobs gives a stage-1 move: `--inject-treecko` gives Pound/Leer/Absorb/Quick Attack (`tools/story-dev/story_harness.py:28496-28501`) and `--inject-hmmule` gives Surf/Water Gun/Tackle/Defense Curl (`:28555-28558`).
  - **Logged evidence agrees:**
    - In a storyresume on `post_mtpyre`, seed 1, Mightyena led both dex catches (`evidence/2026-09-29-r24catchhurt-G-OFF.txt:24-29` Oddish on Route 121; `:60-65` Geodude on MAGMA_HIDEOUT_1F).
    - Skitty only ever acted as a replacement in a boss fight: `[TURN 17] Skitty L17 -> UseMove:Tackle` in `evidence/2026-09-29-r27keyitems-B2-ON.txt` and `-B2-ORD.txt`.

**Ranked candidates** (all hold Sing on Skitty#5CCCD8BE L17, Cute Charm, slot 3; wild tables read from the ROM):

| # | Fixture (md5) | Where / state | Wanted wilds nearby | Would a storyresume meet one? | Stage-1 branch *if Skitty led* | Verdict |
|---|---|---|---|---|---|---|
| 1 | `post_mtpyre.ss1` (80602159694b) | MT_PYRE_SUMMIT; Skitty fainted at load, lead Sceptile 21/117 | Route 121, Mt Pyre, Magma Hideout | **Yes, VERIFIED:** OFF caught Oddish and Geodude; the CATCHHURT arm caught Shuppet, Wingull and Torkoal (`r24catchhurt-G-ON.txt`) | status (Sing), Explosion throw-only (Geodude) | vacuous: Mightyena led every catch |
| 2 | `magma_door_losing.ss1` (76ef84a3e70c) | JAGGED_PASS (16,20), 6/6 full HP, 17 balls, lead Mightyena L43 | Numel 55%, Machop 25%, Spoink 20% (L20-22); Magma Hideout 1F-4F: Geodude 55% L27-30, Torkoal 30%, Graveler 15% (L30-33), all unowned | Likely (INFERRED); replays deterministically. The one logged run used the `magmahideout` driver, not storyresume, and *fought* a wild Geodude (`r27keyitems-B2-ON.txt:4-5`); the reason was not in the kept lines | Sing; Explosion throw-only (Geodude and Graveler learn Self-Destruct at L21, pret `level_up_learnsets.h:980`, `:995`) | vacuous |
| 3 | `magma_door_ki52.ss1` (273d19b34d96) | same tile, lead Sceptile L44 | same | same (INFERRED) | same | vacuous |
| 4 | `strength_boxfirst_mauville.ss1` (ba23ca04f9d7) | MAUVILLE_CITY (22,6), full HP, lead Sceptile L44 | no wild table in the city; next grass not read | unknown | Sing | vacuous |
| 5 | `fortree_gym_wedge.ss1` (87d390d74474) | FORTREE_CITY_GYM, lead Mightyena L38 | none in the gym (Route 120 next, INFERRED) | gym trainer battles come first | Sing | vacuous |
| 6 | `post_dive_ki76.ss1` (a00378595409) | MOSSDEEP_CITY; Sceptile fainted, lead Zigzagoon L15 | surf and rods only | the fence refuses until a heal because the party is not at full HP (`story_mode.py:2669`, `:2074-2079`) | Sing | vacuous |
| 7 | `post_maxie.ss1` (19399688e730) | MAGMA_HIDEOUT_4F; 5 of 6 fainted, Skitty included | Geodude, Torkoal, Graveler | refused until a heal | none | vacuous |

**What a non-vacuous stage-1 arm would need (INFERRED — a decision for you, not a fixture that exists):**
- A Sing holder in slot 0 before the first wanted encounter. There are two ways to get it:
  - a driver pre-step that reorders the party in the game menu with `modules/story/roster.py:122 reorder_party`, which is faithful to normal play;
  - a new harness injection, which is a state write.
- Either is new code. A slot-0 Skitty L17 against L27-30 wilds would likely faint and be rotated out after its first loss.
- **Even then, "ON used Sing" does not tell the arms apart**, because OFF already sings when the one-throw chance is below 0.5 and the target is healthy (`catch.py:50-61`). OFF and ON would differ only on stage 1's extra rules:
  - Self-Destruct targets: Geodude and Graveler, about 70% of Magma Hideout encounters. Geodude's logged `exp_throws=3.0` suggests a chance of about 0.33, so OFF would sing and ON would throw;
  - Soundproof targets;
  - enders such as Abra;
  - confused or ticking targets;
  - Substitute or Safeguard;
  - the 3-try cap.
- On that basis, `magma_door_losing` with a Skitty lead would be the best discriminator.
