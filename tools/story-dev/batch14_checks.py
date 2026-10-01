r"""DESIGN v2 STEP 14, T4a — the batch's CORRECTNESS checks (E1-E5) and the STOP-3 read.

⛔ THE CAVEAT IS THE HEADLINE: a MEASUREMENT tool (tools/story-dev only). None of it is a confirmatory reading: those
are C1-C5 in `compare_arms.py` (T3). A FINDING is a deterministic invariant the batch broke — a defect to DIAGNOSE
with a driver, never a grade; a PASS means "no violation in the lines read", never "the package is correct".

THE SPEC (binding): `ai-research-notes/2026-10-01-batch14-T4-PREDICTIONS.md` (T4a), and its parent
`…-batch14-DESIGN.md` §4 (STOP-3) and §5 (E1-E5). Every emitter and its line shape: `…-batch14-recon/
b14_recon_expectations.md` §B. Where the spec is silent the simplest reading is taken and marked `SPEC-SILENT` beside
the code.

INPUT. Exactly `compare_arms.py`'s: a batch directory (`x4-runs/<stamp>` under the MAIN checkout, or any path) or
`--tag TAG` for a RUNNING batch, loaded through `compare_arms.collect_runs` — the arm refusal and the cut / lost /
capped status are ITS — with ONE read per log: `extract` runs on the same lines through the loader's `visit` hook.
The instrument controls are `compare_arms.controls` + `completeness_failures`: on any failure (a refused log, an arm
with no usable run, an incomplete batch directory) NO check is printed and the exit is 1, exactly as compare_arms
prints no grade.

REUSED, never re-parsed: `battle_log` (the battle split, the offline class, the `[TRAINER]` / `[KEYBATTLE]` /
`[DBLITEM]` parsers, `first_attempts`, `keys_met`, `hp_item_count`, `partner_rose`, `outcome_bucket`), `x4_headless`
(`_RUN_END_RE`, `classify_outcome`, `_derail_reason`, and `scan_lines` — the LIVE monitor's own matcher) and
`grade_r20_telemetry.CATCH`. What no module parsed yet has its own small pattern here (`[MAP]`, `[CATCH] loss-filed`,
`[DEXFENCE]`, `[BALLS-BUY]` / `[KIT-BUY]` fields, `[WEAKEN-OBS]`, `[DMGAUDIT]` blocks, our side's `[TURN]` HP), each
quoted against a real line in the gate (`probe_batch14_checks.py`).

THE CHECKS (DESIGN §5; the spec's table):
  E1  B: 0 `[ITEM] using` and 0 `[DBLITEM] use` in NON-KEY battles, except battles whose `[KEYBATTLE]` reason is a
      fail-open one (`fail_open_*`, `FAIL_OPEN(…)`), each listed. Both arms: 0 in WILD battles.
  E2  B: at most one `[KEYBATTLE]` per battle; its `key=` equals the offline class; any `reason=flag_off` is a
      violation. Trainer battles with no `[KEYBATTLE]` are counted (a summary, never a finding).
  E3  the arm identity: A prints none of the arms file's `monitor.A.forbid` texts, B none of `monitor.B.forbid` (the
      live monitor's lists and its matcher). B: every `[CATCH] end kind=dex … end=lost` is followed by a `[CATCH]
      loss-filed kind=dex`. B: each run's FIRST Pokémon Center heal in Rustboro logs a `why=topoff…` line and a
      `[KIT-BUY]` line. `[CATCH] trainee` and `[DEXCATCH-NOBAIL]`: counts per arm only.
  E4  B: at least 1 `[DBLITEM] use` IF at least 5 distinct B runs reached a Tate & Liza FIRST attempt holding at least
      1 HP item (`hp_item_count` on its `[TRAINER] start heal_stock`); else NOT ASSESSED. On a zero: every such battle
      with its lowest own-battler HP and whether it reached the 0.35 heal gate.
  E5  B: every `[DBLITEM] after` whose PARTNER's HP rose although no `[DBLITEM] use` of that turn targeted the partner,
      listed for reading BY HAND — never counted as a defect (its word is "READ BY HAND", not FINDING).
  STOP-3  the run-end signatures per arm (`x4_headless._derail_reason` over each lane's `stdout.txt`); for every
      signature in >= 2 B runs and 0 A runs, the last 200 lines of each such run's debug log scanned for a package tag.

EXIT: 0 the checks were computed (FINDINGs are reported, not errors); 1 an instrument control failed (nothing checked);
2 usage.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 batch14_checks.py 20261001-090649
      PYTHONUTF8=1 py -3.12 batch14_checks.py --tag s14            (LIVE, during the batch)
Gate: PYTHONUTF8=1 py -3.12 probe_batch14_checks.py
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import battle_log as bl  # noqa: E402
import compare_arms as ca  # noqa: E402
import grade_r20_telemetry as gr  # noqa: E402
import x4_headless as x4  # noqa: E402

ARM_A, ARM_B = ca.ARM_A, ca.ARM_B

# ---------------------------------------------------------------------------------------------------- constants
#: STOP-3 (DESIGN §4): "the last ~200 debug-log lines before each of those derails". A run's log ENDS at its run end
#: (the next run opens a new log), so its tail IS the lines before the derail. SPEC-SILENT: exactly 200 lines, the
#: logger's closing `=== DEBUG LOG END ===` line not counted.
TAIL_LINES = 200
LOG_END = "=== DEBUG LOG END ==="
#: STOP-3's package tags, verbatim from DESIGN §4 (plain substrings over the whole line, as the live monitor matches).
PACKAGE_TAGS = ("[ITEM] using", "[DBLITEM]", "[KIT-BUY]", "why=topoff", "[KEYBATTLE]", "[DEXCATCH-NOBAIL]",
                "[CATCH] trainee")
#: E1: the `[KEYBATTLE]` reasons that FAIL OPEN (`trainer_identity.py:70-85`, `story_mode.py:6455`).
FAIL_OPEN_PREFIXES = ("fail_open_", "FAIL_OPEN(")
#: E2: DESIGN AI-6 — `flag_off` cannot reach a log line, so one that does is a violation.
FLAG_OFF = "flag_off"
#: E4 (DESIGN §5, review F7): the denominator's size and the production heal gate (`battle_items.HEAL_AT_FRACTION`).
E4_MIN_RUNS = 5
HEAL_FRACTION = 0.35
#: Map ids (`sandbox-pokebot/modules/map_data.py`; a `[MAP]` line's NAME can lag its ids — the batch0926 excerpt reads
#: `EVER GRANDE CITY(24,43)` for Victory Road — so every rule here keys on the (group, number) pair, never the name).
#: SPEC-SILENT (E3, "each run's FIRST Pokémon Center heal IN RUSTBORO"): a heal is the per-heal `[PC] … withdraw:`
#: report (`_HEAL_MARK`) logged while the avatar's map is Rustboro's Pokémon Center; its errand is every line after it
#: until a `[MAP]` load outside Rustboro (city, Pokémon Center, mart) or the next heal. Only Rustboro is whitelisted
#: (`stock_topoff._whitelist`), and the errand runs at the END of `heal_in_pokemon_center`, after the exit warp.
RUSTBORO_PC = (11, 5)          # RUSTBORO_CITY_POKEMON_CENTER_1F
RUSTBORO_CITY = (0, 3)
RUSTBORO_MART = (11, 7)
#: SPEC-SILENT (D-fence's era): "after Sootopolis" begins at the run's first `[MAP]` load of SOOTOPOLIS CITY.
SOOTOPOLIS_CITY = (0, 7)
#: D-leg11 / D-economy. SPEC-SILENT: "money at leg 11" is the last `[MONEY] … money=₽N` or `[hb] … money=N` reading
#: logged before the run's FIRST load of (16,10); the refusals are the debug log's `DERAIL #` lines (one log = one run).
LEAGUE_1F = (16, 10)           # EVER_GRANDE_CITY_POKEMON_LEAGUE_1F: "loaded EVER GRANDE CITY (16,10)" (D-leg11)
VICTORY_ROAD = {(24, 43): "VICTORY_ROAD_1F", (24, 44): "VICTORY_ROAD_B1F", (24, 45): "VICTORY_ROAD_B2F"}
#: D-leg11: BOTH refusal texts (the recon §A: batch0926's text no longer exists in the code; today's is
#: `victory_road.py:3522-3525`).
LEG11_OLD = "Ch23 leg 11: the basket costs ₽"
LEG11_NEW = ("Ch23 leg 11: the missing basket lines", "short by")

#: Every KEY trainer the tables NAME (pret/pokeemerald `include/constants/opponents.h`, re-read with `gh api` by the
#: builder on 2026-10-01: :265-276 the Elite Four and leaders, :339 Wallace, :36-37 Shelly, :518 Tabitha (Mossdeep),
#: :523-541 Wally VR_1 and the Route 103/110/119 rivals, :596-606 the Rustboro rivals, Maxie / Tabitha, :660-670 Wally
#: and the Lilycove rivals, :736-738 the Magma Hideout Tabitha and Maxie (Mossdeep), :772-773 the Rustboro Mays).
#: K* is compare_arms' FROZEN dict, by reference. A key trainer this table does not name is reported as
#: `opp=<ids> <class>` (never dropped). A rival's six ids (Brendan / May x three starters) are ONE trainer.
TRAINERS = {
    **ca.KSTAR,
    "NORMAN": (269,), "WINONA": (270,), "TATE_AND_LIZA": (271,), "JUAN": (272,),
    "SIDNEY": (261,), "PHOEBE": (262,), "GLACIA": (263,), "DRAKE": (264,), "WALLACE": (335,),
    "RIVAL_ROUTE_103": (520, 523, 526, 529, 532, 535),
    "RIVAL_RUSTBORO": (592, 593, 599, 600, 768, 769),
    "RIVAL_ROUTE_119": (522, 525, 528, 531, 534, 537),
    "RIVAL_LILYCOVE": (661, 662, 663, 664, 665, 666),
    "WALLY_MAUVILLE": (656,),
    "WALLY_VICTORY_ROAD": (519, 657, 658, 659, 660),
    "MAXIE_MAGMA_HIDEOUT": (601,),
    "TABITHA_MAGMA_HIDEOUT": (732,),
    # the Space Center MULTI battle (both admins on one side): one trainer, so it is one attempt, never two rows
    "MAXIE_TABITHA_SPACE_CENTER": (734, 514),
    "SHELLY_WEATHER_INSTITUTE": (32,),
    "SHELLY_SEAFLOOR_CAVERN": (33,),
}
BOSSES = ("TATE_AND_LIZA", "WINONA", "NORMAN", "JUAN")
ELITE_FOUR = ("SIDNEY", "PHOEBE", "GLACIA", "DRAKE", "WALLACE")
NAMED_IDS = frozenset(i for ids in TRAINERS.values() for i in ids)


def _check_trainers(table: dict) -> None:
    """Raise unless no trainer id is named twice (a shared id would make one battle an attempt at two trainers)."""
    seen: dict = {}
    for name, ids in table.items():
        for i in ids:
            if i in seen:
                raise AssertionError(f"trainer id {i} is in both {seen[i]} and {name}")
            seen[i] = name


_check_trainers(TRAINERS)

# ---------------------------------------------------------------------------------------------------- line patterns
#: `f<frame> [CATEGORY] message` (the frame prefix optional, as `battle_log._PREFIX`).
_CAT = re.compile(r"^(?:f(\d+) )?\[([A-Za-z0-9_-]+)\] (.*)$")
#: `[MAP] RUSTBORO CITY(11,5) -> RUSTBORO CITY(0,3) pos=(7, 8)`: the FIRST numeric pair, then ` -> `, then the next.
_MAP = re.compile(r"\((\d+),(\d+)\) -> .*?\((\d+),(\d+)\)")
#: The per-heal report `heal_in_pokemon_center` writes after the nurse (`higher_level_actions._piggyback_report`, its
#: source is `none` / `counter` / `hm-carrier`): `[PC] Story: PC — none withdraw: SKIPPED — …`. Not `… withdraw
#: result: …` (a second line of the same heal).
_HEAL_MARK = re.compile(r"^Story: PC — \S+ withdraw: ")
#: OUR side of a `[TURN]` line (`battle_action_selection._describe`): `Name Llvl hp/max[ [status]] -> `. Anchored on
#: ` -> ` so an unreadable `?` side can never borrow the FOE's numbers. `battle_log` parses only the foe.
_TURN_ME = re.compile(r"\[TURN (\d+)\] ([^>]+?) L(\d+) (\d+)/(\d+)(?: \[[^\]]*\])? -> ")
_TURN_N = re.compile(r"\[TURN (\d+)\]")
_G = re.compile(r"\bg=(\d+)")
#: `[DBLITEM] use side=0 g=0 item=Hyper Potion target=Sceptile#863B0917 P=1 …` (a species may hold a space).
_USE_TARGET = re.compile(r"\btarget=([^=]+?#[0-9A-F]{8}|\?) P=")
_SP = re.compile(r"\bsp=([^=]+?)#(\d+)(?= )")
_END = re.compile(r"\bend=(\S+)")
_KIND = re.compile(r"\bkind=(\S+)")
_RARE = re.compile(r"\brare=(\S+)")
#: `[DEXFENCE] skip #263 Zigzagoon — no Pokédex yet[ rare=… tier=… note=…]` / `[DEXFENCE] CATCH #63 Abra — …`.
_FENCE = re.compile(r"^(\S+) #(\d+) (.+?) — (.*)$")
_BADGE = re.compile(r"\bn=(\d+)\b")
_MONEY_SIGN = re.compile(r"money=₽([\d,]+)")
_MONEY_HB = re.compile(r"\bmoney=(\d+)\b")
_WHY = re.compile(r"\bwhy=(\S+)")
_BALL = re.compile(r"\bball=(.+?) bought=")
_BOUGHT_N = re.compile(r"\bbought=(\d+)\b")
_BOUGHT_KIT = re.compile(r"\bbought=(\{[^}]*\}|\S+)")
_MONEY_AB = re.compile(r"\bmoney=(-?\d+|\?)->(-?\d+|\?)")
_WOULD = re.compile(r"\[WEAKEN-OBS\] would=(\S+)")
_REASON = re.compile(r"\breason=(\S+)")
_STDOUT_LOG = re.compile(r"debug logging ON -> (.+?\.log)\s*$", re.MULTILINE)


def _int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def strip_numbers(text: str) -> str:
    """D-fence: a reason with every number replaced by `N` (`party is 4/6` -> `party is N/N`)."""
    return re.sub(r"\d[\d,]*", "N", text)


def is_fail_open(reason) -> bool:
    return bool(reason) and str(reason).startswith(FAIL_OPEN_PREFIXES)


def parse_map(msg: str) -> "tuple | None":
    """A `[MAP]` message -> ((g, n) from, (g, n) to), or None."""
    m = _MAP.search(msg)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2))), (int(m.group(3)), int(m.group(4)))


def tail_of(lines, n: int = TAIL_LINES) -> list:
    """The last `n` lines of a run's log, its closing `=== DEBUG LOG END ===` (and blank lines after it) excluded."""
    end = len(lines)
    while end and (not lines[end - 1].strip() or lines[end - 1].startswith(LOG_END)):
        end -= 1
    return list(lines[max(0, end - n):end])


