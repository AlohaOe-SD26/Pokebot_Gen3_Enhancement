# Game Cheat Menu — design

Sandbox feature. **GAME cheats** (modify the running game via memory writes),
distinct from upstream's `cheats.yml` (bot-behaviour cheats). This is the
user's own game/ROM — full modification is intended. Every cheat is built on
the bot's own verified memory-write toolkit (`modules/debug_utilities.py`,
`modules/memory.py`), the same code the stock Debug menu uses.

## Safety model
- **Actions** (one-shot, on click) that rewrite the party/bag/money require
  the game to be in `GameState.OVERWORLD` — writing mid-battle/mid-menu can
  corrupt display or battle state. If not in the overworld, the action is
  refused with a message.
- **Toggles** (persistent) are re-applied by a `BotListener`; party/money
  toggles only act in the overworld; the wild-encounter overrides act only
  at battle start (mirroring the stock `ForceShinyEncounterListener`).
- Every cheat is fully exception-guarded — a failure logs to
  `logs/game_cheats.log` and returns a message; it can never crash the frame
  loop or half-write. One-shot actions cannot be "undone" except by playing
  on or restoring — the UI reminds the user to **back up first**.

## Implemented cheats

### Party actions (rebuild via `debug_create_pokemon` + `debug_write_party`)
Rebuilding through the bot's own valid-Pokémon generator (not raw byte pokes)
keeps the encrypted growth/misc substructs + checksum correct. Each rebuild
preserves species/nickname/IVs/EVs/nature/gender/moves/PV (and therefore
PV-derived traits: Unown letter, Spinda spots, Wurmple evolution) unless the
cheat changes them. (The `nickname=mon.nickname` pass-through is required —
without it `debug_create_pokemon` resets the name to the species default.)

| Cheat | Type | Mechanism | Verified |
|---|---|---|---|
| Heal party | action | rebuild, `current_hp=max`, `status=Healthy` | byte ✓ / in-game pending |
| Max level (100) | action | rebuild `level=100` (exp+stats auto-recomputed for L100) | byte ✓ / pending |
| Perfect IVs (31) | action | rebuild `ivs=31×6` | byte ✓ / pending |
| Max friendship (255) | action | rebuild `friendship=255` | byte ✓ / pending |

Eggs are left untouched by party rebuilds.

### Items / money
| Cheat | Type | Mechanism | Verified |
|---|---|---|---|
| Max money | action | `debug_give_max_coins_and_money()` (900,000 + 9,999 coins) | upstream ✓ |
| Give item pack | action | `debug_give_test_item_pack()` (balls/berries/TMs/key items) | upstream ✓ |
| 99× Rare Candy | action | bag rewrite via `debug_write_item_bag` | byte ✓ / pending |
| Max Poké Balls | action | fill Poké Ball pocket, bag rewrite | byte ✓ / pending |
| Infinite money | toggle | overworld frames: if money < 900k → set 900k | mechanism ✓ / pending |
| Set money = X (#31) | action | overworld-gated write of `pack_uint32(decrypt32(clamp(X,0..999999)))` to SaveBlock1 money offset (`0x490` RSE / `0x290` FRLG — same offset the verified `player.money` reader uses); exactly the 4-byte money field, coins `[+4:+6]` / registered-item `[+6:+8]` untouched | byte ✓ / pending |
| Lock money = X (#31) | toggle | overworld frames: re-write the clamped **locked** value each tick; takes precedence over Infinite money (both write money) | byte ✓ / pending |
| Auto-heal party | toggle | overworld frames: surgical `current_hp=max`, `status=0` per slot (HP/status live OUTSIDE the encrypted region — no re-encryption needed) | byte ✓ / pending |

### Encounters (the "change wild spawns" headline)
Mirrors the stock `ForceShinyEncounterListener`: on `Task_BattleStart`, if the
opponent is a **wild** mon (its OT id/secret id equal the player's), overwrite
`gEnemyParty` with a fabricated mon.
| Cheat | Type | Mechanism | Verified |
|---|---|---|---|
| Force wild species = X @ level L | toggle | `debug_create_pokemon(X, L)` → `write_symbol("gEnemyParty", …)` | mechanism ✓ / in-battle pending |
| Guaranteed shiny wild | toggle | rebuild opponent preserving all stats, `is_shiny=True` | mechanism ✓ (exact stock pattern) / pending |

## Considered but NOT implemented (honest)
- **No / guaranteed wild encounters** — needs hooking the encounter-RNG/step
  logic, not a single memory write. Deferred.
- **PP restore in Heal** — PP lives in the encrypted growth substruct; a clean
  restore needs full re-encryption per move and risks pp-up loss. Heal covers
  HP + status only (documented).
- **Fast egg hatch / infinite Safari balls / always-bite** — the stock Debug
  menu already ships an InfiniteSafariZone listener; the rest are edge/mode
  specific. Deferred to avoid duplicating or half-doing them.

## Verification honesty
"byte ✓" = the bytes written were decoded back through the bot's own reader and
asserted correct. "in-game pending" = the actual in-game effect (party really at
L100, wild really replaced) needs the user's real save — the title-screen test
save has no party/bag to round-trip. Nothing here claims an unproven in-game
result.

Adversarial verification pass (2026-07-18): the party-rebuild actions are now
byte-verified through the *real* CheatManager code (capturing `debug_write_party`)
for nickname/PV(form)/IV/friendship/level survival + egg pass-through; the
auto-heal surgical write is byte-verified live against `gPlayerParty` (HP
restored, status cleared, checksum still valid, egg untouched); negative controls
confirm a corrupted mon reads as invalid; edge species (Unown/Deoxys/Mew/Wurmple/
held-item/level-1/level-100) fabricate valid; the wild override is confirmed to
skip trainer battles and clone/force only wild ones; listener throttle (1 write /
15 frames) and battle-start single-fire are unit-checked. Batteries: 32 headless +
15 live + 77 adversarial, all green.

Adversarial verification pass (2026-07-19, #30–#32 batch): the #31 adjustable
money cheat is byte-verified through the *real* `CheatManager` code by routing
its `get_save_block`/`write_to_save_block`/`decrypt32` calls through an in-memory
save block with a real non-zero XOR key — the money field round-trips exactly
for 0/1/12345/999999, over-range and negative inputs clamp to `[0, 999999]` on
BOTH `set_money` and lock, the write is exactly 4 bytes wide (coins +
registered-item neighbour bytes proven byte-identical), lock re-applies the
LOCKED value and beats Infinite money, off/overworld gating stops writes, and
malformed input / raising primitives are fully swallowed (56 checks green). The
#30/#32 GUI is adversarially checked headless (destroyed-widget focus, tooltip
destroy-while-shown, out-of-range/negative/empty tooltip index, focus-registry
churn, all seven GAME-MENU buttons proven to be the real stock callbacks — 28
checks green) and confirmed live (real ROM): focus ring renders on the first
target, GAME MENU works from the Play tab, handheld hides the Tk menu bar,
overworld input is suppressed while GUI-nav is active, and window close tears
down cleanly (rc=0, save state written). No code bugs found in this pass.
