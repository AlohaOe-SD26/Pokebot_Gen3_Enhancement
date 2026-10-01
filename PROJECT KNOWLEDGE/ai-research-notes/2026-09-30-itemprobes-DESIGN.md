# 2026-09-30 — `#27-itemprobes`: step 14's battle-level item instruments, fixed against today's log lines — DESIGN + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** These are MEASUREMENT tools (tools/story-dev only; no production code). Fixing them
makes step 14 gradable; it measures nothing about the bot by itself.

**Why** (`03-PUNCH-LIST.md` `#27-itemprobes`; found by design v2 step 13's recon, `2026-09-30-doubleitems13-DESIGN.md`
§8): design v2 §Step 14 grades "B's key-battle win rate … on battle-level metrics (`probe_item_index_space.py`,
`probe_boss_healing.py`)". Both are blind on today's logs. Measured by the author on the batch0927 corpus (40 run logs,
`sandbox-pokebot/profiles/endless-P*/debug-logs{,/Old}/*.log` stamped 2026-09-27..28; scratch `itemprobes_measure.py`):
- **`probe_boss_healing.py`'s `TURN_RE`** ends `L(\d+) (\d+)/(\d+)\s*$`, so it drops every `[TURN]` line whose FOE carries a
  bracketed status suffix: of 134,768 `[TURN]` lines it parses 123,349. Of the 11,419 it misses, 4,788 end `vs ?` (no
  foe data: correctly unparseable) and ~6,600 end in a suffix such as `[FocusEnergy]`, `[Uproar/MultipleTurns]`,
  `[Sleep]`, `[Confused]`, `[Burn]` (real data lost).
