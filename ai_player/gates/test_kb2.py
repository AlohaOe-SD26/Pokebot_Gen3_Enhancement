"""UNIT PROOFS of KB2 slice 1 (spec S3-4): extract_world.py, verify_world.py and the four files under knowledge/world/.

    py -3.12 ai_player/gates/test_kb2.py        (exit 0 = every test passed; needs the PINNED decomp clone)

Every test has a FAULT half (the rule broken: the check must fail) beside its CONTROL (the real data passes), so no
test can pass vacuously. The decomp-built objects are made ONCE (about a second) and every fault is made on a COPY:
a scratch skeleton, a scratch map.json read through an overlay, a deep copy of an output. Nothing is written inside the
repository (FrozenTree, provenance.py G1, watches it): every file a test writes goes to a temp folder.

  OutputsTests      the committed files are byte-identical to a fresh extraction (FAULT: one changed value differs); an
                    input's recorded hash ignores its line ends (2026-10-29; FAULT: a CRLF and an LF copy, whose raw bytes
                    differ, must hash the same).
  W1WithheldTests   WITHHELD_FIELDS is ("iv", "aiFlags") in both files; the scan of EVERY knowledge JSON (the library
                    and verify_world's CLI) finds a planted iv / aiFlags / ai_flags / IVs and nothing in the real tree;
                    heldItem is ALLOWED (USER RULING 44); the extractor's one door to disk refuses a withheld key.
  W2PlantTests      verify_world --plant reports exactly its four plants; the control has zero mismatches on the
                    fixed-seed sample (>= 60 trainers, 20 maps, 20 item records, every boss) and on every record; one
                    more FAULT per check family the plants do not touch (an item, a badge, a key-item citation, a
                    trainer object's join, an emptied party, a route key, a shared party, W4b, a level band, an area
                    map, the milestone ids, a hidden item, a dropped trainer, a dropped boss, a warp).
  W3RecallTests     every trainer, flag and level of milestones.json's table is in trainers.json, and each trainer is
                    PLACED (an object or a coord event) on a map of its chapter in maps.json (recall 100 %; the chapter
                    mapping is CHAPTER_OF below); FAULT: Calvin's object deleted from a scratch Route102 map.json.
  W4ConsistencyTests the first campaign ids (as many as milestones.json has: 28 since chapter 5) are milestones.json's; every area map resolves; every FLAG/VAR in the
                    outputs is in the event-flag table audit_flag_names.py reads; FAULT: a renamed area map makes the
                    generator exit non-zero naming it; a renamed milestone id and a phantom flag are caught.
  W4bOrderTests     every needed badge is awarded by an EARLIER entry's boss; FAULT: Flannery and Norman swapped.
  W5ShapeTests      all four party shapes parse (672 / 87 / 31 / 64 = the 854 TrainerMon arrays); only TRAINER_NONE is
                    empty; FAULT: each shape's regex dropped in turn; an extra array of an unknown shape (only the count
                    sees it); another trainer emptied; a macro of the wrong shape; a party array that does not exist.
  W6RouteTests      campaign.json holds no x, y, route, path, steps or coords; FAULT: each one planted.
  W8ConsumerTests   a pure reader of campaign.json says "no Surf learner" for a party with none at the entry that
                    needs Surf; CONTROL: a Surf learner in the party; FAULT: the need removed from the data.
  GuardTests        each remaining guard of the extractor refuses its broken input (the field-move cross-check, a
                    second badge in a leader's defeat script, an unknown boss or key item, a citation that is not in
                    the decomp, the label-closure bound, an unpinned decomp).
  NotReadTests      no play code names a world file, and check_fairness's knowledge glob does not see world/ (FAULT:
                    campaign.json copied to the knowledge top level is flagged).
The 2026-10-22 verify's REFIX (its F1-F3 and its 22 guard-deleting mutants):
  CitationTests     F1: every `file:line` must sit on a line that HOLDS its token (move + badge flag, badge flag,
                    `[TRAINER_X]`, the party array, the item, Norman's gate in its badge's label); FAULT: 15 citations
                    moved to unrelated lines (the verify's `src/party_menu.c:2` first), a missing file and a citation in
                    a place no rule covers, each reported on its record; the extractor refuses a gate outside the label.
  TabithaTests      F2: TRAINER_TABITHA_MOSSDEEP is ch19's (order, entry, fights, band 36-44, types), DERIVED from the
                    Space Center's SET_TRAINER_A/B pair; FAULT: her order nulled, ROXANNE's order 20 -> 3, ch4's band low
                    12 -> 2, a fight / an area boss / a type / a key item / a field move / a badge dropped; the extractor
                    refuses a half multi battle and a fight off the entry's area.
  GabbyTests        F3: Gabby and Ty's six fights (data/scripts/gabby_and_ty.inc) are on Routes 111/118/120; FAULT: one
                    removed from Route 118 is reported there and in the totals; a Lavaridge B1F battle dropped is
                    reported on 1F, whose file holds it; a coord event's battle dropped is reported.
  FieldFaultTests   one FAULT per field check of the verifier (flag, rematch_of, party_shape, sight, map header, role,
                    rematches, double/party_min, types, order, boss double), all in one verify run.
  ExtractorGuardFaultTests  an empty party array, an id with no block, a member of the wrong shape, the flag base gone;
                    W4b's no-giver branch; the plural `ivs` in both scans.
  PinTests          a clone at ANOTHER commit (a .git whose HEAD is not the pin) is refused by both programs; CONTROL:
                    the same folder at the pin is accepted.
Slice 2, stage 2a (items_gifts.json, extract_items.py): S2OutputTests, S2RuleTests (R-4..R-7), S2VerifierTests (every
plant (e)..(q) on its own one line), S2GuardTests, TFairTests; and its FIX ROUND 1 (the 2a verifier's F1-F6):
  S2FixRound1Tests  F1 `repeatable` only when nothing after the gift moves state (FAULT: a setflag planted after the Lava
                    Cookie lady); F2 no fall-through out of a data table (round 0: 427 such edges); F3 a menu's arms are
                    one choice (FAULT: the same arms behind no menu); F4 every CHOOSER_OF cite holds its token (FAULT:
                    each line off by one, a moved C file refuses the build); F5 story gates on the own var stay (FAULT:
                    a second setter of the SS Ticket's value outside the Hall of Fame unwords it); F6 the lottery's
                    words, the Mirage Tower's map condition, the Petalburg mart's setter by reference.
  S2VerifierFixTests the daily regex (both forms, set and unset); a golden cite moved off its line is reported; each
                    rule check (a1-a4) fires on a record the golden list does not hold.
Slice 2, stage 2b (events.json, extract_events.py; spec S3-4 "STAGE 2b"), each a FAULT beside its CONTROL:
  S2bOutputTests    the committed file equals a fresh build (a DETERMINISM check, left out of the mutant run).
  S2bBuildTests     the FRESH build (not the committed file) passes the independent verifier; W7's 13 events facts
                    (recon Q7 rows 1, 3-12, 14, 15) are findable by map and label; R-4..R-7 over the whole output; the
                    dead / excluded lists named; the re-measured counts and the values no verifier rule reads (trigger
                    dev evidence, copyvar sources, facility battles, warphole words); --check's comparison.
  S2bGuardTests     every guard refuses its broken input AND its call inside the build fires (check_sources, check_cites
                    per table, check_map_scripts, check_joins, check_gate_table's two clauses, check_maps_json,
                    refuse_all in build_all and at the door); an op line planted after `end` is listed dead.
  S2bUnitTests      change_of's branches, Persist's ranges, the SAFE whitelist, callee_returns / diverts, live_body,
                    persistent_test, set_aliases, on synthetic inputs where the call decides.
  S2bVerifierTests  verify_world's stage-2b reading: CONTROL 0 on the real file; each EV plant on exactly its own line;
                    its own units (ev_eval, ev_ids vs the extractor's ids, ev_saved, ev_live, ev_op, s2_strip's comment
                    removal, the candidate set); the CLI and selftest wiring; it imports no extractor.
"""
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
for p in (str(HERE), str(REPO)):
    if p not in sys.path:
        sys.path.insert(0, p)
import extract_world as ew  # noqa: E402
import verify_world as vw  # noqa: E402

KNOWLEDGE = REPO / "ai_player" / "knowledge"
WORLD = KNOWLEDGE / "world"
FLAG_TABLE = REPO / "sandbox-pokebot" / "modules" / "data" / "event_flags" / "emerald.txt"
VAR_TABLE = REPO / "sandbox-pokebot" / "modules" / "data" / "event_vars" / "emerald.txt"
#: W3's chapter mapping (milestones.json's trainers table has no chapter): the milestone that names or meets each one.
CHAPTER_OF = {
    1: ["MAY_ROUTE_103_TREECKO", "MAY_ROUTE_103_TORCHIC", "MAY_ROUTE_103_MUDKIP", "BRENDAN_ROUTE_103_TREECKO",
        "BRENDAN_ROUTE_103_TORCHIC", "BRENDAN_ROUTE_103_MUDKIP"],      # ch1_rival_route103
    2: ["CALVIN_1", "RICK", "TIANA", "ALLEN"],                         # ch2_route102 "ROUTE 102 and its trainers"
    3: ["GRUNT_PETALBURG_WOODS"],                                      # ch3_woods
    4: ["JOSH", "TOMMY", "ROXANNE_1"],                                 # ch4_gym_trainers (JOSH, TOMMY), ch4_roxanne
    5: ["GRUNT_RUSTURF_TUNNEL", "MAY_RUSTBORO_TREECKO", "MAY_RUSTBORO_TORCHIC", "MAY_RUSTBORO_MUDKIP",
        "BRENDAN_RUSTBORO_TREECKO", "BRENDAN_RUSTBORO_TORCHIC", "BRENDAN_RUSTBORO_MUDKIP"],  # ch5_rusturf_grunt, ch5_rival_*
    7: ["TAKAO", "JOCELYN", "LAURA", "BRENDEN", "CRISTIAN", "LILITH", "BRAWLY_1"],  # ch7_gym_trainers (six), ch7_brawly
}
#: what a reader of the world files would have to write (`world/` alone is not one: the AI's own `ai_player/world/`
#: package is named in comments and paths all over the play code)
PLAY_NAMES = ("knowledge/world", "trainers.json", "bosses.json", "maps.json", "campaign.json", "items_gifts.json",
              "events.json",
              # (P11-1, 2026-11-11) the way through each dark cave, read ONLY by its declared loader `knowledge/ways.py`
              "ways.json")

ROOT = None
D = None
OBJS = None
RAW = None
SCRIPTS = None
MILESTONES = json.loads((KNOWLEDGE / "milestones.json").read_text(encoding="utf-8"))


def setUpModule():
    global ROOT, D, OBJS, RAW, SCRIPTS
    ROOT = ew.resolve_decomp()  # no pinned clone: every test ERRORS (a loud failure, never a silent skip or pass)
    D = ew.Decomp(ROOT)
    OBJS = ew.build_all(D)
    RAW = vw.raw(ROOT)
    SCRIPTS = ew.map_scripts(D)


def fake_clone(tmp, head):
    """A folder git reads as a repository whose HEAD is `head` (a detached sha): a clone at ANOTHER commit for the pin
    test, made without any git command that writes."""
    for sub in ("objects", "refs"):
        os.makedirs(os.path.join(tmp, ".git", sub), exist_ok=True)
    with open(os.path.join(tmp, ".git", "HEAD"), "w", encoding="utf-8") as f:
        f.write(head + "\n")
    return tmp


def verify_lines(change):
    """The verifier's full report on a deep copy of the committed data after `change(data)`."""
    data = vw.load(str(WORLD))
    change(data)
    rep, _ = vw.verify(RAW, data, MILESTONES, None)
    return rep.lines


def assert_reported(test, lines, expected):
    """Each (record line prefix, substring) is on a line of the report: the check that owns it fired."""
    for prefix, sub in expected:
        hit = [ln for ln in lines if ln.startswith(prefix + ":")]
        test.assertTrue(hit and sub in hit[0], "%s / %r not reported; lines: %s" % (prefix, sub, [ln[:300] for ln in lines]))


def entry(data, eid):
    """One campaign entry of verify_world's data dict (keyed 'campaign') or of the campaign object itself."""
    return next(e for e in data.get("campaign", data)["entries"] if e["id"] == eid)


def boss(data, bid):
    return next(b for b in data["bosses"]["bosses"] if b["id"] == bid)


def trainer(data, sym):
    """One trainer of verify_world's data dict (keyed 'trainers') or of the trainers object itself."""
    ts = data["trainers"]
    return next(t for t in (ts["trainers"] if isinstance(ts, dict) else ts) if t["symbol"] == sym)


def map_rec(data, mid):
    return next(m for m in data["maps"]["maps"] if m["id"] == mid)


class OverlayDecomp(ew.Decomp):
    """The pinned decomp with some files replaced by scratch copies (a FAULT reads a broken file, never the clone)."""

    def __init__(self, root, overrides):
        super().__init__(root)
        self.overrides = overrides

    def read(self, rel):
        if rel in self.overrides:
            self.used[rel] = "overlay"
            return self.overrides[rel]
        return super().read(rel)


def raw_text(rel):
    return (Path(ROOT) / rel).read_bytes().decode("utf-8")


def scratch_skeleton(change):
    sk = json.loads(Path(ew.SKELETON_DEFAULT).read_text(encoding="utf-8"))
    change(sk["entries"])
    return sk


def campaign_of(sk, scripts=None):
    o = OBJS
    maps, bosses = o["maps.json"]["maps"], o["bosses.json"]["bosses"]
    return ew.build_campaign(D, sk, MILESTONES, maps, bosses, o["trainers.json"]["trainers"],
                             o["campaign.json"]["field_move_badges"], scripts if scripts is not None else SCRIPTS)


def serial(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


class OutputsTests(unittest.TestCase):
    def test_committed_files_equal_a_fresh_extraction(self):
        for name in ew.OUTPUTS:
            self.assertEqual((WORLD / name).read_bytes(), serial(OBJS[name]), name)
        bad = copy.deepcopy(OBJS["bosses.json"])
        bad["bosses"][0]["party"][0]["level"] += 1
        self.assertNotEqual((WORLD / "bosses.json").read_bytes(), serial(bad))

    def test_input_hashes_do_not_depend_on_line_ends(self):
        """(2026-10-29) an input's recorded sha256 is taken with its line ends made "\\n": `campaign_skeleton.json` and
        `milestones.json` have no `eol` attribute, so another checkout's git writes their line ends its own way, and a
        raw-byte hash made the committed headers differ there (measured: a CRLF skeleton, an LF milestones file).
        FAULT: the raw bytes of a CRLF and an LF copy hash differently; `load_json` hashes them the SAME. CONTROL: one
        byte more hashes differently. And the committed headers hold `load_json`'s hashes of the real inputs."""
        text = Path(ew.SKELETON_DEFAULT).read_bytes().replace(b"\r\n", b"\n")
        with tempfile.TemporaryDirectory() as tmp:
            lf, crlf, more = (Path(tmp) / name for name in ("lf.json", "crlf.json", "more.json"))
            lf.write_bytes(text)
            crlf.write_bytes(text.replace(b"\n", b"\r\n"))
            more.write_bytes(text + b" ")
            self.assertNotEqual(lf.read_bytes(), crlf.read_bytes())  # the two copies really differ in bytes
            data_lf, sha_lf = ew.load_json(lf)
            data_crlf, sha_crlf = ew.load_json(crlf)
            self.assertEqual(data_lf, data_crlf)
            self.assertEqual(sha_lf, sha_crlf)  # FAULT half: a raw-byte hash would differ here
            self.assertNotEqual(sha_lf, ew.load_json(more)[1])  # CONTROL: other content, another hash
        skeleton_sha = ew.load_json(ew.SKELETON_DEFAULT)[1]
        milestones_sha = ew.load_json(ew.MILESTONES_DEFAULT)[1]
        campaign = json.loads((WORLD / "campaign.json").read_text(encoding="utf-8"))
        bosses = json.loads((WORLD / "bosses.json").read_text(encoding="utf-8"))
        self.assertEqual(campaign["_inputs"], {"campaign_skeleton.json": skeleton_sha, "milestones.json": milestones_sha})
        self.assertEqual(bosses["_inputs"]["campaign_skeleton.json"], skeleton_sha)


class W1WithheldTests(unittest.TestCase):
    def test_constant_is_the_ruling(self):
        self.assertEqual(ew.WITHHELD_FIELDS, ("iv", "aiFlags"))
        self.assertEqual(vw.WITHHELD, ew.WITHHELD_FIELDS)

    def test_scan_every_knowledge_file(self):
        n, hits = vw.withheld_scan(str(KNOWLEDGE))
        self.assertEqual(hits, [])
        world = sorted(p.name for p in WORLD.glob("*.json"))
        # slice 1's four + stage 2a's items_gifts + stage 2b's events + (P11-1, 2026-11-11) extract_ways' ways.json
        self.assertEqual(world, sorted(ew.OUTPUTS + (ei.OUT_NAME, xe.OUT_NAME, os.path.basename(xwy.OUT_DEFAULT))))
        self.assertGreaterEqual(n, len(list(KNOWLEDGE.rglob("*.json"))))
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(KNOWLEDGE, Path(tmp) / "k", ignore=shutil.ignore_patterns("*.py", "__pycache__"))
            p = Path(tmp) / "k" / "world" / "trainers.json"
            for key, where in (("iv", "party"), ("aiFlags", "trainer"), ("ai_flags", "trainer"), ("IVs", "party")):
                data = copy.deepcopy(OBJS["trainers.json"])
                rec = data["trainers"][265]
                (rec["party"][0] if where == "party" else rec)[key] = 0
                p.write_text(json.dumps(data), encoding="utf-8")
                _, hits = vw.withheld_scan(str(Path(tmp) / "k" / "world"))  # each spelling; the CLI arms scan the tree
                self.assertEqual(len(hits), 1, (key, hits))
                self.assertIn(key, hits[0][1])
            for tree, want in ((str(Path(tmp) / "k"), 1), (str(KNOWLEDGE), 0)):  # the CLI scans: FAULT, then CONTROL
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(vw.main(["--knowledge", tree]), want, buf.getvalue()[-400:])
                self.assertEqual("MISMATCH withheld" in buf.getvalue(), bool(want))

    def test_held_item_is_allowed(self):
        held = [p for t in OBJS["trainers.json"]["trainers"] for p in t["party"] if p.get("held_item")]
        self.assertGreater(len(held), 50)
        obj = copy.deepcopy(OBJS["trainers.json"])
        obj["trainers"][265]["party"][0]["heldItem"] = "ITEM_ORAN_BERRY"
        self.assertEqual(vw.withheld_hits_in(obj), [])
        self.assertEqual(ew.withheld_keys(obj), [])

    def test_extractor_door_refuses_a_withheld_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            ew.write_outputs(tmp, OBJS)  # CONTROL
            self.assertEqual((Path(tmp) / "maps.json").read_bytes(), (WORLD / "maps.json").read_bytes())
            for name, plant in (("trainers.json", lambda o: o["trainers"][3]["party"][0].__setitem__("iv", 250)),
                                ("bosses.json", lambda o: o["bosses"][0].__setitem__("aiFlags", 7))):
                objs = dict(OBJS)
                objs[name] = copy.deepcopy(OBJS[name])
                plant(objs[name])
                with self.assertRaises(ew.Refused):
                    ew.write_outputs(os.path.join(tmp, "f"), objs)
                self.assertFalse(os.path.exists(os.path.join(tmp, "f", "trainers.json")))


class W2PlantTests(unittest.TestCase):
    def test_plant_reports_exactly_the_four(self):
        ok, lines, keys = vw.plant_result(RAW, str(WORLD), MILESTONES, vw.DEFAULT_SEED)
        self.assertTrue(ok, lines)
        self.assertEqual(len(lines), 4)
        for k in keys:
            self.assertEqual(sum(1 for ln in lines if ln.startswith(k)), 1, (k, lines))

    def test_control_sample_and_full(self):
        rep, n = vw.verify(RAW, vw.load(str(WORLD)), MILESTONES, vw.DEFAULT_SEED)
        self.assertEqual(rep.lines, [])
        self.assertGreaterEqual(rep.counts["trainers"], 60)
        self.assertGreaterEqual(rep.counts["maps"], 20)
        self.assertGreaterEqual(rep.counts["items"], 20)
        self.assertEqual(n, (60, 20, 20))
        roles = [b["role"] for b in OBJS["bosses.json"]["bosses"]]
        self.assertEqual((roles.count("gym_leader"), roles.count("elite_four"), roles.count("champion")), (8, 4, 1))
        self.assertEqual(rep.counts["bosses"], len(roles))
        rep, _ = vw.verify(RAW, vw.load(str(WORLD)), MILESTONES, None)
        self.assertEqual(rep.lines, [])
        self.assertEqual(rep.counts["trainers"], 855)
        self.assertGreater(rep.counts["citations"], 2000)  # every citation of the four files was checked

    def _one(self, change, prefix, also=None):
        data = vw.load(str(WORLD))
        change(data)
        rep, _ = vw.verify(RAW, data, MILESTONES, None)
        self.assertEqual(len(rep.lines), 1 + (also is not None), rep.lines)
        self.assertTrue(rep.lines[0].startswith(prefix), rep.lines)
        if also:
            self.assertTrue(rep.lines[1].startswith(also), rep.lines)

    def test_more_faults(self):
        def item(data):  # the map's exact item-ball list and the item record both see it
            m = next(m for m in data["maps"]["maps"] if m["item_balls"])
            m["item_balls"][0]["item"] = "ITEM_MASTER_BALL"
        self._one(item, "MISMATCH map", also="MISMATCH item")

        def invented_ball(data):  # an item ball the decomp does not have: only the exact list sees it
            m = next(m for m in data["maps"]["maps"] if m["item_balls"])
            m["item_balls"].append(dict(m["item_balls"][0], x=999))
        self._one(invented_ball, "MISMATCH map")

        def badge(data):
            next(b for b in data["bosses"]["bosses"] if b["fight"] == "NORMAN")["badge"]["id"] = "BADGE04"
        self._one(badge, "MISMATCH boss TRAINER_NORMAN_1")

        def key_item(data):
            e = next(e for e in data["campaign"]["entries"] if e["needs"]["key_items"])
            e["needs"]["key_items"][0]["ref"] = "src/party_menu.c:1"
        self._one(key_item, "MISMATCH campaign ch13_winona")

        def join(data):
            m = next(m for m in data["maps"]["maps"] if m["id"] == "MAP_ROUTE102")
            m["trainers"][0]["trainers"] = []
        self._one(join, "MISMATCH map MAP_ROUTE102", also="MISMATCH totals map battles")

        def emptied(data):
            next(t for t in data["trainers"]["trainers"] if t["symbol"] == "TRAINER_SAWYER_1")["party"] = []
        self._one(emptied, "MISMATCH trainer TRAINER_SAWYER_1", also="MISMATCH totals empty parties")

        def route(data):
            data["campaign"]["entries"][5]["needs"]["steps"] = ["up", "up"]
        self._one(route, "MISMATCH campaign W6")

        def dup_party(data):
            ts = data["trainers"]["trainers"]
            ts[2]["party_ref"] = ts[1]["party_ref"]
        self._one(dup_party, "MISMATCH trainer", also="MISMATCH totals parties")  # its citation and the count

        def late_badge(data):  # W4b re-derived: Norman needing Winona's badge
            e = next(e for e in data["campaign"]["entries"] if e["id"] == "ch12_norman")
            e["needs"]["badges"].append("BADGE06")
        self._one(late_badge, "MISMATCH campaign ch12_norman")

        def band(data):
            data["campaign"]["entries"][30]["needs"]["level_band"]["high"] += 3
        self._one(band, "MISMATCH campaign %s" % OBJS["campaign.json"]["entries"][30]["id"])

        def area(data):
            data["campaign"]["entries"][44]["area"].append("ROUTE999")
        self._one(area, "MISMATCH campaign %s" % OBJS["campaign.json"]["entries"][44]["id"])

        def milestone(data):
            data["campaign"]["entries"][0]["chapter"] = 2
        self._one(milestone, "MISMATCH campaign milestones", also="MISMATCH campaign ch1_intro")  # + the skeleton's

        def hidden(data):
            m = next(m for m in data["maps"]["maps"] if m["hidden_items"])
            m["hidden_items"][0]["flag"] = "FLAG_HIDDEN_ITEM_ROUTE_999"
        self._one(hidden, "MISMATCH map", also="MISMATCH item")

    def _has(self, change, prefix):
        data = vw.load(str(WORLD))
        change(data)
        rep, _ = vw.verify(RAW, data, MILESTONES, None)
        self.assertTrue(any(ln.startswith(prefix) for ln in rep.lines), (prefix, rep.lines))

    def test_set_faults(self):
        def drop_trainer(data):
            ts = data["trainers"]["trainers"]
            ts.remove(next(t for t in ts if t["symbol"] == "TRAINER_SAWYER_1"))
        self._has(drop_trainer, "MISMATCH totals trainers")

        def drop_boss(data):
            bs = data["bosses"]["bosses"]
            bs.remove(next(b for b in bs if b["fight"] == "JUAN"))
        self._has(drop_boss, "MISMATCH bosses the set")
        self._has(drop_boss, "MISMATCH bosses the league")

        def warp(data):
            m = next(m for m in data["maps"]["maps"] if m["warps"])
            m["warps"][0]["dest_warp_id"] = 99
        self._has(warp, "MISMATCH map")


def shift(ref, by):
    rel, n = ref.rsplit(":", 1)
    return "%s:%d" % (rel, int(n) + by)


def var_conditional_outside(rel, label):
    """'rel:N' of the first `call_if/goto_if VAR_...` line of `rel` whose label is not `label` (a real conditional of
    the same file, so only the same-label rule can reject it)."""
    cur = None
    for i, ln in enumerate(raw_text(rel).split("\n"), 1):
        m = re.match(r"^([A-Za-z_]\w*)::?\s*$", ln)
        if m:
            cur = m.group(1)
        elif cur != label and re.match(r"^\s*(call|goto)_if\w*\s+VAR_\w+", ln):
            return "%s:%d" % (rel, i)
    raise AssertionError("no VAR conditional outside %s in %s" % (label, rel))


class CitationTests(unittest.TestCase):
    """F1 (the 2026-10-22 verify): a citation is checked for what its line SAYS, not merely that the line exists."""

    def test_the_verify_demos_are_mismatches(self):
        """FAULT: the verify's own four fields (a badge ref, a field move's ref and rule_ref, a boss's badge ref) moved
        to `src/party_menu.c:2` (an #include). be63abd1's verifier reported 0 mismatches for each."""
        def change(data):
            entry(data, "ch12_norman")["needs"]["badge_refs"]["BADGE01"][0] = "src/party_menu.c:2"
            entry(data, "ch13_route118")["needs"]["field_moves"][0]["ref"] = "src/party_menu.c:2"
            entry(data, "ch13_route118")["needs"]["field_moves"][0]["rule_ref"] = "src/party_menu.c:2"
            boss(data, "TRAINER_WATTSON_1")["badge"]["ref"] = "src/party_menu.c:2"
        assert_reported(self, verify_lines(change), [
            ("MISMATCH campaign ch12_norman", "src/party_menu.c:2"),
            ("MISMATCH campaign ch13_route118", "src/party_menu.c:2 (ref)"),
            ("MISMATCH campaign ch13_route118", "src/party_menu.c:2 (rule_ref)"),
            ("MISMATCH boss TRAINER_WATTSON_1", "src/party_menu.c:2"),
        ])

    def test_moved_citations_are_mismatches(self):
        """FAULT: each citation moved to a line that does not hold its token is reported on its record's line.
        (On be63abd1's verifier the first of these, Norman's BADGE01 -> src/party_menu.c:2, gave 0 mismatches.)"""
        gate_elsewhere = var_conditional_outside("data/maps/DewfordTown_Gym/scripts.inc",
                                                 "DewfordTown_Gym_EventScript_BrawlyDefeated")
        custom = next((b["id"], i) for b in OBJS["bosses.json"]["bosses"] for i, p in enumerate(b["party"])
                      if p["moves_source"].startswith("custom"))

        def change(data):
            nor = entry(data, "ch12_norman")["needs"]
            nor["badge_refs"]["BADGE01"][0] = "src/party_menu.c:2"                      # the verify's own demo
            nor["badge_gates"][1]["ref"] = gate_elsewhere                                 # a VAR conditional, wrong label
            entry(data, "ch13_route118")["needs"]["field_moves"][0]["ref"] = "src/party_menu.c:120"  # CUT's line
            entry(data, "ch14_mt_pyre")["needs"]["field_moves"][0]["rule_ref"] = "src/party_menu.c:2"
            entry(data, "ch18_tate_and_liza")["needs"]["party_min_ref"] = boss(data, "TRAINER_ROXANNE_1")["ref"]
            rox = boss(data, "TRAINER_ROXANNE_1")
            rox["badge"]["ref"] = shift(rox["badge"]["ref"], 1)
            tate = boss(data, "TRAINER_TATE_AND_LIZA_1")
            tate["notes"][0] = re.sub(r"trainers\.h:\d+", "trainers.h:%s" % rox["ref"].rsplit(":", 1)[1],
                                      tate["notes"][0])
            boss(data, custom[0])["party"][custom[1]]["moves_source"] = "custom (src/data/trainer_parties.h:1)"
            boss(data, "TRAINER_WATTSON_1")["ref"] = "src/nope.c:5"
            trainer(data, "TRAINER_SAWYER_1")["ref"] = trainer(data, "TRAINER_RICK")["ref"]
            trainer(data, "TRAINER_CALVIN_1")["party_ref"] = trainer(data, "TRAINER_RICK")["party_ref"]
            sc = next(t for t in map_rec(data, "MAP_MOSSDEEP_CITY_SPACE_CENTER_2F")["trainers"] if t["source"] == "script")
            champ = next(t for t in map_rec(data, "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM")["trainers"]
                         if t["source"] == "script")
            champ["label"], champ["ref"] = sc["label"], sc["ref"]      # a true label line, of ANOTHER map's file
            sc["ref"] = shift(sc["ref"], 1)
            win, brawly = boss(data, "TRAINER_WINONA_1"), boss(data, "TRAINER_BRAWLY_1")
            win["badge"] = dict(brawly["badge"])                        # a true setflag line, of ANOTHER gym's file
            fms = {r["move"]: r for r in data["campaign"]["field_move_badges"]}
            fms["SURF"]["move_ref"] = fms["FLY"]["move_ref"]
            fms["WATERFALL"]["ref"] = "src/party_menu.c:2"
            fms["DIVE"]["rule_ref"] = "src/party_menu.c:2"
            fms["DIVE"]["overworld_ref"] = "src/party_menu.c:2"
            data["trainers"]["trainers"][0]["comment"] = "see src/party_menu.c:120"     # a place no rule covers
        lines = verify_lines(change)
        assert_reported(self, lines, [
            ("MISMATCH campaign ch12_norman", "src/party_menu.c:2 (BADGE01[])"),
            ("MISMATCH campaign ch12_norman", "%s (ref): the line is not in the label" % gate_elsewhere),
            ("MISMATCH campaign ch13_route118", "src/party_menu.c:120 (ref)"),
            ("MISMATCH campaign ch14_mt_pyre", "src/party_menu.c:2 (rule_ref)"),
            ("MISMATCH campaign ch18_tate_and_liza", "(party_min_ref): the line is no block"),
            ("MISMATCH boss TRAINER_ROXANNE_1", "(ref): the line does not hold ['setflag FLAG_BADGE01_GET']"),
            ("MISMATCH boss TRAINER_TATE_AND_LIZA_1", "is not in TRAINER_TATE_AND_LIZA_1's trainers.h block"),
            ("MISMATCH boss %s" % custom[0], "src/data/trainer_parties.h:1 (moves_source)"),
            ("MISMATCH boss TRAINER_WATTSON_1", "src/nope.c:5 cites no line"),
            ("MISMATCH trainer TRAINER_SAWYER_1", "(ref): the line does not hold ['[TRAINER_SAWYER_1]']"),
            ("MISMATCH trainer TRAINER_CALVIN_1", "(party_ref)"),
            ("MISMATCH map MAP_MOSSDEEP_CITY_SPACE_CENTER_2F", "(ref): the line is not the label"),
            ("MISMATCH map MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM", "is not the map's own scripts.inc"),
            ("MISMATCH boss TRAINER_WINONA_1", "is not the file that battles TRAINER_WINONA_1"),
            ("MISMATCH field_move SURF", "(move_ref)"),
            ("MISMATCH field_move WATERFALL", "src/party_menu.c:2 (ref)"),
            ("MISMATCH field_move DIVE", "src/party_menu.c:2 (rule_ref)"),
            ("MISMATCH field_move DIVE", "src/party_menu.c:2 (overworld_ref)"),
            ("MISMATCH citation trainers/trainers[]/comment", "no citation rule covers"),
        ])

    def test_every_citation_holds_its_token(self):
        """CONTROL: the real files' citations all pass; the field moves cite the enum line that names move and badge."""
        rep, _ = vw.verify(RAW, vw.load(str(WORLD)), MILESTONES, None)
        self.assertEqual(rep.lines, [])
        for e in OBJS["campaign.json"]["entries"]:
            for fm in e["needs"]["field_moves"]:
                line = vw.line_at(RAW, fm["ref"])
                self.assertIn("FIELD_MOVE_" + fm["move"], line)
                self.assertIn("FLAG_%s_GET" % fm["badge"], line)
            for b, refs in e["needs"]["badge_refs"].items():
                for ref in refs:
                    self.assertIn("FLAG_%s_GET" % b, vw.line_at(RAW, ref))

    def test_extractor_refuses_a_gate_outside_the_badge_label(self):
        """The generator's own guard: Norman's gate line must share the defeat-script label of the badge's setflag."""
        def far_gate(es):
            next(e for e in es if e["id"] == "ch12_norman")["needs"]["badges"][0]["gate_needle"] = \
                "RustboroCity_Gym_EventScript_GiveRockTomb::"
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(far_gate))
        self.assertIn("BADGE01's gate line", str(cm.exception))


