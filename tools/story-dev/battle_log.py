"""BATTLE-LEVEL LOG PARSING, shared by the item instruments (`#27-itemprobes`, design D1).

⛔ THE CAVEAT IS THE HEADLINE: this is a MEASUREMENT module (tools/story-dev only). It reads debug logs; it decides
nothing about the bot, and a clean parse proves nothing about the bot's play.

WHY IT EXISTS (`ai-research-notes/2026-09-30-itemprobes-DESIGN.md`): design v2 §Step 14 grades the key-battle item
policy on `probe_item_index_space.py` and `probe_boss_healing.py`, and on 2026-09-30 both were blind on current logs:
  * the `[TURN]` pattern ended `L(\\d+) (\\d+)/(\\d+)\\s*$`, so every turn whose FOE carried a bracketed status suffix
    (`[FocusEnergy]`, `[Uproar/MultipleTurns]`, `[Sleep]` ...) was silently dropped — ~6,600 lines of real data in the
    batch0927 corpus;
  * the item probe counted three `[ITEM]` line kinds that KI-101's remap retired (0 in that corpus);
  * neither could tell a KEY battle from any other, because the corpus predates `[TRAINER]`/`[KEYBATTLE]`/`[DBLITEM]`.
One module, so the two probes and their gate (`probe_itemprobes.py`) read every line the SAME way.

THE SHAPE. Everything above the `# ---- I/O` marker is PURE (strings in, values out; no file, no emulator), so the gate
pins it on lines quoted verbatim from committed evidence. Only the functions below that marker touch the disk (the log
readers and selectors, `main_checkout`, `item_parameter`'s item data) or the command line (`add_source_args`,
`resolve_sources`, the two probes' shared log-selection options).

THE LINE SHAPES (each taken from the code that EMITS it, never from memory — rule: never paraphrase a log line):
  * `f<frame> [BATTLE] started hp=[...]` / `[BATTLE] ended (outcome=BattleOutcome.<X>) party=[...]`
    (`modules/debug_logger.py`); one battle = one `started` up to the next `started`.
  * `f<frame> [BATTLE] [TURN n] <me> -> <action>  vs <foe>` where `<foe>` is `Name Llvl hp/max[ [status]]` or `?`
    (`modules/battle_action_selection.py`, `_describe`). The status suffix exists on BOTH sides; only the foe's
    position ends the line, which is what the old anchor got wrong.
  * `f<frame> [BATTLE] [ITEM] ...` (`plugins/custom_modes/story_mode.py`, `_maybe_use_item`): see `ITEM_KINDS`.
  * `f<frame> [TRAINER] start|end|skip ...` (`modules/story/trainer_identity.format_start/format_end`, story_mode
    `_t1_start`): `class=0x20(LEADER)` or `class=0x0E(HEX_MANIAC)+0x07(COLLECTOR)` (two opponents), `?` unreadable.
  * `f<frame> [KEYBATTLE] opp= class= key= allow= reason=` (story_mode `_r27_key_gate`).
  * `f<frame> [DBLITEM] use|menu|after|struggle-exit|err ...` (story_mode `_dbl_act`, `battle_action_selection`
    `_dbl_log`); `[DBLITEM-OBS]` is a SEPARATE category (observe mode) and is counted apart.

KEY vs NON-KEY is derived OFFLINE from the `[TRAINER]` class ids against
`sandbox-pokebot/modules/story/trainer_identity.KEY_TRAINER_CLASSES` — IMPORTED, never copied (design v2 §Step 14
`[A-S3]`): a copy here would keep passing after the production list changed. ⛔ By class ID, never by class NAME:
the rival's ROM name is `PkMn_TRAINER`, which also names class 0x00. Step 14 reports PER KEY GROUP (leaders, Elite
Four + Champion, rivals, Magma/Aqua): `KEY_GROUPS`, checked at import to partition `KEY_TRAINER_CLASSES` exactly.

OUTCOMES. ⛔ A DRAW IS A DEFEAT: `IsPlayerDefeated` returns TRUE for `B_OUTCOME_DREW` (pret/pokeemerald
`src/battle_setup.c:994-1000`) and `CB2_EndTrainerBattle` then whites the player out (`:1327-1334`). The batch0927
corpus has 5 Draws, 3 of them at Tate & Liza (the independent pass, `evidence/2026-09-30-itemprobes-ADVERSARIAL.txt`).

WHAT THE LINES CANNOT SAY (the independent pass's findings, documented rather than hidden):
  * ⚠ `[TURN]` RECORDS OVER-COUNT TURNS. Each decision can render 2-3 IDENTICAL `[TURN]` lines (T-ON:49-50), so
    "turn records" is not a turn count and the >=12-record boss-length proxy is ~4-6 real turns. They are NOT
    de-duplicated: the filed predictions count lines, and a de-duplicating rule would need its own evidence.
  * ⚠ A HEAL'S IDENTITY IS `(species, max HP)`, so two IDENTICAL party members (Phoebe's two Banette L49, Roxanne_1's
    two Geodude L12; 88 trainers in the decomp have such a pair) can read as one foe being healed when the second
    comes in. Only the foe's PID on the `[TURN]` line would fix it — a PRODUCTION change, out of this item's scope.
  * ⚠ A rise that newly gains `[Sleep]` is REST (Juan's Kingdra), never an item: `foe_heal_events` tags it "rest".
  * ⚠ In a DOUBLE battle the `[TURN]` line describes only `opponent.left_battler`: right-side heals are invisible.

DESIGN v2 STEP 14, T2 (`ai-research-notes/2026-10-01-batch14-T23-PREDICTIONS.md`; its parent's §3 T2): what ONE run
log says about ITSELF, for `compare_arms.py` — its arm (`parse_env_all` / `arm_of`, from the run header's `env-all:`),
its starter (`run_identity`), whether the 30 MiB cap silenced its event lines (`log_capped`), and its FIRST attempt at
each key trainer (`first_attempts`: the earliest `[TRAINER] start` with a matching `[TRAINER] end`). ⛔ Never `first=`:
it is True on every lost re-attempt too (review S10). The sources gained `batch_logs` (any lane count), `live_logs` (a
RUNNING batch's lane profiles) and the MAIN checkout for a stamp; zero logs from those is an error (exit 2), never an
empty report that reads as "nothing happened".
"""

from __future__ import annotations

import ast
import collections
import dataclasses
import glob
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
if str(SANDBOX) not in sys.path:
    sys.path.insert(0, str(SANDBOX))

from modules.story import trainer_identity as _trainer_identity  # noqa: E402  (the sandbox package, on sys.path above)

#: THE single source of truth for "key" (USER RULING 27's classes). Bound by reference, so the gate can assert identity.
KEY_CLASSES = _trainer_identity.KEY_TRAINER_CLASSES

KEY, NONKEY, WILD, UNCLASSIFIED = "KEY", "NON-KEY", "WILD", "UNCLASSIFIED"
#: Report order. ⛔ WILD is its own class, never folded into NON-KEY (design D2): a wild battle is not a trainer the
#: key policy declined, and folding it would dilute every non-key rate with fights the policy never saw.
BATTLE_CLASSES = (KEY, NONKEY, WILD, UNCLASSIFIED)
OUTCOMES = ("won", "lost", "other")

