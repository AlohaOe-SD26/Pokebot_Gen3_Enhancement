# -*- coding: utf-8 -*-
"""DOES THE HEARTBEAT ACTUALLY EMIT? Drive the REAL `debug_logger.on_frame()` past two heartbeats.

⛔⛔ WHY THIS EXISTS, AND WHY IT IS A GATE. On 2026-09-09 a dex-telemetry change put `_last_owned`
into the `global` line of the WRONG FUNCTION (`enable()` instead of `on_frame()`). Because
`on_frame()` assigns that name, Python made it a LOCAL for the whole function, so the read a few
lines earlier raised `UnboundLocalError` on the first healthy heartbeat.
‼ `main.py:101-107` wraps the call in `except Exception: pass` ("Fully guarded so it can never
break/slow the loop") ⇒ the failure was **SILENT AND TOTAL**: every `[hb]` line gone, on every run,
forever — including the `party_ids` field a queued measurement depends on. **A telemetry change that
disables telemetry, invisibly.**

⭐⭐ AND THE TEST THAT MISSED IT IS THE POINT. A stub suite had passed FIVE arms — correct dex set,
correct delta wording, unreadable dex degrades, shrinking set silent, first beat silent. Every arm
was true. **Every arm exercised `_owned_dex()` and the delta arithmetic in ISOLATION; not one called
`on_frame()`.** ⇒ the pieces were proven and the PATH was never run.
   **RULE: TEST THE FUNCTION THE PRODUCTION LOOP CALLS, NOT THE HELPERS IT CALLS.**
   (project rule §7 restated: *instrument the ACTION, not the input to the action*.)

WHAT THIS DOES: stubs only the two emulator-touching readers (`_light_state`, `_owned_dex`), then
calls the REAL `on_frame()` across two full heartbeat intervals and asserts on the REAL log file.
⭐ ARM B FAULT-INJECTS the original bug (strips `_last_owned` from `on_frame`'s `global`) and proves
this repro FAILS when the defect is present — a gate that cannot fail is not a gate.

EXIT 0 = heartbeats emit and the dex delta is reported. EXIT 1 = telemetry is silently broken.
"""
import importlib.util
import pathlib
import sys
import tempfile
import types

sys.stdout.reconfigure(encoding="utf-8")
SB = pathlib.Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"
SRC = SB / "modules" / "debug_logger.py"


