import shutil, pathlib

SCRATCH = pathlib.Path(r"C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/443dd07c-4fe2-4dd6-bef3-d8917e743ad5/scratchpad/p4a/fake_lint")
REAL_LINT = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement/tools/story-dev/lint_docs.py")

REGISTRY_TEXT = """# 29 Disabled Features Registry (fake, for lint_docs self-test)
POKEBOT_ENCOUNTER_BENCHMARK - measured, pinned off
POKEBOT_STORY_DEBUG_TURBO - measured, pinned off
POKEBOT_RNG_DECORRELATION_FRAMES - measured, pinned off
"""

README_TEXT = "# 00 README\n\nThis is a fake reading order doc with no file references.\n"

def make_fake(name: str, docs: dict[str, str], include_registry=True, include_readme=True):
    root = SCRATCH / name
    if root.exists():
        shutil.rmtree(root)
    ts_dir = root / "tools" / "story-dev"
    ts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_LINT, ts_dir / "lint_docs.py")
    pk = root / "PROJECT KNOWLEDGE"
    pk.mkdir(parents=True, exist_ok=True)
    if include_registry:
        (pk / "29-DISABLED-FEATURES-REGISTRY.md").write_text(REGISTRY_TEXT, encoding="utf-8")
    if include_readme:
        (pk / "00-README.md").write_text(README_TEXT, encoding="utf-8")
    for fname, content in docs.items():
        (pk / fname).write_text(content, encoding="utf-8")
    return ts_dir / "lint_docs.py"

# ---------- baseline: clean tree, must PASS ----------
make_fake("baseline_pass", {
    "01-VISION-AND-DESIGN.md": "# Vision\n\nAll good, nothing weird here.\n",
})

# ---------- R1: HISTORY block inside a current-state file ----------
make_fake("r1_fail", {
    "04-HANDOFF.md": "# Handoff\n\nCurrent state text.\n\n# HISTORY\n\nOld stuff here.\n",
})

# ---------- R1 control: "# HISTORY" mentioned inside a fenced code block (quotation) ----------
make_fake("r1_control_fence", {
    "04-HANDOFF.md": "# Handoff\n\nCurrent state text.\n\n"
                      "Example of what NOT to do:\n\n```\n# HISTORY\nsome archived text\n```\n"
                      "End of doc.\n",
})

# ---------- R2: two banners ----------
make_fake("r2_fail", {
    "04-HANDOFF.md": "# START HERE\n\nfirst banner\n\n## YOU ARE HERE\n\nsecond banner\n",
})

# ---------- R2 control: banner phrase inside a quote/code fence (only one real banner) ----------
make_fake("r2_control_fence", {
    "04-HANDOFF.md": "# START HERE\n\nreal banner\n\n"
                      "Quoted example:\n\n> \"we used to write ## START HERE here\"\n\n"
                      "```\n## YOU ARE HERE (example, not real)\n```\n",
})

# ---------- R3: line budget 04- (900 pass / 901 fail) ----------
def n_lines(n):
    return "\n".join(f"line {i}" for i in range(1, n + 1)) + "\n"

make_fake("r3_900_pass", {"04-HANDOFF.md": n_lines(900)})
make_fake("r3_901_fail", {"04-HANDOFF.md": n_lines(901)})
make_fake("r3_3600_pass", {"03-PUNCH-LIST.md": n_lines(3600)})
make_fake("r3_3601_fail", {"03-PUNCH-LIST.md": n_lines(3601)})

# ---------- R4: duplicate NN- number ----------
make_fake("r4_fail", {
    "01-VISION-AND-DESIGN.md": "# Vision A\n",
    "01-DUPLICATE.md": "# Vision B (duplicate number)\n",
})

# ---------- R5: 00-README references a file that does not exist ----------
make_fake("r5_fail", {}, include_readme=False)
(SCRATCH / "r5_fail" / "PROJECT KNOWLEDGE" / "00-README.md").write_text(
    "# 00 README\n\nRead `01-VISION-AND-DESIGN.md` then `99-NONEXISTENT-FILE.md`.\n",
    encoding="utf-8",
)

# ---------- R6: a POKEBOT_* flag used in bot code, not in the registry ----------
make_fake("r6_fail", {
    "01-VISION-AND-DESIGN.md": "# Vision\n",
})
mods = SCRATCH / "r6_fail" / "sandbox-pokebot" / "modules"
mods.mkdir(parents=True, exist_ok=True)
(mods / "foo.py").write_text(
    'import os\nFLAG = os.environ.get("POKEBOT_TOTALLY_UNDOCUMENTED_FLAG")\n', encoding="utf-8"
)

# ---------- R6 control: flag IS documented -> must not fire for that flag ----------
make_fake("r6_control_documented", {
    "01-VISION-AND-DESIGN.md": "# Vision\n",
    "29-DISABLED-FEATURES-REGISTRY.md": REGISTRY_TEXT + "\nPOKEBOT_TOTALLY_DOCUMENTED_FLAG - documented here.\n",
}, include_registry=False)
mods2 = SCRATCH / "r6_control_documented" / "sandbox-pokebot" / "modules"
mods2.mkdir(parents=True, exist_ok=True)
(mods2 / "foo.py").write_text(
    'import os\nFLAG = os.environ.get("POKEBOT_TOTALLY_DOCUMENTED_FLAG")\n', encoding="utf-8"
)

print("done")