_TC = _trainer_identity.TRAINER_CLASS
#: design v2 §Step 14: "B's key-battle win rate … reported PER KEY CLASS (leaders, Elite Four, rivals, Magma/Aqua)".
#: Built from `trainer_identity.TRAINER_CLASS` (the same source as `KEY_TRAINER_CLASSES`); order = report order.
KEY_GROUPS = {
    "leaders": frozenset({_TC["LEADER"]}),
    "elite_four": frozenset({_TC["ELITE_FOUR"], _TC["CHAMPION"]}),
    "rivals": frozenset({_TC["RIVAL"]}),
    "magma_aqua": frozenset({_TC["MAGMA_LEADER"], _TC["AQUA_LEADER"], _TC["MAGMA_ADMIN"], _TC["AQUA_ADMIN"]}),
}


def check_key_groups(groups: dict, key_classes) -> None:
    """Raise unless `groups` PARTITION `key_classes` exactly: every key class in exactly one group, no non-key class in
    any. ⛔ Called at import: a key class added to `KEY_TRAINER_CLASSES` tomorrow must fail loudly here, never fall
    outside every group and vanish from the per-group table. (`raise`, not `assert`: `-O` must not strip it.)"""
    union = frozenset().union(*groups.values())
    if union != frozenset(key_classes):
        raise AssertionError(f"KEY_GROUPS != KEY_TRAINER_CLASSES: missing {sorted(set(key_classes) - union)}, "
                             f"extra {sorted(union - set(key_classes))}")
    if sum(len(ids) for ids in groups.values()) != len(union):
        raise AssertionError("KEY_GROUPS overlap: a key class is in two groups")


check_key_groups(KEY_GROUPS, KEY_CLASSES)

# ---------------------------------------------------------------------------------------------------- line routing
#: `f<frame> [CATEGORY] message`; the frame prefix is optional so a hand-trimmed excerpt still routes.
_PREFIX = re.compile(r"^(?:f\d+ )?\[([A-Z0-9_-]+)\] (.*)$")
#: Substrings that mark a line this module is responsible for. A line carrying one that does NOT route is STRAY — a
#: format drift that would otherwise lose data silently. The probes print the stray count as a control.
_TAG_MARKERS = ("[TURN ", "[ITEM] ", "[TRAINER] ", "[KEYBATTLE] ", "[DBLITEM] ", "[DBLITEM-OBS] ",
                "[BATTLE] started", "[BATTLE] ended")


def route(line: str) -> "str | None":
    """Which part of a battle record a line belongs to: `start`, `end`, `turn`, `item`, `trainer`, `keybattle`,
    `dblitem`, `dblobs`; `stray` for a line that MENTIONS a tag but is not in that tag's position; None otherwise."""
    m = _PREFIX.match(line.rstrip("\r\n"))
    if m:
        cat, msg = m.group(1), m.group(2)
        if cat == "BATTLE":
            if msg.startswith("started"):
                return "start"
            if msg.startswith("ended (outcome="):
                return "end"
            if msg.startswith("[TURN "):
                return "turn"
            if msg.startswith("[ITEM] "):
                return "item"
        elif cat == "TRAINER":
            return "trainer"
        elif cat == "KEYBATTLE":
            return "keybattle"
        elif cat == "DBLITEM":
            return "dblitem"
        elif cat == "DBLITEM-OBS":
            return "dblobs"
    if any(tag in line for tag in _TAG_MARKERS):
        return "stray"
    return None


# ---------------------------------------------------------------------------------------------------- [TURN]
#: ⭐ THE FIXED PATTERN. The foe block is `Name Llvl hp/max`, then an OPTIONAL bracketed status suffix, then the end.
#: The old pattern stopped at `(\d+)/(\d+)\s*$` and so dropped every statused foe. `(.*)` is greedy so the LAST
#: ` vs ` is the separator; the name is `.+?`, not `[A-Za-z' .-]+?`, so `Nidoran♀` / `Farfetch'd` / `Mr. Mime` parse.
TURN_RE = re.compile(
    r"\[TURN (\d+)\] (.*) +vs (.+?) L(\d+) (\d+)/(\d+)(?: \[([^\]]*)\])?\s*$")
#: `vs ?`: the foe was unreadable (`_describe(None)`). NO FOE DATA — correctly unparseable, and COUNTED, never mixed
#: into "parsed" or into "unparsed".
NO_FOE_RE = re.compile(r"\[TURN \d+\] .* +vs \?\s*$")

Turn = collections.namedtuple("Turn", "turn foe level hp max_hp status")


def parse_turn(line: str) -> "Turn | None":
    """One `[TURN]` line -> `Turn(turn, foe, level, hp, max_hp, status)` (`status` is the foe's suffix text or None).
    None for a `vs ?` line (no foe data) and for anything that does not match."""
    if NO_FOE_RE.search(line):
        return None
    m = TURN_RE.search(line)
    if not m:
        return None
    turn, _me, name, lvl, hp, mx, status = m.groups()
    return Turn(int(turn), name.strip(), int(lvl), int(hp), int(mx), status)


def turn_shape(line: str) -> "str | None":
    """`parsed`, `no_foe` (a `vs ?` line), `unparsed` (a [TURN] line WITH foe data that the pattern missed — must be 0;
    every one is real data lost), or None for a line that is not a [TURN] line."""
    if "[TURN " not in line:
        return None
    if NO_FOE_RE.search(line):
        return "no_foe"
    if parse_turn(line) is not None:
        return "parsed"
    return "unparsed"


def _gains_sleep(before_status, now_status) -> bool:
    return "Sleep" in (now_status or "").split("/") and "Sleep" not in (before_status or "").split("/")


def foe_heal_events(turns) -> list:
    """`(turn, foe, before, after, kind)` for every rise of the SAME foe's current HP between consecutive records of
    one battle. Identity is `(foe, max_hp)`, so a switch to a different species — or to the same species with different
    bulk — is not mistaken for a heal. `kind` is "rest" when the rising record NEWLY carries `Sleep` in the foe's
    status suffix (Rest heals to full and sleeps the user: a move, never an item), else "heal".
    ⚠ Two IDENTICAL party members (same species and max HP) are one identity here — see the module docstring."""
    last = {}
    last_status = {}
    events = []
    for t in turns:
        key = (t.foe, t.max_hp)
        if key in last and t.hp > last[key]:
            kind = "rest" if _gains_sleep(last_status.get(key), t.status) else "heal"
            events.append((t.turn, t.foe, last[key], t.hp, kind))
        last[key] = t.hp
        last_status[key] = t.status
    return events


def foe_heals(turns) -> list:
    """`(turn, foe, before, after)` for every rise (Rest included; `foe_heal_events` tells them apart). Unchanged
    contract of the pre-#27 probe's `heals_in`."""
    return [e[:4] for e in foe_heal_events(turns)]


