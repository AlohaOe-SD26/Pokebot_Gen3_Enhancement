#!/usr/bin/env python3
"""Selftest for tools/make_chapter_pack.py (spec S3-4, A5): every arm has a FAULT (the rule broken: it must be caught)
and a CONTROL (the healthy path passes).

    py -3.12 tools/story-dev/selftest_chapter_pack.py                       # every arm, real generator and inputs
    py -3.12 tools/story-dev/selftest_chapter_pack.py --work DIR            # scratch folder (default: temp, removed)
    py -3.12 tools/story-dev/selftest_chapter_pack.py --mutants --work DIR  # also: every mutant in a scratch copy of
                                                                            # the generator must fail some arm

It lives in tools/story-dev/ so run_gates.py finds it like every other suite; the generator stays in tools/ and is
run as a subprocess (and, for the arms that test its check functions directly, loaded from its file path), so a
mutant copy is exercised exactly like the real one.

INTENT: a chapter pack is what an agent reads instead of re-doing a chapter's recon, so a pack that silently drops a
trainer, a boss, an HM or a link, hides that a section is missing, or carries a stale hash is worse than no pack.
The first build passed 29 arms while chapters 19 and 24 crashed, four chapters could not fit the cap, and 24 of 24
omission and logic mutants survived (the 2026-10-22 verify). The arms, each FAULT + CONTROL:
  all         CONTROL every campaign chapter (24) generates, each passing its completeness check and the 12 KB cap.
  F1 shapes   a trainer object carries `script` (object, trigger) or `label` (map-script battle: Wallace, the Space
              Center): CONTROL a fixture of each shape gives its label, and the real ch19/ch24 packs cite the labels;
              FAULT an object with neither is refused naming its map, by the function and by the generator.
  F2 size     CONTROL every .md <= 12 KB and at least one chapter needed summarising; a forced summary of ch4 still
              holds every load-bearing item. FAULT: a summarised .md with one load-bearing item removed (a boss mon,
              a double battle, a claim, an HM, a links line, a summary line) or with 'none fought' added is caught by
              check_md_complete; a cap no load-bearing part fits (2000) still refuses, naming the cap.
  F3 complete CONTROL check_complete finds nothing on real packs. FAULT (pack level): one item per category removed
              from a real pack (boss, area/ring trainer, levels, double flag, species, ring map, connection, warp, warp
              in, HM, wild row, a claim of each kind) is named. FAULT (input level, a scratch world): a boss row, a boss
              trainer's object on an area map and on a ring map, the field-move row of a badge won and of a needed
              move, either side of a connection, and a warp to a missing map each make the run exit 2 naming EXACTLY
              that one finding (an exact count, so a second, wrong finding fails the arm). An ORDINARY trainer or a
              warp deleted from maps.json is named by no other input: only W3 (ch1-4) sees that. FAULT (generator level): a copy
              of the generator that drops ring trainers, a boss mon from the .md, the HMs or the boss claims exits 2.
  W3 recall   (the spec's real control for A5) milestones.json's hand-recon'd `trainers` table must be fully contained
              in the packs for chapters 1-4 (symbol + id, defeat flag in JSON and named with it in the .md, levels in
              order). FAULT: JOSH's object removed from a scratch maps.json makes recall fall. The milestone -> chapter
              mapping is the identity; FAULT: one chapter changed is reported. Extras are printed, not hidden.
  CRLF        CONTROL a CRLF copy of an input hashes as its LF original; CRLF copies of the packs pass --check.
              FAULT: a CRLF copy with one changed byte still fails --check (the normalisation hides line ends only).
  routekeys   CONTROL no x/y/route/path/steps/coords key in any pack's entries; ROUTE_KEYS (read with ast) equals
              extract_world.py's. FAULT: a scratch copy with one key dropped is reported; a key planted in a dict and
              one inside a LIST in a ch4 entry each exit 2 naming the path.
  others      absent (header names every missing section), hashes (each source's own, the generator's own, two runs
              identical: a determinism check, not a replication; one changed source changes exactly its hash), empty
              chapter, pin, unknown area map, unknown trainer, extra entry field not carried, non-normal wild rows not
              carried, the one-way claim (ch3's counted "none of N", and a redirected Petalburg Woods warp named), and
              --check (committed packs pass; an edited copy fails).
--mutants deletes each guard's CALL and applies the verify's 24 omission/logic mutants, each in a scratch copy; the
selftest run against that copy must fail. Nothing here writes outside --work; the committed packs and ai_player/ are
only read.
"""
import argparse
import ast
import concurrent.futures
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
GEN_DEFAULT = os.path.join(TOOLS, "make_chapter_pack.py")
WORLD = os.path.join(REPO, "ai_player", "knowledge", "world")
SEASONED = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
PIN = os.path.join(REPO, "tools", "decomp.pin")
PACKS = os.path.join(REPO, "PROJECT KNOWLEDGE", "chapter-packs")
MILESTONES = os.path.join(REPO, "ai_player", "knowledge", "milestones.json")
EXTRACT_WORLD = os.path.join(REPO, "ai_player", "gates", "extract_world.py")
W3_CHAPTERS = (1, 2, 3, 4)
MD_CAP = 12 * 1024
ROUTE_KEYS = ("x", "y", "route", "path", "steps", "coords")
ABSENT_MARKERS = ("NOT INCLUDED YET: items, gifts, marts and scripted events",
                  "NOT INCLUDED YET: A6's measured traps",
                  "NOT INCLUDED YET: story-event flags",
                  "THE DECOMP WINS")
SOURCES = {"ai_player/knowledge/world/" + n: os.path.join(WORLD, n)
           for n in ("campaign.json", "maps.json", "trainers.json", "bosses.json")}
SOURCES.update({"ai_player/knowledge/seasoned/" + n: os.path.join(SEASONED, n)
                for n in ("encounters.json", "learnsets.json", "species.json")})

