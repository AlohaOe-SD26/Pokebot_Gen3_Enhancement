"""Machine-check the Gemini #24-pokeprofiles response (2026-07-23) against the bot's
ROM-extracted data — the known-answer control from GEMINI-POKEPROFILES-RESEARCH.md.

Two claim classes are checkable automatically:
  LV  — "species S learns move M at level N" → species.learnset.level_up
  TM  — "species S can learn TM/HM X"        → species.can_learn_tm_hm(item)
Location/judgment claims are NOT checkable here (spot-checked by hand in the grading).

No emulator needed — the data layer only requires a ROM to be selected.
"""

import pathlib as _pl
import sys

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

p = load_profile_by_name("repro-ml")
context.profile = p
context.config.load(p.path, strict=False)
set_rom(p.rom)

from modules.items import get_item_by_name
from modules.pokemon import get_species_by_name

# (species, move, claimed_level) — from the response's movesets/phases/evo notes.
LV_CLAIMS = [
    ("Grovyle", "Leaf Blade", 29),        # "Leaf Blade (Lv29...)"
    ("Torchic", "Flamethrower", 36),      # "Lv36 as Torchic" (evo-delay note)
    ("Blaziken", "Sky Uppercut", 59),     # "Sky Uppercut (Lv59...)"
    ("Blaziken", "Slash", 42),            # "Slash (Lv42)"
    ("Swampert", "Earthquake", 52),       # "Earthquake (TM26 or Lv52)"
    ("Poochyena", "Howl", 13),            # "Howl (Lv13)"
    ("Shroomish", "Leech Seed", 16),      # (listed in Breloom goal set)
    ("Shroomish", "Spore", 54),           # evo-timing note
    ("Breloom", "Mach Punch", 23),        # "Mach Punch (Lv23)"
    ("Breloom", "Sky Uppercut", 54),      # goal set
    ("Slakoth", "Yawn", 19),              # "Yawn (Lv19)"
    ("Slaking", "Slack Off", 43),         # "Slack Off (Lv43)"
    ("Ralts", "Confusion", 6),            # "switch-train until Lv6 (Confusion)"
    ("Gardevoir", "Psychic", 26),         # "Psychic (Lv26)"
    ("Kirlia", "Reflect", 33),            # "Reflect (Lv33)"
    ("Kadabra", "Psychic", 36),           # "Psychic (Lv36)"
    ("Kadabra", "Recover", 43),           # "Recover (Lv43)"
    ("Makuhita", "Vital Throw", 10),      # "Vital Throw (Lv10)"
    ("Makuhita", "Fake Out", 13),         # "Fake Out (Lv13)"
    ("Hariyama", "Cross Chop", 46),       # "Cross Chop (Lv46)"
    ("Pelipper", "Protect", 33),          # "Protect (Lv33)"
    ("Geodude", "Earthquake", 31),        # "(Lv31)" (listed for the Graveler set)
    ("Geodude", "Rollout", 22),           # "Rollout (Lv22)"
    ("Graveler", "Explosion", 46),        # "Explosion (Lv46)"
    ("Zubat", "Bite", 16),                # "Bite (Lv16)"
    ("Golbat", "Confuse Ray", 21),        # "Confuse Ray (Lv21)" (as Zubat line)
    ("Skitty", "Faint Attack", 27),       # "Faint Attack (Lv27 Skitty)"
    ("Skitty", "Assist", 39),             # "Assist (Lv39 Skitty)"
    ("Oddish", "Sleep Powder", 14),       # "Sleep Powder (Lv14)"
    ("Gloom", "Moonlight", 35),           # "Moonlight (Lv35 Gloom)"
    ("Vileplume", "Petal Dance", 44),     # "Petal Dance (Lv44)"
    ("Beautifly", "Silver Wind", 24),     # "Silver Wind (Lv24)"
    ("Beautifly", "Morning Sun", 20),     # "Morning Sun (Lv20)"
    ("Dustox", "Psybeam", 24),            # "Psybeam (Lv24)"
    ("Dustox", "Moonlight", 17),          # "Moonlight (Lv17)"
    ("Taillow", "Quick Attack", 13),      # "Quick Attack (Lv13)"
    ("Linoone", "Belly Drum", 53),        # "Belly Drum (Lv53)"
    ("Whismur", "Uproar", 11),            # phases list (level not claimed; sanity extra)
]

