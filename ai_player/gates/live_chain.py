"""THE GRADED NEW GAME CHAIN HELD-OUT (USER RULING 55: after practising from saves, the AI passes a NEW GAME test so that
what it learned connects). Build spec `PROJECT KNOWLEDGE/ai-research-notes/2026-11-05-LIVE-CHAIN-BUILD-SPEC.md` (written in
the session scratch as s53/chainheld/SPEC.md, with its adversarial critique CH-01..CH-18 and N1-N7 applied or rebutted in
the build report). TEST SIDE: the AI never imports this module (ImportTests).

    py -3.12 ai_player/gates/live_chain.py bounds (--run ch5 | --to ID [--chains 3|6] [--leg-frames L1=F,...])
        print the BOUNDS TEXT, the legs, the registered numbers (without the text) and both sha256s (read only)
    py -3.12 ai_player/gates/live_chain.py register --run ch5 [--note-file F]
        pre-register GRADED_RUNS["ch5"]'s seeds with registered_numbers()'s sha256 (BEFORE any run; commit and push it);
        REFUSED (R12, the checker's C2-05 and the third check's C3-H01/H02) while the grader's code could be a file the
        registration does not hash (`closure_missing`: an unhashed file of the import closure, a package folder, an
        extension module or a sourceless .pyc beside a closure module, a __pycache__ file CPython would load instead of
        its source, or a file in a script folder named like a module a closure file imports or the standard library; not
        sandbox-pokebot's own git-ignored mgba (the emulator's library) and profiles, unhashed by design)
    py -3.12 ai_player/gates/live_chain.py run --purpose graded --run ch5 --out DIR
    py -3.12 ai_player/gates/live_chain.py run --purpose development --first-seed N --to ID --prediction-file F --out DIR
            [--chains 3|6] [--leg-frames L1=F[,L2=F...]] [--build-root DIR]
        EXIT CODES: 0 = PASS (graded) / ran (development); 1 = FAIL; 2 = refused before any leg (the ledger untouched);
        3 = ABORTED by the harness (disk); 4 = ERROR: the harness raised after ledger.begin, while the chains ran or while
        grading, writing the evidence, results.json or the ledger (the checkers' C2-07 and C3-E03): the ledger entry is
        FINISHED as "ERROR (harness: <type>: <message> while <stage>; no PASS or FAIL; the seeds are spent)", with the
        traceback in the evidence, UNLESS the ledger itself cannot be written: then the evidence and the output say the
        entry is NOT finished and give the exact command that finishes it (`finish-entry`), and the exit is still 4;
        5 = a harness crash the guard did not cover (before ledger.begin: the ledger untouched; see the ledger entry's
        status). Ctrl+C after ledger.begin finishes the entry as ERROR and then stops the process; (the fourth check's
        C4-E03) the guard prints one line at once, and a second Ctrl+C is ignored until the entry is written. After
        ledger.begin the only way the entry stays "started" is a HARD KILL of this orchestrator process itself (closing its
        window, Ctrl+Break, a task kill) or a ledger that cannot be written, which the output says.
        --out must not exist or be EMPTY, and must be a folder this process can create and write (R11, the verifier's V-01
        and the third check's C3-E01): --out and the chains' job files are written BEFORE ledger.begin, so a typo in --out
        never spends the seeds; (C4-E02) a launch first CLAIMS --out by creating BATCH.claim.json exclusively, so a second
        launch on the same --out is refused (R11, exit 2, the ledger untouched) and removes only what it made itself; a
        graded run is refused (R12) like a registration, and (C4-H02) while any PYTHON* variable is set other than
        PYTHON_ENV_ALLOWED's
    py -3.12 ai_player/gates/live_chain.py grade DIR [--ledger PATH]   offline re-grade of a batch's rows (no ledger
        write): only the registered chains' rows, each read from rows/<chain>.json and RE-DERIVED from its own facts; any
        other row is printed as IGNORED (V-02). (C3-G02) The legs, jobs and reach floor come from the numbers results.json
        carries, VERIFIED against its numbers sha256 and the ledger entry's registered bounds sha256 (an older folder with
        no numbers prints UNVERIFIED). (The fourth check's C4-G01..G03, C4-E06) it reads the batch's LEDGER ENTRY NOW (by
        its seeds and bounds sha256, its id preferred) and never reports a verdict better than that entry's: its status,
        verdict and purpose win over the folder's files; a development batch is labelled DEVELOPMENT, not graded; numbers
        that are missing, or that no ledger entry verifies, are UNVERIFIED, and a GRADED folder then never exits 0. A folder
        with no ledger entry (an old one, or a ledger that is not the one it ran with) is re-graded from its own records,
        labelled with results.json's purpose (said to be unconfirmed): a graded one exits 1 (UNVERIFIED), a development one
        by its re-grade. EXIT: 0 = PASS (graded: VERIFIED and the ledger says PASS; development: labelled), 1 = FAIL or
        UNVERIFIED, 2 = could not be graded, 3 = ABORTED (ABORT.txt, results.json or the ledger entry), 4 = ERROR
        (results.error.json, the ledger entry's ERROR verdict, or an entry still "started"); the worst of these wins
    py -3.12 ai_player/gates/live_chain.py finish-entry DIR [--ledger PATH]   finish a ledger entry the ERROR path could
        not write (it left DIR/ledger.unfinished.json): refused unless that entry is still "started" and (C4-E05) the verdict
        is this driver's own ERROR verdict for it, rebuilt from DIR/results.error.json (never a PASS or a FAIL)
    py -3.12 ai_player/gates/live_chain.py read RUN_DIR [--truth]
        one leg folder, READ ONLY: its log counts, its memory line, its world.jsonl streamed (never kept, never deleted)
    `child JOB.json` is the internal entry of one chain's process.

WHAT IT IS. Chains of LEGS: each chain starts from a REAL New Game and plays one leg per chapter, each leg through the real
launcher (`live_step5.run_arm`: the purity gate on every launch), from the save state AND the world memory the previous leg
left. A leg targets its chapter's end milestone (`legs_of`, derived from `knowledge/milestones.json`); the last targets
`--to`. What a leg reached is read from the GAME (the harness's `truth` on the state it left, at the save-block numbers
the milestones name), freshness-checked by `L5.THIS_RUN`. A chain that misses STOPS: its later legs are NOT RUN, each with
a row that says why. Everything the batch is graded by (BOUNDS_TEXT, every constant, the legs and their proofs, the
milestones' sha256, the AI code's sha256 and the grader files' sha256) is hashed into the ledger registration, so
`ledger.begin` refuses a graded run on other numbers or code. The grader files are the IMPORT CLOSURE of this module, of
the files the harness and the launcher RUN BY PATH (`PATH_ROOTS`: the purity gate, the truth and hands harnesses, the
framework's pokebot.py) and of the plugins the framework LOADS BY NAME in every leg (`loaded_plugins`), the checker's
C2-02. The disk rule is live_ki128's section 6, per leg.

KNOWN LIMITS (said, not hidden; also in the evidence): each leg is its own launcher session, so the goal manager's in-run
memory starts again at every leg and the HARNESS names each leg's target (critic CH-18: this tests the game state and the
world memory carried across chapters, NOT the AI moving from one chapter to the next in one process; the rejected
alternative, one process to --to, would be about 2.76 M frames and 3 h a chain); the legs hand the game over by savestate,
not through the game's own save (USER RULING 51's saving is not part of this test); `live_step5.run_arm` reads the whole
action log into memory (the 2 GB-world churn runs of 2026-10-30, profiles ai-ch3-probe-1/2, had actions.jsonl of 12.97 MB
and 14.61 MB and logs under 1 MB, so this is megabytes, not gigabytes); the world cap is per leg, and later chapters'
snapshot lines are larger. LC.CUSTODY reads only the HARNESS's own records (the truth of one state file read twice, the
sha256 of the one kept file, the keys of the environment `run_chain` builds, not the whole environment `run_arm` passes): on
a later leg it catches a regression of the harness only, never anything the AI does (the verifier's V-09). A launch that
dies before playing a frame RAN, so it fails LC.PURITY and LC.THIS_RUN and the batch (the lead's ruling on V-08: the
registered rule is kept); its row and the evidence name it "harness: the launch died before playing a frame". (The
checkers' C2-07, C3-E01 and the chains-run guard) an exception in the harness after ledger.begin, while the chains run
(every running chain process is then killed) or while grading, writing the evidence, results.json or the ledger, still
FINISHES the ledger entry, as "ERROR (harness: <type>: <message> while <stage>; no PASS or FAIL; the seeds are spent)",
the way the disk guard's ABORT is recorded, with whatever evidence could be written and the traceback (exit 4); every
step that needs no chain (--out, the job files, the profile snapshots) runs BEFORE ledger.begin. The only ways an entry
stays "started" are a hard kill of this orchestrator process and a ledger file that cannot be written at all (then the
evidence and the output say so, with the command that finishes it); a second Ctrl+C while the guard finishes is ignored
(C4-E03). (C3-E02, C4-E01, C4-E04) every file the AI writes (world.jsonl and its kept last line, ai_player.log, the
verdict file and its counters, actions.jsonl), of ANY content or kind, is UNTRUSTED: a line or a value that does not
parse or has the wrong shape, text that cannot be written as UTF-8 (it is escaped), a folder where a file was meant, or a
file the OS refuses to open, is a failed check of that leg (its chain stops; the batch is GRADED), never an exception of
the harness.

THREAT MODEL (what the guards are for; every claim in this file and in the bounds text stays inside it). The driver
guards against (a) HONEST-CASE HARNESS DEFECTS: anything the AI writes, of any content or kind, gives a GRADED verdict,
never the harness's ERROR; real races between processes (two launches on one --out, a second Ctrl+C while the entry is
finished) are handled; an honest ABORTED, ERROR or development batch re-graded offline says exactly that; (b) ACCIDENTAL CONTAMINATION: stray, stale or unhashed files or caches that would run in a graded run,
and environment variables that change what Python loads, are refused before ledger.begin (R12); (c) EDITS OF AN --out
FOLDER AFTER THE RUN, which can never make the offline re-grade (`grade DIR`) report a verdict better than the ledger's.
It does NOT claim to stop code crafted to switch the grader off from inside its own process (the fourth check's C4-H05:
such code runs before any check of this process can look at it); the purity gate and the clean, pushed tree (R9) are the
defence there.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.machinery
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates import ledger  # noqa: E402
from ai_player.gates.grader_checks import (  # noqa: E402
    AI, GAME, GRADED, HARNESS, PASS, REPORTED, Check, status_of, verdict as typed_verdict,
)
# (spec D7) live_ki128's readers are imported, not copied: its 55 tests cover them, and it is in GRADER_FILES
from ai_player.gates.live_ki128 import (  # noqa: E402
    ai_code_sha256, file_sha256, free_gb, kill_descendants, measure_then_delete, text_sha256,
)
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_CLOCK, ENV_PERSONALITY, ENV_SEED, ENV_STARTER, ENV_TARGET, ENV_WORLD,
)

GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
FAMILY = "story"
DRIVER = "live_chain"
SPEC = "PROJECT KNOWLEDGE/ai-research-notes/2026-11-05-LIVE-CHAIN-BUILD-SPEC.md"

# ====================================================================== the registered constants (section 3 and 5)
#: (pair, personality, starter): one chain per pair and seed
PAIRS = (("S", "Story", "TREECKO"), ("C", "Catcher", "TORCHIC"), ("T", "Trainer", "MUDKIP"))
#: (pair, seed offset) in launch order: one chain of each pair in the first wave
JOB_ORDER = (("S", 0), ("C", 2), ("T", 4), ("S", 1), ("C", 3), ("T", 5))
#: development `--chains 3` only (its seed range is first..first+2, critic N3)
JOB_ORDER_3 = (("S", 0), ("C", 1), ("T", 2))
#: one row per graded registration (seeds 6201-6206 checked unused in every ledger on 2026-11-05)
GRADED_RUNS = {"ch5": {"seeds": (6201, 6206), "to": "ch5_rival_meet"}}
#: a chapter needs its OWN registered budget (adding one changes the grader hash, so a new registration)
FRAMES_BY_CHAPTER = {1: 330000, 2: 330000, 3: 600000, 4: 900000, 5: 600000}
WALL = 3600.0
PARALLEL = 3
STAGGER_SECONDS = 15
#: a pre-registered PRIOR (critic CH-16), not a measured rate: 0 unbroken New Game -> chapter 5 chains have run on one code
#: version, and the chains come in pairs (two seeds per personality and starter), so the binomial power of "at least 5 of 6"
#: (0.97 at p 0.95, 0.89 at 0.90, 0.66 at 0.80, 0.11 at 0.50) assumes independent chains it does not have
REACH_MIN = 5
#: every leg's world.jsonl UNDER this many bytes (decimal), measured before its deletion (the live_ki128 precedent)
WORLD_MAX_BYTES = 300_000_000
#: (critic CH-02) GRADED by the spec's D2; the known, unfixed Route 116 after-battle churn (774 MB in 200,000 frames) fails
#: it, so the lead rules on this ONE word before registering (REPORTED: the cap is printed and never counts, and a churn leg
#: no longer stops its chain)
WORLD_SIZE_KIND = GRADED
#: the disk guard during the batch (a leg past it has its launcher killed; free space under GUARD_FREE_GB ABORTS the batch)
GUARD_WORLD_BYTES = 1_500_000_000
GUARD_FREE_GB = 30.0
FREE_MIN_GB = 40.0
#: `live_step5.run_arm`'s own margin over the wall clock, and `truth_of`'s timeout (two truth reads a leg)
LEG_MARGIN_SECONDS = 300
TRUTH_SECONDS = 600
PROFILE_PREFIX = "ai-livechain-"
#: `live_step5.PROFILE`'s default: the profile `run_arm` writes when the global is not re-pointed
MAIN_PROFILE = "ai-step5-play"
#: the purity checks of `live_step2.check_purity` that COUNT (L5.PURITY_ENDED is reported only: a leg may end on its budget)
PURITY_IDS = ("L5.PURITY_GATE", "L5.PURITY_CLEAN", "L5.PURITY_PRESSES", "L5.PURITY_FRAMES", "L5.PURITY_BREACHES",
              "L5.PURITY_PACKAGE")
#: the environment each leg gets (`live_step2.clean_env` strips the caller's AI_PLAYER_*); nothing else, no fault switch
ENV_KEYS_FIRST = tuple(sorted((ENV_BRAIN, ENV_SEED, ENV_PERSONALITY, ENV_TARGET, ENV_CLOCK, ENV_STARTER)))
ENV_KEYS_LATER = tuple(sorted((ENV_BRAIN, ENV_SEED, ENV_PERSONALITY, ENV_TARGET, ENV_CLOCK, ENV_WORLD)))
#: where the game sets a target's proof (pinned decomp 731ad5b), printed beside its leg (critic CH-09)
PROOF_NOTES = {
    "ch5_rival_meet": "the flag and VAR 8 are set together when the rival is met in Rustboro (RustboroCity/scripts.inc:740-741 "
                      "and :808-809); on Route 104 the flag is set at Route104/scripts.inc:99 and :184 and VAR 8 at :50; MR. "
                      "BRINEY's sail sets VAR 8 alone (Route104_MrBrineysHouse/scripts.inc:78), so the FLAG is what tells a "
                      "rival meeting: the proof means 'met the rival in Rustboro or on Route 104'",
}
#: (the verifier's V-03; the checker's C2-02) the module names the grader's IMPORT CLOSURE is followed through: (module
#: prefix, the path of that package or module without ".py"). The AI's own modules (ai_player/ outside gates/) are not
#: followed: they are hashed whole, as ai_code_sha256. The framework's are the top-level names a leg's pokebot.py and its
#: modules import (sandbox-pokebot is sys.path[0] in a leg): its modules and plugins packages and its pokebot,
#: requirements and updater files. NOT `profiles` and `mgba` (TOPLEVEL_NOT_FOLLOWED): git-ignored and per machine, so
#: following them would make the closure depend on the machine; they are not hashed, and the bounds text says so (R12
#: refuses any other folder or module of sandbox-pokebot named like a top-level module a closure file imports)
CLOSURE_ROOTS = (("ai_player.gates", "ai_player/gates"), ("modules", "sandbox-pokebot/modules"),
                 ("plugins", "sandbox-pokebot/plugins"), ("pokebot", "sandbox-pokebot/pokebot"),
                 ("requirements", "sandbox-pokebot/requirements"), ("updater", "sandbox-pokebot/updater"))
#: (the checker's C2-02) the files the harness or the launcher RUNS BY PATH (`[sys.executable, <file>, ...]`), which no
#: import statement has to reach, so each STARTS the closure: test_live_chain finds every path-built argv in the closure's
#: files and the AI's code and fails on a script that is not listed here (a file that runs itself is in the closure
#: already). The purity gate decides L5.PURITY_GATE: host/launcher.py's run_gate runs it and its exit code is the
#: '[AI-GATE] ... verdict=PASS' line live_step2 requires; host/launcher.py's bot_command runs pokebot.py in every leg
PATH_ROOTS = ("ai_player/gates/check_purity.py",  # host/launcher.py run_gate: L5.PURITY_GATE
              "ai_player/gates/hands_harness.py",  # live_step2's hands harness
              "ai_player/gates/play_harness.py",  # live_step5.truth_of and rate_step5: the truth every proof is read from
              "ai_player/gates/probe_presses.py",  # live_step2's presses probe
              "sandbox-pokebot/pokebot.py")  # host/launcher.py bot_command (and modules/endless_x4.py's lanes): every leg
#: (the checker's C2-02) the plugins the framework loads BY NAME in every leg: modules/plugins.py's load_plugins() imports
#: every name ending in .py in this folder with __import__("plugins.<name>") ...
PLUGINS_DIR = "sandbox-pokebot/plugins"
#: ... and plugins/custom_modes_loader.py's get_additional_bot_modes() (called for pokebot.py's bot-mode names) imports
#: every *.py here not starting with "_" with importlib.import_module("plugins.custom_modes.<stem>")
CUSTOM_MODES_DIR = "sandbox-pokebot/plugins/custom_modes"
#: (the third check's C3-H05) the framework's top-level names whose ABSOLUTE imports in the AI's own files (ai_player/
#: outside gates/ and evidence/) also START the closure: a framework module only the AI imports runs in every leg, so it
#: is hashed and R12 sees it (the AI's own files are hashed whole, as ai_code_sha256, and never followed)
AI_FRAMEWORK_PREFIXES = ("modules", "plugins")
#: (the third check's C3-H02) the folders Python puts FIRST on sys.path in the grader's own processes: the repository root
#: (live_chain.py inserts it at sys.path[0]), ai_player/gates (the folder of every gates script run by path: the grader, the
#: purity gate, the truth and the hands harnesses) and sandbox-pokebot (a leg's pokebot.py runs from it). A .py, .pyw,
#: .pyc, extension module or package folder directly in one of them, named like the standard library's module (or any
#: folder or such file named like a module a closure file imports at top level), runs INSTEAD of that module: R12 refuses
#: it (`toplevel_problems`)
SCRIPT_FOLDERS = ("", "ai_player/gates", "sandbox-pokebot")
#: (C3-H02; the fourth check's C4-H01: EXACT entries) the entries of a script folder that ARE the module a closure file
#: imports by that name, as (folder, entry name, is a folder): the AI's package FOLDER at the repository root, and in
#: sandbox-pokebot the framework's own top-level names (the CLOSURE_ROOTS rooted there): the FOLDERS modules and plugins
#: and the FILES pokebot.py, requirements.py and updater.py. Only that entry is exempt: another entry of the same name (a
#: modules.pyw beside the modules folder, a pokebot folder, a root modules.py) runs INSTEAD of it and is refused
TOPLEVEL_HOMES = frozenset({("", "ai_player", True), ("sandbox-pokebot", "modules", True),
                            ("sandbox-pokebot", "plugins", True), ("sandbox-pokebot", "pokebot.py", False),
                            ("sandbox-pokebot", "requirements.py", False), ("sandbox-pokebot", "updater.py", False)})
#: (C2-02, C3-H02) the top-level names of sandbox-pokebot a closure file imports that the closure does NOT follow, each with
#: why (EXACT: test_live_chain fails on an entry no closure file imports any more; a stale exemption is a hole). Each is
#: exempt BY NAME, only as a FOLDER (C4-H01) and only in that folder: `toplevel_problems` never refuses that folder there,
#: and still refuses the same name in any other script folder or as a file (the full regression lane of 2026-11-06 on
#: d1a853bc: sandbox-pokebot/mgba exists wherever the emulator is installed, which is the main checkout always, and the
#: test's earlier rule failed on it)
TOPLEVEL_NOT_FOLLOWED = {
    ("sandbox-pokebot", "profiles"):
        "git-ignored and per machine (the framework copies modules/config/templates into it at start, the catch filters "
        "modules/encounter.py imports among them): following it would make the closure depend on the machine; the bounds "
        "text says it is not hashed",
    ("sandbox-pokebot", "mgba"):
        "the emulator's library: it exists wherever the emulator is installed (the main checkout always; a fresh worktree "
        "has none), git-ignored and installed per machine with its compiled _pylib (modules/libmgba.py and "
        "modules/gui/glfw.py import it); it is unhashed BY DESIGN, and the bounds text says so",
}
#: (C3-H02, the fourth check's C4-H02) the ONLY environment variables starting with PYTHON a graded run allows, each with why
#: it is harmless: none of them changes which file Python loads for a module. EVERY OTHER one refuses a graded run (R12)
#: and is dropped from every chain process's environment, and so from the truth reads' (`child_env`, `child`):
#: PYTHONPATH and PYTHONHOME (other folders on sys.path), PYTHONPYCACHEPREFIX (caches read from another folder),
#: PYTHONCASEOK (a file whose name differs in case imported), PYTHONUSERBASE (another user site-packages with its .pth
#: files), PYTHONSTARTUP, PYTHONSAFEPATH, PYTHONINSPECT, ... and any a later Python adds (refuse more, never less)
PYTHON_ENV_ALLOWED = {
    "PYTHONIOENCODING": "the encoding of stdin, stdout and stderr only",
    "PYTHONUTF8": "the UTF-8 mode: the default encoding of text files and streams (every chain process gets it set)",
    "PYTHONDONTWRITEBYTECODE": "Python writes no cache file; it reads caches as before, and R12 judges those (every chain "
                               "process gets it set)",
    "PYTHONUNBUFFERED": "the buffering of stdout and stderr only",
}


def python_env_refused(name: str) -> bool:
    """(C4-H02) An environment variable a graded run refuses and a chain process never gets: PYTHON*, not allowed."""
    upper = name.upper()
    return upper.startswith("PYTHON") and upper not in PYTHON_ENV_ALLOWED
#: THE FILES THAT GRADE THE BATCH, hashed into the registration (`grader_files`). (V-03, C2-02) The code is the IMPORT
#: CLOSURE, within the repository, of this module, of PATH_ROOTS, of the plugins the framework loads by name
#: (`loaded_plugins`) and of the framework modules the AI's own files import (`ai_framework_imports`, C3-H05), as
#: `closure_scan` finds it: every import, at module level or inside a function (a function-local import runs on the path
#: that calls it; a static scan cannot tell which do, so all are followed), relative imports resolved, parent packages'
#: __init__.py included, each module resolved in CPython's order. `register` and a graded run are REFUSED (R12) while the
#: scan finds a file not listed here (C2-05) or another file in place of one (C3-H01, C3-H02: `closure_missing`), and
#: test_live_chain fails. The truth harness (play_harness.py), the party decoder
#: (modules/pokemon.py, pokemon_party.py), the symbol reader (modules/game.py, memory.py), the purity gate and the AI's
#: plugin are among them; so is most of the bot framework, because its modules import one another (a change there means a
#: new registration, which is cheap: the same unplayed range may be re-registered).
#: (critic CH-08) the gates part, under ai_player/gates/
GRADER_GATES = ("__init__.py", "check_grader_imports.py", "check_purity.py", "disk_budget.py", "grader_checks.py",
                "hands_harness.py", "ledger.py", "live_chain.py", "live_ki128.py", "live_step2.py", "live_step5.py",
                "play_harness.py", "probe_end_screen.py", "probe_eyes.py", "probe_presses.py", "probe_save_kill.py",
                "provenance.py", "rate_step5.py", "revert_step5.py", "window.py")
#: the framework part, under sandbox-pokebot/modules/ (reached from the gates' and the framework's `modules.*` imports)
GRADER_SANDBOX = (
    "analytics.py", "backup_manager.py", "badge_case.py", "badge_log.py", "battle_action_selection.py",
    "battle_evolution_scene.py", "battle_fault.py", "battle_handler.py", "battle_menuing.py",
    "battle_move_replacing.py", "battle_state.py", "battle_strategies/__init__.py", "battle_strategies/_interface.py",
    "battle_strategies/_util.py", "battle_strategies/catch.py", "battle_strategies/default.py",
    "battle_strategies/item_stealing.py", "battle_strategies/level_balancing.py", "battle_strategies/level_up.py",
    "battle_strategies/lose_on_purpose.py", "battle_strategies/run_away.py", "berry_trees.py",
    "built_in_plugins/discord_integration.py", "built_in_plugins/generate_encounter_media.py",
    "built_in_plugins/obs.py", "capabilities.py", "catch_balls.py", "clock.py", "cloud_sync.py", "config/__init__.py",
    "config/schemas_v1.py", "console.py", "context.py", "daycare.py", "debug.py", "debug_logger.py",
    "debug_utilities.py", "discord.py", "dmgaudit.py", "encounter.py", "encounter_index.py", "endless_x4.py",
    "exceptions.py", "exceptions_hook.py", "faint_chooser.py", "files.py", "fishing.py", "game.py", "game_cheats.py",
    "game_sprites.py", "game_stats.py", "gamepad.py", "gui/__init__.py", "gui/create_profile_screen.py",
    "gui/dashboard_gui.py", "gui/debug_edit_item_bag.py", "gui/debug_edit_party.py", "gui/debug_edit_pokedex.py",
    "gui/debug_menu.py", "gui/debug_tabs.py", "gui/desktop_notification.py", "gui/emulator_controls.py",
    "gui/emulator_screen.py", "gui/ev_selection_window.py", "gui/glfw.py", "gui/headless.py",
    "gui/load_state_window.py", "gui/milestone_window.py", "gui/multi_select_window.py", "gui/select_profile_screen.py",
    "gui/tile_child.py", "items.py", "keyboard.py", "libmgba.py", "living_dex.py", "macros.py", "main.py", "map.py",
    "map_data.py", "map_path.py", "mart.py", "memory.py", "menu_parsers.py", "menuing.py", "modes/__init__.py",
    "modes/_asserts.py", "modes/_interface.py", "modes/_listeners.py", "modes/berry_blend.py", "modes/bunny_hop.py",
    "modes/daycare.py", "modes/ev_train.py", "modes/feebas.py", "modes/fishing.py", "modes/game_corner.py",
    "modes/item_steal.py", "modes/kecleon.py", "modes/level_grind.py", "modes/nugget_bridge.py",
    "modes/puzzle_solver.py", "modes/roamer_reencounter.py", "modes/roamer_reset.py", "modes/rock_smash.py",
    "modes/safari.py", "modes/spin.py", "modes/starters.py", "modes/static_gift_resets.py", "modes/static_run_away.py",
    "modes/static_soft_resets.py", "modes/sudowoodo.py", "modes/sweet_scent.py", "modes/util/__init__.py",
    "modes/util/_util_helper.py", "modes/util/event_flags_and_vars.py", "modes/util/global_navigation.py",
    "modes/util/higher_level_actions.py", "modes/util/items.py", "modes/util/map.py", "modes/util/pc_interaction.py",
    "modes/util/pokecenter_loop.py", "modes/util/sleep.py", "modes/util/soft_reset.py", "modes/util/tasks_scripts.py",
    "modes/util/walking.py", "obtainability.py", "party_accounting.py", "player.py", "plugin_interface.py",
    "plugins.py", "pokeblock_feeder.py", "pokedex.py", "pokemon.py", "pokemon_party.py", "pokemon_storage.py",
    "profiles.py", "rarity.py", "region_map.py", "remote_party.py", "roamer.py", "roms.py", "runtime.py",
    "safari_strategy.py", "save_data.py", "save_import.py", "sprites.py", "state_cache.py", "stats.py",
    "stats_migrate.py", "story/__init__.py", "story/amulet_coin.py", "story/battle_items.py", "story/bossmode_topup.py",
    "story/chapters.py", "story/config.py", "story/counter_hunt.py", "story/counter_plan.py", "story/double_items.py",
    "story/early_game.py", "story/fortree_gates.py", "story/gym_tm_teach.py", "story/intro.py",
    "story/league_reserve.py", "story/mossdeep_gym.py", "story/mossdeep_gym_puzzle.py", "story/obstacle_clearing.py",
    "story/overworld_items.py", "story/pc_trip.py", "story/pokemon_league.py", "story/progress.py",
    "story/region_reach.py", "story/seafloor_cavern.py", "story/sootopolis.py", "story/sootopolis_gym.py",
    "story/space_center.py", "story/stock_topoff.py", "story/team_policy.py", "story/trainer_identity.py",
    "story/training_areas.py", "story/victory_road.py", "story/weaken_catch.py", "story_milestones.py", "tasks.py",
    "tcg_card.py", "text_printer.py", "tile_bridge.py", "tile_mosaic.py", "update_check.py", "version.py",
    "warp_graph.py", "watchdog.py", "web/http.py", "web/http_stream.py", "x4_logs.py")
#: (C2-02) the rest of the framework, under sandbox-pokebot/: its entry (pokebot.py, run by path) with the requirements and
#: updater files it imports, and the plugins it loads by name (the AI's own hook, PLUGIN, among them)
GRADER_BOT = (
    "plugins/backup_plugin.py", "plugins/custom_modes/__init__.py", "plugins/custom_modes/ai_player_mode.py",
    "plugins/custom_modes/hunt_mode.py", "plugins/custom_modes/living_dex_mode.py",
    "plugins/custom_modes/macro_player.py", "plugins/custom_modes/patrol.py", "plugins/custom_modes/story_mode.py",
    "plugins/custom_modes_loader.py", "plugins/dashboard_autoopen.py", "plugins/game_cheats_plugin.py",
    "plugins/gamepad_plugin.py", "plugins/macro_plugin.py", "plugins/shiny_alert_plugin.py",
    "plugins/watchdog_plugin.py", "pokebot.py", "requirements.py", "updater.py")
#: the AI's plugin in the framework: the hook it plays through (no grader imports it; the framework loads it by name, so it
#: is in GRADER_BOT through `loaded_plugins`)
PLUGIN = "sandbox-pokebot/plugins/custom_modes/ai_player_mode.py"
#: THE DATA THE GRADE READS (V-03): the truth's symbol tables (modules/game.py loads both for Emerald: every address the
#: truth reads, gSaveBlock1Ptr's and gSaveBlock2Ptr's among them), the tables the party decoder opens when it is imported
#: (MEASURED 2026-11-05 by an audit hook on `open` while modules.memory, game, pokemon_party and pokemon were imported:
#: species.json, whose names LC.STARTER compares, and five more), the item flags the truth's story read reads, and the
#: check table's B1 debt and waiver lists
GRADER_DATA = ("sandbox-pokebot/modules/data/symbols/pokeemerald.sym",
               "sandbox-pokebot/modules/data/symbols/patches/pokeemerald.sym",
               "sandbox-pokebot/modules/data/species.json", "sandbox-pokebot/modules/data/types.json",
               "sandbox-pokebot/modules/data/moves.json", "sandbox-pokebot/modules/data/natures.json",
               "sandbox-pokebot/modules/data/abilities.json", "sandbox-pokebot/modules/data/items.json",
               "ai_player/gates/fixtures/item_flags.json", "ai_player/gates/b1_debt.json",
               "ai_player/gates/grader_waivers.json")
GRADER_FILES = (*(f"ai_player/gates/{name}" for name in GRADER_GATES),
                *(f"sandbox-pokebot/modules/{name}" for name in GRADER_SANDBOX),
                *(f"sandbox-pokebot/{name}" for name in GRADER_BOT), *GRADER_DATA)
MILESTONES = "ai_player/knowledge/milestones.json"
#: (critic CH-11) the graded check that reads an AI input, declared: the only record that the AI LOADED the carried memory
AI_INPUT_DEBT = {
    "LC.MEMORY": {"ai_input": "'[AI-WORLD] memory from ...' line in ai_player.log",
                  "plan": "critic CH-11: no game or harness record shows that the AI loaded the memory it was handed; its "
                          "own line names the file and five counts, and the counts are checked against the kept line the "
                          "HARNESS wrote, so an amnesiac leg or a wrong memory fails"},
}
STOP_FILE = "STOP.txt"
ABORT_FILE = "ABORT.txt"
RAN = ("RAN", "SALVAGED", "ERROR")  # a leg that was (or may have been) launched: every check samples it


class Refusal(Exception):
    """A batch, a leg list or a chain the driver refuses: the message says why."""


def repo_root() -> Path:
    """REPO, read at call time (the mutant tests load a mutated copy and rebind it)."""
    return REPO


def chain_watchdog_seconds(legs: list[dict]) -> int:
    """A chain child alive past this is killed and salvaged: each leg's wall plus run_arm's margin plus two truth reads,
    plus 300 s (5 legs of 3,600 s: 25,800 s)."""
    return int(sum(leg["wall"] + LEG_MARGIN_SECONDS + 2 * TRUTH_SECONDS for leg in legs) + 300)


def reach_min_of(chains: int) -> int:
    """At least REACH_MIN of 6 (graded); a development batch of 3 allows one miss (2 of 3)."""
    return REACH_MIN if chains == 6 else chains - 1


# ====================================================================== the legs (pure)
def load_milestones(repo: Path | None = None) -> dict:
    return json.loads(((repo or REPO) / MILESTONES).read_text(encoding="utf-8"))


def legs_of(to: str | None, data: dict, frames_by_chapter: dict[int, int] | None = None) -> list[dict]:
    """One leg per chapter up to `to`'s (spec section 2), RAISING `Refusal` for an unknown, optional or waypoint target, a
    chapter with no end milestone or no budget, an empty proof, or milestones whose chapters go backwards in file order.
    A chapter's leg ends at its LAST milestone in file order that is neither optional nor a waypoint; the last leg's is `to`."""
    budgets = FRAMES_BY_CHAPTER if frames_by_chapter is None else frames_by_chapter
    ms = list(data.get("milestones") or [])
    if any(not isinstance(m.get("chapter"), int) for m in ms):
        raise Refusal("a milestone of milestones.json has no chapter number")
    for a, b in zip(ms, ms[1:]):
        if b["chapter"] < a["chapter"]:
            raise Refusal(f"milestones.json's chapters go BACKWARDS in file order: {a['id']} (chapter {a['chapter']}) "
                          f"before {b['id']} (chapter {b['chapter']})")
    target = next((m for m in ms if m.get("id") == to), None)
    if target is None:
        raise Refusal(f"--to {to!r} is no milestone of milestones.json")
    if target.get("optional"):
        raise Refusal(f"--to {to} is OPTIONAL: a run may never need it, so no chain may end on it")
    if target.get("waypoint") is not None:
        raise Refusal(f"--to {to} is a WAYPOINT ({target['waypoint']}): its proof is a later milestone's, so the AI stops "
                      f"on its map while the game's proof is still false")
    legs = []
    for chapter in range(1, target["chapter"] + 1):
        if chapter == target["chapter"]:
            end = target
        else:
            ends = [m for m in ms if m["chapter"] == chapter and not m.get("optional") and m.get("waypoint") is None]
            if not ends:
                raise Refusal(f"chapter {chapter} has no milestone that is neither optional nor a waypoint: no leg ends it")
            end = ends[-1]
        if chapter not in budgets:
            raise Refusal(f"chapter {chapter} has no registered frame budget (FRAMES_BY_CHAPTER {sorted(budgets)}): a chapter "
                          f"needs its own, and adding one is a new registration")
        done = end.get("done") or {}
        proof = {"flags": {k: int(v) for k, v in (done.get("flags") or {}).items()},
                 "variables": {k: {"number": int(v["number"]), "at_least": int(v["at_least"])}
                               for k, v in (done.get("variables") or {}).items()},
                 "trainers": {k: int(v) for k, v in (done.get("trainers") or {}).items()}}
        if not (proof["flags"] or proof["variables"] or proof["trainers"]):
            raise Refusal(f"{end['id']}'s proof is EMPTY: an empty proof holds on any state")
        legs.append({"leg": f"L{chapter}", "chapter": chapter, "target": end["id"], "frames": int(budgets[chapter]),
                     "wall": WALL, "proof": proof})
    return legs


def parse_leg_frames(text: str | None, legs: list[dict]) -> dict[str, int]:
    """`L1=30000,L2=5000` -> {"L1": 30000, "L2": 5000}, RAISING `Refusal` on a leg not in `legs` or a budget under 1."""
    if not text:
        return {}
    names = {leg["leg"] for leg in legs}
    out: dict[str, int] = {}
    for part in text.split(","):
        name, _, value = part.strip().partition("=")
        if name not in names:
            raise Refusal(f"--leg-frames names {name!r}, not one of the legs {sorted(names)}")
        try:
            frames = int(value)
        except ValueError:
            raise Refusal(f"--leg-frames {part!r}: not a whole number of frames") from None
        if frames < 1:
            raise Refusal(f"--leg-frames {part!r}: a budget must be at least 1 frame")
        out[name] = frames
    return out


def proof_holds(marks: dict | None, proof: dict) -> dict:
    """Does the game's proof hold on a truth's marks? Every flag == 1, every `VAR_<name>` >= its at_least, every
    `TRAINER_<name>` == 1. A key the truth did NOT return is NOT held: it is listed as missing, never defaulted. An empty
    proof never holds."""
    marks = marks or {}
    values: dict[str, object] = {}
    missing: list[str] = []
    failing: list[str] = []

    def one(key: str, ok) -> None:
        value = marks.get(key)
        values[key] = value
        if value is None:
            missing.append(key)
        elif not ok(value):
            failing.append(key)

    for name in proof.get("flags") or {}:
        one(name, lambda v: v == 1)
    for name, info in (proof.get("variables") or {}).items():
        one(f"VAR_{name}", lambda v, need=info["at_least"]: isinstance(v, int) and v >= need)
    for name in proof.get("trainers") or {}:
        one(f"TRAINER_{name}", lambda v: v == 1)
    return {"held": bool(values) and not missing and not failing, "missing": missing, "failing": failing,
            "values": values}


def proof_text(proof: dict | None) -> str:
    if not proof:
        return "not read"
    if proof.get("unread"):
        return "UNREAD (no start truth)"
    return (f"{proof.get('values')}" + (f"; missing {proof['missing']}" if proof.get("missing") else "")
            + (f"; failing {proof['failing']}" if proof.get("failing") else ""))


def proof_line(leg: dict) -> str:
    """One leg's proof as the bounds text writes it: NAME (number) = 1 / VAR_NAME (number) >= n / TRAINER_NAME (number) = 1."""
    p = leg["proof"]
    parts = [f"{name} ({number}) = 1" for name, number in p["flags"].items()]
    parts += [f"VAR_{name} ({info['number']}) >= {info['at_least']}" for name, info in p["variables"].items()]
    parts += [f"TRAINER_{name} ({number}) = 1" for name, number in p["trainers"].items()]
    return ", ".join(parts)


