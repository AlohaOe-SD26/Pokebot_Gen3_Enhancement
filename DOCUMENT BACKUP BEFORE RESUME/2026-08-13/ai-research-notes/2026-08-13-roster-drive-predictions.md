# PRE-REGISTERED PREDICTIONS — the first live drive of `reorder_party()` (2026-08-13)

> Written **BEFORE** the run, per `14-AGENT-PLAYBOOK.md` / the §Ch19 method (write the predicted
> failure down first — 3/3 held there, and two traps got designed out instead of debugged).
> Derived by DIFFING `RotatePokemon` against the one party-menu path this project has actually
> proven in production, `change_lead_party_pokemon`. Nothing here is recalled; every claim carries
> a file:line.

## The structural finding the diff produced

`change_lead_party_pokemon` (`modules/modes/util/higher_level_actions.py:287-306`) — **proven, runs
every training round** — does this between opening the Start menu and touching the cursor:

```
yield from StartMenuNavigator("POKEMON").step()
yield from wait_until_task_is_active(party_menu_task)   # "Task_HandleChooseMonInput"
yield
yield from wait_for_fade_to_finish()
yield from PokemonPartyMenuNavigator(0, "", cursor_option_switch).step()
```

`RotatePokemon` (`modules/menuing.py:1033-1042`) does this:

```
case "open_party_menu":       self.navigator = StartMenuNavigator("POKEMON").step()
case "select_first_pokemon":  self.navigator = PokemonPartyMenuNavigator(idx=..., mode="select_switch").step()
```

‼ **All three synchronisation steps are missing** — no `wait_until_task_is_active`, no bare `yield`,
no `wait_for_fade_to_finish`. The very next thing that happens is `navigate_to_mon`
(`menuing.py:520-527`) *reading* `get_party_menu_cursor_pos`. That is precisely the stale-cursor
read `modules/story/roster.py`'s docstring predicted, and it is now confirmed by construction
rather than by suspicion.

It also differs in kind: the proven path drives the cursor with **explicit presses separated by
`wait_for_n_frames(4)`**; `RotatePokemon` drives it with **read-compare-press loops that have no
inter-press settle at all**.

## Ranked predictions

