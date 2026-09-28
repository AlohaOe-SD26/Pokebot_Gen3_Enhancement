# 2026-09-28 — `#27-ki47range` PREDICTIONS ADDENDUM (filed BEFORE the `Swp` arm and BEFORE any fixed-code arm)

> Extends `2026-09-28-ki47range-PREDICTIONS.md` (committed `b11f327f`). Nothing in that file is withdrawn: the
> unfixed `C0`/`Wid`/`Foor`/`Finr` predictions stand and are graded against it. This file records (1) why the first
> unfixed runs were VOID, (2) a production-relevant finding, (3) a CHANGE OF FIX DESIGN, and (4) a new, natural arm.

## 1. THE FIRST UNFIXED RUNS WERE VACUOUS — two driver defects, both measured

- All four arms first ran identically (148 frames, sent Whismur#7E9BB3BA), Foor included, although the driver had
  written `104523`. The handler's own `[KI47-OBS] snapshot` line read **`012345`** in every arm.
- Defect 1: `get_battle_state()` is cached PER FRAME, and the dispatcher's condition (`battle_handler.py` ~:402) had
  already read it in the frame the driver wrote the bytes.
- Defect 2 (after ageing the cache entry): the driver's own re-read said `104523` while the handler, same frame, still
  read `012345`. **`BattleState.__eq__` (`battle_state.py` ~:249-261) omits `_battler_party_order`**, and the state
  cache's setter KEEPS THE OLD OBJECT when `old == new`. So a re-read whose only difference is the order is discarded.
- ⇒ The driver now installs the re-read object directly, and the verdict carries a premise conjunct,
  `injection_reached_snapshot` = the cached object's order == the written order == what `get_battle_state()` returns.
  (`Wid`, the "faithfulness control", could not have caught this: writing the TRUE order is indistinguishable from
  writing nothing. A control that cannot fail is not a control.)

## 2. A PRODUCTION FINDING (separate item, NOT fixed here): the cache can serve a stale party order

`__eq__`'s omission is also in the pristine upstream mirror. Any consumer that reads the order from
`get_battle_state()` may get an older order whenever `gBattlePartyCurrentOrder` changed and nothing compared did.
Filed as its own item; this fix is designed NOT to depend on the order at all (below), so it is unaffected.

## 3. RESULT SO FAR — the mechanism HOLDS (unfixed `Foor`, valid injection)

`froze=True`, `handler_frames=3045`, a KI-47 fault at 3,001 frames, `presses={'A': 105, 'Down': 685}`,
`injection_reached_snapshot=True`. Handler log: `snapshot order=104523`, `acted_on=[0, 4, 5]`,
`out_of_range=[4, 5]`, one `A at cursor=0` (the fainted Shedinja, refused), then Down until the watchdog. The
pre-registered falsifier ("unfixed Foor resolves") did NOT fire.

## 4. CHANGE OF FIX DESIGN — IDENTITY, not index conversion (CLAUDE.md rule 3)

The registered fix was (a) no second map in the sweep, (b) map the primary index through a FRESH `get_battle_state()`,
(c) drop out-of-range candidates. **(b) is unsound** by §1's defect 2: a "fresh" `get_battle_state()` can return the
stale-order object. Replacing it with a raw `read_symbol` would work, but this function has now had FOUR index-space
bugs (KI-18, KI-34, KI-66, this one); the robust fix is to stop converting indices at all:

- **Primary:** record the chosen mon's identity `(personality_value, species.index)` from `get_party()` at the moment
  the strategy chose it. After the in-battle menu is open, the cursor target is the slot of that identity in
  `get_party()`. No `map_battle_party_index`.
- **Sweep:** candidates = the menu slots (`enumerate(get_party())` with the menu open) of living non-egg mons whose
  identity is NOT on the field (on-field identities from `gBattleMons`). No `_to_menu_order`; no map for `_on_field`.
- **(c) is dropped:** candidates are drawn from `enumerate(party_in_menu)`, so an out-of-range slot cannot arise.
  A guard that cannot fire would be decoration.
- **Why species too:** Nincada's Shedinja is a byte copy of Nincada (`CreateShedinja` copies the whole mon), so a
  Ninjask and its Shedinja share a PID and OT ID in a real game, and the story party has a Nincada.
- **Premises** (decomp-checked by an agent, a NOTE; quoted code in `pret/pokeemerald`): `OpenPartyMenuInBattle` calls
  `UpdatePartyToBattleOrder()` synchronously, so `gPlayerParty[i]` is menu slot i while the menu is open;
  `GetCursorSelectionMonId()` is `gPartyMenu.slotId`; `SwitchPartyOrder()` has no side check, so an ENEMY send-out
  leaves the enemy's order in `gBattlePartyCurrentOrder`. The fixed `Swp` arm below tests the first premise LIVE.
- **Fault arm:** `POKEBOT_KI47_FAULT_STALEMAP=1` (read inside `handle_fainted_pokemon`) restores all three old
  conversions (the primary map through the snapshot, the KI-66 `_on_field` map, the sweep's `_to_menu_order`).

The fixed-code predictions in the original file (C0/Wid/Foor/Finr, and fixed `Foor` + STALEMAP freezing again) are
UNCHANGED by the design change.

## 5. NEW ARM `Swp` — a NATURAL non-identity order (no memory write)

Party staged `[Whismur#7E9BB3BA, Nincada#4457D0FB, Shedinja (burned, 1 HP, Growl), Poochyena#5815089E]`. Turn 1 the
strategy returns `rotate_lead(<Shedinja's index>)`, so the GAME's own `SwitchPartyOrder` sets the player's order to
`[2,1,0,3,4,5]` (`210345`); the burned Shedinja faints at the end of turn 1. The chooser is directed to Whismur (the
driver's `choose` returns Whismur's `get_party()` index: field slot 0, menu slot 2).

Computed from the unfixed code: the primary map sends the cursor to 2 (correct); the sweep double-maps menu slots
`[1,2,3]` to candidates `{1,0,3}`; cursor 2 is not a candidate, so it presses Down to 3 and A: **it sends Poochyena**.

| `Swp` | Unfixed | Fixed | Fixed + `POKEBOT_KI47_FAULT_STALEMAP=1` |
|---|---|---|---|
| premises | the turn-1 switch put the Shedinja on the field; snapshot `210345` (non-identity); Whismur's field slot (0) != its menu slot (2) | same | same |
| sends | **Poochyena#5815089E** (the WRONG mon), no freeze | **Whismur#7E9BB3BA** (the chosen mon), no freeze, <= 3x C0 frames | Poochyena again |

### Falsifiers for `Swp`
- Unfixed `Swp` sends Whismur: the double-map claim (fix part (a)) is wrong for a natural order. STOP; do not ship.
- Fixed `Swp` sends anything but Whismur: the identity premise (menu slot i == `get_party()[i]` with the menu open)
  is wrong. STOP.
- A premise conjunct false (no switch, identity order, or field slot == menu slot): the arm is VACUOUS, not a result.

## 6. REGRESSION ARM (unchanged): `--driver ki66faint` (the Steven multi battle), graded sent PID == chosen PID.
