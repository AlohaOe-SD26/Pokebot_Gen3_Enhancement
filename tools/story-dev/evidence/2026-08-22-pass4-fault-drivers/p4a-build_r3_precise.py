import shutil, pathlib
SCRATCH = pathlib.Path(r"C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/443dd07c-4fe2-4dd6-bef3-d8917e743ad5/scratchpad/p4a/fake_lint")
REAL_LINT = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement/tools/story-dev/lint_docs.py")
REGISTRY_TEXT = "POKEBOT_ENCOUNTER_BENCHMARK POKEBOT_STORY_DEBUG_TURBO POKEBOT_RNG_DECORRELATION_FRAMES\n"

def make_fake(name, docs):
    root = SCRATCH / name
    if root.exists(): shutil.rmtree(root)
    ts = root / "tools" / "story-dev"; ts.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_LINT, ts / "lint_docs.py")
    pk = root / "PROJECT KNOWLEDGE"; pk.mkdir(parents=True, exist_ok=True)
    (pk / "29-DISABLED-FEATURES-REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")
    (pk / "00-README.md").write_text("# 00 README\nno refs\n", encoding="utf-8")
    for fname, content in docs.items():
        (pk / fname).write_text(content, encoding="utf-8")
    return ts / "lint_docs.py"

# text.count("\n")+1 == n  =>  need exactly (n-1) newline chars, NO trailing newline
def exact_n(n):
    return "\n".join(f"line {i}" for i in range(1, n + 1))  # n-1 embedded \n, no trailing \n

def verify(n, text):
    reported = text.count("\n") + 1
    assert reported == n, f"generator bug: wanted {n}, formula reports {reported}"

for n in (900, 901):
    t = exact_n(n); verify(n, t)
    make_fake(f"r3_exact_{n}", {"04-HANDOFF.md": t})

for n in (3600, 3601):
    t = exact_n(n); verify(n, t)
    make_fake(f"r3_exact_{n}_punch", {"03-PUNCH-LIST.md": t})

# also: the "typical real file" case -- 900 lines of content PLUS the conventional trailing
# newline that git/editors enforce. This is what a human editor would call "900 lines".
def typical_n(n):
    return "\n".join(f"line {i}" for i in range(1, n + 1)) + "\n"  # trailing newline present

for n in (900,):
    t = typical_n(n)
    make_fake(f"r3_typical_{n}_trailing_nl", {"04-HANDOFF.md": t})

print("done")