# ---------------------------------------------------------------------------------------------------- [ITEM]
#: Every `[ITEM]` line kind, today's AND the legacy ones, in match order (first match wins). The text of each is the
#: emitting code's (story_mode `_maybe_use_item`; the legacy ones from git history: 706d6b4c, 83a9e2f1, 96ed1ec7).
#: ⚠ `no_effect_retry` is a SHARED shape: before KI-101 (96ed1ec7, 2026-09-16) it was the index-space FLIP; today the
#: same text is emitted only when the bag count was UNREADABLE and the HP heuristic fell through. So it counts as a
#: no-effect line always, and feeds the legacy verdict only alongside a legacy-ONLY line (`LEGACY_ONLY_KINDS`).
ITEM_KINDS = (
    ("using", re.compile(r"\[ITEM\] using .+ on .+ \d+/\d+ \(use \d+, worst hit \d+\)")),
    ("consumed", re.compile(r"\[ITEM\] ✔ CONSUMED \(bag count dropped\)")),
    ("landed", re.compile(r"\[ITEM\] ✔ landed \(KI-101")),
    ("not_consumed_retry", re.compile(r"\[ITEM\] ‼ not consumed — the item was NOT consumed — retrying once")),
    ("not_consumed_disable", re.compile(r"\[ITEM\] ‼ not consumed — the item was NOT consumed twice; disabling")),
    ("no_effect_retry", re.compile(r"\[ITEM\] ‼ no effect \(HP still [^)]*\) — retrying with the (\w+)-order index")),
    ("no_effect_disable", re.compile(r"\[ITEM\] ‼ no effect \(HP still [^)]*\) — HP did not rise on two attempts")),
    ("cure_worked", re.compile(r"\[ITEM\] status cure ✔ WORKED: ")),
    ("cure_no_change", re.compile(r"\[ITEM\] status cure ‼ no change: ")),
    ("fresh_read_failed", re.compile(r"\[ITEM\] KI-101 fresh-read failed ")),
    ("legacy_landed", re.compile(r"\[ITEM\] ✔ landed using the (\w+)-order index")),
    ("legacy_both_failed", re.compile(r"\[ITEM\] ‼ no effect \(HP still [^)]*\) — both index spaces failed")),
    ("legacy_not_executing", re.compile(r"\[ITEM\] ‼ no effect \(HP still [^)]*\) — item use is not executing")),
)
ITEM_KIND_NAMES = tuple(name for name, _ in ITEM_KINDS) + ("unknown",)
#: Kinds only the pre-KI-101 code printed: their presence is what turns the legacy index-space verdict on.
LEGACY_ONLY_KINDS = frozenset({"legacy_landed", "legacy_both_failed"})
#: Every kind that is a VERDICT on a preceding `using` request (the rest are requests or notes).
VERDICT_KINDS = frozenset({"consumed", "landed", "not_consumed_retry", "not_consumed_disable", "no_effect_retry",
                           "no_effect_disable", "cure_worked", "cure_no_change", "legacy_landed",
                           "legacy_both_failed", "legacy_not_executing"})
#: The "no effect" family (the HP-heuristic verdicts), today's and legacy.
NO_EFFECT_KINDS = frozenset({"no_effect_retry", "no_effect_disable", "legacy_both_failed", "legacy_not_executing"})


def item_kind(line: str) -> "str | None":
    """The kind of one `[ITEM]` line (see `ITEM_KINDS`), `unknown` for an `[ITEM]` line matching none — COUNTED,
    never dropped — and None for a line that is not an `[ITEM]` line (`[ITEM-FLOW]` is not)."""
    if "[ITEM] " not in line:
        return None
    for name, pattern in ITEM_KINDS:
        if pattern.search(line):
            return name
    return "unknown"


def index_space(line: str) -> "str | None":
    """The `<party|battle>` word of a legacy landed / flip line, else None (the legacy verdict counts by it)."""
    for name in ("legacy_landed", "no_effect_retry"):
        m = dict(ITEM_KINDS)[name].search(line)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------------------------------- [TRAINER]
_CLASS_TOKEN = re.compile(r"^0x([0-9A-Fa-f]+)(?:\([^)]*\))?$")


def parse_classes(field: str) -> list:
    """`0x0E(HEX_MANIAC)+0x07(COLLECTOR)` -> `[0x0E, 0x07]`; a `?` side (or any token that is not a class id) -> None
    in its place. The id is the identity; the parenthesised ROM name is only a label (and not unique)."""
    out = []
    for tok in field.split("+"):
        m = _CLASS_TOKEN.match(tok.strip())
        out.append(int(m.group(1), 16) if m else None)
    return out


def _fields(msg: str) -> dict:
    return {k: v for k, v in re.findall(r"(\w+)=(\S+)", msg)}


def parse_trainer(line: str) -> "dict | None":
    """A `[TRAINER]` line -> `{"kind": start|end|skip|unreadable|other, "classes": [...], "opp": str|None,
    "double": str|None, "two": str|None, "res": str|None}`; None if not a `[TRAINER]` line."""
    if route(line) != "trainer":
        return None
    msg = _PREFIX.match(line.rstrip("\r\n")).group(2)
    word = msg.split(" ", 1)[0]
    if word in ("start", "end") and "unreadable" in msg.split(" ", 2)[1:2]:
        kind = "unreadable"
    elif word in ("start", "end", "skip"):
        kind = word
    else:
        kind = "other"
    f = _fields(msg)
    return {"kind": kind, "classes": parse_classes(f["class"]) if "class" in f else [], "opp": f.get("opp"),
            "double": f.get("double"), "two": f.get("two"), "res": f.get("res"),
            "heal_stock": parse_heal_stock(f["heal_stock"]) if "heal_stock" in f else None}


def parse_heal_stock(field: str) -> "list | None":
    """`Potion:1,Full_Heal:1` -> `[("Potion", 1), ("Full Heal", 1)]` (the emitter writes spaces as `_`,
    `trainer_identity.heal_stock`); `-` -> `[]` (none held); anything unparseable -> None (unreadable, never 0)."""
    if field == "-":
        return []
    out = []
    for part in field.split(","):
        name, sep, qty = part.rpartition(":")
        if not sep or not name or not qty.isdigit():
            return None
        out.append((name.replace("_", " "), int(qty)))
    return out


def hp_item_count(stock, param_of) -> "tuple[int | None, list]":
    """PURE: (how many HP-restoring items `stock` holds, names `param_of` could not resolve). An HP item is one whose
    item `parameter` > 0 — the SAME filter the production HP policy applies (`story_mode._maybe_use_item`:
    `options = [opt for opt in medicine if opt[2] > 0]`), so a Full Heal or a Revive is never counted. `stock` None
    (unreadable) -> (None, [])."""
    if stock is None:
        return None, []
    count, unknown = 0, []
    for name, qty in stock:
        param = param_of(name)
        if param is None:
            unknown.append(name)
        elif param > 0:
            count += qty
    return count, unknown


def key_group(classes) -> "str | None":
    """The `KEY_GROUPS` name of the battle's key class (the first group in report order that holds any side's class);
    None when no side is a key class. ⚠ A two-opponent battle whose sides fall in DIFFERENT groups would be reported
    under the first; none has been seen (Maxie + Tabitha at the Space Center are both `magma_aqua`)."""
    for name, ids in KEY_GROUPS.items():
        if any(c is not None and c in ids for c in classes):
            return name
    return None


