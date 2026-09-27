"""DRY-RUN of the proposed `#24-promotedpairgate` check — run BEFORE anyone builds it.

Two things this is trying to learn, and the second matters more than the first:
  1. does any STALE status claim survive in 04-HANDOFF today?
  2. would the proposed rule FALSE-POSITIVE on this project's dated retraction style? A gate with
     false positives is the one CLAUDE.md rates worse than no gate at all, so if the answer is yes,
     the proposal has to change before it is written.
"""
import pathlib, re

REPO = pathlib.Path(__file__).resolve().parents[2]
KI_FILE = REPO / "PROJECT KNOWLEDGE" / "05-KNOWN-ISSUES.md"
HANDOFF = REPO / "PROJECT KNOWLEDGE" / "04-HANDOFF.md"

DONE_WORDS = ("PROMOTED", "FIXED", "CLOSED", "RESOLVED", "SOLVED")
STALE_WORDS = ("NOT PROMOTED", "STILL OPEN", "AWAITING", "UNPROMOTED", "NOT YET PROMOTED")
#: this project deliberately preserves superseded wording inside dated retraction markers.
RETRACTION = ("*(This clause read", "*(This read", "*(it was", "*(was ", "SUPERSEDED", "RETRACTED",
              "\u26d4 **THE TEXT BELOW IS HISTORY", "(This row read", "*(The superseded",
              "*(the 2026-", "*(This cell read", "*(This clause expected")

ki_status = {}
for line in KI_FILE.read_text(encoding="utf-8-sig").replace("\r\n", "\n").splitlines():
    if line.startswith("## ") and "KI-" in line:
        m = re.search(r"KI-(\d+)", line)
        if m:
            head = line.upper()
            ki_status[m.group(1)] = any(w in head for w in DONE_WORDS)

hand = HANDOFF.read_text(encoding="utf-8-sig").replace("\r\n", "\n").splitlines()
real, excused = [], []
for i, line in enumerate(hand, 1):
    U = line.upper()
    for ki, is_done in ki_status.items():
        if not is_done or f"KI-{ki}" not in line:
            continue
        for sw in STALE_WORDS:
            if sw not in U:
                continue
            # window: the retraction marker must be near the stale phrase, not merely in the line
            pos = U.index(sw)
            window = line[max(0, pos - 420): pos + 420]
            if any(r.lower() in window.lower() for r in RETRACTION):
                excused.append((i, ki, sw))
            else:
                real.append((i, ki, sw, line[max(0, pos - 150): pos + 150]))

print("=" * 96)
print(f"DRY-RUN: {len(ki_status)} KI headers parsed, "
      f"{sum(1 for v in ki_status.values() if v)} marked done")
print("=" * 96)
print(f"\nREAL FINDINGS (un-excused stale claims): {len(real)}")
for i, ki, sw, ctx in real:
    print(f"  04-HANDOFF.md:{i}  KI-{ki} is DONE but the line says {sw!r}")
    print(f"      ...{ctx.strip()}...")
print(f"\nEXCUSED BY A NEARBY RETRACTION MARKER: {len(excused)}")
for i, ki, sw in excused[:12]:
    print(f"  04-HANDOFF.md:{i}  KI-{ki} {sw!r} — inside a dated retraction, correctly ignored")
print("\n" + "=" * 96)
if real:
    print("  \u26d4 the proposed gate WOULD FIRE on live text today.")
elif excused:
    print("  \u2705 clean, AND the retraction-exemption did real work "
          f"({len(excused)} would-be false positives suppressed) \u21d2 the exemption is REQUIRED,")
    print("     not decorative. A naive version of this gate would have been noisy on day one.")
else:
    print("  \u2705 clean, but NOTHING exercised the retraction exemption \u2014 so this dry run does NOT")
    print("     show the gate is safe against this project's retraction style. Say so when filing.")
print("=" * 96)
