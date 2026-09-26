r"""GATE — §Ch23 CHUNKED TRAINING: the planner, the identity lookup and the impossible-case refusal.

WHY THIS EXISTS (`#24-ch23training`, USER RULING 14, 2026-09-26)
-----------------------------------------------------------------
`train_for_victory_road` used to REFUSE whenever one battler's climb to L47 was estimated over the
250,000-frame per-call ceiling — and that refusal ended **30 of the 39** badge-8 organic runs of
2026-09-15. It now trains such a climb in CHUNKS (`ch23_chunk_target`), each estimated ≤ the ceiling and
run inside a real-frame purse. Three properties make that safe, and each is checked here WITHOUT a ROM:

  C1  Every refused species of the 2026-09-15 corpus reaches L47 within `CH23_MAX_CHUNKS_PER_MON`, with
      every planned chunk ≤ `MAX_TRAINING_FRAMES` estimated AND ≤ `CH23_CHUNK_PLAN_FRAMES` real.
  C2  THE ORDINARY PATH IS UNCHANGED: the fixture party's battlers (Wailmer L40, Swellow L42, Mightyena
      L44) plan ONE chunk straight to L47 — the same single `train_team(47)` call HEAD made.
  C3  `CH23_UNDERLEVEL_MARGIN` equals `SwapTrainBattleStrategy.UNDERLEVEL_MARGIN` (a local copy that
      could otherwise drift and mis-classify the swap regime).
  C4  `_trainee_by_pid` survives EVOLUTION (Marill → Azumarill, same PID) and the Nincada split
      (Ninjask + Shedinja share a PID: the tracked mon is the evolved one).
  C5  `ch23_swap_finisher_exists` — the loud refusal for the genuinely IMPOSSIBLE plan — is True only when
      ANOTHER non-egg member is ≥ L40 with a damaging, non-banned move.
  C6  The skip-the-fix arm `NOCHUNK` is registered and restores the old refusal (source check, comments
      stripped so a MENTION cannot satisfy it).

FAULT ARMS (run every time): a planner that returns `target` unchanged (no chunking) must FAIL C1, and a
species-keyed lookup must FAIL C4 — a gate that cannot fail is decoration (CLAUDE.md rule 6).
"""
from __future__ import annotations

import io
import sys
import tokenize
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))
for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.context import context  # noqa: E402
from modules.pokemon import get_species_by_name  # noqa: E402
from modules.story import victory_road as VR  # noqa: E402

failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


class Mon:
    """Duck-typed party mon on a REAL species growth curve."""

    def __init__(self, species: str, level: int, pid: int = 0x1234, moves=(("Tackle", 35),)):
        self.species = get_species_by_name(species)
        self.level = level
        self.total_exp = self.species.level_up_type.get_experience_needed_for_level(level)
        self.personality_value = pid
        self.is_egg = False
        self.moves = [types.SimpleNamespace(move=types.SimpleNamespace(name=n, base_power=bp))
                      for n, bp in moves]

    def advance_to(self, level: int):
        self.level = level
        self.total_exp = self.species.level_up_type.get_experience_needed_for_level(level)


def climb(mon: Mon, planner, target=VR.TRAIN_TARGET, wild=40):
    """Simulate the chunk loop's PLAN (not its battles): returns the list of planned chunks."""
    from modules.story.training_areas import estimate_frames_to_level
    chunks = []
    for _ in range(VR.CH23_MAX_CHUNKS_PER_MON):
        if mon.level >= target:
            break
        sub = planner(mon, target, wild)
        est = estimate_frames_to_level(mon, sub, wild)
        factor = (VR.CH23_SWAP_FRAME_FACTOR if mon.level + VR.CH23_UNDERLEVEL_MARGIN <= wild
                  else VR.CH23_SOLO_FRAME_FACTOR)
        chunks.append((mon.level, sub, est, int(est * factor)))
        mon.advance_to(sub)
    return chunks


#: The refused mons of the 2026-09-15 corpus (worst per run), `ai-research-notes/…-organic-frontier-RECON.md`.
CORPUS_REFUSED = [("Marill", 13), ("Slugma", 15), ("Slugma", 19), ("Nincada", 18), ("Dustox", 14),
                  ("Swellow", 36), ("Loudred", 29), ("Loudred", 36), ("Beautifly", 29),
                  ("Mightyena", 30), ("Mightyena", 33), ("Shedinja", 27), ("Ninjask", 26),
                  ("Marshtomp", 34)]


def c1(planner, sink=None) -> None:
    for sp, lv in CORPUS_REFUSED:
        chunks = climb(Mon(sp, lv), planner)
        reached = chunks and chunks[-1][1] >= VR.TRAIN_TARGET
        ok_sizes = all(est <= VR.MAX_TRAINING_FRAMES and real <= VR.CH23_CHUNK_PLAN_FRAMES
                       for _f, _t, est, real in chunks)
        check(bool(reached) and ok_sizes,
              f"C1 {sp} L{lv}: reaches L47 in {len(chunks)} chunk(s), every chunk within the ceiling "
              f"and the plan {[(f, t, est) for f, t, est, _r in chunks]}", sink)


