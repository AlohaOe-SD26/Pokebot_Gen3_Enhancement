"""Check the load-bearing save fixtures against `saves/FIXTURES.md5`. NO EMULATOR — seconds.

‼‼ WHY. On 2026-08-11 the same hazard cost three separate results in one day, all of them "same
filename, different bytes":
  1. the `#24-teachmsgstall` "cheap repro" stopped reproducing — `magma_door.ss1` had been
     re-captured by a `magmatravel` success hours after the failures were measured on it;
  2. KI-50 was published as "the chapter wins 1 in 3" — a RATE — when all three losing runs were
     byte-identical and the one win had been on different bytes of the same name;
  3. the KI-52 live A/B was VOIDED — the fixture was pinned *after* a still-in-flight background
     job overwrote it, and only the copy was md5'd, never compared to the failing run's md5.

Resolving to be careful did not work three times running. This makes the check mechanical.

RUN IT:
  * before trusting any result that rests on a fixture;
  * before and after any long driven run (drivers re-capture saves as a side effect);
  * at session start, alongside the git sync.

  PYTHONUTF8=1 py -3.12 verify_fixtures.py
  PYTHONUTF8=1 py -3.12 verify_fixtures.py --update    # ONLY when a change is intended

EXIT CODES: 0 all PINNED fixtures match; 1 a PINNED fixture drifted or is missing.
‼ VOLATILE entries are REPORTED but never fail the run — they are caches by design.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SAVES = HERE / "saves"
MANIFEST = SAVES / "FIXTURES.md5"


def md5_of(path: pathlib.Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse() -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    if not MANIFEST.is_file():
        raise SystemExit(f"missing manifest: {MANIFEST}")
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # md5 <2 spaces> name <2 spaces> kind <2 spaces> description
        parts = line.split("  ", 3)
        if len(parts) < 3:
            print(f"  ‼ unparseable manifest line, ignored: {line[:70]}")
            continue
        md5, name, kind = parts[0], parts[1], parts[2]
        note = parts[3] if len(parts) > 3 else ""
        rows.append((md5.strip(), name.strip(), kind.strip(), note.strip()))
    return rows


def assert_mode(args: list[str]) -> int:
    """`--assert name=md5prefix [...]` — REFUSE unless the named save is exactly those bytes.

    ‼‼ THIS IS THE FIX FOR THE MISTAKE THAT VOIDED AN A/B ON 2026-08-11. The wedging save was
    `magma_door.ss1` = `8171734228f3`. A still-in-flight background job overwrote it with
    `273d19b34d96`; I copied *that* to a "pinned" name, md5'd the COPY, and never compared it to
    the md5 of the run that had failed. Both A/B arms then ran on a save that does not reproduce
    the bug, and the result was meaningless.

    Pinning a fixture is not "copy the file now". It is **"copy the file AND assert its md5 equals
    the one the failure was measured on"** — and the assertion belongs IN the command that runs the
    measurement, not in a human's memory:

        py -3.12 verify_fixtures.py --assert magma_door_ki52.ss1=273d19b34d96 && \\
        py -3.12 story_harness.py magma_door_ki52.ss1 --driver magmahideout ...

    A prefix of any length is accepted, so 12 characters from a log line is enough.
    """
    ok = True
    for spec in args:
        if "=" not in spec:
            print(f"  ‼ bad --assert spec {spec!r}; expected name=md5prefix")
            ok = False
            continue
        name, want = spec.split("=", 1)
        path = SAVES / name.strip()
        if not path.is_file():
            print(f"  ‼ MISSING   {name} — cannot assert bytes for a file that is not there")
            ok = False
            continue
        got = md5_of(path)
        if got.startswith(want.strip().lower()):
            print(f"  OK         {name} = {got[:12]}")
        else:
            print(f"  ‼ MISMATCH {name}: expected {want.strip()}…, got {got[:12]}")
            print(f"             The save is NOT the one this measurement was defined against.")
            print(f"             A driver or a background job probably rewrote it. Do NOT run the")
            print(f"             measurement — recover the right bytes first.")
            ok = False
    return 0 if ok else 1


def main() -> int:
    if "--assert" in sys.argv:
        i = sys.argv.index("--assert")
        specs = [a for a in sys.argv[i + 1:] if not a.startswith("--")]
        if not specs:
            raise SystemExit("--assert needs at least one name=md5prefix")
        print("FIXTURE ASSERTION")
        return assert_mode(specs)

    update = "--update" in sys.argv
    rows = parse()
    if not rows:
        raise SystemExit("manifest parsed to zero entries — refusing to report success")

    failures: list[str] = []
    drifted_volatile: list[str] = []
    lines: list[str] = []

    for want, name, kind, note in rows:
        path = SAVES / name
        if not path.is_file():
            msg = f"MISSING   {name}"
            lines.append(f"  {msg}")
            if kind == "PINNED":
                failures.append(f"{name} is MISSING")
            continue
        got = md5_of(path)
        short_got, short_want = got[:12], want[:12]
        if got == want:
            lines.append(f"  OK        {name:<26} {short_got}  [{kind}]")
        elif kind == "VOLATILE":
            lines.append(f"  drifted   {name:<26} {short_got} (was {short_want})  [VOLATILE — expected]")
            drifted_volatile.append(name)
        else:
            lines.append(f"  ‼ DRIFT   {name:<26} {short_got} (expected {short_want})  [PINNED]")
            failures.append(f"{name}: {short_got} != {short_want}")

    print("=" * 88)
    print("FIXTURE VERIFICATION")
    print("=" * 88)
    for line in lines:
        print(line)

    if update:
        # ‼ Rewrite ONLY the md5 column, in place, preserving every comment and description. An
        # --update that reformatted the file would quietly destroy the reasoning it carries.
        text = MANIFEST.read_text(encoding="utf-8")
        for want, name, kind, note in rows:
            path = SAVES / name
            if path.is_file():
                text = text.replace(f"{want}  {name}", f"{md5_of(path)}  {name}")
        MANIFEST.write_text(text, encoding="utf-8")
        print("\n--update: manifest rewritten to the CURRENT bytes.")
        print("‼ Only correct if you INTENDED these fixtures to change. If a PINNED fixture")
        print("  drifted without you meaning it, a driver overwrote it — recover it, do not bless it.")
        return 0

    print()
    if drifted_volatile:
        print(f"NOTE: {len(drifted_volatile)} volatile cache(s) changed: {', '.join(drifted_volatile)}")
        print("      That is by design. ‼ But any measurement taken on the OLD bytes is now")
        print("      unreproducible — copy a volatile save to a PINNED name BEFORE measuring on it.")
    if failures:
        print(f"\n‼ FAILED — {len(failures)} PINNED fixture(s) are not what the manifest says:")
        for f in failures:
            print(f"    - {f}")
        print("\n  Do NOT trust any result resting on these until they are recovered or the change")
        print("  is understood. `--update` blesses the current bytes; only use it deliberately.")
        return 1
    print("ALL PINNED FIXTURES MATCH.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