def tags_in(lines) -> list:
    """STOP-3: the package tags present in `lines` (substrings), in `PACKAGE_TAGS` order."""
    return [t for t in PACKAGE_TAGS if any(t in line for line in lines)]


# ---------------------------------------------------------------------------------------------------- one battle
def battle_rec(k: int, battle, telemetry: bool) -> dict:
    """PURE: what the checks and tables need from ONE started battle (`battle_log.Battle`), by battle_log's own rules."""
    facts = bl.battle_facts(battle, telemetry)
    starts, ends = bl._trainer_events(battle)
    trainer_start = False
    t_ends = []
    for line in battle.trainer:
        t = bl.parse_trainer(line)
        if not t:
            continue
        msg = bl._PREFIX.match(line.rstrip("\r\n")).group(2)
        if msg.startswith("start"):              # `start …` or `start unreadable …`: a trainer battle began
            trainer_start = True
        if t["kind"] == "end":
            f = bl._fields(msg)
            t_ends.append((_int(f.get("delta")), f.get("map")))
    return {"k": k, "cls": facts["cls"], "group": facts["group"], "outcome": facts["outcome"], "opp": facts["opp"],
            "double": facts["double"], "heal_stock": facts["heal_stock"], "starts": starts, "ends": ends,
            "classes": bl.battle_classes(battle), "trainer_start": trainer_start, "t_ends": t_ends,
            "keybattle": [(line, bl.parse_keybattle(line)) for line in battle.keybattle],
            "using": [line for line in battle.items if bl.item_kind(line) == "using"],
            "dbl_use": [line for line in battle.dblitem if (bl.parse_dblitem(line) or {}).get("kind") == "use"],
            "dbl_after": sum(1 for line in battle.dblitem if (bl.parse_dblitem(line) or {}).get("kind") == "after"),
            # filled by the ordered pass in `extract`:
            "map": None, "catch": False, "catch_lost": [], "lead": None, "min_frac": None, "min_hp": None, "e5": []}


