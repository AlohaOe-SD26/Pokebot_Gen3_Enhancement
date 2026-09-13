"""`#24-wallydecline` — the three-arm proof, plus the phase sweep kept as a MEASURED DEAD END.

⛔⛔ READ THIS BEFORE TRUSTING ANY RUN OF THIS SITE. The Mauville Wally defect is **PHASE-LOCKED,
NOT RANDOM.** `fight_wally_mauville` mashes `"B" if frames % 3 else "A"`; Wally's script reaches
`msgbox …, MSGBOX_YESNO` after a FIXED `Common_Movement_Delay48`; and at a Gen-3 yes/no **B IS "NO"**
(`src/script_menu.c Task_HandleYesNoInput`: `case MENU_B_PRESSED:` falls through to
`gSpecialVar_Result = 0`). Deterministic script timing × deterministic mash ⇒ whichever button lands
on the accept frame lands there for the WHOLE run.
‼ **THEREFORE A SINGLE GREEN RUN AT THIS SITE PROVES NOTHING — MEASURED, NOT FEARED:** the FIRST
repro attempt, against **UNFIXED** code on `mauville_prewattson.ss1`, returned `ACCEPTANCE: PASS`.
Accepting it would have closed the project's largest defect as "cannot reproduce".

================================================================================================
PART 1 — THE PROOF (default). Three arms, all injected INSIDE production code:
  `decline`  force B at the choice box.  MUST WEDGE — it is the causal experiment.
  `mash`     the pre-fix blind masher.   ⚠ EXPECTED TO PASS HERE; that is the point, not a bug.
  `prod`     the fix.                    MUST beat Wally with declined=False and reached_prompt=True.
GRADE: `decline` wedges/declines AND `prod` passes non-vacuously. ⛔ `mash` is NOT graded — it is
printed as the standing demonstration that a lucky pass means nothing.

PART 2 — THE PHASE SWEEP (`--sweep`), KEPT ONLY AS A DOCUMENTED FAILURE.
`POKEBOT_WALLY_PHASE` offsets the mash phase. **It cannot reach the bug.** MEASURED 2026-09-13:
3 phases × 2 arms = **6/6 runs `declined=False beat=True`** (p0 mash and p0 prod byte-identical at
`frames=2078`). ⛔ WHY: identical consecutive presses cancel in `libmgba.press_button:476`, so a
cycle emits `A, B, nothing`; shifting the phase ALSO shifts how fast the three msgboxes advance, so
the box's open frame **co-moves** and the offset partly cancels itself.
⇒ **AN ARM WHOSE FIRING DEPENDS ON LUCK IS NOT AN ARM.** This part is retained so the next reader
does not rebuild the same useless knob; it is NOT a pass/fail gate.

⛔ The STANDING REGRESSION DEFENCE is not this file — it is `probe_yesno_guard.py` (gate #58), which
is STATIC precisely because a behavioural check cannot be trusted for a phase-locked defect.

`DECLINED_WALLY_BATTLE_MAUVILLE` (flag 284) is the ground truth for "we answered NO": set ONLY by
`MauvilleCity_EventScript_DeclineWallyBattle`, and **nothing in the decomp clears it**. That is an
IDENTITY assertion, not a count (SESSION DISCIPLINE #3).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_wally_phase_sweep.py [--sweep] [--rerun]
"""
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVID = HERE / "evidence"
FIXTURE = "mauville_prewattson.ss1"
LINE = "=" * 96


def _read(tag: str) -> dict:
    log = EVID / f"{tag}.log"
    if not log.is_file():
        return {"missing": True}
    text = log.read_text(encoding="utf-8", errors="replace")

    def grab(field: str):
        m = re.search(rf"^\s*{field}\s+(True|False|\d+)\s*$", text, re.M)
        return m.group(1) if m else None

    verdicts = re.findall(r"ACCEPTANCE: (PASS|FAIL)", text)
    return {
        "verdict": verdicts[-1] if verdicts else None,
        "declined": grab("declined_ever"),
        "declined_now": grab("declined_now"),
        "beat": grab("defeated_now"),
        "reached": grab("reached_prompt"),
        "frames": grab("frames"),
        # ⭐ A WEDGE PRINTS NO VERDICT — the harness kills the run first. Absence of a verdict is
        #   therefore SIGNAL here, not a missing measurement, and must be read explicitly.
        "wedged": "HANG CONFIRMED" in text and not verdicts,
    }


