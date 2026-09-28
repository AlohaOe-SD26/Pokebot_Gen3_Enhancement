# 2026-09-28 — `#27-ki47range` GRADED: KI-47's faint-chooser wedge is REPRODUCED, FIXED BY IDENTITY, and A/B-PROVEN

> Predictions: `2026-09-28-ki47range-PREDICTIONS.md` (`b11f327f`) and `...-PREDICTIONS-ADDENDUM.md` (`da891426`), both
> committed BEFORE the runs they grade. Driver `--driver ki47oor` on `r20_pregym1_party4_r116.ss1` (`9710585350be`,
> asserted each batch of runs), `--frames 30000`. Fixed code = `1dc3a8f3` (the runner verified HEAD and a clean tree).
> Evidence: `tools/story-dev/evidence/2026-09-28-ki47oor-{unfixed,FIXED,STALEMAP}-<arm>.txt`, `...-VOID-injection.txt`.
> Graded on the FIRST faint only (later faints in the same battle are observations, not graded).

## RESULTS — every graded reading matched its prediction

| Arm | Snapshot the handler used | Unfixed | Fixed (`1dc3a8f3`) | Fixed + `POKEBOT_KI47_FAULT_STALEMAP=1` |
|---|---|---|---|---|
| C0 (no write) | `012345` | 148 frames, sent the chosen Whismur | **148 frames** (≤ 1.5x ✅), chosen sent | (not run) |
| Wid (true order written) | `012345` | identical to C0 ✅ | identical to C0 ✅ | (not run) |
| **Foor** (stale enemy-shaped order) | `104523` | **FROZE**: 3,045 frames, KI-47 fault at 3,001, `{'A': 105, 'Down': 685}`, candidates `[0,4,5]`, `out_of_range=[4,5]` | **148 frames, chosen Whismur sent**, candidates `[1,2,3]` | **FROZE again**: 3,045 frames, `{'A': 105, 'Down': 685}`, `OUT OF RANGE [4, 5]` |
| Finr (in range, wrong) | `021345` | resolved, chosen sent (the 1↔2 swap never touches slot 3; the prediction said "may") | resolved, chosen sent ✅ | (not run) |
| **Swp** (NATURAL order, one real switch) | `210345` | **sent Poochyena#5815089E, NOT the chosen Whismur#7E9BB3BA** (154 frames) | **sent the chosen Whismur** (146 frames), found at menu slot 2 (field slot 0) | **sent Poochyena again** (154 frames) |

Premise conjuncts TRUE in every graded run:
- `injection_reached_snapshot`: the order of the CACHED object the handler receives == the written order == what
  `get_battle_state()` returns in the same frame;
- `premise_fainted_is_shedinja`;
- for `Swp`, `premise_swp`: the Shedinja fainted, the order is not identity, and field slot 0 != menu slot 2.

## WHAT IT PROVES

1. **The mechanism** (arm `Foor`, all three columns). A stale order in the entry snapshot makes the double-mapped
   sweep target unreachable slots at party 4, and the chooser freezes until the watchdog. The identity chooser resolves
   the SAME injected state in the ordinary 148 frames, and the fault arm brings the freeze back byte-for-byte (the same
   3,045 frames and the same press counts).
2. **The quieter bug** (arm `Swp`, all three columns). With NO injection, after one ordinary switch, the old sweep sent
   the WRONG living mon. The fixed code sent the chosen one, and the fault arm brings the wrong mon back.
3. **The identity premise, LIVE** (fixed `Swp`). With the menu open, `get_party()[2]` held Whismur, whose field slot is
   0; A on cursor 2 put `7E9BB3BA` on the field. So `get_party()` IS menu order while the menu is open, measured
   rather than inferred.
4. **No regression on the ordinary faint.** Fixed C0 = 148 frames = unfixed C0, with the same presses.
5. **The MULTI battle, the regression arm** (`--driver ki66faint` on `at_steven_2f.ss1`, the REAL Steven battle, fixed
   code; `evidence/2026-09-28-ki66faint-FIXED-identity.txt`). Sent == chosen on BOTH faints:
   - faint 1: `identity: chosen=Mightyena#5C96EA9B menu_slot=2`, then `A at cursor=2 pid=5C96EA9B`;
   - faint 2: `chosen=Swellow#0B30A747 menu_slot=3`, then `A at cursor=3 pid=0B30A747`, and the PARTY CHANGE puts
     Swellow in slot 0.
   The battle was `Won`, `[ch19b] ACCEPTANCE: PASS`, and the anchor is intact. Faint 1's snapshot held `031245`, a
   non-identity order; through the old double map that gives candidates `[1,3,4,5]`, exactly the 2026-08-17 run's
   set, in which the nominated Mightyena was NOT sent (Swellow was). The old "residual" is explained and gone.

## THE VOID FIRST ROUND (why the driver has a premise conjunct)

The first four unfixed runs never reached the handler (a per-frame cache, then `BattleState.__eq__` omitting the
order), and the first premise check read the driver's own object. Had they been graded, the falsifier "unfixed Foor
resolves" would have REFUTED a true mechanism. `08-MISTAKES.md` 2026-09-28; `evidence/...-VOID-injection.txt`.

## UNREGISTERED OBSERVATIONS (not graded)

- Unfixed `Swp`, the same battle's later faints:
  - faint 2: A on the fainted Shedinja first (refused), then SENT NINCADA instead of the chosen Whismur;
  - faint 3: walked three refused slots, 650 frames, before reaching Whismur.
  ⇒ On one natural battle, the old sweep chose wrong in 2 of 3 faints.
- The old `#24-faintchooser-fourthspace` "residual" (2026-08-17: Mightyena nominated, Swellow sent) is this bug. The
  closure is superseded in `06`.

## WHAT THIS DOES NOT SHOW

- A NATURAL enemy send-out: the stale order in `Foor` is injected. The natural evidence is the batch's 4 wedges, and
  the decomp (a NOTE: `SwitchPartyOrder` copies ANY battler's order into the global).
- FREQUENCY. The next batch answers that: expect 0 faint-chooser `KI-47 PARK` lines and no `‼ OUT OF RANGE` candidate
  lines.
- A multi battle's OWNER problem: the partner's benched mons are still candidates, exactly as before (the KI-66 owner
  filter is still OPEN). The game refuses them and the KI-38 refusal learning steps past them; on this run the chooser
  never asked for one.
- RESIDUAL, pre-existing and out of this diff's scope (found by the adversarial review, reasoned): on a RE-ENTRY with
  the menu already open, `LevelUpLeadBattleStrategy.choose_new_lead_after_faint` compares field-order `party_index`
  against menu-order `enumerate(get_party())`, so the strategy can nominate an on-field mon. The identity plan then
  finds that mon on the field and falls back to a living bench candidate, which is safe but is not the strategy's
  pick.
- KI-108 (`#27-battleeq`): the cache can serve a stale ORDER to other readers. This fix no longer consumes the order.