def _e5_readings(events) -> list:
    """PURE (E5). `events` = the battle's ordered ('use', pos, g, target, line) / ('turn', pos, n) / ('after', pos, g,
    parsed, line). Each `after` whose partner's HP ROSE (`battle_log.partner_rose`) is listed UNLESS a `use` of the
    SAME turn targeted that partner. SPEC-SILENT ("not healed that turn"): an action's turn is the first `[TURN n]`
    line after its `use` (the decision line, logged in the same frame); an `after` belongs to the latest `use` of the
    same battler `g` before it; no `use` or no turn -> unexplained (listed)."""
    turns = [(e[1], e[2]) for e in events if e[0] == "turn"]
    uses = [e for e in events if e[0] == "use"]

    def turn_after(pos):
        for tpos, n in turns:
            if tpos > pos:
                return n
        return None

    use_turn = {u[1]: turn_after(u[1]) for u in uses}
    out = []
    for e in events:
        if e[0] != "after" or not bl.partner_rose(e[3]):
            continue
        _kind, pos, g, parsed, line = e
        action = None
        for u in uses:
            if u[1] < pos and u[2] == g:
                action = u
        turn = use_turn.get(action[1]) if action else None
        partner = parsed.get("partner")
        healed = turn is not None and any(u[3] == partner and use_turn.get(u[1]) == turn for u in uses)
        if not healed:
            out.append({"turn": turn, "g": g, "partner": partner, "partner_hp": parsed.get("partner_hp"),
                        "target": parsed.get("target"), "target_hp": parsed.get("target_hp"), "line": line})
    return out


# ---------------------------------------------------------------------------------------------------- one run
class M1bPool:
    """D-M1b: `[DMGAUDIT]` blocks (a `CTL` line — the battle's start — up to the next) pooled over every log of both
    arms, DE-DUPLICATED BY CONTENT (each line with its `f<frame>` prefix stripped: a replay of one seed differs only
    by the RNG hold's few frames). The unique blocks are written in log order (`out`), so `audit_damage_calc.py
    <out>` pairs them exactly as within one log: every block opens with its CTL, which clears a pending BEFORE."""

    def __init__(self, out=None):
        self.seen: set = set()
        self.blocks = self.unique = self.lines = self.unique_lines = self.befores = 0
        self.out = out

    def add(self, block: list) -> None:
        self.blocks += 1
        self.lines += len(block)
        key = hashlib.sha1("\n".join(re.sub(r"^f\d+ ", "", s) for s in block).encode("utf-8")).hexdigest()
        if key in self.seen:
            return
        self.seen.add(key)
        self.unique += 1
        self.unique_lines += len(block)
        self.befores += sum(1 for s in block if "[DMGAUDIT] BEFORE " in s)
        if self.out is not None:
            self.out.write("\n".join(block) + "\n")


