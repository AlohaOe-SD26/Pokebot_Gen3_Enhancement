#!/usr/bin/env python3
"""A5 chapter packs (spec S3-4): one chapter's static world, generated from KB1 + KB2, for a reader and for W7.

    py -3.12 tools/make_chapter_pack.py 4              # writes PROJECT KNOWLEDGE/chapter-packs/ch4.json + ch4.md
    py -3.12 tools/make_chapter_pack.py 1 2 3 4        # several chapters
    py -3.12 tools/make_chapter_pack.py 1 2 3 4 --check  # regenerates in memory; exit 1 if a committed pack differs

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
  trainers  every trainer object / trigger on those maps (maps.json, joined to trainers.json): single or double, sight,
            party levels min..max (and the full list), species, the defeat flag NUMBER
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
CRLF normalised to LF, because this PC checks text out with CRLF (core.autocrlf) and another may not.

THE GUARDS (each stops the run with exit 2 and a message naming what it found; tools/selftest_chapter_pack.py feeds
each a broken input beside a healthy one, and its --mutants mode deletes each CALL in a scratch copy and must see a
failing arm):
  check_pins             an input whose `_source` pin differs from tools/decomp.pin (a pack mixing two decomps)
  refuse_empty_chapter   a chapter with no campaign entry (a typo'd chapter must not write an empty pack)
  refuse_route_keys      a key named x, y, route, path, steps or coords inside the chapter's campaign entries
  resolve_maps           an area map that maps.json does not hold
  join_trainer           a trainer symbol on a map that trainers.json does not hold
  check_md_size          a rendered .md over the cap (default 12 KB, the spec's "at most ~12 KB")
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


def check_md_size(text, cap):
    size = len(text.encode("utf-8"))
    if size > cap:
        raise PackError("the .md is %d bytes, over the %d-byte cap" % (size, cap))
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
    return sorted(out - area)


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
    """Every trainer battled by an object or trigger on these maps, deduplicated by symbol, with each sighting."""
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
                seen = {"map": mid, "source": obj["source"], "script": obj["script"]}
                for k in ("trainer_type", "sight", "x", "y"):
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


# ---------------------------------------------------------------- rendering
def render_md(pack):
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
    a("- Neighbours (one ring, %d): %s" % (len(nb), ", ".join(nb) or "-"))
    a("")
    a("## Trainers")
    a("EVERY trainer on the area maps, whether or not this chapter fights them (compare the levels with the entries' "
      "level band). Area maps: name, class, single/DOUBLE, sight, levels, team, defeat flag number.")
    for t in pack["trainers"]:
        if not t["in_area"]:
            continue
        s = t["seen"][0]
        sight = ("sight %s" % s["sight"]) if "sight" in s else ("a %s" % SEEN_AS.get(s["source"], s["source"]))
        a("- %s `%s` %s, %s, %s, Lv %s (%s), flag %d, on %s" % (
            t["name"] or "-", short(t["symbol"]), t["class"], "DOUBLE" if t["double"] else "single",
            sight, "/".join(str(x) for x in t["levels"]),
            " ".join(short(x) for x in t["species"]), t["flag"],
            ", ".join(sorted({short(x["map"]) for x in t["seen"]}))))
    outer = {}
    for t in pack["trainers"]:
        if not t["in_area"]:
            outer.setdefault(short(t["seen"][0]["map"]), []).append(t)
    if outer:
        a("")
        a("Neighbour maps (name, Lv min-max, D = double):")
        for mp, ts in sorted(outer.items()):
            a("- %s: %s" % (mp, ", ".join("%s %s-%s%s" % (short(t["symbol"]), t["level_min"], t["level_max"],
                                                          " D" if t["double"] else "") for t in ts)))
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
    for r in pack["wild"]:
        tag = "".join([" REQUIRES %s" % r["requires"] if r["requires"] else "",
                       " IF %s" % r["condition"] if r["condition"] else ""])
        a("- %s %s (rate %s)%s: %s" % (short(r["map"]), r["method"], r["encounter_rate"], tag, ", ".join(
            "%s %d%% L%d-%d" % (m["name"], m["chance_pct"], m["min_level"], m["max_level"]) for m in r["species"])))
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


def dump_json(pack):
    return json.dumps(pack, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


def generate(chapter, world, seasoned, pin_path, md_cap):
    """(json text, md text) for one chapter; every guard runs here."""
    pin = read_pin(pin_path)
    data, hashes = load_inputs(world, seasoned)
    check_pins(data, pin)
    pack = build_pack(chapter, data, hashes, pin, sha256_lf(os.path.abspath(__file__)))
    md = render_md(pack)
    check_md_size(md, md_cap)
    return dump_json(pack), md


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("chapters", nargs="+", type=int)
    ap.add_argument("--world", default=WORLD_DEFAULT, help="folder of campaign/maps/trainers/bosses.json")
    ap.add_argument("--seasoned", default=SEASONED_DEFAULT, help="folder of KB1's encounters/learnsets/species.json")
    ap.add_argument("--pin", default=PIN_DEFAULT)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--md-cap", type=int, default=MD_CAP_DEFAULT, help="bytes (default 12 KB)")
    ap.add_argument("--check", action="store_true", help="compare with the files in --out; write nothing")
    args = ap.parse_args(argv)
    drift = 0
    for n in args.chapters:
        try:
            js, md = generate(n, args.world, args.seasoned, args.pin, args.md_cap)
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
        print("ch%d: %d trainers, %d bosses, %d claims, md %d bytes" % (
            n, len(json.loads(js)["trainers"]), len(json.loads(js)["bosses"]), len(json.loads(js)["claims"]),
            len(md.encode("utf-8"))))
    if args.check:
        print("CHECK: %s" % ("PASS" if not drift else "%d file(s) differ" % drift))
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
