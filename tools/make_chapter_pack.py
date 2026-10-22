#!/usr/bin/env python3
"""A5 chapter packs (spec S3-4): one chapter's static world, generated from KB1 + KB2, for a reader and for W7.

    py -3.12 tools/make_chapter_pack.py 4              # writes PROJECT KNOWLEDGE/chapter-packs/ch4.json + ch4.md
    py -3.12 tools/make_chapter_pack.py --all          # every chapter campaign.json has (1-24 today)
    py -3.12 tools/make_chapter_pack.py --all --check  # regenerates in memory; exit 1 if a committed pack differs

INTENT: before a chapter is built or debugged, an agent (and W7's adversarial agent) needs that chapter's world on one
page: the maps it happens on and one ring of neighbours, the links between them, every trainer standing there, the
chapter's bosses with their teams, the wild encounters, who can learn a needed HM, and a short list of LOAD-BEARING
CLAIMS that a wrong fact would turn into a lost run. The chapter 3-4 recon took nine agents (about 16M tokens) to
assemble that by hand; this tool derives it from files that are already decomp-derived and verified:
  KB2 slice 1  ai_player/knowledge/world/{campaign,maps,trainers,bosses}.json   (extract_world.py, verify_world.py)
  KB1          ai_player/knowledge/seasoned/{encounters,learnsets,species}.json (extract_seasoned.py)
It READS them only and writes nothing under ai_player/.

WHAT A PACK HOLDS, FOR CHAPTER N:
  entries   the campaign.json entries with `chapter == N`, copied through an allowlist of fields (never routes,
            coordinates or step lists: L1's rule, W6; refuse_route_keys stops the run if one appears)
  maps      the entries' `area` maps, plus ONE RING of neighbours: every map an area map connects or warps to, and every
            map that connects or warps into an area map (MAP_DYNAMIC is the game's "back where you came from", no map)
  links     each area map's connections and warps, each warp classified by whether its arrival warp leads back.
            A warp to MAP_DYNAMIC has no arrival warp to read: the game sends the player to the "dynamic warp" it
            recorded. A warp records one when the player ARRIVES on a MAP_DYNAMIC warp of that map
            (field_control_avatar.c SetupWarp, at the pin), and C code records one for a secret base
            (src/secret_base.c:450; `C_RECORDED_RETURN`). So a MAP_DYNAMIC warp is `dynamic` (it leads back) when
            some maps.json warp arrives on a MAP_DYNAMIC warp of its map or the map is a secret base, and `one_way`
            otherwise: then only a script sets where it goes and no warp leads back in (the truck's three exits to
            Littleroot; W7, claim 14).
            A `one_way` warp is a ONE-WAY claim like an asymmetric one.
  trainers  every trainer battled on those maps (maps.json, joined to trainers.json) by a sighted object, a trigger
            tile, or a map script (a script battle carries a `label`, the others a `script`; script_label takes either):
            single or double, sight, party levels min..max (and the full list), species, the defeat flag NUMBER
  bosses    the bosses.json fights of the chapter's entries (full team, moves, held items: USER RULING 44 allows them);
            `area_bosses_later` names the bosses battled on these maps in a LATER chapter (information only)
  wild      KB1 encounters for the AREA maps (not the ring), normal-play rows only (availability == "normal")
  hms       each field move a chapter entry needs (needs.field_moves) and each one the chapter's badges unlock: the
            species that learn it by HM (KB1 learnsets), and which of them are met wild in this chapter
  claims    the LOAD-BEARING CLAIMS list (progress-gating flags, HM gates, double battles, one-way warps, boss teams),
            the only part handed to W7's adversarial agent
WHAT IT DOES NOT HOLD, AND SAYS SO IN ITS HEADER (so an absent section is never read as "none here"):
  - items, gifts, marts and scripted events: slice 2 (items_gifts.json, events.json) NEEDS DESIGN. maps.json already
    holds item balls and hidden items, but they are left out on purpose so the items section ships whole, never as a
    partial list that reads as "these are all the items".
  - A6's measured traps (top wall, level at first loss and at win, whiteouts): chapter_priors.json is not generated.
  - Story-event flags (setflag/setvar in scripts): slice 2's events.json. The claims' flags are badge flags, trainer
    defeat flags and campaign.json's badge gates only.
THE PACK IS GENERATED AND THE DECOMP WINS: its header says so, and carries the sha256 of every source file, the
generator's own sha256, the decomp pin, and the record of the input verification (below), so a stale pack is visible.
The .json holds each sha256 in full; the .md shows their first 16 hex digits (MD_HASH_CHARS), which pays for the
verification line under the cap. Hashes are taken over the file's bytes with CRLF normalised to LF, because this PC
checks text out with CRLF (core.autocrlf) and another may not; `--check` reads the committed packs the same way.
(`.gitattributes` also pins the packs to LF.)

THE DIVISION OF LABOUR (fix round 2, 2026-10-22). Two different failures, two different checkers:
  1. THE INPUTS ARE WRONG OR INCOMPLETE (an extractor dropped a double battle, a badge, a connection on both sides, an
     ordinary trainer, a warp). This tool cannot see that: the fact is absent from every file it reads, so any reading
     of those files agrees with itself. That is ai_player/gates/verify_world.py's job: it re-reads the PINNED DECOMP by
     its own regexes (it never imports the extractor). So the run starts it as a subprocess on the same world folder,
     over EVERY record (never the seeded sample), before anything is generated, and REFUSES (exit 2, nothing written)
     unless it exits 0 with `[VERIFY-WORLD] PASS: 0 mismatches (every record; ...`. A verifier that cannot run (no
     clone at the pin) is a refusal too, and so is one still running after --verify-timeout seconds (default 120;
     it takes about 1 s). The pack header's `inputs_verified` records the command, its exit code, its
     summary line and the verifier's sha256. verify_world covers the four WORLD files only; KB1's seasoned files
     (encounters, learnsets, species) are not re-verified by this run (their verifier is verify_seasoned.py).
  2. THE PACK IS WRONG AGAINST ITS INPUTS (the generator, or its input reader, dropped or changed something). That is
     this tool's own check. The check reads the input FILES again with its own loader (read_inputs_for_check, by its
     own key paths; fix round 3: until then both readings consumed the one dict load_inputs returns, so a boss level,
     a connection or a double flag corrupted inside that reader passed both, and verify_world too, since the files on
     disk were right). expected_selection is that SECOND reading, sharing no code with build_pack, and expected_pack
     builds the WHOLE pack from it a second time (every key but the pin, generator and verification header; the
     source hashes are the check's own). check_complete compares the pack with
     it VALUE BY VALUE (deep_diff: a boss mon's moves and held item, a double flag, a connection's offset, an HM's badge,
     every claim's full text and source; a bool is never equal to an int there) beside its older findings that name an
     omission in words (MISSING boss ...).
     check_md_complete then compares the .md LINE BY LINE, every line, with render_md_check's rendering of that second
     reading, at the summary level its own size measurements choose: so a boss line must hold every mon with species,
     level, types, moves and held item, a double battle must say DOUBLE, a links line must list every connection and
     warp, an HM line must name its badge, and every claim must be there in full. Never a line's start (round 1 matched
     prefixes, and 13 mutants that corrupted real output passed it). Any finding stops the run with exit 2 naming it.
     The same reading also cross-checks the inputs against each other (a second line of defence behind verify_world):
     a boss an entry names with no bosses.json row; a bosses.json `battled_on` map with no object for that boss; a badge
     won or a field move needed with no `field_move_badges` row; a connection with no connection back (all 148 at the
     pin are mirrored); a connection or warp to a map maps.json does not hold.
  Every chapter is generated and checked in memory before any file is written, so a refusal at chapter N of --all
  leaves no partial set behind.

THE 12 KB .md CAP NEVER REFUSES A CHAPTER (fix round 1, 2026-10-22). The .md is rendered in full; when that is over the
cap it is rendered again with the ORDINARY trainers (single battles) summarised per map: their count, level range and
species set, pointing to the .json for the full list. Only if that is still over, deeper levels follow one at a time
(SUMMARY_LEVELS: wild tables without rates; warps and neighbour maps counted; trainer and wild species and neighbour
trainers left to the .json). On the 2026-10-22 inputs chapters 9 and 11 use level 1, 14 level 2 and 13 level 4 (its
full page is 21,034 bytes; it ends at 11,987). The load-bearing sections stay in full at every level (the bosses and
their teams, the HM moves, every double battle, each area map's links line, the LOAD-BEARING CLAIMS), and
check_md_complete proves it line by line (above); only a page still over the cap at the deepest level makes
check_md_size stop the run.

THE GUARDS (each stops the run with exit 2 and a message naming what it found; tools/story-dev/selftest_chapter_pack.py
feeds each a broken input beside a healthy one, and its --mutants mode deletes each CALL in a scratch copy and must see
a failing arm):
  check_pins             an input whose `_source` pin differs from tools/decomp.pin (a pack mixing two decomps)
  verify_inputs          verify_world.py not exiting 0 with 0 mismatches over every record, or not finishing within
                         --verify-timeout seconds (division of labour, 1)
  read_inputs_for_check  the check's own reading of the files (division of labour, 2): what the pack is compared with
  refuse_empty_chapter   a chapter with no campaign entry (a typo'd chapter must not write an empty pack)
  refuse_route_keys      a key named x, y, route, path, steps or coords inside the chapter's campaign entries
  resolve_maps           an area map that maps.json does not hold
  join_trainer           a trainer symbol on a map that trainers.json does not hold
  script_label           a trainer object with neither `script` nor `label` (a battle that cannot be cited)
  refuse_incomplete      check_complete's and check_md_complete's findings (division of labour, 2)
  check_md_size          a rendered .md still over the cap after summarising
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
WORLD_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "world")
SEASONED_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
PIN_DEFAULT = os.path.join(REPO, "tools", "decomp.pin")
OUT_DEFAULT = os.path.join(REPO, "PROJECT KNOWLEDGE", "chapter-packs")
#: KB2's independent verifier (regex over the raw pinned decomp; it never imports the extractor). Run, never imported.
VERIFY_WORLD = os.path.join(REPO, "ai_player", "gates", "verify_world.py")
#: the only summary line that lets a pack be written: zero mismatches over EVERY record (never a seeded sample)
VERIFY_PASS = re.compile(r"^\[VERIFY-WORLD\] PASS: 0 mismatches \(every record;")
#: seconds verify_world may run before the run refuses: it takes about 1 s here, so this only ever fires on a hang
#: (a timeout is a refusal with its reason, never a wait without end)
VERIFY_TIMEOUT_S = 120
#: the pack's provenance header: check_complete copies these from the pack (the selftest's pin, hashes and F2 arms
#: check them); every other key, `sources` included (fix round 3), is re-derived from the check's own reading
PROVENANCE = ("decomp_pin", "generator", "inputs_verified")
#: hex digits of each sha256 the .md shows (the .json keeps all 64); the room pays for the verification line
MD_HASH_CHARS = 16

#: the inputs, by the repo path the header names them by (the logical name, whatever folder they were read from)
WORLD_FILES = ("campaign.json", "maps.json", "trainers.json", "bosses.json")
SEASONED_FILES = ("encounters.json", "learnsets.json", "species.json")
#: the spec's "at most ~12 KB" for the .md, in bytes (LF line ends)
MD_CAP_DEFAULT = 12 * 1024
#: W6 / L1's rule, the same set as ai_player/gates/extract_world.py ROUTE_KEYS (the selftest compares the two)
ROUTE_KEYS = ("x", "y", "route", "path", "steps", "coords")
#: the campaign-entry fields a pack copies; anything else in an entry is not carried
ENTRY_FIELDS = ("id", "chapter", "order", "area", "boss", "fights", "area_bosses", "needs", "measured")
DYNAMIC = "MAP_DYNAMIC"
#: maps whose MAP_DYNAMIC exits lead back although no maps.json warp arrives on them: C code records the way back
#: (src/secret_base.c:450 at the pin sets the dynamic warp when the player enters a secret base; the W7 verify of the
#: one-way rule, 2026-10-22). A plain prefix test on purpose: every secret base map is MAP_SECRET_BASE_*.
C_RECORDED_RETURN = ("MAP_SECRET_BASE_",)
#: maps.json trainer `source` values that are not a sighted object
SEEN_AS = {"coord_event": "trigger tile", "script": "map-script battle"}
#: the line that opens a summarised trainers section (check_md_complete reads the mode from it)
SUMMARY_MARK = "SUMMARISED to fit the cap"

ABSENT = [
    "NOT INCLUDED YET: items, gifts, marts and scripted events (spec S3-4 slice 2, items_gifts.json and events.json, "
    "NEEDS DESIGN). Item balls and hidden items exist in maps.json but are left out so the items section ships whole. "
    "An absent item, gift, mart or event list here means NOT EXTRACTED, never 'none here'.",
    "NOT INCLUDED YET: A6's measured traps (top wall, level at first loss and at win, whiteouts; source 'bot corpus'): "
    "chapter_priors.json is not generated. No measured section means NOT MEASURED, never 'no traps here'.",
    "NOT INCLUDED YET: story-event flags (setflag/setvar in map scripts; slice 2's events.json). The flags below are "
    "badge flags, trainer defeat flags and campaign.json badge gates only.",
]
GENERATED = ("GENERATED by tools/make_chapter_pack.py from KB1 and KB2 (both decomp-derived). This pack is NOT a "
             "source of truth: where it and the decomp (the pin below) disagree, THE DECOMP WINS. Regenerate, never "
             "hand-edit.")


class PackError(Exception):
    """A guard refused: the message names what it found."""


# ---------------------------------------------------------------- inputs
def sha256_lf(path):
    """sha256 of the file's bytes with CRLF normalised to LF (a CRLF checkout must not change a pack's header)."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def load_inputs(world_dir, seasoned_dir):
    """({logical name: parsed json}, {logical name: sha256}) for the seven inputs."""
    data, hashes = {}, {}
    for folder, rel, names in ((world_dir, "ai_player/knowledge/world/", WORLD_FILES),
                               (seasoned_dir, "ai_player/knowledge/seasoned/", SEASONED_FILES)):
        for name in names:
            path = os.path.join(folder, name)
            with open(path, encoding="utf-8") as f:
                data[rel + name] = json.load(f)
            hashes[rel + name] = sha256_lf(path)
    return data, hashes


