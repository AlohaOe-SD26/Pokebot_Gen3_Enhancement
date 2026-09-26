# 2026-09-26 — USER RULING 17 (Amulet Coin) — GRADED: ALL NINE ARMS AS PREDICTED

> Grades `2026-09-26-ruling17-amulet-PREDICTIONS.md` (committed `76ba5bbd` BEFORE any drive; the A6 addendum
> committed `2497a2a2` after A1-A5 were graded and BEFORE A6 was driven; the B1/B2 addendum committed `b4e9ced6` BEFORE
> they were driven). Evidence, committed: `tools/story-dev/evidence/2026-09-26-amulet-{A1-GIVEN,A2-VACUITY-OWN-OUTPUT,
> A2b-OWN-OUTPUT-SKIP,A3-ERA-GATE,A4-ONETALK,A5-NOGIVE,A6-REGIVE,B1-BUDGET-WALK,B2-BUDGET-GIVE}.txt` (+ `.stdout.txt`),
> all captured on the FINAL code. Fixtures asserted (`norman_done` `e6fb7d5f36db`, pinned
> today; `post_mtpyre` `80602159694b`). All drives `HARNESS_EXIT_ON_MANUAL=1`. ⚠ Every arm was driven TWICE (once
> during the build, once on the final code) with identical output — **one trajectory, replayed**: a determinism
> check, not a replication.

| arm | prediction | reading | verdict |
|---|---|---|---|
| **A1 GIVEN** | PASS; order HOUSE→REGISTERED→RECEIVED→GIVEN→BACK; talks `[register, coin]`; MultipleRows; party menu opens; holder Blaziken#341D550A; 5k-30k frames | `ACCEPTANCE: PASS`, **5,927 frames**; talk 1 `registered (False→True)`, coins 0→0; talk 2 `received (False→True)`, coins 0→1; `give_context_task = Task_ItemContext_MultipleRows`; `give_party_menu True`; `give_slot_cursor 1`; no switch; `holder_end Blaziken#341D550A`; bag coins 0; end PETALBURG_CITY (20,18); `continue_path OK len=29` | ✅ |
| **A2 VACUITY (own output)** | FAIL on the premise | `PREMISE FAILED for expect=given (in_era=False, received=True, bag coins=0)` ⇒ `ACCEPTANCE: FAIL`, 0 frames | ✅ the grade cannot pass a no-op |
| **A2b** | PASS "nothing pending", no move | `amulet_coin = 'nothing pending'`, 0 frames, start == end | ✅ |
| **A3 ERA GATE** (`post_mtpyre`, badge 6, `pending()` True) | PASS "out of era", no move | `'out of era'`, 0 frames, still MT_PYRE_SUMMIT (23,7) | ✅ only the era gate stopped it |
| **A4 ONETALK** | PASS (recovery): registered, not received, soft failure, back | order HOUSE→REGISTERED→BACK; `'Mom did not hand over the coin after 1 talk(s) (RECEIVED=False, bag coins 0→0).'`; 3,656 frames | ✅ the coin is read from flag + bag, not from "we talked" |
| **A5 NOGIVE** | PASS (recovery): received, NOT given, coin in bag, back | order HOUSE→REGISTERED→RECEIVED→BACK; `holder_end None`; bag coins 1; `'the give did not land (holder now None; error None).'` | ✅ AC-GIVEN is read from the party |
| **A6 REGIVE** (A5's end state) | PASS: `AC-GIVEN, AC-BACK` only, no talks, < 3,000 frames | order `[AC-GIVEN, AC-BACK]`, talks `[]`, **580 frames**, Blaziken holds it, bag 0 | ✅ a failed give heals itself on the next `_play` pass |
| **B1 BUDGET-WALK** (`POKEBOT_AMULET_FAULT_BUDGET=800`) | expiry before the house; fallback walk back; OVERWORLD, no menu | `finished False`, order `[]`, no talks, `retry_return True`, end PETALBURG_CITY (20,18), `state_end OVERWORLD`, `menus_open_end []`, path east OK, 1,524 frames | ✅ the fallback walk works from mid-route |
| **B2 BUDGET-GIVE** (`=3050`) | expiry INSIDE the give; menu closed; walk back | expired after `give_slot_cursor 1` (context + party menu recorded, no `give_finished`); `menus_open_end []`, OVERWORLD, back in Petalburg. ⭐ The coin LANDED anyway (the game finished the give while the menu was being closed): `holder_end Blaziken#341D550A`, bag 0 ⇒ the next pass reads "nothing pending" | ✅ the review's risk #3 is closed, and driven |
| **G** `probe_amulet_coin.py` | PASS; every fault arm red | G1-G6 PASS; six built-in fault arms caught (moved-after-13a ×2, missing Petalburg map, lowest-level holder ×2, `-1` passthrough, a hand-spelled reading, an unread arm); a commented-out call does NOT change G1 | ✅ |

## WHAT THIS SETTLES
* ✅ The decomp reading of Mom's script is right on the live game: the first talk ONLY registers her in Match Call,
  the second hands over the coin (no yes/no anywhere; B rides both).
* ✅ The bag GIVE chain works as read: the Amulet Coin opens the 2×2 context grid, Right reaches GIVE, the party menu
  opens (which USE never would), and the game returns to the bag, then to the overworld.
* ✅ Segment 12d is gated to the Petalburg era, fails soft with a named reason in every tested failure, recovers to
  Petalburg in both fault arms, and a failed give is finished on the next pass without re-walking.

## CODE REVIEW (adversarial `reviewer`) — KICK-BACK ON DOCS ONLY; one risk turned into a driven fix

* BLOCKER: the tracking docs (07, 03, 04) did not yet record the build — they were being held for the review's
  outcome and land in the same commits (branch: code + 02/06/07/08/29; main: the 03/04 status).
* Risk 3 (budget expiring with a menu open skips the errand's own cleanup; worst case a stopped run): FIXED —
  `run_ch12d` closes menus (bounded) when `finished` is False, before the fallback walk — and DRIVEN (B1, B2).
* Risks 1-2 (female house, the switch yes/no) are the undriven branches listed below; both fail soft. Risk 4
  (`pick_holder` ties are decided by party order) is deterministic and harmless — both candidates are battlers.
* Ruled out by the reviewer, so nobody re-litigates: the guard cannot fire when the errand did not run; every
  `talk_to_npc` is frame-bounded; every `except` re-raises story aborts first; the decomp's context menu resets its
  cursor to index 0 on each open; no RSE wild species carries an Amulet Coin.

## WHAT IT DOES NOT SETTLE
* ⚠ **Whether the coin pays enough.** The ×2 applies only when the holder is SENT OUT (`battle_util.c:3294-3296`); a
  static top-level holder was measured SHORT on one whiteout-heavy replay in the recon. The batch's `[MONEY]` lines
  (F0) are the instrument; "move the coin to the entrant" is a separate item if they show it matters.
* ⚠ The **female** path (May's house, door (14,8)) — no fixture; the door comes from the recon's map read. The
  decomp is symmetric (May's 1F fires its neighbour scene on `HOUSES_STATE_BRENDAN == 1`, the rival-house counter
  for a female player), so no scene is expected at badge 5 — undriven.
* ⚠ The **switch** branch (a holder that already carries an item) — Blaziken held nothing.
* ⚠ Not yet run inside a whole organic `_play` — the next batch after the merge is the first.