def _load(source_text, tag):
    """Load a private copy of debug_logger from `source_text` with emulator readers stubbed."""
    d = pathlib.Path(tempfile.mkdtemp(prefix=f"hb-{tag}-"))
    mod_path = d / "dbg.py"
    mod_path.write_text(source_text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"dbg_{tag}", mod_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, d


def _drive(m, profile_dir, owned_sequence):
    """Call the REAL on_frame() across two heartbeats. Returns the log text."""
    prof = types.SimpleNamespace(path=str(profile_dir))
    state = {"i": 0, "frame": 0}
    # ⛔ `on_frame` takes its frame count from `_light_state()["frame"]`, NOT from its argument —
    # a stub without that key leaves `_start_frame` None and the heartbeat can NEVER fire, which
    # is exactly how the first version of this repro produced a false FAIL on correct code.
    m._light_state = lambda: {"mode": "Story", "game_state": "OVERWORLD", "controllable": True,
                              "map": None, "pos": (1, 2), "party_key": ["Torchic:L5"],
                              "frame": state["frame"],
                              "party_ids": ["Torchic#AABBCCDD:L5:exp135"], "message": "",
                              "battle_active": False, "learn_state": None, "balls": 10}
    def _owned():
        v = owned_sequence[min(state["i"], len(owned_sequence) - 1)]
        return set(v)
    m._owned_dex = _owned
    m._cur_mode = lambda: "Story"

    m.enable(profile=prof, name_prefix="TEST-")
    hb = m._HEARTBEAT_EVERY
    err = None
    try:
        for step, fc in enumerate([0, hb, 2 * hb]):
            state["i"] = step
            state["frame"] = fc
            m.on_frame(fc)
    except Exception as e:  # noqa: BLE001 - the whole point is to observe it
        err = e
    path = m._path
    m.disable()
    return (pathlib.Path(path).read_text(encoding="utf-8") if path else ""), err


def main() -> int:
    original = SRC.read_text(encoding="utf-8")
    print("=" * 100)
    print("HEARTBEAT EMISSION — driving the REAL on_frame() past two heartbeats")
    print("=" * 100)

    # ---- ARM A: the tree as it stands -------------------------------------------------------------
    with tempfile.TemporaryDirectory() as td:
        mA, _ = _load(original, "A")
        logA, errA = _drive(mA, pathlib.Path(td), [[1, 4], [1, 4], [1, 4, 183]])
    hbA = [l for l in logA.splitlines() if "[hb]" in l]
    dexA = [l for l in logA.splitlines() if "[DEX]" in l]
    print(f"\n  ARM A — the tree as it stands")
    print(f"    exception      : {errA!r}")
    print(f"    [hb] lines     : {len(hbA)}")
    for l in hbA:
        print(f"        {l.strip()[:118]}")
    print(f"    [DEX] lines    : {len(dexA)}")
    for l in dexA:
        print(f"        {l.strip()[:118]}")
    # ‼ FIELD ASSERTION, ADDED 2026-09-10 — the gate used to check only that heartbeats EXISTED.
    # Every load-bearing field could have been deleted from the f-string and this stayed GREEN,
    # which is the "a checklist protects exactly what it enumerates" shape: it enumerated LINES,
    # so it could not see a missing FIELD. Each name below is depended on by a shipped tool:
    #   party= / ids=  -> `probe_laggard_origin.py`, `probe_dexfence_opportunity.py` (party size)
    #   owned=         -> the `#24-dexhunt` A/B grade (dex strictly increasing)
    #   balls=         -> `#24-dexhunt`'s ball clause; a `[BALLS]` delta only fires on a CHANGE,
    #                     so a run parked at 1 ball emits nothing and reads like one at 30.
    REQUIRED_HB_FIELDS = ("party=", "ids=", "owned=", "balls=", "money=")  # money= : #26-ch23money F0
    missingA = sorted({f for f in REQUIRED_HB_FIELDS if any(f not in l for l in hbA)})
    print(f"    required fields: {'all present' if not missingA else 'MISSING ' + ', '.join(missingA)}")
    okA = (
        errA is None
        and len(hbA) >= 2
        and len(dexA) == 1
        and "+#183" in "".join(dexA)
        and not missingA
    )

    # ---- ARM B: FAULT-INJECT the original bug -----------------------------------------------------
    broken = original.replace("    global _prev, _stall_frames, _last_sig, _last_dump_stall, _start_frame\n"
                              "    global _last_owned\n",
                              "    global _prev, _stall_frames, _last_sig, _last_dump_stall, _start_frame\n", 1)
    injected = broken != original
    with tempfile.TemporaryDirectory() as td:
        mB, _ = _load(broken, "B")
        logB, errB = _drive(mB, pathlib.Path(td), [[1, 4], [1, 4], [1, 4, 183]])
    hbB = [l for l in logB.splitlines() if "[hb]" in l]
    print(f"\n  ARM B — FAULT-INJECTED (`_last_owned` removed from on_frame's `global`)")
    print(f"    injected       : {injected}")
    print(f"    exception      : {type(errB).__name__ if errB else None}: {errB}")
    print(f"    [hb] lines     : {len(hbB)}   ⇐ 0 means telemetry is SILENTLY DEAD")
    okB = injected and errB is not None and len(hbB) < len(hbA)

    # ---- ARM C: prove the FIELD assertion itself can fail -----------------------------------------
    # ⛔ AN ASSERTION ADDED WITHOUT AN ARM IS DECORATION. ARM B proves the gate catches telemetry
    # that is DEAD; it cannot prove the gate catches telemetry that is ALIVE BUT INCOMPLETE — the
    # heartbeats still emit, no exception is raised, and every one of ARM B's checks passes. So
    # this arm deletes exactly one field from the f-string and requires ARM A's check to go RED.
    dropped = original.replace('f"balls={st.get(\'balls\')} "\n', "", 1)
    dropped_ok = dropped != original
    hbC: list[str] = []
    if dropped_ok:
        with tempfile.TemporaryDirectory() as td:
            mC, _ = _load(dropped, "C")
            logC, _errC = _drive(mC, pathlib.Path(td), [[1, 4], [1, 4], [1, 4, 183]])
        hbC = [l for l in logC.splitlines() if "[hb]" in l]
    missingC = sorted({f for f in REQUIRED_HB_FIELDS if any(f not in l for l in hbC)})
    okC = dropped_ok and len(hbC) >= 2 and missingC == ["balls="]
    print("\n  ARM C — FIELD-DROP (`balls=` deleted from the heartbeat f-string)")
    print(f"    dropped        : {dropped_ok}")
    print(f"    [hb] lines     : {len(hbC)}   ⇐ still emitting: this is the ALIVE-BUT-INCOMPLETE case")
    print(f"    detected as    : {'MISSING ' + ', '.join(missingC) if missingC else 'nothing missing ⇒ GATE IS BLIND'}")

    print("\n" + "=" * 100)
    print(f"  [{'OK  ' if okA else 'FAIL'}] ARM A: heartbeats emit, dex gain reported once, all fields present")
    print(f"  [{'OK  ' if okB else 'FAIL'}] ARM B: removing the fix BREAKS it ⇒ this repro can fail")
    print(f"  [{'OK  ' if okC else 'FAIL'}] ARM C: dropping ONE field is CAUGHT ⇒ the field check is live")
    good = okA and okB and okC
    print(("  PASS — the heartbeat path is exercised end to end." if good
           else "  ⛔ FAIL — see the arms above."))
    print("=" * 100)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
