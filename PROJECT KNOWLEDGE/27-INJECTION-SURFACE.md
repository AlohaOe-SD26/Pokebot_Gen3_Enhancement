# 27 — THE INJECTION SURFACE: how the bot OBSERVES and ACTS on the game

> **Reference file.** The sensorimotor contract between this program and Pokémon Emerald.
>
> ‼ **This document exists for the SECOND north star** (`01-VISION-AND-DESIGN.md`): a future
> self-training AI agent needs to know *how state is observed and how inputs are applied* before it
> can learn anything. Code can be read; the **failure modes** cannot — and they are the reason this
> file is mostly about traps.
>
> Every API below was verified present in `sandbox-pokebot/modules/` on 2026-08-11. Every trap cites
> the incident that taught it.

---

# 1. THE FRAME CONTRACT — the unit everything is built on

The bot is a **generator driven one emulated frame at a time**.

```python
def some_step() -> Generator:
    context.emulator.press_button("A")   # queued for THIS frame
    yield                                # <- advance exactly ONE frame
```

* **`yield` == one frame.** Every wait, every loop bound, every budget in this project is counted
  in frames. 60 frames ≈ 1 second of game time.
* **A button press applies to the frame it is issued on.** It is not held unless you hold it.
* **`context.emulator.get_frame_count()`** is the absolute clock used in every log line (`f3232735`).

‼ **THE SINGLE MOST IMPORTANT CONSEQUENCE:** *game state can change between two of your yields, and
a state that exists for one frame can be missed entirely.* This is not theoretical — see §4.1.

---

# 2. OBSERVATION — what the bot can see

## 2.1 Game state
```python
from modules.memory import get_game_state, GameState
get_game_state() is GameState.OVERWORLD
```
`GameState` is an `IntEnum` (`memory.py:220`), so the numbers in raw logs decode as:

| n | state | n | state | n | state |
|---|---|---|---|---|---|
| 1 | `BAG_MENU` | 8 | `CHANGE_MAP` | 15 | `NAMING_SCREEN` |
| 2 | `CHOOSE_STARTER` | 9 | `TITLE_SCREEN` | 16 | `POKE_STORAGE` |
| 3 | `PARTY_MENU` | 10 | `MAIN_MENU` | 17 | `POKEMON_SUMMARY_SCREEN` |
| 4 | `BATTLE` | 11 | `GARBAGE_COLLECTION` | 18 | `UNKNOWN` |
| 5 | `BATTLE_STARTING` | 12 | `EVOLUTION` | 19 | `QUEST_LOG` |
| 6 | `BATTLE_ENDING` | 13 | `EGG_HATCH` | | |
| 7 | `OVERWORLD` | 14 | `WHITEOUT` | | |

‼ **`UNKNOWN` (18) is normal, not an error** — it is what screen transitions read as. A 2026-08-11
teach trace passes through `18` twice while the party menu opens.

‼‼ **`OVERWORLD` DOES NOT MEAN "THE MENUS ARE CLOSED" (KI-14).** The START MENU reads as
`OVERWORLD`. Menu-free means **`OVERWORLD` AND no menu task up AND the avatar controllable** — all
three. Getting this wrong left a bag open and wedged the next travel leg.

## 2.2 Flags and vars — the story clock
```python
from modules.memory import get_event_flag, get_event_var, _event_flags, _event_vars
get_event_flag("GROUDON_AWAKENED_MAGMA_HIDEOUT")   # bool
get_event_var("SLATEPORT_HARBOR_STATE")            # int
```
‼‼ **NAMES CARRY NO `FLAG_` / `VAR_` PREFIX.** The tables are keyed `SLATEPORT_HARBOR_STATE`, not
`VAR_SLATEPORT_HARBOR_STATE`.

‼‼ **AND BOTH READERS FAIL SILENTLY ON A BAD NAME:**
| reader | unknown name returns | why that is dangerous |
|---|---|---|
| `get_event_flag` | **`False`** | indistinguishable from "the flag is not set yet" |
| `get_event_var` | **`-1`** | compares `False` against every threshold, for ever |

