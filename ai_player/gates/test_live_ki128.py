"""UNIT PROOFS of the KI-128 + KI-129 held-out driver's graders (`gates/live_ki128.py`), on PLANTED logs, world files and
rows. Test side; no emulator, no live run.

    py -3.12 -B -m unittest ai_player.gates.test_live_ki128

Every grader has a FAULT case that must FAIL and a CONTROL that must PASS (CLAUDE.md rule 6):
  AlternationTests  6 crossings of one edge with nothing new between them FAIL; 7 with news after the 2nd PASS (the spec's
                    B-F1 seed-3 shape), by each of the four news records (N1 novelty line, N2 milestone line, N3 tiles_learned,
                    N4 maps visited); news outside the run does not count; a crossing with no world line gets no world news
                    (strict); an intent boundary splits a run; two edges never pool.
  EdgeWindowTests   (verifier F1) the ping-pong carried ACROSS intents (4 intents x 5 crossings: the per-intent bound
                    PASSES by construction) FAILS K8.EDGE_WINDOW; Part B working, and 40 crossings spread 400 frames apart,
                    PASS; 11 crossings in exactly 3,000 frames FAIL and in 3,010 PASS; news does not excuse the window; two
                    edges never pool; an unframed crossing leaves the run unread (VACUOUS); warps do not count; it is
                    GRADED, in the bounds text, and declared as B1 debt.
  WoodsTests        a woods exit arriving at y 38 does not count, one at y 30 from (14,5) does; the east warp, an earlier
                    north arrival from Rustboro, and a log the world memory does not back do not count; 5 of 6 PASS, 4 of 6
                    FAIL; the game showing Rustboro where the instruments do not FAILS.
  WorldSizeTests    a 301 MB world.jsonl FAILS (measured on a real file, then deleted); one under 300 MB PASSES.
  ThisRunTests      a stale end state FAILS L5.THIS_RUN (live_step5's own check) and so K8.THIS_RUN; a fresh one PASSES.
  LedgerTests       register, then a changed bound is REFUSED by ledger.begin; the same numbers begin; no other ledger entry
                    names 5972-5977.
  PurityTests, VerdictTests, ImportTests, ReaderTests: the purity bound, vacuity, REPORTED never counting, the frozen and
                    leftover checks, the G-3 import walk of the driver (and its fault), and the log reader on real lines.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates import live_ki128 as K  # noqa: E402

KEYS = K.map_key_table()
PC, R104, WOODS, RUST = "PETALBURG_CITY", "ROUTE104", "PETALBURG_WOODS", "RUSTBORO_CITY"


# ---------------------------------------------------------------------------------------------------- planted runs
def intent_line(name: str = "travel to RUSTBORO_CITY") -> str:
    return f"[AI-WORLD] intent '{name}': budget 9000 frames; on ROUTE104 at (39, 63); 12413 tiles known on 27 maps"


def edge_line(src: str, dst: str, frame: int, side: str = "left") -> str:
    return (f"[AI-WORLD] MAP {src} -> {dst} at (39, 63): the {side} edge from (0, 13) (the AI, f{frame}); 993 tiles of it "
            f"known")


def warp_line(src: str, dst: str, arrive: tuple, depart: tuple, frame: int, actor: str = "the AI") -> str:
    return (f"[AI-WORLD] MAP {src} -> {dst} at ({arrive[0]}, {arrive[1]}): the warp at ({depart[0]}, {depart[1]}) ({actor}, "
            f"f{frame}); 1571 tiles of it known")


def novelty_line(frame: int) -> str:
    return (f"[AI-WORLD] novelty at f{frame}: experience gained (PID aaad4c0c: 2686 -> 2725): progress (the intent's clock "
            f"f1 -> f{frame})")


class Planted:
    """A run folder: an ai_player.log and a world.jsonl written as the AI writes them (a full-memory line at every map
    change, transitions cumulative, `tiles_learned` monotone)."""

    def __init__(self, root: Path, start_frame: int = 1000) -> None:
        self.dir = root
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log: list[str] = []
        self.transitions: list[list] = [[10, "0:17", "0:0", "connection", "ai", [0, 8], [29, 18], "left"]]
        self.tiles = 5000
        self.maps = {"0:0": {"const": PC, "visits": {"1,1": 1}}, "0:19": {"const": R104, "visits": {"2,2": 1}}}
        self.lines = [self._line()]
        self.start_frame = start_frame

    def _line(self) -> str:
        return json.dumps({"maps": self.maps, "warps": {}, "connections": [], "transitions": list(self.transitions),
                           "tiles_learned": self.tiles})

    def cross(self, src: str, dst: str, frame: int, world: bool = True, side: str = "left") -> "Planted":
        self.log.append(edge_line(src, dst, frame, side))
        if world:
            self.transitions.append([frame, KEYS[src], KEYS[dst], "connection", "ai", [0, 13], [39, 63], side])
            self.lines.append(self._line())
        return self

    def warp(self, src: str, dst: str, arrive: tuple, depart: tuple, frame: int, world: bool = True) -> "Planted":
        self.log.append(warp_line(src, dst, arrive, depart, frame))
        if world:
            self.transitions.append([frame, KEYS[src], KEYS[dst], "warp", "ai", list(depart), list(arrive), "up"])
            self.lines.append(self._line())
        return self

    def say(self, line: str) -> "Planted":
        self.log.append(line)
        return self

    def learn(self, tiles: int = 3) -> "Planted":
        self.tiles += tiles
        return self

    def new_map(self, key: str = "24:11") -> "Planted":
        self.maps[key] = {"const": WOODS, "visits": {"5,5": 1}}
        return self

    def write(self) -> Path:
        (self.dir / "ai_player.log").write_text("\n".join(self.log) + "\n", encoding="utf-8")
        (self.dir / "world.jsonl").write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return self.dir

    def measures(self) -> dict:
        self.write()
        return K.measure_run(self.dir, self.start_frame, KEYS)


def ping_pong(p: Planted, crossings: int, first_frame: int = 2000, news_after: int | None = None, how: str = "N1",
              intent: bool = True) -> Planted:
    """`crossings` alternating crossings of PETALBURG_CITY|ROUTE104 in one intent; news of kind `how` after crossing
    number `news_after` (1-based), if given."""
    if intent:
        p.say(intent_line())
    for at in range(1, crossings + 1):
        src, dst = (R104, PC) if at % 2 else (PC, R104)
        frame = first_frame + 100 * at
        if news_after is not None and at == news_after + 1:
            if how == "N1":
                p.say(novelty_line(frame - 50))
            elif how == "N2":
                p.say("[AI-HANDS] [AI-GOALS] MILESTONE ch3_woods done at f%d (PETALBURG WOODS): VAR_PETALBURG_WOODS_STATE=1"
                      % (frame - 50))
            elif how == "N3":
                p.learn()
            elif how == "N4":
                p.new_map()
        p.cross(src, dst, frame, side="left" if at % 2 else "right")
    return p


def truth(visited: int = 0) -> dict:
    return {"frame": 1, "map": [0, 19], "state_md5": "x", "marks": {"VISITED_RUSTBORO_CITY": visited}, "stats": {}}


def row(name: str, *, purity: str = "PASS", this_run: str = "PASS", woods: bool = True, alt: int = 1,
        world_bytes: int | None = 1_000_000, visited: int = 1, measures: dict | None = None, by: str = "ai",
        window: int = 1, unframed: int = 0) -> dict:
    checks = [{"id": i, "kind": "GRADED", "status": purity if i == "L5.PURITY_CLEAN" else "PASS", "n": 1, "floor": 1,
               "text": i} for i in K.PURITY_IDS]
    checks.append({"id": "L5.PURITY_ENDED", "kind": "REPORTED", "status": "FAIL", "n": 1, "floor": None, "text": "ended"})
    checks.append({"id": "L5.THIS_RUN", "kind": "GRADED", "status": this_run, "n": 1, "floor": 1, "text": "fresh"})
    north = {"src": WOODS, "dst": R104, "depart": [14, 5], "arrive": [10, 30], "frame": 9000, "by_woods": woods}
    if measures is None:
        measures = {"log": {"lines": 10}, "world": {"bytes": world_bytes}, "north_log": north if woods else None,
                    "north_world": north if woods else None,
                    "alternation": {"crossings": alt, "runs": 1, "max": alt, "unmatched": 0, "over_count": int(alt > 5),
                                    "max_at": {"intent": 1, "edge": f"{PC}|{R104}", "length": alt, "frames": []}},
                    "edge_window": {"crossings": max(alt, window), "unframed": unframed, "max": window,
                                    "max_edge": f"{PC}|{R104}", "max_frames": [], "window": K.EDGE_WINDOW_FRAMES,
                                    "over": [f"{PC}|{R104}"] if window > K.EDGE_WINDOW_MAX else [],
                                    "per_edge": {f"{PC}|{R104}": window}},
                    "alternation_pooled": {"crossings": alt, "runs": 1, "max": alt, "max_at": None, "over_count": 0,
                                           "unmatched": 0}}
    return {"name": name, "personality": "Story", "seed": 1, "checks": checks, "measures": measures,
            "world_file": {"bytes": world_bytes, "deleted": True}, "truth_before": truth(0), "truth_after": truth(visited),
            "harness_stop": {"by": by, "cause": "test", "real_frames": 1}}


def by_id(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def six(**changes) -> list[dict]:
    """Five healthy rows plus one built from `changes` (the row under test)."""
    return [row(f"R{i}") for i in range(5)] + [row("R5", **changes)]


class Temp(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="ki128_test_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------- the alternation
class AlternationTests(Temp):
    def grade_with(self, measures: dict) -> str:
        checks = K.grade_batch([row(f"R{i}") for i in range(5)] + [row("R5", measures=measures)])
        return by_id(checks, "K8.ALTERNATION").status

    def test_six_crossings_with_nothing_new_between_fail(self):
        m = ping_pong(Planted(self.tmp / "r"), 6).measures()
        self.assertEqual(m["alternation"]["max"], 6)
        self.assertEqual(m["alternation"]["unmatched"], 0)
        self.assertEqual(self.grade_with(m), "FAIL")

    def test_five_crossings_with_nothing_new_pass(self):
        m = ping_pong(Planted(self.tmp / "r"), 5).measures()
        self.assertEqual(m["alternation"]["max"], 5)
        self.assertEqual(self.grade_with(m), "PASS")

    def test_seven_crossings_with_news_after_the_second_pass_by_each_record(self):
        # the spec's B-F1 seed-3 shape: 7 crossings in one intent, news after the 2nd -> alternations of 2 and 5
        for how in ("N1", "N2", "N3", "N4"):
            with self.subTest(how=how):
                m = ping_pong(Planted(self.tmp / how), 7, news_after=2, how=how).measures()
                self.assertEqual(m["alternation"]["crossings"], 7)
                self.assertEqual(m["alternation"]["max"], 5, m["alternation"])
                self.assertEqual(m["alternation"]["runs"], 2)
                self.assertEqual(self.grade_with(m), "PASS")

    def test_seven_crossings_with_news_after_the_first_fail(self):
        # FAULT twin of the above: news after the 1st leaves 6 with nothing new between
        m = ping_pong(Planted(self.tmp / "r"), 7, news_after=1).measures()
        self.assertEqual(m["alternation"]["max"], 6)
        self.assertEqual(self.grade_with(m), "FAIL")

    def test_news_outside_the_run_does_not_count(self):
        p = Planted(self.tmp / "r").say(intent_line()).say(novelty_line(1500))
        m = ping_pong(p, 6, intent=False).measures()
        self.assertEqual(m["alternation"]["max"], 6)
        self.assertEqual(self.grade_with(m), "FAIL")

    def test_a_crossing_without_its_world_line_gets_no_world_news(self):
        # tiles rise before crossing 3, but crossing 3 has no world line: no N3 news is credited (strict)
        p = Planted(self.tmp / "r").say(intent_line())
        for at in range(1, 8):
            src, dst = (R104, PC) if at % 2 else (PC, R104)
            if at == 3:
                p.learn()
            p.cross(src, dst, 2000 + 100 * at, world=at != 3)
        m = p.measures()
        self.assertEqual(m["alternation"]["unmatched"], 1)
        self.assertEqual(m["alternation"]["max"], 7)
        self.assertEqual(self.grade_with(m), "FAIL")
        # CONTROL: the same walk with crossing 3's world line splits at the news
        p2 = Planted(self.tmp / "r2").say(intent_line())
        for at in range(1, 8):
            src, dst = (R104, PC) if at % 2 else (PC, R104)
            if at == 3:
                p2.learn()
            p2.cross(src, dst, 2000 + 100 * at)
        m2 = p2.measures()
        self.assertEqual((m2["alternation"]["unmatched"], m2["alternation"]["max"]), (0, 5))

    def test_an_intent_boundary_splits_a_run(self):
        p = ping_pong(Planted(self.tmp / "r"), 3)
        ping_pong(p, 3, first_frame=4000)
        m = p.measures()
        self.assertEqual(m["alternation"]["crossings"], 6)
        self.assertEqual(m["alternation"]["max"], 3)
        self.assertEqual(self.grade_with(m), "PASS")

    def test_two_edges_never_pool(self):
        p = Planted(self.tmp / "r").say(intent_line())
        frame = 2000
        for _ in range(3):
            for src, dst in ((PC, R104), (R104, PC), ("ROUTE102", PC), (PC, "ROUTE102")):
                frame += 100
                p.cross(src, dst, frame)
        m = p.measures()
        self.assertEqual(m["alternation"]["crossings"], 12)
        self.assertEqual(m["alternation"]["max"], 6)  # each edge: 6 crossings, nothing new
        self.assertEqual(self.grade_with(m), "FAIL")
        q = Planted(self.tmp / "q").say(intent_line())
        frame = 2000
        for src, dst in ((PC, R104), (R104, PC), ("ROUTE102", PC), (PC, "ROUTE102"), (PC, R104), (R104, PC)):
            frame += 100
            q.cross(src, dst, frame)
        mq = q.measures()
        self.assertEqual(mq["alternation"]["max"], 4)  # PETALBURG_CITY|ROUTE104: 4; ROUTE102|PETALBURG_CITY: 2

    def test_warps_are_not_edge_crossings(self):
        p = Planted(self.tmp / "r").say(intent_line())
        for at in range(1, 9):
            p.warp(R104, WOODS, (16, 38), (10, 38), 2000 + 100 * at) if at % 2 else \
                p.warp(WOODS, R104, (10, 39), (16, 38), 2000 + 100 * at)
        m = p.measures()
        self.assertEqual((m["alternation"]["crossings"], m["alternation"]["max"]), (0, 0))
        self.assertEqual(m["log"]["map_changes"], {"edge": 0, "warp": 8})

    def test_no_world_file_reads_vacuous(self):
        m = ping_pong(Planted(self.tmp / "r"), 2).measures()
        m["world"] = None
        m["alternation"] = None
        checks = K.grade_batch([row(f"R{i}") for i in range(5)] + [row("R5", measures=m)])
        self.assertEqual(by_id(checks, "K8.ALTERNATION").status, "VACUOUS")
        self.assertEqual(K.batch_verdict(checks), "FAIL")


# ---------------------------------------------------------------------------------------------------- the edge window
def stop_and_restart(p: Planted, intents: int, per_intent: int = 5, first_frame: int = 2000, gap: int = 100) -> Planted:
    """THE VERIFIER F1 SHAPE (round 2's Bstop arm): Part B stops each intent at 5 crossings, a new intent restarts the
    count, and the walk carries on across the same edge with nothing new; `gap` frames between crossings."""
    frame = first_frame
    for _ in range(intents):
        p.say(intent_line())
        for at in range(1, per_intent + 1):
            frame += gap
            src, dst = (R104, PC) if at % 2 else (PC, R104)
            p.cross(src, dst, frame, side="left" if at % 2 else "right")
    return p


class EdgeWindowTests(Temp):
    def grade_with(self, measures: dict, check_id: str = "K8.EDGE_WINDOW") -> str:
        checks = K.grade_batch([row(f"R{i}") for i in range(5)] + [row("R5", measures=measures)])
        return by_id(checks, check_id).status

    def test_a_ping_pong_carried_across_intents_fails_the_window_and_passes_the_per_intent_bound(self):
        # FAULT: 4 intents x 5 crossings, 100 frames apart: the per-intent bound reads 5 (PASS, by construction), the
        # window reads 20 in 3,000 frames (FAIL). This is the case K8.ALTERNATION alone graded as clean (verifier F1).
        m = stop_and_restart(Planted(self.tmp / "r"), 4).measures()
        self.assertEqual(m["alternation"]["max"], 5)
        self.assertEqual(self.grade_with(m, "K8.ALTERNATION"), "PASS")
        self.assertEqual(m["edge_window"]["crossings"], 20)
        self.assertEqual(m["edge_window"]["max"], 20)
        self.assertEqual(m["alternation_pooled"]["max"], 20)
        self.assertEqual(self.grade_with(m), "FAIL")

    def test_part_b_working_passes(self):
        # CONTROL: one intent stopped at 5, then the next intents cross the edge once each, far apart (the B arms: 5-8)
        p = stop_and_restart(Planted(self.tmp / "r"), 1)
        stop_and_restart(p, 3, per_intent=1, first_frame=8000, gap=4000)
        m = p.measures()
        self.assertEqual(m["edge_window"]["max"], 5)
        self.assertEqual(self.grade_with(m), "PASS")

    def test_the_window_boundary(self):
        # 11 crossings whose last minus first is exactly 3,000 frames FAIL (11 within); 3,010 frames PASS (at most 10)
        m = stop_and_restart(Planted(self.tmp / "a"), 1, per_intent=11, gap=300).measures()
        self.assertEqual(m["edge_window"]["max"], 11)
        self.assertEqual(self.grade_with(m), "FAIL")
        m = stop_and_restart(Planted(self.tmp / "b"), 1, per_intent=11, gap=301).measures()
        self.assertEqual(m["edge_window"]["max"], 10)
        self.assertEqual(self.grade_with(m), "PASS")

    def test_many_crossings_spread_out_pass(self):
        # CONTROL: 40 crossings of one edge in all, 400 frames apart: at most 8 in any 3,000 frames
        m = stop_and_restart(Planted(self.tmp / "r"), 8, gap=400).measures()
        self.assertEqual((m["edge_window"]["crossings"], m["edge_window"]["max"]), (40, 8))
        self.assertEqual(self.grade_with(m), "PASS")

    def test_news_does_not_excuse_the_window(self):
        # the window ignores news by design (round 2's D2w): 12 crossings within 1,200 frames with novelty between FAIL
        p = Planted(self.tmp / "r").say(intent_line())
        for at in range(1, 13):
            src, dst = (R104, PC) if at % 2 else (PC, R104)
            p.say(novelty_line(2000 + 100 * at - 50))
            p.cross(src, dst, 2000 + 100 * at)
        m = p.measures()
        self.assertEqual(m["alternation"]["max"], 1)
        self.assertEqual(m["edge_window"]["max"], 12)
        self.assertEqual(self.grade_with(m), "FAIL")

    def test_two_edges_never_pool_in_the_window(self):
        p = Planted(self.tmp / "r").say(intent_line())
        frame = 2000
        for _ in range(4):
            for src, dst in ((PC, R104), (R104, PC), ("ROUTE102", PC), (PC, "ROUTE102")):
                frame += 100
                p.cross(src, dst, frame)
        m = p.measures()
        self.assertEqual((m["edge_window"]["crossings"], m["edge_window"]["max"]), (16, 8))
        self.assertEqual(self.grade_with(m), "PASS")

    def test_an_unframed_crossing_is_not_read_and_the_batch_is_vacuous(self):
        # strict: a crossing line without '(actor, f<N>)' cannot be placed in a window; the run is not read
        p = stop_and_restart(Planted(self.tmp / "r"), 1)
        p.say(f"[AI-WORLD] MAP {PC} -> {R104} at (39, 63): the left edge from (0, 13); 993 tiles of it known")
        m = p.measures()
        self.assertEqual(m["edge_window"]["unframed"], 1)
        checks = K.grade_batch([row(f"R{i}") for i in range(5)] + [row("R5", measures=m)])
        self.assertEqual(by_id(checks, "K8.EDGE_WINDOW").status, "VACUOUS")
        self.assertIn("R5 1", by_id(checks, "K8.EDGE_WINDOW").text)
        self.assertEqual(K.batch_verdict(checks), "FAIL")

    def test_warps_do_not_count(self):
        p = Planted(self.tmp / "r").say(intent_line())
        for at in range(1, 13):
            p.warp(R104, WOODS, (16, 38), (10, 38), 2000 + 100 * at) if at % 2 else \
                p.warp(WOODS, R104, (10, 39), (16, 38), 2000 + 100 * at)
        self.assertEqual(p.measures()["edge_window"]["max"], 0)

    # (changed on purpose, the orchestrator's ruling, 06 2026-10-31) K8.EDGE_WINDOW is REPORTED: it is measured and shown,
    # and an over-the-window run is flagged FAIL in its own line, but it never decides the batch's verdict
    def test_planted_rows_over_the_window_are_reported_never_counted(self):
        over = K.grade_batch(six(window=11), frozen=(True, "ok"), leftover=[])
        self.assertEqual(by_id(over, "K8.EDGE_WINDOW").status, "FAIL")
        self.assertEqual(K.batch_verdict(over), "PASS")
        self.assertEqual(K.batch_verdict(K.grade_batch(six(window=10), frozen=(True, "ok"), leftover=[])), "PASS")

    def test_it_is_reported_and_in_the_bounds(self):
        self.assertEqual(K.EDGE_WINDOW_KIND, "REPORTED")
        check = by_id(K.grade_batch(six()), "K8.EDGE_WINDOW")
        self.assertEqual(check.kind, "REPORTED")
        self.assertIn("<= 10", check.text)
        self.assertIn("K8.EDGE_WINDOW (information, never counted): in every run, at most 10 crossings", K.BOUNDS_TEXT)
        self.assertGreater(K.BOUNDS_TEXT.index("K8.EDGE_WINDOW"), K.BOUNDS_TEXT.index("REPORTED (information"))


# ---------------------------------------------------------------------------------------------------- the woods exit
class WoodsTests(Temp):
    def run_with(self, steps, start_frame: int = 1000) -> dict:
        p = Planted(self.tmp / f"w{len(list(self.tmp.iterdir()))}", start_frame)
        p.say(intent_line())
        for step in steps:
            step(p)
        return p.measures()

    def test_an_exit_at_y38_does_not_count_and_one_at_y30_from_14_5_does(self):
        south = self.run_with([lambda p: p.warp(WOODS, R104, (10, 38), (16, 38), 5000)])
        self.assertIsNone(south["north_log"])
        self.assertIsNone(south["north_world"])
        self.assertFalse(K.woods_counted({"measures": south}))
        north = self.run_with([lambda p: p.warp(WOODS, R104, (10, 30), (14, 5), 6000)])
        self.assertTrue(north["north_log"]["by_woods"], north["north_log"])
        self.assertTrue(north["north_world"]["by_woods"], north["north_world"])
        self.assertTrue(K.woods_counted({"measures": north}))
        # the other north warp counts too
        other = self.run_with([lambda p: p.warp(WOODS, R104, (11, 30), (15, 5), 6000)])
        self.assertTrue(K.woods_counted({"measures": other}))

    def test_the_east_warp_does_not_count(self):
        m = self.run_with([lambda p: p.warp(WOODS, R104, (10, 30), (37, 38), 6000)])
        self.assertFalse(m["north_log"]["by_woods"])
        self.assertFalse(K.woods_counted({"measures": m}))

    def test_an_earlier_north_arrival_from_rustboro_is_the_first_and_does_not_count(self):
        m = self.run_with([lambda p: p.cross(RUST, R104, 5000, side="down"),
                           lambda p: p.warp(WOODS, R104, (10, 30), (14, 5), 6000)])
        # the edge line arrives at y 63 in this planting; plant a real north arrival from Rustboro instead
        self.assertTrue(K.woods_counted({"measures": m}))
        p = Planted(self.tmp / "rust").say(intent_line())
        p.log.append(f"[AI-WORLD] MAP {RUST} -> {R104} at (19, 0): the down edge from (19, 59) (the AI, f5000); 165 tiles "
                     f"of it known")
        p.transitions.append([5000, KEYS[RUST], KEYS[R104], "connection", "ai", [19, 59], [19, 0], "down"])
        p.lines.append(p._line())
        p.warp(WOODS, R104, (10, 30), (14, 5), 6000)
        m2 = p.measures()
        self.assertEqual(m2["north_log"]["src"], RUST)
        self.assertFalse(K.woods_counted({"measures": m2}))

    def test_a_log_the_world_memory_does_not_back_does_not_count(self):
        m = self.run_with([lambda p: p.warp(WOODS, R104, (10, 30), (14, 5), 6000, world=False)])
        self.assertTrue(m["north_log"]["by_woods"])
        self.assertIsNone(m["north_world"])
        self.assertFalse(K.woods_counted({"measures": m}))

    def test_a_transition_from_before_the_run_does_not_count_for_the_world(self):
        m = self.run_with([lambda p: p.warp(WOODS, R104, (10, 30), (14, 5), 600)], start_frame=1000)
        self.assertIsNone(m["north_world"])

    def test_five_of_six_pass_and_four_of_six_fail(self):
        five = [row(f"R{i}") for i in range(5)] + [row("R5", woods=False, visited=0)]
        self.assertEqual(by_id(K.grade_batch(five), "K8.WOODS").status, "PASS")
        four = [row(f"R{i}") for i in range(4)] + [row(f"R{i}", woods=False, visited=0) for i in (4, 5)]
        self.assertEqual(by_id(K.grade_batch(four), "K8.WOODS").status, "FAIL")

    def test_the_game_showing_rustboro_where_the_instruments_do_not_fails(self):
        rows = six(woods=False, visited=1)
        check = by_id(K.grade_batch(rows), "K8.WOODS")
        self.assertEqual(check.status, "FAIL")
        self.assertIn("R5", check.text)


# ---------------------------------------------------------------------------------------------------- the world size
class WorldSizeTests(Temp):
    def sized(self, size: int) -> dict:
        path = self.tmp / "world.jsonl"
        with open(path, "wb") as handle:
            handle.truncate(size)
        record = K.measure_then_delete(path)
        self.assertFalse(path.exists(), "the file must be deleted after its size is recorded")
        return record

    def test_a_301_mb_world_file_fails(self):
        record = self.sized(301_000_000)
        self.assertEqual(record["bytes"], 301_000_000)
        rows = [row(f"R{i}") for i in range(5)] + [row("R5", world_bytes=record["bytes"])]
        self.assertEqual(by_id(K.grade_batch(rows), "K8.WORLD_SIZE").status, "FAIL")

    def test_a_world_file_under_300_mb_passes(self):
        record = self.sized(299_999_999)
        rows = [row(f"R{i}") for i in range(5)] + [row("R5", world_bytes=record["bytes"])]
        self.assertEqual(by_id(K.grade_batch(rows), "K8.WORLD_SIZE").status, "PASS")

    def test_exactly_300_mb_is_not_under(self):
        rows = six(world_bytes=300_000_000)
        self.assertEqual(by_id(K.grade_batch(rows), "K8.WORLD_SIZE").status, "FAIL")

    def test_an_unmeasured_world_is_vacuous(self):
        rows = six(world_bytes=None)
        self.assertEqual(by_id(K.grade_batch(rows), "K8.WORLD_SIZE").status, "VACUOUS")

    def test_a_crashed_child_still_has_its_world_measured_and_deleted_and_is_not_judged(self):
        build, out = self.tmp / "build", self.tmp / "out"
        job = K.jobs_of(K.SEEDS[0])[0]
        run_dir = build / "profiles" / job["profile"] / "ai_player_runs" / "20261101-000000-X"
        p = ping_pong(Planted(run_dir), 3)
        p.write()
        size = (run_dir / "world.jsonl").stat().st_size
        salvaged = K.salvage(job, build, out)
        self.assertFalse((run_dir / "world.jsonl").exists())
        self.assertEqual(salvaged["world_file"]["bytes"], size)
        self.assertTrue((out / "rows" / f"{job['name']}.json").is_file())
        self.assertTrue((out / job["name"] / "world_last.jsonl").is_file())
        checks = K.grade_batch([row(f"R{i}") for i in range(5)] + [salvaged], frozen=(True, "ok"), leftover=[])
        self.assertEqual(by_id(checks, "K8.PURITY").status, "VACUOUS")
        self.assertEqual(by_id(checks, "K8.THIS_RUN").status, "VACUOUS")
        self.assertEqual(by_id(checks, "K8.WORLD_SIZE").status, "PASS")
        self.assertEqual(K.batch_verdict(checks), "FAIL")
        # no folder at all: nothing to salvage
        self.assertIsNone(K.salvage(K.jobs_of(K.SEEDS[0])[1], build, out))

    def test_the_last_line_is_kept_and_the_stream_counts_lines(self):
        p = ping_pong(Planted(self.tmp / "r"), 3)
        p.write()
        keep = self.tmp / "kept" / "world_last.jsonl"
        world = K.stream_world(p.dir / "world.jsonl", keep)
        self.assertEqual(world["lines"], 4)
        self.assertEqual(json.loads(keep.read_bytes())["transitions"][-1][0], 2300)


# ---------------------------------------------------------------------------------------------------- L5.THIS_RUN
class ThisRunTests(unittest.TestCase):
    def run_of(self, mtime_offset: float):
        from ai_player.gates import live_step5 as L5

        run = L5.Run(L5.Arm("T", "t", 1000, 10.0, {}, fresh=False, state_from="START"))
        run.started = time.time()
        run.state_mtime = run.started + mtime_offset
        run.before = {"frame": 100, "state_md5": "start"}
        run.after = {"frame": 1100, "state_md5": "end"}
        run.verdict = {"counters": {"real_frames": 1000}}
        L5.check_after_is_this_run(run)
        return run

    def test_a_stale_end_state_fails(self):
        run = self.run_of(-100.0)  # written 100 s BEFORE this run started: an earlier run's state
        self.assertEqual([c.status for c in run.checks], ["FAIL"])
        r = row("R5", this_run=run.checks[0].status)
        rows = [row(f"R{i}") for i in range(5)] + [r]
        self.assertEqual(by_id(K.grade_batch(rows), "K8.THIS_RUN").status, "FAIL")

    def test_a_fresh_end_state_passes(self):
        run = self.run_of(5.0)
        self.assertEqual([c.status for c in run.checks], ["PASS"])
        rows = [row(f"R{i}") for i in range(5)] + [row("R5", this_run=run.checks[0].status)]
        self.assertEqual(by_id(K.grade_batch(rows), "K8.THIS_RUN").status, "PASS")

    def test_check_rows_carry_the_id(self):
        run = self.run_of(5.0)
        self.assertEqual(K.check_rows(run.checks)[0]["id"], "L5.THIS_RUN")


# ---------------------------------------------------------------------------------------------------- the ledger
class LedgerTests(Temp):
    def starts(self) -> Path:
        root = self.tmp / "starts"
        for folder, _ in K.STARTS.values():
            (root / folder).mkdir(parents=True)
            for name in K.START_FILES:
                (root / folder / name).write_bytes(f"{folder}/{name}".encode())
        return root

    def test_register_then_a_changed_bound_is_refused(self):
        path = self.tmp / "ledger.json"
        starts = self.starts()
        numbers = K.registered_numbers(K.SEEDS, starts)
        K.register(K.SEEDS, numbers, "test", path=path)
        saved = K.ALT_MAX
        try:
            K.ALT_MAX = 6  # a bound loosened after registration
            changed = K.registered_numbers(K.SEEDS, starts)
        finally:
            K.ALT_MAX = saved
        self.assertNotEqual(ledger.numbers_sha256(numbers), ledger.numbers_sha256(changed))
        with self.assertRaises(ledger.Refused) as caught:
            K.begin("graded", K.SEEDS, changed, "tree", path=path)
        self.assertIn("NOT the ones registered", str(caught.exception))
        # a changed START file is refused the same way
        (starts / K.STARTS["CH2"][0] / "world.jsonl").write_bytes(b"another memory")
        with self.assertRaises(ledger.Refused):
            K.begin("graded", K.SEEDS, K.registered_numbers(K.SEEDS, starts), "tree", path=path)

    def test_the_registered_numbers_begin(self):
        path = self.tmp / "ledger.json"
        starts = self.starts()
        numbers = K.registered_numbers(K.SEEDS, starts)
        K.register(K.SEEDS, numbers, "test", path=path)
        entry, lines = K.begin("graded", K.SEEDS, numbers, "tree", path=path)
        self.assertEqual(entry["status"], "started")
        self.assertIn("GRADED, HELD-OUT seeds 5972-5977", lines[0])

    def test_an_unregistered_graded_batch_is_refused(self):
        numbers = K.registered_numbers(K.SEEDS, self.starts())
        with self.assertRaises(ledger.Refused):
            K.begin("graded", K.SEEDS, numbers, "tree", path=self.tmp / "ledger.json")

    def test_no_other_ledger_entry_names_the_seeds(self):
        named = K.seeds_named(*K.SEEDS)
        self.assertEqual([e["id"] for e in named if e["driver"] != K.DRIVER], [])
        self.assertEqual(K.SEEDS, (5972, 5977))

    def test_the_ai_code_hash_ignores_line_endings_and_sees_a_change(self):
        def tree(name: str, body: bytes) -> Path:
            root = self.tmp / name
            (root / "ai_player" / "brain").mkdir(parents=True)
            (root / "ai_player" / "brain" / "goals.py").write_bytes(body)
            (root / "ai_player" / "gates").mkdir()
            (root / "ai_player" / "gates" / "x.py").write_bytes(name.encode())  # gates/ is not the AI's code
            (root / "ai_player" / "README.md").write_bytes(name.encode())  # nor are documents
            return root
        lf = tree("lf", b"a = 1\nb = 2\n")
        crlf = tree("crlf", b"a = 1\r\nb = 2\r\n")
        changed = tree("changed", b"a = 1\nb = 3\n")
        self.assertEqual(K.ai_code_sha256(lf), K.ai_code_sha256(crlf))
        self.assertNotEqual(K.ai_code_sha256(lf), K.ai_code_sha256(changed))

    def test_missing_start_files_refuse(self):
        with self.assertRaises(SystemExit):
            K.registered_numbers(K.SEEDS, self.tmp / "nowhere")

    def test_the_bounds_text_says_how_news_is_read(self):
        for needle in ("(N1)", "(N2)", "(N3)", "(N4)", "tiles_learned", "novelty at f", "unordered pair",
                       "<= 5", "300,000,000" if False else "300000000", "(14, 5)", "y < 31", "VISITED_RUSTBORO_CITY"):
            self.assertIn(needle, K.BOUNDS_TEXT, needle)


# ---------------------------------------------------------------------------------------------------- purity, verdict
class PurityTests(unittest.TestCase):
    def test_a_launch_not_clean_fails(self):
        self.assertEqual(by_id(K.grade_batch(six(purity="FAIL")), "K8.PURITY").status, "FAIL")

    def test_every_launch_clean_passes(self):
        self.assertEqual(by_id(K.grade_batch(six()), "K8.PURITY").status, "PASS")

    def test_the_ended_check_is_not_purity(self):
        rows = six()
        self.assertTrue(all(c["status"] == "FAIL" for r in rows for c in r["checks"] if c["id"] == "L5.PURITY_ENDED"))
        self.assertEqual(K.batch_verdict(K.grade_batch(rows, frozen=(True, "ok"), leftover=[])), "PASS")


class VerdictTests(unittest.TestCase):
    def test_a_healthy_batch_passes(self):
        checks = K.grade_batch(six(), frozen=(True, "unchanged"), leftover=[])
        self.assertEqual(K.batch_verdict(checks), "PASS", [c for c in checks if c.status != "PASS"])

    def test_five_rows_are_vacuous_and_fail(self):
        checks = K.grade_batch([row(f"R{i}") for i in range(5)], frozen=(True, "ok"), leftover=[])
        self.assertEqual({c.status for c in checks if c.kind == "GRADED" and c.id not in ("K8.FROZEN", "K8.LEFTOVER")},
                         {"VACUOUS"})
        self.assertEqual(K.batch_verdict(checks), "FAIL")

    def test_rustboro_is_reported_and_never_counts(self):
        rows = [row(f"R{i}") for i in range(3)] + [row(f"R{i}", visited=0) for i in (3, 4, 5)]
        checks = K.grade_batch(rows, frozen=(True, "ok"), leftover=[])
        rust = by_id(checks, "K8.RUSTBORO")
        self.assertEqual((rust.kind, rust.status), ("REPORTED", "FAIL"))
        self.assertEqual(K.batch_verdict(checks), "PASS")

    def test_a_frozen_tree_move_and_a_leftover_process_fail(self):
        self.assertEqual(K.batch_verdict(K.grade_batch(six(), frozen=(False, "moved"), leftover=[])), "FAIL")
        self.assertEqual(K.batch_verdict(K.grade_batch(six(), frozen=(True, "ok"), leftover=["123 x"])), "FAIL")

    def test_every_check_quotes_its_bound(self):
        checks = K.grade_batch(six(), frozen=(True, "ok"), leftover=[])
        self.assertIn("at least 5 of 6", by_id(checks, "K8.WOODS").text)
        self.assertIn("<= 5", by_id(checks, "K8.ALTERNATION").text)
        self.assertIn("300000000", by_id(checks, "K8.WORLD_SIZE").text)
        lines = K.check_lines(checks)
        self.assertTrue(any(line.startswith("B1 DEBT K8.WOODS") for line in lines))


class ImportTests(Temp):
    def test_the_driver_takes_no_value_from_the_ai(self):
        from ai_player.gates.check_grader_imports import scan

        self.assertEqual(scan(REPO, ("ai_player.gates.live_ki128",)), [])

    def test_the_walk_sees_an_ai_import_planted_in_the_driver(self):
        from ai_player.gates.check_grader_imports import scan

        root = self.tmp / "copy"
        for path in (REPO / "ai_player").rglob("*.py"):
            rel = path.relative_to(REPO)
            if rel.parts[1] == "evidence":
                continue
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, root / rel)
        driver = root / "ai_player" / "gates" / "live_ki128.py"
        driver.write_text(driver.read_text(encoding="utf-8").replace(
            "from ai_player.gates import ledger  # noqa: E402",
            "from ai_player.gates import ledger  # noqa: E402\nfrom ai_player.brain.goals import open_way  # noqa: E402"),
            encoding="utf-8")
        self.assertTrue(scan(root, ("ai_player.gates.live_ki128",)))


class ReaderTests(unittest.TestCase):
    REAL = [
        "[AI-WORLD] intent 'travel to PETALBURG_WOODS': budget 4500 frames; on ROUTE104 at (39, 63); 12413 tiles known on 27 maps",
        "[AI-WORLD] MAP ROUTE104 -> PETALBURG_WOODS at (16, 38): the warp at (10, 38) (the AI, f620435); 636 tiles of it known",
        "[AI-WORLD] novelty at f623622: experience gained (PID aaad4c0c: 2686 -> 2725): progress (the intent's clock f621773 -> f623622)",
        "[AI-HANDS] [AI-GOALS] MILESTONE ch3_woods done at f639165 (PETALBURG WOODS: the TEAM AQUA GRUNT bothering the DEVON researcher): VAR_PETALBURG_WOODS_STATE=1 (>= 1)",
        "[AI-WORLD] MAP PETALBURG_WOODS -> ROUTE104 at (11, 30): the warp at (15, 5) (the AI, f689171); 1585 tiles of it known",
        "[AI-WORLD] MAP ROUTE104 -> RUSTBORO_CITY at (19, 59): the up edge from (19, 0) (the AI, f714114); 165 tiles of it known",
        "[AI-WORLD] MAP PETALBURG_CITY_HOUSE1 -> PETALBURG_CITY at (7, 15): the warp at (3, 8) (a scene, f490100); 993 tiles of it known",
        "[AI-HANDS] [AI-GOALS] goal go not done: stuck: ping-pong: the edge 0:19|edge:right crossed 3 times (f482448..f482640) with nothing new",
    ]

    def test_real_lines_are_read(self):
        log = K.parse_log(self.REAL)
        self.assertEqual(log["intents"], 1)
        self.assertEqual(len(log["maps"]), 4)
        edge = log["maps"][2]
        self.assertEqual((edge["kind"], edge["dir"], edge["depart"], edge["frame"], edge["intent"]),
                         ("edge", "up", [19, 0], 714114, 1))
        self.assertEqual(log["maps"][3]["actor"], "a scene")
        self.assertEqual(log["novelty"], [{"line": 2, "frame": 623622}])
        self.assertEqual(log["milestones"][0]["id"], "ch3_woods")
        self.assertEqual(log["edge_stops"], 1)
        north = K.first_north_log(log)
        self.assertEqual((north["frame"], north["by_woods"]), (689171, True))

    def test_the_bounds_and_numbers_hash_is_stable(self):
        self.assertEqual(ledger.numbers_sha256({"a": K.BOUNDS_TEXT}), ledger.numbers_sha256({"a": K.BOUNDS_TEXT}))


if __name__ == "__main__":
    unittest.main()
