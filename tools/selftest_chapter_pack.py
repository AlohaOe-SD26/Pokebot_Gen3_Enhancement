#!/usr/bin/env python3
"""Selftest for tools/make_chapter_pack.py (spec S3-4, A5): every arm has a FAULT (the rule broken: it must be caught)
and a CONTROL (the healthy path passes).

    py -3.12 tools/selftest_chapter_pack.py                         # all arms on the real generator and inputs
    py -3.12 tools/selftest_chapter_pack.py --work DIR              # scratch folder for the fault inputs (default: temp)
    py -3.12 tools/selftest_chapter_pack.py --mutants --work DIR    # also: delete each guard's CALL in a scratch copy of
                                                                    # the generator; every mutant must fail some arm

INTENT: a chapter pack is what an agent reads instead of re-doing a chapter's recon, so a pack that silently drops a
trainer, hides that a section is missing, or carries a stale hash is worse than no pack. The arms:
  W3 recall   (the spec's real control for A5) milestones.json's hand-recon'd `trainers` table, an artefact built
              independently through `gh api` by extract_milestones.py, must be fully contained in the packs for
              chapters 1-4: every trainer (symbol and id), its defeat flag and its party levels (in order), in the
              pack's JSON and named with its flag in its .md. FAULT: a scratch maps.json with JOSH's object removed
              from the Rustboro Gym makes recall fall. The milestone -> pack chapter mapping is checked too (it is the
              identity: every milestone id is a campaign entry of the same chapter); FAULT: one chapter changed.
              Extras (pack trainers the table does not list) are printed, not hidden.
  size        CONTROL each .md <= 12 KB; FAULT --md-cap 2000 refuses (exit 2, naming the cap).
  absent      CONTROL the generated header names every absent section (items/gifts/marts/events, A6's traps, story
              flags) and says the decomp wins; FAULT a copy with the items line removed is caught.
  hashes      CONTROL the header's sha256 of every source equals the file's own, the generator's is its own, and two
              runs give identical bytes (determinism, not replication); FAULT one changed source changes that hash
              and only that one.
  empty       FAULT chapter 99 exits 2 naming it and writes nothing; CONTROL chapter 4 exits 0.
  routekeys   FAULT a `route` key planted in a chapter-4 campaign entry exits 2 naming it; CONTROL no x/y/route/
              path/steps/coords key in the pack's campaign entries, and ROUTE_KEYS equals extract_world.py's.
  pin         FAULT one input's `_source` pin changed exits 2 naming that file; CONTROL the real inputs pass.
  areamap     FAULT a renamed area map exits 2 naming it; trainer: FAULT an unknown trainer symbol exits 2 naming it.
  check       CONTROL --check on the committed packs exits 0; FAULT an edited pack copy exits 1.
The generator runs as a subprocess with EVERY path passed explicitly, so a scratch copy (a mutant) reads the same
inputs. Nothing here writes outside --work; the committed packs and ai_player/ are only read.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
GEN_DEFAULT = os.path.join(HERE, "make_chapter_pack.py")
WORLD = os.path.join(REPO, "ai_player", "knowledge", "world")
SEASONED = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
PIN = os.path.join(REPO, "tools", "decomp.pin")
PACKS = os.path.join(REPO, "PROJECT KNOWLEDGE", "chapter-packs")
MILESTONES = os.path.join(REPO, "ai_player", "knowledge", "milestones.json")
EXTRACT_WORLD = os.path.join(REPO, "ai_player", "gates", "extract_world.py")
CHAPTERS = (1, 2, 3, 4)
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
    "check_pins": ("    check_pins(data, pin)\n", "    pass\n"),
    "refuse_empty_chapter": ("    refuse_empty_chapter(raw, chapter)\n", "    pass\n"),
    "refuse_route_keys": ("    refuse_route_keys(raw)\n", "    pass\n"),
    "resolve_maps": ('resolve_maps(e["area"], maps_by_id)', '["MAP_" + n for n in e["area"]]'),
    "join_trainer": ("join_trainer(sym, trainers_by_symbol, mid)", "trainers_by_symbol[sym]"),
    "check_md_size": ("    check_md_size(md, md_cap)\n", "    pass\n"),
    "absent_header_lines": ('        a("> - " + line)\n', "        pass\n"),
    "source_hashes": ("            hashes[rel + name] = sha256_lf(path)\n",
                      '            hashes[rel + name] = "0" * 64\n'),
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


class Runner:
    def __init__(self, gen, work):
        self.gen, self.work = gen, work
        self.results = []

    def run(self, chapters, out, world=WORLD, seasoned=SEASONED, extra=()):
        cmd = [sys.executable, self.gen] + [str(c) for c in chapters] + [
            "--world", world, "--seasoned", seasoned, "--pin", PIN, "--out", out] + list(extra)
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return p.returncode, p.stdout, p.stderr

    def scratch(self, name, world_files=()):
        """A fresh scratch folder; with world_files, a copy of the real world/ folder to break."""
        d = os.path.join(self.work, name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        if world_files:
            os.makedirs(os.path.join(d, "world"))
            for n in os.listdir(WORLD):
                if n.endswith(".json"):
                    shutil.copyfile(os.path.join(WORLD, n), os.path.join(d, "world", n))
        return d

    def arm(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail) if detail else ""))


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


def read_packs(folder, chapters=CHAPTERS):
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


def tuple_in_source(text, name):
    m = re.search(r"^%s\s*=\s*\(([^)]*)\)" % name, text, re.M)
    return tuple(re.findall(r'"([^"]+)"', m.group(1))) if m else None


# ---------------------------------------------------------------- the arms
def all_arms(R):
    ms = load(MILESTONES)
    fresh = R.scratch("fresh")
    rc, out, err = R.run(CHAPTERS, fresh)
    R.arm("generate ch1-4 from the real inputs exits 0", rc == 0, (err or out).strip().splitlines()[-1:] and
          (err or out).strip().splitlines()[-1])
    if rc != 0:
        return
    packs, mds = read_packs(fresh)

    # W3 recall
    h, t, miss, extras = recall(packs, mds, ms)
    R.arm("W3 CONTROL: recall on freshly generated ch1-4 packs is 100%% (%d/%d facts, %d table trainers)" % (
        h, t, len(ms["trainers"])), h == t and t == 3 * len(ms["trainers"]) and t > 0, "; ".join(miss[:3]))
    for c in CHAPTERS:
        print("      extras ch%d (pack trainers on area maps the table does not list): %d %s" % (
            c, len(extras[c]), ", ".join(x.replace("TRAINER_", "") for x in extras[c])))
    if os.path.isdir(PACKS) and all(os.path.isfile(os.path.join(PACKS, "ch%d.json" % c)) for c in CHAPTERS):
        cp, cm = read_packs(PACKS)
        h2, t2, miss2, _ = recall(cp, cm, ms)
        R.arm("W3 CONTROL: recall on the COMMITTED packs is 100%% (%d/%d)" % (h2, t2), h2 == t2 and t2 > 0,
              "; ".join(miss2[:3]))
    else:
        R.arm("W3 CONTROL: the committed packs exist", False, "missing under %s" % PACKS)
    d = R.scratch("w3_fault", world_files=True)
    maps = load(os.path.join(d, "world", "maps.json"))
    gym = next(m for m in maps["maps"] if m["id"] == "MAP_RUSTBORO_CITY_GYM")
    before = len(gym["trainers"])
    gym["trainers"] = [o for o in gym["trainers"] if o["trainers"] != ["TRAINER_JOSH"]]
    save(maps, os.path.join(d, "world", "maps.json"))
    rc, _, err = R.run(CHAPTERS, os.path.join(d, "out"), world=os.path.join(d, "world"))
    if rc == 0:
        fp, fm = read_packs(os.path.join(d, "out"))
        h3, t3, miss3, _ = recall(fp, fm, ms)
        R.arm("W3 FAULT: JOSH's object removed from a scratch maps.json -> recall falls (%d/%d) naming JOSH" % (h3, t3),
              before - len(gym["trainers"]) == 1 and h3 < t3 and any("JOSH" in x for x in miss3),
              "; ".join(miss3[:2]))
    else:
        R.arm("W3 FAULT: the scratch generation ran", False, err.strip()[-200:])
    camp = load(os.path.join(WORLD, "campaign.json"))
    errs = chapter_mapping_errors(ms, camp)
    R.arm("W3 mapping CONTROL: every milestone id is a campaign entry of the SAME chapter (%d milestones)" % len(
        ms["milestones"]), not errs and len(ms["milestones"]) == 20, "; ".join(errs[:3]))
    bad = json.loads(json.dumps(ms))
    bad["milestones"][-1]["chapter"] = 5
    R.arm("W3 mapping FAULT: one milestone's chapter changed is reported",
          any(bad["milestones"][-1]["id"] in x for x in chapter_mapping_errors(bad, camp)))

    # size
    sizes = {c: len(mds[c].encode("utf-8")) for c in CHAPTERS}
    R.arm("size CONTROL: every .md <= %d bytes %s" % (MD_CAP, sizes), all(s <= MD_CAP for s in sizes.values()))
    rc, _, err = R.run([4], R.scratch("size_fault"), extra=["--md-cap", "2000"])
    R.arm("size FAULT: --md-cap 2000 refuses with exit 2 naming the cap", rc == 2 and "cap" in err, err.strip()[-160:])

    # absent sections
    R.arm("absent CONTROL: every generated header names the absent sections and that the decomp wins",
          all(absent_ok(mds[c], packs[c]) for c in CHAPTERS))
    cut = "\n".join(line for line in mds[4].split("\n") if ABSENT_MARKERS[0] not in line)
    R.arm("absent FAULT: a .md with the items line removed is caught", not absent_ok(cut, packs[4]))

    # hashes
    exp = {k: sha256_lf(p) for k, p in SOURCES.items()}
    ok = all(packs[c]["sources"] == exp for c in CHAPTERS)
    R.arm("hashes CONTROL: every pack's source sha256 equals the file's own (7 sources)", ok and len(exp) == 7)
    R.arm("hashes CONTROL: the generator sha256 is the generator's own",
          all(packs[c]["generator"]["sha256"] == sha256_lf(R.gen) for c in CHAPTERS))
    again = R.scratch("again")
    R.run(CHAPTERS, again)
    same = all(open(os.path.join(fresh, "ch%d.%s" % (c, x)), "rb").read() ==
               open(os.path.join(again, "ch%d.%s" % (c, x)), "rb").read() for c in CHAPTERS for x in ("json", "md"))
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

    # empty chapter
    d = R.scratch("empty")
    rc, _, err = R.run([99], d)
    R.arm("empty FAULT: chapter 99 exits 2 naming it and writes nothing",
          rc == 2 and "chapter 99" in err and not os.listdir(d), err.strip()[-160:])
    rc, _, _ = R.run([4], R.scratch("empty_control"))
    R.arm("empty CONTROL: chapter 4 exits 0", rc == 0)

    # route keys
    hits = [h for c in CHAPTERS for h in route_keys(packs[c]["entries"])]
    R.arm("routekeys CONTROL: no x/y/route/path/steps/coords key in any pack's campaign entries", not hits, str(hits[:3]))
    with open(EXTRACT_WORLD, encoding="utf-8") as f:
        ew = tuple_in_source(f.read(), "ROUTE_KEYS")
    with open(R.gen, encoding="utf-8") as f:
        gk = tuple_in_source(f.read(), "ROUTE_KEYS")
    R.arm("routekeys CONTROL: the generator's ROUTE_KEYS equal extract_world.py's", ew == gk == ROUTE_KEYS, "%s %s" % (ew, gk))
    R.arm("routekeys FAULT: a differing tuple is detected",
          tuple_in_source('ROUTE_KEYS = ("x", "y")', "ROUTE_KEYS") != ROUTE_KEYS)
    d = R.scratch("route_fault", world_files=True)
    cj = load(os.path.join(d, "world", "campaign.json"))
    e4 = next(e for e in cj["entries"] if e["chapter"] == 4)
    e4["needs"]["route"] = ["RUSTBORO_CITY", "RUSTBORO_CITY_GYM"]
    save(cj, os.path.join(d, "world", "campaign.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    R.arm("routekeys FAULT: a `route` key planted in a ch4 entry's needs exits 2 naming it",
          rc == 2 and "route" in err and e4["id"] in err, err.strip()[-200:])

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
          all(packs[c]["decomp_pin"] == pin for c in CHAPTERS) and len(pin) == 40)

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
    camp_area = {c: {"MAP_" + a for e in camp["entries"] if e["chapter"] == c for a in e["area"]} for c in CHAPTERS}
    R.arm("areamap/trainer CONTROL: each pack's area maps are exactly its entries' areas, and each has trainers",
          all({m["id"] for m in packs[c]["maps"] if m["role"] == "area"} == camp_area[c] and packs[c]["trainers"]
              for c in CHAPTERS))

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
    rc, out, _ = R.run(CHAPTERS, PACKS, extra=["--check"])
    R.arm("check CONTROL: --check on the committed packs exits 0", rc == 0, out.strip().splitlines()[-1:] and
          out.strip().splitlines()[-1])
    d = R.scratch("check_fault")
    for c in CHAPTERS:
        for x in ("json", "md"):
            shutil.copyfile(os.path.join(fresh, "ch%d.%s" % (c, x)), os.path.join(d, "ch%d.%s" % (c, x)))
    with open(os.path.join(d, "ch4.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("hand edit\n")
    rc, out, _ = R.run(CHAPTERS, d, extra=["--check"])
    R.arm("check FAULT: an edited pack copy makes --check exit 1 naming it", rc == 1 and "ch4.md" in out)


def run_mutants(gen, work):
    """Each guard's CALL deleted in a scratch copy; the selftest against that copy must FAIL (exit 1)."""
    with open(gen, encoding="utf-8") as f:
        src = f.read()
    rows = []
    for name, (old, new) in MUTANTS.items():
        n = src.count(old)
        if n != 1:
            rows.append((name, False, "the call text occurs %d times (want 1)" % n))
            continue
        d = os.path.join(work, "mutants", name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        path = os.path.join(d, "make_chapter_pack.py")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace(old, new))
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--generator", path,
                            "--work", os.path.join(d, "run"), "--skip-committed"],
                           capture_output=True, text=True, encoding="utf-8")
        fails = [ln for ln in p.stdout.splitlines() if ln.startswith("FAIL")]
        rows.append((name, p.returncode == 1 and bool(fails), fails[0][:150] if fails else "NOT CAUGHT"))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--generator", default=GEN_DEFAULT)
    ap.add_argument("--work", default=None, help="scratch folder (default: a temp folder, removed after)")
    ap.add_argument("--mutants", action="store_true")
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
            R.run(CHAPTERS, PACKS)
        all_arms(R)
        if args.mutants:
            for name, ok, detail in run_mutants(R.gen, R.work):
                R.arm("MUTANT %s (call deleted) is caught" % name, ok, detail)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    bad = [r for r in R.results if not r[1]]
    print("SELFTEST chapter_pack: %d/%d arms PASS (%.1f s)" % (len(R.results) - len(bad), len(R.results),
                                                               time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