**Always membership-test first**: `if name not in _event_vars: raise`. This cost a chapter gate
(a phantom flag name silently gated a segment, 2026-07-22) and a save capture (2026-08-11, a
`VAR_`-prefixed read returned `-1` in silence). `audit_flag_names.py` exists for this.

## 2.3 Position and control
```python
from modules.player import get_player_avatar, player_avatar_is_controllable
avatar = get_player_avatar()
avatar.local_coordinates          # (x, y) on the CURRENT map
avatar.map_group_and_number       # (group, number) tuple  <- IDENTITY
player_avatar_is_controllable()   # can we act at all?
```
‼‼ **REPORT MAP IDENTITY AS THE ENUM, NEVER THE DISPLAY LABEL.**
`MapRSE(tuple(avatar.map_group_and_number)).name` is identity. `map_name` is a *label*, and
`MAUVILLE_CITY_GYM`'s label is literally `"MAUVILLE CITY"` — which is how a GYM save was written
down as a CITY save (2026-08-09).
‼ `map_group_and_number` is a plain tuple, so `== MapRSE.X.value` is a valid identity test
(verified 2026-08-11 both directions on real saves).

## 2.4 Tasks — the menu/scene state machine
```python
from modules.tasks import get_tasks, get_global_script_context
{t.symbol for t in get_tasks()}    # e.g. {'Task_HandleChooseMonInput', 'ListMenuDummyTask'}
```
This is how the bot knows *which menu or cutscene step is live*. It is the richest observation
surface and the most trap-laden — see §4.

## 2.5 Party, storage, bag, battle
```python
from modules.pokemon_party import get_party, get_party_size
from modules.pokemon_storage import get_pokemon_storage      # the PC boxes
from modules.items import get_item_bag                       # .quantity_of(item)
from modules.battle_state import get_battle_state
```
`BattlePokemon` exposes `current_hp`, `total_hp`, `level`, `species`, `moves` (with `.pp`),
**`status_permanent`** (Sleep/Paralysis/Freeze/Burn/Poison) and **`status_temporary`**
(`Confused`, `Flinched`, `Wrapped`, `Rooted`, `EscapePrevention`, `Substitute`, …).

‼ **`status_temporary` mixes INCAPACITATING and non-incapacitating states.** `Foresight` and
`Wrapped` do not stop a mon acting; `Confused`, `Sleep`, `Flinched` do. Treating them as one bucket
diluted a measurement on 2026-08-11 (`probe_status_tax.py`).

## 2.6 Maps and paths
```python
from modules.map import get_map_data, get_map_data_for_current_position
from modules.map_path import calculate_path, PathFindingError
```
‼‼ **`calculate_path` READS THE ROM'S LAYOUT, NOT THE LIVE WORLD.** It cannot see:
* **metatile changes** — the Jagged Pass hideout door planned as *"2 waypoints"* while the game had
  it **walled shut** by a `setmetatile` only a coord trigger removes. That false YES cost three
  wrong answers about one door;
* **NPCs standing in doorways** — hours were spent debugging a pathfinder whose destination was
  blocked by three NPCs;
* **warps** — it refuses across unconnected maps by design (that FAIL means nothing).
⇒ **A static OK means "worth driving". It is never evidence.**

---

# 3. ACTION — what the bot can do

```python
context.emulator.press_button("A")     # A B L R Up Down Left Right Start Select
context.emulator.hold_button("Left")   # persists until released
context.emulator.release_button("Left")
```

Higher-level helpers (`modules/modes/util/`, `modules/menuing.py`):
`wait_for_n_frames`, `navigate_to`, `StartMenuNavigator`, `scroll_to_item_in_bag`,
`scroll_to_party_menu_index`, `wait_until_truly_controllable`, `wait_for_player_avatar_to_be_standing_still`.

‼ **`hold_button` LEAKS IF YOU ABANDON A HELPER EARLY.** `walk_one_tile` leaves the direction and
B held; release in a `finally`, or every later retry runs with a jammed D-pad (2026-08-10).

