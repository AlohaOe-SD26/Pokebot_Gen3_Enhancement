# PASS 4 FAULT-INJECTION DRIVERS — kept on purpose (2026-08-22)

These 37 scripts are the working drivers eight agents used to answer ONE question during deep
sanity check **PASS 4 (INFRASTRUCTURE)**: *can this gate actually fail?*

## Why they are committed rather than thrown away

Pass 4's most useful result was **negative**: most of the 21 suite gates that had no `--self-test`
turned out to fail correctly when their subject was genuinely broken. That is real, expensive
knowledge — and it was about to evaporate, because every demonstration lived in a temp directory.

⛔ **A gate proven to fail once, with no standing proof, decays into a gate nobody can trust.** That
is the whole content of `#24-gateselftests`, and these files are its starting material: porting a
driver into a `--self-test` block is a much smaller job than rediscovering how to fault the gate.

## What they are — and what they are NOT

* They are **not** tests, **not** wired into `run_gates.py`, and **not** maintained. Paths inside
  them point at temp directories that no longer exist; most need their `sys.path` / root constants
  re-pointed before they will run.
* They **are** a record of the injection TECHNIQUE per gate, which is the part that took the time:
  which production symbol to monkeypatch, which root constant to override, which arm discriminates.

## The technique they all share

None of them modified the repository. With eight agents running concurrently, in-place injection was
forbidden — a transient edit makes another agent's gate run falsely red. Instead each driver either
`import`s the gate module and **overrides its root/path constants** to point at a scratch tree, or
**monkeypatches the production function** under test before calling the gate's entry point.

## Notable ones

| file | what it proves |
|---|---|
| `p4f-harness.py` | the general "monkeypatch a production symbol, then run the probe, print its real exit code" harness. **The most reusable file here** — it is what showed three suite gates exiting 0 while printing their own alarms |
| `p4g-run_gates_mini*.py`, `p4g-g_*.py` | the runner's own failure modes: a gate that exits 1, crashes, exits 2, HANGS, is missing from disk, or lies `ALL PASS` on stdout while exiting 1 |
| `p4e-independent_impassable_count.py` | re-derives KI-59's 2658 / 401 / 144 / 98 / 58 figures with its OWN pointer-chase, bypassing the project's helpers entirely. The pattern for "check a published number without reusing the code that produced it" |
| `p4e-ki65_armc.py` | reproduces KI-65's documented residual (`party_index = -1` → the LAST party member, a wrong-mon rather than an exception). The basis of `#24-p4residuals` (f) |
| `p4d-fault_*.py` | monkeypatch-a-production-symbol drivers for the four behavioural gates |
| `p4h-r6_faultinject.py` | showed lint R6 never scanned `custom-pokebot` — 234 `.py` files invisible to the registry guard |
| `p4b-driver.py` | overrides `SAVES`/`MANIFEST` to scratch; found `verify_fixtures.py` blind to unlisted fixtures |

‼ **Before reusing one, re-derive its numbers.** These were true on 2026-08-22 against that day's
tree; several of the gates they target have since been changed by the very findings they produced.