| # | Prediction | Where | What I expect to SEE |
|---|---|---|---|
| **P1** | The cursor is read before the party menu has initialised, `slot_id` comes back `-1`, and `get_party_menu_cursor_pos` **calls `context.set_manual_mode()` and still returns** | `menu_parsers.py:164-166`, reached from `menuing.py:523/525` | `reorder_party` raises `BotModeError("...dropped the bot to MANUAL mid-swap...")` (`roster.py:198-202`). **Phase 1 fails on swap 1.** |
| **P2** | `get_index_from_option` returns `None` implicitly when the SWITCH submenu is not parsed yet; `select_desired_option` then evaluates `None < 0` | `menuing.py:370-386` | `TypeError` caught by `roster.py:189` → `swap attempt failed (TypeError(...))`, retried up to 3× |
| **P3** | ‼ **THE INVISIBLE ONE.** `navigate_to_mon` computes its scroll `direction` **once, before the loop**, from a possibly-stale read, then presses only that direction. A wrong initial read swaps the **wrong pair** while every navigator "completes" | `menuing.py:520-527` | `finished=True` **and** the PID check fails → `swap did not land (navigator completed)`. This is why `roster.py` verifies by PID and keeps `finished` as a diagnostic; a slot-based check would have called this a PASS |
| **P4** | `select_replacement`'s two `while` loops are unbounded and have no settle between presses; if the SWITCH submenu never opened they press against the CHOOSE menu instead | `menuing.py:1044-1056` | `_yield_bounded` caps at `SWAP_TIMEOUT_FRAMES=3000` → `navigator timed out`. **Not** a hang — the bound holds |
| **P5** | `PartyMenuExit.wait_for_start_menu` raises (this fork's freeze fix) if the start menu never reappears | `menuing.py:833-843` | `BotModeError("PartyMenuExit: the start menu never reappeared...")`, caught and retried. Upstream would have **frozen the process** here |
| **P6** | `wait_for_init`'s give-up sets Manual and **keeps looping** (it does yield, so the frame bound still applies) | `menuing.py:361-368` | Bound fires, then `roster.py`'s Manual check raises. Same observable as P1 |

## What would make the run a genuine PASS

* All four phases land, **verified by PID** — never by slot.
* `saw_j_nonzero=True`. A run that only ever emitted `destination == 0` swaps has re-proven
  `change_lead_party_pokemon`'s shape and proven nothing new; the driver asserts the plan contains
  a `destination != 0` swap **before** spending the drive.
* `can_continue=True`, meaning a real `calculate_path` off the end tile **and an actual position
  change** — not "controllable". §Ch15 ended four floors underground, §Ch18 on an eleven-tile
  island and §Ch19 in a living room, all three controllable.

## What would make it a FAIL I must not launder

If P1/P2/P4/P6 fire, the honest report is **"`RotatePokemon` is not drivable as written"**, and the
fix is to give it the synchronisation the proven path already has — **not** to widen a timeout.
Recording that here so the finding cannot be re-described after the fact.

---

# 🔻 OUTCOME — adjudicated against the run, 2026-08-13. **0 of 6 predictions fired.**

Driven three times from `saves/post_dive.ss1` (`--driver roster`). Runs 2 and 3 are the A/B.

| # | Predicted | Fired? | Evidence |
|---|---|---|---|
| P1 | `slot_id == -1` → silent Manual | **NO** | `slot_id` never read `-1` in 157 traced transitions; zero Manual drops |
| P2 | `None < 0` TypeError in the submenu | **NO** | no exception logged on any of 6 swaps |
| P3 | stale `direction` → **wrong pair swapped** | **NO** | all 6 swaps landed the PID check **first attempt**; zero `swap did not land` lines |
| P4 | `select_replacement` loops time out | **NO** | longest phase 690 frames vs the 3,000-frame bound |
| P5 | `PartyMenuExit` raises | **NO** | never reached its 60-frame give-up |
| P6 | `wait_for_init` give-up | **NO** | never reached |

**`RotatePokemon` IS drivable as written**, including the never-before-driven `destination != 0`
case: `Story: roster — swapping party slots 2 <-> 1` ran twice and landed both times.

⚠ **P3's MECHANISM is real even though it did not bite.** `gPartyMenu.slot_id` is **not reset
between menu sessions**: the tracer read `slot_id=2` at PHASE1 f1, on the overworld, before the
Start menu had even opened — a residue of whatever last used the party menu. `navigate_to_mon`
(`menuing.py:520-524`) computes its scroll direction from exactly that global. It happened to be
re-read live (`0`) by the time the loop ran. **This is luck, not safety**, and it is the thing to
re-check if a future roster drive ever mis-swaps.

## ‼ THE DEFECT THAT WAS REAL WAS PREDICTED BY NOBODY

Neither this list nor the independent adversarial pre-drive review found it. Both hunted the
**KI-38 hang family** — which is where every doc in this project points — and neither asked the
different question: *what state does the function LEAVE BEHIND?*

`reorder_party()` returned `True` with the avatar **still uncontrollable**. The next
`navigate_to` raised *"The player avatar is currently not controllable. Cannot navigate."*

And it is invisible to every cheap check: at that instant `context.bot_mode` was **not** Manual,
`get_game_state()` was already **OVERWORLD**, and `parse_start_menu()["open"]` was already
**False**. The trace shows why — `Task_ShowStartMenu` was still live at f660 of a 662-frame call.
The party menu's last act is to re-show the Start menu, and control returns some frames later.

**A/B proof** (identical save, identical driver, only `roster.py` differs):

| phase | ARM A (no settle) | ARM B (settle) | Δ |
|---|---|---|---|
| 1 — `j != 0` | 445 | 476 | +31 |
| 2 — Regi shape | 227 | 258 | +31 |
| **3 — already correct** | **0** | **0** | **0 ← the guard correctly did NOT fire** |
| 4 — restore | 662 | 690 | +28 |
| `moved` | **False** (raised) | **True** `(19,11)→(21,12)` | |
| ACCEPTANCE | **FAIL** | **PASS** | |

Phase 3 is the control arm: it proves the settle is skipped when no menu was opened, so the common
"already in the right order" path stays free.

## 📄 RAW TRANSCRIPTS — verbatim, unedited (per-frame trace lines elided, nothing else)

‼ `tools/story-dev/.gitignore:2` ignores `*.log` **on purpose**, so raw run logs are not
committable in this project. Evidence is transcribed here instead. These are the literal
`[roster]` lines as printed.

**ALL FOUR RUNS, DISCLOSED** — including the one that proved nothing:

| profile | tree | outcome |
|---|---|---|
| `roster1` | fixed driver, **broken import** | ‼ **NO PHASES RAN.** `ImportError: cannot import name 'GameState' from 'modules.game'` at f0. See the separate finding below |
| `roster2` | **ARM A** — `roster.py` unfixed | `ACCEPTANCE: FAIL`, `moved=False` |
| `roster3` | **ARM B** — `roster.py` fixed | `ACCEPTANCE: PASS`, `moved=True` |
| `roster4` | ARM B + the new PHASE 6 measurement | `ACCEPTANCE: PASS`, plus the `_rotate_lead_safely` margin number |

### ARM A — `roster2`, before the fix

```
[roster] start map=(0, 6) at=(19, 11) party=['SceptileL49#2252015895', 'ZigzagoonL15#868971715', 'SwellowL40#187737927', 'SkittyL17#1556928702', 'MightyenaL44#1553394331', 'CastformL36#3380138318']
[roster] PHASE1 target=[187737927, 2252015895] PLANNED-SWAPS=[(0, 2), (1, 2)] (destination,source) -> RotatePokemon(source, destination)
[roster] PHASE1 finished after 445 frames, 45 state transitions, returned True
[roster] PHASE1 returned=True landed=True party=[187737927, 2252015895, 868971715, 1556928702, 1553394331, 3380138318] frames=445
[roster] PHASE2 (REGI shape) target=[3380138318, 2252015895, 868971715, 1556928702, 1553394331, 187737927] PLANNED-SWAPS=[(0, 5)]
[roster] PHASE2 finished after 227 frames, 27 state transitions, returned True
[roster] PHASE2 returned=True landed=True first=3380138318 last=187737927 party=[3380138318, 2252015895, 868971715, 1556928702, 1553394331, 187737927] frames=227
[roster] PHASE3 finished after 0 frames, 0 state transitions, returned True
[roster] PHASE3 (idempotence) returned=True unchanged=True frames=0 idempotent=True
[roster] PHASE4 finished after 662 frames, 70 state transitions, returned True
[roster] PHASE4 (restore) returned=True restored=True frames=662
[roster] CAN-CONTINUE navigate to (21, 12) raised BotModeError: The player avatar is currently not controllable. Cannot navigate.
[roster] CAN-CONTINUE manual=False state=OVERWORLD start_menu_open=False path_ok=True path_len=15 moved=False (19, 11)->(19, 11)
[roster] RESULT phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=False manual=False detail={'phase1': (True, True, 445), 'phase2': (True, True, 227), 'phase3': (True, True, 0), 'phase4': (True, True, 662)}
[roster] ACCEPTANCE: FAIL
```

### ARM B — `roster4`, after the fix (identical save, identical driver)

```
[roster] start map=(0, 6) at=(19, 11) party=['SceptileL49#2252015895', 'ZigzagoonL15#868971715', 'SwellowL40#187737927', 'SkittyL17#1556928702', 'MightyenaL44#1553394331', 'CastformL36#3380138318']
[roster] PHASE1 target=[187737927, 2252015895] PLANNED-SWAPS=[(0, 2), (1, 2)] (destination,source) -> RotatePokemon(source, destination)
[roster] PHASE1 finished after 476 frames, 46 state transitions, returned True
[roster] PHASE1 returned=True landed=True party=[187737927, 2252015895, 868971715, 1556928702, 1553394331, 3380138318] frames=476
[roster] PHASE2 (REGI shape) target=[3380138318, 2252015895, 868971715, 1556928702, 1553394331, 187737927] PLANNED-SWAPS=[(0, 5)]
[roster] PHASE2 finished after 258 frames, 28 state transitions, returned True
[roster] PHASE2 returned=True landed=True first=3380138318 last=187737927 party=[3380138318, 2252015895, 868971715, 1556928702, 1553394331, 187737927] frames=258
[roster] PHASE3 finished after 0 frames, 0 state transitions, returned True
[roster] PHASE3 (idempotence) returned=True unchanged=True frames=0 idempotent=True
[roster] PHASE4 finished after 690 frames, 67 state transitions, returned True
[roster] PHASE4 (restore) returned=True restored=True frames=690
[roster] CAN-CONTINUE manual=False state=OVERWORLD start_menu_open=False path_ok=True path_len=15 moved=True (19, 11)->(21, 12)
[roster] PHASE6 (_rotate_lead_safely MARGIN, production) controllable_on_return=True party [2252015895, 868971715, 187737927, 1556928702, 1553394331, 3380138318] -> [187737927, 868971715, 2252015895, 1556928702, 1553394331, 3380138318]
[roster] RESULT phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True manual=False rotate_lead_controllable_on_return=True rotate_lead_measured=True detail={'phase1': (True, True, 476), 'phase2': (True, True, 258), 'phase3': (True, True, 0), 'phase4': (True, True, 690)}
[roster] ACCEPTANCE: PASS
```

Six swaps ran across the phases and **every one landed its PID check on the first attempt** —
zero `swap did not land` lines, zero Manual drops, zero KI-38 give-ups. The console shows
`Story: roster — swapping party slots 2 <-> 1` twice, which is the `destination != 0` case.

## ‼ A SEPARATE FINDING FROM RUN 1: THE HARNESS REPORTS AN `ImportError` AS "HANG CONFIRMED"

`roster1` died at **f0** on `ImportError: cannot import name 'GameState' from 'modules.game'`
(it lives in `modules.memory`). The harness caught it, set Manual, cleared the controller stack —
and then printed **twenty thousand frames of `NO-PROGRESS` heartbeats** before concluding
`HANG CONFIRMED (20000 frames no progress)`. The real cause was one line in the traceback at the
very top of a ~40-line log.

Two things follow:

1. **`pyflakes` cannot catch a wrong-module import.** It flagged the line only as
   *"redefinition of unused 'GameState'"* — a style note. `repro_undefined_names.py` inherits that
   blind spot. ⇒ New cheap gate used before every later run in this session: parse the driver's
   `ImportFrom` nodes with `ast`, `importlib.import_module` each module and `hasattr` each name.
   It checked 20 symbols in under a second and would have caught this before a 20,000-frame run.
2. **"HANG CONFIRMED" is not a diagnosis.** It is what this harness prints for *any* condition
   that empties the controller stack, including an immediate crash. Read the head of the log,
   not the tail.

## 📌 `_rotate_lead_safely` HAS THE SAME SHAPE — MEASURED, **n = 1**, NOT FIXED

Found by the adversarial review of *this* fix. `early_game.py:1629-1630`: the **success** path
returns with no settle while the **failure** path at `:1637` does settle. Its callers walk
immediately (`do_rustboro_gym:1838`; every `_lead_best_matchup` site in `story_mode.py`), and it
runs **every training round** — the hottest path in the bot.

**Measured (PHASE 6):** `controllable_on_return=True`. The margin held.

⚠ **n = 1.** One observation on one save is not a rate — this project has made exactly that error
before (a 64.3% figure from n=2 that a real batch cut to 32.6%). So: **filed as KI-70, not fixed.**
An unconditional settle would cost ~30 frames (`stable_frames`) per rotation on the hottest path
in the bot, to fix something that has never been observed failing. The explanation for why it
survives is a **margin, not a guarantee**: `change_lead_party_pokemon` ends with
`wait_for_task_to_start_and_finish` + `wait_for_n_frames(10)`, whereas `RotatePokemon`/
`PartyMenuExit` exits on the strictly weaker *"OVERWORLD and start menu closed"*.

## Two lessons worth carrying forward

1. **Pre-registering predictions is still worth it at 0/6.** The list is what let me say
   "`RotatePokemon` is drivable" as a *measurement* instead of a relieved guess, and it is what
   isolated P3's mechanism as live-but-unfired rather than absent.
2. **Both prediction passes inherited the same blind spot from the documentation.** The docs are
   dense on hangs, so both passes searched for hangs. ⇒ Ask separately, every time:
   *what state does this hand back to its caller?* Added to `08-MISTAKES.md` as a prevention rule.