class TabithaTests(unittest.TestCase):
    """F2: a boss's campaign membership and order are DERIVED from the area's trainerbattle lines (the Space Center's
    TRAINER_BATTLE_SET_TRAINER_A/B pair), never left null by hand."""

    def test_tabitha_is_fought_in_ch19(self):
        """CONTROL (on be63abd1 her order was null and ch19's band was Maxie's 42-44 alone)."""
        tab = next(b for b in OBJS["bosses.json"]["bosses"] if b["id"] == "TRAINER_TABITHA_MOSSDEEP")
        e = entry(OBJS["campaign.json"], "ch19_space_center")
        self.assertEqual(tab["order"], e["order"])
        self.assertEqual(tab.get("entry"), "ch19_space_center")
        self.assertEqual(e["fights"], ["MAXIE_MOSSDEEP", "TABITHA_MOSSDEEP"])
        both = [p for sym in ("TRAINER_MAXIE_MOSSDEEP", "TRAINER_TABITHA_MOSSDEEP")
                for p in trainer(OBJS["trainers.json"], sym)["party"]]
        band = e["needs"]["level_band"]
        self.assertEqual((band["low"], band["high"]), (min(p["level"] for p in both), max(p["level"] for p in both)))
        self.assertLess(band["low"], 42)  # her L36-40 party is inside the band
        self.assertTrue(set(t for p in tab["party"] for t in p["types"]) <= set(e["needs"]["types_ahead"]))
        self.assertEqual(e["needs"]["types_ahead_of"], ["MAXIE_MOSSDEEP", "TABITHA_MOSSDEEP"])
        nulls = sorted(b["id"] for b in OBJS["bosses.json"]["bosses"] if b["order"] is None)
        self.assertEqual(nulls, ["TRAINER_STEVEN", "TRAINER_WALLY_VR_2"])  # fought in no entry: post-game
        self.assertIn("WALLY_VR_2", entry(OBJS["campaign.json"], "ch23_victory_road")["area_bosses"])

    def test_the_verify_demos_are_mismatches(self):
        """FAULT: the verify's two demos (ROXANNE order 20 -> 3; ch4's band low 12 -> 2), each 0 mismatches on be63abd1."""
        def change(data):
            boss(data, "TRAINER_ROXANNE_1")["order"] = 3
            entry(data, "ch4_roxanne")["needs"]["level_band"]["low"] = 2
        assert_reported(self, verify_lines(change), [("MISMATCH boss TRAINER_ROXANNE_1", "order"),
                                                     ("MISMATCH campaign ch4_roxanne", "level_band 2..15")])

    def test_verifier_catches_membership_band_and_dropped_needs(self):
        """FAULT: the verify's F2 demos (ROXANNE order 20 -> 3, ch4's band low 12 -> 2) and the membership itself."""
        def change(data):
            boss(data, "TRAINER_TABITHA_MOSSDEEP")["order"] = None
            boss(data, "TRAINER_ROXANNE_1")["order"] = 3
            entry(data, "ch4_roxanne")["needs"]["level_band"]["low"] = 2
            entry(data, "ch19_space_center")["fights"] = ["MAXIE_MOSSDEEP"]
            entry(data, "ch23_victory_road")["area_bosses"].remove("WALLY_VR_2")
            entry(data, "ch7_brawly")["needs"]["types_ahead"].pop()
            entry(data, "ch13_winona")["needs"]["key_items"] = []
            entry(data, "ch10_fallarbor")["needs"]["field_moves"] = []
            n = entry(data, "ch24_sidney")["needs"]
            n["badges"], n["badge_refs"] = [], {}
        assert_reported(self, verify_lines(change), [
            ("MISMATCH boss TRAINER_TABITHA_MOSSDEEP", "order/entry None/"),
            ("MISMATCH boss TRAINER_ROXANNE_1", "order/entry 3/"),
            ("MISMATCH campaign ch4_roxanne", "level_band 2..15"),
            ("MISMATCH campaign ch19_space_center", "fights ['MAXIE_MOSSDEEP'] != re-derived"),
            ("MISMATCH campaign ch23_victory_road", "area_bosses"),
            ("MISMATCH campaign ch7_brawly", "types_ahead"),
            ("MISMATCH campaign ch13_winona", "key items [] != the skeleton's"),
            ("MISMATCH campaign ch10_fallarbor", "field moves [] != the skeleton's"),
            ("MISMATCH campaign ch24_sidney", "badges [] != the skeleton's needs"),
        ])

    def test_extractor_guards_the_pair_and_the_area(self):
        """FAULT: a half multi battle (Tabitha's SET_TRAINER_B line gone) and a fight off the entry's area are refused."""
        rel = "data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc"
        half = dict(SCRIPTS)
        half[rel] = "\n".join(ln for ln in SCRIPTS[rel].split("\n") if "TRAINER_TABITHA_MOSSDEEP" not in ln)
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(lambda es: None), scripts=half)
        self.assertIn("multi battle", str(cm.exception))

        def off_area(es):
            e = next(e for e in es if e["id"] == "ch19_space_center")
            e["area"] = [a for a in e["area"] if a != "MOSSDEEP_CITY_SPACE_CENTER_2F"]
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(off_area))
        self.assertIn("not battled on its area maps", str(cm.exception))
        self.assertEqual(len(campaign_of(scratch_skeleton(lambda es: None))), len(OBJS["campaign.json"]["entries"]))


class GabbyTests(unittest.TestCase):
    """F3: every trainer a map object's script battles is on that map, whichever file holds the battle line."""
    WANT = {1: {"MAP_ROUTE111"}, 2: {"MAP_ROUTE118"}, 3: {"MAP_ROUTE120"}, 4: {"MAP_ROUTE111"}, 5: {"MAP_ROUTE118"},
            6: {"MAP_ROUTE111", "MAP_ROUTE118", "MAP_ROUTE120"}}

    def test_gabby_and_ty_are_on_their_maps(self):
        """CONTROL (on be63abd1 all six were on no map): data/scripts/gabby_and_ty.inc's battles, joined to the
        Route 111/118/120 objects that name them."""
        on = {}
        for m in OBJS["maps.json"]["maps"]:
            for t in m["trainers"]:
                for tid in t["trainers"]:
                    if tid.startswith("TRAINER_GABBY_AND_TY_"):
                        self.assertEqual(t["source"], "object")
                        on.setdefault(int(tid[-1]), set()).add(m["id"])
        self.assertEqual(on, self.WANT)

    def test_verifier_counts_each_map_battle(self):
        """FAULT: one trainer removed from the objects of its map is reported on that map and in the totals; a
        battle of a map's own file carried by a neighbouring floor is reported when that floor drops it."""
        def change(data):
            for t in map_rec(data, "MAP_ROUTE118")["trainers"]:
                if "TRAINER_GABBY_AND_TY_2" in t["trainers"]:
                    t["trainers"].remove("TRAINER_GABBY_AND_TY_2")
            b1f = map_rec(data, "MAP_LAVARIDGE_TOWN_GYM_B1F")
            self.dropped = b1f["trainers"][0]["trainers"].pop(0)
        lines = verify_lines(change)
        assert_reported(self, lines, [
            ("MISMATCH map MAP_ROUTE118", "not on this map: ['TRAINER_GABBY_AND_TY_2']"),
            ("MISMATCH totals map battles", "'TRAINER_GABBY_AND_TY_2'"),
            ("MISMATCH map MAP_LAVARIDGE_TOWN_GYM_1F", "on none of its maps: ['%s']" % self.dropped),
        ])

    def test_coord_event_battles_are_checked(self):
        """FAULT: a coord event's battle (Petalburg Woods' grunt) dropped from maps.json is reported."""
        def change(data):
            ce = next(t for t in map_rec(data, "MAP_PETALBURG_WOODS")["trainers"] if t["source"] == "coord_event")
            ce["trainers"] = []
        assert_reported(self, verify_lines(change), [("MISMATCH map MAP_PETALBURG_WOODS", "trainer coord_event")])


class FieldFaultTests(unittest.TestCase):
    """The verify's per-field mutants: each check of the verifier has a FAULT that only it reports."""

    def test_each_field_check_fires(self):
        def change(data):
            trainer(data, "TRAINER_RICK")["flag"] += 1
            trainer(data, "TRAINER_ROXANNE_2")["rematch_of"] = "TRAINER_NONE"
            trainer(data, "TRAINER_TIANA")["party_shape"] = "ItemCustomMoves"
            obj = next(t for t in map_rec(data, "MAP_ROUTE104")["trainers"] if t["source"] == "object")
            obj["sight"] += 1
            map_rec(data, "MAP_ROUTE103")["map_type"] = "MAP_TYPE_UNDERWATER"
            boss(data, "TRAINER_BRAWLY_1")["role"] = "rival"
            boss(data, "TRAINER_ROXANNE_1")["rematches"].pop()
            entry(data, "ch18_tate_and_liza")["needs"]["double_battle"] = False
            boss(data, "TRAINER_WATTSON_1")["party"][0]["types"] = ["FIRE"]
            entry(data, "ch2_oldale")["order"] = 99
            b = boss(data, "TRAINER_FLANNERY_1")
            b["double"] = not b["double"]
        assert_reported(self, verify_lines(change), [
            ("MISMATCH trainer TRAINER_RICK", "flag "),
            ("MISMATCH trainer TRAINER_ROXANNE_2", "rematch_of 'TRAINER_NONE'"),
            ("MISMATCH trainer TRAINER_TIANA", "party_shape 'ItemCustomMoves'"),
            ("MISMATCH map MAP_ROUTE104", "type/sight differ"),
            ("MISMATCH map MAP_ROUTE103", "map_type 'MAP_TYPE_UNDERWATER'"),
            ("MISMATCH boss TRAINER_BRAWLY_1", "role 'rival'"),
            ("MISMATCH boss TRAINER_ROXANNE_1", "rematches differ"),
            ("MISMATCH campaign ch18_tate_and_liza", "double_battle/party_min False/2"),
            ("MISMATCH boss TRAINER_WATTSON_1", "slot 1"),
            ("MISMATCH campaign ch2_oldale", "order 99 at position 11"),
            ("MISMATCH boss TRAINER_FLANNERY_1", "double differs"),
        ])


class ExtractorGuardFaultTests(unittest.TestCase):
    """The verify's extractor mutants: each guard refuses a broken decomp file read through an overlay."""

    def _refused(self, rel, old, new, needle):
        text = raw_text(rel)
        self.assertEqual(text.count(old), 1, old)
        with self.assertRaises(ew.Refused) as cm:
            ew.build_trainers(OverlayDecomp(ROOT, {rel: text.replace(old, new, 1)}))
        self.assertIn(needle, str(cm.exception))

    def test_guards_refuse(self):
        tp = raw_text("src/data/trainer_parties.h")
        start = tp.index("sParty_Sawyer1[] = {")
        body_end = tp.index("\n};", start)
        self._refused("src/data/trainer_parties.h", tp[start:body_end + 3], "sParty_Sawyer1[] = {\n};",
                      "has no members")                                                     # an empty party array
        self._refused("include/constants/opponents.h", "#define TRAINER_SAWYER_1 ",
                      "#define TRAINER_PHANTOM_ZZ          999\n#define TRAINER_SAWYER_1 ",
                      "no trainers.h block")                                                # an id with no block
        member = tp[start:body_end].split(".lvl", 1)
        self._refused("src/data/trainer_parties.h", tp[start:body_end],
                      member[0] + ".heldItem = ITEM_NONE,\n    .lvl" + member[1],
                      "does not have its shape's fields")                                   # a member of the wrong shape
        self._refused("include/constants/flags.h", "#define TRAINER_FLAGS_START ",
                      "#define TRAINER_FLAGS_START_RENAMED ", "TRAINER_FLAGS_START")        # the flag base is gone
        ew.build_trainers(OverlayDecomp(ROOT, {}))                                          # CONTROL

    def test_w4b_no_giver_and_plural_iv(self):
        entries = OBJS["campaign.json"]["entries"]
        award = {b["fight"]: b["badge"]["id"] for b in OBJS["bosses.json"]["bosses"] if "badge" in b}
        award.pop("ROXANNE")
        with self.assertRaises(ew.Refused) as cm:
            ew.check_badge_order(entries, award)
        self.assertIn("BADGE01, which no entry's boss awards", str(cm.exception))
        for key in ("ivs", "IVs", "iv", "aiFlags", "AI_flags"):
            self.assertEqual(len(ew.withheld_keys({"party": [{key: 1}]})), 1, key)
            self.assertEqual(len(vw.withheld_hits_in({"party": [{key: 1}]})), 1, key)


class PinTests(unittest.TestCase):
    """The pin is compared, not only looked up: a clone at ANOTHER commit is refused by both programs."""

    def test_another_commit_is_refused(self):
        pin = Path(ew.PIN_FILE).read_text(encoding="utf-8").strip()
        other = ("0" if pin[0] != "0" else "1") + pin[1:]
        with tempfile.TemporaryDirectory() as tmp:
            fake_clone(tmp, pin)  # CONTROL: the same folder at the pinned commit is accepted
            self.assertEqual(ew.resolve_decomp(tmp), tmp)
            self.assertEqual(vw.pinned_root(tmp), tmp)
            fake_clone(tmp, other)
            with self.assertRaises(ew.Refused) as cm:
                ew.resolve_decomp(tmp)
            self.assertIn(other, str(cm.exception))
            with self.assertRaises(vw.Refused):
                vw.pinned_root(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(vw.main(["--decomp", tmp]), 2)


def recall(maps, trainers):
    """(missing, extras): every milestones.json trainer whose id, flag or levels differ in trainers.json, or that is not
    PLACED (an object or a coord event) on a map of its chapter; extras = placed trainers of those maps not in the table."""
    by_sym = {t["symbol"]: t for t in trainers}
    gendered = MILESTONES["gendered_maps"]
    chapter_maps = {}
    for m in MILESTONES["milestones"]:
        for name in m["maps"]:
            names = list(gendered[name[1:-1]].values()) if name.startswith("<") else [name]
            chapter_maps.setdefault(m["chapter"], set()).update("MAP_" + n for n in names)
    placed = {}
    for mp in maps:
        for t in mp["trainers"]:
            if t["source"] in ("object", "coord_event"):
                for tid in t["trainers"]:
                    placed.setdefault(tid, set()).add(mp["id"])
    missing, extras = [], []
    for ch, names in CHAPTER_OF.items():
        for name in names:
            want = MILESTONES["trainers"][name]
            t = by_sym.get("TRAINER_" + name)
            if t is None or (t["id"], t["flag"], [p["level"] for p in t["party"]]) != (want["id"], want["flag"],
                                                                                    want["levels"]):
                missing.append((name, "id/flag/levels"))
            elif not placed.get("TRAINER_" + name, set()) & chapter_maps[ch]:
                missing.append((name, "not placed on a chapter %d map" % ch))
        on = {tid for tid, ms in placed.items() if ms & chapter_maps[ch]}
        extras += sorted(tid for tid in on if tid[len("TRAINER_"):] not in MILESTONES["trainers"])
    return missing, extras


class W3RecallTests(unittest.TestCase):
    def test_mapping_covers_the_table(self):
        self.assertEqual(sorted(n for v in CHAPTER_OF.values() for n in v), sorted(MILESTONES["trainers"]))

    def test_recall_is_complete(self):
        missing, extras = recall(OBJS["maps.json"]["maps"], OBJS["trainers.json"]["trainers"])
        self.assertEqual(missing, [])
        print("\n  W3 extras on the chapter 1-5 and 7 maps (listed for adjudication, not hidden): %s" % extras)

    def test_fault_deleted_object_lowers_recall(self):
        rel = "data/maps/Route102/map.json"
        j = json.loads(raw_text(rel))
        j["object_events"] = [o for o in j["object_events"] if o["script"] != "Route102_EventScript_Calvin"]
        maps = ew.build_maps(OverlayDecomp(ROOT, {rel: json.dumps(j, indent=2)}))
        missing, _ = recall(maps, OBJS["trainers.json"]["trainers"])
        self.assertEqual(missing, [("CALVIN_1", "not placed on a chapter 2 map")])


def flag_names(obj):
    out = set()
    if isinstance(obj, dict):
        for v in obj.values():
            out |= flag_names(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= flag_names(v)
    elif isinstance(obj, str) and (obj.startswith("FLAG_") or obj.startswith("VAR_")):
        out.add(obj)
    return out


def phantom(names):
    """The names not in the tables audit_flag_names.py reads (no FLAG_/VAR_ prefix in the tables)."""
    flags = {ln.split()[1] for ln in FLAG_TABLE.read_text().splitlines() if len(ln.split()) >= 2}
    evars = {ln.split()[1] for ln in VAR_TABLE.read_text().splitlines() if len(ln.split()) >= 2}
    return sorted(n for n in names if (n[5:] not in flags if n.startswith("FLAG_") else n[4:] not in evars))


class W4ConsistencyTests(unittest.TestCase):
    def test_ids_and_areas(self):
        entries = OBJS["campaign.json"]["entries"]
        # (2026-11-01) the milestones' count is READ, not written: chapter 5 moved it from 20 to 28 and chapter 6 will again
        self.assertEqual([e["id"] for e in entries[:len(MILESTONES["milestones"])]],
                         [m["id"] for m in MILESTONES["milestones"]])
        ids = {m["id"] for m in OBJS["maps.json"]["maps"]}
        self.assertEqual([n for e in entries for n in e["area"] if "MAP_" + n not in ids], [])

    def test_every_flag_is_real(self):
        names = set()
        for name in ew.OUTPUTS:
            names |= flag_names(OBJS[name])
        self.assertGreater(len(names), 250)
        self.assertEqual(phantom(names), [])
        self.assertEqual(phantom(names | {"FLAG_HIDDEN_ITEM_ROUTE_999_PHANTOM"}), ["FLAG_HIDDEN_ITEM_ROUTE_999_PHANTOM"])

    def test_renamed_area_map_exits_non_zero_naming_it(self):
        # (2026-11-01) picked by id, not by position: es[40] named the entry that was 41st before chapter 5 moved the order
        sk = scratch_skeleton(lambda es: next(e for e in es if e["id"] == "ch13_route118")["area"].__setitem__(1, "ROUTE118X"))
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(sk)
        self.assertIn("ROUTE118X", str(cm.exception))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "skeleton.json"
            p.write_text(json.dumps(sk), encoding="utf-8")
            r = subprocess.run([sys.executable, str(HERE / "extract_world.py"), "--skeleton", str(p), "--out",
                                str(Path(tmp) / "out")], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("ROUTE118X", r.stdout)
            self.assertFalse((Path(tmp) / "out").exists())

    def test_milestone_ids_guard(self):
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: es[3].__setitem__("id", "ch1_clock_renamed")))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: es.__setitem__(slice(0, 2), [es[1], es[0]])))

    def test_chapter_5_ids_are_guarded_too(self):
        """(2026-11-01) FAULT: a chapter-5 skeleton id renamed, two chapter-5 entries swapped, and a chapter-5 entry dropped
        are each REFUSED naming the milestone; CONTROL: the real skeleton (28 milestones, 8 of them chapter 5) is accepted."""
        ch5 = [m["id"] for m in MILESTONES["milestones"] if m["chapter"] == 5]
        self.assertEqual(len(ch5), 8)
        campaign_of(scratch_skeleton(lambda es: None))  # CONTROL: unchanged -> no raise
        def index(es, mid):
            return next(i for i, e in enumerate(es) if e["id"] == mid)

        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(lambda es: es[index(es, "ch5_pokenav_tutorial")].__setitem__("id", "ch5_pokenav")))
        self.assertIn("ch5_pokenav_tutorial", str(cm.exception))

        def swap(es):
            i, j = index(es, "ch5_rival_meet"), index(es, "ch5_rival_battle")
            es[i], es[j] = es[j], es[i]
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(swap))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: es.pop(index(es, "ch5_goods_employee"))))

    def test_chapter_6_and_7_ids_are_guarded_too(self):
        """(2026-11-05) FAULT: a chapter-6 and a chapter-7 skeleton id renamed, two chapter-7 entries swapped, and a chapter-6
        entry dropped are each REFUSED naming the milestone; CONTROL: the real skeleton (36 milestones, 3 of chapter 6 and 5 of
        chapter 7) is accepted. The skeleton's old ids (ch6_sail_dewford, ch7_granite_cave) are refused too: a stale skeleton."""
        ids = {c: [m["id"] for m in MILESTONES["milestones"] if m["chapter"] == c] for c in (6, 7)}
        self.assertEqual((len(ids[6]), len(ids[7])), (3, 5))
        campaign_of(scratch_skeleton(lambda es: None))  # CONTROL: unchanged -> no raise

        def index(es, mid):
            return next(i for i, e in enumerate(es) if e["id"] == mid)

        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(lambda es: es[index(es, "ch6_dewford")].__setitem__("id", "ch6_sail_dewford")))
        self.assertIn("ch6_dewford", str(cm.exception))
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(lambda es: es[index(es, "ch7_steven")].__setitem__("id", "ch7_granite_cave")))
        self.assertIn("ch7_steven", str(cm.exception))

        def swap(es):
            i, j = index(es, "ch7_steven"), index(es, "ch7_brawly")
            es[i], es[j] = es[j], es[i]
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(swap))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: es.pop(index(es, "ch6_old_rod"))))


class W4bOrderTests(unittest.TestCase):
    def test_real_order_passes(self):
        entries = OBJS["campaign.json"]["entries"]
        need = sum(len(e["needs"]["badges"]) for e in entries)
        self.assertGreater(need, 10)
        award = {b["fight"]: b["badge"]["id"] for b in OBJS["bosses.json"]["bosses"] if "badge" in b}
        ew.check_badge_order(entries, award)  # CONTROL: no raise

    def test_swapped_gyms_fail_naming_both(self):
        def swap(es):
            i = next(k for k, e in enumerate(es) if e["id"] == "ch11_flannery")
            j = next(k for k, e in enumerate(es) if e["id"] == "ch12_norman")
            es[i], es[j] = es[j], es[i]
        with self.assertRaises(ew.Refused) as cm:
            campaign_of(scratch_skeleton(swap))
        self.assertIn("ch12_norman", str(cm.exception))
        self.assertIn("ch11_flannery", str(cm.exception))


class W5ShapeTests(unittest.TestCase):
    def test_all_four_shapes(self):
        arrays, raw_count = ew.parse_party_arrays(D)
        self.assertEqual(raw_count, 854)
        self.assertEqual(len(arrays), raw_count)
        self.assertEqual(RAW["n_arrays"], raw_count)
        shapes = [t["party_shape"] for t in OBJS["trainers.json"]["trainers"]]
        self.assertEqual({s: shapes.count(s) for s in ew.PARTY_SHAPES},
                         {"NoItemDefaultMoves": 672, "NoItemCustomMoves": 87, "ItemDefaultMoves": 31, "ItemCustomMoves": 64})
        empty = [t["symbol"] for t in OBJS["trainers.json"]["trainers"] if not t["party"]]
        self.assertEqual(empty, ["TRAINER_NONE"])
        self.assertEqual(len({t.get("party_ref") for t in OBJS["trainers.json"]["trainers"] if t["party"]}), raw_count)

    def test_dropping_any_shape_fails_the_count(self):
        for shape in ew.PARTY_SHAPES:
            fewer = {k: v for k, v in ew.PARTY_SHAPES.items() if k != shape}
            arrays, raw_count = ew.parse_party_arrays(D, shapes=fewer)
            self.assertLess(len(arrays), raw_count, shape)
            with self.assertRaises(ew.Refused):
                ew.check_party_count(arrays, raw_count)

    def test_build_refuses_an_unknown_shape(self):
        """The build runs the count guard: an extra array of a shape the parser does not know (referenced by no
        trainer, so only the COUNT can see it) is refused."""
        rel = "src/data/trainer_parties.h"
        extra = raw_text(rel) + ("\nstatic const struct TrainerMonNoItemSomeNewShape sParty_Extra[] = {\n    {\n    .iv = 0,"
                                 "\n    .lvl = 5,\n    .species = SPECIES_ZIGZAGOON,\n    }\n};\n")
        with self.assertRaises(ew.Refused) as cm:
            ew.build_trainers(OverlayDecomp(ROOT, {rel: extra}))
        self.assertIn("parsed 854 party arrays, trainer_parties.h declares 855", str(cm.exception))

    def test_another_empty_party_is_refused(self):
        rel = "src/data/trainers.h"
        t = raw_text(rel)
        arrays, _ = ew.parse_party_arrays(D)
        ids = ew.trainer_ids(D)

        def parties(text):
            ew.check_parties(ew.parse_trainer_blocks(OverlayDecomp(ROOT, {rel: text})), arrays, ids)

        empty = t.replace(".party = NO_ITEM_DEFAULT_MOVES(sParty_Sawyer1),",
                          ".partySize = 0,\n        .party = {.NoItemDefaultMoves = NULL},", 1)
        self.assertNotEqual(empty, t)
        with self.assertRaises(ew.Refused) as cm:
            parties(empty)
        self.assertIn("SAWYER", str(cm.exception))
        with self.assertRaises(ew.Refused):  # a macro of the wrong shape
            parties(t.replace("NO_ITEM_DEFAULT_MOVES(sParty_Sawyer1)", "ITEM_DEFAULT_MOVES(sParty_Sawyer1)", 1))
        with self.assertRaises(ew.Refused):  # an array that does not exist
            parties(t.replace("NO_ITEM_DEFAULT_MOVES(sParty_Sawyer1)", "NO_ITEM_DEFAULT_MOVES(sParty_Nobody1)", 1))
        parties(t)  # CONTROL: the real file, TRAINER_NONE exempt by name
        with self.assertRaises(ew.Refused) as cm:  # and the build itself runs the guard
            ew.build_trainers(OverlayDecomp(ROOT, {rel: empty}))
        self.assertIn("SAWYER", str(cm.exception))


class W6RouteTests(unittest.TestCase):
    def test_route_keys(self):
        self.assertEqual(ew.route_keys(OBJS["campaign.json"]), [])
        self.assertEqual(vw.route_keys(OBJS["campaign.json"]), [])
        for key in ew.ROUTE_KEYS:
            camp = copy.deepcopy(OBJS["campaign.json"])
            camp["entries"][10]["needs"][key] = 1
            self.assertEqual(len(vw.route_keys(camp)), 1, key)
            objs = dict(OBJS, **{"campaign.json": camp})
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ew.Refused):
                    ew.write_outputs(tmp, objs)


def missing_field_move_learners(entry, party, learnsets):
    """W8's pure consumer: for each field move the entry needs, say when no party species can learn it (TM/HM list)."""
    can = {s["symbol"]: {m["move"] for m in s.get("tm_hm", [])} for s in learnsets["species"]}
    out = []
    for fm in entry["needs"]["field_moves"]:
        if not any("MOVE_" + fm["move"] in can.get(sp, set()) for sp in party):
            out.append("no %s learner" % fm["move"].replace("_", " ").title())
    return out