# ====================================================================== chains, seeds, jobs
def jobs_of(first: int, chains: int = 6) -> list[dict]:
    order = JOB_ORDER if chains == 6 else JOB_ORDER_3 if chains == 3 else None
    if order is None:
        raise Refusal(f"--chains {chains}: 3 (development) or 6")
    pairs = {p[0]: p for p in PAIRS}
    return [{"chain": f"LC-{pair}-{first + off}", "pair": pair, "personality": pairs[pair][1], "starter": pairs[pair][2],
             "seed": first + off, "profile": f"{PROFILE_PREFIX}{first + off}"} for pair, off in order]


def seeds_of(first: int, chains: int) -> tuple[int, int]:
    return first, first + chains - 1


# ====================================================================== the bounds text (one generator)
def bounds_text(to: str, legs: list[dict], jobs: list[dict], reach_min: int) -> str:
    """BOUNDS_TEXT for these legs and jobs (graded and development use this one generator; hashed into the numbers)."""
    chains = len(jobs)
    first = min(j["seed"] for j in jobs)
    world_graded = WORLD_SIZE_KIND == GRADED
    leg_lines = []
    for leg in legs:
        note = PROOF_NOTES.get(leg["target"])
        leg_lines.append(f"  {leg['leg']} {leg['target']}, {leg['frames']} frames: {proof_line(leg)}"
                         + (f" ({note})" if note else ""))
    job_text = ", ".join(f"{j['personality']} {j['starter']} +{j['seed'] - first}" for j in jobs)
    world_rule = (f"LC.WORLD_SIZE: every leg that ran: its world.jsonl, measured before its deletion, is under {WORLD_MAX_BYTES} "
                  f"bytes (300 MB); if it grew between the first size and the deletion the larger is graded.")
    lines = [
        f"LIVE CHAIN GRADED HELD-OUT (USER RULING 55: the New Game test), build spec {SPEC} (with its critique CH-01..CH-18). "
        f"Driver ai_player/gates/live_chain.py.",
        "THREAT MODEL: the driver guards against (a) honest-case harness defects: anything the AI writes, of any content or "
        "kind, gives a GRADED verdict, never the harness's ERROR; real races between processes (two launches on one --out, a "
        "second Ctrl+C while the entry is finished) are handled; an honest ABORTED, ERROR or development batch re-graded "
        "offline says exactly that; (b) accidental contamination: stray, stale or unhashed "
        "files or caches that would run in a graded run, and environment variables that change what Python loads, are "
        "refused before ledger.begin (R12); (c) edits of an --out folder after the run, which can never make the offline "
        "re-grade (grade DIR) report a verdict better than the ledger's. It does not claim to stop code crafted to switch the "
        "grader off from inside its own process: the purity gate and the clean, pushed tree (R9) are the defence there.",
        "CODE: the AI's files (every file under ai_player/ outside gates/ and evidence/ except *.md files, *.pyc files and "
        "__pycache__ folders; a sourceless .pyc there is refused by R12 below and by the purity gate at every launch) are "
        "hashed into these numbers (ai_code_sha256), knowledge/milestones.json among them and also as milestones_sha256. "
        "grader_files hashes, "
        f"by path and content, exactly these {len(GRADER_FILES)} files and nothing else: the IMPORT CLOSURE, within this "
        f"repository, of ai_player/gates/live_chain.py, of the files the harness and the launcher run by path "
        f"({', '.join(PATH_ROOTS)}), of the plugins the framework loads by name in every leg (every name ending in .py in "
        f"{PLUGINS_DIR}, and every *.py of {CUSTOM_MODES_DIR} not starting with _) and of the framework modules the AI's own "
        f"files import (every absolute {' and '.join(p + '.*' for p in AI_FRAMEWORK_PREFIXES)} import of ai_player/ outside "
        f"gates/ and evidence/) ({len(GRADER_GATES)} files of ai_player/gates, {len(GRADER_SANDBOX)} of "
        f"sandbox-pokebot/modules and {len(GRADER_BOT)} more of sandbox-pokebot: every import, at module level or inside a "
        "function, followed through ai_player/gates and the framework's modules, plugins, pokebot, requirements and updater, "
        "each module resolved in CPython's order (a package's __init__.py, then __init__.pyw, before a module X.py, then "
        "X.pyw); the truth harness, the "
        f"party decoder, the symbol reader, the purity gate and the AI's plugin ({PLUGIN}) among them), and the data the "
        f"grade reads ({', '.join(GRADER_DATA)}). Registration and a graded run are REFUSED (R12) while that scan finds a "
        "file this list does not hash (every one named; a .pyw the closure reaches is one), a package folder, an extension "
        "module or a sourceless .pyc beside a closure module (or as the only importable file of a module the closure "
        "follows), a __pycache__ file CPython would load INSTEAD of its source that holds other code (of a closure file, or "
        "of any .py file of the AI's under ai_player/ outside gates/), a .pyc file of the AI's outside __pycache__, any "
        "Python code file (.py, .pyw, .pyc or an extension module) under ai_player/evidence/ (not hashed, and the AI could "
        "import it), or an entry directly in the repository root, ai_player/gates or sandbox-pokebot that Python could "
        "import instead of a module, its name compared without case: any file or folder named like a top-level module a "
        "closure file imports, unless the entry IS that module (exactly these: the folder ai_player at the root; in "
        "sandbox-pokebot the folders modules and plugins and the files pokebot.py, requirements.py and updater.py; and there "
        "the git-ignored folders mgba and profiles, which are not hashed: see below), and any .py, .pyw, .pyc, extension "
        "module or package folder named like a standard-library module or a module installed outside the repository (every "
        "folder on the interpreter's sys.path outside it, listed when the scan runs, so a library's own imports are "
        "covered; a folder without __init__ only when the installed one is such a folder too; a folder without __init__ "
        "named like a standard-library module is never refused: it never replaces a regular module); a graded run is "
        "also refused while any environment variable starting "
        f"with PYTHON is set other than {', '.join(PYTHON_ENV_ALLOWED)} (none of which changes which file Python loads), "
        "and every chain process runs without them. R12 is a guard against stray, stale or unhashed files, caches and "
        "environment variables (honest mistakes and accidental contamination); it does not claim to stop code written to "
        "switch the grader off from inside its own process: the purity gate and the clean, pushed tree (R9) are the defence "
        "there. Not "
        "hashed: the ROM, the emulator's library (sandbox-pokebot/mgba), the framework's configuration (its *.yml files and "
        "the git-ignored, per-machine sandbox-pokebot/profiles folder it writes at start, catch filters included) and every "
        "other file. Every hashed "
        "file is read with CRLF as LF, so a change of line endings alone is accepted BY "
        "DESIGN (git checks the same commit out with either ending). A graded run on any other AI code, milestone data or "
        "grader file is refused by ledger.begin. A graded run also needs HEAD to be origin/main after a fetch with no tracked "
        "file changed, and the build root to be the one the truth harness reads. The frozen-tree watch must see no change "
        "from the batch's start to its verdict.",
        f"TARGET {to}. LEGS, one per chapter, derived from milestones.json (each chapter before the target's: the LAST "
        f"milestone of the chapter in file order that is neither optional nor a waypoint; the target's chapter: the target), "
        f"each with its frame budget, a {WALL:g} s wall clock and the GAME's proof of its target (save block 1 at the numbers "
        f"named, read by the harness's truth on the state the leg left):",
        *leg_lines,
        f"CHAINS: {chains} on the registered seeds, one seed per chain for all its legs; in launch order (personality, starter, "
        f"seed offset): {job_text}; at most {PARALLEL} chains at once, {STAGGER_SECONDS} s apart; each chain in its own NEW "
        f"profile {PROFILE_PREFIX}<seed> under the build root (refused if it exists).",
        "EACH LEG: the real launcher through live_step5.run_arm, brain play, the chain's personality and seed, target the "
        "leg's; L1 from a REAL New Game (--fresh, the chain's starter); each later leg from the end state the previous leg "
        "left (--state) and the world memory it left (AI_PLAYER_WORLD = that leg's world.jsonl's LAST line, kept outside the "
        "repo; the AI reads only the last line), with the pages read in the earlier legs. The environment holds exactly "
        f"{', '.join(ENV_KEYS_FIRST)} (L1) or {', '.join(ENV_KEYS_LATER)} (later legs); no fault switch. Each leg is its own "
        "session: the game and the world memory are carried, the goal manager's in-run memory starts again, and the harness "
        "names each leg's target (the AI connecting one chapter to the next inside one process is NOT what this tests). "
        "Every file the AI writes (world.jsonl and its kept last line, ai_player.log, the verdict file and its counters, "
        "actions.jsonl), of any content or kind, is UNTRUSTED: a line or a value that does not parse or has the wrong shape, "
        "a folder where a file was meant, or a file the OS refuses to open (a world.jsonl is tried "
        f"{WORLD_READ_TRIES} times, {WORLD_READ_PAUSE_SECONDS:g} s apart, first) fails the check of that leg that reads it "
        "(so its chain stops, by C1-C3 or the purity checks), and text that cannot be written as UTF-8 is kept escaped (a "
        "lone surrogate as \\ud800), never the harness: the batch is still graded.",
        "A LEG REACHES its target iff its L5.THIS_RUN PASSES and every proof of its target holds on the state it left; a mark "
        "the truth did not return is not held. Every chain starts from a New Game, which holds none of the proofs, so the "
        "chain's claim is never vacuous; a leg whose target already held at its start (an earlier leg played past its own "
        "target) still REACHES and is marked ALREADY HELD. For a leg after the first, a start state the truth could not read "
        "is UNREAD, never 'not held' (its custody then fails).",
        f"A CHAIN CONTINUES after a leg iff (C1) the leg reached its target, (C2) every counting purity check of its launch "
        f"PASSED, (C3) its world.jsonl was measured{(' under ' + str(WORLD_MAX_BYTES) + ' bytes') if world_graded else ''} "
        f"and its last line parsed as a JSON object whose five counts (maps, tiles learned, warp links, connections, map "
        f"changes) can be read, and was kept (a failed deletion is recorded and retried at the end, never a stop), (C4) "
        f"the disk guard did not kill it, (C5) its custody held, (C6) the frozen tree had not moved. Otherwise the chain "
        f"STOPS: it fails, and every later leg is NOT RUN (a row says so, with the reason) and is in no check's sample. A "
        f"CHAIN REACHES {to} iff every one of its legs ran and passed C1-C6, the last included.",
        f"DISK: refused under {FREE_MIN_GB:g} GB free on the build root's drive. During the batch a leg whose world.jsonl "
        f"(the newest run folder of its chain's profile) passes {GUARD_WORLD_BYTES} bytes has its launcher killed (recorded; "
        f"its chain stops); under {GUARD_FREE_GB:g} GB free the batch is ABORTED by the harness (every launcher killed, no "
        f"PASS or FAIL: a neighbour's disk use is not the AI's); a chain past its watchdog (each leg's wall + "
        f"{LEG_MARGIN_SECONDS} s + two {TRUTH_SECONDS} s truth reads, + 300 s) is killed and salvaged. After each leg, before "
        f"the next starts, its world.jsonl's size is recorded, it is streamed line by line (never a whole-file read), its "
        f"last line is written outside the repo, and it is DELETED.",
        "GRADED (every one must PASS; a VACUOUS check fails; no waivers):",
        f"LC.REACH: at least {reach_min} of the {chains} chains reach {to} (a pre-registered prior: it assumes independent "
        f"chains, and the chains come in pairs). Every check counts the REGISTERED chains only, one row each: a row of any "
        f"other chain, a second row of one (then none of its rows counts), and a row whose chain, pair, personality, "
        f"starter, seed or profile is not the registered job's are each IGNORED and named with the reason, so a registered "
        f"chain whose row is ignored is ABSENT (LC.CUSTODY's 'every registered chain's L1 ran' then fails, and a check's "
        f"floor may read VACUOUS). Each counted row's legs that ran are RE-DERIVED from the row's own facts: its reach from "
        f"the truth's marks against the REGISTERED leg's proof, its custody by LC.CUSTODY's rule (joined to any problem the "
        f"row stored), its kept last line from the file "
        f"(present, a JSON object whose five counts can be read, its sha256 the row's), so a stored flag can stop a chain "
        f"but never continue one (a leg's status is read as stored: below). (Each leg) every leg that RAN must carry its "
        f"REGISTERED job in its own harness records: "
        f"its environment's AI_PLAYER_SEED (the seed) and AI_PLAYER_PERSONALITY, its command's --profile, its arm "
        f"'<chain>-<leg>' and a run folder under profiles/<profile>/ai_player_runs; and no two legs of the counted rows may "
        f"share a run folder or a kept file: otherwise its custody fails (C5), so a row copied from another chain fails "
        f"custody unless every one of these records is rewritten as well (the rows are trusted as the harness wrote them). "
        f"Each counted row holds exactly the registered legs, in order: a leg missing, added, renamed or moved fails "
        f"LC.CUSTODY. Each leg's STATUS (RAN, NOT RUN, ...) is READ AS STORED, because no row carries what decides it, so a "
        f"stored stop could take a leg out of every sample: a NOT RUN leg after a leg whose re-derived continuation holds "
        f"is a custody failure unless STOP.txt or ABORT.txt is in --out, or the orchestrator's own record of the batch "
        f"(its events, written beside the rows) lists that chain as SALVAGED and the leg's reason is the salvage reason "
        f"(\"the chain's process ended ...\").",
        f"LC.PURITY: on every leg that ran, the counting purity checks of live_step2.check_purity ({', '.join(PURITY_IDS)}) "
        f"all PASS. L5.PURITY_ENDED is reported only.",
        "LC.THIS_RUN: every leg that ran: L5.THIS_RUN (live_step5.check_after_is_this_run) PASSES. A leg whose launch died "
        "before playing a frame RAN (it was launched), so it fails LC.PURITY and LC.THIS_RUN and the batch, like any other "
        "leg: the reach tolerance does not cover it; its row and the evidence name it 'harness: the launch died before "
        "playing a frame', from the run's own exit facts (no exit by the AI, no frame counted, no line of the AI's log, no "
        "world file; a launch killed mid-play is not named).",
        *([world_rule] if world_graded else []),
        "LC.CUSTODY: every registered chain's L1 ran, and every leg that ran started as above: L1 from --fresh with the "
        "chain's starter and no world memory or start state; each later leg from --state of the previous leg's end state, its "
        "start truth (frame, md5) equal to the previous leg's end truth, and an AI_PLAYER_WORLD file whose sha256 equals the "
        "previous leg's kept last line's; every leg's environment keys exactly the set above; every leg that ran names its "
        "registered job and shares no run folder or kept file, and no NOT RUN leg follows a continuing leg unexplained (as "
        "under LC.REACH). These checks read only the "
        "HARNESS's own records (the truth of one state file read twice, the sha256 of the one kept file, the keys of the "
        "environment run_chain builds and hands run_arm, whose clean_env also passes on the caller's variables that are not "
        "AI_PLAYER_*): on a later leg they catch a regression of the harness only, never anything the AI does.",
        "LC.STARTER: every chain whose first leg left a party: its first Pokemon is the chain's registered starter, the "
        "player's own (OT).",
        "LC.MEMORY (reads the AI's log, declared as B1 debt): every leg that ran said '[AI-WORLD] memory from ...': L1 from "
        "nothing (a new memory); each later leg from the last snapshot of its AI_PLAYER_WORLD file, with its maps, tiles "
        "learned, warp links, connections and map changes equal to the counts of the kept last line.",
        "LC.FROZEN: the frozen-tree watch saw no change of the code under test from the batch's start to its verdict (a "
        "STOP.txt in --out, which the batch writes only when the tree moved, beside a record that says it held, fails it).",
        f"LC.LEFTOVER: no python process whose command line names {PROFILE_PREFIX} is left after the batch.",
        "REPORTED (information, never counted): LC.PROGRESS (per chain the legs reached; per leg real frames of the budget, "
        "seconds of the wall), LC.MULTICHOICE (per leg the LINES of ai_player.log saying 'an unexpected multichoice', by form, "
        "and every 'an unexpected <kind>' line by kind: lines, not events), LC.OUTCOME (the AI's exit claim beside the game's "
        "proof), LC.ENDED (who ended each leg, the harness's own record), LC.OPTIONAL (the optional milestones' proofs at "
        "each chain's last leg), LC.WORLD (bytes per leg and chain; deletions; leftovers), LC.PROFILES (each chain's run "
        "folders are its legs', and no run folder of this batch's arms anywhere else), LC.MAIN_PROFILE (ai-step5-play's run "
        "folders and its state file unchanged)"
        + ("" if world_graded else f", LC.WORLD_SIZE (the {WORLD_MAX_BYTES}-byte cap, information)") + ".",
        "VERDICT: PASS iff every GRADED check PASSES. Nothing is tuned to a grader (B1): a miss is reported, never re-run on "
        "new seeds. Every step that needs no chain (--out, the job files, the profile snapshots) runs before ledger.begin, so "
        "an --out that cannot be written is refused with the seeds unspent; a launch first claims --out by creating "
        "BATCH.claim.json there exclusively, so a second launch on the same --out is refused (R11) with the ledger "
        "untouched and removes only what it made itself. If the harness raises after ledger.begin, while "
        "the chains run (every running chain process is killed first) or while grading or writing the evidence, "
        "results.json or the ledger, the ledger entry is still FINISHED, as 'ERROR (harness: <type>: <message> while "
        "<stage>; no PASS or FAIL; the seeds are spent)' (the stage: the chains, grading, the evidence, results.json or the "
        "ledger), with whatever evidence could be written and the traceback, the way the disk guard's ABORT is recorded; a "
        "failed ledger write is retried with the computed verdict before it falls back to ERROR. While the entry is being "
        "finished a second Ctrl+C is ignored (a line says so first). The entry stays 'started' only if this orchestrator "
        "process is killed hard (its window closed, Ctrl+Break, a task kill), or if the ledger file cannot be written at "
        "all: the evidence and the output then say the entry is NOT finished and give the command that finishes it, which "
        "writes only this ERROR verdict. The offline re-grade (grade DIR) reads the batch's ledger entry and never reports "
        "a verdict better than it: an ABORTED or ERROR batch or entry is reported as such, a development batch is labelled "
        "development, and numbers that no ledger entry verifies never give a graded PASS.",
    ]
    return "\n".join(lines)


# ====================================================================== registration
def _module_base(repo: Path, module: str) -> Path | None:
    """The path of a dotted module inside CLOSURE_ROOTS without a suffix (`modules.game` -> sandbox-pokebot/modules/game),
    or None for a module outside them."""
    for prefix, folder in CLOSURE_ROOTS:
        if module == prefix:
            return repo / folder
        if module.startswith(prefix + "."):
            return repo / folder / module[len(prefix) + 1:].replace(".", "/")
    return None


def _closure_file(repo: Path, module: str) -> Path | None:
    """The repository file of a dotted module inside CLOSURE_ROOTS, in CPython's order (the third check's C3-H01: its
    FileFinder tries a package folder's __init__ BEFORE a module's X.py; the fourth check's C4-H01: each in the source
    suffixes' order, .py then .pyw, and a module FILE wins over a namespace folder of the same name), or None (a namespace
    package, such as `plugins`, has no file of its own; a module whose only importable file is no source is R12's:
    `resolution_problems`). A .pyw it finds is in the closure, so R12 names it unless GRADER_FILES hashes it."""
    base = _module_base(repo, module)
    if base is None:
        return None
    for path in (*(base / f"__init__{suffix}" for suffix in SOURCE_SUFFIXES),
                 *(base.parent / f"{base.name}{suffix}" for suffix in SOURCE_SUFFIXES)):
        if path.is_file():
            return path
    return None


def _closure_package(repo: Path, path: Path) -> str:
    """The package a file's relative imports resolve against (a package's own name for its __init__ file; "" for a
    top-level module such as pokebot.py, which has none). (C4-H01) a .pyw file resolves like a .py."""
    rel = path.relative_to(repo).as_posix()
    for prefix, folder in CLOSURE_ROOTS:
        if rel in (f"{folder}{suffix}" for suffix in SOURCE_SUFFIXES):
            return ""
        if rel.startswith(folder + "/"):
            parts = [prefix, *rel[len(folder) + 1:].rsplit(".", 1)[0].split("/")]
            return ".".join(parts[:-1])
    raise ValueError(f"{rel} is in no closure root")


