#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every REGISTERED gate that boots an emulator must unthrottle it.

⛔ WHY THIS EXISTS — a MEASURED 16-day outage, not a hypothetical.
`repro_gym_whiteout_guard.py` set `context.audio = False` and `context.video = False` but not the
third line of that triple, `context.emulation_speed = 0`. Consequences, all observed:
  * `context.audio = False` only decides whether real samples or SILENCE are copied
    (`libmgba.py:593`). **The write is guarded by `if self._throttled:` alone** (`:618-621`), so a
    "silent" emulator still writes a frame of silence to the sound device every frame — and that
    BLOCKING WRITE IS THE 1× THROTTLE (the file says so at `:606-608`).
  * ⇒ the gate walked a long gym route AT REAL TIME. The suite's 900s bound is only ~54,000 frames
    at 60fps, so it was killed for being PACED, not for being stuck.
  * It was filed as `#26-gatestartupcontention` on 2026-08-26 and stayed red until 2026-09-11,
    during which NO full suite run could be green. Three separate 900s timeouts were logged, and
    the item's headline claimed "passes solo" while the handoff recorded a ~36-minute solo hang.
⭐ MEASURED A/B: throttled → killed at 900s (×3); `emulation_speed = 0` → **107s, EXIT=0, 5/5 pass**,
matching that gate's own documented 114s runtime.

‼ THE POINT OF A GATE HERE RATHER THAN A NOTE: the other five registered emulator gates had the
SAME omission and were passing, purely because their routes are short. A latent defect that only
surfaces when someone adds frames is exactly the kind prose does not catch — this project's rule 6.

⚠ SCOPE IS DELIBERATELY THE REGISTRY, NOT THE DIRECTORY. ~120 one-off recon probes in this folder
also construct emulators; they are not run by `run_gates.py`, are often interactive, and churning
them would make this gate noisy. A noisy gate teaches the reader to bypass it, which is strictly
worse than no gate.

Run:   cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gate_unthrottled.py
Fault: POKEBOT_UNTHROTTLED_FAULT=1  — pretend one compliant gate lacks the line; MUST go red.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / "run_gates.py"

#: Either spelling unthrottles. `context.emulation_speed = 0` is the idiom (`story_harness.py:126`,
#: and every batch lane via `x4_headless.py`'s `-s 0`); it routes to `set_throttle(False)`
#: (`context.py:99-102`). The direct call is accepted because it is exactly what the property does.
#: ⛔⛔ THESE MATCH AN ASSIGNMENT OR A CALL, NEVER A MENTION — corrected 2026-09-11 by a Tier 1 review.
#: v1 used `"emulation_speed" in src`, which a file satisfies merely by TALKING about the identifier
#: in a comment or docstring. `CLAUDE.md` rule 6 demands the opposite of both halves: a gate must
#: fail when the thing it guards is broken, and must NOT fire on mentions in prose. A substring test
#: fails the FIRST half silently — a gate that documents the rule in a comment and never obeys it
#: would have been waved through. Self-tests M1/M2 below pin this.
UNTHROTTLE_PATTERNS = (
    re.compile(r"^\s*(?:context\.)?emulation_speed\s*=", re.M),      # context.emulation_speed = 0
    re.compile(r"\.set_throttle\s*\(\s*False\s*\)"),                 # emulator.set_throttle(False)
)

#: A gate only needs this if it actually boots an emulator. Pure-static gates (AST/text checks) do not.
#: ⛔ ASSEMBLED AT RUNTIME, NEVER WRITTEN AS ONE LITERAL — and ⛔ do not spell the marker out anywhere
#: in this file, including in prose like this note. This file is itself in the registry it scans, so
#: the contiguous marker text appearing ANYWHERE here makes the gate MATCH ITSELF and report that it
#: boots an emulator. It did exactly that (found by a Tier 1 review, 2026-09-11) and passed only by
#: coincidence — its own docstring happened to contain the word `emulation_speed`. ⇒ a later edit to
#: this file's PROSE could have turned ENFORCING gate #54 permanently red against no real defect.
#: ‼ Self-test M7 pins this, and it FIRED on the first attempt at this very comment, which had
#: helpfully quoted the marker while explaining not to.
#: ‼ Belt AND braces: the scan also skips this file by name (see `main`). Two independent guards,
#: because a self-referential gate is the one shape that cannot be caught by testing other files.
BOOTS_EMULATOR = "Libmgba" + "Emulator("

