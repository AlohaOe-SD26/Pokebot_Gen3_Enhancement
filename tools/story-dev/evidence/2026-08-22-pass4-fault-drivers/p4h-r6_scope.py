import re, pathlib
REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
flag_re = re.compile(r'["\'](POKEBOT_[A-Z0-9_]+)["\']')
def scan(roots, singles=()):
    f=set()
    for s in singles:
        if s.is_file(): f |= set(flag_re.findall(s.read_text(encoding="utf-8",errors="replace")))
    for r in roots:
        if not r.is_dir(): continue
        for py in r.rglob("*.py"):
            f |= set(flag_re.findall(py.read_text(encoding="utf-8",errors="replace")))
    return f
r6 = scan([REPO/"sandbox-pokebot"/"modules", REPO/"sandbox-pokebot"/"plugins", REPO/"tools"/"story-dev"],
          [REPO/"sandbox-pokebot"/"pokebot.py"])
cust = scan([REPO/"custom-pokebot"/"modules", REPO/"custom-pokebot"/"plugins"],
            [REPO/"custom-pokebot"/"pokebot.py"])
reg = (REPO/"PROJECT KNOWLEDGE"/"29-DISABLED-FEATURES-REGISTRY.md").read_text(encoding="utf-8",errors="replace")
print("R6-scanned flags:", len(r6))
print("custom-pokebot flags:", len(cust))
print("IN CUSTOM BUT INVISIBLE TO R6:", sorted(cust - r6))
print("R6 missing from registry:", sorted(f for f in r6 if f not in reg))
print("CUSTOM missing from registry:", sorted(f for f in cust if f not in reg))
# reverse direction: registry entries with no code reader anywhere
allcode = r6 | cust
regflags = set(re.findall(r'POKEBOT_[A-Z0-9_]+', reg))
print("REGISTRY-ONLY (no code reader):", sorted(regflags - allcode))