class W8ConsumerTests(unittest.TestCase):
    def test_no_surf_learner(self):
        learn = json.loads((KNOWLEDGE / "seasoned" / "learnsets.json").read_text(encoding="utf-8"))
        entry = next(e for e in OBJS["campaign.json"]["entries"] if any(f["move"] == "SURF" for f in e["needs"]["field_moves"]))
        party = ["SPECIES_TORCHIC", "SPECIES_TAILLOW", "SPECIES_GEODUDE"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            for line in missing_field_move_learners(entry, party, learn):
                print(line)
        self.assertEqual(buf.getvalue().strip(), "no Surf learner")
        self.assertEqual(entry["id"], "ch13_route118")
        self.assertEqual(missing_field_move_learners(entry, party + ["SPECIES_MARSHTOMP"], learn), [])  # CONTROL
        bare = copy.deepcopy(entry)
        bare["needs"]["field_moves"] = []
        self.assertEqual(missing_field_move_learners(bare, party, learn), [])  # the message comes from the DATA


class GuardTests(unittest.TestCase):
    def test_field_move_cross_check(self):
        rel = "src/field_control_avatar.c"
        t = raw_text(rel)
        bad = t.replace("FlagGet(FLAG_BADGE05_GET) == TRUE && PartyHasMonWithSurf", "FlagGet(FLAG_BADGE04_GET) == TRUE && "
                                                                                    "PartyHasMonWithSurf", 1)
        self.assertNotEqual(bad, t)
        with self.assertRaises(ew.Refused) as cm:
            ew.field_move_table(OverlayDecomp(ROOT, {rel: bad}))
        self.assertIn("SURF", str(cm.exception))
        self.assertEqual(len(ew.field_move_table(OverlayDecomp(ROOT, {}))), 8)

    def test_leader_badge_exactly_one(self):
        rel = "data/maps/RustboroCity_Gym/scripts.inc"
        t = raw_text(rel)
        two = t.replace("\tsetflag FLAG_BADGE01_GET\n", "\tsetflag FLAG_BADGE01_GET\n\tsetflag FLAG_BADGE02_GET\n", 1)
        self.assertNotEqual(two, t)
        with self.assertRaises(ew.Refused):
            ew.leader_badge(D, {rel: two}, "TRAINER_ROXANNE_1")
        none = t.replace("\tsetflag FLAG_BADGE01_GET\n", "", 1)
        with self.assertRaises(ew.Refused):
            ew.leader_badge(D, {rel: none}, "TRAINER_ROXANNE_1")
        self.assertEqual(ew.leader_badge(D, {rel: t}, "TRAINER_ROXANNE_1")["id"], "BADGE01")

    def test_unknown_boss_item_and_citation(self):
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: es[25].__setitem__("boss", "NOBODY")))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: next(e for e in es if e["id"] == "ch13_winona")["needs"]
                                         ["key_items"][0].__setitem__("item", "ITEM_NOT_A_THING")))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: next(e for e in es if e["id"] == "ch13_winona")["needs"]
                                         ["key_items"][0].__setitem__("needle", "checkitem ITEM_NOT_IN_THIS_FILE")))
        with self.assertRaises(ew.Refused):
            campaign_of(scratch_skeleton(lambda es: next(e for e in es if e["id"] == "ch13_route118")["needs"]
                                         ["field_moves"][0].__setitem__("move", "TELEPORT")))
        self.assertEqual(len(campaign_of(scratch_skeleton(lambda es: None))), len(OBJS["campaign.json"]["entries"]))

    def test_closure_is_bounded(self):
        labels = {"L%d" % i: {"line": i, "body": [(i, "\tgoto L%d" % (i + 1))]} for i in range(ew.MAX_LABELS + 5)}
        with self.assertRaises(ew.Refused):
            ew.reach(labels, "L0")
        self.assertEqual(len(ew.reach(labels, "L%d" % (ew.MAX_LABELS - 5))), 10)

    def test_unpinned_decomp_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ew.Refused):
                ew.resolve_decomp(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = ew.main(["--decomp", tmp, "--out", os.path.join(tmp, "out")])
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(os.path.join(tmp, "out")))
            with self.assertRaises(vw.Refused):
                vw.pinned_root(tmp)
        self.assertEqual(os.path.normcase(ew.resolve_decomp(ROOT)), os.path.normcase(ROOT))  # CONTROL


def loader_allowed_names():
    """(KI-128, 2026-10-31) {play file: the world names it may name}: a declared LOADER (`check_fairness.LOADERS`) of a
    world file may name `knowledge/world` and that file, nothing else of the world folder."""
    from ai_player.gates.check_fairness import LOADERS
    out = {}
    for loader, files in LOADERS.items():
        world = [Path(f).name for f in files if f.startswith("world/")]
        if world:
            out[loader] = {"knowledge/world", *world}
    return out


def names_in_play_code(package, allowed=None):
    """(files scanned, [(file, name)]) of every .py of the AI package, the test side `gates/` excepted, that names a
    world file or folder; a name `allowed` for that file (its declared loader's own file, `loader_allowed_names`) is no
    hit."""
    allowed = loader_allowed_names() if allowed is None else allowed
    hits, n = [], 0
    for p in sorted(Path(package).rglob("*.py")):
        rel = p.relative_to(package).as_posix()
        if rel.startswith("gates/") or "__pycache__" in rel:
            continue
        n += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        hits += [(rel, name) for name in PLAY_NAMES if name in text and name not in allowed.get(rel, ())]
    return n, hits


class NotReadTests(unittest.TestCase):
    def test_no_play_code_names_a_world_file(self):
        """No play code names a world file, but (KI-128) the declared loader `knowledge/atlas.py` its own ones ((chapter 7
        NS4, 2026-11-06) maps.json and, since its second slice, bosses.json: which leader holds which gym) and (P11-1,
        2026-11-11) the declared loader `knowledge/ways.py` its ways.json (the way through each dark cave)."""
        self.assertEqual(loader_allowed_names(), {"knowledge/atlas.py": {"knowledge/world", "maps.json", "bosses.json"},
                                                  "knowledge/ways.py": {"knowledge/world", "ways.json"}})
        n, hits = names_in_play_code(REPO / "ai_player")
        self.assertGreater(n, 20)
        self.assertEqual(hits, [])
        self.assertIn("maps.json", (KNOWLEDGE / "atlas.py").read_text(encoding="utf-8"))  # the allowance is used
        self.assertIn("bosses.json", (KNOWLEDGE / "atlas.py").read_text(encoding="utf-8"))  # and the second one
        self.assertIn("ways.json", (KNOWLEDGE / "ways.py").read_text(encoding="utf-8"))  # (P11-1) and ways.py's own
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "brain").mkdir()
            (Path(tmp) / "brain" / "goals.py").write_text('BOOK = "knowledge/world/bosses.json"\nATLAS = "maps.json"\n',
                                                          encoding="utf-8")
            (Path(tmp) / "gates").mkdir()
            (Path(tmp) / "gates" / "ok.py").write_text('X = "maps.json"\n', encoding="utf-8")
            (Path(tmp) / "knowledge").mkdir()
            (Path(tmp) / "knowledge" / "atlas.py").write_text('F = "knowledge/world/maps.json"\nB = "trainers.json"\n',
                                                              encoding="utf-8")
            _, hits = names_in_play_code(tmp)
            self.assertEqual(hits, [("brain/goals.py", "knowledge/world"), ("brain/goals.py", "bosses.json"),
                                    ("brain/goals.py", "maps.json"), ("knowledge/atlas.py", "trainers.json")])

    def test_check_fairness_does_not_glob_world(self):
        """RULE B walks ONLY the world files a LOADER names (KI-128: maps.json, and (chapter 7 NS4, 2026-11-06)
        bosses.json, both for `knowledge/atlas.py`; (P11-1, 2026-11-11) ways.json for `knowledge/ways.py`); the others
        stay unread and unchecked. (BP-1, 2026-11-09) And the three `seasoned/` files `knowledge/seasoned.py` names
        (seasoned/moves.json, named by no loader, stays unwalked)."""
        from ai_player.gates.check_fairness import knowledge_files, schema_problems, world_files
        self.assertEqual(world_files(), ["seasoned/encounters.json", "seasoned/learnsets.json", "seasoned/species.json",
                                         "world/bosses.json", "world/maps.json", "world/ways.json"])
        walked = [name for name, _ in knowledge_files(KNOWLEDGE)]
        self.assertEqual([n for n in walked if n.startswith("world/")],
                         ["world/bosses.json", "world/maps.json", "world/ways.json"])
        problems, counts = schema_problems(KNOWLEDGE)
        self.assertEqual([p for p in problems if "world" in p or "campaign" in p or "trainers" in p], [])
        self.assertEqual(problems, [])
        with tempfile.TemporaryDirectory() as tmp:
            k = Path(tmp) / "knowledge"
            shutil.copytree(KNOWLEDGE, k, ignore=shutil.ignore_patterns("*.py", "__pycache__"))
            self.assertEqual(schema_problems(k)[0], [])  # CONTROL: the copy with world/ inside is still clean
            shutil.copy(WORLD / "campaign.json", k / "campaign.json")
            problems, _ = schema_problems(k)
            self.assertEqual(len(problems), 1)
            self.assertIn("campaign.json", problems[0])
            # an unclassified key in a world file NO loader names is not walked (trainers.json); in a loaded one
            # (bosses.json, since its loader slice) it FAILS
            trainers = json.loads((k / "world" / "trainers.json").read_text(encoding="utf-8"))
            trainers["planted_secret"] = 1
            (k / "world" / "trainers.json").write_text(json.dumps(trainers), encoding="utf-8")
            self.assertEqual(len(schema_problems(k)[0]), 1)  # still only campaign.json's
            boss = json.loads((k / "world" / "bosses.json").read_text(encoding="utf-8"))
            boss["bosses"][0]["planted_secret"] = 1
            (k / "world" / "bosses.json").write_text(json.dumps(boss), encoding="utf-8")
            problems, _ = schema_problems(k)
            self.assertEqual(len(problems), 2)
            self.assertTrue(any("bosses.json" in p and "planted_secret" in p for p in problems), problems)

    def test_k_f3_the_atlas_loader_gate(self):
        """(KI-128, K-F3) The world loader is gated like every loader: a developer key read in `knowledge/atlas.py` FAILS
        (B2), maps.json named in deciding code FAILS (B1), an unclassified key planted in maps.json FAILS (B); a
        docstring MENTION of maps.json or of a flag key does not fire. And x and y stay developer-only keys (the
        milestones' MEASURED coordinates) although maps.json's AI paths use those names."""
        from ai_player.gates import check_fairness as cf_
        ok, problems, summary = cf_.check(REPO / "ai_player")
        self.assertTrue(ok, problems)
        self.assertIn("'x', 'y'", summary)  # CONTROL: developer-only keys keep x and y
        for key in ("flag", "script", "label", "object", "ref"):
            self.assertIn(f"'{key}'", summary.split("developer-only keys")[1].split("hidden keys")[0], key)

        def plant(edit) -> list[str]:
            with tempfile.TemporaryDirectory() as tmp:
                pkg = Path(tmp) / "ai_player"
                shutil.copytree(REPO / "ai_player", pkg, ignore=shutil.ignore_patterns(
                    "__pycache__", "evidence", "gates", "*.ss1", "eyes", "host"))
                edit(pkg)
                ok_, problems_, _ = cf_.check(pkg)
                return problems_

        def add(rel: str, text: str):
            def do(pkg):
                path = pkg / rel
                path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
            return do

        self.assertEqual(plant(lambda pkg: None), [])  # CONTROL: the copy is clean
        found = plant(add("knowledge/atlas.py", '\n\ndef leak(entry):\n    return entry["flag"], entry.get("script")\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")),
                         ["'flag'", "'script'"])
        found = plant(add("brain/goals.py", '\n\nATLAS = "knowledge/world/maps.json"\n'))
        self.assertTrue(any(f.startswith("B1") and "maps.json" in f for f in found), found)
        mention = ('\n\ndef told():\n    """It never reads maps.json\'s x["flag"] or entry.get("script")."""\n'
                   '    # entry["flag"], "maps.json"\n    return f"maps.json {1}"\n')
        self.assertEqual(plant(add("knowledge/atlas.py", mention)), [])  # mentions never fire: in the loader,
        self.assertEqual(plant(add("brain/goals.py", mention)), [])  # nor in deciding code (B1 judges values only)

        def unclassified(pkg):
            path = pkg / "knowledge" / "world" / "maps.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["maps"][0]["secret_route"] = "x"
            path.write_text(json.dumps(data), encoding="utf-8")
        found = plant(unclassified)
        self.assertTrue(any("world/maps.json" in f and "UNCLASSIFIED" in f and "secret_route" in f for f in found), found)

    def test_k_f3b_the_bosses_slice_is_gated_and_weakens_nothing(self):
        """(chapter 7 NS4 round 3, the second builder, 2026-11-06) The fairness gate's CHANGE: `knowledge/atlas.py` may now
        name a SECOND world file, `world/bosses.json` (`gym_leaders`: which leader holds which gym), and every key path of
        it is classified. What that must NOT do, and does not: remove a key from the developer-only set (a world file's
        AI names never excuse a name elsewhere, `developer_keys`) or touch the hidden keys; measured here with LOADERS put
        back to the base's (atlas: maps.json only). What it ADDS: the bosses' own developer keys are refused now
        (`rematches`, `order`, `entry`, `notes`), and deciding code that names `bosses.json` breaks B1 (before, a world file
        no loader named was not one of B1's names). THE NEW BREACHES of the kind the change is about FAIL: the loader
        reading a boss's badge FLAG or its rematch constants (B2), deciding code naming the file (B1), a key planted
        under a boss (RULE B); a docstring mention of them does not fire."""
        from unittest import mock

        from ai_player.gates import check_fairness as cf_
        loaders = dict(cf_.LOADERS)
        loaders["knowledge/atlas.py"] = ("world/maps.json",)
        with_slice = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        with mock.patch.object(cf_, "LOADERS", loaders):
            without = cf_.developer_keys(knowledge=KNOWLEDGE), cf_.hidden_keys(knowledge=KNOWLEDGE)
        self.assertEqual(without[0] - with_slice[0], set())  # no developer-only key is lost
        self.assertEqual(with_slice[0] - without[0], {"entry", "notes", "order", "rematches"})
        self.assertEqual(with_slice[1], without[1])

        def plant(edit) -> list[str]:
            with tempfile.TemporaryDirectory() as tmp:
                pkg = Path(tmp) / "ai_player"
                shutil.copytree(REPO / "ai_player", pkg, ignore=shutil.ignore_patterns(
                    "__pycache__", "evidence", "gates", "*.ss1", "eyes", "host"))
                edit(pkg)
                return cf_.check(pkg)[1]

        def add(rel: str, text: str):
            def do(pkg):
                path = pkg / rel
                path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")
            return do

        self.assertEqual(plant(lambda pkg: None), [])  # CONTROL: the copy is clean
        found = plant(add("knowledge/atlas.py", '\n\ndef leak(boss):\n    return boss["badge"]["flag"], '
                                                'boss.get("rematches")\n'))
        self.assertEqual(sorted(f.split("key ")[1].split(" ")[0] for f in found if f.startswith("B2")),
                         ["'flag'", "'rematches'"])
        found = plant(add("brain/goals.py", '\n\nBOOK = "knowledge/world/bosses.json"\n'))
        self.assertTrue(any(f.startswith("B1") and "bosses.json" in f for f in found), found)
        with mock.patch.object(cf_, "LOADERS", loaders):  # FAULT half: without the slice B1 did not know the name
            found = plant(add("brain/goals.py", '\n\nBOOK = "knowledge/world/bosses.json"\n'))
        self.assertFalse(any(f.startswith("B1") and "bosses.json" in f for f in found), found)
        mention = '\n\ndef told():\n    """Never boss["badge"]["flag"] nor bosses.json."""\n    return "x"\n'
        self.assertEqual(plant(add("knowledge/atlas.py", mention)), [])

        def unclassified(pkg):
            path = pkg / "knowledge" / "world" / "bosses.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            next(boss for boss in data["bosses"] if isinstance(boss.get("badge"), dict))["badge"]["secret_flag"] = "FLAG_X"
            path.write_text(json.dumps(data), encoding="utf-8")
        found = plant(unclassified)
        self.assertTrue(any("world/bosses.json" in f and "UNCLASSIFIED" in f and "secret_flag" in f for f in found), found)

    def test_k_f3c_the_atlas_reads_only_role_name_and_battled_on_of_bosses_json(self):
        """(chapter 7 stops round 4, the round-3 verifier's V3-6, 2026-11-06) `bosses[].fight` is DEVELOPER in bosses.json
        but AI in milestones.json (`milestones[].fight`), so the gate's by-name rule cannot refuse it (its documented
        limit). The atlas's reads of the file are pinned by NAME instead: every key `gym_leaders` subscripts or `.get`s on
        the file's data or a boss is one of `bosses`, `role`, `name`, `battled_on`. FAULT half: a planted
        `boss["fight"]` (or `boss.get("badge")`) is seen by the same reading."""
        import ast as ast_

        def keys_read(source: str) -> set[str]:
            tree = ast_.parse(source)
            func = next(node for node in ast_.walk(tree) if isinstance(node, ast_.FunctionDef) and node.name == "gym_leaders")
            found = set()
            for node in ast_.walk(func):
                if isinstance(node, ast_.Subscript) and isinstance(node.value, ast_.Name) and node.value.id in ("data", "boss") \
                        and isinstance(node.slice, ast_.Constant) and isinstance(node.slice.value, str):
                    found.add(node.slice.value)
                if isinstance(node, ast_.Call) and isinstance(node.func, ast_.Attribute) and node.func.attr == "get" \
                        and isinstance(node.func.value, ast_.Name) and node.func.value.id in ("data", "boss") and node.args \
                        and isinstance(node.args[0], ast_.Constant):
                    found.add(node.args[0].value)
            return found

        source = (REPO / "ai_player" / "knowledge" / "atlas.py").read_text(encoding="utf-8")
        self.assertEqual(keys_read(source), {"bosses", "role", "name", "battled_on"})
        planted = source.replace('leaders[str(boss["name"])]', 'leaders[str(boss["name"]) + str(boss["fight"])]', 1)
        self.assertNotEqual(planted, source)
        self.assertIn("fight", keys_read(planted))  # FAULT half
        planted = source.replace('boss.get("role")', 'boss.get("badge") and boss.get("role")', 1)
        self.assertIn("badge", keys_read(planted))

    @staticmethod
    def _keys_read(source: str, function: str | None, names: tuple[str, ...] | None = None) -> set[str]:
        """(BP-1) Every constant key a function (None: the whole module) subscripts or `.get`s, on the names given (None:
        on anything but the module's own cache, `_CACHE`)."""
        import ast as ast_

        tree = ast_.parse(source)
        scope = tree if function is None else next(node for node in ast_.walk(tree)
                                                   if isinstance(node, ast_.FunctionDef) and node.name == function)

        def counted(value) -> bool:
            if names is None:
                return not (isinstance(value, ast_.Name) and value.id == "_CACHE")
            return isinstance(value, ast_.Name) and value.id in names

        found = set()
        for node in ast_.walk(scope):
            if isinstance(node, ast_.Subscript) and isinstance(node.slice, ast_.Constant) and isinstance(node.slice.value, str) \
                    and counted(node.value):
                found.add(node.slice.value)
            if isinstance(node, ast_.Call) and isinstance(node.func, ast_.Attribute) and node.func.attr == "get" and node.args \
                    and isinstance(node.args[0], ast_.Constant) and isinstance(node.args[0].value, str) \
                    and counted(node.func.value):
                found.add(node.args[0].value)
        return found

    def test_k_f3d_boss_party_reads_only_its_slice(self):
        """(boss preparation BP-1, 2026-11-09) `knowledge/atlas.py` boss_party reads, of bosses.json, only `bosses`, a
        boss's `name` and `party`, and each Pokemon's `species`, `level`, `moves` and `held_item` (RULING 44: the item is
        known). FAULT half: a planted read of a boss's `id` (TRAINER_BRAWLY_1, a defeated flag's name) is seen."""
        source = (REPO / "ai_player" / "knowledge" / "atlas.py").read_text(encoding="utf-8")
        self.assertEqual(self._keys_read(source, "boss_party", ("data", "boss", "mon")),
                         {"bosses", "name", "party", "species", "level", "moves", "held_item"})
        planted = source.replace('key = str(boss["name"])', 'key = str(boss["name"]) + str(boss["id"])', 1)
        self.assertNotEqual(planted, source)
        self.assertIn("id", self._keys_read(planted, "boss_party", ("data", "boss", "mon")))
        self.assertEqual(self._keys_read(source, "gym_leaders", ("data", "boss")), {"bosses", "role", "name", "battled_on"})

    def test_k_f3e_the_seasoned_loader_reads_only_its_keys(self):
        """(BP-1) `knowledge/seasoned.py` reads, of the three seasoned files, only the keys its docstring names (species:
        `symbol`, `name`, `evolutions[].method / parameter.value / into`; learnsets: `symbol`, `level_up[].level / move`;
        encounters: `map`, `availability`, `methods.land.slots[].min_level / max_level`), never a hidden one (base stats,
        catch rate, experience, growth, wild held items: also refused by check_fairness B2). FAULT half: a planted
        `entry["catch_rate"]` is seen."""
        source = (REPO / "ai_player" / "knowledge" / "seasoned.py").read_text(encoding="utf-8")
        allowed = {"species", "symbol", "name", "evolutions", "method", "parameter", "value", "into", "level_up", "level",
                   "move", "maps", "map", "availability", "methods", "land", "slots", "min_level", "max_level"}
        self.assertEqual(self._keys_read(source, None), allowed)
        planted = source.replace('out[str(entry["symbol"])] = ', 'entry["catch_rate"]\n            out[str(entry["symbol"])] = ', 1)
        self.assertNotEqual(planted, source)
        self.assertIn("catch_rate", self._keys_read(planted, None) - allowed)

    def test_v1_warps_and_connections_are_classified_leaf_by_leaf(self):
        """(The round-1 verifier's V1, 2026-10-31) `maps[].warps` and `maps[].connections` were SUBTREE entries, so a key
        planted under a warp (`warps[].script`, the verifier's gate mutant M4) passed RULE B unmarked. Every leaf under
        them is now classified by its OWN exact pattern, the containers marked without a subtree; a key planted under
        `warps[]` or `connections[]` FAILS (K-F3's shape). FAULT (17ed7794's check_fairness): both plants PASS."""
        from ai_player.gates import check_fairness as cf_
        schema = cf_.KNOWLEDGE_FIELDS["world/maps.json"]
        data = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
        leaves = sorted({p for p in cf_.key_paths(data) if p[2:3] in (("warps",), ("connections",)) and len(p) > 3})
        self.assertEqual(sorted({cf_.shown(p) for p in leaves}),
                         ["maps[].connections[].dir", "maps[].connections[].map", "maps[].connections[].offset",
                          "maps[].warps[].dest_map", "maps[].warps[].dest_warp_id", "maps[].warps[].elevation",
                          "maps[].warps[].x", "maps[].warps[].y"])
        for p in leaves:
            found = cf_.classify(p, schema)
            self.assertEqual(found and found[0], cf_.shown(p))  # its own pattern, never a parent's subtree
        for container in ("maps[].warps", "maps[].warps[]", "maps[].connections", "maps[].connections[]"):
            self.assertFalse(schema[container][2], container)  # FAULT half: a subtree, which classifies any plant

        def plant(edit) -> list[str]:
            with tempfile.TemporaryDirectory() as tmp:
                pkg = Path(tmp) / "ai_player"
                shutil.copytree(REPO / "ai_player", pkg, ignore=shutil.ignore_patterns(
                    "__pycache__", "evidence", "gates", "*.ss1", "eyes", "host"))
                path = pkg / "knowledge" / "world" / "maps.json"
                doc = json.loads(path.read_text(encoding="utf-8"))
                edit(doc)
                path.write_text(json.dumps(doc), encoding="utf-8")
                return cf_.check(pkg)[1]

        self.assertEqual(plant(lambda doc: None), [])  # CONTROL: the copy is clean

        def under(part: str, key: str):
            def edit(doc):
                next(m for m in doc["maps"] if m.get(part))[part][0][key] = "SomeScript_Label"
            return edit

        for part, key in (("warps", "script"), ("warps", "secret_door"), ("connections", "flag")):
            with self.subTest(part=part, key=key):
                found = plant(under(part, key))
                self.assertTrue(any("world/maps.json" in f and "UNCLASSIFIED" in f and f"maps[].{part}[].{key}" in f
                                    for f in found), found)  # FAULT (17ed7794): [] (classified by the subtree)

    def test_k_c6_the_atlas_facts_equal_the_pinned_decomp(self):
        """(KI-128, K-C6) The atlas's facts for the woods, ROUTE 104 and RUSTBORO CITY are the pinned decomp's own:
        PetalburgWoods is MAP_TYPE_ROUTE with warps (14, 5) and (15, 5) to Route104's warps 2 and 3, which are (10, 30)
        and (11, 30)."""
        from ai_player.knowledge.atlas import open_map
        decomp = {}
        for name in ("PetalburgWoods", "Route104", "RustboroCity"):
            decomp[name] = json.loads(Path(ROOT, "data", "maps", name, "map.json").read_text(encoding="utf-8"))
        maps = {m["id"]: m for m in json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))["maps"]}
        for name, const in (("PetalburgWoods", "PETALBURG_WOODS"), ("Route104", "ROUTE104"),
                            ("RustboroCity", "RUSTBORO_CITY")):
            self.assertEqual(maps["MAP_" + const]["map_type"], decomp[name]["map_type"], name)
            self.assertIs(open_map(const), decomp[name]["map_type"] in ("MAP_TYPE_ROUTE", "MAP_TYPE_CITY"), name)
        self.assertEqual(decomp["PetalburgWoods"]["map_type"], "MAP_TYPE_ROUTE")
        woods = [(w["x"], w["y"], w["dest_map"], int(w["dest_warp_id"])) for w in decomp["PetalburgWoods"]["warp_events"]]
        self.assertEqual(woods[:2], [(14, 5, "MAP_ROUTE104", 2), (15, 5, "MAP_ROUTE104", 3)])
        r104 = decomp["Route104"]["warp_events"]
        self.assertEqual([(r104[i]["x"], r104[i]["y"], r104[i]["dest_map"]) for i in (2, 3)],
                         [(10, 30, "MAP_PETALBURG_WOODS"), (11, 30, "MAP_PETALBURG_WOODS")])


# ---------------------------------------------------------------- slice 2, stage 2a: items_gifts.json
import check_fairness as cf  # noqa: E402
import extract_items as ei  # noqa: E402
import extract_events as xe  # noqa: E402
import extract_ways as xwy  # noqa: E402  (P11-1, 2026-11-11) the way through each dark cave: its output's name (W1)

_S2 = {}


def s2():
    """(the fresh items_gifts object, the build's parts) at the pin, built once (about 3 s)."""
    if not _S2:
        _S2["obj"], _S2["res"] = ei.build_all(ew.Decomp(ROOT), str(WORLD / "maps.json"))
    return _S2["obj"], _S2["res"]


def items_copy():
    return copy.deepcopy(s2()[0])


def gift(obj, prefix):
    return next(g for g in obj["gifts"] if g["id"].startswith(prefix))


def w7_acceptance(obj):
    """W7's two items_gifts facts (recon-data Q7 rows 5 and 16), as failures: Birch's five Poke Balls (lab :519 /
    :527, no own flag) and TM39 Rock Tomb (after Roxanne, in her gym).
    ‼ ROW 16 IS NOT MET FOR THE AI SINCE FIX ROUND 3 (a coordinator ruling is pending, fix3b-report.md): the fact
    'missable on a full bag and re-offered' was `until_received`; the round-3 SOLE-WRITER rule (fix-spec-3 item 1)
    cannot re-check a trainer flag (TRAINER_ROXANNE_1 is set by the battle, not by a named writer), so the record is
    `unknown`. What this pins is the honest current shape: `unknown`, never `once` (which would tell the AI a lost
    TM is gone), with the until_received evidence kept under dev.blocked_by (the gift's own setflag at :31)."""
    bad = []
    balls = [g for g in obj["gifts"] if g["ref"] in ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:519",
                                                      "data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:527")]
    if len(balls) != 2 or any(g["what"] != "ITEM_POKE_BALL" for g in balls):
        bad.append("row 5: Birch's Poke Balls %s" % [(g["id"], g["what"]) for g in balls])
    rt = [g for g in obj["gifts"] if g["what"] == "ITEM_TM_ROCK_TOMB"]
    if not rt or rt[0]["repeat"] != "unknown" or "Roxanne" not in (rt[0]["when"] or "").title() or \
            rt[0]["maps"] != ["MAP_RUSTBORO_CITY_GYM"] or \
            rt[0]["dev"].get("blocked_by") != ["FLAG_RECEIVED_TM_ROCK_TOMB = set (data/maps/RustboroCity_Gym/scripts.inc:31)"]:
        bad.append("row 16: Rock Tomb %s" % [(g["repeat"], g["when"], g["maps"]) for g in rt])
    return bad


class S2OutputTests(unittest.TestCase):
    """--check: the committed file is byte-identical to a fresh extraction (a determinism check, not a replication)."""

    def test_committed_equals_fresh(self):
        self.assertEqual((WORLD / ei.OUT_NAME).read_bytes(), serial(s2()[0]))
        bad = items_copy()
        bad["gifts"][0]["repeat"] = "daily" if bad["gifts"][0]["repeat"] != "daily" else "once"
        self.assertNotEqual((WORLD / ei.OUT_NAME).read_bytes(), serial(bad))

    def test_check_cli(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ei.main(["--check"]), 0)
            with tempfile.TemporaryDirectory() as tmp:
                bad = items_copy()
                bad["marts"][0]["lists"][0]["items"].pop()
                Path(tmp, ei.OUT_NAME).write_bytes(serial(bad))
                self.assertEqual(ei.main(["--check", "--out", tmp]), 1)

    def test_counts_re_measured(self):
        """The recon's counts at the pin (2026-10-22 notes), re-measured: 176 reachable gift lines (145 giveitem + 13
        givedecoration + 7 givemon + 1 giveegg in the map scripts, 10 shared giveitem once the Eon Ticket is excluded),
        58 TM/HM rows each with a source, 37 mart lists, 5 dead lines, 10 excluded."""
        obj, res = s2()
        self.assertEqual(len(obj["gifts"]), 176)
        self.assertEqual(len(obj["tm_hm"]), 58)
        self.assertTrue(all(row["sources"] for row in obj["tm_hm"]))
        self.assertEqual(sum(len(m["lists"]) for m in obj["marts"]), 37)
        self.assertEqual(len(obj["dead"]), 5)
        self.assertEqual(len(obj["excluded"]), 10)
        self.assertLess(res["max_closure"] * 2, ei.MAX_CLOSURE, "the closure bound has lost its margin")


