"""Audit every flag/var name string used by story code against the emerald tables.
Phantom names silently read False/0 forever — find them ALL at once."""
import pathlib, re

# ‼ DERIVED FROM THIS FILE'S LOCATION, never hardcoded (fixed 2026-08-22, sanity check PASS 4).
# This was an ABSOLUTE `C:\Remote Projects\...` path in a project whose own CLAUDE.md says it is
# "worked on from multiple computers". On any machine with a different checkout path this standing
# gate would have died on FileNotFoundError; worse, on a machine that HAS that path but is working
# in a second clone it would have silently audited the WRONG TREE and reported PASS — a
# right-answer-to-the-wrong-question, which this project has been bitten by before.
ROOT = pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot"
flags = set()
for line in (ROOT / "modules/data/event_flags/emerald.txt").read_text().splitlines():
    parts = line.split()
    if len(parts) >= 2:
        flags.add(parts[1])
evars = set()
for line in (ROOT / "modules/data/event_vars/emerald.txt").read_text().splitlines():
    parts = line.split()
    if len(parts) >= 2:
        evars.add(parts[1])

# ‼ EVERY story module, DISCOVERED not listed. This audit ran for weeks against exactly two
# hand-written paths while the chapters moved OUT of `early_game.py` into `modules/story/*.py`
# (§Ch18 `mossdeep_gym.py`, §Ch19 `space_center.py`, `pc_trip.py`, `counter_hunt.py`, ...). Those
# files were therefore NEVER audited, which is precisely the coverage this gate exists to provide:
# a phantom name reads False/0 in silence forever, so an unaudited completion check is a chapter
# that can never pass and never says why. Found 2026-08-12 while building §Ch19 — the names were
# all real, but nothing had been checking. A glob cannot go stale as the code moves.
files = sorted((ROOT / "modules/story").glob("*.py"))
files += [
    ROOT / "plugins/custom_modes/story_mode.py",
]
flag_call = re.compile(r"get_event_flag\(\s*[\"']([A-Z0-9_]+)[\"']")
var_call = re.compile(r"get_event_var\(\s*[\"']([A-Z0-9_]+)[\"']")
done_call = re.compile(r"_done\(\s*[\"']([A-Z0-9_]+)[\"']")

# ‼ THE NAME IS USUALLY NOT AT THE CALL SITE. The house idiom is a module constant —
# `BADGE_FLAG = "BADGE07_GET"` ... `get_event_flag(BADGE_FLAG)` — and a literal-only regex sees
# NOTHING there. Measured 2026-08-12: with the file list widened to all 19 story modules,
# `mossdeep_gym.py` still reported 0 names while gating §Ch18 on BADGE07_GET, and
# `space_center.py` reported 1 of its 2. So the audit was blindest exactly where it matters most:
# the COMPLETION MARKERS, the names whose silent False/0 makes a chapter unable to ever pass.
# Resolving `CONST = "LITERAL"` one level is enough for every current call site, and a constant
# that cannot be resolved is REPORTED rather than skipped — an unresolvable name is unaudited,
# and unaudited must never look like audited.
const_def = re.compile(r"^(_?[A-Z][A-Z0-9_]*)\s*(?::\s*str\s*)?=\s*[\"']([A-Za-z0-9_]+)[\"']", re.M)
flag_call_const = re.compile(r"get_event_flag\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")
var_call_const = re.compile(r"get_event_var\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)")

bad = []
checked = []          # (path, how many flag/var names that file actually contained)
total_names = 0
dynamic = 0           # call sites whose name is a function PARAMETER — unauditable by design
for f in files:
    text = f.read_text(encoding="utf-8")
    found = 0
    for m in flag_call.finditer(text):
        found += 1
        if m.group(1) not in flags:
            bad.append((f.name, "flag", m.group(1)))
    for m in done_call.finditer(text):
        found += 1
        if m.group(1) not in flags:
            bad.append((f.name, "_done-flag", m.group(1)))
    for m in var_call.finditer(text):
        found += 1
        if m.group(1) not in evars:
            bad.append((f.name, "var", m.group(1)))

    # --- names reached through a module constant (see `const_def` above) ---
    consts = {m.group(1): m.group(2) for m in const_def.finditer(text)}
    for rx, kind, table in ((flag_call_const, "flag-via-const", flags),
                            (var_call_const, "var-via-const", evars)):
        for m in rx.finditer(text):
            ident = m.group(1)
            if ident not in consts:
                # ‼ TWO DIFFERENT THINGS LOOK THE SAME HERE, and conflating them makes the gate
                # noise. A lower-case identifier (`flag_name`, `badge`, `var`) is a FUNCTION
                # PARAMETER of a generic helper — dynamic by design, unauditable statically, and
                # not a defect. An UPPER_SNAKE identifier is meant to be a module constant, so
                # failing to resolve one IS a real coverage gap. Count the first, report the
                # second. (A gate that cries wolf is a gate that gets ignored — which is how the
                # original two-file version survived so long.)
                if ident.lstrip("_").isupper():
                    bad.append((f.name, f"UNRESOLVED-{kind}", ident))
                else:
                    dynamic += 1
                continue
            found += 1
            if consts[ident] not in table:
                bad.append((f.name, kind, f"{ident}={consts[ident]!r}"))

    checked.append((f, found))
    total_names += found

if bad:
    print("PHANTOM NAMES (silently False/0):")
    for row in sorted(set(bad)):
        print(f"  {row[0]}: {row[1]} {row[2]}")
else:
    print("all names valid")

# ‼ PRINT WHAT WAS SEARCHED, AND HOW MANY NAMES IT FOUND. "all names valid" over zero files, or
# over the wrong files, is indistinguishable from a real pass — which is exactly how this audit
# silently stopped covering the chapters. The per-file name count makes an empty scan visible.
print(f"(checked {len(files)} files against {len(flags)} flags / {len(evars)} vars; "
      f"{total_names} name(s) resolved, {dynamic} dynamic call site(s) skipped)")
for f, n in sorted(checked):
    print(f"  {n:4d} name(s)  {f.relative_to(ROOT).as_posix()}")
if total_names == 0:
    print("‼ ZERO flag/var names were found in ANY file — this audit checked nothing. Exit 1.")
    raise SystemExit(1)

# ‼ A GATE THAT DOES NOT REFUSE IS A REPORT. This printed its phantom list and then exited 0,
# so any caller that checked the status code — the house rule is to check the status code, never
# to grep the text — saw a PASS. That is the same shape as the bug it hunts: a failure that reads
# as success in silence. (The project's hardening direction: advisory rules become code that
# refuses.) Exits 1 so it can be chained into a build/verification command.
if bad:
    raise SystemExit(1)