def extract(lines, *, forbid=(), param_of=bl.item_parameter, m1b: "M1bPool | None" = None) -> dict:
    """PURE (lines in, a dict out; `m1b` an optional accumulator): everything T4 needs from ONE run log. `forbid` =
    the arms file's `monitor.<lane arm>.forbid` (E3)."""
    telemetry = bl.has_trainer_telemetry(lines)
    battles = [b for b in bl.split_battles(lines) if b.started]
    recs = [battle_rec(k, b, telemetry) for k, b in enumerate(battles)]
    events: dict = collections.defaultdict(list)
    out = {
        "telemetry": telemetry, "battles": recs, "monitor_hits": x4.scan_lines(lines, list(forbid), ())[0],
        "loss_lost_dex": [], "loss_matched": 0, "loss_orphans": 0, "loss_missed": [],
        "rustboro": None, "trainee": 0, "trainee_after": 0, "nobail": 0,
        "tail": tail_of(lines), "badges": {}, "caught": [], "fence": set(), "fence_unparsed": 0,
        "balls_buy": [], "kit_buy": [], "leg11_loaded": False, "leg11_old": [], "leg11_new": [], "leg11_money": None,
        "weaken": collections.Counter(), "rare": [], "frames": 0, "dmg_lines": 0,
    }
    k = -1
    cur_map = None
    era = "before"
    money = None
    heal_window = False
    catch_open = None       # the open [CATCH] start of this run: [species, dex, rare, battle k]
    pending_loss: list = []
    block: list = []
    for pos, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        m = _CAT.match(line)
        if m and m.group(1):
            out["frames"] = max(out["frames"], int(m.group(1)))
        r = bl.route(line)
        if r == "start":
            k += 1
            recs[k]["map"] = cur_map
            continue
        cat, msg = (m.group(2), m.group(3)) if m else (None, "")
        if r == "turn" and k >= 0:
            me = _TURN_ME.search(line)
            if me:
                hp, mx = int(me.group(4)), int(me.group(5))
                if recs[k]["lead"] is None:
                    recs[k]["lead"] = me.group(2).strip()
                if mx > 0 and (recs[k]["min_frac"] is None or hp / mx < recs[k]["min_frac"]):
                    recs[k]["min_frac"], recs[k]["min_hp"] = hp / mx, f"{me.group(2).strip()} {hp}/{mx}"
            n = _TURN_N.search(line)
            if n:
                events[k].append(("turn", pos, int(n.group(1))))
        elif r == "dblitem" and k >= 0:
            d = bl.parse_dblitem(line) or {}
            g = _G.search(line)
            if d.get("kind") == "use":
                t = _USE_TARGET.search(line)
                events[k].append(("use", pos, g.group(1) if g else None, t.group(1) if t else None, line))
            elif d.get("kind") == "after":
                events[k].append(("after", pos, g.group(1) if g else None, d, line))
        elif cat == "MAP":
            mm = parse_map(msg)
            if mm:
                cur_map = mm[1]
                if cur_map == SOOTOPOLIS_CITY:
                    era = "after"
                if cur_map == LEAGUE_1F and not out["leg11_loaded"]:
                    out["leg11_loaded"], out["leg11_money"] = True, money
                if heal_window and cur_map not in (RUSTBORO_PC, RUSTBORO_CITY, RUSTBORO_MART):
                    heal_window = False
        elif cat == "PC" and _HEAL_MARK.match(msg):
            heal_window = False                     # a heal ends the previous heal's errand window
            if out["rustboro"] is None and cur_map == RUSTBORO_PC:
                out["rustboro"] = {"marker": line, "topoff": None, "kit": None}
                heal_window = True
                continue
        elif cat == "CATCH":
            cm = gr.CATCH.match(line)
            if cm:
                sp = _SP.search(line)
                if cm.group(2) == "start":
                    rare = _RARE.search(line)
                    catch_open = [sp.group(1) if sp else "?", _int(sp.group(2)) if sp else None,
                                  rare.group(1) if rare else None, k]
                    out["rare"].append(catch_open + ["?"])      # the end is filled when its `end` arrives
                    if k >= 0:
                        recs[k]["catch"] = True
                else:
                    end = _END.search(line)
                    kind = _KIND.search(line)
                    end_v = end.group(1) if end else "?"
                    if catch_open is not None and out["rare"]:
                        out["rare"][-1][4] = end_v
                    catch_open = None
                    if k >= 0:
                        recs[k]["catch"] = True
                        if end_v == "lost":
                            recs[k]["catch_lost"].append(line)
                    if end_v == "caught":
                        out["caught"].append((sp.group(1) if sp else "?", max(out["badges"], default=0)))
                    if kind and kind.group(1) == "dex" and end_v == "lost":
                        out["loss_lost_dex"].append(line)
                        pending_loss.append(line)
            elif msg.startswith("loss-filed "):
                kind = _KIND.search(msg)
                if kind and kind.group(1) == "dex":
                    if pending_loss:
                        pending_loss.pop(0)
                        out["loss_matched"] += 1
                    else:
                        out["loss_orphans"] += 1
            elif msg.startswith("trainee lead="):
                out["trainee"] += 1
            elif msg.startswith("trainee-after "):
                out["trainee_after"] += 1
        elif cat == "DEXFENCE":
            fm = _FENCE.match(msg.split(" rare=", 1)[0])
            if fm:
                out["fence"].add((era, fm.group(1), f"#{fm.group(2)} {fm.group(3)}", strip_numbers(fm.group(4))))
            else:
                out["fence_unparsed"] += 1
        elif cat == "BADGE":
            bm = _BADGE.search(msg)
            if bm and m.group(1):
                out["badges"].setdefault(int(bm.group(1)), int(m.group(1)))
        elif cat == "MONEY":
            mm = _MONEY_SIGN.search(msg)
            if mm:
                money = int(mm.group(1).replace(",", ""))
        elif cat == "hb":
            mm = _MONEY_HB.search(msg)
            if mm:
                money = int(mm.group(1))
        elif cat == "WEAKEN" and "[WEAKEN-OBS] " in msg:
            wm = _WOULD.search(msg)
            rm = _REASON.search(msg)
            reason = rm.group(1) if rm else ""
            stage = reason.split(":", 1)[0] if reason.startswith(("stage1:", "stage2:")) else "-"
            out["weaken"][(wm.group(1) if wm else "?", stage)] += 1
        elif cat == "DMGAUDIT":
            out["dmg_lines"] += 1
            if msg.startswith("CTL") and block:
                if m1b is not None:
                    m1b.add(block)
                block = []
            block.append(line)
        if "[DEXCATCH-NOBAIL]" in line:
            out["nobail"] += 1
        if "[BALLS-BUY] " in line:
            out["balls_buy"].append(_buy(line, kit=False))
        if "[KIT-BUY] " in line:
            out["kit_buy"].append(_buy(line, kit=True))
        if "DERAIL #" in line:
            if LEG11_OLD in line:
                out["leg11_old"].append(line)
            elif all(t in line for t in LEG11_NEW):
                out["leg11_new"].append(line)
        if heal_window and out["rustboro"] is not None:
            if out["rustboro"]["topoff"] is None and "why=topoff" in line:
                out["rustboro"]["topoff"] = line
            if out["rustboro"]["kit"] is None and "[KIT-BUY]" in line:
                out["rustboro"]["kit"] = line
    if block and m1b is not None:
        m1b.add(block)
    if out["rustboro"] is not None:
        out["rustboro"]["open_at_end"] = heal_window      # the log ENDED inside the errand (a cut run's tail)
    out["loss_missed"] = pending_loss
    for k2, evs in events.items():
        recs[k2]["e5"] = _e5_readings(evs)
    out["trainers"] = run_trainers(battles, recs, param_of)
    return out


