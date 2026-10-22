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
  links     each area map's connections and warps, each warp classified by whether its arrival warp leads back
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
generator's own sha256, and the decomp pin, so a stale pack is visible. Hashes are taken over the file's bytes with
CRLF normalised to LF, because this PC checks text out with CRLF (core.autocrlf) and another may not; `--check` reads
the committed packs the same way. (`.gitattributes` also pins the packs to LF.)

THE 12 KB .md CAP NEVER REFUSES A CHAPTER (fix round, 2026-10-22). The .md is rendered in full; when that is over the
cap it is rendered again with the ORDINARY trainers (single battles) summarised per map: their count, level range and
species set, pointing to the .json for the full list. Only if that is still over, deeper levels follow one at a time
(SUMMARY_LEVELS: wild tables without rates; warps and neighbour maps counted; trainer and wild species and neighbour
trainers left to the .json). On the 2026-10-22 inputs chapters 9 and 11 use level 1, 14 level 2 and 13 level 4 (its
full page is 21,164 bytes and level 1 left 15,096; it ends at 12,117). Everything load-bearing stays in full at every
level: the bosses and their teams, the HM moves, every double battle, each area map's links line, and the
LOAD-BEARING CLAIMS (which carry the progress flags and one-way links). check_md_complete proves that on every .md
it writes; only a page still over the cap at the deepest level makes check_md_size stop the run.

COMPLETENESS (fix round, 2026-10-22). WHY: the first build could drop a boss, an HM, a ring-map trainer or a link and
still exit 0, and its ch4 .md said both "boss ROXANNE" and "none fought". Now every pack is checked against
expected_selection, a SECOND reading of the inputs that shares no code with build_pack (it re-derives the ring, the
trainers, the bosses, the links, the warp kinds, the wild rows from the slots, the HM learners and the claims each
of those requires). Any difference, missing OR extra, stops the run with exit 2 naming it. The same reading also
cross-checks the inputs against each other, so an item lost from one file is caught by another file that names it:
  - a boss an entry names (`boss`, `fights`, or bosses.json `entry`) with no bosses.json row;
  - a bosses.json `battled_on` map on the ring with no trainer object, trigger or script for that boss;
  - a badge won in the chapter (or a field move an entry needs) with no campaign.json `field_move_badges` row;
  - a connection with no connection back (all 148 connections in maps.json at the pin are mirrored, so a one-sided
    one is far likelier an extraction loss than a real one-way edge; the run stops instead of publishing it);
  - a connection or warp to a map maps.json does not hold.
LIMIT, stated so nobody reads more into it: an ordinary trainer or a warp deleted from maps.json is named by no other
input, so only W3 (milestones.json's table, chapters 1-4) can notice it; the checker catches a GENERATOR that drops one.

THE GUARDS (each stops the run with exit 2 and a message naming what it found; tools/story-dev/selftest_chapter_pack.py
feeds each a broken input beside a healthy one, and its --mutants mode deletes each CALL in a scratch copy and must see
a failing arm):
  check_pins             an input whose `_source` pin differs from tools/decomp.pin (a pack mixing two decomps)
  refuse_empty_chapter   a chapter with no campaign entry (a typo'd chapter must not write an empty pack)
  refuse_route_keys      a key named x, y, route, path, steps or coords inside the chapter's campaign entries
  resolve_maps           an area map that maps.json does not hold
  join_trainer           a trainer symbol on a map that trainers.json does not hold
  script_label           a trainer object with neither `script` nor `label` (a battle that cannot be cited)
  refuse_incomplete      check_complete's and check_md_complete's findings (above)
  check_md_size          a rendered .md still over the cap after summarising
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))
WORLD_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "world")
SEASONED_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
PIN_DEFAULT = os.path.join(REPO, "tools", "decomp.pin")
OUT_DEFAULT = os.path.join(REPO, "PROJECT KNOWLEDGE", "chapter-packs")

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


def classify_warp(src_id, warp, maps_by_id):
    dest = warp["dest_map"]
    if dest == DYNAMIC:
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


def build_pack(chapter, data, hashes, pin, generator_sha):
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
            if w["kind"] in ("asymmetric", "unknown"):
                out.append(("one_way_warp", "%s warp %d -> %s: %s" % (short(row["map"]), w["warp"],
                                                                      short(w["dest_map"]), w["why"]), "maps.json warps"))
        for c in row["connections"]:
            if not c["connects_back"]:
                out.append(("one_way_warp", "%s connects %s to %s, which has no connection back" % (
                    short(row["map"]), c["dir"], short(c["map"])), "maps.json connections"))
    for w in pack["warps_in"]:
        n_warps += 1
        if w["kind"] in ("asymmetric", "unknown"):
            out.append(("one_way_warp", "%s warp %d -> %s: %s" % (short(w["from"]), w["warp"], short(w["dest_map"]),
                                                                  w["why"]), "maps.json warps"))
    if not any(c[0] == "one_way_warp" for c in out):
        out.append(("one_way_warp", "none of the %d warps touching the area maps is one-way by warp data (ledges, "
                                    "holes and scripted movement are NOT modelled)" % n_warps, "maps.json warps"))
    return [{"n": i + 1, "kind": k, "claim": c, "source": s} for i, (k, c, s) in enumerate(out)]