def key_class(classes) -> "bool | None":
    """KEY (True) if ANY side's class id is in `KEY_CLASSES`; NON-KEY (False) only when EVERY side was read and none
    is; None (UNCLASSIFIED) for no class at all, or an unreadable side beside non-key ones (it might be the key one)."""
    if not classes:
        return None
    if any(c is not None and c in KEY_CLASSES for c in classes):
        return True
    if any(c is None for c in classes):
        return None
    return False


# ---------------------------------------------------------------------------------------------------- [KEYBATTLE]
def parse_keybattle(line: str) -> "dict | None":
    """`[KEYBATTLE] opp= class= key= allow= reason=` -> its fields (`classes` parsed), else None."""
    if route(line) != "keybattle":
        return None
    f = _fields(_PREFIX.match(line.rstrip("\r\n")).group(2))
    f["classes"] = parse_classes(f["class"]) if "class" in f else []
    return f


# ---------------------------------------------------------------------------------------------------- [DBLITEM]
#: `after g=0 target=Sceptile#863B0917 hp=21->117 ... partner=Swellow#0B30A747 hp=18->18 ...`. The label is
#: `Species#PID8` or `?`, and a species name may hold a space, so each `hp=` is bound to the label BEFORE it.
#: ⛔ The label is `[^=]+?`, never `.+?`: an UNREADABLE target prints `target=? hp=?->117 ... partner=Swellow#0B30A747
#: hp=18->109`, and `.+?#…` (tried before `\?`) ran on through `hp=` into the PARTNER's label, binding the partner's
#: 18->109 to the target. A label holds no `=`, so it cannot cross a field (found by the builder's review, 2026-09-30).
_AFTER_TARGET = re.compile(r"\btarget=([^=]+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")
_AFTER_PARTNER = re.compile(r"\bpartner=([^=]+?#[0-9A-F]{8}|\?) hp=(\S+?)->(\S+)")
#: ... `partner=… hp=a->b <item>=q0->q1 healed=h0->h1 same=0|1` (battle_action_selection `_dbl_after`). The item NAME
#: may hold a space ("Hyper Potion") but never `=`, so it is `[^=]+?` after the LAST `hp=` field.
_AFTER_ITEM = re.compile(r" hp=\S+ ([^=]+?)=(\S+?)->(\S+) healed=(\S+?)->(\S+) same=(\S+)\s*$")


def _int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def parse_dblitem(line: str) -> "dict | None":
    """A `[DBLITEM]` line -> `{"kind": use|menu|after|struggle-exit|err|other, ...}`; None if not one. `menu` carries
    `ok` / `a_pressed` (ints); `after` carries target/partner HP before/after (ints or None) or `err`."""
    if route(line) != "dblitem":
        return None
    msg = _PREFIX.match(line.rstrip("\r\n")).group(2)
    word = msg.split(" ", 1)[0]
    out = {"kind": word if word in ("use", "menu", "after", "struggle-exit", "err") else "other"}
    if word == "menu":
        f = _fields(msg)
        out.update(ok=_int(f.get("ok")), a_pressed=_int(f.get("a_pressed")), slot=f.get("slot"),
                   menu_pid=f.get("menu_pid"), intended_pid=f.get("intended_pid"))
    elif word == "after":
        t = _AFTER_TARGET.search(msg)
        p = _AFTER_PARTNER.search(msg)
        q = _AFTER_ITEM.search(msg)
        out.update(err="err=" in msg and not t,
                   target=t.group(1) if t else None, target_hp=(_int(t.group(2)), _int(t.group(3))) if t else None,
                   partner=p.group(1) if p else None, partner_hp=(_int(p.group(2)), _int(p.group(3))) if p else None,
                   item=q.group(1) if q else None, qty=(_int(q.group(2)), _int(q.group(3))) if q else None,
                   same=_int(q.group(6)) if q else None)
    return out


def lost_item(after: "dict | None") -> bool:
    """True when an `after` record shows the BAG DROPPED (q1 < q0) while the TARGET's HP did NOT rise, the target's
    identity held (`same=1`) and the PARTNER did not rise either: the item went to a benched Pokémon or nowhere
    visible (the independent pass, S3). ⚠ A singles `[ITEM] ✔ CONSUMED` proves only that SOME Pokémon took the item;
    this column exists only where `[DBLITEM] after` reads both battlers. Any unreadable field -> False (never guessed)."""
    if not after or after.get("kind") != "after" or not after.get("qty") or not after.get("target_hp"):
        return False
    (q0, q1), (h0, h1) = after["qty"], after["target_hp"]
    if None in (q0, q1, h0, h1):
        return False
    return q1 < q0 and h1 <= h0 and after.get("same") == 1 and not partner_rose(after)


def partner_rose(after: "dict | None") -> bool:
    """True when an `after` record shows the PARTNER's HP RISE — the item landed on the wrong Pokémon (design D3).
    Unreadable (`?`) or absent partner HP is never a rise."""
    if not after or after.get("kind") != "after" or not after.get("partner_hp"):
        return False
    before, now = after["partner_hp"]
    return before is not None and now is not None and now > before


# ---------------------------------------------------------------------------------------------------- battles
@dataclasses.dataclass
class Battle:
    """One battle: from a `[BATTLE] started` line up to the next one. `started` is False only for the segment BEFORE a
    log's first start (kept so no [TURN]/[ITEM] line is ever dropped; it is always UNCLASSIFIED)."""
    started: bool
    outcome: "str | None" = None
    trainer: list = dataclasses.field(default_factory=list)
    turns: list = dataclasses.field(default_factory=list)
    items: list = dataclasses.field(default_factory=list)
    keybattle: list = dataclasses.field(default_factory=list)
    dblitem: list = dataclasses.field(default_factory=list)
    dblobs: list = dataclasses.field(default_factory=list)


_OUTCOME = re.compile(r"ended \(outcome=(?:BattleOutcome\.)?([^)]*)\)")


def stray_lines(lines) -> list:
    """The lines that MENTION a battle tag but do not route (see `route`). Expected empty; each one is a format drift
    that would otherwise lose data silently, so the probes print the count as a control."""
    return [line for line in lines if route(line) == "stray"]


def split_battles(lines) -> list:
    """Lines of ONE log -> its `Battle` records, in order. Lines before the first `[BATTLE] started` that carry any
    battle data form a `started=False` record. `[TRAINER] end` usually follows `[BATTLE] ended` (ARMS:68-69), but when
    an evolution intervenes it comes ~1,550 frames BEFORE it, with a post-battle `[TRAINER] skip` between them
    (`evidence/2026-09-29-r25cap-raw/M0-r1.debug.txt:96-99`): either way they stay with their battle, because a record
    runs to the NEXT start. Stray lines are not battle data (`stray_lines` counts them)."""
    battles: list = []
    cur = None
    for line in lines:
        kind = route(line)
        if kind is None or kind == "stray":
            continue
        if kind == "start":
            cur = Battle(started=True)
            battles.append(cur)
            continue
        if cur is None:
            cur = Battle(started=False)
            battles.append(cur)
        if kind == "end":
            m = _OUTCOME.search(line)
            if cur.outcome is None and m:
                cur.outcome = m.group(1)
        elif kind == "turn":
            cur.turns.append(line)
        elif kind == "item":
            cur.items.append(line)
        elif kind == "trainer":
            cur.trainer.append(line)
        elif kind == "keybattle":
            cur.keybattle.append(line)
        elif kind == "dblitem":
            cur.dblitem.append(line)
        elif kind == "dblobs":
            cur.dblobs.append(line)
    return battles