def _buy(line: str, kit: bool) -> dict:
    """A `[BALLS-BUY]` (both prefixes) or `[KIT-BUY]` line -> why, ball, bought, ₽ spent (None when unreadable)."""
    why = _WHY.search(line)
    mab = _MONEY_AB.search(line)
    a, b = (_int(mab.group(1)), _int(mab.group(2))) if mab else (None, None)
    out = {"why": why.group(1) if why else "?", "spent": (a - b) if a is not None and b is not None else None}
    if kit:
        bm = _BOUGHT_KIT.search(line)
        items = {}
        if bm and bm.group(1).startswith("{"):
            try:
                import ast

                got = ast.literal_eval(bm.group(1))
                items = {str(k): int(v) for k, v in got.items()} if isinstance(got, dict) else {}
            except (ValueError, SyntaxError, TypeError):
                items = {}
        out["items"] = items
    else:
        ball = _BALL.search(line)
        bn = _BOUGHT_N.search(line)
        out["ball"] = ball.group(1) if ball else "-"
        out["bought"] = int(bn.group(1)) if bn else 0
    return out


def key_of(starts: set) -> "str | None":
    """The NAMED trainer whose ids a battle's `[TRAINER] start` opp ids hit (`TRAINERS`), else None."""
    for name, ids in TRAINERS.items():
        if starts & set(ids):
            return name
    return None


def run_trainers(battles, recs, param_of=bl.item_parameter) -> dict:
    """PURE: every KEY trainer the run met -> `{"met", "attempts": [outcomes], "first": outcome | None, "first_k",
    "hp", "hp_unknown", "lead", "won_ever"}`. Named trainers come from `TRAINERS`; any other trainer of a battle the
    offline class calls KEY is `opp=<ids> <class>`. ⛔ The first attempt is `battle_log.first_attempts`' (the earliest
    start with a matching end; never `first=`), met is `keys_met`, an attempt is a battle with both (T2(e))."""
    ids_of = dict(TRAINERS)
    for rec in recs:
        if rec["cls"] == bl.KEY and rec["starts"] and not (rec["starts"] & NAMED_IDS):
            label = "+".join("?" if c is None else f"0x{c:02X}" for c in dict.fromkeys(rec["classes"]))
            ids_of.setdefault(f"opp={'+'.join(str(i) for i in sorted(rec['starts']))} class={label}",
                              tuple(sorted(rec["starts"])))
    met = bl.keys_met(battles, ids_of)
    first = bl.first_attempts(battles, ids_of)
    out = {}
    for key, ids in ids_of.items():
        if key not in met:
            continue
        idset = set(ids)
        attempts = [rec["outcome"] for rec in recs if rec["starts"] & idset and rec["ends"] & idset]
        fa = first[key]
        hp, unknown = bl.hp_item_count(fa["heal_stock"], param_of) if fa else (None, [])
        out[key] = {"met": True, "attempts": attempts, "first": fa["outcome"] if fa else None,
                    "first_k": fa["index"] if fa else None, "hp": hp, "hp_unknown": unknown,
                    "lead": recs[fa["index"]]["lead"] if fa else None, "won_ever": "won" in attempts}
    return out


# ---------------------------------------------------------------------------------------------------- the batch (I/O)
def parse_stdout(text: str) -> list:
    """A lane's `stdout.txt` -> one dict per ENDED run: `run`, `outcome`, `bucket` (`x4_headless.classify_outcome`),
    `frames`, `signature` (`x4_headless._derail_reason`, non-finished runs only; None for a finish) and `log`, the
    BASENAME of the debug log the run opened (the last `debug logging ON -> <path>` before its end; None if none)."""
    opens = [(m.start(), re.split(r"[\\/]", m.group(1).strip())[-1]) for m in _STDOUT_LOG.finditer(text)]
    out = []
    for m in x4._RUN_END_RE.finditer(text):
        outcome = m.group(2).strip()
        bucket = x4.classify_outcome(outcome)
        log = None
        for start, name in opens:
            if start < m.start():
                log = name
        try:
            frames = int(m.group(3).replace(",", ""))
        except ValueError:
            frames = 0
        out.append({"run": int(m.group(1)), "outcome": outcome, "bucket": bucket, "frames": frames,
                    "signature": None if bucket == "finished" else x4._derail_reason(outcome), "log": log})
    return out


