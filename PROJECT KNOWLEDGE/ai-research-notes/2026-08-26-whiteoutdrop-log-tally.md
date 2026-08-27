# NOTE — `#24-harnesswhiteoutdrop`: the 36-incident log tally (mined 2026-08-26)

> ⚠ **RESEARCH NOTE, NOT TRUTH.** One Claude explorer mined the profile debug logs
> read-only; the load-bearing claims below marked VERIFIED were re-checked in the main
> session against the named lines. The item in `03-PUNCH-LIST.md` stays OPEN; its recon
> paragraph should point here (pointer owed from the post-batch docs round, budget rule).

## The tally (agent-mined)

* **36 incidents** of `Player whited out. Switched back to manual mode.` across **27
  profile dirs** under `sandbox-pokebot/profiles/*/debug-logs/Story-debug-*.log`;
  `repro-ml` alone has 8, the rest 1-2 each. None in x4 lane logs.
* **100% of the transition lines read `[MODE] Story -> Manual`** — the mode NAME was
  Story in every incident.

## What that pins down (with the session's own verifications)

1. VERIFIED (`story_mode.py:1242-1255`): `StoryMode.on_whiteout()` **unconditionally
   returns True** (sets `_whiteout_pending`, sets the story-abort latch, prints its own
   recovery message). A real StoryMode instance can NEVER produce the generic drop.
2. VERIFIED (`_listeners.py:566-570`): the generic message + `set_manual_mode()` fire
   only when `bot_mode.on_whiteout()` returned falsy.
3. ⇒ **In all 36 incidents the object that received the event was NOT a StoryMode**,
   while the logged mode NAME said Story — a name/instance mismatch. The item's original
   "harness ran without a proper `bot_mode_instance`" diagnosis is re-confirmed as the
   shape, against the static sweep that found all 67 CURRENT driver branches assigning
   correctly (`story_harness.py:10284-10551`, else-fallback included, VERIFIED).

## Reconciling "all current branches assign" with "36 mismatches happened"

Surviving explanations, in order of likelihood — the next discriminating step:
* **The incidents predate the current assignment chain** (older harness revisions).
  Discriminator: incident file dates vs `git log` on `story_harness.py`'s chain.
* **The stack-non-empty window** (`:10286` — assignment only runs when
  `controller_stack` is empty, so a stale instance can persist across a mode change).
* A third path writing `context.bot_mode` name without instance (unswept).

⛔ Do NOT ship any fix from this note alone: pick the discriminator (dates first — it is
free), and any code change needs a driven whiteout repro per the standing craft rules.

## Date discriminator — RUN 2026-08-26 (same session)

Incident log dates: 2026-07-21 (2), 07-23 (4), 07-31 (3), 08-07 (2), 08-08 (2),
**08-09 (16)**, 08-10 (3), 08-14 (1), 08-15 (1), **08-17 (2)**.
⇒ **"historical only" is REFUTED** — incidents run through 2026-08-17, well inside the
mature-harness era. The stack-window and third-path candidates stay live, PLUS a fourth
raised by the data: the harness may run NON-StoryMode recon/repro drivers under the
mode NAME "Story", making some of the 36 EXPECTED for those drivers (no whiteout
recovery to inherit) — in which case the true fidelity defect is only the subset whose
driver subclasses StoryMode. **Next discriminator: per-incident DRIVER identity from
each log's run header** (one more read-only mining pass), THEN judge which incidents
are defects at all.

## Driver-identity pass — RUN 2026-08-26, agent tally CORRECTED in-session

An explorer classified all 36: **26 ran named NON-story drivers** (NormanCounterMode,
TeachFullMode, GroundSweepMode, PokenavSkip/RivalRetry/FaintRepro…) — those drops are
EXPECTED BY DESIGN (no story recovery to inherit), not defects. The remaining **10 were
labeled "real fidelity defects" on a SIGNATURE heuristic — that label is REJECTED here**:
* VERIFIED (`story_harness.py:2878-2929`): `StoryWhiteoutRecoveryMixin.on_whiteout`
  returns True and an `__init_subclass__` guard REFUSES any adopter that shadows it —
  so a mixin-carrying driver (SpaceCenter2Mode and its `Ki66FaintMode` subclass,
  `:3168`/`:3313`, mixin since 2026-08-12) cannot produce the generic drop while
  actually consulted.
* The flagged ki66single 08-17 log has only THREE `[STEP]` lines and drops at f143195 —
  consistent with an early build-iteration run or the harness DEFAULT `--driver spin`
  on that profile, both innocent.
* ⇒ the 10 are **UNRESOLVED, not confirmed defects** — and they are unresolvable from
  the logs because **the RUN HEADER never records `--driver`** (verified against a real
  header: build/mode/profile/rom/emulation lines only).

## ⇒ The item's concrete next steps (recorded for `03-PUNCH-LIST.md`)

1. **Add `driver: <args.driver>` to the harness run header** (2 lines) — makes every
   future incident self-classifying; prove with one harness boot (post-batch, it needs
   an emulator start). ⛔ Until it lands, no further mining can settle the 10.
2. Only after (1): re-judge any NEW incident; the 26 named-driver drops need no fix.
3. Optional hardening candidate (needs its own decision): non-story drivers COULD adopt
   the mixin, but "expected drop on a recon driver" may be the desired behavior —
   USER's call, do not build unilaterally.
