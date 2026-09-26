# 2026-09-26 — `#24-ch23training` TINYPURSE ARM — PRE-REGISTERED PREDICTIONS (written BEFORE the drive)

> The code review of chunked training (APPROVE) named ONE designed-for path with zero direct evidence: a
> chunk's real-frame purse EXPIRING mid-`train_team`. Every chunk in the E1/E2 drives finished inside its
> purse. This arm forces it: `POKEBOT_CH23_FAULT_TINYPURSE=1` shrinks each chunk's purse to 30,000 frames.
> Drive: `post_ever_grande.ss1 --inject-hmmule --driver ch23train --frames 450000`.

| # | prediction | falsifier |
|---|---|---|
| T1 | chunks END with `finished=False` (the purse expired) — at least 2 of them | every chunk finishes ⇒ the purse never expired; the arm tested nothing |
| T2 | an expired chunk that banked EXP does **NOT** raise: each recorded chunk shows `exp > 0` and the NEXT chunk runs | a "banked NO EXP" raise on a chunk with exp > 0, or the loop stopping after the first expiry |
| T3 | after an expiry the next chunk re-resolves the SAME trainee by PID (the chunk table's `mon` is the Marill every time, including after it becomes Azumarill) and its `from` level ≥ the previous `to` | a different mon trained, or a "vanished" raise |
| T4 | the per-mon cap ends it LOUDLY: `FAILURE … reached only L<n> of L47 after 8 chunks`, with the chunk table in the message — OR, if 8 × 30k frames happens to carry the mule to 47, R-READY is NOT expected because the other battlers are trained next and each of THEIR chunks also expires … ⇒ in either case the run ends with a named reason, never a hang | a hang, a silent return, or an unnamed exception |
| T5 | 0 whiteouts; the lead is restored (the existing `except BaseException` path) — the driver's PRE/RESULT lines print | a whiteout, or no RESULT line |
