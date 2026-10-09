"""TEACHER SIDE (build step 4): extract the GAME FACTS a person knows into the AI's own knowledge files.

    py -3.12 ai_player/gates/extract_knowledge.py            # writes ai_player/knowledge/{types,moves,species}.json
    py -3.12 ai_player/gates/extract_knowledge.py --check    # exits 1 if a written file differs from a fresh extraction

WHY (USER RULING 35, design draft §3 "How the bot teaches it": "`modules/data/types.json`, `moves.json`,
`species.json` -> type chart, move table with recoil class, base stats ... the battle decider and catch logic (game facts,
not bot logic)"): a person who plays Pokemon knows that Water beats Rock, that TAKE DOWN hurts its user, that MUDKIP is a
Water type and that a ZIGZAGOON is easy to catch. Those are FACTS of the game, not the bot's decisions, so the bot's data
files may teach them: this script READS the bot's `sandbox-pokebot/modules/data/*.json` (never its code) and WRITES the
AI's own files, `ai_player/knowledge/*.json`, each carrying its provenance (the source file and its sha256). The play loop
reads only those files (`ai_player/knowledge/facts.py`); it never reads the bot's data or imports the bot.

WHAT IS NOT EXTRACTED, ON PURPOSE: learnsets, evolution levels, encounter tables, trainer parties and the bot's own
tables of decisions. A person meets those by playing (or the coach tells them, later steps); the battle decider must not
know what the foe will do next or what a move it has never seen does to its own Pokemon beyond the move's printed facts.

THE RECOIL FACTS (the user's pillar 3: "account for RECOIL damage when choosing moves"), checked against pret/pokeemerald
by `gates/verify_knowledge.py`:
  * EFFECT_RECOIL (Take Down, Submission, Struggle): `MOVE_EFFECT_RECOIL_25`, the user loses 1/4 of the HP it dealt
    (`src/battle_script_commands.c` SetMoveEffect: `gBattleMoveDamage = (gHpDealt) / 4`, at least 1);
  * EFFECT_DOUBLE_EDGE (Double-Edge, Volt Tackle): `MOVE_EFFECT_RECOIL_33`, 1/3 of the HP dealt (`gHpDealt / 3`);
  * EFFECT_RECOIL_IF_MISS (Jump Kick, Hi Jump Kick): on a MISS the user takes half the damage the move would have dealt,
    capped at half the TARGET's max HP (`Cmd_manipulatedamage` DMG_RECOIL_FROM_MISS: `/= 2`, then
    `if (gBattleMons[gBattlerTarget].maxHP / 2 < gBattleMoveDamage) gBattleMoveDamage = maxHP / 2`);
  * EFFECT_EXPLOSION (Selfdestruct, Explosion): the user faints.
Gen 3's physical / special split is by TYPE (`include/battle.h` IS_TYPE_PHYSICAL: below TYPE_MYSTERY), so a move's
category is its type's.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "sandbox-pokebot" / "modules" / "data"
OUT = REPO / "ai_player" / "knowledge"

#: Gen 3: a move's category is its TYPE's (`include/battle.h` IS_TYPE_PHYSICAL(type) = type < TYPE_MYSTERY; the types
#: below `???` are physical, the ones above it special).
PHYSICAL_TYPES = ("Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel")
SPECIAL_TYPES = ("Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark")
#: The recoil class of each effect (module docstring has the decomp lines).
RECOIL = {
    "RECOIL": {"kind": "of_damage_dealt", "fraction": 0.25, "source": "MOVE_EFFECT_RECOIL_25: gHpDealt / 4 (at least 1)"},
    "DOUBLE_EDGE": {"kind": "of_damage_dealt", "fraction": 1 / 3, "source": "MOVE_EFFECT_RECOIL_33: gHpDealt / 3 (at least 1)"},
    "RECOIL_IF_MISS": {"kind": "if_it_misses", "fraction": 0.5, "cap": "half the target's max HP",
                       "source": "DMG_RECOIL_FROM_MISS: half the damage it would have dealt, at most targetMaxHP / 2"},
}
SELF_KO = ("EXPLOSION",)
#: Effects that deal damage but not by the base-power formula (a person learns these as "always N HP" or "depends").
FIXED_DAMAGE = ("SONICBOOM", "DRAGON_RAGE", "LEVEL_DAMAGE", "PSYWAVE", "SUPER_FANG", "ENDEAVOR", "COUNTER", "MIRROR_COAT",
                "BIDE", "OHKO")
TWO_TURN = ("RAZOR_WIND", "SOLAR_BEAM", "SKULL_BASH", "SKY_ATTACK", "SEMI_INVULNERABLE", "FUTURE_SIGHT")
RECHARGE = ("RECHARGE",)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance(name: str) -> dict:
    path = SOURCE / name
    return {
        "source": f"sandbox-pokebot/modules/data/{name} (the bot's game-fact data, read as teaching material: RULING 35)",
        "source_sha256": sha(path),
        "extracted_by": "ai_player/gates/extract_knowledge.py",
        "verified_by": "ai_player/gates/verify_knowledge.py (every entry against pret/pokeemerald through `gh api`)",
    }


def types() -> dict:
    data = json.loads((SOURCE / "types.json").read_text(encoding="utf-8"))
    names = [t["name"] for t in data]
    chart = {t["name"]: {k: float(v) for k, v in sorted(t["effectiveness"].items())} for t in data}
    return {"provenance": provenance("types.json"),
            "what": "chart[attacking type][defending type] = the damage multiplier (missing = 1.0); a dual type multiplies "
                    "both. Includes Normal and Fighting against Ghost (0), which Foresight / Odor Sleuth lift.",
            "types": names, "physical_types": list(PHYSICAL_TYPES), "special_types": list(SPECIAL_TYPES), "chart": chart}


def moves() -> dict:
    data = json.loads((SOURCE / "moves.json").read_text(encoding="utf-8"))
    out = {}
    for move in data:
        name = move["name"]
        if name == "-":
            continue
        effect = move["effect"]
        never_misses = effect == "ALWAYS_HIT" or move["accuracy"] in (0, 1) and isinstance(move["accuracy"], int)
        accuracy = 100 if never_misses else int(round(float(move["accuracy"]) * 100))
        out[name] = {
            "type": move["type"],
            "power": move["base_power"],
            "accuracy": accuracy,
            "never_misses": bool(never_misses),
            "pp": move["pp"],
            "effect": effect,
            "priority": move["priority"],
            "target": move["target"],
            "makes_contact": move["makes_contact"],
            "category": "status" if move["base_power"] == 0 else ("physical" if move["type"] in PHYSICAL_TYPES else "special"),
            "recoil": RECOIL.get(effect),
            "self_ko": effect in SELF_KO,
            "fixed_damage": effect in FIXED_DAMAGE,
            "two_turn": effect in TWO_TURN,
            "recharge": effect in RECHARGE,
        }
    return {"provenance": provenance("moves.json"),
            "what": "every move by the name the game shows: type, power, accuracy (percent; never_misses for the moves that "
                    "skip the check), PP, the effect, the Gen-3 category (by type), the RECOIL class, self-KO, fixed "
                    "damage, two-turn and recharge moves",
            "moves": out}


def species() -> dict:
    data = json.loads((SOURCE / "species.json").read_text(encoding="utf-8"))
    out = {}
    for entry in data:
        name = entry["name"]
        if not name.strip("?") or name in out:
            continue  # the table's placeholders ("?", "??????????": no species of the game) and repeats
        base = entry["base_stats"]
        out[name] = {
            "dex": entry["national_dex_number"],
            "types": list(dict.fromkeys(entry["types"])),
            "base": {"hp": base["hp"], "attack": base["attack"], "defense": base["defence"], "speed": base["speed"],
                     "sp_attack": base["special_attack"], "sp_defense": base["special_defence"]},
            "catch_rate": entry["catch_rate"],
            "exp_yield": entry["base_experience_yield"],
            "growth": entry["level_up_type"],
        }
    return {"provenance": provenance("species.json"),
            "what": "every species by the name the game shows: its types, base stats, catch rate, experience yield and "
                    "growth rate (what a person reads in a Pokedex or a strategy guide; no learnsets, no evolutions)",
            "species": out}


def render(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if a written file differs from a fresh extraction")
    args = parser.parse_args()
    files = {"types.json": types(), "moves.json": moves(), "species.json": species()}
    status = 0
    for name, obj in files.items():
        path = OUT / name
        text = render(obj)
        if args.check:
            same = path.exists() and path.read_text(encoding="utf-8") == text
            print(f"[KNOWLEDGE] {name}: {'up to date' if same else 'DIFFERS from a fresh extraction'}")
            status |= 0 if same else 1
            continue
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        count = len(obj.get("chart") or obj.get("moves") or obj.get("species"))
        print(f"[KNOWLEDGE] wrote {path.relative_to(REPO).as_posix()}: {count} entries, source sha256 {obj['provenance']['source_sha256'][:16]}")
    return status


if __name__ == "__main__":
    sys.exit(main())