---

# 4. ‼‼ THE TRAPS — the part that cannot be recovered from the code

## 4.1 A task can exist for ONE FRAME
`Task_ReplaceMoveYesNo` displays the yes/no menu **and sets its own function to
`Task_HandleReplaceMoveYesNoInput` in the same frame** (decomp `src/party_menu.c`). Measured:
```
f3232735  tasks=['Task_ReplaceMoveYesNo']              <- the ONLY frame it is visible
f3232736  tasks=['Task_HandleReplaceMoveYesNoInput']   <- gone, and it never returns
```
**Rule: never key a detector on a `Task_XxxYesNo` DISPLAY task alone. Watch the
`Task_HandleXxxYesNoInput` handler too**, or you have a one-frame lottery. This one cost four rounds
of investigation (`#24-teachmsgstall`).

## 4.2 A task present on BOTH branches cannot choose between them
`Task_HandleChooseMonInput` stays up after the mon is chosen, so on a slow frame it "proved" the
instant-learn path on a mon with four moves (`#24-teachpathrace`). **An exit needs POSITIVE
evidence, not the absence of the other branch's marker.**

## 4.3 A flag set by a script is NOT the end of that script
`EventScript_ActivateStrength` sets `FLAG_SYS_USE_STRENGTH` and then keeps running (animation,
message, `releaseall`). Exiting the wait when the flag flips leaves the avatar `lockall`ed and every
later press does nothing. **Cost: two runs.** ⇒ **Grade on the flag; wait for CONTROL.**
The same shape is waiting in §Ch16: `VAR_SLATEPORT_HARBOR_STATE` is set *mid-script*.

## 4.4 Never blind-mash A at a live yes/no
Somewhere in Gen 3 there is a prompt where **A means "give up"** —
`Task_HandleStopLearningMoveYesNoInput` case 0 abandons the teach. A 900-frame A-mash found it.
**Mash only to advance TEXT; every yes/no needs a named branch.**

## 4.5 Confusion, sleep and flinch do NOT consume PP
A move can be **selected but never executed**, leaving PP frozen. ‼ A **miss still consumes PP**, so
frozen PP means "it never acted", not "it missed". Without the status field this is
indistinguishable from a bot bug — and it was misread as one until 2026-08-11.

## 4.6 Reads are cached per frame
Reading back live state **in the same frame you wrote it** returns the stale value. The heal fixture
logged `Mightyena 0/124` immediately after healing it. **Log the BEFORE→AFTER you wrote, never a
same-frame read-back.**

## 4.7 `.ss1` and `.sav` are different things
A `.ss1` is a **full machine snapshot** and DOES preserve battle callbacks and mid-script state
(measured 6 of 6). "X is runtime state so a save can't hold it" is true of `.sav` only — believing
it of `.ss1` cost three wedged probe runs.
‼ **And a `.ss1` replays IDENTICALLY.** A save that loses a frame-timing race loses it on *every*
replay. That is why one fight repeated five times is still **n = 1** (2026-08-11).

## 4.8 Object events are camera-loaded
An NPC "not present on the map" may simply be outside the loaded camera window (Briney at the dock,
2026-07-22). Absence of an object is not proof of absence.

---

# 5. WHAT A FUTURE AGENT SHOULD TAKE FROM THIS

1. **The observation surface is rich but every reader has a silent failure mode.** Membership-test
   names; prefer enums to labels; never trust a static planner over the live world.
2. **The action surface is one button per frame.** Everything hard is *timing*, not choice.
3. **The traps in §4 are the actual knowledge.** Each one cost hours-to-days and none is derivable
   from reading the code — they come from the game's behaviour.
4. **Faithfulness is a constraint on the ACTION side.** The bot may only do what a player could do
   with a controller. A state-write is a documented last-resort fallback that must reproduce
   vanilla's exact end state (`14-AGENT-PLAYBOOK.md`).

⇒ **The honest summary for a learning agent: the game is observable enough to play well, and the
difficulty is almost entirely in knowing WHEN a thing is true — not in knowing what to do about it.**