def _statements(nodes: list) -> Iterable[ast.AST]:
    """Every STATEMENT of a syntax tree, nested ones included (function, class, if, try, with, loop and match bodies). An
    import is a statement and never sits inside an expression, so this finds exactly the imports `ast.walk` finds (checked
    2026-11-05 on all 369 .py files of ai_player/ and sandbox-pokebot/: 5,944 each) without walking every expression."""
    for node in nodes:
        yield node
        for name in ("body", "orelse", "finalbody", "handlers", "cases"):
            yield from _statements(getattr(node, name, None) or [])


def _parse(repo: Path, path: Path) -> ast.Module:
    """A file's syntax tree, parsed from its BYTES (the import system decodes by the coding cookie); (the third check's
    C3-E06) a file that does not parse raises a SyntaxError that NAMES it."""
    try:
        name = path.relative_to(repo).as_posix()
    except ValueError:
        name = str(path)
    return ast.parse(path.read_bytes(), filename=name)


def _closure_imports(repo: Path, path: Path) -> set[str]:
    """Every module an import statement of `path` names, read from its SYNTAX (a mention in a comment or a string is no
    import), at module level or inside a function, relative ones resolved, with each one's parent packages."""
    package = _closure_package(repo, path)
    named: set[str] = set()
    for node in _statements(_parse(repo, path).body):
        if isinstance(node, ast.Import):
            named.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                if not package:  # a top-level module has no package: Python refuses its relative import
                    continue
                base = ".".join(parts[:len(parts) - (node.level - 1)] + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            named.add(base)
            named.update(f"{base}.{alias.name}" for alias in node.names if alias.name != "*")
    out: set[str] = set()
    for name in named:
        parts = name.split(".")
        out.update(".".join(parts[:k]) for k in range(1, len(parts) + 1))
    return out


def loaded_plugins(repo: Path | None = None) -> list[str]:
    """(The checker's C2-02) The module names the framework imports BY NAME in every leg, read from the folders the way its
    loaders read them: "plugins.<name>" for every name ending in .py in PLUGINS_DIR (modules/plugins.py load_plugins,
    __import__) and "plugins.custom_modes.<stem>" for every *.py of CUSTOM_MODES_DIR not starting with "_"
    (plugins/custom_modes_loader.py get_additional_bot_modes, importlib.import_module)."""
    repo = repo or REPO
    try:
        names = [f"plugins.{p.name[:-3]}" for p in sorted((repo / PLUGINS_DIR).iterdir()) if p.name.endswith(".py")]
    except OSError:
        names = []
    names += [f"plugins.custom_modes.{p.stem}" for p in sorted((repo / CUSTOM_MODES_DIR).glob("*.py"))
              if not p.name.startswith("_")]
    return names


def ai_framework_imports(repo: Path | None = None) -> set[str]:
    """(The third check's C3-H05) The framework modules the AI's OWN files import: every ABSOLUTE import of ai_player/
    outside gates/ and evidence/ (its .py and .pyw files, __pycache__ skipped) whose top-level name is one of
    AI_FRAMEWORK_PREFIXES, with its parent packages. They start the closure too (a framework module only the AI imports
    runs in every leg); the AI's own files are hashed whole (ai_code_sha256) and never followed."""
    repo = repo or REPO
    root = repo / "ai_player"
    names: set[str] = set()
    for path in sorted([*root.rglob("*.py"), *root.rglob("*.pyw")]):
        rel = path.relative_to(root)
        if rel.parts[0] in ("gates", "evidence") or "__pycache__" in rel.parts:
            continue
        for node in _statements(_parse(repo, path).body):
            if isinstance(node, ast.Import):
                found = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
                found = [node.module, *(f"{node.module}.{alias.name}" for alias in node.names if alias.name != "*")]
            else:
                continue
            for name in found:
                if name.split(".")[0] in AI_FRAMEWORK_PREFIXES:
                    parts = name.split(".")
                    names.update(".".join(parts[:k]) for k in range(1, len(parts) + 1))
    return names


def closure_scan(repo: Path | None = None) -> dict:
    """(The verifier's V-03, the checkers' C2-02 and C3-H05) THE IMPORT CLOSURE within the repository of live_chain.py, of
    the files the harness and the launcher run by path (PATH_ROOTS), of the plugins the framework loads by name
    (`loaded_plugins`, each with its parent packages, as Python imports them) and of the framework modules the AI's own
    files import (`ai_framework_imports`): every file reached by import statements, transitively (module level or inside
    a function), through CLOSURE_ROOTS. Returns {"closure": the sorted repository-relative paths, "paths": those files,
    "modules": every module name followed -> its file or None, "tops": every top-level name an import of a closure file
    names}."""
    repo = repo or REPO
    start = repo / "ai_player" / "gates" / "live_chain.py"
    seen, todo = {start}, [start]
    files: dict[str, Path | None] = {}  # module -> its file, looked up once per scan
    tops: set[str] = set()

    def follow(module: str) -> None:
        if module not in files:
            files[module] = _closure_file(repo, module)
        found = files[module]
        if found is not None and found not in seen:
            seen.add(found)
            todo.append(found)

    for rel in PATH_ROOTS:  # (C2-02) run by path: no import statement reaches them
        path = repo / rel
        if path.is_file() and path not in seen:
            seen.add(path)
            todo.append(path)
    for name in loaded_plugins(repo):  # (C2-02) loaded by name: "plugins", "plugins.custom_modes", ... each imported
        parts = name.split(".")
        for k in range(1, len(parts) + 1):
            follow(".".join(parts[:k]))
    for name in sorted(ai_framework_imports(repo)):  # (C3-H05) the framework modules the AI's own files import
        follow(name)
    while todo:
        path = todo.pop()
        for module in _closure_imports(repo, path):
            if "." not in module:
                tops.add(module)
            follow(module)
    return {"closure": sorted(p.relative_to(repo).as_posix() for p in seen), "paths": seen,
            "modules": {name: found for name, found in files.items() if _module_base(repo, name) is not None},
            "tops": tops}


def grader_closure(repo: Path | None = None) -> list[str]:
    """(V-03, C2-02, C3-H05) `closure_scan`'s files as sorted repository-relative paths. GRADER_FILES must list every one
    (`closure_missing`: R12 at registration and before a graded run; test_live_chain)."""
    return closure_scan(repo)["closure"]


#: (C3-H01) the suffixes of an IMPORTABLE file that is no source: an extension module (CPython loads one BEFORE a source of
#: the same name) and bytecode (loaded when no source is there)
EXTENSION_SUFFIXES = tuple(sorted({*importlib.machinery.EXTENSION_SUFFIXES, ".pyd", ".so"}))
SOURCE_SUFFIXES = (".py", ".pyw")


def _opaque_names(names: Iterable[str], stem: str) -> list[str]:
    """The names among `names` of an importable file of module `stem` that is no source: `stem.pyc`, `stem.pyd`,
    `stem.<tag>.pyd` (any tag) or `stem` + an extension suffix (compared without case: refuse more, never less)."""
    stem = stem.lower()
    found = []
    for name in names:
        low = name.lower()
        if low.startswith(stem + ".") and (low == stem + ".pyc" or low.endswith(EXTENSION_SUFFIXES)):
            found.append(name)
    return sorted(found)


def _entries(cache: dict, folder: Path) -> dict[str, tuple[str, bool]]:
    """{lower-case name: (name, is a folder)} of a folder's entries, listed once per scan ({} when it cannot be)."""
    if folder not in cache:
        try:
            cache[folder] = {entry.name.lower(): (entry.name, entry.is_dir()) for entry in os.scandir(folder)}
        except OSError:
            cache[folder] = {}
    return cache[folder]


def _package_inits(cache: dict, folder: Path) -> list[str]:
    """The `__init__` files of a folder that make it a package for CPython (source, bytecode or an extension module)."""
    return sorted(name for low, (name, is_dir) in _entries(cache, folder).items()
                  if not is_dir and low.startswith("__init__.") and low.endswith((*SOURCE_SUFFIXES, ".pyc",
                                                                                  *EXTENSION_SUFFIXES)))


def resolution_problems(repo: Path, modules: dict[str, Path | None]) -> list[str]:
    """(The third check's C3-H01) Every module the closure follows (`closure_scan`'s "modules") that CPython could import
    from a file the scan did not read: an extension module or a sourceless .pyc beside its X.py or its package's
    __init__.py; a package folder (one with an __init__ file) of the same name beside its X.py; a module X.py beside its
    package folder; a module the scan found no source for whose only importable file is an extension module or bytecode."""
    cache: dict = {}
    problems: list[str] = []

    def rel(path: Path) -> str:
        return path.relative_to(repo).as_posix()
    for module, found in sorted(modules.items()):
        base = _module_base(repo, module)
        if base is None:
            continue
        folder, stem = base.parent, base.name
        here = _entries(cache, folder)
        opaque = _opaque_names((name for name, _ in here.values()), stem)
        is_folder = here.get(stem.lower(), ("", False))[1]
        inits = _package_inits(cache, base) if is_folder else []
        if found is not None and found.parent == base and found.stem == "__init__":  # (C4-H01: __init__.py or .pyw)
            extra = [n for n in _opaque_names(inits, "__init__")]
            problems += [f"{rel(base / n)}: beside the closure file {rel(found)}: an importable file CPython loads "
                         f"instead (an extension module) or that the registration does not hash (bytecode)" for n in extra]
            module_files = [name for name, is_dir in here.values() if not is_dir and name.lower() in
                            {f"{stem.lower()}{s}" for s in SOURCE_SUFFIXES}] + opaque
            problems += [f"{rel(folder / n)}: a module named like the package {rel(base)}/ (the closure file "
                         f"{rel(found)}): two files for one module name" for n in sorted(module_files)]
        elif found is not None:
            problems += [f"{rel(folder / n)}: beside the closure file {rel(found)}: an importable file CPython loads "
                         f"instead (an extension module) or that the registration does not hash (bytecode)" for n in opaque]
            if inits:
                problems.append(f"{rel(base)}/ ({', '.join(inits)}): a package folder named like the closure file "
                                f"{rel(found)}: CPython imports the package INSTEAD of it")
        else:
            problems += [f"{rel(folder / n)}: the only importable file of {module}, which the closure follows, is no "
                         f"source (an extension module or bytecode): it would run unhashed" for n in opaque]
            problems += [f"{rel(base / n)}: the package {module}, which the closure follows, is imported from a file that "
                         f"is no source: it would run unhashed" for n in inits if not n.lower().endswith(".py")]
    return problems


def pycache_problems(repo: Path, paths: Iterable[Path]) -> list[str]:
    """(The third check's C3-H01) Every __pycache__ file of a closure file that CPython (this interpreter's cache tag)
    would load INSTEAD of its source while holding other code: check_purity's rule (e), reused (`_pyc_problem`: the
    header matches the source, so the source is never read, and the code differs from compiling it)."""
    from ai_player.gates.check_purity import CACHE_FILE, _pyc_problem

    problems: list[str] = []
    by_folder: dict[Path, dict[str, Path]] = {}
    for path in paths:
        if path.suffix == ".py":
            by_folder.setdefault(path.parent, {})[path.stem.lower()] = path
    for folder, sources in sorted(by_folder.items()):
        cache = folder / "__pycache__"
        try:
            names = sorted(os.listdir(cache))
        except OSError:
            continue
        for name in names:
            match = CACHE_FILE.match(name)
            source = sources.get(match["stem"].lower()) if match else None
            if source is None or match["tag"] != sys.implementation.cache_tag or not source.is_file():
                continue
            try:
                problem = _pyc_problem(cache / name, source, int(match["opt"] or 0))
            except OSError as error:
                problem = f"it cannot be read ({type(error).__name__}), so it cannot be shown to hold the source's code"
            if problem:
                problems.append(f"{(cache / name).relative_to(repo).as_posix()}: {problem}")
    return problems


def ai_problems(repo: Path) -> list[str]:
    """(The fourth check's C4-H04 and C4-H06) What R12 refuses in the AI's own package, ai_player/ outside gates/ (whose
    modules the closure follows itself): (1) a __pycache__ file CPython would load INSTEAD of the source of one of the AI's
    .py files while holding other code (`pycache_problems`: the grader's own processes import the AI's ai_player, options,
    host, ... before any check, and ai_code_sha256 skips __pycache__, so ledger.begin cannot see it); (2) a .pyc file of
    the AI's outside __pycache__ (bytecode ai_code_sha256 does not hash, imported when no source is beside it); (3) ANY
    Python code file (.py, .pyw, .pyc or an extension module) under ai_player/evidence/, which ai_code_sha256 does not
    hash and the AI could import (the evidence folder holds text, JSON and zip files only)."""
    root = repo / "ai_player"
    sources: list[Path] = []
    problems: list[str] = []
    for folder, dirs, files in os.walk(root):
        here = Path(folder)
        parts = here.relative_to(root).parts
        if parts[:1] == ("gates",):
            dirs[:] = []
            continue
        dirs.sort()
        for name in sorted(files):
            low = name.lower()
            rel = (here / name).relative_to(repo).as_posix()
            if parts[:1] == ("evidence",):
                if low.endswith((*SOURCE_SUFFIXES, ".pyc")) or low.endswith(EXTENSION_SUFFIXES):
                    problems.append(f"{rel}: Python code under ai_player/evidence/: ai_code_sha256 does not hash "
                                    f"evidence/, and the AI could import it")
            elif "__pycache__" in parts:
                continue  # judged by pycache_problems, against its source
            elif low.endswith(".pyc"):
                problems.append(f"{rel}: bytecode of the AI's outside __pycache__: ai_code_sha256 does not hash it, and "
                                f"CPython imports it when no source is beside it")
            elif low.endswith(".py"):
                sources.append(here / name)
    return problems + pycache_problems(repo, sources)


def _importable(entry: Path) -> tuple[str | None, str]:
    """(kind, module name) of a folder's entry as CPython imports it from sys.path: ("package", name) for a folder with an
    __init__ file, ("folder", name) for one without (a namespace package), ("module", name) for a .py, .pyw, .pyc or
    extension module file; (None, name) for anything else."""
    name = entry.name
    if entry.is_dir():
        inits = _package_inits({}, entry)
        return ("package" if inits else "folder"), name
    low = name.lower()
    for suffix in (*SOURCE_SUFFIXES, ".pyc"):
        if low.endswith(suffix) and "." not in name[:-len(suffix)]:
            return "module", name[:-len(suffix)]
    if low.endswith(EXTENSION_SUFFIXES):
        return "module", name.split(".", 1)[0]
    return None, name


def _inside(path: Path, roots: Iterable[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def outside_modules(repo: Path) -> dict[str, str]:
    """(The fourth check's C4-H03) {lower-case name: kind} of every top-level module importable from OUTSIDE the
    repository: each entry Python could import (`_importable`: a module file, a package, a namespace folder) of every
    folder on this interpreter's sys.path that is not inside `repo` (nor this module's own repository), listed when the scan
    runs, with the builtins. It is a superset of the names the closure's third-party libraries import (pydantic's
    typing_extensions, ...): complete without importing them, and correct after a library update."""
    roots = {Path(repo).resolve(), REPO.resolve()}
    found: dict[str, str] = {name.lower(): "module" for name in sys.builtin_module_names}
    for entry in list(sys.path):
        try:
            folder = Path(entry or os.getcwd()).resolve()
            if _inside(folder, roots) or not folder.is_dir():
                continue
            children = sorted(os.scandir(folder), key=lambda child: child.name)
        except (OSError, ValueError):
            continue
        for child in children:
            try:
                kind, name = _importable(Path(child.path))
            except OSError:
                continue
            if kind is not None and name.isidentifier():
                # a module or package anywhere wins over a namespace folder of the same name: keep the strongest kind
                if found.get(name.lower()) in (None, "folder"):
                    found[name.lower()] = kind
    return found


def toplevel_problems(repo: Path, tops: set[str]) -> list[str]:
    """(The third check's C3-H02; moved here from the test and extended to the repository root) Every entry directly in a
    SCRIPT_FOLDERS folder that Python would import INSTEAD of a module, its name compared WITHOUT case (the fourth check's
    C4-H02: refuse more, never less): named like a top-level module a closure file imports (any file or folder CPython can
    import, unless it IS that module: exactly the TOPLEVEL_HOMES entry, or the declared exempt FOLDER of
    TOPLEVEL_NOT_FOLLOWED, the fourth check's C4-H01), or like a standard-library module or a module installed outside the
    repository (C4-H03, `outside_modules`: a module file or a package; a namespace folder only beside an installed
    namespace folder of the same name). A namespace folder named like a standard-library module is never refused: a
    namespace folder never replaces a regular module."""
    stdlib = {name.lower() for name in getattr(sys, "stdlib_module_names", frozenset())}
    installed = outside_modules(repo)
    tops_low = {name.lower() for name in tops}
    homes = {(rel, name.lower(), is_dir) for rel, name, is_dir in TOPLEVEL_HOMES}
    exempt = {(rel, name.lower()) for rel, name in TOPLEVEL_NOT_FOLLOWED}
    problems: list[str] = []
    for rel in SCRIPT_FOLDERS:
        folder = repo / rel if rel else repo
        try:
            entries = sorted(folder.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        for entry in entries:
            kind, name = _importable(entry)
            if kind is None or not name.isidentifier() or (name.startswith("__") and name.endswith("__")):
                continue
            low, is_dir = name.lower(), entry.is_dir()
            if (rel, entry.name.lower(), is_dir) in homes or (is_dir and (rel, low) in exempt):
                continue
            if kind == "folder" and low in stdlib:  # a namespace folder never replaces a regular (library) module
                continue
            where = f"{rel}/{entry.name}" if rel else entry.name
            if low in tops_low:
                problems.append(f"{where}: a {kind} named like {name!r}, a top-level module a closure file imports: with "
                                f"{rel or 'the repository root'} first on sys.path it runs INSTEAD, unhashed")
            elif low in stdlib:
                problems.append(f"{where}: a {kind} named like the standard library's {name!r}: with "
                                f"{rel or 'the repository root'} first on sys.path it runs INSTEAD, unhashed")
            elif low in installed and (kind != "folder" or installed[low] == "folder"):
                problems.append(f"{where}: a {kind} named like {name!r}, a module installed outside the repository (a "
                                f"library the closure's imports may load): with {rel or 'the repository root'} first on "
                                f"sys.path it runs INSTEAD, unhashed")
    return problems


def closure_missing(repo: Path | None = None) -> tuple[list[str], int, float]:
    """(The checkers' C2-05, C3-H01, C3-H02 and C4-H01..H06) WHAT R12 REFUSES: every file of the import closure
    (`closure_scan`) that GRADER_FILES does not hash, then every other file the grader's code could be
    (`resolution_problems`, `pycache_problems`, `toplevel_problems`, `ai_problems`, each "path: why"); with the closure's
    size and the scan's seconds. `register` and a graded run are refused (R12) unless the list is empty; a development
    batch only prints it."""
    repo = repo or REPO
    began = time.perf_counter()
    scan = closure_scan(repo)
    missing = [rel for rel in scan["closure"] if rel not in GRADER_FILES]
    problems = [*resolution_problems(repo, scan["modules"]), *pycache_problems(repo, scan["paths"]),
                *toplevel_problems(repo, scan["tops"]), *ai_problems(repo)]
    return [*missing, *problems], len(scan["closure"]), round(time.perf_counter() - began, 2)


def closure_refusal(missing: list[str]) -> str | None:
    """R12's text for `closure_missing`'s list (EVERY entry named, the third check's C3-H04), or None when it is empty."""
    if not missing:
        return None
    return (f"R12: the grader's code could be {len(missing)} file(s) the registration does not hash: {missing}: list an "
            f"unhashed closure file in GRADER_GATES, GRADER_SANDBOX or GRADER_BOT (a new registration) or remove its "
            f"import; remove any other file named (it would run instead of a hashed one)")


def env_keys() -> dict:
    return {"L1": list(ENV_KEYS_FIRST), "later": list(ENV_KEYS_LATER)}


def registered_numbers(run: str | None, to: str, seeds: tuple[int, int], chains: int, legs: list[dict],
                       repo: Path | None = None, development: dict | None = None) -> dict:
    """Everything the batch is graded by (`ledger.numbers_sha256` of this is the registration's bounds field). A
    development batch adds {purpose, chains, leg_frames_override, prediction_sha256}: its ledger entry covers its
    prediction, registered before the runs."""
    repo = repo or REPO
    jobs = jobs_of(seeds[0], chains)
    reach_min = reach_min_of(chains)
    numbers = {"family": FAMILY, "driver": DRIVER, "run": run, "seeds": list(seeds), "to": to,
               "bounds_text": bounds_text(to, legs, jobs, reach_min),
               "legs": [{k: leg[k] for k in ("leg", "chapter", "target", "frames", "wall", "proof")} for leg in legs],
               "jobs": [{k: j[k] for k in ("chain", "pair", "personality", "starter", "seed")} for j in jobs],
               "parallel": PARALLEL, "stagger_seconds": STAGGER_SECONDS, "reach_min": reach_min, "chains": chains,
               "frames_by_chapter": {str(k): v for k, v in FRAMES_BY_CHAPTER.items()},
               "free_min_gb": FREE_MIN_GB, "world_max_bytes": WORLD_MAX_BYTES, "world_size_kind": WORLD_SIZE_KIND,
               "guard_world_bytes": GUARD_WORLD_BYTES, "guard_free_gb": GUARD_FREE_GB,
               "chain_watchdog_seconds": chain_watchdog_seconds(legs), "profile_prefix": PROFILE_PREFIX,
               "purity_ids": list(PURITY_IDS), "env_keys": env_keys(), "proof_notes": PROOF_NOTES,
               "milestones_sha256": text_sha256(repo / MILESTONES), "ai_code_sha256": ai_code_sha256(repo),
               "grader_files": {name: text_sha256(repo / name) for name in GRADER_FILES}}
    if development is not None:
        numbers.update({"purpose": "development", **development})
    return numbers


def register(seeds: tuple[int, int], numbers: dict, note: str = "", path: Path | None = None) -> dict:
    return ledger.register(FAMILY, DRIVER, seeds[0], seeds[1], ledger.numbers_sha256(numbers), note=note,
                           path=path or ledger.LEDGER)


def begin(purpose: str, seeds: tuple[int, int], numbers: dict, tree: str | None, note: str = "",
          path: Path | None = None) -> tuple[dict, list[str]]:
    return ledger.begin(FAMILY, DRIVER, purpose, seeds[0], seeds[1], ledger.numbers_sha256(numbers), tree, note=note,
                        path=path or ledger.LEDGER)


def seeds_named(first: int, last: int, path: Path | None = None) -> list[dict]:
    """Every ledger entry, of ANY family, whose range overlaps first..last."""
    return [e for e in ledger.load(path or ledger.LEDGER).get("entries", []) if e["first"] <= last and first <= e["last"]]


# ====================================================================== the readers (pure; unit-tested on planted files)
UNEXPECTED = re.compile(r"an unexpected (?P<kind>\S+)(?: (?P<form>on screen|while the person|in the battle))?")
MEMORY_LINE = re.compile(r"\[AI-WORLD\] memory from (?P<source>.+?): (?P<maps>\d+) maps \(")
MEMORY_COUNTS = re.compile(r", (?P<tiles>\d+) tiles learned, (?P<warps>\d+) warp links, (?P<connections>\d+) connections, "
                           r"(?P<transitions>\d+) map changes")
SNAPSHOT_SOURCE = "the last snapshot of "
NEW_MEMORY = "nothing (a new memory)"


def world_counts(raw: bytes) -> tuple[dict | None, str | None]:
    """(The third check's C3-E02) The five counts of one world.jsonl line the AI wrote (maps, tiles learned, warp links,
    connections, map changes: the five it says it loaded), or (None, why) for a line that does not parse or has the wrong
    shape. The AI's output is UNTRUSTED: EVERY exception of the parse and of the counts (ValueError, RecursionError on a
    deeply nested line, TypeError on a field of the wrong type, OverflowError, ...) is a failed line, never the harness's."""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, f"its last line is a JSON {type(data).__name__}, not an object"
        tiles = data.get("tiles_learned") or 0
        if isinstance(tiles, bool) or not isinstance(tiles, int):
            return None, f"its tiles_learned is a {type(tiles).__name__}, not a whole number"
        counts = {"maps": len(data.get("maps") or {}), "tiles": tiles, "warps": len(data.get("warps") or {}),
                  "connections": len(data.get("connections") or []), "transitions": len(data.get("transitions") or [])}
        wrong = [key for key, kind in (("maps", dict), ("warps", dict), ("connections", list), ("transitions", list))
                 if data.get(key) is not None and not isinstance(data.get(key), kind)]
        if wrong:
            return None, f"its {', '.join(wrong)} have the wrong JSON type"
        return counts, None
    except Exception as error:  # noqa: BLE001 - (C3-E02) the AI's output is untrusted: any failure is a failed line
        return None, f"its last line does not parse ({type(error).__name__})"


def _line_parses(raw: bytes) -> bool:
    """One world.jsonl line parses as JSON (any exception of the parse, a RecursionError included, is a bad line)."""
    try:
        json.loads(raw)
        return True
    except Exception:  # noqa: BLE001 - (C3-E02) untrusted: a deeply nested line raises RecursionError, not ValueError
        return False


def stream_world_tail(path: Path, keep: Path | None = None) -> dict:
    """ONE PASS over a world.jsonl, line by line, never a whole-file read: its size, its non-blank lines, the ones that do
    not parse, and its LAST non-blank line, byte for byte (written to `keep` when given): whether it parses as a JSON object
    whose five counts can be read (`world_counts`; maps, tiles learned, warp links, connections, map changes: the five the
    AI says it loaded), its sha256, its size and its counts. (C3-E02) no line the AI wrote can make it raise."""
    size = path.stat().st_size
    lines = bad = 0
    last: bytes | None = None
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.strip():
                continue
            lines += 1
            last = raw
            if not _line_parses(raw):
                bad += 1
    out = {"bytes": size, "lines": lines, "bad_lines": bad, "last_ok": False, "last_sha256": None, "last_bytes": 0,
           "kept": None, "counts": None}
    if last is None:
        return out
    counts, why = world_counts(last)
    out.update({"last_ok": counts is not None, "last_sha256": hashlib.sha256(last).hexdigest(), "last_bytes": len(last),
                "counts": counts})
    if why:
        out["last_problem"] = why
    if keep is not None:
        keep.parent.mkdir(parents=True, exist_ok=True)
        keep.write_bytes(last)
        out["kept"] = str(keep)
    return out


def parse_memory_line(line: str) -> dict | None:
    """The AI's '[AI-WORLD] memory from <source>: N maps (...), T tiles learned, W warp links, C connections, M map
    changes' -> {source, path (a snapshot's file, else None), counts}."""
    found = MEMORY_LINE.search(line)
    if not found:
        return None
    source = found["source"]
    counts = MEMORY_COUNTS.search(line, found.end())
    return {"source": source, "path": source[len(SNAPSHOT_SOURCE):] if source.startswith(SNAPSHOT_SOURCE) else None,
            "new": source == NEW_MEMORY,
            "counts": None if counts is None else {"maps": int(found["maps"]), "tiles": int(counts["tiles"]),
                                                   "warps": int(counts["warps"]),
                                                   "connections": int(counts["connections"]),
                                                   "transitions": int(counts["transitions"])},
            "line": line.strip()[:600]}


def log_counts(lines: Iterable[str]) -> dict:
    """The AI's log, line by line: every 'an unexpected <kind>' LINE by kind and by form (lines, not events: one stop may
    be said more than once), the multichoice lines, the first such line, and the FIRST memory line. (C3-E02) a memory line
    that cannot be read (a count of more digits than int() takes, ...) is kept as an UNREADABLE memory line, with no
    counts and no source, so LC.MEMORY fails that leg; it never raises."""
    out: dict = {"lines": 0, "unexpected": {}, "forms": {}, "multichoice": 0, "first_unexpected": None, "memory": None}
    for line in lines:
        out["lines"] += 1
        found = UNEXPECTED.search(line)
        if found:
            kind = found["kind"]
            form = found["form"] or "other"
            out["unexpected"][kind] = out["unexpected"].get(kind, 0) + 1
            out["forms"][f"{kind} {form}"] = out["forms"].get(f"{kind} {form}", 0) + 1
            if kind == "multichoice":
                out["multichoice"] += 1
            if out["first_unexpected"] is None:
                out["first_unexpected"] = line.strip()[:300]
        if out["memory"] is None and "[AI-WORLD] memory from " in line:
            try:
                out["memory"] = parse_memory_line(line)
            except Exception as error:  # noqa: BLE001 - (C3-E02) the AI's log is untrusted
                out["memory"] = {"source": None, "path": None, "new": False, "counts": None, "line": line.strip()[:600],
                                 "unreadable": f"{type(error).__name__}"}
    return out


def read_log_counts(path: Path) -> dict | None:
    """`log_counts` of the AI's log, or None when there is none (or it is no regular file: a folder, C4-E01). (C3-E02) a
    log that cannot be read to its end (an OS error mid-read, ...) keeps what was counted, marked "error": its lines are
    untrusted input, never the harness's."""
    if not os.path.isfile(path):  # (C4-E01) os.path never raises: a path the OS refuses to stat is no log
        return None
    counted = {"lines": 0}

    def lines(handle) -> Iterable[str]:
        for line in handle:
            counted["lines"] += 1
            yield line
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return log_counts(lines(handle))
    except Exception as error:  # noqa: BLE001 - (C3-E02) an unreadable log is a failed read of that leg, not a crash
        return {"lines": counted["lines"], "unexpected": {}, "forms": {}, "multichoice": 0, "first_unexpected": None,
                "memory": None, "error": f"the AI's log could not be read: {type(error).__name__}"}


# ====================================================================== the rules (pure; unit-tested on planted rows)
def _status(row: dict, check_id: str) -> str | None:
    return next((c["status"] for c in row.get("checks") or [] if c["id"] == check_id), None)


def _norm(path) -> str | None:
    return None if path is None else os.path.normcase(os.path.abspath(str(path)))


def leg_reached(row: dict) -> tuple[bool, str]:
    """C1: L5.THIS_RUN PASS and the target's proof holds on the state the leg left."""
    this_run = _status(row, "L5.THIS_RUN")
    after = row.get("proof_after") or {}
    ok = this_run == PASS and bool(after.get("held"))
    return ok, (f"L5.THIS_RUN {this_run or 'MISSING'}; {row.get('target')}'s proof on the state it left "
                f"{'HOLDS' if after.get('held') else 'does NOT hold'} ({proof_text(after)})")


DEAD_LAUNCH = "harness: the launch died before playing a frame"


def launch_died(row: dict) -> str | None:
    """(The lead's ruling on the verifier's V-08) A leg that RAN whose launch died before playing a frame, by the run's OWN
    exit facts, all four: the harness's stop record (`live_step5.harness_stop`) names no exit by the AI; it counted no
    frame (`real_frames` 0, or None: no verdict file); the AI's log has no line; and no world file was written (the
    verifier's live V1: the sandbox's updater died on its own prompt before the AI started). A launch the disk guard or the
    wall clock KILLED also leaves no verdict file, but it played: its log and its world file say so, and it is not named.
    It still fails the batch (the registered rule: every leg that ran passes purity and THIS_RUN); this only NAMES what
    the exit facts show. Needs the row's measures (`finish_leg`). None: not such a leg."""
    stop = row.get("harness_stop") or {}
    log = (row.get("measures") or {}).get("log") or {}
    if (row.get("status") != "RAN" or not stop or stop.get("by") == "ai" or stop.get("real_frames") or log.get("lines")
            or not no_world_file(row)):
        return None
    return (f"{DEAD_LAUNCH} (the harness's stop record: by {stop.get('by')}, {stop.get('cause')}; real frames "
            f"{stop.get('real_frames')}; {stop.get('elapsed_seconds')} s; no line of the AI's log; no world file)")


def leg_identity_problems(row: dict, job: dict) -> list[str]:
    """(The third check's C3-G01) Does a leg that RAN carry its REGISTERED job in the harness's own records? Its
    environment's AI_PLAYER_SEED is str(seed) and its AI_PLAYER_PERSONALITY the personality, its command's --profile is the
    profile, its arm is '<chain>-<leg>', and its run folder is recorded and lies under profiles/<profile>/ai_player_runs.
    Empty: it does. A row copied from another chain of the same pair, its labels renamed, keeps the other job's records."""
    name = row.get("leg")
    env = row.get("env") if isinstance(row.get("env"), dict) else {}
    command = [str(c) for c in row.get("command") or []]
    at = command.index("--profile") if "--profile" in command else None
    profile = command[at + 1] if at is not None and at + 1 < len(command) else None
    problems: list[str] = []
    if env.get(ENV_SEED) != str(job.get("seed")):
        problems.append(f"{name}'s environment seed {env.get(ENV_SEED)!r} is not the registered {str(job.get('seed'))!r}")
    if env.get(ENV_PERSONALITY) != job.get("personality"):
        problems.append(f"{name}'s environment personality {env.get(ENV_PERSONALITY)!r} is not the registered "
                        f"{job.get('personality')!r}")
    if profile != job.get("profile"):
        problems.append(f"{name}'s command's --profile {profile!r} is not the registered {job.get('profile')!r}")
    if row.get("arm") != f"{job.get('chain')}-{name}":
        problems.append(f"{name}'s arm {row.get('arm')!r} is not {job.get('chain')}-{name}")
    run_dir = row.get("run_dir")
    parts = [part.lower() for part in Path(str(run_dir)).parts] if run_dir else []
    if len(parts) < 4 or parts[-4:-1] != ["profiles", str(job.get("profile")).lower(), "ai_player_runs"]:
        problems.append(f"{name}'s run folder {run_dir!r} is not under profiles/{job.get('profile')}/ai_player_runs")
    return problems


def custody_problems(row: dict, prev: dict | None, job: dict, index: int) -> list[str]:
    """Did this leg start from what the bounds say? (section 4, CUSTODY) Empty: it did. (V-09) Every input is the
    HARNESS's own record (the command it built, the dict of environment keys `run_chain` built, its truth of one state file
    read twice, the sha256 of its one kept file): on a later leg this catches a harness regression, never the AI. (C3-G01)
    every leg first names its REGISTERED job (`leg_identity_problems`)."""
    problems: list[str] = leg_identity_problems(row, job)
    command = [str(c) for c in row.get("command") or []]
    env = row.get("env") if isinstance(row.get("env"), dict) else {}
    keys = tuple(sorted(row.get("env_keys") or []))
    if index == 0:
        if "--fresh" not in command:
            problems.append("L1 did not start with --fresh")
        if "--state" in command:
            problems.append("L1 started from --state")
        if row.get("world_in") is not None:
            problems.append(f"L1 was handed a world memory {row.get('world_in')}")
        if row.get("truth_before") is not None:
            problems.append("L1 has a start truth (a fresh boot has none)")
        if env.get(ENV_STARTER) != job.get("starter"):
            problems.append(f"L1's starter {env.get(ENV_STARTER)!r} is not the chain's {job.get('starter')!r}")
        if keys != ENV_KEYS_FIRST:
            problems.append(f"L1's environment keys {list(keys)} are not {list(ENV_KEYS_FIRST)}")
        return problems
    if prev is None:
        return [*problems, f"{row.get('leg')}: no row of the leg before it"]
    want = str(Path(prev["run_dir"]) / "end_state.ss1") if prev.get("run_dir") else None
    state = command[command.index("--state") + 1] if "--state" in command and command.index("--state") + 1 < len(command) \
        else None
    if "--fresh" in command:
        problems.append(f"{row['leg']} started with --fresh")
    if state is None or want is None or _norm(state) != _norm(want):
        problems.append(f"{row['leg']} started from --state {state}, not {prev.get('leg')}'s end state {want}")
    before, after = row.get("truth_before"), prev.get("truth_after") or {}
    if not before:
        problems.append(f"{row['leg']}'s start truth is UNREAD")
    elif after.get("state_md5") is None or (before.get("frame"), before.get("state_md5")) != (after.get("frame"),
                                                                                             after.get("state_md5")):
        problems.append(f"{row['leg']}'s start truth (frame {before.get('frame')}, md5 {before.get('state_md5')}) is not "
                        f"{prev.get('leg')}'s end truth (frame {after.get('frame')}, md5 {after.get('state_md5')})")
    if row.get("world_in_sha256") is None or row.get("world_in_sha256") != prev.get("kept_world_sha256"):
        problems.append(f"{row['leg']}'s AI_PLAYER_WORLD sha256 {row.get('world_in_sha256')} is not {prev.get('leg')}'s "
                        f"kept last line's {prev.get('kept_world_sha256')}")
    if _norm(row.get("world_in")) != _norm(prev.get("kept_world")):
        problems.append(f"{row['leg']}'s AI_PLAYER_WORLD {row.get('world_in')} is not {prev.get('leg')}'s kept last line "
                        f"{prev.get('kept_world')}")
    if keys != ENV_KEYS_LATER:
        problems.append(f"{row['leg']}'s environment keys {list(keys)} are not {list(ENV_KEYS_LATER)}")
    return problems


def continue_after(row: dict, stop_seen: bool) -> tuple[bool, str]:
    """THE CONTINUATION RULE (C1-C6, registered in the bounds text): (go on, why). The why names each failing condition
    with both values."""
    why: list[str] = []
    reached, reach_text = leg_reached(row)
    if not reached:
        why.append(f"C1 {row.get('target')} not reached: {reach_text}")
    statuses = {c["id"]: c["status"] for c in row.get("checks") or [] if c["id"] in PURITY_IDS}
    wrong = [f"{i} {statuses.get(i, 'MISSING')}" for i in PURITY_IDS if statuses.get(i) != PASS]
    if wrong:
        why.append(f"C2 purity not clean: {', '.join(wrong)}")
    size = (row.get("world_file") or {}).get("bytes")
    world = (row.get("measures") or {}).get("world") or {}
    if not isinstance(size, int):
        why.append("C3 its world.jsonl was not measured")
    elif WORLD_SIZE_KIND == GRADED and size >= WORLD_MAX_BYTES:
        why.append(f"C3 its world.jsonl was {size} bytes, not under {WORLD_MAX_BYTES}")
    if not world.get("last_ok"):
        why.append(f"C3 its world.jsonl's last line did not parse ({world.get('lines')} lines, {world.get('bad_lines')} bad)")
    elif not row.get("kept_world") or not Path(row["kept_world"]).is_file():
        why.append("C3 its last line was not kept")
    if row.get("guard_killed"):
        why.append(f"C4 the disk guard killed it ({(row.get('guard_killed') or {}).get('text')})")
    if row.get("custody"):
        why.append(f"C5 custody: {'; '.join(row['custody'])}")
    if stop_seen:
        why.append("C6 the code under test changed mid-batch (STOP.txt)")
    return not why, "; ".join(why) if why else "C1-C6 held"


def chain_reaches(chain: dict, legs_wanted: int) -> bool:
    """A chain REACHES --to iff every one of its legs RAN and passed C1-C6, the last included."""
    legs = chain.get("legs") or []
    return len(legs) == legs_wanted and legs_wanted > 0 and all(leg.get("status") == "RAN" and leg.get("continue")
                                                                for leg in legs)


def guard_decision(world_bytes: int | None, free: float | None) -> str | None:
    """The disk guard: "free" (under GUARD_FREE_GB free: the batch aborts), "world" (the leg's world.jsonl over
    GUARD_WORLD_BYTES: its launcher is killed), or None."""
    if free is not None and free < GUARD_FREE_GB:
        return "free"
    if world_bytes is not None and world_bytes > GUARD_WORLD_BYTES:
        return "world"
    return None


def newest_world(runs: Path) -> tuple[str | None, int | None]:
    """(the newest run folder's name, its world.jsonl's size): ONLY the newest folder (run_arm names them by time), so a
    world.jsonl whose deletion failed in an older folder cannot kill a healthy later leg. Every stat is OSError-safe: a file
    deleted between the listing and the stat reads None (critic CH-14)."""
    try:
        folders = sorted(p.name for p in runs.iterdir() if p.is_dir())
    except OSError:
        return None, None
    if not folders:
        return None, None
    try:
        return folders[-1], (runs / folders[-1] / "world.jsonl").stat().st_size
    except OSError:
        return folders[-1], None


def leg_of_folder(name: str | None, chain: str) -> str | None:
    """The leg ("L3") of a run folder named `<time>-<chain>-L3`, or None."""
    if not name or f"-{chain}-L" not in name:
        return None
    return name.rsplit("-", 1)[1]


# ====================================================================== the grader (pure; unit-tested on planted rows)
def _check(check_id: str, kind: str, ok: bool, n: int | None, floor: int | None, inputs: Iterable[str], text: str) -> Check:
    return Check(check_id, kind, status_of(ok, n, floor), n, floor, frozenset(inputs), f"{check_id}: {text}",
                 debt=AI_INPUT_DEBT)


def ran_legs(chains: list[dict]) -> list[tuple[dict, dict]]:
    return [(c, leg) for c in chains for leg in c.get("legs") or [] if leg.get("status") in RAN]


def _starter_ok(chain: dict) -> tuple[bool | None, str]:
    legs = chain.get("legs") or []
    first = legs[0] if legs else None
    after = (first or {}).get("truth_after") or {}
    party = after.get("party_exp") or []
    if not first or first.get("status") not in RAN or not party:
        return None, f"{chain.get('chain')}: no party"
    owner = {row[0]: row[1] for row in after.get("party_ot") or []}
    lead = party[0]
    ok = str(lead[1]).upper() == chain.get("starter") and owner.get(lead[0]) == after.get("player_tid") \
        and after.get("player_tid") is not None
    return ok, (f"{chain.get('chain')}: first {lead[1]} (PID {lead[0]}) OT {owner.get(lead[0])}, the player's "
                f"{after.get('player_tid')}; registered {chain.get('starter')}")


def memory_problems(chain: dict) -> tuple[int, list[str], list[str]]:
    """LC.MEMORY over one chain: (legs judged, problems, per-leg lines)."""
    judged, problems, lines = 0, [], []
    legs = chain.get("legs") or []
    for at, leg in enumerate(legs):
        if leg.get("status") not in RAN:
            continue
        said = ((leg.get("measures") or {}).get("log") or {}).get("memory")
        if not said:
            continue
        judged += 1
        name = f"{chain.get('chain')} {leg.get('leg')}"
        if at == 0:
            if not said.get("new"):
                problems.append(f"{name}: L1 said memory from {said.get('source')!r}, not {NEW_MEMORY!r}")
            lines.append(f"{name} from {said.get('source')}")
            continue
        prev = legs[at - 1]
        kept = ((prev.get("measures") or {}).get("world") or {}).get("counts")
        if _norm(said.get("path")) != _norm(leg.get("world_in")):
            problems.append(f"{name}: the memory said is from {said.get('source')!r}, not its AI_PLAYER_WORLD "
                            f"{leg.get('world_in')}")
        if kept is None or said.get("counts") != kept:
            problems.append(f"{name}: the AI's counts {said.get('counts')} are not the kept line's {kept}")
        lines.append(f"{name} {said.get('counts')} vs kept {kept}")
    return judged, problems, lines


#: (V-02) a chain row's identity: a row counts for a registered chain only when every one of these is the job's
IDENTITY = ("chain", "pair", "personality", "starter", "seed", "profile")
#: (V-02) what the re-derivation reads, and what no row carries the inputs of (printed by `grade DIR`)
REDERIVED_TEXT = ("RE-DERIVED from each row's own facts: each leg's proof (the truth's marks against the REGISTERED leg's "
                  "proof), its reach (L5.THIS_RUN and that proof), its custody (custody_problems on the rows, against the "
                  "registered job, joined to the problems the row stored), its kept last line (the file: present, a JSON "
                  "object, its sha256 the row's) and so its "
                  "continuation (C1-C5). READ AS STORED, because no row carries their inputs: L5.THIS_RUN's and the purity "
                  "checks' statuses (their inputs are the launch's verdict file and counters and the end state's write "
                  "time), the world file's measured size (the file is deleted by design: the measurement is its only "
                  "record), the disk guard's mark (grade DIR also reads the marker files on disk), C6 (when STOP.txt "
                  "appeared) and each leg's STATUS (RAN, NOT RUN, ...) with its stored reason. A stored flag can stop a "
                  "chain, never continue one; and since a stored stop could take a leg out of every sample, (C3-G06) a "
                  "NOT RUN leg after a leg whose re-derived continuation holds fails LC.CUSTODY unless STOP.txt or "
                  "ABORT.txt is in --out or (C4-G04) the orchestrator's own events list that chain as salvaged and its "
                  "reason is the salvage reason; (C4-G02) a row whose legs are not exactly the registered ones fails "
                  "LC.CUSTODY, and a STOP.txt beside a frozen record that says the tree held fails LC.FROZEN. (C3-G01) "
                  "every leg that ran must name its registered job in its own records, and no two counted legs share a "
                  "run folder or a kept file.")
#: (C3-G06) how the orchestrator's salvage names a leg a dead chain process never played (`salvage_chain`, `salvage_leg`)
SALVAGE_REASON = "the chain's process ended"
#: (the fourth check's C4-G04) how the orchestrator RECORDS each chain it salvaged, in its own events ("<chain>: salvaged
#: (<why>)", results.json's and results.error.json's "events"): the salvage reason explains a stop only for those chains
SALVAGE_EVENT = ": salvaged ("


def salvaged_chains(events: Iterable | None) -> list[str]:
    """(C4-G04) The chains the orchestrator's own events say it salvaged."""
    return sorted({str(e).split(SALVAGE_EVENT, 1)[0] for e in events or [] if SALVAGE_EVENT in str(e)})


def kept_path(leg: dict, chain: str | None = None, kept_root: Path | None = None) -> str | None:
    """(The third check's C3-G04) The file of a leg's kept last line: the row's stored path; when that is gone and
    `kept_root` (a --out folder that was MOVED after its batch) is given, <kept_root>/<chain>/<leg>/world_last.jsonl, where
    the harness writes it (its sha256 is still checked against the row's)."""
    kept = leg.get("kept_world")
    if kept and Path(kept).is_file():
        return kept
    if kept_root is not None and chain:
        moved = Path(kept_root) / chain / str(leg.get("leg")) / "world_last.jsonl"
        if moved.is_file():
            return str(moved)
    return kept


def kept_problem(leg: dict, path: str | None = None) -> str | None:
    """(V-02) A leg's kept last line, re-read from its FILE (`path`, else the row's): present, its sha256 the row's, a
    JSON object whose five counts can be read (`world_counts`: the AI's bytes are untrusted, C3-E02). None: it holds."""
    kept = path if path is not None else leg.get("kept_world")
    if not kept or not os.path.isfile(str(kept)):
        return f"its kept last line {kept} is not on disk"
    try:
        data = Path(kept).read_bytes()
    except Exception as error:  # noqa: BLE001 - (C4-E01) the AI's bytes, in any file: a failed read never counts
        return f"its kept last line {kept} cannot be read ({type(error).__name__})"
    if hashlib.sha256(data).hexdigest() != leg.get("kept_world_sha256"):
        return f"its kept last line's sha256 is not the row's {leg.get('kept_world_sha256')}"
    counts, why = world_counts(data)
    return None if counts is not None else f"its kept last line is not a JSON object whose five counts can be read ({why})"


def rederived_chain(chain: dict, job: dict, legs: list[dict] | None = None, shared: dict | None = None,
                    stop_files: Iterable[str] = (), kept_root: Path | None = None, salvaged: Iterable[str] = ()) -> dict:
    """(The verifier's V-02) A COPY of one registered chain's row whose every leg that RAN is RE-DERIVED from the row's own
    facts (`REDERIVED_TEXT`): its proof from the truth's marks against the REGISTERED leg's proof (`legs`; the row's own
    proof only when no legs are given), its reach, its custody against the registered job (joined to the stored custody
    problems: a stored problem still counts; with C3-G01 the leg's own records must name that job, and `shared` adds each
    leg's run folder or kept file that another counted leg also has), its kept last line (`kept_root`: a moved --out,
    C3-G04), and so its continuation. A leg continues iff its STORED flag AND the re-derived rule say so. (The checker's
    C2-01) the row's identity (`IDENTITY`) is the job's: a row whose identity is not never reaches here (`registered_chains`
    IGNORES it), so LC.STARTER compares the REGISTERED starter. Every stored flag the facts do not support is listed in the
    copy's "rederived". (C3-G06) a leg that did not run after a leg whose re-derived continuation holds, with no STOP.txt
    or ABORT.txt in --out (`stop_files`) and no salvage, is listed in "custody_chain" (LC.CUSTODY fails); (the fourth
    check's C4-G04) a salvage explains it only when the orchestrator's own events list this chain as salvaged (`salvaged`)
    AND the leg's reason is the salvage reason. (C4-G02) a row whose legs are not exactly the registered legs (their names
    and targets, in order: a leg deleted, added, renamed or moved) is listed there too."""
    out = copy.deepcopy(chain)
    notes: list[str] = []
    unexplained: list[str] = []
    stops = set(stop_files)
    by_salvage = job["chain"] in set(salvaged)
    if legs is not None:
        have = [(leg.get("leg"), leg.get("target")) for leg in out.get("legs") or [] if isinstance(leg, dict)]
        want = [(leg["leg"], leg["target"]) for leg in legs]
        if have != want or len(have) != len(out.get("legs") or []):
            unexplained.append(f"{job['chain']}: its row's legs {have} are not the registered legs {want}: a leg missing, "
                               f"added, renamed or moved never leaves the sample unseen")
    prev: dict | None = None
    for index, leg in enumerate(out.get("legs") or []):
        stored = bool(leg.get("continue"))
        if leg.get("status") == "RAN":
            problems: list[str] = []
            want = legs[index] if legs is not None and index < len(legs) else None
            if legs is not None and (want is None or (leg.get("leg"), leg.get("target")) != (want["leg"], want["target"])):
                problems.append(f"the row's leg {leg.get('leg')} {leg.get('target')} is not the registered "
                                f"{(want or {}).get('leg')} {(want or {}).get('target')}")
            proof = want["proof"] if want is not None else (leg.get("proof") or {})
            after = leg.get("truth_after")
            leg["proof_after"] = (proof_holds(after.get("marks"), proof) if after else
                                  {"held": False, "missing": ["(no end truth)"], "failing": [], "values": {}})
            leg["reached"] = leg_reached(leg)[0]
            leg["harness"] = launch_died(leg)
            # a stored custody problem still counts (a stored flag may stop a leg, never clear one): the union
            leg["custody"] = list(dict.fromkeys([*(leg.get("custody") or []), *custody_problems(leg, prev, job, index),
                                                 *((shared or {}).get(str(leg.get("leg"))) or [])]))
            path = kept_path(leg, job["chain"], kept_root)
            kept = kept_problem(leg, path)
            if kept is not None:
                problems.append(f"C3 {kept}")
            go, why = continue_after({**leg, "kept_world": path}, False)
            if not go:
                problems.append(why)
            leg["continue"] = stored and not problems
            if stored and problems:
                text = "; ".join(problems)
                notes.append(f"{job['chain']} {leg.get('leg')}: its stored continue is True, the re-derived rule says "
                             f"no: {text[:400]}")
                leg["why"] = f"RE-DERIVED: {text}"
                if out.get("stopped_at") is None:
                    out.update({"stopped_at": leg.get("leg"), "stop_reason": f"RE-DERIVED: {text}"})
        elif (leg.get("status") not in RAN and prev is not None and prev.get("status") == "RAN" and prev.get("continue")
              and not stops and not (by_salvage and str(leg.get("reason") or "").startswith(SALVAGE_REASON))):
            unexplained.append(f"{job['chain']} {leg.get('leg')}: {leg.get('status')} after {prev.get('leg')}, whose "
                               f"re-derived continuation holds, with no STOP.txt or ABORT.txt in --out and no salvage the "
                               f"orchestrator recorded for this chain (its stored reason: {str(leg.get('reason'))[:200]!r})")
        prev = leg
    out["rederived"] = notes
    out["custody_chain"] = unexplained
    out["reached_to"] = chain_reaches(out, len(legs) if legs is not None else len(out.get("legs") or []))
    return out


def shared_legs(rows: list[tuple[dict, dict]]) -> dict[str, dict[str, list[str]]]:
    """(The third check's C3-G01) Two legs of the counted rows that share a run folder or a kept file never both count:
    {chain: {leg: [why]}} for every leg (RAN, SALVAGED or ERROR) whose run_dir or kept_world another such leg also has."""
    owners: dict[tuple[str, str | None], list[tuple[str, str]]] = {}
    for chain, job in rows:
        for leg in chain.get("legs") or []:
            if leg.get("status") not in RAN:
                continue
            for key in ("run_dir", "kept_world"):
                if leg.get(key):
                    owners.setdefault((key, _norm(leg[key])), []).append((job["chain"], str(leg.get("leg"))))
    out: dict[str, dict[str, list[str]]] = {}
    for (key, _), found in owners.items():
        if len(found) > 1:
            for chain, leg in found:
                others = ", ".join(f"{c} {l}" for c, l in found if (c, l) != (chain, leg))
                out.setdefault(chain, {}).setdefault(leg, []).append(
                    f"{leg}'s {key} is also {others}'s: two legs never share one, so neither counts")
    return out


def registered_chains(chains: list[dict], jobs: list[dict], legs: list[dict] | None = None,
                      stop_files: Iterable[str] = (), kept_root: Path | None = None,
                      salvaged: Iterable[str] = ()) -> tuple[list[dict], list[str], list[str]]:
    """(The verifier's V-02) The rows that COUNT, in the jobs' order: each registered chain's ONE row, re-derived
    (`rederived_chain`). Returns (those rows, the rows IGNORED with why, the stored flags the facts do not support). A row
    of a chain that is not registered never counts, a registered chain with two rows counts neither, and (the checker's
    C2-01) a row whose chain, pair, personality, starter, seed or profile (`IDENTITY`) is not the registered job's is
    IGNORED the same way, named with its reason: its registered chain is then ABSENT (LC.CUSTODY's "every registered
    chain's L1 ran" fails, and a floor may read VACUOUS). (C3-G01) two counted legs that share a run folder or a kept file
    (`shared_legs`) fail custody."""
    registered = [job["chain"] for job in jobs]
    rows: dict = {}
    for chain in chains:
        rows.setdefault(chain.get("chain"), []).append(chain)
    ignored = [f"{name}: not a registered chain of this batch ({len(found)} row(s)): never counted"
               for name, found in rows.items() if name not in registered]
    ignored += [f"{name}: {len(rows[name])} rows for one registered chain: none of them counts" for name in registered
                if len(rows.get(name) or []) > 1]
    counted: list[tuple[dict, dict]] = []
    for job in jobs:
        found = rows.get(job["chain"]) or []
        if len(found) != 1:
            continue
        wrong = [f"its {key} {found[0].get(key)!r} is not the registered {job.get(key)!r}" for key in IDENTITY
                 if found[0].get(key) != job.get(key)]
        if wrong:
            ignored.append(f"{job['chain']}: its row is not the registered job's ({'; '.join(wrong)}): it never counts, "
                           f"so the chain is ABSENT")
            continue
        counted.append((found[0], job))
    shared = shared_legs(counted)
    salvaged = list(salvaged)
    kept = [rederived_chain(row, job, legs, shared.get(job["chain"]), stop_files, kept_root, salvaged)
            for row, job in counted]
    return kept, ignored, [note for chain in kept for note in chain.get("rederived") or []]


def grade_batch(chains: list[dict], jobs: list[dict], legs_wanted: int, reach_min: int,
                frozen: tuple[bool, str] | None = None, leftover: list[str] | None = None,
                reported: dict | None = None, legs: list[dict] | None = None, stop_files: Iterable[str] = (),
                kept_root: Path | None = None, salvaged: Iterable[str] = ()) -> list[Check]:
    """THE GRADED BOUNDS of the bounds text over a batch's chain rows (each with every leg's row, NOT RUN ones included).
    `jobs` are the REGISTERED chains: (V-02) only their rows count, each RE-DERIVED from its own facts against the
    registered `legs` (`registered_chains`; `stop_files`: which of STOP.txt and ABORT.txt are in --out, C3-G06;
    `kept_root`: a moved --out, C3-G04; `salvaged`: the chains the orchestrator's own events say it salvaged, C4-G04);
    `reported` carries the harness's own records for the reported checks (world files left after the sweep, the
    profiles' listings, the main profile, the most chains at once). Every check quotes both values. (The fourth check's
    C4-G02) a STOP.txt in --out (written only when the tree moved) beside a frozen record that says it held fails
    LC.FROZEN: a planted stop file never explains a hidden leg while the watch reads clean."""
    reported = reported or {}
    checks: list[Check] = []
    expected = len(jobs)
    stop_files = list(stop_files)
    if frozen is not None and frozen[0] and STOP_FILE in stop_files:
        frozen = (False, f"{STOP_FILE} is in --out (the batch writes it only when the tree moved) but the frozen-tree "
                         f"record says it held ({frozen[1]}): the two disagree, so LC.FROZEN FAILS")
    chains, ignored, rederived = registered_chains(chains, jobs, legs, stop_files, kept_root, salvaged)
    by_name = {c.get("chain"): c for c in chains}
    ran = ran_legs(chains)
    floor = max(len(ran), expected)
    # LC.REACH
    reached = [c["chain"] for c in chains if chain_reaches(c, legs_wanted)]
    stopped = [f"{c.get('chain')} at {c.get('stopped_at')}: {str(c.get('stop_reason'))[:200]}" for c in chains
               if not chain_reaches(c, legs_wanted)]
    present = [j["chain"] for j in jobs if j["chain"] in by_name]
    checks.append(_check("LC.REACH", GRADED, len(reached) >= reach_min, len(present), expected, (GAME, HARNESS),
                         f"chains reaching the target (every leg continued, the last reached by the game): {len(reached)} "
                         f"of {len(present)} (bound: at least {reach_min} of {expected}); reached {reached or 'none'}; "
                         f"not: {stopped or 'none'}; rows IGNORED (V-02): {ignored or 'none'}; stored flags the "
                         f"re-derived rule does not support: {rederived or 'none'}"))
    # LC.PURITY
    judged, bad = 0, []
    for chain, leg in ran:
        statuses = {c["id"]: c["status"] for c in leg.get("checks") or [] if c["id"] in PURITY_IDS}
        if statuses:
            judged += 1
            wrong = [f"{i} {statuses.get(i, 'MISSING')}" for i in PURITY_IDS if statuses.get(i) != PASS]
            if wrong:
                bad.append(f"{chain.get('chain')} {leg.get('leg')}: "
                           + (f"{DEAD_LAUNCH}; " if leg.get("harness") else "") + ", ".join(wrong))
    checks.append(_check("LC.PURITY", GRADED, not bad and judged == len(ran), judged, floor, (HARNESS,),
                         f"purity CLEAN on every leg that ran: {judged - len(bad)} of {judged} judged legs with every "
                         f"counting purity check PASS, of {len(ran)} legs that ran (want every one; floor {floor}); "
                         f"failing: {bad or 'none'}"))
    # LC.THIS_RUN
    fresh = [(chain.get("chain"), leg.get("leg"), _status(leg, "L5.THIS_RUN")) for chain, leg in ran]
    read = [f for f in fresh if f[2] is not None]
    dead = {(chain.get("chain"), leg.get("leg")) for chain, leg in ran if leg.get("harness")}
    stale = [f"{c} {l} {s}" + (f" ({DEAD_LAUNCH})" if (c, l) in dead else "") for c, l, s in read if s != PASS]
    checks.append(_check("LC.THIS_RUN", GRADED, not stale and len(read) == len(ran), len(read), floor, (HARNESS, GAME),
                         f"L5.THIS_RUN PASS on {len(read) - len(stale)} of {len(read)} legs read, of {len(ran)} that ran "
                         f"(want every one; floor {floor}); not: {stale or 'none'}"))
    # LC.WORLD_SIZE
    sizes = [(f"{chain.get('chain')} {leg.get('leg')}", (leg.get("world_file") or {}).get("bytes")) for chain, leg in ran]
    measured = [(name, size) for name, size in sizes if isinstance(size, int)]
    big = [f"{name} {size}" for name, size in measured if size >= WORLD_MAX_BYTES]
    checks.append(_check("LC.WORLD_SIZE", WORLD_SIZE_KIND, not big and len(measured) == len(ran), len(measured), floor,
                         (HARNESS,), f"{'(information, never counted) ' if WORLD_SIZE_KIND == REPORTED else ''}every leg's "
                                     f"world.jsonl, measured before its deletion, under {WORLD_MAX_BYTES} bytes: largest "
                                     f"{max((s for _, s in measured), default=None)}; at or over: {big or 'none'}; not "
                                     f"measured: {[n for n, s in sizes if not isinstance(s, int)] or 'none'}"))
    # LC.CUSTODY (critic CH-06: every registered chain's L1 ran)
    unlaunched = [j["chain"] for j in jobs
                  if not ((by_name.get(j["chain"]) or {}).get("legs") or [{}])[0].get("status") == "RAN"]
    custody_bad = [f"{chain.get('chain')} {leg.get('leg')}: {'; '.join(leg.get('custody') or ['not checked'])}"
                   for chain, leg in ran if leg.get("status") != "RAN" or leg.get("custody") is None or leg.get("custody")]
    # (C3-G06) a leg that did not run after a continuing leg, unexplained: a stored stop never hides a leg unseen
    custody_bad += [problem for chain in chains for problem in chain.get("custody_chain") or []]
    custody_judged = sum(1 for _, leg in ran if leg.get("status") == "RAN" and leg.get("custody") is not None)
    checks.append(_check("LC.CUSTODY", GRADED, not unlaunched and not custody_bad, custody_judged, floor, (HARNESS, GAME),
                         f"every registered chain's L1 ran ({expected - len(unlaunched)} of {expected}; not: "
                         f"{unlaunched or 'none'}) and every leg that ran started from what the bounds say "
                         f"({custody_judged - sum(1 for _, leg in ran if leg.get('custody'))} of {len(ran)}); problems: "
                         f"{custody_bad or 'none'}"))
    # LC.STARTER
    starters = [_starter_ok(c) for c in chains]
    judged_starters = [(ok, text) for ok, text in starters if ok is not None]
    wrong_starters = [text for ok, text in judged_starters if not ok]
    checks.append(_check("LC.STARTER", GRADED, not wrong_starters, len(judged_starters), reach_min, (GAME,),
                         f"the registered starter, the player's own, leads the party L1 left: {len(judged_starters) - len(wrong_starters)} "
                         f"of {len(judged_starters)} chains (floor {reach_min}); wrong: {wrong_starters or 'none'}"))
    # LC.MEMORY (B1 debt, declared)
    memory_judged, memory_bad, memory_lines = 0, [], []
    for chain in chains:
        n, problems, lines = memory_problems(chain)
        memory_judged += n
        memory_bad += problems
        memory_lines += lines
    checks.append(_check("LC.MEMORY", GRADED, not memory_bad and memory_judged == len(ran), memory_judged, floor, (AI, HARNESS),
                         f"the AI's memory line on {memory_judged} of {len(ran)} legs that ran (want every one; floor "
                         f"{floor}): L1 from nothing, each later leg from its AI_PLAYER_WORLD with the kept line's counts; "
                         f"wrong: {memory_bad or 'none'}; per leg: {' | '.join(memory_lines) or 'none'}"))
    if frozen is not None:
        checks.append(_check("LC.FROZEN", GRADED, bool(frozen[0]), 1, 1, (HARNESS,), f"the frozen-tree watch: {frozen[1]}"))
    if leftover is not None:
        checks.append(_check("LC.LEFTOVER", GRADED, not leftover, 1, 1, (HARNESS,),
                             f"python processes naming {PROFILE_PREFIX} after the batch: {leftover or 'none'} (want none)"))
    checks += reported_checks(chains, legs_wanted, reported)
    return checks


def no_world_file(leg: dict) -> bool:
    """(V-08) The leg never had a world.jsonl: none was measured and none was there to delete (a launch that died before
    playing a frame writes none)."""
    world = leg.get("world_file") or {}
    return world.get("bytes") is None and not world.get("present")


def reported_checks(chains: list[dict], legs_wanted: int, reported: dict) -> list[Check]:
    """The REPORTED checks: information, never counted (each prints FAIL in its own line when its property did not hold)."""
    checks: list[Check] = []
    ran = ran_legs(chains)
    progress, shares = [], []
    for chain in chains:
        legs = chain.get("legs") or []
        reached = [leg["leg"] for leg in legs if leg.get("status") == "RAN" and leg_reached(leg)[0]]
        progress.append(f"{chain.get('chain')}: reached {reached or 'none'}"
                        + ("" if chain_reaches(chain, legs_wanted) else f", stopped at {chain.get('stopped_at')}"))
        for leg in legs:
            stop = leg.get("harness_stop") or {}
            if leg.get("status") in RAN and isinstance(stop.get("real_frames"), int):
                shares.append((stop["real_frames"] / max(1, leg.get("frames") or 1), f"{chain.get('chain')} {leg.get('leg')}",
                               stop["real_frames"], leg.get("frames"), leg.get("elapsed"), leg.get("wall")))
    top = max(shares, default=None)
    checks.append(_check("LC.PROGRESS", REPORTED, all(chain_reaches(c, legs_wanted) for c in chains), len(chains), None,
                         (GAME, HARNESS), f"(information) {'; '.join(progress) or 'none'}; per leg real frames / budget, "
                                          f"s / wall: " + "; ".join(f"{n} {f}/{b} {e}/{w:g}" for _, n, f, b, e, w in shares)
                         + (f"; the most of its budget a leg used: {top[1]} {top[0]:.0%}" if top else "")))
    multi = [(f"{c.get('chain')} {leg.get('leg')}", ((leg.get("measures") or {}).get("log") or {})) for c, leg in ran]
    flagged = [f"{n} {m.get('multichoice')} ({m.get('forms')}; first: {m.get('first_unexpected')})" for n, m in multi
               if m.get("multichoice")]
    checks.append(_check("LC.MULTICHOICE", REPORTED, not flagged, len(multi), None, (AI,),
                         f"(information) LINES of ai_player.log saying 'an unexpected multichoice' (lines, not events) per "
                         f"leg: " + "; ".join(f"{n} {m.get('multichoice')}" for n, m in multi)
                         + f"; legs over 0: {flagged or 'none'}; every 'an unexpected <kind>' by kind: "
                         + ("; ".join(f"{n} {m.get('unexpected')}" for n, m in multi if m.get("unexpected")) or "none")))
    outcomes, disagree = [], []
    for c, leg in ran:
        stop = leg.get("harness_stop") or {}
        claim = None
        if leg.get("outcome") and stop.get("by") == "ai":
            claim = leg["outcome"] == f"play: done: {leg.get('target')} reached"
        held = bool((leg.get("proof_after") or {}).get("held"))
        mark = "no claim" if claim is None else "agree" if claim == held else "DISAGREE"
        outcomes.append(f"{c.get('chain')} {leg.get('leg')} {leg.get('outcome')!r} vs game {'held' if held else 'not held'}: {mark}")
        if mark == "DISAGREE":
            disagree.append(outcomes[-1])
    checks.append(_check("LC.OUTCOME", REPORTED, not disagree, len(outcomes), None, (AI, GAME),
                         f"(information) the AI's exit claim beside the game's proof: {'; '.join(outcomes) or 'none'}"))
    ended = [f"{c.get('chain')} {leg.get('leg')} {(leg.get('harness_stop') or {}).get('by')} "
             f"({(leg.get('harness_stop') or {}).get('cause')})" for c, leg in ran]
    checks.append(_check("LC.ENDED", REPORTED, all((leg.get("harness_stop") or {}).get("by") == "ai" for _, leg in ran),
                         len(ran), None, (HARNESS,), f"(information) who ended each leg: {'; '.join(ended) or 'none'}"))
    optional = reported.get("optional") or {}
    checks.append(_check("LC.OPTIONAL", REPORTED, True, len(optional), None, (GAME,),
                         f"(information) the optional milestones' proofs at each chain's last leg that ran: "
                         + ("; ".join(f"{k}: {v}" for k, v in optional.items()) or "none")))
    worlds = [f"{c.get('chain')} {leg.get('leg')} "
              + ("no world file" if no_world_file(leg) else
                 f"{(leg.get('world_file') or {}).get('bytes')} B, "
                 f"{((leg.get('measures') or {}).get('world') or {}).get('lines')} lines, deleted "
                 f"{(leg.get('world_file') or {}).get('deleted')}") for c, leg in ran]
    totals = {c.get("chain"): sum((leg.get("world_file") or {}).get("bytes") or 0 for leg in c.get("legs") or [])
              for c in chains}
    left = reported.get("world_left") or []
    # (V-08) a leg that never had a world file has nothing to delete: it is "no world file", never "not deleted"
    undeleted = [w for c, leg in ran for w in [f"{c.get('chain')} {leg.get('leg')}"]
                 if not no_world_file(leg) and not (leg.get("world_file") or {}).get("deleted")]
    checks.append(_check("LC.WORLD", REPORTED, not left and not undeleted, len(ran), None, (HARNESS,),
                         f"(information) per leg: {'; '.join(worlds) or 'none'}; per chain total bytes {totals}; not deleted "
                         f"after its leg: {undeleted or 'none'}; still present after the end sweep: {left or 'none'}"))
    profiles = reported.get("profiles")
    checks.append(_check("LC.PROFILES", REPORTED, profiles is not None and not profiles.get("problems"), len(chains), None,
                         (HARNESS,), f"(information) {profiles.get('text') if profiles else 'not measured'}"))
    main = reported.get("main_profile")
    checks.append(_check("LC.MAIN_PROFILE", REPORTED, main is not None and main.get("unchanged"), 1, None, (HARNESS,),
                         f"(information) {MAIN_PROFILE}: {main.get('text') if main else 'not measured'}"))
    most = reported.get("most_running")
    checks.append(_check("LC.CONCURRENCY", REPORTED, most is not None and most <= PARALLEL, 1, None, (HARNESS,),
                         f"(information) the most chains running at once: {most} (bound {PARALLEL})"))
    return checks


def batch_verdict(checks: list[Check]) -> str:
    """PASS iff every GRADED check PASSES (no waivers: a VACUOUS check fails)."""
    return typed_verdict(checks, waivers={})


def check_lines(checks: list[Check]) -> list[str]:
    lines = [f"  [{c.status}] {c.id} {c.kind} n/floor {'-' if c.n is None else c.n}/{'-' if c.floor is None else c.floor} "
             f"inputs {'+'.join(sorted(c.inputs))}: {c.text}" for c in checks]
    debts = [c for c in checks if c.id in AI_INPUT_DEBT and c.kind == GRADED]
    for c in debts:
        lines.append(f"B1 DEBT {c.id} ({c.status}): reads the AI's {AI_INPUT_DEBT[c.id]['ai_input']}; why: "
                     f"{AI_INPUT_DEBT[c.id]['plan']}")
    if not debts:
        lines.append("B1 DEBT: none")
    return lines


def optional_report(chains: list[dict], data: dict, to_chapter: int) -> dict:
    """LC.OPTIONAL: at each chain's last leg that ran, every optional milestone's proof for chapters up to the target's."""
    optional = [m for m in data.get("milestones") or [] if m.get("optional") and m["chapter"] <= to_chapter]
    out = {}
    for chain in chains:
        last = next((leg for leg in reversed(chain.get("legs") or []) if leg.get("status") in RAN), None)
        marks = ((last or {}).get("truth_after") or {}).get("marks")
        out[chain.get("chain")] = {m["id"]: proof_holds(marks, {"flags": m["done"].get("flags") or {},
                                                                "variables": m["done"].get("variables") or {},
                                                                "trainers": m["done"].get("trainers") or {}})["held"]
                                   for m in optional} if marks else "no end truth"
    return out


# ====================================================================== one chain (the child process)
def utf8_safe(value: object) -> object:
    """(The fourth check's C4-E04) `value` with every str in it (dict keys too, through lists and tuples) made writable
    as UTF-8: a str that cannot be encoded (a lone surrogate the AI wrote, read back by json) is kept with those characters
    ESCAPED as text ('\\ud800'), so no write of it can raise; every other str is returned unchanged."""
    if isinstance(value, str):
        try:
            value.encode("utf-8")
            return value
        except UnicodeEncodeError:
            return value.encode("utf-8", "backslashreplace").decode("utf-8")
    if isinstance(value, dict):
        return {utf8_safe(key): utf8_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [utf8_safe(item) for item in value]
    return value


def safe_text(value: object, limit: int = 300) -> str:
    """str(value), cut to `limit`, NEVER raising (the third check's C3-E06: an exception whose str() raises must not
    break the ERROR record): repr, then the type's name; (C4-E04) always writable as UTF-8."""
    try:
        text = str(value)
    except Exception:  # noqa: BLE001
        try:
            text = repr(value)
        except Exception:  # noqa: BLE001
            text = f"<a {type(value).__name__} that cannot be printed>"
    return utf8_safe(text[:limit])


def error_text(error: BaseException) -> str:
    """'<type>: <message>', never raising; (C3-E06) a SyntaxError also names its file's repository path (its own message
    names the file's last part only)."""
    text = f"{type(error).__name__}: {safe_text(error)}"
    filename = getattr(error, "filename", None) if isinstance(error, SyntaxError) else None
    return f"{text} in {filename}" if filename else text


def dig(value: object, *keys: str) -> object:
    """value[k1][k2]... through dicts only, None at the first step that is not a dict: (C3-E02) the reader of a file the
    AI wrote, whose shape is untrusted."""
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def untrusted_text(value: object) -> str | None:
    """(C3-E02) A value the AI wrote, kept as text (None stays None); (C4-E04) text that cannot be written as UTF-8 (a lone
    surrogate) is kept ESCAPED, so writing its row can never raise."""
    return None if value is None else utf8_safe(value) if isinstance(value, str) else safe_text(value, 200)


def judged(check: Callable[[], None], what: str, notes: list) -> None:
    """(The third check's C3-E02) Run one check of the AI's output (its verdict file and counters): an exception leaves the
    checks it would have made MISSING, so they fail and the chain stops, with a note; it never ends the chain process."""
    try:
        check()
    except Exception as error:  # noqa: BLE001 - the AI's output is untrusted: a failed read is a failed check
        notes.append(f"{what} could not judge the AI's output ({type(error).__name__}: {safe_text(error, 200)}): its "
                     f"checks are MISSING, so they fail")


def _truth_subset(truth: dict | None) -> dict | None:
    if not truth:
        return None
    story = truth.get("story") or {}
    return {"frame": truth.get("frame"), "map": truth.get("map"), "state_md5": truth.get("state_md5"),
            "marks": story.get("marks"), "stats": story.get("stats"), "party_exp": truth.get("party_exp"),
            "party_ot": truth.get("party_ot"), "player_tid": truth.get("player_tid")}


def check_rows(checks) -> list[dict]:
    return [{"id": c.id, "kind": c.kind, "status": c.status, "n": c.n, "floor": c.floor, "text": c.text} for c in checks]


def _write_json(path: Path, data) -> None:
    """`data` as JSON, written whole (a temp file, then os.replace); (C4-E04) every str made writable first (`utf8_safe`):
    a row holding the AI's text never fails to write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    text = json.dumps(utf8_safe(data), ensure_ascii=False, indent=1, default=lambda value: safe_text(value, 10 ** 6))
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def not_run_row(job: dict, leg: dict, status: str, reason: str) -> dict:
    return {"chain": job["chain"], "leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"],
            "proof": leg["proof"], "frames": leg["frames"], "wall": leg["wall"], "status": status, "reason": reason,
            "checks": [], "continue": False}


def new_chain_row(job: dict) -> dict:
    return {**{k: job.get(k) for k in ("chain", "pair", "personality", "starter", "seed", "profile")},
            "to": job["legs"][-1]["target"] if job.get("legs") else None, "legs": [], "reached_to": False,
            "stopped_at": None, "stop_reason": None}


def write_chain(out: Path, chain: dict, legs_wanted: int) -> None:
    chain["reached_to"] = chain_reaches(chain, legs_wanted)
    _write_json(out / "rows" / f"{chain['chain']}.json", chain)


def stop_rest(job: dict, chain: dict, start: int, reason: str, status: str = "NOT RUN") -> None:
    """Every leg from `start` on gets a row that says why it was not run (and is in no check's sample)."""
    for leg in job["legs"][start:]:
        chain["legs"].append(not_run_row(job, leg, status, reason))


def child_refusal(job: dict, profile: str) -> str | None:
    """The child's profile guard: it plays only in its own chain's NEW profile, never in the main one."""
    if not str(job.get("profile", "")).startswith(PROFILE_PREFIX):
        return f"the chain's profile {job.get('profile')!r} does not start with {PROFILE_PREFIX!r}"
    if job.get("profile") == MAIN_PROFILE or profile == MAIN_PROFILE:
        return f"refusing to play in {MAIN_PROFILE}"
    if profile != job.get("profile"):
        return f"live_step5.PROFILE is {profile!r}, not this chain's {job.get('profile')!r}"
    return None


#: (the fourth check's C4-E01) a world.jsonl the OS refuses to open (another process may still hold it as its leg ends) is
#: read again up to this many times, this many seconds apart, before it is recorded as NOT MEASURED (its leg fails C3)
WORLD_READ_TRIES = 3
WORLD_READ_PAUSE_SECONDS = 1.0


def finish_leg(row: dict, run_dir: Path | None, keep: Path) -> None:
    """Section 6.3 inside the child, BEFORE the next leg: the world.jsonl's size recorded, streamed once (its last line
    kept outside the repo), then DELETED; the log counted; the small files copied. Writes into `row`. (The fourth check's
    C4-E01) the run folder is the AI's, so its files are untrusted in KIND too, and this NEVER raises: a world.jsonl that
    is no regular file (a folder) is NOT MEASURED; one the OS refuses to open (after WORLD_READ_TRIES tries), a measurement
    or a deletion that raises, and a small file that cannot be copied are each a NOTE; a leg not measured fails C3, so the
    batch is GRADED (both in the chain process and in the orchestrator's `salvage_leg`)."""
    measures: dict = {"log": None, "world": None}
    world_file = {"bytes": None, "deleted": False, "present": False}
    notes = row.setdefault("notes", [])
    if run_dir is not None and os.path.isdir(run_dir):
        world_path = run_dir / "world.jsonl"
        if os.path.isfile(world_path):  # (C4-E01) os.path never raises; a folder named world.jsonl is no world file
            size_first, why = None, None
            for attempt in range(WORLD_READ_TRIES):
                if attempt:
                    time.sleep(WORLD_READ_PAUSE_SECONDS)
                try:
                    size_first = world_path.stat().st_size
                    measures["world"] = stream_world_tail(world_path, keep / "world_last.jsonl")
                    break
                except Exception as error:  # noqa: BLE001 - (C4-E01) the AI's file: a failed read is a failed check
                    measures["world"], why = None, f"{type(error).__name__}: {safe_text(error, 200)}"
            if measures["world"] is None:
                notes.append(f"world.jsonl could not be read in {WORLD_READ_TRIES} tries ({why}): NOT MEASURED, so the "
                             f"leg fails C3")
            try:
                world_file = measure_then_delete(world_path)
            except Exception as error:  # noqa: BLE001 - (C4-E01) recorded; the end sweep tries again
                world_file = {"bytes": None, "deleted": False, "present": True}
                notes.append(f"world.jsonl could not be measured and deleted ({type(error).__name__}: "
                             f"{safe_text(error, 200)}): the end sweep tries again")
            sizes = [s for s in (size_first, world_file.get("bytes"), (measures["world"] or {}).get("bytes"))
                     if isinstance(s, int)]
            if size_first is not None and world_file.get("bytes") != size_first:
                notes.append(f"world.jsonl was {size_first} bytes at first and {world_file.get('bytes')} at its "
                             f"deletion: the larger is graded")
            world_file["bytes"] = max(sizes) if sizes else None
            if not world_file.get("deleted"):
                notes.append("world.jsonl could not be DELETED after 5 tries (recorded; the end sweep retries)")
        elif os.path.lexists(world_path):
            world_file["present"] = True
            notes.append("world.jsonl is not a regular file (a folder?): NOT MEASURED, so the leg fails C3")
        measures["log"] = read_log_counts(run_dir / "ai_player.log")
        for name in ("actions.jsonl", "ai_player.log", "purity.json", "end_state.ss1", "stdout.txt"):
            if os.path.isfile(run_dir / name):
                try:
                    keep.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(run_dir / name, keep / name)
                except Exception as error:  # noqa: BLE001 - (C4-E01) a copy is a record, never the grade's input
                    notes.append(f"{name} could not be copied ({type(error).__name__}: {safe_text(error, 200)})")
    world = measures["world"] or {}
    row["measures"], row["world_file"] = measures, world_file
    row["kept_world"] = world.get("kept")
    row["kept_world_sha256"] = world.get("last_sha256")


def guard_mark(out: Path, chain: str, leg: str) -> dict | None:
    marker = out / chain / f"{leg}.KILLED.json"
    if not marker.is_file():
        return None
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"cause": "unknown", "text": "an unreadable marker"}


def run_chain(job: dict, run_leg: Callable | None = None) -> dict:
    """ONE CHAIN (spec section 4): its legs one after another in this process, each through `run_leg` (live:
    `live_step5.run_arm`; the tests pass a stub). Writes each leg's row and the chain row after EVERY leg; a chain that
    misses stops, its later legs NOT RUN with the reason."""
    from ai_player.gates import live_step5 as L5
    from ai_player.gates.live_step2 import check_purity

    run_leg = run_leg or L5.run_arm
    out = Path(job["out"])
    build_root = Path(job["build_root"])
    legs = job["legs"]
    chain = new_chain_row(job)
    refusal = child_refusal(job, L5.PROFILE)
    if refusal is not None:
        stop_rest(job, chain, 0, f"REFUSED: {refusal}", status="REFUSED")
        chain.update({"stopped_at": "L1", "stop_reason": f"REFUSED: {refusal}"})
        write_chain(out, chain, len(legs))
        return chain
    carried: dict = {}
    prev: dict | None = None
    for index, leg in enumerate(legs):
        for name, why in ((STOP_FILE, "the code under test changed mid-batch (STOP.txt)"),
                          (ABORT_FILE, "the batch was ABORTED by the harness (disk: free space)")):
            if (out / name).is_file():
                stop_rest(job, chain, index, why)
                chain.update({"stopped_at": leg["leg"], "stop_reason": why})
                write_chain(out, chain, len(legs))
                return chain
        arm_name = f"{job['chain']}-{leg['leg']}"
        _write_json(out / job["chain"] / "current_leg.json", {"leg": leg["leg"], "arm": arm_name,
                                                              "started": time.strftime("%Y-%m-%d %H:%M:%S")})
        fresh = prev is None
        env = L5.play_env(job["personality"], job["starter"] if fresh else None, leg["target"])
        arm = L5.Arm(arm_name, f"{job['chain']} {leg['leg']}: chapter {leg['chapter']} to {leg['target']} "
                               f"({job['personality']}, {job['starter']}, seed {job['seed']})",
                     leg["frames"], leg["wall"], env, seed=job["seed"], fresh=fresh,
                     state_from=None if fresh else prev["arm"])
        keep = out / job["chain"] / leg["leg"]
        try:
            run = run_leg(arm, build_root, carried)
        except Exception as error:  # noqa: BLE001 - a crashed leg still has its world measured and deleted
            row = salvage_leg(job, leg, build_root, out, arm_name, f"ERROR: the leg raised {type(error).__name__}: "
                                                                    f"{safe_text(error, 400)}", status="ERROR")
            chain["legs"].append(row)
            stop_rest(job, chain, index + 1, f"the chain stopped at {leg['leg']}: it raised {type(error).__name__}")
            chain.update({"stopped_at": leg["leg"], "stop_reason": row["reason"]})
            write_chain(out, chain, len(legs))
            return chain
        # (C3-E02) the verdict file and its counters are the AI process's output: a value of the wrong shape leaves the
        # checks it would have made MISSING (so they fail and the chain stops), never a dead chain process
        judged(lambda: check_purity(run, None), "the purity checks", run.notes)
        judged(lambda: L5.check_after_is_this_run(run), "L5.THIS_RUN", run.notes)
        sent = {ENV_BRAIN: "play", ENV_SEED: str(arm.seed), **arm.env}
        if run.world_in is not None:
            sent[ENV_WORLD] = str(run.world_in)
        before, after = _truth_subset(run.before), _truth_subset(run.after)
        proof_before = (proof_holds(before.get("marks"), leg["proof"]) if before
                        else None if fresh else {"unread": True, "held": None})
        row = {"chain": job["chain"], "leg": leg["leg"], "chapter": leg["chapter"], "target": leg["target"],
               "proof": leg["proof"], "frames": leg["frames"], "wall": leg["wall"], "arm": arm_name, "status": "RAN",
               "reason": None, "exit": run.exit_code, "elapsed": round(run.elapsed or 0, 1),
               "run_dir": str(run.run_dir) if run.run_dir else None, "command": [str(c) for c in run.command],
               "env": sent, "env_keys": sorted(sent), "world_in": str(run.world_in) if run.world_in else None,
               "world_in_sha256": file_sha256(run.world_in) if run.world_in and Path(run.world_in).is_file() else None,
               "start_state": str(run.start_state) if run.start_state else None,
               "truth_before": before, "truth_after": after, "proof_before": proof_before,
               "proof_after": proof_holds((after or {}).get("marks"), leg["proof"]) if after else
               {"held": False, "missing": ["(no end truth)"], "failing": [], "values": {}},
               "already_held": (proof_before or {}).get("held") if proof_before else (False if fresh else None),
               "checks": check_rows(run.checks), "harness_stop": run.measures.get("harness_stop"),
               "outcome": untrusted_text(dig(run.verdict, "facts", "exit_reason")),
               "gate_line": next((ln for ln in run.stdout.splitlines() if ln.startswith("[AI-GATE]")), None),
               "notes": list(run.notes)}
        row["reached"] = leg_reached(row)[0]
        finish_leg(row, run.run_dir, keep)
        row["harness"] = launch_died(row)
        row["guard_killed"] = guard_mark(out, job["chain"], leg["leg"])
        end_state = (run.run_dir / "end_state.ss1") if run.run_dir else None
        # (spec section 4) the next leg gets the KEPT last line as its world memory, never the deleted original (F6/F8)
        carried.pop(arm_name, None)
        if end_state is not None and end_state.is_file() and row["kept_world"]:
            # (C3-E02) actions.jsonl is the AI's: a record that is not a JSON object is no page it read
            reads = [r for r in run.earlier + run.records if isinstance(r, dict) and r.get("decision") == "read"]
            carried[arm_name] = (end_state, Path(row["kept_world"]), reads)
        row["custody"] = custody_problems(row, prev, job, index)
        go, why = continue_after(row, (out / STOP_FILE).is_file())
        if row["harness"]:
            why = f"{row['harness']}; {why}"
        row["continue"], row["why"] = go, why
        _write_json(keep / "row.json", row)
        chain["legs"].append(row)
        if not go:
            stop_rest(job, chain, index + 1, f"the chain stopped at {leg['leg']}: {why}")
            chain.update({"stopped_at": leg["leg"], "stop_reason": why})
            write_chain(out, chain, len(legs))
            return chain
        write_chain(out, chain, len(legs))
        prev = {**row, "arm": arm_name}
    write_chain(out, chain, len(legs))
    return chain


def salvage_leg(job: dict, leg: dict, build_root: Path, out: Path, arm_name: str, reason: str,
                status: str = "SALVAGED") -> dict:
    """A leg whose child died (or raised): the NEWEST run folder named for THIS leg's arm (critic CH-13: never the
    previous leg's folder) has its world.jsonl measured and DELETED and gets a row with NO checks (purity and THIS_RUN
    read it as not judged: VACUOUS, which fails). No such folder: NOT RUN (the process ended before the launch)."""
    runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
    try:
        folders = sorted(p for p in runs.iterdir() if p.is_dir() and p.name.endswith(f"-{arm_name}"))
    except OSError:
        folders = []
    if not folders:
        return not_run_row(job, leg, "NOT RUN", f"{reason}; no run folder of {arm_name}: the process ended before its "
                                                f"launch")
    row = {**not_run_row(job, leg, status, reason), "arm": arm_name, "run_dir": str(folders[-1]), "notes": [],
           "truth_before": None, "truth_after": None, "harness_stop": None}
    finish_leg(row, folders[-1], out / job["chain"] / leg["leg"])
    row["notes"].append("NO CHILD ROW: salvaged by the orchestrator; its world.jsonl was measured and deleted; no check "
                        "was made, so purity and freshness read it as not judged")
    return row


def salvage_chain(job: dict, build_root: Path, out: Path, why: str) -> dict:
    """A chain whose child left no complete chain row: its done legs are kept, the leg it was playing is salvaged
    (`salvage_leg`), the later legs are NOT RUN with the reason."""
    path = out / "rows" / f"{job['chain']}.json"
    chain = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else new_chain_row(job)
    done = {leg["leg"] for leg in chain["legs"]}
    current = None
    marker = out / job["chain"] / "current_leg.json"
    if marker.is_file():
        try:
            current = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            current = None
    salvaged = False
    for index, leg in enumerate(job["legs"]):
        if leg["leg"] in done:
            continue
        if not salvaged and current and current.get("leg") == leg["leg"]:
            row = salvage_leg(job, leg, build_root, out, current["arm"], f"the chain's process ended during this leg ({why})")
            chain["legs"].append(row)
            salvaged = True
            chain.update({"stopped_at": leg["leg"], "stop_reason": row["reason"]})
            continue
        chain["legs"].append(not_run_row(job, leg, "NOT RUN", f"the chain's process ended ({why}; see "
                                                              f"out/{job['chain']}.child.log)"))
        if chain.get("stopped_at") is None:
            chain.update({"stopped_at": leg["leg"], "stop_reason": f"the chain's process ended ({why})"})
    write_chain(out, chain, len(job["legs"]))
    return chain


def child(job_path: Path) -> int:
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    # (C3-H02, C4-H02) the truth reads' environment (live_step2.clean_env copies this one) drops every refused PYTHON*
    for name in [name for name in os.environ if python_env_refused(name)]:
        os.environ.pop(name, None)
    from ai_player.gates import live_step5 as L5

    L5.PROFILE = job["profile"]
    chain = run_chain(job)
    print(f"[{job['chain']}] " + "; ".join(f"{leg['leg']} {leg['status']}"
                                           + (f" reached {leg.get('reached')}" if leg["status"] == "RAN" else "")
                                           for leg in chain["legs"]), flush=True)
    return 0


# ====================================================================== the batch (the orchestrator)
def leftover_processes(prefix: str | None = None) -> list[str]:
    """Python processes whose command line names this batch's profiles; never any other (the bot tuner runs beside)."""
    prefix = prefix or PROFILE_PREFIX
    try:
        done = subprocess.run(["powershell", "-NoProfile", "-Command",
                               "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine "
                               f"-like '*{prefix}*' }} | ForEach-Object {{ \"$($_.ProcessId) $($_.CommandLine)\" }}"],
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return [f"could not list the processes: {error}"]
    return [line.strip()[:200] for line in done.stdout.decode(errors="replace").splitlines() if line.strip()]


def safe_free(path: Path) -> float | None:
    try:
        return free_gb(path)
    except OSError:
        return None


def default_build_root() -> Path:
    """The build root the truth harness reads (`probe_eyes.boot` resolves it with no argument), so the only one a graded
    batch may play in (critic CH-08)."""
    from ai_player.host import launcher

    return (launcher.PACKAGE_ROOT / "sandbox-pokebot").resolve()


def git_state(repo: Path | None = None) -> dict:
    """R9's facts: HEAD and origin/main after a fetch, and every TRACKED file changed (critic CH-08: the whole tree)."""
    repo = repo or REPO

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, timeout=120,
                              check=True).stdout.strip()
    try:
        git("fetch", "-q", "origin")
        return {"head": git("rev-parse", "HEAD"), "origin": git("rev-parse", "origin/main"),
                "dirty": [ln for ln in git("status", "--porcelain", "--untracked-files=no").splitlines() if ln.strip()]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"head": None, "origin": None, "dirty": [], "error": str(error)[:300]}


def g3_scan() -> list:
    from ai_player.gates.check_grader_imports import scan

    return scan(REPO, ("ai_player.gates.live_chain",))


def watch_tree():
    from ai_player.gates.provenance import watch

    return watch(REPO, explicit=True)


def code_line() -> str:
    from ai_player.gates.provenance import provenance

    return provenance(REPO)


def snapshot() -> object:
    from ai_player.gates.provenance import snapshot_tree

    return snapshot_tree(REPO)


def child_env() -> dict[str, str]:
    """(The third check's C3-H02, the fourth check's C4-H02) The environment of a chain process: this one's without every
    PYTHON* variable PYTHON_ENV_ALLOWED does not list (PYTHONPATH, PYTHONHOME, PYTHONSTARTUP, PYTHONPYCACHEPREFIX,
    PYTHONCASEOK, PYTHONUSERBASE, ...), so neither the chain process nor the truth reads it starts load another file in
    place of a hashed one."""
    return {k: v for k, v in os.environ.items() if not python_env_refused(k)}


class ChildProcess:
    """One chain's child: `py -B live_chain.py child JOB.json`, its output in `<chain>.child.log`."""

    def __init__(self, job_path: Path, log_path: Path) -> None:
        self.log = open(log_path, "w", encoding="utf-8")
        env = {**child_env(), "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        self.proc = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "child", str(job_path)],
                                     cwd=str(REPO), env=env, stdout=self.log, stderr=subprocess.STDOUT, creationflags=flags)
        self.pid = self.proc.pid

    def poll(self) -> int | None:
        code = self.proc.poll()
        if code is not None and not self.log.closed:
            self.log.close()
        return code

    def kill_tree(self) -> None:
        kill_descendants(self.pid)
        try:
            self.proc.kill()
        except OSError:
            pass


def spawn_child(job: dict, job_path: Path, log_path: Path) -> ChildProcess:
    return ChildProcess(job_path, log_path)


@dataclass
class Deps:
    """The orchestrator's side effects, injected (the tests run a whole batch with stub launches, a temp ledger and a temp
    evidence folder; spec section 8)."""
    spawn: Callable = spawn_child
    free: Callable[[Path], float | None] = safe_free
    git_state: Callable[[], dict] = git_state
    leftover: Callable[[], list[str]] = leftover_processes
    g3: Callable[[], list] = g3_scan
    #: (the checker's C2-05) the grader's import closure against GRADER_FILES: (missing, closure size, seconds)
    closure: Callable[[], tuple[list[str], int, float]] = closure_missing
    watch: Callable[[], object] = watch_tree
    snapshot: Callable[[], object] = snapshot
    code_line: Callable[[], str] = code_line
    default_build_root: Callable[[], Path] = default_build_root
    kill: Callable[[int], list] = kill_descendants
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    ledger_path: Path | None = None
    evidence_dir: Path | None = None
    #: the repository R1 and R8 measure --out and the build root against (None: this one; a test puts a temp tree here)
    repo: Path | None = None
    poll_seconds: float = 5.0
    stagger: float | None = None
    tree_every: float = 60.0
    events: list = field(default_factory=list)


def schedule(jobs: list[dict], spawn: Callable, tick: Callable, parallel: int, stagger: float, sleep: Callable,
             may_start: Callable, poll_seconds: float) -> dict:
    """At most `parallel` chains at once, `stagger` seconds apart, in the jobs' order; `tick(running)` after every pass (the
    disk guard, the watchdog, the frozen tree). Returns the most chains it ever had running, the start order and the chains
    it did not start (with why)."""
    pending = list(jobs)
    running: list[tuple[dict, object]] = []
    most = 0
    order: list[str] = []
    not_started: list[tuple[dict, str]] = []
    while pending or running:
        while pending and len(running) < parallel:
            job = pending.pop(0)
            ok, why = may_start(job)
            if not ok:
                not_started.append((job, why))
                continue
            running.append((job, spawn(job)))
            order.append(job["chain"])
            most = max(most, len(running))
            if pending:
                sleep(stagger)
        tick(running)
        for item in list(running):
            if item[1].poll() is not None:
                running.remove(item)
        if pending or running:
            sleep(poll_seconds)
    return {"most_running": most, "order": order, "not_started": not_started}


def run_refusal(args, facts: dict) -> str | None:
    """Every refusal JUDGED FROM FACTS before `ledger.begin` (spec section 7, R1-R9, the critique's additions; R11: --out
    missing or empty, the verifier's V-01, or (C3-E01) one that can never be made: a file above it, a missing drive; R12: a
    graded batch whose grader code could be a file the registration does not hash (`closure_missing`, the checkers' C2-05,
    C3-H01, C3-H02, C4-H01..H06), a closure that cannot be scanned (C3-E06), or a PYTHON* variable set that
    PYTHON_ENV_ALLOWED does not list (C3-H02, C4-H02)),
    pure: `facts` are what the orchestrator measured (`gather_facts`). None: the batch may go on; it may still be refused
    by R11 when --out cannot actually be MADE or written (`prepare_out`, still before the ledger) and by the ledger (R10)."""
    repo = Path(facts["repo"])
    out, build_root = Path(facts["out"]), Path(facts["build_root"])
    graded = args.purpose == "graded"
    if out == repo or out.is_relative_to(repo):
        return f"R1: --out {out} is inside the repository; the summaries and kept lines live outside it (section 6)"
    # (the verifier's V-01, graded AND development) an earlier batch's STOP.txt or ABORT.txt in --out stops every chain
    # before its first leg, AFTER ledger.begin has spent the seeds; its rows would be re-graded as this batch's
    if facts.get("out_error"):
        return f"R11: --out {out}: {facts['out_error']}; give a new or an empty folder"
    entries = facts.get("out_entries") or []
    if entries:
        return (f"R11: --out {out} exists and is NOT EMPTY ({len(entries)} entries: {entries[:8]}): an earlier batch's "
                f"STOP.txt, ABORT.txt or rows would be read as this batch's after the ledger began, spending the seeds; "
                f"give a new or an empty folder")
    learner = [p for p in (out, build_root) if "pokebot-learner" in (part.lower() for part in p.parts)]
    if learner:
        return f"R8: {learner[0]} lies in a folder named pokebot-learner: the learner clone is never touched"
    if not build_root.is_relative_to(repo):
        return f"R8: the build root {build_root} is not under this repository {repo}"
    if graded:
        given = [name for name in ("first_seed", "to", "chains", "leg_frames", "prediction_file")
                 if getattr(args, name, None) is not None]
        if given or args.run not in GRADED_RUNS:
            return (f"R2: a graded batch plays exactly a registered run ({sorted(GRADED_RUNS)}) and nothing else: "
                    f"--run {args.run!r}, given {['--' + g.replace('_', '-') for g in given] or 'nothing more'}")
        if Path(facts["default_build_root"]) != build_root:
            return (f"R2: a graded batch plays in the build root the truth harness reads ({facts['default_build_root']}), "
                    f"not {build_root}")
    else:
        missing = [name for name in ("first_seed", "to", "prediction_file") if getattr(args, name, None) is None]
        if missing:
            return f"R3: a development batch needs {['--' + m.replace('_', '-') for m in missing]} (registered and predicted)"
        if args.run is not None:
            return "R3: --run names a GRADED registration; a development batch gives --first-seed and --to"
        if facts.get("prediction_error"):
            return f"R3: {facts['prediction_error']}"
    if facts.get("legs_error"):
        return f"R4: {facts['legs_error']}"
    if facts.get("g3"):
        return f"R5: the G-3 walk of ai_player.gates.live_chain found an AI import: {facts['g3']}"
    if graded and facts.get("closure_error"):
        # (the third check's C3-E06) a closure file that does not parse: the scan names it, and nothing is begun
        return (f"R12: the grader's import closure could not be scanned ({facts['closure_error']}), so what it runs "
                f"cannot be shown to be hashed")
    # (the checkers' C2-05, C3-H01, C3-H02, C4-H01..H06) a file the grade imports or runs that the registration did not
    # hash; (C4-H05) a refusal text is RETURNED only when there is one: no value of this check skips the ones below
    closure = closure_refusal(facts.get("closure_missing") or []) if graded else None
    if closure:
        return closure
    if graded and facts.get("python_env"):
        # (C3-H02, C4-H02) each changes which file Python loads (other folders first, another cache folder, names
        # without case, another user site-packages, a file run at start, ...)
        return (f"R12: {', '.join(facts['python_env'])} is set: a graded run allows no PYTHON* variable but "
                f"{', '.join(PYTHON_ENV_ALLOWED)} (none changes which file Python loads); unset it and run again")
    if graded:
        git = facts.get("git") or {}
        if git.get("error") or not git.get("head") or git.get("head") != git.get("origin"):
            return (f"R9: a graded batch runs on a PUSHED commit: HEAD {git.get('head')} is not origin/main "
                    f"{git.get('origin')} {git.get('error') or ''}".rstrip())
        if git.get("dirty"):
            return f"R9: tracked files are changed: {git['dirty'][:8]}"
    else:
        named = facts.get("named") or []
        if named:
            return (f"R3: the development seeds {facts.get('seeds')} are named by ledger entries "
                    f"{[e['id'] for e in named]}: a rehearsal on them would replay their trajectories (critic CH-15)")
    free = facts.get("free")
    if free is None or free < FREE_MIN_GB:
        return f"R6: {free if free is None else round(free, 1)} GB free on the build root's drive, under the {FREE_MIN_GB:g} GB floor"
    if facts.get("profiles_exist"):
        return f"R7: the profiles {facts['profiles_exist']} exist under {build_root / 'profiles'}: each chain needs a NEW one"
    return None


def out_listing(out: Path) -> dict:
    """(The verifier's V-01) What --out holds before the batch: {"out_entries": every name in it, sorted (empty when it does
    not exist)}, or {"out_error": why it cannot be a batch's --out} when it is not a folder or cannot be listed, or (the
    third check's C3-E01) when it does not exist and cannot be created: the nearest path above it that exists is a file
    (a typo), or nothing above it exists (a missing drive). `prepare_out` then tries what no listing can show (an invalid
    name, no permission) by making it, before ledger.begin."""
    if not out.exists():
        for parent in out.parents:
            if parent.exists():
                if not parent.is_dir():
                    return {"out_error": f"it cannot be created: {parent} above it is not a folder"}
                return {"out_entries": []}
        return {"out_error": "it cannot be created: no folder above it exists (a missing drive?)"}
    if not out.is_dir():
        return {"out_error": "it exists and is not a folder"}
    try:
        return {"out_entries": sorted(p.name for p in out.iterdir())}
    except OSError as error:
        return {"out_error": f"it cannot be listed: {error}"}


def gather_facts(args, deps: Deps) -> dict:
    """What `run_refusal` judges, measured once (each piece robust to the arguments it has)."""
    repo = repo_root()
    facts: dict = {"repo": Path(deps.repo).resolve() if deps.repo else repo, "out": Path(args.out).resolve(),
                   "default_build_root": Path(deps.default_build_root())}
    facts["build_root"] = Path(args.build_root).resolve() if args.build_root else facts["default_build_root"]
    graded = args.purpose == "graded"
    run = GRADED_RUNS.get(args.run) if graded else None
    to = run["to"] if run else (None if graded else args.to)
    chains = 6 if graded else (args.chains or 3)
    first = run["seeds"][0] if run else args.first_seed
    facts.update({"to": to, "chains": chains, "first": first})
    try:
        legs = legs_of(to, load_milestones(repo))
        if not graded:
            override = parse_leg_frames(args.leg_frames, legs)
            facts["override"] = override
            legs = [{**leg, "frames": override.get(leg["leg"], leg["frames"])} for leg in legs]
        facts["legs"] = legs
        facts["jobs"] = jobs_of(first, chains) if first is not None else []
    except Refusal as error:
        facts["legs_error"] = str(error)
    if not graded and args.prediction_file is not None:
        try:
            raw = Path(args.prediction_file).read_bytes()
            # (the verifier's V-06) the sha256 registered is of the FILE's bytes, so `sha256sum prediction.txt` matches it
            facts["prediction_sha256"] = hashlib.sha256(raw).hexdigest()
            facts["prediction"] = raw.decode("utf-8").strip()
            if not facts["prediction"]:
                facts["prediction_error"] = f"the prediction file {args.prediction_file} is empty"
        except (OSError, UnicodeDecodeError) as error:
            facts["prediction_error"] = f"the prediction file cannot be read as UTF-8 text: {error}"
    facts.update(out_listing(facts["out"]))
    facts["g3"] = deps.g3()
    # (the checker's C2-05) measured for every batch, refused (R12) for a graded one; its cost is printed
    try:
        facts["closure_missing"], facts["closure_size"], facts["closure_seconds"] = deps.closure()
    except Exception as error:  # noqa: BLE001 - (C3-E06) a file that does not parse is named, never a crash
        facts.update({"closure_missing": [], "closure_size": None, "closure_seconds": None,
                      "closure_error": error_text(error)})
    # (C3-H02, C4-H02) a graded run is refused while one is set (`run_refusal`), even set to nothing
    facts["python_env"] = sorted(name for name in os.environ if python_env_refused(name))
    if first is not None:
        facts["seeds"] = run["seeds"] if run else seeds_of(first, chains)
    if graded:
        facts["git"] = deps.git_state()
    elif first is not None:
        facts["named"] = seeds_named(*facts["seeds"], path=deps.ledger_path)
    facts["free"] = deps.free(facts["build_root"])
    facts["profiles_exist"] = [j["profile"] for j in facts.get("jobs") or []
                               if (facts["build_root"] / "profiles" / j["profile"]).exists()]
    return facts


def run_folders(build_root: Path) -> dict[str, list[str]]:
    """Every profile's run folders (profile -> names), for LC.PROFILES."""
    out: dict[str, list[str]] = {}
    try:
        profiles = [p for p in (build_root / "profiles").iterdir() if p.is_dir()]
    except OSError:
        return out
    for profile in profiles:
        try:
            out[profile.name] = sorted(p.name for p in (profile / "ai_player_runs").iterdir() if p.is_dir())
        except OSError:
            continue
    return out


def profiles_report(before: dict, after: dict, chains: list[dict], jobs: list[dict]) -> dict:
    """LC.PROFILES (REPORTED, critic CH-10): each chain's profile holds one run folder per leg that ran, named for it, and
    no profile but the chain's own gained a folder named for one of this batch's arms."""
    problems, lines = [], []
    by_name = {c.get("chain"): c for c in chains}
    for job in jobs:
        arms = sorted(f"{job['chain']}-{leg['leg']}" for leg in (by_name.get(job["chain"]) or {}).get("legs") or []
                      if leg.get("status") in RAN and leg.get("run_dir"))
        folders = after.get(job["profile"], [])
        found = sorted(next((a for a in arms if name.endswith("-" + a)), name) for name in folders)
        if found != arms:
            problems.append(f"{job['profile']}: folders {folders} for the legs {arms}")
        lines.append(f"{job['profile']} {len(folders)} folders")
    ours = {j["profile"] for j in jobs}
    for profile, names in after.items():
        new = set(names) - set(before.get(profile, []))
        strays = [n for n in new if "-LC-" in n and profile not in ours]
        if strays:
            problems.append(f"{profile} gained {strays}")
    return {"problems": problems, "text": f"{'; '.join(lines)}; problems: {problems or 'none'}"}


def main_profile_state(build_root: Path) -> dict:
    profile = build_root / "profiles" / MAIN_PROFILE
    state = profile / "current_state.ss1"
    runs = profile / "ai_player_runs"
    try:
        folders = sorted(p.name for p in runs.iterdir()) if runs.is_dir() else []
    except OSError:
        folders = ["(unreadable)"]
    try:
        mark = [state.stat().st_mtime_ns, file_sha256(state)] if state.is_file() else None
    except OSError:
        mark = ["(unreadable)"]
    return {"present": profile.is_dir(), "folders": folders, "state": mark}


def end_sweep(jobs: list[dict], build_root: Path) -> list[str]:
    """After the batch: any world.jsonl still in the chains' profiles is deleted again; what could not be is reported."""
    left = []
    for job in jobs:
        runs = build_root / "profiles" / job["profile"] / "ai_player_runs"
        if not runs.is_dir():
            continue
        for world in runs.glob("*/world.jsonl"):
            record = measure_then_delete(world)
            if not record.get("deleted"):
                left.append(f"{world} {record.get('bytes')} bytes (could not be deleted)")
            else:
                left.append(f"{world} {record.get('bytes')} bytes (deleted by the end sweep)")
    return left


def evidence_path(evidence_dir: Path, graded: bool, to: str, first: int) -> Path:
    stamp = time.strftime("%Y-%m-%d")
    return evidence_dir / (f"{stamp}-chain-heldout.txt" if graded else f"{stamp}-chain-heldout-dev-{to}-{first}.txt")


#: (the third check's C3-E05) the ERROR path's own record, written BESIDE a complete results.json, never over it
RESULTS_ERROR = "results.error.json"
#: (C3-E03) what the ERROR path leaves in --out when the ledger cannot be written at all: `finish-entry DIR` reads it
UNFINISHED = "ledger.unfinished.json"
#: (C3-E03) a ledger finish is tried this many times, this many seconds apart (a lock another writer holds, a ledger file
#: another program has open): the computed verdict first, and only then the ERROR verdict
FINISH_TRIES = 3
FINISH_PAUSE_SECONDS = 2.0
#: (C3-E06, C3-E07) the stage the guard names in an ERROR verdict ("... while <the text>")
STAGES = {"chains": "while the chains ran", "grading": "while grading", "evidence": "while writing the evidence",
          "results.json": "while writing results.json", "ledger": "while writing the ledger"}
BOUNDS_HEADING = "BOUNDS TEXT (hashed into the registration):"


#: (the fourth check's C4-E02) the file a launch creates FIRST in --out, EXCLUSIVELY (os.O_EXCL): its claim that this --out
#: is its own. A second launch of the same batch on the same --out cannot create it, so it is refused (R11) before
#: ledger.begin and removes only what it made itself, never the first launch's job files
OUT_CLAIM = "BATCH.claim.json"


class OutTaken(Exception):
    """(C4-E02) --out was claimed by another launch, or written by another process, between the listing and the claim."""


def prepare_out(out: Path, files: dict[str, object]) -> list[Path]:
    """(The third check's C3-E01) --out and the files the batch writes there before any chain (the chains' job files),
    made BEFORE ledger.begin. (The fourth check's C4-E02) --out is first CLAIMED: OUT_CLAIM is created with os.O_EXCL,
    which only one process can do, and --out must then hold nothing else; only after that are the job files written.
    RAISES `Refusal` (R11) when --out cannot be created or written (a file in its path, a missing drive, an invalid name,
    no permission) or another launch holds it, after removing what THIS call made, so the ledger is never begun on an --out
    the batch cannot use. Returns what it made (the folders it created, recorded BEFORE mkdir so a failure part-way
    removes them too, C4-E07; then the claim, each file and its temp file), for `undo_out`."""
    made: list[Path] = []
    try:
        made += sorted((p for p in (out, *out.parents) if not p.exists()), key=lambda p: len(p.parts))
        out.mkdir(parents=True, exist_ok=True)
        claim = out / OUT_CLAIM
        try:
            handle = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise OutTaken(f"--out {out} is CLAIMED by another launch ({OUT_CLAIM} is there): another batch is using "
                           f"it") from None
        made.append(claim)
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps({"pid": os.getpid(), "claimed": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
        others = sorted(p.name for p in out.iterdir() if p.name != OUT_CLAIM)
        if others:
            raise OutTaken(f"--out {out} is no longer empty ({len(others)} entries: {others[:8]}): another process wrote "
                           f"into it after it was listed")
        for name, data in files.items():
            path = out / name
            made += [path, path.with_name(path.name + ".tmp")]
            _write_json(path, data)
    except OutTaken as error:
        undo_out(made)
        raise Refusal(f"R11: {error}; give a new or an empty folder") from None
    except Exception as error:  # noqa: BLE001 - any failure to make or write --out is R11's, before the ledger
        undo_out(made)
        raise Refusal(f"R11: --out {out} cannot be created or written ({type(error).__name__}: {safe_text(error)}); give a "
                      f"folder this process can create and write") from None
    return made


def undo_out(made: list[Path]) -> None:
    """Remove what `prepare_out` made (its files, then the folders it created, deepest first, a folder only when empty), so
    a batch refused by the ledger leaves --out as it found it (R11 would refuse that --out next time otherwise)."""
    for path in sorted(made, key=lambda p: len(p.parts), reverse=True):
        try:
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink(missing_ok=True)
        except OSError:
            pass


def entry_finished(entry_id: int, verdict: str, path: Path) -> bool:
    """The ledger entry is "done" with exactly this verdict (False when the ledger cannot be read)."""
    try:
        entry = next((e for e in ledger.load(path).get("entries", []) if e.get("id") == entry_id), None)
    except Exception:  # noqa: BLE001
        return False
    return bool(entry) and entry.get("status") == "done" and entry.get("verdict") == verdict


def finish_entry(entry_id: int, verdict: str, evidence: str | None, path: Path, sleep: Callable[[float], None],
                 tries: int = FINISH_TRIES) -> str | None:
    """(The third check's C3-E03) `ledger.finish`, tried up to `tries` times, FINISH_PAUSE_SECONDS apart. None when the
    entry is finished with `verdict` (re-read after a failed try, in case it was written); else why the last try failed."""
    why = None
    for attempt in range(tries):
        if attempt:
            sleep(FINISH_PAUSE_SECONDS)
        try:
            ledger.finish(entry_id, verdict, evidence, path=path)
            return None
        except Exception as error:  # noqa: BLE001 - retried; the caller decides what a ledger it cannot write means
            why = f"{type(error).__name__}: {safe_text(error)}"
            if entry_finished(entry_id, verdict, path):
                return None
    return why


class LedgerUnwritten(Exception):
    """(C3-E03) The batch's computed verdict could not be written to the ledger after FINISH_TRIES tries."""


def stop_children(handles: list[tuple[str, object]], interrupts: list | None = None) -> list[str]:
    """(The chains-run guard) Kill every chain process still running, with its launcher's process tree (`kill_tree`): the
    guard's first step when the harness raised while the chains ran. One line per chain it acted on. (C4-E03) a Ctrl+C
    here is noted in `interrupts` and the next chain is still killed."""
    lines: list[str] = []
    for chain, handle in handles:
        try:
            if handle.poll() is None:
                handle.kill_tree()
                lines.append(f"{chain}: its process (pid {handle.pid}) was still running: killed")
        except BaseException as error:  # noqa: BLE001 - (C4-E03) a second Ctrl+C never stops the guard
            if interrupts is not None and not isinstance(error, Exception):
                interrupts.append(f"{type(error).__name__} while killing {chain}")
            lines.append(f"{chain}: its process could not be killed ({type(error).__name__}: {safe_text(error, 200)})")
    return lines


def note_interrupt(ctx: dict, error: BaseException) -> None:
    """(C4-E03) A BaseException that is no Exception (a second Ctrl+C) caught by a step of the guard: noted, so the guard
    raises KeyboardInterrupt again once the entry is written."""
    if not isinstance(error, Exception):
        ctx.setdefault("interrupts", []).append(f"{type(error).__name__} at the stage {ctx.get('stage')}")


def hold_interrupts(error: BaseException, ctx: dict) -> Callable[[], None]:
    """(The fourth check's C4-E03) The guard's first step: ONE line at once (the guard can take seconds: killing the chains,
    their world files' deletion retries), then SIGINT is IGNORED until the entry is written, so a second Ctrl+C cannot
    leave it 'started' with nothing written. Returns the call that restores the previous handler (always run). In a thread
    that cannot set a handler, nothing is ignored: each step of the guard still notes an interrupt and goes on."""
    try:
        print(f"[LC] the harness stopped ({type(error).__name__} {STAGES.get(ctx.get('stage'), '')}): killing the running "
              f"chains, then finishing ledger entry #{ctx.get('entry_id')} as ERROR; Ctrl+C is ignored until that is "
              f"written", flush=True)
    except BaseException:  # noqa: BLE001 - a line that cannot be printed never stops the guard
        pass
    try:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    except (ValueError, OSError, AttributeError):  # not the main thread
        return lambda: None

    def restore() -> None:
        try:
            signal.signal(signal.SIGINT, previous if previous is not None else signal.default_int_handler)
        except (ValueError, OSError, TypeError):
            pass
    return restore


def run_batch(args, deps: Deps | None = None) -> int:
    """THE BATCH: refusals; every step that needs no chain (--out and the job files, the profile snapshots: BEFORE the
    ledger, the third check's C3-E01 and C3-G05); the ledger's begin; the chains (at most PARALLEL at once); salvage, the
    end sweep, the grade, one evidence file, results.json and the ledger's finish. Exit 0 PASS (graded) or ran
    (development), 1 FAIL, 2 refused, 3 ABORTED, 4 ERROR. (The checkers' C2-07, C3-E03 and the chains-run guard) from
    ledger.begin to the ledger's finish the harness is GUARDED: an exception while the chains run (every running chain
    process is killed first, then the end sweep deletes their world files) or while grading or writing the evidence,
    results.json or the ledger FINISHES the entry with `error_verdict`'s ERROR naming the stage (neither PASS nor FAIL: the
    seeds are spent) and writes whatever evidence it can with the traceback (`finish_on_error`); a Ctrl+C
    (KeyboardInterrupt) does the same and then stops the process. (The fourth check's C4-E03) the guard prints one line
    at once and IGNORES a second Ctrl+C until the entry is written (`hold_interrupts`); one that slips in is noted by each
    step and the finish goes on, and an entry already finished with the computed verdict is never overwritten. A failed
    ledger write is retried with the computed verdict before it falls back to ERROR (`finish_entry`). The entry stays
    "started" only after a HARD KILL of this process, or when the ledger cannot be written at all: then the evidence and
    the output say it is NOT finished, with the command that finishes it, and the exit is still 4. (C4-E02) --out is
    claimed exclusively before anything is written there (`prepare_out`); (C4-G04) the grade's salvage exemption reads
    the orchestrator's own salvage events."""
    from ai_player.gates.provenance import keep_earlier, line_digest

    deps = deps or Deps()
    graded = args.purpose == "graded"
    facts = gather_facts(args, deps)
    refusal = run_refusal(args, facts)
    if refusal is not None:
        print(f"REFUSED: {refusal}", flush=True)
        return 2
    missing = facts.get("closure_missing") or []
    if facts.get("closure_error"):
        print(f"[LC] the grader's import closure could NOT be scanned: {facts['closure_error']} (a development batch is "
              f"not refused)", flush=True)
    print(f"[LC] the grader's import closure: {facts.get('closure_size')} files, "
          + (f"{len(missing)} NOT hashed (a development batch is not refused): {missing}" if missing else
             "every one hashed") + f" (scan {facts.get('closure_seconds')} s)", flush=True)
    out, build_root = facts["out"], facts["build_root"]
    legs, jobs, seeds, to = facts["legs"], facts["jobs"], facts["seeds"], facts["to"]
    chains_n, reach_min = facts["chains"], reach_min_of(facts["chains"])
    prediction = facts.get("prediction")
    # (V-06) the sha256 of the prediction FILE's bytes (`gather_facts`), not of its stripped text
    development = None if graded else {"chains": chains_n, "leg_frames_override": facts.get("override") or {},
                                       "prediction_sha256": facts["prediction_sha256"]}
    numbers = registered_numbers(args.run if graded else None, to, seeds, chains_n, legs, repo_root(), development)
    sha = ledger.numbers_sha256(numbers)
    code = deps.code_line()
    tree = deps.watch()
    kept = deps.snapshot()
    print(f"[LC] numbers sha256 {sha} (seeds {seeds[0]}-{seeds[1]}, {args.purpose}); code: {code}; tree kept: {kept}",
          flush=True)
    # (the third check's C3-E01, C3-G05) every step that needs no chain runs BEFORE ledger.begin: an --out that cannot be
    # made or written is refused with the seeds unspent, and between begin and the guard nothing can raise
    began = time.strftime("%Y-%m-%d %H:%M:%S")
    main_before = main_profile_state(build_root)
    folders_before = run_folders(build_root)
    events: list[str] = deps.events
    stagger = STAGGER_SECONDS if deps.stagger is None else deps.stagger
    watchdog = chain_watchdog_seconds(legs)
    label = ledger.label(args.purpose)
    paths = {job["chain"]: (out / f"{job['chain']}.job.json", out / f"{job['chain']}.child.log") for job in jobs}
    try:
        made = prepare_out(out, {f"{job['chain']}.job.json": {**job, "legs": legs, "out": str(out),
                                                              "build_root": str(build_root), "watchdog_seconds": watchdog}
                                 for job in jobs})
    except Refusal as error:
        print(f"REFUSED: {error}", flush=True)
        return 2
    # (the checkers' C2-07, C3-E03..E07) what the ERROR record needs, and what the guarded part has built so far
    ctx: dict = {"graded": graded, "purpose": args.purpose, "label": label, "to": to, "seeds": seeds, "sha": sha,
                 "code": code, "began": began, "out": out, "evidence_dir": deps.evidence_dir or EVIDENCE_DIR,
                 "ledger_path": deps.ledger_path or ledger.LEDGER, "bounds_text": numbers["bounds_text"],
                 "keep_earlier": keep_earlier, "chains_n": chains_n, "run": args.run if graded else None,
                 "numbers": numbers, "legs": legs, "jobs": jobs, "reach_min": reach_min, "sleep": deps.sleep,
                 "stage": "chains", "events": deps.events}
    try:
        entry, ledger_lines = begin(args.purpose, seeds, numbers, line_digest(code),
                                    note=f"LIVE CHAIN held-out (USER RULING 55), {args.purpose}, to {to}, {chains_n} chains, "
                                         f"driver ai_player/gates/live_chain.py, numbers sha256 {sha[:16]}, free "
                                         f"{facts['free']:.1f} GB"
                                         + (f", prediction file sha256 {development['prediction_sha256'][:16]}" if development
                                            else ""), path=deps.ledger_path)
    except ledger.Refused as error:
        undo_out(made)
        print(f"REFUSED by the ledger (R10): {error}", flush=True)
        return 2
    except BaseException:
        undo_out(made)  # (ledger.begin writes the ledger last and atomically: on a raise the entry was not begun)
        raise
    ctx.update({"entry_id": entry["id"], "ledger_lines": ledger_lines})
    handles: list[tuple[str, object]] = []
    started: dict[str, float] = {}
    state = {"last_tree": deps.clock(), "aborted": False}

    def may_start(job: dict) -> tuple[bool, str]:
        if state["aborted"] or (out / ABORT_FILE).is_file():
            return False, "the batch was ABORTED by the harness (disk: free space)"
        if tree.moved or not tree.check(f"before {job['chain']}"):
            if not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the tree moved: {tree.moves[-1]}\n", encoding="utf-8")
            return False, "the code under test changed mid-batch"
        return True, ""

    def spawn(job: dict):
        job_path, log_path = paths[job["chain"]]
        started[job["chain"]] = deps.clock()
        print(f"[LC] {job['chain']} started ({time.strftime('%H:%M:%S')})", flush=True)
        handle = deps.spawn({**job, "legs": legs, "out": str(out), "build_root": str(build_root)}, job_path, log_path)
        handles.append((job["chain"], handle))  # (the chains-run guard kills each one still running)
        return handle

    def tick(running: list) -> None:
        now = deps.clock()
        if now - state["last_tree"] >= deps.tree_every:
            state["last_tree"] = now
            if not tree.check("during the batch") and not (out / STOP_FILE).is_file():
                (out / STOP_FILE).write_text(f"the tree moved: {tree.moves[-1]}\n", encoding="utf-8")
                events.append(f"the frozen tree moved: {tree.moves[-1]}")
        free = deps.free(build_root)
        for job, handle in running:
            if handle.poll() is not None:
                continue
            name, size = newest_world(build_root / "profiles" / job["profile"] / "ai_player_runs")
            leg = leg_of_folder(name, job["chain"])
            cause = guard_decision(size, free)
            if cause == "free" and not state["aborted"]:
                state["aborted"] = True
                (out / ABORT_FILE).write_text(f"under {GUARD_FREE_GB:g} GB free: {free}\n", encoding="utf-8")
                events.append(f"ABORT: {free} GB free, under {GUARD_FREE_GB:g}: every running launcher is killed")
            if cause is not None and leg is not None:
                marker = out / job["chain"] / f"{leg}.KILLED.json"
                if not marker.exists():
                    killed = deps.kill(handle.pid)
                    text = (f"{job['chain']} {leg}: the disk guard ({cause}) killed the launcher at "
                            f"{time.strftime('%H:%M:%S')}: world.jsonl {size} bytes, {free} GB free; pids {killed}")
                    _write_json(marker, {"cause": cause, "text": text})
                    events.append(text)
            if now - started.get(job["chain"], now) > watchdog and not (out / job["chain"] / "WATCHDOG.txt").exists():
                handle.kill_tree()
                (out / job["chain"]).mkdir(parents=True, exist_ok=True)
                (out / job["chain"] / "WATCHDOG.txt").write_text(f"past {watchdog} s\n", encoding="utf-8")
                events.append(f"{job['chain']}: the chain watchdog ({watchdog} s) killed its process tree")

    try:
        for line in ledger_lines:
            print(f"[LC] {line}", flush=True)
        plan = schedule(jobs, spawn, tick, PARALLEL, stagger, deps.sleep, may_start, deps.poll_seconds)
        ctx["stage"] = "grading"
        left_procs = deps.leftover()
        chains: list[dict] = []
        not_started = {job["chain"]: why for job, why in plan["not_started"]}
        for job in jobs:
            full = {**job, "legs": legs}
            if job["chain"] in not_started:
                chain = new_chain_row(full)
                stop_rest(full, chain, 0, not_started[job["chain"]])
                chain.update({"stopped_at": "L1", "stop_reason": not_started[job["chain"]]})
                write_chain(out, chain, len(legs))
                chains.append(chain)
                continue
            path = out / "rows" / f"{job['chain']}.json"
            chain = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
            if chain is None or len(chain.get("legs") or []) != len(legs):
                why = ("killed by the chain watchdog" if (out / job["chain"] / "WATCHDOG.txt").is_file()
                       else "it ended without its chain row")
                chain = salvage_chain({**full, "out": str(out)}, build_root, out, why)
                events.append(f"{job['chain']}{SALVAGE_EVENT}{why})")
            chains.append(chain)
        world_left = end_sweep(jobs, build_root)
        profiles = profiles_report(folders_before, run_folders(build_root), chains, jobs)
        main_after = main_profile_state(build_root)
        main = {"unchanged": main_before == main_after,
                "text": f"before {main_before}, after {main_after}: {'unchanged' if main_before == main_after else 'CHANGED'}"}
        held = tree.check("after the batch")
        _, frozen_line = tree.seal("PASS" if held else "FAIL")
        optional = optional_report(chains, load_milestones(repo_root()), legs[-1]["chapter"])
        # (C3-G06) a leg that did not run after a continuing leg is explained only by these files, or (C4-G04) by the
        # orchestrator's OWN record that it salvaged that chain (its events), never by a stored reason alone
        stop_files = [name for name in (STOP_FILE, ABORT_FILE) if (out / name).is_file()]
        salvaged = salvaged_chains(events)
        checks = grade_batch(chains, jobs, len(legs), reach_min, (held and not tree.moves, frozen_line), left_procs,
                             {"world_left": [w for w in world_left if "could not" in w], "profiles": profiles,
                              "main_profile": main, "optional": optional, "most_running": plan["most_running"]}, legs=legs,
                             stop_files=stop_files, salvaged=salvaged)
        result = batch_verdict(checks)
        aborted = state["aborted"] or (out / ABORT_FILE).is_file()
        failing = [c.id for c in checks if c.kind == GRADED and c.status != PASS]
        shown = "ABORTED (harness: disk)" if aborted else result
        reach = next(c for c in checks if c.id == "LC.REACH")
        # (V-08) a launch that died before playing a frame fails the batch by the registered rule: NAMED, never hidden
        died_rows = [(c["chain"], leg["leg"], launch_died(leg)) for c in chains for leg in c["legs"] if launch_died(leg)]
        died_text = f"; {DEAD_LAUNCH}: {[f'{c} {leg}' for c, leg, _ in died_rows]}" if died_rows else ""
        verdict_line = (f"{label}, {shown if graded else 'NO PASS (development: ' + shown + ' by the registered rules)'}"
                        f"{' (failing: ' + ', '.join(failing) + ')' if failing and not aborted else ''}{died_text}: live chain "
                        f"held-out, to {to}, seeds {seeds[0]}-{seeds[1]}, numbers sha256 {sha[:16]}; "
                        f"{reach.text.split(': ', 1)[1][:400]}")
        ctx["stage"] = "evidence"
        evidence = evidence_path(ctx["evidence_dir"], graded, to, seeds[0])
        evidence.parent.mkdir(parents=True, exist_ok=True)
        keep_earlier(evidence)
        ctx.update({"evidence": evidence, "kept_earlier": True})
        head = (f"LIVE CHAIN HELD-OUT - {'GRADED' if graded else 'DEVELOPMENT, NOT GRADED, NO PASS'} - VERDICT {shown}"
                f"{' (failing: ' + ', '.join(failing) + ')' if failing and not aborted else ''}{died_text} (to {to}; driver "
                f"ai_player/gates/live_chain.py; build spec {SPEC})")
        not_run = [f"{c['chain']} {leg['leg']}: {leg.get('reason')}" for c in chains for leg in c["legs"]
                   if leg.get("status") in ("NOT RUN", "REFUSED")]
        flagged = [f"{c['chain']} {leg['leg']} {((leg.get('measures') or {}).get('log') or {}).get('multichoice')}"
                   for c, leg in ran_legs(chains) if ((leg.get("measures") or {}).get("log") or {}).get("multichoice")]
        text = [head, f"date: {began} -> {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {code}", *ledger_lines,
                f"numbers sha256: {sha} (seeds {seeds[0]}-{seeds[1]}; {args.purpose}; {chains_n} chains; at least "
                f"{reach_min} to reach)"]
        ctx["text"] = text
        if development:
            text += [f"PREDICTION (sha256 of the file's bytes {development['prediction_sha256']}, in the numbers, registered "
                     f"before the runs): {prediction}",
                     f"leg budgets overridden: {development['leg_frames_override'] or 'none'}"]
        text += [f"build root: {build_root}   out: {out}   free at start: {facts['free']:.1f} GB",
                 f"frozen tree: {frozen_line}", f"leftover processes: {left_procs or 'none'}",
                 f"the most chains running at once: {plan['most_running']} (launch order {plan['order']})",
                 f"NOT RUN: {not_run or 'none'}", f"guard and watchdog events: {events or 'none'}",
                 f"{DEAD_LAUNCH} (each RAN, so each fails LC.PURITY and LC.THIS_RUN by the registered rule): "
                 f"{[f'{c} {leg}: {why}' for c, leg, why in died_rows] or 'none'}",
                 f"legs with an unexpected-multichoice line: {flagged or 'none'}",
                 f"VERDICT: {shown}" + (" (the checks below are information: a harness abort is no PASS and no FAIL)"
                                         if aborted else ""),
                 "checks (registered in the bounds text below; each quotes both values):", *check_lines(checks), "",
                 "per chain and leg (each counted chain as it was RE-DERIVED and graded):"]
        # (the checker's C2-03) the reach printed is the RE-DERIVED one that LC.REACH counted, never the stored flag alone
        counted = {c.get("chain"): c for c in registered_chains(chains, jobs, legs, stop_files, salvaged=salvaged)[0]}
        for chain in chains:
            row = counted.get(chain["chain"])
            stored = chain_reaches(chain, len(legs))
            if row is None:
                reached_text = "NOT COUNTED (its row is IGNORED: see LC.REACH)"
            else:
                rederived = chain_reaches(row, len(legs))
                reached_text = f"{rederived} (re-derived{'' if rederived == stored else f'; the row stored {stored}'})"
            shown_row = row or chain
            text.append(f"  {chain['chain']} ({chain.get('personality')}, {chain.get('starter')}, seed {chain.get('seed')}, "
                        f"profile {chain.get('profile')}): reached {to} {reached_text}; stopped at "
                        f"{shown_row.get('stopped_at')}: {shown_row.get('stop_reason')}")
            for leg in shown_row["legs"]:
                text += leg_lines(leg)
        text += ["", BOUNDS_HEADING, numbers["bounds_text"]]
        evidence.write_text("\n".join(text) + "\n", encoding="utf-8", errors="backslashreplace")  # (C4-E04)
        ctx["stage"] = "results.json"
        _write_json(out / "results.json", {"began": began, "ended": time.strftime("%Y-%m-%d %H:%M:%S"),
                                           "purpose": args.purpose, "run": args.run if graded else None, "to": to,
                                           "chains": chains_n, "seeds": list(seeds), "numbers_sha256": sha,
                                           "ledger": entry["id"], "frozen": [held and not tree.moves, frozen_line],
                                           "leftover": left_procs, "not_run": not_run, "events": events,
                                           "most_running": plan["most_running"], "verdict": shown, "reach_min": reach_min,
                                           "legs": legs, "jobs": jobs, "world_left": world_left,
                                           "reported": {"profiles": profiles, "main_profile": main, "optional": optional},
                                           "checks": check_rows(checks), "evidence": str(evidence),
                                           # (C3-G02) grade DIR takes its legs, jobs and reach floor from these, verified
                                           "numbers": numbers})
        ctx["stage"] = "ledger"
        reference = (str(evidence.resolve().relative_to(REPO)).replace("\\", "/") if evidence.resolve().is_relative_to(REPO)
                     else str(evidence))
        # (C3-E03) a failed write is retried with the COMPUTED verdict first; only then does the guard write ERROR
        why = finish_entry(entry["id"], verdict_line, reference, ctx["ledger_path"], deps.sleep)
        ctx["finished"] = why is None  # (C4-E03) a Ctrl+C after this point never overwrites the computed verdict
        if why is not None:
            raise LedgerUnwritten(f"the computed verdict could not be written to ledger entry #{entry['id']} in "
                                  f"{FINISH_TRIES} tries: {why}")
    except BaseException as error:  # noqa: BLE001 - (C2-07, the chains-run guard) the seeds are spent: FINISH the entry
        # (the fourth check's C4-E03) one line at once, then a second Ctrl+C is IGNORED until the entry is written; one
        # that slips in anyway is noted by each step below and the finish goes on, then the interrupt is raised again
        restore = hold_interrupts(error, ctx)
        try:
            ctx["guard_notes"] = stop_children(handles, ctx.setdefault("interrupts", []))
            if ctx["stage"] == "chains":
                try:  # the killed legs' world files: deleted as the end sweep deletes them
                    ctx["guard_notes"] += end_sweep(jobs, build_root)
                except BaseException as sweep:  # noqa: BLE001 - (C4-E03) a sweep that raises never leaves 'started'
                    note_interrupt(ctx, sweep)
                    ctx["guard_notes"].append(f"the end sweep could not run: {type(sweep).__name__}: "
                                              f"{safe_text(sweep, 200)}")
            exit_code = finish_on_error(error, traceback.format_exc(), ctx)
        finally:
            restore()
        if not isinstance(error, Exception):
            raise  # (C3-E06) a Ctrl+C still stops the process, AFTER the entry is finished
        if ctx.get("interrupts"):
            raise KeyboardInterrupt(f"a Ctrl+C while the guard finished ledger entry #{ctx.get('entry_id')}")
        return exit_code
    print(f"[LC] evidence: {evidence}", flush=True)
    for line in check_lines(checks):
        print(f"[LC] {line.strip()}", flush=True)
    print(f"[LC] OVERALL {shown} ({label}); ledger #{entry['id']} finished", flush=True)
    if aborted:
        return 3
    return 0 if (result == "PASS" or not graded) else 1


def error_verdict(error: BaseException, stage: str = "grading") -> str:
    """(The checkers' C2-07, C3-E06 and C3-E07) The named verdict of a batch whose harness raised after ledger.begin:
    neither PASS nor FAIL (the seeds are spent), recorded the way the disk guard's ABORT is, naming the STAGE (`STAGES`) and
    the error (`safe_text`: an exception whose str() raises still gives a verdict)."""
    return (f"ERROR (harness: {type(error).__name__}: {safe_text(error) or 'no message'} "
            f"{STAGES.get(stage, 'while ' + stage)}; no PASS or FAIL; the seeds are spent)")


def finish_command(ctx: dict) -> str:
    """(C3-E03) The exact command that finishes an entry the ERROR path could not write (run from the repository)."""
    path = Path(ctx["ledger_path"])
    return (f'py -3.12 ai_player/gates/live_chain.py finish-entry "{ctx["out"]}"'
            + ("" if path == ledger.LEDGER else f' --ledger "{path}"'))


def error_line(label: str, graded: bool, shown: str, to: str, seeds, sha: str) -> str:
    """(C3-E04, the fourth check's C4-E05) The ledger verdict line of a batch that ended in ERROR (`shown` is
    `error_verdict`'s text): its label, "NO PASS (development: ...)" for a development batch, the target, the seeds and the
    numbers sha256. `finish-entry` REBUILDS it from results.error.json and the ledger entry, and writes nothing else."""
    return (f"{label}, {shown if graded else 'NO PASS (development: ' + shown + ')'}: live chain "
            f"held-out, to {to}, seeds {seeds[0]}-{seeds[1]}, numbers sha256 {sha[:16]}")


#: (C4-E05) the form of `error_verdict`'s text: the only verdict `finish-entry` writes
ERROR_FORM = re.compile(r"ERROR \(harness: .+ while .+; no PASS or FAIL; the seeds are spent\)", re.S)


def entry_status(entry_id: int, path: Path) -> str | None:
    """A ledger entry's status read NOW ("registered", "started", "done"), or None when the ledger or the entry cannot be
    read."""
    try:
        entry = next((e for e in ledger.load(Path(path)).get("entries", []) if e.get("id") == entry_id), None)
    except Exception:  # noqa: BLE001
        return None
    return entry.get("status") if isinstance(entry, dict) else None


def finish_on_error(error: BaseException, trace: str, ctx: dict) -> int:
    """(The checkers' C2-07 and C3-E03..E07) The harness raised after ledger.begin, at `ctx["stage"]`. In this order,
    each step guarded on its own: (1) the evidence: the ERROR verdict naming the stage, the guard's own steps, the
    traceback, then what the harness had built before the error, every line marked "UNFINISHED| " and cut before its bounds
    text (the bounds text follows once); an evidence file that cannot be written does not stop the rest, and the verdict
    line says so; (2) the ledger entry FINISHED with `error_verdict` (`finish_entry`: retried); (3) results.error.json
    BESIDE any complete results.json (never over it), with the numbers, the legs, the jobs and the reach floor, for `grade
    DIR`; (4) one line appended to the evidence saying whether the entry was finished. When the ledger cannot be written
    at all, the entry is NOT finished: the evidence, results.error.json, the output and ledger.unfinished.json say so, with
    the exact command that finishes it (`finish_command`). Exit 4 in every case, never 1. (The fourth check's C4-E03)
    every step catches a second Ctrl+C too (noted: the guard raises it again after), and an entry the batch had ALREADY
    finished with its computed verdict (the interrupt came after that write) is left as it is: nothing is overwritten."""
    if ctx.get("finished") or entry_status(ctx["entry_id"], Path(ctx["ledger_path"])) == "done":
        print(f"[LC] ledger entry #{ctx['entry_id']} was already FINISHED with the batch's computed verdict before "
              f"{type(error).__name__}: nothing is overwritten", flush=True)
        return 4
    stage = ctx.get("stage") or "grading"
    shown = error_verdict(error, stage)
    graded, seeds = ctx["graded"], ctx["seeds"]
    verdict_line = error_line(ctx["label"], graded, shown, ctx["to"], seeds, ctx["sha"])
    reference, evidence = None, None
    try:
        evidence = ctx.get("evidence") or evidence_path(ctx["evidence_dir"], graded, ctx["to"], seeds[0])
        evidence.parent.mkdir(parents=True, exist_ok=True)
        if not ctx.get("kept_earlier"):
            ctx["keep_earlier"](evidence)
        head = (f"LIVE CHAIN HELD-OUT - {'GRADED' if graded else 'DEVELOPMENT, NOT GRADED, NO PASS'} - VERDICT {shown} "
                f"(to {ctx['to']}; driver ai_player/gates/live_chain.py; build spec {SPEC})")
        built: list[str] = []
        for line in ctx.get("text") or []:
            if line == BOUNDS_HEADING:  # (C3-E07) the bounds text is printed ONCE, below
                break
            built.append(line)
        lines = [head, f"date: {ctx['began']} -> {time.strftime('%Y-%m-%d %H:%M:%S')}", f"code: {ctx['code']}",
                 *ctx["ledger_lines"], f"numbers sha256: {ctx['sha']} (seeds {seeds[0]}-{seeds[1]}; {ctx['purpose']}; "
                                       f"{ctx['chains_n']} chains)",
                 f"VERDICT: {shown}: the harness raised {STAGES.get(stage, 'while ' + stage)}, so this batch has no PASS and "
                 f"no FAIL, and its seeds are spent",
                 f"LEDGER: entry #{ctx['entry_id']} is being finished with this verdict; the LAST line of this file says "
                 f"whether that was written",
                 *(f"the guard: {note}" for note in ctx.get("guard_notes") or []),
                 "the traceback:", *trace.rstrip().splitlines(), "",
                 "what the harness had built before the error (UNFINISHED, so never a verdict; every line marked):",
                 *([f"UNFINISHED| {line}" for line in built] or ["UNFINISHED| (nothing yet)"]), "",
                 BOUNDS_HEADING, ctx["bounds_text"]]
        evidence.write_text("\n".join(lines) + "\n", encoding="utf-8", errors="backslashreplace")
        reference = (str(evidence.resolve().relative_to(REPO)).replace("\\", "/") if evidence.resolve().is_relative_to(REPO)
                     else str(evidence))
    except BaseException as second:  # noqa: BLE001 - the entry is still finished; the verdict line says the evidence is missing
        note_interrupt(ctx, second)
        verdict_line += f"; no evidence file ({type(second).__name__}: {safe_text(second, 200)})"
        evidence = None
    why = "the ledger write was never tried"
    for _ in range(2):  # (C4-E03) a Ctrl+C that slips into the write is noted, and the write is tried once more
        try:
            why = finish_entry(ctx["entry_id"], verdict_line, reference, Path(ctx["ledger_path"]), ctx.get("sleep") or time.sleep)
            break
        except BaseException as late:  # noqa: BLE001
            note_interrupt(ctx, late)
            why = f"{type(late).__name__}: {safe_text(late, 200)}"
    finished = why is None
    command = finish_command(ctx)
    status = (f"LEDGER: entry #{ctx['entry_id']} FINISHED with this verdict" if finished else
              f"LEDGER: entry #{ctx['entry_id']} is NOT FINISHED (it is still 'started'): the ledger could not be written "
              f"({why}). Finish it by hand, from the repository: {command}")
    record = {"verdict": shown, "stage": stage, "purpose": ctx["purpose"], "run": ctx["run"], "to": ctx["to"],
              "seeds": list(seeds), "numbers_sha256": ctx["sha"], "ledger": ctx["entry_id"],
              "error": f"{type(error).__name__}: {safe_text(error, 2000)}", "traceback": trace, "evidence": reference,
              "ledger_finished": finished, "finish_command": None if finished else command,
              "guard_notes": ctx.get("guard_notes") or [], "numbers": ctx.get("numbers"), "legs": ctx.get("legs"),
              "jobs": ctx.get("jobs"), "reach_min": ctx.get("reach_min"),
              # (C4-E05) the line finish-entry may write; (C4-G04) the orchestrator's own salvage record
              "ledger_verdict": verdict_line, "events": list(ctx.get("events") or [])}
    try:
        _write_json(ctx["out"] / RESULTS_ERROR, record)
    except BaseException as third:  # noqa: BLE001 - the ledger and the evidence are the record
        note_interrupt(ctx, third)
        print(f"[LC] {RESULTS_ERROR} could not be written: {type(third).__name__}: {safe_text(third, 200)}", flush=True)
    if not finished:
        try:
            _write_json(ctx["out"] / UNFINISHED, {"entry_id": ctx["entry_id"], "verdict": verdict_line,
                                                  "evidence": reference, "seeds": list(seeds),
                                                  "ledger": str(ctx["ledger_path"])})
        except BaseException as fourth:  # noqa: BLE001
            note_interrupt(ctx, fourth)
            print(f"[LC] {UNFINISHED} could not be written either ({type(fourth).__name__}): finish the entry with "
                  f"ledger.finish({ctx['entry_id']}, {verdict_line!r}, {reference!r}, path=Path({str(ctx['ledger_path'])!r}))",
                  flush=True)
    if evidence is not None:
        try:
            with open(evidence, "a", encoding="utf-8", errors="backslashreplace") as handle:
                handle.write(status + "\n")
        except BaseException as fifth:  # noqa: BLE001
            note_interrupt(ctx, fifth)
            print(f"[LC] the evidence's last line could not be written: {type(fifth).__name__}", flush=True)
    try:
        print(trace, flush=True)
        print(f"[LC] {status}", flush=True)
        print(f"[LC] OVERALL {shown} ({ctx['label']}); evidence {reference}", flush=True)
    except BaseException as sixth:  # noqa: BLE001 - the entry is written; a line that cannot be printed changes nothing
        note_interrupt(ctx, sixth)
    return 4


def leg_lines(leg: dict) -> list[str]:
    """One leg's evidence block."""
    if leg.get("status") in ("NOT RUN", "REFUSED"):
        return [f"    {leg['leg']} {leg['target']}: {leg['status']} - {leg.get('reason')}"]
    stop = leg.get("harness_stop") or {}
    m = leg.get("measures") or {}
    log, world = m.get("log") or {}, m.get("world") or {}
    statuses = {c["id"]: c["status"] for c in leg.get("checks") or []}
    purity = "CLEAN" if all(statuses.get(i) == PASS for i in PURITY_IDS) else \
        {i: statuses.get(i) for i in PURITY_IDS if statuses.get(i) != PASS}
    died = launch_died(leg)
    return [f"    {leg['leg']} {leg['target']} ({leg['status']}): proof before {proof_text(leg.get('proof_before'))} -> "
            f"after {proof_text(leg.get('proof_after'))}; reached {leg.get('reached')}"
            f"{' (ALREADY HELD at its start)' if leg.get('already_held') is True else ''}; real frames "
            f"{stop.get('real_frames')} of {leg.get('frames')}; {leg.get('elapsed')} s of {leg.get('wall')}; stop by "
            f"{stop.get('by')} ({stop.get('cause')})",
            *([f"      {died}: it RAN, so it fails LC.PURITY and LC.THIS_RUN (the registered rule)"] if died else []),
            f"      purity {purity}; THIS_RUN {statuses.get('L5.THIS_RUN')}; custody {leg.get('custody') or 'held'}; "
            f"continue {leg.get('continue')}: {leg.get('why')}",
            ("      world.jsonl: no world file (the leg wrote none)" if no_world_file(leg) else
             f"      world.jsonl {(leg.get('world_file') or {}).get('bytes')} B, {world.get('lines')} lines "
             f"({world.get('bad_lines')} bad), last line {world.get('last_bytes')} B ok {world.get('last_ok')}, deleted "
             f"{(leg.get('world_file') or {}).get('deleted')}") + f"; kept {leg.get('kept_world')}",
            f"      unexpected lines {log.get('unexpected')} (multichoice {log.get('multichoice')}, forms "
            f"{log.get('forms')}); first {log.get('first_unexpected')!r}",
            f"      the AI's outcome {leg.get('outcome')!r}; memory line {((log.get('memory') or {}).get('line') or '')[:300]!r}",
            f"      run dir {leg.get('run_dir')}; notes {leg.get('notes') or 'none'}"]


def registered_rows(out: Path, jobs: list[dict]) -> tuple[list[dict], list[str]]:
    """(The verifier's V-02) `grade DIR`'s rows: each REGISTERED chain's row read from rows/<chain>.json, kept only when its
    own chain field names that chain; every other file of rows/ is IGNORED, with why (a reused --out, a copied row, a file
    that does not parse, whatever the parse raises)."""
    names = {job["chain"] for job in jobs}
    chains: list[dict] = []
    ignored: list[str] = []
    for path in sorted((out / "rows").glob("*.json")):
        if path.stem not in names:
            ignored.append(f"rows/{path.name}: not a registered chain of this batch {sorted(names)}: never counted")
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001 - a row file that cannot be read never counts
            ignored.append(f"rows/{path.name}: unreadable ({type(error).__name__}): not counted")
            continue
        if not isinstance(row, dict) or row.get("chain") != path.stem:
            ignored.append(f"rows/{path.name}: its chain field "
                           f"{row.get('chain') if isinstance(row, dict) else None!r} is not {path.stem!r}: not counted")
            continue
        chains.append(row)
    return chains, ignored


def _read_record(path: Path) -> dict | None:
    """A results file of --out: its JSON object, None when it is not there; RAISES `Refusal` when it cannot be read."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:  # noqa: BLE001
        raise Refusal(f"{path.name} cannot be read ({type(error).__name__}: {safe_text(error, 200)})") from None
    if not isinstance(data, dict):
        raise Refusal(f"{path.name} holds a JSON {type(data).__name__}, not an object")
    return data


def find_entry(ledger_path: Path, seeds: list, entry_id, sha) -> tuple[dict | None, str]:
    """(The fourth check's C4-G01, C4-E06) A --out folder's live_chain ledger entry, READ NOW: among the entries for exactly
    its seeds, the one with its recorded id AND bounds sha256, else its bounds sha256 (a merged ledger renumbers entries:
    R0's results.json names #86, the worktree's ledger holds it as #96), else its id, else the latest one that was begun
    (so a folder whose id and sha256 were both edited still meets its seeds' entry, whose verdict then bounds the
    re-grade). (None, why) when no entry names those seeds or the ledger cannot be read."""
    try:
        entries = [e for e in ledger.load(Path(ledger_path)).get("entries", []) if isinstance(e, dict)
                   and e.get("driver") == DRIVER and [e.get("first"), e.get("last")] == list(seeds)]
    except Exception as error:  # noqa: BLE001 - an unreadable ledger is said, never a crash
        return None, f"the ledger {ledger_path} could not be read ({type(error).__name__})"
    if not entries:
        return None, f"no {DRIVER} entry for seeds {seeds} in {ledger_path}"
    for match in (lambda e: e.get("id") == entry_id and e.get("bounds_sha256") == sha,
                  lambda e: e.get("bounds_sha256") == sha and e.get("status") != "registered",
                  lambda e: e.get("bounds_sha256") == sha, lambda e: e.get("id") == entry_id,
                  lambda e: e.get("status") != "registered", lambda e: True):
        found = [e for e in entries if match(e)]
        if found:
            return found[-1], ""
    return None, f"no {DRIVER} entry for seeds {seeds} in {ledger_path}"


def numbers_jobs_problems(numbers: dict) -> list[str]:
    """(C4-G01) The numbers' jobs belong to the numbers' seeds: one job per seed of the range, each named LC-<pair>-<seed>
    (so seeds moved to another range with the jobs left as they were never verify)."""
    try:
        first, last = int(numbers["seeds"][0]), int(numbers["seeds"][1])
        named = [(str(job["chain"]), int(job["seed"]), str(job["pair"])) for job in numbers["jobs"]]
    except Exception as error:  # noqa: BLE001 - numbers from a folder are untrusted
        return [f"the numbers' seeds or jobs cannot be read ({type(error).__name__})"]
    problems: list[str] = []
    if sorted(seed for _, seed, _ in named) != list(range(first, last + 1)) or numbers.get("chains") != len(named):
        problems.append(f"the numbers' jobs {[c for c, _, _ in named]} are not one per seed of {first}-{last} "
                        f"({numbers.get('chains')} chains)")
    wrong = [chain for chain, seed, pair in named if chain != f"LC-{pair}-{seed}"]
    if wrong:
        problems.append(f"the numbers' jobs {wrong} are not named LC-<pair>-<seed>")
    return problems


def verify_numbers(source: dict, entry: dict | None, entry_why: str = "") -> tuple[dict | None, list[str], str, bool]:
    """(The third check's C3-G02, the fourth check's C4-G01) The numbers a --out records, VERIFIED: (the numbers, the
    problems, what was checked, VERIFIED or not). Their sha256 must be the numbers_sha256 recorded beside them, their seeds
    the batch's, their jobs one per seed (`numbers_jobs_problems`), and their sha256 the bounds sha256 that the batch's
    ledger ENTRY registered (`find_entry`). With no entry they are UNVERIFIED (never 'VERIFIED'); a graded folder then
    never re-grades PASS. An older folder with no numbers: (None, [], UNVERIFIED (no numbers), False)."""
    numbers = source.get("numbers")
    if not isinstance(numbers, dict):
        note = ("" if entry is None or entry.get("bounds_sha256") != source.get("numbers_sha256") else
                f"; ledger entry #{entry.get('id')} registered the numbers_sha256 recorded beside them")
        return None, [], f"UNVERIFIED (no numbers): the legs, jobs and reach floor are results.json's own{note}", False
    problems: list[str] = []
    sha = ledger.numbers_sha256(numbers)
    if sha != source.get("numbers_sha256"):
        problems.append(f"the numbers' sha256 {sha[:16]} is not the numbers_sha256 recorded beside them "
                        f"{str(source.get('numbers_sha256'))[:16]}")
    seeds = list(numbers.get("seeds") or [])
    if list(source.get("seeds") or []) != seeds:
        problems.append(f"the numbers' seeds {seeds} are not the batch's {source.get('seeds')}")
    problems += numbers_jobs_problems(numbers)
    checked = f"numbers sha256 {sha[:16]} == the one recorded beside them"
    verified = False
    if entry is None:
        checked = f"{checked}; NOT verified against the ledger ({entry_why or 'no ledger entry'})"
    elif entry.get("bounds_sha256") == sha:
        checked = f"{checked} == the bounds sha256 ledger entry #{entry.get('id')} registered"
        verified = True
    else:
        problems.append(f"the numbers' sha256 {sha[:16]} is not the bounds sha256 the ledger registered for seeds "
                        f"{seeds} (entry #{entry.get('id')}: {str(entry.get('bounds_sha256'))[:16]})")
    if problems:
        return numbers, problems, f"MISMATCH: {'; '.join(problems)}", False
    return numbers, problems, f"{'VERIFIED' if verified else 'UNVERIFIED'}: {checked}", verified


def ledger_result(entry: dict) -> str:
    """(The fourth check's C4-E06, C4-G03) What a live_chain ledger entry says NOW: STARTED (begun, never finished: no
    verdict was written), REGISTERED (never begun), or its verdict's own word after its label (PASS, FAIL, ABORTED,
    ERROR); UNREADABLE otherwise."""
    if entry.get("status") == "started":
        return "STARTED"
    if entry.get("status") == "registered":
        return "REGISTERED"
    verdict = str(entry.get("verdict") or "")
    for prefix in (f"{ledger.label('graded')}, ", f"{ledger.label('development')}, NO PASS (development: "):
        if verdict.startswith(prefix):
            word = re.match(r"[A-Z]+", verdict[len(prefix):])
            if word and word.group(0) in ("PASS", "FAIL", "ABORTED", "ERROR"):
                return word.group(0)
    return "UNREADABLE"


#: (C4-G01..G03, C4-E06) grade DIR's exit per verdict; the WORST of the batch's files, its ledger entry and the re-grade
GRADE_EXIT = {"PASS": 0, "FAIL": 1, "UNVERIFIED": 1, "ABORTED": 3, "ERROR": 4}
_WORST = ("PASS", "UNVERIFIED", "FAIL", "ABORTED", "ERROR")


def regrade_dir(out: Path, ledger_path: Path | None = None) -> dict:
    """THE OFFLINE RE-GRADE of a batch's --out (no ledger write). (The third check's C3-G02) the registered numbers come from
    results.json's "numbers" (for a batch that ended in ERROR before results.json was written, from results.error.json's),
    VERIFIED by `verify_numbers` against `ledger_path` when given; the legs, jobs and reach floor are taken from them (an
    older folder with no numbers: results.json's own, UNVERIFIED). The registered chains only, each from its own row file
    (`registered_rows`), a disk guard's marker file on disk joined to its leg (it can only stop a leg), then `grade_batch`
    against the registered legs, which re-derives every leg from the row's facts (C3-G04: `kept_root` reads a kept line
    from out/<chain>/<leg>/ when a moved --out lost its stored path; C3-G06: STOP.txt and ABORT.txt read on disk). A
    frozen-tree or leftover record that is missing grades FAIL, never drops its check. Numbers that do not verify make the
    verdict FAIL. (C3-E05) a batch that ended in ERROR says so ("ended_in_error"); its rows are re-graded as information.
    (The fourth check's C4-G01..G03, C4-E06) the batch's ledger entry is read NOW (`find_entry`) and bounds the result:
    "verdict" is the rows' re-grade, "final" the worst of it, the entry's verdict (STARTED reads as ERROR), the folder's
    own ERROR (results.error.json) and ABORTED (ABORT.txt, results.json's verdict) marks, and UNVERIFIED for a graded
    folder whose numbers no entry verifies; "purpose" is the entry's (else results.json's, said unconfirmed); (C4-G04) the
    salvage exemption reads the orchestrator's own events."""
    error_record = _read_record(out / RESULTS_ERROR)
    results = _read_record(out / "results.json")
    source = results if results is not None else error_record
    if source is None:
        raise Refusal(f"{out} holds no results.json and no {RESULTS_ERROR}: nothing to grade from")
    raw = source.get("numbers")
    seeds = list((raw.get("seeds") if isinstance(raw, dict) else None) or source.get("seeds") or [])
    sha = ledger.numbers_sha256(raw) if isinstance(raw, dict) else source.get("numbers_sha256")
    if ledger_path is None:
        entry, entry_why = None, "no ledger was given"
    elif len(seeds) != 2:
        entry, entry_why = None, f"the folder records no seed range ({seeds})"
    else:
        entry, entry_why = find_entry(Path(ledger_path), seeds, source.get("ledger"), sha)
    numbers, problems, verified, is_verified = verify_numbers(source, entry, entry_why)
    if numbers is not None:
        prefix = numbers.get("profile_prefix") or PROFILE_PREFIX
        legs = numbers["legs"]
        jobs = [{**job, "profile": f"{prefix}{job['seed']}"} for job in numbers["jobs"]]
        reach_min = numbers["reach_min"]
    else:
        legs, jobs, reach_min = source["legs"], source["jobs"], source["reach_min"]
    chains, ignored = registered_rows(out, jobs)
    markers = []
    for chain in chains:
        for leg in chain.get("legs") or []:
            mark = guard_mark(out, chain["chain"], str(leg.get("leg"))) if leg.get("status") in RAN else None
            if mark is not None and not leg.get("guard_killed"):
                leg["guard_killed"] = mark
                markers.append(f"{chain['chain']} {leg.get('leg')}: the disk guard's marker is on disk; the row had none")
    frozen = source.get("frozen")
    frozen = (tuple(frozen) if isinstance(frozen, list) and len(frozen) == 2 else
              (False, f"the frozen-tree record is missing from {'results.json' if results else RESULTS_ERROR}: graded FAIL"))
    leftover = source.get("leftover")
    if not isinstance(leftover, list):
        leftover = [f"the leftover-process record is missing from {'results.json' if results else RESULTS_ERROR}: graded "
                    f"FAIL"]
    rep = source.get("reported") or {}
    salvaged = salvaged_chains(source.get("events"))  # (C4-G04) the orchestrator's own record, never a stored reason
    checks = grade_batch(chains, jobs, len(legs), reach_min, frozen, leftover,
                         {"world_left": [w for w in source.get("world_left") or [] if "could not" in w],
                          "profiles": rep.get("profiles"), "main_profile": rep.get("main_profile"),
                          "optional": rep.get("optional"), "most_running": source.get("most_running")}, legs=legs,
                         stop_files=[name for name in (STOP_FILE, ABORT_FILE) if (out / name).is_file()], kept_root=out,
                         salvaged=salvaged)
    regrade = "FAIL" if problems else batch_verdict(checks)
    # (C4-G01..G03, C4-E06) what the batch's own files and its ledger entry (read NOW) say; the worst of them wins
    purpose = (entry or {}).get("purpose") or source.get("purpose") or "graded"
    word = ledger_result(entry) if entry is not None else None
    states: dict[str, str] = {}
    if error_record is not None:
        states["ERROR"] = f"{RESULTS_ERROR} says {error_record.get('verdict')} (stage {error_record.get('stage')})"
    if word == "STARTED":
        states["ERROR"] = (f"ledger entry #{entry.get('id')} is still 'started': no verdict was ever written for it (see "
                           f"{UNFINISHED} and finish-entry)")
    elif word in ("ERROR", "ABORTED"):
        states.setdefault(word, f"ledger entry #{entry.get('id')}'s verdict: {str(entry.get('verdict'))[:300]}")
    if (out / ABORT_FILE).is_file() or str(source.get("verdict") or "").startswith("ABORTED"):
        states.setdefault("ABORTED", f"{ABORT_FILE if (out / ABORT_FILE).is_file() else 'results.json'} says the harness "
                                     f"ABORTED the batch (disk)")
    candidates = [regrade, *states]
    if word in ("PASS", "FAIL"):
        candidates.append(word)
    final = max(candidates, key=_WORST.index)
    why_not = ""
    if final == "PASS" and (word in ("REGISTERED", "UNREADABLE") or (purpose == "graded" and not is_verified)):
        final = "UNVERIFIED"
        why_not = ("its ledger entry " + ("was never begun" if word == "REGISTERED" else "has a verdict this driver "
                                                                                       "never writes")
                   if word in ("REGISTERED", "UNREADABLE") else "a GRADED folder whose numbers no ledger entry verifies")
    return {"checks": checks, "verdict": regrade, "ignored": ignored, "markers": markers, "rows": len(chains),
            "jobs": len(jobs), "numbers": verified, "verified": is_verified,
            "ended_in_error": states.get("ERROR"), "error_stage": (error_record or {}).get("stage"),
            "aborted": states.get("ABORTED"), "entry": entry, "entry_why": entry_why, "entry_word": word,
            "recorded_id": source.get("ledger"), "purpose": purpose, "purpose_confirmed": entry is not None,
            "final": final, "why_not": why_not, "exit": GRADE_EXIT[final]}


def grade_dir(out: Path, ledger_path: Path | None = None) -> int:
    """`grade DIR`: the offline re-grade, printed. (C3-G02, C3-G04, C3-E05; the fourth check's C4-G01..G03, C4-E06) It
    reads the batch's ledger entry NOW and NEVER reports a verdict better than that entry's (`regrade_dir`'s "final", the
    worst of the re-grade, the entry and the folder's own ERROR or ABORTED marks): EXIT 0 = PASS (a GRADED folder only when
    its numbers are VERIFIED against its ledger entry; a development folder is labelled DEVELOPMENT, not graded); 1 = FAIL
    or UNVERIFIED (VACUOUS checks, numbers that do not verify, a graded folder no ledger entry verifies); 2 = it could not
    be graded (no results file, an unreadable one); 3 = ABORTED by the harness (ABORT.txt, results.json or the entry);
    4 = ERROR (results.error.json, the entry's ERROR verdict, or an entry still 'started'). In 3 and 4 the rows are
    re-graded as information only."""
    try:
        found = regrade_dir(out, ledger_path)
    except Exception as error:  # noqa: BLE001 - grade DIR reads files it did not write: it says why, never crashes
        print(f"CANNOT GRADE {out}: {type(error).__name__}: {safe_text(error)}")
        return 2
    entry = found["entry"]
    if entry is not None:
        renumbered = ("" if found["recorded_id"] == entry.get("id") else
                      f" (results.json names #{found['recorded_id']}: matched by its seeds and bounds sha256)")
        print(f"LEDGER (read now): entry #{entry.get('id')}{renumbered}, {entry.get('purpose')}, status "
              f"{entry.get('status')}: {str(entry.get('verdict'))[:300]}")
    else:
        print(f"LEDGER (read now): {found['entry_why']}: the purpose is results.json's own ({found['purpose']}), "
              f"unconfirmed")
    if found["ended_in_error"]:
        status = "unknown (no ledger entry)" if entry is None else (
            "finished" if entry.get("status") == "done" else f"NOT finished (it is {entry.get('status')!r})")
        print(f"this batch ended in ERROR: {found['ended_in_error']}; its ledger entry is {status} (read now): no PASS "
              f"or FAIL; the re-grade below is information only")
    if found["aborted"]:
        print(f"this batch was ABORTED by the harness: {found['aborted']}: no PASS or FAIL; the re-grade below is "
              f"information only")
    for line in found["ignored"]:
        print(f"IGNORED: {line}")
    for line in found["markers"]:
        print(f"MARKER: {line}")
    for line in check_lines(found["checks"]):
        print(line)
    print(REDERIVED_TEXT)
    print(f"NUMBERS: {found['numbers']}")
    print(f"OFFLINE RE-GRADE (no ledger write): {found['verdict']} over the {found['rows']} rows of the {found['jobs']} "
          f"registered chains ({len(found['ignored'])} row file(s) IGNORED)"
          + ("; THE BATCH ENDED IN ERROR" if found["ended_in_error"] else "")
          + ("; THE BATCH WAS ABORTED" if found["aborted"] else ""))
    label = ledger.label(found["purpose"]) if found["purpose"] in ledger.PURPOSES else str(found["purpose"])
    print(f"GRADE DIR VERDICT: {label}{'' if found['purpose_confirmed'] else ' (unconfirmed: no ledger entry)'}: "
          f"{found['final']}" + (f" ({found['why_not']})" if found["why_not"] else "")
          + (f" (the rows re-grade {found['verdict']})" if found["final"] != found["verdict"] else "")
          + f"; exit {found['exit']}")
    return found["exit"]


def unfinished_problems(data: dict, record: dict | None, entry: dict) -> list[str]:
    """(The fourth check's C4-E05) Why `finish-entry` must NOT write DIR/ledger.unfinished.json's verdict into `entry`
    (empty: it may). The verdict must be this driver's own ERROR verdict for that entry, REBUILT from DIR/results.error.json
    (`error_line`: the entry's own purpose label, results.error.json's `error_verdict` text, its target, the entry's seeds
    and bounds sha256; "; no evidence file (...)" may follow), and results.error.json must name the same entry, seeds and
    numbers sha256 and say the ledger was NOT finished. A PASS, a FAIL or any edited line is refused."""
    if record is None:
        return [f"{RESULTS_ERROR} is not there, so the ERROR verdict cannot be rebuilt"]
    seeds = [entry.get("first"), entry.get("last")]
    problems: list[str] = []
    for key, want in (("ledger", entry.get("id")), ("seeds", seeds), ("numbers_sha256", entry.get("bounds_sha256")),
                      ("ledger_finished", False)):
        if record.get(key) != want:
            problems.append(f"{RESULTS_ERROR}'s {key} is {record.get(key)!r}, not {want!r}")
    shown = str(record.get("verdict") or "")
    if not ERROR_FORM.fullmatch(shown):
        problems.append(f"{RESULTS_ERROR}'s verdict {shown[:120]!r} is not this driver's ERROR verdict")
    purpose = entry.get("purpose")
    if purpose not in ledger.PURPOSES or not isinstance(entry.get("bounds_sha256"), str):
        return [*problems, f"the entry's purpose {purpose!r} or bounds sha256 cannot be read"]
    rebuilt = error_line(ledger.label(purpose), purpose == "graded", shown, str(record.get("to")), seeds,
                         entry["bounds_sha256"])
    verdict = str(data.get("verdict") or "")
    if not (verdict == rebuilt or verdict.startswith(rebuilt + "; no evidence file (")):
        problems.append(f"{UNFINISHED}'s verdict {verdict[:160]!r} is not the ERROR verdict rebuilt from {RESULTS_ERROR} "
                        f"({rebuilt[:160]!r})")
    return problems


def finish_entry_cli(out: Path, ledger_path: Path | None = None) -> int:
    """`finish-entry DIR`: finish the ledger entry the ERROR path could not write (its DIR/ledger.unfinished.json), with the
    verdict and evidence recorded there. REFUSED (exit 2, the ledger untouched) unless that entry exists in the ledger,
    names the recorded seeds and is still "started" (C3-E03), and (the fourth check's C4-E05) the verdict is this driver's
    own ERROR verdict for it, rebuilt from DIR/results.error.json (`unfinished_problems`)."""
    path = Path(ledger_path or ledger.LEDGER)
    try:
        data = _read_record(out / UNFINISHED)
        record = _read_record(out / RESULTS_ERROR)
    except Refusal as error:
        print(f"REFUSED: {error}")
        return 2
    if data is None:
        print(f"REFUSED: {out / UNFINISHED} is not there: no entry was left unfinished in {out}")
        return 2
    try:
        entry = next((e for e in ledger.load(path).get("entries", []) if e.get("id") == data.get("entry_id")), None)
    except Exception as error:  # noqa: BLE001 - a ledger that cannot be read is said, never written
        print(f"REFUSED: the ledger {path} cannot be read ({type(error).__name__}: {safe_text(error, 200)})")
        return 2
    if entry is None or entry.get("status") != "started" or [entry.get("first"), entry.get("last")] != data.get("seeds"):
        print(f"REFUSED: ledger entry #{data.get('entry_id')} in {path} is "
              f"{'missing' if entry is None else repr(entry.get('status')) + ' for seeds ' + str([entry.get('first'), entry.get('last')])}"
              f", not a 'started' entry for seeds {data.get('seeds')}")
        return 2
    problems = unfinished_problems(data, record, entry)
    if problems:
        print(f"REFUSED: finish-entry writes only this driver's own ERROR verdict for entry #{entry.get('id')}: "
              f"{'; '.join(problems)}")
        return 2
    ledger.finish(data["entry_id"], data["verdict"], data.get("evidence"), path=path)
    print(f"FINISHED ledger entry #{data['entry_id']}: {data['verdict'][:300]}")
    return 0


def read_leg(run_dir: Path, truth: bool = False) -> dict:
    """One leg folder, READ ONLY: its log counts, its world.jsonl streamed (no copy kept, nothing deleted), and with
    `truth` the harness's truth of its end_state.ss1 against every chapter end's proof."""
    out: dict = {"log": read_log_counts(run_dir / "ai_player.log"), "world": None, "proofs": None}
    world = run_dir / "world.jsonl"
    if os.path.isfile(world):
        try:  # (C4-E01) the AI's file: one the OS refuses to open is said, never a crash
            out["world"] = stream_world_tail(world, None)
        except Exception as error:  # noqa: BLE001
            out["world"] = f"world.jsonl could not be read ({type(error).__name__}: {safe_text(error, 200)})"
    if truth and (run_dir / "end_state.ss1").is_file():
        from ai_player.gates import live_step5 as L5

        found, raw = L5.truth_of(run_dir / "end_state.ss1")
        marks = ((found or {}).get("story") or {}).get("marks")
        data = load_milestones()
        ends = {}
        for m in data["milestones"]:
            if not m.get("optional") and m.get("waypoint") is None:
                ends[m["chapter"]] = m
        out["proofs"] = {m["id"]: proof_holds(marks, {"flags": m["done"].get("flags") or {},
                                                      "variables": m["done"].get("variables") or {},
                                                      "trainers": m["done"].get("trainers") or {}})
                         for m in ends.values()} if marks else f"no truth: {raw[-400:]}"
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("bounds")
    p.add_argument("--run")
    p.add_argument("--to")
    p.add_argument("--first-seed", type=int)
    p.add_argument("--chains", type=int, choices=(3, 6))
    p.add_argument("--leg-frames")
    p = sub.add_parser("register")
    p.add_argument("--run", required=True)
    p.add_argument("--note-file")
    p = sub.add_parser("run")
    p.add_argument("--purpose", choices=("graded", "development"), required=True)  # NO default (spec section 7)
    p.add_argument("--run")
    p.add_argument("--first-seed", type=int)
    p.add_argument("--to")
    p.add_argument("--chains", type=int, choices=(3, 6))
    p.add_argument("--leg-frames")
    p.add_argument("--prediction-file")
    p.add_argument("--out", required=True)
    p.add_argument("--build-root")
    p = sub.add_parser("grade")
    p.add_argument("dir")
    p.add_argument("--ledger", type=Path, default=None)
    p = sub.add_parser("finish-entry")
    p.add_argument("dir")
    p.add_argument("--ledger", type=Path, default=None)
    p = sub.add_parser("read")
    p.add_argument("run_dir")
    p.add_argument("--truth", action="store_true")
    p = sub.add_parser("child")
    p.add_argument("job")
    return parser


def register_run(run: str, note_file: str | None = None, repo: Path | None = None, path: Path | None = None) -> int:
    """`register --run RUN`: pre-register GRADED_RUNS[run]'s seeds with registered_numbers()'s sha256 (exit 0), REFUSED
    (exit 2, the ledger untouched) for an unknown run, seeds another ledger entry names, or (R12, the checkers' C2-05,
    C3-H01 and C3-H02) a grader whose code could be a file the registration does not hash (`closure_missing`, every file
    named), or a closure that cannot be scanned (C3-E06: the file that does not parse is named). `repo` and `path` (the
    ledger) are the tests'."""
    repo = repo or REPO
    path = path or ledger.LEDGER
    if run not in GRADED_RUNS:
        print(f"REFUSED: --run {run!r} is not one of {sorted(GRADED_RUNS)}")
        return 2
    spec = GRADED_RUNS[run]
    seeds = spec["seeds"]
    named = [e for e in seeds_named(*seeds, path=path) if not (e["driver"] == DRIVER and e["status"] == "registered")]
    if named:
        print(f"REFUSED: ledger entries already name seeds {seeds[0]}-{seeds[1]}: {[e['id'] for e in named]}")
        return 2
    try:
        missing, size, seconds = closure_missing(repo)
    except Exception as error:  # noqa: BLE001 - (C3-E06) refused, naming the file, never a crash
        print(f"REFUSED: R12: the grader's import closure could not be scanned ({error_text(error)}), so what it runs "
              f"cannot be shown to be hashed")
        return 2
    refusal = closure_refusal(missing)
    if refusal is not None:
        print(f"REFUSED: {refusal}")
        return 2
    print(f"[LC] the grader's import closure: {size} files, every one hashed (scan {seconds} s)")
    legs = legs_of(spec["to"], load_milestones(repo))
    numbers = registered_numbers(run, spec["to"], seeds, 6, legs, repo)
    note = (Path(note_file).read_text(encoding="utf-8").strip() if note_file else
            f"LIVE CHAIN graded held-out (USER RULING 55), run {run}, to {spec['to']}, driver "
            f"ai_player/gates/live_chain.py: registered BEFORE any run; the bounds field is the sha256 of "
            f"registered_numbers() (the bounds text, the legs and proofs, every constant, the milestones', the AI "
            f"code's and the grader files' sha256)")
    print(numbers["bounds_text"])
    entry = register(seeds, numbers, note, path=path)
    print(f"REGISTERED numbers sha256 {ledger.numbers_sha256(numbers)}")
    print("ENTRY " + json.dumps(entry, ensure_ascii=False))
    return 0


#: (the third check's C3-E06) the exit code of an exception no guard covered (run_batch's guard covers ledger.begin to the
#: finish; before begin the ledger is untouched): never 1, which reads as a graded FAIL
CRASH_EXIT = 5


def main(argv: list[str] | None = None) -> int:
    """The command line (the module docstring). (C3-E06) an exception no guard covered exits CRASH_EXIT (5): 'a harness
    crash; see the ledger entry's status', never 1 (FAIL); a Ctrl+C propagates (run_batch's guard finishes the entry first)."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    args = build_parser().parse_args(argv)
    try:
        return command(args)
    except Exception:  # noqa: BLE001 - (C3-E06) a crash is never the FAIL code
        print(traceback.format_exc(), flush=True)
        print(f"[LC] HARNESS CRASH (exit {CRASH_EXIT}): no guard covered this exception; see the ledger entry's status "
              f"(before ledger.begin the ledger is untouched)", flush=True)
        return CRASH_EXIT


def command(args) -> int:
    if args.cmd == "child":
        return child(Path(args.job))
    if args.cmd == "bounds":
        if args.run:
            spec = GRADED_RUNS[args.run]
            to, first, chains, override = spec["to"], spec["seeds"][0], 6, {}
        else:
            to, first, chains = args.to, args.first_seed or 1, args.chains or 3
        legs = legs_of(to, load_milestones())
        if not args.run:
            override = parse_leg_frames(args.leg_frames, legs)
            legs = [{**leg, "frames": override.get(leg["leg"], leg["frames"])} for leg in legs]
        numbers = registered_numbers(args.run, to, seeds_of(first, chains), chains, legs)
        print(numbers["bounds_text"])
        print(json.dumps({k: v for k, v in numbers.items() if k != "bounds_text"}, indent=1))
        print(f"BOUNDS TEXT sha256 {hashlib.sha256(numbers['bounds_text'].encode('utf-8')).hexdigest()}")
        print(f"REGISTERED NUMBERS sha256 {ledger.numbers_sha256(numbers)}")
        return 0
    if args.cmd == "register":
        return register_run(args.run, args.note_file)
    if args.cmd == "run":
        return run_batch(args)
    if args.cmd == "grade":
        return grade_dir(Path(args.dir), args.ledger or ledger.LEDGER)
    if args.cmd == "finish-entry":
        return finish_entry_cli(Path(args.dir), args.ledger)
    if args.cmd == "read":
        print(json.dumps(read_leg(Path(args.run_dir), args.truth), indent=1, default=str))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