def read_pin(pin_path):
    with open(pin_path, encoding="utf-8") as f:
        return f.read().strip()


def check_pins(data, pin):
    """Every input must name the pinned commit in its `_source` (pret/pokeemerald@<sha>): a pack built from files of two
    different decomps would cite lines that do not exist in either."""
    bad = []
    for name, d in sorted(data.items()):
        src = d.get("_source", "") if isinstance(d, dict) else ""
        if src.rsplit("@", 1)[-1] != pin:
            bad.append("%s (_source %r)" % (name, src))
    if bad:
        raise PackError("input pin differs from tools/decomp.pin %s: %s" % (pin, "; ".join(bad)))


def repo_rel(path, root=REPO):
    """`path` relative to `root` with forward slashes, or absolute when it lies outside it (a scratch world)."""
    p = os.path.abspath(path)
    try:
        rel = os.path.relpath(p, root)
    except ValueError:  # another drive
        return p.replace("\\", "/")
    return p.replace("\\", "/") if rel.startswith("..") else rel.replace("\\", "/")


def verify_inputs(world_dir, decomp=None, verifier=VERIFY_WORLD, timeout=None):
    """Run ai_player/gates/verify_world.py over EVERY record of the four world files this run reads, and stop the run
    (PackError, so exit 2 and nothing written) unless it exits 0 with a `PASS: 0 mismatches (every record; ...)` line.
    WHY: this tool cannot see a fact missing from its own inputs (a double battle, a badge or a connection dropped by
    the extractor is simply absent from every file it reads), while verify_world re-reads the pinned decomp by its own
    regexes and reports exactly such omissions. `--knowledge` points its W1 withheld-field scan at the same folder, so
    the result line depends only on these inputs. Returns the record the pack header carries. (`verifier` is a path
    only so that a scratch copy of this file, which has no repo around it, can name the real one: the selftest's.
    The paths the record shows are relative to the repo the verifier lives in, <repo>/ai_player/gates/.)
    A verifier that has not finished after `timeout` seconds (default VERIFY_TIMEOUT_S) is killed and the run refuses
    naming the timeout (fix round 3: without it a hung verifier hung the generator until something outside killed it,
    and the project's rule is that every wait is bounded)."""
    timeout = VERIFY_TIMEOUT_S if timeout is None else timeout
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(verifier))))
    cmd = [sys.executable, verifier, "--data", world_dir, "--knowledge", world_dir]
    shown = "py -3.12 %s --data %s --knowledge %s" % (repo_rel(verifier, root), repo_rel(world_dir, root),
                                                      repo_rel(world_dir, root))
    if decomp:
        cmd += ["--decomp", decomp]
        shown += " --decomp %s" % repo_rel(decomp, root)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise PackError("ai_player/gates/verify_world.py did not finish within %g s (`%s`): it was stopped and the run "
                        "refuses rather than wait (the inputs are NOT verified; --verify-timeout raises the bound)" % (
                            timeout, shown)) from None
    lines = (p.stdout or "").strip().splitlines()
    summary = next((ln for ln in reversed(lines) if ln.startswith("[VERIFY-WORLD]")), "")
    if p.returncode != 0 or not VERIFY_PASS.match(summary):
        bad = [ln for ln in lines if ln.startswith("MISMATCH")]
        tail = summary or ((p.stderr or "").strip().splitlines() or ["no output"])[-1]
        raise PackError("the inputs did not pass ai_player/gates/verify_world.py (exit %d; `%s`): %s%s" % (
            p.returncode, shown, tail, ("; " + " | ".join(bad[:8])) if bad else ""))
    return {"by": repo_rel(verifier, root), "verifier_sha256": sha256_lf(verifier), "command": shown,
            "exit": p.returncode, "result": summary}


def campaign_chapters(data):
    """Every chapter number campaign.json has, sorted (what --all generates)."""
    return sorted({e["chapter"] for e in data["ai_player/knowledge/world/campaign.json"]["entries"]})


# ---------------------------------------------------------------- guards on the campaign
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


def refuse_route_keys(entries):
    """L1's rule (W6): a manifest must never become the bot's script, so no route key may ride into a pack from it."""
    hits = []
    for e in entries:
        hits += route_keys(e, "entry %s" % e.get("id"))
    if hits:
        raise PackError("campaign.json route keys would leak into the pack: %s" % hits[:5])


def refuse_empty_chapter(entries, chapter):
    if not entries:
        raise PackError("chapter %s has no campaign.json entries (no pack written)" % chapter)


def resolve_maps(names, maps_by_id):
    """Campaign `area` names are map ids without the MAP_ prefix; every one must be a maps.json map."""
    missing = [n for n in names if "MAP_" + n not in maps_by_id]
    if missing:
        raise PackError("area maps not in maps.json: %s" % ", ".join(missing))
    return ["MAP_" + n for n in names]


def join_trainer(symbol, trainers_by_symbol, map_id):
    if symbol not in trainers_by_symbol:
        raise PackError("trainer %s on %s is not in trainers.json" % (symbol, map_id))
    return trainers_by_symbol[symbol]


def script_label(obj, map_id):
    """The script a trainer battle runs from. maps.json gives a sighted object and a trigger tile a `script` (the
    object's or coord_event's script) and a map-script battle (Wallace; the Space Center's Maxie, Tabitha and three
    grunts) a `label` (the scripts.inc label holding its trainerbattle line) plus a `ref`. The first build read only
    `script` and crashed on chapters 19 and 24. A battle with neither cannot be cited, so the run stops naming it."""
    for key in ("script", "label"):
        if obj.get(key):
            return obj[key]
    raise PackError("a trainer object on %s has neither `script` nor `label` (keys %s, trainers %s)" % (
        map_id, sorted(obj), obj.get("trainers")))


def refuse_incomplete(findings, chapter):
    """check_complete / check_md_complete findings stop the run: a pack that silently drops a trainer, a boss or a link
    is worse than no pack, because the reader stops looking."""
    if findings:
        raise PackError("ch%s pack is INCOMPLETE or WRONG against the inputs (%d finding%s): %s" % (
            chapter, len(findings), "" if len(findings) == 1 else "s", " | ".join(findings[:12])))


def check_md_size(text, cap):
    size = len(text.encode("utf-8"))
    if size > cap:
        raise PackError("the .md is %d bytes, over the %d-byte cap even with the ordinary trainers summarised" % (
            size, cap))
    return size


# ---------------------------------------------------------------- derivations
def short(sym):
    for p in ("MAP_", "SPECIES_", "MOVE_", "ITEM_", "TRAINER_"):
        if sym and sym.startswith(p):
            return sym[len(p):]
    return sym


def ring(area_ids, maps_by_id):
    """One ring of neighbours: maps an area map connects/warps to, and maps that connect/warp into an area map."""
    area = set(area_ids)
    out = set()
    for mid in area_ids:
        m = maps_by_id[mid]
        out.update(c["map"] for c in m["connections"])
        out.update(w["dest_map"] for w in m["warps"])
    for mid, m in maps_by_id.items():
        if mid in area:
            continue
        if any(c["map"] in area for c in m["connections"]) or any(w["dest_map"] in area for w in m["warps"]):
            out.add(mid)
    out.discard(DYNAMIC)
    # a destination maps.json does not hold has no row to show; expected_selection reports it and stops the run
    return sorted((out - area) & set(maps_by_id))


def dynamic_origins(src_id, maps_by_id):
    """The maps whose warps ARRIVE on a MAP_DYNAMIC warp of `src_id`: the only arrivals that make a MAP_DYNAMIC exit
    of `src_id` lead back. WHY: a MAP_DYNAMIC warp has no destination in the map data; the game sends the player to
    the dynamic warp it recorded, and SetupWarp (field_control_avatar.c, at the pin) records one only when the player
    warps onto a map's MAP_DYNAMIC warp. With no such arrival the destination is whatever a script set (the truck's
    `setdynamicwarp MAP_LITTLEROOT_TOWN`), and no warp leads back in: W7 found ch1 calling the truck's exits
    reciprocal because the old rule called every MAP_DYNAMIC warp `dynamic` unchecked."""
    own = maps_by_id[src_id]["warps"]
    out = set()
    for mid, m in maps_by_id.items():
        for w in m["warps"]:
            k = w["dest_warp_id"]
            if w["dest_map"] == src_id and isinstance(k, int) and 0 <= k < len(own) and own[k]["dest_map"] == DYNAMIC:
                out.add(mid)
    return sorted(out)


def classify_warp(src_id, warp, maps_by_id):
    dest = warp["dest_map"]
    if dest == DYNAMIC:
        if not dynamic_origins(src_id, maps_by_id) and not src_id.startswith(C_RECORDED_RETURN):
            return "one_way", ("ONE-WAY: no maps.json warp arrives on a MAP_DYNAMIC warp of %s, so no warp records a "
                               "way back (a script sets this destination) and no warp leads back in" % short(src_id))
        return "dynamic", "MAP_DYNAMIC: returns to the map the player came from"
    if dest not in maps_by_id:
        return "unknown", "destination is not a maps.json map"
    dw = maps_by_id[dest]["warps"]
    k = warp["dest_warp_id"]
    if not isinstance(k, int) or k >= len(dw):
        return "asymmetric", "arrival warp %s does not exist on %s (%d warps)" % (k, short(dest), len(dw))
    back = dw[k]["dest_map"]
    if back in (src_id, DYNAMIC):
        return "two_way", None
    return "asymmetric", "arrival warp %d on %s leads to %s, not back" % (k, short(dest), short(back))