def has_trainer_telemetry(lines) -> bool:
    """Does this log carry ANY `[TRAINER]` line? ⛔ Without one the log predates `[TRAINER]` (design v2 step 5,
    2026-09-29) — or the hook never ran — and the ABSENCE of a `[TRAINER]` line in a battle then says nothing about
    whether it was a wild battle."""
    return any(route(line) == "trainer" for line in lines)


def battle_classes(battle: Battle) -> list:
    """Every class id named by the battle's `[TRAINER] start/end` lines, in order."""
    out = []
    for line in battle.trainer:
        t = parse_trainer(line)
        if t and t["kind"] in ("start", "end"):
            out.extend(t["classes"])
    return out


def battle_class(battle: Battle, trainer_telemetry: bool) -> str:
    """KEY / NON-KEY from the `[TRAINER]` class ids (`key_class`); UNCLASSIFIED for a battle whose `[TRAINER]` lines
    give no readable verdict, for the pre-first-start segment, and for EVERY battle of a log with no `[TRAINER]`
    telemetry at all; WILD only for a started battle with no `[TRAINER]` line in a log that has the telemetry.
    ⛔ DECISION (the design's D2 says "WILD by the absence of a `[TRAINER] start`"): in a pre-`[TRAINER]` log that
    absence carries no information — calling those battles WILD would label every trainer battle of the batch0927
    corpus wild. So the rule needs the log-level `trainer_telemetry` flag."""
    if not battle.started:
        return UNCLASSIFIED
    if battle.trainer:
        verdict = key_class(battle_classes(battle))
        return KEY if verdict is True else NONKEY if verdict is False else UNCLASSIFIED
    return WILD if trainer_telemetry else UNCLASSIFIED


def outcome_bucket(battle: Battle) -> str:
    """`won` / `lost` / `other` from `[BATTLE] ended (outcome=...)`, else (no ended line, or an unreadable
    `outcome=None`) from a `[TRAINER] end res=`; a battle the log never ends (a reset mid-battle) is `other`.
    ⛔ A DRAW IS `lost`: `IsPlayerDefeated` returns TRUE for `B_OUTCOME_DREW` (pret/pokeemerald
    `src/battle_setup.c:994-1000`) and `CB2_EndTrainerBattle` whites the player out on it (`:1327-1334`). Counting it
    "other" silently dropped real key defeats (3 at Tate & Liza in batch0927). RanAway / Caught / OpponentTeleported
    are `other`: no trainer battle ends that way."""
    res = battle.outcome if battle.outcome not in (None, "None") else None
    if res is None:
        for line in battle.trainer:
            t = parse_trainer(line)
            if t and t["kind"] == "end" and t["res"]:
                res = t["res"]
    if res == "Won":
        return "won"
    if res in ("Lost", "Draw"):
        return "lost"
    return "other"


def win_rate(won: int, lost: int) -> "float | None":
    """won / (won + lost) — Draws are in `lost`; `other` is excluded (a battle the log never finished is no verdict).
    None when there is no decided battle (never 0: no data is not a rate)."""
    return won / (won + lost) if won + lost else None


def unclassified_reason(battle: Battle, trainer_telemetry: bool) -> "str | None":
    """WHY a battle is UNCLASSIFIED (the independent pass's N5): `pre-start` (the segment before a log's first
    `[BATTLE] started`), `no-telemetry` (a log with no `[TRAINER]` line at all), `unreadable` (it HAS `[TRAINER]` lines
    but no readable verdict: `start unreadable`, a skip only, or a `?` side beside non-key ones). None if classified."""
    if battle_class(battle, trainer_telemetry) != UNCLASSIFIED:
        return None
    if not battle.started:
        return "pre-start"
    if battle.trainer:
        return "unreadable"
    return "no-telemetry"


def battle_facts(battle: Battle, trainer_telemetry: bool) -> dict:
    """PURE: everything the probes report about ONE battle — `cls`, `group` (a `KEY_GROUPS` name, KEY battles only),
    `outcome`, `opp` (the first `[TRAINER]` start/end `opp=`, `?` if none), `double` (True / False / None from
    `[TRAINER] start double=`), `heal_stock` (the parsed start `heal_stock=`, None if absent or unreadable) and
    `reason` (`unclassified_reason`)."""
    cls = battle_class(battle, trainer_telemetry)
    opp, double, stock = None, None, None
    for line in battle.trainer:
        t = parse_trainer(line)
        if not t or t["kind"] not in ("start", "end"):
            continue
        if opp is None and t["opp"]:
            opp = t["opp"]
        if t["kind"] == "start" and double is None and t["double"] in ("True", "False"):
            double = t["double"] == "True"
        if t["kind"] == "start" and stock is None:
            stock = t["heal_stock"]
    return {"cls": cls, "group": key_group(battle_classes(battle)) if cls == KEY else None,
            "outcome": outcome_bucket(battle), "opp": opp or "?", "double": double, "heal_stock": stock,
            "reason": unclassified_reason(battle, trainer_telemetry)}


def attempt_summary(records) -> dict:
    """PURE: per KEY group, the per-TRAINER view (the independent pass's S1). `records` is an ordered iterable of
    `(log_id, opp, group, outcome)` for KEY battles. ⛔ WHY: a per-ATTEMPT win rate is dominated by a few looping runs
    (one batch0927 run whited out 28 times at Tate & Liza), and `first=` cannot mark a first attempt — the defeated
    flag stays unset on every attempt until a win (`trainer_identity.is_first_fight`). So each `(log, opp)` pair is
    one trainer met in one run: its FIRST attempt's outcome, whether it was EVENTUALLY won, and the attempts it took.
    Returns `{group: {"pairs", "first": Counter(won/lost/other), "eventually_won", "attempts_to_win": [...],
    "max_attempts"}}`."""
    pairs: dict = {}
    for log_id, opp, group, outcome in records:
        pairs.setdefault((group, log_id, opp), []).append(outcome)
    out: dict = {}
    for (group, _log, _opp), outcomes in pairs.items():
        g = out.setdefault(group, {"pairs": 0, "first": collections.Counter(), "eventually_won": 0,
                                   "attempts_to_win": [], "max_attempts": 0})
        g["pairs"] += 1
        g["first"][outcomes[0]] += 1
        g["max_attempts"] = max(g["max_attempts"], len(outcomes))
        if "won" in outcomes:
            g["eventually_won"] += 1
            g["attempts_to_win"].append(outcomes.index("won") + 1)
    return out


def turn_counts(battle: Battle) -> "collections.Counter":
    """`parsed` / `no_foe` / `unparsed` over the battle's [TURN] lines."""
    return collections.Counter(turn_shape(line) for line in battle.turns)


def item_counts(battle: Battle) -> "collections.Counter":
    """Per-kind counts of the battle's `[ITEM]` lines (every line counted exactly once, `unknown` included)."""
    return collections.Counter(item_kind(line) for line in battle.items)