def load(batch_arg, tag, ap, *, m1b: "M1bPool | None" = None) -> dict:
    """The batch through `compare_arms` (its loader, controls and completeness), plus T4's per-run extraction and
    each lane's `stdout.txt`. `ap.error` (exit 2) on an unusable ARMS.json or a batch without arms A and B."""
    batch_dir = ca.find_batch(batch_arg, tag, ap)
    try:
        man = ca.load_manifest(batch_dir)
        monitor = json.loads(man["raw"]["arms_text"]).get("monitor") or {}
    except (OSError, KeyError, ValueError, TypeError) as error:
        ap.error(f"{batch_dir / 'ARMS.json'} is not a usable T1 manifest: {type(error).__name__}: {error}")
    if not {ARM_A, ARM_B} <= set(man["arms"]):
        ap.error(f"ARMS.json arms {sorted(man['arms'])}: T4 reads {ARM_A} and {ARM_B}")

    def visit(record, lines):
        forbid = (monitor.get(record.get("lane_arm")) or {}).get("forbid", [])
        record["t4"] = extract(lines, forbid=forbid, m1b=m1b)

    try:
        runs, facts = ca.collect_runs(batch_dir, tag, visit=visit)
    except (OSError, KeyError, ValueError, TypeError) as error:
        ap.error(f"{batch_dir / 'ARMS.json'} is not a usable T1 manifest: {type(error).__name__}: {error}")
    for r in runs:
        r.setdefault("t4", None)
    summ = facts["summary"]
    failures, info = ca.controls(runs, completeness=ca.completeness_failures(
        man["lanes"], facts["logs_per_lane"], summ, live=bool(tag), tag=man["raw"].get("profile_tag")))
    stdout = {}
    for lane in man["lanes"]:
        p = batch_dir / f"L{lane['slot'] + 1:02d}" / "stdout.txt"
        try:
            text = p.read_bytes().decode("utf-8", errors="replace")
        except OSError:
            text = None
        stdout[lane["tag"]] = {"arm": lane.get("arm"), "runs": parse_stdout(text) if text is not None else None,
                               "path": str(p)}
    return {"batch_dir": batch_dir, "manifest": man, "monitor": monitor, "runs": runs, "facts": facts,
            "summary": summ, "failures": failures, "info": info, "stdout": stdout, "live": bool(tag), "tag": tag}


# ---------------------------------------------------------------------------------------------------- the checks (pure)
def _name(run) -> str:
    return f"{run.get('lane') or '?'} {pathlib.Path(run['log']).name}"


def _arm_runs(runs, arm):
    """The runs of `arm` that were read (a `t4` record). SPEC-SILENT: the CHECKS read every such run, excluded ones
    (no starter, not a starter) too — a correctness invariant holds for every line the bot wrote."""
    return [r for r in runs if r.get("t4") and r.get("lane_arm") == arm and not r.get("refused")]


def check_e1(runs) -> dict:
    """E1 (see the module docstring). Returns {status, detail lines, counts}."""
    viol, exempt, unclassified = [], [], []
    nonkey_b = wild = 0
    for arm in (ARM_A, ARM_B):
        for run in _arm_runs(runs, arm):
            for rec in run["t4"]["battles"]:
                uses = rec["using"] + rec["dbl_use"]
                if rec["cls"] == bl.WILD:
                    wild += 1
                    viol += [f"{arm} WILD battle #{rec['k']} {_name(run)}: {u.strip()}" for u in uses]
                elif arm == ARM_B and rec["cls"] == bl.NONKEY:
                    nonkey_b += 1
                    reasons = [p.get("reason") for _l, p in rec["keybattle"] if p]
                    if uses and any(is_fail_open(x) for x in reasons):
                        exempt.append(f"B NON-KEY battle #{rec['k']} opp={rec['opp']} {_name(run)}: fail-open "
                                      f"{[x for x in reasons if is_fail_open(x)]}, {len(uses)} item line(s)")
                    else:
                        viol += [f"B NON-KEY battle #{rec['k']} opp={rec['opp']} {_name(run)}: {u.strip()}"
                                 for u in uses]
                elif arm == ARM_B and rec["cls"] == bl.UNCLASSIFIED and uses:
                    unclassified.append(f"B UNCLASSIFIED battle #{rec['k']} opp={rec['opp']} {_name(run)}: "
                                        f"{len(uses)} item line(s)")
    detail = [f"B NON-KEY battles {nonkey_b}; WILD battles (both arms) {wild}; violating lines {len(viol)}; "
              f"exempted fail-open battles {len(exempt)}"]
    detail += [f"  ⛔ {v}" for v in viol] + [f"  exempt: {e}" for e in exempt]
    # SPEC-SILENT: an UNCLASSIFIED battle (a `?` side) is neither NON-KEY nor WILD, so E1 does not judge it; listed.
    detail += [f"  not judged (UNCLASSIFIED): {u}" for u in unclassified]
    return {"status": "FINDING" if viol else "PASS", "detail": detail, "violations": viol, "exempt": exempt,
            "nonkey_b": nonkey_b, "wild": wild}


def check_e2(runs) -> dict:
    """E2. SPEC-SILENT: DESIGN counts the trainer battles with no `[KEYBATTLE]` "by strategy", which no log line
    names; they are counted by OFFLINE CLASS."""
    viol, missing = [], collections.Counter()
    lines_b = unreadable = 0
    for run in _arm_runs(runs, ARM_B):
        for rec in run["t4"]["battles"]:
            kb = rec["keybattle"]
            lines_b += len(kb)
            if len(kb) > 1:
                viol.append(f"battle #{rec['k']} opp={rec['opp']} {_name(run)}: {len(kb)} [KEYBATTLE] lines")
            for line, p in kb:
                p = p or {}
                if p.get("reason") == FLAG_OFF:
                    viol.append(f"battle #{rec['k']} {_name(run)}: reason=flag_off: {line.strip()}")
                key = p.get("key")
                offline = {bl.KEY: "True", bl.NONKEY: "False"}.get(rec["cls"])
                # SPEC-SILENT: `key=?` (a fail-open read) and an UNCLASSIFIED battle cannot be compared; tallied only.
                if key in ("True", "False") and offline is not None:
                    if key != offline:
                        viol.append(f"battle #{rec['k']} {_name(run)}: key={key} but the offline class is "
                                    f"{rec['cls']}: {line.strip()}")
                else:
                    unreadable += 1
            if rec["trainer_start"] and not kb:
                missing[rec["cls"]] += 1
    detail = [f"B [KEYBATTLE] lines {lines_b}; violations {len(viol)}; not comparable (key=? or UNCLASSIFIED) "
              f"{unreadable}; trainer battles with NO [KEYBATTLE], by offline class: {dict(missing) or 'none'}"]
    detail += [f"  ⛔ {v}" for v in viol]
    status = "FINDING" if viol else ("PASS" if lines_b or sum(missing.values()) else "NOT ASSESSED")
    return {"status": status, "detail": detail, "violations": viol, "missing": dict(missing), "lines": lines_b}


