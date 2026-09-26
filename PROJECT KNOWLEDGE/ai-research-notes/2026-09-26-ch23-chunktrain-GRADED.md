# 2026-09-26 — `#24-ch23training` CHUNKED TRAINING — GRADED: ALL FIVE PREDICTIONS CONFIRMED

> Grades `2026-09-26-ch23-chunktrain-PREDICTIONS.md` (committed `878dbb3d` BEFORE any drive). Evidence,
> committed: `tools/story-dev/evidence/2026-09-26-ch23chunk-{E0a-CONTROL-ESTIMATE,E0b-MULE-ESTIMATE,
> E0c-NOCHUNK-ESTIMATE,E1-MULE-FULL,E2-CONTROL-HEAD,E2-CONTROL-NEW}.txt` (+ `.stdout-excerpt.txt`).
> Fixture `post_ever_grande.ss1` (md5 `18203e997edc`), `--driver ch23train`, harness now installing
> `SwapTrainBattleStrategy` exactly as production does.

| # | arm | prediction | reading | verdict |
|---|---|---|---|---|
| E0a | CONTROL, estimate-only | nothing chunked; every battler one chunk to 47 | `train_chunked=[]`, `train_plan={Swellow:47, Wailmer:47, Mightyena:47}` | ✅ |
| E0b | MULE, estimate-only | no refusal; the Marill chunked; first chunk L32 | `train_chunked=['Marill#…']`, `train_plan[Marill]=32`, `trained='ESTIMATE ONLY'` | ✅ |
| E0c | MULE + `NOCHUNK` | the organic refusal text | `Marill#… alone needs 406,972 frames, over the 250,000 per-call ceiling …` | ✅ verbatim |
| E1 | MULE, FULL | `R-READY`; mule ≥ L47 as Azumarill; ≥2 chunks each banking EXP; 0 whiteouts; money unchanged | `R-READY`, `missing=[]`; **Marill L13 → Azumarill L47 in 3 chunks** (13→32: 205,293 f / +24,474 EXP · 32→40: 161,154 f / +25,504 · 40→47: 113,872 f / +31,465), every chunk `finished=True`; the other three one chunk each; **257 battles, 0 whiteouts**, `train_money_dropped=None` (₽38,893 throughout) | ✅ |
| E2 | CONTROL FULL, HEAD vs NEW `victory_road.py` | **BIT-IDENTICAL** | same `train_post`, 118 battles each, **the md5 of every battle-start frame stamp is identical**, both end at **f371647** | ✅ |

## What this settles

* ✅ The refusal that ended 30 of 39 organic badge-8 runs is replaced by a bounded climb that WORKS on the
  exact failing shape: a L13 HM mule in an otherwise-ready party reaches L47 with zero whiteouts.
* ✅ **Identity by PID survived evolution** inside chunk 1 (Marill → Azumarill at L18) — the old
  `(pid, species)` lookup would have raised "vanished".
* ✅ **The ordinary path is provably unchanged** (E2, frame-exact): a party with no over-ceiling mon trains
  exactly as before, so no other run's training moved.
* ✅ The skip-the-fix arm reproduces the organic death verbatim ⇒ the chunking is LOAD-BEARING.
* ⭐ Cost measured: the mule's whole climb was **480k real frames** (≈2.2 h at ×1), below my 0.66M estimate.

## What it does NOT settle

* ⚠ One fixture, one party, one trajectory per arm (rule 8). The ORGANIC frequency — how many badge-8 runs
  now get past §Ch23 — is `#26-batch0926`'s question, and the next blocker after §Ch23 is `#26-ch24organic`.
* ⚠ Not driven: the L26-37 team-member class (the planner covers it — `probe_ch23_chunk_plan.py` C1 — but
  no drive), a whiteout during training, the no-finisher refusal in a drive. *(A purse expiry mid-chunk WAS
  listed here — ✅ now DRIVEN, see the TINYPURSE addendum below.)*

## ADDENDUM — the TINYPURSE arm (the path the code review found undriven), graded

Predictions `2026-09-26-ch23-tinypurse-PREDICTIONS.md` (committed `da78c3c9` before the drive). Evidence
`tools/story-dev/evidence/2026-09-26-ch23chunk-T-TINYPURSE.txt`. `POKEBOT_CH23_FAULT_TINYPURSE=1` (30,000-frame
chunk purse), `--inject-hmmule`.

| # | prediction | reading | verdict |
|---|---|---|---|
| T1 | ≥2 chunks end `finished=False` | **all 8** chunks `finished=False` (30,031-32,883 frames each) | ✅ |
| T2 | an expired chunk that banked EXP does not raise; the next runs | every chunk `exp > 0` (+2,244 … +4,526); the loop continued through all 8 | ✅ |
| T3 | the same trainee re-resolved by PID after every expiry, levels monotonic | every row `Marill#670A87E8`, `species_now=Azumarill` from chunk 1 on; levels 13→19→23→26→28→30→31→33→34 | ✅ |
| T4 | the per-mon cap ends it LOUDLY | `FAILURE … Marill#670A87E8 reached only L34 of L47 after 8 chunks. Chunks: [...]` | ✅ |
| T5 | 0 whiteouts; the verdict prints | `whiteouts=0`, RESULT lines printed | ✅ |

⇒ the settle-after-expiry → re-resolve-by-PID → partial-EXP → loud-cap path is now DRIVEN, not reasoned.
