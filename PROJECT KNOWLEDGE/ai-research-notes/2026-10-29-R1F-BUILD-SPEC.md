> **Filed 2026-10-29** by the orchestrating session, VERBATIM below this box, from the session scratch `s53/r1f/SPEC.md` (sha256 `ac919461d97fe44e`). R1 + R2's follow-up (`04` queue item 4; `06` 2026-10-29 "R1 + R2 BUILT", its "Known limits"). Made by the workflow `r1f-spec` (6.54 Mtok input-equivalent, `cost-ledger.jsonl`): a designer; two adversarial critics (code and host truth; proof, rulings and person-fairness: 16 findings, 2 MAJOR); a reviser that checked each finding before fixing or rebutting it (its section 11); and a cold-start check (could it start with no human input: YES; its one MAJOR gap is ruling 1 below). Its section 10 asks the user one question (a refused reset combination: the game over for good, or a continue allowed?); the build proceeds fail-closed meanwhile.
> **The orchestrator's rulings (they bind the build, workflow `r1f-build`, and amend the spec where they differ):** (1) CHAIN, CHAIN-OLD and CHAIN-R1-OLD are built on K-SILENT's frozen set, NOT K-INSIDE's: on K-INSIDE's cart child B's own first save rewrites some sectors byte-identical to the torn S2's (same counter, same slot, unchanged data), so SaveWatch's rule (a completed sector differs from the flash before the write) would never see its e4; K-SILENT keeps S2's line as the newest save line while the cart loads S1, so mutant CH1 still discriminates. (2) CH1's edit is anchored at `game_memory.py:734` (the parent becomes the newest save line's id). (3) The parent makes the CHAIN arms' known-maps set from the K-SILENT row's child-A maps with frame <= S1.e3; child B's first save is S3 by id. (4) D2 is built fail-closed until the user answers. (5) The R1 + R2 build's orchestrator rulings stand (`06` 2026-10-29). (6) test_host and test_kb2 cannot run in a worktree (but see 9). (7) Live steps start only when no `run_regression.py` runs. (8) After the build's first STOP at step 3(b) (the default brain never raises): the `reset_refusal` harness's case (3) and its CONTROL (b) use the existing fault switch `AI_PLAYER_FAULT_RAISE=1` (the brain raises after 30 steps), not the watcher brain, whose error comes from what the fake emulator lacks. (9) `test_host` honours `AI_PLAYER_TEST_SUPPORT_ROOT` for its build root, as `test_check_purity` does, and its harness passes that one variable through, so the harness and its mutants run from revert copies and from a worktree against the main checkout's `sandbox-pokebot`, read only, with a CONTROL. (10) The builder's two extra purity plants (an imported exit-class alias; a break or continue in the else of a loop nested in a finally) are accepted.

# R1 + R2 FOLLOW-UP BUILD SPEC: the review's NITs, the verification's V2 findings, and two live arms (2026-10-29, revised)