def links(area_ids, maps_by_id):
    """Connections (with whether the other side connects back) and warps grouped by destination, per area map, plus
    the warps INTO an area map from a ring map, classified the same way."""
    out = []
    area = set(area_ids)
    for mid in area_ids:
        m = maps_by_id[mid]
        conns = []
        for c in m["connections"]:
            back = any(cc["map"] == mid for cc in maps_by_id.get(c["map"], {}).get("connections", []))
            conns.append({"dir": c["dir"], "map": c["map"], "offset": c["offset"], "connects_back": back})
        warps = []
        for i, w in enumerate(m["warps"]):
            kind, why = classify_warp(mid, w, maps_by_id)
            warps.append({"warp": i, "x": w["x"], "y": w["y"], "dest_map": w["dest_map"],
                          "dest_warp_id": w["dest_warp_id"], "kind": kind, "why": why})
        out.append({"map": mid, "connections": conns, "warps": warps})
    incoming = []
    for sid, m in sorted(maps_by_id.items()):
        if sid in area:
            continue
        for i, w in enumerate(m["warps"]):
            if w["dest_map"] in area:
                kind, why = classify_warp(sid, w, maps_by_id)
                incoming.append({"from": sid, "warp": i, "dest_map": w["dest_map"],
                                 "dest_warp_id": w["dest_warp_id"], "kind": kind, "why": why})
    return out, incoming


def trainers_on(map_ids, area_ids, maps_by_id, trainers_by_symbol):
    """Every trainer battled by an object, a trigger or a map script on these maps, deduplicated by symbol, with each
    sighting."""
    area = set(area_ids)
    by_sym = {}
    for mid in map_ids:
        for obj in maps_by_id[mid]["trainers"]:
            for sym in obj["trainers"]:
                t = join_trainer(sym, trainers_by_symbol, mid)
                rec = by_sym.get(sym)
                if rec is None:
                    levels = [p["level"] for p in t["party"]]
                    rec = by_sym[sym] = {
                        "symbol": sym, "id": t["id"], "name": t["name"], "class": t["class_name"],
                        "double": t["double"], "flag": t["flag"], "levels": levels,
                        "level_min": min(levels) if levels else None, "level_max": max(levels) if levels else None,
                        "species": [p["species"] for p in t["party"]], "ref": t["ref"],
                        "in_area": False, "seen": []}
                rec["in_area"] = rec["in_area"] or mid in area
                seen = {"map": mid, "source": obj["source"], "script": script_label(obj, mid)}
                for k in ("trainer_type", "sight", "x", "y", "ref"):
                    if k in obj:
                        seen[k] = obj[k]
                rec["seen"].append(seen)
    return sorted(by_sym.values(), key=lambda r: (not r["in_area"], r["seen"][0]["map"], r["symbol"]))


def wild(area_ids, encounters, species_names):
    rows = []
    for e in encounters["maps"]:
        if e.get("map") not in area_ids or e.get("availability") != "normal":
            continue
        for method, tab in sorted(e["methods"].items()):
            rar = tab.get("rarity") or {}
            mons = [{"species": s, "name": species_names.get(s, short(s)), "chance_pct": r["chance_pct"],
                     "min_level": r["min_level"], "max_level": r["max_level"]}
                    for s, r in sorted(rar.items(), key=lambda kv: (-kv[1]["chance_pct"], kv[0]))]
            rows.append({"map": e["map"], "method": method, "encounter_rate": tab.get("encounter_rate"),
                         "requires": e.get("requires"),
                         "condition": (e.get("conditions") or {}).get(method), "species": mons})
    return rows


def hm_learners(move, learnsets):
    """Species that learn `move` by TM/HM (KB1 learnsets tm_hm), the HM number, sorted by species id."""
    hm, out = None, []
    for s in learnsets["species"]:
        for t in s.get("tm_hm", []):
            if t["move"] == move:
                out.append(s["symbol"])
                hm = hm or t["tm"]
    return hm, out


def build_pack(chapter, data, hashes, pin, generator_sha, verified):
    camp = data["ai_player/knowledge/world/campaign.json"]
    maps = data["ai_player/knowledge/world/maps.json"]
    trainers = data["ai_player/knowledge/world/trainers.json"]
    bosses = data["ai_player/knowledge/world/bosses.json"]
    enc = data["ai_player/knowledge/seasoned/encounters.json"]
    learn = data["ai_player/knowledge/seasoned/learnsets.json"]
    species = data["ai_player/knowledge/seasoned/species.json"]

    raw = [e for e in camp["entries"] if e.get("chapter") == chapter]
    refuse_empty_chapter(raw, chapter)
    refuse_route_keys(raw)
    entries = [{k: e[k] for k in ENTRY_FIELDS if k in e} for e in raw]

    maps_by_id = {m["id"]: m for m in maps["maps"]}
    trainers_by_symbol = {t["symbol"]: t for t in trainers["trainers"]}
    names = {s["symbol"]: s["name"] for s in species["species"]}

    area_ids = []
    for e in entries:
        for mid in resolve_maps(e["area"], maps_by_id):
            if mid not in area_ids:
                area_ids.append(mid)
    ring_ids = ring(area_ids, maps_by_id)

    def map_row(mid, role):
        m = maps_by_id[mid]
        return {"id": mid, "role": role, "name": m["name"], "map_type": m["map_type"],
                "requires_flash": m["requires_flash"], "allow_cycling": m["allow_cycling"],
                "allow_escaping": m["allow_escaping"], "allow_running": m["allow_running"]}

    link_rows, incoming = links(area_ids, maps_by_id)
    trs = trainers_on(area_ids + ring_ids, area_ids, maps_by_id, trainers_by_symbol)

    fights = []
    for e in entries:
        for f in e.get("fights") or []:
            if f not in fights:
                fights.append(f)
    later = []
    for e in entries:
        for f in e.get("area_bosses") or []:
            if f not in fights and f not in later:
                later.append(f)
    boss_rows = [b for b in bosses["bosses"] if b["fight"] in fights]
    boss_rows.sort(key=lambda b: (fights.index(b["fight"]), b["id"]))
    later_rows = []
    for f in later:
        variants = [b for b in bosses["bosses"] if b["fight"] == f]
        if variants:
            later_rows.append({"fight": f, "role": variants[0]["role"], "entry": variants[0]["entry"],
                               "ids": [b["id"] for b in variants],
                               "level_max": max(p["level"] for b in variants for p in b["party"])})
    wild_rows = wild(area_ids, enc, names)
    wild_species = sorted({m["species"] for r in wild_rows for m in r["species"]})

    fmb = {r["move"]: r for r in camp["field_move_badges"]}
    badges_won = [b["badge"] for b in boss_rows if b.get("badge")]
    hm_moves = []
    for e in entries:
        for fm in e["needs"].get("field_moves") or []:
            hm_moves.append((fm["move"], "needed by %s" % e["id"]))
    won_ids = {b["id"] for b in badges_won}
    for r in camp["field_move_badges"]:
        if r["badge"] in won_ids:
            hm_moves.append((r["move"], "unlocked by %s, won this chapter" % r["badge"]))
    hms = []
    for move, why in hm_moves:
        hm, who = hm_learners("MOVE_" + move, learn)
        hms.append({"move": move, "why": why, "hm": hm, "badge": fmb.get(move, {}).get("badge"),
                    "badge_ref": fmb.get(move, {}).get("ref"), "learners_count": len(who), "learners": who,
                    "learners_met_wild_here": [s for s in who if s in wild_species]})

    pack = {
        "_generated": GENERATED,
        "_absent": ABSENT,
        "chapter": chapter,
        "decomp_pin": pin,
        "generator": {"path": "tools/make_chapter_pack.py", "sha256": generator_sha},
        "sources": dict(sorted(hashes.items())),
        "inputs_verified": verified,
        "entries": entries,
        "maps": [map_row(m, "area") for m in area_ids] + [map_row(m, "neighbour") for m in ring_ids],
        "links": link_rows,
        "warps_in": incoming,
        "trainers": trs,
        "bosses": boss_rows,
        "area_bosses_later": later_rows,
        "wild": wild_rows,
        "hms": hms,
    }
    pack["claims"] = claims(pack, badges_won, maps_by_id)
    return pack


def claims(pack, badges_won, maps_by_id):
    """The LOAD-BEARING CLAIMS: facts that would cost a run if wrong. Each names its source so W7 can refute it."""
    out = []
    for b in pack["bosses"]:
        team = ", ".join("%s Lv%d%s" % (short(p["species"]), p["level"],
                                        (" @" + short(p["held_item"])) if p.get("held_item") else "")
                         for p in b["party"])
        out.append(("boss_team", "%s (%s, %s) %s battle: %s" % (
            b["fight"], short(b["id"]), b["role"], "DOUBLE" if b["double"] else "single", team), b["ref"]))
    for b in pack["bosses"]:
        t = next((t for t in pack["trainers"] if t["symbol"] == b["id"]), None)
        if t:
            out.append(("progress_flag", "%s's defeat flag is number %d (TRAINER_FLAGS_START + %d)" % (
                short(b["id"]), t["flag"], t["id"]), t["ref"]))
    for bd in badges_won:
        out.append(("progress_flag", "the chapter's boss sets %s (%s)" % (bd["flag"], bd["id"]), bd["ref"]))
    for e in pack["entries"]:
        n = e["needs"]
        for bd in n.get("badges") or []:
            out.append(("progress_flag", "%s needs %s" % (e["id"], bd), (n.get("badge_refs") or {}).get(bd)))
        for g in n.get("badge_gates") or []:
            out.append(("progress_flag", "%s badge gate: %s" % (e["id"], json.dumps(g, sort_keys=True)), None))
        for fm in n.get("field_moves") or []:
            out.append(("hm_gate", "%s needs field move %s (badge %s)" % (e["id"], fm["move"], fm.get("badge")),
                        fm.get("ref")))
        if n.get("double_battle") or (n.get("party_min") or 1) > 1:
            out.append(("double_battle", "%s: party_min %s (%s)" % (e["id"], n.get("party_min"),
                                                                     n.get("party_min_basis")), n.get("party_min_ref")))
    for h in pack["hms"]:
        out.append(("hm_gate", "%s (%s) usable outside battle only with %s; %d species learn it, met wild here: %s" % (
            h["move"], h["hm"], h["badge"], h["learners_count"],
            ", ".join(short(s) for s in h["learners_met_wild_here"]) or "none"), h["badge_ref"]))
    for m in pack["maps"]:
        if m["role"] == "area" and m["requires_flash"]:
            out.append(("hm_gate", "%s requires Flash (dark map)" % short(m["id"]), "maps.json requires_flash"))
    for t in pack["trainers"]:
        if t["in_area"] and t["double"]:
            out.append(("double_battle", "%s is a DOUBLE battle (%s)" % (short(t["symbol"]), t["class"]), t["ref"]))
    by_trigger = {}
    for t in pack["trainers"]:
        trig = tuple(sorted({s["script"] for s in t["seen"] if s["source"] == "coord_event"}))
        if t["in_area"] and trig:
            by_trigger.setdefault(trig, []).append(short(t["symbol"]))
    for trig, syms in by_trigger.items():
        out.append(("scripted_battle", "%s can be started by a trigger tile (%s); the trigger's var condition is NOT "
                                       "modelled here" % (" / ".join(syms), ", ".join(trig)), "maps.json coord_events"))
    n_warps = 0
    for row in pack["links"]:
        for w in row["warps"]:
            n_warps += 1
            if w["kind"] in ("asymmetric", "unknown", "one_way"):
                out.append(("one_way_warp", "%s warp %d -> %s: %s" % (short(row["map"]), w["warp"],
                                                                      short(w["dest_map"]), w["why"]), "maps.json warps"))
        for c in row["connections"]:
            if not c["connects_back"]:
                out.append(("one_way_warp", "%s connects %s to %s, which has no connection back" % (
                    short(row["map"]), c["dir"], short(c["map"])), "maps.json connections"))
    for w in pack["warps_in"]:
        n_warps += 1
        if w["kind"] in ("asymmetric", "unknown", "one_way"):
            out.append(("one_way_warp", "%s warp %d -> %s: %s" % (short(w["from"]), w["warp"], short(w["dest_map"]),
                                                                  w["why"]), "maps.json warps"))
    if not any(c[0] == "one_way_warp" for c in out):
        out.append(("one_way_warp", "none of the %d warps touching the area maps is one-way by warp data (ledges, "
                                    "holes and scripted movement are NOT modelled)" % n_warps, "maps.json warps"))
    return [{"n": i + 1, "kind": k, "claim": c, "source": s} for i, (k, c, s) in enumerate(out)]


