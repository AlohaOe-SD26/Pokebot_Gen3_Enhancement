"""ONE LOOKUP before asking anyone anything (backlog N2 + P5, spec S3-2): rulings, verified facts, and the PINNED decomp.

    py -3.12 tools/decomp_lookup.py ask "<words>"     # rulings (do-not first), ledger facts, decomp hits; exit 3 = nothing

WHY. CLAUDE.md rule 11: a question already ruled in `06-DECISIONS-LOG.md` must never be asked twice, and ~10 `08`
entries record that it was. Decomp facts were re-fetched with `gh api` by agent after agent. This tool answers from
three local sources and says which one each line came from:
  ruling <text|n>   06 sections ranked by token overlap (title, first 400 characters, slugs, KI ids, ruling numbers,
                    do-not lines, overlay topics). A section's do-not line prints FIRST and is QUOTED FROM 06 ITSELF,
                    never from the index. 06 wins; the index and overlay are finding aids.
  fact <text>       rows of `PROJECT KNOWLEDGE/facts-ledger.jsonl` (CONFIRMED / REFUTED / UNVERIFIED, with source + tool)
  grep <regex> [--in <glob>] [-i]      the pinned decomp, `\\r\\n`-tolerant
  symbol <NAME> [--in <glob>]          `#define NAME`, `[NAME] =`, a function or data definition, an enum member, a label
  trainer <TRAINER_X>                  id from opponents.h + the trainers.h block + its party (trainer_parties.h)
  map <MapName | MAP_ID>               a map.json summary (connections, warps, trainers, items)
  ask "<words>"                        all three; prints "NO PRIOR RULING OR FACT FOUND" and exits 3 when all are empty

THE PIN. `decomp_root()` resolves `--decomp`, else env `POKEBOT_DECOMP`, else the sibling `../_decomp/pokeemerald`
(derived from this file's location), and requires `git rev-parse HEAD` to equal `tools/decomp.pin`. Otherwise it
REFUSES with exit 2 and prints the exact clone commands: a silent answer from the wrong commit is the failure this
exists to prevent (the June 2026 clone in POKEMON_EMERAL_AI is at a different commit and must be refused).
`ask` with no clone present still answers from rulings and facts and says the decomp was not searched; a clone at
the WRONG commit is refused even there.

Exit codes: 0 found; 1 no match (grep/symbol/trainer/map/ruling/fact); 2 refused (pin); 3 `ask` found nothing.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PIN_FILE = HERE / "decomp.pin"
DEFAULT_DECOMP = REPO.parent / "_decomp" / "pokeemerald"
DOCS = REPO / "PROJECT KNOWLEDGE"
DEFAULT_LEDGER = DOCS / "facts-ledger.jsonl"
sys.path.insert(0, str(HERE / "story-dev"))
import build_rulings_index as bri  # noqa: E402  (one 06 parser for the index AND the lookup)

DEFAULT_GLOBS = ("src/**/*.c", "src/**/*.h", "include/**/*.h", "data/**/*.inc", "data/**/*.s", "data/**/*.json",
                 "asm/**/*.inc")
EXIT_FOUND, EXIT_NONE, EXIT_REFUSED, EXIT_ASK_EMPTY = 0, 1, 2, 3


# ============================================================================================ the pinned clone

class DecompRefused(Exception):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind  # "absent" | "not_a_clone" | "wrong_commit" | "no_pin"


def read_pin(pin_file: Path = PIN_FILE) -> str:
    if not pin_file.is_file():
        raise DecompRefused("no_pin", f"no pin file at {pin_file} (one line: the pinned pret/pokeemerald SHA)")
    pin = pin_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise DecompRefused("no_pin", f"{pin_file} does not hold one 40-hex SHA: {pin[:60]!r}")
    return pin


def clone_commands(pin: str, target: Path = DEFAULT_DECOMP) -> str:
    return (f'  git clone -c core.autocrlf=false --depth 1 https://github.com/pret/pokeemerald "{target}"\n'
            f'  git -C "{target}" fetch --depth 1 origin {pin}\n'
            f'  git -C "{target}" checkout {pin}\n'
            f"  (or pass --decomp / set POKEBOT_DECOMP to a clone whose HEAD is {pin})")


def head_of(path: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def verify_pin(path: Path, pin: str) -> None:
    """Raise DecompRefused unless `path` is a git clone whose HEAD is exactly `pin`."""
    if not path.is_dir():
        raise DecompRefused("absent", f"no decomp clone at {path}")
    head = head_of(path)
    if head is None:
        raise DecompRefused("not_a_clone", f"{path} is not a git clone (git rev-parse HEAD failed)")
    if head != pin:
        raise DecompRefused("wrong_commit", f"{path} is at {head}, not the pinned {pin}: refusing to answer from "
                                            f"the wrong commit")


def candidate_path(explicit: Path | None = None) -> Path:
    """Where the clone is looked for: `--decomp`, else env POKEBOT_DECOMP, else the sibling `../_decomp/pokeemerald`."""
    env = os.environ.get("POKEBOT_DECOMP")
    return Path(explicit) if explicit else (Path(env) if env else DEFAULT_DECOMP)


def decomp_root(explicit: Path | None = None, pin_file: Path = PIN_FILE) -> Path:
    pin = read_pin(pin_file)
    path = candidate_path(explicit)
    verify_pin(path, pin)
    return path


def refusal_text(exc: DecompRefused, pin_file: Path = PIN_FILE) -> str:
    try:
        pin = read_pin(pin_file)
    except DecompRefused:
        pin = "<the SHA in tools/decomp.pin>"
    return f"REFUSED ({exc.kind}): {exc}\nMake the pinned clone (outside the repo, never committed):\n" + \
        clone_commands(pin)


# ============================================================================================ decomp search

def read_lines(path: Path) -> list[str]:
    """CRLF-tolerant: a file checked out with CRLF answers exactly like an LF one."""
    return path.read_bytes().decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")


def iter_files(root: Path, globs: tuple[str, ...]):
    seen = set()
    for g in globs:
        if any(ch in g for ch in "*?["):
            for p in sorted(root.glob(g)):
                if p.is_file() and p not in seen:
                    seen.add(p)
                    yield p
        else:
            p = root / g
            if p.is_file() and p not in seen:
                seen.add(p)
                yield p


def grep(root: Path, pattern: str, globs: tuple[str, ...] = DEFAULT_GLOBS, ignore_case: bool = False,
         limit: int = 200) -> list[tuple[str, int, str]]:
    rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
    hits = []
    for p in iter_files(root, globs):
        for i, ln in enumerate(read_lines(p), 1):
            if rx.search(ln):
                hits.append((p.relative_to(root).as_posix(), i, ln.rstrip()))
                if len(hits) >= limit:
                    return hits
    return hits


def symbol_patterns(name: str) -> list[tuple[str, re.Pattern]]:
    n = re.escape(name)
    return [
        ("define", re.compile(rf"^\s*#define\s+{n}\b")),
        ("designated", re.compile(rf"\[\s*{n}\s*\]\s*=")),
        ("function", re.compile(rf"^[A-Za-z_][\w \t\*]*\b{n}\s*\([^;]*$")),
        ("data", re.compile(rf"^\s*(?:static\s+|extern\s+)?(?:const\s+)?[A-Za-z_][\w \t\*]*\b{n}\s*(?:\[[^\]]*\])*\s*=")),
        ("enum", re.compile(rf"^\s+{n}\s*(?:=[^,]*)?,?\s*(?://.*|/\*.*)?$")),
        ("label", re.compile(rf"^{n}::?\s*(?:@.*)?$")),
    ]


def symbol(root: Path, name: str, globs: tuple[str, ...] = DEFAULT_GLOBS) -> list[tuple[str, int, str, str]]:
    pats = symbol_patterns(name)
    hits = []
    for p in iter_files(root, globs):
        lines = read_lines(p)
        if not any(name in ln for ln in lines):
            continue
        for i, ln in enumerate(lines, 1):
            if name not in ln:
                continue
            for kind, rx in pats:
                if rx.search(ln):
                    hits.append((p.relative_to(root).as_posix(), i, kind, ln.rstrip()))
                    break
    return hits


def _block_after(lines: list[str], start: int) -> list[str]:
    """Lines from `start` through the brace that closes the first `{` at or after it."""
    depth, out, opened = 0, [], False
    for ln in lines[start:]:
        out.append(ln)
        depth += ln.count("{") - ln.count("}")
        opened = opened or "{" in ln
        if opened and depth <= 0:
            break
    return out


def trainer(root: Path, name: str) -> dict | None:
    opp = read_lines(root / "include/constants/opponents.h")
    tid = None
    for i, ln in enumerate(opp, 1):
        m = re.match(rf"^\s*#define\s+{re.escape(name)}\s+(\d+)\b", ln)
        if m:
            tid, id_line = int(m.group(1)), i
            break
    if tid is None:
        return None
    tr = read_lines(root / "src/data/trainers.h")
    start = next((i for i, ln in enumerate(tr) if re.search(rf"\[\s*{re.escape(name)}\s*\]\s*=", ln)), None)
    info = {"name": name, "id": tid, "opponents_h_line": id_line, "trainers_h_line": None, "fields": {}, "party": [],
            "party_symbol": None}
    if start is None:
        return info
    info["trainers_h_line"] = start + 1
    block = "\n".join(_block_after(tr, start))
    for key in ("trainerClass", "trainerName", "items", "doubleBattle", "aiFlags", "party"):
        m = re.search(rf"\.{key}\s*=\s*(.+?),?\s*\n", block)
        if m:
            info["fields"][key] = m.group(1).strip().rstrip(",")
    m = re.search(r"(sParty_\w+)", info["fields"].get("party", ""))
    if not m:
        return info
    info["party_symbol"] = sym = m.group(1)
    tp = read_lines(root / "src/data/trainer_parties.h")
    pstart = next((i for i, ln in enumerate(tp) if re.search(rf"\b{sym}\s*\[\s*\]\s*=", ln)), None)
    if pstart is None:
        return info
    info["trainer_parties_h_line"] = pstart + 1
    body = "\n".join(_block_after(tp, pstart))
    for mon in re.findall(r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", body.split("=", 1)[1]):
        d = {}
        for key in ("lvl", "species", "heldItem", "iv"):
            mm = re.search(rf"\.{key}\s*=\s*([^,\n]+)", mon)
            if mm:
                d[key] = mm.group(1).strip()
        mm = re.search(r"\.moves\s*=\s*\{([^}]*)\}", mon)
        if mm:
            d["moves"] = [x.strip() for x in mm.group(1).split(",") if x.strip()]
        if "species" in d:
            info["party"].append(d)
    return info


def find_map(root: Path, name: str) -> Path | None:
    p = root / "data/maps" / name / "map.json"
    if p.is_file():
        return p
    for mj in sorted((root / "data/maps").glob("*/map.json")):
        try:
            if json.loads("\n".join(read_lines(mj))).get("id") == name:
                return mj
        except ValueError:
            continue
    return None


def map_summary(root: Path, name: str) -> dict | None:
    p = find_map(root, name)
    if p is None:
        return None
    d = json.loads("\n".join(read_lines(p)))
    objs = d.get("object_events") or []
    return {
        "file": p.relative_to(root).as_posix(),
        "id": d.get("id"), "name": d.get("name"), "map_type": d.get("map_type"),
        "region_map_section": d.get("region_map_section"),
        "connections": [(c.get("direction"), c.get("map"), c.get("offset")) for c in (d.get("connections") or [])],
        "warps": [(w.get("x"), w.get("y"), w.get("dest_map"), w.get("dest_warp_id")) for w in d.get("warp_events") or []],
        "trainers": [(o.get("x"), o.get("y"), o.get("script")) for o in objs
                     if o.get("trainer_type") not in (None, "TRAINER_TYPE_NONE")],
        "objects": len(objs), "coord_events": len(d.get("coord_events") or []),
        "bg_events": len(d.get("bg_events") or []),
    }


# ============================================================================================ rulings + ledger search

STOP = set("a an and are as at be by do does for from how i in is it its just no not of on or should s that the "
           "this to was we what when where which why will with".split())


def tokens(text: str, query: bool = False) -> list[str]:
    """Alphanumeric runs, lower-cased. A mixed token also yields its letter/digit sub-runs of 2+ characters, so the
    query "32x310" meets the 06 text "32×310". In a QUERY a mixed token is replaced by those sub-runs when it has
    any (a compound the docs never spell would otherwise count as a miss); "b1f" has none and stays whole."""
    out = []
    for t in re.findall(r"[a-z0-9]+", text.lower()):
        parts = [p for p in re.findall(r"[a-z]+|[0-9]+", t) if len(p) >= 2] if (
            re.search(r"[a-z]", t) and re.search(r"[0-9]", t)) else []
        if query:
            out.extend(parts if parts else [t])
        else:
            out.append(t)
            out.extend(parts)
    return [t for t in out if t not in STOP and len(t) >= 2 or t.isdigit()]


def section_fields(s: dict, entry: dict) -> tuple[set[str], set[str], set[str]]:
    """(flag tokens, title tokens, other tokens) for ranking. `other` = the spec's fields (first 400 characters, slugs,
    KI ids, ruling numbers, overlay topics) plus every do-not candidate line. `flag` = the OVERLAY's do-not judgment
    only (its `do_not_reopen` line and the candidate lines it classified `marker`): a question that matches what a
    ruling forbids re-asking is the one this tool exists to catch, so those words weigh most. Empty the overlay and
    the boost is gone (the N6 FAULT arm measures exactly that)."""
    markers = [d["text"] for d in s["donot"] if entry.get("candidates", {}).get(d["key"]) == "marker"]
    flag = " ".join([entry.get("do_not_reopen", "")] + markers) if entry.get("do_not_reopen") else ""
    other = " ".join([
        s["_body"][:400], " ".join(s["slugs"]), " ".join(s["ki"]),
        " ".join(f"ruling {n}" for n in s["rulings"] + s["ruling_mentions"]),
        " ".join(d["text"] for d in s["donot"]), " ".join(entry.get("topics", [])),
        " ".join([entry["ruling_key"]] if isinstance(entry.get("ruling_key"), str) else entry.get("ruling_key", [])),
    ])
    return set(tokens(flag)), set(tokens(s["title"])), set(tokens(other))


def rank(query: str, docs: list[tuple[object, set[str], set[str], set[str]]], coverage: float = 0.5, top: int = 5):
    """IDF-weighted token overlap; a doc must cover at least `coverage` of the query's IDF mass (so one common word
    cannot pull in an unrelated section). A token found in the do-not judgment weighs 2x, in the title 1.5x."""
    q = list(dict.fromkeys(tokens(query, query=True)))
    if not q:
        return []
    n = len(docs)
    df = {t: sum(1 for _, f, a, b in docs if t in f or t in a or t in b) for t in q}
    idf = {t: math.log((n + 1) / (df[t] + 0.5)) for t in q}
    total = sum(idf.values())
    scored = []
    for doc, flag, title, other in docs:
        hit = [t for t in q if t in flag or t in title or t in other]
        mass = sum(idf[t] for t in hit)
        if not hit or mass < coverage * total:
            continue
        score = sum(idf[t] * (2.0 if t in flag else 1.5 if t in title else 1.0) for t in hit)
        scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    return scored[:top]


def load_sections(decisions: Path, overlay_path: Path | None):
    sections = bri.parse_sections(bri.read_text(decisions))
    overlay = bri.load_overlay(overlay_path)
    return sections, overlay


def find_rulings(query: str, sections: list[dict], overlay: dict, top: int = 5) -> list[dict]:
    q = query.strip()
    m = re.fullmatch(r"(?:user\s+)?(?:ruling\s+)?(\d+)", q, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        defining = [s for s in sections if n in s["rulings"]]
        mentioning = [s for s in sections if n in s["ruling_mentions"]]
        return defining + mentioning[: max(0, top * 2 - len(defining))]
    docs = [(s, *section_fields(s, overlay.get(s["id"], {}))) for s in sections]
    return [s for _, s in rank(q, docs, top=top)]


def _reverse_links(overlay: dict) -> dict[str, list[tuple[str, str]]]:
    rev: dict[str, list[tuple[str, str]]] = {}
    for oid, e in overlay.items():
        for field, label in (("amends", "amended by"), ("application_of", "applied by"),
                             ("superseded_by", None)):
            v = e.get(field)
            if not v or label is None:
                continue
            for t in ([v] if isinstance(v, str) else v):
                rev.setdefault(t, []).append((label, oid))
    return rev


def format_ruling(s: dict, overlay: dict, rank_no: int, rev: dict) -> list[str]:
    e = overlay.get(s["id"], {})
    out = [f"[{rank_no}] {s['id']}  06:{s['line_start']}-{s['line_end']}  {s['title']}"]
    if e.get("do_not_reopen"):
        out.append(f"    ⛔ DO-NOT-REOPEN: {e['do_not_reopen']}")
        body = s["_body"].split("\n")
        for d in s["donot"]:
            if e.get("candidates", {}).get(d["key"]) == "marker":
                quoted = body[d["line"] - s["line_start"] - 1].strip()
                out.append(f"    06:{d['line']}> {quoted}")
    status = e.get("status", "ACTIVE")
    if status != "ACTIVE":
        out.append(f"    STATUS: {status}" + (f" -> read {e['superseded_by']} instead" if e.get("superseded_by") else ""))
    rel = []
    if e.get("ruling_key"):
        rel.append("defines " + (e["ruling_key"] if isinstance(e["ruling_key"], str) else ", ".join(e["ruling_key"])))
    for field, label in (("application_of", "applies"), ("amends", "amends")):
        if e.get(field):
            v = e[field]
            rel.append(f"{label} " + (v if isinstance(v, str) else ", ".join(v)))
    for label, oid in rev.get(s["id"], []):
        rel.append(f"{label} {oid}")
    if rel:
        out.append("    relation: " + "; ".join(rel))
    shown = 0
    for k, ln in enumerate(s["_body"].split("\n")):
        if ln.strip() and shown < 3:
            out.append(f"    06:{s['line_start'] + 1 + k}> {ln.strip()[:200]}")
            shown += 1
    return out


def load_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for ln in path.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n"):
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except ValueError:
                continue
    return rows


def find_facts(query: str, rows: list[dict], top: int = 5) -> list[dict]:
    docs = []
    for r in rows:
        src = r.get("source") or {}
        text = " ".join(str(x) for x in (r.get("claim", ""), r.get("correction", ""), src.get("ref", ""),
                                          " ".join(r.get("dependents") or [])))
        docs.append((r, set(), set(tokens(r.get("id", ""))), set(tokens(text))))
    return [r for _, r in rank(query, docs, top=top)]


def format_fact(r: dict) -> list[str]:
    src = r.get("source") or {}
    out = [f"  [{r.get('status')}] {r.get('id')}: {r.get('claim')}",
           f"      source: {src.get('kind')} {src.get('ref')}   re-check: {r.get('tool')}   last checked "
           f"{r.get('last_checked')} by {r.get('checked_by')}"]
    if r.get("correction"):
        out.append(f"      correction: {r['correction']}")
    return out


# ============================================================================================ CLI

def _common() -> argparse.ArgumentParser:
    c = argparse.ArgumentParser(add_help=False)
    c.add_argument("--decomp", type=Path, help="the pinned clone (default: env POKEBOT_DECOMP, else ../_decomp/pokeemerald)")
    c.add_argument("--pin-file", type=Path, default=PIN_FILE)
    c.add_argument("--decisions", type=Path, default=bri.DEFAULT_DECISIONS)
    c.add_argument("--overlay", type=Path, default=bri.DEFAULT_OVERLAY)
    c.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    return c


def _root_or_refuse(args) -> Path:
    return decomp_root(args.decomp, args.pin_file)


def cmd_ruling(args) -> int:
    sections, overlay = load_sections(args.decisions, args.overlay)
    found = find_rulings(args.text, sections, overlay)
    if not found:
        print(f"no 06 section matches {args.text!r}")
        return EXIT_NONE
    rev = _reverse_links(overlay)
    print(f"RULINGS for {args.text!r} (06 wins: every 06:<n>> line is quoted from 06 itself)")
    for k, s in enumerate(found, 1):
        print("\n".join(format_ruling(s, overlay, k, rev)))
    return EXIT_FOUND


def cmd_fact(args) -> int:
    found = find_facts(args.text, load_ledger(args.ledger))
    if not found:
        print(f"no ledger row matches {args.text!r}")
        return EXIT_NONE
    print(f"FACTS for {args.text!r} ({args.ledger.name})")
    for r in found:
        print("\n".join(format_fact(r)))
    return EXIT_FOUND


def cmd_grep(args) -> int:
    root = _root_or_refuse(args)
    hits = grep(root, args.regex, tuple(args.globs or DEFAULT_GLOBS), args.ignore_case, args.max)
    for f, i, ln in hits:
        print(f"{f}:{i}: {ln}")
    print(f"-- {len(hits)} hit(s) at pinned {head_of(root)[:8]}")
    return EXIT_FOUND if hits else EXIT_NONE


def cmd_symbol(args) -> int:
    root = _root_or_refuse(args)
    hits = symbol(root, args.name, tuple(args.globs or DEFAULT_GLOBS))
    for f, i, kind, ln in hits:
        print(f"{f}:{i}: [{kind}] {ln}")
    print(f"-- {len(hits)} definition(s) of {args.name} at pinned {head_of(root)[:8]}")
    return EXIT_FOUND if hits else EXIT_NONE


def cmd_trainer(args) -> int:
    root = _root_or_refuse(args)
    info = trainer(root, args.name)
    if info is None:
        print(f"{args.name}: no #define in include/constants/opponents.h")
        return EXIT_NONE
    print(f"{info['name']} = {info['id']}   (include/constants/opponents.h:{info['opponents_h_line']})")
    if info["trainers_h_line"]:
        print(f"  src/data/trainers.h:{info['trainers_h_line']}")
        for k, v in info["fields"].items():
            print(f"    .{k} = {v}")
    if info["party_symbol"]:
        print(f"  party {info['party_symbol']} (src/data/trainer_parties.h:{info.get('trainer_parties_h_line')}):")
        for k, mon in enumerate(info["party"], 1):
            print(f"    {k}. L{mon.get('lvl')} {mon.get('species')}  held {mon.get('heldItem', '-')}  "
                  f"moves {', '.join(mon.get('moves', [])) or '(default)'}")
    print(f"-- at pinned {head_of(root)[:8]}")
    return EXIT_FOUND


def cmd_map(args) -> int:
    root = _root_or_refuse(args)
    info = map_summary(root, args.name)
    if info is None:
        print(f"{args.name}: no data/maps/<name>/map.json and no map.json with that id")
        return EXIT_NONE
    for k, v in info.items():
        print(f"{k}: {v}")
    print(f"-- at pinned {head_of(root)[:8]}")
    return EXIT_FOUND


def cmd_ask(args) -> int:
    sections, overlay = load_sections(args.decisions, args.overlay)
    rulings = find_rulings(args.words, sections, overlay)
    facts = find_facts(args.words, load_ledger(args.ledger))
    rev = _reverse_links(overlay)
    lines: list[str] = []
    flagged = [s for s in rulings[:3] if overlay.get(s["id"], {}).get("do_not_reopen")]
    if flagged:
        lines.append("⛔ DO-NOT-REOPEN: a matching ruling says this must not be re-asked (quoted from 06 below):")
        for s in flagged:
            lines.append(f"    {s['id']}: {overlay[s['id']]['do_not_reopen']}")
    if rulings:
        lines.append(f"RULINGS ({len(rulings)}; 06 wins, every 06:<n>> line is quoted from 06 itself)")
        for k, s in enumerate(rulings, 1):
            lines.extend(format_ruling(s, overlay, k, rev))
    if facts:
        lines.append(f"FACTS ({len(facts)}, {args.ledger.name})")
        for r in facts:
            lines.extend(format_fact(r))
    decomp_hits: list[str] = []
    decomp_note = ""
    if args.no_decomp:
        decomp_note = "decomp: not searched (--no-decomp)"
    else:
        try:
            root = decomp_root(args.decomp, args.pin_file)
        except DecompRefused as exc:
            if exc.kind != "absent":
                print(refusal_text(exc, args.pin_file))
                return EXIT_REFUSED
            root = None
            decomp_note = f"decomp: NOT SEARCHED ({exc}); make the pinned clone:\n{clone_commands(read_pin(args.pin_file))}"
        if root is not None:
            syms = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", args.words)
                    if ("_" in w and w.upper() == w) or re.fullmatch(r"(?:[A-Z][a-z0-9]+){2,}\w*", w)]
            seen: set[tuple[str, int]] = set()
            for w in syms:
                for f, i, kind, ln in symbol(root, w)[:5]:
                    seen.add((f, i))
                    decomp_hits.append(f"  {f}:{i}: [{kind}] {ln.strip()[:160]}")
            phrase = args.words.strip()
            if len(phrase) >= 3:
                for f, i, ln in grep(root, re.escape(phrase), ignore_case=True, limit=10):
                    if (f, i) not in seen:
                        decomp_hits.append(f"  {f}:{i}: {ln.strip()[:160]}")
            decomp_note = f"decomp: searched the pinned clone at {head_of(root)[:8]}"
    if decomp_hits:
        lines.append(f"DECOMP ({len(decomp_hits)} hit(s); {decomp_note})")
        lines.extend(decomp_hits)
    if not (rulings or facts or decomp_hits):
        lines.append("NO PRIOR RULING OR FACT FOUND")
        lines.append(decomp_note)
        print("\n".join(lines))
        return EXIT_ASK_EMPTY
    if not decomp_hits:
        lines.append(decomp_note)
    print("\n".join(lines))
    return EXIT_FOUND


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = _common()
    p = sub.add_parser("ruling", parents=[c]); p.add_argument("text"); p.set_defaults(fn=cmd_ruling)
    p = sub.add_parser("fact", parents=[c]); p.add_argument("text"); p.set_defaults(fn=cmd_fact)
    p = sub.add_parser("grep", parents=[c]); p.add_argument("regex")
    p.add_argument("--in", dest="globs", action="append"); p.add_argument("-i", dest="ignore_case", action="store_true")
    p.add_argument("--max", type=int, default=200); p.set_defaults(fn=cmd_grep)
    p = sub.add_parser("symbol", parents=[c]); p.add_argument("name")
    p.add_argument("--in", dest="globs", action="append"); p.set_defaults(fn=cmd_symbol)
    p = sub.add_parser("trainer", parents=[c]); p.add_argument("name"); p.set_defaults(fn=cmd_trainer)
    p = sub.add_parser("map", parents=[c]); p.add_argument("name"); p.set_defaults(fn=cmd_map)
    p = sub.add_parser("ask", parents=[c]); p.add_argument("words")
    p.add_argument("--no-decomp", action="store_true"); p.set_defaults(fn=cmd_ask)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except DecompRefused as exc:
        print(refusal_text(exc, args.pin_file))
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