class S2RuleTests(unittest.TestCase):
    """R-4..R-7 on the whole output, each with a FAULT beside the CONTROL; the extractor's door refuses each."""

    def test_r4_keys_only_under_dev(self):
        obj = items_copy()
        self.assertEqual(ei.dev_key_hits(obj), [])
        self.assertEqual(vw.s2_key_hits(obj), [])
        for plant in ("flag", "flags", "var", "vars"):
            bad = items_copy()
            bad["gifts"][3][plant] = "FLAG_RECEIVED_TM_ROCK_TOMB"
            self.assertTrue(ei.dev_key_hits(bad), plant)
            self.assertTrue(vw.s2_key_hits(bad), plant)
            self.assertRaises(ei.Refused, ei.refuse_dev_keys, bad)
        bad = items_copy()
        bad["marts"][0]["lists"][0]["when"] = "after FLAG_BADGE03_GET"
        self.assertRaises(ei.Refused, ei.refuse_dev_keys, bad)

    def test_r5_names_from_the_decomp(self):
        obj = items_copy()
        defined = ei.defined_names(ew.Decomp(ROOT))
        ei.check_dev_names(obj, defined)
        self.assertIn("FLAG_TEMP_SKIP_GABBY_INTERVIEW", defined)  # an alias emerald.txt lacks is still a real name
        bad = items_copy()
        bad["gifts"][0]["dev"]["flags"].append("FLAG_HIDE_FALLORBOR_POKEMON_CENTER_LANETTE")  # emerald.txt's spelling
        self.assertRaises(ei.Refused, ei.check_dev_names, bad, defined)

    def test_r6_r7_and_the_door(self):
        d = ew.Decomp(ROOT)
        defined = ei.defined_names(d)
        ei.refuse_all(items_copy(), defined)
        for where, key in ((("gifts", 0), "x"), (("marts", 0), "route"), (("gifts", 1), "iv"), (("gifts", 2), "aiFlags")):
            bad = items_copy()
            bad[where[0]][where[1]][key] = 1
            self.assertRaises(ei.Refused, ei.refuse_all, bad, defined)
            with tempfile.TemporaryDirectory() as tmp:
                self.assertRaises(ei.Refused, ei.write_output, tmp, bad, d)
                self.assertFalse(os.path.exists(os.path.join(tmp, ei.OUT_NAME)))

    def test_dead_and_excluded_are_named(self):
        obj = items_copy()
        dead = {x["label"] for x in obj["dead"]}
        self.assertEqual(dead, {"AquaHideout_B2F_EventScript_ItemMasterBall", "Route119_EventScript_ItemMaxElixir",
                                "Route119_EventScript_ItemNestBall", "MossdeepCity_StevensHouse_EventScript_DiveItemBall",
                                "LilycoveCity_ContestLobby_EventScript_SetDebug"})
        self.assertIn("IsContestDebugActive", next(x["why"] for x in obj["dead"] if "SetDebug" in x["label"]))
        ex = {x["ref"].split(":")[0] for x in obj["excluded"]}
        self.assertTrue({"data/scripts/gift_pichu.inc", "data/scripts/cable_club.inc",
                         "data/scripts/obtain_item.inc"} <= ex, ex)
        self.assertFalse({x["ref"] for x in obj["dead"] + obj["excluded"]} & {g["ref"] for g in obj["gifts"]})
        bad = items_copy()
        bad["dead"] = bad["dead"][1:]
        rep = vw.Report()
        vw.verify_items(ROOT, bad, vw.load(str(WORLD))["maps"], rep)
        self.assertTrue(any(ln.startswith("MISMATCH items dead:") for ln in rep.lines), rep.lines)

    def test_w7_acceptance(self):
        self.assertEqual(w7_acceptance(items_copy()), [])
        bad = items_copy()
        gift(bad, "RustboroCity_Gym_EventScript_GiveRockTomb")["repeat"] = "once"
        self.assertTrue(w7_acceptance(bad))
        bad = items_copy()
        bad["gifts"] = [g for g in bad["gifts"] if not g["ref"].endswith("ProfessorBirchsLab/scripts.inc:519")]
        self.assertTrue(w7_acceptance(bad))

    def test_conditions_that_matter(self):
        """The recon's conditionality table, as the output says it: daily, weekly + friendship, one of two fossils,
        a random berry range, the lottery's C table, an unresolvable prize kept 'unknown', words never invented."""
        obj = items_copy()
        self.assertEqual(gift(obj, "LilycoveCity_EventScript_BerryGentleman")["repeat"], "daily")
        ret = gift(obj, "PacifidlogTown_House2_EventScript_GiveReturn")
        # fix round 3 (item 3): an untabled special on the way in (GetDaysUntilPacifidlogTMAvailable) makes `when` null
        self.assertEqual((ret["repeat"], ret["when"]), ("weekly", None))
        self.assertEqual(next(w["dev"]["unworded"] for w in obj["_when_null"] if w["id"] == ret["id"]),
                         ["a special on the way in that SPECIAL_EFFECTS does not table: "
                          "GetDaysUntilPacifidlogTMAvailable"])
        self.assertEqual(gift(obj, "MirageTower_4F_EventScript_RootFossil")["exclusive_with"],
                         ["MirageTower_4F_EventScript_ClawFossil:1"])
        self.assertEqual(gift(obj, "LilycoveCity_DepartmentStore_1F_EventScript_LotteryClerk")["what"]["one_of"],
                         ["ITEM_EXP_SHARE", "ITEM_MASTER_BALL", "ITEM_MAX_REVIVE", "ITEM_PP_UP"])
        self.assertEqual(gift(obj, "LilycoveCity_PokemonCenter_1F_EventScript_GivePrize")["what"]["one_of"], "unknown")
        nulls = {w["id"] for w in obj["_when_null"]}
        self.assertTrue(all((g["when"] is None) == (g["id"] in nulls) for g in obj["gifts"]))
        self.assertFalse(any(isinstance(g["what"], str) and g["what"].startswith("VAR_") for g in obj["gifts"]))
        marts = {m["id"]: m for m in obj["marts"]}
        th = marts["TrainerHill_Entrance_EventScript_Clerk"]["lists"]
        self.assertEqual(th[0]["when"], "before entering the Hall of Fame")


class S2VerifierTests(unittest.TestCase):
    """verify_world's stage-2a reading: CONTROL 0 mismatches on the real file; each plant (e) (g) (h) (h2) (i) (j)
    (k), and fix round 1's (l)..(q), reported on exactly its own ONE line, (g) being the dead label a finditem
    recount would AGREE with."""

    def test_control_and_plants(self):
        rep = vw.Report()
        vw.verify_items(ROOT, vw.load_items(str(WORLD)), vw.load(str(WORLD))["maps"], rep)
        self.assertEqual(rep.lines, [])
        self.assertEqual(rep.counts.get("items_gift_lines"), 176)
        for name in vw.S2_PLANTS:
            ok, lines, prefix = vw.s2_plant_result(ROOT, str(WORLD), name)
            self.assertTrue(ok, "%s: %s not in %s" % (name, prefix, lines))

    def test_verifier_shares_no_function(self):
        src = (HERE / "verify_world.py").read_text(encoding="utf-8")
        self.assertNotRegex(src, r"^\s*(import|from)\s+extract_items", "the verifier must not import the extractor")


class S2GuardTests(unittest.TestCase):
    """Each guard of extract_items refuses its broken input (a scratch input, never the clone)."""

    def test_guards_refuse(self):
        d = ew.Decomp(ROOT)
        ev, gf = ei.script_files(d)
        ei.check_sources(d, ev, gf)
        self.assertRaises(ei.Refused, ei.check_sources, d, [f for f in ev if "Route104/" not in f], gf)
        self.assertRaises(ei.Refused, ei.vanilla_lines, "#ifdef DEBUG\n\tend\n#endif\n", "x.inc")
        self.assertEqual(len(ei.vanilla_lines("#ifdef BUGFIX\n\tA\n#else\n\tB\n#endif\n", "x.inc")), 6)

        class Fake:
            def read(self, rel):
                return "Dup::\n\tend\nDup::\n\tend\n"
        self.assertRaises(ei.Refused, ei.parse_labels, Fake(), ["a.inc"])
        labels = {"A": {"file": "a", "line": 1, "body": [], "next": None}}
        roots = [{"label": "Missing_Label", "map": "MAP_X", "giver": {"kind": "object"}, "object_flag": None}]
        self.assertRaises(ei.Refused, ei.check_map_scripts, roots, labels)
        chain = {"L%d" % i: [("L%d" % (i + 1), "goto", 1, None, None)] for i in range(ei.MAX_CLOSURE + 5)}
        self.assertRaises(ei.Refused, ei.closure, chain, "L0")

        class G:
            labels = {"List": {"file": "a", "line": 1, "body": [(2, ".2byte ITEM_POTION")], "next": None}}
        self.assertRaises(ei.Refused, ei.mart_items, G(), "List")
        G.labels["List"]["body"].append((3, "pokemartlistend"))
        self.assertEqual(ei.mart_items(G(), "List"), ["ITEM_POTION"])
        maps_doc = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
        ei.check_maps_json(maps_doc, d.sha)
        self.assertRaises(ei.Refused, ei.check_maps_json, dict(maps_doc, _source="pret/pokeemerald@0000"), d.sha)

    def test_build_refuses(self):
        """The guards' CALLS inside the build: each broken decomp file (an overlay) or input makes build_all refuse."""
        maps_path = str(WORLD / "maps.json")
        ev = raw_text("data/event_scripts.s")
        r104 = raw_text("data/maps/Route104/scripts.inc")
        # each refusal must come from ITS guard (the message names it): a later guard refusing the same broken input
        # would otherwise hide a deleted call (the first mutant round: check_sources' call survived that way)
        cases = {
            "neither data/event_scripts.s nor": {
                "data/event_scripts.s": ev.replace('\t.include "data/maps/Route104/scripts.inc"\n', "")},
            "map.json scripts that are no label": {
                "data/maps/Route104/map.json": raw_text("data/maps/Route104/map.json").replace(
                    '"Route104_EventScript_Boy2"', '"Route104_EventScript_NoSuchLabel"')},
            "R-4": {"data/maps/Route104/scripts.inc": r104.replace(
                "giveitem ITEM_TM_BULLET_SEED", "giveitem FLAG_RECEIVED_TM_BULLET_SEED")},
        }
        for needle, over in cases.items():
            self.assertNotEqual(list(over.values())[0], raw_text(list(over)[0]), needle)
            self.assertRaisesRegex(ei.Refused, re.escape(needle), ei.build_all, OverlayDecomp(ROOT, over), maps_path)
        with tempfile.TemporaryDirectory() as tmp:
            doc = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
            doc["_source"] = "pret/pokeemerald@0000000"
            Path(tmp, "maps.json").write_text(json.dumps(doc), encoding="utf-8")
            shutil.copy(WORLD / "trainers.json", Path(tmp, "trainers.json"))
            self.assertRaisesRegex(ei.Refused, "maps.json is from", ei.build_all, ew.Decomp(ROOT),
                                   str(Path(tmp, "maps.json")))
        defined = ei.defined_names(ew.Decomp(ROOT))
        for needle, plant in (("R-4", {"flag": "FLAG_X"}), ("R-5", {"dev": {"flags": ["FLAG_NO_SUCH_FLAG"]}})):
            bad = items_copy()
            bad["gifts"][5].update(plant)
            self.assertRaisesRegex(ei.Refused, needle, ei.refuse_all, bad, defined)

    def test_constant_branch_is_pruned(self):
        obj, res = s2()
        self.assertEqual([p[2] for p in res["graph"].pruned], ["IsContestDebugActive"])
        self.assertFalse(any("ContestLobby_EventScript_SetDebug" in p["id"] for p in obj["purchases"]))


def fake_graph(text):
    """An extract_items Graph over one synthetic script file (rooted at its first label, an object on MAP_X)."""
    class Fake:
        def read(self, rel):
            return text
    labels = ei.parse_labels(Fake(), ["x.inc"])
    edges = ei.build_edges(labels)
    first = next(iter(labels))
    roots = [{"label": first, "map": "MAP_X", "cond": None, "object_flag": None, "hidden": False,
              "giver": {"map": "MAP_X", "kind": "object", "object": 1, "local_id": 1, "graphics": "G"}}]
    return ei.Graph(None, labels, edges, roots, {})


def no_condition_over_tests(obj):
    """Records whose `when` says 'no condition' while dev.tests is not empty (F5: never)."""
    recs = obj["gifts"] + obj["purchases"] + [lst for m in obj["marts"] for lst in m["lists"]]
    return [r.get("id", r.get("label")) for r in recs if r["when"] == "no condition beyond `repeat`" and r["dev"]["tests"]]


class S2FixRound1Tests(unittest.TestCase):
    """FIX ROUND 1 of stage 2a (the verifier's F1-F6), each a FAULT beside its CONTROL:
    F1 `repeatable` only on positive evidence (nothing after the gift moves state); F2 no fall-through out of a data
    table; F3 rule E, the arms of one menu are one choice; F4 every CHOOSER_OF entry cited to a line holding its token
    (the Favor Lady is `random`); F5 a test on the own var is a story gate unless it is the once-guard; F6 the lottery's
    words, the Mirage Tower's map condition, the Petalburg mart's setter by reference."""

    def test_fresh_build_passes_the_verifier(self):
        """The independent verifier (rules a1-a4 + the golden list) over a FRESH extraction, not the committed file: a
        semantic check of the build itself (the --check byte comparison is only a determinism check)."""
        rep = vw.Report()
        vw.verify_items(ROOT, items_copy(), vw.load(str(WORLD))["maps"], rep)
        self.assertEqual(rep.lines, [])
        bad = items_copy()  # FAULT: the fresh build with HM Fly said repeatable
        gift(bad, "Route119_EventScript_GiveFlyHM")["repeat"] = "repeatable"
        rep = vw.Report()
        vw.verify_items(ROOT, bad, vw.load(str(WORLD))["maps"], rep)
        self.assertEqual(len(rep.lines), 1)

    def test_f1_repeat_on_positive_evidence(self):
        """Updated in fix round 3 (stage 3b): round 1's `after_gift` is gone; `repeatable` now rests on evidence()'s
        open path or a cited re-arm (dev.repeat_why / dev.rearm), and the strict sole-writer rule moved many records
        to `unknown` (fix-spec-3: 'more unknown is the expected, correct cost'). Counts re-measured at the pin."""
        obj, res = s2()
        counts = {}
        for x in obj["gifts"]:
            counts[x["repeat"]] = counts.get(x["repeat"], 0) + 1
        self.assertEqual(counts, {"once": 28, "repeatable": 11, "until_received": 41, "daily": 27, "weekly": 2,
                                  "unknown": 67})
        for x in obj["gifts"]:  # CONTROL: every repeatable gift says WHY: an open path, or a re-arm it cites
            if x["repeat"] == "repeatable":
                why = x["dev"].get("repeat_why") or ""
                self.assertTrue(why.startswith("a path stays open") or (x["dev"].get("rearm") and "re-arm" in why),
                                (x["id"], why))
        want = {"PetalburgCity_WallysHouse_EventScript_GiveHMSurf:1": "unknown",       # VAR_PETALBURG_CITY_STATE: 3 writers
                "Route119_EventScript_GiveFlyHM:1": "once",                            # VAR_ROUTE119_STATE, sole at :144
                "PetalburgCity_Gym_EventScript_GiveFacade:1": "unknown",               # VAR_PETALBURG_GYM_STATE: addvar elsewhere
                "LittlerootTown_ProfessorBirchsLab_EventScript_MayGivePokeBalls:1": "unknown",
                "Route111_EventScript_GiveSecretPower:1": "until_received",            # removeobject VAR_LAST_TALKED
                "DesertUnderpass_EventScript_GiveClawFossil:1": "unknown",             # its hide flag has other writers
                "SlateportCity_PokemonFanClub_EventScript_GiveRedScarf:1": "unknown",  # its flag, also set before the gift
                "SlateportCity_Harbor_EventScript_DeepSeaTooth:1": "until_received"}   # the one Scanner, handed over
        self.assertEqual({k: gift(obj, k)["repeat"] for k in want}, want)
        notes = {x["id"]: x["dev"] for x in obj["_notes"]["repeat_unknown"]}
        self.assertEqual(sorted(notes), sorted(x["id"] for x in obj["gifts"] if x["repeat"] == "unknown"))
        self.assertEqual(gift(obj, "SlateportCity_Harbor_EventScript_DeepSeaTooth")["dev"]["blocked_by"],
                         ["ITEM:ITEM_SCANNER = sub 1 (data/maps/SlateportCity_Harbor/scripts.inc:337)"])
        # FAULT (s2_faulted F-writer): `setvar VAR_ROUTE119_STATE, 0` planted after the Lava Cookie lady's giveitem, a
        # write her path does not test but Route 119's coord events read: her gift is no longer `repeatable`
        self.assertEqual(gift(obj, "MtChimney_EventScript_LavaCookieLady")["repeat"], "repeatable")
        self.assertEqual(gift(s2_faulted(), "MtChimney_EventScript_LavaCookieLady")["repeat"], "unknown")

    def test_f2_no_fall_out_of_a_table(self):
        obj, res = s2()
        g = res["graph"]
        falls = [(s, t) for s, outs in g.edges.items() for t, k, *_ in outs if k == "fall"
                 and any(c.startswith(".") for _, c in g.labels[s]["body"])]
        self.assertEqual(falls, [])  # round 0: 427 (every map_script / map_script_2 table and MapScripts list)
        lab = lambda *body: {"body": list(enumerate(body, 1))}  # noqa: E731
        self.assertFalse(ei.falls_through(lab("map_script_2 VAR_X, 4, L", ".2byte 0")))
        self.assertFalse(ei.falls_through(lab("map_script MAP_SCRIPT_ON_FRAME_TABLE, L")))
        self.assertFalse(ei.falls_through(lab("msgbox T", "end")))
        self.assertFalse(ei.falls_through(lab(".string \"x$\"")))
        self.assertTrue(ei.falls_through(lab("msgbox T", "setflag FLAG_X")))  # FAULT side: a command runs on
        self.assertTrue(ei.falls_through(lab()))
        for gid, test in (("PetalburgCity_WallysHouse_EventScript_GiveHMSurf:1", "VAR_PETALBURG_CITY_STATE eq 4"),
                          ("MossdeepCity_StevensHouse_EventScript_StevenGivesDive:1", "VAR_STEVENS_HOUSE_STATE eq 1"),
                          ("RustboroCity_DevonCorp_3F_EventScript_MeetPresident:1", "VAR_DEVON_CORP_3F_STATE eq 0")):
            self.assertIn(test, gift(obj, gid)["dev"]["tests"])
            self.assertIsNone(gift(obj, gid)["when"])
        for gid in ("Route114_EventScript_Man:1", "Route118_EventScript_ReceiveGoodRod:1"):
            self.assertEqual([x["kind"] for x in gift(obj, gid)["giver"]], ["object"], gid)

    def test_f3_menu_arms_are_one_choice(self):
        obj = s2()[0]
        pairs = (("SlateportCity_Harbor_EventScript_DeepSeaTooth:1", "SlateportCity_Harbor_EventScript_DeepSeaScale:1"),
                 ("MauvilleCity_BikeShop_EventScript_GetMachBike:1", "MauvilleCity_BikeShop_EventScript_GetAcroBike:1"))
        for a, b in pairs:
            self.assertEqual((gift(obj, a)["exclusive_with"], gift(obj, b)["exclusive_with"]), ([b], [a]))
        # fix round 2 (item 5): the four Trick House tents are ONE prize (EXCLUSIVE_CITED): each excludes the other three
        tents = ["Route110_Trick%s_EventScript_Give%sTent:1" % (w, c) for w in ("HouseEnd", "HouseEntrance")
                 for c in ("Red", "Blue")]
        for t in tents:
            self.assertEqual(gift(obj, t)["exclusive_with"], sorted(set(tents) - {t}), t)
        text = ("Menu::\n\tmultichoice 0, 0, MULTI_TENT, TRUE\n\tswitch VAR_RESULT\n\tcase 0, GiveA\n\tgoto GiveB\n"
                "GiveA::\n\tgiveitem ITEM_POTION\n\treturn\nGiveB::\n\tgiveitem ITEM_ANTIDOTE\n\treturn\n")

        def run(txt, repeat):
            gifts = [{"id": "GiveA:1", "what": {"one_of": "unknown", "chosen_by": "unknown"}, "repeat": repeat,
                      "exclusive_with": []},
                     {"id": "GiveB:1", "what": "ITEM_ANTIDOTE", "repeat": repeat, "exclusive_with": []}]
            ei.menu_exclusive(gifts, fake_graph(txt), {"GiveA": [gifts[0]], "GiveB": [gifts[1]]})
            return [x["exclusive_with"] for x in gifts], gifts[0]["what"]["chosen_by"]
        self.assertEqual(run(text, "once"), ([["GiveB:1"], ["GiveA:1"]], "choice"))  # CONTROL: case arm vs default goto
        self.assertEqual(run(text, "repeatable"), ([[], []], "choice"))  # both repeatable: the menu can be opened again
        self.assertEqual(run(text.replace("multichoice 0, 0, MULTI_TENT, TRUE", "msgbox T, MSGBOX_DEFAULT"), "once"),
                         ([[], []], "unknown"))                           # FAULT: no menu, so no choice either

    def test_f4_every_chooser_is_cited(self):
        d = ew.Decomp(ROOT)
        cites = ei.table_cites()
        self.assertEqual({e.split(" ", 1)[1] for e, _, _ in cites if e.startswith("CHOOSER_OF")}, set(ei.CHOOSER_OF))

        def unheld(table):
            out = []
            for entry_, where, token in table:
                rel, n = where.rsplit(":", 1)
                lines = raw_text(rel).split("\n")
                if int(n) > len(lines) or token not in lines[int(n) - 1]:
                    out.append(entry_)
            return out
        self.assertEqual(unheld(cites), [])  # CONTROL: each cite opened at the pin holds its token
        moved = [(e, "%s:%d" % (w.rsplit(":", 1)[0], int(w.rsplit(":", 1)[1]) + 1), t) for e, w, t in cites]
        self.assertEqual(len(unheld(moved)), len(cites))  # FAULT: every line number off by one is refused
        ei.check_cites(d)
        saved = ei.CHOOSER_CITED["FavorLadyGetPrize"]
        try:
            ei.CHOOSER_CITED["FavorLadyGetPrize"] = ("random", ("src/lilycove_lady.c:134", "Random()"))
            self.assertRaisesRegex(ei.Refused, "FavorLadyGetPrize", ei.check_cites, d)
        finally:
            ei.CHOOSER_CITED["FavorLadyGetPrize"] = saved
        rel = "src/lottery_corner.c"  # FAULT through the build: the cited file moves by one line
        self.assertRaisesRegex(ei.Refused, "cited table lines", ei.build_all,
                               OverlayDecomp(ROOT, {rel: "\n" + raw_text(rel)}), str(WORLD / "maps.json"))
        self.assertEqual(ei.CHOOSER_OF["FavorLadyGetPrize"], "random")
        self.assertEqual(gift(s2()[0], "LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize")["what"]["chosen_by"],
                         "random")

    def test_f5_story_gates_stay(self):
        obj = s2()[0]
        ss = gift(obj, "PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV")
        self.assertEqual((ss["when"], ss["dev"]["tests"]),
                         ("after entering the Hall of Fame", ["VAR_LITTLEROOT_HOUSES_STATE_MAY eq 3"]))
        nulls = {w["id"] for w in obj["_when_null"]}
        for n in range(1, 8):
            th = gift(obj, "Route110_TrickHouseEnd_EventScript_CompletedPuzzle%d" % n)
            self.assertEqual(th["dev"]["tests"], ["VAR_TRICK_HOUSE_LEVEL eq %d" % (n - 1)])
            self.assertTrue(th["when"] is None and th["id"] in nulls)
        # fix round 2: each path's conditions in dev.path_tests (they differ); none is common, and `when` is null
        rus = gift(obj, "RusturfTunnel_EventScript_ClearTunnelScene")
        self.assertEqual((rus["dev"]["tests"], rus["dev"]["path_tests"], rus["when"]),
                         ([], [["VAR_RUSTURF_TUNNEL_STATE eq 4"], ["VAR_RUSTURF_TUNNEL_STATE eq 5"]], None))
        self.assertEqual(no_condition_over_tests(obj), [])
        bad = items_copy()
        bad["gifts"][0]["when"], bad["gifts"][0]["dev"]["tests"] = "no condition beyond `repeat`", ["VAR_X eq 1"]
        self.assertEqual(len(no_condition_over_tests(bad)), 1)
        info = {"own_values": ["1"]}
        self.assertTrue(ei.is_once_guard(("var", "V", "ne", "1"), "V", info))       # flipped by the gift's own write
        self.assertTrue(ei.is_once_guard(("var", "V", "lt", "2"), "V", {"own_values": ["2"]}))
        self.assertTrue(ei.is_once_guard(("flag", "F", False), "F", None))
        self.assertFalse(ei.is_once_guard(("var", "V", "eq", "4"), "V", {"own_values": ["5"]}))  # a value set elsewhere
        self.assertFalse(ei.is_once_guard(("var", "V", "eq", "0"), "V", info))      # eq is kept (the Letter)
        self.assertFalse(ei.is_once_guard(("var", "V", "ne", "1"), "V", {"own_values": None}))  # a relative write
        self.assertFalse(ei.is_once_guard(("var", "W", "ne", "1"), "V", info))      # another var
        # FAULT: a second setter of the value 3, outside the Hall of Fame: the setter rule no longer words it
        rel = "data/maps/InsideOfTruck/scripts.inc"
        old = "setvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 1"
        self.assertIn(old, raw_text(rel))
        bad, _ = ei.build_all(OverlayDecomp(ROOT, {rel: raw_text(rel).replace(old, old[:-1] + "3")}),
                              str(WORLD / "maps.json"))
        self.assertIsNone(gift(bad, "PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV")["when"])

    def test_f6_records_the_ai_could_misread(self):
        obj = s2()[0]
        lot = gift(obj, "LilycoveCity_DepartmentStore_1F_EventScript_LotteryClerk")["what"]
        self.assertEqual(lot["chosen_by"], "draw")
        self.assertIn("most draws win nothing", lot["words"])
        self.assertNotIn("words", ei.DEV_KEYS)  # an AI-facing key (a `note` would be developer-only)
        nulls = {w["id"]: w["dev"]["unworded"] for w in obj["_when_null"]}
        for gid in ("MirageTower_4F_EventScript_RootFossil:1", "MirageTower_4F_EventScript_ClawFossil:1"):
            g = gift(obj, gid)
            self.assertIsNone(g["when"])
            self.assertIn("src/mirage_tower.c:328", g["dev"]["map_condition"]["refs"])
            self.assertTrue(any("coin flip" in u for u in nulls[gid]))
        self.assertNotIn("map_condition", gift(obj, "DesertUnderpass_EventScript_GiveClawFossil")["dev"])  # CONTROL
        marts = {m["id"]: m for m in obj["marts"]}
        exp = next(x for x in marts["PetalburgCity_Mart_EventScript_Clerk"]["lists"]
                   if x["label"] == "PetalburgCity_Mart_Pokemart_Expanded")
        setter = next(x for x in exp["dev"]["setters"] if x["ref"] == "data/event_scripts.s:678")
        self.assertEqual(sorted(x["ref"].split("/")[2] for x in setter["reached_by"]),
                         ["DewfordTown_Gym", "LavaridgeTown_Gym_1F", "MauvilleCity_Gym", "RustboroCity_Gym"])
        self.assertTrue(all(x["test"] == "VAR_PETALBURG_GYM_STATE eq 6" for x in setter["reached_by"]))
        self.assertIsNone(exp["when"])  # words only from a rule: none covers VAR_PETALBURG_GYM_STATE 6
        basic = next(x for x in marts["PetalburgCity_Mart_EventScript_Clerk"]["lists"]
                     if x["label"] == "PetalburgCity_Mart_Pokemart_Basic")
        self.assertNotIn("setters", basic["dev"])  # CONTROL: the basic list tests no flag set


class S2VerifierFixTests(unittest.TestCase):
    """F7: the verifier now reads repeat, when, chosen_by, one_of and exclusive_with (rules + a golden list read off the
    decomp by hand, its cites checked at verify time), and its daily guard regex takes every conditional form."""

    def test_daily_regex(self):
        for ok in ("goto_if_set FLAG_DAILY_X, L", "call_if_set FLAG_DAILY_X, L", "goto_if_unset FLAG_DAILY_X, L",
                   "call_if_unset FLAG_DAILY_LILYCOVE_RECEIVED_BERRY, L"):
            self.assertTrue(vw.S2_DAILY.search(ok), ok)
        for no in ("setflag FLAG_DAILY_X", "goto_if_set FLAG_RECEIVED_X, L", "goto_if_eq VAR_DAILY_X, 1, L",
                   "call_if_set FLAG_DAILYX, L"):
            self.assertFalse(vw.S2_DAILY.search(no), no)

    def test_golden_cites_fail_loudly(self):
        self.assertGreaterEqual(len(vw.S2_GOLDEN), 20)
        self.assertTrue(all(e["cites"] for e in vw.S2_GOLDEN))
        saved = copy.deepcopy(vw.S2_GOLDEN)
        try:
            e = next(x for x in vw.S2_GOLDEN if x.get("id") == "LilycoveCity_EventScript_BerryGentleman:1")
            e["cites"][0] = ("data/maps/LilycoveCity/scripts.inc:38", e["cites"][0][1])  # a moved pin
            rep = vw.Report()
            vw.verify_items(ROOT, vw.load_items(str(WORLD)), vw.load(str(WORLD))["maps"], rep)
            self.assertEqual(len(rep.lines), 1)
            self.assertIn("golden cite data/maps/LilycoveCity/scripts.inc:38 no longer holds", rep.lines[0])
        finally:
            vw.S2_GOLDEN[:] = saved

    def test_each_rule_fires(self):
        """One FAULT per rule check, on records the golden list does NOT hold (so the RULE is what fires)."""
        items = vw.load_items(str(WORLD))
        golden = {e.get("id") for e in vw.S2_GOLDEN}
        cases = (("FortreeCity_Gym_EventScript_GiveAerialAce:1", "repeat", "repeatable",
                  "runs after it"),                                           # a1 (Birch's balls became golden: round 2)
                 ("Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1", "exclusive_with", [],
                  "exclusive_with lacks the sibling"),                       # a2
                 ("Route116_EventScript_GiveRepeatBall:1", "giver",
                  [{"map": "MAP_ROUTE116", "kind": "map_script"}], "no map_script / map_script_2 entry"),  # a3
                 ("Route120_EventScript_GiveBerry:1", "what", {"one_of": ["ITEM_FIGY_BERRY"]}, "needs one_of"))  # a4
        for gid, key, val, needle in cases:
            self.assertNotIn(gid, golden)
            bad = copy.deepcopy(items)
            next(g for g in bad["gifts"] if g["id"] == gid)[key] = val
            rep = vw.Report()
            vw.verify_items(ROOT, bad, vw.load(str(WORLD))["maps"], rep)
            self.assertEqual(len(rep.lines), 1, rep.lines)
            self.assertTrue(rep.lines[0].startswith("MISMATCH items gift %s:" % gid) and needle in rep.lines[0],
                            rep.lines)


