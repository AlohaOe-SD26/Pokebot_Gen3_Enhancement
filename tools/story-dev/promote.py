"""PROMOTION TOOL — copy sandbox → custom under the project's own rules, and REFUSE if they are unmet.

‼‼ WHY THIS IS A TOOL AND NOT A CHECKLIST. Promotion has a documented procedure (measure first,
restore point BEFORE touching anything, copy, re-measure BOTH directions, verify by DRIVING and
never by a diff) — and on 2026-08-14 a hand-run promotion still shipped with a hole: the gate that
proved the promoted fix hard-coded `sandbox-pokebot` on its import path, so **nothing verified the
fix had actually landed in the other fork.** A prose checklist cannot notice that; a tool can
refuse. `CLAUDE.md`: *anything enforceable belongs in a GATE, not in prose.*

⛔ THIS TOOL DOES NOT DECIDE. Promotion is the USER's call, every time — it only executes an
already-approved one, and it fails closed on anything it cannot verify.

WHAT IT REFUSES TO DO (each of these is a real failure this project has paid for):
  * promote with a DIRTY working tree            — you could not tell afterwards what moved
  * promote without an annotated RESTORE POINT   — there would be no rollback target
  * promote while local and origin have diverged — the remote is the truth here
  * promote a file that is IDENTICAL             — a no-op promotion inflates a commit and lies
  * report success without RE-MEASURING drift in BOTH directions afterwards

WHAT IT STILL CANNOT DO, and says so: it cannot DRIVE the bot. A copy is not evidence. After this
returns, run a real driver against `--build custom` and paste the ACCEPTANCE line — that is the
standing rule and this tool prints the reminder rather than pretending to satisfy it.

    PYTHONUTF8=1 py -3.12 promote.py --self-test                   # fault-test THIS TOOL, touch nothing
    PYTHONUTF8=1 py -3.12 promote.py --check                       # measure only, change nothing
    PYTHONUTF8=1 py -3.12 promote.py --restore-point <tag> --go     # execute an approved promotion

Exit 0 = clean (or, with --check, drift measured). Exit 1 = refused or verification failed.
"""

import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
CUSTOM = REPO / "custom-pokebot"
#: ⛔⛔ THE COMPARISON SET, AND ITS LIMITS — SAY THEM, DO NOT IMPLY COVERAGE (2026-08-17, pass 2+3).
#: Two independent audit agents flagged the same thing: `drift: 0` reads like "the forks are
#: identical" and it means "the forks are identical IN `modules/` AND `plugins/`, over `*.py`".
#: It does NOT look at root scripts, `*.yml`, `profiles/`, `tests/`, `utility/` or `tools/`.
#: ‼ Both agents then diffed ALL of those by hand and found them byte-identical TODAY — so this is
#: a FALSE-CONFIDENCE risk, not a live gap. The fix is therefore honesty in the OUTPUT rather than a
#: wider comparison: widening it would sweep in `profiles/` (gitignored runtime state that is
#: SUPPOSED to differ) and start reporting drift that is not drift.
TREES = ("modules", "plugins")
SCOPE_NOTE = ("compared: modules/ + plugins/, *.py only  |  NOT compared: root scripts, *.yml, "
              "profiles/ (runtime, expected to differ), tests/, utility/, tools/")
BAR = "=" * 92


def _digest(path: pathlib.Path) -> str:
    """Content hash, NEWLINE-NORMALISED — and the normalisation is load-bearing, not cosmetic.

    ⛔⛔ THE FALSE DRIFT THIS REMOVES (measured 2026-09-15). This repo runs `core.autocrlf=true`,
    so a file git CHECKS OUT lands in the working tree with CRLF while the same file WRITTEN by a
    Python tool keeps LF. The two copies are then byte-different and blob-IDENTICAL:
        git rev-parse HEAD:custom-pokebot/.../higher_level_actions.py \
                      HEAD:sandbox-pokebot/.../higher_level_actions.py
        -> 08b92af10e79bc15d543e460c7859a7b0279d844  (BOTH)
    while this tool reported `drift: 1 file(s)` and `git status` was clean.

    ‼ WHY THAT IS SERIOUS AND NOT PEDANTRY. Four documents call this tool *the authority* on fork
    drift and tell agents to trust its number over any figure written into a doc. A permanent
    phantom 1 has exactly two outcomes, both bad: (a) an agent "promotes" it — a copy git records as
    NOTHING, i.e. the no-op promotion this module's own docstring says it REFUSES because it
    "inflates a commit and lies"; or (b) the reader learns the number is noise and stops reading it.
    `CLAUDE.md` rule 6: a gate with false positives is strictly worse than no gate.

    ⛔ NORMALISING IS NOT HIDING. A line-ending-only difference is still REPORTED — `measure()`
    returns it as its own third list and `main()` prints it on its own line. It is simply not
    counted as DRIFT, because for a Python file it cannot change behaviour: the tokenizer never
    sees the CR (PEP 278 universal newlines), so the two files compile to the same code object.
    The claim is CHECKED, not asserted — `--self-test` arm A proves a ONE-CHARACTER content change
    still reads as drift, and arm B proves a pure-CRLF pair does not.
    """
    raw = path.read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