# ---------------------------------------------------------------- the independent completeness check
def expected_selection(chapter, data):
    """A SECOND reading of the inputs for chapter `chapter`, sharing no code with build_pack, ring, links,
    trainers_on, wild, hm_learners or claims, so a bug or a deleted line in those cannot hide here too.
    Returns (expected, problems): `expected` is what a complete pack must hold; `problems` are the inputs disagreeing
    with each other (an item one file names and another lost), each a finding on its own."""
    camp = data["ai_player/knowledge/world/campaign.json"]
    every_map = data["ai_player/knowledge/world/maps.json"]["maps"]
    tdata = {t["symbol"]: t for t in data["ai_player/knowledge/world/trainers.json"]["trainers"]}
    brows = data["ai_player/knowledge/world/bosses.json"]["bosses"]
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
    for sp in data["ai_player/knowledge/seasoned/learnsets.json"]["species"]:
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
    def kind_of(src, w):
        target = w["dest_map"]
        if target == DYNAMIC:
            return "dynamic"
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
    for row in data["ai_player/knowledge/seasoned/encounters.json"]["maps"]:
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
                "entries": mine}
    return expected, problems


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
           for i, d, _k, kind in ws if kind in ("asymmetric", "unknown")]
    odd += ["%s warp %d -> %s" % (short(s), i, short(d)) for s, i, d, kind in expected["warps_in"]
            if kind in ("asymmetric", "unknown")]
    odd += ["%s connects %s to %s, which has no connection back" % (short(a), dr, short(m))
            for a, cs in sorted(expected["connections"].items()) for dr, m, back in cs if not back]
    for text in odd:
        need("one_way_warp", text)
    if not odd:
        total = sum(len(ws) for ws in expected["warps"].values()) + len(expected["warps_in"])
        need("one_way_warp", "none of the %d warps" % total)
    return out


def check_md_complete(pack, md):
    """The .md must carry every LOAD-BEARING item of the pack in full, in either rendering: each boss with its whole
    team in order, each HM move, each double battle (with its defeat flag), each area map's links line, and every
    claim verbatim; in a full rendering every area trainer by name and flag, in a summarised one each map's count.
    It must never say 'none fought' when the chapter has a boss. Returns the findings."""
    out = []
    lines = md.split("\n")
    summarised = SUMMARY_MARK in md
    if pack["bosses"] and "none fought" in md:
        out.append("md says 'none fought' but the pack has %d boss row(s)" % len(pack["bosses"]))
    for b in pack["bosses"]:
        head = [i for i, ln in enumerate(lines) if ln.startswith("- **%s** `%s` " % (b["fight"], short(b["id"])))]
        if len(head) != 1:
            out.append("md boss %s: %d header lines (want 1)" % (b["id"], len(head)))
            continue
        team = lines[head[0] + 1: head[0] + 1 + len(b["party"])]
        for k, p in enumerate(b["party"]):
            want = "  - %s Lv%d " % (short(p["species"]), p["level"])
            if k >= len(team) or not team[k].startswith(want):
                out.append("md boss %s mon %d (%s) missing or out of order" % (b["id"], k + 1, want.strip()))
    for h in pack["hms"]:
        if not any(ln.startswith("- %s (%s, badge " % (h["move"], h["hm"])) for ln in lines):
            out.append("md HM %s missing" % h["move"])
    for m in pack["maps"]:
        if m["role"] == "area" and not any(ln.startswith("- **%s** (" % short(m["id"])) for ln in lines):
            out.append("md links line for %s missing" % m["id"])
    for t in pack["trainers"]:
        named = any("`%s`" % short(t["symbol"]) in ln and "flag %d," % t["flag"] in ln for ln in lines)
        if t["in_area"] and (t["double"] or not summarised) and not named:
            out.append("md trainer %s (flag %d%s) missing" % (t["symbol"], t["flag"], ", DOUBLE" if t["double"] else ""))
    if summarised:
        per_map = {}
        for t in pack["trainers"]:
            if t["in_area"] and not t["double"]:
                mp = short(t["seen"][0]["map"])
                per_map[mp] = per_map.get(mp, 0) + 1
        for mp, n in sorted(per_map.items()):
            if not any(ln.startswith("- %s: %d ordinary trainer" % (mp, n)) for ln in lines):
                out.append("md summary line for %s (%d ordinary trainers) missing" % (mp, n))
    for c in pack["claims"]:
        text = "%d. [%s] %s" % (c["n"], c["kind"], c["claim"])
        if not any(ln.startswith(text) for ln in lines):
            out.append("md claim %d [%s] missing" % (c["n"], c["kind"]))
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
                                                          pack["generator"]["sha256"]))
    a("")
    a("| source | sha256 |")
    a("|---|---|")
    for k, v in pack["sources"].items():
        a("| `%s` | `%s` |" % (k, v))
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
            g["odd"] += w["kind"] in ("asymmetric", "unknown")
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


def generate_loaded(chapter, data, hashes, pin, md_cap):
    """(json text, md text) for one chapter from loaded inputs (main runs check_pins first); every other guard runs
    here."""
    pack = build_pack(chapter, data, hashes, pin, sha256_lf(os.path.abspath(__file__)))
    expected, problems = expected_selection(chapter, data)
    refuse_incomplete(problems + check_complete(pack, expected), chapter)
    md = render_within_cap(pack, md_cap)
    refuse_incomplete(check_md_complete(pack, md), chapter)
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
    args = ap.parse_args(argv)
    pin = read_pin(args.pin)
    data, hashes = load_inputs(args.world, args.seasoned)
    chapters = list(args.chapters) + (campaign_chapters(data) if args.all else [])
    if not chapters:
        ap.error("name at least one chapter, or --all")
    try:
        check_pins(data, pin)
    except PackError as exc:
        print("REFUSED: %s" % exc, file=sys.stderr)
        return 2
    drift = 0
    for n in chapters:
        try:
            js, md = generate_loaded(n, data, hashes, pin, args.md_cap)
        except PackError as exc:
            print("REFUSED ch%d: %s" % (n, exc), file=sys.stderr)
            return 2
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