_S2F = {}


def s2_faulted():
    """ONE extraction with SEVEN independent faults planted at once, built once (about 9 s) and shared by the fix-round
    2/3 tests. Each fault touches records the others leave alone, and each test reads only its own fault's records, so
    one build serves as every FAULT arm that must go through the whole extractor (a fresh build per fault would cost
    9 s each, again for every mutant of the mutant run):
      F-rearm    REARM without the 8 Shoal Cave entries (the salt and shells lose their cited daily re-arm);
      F-writer   an overlay adds `setvar VAR_ROUTE119_STATE, 0` right after the Lava Cookie's giveitem
                 (data/maps/MtChimney/scripts.inc:98-99, so the new line is :100): a writer of HM Fly's blocking var
                 outside its continuation, and a write the Lava Cookie's path does not test but Route 119 reads;
      F-castform MAP_CONDITIONS without Route119_WeatherInstitute_2F;
      F-weekly   SPECIAL_EFFECTS without SetPacifidlogTMReceivedDay (on the Pacifidlog TMs' continuation);
      F-seedot   SPECIAL_EFFECTS without CompareSeedotSize (on Big Seedot's way in; Big Lotad is the control);
      F-room     checkitem moved from POSSESSION to ROOM_PRODUCERS (round 1's bug: owning an item counted as room);
      F-tents    EXCLUSIVE_CITED emptied (the Trick House tents lose their cited one-prize link).
    The tables are restored in `finally`, whatever the build does."""
    if not _S2F:
        rel = "data/maps/MtChimney/scripts.inc"
        old = "\tgiveitem ITEM_LAVA_COOKIE\n\tgoto_if_eq VAR_RESULT, FALSE, MtChimney_EventScript_BagIsFull\n"
        text = raw_text(rel)
        assert text.count(old) == 1, "the Lava Cookie lines moved"
        tables = (ei.REARM, ei.MAP_CONDITIONS, ei.SPECIAL_EFFECTS, ei.POSSESSION, ei.ROOM_PRODUCERS)
        saved = [dict(t) for t in tables] + [list(ei.EXCLUSIVE_CITED)]
        try:
            for k in [k for k in ei.REARM if k.startswith("FLAG_RECEIVED_SHOAL_")]:
                del ei.REARM[k]
            del ei.MAP_CONDITIONS["Route119_WeatherInstitute_2F"]
            del ei.SPECIAL_EFFECTS["SetPacifidlogTMReceivedDay"]
            del ei.SPECIAL_EFFECTS["CompareSeedotSize"]
            ei.ROOM_PRODUCERS["checkitem"] = ei.POSSESSION.pop("checkitem")
            ei.EXCLUSIVE_CITED[:] = []
            over = {rel: text.replace(old, old + "\tsetvar VAR_ROUTE119_STATE, 0\n")}
            _S2F["obj"], _ = ei.build_all(OverlayDecomp(ROOT, over), str(WORLD / "maps.json"))
        finally:
            for t, keep in zip(tables, saved):
                t.clear()
                t.update(keep)
            ei.EXCLUSIVE_CITED[:] = saved[-1]
    return _S2F["obj"]


class Ctx:
    """The two things holds_at_start / is_once_guard read off a build's Context: the graph (its Decomp) and the flags
    EventScript_ResetAllMapFlags sets at new game."""

    def __init__(self):
        self.g = s2()[1]["graph"]
        self.hidden0 = ei.hidden_at_start(self.g.labels)


_CTX = {}


def real_ctx():
    """A build's own Context over the fresh graph (its writer index built on first use): the sole-writer rule's inputs
    for the function-level tests (the build keeps its Context local). Built once."""
    if not _CTX:
        g = s2()[1]["graph"]
        ctx = ei.Context(g, ei.read_maps(g.d), set(), json.loads((WORLD / "maps.json").read_text(encoding="utf-8")))
        ctx.hidden0 = ei.hidden_at_start(g.labels)
        _CTX["ctx"] = ctx
    return _CTX["ctx"]


class Swap:
    """Set `obj.name = value` for a `with` block, put back after (a rule turned off, a table entry removed)."""

    def __init__(self, obj, name, value):
        self.obj, self.name, self.value = obj, name, value

    def __enter__(self):
        self.saved = getattr(self.obj, self.name)
        setattr(self.obj, self.name, self.value)

    def __exit__(self, *exc):
        setattr(self.obj, self.name, self.saved)


def plant_ok(name):
    return vw.s2_plant_result(ROOT, str(WORLD), name)[0]


#: round 2's Favor Lady words (fix2-items_gifts.json), false in solo play: the FAULT arm of favor_words_ok
FAVOR_ROUND2 = ("the lady in the Lilycove Pokemon Center is the Favor Lady; it is the 5th item of hers you have given "
                "that she liked (her single best item counts as all 5); it is an item she likes")


def favor_words_ok(when):
    """Fix-spec-3 item 4: the Favor Lady's words true for SOLO play. She takes ONE item (src/lilycove_lady.c:237 sets
    COMPLETED on every item given), so the words must say so and name her single favourite, and never describe a
    count of liked items (5th / all 5 / five), which only record mixing could make possible."""
    return bool(when) and "she takes only one" in when and "single favourite" in when and \
        not re.search(r"\b5th\b|\ball 5\b|\bfive\b", when)


class S2FixRound23Tests(unittest.TestCase):
    """FIX ROUNDS 2 AND 3 of stage 2a (fix-spec-2 items 1-7, fix-spec-3 items 1-7), one test per item, each a FAULT
    beside its CONTROL, plus the Johto starter ball (round 2's surviving mutant M11). The FAULT arms that need the
    whole extractor share ONE faulted build (s2_faulted); the rest break the rule at the function it lives in. WHY:
    three rounds each closed their verifier's failures and each next verifier found a new wrong value; a value the
    tests do not pin, a later edit can silently change."""

    # ---------------------------------------------------------------- fix-spec-2
    def test_r2_1_blocking_writer_and_known_answers(self):
        """F2-1: `repeatable` needs an open path or a cited re-arm; `until_received` is decided by the gift's own
        result test before its blocking writer (Cozmo: `goto_if_eq VAR_RESULT, FALSE` at :20, a call at :22, the
        setflag at :23). Known answers: the Glass Workshop flute and decor re-armed by their own :195 / :285, the
        Contest Hall Luxury Ball by contest_hall.inc:181, the Deep Sea pair blocked by the one Scanner, the Favor Lady
        never repeatable. (Beldum's round-2 answer `until_received` is now `unknown`: the golden list keeps its truth.)"""
        obj = s2()[0]
        for gid in ("Route113_GlassWorkshop_EventScript_GiveGlassFlute:1",
                    "Route113_GlassWorkshop_EventScript_GiveGlassDecor:1"):
            g = gift(obj, gid)
            self.assertEqual((g["repeat"], [r["ref"] for r in g["dev"]["rearm"]]),
                             ("repeatable", ["data/maps/Route113_GlassWorkshop/scripts.inc:195",
                                             "data/maps/Route113_GlassWorkshop/scripts.inc:285"]), gid)
        hall = gift(obj, "ContestHall_EventScript_GiveLuxuryBall")
        self.assertEqual(hall["repeat"], "repeatable")
        self.assertIn("data/scripts/contest_hall.inc:181", [r["ref"] for r in hall["dev"]["rearm"]])
        for gid in ("SlateportCity_Harbor_EventScript_DeepSeaTooth:1", "SlateportCity_Harbor_EventScript_DeepSeaScale:1"):
            self.assertEqual(gift(obj, gid)["repeat"], "until_received", gid)
        cozmo = gift(obj, "FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite")
        self.assertEqual((cozmo["repeat"], cozmo["dev"]["blocked_by"]),
                         ("until_received", ["FLAG_RECEIVED_TM_RETURN = set "
                                             "(data/maps/FallarborTown_CozmosHouse/scripts.inc:23)"]))
        self.assertNotEqual(gift(obj, "LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize")["repeat"],
                            "repeatable")
        # FAULT: F-writer, a write of a var Route 119 reads, after the Lava Cookie: no open path is proven any more
        self.assertEqual(gift(obj, "MtChimney_EventScript_LavaCookieLady")["dev"]["repeat_why"],
                         "a path stays open after the gift (nothing it tests is changed)")
        self.assertEqual(gift(s2_faulted(), "MtChimney_EventScript_LavaCookieLady")["repeat"], "unknown")

    def test_r2_2_no_condition_needs_an_ungated_path(self):
        """F2-2: 'no condition' only when SOME path has no condition at all; two paths with DIFFERENT gates are worded
        'either (A) or (B)' (round 1 intersected them and printed 'no condition' for 7 records)."""
        obj = s2()[0]
        for g in obj["gifts"]:  # CONTROL: every 'no condition' record has a path whose condition set is empty
            if g["when"] == "no condition beyond `repeat`":
                self.assertEqual(g["dev"]["tests"], [], g["id"])
                self.assertTrue(not g["dev"].get("path_tests") or [] in g["dev"]["path_tests"], g["id"])
        for gid in ("RustboroCity_EventScript_ReturnGoods:1", "SootopolisCity_EventScript_KiriGiveBerry:1",
                    "Route120_EventScript_StevenGiveDeconScope:1", "PetalburgCity_Gym_EventScript_GiveFacade:1",
                    "Route119_WeatherInstitute_2F_EventScript_ReceiveCastform:1",
                    "LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize:1",
                    "LilycoveCity_PokemonCenter_1F_EventScript_GivePrize:1"):
            self.assertNotEqual(gift(obj, gid)["when"], "no condition beyond `repeat`", gid)
        p1 = [(("flag", "FLAG_BADGE01_GET", True), "x.inc:1")]
        p2 = [(("flag", "FLAG_BADGE02_GET", True), "x.inc:2")]
        self.assertEqual(ei.when_of([p1, p2], None, {})[0], "either (after badge 1) or (after badge 2)")
        # FAULT: round 1's rule (the intersection of the paths' tests) finds nothing common: it said 'no condition'
        self.assertEqual(ei.common_tests([p1, p2]), set())
        self.assertEqual(ei.when_of([p1, p2, []], None, {})[0], "no condition beyond `repeat`")  # an ungated path

    def test_r2_3_possession_is_a_condition(self):
        """F2-3: owning an item, money or coins is a CONDITION worded from the item's display name and count, never
        bag room (ROOM_PRODUCERS keeps only the room measures, each cited)."""
        obj = s2()[0]
        for gid, words in (("MauvilleCity_House2_EventScript_AcceptTrade:1", "needs 1 Harbor Mail"),
                           ("ShoalCave_LowTideEntranceRoom_EventScript_ShellBellExpert:1", "needs 4 Shoal Salt"),
                           ("ShoalCave_LowTideEntranceRoom_EventScript_ShellBellExpert:1", "needs 4 Shoal Shell"),
                           ("FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite:1", "needs 1 Meteorite"),
                           ("SlateportCity_Harbor_EventScript_DeepSeaTooth:1", "needs 1 Scanner"),
                           ("MtChimney_EventScript_LavaCookieLady:1", "needs at least 200 money")):
            self.assertIn(words, gift(obj, gid)["when"] or "", gid)
        self.assertFalse(set(ei.ROOM_PRODUCERS) & set(ei.POSSESSION))
        cited = {e for e, _, _ in ei.table_cites()}
        self.assertTrue({"ROOM_PRODUCERS " + k for k in ei.ROOM_PRODUCERS} <= cited)
        self.assertTrue({"POSSESSION " + k for k in ei.POSSESSION} <= cited)
        # FAULT: F-room, checkitem counted as room: the Coin Case's Harbor Mail trade reads 'no condition' again
        self.assertEqual(gift(s2_faulted(), "MauvilleCity_House2_EventScript_AcceptTrade")["when"],
                         "no condition beyond `repeat`")

    def test_r2_4_specials_table(self):
        """F2-4: every special on a gift's trigger path or continuation is in the CITED SPECIAL_EFFECTS table (a kind
        from the five), and one missing on the continuation makes `repeat` unknown (the weekly Pacifidlog TMs)."""
        obj = s2()[0]
        cited = {e for e, _, _ in ei.table_cites()}
        for k, v in ei.SPECIAL_EFFECTS.items():
            self.assertIn(v[0], ("inert", "result", "resource", "writes", "record"), k)
            self.assertIn("SPECIAL_EFFECTS " + k, cited)
        for gid in ("PacifidlogTown_House2_EventScript_GiveReturn:1", "PacifidlogTown_House2_EventScript_GiveFrustration:1"):
            self.assertEqual(gift(obj, gid)["repeat"], "weekly", gid)
        for mon in ("Seedot", "Lotad"):  # the size records: SPECIALVAR_WORDS + LINE_WORDS give every word
            g = gift(obj, "SootopolisCity_LotadAndSeedotHouse_EventScript_Big%s" % mon)
            self.assertEqual((g["repeat"], g["when"]), (
                "repeatable", "you show him a %s bigger than the biggest one he has seen (each bigger one sets a new "
                              "record); you show him one of your Pokemon" % mon), mon)
        # FAULT: F-weekly, SetPacifidlogTMReceivedDay untabled on the continuation: `repeat` unknown, the why names it
        for gid in ("PacifidlogTown_House2_EventScript_GiveReturn:1", "PacifidlogTown_House2_EventScript_GiveFrustration:1"):
            g = gift(s2_faulted(), gid)
            self.assertEqual(g["repeat"], "unknown", gid)
            self.assertIn("SetPacifidlogTMReceivedDay", g["dev"]["repeat_why"], gid)

    def test_r2_5_alternatives(self):
        """F2-5: one gift of two by a chooser fixed at new game (gender: Lavaridge's Go-Goggles, Birch's Poke Balls;
        trainer ID: the Favor Lady vs the Quiz Lady) are exclusive_with each other (rule G); the four Trick House tents
        are one prize (EXCLUSIVE_CITED)."""
        obj = s2()[0]
        for a, b in (("LavaridgeTown_EventScript_MayGiveGoGoggles:1", "LavaridgeTown_EventScript_BrendanGiveGoGoggles:1"),
                     ("LittlerootTown_ProfessorBirchsLab_EventScript_MayGivePokeBalls:1",
                      "LittlerootTown_ProfessorBirchsLab_EventScript_BrendanGivePokeBalls:1"),
                     ("LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize:1",
                      "LilycoveCity_PokemonCenter_1F_EventScript_GivePrize:1")):
            self.assertEqual((gift(obj, a)["exclusive_with"], gift(obj, b)["exclusive_with"]), ([b], [a]))

        def fixed(v1, v2):
            gs = [{"id": "G%d:1" % i, "maps": ["MAP_X"], "exclusive_with": [],
                   "_conds": [[(("var", "VAR_RESULT", "eq", v), "gender")]]} for i, v in ((1, v1), (2, v2))]
            ei.link_fixed_choosers(gs)
            return [g["exclusive_with"] for g in gs]
        self.assertEqual(fixed("MALE", "FEMALE"), [["G2:1"], ["G1:1"]])  # CONTROL
        self.assertEqual(fixed("MALE", "MALE"), [[], []])                 # FAULT side: one value, no alternative
        # FAULT: F-tents, EXCLUSIVE_CITED emptied: the End's Red Tent keeps only its menu sibling
        self.assertEqual(gift(s2_faulted(), "Route110_TrickHouseEnd_EventScript_GiveRedTent")["exclusive_with"],
                         ["Route110_TrickHouseEnd_EventScript_GiveBlueTent:1"])

    def test_r2_6_no_fall_after_a_jump(self):
        """F2-6: a label whose last command never continues (NEVER_CONTINUES, each cited to src/scrcmd.c) does not fall
        into the next label (round 1: 5 phantom edges out of trainer_battle.inc's gotopostbattlescript); the scrolling
        menu is a menu producer (the Glass Workshop's choice)."""
        g = s2()[1]["graph"]
        enders = [s for s, outs in g.edges.items() for t, k, *_ in outs if k == "fall" and g.labels[s]["body"]
                  and ei.cmd(g.labels[s]["body"][-1][1])[0] in ei.NEVER_CONTINUES]
        self.assertEqual(enders, [])
        self.assertTrue(set(ei.NEVER_CONTINUES) <= set(ei.TERMINATORS))
        self.assertEqual(gift(s2()[0], "Route113_GlassWorkshop_EventScript_GiveGlassFlute")["what"]["chosen_by"],
                         "choice")
        text = "A::\n\tgotopostbattlescript\nB::\n\tgiveitem ITEM_POTION\n\tend\n"
        falls = lambda gr: [t for t, k, *_ in gr.edges["A"] if k == "fall"]  # noqa: E731
        self.assertEqual(falls(fake_graph(text)), [])                       # CONTROL
        # FAULT: the round-1 phantom edge. Since stage 2b fix round 1, falls_through also stops at the FIRST
        # NEVER_CONTINUES command, so the fault takes gotopostbattlescript out of BOTH lists (TERMINATORS is built from
        # NEVER_CONTINUES at import)
        with Swap(ei, "TERMINATORS", tuple(x for x in ei.TERMINATORS if x != "gotopostbattlescript")), \
                Swap(ei, "NEVER_CONTINUES", {k: v for k, v in ei.NEVER_CONTINUES.items() if k != "gotopostbattlescript"}):
            self.assertEqual(falls(fake_graph(text)), ["B"])

    def test_r2_7_verifier_rules_a5_a8(self):
        """F2-7: the verifier's rules a5-a8 each report their own plant on one line, and turning a rule's function off
        silences exactly that plant (a5, a6 live in s2_rules_round2; a8 in s2_gender)."""
        for name in ("a5", "a6", "a7", "a8"):
            self.assertTrue(plant_ok(name), name)                           # CONTROL
        with Swap(vw, "s2_gender", lambda *a: None):
            self.assertFalse(plant_ok("a8"))                                # FAULT: the gender rule off
            self.assertTrue(plant_ok("a5"))
        with Swap(vw, "s2_rules_round2", lambda *a, **k: None):
            self.assertEqual([plant_ok(n) for n in ("a5", "a6", "a8")], [False, False, True])

    # ---------------------------------------------------------------- fix-spec-3
    def test_r3_1_sole_writer(self):
        """S3-1: `once` / `until_received` only when the blocking flag/var has NO writer anywhere but the gift's own
        continuation; a cited REARM entry decides `daily` (the 8 Shoal Cave gifts, src/clock.c:53 ->
        src/field_specials.c:1420 -> ShoalCave_LowTideEntranceRoom:22, :82-90); any other writer -> `unknown`. The
        round-2 'spent' shortcut (one_shot) is gone."""
        obj = s2()[0]
        shoal = [g for g in obj["gifts"] if g["id"].startswith(("ShoalCave_LowTideInnerRoom_EventScript_Shoal",
                                                                 "ShoalCave_LowTideStairsRoom_EventScript_Shoal",
                                                                 "ShoalCave_LowTideLowerRoom_EventScript_Shoal"))]
        self.assertEqual(len(shoal), 8)
        for g in shoal:
            self.assertEqual(g["repeat"], "daily", g["id"])
            self.assertIn("src/clock.c:53", [r["ref"] for r in g["dev"]["rearm"]], g["id"])
            self.assertIn("Shell Bell man", g["when"], g["id"])
        lobby = gift(obj, "LilycoveCity_ContestLobby_EventScript_GiveLuxuryBallAtCounter")
        self.assertEqual((lobby["repeat"], lobby["dev"]["other_writers"]),
                         ("unknown", ["VAR_CONTEST_PRIZE_PICKUP: setvar at data/scripts/contest_hall.inc:1105"]))
        exp = gift(obj, "RustboroCity_DevonCorp_3F_EventScript_GiveExpShare")
        self.assertEqual(exp["dev"]["c_uses"],
                         ["FLAG_RECEIVED_EXP_SHARE named by C code at src/pokenav_match_call_data.c:183"])
        self.assertNotIn("written by", exp["dev"]["repeat_why"])
        self.assertFalse(hasattr(ei, "one_shot"))
        # the sole-writer rule's hand tables are cited like every other (check_cites holds each token at the pin)
        cited = {e for e, _, _ in ei.table_cites()}
        want = ({"WRITER_CMDS " + k for k in ei.WRITER_CMDS} | {"REARM " + k for k in ei.REARM} |
                {"C_RANGES " + r[0] for r in ei.C_RANGES} | {"CITED_READS " + k for k in ei.CITED_READS} |
                {"REMOVEOBJECT_SETS", "TRAINER_FLAG_SET", "TRAINER_FLAG_CLEAR", "TEMP_CLEAR"})
        self.assertEqual(want - cited, set())
        for g in obj["gifts"]:  # every asserted once / until_received names what blocks it
            if g["repeat"] in ("once", "until_received"):
                self.assertTrue(g["dev"].get("blocked_by"), g["id"])
                self.assertNotIn("other_writers", g["dev"], g["id"])
        fly = gift(obj, "Route119_EventScript_GiveFlyHM")
        self.assertEqual((fly["repeat"], fly["dev"]["blocked_by"]),
                         ("once", ["VAR_ROUTE119_STATE = set 1 (data/maps/Route119/scripts.inc:144)"]))
        bad = s2_faulted()
        # FAULT: F-rearm, no REARM entry: the Shoal salt is `unknown` (its clearflag at :82 is an outside writer),
        # never round 2's until_received
        salt = gift(bad, "ShoalCave_LowTideInnerRoom_EventScript_ShoalSalt1")
        self.assertEqual(salt["repeat"], "unknown")
        self.assertIn("FLAG_RECEIVED_SHOAL_SALT_1: clearflag at data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:82",
                      salt["dev"]["other_writers"])
        # FAULT: F-writer, a second writer of HM Fly's blocking var (MtChimney:100): no longer sole, so `unknown`
        fly = gift(bad, "Route119_EventScript_GiveFlyHM")
        self.assertEqual(fly["repeat"], "unknown")
        self.assertIn("VAR_ROUTE119_STATE: setvar at data/maps/MtChimney/scripts.inc:100", fly["dev"]["other_writers"])

    def test_r3_2_once_guard_holds_at_start(self):
        """S3-2: a test on a value the gift writes is its once-guard only if it HOLDS at new game (flag clear, var 0).
        The lottery's owed prize, `goto_if_ne VAR_POKELOT_PRIZE_ITEM, ITEM_NONE` (LilycoveCity_DepartmentStore_1F
        /scripts.inc:12), fails at 0 = ITEM_NONE: a precondition, so the record is not 'no condition'."""
        prize = gift(s2()[0], "LilycoveCity_DepartmentStore_1F_EventScript_GivePrizeFromEarlier")
        self.assertEqual((prize["when"], prize["dev"]["tests"]), (None, ["VAR_POKELOT_PRIZE_ITEM ne ITEM_NONE"]))
        ctx = Ctx()
        owed = ("var", "VAR_POKELOT_PRIZE_ITEM", "ne", "ITEM_NONE")
        self.assertIs(ei.holds_at_start(owed, ctx), False)
        self.assertIs(ei.holds_at_start(("var", "V", "lt", "6"), ctx), True)
        self.assertIs(ei.holds_at_start(("flag", "FLAG_RECEIVED_TM_RETURN", False), ctx), True)
        hidden = sorted(ctx.hidden0)[0]
        self.assertIs(ei.holds_at_start(("flag", hidden, False), ctx), False)  # set at new game: unset fails
        info = {"own_values": ["ITEM_NONE"]}
        self.assertFalse(ei.is_once_guard(owed, "VAR_POKELOT_PRIZE_ITEM", info, ctx))  # CONTROL: kept as a condition
        with Swap(ei, "holds_at_start", lambda c, ctx=None: True):
            self.assertTrue(ei.is_once_guard(owed, "VAR_POKELOT_PRIZE_ITEM", info, ctx))  # FAULT: round 2 dropped it

    def test_r3_3_specials_enforced(self):
        """S3-3: an untabled special on the way in makes `when` null and forbids the open-path `repeatable` (unless a
        cited REARM entry re-arms the record: the Contest Hall); QuizLadyRecordCustomQuizData is a writer
        (src/lilycove_lady.c:553-554 stores the player's ID, read at :383), not inert."""
        obj = s2()[0]
        for g in obj["gifts"]:
            if g["dev"].get("untabled_specials_on_the_way"):
                self.assertIsNone(g["when"], g["id"])
                self.assertTrue(g["repeat"] != "repeatable" or g["id"] == "ContestHall_EventScript_GiveLuxuryBall:1",
                                g["id"])
        self.assertEqual(gift(obj, "SlateportCity_EventScript_TryBuyBerryPowderItem")["repeat"], "unknown")
        self.assertEqual(ei.SPECIAL_EFFECTS["QuizLadyRecordCustomQuizData"][:3],
                         ("writes", "STATE_QUIZ_AUTHOR", "QUIZ_AUTHOR_PLAYER"))
        bad = s2_faulted()
        # FAULT: F-seedot, CompareSeedotSize untabled on Big Seedot's way in: `when` null, no repeatable
        seedot = gift(bad, "SootopolisCity_LotadAndSeedotHouse_EventScript_BigSeedot")
        self.assertEqual((seedot["when"], seedot["dev"]["untabled_specials_on_the_way"]), (None, ["CompareSeedotSize"]))
        self.assertNotEqual(seedot["repeat"], "repeatable")
        self.assertEqual(gift(bad, "SootopolisCity_LotadAndSeedotHouse_EventScript_BigLotad")["repeat"],
                         "repeatable")  # CONTROL inside the faulted build: Lotad's special is still tabled

    def test_r3_4_favor_lady_solo(self):
        """S3-4: the Favor Lady's words say what solo play allows: ONE item (src/lilycove_lady.c:237), and only her
        single best item wins the prize (:250-251)."""
        when = gift(s2()[0], "LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize")["when"]
        self.assertTrue(favor_words_ok(when), when)                                # CONTROL
        self.assertFalse(favor_words_ok(FAVOR_ROUND2))                             # FAULT: round 2's 5-item words
        self.assertIn("src/lilycove_lady.c:237",
                      [c for c, _ in ei.SPECIALVAR_WORDS[("IsFavorLadyThresholdMet", "1")][1:]])

    def test_r3_5_latest_producer(self):
        """S3-5: VAR_RESULT is attributed to its LATEST producer. Cozmo's test at :17 reads the yes/no answer of the
        callee (`call_if_unset` / `call_if_set FLAG_TEMP_2` at :15-16, both ending in MSGBOX_YESNO, :30 / :34), not the
        checkitem at :8; his `when` names the Meteorite and his hidden start. The Quiz Lady's null is accepted."""
        obj, res = s2()
        g = res["graph"]
        lab = "FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite"
        self.assertEqual(gift(obj, lab)["when"], "the giver is not there at first: they appear later in the story; "
                                                 "needs 1 Meteorite")
        self.assertIsNone(gift(obj, "LilycoveCity_PokemonCenter_1F_EventScript_GivePrize")["when"])
        self.assertEqual(g.producer("FallarborTown_CozmosHouse_EventScript_ProfCozmo", 9, "VAR_RESULT"),
                         ("cmd", "checkitem", "ITEM_METEORITE", "1"))
        self.assertEqual(g.producer(lab, 17, "VAR_RESULT"), ("cmd", "yesno"))   # CONTROL
        with Swap(g, "callee_producer", lambda lab_, var: None):
            self.assertNotEqual(g.producer(lab, 17, "VAR_RESULT"), ("cmd", "yesno"))  # FAULT: the callee unread

    def test_r3_6_castform_behind_aqua(self):
        """S3-6: Castform's scientist stands behind Team Aqua until Shelly is beaten (Route119_WeatherInstitute_2F
        /scripts.inc:6, :12, :42, :60): a cited MAP_CONDITIONS entry, so `when` is null, never 'no condition'."""
        cast = gift(s2()[0], "Route119_WeatherInstitute_2F_EventScript_ReceiveCastform")
        self.assertIsNone(cast["when"])
        self.assertEqual(cast["dev"]["map_condition"]["refs"],
                         ["data/maps/Route119_WeatherInstitute_2F/scripts.inc:%d" % n for n in (6, 12, 42, 60)])
        bad = gift(s2_faulted(), "Route119_WeatherInstitute_2F_EventScript_ReceiveCastform")
        self.assertEqual(bad["when"], "no condition beyond `repeat`")  # FAULT: F-castform, round 2's answer
        self.assertNotIn("map_condition", bad["dev"])

    def test_r3_7_verifier_sole_writer_scan(self):
        """S3-7: the verifier's own whole-decomp scans: a7 (sole writer), a9 (a false-at-start precondition), a10 (an
        unread special), the daily re-arm (d3) and the golden `other_writer` (gw) each report their plant on one line
        and fall silent with their function off; S2_HAVE reads money / coins / decorations; S2_ROOMISH never counts a
        yes/no box as room; the golden list holds the five records fix-spec-3 names; S2_SPECIALS is load-bearing
        (without SetPacifidlogTMReceivedDay the two weekly Pacifidlog TMs are mismatches: stage 3a's VM4g arm)."""
        rep = vw.Report()
        vw.verify_items(ROOT, vw.load_items(str(WORLD)), vw.load(str(WORLD))["maps"], rep)
        self.assertEqual(rep.lines, [])                                              # CONTROL
        for name in ("a7s", "a9", "a10", "d3", "gw"):
            self.assertTrue(plant_ok(name), name)
        golden = {e.get("id") for e in vw.S2_GOLDEN}
        self.assertTrue({"ShoalCave_LowTideInnerRoom_EventScript_ShoalSalt1:1",
                         "LilycoveCity_DepartmentStore_1F_EventScript_GivePrizeFromEarlier:1",
                         "LilycoveCity_ContestLobby_EventScript_GiveLuxuryBallAtCounter:1",
                         "FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite:1",
                         "Route119_WeatherInstitute_2F_EventScript_ReceiveCastform:1"} <= golden)
        for ok in ("checkmoney 200", "checkcoins 1", "checkdecor DECOR_PRETTY_CHAIR", "checkitem ITEM_SCANNER, 1"):
            self.assertTrue(vw.S2_HAVE.match(ok), ok)
        for no in ("msgbox T, MSGBOX_YESNO", "yesnobox 20, 8"):
            self.assertFalse(vw.S2_ROOMISH.match(no), no)
        self.assertTrue(vw.S2_ROOMISH.match("checkitemspace ITEM_POTION, 1"))
        with Swap(vw, "s2_rules_round2", lambda *a, **k: None):                     # FAULT: a7 / a9 / a10 off
            self.assertEqual([plant_ok(n) for n in ("a7s", "a9", "a10")], [False, False, False])
        with Swap(vw, "s2_golden", lambda *a: None):                                # FAULT: the golden check off
            self.assertFalse(plant_ok("gw"))
        saved = vw.S2_SPECIALS.pop("SetPacifidlogTMReceivedDay")
        try:                                                                         # FAULT: VM4g
            rep = vw.Report()
            vw.verify_items(ROOT, vw.load_items(str(WORLD)), vw.load(str(WORLD))["maps"], rep)
        finally:
            vw.S2_SPECIALS["SetPacifidlogTMReceivedDay"] = saved
        self.assertEqual(len(rep.lines), 2, rep.lines)
        self.assertTrue(all("PacifidlogTown_House2" in ln and "runs after the gift" in ln for ln in rep.lines))

    # ---------------------------------------------------------------- stage 3b strengthening (the mutant run)
    def test_dev_evidence_pins(self):
        """The developer evidence behind `repeat` (dev.other_writers, c_uses, rearm, tests), pinned where a deleted
        call changes ONLY it (the first mutant run of stage 3b: E10, E11, E22, E48, E49, E51, E56, E59, E60 changed
        these and nothing AI-facing). A wrong why is how round 2's verifier found the Exp Share's untrue 'written by'."""
        obj = s2()[0]
        scarf = gift(obj, "SlateportCity_PokemonFanClub_EventScript_GiveRedScarf")["dev"]
        self.assertEqual(scarf["other_writers"][0],  # the implied call_if test makes its own flag a blocker (E10)
                         "FLAG_RECEIVED_RED_SCARF: setflag at data/maps/SlateportCity_PokemonFanClub/scripts.inc:76")
        self.assertEqual(scarf["c_uses"], ["VAR_TEMP_1 named by C code at src/field_tasks.c:114",  # aliases (E51)
                                           "VAR_TEMP_1 named by C code at src/record_mixing.c:975",
                                           "VAR_TEMP_1 named by C code at src/record_mixing.c:982"])
        self.assertEqual(gift(obj, "DewfordTown_Gym_EventScript_GiveBulkUp")["dev"]["other_writers"],  # E11
                         ["TRAINER:TRAINER_BRAWLY_1: not a flag or var name, so no whole-decomp scan can re-check it"])
        self.assertEqual(gift(obj, "MauvilleCity_BikeShop_EventScript_GetMachBike")["dev"]["tests"],
                         ["VAR_RESULT eq FALSE"])  # norm (E22)
        berry = gift(obj, "LilycoveCity_EventScript_BerryGentleman")["dev"]  # the daily C range decides (E48, E49, E56)
        self.assertEqual((berry["rearm"], berry.get("blocked_by")),
                         ([{"ref": "src/event_data.c:52", "writes": "FLAG_DAILY_LILYCOVE_RECEIVED_BERRY"}], None))
        self.assertEqual(gift(obj, "LilycoveCity_DepartmentStore_1F_EventScript_LotteryClerk")["dev"]["other_writers"],
                         ["FLAG_DAILY_PICKED_LOTO_TICKET: setflag at data/maps/LilycoveCity_DepartmentStore_1F"
                          "/scripts.inc:16", "FLAG_DAILY_PICKED_LOTO_TICKET: written by C (daily flags, "
                                             "src/event_data.c:52)"])  # ranges_of (E60)
        bad = copy.deepcopy(scarf)  # FAULT side of the pins: the same comparison over a changed list fails
        bad["other_writers"] = bad["other_writers"][1:]
        self.assertNotEqual(bad["other_writers"][0], scarf["other_writers"][0])

    def test_extractor_units(self):
        """Function-level FAULT / CONTROL arms for extractor calls whose deletion changes no record at the pin (the
        first mutant run's survivors): each arm runs the function on an input where the call decides."""
        g = s2()[1]["graph"]
        ctx = real_ctx()
        wi = ctx.writer_index()
        # E44: an ITEM: blocker is sole only when the item has ONE source (the Scanner), never the Potion
        self.assertEqual((ei.sole_writer(ctx, "ITEM:ITEM_POTION", set())["sole"],
                          ei.sole_writer(ctx, "ITEM:ITEM_SCANNER", set())["sole"]), (False, True))
        # E46 / E85: a CITED_READS entry (a C line read to be a pure read) takes that line out of the C mentions and
        # puts its cite into table_cites; CITED_READS is empty at the pin, so this plants one (the Exp Share's table)
        exp = gift(s2()[0], "RustboroCity_DevonCorp_3F_EventScript_GiveExpShare")
        lab, ln = exp["id"].rsplit(":", 1)[0], int(exp["ref"].rsplit(":", 1)[1])
        own = ei.continuation_refs(g, lab, ln)
        self.assertFalse(ei.sole_writer(ctx, "FLAG_RECEIVED_EXP_SHARE", own)["sole"])          # CONTROL
        read = {"FLAG_RECEIVED_EXP_SHARE": [("src/pokenav_match_call_data.c:183", "FLAG_RECEIVED_EXP_SHARE")]}
        with Swap(ei, "CITED_READS", read):
            self.assertTrue(ei.sole_writer(ctx, "FLAG_RECEIVED_EXP_SHARE", own)["sole"])       # the read is cited
            self.assertIn("CITED_READS FLAG_RECEIVED_EXP_SHARE", {e for e, _, _ in ei.table_cites()})
        # E54 / E55: removeobject writes the hide flag (VAR_LAST_TALKED: the talked-to giver; another var: any object)
        self.assertIn(("data/scripts/secret_power_tm.inc:55", "removeobject"),
                      wi.script["FLAG_HIDE_ROUTE_111_SECRET_POWER_MAN"])
        self.assertTrue(any(("data/scripts/players_house.inc:418", "removeobject") in v for v in wi.script.values()))
        # E57 / E58 / E56: the C ranges by prefix, by object and by id range
        self.assertIn("hidden item flags", [k for k, _, _ in wi.ranges_of("FLAG_HIDDEN_ITEM_ABANDONED_SHIP_RM_1_KEY")])
        self.assertIn("objects removed by C", [k for k, _, _ in wi.ranges_of("FLAG_HIDE_BIRTH_ISLAND_DEOXYS_TRIANGLE")])
        self.assertEqual(wi.ranges_of("FLAG_DAILY_APPRENTICE_LEAVES"),
                         [("daily flags", "daily", "src/event_data.c:52")])
        self.assertEqual(wi.aliases("FLAG_TEMP_1"), ["FLAG_TEMP_1", "FLAG_TEMP_SKIP_GABBY_INTERVIEW"])
        # E14 / E15b: a flag no script reads but C names is NOT inert; one nothing names is
        self.assertEqual((ctx.inert("FLAG_ADDED_MATCH_CALL_TO_POKENAV", set()), ctx.inert("FLAG_UNUSED_0x020", set())),
                         (False, True))
        # E64: blockers re-armed by DIFFERENT cited rules (one daily, one on every map entry) leave `repeat` unknown,
        # never one of them picked. No record at the pin has that shape, so sole_writer is stubbed on a real record
        # with two blockers (the Trick House End's Red Tent: its hide flag and VAR_TRICK_HOUSE_LEVEL)
        tent = gift(s2()[0], "Route110_TrickHouseEnd_EventScript_GiveRedTent")
        lab, ln = tent["id"].rsplit(":", 1)[0], int(tent["ref"].rsplit(":", 1)[1])

        def stub(decides):
            return lambda ctx_, s, own_: {"sole": False, "others": [], "c": [], "ranges": [], "words": None,
                                          "cites": ["x.inc:1"], "decides": decides(s)}
        with Swap(ei, "sole_writer", stub(lambda s: "daily")):                          # CONTROL: one rule decides
            self.assertEqual(ei.evidence(g, lab, ln, "giveitem", g.paths_to(lab, ln), ctx)["repeat"], "daily")
        with Swap(ei, "sole_writer", stub(lambda s: "daily" if s.startswith("FLAG_") else "repeatable")):
            out = ei.evidence(g, lab, ln, "giveitem", g.paths_to(lab, ln), ctx)
            self.assertEqual((out["repeat"], out["why"]), ("unknown", "its blocked paths are re-armed differently "
                                                                      "(daily, repeatable)"))
        # E35: an answer shaped by a loop cut is not memoised: asked again from outside the loop, a label's paths are
        # the same as on a fresh graph (a memoised cut answer would lack the way in through the loop's head)
        loop = ("R::\n\tgoto M\nM::\n\tgoto_if_eq VAR_X, 1, G\n\tgoto M2\nM2::\n\tgoto M\n"
                "G::\n\tgiveitem ITEM_POTION\n\tend\n")
        fresh = fake_graph(loop).paths_to("M2", 7)
        warm = fake_graph(loop)
        warm.paths_to("G", 9)
        self.assertEqual(warm.paths_to("M2", 7), fresh)
        self.assertTrue(fresh)
        # E74: a test on a non-own blocked var that FAILS at new game is no once-guard (it is a precondition)
        owed = ("var", "VAR_POKELOT_PRIZE_ITEM", "ne", "ITEM_NONE")
        self.assertFalse(ei.once_guard(owed, "x", {"VAR_POKELOT_PRIZE_ITEM": 0}, ctx.hidden0, None, ctx))
        self.assertTrue(ei.once_guard(("var", "VAR_POKELOT_PRIZE_ITEM", "lt", "1"), "x", {"VAR_POKELOT_PRIZE_ITEM": 0},
                                      ctx.hidden0, None, ctx))
        # E31: a test fed by one of two specials, one per way in (the Quiz Lady's question / answer screens,
        # lilycove_lady.inc:190 / :195), reads "one of them" (a synthetic copy of that shape)
        fg = fake_graph("R::\n\tgoto_if_eq VAR_0x8004, 0, S1\n\tgoto S2\nS1::\n\tspecial QuizLadyShowQuizQuestion\n"
                        "\tgoto C\nS2::\n\tspecial QuizLadyGetPlayerAnswer\n\tgoto C\nC::\n"
                        "\tgoto_if_eq VAR_RESULT, 1, D\n\tend\nD::\n\tend\n")
        self.assertEqual(fg.producer("C", 11, "VAR_RESULT"),
                         ("special", "QuizLadyGetPlayerAnswer|QuizLadyShowQuizQuestion"))
        # E75: a plain `call` hands on its callee's last producer (a yes/no box)
        fg = fake_graph("A::\n\tcall B\n\tgoto_if_eq VAR_RESULT, 1, C\n\tend\nB::\n\tmsgbox T, MSGBOX_YESNO\n\treturn\n"
                        "C::\n\tend\n")
        self.assertEqual(fg.producer("A", 3, "VAR_RESULT"), ("cmd", "yesno"))
        # E43: the gift's continuation runs on through a fall into the next label
        fg = fake_graph("A::\n\tgiveitem ITEM_POTION\nB::\n\tsetflag FLAG_X\n\tend\n")
        self.assertIn("x.inc:4", ei.continuation_refs(fg, "A", 2))
        # E05: a result writer after the gift ends the gift's own result: the test after it is not the gift's
        fg = fake_graph("A::\n\tgiveitem ITEM_POTION\n\tcheckitemspace ITEM_POTION, 1\n"
                        "\tgoto_if_eq VAR_RESULT, FALSE, B\n\tend\nB::\n\tend\n")
        self.assertEqual([w["fail"] for w in ei.gift_ways(fg, "A", 2, "giveitem", None)[0]], [False, False])
        fg = fake_graph("A::\n\tgiveitem ITEM_POTION\n\tgoto_if_eq VAR_RESULT, FALSE, B\n\tend\nB::\n\tend\n")
        self.assertEqual(sorted(w["fail"] for w in ei.gift_ways(fg, "A", 2, "giveitem", None)[0]), [False, True])

    def test_verifier_units(self):
        """Function-level and plant FAULT / CONTROL arms for verifier checks the 26 plants do not reach (the first
        mutant run's survivors): its own whole-decomp tables, s2_false_at_start, s2_cont's fall, the golden list's
        when_has / why_has, the table-cite call, and a7's ITEM: and non-name blockers."""
        s = vw.s2_raw(ROOT)
        t = vw.s2_sole_tables(s, ROOT)
        self.assertIn("data/maps/MtPyre_Exterior/scripts.inc:10", t["writers"]["VAR_TEMP_1"])            # V13
        self.assertIn("data/scripts/secret_power_tm.inc:55", t["writers"]["FLAG_HIDE_ROUTE_111_SECRET_POWER_MAN"])  # V14
        self.assertEqual(vw.s2_names_of(t, "FLAG_TEMP_1"), ["FLAG_TEMP_1", "FLAG_TEMP_SKIP_GABBY_INTERVIEW"])  # V17
        self.assertIn("FLAG_DAILY_APPRENTICE_LEAVES", t["daily"])                                            # V18
        self.assertIn("FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_POKEBALL_CYNDAQUIL", t["start"])                 # V19
        self.assertEqual(vw.s2_outside_writers(s, ROOT, "FLAG_RECEIVED_EXP_SHARE", set()),            # V20
                         ["script data/maps/RustboroCity_DevonCorp_3F/scripts.inc:162",
                          "C src/pokenav_match_call_data.c:183"])
        self.assertIn("C range daily flags (src/event_data.c:52)",                                          # V21, V22
                      vw.s2_outside_writers(s, ROOT, "FLAG_DAILY_APPRENTICE_LEAVES", set()))
        self.assertIn("C range objects removed by C (src/field_effect.c:3734)",                             # V23
                      vw.s2_outside_writers(s, ROOT, "FLAG_HIDE_BIRTH_ISLAND_DEOXYS_TRIANGLE", set()))
        self.assertIn("MAP_PETALBURG_CITY hidden", vw.s2_item_sources(s, ROOT, "ITEM_RARE_CANDY"))      # V24
        fs = lambda c: vw.s2_false_at_start(s, ROOT, c)  # noqa: E731
        self.assertIs(fs(("object", "FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_POKEBALL_CYNDAQUIL", True, "o")), True)  # V25
        self.assertIs(fs(("goto_if_set FLAG_RECEIVED_TM_RETURN, L", "FLAG_RECEIVED_TM_RETURN", True, "w")), True)  # V26
        self.assertIs(fs(("goto_if_eq VAR_X, 0, L", "VAR_X", False, "w")), True)                           # V27
        self.assertIs(fs(("goto_if_eq VAR_X, 0, L", "VAR_X", True, "w")), False)
        self.assertIs(fs(("map_script_2 VAR_X, 1, L", "VAR_X", True, "w")), True)                          # V28
        # V30: the Quiz Lady's prize runs off its label into the next one: s2_cont follows the fall
        name = "LilycoveCity_PokemonCenter_1F_EventScript_GivePrize"
        n = int(gift(s2()[0], name)["ref"].rsplit(":", 1)[1])
        full = vw.s2_cont(s, name, n)
        saved = s["fwd"]
        try:
            s["fwd"] = {k: [(w, m) for w, m in v if m != 10 ** 9] for k, v in saved.items()}
            self.assertLess(len(vw.s2_cont(s, name, n)), len(full))  # FAULT: no fall, fewer lines
        finally:
            s["fwd"] = saved

        def lines_for(change):
            items = vw.load_items(str(WORLD))
            change({g["id"]: g for g in items["gifts"]})
            rep = vw.Report()
            vw.verify_items(ROOT, items, vw.load(str(WORLD))["maps"], rep)
            return rep.lines

        def tooth_when(gs):
            gs["SlateportCity_Harbor_EventScript_DeepSeaTooth:1"]["when"] = "after badge 7"
        self.assertTrue(any("lacks 'Scanner'" in ln for ln in lines_for(tooth_when)))                      # V41

        def tomb_why(gs):
            gs["RustboroCity_Gym_EventScript_GiveRockTomb:1"]["dev"]["repeat_why"] = "x"
        self.assertTrue(any("dev.repeat_why 'x' lacks" in ln for ln in lines_for(tomb_why)))               # V34

        def item_blocker(gs):  # V03: an ITEM: blocker with many sources
            gs["MauvilleCity_House2_EventScript_AcceptTrade:1"]["dev"]["blocked_by"] = ["ITEM:ITEM_POTION = sub 1 (x)"]
        self.assertTrue(any("ITEM:ITEM_POTION has" in ln and "sources" in ln for ln in lines_for(item_blocker)))

        def trainer_blocker(gs):  # V05: a blocker that is no flag or var
            gs["MauvilleCity_House2_EventScript_AcceptTrade:1"]["dev"]["blocked_by"] = ["TRAINER:TRAINER_ROXANNE_1 = x"]
        self.assertTrue(any("is no flag or var a scan can check" in ln for ln in lines_for(trainer_blocker)))
        saved = vw.S2_SPECIALS["ShakeCamera"]
        try:                                                                                                # V35
            vw.S2_SPECIALS["ShakeCamera"] = ("src/field_specials.c:1471", saved[1])
            self.assertTrue(any("table S2_SPECIALS ShakeCamera" in ln for ln in lines_for(lambda gs: None)))
        finally:
            vw.S2_SPECIALS["ShakeCamera"] = saved

    def test_johto_starter_giver_hidden(self):
        """Round 2's M11: a Johto starter ball's `when` is 'the giver is not there at first' (its ball is hidden at new
        game, data/scripts/new_game.inc), and its own var's `lt 6` test (LittlerootTown_ProfessorBirchsLab
        /scripts.inc:287, flipped by :363 `setvar VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 6`) is the once-guard, dropped
        from dev.tests. That decision needs the gift's own written values (own_writes): without them it is kept."""
        obj = s2()[0]
        for mon in ("CYNDAQUIL", "TOTODILE", "CHIKORITA"):
            g = gift(obj, "LittlerootTown_ProfessorBirchsLab_EventScript_Give%s" % mon.capitalize())
            self.assertEqual((g["when"], g["dev"]["tests"], g["dev"]["own"]),
                             ("the giver is not there at first: they appear later in the story",
                              ["FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_POKEBALL_%s unset" % mon],
                              "VAR_DEX_UPGRADE_JOHTO_STARTER_STATE"), mon)
        ctx, own = Ctx(), "VAR_DEX_UPGRADE_JOHTO_STARTER_STATE"
        guard = ("var", own, "lt", "6")
        self.assertTrue(ei.is_once_guard(guard, own, {"own_values": ["6"]}, ctx))   # CONTROL
        self.assertFalse(ei.is_once_guard(guard, own, {}, ctx))                    # FAULT: no own values (M11)


