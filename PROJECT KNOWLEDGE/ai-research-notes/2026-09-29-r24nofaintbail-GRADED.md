# 2026-09-29 — USER RULING 24 step 5 GRADED: `POKEBOT_R24_NOFAINTBAIL` throws on after a faint and catches the Gulpin OFF abandons; the fault arm proves path (b) is what stops the next-turn bail; OFF is unchanged

> Predictions: `2026-09-29-r24nofaintbail-PREDICTIONS.md` (`3f1e6544`, before the code). Code: `db41db78`, telemetry fix
> `4161a1cb`. Every arm ran `storyresume` on `r20_badge1_party1_gym.ss1` with `POKEBOT_R20_OPENFENCE=1`,
> `--set-balls 60`, 240,000 frames and `random.seed(1)`. Evidence: `tools/story-dev/evidence/2026-09-29-r24nofaintbail-*.txt`
> (`-GRADER.txt` is the comparison against step 4's M0; `*-run1.txt` is the first run, kept as a record). Frames are
> debug-log frames.

## RESULTS (the re-run on `4161a1cb`) — every prediction held

| Arm | Env | Reading | Verdict |
|---|---|---|---|
| **OFF** | flag unset | **0 differing tracked lines** against M0 through f376701 (184 lines), including `[DEXCATCH-BAIL] a team member fainted` at f359393 and `bail=faint` at f359583; no `[DEXCATCH-NOBAIL]` line | ✅ OFF unchanged (one trajectory, replayed) |
| **ON** | `NOFAINTBAIL=1` | 0 differing lines before f359393. At the Zubat's faint: `[DEXCATCH-NOBAIL] … (fainted=1)` INSTEAD of the bail. `f359752 [TURN 10] Marshtomp L23 72/72 -> UseItem`, then `[CATCH] end kind=dex sp=Gulpin#316 end=caught res=Caught thrown=11 … dest=party party=4/6` | ✅ |
| **HALF** (fault) | + `FAULT_HALFBAIL=1` | the same `[DEXCATCH-NOBAIL]` line and send-in; then `f359752 [DEXCATCH-BAIL] a team member fainted`, `[TURN 10] Marshtomp … -> RunAway`, `[CATCH] end … end=bail thrown=10 … bail=faint` | ✅ path (a) alone still flees one turn later: the design's C5 finding, measured |

No arm has a traceback or a `[MODE]` change before f379500.

## FOUND BY THE FIRST RUN (`db41db78`): the per-faint line fired twice for one faint

- Run 1 behaved exactly as pre-registered in all three arms. But its `[DEXCATCH-NOBAIL]` line appeared at f359393 AND
  f359535 for the one Zubat.
- **Cause:** the battle handler calls `should_flee_after_faint` twice for one faint. The dispatcher re-enters
  `handle_fainted_pokemon` while the send-in completes: the party order flips at f359512 and back at f359534. The old
  bail line never showed this, because `_announce_bail` is idempotent.
- The docs claimed one line per faint. A batch counting faints would have double-counted.
- **Fix (`4161a1cb`):** the line is deduped on the number of fainted party members, which only a new faint changes, and
  carries `fainted=N`. Gate N7 plus the no-dedupe mutant F7.
- The re-run above shows one line. Run 1's files are kept (`*-run1.txt`). Recorded in 08.

## SEEN, NOT MEASURED (one trajectory)

- The Gulpin that ON caught at f360921 joined the party (4/6). In the rival fight that followed, run 1's log shows it
  on the field (`[TURN 7] Gulpin L12 … vs Grovyle L20`). This is the same "a fresh catch fights a boss" pattern step 3
  recorded for `#24-leadpolicy`. It is DATA for that item, not a proposal: option B is ruled out.

## WHAT THIS DOES NOT SHOW

- **How often a no-bail catch becomes a whiteout, and what that costs.** RULING 24 accepts the cost; the batch measures
  it.
- **The dependency on `POKEBOT_R24_CATCHHURT`.** As in step 4, C4 is keyed on that flag only, so the registry says to
  run the two together.