def dbl_counts(battle: Battle) -> "collections.Counter":
    """The battle's `[DBLITEM]` tallies: `use`, `menu`, `menu_ok`, `menu_refused`, `menu_refused_pressed` (a refusal
    whose A was pressed anyway — only the NOGUARD fault does that), `menu_ok_not_pressed`, `after`, `after_err`,
    `wrong_target` (an `after` whose PARTNER's HP rose), `lost_item` (`lost_item`: the bag dropped, the target did not
    rise, `same=1`, the partner did not rise), `struggle-exit`, `err`, `other`, and `obs` (`[DBLITEM-OBS]`)."""
    c = collections.Counter()
    for line in battle.dblitem:
        d = parse_dblitem(line)
        c[d["kind"]] += 1
        if d["kind"] == "menu":
            if d["ok"] == 1:
                c["menu_ok"] += 1
                if d["a_pressed"] != 1:
                    c["menu_ok_not_pressed"] += 1
            else:
                c["menu_refused"] += 1
                if d["a_pressed"] == 1:
                    c["menu_refused_pressed"] += 1
        elif d["kind"] == "after":
            if d["err"]:
                c["after_err"] += 1
            if partner_rose(d):
                c["wrong_target"] += 1
            if lost_item(d):
                c["lost_item"] += 1
    c["obs"] += len(battle.dblobs)
    return c


def _fmt_rate(won: int, lost: int) -> str:
    r = win_rate(won, lost)
    return "n/a" if r is None else f"{100.0 * r:.1f}%"


def group_outcome_lines(by_group: dict) -> list:
    """PURE: the per-KEY-GROUP x outcome table both probes print — n, won, lost (Draw included), other, and
    won/(won+lost) ("n/a" with no decided battle, never 0%). `by_group[g]` needs n / won / lost / other."""
    lines = [f"      {'key group':<13}{'n':>7}{'won':>7}{'lost':>7}{'other':>7}{'won/(won+lost)':>17}"]
    for g in KEY_GROUPS:
        r = by_group.get(g) or {}
        n, won, lost, other = (r.get(k, 0) for k in ("n", "won", "lost", "other"))
        lines.append(f"      {g:<13}{n:>7}{won:>7}{lost:>7}{other:>7}{_fmt_rate(won, lost):>17}")
    return lines


def attempt_lines(summary: dict) -> list:
    """PURE: the per-(log, trainer) table both probes print from `attempt_summary`."""
    lines = [f"      {'key group':<13}{'trainers':>9}{'1st won':>9}{'1st lost':>9}{'1st other':>10}"
             f"{'eventually won':>16}{'attempts to win: median / max':>32}{'most attempts':>15}"]
    for g in KEY_GROUPS:
        r = summary.get(g)
        if not r:
            lines.append(f"      {g:<13}{0:>9}")
            continue
        a = sorted(r["attempts_to_win"])
        med = a[len(a) // 2] if a else "-"
        lines.append(f"      {g:<13}{r['pairs']:>9}{r['first']['won']:>9}{r['first']['lost']:>9}"
                     f"{r['first']['other']:>10}{r['eventually_won']:>16}"
                     f"{(str(med) + ' / ' + str(a[-1])) if a else '-':>32}{r['max_attempts']:>15}")
    return lines


# ---------------------------------------------------------------------------------------------------- run identity (T2)
#: The run header's `env-all:` line (`modules/debug_logger.py:262-266`): a dict repr of every `POKEBOT_*` variable, or
#: the note "(no POKEBOT_* env vars set)". The same shape `x4_headless._ENV_ALL_RE` checks live (T1(b)).
_ENV_ALL_LINE = re.compile(r"^\s*env-all:\s+(.*)$")
#: The header's last line (`debug_logger.py`). ⛔ The arm is read from the HEADER only: a later line that merely
#: quotes an `env-all:` text must never decide a run's arm.
HEADER_END = "--- END RUN HEADER ---"
#: The cap marker (`debug_logger._event`, :463-468): after it only STUCK dumps are written, so a capped log's TAIL is
#: missing, never empty — the comparator treats it as censored there, exactly like a run cut by the deadline.
CAP_MARKER = "event log size cap reached"
#: A heartbeat line (`f<frame> [hb] … ids=[…] …`). Its FIRST line has `ids=[]` (no party yet), so identity is the
#: first `[hb]` whose `ids=` list is NON-EMPTY: `ids=['<Species>#<PID8>:L5:exp135', …]`.
_HB_LINE = re.compile(r"^(?:f\d+ )?\[hb\] ")
_HB_IDS_OPEN = re.compile(r"\bids=\[(.)")
_HB_FIRST_ID = re.compile(r"\bids=\['([^'#:]+)#([0-9A-Fa-f]{8}):")
#: `[STEP] 'Intro: holding 7f before confirming (RNG decorrelation)...'` (`intro.py:176-186`; no line when the hold is
#: 0) and `[STEP] 'Story: choosing Treecko!'`. The message is a Python repr, so either quote may open it.
_HOLD = re.compile(r"\[STEP\] ['\"]Intro: holding (\d+)f before confirming")
_CHOSEN = re.compile(r"\[STEP\] ['\"]Story: choosing ([A-Za-z]+)!")


def parse_env_all(lines) -> "dict | None":
    """The run header's `env-all:` value as a dict (`ast.literal_eval`), or None: no such line before the header's
    end, an unparseable value, or a value that is not a dict (the "(no POKEBOT_* env vars set)" note)."""
    for line in lines:
        if line.startswith(HEADER_END):
            return None
        m = _ENV_ALL_LINE.match(line.rstrip("\r\n"))
        if m:
            try:
                got = ast.literal_eval(m.group(1).strip())
            except Exception:  # noqa: BLE001 - an unparseable header is "no arm", never a guess
                return None
            return got if isinstance(got, dict) else None
    return None


def has_header(lines) -> bool:
    """Does the log carry a COMPLETE run header (its end line)? A log the deadline cut before the header was written
    has no arm to read and no run in it."""
    return any(line.startswith(HEADER_END) for line in lines)


def arm_of(lines, arms: dict) -> str:
    """The arm name whose dict EQUALS the header's `env-all:` dict; `"?"` when none does (or the header has none) and
    `"ambiguous"` when several do. ⛔ Equality, never a subset: one leaked or missing key is a different arm."""
    env = parse_env_all(lines)
    hits = [name for name, spec in arms.items() if env is not None and env == spec]
    if len(hits) > 1:
        return "ambiguous"
    return hits[0] if hits else "?"


def run_identity(lines) -> dict:
    """`{"species", "pid", "hold", "chosen"}` of one run. `species` / `pid` from the FIRST `[hb]` line whose `ids=` is
    non-empty (if that line does not parse, both stay None: the first is the identity, never a later one); `hold` from
    the `Intro: holding Nf` STEP line (0 when absent: the hold was 0; kept for audit only); `chosen` from
    `Story: choosing X!`. ⛔ A missing value is None, never guessed (e.g. a run cut before its starter was given)."""
    out = {"species": None, "pid": None, "hold": 0, "chosen": None}
    ids_seen = hold_seen = False
    for line in lines:
        if not hold_seen and "Intro: holding" in line:
            m = _HOLD.search(line)
            if m:
                out["hold"], hold_seen = int(m.group(1)), True
        if out["chosen"] is None and "Story: choosing" in line:
            m = _CHOSEN.search(line)
            if m:
                out["chosen"] = m.group(1)
        if not ids_seen and _HB_LINE.match(line):
            opened = _HB_IDS_OPEN.search(line)
            if opened and opened.group(1) != "]":
                ids_seen = True
                m = _HB_FIRST_ID.search(line)
                if m:
                    out["species"], out["pid"] = m.group(1), m.group(2).upper()
        if ids_seen and out["chosen"] is not None:
            break
    return out


def log_capped(lines) -> bool:
    """True if any line carries the cap marker (`CAP_MARKER`): the log's event lines stop there."""
    return any(CAP_MARKER in line for line in lines)


def opp_ids(opp) -> set:
    """`265` -> {265}; `106+13` -> {106, 13}; `?` / None -> set()."""
    return {int(tok) for tok in (opp or "").split("+") if tok.strip().isdigit()}


def _trainer_events(battle: Battle) -> "tuple[set, set]":
    """(the opp ids of the battle's `[TRAINER] start` lines, the opp ids of its `[TRAINER] end` lines)."""
    starts, ends = set(), set()
    for line in battle.trainer:
        t = parse_trainer(line)
        if t and t["kind"] == "start":
            starts |= opp_ids(t["opp"])
        elif t and t["kind"] == "end":
            ends |= opp_ids(t["opp"])
    return starts, ends


def keys_met(battles, ids_of: dict) -> set:
    """The keys of `ids_of` (key -> trainer ids) the run MET: any `[TRAINER] start` whose opp is one of the key's ids,
    finished or not."""
    met = set()
    for battle in battles:
        starts, _ends = _trainer_events(battle)
        met |= {key for key, ids in ids_of.items() if starts & set(ids)}
    return met


def first_attempts(battles, ids_of: dict) -> dict:
    """PURE: key -> the run's FIRST ATTEMPT at that key (`ids_of`: key -> trainer ids), or None. The first attempt is
    the EARLIEST battle whose `[TRAINER] start` opp is one of the key's ids AND that has a `[TRAINER] end` for one of
    them (design T2(e)); a start without its end (a reset, or the deadline mid-battle) is not an attempt. Each value is
    `{"index", "outcome", "heal_stock", "battle"}`: `outcome` is `outcome_bucket` (won / lost / other; ⛔ a Draw is
    LOST) and `heal_stock` the START line's parsed bag (None if absent or unreadable). ⛔ The `first=` field is NOT
    read: it stays True on every lost re-attempt (`trainer_identity.is_first_fight`; review S10)."""
    out = {key: None for key in ids_of}
    for index, battle in enumerate(battles):
        starts, ends = _trainer_events(battle)
        for key, ids in ids_of.items():
            if out[key] is None and starts & set(ids) and ends & set(ids):
                out[key] = {"index": index, "outcome": outcome_bucket(battle),
                            "heal_stock": battle_facts(battle, True)["heal_stock"], "battle": battle}
    return out


# ---------------------------------------------------------------------------------------------------- I/O
# Everything below touches the disk. Nothing above does.

def main_checkout(repo: pathlib.Path = REPO) -> pathlib.Path:
    """The MAIN checkout's root. A git worktree's `.git` is a FILE (`gitdir: <main>/.git/worktrees/<name>`), and a
    worktree has no batch logs — so the default profiles directory is the main checkout's, never the worktree's."""
    dotgit = repo / ".git"
    if dotgit.is_file():
        text = dotgit.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"gitdir:\s*(.+)", text)
        if m:
            gitdir = pathlib.Path(m.group(1).strip())
            parts = gitdir.parts
            if "worktrees" in parts:
                return pathlib.Path(*parts[:parts.index("worktrees") - 1])
    return repo