# ---------------------------------------------------------------- slice 2, stage 2b: events.json
Refused = xe.Refused
_EVB = {}


def ev_build():
    """(the FRESH events object, the build's parts) at the pin, built once per process (about 50 s: entry_tests walks
    every known path into 2278 labels). The semantic tests read THIS, never the committed file, so an extractor change
    is judged by what it builds now; only S2bOutputTests compares it with the committed bytes."""
    if not _EVB:
        _EVB["obj"], _EVB["res"] = xe.build_all(ew.Decomp(ROOT), str(WORLD / "maps.json"))
    return _EVB["obj"], _EVB["res"]


def ev_copy():
    return json.loads(json.dumps(ev_build()[0]))


def ev_by(obj):
    return {r["label"]: r for r in obj["labels"]}


def ev_stub_tests(g, name):
    """entry_tests stubbed (no path walk): a guard's FAULT build reaches its guard in seconds, not 50 s. Used ONLY by
    builds whose assertions never read dev.tests."""
    return {"tests": [], "paths": 0, "paths_known": 0, "collapsed": False}


def ev_fast(d=None, maps_path=None):
    with Swap(xe, "entry_tests", ev_stub_tests):
        return xe.build_all(d or ew.Decomp(ROOT), maps_path or str(WORLD / "maps.json"))


_EVF = {}
#: the overlay of ev_faulted: an op line planted after Route 103's RivalEnd `end` (:139), with no label between
EV_DEAD_OLD = "\treleaseall\n\tend\n\nRoute103_Movement_RivalExitFacingNorth1:"
EV_DEAD_NEW = "\treleaseall\n\tend\n\tsetflag FLAG_DEFEATED_RIVAL_ROUTE103\n\nRoute103_Movement_RivalExitFacingNorth1:"


def ev_faulted():
    """ONE fast build over an overlay that plants `setflag FLAG_DEFEATED_RIVAL_ROUTE103` right after RivalEnd's `end`
    (data/maps/Route103/scripts.inc:139, so the new line is :140). It must be listed in `dead` with its line and never
    kept as a change. WHY a planted input: no label at the pin has an op line after a stop (0 such lines), so without
    it the dead-lines loop and live_body's stop could be deleted with no record changing."""
    if not _EVF:
        rel = "data/maps/Route103/scripts.inc"
        text = raw_text(rel)
        assert text.count(EV_DEAD_OLD) == 1, "Route 103's RivalEnd lines moved"
        _EVF["obj"], _ = ev_fast(OverlayDecomp(ROOT, {rel: text.replace(EV_DEAD_OLD, EV_DEAD_NEW)}))
    return _EVF["obj"]


def ev_target(c):
    """What a change acts on, read by the TEST (not the verifier's ev_out_ops): the flag, var, special, map or trainer."""
    d = c["dev"]
    if c["op"] in ("setflag", "clearflag"):
        return (d.get("flags") or [None])[0]
    if c["op"] in ("setvar", "addvar", "subvar", "copyvar"):
        return (d.get("vars") or [None])[0]
    if c["op"] == "special":
        return c.get("name")
    if c["op"] == "warp":
        return c.get("map")
    return c.get("trainer")


def ev_has(by, lab, mp, op, target, line, value=None, conditional=None):
    """A change (op, target) at line `line` of label `lab` (any label when None) on map `mp`, with the value and the
    certainty asked for (None = not asked)."""
    recs = [by[lab]] if lab in by else ([] if lab else list(by.values()))
    return any(mp in r["maps"] and c["op"] == op and ev_target(c) == target and
               c["dev"].get("ref", "").endswith(":%d" % line) and
               (value is None or c["dev"].get("value") == value) and
               (conditional is None or c.get("conditional") is conditional)
               for r in recs for c in r["changes"])


def ev_trig(by, lab):
    return (by.get(lab) or {}).get("trigger") or []


#: W7 row 11's rival battles: May / Brendan x the three starters, on Route 104 and in Rustboro (12 labels)
EV_RIVAL_LABELS = ["%s_EventScript_Battle%s%s" % (pre, who, mon) for pre in ("Route104", "RustboroCity")
                   for who in ("May", "Brendan") for mon in ("Treecko", "Torchic", "Mudkip")]
#: W7 row 6's four `addvar VAR_PETALBURG_GYM_STATE, 1` lines (one per badge that counts), cited by GATE_WORDS
EV_GYM_ADDVARS = (("MAP_RUSTBORO_CITY_GYM", "RustboroCity_Gym", 21), ("MAP_DEWFORD_TOWN_GYM", "DewfordTown_Gym", 152),
                  ("MAP_MAUVILLE_CITY_GYM", "MauvilleCity_Gym", 95), ("MAP_LAVARIDGE_TOWN_GYM_1F", "LavaridgeTown_Gym_1F", 63))


def ev_w7(obj):
    """W7's events.json facts as failures ('row N: ...'; [] when all hold), each findable by MAP and LABEL with the
    values recon-data Q7 cites. The spec names "rows 1, 4-12, 14, 15" and "13 facts": that list is TWELVE rows; the
    thirteenth is row 3, which Q7 itself assigns to events.json (`special ChooseStarter`, Route101/scripts.inc:223).
    Rows 2, 13 and 16-20 are not events.json facts (Q7 gives them to C, slice 1 or items_gifts.json)."""
    by = ev_by(obj)
    gates = {g["label"]: g for g in obj["gates"]}
    bad = []

    def need(row, ok, what):
        if not ok:
            bad.append("row %d: %s" % (row, what))
    lab_map, lab = "MAP_LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "LittlerootTown_ProfessorBirchsLab_EventScript_%s"
    # 1 the Route 103 rival battle's end (Route103/scripts.inc:131-134), every change certain
    for op, t, n, v in (("setvar", "VAR_BIRCH_LAB_STATE", 131, "4"), ("setflag", "FLAG_DEFEATED_RIVAL_ROUTE103", 133, None),
                        ("setvar", "VAR_OLDALE_RIVAL_STATE", 134, "1")):
        need(1, ev_has(by, "Route103_EventScript_RivalEnd", "MAP_ROUTE103", op, t, n, v, False), "RivalEnd %s %s" % (op, t))
    # 3 the starter is chosen by talking to Birch's bag on Route 101 (:223 special ChooseStarter)
    need(3, ev_has(by, "Route101_EventScript_BirchsBag", "MAP_ROUTE101", "special", "ChooseStarter", 223) and
         any(t["kind"] == "talk" for t in ev_trig(by, "Route101_EventScript_BirchsBag")), "BirchsBag ChooseStarter")
    # 4 Oldale's west exit: a WORDED steer gate on VAR_OLDALE_TOWN_STATE; the lab's writes that open it (:510, :511);
    # Oldale's own setter (:15), reached only when FLAG_ADVENTURE_STARTED is set (:10)
    g = gates.get("OldaleTown_EventScript_BlockedPath") or {}
    need(4, g.get("maps") == ["MAP_OLDALE_TOWN"] and g.get("kind") == "steer" and "Pokedex" in (g.get("when") or "") and
         (g.get("dev") or {}).get("vars") == ["VAR_OLDALE_TOWN_STATE"], "the Oldale west gate %r" % g.get("when"))
    need(4, ev_has(by, lab % "GivePokedex", lab_map, "setflag", "FLAG_ADVENTURE_STARTED", 510) and
         ev_has(by, lab % "GivePokedex", lab_map, "setvar", "VAR_OLDALE_TOWN_STATE", 511, "1"), "the lab opens it")
    need(4, ev_has(by, "OldaleTown_EventScript_SetOldaleState", "MAP_OLDALE_TOWN", "setvar", "VAR_OLDALE_TOWN_STATE",
                   15, "1") and any((t.get("dev") or {}).get("test") == "FLAG_ADVENTURE_STARTED set"
                                    for t in ev_trig(by, "OldaleTown_EventScript_SetOldaleState")), "Oldale's setter")
    # 5 the Pokedex flag (lab :537)
    need(5, ev_has(by, lab % "ReceivePokedex", lab_map, "setflag", "FLAG_SYS_POKEDEX_GET", 537, None, False), "Pokedex")
    # 6 Petalburg Gym's Speed / Accuracy doors: worded, locked on VAR_PETALBURG_GYM_STATE lt 6; +1 per counted badge
    for door in ("SpeedRoomDoor", "AccuracyRoomDoor"):
        g = gates.get("PetalburgCity_Gym_EventScript_" + door) or {}
        need(6, g.get("maps") == ["MAP_PETALBURG_CITY_GYM"] and g.get("kind") == "locked" and
             "four badges" in (g.get("when") or "") and
             (g.get("dev") or {}).get("tests") == ["VAR_PETALBURG_GYM_STATE lt 6"], "the %s gate" % door)
    for mp, folder, n in EV_GYM_ADDVARS:
        need(6, any(ev_has(by, r["label"], mp, "addvar", "VAR_PETALBURG_GYM_STATE", n, "1") for r in obj["labels"]
                    if r["ref"].startswith("data/maps/%s/" % folder)), "%s addvar :%d" % (folder, n))
    # 7 a scripted warp: the Wally tutorial moves you into the Gym (:52); the three warp commands the recon counted
    wally = "PetalburgCity_EventScript_WallyTutorial"
    need(7, ev_has(by, wally, "MAP_PETALBURG_CITY", "warp", "MAP_PETALBURG_CITY_GYM", 52) and
         any(c["op"] == "warp" and "PetalburgCity_Gym" in (c.get("effect") or "") for c in by.get(wally, {}).get(
             "changes", [])), "the Wally tutorial's warp")
    cmds = {c["dev"].get("cmd") for r in obj["labels"] for c in r["changes"] if c["op"] == "warp"}
    need(7, {"warp", "warpdoor", "warpsilent"} <= cmds, "warp commands %s" % sorted(c for c in cmds if c))
    # 8 the tutorial battle is a special (:40)
    need(8, ev_has(by, wally, "MAP_PETALBURG_CITY", "special", "StartWallyTutorialBattle", 40), "Wally's battle")
    # 9 the four Petalburg steer triggers, worded
    for i in range(4):
        g = gates.get("PetalburgCity_EventScript_ShowGymToPlayer%d" % i) or {}
        need(9, g.get("maps") == ["MAP_PETALBURG_CITY"] and g.get("kind") == "steer" and g.get("when"),
             "ShowGymToPlayer%d" % i)
    # 10 the Petalburg Woods grunt: two coord triggers on VAR_PETALBURG_WOODS_STATE, the battle (:23 / :51), its end (:92)
    for side, n in (("Left", 23), ("Right", 51)):
        lb = "PetalburgWoods_EventScript_DevonResearcher" + side
        need(10, ev_has(by, lb, "MAP_PETALBURG_WOODS", "trainerbattle", "TRAINER_GRUNT_PETALBURG_WOODS", n) and
             any(t["kind"] == "coord" and (t.get("dev") or {}).get("vars") == ["VAR_PETALBURG_WOODS_STATE"]
                 for t in ev_trig(by, lb)), "the grunt (%s)" % side)
    need(10, ev_has(by, "PetalburgWoods_EventScript_RemoveDevonResearcher", "MAP_PETALBURG_WOODS", "setvar",
                    "VAR_PETALBURG_WOODS_STATE", 92, "1"), "RemoveDevonResearcher")
    # 11 the rival battles are optional: a YES answer two labels up is on every known path (dev.tests)
    for lb in EV_RIVAL_LABELS:
        r = by.get(lb) or {}
        need(11, ("MAP_ROUTE104" if lb.startswith("Route104") else "MAP_RUSTBORO_CITY") in r.get("maps", []) and
             any(c["op"] == "trainerbattle" for c in r.get("changes", [])) and
             "VAR_RESULT eq YES (answer)" in (r.get("dev") or {}).get("tests", []), lb)
    # 12 the rival's gating vars are set only after Devon Corp 3F (:68), then Rustboro (:33, :88)
    need(12, ev_has(by, "RustboroCity_DevonCorp_3F_EventScript_MeetPresident", "MAP_RUSTBORO_CITY_DEVON_CORP_3F", "setvar",
                    "VAR_RUSTBORO_CITY_STATE", 68, "6"), "MeetPresident")
    need(12, ev_has(by, "RustboroCity_EventScript_ScientistAddMatchCall", "MAP_RUSTBORO_CITY", "setvar",
                    "VAR_ROUTE104_STATE", 33, "1"), "ScientistAddMatchCall")
    need(12, ev_has(by, "RustboroCity_EventScript_MatchCallTutorial", "MAP_RUSTBORO_CITY", "setvar",
                    "VAR_RUSTBORO_CITY_STATE", 88, "7"), "MatchCallTutorial")
    # 14 the badge marks Roxanne's gym trainers beaten (set_gym_trainers.inc:14-16), in words naming each one
    for t, n in (("TRAINER_JOSH", 14), ("TRAINER_TOMMY", 15), ("TRAINER_MARC", 16)):
        sg = by.get("RustboroCity_Gym_SetGymTrainers") or {}
        need(14, ev_has(by, "RustboroCity_Gym_SetGymTrainers", "MAP_RUSTBORO_CITY_GYM", "settrainerflag", t, n) and
             any(ev_target(c) == t and t.split("_", 1)[1] in (c.get("effect") or "") and "beaten" in c["effect"]
                 for c in sg.get("changes", [])), t)
    # 15 Roxanne's defeat (RustboroCity_Gym/scripts.inc:18, :20, :21), certain, after her battle
    rox = "RustboroCity_Gym_EventScript_RoxanneDefeated"
    for op, t, n, v in (("setflag", "FLAG_DEFEATED_RUSTBORO_GYM", 18, None), ("setvar", "VAR_RUSTBORO_CITY_STATE", 20, "1"),
                        ("addvar", "VAR_PETALBURG_GYM_STATE", 21, "1")):
        need(15, ev_has(by, rox, "MAP_RUSTBORO_CITY_GYM", op, t, n, v, False), "RoxanneDefeated %s %s" % (op, t))
    need(15, any(t["kind"] == "battle" and t.get("trainer") == "TRAINER_ROXANNE_1" for t in ev_trig(by, rox)),
         "Roxanne's battle trigger")
    return bad