def _run(tag: str, env_extra: dict, frames: str, rerun: bool) -> dict:
    if rerun or not (EVID / f"{tag}.log").is_file():
        print(f"  running {tag} …", flush=True)
        env = dict(os.environ, PYTHONUTF8="1")
        env.pop("POKEBOT_WALLY_FAULT", None)
        env.pop("POKEBOT_WALLY_PHASE", None)
        env.update(env_extra)
        EVID.mkdir(exist_ok=True)
        with open(EVID / f"{tag}.stdout.txt", "w", encoding="utf-8") as out:
            subprocess.run(
                [sys.executable, "story_harness.py", FIXTURE, "--driver", "wallymauville",
                 "--frames", frames, "--profile", tag.replace("-", "")[:12],
                 "--log", str(EVID / f"{tag}.log")],
                cwd=HERE, env=env, stdout=out, stderr=subprocess.STDOUT, check=False)
    return _read(tag)


def main() -> int:
    rerun = "--rerun" in sys.argv
    print(LINE)
    print("  PART 1 — THE PROOF (three arms)")
    arms = {
        "decline": _run("wallyarm-decline", {"POKEBOT_WALLY_FAULT": "decline"}, "30000", rerun),
        "mash": _run("wallyarm-mash", {"POKEBOT_WALLY_FAULT": "mash"}, "30000", rerun),
        "prod": _run("wallyarm-prod", {}, "12000", rerun),
    }
    print(f"  {'arm':9} {'verdict':12} {'wedged':7} {'declined':9} {'beat':6} {'reached':8} frames")
    for name, r in arms.items():
        print(f"  {name:9} {str(r.get('verdict')):12} {str(r.get('wedged')):7} "
              f"{str(r.get('declined')):9} {str(r.get('beat')):6} {str(r.get('reached')):8} "
              f"{r.get('frames')}")

    fails = []
    d, p = arms["decline"], arms["prod"]
    if d.get("missing"):
        fails.append("the `decline` arm never ran — without it nothing here is a proof")
    elif not (d.get("wedged") or d.get("declined") == "True" or d.get("declined_now") == "True"):
        fails.append(
            "⛔ THE `decline` ARM NEITHER WEDGED NOR DECLINED. Forcing B at the box is supposed to "
            "reproduce the run-killer; if it does not, either the arm is not reaching production "
            "or the causal story is wrong. DO NOT read a green `prod` as a fix until this fires.")
    if p.get("missing"):
        fails.append("the `prod` arm never ran")
    else:
        if p.get("reached") != "True":
            fails.append("⛔ `prod` is VACUOUS — it never opened a yes/no, so it measured NOTHING")
        if p.get("beat") != "True":
            fails.append("`prod` did not beat Wally")
        if p.get("declined") == "True" or p.get("declined_now") == "True":
            fails.append("⛔ THE FIX LEAKS — production answered NO")

    print(LINE)
    print("  ⚠ `mash` is deliberately NOT graded: it PASSES here by phase luck (frames=2078), and")
    print("    that is the standing demonstration that one green run at this site proves nothing.")

    if "--sweep" in sys.argv:
        print(LINE)
        print("  PART 2 — the phase sweep, kept as a MEASURED DEAD END (not graded)")
        for phase in (0, 1, 2):
            for arm in ("mash", "prod"):
                extra = {"POKEBOT_WALLY_PHASE": str(phase)}
                if arm == "mash":
                    extra["POKEBOT_WALLY_FAULT"] = "mash"
                r = _run(f"wallysweep-p{phase}-{arm}", extra, "90000", rerun)
                print(f"    p{phase} {arm:5} declined={str(r.get('declined')):6} "
                      f"beat={str(r.get('beat')):6} frames={r.get('frames')}")
        print("  ⇒ the knob cannot reach the bug; see this file's docstring for WHY.")

    print(LINE)
    if fails:
        for f in fails:
            print(f"  {f}")
        print("  RESULT: FAIL")
        return 1
    print("  ✅ `decline` reproduces the run-killer; `prod` beats Wally, non-vacuously, never declining.")
    print("  RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