def default_profiles() -> pathlib.Path:
    return main_checkout() / "sandbox-pokebot" / "profiles"


def try_read(path) -> "tuple[list, int] | None":
    """(lines, bytes) of one log, or None when it cannot be read — so the file control counts SUCCESSFUL reads
    (the independent pass's N2), never paths. A log cut mid-character still reads (`errors="replace"`)."""
    p = pathlib.Path(path)
    try:
        data = p.read_bytes()
    except OSError:
        return None
    return data.decode("utf-8", errors="replace").splitlines(), len(data)


def read_lines(path) -> "tuple[list, int]":
    """(lines, bytes) of one log; ([], 0) when it cannot be read (`try_read` tells the two apart)."""
    got = try_read(path)
    return got if got is not None else ([], 0)


def read_logs(paths, stats: dict):
    """Yield each READABLE log's lines, one log in memory at a time; `stats` gains `read` (successful reads) and
    `bytes` — the file control counts what was read, never what was matched (an unreadable log is visible as
    `matched - read`)."""
    stats["read"] = stats.get("read", 0)
    stats["bytes"] = stats.get("bytes", 0)
    for path in paths:
        got = try_read(path)
        if got is None:
            continue
        stats["read"] += 1
        stats["bytes"] += got[1]
        yield got[0]


def scan_logs(profiles_dir, since: str, until: str, lanes=None) -> dict:
    """`analyze_endless_batch.analyse`'s rule with the profiles directory a PARAMETER: every `endless-P*` lane (and, with
    `lanes`, only lanes whose directory NAME contains one of those substrings), its `debug-logs/*.log` AND
    `debug-logs/Old/*.log` (a name in both is taken from `Old/`), the day read from the file name
    (`...debug-YYYYMMDD-HHMMSS.log`), `since <= day <= until`. Returns `paths` (sorted by lane, then name) and what the
    window and the filter LEFT OUT (the independent pass's S6: a batch that crosses midnight, or two arms sharing a
    day, must not be cut or merged silently): `per_lane` (selected per lane), `before` / `after` (logs outside the
    window), `lanes_skipped` (lane names `lanes` excluded)."""
    root = pathlib.Path(profiles_dir)
    out = {"paths": [], "per_lane": collections.Counter(), "before": 0, "after": 0, "lanes_skipped": []}
    for lane in sorted(p for p in root.glob("endless-P*") if p.is_dir()):
        if lanes and not any(s in lane.name for s in lanes):
            out["lanes_skipped"].append(lane.name)
            continue
        logs = {q.name: q for q in (lane / "debug-logs").glob("*.log")}
        logs.update({q.name: q for q in (lane / "debug-logs" / "Old").glob("*.log")})
        for name in sorted(logs):
            stamp = name.split("debug-")[-1].replace(".log", "")
            day = stamp.split("-")[0]
            if since <= day <= until:
                out["paths"].append(logs[name])
                out["per_lane"][lane.name] += 1
            elif day < since:
                out["before"] += 1
            else:
                out["after"] += 1
    return out


def select_logs(profiles_dir, since: str, until: str, lanes=None) -> list:
    """The paths of `scan_logs` (the `analyze_endless_batch.analyse` rule; gate row SL2 holds them equal)."""
    return scan_logs(profiles_dir, since, until, lanes)["paths"]