# (species, item, claimed_can_learn) — compat claims from the goal sets / registry.
TM_CLAIMS = [
    ("Sceptile", "TM02", True),   # Dragon Claw
    ("Sceptile", "TM31", True),   # Brick Break
    ("Sceptile", "TM40", True),   # Aerial Ace
    ("Blaziken", "TM08", True),   # Bulk Up
    ("Blaziken", "TM35", True),   # Flamethrower
    ("Blaziken", "TM40", True),   # Aerial Ace
    ("Swampert", "TM13", True),   # Ice Beam
    ("Swampert", "TM26", True),   # Earthquake
    ("Swampert", "TM27", True),   # Return
    ("Mightyena", "TM27", True),  # Return
    ("Mightyena", "TM30", True),  # Shadow Ball
    ("Mightyena", "HM04", True),  # Strength
    ("Linoone", "HM01", True),    # Cut
    ("Linoone", "HM03", True),    # Surf
    ("Linoone", "HM04", True),    # Strength
    ("Linoone", "HM06", True),    # Rock Smash
    ("Beautifly", "TM19", True),  # Giga Drain
    ("Dustox", "TM36", True),     # Sludge Bomb
    ("Swellow", "TM27", True),    # Return
    ("Swellow", "TM42", True),    # Facade
    ("Swellow", "TM47", True),    # Steel Wing
    ("Swellow", "TM30", True),    # Shadow Ball — REGISTRY claims Swellow contests it
    ("Pelipper", "HM03", True),   # Surf
    ("Pelipper", "HM02", True),   # Fly
    ("Pelipper", "TM34", True),   # Shock Wave
    ("Gardevoir", "TM24", True),  # Thunderbolt
    ("Gardevoir", "TM04", True),  # Calm Mind
    ("Gardevoir", "TM34", True),  # Shock Wave
    ("Breloom", "TM19", True),    # Giga Drain
    ("Slaking", "TM15", True),    # Hyper Beam
    ("Slaking", "TM26", True),    # Earthquake
    ("Slaking", "TM30", True),    # Shadow Ball
    ("Slaking", "TM31", True),    # Brick Break
    ("Kadabra", "TM04", True),    # Calm Mind
    ("Kadabra", "TM34", True),    # Shock Wave
    ("Exploud", "TM26", True),    # Earthquake
    ("Exploud", "TM35", True),    # Flamethrower
    ("Exploud", "TM13", True),    # Ice Beam
    ("Exploud", "TM30", True),    # Shadow Ball
    ("Hariyama", "TM08", True),   # Bulk Up
    ("Hariyama", "TM31", True),   # Brick Break
    ("Hariyama", "HM03", True),   # Surf ("funny Gen 3 quirk")
    ("Azumarill", "TM27", True),  # Return
    ("Azumarill", "TM31", True),  # Brick Break
    ("Azumarill", "TM23", True),  # Iron Tail
    ("Azumarill", "HM07", True),  # Waterfall
    ("Azumarill", "HM08", True),  # Dive
    ("Crobat", "TM36", True),     # Sludge Bomb
    ("Crobat", "TM30", True),     # Shadow Ball — goal-set claim
    ("Crobat", "HM02", True),     # Fly
    ("Delcatty", "TM27", True),   # Return
    ("Vileplume", "TM19", True),  # Giga Drain
    ("Vileplume", "TM36", True),  # Sludge Bomb
    ("Tropius", "HM02", True),    # Fly (mule tier)
    ("Tropius", "HM01", True),    # Cut
    ("Tropius", "HM04", True),    # Strength
    ("Tentacruel", "TM13", True), # Ice Beam ("SUPER CORE - Swampert, Tentacruel")
    ("Tentacool", "HM03", True),  # Surf (mule "water trinity")
    ("Tentacool", "HM07", True),  # Waterfall
    ("Tentacool", "HM08", True),  # Dive
]

print("=== LEVEL-UP CLAIMS ===")
lv_pass = lv_fail = 0
for sp_name, move_name, lvl in LV_CLAIMS:
    sp = get_species_by_name(sp_name)
    entries = [e for e in sp.learnset.level_up if e.move.name == move_name]
    actual = sorted({e.level for e in entries})
    ok = lvl in actual
    lv_pass += ok
    lv_fail += not ok
    verdict = "PASS" if ok else f"FAIL (actual: {actual if actual else 'NOT IN LEVEL-UP SET'})"
    print(f"  {sp_name:11s} {move_name:14s} @{lvl:<3d} {verdict}")

print("\n=== TM/HM COMPAT CLAIMS ===")
tm_pass = tm_fail = 0
for sp_name, item_name, claimed in TM_CLAIMS:
    sp = get_species_by_name(sp_name)
    item = get_item_by_name(item_name)
    actual = sp.can_learn_tm_hm(item)
    ok = actual == claimed
    tm_pass += ok
    tm_fail += not ok
    move = item.tm_hm_move()
    print(f"  {sp_name:11s} {item_name} ({move.name if move else '?':14s}) claimed={claimed} actual={actual} {'PASS' if ok else 'FAIL'}")

total = lv_pass + lv_fail + tm_pass + tm_fail
print(f"\n=== SUMMARY: level-up {lv_pass}/{lv_pass+lv_fail} | tm-compat {tm_pass}/{tm_pass+tm_fail} "
      f"| overall {lv_pass+tm_pass}/{total} ({100*(lv_pass+tm_pass)//total}%) ===")