# ---------------------------------------------------------------- the independent completeness check
def read_inputs_for_check(world_dir, seasoned_dir):
    """The CHECKING side's own loader (fix round 3, 2026-10-22): it opens the seven input files itself, parses their
    bytes and hashes those same bytes, then hands them to check_fields. It calls neither load_inputs nor sha256_lf.
    WHY: up to round 2 both readings consumed the ONE dict load_inputs returned, so a defect inside that reader (a boss
    level off by one, a dropped connection, a double battle read as single: the round-2 re-verify planted all three)
    reached the written packs at exit 0. The files on disk stayed right, so verify_world passed too, and the pack was
    checked only against the corrupted dict, never against the files whose sha256 its header records. A check that
    shares its input path with the thing it checks is not a check (02-ARCHITECTURE). Reading the files a second time
    costs about 0.1 s a run."""
    parsed, digests = {}, {}
    for folder, prefix, names in (
            (world_dir, "ai_player/knowledge/world/", ("campaign.json", "maps.json", "trainers.json", "bosses.json")),
            (seasoned_dir, "ai_player/knowledge/seasoned/", ("encounters.json", "learnsets.json", "species.json"))):
        for name in names:
            with open(os.path.join(folder, name), "rb") as f:
                raw = f.read()
            parsed[prefix + name] = json.loads(raw.decode("utf-8"))
            digests[prefix + name] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return check_fields(parsed, digests)


def check_fields(parsed, digests):
    """The fields the second reading checks, pulled out of the parsed files by the check side's OWN key paths into
    one flat dict (expected_selection and expected_pack read only this dict, never load_inputs' one). `sha256` is the
    hash of the bytes the check itself read: expected_pack carries it as the pack's `sources`, so a header hash that
    differs from the files' is a finding too. (Called only by read_inputs_for_check. The selftest's mutant hands it the
    FIRST reading instead, and the reader-plant arms must then fail.)"""
    world, seasoned = "ai_player/knowledge/world/", "ai_player/knowledge/seasoned/"
    return {"entries": parsed[world + "campaign.json"]["entries"],
            "field_move_badges": parsed[world + "campaign.json"]["field_move_badges"],
            "maps": parsed[world + "maps.json"]["maps"],
            "trainers": parsed[world + "trainers.json"]["trainers"],
            "bosses": parsed[world + "bosses.json"]["bosses"],
            "encounters": parsed[seasoned + "encounters.json"]["maps"],
            "learnsets": parsed[seasoned + "learnsets.json"]["species"],
            "species": parsed[seasoned + "species.json"]["species"],
            "sha256": dict(sorted(digests.items()))}


def expected_selection(chapter, chk):
    """A SECOND reading of the inputs for chapter `chapter`, sharing no code with build_pack, ring, links,
    trainers_on, wild, hm_learners or claims, so a bug or a deleted line in those cannot hide here too. `chk` is
    read_inputs_for_check's dict: the files read again by the check's own loader, never load_inputs' dict.
    Returns (expected, problems): `expected` is what a complete pack must hold; `problems` are the inputs disagreeing
    with each other (an item one file names and another lost), each a finding on its own."""
    camp = {"entries": chk["entries"], "field_move_badges": chk["field_move_badges"]}
    every_map = chk["maps"]
    tdata = {t["symbol"]: t for t in chk["trainers"]}
    brows = chk["bosses"]
    mapd = {m["id"]: m for m in every_map}
    problems = []

    mine = [e for e in camp["entries"] if e.get("chapter") == chapter]
    entry_ids = {e["id"] for e in mine}
    area = {"MAP_" + a for e in mine for a in e["area"]}

    # the ring, from one flat edge list (build_pack walks the area maps, then every other map)
    edges = [(m["id"], c["map"]) for m in every_map for c in m["connections"]] + \
            [(m["id"], w["dest_map"]) for m in every_map for w in m["warps"]]
    neighbours = ({dst for src, dst in edges if src in area} | {src for src, dst in edges if dst in area}) \
        - area - {DYNAMIC}
    for lost in sorted(neighbours - set(mapd)):
        problems.append("maps.json: %s links to %s, a map maps.json does not hold" % (
            ", ".join(sorted({src for src, dst in edges if dst == lost and src in area})), lost))
    neighbours &= set(mapd)

    # trainers: every symbol on an area or ring map, with its sightings and its trainers.json facts
    exp_tr = {}
    for mid in sorted(area | neighbours):
        for obj in mapd[mid]["trainers"]:
            cite = obj.get("script") or obj.get("label")
            for sym in obj["trainers"]:
                row = exp_tr.setdefault(sym, {"maps": set(), "in_area": False, "sightings": set()})
                row["maps"].add(mid)
                row["in_area"] = row["in_area"] or mid in area
                row["sightings"].add((mid, obj["source"], cite))
    for sym, row in exp_tr.items():
        src = tdata.get(sym) or {}
        party = src.get("party") or []
        row.update(id=src.get("id"), flag=src.get("flag"), double=src.get("double"),
                   party=[(m["species"], m["level"]) for m in party])
    for b in brows:
        for mid in b.get("battled_on") or []:
            if mid in area | neighbours and mid not in exp_tr.get(b["id"], {}).get("maps", ()):
                problems.append("bosses.json says %s is battled on %s, but maps.json has no trainer object, trigger or "
                                "script for it there" % (b["id"], mid))

    # bosses: every fight an entry names, by `boss`, by `fights`, or by bosses.json's own `entry`
    named = []
    for e in mine:
        for f in ([e["boss"]] if e.get("boss") else []) + list(e.get("fights") or []):
            named.append((e["id"], f))
    named += [(b["entry"], b["fight"]) for b in brows if b.get("entry") in entry_ids]
    fight_names = {f for _, f in named}
    for eid, f in sorted(set(named)):
        if not any(b["fight"] == f for b in brows):
            problems.append("campaign entry %s names boss %s, but bosses.json has no row for it" % (eid, f))
    exp_boss = {b["id"]: [(m["species"], m["level"]) for m in b["party"]] for b in brows if b["fight"] in fight_names}
    won = {}
    for b in brows:
        if b["fight"] in fight_names and b.get("badge"):
            won[b["badge"]["id"]] = (b["badge"]["flag"], b["id"])

    # HMs: every field move an entry needs, and the one each badge won here unlocks
    rows_by_badge = {}
    rows_by_move = {}
    for r in camp["field_move_badges"]:
        rows_by_badge.setdefault(r["badge"], []).append(r["move"])
        rows_by_move[r["move"]] = r
    exp_hm = set()
    for e in mine:
        for fm in e["needs"].get("field_moves") or []:
            exp_hm.add(fm["move"])
            if fm["move"] not in rows_by_move:
                problems.append("%s needs field move %s, but campaign.json field_move_badges has no row for it" % (
                    e["id"], fm["move"]))
    for badge, (_flag, who) in sorted(won.items()):
        if not rows_by_badge.get(badge):
            problems.append("%s is won in this chapter (%s), but campaign.json field_move_badges names no field move "
                            "for it" % (badge, who))
        exp_hm.update(rows_by_badge.get(badge) or [])
    learners = {}
    for sp in chk["learnsets"]:
        for row in sp.get("tm_hm") or []:
            learners.setdefault(row["move"], set()).add(sp["symbol"])

    # connections: each one an area map has, whether it is mirrored, and the pair rule
    exp_conn = {}
    for a in sorted(area):
        mirrored = []
        for c in mapd[a]["connections"]:
            other = mapd.get(c["map"])
            back = bool(other) and a in [x["map"] for x in other["connections"]]
            mirrored.append((c["dir"], c["map"], back))
            if not back:
                problems.append("maps.json: %s connects %s to %s, but %s has no connection back (every connection in "
                                "the pinned decomp is mirrored)" % (a, c["dir"], c["map"], c["map"]))
        exp_conn[a] = mirrored
    for m in every_map:
        if m["id"] in area:
            continue
        for c in m["connections"]:
            if c["map"] in area and m["id"] not in [x["map"] for x in mapd[c["map"]]["connections"]]:
                problems.append("maps.json: %s connects %s to %s, but %s has no connection to %s (every connection "
                                "in the pinned decomp is mirrored)" % (m["id"], c["dir"], c["map"], c["map"], m["id"]))

    # warps: every warp of an area map and every warp into one, each with its kind
    edges_w = [(m["id"], w["dest_map"], w["dest_warp_id"]) for m in every_map for w in m["warps"]]

    def kind_of(src, w):
        target = w["dest_map"]
        if target == DYNAMIC:
            # the check's own reading of the MAP_DYNAMIC rule (dynamic_origins): it leads back only when some warp
            # arrives on a MAP_DYNAMIC warp of `src` (the arrival that records a way back); otherwise ONE-WAY
            mine_w = mapd[src]["warps"]
            arrivals_on_dyn = [x for x in edges_w if x[1] == src and isinstance(x[2], int)
                               and 0 <= x[2] < len(mine_w) and mine_w[x[2]]["dest_map"] == DYNAMIC]
            # (secret bases: C code records the way back, src/secret_base.c:450)
            return "dynamic" if arrivals_on_dyn or src.startswith(C_RECORDED_RETURN) else "one_way"
        if target not in mapd:
            return "unknown"
        arrivals = mapd[target]["warps"]
        idx = w["dest_warp_id"]
        if not isinstance(idx, int) or not 0 <= idx < len(arrivals):
            return "asymmetric"
        return "two_way" if arrivals[idx]["dest_map"] in (src, DYNAMIC) else "asymmetric"

    exp_warps = {a: [(i, w["dest_map"], w["dest_warp_id"], kind_of(a, w)) for i, w in enumerate(mapd[a]["warps"])]
                 for a in sorted(area)}
    exp_in = sorted((m["id"], i, w["dest_map"], kind_of(m["id"], w))
                    for m in every_map if m["id"] not in area
                    for i, w in enumerate(m["warps"]) if w["dest_map"] in area)

    # wild: re-aggregated from the SLOTS (build_pack reads the precomputed `rarity`)
    exp_wild = []
    for row in chk["encounters"]:
        if row.get("map") in area and row.get("availability") == "normal":
            for meth in sorted(row["methods"]):
                agg = {}
                for s in row["methods"][meth].get("slots") or []:
                    pct, lo, hi = agg.get(s["species"], (0, 999, 0))
                    agg[s["species"]] = (pct + s["chance_pct"], min(lo, s["min_level"]), max(hi, s["max_level"]))
                exp_wild.append((row["map"], meth, tuple(sorted(agg.items()))))

    expected = {"entry_ids": entry_ids, "area": area, "neighbours": neighbours, "trainers": exp_tr,
                "bosses": exp_boss, "badges_won": won, "hms": {m: learners.get("MOVE_" + m, set()) for m in exp_hm},
                "connections": exp_conn, "warps": exp_warps, "warps_in": exp_in, "wild": sorted(exp_wild),
                "flash": sorted(a for a in area if mapd[a]["requires_flash"]),
                "entries": mine,
                "pack": expected_pack(chapter, chk)}
    return expected, problems


def _bare(sym):
    """The checking side's own copy of short(): a broken short() must not hide in both readings."""
    if not sym:
        return sym
    for prefix in ("MAP_", "SPECIES_", "MOVE_", "ITEM_", "TRAINER_"):
        if sym.startswith(prefix):
            return sym[len(prefix):]
    return sym


