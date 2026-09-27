# 2026-09-27 — RULING 20 Phase 1, increment B (Fly box-first) + USER RULING 21 (the swap-back): PRE-REGISTERED PREDICTIONS

> Filed BEFORE any drive (a 300-frame smoke test only checked the premise and the injection). Branch `wt/r20fly` (cut
> from `wt/r20phase1` at `26431078`). Recon: `2026-09-27-ruling20-incB-RECON.md` (a NOTE), site "fly".
> Gate green before the drive: `probe_r20_flybox.py` (5 built-in fault arms).

## THE CHANGE UNDER TEST

- `pc_trip.pc_stand_for(map)`: the League lobby's PC is at (6,1), so its stand tile is (6,2)/Up. Every other map keeps
  (10,2)/Up. All PC walks in `pc_trip` use it.
- `ensure_fly_learner`: if no party member can take Fly but a boxed one can (`_boxed_fly_learners`), the bot walks into
  the lobby (`_in_league_lobby`), withdraws the head (make-room boxes one fighter by increment A's rule), walks back out
  onto EVER_GRANDE_CITY, and teaches Fly. It records RULING 21's swap: the fighters before, the carrier, the boxed
  fighter.
- The carrier is not a trainee (`ch24_trainees_below_floor`), and R1's head-count leaves it out.
- `restore_ch24_fighters`: in the lobby, after `E1-INSIDE` and before the guards, `pc_trip.swap_party_box` deposits the
  carrier and withdraws the boxed fighter. Then the party's non-egg `(PID, species)` set must EQUAL the recorded
  fighters, or it refuses by name.

## THE DRIVE — `--driver flybox`

- Fixture `post_moveset.ss1` (PINNED, md5 `36e4510e…`, asserted): EVER_GRANDE_CITY (18,6), HM02 in the bag, box empty.
  Party: Swellow 0B30A747 (the only Fly learner; does not know Fly), Zigzagoon 33CB74C3 L19, Mightyena 5C96EA9B,
  Sceptile 863B0917, Castform C978D14E, Wailord FA51ECF3.
- Injection (every case but `ordinary`): Swellow into box slot 0; the party = the other five + a created Machop L50
  (cannot learn Fly), 6/6.
- The make-room victim, computed BEFORE the run with increment A's rule: **Zigzagoon 33CB74C3** (dead weight).
- Recorded ACTIONS: `PCAction.deposit_pokemon_to_box` and `withdraw_pokemon_from_box`, by (PID, species).

## PREDICTIONS

| Case (`FB_CASE`) | Predicted |
|---|---|
| **swap** | `ensure_fly_learner`: PC actions **[deposit Zigzagoon, withdraw Swellow]**; back on EVER_GRANDE_CITY; `fly_teach=taught`; Swellow knows Fly; swap recorded (carrier Swellow, boxed Zigzagoon, fighters = the injected six). `restore_ch24_fighters`: PC actions **[deposit Swellow, withdraw Zigzagoon]**; `F-RESTORED`; the party equals the six fighters; Swellow boxed; standing in the lobby |
| **nofly** (`POKEBOT_R20_FAULT_NOFLYBOX=1`) | `fly_teach=no_learner`; **no PC action**; still on EVER_GRANDE_CITY; Swellow still boxed; nothing recorded |
| **wrongtile** (`POKEBOT_R20_FAULT_LOBBYSTAND=1`) | the lobby is entered and the withdraw aims at (10,2): no path (a guard stands there), so `withdraw_from_box` returns `error`; `fly_teach=no_learner`; Swellow still boxed; back on EVER_GRANDE_CITY; nothing recorded |
| **noswap** (`POKEBOT_R20_FAULT_NOSWAPBACK=1` on the restore) | as swap through the teach; then `restore_ch24_fighters` **refuses by name** ("RULING 21"), no restore PC action, and Swellow is still in the party |
| **ordinary** (no injection) | Swellow taught from the party; **no PC action**; nothing recorded; the restore is a no-op (`none_needed`) |
| **regression: `--driver hmpcfirst`** (default arm, `fortree_gym_wedge.ss1`) | still **PASS**: every PC walk now goes through `pc_stand_for`, and a normal centre must still resolve to (10,2) |

**Discriminators:** swap vs nofly and wrongtile use the same injected state; only a production arm differs. ordinary has
a party learner, so box-first must not fire.

## FALSIFIERS

- **swap's deposit is not Zigzagoon:** increment A's rule is not what make-room used. A RESULT; read the failing line.
- **wrongtile withdraws Swellow anyway:** the per-map stand tile is not what makes the lobby withdraw work.
- **noswap enters or passes:** the identity check is not live.
- **ordinary visits the lobby or records a swap:** box-first fires with a party learner, a regression.

## WHAT THIS DOES NOT SHOW

- §Ch24 end to end: the training with the carrier excluded (pure-gated only), R1's head-count (AST-gated), and the
  swap-back inside the real `prepare_and_open_the_league` flow. The driver calls the two production functions directly.
- A boxed Fly KNOWER (the no-teach branch) live; it is gated with stubs only.
- Frequency. One trajectory per arm.