def _raw_digest(path: pathlib.Path) -> str:
    """Byte-exact hash. Used ONLY where the claim being checked is literally "byte-identical"."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=60)


def measure() -> "tuple[list[str], list[str], list[str]]":
    """(differing/missing in custom, present only in custom, differing ONLY in line endings).

    ‼ BOTH DIRECTIONS. A one-way sweep cannot see a file that exists only in the target, which is
    how a promotion can silently leave orphaned code behind.

    ‼ THE THIRD LIST IS THE HONESTY CLAUSE (2026-09-15). `_digest` ignores line endings, so a
    CRLF/LF pair is no longer COUNTED as drift; this list is where it still gets SAID. Reporting a
    category and counting it are different things, and the difference is the whole point — an
    instrument that silently swallowed a category would be a worse instrument, not a better one.
    """
    differing, orphaned, eol_only = [], [], []
    for tree in TREES:
        for source in sorted((SANDBOX / tree).rglob("*.py")):
            if "__pycache__" in source.parts:
                continue
            rel = source.relative_to(SANDBOX)
            target = CUSTOM / rel
            if not target.exists():
                differing.append(str(rel).replace("\\", "/"))
            elif _digest(source) != _digest(target):
                differing.append(str(rel).replace("\\", "/"))
            elif _raw_digest(source) != _raw_digest(target):
                eol_only.append(str(rel).replace("\\", "/"))
        for target in sorted((CUSTOM / tree).rglob("*.py")):
            if "__pycache__" in target.parts:
                continue
            rel = target.relative_to(CUSTOM)
            if not (SANDBOX / rel).exists():
                orphaned.append(str(rel).replace("\\", "/"))
    return differing, orphaned, eol_only


def _refuse(reason: str) -> int:
    print(f"\n  ⛔ REFUSED — {reason}")
    print(BAR)
    return 1


def _self_test() -> int:
    """FAULT-TEST THE INSTRUMENT (2026-09-15). Exit 0 = every arm behaved; 1 = this tool is lying.

    ⛔⛔ WHY THIS EXISTS AT ALL. On 2026-09-15 `_digest` was changed to ignore line endings, to kill
    a phantom `drift: 1` that git itself did not see (one blob, two working-tree encodings). Every
    such change buys a reduction in false positives with a RISK of false negatives — the failure
    that matters far more here, because a missed drift means a fix silently never reached the fork
    that ships. `CLAUDE.md` rule 6 is explicit: FAULT-TEST every gate — prove it fails when the
    thing it guards is broken, and prove it does NOT fire on a mere cosmetic difference.

    ‼ IT EXERCISES THE REAL `measure()`, against real files on disk, by rebinding SANDBOX/CUSTOM at
    module scope. It deliberately does NOT re-implement the comparison: a self-test that re-derives
    the logic it is testing passes whenever the two derivations agree, including when both are
    wrong. That is the vacuous-gate shape this project has paid for repeatedly.

    ARM A is the CONTROL THAT MUST FIRE — one character apart, and it must still read as drift.
    Without arm A, a `_digest` that returned a constant would pass arms B and C perfectly.
    """
    body = "SENTINEL = 1\n\n\ndef f(a):\n    return a + SENTINEL\n"
    cases = [
        ("A  ONE CHARACTER of content differs  (the control that MUST fire)",
         body, body.replace("a + SENTINEL", "a - SENTINEL"), 1, 0),
        ("B  line endings differ, CRLF vs LF   (the false positive being removed)",
         body, body.replace("\n", "\r\n"), 0, 1),
        ("C  byte-identical",
         body, body, 0, 0),
        ("D  absent from custom entirely",
         body, None, 1, 0),
        ("E  content differs AND endings differ (must not be excused as cosmetic)",
         body, body.replace("a + SENTINEL", "a - SENTINEL").replace("\n", "\r\n"), 1, 0),
    ]

    global SANDBOX, CUSTOM
    keep_sandbox, keep_custom = SANDBOX, CUSTOM
    failures = []
    print(BAR)
    print("PROMOTE.PY SELF-TEST — does the drift meter still see what it must?")
    print(BAR)
    try:
        for label, src_text, dst_text, want_drift, want_eol in cases:
            with tempfile.TemporaryDirectory() as box:
                root = pathlib.Path(box)
                SANDBOX, CUSTOM = root / "sandbox", root / "custom"
                for side in (SANDBOX, CUSTOM):
                    (side / "modules").mkdir(parents=True)
                (SANDBOX / "modules" / "probe.py").write_bytes(src_text.encode())
                if dst_text is not None:
                    (CUSTOM / "modules" / "probe.py").write_bytes(dst_text.encode())
                differing, orphaned, eol_only = measure()
                got = (len(differing), len(eol_only))
                ok = got == (want_drift, want_eol)
                print(f"  {'PASS' if ok else 'FAIL'}  {label}")
                print(f"          drift={got[0]} (want {want_drift})   "
                      f"line-ending-only={got[1]} (want {want_eol})")
                if not ok:
                    failures.append(label)
    finally:
        SANDBOX, CUSTOM = keep_sandbox, keep_custom

    print()
    if failures:
        print(f"  ⛔ {len(failures)} ARM(S) FAILED — the drift meter is not measuring what it claims:")
        for label in failures:
            print(f"      {label}")
        print(BAR)
        return 1
    print(f"  ✅ all {len(cases)} arms behaved. A real change still reads as drift; a pure")
    print("     line-ending difference does not, and is reported separately instead.")
    print(BAR)
    return 0


def main() -> int:
    # ‼ FIRST, and before anything reads the real trees — the self-test must be runnable on a dirty
    #   tree, mid-refactor, at the exact moment you most need to know whether to trust the number.
    if "--self-test" in sys.argv:
        return _self_test()
    check_only = "--check" in sys.argv
    go = "--go" in sys.argv
    # ‼ `--strict` — added 2026-08-23 (`#24-p4residuals` (a)). Four documents call this tool "THE
    # authority" on fork drift, but `--check` ALWAYS returned 0 (the `check_only or not go` early
    # return below runs before any refusal), so the drift figure existed only as text a human had to
    # read. It could not be chained, put in a CI step, or made a gate.
    # ⛔ DELIBERATELY A SEPARATE FLAG, NOT A CHANGE TO `--check`. Drift is a NORMAL state — a
    # sandbox-only fix awaiting a promotion ruling has drift ≥ 1 and nothing is wrong. Making plain
    # `--check` exit non-zero would turn "work is pending the user's decision" into "the build is
    # broken", which is exactly the cry-wolf shape this project rates worse than no check at all.
    strict = "--strict" in sys.argv
    tag = None
    if "--restore-point" in sys.argv:
        index = sys.argv.index("--restore-point")
        if index + 1 < len(sys.argv):
            tag = sys.argv[index + 1]

    print(BAR)
    print("PROMOTION — sandbox-pokebot → custom-pokebot")
    print(BAR)

    differing, orphaned, eol_only = measure()
    # ‼ PRINT THE SCOPE BESIDE THE NUMBER. "drift: 0" reads as "the forks are identical"; it means
    # "identical in what this tool looks at". Two audit agents had to derive that from the source.
    print(f"  SCOPE: {SCOPE_NOTE}")
    print(f"  drift (sandbox → custom): {len(differing)} file(s)")
    for name in differing:
        print(f"      {name}")
    print(f"  orphaned (in custom only): {len(orphaned)} file(s)")
    for name in orphaned:
        print(f"      ‼ {name}")
    # ⛔ NOT drift — and SAID OUT LOUD rather than swallowed. Rationale in `_digest`.
    if eol_only:
        print(f"  line-ending-only (NOT drift, no behaviour difference): {len(eol_only)} file(s)")
        for name in eol_only:
            print(f"      ~ {name}")
        print("      ⇒ `core.autocrlf=true` materialised one copy with CRLF. git sees ONE blob;")
        print("        confirm with: git rev-parse HEAD:<custom path> HEAD:<sandbox path>")

    if check_only or not go:
        print("\n  (measure only — nothing was changed. Pass --restore-point <tag> --go to execute.)")
        if strict:
            n = len(differing) + len(orphaned)
            if n:
                print(f"  ⛔ --strict: {len(differing)} differing + {len(orphaned)} orphaned — exiting 1.")
                print("     (Drift is not itself an error; --strict is for callers that need a")
                print("      machine-readable 'the forks are identical' answer.)")
                print(BAR)
                return 1
            print("  ✅ --strict: 0 differing, 0 orphaned.")
        print(BAR)
        return 0

    # ---- REFUSALS, in the order that makes each one cheapest to fix --------------------------
    if not differing:
        extra = ""
        if eol_only:
            extra = (f"\n     ({len(eol_only)} file(s) differ in LINE ENDINGS only. That is NOT drift: git "
                     f"stores one blob for both\n      copies, so copying them would produce a commit "
                     f"containing nothing at all.)")
        return _refuse("there is nothing to promote — drift is already zero. A no-op promotion "
                       "would inflate a commit and claim work that did not happen." + extra)

    dirty = _git("status", "--porcelain").stdout.strip()
    if dirty:
        return _refuse("the working tree is DIRTY. Promote from a clean tree, so the resulting "
                       f"diff is exactly the promotion and nothing else.\n{dirty[:400]}")

    ahead_behind = _git("rev-list", "--left-right", "--count", "HEAD...@{upstream}").stdout.split()
    if len(ahead_behind) == 2 and ahead_behind != ["0", "0"]:
        return _refuse(f"local and origin have diverged (ahead {ahead_behind[0]}, behind "
                       f"{ahead_behind[1]}). The remote is the truth here — reconcile first.")

    if not tag:
        return _refuse("no --restore-point given. A promotion without a rollback target is not "
                       "reversible; create an annotated tag first and pass its name.")
    if _git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode != 0:
        return _refuse(f"restore point {tag!r} does not exist. Create it BEFORE promoting:\n"
                       f"      git tag -a {tag} -m \"...\" && git push origin {tag}")
    if _git("ls-remote", "--exit-code", "--tags", "origin", tag).returncode != 0:
        return _refuse(f"restore point {tag!r} exists locally but is NOT PUSHED. A rollback target "
                       f"that lives only on this machine is not a rollback target.\n"
                       f"      git push origin {tag}")

    # ---- execute ----------------------------------------------------------------------------
    print(f"\n  restore point verified (local + origin): {tag}")
    print("  copying:")
    for name in differing:
        source, target = SANDBOX / name, CUSTOM / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"      promoted {name}")

    # ---- verify: re-measure, both directions, and prove byte-equality per file ---------------
    after_differing, after_orphaned, _after_eol = measure()
    # ‼ `_raw_digest`, NOT `_digest`: the line below CLAIMS "byte-identical", and a claim is checked
    #   by the strictest reading of its own words. `shutil.copy2` copies bytes, so after a real
    #   promotion this is exactly true — and if it ever is not, the promotion is wrong.
    mismatched = [n for n in differing if _raw_digest(SANDBOX / n) != _raw_digest(CUSTOM / n)]
    print("\n  VERIFY")
    print(f"      drift after     : {len(after_differing)} (expected 0)")
    print(f"      orphaned after  : {len(after_orphaned)} (expected 0)")
    print(f"      byte-identical  : {len(differing) - len(mismatched)}/{len(differing)}")
    if after_differing or mismatched:
        return _refuse("post-copy verification FAILED — the trees are still not identical.")

    print("\n  ✅ COPY VERIFIED. Drift is zero in both directions.")
    print("\n  ‼ NOT DONE YET — A COPY IS NOT EVIDENCE. The standing rule is VERIFY BY DRIVING:")
    print("      PYTHONUTF8=1 py -3.12 story_harness.py <save> --driver <d> --build custom")
    print("      ...and paste the ACCEPTANCE line. Also run any --build-aware gates against")
    print("      custom (repro_box_counter_move_test.py, repro_pid_identity_key.py), because a")
    print("      gate that only ever imports sandbox cannot see whether the fix landed here.")
    print("  ‼ Then record it in custom-pokebot/DIVERGENCE-LOG.md and update the drift row.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
