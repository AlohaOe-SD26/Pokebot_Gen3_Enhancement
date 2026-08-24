"""Re-derive the (b) population on an ARBITRARY early_game.py. Criterion, stated once:
a handler catching BotModeError/Exception/bare, whose TRY BODY can TRANSITIVELY reach
`_check_abort`, and which neither re-raises nor calls `reraise_if_aborting`."""
import ast, sys, collections

src = open(sys.argv[1], encoding="utf-8").read()
tree = ast.parse(src)

# fn name -> names it calls (direct, same module)
calls = collections.defaultdict(set)
fnnodes = {}
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        fnnodes[node.name] = node
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                if isinstance(f, ast.Name):
                    calls[node.name].add(f.id)
                elif isinstance(f, ast.Attribute):
                    calls[node.name].add(f.attr)

# transitive closure: which functions can reach _check_abort
reaches = set()
changed = True
while changed:
    changed = False
    for fn, targets in calls.items():
        if fn in reaches:
            continue
        if "_check_abort" in targets or (targets & reaches):
            reaches.add(fn); changed = True

def body_reaches_abort(stmts):
    for st in stmts:
        for sub in ast.walk(st):
            if isinstance(sub, ast.Call):
                f = sub.func
                n = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
                if n == "_check_abort" or n in reaches:
                    return True
    return False

def handler_guards(h):
    for sub in ast.walk(h):
        if isinstance(sub, ast.Raise):
            return True
        if isinstance(sub, ast.Call):
            f = sub.func
            n = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if n == "reraise_if_aborting":
                return True
    return False

def catches_bme(h):
    if h.type is None:
        return True
    names = []
    for sub in ast.walk(h.type):
        if isinstance(sub, ast.Name):
            names.append(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.append(sub.attr)
    return any(n in ("BotModeError", "Exception", "BaseException") for n in names)

# enclosing function for each node
parent_fn = {}
for fn, node in fnnodes.items():
    for sub in ast.walk(node):
        parent_fn[id(sub)] = fn

sites = []
for node in ast.walk(tree):
    if isinstance(node, ast.Try) and body_reaches_abort(node.body):
        for h in node.handlers:
            if catches_bme(h) and not handler_guards(h):
                sites.append((parent_fn.get(id(h), "<module>"), h.lineno))

fns = sorted({f for f, _ in sites})
print(f"  SITES: {len(sites)}   FUNCTIONS: {len(fns)}")
for f in fns:
    print(f"     {f}  (lines {', '.join(str(l) for ff, l in sites if ff == f)})")
