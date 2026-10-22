#!/usr/bin/env python3
"""Selftest for tools/make_chapter_pack.py (spec S3-4, A5): every arm has a FAULT (the rule broken: it must be caught)
and a CONTROL (the healthy path passes).

    py -3.12 tools/story-dev/selftest_chapter_pack.py                       # every arm, real generator and inputs
    py -3.12 tools/story-dev/selftest_chapter_pack.py --work DIR            # scratch folder (default: temp, removed)
    py -3.12 tools/story-dev/selftest_chapter_pack.py --mutants --work DIR  # also: every mutant in a scratch copy of
                                                                            # the generator must fail some arm
    py -3.12 tools/story-dev/selftest_chapter_pack.py --decomp DIR          # the pinned decomp clone to use

EXIT: 0 every arm ran and passed; 1 an arm that RAN failed; 4 WARN: no arm failed, but the real-data arms were SKIPPED
because this machine has no pinned decomp clone ("real-data arms SKIPPED: no pinned decomp clone; not a pass").
WHY A THIRD STATE: every real generator run starts ai_player/gates/verify_world.py, which re-reads the PINNED decomp
and refuses without it, so on a machine with no clone those arms cannot pass; failing them would turn run_gates red for
a reason that is not a defect, and passing them silently would be a vacuous gate. So the clone is looked for FIRST,
the way verify_world and tools/decomp_lookup.py look (--decomp, else env POKEBOT_DECOMP, else the sibling
../_decomp/pokeemerald, whose `git rev-parse HEAD` must EQUAL tools/decomp.pin): without it the arms that need no clone
(the in-process guards, the fixtures, the pin and no-clone refusals, the hung-verifier timeout, deep_diff's bool test
and the WARN arms below) still run, every other scenario is listed as SKIP, and the exit is 4 unless a run arm failed
(then 1: a skip never hides a failure). run_gates lists this file in WARN_OK, so a 4 is counted OUT of the passing gates
and named, never as a pass.

It lives in tools/story-dev/ so run_gates.py finds it like every other suite; the generator stays in tools/ and is
run as a subprocess (and, for the arms that test its functions directly, loaded from its file path), so a mutant copy
is exercised exactly like the real one. The scenarios run in parallel threads (each generator run starts
verify_world, about 0.8 s), and the arms print in a fixed order at the end.

INTENT: a chapter pack is what an agent reads instead of re-doing a chapter's recon, so a pack that silently drops or
corrupts a trainer, a boss, an HM or a link, hides that a section is missing, or carries a stale hash is worse than no
pack. The first build passed 29 arms while chapters 19 and 24 crashed; the second passed 81 while 13 mutants that
corrupt real output (a boss losing its ace, Tate and Liza shown as a single battle, a links line blanked) survived,
because its checks compared a line's START. The arms, each FAULT + CONTROL:
  all         CONTROL every campaign chapter (24) generates, each passing its completeness checks and the 12 KB cap.
  F1 content  (round 2) the pack is compared VALUE BY VALUE with a second reading of the inputs (expected_pack), and
              the .md LINE BY LINE with a second rendering of it. FAULT (pack): a boss mon's held item or move, Tate and
              Liza's double flag, a connection's offset, an HM's badge, a claim's tail each changed in a real pack are
              named. FAULT (.md): a held item, a mon's moves, DOUBLE, one connection, a claim's last word, an HM's badge,
              an entry's needs, a summary's species each changed in a real page are named, beside the old removals
              (a boss mon, a double line, a claim, an HM line, a links line, a summary line, 'none fought' added).
              FAULT (generator): copies with the verify's mutants planted (a boss claim's last mon, a held item, a
              links line, Tate and Liza single, an HM's badge) exit 2. CONTROL: no finding on any real pack or page.
  F2 inputs   (round 2) the generator runs ai_player/gates/verify_world.py over every record first and refuses unless
              it reports 0 mismatches. FAULT: the verify's three omissions (an area DOUBLE battle, Roxanne's badge, a
              connection removed on BOTH sides) and three more (an ordinary trainer, a warp, Roxanne gone from two
              files) in scratch worlds each exit 2 naming verify_world and the record, writing nothing; a decomp
              folder that is no pinned clone exits 2; a refusal at chapter 13 of --all writes no earlier chapter.
              CONTROL: every pack header records the verification, and verify_world run here gives the same line.
  F1 shapes   a trainer object carries `script` (object, trigger) or `label` (map-script battle): CONTROL a fixture of
              each shape and the real ch19/ch24 packs; FAULT an object with neither is refused naming its map.
  F2 size     CONTROL every .md <= 12 KB, at least one chapter summarised, a forced summary of ch4 passes; FAULT a cap
              no load-bearing part fits (2000) refuses naming the cap.
  F3 complete CONTROL check_complete finds nothing on real packs. FAULT (pack level): one item per category removed is
              named. FAULT (input level, in-process so verify_world does not answer first): a boss row, a boss
              trainer's object on an area and on a ring map, the field-move row of a badge won and of a needed move,
              either side of a connection, a warp to a missing map each give EXACTLY one finding naming it.
  W3 recall   milestones.json's hand-recon'd `trainers` table must be fully contained in the ch1-4 packs. FAULT: JOSH's
              object removed from a scratch maps.json: recall on the pack built from it falls (in-process), and the
              real run refuses that world through verify_world. The milestone -> chapter mapping is the identity.
  R3 reader   (round 3) the check reads the input files with its OWN loader (read_inputs_for_check), never load_inputs'
              dict. FAULT: copies of the generator with the round-2 re-verify's six shared-reader mutants planted in
              load_inputs (Winona's and Roxanne's last mon a level low, ROUTE120<->121 and ROUTE119<->FORTREE dropped,
              KATE_AND_JOY read as single, CUT's badge read as BADGE02) each exit 2 naming it, nothing written; a pack
              whose header hash differs from the file is named. CONTROL: the real reader passes (the `all` arm).
  R3 timeout  FAULT: a verify_world that hangs makes the generator exit 2 naming --verify-timeout's bound, nothing
              written. CONTROL: the real verifier under an explicit timeout passes.
  R3 bool     FAULT: deep_diff names True vs 1 (and the reverse, and False vs 0), and a real pack whose double flag is
              written as 1 is named. CONTROL: equal values of one type give no finding.
  WARN path   (the run_gates follow-up) this file's own exit, by running it as a child with --no-warn-arms. FAULT: env
              POKEBOT_DECOMP at an empty folder exits 4 with every clone-free arm PASS and no real-data arm run, and
              so do --decomp at an empty folder and POKEBOT_DECOMP at a git checkout whose HEAD is not the pin (this
              repo, read only); a failing clone-free arm (deep_diff's bool clause deleted in a
              generator copy) with no clone exits 1, never 4. CONTROL (real-data): --decomp at the real clone wins
              over an empty POKEBOT_DECOMP, so the child runs every arm and exits 0.
  CRLF, routekeys, absent, hashes, empty chapter, pin, unknown area map, unknown trainer, extra entry field, non-normal
              wild rows, the one-way claims and --check: as before (each FAULT + CONTROL). The guards verify_world now
              answers first (area map, trainer, route keys, Wallace's label, the redirected warp, the entry field) are
              driven in-process through generate_loaded, which runs every guard but the verification.
--mutants deletes each guard's CALL and applies the verify's 24 + 15 mutants, each in a scratch copy; the selftest run
against that copy must fail. Nothing here writes outside --work; the committed packs and ai_player/ are only read.
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
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
GEN_DEFAULT = os.path.join(TOOLS, "make_chapter_pack.py")
WORLD = os.path.join(REPO, "ai_player", "knowledge", "world")
SEASONED = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
PIN = os.path.join(REPO, "tools", "decomp.pin")
#: where verify_world (DEFAULT_DECOMP) and tools/decomp_lookup.py look when neither --decomp nor POKEBOT_DECOMP is given
DEFAULT_DECOMP = os.path.normpath(os.path.join(REPO, "..", "_decomp", "pokeemerald"))
#: run_gates' WARN_EXIT: "ran, but could not verify" (see EXIT in the docstring)
WARN_EXIT = 4
WARN_TEXT = "real-data arms SKIPPED: no pinned decomp clone; not a pass"
#: bound on one child run of this file (the WARN arms); a full child run takes about 7 s
WARN_CHILD_TIMEOUT_S = 300
PACKS = os.path.join(REPO, "PROJECT KNOWLEDGE", "chapter-packs")
MILESTONES = os.path.join(REPO, "ai_player", "knowledge", "milestones.json")
EXTRACT_WORLD = os.path.join(REPO, "ai_player", "gates", "extract_world.py")
VERIFY_WORLD = os.path.join(REPO, "ai_player", "gates", "verify_world.py")
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
#: what the in-process arms pass as the verification record (generate_loaded runs every guard but the verification)
STUB_VERIFIED = {"by": "ai_player/gates/verify_world.py", "verifier_sha256": "0" * 64,
                 "command": "(selftest, in-process: verify_world not run)", "exit": None,
                 "result": "NOT RUN (in-process selftest arm)"}

#: guard -> (the exact text of its call in the generator, the text a call-deleting mutant puts there)
MUTANTS = {
    "check_pins": ("        check_pins(data, pin)\n", "        pass\n"),
    "verify_inputs": ("        verified = verify_inputs(args.world, args.decomp, args.verify_world, args.verify_timeout)\n",
                      '        verified = {"by": "-", "verifier_sha256": "0" * 64, "command": "-", "exit": 0, '
                      '"result": "-"}\n'),
    "verify_inputs PASS test": ("    if p.returncode != 0 or not VERIFY_PASS.match(summary):\n", "    if False:\n"),
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
    "refuse_incomplete(check_md_complete)": (
        "    refuse_incomplete(check_md_complete(pack, md, expected, md_cap), chapter)\n", "    pass\n"),
    "deep_diff (the value-by-value pack check)": (
        '        deep_diff(pack, with_provenance(expected["pack"], pack), "$", out)\n', "        pass\n"),
    "expected_md (the line-by-line page check)": (
        '    want = expected_md(with_provenance(expected["pack"], pack), cap).split("\\n")\n',
        '    want = md.split("\\n")\n'),
    "render_within_cap summary": ("        md = render_md(pack, summary_of=full, level=level)\n", "        pass\n"),
    # not a deletion: each chapter written as soon as it is made (the first build's behaviour), which leaves the
    # earlier chapters on disk when a later one refuses; the F2 partial-write arm must catch it
    "write only after every chapter is made": (
        "            made.append((n,) + generate_loaded(n, data, hashes, pin, args.md_cap, verified, check_src))\n",
        "            made.append((n,) + generate_loaded(n, data, hashes, pin, args.md_cap, verified, check_src))\n"
        "            if not args.check:\n"
        "                os.makedirs(args.out, exist_ok=True)\n"
        "                for ext, text in ((\"json\", made[-1][1]), (\"md\", made[-1][2])):\n"
        "                    with open(os.path.join(args.out, \"ch%d.%s\" % (n, ext)), \"w\", encoding=\"utf-8\",\n"
        "                              newline=\"\\n\") as f:\n"
        "                        f.write(text)\n"),
    # fix round 3: the check's own reader replaced by the FIRST reading (load_inputs' dict, through check_fields):
    # the reader-plant arms must then fail, because a defect in load_inputs reaches both sides again
    "read_inputs_for_check (the check's own reading)": (
        "    check_src = read_inputs_for_check(args.world, args.seasoned)\n",
        "    check_src = check_fields(data, hashes)\n"),
    # fix round 3: the verifier's timeout deleted (a hung verifier hangs the generator); the timeout arm must fail
    "verify_inputs timeout": ('errors="replace", timeout=timeout)', 'errors="replace")'),
    # fix round 3: deep_diff's bool-is-not-int clause deleted (True == 1 in Python); the bool arms must fail
    "deep_diff bool-is-not-int clause": ("    elif type(have) is not type(want) or have != want:\n",
                                         "    elif have != want:\n"),
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

#: the 2026-10-22 RE-verify's 15 render/claim mutants, verbatim from its reverify-work/newmut.py (13 of them survived
#: round 1's generator AND selftest; R6 and C5 were already caught)
REVERIFY_MUTANTS = {
    "R1_md_boss_moves_dropped": ('" ".join(short(m) for m in p.get("moves") or []),\n                                         (" @"',
                                 '"",\n                                         (" @"'),
    "R2_md_boss_held_item_dropped": ('(" @" + short(p["held_item"])) if p.get("held_item") else ""))\n    if pack["area_bosses_later"]',
                                     '""))\n    if pack["area_bosses_later"]'),
    "R3_md_boss_double_shown_single": ('                                            "DOUBLE" if b["double"] else "single",\n',
                                       '                                            "single",\n'),
    "R4_md_links_connections_blanked": ('        a("- **%s** (%s). Connections: %s. Warps: %s." % (short(m["id"]), ", ".join(flags), conns, warps))',
                                        '        a("- **%s** (%s). Connections: %s. Warps: %s." % (short(m["id"]), ", ".join(flags), "-", warps))'),
    "R5_md_links_warps_blanked": ('        a("- **%s** (%s). Connections: %s. Warps: %s." % (short(m["id"]), ", ".join(flags), conns, warps))',
                                  '        a("- **%s** (%s). Connections: %s. Warps: %s." % (short(m["id"]), ", ".join(flags), conns, "-"))'),
    "R6_md_trainer_double_shown_single": ('short(t["symbol"]), t["class"], "DOUBLE" if t["double"] else "single",',
                                          'short(t["symbol"]), t["class"], "single",'),
    "R7_md_entries_needs_dropped": ('            if (nd.get("badges") or nd.get("field_moves")) else ""))', '            if 0 else ""))'),
    "R8_md_hm_met_wild_none": ('            ", ".join(short(s) for s in h["learners_met_wild_here"]) or "none"))\n    a("")\n    a("## LOAD',
                               '            "none"))\n    a("")\n    a("## LOAD'),
    "R9_md_flash_flag_dropped": ('        if m["requires_flash"]:\n            flags.append("FLASH")', '        if 0:\n            flags.append("FLASH")'),
    "R10_md_summary_species_wrong": ('                "" if level >= 4 else ", species " + (" ".join(sp) or "-")))',
                                     '                "" if level >= 4 else ", species -"))'),
    "C1_claim_boss_team_last_mon_dropped": ('                         for p in b["party"])\n        out.append(("boss_team"',
                                            '                         for p in b["party"][:-1])\n        out.append(("boss_team"'),
    "C2_claim_boss_double_shown_single": ('            b["fight"], short(b["id"]), b["role"], "DOUBLE" if b["double"] else "single", team), b["ref"]))',
                                          '            b["fight"], short(b["id"]), b["role"], "single", team), b["ref"]))'),
    "C3_claim_hm_badge_wrong": ('            h["move"], h["hm"], h["badge"], h["learners_count"],', '            h["move"], h["hm"], "BADGE01", h["learners_count"],'),
    "C4_claim_hm_met_wild_none": ('            h["move"], h["hm"], h["badge"], h["learners_count"],\n            ", ".join(short(s) for s in h["learners_met_wild_here"]) or "none")',
                                  '            h["move"], h["hm"], h["badge"], h["learners_count"],\n            "none")'),
    "C5_claim_scripted_battle_names_first_only": ('        out.append(("scripted_battle", "%s can be started by a trigger tile (%s); the trigger\'s var condition is NOT "\n                                       "modelled here" % (" / ".join(syms),',
                                                  '        out.append(("scripted_battle", "%s can be started by a trigger tile (%s); the trigger\'s var condition is NOT "\n                                       "modelled here" % (" / ".join(syms[:1]),'),
}

#: the 2026-10-22 round-2 re-verify's SHARED-READER mutants, verbatim from its reverify2-work/newmut.py: each corrupts
#: load_inputs' dict after json.load (the files stay right, so verify_world passes). N1b, N5b and N10 survived round 2
#: (both readings consumed that dict); N1, N5 and N6 were killed only because a selftest fixture line went missing.
_RET = "    return data, hashes\n"
_BOSSES = 'data["ai_player/knowledge/world/bosses.json"]["bosses"]'
READER_MUTANTS = {
    "N1_level_shared_reader": (_RET, "    [p.__setitem__('level', p['level'] - 1) for b in %s if b['id'] == 'TRAINER_ROXANNE_1' for p in b['party'][-1:]]\n%s" % (_BOSSES, _RET)),
    "N5_connection_shared_reader": (_RET, "    [m.__setitem__('connections', [c for c in m['connections'] if c['map'] not in ('MAP_FORTREE_CITY', 'MAP_ROUTE119')]) for m in data['ai_player/knowledge/world/maps.json']['maps'] if m['id'] in ('MAP_ROUTE119', 'MAP_FORTREE_CITY')]\n%s" % _RET),
    "N6_hm_badge_shared_reader": (_RET, "    [r.__setitem__('badge', 'BADGE02') for r in data['ai_player/knowledge/world/campaign.json']['field_move_badges'] if r['move'] == 'CUT']\n%s" % _RET),
    "N1b_level_shared_reader_winona": (_RET, "    [p.__setitem__('level', p['level'] - 1) for b in %s if b['id'] == 'TRAINER_WINONA_1' for p in b['party'][-1:]]\n%s" % (_BOSSES, _RET)),
    "N5b_connection_shared_reader_r120_r121": (_RET, "    [m.__setitem__('connections', [c for c in m['connections'] if c['map'] not in ('MAP_ROUTE120', 'MAP_ROUTE121')]) for m in data['ai_player/knowledge/world/maps.json']['maps'] if m['id'] in ('MAP_ROUTE120', 'MAP_ROUTE121')]\n%s" % _RET),
    "N10_trainer_double_shared_reader": (_RET, "    [t.__setitem__('double', False) for t in data['ai_player/knowledge/world/trainers.json']['trainers'] if t['symbol'] == 'TRAINER_KATE_AND_JOY']\n%s" % _RET),
}

#: generator-level plants: a defect written into a scratch copy of the generator under test; the copy must exit 2
#: naming it (the in-run checks catch a GENERATOR that drops or corrupts an item, not only a broken input)
PLANTS = {
    "ring trainers dropped": (VERIFIER_MUTANTS["OM1_ring_trainers_dropped"], [4, 13], "MISSING trainer"),
    "last boss mon dropped from the .md": (VERIFIER_MUTANTS["OM12_boss_party_last_mon_dropped"], [4, 13],
                                           "md [Bosses]"),
    "HMs emptied": (VERIFIER_MUTANTS["OM4_hms_dropped"], [4, 13], "MISSING HM"),
    "boss_team claims dropped": (VERIFIER_MUTANTS["OM8_boss_team_claims_dropped"], [4, 13], "MISSING claim [boss_team]"),
    "boss_team claim losing its last mon (F1)": (REVERIFY_MUTANTS["C1_claim_boss_team_last_mon_dropped"], [4],
                                                 "WRONG pack $.claims[0].claim"),
    "boss held items dropped from the .md (F1)": (REVERIFY_MUTANTS["R2_md_boss_held_item_dropped"], [4],
                                                  "md [Bosses] line"),
    "links lines' connections blanked (F1)": (REVERIFY_MUTANTS["R4_md_links_connections_blanked"], [13],
                                              "md [Maps and links] line"),
    "Tate and Liza rendered as a single battle (F1)": (REVERIFY_MUTANTS["R3_md_boss_double_shown_single"], [18],
                                                       "(gym_leader, single)"),
    "an HM claim naming the wrong badge (F1)": (REVERIFY_MUTANTS["C3_claim_hm_badge_wrong"], [7], "WRONG pack $.claims"),
    # fix round 3: a defect INSIDE the first reader (load_inputs); the check's own reader of the files must name it
    "reader: Winona's ALTARIA one level low (R3)": (READER_MUTANTS["N1b_level_shared_reader_winona"], [13],
                                                    "WRONG boss TRAINER_WINONA_1 team"),
    "reader: ROUTE120 <-> ROUTE121 dropped (R3)": (READER_MUTANTS["N5b_connection_shared_reader_r120_r121"], [13],
                                                   "MISSING ring map MAP_ROUTE121"),
    "reader: KATE_AND_JOY read as a single battle (R3)": (READER_MUTANTS["N10_trainer_double_shared_reader"], [13],
                                                          "WRONG trainer TRAINER_KATE_AND_JOY double"),
    "reader: Roxanne's NOSEPASS one level low (R3)": (READER_MUTANTS["N1_level_shared_reader"], [4],
                                                      "WRONG pack $.bosses[0].party[2].level"),
    "reader: ROUTE119 <-> FORTREE_CITY dropped (R3)": (READER_MUTANTS["N5_connection_shared_reader"], [13],
                                                       "MISSING connection on MAP_ROUTE119"),
    "reader: CUT's badge read as BADGE02 (R3)": (READER_MUTANTS["N6_hm_badge_shared_reader"], [4], "MISSING HM CUT"),
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


def listing(folder):
    return sorted(os.listdir(folder)) if os.path.isdir(folder) else []


def decomp_clone(explicit=None):
    """(root, None) when the pinned decomp clone is on this machine, else (None, why).
    Looked for exactly where the generator's verifier looks (ai_player/gates/verify_world.py `pinned_root`, and
    tools/decomp_lookup.py `candidate_path`): `explicit` (--decomp), else env POKEBOT_DECOMP, else the sibling
    ../_decomp/pokeemerald; it counts only if `git rev-parse HEAD` there EQUALS tools/decomp.pin, so a folder that is
    no clone, a clone at another commit, or an empty folder that sits inside some other git repository (rev-parse then
    answers with THAT repo's HEAD) is "no clone". WHY a copy and not an import of verify_world: this decides only
    whether to run the real-data arms; those arms then run the real verifier, which applies its own check."""
    root = explicit or os.environ.get("POKEBOT_DECOMP") or DEFAULT_DECOMP
    with open(PIN, encoding="utf-8") as f:
        pin = f.read().strip()
    try:  # a missing folder needs no test of its own: git -C fails there, so HEAD is None
        r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "git rev-parse HEAD failed under %s (%s)" % (root, exc)
    head = r.stdout.strip() if r.returncode == 0 else None
    if head != pin:
        return None, "%s is not a clone at the pinned %s (HEAD %s)" % (root, pin, head)
    return root, None


class Runner:
    """Arms are collected per Runner; `child()` gives a scenario its own list, merged in a fixed order at the end."""

    def __init__(self, gen, work, shared=None):
        self.gen, self.work = gen, work
        self.results = []
        self.shared = shared if shared is not None else {"lock": threading.Lock()}

    def child(self):
        return Runner(self.gen, self.work, self.shared)

    def run(self, chapters, out, world=WORLD, seasoned=SEASONED, extra=(), gen=None, verifier=VERIFY_WORLD,
            timeout=None):
        """The generator as a subprocess: (exit code, stdout, stderr). With `timeout`, a run still going after that
        many seconds is killed and returns exit code None (an arm reads that as a hang)."""
        cmd = [sys.executable, gen or self.gen] + [str(c) for c in chapters] + [
            "--world", world, "--seasoned", seasoned, "--pin", PIN, "--out", out,
            "--verify-world", verifier] + list(extra)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, "", "(killed by the selftest after %s s: the generator did not return)" % timeout
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

    def mod(self):
        """The generator under test as a module, loaded once (shared by the scenarios)."""
        with self.shared["lock"]:
            if "mod" not in self.shared:
                self.shared["mod"] = import_generator(self.gen)
            return self.shared["mod"]

    def real_data(self):
        """The real inputs as the CHECK side reads them (read_inputs_for_check, the reading expected_selection takes),
        loaded once by the module under test (never mutated by an arm: they deep-copy)."""
        mod = self.mod()
        with self.shared["lock"]:
            if "data" not in self.shared:
                self.shared["data"] = mod.read_inputs_for_check(WORLD, SEASONED)
            return self.shared["data"]

    def inproc(self, chapters, world=WORLD, seasoned=SEASONED, cap=MD_CAP):
        """generate_loaded in-process (every guard but the verification), with both readings of the same folders.
        ("ok", {c: (pack, md)}) or ("refused", message); any other exception propagates (the arm fails with it)."""
        mod = self.mod()
        data, hashes = mod.load_inputs(world, seasoned)
        check_src = mod.read_inputs_for_check(world, seasoned)
        with open(PIN, encoding="utf-8") as f:
            pin = f.read().strip()
        try:
            mod.check_pins(data, pin)
            out = {}
            for c in chapters:
                js, md = mod.generate_loaded(c, data, hashes, pin, cap, STUB_VERIFIED, check_src)
                out[c] = (json.loads(js), md)
            return "ok", out
        except mod.PackError as exc:
            return "refused", str(exc)

    def arm(self, name, ok, detail=""):
        self.results.append((name, bool(ok), detail))

    def guarded(self, name, fn):
        """An arm whose body may raise (for instance on a generator without the function under test): a raise FAILS."""
        try:
            ok, detail = fn()
        except Exception as exc:  # noqa: BLE001 - any exception is the arm failing, with its text
            ok, detail = False, "%s: %s" % (type(exc).__name__, exc)
        self.arm(name, ok, detail)


def parallel(R, scenarios):
    """Run each scenario(child) in its own thread; merge their arms into R in the listed order. A scenario that
    raises becomes a FAIL arm naming it."""
    kids = [R.child() for _ in scenarios]

    def go(fn, kid):
        try:
            fn(kid)
        except Exception as exc:  # noqa: BLE001
            kid.arm("scenario %s ran" % fn.__name__, False, "%s: %s" % (type(exc).__name__, exc))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(scenarios))) as ex:
        for f in [ex.submit(go, fn, kid) for fn, kid in zip(scenarios, kids)]:
            f.result()
    for kid in kids:
        R.results.extend(kid.results)


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


def edit_world(d, name, fn):
    """Apply fn to the scratch copy of world/<name>; returns fn's result (whether the item to break was found)."""
    path = os.path.join(d, "world", name)
    obj = load(path)
    ok = fn(obj)
    save(obj, path)
    return ok


# ---------------------------------------------------------------- input edits shared by several arms
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


def drop_conn(src, dst):
    def fn(obj):
        m = next(x for x in obj["maps"] if x["id"] == src)
        n = len(m["connections"])
        m["connections"] = [c for c in m["connections"] if c["map"] != dst]
        return len(m["connections"]) == n - 1
    return fn


def drop_boss(sym):
    def fn(obj):
        n = len(obj["bosses"])
        obj["bosses"] = [b for b in obj["bosses"] if b["id"] != sym]
        return len(obj["bosses"]) == n - 1
    return fn


# ---------------------------------------------------------------- phase 1: scenarios that need no generated pack
def s_fresh(R):
    chapters = campaign_chapters()
    fresh = R.scratch("fresh")
    rc, out, err = R.run(["--all"], fresh)
    last = (err or out).strip().splitlines()[-1:] or [""]
    R.shared["fresh"] = fresh if rc == 0 else None
    R.arm("all CONTROL: every campaign chapter (%d: %s-%s) generates from the real inputs, verified by verify_world, "
          "each passing its completeness checks and the cap" % (len(chapters), chapters[0], chapters[-1]),
          rc == 0 and len(chapters) >= 24 and all(os.path.isfile(os.path.join(fresh, "ch%d.md" % c)) for c in chapters),
          last[0])


def s_again(R):
    again = R.scratch("again")
    rc, _, err = R.run(["--all"], again)
    R.shared["again"] = again if rc == 0 else None
    if rc != 0:
        R.arm("hashes CONTROL: the second --all run (for the determinism arm) ran", False, err.strip()[-200:])


def s_hash_fault(R):
    d = R.scratch("hash_fault", world_files=True)
    with open(os.path.join(d, "world", "trainers.json"), "ab") as f:
        f.write(b"\n")
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    exp = {k: sha256_lf(p) for k, p in SOURCES.items()}
    if rc == 0:
        hp = load(os.path.join(d, "out", "ch4.json"))["sources"]
        k = "ai_player/knowledge/world/trainers.json"
        changed = sorted(x for x in exp if hp.get(x) != exp[x])
        R.arm("hashes FAULT: one changed source changes exactly its own hash (changed: %s)" % changed,
              changed == [k] and hp[k] == sha256_lf(os.path.join(d, "world", "trainers.json")))
    else:
        R.arm("hashes FAULT: the scratch generation ran", False, err.strip()[-200:])


def s_crlf_input(R):
    d = R.scratch("crlf_input", world_files=True)
    p = os.path.join(d, "world", "trainers.json")
    to_crlf(os.path.join(WORLD, "trainers.json"), p)
    with open(p, "rb") as f:
        n_crlf = f.read().count(b"\r\n")
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    h = load(os.path.join(d, "out", "ch4.json"))["sources"].get("ai_player/knowledge/world/trainers.json") if rc == 0 \
        else None
    R.arm("CRLF CONTROL: a CRLF copy of trainers.json (%d CRLF) hashes as its LF original in the pack header" % n_crlf,
          n_crlf > 1000 and rc == 0 and h == sha256_lf(os.path.join(WORLD, "trainers.json")), err.strip()[-160:])


def s_empty(R):
    d = R.scratch("empty")
    rc, _, err = R.run([99], d)
    R.arm("empty FAULT: chapter 99 exits 2 naming it and writes nothing",
          rc == 2 and "chapter 99" in err and not os.listdir(d), err.strip()[-160:])
    rc, _, err = R.run([4], R.scratch("empty_control"))
    R.arm("empty CONTROL: chapter 4 exits 0", rc == 0, err.strip()[-160:])


def s_pin(R):
    d = R.scratch("pin_fault", world_files=True)
    tj = load(os.path.join(d, "world", "trainers.json"))
    tj["_source"] = "pret/pokeemerald@" + "0" * 40
    save(tj, os.path.join(d, "world", "trainers.json"))
    rc, _, err = R.run([4], os.path.join(d, "out"), world=os.path.join(d, "world"))
    # check_pins runs BEFORE verify_world, so this arm needs no clone (it runs in a WARN run too)
    R.arm("pin FAULT: one input's _source pin changed exits 2 naming trainers.json",
          rc == 2 and "trainers.json" in err and "pin" in err, err.strip()[-200:])


def s_wild_avail(R):
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
    real = load(os.path.join(R.shared["fresh"], "ch3.json")) if R.shared.get("fresh") else {"wild": []}
    R.arm("wild FAULT: Route104's rows (%d) marked not-normal in a scratch encounters.json leave the ch3 pack; "
          "CONTROL: the real ch3 pack has them" % n104,
          n104 >= 1 and rc == 0 and rows == [] and any(r["map"] == "MAP_ROUTE104" for r in real["wild"]),
          err.strip()[-200:])


def s_size(R):
    rc, _, err = R.run([4], R.scratch("size_fault"), extra=["--md-cap", "2000"])
    R.arm("F2 FAULT: a cap the load-bearing part cannot fit (2000) still refuses with exit 2 naming the cap",
          rc == 2 and "cap" in err, err.strip()[-160:])


#: F2 input omissions: (name, chapters, file, edit, the record verify_world must name)
OMISSIONS = [
    ("an area DOUBLE battle (AMY_AND_LIV_1 on ROUTE103, ch1) removed", [1], "maps.json",
     drop_object("MAP_ROUTE103", "TRAINER_AMY_AND_LIV_1"), "MAP_ROUTE103"),
    ("Roxanne's badge key removed from bosses.json (ch4 loses CUT and the BADGE01 claim)", [4], "bosses.json",
     lambda o: next(b for b in o["bosses"] if b["id"] == "TRAINER_ROXANNE_1").pop("badge", None) is not None,
     "TRAINER_ROXANNE_1"),
    ("ROUTE119 <-> FORTREE_CITY removed on BOTH sides (ch13)", [13], "maps.json",
     lambda o: drop_conn("MAP_ROUTE119", "MAP_FORTREE_CITY")(o) and drop_conn("MAP_FORTREE_CITY", "MAP_ROUTE119")(o),
     "MAP_ROUTE119"),
    ("an ORDINARY trainer (GREG on ROUTE119, ch13) removed", [13], "maps.json",
     drop_object("MAP_ROUTE119", "TRAINER_GREG"), "MAP_ROUTE119"),
    ("FORTREE_CITY's last warp removed (ch13)", [13], "maps.json",
     lambda o: bool(next(m for m in o["maps"] if m["id"] == "MAP_FORTREE_CITY")["warps"].pop()), "MAP_FORTREE_CITY"),
]


def omission_scenario(i):
    name, chapters, fname, fn, needle = OMISSIONS[i]

    def scenario(R):
        d = R.scratch("f2_omission_%d" % i, world_files=True)
        found = edit_world(d, fname, fn)
        out = os.path.join(d, "out")
        rc, _, err = R.run(chapters, out, world=os.path.join(d, "world"))
        R.arm("F2 FAULT (input): %s -> exit 2 naming verify_world and %s, nothing written" % (name, needle),
              found and rc == 2 and "verify_world" in err and needle in err and "MISMATCH" in err and not listing(out),
              (err.strip()[-300:] or "exit %d" % rc))
    scenario.__name__ = "omission_%d" % i
    return scenario


def s_roxanne_two_files(R):
    d = R.scratch("f2_roxanne_two_files", world_files=True)
    ok1 = edit_world(d, "campaign.json", lambda o: [e.update(boss=None, fights=[]) for e in o["entries"]
                                                    if e["id"] == "ch4_roxanne"] != [])
    ok2 = edit_world(d, "bosses.json", drop_boss("TRAINER_ROXANNE_1"))
    out = os.path.join(d, "out")
    rc, _, err = R.run([4], out, world=os.path.join(d, "world"))
    R.arm("F2 FAULT (input): Roxanne removed from campaign.json AND bosses.json -> exit 2 naming verify_world, "
          "nothing written", ok1 and ok2 and rc == 2 and "verify_world" in err and "ROXANNE" in err and not listing(out),
          err.strip()[-300:] or "exit %d" % rc)


def s_no_clone(R):
    d = R.scratch("f2_no_clone")
    empty = os.path.join(d, "not_a_clone")
    os.makedirs(empty)
    out = os.path.join(d, "out")
    rc, _, err = R.run([4], out, extra=["--decomp", empty])
    R.arm("F2 FAULT: a decomp folder that is no pinned clone (verify_world refuses, exit 2) -> exit 2 naming "
          "verify_world, nothing written", rc == 2 and "verify_world" in err and "REFUSED" in err and not listing(out),
          err.strip()[-300:])


def s_w3_world(R):
    """W3 FAULT: the pack built from a world without JOSH's object misses him (in-process, because the real run now
    refuses that world through verify_world, which is the other half of this arm: s_w3_world_real, which needs the
    pinned clone while this half does not)."""
    ms = load(MILESTONES)
    d = R.scratch("w3_fault", world_files=True)
    found = edit_world(d, "maps.json", drop_object("MAP_RUSTBORO_CITY_GYM", "TRAINER_JOSH"))

    def body():
        status, got = R.inproc(W3_CHAPTERS, world=os.path.join(d, "world"))
        if status != "ok":
            return False, "in-process generation refused: %s" % got[:200]
        h3, t3, miss3, _ = recall({c: got[c][0] for c in got}, {c: got[c][1] for c in got}, ms)
        return found and h3 < t3 and any("JOSH" in x for x in miss3), "%d/%d %s" % (h3, t3, "; ".join(miss3[:2]))
    R.guarded("W3 FAULT: JOSH's object removed from a scratch maps.json -> recall on the pack built from it falls, "
              "naming JOSH", body)


def s_w3_world_real(R):
    """The real-data half of s_w3_world (split from it so the in-process half runs without a clone): the generator
    run on the same broken world is refused by verify_world, which reads the pinned decomp."""
    d = R.scratch("w3_fault_real", world_files=True)
    found = edit_world(d, "maps.json", drop_object("MAP_RUSTBORO_CITY_GYM", "TRAINER_JOSH"))
    out = os.path.join(d, "out")
    rc, _, err = R.run(W3_CHAPTERS, out, world=os.path.join(d, "world"))
    R.arm("W3 FAULT: the real run on that world exits 2 through verify_world naming MAP_RUSTBORO_CITY_GYM, nothing "
          "written", found and rc == 2 and "verify_world" in err and "MAP_RUSTBORO_CITY_GYM" in err and not listing(out),
          err.strip()[-200:])


def s_guards_inproc(R):
    """The guards behind verify_world, each driven in-process through generate_loaded on a broken scratch world."""
    def world_case(name, fname, fn, chapters, check):
        d = R.scratch("inproc_" + re.sub(r"\W+", "_", name), world_files=True)
        found = edit_world(d, fname, fn)

        def body():
            status, got = R.inproc(chapters, world=os.path.join(d, "world"))
            ok, detail = check(status, got)
            return found and ok, detail
        R.guarded(name, body)

    def refused(*needles):
        def check(status, got):
            return status == "refused" and all(n in got for n in needles), str(got)[:300]
        return check

    def rename_area(o):
        e4 = next(e for e in o["entries"] if e["chapter"] == 4)
        e4["area"] = [a + "_RENAMED" for a in e4["area"]]
        return True
    world_case("areamap FAULT: a renamed area map is refused naming it (in-process)", "campaign.json", rename_area,
               [4], refused("RUSTBORO_CITY_GYM_RENAMED"))

    def unknown_trainer(o):
        gym = next(m for m in o["maps"] if m["id"] == "MAP_RUSTBORO_CITY_GYM")
        gym["trainers"][0]["trainers"] = ["TRAINER_NOBODY_AT_ALL"]
        return True
    world_case("trainer FAULT: an unknown trainer symbol on a map is refused naming it (in-process)", "maps.json",
               unknown_trainer, [4], refused("TRAINER_NOBODY_AT_ALL"))

    def private(o):
        next(e for e in o["entries"] if e["chapter"] == 4)["private_note"] = "never copy me"
        return True
    world_case("entries FAULT: a field outside ENTRY_FIELDS planted in a ch4 entry is not carried (in-process)",
               "campaign.json", private, [4],
               lambda s, g: (s == "ok" and not any("private_note" in e for e in g[4][0]["entries"]), str(g)[:200]))

    def no_label(o):
        room = next(m for m in o["maps"] if m["id"] == "MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM")
        obj = next(x for x in room["trainers"] if x["trainers"] == ["TRAINER_WALLACE"])
        return obj.pop("label", None) is not None
    world_case("F1 FAULT: Wallace's `label` removed -> ch24 is refused naming the Champion's room (in-process)",
               "maps.json", no_label, [24], refused("MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM"))

    def woods(o):
        next(m for m in o["maps"] if m["id"] == "MAP_PETALBURG_WOODS")["warps"][0]["dest_map"] = "MAP_ROUTE102"
        return True

    def one_way(s, g):
        if s != "ok":
            return False, str(g)[:200]
        ow = [c["claim"] for c in g[3][0]["claims"] if c["kind"] == "one_way_warp"]
        return (any(c.startswith("ROUTE104 warp") and "PETALBURG_WOODS" in c for c in ow)
                and not any(c.startswith("none of") for c in ow)), str(ow[:2])
    world_case("claims FAULT: Petalburg Woods' arrival warp 0 redirected -> one-way claims name ROUTE104 -> "
               "PETALBURG_WOODS (in-process)", "maps.json", woods, [3], one_way)
    for name, plant, want in (
            ("in a dict (needs.route)", lambda e: e["needs"].__setitem__("route", ["RUSTBORO_CITY"]), "needs.route"),
            ("inside a LIST (needs.badge_gates[0].steps)",
             lambda e: e["needs"].__setitem__("badge_gates", [{"steps": 3}]), "badge_gates[0].steps")):
        e4_id = next(e for e in load(os.path.join(WORLD, "campaign.json"))["entries"] if e["chapter"] == 4)["id"]

        def plant_it(o, plant=plant):
            plant(next(e for e in o["entries"] if e["chapter"] == 4))
            return True
        world_case("routekeys FAULT: a route key planted %s in a ch4 entry is refused naming it (in-process)" % name,
                   "campaign.json", plant_it, [4], refused(want, e4_id))


def s_input_problems(R):
    """F3 input level: an item lost from one input, named by another, gives EXACTLY that one finding (in-process:
    the real run refuses these worlds through verify_world before the cross-checks speak)."""
    def input_fault(name, chapter, fname, fn, needles):
        d = R.scratch("f3_" + re.sub(r"\W+", "_", name), world_files=True)
        found = edit_world(d, fname, fn)

        def body():
            status, got = R.inproc([chapter], world=os.path.join(d, "world"))
            n = findings_count(got) if status == "refused" else None
            return found and status == "refused" and n == 1 and all(x in got for x in needles), str(got)[-300:]
        R.guarded("F3 FAULT (input, in-process): %s -> ch%d is refused with exactly 1 finding naming it" % (
            name, chapter), body)

    def drop_fmb(move):
        def fn(obj):
            n = len(obj["field_move_badges"])
            obj["field_move_badges"] = [r for r in obj["field_move_badges"] if r["move"] != move]
            return len(obj["field_move_badges"]) == n - 1
        return fn

    def warp_nowhere(obj):
        next(x for x in obj["maps"] if x["id"] == "MAP_RUSTBORO_CITY_GYM")["warps"][0]["dest_map"] = "MAP_NOWHERE_AT_ALL"
        return True

    input_fault("boss row ROXANNE_1 removed from bosses.json", 4, "bosses.json", drop_boss("TRAINER_ROXANNE_1"),
                ["ROXANNE", "bosses.json has no row"])
    input_fault("ROXANNE_1's object removed from the Gym (an area map)", 4, "maps.json",
                drop_object("MAP_RUSTBORO_CITY_GYM", "TRAINER_ROXANNE_1"),
                ["TRAINER_ROXANNE_1", "MAP_RUSTBORO_CITY_GYM"])
    input_fault("BRENDAN_RUSTBORO_MUDKIP's object removed from RUSTBORO_CITY (a ring map)", 4, "maps.json",
                drop_object("MAP_RUSTBORO_CITY", "TRAINER_BRENDAN_RUSTBORO_MUDKIP"),
                ["TRAINER_BRENDAN_RUSTBORO_MUDKIP", "MAP_RUSTBORO_CITY"])
    input_fault("CUT's field_move_badges row removed (a badge won here)", 4, "campaign.json", drop_fmb("CUT"),
                ["BADGE01", "field_move_badges"])
    input_fault("SURF's field_move_badges row removed (a field move an entry needs)", 13, "campaign.json",
                drop_fmb("SURF"), ["ch13_route118 needs field move SURF", "no row"])
    input_fault("ROUTE103's connection to ROUTE110 removed (the area side)", 1, "maps.json",
                drop_conn("MAP_ROUTE103", "MAP_ROUTE110"), ["MAP_ROUTE110 connects", "MAP_ROUTE103"])
    input_fault("ROUTE110's connection to ROUTE103 removed (the ring side)", 1, "maps.json",
                drop_conn("MAP_ROUTE110", "MAP_ROUTE103"), ["MAP_ROUTE103 connects", "MAP_ROUTE110 has no connection back"])
    input_fault("the Gym's warp 0 sent to a map maps.json does not hold", 4, "maps.json", warp_nowhere,
                ["MAP_NOWHERE_AT_ALL"])


def plant_scenario(name):
    (old, new), chapters, needle = PLANTS[name]

    def scenario(R):
        with open(R.gen, encoding="utf-8") as f:
            src = f.read()
        if src.count(old) != 1:
            R.arm("F3/F1 FAULT (generator): %s" % name, False, "plant text occurs %d times (want 1)" % src.count(old))
            return
        d = R.scratch("plant_" + re.sub(r"\W+", "_", name))
        g = os.path.join(d, "make_chapter_pack.py")
        with open(g, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace(old, new))
        out = os.path.join(d, "out")
        rc, _, err = R.run(chapters, out, gen=g)
        R.arm("F3/F1 FAULT (generator): a copy whose %s exits 2 naming it, nothing written" % name,
              rc == 2 and needle in err and "Traceback" not in err and not listing(out), err.strip()[-240:])
    scenario.__name__ = "plant " + name
    return scenario


def s_mapping(R):
    ms = load(MILESTONES)
    camp = load(os.path.join(WORLD, "campaign.json"))
    errs = chapter_mapping_errors(ms, camp)
    R.arm("W3 mapping CONTROL: every milestone id is a campaign entry of the SAME chapter (%d milestones)" % len(
        ms["milestones"]), not errs and len(ms["milestones"]) == 20, "; ".join(errs[:3]))
    bad = json.loads(json.dumps(ms))
    bad["milestones"][-1]["chapter"] = 5
    R.arm("W3 mapping FAULT: one milestone's chapter changed is reported",
          any(bad["milestones"][-1]["id"] in x for x in chapter_mapping_errors(bad, camp)))


def s_f1_fixtures(R):
    def fixture():
        mod = R.mod()
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
        mod = R.mod()
        maps_by_id = {"MAP_FIX": {"trainers": [{"source": "script", "ref": "x", "trainers": ["TRAINER_A"]}]}}
        tby = {"TRAINER_A": {"id": 1, "name": "A", "class_name": "C", "double": False, "flag": 1001,
                             "party": [{"species": "SPECIES_X", "level": 5}], "ref": "r"}}
        try:
            mod.trainers_on(["MAP_FIX"], ["MAP_FIX"], maps_by_id, tby)
        except mod.PackError as exc:
            return "MAP_FIX" in str(exc), str(exc)
        return False, "no PackError"
    R.guarded("F1 FAULT: a fixture object with neither `script` nor `label` raises PackError naming its map", neither)


def s_routekey_source(R):
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


# ---------------------------------------------------------------- phase 2: scenarios that read the fresh packs
def fresh_packs(R):
    chapters = campaign_chapters()
    return chapters, read_packs(R.shared["fresh"], chapters)


def s_w3_control(R):
    ms = load(MILESTONES)
    chapters, (packs, mds) = fresh_packs(R)
    h, t, miss, extras = recall({c: packs[c] for c in W3_CHAPTERS}, {c: mds[c] for c in W3_CHAPTERS}, ms)
    R.arm("W3 CONTROL: recall on freshly generated ch1-4 packs is 100%% (%d/%d facts, %d table trainers; extras "
          "adjudicated in the report: %s)" % (h, t, len(ms["trainers"]), {c: len(extras[c]) for c in extras}),
          h == t and t == 3 * len(ms["trainers"]) and t > 0, "; ".join(miss[:3]))
    if all(os.path.isfile(os.path.join(PACKS, "ch%d.%s" % (c, x))) for c in chapters for x in ("json", "md")):
        cp, cm = read_packs(PACKS, W3_CHAPTERS)
        h2, t2, miss2, _ = recall(cp, cm, ms)
        R.arm("W3 CONTROL: recall on the COMMITTED packs is 100%% (%d/%d)" % (h2, t2), h2 == t2 and t2 > 0,
              "; ".join(miss2[:3]))
    else:
        R.arm("W3 CONTROL: the committed packs exist for every chapter", False, "missing under %s" % PACKS)


def s_header_arms(R):
    chapters, (packs, mds) = fresh_packs(R)
    R.arm("absent CONTROL: every generated header names the absent sections and that the decomp wins",
          all(absent_ok(mds[c], packs[c]) for c in chapters))
    cut = "\n".join(line for line in mds[4].split("\n") if ABSENT_MARKERS[0] not in line)
    R.arm("absent FAULT: a .md with the items line removed is caught", not absent_ok(cut, packs[4]))
    exp = {k: sha256_lf(p) for k, p in SOURCES.items()}
    R.arm("hashes CONTROL: every pack's source sha256 equals the file's own (7 sources)",
          all(packs[c]["sources"] == exp for c in chapters) and len(exp) == 7)
    R.arm("hashes CONTROL: the generator sha256 is the generator's own",
          all(packs[c]["generator"]["sha256"] == sha256_lf(R.gen) for c in chapters))
    again = R.shared.get("again")
    same = bool(again) and all(
        open(os.path.join(R.shared["fresh"], "ch%d.%s" % (c, x)), "rb").read() ==
        open(os.path.join(again, "ch%d.%s" % (c, x)), "rb").read() for c in chapters for x in ("json", "md"))
    R.arm("hashes CONTROL: two runs give identical bytes (a determinism check, not a replication)", same)
    with open(PIN, encoding="utf-8") as f:
        pin = f.read().strip()
    R.arm("pin CONTROL: the real inputs pass and every pack names tools/decomp.pin (%s)" % pin[:12],
          all(packs[c]["decomp_pin"] == pin for c in chapters) and len(pin) == 40)
    camp = load(os.path.join(WORLD, "campaign.json"))
    camp_area = {c: {"MAP_" + a for e in camp["entries"] if e["chapter"] == c for a in e["area"]} for c in chapters}
    R.arm("areamap/trainer CONTROL: each pack's area maps are exactly its entries' areas, and each has trainers",
          all({m["id"] for m in packs[c]["maps"] if m["role"] == "area"} == camp_area[c] and packs[c]["trainers"]
              for c in chapters))
    hits = [h for c in chapters for h in route_keys(packs[c]["entries"])]
    R.arm("routekeys CONTROL: no x/y/route/path/steps/coords key in any pack's campaign entries", not hits, str(hits[:3]))
    ow = [c["claim"] for c in packs[3]["claims"] if c["kind"] == "one_way_warp"]
    R.arm("claims CONTROL: ch3's warps are all two-way, said as a counted 'none of N' claim",
          len(ow) == 1 and ow[0].startswith("none of the ") and int(ow[0].split()[3]) > 0, str(ow))
    want = {(19, "TRAINER_MAXIE_MOSSDEEP"): "MossdeepCity_SpaceCenter_2F_EventScript_MaxieTrainer",
            (24, "TRAINER_WALLACE"): "EverGrandeCity_ChampionsRoom_EventScript_Wallace"}
    got = {k: [s.get("script") for t in packs[k[0]]["trainers"] if t["symbol"] == k[1] for s in t["seen"]]
           for k in want}
    R.arm("F1 CONTROL: the real ch19 and ch24 packs cite the map-script battles by their labels (Maxie, Wallace)",
          all(got[k] == [v] for k, v in want.items()), str(got))


def s_f2_verified(R):
    """F2 CONTROL: every header records the verification, and verify_world run here prints the same line."""
    chapters, (packs, mds) = fresh_packs(R)
    p = subprocess.run([sys.executable, VERIFY_WORLD, "--data", WORLD, "--knowledge", WORLD], capture_output=True,
                       text=True, encoding="utf-8")
    line = next((ln for ln in reversed(p.stdout.strip().splitlines()) if ln.startswith("[VERIFY-WORLD]")), "")
    rec = [packs[c].get("inputs_verified") or {} for c in chapters]
    ok = p.returncode == 0 and line.startswith("[VERIFY-WORLD] PASS: 0 mismatches (every record;") and all(
        r.get("result") == line and r.get("exit") == 0 and r.get("by") == "ai_player/gates/verify_world.py" and
        r.get("verifier_sha256") == sha256_lf(VERIFY_WORLD) and
        r.get("command") == "py -3.12 ai_player/gates/verify_world.py --data ai_player/knowledge/world --knowledge "
                            "ai_player/knowledge/world" for r in rec) and \
        all("verified first by `ai_player/gates/verify_world.py`" in mds[c] and "exit 0, 0 mismatches" in mds[c]
            for c in chapters)
    R.arm("F2 CONTROL: every pack header records verify_world's command and its PASS line over every record, and "
          "verify_world run here prints the same line", ok, line[:200] if not ok else "")


def s_f2_partial(R):
    """F2: a refusal late in --all writes no earlier chapter (every chapter is made in memory first)."""
    chapters, (packs, mds) = fresh_packs(R)
    sizes = {c: len(mds[c].encode("utf-8")) for c in chapters}
    deepest = [c for c in chapters if "SUMMARISED to fit the cap (level %d" % 4 in mds[c]]
    c = max(deepest, key=lambda x: sizes[x]) if deepest else None
    if c is None or c == chapters[0]:
        R.arm("F2 FAULT: a chapter at the deepest summary level exists past the first (to refuse late in --all)", False,
              str(deepest))
        return
    out = R.scratch("f2_partial")
    rc, _, err = R.run(["--all"], out, extra=["--md-cap", str(sizes[c] - 1)])
    R.arm("F2 FAULT: --all with the cap one byte under ch%d's deepest page refuses at ch%d (exit 2) and writes NO "
          "earlier chapter" % (c, c), rc == 2 and ("REFUSED ch%d" % c) in err and not listing(out),
          (err.strip()[-200:] or "exit %d, wrote %s" % (rc, listing(out)[:4])))


def s_f2_size(R):
    chapters, (packs, mds) = fresh_packs(R)
    sizes = {c: len(mds[c].encode("utf-8")) for c in chapters}
    summ = sorted(c for c in chapters if "SUMMARISED to fit the cap" in mds[c])
    R.arm("F2 CONTROL: every .md <= %d bytes (largest ch%d, %d) and at least one chapter was summarised (%s)" % (
        MD_CAP, max(sizes, key=sizes.get), max(sizes.values()), summ), all(s <= MD_CAP for s in sizes.values()) and summ)
    full4 = sizes[4]
    d = R.scratch("f2_force")
    rc, out, err = R.run([4], d, extra=["--md-cap", str(full4 - 1)])
    md4 = open(os.path.join(d, "ch4.md"), encoding="utf-8").read() if rc == 0 else ""
    R.arm("F2 CONTROL: ch4 with the cap one byte under its full size is summarised, fits, and passes its own "
          "completeness checks (exit 0)", rc == 0 and "SUMMARISED to fit the cap" in md4 and
          len(md4.encode("utf-8")) < full4, (err or out).strip()[-200:])


def line_edit(pred, fn):
    """A page mutation: the FIRST line matching pred replaced by fn(line) (None = the line removed); None if no line
    matches or the edit changes nothing (so an arm can never pass on a no-op)."""
    def m(lines):
        idx = [i for i, ln in enumerate(lines) if pred(ln)]
        if not idx:
            return None
        new = fn(lines[idx[0]])
        if new == lines[idx[0]]:
            return None
        return lines[:idx[0]] + ([] if new is None else [new]) + lines[idx[0] + 1:]
    return m


#: F1 page faults: (chapter, what, mutation of the page's lines, the finding's needle). Each changes ONE thing inside a
#: line whose start stays intact: the first build's prefix checks passed every one of these.
MD_FAULTS = [
    (4, "Roxanne's NOSEPASS losing its held item (@ORAN_BERRY)",
     line_edit(lambda ln: ln.startswith("  - NOSEPASS Lv15 ") and "@" in ln, lambda ln: ln.rsplit(" @", 1)[0]),
     "md [Bosses] line"),
    (1, "a rival mon losing its moves",
     line_edit(lambda ln: ln.startswith("  - TREECKO Lv5 [GRASS] "), lambda ln: "  - TREECKO Lv5 [GRASS] "),
     "md [Bosses] line"),
    (18, "Tate and Liza's header saying single",
     line_edit(lambda ln: ln.startswith("- **TATE_AND_LIZA** ") and "DOUBLE" in ln,
               lambda ln: ln.replace("DOUBLE", "single")), "md [Bosses] line"),
    (1, "AMY_AND_LIV_1's trainer line saying single",
     line_edit(lambda ln: "`AMY_AND_LIV_1`" in ln and "DOUBLE" in ln, lambda ln: ln.replace("DOUBLE", "single")),
     "md [Trainers] line"),
    (13, "ROUTE119's links line losing FORTREE_CITY",
     line_edit(lambda ln: ln.startswith("- **ROUTE119** (") and "FORTREE_CITY" in ln,
               lambda ln: re.sub(r",? ?\w+ FORTREE_CITY", "", ln, count=1)), "md [Maps and links] line"),
    (7, "FLASH's HM line naming BADGE01",
     line_edit(lambda ln: ln.startswith("- FLASH (") and "badge BADGE02" in ln,
               lambda ln: ln.replace("badge BADGE02", "badge BADGE01")), "md [HM moves] line"),
    (13, "claim 1's last word changed",
     line_edit(lambda ln: ln.startswith("1. ["), lambda ln: ln[:-1] + ("X" if ln[-1] != "X" else "Y")),
     "md [LOAD-BEARING CLAIMS] line"),
    (10, "an entry losing its needs",
     line_edit(lambda ln: ln.startswith("- **ch10_") and "; needs " in ln, lambda ln: ln.split("; needs ")[0]),
     "md [Entries] line"),
    (9, "a summary line's species emptied",
     line_edit(lambda ln: re.match(r"- [A-Z0-9_]+: \d+ ordinary trainers?, Lv \d+-\d+, species \w", ln) is not None,
               lambda ln: ln.split(", species ")[0] + ", species -"), "md [Trainers] line"),
    # the first round's removals, still caught
    (13, "the last boss's last mon removed",
     lambda ls: (lambda i: ls[:i] + ls[i + 1:])(max(i for i, ln in enumerate(ls) if ln.startswith("  - "))),
     "md [Bosses]"),
    (13, "a DOUBLE battle line removed", line_edit(lambda ln: ln.startswith("- ") and "`" in ln and ", DOUBLE, " in ln,
                                                   lambda ln: None), "md [Trainers]"),
    (13, "claim 3 removed", line_edit(lambda ln: ln.startswith("3. ["), lambda ln: None), "md [LOAD-BEARING CLAIMS]"),
    (13, "an HM line removed", line_edit(lambda ln: ln.startswith("- SURF ("), lambda ln: None), "md [HM moves]"),
    (13, "an area map's links line removed", line_edit(lambda ln: ln.startswith("- **ROUTE119** ("), lambda ln: None),
     "md [Maps and links]"),
    (13, "a per-map summary line removed",
     line_edit(lambda ln: re.match(r"- [A-Z0-9_]+: \d+ ordinary trainer", ln) is not None, lambda ln: None),
     "md [Trainers]"),
    (13, "'none fought' added", lambda ls: ls + ["- none fought in this chapter's entries"], "none fought"),
]


def boss_mon(c, fight, k):
    def get(p):
        b = next(b for b in p["bosses"] if b["fight"] == fight)
        return b["party"][k]
    return get


#: F1 pack faults: (chapter, what, mutation of a deep copy of the real pack (False = the item was not found), needle)
PACK_FAULTS = [
    (4, "Roxanne's NOSEPASS losing its held item",
     lambda p: boss_mon(4, "ROXANNE", -1)(p).pop("held_item", None) is not None, "$.bosses[0].party["),
    (4, "Roxanne's last mon's first move changed",
     lambda p: bool(boss_mon(4, "ROXANNE", -1)(p)["moves"]) and boss_mon(4, "ROXANNE", -1)(p)["moves"].__setitem__(
         0, "MOVE_SPLASH") is None, "].moves[0]"),
    (18, "Tate and Liza's double flag cleared",
     lambda p: next(b for b in p["bosses"] if b["fight"] == "TATE_AND_LIZA").__setitem__("double", False) is None,
     "$.bosses[0].double"),
    (13, "ROUTE119's first connection offset changed",
     lambda p: bool(next(r for r in p["links"] if r["map"] == "MAP_ROUTE119")["connections"]) and next(
         r for r in p["links"] if r["map"] == "MAP_ROUTE119")["connections"][0].__setitem__("offset", 99) is None,
     "].connections[0].offset"),
    (7, "FLASH's badge changed in the HM section", lambda p: next(h for h in p["hms"] if h["move"] == "FLASH")
     .__setitem__("badge", "BADGE01") is None, "].badge"),
    (4, "the boss_team claim losing its last mon (text only)",
     lambda p: next(c for c in p["claims"] if c["kind"] == "boss_team").__setitem__(
         "claim", next(c for c in p["claims"] if c["kind"] == "boss_team")["claim"].rsplit(", ", 1)[0]) is None,
     "$.claims[0].claim"),
    (13, "a claim's source changed", lambda p: p["claims"][0].__setitem__("source", "src/nowhere.c:1") is None,
     "$.claims[0].source"),
    (1, "a trainer's sighting sight changed",
     lambda p: next(s for t in p["trainers"] for s in t["seen"] if "sight" in s).__setitem__("sight", 99) is None,
     "].sight"),
    # fix round 3: a bool written as an int (True == 1 in Python, so only deep_diff's type test can see these)
    (18, "Tate and Liza's double flag written as the int 1",
     lambda p: next(b for b in p["bosses"] if b["fight"] == "TATE_AND_LIZA").__setitem__("double", 1) is None,
     "$.bosses[0].double"),
    (1, "AMY_AND_LIV_1's double flag written as the int 1",
     lambda p: next(t for t in p["trainers"] if t["symbol"] == "TRAINER_AMY_AND_LIV_1").__setitem__("double", 1) is None,
     "].double"),
    # fix round 3: the header's source hashes are checked against the bytes the check's own reader hashed
    (4, "trainers.json's source sha256 changed in the header",
     lambda p: p["sources"].__setitem__("ai_player/knowledge/world/trainers.json", "0" * 64) is None,
     "$.sources.ai_player/knowledge/world/trainers.json"),
]


def s_f1_pack(R):
    chapters, (packs, mds) = fresh_packs(R)

    def control():
        mod = R.mod()
        data = R.real_data()
        bad = {}
        for c in chapters:
            exp, problems = mod.expected_selection(c, data)
            got = problems + mod.check_complete(packs[c], exp)
            if got:
                bad[c] = got[:2]
        return not bad, str(bad)[:300]
    R.guarded("F3/F1 CONTROL: expected_selection + check_complete find nothing on all %d real packs (every value "
              "compared)" % len(chapters), control)

    for c, what, mutate, needle in PACK_FAULTS:
        def body(c=c, mutate=mutate, needle=needle):
            mod = R.mod()
            exp, _ = mod.expected_selection(c, R.real_data())
            p = copy.deepcopy(packs[c])
            if mutate(p) is False:
                return False, "the item to change was not found in ch%d" % c
            # compared as JSON text, because True == 1 in Python and a bool-to-int change must count as a change
            if json.dumps(p, sort_keys=True) == json.dumps(packs[c], sort_keys=True):
                return False, "the mutation changed nothing"
            got = mod.check_complete(p, exp)
            return any(needle in x and x.startswith(("WRONG pack", "MISSING pack")) for x in got), str(got)[:300]
        R.guarded("F1 FAULT (pack): ch%d %s is named (%s)" % (c, what, needle), body)

    # the first round's per-category removals, still named in words
    def pack_fault(c, name, mutate, needle):
        def body():
            mod = R.mod()
            exp, _problems = mod.expected_selection(c, R.real_data())
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


def s_f1_md(R):
    chapters, (packs, mds) = fresh_packs(R)

    def control():
        mod = R.mod()
        data = R.real_data()
        bad = {}
        for c in chapters:
            exp, _ = mod.expected_selection(c, data)
            got = mod.check_md_complete(packs[c], mds[c], exp, MD_CAP)
            if got:
                bad[c] = got[:2]
        return not bad, str(bad)[:300]
    R.guarded("F1/F2 CONTROL: check_md_complete finds nothing on every generated .md (%d; every line compared)" %
              len(chapters), control)
    for c, what, mutate, needle in MD_FAULTS:
        def body(c=c, mutate=mutate, needle=needle):
            mod = R.mod()
            exp, _ = mod.expected_selection(c, R.real_data())
            new = mutate(mds[c].split("\n"))
            if new is None:
                return False, "the line to change was not found in ch%d.md (or the edit changed nothing)" % c
            got = mod.check_md_complete(packs[c], "\n".join(new), exp, MD_CAP)
            return any(needle in x for x in got), str(got)[:300]
        R.guarded("F1 FAULT (.md): ch%d.md with %s is named (%s)" % (c, what, needle), body)


def s_crlf_packs(R):
    chapters = campaign_chapters()
    d = R.scratch("crlf_packs")
    for c in chapters:
        for x in ("json", "md"):
            to_crlf(os.path.join(R.shared["fresh"], "ch%d.%s" % (c, x)), os.path.join(d, "ch%d.%s" % (c, x)))
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("CRLF CONTROL: CRLF copies of every pack pass --check", rc == 0, (out.strip().splitlines()[-1:] or [""])[0])
    with open(os.path.join(d, "ch5.md"), "rb") as f:
        raw = f.read()
    with open(os.path.join(d, "ch5.md"), "wb") as f:
        f.write(raw.replace(b"Chapter 5 pack", b"Chapter 5 Pack", 1))
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("CRLF FAULT: a CRLF pack copy with one changed byte still fails --check naming it",
          rc == 1 and "ch5.md" in out and "ch4.md" not in out, out.strip()[-160:])


#: the hung verifier sleeps this long; the selftest kills a generator still running after VERIFY_HANG_OUTER_S
VERIFY_HANG_S = 60
VERIFY_HANG_OUTER_S = 30


def s_verify_timeout(R):
    """Fix round 3: verify_inputs' timeout. FAULT: a stand-in verify_world that never answers (it sleeps
    VERIFY_HANG_S) with --verify-timeout 2 must make the generator exit 2 naming the timeout, well before the selftest's
    own bound, writing nothing. (Before the fix the generator waited until something outside killed it.) This half needs
    no decomp clone. CONTROL (s_verify_timeout_control): the real verifier under an explicit --verify-timeout passes."""
    d = R.scratch("verify_timeout")
    fake = os.path.join(d, "hung_verify_world.py")
    with open(fake, "w", encoding="utf-8", newline="\n") as f:
        f.write("import time\ntime.sleep(%d)\n" % VERIFY_HANG_S)
    out = os.path.join(d, "out")
    t0 = time.time()
    rc, _, err = R.run([4], out, verifier=fake, extra=["--verify-timeout", "2"], timeout=VERIFY_HANG_OUTER_S)
    took = time.time() - t0
    R.arm("timeout FAULT: a verify_world that hangs (sleeps %d s) with --verify-timeout 2 -> exit 2 naming the timeout "
          "inside the selftest's %d s bound, nothing written" % (VERIFY_HANG_S, VERIFY_HANG_OUTER_S),
          rc == 2 and "did not finish within 2 s" in err and "REFUSED" in err and not listing(out),
          "exit %s after %.1f s: %s" % (rc, took, err.strip()[-200:]))


def s_verify_timeout_control(R):
    """The CONTROL half of s_verify_timeout (split from it because the real verifier needs the pinned clone, and the
    FAULT half, a stand-in verifier, does not)."""
    rc, _, err = R.run([4], R.scratch("verify_timeout_control"), extra=["--verify-timeout", "60"],
                       timeout=VERIFY_HANG_OUTER_S + 30)
    R.arm("timeout CONTROL: the real verify_world under --verify-timeout 60 passes (chapter 4 exits 0)", rc == 0,
          "exit %s: %s" % (rc, err.strip()[-200:]))


def s_bool_int(R):
    """Fix round 3: deep_diff's bool-is-not-int test. True == 1 in Python, so without it a double flag written as 1
    (or a level written as True) compares equal. FAULT: each bool/int pair gives exactly one WRONG finding. CONTROL:
    equal values of the same type give none. (The pack-level arms are in PACK_FAULTS: a double flag written as 1.)"""
    def body():
        mod = R.mod()
        missed = []
        for have, want in ((True, 1), (1, True), (False, 0), (0, False), ([True], [1]), ({"double": 1}, {"double": True})):
            out = []
            mod.deep_diff(have, want, "$.x", out)
            if len(out) != 1 or not out[0].startswith("WRONG pack $.x"):
                missed.append("%r vs %r -> %s" % (have, want, out))
        noise = []
        for v in (True, False, 1, 0, [True, 1], {"double": True, "level": 1}):
            mod.deep_diff(v, copy.deepcopy(v), "$.x", noise)
        return not missed and not noise, "missed %s; control findings %s" % (missed, noise)
    R.guarded("bool FAULT: deep_diff names True vs 1, 1 vs True, False vs 0, 0 vs False (also inside a list and a "
              "dict); CONTROL: equal values of one type give no finding", body)


def s_check(R):
    chapters = campaign_chapters()
    rc, out, err = R.run(["--all"], PACKS, extra=["--check"])
    R.arm("check CONTROL: --check on the committed packs (every chapter) exits 0", rc == 0,
          (out.strip().splitlines()[-1:] or [""])[0] + err.strip()[-160:])
    d = R.scratch("check_fault")
    for c in chapters:
        for x in ("json", "md"):
            shutil.copyfile(os.path.join(R.shared["fresh"], "ch%d.%s" % (c, x)), os.path.join(d, "ch%d.%s" % (c, x)))
    with open(os.path.join(d, "ch4.md"), "a", encoding="utf-8", newline="\n") as f:
        f.write("hand edit\n")
    rc, out, _ = R.run(["--all"], d, extra=["--check"])
    R.arm("check FAULT: an edited pack copy makes --check exit 1 naming it", rc == 1 and "ch4.md" in out)


# ---------------------------------------------------------------- the WARN path (this file's own exit)
#: one arm of each clone-free scenario, by the start of its name: a WARN child must print each of these as PASS
WARN_CHILD_MUST_PASS = ("pin FAULT", "F2 FAULT: a decomp folder that is no pinned clone",
                        "W3 FAULT: JOSH's object removed", "areamap FAULT", "F3 FAULT (input, in-process)",
                        "W3 mapping CONTROL", "F1 CONTROL: a fixture", "routekeys CONTROL", "timeout FAULT",
                        "bool FAULT")
#: arms that need the clone: a WARN child must print none of them (it SKIPPED their scenarios)
WARN_CHILD_MUST_SKIP = ("all CONTROL", "timeout CONTROL", "W3 FAULT: the real run", "check CONTROL",
                        "F2 FAULT (input)", "empty FAULT")


def run_self(R, d, name, env_decomp=None, extra=(), gen=None):
    """This file as a child (--no-warn-arms, so it does not recurse), its own work folder under `d`:
    (exit code, stdout). env_decomp=None leaves POKEBOT_DECOMP as this process has it; a path sets it."""
    env = dict(os.environ)
    if env_decomp is not None:
        env["POKEBOT_DECOMP"] = env_decomp
    cmd = [sys.executable, os.path.abspath(__file__), "--generator", gen or R.gen, "--work", os.path.join(d, name),
           "--no-warn-arms"] + list(extra)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, timeout=WARN_CHILD_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, "(killed after %d s: the child did not return)" % WARN_CHILD_TIMEOUT_S
    return p.returncode, p.stdout


def warn_shape(out):
    """'' when a child's output is a proper WARN run (the WARN line, no FAIL, every clone-free arm PASS, no real-data
    arm printed), else what is wrong."""
    lines = out.splitlines()
    bad = []
    if not any(ln.startswith("WARN: " + WARN_TEXT) for ln in lines):
        bad.append("no 'WARN: %s' line" % WARN_TEXT)
    bad += ["a FAIL: " + ln[:120] for ln in lines if ln.startswith("FAIL")][:2]
    bad += ["no PASS of '%s'" % a for a in WARN_CHILD_MUST_PASS if not any(ln.startswith("PASS  " + a) for ln in lines)]
    bad += ["a real-data arm ran: '%s'" % a for a in WARN_CHILD_MUST_SKIP
            if any(ln[6:].startswith(a) for ln in lines if ln[:4] in ("PASS", "FAIL"))]
    return "; ".join(bad)


def s_warn_path(R):
    """This file's own WARN path, run as children against an EMPTY folder (no clone). WHY in-file: run_gates counts a
    4 from this gate as "ran but could not verify", so the line between 4 (skipped, nothing failed), 1 (something that
    ran failed) and 0 must itself be tested, or the third state silently widens into a pass. Clone-free, so it runs on
    every machine."""
    d = R.scratch("warn_path")
    empty = os.path.join(d, "empty_decomp")
    os.makedirs(empty)
    with open(R.gen, encoding="utf-8") as f:
        src = f.read()
    old, new = MUTANTS["deep_diff bool-is-not-int clause"]
    broken = os.path.join(d, "make_chapter_pack.py")
    with open(broken, "w", encoding="utf-8", newline="\n") as f:
        f.write(src.replace(old, new))
    jobs = {"env": dict(name="env_empty", env_decomp=empty),
            "flag": dict(name="flag_empty", extra=["--decomp", empty]),
            # a git checkout at ANOTHER commit (this repo, read only): a clone, but not at the pin
            "commit": dict(name="wrong_commit", env_decomp=REPO),
            "fail": dict(name="fail_empty", env_decomp=empty, gen=broken)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        futs = {k: ex.submit(run_self, R, d, **v) for k, v in jobs.items()}
        got = {k: f.result() for k, f in futs.items()}
    rc, out = got["env"]
    why = warn_shape(out)
    R.arm("WARN FAULT: env POKEBOT_DECOMP at an empty folder -> exit 4, every clone-free arm PASS, no real-data arm run",
          rc == WARN_EXIT and not why, "exit %s: %s" % (rc, why or out.strip()[-160:]))
    rc, out = got["flag"]
    why = warn_shape(out)
    R.arm("WARN FAULT: --decomp at an empty folder (it wins over the environment) -> exit 4 the same way",
          rc == WARN_EXIT and not why, "exit %s: %s" % (rc, why or out.strip()[-160:]))
    rc, out = got["commit"]
    why = warn_shape(out)
    R.arm("WARN FAULT: POKEBOT_DECOMP at a git checkout whose HEAD is not tools/decomp.pin (this repo) -> exit 4 the "
          "same way", rc == WARN_EXIT and not why, "exit %s: %s" % (rc, why or out.strip()[-160:]))
    rc, out = got["fail"]
    R.arm("WARN FAULT: a clone-free arm failing (deep_diff's bool clause deleted in a generator copy) with no clone -> "
          "exit 1, never 4", src.count(old) == 1 and rc == 1 and any(ln.startswith("FAIL  bool FAULT")
                                                                     for ln in out.splitlines()),
          "exit %s: %s" % (rc, out.strip()[-200:]))


def s_warn_explicit_decomp(R):
    """CONTROL of the WARN path (real-data: it needs the clone). --decomp at the real clone must win over an EMPTY
    POKEBOT_DECOMP for the WHOLE child run: the child finds the clone, hands it to every generator run (through
    POKEBOT_DECOMP, which verify_world reads), runs every arm and exits 0. Without that hand-off the generator runs
    would read the empty folder and fail."""
    d = R.scratch("warn_control")
    empty = os.path.join(d, "empty_decomp")
    os.makedirs(empty)
    rc, out = run_self(R, d, "flag_real", env_decomp=empty, extra=["--decomp", R.shared["clone"]])
    lines = out.splitlines()
    ran = [a for a in WARN_CHILD_MUST_SKIP if any(ln.startswith("PASS  " + a) for ln in lines)]
    R.arm("WARN CONTROL: --decomp at the real clone with POKEBOT_DECOMP empty -> exit 0, the real-data arms run, no SKIP",
          rc == 0 and ran == list(WARN_CHILD_MUST_SKIP) and not any(ln.startswith(("SKIP", "WARN")) for ln in lines),
          "exit %s, real-data arms seen %s: %s" % (rc, ran, out.strip()[-160:]))


def all_arms(R, clone=True, warn_arms=True):
    """Run the scenarios; return the names of those SKIPPED. `clone` False (no pinned decomp clone here): only the
    clone-free scenarios run, and every other one is returned as skipped (main then exits 4 unless an arm failed).
    `warn_arms` False (a child of the WARN arms, or a mutant run): the WARN arms themselves are left out."""
    free = [s_pin, s_no_clone, s_w3_world, s_guards_inproc, s_input_problems, s_mapping, s_f1_fixtures,
            s_routekey_source, s_verify_timeout, s_bool_int] + ([s_warn_path] if warn_arms else [])
    real = [s_fresh, s_again, s_hash_fault, s_crlf_input, s_empty, s_size] + \
           [omission_scenario(i) for i in range(len(OMISSIONS))] + \
           [s_roxanne_two_files, s_w3_world_real, s_verify_timeout_control] + [plant_scenario(n) for n in PLANTS] + \
           ([s_warn_explicit_decomp] if warn_arms else [])
    phase2 = [s_w3_control, s_header_arms, s_f2_verified, s_f2_partial, s_f2_size, s_f1_pack, s_f1_md,
              s_crlf_packs, s_check, s_wild_avail]
    if not clone:
        parallel(R, free)
        return [fn.__name__ for fn in real + phase2]
    parallel(R, real + free)
    if not R.shared.get("fresh"):
        return []
    parallel(R, phase2)
    return []


# ---------------------------------------------------------------- mutants
def run_mutants(gen, work, jobs):
    """Each mutant (a guard's CALL deleted, or one of the verifies' 24 + 15) in a scratch copy; the selftest against
    that copy must FAIL (exit 1). Run `jobs` at a time; each copy has its own scratch folder."""
    with open(gen, encoding="utf-8") as f:
        src = f.read()
    todo, rows = [], []
    for group, table in (("guard", MUTANTS), ("verify", VERIFIER_MUTANTS), ("reverify", REVERIFY_MUTANTS)):
        for name, (old, new) in table.items():
            n = src.count(old)
            if n != 1 or old == new:
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
        # --no-warn-arms: a mutant is a defect in the GENERATOR; the WARN arms test this file's own exit and would
        # only double each mutant's run
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "--generator", path,
                            "--work", os.path.join(d, "run"), "--skip-committed", "--no-warn-arms"],
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
    ap.add_argument("--jobs", type=int, default=6, help="mutants run at a time (default 6)")
    ap.add_argument("--skip-committed", action="store_true",
                    help="(used by --mutants) leave out the arms that compare with the committed packs")
    ap.add_argument("--decomp", default=None,
                    help="the pinned decomp clone (default: env POKEBOT_DECOMP, else ../_decomp/pokeemerald)")
    ap.add_argument("--no-warn-arms", action="store_true",
                    help="(used by the WARN arms and --mutants) leave out the arms that run this file as a child")
    args = ap.parse_args(argv)
    t0 = time.time()
    # the clone is looked for FIRST: without it the real-data scenarios are skipped and the exit is WARN (4), not FAIL
    clone, no_clone_why = decomp_clone(args.decomp)
    if clone and args.decomp:
        # every generator run (and verify_world inside it) must read the clone this run found, not its own default
        os.environ["POKEBOT_DECOMP"] = os.path.abspath(clone)
    tmp = None
    work = args.work
    if work is None:
        tmp = work = tempfile.mkdtemp(prefix="chapter_pack_selftest_")
    os.makedirs(work, exist_ok=True)
    R = Runner(os.path.abspath(args.generator), os.path.abspath(work))
    R.shared["clone"] = clone
    skipped = []
    try:
        if args.skip_committed and clone:
            # A mutant's output differs from the committed packs by construction (its own sha256 is in the header),
            # so --check would "catch" every mutant vacuously. The mutant's own output stands in for the committed
            # packs instead, and a mutant must be caught by an arm that tests BEHAVIOUR.
            global PACKS
            PACKS = R.scratch("stand-in-packs")
            R.run(["--all"], PACKS)
        skipped = all_arms(R, clone=bool(clone), warn_arms=not args.no_warn_arms)
        if args.mutants:
            if clone:
                for name, ok, detail in run_mutants(R.gen, R.work, args.jobs):
                    R.arm("MUTANT %s is caught" % name, ok, detail)
            else:
                skipped.append("--mutants")  # each mutant is judged by the real-data arms
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in R.results:
        detail = " / ".join(str(detail).split("\n"))
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  -- " + detail[:300]) if detail else ""))
    for name in skipped:
        print("SKIP  %s (needs the pinned decomp clone)" % name)
    bad = [r for r in R.results if not r[1]]
    print("SELFTEST chapter_pack: %d/%d arms PASS%s (%.1f s)" % (
        len(R.results) - len(bad), len(R.results),
        ", %d scenarios SKIPPED" % len(skipped) if skipped else "", time.time() - t0))
    if bad:
        return 1  # an arm that RAN failed: a skip never turns that into a WARN
    if skipped:
        print("no clone: %s" % no_clone_why)
        print("WARN: " + WARN_TEXT)
        return WARN_EXIT
    return 0


if __name__ == "__main__":
    sys.exit(main())
