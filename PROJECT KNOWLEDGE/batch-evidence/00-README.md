# Batch evidence — the measurements, preserved

‼ **WHY THIS EXISTS.** `tools/story-dev/x4-runs/` is **2.2 GB and gitignored**. It holds 13
batches, each of which cost **3 hours of emulation**, and until 2026-08-04 it existed **only on
one machine**. Every conclusion in `07-CHANGELOG.md` and `05-KNOWN-ISSUES.md` rests on it.
Losing that directory would make the entire measured history unre-derivable.

This folder is the small, git-tracked subset that preserves the ANALYSIS:

| file | what it is |
|---|---|
| `MANIFEST.txt` | lanes, runs, finishes, commit, emulation assertion — the batch's identity |
| `summary.json` | finish rate, grouped end-reasons, canaries, per-lane detail |
| `mechanism-lines.txt` | every line the analyses actually grep for — badges, counter chain, PC rotation, KI-38/45/46/47 net hits, lead decisions, reachability refusals |

**1.4 MB total, versus 2.2 GB of raw stdout.** The raw logs stay where they are; this is the
part that cannot be regenerated and that every comparison depends on.

## The batches, and which are usable
| batch | commit | rate | status |
|---|---|---|---|
| 20260731-105549 | `289d1710` | 23.7% | baseline, pre-counter-chain |
| 20260731-140514 | `1b9e690f` | 30.8% | |
| 20260731-170603 | `3875843c` | 57.1% | **clean plateau** |
| 20260731-201554 | `92d220d5` | 60.0% | **clean plateau** |
| 20260801-075805 | `b7345ffd` | 47.1% | **clean plateau** |
| 20260802-160603 | `1700b965` | 5.4% | ‼ **VOID** — `#24-pc` ungated regression |
| 20260802-215519 | `09c6129e` | 26.9% | ‼ **VOID** — `#24-leadpolicy` (c) removed a winning lead |
| 20260803-063939 | `1811148a` | 45.8% | **clean plateau** |
| 20260803-105323 | `b726fcd6` | 37.0% | ‼ CONTAMINATED — 1 lane hung |
| 20260803-164713 | `d8879750` | 38.1% | ‼ CONTAMINATED — 2 lanes hung (H8 = 0 runs) |
| 20260804-062303 | `fe4a2369` | 38.5% | clean (all 8 lanes) |
| 20260804-1… | `32ba1dec` | 35.7% | clean (all 8 lanes) |

‼ **Clean plateau = 65/123 = 52.8%. Clean recent (last two) = 20/54 = 37.0%, z = −1.94.**
That decline is the open question the bisect exists to answer. **Never baseline against a VOID
or CONTAMINATED batch** — that mistake has been made twice.
