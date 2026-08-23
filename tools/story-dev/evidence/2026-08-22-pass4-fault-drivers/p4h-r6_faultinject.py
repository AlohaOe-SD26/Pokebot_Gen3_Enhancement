import re, pathlib
REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
flag_re = re.compile(r'["\'](POKEBOT_[A-Z0-9_]+)["\']')
# EXACT roots copied from lint_docs.py R6
bot_roots = [REPO/"sandbox-pokebot"/"modules", REPO/"sandbox-pokebot"/"plugins", REPO/"tools"/"story-dev"]
singles   = [REPO/"sandbox-pokebot"/"pokebot.py"]
walked = [p for r in bot_roots if r.is_dir() for p in r.rglob("*.py")] + [s for s in singles if s.is_file()]
under_custom = [p for p in walked if "custom-pokebot" in p.parts]
custom_py = list((REPO/"custom-pokebot").rglob("*.py"))
custom_py = [p for p in custom_py if "__pycache__" not in p.parts]
print(f"R6 walks {len(walked)} .py files; of those, {len(under_custom)} are under custom-pokebot/")
print(f"custom-pokebot/ actually contains {len(custom_py)} .py files -> ALL INVISIBLE to R6")
# FAULT INJECTION: simulate a flag that exists ONLY in the shipping fork.
INJECTED = "POKEBOT_SHIPPED_ONLY_KILLSWITCH"
fake_src = f'x = os.environ.get("{INJECTED}", "0")\n'
found_r6 = set()
for p in walked:
    found_r6 |= set(flag_re.findall(p.read_text(encoding="utf-8", errors="replace")))
# the injected flag lives in a custom-pokebot file, which R6 never opens:
found_with_custom = set(found_r6) | set(flag_re.findall(fake_src))
reg = (REPO/"PROJECT KNOWLEDGE"/"29-DISABLED-FEATURES-REGISTRY.md").read_text(encoding="utf-8", errors="replace")
print(f"R6 verdict on injected flag -> missing list = {sorted(f for f in found_r6 if f not in reg)}  (EXIT 0 = PASS)")
print(f"widened-scope verdict       -> missing list = {sorted(f for f in found_with_custom if f not in reg)}  (would FAIL)")