- **`probe_item_index_space.py`** counts three line kinds (`landed using the X-order index`, `retrying with the …`,
  `both index spaces failed`) that KI-101's remap retired: the corpus has **0** of each. Its question (which index space
  the item menu uses) was answered by KI-101. Today's lines: `[ITEM] using` 114, `[ITEM] ✔ CONSUMED` 111, `[ITEM] status
  cure ✔ WORKED` 3, and 0 of `✔ landed (KI-101`, `NOT consumed — retrying once`, `NOT consumed twice; disabling`,
  `‼ no effect`, `status cure ‼ no change`, `KI-101 fresh-read failed`.
- **Both glob an `x4-runs/<stamp>/L0*` layout**; today's batches are `install_sandbox.py` endless lanes
  (`analyze_endless_batch.py` already selects them with `--since/--until`).
- **No battle is classified:** the corpus predates `[TRAINER]` (design v2 step 5, 2026-09-29), `[KEYBATTLE]` (step 6)
  and `[DBLITEM]` (step 13): 0 of each. Step 14's batch will have all three.

## DESIGN

- **D1. One shared, PURE parsing module** `tools/story-dev/battle_log.py` (no emulator, no file I/O in its core):
  - `select_logs(profiles_dir, since, until)` — the `analyze_endless_batch.analyse` rule (both `debug-logs/` and `Old/`,
    the day from the file name), with the profiles directory a PARAMETER (a worktree has no batch logs; default the
    main checkout's `sandbox-pokebot/profiles`).
  - `split_battles(lines)` — one record per battle, from `[BATTLE] started` to the next start; within it the
    `[TRAINER] start/end` fields (opp, class list, `double=`, `two=`, `res=`), the `[BATTLE] ended (outcome=…)` value,
    the `[TURN]` records, the `[ITEM]`, `[KEYBATTLE]` and `[DBLITEM]` lines.
  - `parse_turn(line)` — the FIXED pattern: an optional bracketed status suffix after the foe's HP is allowed; a `vs ?`
    line returns None and is COUNTED as "no foe data".
  - `item_kind(line)` — one kind per `[ITEM]` line, covering every kind above (today's and the three legacy ones), and
    `unknown` for anything else (counted, never dropped).
  - `key_class(classes)` — derived OFFLINE from the `[TRAINER]` class list against
    `sandbox-pokebot/modules/story/trainer_identity.KEY_TRAINER_CLASSES` (imported, the single source of truth; v2
    §Step 14 `[A-S3]`); `None` (UNCLASSIFIED) when a battle has no `[TRAINER]` line.
- **D2. `probe_boss_healing.py`** keeps its `x4-runs` stamp mode and its classes (LARGE ≥ 50 HP, the quarantined small
  class), adds `--since/--until/--profiles`, uses D1, and reports per battle class: key / non-key / unclassified (wild
  battles have no `[TRAINER]` line and are reported apart, as WILD, by the absence of a `[TRAINER] start` in a battle
  whose `[BATTLE] started` exists, never folded into "non-key").
- **D3. `probe_item_index_space.py` is RE-PURPOSED** (same name, because v2 §Step 14 names it): battle-level ITEM
  OUTCOMES per battle class and per outcome (won / lost / other): requests, consumed, landed, not-consumed retries and
  disables, no-effect, cures, unknown kinds; and from `[DBLITEM]`: menu passes / refusals (`ok`, `a_pressed`) and any
  `after` line where the PARTNER's HP rose (a wrong target). The legacy index-space verdict runs only when legacy lines
  exist. Its old docstring's history is kept, marked as historical.
- **D4. Positive controls stay** (files and bytes read, records parsed, "no data" ≠ "zero"), and each probe exits 1 on a
  control failure, 0 otherwise (a measurement, not a gate).
- **D5. The gate** `tools/story-dev/probe_itemprobes.py` (appended to `run_gates.py`): rows on REAL lines quoted
  verbatim from committed evidence (`evidence/2026-09-30-doubleitems13-ARMS.txt` and `-RERUN.txt`: `[TRAINER]`,
  `[TURN]` with `[Confused]`, `[ITEM] using`, `✔ CONSUMED`, the disable line, `[DBLITEM] menu/after` incl. P-NOG's
  partner rise, `[KEYBATTLE]`) plus the legacy and the `vs ?` shapes; each pure function's output pinned; mutants
  (the old `\s*$` anchor, a dropped kind, key derived from the wrong list, wild folded into non-key, a partner rise
  missed, a `vs ?` line parsed) each reddening its own rows. ⛔ After an adversarial mutant pass, as every gate here.

## PREDICTIONS (filed BEFORE any code; graded by running the fixed probes on the real corpora)

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| I1 | `probe_boss_healing.py --since 20260927 --until 20260928` (the main checkout's profiles) | 40 logs; exactly **129,980** turn records parsed (all 134,768 `[TURN]` lines minus the 4,788 `vs ?`), and 4,788 counted as "no foe data"; every battle UNCLASSIFIED or WILD (0 key, 0 non-key: no `[TRAINER]` lines) | any other count; any battle called key or non-key |
| I2 | `probe_item_index_space.py --since 20260927 --until 20260928` | 114 requests, 111 consumed, 3 cures worked, 0 unknown kinds, 0 legacy lines (so no legacy verdict), 0 `[DBLITEM]`; every item battle UNCLASSIFIED | any other count; an unknown kind; a legacy verdict printed |
| I3 | `probe_item_index_space.py` on the step-13 arms' full debug logs (scratch `d13arms2/`, via a path option) | P-ON: 1 request, 1 consumed, its battle NON-KEY (Hex Maniac + Collector), `[DBLITEM]` 1 pass, 0 wrong targets. P-NOG: 1 wrong-target `after` (Swellow 18→109). T-ON: 1 request, 1 consumed, its battle KEY (LEADER), 1 pass | any other classification or count |
| I4 | `probe_boss_healing.py` on the same arms logs (`d13arms2/`) | T-ON: 1 trainer battle, KEY (class 0x20 LEADER); 21 `[TURN]` lines, **15 parsed**, **6** counted as "no foe data" (`vs ?`); **0** opponent heals. P-ON: 37 `[TURN]` lines, 20 parsed, 17 `vs ?`; 0 heals. P-NOG: 27, 21, 6; 0 heals. T-OFF1: 16, 13, 3; 0 heals | any other count; a heal reported; a `[TURN]` line with foe data left unparsed |

(I3/I4's numbers were computed by the author from the scratch arms logs with the FIXED pattern before any code; the
builder adds a `--logs <glob>` option so a probe can be pointed at any set of logs.)
