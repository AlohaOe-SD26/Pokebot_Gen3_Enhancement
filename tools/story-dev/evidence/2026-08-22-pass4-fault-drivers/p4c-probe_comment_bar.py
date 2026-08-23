import ast, pathlib
REAL_GATE = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\repro_no_silent_except.py")
src = REAL_GATE.read_text(encoding="utf-8")
tree = ast.parse(src)
func_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "handler_is_loud")
func_src = ast.get_source_segment(src, func_node)
REPORTERS = ("log", "print", "debug_logger", "console", "logger", "warn", "_say", "_ch14_say", "_piggyback_report")
ns = {"ast": ast, "REPORTERS": REPORTERS}
exec(compile(func_src, "<extracted>", "exec"), ns)
handler_is_loud = ns["handler_is_loud"]

def run_case(label, code, expect_loud):
    t = ast.parse(code)
    h = [n for n in ast.walk(t) if isinstance(n, ast.ExceptHandler)][0]
    loud, why = handler_is_loud(h, code.split("\n"))
    status = "PASS" if loud == expect_loud else "FAIL (FALSE-FIRE RISK)"
    print(f"  {status}  {label}: loud={loud} why={why!r}")
    return loud == expect_loud

print("=== Does a non-justifying but >=12-char comment count as 'justified'? ===")
r1 = run_case(
    "genuinely SILENT handler, comment is just filler chatter (not a real justification)",
    "try:\n    do_thing()\nexcept Exception:  # whatever man just move on\n    pass\n",
    expect_loud=False,   # if this is True instead, that's a real false-fire in the heuristic
)