def ev_change(obj, lab, line):
    """The change of label `lab` at `line`; with lab None, the change whose ref is exactly `line` (a path:line)."""
    if lab is None:
        return next(c for r in obj["labels"] for c in r["changes"] if c["dev"]["ref"] == line)
    return next(c for c in ev_by(obj)[lab]["changes"] if c["dev"]["ref"].endswith(":%d" % line))


#: one FAULT per W7 row: (row, the change that breaks only that row's fact)
EV_W7_FAULTS = (
    (1, lambda o: ev_by(o)["Route103_EventScript_RivalEnd"]["changes"].pop(2)),
    (3, lambda o: ev_by(o)["Route101_EventScript_BirchsBag"].__setitem__("maps", ["MAP_ROUTE102"])),
    (4, lambda o: next(g for g in o["gates"] if g["label"] == "OldaleTown_EventScript_BlockedPath").__setitem__(
        "when", None)),
    (5, lambda o: o.__setitem__("labels", [r for r in o["labels"] if not r["label"].endswith("ReceivePokedex")])),
    (6, lambda o: ev_change(o, None, "data/maps/DewfordTown_Gym/scripts.inc:152")["dev"].__setitem__("value", "2")),
    (7, lambda o: ev_change(o, "PetalburgCity_EventScript_WallyTutorial", 52).__setitem__("effect", None)),
    (8, lambda o: ev_change(o, "PetalburgCity_EventScript_WallyTutorial", 40).__setitem__("name", "StartWallyBattle")),
    (9, lambda o: next(g for g in o["gates"] if g["label"] == "PetalburgCity_EventScript_ShowGymToPlayer2").__setitem__(
        "kind", "locked")),
    (10, lambda o: ev_by(o)["PetalburgWoods_EventScript_DevonResearcherRight"].__setitem__("trigger", [])),
    (11, lambda o: ev_by(o)["RustboroCity_EventScript_BattleBrendanMudkip"]["dev"]["tests"].remove(
        "VAR_RESULT eq YES (answer)")),
    (12, lambda o: ev_change(o, "RustboroCity_EventScript_MatchCallTutorial", 88)["dev"].__setitem__("value", "6")),
    (14, lambda o: ev_change(o, "RustboroCity_Gym_SetGymTrainers", 15).__setitem__("effect", None)),
    (15, lambda o: ev_change(o, "RustboroCity_Gym_EventScript_RoxanneDefeated", 18).__setitem__("conditional", True)),
)


class S2bOutputTests(unittest.TestCase):
    """--check: the committed file is byte-identical to a fresh extraction. A DETERMINISM check, not a replication, and
    the one class the mutant run leaves out (a byte comparison catches every output change, so it would hide which
    SEMANTIC test pins a value)."""

    def test_committed_equals_fresh(self):
        self.assertEqual((WORLD / xe.OUT_NAME).read_bytes(), serial(ev_build()[0]))
        bad = ev_copy()
        bad["gates"][0]["kind"] = "locked" if bad["gates"][0]["kind"] != "locked" else "steer"
        self.assertNotEqual((WORLD / xe.OUT_NAME).read_bytes(), serial(bad))


class S2bBuildTests(unittest.TestCase):
    """The FRESH build's content: the verifier's verdict on it, W7, R-4..R-7, the dead / excluded lists, the counts and
    the values no verifier rule reads. Each FAULT is a copy with one fact broken."""

    def test_fresh_build_passes_the_verifier(self):
        """The independent verifier over a FRESH extraction, not the committed file: a semantic check of the build itself
        (S2bOutputTests' byte comparison is only a determinism check)."""
        rep = vw.Report()
        vw.verify_events(ROOT, ev_build()[0], vw.load(str(WORLD)), rep)
        self.assertEqual(rep.lines, [])
        self.assertEqual((rep.counts.get("events_labels"), rep.counts.get("events_dead"), rep.counts.get("events_gates"),
                          rep.counts.get("events_matchcall")), (2300, 54, 32, 76))  # fix round 1: +22 Match Call labels
        bad = ev_copy()  # FAULT: the fresh build with one certain setflag dropped
        bad_rec = ev_by(bad)["Route103_EventScript_RivalEnd"]
        bad_rec["changes"] = [c for c in bad_rec["changes"] if c["op"] != "setflag"]
        rep = vw.Report()
        vw.verify_events(ROOT, bad, vw.load(str(WORLD)), rep)
        self.assertEqual(len(rep.lines), 1, rep.lines)
        self.assertTrue(rep.lines[0].startswith("MISMATCH events label Route103_EventScript_RivalEnd:"), rep.lines)

    def test_w7_acceptance(self):
        self.assertEqual(ev_w7(ev_build()[0]), [])
        for row, fault in EV_W7_FAULTS:
            bad = ev_copy()
            fault(bad)
            got = ev_w7(bad)
            self.assertTrue(got and all(x.startswith("row %d:" % row) for x in got), (row, got))

    def test_counts_re_measured(self):
        """Builder A's measured counts at the pin (2026-10-22 report), re-measured on the fresh build: the changes by op
        and how many are conditional, the trigger kinds with their dev evidence, the excluded groups, the dead split.
        FIX ROUND 1 moved these pins, each for a stated reason: the 76 register_matchcall lines are now `special` changes
        (special 1390 -> 1466, 54 of them conditional: 727 -> 781), 22 labels whose ONLY change is one became records
        (labels 2278 -> 2300; their 12 called triggers carry a flag test, 128 -> 140, and 10 are battles, 97 -> 107),
        and the 2 phantom `fall` triggers are gone (called with only a ref, 962 -> 960)."""
        import collections
        obj, res = ev_build()
        self.assertEqual(obj["_notes"]["counts"], {"labels": 2300, "changes": 3849, "conditional": 1447, "gates": 32,
                                                   "gates_worded": 20, "dead": 54})
        ch = [c for r in obj["labels"] for c in r["changes"]]
        self.assertEqual(dict(collections.Counter(c["op"] for c in ch)), {
            "special": 1466, "setflag": 806, "trainerbattle": 652, "setvar": 436, "clearflag": 237, "warp": 140,
            "settrainerflag": 57, "copyvar": 24, "addvar": 20, "subvar": 7, "cleartrainerflag": 4})
        self.assertEqual(dict(collections.Counter(c["op"] for c in ch if c["conditional"])), {
            "special": 781, "setflag": 298, "setvar": 141, "clearflag": 109, "warp": 81, "trainerbattle": 14,
            "copyvar": 10, "subvar": 7, "addvar": 6})
        self.assertTrue(all((c["conditional"] is True) == bool(c["dev"].get("after")) for c in ch))
        trig = collections.Counter((t["kind"], tuple(sorted((t.get("dev") or {})))) for r in obj["labels"]
                                   for t in r["trigger"])
        self.assertEqual(dict(trig), {
            ("called", ("ref", "test", "vars")): 1148, ("called", ("ref",)): 960, ("talk", ()): 715,
            ("map_script", ("ref", "test", "vars")): 251, ("talk", ("flags", "test")): 171,
            ("called", ("flags", "ref", "test")): 140, ("map_script", ("ref",)): 104, ("battle", ("ref",)): 107,
            ("C", ("ref",)): 65, ("sign", ()): 54, ("coord", ("test", "vars")): 51, ("coord", ("test",)): 1,
            ("called", ("ref", "test")): 1})
        self.assertEqual(dict(collections.Counter(t["map_script"] for r in obj["labels"] for t in r["trigger"]
                                                  if t["kind"] == "map_script")),
                         {"on_frame": 245, "on_transition": 80, "on_resume": 21, "on_warp_into_map": 6,
                          "on_return_to_field": 2, "on_load": 1})
        self.assertEqual([(x["what"], x["count"], x.get("by_command")) for x in obj["excluded"]], [
            ("writes to not a save flag (id past FLAGS_COUNT)", 1, {"setflag": 1}),
            ("writes to special flags (not saved)", 39, {"clearflag": 21, "setflag": 18}),
            ("writes to special vars (scratch registers, the script result included; not saved)", 1107,
             {"addvar": 52, "copyvar": 121, "setorcopyvar": 10, "setvar": 919, "subvar": 5}),
            ("writes to temp flags (cleared on every map entry)", 44, {"clearflag": 2, "setflag": 42}),
            ("writes to temp vars (cleared on every map entry)", 518, {"addvar": 32, "copyvar": 17, "setvar": 469}),
            ("mystery gift scripts (data/mystery_gift.s includes)", 19, None),
            ("the Eon Ticket distribution (record mixing)", 1, None)])
        self.assertEqual(sum(1 for r in obj["labels"] if r.get("reached_from") == "C"), 96)
        self.assertEqual(sum(1 for r in obj["labels"] if r["dev"]["paths_known"] == 0), 96)
        self.assertEqual(sum(1 for r in obj["labels"] if r["dev"]["collapsed"]), 54)
        self.assertLess(res["max_closure"] * 2, ei.MAX_CLOSURE, "the closure bound has lost its margin")
        bad = ev_copy()  # FAULT: the same counter over a copy with one change made conditional differs
        next(c for r in bad["labels"] for c in r["changes"] if not c["conditional"])["conditional"] = True
        self.assertNotEqual(sum(1 for r in bad["labels"] for c in r["changes"] if c["conditional"]), 1447)

    def test_values_no_rule_reads(self):
        """Values the verifier does not re-derive, pinned on records that hold them: each trigger kind's dev evidence,
        copyvar's source and the R-3 value, the facility battles' null trainer, warphole's null words, the trainer-flag
        words, the C-only records' C line, the pruned branch's dead why."""
        obj = ev_build()[0]
        by = ev_by(obj)
        self.assertEqual(ev_trig(by, "Route101_EventScript_BirchsBag")[0]["dev"]["flags"],
                         ["FLAG_HIDE_ROUTE_101_BIRCH_STARTERS_BAG"])                                    # talk + hide flag
        self.assertEqual(ev_trig(by, "PetalburgWoods_EventScript_DevonResearcherLeft")[0]["dev"],
                         {"test": "VAR_PETALBURG_WOODS_STATE eq 0", "vars": ["VAR_PETALBURG_WOODS_STATE"]})  # coord
        self.assertEqual(ev_trig(by, "EventScript_SetBrineyLocation_House")[0]["dev"]["flags"],
                         ["FLAG_HIDE_ROUTE_104_MR_BRINEY_BOAT"])                                        # called on a flag
        self.assertEqual(ev_trig(by, "Route104_EventScript_BattleMayTreecko")[0]["dev"]["vars"], ["VAR_STARTER_MON"])
        wt = ev_trig(by, "PetalburgCity_EventScript_WallyTutorial")[0]
        self.assertEqual((wt["kind"], wt["maps"], wt["dev"]["vars"]),
                         ("map_script", ["MAP_PETALBURG_CITY"], ["VAR_PETALBURG_CITY_STATE"]))
        self.assertEqual(by["OldaleTown_OnTransition"]["trigger"][0]["map_script"], "on_transition")
        cv = [c for r in obj["labels"] for c in r["changes"] if c["op"] == "copyvar"]
        self.assertEqual(sum(1 for c in cv if c["dev"].get("from") and c["dev"]["vars"][1:] == [c["dev"]["from"]]), 20)
        self.assertEqual(sorted(c["dev"]["ref"] for c in cv if c["dev"].get("value") == xe.COPYVAR_BUG), [
            "data/maps/LilycoveCity_LilycoveMuseum_2F/scripts.inc:78", "data/maps/SkyPillar_2F/scripts.inc:12",
            "data/maps/SkyPillar_4F/scripts.inc:12", "data/scripts/cave_hole.inc:9"])
        tb = [(r["label"], c["dev"]["why"]) for r in obj["labels"] for c in r["changes"]
              if c["op"] == "trainerbattle" and c["trainer"] is None]
        self.assertEqual([x for x, _ in tb], ["BattlePyramid_TrainerBattle", "TrainerHill_EventScript_TrainerBattle"])
        self.assertTrue(all(w.startswith("a facility battle") for _, w in tb))
        holes = [c for r in obj["labels"] for c in r["changes"] if c.get("dev", {}).get("cmd") == "warphole"]
        self.assertEqual([(c["map"], c["effect"]) for c in holes],
                         [("MAP_SOOTOPOLIS_CITY_GYM_B1F", None), ("MAP_UNDEFINED", None)])
        tf = [c for r in obj["labels"] for c in r["changes"] if c["op"] in ("settrainerflag", "cleartrainerflag")]
        self.assertTrue(all(c["effect"] == xe.EFFECT_WORDS[c["op"]][0].format(name=c["name"]) for c in tf))
        conly = by["EventScript_MoveMrBrineyToHouse"]
        self.assertEqual((conly["reached_from"], conly["maps"], conly["c_ref"][:4]), ("C", [], "src/"))
        why = next(x["why"] for x in obj["dead"] if x["label"] == "LilycoveCity_ContestLobby_EventScript_SetDebug")
        self.assertIn("IsContestDebugActive", why)
        self.assertEqual(sum(1 for r in obj["labels"] for c in r["changes"] if c["op"] == "warp" and c["effect"]),
                         EV_WORDED_WARPS)

    def test_rules_r4_to_r7(self):
        """R-4..R-7 over the WHOLE fresh output (CONTROL), and each rule broken on a one-record object (FAULT), refused
        by refuse_all and found by the verifier's own R-4 scan; the door to disk writes nothing it refuses."""
        obj = ev_build()[0]
        d = ew.Decomp(ROOT)
        defined = ei.defined_names(d)
        self.assertEqual(ei.dev_key_hits(obj), [])
        self.assertEqual(vw.s2_key_hits(obj), [])
        xe.refuse_all(obj, defined)
        rec = ev_by(obj)["Route103_EventScript_RivalEnd"]
        gate = next(g for g in obj["gates"] if g["label"] == "OldaleTown_EventScript_BlockedPath")

        def small(change, of=rec, key="labels"):
            o = {key: [copy.deepcopy(of)]}
            change(o[key][0])
            return o
        xe.refuse_all(small(lambda r: None), defined)  # CONTROL of the small shape
        for plant in ("flag", "flags", "var", "vars"):
            bad = small(lambda r: r["changes"][2].__setitem__(plant, "FLAG_DEFEATED_RIVAL_ROUTE103"))
            self.assertRaisesRegex(Refused, "R-4", xe.refuse_all, bad, defined)
            self.assertTrue(vw.s2_key_hits(bad), plant)
        bad = small(lambda g: g.__setitem__("when", "after FLAG_ADVENTURE_STARTED"), gate, "gates")
        self.assertRaisesRegex(Refused, "R-4", xe.refuse_all, bad, defined)
        bad = small(lambda r: r["changes"][2]["dev"]["flags"].append("FLAG_HIDE_FALLORBOR_POKEMON_CENTER_LANETTE"))
        self.assertRaisesRegex(Refused, "R-5", xe.refuse_all, bad, defined)
        for key, needle in (("x", "R-6"), ("route", "R-6"), ("iv", ""), ("aiFlags", "")):
            bad = small(lambda r: r["trigger"][0].__setitem__(key, 1))
            self.assertRaisesRegex(Refused, needle, xe.refuse_all, bad, defined)
            with tempfile.TemporaryDirectory() as tmp:
                self.assertRaises(Refused, xe.write_output, tmp, bad, d)
                self.assertFalse(os.path.exists(os.path.join(tmp, xe.OUT_NAME)))
        with tempfile.TemporaryDirectory() as tmp:  # CONTROL of the door: the real output goes through
            xe.write_output(tmp, obj, d)
            self.assertTrue(os.path.exists(os.path.join(tmp, xe.OUT_NAME)))

    def test_dead_and_excluded_are_named(self):
        obj = ev_build()[0]
        dead = {x["label"] for x in obj["dead"]}
        self.assertTrue({"MossdeepCity_Gym_EventScript_Switch1", "LilycoveCity_ContestLobby_EventScript_SetDebug",
                         "EventScript_CableClub_SetVarResult1"} <= dead, sorted(dead)[:10])
        self.assertTrue(all(x["why"] and x["ref"] for x in obj["dead"]))
        self.assertFalse(dead & {r["label"] for r in obj["labels"]})
        self.assertEqual([x["label"] for x in obj["excluded"][-1]["labels"]], ["CableClub_EventScript_DistributeEonTicket"])
        self.assertNotIn("CableClub_EventScript_DistributeEonTicket", {r["label"] for r in obj["labels"]})
        self.assertIn("data/scripts/gift_pichu.inc", obj["excluded"][-2]["files"])
        self.assertTrue(all(x["count"] > 0 and x["what"] and x["why"] for x in obj["excluded"]))
        bad = ev_copy()  # FAULT: one dead label left out is reported by the verifier
        bad["dead"] = [x for x in bad["dead"] if x["label"] != "EventScript_CableClub_SetVarResult1"]
        rep = vw.Report()
        vw.verify_events(ROOT, bad, vw.load(str(WORLD)), rep)
        self.assertTrue(any(ln.startswith("MISMATCH events dead:") for ln in rep.lines), rep.lines)

    def test_check_cli_compare(self):
        """main --check's comparison (exit 0 same, 1 different or missing), with `run` swapped for the cached build so
        the arm costs no second 50 s extraction. The CONTROL compares against a file written from the same object, so
        this tests the COMPARISON, not the committed file (that is S2bOutputTests' job)."""
        obj = ev_build()[0]
        d = ew.Decomp(ROOT)

        def fake_run(root, out, maps=None):
            xe.write_output(out, obj, d)
            return obj
        with Swap(xe, "run", fake_run), redirect_stdout(io.StringIO()), tempfile.TemporaryDirectory() as tmp:
            Path(tmp, xe.OUT_NAME).write_bytes(serial(obj))
            self.assertEqual(xe.main(["--check", "--out", tmp]), 0)
            bad = ev_copy()
            bad["gates"][0]["when"] = "x"
            Path(tmp, xe.OUT_NAME).write_bytes(serial(bad))
            self.assertEqual(xe.main(["--check", "--out", tmp]), 1)
            self.assertEqual(xe.main(["--check", "--out", os.path.join(tmp, "none")]), 1)


#: warps with words (a cited warp command whose map maps.json names); measured at the pin
EV_WORDED_WARPS = 138


def ev_moved(cite):
    """(path:line, token) with the line moved one down: a cite that no longer holds its token."""
    return (shift(cite[0], 1), cite[1])


class S2bGuardTests(unittest.TestCase):
    """Each guard of extract_events refuses its broken input (CONTROL: the real input passes), and each guard's CALL
    inside the build fires: the build is made over the broken input and must refuse with THAT guard's message (a later
    guard refusing the same input would hide a deleted call; 2a's first mutant round)."""

    def test_table_cites_each_table(self):
        d = ew.Decomp(ROOT)
        xe.check_cites(d)
        self.assertEqual({e.split(" ")[0] for e, _, _ in xe.table_cites()},
                         {"GATE_WORDS", "EFFECT_WORDS", "WARP_CMDS", "PERSIST_RANGES", "FLAGS_COUNT", "COPYVAR_BUG",
                          "PLACEHOLDER_BATTLES"})
        gw = dict(xe.GATE_WORDS)
        e = gw["OldaleTown_EventScript_BlockedPath"]
        gw["OldaleTown_EventScript_BlockedPath"] = (e[0], ev_moved(e[1])) + e[2:]
        ew_ = dict(xe.EFFECT_WORDS)
        ew_["settrainerflag"] = (ew_["settrainerflag"][0], ev_moved(ew_["settrainerflag"][1]))
        wc = dict(xe.WARP_CMDS)
        wc["warpdoor"] = ev_moved(wc["warpdoor"])
        pr = [list(x) for x in xe.PERSIST_RANGES]
        pr[2][4] = ev_moved(pr[2][4])
        ph = dict(xe.PLACEHOLDER_BATTLES)
        ph["TRAINER_BATTLE_HILL"] = ev_moved(ph["TRAINER_BATTLE_HILL"])
        for name, value, needle in (("GATE_WORDS", gw, "GATE_WORDS OldaleTown_EventScript_BlockedPath"),
                                    ("EFFECT_WORDS", ew_, "EFFECT_WORDS settrainerflag"),
                                    ("WARP_CMDS", wc, "WARP_CMDS warpdoor"),
                                    ("PERSIST_RANGES", [tuple(x) for x in pr], "PERSIST_RANGES temp vars"),
                                    ("FLAGS_COUNT_CITE", ev_moved(xe.FLAGS_COUNT_CITE), "FLAGS_COUNT"),
                                    ("COPYVAR_CITES", (ev_moved(xe.COPYVAR_CITES[0]),) + xe.COPYVAR_CITES[1:],
                                     "COPYVAR_BUG"),
                                    ("PLACEHOLDER_BATTLES", ph, "PLACEHOLDER_BATTLES TRAINER_BATTLE_HILL")):
            with Swap(xe, name, value):
                self.assertRaisesRegex(Refused, re.escape(needle), xe.check_cites, d)

    def test_gate_table_both_clauses(self):
        g = ev_build()[1]["graph"]
        cands = xe.gate_candidates(g, xe.Persist(g.d))
        xe.check_gate_table(cands)
        self.assertEqual({(c[0], c[1]) for c in cands}, {(x["label"], x["kind"]) for x in ev_build()[0]["gates"]})
        no_oldale = [c for c in cands if c[0] != "OldaleTown_EventScript_BlockedPath"]
        self.assertRaisesRegex(Refused, "OldaleTown_EventScript_BlockedPath", xe.check_gate_table, no_oldale)
        twice = cands + [c for c in cands if c[0] == "OldaleTown_EventScript_BlockedPath"]
        self.assertRaisesRegex(Refused, "OldaleTown_EventScript_BlockedPath", xe.check_gate_table, twice)

    def test_check_joins(self):
        obj = ev_build()[0]
        names = {t["symbol"]: t["name"] for t in OBJS["trainers.json"]["trainers"]}
        xe.check_joins(obj["labels"], names)
        names.pop("TRAINER_GRUNT_PETALBURG_WOODS")
        self.assertRaisesRegex(Refused, "TRAINER_GRUNT_PETALBURG_WOODS", xe.check_joins, obj["labels"], names)

    def test_build_refuses(self):
        """The guards' CALLS inside build / build_all, each over its broken input (fast builds: entry_tests stubbed)."""
        maps_path = str(WORLD / "maps.json")
        ev = raw_text("data/event_scripts.s")
        overlays = {
            "neither data/event_scripts.s nor": {
                "data/event_scripts.s": ev.replace('\t.include "data/maps/Route104/scripts.inc"\n', "")},
            "map.json scripts that are no label": {
                "data/maps/Route104/map.json": raw_text("data/maps/Route104/map.json").replace(
                    '"Route104_EventScript_Boy2"', '"Route104_EventScript_NoSuchLabel"')},
        }
        for needle, over in overlays.items():
            self.assertNotEqual(list(over.values())[0], raw_text(list(over)[0]), needle)
            self.assertRaisesRegex(Refused, re.escape(needle), ev_fast, OverlayDecomp(ROOT, over), maps_path)
        e = xe.GATE_WORDS["OldaleTown_EventScript_BlockedPath"]
        moved = dict(xe.GATE_WORDS, OldaleTown_EventScript_BlockedPath=(e[0], ev_moved(e[1])) + e[2:])
        with Swap(xe, "GATE_WORDS", moved):
            self.assertRaisesRegex(Refused, "cited table lines", ev_fast)
        extra = dict(xe.GATE_WORDS, Route103_EventScript_RivalEnd=(
            "words", ("data/maps/Route103/scripts.inc:133", "setflag FLAG_DEFEATED_RIVAL_ROUTE103")))
        with Swap(xe, "GATE_WORDS", extra):
            self.assertRaisesRegex(Refused, "GATE_WORDS labels that are not exactly one", ev_fast)
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(WORLD / "maps.json", Path(tmp, "maps.json"))
            tr = json.loads((WORLD / "trainers.json").read_text(encoding="utf-8"))
            tr["trainers"] = [t for t in tr["trainers"] if t["symbol"] != "TRAINER_GRUNT_PETALBURG_WOODS"]
            Path(tmp, "trainers.json").write_text(json.dumps(tr), encoding="utf-8")
            self.assertRaisesRegex(Refused, "trainers the scripts name that trainers.json lacks", ev_fast, None,
                                   str(Path(tmp, "maps.json")))
            doc = json.loads((WORLD / "maps.json").read_text(encoding="utf-8"))
            doc["_source"] = "pret/pokeemerald@0000000"
            Path(tmp, "maps.json").write_text(json.dumps(doc), encoding="utf-8")
            self.assertRaisesRegex(Refused, "maps.json is from", ev_fast, None, str(Path(tmp, "maps.json")))
        res = dict(ev_build()[1])
        res["labels"] = copy.deepcopy(res["labels"][:3])
        res["labels"][0]["flag"] = "FLAG_X"
        with Swap(xe, "build", lambda d, mj, names: res):
            self.assertRaisesRegex(Refused, "R-4", xe.build_all, ew.Decomp(ROOT), maps_path)
        res["labels"][0].pop("flag")
        with Swap(xe, "build", lambda d, mj, names: res):  # CONTROL: the same short result passes
            self.assertEqual(len(xe.build_all(ew.Decomp(ROOT), maps_path)[0]["labels"]), 3)

    def test_dead_line_after_end(self):
        """An op line after `end` (ev_faulted's overlay) is listed in `dead` with its line, and is no change. CONTROL:
        the real build has no such line."""
        self.assertEqual([x for x in ev_build()[0]["dead"] if "line" in x], [])
        obj = ev_faulted()
        self.assertEqual([x for x in obj["dead"] if "line" in x], [{
            "label": "Route103_EventScript_RivalEnd", "ref": "data/maps/Route103/scripts.inc:129",
            "line": "data/maps/Route103/scripts.inc:140", "command": "setflag",
            "why": "after `end` (data/maps/Route103/scripts.inc:139) in the same label: this line never runs"}])
        self.assertEqual([c["dev"]["ref"].rsplit(":", 1)[1] for c in ev_by(obj)["Route103_EventScript_RivalEnd"]["changes"]],
                         ["131", "132", "133", "134", "135"])


def ev_unit_ctx():
    d = ew.Decomp(ROOT)
    return {"persist": xe.Persist(d), "names": {"TRAINER_JOSH": "YOUNGSTER JOSH"},
            "alias": {"MYFLAG": "FLAG_TEMP_1", "MYVAR": "VAR_TEMP_0", "SRC": "VAR_BIRCH_LAB_STATE"},
            "map_names": {"MAP_ROUTE101": "Route101"}}


