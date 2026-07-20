#!/usr/bin/env python3
"""
build_dex_data.py — DEX DATA Phase 2 assembler.

Reads the bot's shipped ROM-extracted JSON (species/moves/items/abilities/
types/natures) from modules/data/ and assembles two static, denormalized
datasets for the future Pokedex and Item-Dex tabs:

  modules/data/generated/pokedex_data.json   (386 real species)
  modules/data/generated/itemdex_data.json   (309 real items)

Only BOT-sourced fields are populated. Research-only fields (Phase 3) are left
as null and enumerated per-entry under "_phase3_gaps".

This is pure data assembly — no emulator, ROM, or GUI needed.

Run from the sandbox-pokebot directory:
    py -3.12 tools/build_dex_data.py

It prints a JSON validation report to stdout (counts, referential integrity,
sprite-existence, spot-checks) and writes the two datasets + does not itself
write the README (see modules/data/generated/README.md).
"""

from __future__ import annotations

import json
import os
import string
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent  # sandbox-pokebot/
DATA = ROOT / "modules" / "data"
OUT = DATA / "generated"
SPRITES = ROOT / "modules" / "web" / "static" / "sprites"
POKE_SPRITES = SPRITES / "pokemon"
POKE_ANIM = SPRITES / "pokemon-animated"
ITEM_SPRITES = SPRITES / "items"

PLACEHOLDER_NAMES = {"?", "??????????", "????????"}


# ---------------------------------------------------------------------------
# Name normalization (mirrors modules/files.make_string_safe_for_file_name)
# ---------------------------------------------------------------------------
_SAFE_ALLOWED = f"-_.()' {string.ascii_letters}{string.digits}"


def make_string_safe_for_file_name(base_string: str) -> str:
    result = ""
    for c in base_string:
        if c in _SAFE_ALLOWED:
            result += c
        elif c == "♂":  # ♂
            result += "_m"
        elif c == "♀":  # ♀
            result += "_f"
        elif c == "!":
            result += "em"
        elif c == "?":
            result += "qm"
        else:
            result += "_"
    return result


# Item icon filenames were authored by hand and do NOT always follow the
# name-safe rule (e.g. "Thunderstone" -> "Thunder Stone.png"). These overrides
# map an item's exact in-data name to its exact on-disk icon filename. The
# four "Rm. N Key" FR/LG Rocket-hideout keys have NO shipped icon.
ITEM_SPRITE_OVERRIDES = {
    "Guard Spec.": "Guard Spec.png",
    "Thunderstone": "Thunder Stone.png",
    "Exp. Share": "Exp Share.png",
    "King’s Rock": "Kings Rock.png",  # curly apostrophe
    "S.S. Ticket": "SS Ticket.png",
    "Go-Goggles": "Go-goggles.png",
    "Oak’s Parcel": "Oaks Parcel.png",
    "Tri-Pass": "Tri-pass.png",
    "MysticTicket": "Mysticticket.png",
    "AuroraTicket": "Auroraticket.png",
}

# Research-sourced gap fields left null in Phase 2.
POKEDEX_GAP_FIELDS = ["dex_artwork", "flavor_text", "height_m", "weight_kg", "category"]
ITEMDEX_GAP_FIELDS = ["map_locations", "mart_stock", "pickup_chance"]

# Gen-3 gender ratio (female threshold byte) -> human percentages.
GENDER_TABLE = {
    0: (100.0, 0.0),
    31: (87.5, 12.5),
    63: (75.0, 25.0),
    127: (50.0, 50.0),
    191: (25.0, 75.0),
    225: (12.5, 87.5),
    254: (0.0, 100.0),
}


def load(name: str):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def is_real_species(entry) -> bool:
    return (
        isinstance(entry, dict)
        and entry.get("name") not in PLACEHOLDER_NAMES
        and isinstance(entry.get("national_dex_number"), int)
        and 1 <= entry["national_dex_number"] <= 386
    )


def is_real_item(entry) -> bool:
    return isinstance(entry, dict) and entry.get("name") not in PLACEHOLDER_NAMES