FAULT = os.environ.get("POKEBOT_UNTHROTTLED_FAULT", "")


def registered_scripts() -> list[str]:
    """Gate filenames as they appear in the suite registry."""
    src = REGISTRY.read_text(encoding="utf-8")
    found = set(re.findall(r"""["']([a-z0-9_]+\.py)["']""", src))
    return sorted(found)


def self_test() -> int:
    """⛔ Pins the two shapes a substring test got wrong. Run: `--self-test`."""
    cases = [
        # (label, source text, must the file count as UNTHROTTLED?)
        ("M1 a real assignment satisfies it",
         "context.audio = False\ncontext.emulation_speed = 0\n", True),
        ("M2 a MENTION in a comment does NOT satisfy it",
         "# remember to set context.emulation_speed = 0 one day\ncontext.audio = False\n", False),
        ("M3 a MENTION in a docstring does NOT satisfy it",
         '"""This gate would need emulation_speed handling."""\ncontext.audio = False\n', False),
        ("M4 the direct call satisfies it",
         "context.emulator.set_throttle(False)\n", True),
        ("M5 set_throttle(True) is the OPPOSITE and must NOT satisfy it",
         "context.emulator.set_throttle(True)\n", False),
        ("M6 an indented assignment (inside a function) satisfies it",
         "def setup():\n    context.emulation_speed = 0\n", True),
    ]
    bad = 0
    for label, src, want in cases:
        got = any(p.search(src) for p in UNTHROTTLE_PATTERNS)
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label}: {'unthrottled' if got else 'THROTTLED'} "
              f"(expected {'unthrottled' if want else 'THROTTLED'})")
    # ⛔ And the self-referential guard, which is the reason this gate was nearly a landmine.
    own = Path(__file__).read_text(encoding="utf-8", errors="replace")
    self_matches = BOOTS_EMULATOR in own
    print(f"  {'PASS' if not self_matches else 'FAIL'}  M7 this file does NOT contain the literal "
          f"emulator-construction marker (it is assembled at runtime)")
    bad += 1 if self_matches else 0
    print(f"\n  SELF-TEST {'PASS' if not bad else 'FAIL'} ({bad} deviation(s))")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if not REGISTRY.exists():
        print("  ⛔ run_gates.py not found — cannot determine the registry.")
        return 2

    names = registered_scripts()
    me = Path(__file__).name
    checked: list[tuple[bool, str]] = []
    for name in names:
        if name == me:
            continue                  # ⛔ never scan self — see BOOTS_EMULATOR's note
        path = HERE / name
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        if BOOTS_EMULATOR not in src:
            continue
        ok = any(p.search(src) for p in UNTHROTTLE_PATTERNS)
        if FAULT == "1" and ok and not checked:
            # ⛔ Corrupt the VERDICT for the first compliant gate, not any file on disk: an arm that
            # edits source text can silently miss its target (that happened in this project on
            # 2026-09-10 and printed a false "did not reach the code").
            ok = False
        checked.append((ok, name))

    print("=" * 92)
    print("REGISTERED EMULATOR GATES MUST RUN UNTHROTTLED")
    print("=" * 92)
    print(f"  registry: {len(names)} script(s); {len(checked)} boot an emulator\n")
    for ok, name in sorted(checked, key=lambda r: (r[0], r[1])):
        print(f"    {'✅ unthrottled' if ok else '⛔ THROTTLED  '}  {name}")

    bad = [n for ok, n in checked if not ok]
    print()
    if not checked:
        print("  ⛔ NO registered gate boots an emulator — the detector is broken, not the tree.")
        print("=" * 92)
        return 1
    if bad:
        print(f"  ❌ FAIL — {len(bad)} registered gate(s) run at 1× real time:")
        for n in bad:
            print(f"       • {n}")
        print()
        print("  ⇒ add `context.emulation_speed = 0` beside that gate's `context.audio`/`context.video`")
        print("    lines. ⛔ Do NOT instead raise the suite's time bound: a bound raised to")
        print("    accommodate a defect stops being a bound.")
        print("=" * 92)
        return 1

    print(f"  ✅ PASS — all {len(checked)} registered emulator gate(s) unthrottle themselves.")
    print("=" * 92)
    if FAULT == "1":
        print("  ⛔⛔ FAULT ARM DID NOT REACH THE CHECK — this gate proves nothing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