class S2bUnitTests(unittest.TestCase):
    """Function-level FAULT / CONTROL arms on synthetic inputs where the branch decides, for branches no record at the
    pin exercises (a flag alias, a saved specialvar result, a warp id, an unnamed trainer, a closure past the bound)
    and for the ones the verifier does not re-derive."""

    def test_change_of_branches(self):
        ctx = ev_unit_ctx()
        lab = {"file": "x.inc", "line": 1, "body": []}

        def co(mn, *args):
            return xe.change_of(ctx, lab, 5, mn, list(args))
        self.assertEqual(co("setflag", "FLAG_ADVENTURE_STARTED")[0]["dev"], {"flags": ["FLAG_ADVENTURE_STARTED"],
                                                                             "ref": "x.inc:5"})
        self.assertEqual(co("setflag", "MYFLAG"), (None, ("temp flags (cleared on every map entry)", "FLAG_TEMP_1")))
        self.assertEqual(co("setvar", "MYVAR", "1")[1][1], "VAR_TEMP_0")
        self.assertEqual(co("setvar", "VAR_RESULT", "1")[1][0][:12], "special vars")
        self.assertEqual(co("copyvar", "VAR_OLDALE_TOWN_STATE", "SRC")[0]["dev"],
                         {"vars": ["VAR_OLDALE_TOWN_STATE", "VAR_BIRCH_LAB_STATE"], "ref": "x.inc:5",
                          "from": "VAR_BIRCH_LAB_STATE"})
        self.assertEqual(co("copyvar", "VAR_OLDALE_TOWN_STATE", "1")[0]["dev"]["value"], xe.COPYVAR_BUG)
        self.assertEqual(co("copyvar", "VAR_OLDALE_TOWN_STATE", "0x4050")[0]["dev"]["value"],
                         "unknown (copied from var id 0x4050)")
        self.assertEqual((co("setorcopyvar", "VAR_OLDALE_TOWN_STATE", "VAR_BIRCH_LAB_STATE")[0]["op"],
                          co("setorcopyvar", "VAR_OLDALE_TOWN_STATE", "3")[0]["op"],
                          co("setorcopyvar", "VAR_OLDALE_TOWN_STATE", "3")[0]["dev"]["value"]), ("copyvar", "setvar", "3"))
        self.assertEqual(co("settrainerflag", "TRAINER_JOSH")[0]["effect"], "YOUNGSTER JOSH now counts as beaten")
        self.assertEqual(co("cleartrainerflag", "TRAINER_TOMMY")[0]["effect"], None)  # not in names: no words
        self.assertEqual(co("specialvar", "VAR_OLDALE_TOWN_STATE", "GetX")[0]["dev"]["vars"], ["VAR_OLDALE_TOWN_STATE"])
        self.assertNotIn("vars", co("specialvar", "VAR_RESULT", "GetX")[0]["dev"])
        self.assertEqual(co("specialvar", "VAR_RESULT", "GetX")[0]["name"], "GetX")
        w = [co("warp", "MAP_ROUTE101", *a)[0] for a in (("1",), ("2", "3", "4"), ("5", "6"))]
        self.assertEqual([x["warp_id"] for x in w], [1, 2, None])
        self.assertEqual(w[0]["effect"], "you are moved to Route101")
        self.assertEqual((co("warphole", "MAP_ROUTE101")[0]["effect"], co("warp", "MAP_UNDEFINED")[0]["effect"]),
                         (None, None))
        tb = co("trainerbattle", "TRAINER_BATTLE_PYRAMID", "TRAINER_PHILLIP", "0", "T", "T")[0]
        self.assertEqual(tb["trainer"], None)
        self.assertIn("TRAINER_BATTLE_PYRAMID", tb["dev"]["why"])
        self.assertEqual(co("trainerbattle_single", "TRAINER_JOSH", "A", "B")[0]["name"], "YOUNGSTER JOSH")

    def test_persist_ranges(self):
        p = xe.Persist(ew.Decomp(ROOT))
        self.assertEqual([p.dropped(ns, n) for ns, n in (
            ("flag", "FLAG_TEMP_1"), ("flag", "FLAG_HIDE_MAP_NAME_POPUP"), ("var", "VAR_TEMP_0"), ("var", "VAR_RESULT"),
            ("flag", "VAR_0x8005"), ("flag", "FLAG_ADVENTURE_STARTED"), ("var", "VAR_BIRCH_LAB_STATE"),
            ("flag", "NO_SUCH_NAME"))], [
            "temp flags (cleared on every map entry)", "special flags (not saved)",
            "temp vars (cleared on every map entry)",
            "special vars (scratch registers, the script result included; not saved)",
            "not a save flag (id past FLAGS_COUNT)", None, None, None])

    def test_safe_callee_and_diverts(self):
        g = fake_graph("A::\n\tcall B\n\tsetflag FLAG_X\n\tend\nB::\n\tsetvar VAR_Y, 1\n\tgoto_if_eq VAR_Y, 1, C\n"
                       "\treturn\nC::\n\treturn\nD::\n\tspecial Foo\n\treturn\nE::\n\tend\n")
        self.assertEqual((xe.safe_line("bufferspeciesname"), xe.safe_line("msgbox"), xe.safe_line("special")),
                         (True, True, False))
        self.assertEqual([xe.callee_returns(g, x, {}) for x in "BCDE"], [True, True, False, False])
        with Swap(ei, "MAX_CLOSURE", 0):  # a closure past the bound is not proven (Refused -> False, never raised)
            self.assertIs(xe.callee_returns(g, "B", {}), False)
        self.assertEqual([xe.diverts(g, mn, a, {}) for mn, a in (
            ("call", ["B"]), ("call", ["D"]), ("call_if_eq", ["VAR_X", "1", "B"]), ("call_if_eq", ["VAR_X", "1", "E"]),
            ("special", ["Foo"]), ("msgbox", ["T"]), ("bufferspeciesname", ["0", "X"]))],
            [False, True, False, True, True, False, False])

    def test_live_body(self):
        g = fake_graph("A::\n\tsetflag FLAG_X\n\tend\n\tsetflag FLAG_Y\nB::\n\tend\n")
        live, dead = xe.live_body(g.labels["A"])
        self.assertEqual(([x[0] for x in live], [(x[0], x[2]) for x in dead]), ([2, 3], [(4, ("end", 3))]))
        live, dead = xe.live_body(g.labels["B"])
        self.assertEqual(dead, [])

    def test_gate_candidate_patterns(self):
        """gate_candidates on a synthetic graph where each clause decides (the first mutant run: deleting the steer
        warp/story clauses, the locked target's warp/story/end clauses, the reachable filter or profile's story count
        changed no candidate at the pin). CONTROL: S1 (a coord trigger that only steps the player) and L1 (a goto_if
        on a saved flag whose target only talks and ends, while the label's own way on warps) are the only candidates.
        Each other label breaks exactly one clause: S2 warps, S3 gives an item, L2's target warps, L3's target gives an
        item, L4's target returns instead of ending, U1 is L1's shape that nothing reaches."""
        text = ("S1::\n\tapplymovement LOCALID_PLAYER, M\n\twaitmovement 0\n\tend\n"
                "S2::\n\tapplymovement LOCALID_PLAYER, M\n\twarp MAP_ROUTE101, 1\n\tend\n"
                "S3::\n\tapplymovement LOCALID_PLAYER, M\n\tgiveitem ITEM_POTION\n\tend\n")
        for i, tgt in ((1, "\tmsgbox X\n\tend\n"), (2, "\twarp MAP_ROUTE102, 1\n\tend\n"),
                       (3, "\tgiveitem ITEM_POTION\n\tend\n"), (4, "\tmsgbox X\n\treturn\n")):
            text += "L%d::\n\tgoto_if_set FLAG_ADVENTURE_STARTED, T%d\n\twarp MAP_ROUTE101, 1\n\tend\nT%d::\n%s" % (
                i, i, i, tgt)
        text += "U1::\n\tgoto_if_set FLAG_ADVENTURE_STARTED, T1\n\twarp MAP_ROUTE101, 1\n\tend\nM::\n\tstep_end\n"

        class Fake:
            def read(self, rel):
                return text
        labels = ei.parse_labels(Fake(), ["x.inc"])
        roots = []
        for lab in ("S1", "S2", "S3", "L1", "L2", "L3", "L4"):
            kind = "coord" if lab[0] == "S" else "object"
            roots.append({"label": lab, "map": "MAP_X", "cond": ("var", "VAR_ROUTE101_STATE", "eq", "0") if
                          kind == "coord" else None, "object_flag": None, "hidden": False,
                          "giver": {"map": "MAP_X", "kind": kind, "object": 1, "local_id": 1, "graphics": "G"}})
        g = ei.Graph(None, labels, ei.build_edges(labels), roots, {})
        cands = xe.gate_candidates(g, xe.Persist(ew.Decomp(ROOT)))
        self.assertEqual(sorted((c[0], c[1]) for c in cands), [("L1", "locked"), ("S1", "steer")])
        self.assertFalse(g.reachable("U1"))

    def test_persistent_test_and_aliases(self):
        p = xe.Persist(ew.Decomp(ROOT))
        self.assertEqual([xe.persistent_test(c, p) for c in (
            ("trainer", "TRAINER_ROXANNE_1", True), ("flag", "FLAG_ADVENTURE_STARTED", True), ("flag", "FLAG_TEMP_1", True),
            ("var", "VAR_RESULT", "eq", "1"), ("var", "VAR_BIRCH_LAB_STATE", "eq", "1"),
            ("flag", "TRAINER_FLAGS_START", True), None)], [True, True, False, False, True, False, False])
        self.assertIn("TRAINER_FLAGS_START", p.ids)  # the regex arm's input is a real, saved, non-FLAG_ name

        class Fake:
            def read(self, rel):
                return ".set FOO, VAR_0x8009\n.set BAR, FLAG_TEMP_1\n.set BAZ, 5\n"
        self.assertEqual(xe.set_aliases(Fake(), ["a.inc"]), {"FOO": "VAR_0x8009", "BAR": "FLAG_TEMP_1"})
        self.assertEqual(xe.ms_word("MAP_SCRIPT_ON_FRAME_TABLE"), "on_frame")


class S2bVerifierTests(unittest.TestCase):
    """verify_world's stage-2b reading: CONTROL 0 on the real file; each EV plant on exactly its own ONE line; its own
    units where no plant reaches; the CLI and selftest wiring."""

    def test_control_and_plants(self):
        rep = vw.Report()
        vw.verify_events(ROOT, vw.load_events(str(WORLD)), vw.load(str(WORLD)), rep)
        self.assertEqual(rep.lines, [])
        self.assertEqual(rep.counts.get("events_labels"), 2300)
        self.assertEqual(len(vw.EV_PLANTS), 25)  # fix round 1: + b4f b4s b4m b11 b10m
        for name in vw.EV_PLANTS:
            ok, lines, prefix = vw.ev_plant_result(ROOT, str(WORLD), name)
            self.assertTrue(ok, "%s: %s not in %s" % (name, prefix, lines))

    def test_verifier_units(self):
        self.assertEqual(vw.ev_eval("0x10 + 2*3", {}), 22)
        self.assertEqual(vw.ev_eval("A / 2 // a comment", {"A": 7}), 3)
        self.assertEqual(vw.ev_eval("0x7FFFFFFFFFFFFFFF / 1", {}), 0x7FFFFFFFFFFFFFFF)  # integer, not float, division
        self.assertRaises(ValueError, vw.ev_eval, "1;2", {})
        ids = vw.ev_ids(vw.raw(ROOT))
        mine = ei.name_ids(ew.Decomp(ROOT))  # the extractor's ids, read independently: the bounds must agree
        for n in ("TEMP_FLAGS_START", "TEMP_FLAGS_END", "SPECIAL_FLAGS_START", "SPECIAL_FLAGS_END", "TEMP_VARS_START",
                  "TEMP_VARS_END", "SPECIAL_VARS_START", "SPECIAL_VARS_END", "FLAGS_COUNT", "VARS_START",
                  "FLAG_REGISTERED_ROSE"):  # the last needs rematches.h's enum (TRAINER_REGISTERED_FLAGS_START + id)
            self.assertEqual(ids[n], mine[n], n)
        # a flag id past FLAGS_COUNT but below the special range is no save flag (only the FLAGS_COUNT clause says so;
        # the special-flags clause is implied by it, since SPECIAL_FLAGS_START 0x4000 > FLAGS_COUNT 0x960)
        self.assertIs(vw.ev_saved(dict(ids, FLAG_PAST=ids["FLAGS_COUNT"]), "flag", "FLAG_PAST"), False)
        self.assertGreater(ids["SPECIAL_FLAGS_START"], ids["FLAGS_COUNT"])
        self.assertEqual([vw.ev_saved(ids, ns, n) for ns, n in (
            ("flag", "FLAG_TEMP_1"), ("flag", "FLAG_HIDE_MAP_NAME_POPUP"), ("flag", "VAR_0x8005"),
            ("flag", "FLAG_ADVENTURE_STARTED"), ("var", "VAR_TEMP_0"), ("var", "VAR_RESULT"),
            ("var", "VAR_BIRCH_LAB_STATE"), ("var", "NO_SUCH_NAME"))], [False, False, False, True, False, False, True, None])
        self.assertEqual(vw.ev_live({"lines": [(1, "setflag FLAG_X"), (2, "end"), (3, "setflag FLAG_Y")]}),
                         [(1, "setflag FLAG_X"), (2, "end")])

        def op(line, aliases=None):
            p = line.replace(",", " ").split()
            return vw.ev_op(p[0], p, aliases or {}, ids)
        self.assertEqual([op("setorcopyvar VAR_OLDALE_TOWN_STATE, VAR_BIRCH_LAB_STATE"),
                          op("setorcopyvar VAR_OLDALE_TOWN_STATE, 3"), op("specialvar VAR_RESULT, GetX"),
                          op("trainerbattle TRAINER_BATTLE_PYRAMID, TRAINER_PHILLIP, 0, T, T"),
                          op("setvar NUM_OPPONENTS, 1", {"NUM_OPPONENTS": "VAR_0x8009"}), op("msgbox T"),
                          op("setflag MYFLAG", {"MYFLAG": "FLAG_TEMP_1"}),
                          op("setorcopyvar VAR_OLDALE_TOWN_STATE, SRC", {"SRC": "VAR_BIRCH_LAB_STATE"})],
                         [("copyvar", "VAR_OLDALE_TOWN_STATE", None), ("setvar", "VAR_OLDALE_TOWN_STATE", "3"),
                          ("special", "GetX", None), ("trainerbattle", None, None), "drop", None, "drop",
                          ("copyvar", "VAR_OLDALE_TOWN_STATE", None)])
        out = vw.s2_strip("L::\n\tend\n\t/* Never used */\nM::\n\tend\n")
        self.assertFalse(any("/*" in ln for ln in out), out)
        self.assertEqual(len(out), 6)  # one output line per input line (the comment line kept, emptied)

    def test_reach_and_story_clauses(self):
        """Verifier clauses that changed nothing at the pin (the first mutant run: V36, V46, V54), each on a planted copy
        of the real reading. ev_kinds: a mention from a label nothing reaches (a dead label) adds no `called` kind.
        ev_candidates: a story line (giveitem) in a steer trigger's script ends it being a steer; a label with the
        locked shape that nothing reaches is no candidate. CONTROL: the unplanted reading."""
        e = vw.ev_raw(ROOT)
        s = e["s"]
        bag, dead = "Route101_EventScript_BirchsBag", "EventScript_CableClub_SetVarResult1"
        self.assertEqual(vw.ev_kinds(e, bag), {"talk"})
        s2 = dict(s, at=dict(s["at"]), labs=dict(s["labs"]), owner=dict(s["owner"]))
        s2["at"][bag] = list(s["at"].get(bag, ())) + [(dead, s["labs"][dead]["lines"][0][0])]
        e2 = dict(e, s=s2)
        self.assertEqual(vw.ev_kinds(e2, bag), {"talk"})
        base = vw.ev_candidates(e)
        steer = ("OldaleTown_EventScript_BlockedPath", "steer")
        self.assertIn(steer, base)
        lab = s["labs"][steer[0]]
        s2["labs"][steer[0]] = dict(lab, lines=list(lab["lines"][:-1]) + [(9998, "giveitem ITEM_POTION")] +
                                    list(lab["lines"][-1:]))
        s2["labs"]["ZZ_Unreached"] = {"file": "x.inc", "line": 1, "lines": [
            (2, "goto_if_set FLAG_ADVENTURE_STARTED, ZZ_Talk"), (3, "warp MAP_ROUTE101, 1"), (4, "end")]}
        s2["labs"]["ZZ_Talk"] = {"file": "x.inc", "line": 5, "lines": [(6, "msgbox X"), (7, "end")]}
        self.assertFalse(vw.ev_reached(s2, "ZZ_Unreached"))
        self.assertEqual(vw.ev_candidates(e2), base - {steer})

    def test_dead_lines_reading(self):
        """The verifier's own dead-line reading (ev_raw over s2_raw's labels): an op line after `end` is a dead line and
        never a wanted op. No label at the pin has one, so s2_raw is swapped for a copy whose RivalEnd gains the line
        ev_faulted plants (data/maps/Route103/scripts.inc:140); CONTROL: the real reading has none."""
        self.assertEqual(vw.ev_raw(ROOT)["dead_lines"], set())
        real = vw.s2_raw(ROOT)
        lab = real["labs"]["Route103_EventScript_RivalEnd"]
        planted = dict(real, labs=dict(real["labs"]))
        planted["labs"]["Route103_EventScript_RivalEnd"] = dict(
            lab, lines=list(lab["lines"]) + [(140, "setflag FLAG_DEFEATED_RIVAL_ROUTE103")])
        saved = dict(vw._EV)
        try:
            vw._EV.clear()
            with Swap(vw, "s2_raw", lambda root: planted):
                e = vw.ev_raw(ROOT)
            self.assertEqual(e["dead_lines"], {"data/maps/Route103/scripts.inc:140"})
            self.assertEqual(len(e["want"]["Route103_EventScript_RivalEnd"]), 5)
        finally:
            vw._EV.clear()
            vw._EV.update(saved)

    def test_cli_and_selftest_wiring(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(vw.main(["--plant", "f"]), 0)
        self.assertIn("PLANT f PASS: MISMATCH events label RustboroCity_Gym_EventScript_RoxanneDefeated", buf.getvalue())
        with tempfile.TemporaryDirectory() as tmp:  # the full run reads events.json: CONTROL 0, FAULT (f) exits 1
            for p in WORLD.glob("*.json"):
                shutil.copy(p, Path(tmp, p.name))
            for want in (0, 1):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    self.assertEqual(vw.main(["--data", tmp]), want, buf.getvalue()[-600:])
                self.assertIn("'events_labels': 2300", buf.getvalue())
                ev = vw.load_events(tmp)
                vw.ev_plant(ev, "f")
                Path(tmp, xe.OUT_NAME).write_text(json.dumps(ev), encoding="utf-8")
            self.assertIn("MISMATCH events label RustboroCity_Gym_EventScript_RoxanneDefeated", buf.getvalue())
        with Swap(vw, "S2_PLANTS", ()), Swap(vw, "EV_PLANTS", ("f",)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertTrue(vw.selftest(vw.raw(ROOT), str(WORLD), MILESTONES, vw.DEFAULT_SEED))
            self.assertIn("[PASS] EV CONTROL: events.json, 0 mismatches", buf.getvalue())
            self.assertIn("[PASS] EV FAULT (f)", buf.getvalue())
            with Swap(vw, "ev_plant_result", lambda *a: (False, [], "x")), redirect_stdout(io.StringIO()):
                self.assertFalse(vw.selftest(vw.raw(ROOT), str(WORLD), MILESTONES, vw.DEFAULT_SEED))

    def test_verifier_shares_no_function(self):
        src = (HERE / "verify_world.py").read_text(encoding="utf-8")
        self.assertNotRegex(src, r"(?m)^\s*(import|from)\s+extract_(events|items)", "the verifier imports no extractor")


#: stage 2b fix round 1, item 1: the only two labels in the decomp whose live body ends in a jump followed by a DEAD
#: line (the verifier's whole-decomp scan): (the label that jumps, the label after it, its `goto` line, the dead line)
FIX1_KNOWN = (("FallarborTown_BattleTentBattleRoom_EventScript_ContinueChallenge",
               "FallarborTown_BattleTentBattleRoom_EventScript_WarpToLobbyWon",
               "data/maps/FallarborTown_BattleTentBattleRoom/scripts.inc", 122, 123),
              ("BattleFrontier_BattleArenaBattleRoom_EventScript_ContinueChallenge",
               "BattleFrontier_BattleArenaBattleRoom_EventScript_ReturnToLobbyWon",
               "data/maps/BattleFrontier_BattleArenaBattleRoom/scripts.inc", 185, 186))


def mc_lines():
    """{path:line: trainer} of every `register_matchcall` line under data/ at the pin, read by the TEST from the raw
    files (never through either reader)."""
    out = {}
    for p in sorted(Path(ROOT, "data").rglob("*")):
        if p.suffix in (".inc", ".s"):
            for n, line in enumerate(p.read_bytes().decode("utf-8").split("\n"), 1):
                m = re.match(r"\s*register_matchcall\s+(\w+)", line)
                if m:
                    out["%s:%d" % (p.relative_to(ROOT).as_posix(), n)] = m.group(1)
    return out


class S2bFixRound1Tests(unittest.TestCase):
    """Stage 2b FIX ROUND 1 (fix-spec-2b1): (1) no fall after a jump in the extractor's edge builder, (2) the same rule
    written independently in the verifier, (3) the verifier compares each trigger's TARGET, (4) register_matchcall is a
    persistent change. Each test has a CONTROL on the real build and a FAULT with the rule broken."""

    def test_fix1_no_fall_after_a_jump(self):
        lab = lambda *body: {"body": list(enumerate(body, 1))}  # noqa: E731
        self.assertFalse(ei.falls_through(lab("goto X", "waitstate")))           # CONTROL: the jump ends the flow
        self.assertTrue(ei.falls_through(lab("msgbox T", "waitstate")))           # CONTROL: no jump, a command runs on
        with Swap(ei, "NEVER_CONTINUES", {}):                                     # FAULT: the last-line reading only
            self.assertTrue(ei.falls_through(lab("goto X", "waitstate")))
        text = "A::\n\tgoto C\n\twaitstate\nB::\n\tsetflag FLAG_ADVENTURE_STARTED\n\tend\nC::\n\tend\n"
        falls = lambda gr: [t for t, k, *_ in gr.edges["A"] if k == "fall"]  # noqa: E731
        self.assertEqual(falls(fake_graph(text)), [])
        with Swap(ei, "NEVER_CONTINUES", {}):
            self.assertEqual(falls(fake_graph(text)), ["B"])
        # the whole real graph: no fall edge out of a label whose body holds a never-continuing command
        g = ev_build()[1]["graph"]
        bad = [s for s, outs in g.edges.items() for t, k, *_ in outs if k == "fall"
               and any(ei.cmd(c)[0] in ei.NEVER_CONTINUES for _, c in g.labels[s]["body"])]
        self.assertEqual(bad, [])
        self.assertGreater(sum(1 for outs in g.edges.values() for _, k, *_ in outs if k == "fall"), 0)
        # the known answers (decomp lines read here): the jump, then the dead line; no `fall` trigger, other triggers stay
        by = ev_by(ev_build()[0])
        for src, tgt, rel, jump, dead in FIX1_KNOWN:
            lines = raw_text(rel).split("\n")
            self.assertTrue(lines[jump - 1].strip().startswith("goto "), lines[jump - 1])
            self.assertEqual(lines[dead - 1].strip(), "waitstate")
            self.assertEqual(next(x.strip() for x in lines[dead:] if x.strip()), tgt + "::")  # no label between
            trig = by[tgt]["trigger"]
            self.assertFalse([t for t in trig if t.get("by") == src], trig)
            self.assertTrue(trig)
            self.assertFalse([e for e in g.edges[src] if e[1] == "fall"])

    def test_fix2_verifier_fall_rule(self):
        """The verifier's own reading (s2_raw): no fall mention out of a label with an S2_ENDS command before its last
        line, over every label; the two known answers. FAULT: the stage-2b phantom put back into a fresh copy is
        reported, which needs this rule (with the old last-line rule the verifier read the same phantom and agreed)."""
        s = vw.s2_raw(ROOT)
        falls = [(tgt, src) for tgt, ms_ in s["at"].items() for src, n in ms_ if n == 10 ** 9]
        self.assertGreater(len(falls), 0)
        bad = [(t, src) for t, src in falls
               if any(ln.split()[0] in vw.S2_ENDS for _, ln in s["labs"][src]["lines"][:-1] if not ln.startswith("."))]
        self.assertEqual(bad, [])
        for src, tgt, *_ in FIX1_KNOWN:
            self.assertNotIn((src, 10 ** 9), s["at"].get(tgt, []))
            self.assertTrue(s["at"].get(tgt))
        obj = ev_copy()
        for src, tgt, rel, _, dead in FIX1_KNOWN:
            ev_by(obj)[tgt]["trigger"].append({"kind": "called", "by": src, "how": "fall",
                                               "dev": {"ref": "%s:%d" % (rel, dead)}})
        rep = vw.Report()
        vw.verify_events(ROOT, obj, vw.load(str(WORLD)), rep)
        self.assertEqual(sorted(rep.lines), sorted(
            "MISMATCH events label %s: trigger sources: extra [('called', '%s')], missing [] (the verifier's reading)"
            % (tgt, src) for src, tgt, *_ in FIX1_KNOWN))

    def test_fix3_trigger_targets(self):
        """ev_trig_src / ev_trig_how / ev_trig_map: CONTROL 0 on the fresh build; each plant reported by ITS check's
        words only (the other two are silent on it); ev_how and the self-loop read."""
        rep = vw.Report()
        vw.verify_events(ROOT, ev_build()[0], vw.load(str(WORLD)), rep)
        self.assertEqual(rep.lines, [])
        tags = {"b4f": " how ['", "b4s": "trigger sources:", "b4m": "trigger maps:"}  # each check's own words
        needles = {"b4f": "RivalExitFacingNorth how ['fall'], the verifier's reading ['goto']",
                   "b4s": "extra [('called', 'Route101_EventScript_BirchsBag')]",
                   "b4m": "extra [('coord', 'MAP_ROUTE101')], missing [('coord', 'MAP_PETALBURG_WOODS')]"}
        for name, tag in tags.items():
            ok, lines, _ = vw.ev_plant_result(ROOT, str(WORLD), name)
            self.assertTrue(ok, lines)
            self.assertIn(needles[name], lines[0])
            self.assertEqual([t for t in tags.values() if t in lines[0]], [tag], (name, lines))
        self.assertEqual([vw.ev_how(ln, n) for ln, n in (
            ("goto X", 1), ("call X", 1), ("goto_if_set FLAG_X, X", 1), ("call_if_eq VAR_X, 1, X", 1), ("case 1, X", 1),
            (".4byte X", 1), ("trainerbattle_single TRAINER_X, A, B, X", 1), ("", 10 ** 9), ("gotostd X", 1))],
            ["goto", "call", "goto_if", "call_if", "case", "ref", "ref", "fall", "ref"])
        e = vw.ev_raw(ROOT)
        loop = "EventScript_DoTVShow"  # it jumps back into itself: a way in that `at` (no self-mentions) leaves out
        self.assertIn(loop, vw.ev_trigs(e, loop)[1])
        self.assertIn(("called", loop), vw.ev_out_trigs(e["s"], ev_by(ev_build()[0])[loop])[0])
        wt = ev_by(ev_build()[0])["PetalburgCity_EventScript_WallyTutorial"]  # a map_script_2 row: table label + maps
        src, _, maps = vw.ev_out_trigs(e["s"], wt)
        self.assertEqual((src, maps), vw.ev_trigs(e, wt["label"])[::2])
        self.assertIn(("map_script", ("MAP_PETALBURG_CITY",)), maps)

    def test_fix4_matchcall_is_a_change(self):
        """Every register_matchcall line at the pin (76, read here from the raw files) is a `special
        SetMatchCallRegisteredFlag` change naming its trainer, in line order within its label, worded from the cited
        template; check_matchcall refuses a trainer that heads no rematch row; the verifier checks it on every record."""
        want = mc_lines()
        self.assertEqual((len(want), len(set(want.values()))), (76, 64))
        obj = ev_build()[0]
        names = {t["symbol"]: ("%s %s" % (t.get("class_name") or "", t["name"])).strip()
                 for t in OBJS["trainers.json"]["trainers"]}
        got = {}
        for r in obj["labels"]:
            refs = [int(c["dev"]["ref"].rsplit(":", 1)[1]) for c in r["changes"]]
            self.assertEqual(refs, sorted(refs), r["label"])  # in order with the label's other changes
            for c in r["changes"]:
                if c["dev"].get("cmd") == "register_matchcall":
                    got[c["dev"]["ref"]] = c
        self.assertEqual(set(got), set(want))
        for ref_, c in got.items():
            self.assertEqual((c["op"], c["name"], c["trainer"], c["effect"]),
                             ("special", "SetMatchCallRegisteredFlag", want[ref_],
                              "%s is registered in your Match Call" % names[want[ref_]]), ref_)
        # the extractor's unit and its guard (CONTROL / FAULT)
        ctx = dict(ev_unit_ctx(), rematch_first={"TRAINER_JOSH": "REMATCH_JOSH"})
        lab = {"file": "x.inc", "line": 1, "body": []}
        rec, drop = xe.change_of(ctx, lab, 5, "register_matchcall", ["TRAINER_JOSH"])
        self.assertEqual((rec, drop), ({"op": "special", "name": "SetMatchCallRegisteredFlag", "trainer": "TRAINER_JOSH",
                                        "effect": "YOUNGSTER JOSH is registered in your Match Call",
                                        "dev": {"cmd": "register_matchcall", "ref": "x.inc:5"}}, None))
        self.assertRaisesRegex(Refused, "TRAINER_TOMMY at x.inc:5: the trainer heads no gRematchTable row",
                               xe.change_of, ctx, lab, 5, "register_matchcall", ["TRAINER_TOMMY"])
        firsts = xe.rematch_first(ew.Decomp(ROOT))
        self.assertEqual(len(firsts), 78)
        self.assertIn("TRAINER_ROSE_1", firsts)
        self.assertNotIn("TRAINER_ROSE_2", firsts)
        # the guards' CALLS inside the build: a row whose first id is not the one the script registers, and no table
        rel = "src/battle_setup.c"
        text = raw_text(rel)
        haley = "[REMATCH_HALEY] = REMATCH(TRAINER_HALEY_1,"
        self.assertEqual(text.count(haley), 1)
        self.assertRaisesRegex(Refused, "register_matchcall TRAINER_HALEY_1 at data/maps/Route104/scripts.inc",
                               ev_fast, OverlayDecomp(ROOT, {rel: text.replace(haley, haley.replace("_1,", "_2,"))}))
        self.assertRaisesRegex(Refused, "no gRematchTable row read", ev_fast,
                               OverlayDecomp(ROOT, {rel: text.replace("= REMATCH(", "= NOT_A_ROW(")}))
        # the verifier: its own macro reading, its rematch clause (a planted reading), ev_op, ev_mc_line
        r = vw.raw(ROOT)
        self.assertEqual(vw.ev_matchcall_macro(r), "SetMatchCallRegisteredFlag")
        self.assertEqual(vw.ev_rematch_first(r), set(firsts))
        ids = vw.ev_ids(r)
        p = "register_matchcall TRAINER_HALEY_1".split()
        self.assertEqual(vw.ev_op(p[0], p, {}, ids, "SetMatchCallRegisteredFlag"),
                         ("special", "SetMatchCallRegisteredFlag", None))
        self.assertIsNone(vw.ev_op(p[0], p, {}, ids))  # no macro reading: not an op
        self.assertEqual(vw.ev_mc_line(r, {"dev": {"ref": "data/maps/Route104/scripts.inc:874"}}), "TRAINER_HALEY_1")
        self.assertIsNone(vw.ev_mc_line(r, {"dev": {"ref": "data/maps/Route104/scripts.inc:873"}}))
        e = vw.ev_raw(ROOT)
        saved = e["rematch_first"]
        try:
            e["rematch_first"] = saved - {"TRAINER_HALEY_1"}
            rep = vw.Report()
            vw.verify_events(ROOT, ev_build()[0], vw.load(str(WORLD)), rep)
            self.assertEqual(len(rep.lines), 2, rep.lines)  # RegisterHaley and RegisterHaleyAfterBattle
            self.assertTrue(all("TRAINER_HALEY_1 heads no gRematchTable row" in ln for ln in rep.lines), rep.lines)
        finally:
            e["rematch_first"] = saved
        for name, needle in (("b11", "the line registers TRAINER_HALEY_1"),
                             ("b10m", "Match Call effect 'LASS HALEY is registered")):
            ok, lines, _ = vw.ev_plant_result(ROOT, str(WORLD), name)
            self.assertTrue(ok and needle in lines[0], lines)


class TFairTests(unittest.TestCase):
    """T-FAIR (spec S3-4 slice 2): check_fairness.developer_keys() still refuses `flag` with the new file present. If a
    KNOWLEDGE_FIELDS entry ever classifies a flag path `ai`, `flag` leaves the set and B2 stops refusing x['flag']
    everywhere (milestones.json included). The loader item must add `dev` as developer and extend this test."""

    def test_flag_stays_developer(self):
        self.assertIn("flag", cf.developer_keys())
        self.assertTrue((WORLD / ei.OUT_NAME).exists())
        self.assertTrue((WORLD / xe.OUT_NAME).exists())  # stage 2b: still `flag` with events.json present
        for name, path in (("items_gifts.json", "gifts.[].flag"), ("events.json", "labels.[].changes.[].flag")):
            fields = copy.deepcopy(cf.KNOWLEDGE_FIELDS)
            fields[name] = {path: (cf.AI, "a FAULT: a flag classified ai", True)}
            self.assertNotIn("flag", cf.developer_keys(fields), name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