def check_e3(runs, monitor: dict) -> dict:
    detail, finds = [], []
    for arm in (ARM_A, ARM_B):
        rs = _arm_runs(runs, arm)
        forbid = (monitor.get(arm) or {}).get("forbid")
        if forbid is None:
            detail.append(f"{arm}: the arms file has no monitor.{arm}.forbid list — the identity half NOT ASSESSED")
            continue
        hits = [(run, e, ln) for run in rs for e, ln in run["t4"]["monitor_hits"]]
        detail.append(f"{arm}: {len(hits)} line(s) carrying one of its {len(forbid)} forbidden texts over {len(rs)} "
                      f"run(s)")
        for run, e, ln in hits:
            finds.append(f"{arm} {_name(run)}: {e!r}: {ln.strip()[:240]}")
    rb = _arm_runs(runs, ARM_B)
    lost = sum(len(r["t4"]["loss_lost_dex"]) for r in rb)
    missed = [(r, ln) for r in rb for ln in r["t4"]["loss_missed"]]
    orphans = sum(r["t4"]["loss_orphans"] for r in rb)
    detail.append(f"B: [CATCH] end kind=dex … end=lost {lost}; followed by a loss-filed kind=dex {lost - len(missed)};"
                  f" without one {len(missed)}; loss-filed lines with no lost end before them {orphans}")
    finds += [f"B {_name(r)}: no [CATCH] loss-filed kind=dex after: {ln.strip()[:240]}" for r, ln in missed]
    healed = [r for r in rb if r["t4"]["rustboro"]]
    # a CENSORED run (cut / lost / capped) whose log ends inside that errand was never observed to finish it: not a miss
    censored = [r for r in healed if r["t4"]["rustboro"].get("open_at_end") and r["status"] != "complete"
                and not (r["t4"]["rustboro"]["topoff"] and r["t4"]["rustboro"]["kit"])]
    healed = [r for r in healed if r not in censored]
    miss = [r for r in healed if not (r["t4"]["rustboro"]["topoff"] and r["t4"]["rustboro"]["kit"])]
    detail.append(f"B: runs with a Pokémon Center heal in Rustboro {len(healed)} of {len(rb)}; its FIRST heal logged "
                  f"why=topoff… AND [KIT-BUY] in {len(healed) - len(miss)}"
                  + (f"; censored inside that errand (the log ends there; not judged) {len(censored)}" if censored else "")
                  + ("" if healed else " (no B run healed there: this half NOT ASSESSED)"))
    for r in miss:
        h = r["t4"]["rustboro"]
        finds.append(f"B {_name(r)}: the first Rustboro heal ({h['marker'].split(' ', 1)[0]}) logged "
                     f"{'no why=topoff line' if not h['topoff'] else ''}{' and ' if not h['topoff'] and not h['kit'] else ''}"
                     f"{'no [KIT-BUY] line' if not h['kit'] else ''}")
    counts = {arm: {"trainee": sum(r["t4"]["trainee"] for r in _arm_runs(runs, arm)),
                    "trainee_after": sum(r["t4"]["trainee_after"] for r in _arm_runs(runs, arm)),
                    "nobail": sum(r["t4"]["nobail"] for r in _arm_runs(runs, arm))} for arm in (ARM_A, ARM_B)}
    detail.append("counts only (their triggers are not observable): " + "; ".join(
        f"{arm} [CATCH] trainee {c['trainee']} (trainee-after {c['trainee_after']}), [DEXCATCH-NOBAIL] {c['nobail']}"
        for arm, c in counts.items()))
    head = (f"{len(finds)} miss(es): forbidden texts, unfiled dex losses and first Rustboro heals without both "
            f"lines (each listed)")
    detail = [head] + detail + [f"  ⛔ {f}" for f in finds]
    return {"status": "FINDING" if finds else "PASS", "detail": detail, "findings": finds, "counts": counts,
            "rustboro_healed": len(healed), "rustboro_missed": len(miss), "loss_missed": len(missed)}


def check_e4(runs) -> dict:
    rb = _arm_runs(runs, ARM_B)
    qual = []
    for run in rb:
        t = run["t4"]["trainers"].get("TATE_AND_LIZA")
        if t and t["first_k"] is not None and (t["hp"] or 0) >= 1:
            qual.append((run, t))
    # SPEC-SILENT: "at least 1 [DBLITEM] use" names no battle, so it counts over EVERY B battle; the count inside the
    # qualifying first attempts is printed beside it.
    uses = sum(len(rec["dbl_use"]) for run in rb for rec in run["t4"]["battles"])
    in_tl = sum(len(run["t4"]["battles"][t["first_k"]]["dbl_use"]) for run, t in qual)
    head = (f"B runs whose Tate & Liza FIRST attempt held >= 1 HP item: {len(qual)} (assessed at >= {E4_MIN_RUNS}); "
            f"B [DBLITEM] use lines {uses} (in those first attempts {in_tl})")
    if len(qual) < E4_MIN_RUNS:
        return {"status": "NOT ASSESSED", "detail": [head], "qualifying": len(qual), "uses": uses}
    detail = [head]
    if uses == 0:
        # E4's zero: every such battle, its lowest own-battler HP (`[TURN]`, our side) and whether it reached the gate.
        # SPEC-SILENT: "while an HP item was held" = the start bag held one (`hp`); with 0 uses none was spent.
        for run, t in qual:
            rec = run["t4"]["battles"][t["first_k"]]
            frac = rec["min_frac"]
            detail.append(f"  {_name(run)} battle #{rec['k']}: HP items {t['hp']}; lowest own battler "
                          f"{rec['min_hp'] or '?'} ({'?' if frac is None else f'{frac:.2f}'}); at or below "
                          f"{HEAL_FRACTION}: {'?' if frac is None else 'yes' if frac <= HEAL_FRACTION else 'no'}")
    return {"status": "PASS" if uses >= 1 else "FINDING", "detail": detail, "qualifying": len(qual), "uses": uses}


def check_e5(runs) -> dict:
    rb = _arm_runs(runs, ARM_B)
    afters = sum(rec["dbl_after"] for run in rb for rec in run["t4"]["battles"])
    listed = [(run, rec, e) for run in rb for rec in run["t4"]["battles"] for e in rec["e5"]]
    detail = [f"B [DBLITEM] after readings {afters}; partner rose with no same-turn use on the partner {len(listed)} "
              f"(listed for reading BY HAND; never counted as a defect)"]
    for run, rec, e in listed:
        detail.append(f"  {_name(run)} battle #{rec['k']} turn {e['turn']} g={e['g']}: target {e['target']} "
                      f"{e['target_hp']}, partner {e['partner']} {e['partner_hp']}: {e['line'].strip()[:240]}")
    # SPEC-SILENT: E5 never reads FINDING; with no reading at all there is nothing to read (NOT ASSESSED).
    status = "READ BY HAND" if listed else ("PASS" if afters else "NOT ASSESSED")
    return {"status": status, "detail": detail, "listed": len(listed), "afters": afters}


