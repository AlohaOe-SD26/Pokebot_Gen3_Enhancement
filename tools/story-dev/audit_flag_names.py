"""Audit every flag/var name string used by story code against the emerald tables.
Phantom names silently read False/0 forever — find them ALL at once."""
import pathlib, re

ROOT = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot")
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

files = [
    ROOT / "modules/story/early_game.py",
    ROOT / "plugins/custom_modes/story_mode.py",
]
flag_call = re.compile(r"get_event_flag\(\s*[\"']([A-Z0-9_]+)[\"']")
var_call = re.compile(r"get_event_var\(\s*[\"']([A-Z0-9_]+)[\"']")
done_call = re.compile(r"_done\(\s*[\"']([A-Z0-9_]+)[\"']")

bad = []
for f in files:
    text = f.read_text(encoding="utf-8")
    for m in flag_call.finditer(text):
        if m.group(1) not in flags:
            bad.append((f.name, "flag", m.group(1)))
    for m in done_call.finditer(text):
        if m.group(1) not in flags:
            bad.append((f.name, "_done-flag", m.group(1)))
    for m in var_call.finditer(text):
        if m.group(1) not in evars:
            bad.append((f.name, "var", m.group(1)))

if bad:
    print("PHANTOM NAMES (silently False/0):")
    for row in sorted(set(bad)):
        print(f"  {row[0]}: {row[1]} {row[2]}")
else:
    print("all names valid")
print(f"(checked {len(files)} files against {len(flags)} flags / {len(evars)} vars)")