#: guard -> (the exact text of its call in the generator, the text a call-deleting mutant puts there)
MUTANTS = {
    "check_pins": ("        check_pins(data, pin)\n", "        pass\n"),
    "refuse_empty_chapter": ("    refuse_empty_chapter(raw, chapter)\n", "    pass\n"),
    "refuse_route_keys": ("    refuse_route_keys(raw)\n", "    pass\n"),
    "resolve_maps": ('resolve_maps(e["area"], maps_by_id)', '["MAP_" + n for n in e["area"]]'),
    "join_trainer": ("join_trainer(sym, trainers_by_symbol, mid)", "trainers_by_symbol[sym]"),
    "script_label": ("script_label(obj, mid)", 'obj.get("script")'),
    "check_md_size": ("    check_md_size(md, md_cap)\n", "    pass\n"),
    "absent_header_lines": ('        a("> - " + line)\n', "        pass\n"),
    "source_hashes": ("            hashes[rel + name] = sha256_lf(path)\n",
                      '            hashes[rel + name] = "0" * 64\n'),
    "refuse_incomplete(check_complete)": ("    refuse_incomplete(problems + check_complete(pack, expected), chapter)\n",
                                          "    pass\n"),
    "refuse_incomplete(check_md_complete)": ("    refuse_incomplete(check_md_complete(pack, md), chapter)\n",
                                             "    pass\n"),
    "render_within_cap summary": ("        md = render_md(pack, summary_of=full, level=level)\n", "        pass\n"),
    # the input cross-checks inside expected_selection: each report deleted
    "problem: boss battled_on": ('problems.append("bosses.json says', '(lambda *_: None)("bosses.json says'),
    "problem: boss with no row": ('problems.append("campaign entry %s names boss',
                                  '(lambda *_: None)("campaign entry %s names boss'),
    "problem: badge with no field move": ('problems.append("%s is won in this chapter',
                                          '(lambda *_: None)("%s is won in this chapter'),
    "problem: needed move with no row": ('problems.append("%s needs field move %s, but',
                                         '(lambda *_: None)("%s needs field move %s, but'),
    "problem: area connection not mirrored": ('problems.append("maps.json: %s connects %s to %s, but %s has no '
                                              'connection back',
                                              '(lambda *_: None)("maps.json: %s connects %s to %s, but %s has no '
                                              'connection back'),
    "problem: ring connection not mirrored": ('problems.append("maps.json: %s connects %s to %s, but %s has no '
                                              'connection to',
                                              '(lambda *_: None)("maps.json: %s connects %s to %s, but %s has no '
                                              'connection to'),
    "problem: link to a missing map": ('problems.append("maps.json: %s links to',
                                       '(lambda *_: None)("maps.json: %s links to'),
}

#: the 2026-10-22 verify's 24 mutants, verbatim from its verify-work/vmut.py (all 24 survived the first build's selftest)
VERIFIER_MUTANTS = {
    "OM1_ring_trainers_dropped": ("trs = trainers_on(area_ids + ring_ids, area_ids,", "trs = trainers_on(area_ids, area_ids,"),
    "OM2_double_trainers_dropped": ("    fights = []\n", "    trs = [t for t in trs if not t[\"double\"]]\n    fights = []\n"),
    "OM3_gym_leader_boss_dropped": ('boss_rows = [b for b in bosses["bosses"] if b["fight"] in fights]',
                                    'boss_rows = [b for b in bosses["bosses"] if b["fight"] in fights and b["role"] != "gym_leader"]'),
    "OM4_hms_dropped": ("    pack = {\n", "    hms = []\n    pack = {\n"),
    "OM5_wild_water_dropped": ("        for method, tab in sorted(e[\"methods\"].items()):\n",
                               "        for method, tab in sorted(e[\"methods\"].items()):\n            if method == 'water': continue\n"),
    "OM6_connections_dropped": ('            conns.append({"dir"', '            if 0: conns.append({"dir"'),
    "OM7_levels_truncated_to_3": ('levels = [p["level"] for p in t["party"]]', 'levels = [p["level"] for p in t["party"]][:3]'),
    "OM8_boss_team_claims_dropped": ('        out.append(("boss_team",', '        if 0: out.append(("boss_team",'),
    "OM9_double_flag_false": ('"double": t["double"], "flag"', '"double": False, "flag"'),
    "OM10_ring_maps_dropped": ("    ring_ids = ring(area_ids, maps_by_id)\n", "    ring_ids = []\n"),
    "OM11_warps_in_dropped": ("    link_rows, incoming = links(area_ids, maps_by_id)\n",
                              "    link_rows, incoming = links(area_ids, maps_by_id)\n    incoming = []\n"),
    "OM12_boss_party_last_mon_dropped": ('        for p in b["party"]:\n            a("  - %s',
                                         '        for p in b["party"][:-1]:\n            a("  - %s'),
    "OM13_trainer_species_dropped": ('"species": [p["species"] for p in t["party"]], "ref"', '"species": [], "ref"'),
    "CM1_crlf_norm_inputs": ('        return hashlib.sha256(f.read().replace(b"\\r\\n", b"\\n")).hexdigest()',
                             '        return hashlib.sha256(f.read()).hexdigest()'),
    "CM2_check_crlf_norm": ('have = f.read().replace(b"\\r\\n", b"\\n").decode("utf-8")', 'have = f.read().decode("utf-8")'),
    "CM3_wild_availability_filter": ('if e.get("map") not in area_ids or e.get("availability") != "normal":',
                                     'if e.get("map") not in area_ids:'),
    "CM4_entry_allowlist": ('    entries = [{k: e[k] for k in ENTRY_FIELDS if k in e} for e in raw]\n', '    entries = raw\n'),
    "CM5_route_keys_no_recursion_in_lists": ('            out += route_keys(v, "%s[%d]" % (path, i))\n', '            pass\n'),
    "CM6_connects_back_always_true": ('back = any(cc["map"] == mid for cc in', 'back = True or any(cc["map"] == mid for cc in'),
    "CM7_requires_flash_claim": ('        if m["role"] == "area" and m["requires_flash"]:\n', '        if 0:\n'),
    "CM8_double_claim": ('        if t["in_area"] and t["double"]:\n', '        if 0:\n'),
    "CM9_scripted_battle_claims": ('    for trig, syms in by_trigger.items():\n', '    for trig, syms in []:\n'),
    "CM10_classify_unknown_dest_two_way": ('        return "unknown", "destination is not a maps.json map"',
                                           '        return "two_way", None'),
    "CM11_progress_flag_badge": ('    for bd in badges_won:\n        out.append(("progress_flag"',
                                 '    for bd in []:\n        out.append(("progress_flag"'),
}

#: generator-level plants: a defect written into a scratch copy of the generator under test; the copy must exit 2
#: naming it (the in-run completeness checks catch a GENERATOR that drops an item, not only a broken input)
PLANTS = {
    "ring trainers dropped": (VERIFIER_MUTANTS["OM1_ring_trainers_dropped"], "MISSING trainer"),
    "last boss mon dropped from the .md": (VERIFIER_MUTANTS["OM12_boss_party_last_mon_dropped"], "md boss"),
    "HMs emptied": (VERIFIER_MUTANTS["OM4_hms_dropped"], "MISSING HM"),
    "boss_team claims dropped": (VERIFIER_MUTANTS["OM8_boss_team_claims_dropped"], "MISSING claim [boss_team]"),
}