def gender_info(raw: int) -> dict:
    if raw == 255:
        return {"genderless": True, "male_percent": None, "female_percent": None}
    if raw in GENDER_TABLE:
        m, f = GENDER_TABLE[raw]
    else:
        f = round(raw / 256 * 100, 1)
        m = round(100 - f, 1)
    return {"genderless": False, "male_percent": m, "female_percent": f}


def rel_sprite(path: Path) -> str:
    """Return the sprite path relative to the sprites root, forward-slashed."""
    return path.relative_to(SPRITES).as_posix()


# ---------------------------------------------------------------------------
# Main build
# ---------------------------------------------------------------------------
def build():
    species = load("species.json")
    moves = load("moves.json")
    items = load("items.json")
    abilities = load("abilities.json")
    types = load("types.json")
    _natures = load("natures.json")  # read for completeness / validation surface

    move_name = {i: m["name"] for i, m in enumerate(moves)}
    move_tmhm = {i: m.get("tm_hm") for i, m in enumerate(moves)}
    ability_names = {a["name"] for a in abilities if isinstance(a, dict)}
    type_names = {t["name"] for t in types if isinstance(t, dict)}

    items_by_index = {it["index"]: it for it in items if isinstance(it, dict)}
    items_by_name = {}
    for it in items:
        if is_real_item(it):
            items_by_name.setdefault(it["name"], it)

    real_species = sorted(
        (s for s in species if is_real_species(s)),
        key=lambda s: s["national_dex_number"],
    )
    # IMPORTANT: `family`, `evolves_from`, and evolution `target_species` are
    # ARRAY INDICES into species.json (Gen-3 internal species IDs), NOT national
    # dex numbers. (They coincide for Gen 1/2 mons but diverge for Hoenn.)
    index_to_species = {i: e for i, e in enumerate(species) if is_real_species(e)}

    def name_for_index(idx):
        e = index_to_species.get(idx)
        return e["name"] if e else None

    def ndex_for_index(idx):
        e = index_to_species.get(idx)
        return e["national_dex_number"] if e else None

    # On-disk sprite file sets (exact names) for existence checks.
    normal_files = set(os.listdir(POKE_SPRITES / "normal"))
    shiny_files = set(os.listdir(POKE_SPRITES / "shiny"))
    ncrop_files = set(os.listdir(POKE_SPRITES / "normal-cropped"))
    scrop_files = set(os.listdir(POKE_SPRITES / "shiny-cropped"))
    anim_n_files = set(os.listdir(POKE_ANIM / "normal"))
    anim_s_files = set(os.listdir(POKE_ANIM / "shiny"))

    # Animated gifs use a looser naming than the PNG battle sprites (e.g.
    # "Ho-oh.gif", "Farfetch'd.gif"). Build a fuzzy stem->filename index.
    def _norm(s: str) -> str:
        return s.lower().replace("’", "'").replace("_", "")

    anim_n_map = {_norm(os.path.splitext(f)[0]): f for f in anim_n_files}
    anim_s_map = {_norm(os.path.splitext(f)[0]): f for f in anim_s_files}
    item_files = set(os.listdir(ITEM_SPRITES))

    report = {
        "counts": {},
        "integrity": {
            "orphan_move_ids": [],
            "unresolved_abilities": [],
            "unresolved_types": [],
            "unresolved_evolution_targets": [],
            "unresolved_family_members": [],
            "unresolved_held_item_names": [],
            "unresolved_tmhm_links": [],
            "held_by_missing_species": [],
        },
        "sprites": {
            "species_missing_normal": [],
            "species_missing_shiny": [],
            "species_missing_cropped": [],
            "species_missing_animated": [],
            "items_missing_icon": [],
        },
        "spot_checks": {},
    }
    integ = report["integrity"]
    spr = report["sprites"]

    # ----- sprite resolvers -----
    def species_sprite_name(name: str) -> str:
        base = "Unown (P)" if name == "Unown" else name
        return make_string_safe_for_file_name(base)

    def resolve_species_sprites(name: str) -> dict:
        fn = species_sprite_name(name)
        png = fn + ".png"
        gif = fn + ".gif"
        result = {}
        # normal
        if png in normal_files:
            result["normal"] = rel_sprite(POKE_SPRITES / "normal" / png)
        else:
            result["normal"] = None
            spr["species_missing_normal"].append(name)
        # shiny
        if png in shiny_files:
            result["shiny"] = rel_sprite(POKE_SPRITES / "shiny" / png)
        else:
            result["shiny"] = None
            spr["species_missing_shiny"].append(name)
        # cropped normal
        if png in ncrop_files:
            result["normal_cropped"] = rel_sprite(POKE_SPRITES / "normal-cropped" / png)
        else:
            result["normal_cropped"] = None
            spr["species_missing_cropped"].append(name)
        # cropped shiny (bonus, no separate report bucket)
        result["shiny_cropped"] = (
            rel_sprite(POKE_SPRITES / "shiny-cropped" / png) if png in scrop_files else None
        )
        # animated — try exact safe name, then a fuzzy (case/apostrophe) match
        keys = [_norm(fn), _norm(name)]
        an = next((anim_n_map[k] for k in keys if k in anim_n_map), None)
        if an:
            result["animated_normal"] = rel_sprite(POKE_ANIM / "normal" / an)
        else:
            result["animated_normal"] = None
            spr["species_missing_animated"].append(name)
        as_ = next((anim_s_map[k] for k in keys if k in anim_s_map), None)
        result["animated_shiny"] = rel_sprite(POKE_ANIM / "shiny" / as_) if as_ else None
        return result

    def resolve_item_sprite(name: str):
        # 1) manual override map
        if name in ITEM_SPRITE_OVERRIDES:
            fn = ITEM_SPRITE_OVERRIDES[name]
            if fn in item_files:
                return rel_sprite(ITEM_SPRITES / fn), True
        # 2) raw name
        if (name + ".png") in item_files:
            return rel_sprite(ITEM_SPRITES / (name + ".png")), True
        # 3) name-safe normalization
        safe = make_string_safe_for_file_name(name) + ".png"
        if safe in item_files:
            return rel_sprite(ITEM_SPRITES / safe), True
        return None, False

    # ----- learnset resolver -----
    def resolve_learnset(ls: dict, owner: str) -> dict:
        out = {"level_up": [], "tm_hm": [], "tutor": [], "egg": []}
        # level_up is {move_id: level}
        lv = []
        for mid, level in ls.get("level_up", {}).items():
            mid = int(mid)
            if mid not in move_name:
                integ["orphan_move_ids"].append({"species": owner, "bucket": "level_up", "id": mid})
                continue
            lv.append((level, mid))
        lv.sort(key=lambda x: (x[0], x[1]))
        out["level_up"] = [{"level": l, "move": move_name[m]} for l, m in lv]
        # tm_hm list of move ids
        for mid in ls.get("tm_hm", []):
            if mid not in move_name:
                integ["orphan_move_ids"].append({"species": owner, "bucket": "tm_hm", "id": mid})
                continue
            out["tm_hm"].append({"tm_hm": move_tmhm.get(mid), "move": move_name[mid]})
        # tutor / egg lists of move ids -> names
        for bucket in ("tutor", "egg"):
            for mid in ls.get(bucket, []):
                if mid not in move_name:
                    integ["orphan_move_ids"].append({"species": owner, "bucket": bucket, "id": mid})
                    continue
                out[bucket].append(move_name[mid])
        return out

    def resolve_evolution(e: dict, owner: str) -> dict:
        method = e["method"]
        param = e.get("method_param", 0)
        target_idx = e.get("target_species")  # array index (internal species id)
        target = name_for_index(target_idx)
        if target is None:
            integ["unresolved_evolution_targets"].append(
                {"species": owner, "target_index": target_idx}
            )
        resolved_param = param
        if method in ("item", "trade_with_item"):
            it = items_by_index.get(param)
            resolved_param = it["name"] if it else param
        entry = {
            "method": method,
            "target": target,
            "target_national_dex": ndex_for_index(target_idx),
        }
        if method in ("item", "trade_with_item"):
            entry["item"] = resolved_param
        elif method.startswith("level") and param:
            entry["parameter"] = param
        return entry

    def resolve_held(hlist, game, owner):
        out = []
        for pair in hlist:
            name, prob = pair[0], pair[1]
            if name not in items_by_name:
                integ["unresolved_held_item_names"].append({"species": owner, "item": name})
            out.append({"item": name, "probability": prob, "game": game})
        return out

    # ----- build pokedex -----
    pokedex = []
    for s in real_species:
        name = s["name"]
        # ability / type integrity
        for ab in s.get("abilities", []):
            if ab not in ability_names:
                integ["unresolved_abilities"].append({"species": name, "ability": ab})
        for ty in s.get("types", []):
            if ty not in type_names:
                integ["unresolved_types"].append({"species": name, "type": ty})
        # family integrity — family members are ARRAY INDICES
        family_names = []
        for fidx in s.get("family", []):
            fn = name_for_index(fidx)
            if fn is None:
                integ["unresolved_family_members"].append({"species": name, "member_index": fidx})
            else:
                family_names.append(fn)

        bstats = s["base_stats"]
        entry = {
            "national_dex_number": s["national_dex_number"],
            "hoenn_dex_number": s.get("hoenn_dex_number"),
            "name": name,
            "localised_names": s.get("localised_names", {}),
            "types": s["types"],
            "abilities": s["abilities"],
            "base_stats": bstats,
            "bst": sum(bstats.values()),
            "ev_yield": s.get("ev_yield", {}),
            "catch_rate": s.get("catch_rate"),
            "base_experience_yield": s.get("base_experience_yield"),
            "gender_ratio": s.get("gender_ratio"),
            "gender": gender_info(s.get("gender_ratio", 255)),
            "egg_groups": s.get("egg_groups", []),
            "egg_cycles": s.get("egg_cycles"),
            "base_friendship": s.get("base_friendship"),
            "growth_rate": s.get("level_up_type"),
            "safari_zone_flee_probability": s.get("safari_zone_flee_probability"),
            "evolves_from": name_for_index(s.get("evolves_from"))
            if s.get("evolves_from")
            else None,
            "evolutions": [resolve_evolution(e, name) for e in s.get("evolutions", [])],
            "family": family_names,
            "held_items": (
                resolve_held(s.get("held_items_rse", []), "rse", name)
                + resolve_held(s.get("held_items_frlg", []), "frlg", name)
            ),
            "learnset": resolve_learnset(s.get("learnset", {}), name),
            "sprites": resolve_species_sprites(name),
            "_phase3_gaps": POKEDEX_GAP_FIELDS,
        }
        for g in POKEDEX_GAP_FIELDS:
            entry[g] = None
        pokedex.append(entry)

    # ----- build itemdex -----
    real_items = [it for it in items if is_real_item(it)]

    # held_by inversion: item name -> list of {species, game, probability}
    held_by = {}
    for s in real_species:
        for game, key in (("rse", "held_items_rse"), ("frlg", "held_items_frlg")):
            for pair in s.get(key, []):
                iname, prob = pair[0], pair[1]
                held_by.setdefault(iname, []).append(
                    {"species": s["name"], "game": game, "probability": prob}
                )
    # validate held_by species exist (they do by construction, but assert names resolve)
    real_species_names = {s["name"] for s in real_species}
    for iname, holders in held_by.items():
        for h in holders:
            if h["species"] not in real_species_names:
                integ["held_by_missing_species"].append(h["species"])

    # learnable_by: move_id -> list of species whose tm_hm learnset contains it
    tm_learnable = {}
    for s in real_species:
        for mid in s.get("learnset", {}).get("tm_hm", []):
            tm_learnable.setdefault(mid, []).append(s["name"])

    itemdex = []
    for it in real_items:
        name = it["name"]
        sprite, exists = resolve_item_sprite(name)
        if not exists:
            spr["items_missing_icon"].append({"index": it["index"], "name": name, "pocket": it["pocket"]})
        tm_move_id = it.get("tm_hm_move_id")
        tm_move = None
        learnable_by = None
        if tm_move_id is not None:
            if tm_move_id in move_name:
                tm_move = move_name[tm_move_id]
            else:
                integ["unresolved_tmhm_links"].append({"item": name, "move_id": tm_move_id})
            learnable_by = sorted(tm_learnable.get(tm_move_id, []))
        price = it.get("price")
        entry = {
            "index": it["index"],
            "name": name,
            "localised_names": it.get("localised_names", {}),
            "pocket": it.get("pocket"),
            "price": price,
            "sell_price": (price // 2) if isinstance(price, int) else None,
            "hold_effect": it.get("hold_effect"),
            "parameter": it.get("parameter"),
            "description": (it.get("localised_descriptions") or {}).get("E"),
            "localised_descriptions": it.get("localised_descriptions", {}),
            "tm_hm_move_id": tm_move_id,
            "tm_hm_move": tm_move,
            "sprite": sprite,
            "held_by": held_by.get(name, []),
            "learnable_by": learnable_by,
            "_phase3_gaps": ITEMDEX_GAP_FIELDS,
        }
        for g in ITEMDEX_GAP_FIELDS:
            entry[g] = None
        itemdex.append(entry)

    # ----- write outputs -----
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "pokedex_data.json", "w", encoding="utf-8") as f:
        json.dump(pokedex, f, ensure_ascii=False, indent=1)
    with open(OUT / "itemdex_data.json", "w", encoding="utf-8") as f:
        json.dump(itemdex, f, ensure_ascii=False, indent=1)

    # ----- counts + spot checks -----
    report["counts"] = {
        "species_array_entries": len(species),
        "pokedex_entries": len(pokedex),
        "items_array_entries": len(items),
        "itemdex_entries": len(itemdex),
        "item_placeholders_excluded": len(items) - len(itemdex),
        "moves": len(moves),
        "abilities": len(abilities),
        "types": len(types),
    }

    pk_by_name = {e["name"]: e for e in pokedex}
    it_by_name = {e["name"]: e for e in itemdex}
    spot_species = ["Unown", "Deoxys", "Wurmple", "Vaporeon", "Charmander", "Rayquaza", "Pikachu", "Metagross"]
    spot_items = ["TM26", "Oran Berry", "Master Ball", "HM01", "Devon Scope", "Leftovers", "Rare Candy", "Bicycle"]
    report["spot_checks"]["species"] = {
        n: pk_by_name.get(n) for n in spot_species if n in pk_by_name
    }
    report["spot_checks"]["items"] = {
        n: it_by_name.get(n) for n in spot_items if n in it_by_name
    }

    return report


def main():
    report = build()
    # Compact pass/fail summary at top for humans, then full JSON.
    integ = report["integrity"]
    spr = report["sprites"]
    integ_ok = all(len(v) == 0 for v in integ.values())
    sprite_species_ok = all(
        len(spr[k]) == 0 for k in ("species_missing_normal", "species_missing_shiny", "species_missing_cropped")
    )
    print("=" * 70)
    print("DEX DATA PHASE 2 — VALIDATION SUMMARY")
    print("=" * 70)
    print("counts:", json.dumps(report["counts"]))
    print("referential integrity:", "PASS" if integ_ok else "FAIL")
    for k, v in integ.items():
        if v:
            print(f"  {k}: {len(v)} -> {v[:5]}")
    print("species sprites (normal+shiny+cropped):", "PASS" if sprite_species_ok else "FAIL")
    for k in ("species_missing_normal", "species_missing_shiny", "species_missing_cropped", "species_missing_animated"):
        if spr[k]:
            print(f"  {k}: {spr[k]}")
    print(f"item icons missing: {len(spr['items_missing_icon'])}")
    for m in spr["items_missing_icon"]:
        print(f"  {m}")
    return 0 if (integ_ok and sprite_species_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