def expected_pack(chapter, chk):
    """The WHOLE pack a second time, every key build_pack writes except the PROVENANCE header, written as its own code
    over the inputs (it calls none of build_pack, ring, links, classify_warp, trainers_on, wild, hm_learners, claims or
    short), from `chk`, read_inputs_for_check's own reading of the files. check_complete compares the pack with it
    value by value, so a boss mon's move or held item, a double flag, a connection, an HM's badge, one word of a claim
    or a source hash that differs from the files is a finding; and render_md_check renders the .md from THIS dict, so
    check_md_complete compares every line of the page with the files.
    Wild rows are summed from the SLOTS (build_pack reads the precomputed `rarity`). `sources` is the sha256 of the
    bytes the check read. Returns None if an area map is not in maps.json (resolve_maps refuses that chapter first)."""
    camp = {"entries": chk["entries"], "field_move_badges": chk["field_move_badges"]}
    mapd = {m["id"]: m for m in chk["maps"]}
    tdata = {t["symbol"]: t for t in chk["trainers"]}
    brows = chk["bosses"]
    mine = [e for e in camp["entries"] if e.get("chapter") == chapter]
    entries = [dict((k, v) for k, v in e.items() if k in ENTRY_FIELDS) for e in mine]
    area = list(dict.fromkeys("MAP_" + a for e in mine for a in e["area"]))
    in_area = set(area)
    if not in_area <= set(mapd):
        return None

    touching = set()
    for mid, m in mapd.items():
        outs = [c["map"] for c in m["connections"]] + [w["dest_map"] for w in m["warps"]]
        if mid in in_area:
            touching.update(outs)
        elif in_area.intersection(outs):
            touching.add(mid)
    ring_ids = sorted(x for x in touching if x in mapd and x not in in_area and x != DYNAMIC)
    map_rows = [dict({"id": mid, "role": role}, **{k: mapd[mid][k] for k in (
        "name", "map_type", "requires_flash", "allow_cycling", "allow_escaping", "allow_running")})
        for role, ids in (("area", area), ("neighbour", ring_ids)) for mid in ids]

    def warp_kind(src, w):
        dest, k = w["dest_map"], w["dest_warp_id"]
        if dest == DYNAMIC:
            # its own copy of the MAP_DYNAMIC rule (classify_warp / dynamic_origins), never a call to it
            own = mapd[src]["warps"]
            recorded = any(x["dest_map"] == src and isinstance(x["dest_warp_id"], int)
                           and 0 <= x["dest_warp_id"] < len(own) and own[x["dest_warp_id"]]["dest_map"] == DYNAMIC
                           for o in mapd.values() for x in o["warps"])
            if not recorded and not src.startswith(C_RECORDED_RETURN):
                return "one_way", ("ONE-WAY: no maps.json warp arrives on a MAP_DYNAMIC warp of %s, so no warp records "
                                   "a way back (a script sets this destination) and no warp leads back in" % _bare(src))
            return "dynamic", "MAP_DYNAMIC: returns to the map the player came from"
        if dest not in mapd:
            return ("unknown", "destination is not a maps.json map")
        arrivals = mapd[dest]["warps"]
        if not isinstance(k, int) or not 0 <= k < len(arrivals):
            return "asymmetric", "arrival warp %s does not exist on %s (%d warps)" % (k, _bare(dest), len(arrivals))
        back = arrivals[k]["dest_map"]
        if back == src or back == DYNAMIC:
            return "two_way", None
        return "asymmetric", "arrival warp %d on %s leads to %s, not back" % (k, _bare(dest), _bare(back))

    link_rows = []
    for a in area:
        conns = [{"dir": c["dir"], "map": c["map"], "offset": c["offset"],
                  "connects_back": c["map"] in mapd and any(x["map"] == a for x in mapd[c["map"]]["connections"])}
                 for c in mapd[a]["connections"]]
        warps = []
        for i, w in enumerate(mapd[a]["warps"]):
            kind, why = warp_kind(a, w)
            warps.append({"warp": i, "x": w["x"], "y": w["y"], "dest_map": w["dest_map"],
                          "dest_warp_id": w["dest_warp_id"], "kind": kind, "why": why})
        link_rows.append({"map": a, "connections": conns, "warps": warps})
    warps_in = []
    for sid in sorted(mapd):
        if sid in in_area:
            continue
        for i, w in enumerate(mapd[sid]["warps"]):
            if w["dest_map"] in in_area:
                kind, why = warp_kind(sid, w)
                warps_in.append({"from": sid, "warp": i, "dest_map": w["dest_map"], "dest_warp_id": w["dest_warp_id"],
                                 "kind": kind, "why": why})

    recs = {}
    for mid in area + ring_ids:
        for obj in mapd[mid]["trainers"]:
            for sym in obj["trainers"]:
                t = tdata.get(sym)
                if t is None:  # join_trainer refuses it
                    continue
                if sym not in recs:
                    lv = [p["level"] for p in t["party"]]
                    recs[sym] = {"symbol": sym, "id": t["id"], "name": t["name"], "class": t["class_name"],
                                 "flag": t["flag"], "double": t["double"], "levels": lv,
                                 "level_min": min(lv) if lv else None, "level_max": max(lv) if lv else None,
                                 "ref": t["ref"], "species": [p["species"] for p in t["party"]], "in_area": False,
                                 "seen": []}
                rec = recs[sym]
                rec["in_area"] = rec["in_area"] or mid in in_area
                s = {"map": mid, "source": obj["source"], "script": obj.get("script") or obj.get("label")}
                s.update((k, obj[k]) for k in ("trainer_type", "sight", "x", "y", "ref") if k in obj)
                rec["seen"].append(s)
    trainers = sorted(recs.values(), key=lambda r: (not r["in_area"], r["seen"][0]["map"], r["symbol"]))

    fight_order = list(dict.fromkeys(f for e in mine for f in (e.get("fights") or [])))
    entry_ids = {e["id"] for e in mine}
    named = set(fight_order) | {e["boss"] for e in mine if e.get("boss")} | \
        {b["fight"] for b in brows if b.get("entry") in entry_ids}
    pos = {f: i for i, f in enumerate(fight_order)}
    bosses = sorted((b for b in brows if b["fight"] in named), key=lambda b: (pos.get(b["fight"], len(pos)), b["id"]))
    done, later = set(fight_order), []
    for e in mine:
        for f in e.get("area_bosses") or []:
            if f in done:
                continue
            done.add(f)
            vs = [b for b in brows if b["fight"] == f]
            if vs:
                later.append({"fight": f, "role": vs[0]["role"], "entry": vs[0]["entry"], "ids": [b["id"] for b in vs],
                              "level_max": max(p["level"] for b in vs for p in b["party"])})

    names = {s["symbol"]: s["name"] for s in chk["species"]}
    wild_rows = []
    for row in chk["encounters"]:
        if row.get("map") not in in_area or row.get("availability") != "normal":
            continue
        for meth in sorted(row["methods"]):
            tab = row["methods"][meth]
            agg = {}
            for s in tab.get("slots") or []:
                pct, lo, hi = agg.get(s["species"], (0, 999, 0))
                agg[s["species"]] = (pct + s["chance_pct"], min(lo, s["min_level"]), max(hi, s["max_level"]))
            mons = [{"species": sp, "name": names.get(sp, _bare(sp)), "chance_pct": v[0], "min_level": v[1],
                     "max_level": v[2]} for sp, v in sorted(agg.items(), key=lambda kv: (-kv[1][0], kv[0]))]
            wild_rows.append({"map": row["map"], "method": meth, "encounter_rate": tab.get("encounter_rate"),
                              "requires": row.get("requires"), "condition": (row.get("conditions") or {}).get(meth),
                              "species": mons})

    fmb = {}
    for r in camp["field_move_badges"]:
        fmb[r["move"]] = r
    badge_rows = [b["badge"] for b in bosses if b.get("badge")]
    won = {bd["id"] for bd in badge_rows}
    wanted = [(fm["move"], "needed by %s" % e["id"]) for e in mine for fm in (e["needs"].get("field_moves") or [])]
    wanted += [(r["move"], "unlocked by %s, won this chapter" % r["badge"]) for r in camp["field_move_badges"]
               if r["badge"] in won]
    wild_species = {m["species"] for r in wild_rows for m in r["species"]}
    hms = []
    for mv, why in wanted:
        rows = [(s["symbol"], t["tm"]) for s in chk["learnsets"]
                for t in s.get("tm_hm", []) if t["move"] == "MOVE_" + mv]
        who = [sp for sp, _ in rows]
        hms.append({"move": mv, "why": why, "hm": next((tm for _, tm in rows if tm), None),
                    "badge": (fmb.get(mv) or {}).get("badge"), "badge_ref": (fmb.get(mv) or {}).get("ref"),
                    "learners_count": len(who), "learners": who,
                    "learners_met_wild_here": [sp for sp in who if sp in wild_species]})

    cl = []

    def add(kind, text, source):
        cl.append({"n": len(cl) + 1, "kind": kind, "claim": text, "source": source})

    for b in bosses:
        team = ", ".join("%s Lv%d" % (_bare(p["species"]), p["level"]) +
                         (" @%s" % _bare(p["held_item"]) if p.get("held_item") else "") for p in b["party"])
        add("boss_team", "%s (%s, %s) %s battle: %s" % (b["fight"], _bare(b["id"]), b["role"],
                                                        "DOUBLE" if b["double"] else "single", team), b["ref"])
    for b in bosses:
        if b["id"] in recs:
            t = recs[b["id"]]
            add("progress_flag", "%s's defeat flag is number %d (TRAINER_FLAGS_START + %d)" % (
                _bare(b["id"]), t["flag"], t["id"]), t["ref"])
    for bd in badge_rows:
        add("progress_flag", "the chapter's boss sets %s (%s)" % (bd["flag"], bd["id"]), bd["ref"])
    for e in entries:
        nd = e["needs"]
        for bd in nd.get("badges") or []:
            add("progress_flag", "%s needs %s" % (e["id"], bd), (nd.get("badge_refs") or {}).get(bd))
        for g in nd.get("badge_gates") or []:
            add("progress_flag", "%s badge gate: %s" % (e["id"], json.dumps(g, sort_keys=True)), None)
        for fm in nd.get("field_moves") or []:
            add("hm_gate", "%s needs field move %s (badge %s)" % (e["id"], fm["move"], fm.get("badge")), fm.get("ref"))
        if nd.get("double_battle") or (nd.get("party_min") or 1) > 1:
            add("double_battle", "%s: party_min %s (%s)" % (e["id"], nd.get("party_min"), nd.get("party_min_basis")),
                nd.get("party_min_ref"))
    for h in hms:
        met = ", ".join(_bare(s) for s in h["learners_met_wild_here"]) or "none"
        add("hm_gate", "%s (%s) usable outside battle only with %s; %d species learn it, met wild here: %s" % (
            h["move"], h["hm"], h["badge"], len(h["learners"]), met), h["badge_ref"])
    for mid in area:
        if mapd[mid]["requires_flash"]:
            add("hm_gate", "%s requires Flash (dark map)" % _bare(mid), "maps.json requires_flash")
    for t in trainers:
        if t["double"] and t["in_area"]:
            add("double_battle", "%s is a DOUBLE battle (%s)" % (_bare(t["symbol"]), t["class"]), t["ref"])
    triggers = {}
    for t in trainers:
        key = tuple(sorted({s["script"] for s in t["seen"] if s["source"] == "coord_event"}))
        if t["in_area"] and key:
            triggers.setdefault(key, []).append(_bare(t["symbol"]))
    for key, syms in triggers.items():
        add("scripted_battle", "%s can be started by a trigger tile (%s); the trigger's var condition is NOT modelled "
                               "here" % (" / ".join(syms), ", ".join(key)), "maps.json coord_events")
    total = 0
    for row in link_rows:
        for w in row["warps"]:
            total += 1
            if w["kind"] in ("asymmetric", "unknown", "one_way"):
                add("one_way_warp", "%s warp %d -> %s: %s" % (_bare(row["map"]), w["warp"], _bare(w["dest_map"]),
                                                              w["why"]), "maps.json warps")
        for c in row["connections"]:
            if not c["connects_back"]:
                add("one_way_warp", "%s connects %s to %s, which has no connection back" % (
                    _bare(row["map"]), c["dir"], _bare(c["map"])), "maps.json connections")
    for w in warps_in:
        total += 1
        if w["kind"] in ("asymmetric", "unknown", "one_way"):
            add("one_way_warp", "%s warp %d -> %s: %s" % (_bare(w["from"]), w["warp"], _bare(w["dest_map"]), w["why"]),
                "maps.json warps")
    if not any(c["kind"] == "one_way_warp" for c in cl):
        add("one_way_warp", "none of the %d warps touching the area maps is one-way by warp data (ledges, holes and "
                            "scripted movement are NOT modelled)" % total, "maps.json warps")

    return {"_generated": GENERATED, "_absent": ABSENT, "chapter": chapter, "entries": entries, "maps": map_rows,
            "links": link_rows, "warps_in": warps_in, "trainers": trainers, "bosses": bosses,
            "area_bosses_later": later, "wild": wild_rows, "hms": hms, "claims": cl, "sources": chk["sha256"]}