def sha256_lf(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def to_crlf(src, dst):
    with open(src, "rb") as f:
        raw = f.read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    with open(dst, "wb") as f:
        f.write(raw)


def import_generator(path):
    """The generator under test, loaded from its file (a mutant copy is loaded the same way)."""
    spec = importlib.util.spec_from_file_location("chapter_pack_under_test_%d" % abs(hash(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def findings_count(err):
    m = re.search(r"\((\d+) findings?\)", err)
    return int(m.group(1)) if m else None


class Runner:
    def __init__(self, gen, work):
        self.gen, self.work = gen, work
        self.results = []

    def run(self, chapters, out, world=WORLD, seasoned=SEASONED, extra=(), gen=None):
        cmd = [sys.executable, gen or self.gen] + [str(c) for c in chapters] + [
            "--world", world, "--seasoned", seasoned, "--pin", PIN, "--out", out] + list(extra)
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout, p.stderr

    def scratch(self, name, world_files=False, seasoned_files=False):
        """A fresh scratch folder; with world_files / seasoned_files, copies of the real input folders to break."""
        d = os.path.join(self.work, name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        for flag, src, sub in ((world_files, WORLD, "world"), (seasoned_files, SEASONED, "seasoned")):
            if flag:
                os.makedirs(os.path.join(d, sub))
                for n in os.listdir(src):
                    if n.endswith(".json"):
                        shutil.copyfile(os.path.join(src, n), os.path.join(d, sub, n))
        return d

    def arm(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + str(detail)[:300]) if detail else ""))

    def guarded(self, name, fn):
        """An arm whose body may raise (for instance on a generator without the function under test): a raise FAILS."""
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001 - any exception is the arm failing, with its text
            ok, detail = False, "%s: %s" % (type(exc).__name__, exc)
        self.arm(name, ok, detail)


# ---------------------------------------------------------------- W3 recall
def milestone_trainer_chapters(ms):
    """{table key: chapter} from the milestones that fight or require each `trainers` table entry."""
    out = {}
    for m in ms["milestones"]:
        keys = list((m.get("fight") or {}).get("trainers") or []) + list((m.get("done") or {}).get("trainers") or {})
        for k in keys:
            out.setdefault(k, m["chapter"])
    return out


def chapter_mapping_errors(ms, campaign):
    """The milestone -> pack chapter mapping must be the identity: each milestone id is a campaign entry whose chapter
    equals the milestone's. Returns the mismatches."""
    camp = {e["id"]: e["chapter"] for e in campaign["entries"]}
    return ["%s: milestone ch%s, campaign %s" % (m["id"], m["chapter"], camp.get(m["id"], "absent"))
            for m in ms["milestones"] if camp.get(m["id"]) != m["chapter"]]


def recall(packs, mds, ms):
    """(hits, total, missing[], extras{chapter: [symbols]}). Three facts per table trainer: present (symbol + id),
    defeat flag, party levels in order; each must hold in its chapter's pack JSON, and the .md must name the trainer
    with its flag. A table trainer with no milestone chapter is a miss (it cannot be placed)."""
    chap = milestone_trainer_chapters(ms)
    hits = total = 0
    missing = []
    for key, row in sorted(ms["trainers"].items()):
        sym = "TRAINER_" + key
        total += 3
        c = chap.get(key)
        if c not in packs:
            missing.append("%s: no chapter 1-4 milestone places it" % key)
            continue
        pack, md = packs[c], mds[c]
        cands = [t for t in pack["trainers"] if t["symbol"] == sym] + \
                [{"symbol": b["id"], "id": None, "flag": None, "levels": [p["level"] for p in b["party"]]}
                 for b in pack["bosses"] if b["id"] == sym]
        t = next((x for x in cands if x["id"] == row["id"]), None)
        if t is None:
            missing.append("ch%d %s (id %s): not in the pack" % (c, key, row["id"]))
            continue
        hits += 1
        if t["flag"] == row["flag"] and re.search(r"`%s`[^\n]*flag %d\b" % (re.escape(key), row["flag"]), md):
            hits += 1
        else:
            missing.append("ch%d %s: flag %s, pack %s (or the .md lacks it)" % (c, key, row["flag"], t["flag"]))
        if t["levels"] == row["levels"]:
            hits += 1
        else:
            missing.append("ch%d %s: levels %s, pack %s" % (c, key, row["levels"], t["levels"]))
    listed = {"TRAINER_" + k for k in ms["trainers"]}
    extras = {c: sorted(t["symbol"] for t in packs[c]["trainers"] if t["in_area"] and t["symbol"] not in listed)
              for c in packs}
    return hits, total, missing, extras


def read_packs(folder, chapters):
    packs, mds = {}, {}
    for c in chapters:
        packs[c] = load(os.path.join(folder, "ch%d.json" % c))
        with open(os.path.join(folder, "ch%d.md" % c), "rb") as f:
            mds[c] = f.read().replace(b"\r\n", b"\n").decode("utf-8")
    return packs, mds


def absent_ok(md, pack):
    return all(m in md for m in ABSENT_MARKERS) and len(pack.get("_absent") or []) == 3 and \
        all(any(m in line for line in pack["_absent"]) for m in ABSENT_MARKERS[:3])


def route_keys(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ROUTE_KEYS:
                out.append("%s.%s" % (path, k))
            out += route_keys(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += route_keys(v, "%s[%d]" % (path, i))
    return out


def assigned_tuple(text, name):
    """The value of a module-level `name = (...)` tuple, read with ast (a comment or a line break inside the tuple
    cannot fool it the way a regex could); None if there is no such assignment."""
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    return None


def campaign_chapters():
    return sorted({e["chapter"] for e in load(os.path.join(WORLD, "campaign.json"))["entries"]})


# ---------------------------------------------------------------- the arms
def all_arms(R):
    ms = load(MILESTONES)
    camp = load(os.path.join(WORLD, "campaign.json"))
    chapters = campaign_chapters()
    fresh = R.scratch("fresh")
    rc, out, err = R.run(["--all"], fresh)
    last = (err or out).strip().splitlines()[-1:] or [""]
    R.arm("all CONTROL: every campaign chapter (%d: %s-%s) generates from the real inputs, each passing its "
          "completeness check and the cap" % (len(chapters), chapters[0], chapters[-1]),
          rc == 0 and len(chapters) >= 24 and all(os.path.isfile(os.path.join(fresh, "ch%d.md" % c)) for c in chapters),
          last[0])
    if rc != 0:
        return
    packs, mds = read_packs(fresh, chapters)

    f1_arms(R, packs)
    f2_arms(R, packs, mds)
    f3_arms(R, packs)

    # W3 recall
    w3p = {c: packs[c] for c in W3_CHAPTERS}
    w3m = {c: mds[c] for c in W3_CHAPTERS}
    h, t, miss, extras = recall(w3p, w3m, ms)
    R.arm("W3 CONTROL: recall on freshly generated ch1-4 packs is 100%% (%d/%d facts, %d table trainers)" % (
        h, t, len(ms["trainers"])), h == t and t == 3 * len(ms["trainers"]) and t > 0, "; ".join(miss[:3]))
    for c in W3_CHAPTERS:
        print("      extras ch%d (pack trainers on area maps the table does not list): %d %s" % (
            c, len(extras[c]), ", ".join(x.replace("TRAINER_", "") for x in extras[c])))
    if all(os.path.isfile(os.path.join(PACKS, "ch%d.%s" % (c, x))) for c in chapters for x in ("json", "md")):
        cp, cm = read_packs(PACKS, W3_CHAPTERS)
        h2, t2, miss2, _ = recall(cp, cm, ms)
        R.arm("W3 CONTROL: recall on the COMMITTED packs is 100%% (%d/%d)" % (h2, t2), h2 == t2 and t2 > 0,
              "; ".join(miss2[:3]))
    else:
        R.arm("W3 CONTROL: the committed packs exist for every chapter", False, "missing under %s" % PACKS)
    d = R.scratch("w3_fault", world_files=True)
    maps = load(os.path.join(d, "world", "maps.json"))
    gym = next(m for m in maps["maps"] if m["id"] == "MAP_RUSTBORO_CITY_GYM")
    before = len(gym["trainers"])
    gym["trainers"] = [o for o in gym["trainers"] if o["trainers"] != ["TRAINER_JOSH"]]
    save(maps, os.path.join(d, "world", "maps.json"))
    rc, _, err = R.run(W3_CHAPTERS, os.path.join(d, "out"), world=os.path.join(d, "world"))
    if rc == 0:
        fp, fm = read_packs(os.path.join(d, "out"), W3_CHAPTERS)
        h3, t3, miss3, _ = recall(fp, fm, ms)
        R.arm("W3 FAULT: JOSH's object removed from a scratch maps.json -> recall falls (%d/%d) naming JOSH" % (h3, t3),
              before - len(gym["trainers"]) == 1 and h3 < t3 and any("JOSH" in x for x in miss3),
              "; ".join(miss3[:2]))
    else:
        R.arm("W3 FAULT: the scratch generation ran", False, err.strip()[-200:])
    errs = chapter_mapping_errors(ms, camp)
    R.arm("W3 mapping CONTROL: every milestone id is a campaign entry of the SAME chapter (%d milestones)" % len(
        ms["milestones"]), not errs and len(ms["milestones"]) == 20, "; ".join(errs[:3]))
    bad = json.loads(json.dumps(ms))
    bad["milestones"][-1]["chapter"] = 5
    R.arm("W3 mapping FAULT: one milestone's chapter changed is reported",
          any(bad["milestones"][-1]["id"] in x for x in chapter_mapping_errors(bad, camp)))

    # absent sections
    R.arm("absent CONTROL: every generated header names the absent sections and that the decomp wins",
          all(absent_ok(mds[c], packs[c]) for c in chapters))
    cut = "\n".join(line for line in mds[4].split("\n") if ABSENT_MARKERS[0] not in line)
    R.arm("absent FAULT: a .md with the items line removed is caught", not absent_ok(cut, packs[4]))

    # hashes
    exp = {k: sha256_lf(p) for k, p in SOURCES.items()}
    R.arm("hashes CONTROL: every pack's source sha256 equals the file's own (7 sources)",
          all(packs[c]["sources"] == exp for c in chapters) and len(exp) == 7)
    R.arm("hashes CONTROL: the generator sha256 is the generator's own",
          all(packs[c]["generator"]["sha256"] == sha256_lf(R.gen) for c in chapters))
    again = R.scratch("again")
    R.run(["--all"], again)
    same = all(open(os.path.join(fresh, "ch%d.%s" % (c, x)), "rb").read() ==
               open(os.path.join(again, "ch%d.%s" % (c, x)), "rb").read() for c in chapters for x in ("json", "md"))
    R.arm("hashes CONTROL: two runs give identical bytes (a determinism check, not a replication)", same)
    d = R.scratch("hash_fault", world_files=True)
    with open(os.path.join(d, "world", "trainers.json"), "ab") as f:
        f.write(b"\n")
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    if rc == 0:
        hp = load(os.path.join(d, "out", "ch4.json"))["sources"]
        k = "ai_player/knowledge/world/trainers.json"
        changed = sorted(x for x in exp if hp.get(x) != exp[x])
        R.arm("hashes FAULT: one changed source changes exactly its own hash (changed: %s)" % changed,
              changed == [k] and hp[k] == sha256_lf(os.path.join(d, "world", "trainers.json")))
    else:
        R.arm("hashes FAULT: the scratch generation ran", False, err.strip()[-200:])

    crlf_arms(R, fresh, chapters, exp)

    # empty chapter
    d = R.scratch("empty")
    rc, _, err = R.run([99], d)
    R.arm("empty FAULT: chapter 99 exits 2 naming it and writes nothing",
          rc == 2 and "chapter 99" in err and not os.listdir(d), err.strip()[-160:])
    rc, _, _ = R.run([4], R.scratch("empty_control"))
    R.arm("empty CONTROL: chapter 4 exits 0", rc == 0)

    routekey_arms(R, packs, chapters)

    # pin
    d = R.scratch("pin_fault", world_files=True)
    tj = load(os.path.join(d, "world", "trainers.json"))
    tj["_source"] = "pret/pokeemerald@" + "0" * 40
    save(tj, os.path.join(d, "world", "trainers.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    R.arm("pin FAULT: one input's _source pin changed exits 2 naming trainers.json",
          rc == 2 and "trainers.json" in err and "pin" in err, err.strip()[-200:])
    with open(PIN, encoding="utf-8") as f:
        pin = f.read().strip()
    R.arm("pin CONTROL: the real inputs pass and every pack names tools/decomp.pin (%s)" % pin[:12],
          all(packs[c]["decomp_pin"] == pin for c in chapters) and len(pin) == 40)

    # unknown area map, unknown trainer
    d = R.scratch("area_fault", world_files=True)
    cj = load(os.path.join(d, "world", "campaign.json"))
    e4 = next(e for e in cj["entries"] if e["chapter"] == 4)
    e4["area"] = [a + "_RENAMED" for a in e4["area"]]
    save(cj, os.path.join(d, "world", "campaign.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    R.arm("areamap FAULT: a renamed area map exits 2 naming it", rc == 2 and "RUSTBORO_CITY_GYM_RENAMED" in err,
          err.strip()[-200:])
    d = R.scratch("trainer_fault", world_files=True)
    mj = load(os.path.join(d, "world", "maps.json"))
    gym = next(m for m in mj["maps"] if m["id"] == "MAP_RUSTBORO_CITY_GYM")
    gym["trainers"][0]["trainers"] = ["TRAINER_NOBODY_AT_ALL"]
    save(mj, os.path.join(d, "world", "maps.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    R.arm("trainer FAULT: an unknown trainer symbol on a map exits 2 naming it",
          rc == 2 and "TRAINER_NOBODY_AT_ALL" in err, err.strip()[-200:])
    camp_area = {c: {"MAP_" + a for e in camp["entries"] if e["chapter"] == c for a in e["area"]} for c in chapters}
    R.arm("areamap/trainer CONTROL: each pack's area maps are exactly its entries' areas, and each has trainers",
          all({m["id"] for m in packs[c]["maps"] if m["role"] == "area"} == camp_area[c] and packs[c]["trainers"]
              for c in chapters))

    # an entry field outside the allowlist is not carried (CM4)
    d = R.scratch("entry_field", world_files=True)
    cj = load(os.path.join(d, "world", "campaign.json"))
    next(e for e in cj["entries"] if e["chapter"] == 4)["private_note"] = "never copy me"
    save(cj, os.path.join(d, "world", "campaign.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    carried = rc == 0 and any("private_note" in e for e in load(os.path.join(d, "out", "ch4.json"))["entries"])
    R.arm("entries FAULT: a field outside ENTRY_FIELDS planted in a ch4 entry is not carried into the pack",
          rc == 0 and not carried, err.strip()[-200:] or ("carried" if carried else ""))

    # non-normal wild rows are not carried (CM3)
    d = R.scratch("wild_avail", seasoned_files=True)
    ej = load(os.path.join(d, "seasoned", "encounters.json"))
    n104 = 0
    for row in ej["maps"]:
        if row.get("map") == "MAP_ROUTE104":
            row["availability"] = "mystery_gift_required"
            n104 += 1
    save(ej, os.path.join(d, "seasoned", "encounters.json"))
    rc, _, err = R.run([3], os.path.join(d, "out"), seasoned=os.path.join(d, "seasoned"))
    rows = [r for r in load(os.path.join(d, "out", "ch3.json"))["wild"] if r["map"] == "MAP_ROUTE104"] if rc == 0 else None
    R.arm("wild FAULT: Route104's rows (%d) marked not-normal in a scratch encounters.json leave the ch3 pack; "
          "CONTROL: the real ch3 pack has them" % n104,
          n104 >= 1 and rc == 0 and rows == [] and any(r["map"] == "MAP_ROUTE104" for r in packs[3]["wild"]),
          err.strip()[-200:])

    # claims: the one-way warp claim is not vacuous
    ow = [c["claim"] for c in packs[3]["claims"] if c["kind"] == "one_way_warp"]
    R.arm("claims CONTROL: ch3's warps are all two-way, said as a counted 'none of N' claim",
          len(ow) == 1 and ow[0].startswith("none of the ") and int(ow[0].split()[3]) > 0, str(ow))
    d = R.scratch("claims_fault", world_files=True)
    mj = load(os.path.join(d, "world", "maps.json"))
    woods = next(m for m in mj["maps"] if m["id"] == "MAP_PETALBURG_WOODS")
    woods["warps"][0]["dest_map"] = "MAP_ROUTE102"
    save(mj, os.path.join(d, "world", "maps.json"))
    rc, _, err = R.run([3], os.path.join(d, "out"), world=os.path.join(d, "world"))
    ow = [c["claim"] for c in load(os.path.join(d, "out", "ch3.json"))["claims"]
          if c["kind"] == "one_way_warp"] if rc == 0 else []
    R.arm("claims FAULT: Petalburg Woods' arrival warp 0 redirected -> one-way claims name ROUTE104 -> PETALBURG_WOODS",
          any(c.startswith("ROUTE104 warp") and "PETALBURG_WOODS" in c for c in ow)
          and not any(c.startswith("none of") for c in ow), (err or str(ow[:2]))[-200:])

    # --check
    rc, out, _ = R.run(["--all"], PACKS, extra=["--check"])
    R.arm("check CONTROL: --check on the committed packs (every chapter) exits 0", rc == 0,
          (out.strip().splitlines()[-1:] or [""])[0])
    d = R.scratch("check_fault")
    for c in chapters:
        for x in ("json", "md"):
            shutil.copyfile(os.path.join(fresh, "ch%d.%s" % (c, x)), os.path.join(d, "ch%d.%s" % (c, x)))
    with open(os.path.join(d, "ch4.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("hand edit\n")
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("check FAULT: an edited pack copy makes --check exit 1 naming it", rc == 1 and "ch4.md" in out)


def f1_arms(R, packs):
    """F1: a trainer object carries `script` or `label`; neither is refused naming its map."""
    def fixture():
        mod = import_generator(R.gen)
        maps_by_id = {"MAP_FIX": {"trainers": [
            {"source": "object", "object": 1, "script": "Fix_EventScript_Obj", "trainer_type": "TRAINER_TYPE_NORMAL",
             "sight": 2, "x": 1, "y": 1, "trainers": ["TRAINER_A"]},
            {"source": "script", "label": "Fix_EventScript_Label", "ref": "data/maps/Fix/scripts.inc:9",
             "trainers": ["TRAINER_B"]}]}}
        tby = {s: {"id": i, "name": s, "class_name": "C", "double": False, "flag": 1000 + i,
                   "party": [{"species": "SPECIES_X", "level": 5}], "ref": "r"}
               for i, s in enumerate(("TRAINER_A", "TRAINER_B"))}
        got = {t["symbol"]: t["seen"][0]["script"] for t in mod.trainers_on(["MAP_FIX"], ["MAP_FIX"], maps_by_id, tby)}
        return got == {"TRAINER_A": "Fix_EventScript_Obj", "TRAINER_B": "Fix_EventScript_Label"}, str(got)
    R.guarded("F1 CONTROL: a fixture object with `script` and one with `label` each give their script", fixture)

    def neither():
        mod = import_generator(R.gen)
        maps_by_id = {"MAP_FIX": {"trainers": [{"source": "script", "ref": "x", "trainers": ["TRAINER_A"]}]}}
        tby = {"TRAINER_A": {"id": 1, "name": "A", "class_name": "C", "double": False, "flag": 1001,
                             "party": [{"species": "SPECIES_X", "level": 5}], "ref": "r"}}
        try:
            mod.trainers_on(["MAP_FIX"], ["MAP_FIX"], maps_by_id, tby)
        except mod.PackError as exc:
            return "MAP_FIX" in str(exc), str(exc)
        return False, "no PackError"
    R.guarded("F1 FAULT: a fixture object with neither `script` nor `label` raises PackError naming its map", neither)

    want = {(19, "TRAINER_MAXIE_MOSSDEEP"): "MossdeepCity_SpaceCenter_2F_EventScript_MaxieTrainer",
            (24, "TRAINER_WALLACE"): "EverGrandeCity_ChampionsRoom_EventScript_Wallace"}
    got = {k: [s.get("script") for t in packs[k[0]]["trainers"] if t["symbol"] == k[1] for s in t["seen"]]
           for k in want}
    R.arm("F1 CONTROL: the real ch19 and ch24 packs cite the map-script battles by their labels (Maxie, Wallace)",
          all(got[k] == [v] for k, v in want.items()), str(got))
    d = R.scratch("f1_fault", world_files=True)
    mj = load(os.path.join(d, "world", "maps.json"))
    room = next(m for m in mj["maps"] if m["id"] == "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM")
    obj = next(o for o in room["trainers"] if o["trainers"] == ["TRAINER_WALLACE"])
    had = obj.pop("label", None)
    save(mj, os.path.join(d, "world", "maps.json"))
    rc, _, err = R.run([24], os.path.join(d, "out"), world=os.path.join(d, "world"))
    R.arm("F1 FAULT: Wallace's `label` removed in a scratch maps.json -> ch24 exits 2 naming the Champion's room",
          had and rc == 2 and "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM" in err and "Traceback" not in err,
          err.strip()[-200:])


def f2_arms(R, packs, mds):
    """F2: the cap never refuses a chapter; a summarised .md keeps every load-bearing item."""
    sizes = {c: len(mds[c].encode("utf-8")) for c in mds}
    summ = sorted(c for c in mds if "SUMMARISED to fit the cap" in mds[c])
    R.arm("F2 CONTROL: every .md <= %d bytes (largest ch%d, %d) and at least one chapter was summarised (%s)" % (
        MD_CAP, max(sizes, key=sizes.get), max(sizes.values()), summ),
          all(s <= MD_CAP for s in sizes.values()) and summ)
    for c in summ:
        print("      ch%d summarised: %s" % (c, re.search(r"SUMMARISED to fit the cap \(level \d", mds[c]).group(0)))

    def control():
        mod = import_generator(R.gen)
        bad = {c: mod.check_md_complete(packs[c], mds[c]) for c in mds}
        bad = {c: v for c, v in bad.items() if v}
        return not bad, str(bad)[:300]
    R.guarded("F2 CONTROL: check_md_complete finds nothing on every generated .md (%d)" % len(mds), control)

    def fault(c, name, mutate, needle):
        def body():
            mod = import_generator(R.gen)
            lines = mds[c].split("\n")
            new = mutate(lines)
            if new is None:
                return False, "the planted item was not found in ch%d.md" % c
            got = mod.check_md_complete(packs[c], "\n".join(new))
            return any(needle in x for x in got), str(got)[:300]
        R.guarded("F2 FAULT: summarised ch%d.md with %s is caught" % (c, name), body)

    def drop(pred):
        def m(lines):
            idx = [i for i, ln in enumerate(lines) if pred(ln)]
            return None if not idx else lines[:idx[0]] + lines[idx[0] + 1:]
        return m

    c13 = 13 if 13 in summ else (summ[0] if summ else 13)
    boss = packs[c13]["bosses"][-1] if packs[c13]["bosses"] else None
    last_mon = ("  - %s Lv%d " % (boss["party"][-1]["species"][8:], boss["party"][-1]["level"])) if boss else "\0"
    fault(c13, "the last boss's last mon removed", lambda ls: (
        None if not boss else
        (lambda i: ls[:i] + ls[i + 1:])(max(i for i, ln in enumerate(ls) if ln.startswith(last_mon)))), "md boss")
    dbl = next((t for t in packs[c13]["trainers"] if t["in_area"] and t["double"]), None)
    fault(c13, "a DOUBLE battle line removed", drop(lambda ln: dbl and "`%s`" % dbl["symbol"][8:] in ln and
                                                   "DOUBLE" in ln), "md trainer")
    fault(c13, "a claim removed", drop(lambda ln: ln.startswith("3. [")), "md claim 3")
    hm = packs[c13]["hms"][0]["move"] if packs[c13]["hms"] else "\0"
    fault(c13, "an HM line removed", drop(lambda ln: ln.startswith("- %s (" % hm)), "md HM")
    fault(c13, "an area map's links line removed", drop(lambda ln: ln.startswith("- **ROUTE119** (")),
          "md links line")
    fault(c13, "a per-map summary line removed", drop(lambda ln: re.match(r"- [A-Z0-9_]+: \d+ ordinary trainer", ln)),
          "md summary line")
    fault(c13, "'none fought' added", lambda ls: ls + ["- none fought in this chapter's entries"], "none fought")

    # a forced summary of a small chapter still holds every load-bearing item, and fits
    full4 = len(mds[4].encode("utf-8"))
    d = R.scratch("f2_force")
    rc, out, err = R.run([4], d, extra=["--md-cap", str(full4 - 1)])
    md4 = open(os.path.join(d, "ch4.md"), encoding="utf-8").read() if rc == 0 else ""
    R.arm("F2 CONTROL: ch4 with the cap one byte under its full size is summarised, fits, and passes its own "
          "completeness check (exit 0)", rc == 0 and "SUMMARISED to fit the cap" in md4 and
          len(md4.encode("utf-8")) < full4, (err or out).strip()[-200:])
    rc, _, err = R.run([4], R.scratch("size_fault"), extra=["--md-cap", "2000"])
    R.arm("F2 FAULT: a cap the load-bearing part cannot fit (2000) still refuses with exit 2 naming the cap",
          rc == 2 and "cap" in err, err.strip()[-160:])


def f3_arms(R, packs):
    """F3: the pack is checked against an independent selection; an omission is named and stops the run."""
    def control():
        mod = import_generator(R.gen)
        data, hashes = mod.load_inputs(WORLD, SEASONED)
        bad = {}
        for c in sorted(packs):
            exp, problems = mod.expected_selection(c, data)
            got = problems + mod.check_complete(packs[c], exp)
            if got:
                bad[c] = got[:2]
        return not bad, str(bad)[:300]
    R.guarded("F3 CONTROL: expected_selection + check_complete find nothing on all %d real packs" % len(packs), control)

    # pack level: one item per category removed from a real pack
    def pack_fault(c, name, mutate, needle):
        def body():
            mod = import_generator(R.gen)
            data, _ = mod.load_inputs(WORLD, SEASONED)
            exp, _problems = mod.expected_selection(c, data)
            p = copy.deepcopy(packs[c])
            if mutate(p) is False:
                return False, "the item to remove was not found in ch%d" % c
            got = mod.check_complete(p, exp)
            return any(needle in x for x in got), str(got)[:300]
        R.guarded("F3 FAULT (pack): ch%d %s is named" % (c, name), body)

    def rm(listname, pred):
        def m(p):
            n = len(p[listname])
            p[listname] = [x for x in p[listname] if not pred(x)]
            return len(p[listname]) < n or False
        return m

    def edit_trainer(sym, fn):
        def m(p):
            t = next((t for t in p["trainers"] if t["symbol"] == sym), None)
            if t is None:
                return False
            fn(t)
        return m

    def drop_claim(kind, text):
        return rm("claims", lambda c: c["kind"] == kind and text in c["claim"])

    pack_fault(4, "boss ROXANNE_1 removed", rm("bosses", lambda b: b["id"] == "TRAINER_ROXANNE_1"),
               "MISSING boss TRAINER_ROXANNE_1")
    pack_fault(1, "area trainer AMY_AND_LIV_1 removed", rm("trainers", lambda t: t["symbol"] == "TRAINER_AMY_AND_LIV_1"),
               "MISSING trainer TRAINER_AMY_AND_LIV_1")
    pack_fault(4, "ring trainer BRENDAN_RUSTBORO_MUDKIP removed",
               rm("trainers", lambda t: t["symbol"] == "TRAINER_BRENDAN_RUSTBORO_MUDKIP"),
               "MISSING trainer TRAINER_BRENDAN_RUSTBORO_MUDKIP")
    pack_fault(3, "LYLE's levels truncated to 3", edit_trainer("TRAINER_LYLE", lambda t: (
        t.__setitem__("levels", t["levels"][:3]))), "WRONG trainer TRAINER_LYLE party")
    pack_fault(1, "AMY_AND_LIV_1's double flag cleared", edit_trainer("TRAINER_AMY_AND_LIV_1", lambda t: (
        t.__setitem__("double", False))), "WRONG trainer TRAINER_AMY_AND_LIV_1 double")
    pack_fault(4, "JOSH's species emptied", edit_trainer("TRAINER_JOSH", lambda t: t.__setitem__("species", [])),
               "WRONG trainer TRAINER_JOSH party")
    pack_fault(4, "ring map RUSTBORO_CITY removed", rm("maps", lambda m: m["id"] == "MAP_RUSTBORO_CITY"),
               "MISSING ring map MAP_RUSTBORO_CITY")

    def no_conn(p):
        row = next(r for r in p["links"] if r["map"] == "MAP_ROUTE103")
        n = len(row["connections"])
        row["connections"] = [c for c in row["connections"] if c["map"] != "MAP_ROUTE110"]
        return len(row["connections"]) < n or False
    pack_fault(1, "connection ROUTE103 -> ROUTE110 removed", no_conn, "MISSING connection on MAP_ROUTE103")

    def no_warp(p):
        row = next(r for r in p["links"] if r["map"] == "MAP_RUSTBORO_CITY_GYM")
        if not row["warps"]:
            return False
        row["warps"] = row["warps"][:-1]
    pack_fault(4, "the Gym's last warp removed", no_warp, "MISSING warp on MAP_RUSTBORO_CITY_GYM")
    pack_fault(4, "a warp into the Gym removed", lambda p: (bool(p["warps_in"]) and p.__setitem__(
        "warps_in", p["warps_in"][1:])) if p["warps_in"] else False, "MISSING warp into the area")
    pack_fault(4, "HM CUT removed", rm("hms", lambda h: h["move"] == "CUT"), "MISSING HM CUT")
    pack_fault(3, "Route104's water wild row removed",
               rm("wild", lambda r: r["map"] == "MAP_ROUTE104" and r["method"] == "water"), "MISSING wild row")
    pack_fault(3, "a non-normal wild row added", lambda p: p["wild"].append(dict(p["wild"][0], method="fake")),
               "EXTRA wild row")
    pack_fault(4, "the boss_team claim removed", drop_claim("boss_team", "ROXANNE_1"), "[boss_team]")
    pack_fault(4, "the badge progress_flag claim removed", drop_claim("progress_flag", "FLAG_BADGE01_GET"),
               "[progress_flag]")
    pack_fault(1, "AMY_AND_LIV_1's double_battle claim removed", drop_claim("double_battle", "AMY_AND_LIV_1"),
               "[double_battle]")
    pack_fault(7, "a requires-Flash claim removed", drop_claim("hm_gate", "requires Flash"), "requires Flash")
    pack_fault(13, "the scripted_battle claim removed", drop_claim("scripted_battle", "trigger tile"),
               "[scripted_battle]")
    pack_fault(17, "a one-way warp claim removed", drop_claim("one_way_warp", "AQUA_HIDEOUT_B2F warp 9"),
               "[one_way_warp]")
    pack_fault(3, "the counted 'none of N' warp claim removed", drop_claim("one_way_warp", "none of the"),
               "none of the")

    # input level: an item lost from one input, named by another, must stop the run with exactly that finding
    def input_fault(name, chapter, edit, needles, seasoned=False):
        d = R.scratch("f3_" + re.sub(r"\W+", "_", name), world_files=not seasoned, seasoned_files=seasoned)
        found = edit(d)
        rc, _, err = R.run([chapter], os.path.join(d, "out"),
                           world=os.path.join(d, "world") if not seasoned else WORLD,
                           seasoned=os.path.join(d, "seasoned") if seasoned else SEASONED)
        n = findings_count(err)
        R.arm("F3 FAULT (input): %s -> ch%d exits 2 with exactly 1 finding naming it" % (name, chapter),
              found and rc == 2 and n == 1 and all(x in err for x in needles), err.strip()[-300:])

    def edit_json(name, fn):
        def e(d):
            path = os.path.join(d, "world", name)
            obj = load(path)
            ok = fn(obj)
            save(obj, path)
            return ok
        return e

    def drop_boss(obj):
        n = len(obj["bosses"])
        obj["bosses"] = [b for b in obj["bosses"] if b["id"] != "TRAINER_ROXANNE_1"]
        return len(obj["bosses"]) == n - 1

    def drop_object(map_id, sym):
        """`sym` removed from every trainer object on the map (an object left with no trainer is removed)."""
        def fn(obj):
            m = next(x for x in obj["maps"] if x["id"] == map_id)
            hit = sum(sym in o["trainers"] for o in m["trainers"])
            for o in m["trainers"]:
                o["trainers"] = [s for s in o["trainers"] if s != sym]
            m["trainers"] = [o for o in m["trainers"] if o["trainers"]]
            return hit >= 1
        return fn

    def drop_fmb(move):
        def fn(obj):
            n = len(obj["field_move_badges"])
            obj["field_move_badges"] = [r for r in obj["field_move_badges"] if r["move"] != move]
            return len(obj["field_move_badges"]) == n - 1
        return fn

    def drop_conn(src, dst):
        def fn(obj):
            m = next(x for x in obj["maps"] if x["id"] == src)
            n = len(m["connections"])
            m["connections"] = [c for c in m["connections"] if c["map"] != dst]
            return len(m["connections"]) == n - 1
        return fn

    def warp_nowhere(obj):
        m = next(x for x in obj["maps"] if x["id"] == "MAP_RUSTBORO_CITY_GYM")
        m["warps"][0]["dest_map"] = "MAP_NOWHERE_AT_ALL"
        return True

    input_fault("boss row ROXANNE_1 removed from bosses.json", 4, edit_json("bosses.json", drop_boss),
                ["ROXANNE", "bosses.json has no row"])
    input_fault("ROXANNE_1's object removed from the Gym (an area map)", 4,
                edit_json("maps.json", drop_object("MAP_RUSTBORO_CITY_GYM", "TRAINER_ROXANNE_1")),
                ["TRAINER_ROXANNE_1", "MAP_RUSTBORO_CITY_GYM"])
    input_fault("BRENDAN_RUSTBORO_MUDKIP's object removed from RUSTBORO_CITY (a ring map)", 4,
                edit_json("maps.json", drop_object("MAP_RUSTBORO_CITY", "TRAINER_BRENDAN_RUSTBORO_MUDKIP")),
                ["TRAINER_BRENDAN_RUSTBORO_MUDKIP", "MAP_RUSTBORO_CITY"])
    input_fault("CUT's field_move_badges row removed (a badge won here)", 4, edit_json("campaign.json", drop_fmb("CUT")),
                ["BADGE01", "field_move_badges"])
    input_fault("SURF's field_move_badges row removed (a field move an entry needs)", 13,
                edit_json("campaign.json", drop_fmb("SURF")), ["ch13_route118 needs field move SURF", "no row"])
    input_fault("ROUTE103's connection to ROUTE110 removed (the area side)", 1,
                edit_json("maps.json", drop_conn("MAP_ROUTE103", "MAP_ROUTE110")),
                ["MAP_ROUTE110 connects", "MAP_ROUTE103"])
    input_fault("ROUTE110's connection to ROUTE103 removed (the ring side)", 1,
                edit_json("maps.json", drop_conn("MAP_ROUTE110", "MAP_ROUTE103")),
                ["MAP_ROUTE103 connects", "MAP_ROUTE110 has no connection back"])
    input_fault("the Gym's warp 0 sent to a map maps.json does not hold", 4, edit_json("maps.json", warp_nowhere),
                ["MAP_NOWHERE_AT_ALL"])

    # generator level: a copy of the generator under test with a planted omission exits 2 naming it
    with open(R.gen, encoding="utf-8") as f:
        src = f.read()
    for name, ((old, new), needle) in PLANTS.items():
        d = R.scratch("f3_plant_" + re.sub(r"\W+", "_", name))
        if src.count(old) != 1:
            R.arm("F3 FAULT (generator): %s" % name, False, "plant text occurs %d times (want 1)" % src.count(old))
            continue
        g = os.path.join(d, "make_chapter_pack.py")
        with open(g, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace(old, new))
        rc, _, err = R.run([4, 13], os.path.join(d, "out"), gen=g)
        R.arm("F3 FAULT (generator): a copy whose %s exits 2 naming it" % name,
              rc == 2 and needle in err and "Traceback" not in err, err.strip()[-200:])


def crlf_arms(R, fresh, chapters, exp):
    """The CRLF normalisation (inputs and --check) has arms that can fail."""
    d = R.scratch("crlf_input", world_files=True)
    p = os.path.join(d, "world", "trainers.json")
    to_crlf(os.path.join(WORLD, "trainers.json"), p)
    with open(p, "rb") as f:
        n_crlf = f.read().count(b"\r\n")
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    h = load(os.path.join(d, "out", "ch4.json"))["sources"].get("ai_player/knowledge/world/trainers.json") if rc == 0 \
        else None
    R.arm("CRLF CONTROL: a CRLF copy of trainers.json (%d CRLF) hashes as its LF original in the pack header" % n_crlf,
          n_crlf > 1000 and rc == 0 and h == exp["ai_player/knowledge/world/trainers.json"], err.strip()[-160:])
    d = R.scratch("crlf_packs")
    for c in chapters:
        for x in ("json", "md"):
            to_crlf(os.path.join(fresh, "ch%d.%s" % (c, x)), os.path.join(d, "ch%d.%s" % (c, x)))
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("CRLF CONTROL: CRLF copies of every pack pass --check", rc == 0, (out.strip().splitlines()[-1:] or [""])[0])
    with open(os.path.join(d, "ch5.md"), "rb") as f:
        raw = f.read()
    with open(os.path.join(d, "ch5.md"), "wb") as f:
        f.write(raw.replace(b"Chapter 5 pack", b"Chapter 5 Pack", 1))
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("CRLF FAULT: a CRLF pack copy with one changed byte still fails --check naming it",
          rc == 1 and "ch5.md" in out and "ch4.md" not in out, out.strip()[-160:])


def routekey_arms(R, packs, chapters):
    hits = [h for c in chapters for h in route_keys(packs[c]["entries"])]
    R.arm("routekeys CONTROL: no x/y/route/path/steps/coords key in any pack's campaign entries", not hits, str(hits[:3]))
    with open(EXTRACT_WORLD, encoding="utf-8") as f:
        ew = assigned_tuple(f.read(), "ROUTE_KEYS")
    with open(R.gen, encoding="utf-8") as f:
        gsrc = f.read()
    gk = assigned_tuple(gsrc, "ROUTE_KEYS")
    R.arm("routekeys CONTROL: the generator's ROUTE_KEYS equal extract_world.py's (read with ast)",
          ew == gk == ROUTE_KEYS, "%s %s" % (ew, gk))
    bad_src = gsrc.replace('ROUTE_KEYS = ("x", "y", "route", "path", "steps", "coords")',
                           'ROUTE_KEYS = ("x", "y", "route", "path", "steps")', 1)
    tricky = 'ROUTE_KEYS = ("x",  # a comment with a ) in it\n    "y")\n'
    R.arm("routekeys FAULT: a scratch copy of the generator with 'coords' dropped differs from extract_world.py's; "
          "a multi-line tuple with ')' in a comment reads as both its keys",
          bad_src != gsrc and assigned_tuple(bad_src, "ROUTE_KEYS") != ew and
          assigned_tuple(tricky, "ROUTE_KEYS") == ("x", "y"), str(assigned_tuple(bad_src, "ROUTE_KEYS")))
    for name, plant, want in (
            ("in a dict (needs.route)", lambda e: e["needs"].__setitem__("route", ["RUSTBORO_CITY"]), "needs.route"),
            ("inside a LIST (needs.badge_gates[0].steps)",
             lambda e: e["needs"].__setitem__("badge_gates", [{"steps": 3}]), "badge_gates[0].steps")):
        d = R.scratch("route_fault_" + want.replace(".", "_").replace("[", "_").replace("]", ""), world_files=True)
        cj = load(os.path.join(d, "world", "campaign.json"))
        e4 = next(e for e in cj["entries"] if e["chapter"] == 4)
        plant(e4)
        save(cj, os.path.join(d, "world", "campaign.json"))
        rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
        R.arm("routekeys FAULT: a route key planted %s in a ch4 entry exits 2 naming it" % name,
              rc == 2 and want in err and e4["id"] in err, err.strip()[-200:])


# ---------------------------------------------------------------- mutants
def run_mutants(gen, work, jobs):
    """Each mutant (a guard's CALL deleted, or one of the verify's 24) in a scratch copy; the selftest against that
    copy must FAIL (exit 1). Run `jobs` at a time; each copy has its own scratch folder."""
    with open(gen, encoding="utf-8") as f:
        src = f.read()
    todo, rows = [], []
    for group, table in (("guard", MUTANTS), ("verify", VERIFIER_MUTANTS)):
        for name, (old, new) in table.items():
            n = src.count(old)
            if n != 1:
                rows.append(("%s %s" % (group, name), False, "the mutant text occurs %d times (want 1)" % n))
                continue
            d = os.path.join(work, "mutants", re.sub(r"\W+", "_", "%s_%s" % (group, name)))
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d)
            path = os.path.join(d, "make_chapter_pack.py")
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(src.replace(old, new))
            todo.append(("%s %s" % (group, name), path, d))

    def one(item):
        label, path, d = item
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--generator", path,
                            "--work", os.path.join(d, "run"), "--skip-committed"],
                           capture_output=True, text=True, encoding="utf-8")
        fails = [ln for ln in p.stdout.splitlines() if ln.startswith("FAIL")]
        return label, p.returncode == 1 and bool(fails), (fails[0][:150] if fails else "NOT CAUGHT")

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        rows += list(ex.map(one, todo))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--generator", default=GEN_DEFAULT)
    ap.add_argument("--work", default=None, help="scratch folder (default: a temp folder, removed after)")
    ap.add_argument("--mutants", action="store_true")
    ap.add_argument("--jobs", type=int, default=8, help="mutants run at a time (default 8)")
    ap.add_argument("--skip-committed", action="store_true",
                    help="(used by --mutants) leave out the arms that compare with the committed packs")
    args = ap.parse_args(argv)
    t0 = time.time()
    tmp = None
    work = args.work
    if work is None:
        tmp = work = tempfile.mkdtemp(prefix="chapter_pack_selftest_")
    os.makedirs(work, exist_ok=True)
    R = Runner(os.path.abspath(args.generator), os.path.abspath(work))
    try:
        if args.skip_committed:
            # A mutant's output differs from the committed packs by construction (its own sha256 is in the header),
            # so --check would "catch" every mutant vacuously. The mutant's own output stands in for the committed
            # packs instead, and a mutant must be caught by an arm that tests BEHAVIOUR.
            global PACKS
            PACKS = R.scratch("stand-in-packs")
            R.run(["--all"], PACKS)
        all_arms(R)
        if args.mutants:
            for name, ok, detail in run_mutants(R.gen, R.work, args.jobs):
                R.arm("MUTANT %s is caught" % name, ok, detail)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    bad = [r for r in R.results if not r[1]]
    print("SELFTEST chapter_pack: %d/%d arms PASS (%.1f s)" % (len(R.results) - len(bad), len(R.results),
                                                               time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
