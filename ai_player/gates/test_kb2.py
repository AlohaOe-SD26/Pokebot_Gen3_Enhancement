"""UNIT PROOFS of KB2 slice 1 (spec S3-4): extract_world.py, verify_world.py and the four files under knowledge/world/.

    py -3.12 ai_player/gates/test_kb2.py        (exit 0 = every test passed; needs the PINNED decomp clone)

Every test has a FAULT half (the rule broken: the check must fail) beside its CONTROL (the real data passes), so no
test can pass vacuously. The decomp-built objects are made ONCE (about a second) and every fault is made on a COPY:
a scratch skeleton, a scratch map.json read through an overlay, a deep copy of an output. Nothing is written inside the
repository (FrozenTree, provenance.py G1, watches it): every file a test writes goes to a temp folder.

  OutputsTests      the committed files are byte-identical to a fresh extraction (FAULT: one changed value differs).
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
  W4ConsistencyTests the first 20 campaign ids are milestones.json's; every area map resolves; every FLAG/VAR in the
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
"""
import copy
import io
import json
import os
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
}
#: what a reader of the world files would have to write (`world/` alone is not one: the AI's own `ai_player/world/`
#: package is named in comments and paths all over the play code)
PLAY_NAMES = ("knowledge/world", "trainers.json", "bosses.json", "maps.json", "campaign.json")

ROOT = None
D = None
OBJS = None
RAW = None
MILESTONES = json.loads((KNOWLEDGE / "milestones.json").read_text(encoding="utf-8"))


def setUpModule():
    global ROOT, D, OBJS, RAW
    ROOT = ew.resolve_decomp()  # no pinned clone: every test ERRORS (a loud failure, never a silent skip or pass)
    D = ew.Decomp(ROOT)
    OBJS = ew.build_all(D)
    RAW = vw.raw(ROOT)


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


def campaign_of(sk):
    o = OBJS
    maps, bosses = o["maps.json"]["maps"], o["bosses.json"]["bosses"]
    return ew.build_campaign(D, sk, MILESTONES, maps, bosses, o["trainers.json"]["trainers"],
                             o["campaign.json"]["field_move_badges"])


def serial(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


class OutputsTests(unittest.TestCase):
    def test_committed_files_equal_a_fresh_extraction(self):
        for name in ew.OUTPUTS:
            self.assertEqual((WORLD / name).read_bytes(), serial(OBJS[name]), name)
        bad = copy.deepcopy(OBJS["bosses.json"])
        bad["bosses"][0]["party"][0]["level"] += 1
        self.assertNotEqual((WORLD / "bosses.json").read_bytes(), serial(bad))


class W1WithheldTests(unittest.TestCase):
    def test_constant_is_the_ruling(self):
        self.assertEqual(ew.WITHHELD_FIELDS, ("iv", "aiFlags"))
        self.assertEqual(vw.WITHHELD, ew.WITHHELD_FIELDS)

    def test_scan_every_knowledge_file(self):
        n, hits = vw.withheld_scan(str(KNOWLEDGE))
        self.assertEqual(hits, [])
        world = sorted(p.name for p in WORLD.glob("*.json"))
        self.assertEqual(world, sorted(ew.OUTPUTS))
        self.assertGreaterEqual(n, len(list(KNOWLEDGE.rglob("*.json"))))
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(KNOWLEDGE, Path(tmp) / "k", ignore=shutil.ignore_patterns("*.py", "__pycache__"))
            p = Path(tmp) / "k" / "world" / "trainers.json"
            for key, where in (("iv", "party"), ("aiFlags", "trainer"), ("ai_flags", "trainer"), ("IVs", "party")):
                data = copy.deepcopy(OBJS["trainers.json"])
                rec = data["trainers"][265]
                (rec["party"][0] if where == "party" else rec)[key] = 0
                p.write_text(json.dumps(data), encoding="utf-8")
                _, hits = vw.withheld_scan(str(Path(tmp) / "k"))
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

    def _one(self, change, prefix, also=None):
        data = vw.load(str(WORLD))
        change(data)
        rep, _ = vw.verify(RAW, data, MILESTONES, None)
        self.assertEqual(len(rep.lines), 1 + (also is not None), rep.lines)
        self.assertTrue(rep.lines[0].startswith(prefix), rep.lines)
        if also:
            self.assertTrue(rep.lines[1].startswith(also), rep.lines)

    def test_more_faults(self):
        def item(data):
            m = next(m for m in data["maps"]["maps"] if m["item_balls"])
            m["item_balls"][0]["item"] = "ITEM_MASTER_BALL"
        self._one(item, "MISMATCH item")

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
        self._one(dup_party, "MISMATCH totals parties")

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
        self._one(milestone, "MISMATCH campaign milestones")

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
        print("\n  W3 extras on the chapter 1-4 maps (listed for adjudication, not hidden): %s" % extras)

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
        self.assertEqual([e["id"] for e in entries[:20]], [m["id"] for m in MILESTONES["milestones"]])
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
        sk = scratch_skeleton(lambda es: es[40]["area"].__setitem__(1, "ROUTE118X"))
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


def names_in_play_code(package):
    """(files scanned, [(file, name)]) of every .py of the AI package, the test side `gates/` excepted, that names a
    world file or folder."""
    hits, n = [], 0
    for p in sorted(Path(package).rglob("*.py")):
        rel = p.relative_to(package).as_posix()
        if rel.startswith("gates/") or "__pycache__" in rel:
            continue
        n += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        hits += [(rel, name) for name in PLAY_NAMES if name in text]
    return n, hits


class NotReadTests(unittest.TestCase):
    def test_no_play_code_names_a_world_file(self):
        n, hits = names_in_play_code(REPO / "ai_player")
        self.assertGreater(n, 20)
        self.assertEqual(hits, [])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "brain").mkdir()
            (Path(tmp) / "brain" / "goals.py").write_text('BOOK = "knowledge/world/bosses.json"\n', encoding="utf-8")
            (Path(tmp) / "gates").mkdir()
            (Path(tmp) / "gates" / "ok.py").write_text('X = "maps.json"\n', encoding="utf-8")
            _, hits = names_in_play_code(tmp)
            self.assertEqual(hits, [("brain/goals.py", "knowledge/world"), ("brain/goals.py", "bosses.json")])

    def test_check_fairness_does_not_glob_world(self):
        from ai_player.gates.check_fairness import schema_problems
        problems, _ = schema_problems(KNOWLEDGE)
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


if __name__ == "__main__":
    unittest.main(verbosity=1)
