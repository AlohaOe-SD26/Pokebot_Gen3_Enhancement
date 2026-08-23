"""P4f fault-injection harness. Runs a probe in-process with production facts monkeypatched.

Usage: py -3.12 harness.py <probe.py> <injection-name> [-- probe args...]
Never modifies the repo working tree; all patches are in-memory.
"""
import os, sys, runpy, pathlib, traceback

REPO = pathlib.Path(r"C:/Remote Projects/Pokebot_Gen3_Enhancement")
SD = REPO / "tools" / "story-dev"
BUILD = REPO / "sandbox-pokebot"
sys.path.insert(0, str(BUILD))
os.chdir(SD)

probe = sys.argv[1]
injection = sys.argv[2]
probe_args = sys.argv[3:]

# ---- SAFETY: force is_test_run=True so no probe can write profiles/<name>/current_state.ss1
import modules.libmgba as _lm
_Real = _lm.LibmgbaEmulator
class _TestEmu(_Real):
    def __init__(self, profile, cb, is_test_run=False):
        super().__init__(profile, cb, is_test_run=True)
_lm.LibmgbaEmulator = _TestEmu
print(f"[harness] LibmgbaEmulator forced to is_test_run=True (no profile writes)")

# ---- INJECTIONS -------------------------------------------------------------
if injection == "none":
    print("[harness] injection: NONE (baseline)")

elif injection == "chapters_reversed":
    # probe_chapter_order asserts: detect_live() on post_mossdeep_gym.ss1 names
    # 'Mossdeep & Space Center'. The production fact is the ORDER of CHAPTERS.
    import modules.story.chapters as ch
    lst = ch.CHAPTERS
    idx = {c.name: i for i, c in enumerate(lst)}
    a = idx["Mossdeep & Space Center"]
    b = idx["Gym 7 - Tate & Liza"] if "Gym 7 - Tate & Liza" in idx else None
    if b is None:
        # find whatever the gym7 chapter is called
        for i, c in enumerate(lst):
            if "Tate" in c.name or "Gym 7" in c.name:
                b = i
    print(f"[harness] swapping CHAPTERS[{a}] {lst[a].name!r} <-> CHAPTERS[{b}] {lst[b].name!r}")
    lst[a], lst[b] = lst[b], lst[a]

elif injection == "chapters_order_bug":
    # Reproduce the ACTUAL KI-61 defect: Space Center listed BEFORE the gym.
    # ‼ BADGES_BEFORE is computed at import time, so the swap must be followed by a
    # recompute or the injection is inert (measured: a bare swap left the probe green).
    import modules.story.chapters as ch
    lst = ch.CHAPTERS
    idx = {c.key: i for i, c in enumerate(lst)}
    a, b = idx["18"], idx["19"]
    print(f"[harness] swapping CHAPTERS[{a}] {lst[a].name!r} <-> CHAPTERS[{b}] {lst[b].name!r}")
    lst[a], lst[b] = lst[b], lst[a]
    ch.BADGES_BEFORE.clear()
    ch.BADGES_BEFORE.update(ch._compute_badges_before())
    print(f"[harness] BADGES_BEFORE recomputed: ch18={ch.BADGES_BEFORE['18']} ch19={ch.BADGES_BEFORE['19']}")

elif injection == "victim_is_surf_carrier":
    # probe_slot_free_plan's headline claim: "the deposit does NOT take a Surf carrier".
    # Make the production victim chooser pick the Surf carrier.
    import modules.story.team_policy as tp
    tp.find_dead_weight = lambda views: [(1, "INJECTED: pick the Surf carrier")]
    print("[harness] team_policy.find_dead_weight() patched -> always returns slot 1 (Zigzagoon, the sole Surf carrier)")

elif injection == "not_blocked":
    # probe_slot_free_plan's other claim: hm_learner_slot(HM08) is None and party is full.
    import modules.story.early_game as eg
    eg.hm_learner_slot = lambda item: 3
    print("[harness] early_game.hm_learner_slot() patched -> always returns slot 3 (i.e. NOT blocked)")

elif injection == "bag_empty_and_flags_false":
    import modules.memory as mem
    mem.get_event_flag = lambda name: False
    import modules.items as it
    real_bag = it.get_item_bag
    class _Empty:
        def quantity_of(self, item): return 0
    it.get_item_bag = lambda: _Empty()
    print("[harness] get_event_flag()->False and get_item_bag() emptied: EVERY Regi capability is now MISSING")

elif injection == "no_dive_party_no_badge":
    import modules.memory as mem
    mem.get_event_flag = lambda name: False
    import modules.pokemon_party as pp
    pp.get_party = lambda *a, **k: [None] * 6
    print("[harness] get_event_flag()->False and get_party()->empty: can_dive() preconditions now FALSE")

