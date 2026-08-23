"""Isolate handler_is_loud() from repro_no_silent_except.py and fault-test it directly.
Does NOT modify the real repo; only reads it and execs the extracted function in a scratch
namespace, per rule 2(a): "calls its check functions on synthetic files you author"."""
import ast
import pathlib

REAL_GATE = pathlib.Path(
    r"C:\Remote Projects\Pokebot_Gen3_Enhancement\tools\story-dev\repro_no_silent_except.py"
)
src = REAL_GATE.read_text(encoding="utf-8")
tree = ast.parse(src)
func_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "handler_is_loud")
func_src = ast.get_source_segment(src, func_node)
assert func_src, "could not extract handler_is_loud source"

REPORTERS = ("log", "print", "debug_logger", "console", "logger", "warn", "_say", "_ch14_say", "_piggyback_report")
ns = {"ast": ast, "REPORTERS": REPORTERS}
exec(compile(func_src, "<extracted handler_is_loud>", "exec"), ns)
handler_is_loud = ns["handler_is_loud"]


def run_case(label, code, expect_loud):
    t = ast.parse(code)
    handlers = [n for n in ast.walk(t) if isinstance(n, ast.ExceptHandler)]
    assert len(handlers) == 1, f"{label}: expected 1 except handler, got {len(handlers)}"
    lines = code.split("\n")
    loud, why = handler_is_loud(handlers[0], lines)
    status = "PASS" if loud == expect_loud else "FAIL"
    print(f"  {status}  {label}: loud={loud} why={why!r} (expected loud={expect_loud})")
    return loud == expect_loud


print("=== DOWNWARD: real defect shapes the gate exists to catch ===")
ok1 = run_case(
    "bare except: pass (the exact defect family)",
    "try:\n    do_thing()\nexcept Exception:\n    pass\n",
    expect_loud=False,
)
ok2 = run_case(
    "except with only a bare noqa code, no prose (should NOT count as justified)",
    "try:\n    do_thing()\nexcept Exception:  # noqa: BLE001\n    move_to_forget = 4\n",
    expect_loud=False,
)

print("\n=== CONTROL: genuinely loud handlers must stay loud ===")
ok3 = run_case(
    "re-raises",
    "try:\n    do_thing()\nexcept Exception:\n    raise\n",
    expect_loud=True,
)
ok4 = run_case(
    "reports via log()",
    "try:\n    do_thing()\nexcept Exception as e:\n    log(f'failed: {e}')\n",
    expect_loud=True,
)
ok5 = run_case(
    "justified by a real prose comment",
    "try:\n    do_thing()\nexcept Exception:  # noqa: BLE001 -- a probe reports, it does not crash\n    pass\n",
    expect_loud=True,
)

print("\n=== UPWARD: defect-shaped TEXT inside comment/docstring/string near a LOUD handler ===")
ok6 = run_case(
    "comment ABOVE the handler says 'except: pass' but the real handler reports",
    "def f():\n    # except Exception: pass  -- old code used to look like this, now fixed\n    try:\n        do_thing()\n    except Exception as e:\n        log(f'failed: {e}')\n",
    expect_loud=True,
)
ok7 = run_case(
    "docstring inside try contains 'except Exception: pass' as prose",
    'def f():\n    try:\n        """warning: never write except Exception: pass here"""\n        do_thing()\n    except Exception as e:\n        log(str(e))\n',
    expect_loud=True,
)
ok8 = run_case(
    "quoted string literal 'except Exception: pass' assigned, handler itself reports",
    "def f():\n    BAD_EXAMPLE = 'except Exception: pass'\n    try:\n        do_thing()\n    except Exception as e:\n        print(BAD_EXAMPLE, e)\n",
    expect_loud=True,
)

results = [ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8]
print(f"\n{sum(results)}/{len(results)} sub-checks matched expectation")
raise SystemExit(0 if all(results) else 1)