def deep_diff(have, want, path, out):
    """Every leaf where `have` (the pack) differs from `want` (the second reading), as `WRONG pack <path>` findings. A
    bool is not an int here (True == 1 in Python, and a double flag must not pass as a level)."""
    if isinstance(have, dict) and isinstance(want, dict):
        for k in sorted(set(have) | set(want), key=str):
            p = "%s.%s" % (path, k)
            if k not in have:
                out.append("MISSING pack %s (the inputs give %s)" % (p, json.dumps(want[k])[:120]))
            elif k not in want:
                out.append("EXTRA pack %s (%s)" % (p, json.dumps(have[k])[:120]))
            else:
                deep_diff(have[k], want[k], p, out)
    elif isinstance(have, list) and isinstance(want, list):
        if len(have) != len(want):
            out.append("WRONG pack %s: %d items in the pack, %d from the inputs" % (path, len(have), len(want)))
        for i in range(min(len(have), len(want))):
            deep_diff(have[i], want[i], "%s[%d]" % (path, i), out)
    elif type(have) is not type(want) or have != want:
        out.append("WRONG pack %s: pack %s, inputs %s" % (path, json.dumps(have)[:160], json.dumps(want)[:160]))


def check_complete(pack, expected):
    """Every difference between the pack and expected_selection, as findings (MISSING, EXTRA or WRONG)."""
    out = []

    def diff(what, have, want):
        for x in sorted(set(want) - set(have), key=str):
            out.append("MISSING %s %s" % (what, x))
        for x in sorted(set(have) - set(want), key=str):
            out.append("EXTRA %s %s" % (what, x))

    diff("entry", [e["id"] for e in pack["entries"]], expected["entry_ids"])
    diff("area map", [m["id"] for m in pack["maps"] if m["role"] == "area"], expected["area"])
    diff("ring map", [m["id"] for m in pack["maps"] if m["role"] == "neighbour"], expected["neighbours"])

    have_tr = {t["symbol"]: t for t in pack["trainers"]}
    diff("trainer", have_tr, expected["trainers"])
    for sym, want in sorted(expected["trainers"].items()):
        t = have_tr.get(sym)
        if t is None:
            continue
        got = {"id": t["id"], "flag": t["flag"], "double": t["double"], "in_area": t["in_area"],
               "party": list(zip(t["species"], t["levels"])) if len(t["species"]) == len(t["levels"]) else None,
               "sightings": {(s["map"], s["source"], s.get("script")) for s in t["seen"]}}
        for k in ("id", "flag", "double", "in_area", "party", "sightings"):
            if got[k] != want[k]:
                out.append("WRONG trainer %s %s: pack %s, inputs %s" % (sym, k, got[k], want[k]))

    have_b = {b["id"]: [(m["species"], m["level"]) for m in b["party"]] for b in pack["bosses"]}
    diff("boss", have_b, expected["bosses"])
    for bid, party in sorted(expected["bosses"].items()):
        if bid in have_b and have_b[bid] != party:
            out.append("WRONG boss %s team: pack %s, inputs %s" % (bid, have_b[bid], party))

    have_hm = {h["move"]: set(h["learners"]) for h in pack["hms"]}
    diff("HM", have_hm, expected["hms"])
    for mv, who in sorted(expected["hms"].items()):
        if mv in have_hm and have_hm[mv] != who:
            out.append("WRONG HM %s learners: pack %d, inputs %d" % (mv, len(have_hm[mv]), len(who)))

    rows = {r["map"]: r for r in pack["links"]}
    diff("links row", rows, expected["connections"])
    for a, want in sorted(expected["connections"].items()):
        if a in rows:
            diff("connection on %s" % a, [(c["dir"], c["map"], c["connects_back"]) for c in rows[a]["connections"]],
                 want)
            diff("warp on %s" % a, [(w["warp"], w["dest_map"], w["dest_warp_id"], w["kind"])
                                   for w in rows[a]["warps"]], expected["warps"][a])
    diff("warp into the area", [(w["from"], w["warp"], w["dest_map"], w["kind"]) for w in pack["warps_in"]],
         expected["warps_in"])

    diff("wild row", [(r["map"], r["method"], tuple(sorted((m["species"], (m["chance_pct"], m["min_level"],
                                                                            m["max_level"])) for m in r["species"])))
                      for r in pack["wild"]], expected["wild"])

    # the claims each of the above requires (substring match on the claim text, by kind)
    have_c = {}
    for c in pack["claims"]:
        have_c.setdefault(c["kind"], []).append(c["claim"])

    def need(kind, text):
        if not any(text in c for c in have_c.get(kind, [])):
            out.append("MISSING claim [%s] containing %r" % (kind, text))

    for bid in sorted(expected["bosses"]):
        need("boss_team", "(%s, " % short(bid))
        if bid in expected["trainers"]:
            need("progress_flag", "%s's defeat flag is number %s" % (short(bid), expected["trainers"][bid]["flag"]))
    for badge, (flag, _who) in sorted(expected["badges_won"].items()):
        need("progress_flag", "sets %s (%s)" % (flag, badge))
    for e in expected["entries"]:
        for bd in e["needs"].get("badges") or []:
            need("progress_flag", "%s needs %s" % (e["id"], bd))
        for fm in e["needs"].get("field_moves") or []:
            need("hm_gate", "%s needs field move %s" % (e["id"], fm["move"]))
        if e["needs"].get("double_battle") or (e["needs"].get("party_min") or 1) > 1:
            need("double_battle", "%s: party_min %s" % (e["id"], e["needs"].get("party_min")))
    for mv in sorted(expected["hms"]):
        need("hm_gate", "%s (" % mv)
    for a in expected["flash"]:
        need("hm_gate", "%s requires Flash" % short(a))
    for sym, want in sorted(expected["trainers"].items()):
        if want["in_area"] and want["double"]:
            need("double_battle", "%s is a DOUBLE battle" % short(sym))
        if want["in_area"] and any(src == "coord_event" for _m, src, _c in want["sightings"]):
            need("scripted_battle", short(sym))
    odd = [("%s warp %d -> %s" % (short(a), i, short(d))) for a, ws in sorted(expected["warps"].items())
           for i, d, _k, kind in ws if kind in ("asymmetric", "unknown", "one_way")]
    odd += ["%s warp %d -> %s" % (short(s), i, short(d)) for s, i, d, kind in expected["warps_in"]
            if kind in ("asymmetric", "unknown", "one_way")]
    odd += ["%s connects %s to %s, which has no connection back" % (short(a), dr, short(m))
            for a, cs in sorted(expected["connections"].items()) for dr, m, back in cs if not back]
    for text in odd:
        need("one_way_warp", text)
    if not odd:
        total = sum(len(ws) for ws in expected["warps"].values()) + len(expected["warps_in"])
        need("one_way_warp", "none of the %d warps" % total)

    # and then EVERY value: the findings above name an omission in words; this one compares the whole pack (each boss
    # mon's moves and held item, each claim's full text, each connection's offset ...) with expected_pack
    if expected.get("pack") is None:
        out.append("MISSING the second reading of the inputs (expected_pack returned nothing)")
    else:
        deep_diff(pack, with_provenance(expected["pack"], pack), "$", out)
    return out


def with_provenance(xp, pack):
    """The second reading plus the pack's PROVENANCE header (pin, generator, verification: the selftest's pin, hashes
    and F2 arms check those). The source hashes are NOT copied: the second reading carries its own. A header key the
    pack lacks stays absent from the pack and present here, so deep_diff names it."""
    full = dict(xp)
    for k in PROVENANCE:
        full[k] = pack.get(k, "(absent from the pack)")
    return full