> Backlog R1 + R2's follow-up, `04-HANDOFF` NEXT ACTIONS item 4; `06` 2026-10-29 "R1 + R2 BUILT", its "Known limits"
> bullet. Built on HEAD `f4412116`; `67c73a0f` is the tree before R1 + R2. Every `file:line` below was read at `f4412116`
> (the main checkout's working tree equals HEAD for every code file; only evidence files differ). Every finding was
> re-verified against that code before its fix was designed. Probes ran on COPIES under the spec author's scratch
> (`s53/r1f/`; the reviser's re-runs in `s53/r1f/mine/`, on `s53/r1f/rvcode/tree`, which equals HEAD's files apart from
> line endings, checked with `diff --strip-trailing-cr`), never in the main checkout. This revision answers two adversarial
> lenses (section 11).

## 0. Summary

Ten parts, one item. The AI's play is unchanged except one rule (part 6: a save no longer resets the curiosity row).

1. **N-1 (purity, ruling 52).** The play loop's exit rule also refuses `GeneratorExit`, `BaseException`,
   `BaseExceptionGroup`, a bare `except:`, a `return`/`break`/`continue`/`yield`/`yield from`/`await` directly in a
   `finally`, a `def __exit__`/`__aexit__`, and the names `ExitStack`/`AsyncExitStack`. A START/SELECT press the
   controller refuses now LATCHES the controller: nothing more is ever pressed, and the HOST ends the run on its next frame
   (or at once, if the brain returns or raises first). The verdict reason is `reset-refused` (exit 9), which the launcher
   classes NOT CLEAN, so no continue is allowed. The controller's held-button set becomes private, so the brain cannot
   empty it to slip a combination past the check.
2. **N-2 (fairness RULE C).** The play time is also caught when it is read as the constant key `'play_time'` (a
   subscript, a `.get`, a match-mapping key, a named constant), through a match-class keyword `play_time=`, through a
   whole-object copy (`asdict`, `astuple`), and through ANY class pattern with positional sub-patterns in deciding code
   (it reads fields by position through `__match_args__`; measured: no class pattern exists anywhere in the AI code).
   `vars(...)` and a non-constant `getattr` are ALREADY refused by the purity gate's rule (d) (measured), so nothing is
   built for them. The gate's docstring and a test record the two-gate cover.
3. **N-4 (memory file).** `read_book` refuses a MIDDLE line holding any non-ASCII character (every line is written with
   `ensure_ascii=True`, so such a character means a corrupted byte). A torn LAST line stays ignored (D6). The decoding
   stays total (`errors="replace"`), so a bad byte can never raise past the `MemoryFileError` contract.
4. **V2-1 + V2-2 (`live_r1` headline).** The caveat counts the midpoint arm's PASSES and names the failing seeds. One
   function, `verdict_line`, builds the verdict line; a LANE unit test and a revert mutant pin it. `verdict.json`
   carries the same line.
5. **V2-5 (the look-through).** Each look-through is COUNTED and TOLD (`(looked through N continues that stopped ...;
   the newest: ...)`) and exposed as `ContinueCheck.looked_through`. **No cap** (decision D5).
6. **V2-6.** A save is TRANSPARENT to the AI's curiosity row and to the grader's curiosity and aside streaks, the way
   `intent_mix` already treats it (spec T4).
7. **R-EXCEPT audit.** R1 + R2 added 28 handlers (11 AI side, 17 test side), and each was read. None in a play path catches
   an abort-class exception, and no `except ... as name` is read after its handler. There is ONE real defect, in the
   launcher (not a play path): `read_launches` reads `launches.jsonl` inside a `try` that catches only
   `FileNotFoundError`. So a non-UTF-8 byte escapes as a `UnicodeDecodeError` past `memory_check` and past `cmd_run`'s
   handler: the user gets a traceback, not the refusal sentence. It fails closed (nothing is changed), and it is fixed here.
8. **N-3 live: arm CHAIN, built on K-INSIDE's frozen set** (the cart holds S1, and the memory file also holds S2's line,
   the abandoned branch, as its NEWEST save line). Child B continues S1, plays on to its own save S3 and is killed after it
   stands on a map new since that save. Child C continues AGAIN and must arrive at S3 with its memory as of S3. The OLD arms
   are CHAIN-OLD (new mutant CH1: a continued writer chains to the NEWEST save line) and CHAIN-R1-OLD (mutant FX1: "C3 can
   fail").
9. **R-2 live: arm R2-RETRY** (and R2-RETRY-OLD on mutant FX3). A continue run through the REAL launcher stops on its
   arrival bound (a test-side COPY with `ARRIVAL_BUDGET` shrunk). The next continue, judged by the real launcher's
   `memory_check`, is allowed (it looks through the stopped session) and arrives at S2. On FX3 it is refused.
10. **The whole `live_r1` arm set is re-run on the final tree** with the new arms. Seeds: development 5501-5506,
    held-out 5551-5554 (registered first), independent re-run 5561-5564, fix round 5571-5574, verification after a fix
    round 5581-5584.

## 1. What and why (each part traced to the finding that asks for it)

### 1.1 N-1: verified TRUE (both halves)

- **The gate.** `gates/check_purity.py:179` `PLAY_LOOP_EXIT_NAMES = frozenset({"exit", "quit", "SystemExit",
  "KeyboardInterrupt"})`, judged in `visit_Name` (`:1171-1176`, Load context, `in_play_loop`). Plants on a copy
  (`s53/r1f/probe_gates.out`): `raise GeneratorExit` (brain/), `except BaseException:` (brain/), a bare `except:`
  (skills/), `except (ValueError, BaseException):` (mode.py) and `except* BaseException:` (hands/) **all PASS the gate**.
  `raise SystemExit` fails it (rule b), `import builtins` fails rule (a), and `Exception.__base__` fails rule (d).
  Two more forms also PASS the HEAD gate (`s53/r1f/mine/probe_plants_all.out`, re-run by the reviser):
  `contextlib.ExitStack()` with `stack.push(lambda *exc: True)` in brain/, and `yield from controls.wait(1)` inside a
  `finally` in skills/. `contextlib` is open to every file (`check_purity.py:418`). Pure-Python probes
  (`s53/r1f/rvcode/probe_swallow.py`, `s53/r1f/rev_proof/probe_yield_finally.py`, Python 3.12.4, re-run) show what they
  do to an exit raised inside a press: the ExitStack swallows a `SystemExit(9)` completely, and a yield in a `finally`
  hands the driver one ordinary frame after the exit began (CONTROL, the same code with no yield: 0 frames).
- **What `raise GeneratorExit` does.** `host/session.py:333-335` turns it into `lifecycle.note_abandoned()`. The guard
  then ends the run `abandoned` (`:293-294`), and `host/launcher.py:260` `_INVOLUNTARY` allows that end to continue.
- **The refused press.** `host/controller.py:69-74` `_check_together` raises `ControllerError` (a `ValueError`, `:46`).
  Left uncaught, `host/session.py:336-337` makes it a `crash` (`host/lifecycle.py:191-196`), which is INVOLUNTARY, so the
  reset the controller blocked still gets its reload at the next `--continue`. If the brain catches it (`except Exception`
  or `except ValueError`), the run plays on with no record at all.
- **The check's own input is writable.** `host/controller.py:67` `self.held: set[str] = set()` is a public mutable set,
  and `_check_together` computes `down = self.held | {button}` (`:71`). A brain-side plant that advances
  `controls.hold("A", 10)` once, calls `controls.held.clear()` and then taps Start PASSES the HEAD purity and fairness
  gates (`probe_plants_all.out`), so the check would see `{Start}`. The POSITIVE CONTROL `controls._held = set()` FAILS
  purity rule (d) (`s53/r1f/mine/probe_plants_pc.out`), which is why a private attribute closes the route.
- **Existing uses in the play loop** (`s53/r1f/scan_exit_forms.out`, all 30 `PLAY_LOOP_PARTS` files, plus the reviser's
  `s53/r1f/mine/scan_forms.out`): ZERO of a bare `except:`, `GeneratorExit`, `BaseException`, `BaseExceptionGroup`, a
  `return`/`break`/`continue`/`yield`/`yield from`/`await` in a `finally`, a `def __exit__`/`__aexit__`, `ExitStack`,
  `suppress`, or any class pattern. Outside `host/controller.py` itself, nothing in the AI code reads `.held` (the tests
  `test_host.py:825` and `:834` compare it with `set()`, and a frozenset equals that). The play loop's only handlers are
  `mode.py:444` (`MemoryFileError`), `mode.py:1136` and `:1348` (`StopIteration`), `game_memory.py:641`
  (`FileNotFoundError`), and `:651` and `:669` (`ValueError`). So no new refused form breaks anything in the real package.
- **Why the extra forms** (beyond the review's two): each one discards or holds back an exception in flight without
  naming it. A `return` in a `finally` silently drops the exception being raised (Python 3.12 allows it; PEP 765
  deprecates it in 3.14). A `yield` in a `finally` suspends it and gives the caller a frame. An `__exit__` that returns
  True, or an `ExitStack` callback that does, swallows whatever passes through its `with`. `BaseExceptionGroup` catches a
  group that may wrap an exit.

### 1.2 N-2: verified PARTLY (two of the review's routes are already closed; one more route found)

- `gates/check_fairness.py:393-397` fires on `.play_time` (an attribute not of `self`/`cls`) and on
  `getattr/hasattr(x, "play_time")` with that constant. Plants (`probe_gates.out`), against the fairness gate and the
  purity gate each:
  - a subscript `memory.last_save['play_time']`: passes BOTH;
  - `asdict(look.progress)[...]`, `astuple(look.progress)[-1]`: pass BOTH;
  - `memory.last_save.get('play_time')`: passes BOTH;
  - `match look.progress: case object(play_time=t)`: passes BOTH (as does `case Progress(play_time=t)`,
    `probe_plants_all.out`);
  - `match line: case {'play_time': t}`: passes BOTH;
  - **`case Progress(_, _, _, _, _, _, _, t)`** (positional, through the dataclass's default `__match_args__`;
    `eyes/observation.py:248-264`, `play_time` is the 8th field): passes BOTH (`probe_plants_all.out`). The same route
    reads `.flags` and `.marks` past RULE A;
  - `vars(look.progress)`: passes fairness, **FAILS purity rule (d)** (`check_purity.py:76-77`, `REFLECTION_NAMES`);
  - `FIELD = 'play_time'; getattr(x, FIELD)`: passes fairness, **FAILS purity rule (d)** ("getattr ... other than as
    `getattr(obj, 'constant name')`");
  - `getattr(look.progress, 'play_time')` (a direct constant) **FAILS fairness RULE C** today. The task text's "a getattr
    with a constant name ... passes it" is WRONG for the direct constant. It holds only through a named constant, which
    purity already refuses.
  - POSITIVE CONTROL of the reviser's harness: `look.progress.play_time` in a new brain/ file FAILS RULE C
    (`probe_plants_pc.out`).
- The launcher runs the PURITY gate before every launch (`host/launcher.py` `run_gate`), and the fairness gate runs in
  the lane (`run_regression.py` QUICK). So `vars` and the named-constant `getattr` are closed for any launched package.
  Nothing is built for them: RULE C's docstring says so, and a test pins the two-gate cover.
- Risk, as the review said, is low (the stamp in `last_save` is a past value, not the live clock). But D18 says "a read
  anywhere else in the deciding code fails the gate", and today five forms pass.

### 1.3 N-4: verified TRUE

`game_memory.py:639` opens the file with `errors="replace"`. Probe on a copy (`s53/r1f/probe_readbook.out`): a 3-line
file whose MIDDLE line has one byte inside a string made `0xFF` reads as `READ, 3 lines, session.started='�'`. The
content changed and the file was accepted. The CONTROL file reads `'x'`. A bad byte in a torn LAST line is ignored, as
D6 says.

### 1.4 V2-1 and V2-2: verified TRUE

`gates/live_r1.py:1488-1496` `between_caveat` counts `counted` only. `:1530` prints the verdict line inline in
`cmd_verdict`, and `:1526-1528` writes `verdict.json` with the bare `verdict`. The selftest case `:1742-1746` calls
`between_caveat()` directly. No `test_*.py`, `revert_*.py`, `run_regression.py` or `run_units.py` names `live_r1` (grep:
no file). `live_r1` imports offline (`py -3.12 -c "import ai_player.gates.live_r1"` run from the copy's root: OK; with
`-I` it fails with `ModuleNotFoundError`, because `-I` drops the current directory), so a lane unit test can pin it.

### 1.5 V2-5: verified TRUE

`host/launcher.py:350-356`: the loop returns the earlier session's `words` unchanged. Probe
(`s53/r1f/probe_launches.out`): 1, 5 and 50 identical arrival-timeout stops each give `('KILLED', 'harness session 1 has
no end line: it was killed', True)`, which says nothing of the stops.

### 1.6 V2-6: verified TRUE

`brain/goals.py:1068-1069` resets `curious_row` for any goal not in `CURIOSITY_KINDS` (`:282`), and `mode.py:930` calls
`after_goal` for a save goal too. `gates/rate_step5.py:1527` ends a curiosity streak at any other kind, and
`aside_streaks` (`:1645-1662`) ends a streak at any other key. `live_step5.py:608` and `:646` grade them. Only
`intent_mix` (`:1103-1104`) leaves `SAVE_KIND` (`:377`) out.

### 1.7 R-EXCEPT: the 28 handlers, each read (AST scan `s53/r1f/scan_except.out`: 28 = 11 AI + 17 test)

| # | where | handler | play path? | verdict |
|---|---|---|---|---|
| 1 | `__main__.py:166` `cmd_run` | `(LaunchError, OSError, PathsError) as error` | no (launcher) | sound. The scanner's "name read after" is a false positive: the later reads (`:191`) are inside another handler that binds its own `error` |
| 2 | `__main__.py:217` | `OSError as error` (record_launch) | no | sound: the next `memory_check` falls back to the run's verdict file, or to UNKNOWN if the folder is gone (refused). Fails closed |
| 3 | `game_memory.py:641` | `FileNotFoundError` | read before any press | sound |
| 4 | `game_memory.py:651` | `ValueError` (the header) | same | sound |
| 5 | `game_memory.py:669` | `ValueError` (a line) | same | sound (part 3 adds the ASCII check beside it) |
| 6 | `host/eyes.py:517` | `Exception: continue` (a symbol-table lookup, once) | host eyes, no press | sound: it catches `Exception` only, around `get_symbol` |
| 7 | `host/launcher.py:280` | `FileNotFoundError` | no | **DEFECT (minor)**: the read at `:279` is INSIDE the `try`, but it decodes strictly and only `FileNotFoundError` is caught. Probe: `read_launches RAISED UnicodeDecodeError (not LaunchError)`. `memory_check` (`:448-451`) catches only `LaunchError`, and `cmd_run` (`:166`) only `LaunchError/OSError/PathsError`, so the user gets a traceback instead of the refusal sentence. It fails closed (it runs before `seed_profile`), so no state changes. Fixed in part 7 |
| 8 | `host/launcher.py:287` | `ValueError as error` → `raise LaunchError from error` | no | sound |
| 9 | `host/launcher.py:441` | `MemoryFileError as error` | no | sound (the scanner's flag: the later `error` at `:450` belongs to its own handler) |
| 10 | `host/launcher.py:450` | `LaunchError as error` | no | sound |
| 11 | `mode.py:444` `_open_memory` | `MemoryFileError as error` | before any press | sound |
| 12-28 | test side: `check_paths.py:117`, `live_r1.py:187, 251, 266, 361, 376, 1211, 1218, 1288, 1885`, `probe_save_eyes.py:480, 488, 703`, `revert_r1.py:241, 259, 292`, `test_saving.py:1440` | narrow, or `except Exception` around a read, a `stdout.reconfigure` or a psutil call | no | sound: none catches `BaseException`, and none re-reads an unbound name |

Considered and NOT a defect: a JSON line nested more than about 1000 levels deep makes `json.loads` raise
`RecursionError`, not `ValueError`, past `game_memory.py:669`. Corruption cannot produce that, and the result (a crash
before any press, or a launcher traceback) fails closed.

### 1.8 N-3 and R-2 live: verified TRUE

- N-3: child B's frames are `CONTINUE_BUDGET + ARRIVAL_BUDGET + 600` (`live_r1.py:655`; 1700 + 320 + 600 = 2,620). A
  save needs `SAVE_FRAMES_NEEDED` = `SAVE_DIALOG_BUDGET` = 3,600 frames left (`skills/saving.py:110-115`), so no child B
  ever saves. These are unit-tested only: the continued writer's chain (`game_memory.py:733-735`: `parent =
  continued_from`, `last_payload = book.rebuild(parent)`), `own_cart("continued", False)` (`brain/saving.py:69-73`)
  answering OVERWRITE live, and R-1's "a save line carries its own `last_save`" after a continue. The unit pin of the
  chain is `test_saving.py:668` `test_rebuild_follows_the_parent_across_a_continue` (a continue from S1 while S2 is the
  newest line must write parent 1).
- **Which frozen set can show the chain.** In K-AFTER (`KILLS["K-AFTER"] = "S2.e4+40"`, `live_r1.py:73`) the continued
  save S2 is also the NEWEST save line (`MemoryBook.newest_save`, `game_memory.py:545-547`). So a mutant that chains to
  the newest line writes the same parent, the same base and the same id (`next_save_id` = 1 + max id, `:549-550`): there,
  "parent = continued_from" holds by construction. In K-INSIDE (`"S2.e3+130"`) the cart keeps S1 while S2's line is in
  the file (`live_r1.py:853` target S1; check 7 at `:932-940`), and `match_time` picks S1 (`game_memory.py:564-570`).
  There the two differ. K-INSIDE counted 4 of 4 in every held-out run so far (`r1live-HELDOUT`, `-FIXROUND`, `-VERIFY`).
- R-2: no arm stops a continue on a bound. The look-through is unit-tested and probed only (`06`, "Proven offline only").

## 2. Decisions (each with the rejected alternative)

- **D1. The refused exit forms (N-1).** `PLAY_LOOP_EXIT_NAMES` gains `GeneratorExit`, `BaseException`,
  `BaseExceptionGroup`, `ExitStack` and `AsyncExitStack`, so `raise`, `except`, `except*`, a tuple member, a subclass base
  and `contextlib.ExitStack` (an Attribute, judged by its attr) are all refused through `visit_Name`/`visit_Attribute`.
  New play-loop rules, all rule "b":
  - a bare `except:`;
  - a `return`, `yield`, `yield from` or `await` reached from a `finally` body without entering a nested
    `FunctionDef`/`AsyncFunctionDef`/`Lambda`/`ClassDef`;
  - a `break` or `continue` reached the same way and also without entering a loop nested in the `finally` (a `return`
    inside such a loop still discards the exit, so the loop exception is for `break`/`continue` only);
  - a `def __exit__` or `__aexit__`.

  Rejected: the review's two names only (a bare `except:`, a `finally: return`, a yield in a `finally` and an
  `ExitStack` callback each hold back or swallow an exit without naming any exit class); recording them as known limits
  (CLAUDE.md rule 6: a rule broken once belongs in a gate, and the play loop has no use of any of them today, measured).
- **D2. A together-refusal LATCHES the controller, and the HOST ends the run, outside the brain's stack (N-1).**
  `Controller` keeps a private `self._refused: str | None` and a read-only `refused` property. `_check_together` sets
  `_refused` on the first refusal and raises `ControllerError` as today, with no button touched. Once `_refused` is set,
  every later `tap` and `hold` raises `ControllerError` before any press, while `wait` still lets its frames pass. The
  held-button set becomes private (`self._held`) behind a read-only `held` property that returns a `frozenset`. The
  `if len(down) > 1 and down & _ALONE:` line stays byte-identical (S39's anchor).

  `Session` gains `_end_if_refused()`: if `self.controller.refused` is set, it logs `[AI-LIFECYCLE] the controller
  refused a reset or erase combination: <why> (USER RULING 52); ending the run` and calls
  `self.lifecycle.finish(_RESET_REFUSED, EXIT_REFUSED)`, with `_RESET_REFUSED = "reset-refused"` (exit 9, the code of
  `refused-debug-mode`, `host/session.py:190`). It is called:
  - FIRST in `_on_frame` (the next frame after a refusal, whatever the brain did with the error);
  - in `Session.run` before `give_up`/`finish("brain-returned")` (the brain returned right after catching it);
  - at the top of `run`'s `except BaseException` crash path (the error was never caught);
  - in `run`'s `except SystemExit` stray path, before `stray-exit`.

  The verdict file then says `exit_reason: reset-refused`. `_classify_session` already classes that NOT CLEAN through its
  default branch (`host/launcher.py:428`): not INVOLUNTARY and not `play: ...`, so refused. NOT CLEAN is PERMANENT for
  that game (`classify_end` is a pure function of the files, so only `--fresh`, which archives the memory, is left), as
  for a purity breach (spec D12's table, `06` 2026-10-29 "Consequences": R15 never relaunches after NOT CLEAN). The user is
  asked to confirm (section 10). Rejected:
  - the first draft's callback that finished INSIDE the refused press. It put a `SystemExit` into the brain's own
    generator stack, the only finish path that does so. A yield in a `finally` gave the brain a frame after the verdict,
    and an `ExitStack` callback swallowed it whole (section 1.1);
  - classifying the crash by `isinstance(error, ControllerError)` in `Session.run`. That misses a refusal the brain
    catches, after which it plays on unrecorded;
  - INVOLUNTARY for `reset-refused`. The reset the controller blocked would still get its reload: the effect ruling 52
    forbids;
  - a new `EXIT_` constant. That is a pinned `HOST_EXPORTS` change (`check_purity.py:638-643`) for no gain: the reason
    string carries the class.

  Known: a brain that catches the error and then never yields hangs until the launcher's wall clock. That is the
  pre-existing class of any brain that never yields, not new here.
- **D3. RULE C's new forms (N-2).** In the DECIDING files outside `PLAY_TIME_DOORS`:
  - (a) a string constant whose whole value is `play_time`, wherever it appears (a subscript key, a `.get`/`.pop`
    argument, a match-mapping key, a named constant, `attrgetter`'s argument). The exceptions are a dict display's key,
    a docstring and f-string text (the gate's MENTIONS-NEVER-FIRE convention: a dict display's key builds a dict, it
    reads nothing);
  - (b) `play_time` in a match class pattern's keyword attributes;
  - (c) a call of `asdict` or `astuple` (by name or as `dataclasses.<name>`): a whole-object copy carries the play time.

  New, in ALL deciding code (doors included):
  - (d) an `ast.MatchClass` with any positional `patterns`. It reads fields by position through `__match_args__`, so it
    is reported as RULE C and RULE A both (it reaches `play_time`, `flags` and `marks`).

  `vars` and a non-constant `getattr` stay purity rule (d)'s. Rejected: type inference (which object is a `Progress`; not
  possible in an AST gate); refusing only `asdict(<...>.progress)` (any alias passes); `@dataclass(match_args=False)` on
  `Progress` alone (it closes one class; the gate rule closes every class and needs no AI-code change). Measured: no
  deciding file outside the doors has any of (a)-(c) today. Every `'play_time'` constant in deciding code
  (`s53/r1f/mine/scan_forms.out`: `brain/saving.py`, `game_memory.py`, `skills/saving.py`) and the two `asdict` calls
  (`game_memory.py:396`, `:408`) are in door files. There are no class patterns at all (d). `brain/goals.py:501` is a
  comment, and `hands/dialogue.py:124` and `mode.py:575` are keywords.
- **D4. N-4: a per-line ASCII check, decoding unchanged.** In `read_book`, a line (the header included) that is not
  `str.isascii()` is unparsable (`None`): refused as a middle line, ignored as a torn last line (D6). Rejected:
  - `errors="strict"`. A `UnicodeDecodeError` would escape the `MemoryFileError` contract (a launcher traceback, or a
    brain crash classed INVOLUNTARY), and one bad byte in a torn LAST line would refuse the whole file, against D6;
  - a per-line checksum. That is a schema change (schema 2), for a bit flip that stays ASCII, and out of scope (section 9).

  The `torn` line's `length` keeps its meaning (the same decoding), so files written by `f4412116` read the same.
- **D5. V2-5: count and tell, never cap.** `judge_end` returns the class with `looked_through` (each looked-through
  session's number and end reason, newest first). `classify_end` keeps its 3-tuple, and its `words` gain `(looked through
  N continue(s) that stopped before restoring anything; the newest: '<reason>')`. `ContinueCheck` gains `looked_through:
  int`. Rejected: refusing after K consecutive stops. `classify_end` is a pure function of the files, so such a refusal
  would be PERMANENT (only `--fresh`, which loses the game): exactly the failure R-2 fixed. A stopped continue restores
  and plays nothing, so a run of them cannot undo anything (ruling 52 holds). Bounding RETRIES is the job of whoever
  retries (R15's supervisor, not built), and `looked_through` now lets it do that.
- **D6. V2-6: a save is TRANSPARENT to the curiosity row and the grader's streaks.** `after_goal` returns at once for a
  `save` goal, so the row neither resets nor grows. `curiosity_streaks` and `aside_streaks` skip `SAVE_KIND` spans. A
  streak's frames still run from its first goal's start to its last goal's end, so the save's frames are inside it, as the
  AI's own `STORY_ASIDE_FRAMES` clock counts them. Why: spec T4 already ruled a save "neither an errand nor the story's
  step". `CURIOUS_ROW_MAX` (`brain/goals.py:337`) exists because the step-5.1 review found six curiosity goals in a row,
  and a reset by bookkeeping lets C C save C C through. Rejected: a save as a break (it would be the one bookkeeping
  action that buys two more curiosity goals). Left as is, on purpose: `memory.decisions` (`brain/goals.py:1178`) counts
  the save decision (it is a clock for cooldowns, not a pattern of play).
- **D7. The launches read (R-EXCEPT).** `read_launches`'s `try` (`host/launcher.py:278-281`, the read already inside it)
  gains `except UnicodeDecodeError as error: raise LaunchError(...) from error` beside `FileNotFoundError`, so
  `memory_check` refuses with its sentence. Rejected: catching it in `cmd_run` (every other caller of `read_launches`
  would still see a raw exception).
- **D8. CHAIN is built on K-INSIDE's frozen set (a COPY), and kills child B by the state it REACHED.** On that set, the
  save the game loads (S1) is NOT the newest save line (S2, the abandoned branch), so "B's save chains to its
  `continued_from`" can fail (mutant CH1) where on K-AFTER it held by construction (section 1.8). Kill rule `N1+30`:
  after child B's FIRST save is complete (its `e4`), the rule is met at the first frame on which B stands on a map NEW to
  that save, provided no START has been pressed since that save's `e4` (no write under way). The kill is 30 frames after
  that. "NEW to that save" means in neither child A's maps before S1's `e3` nor B's maps from its arrival to its own save's
  `e3`. Child C then continues.

  What this makes falsifiable: C's arrival at S3 and C's restore holding NEW_B_pre (both non-empty by the counting rule).
  What it does NOT make falsifiable: C's restore holding none of NEW_B_post. Only save lines carry payloads
  (`game_memory.py:785-794`), so no registered mutant can put a post-save map into C's restore. That half is reported as
  a consistency check with no mutant, never as a proof. Rejected:
  - K-AFTER's frozen set (the chain property holds there by construction; the first draft's choice);
  - `B1.e4+40` alone (the post-save set is empty);
  - a midpoint rule from a CONTROL (child B's trajectory after a continue has no CONTROL run).
- **D9. R-2's arm stops the continue with a test-side COPY, not a fault switch.** The stopped continue runs the real
  launcher on a copy whose only edit is `skills/saving.py:127` `ARRIVAL_BUDGET = 320` → `R2_STOP_ARRIVAL` (half the
  narrowest arrival measured in development, section 5). Rejected:
  - an `AI_PLAYER_FAULT_*` switch read in `continue_game` (a new env read in the deployed continue path, and a new
    `ALL_SWITCHES` entry, for a test);
  - a frame-starving watcher (the stop would be the harness's, not one of the AI's seven retryable stops).

  The arrival bound is chosen because V2-5 names it as the stop likely to repeat, and because the game really has been
  CONTINUED in RAM before it stops (the strongest case for "a stop is not a reload").
- **D10. R-2's retry runs through `child_b` (real `memory_check` and `seed_profile`, then the harness with
  `ArrivalWatch`).** The stopped run before it goes through the REAL launcher, so the session the look-through judges
  carries the launcher's own record (`launches.jsonl`, the verdict's `exit_reason`). That record is EXERCISED live, not
  discriminated: in this arm the launcher's `exit_reason` and the end line's reason are the same continue-stop text, so
  mutant FX5 (`revert_r1.py:170-173`, the look-through reading the end line only) would also allow step 2. R2-RETRY is
  not counted as live evidence for FX5's guard, which stays unit-proven (section 9). Rejected: the retry through the
  launcher too (a launcher run has no test-side watcher, so its arrival would rest on the AI's own record).
- **D11. OLD arms reuse registered revert mutants.**
  - CHAIN-OLD = the NEW mutant CH1 in child B's tree. It is registered in `revert_r1.py` with its predicted unit test,
    the existing `test_rebuild_follows_the_parent_across_a_continue` (`test_saving.py:668`).
  - CHAIN-R1-OLD = FX1 in child B's tree (`revert_r1.py:152-155`).
  - R2-RETRY-OLD = FX3 in the retry child's tree (`revert_r1.py:161-164`).

  The selftest asserts that each live edit tuple equals revert_r1's, as it does for `R1M_EDITS`/S20+S22 and
  `S27_EDITS`. Rejected: new live-only mutants (an OLD half the unit lane does not also catch). FX1 is NOT
  continuation-specific (it changes every save line, child A's included), so CHAIN-R1-OLD shows only that C3 CAN FAIL. The
  continuation-specific OLD arm is CHAIN-OLD.
- **D12. Seeds.** The ledger (`gates/ledger.json`, 56 entries) uses 1-1384, 9901-9933, 5301-5365, 5401-5406 and
  5451-5484, and `git grep` finds no 55xx seed anywhere. Development 5501-5506; held-out 5551-5554; independent re-run
  5561-5564; fix round 5571-5574; verification after a fix round 5581-5584; spare 5591-5594. Each range is re-checked
  against the ledger at its registration.

## 3. The parts (file by file; anchors at `f4412116`)

### (a) `ai_player/gates/check_purity.py` (N-1, D1)
- `:179` `PLAY_LOOP_EXIT_NAMES` += `"GeneratorExit", "BaseException", "BaseExceptionGroup", "ExitStack",
  "AsyncExitStack"`; the comment at `:178` says why. If `visit_Attribute` does not already judge attr names against this
  set for play-loop files, it gains that check (`contextlib.ExitStack`). MEASURE on the worktree first, with a plant.
- New `visit_ExceptHandler`: in a play-loop file, `node.type is None` → fail rule "b" ("a bare `except:` catches the
  process's end"); then `generic_visit`.
- New check in `visit_Try` (and `TryStar`), play-loop files only:
  - a `Return`, `Yield`, `YieldFrom` or `Await` reached from the `finalbody` without entering a nested
    `FunctionDef`/`AsyncFunctionDef`/`Lambda`/`ClassDef` → fail "b" ("a `return` or `yield` in a `finally` discards or
    holds back the exit in flight");
  - a `Break` or `Continue` reached the same way and also without entering a `For`/`AsyncFor`/`While` nested in the
    `finally` → fail "b".
- In `visit_FunctionDef`/`AsyncFunctionDef`: the name `__exit__`/`__aexit__` in a play-loop file → fail "b".
- The module docstring's rule (b) paragraph (`:67-71`) lists the new forms.

### (b) `ai_player/host/controller.py` (N-1, D2)
- `__init__`: `self._held: set[str] = set()`, `self._refused: str | None = None`; read-only properties `held` (returns
  `frozenset(self._held)`) and `refused`. Purity rule (d) refuses `x._y` on anything but `self` (measured:
  `controls._held = set()` FAILS [d]), so the brain can neither empty the set nor reset the latch.
- `_check_together` (`:69-74`): `down = self._held | {button}`; the `if len(down) > 1 and down & _ALONE:` line stays
  byte-identical (S39). On a refusal it sets `self._refused = message` and raises `ControllerError` as today. A new
  first statement raises `ControllerError("refused: the controller refused a reset or erase combination earlier; nothing
  more is pressed")` when `_refused` is set.
- `hold` (`:91-103`): `self._held.add`/`discard` in place of `self.held.*`. The check stays before
  `press_button`/`hold_button` (`:86-87`, `:95-96`), so nothing is pressed. `wait` is unchanged.
- No new export (`HOST_EXPORTS` unchanged) and no callback (the controller stays framework-agnostic).

### (c) `ai_player/host/session.py` (N-1, D2)
- A private module constant `_RESET_REFUSED = "reset-refused"`; a new method `_end_if_refused(self)` (D2).
- `_on_frame` (`:288`): `self._end_if_refused()` as its first statement after `self.frames_seen += 1`.
- `run` (`:322-339`): `self._end_if_refused()` before `if reason is None:` (the return path), as the first statement of
  `except BaseException` (before `crash`), and as the first statement of `except SystemExit` when
  `not self.lifecycle.finishing` (before `stray-exit`). `except GeneratorExit` is unchanged (the next `_on_frame` checks
  the latch before `abandoned`).

### (d) `ai_player/host/launcher.py` (N-1 test row, V2-5, R-EXCEPT)
- `_INVOLUNTARY` (`:260`) unchanged: `reset-refused` falls to NOT CLEAN at `:428`. The `END_CLASSES` comment
  (`:255-258`) and the D12 table in the README name `reset-refused` under NOT CLEAN.
- `read_launches` (`:275-296`): D7's clause beside `except FileNotFoundError` (`:280`).
- V2-5 (D5): a frozen dataclass `EndJudgement(kind, words, allowed, looked_through: tuple[tuple[int, str], ...])`.
  `judge_end(book, launches)` is today's `classify_end` body (`:336-357`); it collects `(session["n"], str(reason))`
  before each `session = earlier`, and appends the count and the newest reason to `words` when the tuple is non-empty.
  ‼ The line `if kind != "CHOSEN" or earlier is None or not _stopped_before_restore(book, session, reason):` stays
  byte-identical (FX3's anchor, `revert_r1.py:162`, and R2-RETRY-OLD's live edit). `classify_end` becomes `e =
  judge_end(...); return e.kind, e.words, e.allowed`. `ContinueCheck` (`:264-272`) gains `looked_through: int = 0`.
- `memory_check` (`:435-458`): `:452` becomes `judgement = judge_end(book, launches)` followed by `kind, words, allowed =
  judgement.kind, judgement.words, judgement.allowed`. `if not allowed:\n        return ContinueCheck(False,` stays
  byte-identical (hand-written L7's anchor, `revert_r1.py:136-139`). Both returns pass `looked_through=len(...)`.
  Census mutant C230 (`revert_r1_mutants.json`, anchor `    kind, words, allowed = classify_end(book, launches)\n`)
  loses its anchor: it is regenerated against the `judge_end` call in `memory_check`, with a name map (section 6).

### (e) `ai_player/__main__.py` (V2-5)
- The CONTINUE state line (`:170-175`) adds `; looked through {check.looked_through} stopped continue(s)` when the count
  is non-zero.

### (f) `ai_player/gates/check_fairness.py` (N-2, D3)
- In `scan_file`'s RULE C block (`:392-404`), `reads_time` also becomes true for:
  - an `ast.Constant` whose value is `PLAY_TIME_FIELD`, not a docstring, not inside a `JoinedStr`, and not a key of an
    `ast.Dict` display (collect those keys' ids first, as RULE A's `skipped` set does);
  - an `ast.MatchClass` whose `kwd_attrs` hold `PLAY_TIME_FIELD`;
  - an `ast.Call` whose `_call_name` (`:325`) is `asdict` or `astuple`.

  Each fires through `time_door` (`:344-350`), so the three doors (`:101-107`) keep working, and the stale-door check
  (`:458-461`) is unchanged.
- New, under `if deciding:` and outside any door test: an `ast.MatchClass` with non-empty `patterns` → `C  ...: matches
  a class by POSITION: it reads its fields through __match_args__ (the play time, the flags and the marks among them);
  name the attributes` (D3 (d)).
- The docstring's RULE C paragraph (`:33-36`) lists the forms, and says `vars` and a non-constant `getattr` are purity
  rule (d)'s.

### (g) `ai_player/game_memory.py` (N-4, D4)
- `read_book` (`:634-691`): the header parse (`:649-652`) treats a non-ASCII `parts[0]` as unparsable (→ `no_header`).
  The line loop (`:666-670`) appends `None` for a non-ASCII line before trying `json.loads`. `errors="replace"` at
  `:639` stays, with a comment saying why (D4). The docstring (`:635-637`) and the module docstring's D6 sentence (`:37`)
  say "an unreadable or non-ASCII line".

### (h) `ai_player/brain/goals.py` (V2-6, D6)
- `after_goal` (`:1062-1069`): first statement `if goal.kind == "save": return None`, with the comment (T4; D6). The
  docstring (`:1063-1067`) says a save neither ends nor joins a row.

### (i) `ai_player/gates/rate_step5.py` (V2-6, D6)
- `curiosity_streaks` (`:1521-1536`): `if span["kind"] == SAVE_KIND: continue` before `:1527`.
- `aside_streaks` (`:1645-1662`): `spans = [s for s in goal_spans(actions) if s["kind"] != SAVE_KIND]`.
- Both docstrings cite T4. `SAVE_KIND` (`:377`) is the grader's own copy (the G-3 rule: no AI import).

### (j) `ai_player/gates/live_r1.py` (V2-1, V2-2, N-3, R-2, seeds)
- **Headline.** `between_caveat(summaries, seeds)` (`:1488-1496`) reads `pass` too: `... (the midpoint arm
  K-BETWEEN-MID counted C of N{: vacuous}; passed P of C{; FAILING on seeds [...]}; orchestrator ruling 5)`. A new
  `verdict_line(result, summaries, seeds, found) -> str` returns exactly the `LIVE R1 VERDICT: ...` line. `cmd_verdict`
  prints it (`:1530`) and writes it to `verdict.json` as `"headline"` (`:1526-1528`).
- **SaveWatch in a continued child (code-host F4).** `MemoryTail.__init__` gains `start: int = 0`. In a child B,
  SaveWatch builds its tail with `start = memory.stat().st_size` (the frozen file's size), so the frozen set's lines
  (child A's S1 and S2) are never attached to B's save. As a second guard, a save line attaches to a save only if its
  `id` is at least the frozen file's `next_save_id`. CHAIN's checks never read the watcher's attached line: they read
  B's save line from the frozen `memory.jsonl` BY ID (section 5.2).
- **SaveWatch kill rule `N<k>+<frames>`** (`parse_kill` `:230-240`, `_check_kill` `:478-516`). It is reached at the
  first frame `f` after save k's `e4` that meets all of these:
  - its RAM map (`self.maps`, `:382-385`) is not in `self.known` (the `--known-maps` file's set, plus every map this
    watcher recorded from `--maps-from` up to save k's `e3`);
  - no START has been pressed since save k's `e4` (`self.starts`);
  - `f - entered >= frames`.

  The READY payload adds `entered`, `new_map` and `starts_since_e4`. A START pressed before the rule is met is recorded
  (`"n_rule": "a save began first"`) and the child is NOT killed (the arm then does not count).
- **child_b** (`:623-666`): optional `--kill`, `--record`, `--known-maps` and `--maps-from-arrival`. With `--kill` it
  attaches a `SaveWatch` (killable) beside `ArrivalWatch`, and its `maps` count only from ArrivalWatch's held free
  arrival frame (a continued game's RAM location before the load is not a map it stood on: MEASURE in development,
  section 8 step 5). `RESULT` adds `launcher_sha` (sha256 of the `host/launcher.py` it imported) and `memory_sha` (sha256
  of the `game_memory.py` it imported), as `skills_saving` (`:635-636`) does.
- **A test-side memory reader** `rebuild_payload(lines, save_id)`: applies the delta ops of a save line's chain to its
  full ancestor, importing NOTHING from `ai_player` (a port of the verification's `r1_live.py`,
  `s53/r1build/build/verify2-rerun/r1_live.py`, which was fault-tested: 0 of 93 on #53's pre-fix files, 94 of 94 on
  #55's).
- **Arms** `CHAIN`, `CHAIN-OLD`, `CHAIN-R1-OLD`, `R2-RETRY`, `R2-RETRY-OLD` (section 5), with `cmd_chain`,
  `cmd_chain_old`, `cmd_r2`, `grade_chain` and `grade_r2`. These gain them: `GRADED_ARMS` (`:104`), `OLD_OF` (`:103`),
  `EXPECTED`, `discriminators` (`:1445-1485`) and `registered_numbers` (`:1565-1581`). The new registered numbers are the
  new constants, `CH1_EDITS`, `FX1_EDITS`, `FX3_EDITS`, `R2_STOP_EDITS`, `R2_STOP_ARRIVAL`, `CHAIN_B_FRAMES`,
  `CHAIN_B_TIMEOUT` and `N_KILL_FRAMES`. `HELD_OUT` (`:91`) becomes `(5551, 5554)`.
- **Selftest** (`:1620-1748`): the new arms' recorded development rows, and planted grader FAULTS (in `FAULTS`, `:135`):
  - `chain_parent_ignored` (C3's parent check skipped; CHAIN-OLD's row must then fail to show);
  - `chain_last_save_ignored`;
  - `pre_maps_ignored` (C6's NEW_B_pre half skipped);
  - `stale_line_attached` (the tail starts at 0: B's save graded by S2's line);
  - `lookthrough_ignored`;
  - `caveat_passes_ignored`;

  and cases for the headline (vacuous; counted 4 and failing 4; the verdict LINE through `verdict_line` contains the
  caveat).

### (k) `ai_player/README.md`
- "Fault and control switches": four "(a COPY)" rows: R2-STOP's arrival bound; CH1 for CHAIN-OLD; FX1 for
  CHAIN-R1-OLD; FX3 for R2-RETRY-OLD.
- "Saving and CONTINUE": the new refused forms, the controller's latch and `reset-refused` (NOT CLEAN, permanent), the
  look-through's count, the arms, and KNOWN LIMITS rewritten (section 9's).

## 4. Unit tests (a FAULT and a CONTROL for every guard)

| guard | test (file: class.method) | FAULT | CONTROL |
|---|---|---|---|
| D1 names | `test_check_purity: PlayLoopExitTests.test_the_play_loop_cannot_exit` (extend `EXIT_PROBES`, `test_check_purity.py:759-769`) | X07 `raise GeneratorExit` in brain/; X08 `except BaseException:` in skills/; X09 `except (ValueError, BaseException):` in mode.py; X10 `except* BaseException:` in hands/; X11 `class Stop(BaseExceptionGroup)` in world/; X16 `contextlib.ExitStack()` with `stack.push(lambda *e: True)` in brain/ | the same words in a docstring, a comment and a string pass; the real package passes |
| D1 bare except | same test, X12 bare `except:` in game_memory.py | fails "b" in the planted file | `except ValueError:` in the same place passes |
| D1 finally | same test, X13 `finally: return None` in brain/; X14 `finally: break` inside a loop that encloses the `try`, in skills/; X17 `finally: yield from controls.wait(1)` in skills/ (the measured plant); X18 `return` inside a `for` loop inside a `finally` in hands/ | each fails "b" | `finally:` holding a nested `def` with a `return` and a `yield`, and a `for` loop with `break` inside a `finally`, pass |
| D1 `__exit__` | same test, X15 a class with `def __exit__` in hands/ | fails "b" | `def exit_menu` (a name with `exit` in it) passes |
| D2 controller | `test_host: ControllerTogetherTests.test_a_refusal_latches_the_controller` (the fake framework of `:779-801`) | A held, tap START: `ControllerError`, `refused` set, no `press_button` call. Then `tap("B")` and `hold("Up", 2)` each raise with no press, and `wait(3)` passes 3 frames | a FRESH controller: START alone, then B held + Up: no error, `refused` None |
| D2 held | same class, `test_the_held_set_cannot_be_changed_from_outside` | `controller.held` is a `frozenset` (`.clear` absent), `controller.held = set()` raises `AttributeError`; a purity plant in brain/ that reads `controls._held` fails rule (d) | `held` reports A while a hold of A runs, and is empty after it |
| D2 existing | `ControllerTogetherTests.test_start_or_select_never_with_another_button` (`:808-834`) | restructured: one FRESH controller per subTest (the latch would otherwise refuse the next case) | its CONTROL half on its own fresh controller |
| D2 session | `test_host` harness `reset_refusal`, on the `harness_guarded_attacks` pattern (`test_host.py:417-425`; runs where the framework is, ruling 2). `Session(RunOptions.from_env(), None)` with NO `start()` (a harness has no emulator: `start()` reaches `attribution.install()`, which raises without one, `attribution.py:748-750`, as `test_host.py:572-580` records); `modules.context.context.emulator` set to a SimpleNamespace fake recording `press_button`, `hold_button` and `release_button`; `context.bot_mode = "AI Player"` | (1) `hold("A", 10)` advanced once, `tap("Start")` advanced (bare, the error caught by the harness), then `session._on_frame()`: SystemExit code 9, `purity.json` `exit_reason` `reset-refused` (verdict UNVERIFIED, as `test_host.py:566-567` accepts), no `Start` among the fake's presses. (2) The same with the tap inside `try: ... except Exception: pass`. (3) The latch set as in (1), then `session.run()` driven with `next()`: the real brain's first step on the fake emulator ends in an exception (MEASURE in development; STOP if it does not), and the run ends `reset-refused`/9, not `crash`/2. Each case runs in its own subprocess | (a) START alone, then B held + Up, then `_on_frame()` returns normally (no finish), `refused` None. (b) Case (3) with NO latch ends `crash`/2 |
| D2 launcher | `test_saving: LauncherContinueTests.test_the_end_classes` (`test_saving.py:2057`) gains rows | a launcher line or verdict with `exit_reason` `reset-refused` → NOT CLEAN, refused | `crash` → INVOLUNTARY, allowed (unchanged) |
| D3 | `test_safety_gates: FairnessTests.test_the_play_time_is_read_only_through_its_doors` (`:477`) gains plants | each fails RULE C in `brain/goals.py`: the review's F2 (subscript), F3 (`asdict`), F7 (`.get`), F8 (match class keyword), F9 (`astuple`), F11 (match mapping), `FIELD = 'play_time'`, and F12 `case Progress(_, _, _, _, _, _, _, t)` (positional) | a dict display key, a docstring, an f-string's text and `replace(p, play_time=None)` pass; the same subscript inside `brain/saving.py` (a door) passes; `case Progress(play_time=t)` inside a door passes |
| D3 cover | same class, `test_vars_and_named_getattr_are_purity_s` | `vars(look.progress)` and `getattr(x, FIELD)` in brain/ fail `check_purity.scan` rule (d) | the real package passes both gates |
| D4 | `test_saving` (the S25 test's class) `test_a_non_ascii_middle_line_is_refused` | a `0xFF` byte in a middle line's string → `MemoryFileError("unreadable")`; a valid UTF-8 `é` in a middle line → refused; a non-ASCII header → `no_header` | a clean file reads; a `0xFF` in a torn LAST line → ignored (`torn` set), and after a continue's writer acknowledges it the next read accepts the file |
| D5 | `LauncherContinueTests.test_the_look_through_is_counted_and_told` | 1, 5 and 50 stops → `words` contains `looked through 1`/`5`/`50` and the newest reason; `memory_check(...).looked_through` equals the count | no stop → no "looked through" in `words`, `looked_through` 0; the six cases of `test_a_continue_that_stopped_before_its_restore_is_looked_through` unchanged |
| D6 AI | `test_goals` beside `:3486-3493` `test_a_save_neither_ends_nor_joins_a_curiosity_row` | C C save: `curious_row` stays 2, `curious_ok()` False (the FAULT half on the old code: 0 and True) | C C story-goal: 0 (unchanged); a save after a story goal leaves 0 |
| D6 grader | `test_goals` beside `:5297-5302` and `:3158-3167` | C C save C C → one curiosity streak of 4; aside aside save aside → one aside streak of 3 | C C story C C → two streaks; `intent_mix`'s save test unchanged |
| D7 | `LauncherContinueTests.test_an_unreadable_launches_file_is_refused` | a `0xFF` byte in `launches.jsonl` → `memory_check` returns `ok False` with "cannot be read", no exception | a clean file → allowed as before |
| CH1 | existing `test_saving.py:668` `test_rebuild_follows_the_parent_across_a_continue` (asserts parent 1 on a continue from S1 while S2 is newest) | under CH1: parent 2 | its existing rebuild asserts |
| V2-1/V2-2 | NEW `test_saving: LiveR1HeadlineTests` (imports `ai_player.gates.live_r1`; offline) | midpoint counted 4 failing 4 → the line says `passed 0 of 4; FAILING on seeds [1, 2, 3, 4]`; counted 0 → `vacuous`; `verdict_line` without the caveat (a monkeypatched `between_caveat` returning "") is detected by comparing to the expected line | the midpoint rule (`BETWEEN_RULE = "midpoint"`, patched) → no caveat |

Every new test names its FAULT and CONTROL halves in its docstring, as the R1 tests do.

## 5. The live proof

### 5.1 Arms (new; the existing ten graded arms and K-BETWEEN-MID run unchanged)

| arm | built from | kill / stop | expectation (from the arm's OWN record) |
|---|---|---|---|
| **CHAIN** | a COPY of K-INSIDE's frozen set, same seed (counts only where K-INSIDE counted) | child B (REAL tree) continues S1 and plays; kill `N1+N_KILL_FRAMES` (D8); then child C (REAL tree) continues B's frozen set | FILE at B's kill = S3 (B's save); B's S3 line has parent = S1's id ≠ S2's id; C continues S3 |
| **CHAIN-OLD** | another COPY of the same K-INSIDE frozen set | child B on mutant CH1, kill `S1.e4+40` (B's own first save complete); no child C | B's S3 line's `parent` = S2's id (the abandoned line) |
| **CHAIN-R1-OLD** | another COPY of the same set | child B on mutant FX1, kill `S1.e4+40`; no child C | B's S3 line's rebuilt `goals.last_save.id` ≠ its own id ("C3 can fail") |
| **R2-RETRY** | K-AFTER's frozen set, in a mirror build root (`mirror_build_root`, `:1173-1201`) | step 1: the REAL launcher `run --continue` on the R2-STOP COPY (D9) → stops on its arrival bound; freeze; step 2: `child_b` (REAL tree) | step 2 allowed (looking through step 1) and arrives at S2 |
| **R2-RETRY-OLD** | R2-RETRY's frozen set after step 1 | step 2 only, `child_b` from the FX3 tree (`revert_r1.py:161-164`) | refused, class CHOSEN |

### 5.2 Checks (graded by the second path; the AI's own record only where named)

CHAIN counts when all of these hold:
- K-INSIDE counted on this seed (its FILE S1 or S1+ERROR, S2's line in the file first, NEW non-empty);
- B's record shows its first save's `e4` before the kill;
- the kill was by rule N with `starts_since_e4` 0;
- `NEW_B_pre` is non-empty.

`NEW_B_pre` is the maps B first stood on from its arrival to its save's `e3`, minus child A's maps before S1's `e3`.
`NEW_B_post` is the maps B first stood on after its save's `e3` and before the kill, not in the known set; it is
non-empty by the rule. `ABANDONED` is K-INSIDE's NEW minus every map B stood on before its save's `e3`.

- **C1 file:** the probe's parser on B's frozen cart, with truths `{S1: child A's; S3: B's save 1}` → `S3`. A completed
  write is positive evidence that "There is already a saved file" was answered YES (`own_cart("continued")`, live).
- **C2 B continued S1:** B's session line `continued_from` = S1's line id, and B's arrival = S1's truth (PIDs, map,
  tile, the boot play time), as K-INSIDE's check 2.
- **C3 the chain (N-3, R-1):** read by the TEST-SIDE reader from B's frozen `memory.jsonl`, the save line found BY ID
  (the frozen file's `next_save_id` before B, i.e. 3):
  - its `parent` = B's `continued_from` (S1's id) and ≠ S2's id (the discriminated half; CHAIN-OLD);
  - its payload REBUILDS through its chain (no missing parent, no failed op);
  - the rebuilt `goals.last_save` holds `id` = its own id and `play_time` = its line's stamp, compared field by field
    (the record also carries `frame` and `why`, `brain/saving.py:236-237`);
  - that stamp = B's RAM truth play time at that save's `e3` (the game's data).
- **C4 the save across the continue:** B's save began on a held free screen at a ruling-51 moment (`moment_of`), and
  its stamp is at least 3 game minutes after S1's. Both are REPORTED, not graded as proof of the restored `last_save`:
  any later save passes them. "The restored `last_save` at work" counts as exercised ONLY where B's own log (the AI's own
  record, named as such) has an `[AI-SAVE] no save for ...: its last save was at <S1's stamp>` line. Otherwise it is
  reported `not exercised`.
- **C5 C's continue:** child C's `memory_check` (the REAL launcher's) is `ok`, class KILLED. C's session
  `continued_from` = B's save id. C's arrival (ArrivalWatch) = B's save-1 truth (PIDs, map, tile, boot play time).
  CONTINUE pressed, no NEW GAME, no page.
- **C6 the memory as of the post-continue save:** C's restore snapshot (`restore_snapshot`, `:794-814`) agrees with C's
  session `restored_maps`, and it holds every map of S1's restored set and of `NEW_B_pre` (graded). That it holds NONE of
  `NEW_B_post` and NONE of `ABANDONED` is a CONSISTENCY CHECK with no registered mutant (D8; only save lines carry
  payloads). It is reported, and a failure of it is a FAIL, but it is never cited as proof of the property.
- **CHAIN-OLD `old_shows`** (positive evidence): the CH1 tree ran (B's `RESULT` names the mutant `game_memory.py`
  sha256), B's save line exists, and its `parent` = S2's id.
- **CHAIN-R1-OLD `old_shows`:** the FX1 tree ran (the mutant `mode.py` sha256), B's save line exists, and its rebuilt
  `goals.last_save.id` ≠ its own id. Determinism line for both: the OLD B's presses digest up to its save's `e3` equals
  CHAIN's B (one trajectory, replayed; not a replication).

R2-RETRY counts when all of these hold:
- K-AFTER's FILE was S2;
- step 1's launcher line exists with `exit_reason` beginning `play: stuck: the continue stopped: the continued game did
  not reach a free overworld within {R2_STOP_ARRIVAL} frames`;
- step 1's session has `continued_from` None, its end line `stopped_before_restore` True and `chosen` False;
- no `save` or `lost` line follows it;
- step 1's action log shows the CONTINUE press (the game was continued in RAM).

- **R1 allowed:** step 2's `memory_check` is `ok`, class KILLED (session 1, K-AFTER's child A, has no end line). Its
  words contain `looked through 1` (V2-5) and step 1's reason.
- **R2 arrival:** step 2 continued S2 (`continued_from`), arrival = S2's truth (PIDs, map, tile, boot play time),
  CONTINUE pressed, no NEW GAME, no page.
- **R3 step 1 was clean:** its `purity.json` verdict is CLEAN (a NOT CLEAN step 1 would be refused for another reason).
- **R2-RETRY-OLD `old_shows`:** the FX3 tree ran (`launcher_sha` = the mutant's), `memory_check` refused with class
  CHOSEN, and the frozen `memory.jsonl` is byte-identical after it (sha256 before and after).
- Not claimed: FX5's guard (D10; the two reasons are the same text in this arm).

### 5.3 Discriminators (9 per seed; reported, never in the verdict)

These are the existing 6 per seed (`discriminators`, `:1445-1485`), plus:
- CHAIN / CHAIN-OLD: B's save line `parent` [S1's id, S2's id];
- CHAIN / CHAIN-R1-OLD: the rebuilt `last_save.id` [own id, S1's id];
- R2-RETRY / R2-RETRY-OLD: `memory_check.ok` [True, False].

As today, `discriminators` is REPORTED ONLY and `verdict_of` never reads it. The expectation is that **every pair
differs on each seed where both of its arms count**. A pair on a seed where an arm did not count is listed and not
expected to differ. The OLD arm's `old_shows`, which IS in the verdict, already requires its own difference.

### 5.4 Floors, verdict, OLD-arm counting

As today (`verdict_of`, `:1386-1420`):
- every graded arm counts on at least `FLOOR` = 3 of 4 held-out seeds;
- an OLD arm counts on a seed only where its NEW twin counts (CHAIN-OLD and CHAIN-R1-OLD have CHAIN as their twin);
- PASS needs every counted NEW arm passing and every counted OLD arm showing.

The verdict line is `verdict_line`'s (part (j)), naming ruling 5 and the midpoint arm's count AND passes.

### 5.5 Budgets and timeouts: MEASURED in development first, then 2x the widest (orchestrator ruling 2)

| constant | development value (a measuring cap) | graded value |
|---|---|---|
| `CHAIN_B_FRAMES` | 120,000 frames | `CONTINUE_BUDGET + ARRIVAL_BUDGET` + 2 x the widest (arrival → kill) seen on 5501-5506 |
| `CHAIN_B_TIMEOUT` | 1,800 s | 2 x the widest wall time, never under 300 s |
| the OLD B arms (kill `S1.e4+40`) | as CHAIN's B | 2 x the widest (arrival → that kill) |
| `N_KILL_FRAMES` | 30 | 30 (fixed: a frame offset after the rule is met, not a budget) |
| `R2_STOP_ARRIVAL` | set BEFORE R2-RETRY's development run, from the development K-AFTER, K-INSIDE and LAUNCH arrivals | floor(narrowest measured arrival / 2); the README's earlier 130-159 frames suggest about 65 |
| step 1 frames / wall | `CONTINUE_BUDGET + R2_STOP_ARRIVAL + 600`; `LAUNCH_WALL` 300 s, `LAUNCH_TIMEOUT` | as measured, 2x |
| child C, step 2 | the existing child B budget (2,620 frames) and `CHILD_B_TIMEOUT` | unchanged unless development measures more |

All of them go into `registered_numbers` before the held-out registration.

### 5.6 Seeds and the ledger (D12)

- `#57`: development 5501-5506, begun before its first run (`live_r1.py ledger register|begin --first 5501 --last
  5506`).
- `#58`: held-out 5551-5554, registered (and `ledger begin` checked) BEFORE any of them runs. One plan of every arm
  (CONTROL, K-AFTER, K-INSIDE, K-SILENT, K-FIRST, K-BETWEEN, K-BETWEEN-MID, LAUNCH, the three existing OLD arms, CHAIN,
  CHAIN-OLD, CHAIN-R1-OLD, R2-RETRY, R2-RETRY-OLD) and one verdict.
- The independent re-run (by an agent that wrote none of the code): 5561-5564. A fix round (any code change after #58):
  5571-5574, every arm re-run, registered first. Its independent verification: 5581-5584.

## 6. Revert mutants (`gates/revert_r1.py` `MUTANTS`, `:59-181`; census sites in `revert_r1_mutants.json`)

| name | rule broken | predicted test(s) | suites |
|---|---|---|---|
| S40c | the five names out of `PLAY_LOOP_EXIT_NAMES` (`:179` back to its four) | `PlayLoopExitTests.test_the_play_loop_cannot_exit` | `test_check_purity:PlayLoopExitTests` |
| S40d | the bare-`except` rule's `if` → `if False` | same | same |
| S40e | the `finally` return/break/continue rule off | same | same |
| S40f | the `__exit__` rule off | same | same |
| S40g | the `finally` yield/await rule off | same | same |
| L11 | `_check_together` never sets `_refused` | `ControllerTogetherTests.test_a_refusal_latches_the_controller`; the `reset_refusal` harness tests | `test_host:ControllerTogetherTests`, `test_host` |
| L12 | the latch's first statement removed (a press after a refusal goes through) | `test_a_refusal_latches_the_controller` | `test_host:ControllerTogetherTests` |
| L13 | `"reset-refused"` added to `_INVOLUNTARY` | `LauncherContinueTests.test_the_end_classes` | `test_saving` |
| L14 | `read_launches`'s `UnicodeDecodeError` clause removed | `LauncherContinueTests.test_an_unreadable_launches_file_is_refused` | `test_saving` |
| L15 | `_on_frame`'s `_end_if_refused()` call removed | the `reset_refusal` harness cases (1) and (2) | `test_host` (main checkout, ruling 2) |
| L16 | `run`'s crash path's `_end_if_refused()` call removed | the `reset_refusal` harness case (3) | `test_host` (main checkout) |
| L17 | `held` returns the mutable `self._held` | `test_the_held_set_cannot_be_changed_from_outside` | `test_host:ControllerTogetherTests` |
| S46c / S46d / S46e / S46f | RULE C's constant / match-class keyword / `asdict` / positional class pattern form off | `FairnessTests.test_the_play_time_is_read_only_through_its_doors` | `test_safety_gates:FairnessTests` |
| M14 | `read_book`'s ASCII check removed (both places) | `test_a_non_ascii_middle_line_is_refused` | `test_saving` |
| FX8 | `judge_end` drops the count from `words` | `test_the_look_through_is_counted_and_told` | `test_saving` |
| FX9 | `memory_check` leaves `looked_through` 0 | same | `test_saving` |
| CH1 | `MemoryWriter.__init__`'s `self.parent` = the NEWEST save line's id (`game_memory.py:734`) | `test_rebuild_follows_the_parent_across_a_continue` (`test_saving.py:668`) | `test_saving` |
| V6a | `after_goal`'s save return removed | `test_a_save_neither_ends_nor_joins_a_curiosity_row` | `test_goals` |
| V6b / V6c | `curiosity_streaks` / `aside_streaks` count a save as a break | the two grader tests | `test_goals` |
| LV1 | `verdict_line` omits `between_caveat` | `LiveR1HeadlineTests` | `test_saving` |
| LV2 | `between_caveat` ignores `pass` | `LiveR1HeadlineTests` | `test_saving` |

- **Anchors that must not move** (revert_r1 requires each anchor exactly once, `revert_r1.py:226`):
  - FX3's look-through line in `judge_end`;
  - L7's `    if not allowed:\n        return ContinueCheck(False,` in `memory_check`;
  - S39's `        if len(down) > 1 and down & _ALONE:\n` in `_check_together`;
  - FX1's `mode.py` line.

  Before the change, the builder lists every hand-written and census mutant whose anchor text lies in a function the
  change edits (`_check_together`, `tap`, `hold`, `Controller.__init__`, `Session.__init__`/`_on_frame`/`run`,
  `read_launches`, `classify_end`, `memory_check`, `read_book`, `after_goal`), and runs `revert_r1` once to confirm
  every anchor still resolves. Census mutant **C230** (`memory_check`'s `classify_end` call) is REGENERATED against the
  new `judge_end` call in `memory_check`, with a name map (C230 → its new name) and the same predicted tests
  (`test_a_chosen_end_is_refused_by_the_cli`, `test_a_newer_memory_is_refused_byte_identical`). Any other anchor the
  change moves is regenerated the same way.
- **CALL-SITE CENSUS (orchestrator ruling 4).** `gates/call_census.py` scans the AI side only (`SKIP_PARTS = ("gates",
  "evidence", "__pycache__")`, `call_census.py:50`). Against HEAD `f4412116`, the call sites of every new or changed
  AI-side function are closed by generated census mutants (the fix round's `gen_fix_mutants.py` pattern, predictions
  recorded from their first run), never by a waiver: `judge_end` (and its call in `memory_check`), `read_launches`,
  `read_book`, `after_goal`, `Controller.__init__`/`_check_together`/`tap`/`hold`/`held`/`refused`,
  `Session._end_if_refused` (its four call sites) and `Session.__init__`. The census mutants on the Session wiring
  predict the `reset_refusal` harness tests and are RECORDED on the main checkout at apply (ruling 2). The test-side
  functions (`verdict_line`, `between_caveat`, the new purity and fairness visitors, `curiosity_streaks`,
  `aside_streaks`) are not census sites: they are covered by the hand-written S40c-g, S46c-f, V6b/V6c and LV1/LV2
  above. `census_waivers.json` gains no entry.
- The live constants `CH1_EDITS`, `FX1_EDITS` and `FX3_EDITS` equal `MUTANTS["CH1"][2]`, `MUTANTS["FX1"][2]` and
  `MUTANTS["FX3"][2]`, as the selftest asserts (D11).

## 7. Regression lane and gates impact

- **Suites touched (no new suite):**
  - QUICK (`run_regression.py:210-221`): `check_purity`, `test_goals`, `call_census`, `check_fairness`, `test_saving`;
  - units: `test_check_purity` (sharded), `test_safety_gates`, and `test_host` (whole, on the main checkout, ruling 2:
    the `reset_refusal` harness needs the framework);
  - reverts: `revert_r1` (about 23 hand-written plus the census mutants; update `run_regression_times.json`);
    `revert_step5` (its G-mutants anchor `brain/goals.py` near `after_goal`, `revert_step5.py:672-697`, and
    `rate_step5.py`: re-run, re-anchor if a count changes); `revert_safety_gates` (it covers `rate_step5`'s
    `HASHED_FILES`).
- **Grader hashes:** `rate_step5.py` is in its own `HASHED_FILES` (`rate_step5.py:2893`), so its sha moves. Ledger #1-#56
  are all `done`, so no registered graded range is left open. `live_step5`'s next run is ALREADY a re-baseline (`06`
  2026-10-29 Consequences) and now also carries D6. `live_r1.py`'s sha moves too (its `HASHED_FILES`, `:130-133`): the
  new registrations (#57, #58, ...) hash the final file.
- **Behaviour change in the AI:** D6 only (a save no longer resets the curiosity row). D2 changes nothing in the AI's
  play: nothing in the AI holds two buttons today (`controller.py:39-42`). It reaches the bot tuner only through a commit
  (the learner's clone fast-forwards between cycles), and the bot itself is untouched.
- **Gates:** `check_purity` and `check_fairness` must PASS on the real package after their changes (the measured zero
  uses, section 1.1 and D3). `check_paths` is unchanged. `HOST_EXPORTS` and `INSTRUMENT_SHA256` are unchanged (no new
  export, `attribution.py` untouched).
- **Evidence:** `ai_player/evidence/<date>-r1f-REVERT.txt`, `<date>-r1f-live-DEV.txt` and `<date>-r1f-live-HELDOUT.txt`
  (and the re-run's and any fix round's), with tree zips only where an evidence file names one.

## 8. Step order and STOP rules for the builder; size

1. **One worktree** off `f4412116` (or the newer `main` if the orchestrator says). The main checkout,
   `sandbox-pokebot/` code and the tuner's clone are READ ONLY. Confirm no lane is running before any live step. Every
   live run uses `AI_PLAYER_BUILD_ROOT` = the MAIN checkout's `sandbox-pokebot` (read only), and every throwaway profile
   and mirror build root lives under the run's own `--out`. No git writes and no commit (the orchestrator commits).
2. **Re-verify each finding on the worktree first**, with the probes in `s53/r1f/` (`probe_gates.py`,
   `probe_readbook.py`, `probe_launches.py`, `scan_exit_forms.py`, `scan_except.py`) and `s53/r1f/mine/`
   (`probe_plants_all.py`, `probe_plants_pc.py`, `scan_forms.py`). **STOP** if any result differs from section 1 (the
   code moved: re-anchor with the orchestrator).
3. Offline parts in this order, each with its tests and mutants green before the next:
   - (a) purity D1;
   - (b) controller + session + launcher row D2. First MEASURE the `reset_refusal` harness's two assumptions: that
     `context.emulator` can be set to a fake in a harness subprocess, and that case (3)'s first brain step raises.
     **STOP** if either fails, and respecify with the orchestrator;
   - (c) fairness D3;
   - (d) `read_book` D4 and `read_launches` D7;
   - (e) `judge_end` D5 and the launcher line (C230 regenerated);
   - (f) D6 in `goals.py` and `rate_step5.py`;
   - (g) the `live_r1` headline (V2-1, V2-2) with `LiveR1HeadlineTests`.

   Then: `call_census` → 0 MISSING with no new waiver; `revert_r1` all CAUGHT as predicted; `revert_step5`;
   `revert_safety_gates`; the quick lane. **STOP** if a new gate rule fires on the real package (section 1.1 measured
   zero, so a hit means the tree changed).
4. `live_r1.py` arms (section 5), the SaveWatch tail fix and the test-side reader. Fault-test the reader (FX1-built and
   CH1-built lines read wrong, real lines read right) before relying on it.
5. **Development `#57`, seeds 5501-5506** (ledger first):
   - (a) CONTROL, K-AFTER and K-INSIDE on all six. Record child B's arrival frames (and LAUNCH's) → set
     `R2_STOP_ARRIVAL`.
   - (b) CHAIN with the measuring caps on all six. Record: arrival → B's save `e4` → rule N's map → kill; B's maps
     before its arrival; whether the frozen lines were attached (they must not be). **STOP** if any map is recorded
     before the arrival that the arrival gating does not exclude. Set `CHAIN_B_FRAMES` and `CHAIN_B_TIMEOUT` at 2x.
   - (c) R2-RETRY and the three new OLD arms on all six; the existing arms on at least two seeds (rehearsal), with the
     grader run on them; the selftest's development rows.
   - **STOP and report** (never tune the AI's policy to the proof; never change `SAVE_MIN_MINUTES` or the moments) if:
     - CHAIN counts on fewer than 4 of 6 seeds;
     - step 1 of R2-RETRY does not stop on its arrival bound on any seed, or its purity verdict is not CLEAN;
     - any OLD arm fails to show on a seed where its twin counts;
     - a measured value contradicts orchestrator ruling 1's ranges beyond its variation;
     - the K-BETWEEN 'new' rule is vacuous on 2 or more seeds.
6. `live_r1.py selftest --all` green (the clean run PASSES; every planted fault, old and new, FAILS).
7. `ledger register --first 5551 --last 5554` (grep the ledger and evidence for 5551-5554 first: 0 hits), `ledger
   begin`, the plan, `verdict`, `ledger finish`, `ledger --check`. Hand back: the diff, the evidence, the numbers, which
   ruling-51 moments were seen live, and whether C4's restored `last_save` was exercised on any seed.
8. The orchestrator then runs an independent re-run on 5561-5564 and an adversarial review. Any fix re-runs EVERY arm on
   5571-5574, registered first, and its verification uses 5581-5584.

**Size (estimate):**
- AI and host code, about 135 lines: controller 25, session 15, launcher 45, `read_book` 8, goals 3, `__main__` 4.
- Gate rules (test side), about 95 lines: purity 55, fairness 40.
- Test side, about 1,400 lines: unit tests 420 (the harness included), `live_r1.py` 800 (five arms, the reader, the N
  rule, the tail fix, the headline, selftest cases), `revert_r1.py` 95, census mutants (generated).
- Live wall time: about 18 minutes for a 4-seed held-out plan at 12 parallel emulators (#55: 44 jobs, 583 s; the new arms
  add about 24 jobs, with CHAIN's child B the longest).

## 9. Out of scope

- The gym-leader save, live (it needs chapter 4's ROXANNE; unit-tested only, as `06` says).
- The users' U1 (the big-moment list) and U2 (a continue after a time-limit end).
- A live PLANT arm for the together-refusal through the real launcher. The `reset_refusal` harness runs the real
  `Session`, `Controller` and `Lifecycle` and writes the real verdict file, and the launcher's class is pinned on that
  reason, so a live plant adds no new path.
- FX5's guard, live (D10): this arm's two reasons are the same text. A live discriminator would need a step 1 whose host
  reason differs from its end line; FX5 stays unit-proven.
- `HarnessControls` (`gates/hands_harness.py:81`) does not refuse a together-press: the in-process harness is the TEST
  host, and ruling 52's enforcement is the deployed host's.
- A brain that catches the refusal and then never yields hangs until the launcher's wall clock: the pre-existing class
  of any non-yielding brain (D2).
- A per-line checksum in `memory.jsonl` (a schema change; a bit flip that stays ASCII is not detected), and
  `read_launches`'s own non-ASCII check beyond D7.
- A cap on retries (D5: R15's supervisor, not built).
- `memory.decisions` counting a save decision (D6: left on purpose).
- Reading the play time from `repr`/`str` of a `Progress` (textual parsing): neither gate judges text, and nothing does it.

## 10. Open questions

**Technical, all DECIDED here** (each goes to `06` with its rejected alternative): D1-D12. D2's `06` entry records that
NOT CLEAN is permanent for that game (only `--fresh`), why that is accepted (the same class as a purity breach under
ruling 52; INVOLUNTARY would hand the blocked reset its reload), and the rejected alternative.

**For the USER: one (goals, not blocking).** The build proceeds with the fail-closed answer. Only `_INVOLUNTARY`'s
membership changes if the user rules otherwise, and that would itself need a new mechanism, because INVOLUNTARY reloads.
`grep -i "NOT CLEAN"` over `06` finds only the R15 consequence line (`06:9901`), which is no ruling on an accidental
press. The question is in `user_questions`.

## 11. Revision log

| finding | lens | what was done | why |
|---|---|---|---|
| F1 (MAJOR) | code-host | APPLIED. The `reset_refusal` harness is respecified on the `harness_guarded_attacks` pattern: a Session with no `start()`, a fake emulator on `context`, `session._on_frame()` called by hand, and three cases plus two CONTROLs, each in its own subprocess. Step 3(b) MEASURES its two assumptions first, with a STOP | Confirmed: `session.py:200` `start()` calls `attribution.install()`, which raises with no emulator (`attribution.py:748-750`), and `test_host.py:572-580` records exactly that (`crash`/2) |
| F2 | code-host | APPLIED, by a gate rule, not `match_args=False`: D3 (d) refuses ANY class pattern with positional sub-patterns in deciding code (RULE C and A both); FAULT plant F12; mutant S46f; section 0 and 1.2 corrected | Re-run (`s53/r1f/mine/probe_plants_all.out`): `case Progress(_, ..., t)` passes both HEAD gates; the positive control `.play_time` fails RULE C. Measured: zero class patterns anywhere in the AI code, so the rule costs nothing and covers every class (flags and marks too) |
| F3 | code-host | APPLIED. D1 adds `yield`/`yield from`/`await` directly in a `finally`, and the names `ExitStack`/`AsyncExitStack`, with FAULT plants X16/X17 and mutants S40g (S40c covers the names). D2 is redesigned (latch; see proof-rulings F2), so "the play loop cannot catch it" no longer rests on D1 | Re-run: both plants pass the HEAD gate, and the pure-Python probes show the ExitStack swallowing `SystemExit(9)` and the finally-yield giving one frame. Measured zero uses |
| F4 | code-host | APPLIED. `MemoryTail` gains `start`; child B's tail starts at the frozen file's size; a save line attaches only with id ≥ the frozen `next_save_id`; C3 and C4 read B's line BY ID from the frozen file; selftest FAULT `stale_line_attached` | Confirmed: `live_r1.py:246` starts at 0, `:400-401` keeps the last frozen save line pending, and `:443-444` attaches it when its `frame` (child A's) ≥ B's emulator frame |
| F5 | code-host | APPLIED. `memory_check` keeps `if not allowed:` byte-identical (L7); its `classify_end` line changes, so C230 is regenerated against `judge_end` with a name map; section 6 lists every protected anchor (FX3, L7, S39, FX1) and has the builder enumerate anchors in edited functions before the change | Confirmed: C230's anchor is `    kind, words, allowed = classify_end(book, launches)\n` (`revert_r1_mutants.json`), L7's is `revert_r1.py:136-139`, and `make_copy` refuses a non-unique or missing anchor (`revert_r1.py:226`) |
| F6 (NIT) | code-host | APPLIED. The census list is split into AI-side census sites and test-side functions covered by hand-written mutants | Confirmed: `call_census.py:50` `SKIP_PARTS = ("gates", ...)` |
| F7 (NIT) | code-host | APPLIED. C3 compares `last_save` field by field (`id`, `play_time`) | Confirmed: `brain/saving.py:236-237` also carries `frame` and `why` |
| F8 (NIT) | code-host | APPLIED, all four: (1) section 0 part 7 and 1.7 row 7 now say the read is inside the `try` but only `FileNotFoundError` is caught; (2) the import command in 1.4 runs without `-I` from the copy's root; (3) D1 uses 3(a)'s rule (the loop exception is for `break`/`continue` only); (4) the NOT CLEAN return is cited at `launcher.py:428` | Each confirmed at HEAD (`launcher.py:278-281`, `:428`) |
| F1 (MAJOR) | proof-rulings | APPLIED. CHAIN moves to a COPY of K-INSIDE's frozen set (S1 continued while S2's line is the newest); the new mutant CH1 (`self.parent` = the newest line's id) is registered with its existing unit test (`test_saving.py:668`) and is CHAIN-OLD's tree; FX1 becomes CHAIN-R1-OLD. CORRECTED the finding's suggested positive evidence: under CH1 the rebuilt payload does NOT hold S2's maps (CH1 changes `parent` and `last_payload` together, so the delta still rebuilds B's own memory), so the evidence is the `parent` field (S2's id) | Confirmed: on K-AFTER `continued_from` = `newest_save()` and `next_save_id` = 1 + max (`game_memory.py:545-550`, `:733-735`); K-INSIDE keeps S1 with S2's line in the file (`live_r1.py:853`, `:932-940`) and counted 4/4 in all three held-out runs |
| F2 | proof-rulings | APPLIED, by the finding's second option: D2 LATCHES the controller, and the host finishes on the next `_on_frame` (or at the brain's return, crash or stray exit), never inside the brain's stack. D1 also refuses the finally-yield (code-host F3) | Re-ran `probe_yield_finally.py`: one ordinary frame after the exit began (CONTROL 0). The latch keeps `finish` on the path every other ending uses, and makes the refusal independent of any handler in the brain |
| F3 | proof-rulings | APPLIED. `held` becomes a read-only frozenset property over a private `_held`; new test `test_the_held_set_cannot_be_changed_from_outside` (FAULT + CONTROL); mutant L17 | Re-run: the plant `controls.held.clear()` then a Start tap passes both HEAD gates; the positive control `controls._held = set()` fails purity rule (d). Only `controller.py` and two test asserts (which hold for a frozenset) read `.held` |
| F4 | proof-rulings | APPLIED. C6's NONE halves (NEW_B_post, ABANDONED) are named consistency checks with no mutant, never cited as proof; C4's "restored last_save at work" counts only where B's own `[AI-SAVE] no save for ...: its last save was at <S1 stamp>` line exists, else it is reported "not exercised"; D8 no longer claims a non-empty set makes the check falsifiable | Confirmed: payloads live only in save lines (`game_memory.py:785-794`), and a later save passes the 3-minute check whether or not `last_save` was restored (`brain/saving.py:150-155`, `:170-171`) |
| F5 | proof-rulings | APPLIED. D10 and 5.2 say the launcher record is EXERCISED, not discriminated; FX5 is listed in section 9 | Confirmed: FX5 (`revert_r1.py:170-173`) drops the host reason, and in R2-RETRY both reasons start with `_CONTINUE_STOPPED` |
| F6 (NIT) | proof-rulings | APPLIED. Discriminators are stated as reported-only, with the rule "every pair differs on each seed where both of its arms count"; the count is now 9 per seed | Confirmed: `verdict_of` (`:1386-1420`) never reads `discriminators`, and FLOOR = 3 (`:94`) |
| F7 (NIT) | proof-rulings | APPLIED. FX1's arm is renamed CHAIN-R1-OLD and claims only "C3 can fail"; the continuation-specific OLD arm is CH1's | Confirmed: FX1 edits `mode.py`'s save line for every save |
| F8 (NIT) | proof-rulings | APPLIED. D2 records that NOT CLEAN is permanent, why that is accepted and the rejected INVOLUNTARY; `06` was grepped (only `06:9901`, no ruling on an accidental press); section 10 now carries one USER question, with the build proceeding fail-closed | A permanent loss of the game is a goals question for the user, not a technical one |