elif injection == "no_land_dive_tables":
    # probe_dive_learner section 3 claims LAND tables host a Dive learner. Make every
    # encounter-index slot a non-grass method so `rows` ends up EMPTY.
    import json as _json
    _real_loads = _json.loads
    def _loads(text, *a, **k):
        obj = _real_loads(text, *a, **k)
        if isinstance(obj, dict) and "index" in obj and isinstance(obj["index"], dict):
            n = 0
            for locs in obj["index"].values():
                if isinstance(locs, list):
                    for slot in locs:
                        if isinstance(slot, dict) and str(slot.get("method", "")).strip().lower() == "grass":
                            slot["method"] = "surf"
                            n += 1
            print(f"[harness] encounter index: rewrote {n} 'grass' slots -> 'surf' (no LAND table left)")
        return obj
    _json.loads = _loads
    print("[harness] json.loads patched for the encounter index")

elif injection == "break_evo_control":
    import json as _json
    _real_loads = _json.loads
    def _loads(text, *a, **k):
        obj = _real_loads(text, *a, **k)
        return obj
    print("[harness] noop")

elif injection == "hide_dive_move":
    # probe_dive_learner's FIRST guard: it resolves move ids from moves.json by NAME.
    import json as _json
    _real_loads = _json.loads
    def _loads(text, *a, **k):
        obj = _real_loads(text, *a, **k)
        entries = list(obj.values()) if isinstance(obj, dict) else obj
        if isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict) and e.get("name") == "Dive":
                    e["name"] = "Div3"
                    print("[harness] moves.json: renamed 'Dive' -> 'Div3' (id now unresolvable)")
        return obj
    _json.loads = _loads

elif injection == "strip_gym_whiteout_guard":
    import types
    src_path = BUILD / "modules" / "story" / "mossdeep_gym.py"
    src = src_path.read_text(encoding="utf-8")
    needle = (" " * 8) + "if not _on_gym_map():"
    n = src.count(needle)
    print("[harness] 8-space guard sites: %d (first = require_in_gym, the in-loop guard [1]/[2] test)" % n)
    if n != 2:
        raise SystemExit("shape changed - refusing to report a result")
    new = src.replace(needle, (" " * 8) + "if False:  # INJECTED: require_in_gym guard removed", 1)
    mod = types.ModuleType("modules.story.mossdeep_gym")
    mod.__file__ = str(src_path)
    mod.__package__ = "modules.story"
    sys.modules["modules.story.mossdeep_gym"] = mod
    exec(compile(new, str(src_path), "exec"), mod.__dict__)
    print("[harness] mossdeep_gym re-execd; require_in_gym no longer raises")

elif injection == "gym_guard_wrong_type":
    import types
    src_path = BUILD / "modules" / "story" / "mossdeep_gym.py"
    src = src_path.read_text(encoding="utf-8")
    needle = "else BotModeError)("
    n = src.count(needle)
    print("[harness] require_in_gym raise sites matched: %d" % n)
    if n != 1:
        raise SystemExit("shape changed - refusing to report a result")
    new = src.replace(needle, "else RuntimeError)(")
    mod = types.ModuleType("modules.story.mossdeep_gym")
    mod.__file__ = str(src_path)
    mod.__package__ = "modules.story"
    sys.modules["modules.story.mossdeep_gym"] = mod
    exec(compile(new, str(src_path), "exec"), mod.__dict__)
    print("[harness] the whiteout guard now raises RuntimeError, not BotModeError")

elif injection == "detect_live_lies":
    # Break the CONSUMER instead: make detect_live report the wrong chapter name.
    import modules.story.progress as pg
    real = pg.detect_live
    def liar(*a, **k):
        r = real(*a, **k)
        try:
            object.__setattr__(r, "chapter_name", "TOTALLY BOGUS CHAPTER")
        except Exception:
            r = r._replace(chapter_name="TOTALLY BOGUS CHAPTER")
        return r
    pg.detect_live = liar
    print("[harness] detect_live() patched to always answer 'TOTALLY BOGUS CHAPTER'")

elif injection == "party_empty":
    # probe_slot_free_plan / probe_regi_capabilities / probe_dive_routing all read get_party().
    import modules.pokemon_party as pp
    pp.get_party = lambda *a, **k: [None] * 6
    print("[harness] get_party() patched to return an EMPTY party (6x None)")

elif injection == "flags_all_false":
    import modules.memory as mem
    mem.get_event_flag = lambda name: False
    print("[harness] get_event_flag() patched to always return False")

elif injection == "no_dive_learners":
    # probe_dive_learner: kill the encounter index rows by making learns() find nothing
    # -> the "no LAND table hosts a Dive learner ... NOT a pass" branch.
    import json as _json
    real_loads = _json.loads
    print("[harness] (handled inside probe via species stub)")

else:
    raise SystemExit(f"unknown injection {injection!r}")

sys.argv = [probe] + probe_args
code = 0
try:
    runpy.run_path(str(SD / probe), run_name="__main__")
except SystemExit as e:
    code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
except BaseException:
    traceback.print_exc()
    code = 99
print(f"[harness] PROBE EXIT CODE = {code}")
sys.stdout.flush()
os._exit(code)