def render_md_check(xp, level, full_size):
    """The .md a SECOND time, from expected_pack's dict (plus the pack's provenance header), section by section. It is
    render_md's page by contract, written as separate code so a dropped move, a blanked links line or a wrong word in
    either renderer makes the two pages differ. Change the page's wording in BOTH (the CONTROL arm fails until then)."""
    n = xp["chapter"]

    def head():
        vf = xp["inputs_verified"]
        ok = isinstance(vf, dict) and bool(VERIFY_PASS.match(vf.get("result", "")))
        rows = ["| `%s` | `%s` |" % (k, v[:MD_HASH_CHARS]) for k, v in xp["sources"].items()]
        return (["# Chapter %d pack (generated)" % n, "", "> " + xp["_generated"], ">"] +
                ["> - " + x for x in xp["_absent"]] +
                ["", "Decomp pin: `%s`. Generator: `%s` sha256 `%s`." % (
                    xp["decomp_pin"], xp["generator"]["path"], xp["generator"]["sha256"][:MD_HASH_CHARS]), "",
                 "Inputs verified first by `%s` (sha256 `%s`) over every record of the four world files read: exit "
                 "%s, %s. Its command and result line are in ch%d.json `inputs_verified`." % (
                     vf["by"], vf["verifier_sha256"][:MD_HASH_CHARS], vf["exit"],
                     "0 mismatches" if ok else "NOT VERIFIED", n), "",
                 "| source | sha256 (first %d; all 64 in ch%d.json) |" % (MD_HASH_CHARS, n), "|---|---|"] + rows)

    def entries():
        out = ["## Entries"]
        for e in xp["entries"]:
            nd = e["needs"]
            band = nd.get("level_band") or {}
            needs = list(nd.get("badges") or []) + [f["move"] for f in (nd.get("field_moves") or [])]
            out.append("- **%s** (order %d) area %s; boss %s; party_min %s; types ahead %s; level band %s-%s%s" % (
                e["id"], e["order"], ", ".join(e["area"]), e["boss"] or "-", nd.get("party_min"),
                "/".join(nd.get("types_ahead") or []) or "-", band.get("low"), band.get("high"),
                ("; needs " + ", ".join(needs)) if needs else ""))
        return out

    def links():
        out = ["## Maps and links"]
        rows = {m["id"]: m for m in xp["maps"]}
        for row in xp["links"]:
            m = rows[row["map"]]
            tags = [m["map_type"][len("MAP_TYPE_"):].lower() if m["map_type"].startswith("MAP_TYPE_")
                    else m["map_type"].lower()]
            tags += ["FLASH"] * bool(m["requires_flash"]) + ["no running"] * (not m["allow_running"])
            conns = [_bare(c["map"]) for c in row["connections"]]
            conn_text = ", ".join("%s %s%s" % (c["dir"], name, "" if c["connects_back"] else " (NO WAY BACK)")
                                  for c, name in zip(row["connections"], conns)) or "-"
            dests, count, odd = [], {}, {}
            for w in row["warps"]:
                if w["dest_map"] not in count:
                    dests.append(w["dest_map"])
                count[w["dest_map"]] = count.get(w["dest_map"], 0) + 1
                odd[w["dest_map"]] = odd.get(w["dest_map"], 0) + (w["kind"] in ("asymmetric", "unknown", "one_way"))
            if not dests:
                warp_text = "-"
            elif level >= 3:
                n_odd = sum(odd.values())
                warp_text = "%d to %d map%s%s" % (len(row["warps"]), len(dests), "s" if len(dests) != 1 else "",
                                                  (" (%d ONE-WAY?)" % n_odd) if n_odd else "")
            else:
                warp_text = ", ".join(_bare(d) + ((" x%d" % count[d]) if count[d] > 1 else "") +
                                      ((" (%d ONE-WAY?)" % odd[d]) if odd[d] else "") for d in dests)
            out.append("- **%s** (%s). Connections: %s. Warps: %s." % (_bare(row["map"]), ", ".join(tags), conn_text,
                                                                        warp_text))
        ring = [_bare(m["id"]) for m in xp["maps"] if m["role"] == "neighbour"]
        out.append("- Neighbours (one ring, %d): %s" % (len(ring), ("listed in ch%d.json `maps`" % n) if level >= 3
                                                         else (", ".join(ring) or "-")))
        return out

    def trainers():
        out = ["## Trainers"]
        if level == 0:
            out.append("EVERY trainer on the area maps, whether or not this chapter fights them (compare the levels "
                       "with the entries' level band). Area maps: name, class, single/DOUBLE, sight, levels, team, "
                       "defeat flag number.")
        else:
            out.append("%s (level %d; the full page is %d bytes): %s. Doubles, bosses, HMs, links and claims stay in "
                       "full; everything is in ch%d.json." % (SUMMARY_MARK, level, full_size,
                                                              "; ".join(SUMMARY_LEVELS[1:level + 1]), n))
        ordinary, outer = {}, {}
        for t in xp["trainers"]:
            first = _bare(t["seen"][0]["map"])
            if not t["in_area"]:
                outer.setdefault(first, []).append(t)
                continue
            if level and not t["double"]:
                ordinary.setdefault(first, []).append(t)
                continue
            s0 = t["seen"][0]
            seen_as = ("sight %s" % s0["sight"]) if "sight" in s0 else \
                ("a " + SEEN_AS.get(s0["source"], s0["source"]))
            out.append("- %s `%s` %s, %s, %s, Lv %s (%s), flag %d, on %s" % (
                t["name"] or "-", _bare(t["symbol"]), t["class"], "DOUBLE" if t["double"] else "single", seen_as,
                "/".join(map(str, t["levels"])), " ".join(_bare(s) for s in t["species"]), t["flag"],
                ", ".join(sorted({_bare(s["map"]) for s in t["seen"]}))))
        for mp in sorted(ordinary):
            ts = ordinary[mp]
            lv = [x for t in ts for x in t["levels"]]
            out.append("- %s: %d ordinary trainer%s, Lv %s-%s%s" % (
                mp, len(ts), "s" if len(ts) != 1 else "", min(lv) if lv else "-", max(lv) if lv else "-",
                "" if level >= 4 else ", species %s" % (" ".join(sorted({_bare(x) for t in ts for x in t["species"]}))
                                                        or "-")))
        if outer:
            out.append("")
            if level >= 4:
                lv = [x for ts in outer.values() for t in ts for x in t["levels"]]
                dbl = [_bare(t["symbol"]) for ts in outer.values() for t in ts if t["double"]]
                out.append("Neighbour maps: %d trainers on %d maps, Lv %s-%s%s" % (
                    sum(map(len, outer.values())), len(outer), min(lv) if lv else "-", max(lv) if lv else "-",
                    ("; DOUBLE " + ", ".join(dbl)) if dbl else ""))
            elif level:
                out.append("Neighbour maps (trainer count, Lv min-max, doubles by name):")
                for mp in sorted(outer):
                    lv = [x for t in outer[mp] for x in t["levels"]]
                    dbl = [_bare(t["symbol"]) for t in outer[mp] if t["double"]]
                    out.append("- %s: %d, Lv %s-%s%s" % (mp, len(outer[mp]), min(lv) if lv else "-",
                                                         max(lv) if lv else "-",
                                                         ("; DOUBLE " + ", ".join(dbl)) if dbl else ""))
            else:
                out.append("Neighbour maps (name, Lv min-max, D = double):")
                for mp in sorted(outer):
                    out.append("- %s: %s" % (mp, ", ".join("%s %s-%s%s" % (
                        _bare(t["symbol"]), t["level_min"], t["level_max"], " D" if t["double"] else "")
                        for t in outer[mp])))
        return out

    def bosses():
        out = ["## Bosses"]
        if not xp["bosses"]:
            out.append("- none fought in this chapter's entries")
        for b in xp["bosses"]:
            battle = "DOUBLE" if b["double"] else "single"
            out.append("- **%s** `%s` (%s, %s)%s, %s:" % (b["fight"], _bare(b["id"]), b["role"], battle,
                                                         (" badge " + b["badge"]["id"]) if b.get("badge") else "",
                                                         b["ref"]))
            for p in b["party"]:
                out.append("  - %s Lv%d [%s] %s%s" % (_bare(p["species"]), p["level"], "/".join(p.get("types") or []),
                                                      " ".join(_bare(mv) for mv in (p.get("moves") or [])),
                                                      (" @" + _bare(p["held_item"])) if p.get("held_item") else ""))
        if xp["area_bosses_later"]:
            out.append("- Battled on these maps in a LATER entry: " + ", ".join(
                "%s (%s, %d variant%s, top Lv %d)" % (r["fight"], r["entry"], len(r["ids"]),
                                                      "s" if len(r["ids"]) != 1 else "", r["level_max"])
                for r in xp["area_bosses_later"]))
        return out

    def wild():
        out = ["## Wild encounters (area maps, normal play)"]
        rows = xp["wild"]
        if not rows:
            return out + ["- no wild table on the area maps"]
        if level >= 4:
            return out + ["- %d tables on %s: in ch%d.json `wild` (species, rates and levels)" % (
                len(rows), ", ".join(sorted({_bare(r["map"]) for r in rows})), n)]

        def tag(r):
            return (" REQUIRES %s" % r["requires"] if r["requires"] else "") + \
                (" IF %s" % r["condition"] if r["condition"] else "")
        if level >= 2:
            per = {}
            for r in rows:
                sp = r["species"]
                per.setdefault(_bare(r["map"]), []).append("%s%s %s L%s-%s" % (
                    r["method"], tag(r), " ".join(m["name"] for m in sp),
                    min(m["min_level"] for m in sp) if sp else "-", max(m["max_level"] for m in sp) if sp else "-"))
            return out + ["- %s: %s" % (mp, "; ".join(per[mp])) for mp in sorted(per)]
        return out + ["- %s %s (rate %s)%s: %s" % (_bare(r["map"]), r["method"], r["encounter_rate"], tag(r), ", ".join(
            "%s %d%% L%d-%d" % (m["name"], m["chance_pct"], m["min_level"], m["max_level"]) for m in r["species"]))
            for r in rows]

    def hms():
        out = ["## HM moves"]
        if not xp["hms"]:
            out.append("- no field move is needed by, or unlocked in, this chapter (campaign.json needs.field_moves; "
                       "badges won)")
        for h in xp["hms"]:
            out.append("- %s (%s, badge %s, %s): %s. %d species learn it; met wild here: %s" % (
                h["move"], h["hm"], h["badge"], h["badge_ref"], h["why"], h["learners_count"],
                ", ".join(_bare(s) for s in h["learners_met_wild_here"]) or "none"))
        return out

    def claim_lines():
        return ["## LOAD-BEARING CLAIMS (for the adversarial agent: refute each against the pinned decomp)"] + [
            "%d. [%s] %s" % (c["n"], c["kind"], c["claim"]) + ((" (source: %s)" % c["source"]) if c["source"] else "")
            for c in xp["claims"]]

    page = []
    for part in (head, entries, links, trainers, bosses, wild, hms, claim_lines):
        page += part() + [""]
    return "\n".join(page)


def expected_md(xp, cap):
    """render_md_check at the least summarised level that fits `cap`, chosen by its OWN size measurements (the same
    rule as render_within_cap, so a wrong level choice in either is a difference too)."""
    full = render_md_check(xp, 0, None)
    size = len(full.encode("utf-8"))
    md, level = full, 0
    while len(md.encode("utf-8")) > cap and level + 1 < len(SUMMARY_LEVELS):
        level += 1
        md = render_md_check(xp, level, size)
    return md