def stop3(runs, stdout: dict) -> dict:
    """STOP-3 (DESIGN §4). `stdout` = {lane tag: {"arm", "runs": parse_stdout(...) or None}}. SPEC-SILENT: the pattern
    reads "yes" when a signature in >= 2 B runs and 0 A runs has a package tag in the tail of AT LEAST ONE of those
    runs (the read that parks; the per-run tags are printed so a reader sees exactly which)."""
    by_log = {(r.get("lane"), pathlib.Path(r["log"]).name): r for r in runs}
    per = {ARM_A: collections.defaultdict(list), ARM_B: collections.defaultdict(list)}
    unread_lanes = []
    for lane, s in stdout.items():
        if s["runs"] is None:
            unread_lanes.append(lane)
            continue
        if s["arm"] not in per:
            continue
        for run in s["runs"]:
            if run["signature"] is not None:
                per[s["arm"]][run["signature"]].append((lane, run))
    ends = {arm: sum(len(v) for v in per[arm].values()) for arm in per}
    detail = [f"non-finished run ends: A {ends[ARM_A]} ({len(per[ARM_A])} signatures), B {ends[ARM_B]} "
              f"({len(per[ARM_B])} signatures)" + (f"; lanes with no stdout.txt: {unread_lanes}" if unread_lanes else "")]
    every = set(per[ARM_A]) | set(per[ARM_B])
    for sig in sorted(every, key=lambda s: (-(len(per[ARM_A].get(s, ())) + len(per[ARM_B].get(s, ()))), s)):
        detail.append(f"  run-end signature A {len(per[ARM_A].get(sig, ()))} / B {len(per[ARM_B].get(sig, ()))}: {sig}")
    pattern = False
    qualifying = []
    for sig, hits in sorted(per[ARM_B].items()):
        if len(hits) < 2 or per[ARM_A].get(sig):
            continue
        rows = []
        for lane, run in hits:
            rec = by_log.get((lane, run["log"]))
            if rec is None or not rec.get("t4"):
                rows.append((lane, run, None))
            else:
                rows.append((lane, run, tags_in(rec["t4"]["tail"])))
        found = any(t for _l, _r, t in rows)
        pattern = pattern or found
        qualifying.append({"signature": sig, "runs": rows, "tags_found": found})
        detail.append(f"  signature in {len(hits)} B runs and 0 A runs: {sig!r}")
        for lane, run, t in rows:
            detail.append(f"    {lane} run {run['run']} {run['log'] or '?'}: "
                          + ("tail UNREADABLE (log not read)" if t is None else f"package tags {t or 'none'}"))
    detail.append(f"STOP-3 pattern: {'yes' if pattern else 'no'}")
    return {"pattern": pattern, "detail": detail, "qualifying": qualifying, "ends": ends}


# ---------------------------------------------------------------------------------------------------- report
def header_lines(b: dict) -> list:
    man, summ = b["manifest"], b["summary"]
    return [f"  source        {'LIVE lanes endless-' + b['tag'] + '-H* under ' + str(bl.default_profiles().absolute()) if b['live'] else 'batch ' + str(b['batch_dir'].absolute())}",
            f"  ARMS.json     {(b['batch_dir'] / 'ARMS.json').absolute()} (arms {sorted(man['arms'])}, commit "
            f"{man['raw'].get('code_commit', '?')}, profile_tag {man['raw'].get('profile_tag')!r})",
            f"  batch         " + (f"verdict {summ['verdict']!r}; stop {summ['stop_reason']!r}; lanes lost "
                                   f"{summ['lanes_lost'] or 'none'}" if summ else "no summary.json (a RUNNING batch)")]


def control_lines(b: dict, what: str = "CHECK", excluded_note: str = "still read by the checks") -> list:
    info, failures = b["info"], b["failures"]
    out = ["INSTRUMENT CONTROLS (compare_arms.controls)",
           f"  logs read: {info['runs']}   usable runs per arm: {info['usable_per_arm']}   refused: "
           f"{len(info['refused'])}   excluded ({excluded_note}): {len(info['excluded'])}"]
    out += [f"    ⛔ refused {log}: {why}" for log, why in info["refused"]]
    out += [f"    - excluded {pathlib.Path(log).name}: {why}" for log, why in info["excluded"]]
    if failures:
        out.append(f"⛔ INSTRUMENT CONTROL FAILED — NO {what} (nothing would be about the batch that ran):")
        out += [f"  ⛔ {f}" for f in failures]
    return out


def run_checks(b: dict) -> dict:
    runs = b["runs"]
    return {"E1": check_e1(runs), "E2": check_e2(runs), "E3": check_e3(runs, b["monitor"]), "E4": check_e4(runs),
            "E5": check_e5(runs), "STOP-3": stop3(runs, b["stdout"])}


def render(b: dict, results: "dict | None") -> list:
    out = ["=" * 100, "DESIGN v2 STEP 14 — batch14_checks (T4a): the correctness invariants E1-E5 and STOP-3",
           "⛔ A MEASUREMENT. A FINDING is a defect to diagnose with a driver; a PASS is 'no violation in the lines "
           "read'.", "=" * 100]
    out += header_lines(b) + [""] + control_lines(b)
    if results is None:
        out.append("=" * 100)
        return out
    out.append("")
    for name in ("E1", "E2", "E3", "E4", "E5"):
        r = results[name]
        out.append(f"{name}  {r['status']} — {r['detail'][0]}")
        out += [f"      {d}" for d in r["detail"][1:]]
    s = results["STOP-3"]
    out.append(f"STOP-3  {'yes' if s['pattern'] else 'no'} — {s['detail'][0]}")
    out += [f"      {d}" for d in s["detail"][1:]]
    out.append("=" * 100)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="design v2 step 14 T4a: the batch's E1-E5 and STOP-3 (DESIGN §4-§5).")
    ap.add_argument("batch", nargs="?", help="x4-runs/<stamp> under the MAIN checkout, or a batch directory path")
    ap.add_argument("--tag", help="LIVE: read a RUNNING batch's lane profiles (endless-<tag>-H*)")
    ap.add_argument("--json", metavar="OUT", help="also write the results as JSON")
    args = ap.parse_args(argv)
    if not args.batch and not args.tag:
        ap.error("give a batch (a stamp or a directory) or --tag")
    b = load(args.batch, args.tag, ap)
    results = None if b["failures"] else run_checks(b)
    print("\n".join(render(b, results)))
    if args.json and results is not None:
        pathlib.Path(args.json).write_text(json.dumps(ca._jsonable(results), indent=2, default=str), encoding="utf-8")
        print(f"JSON written: {pathlib.Path(args.json).absolute()}")
    return 1 if b["failures"] else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main())