def c4(lookup, sink=None) -> None:
    marill = Mon("Marill", 17, pid=0xAAAA)
    VR.get_party = lambda: [Mon("Sceptile", 51, pid=1), marill]
    marill.species = get_species_by_name("Azumarill")          # evolved mid-chunk, same PID
    got = lookup(0xAAAA, "Marill")
    check(got is marill, "C4 Marill → Azumarill (same PID) is still found", sink)
    ninjask, shedinja = Mon("Ninjask", 20, pid=0xBBBB), Mon("Shedinja", 20, pid=0xBBBB)
    VR.get_party = lambda: [Mon("Sceptile", 51, pid=1), ninjask, shedinja]
    check(lookup(0xBBBB, "Nincada") is ninjask,
          "C4 Nincada → Ninjask + Shedinja (shared PID): the tracked mon is Ninjask", sink)
    VR.get_party = lambda: [Mon("Sceptile", 51, pid=1)]
    check(lookup(0xCCCC, "Marill") is None, "C4 an absent PID resolves to None (never a wrong mon)", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — §Ch23 chunked training (`#24-ch23training`)")
    print("=" * 92)
    try:
        context.config.battle.banned_moves  # noqa: B018 - probe the attribute
    except Exception:  # noqa: BLE001 - no profile loaded in a gate: give it the one field we read
        context.config = types.SimpleNamespace(battle=types.SimpleNamespace(banned_moves=["Dive", "Fly"]))
    banned = list(context.config.battle.banned_moves)

    print("\n== C1 every corpus-refused climb is PLANNED, never refused ==")
    c1(VR.ch23_chunk_target)

    print("\n== C2 the ordinary party plans ONE chunk to L47 (HEAD's single call) ==")
    for sp, lv in (("Wailmer", 40), ("Swellow", 42), ("Mightyena", 44)):
        check(VR.ch23_chunk_target(Mon(sp, lv), VR.TRAIN_TARGET, 40) == VR.TRAIN_TARGET,
              f"C2 {sp} L{lv} → one chunk straight to L{VR.TRAIN_TARGET}")

    print("\n== C3 the swap margin matches the strategy that applies it ==")
    from plugins.custom_modes.story_mode import SwapTrainBattleStrategy
    check(VR.CH23_UNDERLEVEL_MARGIN == SwapTrainBattleStrategy.UNDERLEVEL_MARGIN,
          f"C3 CH23_UNDERLEVEL_MARGIN={VR.CH23_UNDERLEVEL_MARGIN} == "
          f"SwapTrainBattleStrategy.UNDERLEVEL_MARGIN={SwapTrainBattleStrategy.UNDERLEVEL_MARGIN}")

    real_get_party = VR.get_party
    try:
        print("\n== C4 identity by PID survives evolution ==")
        c4(VR._trainee_by_pid)

        print("\n== C5 the impossible-case refusal fires only when no finisher exists ==")
        trainee = Mon("Marill", 13, pid=0xAAAA)
        VR.get_party = lambda: [Mon("Sceptile", 51, pid=1, moves=(("Leaf Blade", 70),)), trainee]
        check(VR.ch23_swap_finisher_exists(0xAAAA, 40), "C5 a L51 mate with a damaging move ⇒ finisher exists")
        VR.get_party = lambda: [Mon("Swellow", 39, pid=2, moves=(("Aerial Ace", 60),)), trainee]
        check(not VR.ch23_swap_finisher_exists(0xAAAA, 40), "C5 no mate ≥ L40 ⇒ NO finisher (refuse loudly)")
        # ⛔ A REAL damaging move that is banned (the list opens with the string "None", the empty-slot
        #   placeholder — testing with it would pass for the wrong reason).
        only_banned = "Dive" if "Dive" in banned else next(n for n in banned if n and n != "None")
        VR.get_party = lambda: [Mon("Wailmer", 45, pid=3, moves=((only_banned, 80), ("Growl", 0))), trainee]
        check(not VR.ch23_swap_finisher_exists(0xAAAA, 40),
              f"C5 a ≥L40 mate with only banned/zero-power moves ({only_banned}, Growl) ⇒ NO finisher")
        VR.get_party = lambda: [Mon("Marill", 45, pid=0xAAAA, moves=(("Surf", 95),))]
        check(not VR.ch23_swap_finisher_exists(0xAAAA, 40), "C5 the trainee never counts as its own finisher")
    finally:
        VR.get_party = real_get_party

    print("\n== C6 the skip-the-fix arm exists and restores the old refusal ==")
    src = (SANDBOX / "modules" / "story" / "victory_road.py").read_text(encoding="utf-8")
    code = tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)
    check('"NOCHUNK": "POKEBOT_CH23_FAULT_NOCHUNK"' in code, "C6 NOCHUNK is registered in FAULT_ARMS")
    check('_fault("NOCHUNK") and worst[1] > MAX_TRAINING_FRAMES' in code and "alone needs" in code,
          "C6 the NOCHUNK branch raises the old 'alone needs N frames' refusal")

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []
    c1(lambda mon, target, wild: target, sink)            # no chunking at all
    check(bool(sink), f"FAULT a planner that never chunks FAILS C1 ({len(sink)} case(s) caught)")
    sink = []

    def species_keyed(pid, species):
        return next((m for m in VR.get_party() if m.personality_value == pid and m.species.name == species), None)
    try:
        c4(species_keyed, sink)
    finally:
        VR.get_party = real_get_party
    check(bool(sink), f"FAULT a (pid, species) lookup FAILS C4 ({len(sink)} case(s) caught)")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