def main_story_dev() -> pathlib.Path:
    """The MAIN checkout's tools/story-dev: where `x4-runs/<stamp>` batches are written (a worktree has none)."""
    return main_checkout() / "tools" / "story-dev"


#: A lane directory of an `x4_headless` batch: `L{slot + 1:02d}` (`x4_headless.py`), so L01..L16 tonight and
#: L100 past 99 lanes. ⛔ Was the glob `L0*`, which silently read only L01-L09 of a 16-lane batch (review R3).
_LANE_DIR = re.compile(r"L\d{2,}")


def batch_logs(batch_dir) -> list:
    """Every `L<nn>/debug-logs/*.log` of one batch directory, for ANY lane count, files only, sorted."""
    root = pathlib.Path(batch_dir)
    lanes = sorted(p for p in root.glob("L*") if p.is_dir() and _LANE_DIR.fullmatch(p.name))
    return sorted(q for lane in lanes for q in (lane / "debug-logs").glob("*.log") if q.is_file())


def x4_logs(stamp: str, base=None) -> list:
    """`x4-runs/<stamp>/L<nn>/debug-logs/*.log` (`batch_logs`). The stamp resolves under the MAIN checkout's
    tools/story-dev by default (design T2(b), review R3: from a worktree it used to resolve to the worktree's own,
    empty, `x4-runs`)."""
    return batch_logs(pathlib.Path(base if base is not None else main_story_dev()) / "x4-runs" / stamp)


def live_logs(tag: str, profiles=None) -> list:
    """LIVE mode: every `endless-<tag>-H*/debug-logs/*.log` of a RUNNING `x4_headless --profile-tag <tag>` batch,
    under the MAIN checkout's `sandbox-pokebot/profiles` by default (during a batch its `x4-runs/<stamp>/L<nn>/` hold
    only `stdout.txt`: the logs are collected at the END). A name also archived under `debug-logs/Old/` is read once,
    from `Old/` (the `scan_logs` rule). ⛔ `endless-<tag>-H*`, never `endless-<tag>*`: tag `s14` must not read the
    `s14smoke` lanes."""
    root = pathlib.Path(profiles) if profiles is not None else default_profiles()
    found: dict = {}
    for lane in sorted(p for p in root.glob(f"endless-{glob.escape(tag)}-H*") if p.is_dir()):
        for sub in ("debug-logs", "debug-logs/Old"):
            for q in sorted((lane / sub).glob("*.log")):
                if q.is_file():
                    found[(lane.name, q.name)] = q
    return sorted(found.values())


def glob_logs(pattern) -> list:
    """Any set of logs by glob (`--logs`, repeatable: a str or a list of globs), FILES only (a directory matching the
    glob is not a log), de-duplicated, sorted."""
    patterns = [pattern] if isinstance(pattern, str) else list(pattern)
    found = {pathlib.Path(p) for pat in patterns for p in glob.glob(pat) if pathlib.Path(p).is_file()}
    return sorted(found)


_ITEM_PARAM: dict = {}


def item_parameter(name: str) -> "int | None":
    """An item's `parameter` from the sandbox's item data (`modules.items`, read lazily, cached); None for a name the
    data does not know. Used ONLY to tell an HP item (`parameter > 0`) from a cure or a Revive in `heal_stock`."""
    if name not in _ITEM_PARAM:
        try:
            from modules.items import get_item_by_name

            _ITEM_PARAM[name] = get_item_by_name(name).parameter
        except Exception:  # noqa: BLE001 - an unknown name is reported by `hp_item_count`'s unknown list, never guessed
            _ITEM_PARAM[name] = None
    return _ITEM_PARAM[name]


def add_source_args(ap, default_stamp: str) -> None:
    """The probes' shared log-selection options (one rule, one place)."""
    ap.add_argument("stamp", nargs="?", help=f"an x4-runs/<stamp> batch (the default mode: {default_stamp})")
    ap.add_argument("--since", help="YYYYMMDD: install_sandbox endless lanes, first day (alone: ONE day)")
    ap.add_argument("--until", help="YYYYMMDD: last day (alone: ONE day)")
    ap.add_argument("--profiles", help="the profiles directory (default: the MAIN checkout's sandbox-pokebot/profiles)")
    ap.add_argument("--lanes", action="append", help="keep only lanes whose directory name contains this; repeatable")
    ap.add_argument("--logs", action="append", help="a glob of logs to read instead; repeatable")
    ap.add_argument("--tag", help="LIVE: a running x4_headless batch's --profile-tag (reads the MAIN checkout's "
                                  "sandbox-pokebot/profiles/endless-<tag>-H*/debug-logs/*.log)")
    ap.add_argument("--batch-dir", help="an x4_headless batch directory given as a PATH (its L<nn>/debug-logs/*.log)")


def resolve_sources(args, ap, default_stamp: str) -> "tuple[list, str, list]":
    """(paths, a header naming the source by ABSOLUTE path, notes to print). `ap.error` (exit 2) on a conflict, and on
    ZERO logs from a stamp, `--tag` or `--batch-dir` (design T2(b), review R3: an empty batch must never read as a
    batch where nothing happened). `--logs` / `--since` keep their own NO-DATA exit in each probe's report."""
    tag, batch_dir = getattr(args, "tag", None), getattr(args, "batch_dir", None)
    modes = sum(bool(x) for x in (args.stamp, args.since or args.until, args.logs, tag, batch_dir))
    if modes > 1:
        ap.error("give ONE of: a stamp, --since/--until, --logs, --tag, --batch-dir")
    if (args.profiles or args.lanes) and not (args.since or args.until):
        ap.error("--profiles and --lanes need --since/--until")
    notes = []
    if args.logs:
        pats = [str(pathlib.Path(p).absolute()) for p in args.logs]
        return glob_logs(pats), "logs " + " + ".join(pats), notes
    if args.since or args.until:
        since = args.since or args.until
        until = args.until or args.since
        if not (args.since and args.until):
            notes.append(f"⚠ only {'--since' if args.since else '--until'} given: the window is ONE day ({since}); "
                         f"a batch that crosses midnight needs both")
        profiles = pathlib.Path(args.profiles or default_profiles()).absolute()
        scan = scan_logs(profiles, since, until, args.lanes)
        notes.append(f"per lane: {dict(sorted(scan['per_lane'].items()))}; outside the window: {scan['before']} "
                     f"before {since}, {scan['after']} after {until}"
                     + (f"; lanes left out by --lanes: {scan['lanes_skipped']}" if args.lanes else ""))
        return scan["paths"], f"endless lanes {since}..{until} under {profiles}", notes
    if tag:
        paths, source = live_logs(tag), f"LIVE lanes endless-{tag}-H* under {default_profiles().absolute()}"
    elif batch_dir:
        paths, source = batch_logs(batch_dir), f"batch {pathlib.Path(batch_dir).absolute()}"
    else:
        stamp = args.stamp or default_stamp
        paths, source = x4_logs(stamp), f"batch {(main_story_dev() / 'x4-runs' / stamp).absolute()}"
    if not paths:
        ap.error(f"ZERO debug logs in {source} — refusing an empty report (a wrong stamp, tag or path?)")
    return paths, source, notes
