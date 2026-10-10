"""TEST SIDE (build step 4): the AI's knowledge files against pret/pokeemerald, EVERY entry, through `gh api`.

    py -3.12 ai_player/gates/verify_knowledge.py [--evidence PATH]
    exit 0 = every checked fact agrees with the decomp; 1 = a mismatch (each printed); 2 = could not fetch

WHY: `gates/extract_knowledge.py` copies game facts out of the bot's data files (teaching material, RULING 35). The bot's
data is not the game: this script reads the GAME's source (pret/pokeemerald, `gh api repos/pret/pokeemerald/contents/...`)
and compares every entry the AI will act on, so a wrong fact in the bot's data cannot become a wrong decision of the AI
unnoticed (CLAUDE.md: a Gemini or bot fact is a NOTE until checked against the decomp).

WHAT IS COMPARED
  * types.json: the whole chart against `src/battle_main.c` gTypeEffectiveness (every triple, the Foresight section
    included), and every pair the decomp does NOT list must be 1.0 in ours;
  * moves.json: every move's type, power, accuracy (pret's 0 = "never misses"), PP, effect and priority against
    `src/data/battle_moves.h` gBattleMoves; and the recoil class of every recoil move against the decomp's effect;
  * species.json: every species' two types, six base stats, catch rate and experience yield against
    `src/data/pokemon/species_info.h` gSpeciesInfo;
  * the RECOIL arithmetic the decider uses, by the decomp's own lines in `src/battle_script_commands.c` (1/4 and 1/3 of the
    HP dealt, the miss recoil halved and capped at half the target's max HP) and `data/battle_scripts_1.s` (which effect
    sets which recoil).
FAULT HALF: `--plant` changes one fact of each file in memory (Water Gun's power, Mudkip's catch rate, Water vs Rock) and
must report exactly those three mismatches, so a PASS is not a comparator that cannot fail.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KNOWLEDGE = REPO / "ai_player" / "knowledge"
REPOSITORY = "pret/pokeemerald"
FILES = {
    "types": "src/battle_main.c",
    "moves": "src/data/battle_moves.h",
    "species": "src/data/pokemon/species_info.h",
    "commands": "src/battle_script_commands.c",
    "scripts": "data/battle_scripts_1.s",
}
MULTIPLIER = {"TYPE_MUL_NO_EFFECT": 0.0, "TYPE_MUL_NOT_EFFECTIVE": 0.5, "TYPE_MUL_NORMAL": 1.0, "TYPE_MUL_SUPER_EFFECTIVE": 2.0}


def fetch(path: str) -> str:
    result = subprocess.run(["gh", "api", f"repos/{REPOSITORY}/contents/{path}", "-H", "Accept: application/vnd.github.raw"],
                            capture_output=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"gh api {path}: {result.stderr.decode(errors='replace')[:300]}")
    return result.stdout.decode("utf-8", errors="replace")


def key(name: str) -> str:
    """A name as both sides spell it: 'Mud-slap' / MOVE_MUD_SLAP -> MUDSLAP; 'Nidoran♀' / SPECIES_NIDORAN_F -> NIDORANF."""
    name = name.replace("♀", "F").replace("♂", "M")
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def type_name(token: str) -> str:
    """TYPE_WATER -> Water; TYPE_MYSTERY -> ???"""
    token = token.removeprefix("TYPE_")
    return "???" if token == "MYSTERY" else token.capitalize()


def check_types(source: str, data: dict) -> list[str]:
    problems = []
    body = source.split("gTypeEffectiveness[", 1)[1].split("};", 1)[0]
    triples = re.findall(r"(TYPE_\w+),\s*(TYPE_\w+),\s*(TYPE_MUL_\w+)", body)
    listed = set()
    chart = data["chart"]
    for attack, defend, mul in triples:
        if attack in ("TYPE_FORESIGHT", "TYPE_ENDTABLE"):
            continue
        a, d = type_name(attack), type_name(defend)
        listed.add((a, d))
        ours = chart.get(a, {}).get(d, 1.0)
        if ours != MULTIPLIER[mul]:
            problems.append(f"types: {a} vs {d}: ours {ours}, pret {MULTIPLIER[mul]} ({mul})")
    for a, row in chart.items():
        for d, value in row.items():
            if (a, d) not in listed and value != 1.0:
                problems.append(f"types: {a} vs {d}: ours {value}, pret lists nothing (1.0)")
    return problems, len(triples)


def parse_blocks(source: str, prefix: str) -> dict[str, dict[str, str]]:
    """`[PREFIX_NAME] = { .field = value, ... }` blocks -> {NAME: {field: value}}."""
    blocks = {}
    for match in re.finditer(r"\[" + prefix + r"_(\w+)\]\s*=\s*\n\s*\{(.*?)\n\s*\},?\s*\n", source, re.S):
        fields = dict(re.findall(r"\.(\w+)\s*=\s*(\{[^}]*\}|[^,\n]+)", match.group(2)))
        blocks[match.group(1)] = {k: v.strip().rstrip(",") for k, v in fields.items()}
    return blocks


def check_moves(source: str, data: dict) -> tuple[list[str], int]:
    problems = []
    pret = {key(name): fields for name, fields in parse_blocks(source, "MOVE").items()}
    checked = 0
    for name, move in data["moves"].items():
        fields = pret.get(key(name))
        if fields is None:
            problems.append(f"moves: {name}: no MOVE_ entry in pret")
            continue
        checked += 1
        accuracy = int(fields["accuracy"])
        want = {
            "type": type_name(fields["type"]),
            "power": int(fields["power"]),
            "pp": int(fields["pp"]),
            "effect": fields["effect"].removeprefix("EFFECT_"),
            "priority": int(fields["priority"]),
            "target": fields["target"].removeprefix("MOVE_TARGET_"),
            "never_misses": accuracy == 0,
        }
        if accuracy != 0:
            want["accuracy"] = accuracy
        for field, value in want.items():
            if move[field] != value:
                problems.append(f"moves: {name}.{field}: ours {move[field]!r}, pret {value!r}")
    return problems, checked


def check_species(source: str, data: dict) -> tuple[list[str], int]:
    problems = []
    pret = {key(name): fields for name, fields in parse_blocks(source, "SPECIES").items()}
    checked = 0
    for name, entry in data["species"].items():
        fields = pret.get(key(name))
        if fields is None:
            problems.append(f"species: {name}: no SPECIES_ entry in pret")
            continue
        checked += 1
        pair = [type_name(t.strip()) for t in fields["types"].strip("{} ").split(",")]
        # compared as a SET: a dual type's damage multiplier does not depend on the order (the bot's file lists some in
        # another order than the decomp's `.types = { A, B }`)
        want_types = sorted(set(pair))
        want = {
            ("types",): want_types,
            ("base", "hp"): int(fields["baseHP"]), ("base", "attack"): int(fields["baseAttack"]),
            ("base", "defense"): int(fields["baseDefense"]), ("base", "speed"): int(fields["baseSpeed"]),
            ("base", "sp_attack"): int(fields["baseSpAttack"]), ("base", "sp_defense"): int(fields["baseSpDefense"]),
            ("catch_rate",): int(fields["catchRate"]), ("exp_yield",): int(fields["expYield"]),
        }
        for path, value in want.items():
            ours = entry
            for part in path:
                ours = ours[part]
            if path == ("types",):
                ours = sorted(set(ours))
            if ours != value:
                problems.append(f"species: {name}.{'.'.join(path)}: ours {ours!r}, pret {value!r}")
    return problems, checked


def check_recoil(commands: str, scripts: str, moves: dict) -> list[str]:
    """The recoil arithmetic by the decomp's own lines, and which effect sets which recoil."""
    problems = []
    lines = {
        "MOVE_EFFECT_RECOIL_25 is 1/4 of the HP dealt": r"case MOVE_EFFECT_RECOIL_25:.*?gBattleMoveDamage = \(gHpDealt\) / 4;",
        "MOVE_EFFECT_RECOIL_33 is 1/3 of the HP dealt": r"case MOVE_EFFECT_RECOIL_33:.*?gBattleMoveDamage = gHpDealt / 3;",
        "the miss recoil is half the damage, capped at half the TARGET's max HP":
            r"case DMG_RECOIL_FROM_MISS:\s*gBattleMoveDamage /= 2;.*?gBattleMons\[gBattlerTarget\]\.maxHP / 2\) < gBattleMoveDamage",
    }
    for what, pattern in lines.items():
        if not re.search(pattern, commands, re.S):
            problems.append(f"recoil: not found in battle_script_commands.c: {what}")
    scripts_lines = {
        "RECOIL": r"BattleScript_EffectRecoil::\s*setmoveeffect MOVE_EFFECT_RECOIL_25",
        "DOUBLE_EDGE": r"BattleScript_EffectDoubleEdge::\s*setmoveeffect MOVE_EFFECT_RECOIL_33",
        "RECOIL_IF_MISS": r"BattleScript_MoveMissedDoDamage::.*?manipulatedamage DMG_RECOIL_FROM_MISS",
    }
    fractions = {"RECOIL": 0.25, "DOUBLE_EDGE": 1 / 3, "RECOIL_IF_MISS": 0.5}
    for effect, pattern in scripts_lines.items():
        if not re.search(pattern, scripts, re.S):
            problems.append(f"recoil: battle_scripts_1.s does not set the {effect} recoil as expected")
        for name, move in moves["moves"].items():
            if move["effect"] == effect and (move["recoil"] is None or abs(move["recoil"]["fraction"] - fractions[effect]) > 1e-9):
                problems.append(f"recoil: {name} ({effect}) has recoil {move['recoil']}")
    for name, move in moves["moves"].items():
        if move["recoil"] is not None and move["effect"] not in fractions:
            problems.append(f"recoil: {name} has a recoil class but effect {move['effect']}")
    return problems


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plant", action="store_true", help="FAULT: three facts changed in memory must be found")
    parser.add_argument("--evidence", type=Path, help="also write the report here")
    args = parser.parse_args()
    lines: list[str] = []

    def say(line: str) -> None:
        print(line, flush=True)
        lines.append(line)

    try:
        sources = {name: fetch(path) for name, path in FILES.items()}
    except Exception as error:  # noqa: BLE001
        print(f"[VERIFY] could not fetch the decomp: {error}")
        return 2
    data = {name: json.loads((KNOWLEDGE / f"{name}.json").read_text(encoding="utf-8")) for name in ("types", "moves", "species")}
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from ai_player.gates.provenance import provenance  # the code line every evidence file names (`--check-evidence`)

    say(f"[VERIFY] code: {provenance(REPO)}")
    if args.plant:
        data["moves"]["moves"]["Water Gun"]["power"] = 45
        data["species"]["species"]["Mudkip"]["catch_rate"] = 46
        data["types"]["chart"]["Water"]["Rock"] = 1.0
    say(f"[VERIFY] pret/{REPOSITORY.split('/')[1]} via gh api: " + ", ".join(f"{p} ({len(sources[n])} bytes)" for n, p in FILES.items()))
    for name in ("types", "moves", "species"):
        say(f"[VERIFY] {name}.json provenance: {data[name]['provenance']['source']} sha256 {data[name]['provenance']['source_sha256']}")
    type_problems, triples = check_types(sources["types"], data["types"])
    move_problems, moves = check_moves(sources["moves"], data["moves"])
    species_problems, species = check_species(sources["species"], data["species"])
    recoil_problems = check_recoil(sources["commands"], sources["scripts"], data["moves"])
    say(f"[VERIFY] types: {triples} gTypeEffectiveness triples compared, {len(type_problems)} mismatches")
    say(f"[VERIFY] moves: {moves} of {len(data['moves']['moves'])} moves compared (type, power, accuracy, PP, effect, priority, "
        f"target), "
        f"{len(move_problems)} mismatches")
    say(f"[VERIFY] species: {species} of {len(data['species']['species'])} species compared (types, 6 base stats, catch rate, "
        f"exp yield), {len(species_problems)} mismatches")
    say(f"[VERIFY] recoil: the decomp's lines for 1/4, 1/3 and the capped miss recoil, and every recoil move's class: "
        f"{len(recoil_problems)} problems")
    samples = [("Water", "Rock"), ("Water", "Ground"), ("Ground", "Flying"), ("Normal", "Ghost"), ("Grass", "Water")]
    say("[VERIFY] samples: " + "; ".join(f"{a} vs {d} = {data['types']['chart'].get(a, {}).get(d, 1.0)}" for a, d in samples)
        + "; " + "; ".join(f"{m} {data['moves']['moves'][m]['type']} {data['moves']['moves'][m]['power']} acc {data['moves']['moves'][m]['accuracy']} recoil {(data['moves']['moves'][m]['recoil'] or {}).get('fraction')}"
                          for m in ("Take Down", "Double-edge", "Jump Kick", "Mud Shot", "Water Gun")))
    problems = type_problems + move_problems + species_problems + recoil_problems
    for problem in problems:
        say(f"[VERIFY] MISMATCH {problem}")
    verdict = "PASS" if not problems else "FAIL"
    if args.plant:
        planted = {"moves: Water Gun.power: ours 45, pret 40", "species: Mudkip.catch_rate: ours 46, pret 45",
                   "types: Water vs Rock: ours 1.0, pret 2.0 (TYPE_MUL_SUPER_EFFECTIVE)"}
        found = set(problems)
        verdict = "PASS (the plants were found, and nothing else)" if found == planted else f"FAIL (found {sorted(found)})"
    say(f"[VERIFY] OVERALL {verdict}")
    if args.evidence is not None:
        from ai_player.gates.provenance import keep_earlier  # (step 4.1 round 3) an earlier tree's file is archived

        keep_earlier(args.evidence)
        args.evidence.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if verdict.startswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