def check_md_complete(pack, md, expected, cap):
    """The .md, EVERY line of it, against the second rendering of the second reading (render_md_check over
    expected_pack): so a boss line must hold every mon with its species, level, types, moves and held item; a double
    battle must say DOUBLE; a links line must list every connection and warp; an HM line must name its badge; each
    claim must hold its full text and source; and a summarised page must summarise at the same level with the same
    counts and species. Compares whole lines, never a line's start. Returns the findings, each naming the section."""
    out = []
    if pack["bosses"] and "none fought" in md:
        out.append("md says 'none fought' but the pack has %d boss row(s)" % len(pack["bosses"]))
    if expected.get("pack") is None:
        return out + ["md cannot be checked: no second reading of the inputs"]
    want = expected_md(with_provenance(expected["pack"], pack), cap).split("\n")
    have = md.split("\n")

    def section(lines, i):
        for ln in reversed(lines[:i + 1]):
            if ln.startswith("## "):
                return ln[3:].split(" (")[0]
        return "header"

    for op, h1, h2, w1, w2 in difflib.SequenceMatcher(None, have, want, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        for k in range(max(h2 - h1, w2 - w1)):
            hi, wi = h1 + k, w1 + k
            if hi < h2 and wi < w2:
                out.append("md [%s] line %d: the .md has %r, the inputs give %r" % (
                    section(want, wi), hi + 1, have[hi][:200], want[wi][:200]))
            elif wi < w2:
                out.append("md [%s] MISSING line: %r" % (section(want, wi), want[wi][:200]))
            else:
                out.append("md [%s] EXTRA line %d: %r" % (section(have, hi), hi + 1, have[hi][:200]))
    return out


# ---------------------------------------------------------------- rendering
#: what each summary level adds, in the order render_within_cap tries them (level 1 is the coordinator's F2 rule; the
#: deeper levels exist because summarising chapter 13's ordinary trainers still left 15,096 bytes, over the cap).
#: None of them touches a load-bearing section.
SUMMARY_LEVELS = (
    None,
    "ordinary (single-battle) trainers counted per map with level range and species",
    "wild tables without rates",
    "warps and neighbour maps counted",
    "trainer species, wild species and neighbour trainers left to the .json",
)


def render_md(pack, summary_of=None, level=0):
    """The .md. `level` 0 renders everything; `level` k > 0 applies SUMMARY_LEVELS[1..k] (the ordinary trainers
    first) and `summary_of` is the full rendering's size, quoted on the page so a reader knows it was summarised."""
    L = []
    a = L.append
    n = pack["chapter"]
    a("# Chapter %d pack (generated)" % n)
    a("")
    a("> " + pack["_generated"])
    a(">")
    for line in pack["_absent"]:
        a("> - " + line)
    a("")
    a("Decomp pin: `%s`. Generator: `%s` sha256 `%s`." % (pack["decomp_pin"], pack["generator"]["path"],
                                                          pack["generator"]["sha256"][:MD_HASH_CHARS]))
    vf = pack["inputs_verified"]
    a("")
    a("Inputs verified first by `%s` (sha256 `%s`) over every record of the four world files read: exit %s, %s. Its "
      "command and result line are in ch%d.json `inputs_verified`." % (
          vf["by"], vf["verifier_sha256"][:MD_HASH_CHARS], vf["exit"],
          "0 mismatches" if VERIFY_PASS.match(vf["result"]) else "NOT VERIFIED", n))
    a("")
    a("| source | sha256 (first %d; all 64 in ch%d.json) |" % (MD_HASH_CHARS, n))
    a("|---|---|")
    for k, v in pack["sources"].items():
        a("| `%s` | `%s` |" % (k, v[:MD_HASH_CHARS]))
    a("")
    a("## Entries")
    for e in pack["entries"]:
        nd = e["needs"]
        lb = nd.get("level_band") or {}
        a("- **%s** (order %d) area %s; boss %s; party_min %s; types ahead %s; level band %s-%s%s" % (
            e["id"], e["order"], ", ".join(e["area"]), e["boss"] or "-", nd.get("party_min"),
            "/".join(nd.get("types_ahead") or []) or "-", lb.get("low"), lb.get("high"),
            ("; needs " + ", ".join((nd.get("badges") or []) + [f["move"] for f in nd.get("field_moves") or []]))
            if (nd.get("badges") or nd.get("field_moves")) else ""))
    a("")
    a("## Maps and links")
    for row in pack["links"]:
        m = next(x for x in pack["maps"] if x["id"] == row["map"])
        conns = ", ".join("%s %s%s" % (c["dir"], short(c["map"]), "" if c["connects_back"] else " (NO WAY BACK)")
                          for c in row["connections"]) or "-"
        groups = {}
        for w in row["warps"]:
            g = groups.setdefault(w["dest_map"], {"n": 0, "odd": 0})
            g["n"] += 1
            g["odd"] += w["kind"] in ("asymmetric", "unknown", "one_way")
        if level >= 3:
            odd = sum(g["odd"] for g in groups.values())
            warps = "%d to %d map%s%s" % (len(row["warps"]), len(groups), "" if len(groups) == 1 else "s",
                                          " (%d ONE-WAY?)" % odd if odd else "") if groups else "-"
        else:
            warps = ", ".join("%s%s%s" % (short(d), " x%d" % g["n"] if g["n"] > 1 else "",
                                          " (%d ONE-WAY?)" % g["odd"] if g["odd"] else "")
                              for d, g in groups.items()) or "-"
        flags = [m["map_type"].replace("MAP_TYPE_", "").lower()]
        if m["requires_flash"]:
            flags.append("FLASH")
        if not m["allow_running"]:
            flags.append("no running")
        a("- **%s** (%s). Connections: %s. Warps: %s." % (short(m["id"]), ", ".join(flags), conns, warps))
    nb = [short(x["id"]) for x in pack["maps"] if x["role"] == "neighbour"]
    if level >= 3:
        a("- Neighbours (one ring, %d): listed in ch%d.json `maps`" % (len(nb), n))
    else:
        a("- Neighbours (one ring, %d): %s" % (len(nb), ", ".join(nb) or "-"))
    a("")
    a("## Trainers")
    if not level:
        a("EVERY trainer on the area maps, whether or not this chapter fights them (compare the levels with the "
          "entries' level band). Area maps: name, class, single/DOUBLE, sight, levels, team, defeat flag number.")
    else:
        a("%s (level %d; the full page is %d bytes): %s. Doubles, bosses, HMs, links and claims stay in full; "
          "everything is in ch%d.json." % (SUMMARY_MARK, level, summary_of, "; ".join(SUMMARY_LEVELS[1:level + 1]), n))
    for t in pack["trainers"]:
        if not t["in_area"] or (level and not t["double"]):
            continue
        s = t["seen"][0]
        sight = ("sight %s" % s["sight"]) if "sight" in s else ("a %s" % SEEN_AS.get(s["source"], s["source"]))
        a("- %s `%s` %s, %s, %s, Lv %s (%s), flag %d, on %s" % (
            t["name"] or "-", short(t["symbol"]), t["class"], "DOUBLE" if t["double"] else "single",
            sight, "/".join(str(x) for x in t["levels"]),
            " ".join(short(x) for x in t["species"]), t["flag"],
            ", ".join(sorted({short(x["map"]) for x in t["seen"]}))))
    if level:
        per_map = {}
        for t in pack["trainers"]:
            if t["in_area"] and not t["double"]:
                per_map.setdefault(short(t["seen"][0]["map"]), []).append(t)
        for mp, ts in sorted(per_map.items()):
            lv = [x for t in ts for x in t["levels"]]
            sp = sorted({short(x) for t in ts for x in t["species"]})
            a("- %s: %d ordinary trainer%s, Lv %s-%s%s" % (
                mp, len(ts), "" if len(ts) == 1 else "s", min(lv) if lv else "-", max(lv) if lv else "-",
                "" if level >= 4 else ", species " + (" ".join(sp) or "-")))
    outer = {}
    for t in pack["trainers"]:
        if not t["in_area"]:
            outer.setdefault(short(t["seen"][0]["map"]), []).append(t)
    if outer:
        a("")
        if not level:
            a("Neighbour maps (name, Lv min-max, D = double):")
            for mp, ts in sorted(outer.items()):
                a("- %s: %s" % (mp, ", ".join("%s %s-%s%s" % (short(t["symbol"]), t["level_min"], t["level_max"],
                                                              " D" if t["double"] else "") for t in ts)))
        elif level >= 4:
            lv = [x for ts in outer.values() for t in ts for x in t["levels"]]
            dbl = [short(t["symbol"]) for ts in outer.values() for t in ts if t["double"]]
            a("Neighbour maps: %d trainers on %d maps, Lv %s-%s%s" % (
                sum(len(ts) for ts in outer.values()), len(outer), min(lv) if lv else "-", max(lv) if lv else "-",
                ("; DOUBLE " + ", ".join(dbl)) if dbl else ""))
        else:
            a("Neighbour maps (trainer count, Lv min-max, doubles by name):")
            for mp, ts in sorted(outer.items()):
                lv = [x for t in ts for x in t["levels"]]
                dbl = [short(t["symbol"]) for t in ts if t["double"]]
                a("- %s: %d, Lv %s-%s%s" % (mp, len(ts), min(lv) if lv else "-", max(lv) if lv else "-",
                                            ("; DOUBLE " + ", ".join(dbl)) if dbl else ""))
    a("")
    a("## Bosses")
    if not pack["bosses"]:
        a("- none fought in this chapter's entries")
    for b in pack["bosses"]:
        a("- **%s** `%s` (%s, %s)%s, %s:" % (b["fight"], short(b["id"]), b["role"],
                                            "DOUBLE" if b["double"] else "single",
                                            (" badge %s" % b["badge"]["id"]) if b.get("badge") else "", b["ref"]))
        for p in b["party"]:
            a("  - %s Lv%d [%s] %s%s" % (short(p["species"]), p["level"], "/".join(p.get("types") or []),
                                         " ".join(short(m) for m in p.get("moves") or []),
                                         (" @" + short(p["held_item"])) if p.get("held_item") else ""))
    if pack["area_bosses_later"]:
        a("- Battled on these maps in a LATER entry: %s" % ", ".join(
            "%s (%s, %d variant%s, top Lv %d)" % (r["fight"], r["entry"], len(r["ids"]),
                                                   "" if len(r["ids"]) == 1 else "s", r["level_max"])
            for r in pack["area_bosses_later"]))
    a("")
    a("## Wild encounters (area maps, normal play)")
    if not pack["wild"]:
        a("- no wild table on the area maps")
    elif level >= 4:
        a("- %d tables on %s: in ch%d.json `wild` (species, rates and levels)" % (
            len(pack["wild"]), ", ".join(sorted({short(r["map"]) for r in pack["wild"]})), n))
    elif level >= 2:
        per = {}
        for r in pack["wild"]:
            tag = "".join([" REQUIRES %s" % r["requires"] if r["requires"] else "",
                           " IF %s" % r["condition"] if r["condition"] else ""])
            lo = min(m["min_level"] for m in r["species"]) if r["species"] else "-"
            hi = max(m["max_level"] for m in r["species"]) if r["species"] else "-"
            per.setdefault(short(r["map"]), []).append("%s%s %s L%s-%s" % (
                r["method"], tag, " ".join(m["name"] for m in r["species"]), lo, hi))
        for mp, parts in sorted(per.items()):
            a("- %s: %s" % (mp, "; ".join(parts)))
    else:
        for r in pack["wild"]:
            tag = "".join([" REQUIRES %s" % r["requires"] if r["requires"] else "",
                           " IF %s" % r["condition"] if r["condition"] else ""])
            a("- %s %s (rate %s)%s: %s" % (short(r["map"]), r["method"], r["encounter_rate"], tag, ", ".join(
                "%s %d%% L%d-%d" % (m["name"], m["chance_pct"], m["min_level"], m["max_level"])
                for m in r["species"])))
    a("")
    a("## HM moves")
    if not pack["hms"]:
        a("- no field move is needed by, or unlocked in, this chapter (campaign.json needs.field_moves; badges won)")
    for h in pack["hms"]:
        a("- %s (%s, badge %s, %s): %s. %d species learn it; met wild here: %s" % (
            h["move"], h["hm"], h["badge"], h["badge_ref"], h["why"], h["learners_count"],
            ", ".join(short(s) for s in h["learners_met_wild_here"]) or "none"))
    a("")
    a("## LOAD-BEARING CLAIMS (for the adversarial agent: refute each against the pinned decomp)")
    for c in pack["claims"]:
        a("%d. [%s] %s%s" % (c["n"], c["kind"], c["claim"], (" (source: %s)" % c["source"]) if c["source"] else ""))
    a("")
    return "\n".join(L)


def render_within_cap(pack, cap):
    """The full .md, or, when that is over the cap, the least-summarised rendering that fits (SUMMARY_LEVELS, one
    level at a time). The cap never refuses a chapter by itself: only a page whose load-bearing part alone is over the
    cap comes back over it, and check_md_size stops that one."""
    md = render_md(pack)
    full = len(md.encode("utf-8"))
    level = 0
    while len(md.encode("utf-8")) > cap and level < len(SUMMARY_LEVELS) - 1:
        level += 1
        md = render_md(pack, summary_of=full, level=level)
    return md


def dump_json(pack):
    return json.dumps(pack, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


def generate_loaded(chapter, data, hashes, pin, md_cap, verified, check_src):
    """(json text, md text) for one chapter from loaded inputs. main runs check_pins and verify_inputs first and passes
    verify_inputs' record as `verified`; every other guard runs here. `data`/`hashes` are load_inputs' reading (the
    pack is built from it); `check_src` is read_inputs_for_check's separate reading of the same files (the pack is
    checked against it). (The selftest calls this in-process with a stub record to reach the guards that sit behind
    verify_world; such a page says NOT VERIFIED in its header.)"""
    pack = build_pack(chapter, data, hashes, pin, sha256_lf(os.path.abspath(__file__)), verified)
    expected, problems = expected_selection(chapter, check_src)
    refuse_incomplete(problems + check_complete(pack, expected), chapter)
    md = render_within_cap(pack, md_cap)
    refuse_incomplete(check_md_complete(pack, md, expected, md_cap), chapter)
    check_md_size(md, md_cap)
    return dump_json(pack), md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("chapters", nargs="*", type=int)
    ap.add_argument("--all", action="store_true", help="every chapter campaign.json has")
    ap.add_argument("--world", default=WORLD_DEFAULT, help="folder of campaign/maps/trainers/bosses.json")
    ap.add_argument("--seasoned", default=SEASONED_DEFAULT, help="folder of KB1's encounters/learnsets/species.json")
    ap.add_argument("--pin", default=PIN_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--md-cap", type=int, default=MD_CAP_DEFAULT, help="bytes (default 12 KB)")
    ap.add_argument("--check", action="store_true", help="compare with the files in --out; write nothing")
    ap.add_argument("--decomp", help="the pinned decomp clone verify_world reads (default: its own default)")
    ap.add_argument("--verify-world", default=VERIFY_WORLD, help="the verifier (default ai_player/gates/verify_world.py)")
    ap.add_argument("--verify-timeout", type=float, default=VERIFY_TIMEOUT_S,
                    help="seconds verify_world may take before the run refuses (default %d)" % VERIFY_TIMEOUT_S)
    args = ap.parse_args(argv)
    pin = read_pin(args.pin)
    data, hashes = load_inputs(args.world, args.seasoned)
    chapters = list(args.chapters) + (campaign_chapters(data) if args.all else [])
    if not chapters:
        ap.error("name at least one chapter, or --all")
    try:
        check_pins(data, pin)
        verified = verify_inputs(args.world, args.decomp, args.verify_world, args.verify_timeout)
    except PackError as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        return 2
    # the checking side reads the files again with its own loader (never load_inputs' dict: fix round 3)
    check_src = read_inputs_for_check(args.world, args.seasoned)
    # every chapter is generated (and checked) in memory first, so a refusal writes NOTHING, not a partial set
    made = []
    for n in chapters:
        try:
            made.append((n,) + generate_loaded(n, data, hashes, pin, args.md_cap, verified, check_src))
        except PackError as exc:
            print("REFUSED ch%d: %s" % (n, exc), file=sys.stderr)
            return 2
    drift = 0
    for n, js, md in made:
        for ext, text in (("json", js), ("md", md)):
            path = os.path.join(args.out, "ch%d.%s" % (n, ext))
            if args.check:
                try:
                    with open(path, "rb") as f:
                        have = f.read().replace(b"\r\n", b"\n").decode("utf-8")
                except OSError:
                    have = None
                if have != text:
                    print("DIFFERS: %s" % path)
                    drift += 1
            else:
                os.makedirs(args.out, exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
        print("ch%d: %d trainers, %d bosses, %d claims, md %d bytes%s" % (
            n, len(json.loads(js)["trainers"]), len(json.loads(js)["bosses"]), len(json.loads(js)["claims"]),
            len(md.encode("utf-8")), " (trainers summarised)" if SUMMARY_MARK in md else ""))
    if args.check:
        print("CHECK: %s" % ("PASS" if not drift else "%d file(s) differ" % drift))
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
